from pathlib import Path


def test_ci_workflow_contains_required_jobs() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "quality:" in workflow
    assert "package-smoke:" in workflow
    assert "release-gate:" in workflow
    assert "--cov-fail-under=70" in workflow


def test_mobile_workflow_copy_is_identical() -> None:
    hidden = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    visible = Path("GITHUB_ACTIONS_CI.yml").read_text(encoding="utf-8")
    assert hidden == visible
