
import pytest

from pp_aipp.desktop.state import BuildStage, DesktopState


def test_desktop_state_defaults():
    state = DesktopState()
    assert state.stage == BuildStage.READY
    assert state.progress == 0


def test_open_project_sets_export_path(tmp_path):
    state = DesktopState()
    result = state.open_project(tmp_path)
    assert result == tmp_path.resolve()
    assert state.project_path == tmp_path.resolve()
    assert state.export_path == tmp_path.resolve() / "exports"
    assert state.stage == BuildStage.PROJECT_OPEN


def test_select_gold_master(tmp_path):
    source = tmp_path / "master.docx"
    source.write_bytes(b"")
    state = DesktopState()
    state.select_gold_master(source)
    assert state.gold_master_path == source.resolve()
    assert state.stage == BuildStage.IMPORTING


def test_progress_validation():
    state = DesktopState()
    with pytest.raises(ValueError):
        state.set_stage(BuildStage.BUILDING, 101, "invalid")
