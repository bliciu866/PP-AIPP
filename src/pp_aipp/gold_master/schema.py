"""Validation rules for a PP-AIPP Gold Master project."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    path: Path
    severity: str = "error"

@dataclass(slots=True)
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

class GoldMasterSchema:
    VERSION = "1.0.0"
    REQUIRED_FILES = ("project.json", "manifest.json", "metadata.json")
    REQUIRED_DIRECTORIES = ("manuscript", "assets", "qa", "exports", "build")

    @classmethod
    def validate(cls, root: str | Path) -> ValidationResult:
        project_root = Path(root).expanduser().resolve()
        result = ValidationResult()
        if not project_root.is_dir():
            result.issues.append(ValidationIssue("GM001", "Project directory does not exist", project_root))
            return result
        for name in cls.REQUIRED_FILES:
            path = project_root / name
            if not path.is_file():
                result.issues.append(ValidationIssue("GM002", f"Missing file: {name}", path))
        for name in cls.REQUIRED_DIRECTORIES:
            path = project_root / name
            if not path.is_dir():
                result.issues.append(ValidationIssue("GM003", f"Missing directory: {name}", path))
        return result
