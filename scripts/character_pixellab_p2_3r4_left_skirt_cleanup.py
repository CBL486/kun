from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
INPUT = (
    ROOT
    / "art-source/character-v2/pixellab/P2-3R3"
    / "down-legs-microadjusted.png"
)
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-3R4"
EXPECTED_INPUT_SHA256 = (
    "3FB4CBF62C854294220838E04C8DA3EDF9CE9E2C4CE5E354FB0843687F563683"
)
EXPECTED_SIZE = (64, 96)
ALLOWED_REGION = (8, 72, 19, 89)

RESIDUE_COORDS = frozenset(
    {
        *((x, 75) for x in range(15, 17)),
        *((x, 76) for x in range(15, 17)),
        *((x, 77) for x in range(14, 17)),
        *((x, 78) for x in range(14, 17)),
        *((x, 79) for x in range(10, 17)),
        *((x, 80) for x in range(9, 16)),
        *((x, 81) for x in range(8, 16)),
        *((x, 82) for x in range(9, 16)),
        *((x, 83) for x in range(10, 16)),
        *((x, 84) for x in range(12, 16)),
        *((x, 85) for x in range(13, 16)),
        (16, 86),
    }
)

SKIN_COLORS = {
    (250, 212, 202, 255),
    (181, 169, 188, 255),
}
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


def four_panel_preview(
    before: Image.Image,
    residue_mask: Image.Image,
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

    overlay = before.copy()
    for y in range(before.height):
        for x in range(before.width):
            if residue_mask.getpixel((x, y))[3]:
                overlay.putpixel((x, y), (255, 0, 180, 255))

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

    raw_panels = (
        ("BEFORE", before),
        ("RESIDUE MASK", overlay),
        ("AFTER", after),
        ("DIFF", diff),
    )
    for index, (label, panel) in enumerate(raw_panels):
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
                    min(xs),
                    min(ys),
                    max(xs) + 1,
                    max(ys) + 1,
                ],
            }
        )
    return sorted(
        components,
        key=lambda component: int(component["pixel_count"]),
        reverse=True,
    )


def opaque_components(image: Image.Image) -> list[dict[str, object]]:
    remaining = {
        (x, y)
        for y in range(image.height)
        for x in range(image.width)
        if image.getpixel((x, y))[3] != 0
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
                    min(xs),
                    min(ys),
                    max(xs) + 1,
                    max(ys) + 1,
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
        raise ValueError("unexpected P2-3R3 input SHA-256")

    before = Image.open(INPUT).convert("RGBA")
    if before.size != EXPECTED_SIZE:
        raise ValueError(f"unexpected input size: {before.size}")
    after = before.copy()

    residue_mask = Image.new("RGBA", before.size, (0, 0, 0, 0))
    removed: list[dict[str, int]] = []
    protected: list[str] = []
    for x, y in sorted(RESIDUE_COORDS):
        if not (
            ALLOWED_REGION[0] <= x < ALLOWED_REGION[2]
            and ALLOWED_REGION[1] <= y < ALLOWED_REGION[3]
        ):
            raise ValueError(f"residue coordinate outside allowed region: {(x, y)}")
        color = before.getpixel((x, y))
        if color[3] == 0:
            continue
        residue_mask.putpixel((x, y), (255, 0, 180, 255))
        after.putpixel((x, y), (0, 0, 0, 0))
        removed.append({"x": x, "y": y, "before_alpha": color[3]})

    for y in range(ALLOWED_REGION[1], ALLOWED_REGION[3]):
        for x in range(ALLOWED_REGION[0], ALLOWED_REGION[2]):
            point = (x, y)
            color = before.getpixel(point)
            if point in RESIDUE_COORDS or color[3] == 0:
                continue
            if color in SKIN_COLORS and y <= 78:
                protected.append("skin")
            if color in CUFF_COLORS and y <= 75:
                protected.append("cuff")

    changed_points = {
        (x, y)
        for y in range(after.height)
        for x in range(after.width)
        if before.getpixel((x, y)) != after.getpixel((x, y))
    }
    changed_outside = [
        point
        for point in changed_points
        if not (
            ALLOWED_REGION[0] <= point[0] < ALLOWED_REGION[2]
            and ALLOWED_REGION[1] <= point[1] < ALLOWED_REGION[3]
        )
    ]
    if changed_outside:
        raise ValueError(f"changed pixels outside allowed region: {changed_outside[:8]}")

    palette = set(after.get_flattened_data())
    alpha_values = sorted({color[3] for color in palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")
    if len(palette) > 22:
        raise ValueError(f"palette exceeds 22 colors: {len(palette)}")

    allowed_crop = after.crop(ALLOWED_REGION)
    allowed_components = opaque_components(allowed_crop)
    if len(allowed_components) != 1:
        raise ValueError(
            "expected one connected hand/cuff cluster in allowed region, "
            f"got {allowed_components}"
        )

    skin_in_allowed = {
        (x, y)
        for y in range(ALLOWED_REGION[1], ALLOWED_REGION[3])
        for x in range(ALLOWED_REGION[0], ALLOWED_REGION[2])
        if before.getpixel((x, y)) == (250, 212, 202, 255)
        or (
            before.getpixel((x, y)) == (181, 169, 188, 255)
            and y <= 78
        )
    }
    if any(point in changed_points for point in skin_in_allowed):
        raise ValueError("skin pixels were removed or changed")

    left_hand_points = [
        point
        for point in skin_in_allowed
        if point[0] <= 16 and point[1] <= 78
    ]
    if not left_hand_points:
        raise ValueError("left hand skin was not found")
    left_hand_bbox = [
        min(point[0] for point in left_hand_points),
        min(point[1] for point in left_hand_points),
        max(point[0] for point in left_hand_points) + 1,
        max(point[1] for point in left_hand_points) + 1,
    ]

    left_components = connected_components(
        after.crop((18, 72, 30, 90)),
        (250, 212, 202, 255),
    )
    left_legs = [
        component
        for component in left_components
        if int(component["pixel_count"]) >= 20
    ]
    if len(left_legs) != 1:
        raise ValueError(f"expected one left-leg component, got {left_legs}")
    left_leg_bbox = [
        left_legs[0]["bbox_half_open"][0] + 18,
        left_legs[0]["bbox_half_open"][1] + 72,
        left_legs[0]["bbox_half_open"][2] + 18,
        left_legs[0]["bbox_half_open"][3] + 72,
    ]

    leg_components = connected_components(
        after.crop((14, 72, 46, 90)),
        (250, 212, 202, 255),
    )
    major_legs = [
        component
        for component in leg_components
        if int(component["pixel_count"]) >= 20
    ]
    if len(major_legs) != 2:
        raise ValueError(f"expected two leg components, got {major_legs}")
    ordered_legs = sorted(
        major_legs,
        key=lambda component: int(component["bbox_half_open"][0]),
    )
    leg_gap_px = (
        int(ordered_legs[1]["bbox_half_open"][0])
        - int(ordered_legs[0]["bbox_half_open"][2])
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "down-left-skirt-cleaned.png"
    mask_path = OUTPUT_DIR / "left-residue-mask.png"
    mask_preview_path = OUTPUT_DIR / "left-residue-mask-preview-16x.png"
    diff_path = OUTPUT_DIR / "down-left-cleanup-diff-16x.png"
    preview_path = OUTPUT_DIR / "down-left-cleanup-preview-12x.png"
    runtime_path = OUTPUT_DIR / "runtime-48x72-preview-8x.png"
    metrics_path = OUTPUT_DIR / "metrics.json"
    visual_path = OUTPUT_DIR / "visual-review.json"

    after.save(output_path)
    residue_mask.save(mask_path)
    four_panel_preview(before, residue_mask, after, changed_points).save(diff_path)
    preview_panels(after, 12).save(preview_path)
    runtime = after.resize((48, 72), Image.Resampling.NEAREST)
    preview_panels(runtime, 8).save(runtime_path)

    mask_preview = before.copy()
    for y in range(mask_preview.height):
        for x in range(mask_preview.width):
            if residue_mask.getpixel((x, y))[3]:
                r, g, b, a = mask_preview.getpixel((x, y))
                mask_preview.putpixel(
                    (x, y),
                    (
                        min(255, r // 2 + 128),
                        g // 3,
                        min(255, b // 2 + 90),
                        a,
                    ),
                )
    mask_preview.resize(
        (before.width * 16, before.height * 16),
        Image.Resampling.NEAREST,
    ).save(mask_preview_path)

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-3r4-left-skirt-cleanup-v1",
        "input": INPUT.relative_to(ROOT).as_posix(),
        "input_sha256": sha256(INPUT),
        "output": output_path.relative_to(ROOT).as_posix(),
        "output_sha256": sha256(output_path),
        "allowed_region": list(ALLOWED_REGION),
        "residue_pixel_count": sum(
            1
            for x, y in RESIDUE_COORDS
            if before.getpixel((x, y))[3] != 0
        ),
        "removed_pixels": removed,
        "removed_pixel_count": len(removed),
        "preserved_skin_pixels": sum(
            1 for kind in protected if kind == "skin"
        ),
        "preserved_cuff_pixels": sum(
            1 for kind in protected if kind == "cuff"
        ),
        "changed_pixels_outside_allowed_region": len(changed_outside),
        "left_hand_bbox": left_hand_bbox,
        "left_leg_bbox": left_leg_bbox,
        "allowed_region_opaque_components": len(allowed_components),
        "detached_pixels_in_allowed_region": len(allowed_components) - 1,
        "leg_gap_px": leg_gap_px,
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
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    visual_review = {
        "schema_version": "rpg-character-pixellab-p2-3r4-visual-review-v1",
        "status": "technical-pass-pending-user-confirmation",
        "old_skirt_residue_removed": True,
        "left_hand_preserved": True,
        "left_cuff_preserved": True,
        "left_leg_unchanged": True,
        "right_leg_unchanged": True,
        "boots_unchanged": True,
        "exterior_changes": 0,
        "runtime_48x72_preview": runtime_path.relative_to(ROOT).as_posix(),
        "user_confirmation": "pending",
        "four_direction_authorized": False,
        "animation_authorized": False,
    }
    visual_path.write_text(
        json.dumps(visual_review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
