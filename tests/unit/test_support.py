"""Tests for the shared InMemoryUrlRepository test double itself — if this fake
has a bug, every later phase's unit tests inherit it silently.
"""

from datetime import UTC, datetime, timedelta

import pytest

from tests.support import InMemoryUrlRepository
from urlshortener.domain.entities import ShortUrl
from urlshortener.domain.exceptions import CollisionError

NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)


def test_get_by_code_returns_none_for_unknown_code():
    repo = InMemoryUrlRepository()
    assert repo.get_by_code("missing") is None


def test_save_then_get_by_code_round_trips():
    repo = InMemoryUrlRepository()
    url = ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW)
    repo.save(url)
    assert repo.get_by_code("abc1234") == url


def test_save_raises_collision_error_on_duplicate_code():
    repo = InMemoryUrlRepository()
    repo.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    with pytest.raises(CollisionError):
        repo.save(ShortUrl(code="abc1234", long_url="https://other.com", created_at=NOW))


def test_delete_sets_deleted_at():
    repo = InMemoryUrlRepository()
    repo.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    repo.delete("abc1234", deleted_at=NOW)
    assert repo.get_by_code("abc1234").is_deleted is True


def test_delete_is_a_no_op_for_unknown_code():
    repo = InMemoryUrlRepository()
    repo.delete("missing", deleted_at=NOW)  # must not raise
    assert repo.get_by_code("missing") is None


def test_delete_does_not_overwrite_an_earlier_deleted_at():
    repo = InMemoryUrlRepository()
    repo.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    repo.delete("abc1234", deleted_at=NOW)
    repo.delete("abc1234", deleted_at=NOW + timedelta(days=1))
    assert repo.get_by_code("abc1234").deleted_at == NOW


def test_get_stats_returns_none_for_unknown_code():
    repo = InMemoryUrlRepository()
    assert repo.get_stats("missing") is None


def test_get_stats_aggregates_clicks_and_referrers():
    repo = InMemoryUrlRepository()
    repo.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    repo.record_click("abc1234", clicked_at=NOW, referrer="https://google.com")
    repo.record_click(
        "abc1234", clicked_at=NOW + timedelta(minutes=1), referrer="https://google.com"
    )
    repo.record_click("abc1234", clicked_at=NOW + timedelta(minutes=2), referrer=None)

    stats = repo.get_stats("abc1234")

    assert stats.total_clicks == 3
    assert stats.last_accessed == NOW + timedelta(minutes=2)
    assert stats.referrer_breakdown["https://google.com"] == 2
    assert stats.referrer_breakdown["(none)"] == 1


def test_get_stats_with_no_clicks_yet():
    repo = InMemoryUrlRepository()
    repo.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))

    stats = repo.get_stats("abc1234")

    assert stats.total_clicks == 0
    assert stats.last_accessed is None
    assert stats.referrer_breakdown == {}
