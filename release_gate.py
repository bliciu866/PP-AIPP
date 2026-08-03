from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        raise AssertionError(f"Required file is missing: {path}")
    return target.read_text(encoding="utf-8")


def main() -> int:
    init_text = read("src/pp_aipp/__init__.py")
    pyproject = read("pyproject.toml")
    changelog = read("CHANGELOG.md")
    workflow = read(".github/workflows/ci.yml")

    init_match = re.search(r'__version__\s*=\s*"([^"]+)"', init_text)
    project_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    if not init_match or not project_match:
        raise AssertionError("Unable to read version declarations")

    runtime_version = init_match.group(1)
    package_version = project_match.group(1)
    normalized_runtime = runtime_version.replace("-alpha.", "a")
    if normalized_runtime != package_version:
        raise AssertionError(
            f"Version mismatch: runtime={runtime_version}, package={package_version}"
        )

    required_workflow_tokens = (
        "python -m pytest",
        "python -m ruff",
        "package-smoke",
        "release-gate",
        "--cov-fail-under=70",
    )
    missing = [token for token in required_workflow_tokens if token not in workflow]
    if missing:
        raise AssertionError(f"CI workflow misses required gates: {missing}")

    if runtime_version not in changelog:
        raise AssertionError(f"CHANGELOG does not mention {runtime_version}")

    print(
        {
            "status": "PASSED",
            "runtime_version": runtime_version,
            "package_version": package_version,
            "workflow": ".github/workflows/ci.yml",
        }
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print({"status": "FAILED", "error": str(exc)}, file=sys.stderr)
        raise SystemExit(1)
