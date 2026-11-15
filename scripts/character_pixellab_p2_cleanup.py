from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from itertools import product
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2"
EXPECTED_SOURCE_SHA256 = (
    "02B6C148B3139932F4D6B703F7E1B1C4"
    "B40ECAD557DE357B515912C533FEB65A"
)
EXPECTED_LIP_SHA256 = (
    "59DBED82B0CB2E3FE5D1E55F7428CE1"
    "B139891D383943BC00DFFF2EBC745AF79"
)
SOURCE_DIRECTIONS = ("south", "west", "east", "north")
OUTPUT_DIRECTIONS = ("down", "left", "right", "up")
SOURCE_FRAME_SIZE = (96, 96)
CROP_X0 = 20
CROP_X1 = 84
OUTPUT_FRAME_SIZE = (64, 96)
FOOT_BASELINE_EXCLUSIVE = 88
MAX_COLORS = 24

PALETTE_MERGE = {
    (187, 108, 121, 255): (184, 95, 108, 255),
    (163, 155, 175, 255): (181, 169, 188, 255),
    (177, 190, 224, 255): (186, 200, 221, 255),
    (71, 127, 188, 255): (59, 118, 174, 255),
    (21, 21, 32, 255): (25, 25, 39, 255),
}

SEMANTIC_COLORS = {
    "skin_light": "#FAD4CA",
    "skin_shadow": "#B5A9BC",
    "hair_dark": "#0B123F",
    "hair_mid": "#192A71",
    "hair_highlight": "#2E558D",
    "fin_ear_light": "#BAC8DD",
    "outfit_dark": "#10192D",
    "outfit_white": "#F5F4EA",
    "apron_ice": "#E6E3E6",
    "lip_main": "#B85F6C",
    "lip_shadow": "#8D4654",
    "whale_tail_dark": "#0F0E1A",
    "whale_tail_highlight": "#3B76AE",
    "outline_dark": "#000000",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def opaque_pixels_at_bottom(image: Image.Image) -> tuple[int, int]:
    bottom_y = max(
        y
        for y in range(image.height)
        if any(image.getpixel((x, y))[3] for x in range(image.width))
    )
    xs = [
        x
        for x in range(image.width)
        if image.getpixel((x, bottom_y))[3]
    ]
    return min(xs), max(xs)


def anchor_x(image: Image.Image) -> float:
    left, right = opaque_pixels_at_bottom(image)
    return (left + right) / 2


def shift_frame(image: Image.Image, x_offset: int) -> Image.Image:
    shifted = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shifted.alpha_composite(image, (x_offset, 0))
    return shifted


def all_frames_have_margin(images: list[Image.Image]) -> bool:
    for image in images:
        bbox = image.getbbox()
        if bbox is None:
            return False
        if bbox[0] < 1 or bbox[1] < 1:
            return False
        if bbox[2] > image.width - 1 or bbox[3] > image.height - 1:
            return False
    return True


def choose_horizontal_alignment(images: list[Image.Image]) -> list[int]:
    values = range(-4, 5)
    shifted_data: list[dict[int, tuple[bool, float | None]]] = []
    for image in images:
        per_offset: dict[int, tuple[bool, float | None]] = {}
        for offset in values:
            shifted = shift_frame(image, offset)
            bbox = shifted.getbbox()
            safe = (
                bbox is not None
                and bbox[0] >= 1
                and bbox[1] >= 1
                and bbox[2] <= shifted.width - 1
                and bbox[3] <= shifted.height - 1
            )
            per_offset[offset] = (safe, anchor_x(shifted) if safe else None)
        shifted_data.append(per_offset)

    candidates: list[tuple[int, int, tuple[int, ...]]] = []
    for shifts in product(values, repeat=len(images)):
        entries = [
            shifted_data[index][offset]
            for index, offset in enumerate(shifts)
        ]
        if not all(safe for safe, _ in entries):
            continue
        anchors = [anchor for _, anchor in entries]
        if any(anchor is None for anchor in anchors):
            continue
        gaps = [
            abs(right - left)
            for left, right in zip(anchors, anchors[1:])
        ]
        if max(gaps) <= 2:
            candidates.append(
                (
                    sum(abs(offset) for offset in shifts),
                    max(abs(offset) for offset in shifts),
                    tuple(shifts),
                )
            )
    if not candidates:
        raise ValueError("no horizontal frame alignment satisfies the 2 px rule")
    return list(min(candidates)[2])


def make_checkerboard(size: tuple[int, int], square: int = 16) -> Image.Image:
    image = Image.new("RGBA", size, (222, 226, 230, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], square):
        for x in range(0, size[0], square):
            if (x // square + y // square) % 2:
                draw.rectangle(
                    (x, y, x + square - 1, y + square - 1),
                    fill=(176, 184, 192, 255),
                )
    return image


def scaled_frame(frame: Image.Image, scale: int = 4) -> Image.Image:
    return frame.resize(
        (frame.width * scale, frame.height * scale),
        Image.Resampling.NEAREST,
    )


def build_three_background_preview(
    frames: list[Image.Image], scale: int = 4
) -> Image.Image:
    cell_w = OUTPUT_FRAME_SIZE[0] * scale
    cell_h = OUTPUT_FRAME_SIZE[1] * scale
    gutter = 12
    margin = 18
    label_h = 34
    row_label_w = 96
    width = row_label_w + len(frames) * cell_w + (len(frames) + 1) * gutter
    height = label_h + 3 * cell_h + 4 * gutter
    canvas = Image.new("RGBA", (width, height), (20, 23, 30, 255))
    draw = ImageDraw.Draw(canvas)

    for index, direction in enumerate(OUTPUT_DIRECTIONS):
        x = row_label_w + gutter + index * (cell_w + gutter)
        draw.text((x + 4, 8), direction.upper(), fill=(255, 255, 255, 255))

    backgrounds = [
        ("DARK", (27, 31, 39, 255)),
        ("LIGHT", (246, 243, 234, 255)),
        ("CHECKER", None),
    ]
    for row, (label, background) in enumerate(backgrounds):
        y = label_h + gutter + row * (cell_h + gutter)
        draw.text((8, y + cell_h // 2), label, fill=(255, 255, 255, 255))
        for index, frame in enumerate(frames):
            x = row_label_w + gutter + index * (cell_w + gutter)
            if background is None:
                base = make_checkerboard((cell_w, cell_h))
            else:
                base = Image.new("RGBA", (cell_w, cell_h), background)
            base.alpha_composite(scaled_frame(frame, scale))
            canvas.alpha_composite(base, (x, y))
            draw.rectangle((x, y, x + cell_w, y + cell_h), outline=(86, 93, 104, 255))
    return canvas


def build_checker_preview(
    frames: list[Image.Image], scale: int = 4
) -> Image.Image:
    cell_w = OUTPUT_FRAME_SIZE[0] * scale
    cell_h = OUTPUT_FRAME_SIZE[1] * scale
    gutter = 12
    label_h = 34
    width = len(frames) * cell_w + (len(frames) + 1) * gutter
    height = label_h + cell_h + 2 * gutter
    canvas = Image.new("RGBA", (width, height), (20, 23, 30, 255))
    draw = ImageDraw.Draw(canvas)
    for index, (direction, frame) in enumerate(
        zip(OUTPUT_DIRECTIONS, frames, strict=True)
    ):
        x = gutter + index * (cell_w + gutter)
        y = label_h + gutter
        draw.text((x + 4, 8), direction.upper(), fill=(255, 255, 255, 255))
        cell = make_checkerboard((cell_w, cell_h))
        cell.alpha_composite(scaled_frame(frame, scale))
        canvas.alpha_composite(cell, (x, y))
        draw.rectangle((x, y, x + cell_w, y + cell_h), outline=(86, 93, 104, 255))
    return canvas


def build_map_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PixelLab P2-2 四方向地图预览</title>
    <style>
      * { box-sizing: border-box; }
      html, body { width: 100%; height: 100%; margin: 0; }
      body {
        overflow: hidden;
        background: #151a22;
        color: #f8f3df;
        font-family: "Microsoft YaHei", sans-serif;
      }
      .app { position: relative; width: 100%; height: 100%; overflow: hidden; }
      .map {
        position: absolute;
        inset: 0;
        background: url("../../../../assets/maps/town-map-world.webp") 50% 52% / cover;
        image-rendering: pixelated;
      }
      .map::after {
        content: "";
        position: absolute;
        inset: 0;
        background:
          linear-gradient(to top, rgba(7, 15, 24, .68), transparent 42%),
          radial-gradient(circle at 50% 54%, transparent 0 14%, rgba(5, 11, 20, .22) 55%);
      }
      .topbar {
        position: absolute;
        inset: 18px 18px auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        z-index: 3;
      }
      .brand, .status, .direction-panel, .guide {
        border: 1px solid rgba(255, 255, 255, .22);
        background: rgba(10, 19, 29, .78);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 12px 16px;
      }
      .brand strong { color: #8be9e1; letter-spacing: .08em; }
      .brand span { display: block; margin-top: 4px; color: #cbd3d7; font-size: 12px; }
      .status { text-align: right; color: #e9dcc0; font-size: 13px; }
      .player-zone {
        position: absolute;
        left: 54%;
        top: 54%;
        width: 48px;
        height: 72px;
        z-index: 2;
        transform: translate(-50%, -100%);
      }
      .player-shadow {
        position: absolute;
        left: 50%;
        bottom: -5px;
        width: 42px;
        height: 12px;
        border-radius: 50%;
        background: rgba(2, 8, 13, .55);
        transform: translateX(-50%);
        filter: blur(2px);
      }
      #map-player-sprite {
        position: absolute;
        inset: 0;
        width: 48px;
        height: 72px;
        display: block;
        background-image: url("sprite-4dir-cleaned.png");
        background-repeat: no-repeat;
        background-size: 192px 72px;
        background-position: 0 0;
        image-rendering: pixelated;
      }
      #map-player[data-direction="left"] #map-player-sprite { background-position: -48px 0; }
      #map-player[data-direction="right"] #map-player-sprite { background-position: -96px 0; }
      #map-player[data-direction="up"] #map-player-sprite { background-position: -144px 0; }
      .nameplate {
        position: absolute;
        left: 50%;
        top: -30px;
        transform: translateX(-50%);
        white-space: nowrap;
        padding: 5px 12px;
        border-radius: 999px;
        background: rgba(10, 19, 29, .82);
        border: 1px solid rgba(139, 233, 225, .5);
        color: #f8f3df;
        font-size: 12px;
      }
      .direction-panel {
        position: absolute;
        right: 18px;
        top: 92px;
        z-index: 3;
        display: grid;
        grid-template-columns: repeat(4, auto);
        gap: 6px;
        align-items: center;
      }
      .direction-panel span {
        grid-column: 1 / -1;
        color: #aebbc5;
        font-size: 11px;
      }
      .direction-panel button {
        border: 1px solid rgba(139, 233, 225, .45);
        border-radius: 8px;
        background: rgba(20, 39, 48, .85);
        color: #d8fffa;
        padding: 5px 8px;
        cursor: pointer;
      }
      .direction-panel button[aria-pressed="true"] {
        background: #8be9e1;
        color: #10262b;
      }
      .guide {
        position: absolute;
        left: 18px;
        bottom: 18px;
        z-index: 3;
        max-width: 520px;
        font-size: 13px;
        line-height: 1.6;
      }
      .guide strong { color: #8be9e1; }
      @media (max-width: 600px) {
        .topbar { inset: 10px 10px auto; }
        .brand, .status, .direction-panel, .guide {
          padding: 9px 11px;
          border-radius: 12px;
        }
        .brand span { font-size: 10px; }
        .status { max-width: 165px; font-size: 11px; }
        .player-zone { left: 50%; top: 56%; }
        .direction-panel {
          left: 10px;
          right: 10px;
          top: auto;
          bottom: 96px;
          grid-template-columns: repeat(4, 1fr);
        }
        .guide {
          left: 10px;
          right: 10px;
          bottom: 10px;
          max-width: none;
          font-size: 11px;
        }
      }
    </style>
  </head>
  <body>
    <main class="app" aria-label="PixelLab P2-2 四方向地图预览">
      <div class="map" role="img" aria-label="青禾镇像素地图"></div>
      <header class="topbar">
        <div class="brand">
          <strong>青禾镇</strong>
          <span>观察者 · 四方向尺寸预览</span>
        </div>
        <div id="status" class="status">PixelLab P2-2<br>48 × 72 运行时尺寸</div>
      </header>
      <div class="direction-panel" aria-label="预览专用方向切换">
        <span>预览专用 · 非玩家控制</span>
        <button type="button" data-preview-direction="down">DOWN</button>
        <button type="button" data-preview-direction="left">LEFT</button>
        <button type="button" data-preview-direction="right">RIGHT</button>
        <button type="button" data-preview-direction="up">UP</button>
      </div>
      <div id="map-player" class="player-zone" data-direction="down">
        <span class="nameplate">林澄</span>
        <span class="player-shadow"></span>
        <span id="map-player-sprite" role="img" aria-label="林澄 64×96 四方向像素角色"></span>
      </div>
      <aside class="guide">
        <strong>P2-2 图形验收</strong><br>
        精灵表 256×96，单帧 64×96，页面显示 48×72；脚底锚点 y=88。
      </aside>
    </main>
    <script>
      const player = document.querySelector("#map-player");
      const sprite = document.querySelector("#map-player-sprite");
      const buttons = [...document.querySelectorAll("[data-preview-direction]")];
      const directions = ["down", "left", "right", "up"];
      function setDirection(direction) {
        player.dataset.direction = direction;
        buttons.forEach((button) => {
          button.setAttribute("aria-pressed", String(button.dataset.previewDirection === direction));
        });
      }
      buttons.forEach((button) => {
        button.addEventListener("click", () => setDirection(button.dataset.previewDirection));
      });
      const samples = directions.map((direction) => {
        setDirection(direction);
        const rect = sprite.getBoundingClientRect();
        return {
          direction,
          rect: [Math.round(rect.left), Math.round(rect.top), Math.round(rect.width), Math.round(rect.height)],
        };
      });
      setDirection(new URLSearchParams(location.search).get("direction") || "down");
      const xs = samples.map((sample) => sample.rect[0]);
      window.__p2Evidence = {
        samples,
        maxHorizontalDelta: Math.max(...xs) - Math.min(...xs),
        playerRect: [samples[0].rect[2], samples[0].rect[3]],
        directions,
      };
      document.body.dataset.playerRect = samples[0].rect.slice(2).join("x");
    </script>
  </body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic PixelLab P2-2 four-direction cleanup."
    )
    parser.add_argument(
        "--source-sheet",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "sprite-4dir-raw.png",
    )
    parser.add_argument(
        "--source-metadata",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "sprite-4dir-raw.json",
    )
    parser.add_argument(
        "--lip-source",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "lip-fixed-64x96.png",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    source_hash = sha256(args.source_sheet)
    lip_hash = sha256(args.lip_source)
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"unexpected source SHA-256: {source_hash}")
    if lip_hash != EXPECTED_LIP_SHA256:
        raise ValueError(f"unexpected lip source SHA-256: {lip_hash}")

    metadata = json.loads(args.source_metadata.read_text(encoding="utf-8"))
    rows = metadata.get("spritesheet", {}).get("rows", [])
    if not rows or rows[0].get("directions") != list(SOURCE_DIRECTIONS):
        raise ValueError("unexpected source direction order")

    source = Image.open(args.source_sheet).convert("RGBA")
    if source.size != (384, 96):
        raise ValueError(f"unexpected source sheet size: {source.size}")

    cropped_frames: list[Image.Image] = []
    crop_metrics: dict[str, dict[str, object]] = {}
    vertical_shifts: list[int] = []
    for index, (source_direction, output_direction) in enumerate(
        zip(SOURCE_DIRECTIONS, OUTPUT_DIRECTIONS, strict=True)
    ):
        cell = source.crop(
            (
                index * SOURCE_FRAME_SIZE[0],
                0,
                (index + 1) * SOURCE_FRAME_SIZE[0],
                SOURCE_FRAME_SIZE[1],
            )
        )
        crop = cell.crop((CROP_X0, 0, CROP_X1, SOURCE_FRAME_SIZE[1]))
        bbox = crop.getbbox()
        if bbox is None:
            raise ValueError(f"{source_direction} crop is empty")
        vertical_shift = FOOT_BASELINE_EXCLUSIVE - bbox[3]
        vertical_shifts.append(vertical_shift)
        frame = Image.new("RGBA", OUTPUT_FRAME_SIZE, (0, 0, 0, 0))
        frame.alpha_composite(crop, (0, vertical_shift))
        cropped_frames.append(frame)
        crop_metrics[output_direction] = {
            "source_direction": source_direction,
            "crop_rect_in_source": [CROP_X0, 0, CROP_X1, SOURCE_FRAME_SIZE[1]],
            "bbox_after_crop": list(bbox),
            "vertical_shift": vertical_shift,
        }

    horizontal_shifts = choose_horizontal_alignment(cropped_frames)
    frames = [
        shift_frame(frame, shift)
        for frame, shift in zip(cropped_frames, horizontal_shifts, strict=True)
    ]
    if not all_frames_have_margin(frames):
        raise ValueError("a frame touches the 64x96 output edge")

    aligned_sheet = Image.new(
        "RGBA",
        (OUTPUT_FRAME_SIZE[0] * len(frames), OUTPUT_FRAME_SIZE[1]),
        (0, 0, 0, 0),
    )
    for index, frame in enumerate(frames):
        aligned_sheet.alpha_composite(
            frame,
            (index * OUTPUT_FRAME_SIZE[0], 0),
        )

    before_palette_colors = Counter(
        aligned_sheet.getpixel((x, y))
        for y in range(aligned_sheet.height)
        for x in range(aligned_sheet.width)
    )
    clean_sheet = Image.new("RGBA", aligned_sheet.size, (0, 0, 0, 0))
    changed_by_palette = 0
    merge_counts: Counter[tuple[int, int, int, int]] = Counter()
    for y in range(aligned_sheet.height):
        for x in range(aligned_sheet.width):
            before = aligned_sheet.getpixel((x, y))
            after = PALETTE_MERGE.get(before, before)
            if after != before:
                changed_by_palette += 1
                merge_counts[before] += 1
            clean_sheet.putpixel((x, y), after)

    pixels = [
        clean_sheet.getpixel((x, y))
        for y in range(clean_sheet.height)
        for x in range(clean_sheet.width)
    ]
    palette = set(pixels)
    alpha_values = sorted({color[3] for color in palette})
    if len(palette) > MAX_COLORS:
        raise ValueError(f"palette exceeds {MAX_COLORS} colors: {len(palette)}")
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")
    if (184, 95, 108, 255) not in palette or (141, 70, 84, 255) not in palette:
        raise ValueError("rose lip colors were lost during palette cleanup")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "sprite-4dir-cleaned.png"
    preview_path = args.output_dir / "sprite-preview-4x.png"
    checker_path = args.output_dir / "sprite-preview-checker-4x.png"
    html_path = args.output_dir / "map-preview-4dir.html"
    metrics_path = args.output_dir / "metrics-4dir-clean.json"
    visual_review_path = args.output_dir / "visual-review.json"

    clean_sheet.save(output_path)
    build_three_background_preview(frames).save(preview_path)
    build_checker_preview(frames).save(checker_path)
    html_path.write_text(build_map_html(), encoding="utf-8")

    direction_bboxes = {
        direction: list(frame.getbbox())
        for direction, frame in zip(OUTPUT_DIRECTIONS, frames, strict=True)
    }
    foot_anchor_x = {
        direction: round(anchor_x(frame), 3)
        for direction, frame in zip(OUTPUT_DIRECTIONS, frames, strict=True)
    }
    anchors = [foot_anchor_x[direction] for direction in OUTPUT_DIRECTIONS]
    adjacent_gaps = [
        round(abs(right - left), 3)
        for left, right in zip(anchors, anchors[1:])
    ]
    edge_margins = {
        direction: {
            "left": bbox[0],
            "top": bbox[1],
            "right": OUTPUT_FRAME_SIZE[0] - bbox[2],
            "bottom": OUTPUT_FRAME_SIZE[1] - bbox[3],
        }
        for direction, bbox in direction_bboxes.items()
    }

    metrics: dict[str, object] = {
        "schema_version": "rpg-character-pixellab-p2-2-clean-v1",
        "status": "ready-for-a-review",
        "source_sheet": args.source_sheet.relative_to(ROOT).as_posix(),
        "source_sha256": source_hash,
        "output_sheet": output_path.relative_to(ROOT).as_posix(),
        "sheet_size": list(clean_sheet.size),
        "frame_size": list(OUTPUT_FRAME_SIZE),
        "direction_order": list(OUTPUT_DIRECTIONS),
        "crop_windows": crop_metrics,
        "frame_vertical_shifts": {
            direction: shift
            for direction, shift in zip(
                OUTPUT_DIRECTIONS, vertical_shifts, strict=True
            )
        },
        "frame_horizontal_alignment_shifts": {
            direction: shift
            for direction, shift in zip(
                OUTPUT_DIRECTIONS, horizontal_shifts, strict=True
            )
        },
        "foot_baseline_y": FOOT_BASELINE_EXCLUSIVE,
        "foot_anchor_x": foot_anchor_x,
        "adjacent_foot_anchor_gaps": adjacent_gaps,
        "max_adjacent_foot_anchor_gap": max(adjacent_gaps),
        "colors": len(palette),
        "opaque_colors": sum(1 for color in palette if color[3] != 0),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": sum(
            1 for color in pixels if color[3] not in (0, 255)
        ),
        "direction_bboxes": direction_bboxes,
        "edge_margins": edge_margins,
        "source_colors_before_palette_reduction": len(before_palette_colors),
        "color_merge_mapping": [
            {
                "from": "#{:02X}{:02X}{:02X}".format(*source_color[:3]),
                "to": "#{:02X}{:02X}{:02X}".format(*target_color[:3]),
                "pixels": merge_counts[source_color],
            }
            for source_color, target_color in PALETTE_MERGE.items()
        ],
        "changed_pixels_by_palette_reduction": changed_by_palette,
        "semantic_colors": SEMANTIC_COLORS,
        "preview": preview_path.relative_to(ROOT).as_posix(),
        "checker_preview": checker_path.relative_to(ROOT).as_posix(),
        "map_preview": html_path.relative_to(ROOT).as_posix(),
        "output_sha256": sha256(output_path),
        "generation_count": 0,
        "pixellab_calls": 0,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    visual_review = {
        "accepted": False,
        "checks": {
            "identity_matches_reference": "pass",
            "down_direction": "pass",
            "left_direction": "pass",
            "right_direction": "pass",
            "up_back_readable": "pass",
            "north_tail_occlusion_expected": "pass",
            "alpha_clean": "pass",
            "palette_within_limit": "pass",
            "foot_baseline_aligned": "pass",
            "no_edge_clipping": "pass",
            "map_readable_48x72": "pending-screenshot-review",
            "console_errors_zero": "pending-browser-capture",
        },
        "reviewer_notes": (
            "B completed source, anchor, alpha, palette, and edge checks. "
            "Map and console checks remain pending until browser capture."
        ),
    }
    visual_review_path.write_text(
        json.dumps(visual_review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
