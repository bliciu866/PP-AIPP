# Project Database & Domain Models

Sprint K0.3 introduces the canonical publishing domain used by Parser, Layout, QA,
AI and Export plugins.

## Aggregate root

`Recipe` is written transactionally with its ingredients, method steps, nutrition,
badges, QA records and assets. A failed child insert rolls back the full recipe.

## Integrity rules

- recipe IDs are unique within a book;
- servings and method step numbers must be positive;
- nutrition and ingredient quantities cannot be negative;
- one Nutrition Lock record is allowed per recipe;
- deleting a recipe cascades to all owned records;
- provenance is explicit for source, draft and approved content.

## Storage

SQLite is used as the local-first reference implementation. The service boundary is
kept stable so a future PostgreSQL adapter can be added without changing plugins.
