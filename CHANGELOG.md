
# Changelog

## 3.0.0b11.post1 — 2026-08-06

- Updated the export-manifest regression expectation from `3.0.0b10` to `3.0.0b11`.
- Fixes the B3.4 GitHub Actions failure across Python 3.11, 3.12 and 3.13.
- Runtime and publishing output remain unchanged at `3.0.0b11`.

## 3.0.0b11 — 2026-08-06

- Added the B3.4 Final Premium Publishing Polish engine.
- Added consumer-ready copyright, health disclaimer, contents and Project Physique pages.
- Added deterministic recipe-specific Chef's Tips, Common Mistakes, Ingredient Swaps and Serving Suggestions for legacy Gold Masters while preserving authored premium cards when supplied.
- Restored the complete five-value macro panel: energy, protein, carbohydrate, fat and fibre.
- Upgraded the cover positioning and clarified the complete 30-day programme offer.
- Verified a 108-page, 80-recipe publishing PDF from Gold Master v4.1.
- Added clean source-package guidance so release ZIPs exclude Git history, virtual environments, caches, logs and local databases.

## 3.0.0b10 — 2026-08-05

- Added the B3.3 Complete Premium Programme publishing engine.
- Restored the Success Guide, Nutrition Basics, UK Shopping System, 30-day tracker and FAQ to the photography PDF.
- Added a complete Day 1–30 meal plan, five weekly shopping lists and indexes by meal, calories, protein and total time.
- Added Chef's Tip, Common Mistake, Ingredient Swap, Meal Prep and Serving Suggestion cards to every recipe page.
- Added total time, difficulty, fibre, freezer guidance, vegetarian guidance and allergen notes.
- Verified a 105-page, 80-recipe publishing PDF with 80 of 80 photographs present.

## 3.0.0b9 — 2026-08-05

- Added the B3.2 Luxury Editorial Photo Layout Engine.
- Added a branded navy-and-gold cover and recipe collection opener.
- Added alternating left/right 4:5 hero photography layouts.
- Replaced stacked technical output with premium metadata, nutrition and editorial cards.
- Added two-column ingredients and method panels with one recipe per page.

## 3.0.0b8 — 2026-08-05

- Fixed Premium Schema export bypassing the photography renderer when a companion PDF exists.
- The main `*_Print.pdf` now renders imported recipe photographs whenever photography assets are present.
- The supplied Premium PDF is preserved separately as `*_Premium_Layout_Reference.pdf`.
- Added regression coverage for combined Premium layout and photography exports.

## 3.0.0b7 — 2026-08-05

- Added Gold Master Premium v5 schema detection.
- Preserved the complete controlled DOCX during Build Book instead of applying legacy recipe-only reflow.
- Preserved the layout-verified Premium PDF when it is supplied beside the Gold Master DOCX.
- Added explicit Build Console confirmation for Premium Schema passthrough mode.
- Added pipeline and export regression coverage for premium source preservation.

## 3.0.0b6.post9 — 2026-08-05

- Added Beta B2.8 Local Free AI recipe-photo generation with Stable Diffusion.
- Added one-click Windows setup for the local model and all required libraries.
- Added resumable batch generation that skips existing PP-R001–PP-R080 assets.
- Kept the optional OpenAI Images API backend for users who prefer a hosted service.

## 3.0.0b6.post7 — 2026-08-04

- Added the Beta B2.6 Photo Batch Planner for the remaining PP-R001–PP-R080 campaign.
- Added numbered batch folders with CSV, JSON, and plain-text production manifests.
- Added a configurable `Prepare Photo Batch` desktop action and export-package plan reporting.

## 3.0.0b6.post6 — 2026-08-04

- Added the Beta B2.5 80-recipe photography campaign workflow.
- Added persistent batch history, coverage percentages, and next-missing recipe IDs.
- Included photography batch history in verified export packages.

## 3.0.0b6.post3 — 2026-08-04

- Added the Beta B2.2 Premium Layout and Image Engine.
- Added automatic 4:5 hero-image discovery for PP-R001 through PP-R080.
- Added branded image placeholders when licensed production assets are unavailable.
- Added an image coverage report to every verified publishing package.

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
# 3.0.0b6.post8 — Beta B2.7

- Added a one-click, resumable AI photography campaign for all missing recipes.
- Added recipe-aware `gpt-image-2` prompts and automatic `PP-Rxxx` naming.
- Added production 4:5 image preparation and direct PDF/export integration.
- Added retries, checkpoints, coverage reports, and skip-existing behavior.
- API keys are accepted at runtime and are never stored or logged.

# 3.0.0b6.post4 — Beta B2.3

- Added bulk photography import with automatic PP-R001–PP-R080 assignment.
- Added 4:5 crop, resolution, duplicate and naming validation.
- Added photography readiness reporting and export-package integration.

# 3.0.0b6.post5 — Beta B2.4

- Added incremental photography batches that preserve existing project coverage.
- Added automatic EXIF rotation and production-safe 4:5 preparation.
- Added controlled replacement of earlier recipe images and QA report schema v2.
# Beta B2.5

- Added resumable 80-recipe photography campaign tracking.
- Added persistent batch history, coverage percentage and next-missing queue.
- Included photography batch history in verified export packages.
