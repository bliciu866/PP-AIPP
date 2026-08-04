from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class CheckStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass(slots=True)
class VerificationCheck:
    name: str
    status: CheckStatus
    duration_seconds: float
    command: list[str] = field(default_factory=list)
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class VerificationReport:
    version: str
    started_at: str
    finished_at: str
    checks: list[VerificationCheck]
    environment: dict[str, str]

    @property
    def passed(self) -> bool:
        return all(check.status in {CheckStatus.PASSED, CheckStatus.SKIPPED} for check in self.checks)

    @property
    def status(self) -> str:
        return "PASSED" if self.passed else "FAILED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "environment": self.environment,
            "checks": [check.to_dict() for check in self.checks],
        }


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())
