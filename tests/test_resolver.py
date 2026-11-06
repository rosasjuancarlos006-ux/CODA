import pytest
from core.resolver import resolve_query


class TestResolver:
    """Conjunto de pruebas para core/resolver.py."""

    def test_resolve_query_search_default_youtube(self):
        res = resolve_query("Coldplay Yellow")
        assert res["mode"] == "search"
        assert res["query"] == "ytsearch1:Coldplay Yellow"
        assert res["original_input"] == "Coldplay Yellow"

    def test_resolve_query_search_explicit_youtube(self):
        res = resolve_query("Daft Punk Get Lucky", platform="youtube")
        assert res["mode"] == "search"
        assert res["query"] == "ytsearch1:Daft Punk Get Lucky"
        assert res["original_input"] == "Daft Punk Get Lucky"

    def test_resolve_query_search_youtube_music(self):
        res = resolve_query("Coldplay Yellow", platform="youtube_music")
        assert res["mode"] == "search"
        assert res["query"] == "ytsearch1:Coldplay Yellow Audio Oficial"
        assert res["original_input"] == "Coldplay Yellow"

    def test_resolve_query_video_url_cleaning(self):
        # Enlace con mix debe podarse
        url_mix = "https://music.youtube.com/watch?v=ABC123XYZ&list=RDABC123XYZ&index=1"
        res = resolve_query(url_mix, platform="youtube_music")
        assert res["mode"] == "video"
        assert res["query"] == "https://music.youtube.com/watch?v=ABC123XYZ"
        assert "&list=" not in res["query"]

        url_yt_mix = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ"
        res_yt = resolve_query(url_yt_mix, platform="youtube")
        assert res_yt["mode"] == "video"
        assert res_yt["query"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert "&list=" not in res_yt["query"]

    def test_resolve_query_playlist_url_preserved(self):
        pl_url = "https://music.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj"
        res = resolve_query(pl_url, platform="youtube_music")
        assert res["mode"] == "playlist"
        assert res["query"] == pl_url

    def test_resolve_query_empty_or_none(self):
        res_empty = resolve_query("", platform="youtube_music")
        assert res_empty["mode"] == "search"
        assert res_empty["query"] == "ytsearch1:Audio Oficial"

        res_none = resolve_query(None, platform="youtube")
        assert res_none["mode"] == "search"
        assert res_none["query"] == "ytsearch1:"
