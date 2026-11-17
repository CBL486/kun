from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P3-0R"
IDLE_SHEET = OUTPUT_DIR / "idle-4dir-4f.png"
EXPECTED_SHA256 = (
    "656A0414BDAE81EB52CB546441AA67039CB96AB947BD4A5300420E3D9A9B5B69"
)
FRAME_SIZE = (64, 96)
DIRECTIONS = ("down", "left", "right", "up")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


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


def load_frames(sheet: Image.Image) -> dict[str, list[Image.Image]]:
    return {
        direction: [
            sheet.crop(
                (
                    frame * 64,
                    direction_index * 96,
                    (frame + 1) * 64,
                    (direction_index + 1) * 96,
                )
            )
            for frame in range(4)
        ]
        for direction_index, direction in enumerate(DIRECTIONS)
    }


def direction_strip(
    frames: dict[str, list[Image.Image]],
    frame_index: int,
    checker: bool = False,
) -> Image.Image:
    image = (
        checkerboard((256, 96))
        if checker
        else Image.new("RGBA", (256, 96), (0, 0, 0, 0))
    )
    for direction_index, direction in enumerate(DIRECTIONS):
        image.alpha_composite(
            frames[direction][frame_index],
            (direction_index * 64, 0),
        )
    return image.resize((1024, 384), Image.Resampling.NEAREST)


def save_animated_webp(
    frames: list[Image.Image],
    path: Path,
) -> None:
    frames[0].save(
        path,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=200,
        loop=0,
        lossless=True,
        method=6,
        background=(0, 0, 0, 0),
    )


def gif_palette_frame(frame: Image.Image) -> Image.Image:
    rgba = frame.convert("RGBA")
    # The checker background is intentionally visible in the GIF; reserve the
    # last palette index as transparent so every frame has deterministic
    # disposal semantics.
    quantized = rgba.convert("RGB").quantize(
        colors=255,
        method=Image.Quantize.MEDIANCUT,
    )
    palette = quantized.getpalette()[: 256 * 3]
    palette[255 * 3 : 255 * 3 + 3] = [0, 0, 0]
    quantized.putpalette(palette)
    return quantized


def contact_section(
    frames: dict[str, list[Image.Image]],
    background_name: str,
    scale: int = 2,
) -> Image.Image:
    cell_w = 64 * scale
    cell_h = 96 * scale
    gutter = 8
    margin = 16
    header = 28
    row_label_w = 68
    width = row_label_w + 4 * cell_w + 5 * gutter
    height = header + 4 * cell_h + 5 * gutter + 26
    canvas = Image.new("RGBA", (width, height), (22, 26, 34, 255))
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 8), background_name, fill=(255, 255, 255, 255))
    for column in range(4):
        draw.text(
            (
                row_label_w + gutter + column * (cell_w + gutter) + 4,
                8,
            ),
            f"FRAME {column}",
            fill=(210, 220, 228, 255),
        )
    for row, direction in enumerate(DIRECTIONS):
        y = header + gutter + row * (cell_h + gutter)
        draw.text((margin, y + cell_h // 2), direction.upper(), fill=(255, 255, 255, 255))
        for column, frame in enumerate(frames[direction]):
            x = row_label_w + gutter + column * (cell_w + gutter)
            panel = (
                checkerboard((cell_w, cell_h))
                if background_name == "CHECKER"
                else Image.new(
                    "RGBA",
                    (cell_w, cell_h),
                    (246, 243, 234, 255)
                    if background_name == "LIGHT"
                    else (27, 31, 39, 255),
                )
            )
            panel.alpha_composite(
                frame.resize((cell_w, cell_h), Image.Resampling.NEAREST)
            )
            canvas.alpha_composite(panel, (x, y))
            draw.rectangle(
                (x, y, x + cell_w - 1, y + cell_h - 1),
                outline=(80, 88, 98, 255),
            )
    draw.text(
        (margin, height - 20),
        "5 FPS  ·  0 -> 1 -> 2 -> 3 -> 0",
        fill=(190, 204, 214, 255),
    )
    return canvas


def contact_sheet(frames: dict[str, list[Image.Image]]) -> Image.Image:
    sections = [
        contact_section(frames, "DARK"),
        contact_section(frames, "LIGHT"),
        contact_section(frames, "CHECKER"),
    ]
    gap = 18
    canvas = Image.new(
        "RGBA",
        (
            max(image.width for image in sections),
            sum(image.height for image in sections) + gap * (len(sections) - 1),
        ),
        (16, 19, 25, 255),
    )
    y = 0
    for section in sections:
        canvas.alpha_composite(section, (0, y))
        y += section.height + gap
    return canvas


def build_map_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI World P3-0R 确定性 Idle</title>
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
      background-image: url("idle-4dir-4f.png"); background-repeat: no-repeat;
      background-size: 192px 288px; background-position: 0 0; image-rendering: pixelated;
    }
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
      display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px;
    }
    .proof-cell { display: flex; align-items: end; gap: 6px; min-height: 82px; }
    .proof-cell span:last-child { color: #cbd3d7; font-size: 10px; }
    .mini-sprite {
      flex: 0 0 48px; width: 48px; height: 72px; display: block;
      background-image: url("idle-4dir-4f.png"); background-repeat: no-repeat;
      background-size: 192px 288px; image-rendering: pixelated;
    }
    @media (max-width: 600px) {
      .topbar { inset: 10px 10px auto; }
      .brand, .status, .direction-panel, .proof { padding: 9px 11px; border-radius: 12px; }
      .brand span, .status { font-size: 10px; }
      .player-zone { left: 50%; top: 51%; }
      .direction-panel { left: 10px; right: 10px; top: 86px; bottom: auto; grid-template-columns: repeat(4, 1fr); }
      .proof {
        left: 10px; right: 10px; bottom: 10px; grid-template-columns: repeat(3, 1fr); gap: 4px;
      }
      .proof-cell { min-height: 66px; flex-direction: column; align-items: center; gap: 1px; }
      .proof-cell span:last-child { font-size: 9px; }
      .mini-sprite { transform: scale(.72); transform-origin: bottom center; }
    }
  </style>
</head>
<body>
  <main class="app" aria-label="AI World deterministic idle 四方向地图预览">
    <div class="map" role="img" aria-label="青禾镇像素地图"></div>
    <header class="topbar">
      <div class="brand"><strong>青禾镇</strong><span>观察者 · 确定性 idle 预览</span></div>
      <div class="status">P3-0R<br>5 FPS · 48×72</div>
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
      <span id="map-player-sprite" role="img" aria-label="林澄确定性 idle 四方向角色"></span>
    </div>
    <section class="proof" aria-label="idle 方向与帧证据">
      <div class="proof-cell"><span class="mini-sprite" data-direction="down" data-frame="0"></span><span>DOWN F0</span></div>
      <div class="proof-cell"><span class="mini-sprite" data-direction="down" data-frame="1"></span><span>DOWN F1</span></div>
      <div class="proof-cell"><span class="mini-sprite" data-direction="left" data-frame="1"></span><span>LEFT F1</span></div>
      <div class="proof-cell"><span class="mini-sprite" data-direction="right" data-frame="1"></span><span>RIGHT F1</span></div>
      <div class="proof-cell"><span class="mini-sprite" data-direction="up" data-frame="1"></span><span>UP F1</span></div>
    </section>
  </main>
  <script>
    const directions = ["down", "left", "right", "up"];
    const player = document.querySelector("#map-player");
    const sprite = document.querySelector("#map-player-sprite");
    const buttons = [...document.querySelectorAll("[data-preview-direction]")];
    const miniSprites = [...document.querySelectorAll(".mini-sprite")];
    let currentDirection = "down";
    let currentFrame = 0;
    function positionSprite(element, direction, frame) {
      const row = directions.indexOf(direction);
      element.style.backgroundPosition = `${-48 * frame}px ${-72 * row}px`;
    }
    function setDirection(direction) {
      currentDirection = direction;
      buttons.forEach((button) => button.setAttribute(
        "aria-pressed",
        String(button.dataset.previewDirection === direction)
      ));
      positionSprite(sprite, direction, currentFrame);
    }
    miniSprites.forEach((element) => positionSprite(
      element,
      element.dataset.direction,
      Number(element.dataset.frame)
    ));
    buttons.forEach((button) => button.addEventListener("click", () => setDirection(button.dataset.previewDirection)));
    const params = new URLSearchParams(location.search);
    const selectedDirection = params.get("direction") || "down";
    setDirection(selectedDirection);
    currentFrame = Number(params.get("frame") || 0);
    positionSprite(sprite, currentDirection, currentFrame);
    if (params.get("static") !== "1") {
      window.setInterval(() => {
        currentFrame = (currentFrame + 1) % 4;
        positionSprite(sprite, currentDirection, currentFrame);
      }, 200);
    }
    const samples = directions.map((direction) => {
      setDirection(direction);
      const rect = sprite.getBoundingClientRect();
      return { direction, rect: [Math.round(rect.left), Math.round(rect.top), Math.round(rect.width), Math.round(rect.height)] };
    });
    setDirection(selectedDirection);
    const xs = samples.map((sample) => sample.rect[0]);
    window.__idleEvidence = {
      samples,
      maxHorizontalDelta: Math.max(...xs) - Math.min(...xs),
      playerRect: [samples[0].rect[2], samples[0].rect[3]],
      proofCells: miniSprites.map((element) => ({
        direction: element.dataset.direction,
        frame: Number(element.dataset.frame),
        rect: (() => {
          const rect = element.getBoundingClientRect();
          return [Math.round(rect.left), Math.round(rect.top), Math.round(rect.width), Math.round(rect.height)];
        })(),
      })),
    };
  </script>
</body>
</html>
"""


def main() -> None:
    if sha256(IDLE_SHEET) != EXPECTED_SHA256:
        raise ValueError("P3-0R idle sheet SHA-256 mismatch")
    sheet = Image.open(IDLE_SHEET).convert("RGBA")
    if sheet.size != (256, 384):
        raise ValueError(f"unexpected idle sheet size: {sheet.size}")
    frames = load_frames(sheet)

    webp_frames = [
        direction_strip(frames, frame_index, checker=False)
        for frame_index in range(4)
    ]
    webp_path = OUTPUT_DIR / "idle-preview-4x.webp"
    save_animated_webp(webp_frames, webp_path)

    gif_frames = [
        gif_palette_frame(direction_strip(frames, frame_index, checker=True))
        for frame_index in range(4)
    ]
    gif_path = OUTPUT_DIR / "idle-preview-checker-4x.gif"
    gif_frames[0].save(
        gif_path,
        format="GIF",
        save_all=True,
        append_images=gif_frames[1:],
        duration=200,
        loop=0,
        disposal=2,
        transparency=255,
    )

    contact_path = OUTPUT_DIR / "idle-contact-sheet.png"
    contact_sheet(frames).save(contact_path)
    html_path = OUTPUT_DIR / "map-preview-idle.html"
    html_path.write_text(build_map_html(), encoding="utf-8")

    metrics_path = OUTPUT_DIR / "metrics-idle.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics["preview_webp"] = webp_path.relative_to(ROOT).as_posix()
    metrics["preview_gif"] = gif_path.relative_to(ROOT).as_posix()
    metrics["contact_sheet"] = contact_path.relative_to(ROOT).as_posix()
    metrics["map_preview"] = html_path.relative_to(ROOT).as_posix()
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    visual_path = OUTPUT_DIR / "visual-review.json"
    visual = json.loads(visual_path.read_text(encoding="utf-8"))
    visual["checks"]["animated_webp"] = True
    visual["checks"]["animated_gif"] = True
    visual["checks"]["contact_sheet"] = True
    visual["checks"]["map_capture"] = "pending"
    visual_path.write_text(
        json.dumps(visual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "webp": metrics["preview_webp"],
                "gif": metrics["preview_gif"],
                "contact_sheet": metrics["contact_sheet"],
                "map_preview": metrics["map_preview"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
