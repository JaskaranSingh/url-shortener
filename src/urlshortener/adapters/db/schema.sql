-- See docs/SCHEMA.md for the design rationale behind every choice here.

CREATE TABLE IF NOT EXISTS urls (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL,
    long_url    TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    expires_at  TEXT,
    deleted_at  TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_urls_code ON urls(code);

CREATE TABLE IF NOT EXISTS clicks (
    id          INTEGER PRIMARY KEY,
    url_id      INTEGER NOT NULL REFERENCES urls(id),
    clicked_at  TEXT NOT NULL,
    referrer    TEXT
);

CREATE INDEX IF NOT EXISTS idx_clicks_url_id ON clicks(url_id);
