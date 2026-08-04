
# Changelog

## 3.0.0b6.post2 — 2026-08-04

- Added native PDF rendering without Microsoft Word or LibreOffice.
- Added a US Letter 8.5 x 11 inch publishing PDF to every export package.
- Added KDP/Etsy publishing guidance to the verified ZIP package.
- Added PDF generation verification and updated the Windows artifact name for B2.1.

## 3.0.0b6.post1 — 2026-08-04

- Delivered Beta B2 Export Engine integration.
- Added verified DOCX export packages with SHA-256 manifests.
- Included available Gold Master import and layout QA reports in each ZIP package.
- Added Export Complete feedback with Open Export and Open Folder actions.
- Added Export Engine unit tests and updated the Windows artifact name.

## 3.0.0b5.post14 — 2026-08-04

- Delivered Sprint Beta B1.4 controlled-content parsing improvements.
- Moved production DOCX output to the visible project `build` directory.
- Added Open Book and Open Folder actions after a successful build.
- Aligned desktop-state tests and runtime/package version declarations.

## 3.0.0b5 — 2026-08-04

- Connected the desktop Build Book action to the production Gold Master parser.
- Added transactional recipe persistence in the project SQLite database.
- Added deterministic DOCX generation for all imported recipes.
- Added Gold Master import and layout build reports in the project QA directory.
- Added an end-to-end build pipeline test and Windows desktop completion feedback.

## 3.0.0b4.post1 — 2026-08-04

- Added Sprint 1A Gold Master project schema and controlled DOCX import.
- Added SHA-256 source manifests and project structure validation.
- Connected desktop Import Gold Master and Validate actions to production services.
- Normalized Ruff formatting across source and tests.
- Removed the obsolete root package that interfered with pytest discovery.
- Verified 36 tests with 72.83% coverage.

## 3.0.0-beta.1

- Added the first PySide6/Qt desktop application framework.
- Added Project Explorer, Build Console, toolbar, menus and Settings.
- Added project and Gold Master selection flows.
- Added desktop entry points and desktop state tests.


## 3.0.0-alpha.8

- Added production Milestone Pack Builder.
- Added clean Git and verification release gates.
- Added deterministic ZIP, manifests, release notes and SHA-256 outputs.
- Added optional Git bundle creation.

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
