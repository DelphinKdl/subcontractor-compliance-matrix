"""SQLite schema and connection helper for the compliance matrix demo."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "compliance.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS subcontractors (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    trade TEXT NOT NULL,
    scope_of_work TEXT NOT NULL,
    pm_email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    subcontractor_id INTEGER NOT NULL REFERENCES subcontractors(id),
    doc_type TEXT NOT NULL,
    expiration_date TEXT NOT NULL
);
"""

DOC_TYPES = ["General Liability Insurance", "Workers' Compensation", "Safety Certification"]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
