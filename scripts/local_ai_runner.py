"""Free local Stable Diffusion batch runner used by PP-AIPP.

The model is downloaded once and cached locally. No paid API or account key is used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--quality", choices=("low", "medium", "high"), default="medium")
    args = parser.parse_args()

    import torch
    from diffusers import StableDiffusionPipeline
    from PIL import ImageOps

    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    if not tasks:
        return 0
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    model_id = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    pipeline = StableDiffusionPipeline.from_pretrained(
        model_id, torch_dtype=dtype, safety_checker=None, requires_safety_checker=False,
    )
    pipeline = pipeline.to(device)
    if device == "cuda":
        pipeline.enable_attention_slicing()
    steps = {"low": 15, "medium": 25, "high": 35}[args.quality]
    negative = (
        "text, words, letters, watermark, logo, label, people, hands, packaging, collage, "
        "multiple dishes, illustration, painting, CGI, deformed food, blurry, low quality"
    )
    for index, task in enumerate(tasks):
        output = Path(task["output"])
        output.parent.mkdir(parents=True, exist_ok=True)
        generator = torch.Generator(device=device).manual_seed(24000 + index)
        image = pipeline(
            task["prompt"], negative_prompt=negative, width=512, height=640,
            num_inference_steps=steps, guidance_scale=7.5, generator=generator,
        ).images[0].convert("RGB")
        image = ImageOps.fit(image, (1200, 1500))
        image.save(output, "PNG", optimize=True)
        print(f"READY {task['recipe_id']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
