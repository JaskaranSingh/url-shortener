from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from urlshortener.domain.entities import ShortUrl, UrlStats


class UrlRepository(ABC):
    """Port: the persistence boundary for ShortUrl aggregates.

    domain/application depend only on this interface; adapters/ provides the
    concrete implementation (SqliteUrlRepository). Kept as a single combined
    read+write interface — splitting into UrlReader/UrlWriter is a deferred,
    documented-not-built decision (see docs/ARCHITECTURE.md).
    """

    @abstractmethod
    def save(self, short_url: ShortUrl) -> None:
        """Persist a new ShortUrl. Raises CollisionError if its code already exists."""

    @abstractmethod
    def get_by_code(self, code: str) -> ShortUrl | None:
        """Return the ShortUrl for code, or None if it has never existed."""

    @abstractmethod
    def delete(self, code: str, deleted_at: datetime) -> None:
        """Soft-delete: mark the mapping deleted. No-op if missing or already deleted."""

    @abstractmethod
    def record_click(self, code: str, clicked_at: datetime, referrer: str | None) -> None:
        """Record a redirect hit for code."""

    @abstractmethod
    def get_stats(self, code: str) -> UrlStats | None:
        """Return aggregated click stats for code, or None if it has never existed."""
