import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def create_connection(db_path: str) -> sqlite3.Connection:
    """Open a SQLite connection, enable FK enforcement, and apply the schema.

    PRAGMA foreign_keys is a per-connection setting in SQLite (not persisted
    in the file), so it must be set every time a connection is opened, not
    just once at database creation.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text())
    return conn
