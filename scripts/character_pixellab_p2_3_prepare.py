from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art-source/character-v2/pixellab/P2/sprite-4dir-cleaned.png"
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-3"
EXPECTED_SOURCE_SHA256 = (
    "ACFFDB829384987DA361150F82CC036F"
    "66C0847B16C81C55705061A4AFD55DB8"
)
OLD_LIP = (184, 95, 108, 255)
OLD_LIP_SHADOW = (141, 70, 84, 255)
NEW_LIP = (201, 120, 130, 255)
NEW_LIP_SHADOW = (160, 93, 99, 255)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    source_hash = sha256(SOURCE)
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"unexpected P2-2 source SHA-256: {source_hash}")

    sheet = Image.open(SOURCE).convert("RGBA")
    if sheet.size != (256, 96):
        raise ValueError(f"unexpected sheet size: {sheet.size}")
    before = sheet.crop((0, 0, 64, 96))

    old_lip_pixels: list[tuple[int, int]] = []
    old_shadow_pixels: list[tuple[int, int]] = []
    for y in range(before.height):
        for x in range(before.width):
            color = before.getpixel((x, y))
            if color == OLD_LIP:
                old_lip_pixels.append((x, y))
            elif color == OLD_LIP_SHADOW:
                old_shadow_pixels.append((x, y))
    if len(old_lip_pixels) != 3 or len(old_shadow_pixels) != 1:
        raise ValueError(
            "unexpected lip pixel counts: "
            f"main={len(old_lip_pixels)} shadow={len(old_shadow_pixels)}"
        )

    after = before.copy()
    for point in old_lip_pixels:
        after.putpixel(point, NEW_LIP)
    for point in old_shadow_pixels:
        after.putpixel(point, NEW_LIP_SHADOW)

    changed = [
        (x, y)
        for y in range(before.height)
        for x in range(before.width)
        if before.getpixel((x, y)) != after.getpixel((x, y))
    ]
    if changed != sorted(old_lip_pixels + old_shadow_pixels, key=lambda p: (p[1], p[0])):
        raise ValueError(f"unexpected changed lip pixels: {changed}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    input_path = OUTPUT_DIR / "input-down-soft-lips-64x96.png"
    preview_path = OUTPUT_DIR / "lip-preview-8x.png"
    metrics_path = OUTPUT_DIR / "prepare-metrics.json"
    after.save(input_path)

    crop = (16, 22, 48, 60)
    scale = 8
    crop_w = (crop[2] - crop[0]) * scale
    crop_h = (crop[3] - crop[1]) * scale
    margin = 18
    header = 34
    canvas = Image.new("RGBA", (crop_w * 2 + margin * 3, crop_h + header + margin * 2), (23, 27, 34, 255))
    draw = ImageDraw.Draw(canvas)
    labels = ("P2-2 LIPS", "P2-3 SOFT LIPS")
    for index, (label, image) in enumerate(((labels[0], before), (labels[1], after))):
        x = margin + index * (crop_w + margin)
        y = header + margin
        draw.text((x + 4, 8), label, fill=(255, 255, 255, 255))
        zoomed = image.crop(crop).resize((crop_w, crop_h), Image.Resampling.NEAREST)
        canvas.alpha_composite(zoomed, (x, y))
        draw.rectangle((x, y, x + crop_w, y + crop_h), outline=(88, 96, 108, 255))
    canvas.save(preview_path)

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3-prepare-v1",
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": source_hash,
        "output": input_path.relative_to(ROOT).as_posix(),
        "output_sha256": sha256(input_path),
        "size": list(after.size),
        "old_lip_colors": ["#B85F6C", "#8D4654"],
        "new_lip_colors": ["#C97882", "#A05D63"],
        "changed_pixels": changed,
        "changed_pixel_count": len(changed),
        "alpha_values": [0, 255],
        "generation_submissions": 0,
        "pixellab_calls": 0,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
