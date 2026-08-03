# CI and Release Gate

PP-AIPP uses GitHub Actions to block unstable releases.

## Required gates

1. Source compilation.
2. Ruff static analysis.
3. Unit and integration tests on Python 3.11, 3.12 and 3.13.
4. Coverage threshold of 70%.
5. CLI smoke tests.
6. Version and workflow consistency check.
7. Wheel and source-package build.
8. Clean virtual-environment installation of the built wheel.

The final `release-gate` job runs only after all required jobs pass.

## Android/mobile upload note

Android file pickers often hide folders beginning with a dot. The actual workflow must be stored as:

`.github/workflows/ci.yml`

A visible copy is included at repository root as `GITHUB_ACTIONS_CI.yml`. When `.github` is not uploaded automatically, open **Actions → set up a workflow yourself**, replace the template with the contents of `GITHUB_ACTIONS_CI.yml`, and commit it as `.github/workflows/ci.yml`.
