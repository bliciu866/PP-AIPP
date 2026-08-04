from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS recipes (
    id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL,
    recipe_id TEXT NOT NULL,
    title TEXT NOT NULL,
    meal TEXT NOT NULL,
    servings INTEGER NOT NULL CHECK(servings > 0),
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    meal_prep TEXT NOT NULL DEFAULT '',
    chef_tip TEXT NOT NULL DEFAULT '',
    ingredient_swap TEXT NOT NULL DEFAULT '',
    provenance TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(book_id, recipe_id)
);
CREATE TABLE IF NOT EXISTS ingredients (
    id TEXT PRIMARY KEY,
    recipe_pk TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    name TEXT NOT NULL,
    quantity REAL NOT NULL CHECK(quantity >= 0),
    unit TEXT NOT NULL,
    source_ref TEXT,
    preparation_state TEXT,
    provenance TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(recipe_pk, position)
);
CREATE TABLE IF NOT EXISTS method_steps (
    id TEXT PRIMARY KEY,
    recipe_pk TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    number INTEGER NOT NULL CHECK(number > 0),
    text TEXT NOT NULL,
    provenance TEXT NOT NULL,
    UNIQUE(recipe_pk, number)
);
CREATE TABLE IF NOT EXISTS nutrition (
    id TEXT PRIMARY KEY,
    recipe_pk TEXT NOT NULL UNIQUE REFERENCES recipes(id) ON DELETE CASCADE,
    energy_kcal REAL NOT NULL CHECK(energy_kcal >= 0),
    protein_g REAL NOT NULL CHECK(protein_g >= 0),
    carbohydrate_g REAL NOT NULL CHECK(carbohydrate_g >= 0),
    fat_g REAL NOT NULL CHECK(fat_g >= 0),
    fibre_g REAL NOT NULL CHECK(fibre_g >= 0),
    serving_basis TEXT NOT NULL,
    locked INTEGER NOT NULL CHECK(locked IN (0, 1)),
    provenance TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS recipe_badges (
    recipe_pk TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    badge TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY(recipe_pk, badge)
);
CREATE TABLE IF NOT EXISTS qa_records (
    id TEXT PRIMARY KEY,
    recipe_pk TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    provenance TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    recipe_pk TEXT REFERENCES recipes(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    path TEXT NOT NULL,
    alt_text TEXT NOT NULL DEFAULT '',
    width_px INTEGER,
    height_px INTEGER,
    checksum TEXT,
    licence TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_recipes_book ON recipes(book_id, recipe_id);
CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(name);
CREATE INDEX IF NOT EXISTS idx_qa_recipe ON qa_records(recipe_pk, severity);
CREATE INDEX IF NOT EXISTS idx_assets_recipe ON assets(recipe_pk, kind);
"""


class DomainDatabase:
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

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(sql, params).fetchone()
            return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]

    def health(self) -> dict[str, int | str]:
        tables = ("recipes", "ingredients", "method_steps", "nutrition", "recipe_badges", "qa_records", "assets")
        with self.connect() as connection:
            counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}
        return {"status": "READY", "database": str(self.path.resolve()), **counts}


def encode_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def decode_json(value: str | None) -> dict:
    return json.loads(value or "{}")
