import base64
import io
import json
import sqlite3
import subprocess
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from pp_aipp.ai_photography import (
    RecipePhotoBrief,
    build_recipe_photo_prompt,
    generate_recipe_photos,
)


def _project(tmp_path):
    root = tmp_path / "project"
    database = root / "data" / "project.sqlite3"
    database.parent.mkdir(parents=True)
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE recipes (
            id INTEGER PRIMARY KEY,
            recipe_id TEXT,
            title TEXT,
            meal TEXT
        );
        CREATE TABLE ingredients (
            recipe_pk INTEGER,
            position INTEGER,
            name TEXT
        );
        INSERT INTO recipes VALUES
            (1, 'PP-R001', 'Blueberry Overnight Oats', 'Breakfast'),
            (2, 'PP-R002', 'Lemon Chicken', 'Dinner');
        INSERT INTO ingredients VALUES
            (1, 1, 'Porridge oats'),
            (1, 2, 'Blueberries'),
            (2, 1, 'Chicken breast'),
            (2, 2, 'Fresh lemon');
        """
    )
    connection.commit()
    connection.close()
    return root


def _encoded_image():
    stream = io.BytesIO()
    Image.new("RGB", (1024, 1536), "#406b45").save(stream, format="PNG")
    return base64.b64encode(stream.getvalue()).decode("ascii")


class _FakeImages:
    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            data=[SimpleNamespace(b64_json=_encoded_image())]
        )


def test_prompt_is_recipe_specific_and_forbids_text():
    prompt = build_recipe_photo_prompt(
        RecipePhotoBrief(
            "PP-R001",
            "Blueberry Overnight Oats",
            "Breakfast",
            ("Porridge oats", "Blueberries"),
        )
    )

    assert "Blueberry Overnight Oats" in prompt
    assert "Porridge oats, Blueberries" in prompt
    assert "No people" in prompt
    assert "watermarks" in prompt


def test_campaign_generates_missing_images_and_resumes(tmp_path):
    project = _project(tmp_path)
    images = _FakeImages()
    client = SimpleNamespace(images=images)

    first = generate_recipe_photos(
        project, "test-key", batch_size=1, client=client, sleep=lambda _: None
    )

    assert first.generated == 1
    assert first.remaining == 1
    assert len(images.calls) == 1
    assert images.calls[0]["model"] == "gpt-image-2"
    assert images.calls[0]["size"] == "1024x1536"
    with Image.open(project / "images" / "PP-R001.png") as photo:
        assert photo.size == (1200, 1500)

    second = generate_recipe_photos(
        project, "test-key", batch_size=1, client=client, sleep=lambda _: None
    )

    assert second.generated == 1
    assert second.skipped == 1
    assert second.remaining == 0
    assert len(images.calls) == 2


def test_campaign_recovers_staged_image_without_second_api_call(tmp_path):
    project = _project(tmp_path)
    staging = project / "qa" / "ai_photo_staging"
    staging.mkdir(parents=True)
    decoded = base64.b64decode(_encoded_image())
    (staging / "PP-R001.png").write_bytes(decoded)
    images = _FakeImages()

    result = generate_recipe_photos(
        project,
        "test-key",
        batch_size=1,
        client=SimpleNamespace(images=images),
    )

    assert result.generated == 1
    assert not images.calls
    assert (project / "images" / "PP-R001.png").is_file()


def test_local_campaign_uses_runner_and_imports_generated_image(tmp_path, monkeypatch):
    project = _project(tmp_path)
    local_python = tmp_path / "python.exe"
    local_runner = tmp_path / "local_ai_runner.py"
    local_python.touch()
    local_runner.touch()

    def fake_run(command, **kwargs):
        tasks_path = command[command.index("--tasks") + 1]
        for task in json.loads(Path(tasks_path).read_text(encoding="utf-8")):
            Image.new("RGB", (512, 640), "#406b45").save(task["output"], format="PNG")
        return subprocess.CompletedProcess(command, 0, "generated", "")

    monkeypatch.setattr("pp_aipp.ai_photography.subprocess.run", fake_run)

    result = generate_recipe_photos(
        project,
        provider="local",
        batch_size=1,
        local_python=local_python,
        local_runner=local_runner,
    )

    assert result.generated == 1
    assert result.remaining == 1
    assert result.failed == 0
    assert (project / "images" / "PP-R001.png").is_file()
