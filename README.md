# PP-AIPP

Project Physique AI Publishing Platform v3.0 — modular publishing automation for books, recipe collections and digital products.

## Current milestone

**v3.0.0-alpha.1 — Core Kernel**

Implemented:
- application kernel and lifecycle
- workspace manager
- configuration manager
- plugin discovery and registration
- job engine
- structured logging
- AI gateway interface with provenance states
- CLI and automated tests

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
