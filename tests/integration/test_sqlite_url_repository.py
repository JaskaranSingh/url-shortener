import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from urlshortener.adapters.db.connection import create_connection
from urlshortener.adapters.sqlite_url_repository import SqliteUrlRepository
from urlshortener.domain.entities import ShortUrl
from urlshortener.domain.exceptions import CollisionError

NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def repository(db_path):
    conn = create_connection(db_path)
    yield SqliteUrlRepository(conn)
    conn.close()


def test_save_then_get_by_code_round_trips(repository):
    url = ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW)
    repository.save(url)

    result = repository.get_by_code("abc1234")

    assert result == url


def test_save_round_trips_expires_at_and_deleted_at(repository):
    expires_at = NOW + timedelta(days=7)
    url = ShortUrl(
        code="abc1234",
        long_url="https://example.com",
        created_at=NOW,
        expires_at=expires_at,
    )
    repository.save(url)

    result = repository.get_by_code("abc1234")

    assert result.expires_at == expires_at
    assert result.deleted_at is None
    assert result.is_deleted is False
    assert result.is_expired(NOW + timedelta(days=8)) is True


def test_get_by_code_returns_none_for_unknown_code(repository):
    assert repository.get_by_code("missing") is None


def test_save_raises_collision_error_on_duplicate_code(repository):
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))

    with pytest.raises(CollisionError):
        repository.save(ShortUrl(code="abc1234", long_url="https://other.com", created_at=NOW))

    # the original row must be untouched by the failed second insert
    assert repository.get_by_code("abc1234").long_url == "https://example.com"


def test_delete_soft_deletes_without_removing_the_row(repository):
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))

    repository.delete("abc1234", deleted_at=NOW)

    result = repository.get_by_code("abc1234")
    assert result is not None  # row still physically present
    assert result.is_deleted is True
    assert result.deleted_at == NOW


def test_delete_is_a_no_op_for_unknown_code(repository):
    repository.delete("missing", deleted_at=NOW)  # must not raise
    assert repository.get_by_code("missing") is None


def test_delete_does_not_overwrite_an_earlier_deleted_at(repository):
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    repository.delete("abc1234", deleted_at=NOW)

    repository.delete("abc1234", deleted_at=NOW + timedelta(days=1))

    assert repository.get_by_code("abc1234").deleted_at == NOW


def test_get_stats_returns_none_for_unknown_code(repository):
    assert repository.get_stats("missing") is None


def test_get_stats_with_no_clicks_yet(repository):
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))

    stats = repository.get_stats("abc1234")

    assert stats.total_clicks == 0
    assert stats.last_accessed is None
    assert stats.referrer_breakdown == {}


def test_get_stats_aggregates_clicks_and_referrers(repository):
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    repository.record_click("abc1234", clicked_at=NOW, referrer="https://google.com")
    repository.record_click(
        "abc1234", clicked_at=NOW + timedelta(minutes=1), referrer="https://google.com"
    )
    repository.record_click("abc1234", clicked_at=NOW + timedelta(minutes=2), referrer=None)

    stats = repository.get_stats("abc1234")

    assert stats.total_clicks == 3
    assert stats.last_accessed == NOW + timedelta(minutes=2)
    assert stats.referrer_breakdown["https://google.com"] == 2
    assert stats.referrer_breakdown["(none)"] == 1


def test_record_click_for_unknown_code_is_a_silent_no_op(repository):
    repository.record_click("missing", clicked_at=NOW, referrer=None)  # must not raise
    assert repository.get_stats("missing") is None


def test_data_persists_across_separate_connections_to_the_same_file(db_path):
    conn1 = create_connection(db_path)
    SqliteUrlRepository(conn1).save(
        ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW)
    )
    conn1.close()

    conn2 = create_connection(db_path)
    result = SqliteUrlRepository(conn2).get_by_code("abc1234")
    conn2.close()

    assert result is not None
    assert result.long_url == "https://example.com"


def test_foreign_keys_pragma_is_actually_enforced(db_path):
    """Direct proof the PRAGMA is engaged, not just assumed - our own code
    never triggers a real FK violation (record_click resolves url_id via a
    SELECT, so an unmatched code just inserts 0 rows), so this bypasses the
    repository to insert straight into clicks with a bogus url_id.
    """
    conn = create_connection(db_path)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO clicks (url_id, clicked_at) VALUES (?, ?)",
            (99999, NOW.isoformat()),
        )
    conn.close()


def test_schema_creation_is_idempotent(db_path):
    conn1 = create_connection(db_path)
    conn1.close()

    conn2 = create_connection(db_path)  # must not raise on re-applying schema.sql
    conn2.close()
