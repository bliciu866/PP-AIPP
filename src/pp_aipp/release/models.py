from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PackConfig:
    repository: Path
    output_dir: Path
    milestone: str
    version: str | None = None
    require_clean_git: bool = True
    require_verification: bool = True
    verification_report: Path | None = None
    include_git_bundle: bool = False
    exclude_patterns: tuple[str, ...] = (
        ".git/**",
        ".pytest_cache/**",
        "**/__pycache__/**",
        "*.pyc",
        ".coverage",
        "dist/**",
        "build/**",
        "*.egg-info/**",
        "data/*.sqlite3",
        "logs/**",
        "output/**",
        "reports/**",
    )


@dataclass(slots=True)
class ManifestEntry:
    path: str
    size: int
    sha256: str


@dataclass(slots=True)
class PackResult:
    project: str
    milestone: str
    version: str
    commit: str
    dirty: bool
    verification_status: str
    archive: str
    checksum_file: str
    manifest_json: str
    manifest_text: str
    release_notes: str
    git_bundle: str | None = None
    file_count: int = 0
    total_bytes: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
