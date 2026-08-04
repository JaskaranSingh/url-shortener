from datetime import UTC, datetime, timedelta

from urlshortener.domain.entities import ShortUrl, UrlStats

NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)


def make_short_url(**overrides) -> ShortUrl:
    defaults = dict(
        code="abc1234",
        long_url="https://example.com",
        created_at=NOW,
        expires_at=None,
        deleted_at=None,
    )
    defaults.update(overrides)
    return ShortUrl(**defaults)


def test_is_deleted_false_when_deleted_at_is_none():
    url = make_short_url(deleted_at=None)
    assert url.is_deleted is False


def test_is_deleted_true_when_deleted_at_is_set():
    url = make_short_url(deleted_at=NOW)
    assert url.is_deleted is True


def test_is_expired_false_when_expires_at_is_none():
    url = make_short_url(expires_at=None)
    assert url.is_expired(NOW) is False


def test_is_expired_false_when_expires_at_in_future():
    url = make_short_url(expires_at=NOW + timedelta(days=1))
    assert url.is_expired(NOW) is False


def test_is_expired_true_when_expires_at_in_past():
    url = make_short_url(expires_at=NOW - timedelta(seconds=1))
    assert url.is_expired(NOW) is True


def test_is_expired_true_when_expires_at_equals_now():
    url = make_short_url(expires_at=NOW)
    assert url.is_expired(NOW) is True


def test_short_url_is_immutable():
    url = make_short_url()
    try:
        url.long_url = "https://other.com"
        raise AssertionError("expected FrozenInstanceError")
    except AttributeError:
        pass


def test_url_stats_holds_referrer_breakdown():
    stats = UrlStats(
        code="abc1234",
        total_clicks=3,
        last_accessed=NOW,
        referrer_breakdown={"https://google.com": 2, None: 1},
    )
    assert stats.total_clicks == 3
    assert stats.referrer_breakdown["https://google.com"] == 2
