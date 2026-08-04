from datetime import datetime


class DomainError(Exception):
    """Base class for all domain-level errors."""


class UrlNotFoundError(DomainError):
    """Raised when a code has never existed."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"No URL found for code {code!r}")


class UrlExpiredError(DomainError):
    """Raised when a code existed but its expires_at has passed."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"URL for code {code!r} has expired")


class UrlDeletedError(DomainError):
    """Raised when a code existed but was soft-deleted (FR5)."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"URL for code {code!r} has been deleted")


class CollisionError(DomainError):
    """Raised when a generated or requested code already exists."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Code {code!r} already exists")


class InvalidUrlError(DomainError):
    """Raised when a submitted long URL fails validation (e.g. disallowed scheme)."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Invalid URL {url!r}: {reason}")


class InvalidExpiryError(DomainError):
    """Raised when a submitted expires_at fails validation (e.g. already in the past)."""

    def __init__(self, expires_at: datetime, reason: str) -> None:
        self.expires_at = expires_at
        self.reason = reason
        super().__init__(f"Invalid expires_at {expires_at!r}: {reason}")
