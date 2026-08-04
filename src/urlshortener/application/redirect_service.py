from __future__ import annotations

from datetime import datetime

from urlshortener.domain.exceptions import UrlDeletedError, UrlExpiredError, UrlNotFoundError
from urlshortener.domain.repository import UrlRepository


class RedirectService:
    """FR2 (redirect) + FR4/FR5 (consuming side of expiry/deletion).

    Deleted and expired codes both resolve to the same outcome (410, via
    distinct exceptions the API layer maps identically) - deleted is checked
    first, an arbitrary tie-break for the rare case both are true, kept
    distinct from expiry so Phase 8's logging can tell the two apart even
    though the HTTP response doesn't.
    """

    def __init__(self, repository: UrlRepository) -> None:
        self._repository = repository

    def execute(self, code: str, now: datetime, referrer: str | None) -> str:
        short_url = self._repository.get_by_code(code)
        if short_url is None:
            raise UrlNotFoundError(code)
        if short_url.is_deleted:
            raise UrlDeletedError(code)
        if short_url.is_expired(now):
            raise UrlExpiredError(code)

        self._repository.record_click(code, clicked_at=now, referrer=referrer)
        return short_url.long_url
