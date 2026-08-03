# Gold Master Parser Integration

Sprint K0.4 introduces the first production ingestion path from a controlled Project Physique DOCX into PP-AIPP domain storage.

## Pipeline

1. Read DOCX blocks in document order.
2. Distinguish recipe sections from Recipe Index references.
3. Parse recipe identity, title, badges and information panel.
4. Parse ingredient and nutrition tables.
5. Reset method numbering independently for every recipe.
6. Preserve Meal Prep and QA notes as source-verified records.
7. Validate PP-R001–PP-R080 continuity.
8. Persist complete recipe aggregates transactionally in SQLite.
9. Emit a machine-readable import report.

## Integrity rules

- A full Gold Master import is rejected when collection-level errors exist.
- Missing methods are warnings because the controlled source may omit them.
- Nutrition values are copied, never recalculated.
- `CONDITIONAL PASS` QA notes produce a conditional recipe status.
- Existing records are replaced atomically unless `--no-replace` is selected.
