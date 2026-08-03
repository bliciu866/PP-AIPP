# Changelog

## 3.0.0-alpha.7

- Added a three-job GitHub Actions quality and release gate.
- Added Python 3.11–3.13 test matrix, Ruff, coverage threshold and CLI smoke tests.
- Added package build and clean wheel-install verification.
- Added release consistency checks and mobile workflow activation instructions.

## [3.0.0-alpha.6] - 2026-08-03

### Added
- Verification runner with compile, pytest, Ruff and optional Gold Master checks.
- JSON, Markdown and HTML reports.
- GitHub Actions test matrix for Python 3.11–3.13.
- `pp-aipp verify` CLI command and CI artifacts.

## 3.0.0-alpha.5

- Added database-driven Layout Engine.
- Added deterministic DOCX book generation.
- Added optional PDF conversion and layout reports.
- Added layout CLI and tests.


## 3.0.0-alpha.4

- Added Gold Master DOCX parser integration.
- Added transactional import into the project database.
- Added collection validation and JSON import reporting.
- Added parser CLI commands and tests.

## 3.0.0-alpha.3

- Added canonical publishing domain models.
- Added transactional SQLite project database.
- Added Nutrition Lock, QA, badge and asset persistence.
- Added recipe filtering and ingredient search.

## 3.0.0-alpha.2

- Added persistent SQLite project registry.
- Added project, book, release, export and history models.
- Added registry CLI and integrity tests.


## [3.0.0-alpha.1] - 2026-08-03

### Added
- Core Kernel lifecycle and health report.
- Workspace, configuration, plugin, job and logging managers.
- Provider-neutral AI gateway contracts and provenance model.
- CLI commands: `doctor`, `workspace create/list`, `plugins list`, `job demo`.
- Initial test suite and GitHub Actions workflow.
