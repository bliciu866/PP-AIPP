import json
from pathlib import Path

import pytest

from pp_aipp.gold_master import GoldMasterProject, GoldMasterSchema


def test_create_project_builds_standard_structure(tmp_path: Path) -> None:
    project = GoldMasterProject.create(tmp_path / "book", "30 Days Fat Loss")
    assert project.validate().valid
    assert json.loads((project.root / "project.json").read_text())["name"] == "30 Days Fat Loss"
    for directory in GoldMasterSchema.REQUIRED_DIRECTORIES:
        assert (project.root / directory).is_dir()

def test_import_source_copies_docx_and_writes_manifest(tmp_path: Path) -> None:
    source = tmp_path / "Gold_Master.docx"
    source.write_bytes(b"controlled-source")
    project = GoldMasterProject.create(tmp_path / "project")
    result = project.import_source(source)
    assert result.validation.valid
    assert result.imported_source.read_bytes() == b"controlled-source"
    assert len(result.manifest.source_sha256) == 64

def test_import_rejects_non_docx(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("no")
    project = GoldMasterProject.create(tmp_path / "project")
    with pytest.raises(ValueError, match=".docx"):
        project.import_source(source)
