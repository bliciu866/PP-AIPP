"""Manifest generation for imported controlled sources."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GoldMasterManifest:
    schema_version: str
    source_name: str
    source_sha256: str
    source_size: int
    imported_at: str

    @classmethod
    def from_source(cls, source: str | Path, schema_version: str) -> GoldMasterManifest:
        path = Path(source)
        return cls(schema_version, path.name, hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size, datetime.now(UTC).isoformat())

    def write(self, destination: str | Path) -> Path:
        path = Path(destination)
        path.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
        return path
