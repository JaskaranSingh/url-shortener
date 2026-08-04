from __future__ import annotations

import sqlite3
from datetime import datetime

from urlshortener.domain.entities import ShortUrl, UrlStats
from urlshortener.domain.exceptions import CollisionError
from urlshortener.domain.repository import UrlRepository

_NONE_REFERRER_KEY = "(none)"


class SqliteUrlRepository(UrlRepository):
    """Concrete adapter implementing UrlRepository against SQLite.

    Takes an already-configured connection (see adapters/db/connection.py) -
    connection/schema lifecycle is the caller's concern, not this class's.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def save(self, short_url: ShortUrl) -> None:
        try:
            self._conn.execute(
                """
                INSERT INTO urls (code, long_url, created_at, expires_at, deleted_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    short_url.code,
                    short_url.long_url,
                    short_url.created_at.isoformat(),
                    _to_iso(short_url.expires_at),
                    _to_iso(short_url.deleted_at),
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise CollisionError(short_url.code) from exc

    def get_by_code(self, code: str) -> ShortUrl | None:
        row = self._conn.execute(
            "SELECT code, long_url, created_at, expires_at, deleted_at FROM urls WHERE code = ?",
            (code,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_entity(row)

    def delete(self, code: str, deleted_at: datetime) -> None:
        self._conn.execute(
            "UPDATE urls SET deleted_at = ? WHERE code = ? AND deleted_at IS NULL",
            (deleted_at.isoformat(), code),
        )
        self._conn.commit()

    def record_click(self, code: str, clicked_at: datetime, referrer: str | None) -> None:
        self._conn.execute(
            """
            INSERT INTO clicks (url_id, clicked_at, referrer)
            SELECT id, ?, ? FROM urls WHERE code = ?
            """,
            (clicked_at.isoformat(), referrer, code),
        )
        self._conn.commit()

    def get_stats(self, code: str) -> UrlStats | None:
        url_row = self._conn.execute("SELECT id FROM urls WHERE code = ?", (code,)).fetchone()
        if url_row is None:
            return None
        url_id = url_row["id"]

        total_clicks = self._conn.execute(
            "SELECT COUNT(*) AS count FROM clicks WHERE url_id = ?", (url_id,)
        ).fetchone()["count"]

        last_accessed_raw = self._conn.execute(
            "SELECT MAX(clicked_at) AS last_accessed FROM clicks WHERE url_id = ?", (url_id,)
        ).fetchone()["last_accessed"]
        last_accessed = datetime.fromisoformat(last_accessed_raw) if last_accessed_raw else None

        referrer_rows = self._conn.execute(
            "SELECT referrer, COUNT(*) AS count FROM clicks WHERE url_id = ? GROUP BY referrer",
            (url_id,),
        ).fetchall()
        referrer_breakdown = {
            (row["referrer"] if row["referrer"] is not None else _NONE_REFERRER_KEY): row["count"]
            for row in referrer_rows
        }

        return UrlStats(
            code=code,
            total_clicks=total_clicks,
            last_accessed=last_accessed,
            referrer_breakdown=referrer_breakdown,
        )


def _to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _row_to_entity(row: sqlite3.Row) -> ShortUrl:
    return ShortUrl(
        code=row["code"],
        long_url=row["long_url"],
        created_at=datetime.fromisoformat(row["created_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
        deleted_at=datetime.fromisoformat(row["deleted_at"]) if row["deleted_at"] else None,
    )
