from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-3"
INPUT_SHA256 = (
    "77FB41D39AC16C839246EAAA12FDEC43"
    "8F270CCE76973FA7E1B20B70E333940B"
)
SOURCE_DIRECTIONS = ("south", "west", "east", "north")
OUTPUT_DIRECTIONS = ("down", "left", "right", "up")
FRAME_SIZE = (96, 96)
SHEET_SIZE = (384, 96)
SOFT_LIP = (201, 120, 130, 255)
SOFT_LIP_SHADOW = (160, 93, 99, 255)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_frames(export_dir: Path) -> dict[str, Image.Image]:
    frames: dict[str, Image.Image] = {}
    for direction in SOURCE_DIRECTIONS:
        path = export_dir / "Idle" / "rotations" / f"{direction}.png"
        image = Image.open(path).convert("RGBA")
        if image.size != FRAME_SIZE:
            raise ValueError(f"unexpected {direction} size: {image.size}")
        palette = {
            image.getpixel((x, y))
            for y in range(image.height)
            for x in range(image.width)
        }
        if sorted({color[3] for color in palette}) != [0, 255]:
            raise ValueError(f"{direction} contains translucent pixels")
        frames[direction] = image
    return frames


def build_lower_body_preview(frames: dict[str, Image.Image]) -> Image.Image:
    crop_top = 54
    scale = 8
    gutter = 12
    label_h = 34
    cell_w = FRAME_SIZE[0] * scale
    cell_h = (FRAME_SIZE[1] - crop_top) * scale
    width = len(OUTPUT_DIRECTIONS) * cell_w + (len(OUTPUT_DIRECTIONS) + 1) * gutter
    height = label_h + cell_h + 2 * gutter
    canvas = Image.new("RGBA", (width, height), (23, 27, 34, 255))
    draw = ImageDraw.Draw(canvas)

    for index, output_direction in enumerate(OUTPUT_DIRECTIONS):
        source_direction = SOURCE_DIRECTIONS[index]
        image = frames[source_direction]
        x = gutter + index * (cell_w + gutter)
        y = label_h + gutter
        draw.text((x + 4, 8), output_direction.upper(), fill=(255, 255, 255, 255))
        cell = Image.new("RGBA", (cell_w, cell_h), (246, 243, 234, 255))
        crop = image.crop((0, crop_top, FRAME_SIZE[0], FRAME_SIZE[1]))
        crop = crop.resize((cell_w, cell_h), Image.Resampling.NEAREST)
        cell.alpha_composite(crop)
        line_y = (88 - crop_top) * scale
        draw_cell = ImageDraw.Draw(cell)
        draw_cell.line(
            (0, line_y, cell_w, line_y),
            fill=(220, 65, 65, 255),
            width=1,
        )
        canvas.alpha_composite(cell, (x, y))
        draw.rectangle((x, y, x + cell_w, y + cell_h), outline=(86, 93, 104, 255))
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit the single PixelLab P2-3 leg-generation result."
    )
    parser.add_argument("--raw-export-dir", type=Path, required=True)
    parser.add_argument("--export-metadata", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    input_hash = sha256(args.input)
    if input_hash != INPUT_SHA256:
        raise ValueError(f"unexpected P2-3 input SHA-256: {input_hash}")

    export_metadata = json.loads(args.export_metadata.read_text(encoding="utf-8"))
    character = export_metadata.get("states", [{}])[0].get("character", {})
    if character.get("directions") != 4:
        raise ValueError("expected exactly four generated directions")

    frames = load_frames(args.raw_export_dir)
    raw_sheet = Image.new("RGBA", SHEET_SIZE, (0, 0, 0, 0))
    for index, direction in enumerate(SOURCE_DIRECTIONS):
        raw_sheet.alpha_composite(
            frames[direction],
            (index * FRAME_SIZE[0], 0),
        )

    pixels = [
        raw_sheet.getpixel((x, y))
        for y in range(raw_sheet.height)
        for x in range(raw_sheet.width)
    ]
    palette = set(pixels)
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")

    direction_bboxes = {
        direction: list(frames[direction].getbbox())
        for direction in SOURCE_DIRECTIONS
    }
    bottom_rows = {
        direction: direction_bboxes[direction][3] - 1
        for direction in SOURCE_DIRECTIONS
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / "sprite-4dir-raw.png"
    raw_metadata_path = args.output_dir / "sprite-4dir-raw.json"
    lower_body_path = args.output_dir / "lower-body-preview-8x.png"
    metrics_path = args.output_dir / "metrics.json"
    visual_review_path = args.output_dir / "visual-review.json"
    credit_log_path = args.output_dir / "credit-log.json"

    raw_sheet.save(raw_path)
    build_lower_body_preview(frames).save(lower_body_path)

    normalized_metadata = {
        "character": character,
        "spritesheet": {
            "cell_size": {"width": FRAME_SIZE[0], "height": FRAME_SIZE[1]},
            "sheet_size": {"width": SHEET_SIZE[0], "height": SHEET_SIZE[1]},
            "columns": 4,
            "rows": [
                {
                    "row": 0,
                    "type": "rotations",
                    "frame_count": 4,
                    "directions": list(SOURCE_DIRECTIONS),
                }
            ],
        },
        "source_export": "PixelLab Standard four-direction ZIP export",
        "export_version": export_metadata.get("export_version"),
        "export_date": export_metadata.get("export_date"),
    }
    raw_metadata_path.write_text(
        json.dumps(normalized_metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3-audit-v1",
        "status": "blocked",
        "blockers": [
            "no readable short legs in any direction",
            "no distinct dark navy ankle boots",
            "down and up do not show two separated legs",
        ],
        "source_sha256": input_hash,
        "output_sha256": sha256(raw_path),
        "raw_sheet_sha256": sha256(raw_path),
        "sheet_size": list(SHEET_SIZE),
        "frame_size": list(FRAME_SIZE),
        "direction_order": list(SOURCE_DIRECTIONS),
        "common_crop_window": None,
        "direction_bboxes": direction_bboxes,
        "raw_bottom_contact_y": bottom_rows,
        "foot_baseline_y": None,
        "foot_anchor_x": None,
        "leg_visible_height_by_direction": {
            "down": 0,
            "left": 0,
            "right": 0,
            "up": 0,
        },
        "boot_color": None,
        "colors": len(palette),
        "opaque_colors": sum(1 for color in palette if color[3] != 0),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": 0,
        "lip_colors": ["#C97882", "#A05D63"],
        "lip_colors_present": {
            "#C97882": SOFT_LIP in palette,
            "#A05D63": SOFT_LIP_SHADOW in palette,
        },
        "generation_submissions": 1,
        "generations_used": 8,
        "pixellab_calls": 1,
        "animation_started": False,
        "production_modified": False,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    visual_review = {
        "accepted": False,
        "checks": {
            "identity_matches_reference": "pass",
            "down_direction": "fail-no-separated-legs",
            "left_direction": "fail-no-readable-near-leg",
            "right_direction": "fail-no-readable-near-leg",
            "up_back_readable": "pass",
            "north_tail_occlusion_expected": "pass",
            "legs_and_boots_visible": "fail",
            "two_legs_separated_front_back": "fail",
            "left_right_real_side_legs": "fail",
            "foot_baseline_aligned": "fail-not-cleaned",
            "soft_lip_colors": "pass",
            "alpha_clean": "pass",
            "palette_within_limit": "fail-not-cleaned",
            "no_edge_clipping": "fail-not-cleaned",
            "map_readable_48x72": "not-run-generation-failed",
            "console_errors_zero": "not-run-generation-failed",
        },
        "reviewer_notes": (
            "The single authorized generation preserved identity and soft lip "
            "colors but still drew the character as a long-skirt silhouette. "
            "No valid technical cleanup or map pass was produced."
        ),
    }
    visual_review_path.write_text(
        json.dumps(visual_review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    credit_log = {
        "schema_version": "rpg-character-pixellab-p2-3-credit-log-v1",
        "date": "2026-11-15",
        "branch": "codex/character-art-pixellab-p2-3",
        "starting_commit": "89c491d",
        "input_sha256": input_hash,
        "membership_tier": "Tier 1 Pixel Apprentice",
        "usage_before_generation": "1 / 2000",
        "generation_submissions": 1,
        "generations_used": 8,
        "expected_usage_after_generation": "9 / 2000",
        "generation_mode": "Standard",
        "directions": 4,
        "camera_view": "high top-down",
        "displayed_cost": "8 generations",
        "purchases": 0,
        "upgrades": 0,
        "pro_used": False,
        "status": "failed-visual-acceptance",
    }
    credit_log_path.write_text(
        json.dumps(credit_log, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
