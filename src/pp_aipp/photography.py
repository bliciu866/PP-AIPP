"""Validated photography asset import and coverage reporting."""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image, ImageOps

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
    replaced: int = 0
    auto_prepared: int = 0
    coverage_percent: float = 0
    batch_number: int = 0
    next_missing: tuple[str, ...] = ()


def _inspect(path: Path, recipe_id: str) -> PhotoAsset:
    with Image.open(path) as image:
        width, height = ImageOps.exif_transpose(image).size
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


def _production_crop_size(width: int, height: int) -> tuple[int, int]:
    """Return the largest centred 4:5 crop available inside an image."""
    if width / height > TARGET_RATIO:
        return round(height * TARGET_RATIO), height
    return width, round(width / TARGET_RATIO)


def _prepare(candidate: Path, destination: Path) -> bool:
    """Apply EXIF rotation and a centred 4:5 crop when resolution permits it."""
    with Image.open(candidate) as opened:
        image = ImageOps.exif_transpose(opened)
        crop_width, crop_height = _production_crop_size(*image.size)
        if crop_width < 1200 or crop_height < 1500:
            shutil.copy2(candidate, destination)
            return False
        left = (image.width - crop_width) // 2
        top = (image.height - crop_height) // 2
        prepared = image.crop((left, top, left + crop_width, top + crop_height))
        prepared = prepared.resize((1200, 1500), Image.Resampling.LANCZOS)
        if destination.suffix.lower() in {".jpg", ".jpeg"}:
            prepared.convert("RGB").save(destination, quality=94, optimize=True)
        else:
            prepared.save(destination)
        return image.size != (1200, 1500) or prepared.size != image.size


def _existing_assets(images_dir: Path, expected: list[str]) -> list[PhotoAsset]:
    assets: list[PhotoAsset] = []
    for recipe_id in expected:
        matches = sorted(
            path for path in images_dir.glob(f"{recipe_id}.*")
            if path.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not matches:
            continue
        try:
            assets.append(_inspect(matches[0], recipe_id))
        except (OSError, ValueError):
            assets.append(PhotoAsset(
                recipe_id, matches[0].name, 0, 0, 0, "INVALID", "Unreadable image",
            ))
    return assets


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

    imported_recipe_ids: list[str] = []
    rejected: list[dict[str, str]] = []
    seen: set[str] = set()
    replaced = 0
    auto_prepared = 0
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
            _inspect(candidate, recipe_id)
        except (OSError, ValueError):
            rejected.append({"filename": candidate.name, "reason": "Unreadable or invalid image"})
            continue
        existing = [
            path for path in images_dir.glob(f"{recipe_id}.*")
            if path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        replaced += bool(existing)
        for old_asset in existing:
            old_asset.unlink()
        destination = images_dir / f"{recipe_id}{candidate.suffix.lower()}"
        auto_prepared += _prepare(candidate, destination)
        imported_recipe_ids.append(recipe_id)
        seen.add(recipe_id)

    inventory = _existing_assets(images_dir, expected)
    present = {item.recipe_id for item in inventory}
    missing = [recipe_id for recipe_id in expected if recipe_id not in present]
    qa_dir = root / "qa"
    report_path = qa_dir / "photography_readiness_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    ready = sum(item.status == "READY" for item in inventory)
    needs_crop = sum(item.status != "READY" for item in inventory)
    history_path = qa_dir / "photography_batch_history.json"
    try:
        history = json.loads(history_path.read_text(encoding="utf-8"))
        if not isinstance(history, list):
            history = []
    except (OSError, json.JSONDecodeError):
        history = []
    batch_number = len(history) + 1
    coverage_percent = round((ready / len(expected)) * 100, 1) if expected else 100.0
    next_missing = missing[:10]
    batch_record = {
        "batch_number": batch_number,
        "created_utc": datetime.now(UTC).isoformat(),
        "source_folder": source.name,
        "imported_recipe_ids": imported_recipe_ids,
        "imported": len(imported_recipe_ids),
        "replaced": replaced,
        "auto_prepared": auto_prepared,
        "rejected": len(rejected),
        "ready_total": ready,
        "missing_total": len(missing),
        "coverage_percent": coverage_percent,
    }
    history.append(batch_record)
    history_path.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    report = {
        "schema_version": 3,
        "campaign": "PP-R001-PP-R080",
        "latest_batch_number": batch_number,
        "expected_images": len(expected),
        "imported_this_batch": len(imported_recipe_ids),
        "replaced_this_batch": replaced,
        "auto_prepared_this_batch": auto_prepared,
        "imported_images": len(inventory),
        "ready_images": ready,
        "images_needing_attention": needs_crop,
        "rejected_files": len(rejected),
        "missing_images": len(missing),
        "coverage_percent": coverage_percent,
        "next_missing_recipe_ids": next_missing,
        "batch_history_file": history_path.name,
        "assets": [asdict(item) for item in inventory],
        "rejected": rejected,
        "missing_recipe_ids": missing,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return PhotoImportResult(
        images_dir, report_path, len(imported_recipe_ids), ready, needs_crop,
        len(rejected), len(missing), replaced, auto_prepared, coverage_percent,
        batch_number, tuple(next_missing),
    )
