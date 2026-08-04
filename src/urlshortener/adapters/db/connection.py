import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def create_connection(db_path: str) -> sqlite3.Connection:
    """Open a SQLite connection, enable FK enforcement, and apply the schema.

    PRAGMA foreign_keys is a per-connection setting in SQLite (not persisted
    in the file), so it must be set every time a connection is opened, not
    just once at database creation.

    check_same_thread=False: FastAPI runs sync path operations and sync
    dependencies via anyio's threadpool, which does not guarantee a single
    request's dependency resolution and endpoint execution land on the same
    OS thread. This connection is still only ever used sequentially within
    one request's lifecycle (created fresh per-request, closed at the end -
    see api/dependencies.py), never concurrently by two threads at once, so
    disabling Python's same-thread check is safe here, not just silencing it.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text())
    return conn
