from datetime import UTC, datetime, timedelta

import pytest

from tests.support import InMemoryUrlRepository
from urlshortener.application.redirect_service import RedirectService
from urlshortener.domain.entities import ShortUrl
from urlshortener.domain.exceptions import UrlDeletedError, UrlExpiredError, UrlNotFoundError

NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)


def test_redirect_returns_long_url_and_records_click():
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    service = RedirectService(repository)

    result = service.execute("abc1234", now=NOW, referrer="https://google.com")

    assert result == "https://example.com"
    stats = repository.get_stats("abc1234")
    assert stats.total_clicks == 1
    assert stats.referrer_breakdown["https://google.com"] == 1


def test_redirect_records_click_with_no_referrer():
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    service = RedirectService(repository)

    service.execute("abc1234", now=NOW, referrer=None)

    stats = repository.get_stats("abc1234")
    assert stats.referrer_breakdown["(none)"] == 1


def test_redirect_raises_not_found_for_unknown_code():
    repository = InMemoryUrlRepository()
    service = RedirectService(repository)

    with pytest.raises(UrlNotFoundError):
        service.execute("missing", now=NOW, referrer=None)


def test_redirect_raises_deleted_error_and_records_no_click():
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    repository.delete("abc1234", deleted_at=NOW)
    service = RedirectService(repository)

    with pytest.raises(UrlDeletedError):
        service.execute("abc1234", now=NOW, referrer=None)

    assert repository.get_stats("abc1234").total_clicks == 0


def test_redirect_raises_expired_error_and_records_no_click():
    repository = InMemoryUrlRepository()
    repository.save(
        ShortUrl(
            code="abc1234",
            long_url="https://example.com",
            created_at=NOW - timedelta(days=1),
            expires_at=NOW - timedelta(seconds=1),
        )
    )
    service = RedirectService(repository)

    with pytest.raises(UrlExpiredError):
        service.execute("abc1234", now=NOW, referrer=None)

    assert repository.get_stats("abc1234").total_clicks == 0


def test_redirect_prefers_deleted_over_expired_when_both_are_true():
    """Arbitrary tie-break, locked in by this test: deleted is checked first."""
    repository = InMemoryUrlRepository()
    repository.save(
        ShortUrl(
            code="abc1234",
            long_url="https://example.com",
            created_at=NOW - timedelta(days=2),
            expires_at=NOW - timedelta(days=1),
        )
    )
    repository.delete("abc1234", deleted_at=NOW - timedelta(hours=1))
    service = RedirectService(repository)

    with pytest.raises(UrlDeletedError):
        service.execute("abc1234", now=NOW, referrer=None)


def test_redirect_at_the_exact_expiry_instant_is_expired():
    repository = InMemoryUrlRepository()
    repository.save(
        ShortUrl(
            code="abc1234",
            long_url="https://example.com",
            created_at=NOW - timedelta(days=1),
            expires_at=NOW,
        )
    )
    service = RedirectService(repository)

    with pytest.raises(UrlExpiredError):
        service.execute("abc1234", now=NOW, referrer=None)
