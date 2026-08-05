# PP-AIPP v3.0.0-beta.10 B3.3 — Complete Premium Programme

## Complete premium publishing PDF

B3.3 produces a complete 105-page luxury photo edition: programme guidance,
the full Day 1–30 plan, five weekly shopping lists, four recipe indexes, 80
photo-led recipe pages, a 30-day tracker and FAQ. Every recipe includes five
editorial cards plus time, difficulty, fibre, freezer, vegetarian and allergen
guidance. The cover is intentionally retained as the current working cover so
it can be replaced during the final visual polish.

## Gold Master Premium v5 support

Beta B3 preserves the complete controlled Premium v5 DOCX during Build Book,
including Chefie's Tips, Common Mistakes, Ingredient Swaps, Meal-Prep Notes,
Serving Suggestions, the Success Guide, Nutrition Basics, UK Shopping System,
Progress Tracker and FAQ. When the verified `*_Preview.pdf` is stored beside the
DOCX during import, Export reuses that PDF without legacy recipe-only reflow.

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
