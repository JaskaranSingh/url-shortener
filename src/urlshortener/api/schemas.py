from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class CreateUrlRequest(BaseModel):
    long_url: str = Field(..., description="The destination URL to shorten")
    expires_at: datetime | None = Field(
        None, description="Optional expiry; must be timezone-aware and in the future"
    )

    @field_validator("expires_at", mode="before")
    @classmethod
    def _treat_empty_string_as_absent(cls, value: object) -> object:
        # Some clients (HTML forms, simple date pickers) serialize "no value"
        # as "" rather than omitting the key or sending null. "" isn't a
        # valid datetime, so without this it fails Pydantic's own parsing
        # before our validation ever runs - treat it the same as absent.
        return None if value == "" else value

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
