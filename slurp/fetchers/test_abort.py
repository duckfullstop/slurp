import os
import stat
import threading
import time

import pytest

from slurp.fetchers import ytdlp
from slurp.fetchers.cobalt import CobaltFetcher
from slurp.fetchers.get_iplayer import BBCiPlayerFetcher
from slurp.fetchers.types import FetcherProgressReport, Format
from slurp.fetchers.ytdlp import YTDLPFetcher


def test_iplayer_abort_kills_process_group(tmp_path, monkeypatch):
    """Aborting mid-download must end the generator promptly and kill get_iplayer's children."""
    pidfile = tmp_path / "child.pid"
    script = tmp_path / "get_iplayer"
    script.write_text(f"#!/bin/sh\nsleep 60 &\necho $! > {pidfile}\nwait\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")

    fetcher = BBCiPlayerFetcher()
    monkeypatch.setattr(fetcher, "_get_metadata", lambda url, run=None: _meta())
    aborted = threading.Event()
    threading.Timer(1.5, aborted.set).start()

    start = time.monotonic()
    events = list(
        fetcher.fetch(
            "https://example.com",
            Format.VIDEO_AUDIO,
            str(tmp_path),
            "out",
            should_abort=aborted.is_set,
        )
    )
    assert time.monotonic() - start < 15
    assert not any(
        isinstance(e, FetcherProgressReport) and e.typ == "finish" for e in events
    )
    child = int(pidfile.read_text())
    time.sleep(0.2)
    with pytest.raises(ProcessLookupError):
        os.kill(child, 0)


def _meta():
    from slurp.fetchers.types import MediaMetadata

    m = MediaMetadata("x")
    m.name = ""
    return m


def test_cobalt_abort_stops_download(tmp_path, monkeypatch):
    import httpx

    class FakeStream:
        headers: dict = {}
        num_bytes_downloaded = 0

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def iter_bytes(self):
            while True:
                time.sleep(0.1)
                yield b"x"

    class FakeResponse:
        def raise_for_status(self):
            return self

        def json(self):
            return {"status": "tunnel", "url": "http://x/y", "filename": "a.mp4"}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: FakeResponse())
    monkeypatch.setattr(httpx, "stream", lambda *a, **k: FakeStream())
    monkeypatch.setattr(
        CobaltFetcher, "_CobaltFetcher__backend_available", lambda s: True
    )

    fetcher = CobaltFetcher("http://cobalt")
    aborted = threading.Event()
    threading.Timer(1.0, aborted.set).start()
    before = threading.active_count()
    events = list(
        fetcher.fetch(
            "https://example.com",
            Format.VIDEO_AUDIO,
            str(tmp_path),
            "out",
            should_abort=aborted.is_set,
        )
    )
    assert not any(
        isinstance(e, FetcherProgressReport) and e.typ == "finish" for e in events
    )
    assert threading.active_count() <= before


def test_ytdlp_abort_mid_download(tmp_path, monkeypatch):
    """Aborting mid-download must make the progress hook cancel yt-dlp, and the worker thread must exit."""

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.hooks = opts.get("progress_hooks", [])

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def download(self, urls):
            # Mimic yt-dlp reporting progress for a download that never finishes by itself.
            while True:
                time.sleep(0.1)
                for hook in self.hooks:
                    hook({"status": "downloading"})

    monkeypatch.setattr(ytdlp, "YoutubeDL", FakeYoutubeDL)
    monkeypatch.setattr(YTDLPFetcher, "_get_metadata", lambda s, url, fmt: _meta())

    aborted = threading.Event()
    threading.Timer(1.5, aborted.set).start()
    before = threading.active_count()

    start = time.monotonic()
    events = list(
        YTDLPFetcher().fetch(
            "https://example.com",
            Format.VIDEO_AUDIO,
            str(tmp_path),
            "out",
            should_abort=aborted.is_set,
        )
    )
    assert time.monotonic() - start < 15
    finishes = [
        e for e in events if isinstance(e, FetcherProgressReport) and e.typ == "finish"
    ]
    # The generator may end on its own poll before the worker's "aborted" event arrives, so zero or one
    # finish events are both fine - but never an error. The time bound above (the generator joins the
    # worker for up to 30s) proves the progress hook actually cancelled the download.
    assert all(f.message == "Fetcher aborted" for f in finishes)
    assert threading.active_count() <= before
