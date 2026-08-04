from datetime import UTC, datetime, timedelta

import pytest

from tests.support import InMemoryUrlRepository
from urlshortener.application.delete_url_service import DeleteUrlService
from urlshortener.domain.entities import ShortUrl
from urlshortener.domain.exceptions import UrlDeletedError, UrlNotFoundError

NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)


def test_delete_marks_the_url_deleted():
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    service = DeleteUrlService(repository)

    service.execute("abc1234", now=NOW)

    result = repository.get_by_code("abc1234")
    assert result.is_deleted is True
    assert result.deleted_at == NOW


def test_delete_raises_not_found_for_unknown_code():
    repository = InMemoryUrlRepository()
    service = DeleteUrlService(repository)

    with pytest.raises(UrlNotFoundError):
        service.execute("missing", now=NOW)


def test_delete_raises_deleted_error_for_already_deleted_code():
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    repository.delete("abc1234", deleted_at=NOW)
    service = DeleteUrlService(repository)

    with pytest.raises(UrlDeletedError):
        service.execute("abc1234", now=NOW + timedelta(minutes=1))


def test_delete_allows_deleting_an_expired_but_not_yet_deleted_code():
    """Deletion and expiry are independent - expiry never blocks deletion."""
    repository = InMemoryUrlRepository()
    repository.save(
        ShortUrl(
            code="abc1234",
            long_url="https://example.com",
            created_at=NOW - timedelta(days=2),
            expires_at=NOW - timedelta(days=1),
        )
    )
    service = DeleteUrlService(repository)

    service.execute("abc1234", now=NOW)

    assert repository.get_by_code("abc1234").is_deleted is True


def test_delete_preserves_click_history():
    """FR5: soft delete never removes clicks - see docs/SCHEMA.md."""
    repository = InMemoryUrlRepository()
    repository.save(ShortUrl(code="abc1234", long_url="https://example.com", created_at=NOW))
    repository.record_click("abc1234", clicked_at=NOW, referrer="https://google.com")
    service = DeleteUrlService(repository)

    service.execute("abc1234", now=NOW)

    stats = repository.get_stats("abc1234")
    assert stats.total_clicks == 1
