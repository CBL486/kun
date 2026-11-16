from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "art-source/character-v2/pixellab/P2-3R/input-down-soft-lips-64x96.png"
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-3R2"
EXPECTED_INPUT_SHA256 = (
    "77FB41D39AC16C839246EAAA12FDEC43"
    "8F270CCE76973FA7E1B20B70E333940B"
)
MASK_POINTS = (
    (20, 66),
    (43, 66),
    (46, 73),
    (47, 85),
    (43, 90),
    (22, 90),
    (16, 85),
    (17, 73),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    source_hash = sha256(INPUT)
    if source_hash != EXPECTED_INPUT_SHA256:
        raise ValueError(f"unexpected input SHA-256: {source_hash}")

    source = Image.open(INPUT).convert("RGBA")
    if source.size != (64, 96):
        raise ValueError(f"unexpected input size: {source.size}")

    mask = Image.new("RGBA", source.size, (0, 0, 0, 0))
    ImageDraw.Draw(mask).polygon(MASK_POINTS, fill=(255, 255, 255, 255))

    alpha_values = sorted(
        {
            mask.getpixel((x, y))[3]
            for y in range(mask.height)
            for x in range(mask.width)
        }
    )
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected mask alpha values: {alpha_values}")

    mask_bbox = mask.getbbox()
    if mask_bbox is None:
        raise ValueError("mask is empty")
    mask_height = mask_bbox[3] - mask_bbox[1]
    if mask_height < 20:
        raise ValueError(f"mask height is too small: {mask_height}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    input_path = OUTPUT_DIR / "input-down-soft-lips-64x96.png"
    mask_path = OUTPUT_DIR / "down-lower-body-mask.png"
    api_mask_path = OUTPUT_DIR / "down-lower-body-mask-api.png"
    preview_path = OUTPUT_DIR / "down-lower-body-mask-preview-8x.png"
    metrics_path = OUTPUT_DIR / "mask-metrics.json"

    input_path.write_bytes(INPUT.read_bytes())
    mask.save(mask_path)

    api_mask = Image.new("RGB", source.size, (0, 0, 0))
    ImageDraw.Draw(api_mask).polygon(MASK_POINTS, fill=(255, 255, 255))
    api_mask.save(api_mask_path)

    scale = 8
    preview = source.resize(
        (source.width * scale, source.height * scale),
        Image.Resampling.NEAREST,
    )
    mask_scale = mask.resize(preview.size, Image.Resampling.NEAREST)
    translucent_red = Image.new("RGBA", preview.size, (0, 0, 0, 0))
    for y in range(preview.height):
        for x in range(preview.width):
            if mask_scale.getpixel((x, y))[3]:
                translucent_red.putpixel((x, y), (255, 40, 40, 130))
    preview.alpha_composite(translucent_red)
    preview.save(preview_path)

    covered_pixels = sum(
        mask.getpixel((x, y))[3] > 0
        for y in range(mask.height)
        for x in range(mask.width)
    )
    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3r2-mask-v1",
        "input": input_path.relative_to(ROOT).as_posix(),
        "input_sha256": source_hash,
        "mask": mask_path.relative_to(ROOT).as_posix(),
        "mask_sha256": sha256(mask_path),
        "api_mask": api_mask_path.relative_to(ROOT).as_posix(),
        "api_mask_sha256": sha256(api_mask_path),
        "mask_polygon": [list(point) for point in MASK_POINTS],
        "mask_bbox_half_open": list(mask_bbox),
        "mask_visible_bounds_inclusive": [
            mask_bbox[0],
            mask_bbox[1],
            mask_bbox[2] - 1,
            mask_bbox[3] - 1,
        ],
        "mask_size": list(mask.size),
        "mask_height": mask_height,
        "alpha_values": alpha_values,
        "covered_pixels": covered_pixels,
        "generation_submissions": 0,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
