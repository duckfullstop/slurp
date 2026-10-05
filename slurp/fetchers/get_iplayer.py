import json
import math
import os
import pathlib
import queue
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable, Generator
from datetime import datetime
from glob import glob

from slurp.fetchers.exceptions import (
    AmbiguousQueryError,
    FetcherMisconfiguredError,
    NoUpstreamMetadataError,
)
from slurp.fetchers.types import (
    Fetcher,
    FetcherMediaAvailable,
    FetcherMediaMetadataAvailable,
    FetcherProgressReport,
    FetcherUpdateEvent,
    Format,
    MediaMetadata,
)


class _Run:
    """
    _Run tracks the get_iplayer subprocesses belonging to a single fetch, so that they can be killed
    from outside the worker thread (which is usually blocked reading their output).
    """

    def __init__(self) -> None:
        self.stop = threading.Event()
        self._lock = threading.Lock()
        self._procs: list[subprocess.Popen] = []

    def spawn(self, args: list[str], **kwargs) -> subprocess.Popen:
        """Start a subprocess in its own process group. Raises if the run has already been stopped."""
        with self._lock:
            if self.stop.is_set():
                raise InterruptedError("fetch aborted")
            # get_iplayer spawns children (ffmpeg etc.), so we need to be able to signal the whole group.
            proc = subprocess.Popen(args, start_new_session=True, **kwargs)
            self._procs.append(proc)
            return proc

    def kill(self) -> None:
        """Stop the run, terminating (then if necessary killing) every process group it started."""
        with self._lock:
            self.stop.set()
            # Skip anything already reaped, so we never signal a recycled process group.
            procs = [p for p in self._procs if p.poll() is None]
        for sig in (signal.SIGTERM, signal.SIGKILL):
            for proc in procs:
                try:
                    os.killpg(proc.pid, sig)
                except (ProcessLookupError, PermissionError):
                    pass
            deadline = time.monotonic() + 5
            for proc in procs:
                try:
                    proc.wait(timeout=max(0.0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    pass
            procs = [p for p in procs if p.poll() is None]
            if not procs:
                return


class BBCiPlayerFetcher(Fetcher):
    """BBCiPlayerFetcher is a fetcher that uses an available get_iplayer binary to download media from the BBC."""

    name = "get_iplayer"

    _bin_name = "get_iplayer"

    def __backend_available(self) -> bool:
        """__backend_available returns True if we can call get_iplayer. Exception thrown otherwise."""
        assert self._bin_name != ""
        try:
            proc = subprocess.run(
                [self._bin_name, "-V"],
                capture_output=True,
                text=True,
                timeout=3,
            )
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            raise FetcherMisconfiguredError(f"Cannot call get_iplayer binary: {e}")
        if proc.returncode != 0:
            raise FetcherMisconfiguredError(
                f"Cannot call get_iplayer binary: {self._bin_name} returned {proc.returncode}"
            )
        return True

    @property
    def ready(self) -> bool:
        """We're Ready if the get_iplayer binary is available."""
        try:
            return self.__backend_available()
        except FetcherMisconfiguredError:
            return False

    # We're quite a specific fetcher, so relatively high priority.
    priority = 10

    service_names = ["BBC iPlayer"]
    service_urls = ["bbc.co.uk/iplayer", "bbc.co.uk/sounds"]

    @staticmethod
    def _log_emit(log: str) -> FetcherProgressReport:
        """_log_emit produces a FetcherProgressReport with the appropriate level for the given get_iplayer log line."""
        if log.startswith("ERROR: "):
            return FetcherProgressReport(
                typ="log", level="error", message=log.replace("ERROR: ", "")
            )
        elif log.startswith("WARNING: "):
            return FetcherProgressReport(
                typ="log", level="warning", message=log.replace("WARNING: ", "")
            )
        elif log.startswith("INFO: "):
            return FetcherProgressReport(
                typ="log", level="info", message=log.replace("INFO: ", "")
            )
        else:
            return FetcherProgressReport(
                typ="log", level="debug", message=log.replace("DEBUG: ", "")
            )

    def _get_metadata(self, url: str, run: _Run | None = None) -> MediaMetadata:
        """_get_metadata returns MediaMetadata for the given url. If run is given, the call can be aborted through it."""

        # get_iplayer spews metadata in a very annoying way (to allow for listing).
        # To solve this, we call the binary and get it to dump metadata to a temporary directory,
        # then attempt to find that - loading it in if we succeed.
        with tempfile.TemporaryDirectory() as tmpdir:
            args = [
                "get_iplayer",
                url,
                "--metadata-only",
                "--metadata=json",
                "--overwrite",
                f"--output={tmpdir}",
            ]
            if run is None:
                returncode = subprocess.run(
                    args, capture_output=True, text=True, timeout=300
                ).returncode
            else:
                mproc = run.spawn(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                try:
                    mproc.communicate(timeout=300)
                except subprocess.TimeoutExpired:
                    run.kill()
                    raise
                returncode = mproc.returncode
            if run is not None and run.stop.is_set():
                raise InterruptedError("fetch aborted")
            assert returncode == 0, f"get_iplayer failed with code {returncode}"

            # Find the metadata file.
            meta_files = os.listdir(tmpdir)
            if len(meta_files) == 0:
                raise NoUpstreamMetadataError(
                    "get_iplayer could not find any metadata for the given URL"
                )
            if len(meta_files) != 1:
                raise AmbiguousQueryError(
                    f"get_iplayer found {len(meta_files)} matching targets for the given URL - please refine."
                )

            meta_file = meta_files[0]

            # Load its JSON.
            meta = json.loads(open(f"{tmpdir}/{meta_file}").read())

            assert "brand" in meta, "brand key not in returned metadata file"
            if meta["brand"] == "get_iplayer":
                # This seems to happen if get_iplayer had some kind of issue retrieving the metadata file.
                raise NoUpstreamMetadataError(
                    "get_iplayer returned a result, but the response seems to indicate this media does not exist."
                )

            data = MediaMetadata(url)

            data.name = meta.get("title")
            data.author = meta.get("channel")
            data.author_url = meta.get("web")
            data.ts_upload = (
                datetime.fromisoformat(meta.get("firstbcast"))
                if meta.get("firstbcast")
                else None
            )
            try:
                data.duration = (
                    math.ceil(meta.get("duration"))
                    if meta.get("duration") is not None
                    else None
                )
            except ValueError:
                data.duration = None

            data.thumbnail_url = meta.get("thumbnail")

            data.format = meta.get("type")
        return data

    def _get_media(
        self,
        q: queue.Queue[FetcherUpdateEvent],
        url: str,
        fmt: Format,
        directory: str,
        filename: str,
        run: _Run,
    ):
        """
        Commence a download from BBC iPlayer. Stops quietly (without a finish event) if run is killed.
        """
        try:
            # We support early metadata - send that if it's available.
            metadata = self._get_metadata(url, run)
            if metadata.name != "":
                event = FetcherMediaMetadataAvailable(metadata=metadata)
                q.put(event)

            if fmt != Format.VIDEO_AUDIO:
                q.put(
                    FetcherProgressReport(
                        typ="log",
                        level="warning",
                        message="get_iplayer does not support the Format function - you will receive media in the same format as the origin.",
                    )
                )

            proc = run.spawn(
                [
                    "get_iplayer",
                    "-g",
                    url,
                    "--force",
                    "--overwrite",
                    f"--file-prefix={filename}",
                    "--radio-quality=high",
                    "--tv-quality=hd",
                    f"--output={directory}/temp",
                ],
                stdout=subprocess.PIPE,
                bufsize=1,
                text=True,
            )
            for o in proc.stdout:
                q.put(self._log_emit(o))

            # Wait for process to finish returning
            proc.wait()
            if run.stop.is_set():
                return
            assert proc.returncode == 0, (
                f"get_iplayer failed with code {proc.returncode}"
            )

            # Find the downloaded file.
            files = glob(f"{directory}/temp/{filename}.*")
            assert len(files) == 1, (
                f"unexpected number of files in bagging area: {len(files)}"
            )
            target = files[0]
            target_extension = pathlib.Path(target).suffix
            destination = f"{directory}/{filename}{target_extension}"

            # Once writing is finished, move to final location

            try:
                shutil.move(target, destination)
            except Exception as e:
                q.put(
                    FetcherProgressReport(
                        typ="finish",
                        level="error",
                        status=1,
                        message=f"exception occurred manipulating downloaded file: {e}",
                    )
                )
                q.shutdown()
                return

            # signals that media is now available for consumption
            q.put(FetcherMediaAvailable(path=target))

            q.put(
                FetcherProgressReport(
                    typ="finish",
                    level="info",
                    status=0,
                    message="Fetcher complete",
                )
            )
        except Exception as e:
            if run.stop.is_set():
                # Aborted - nobody is listening for the outcome.
                return
            q.put(
                FetcherProgressReport(
                    typ="finish",
                    level="error",
                    status=1,
                    message=f"Fetcher Exception: {e}",
                )
            )
        finally:
            # signal end of data
            q.shutdown()

    def fetch(
        self,
        url: str,
        fmt: Format,
        directory: str,
        filename: str,
        should_abort: Callable[[], bool] | None = None,
    ) -> Generator[FetcherUpdateEvent]:
        """get_media downloads the media at the given params in the foreground, returning log information by means of a Generator."""
        q: queue.Queue[FetcherUpdateEvent] = queue.Queue()
        run = _Run()

        # We need to run the download on a thread so we can continue to execute our client response
        thread = threading.Thread(
            target=self._get_media,
            args=(q, url, fmt, directory, filename, run),
            daemon=True,
        )
        thread.start()

        try:
            last_event = time.monotonic()
            while True:
                try:
                    # Poll briefly so an abort request is noticed even while get_iplayer is quiet.
                    event: FetcherUpdateEvent = q.get(timeout=1)
                except queue.ShutDown:
                    # End of data.
                    break
                except queue.Empty:
                    if should_abort is not None and should_abort():
                        break
                    if time.monotonic() - last_event > 300:
                        raise TimeoutError("get_iplayer produced no output for 300s")
                    continue
                last_event = time.monotonic()
                match event:
                    case FetcherProgressReport() as i:
                        if i.typ == "finish":
                            yield i
                            # Break the generator.
                            break
                        yield i
                    case FetcherMediaMetadataAvailable() as i:
                        yield i
                    case FetcherMediaAvailable() as i:
                        yield i
        finally:
            # Also reached when the caller closes the generator. Kill get_iplayer and its children, and
            # don't let the caller tear down the working directory while they may still be writing to it.
            run.kill()
            thread.join(timeout=30)
