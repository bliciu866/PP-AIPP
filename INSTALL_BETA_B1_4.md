# Install Sprint Beta B1.4 into the PP-AIPP repository

1. Close PP-AIPP and GitHub Desktop.
2. Extract `PP-AIPP-v3.0.0-beta.5-B1.4-SOURCE.zip`.
3. Copy the extracted `PP-AIPP` folder over the existing local `PP-AIPP` folder.
4. Choose **Replace the files in the destination** when Windows asks.
5. Open GitHub Desktop, review the B1.4 changes, enter the commit summary
   `PP-AIPP v3.0.0-beta.5 B1.4`, and select **Commit to main**.
6. Select **Push origin**. GitHub Actions builds the Windows executable and the
   `PP-AIPP-Windows-beta.5-B1.4` artifact.

The repository's hidden `.git` directory is intentionally not included in the
archive, so extracting this source package over the existing clone preserves
the local GitHub Desktop connection.
