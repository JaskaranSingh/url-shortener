"""Shared test doubles. InMemoryUrlRepository is reused by unit tests across all
phases (application services never touch SQLite in unit tests) — see
docs/ARCHITECTURE.md Testing Strategy.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime

from urlshortener.domain.entities import ShortUrl, UrlStats
from urlshortener.domain.exceptions import CollisionError
from urlshortener.domain.repository import UrlRepository


class InMemoryUrlRepository(UrlRepository):
    def __init__(self) -> None:
        self._urls: dict[str, ShortUrl] = {}
        self._clicks: dict[str, list[tuple[datetime, str | None]]] = {}

    def save(self, short_url: ShortUrl) -> None:
        if short_url.code in self._urls:
            raise CollisionError(short_url.code)
        self._urls[short_url.code] = short_url
        self._clicks[short_url.code] = []

    def get_by_code(self, code: str) -> ShortUrl | None:
        return self._urls.get(code)

    def delete(self, code: str, deleted_at: datetime) -> None:
        existing = self._urls.get(code)
        if existing is not None and not existing.is_deleted:
            self._urls[code] = dataclasses.replace(existing, deleted_at=deleted_at)

    def record_click(self, code: str, clicked_at: datetime, referrer: str | None) -> None:
        self._clicks.setdefault(code, []).append((clicked_at, referrer))

    def get_stats(self, code: str) -> UrlStats | None:
        if code not in self._urls:
            return None
        clicks = self._clicks.get(code, [])
        referrer_breakdown: dict[str, int] = {}
        for _, referrer in clicks:
            key = referrer if referrer is not None else "(none)"
            referrer_breakdown[key] = referrer_breakdown.get(key, 0) + 1
        last_accessed = max((ts for ts, _ in clicks), default=None)
        return UrlStats(
            code=code,
            total_clicks=len(clicks),
            last_accessed=last_accessed,
            referrer_breakdown=referrer_breakdown,
        )
