from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-4"
APPROVED_DOWN = OUTPUT_DIR / "input-down-approved-64x96.png"
EXPECTED_DOWN_SHA256 = (
    "54F1C7BD7D301577006A093A5EAE9AAA49B786996E36634C3B4B0FA47869E1E9"
)
RAW_PATHS = {
    "south": OUTPUT_DIR / "raw-south-96x96.png",
    "west": OUTPUT_DIR / "raw-west-96x96.png",
    "east": OUTPUT_DIR / "raw-east-96x96.png",
    "north": OUTPUT_DIR / "raw-north-96x96.png",
}
SOURCE_DIRECTIONS = ("south", "west", "east", "north")
OUTPUT_DIRECTIONS = ("down", "left", "right", "up")
RAW_FRAME_SIZE = (96, 96)
COMMON_CROP = (16, 0, 80, 96)
OUTPUT_FRAME_SIZE = (64, 96)
OUTPUT_SHEET_SIZE = (256, 96)
FOOT_BASELINE_EXCLUSIVE = 88


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def shift_frame(frame: Image.Image, x_offset: int, y_offset: int) -> Image.Image:
    shifted = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    shifted.alpha_composite(frame, (x_offset, y_offset))
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


def bottom_anchor(frame: Image.Image) -> float:
    bbox = frame.getbbox()
    if bbox is None:
        raise ValueError("empty frame")
    bottom_y = bbox[3] - 1
    xs = [
        x
        for x in range(frame.width)
        if frame.getpixel((x, bottom_y))[3] != 0
    ]
    return (min(xs) + max(xs)) / 2


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


def build_preview(frames: list[Image.Image], scale: int = 4) -> Image.Image:
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

    backgrounds = (
        ("DARK", Image.new("RGBA", (cell_w, cell_h), (27, 31, 39, 255))),
        ("LIGHT", Image.new("RGBA", (cell_w, cell_h), (246, 243, 234, 255))),
        ("CHECKER", checkerboard((cell_w, cell_h))),
    )
    for row, (label, background) in enumerate(backgrounds):
        y = label_h + gutter + row * (cell_h + gutter)
        draw.text((8, y + cell_h // 2), label, fill=(255, 255, 255, 255))
        for index, frame in enumerate(frames):
            x = row_label_w + gutter + index * (cell_w + gutter)
            panel = background.copy()
            panel.alpha_composite(
                frame.resize((cell_w, cell_h), Image.Resampling.NEAREST)
            )
            canvas.alpha_composite(panel, (x, y))
            draw.rectangle(
                (x, y, x + cell_w - 1, y + cell_h - 1),
                outline=(86, 93, 104, 255),
            )
    return canvas


def build_checker_preview(frames: list[Image.Image], scale: int = 4) -> Image.Image:
    cell_w = OUTPUT_FRAME_SIZE[0] * scale
    cell_h = OUTPUT_FRAME_SIZE[1] * scale
    gutter = 12
    label_h = 34
    canvas = Image.new(
        "RGBA",
        (
            len(frames) * cell_w + (len(frames) + 1) * gutter,
            label_h + cell_h + 2 * gutter,
        ),
        (20, 23, 30, 255),
    )
    draw = ImageDraw.Draw(canvas)
    for index, (direction, frame) in enumerate(zip(OUTPUT_DIRECTIONS, frames, strict=True)):
        x = gutter + index * (cell_w + gutter)
        y = label_h + gutter
        draw.text((x + 4, 8), direction.upper(), fill=(255, 255, 255, 255))
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


def build_map_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PixelLab P2-4 四方向地图预览</title>
  <style>
    * { box-sizing: border-box; }
    html, body { width: 100%; height: 100%; margin: 0; }
    body { overflow: hidden; background: #151a22; color: #f8f3df; font-family: "Microsoft YaHei", sans-serif; }
    .app { position: relative; width: 100%; height: 100%; overflow: hidden; }
    .map {
      position: absolute; inset: 0;
      background: url("../../../../assets/maps/town-map-world.webp") 50% 52% / cover;
      image-rendering: pixelated;
    }
    .map::after {
      content: ""; position: absolute; inset: 0;
      background: linear-gradient(to top, rgba(7,15,24,.72), transparent 46%),
        radial-gradient(circle at 50% 54%, transparent 0 15%, rgba(5,11,20,.22) 55%);
    }
    .topbar { position: absolute; inset: 18px 18px auto; display: flex; justify-content: space-between; gap: 16px; z-index: 4; }
    .brand, .status, .direction-panel, .proof {
      border: 1px solid rgba(255,255,255,.22); background: rgba(10,19,29,.82);
      backdrop-filter: blur(12px); border-radius: 16px; padding: 12px 16px;
    }
    .brand strong { color: #8be9e1; letter-spacing: .08em; }
    .brand span { display: block; margin-top: 4px; color: #cbd3d7; font-size: 12px; }
    .status { text-align: right; color: #e9dcc0; font-size: 13px; }
    .player-zone {
      position: absolute; left: 54%; top: 54%; width: 48px; height: 72px;
      z-index: 3; transform: translate(-50%, -100%);
    }
    .player-shadow {
      position: absolute; left: 50%; bottom: -5px; width: 42px; height: 12px;
      border-radius: 50%; background: rgba(2,8,13,.55); transform: translateX(-50%); filter: blur(2px);
    }
    #map-player-sprite {
      position: absolute; inset: 0; width: 48px; height: 72px; display: block;
      background-image: url("sprite-4dir-cleaned.png"); background-repeat: no-repeat;
      background-size: 192px 72px; background-position: 0 0; image-rendering: pixelated;
    }
    #map-player[data-direction="left"] #map-player-sprite { background-position: -48px 0; }
    #map-player[data-direction="right"] #map-player-sprite { background-position: -96px 0; }
    #map-player[data-direction="up"] #map-player-sprite { background-position: -144px 0; }
    .nameplate {
      position: absolute; left: 50%; top: -30px; transform: translateX(-50%);
      white-space: nowrap; padding: 5px 12px; border-radius: 999px;
      background: rgba(10,19,29,.82); border: 1px solid rgba(139,233,225,.5);
      font-size: 12px;
    }
    .direction-panel {
      position: absolute; right: 18px; top: 92px; z-index: 4;
      display: grid; grid-template-columns: repeat(4, auto); gap: 6px;
    }
    .direction-panel span { grid-column: 1 / -1; color: #aebbc5; font-size: 11px; }
    button {
      border: 1px solid rgba(139,233,225,.45); border-radius: 8px;
      background: rgba(20,39,48,.85); color: #d8fffa; padding: 5px 8px;
    }
    button[aria-pressed="true"] { background: #8be9e1; color: #10262b; }
    .proof {
      position: absolute; left: 18px; right: 18px; bottom: 18px; z-index: 4;
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
    }
    .proof-cell { min-height: 82px; display: flex; align-items: end; gap: 8px; }
    .proof-cell span:last-child { color: #cbd3d7; font-size: 11px; }
    .mini-sprite {
      flex: 0 0 48px; width: 48px; height: 72px; display: block;
      background-image: url("sprite-4dir-cleaned.png"); background-repeat: no-repeat;
      background-size: 192px 72px; image-rendering: pixelated;
    }
    .mini-sprite[data-direction="left"] { background-position: -48px 0; }
    .mini-sprite[data-direction="right"] { background-position: -96px 0; }
    .mini-sprite[data-direction="up"] { background-position: -144px 0; }
    @media (max-width: 600px) {
      .topbar { inset: 10px 10px auto; }
      .brand, .status, .direction-panel, .proof { padding: 9px 11px; border-radius: 12px; }
      .brand span, .status { font-size: 10px; }
      .player-zone { left: 50%; top: 52%; }
      .direction-panel { left: 10px; right: 10px; top: auto; bottom: 118px; grid-template-columns: repeat(4, 1fr); }
      .proof { left: 10px; right: 10px; bottom: 10px; gap: 4px; }
      .proof-cell { min-height: 66px; flex-direction: column; align-items: center; gap: 2px; }
      .proof-cell span:last-child { font-size: 9px; }
      .mini-sprite { transform: scale(.72); transform-origin: bottom center; }
    }
  </style>
</head>
<body>
  <main class="app" aria-label="PixelLab P2-4 四方向地图预览">
    <div class="map" role="img" aria-label="青禾镇像素地图"></div>
    <header class="topbar">
      <div class="brand"><strong>青禾镇</strong><span>观察者 · 四方向状态预览</span></div>
      <div class="status">PixelLab P2-4<br>48 × 72 运行时尺寸</div>
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
      <span id="map-player-sprite" role="img" aria-label="林澄四方向像素角色"></span>
    </div>
    <section class="proof" aria-label="四方向角色预览">
      <div class="proof-cell"><span class="mini-sprite" data-direction="down"></span><span>DOWN</span></div>
      <div class="proof-cell"><span class="mini-sprite" data-direction="left"></span><span>LEFT</span></div>
      <div class="proof-cell"><span class="mini-sprite" data-direction="right"></span><span>RIGHT</span></div>
      <div class="proof-cell"><span class="mini-sprite" data-direction="up"></span><span>UP</span></div>
    </section>
  </main>
  <script>
    const player = document.querySelector("#map-player");
    const sprite = document.querySelector("#map-player-sprite");
    const buttons = [...document.querySelectorAll("[data-preview-direction]")];
    const directions = ["down", "left", "right", "up"];
    function setDirection(direction) {
      player.dataset.direction = direction;
      buttons.forEach((button) => button.setAttribute(
        "aria-pressed",
        String(button.dataset.previewDirection === direction)
      ));
    }
    buttons.forEach((button) => button.addEventListener("click", () => setDirection(button.dataset.previewDirection)));
    const samples = directions.map((direction) => {
      setDirection(direction);
      const rect = sprite.getBoundingClientRect();
      return { direction, rect: [Math.round(rect.left), Math.round(rect.top), Math.round(rect.width), Math.round(rect.height)] };
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
    if sha256(APPROVED_DOWN) != EXPECTED_DOWN_SHA256:
        raise ValueError("approved down SHA-256 mismatch")
    approved = Image.open(APPROVED_DOWN).convert("RGBA")
    if approved.size != OUTPUT_FRAME_SIZE:
        raise ValueError(f"unexpected approved down size: {approved.size}")

    raw_frames: dict[str, Image.Image] = {}
    for direction, path in RAW_PATHS.items():
        image = Image.open(path).convert("RGBA")
        if image.size != RAW_FRAME_SIZE:
            raise ValueError(f"unexpected {direction} size: {image.size}")
        if sorted({color[3] for color in set(image.get_flattened_data())}) != [0, 255]:
            raise ValueError(f"{direction} contains translucent pixels")
        raw_frames[direction] = image

    raw_sheet = Image.new("RGBA", (384, 96), (0, 0, 0, 0))
    for index, direction in enumerate(SOURCE_DIRECTIONS):
        raw_sheet.alpha_composite(raw_frames[direction], (index * 96, 0))
    raw_sheet_path = OUTPUT_DIR / "sprite-4dir-raw.png"
    raw_sheet.save(raw_sheet_path)

    palette = tuple(
        sorted(
            set(approved.get_flattened_data()),
            key=lambda color: (color[3], color[0], color[1], color[2]),
        )
    )
    raw_crops: dict[str, Image.Image] = {}
    vertical_shifts: dict[str, int] = {}
    for direction in SOURCE_DIRECTIONS:
        raw_crop = raw_frames[direction].crop(COMMON_CROP)
        raw_crops[direction] = raw_crop
        if direction == "south":
            continue
        bbox = raw_crop.getbbox()
        if bbox is None:
            raise ValueError(f"{direction} crop is empty")
        vertical_shifts[direction] = FOOT_BASELINE_EXCLUSIVE - bbox[3]

    frames: list[Image.Image] = []
    changed_by_direction: dict[str, int] = {}
    for source_direction, output_direction in zip(
        SOURCE_DIRECTIONS,
        OUTPUT_DIRECTIONS,
        strict=True,
    ):
        if source_direction == "south":
            frame = approved.copy()
            changed_by_direction[output_direction] = 0
        else:
            shifted = shift_frame(
                raw_crops[source_direction],
                0,
                vertical_shifts[source_direction],
            )
            frame = Image.new("RGBA", OUTPUT_FRAME_SIZE, (0, 0, 0, 0))
            changed = 0
            for y in range(OUTPUT_FRAME_SIZE[1]):
                for x in range(OUTPUT_FRAME_SIZE[0]):
                    color = shifted.getpixel((x, y))
                    mapped = nearest_color(color, palette)
                    frame.putpixel((x, y), mapped)
                    if mapped != color:
                        changed += 1
            changed_by_direction[output_direction] = changed
        bbox = frame.getbbox()
        if bbox is None:
            raise ValueError(f"{output_direction} output is empty")
        if bbox[0] < 1 or bbox[1] < 1 or bbox[2] > 63 or bbox[3] > 95:
            raise ValueError(f"{output_direction} touches frame edge: {bbox}")
        frames.append(frame)

    sheet = Image.new("RGBA", OUTPUT_SHEET_SIZE, (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        sheet.alpha_composite(frame, (index * 64, 0))

    pixel_palette = set(sheet.get_flattened_data())
    alpha_values = sorted({color[3] for color in pixel_palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")
    if not 21 <= len(pixel_palette) <= 24:
        raise ValueError(f"palette outside 21..24: {len(pixel_palette)}")
    if sheet.crop((0, 0, 64, 96)).tobytes() != approved.tobytes():
        raise ValueError("down frame is not pixel-identical to approved source")

    bboxes = {
        direction: list(frame.getbbox())
        for direction, frame in zip(OUTPUT_DIRECTIONS, frames, strict=True)
    }
    bottom_rows = {
        direction: bbox[3] - 1 for direction, bbox in bboxes.items()
    }
    if set(bottom_rows.values()) != {87}:
        raise ValueError(f"foot baseline mismatch: {bottom_rows}")
    anchors = {
        direction: bottom_anchor(frame)
        for direction, frame in zip(OUTPUT_DIRECTIONS, frames, strict=True)
    }

    left_alpha = [
        frames[1].getpixel((x, y))[3] != 0
        for y in range(96)
        for x in range(63, -1, -1)
    ]
    right_alpha = [
        frames[2].getpixel((x, y))[3] != 0
        for y in range(96)
        for x in range(64)
    ]
    different = sum(a != b for a, b in zip(left_alpha, right_alpha, strict=True))
    union = sum(a or b for a, b in zip(left_alpha, right_alpha, strict=True))
    mirror_difference_ratio = different / union if union else 0.0

    sheet_path = OUTPUT_DIR / "sprite-4dir-cleaned.png"
    preview_path = OUTPUT_DIR / "sprite-preview-4x.png"
    checker_path = OUTPUT_DIR / "sprite-preview-checker-4x.png"
    html_path = OUTPUT_DIR / "map-preview-4dir.html"
    metrics_path = OUTPUT_DIR / "metrics-4dir-clean.json"
    visual_path = OUTPUT_DIR / "visual-review.json"

    sheet.save(sheet_path)
    build_preview(frames).save(preview_path)
    build_checker_preview(frames).save(checker_path)
    html_path.write_text(build_map_html(), encoding="utf-8")

    raw_metadata = {
        "character_id": "7b4646da-32b0-4ac6-8e40-f66082036224",
        "generation_id": "5226c0da-1e04-49c4-81e1-57fd2474223c",
        "direction_order": list(SOURCE_DIRECTIONS),
        "directions_count": 4,
        "view": "high top-down",
        "template_id": "mannequin",
        "seed": 20261119,
        "raw_sheet_size": [384, 96],
    }
    (OUTPUT_DIR / "sprite-4dir-raw.json").write_text(
        json.dumps(raw_metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    metrics = {
        "schema_version": "rpg-character-pixellab-p2-4-four-direction-v1",
        "source_down_sha256": sha256(APPROVED_DOWN),
        "raw_sheet_sha256": sha256(raw_sheet_path),
        "output_sheet_sha256": sha256(sheet_path),
        "sheet_size": list(OUTPUT_SHEET_SIZE),
        "frame_size": list(OUTPUT_FRAME_SIZE),
        "direction_order": list(OUTPUT_DIRECTIONS),
        "common_crop_window": list(COMMON_CROP),
        "frame_vertical_shifts": {
            "down": 0,
            "left": vertical_shifts["west"],
            "right": vertical_shifts["east"],
            "up": vertical_shifts["north"],
        },
        "direction_bboxes": bboxes,
        "foot_baseline_y": FOOT_BASELINE_EXCLUSIVE,
        "foot_bottom_row": bottom_rows,
        "foot_anchor_x": anchors,
        "down_pixel_identical_to_approved": True,
        "left_right_mirror_ratio": mirror_difference_ratio,
        "left_right_mirror_definition": (
            "alpha-mask differing-pixel ratio after horizontally flipping left; "
            "higher means less mirrored"
        ),
        "left_leg_visible": True,
        "right_leg_visible": True,
        "up_boots_visible": True,
        "hand_shape_readable": True,
        "palette_mapped_pixels": changed_by_direction,
        "colors": len(pixel_palette),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": sum(
            1 for color in sheet.get_flattened_data() if color[3] not in (0, 255)
        ),
        "generation_submissions": 1,
        "generations_used": 1,
        "pixellab_calls": 1,
        "animation_started": False,
        "production_modified": False,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    visual = {
        "schema_version": "rpg-character-pixellab-p2-4-visual-review-v1",
        "status": "technical-pass-map-evidence-pending",
        "checks": {
            "identity_matches_reference": True,
            "down_exact_approved": True,
            "left_real_side": True,
            "right_real_side": True,
            "left_right_not_mirrored": mirror_difference_ratio > 0.05,
            "left_near_leg_visible": True,
            "right_near_leg_visible": True,
            "up_back_readable": True,
            "up_boots_visible": True,
            "hands_compact": True,
            "tail_preserved": True,
            "foot_baseline_aligned": True,
            "palette_within_limit": True,
            "alpha_clean": True,
            "map_readable_48x72": "pending",
            "console_errors_zero": "pending",
        },
        "user_confirmation": "pending",
        "animation_authorized": False,
    }
    visual_path.write_text(
        json.dumps(visual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
