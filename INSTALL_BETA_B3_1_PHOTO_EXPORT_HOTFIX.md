# PP-AIPP Beta B3.1 — Photo Export Hotfix

1. Close PP-AIPP.
2. Copy every file and folder from this package into the local `PP-AIPP` repository.
3. Allow Windows to replace files with matching names.
4. Commit and push the changes with GitHub Desktop.
5. Wait for the Windows EXE GitHub Actions workflow to finish.
6. Download and extract the new Windows artifact.
7. Open the existing project, import the Luxury Editorial Gold Master, then run Validate, Build Book and Export.

Expected result:

- `*_Print.pdf` contains the imported recipe photographs.
- `*_Premium_Layout_Reference.pdf` preserves the supplied editorial PDF.
- `image_coverage_report.json` reports the actual photo coverage.
