"""Automatic, resumable recipe photography using local or hosted AI."""
from __future__ import annotations

import base64
import io
import json
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from pp_aipp.photography import SUPPORTED_EXTENSIONS, import_photo_assets


@dataclass(frozen=True, slots=True)
class RecipePhotoBrief:
    recipe_id: str
    title: str
    meal: str
    ingredients: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AIPhotoCampaignResult:
    generated: int
    skipped: int
    failed: int
    remaining: int
    coverage_percent: float
    report_path: Path
    images_dir: Path
    generated_ids: tuple[str, ...]
    failed_ids: tuple[str, ...]


def load_recipe_photo_briefs(database_path: str | Path) -> list[RecipePhotoBrief]:
    import sqlite3

    path = Path(database_path)
    if not path.is_file():
        raise FileNotFoundError(f"Project database not found: {path}")
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT id, recipe_id, title, meal FROM recipes ORDER BY recipe_id"
        ).fetchall()
        briefs = []
        for row in rows:
            ingredients = connection.execute(
                "SELECT name FROM ingredients WHERE recipe_pk = ? ORDER BY position",
                (row["id"],),
            ).fetchall()
            briefs.append(RecipePhotoBrief(
                str(row["recipe_id"]).upper(), str(row["title"]), str(row["meal"] or ""),
                tuple(str(item["name"]) for item in ingredients if item["name"]),
            ))
        return briefs
    finally:
        connection.close()


def build_recipe_photo_prompt(brief: RecipePhotoBrief) -> str:
    ingredients = ", ".join(brief.ingredients[:12]) or "the ingredients implied by the title"
    return (
        "Create a premium editorial food photograph for a professionally published healthy "
        f"recipe book. Recipe: {brief.title}. Meal: {brief.meal or 'meal'}. Visible key "
        f"ingredients: {ingredients}. Show one finished, appetising dish with realistic portions "
        "and ingredient accuracy. Clean modern Project Physique aesthetic, natural window light, "
        "subtle green and neutral styling, restrained props, sharp food detail, shallow depth of "
        "field, portrait composition with the entire dish visible and useful crop space. No people, "
        "hands, packaging, logos, text, letters, labels, watermarks, collages, split screens, or "
        "multiple dishes. Photorealistic commercial food photography."
    )


def _ready_ids(images_dir: Path) -> set[str]:
    if not images_dir.is_dir():
        return set()
    return {
        path.stem.upper() for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    }


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _save_production_image(encoded: str, path: Path) -> None:
    """Decode the API response and normalize it to the publishing 4:5 asset size."""
    with Image.open(io.BytesIO(base64.b64decode(encoded))) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        prepared = ImageOps.fit(
            image,
            (1200, 1500),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        prepared.save(path, format="PNG", optimize=True)


def generate_recipe_photos(
    project_root: str | Path,
    api_key: str = "",
    *,
    batch_size: int = 80,
    quality: str = "low",
    model: str = "gpt-image-2",
    client: Any = None,
    progress_callback: Callable[[int, str], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    provider: str = "openai",
    local_python: str | Path | None = None,
    local_runner: str | Path | None = None,
) -> AIPhotoCampaignResult:
    """Generate only missing recipe photos and import them into the project."""
    if provider not in {"openai", "local"}:
        raise ValueError("Provider must be openai or local.")
    if provider == "openai" and not api_key.strip():
        raise ValueError("An OpenAI API key is required.")
    if not 1 <= batch_size <= 80:
        raise ValueError("Batch size must be between 1 and 80.")
    if quality not in {"low", "medium", "high"}:
        raise ValueError("Quality must be low, medium, or high.")

    root = Path(project_root).expanduser().resolve()
    briefs = load_recipe_photo_briefs(root / "data" / "project.sqlite3")
    if not briefs:
        raise ValueError("No recipes found. Build the book before generating photos.")
    images_dir = root / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    ready_before = _ready_ids(images_dir)
    missing = [brief for brief in briefs if brief.recipe_id not in ready_before]
    selected = missing[:batch_size]
    report_path = root / "qa" / "ai_photography_campaign.json"
    staging = root / "qa" / "ai_photo_staging"
    staging.mkdir(parents=True, exist_ok=True)

    if client is None and selected and provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

    generated_ids: list[str] = []
    failed_ids: list[str] = []
    total = len(selected)

    if provider == "local" and selected:
        python_path = Path(local_python) if local_python else default_local_python()
        runner_path = Path(local_runner) if local_runner else default_local_runner()
        if not python_path.is_file():
            raise FileNotFoundError(
                "Local Free AI is not installed. Run SETUP_LOCAL_AI.bat from the PP-AIPP folder."
            )
        if not runner_path.is_file():
            raise FileNotFoundError(f"Local AI runner not found: {runner_path}")
        tasks_path = staging / "local_ai_tasks.json"
        tasks_path.write_text(json.dumps([
            {
                "recipe_id": brief.recipe_id,
                "prompt": build_recipe_photo_prompt(brief),
                "output": str(staging / f"{brief.recipe_id}.png"),
            }
            for brief in selected if not (staging / f"{brief.recipe_id}.png").is_file()
        ], indent=2), encoding="utf-8")
        if progress_callback:
            progress_callback(5, f"Local Free AI is generating {len(selected)} photos")
        completed = subprocess.run(
            [str(python_path), str(runner_path), "--tasks", str(tasks_path), "--quality", quality],
            capture_output=True, text=True, timeout=max(1800, len(selected) * 900), check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()[-1200:]
            raise RuntimeError(f"Local AI generator failed: {detail}")
    for index, brief in enumerate(selected, start=1):
        staged_path = staging / f"{brief.recipe_id}.png"
        if staged_path.is_file():
            generated_ids.append(brief.recipe_id)
            if progress_callback:
                progress_callback(
                    max(1, round(((index - 1) / max(total, 1)) * 90)),
                    f"Recovering saved image for {brief.recipe_id}",
                )
            continue
        if provider == "local":
            failed_ids.append(brief.recipe_id)
            continue
        if progress_callback:
            progress_callback(
                max(1, round(((index - 1) / max(total, 1)) * 90)),
                f"Generating {brief.recipe_id}: {brief.title}",
            )
        error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = client.images.generate(
                    model=model,
                    prompt=build_recipe_photo_prompt(brief),
                    size="1024x1536",
                    quality=quality,
                    output_format="png",
                )
                encoded = response.data[0].b64_json
                if not encoded:
                    raise ValueError("Images API returned no image data.")
                _save_production_image(encoded, staged_path)
                generated_ids.append(brief.recipe_id)
                error = None
                break
            except Exception as exc:  # noqa: BLE001 - SDK errors vary between releases.
                error = exc
                status = getattr(exc, "status_code", None)
                if attempt == 3 or (status is not None and status != 429 and status < 500):
                    break
                sleep(2 ** (attempt - 1))
        if error is not None:
            failed_ids.append(brief.recipe_id)
        _write_report(report_path, {
            "schema_version": 1,
            "updated_utc": datetime.now(UTC).isoformat(),
            "model": model if provider == "openai" else "stable-diffusion-v1-5-local",
            "provider": provider,
            "quality": quality,
            "requested": total,
            "generated_ids": generated_ids,
            "failed_ids": failed_ids,
            "status": "RUNNING",
        })

    if generated_ids:
        import_photo_assets(root, staging, recipe_ids=[brief.recipe_id for brief in briefs])
        for recipe_id in generated_ids:
            (staging / f"{recipe_id}.png").unlink(missing_ok=True)

    ready_after = _ready_ids(images_dir)
    remaining = sum(brief.recipe_id not in ready_after for brief in briefs)
    coverage = round(((len(briefs) - remaining) / len(briefs)) * 100, 1)
    result = AIPhotoCampaignResult(
        len(generated_ids),
        sum(brief.recipe_id in ready_before for brief in briefs),
        len(failed_ids),
        remaining,
        coverage,
        report_path, images_dir, tuple(generated_ids), tuple(failed_ids),
    )
    _write_report(report_path, {
        "schema_version": 1,
        "updated_utc": datetime.now(UTC).isoformat(),
        "model": model if provider == "openai" else "stable-diffusion-v1-5-local",
        "provider": provider,
        "quality": quality,
        "status": "COMPLETE" if remaining == 0 else "PARTIAL",
        **{key: str(value) if isinstance(value, Path) else value for key, value in asdict(result).items()},
    })
    if progress_callback:
        progress_callback(100, f"AI photography batch complete: {len(generated_ids)} generated")
    return result


def application_dir() -> Path:
    """Directory containing the portable app or the source checkout."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def default_local_python() -> Path:
    return application_dir() / ".local-ai" / "Scripts" / "python.exe"


def default_local_runner() -> Path:
    packaged = application_dir() / "local_ai_runner.py"
    if packaged.is_file():
        return packaged
    return application_dir() / "scripts" / "local_ai_runner.py"
