from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import CheckStatus, VerificationCheck, VerificationReport, utc_now


@dataclass(slots=True)
class VerificationConfig:
    project_root: Path
    report_dir: Path
    gold_master: Path | None = None
    run_lint: bool = True
    run_gold_master: bool = True


class VerificationRunner:
    """Runs reproducible local/CI checks and emits machine-readable reports."""

    def __init__(self, config: VerificationConfig) -> None:
        self.config = config
        self.config.report_dir.mkdir(parents=True, exist_ok=True)

    def _command_check(self, name: str, command: Iterable[str]) -> VerificationCheck:
        cmd = list(command)
        started = time.perf_counter()
        process = subprocess.run(
            cmd,
            cwd=self.config.project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        duration = time.perf_counter() - started
        return VerificationCheck(
            name=name,
            status=CheckStatus.PASSED if process.returncode == 0 else CheckStatus.FAILED,
            duration_seconds=round(duration, 4),
            command=cmd,
            return_code=process.returncode,
            stdout=process.stdout[-20000:],
            stderr=process.stderr[-20000:],
        )

    def _gold_master_check(self) -> VerificationCheck:
        source = self.config.gold_master
        if not self.config.run_gold_master:
            return VerificationCheck("gold_master_integration", CheckStatus.SKIPPED, 0.0, details={"reason": "disabled"})
        if source is None or not source.exists():
            return VerificationCheck(
                "gold_master_integration",
                CheckStatus.SKIPPED,
                0.0,
                details={"reason": "source not supplied", "hint": "use --gold-master PATH"},
            )

        temp_dir = self.config.report_dir / "gold_master"
        temp_dir.mkdir(parents=True, exist_ok=True)
        database = temp_dir / "verification.sqlite3"
        report = temp_dir / "import_report.json"
        if database.exists():
            database.unlink()
        env = os.environ.copy()
        env["PPAIPP__PATHS__PROJECT_DB"] = str(database)
        cmd = [
            sys.executable,
            "-m",
            "pp_aipp.cli",
            "parser",
            "import-docx",
            str(source),
            "--book-id",
            "verification-book",
            "--report",
            str(report),
        ]
        started = time.perf_counter()
        process = subprocess.run(
            cmd,
            cwd=self.config.project_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        duration = time.perf_counter() - started
        details: dict[str, object] = {"source": str(source), "report": str(report)}
        if report.exists():
            try:
                payload = json.loads(report.read_text(encoding="utf-8"))
                import_summary = payload.get("import", {})
                details["import_summary"] = {
                    key: import_summary.get(key)
                    for key in (
                        "book_id",
                        "parsed_recipes",
                        "imported_recipes",
                        "ingredients",
                        "method_steps",
                        "conditional_pass",
                        "errors",
                        "warnings",
                    )
                }
            except json.JSONDecodeError:
                details["report_error"] = "invalid JSON"
        return VerificationCheck(
            "gold_master_integration",
            CheckStatus.PASSED if process.returncode == 0 else CheckStatus.FAILED,
            round(duration, 4),
            command=cmd,
            return_code=process.returncode,
            stdout=process.stdout[-20000:],
            stderr=process.stderr[-20000:],
            details=details,
        )

    def run(self) -> VerificationReport:
        started_at = utc_now()
        checks = [
            self._command_check("compile", [sys.executable, "-m", "compileall", "-q", "src"]),
            self._command_check("unit_and_integration_tests", [sys.executable, "-m", "pytest", "-q"]),
        ]
        if self.config.run_lint:
            checks.append(self._command_check("ruff", [sys.executable, "-m", "ruff", "check", "src", "tests"]))
        checks.append(self._gold_master_check())
        return VerificationReport(
            version="3.0.0-alpha.6",
            started_at=started_at,
            finished_at=utc_now(),
            checks=checks,
            environment={
                "python": platform.python_version(),
                "platform": platform.platform(),
                "executable": sys.executable,
            },
        )
