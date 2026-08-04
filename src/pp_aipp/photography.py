"""Validated photography asset import and coverage reporting."""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
RECIPE_IMAGE = re.compile(r"^(PP-R\d{3})(?:_hero)?$", re.IGNORECASE)
TARGET_RATIO = 4 / 5
RATIO_TOLERANCE = 0.035


@dataclass(frozen=True, slots=True)
class PhotoAsset:
    recipe_id: str
    filename: str
    width: int
    height: int
    aspect_ratio: float
    status: str
    note: str


@dataclass(frozen=True, slots=True)
class PhotoImportResult:
    images_dir: Path
    report_path: Path
    imported: int
    ready: int
    needs_crop: int
    rejected: int
    missing: int


def _inspect(path: Path, recipe_id: str) -> PhotoAsset:
    with Image.open(path) as image:
        width, height = image.size
    ratio = width / height if height else 0
    ratio_ok = abs(ratio - TARGET_RATIO) <= RATIO_TOLERANCE
    resolution_ok = width >= 1200 and height >= 1500
    if not ratio_ok:
        status, note = "NEEDS_CROP", "Crop to portrait 4:5"
    elif not resolution_ok:
        status, note = "LOW_RESOLUTION", "Recommended minimum: 1200 x 1500 px"
    else:
        status, note = "READY", "4:5 production asset"
    return PhotoAsset(recipe_id, path.name, width, height, round(ratio, 4), status, note)


def import_photo_assets(
    project_root: str | Path,
    source_folder: str | Path,
    *,
    recipe_ids: list[str] | None = None,
) -> PhotoImportResult:
    """Import named recipe photos and write a deterministic readiness report."""
    root = Path(project_root).expanduser().resolve()
    source = Path(source_folder).expanduser().resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Photo folder not found: {source}")
    images_dir = root / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    expected = [value.upper() for value in (recipe_ids or [f"PP-R{i:03d}" for i in range(1, 81)])]

    imported: list[PhotoAsset] = []
    rejected: list[dict[str, str]] = []
    seen: set[str] = set()
    for candidate in sorted(source.rglob("*")):
        if not candidate.is_file() or candidate.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        match = RECIPE_IMAGE.match(candidate.stem)
        if not match:
            rejected.append({"filename": candidate.name, "reason": "Filename must use PP-R001 format"})
            continue
        recipe_id = match.group(1).upper()
        if recipe_id not in expected:
            rejected.append({"filename": candidate.name, "reason": "Recipe ID is outside this project"})
            continue
        if recipe_id in seen:
            rejected.append({"filename": candidate.name, "reason": "Duplicate recipe image"})
            continue
        try:
            asset = _inspect(candidate, recipe_id)
        except (OSError, ValueError):
            rejected.append({"filename": candidate.name, "reason": "Unreadable or invalid image"})
            continue
        destination = images_dir / f"{recipe_id}{candidate.suffix.lower()}"
        shutil.copy2(candidate, destination)
        imported.append(PhotoAsset(
            asset.recipe_id, destination.name, asset.width, asset.height,
            asset.aspect_ratio, asset.status, asset.note,
        ))
        seen.add(recipe_id)

    present = {item.recipe_id for item in imported}
    missing = [recipe_id for recipe_id in expected if recipe_id not in present]
    report_path = root / "qa" / "photography_readiness_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    ready = sum(item.status == "READY" for item in imported)
    needs_crop = sum(item.status != "READY" for item in imported)
    report_path.write_text(json.dumps({
        "schema_version": 1,
        "expected_images": len(expected),
        "imported_images": len(imported),
        "ready_images": ready,
        "images_needing_attention": needs_crop,
        "rejected_files": len(rejected),
        "missing_images": len(missing),
        "assets": [asdict(item) for item in imported],
        "rejected": rejected,
        "missing_recipe_ids": missing,
    }, indent=2) + "\n", encoding="utf-8")
    return PhotoImportResult(
        images_dir, report_path, len(imported), ready, needs_crop, len(rejected), len(missing)
    )
