from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class BuildStage(StrEnum):
    READY = "Ready"
    PROJECT_OPEN = "Project open"
    IMPORTING = "Importing Gold Master"
    VALIDATING = "Validating"
    BUILDING = "Building book"
    EXPORTING = "Exporting"
    COMPLETE = "Complete"
    FAILED = "Failed"


@dataclass(slots=True)
class DesktopState:
    project_path: Path | None = None
    gold_master_path: Path | None = None
    export_path: Path | None = None
    stage: BuildStage = BuildStage.READY
    progress: int = 0
    messages: list[str] = field(default_factory=list)

    def set_stage(self, stage: BuildStage, progress: int, message: str) -> None:
        if not 0 <= progress <= 100:
            raise ValueError("progress must be between 0 and 100")
        self.stage = stage
        self.progress = progress
        self.messages.append(message)

    def open_project(self, path: str | Path) -> Path:
        resolved = Path(path).expanduser().resolve()
        self.project_path = resolved
        self.export_path = resolved / "exports"
        self.set_stage(BuildStage.PROJECT_OPEN, 5, f"Project opened: {resolved}")
        return resolved

    def select_gold_master(self, path: str | Path) -> Path:
        resolved = Path(path).expanduser().resolve()
        self.gold_master_path = resolved
        self.set_stage(BuildStage.IMPORTING, 10, f"Gold Master selected: {resolved.name}")
        return resolved
