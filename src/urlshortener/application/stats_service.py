from __future__ import annotations

from urlshortener.domain.entities import UrlStats
from urlshortener.domain.exceptions import UrlDeletedError, UrlNotFoundError
from urlshortener.domain.repository import UrlRepository


class StatsService:
    """FR3 (analytics).

    Deleted codes raise UrlDeletedError (410), consistent with redirect/
    delete - the owner explicitly asked for this to be gone, everywhere.
    Expiry deliberately does NOT block stats (no check here): expiry only
    stops the redirect function, not the ability to review history -
    checking a campaign's final numbers after its link expired is a
    legitimate, common use case.
    """

    def __init__(self, repository: UrlRepository) -> None:
        self._repository = repository

    def execute(self, code: str) -> UrlStats:
        short_url = self._repository.get_by_code(code)
        if short_url is None:
            raise UrlNotFoundError(code)
        if short_url.is_deleted:
            raise UrlDeletedError(code)

        stats = self._repository.get_stats(code)
        assert stats is not None  # short_url exists, so get_stats must too
        return stats
