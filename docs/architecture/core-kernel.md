# Core Kernel architecture

The kernel owns lifecycle and shared services but contains no publishing-domain logic.

## Services

- `ConfigManager`: YAML configuration plus environment overrides.
- `WorkspaceManager`: isolated multi-project directory trees.
- `PluginManager`: entry-point discovery, registration and activation.
- `JobEngine`: structured execution state for future queues.
- `AIGateway`: provider-neutral AI interface with mandatory draft provenance.
- Logging: file and console output.

## Plugin boundary

External modules register through the Python entry-point group `pp_aipp.plugins`. Parser, database, layout, QA and export modules will therefore be installable independently.

## Content integrity

AI-generated material is always returned as `EDITORIAL_DRAFT`. Approval must be an explicit later operation. Source-verified records are not silently replaced.
