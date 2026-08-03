from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    brand TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    language TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(project_id, slug)
);
CREATE TABLE IF NOT EXISTS releases (
    id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    UNIQUE(book_id, version)
);
CREATE TABLE IF NOT EXISTS exports (
    id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    format TEXT NOT NULL,
    path TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_books_project ON books(project_id);
CREATE INDEX IF NOT EXISTS idx_releases_book ON releases(book_id);
CREATE INDEX IF NOT EXISTS idx_exports_book ON exports(book_id);
CREATE INDEX IF NOT EXISTS idx_history_entity ON history(entity_type, entity_id);
"""


class RegistryDatabase:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def execute(self, sql: str, params: Iterable[object] = ()) -> None:
        with self.connect() as connection:
            connection.execute(sql, tuple(params))

    def fetchone(self, sql: str, params: Iterable[object] = ()) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(sql, tuple(params)).fetchone()
            return dict(row) if row else None

    def fetchall(self, sql: str, params: Iterable[object] = ()) -> list[dict]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(sql, tuple(params)).fetchall()]

    def health(self) -> dict[str, int | str]:
        counts = {}
        with self.connect() as connection:
            for table in ("projects", "books", "releases", "exports", "history"):
                counts[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return {"status": "READY", "database": str(self.path.resolve()), **counts}


def encode_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def decode_json(value: str | None) -> dict:
    return json.loads(value or "{}")
