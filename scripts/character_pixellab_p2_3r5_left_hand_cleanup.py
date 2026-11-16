from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
INPUT = (
    ROOT
    / "art-source/character-v2/pixellab/P2-3R4"
    / "down-left-skirt-cleaned.png"
)
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-3R5"
EXPECTED_INPUT_SHA256 = (
    "4B51182AA44702F47DB84B014B52DF5ADDD3CCA5D961B21177F85D5557D9B9A2"
)
EXPECTED_SIZE = (64, 96)
ALLOWED_REGION = (9, 68, 20, 84)

MASK_SPANS = {
    69: (14, 18),
    70: (13, 19),
    71: (13, 19),
    72: (12, 18),
    73: (12, 18),
    74: (11, 17),
    75: (10, 16),
    76: (10, 16),
    77: (10, 16),
    78: (10, 16),
    79: (10, 15),
    80: (10, 15),
}
MASK_POINTS = frozenset(
    (x, y)
    for y, (left, right) in MASK_SPANS.items()
    for x in range(left, right)
)

SOFT_LIP = (201, 120, 130, 255)
SOFT_LIP_SHADOW = (160, 93, 99, 255)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def checkerboard(size: tuple[int, int], cell: int = 8) -> Image.Image:
    image = Image.new("RGBA", size, (230, 230, 230, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle(
                    (x, y, x + cell - 1, y + cell - 1),
                    fill=(196, 196, 196, 255),
                )
    return image


def preview_panels(image: Image.Image, scale: int) -> Image.Image:
    labels = ("LIGHT", "DARK", "CHECKER")
    scaled = image.resize(
        (image.width * scale, image.height * scale),
        Image.Resampling.NEAREST,
    )
    margin = 18
    label_height = 26
    canvas = Image.new(
        "RGBA",
        (
            scaled.width * len(labels) + margin * (len(labels) + 1),
            scaled.height + label_height + margin * 2,
        ),
        (238, 238, 238, 255),
    )
    draw = ImageDraw.Draw(canvas)
    backgrounds = {
        "LIGHT": Image.new("RGBA", scaled.size, (247, 245, 239, 255)),
        "DARK": Image.new("RGBA", scaled.size, (24, 29, 39, 255)),
        "CHECKER": checkerboard(scaled.size),
    }
    for index, label in enumerate(labels):
        x = margin + index * (scaled.width + margin)
        y = label_height + margin
        panel = backgrounds[label].copy()
        panel.alpha_composite(scaled)
        canvas.alpha_composite(panel, (x, y))
        draw.text((x, 8), label, fill=(20, 20, 20, 255))
        draw.rectangle(
            (x, y, x + scaled.width - 1, y + scaled.height - 1),
            outline=(70, 70, 70, 255),
        )
    return canvas


def four_panel_preview(
    before: Image.Image,
    mask: Image.Image,
    after: Image.Image,
    changed: set[tuple[int, int]],
) -> Image.Image:
    scale = 16
    panel_width = before.width * scale
    panel_height = before.height * scale
    margin = 20
    label_height = 28
    canvas = Image.new(
        "RGBA",
        (
            panel_width * 4 + margin * 5,
            panel_height + label_height + margin * 2,
        ),
        (233, 233, 233, 255),
    )
    draw = ImageDraw.Draw(canvas)

    mask_overlay = before.copy()
    for y in range(before.height):
        for x in range(before.width):
            if mask.getpixel((x, y))[3]:
                mask_overlay.putpixel((x, y), (255, 0, 180, 255))

    diff = Image.new("RGBA", before.size, (28, 31, 39, 255))
    for y in range(before.height):
        for x in range(before.width):
            point = (x, y)
            if point in changed:
                diff.putpixel(point, (255, 0, 180, 255))
            elif before.getpixel(point)[3]:
                r, g, b, a = before.getpixel(point)
                diff.putpixel(
                    point,
                    (r // 4 + 18, g // 4 + 18, b // 4 + 18, a),
                )
            else:
                diff.putpixel(point, (0, 0, 0, 0))

    panels = (
        ("BEFORE", before),
        ("MASK", mask_overlay),
        ("AFTER", after),
        ("DIFF", diff),
    )
    for index, (label, panel) in enumerate(panels):
        x = margin + index * (panel_width + margin)
        y = label_height + margin
        upscaled = panel.resize(
            (panel_width, panel_height),
            Image.Resampling.NEAREST,
        )
        background = Image.new("RGBA", upscaled.size, (247, 245, 239, 255))
        background.alpha_composite(upscaled)
        canvas.alpha_composite(background, (x, y))
        draw.text((x, 8), label, fill=(20, 20, 20, 255))
        draw.rectangle(
            (x, y, x + panel_width - 1, y + panel_height - 1),
            outline=(70, 70, 70, 255),
        )
    return canvas


def hand_grid_preview(
    image: Image.Image,
    mask: Image.Image,
    hand_bbox: list[int],
) -> Image.Image:
    crop_box = (8, 67, 22, 85)
    scale = 32
    crop = image.crop(crop_box)
    background = Image.new("RGBA", crop.size, (247, 245, 239, 255))
    background.alpha_composite(crop)
    upscaled = background.resize(
        (crop.width * scale, crop.height * scale),
        Image.Resampling.NEAREST,
    )
    margin_left = 56
    margin_top = 36
    legend_width = 190
    canvas = Image.new(
        "RGBA",
        (
            upscaled.width + margin_left + legend_width,
            upscaled.height + margin_top,
        ),
        (238, 238, 238, 255),
    )
    canvas.alpha_composite(upscaled, (margin_left, margin_top))
    draw = ImageDraw.Draw(canvas)
    for index in range(crop.width):
        x = margin_left + index * scale
        draw.text(
            (x + 5, 8),
            str(crop_box[0] + index),
            fill=(0, 0, 0, 255),
        )
        draw.line(
            (x, margin_top, x, margin_top + upscaled.height),
            fill=(130, 130, 130, 255),
        )
    for index in range(crop.height):
        y = margin_top + index * scale
        draw.text(
            (8, y + 8),
            str(crop_box[1] + index),
            fill=(0, 0, 0, 255),
        )
        draw.line(
            (margin_left, y, margin_left + upscaled.width, y),
            fill=(130, 130, 130, 255),
        )
    left = margin_left + (ALLOWED_REGION[0] - crop_box[0]) * scale
    top = margin_top + (ALLOWED_REGION[1] - crop_box[1]) * scale
    right = margin_left + (ALLOWED_REGION[2] - crop_box[0]) * scale
    bottom = margin_top + (ALLOWED_REGION[3] - crop_box[1]) * scale
    draw.rectangle((left, top, right, bottom), outline=(255, 70, 70, 255), width=3)
    hand_left = margin_left + (hand_bbox[0] - crop_box[0]) * scale
    hand_top = margin_top + (hand_bbox[1] - crop_box[1]) * scale
    hand_right = margin_left + (hand_bbox[2] - crop_box[0]) * scale
    hand_bottom = margin_top + (hand_bbox[3] - crop_box[1]) * scale
    draw.rectangle(
        (hand_left, hand_top, hand_right, hand_bottom),
        outline=(0, 190, 255, 255),
        width=3,
    )
    annotations = (
        ("WRIST", (16.5, 69.5), (255, 180, 0, 255), 55),
        ("WHITE CUFF", (15.0, 71.5), (0, 170, 90, 255), 115),
        ("PALM", (12.5, 76.0), (230, 110, 20, 255), 175),
        ("THUMB / ROUND", (10.5, 76.5), (150, 80, 210, 255), 235),
        ("BOTTOM y=79", (13.5, 79.0), (220, 20, 90, 255), 295),
    )
    label_x = margin_left + upscaled.width + 12
    for label, (target_x, target_y), color, label_y in annotations:
        target_px = (
            margin_left + int((target_x - crop_box[0] + 0.5) * scale),
            margin_top + int((target_y - crop_box[1] + 0.5) * scale),
        )
        draw.line((target_px[0], target_px[1], label_x - 8, label_y + 6), fill=color, width=2)
        draw.ellipse(
            (
                target_px[0] - 5,
                target_px[1] - 5,
                target_px[0] + 5,
                target_px[1] + 5,
            ),
            outline=color,
            width=2,
        )
        draw.text((label_x, label_y), label, fill=color)
    draw.text(
        (margin_left, canvas.height - 20),
        "BLUE=HAND BBOX  RED=ALLOWED",
        fill=(0, 0, 0, 255),
    )
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


def opaque_components(
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> list[list[tuple[int, int]]]:
    left, top, right, bottom = box
    remaining = {
        (x, y)
        for y in range(top, bottom)
        for x in range(left, right)
        if image.getpixel((x, y))[3] != 0
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        seed = remaining.pop()
        queue = deque([seed])
        component = [seed]
        while queue:
            x, y = queue.popleft()
            for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if point in remaining:
                    remaining.remove(point)
                    queue.append(point)
                    component.append(point)
        components.append(component)
    return sorted(components, key=len, reverse=True)


def mask_image() -> Image.Image:
    mask = Image.new("RGBA", EXPECTED_SIZE, (0, 0, 0, 0))
    for x, y in MASK_POINTS:
        mask.putpixel((x, y), (255, 255, 255, 255))
    return mask


def prepare() -> None:
    if sha256(INPUT) != EXPECTED_INPUT_SHA256:
        raise ValueError("unexpected P2-3R4 input SHA-256")
    source = Image.open(INPUT).convert("RGBA")
    if source.size != EXPECTED_SIZE:
        raise ValueError(f"unexpected input size: {source.size}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    input_path = OUTPUT_DIR / "input-down-left-skirt-cleaned.png"
    mask_path = OUTPUT_DIR / "left-hand-mask.png"
    api_mask_path = OUTPUT_DIR / "left-hand-mask-api.png"
    preview_path = OUTPUT_DIR / "left-hand-mask-preview-16x.png"
    metrics_path = OUTPUT_DIR / "mask-metrics.json"

    input_path.write_bytes(INPUT.read_bytes())
    mask = mask_image()
    mask.save(mask_path)
    api_mask = Image.new("RGB", EXPECTED_SIZE, (0, 0, 0))
    for x, y in MASK_POINTS:
        api_mask.putpixel((x, y), (255, 255, 255))
    api_mask.save(api_mask_path)

    preview = source.copy()
    for x, y in MASK_POINTS:
        preview.putpixel((x, y), (255, 0, 180, 255))
    preview.resize(
        (preview.width * 16, preview.height * 16),
        Image.Resampling.NEAREST,
    ).save(preview_path)

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3r5-mask-v1",
        "input": input_path.relative_to(ROOT).as_posix(),
        "input_sha256": sha256(input_path),
        "mask": mask_path.relative_to(ROOT).as_posix(),
        "mask_sha256": sha256(mask_path),
        "api_mask": api_mask_path.relative_to(ROOT).as_posix(),
        "api_mask_sha256": sha256(api_mask_path),
        "allowed_region": list(ALLOWED_REGION),
        "mask_spans": {str(y): [left, right - 1] for y, (left, right) in MASK_SPANS.items()},
        "mask_pixel_count": len(MASK_POINTS),
        "alpha_values": [0, 255],
        "generation_submissions": 0,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


def audit(raw_path: Path) -> None:
    source = Image.open(INPUT).convert("RGBA")
    raw = Image.open(raw_path).convert("RGBA")
    mask = mask_image()
    if source.size != EXPECTED_SIZE or raw.size != EXPECTED_SIZE:
        raise ValueError("unexpected image dimensions")

    hand_palette = tuple(
        sorted(
            set(source.get_flattened_data()) - {SOFT_LIP, SOFT_LIP_SHADOW},
            key=lambda color: (color[3], color[0], color[1], color[2]),
        )
    )
    raw_changed_outside = [
        (x, y)
        for y in range(source.height)
        for x in range(source.width)
        if (x, y) not in MASK_POINTS
        and source.getpixel((x, y)) != raw.getpixel((x, y))
    ]
    cleaned = source.copy()
    blue_to_skin_shadow: list[tuple[int, int]] = []
    for y in range(source.height):
        for x in range(source.width):
            if mask.getpixel((x, y))[3]:
                color = nearest_color(raw.getpixel((x, y)), hand_palette)
                if y >= 73 and color == (129, 143, 176, 255):
                    color = (181, 169, 188, 255)
                    blue_to_skin_shadow.append((x, y))
                cleaned.putpixel((x, y), color)

    changed = {
        (x, y)
        for y in range(source.height)
        for x in range(source.width)
        if source.getpixel((x, y)) != cleaned.getpixel((x, y))
    }
    changed_outside = [
        point
        for point in changed
        if point not in MASK_POINTS
    ]
    if changed_outside:
        raise ValueError(f"changed pixels outside mask: {changed_outside[:8]}")

    palette = set(cleaned.get_flattened_data())
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")
    if len(palette) > 22:
        raise ValueError(f"palette exceeds 22 colors: {len(palette)}")

    hand_points = [
        (x, y)
        for x, y in MASK_POINTS
        if cleaned.getpixel((x, y))[3] != 0
    ]
    if not hand_points:
        raise ValueError("generated hand is empty")
    hand_bbox = [
        min(x for x, _ in hand_points),
        min(y for _, y in hand_points),
        max(x for x, _ in hand_points) + 1,
        max(y for _, y in hand_points) + 1,
    ]
    hand_width_by_row = {
        str(y): sum(
            1
            for x in range(ALLOWED_REGION[0], ALLOWED_REGION[2])
            if (x, y) in MASK_POINTS and cleaned.getpixel((x, y))[3] != 0
        )
        for y in range(ALLOWED_REGION[1], min(81, ALLOWED_REGION[3]))
    }
    palm_skin_width_by_row = {
        str(y): sum(
            1
            for x in range(ALLOWED_REGION[0], ALLOWED_REGION[2])
            if (x, y) in MASK_POINTS
            and cleaned.getpixel((x, y))
            in {(250, 212, 202, 255), (181, 169, 188, 255)}
        )
        for y in range(73, min(80, ALLOWED_REGION[3]))
    }
    skin_pixels = sum(
        1
        for x, y in hand_points
        if cleaned.getpixel((x, y)) in {
            (250, 212, 202, 255),
            (181, 169, 188, 255),
        }
    )
    cuff_pixels = sum(
        1
        for x, y in hand_points
        if cleaned.getpixel((x, y)) in {
            (230, 227, 230, 255),
            (245, 244, 234, 255),
            (186, 200, 221, 255),
            (129, 143, 176, 255),
        }
    )
    hand_bottom = hand_bbox[3] - 1
    if hand_bottom > 80:
        raise ValueError(f"hand extends below y=80: {hand_bottom}")
    allowed_components = opaque_components(cleaned, ALLOWED_REGION)
    hand_connected = len(allowed_components) == 1
    palm_readable = (
        max(palm_skin_width_by_row.values(), default=0) >= 3
        and sum(palm_skin_width_by_row.values()) >= 12
    )
    rounded_contour = (
        max(hand_width_by_row.values(), default=0)
        > hand_width_by_row.get("79", 0)
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_output = OUTPUT_DIR / "down-left-hand-raw.png"
    cleaned_output = OUTPUT_DIR / "down-left-hand-cleaned.png"
    diff_output = OUTPUT_DIR / "down-left-hand-diff-16x.png"
    grid_output = OUTPUT_DIR / "down-left-hand-grid-32x.png"
    runtime_output = OUTPUT_DIR / "runtime-48x72-preview-8x.png"
    metrics_output = OUTPUT_DIR / "metrics.json"
    visual_output = OUTPUT_DIR / "visual-review.json"

    raw_output.write_bytes(raw_path.read_bytes())
    cleaned.save(cleaned_output)
    four_panel_preview(source, mask, cleaned, changed).save(diff_output)
    hand_grid_preview(cleaned, mask, hand_bbox).save(grid_output)
    runtime = cleaned.resize((48, 72), Image.Resampling.NEAREST)
    preview_panels(runtime, 8).save(runtime_output)

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3r5-left-hand-v1",
        "input": INPUT.relative_to(ROOT).as_posix(),
        "input_sha256": sha256(INPUT),
        "raw": raw_output.relative_to(ROOT).as_posix(),
        "raw_sha256": sha256(raw_output),
        "output": cleaned_output.relative_to(ROOT).as_posix(),
        "output_sha256": sha256(cleaned_output),
        "allowed_region": list(ALLOWED_REGION),
        "mask_pixel_count": len(MASK_POINTS),
        "changed_pixels_inside_mask": len(changed),
        "changed_pixels_outside_mask": len(changed_outside),
        "raw_changed_pixels_outside_mask": len(raw_changed_outside),
        "outside_mask_restored_from_input": len(raw_changed_outside),
        "hand_bbox": hand_bbox,
        "hand_bottom_y": hand_bottom,
        "hand_pixel_count": len(hand_points),
        "hand_width_by_row": hand_width_by_row,
        "palm_skin_width_by_row": palm_skin_width_by_row,
        "skin_pixels_in_mask": skin_pixels,
        "cuff_pixels_in_mask": cuff_pixels,
        "palm_blue_mapped_to_skin_shadow": blue_to_skin_shadow,
        "soft_lip_colors_inside_hand_mask": sum(
            1
            for x, y in MASK_POINTS
            if cleaned.getpixel((x, y)) in {SOFT_LIP, SOFT_LIP_SHADOW}
        ),
        "opaque_components_in_allowed_region": len(allowed_components),
        "hand_connected_to_arm": hand_connected,
        "palm_readable": palm_readable,
        "rounded_contour_readable": rounded_contour,
        "colors": len(palette),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": sum(
            1
            for y in range(cleaned.height)
            for x in range(cleaned.width)
            if cleaned.getpixel((x, y))[3] not in (0, 255)
        ),
        "lip_colors_present": {
            "#C97882": SOFT_LIP in palette,
            "#A05D63": SOFT_LIP_SHADOW in palette,
        },
        "generation_submissions": 1,
        "generation_requests": 1,
        "generations_used": 10,
        "pixellab_calls": 1,
        "animation_started": False,
        "production_modified": False,
    }
    metrics_output.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    visual = {
        "schema_version": "rpg-character-pixellab-p2-3r5-visual-review-v1",
        "status": "technical-check-pending-visual-confirmation",
        "hand_connected_to_arm": hand_connected,
        "palm_readable": palm_readable,
        "thumb_or_round_contour_readable": rounded_contour,
        "cuff_visible": cuff_pixels > 0,
        "hand_no_long_strip": hand_bottom <= 80,
        "outside_mask_changes": 0,
        "user_confirmation": "pending",
        "four_direction_authorized": False,
        "animation_authorized": False,
    }
    visual_output.write_text(
        json.dumps(visual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument(
        "--raw",
        type=Path,
        default=OUTPUT_DIR / "down-left-hand-raw.png",
    )
    args = parser.parse_args()
    if args.prepare:
        prepare()
    else:
        audit(args.raw)


if __name__ == "__main__":
    main()
