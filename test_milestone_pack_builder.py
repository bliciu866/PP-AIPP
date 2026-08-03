from __future__ import annotations

import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

from pp_aipp.release import MilestonePackBuilder, PackBuildError, PackConfig


def make_repo(tmp_path: Path, *, verification: str = "PASSED") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "demo.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n- Initial.\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text(
        '[project]\nname="demo-project"\nversion="1.2.3"\n', encoding="utf-8"
    )
    reports = repo / "reports" / "latest"
    reports.mkdir(parents=True)
    (reports / "verification_report.json").write_text(
        json.dumps({"status": verification}), encoding="utf-8"
    )
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
    return repo


def test_builds_archive_manifest_notes_and_checksum(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    result = MilestonePackBuilder(
        PackConfig(repository=repo, output_dir=tmp_path / "dist", milestone="Milestone A")
    ).build()
    assert Path(result.archive).exists()
    assert Path(result.checksum_file).exists()
    assert result.verification_status == "PASSED"
    assert result.file_count >= 4
    with ZipFile(result.archive) as archive:
        names = archive.namelist()
        assert any(name.endswith("RELEASE_MANIFEST.json") for name in names)
        assert any(name.endswith("RELEASE_NOTES.md") for name in names)
        assert any(name.endswith("src/demo.py") for name in names)


def test_refuses_failed_verification(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, verification="FAILED")
    with pytest.raises(PackBuildError, match="Verification status"):
        MilestonePackBuilder(
            PackConfig(repository=repo, output_dir=tmp_path / "dist", milestone="Milestone A")
        ).build()


def test_refuses_dirty_tree_by_default(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "README.md").write_text("changed\n", encoding="utf-8")
    with pytest.raises(PackBuildError, match="dirty"):
        MilestonePackBuilder(
            PackConfig(repository=repo, output_dir=tmp_path / "dist", milestone="Milestone A")
        ).build()


def test_allows_dirty_tree_when_requested(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "README.md").write_text("changed\n", encoding="utf-8")
    result = MilestonePackBuilder(
        PackConfig(
            repository=repo,
            output_dir=tmp_path / "dist",
            milestone="Milestone A",
            require_clean_git=False,
        )
    ).build()
    assert result.dirty is True
