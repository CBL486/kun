from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "art-source/character-v2/pixellab/P2-3/input-down-soft-lips-64x96.png"
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-3R"
EXPECTED_INPUT_SHA256 = (
    "77FB41D39AC16C839246EAAA12FDEC43"
    "8F270CCE76973FA7E1B20B70E333940B"
)
MASK_RECT = (14, 79, 46, 90)


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
    draw = ImageDraw.Draw(mask)
    draw.rectangle(
        (MASK_RECT[0], MASK_RECT[1], MASK_RECT[2] - 1, MASK_RECT[3] - 1),
        fill=(255, 255, 255, 255),
    )
    alpha_values = sorted(
        {
            mask.getpixel((x, y))[3]
            for y in range(mask.height)
            for x in range(mask.width)
        }
    )
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected mask alpha values: {alpha_values}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    input_path = OUTPUT_DIR / "input-down-soft-lips-64x96.png"
    mask_path = OUTPUT_DIR / "down-lower-body-mask.png"
    api_mask_path = OUTPUT_DIR / "down-lower-body-mask-api.png"
    preview_path = OUTPUT_DIR / "down-lower-body-mask-preview-8x.png"
    metrics_path = OUTPUT_DIR / "mask-metrics.json"

    input_path.write_bytes(INPUT.read_bytes())
    mask.save(mask_path)
    api_mask = Image.new("RGB", source.size, (0, 0, 0))
    ImageDraw.Draw(api_mask).rectangle(
        (MASK_RECT[0], MASK_RECT[1], MASK_RECT[2] - 1, MASK_RECT[3] - 1),
        fill=(255, 255, 255),
    )
    api_mask.save(api_mask_path)

    scale = 8
    preview = source.resize(
        (source.width * scale, source.height * scale),
        Image.Resampling.NEAREST,
    )
    translucent_red = Image.new(
        "RGBA",
        preview.size,
        (0, 0, 0, 0),
    )
    mask_scale = mask.resize(preview.size, Image.Resampling.NEAREST)
    for y in range(preview.height):
        for x in range(preview.width):
            if mask_scale.getpixel((x, y))[3]:
                translucent_red.putpixel((x, y), (255, 40, 40, 130))
    preview.alpha_composite(translucent_red)
    preview.save(preview_path)

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3r-mask-v1",
        "input": input_path.relative_to(ROOT).as_posix(),
        "input_sha256": source_hash,
        "mask": mask_path.relative_to(ROOT).as_posix(),
        "mask_sha256": sha256(mask_path),
        "api_mask": api_mask_path.relative_to(ROOT).as_posix(),
        "api_mask_sha256": sha256(api_mask_path),
        "mask_rect": list(MASK_RECT),
        "mask_size": list(mask.size),
        "alpha_values": alpha_values,
        "covered_pixels": (MASK_RECT[2] - MASK_RECT[0])
        * (MASK_RECT[3] - MASK_RECT[1]),
        "generation_submissions": 0,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
