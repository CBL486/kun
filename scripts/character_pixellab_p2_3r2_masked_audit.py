from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-3R2"
EXPECTED_SIZE = (64, 96)
SOFT_LIP = (201, 120, 130, 255)
SOFT_LIP_SHADOW = (160, 93, 99, 255)
SKIN_COLOR = (250, 212, 202, 255)
LEG_SCAN_CROP = (12, 72, 52, 90)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def components(
    image: Image.Image,
    predicate,
    offset: tuple[int, int] = (0, 0),
) -> list[dict[str, object]]:
    width, height = image.size
    remaining: set[tuple[int, int]] = set()
    for y in range(height):
        for x in range(width):
            if predicate(image.getpixel((x, y))):
                remaining.add((x, y))

    result: list[dict[str, object]] = []
    while remaining:
        seed = remaining.pop()
        queue = deque([seed])
        points = [seed]
        while queue:
            x, y = queue.popleft()
            for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if point in remaining:
                    remaining.remove(point)
                    queue.append(point)
                    points.append(point)
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        result.append(
            {
                "pixel_count": len(points),
                "bbox_half_open": [
                    min(xs) + offset[0],
                    min(ys) + offset[1],
                    max(xs) + 1 + offset[0],
                    max(ys) + 1 + offset[1],
                ],
            }
        )
    return sorted(
        result,
        key=lambda item: int(item["pixel_count"]),
        reverse=True,
    )


def build_preview(
    original: Image.Image,
    mask: Image.Image,
    raw_result: Image.Image,
    cleaned: Image.Image,
    model_label: str,
) -> Image.Image:
    crop = (8, 62, 56, 96)
    scale = 8
    width = (crop[2] - crop[0]) * scale
    height = (crop[3] - crop[1]) * scale
    canvas = Image.new("RGBA", (width * 4 + 90, height + 58), (235, 235, 235, 255))
    draw = ImageDraw.Draw(canvas)
    panels = (
        ("BEFORE", original),
        ("MASK", None),
        (model_label + " RAW", raw_result),
        ("CLEANED", cleaned),
    )
    for index, (label, image) in enumerate(panels):
        x = 18 + index * (width + 18)
        y = 34
        background = Image.new("RGBA", (width, height), (246, 243, 234, 255))
        if image is None:
            crop_image = original.crop(crop)
            mask_overlay = Image.new("RGBA", crop_image.size, (0, 0, 0, 0))
            for py in range(crop_image.height):
                for px in range(crop_image.width):
                    if mask.getpixel((px + crop[0], py + crop[1]))[3]:
                        mask_overlay.putpixel((px, py), (255, 40, 40, 130))
            crop_image.alpha_composite(mask_overlay)
        else:
            crop_image = image.crop(crop)
        background.alpha_composite(
            crop_image.resize(
                (width, height),
                Image.Resampling.NEAREST,
            )
        )
        canvas.alpha_composite(background, (x, y))
        draw.text((x, 10), label, fill=(0, 0, 0, 255))
        draw.rectangle((x, y, x + width, y + height), outline=(80, 80, 80, 255))
    return canvas


def nearest_color(
    color: tuple[int, int, int, int],
    palette: tuple[tuple[int, int, int, int], ...],
) -> tuple[int, int, int, int]:
    if color[3] == 0:
        return (0, 0, 0, 0)
    return min(
        palette,
        key=lambda candidate: (
            (color[0] - candidate[0]) ** 2
            + (color[1] - candidate[1]) ** 2
            + (color[2] - candidate[2]) ** 2
            + (color[3] - candidate[3]) ** 2
        ),
    )


def clean_masked_result(
    original: Image.Image,
    mask: Image.Image,
    result: Image.Image,
) -> Image.Image:
    original_palette = tuple(
        sorted(
            {
                original.getpixel((x, y))
                for y in range(original.height)
                for x in range(original.width)
            },
            key=lambda color: (color[3], color[0], color[1], color[2]),
        )
    )
    cleaned = original.copy()
    for y in range(original.height):
        for x in range(original.width):
            if mask.getpixel((x, y))[3] != 0:
                cleaned.putpixel(
                    (x, y),
                    nearest_color(result.getpixel((x, y)), original_palette),
                )
    return cleaned


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit the one allowed P2-3R2 corrected-mask result."
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
    parser.add_argument("--model-label", default="INPAINT")
    args = parser.parse_args()

    original = Image.open(args.input).convert("RGBA")
    mask = Image.open(args.mask).convert("RGBA")
    result = Image.open(args.result).convert("RGBA")
    for label, image in (("input", original), ("mask", mask), ("result", result)):
        if image.size != EXPECTED_SIZE:
            raise ValueError(f"unexpected {label} size: {image.size}")

    mask_bbox = mask.getbbox()
    if mask_bbox is None:
        raise ValueError("mask is empty")

    cleaned_path = args.output_dir / "down-masked-edit-cleaned.png"
    cleaned = clean_masked_result(original, mask, result)
    cleaned.save(cleaned_path)

    changes_inside: list[tuple[int, int]] = []
    changes_outside: list[tuple[int, int]] = []
    raw_changes_outside: list[tuple[int, int]] = []
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
                raw_changes_outside.append(point)
                if before[3] == 0 and after[3] != 0:
                    added_outside.append(point)
                elif before[3] != 0 and after[3] == 0:
                    removed_outside.append(point)

    for y in range(cleaned.height):
        for x in range(cleaned.width):
            if original.getpixel((x, y)) != cleaned.getpixel((x, y)):
                point = (x, y)
                if mask.getpixel(point)[3]:
                    changes_inside.append(point)
                else:
                    changes_outside.append(point)

    changes_inside = sorted(set(changes_inside))
    palette = set(cleaned.get_flattened_data())
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")

    leg_components = [
        component
        for component in components(
            cleaned.crop((18, 72, 42, 90)),
            lambda color: color == SKIN_COLOR,
            offset=(18, 72),
        )
        if int(component["pixel_count"]) >= 20
    ]
    leg_gap_px = None
    if len(leg_components) == 2:
        ordered_legs = sorted(
            leg_components,
            key=lambda component: int(component["bbox_half_open"][0]),
        )
        leg_gap_px = (
            int(ordered_legs[1]["bbox_half_open"][0])
            - int(ordered_legs[0]["bbox_half_open"][2])
        )

    boot_components = [
        component
        for component in components(
            cleaned.crop((18, 81, 39, 90)),
            lambda color: (
                color[3] == 255
                and color not in {SKIN_COLOR, SOFT_LIP, SOFT_LIP_SHADOW}
                and max(color[:3]) <= 90
            ),
            offset=(18, 81),
        )
        if int(component["pixel_count"]) >= 20
    ]
    boot_sole_edges = sorted(
        {
            int(component["bbox_half_open"][3])
            for component in boot_components
        }
    )

    skin_components = components(
        cleaned.crop(LEG_SCAN_CROP),
        lambda color: color == SKIN_COLOR,
        offset=(LEG_SCAN_CROP[0], LEG_SCAN_CROP[1]),
    )
    dark_lower_components = components(
        cleaned.crop((12, 81, 52, 90)),
        lambda color: (
            color[3] == 255
            and color not in {SKIN_COLOR, SOFT_LIP, SOFT_LIP_SHADOW}
            and max(color[:3]) <= 90
        ),
        offset=(12, 81),
    )

    output_path = args.output_dir / "down-masked-edit-preview-8x.png"
    metrics_path = args.output_dir / "down-masked-edit-metrics.json"
    build_preview(
        original,
        mask,
        result,
        cleaned,
        args.model_label,
    ).save(output_path)

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3r2-audit-v1",
        "model": "PixelLab Inpaint v3",
        "background_job_id": "7f8271e5-b905-4f84-878a-3b6f20a78a07",
        "generation_id": "b99cae13-c6a5-4fcf-9702-d6454dd9a753",
        "input": args.input.relative_to(ROOT).as_posix(),
        "input_sha256": sha256(args.input),
        "mask": args.mask.relative_to(ROOT).as_posix(),
        "mask_sha256": sha256(args.mask),
        "mask_bbox_half_open": list(mask_bbox),
        "mask_height": mask_bbox[3] - mask_bbox[1],
        "result": args.result.relative_to(ROOT).as_posix(),
        "result_sha256": sha256(args.result),
        "result_bbox": list(result.getbbox()) if result.getbbox() else None,
        "cleaned_result": cleaned_path.relative_to(ROOT).as_posix(),
        "cleaned_result_sha256": sha256(cleaned_path),
        "cleaned_result_bbox": (
            list(cleaned.getbbox()) if cleaned.getbbox() else None
        ),
        "changed_pixels_inside_mask": len(changes_inside),
        "changed_pixels_outside_mask": len(changes_outside),
        "raw_changed_pixels_outside_mask": len(raw_changes_outside),
        "raw_removed_opaque_pixels_outside_mask": len(removed_outside),
        "raw_added_opaque_pixels_outside_mask": len(added_outside),
        "outside_mask_restored_from_input": len(raw_changes_outside),
        "palette_mapped_to_input_palette": True,
        "skin_scan_crop": list(LEG_SCAN_CROP),
        "skin_components": skin_components,
        "skin_component_count": len(skin_components),
        "leg_components": leg_components,
        "two_legs_separated": len(leg_components) == 2,
        "leg_gap_px": leg_gap_px,
        "leg_gap_requirement_px": [1, 2],
        "leg_gap_pass": leg_gap_px is not None and 1 <= leg_gap_px <= 2,
        "boot_components": boot_components,
        "boot_count": len(boot_components),
        "boot_pixel_count": sum(
            int(component["pixel_count"]) for component in boot_components
        ),
        "boot_sole_edges": boot_sole_edges,
        "boot_soles_aligned": boot_sole_edges == [88],
        "dark_lower_components": dark_lower_components,
        "lip_colors_present": {
            "#C97882": SOFT_LIP in palette,
            "#A05D63": SOFT_LIP_SHADOW in palette,
        },
        "colors": len(palette),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": sum(
            1
            for y in range(cleaned.height)
            for x in range(cleaned.width)
            if cleaned.getpixel((x, y))[3] not in (0, 255)
        ),
        "generation_submissions": 1,
        "generation_requests": 1,
        "generations_used": 10,
        "animation_started": False,
        "production_modified": False,
        "status": (
            "pass"
            if leg_gap_px is not None
            and 1 <= leg_gap_px <= 2
            and len(boot_components) == 2
            and boot_sole_edges == [88]
            else "fail"
        ),
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
