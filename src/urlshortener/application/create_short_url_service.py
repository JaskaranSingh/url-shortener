from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

from urlshortener.application.short_code_generator import ShortCodeGenerator
from urlshortener.domain.entities import ShortUrl
from urlshortener.domain.exceptions import CollisionError, InvalidExpiryError, InvalidUrlError
from urlshortener.domain.repository import UrlRepository

ALLOWED_SCHEMES = {"http", "https"}
MAX_URL_LENGTH = 2048
MAX_COLLISION_ATTEMPTS = 5


class CreateShortUrlService:
    """FR1 (create) + FR4 (expiry, creation side).

    URL validation uses an allowlist (only http/https), not a blocklist of
    dangerous schemes — an allowlist is both simpler and strictly safer, since
    a blocklist can miss variants (JAVASCRIPT:, vbscript:, file:, etc.).
    """

    def __init__(
        self,
        repository: UrlRepository,
        code_generator: ShortCodeGenerator,
        max_collision_attempts: int = MAX_COLLISION_ATTEMPTS,
    ) -> None:
        self._repository = repository
        self._code_generator = code_generator
        self._max_collision_attempts = max_collision_attempts

    def execute(
        self,
        long_url: str,
        now: datetime,
        expires_at: datetime | None = None,
    ) -> ShortUrl:
        self._validate_url(long_url)
        if expires_at is not None:
            self._validate_expiry(expires_at, now)

        last_error: CollisionError | None = None
        for _ in range(self._max_collision_attempts):
            code = self._code_generator.generate()
            short_url = ShortUrl(
                code=code,
                long_url=long_url,
                created_at=now,
                expires_at=expires_at,
            )
            try:
                self._repository.save(short_url)
                return short_url
            except CollisionError as exc:
                last_error = exc
        raise last_error

    def _validate_url(self, long_url: str) -> None:
        if len(long_url) > MAX_URL_LENGTH:
            raise InvalidUrlError(long_url, f"exceeds maximum length of {MAX_URL_LENGTH}")
        parsed = urlparse(long_url)
        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            raise InvalidUrlError(long_url, f"scheme must be one of {sorted(ALLOWED_SCHEMES)}")
        if not parsed.netloc:
            raise InvalidUrlError(long_url, "missing host")

    def _validate_expiry(self, expires_at: datetime, now: datetime) -> None:
        if expires_at <= now:
            raise InvalidExpiryError(expires_at, "must be in the future")
