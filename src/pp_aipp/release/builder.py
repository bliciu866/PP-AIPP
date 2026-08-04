from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .models import ManifestEntry, PackConfig, PackResult


class PackBuildError(RuntimeError):
    """Raised when a release pack cannot satisfy its release gate."""


class MilestonePackBuilder:
    """Builds a reproducible milestone package from the current repository."""

    def __init__(self, config: PackConfig) -> None:
        self.config = config
        self.repository = config.repository.resolve()
        self.output_dir = config.output_dir.resolve()
        self.warnings: list[str] = []

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _run_git(self, *args: str) -> str:
        process = subprocess.run(
            ["git", "-C", str(self.repository), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode != 0:
            raise PackBuildError(process.stderr.strip() or "Git command failed")
        return process.stdout.strip()

    def _git_state(self) -> tuple[str, bool]:
        if not (self.repository / ".git").exists():
            self.warnings.append("Repository has no .git directory; commit recorded as UNKNOWN.")
            return "UNKNOWN", False
        commit = self._run_git("rev-parse", "--short=12", "HEAD")
        dirty = bool(self._run_git("status", "--porcelain"))
        if dirty and self.config.require_clean_git:
            raise PackBuildError("Git working tree is dirty. Commit or use --allow-dirty.")
        return commit, dirty

    def _metadata(self) -> tuple[str, str]:
        pyproject = self.repository / "pyproject.toml"
        if not pyproject.exists():
            raise PackBuildError("pyproject.toml is missing")
        with pyproject.open("rb") as handle:
            project = tomllib.load(handle).get("project", {})
        name = str(project.get("name", "pp-aipp"))
        version = self.config.version or str(project.get("version", ""))
        if not version:
            raise PackBuildError("Project version is missing")
        return name, version

    def _verification_status(self) -> str:
        report = self.config.verification_report
        candidates = [
            report,
            self.repository / "reports" / "latest" / "verification_report.json",
            self.repository / "reports" / "k0.7" / "verification_report.json",
            self.repository / "RELEASE_GATE_K0.7.json",
        ]
        selected = next((path for path in candidates if path and path.exists()), None)
        if selected is None:
            if self.config.require_verification:
                raise PackBuildError("No verification report found. Run `pp-aipp verify` first.")
            self.warnings.append("Verification report not supplied; release gate bypassed.")
            return "NOT_CHECKED"
        try:
            payload = json.loads(selected.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PackBuildError(f"Invalid verification JSON: {selected}") from exc
        status = str(payload.get("status") or payload.get("release_gate") or "UNKNOWN").upper()
        if status not in {"PASSED", "PASS", "SUCCESS"} and self.config.require_verification:
            raise PackBuildError(f"Verification status is {status}, not PASSED")
        return "PASSED" if status in {"PASSED", "PASS", "SUCCESS"} else status

    def _excluded(self, relative: str) -> bool:
        normalized = relative.replace(os.sep, "/")
        return any(fnmatch.fnmatch(normalized, pattern) for pattern in self.config.exclude_patterns)

    def _source_files(self) -> list[Path]:
        files: list[Path] = []
        for path in sorted(self.repository.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(self.repository).as_posix()
            if self._excluded(relative):
                continue
            files.append(path)
        if not files:
            raise PackBuildError("No files selected for the milestone package")
        return files

    def _release_notes_text(self, project: str, version: str, commit: str, verification: str) -> str:
        changelog = self.repository / "CHANGELOG.md"
        changelog_text = changelog.read_text(encoding="utf-8") if changelog.exists() else ""
        return "\n".join(
            [
                f"# {project} {version} — {self.config.milestone}",
                "",
                f"- Commit: `{commit}`",
                f"- Verification: **{verification}**",
                f"- Built: {datetime.now(UTC).isoformat()}",
                "",
                "## Milestone scope",
                "",
                "This package is generated from the actual repository state by the PP-AIPP Milestone Pack Builder.",
                "It contains source code, tests, documentation and CI configuration selected by the release policy.",
                "",
                "## Changelog snapshot",
                "",
                changelog_text.strip() or "No changelog was available.",
                "",
            ]
        )

    @staticmethod
    def _zip_write_bytes(archive: ZipFile, path: str, data: bytes) -> None:
        info = ZipInfo(path)
        info.date_time = (2026, 1, 1, 0, 0, 0)
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, data)

    def build(self) -> PackResult:
        project, version = self._metadata()
        commit, dirty = self._git_state()
        verification = self._verification_status()
        files = self._source_files()
        safe_version = version.replace("+", "-")
        safe_milestone = "_".join(self.config.milestone.split())
        stem = f"{project}_{safe_version}_{safe_milestone}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        archive_path = self.output_dir / f"{stem}.zip"
        manifest_json_path = self.output_dir / f"{stem}_MANIFEST.json"
        manifest_text_path = self.output_dir / f"{stem}_MANIFEST.txt"
        release_notes_path = self.output_dir / f"{stem}_RELEASE_NOTES.md"
        checksum_path = self.output_dir / f"{stem}.sha256"
        bundle_path: Path | None = None

        entries = [
            ManifestEntry(
                path=path.relative_to(self.repository).as_posix(),
                size=path.stat().st_size,
                sha256=self._sha256(path),
            )
            for path in files
        ]
        metadata = {
            "project": project,
            "version": version,
            "milestone": self.config.milestone,
            "commit": commit,
            "dirty": dirty,
            "verification_status": verification,
            "generated_at": datetime.now(UTC).isoformat(),
            "file_count": len(entries),
            "total_bytes": sum(entry.size for entry in entries),
            "warnings": self.warnings,
            "files": [{"path": entry.path, "size": entry.size, "sha256": entry.sha256} for entry in entries],
        }
        manifest_json = json.dumps(metadata, indent=2, ensure_ascii=False)
        manifest_text = "\n".join(
            [
                f"Project: {project}",
                f"Version: {version}",
                f"Milestone: {self.config.milestone}",
                f"Commit: {commit}",
                f"Dirty: {dirty}",
                f"Verification: {verification}",
                f"Files: {len(entries)}",
                f"Bytes: {sum(entry.size for entry in entries)}",
                "",
                *[f"{entry.sha256}  {entry.size:>10}  {entry.path}" for entry in entries],
                "",
            ]
        )
        release_notes = self._release_notes_text(project, version, commit, verification)
        manifest_json_path.write_text(manifest_json, encoding="utf-8")
        manifest_text_path.write_text(manifest_text, encoding="utf-8")
        release_notes_path.write_text(release_notes, encoding="utf-8")

        with ZipFile(archive_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            prefix = f"{project}-{safe_version}"
            for path, entry in zip(files, entries, strict=True):
                self._zip_write_bytes(archive, f"{prefix}/{entry.path}", path.read_bytes())
            self._zip_write_bytes(archive, f"{prefix}/RELEASE_MANIFEST.json", manifest_json.encode())
            self._zip_write_bytes(archive, f"{prefix}/RELEASE_MANIFEST.txt", manifest_text.encode())
            self._zip_write_bytes(archive, f"{prefix}/RELEASE_NOTES.md", release_notes.encode())

        archive_checksum = self._sha256(archive_path)
        checksum_path.write_text(f"{archive_checksum}  {archive_path.name}\n", encoding="utf-8")

        if self.config.include_git_bundle:
            if not (self.repository / ".git").exists():
                self.warnings.append("Git bundle requested but repository has no .git directory.")
            else:
                bundle_path = self.output_dir / f"{stem}.bundle"
                self._run_git("bundle", "create", str(bundle_path), "--all")

        return PackResult(
            project=project,
            milestone=self.config.milestone,
            version=version,
            commit=commit,
            dirty=dirty,
            verification_status=verification,
            archive=str(archive_path),
            checksum_file=str(checksum_path),
            manifest_json=str(manifest_json_path),
            manifest_text=str(manifest_text_path),
            release_notes=str(release_notes_path),
            git_bundle=str(bundle_path) if bundle_path else None,
            file_count=len(entries),
            total_bytes=sum(entry.size for entry in entries),
            warnings=self.warnings,
        )
