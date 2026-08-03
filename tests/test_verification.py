from __future__ import annotations

from pathlib import Path

from pp_aipp.verification import (
    CheckStatus,
    VerificationCheck,
    VerificationReport,
    write_html,
    write_json,
    write_markdown,
)


def sample_report() -> VerificationReport:
    return VerificationReport(
        version="3.0.0-alpha.6",
        started_at="2026-08-03T00:00:00+00:00",
        finished_at="2026-08-03T00:00:01+00:00",
        checks=[VerificationCheck("tests", CheckStatus.PASSED, 1.0, return_code=0)],
        environment={"python": "3.11"},
    )


def test_report_passes_when_all_checks_pass_or_skip() -> None:
    report = sample_report()
    report.checks.append(VerificationCheck("optional", CheckStatus.SKIPPED, 0.0))
    assert report.passed
    assert report.status == "PASSED"


def test_report_fails_when_one_check_fails() -> None:
    report = sample_report()
    report.checks.append(VerificationCheck("lint", CheckStatus.FAILED, 0.2, return_code=1))
    assert not report.passed
    assert report.status == "FAILED"


def test_writers_create_all_report_formats(tmp_path: Path) -> None:
    report = sample_report()
    assert write_json(report, tmp_path / "report.json").exists()
    assert write_markdown(report, tmp_path / "report.md").exists()
    assert write_html(report, tmp_path / "report.html").exists()
    assert '"status": "PASSED"' in (tmp_path / "report.json").read_text(encoding="utf-8")
    assert "PP-AIPP Verification Report" in (tmp_path / "report.md").read_text(encoding="utf-8")
