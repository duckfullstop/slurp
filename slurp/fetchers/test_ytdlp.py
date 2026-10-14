import httpx
import pytest
import yt_dlp.utils

from conftest import StubFetch
from slurp.fetchers.types import Format
from slurp.fetchers.ytdlp import YTDLPFetcher, _make_cancel_hook

_fetches = {
    "small": StubFetch(
        url="https://www.youtube.com/watch?v=eVrYbKBrI7o",
        format=Format.VIDEO_AUDIO,
        slug="test",
    ),  # toot
    "huge": StubFetch(
        url="https://www.youtube.com/watch?v=mSX3OyW9Rao",
        format=Format.VIDEO_AUDIO,
        slug="test",
    ),  # 8 hours roaring fire
    "x_odd_length": StubFetch(
        url="https://x.com/IslamInvasion/status/2096682082450002048",
        format=Format.VIDEO_AUDIO,
        slug="test",
    ),  # Fractional length - content warning
}


def __can_contact_youtube() -> bool:
    try:
        httpx.get("https://youtube.com")
    except (httpx.RequestError, httpx.ConnectError):
        return False
    return True


@pytest.mark.skipif(not __can_contact_youtube(), reason="Cannot contact YouTube")
@pytest.mark.xfail(
    raises=yt_dlp.utils.DownloadError,
    reason="Bot detection can cause these tests to fail",
)
class TestYTDLPFetcher:
    @pytest.fixture
    def fetcher_instance(self):
        return YTDLPFetcher()

    @pytest.fixture
    def fetcher_instance_with_args(self):
        extractor_args = {"youtube": {"player_client": ["web_embedded", "web", "tv"]}}
        return YTDLPFetcher(extractor_args=extractor_args)

    @pytest.mark.network
    def test_get_metadata(self, fetcher_instance):
        meta = fetcher_instance._get_metadata(_fetches["huge"].url)
        assert meta is not None, "_get_metadata returned None"

    @pytest.mark.network
    def test_get_metadata_x(self, fetcher_instance):
        meta = fetcher_instance._get_metadata(_fetches["x_odd_length"].url)
        assert meta is not None, "_get_metadata returned None"
        # Check fractional durations are rounded correctly
        assert meta.duration == 32, (
            f"get_metadata returned with an unexpected duration - expected 13, got {meta.duration}"
        )

    @pytest.mark.network
    def test_get_metadata_with_extractor_args(self, fetcher_instance_with_args):
        meta = fetcher_instance_with_args._get_metadata(_fetches["huge"].url)
        assert meta is not None, "_get_metadata returned None"

    @pytest.mark.network
    @pytest.mark.dl
    def test_download(self, tmp_path, fetcher_instance):
        for event in fetcher_instance.fetch(
            _fetches["small"], str(tmp_path.absolute())
        ):
            print(event)
        assert (tmp_path / "test.mkv").exists(), (
            "output file does not exist (expected 'test.mkv')"
        )

    @pytest.mark.network
    @pytest.mark.dl
    def test_download_x(self, tmp_path, fetcher_instance):
        for event in fetcher_instance.fetch(
            _fetches["x_odd_length"], str(tmp_path.absolute())
        ):
            print(event)
        assert (tmp_path / "test.mp4").exists(), (
            "output file does not exist (expected 'test.webm')"
        )

    @pytest.mark.network
    @pytest.mark.dl
    @pytest.mark.huge_dl
    def test_huge_download(self, tmp_path, fetcher_instance):
        """
        Warning: this test downloads an enormous video with a huge filesize!
        It is intended purely as a stress test.
        """
        for event in fetcher_instance.fetch(_fetches["huge"], str(tmp_path.absolute())):
            print(event)
        assert (tmp_path / "test.webm").exists(), (
            "output file does not exist (expected 'test.webm')"
        )


class TestYTDLPFetcherAbort:
    def test_abort_before_start(self, tmp_path):
        events = list(
            YTDLPFetcher().fetch(
                _fetches["small"], str(tmp_path), should_abort=lambda: True
            )
        )
        assert len(events) == 1
        assert type(events[0]).__name__ == "FetcherProgressReport"
        assert events[0].typ == "finish"
        assert events[0].status == 1
        assert events[0].message == "Fetcher aborted"

    def test_cancel_hook_raises_when_aborted(self):
        hook = _make_cancel_hook(lambda: True)
        with pytest.raises(yt_dlp.utils.DownloadCancelled):
            hook({"status": "downloading"})

    def test_cancel_hook_noop_without_abort(self):
        _make_cancel_hook(None)({"status": "downloading"})
        _make_cancel_hook(lambda: False)({"status": "downloading"})
