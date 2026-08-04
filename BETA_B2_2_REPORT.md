# PP-AIPP v3.0.0-beta.6 — Beta B2.2 Premium Layout & Image Engine

## Delivered

- Automatic discovery of recipe hero images in the project `images` directory.
- Supported file names: `PP-R001.jpg`, `.jpeg`, `.png`, `.webp` and `_hero` variants.
- Project asset-record paths are checked before conventional image filenames.
- Every PDF recipe page contains a centred 4:5 premium photo area.
- Missing photos receive a branded Project Physique production placeholder.
- `image_coverage_report.json` lists found images and every missing recipe ID.

## Image workflow

Place licensed production images in the project `images` directory using recipe IDs:

- `images/PP-R001.jpg`
- `images/PP-R002.jpg`
- through `images/PP-R080.jpg`

Run Export again to regenerate the PDF and verified ZIP automatically.
