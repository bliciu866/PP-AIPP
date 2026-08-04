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
