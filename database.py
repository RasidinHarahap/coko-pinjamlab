"""SQLite connections with transactions, foreign keys, and closed handles."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path


def database_path():
    return Path(os.environ.get("DB_PATH", str(Path(__file__).parent / "data" / "pinjamlab.sqlite3")))


def dictionary_row(cursor, values):
    row = dict(zip((column[0] for column in cursor.description), values))
    for key in ("borrowed_on", "due_on", "returned_on"):
        if row.get(key):
            row[key] = date.fromisoformat(row[key])
    return row


@contextmanager
def connect(write=False):
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = dictionary_row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    try:
        if write:
            conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
