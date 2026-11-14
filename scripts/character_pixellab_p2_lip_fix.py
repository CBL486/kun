from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


EXPECTED_SOURCE_SIZE = (64, 96)
EXPECTED_SOURCE_SHA256 = (
    "45E21D3EDABBB201239B359EAAFFDD9C"
    "74EC23A5584880914CA6FE10E178AA47"
)
EXPECTED_MOUTH_PIXEL = (181, 169, 188, 255)
EXPECTED_SHADOW_PIXEL = (250, 212, 202, 255)

LIP_COLOR = (184, 95, 108, 255)
LIP_SHADOW = (141, 70, 84, 255)
MOUTH_LINE = ((29, 53), (30, 53), (31, 53))
MOUTH_SHADOW = ((30, 54),)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def build_lip_fix(source_path: Path) -> tuple[Image.Image, dict[str, object]]:
    source_hash = sha256(source_path)
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"unexpected P1 source SHA-256: {source_hash}"
        )

    source = Image.open(source_path).convert("RGBA")
    if source.size != EXPECTED_SOURCE_SIZE:
        raise ValueError(f"unexpected P1 source size: {source.size}")

    for point in MOUTH_LINE:
        actual = source.getpixel(point)
        if actual != EXPECTED_MOUTH_PIXEL:
            raise ValueError(
                f"unexpected mouth pixel at {point}: {actual}"
            )
    for point in MOUTH_SHADOW:
        actual = source.getpixel(point)
        if actual != EXPECTED_SHADOW_PIXEL:
            raise ValueError(
                f"unexpected lower-lip pixel at {point}: {actual}"
            )

    fixed = source.copy()
    for point in MOUTH_LINE:
        fixed.putpixel(point, LIP_COLOR)
    for point in MOUTH_SHADOW:
        fixed.putpixel(point, LIP_SHADOW)

    difference = ImageChops.difference(source, fixed).convert("RGB")
    changed_bbox = difference.getbbox()
    if changed_bbox != (29, 53, 32, 55):
        raise ValueError(f"lip fix escaped the mouth region: {changed_bbox}")

    pixels = [
        fixed.getpixel((x, y))
        for y in range(fixed.height)
        for x in range(fixed.width)
    ]
    palette = set(pixels)
    opaque_colors = [color for color in palette if color[3] != 0]
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")
    if len(palette) > 24:
        raise ValueError(f"palette exceeds 24 colors: {len(palette)}")

    metrics: dict[str, object] = {
        "schema_version": "rpg-character-pixellab-p2-lip-v1",
        "source": (
            "art-source/character-v2/pixellab/P1/cleaned-64x96.png"
        ),
        "source_sha256": source_hash,
        "size": list(fixed.size),
        "lip_colors": ["#B85F6C", "#8D4654"],
        "colors": len(palette),
        "opaque_colors": len(opaque_colors),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": sum(
            1 for color in pixels if color[3] not in (0, 255)
        ),
        "changed_region": "mouth-only",
        "changed_pixels": len(MOUTH_LINE) + len(MOUTH_SHADOW),
        "changed_bbox": list(changed_bbox),
        "mouth_line": [list(point) for point in MOUTH_LINE],
        "mouth_shadow": [list(point) for point in MOUTH_SHADOW],
    }
    return fixed, metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply the deterministic PixelLab P2 rose-lip fix."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            "art-source/character-v2/pixellab/P1/cleaned-64x96.png"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("art-source/character-v2/pixellab/P2"),
    )
    parser.add_argument("--preview-scale", type=int, default=8)
    args = parser.parse_args()

    if args.preview_scale < 1:
        raise ValueError("preview scale must be positive")

    fixed, metrics = build_lip_fix(args.source)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fixed_path = args.output_dir / "lip-fixed-64x96.png"
    preview_path = args.output_dir / "lip-fixed-preview-8x.png"
    metrics_path = args.output_dir / "lip-metrics.json"

    fixed.save(fixed_path)
    fixed.resize(
        (
            fixed.width * args.preview_scale,
            fixed.height * args.preview_scale,
        ),
        Image.Resampling.NEAREST,
    ).save(preview_path)

    metrics["output"] = fixed_path.as_posix()
    metrics["output_sha256"] = sha256(fixed_path)
    metrics["preview"] = preview_path.as_posix()
    metrics["preview_scale"] = args.preview_scale
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
