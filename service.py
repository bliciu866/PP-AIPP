from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .database import RegistryDatabase, decode_json, encode_json
from .models import BookRecord, ExportRecord, HistoryRecord, ProjectRecord, ReleaseRecord


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectRegistry:
    def __init__(self, database_path: str | Path) -> None:
        self.db = RegistryDatabase(database_path)

    def add_project(self, record: ProjectRecord) -> ProjectRecord:
        self.db.execute(
            "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (record.id, record.slug, record.name, record.brand, record.status.value,
             record.created_at, record.updated_at, encode_json(record.metadata)),
        )
        self._history("project", record.id, "CREATED", {"slug": record.slug})
        return record

    def get_project(self, slug: str) -> dict | None:
        row = self.db.fetchone("SELECT * FROM projects WHERE slug = ?", (slug,))
        return self._decode(row)

    def list_projects(self) -> list[dict]:
        return [self._decode(row) for row in self.db.fetchall("SELECT * FROM projects ORDER BY created_at")]

    def add_book(self, record: BookRecord) -> BookRecord:
        self.db.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (record.id, record.project_id, record.slug, record.title, record.language,
             record.status.value, record.created_at, record.updated_at,
             encode_json(record.metadata)),
        )
        self._history("book", record.id, "CREATED", {"slug": record.slug})
        return record

    def list_books(self, project_slug: str | None = None) -> list[dict]:
        if project_slug:
            rows = self.db.fetchall(
                "SELECT b.* FROM books b JOIN projects p ON p.id=b.project_id WHERE p.slug=? ORDER BY b.created_at",
                (project_slug,),
            )
        else:
            rows = self.db.fetchall("SELECT * FROM books ORDER BY created_at")
        return [self._decode(row) for row in rows]

    def add_release(self, record: ReleaseRecord) -> ReleaseRecord:
        self.db.execute(
            "INSERT INTO releases VALUES (?, ?, ?, ?, ?)",
            (record.id, record.book_id, record.version, record.notes, record.created_at),
        )
        self._history("book", record.book_id, "RELEASE_CREATED", {"version": record.version})
        return record

    def add_export(self, record: ExportRecord) -> ExportRecord:
        self.db.execute(
            "INSERT INTO exports VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (record.id, record.book_id, record.format, record.path, record.status.value,
             record.created_at, record.completed_at, encode_json(record.metadata)),
        )
        self._history("book", record.book_id, "EXPORT_RECORDED", {"format": record.format})
        return record

    def history(self, entity_type: str | None = None, entity_id: str | None = None) -> list[dict]:
        sql = "SELECT * FROM history"
        params: list[str] = []
        clauses = []
        if entity_type:
            clauses.append("entity_type = ?")
            params.append(entity_type)
        if entity_id:
            clauses.append("entity_id = ?")
            params.append(entity_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at"
        return [self._decode(row) for row in self.db.fetchall(sql, params)]

    def summary(self) -> dict:
        return self.db.health()

    def _history(self, entity_type: str, entity_id: str, action: str, payload: dict) -> None:
        record = HistoryRecord(entity_type=entity_type, entity_id=entity_id, action=action, payload=payload)
        self.db.execute(
            "INSERT INTO history VALUES (?, ?, ?, ?, ?, ?)",
            (record.id, record.entity_type, record.entity_id, record.action,
             encode_json(record.payload), record.created_at),
        )

    @staticmethod
    def _decode(row: dict | None) -> dict | None:
        if row is None:
            return None
        result = dict(row)
        for key in ("metadata_json", "payload_json"):
            if key in result:
                result[key.removesuffix("_json")] = decode_json(result.pop(key))
        return result
