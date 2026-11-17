from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
INPUT_SHEET = (
    ROOT / "art-source/character-v2/pixellab/P2-4/sprite-4dir-cleaned.png"
)
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P3-0R"
EXPECTED_INPUT_SHA256 = (
    "6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12"
)
FRAME_SIZE = (64, 96)
DIRECTIONS = ("down", "left", "right", "up")

SWAY_SOURCES = {
    "down": frozenset(
        {
            (47, 74),
            (48, 75),
            (47, 76),
            (46, 77),
        }
    ),
    "left": frozenset(
        {
            (48, 70),
            (48, 71),
            (48, 72),
            (47, 73),
            (47, 74),
            (48, 75),
            (48, 76),
        }
    ),
    "right": frozenset(
        {
            (48, 70),
            (48, 71),
            (48, 72),
            (48, 73),
            (49, 74),
            (49, 75),
            (49, 76),
        }
    ),
    "up": frozenset(
        {
            (44, 77),
            (44, 78),
            (44, 79),
            (43, 80),
            (43, 81),
            (43, 82),
        }
    ),
}
SECONDARY_REGIONS = {
    direction: points
    | frozenset((x - 1, y) for x, y in points)
    | frozenset((x + 1, y) for x, y in points)
    for direction, points in SWAY_SOURCES.items()
}

FACE_REGION = (10, 27, 55, 67)
TORSO_REGION = (14, 62, 42, 82)
HAND_REGIONS = (
    (12, 70, 17, 76),
    (42, 68, 46, 76),
)
LEG_BOOT_REGIONS = (
    (19, 73, 29, 90),
    (31, 73, 41, 90),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def shift_secondary(
    frame: Image.Image,
    direction: str,
    dx: int,
) -> Image.Image:
    shifted = frame.copy()
    source = SWAY_SOURCES[direction]
    region = SECONDARY_REGIONS[direction]
    colors = {point: frame.getpixel(point) for point in source}
    for point in source:
        shifted.putpixel(point, (0, 0, 0, 0))
    for (x, y), color in colors.items():
        target = (x + dx, y)
        if target not in region:
            raise ValueError(f"secondary movement left allowed mask: {target}")
        shifted.putpixel(target, color)
    return shifted


def changed_in_region(
    left: Image.Image,
    right: Image.Image,
    region: tuple[int, int, int, int],
) -> int:
    return sum(
        left.getpixel((x, y)) != right.getpixel((x, y))
        for y in range(region[1], region[3])
        for x in range(region[0], region[2])
    )


def changed_total(left: Image.Image, right: Image.Image) -> int:
    return sum(
        left.getpixel((x, y)) != right.getpixel((x, y))
        for y in range(left.height)
        for x in range(left.width)
    )


def checkerboard(size: tuple[int, int], cell: int = 16) -> Image.Image:
    image = Image.new("RGBA", size, (222, 226, 230, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle(
                    (x, y, x + cell - 1, y + cell - 1),
                    fill=(176, 184, 192, 255),
                )
    return image


def build_preview(frames: list[Image.Image], scale: int = 8) -> Image.Image:
    cell_w = FRAME_SIZE[0] * scale
    cell_h = FRAME_SIZE[1] * scale
    gutter = 12
    label_h = 32
    canvas = Image.new(
        "RGBA",
        (
            len(frames) * cell_w + (len(frames) + 1) * gutter,
            label_h + cell_h + 2 * gutter,
        ),
        (20, 23, 30, 255),
    )
    draw = ImageDraw.Draw(canvas)
    for index, frame in enumerate(frames):
        x = gutter + index * (cell_w + gutter)
        y = label_h + gutter
        draw.text((x + 4, 8), f"FRAME {index}", fill=(255, 255, 255, 255))
        panel = checkerboard((cell_w, cell_h))
        panel.alpha_composite(
            frame.resize((cell_w, cell_h), Image.Resampling.NEAREST)
        )
        canvas.alpha_composite(panel, (x, y))
        draw.rectangle(
            (x, y, x + cell_w - 1, y + cell_h - 1),
            outline=(86, 93, 104, 255),
        )
    return canvas


def save_animated_webp(frames: list[Image.Image], path: Path) -> None:
    scaled = [
        frame.resize(
            (frame.width * 8, frame.height * 8),
            Image.Resampling.NEAREST,
        )
        for frame in frames
    ]
    scaled[0].save(
        path,
        format="WEBP",
        save_all=True,
        append_images=scaled[1:],
        duration=200,
        loop=0,
        lossless=True,
        method=6,
        background=(0, 0, 0, 0),
    )


def main() -> None:
    if sha256(INPUT_SHEET) != EXPECTED_INPUT_SHA256:
        raise ValueError("P2-4 source sheet SHA-256 mismatch")
    sheet = Image.open(INPUT_SHEET).convert("RGBA")
    if sheet.size != (256, 96):
        raise ValueError(f"unexpected source sheet size: {sheet.size}")

    base_frames = {
        direction: sheet.crop((index * 64, 0, (index + 1) * 64, 96))
        for index, direction in enumerate(DIRECTIONS)
    }
    all_frames: dict[str, list[Image.Image]] = {}
    for direction in DIRECTIONS:
        base = base_frames[direction]
        all_frames[direction] = [
            base.copy(),
            shift_secondary(base, direction, -1),
            base.copy(),
            shift_secondary(base, direction, 1),
        ]

    down_frames = all_frames["down"]
    proof = Image.new("RGBA", (256, 96), (0, 0, 0, 0))
    for index, frame in enumerate(down_frames):
        proof.alpha_composite(frame, (index * 64, 0))

    idle_sheet = Image.new("RGBA", (256, 384), (0, 0, 0, 0))
    for row, direction in enumerate(DIRECTIONS):
        for column, frame in enumerate(all_frames[direction]):
            idle_sheet.alpha_composite(frame, (column * 64, row * 96))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    proof_path = OUTPUT_DIR / "down-proof-4f.png"
    proof_preview_path = OUTPUT_DIR / "down-proof-preview-8x.webp"
    idle_sheet_path = OUTPUT_DIR / "idle-4dir-4f.png"
    metrics_path = OUTPUT_DIR / "metrics-idle.json"
    down_metrics_path = OUTPUT_DIR / "down-proof-metrics.json"
    visual_path = OUTPUT_DIR / "visual-review.json"

    proof.save(proof_path)
    save_animated_webp(down_frames, proof_preview_path)
    idle_sheet.save(idle_sheet_path)

    for direction in DIRECTIONS:
        frame_dir = OUTPUT_DIR / "frames" / direction
        frame_dir.mkdir(parents=True, exist_ok=True)
        for index, frame in enumerate(all_frames[direction]):
            frame.save(frame_dir / f"{index}.png")

    palette = set(idle_sheet.get_flattened_data())
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")
    if len(palette) > 22:
        raise ValueError(f"palette exceeds 22 colors: {len(palette)}")

    frame_bboxes: dict[str, list[list[int]]] = {}
    sole_bottom_rows: dict[str, list[int]] = {}
    frame_anchor_x: dict[str, list[float]] = {}
    changed_between: dict[str, list[int]] = {}
    loop_changed: dict[str, int] = {}
    secondary_changed: dict[str, int] = {}
    face_changed: dict[str, int] = {}
    torso_changed: dict[str, int] = {}
    hand_changed: dict[str, int] = {}
    leg_changed: dict[str, int] = {}

    for direction in DIRECTIONS:
        frames = all_frames[direction]
        base = base_frames[direction]
        bboxes = [list(frame.getbbox()) for frame in frames]
        if len({tuple(bbox) for bbox in bboxes}) != 1:
            raise ValueError(f"{direction} changed overall bounds: {bboxes}")
        if frames[0].tobytes() != frames[2].tobytes():
            raise ValueError(f"{direction} frame 2 differs from frame 0")
        if bboxes[0][3] - 1 != 87:
            raise ValueError(f"{direction} sole moved: {bboxes[0]}")

        changed = {
            (x, y)
            for y in range(96)
            for x in range(64)
            if frames[1].getpixel((x, y)) != base.getpixel((x, y))
            or frames[3].getpixel((x, y)) != base.getpixel((x, y))
        }
        changed_outside = sorted(changed - SECONDARY_REGIONS[direction])
        if changed_outside:
            raise ValueError(
                f"{direction} secondary movement escaped mask: {changed_outside[:8]}"
            )
        secondary_changed[direction] = len(changed)
        face_changed[direction] = (
            changed_in_region(base, frames[1], FACE_REGION)
            + changed_in_region(base, frames[3], FACE_REGION)
        )
        torso_changed[direction] = (
            changed_in_region(base, frames[1], TORSO_REGION)
            + changed_in_region(base, frames[3], TORSO_REGION)
        )
        hand_changed[direction] = sum(
            changed_in_region(base, frames[1], region)
            + changed_in_region(base, frames[3], region)
            for region in HAND_REGIONS
        )
        leg_changed[direction] = sum(
            changed_in_region(base, frames[1], region)
            + changed_in_region(base, frames[3], region)
            for region in LEG_BOOT_REGIONS
        )
        frame_bboxes[direction] = bboxes
        sole_bottom_rows[direction] = [bbox[3] - 1 for bbox in bboxes]
        frame_anchor_x[direction] = []
        for frame in frames:
            bottom = frame.getbbox()[3] - 1
            xs = [
                x
                for x in range(64)
                if frame.getpixel((x, bottom))[3] != 0
            ]
            frame_anchor_x[direction].append((min(xs) + max(xs)) / 2)
        changed_between[direction] = [
            changed_total(frames[index], frames[index + 1])
            for index in range(3)
        ]
        loop_changed[direction] = changed_total(frames[3], frames[0])

    max_anchor_drift = max(
        max(anchors) - min(anchors)
        for anchors in frame_anchor_x.values()
    )
    max_sole_drift = max(
        max(rows) - min(rows)
        for rows in sole_bottom_rows.values()
    )

    metrics = {
        "schema_version": "rpg-character-pixellab-p3-0r-idle-v1",
        "status": "technical-pass-pending-user-confirmation",
        "source_sheet_sha256": sha256(INPUT_SHEET),
        "output_sheet_sha256": sha256(idle_sheet_path),
        "sheet_size": [256, 384],
        "frame_size": list(FRAME_SIZE),
        "direction_order": list(DIRECTIONS),
        "frame_count": 4,
        "fps": 5,
        "loop_order": [0, 1, 2, 3, 0],
        "frame0_pixel_identical_to_p2_4": True,
        "frame2_pixel_identical_to_frame0": True,
        "secondary_motion_rules": {
            direction: {
                "source_pixels": sorted(SWAY_SOURCES[direction]),
                "frame1_dx": -1,
                "frame3_dx": 1,
            }
            for direction in DIRECTIONS
        },
        "secondary_region_changed_pixels": secondary_changed,
        "face_region_changed_pixels": face_changed,
        "torso_region_changed_pixels": torso_changed,
        "hand_region_changed_pixels": hand_changed,
        "leg_region_changed_pixels": leg_changed,
        "changed_pixels_between_adjacent_frames": changed_between,
        "loop_frame3_to_frame0_changed_pixels": loop_changed,
        "frame_bboxes": frame_bboxes,
        "sole_bottom_rows": sole_bottom_rows,
        "frame_anchor_x": frame_anchor_x,
        "max_anchor_x_drift": max_anchor_drift,
        "max_sole_bottom_drift": max_sole_drift,
        "colors": len(palette),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": 0,
        "generation_submissions": 0,
        "pixellab_calls": 0,
        "animation_started": False,
        "production_modified": False,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    down_metrics = {
        "schema_version": "rpg-character-pixellab-p3-0r-idle-down-proof-v1",
        "source_sheet_sha256": metrics["source_sheet_sha256"],
        "output_sheet_sha256": sha256(proof_path),
        "sheet_size": [256, 96],
        "frame_size": list(FRAME_SIZE),
        "direction_order": ["down"],
        "frame_count": 4,
        "fps": 5,
        "loop_order": [0, 1, 2, 3, 0],
        "frame0_pixel_identical_to_p2_4": True,
        "frame2_pixel_identical_to_frame0": True,
        "secondary_region_changed_pixels": secondary_changed["down"],
        "face_region_changed_pixels": face_changed["down"],
        "torso_region_changed_pixels": torso_changed["down"],
        "hand_region_changed_pixels": hand_changed["down"],
        "leg_region_changed_pixels": leg_changed["down"],
        "changed_pixels_between_adjacent_frames": changed_between["down"],
        "loop_frame3_to_frame0_changed_pixels": loop_changed["down"],
        "frame_bboxes": frame_bboxes["down"],
        "sole_bottom_rows": sole_bottom_rows["down"],
        "colors": len(set(proof.get_flattened_data())),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": 0,
        "generation_submissions": 0,
        "pixellab_calls": 0,
        "animation_started": False,
        "production_modified": False,
    }
    down_metrics_path.write_text(
        json.dumps(down_metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    visual = {
        "schema_version": "rpg-character-pixellab-p3-0r-idle-visual-v1",
        "status": "technical-pass-pending-user-confirmation",
        "checks": {
            "down_proof": True,
            "frame0_exact": True,
            "frame2_exact": True,
            "face_unchanged": all(value == 0 for value in face_changed.values()),
            "torso_unchanged": all(value == 0 for value in torso_changed.values()),
            "hands_unchanged": all(value == 0 for value in hand_changed.values()),
            "legs_boots_unchanged": all(value == 0 for value in leg_changed.values()),
            "secondary_motion_one_pixel": True,
            "overall_bbox_unchanged": True,
            "sole_y88": True,
            "four_directions_complete": True,
        },
        "user_confirmation": "pending",
    }
    visual_path.write_text(
        json.dumps(visual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
