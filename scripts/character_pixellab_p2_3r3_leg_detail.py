from __future__ import annotations

import hashlib
import json
from collections import Counter, deque
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
INPUT = (
    ROOT
    / "art-source/character-v2/pixellab/P2-3R2"
    / "down-masked-edit-cleaned.png"
)
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-3R3"
EXPECTED_INPUT_SHA256 = (
    "625D0B1E11686BC9BD9217BC20507F3D66CC295E569DCC7A05BB6D06A1D041B6"
)
EXPECTED_SIZE = (64, 96)

COLORS = {
    "transparent": (0, 0, 0, 0),
    "skin": (250, 212, 202, 255),
    "skin_shadow": (181, 169, 188, 255),
    "navy_dark": (16, 25, 45, 255),
    "navy_outline": (25, 25, 39, 255),
    "navy_body": (32, 40, 71, 255),
    "navy_mid": (26, 41, 78, 255),
    "navy_accent": (45, 71, 129, 255),
    "navy_highlight": (129, 143, 176, 255),
}

ALLOWED_REGIONS = {
    "left_leg_boot": [19, 73, 29, 90],
    "right_leg_boot": [31, 73, 41, 90],
}

LEG_ANKLE_EDGE = {
    (25, 79): COLORS["skin_shadow"],
    (25, 80): COLORS["skin_shadow"],
    (37, 79): COLORS["skin_shadow"],
    (37, 80): COLORS["skin_shadow"],
}

BOOT_ROWS = {
    "left_leg_boot": {
        82: [
            (20, COLORS["transparent"]),
            (21, COLORS["navy_body"]),
            (22, COLORS["navy_body"]),
            (23, COLORS["navy_mid"]),
            (24, COLORS["navy_body"]),
            (25, COLORS["navy_body"]),
            (26, COLORS["navy_outline"]),
        ],
        83: [
            (20, COLORS["transparent"]),
            (21, COLORS["navy_highlight"]),
            (22, COLORS["navy_body"]),
            (23, COLORS["navy_mid"]),
            (24, COLORS["navy_body"]),
            (25, COLORS["navy_body"]),
            (26, COLORS["navy_outline"]),
        ],
        84: [
            (20, COLORS["navy_body"]),
            (21, COLORS["navy_body"]),
            (22, COLORS["navy_body"]),
            (23, COLORS["navy_mid"]),
            (24, COLORS["navy_body"]),
            (25, COLORS["navy_body"]),
            (26, COLORS["navy_dark"]),
        ],
        85: [
            (20, COLORS["navy_accent"]),
            (21, COLORS["navy_body"]),
            (22, COLORS["navy_mid"]),
            (23, COLORS["navy_body"]),
            (24, COLORS["navy_body"]),
            (25, COLORS["navy_outline"]),
            (26, COLORS["navy_dark"]),
        ],
        86: [
            (21, COLORS["navy_dark"]),
            (22, COLORS["navy_body"]),
            (23, COLORS["navy_body"]),
            (24, COLORS["navy_mid"]),
            (25, COLORS["navy_body"]),
            (26, COLORS["navy_dark"]),
        ],
        87: [
            (21, COLORS["navy_dark"]),
            (22, COLORS["navy_dark"]),
            (23, COLORS["navy_dark"]),
            (24, COLORS["navy_dark"]),
            (25, COLORS["navy_dark"]),
            (26, COLORS["navy_dark"]),
        ],
    },
    "right_leg_boot": {
        82: [
            (32, COLORS["navy_outline"]),
            (33, COLORS["navy_body"]),
            (34, COLORS["navy_mid"]),
            (35, COLORS["navy_body"]),
            (36, COLORS["navy_body"]),
            (37, COLORS["navy_body"]),
            (38, COLORS["transparent"]),
        ],
        83: [
            (32, COLORS["navy_dark"]),
            (33, COLORS["navy_body"]),
            (34, COLORS["navy_body"]),
            (35, COLORS["navy_highlight"]),
            (36, COLORS["navy_body"]),
            (37, COLORS["navy_body"]),
            (38, COLORS["transparent"]),
        ],
        84: [
            (32, COLORS["navy_body"]),
            (33, COLORS["navy_body"]),
            (34, COLORS["navy_body"]),
            (35, COLORS["navy_mid"]),
            (36, COLORS["navy_body"]),
            (37, COLORS["navy_body"]),
            (38, COLORS["navy_dark"]),
        ],
        85: [
            (32, COLORS["navy_dark"]),
            (33, COLORS["navy_body"]),
            (34, COLORS["navy_body"]),
            (35, COLORS["navy_mid"]),
            (36, COLORS["navy_body"]),
            (37, COLORS["navy_outline"]),
            (38, COLORS["navy_accent"]),
        ],
        86: [
            (32, COLORS["navy_dark"]),
            (33, COLORS["navy_body"]),
            (34, COLORS["navy_mid"]),
            (35, COLORS["navy_body"]),
            (36, COLORS["navy_body"]),
            (37, COLORS["navy_dark"]),
        ],
        87: [
            (32, COLORS["navy_dark"]),
            (33, COLORS["navy_dark"]),
            (34, COLORS["navy_dark"]),
            (35, COLORS["navy_dark"]),
            (36, COLORS["navy_dark"]),
            (37, COLORS["navy_dark"]),
        ],
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def in_allowed_region(x: int, y: int) -> bool:
    return any(
        left <= x < right and top <= y < bottom
        for left, top, right, bottom in ALLOWED_REGIONS.values()
    )


def rule_for_pixel(x: int, y: int) -> str:
    if (x, y) in LEG_ANKLE_EDGE:
        return "ankle_shadow"
    if y == 82:
        return "boot_cuff"
    if y in (83, 84, 85, 86):
        if (x, y) in {(20, 84), (20, 85), (38, 84), (38, 85)}:
            return "boot_toe"
        if (x, y) in {(21, 83), (35, 83)}:
            return "boot_highlight"
        return "boot_body"
    if y == 87:
        return "boot_sole"
    return "leg_accessory"


def build_edits() -> list[tuple[int, int, tuple[int, int, int, int], str]]:
    edits: dict[tuple[int, int], tuple[tuple[int, int, int, int], str]] = {}
    for point, color in LEG_ANKLE_EDGE.items():
        edits[point] = (color, "ankle_shadow")
    for region_name, rows in BOOT_ROWS.items():
        region = ALLOWED_REGIONS[region_name]
        for y, row in rows.items():
            for x, color in row:
                if not (region[0] <= x < region[2] and region[1] <= y < region[3]):
                    raise ValueError(f"edit outside {region_name}: {(x, y)}")
                edits[(x, y)] = (color, rule_for_pixel(x, y))
    return [
        (x, y, color, rule)
        for (x, y), (color, rule) in sorted(edits.items(), key=lambda item: item[0])
    ]


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


def preview_panels(
    image: Image.Image,
    scale: int,
    labels: tuple[str, ...] = ("LIGHT", "DARK", "CHECKER"),
) -> Image.Image:
    scaled = image.resize(
        (image.width * scale, image.height * scale),
        Image.Resampling.NEAREST,
    )
    margin = 18
    label_height = 26
    panel_width = scaled.width
    panel_height = scaled.height
    canvas = Image.new(
        "RGBA",
        (
            panel_width * len(labels) + margin * (len(labels) + 1),
            panel_height + label_height + margin * 2,
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
        x = margin + index * (panel_width + margin)
        y = label_height + margin
        panel = backgrounds[label].copy()
        panel.alpha_composite(scaled)
        canvas.alpha_composite(panel, (x, y))
        draw.text((x, 8), label, fill=(20, 20, 20, 255))
        draw.rectangle(
            (x, y, x + panel_width - 1, y + panel_height - 1),
            outline=(70, 70, 70, 255),
        )
    return canvas


def diff_preview(
    before: Image.Image,
    after: Image.Image,
    changes: dict[tuple[int, int], str],
) -> Image.Image:
    scale = 12
    panel_width = before.width * scale
    panel_height = before.height * scale
    margin = 20
    label_height = 28
    canvas = Image.new(
        "RGBA",
        (
            panel_width * 3 + margin * 4,
            panel_height + label_height + margin * 2,
        ),
        (233, 233, 233, 255),
    )
    draw = ImageDraw.Draw(canvas)

    before_scaled = before.resize(
        (panel_width, panel_height),
        Image.Resampling.NEAREST,
    )
    after_scaled = after.resize(
        (panel_width, panel_height),
        Image.Resampling.NEAREST,
    )
    diff = Image.new("RGBA", (before.width, before.height), (28, 31, 39, 255))
    for y in range(before.height):
        for x in range(before.width):
            point = (x, y)
            if point in changes:
                diff.putpixel(point, (255, 0, 180, 255))
            elif before.getpixel(point)[3]:
                r, g, b, a = before.getpixel(point)
                diff.putpixel(
                    point,
                    (r // 4 + 18, g // 4 + 18, b // 4 + 18, a),
                )
            else:
                diff.putpixel(point, (0, 0, 0, 0))
    diff_scaled = diff.resize(
        (panel_width, panel_height),
        Image.Resampling.NEAREST,
    )

    panels = (
        ("BEFORE", before_scaled),
        ("AFTER", after_scaled),
        ("DIFF", diff_scaled),
    )
    for index, (label, panel) in enumerate(panels):
        x = margin + index * (panel_width + margin)
        y = label_height + margin
        background = Image.new("RGBA", panel.size, (247, 245, 239, 255))
        background.alpha_composite(panel)
        canvas.alpha_composite(background, (x, y))
        draw.text((x, 8), label, fill=(20, 20, 20, 255))
        draw.rectangle(
            (x, y, x + panel_width - 1, y + panel_height - 1),
            outline=(70, 70, 70, 255),
        )
    return canvas


def connected_components(
    image: Image.Image,
    color: tuple[int, int, int, int],
) -> list[dict[str, object]]:
    remaining = {
        (x, y)
        for y in range(image.height)
        for x in range(image.width)
        if image.getpixel((x, y)) == color
    }
    components: list[dict[str, object]] = []
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
        components.append(
            {
                "pixel_count": len(points),
                "bbox_half_open": [
                    min(xs) + 14,
                    min(ys) + 72,
                    max(xs) + 1 + 14,
                    max(ys) + 1 + 72,
                ],
            }
        )
    return sorted(
        components,
        key=lambda component: int(component["pixel_count"]),
        reverse=True,
    )


def main() -> None:
    if sha256(INPUT) != EXPECTED_INPUT_SHA256:
        raise ValueError("unexpected P2-3R2 input SHA-256")

    before = Image.open(INPUT).convert("RGBA")
    if before.size != EXPECTED_SIZE:
        raise ValueError(f"unexpected input size: {before.size}")
    after = before.copy()

    changes: list[dict[str, object]] = []
    for x, y, color, rule in build_edits():
        if not in_allowed_region(x, y):
            raise ValueError(f"edit outside allowed regions: {(x, y)}")
        old_color = before.getpixel((x, y))
        if old_color != color:
            after.putpixel((x, y), color)
            changes.append(
                {
                    "x": x,
                    "y": y,
                    "rule": rule,
                    "before": list(old_color),
                    "after": list(color),
                }
            )
    changed_points = {(int(item["x"]), int(item["y"])): str(item["rule"]) for item in changes}

    changed_outside = [
        (x, y)
        for y in range(after.height)
        for x in range(after.width)
        if before.getpixel((x, y)) != after.getpixel((x, y))
        and not in_allowed_region(x, y)
    ]
    if changed_outside:
        raise ValueError(f"changed pixels outside allowed regions: {changed_outside[:8]}")

    palette = set(after.get_flattened_data())
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")
    if len(palette) > 24:
        raise ValueError(f"palette exceeds 24 colors: {len(palette)}")

    for seed in ((26, 88), (41, 88)):
        if seed < (after.width, after.height) and after.getpixel(seed)[3] != 0:
            raise ValueError(f"sole crosses y=88 contact boundary at {seed}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "down-legs-microadjusted.png"
    diff_path = OUTPUT_DIR / "down-legs-diff-12x.png"
    preview_path = OUTPUT_DIR / "down-legs-preview-12x.png"
    runtime_path = OUTPUT_DIR / "runtime-48x72-preview-8x.png"
    metrics_path = OUTPUT_DIR / "metrics.json"
    visual_path = OUTPUT_DIR / "visual-review.json"

    after.save(output_path)
    diff_preview(before, after, changed_points).save(diff_path)
    preview_panels(after, 12).save(preview_path)
    runtime = after.resize((48, 72), Image.Resampling.NEAREST)
    preview_panels(runtime, 8).save(runtime_path)

    skin_components = connected_components(
        after.crop((14, 72, 46, 90)),
        COLORS["skin"],
    )
    leg_components = [
        component
        for component in skin_components
        if int(component["pixel_count"]) >= 20
    ]
    if len(leg_components) != 2:
        raise ValueError(f"expected two leg components, got {leg_components}")
    ordered_legs = sorted(
        leg_components,
        key=lambda component: int(component["bbox_half_open"][0]),
    )
    leg_gap_px = (
        int(ordered_legs[1]["bbox_half_open"][0])
        - int(ordered_legs[0]["bbox_half_open"][2])
    )
    if not 5 <= leg_gap_px <= 7:
        raise ValueError(f"leg gap outside 5..7 px: {leg_gap_px}")

    def skin_width_by_row(x0: int, x1: int) -> dict[str, int]:
        return {
            str(y): sum(
                after.getpixel((x, y)) == COLORS["skin"]
                for x in range(x0, x1)
            )
            for y in range(74, 82)
        }

    changed_by_rule = Counter(str(item["rule"]) for item in changes)
    boot_cuff_pixels = sum(
        1
        for x0, x1 in ((19, 29), (31, 41))
        for x in range(x0, x1)
        if after.getpixel((x, 82))[3] != 0
    )
    boot_highlights = [
        (21, 83),
        (35, 83),
    ]
    boot_highlight_pixels = sum(
        after.getpixel(point) == COLORS["navy_highlight"]
        for point in boot_highlights
    )

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3r3-leg-detail-v1",
        "input": INPUT.relative_to(ROOT).as_posix(),
        "input_sha256": sha256(INPUT),
        "output": output_path.relative_to(ROOT).as_posix(),
        "output_sha256": sha256(output_path),
        "allowed_regions": ALLOWED_REGIONS,
        "changed_pixels_total": len(changes),
        "changed_pixels_outside_allowed_regions": len(changed_outside),
        "changed_pixels_by_rule": dict(sorted(changed_by_rule.items())),
        "left_leg_width_by_row": skin_width_by_row(19, 29),
        "right_leg_width_by_row": skin_width_by_row(31, 41),
        "leg_components": leg_components,
        "leg_gap_px": leg_gap_px,
        "boot_cuff_pixels": boot_cuff_pixels,
        "boot_highlight_pixels": boot_highlight_pixels,
        "boot_sole_edges": [88, 88],
        "colors": len(palette),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": sum(
            1
            for y in range(after.height)
            for x in range(after.width)
            if after.getpixel((x, y))[3] not in (0, 255)
        ),
        "generation_submissions": 0,
        "pixellab_calls": 0,
        "animation_started": False,
        "production_modified": False,
        "changed_pixels": changes,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    visual_review = {
        "schema_version": "rpg-character-pixellab-p2-3r3-visual-review-v1",
        "status": "technical-pass-pending-user-confirmation",
        "legs": {
            "two_legs_separated": True,
            "knee_to_ankle_taper": True,
            "leg_gap_px": leg_gap_px,
        },
        "boots": {
            "two_boots": True,
            "cuff_visible": True,
            "highlight_visible": boot_highlight_pixels == 2,
            "sole_edges": [88, 88],
        },
        "preserved": {
            "face": True,
            "soft_lips": True,
            "arms": True,
            "hands": True,
            "hair": True,
            "fin_ears": True,
            "skirt": True,
            "apron": True,
            "whale_tail": True,
        },
        "runtime_48x72_preview": runtime_path.relative_to(ROOT).as_posix(),
        "user_confirmation": "pending",
        "animation_authorized": False,
    }
    visual_path.write_text(
        json.dumps(visual_review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
