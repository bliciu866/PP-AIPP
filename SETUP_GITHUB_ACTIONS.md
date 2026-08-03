# Activate GitHub Actions on mobile

The repository contains the correct hidden file:

`.github/workflows/ci.yml`

Some Android file managers do not upload hidden `.github` folders. If the **Actions** tab still shows workflow templates:

1. Open **Actions**.
2. Tap **set up a workflow yourself**.
3. Keep the path `.github/workflows/ci.yml`.
4. Delete the example content.
5. Copy all content from the visible root file `GITHUB_ACTIONS_CI.yml`.
6. Commit directly to `main` with message:

`ci: activate PP-AIPP quality gate`

After the commit, the workflow named **PP-AIPP Quality Gate** should start automatically.
