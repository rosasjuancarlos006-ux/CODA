import pytest
from utils.validator import is_valid_youtube_url, is_playlist_url, classify_input


class TestValidator:
    """Conjunto de pruebas para utils/validator.py."""

    def test_valid_youtube_urls(self):
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "www.youtube.com/watch?v=dQw4w9WgXcQ",
            "youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=kJQP7kiw5Fk&list=RDkJQP7kiw5Fk"
        ]
        for url in urls:
            assert is_valid_youtube_url(url), f"Falló con URL válida: {url}"

    def test_invalid_youtube_urls(self):
        invalid = [
            "",
            "   ",
            "https://vimeo.com/123456",
            "https://spotify.com/track/123",
            "musica gratis 2026",
            None,
            12345
        ]
        for item in invalid:
            assert not is_valid_youtube_url(item), f"Debería ser inválido: {item}"

    def test_playlist_detection(self):
        playlists = [
            "https://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj",
            "www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj",
            "https://www.youtube.com/watch?v=video123&list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj",
            "https://youtu.be/video123?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj"
        ]
        for pl in playlists:
            assert is_playlist_url(pl), f"No detectó playlist: {pl}"

    def test_not_a_playlist(self):
        not_playlists = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "Nombre de una canción",
            "",
            None
        ]
        for item in not_playlists:
            assert not is_playlist_url(item), f"Falso positivo en playlist: {item}"

    def test_classify_input(self):
        # 1. Playlist
        assert classify_input("https://www.youtube.com/playlist?list=PL123") == "playlist"
        assert classify_input("https://www.youtube.com/watch?v=abc&list=PL123") == "playlist"

        # 2. Video individual
        assert classify_input("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "video"
        assert classify_input("https://youtu.be/dQw4w9WgXcQ") == "video"

        # 3. Búsqueda por texto libre
        assert classify_input("Bad Bunny Moscow Mule") == "search"
        assert classify_input("The Beatles Yesterday remastered") == "search"
        assert classify_input("") == "search"
        assert classify_input(None) == "search"
