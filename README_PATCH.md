# PP-AIPP beta.3.1 — GitHub Actions Fix

This is a small patch, not a full repository snapshot.

## Upload method

If `.github` uploads correctly:
- upload the included `.github/workflows/windows-exe.yml`

If `.github` is hidden or skipped:
1. Open the repository on GitHub.
2. Choose **Add file → Create new file**.
3. Enter this exact filename:
   `.github/workflows/windows-exe.yml`
4. Copy the contents of:
   `patch/windows-exe.yml`
5. Commit directly to `main`.

## Expected result

The **Actions** tab will show:

`Build PP-AIPP Windows EXE`

After a successful run, download artifact:

`PP-AIPP-Windows-beta.3.1`
