# Beta B2.8 — Local Free AI Photo Engine

## Delivered

- Free local Stable Diffusion recipe-photo generation.
- Automatic prompts derived from each recipe title, meal type and ingredients.
- Automatic 4:5 crop and 1200 × 1500 PNG production output.
- Resumable batches from 1 to 80 recipes.
- Existing recipe images are skipped instead of overwritten.
- Generated assets are imported into the normal PP-AIPP photography pipeline.
- Optional OpenAI Images API mode remains available.

## Cost and hardware

Local Free AI has no API or per-image charge. It uses the user's own computer,
electricity and disk space. The initial model download is several gigabytes. An
NVIDIA GPU with at least 6 GB VRAM is recommended. CPU mode is supported but much
slower.

## Verification

Python source, tests and runner compile successfully. The GitHub Actions Quality Gate
and Windows EXE workflow provide the final Windows packaging verification.
