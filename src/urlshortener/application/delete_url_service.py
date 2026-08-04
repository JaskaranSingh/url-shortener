from __future__ import annotations

from datetime import datetime

from urlshortener.domain.exceptions import UrlDeletedError, UrlNotFoundError
from urlshortener.domain.repository import UrlRepository


class DeleteUrlService:
    """FR5 (deletion, soft-delete).

    Deleting an already-deleted code raises UrlDeletedError (410), the same
    exception redirect/stats already use for "deleted" - reusing that
    semantics is more consistent than inventing a delete-specific 404 for
    the same underlying state. Expiry is irrelevant here: deleting an
    expired-but-not-yet-deleted code is allowed (deletion and expiry are
    independent concerns).
    """

    def __init__(self, repository: UrlRepository) -> None:
        self._repository = repository

    def execute(self, code: str, now: datetime) -> None:
        short_url = self._repository.get_by_code(code)
        if short_url is None:
            raise UrlNotFoundError(code)
        if short_url.is_deleted:
            raise UrlDeletedError(code)

        self._repository.delete(code, deleted_at=now)
