import math
import queue
import threading
import time
from collections.abc import Callable, Generator
from datetime import UTC, datetime
from glob import glob

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadCancelled

from slurp.fetchers.types import (
    Fetcher,
    FetcherMediaAvailable,
    FetcherMediaMetadataAvailable,
    FetcherProgressReport,
    FetcherUpdateEvent,
    Format,
    MediaMetadata,
)


def _make_cancel_hook(
    should_abort: Callable[[], bool] | None,
) -> Callable[[dict], None]:
    """
    Build a yt-dlp progress / postprocessor hook that raises DownloadCancelled once should_abort reports True.
    Hooks fire many times a second, so the (potentially remote) check is throttled.
    """
    last_check = 0.0

    def _cancel_hook(_status: dict) -> None:
        nonlocal last_check
        if should_abort is None:
            return
        now = time.monotonic()
        if now - last_check < 1:
            return
        last_check = now
        if should_abort():
            raise DownloadCancelled("Abort requested")

    return _cancel_hook


class YTDLPFetcher(Fetcher):
    """YTDLPFetcher is a fetcher that uses the YT-DLP library to download media exclusively from YouTube."""

    name = "yt-dlp"

    # YT-DLP is always ready.
    ready = True

    # We're not particularly specific - but try it first before moving on.
    priority = 100

    service_names = [
        "Most services - see https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md"
    ]

    # service_urls = ["youtube.com", "youtu.be"]
    @property
    def service_urls(self) -> list[str] | None:
        """
        service_urls returns the supported services that we can query for data.
        Cobalt is a special instance: we attempt to download anything that is otherwise unsupported by another module.
        """
        # Special return: we support anything that the backend supports.
        return None

    js_runtimes: dict[str, dict[str, str]] | None = None
    extractor_args: dict[str, dict[str, str]] | None = None

    def __init__(
        self,
        js_runtimes: dict[str, dict[str, str]] | None = None,
        extractor_args: dict[str, dict[str, str]] = None,
    ):
        self.js_runtimes = js_runtimes
        self.extractor_args = extractor_args

    class _Queuelogger:
        """queueLogger provides a yt-dlp compatible logging interface that emits exclusively to a queue."""

        def __init__(self, q: queue.Queue[FetcherUpdateEvent]):
            self.q = q

        def debug(self, msg):
            # As recommended by library documentation
            if msg.startswith("[debug] "):
                self.q.put(FetcherProgressReport(typ="log", level="debug", message=msg))
            else:
                self.info(msg)

        def info(self, msg):
            self.q.put(FetcherProgressReport(typ="log", level="info", message=msg))

        def warning(self, msg):
            self.q.put(FetcherProgressReport(typ="log", level="warning", message=msg))

        def error(self, msg):
            self.q.put(FetcherProgressReport(typ="log", level="error", message=msg))

    def _format_config(self, fmt: Format) -> dict:
        """_format_config returns YT-DLP configuration to be used when downloading media in the given format.
        :param fmt: The desired media format.
        :return: A YT-DLP configuration parameters dictionary.
        """
        cfg = {}
        if self.extractor_args is not None:
            # If extractor args are available, append them to the config.
            cfg = cfg | {"extractor_args": self.extractor_args}

        match fmt:
            case fmt.VIDEO_AUDIO:
                cfg = cfg | {
                    "format": "bestvideo*+bestaudio/best",
                }
                # force codec to h264 m4a/mp4
                # fails if this format isn't available, fix later
                # return ['-f', 'bv*[vcodec^=avc]+ba[ext=m4a]/b[ext=mp4]/b']
            case fmt.AUDIO_ONLY:
                cfg = cfg | {
                    "format": "m4a/bestaudio/best",
                    "postprocessors": [
                        {  # Extract audio using ffmpeg
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "m4a",
                        }
                    ],
                }
            case _:
                raise ValueError("invalid format")
        return cfg

    def _get_metadata(
        self, url: str, fmt: Format = Format.VIDEO_AUDIO
    ) -> MediaMetadata:
        """_get_metadata returns MediaMetadata for the given url."""
        data = MediaMetadata(url)
        with YoutubeDL(self._format_config(fmt)) as ydl:
            info = ydl.extract_info(url, download=False)

            # sanitize_info required to make serializable
            response = ydl.sanitize_info(info)
            data.name = response.get("title")
            data.author = response.get("uploader")
            data.author_url = response.get("uploader_url")
            data.ts_upload = (
                datetime.fromtimestamp(response.get("timestamp"), UTC)
                if response.get("timestamp", False)
                else None
            )
            try:
                data.duration = (
                    math.ceil(response.get("duration"))
                    if response.get("duration") is not None
                    else None
                )
            except ValueError:
                data.duration = None

            data.thumbnail_url = response.get("thumbnail")

            data.format = response.get("format")
        return data

    def _get_media(
        self,
        q: queue.Queue[FetcherUpdateEvent],
        url: str,
        fmt: Format,
        directory: str,
        filename: str,
        should_abort: Callable[[], bool] | None = None,
    ):
        """
        Commence a download from YouTube.
        """
        cancel_hook = _make_cancel_hook(should_abort)
        opts = (
            {
                "logger": self._Queuelogger(q),
                "no_warnings": True,
                "outtmpl": f"{directory}/{filename}.%(ext)s",
                "paths": {
                    "home": directory,
                    "temp": f"{directory}/temp",  # currently hard-coded - should we make this configurable?
                },
                "progress_hooks": [cancel_hook],
                "postprocessor_hooks": [cancel_hook],
            }
            | self._format_config(fmt)
        )

        if self.js_runtimes is not None:
            opts.update({"js_runtimes": self.js_runtimes})

        try:
            if should_abort is not None and should_abort():
                raise DownloadCancelled("Abort requested")

            # We support early metadata - send that if it's available.
            metadata = self._get_metadata(url, fmt)
            if metadata.name != "":
                event = FetcherMediaMetadataAvailable(metadata=metadata)
                q.put(event)

            if should_abort is not None and should_abort():
                raise DownloadCancelled("Abort requested")

            with YoutubeDL(opts) as ydl:
                code = ydl.download([url])
                files = glob(f"{directory}/*.*")
                assert len(files) == 1, (
                    f"unexpected number of files in bagging area: {len(files)}"
                )
                q.put(FetcherMediaAvailable(path=files[0]))
                q.put(
                    FetcherProgressReport(
                        typ="finish",
                        level="info",
                        status=code,
                        message="Fetcher complete",
                    )
                )
        except DownloadCancelled:
            q.put(
                FetcherProgressReport(
                    typ="finish",
                    level="warning",
                    status=1,
                    message="Fetcher aborted",
                )
            )
        except Exception as e:
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

        # We need to run the download on a thread so we can continue to execute our client response
        thread = threading.Thread(
            target=self._get_media,
            args=(q, url, fmt, directory, filename, should_abort),
            daemon=True,
        )
        thread.start()

        try:
            last_event = time.monotonic()
            while True:
                try:
                    # Poll briefly so an abort request is noticed even while yt-dlp is quiet.
                    event: FetcherUpdateEvent = q.get(timeout=1)
                except queue.ShutDown:
                    # End of data.
                    break
                except queue.Empty:
                    if should_abort is not None and should_abort():
                        break
                    if time.monotonic() - last_event > 300:
                        raise TimeoutError("yt-dlp produced no output for 300s")
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
            # Don't let the caller tear down the working directory while yt-dlp may still be writing to it.
            # The cancel hook stops the download within about a second of an abort request.
            thread.join(timeout=30)
