# Install PP-AIPP Beta B3.6

## Apply the source update

1. Close PP-AIPP and extract the B3.6 ZIP.
2. Copy the extracted files into the root of the `PP-AIPP` repository.
3. Allow Windows to merge folders and replace matching files.
4. Open GitHub Desktop and confirm the intended B3.6 source changes.
5. Commit with `PP-AIPP B3.6 Final Editorial and Publication QA` and push.
6. Wait for both GitHub Actions workflows to finish successfully.
7. Download `PP-AIPP-Windows-beta.11-B3.6` from the Windows workflow artifacts.

## Keep runtime output out of Git

The B3.6 `.gitignore` excludes future `workspaces`, QA renders and deliverables.
If an older `workspaces` folder is already tracked, first keep a backup of the
final publication outside the repository, then delete that tracked folder once,
commit the deletion and push. Future local builds will remain invisible to Git.
