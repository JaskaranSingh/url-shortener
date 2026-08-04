from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ShortUrl:
    """A single short-code -> long-URL mapping. Immutable snapshot of a urls row."""

    code: str
    long_url: str
    created_at: datetime
    expires_at: datetime | None = None
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at is not None and self.expires_at <= now


@dataclass(frozen=True)
class UrlStats:
    """Aggregated click analytics for a single short code."""

    code: str
    total_clicks: int
    last_accessed: datetime | None
    referrer_breakdown: dict[str, int]
