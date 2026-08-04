from pathlib import Path

import pytest

from pp_aipp.core.workspace import WorkspaceManager


def test_create_workspace(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path / "workspaces")
    workspace = manager.create("project-physique")
    assert workspace.root.exists()
    assert (workspace.root / "books").is_dir()
    assert manager.list() == ["project-physique"]


def test_reject_invalid_slug(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path / "workspaces")
    with pytest.raises(ValueError):
        manager.create("Bad Name")
