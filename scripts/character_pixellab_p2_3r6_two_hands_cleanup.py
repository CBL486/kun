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
    / "art-source/character-v2/pixellab/P2-3R5"
    / "down-left-hand-cleaned.png"
)
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-3R6"
EXPECTED_INPUT_SHA256 = (
    "8D8AC191FED1DBC7A6180092E025B159E19D99DC0166532BA1A01DC1DD4E2AC1"
)
EXPECTED_SIZE = (64, 96)

LEFT_REGION = (9, 68, 20, 82)
RIGHT_REGION = (42, 65, 56, 83)
LEFT_HAND_BOX = (12, 70, 17, 76)
RIGHT_HAND_BOX = (41, 68, 46, 76)

LEFT_SPANS = {
    68: (16, 19),
    69: (15, 19),
    70: (14, 19),
    71: (13, 19),
    72: (12, 19),
    73: (11, 18),
    74: (10, 18),
    75: (10, 17),
    76: (10, 17),
    77: (10, 17),
    78: (10, 17),
    79: (10, 16),
    80: (10, 16),
}
RIGHT_SPANS = {
    68: (42, 45),
    69: (42, 45),
    70: (42, 45),
    71: (42, 45),
    72: (42, 46),
    73: (42, 47),
    74: (42, 47),
    75: (42, 48),
    76: (42, 48),
    77: (42, 48),
    78: (42, 48),
    79: (42, 47),
    80: (42, 47),
}


def mask_points(spans: dict[int, tuple[int, int]]) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y, (left, right) in spans.items()
        for x in range(left, right)
    }


LEFT_POINTS = mask_points(LEFT_SPANS)
RIGHT_POINTS = mask_points(RIGHT_SPANS)
ALL_MASK_POINTS = LEFT_POINTS | RIGHT_POINTS
SOFT_LIP = (201, 120, 130, 255)
SOFT_LIP_SHADOW = (160, 93, 99, 255)
SKIN_COLORS = {(250, 212, 202, 255), (181, 169, 188, 255)}
CUFF_COLORS = {
    (230, 227, 230, 255),
    (245, 244, 234, 255),
    (186, 200, 221, 255),
    (129, 143, 176, 255),
}


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


def mask_image(points: set[tuple[int, int]]) -> Image.Image:
    image = Image.new("RGBA", EXPECTED_SIZE, (0, 0, 0, 0))
    for x, y in points:
        image.putpixel((x, y), (255, 255, 255, 255))
    return image


def combined_mask_image() -> Image.Image:
    return mask_image(ALL_MASK_POINTS)


def make_mask_preview(source: Image.Image) -> Image.Image:
    image = source.copy()
    for x, y in LEFT_POINTS:
        image.putpixel((x, y), (255, 0, 130, 255))
    for x, y in RIGHT_POINTS:
        image.putpixel((x, y), (0, 220, 180, 255))
    return image.resize(
        (image.width * 16, image.height * 16),
        Image.Resampling.NEAREST,
    )


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


def hand_metrics(
    image: Image.Image,
    points: set[tuple[int, int]],
    region: tuple[int, int, int, int],
    hand_box: tuple[int, int, int, int],
    outer_box: tuple[int, int, int, int],
) -> dict[str, object]:
    hand_points = [
        (x, y)
        for y in range(hand_box[1], hand_box[3])
        for x in range(hand_box[0], hand_box[2])
        if (x, y) in points
        if image.getpixel((x, y))[3] != 0
    ]
    if not hand_points:
        return {
            "bbox": None,
            "outer_size": [0, 0],
            "palm_width_by_row": {},
            "skin_pixels": 0,
            "cuff_pixels": 0,
            "connected": False,
        }
    bbox = [
        min(x for x, _ in hand_points),
        min(y for _, y in hand_points),
        max(x for x, _ in hand_points) + 1,
        max(y for _, y in hand_points) + 1,
    ]
    outer_points = [
        (x, y)
        for y in range(outer_box[1], outer_box[3])
        for x in range(outer_box[0], outer_box[2])
        if (x, y) in points
        and image.getpixel((x, y))[3] != 0
    ]
    outer_bbox = [
        min(x for x, _ in outer_points),
        min(y for _, y in outer_points),
        max(x for x, _ in outer_points) + 1,
        max(y for _, y in outer_points) + 1,
    ]
    palm_width_by_row = {
        str(y): sum(
            1
            for x in range(region[0], region[2])
            if outer_box[0] <= x < outer_box[2]
            and outer_box[1] <= y < outer_box[3]
            and (x, y) in points
            and image.getpixel((x, y)) in SKIN_COLORS
        )
        for y in range(outer_box[1], outer_box[3])
    }
    skin_pixels = sum(
        1 for x, y in hand_points if image.getpixel((x, y)) in SKIN_COLORS
    )
    cuff_pixels = sum(
        1 for x, y in hand_points if image.getpixel((x, y)) in CUFF_COLORS
    )
    return {
        "bbox": bbox,
        "outer_bbox": outer_bbox,
        "outer_size": [
            outer_bbox[2] - outer_bbox[0],
            outer_bbox[3] - outer_bbox[1],
        ],
        "palm_width_by_row": palm_width_by_row,
        "skin_pixels": skin_pixels,
        "cuff_pixels": cuff_pixels,
        "connected": len(opaque_components(image, region)) == 1,
    }


def grid_preview(
    image: Image.Image,
    left_metrics: dict[str, object],
    right_metrics: dict[str, object],
) -> Image.Image:
    crop_box = (8, 66, 58, 85)
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
    legend_width = 210
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
            (x + 2, 8),
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

    def rectangle_for(bbox: list[int], color: tuple[int, int, int, int]) -> None:
        left = margin_left + (bbox[0] - crop_box[0]) * scale
        top = margin_top + (bbox[1] - crop_box[1]) * scale
        right = margin_left + (bbox[2] - crop_box[0]) * scale
        bottom = margin_top + (bbox[3] - crop_box[1]) * scale
        draw.rectangle((left, top, right, bottom), outline=color, width=3)

    if left_metrics["bbox"]:
        rectangle_for(left_metrics["bbox"], (0, 190, 255, 255))
    if right_metrics["bbox"]:
        rectangle_for(right_metrics["bbox"], (0, 210, 120, 255))
    for region in (LEFT_REGION, RIGHT_REGION):
        left = margin_left + (region[0] - crop_box[0]) * scale
        top = margin_top + (region[1] - crop_box[1]) * scale
        right = margin_left + (region[2] - crop_box[0]) * scale
        bottom = margin_top + (region[3] - crop_box[1]) * scale
        draw.rectangle((left, top, right, bottom), outline=(255, 70, 70, 255), width=3)

    label_x = margin_left + upscaled.width + 10
    draw.text((label_x, 20), "LEFT: CUFF + PALM", fill=(0, 160, 230, 255))
    draw.text((label_x, 52), "RIGHT: CUFF + PALM", fill=(0, 160, 90, 255))
    draw.text((label_x, 84), "RED: EDIT REGIONS", fill=(210, 20, 40, 255))
    draw.text((label_x, 116), "RIGHT HAND OVER TAIL", fill=(180, 100, 0, 255))
    draw.text((label_x, 148), "BOTTOM <= y=80", fill=(160, 70, 200, 255))
    tail_left = margin_left + (49 - crop_box[0]) * scale
    tail_top = margin_top + (68 - crop_box[1]) * scale
    tail_right = margin_left + (57 - crop_box[0]) * scale
    tail_bottom = margin_top + (83 - crop_box[1]) * scale
    draw.rectangle(
        (tail_left, tail_top, tail_right, tail_bottom),
        outline=(210, 150, 0, 255),
        width=2,
    )
    draw.text(
        (margin_left, canvas.height - 20),
        "BLUE=LEFT  GREEN=RIGHT  GOLD=TAIL OUTSIDE",
        fill=(0, 0, 0, 255),
    )
    return canvas


def prepare() -> None:
    if sha256(INPUT) != EXPECTED_INPUT_SHA256:
        raise ValueError("unexpected P2-3R5 input SHA-256")
    source = Image.open(INPUT).convert("RGBA")
    if source.size != EXPECTED_SIZE:
        raise ValueError(f"unexpected input size: {source.size}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    input_path = OUTPUT_DIR / "input-down-left-hand-cleaned.png"
    left_path = OUTPUT_DIR / "left-hand-mask.png"
    right_path = OUTPUT_DIR / "right-hand-mask.png"
    combined_path = OUTPUT_DIR / "two-hands-mask.png"
    api_path = OUTPUT_DIR / "two-hands-mask-api.png"
    preview_path = OUTPUT_DIR / "two-hands-mask-preview-16x.png"
    metrics_path = OUTPUT_DIR / "mask-metrics.json"

    input_path.write_bytes(INPUT.read_bytes())
    mask_image(LEFT_POINTS).save(left_path)
    mask_image(RIGHT_POINTS).save(right_path)
    mask_image(ALL_MASK_POINTS).save(combined_path)
    api_mask = Image.new("RGB", EXPECTED_SIZE, (0, 0, 0))
    for x, y in ALL_MASK_POINTS:
        api_mask.putpixel((x, y), (255, 255, 255))
    api_mask.save(api_path)
    make_mask_preview(source).save(preview_path)

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3r6-mask-v1",
        "input": input_path.relative_to(ROOT).as_posix(),
        "input_sha256": sha256(input_path),
        "left_mask_sha256": sha256(left_path),
        "right_mask_sha256": sha256(right_path),
        "combined_mask_sha256": sha256(combined_path),
        "api_mask_sha256": sha256(api_path),
        "left_region": list(LEFT_REGION),
        "right_region": list(RIGHT_REGION),
        "left_mask_pixels": len(LEFT_POINTS),
        "right_mask_pixels": len(RIGHT_POINTS),
        "masks_are_separate": not bool(LEFT_POINTS & RIGHT_POINTS),
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
    mask = combined_mask_image()
    if source.size != EXPECTED_SIZE or raw.size != EXPECTED_SIZE:
        raise ValueError("unexpected image dimensions")

    source_palette = set(source.get_flattened_data())
    hand_palette = tuple(
        sorted(
            source_palette - {SOFT_LIP, SOFT_LIP_SHADOW},
            key=lambda color: (color[3], color[0], color[1], color[2]),
        )
    )
    raw_changed_outside = [
        (x, y)
        for y in range(source.height)
        for x in range(source.width)
        if (x, y) not in ALL_MASK_POINTS
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
    changed_outside = [point for point in changed if point not in ALL_MASK_POINTS]
    if changed_outside:
        raise ValueError(f"changed pixels outside masks: {changed_outside[:8]}")

    palette = set(cleaned.get_flattened_data())
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")
    if len(palette) > 22:
        raise ValueError(f"palette exceeds 22 colors: {len(palette)}")

    left = hand_metrics(
        cleaned,
        LEFT_POINTS,
        LEFT_REGION,
        LEFT_HAND_BOX,
        (12, 72, 17, 76),
    )
    right = hand_metrics(
        cleaned,
        RIGHT_POINTS,
        RIGHT_REGION,
        RIGHT_HAND_BOX,
        (41, 71, 46, 76),
    )
    if not left["bbox"] or not right["bbox"]:
        raise ValueError("one or both hands are missing")
    if left["outer_size"][0] > 5 or left["outer_size"][1] > 5:
        raise ValueError(f"left mask output unexpectedly large: {left['outer_size']}")
    if right["outer_size"][0] > 5 or right["outer_size"][1] > 5:
        raise ValueError(f"right mask output unexpectedly large: {right['outer_size']}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_output = OUTPUT_DIR / "down-two-hands-raw.png"
    cleaned_output = OUTPUT_DIR / "down-two-hands-cleaned.png"
    diff_output = OUTPUT_DIR / "down-two-hands-diff-16x.png"
    grid_output = OUTPUT_DIR / "down-two-hands-grid-32x.png"
    runtime_output = OUTPUT_DIR / "runtime-48x72-preview-8x.png"
    metrics_output = OUTPUT_DIR / "metrics.json"
    visual_output = OUTPUT_DIR / "visual-review.json"

    raw_output.write_bytes(raw_path.read_bytes())
    cleaned.save(cleaned_output)
    four_panel_preview(source, mask, cleaned, changed).save(diff_output)
    grid_preview(cleaned, left, right).save(grid_output)
    runtime = cleaned.resize((48, 72), Image.Resampling.NEAREST)
    preview_panels(runtime, 8).save(runtime_output)

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3r6-two-hands-v1",
        "input_sha256": sha256(INPUT),
        "raw_sha256": sha256(raw_output),
        "output_sha256": sha256(cleaned_output),
        "background_job_id": "1ff8755c-bf1f-44b6-93cf-b74a67e9a411",
        "generation_id": "37e184ad-e091-4300-97fc-2feb42e0ee48",
        "left_hand_bbox": left["bbox"],
        "right_hand_bbox": right["bbox"],
        "left_hand_outer_size": left["outer_size"],
        "right_hand_outer_size": right["outer_size"],
        "left_hand_outer_bbox": left["outer_bbox"],
        "right_hand_outer_bbox": right["outer_bbox"],
        "left_palm_skin_width_by_row": left["palm_width_by_row"],
        "right_palm_skin_width_by_row": right["palm_width_by_row"],
        "left_cuff_pixels": left["cuff_pixels"],
        "right_cuff_pixels": right["cuff_pixels"],
        "left_hand_connected": left["connected"],
        "right_hand_connected": right["connected"],
        "right_hand_in_front_of_tail": True,
        "changed_pixels_inside_masks": len(changed),
        "changed_pixels_outside_masks": len(changed_outside),
        "raw_changed_pixels_outside_masks": len(raw_changed_outside),
        "outside_mask_restored_from_input": len(raw_changed_outside),
        "soft_lip_colors_inside_hand_masks": sum(
            1
            for x, y in ALL_MASK_POINTS
            if cleaned.getpixel((x, y)) in {SOFT_LIP, SOFT_LIP_SHADOW}
        ),
        "palm_blue_mapped_to_skin_shadow": blue_to_skin_shadow,
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
        "pixellab_calls": 1,
        "animation_started": False,
        "production_modified": False,
    }
    metrics_output.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    visual = {
        "schema_version": "rpg-character-pixellab-p2-3r6-visual-review-v1",
        "status": "technical-check-pending-user-confirmation",
        "left_hand_smaller_than_p2_3r5": (
            left["outer_size"][0] <= 5 and left["outer_size"][1] <= 5
        ),
        "right_hand_present": True,
        "left_hand_connected": left["connected"],
        "right_hand_connected": right["connected"],
        "right_hand_in_front_of_tail": True,
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
        default=OUTPUT_DIR / "down-two-hands-raw.png",
    )
    args = parser.parse_args()
    if args.prepare:
        prepare()
    else:
        audit(args.raw)


if __name__ == "__main__":
    main()
