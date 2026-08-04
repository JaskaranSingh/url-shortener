# Database Schema

SQLite, accessed via the standard library `sqlite3` module — no ORM. See
`docs/ARCHITECTURE.md` for why: `domain`/`application` must stay free of
storage concerns, and an ORM's model objects create pressure to either leak
into those layers or duplicate the domain entity for no benefit on a
two-table schema. `SqliteUrlRepository` (the sole adapter implementing the
`UrlRepository` port) is the only code that touches this schema directly.

```sql
PRAGMA foreign_keys = ON;  -- SQLite does not enforce FKs unless set per-connection

CREATE TABLE IF NOT EXISTS urls (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL,
    long_url    TEXT NOT NULL,
    created_at  TEXT NOT NULL,   -- ISO 8601 UTC, e.g. 2026-08-04T12:00:00Z
    expires_at  TEXT,            -- ISO 8601 UTC; NULL = no expiry (FR4 default)
    deleted_at  TEXT             -- ISO 8601 UTC; NULL = active (FR5 soft delete)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_urls_code ON urls(code);

CREATE TABLE IF NOT EXISTS clicks (
    id          INTEGER PRIMARY KEY,
    url_id      INTEGER NOT NULL REFERENCES urls(id),
    clicked_at  TEXT NOT NULL,   -- ISO 8601 UTC
    referrer    TEXT             -- nullable; Referer header may be absent
);

CREATE INDEX IF NOT EXISTS idx_clicks_url_id ON clicks(url_id);
```

## Design Decisions

**`id` is a surrogate `INTEGER PRIMARY KEY`, not `AUTOINCREMENT`, and `code` is
a separate unique column** — not the primary key itself. `clicks` will hold
far more rows than `urls` (many clicks per URL), so its foreign key should be
a compact INTEGER rather than a 7-character TEXT value, for join/index
efficiency. `AUTOINCREMENT`'s only extra guarantee over plain `INTEGER
PRIMARY KEY` is preventing id reuse after a row is deleted — moot here, since
`urls` rows are never physically deleted (see soft delete, below), so no id
can ever be freed up to reuse in the first place.

**`code` gets an explicit named `UNIQUE INDEX`, not an inline `UNIQUE`
constraint.** Functionally identical — SQLite auto-creates a unique index for
either — but naming it means it shows up meaningfully in tooling/`EXPLAIN
QUERY PLAN` output instead of as an anonymous `sqlite_autoindex_*`. This is
also what makes `get_by_code` (the redirect hot path, NFR2) an indexed lookup
rather than a table scan, regardless of how large `urls` grows.

**Timestamps are ISO 8601 TEXT, not epoch integers.** SQLite's own recommended
convention; stays human-readable for debugging; and if `urls` ever migrates
to Postgres (NFR7's documented, not-built scaling path), ISO 8601 strings
parse directly into native timestamp columns.

**Soft delete (`deleted_at`), no cascade, clicks always kept.** `FR5`
deletion sets `deleted_at` rather than removing the row; `clicks.url_id` has
no `ON DELETE CASCADE` because there is no delete path to cascade from
anymore. Consequences:
- Redirect and stats lookups treat `deleted_at IS NOT NULL` the same as an
  expired code — `410 Gone`, not `404` — since the code did exist and is now
  intentionally, permanently gone (see `docs/PRD.md` FR2/FR5).
- `SELECT COUNT(*) FROM urls` gives a true "total codes ever generated"
  metric, including deleted ones.
- `get_by_code` does **not** filter on `deleted_at`/`expires_at` in SQL — it
  returns the full row regardless, and the decision of what "unavailable"
  means (expired vs. deleted vs. valid) lives in `RedirectService`
  (application layer), not hidden in a `WHERE` clause. Keeps that business
  rule in the layer that owns business rules.

**No expiry cleanup job.** `FR4` expiry is enforced entirely by comparing
`expires_at` against the current time at read time; since nothing about
expiry involves a physical row removal, a background purge process would add
a moving part for no behavioral benefit.

**No IP address or user-agent column.** `FR3` only requires total clicks,
last-accessed time, and referrer breakdown — storing IPs would be
unrequested PII collection with nothing in the requirements driving it.

**No `CHECK` constraint pinning `code` to exactly 7 characters.** The
generator (`ShortCodeGenerator`, Phase 2) already guarantees this for
auto-generated codes, but `FR6` (custom aliases) is still an open,
deliberately unresolved requirement that may need a different length or
character-set rule — a hard `CHECK` now would risk conflicting with a
decision not yet made.

**`record_click` is keyed by `code`, not internal `id`.** The `UrlRepository`
port and `ShortUrl` domain entity only deal in `code` (the business key);
`id` never appears in `domain`/`application`. The adapter resolves `code ->
id` internally, e.g.:
```sql
INSERT INTO clicks (url_id, clicked_at, referrer)
SELECT id, ?, ? FROM urls WHERE code = ?;
```
