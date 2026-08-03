# Milestone Pack Builder

The production builder creates a release snapshot from the actual repository state.

## Release gate

By default a pack is produced only when:

- the Git working tree is clean;
- a verification JSON report exists and has `PASSED` status;
- `pyproject.toml` contains a project name and version.

## Command

```bash
pp-aipp release-pack \
  --milestone "Milestone A Stable Alpha" \
  --verification-report reports/k0.7/verification_report.json \
  --git-bundle
```

Outputs include the source ZIP, release notes, JSON and text manifests, a SHA-256 sidecar and an optional Git bundle.

Use `--allow-dirty` only for development snapshots. Use `--skip-verification` only for non-release diagnostics.
