from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


EXPECTED_DIRECTIONS = ["south", "west", "east", "north"]
EXPECTED_SHEET_SIZE = (384, 96)
EXPECTED_CELL_SIZE = (96, 96)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def opaque_pixel_match(left: Image.Image, right: Image.Image) -> tuple[int, int]:
    union = 0
    exact = 0
    for y in range(left.height):
        for x in range(left.width):
            a = left.getpixel((x, y))
            b = right.getpixel((x, y))
            if a[3] or b[3]:
                union += 1
                if a == b:
                    exact += 1
    return exact, union


def build_preview(sheet: Image.Image, scale: int = 4) -> Image.Image:
    cell_width, cell_height = EXPECTED_CELL_SIZE
    gutter = 4
    top_margin = 24
    width = len(EXPECTED_DIRECTIONS) * cell_width * scale + (
        len(EXPECTED_DIRECTIONS) - 1
    ) * gutter
    height = cell_height * scale + top_margin
    preview = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(preview)

    for index, direction in enumerate(EXPECTED_DIRECTIONS):
        cell = sheet.crop(
            (
                index * cell_width,
                0,
                (index + 1) * cell_width,
                cell_height,
            )
        ).resize(
            (cell_width * scale, cell_height * scale),
            Image.Resampling.NEAREST,
        )
        x = index * (cell_width * scale + gutter)
        preview.alpha_composite(cell, (x, top_margin))
        draw.text((x + 4, 4), direction.upper(), fill=(0, 0, 0, 255))
        if index:
            draw.line(
                (x - gutter // 2, 0, x - gutter // 2, height),
                fill=(255, 0, 0, 255),
                width=1,
            )
    return preview


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate and preserve the raw PixelLab P2 four-direction export."
    )
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--source-down", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("art-source/character-v2/pixellab/P2"),
    )
    parser.add_argument("--preview-scale", type=int, default=4)
    args = parser.parse_args()

    if args.preview_scale < 1:
        raise ValueError("preview scale must be positive")

    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    sheet = Image.open(args.sheet).convert("RGBA")
    if sheet.size != EXPECTED_SHEET_SIZE:
        raise ValueError(f"unexpected spritesheet size: {sheet.size}")

    sprite_data = metadata.get("spritesheet", {})
    if sprite_data.get("cell_size") != {
        "width": EXPECTED_CELL_SIZE[0],
        "height": EXPECTED_CELL_SIZE[1],
    }:
        raise ValueError("metadata cell size does not match the raw export")
    rows = sprite_data.get("rows", [])
    if len(rows) != 1 or rows[0].get("directions") != EXPECTED_DIRECTIONS:
        raise ValueError("metadata directions are not south/west/east/north")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / "sprite-4dir-raw.png"
    raw_metadata_path = args.output_dir / "sprite-4dir-raw.json"
    preview_path = args.output_dir / "sprite-4dir-raw-preview-4x.png"
    source_path = args.output_dir / "source-down.png"
    metrics_path = args.output_dir / "metrics-4dir-raw.json"

    shutil.copyfile(args.sheet, raw_path)
    shutil.copyfile(args.metadata, raw_metadata_path)
    shutil.copyfile(args.source_down, source_path)
    build_preview(sheet, args.preview_scale).save(preview_path)

    pixels = [
        sheet.getpixel((x, y))
        for y in range(sheet.height)
        for x in range(sheet.width)
    ]
    palette = set(pixels)
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")

    cells = {}
    cell_images = []
    for index, direction in enumerate(EXPECTED_DIRECTIONS):
        cell = sheet.crop(
            (
                index * EXPECTED_CELL_SIZE[0],
                0,
                (index + 1) * EXPECTED_CELL_SIZE[0],
                EXPECTED_CELL_SIZE[1],
            )
        )
        cell_images.append(cell)
        bbox = cell.getbbox()
        cells[direction] = {
            "bbox": list(bbox) if bbox else None,
            "width": (bbox[2] - bbox[0]) if bbox else 0,
            "height": (bbox[3] - bbox[1]) if bbox else 0,
        }

    west_vs_flipped_east = cell_images[2].transpose(
        Image.Transpose.FLIP_LEFT_RIGHT
    )
    mirror_exact, opaque_union = opaque_pixel_match(
        cell_images[1], west_vs_flipped_east
    )

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-4dir-raw-audit-v1",
        "status": "blocked",
        "blocker": "north whale tail is not visibly readable",
        "source_down": source_path.as_posix(),
        "source_down_sha256": sha256(source_path),
        "raw_sheet": raw_path.as_posix(),
        "raw_sheet_sha256": sha256(raw_path),
        "raw_metadata": raw_metadata_path.as_posix(),
        "sheet_size": list(sheet.size),
        "cell_size": list(EXPECTED_CELL_SIZE),
        "direction_order": EXPECTED_DIRECTIONS,
        "colors": len(palette),
        "opaque_colors": sum(1 for color in palette if color[3] != 0),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": sum(
            1 for color in pixels if color[3] not in (0, 255)
        ),
        "cells": cells,
        "west_vs_flipped_east": {
            "opaque_union_pixels": opaque_union,
            "exact_matching_pixels": mirror_exact,
            "exact_ratio": round(mirror_exact / opaque_union, 6),
        },
        "visual_acceptance": {
            "south": "pass",
            "west": "pass",
            "east": "pass",
            "north_back_hair": "pass",
            "north_back_clothing": "pass",
            "north_whale_tail": "fail-not-readable",
        },
        "cleaned_asset_created": False,
        "map_screenshots_created": False,
        "generation_count": 1,
        "animation_started": False,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
