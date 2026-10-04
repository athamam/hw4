"""Shared SQLite access for the Campus Customs backend."""

import sqlite3
from pathlib import Path

HW4_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = HW4_DIR / "data"
DB_PATH = DATA_DIR / "campus_customs.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
