# Layout Engine Integration

Sprint K0.5 connects the domain SQLite database to a deterministic DOCX layout generator.

## Pipeline

1. Read recipes through a read-only projection.
2. Apply a reusable `LayoutTheme`.
3. Build one controlled recipe page per record.
4. Add hero asset slot, badges, information panel, ingredients, method, nutrition and QA.
5. Optionally convert DOCX to PDF through LibreOffice when available.
6. Emit a machine-readable build report.

The renderer never recalculates nutrition and never invents missing controlled methods.
