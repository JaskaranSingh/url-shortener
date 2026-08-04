from datetime import UTC, datetime, timedelta

import pytest

from tests.support import InMemoryUrlRepository
from urlshortener.application.create_short_url_service import CreateShortUrlService
from urlshortener.domain.entities import ShortUrl
from urlshortener.domain.exceptions import CollisionError, InvalidExpiryError, InvalidUrlError

NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)


class SequentialCodeGenerator:
    """Test double returning a fixed, pre-scripted sequence of codes."""

    def __init__(self, codes: list[str]) -> None:
        self._codes = iter(codes)

    def generate(self) -> str:
        return next(self._codes)


def make_service(repository=None, code_generator=None, max_collision_attempts=5):
    return CreateShortUrlService(
        repository=repository or InMemoryUrlRepository(),
        code_generator=code_generator or SequentialCodeGenerator(["abc1234"]),
        max_collision_attempts=max_collision_attempts,
    )


def test_creates_short_url_with_no_expiry():
    repository = InMemoryUrlRepository()
    service = make_service(repository=repository)

    result = service.execute("https://example.com/page", now=NOW)

    assert result.code == "abc1234"
    assert result.long_url == "https://example.com/page"
    assert result.expires_at is None
    assert repository.get_by_code("abc1234") == result


def test_creates_short_url_with_future_expiry():
    service = make_service()
    expires_at = NOW + timedelta(days=1)

    result = service.execute("https://example.com", now=NOW, expires_at=expires_at)

    assert result.expires_at == expires_at


@pytest.mark.parametrize(
    "long_url",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "ftp://example.com/file",
        "not-a-url",
        "http://",  # missing host
        "https://",  # missing host
    ],
)
def test_rejects_invalid_urls(long_url):
    service = make_service()
    with pytest.raises(InvalidUrlError):
        service.execute(long_url, now=NOW)


def test_rejects_url_exceeding_max_length():
    service = make_service()
    long_url = "https://example.com/" + "a" * 3000
    with pytest.raises(InvalidUrlError):
        service.execute(long_url, now=NOW)


def test_rejects_expiry_in_the_past():
    service = make_service()
    with pytest.raises(InvalidExpiryError):
        service.execute("https://example.com", now=NOW, expires_at=NOW - timedelta(seconds=1))


def test_rejects_expiry_equal_to_now():
    service = make_service()
    with pytest.raises(InvalidExpiryError):
        service.execute("https://example.com", now=NOW, expires_at=NOW)


def test_retries_on_collision_and_succeeds_with_a_fresh_code():
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="dup0001", long_url="https://taken.example.com", created_at=NOW))
    generator = SequentialCodeGenerator(["dup0001", "dup0001", "fresh01"])
    service = make_service(repository=repository, code_generator=generator)

    result = service.execute("https://example.com", now=NOW)

    assert result.code == "fresh01"


def test_raises_collision_error_after_exhausting_retries():
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="dup0001", long_url="https://taken.example.com", created_at=NOW))
    generator = SequentialCodeGenerator(["dup0001"] * 5)
    service = make_service(
        repository=repository, code_generator=generator, max_collision_attempts=5
    )

    with pytest.raises(CollisionError):
        service.execute("https://example.com", now=NOW)
