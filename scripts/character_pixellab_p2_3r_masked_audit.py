from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-3R"
EXPECTED_SIZE = (64, 96)
MASK_RECT = (14, 79, 46, 90)
SOFT_LIP = (201, 120, 130, 255)
SOFT_LIP_SHADOW = (160, 93, 99, 255)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def build_preview(
    original: Image.Image, result: Image.Image
) -> Image.Image:
    crop = (8, 65, 56, 96)
    scale = 8
    width = (crop[2] - crop[0]) * scale
    height = (crop[3] - crop[1]) * scale
    canvas = Image.new(
        "RGBA",
        (width * 2 + 54, height + 58),
        (235, 235, 235, 255),
    )
    draw = ImageDraw.Draw(canvas)
    for index, (label, image) in enumerate(
        (("BEFORE", original), ("CLASSIC INPAINT", result))
    ):
        x = 18 + index * (width + 18)
        y = 34
        background = Image.new("RGBA", (width, height), (246, 243, 234, 255))
        background.alpha_composite(
            image.crop(crop).resize(
                (width, height),
                Image.Resampling.NEAREST,
            )
        )
        canvas.alpha_composite(background, (x, y))
        draw.text((x, 10), label, fill=(0, 0, 0, 255))
        draw.rectangle((x, y, x + width, y + height), outline=(80, 80, 80, 255))
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit the one allowed P2-3R masked inpainting result."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "input-down-soft-lips-64x96.png",
    )
    parser.add_argument(
        "--mask",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "down-lower-body-mask.png",
    )
    parser.add_argument(
        "--result",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "down-masked-edit-raw.png",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    original = Image.open(args.input).convert("RGBA")
    mask = Image.open(args.mask).convert("RGBA")
    result = Image.open(args.result).convert("RGBA")
    for label, image in (("input", original), ("mask", mask), ("result", result)):
        if image.size != EXPECTED_SIZE:
            raise ValueError(f"unexpected {label} size: {image.size}")

    changes_inside: list[tuple[int, int]] = []
    changes_outside: list[tuple[int, int]] = []
    added_outside: list[tuple[int, int]] = []
    removed_outside: list[tuple[int, int]] = []
    for y in range(result.height):
        for x in range(result.width):
            before = original.getpixel((x, y))
            after = result.getpixel((x, y))
            if before == after:
                continue
            point = (x, y)
            if mask.getpixel(point)[3]:
                changes_inside.append(point)
            else:
                changes_outside.append(point)
                if before[3] == 0 and after[3] != 0:
                    added_outside.append(point)
                elif before[3] != 0 and after[3] == 0:
                    removed_outside.append(point)

    palette = {
        result.getpixel((x, y))
        for y in range(result.height)
        for x in range(result.width)
    }
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")

    output_path = args.output_dir / "down-masked-edit-preview-8x.png"
    metrics_path = args.output_dir / "down-masked-edit-metrics.json"
    credit_path = args.output_dir / "credit-log.json"

    build_preview(original, result).save(output_path)

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3r-audit-v1",
        "status": "blocked",
        "blocker": (
            "masked result remains a continuous skirt silhouette without "
            "two readable separated legs"
        ),
        "input": args.input.relative_to(ROOT).as_posix(),
        "input_sha256": sha256(args.input),
        "mask": args.mask.relative_to(ROOT).as_posix(),
        "mask_sha256": sha256(args.mask),
        "mask_rect": list(MASK_RECT),
        "result": args.result.relative_to(ROOT).as_posix(),
        "result_sha256": sha256(args.result),
        "result_bbox": list(result.getbbox()) if result.getbbox() else None,
        "changed_pixels_inside_mask": len(changes_inside),
        "changed_pixels_outside_mask": len(changes_outside),
        "removed_opaque_pixels_outside_mask": len(removed_outside),
        "added_opaque_pixels_outside_mask": len(added_outside),
        "leg_visible_height": 0,
        "two_legs_separated": False,
        "boot_pixel_count": 0,
        "boot_colors": [],
        "lip_colors_present": {
            "#C97882": SOFT_LIP in palette,
            "#A05D63": SOFT_LIP_SHADOW in palette,
        },
        "colors": len(palette),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": 0,
        "generation_submissions": 1,
        "request_attempts": 2,
        "rejected_validation_requests": 1,
        "generations_used": 1,
        "pixellab_calls": 1,
        "animation_started": False,
        "production_modified": False,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    credit_log = {
        "schema_version": "rpg-character-pixellab-p2-3r-credit-log-v1",
        "date": "2026-11-15",
        "branch": "codex/character-art-pixellab-p2-3r",
        "starting_commit": "0dfa3b4",
        "endpoint": "POST /v2/inpaint",
        "model_mode": "Classic",
        "input_sha256": metrics["input_sha256"],
        "mask_sha256": metrics["mask_sha256"],
        "generation_submissions": 1,
        "request_attempts": 2,
        "rejected_validation_requests": 1,
        "generations_used": 1,
        "usage": {"type": "generations", "generations": 1},
        "purchases": 0,
        "upgrades": 0,
        "pro_used": False,
        "status": "failed-visual-acceptance",
    }
    credit_path.write_text(
        json.dumps(credit_log, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
