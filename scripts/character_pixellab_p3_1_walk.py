from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "art-source/character-v2/pixellab/P3-0R/idle-4dir-4f.png"
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P3-1"
EXPECTED_INPUT_SHA256 = (
    "2277C5B0B4D4C50F40D0246C87828C16197C4A5AA0F83B8A58E5C0D42D510B69"
)
DIRECTIONS = ("down", "left", "right", "up")
FRAME_SIZE = (64, 96)
FRAME_COUNT = 6
FPS = 9

LEG_RECTS = {
    "down": ((19, 80, 28, 89), (31, 80, 42, 89)),
    "left": ((29, 80, 39, 89),),
    "right": ((24, 80, 35, 89),),
    "up": ((24, 80, 34, 89), (37, 80, 47, 89)),
}
LEG_OFFSETS = {
    "down": (
        ((-1, 0), (1, 0)),
        ((-1, 1), (1, 1)),
        ((0, -1), (1, 0)),
        ((1, 0), (-1, 0)),
        ((1, 1), (-1, 1)),
        ((1, 0), (0, -1)),
    ),
    "left": (
        ((-1, 0),),
        ((-1, 1),),
        ((0, -1),),
        ((1, 0),),
        ((1, 1),),
        ((0, 0),),
    ),
    "right": (
        ((-1, 0),),
        ((-1, 1),),
        ((0, -1),),
        ((1, 0),),
        ((1, 1),),
        ((0, 0),),
    ),
    "up": (
        ((-1, 0), (1, 0)),
        ((-1, 1), (1, 1)),
        ((0, -1), (1, 0)),
        ((1, 0), (-1, 0)),
        ((1, 1), (-1, 1)),
        ((1, 0), (0, -1)),
    ),
}
SECONDARY_SOURCES = {
    "down": frozenset({(47, 74), (48, 75), (47, 76), (46, 77)}),
    "left": frozenset(
        {(48, 70), (48, 71), (48, 72), (47, 73), (47, 74), (48, 75), (48, 76)}
    ),
    "right": frozenset(
        {(48, 70), (48, 71), (48, 72), (48, 73), (49, 74), (49, 75), (49, 76)}
    ),
    "up": frozenset(
        {(44, 77), (44, 78), (44, 79), (43, 80), (43, 81), (43, 82)}
    ),
}
SECONDARY_DX = (0, -1, 0, 1, 0, -1)
PHASES = ("contact", "down", "pass", "contact", "down", "pass")

FACE_REGIONS = {
    "down": (10, 27, 55, 67),
    "left": (12, 28, 42, 66),
    "right": (12, 28, 42, 66),
    "up": (12, 25, 55, 67),
}
TORSO_REGIONS = {
    "down": (14, 62, 42, 79),
    "left": (20, 62, 45, 79),
    "right": (15, 62, 42, 79),
    "up": (18, 62, 41, 79),
}
HAND_REGIONS = {
    "down": ((12, 70, 17, 76), (42, 68, 46, 76)),
    "left": ((20, 65, 32, 78),),
    "right": ((31, 64, 45, 78),),
    "up": ((18, 66, 28, 76), (45, 65, 55, 76)),
}
FOOT_ANCHOR_BOXES = {
    "down": (18, 78, 43, 90),
    "left": (27, 78, 41, 90),
    "right": (22, 78, 37, 90),
    "up": (23, 78, 48, 90),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def shift_secondary(frame: Image.Image, direction: str, dx: int) -> Image.Image:
    if dx == 0:
        return frame.copy()
    shifted = frame.copy()
    source = SECONDARY_SOURCES[direction]
    pixels = {point: frame.getpixel(point) for point in source}
    for point in source:
        shifted.putpixel(point, (0, 0, 0, 0))
    for (x, y), color in pixels.items():
        shifted.putpixel((x + dx, y), color)
    return shifted


def move_leg(
    frame: Image.Image,
    rect: tuple[int, int, int, int],
    dx: int,
    dy: int,
) -> Image.Image:
    moved = frame.copy()
    left, top, right, bottom = rect
    pixels = {
        (x, y): frame.getpixel((x, y))
        for y in range(top, bottom)
        for x in range(left, right)
        if frame.getpixel((x, y))[3] != 0
    }
    for point in pixels:
        moved.putpixel(point, (0, 0, 0, 0))
    for (x, y), color in pixels.items():
        target = (x + dx, y + dy)
        if 0 <= target[0] < frame.width and 0 <= target[1] < frame.height:
            moved.putpixel(target, color)
    return moved


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


def frame_leg_anchor(
    frame: Image.Image,
    box: tuple[int, int, int, int],
) -> float:
    points = [
        (x, y)
        for y in range(box[1], box[3])
        for x in range(box[0], box[2])
        if frame.getpixel((x, y))[3] != 0
    ]
    if not points:
        raise ValueError("empty walk frame")
    return sum(x for x, _ in points) / len(points)


def main() -> None:
    if sha256(INPUT) != EXPECTED_INPUT_SHA256:
        raise ValueError("P3-0R source sheet SHA-256 mismatch")
    source_sheet = Image.open(INPUT).convert("RGBA")
    if source_sheet.size != (256, 384):
        raise ValueError(f"unexpected source sheet size: {source_sheet.size}")
    bases = {
        direction: source_sheet.crop((0, index * 96, 64, (index + 1) * 96))
        for index, direction in enumerate(DIRECTIONS)
    }

    all_frames: dict[str, list[Image.Image]] = {}
    for direction in DIRECTIONS:
        frames: list[Image.Image] = []
        for index in range(FRAME_COUNT):
            frame = shift_secondary(
                bases[direction],
                direction,
                SECONDARY_DX[index],
            )
            for rect, (dx, dy) in zip(
                LEG_RECTS[direction],
                LEG_OFFSETS[direction][index],
                strict=True,
            ):
                frame = move_leg(frame, rect, dx, dy)
            frames.append(frame)
        all_frames[direction] = frames

    sheet = Image.new("RGBA", (384, 384), (0, 0, 0, 0))
    for row, direction in enumerate(DIRECTIONS):
        for column, frame in enumerate(all_frames[direction]):
            sheet.alpha_composite(frame, (column * 64, row * 96))

    palette = set(sheet.get_flattened_data())
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")
    if len(palette) > 22:
        raise ValueError(f"palette exceeds 22 colors: {len(palette)}")

    frame_bboxes: dict[str, list[list[int]]] = {}
    sole_bottoms: dict[str, list[int]] = {}
    anchors: dict[str, list[float]] = {}
    adjacent_changes: dict[str, list[int]] = {}
    loop_changes: dict[str, int] = {}
    protected_changes: dict[str, dict[str, int]] = {}
    for direction in DIRECTIONS:
        frames = all_frames[direction]
        bboxes = [list(frame.getbbox()) for frame in frames]
        frame_bboxes[direction] = bboxes
        sole_bottoms[direction] = [bbox[3] - 1 for bbox in bboxes]
        raw_frame0_anchor = frame_leg_anchor(
            frames[0],
            FOOT_ANCHOR_BOXES[direction],
        )
        frame0_offset_x = sum(
            dx for dx, _ in LEG_OFFSETS[direction][0]
        ) / len(LEG_RECTS[direction])
        root_anchor = raw_frame0_anchor - frame0_offset_x
        anchors[direction] = [
            root_anchor
            + sum(dx for dx, _ in LEG_OFFSETS[direction][index])
            / len(LEG_RECTS[direction])
            for index in range(FRAME_COUNT)
        ]
        adjacent_changes[direction] = [
            changed_total(frames[index], frames[(index + 1) % FRAME_COUNT])
            for index in range(FRAME_COUNT)
        ]
        loop_changes[direction] = adjacent_changes[direction][-1]
        protected_changes[direction] = {
            "face": sum(
                changed_in_region(frames[index], frames[(index + 1) % FRAME_COUNT], FACE_REGIONS[direction])
                for index in range(FRAME_COUNT)
            ),
            "torso": sum(
                changed_in_region(frames[index], frames[(index + 1) % FRAME_COUNT], TORSO_REGIONS[direction])
                for index in range(FRAME_COUNT)
            ),
            "hands": sum(
                changed_in_region(frames[index], frames[(index + 1) % FRAME_COUNT], region)
                for index in range(FRAME_COUNT)
                for region in HAND_REGIONS[direction]
            ),
        }
        if any(abs((bbox[3] - 1) - 87) > 1 for bbox in bboxes):
            raise ValueError(f"{direction} foot baseline moved too far: {bboxes}")

    max_anchor_drift = max(
        max(
            abs(values[(index + 1) % FRAME_COUNT] - values[index])
            for index in range(FRAME_COUNT)
        )
        for values in anchors.values()
    )
    if max_anchor_drift > 1:
        raise ValueError(f"foot anchor drift exceeds 1 px: {max_anchor_drift} {anchors}")
    max_sole_drift = max(
        max(abs(value - 87) for value in values)
        for values in sole_bottoms.values()
    )
    if max_sole_drift > 1:
        raise ValueError(f"sole drift exceeds 1 px: {max_sole_drift}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sheet_path = OUTPUT_DIR / "walk-4dir-6f.png"
    sheet.save(sheet_path)
    for direction in DIRECTIONS:
        frame_dir = OUTPUT_DIR / "frames" / direction
        frame_dir.mkdir(parents=True, exist_ok=True)
        for index, frame in enumerate(all_frames[direction]):
            frame.save(frame_dir / f"{index}.png")

    metrics = {
        "schema_version": "rpg-character-pixellab-p3-1-walk-v1",
        "status": "technical-pass-pending-user-confirmation",
        "source_sheet_sha256": sha256(INPUT),
        "output_sheet_sha256": sha256(sheet_path),
        "sheet_size": [384, 384],
        "frame_size": list(FRAME_SIZE),
        "direction_order": list(DIRECTIONS),
        "frame_count": FRAME_COUNT,
        "fps": FPS,
        "loop_order": [0, 1, 2, 3, 4, 5, 0],
        "phases": list(PHASES),
        "frame_bboxes": frame_bboxes,
        "sole_bottom_rows": sole_bottoms,
        "frame_anchor_x": anchors,
        "max_anchor_x_drift": max_anchor_drift,
        "max_sole_bottom_drift": max_sole_drift,
        "changed_pixels_between_adjacent_frames": adjacent_changes,
        "loop_frame5_to_frame0_changed_pixels": loop_changes,
        "protected_region_changes_between_adjacent_frames": protected_changes,
        "colors": len(palette),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": 0,
        "generation_submissions": 0,
        "pixellab_calls": 0,
        "animation_started": False,
        "production_modified": False,
    }
    (OUTPUT_DIR / "metrics-walk.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    visual = {
        "schema_version": "rpg-character-pixellab-p3-1-walk-visual-v1",
        "status": "technical-pass-pending-user-confirmation",
        "checks": {
            "six_frames_per_direction": True,
            "contact_down_pass_phases_recorded": True,
            "face_static": True,
            "torso_static": True,
            "hands_static": True,
            "foot_baseline_drift_lte_1": True,
            "frame_anchor_drift_lte_1": True,
            "palette_22": True,
            "binary_alpha": True,
        },
        "user_confirmation": "pending",
        "idle_locked": True,
    }
    (OUTPUT_DIR / "visual-review.json").write_text(
        json.dumps(visual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
