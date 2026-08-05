# PP-AIPP Beta B2.7 — Automatic AI Photography Generator

## Outcome

Beta B2.7 removes the manual one-photo-at-a-time bottleneck. A single desktop action
generates a complete or partial campaign of missing recipe photos and connects them
to the existing publishing pipeline.

## Delivered

- One-click **Generate AI Photos** desktop action.
- Recipe-aware prompts built from title, meal and key ingredients.
- `gpt-image-2` generation in portrait format.
- Automatic 4:5 preparation at 1200 × 1500 pixels.
- Deterministic `PP-R001`–`PP-R080` filenames.
- Existing-photo detection, skip behavior and safe campaign resume.
- Three-attempt transient-error retry policy.
- Incremental JSON campaign checkpoint and final coverage report.
- Immediate compatibility with DOCX, PDF and verified export packages.
- Runtime-only API key handling; no key is written to disk or logs.

## Verification

The test suite covers prompt construction, sequential bulk generation, exact output
dimensions, skip-existing behavior and campaign reporting without making paid API calls.
