# PP-AIPP v3.0.0-beta.3 — Windows App Builder

PP-AIPP is the Project Physique AI Publishing Platform desktop framework.

## Easiest Windows start

Double-click `INSTALL_AND_RUN.bat`. It creates an isolated environment, installs the desktop dependencies, and starts PP-AIPP. Later use `RUN_PP-AIPP.bat`.

## Developer installation

```powershell
python -m pip install -e ".[desktop,dev,build]"
pp-aipp doctor
pp-aipp-desktop
```

## Windows EXE

Push to GitHub `main`. The workflow `.github/workflows/windows-exe.yml` runs tests and builds `PP-AIPP.exe`. Download it from the completed GitHub Actions run under **Artifacts**.

## Local Free AI recipe photography — Beta B2.8

1. Run `SETUP_LOCAL_AI.bat` once. It creates an isolated local environment and
   installs the free Stable Diffusion model dependencies.
2. Start `PP-AIPP.exe`, open the project, and click **Generate AI Photos**.
3. Choose **Local Free AI**, a batch size, and a quality preset.

PP-AIPP generates only missing `PP-R001`–`PP-R080` assets, prepares every image in
the publishing 4:5 format, and connects it to the PDF export. Existing images are
skipped, so the campaign is safe to stop and resume. There is no API key and no
per-image charge. The first run downloads several gigabytes of model data. An NVIDIA
GPU is strongly recommended; CPU generation works but can be slow.

The optional paid OpenAI Images API backend remains available from the same dialog.
