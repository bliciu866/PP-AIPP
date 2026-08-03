# PP-AIPP

Project Physique AI Publishing Platform v3.0 — modular publishing automation for books, recipe collections and digital products.

## Current milestone

**v3.0.0-alpha.6 — Verification Framework**

Implemented:
- application kernel and lifecycle
- workspace manager
- configuration manager
- plugin discovery and registration
- job engine
- structured logging
- AI gateway interface with provenance states
- CLI and automated tests


### Domain layer

- canonical Recipe, Ingredient, Nutrition, QA and Asset models
- transactional SQLite project database
- provenance-aware source/editorial/approved states
- ingredient search and recipe filtering

### Verification framework

- compile, test and lint gates
- JSON, Markdown and HTML verification reports
- GitHub Actions on Python 3.11–3.13
- optional controlled Gold Master integration test

```bash
pp-aipp verify --report-dir reports/local
```

A real Gold Master check is only marked `PASSED` when the source DOCX is explicitly supplied.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
pp-aipp doctor
pp-aipp workspace create project-physique
pp-aipp plugins list
pytest
```

## Principles

1. Source data is never silently overwritten.
2. AI output is marked as `SOURCE_VERIFIED`, `EDITORIAL_DRAFT` or `APPROVED`.
3. Modules communicate through stable interfaces.
4. Every job is logged and versionable.
5. The platform is multi-project and multi-brand.

See [ROADMAP.md](ROADMAP.md) and [docs/architecture/core-kernel.md](docs/architecture/core-kernel.md).


## Gold Master import

```bash
pp-aipp parser import-docx GoldMaster.docx --book-id <BOOK_ID>
pp-aipp parser status --book-id <BOOK_ID>
```

The parser preserves controlled Nutrition Lock and QA records and writes an audit report to `output/parser_import/import_report.json`.


## Layout build

```bash
pp-aipp layout build-book --database data/project.sqlite3 --output output/layout/book.docx
```
