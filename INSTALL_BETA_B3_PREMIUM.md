# PP-AIPP Beta B3 — Premium Schema Upgrade

This is a full source replacement package for the existing PP-AIPP repository.

1. Copy all files from this package into the local PP-AIPP repository and allow
   Windows to replace files with matching names.
2. Commit and push the changes with GitHub Desktop.
3. Wait for the Windows EXE GitHub Actions workflow to finish.
4. Download and extract the new PP-AIPP Windows artifact.
5. Keep the Premium DOCX and its `_Preview.pdf` in the same folder when importing.
6. Run: Open Project → Import Gold Master → Validate → Build Book → Export.

Expected Build Console confirmation:

- `Imported 80 recipes`
- `Premium Schema v5 detected.`
- `Complete premium layout and companion PDF preserved.`

Version: 3.0.0b7
