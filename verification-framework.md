# Verification Framework

Sprint K0.6 adds a reproducible verification gate for PP-AIPP.

## Checks

- Python bytecode compilation
- unit and integration tests
- Ruff static analysis
- optional real Gold Master import test
- JSON, Markdown and HTML reports

## Local run

```bash
pip install -e ".[dev]"
pp-aipp verify --report-dir reports/local
```

To include a controlled Gold Master DOCX:

```bash
pp-aipp verify \
  --gold-master samples/Project_Physique_Gold_Master.docx \
  --report-dir reports/gold-master
```

The Gold Master is not committed to the public repository. The integration check is therefore `SKIPPED`, not falsely marked `PASSED`, unless a source file is explicitly supplied.

## CI

GitHub Actions tests Python 3.11, 3.12 and 3.13. Reports and coverage are uploaded as workflow artifacts. A failing compile, test or lint step blocks the workflow.
