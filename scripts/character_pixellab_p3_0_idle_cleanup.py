from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "art-source/character-v2/pixellab/P3-0"
SOURCE_SHEET = INPUT_DIR / "input-sprite-4dir.png"
EXPECTED_SOURCE_SHA256 = (
    "6B11705F7C3C599697B4D5CFAC6B3C8137CCE7FA5A8E6CB6136BF4C5800CAD12"
)
RAW_FRAMES = tuple(INPUT_DIR / f"down-raw-{index}.png" for index in range(5))
COMMON_CROP = (24, 8, 88, 104)
FRAME_SIZE = (64, 96)
SHEET_SIZE = (256, 96)
FOOT_BASELINE_EXCLUSIVE = 88
FACE_REGION = (10, 27, 55, 67)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def shift_frame(frame: Image.Image, y_offset: int) -> Image.Image:
    shifted = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    shifted.alpha_composite(frame, (0, y_offset))
    return shifted


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


def proof_preview(frames: list[Image.Image], scale: int = 8) -> Image.Image:
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


def changed_count(left: Image.Image, right: Image.Image) -> int:
    return sum(
        left.getpixel((x, y)) != right.getpixel((x, y))
        for y in range(left.height)
        for x in range(left.width)
    )


def main() -> None:
    if sha256(SOURCE_SHEET) != EXPECTED_SOURCE_SHA256:
        raise ValueError("P2-4 source sheet SHA-256 mismatch")
    source_sheet = Image.open(SOURCE_SHEET).convert("RGBA")
    if source_sheet.size != (256, 96):
        raise ValueError(f"unexpected source sheet size: {source_sheet.size}")
    approved_down = source_sheet.crop((0, 0, 64, 96))
    palette = tuple(
        sorted(
            set(approved_down.get_flattened_data()),
            key=lambda color: (color[3], color[0], color[1], color[2]),
        )
    )

    raw_images = [Image.open(path).convert("RGBA") for path in RAW_FRAMES]
    if any(image.size != (112, 112) for image in raw_images):
        raise ValueError("unexpected raw animation frame size")

    frames: list[Image.Image] = [approved_down.copy()]
    vertical_shifts: list[int] = [0]
    for raw in raw_images[1:4]:
        crop = raw.crop(COMMON_CROP)
        bbox = crop.getbbox()
        if bbox is None:
            raise ValueError("empty animation frame")
        vertical_shift = FOOT_BASELINE_EXCLUSIVE - bbox[3]
        vertical_shifts.append(vertical_shift)
        aligned = shift_frame(crop, vertical_shift)
        mapped = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
        for y in range(FRAME_SIZE[1]):
            for x in range(FRAME_SIZE[0]):
                mapped.putpixel(
                    (x, y),
                    nearest_color(aligned.getpixel((x, y)), palette),
                )
        frames.append(mapped)

    proof_sheet = Image.new("RGBA", SHEET_SIZE, (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        proof_sheet.alpha_composite(frame, (index * 64, 0))

    alpha_values = sorted(
        {color[3] for color in set(proof_sheet.get_flattened_data())}
    )
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")
    if proof_sheet.crop((0, 0, 64, 96)).tobytes() != approved_down.tobytes():
        raise ValueError("frame 0 no longer matches P2-4 static down")

    proof_path = INPUT_DIR / "idle-down-proof-4f.png"
    preview_path = INPUT_DIR / "idle-down-proof-4f-preview-8x.png"
    metrics_path = INPUT_DIR / "metrics-idle.json"
    visual_path = INPUT_DIR / "visual-review.json"
    proof_sheet.save(proof_path)
    proof_preview(frames).save(preview_path)

    adjacent_changes = [
        changed_count(frames[index], frames[index + 1])
        for index in range(3)
    ]
    loop_changes = changed_count(frames[3], frames[0])
    face_changes = []
    for frame in frames[1:]:
        face_changes.append(
            sum(
                frame.getpixel((x, y)) != approved_down.getpixel((x, y))
                for y in range(FACE_REGION[1], FACE_REGION[3])
                for x in range(FACE_REGION[0], FACE_REGION[2])
            )
        )

    bboxes = [list(frame.getbbox()) for frame in frames]
    sole_bottoms = [bbox[3] - 1 for bbox in bboxes]
    metrics = {
        "schema_version": "rpg-character-pixellab-p3-0-down-proof-v1",
        "status": "fail-face-expression-drift",
        "source_sheet_sha256": sha256(SOURCE_SHEET),
        "output_sheet_sha256": sha256(proof_path),
        "sheet_size": list(SHEET_SIZE),
        "frame_size": list(FRAME_SIZE),
        "direction_order": ["down"],
        "frame_count": 4,
        "fps": 5,
        "loop_order": [0, 1, 2, 3, 0],
        "row_frame0_pixel_identical_to_p2_4": True,
        "common_crop_window": list(COMMON_CROP),
        "frame_vertical_shifts": vertical_shifts,
        "frame_bboxes": bboxes,
        "sole_bottom_rows": sole_bottoms,
        "face_changed_pixels_vs_frame0": face_changes,
        "changed_pixels_between_adjacent_frames": adjacent_changes,
        "loop_frame3_to_frame0_changed_pixels": loop_changes,
        "colors": len(set(proof_sheet.get_flattened_data())),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": 0,
        "generation_submissions_by_direction": {"down": 1},
        "generations_used": 1,
        "animation_started": True,
        "production_modified": False,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    visual = {
        "schema_version": "rpg-character-pixellab-p3-0-visual-review-v1",
        "status": "blocked-down-proof",
        "checks": {
            "frame0_exact_p2_4": True,
            "four_frames_present": True,
            "foot_baseline_y88": sole_bottoms == [87, 87, 87, 87],
            "face_stable": False,
            "mouth_stable": False,
            "hair_tail_motion_at_most_1px": False,
            "hands_small": True,
            "other_directions_generated": False,
        },
        "blockers": [
            "frames 2 and 3 visibly change the mouth from a soft smile to an open expression",
            "face and silhouette change beyond the allowed 1-pixel idle breathing",
        ],
        "review_evidence": preview_path.relative_to(ROOT).as_posix(),
        "animation_authorized": False,
        "four_direction_animation_completed": False,
    }
    visual_path.write_text(
        json.dumps(visual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
