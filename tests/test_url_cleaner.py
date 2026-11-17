import pytest
from utils.validator import clean_mixed_url


def test_clean_mixed_url_with_rd_playlist():
    """
    1) Poda automática de un enlace mixto (video con mix / radio adjunta):
    debe podar parámetros superfluos (&list=RD..., &index=..., etc.)
    devolviendo solo el video individual limpio y marcando fue_podada=True.
    """
    url_mixed_yt = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ&index=1"
    clean_yt, was_pruned_yt = clean_mixed_url(url_mixed_yt)
    assert clean_yt == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert was_pruned_yt is True

    url_mixed_ytm = "https://music.youtube.com/watch?v=abc123xyz&list=RDAMVMabc123xyz"
    clean_ytm, was_pruned_ytm = clean_mixed_url(url_mixed_ytm)
    assert clean_ytm == "https://music.youtube.com/watch?v=abc123xyz"
    assert was_pruned_ytm is True


def test_clean_mixed_url_normal_playlist():
    """
    2) Playlist genuina (/playlist?list=PL...):
    no debe ser alterada ni recortada y debe reportar fue_podada=False.
    """
    url_playlist_yt = "https://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj"
    clean_pl_yt, was_pruned_pl_yt = clean_mixed_url(url_playlist_yt)
    assert clean_pl_yt == url_playlist_yt
    assert was_pruned_pl_yt is False

    url_playlist_ytm = "https://music.youtube.com/playlist?list=RDCLAK5uy_kfdxoj"
    clean_pl_ytm, was_pruned_pl_ytm = clean_mixed_url(url_playlist_ytm)
    assert clean_pl_ytm == url_playlist_ytm
    assert was_pruned_pl_ytm is False


def test_clean_mixed_url_single_video():
    """
    3) Video individual sin parámetros de lista:
    debe permanecer intacto y reportar fue_podada=False.
    """
    url_single_yt = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    clean_s_yt, was_pruned_s_yt = clean_mixed_url(url_single_yt)
    assert clean_s_yt == url_single_yt
    assert was_pruned_s_yt is False

    url_single_ytm = "https://music.youtube.com/watch?v=9bZkp7q19f0"
    clean_s_ytm, was_pruned_s_ytm = clean_mixed_url(url_single_ytm)
    assert clean_s_ytm == url_single_ytm
    assert was_pruned_s_ytm is False


def test_clean_mixed_url_edge_cases():
    """
    Pruebas adicionales de robustez para entradas vacías o no válidas.
    """
    assert clean_mixed_url("") == ("", False)
    assert clean_mixed_url(None) == ("", False)
    assert clean_mixed_url("not a url") == ("not a url", False)
