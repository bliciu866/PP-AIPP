# PP-AIPP B3.5 Final Brand & Cover Polish

1. Close PP-AIPP and GitHub Desktop.
2. Extract the B3.5 ZIP to a temporary folder.
3. Copy the contents of the extracted `PP-AIPP` folder into your existing local repository.
4. Confirm replacement of matching files.
5. Open GitHub Desktop and commit with `PP-AIPP B3.5 Final Brand and Cover Polish`.
6. Push to `main` and wait for both GitHub Actions workflows to turn green.
7. Download `PP-AIPP-Windows-beta.11-B3.5`, extract it and run `PP-AIPP.exe`.
8. Open Project Physique, import the Gold Master DOCX and click `Validate`.
9. Import the prepared PP-R001–PP-R080 photography folder when available.
10. Click `Build Book`, then `Export`.

The B3.5 print PDF contains 112 pages for an 80-recipe collection. The image
coverage report is the release gate: commercial export requires 80 images found
and 0 missing. Run a final KDP preview before publication.

This source package intentionally excludes `.git`, `.venv`, caches, logs, build
outputs and local SQLite databases. Those files must never be copied between
Git repositories.
