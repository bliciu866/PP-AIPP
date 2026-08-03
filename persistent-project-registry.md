# Persistent Project Registry

Sprint K0.2 introduces the durable registry used by PP-AIPP to track projects, books, releases, exports and immutable history events.

## Storage

SQLite is the default embedded database. Foreign keys are enabled for every connection. The schema is created automatically and can later be migrated to PostgreSQL without changing the public service API.

## Entities

- **Project** — top-level brand or publishing initiative.
- **Book** — publication owned by one project.
- **Release** — versioned book milestone.
- **Export** — generated publication artifact.
- **History** — append-only audit event.

## Integrity guarantees

- project slugs are globally unique;
- book slugs are unique inside a project;
- releases are unique by book and version;
- orphan books, releases and exports are rejected;
- create operations write history events.
