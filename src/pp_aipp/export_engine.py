"""Export built books as verified, portable release packages."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import __version__


@dataclass(frozen=True, slots=True)
class ExportResult:
    export_dir: Path
    book_path: Path
    manifest_path: Path
    package_path: Path
    file_count: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_book_package(project_root: str | Path, built_book: str | Path) -> ExportResult:
    """Copy a built DOCX and QA reports into a verified ZIP export package."""
    root = Path(project_root).expanduser().resolve()
    source = Path(built_book).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Built book not found: {source}")
    if source.suffix.lower() != ".docx":
        raise ValueError("Export Engine requires a built DOCX file")

    export_dir = root / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem.removesuffix("_Built")
    book_path = export_dir / f"{stem}_Export.docx"
    manifest_path = export_dir / "export_manifest.json"
    package_path = export_dir / f"{stem}_Export_Package.zip"
    shutil.copy2(source, book_path)

    files: list[tuple[Path, str]] = [(book_path, book_path.name)]
    qa_dir = root / "qa"
    for report_name in ("gold_master_import_report.json", "layout_build_report.json"):
        report = qa_dir / report_name
        if report.is_file():
            files.append((report, f"qa/{report.name}"))

    manifest = {
        "schema_version": 1,
        "application": "PP-AIPP",
        "application_version": __version__,
        "created_utc": datetime.now(UTC).isoformat(),
        "book": book_path.name,
        "files": [
            {"path": archive_name, "bytes": path.stat().st_size, "sha256": _sha256(path)}
            for path, archive_name in files
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    files.append((manifest_path, manifest_path.name))

    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, archive_name in files:
            archive.write(path, archive_name)

    return ExportResult(
        export_dir=export_dir,
        book_path=book_path,
        manifest_path=manifest_path,
        package_path=package_path,
        file_count=len(files),
    )
