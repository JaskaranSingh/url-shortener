from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class CreateUrlRequest(BaseModel):
    long_url: str = Field(..., description="The destination URL to shorten")
    expires_at: datetime | None = Field(
        None, description="Optional expiry; must be timezone-aware and in the future"
    )

    @field_validator("expires_at")
    @classmethod
    def _require_timezone_aware_and_normalize_to_utc(
        cls, value: datetime | None
    ) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("expires_at must include a timezone offset")
        # Any offset is accepted from the client (e.g. +05:30 is a perfectly
        # valid instant), but docs/SCHEMA.md decided all stored timestamps
        # are UTC - normalize here, at the API boundary, rather than storing
        # whatever offset the client happened to send.
        return value.astimezone(UTC) if value is not None else None


class CreateUrlResponse(BaseModel):
    code: str
    short_url: str
    long_url: str
    created_at: datetime
    expires_at: datetime | None
