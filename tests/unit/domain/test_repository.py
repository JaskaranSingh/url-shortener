import pytest

from urlshortener.domain.repository import UrlRepository


def test_url_repository_cannot_be_instantiated_directly():
    """It's an abstract port — only concrete adapters may be instantiated."""
    with pytest.raises(TypeError):
        UrlRepository()


def test_url_repository_defines_the_full_port_surface():
    expected_methods = {"save", "get_by_code", "delete", "record_click", "get_stats"}
    assert expected_methods <= set(UrlRepository.__abstractmethods__)
