"""Creation and deterministic import of Gold Master source documents."""
from __future__ import annotations
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from .manifest import GoldMasterManifest
from .schema import GoldMasterSchema, ValidationResult

@dataclass(frozen=True, slots=True)
class ImportResult:
    project_root: Path
    imported_source: Path
    manifest: GoldMasterManifest
    validation: ValidationResult

class GoldMasterProject:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()

    @classmethod
    def create(cls, root: str | Path, name: str | None = None) -> "GoldMasterProject":
        project = cls(root)
        project.root.mkdir(parents=True, exist_ok=True)
        for directory in GoldMasterSchema.REQUIRED_DIRECTORIES:
            (project.root / directory).mkdir(exist_ok=True)
        project_name = name or project.root.name
        project._write_json("project.json", {"name": project_name, "schema_version": GoldMasterSchema.VERSION})
        project._write_json("metadata.json", {"title": project_name, "status": "Gold Master Candidate"})
        project._write_json(
            "manifest.json",
            {"schema_version": GoldMasterSchema.VERSION, "source_name": None},
        )
        return project

    def import_source(self, source: str | Path) -> ImportResult:
        source_path = Path(source).expanduser().resolve()
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        if source_path.suffix.lower() != ".docx":
            raise ValueError("Gold Master source must be a .docx document")
        if not self.root.exists():
            self.create(self.root)
        else:
            for directory in GoldMasterSchema.REQUIRED_DIRECTORIES:
                (self.root / directory).mkdir(parents=True, exist_ok=True)
        destination = self.root / "manuscript" / source_path.name
        shutil.copy2(source_path, destination)
        manifest = GoldMasterManifest.from_source(destination, GoldMasterSchema.VERSION)
        manifest.write(self.root / "manifest.json")
        if not (self.root / "project.json").exists():
            self._write_json("project.json", {"name": self.root.name, "schema_version": GoldMasterSchema.VERSION})
        if not (self.root / "metadata.json").exists():
            self._write_json("metadata.json", {"title": self.root.name, "status": "Gold Master Candidate"})
        validation = self.validate()
        return ImportResult(self.root, destination, manifest, validation)

    def validate(self) -> ValidationResult:
        return GoldMasterSchema.validate(self.root)

    def _write_json(self, name: str, payload: dict[str, Any]) -> None:
        (self.root / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
