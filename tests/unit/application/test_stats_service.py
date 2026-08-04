from datetime import UTC, datetime, timedelta

import pytest

from tests.support import InMemoryUrlRepository
from urlshortener.application.stats_service import StatsService
from urlshortener.domain.entities import ShortUrl
from urlshortener.domain.exceptions import UrlDeletedError, UrlNotFoundError

NOW = datetime(2026, 8, 5, 12, 0, 0, tzinfo=UTC)


def test_stats_aggregates_clicks_and_referrers():
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    repository.record_click("abc1234", clicked_at=NOW, referrer="https://google.com")
    repository.record_click(
        "abc1234", clicked_at=NOW + timedelta(minutes=1), referrer="https://google.com"
    )
    repository.record_click("abc1234", clicked_at=NOW + timedelta(minutes=2), referrer=None)
    service = StatsService(repository)

    stats = service.execute("abc1234")

    assert stats.total_clicks == 3
    assert stats.last_accessed == NOW + timedelta(minutes=2)
    assert stats.referrer_breakdown["https://google.com"] == 2
    assert stats.referrer_breakdown["(none)"] == 1


def test_stats_for_code_with_no_clicks_yet():
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    service = StatsService(repository)

    stats = service.execute("abc1234")

    assert stats.total_clicks == 0
    assert stats.last_accessed is None
    assert stats.referrer_breakdown == {}


def test_stats_raises_not_found_for_unknown_code():
    repository = InMemoryUrlRepository()
    service = StatsService(repository)

    with pytest.raises(UrlNotFoundError):
        service.execute("missing")


def test_stats_raises_deleted_error_for_deleted_code():
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    repository.delete("abc1234", deleted_at=NOW)
    service = StatsService(repository)

    with pytest.raises(UrlDeletedError):
        service.execute("abc1234")


def test_stats_are_still_available_for_an_expired_code():
    """Expiry stops redirects, not analytics - reviewing a campaign's final
    numbers after its link expired is a legitimate use case."""
    repository = InMemoryUrlRepository()
    repository.save(
        ShortUrl(
            code="abc1234",
            long_url="https://example.com",
            created_at=NOW - timedelta(days=2),
            expires_at=NOW - timedelta(days=1),
        )
    )
    repository.record_click(
        "abc1234", clicked_at=NOW - timedelta(days=1, minutes=-30), referrer=None
    )
    service = StatsService(repository)

    stats = service.execute("abc1234")

    assert stats.total_clicks == 1
