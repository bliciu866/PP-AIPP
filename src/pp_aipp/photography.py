"""Validated photography asset import and coverage reporting."""
from __future__ import annotations

import csv
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


@dataclass(frozen=True, slots=True)
class PhotoBatchPlan:
    batch_dir: Path
    manifest_path: Path
    readme_path: Path
    batch_number: int
    recipe_ids: tuple[str, ...]
    missing_total: int
    coverage_percent: float


def _expected_ids(recipe_ids: list[str] | None = None) -> list[str]:
    return [value.upper() for value in (recipe_ids or [f"PP-R{i:03d}" for i in range(1, 81)])]


def prepare_next_photo_batch(
    project_root: str | Path,
    *,
    recipe_ids: list[str] | None = None,
    batch_size: int = 10,
) -> PhotoBatchPlan:
    """Create a production folder and manifests for the next missing recipe photos."""
    if not 1 <= batch_size <= 80:
        raise ValueError("Photo batch size must be between 1 and 80")
    root = Path(project_root).expanduser().resolve()
    expected = _expected_ids(recipe_ids)
    inventory = _existing_assets(root / "images", expected)
    ready_ids = {asset.recipe_id for asset in inventory if asset.status == "READY"}
    missing = [recipe_id for recipe_id in expected if recipe_id not in ready_ids]
    selected = missing[:batch_size]
    if not selected:
        raise ValueError("Photography campaign is complete; no missing recipe photos remain.")

    batches_dir = root / "photo_batches"
    batches_dir.mkdir(parents=True, exist_ok=True)
    existing_numbers = []
    for path in batches_dir.glob("Batch_*"):
        match = re.match(r"Batch_(\d+)", path.name)
        if match:
            existing_numbers.append(int(match.group(1)))
    batch_number = max(existing_numbers, default=0) + 1
    batch_dir = batches_dir / (
        f"Batch_{batch_number:03d}_{selected[0]}_to_{selected[-1]}"
    )
    batch_dir.mkdir(parents=True, exist_ok=False)
    csv_path = batch_dir / "PHOTO_BATCH_MANIFEST.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["recipe_id", "required_filename", "status"])
        for recipe_id in selected:
            writer.writerow([recipe_id, f"{recipe_id}.jpg", "MISSING"])

    readme_path = batch_dir / "README.txt"
    readme_path.write_text(
        "PP-AIPP Photography Batch\n"
        "==========================\n\n"
        f"Batch: {batch_number}\n"
        f"Recipes: {selected[0]} to {selected[-1]}\n\n"
        "1. Add one licensed portrait food photo for every listed recipe.\n"
        "2. Use the exact filename from PHOTO_BATCH_MANIFEST.csv.\n"
        "3. Recommended source: at least 1200 x 1500 px.\n"
        "4. In PP-AIPP choose Import Photos and select this folder.\n",
        encoding="utf-8",
    )
    coverage = round((len(ready_ids) / len(expected)) * 100, 1) if expected else 100.0
    manifest = {
        "schema_version": 1,
        "batch_number": batch_number,
        "created_utc": datetime.now(UTC).isoformat(),
        "campaign": "PP-R001-PP-R080",
        "recipe_ids": selected,
        "required_filenames": [f"{recipe_id}.jpg" for recipe_id in selected],
        "missing_total_before_batch": len(missing),
        "coverage_percent_before_batch": coverage,
        "csv_manifest": csv_path.name,
    }
    manifest_path = batch_dir / "photo_batch_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    qa_dir = root / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(manifest_path, qa_dir / "photography_batch_plan.json")
    return PhotoBatchPlan(
        batch_dir, manifest_path, readme_path, batch_number, tuple(selected),
        len(missing), coverage,
    )


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
    expected = _expected_ids(recipe_ids)

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
