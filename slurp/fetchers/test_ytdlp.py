from unittest.mock import patch

import httpx
import pytest
import yt_dlp.utils

from conftest import StubFetch
from slurp.fetchers.exceptions import PlaylistDetected
from slurp.fetchers.types import FetcherPlaylistAvailable, Format
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
    "x_multi": StubFetch(
        url="https://twitter.com/PrimeTobirama/status/1577759019724333058",
        format=Format.VIDEO_AUDIO,
        slug="test",
    ),  # Has multiple videos in one Tweet
    "x_multi_child": StubFetch(
        url="https://twitter.com/PrimeTobirama/status/1577759019724333058",
        format=Format.VIDEO_AUDIO,
        slug="test-02",
        playlist_index=2,
    ),  # The second video of x_multi
    "vimeo_requires_openai_header": StubFetch(
        url="https://player.vimeo.com/video/1151655050?h=ba15f56a51&amp%3Bbadge=0&amp%3Bautopause=0&amp%3Bplayer_id=0&amp%3Bapp_id=58479&controls=0&autopause=0",
        format=Format.VIDEO_AUDIO,
        slug="test",
        headers={"Referer": "openai.com"},
    ),
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
        meta = fetcher_instance._get_metadata(_fetches["huge"])
        assert meta is not None, "_get_metadata returned None"

    @pytest.mark.network
    def test_get_metadata_x(self, fetcher_instance):
        meta = fetcher_instance._get_metadata(_fetches["x_odd_length"])
        assert meta is not None, "_get_metadata returned None"
        # Check fractional durations are rounded correctly
        assert meta.duration == 32, (
            f"get_metadata returned with an unexpected duration - expected 13, got {meta.duration}"
        )

    @pytest.mark.network
    def test_get_metadata_with_extractor_args(self, fetcher_instance_with_args):
        meta = fetcher_instance_with_args._get_metadata(_fetches["huge"])
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
    def test_get_metadata_x_multi(self, fetcher_instance):
        with pytest.raises(PlaylistDetected) as exc:
            fetcher_instance._get_metadata(_fetches["x_multi"])
        # All entries share the Tweet's URL, so the index is what tells them apart.
        assert [e.index for e in exc.value.entries] == [1, 2, 3, 4]

    @pytest.mark.network
    def test_get_metadata_x_multi_child(self, fetcher_instance):
        meta = fetcher_instance._get_metadata(_fetches["x_multi_child"])
        assert meta is not None, "_get_metadata returned None"
        assert meta.duration == 25, (
            f"expected the second video (25s), got {meta.duration}"
        )

    @pytest.mark.network
    @pytest.mark.dl
    def test_download_x_multi_child(self, tmp_path, fetcher_instance):
        for event in fetcher_instance.fetch(
            _fetches["x_multi_child"], str(tmp_path.absolute())
        ):
            print(event)
        assert (tmp_path / "test-02.mp4").exists(), (
            "output file does not exist (expected 'test-02.mp4')"
        )

    @pytest.mark.network
    def test_fetch_x_multi_is_playlist(self, tmp_path, fetcher_instance):
        events = list(
            fetcher_instance.fetch(_fetches["x_multi"], str(tmp_path.absolute()))
        )
        playlists = [e for e in events if isinstance(e, FetcherPlaylistAvailable)]
        assert len(playlists) == 1
        assert len(playlists[0].entries) == 4
        assert events[-1].typ == "finish"
        assert events[-1].status == 0
        assert list(tmp_path.iterdir()) == [], "nothing should be downloaded"

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

    @pytest.mark.network
    def test_get_metadata_vimeo_requires_openai_header(
        self, tmp_path, fetcher_instance
    ):
        meta = fetcher_instance._get_metadata(_fetches["vimeo_requires_openai_header"])
        assert meta is not None, "_get_metadata returned None"

    @pytest.mark.network
    @pytest.mark.dl
    @pytest.mark.huge_dl
    def test_vimeo_download(self, tmp_path, fetcher_instance):
        """
        Warning: this test downloads an enormous video with a huge filesize!
        It is intended purely as a stress test.
        """
        for event in fetcher_instance.fetch(
            _fetches["vimeo_requires_openai_header"], str(tmp_path.absolute())
        ):
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


def _playlist(n: int, **extra) -> dict:
    return {
        "_type": "playlist",
        "entries": [
            {
                "id": str(i),
                "title": f"entry {i}",
                "webpage_url": "https://example.invalid/post",
                "playlist_index": i,
                "duration": 10,
            }
            for i in range(1, n + 1)
        ],
        **extra,
    }


class TestYTDLPFetcherPlaylist:
    @staticmethod
    def _extract(info: dict):
        return patch.object(yt_dlp.YoutubeDL, "extract_info", return_value=info)

    def test_playlist_raises(self):
        with self._extract(_playlist(3)):
            with pytest.raises(PlaylistDetected) as exc:
                YTDLPFetcher()._get_metadata(StubFetch())
        assert [(e.url, e.index, e.title) for e in exc.value.entries] == [
            ("https://example.invalid/post", i, f"entry {i}") for i in (1, 2, 3)
        ]

    def test_single_entry_playlist_is_unwrapped(self):
        with self._extract(_playlist(1)):
            meta = YTDLPFetcher()._get_metadata(StubFetch())
        assert meta.name == "entry 1"
        assert meta.duration == 10

    def test_spawned_fetch_resolving_to_playlist_errors(self):
        with self._extract(_playlist(3)):
            with pytest.raises(ValueError):
                YTDLPFetcher()._get_metadata(StubFetch(playlist_index=2))

    def test_playlist_index_selects_playlist_items(self):
        cfg = YTDLPFetcher()._gen_config(StubFetch(playlist_index=3))
        assert cfg["playlist_items"] == "3"
        assert "playlist_items" not in YTDLPFetcher()._gen_config(StubFetch())

    def test_fetch_playlist_does_not_download(self, tmp_path):
        with (
            self._extract(_playlist(2)),
            patch.object(yt_dlp.YoutubeDL, "download") as download,
        ):
            events = list(YTDLPFetcher().fetch(StubFetch(), str(tmp_path)))
        download.assert_not_called()
        assert isinstance(events[0], FetcherPlaylistAvailable)
        assert [e.index for e in events[0].entries] == [1, 2]
        assert events[-1].typ == "finish"
        assert events[-1].status == 0
