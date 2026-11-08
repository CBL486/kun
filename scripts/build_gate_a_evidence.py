"""Build deterministic Gate A contact sheets and asset metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art-source" / "character-v2" / "candidates" / "gate-a"
OUTPUT = ROOT / "docs" / "character-art-v2"
MAP_REFERENCE = ROOT / "docs" / "screenshots" / "r2-idle-desktop.png"

DIRECTIONS = {
    "a": {
        "name": "深海童话装饰系",
        "files": ["a-thumb-01.png", "a-thumb-02.png", "a-hero.png"],
        "palette": [
            "#07182D",
            "#0D2C4A",
            "#174B73",
            "#267E9E",
            "#54D0D5",
            "#A7F4E8",
            "#EEFBF7",
            "#F0C7B8",
            "#D0AE65",
        ],
    },
    "b": {
        "name": "海玻璃学院轻量像素",
        "files": ["b-thumb-01.png", "b-thumb-02.png", "b-hero.png"],
        "palette": [
            "#071B2E",
            "#0A314B",
            "#155A72",
            "#2C8C9C",
            "#69D3D1",
            "#B9F2E7",
            "#F6FFFC",
            "#F2CDBD",
            "#D8AA65",
        ],
    },
    "c": {
        "name": "潮汐复古海报像素",
        "files": ["c-thumb-01.png", "c-thumb-02.png", "c-hero.png"],
        "palette": [
            "#050915",
            "#0A1832",
            "#133B61",
            "#1C7186",
            "#45CAD0",
            "#C8FFF5",
            "#F2C5B6",
            "#C79D57",
        ],
    },
}


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    )
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_label(image: Image.Image, text: str, *, height: int = 42) -> Image.Image:
    canvas = Image.new("RGB", (image.width, image.height + height), "#071312")
    canvas.paste(image.convert("RGB"), (0, height))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 8), text, fill="#F4E7B3", font=font(20))
    return canvas


def describe(direction: str) -> list[dict]:
    entries = []
    for filename in DIRECTIONS[direction]["files"]:
        path = SOURCE / filename
        with Image.open(path) as image:
            entries.append(
                {
                    "file": path.relative_to(ROOT).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "size": list(image.size),
                    "mode": image.mode,
                    "has_aigc_metadata": any(
                        "TC260:AIGC" in str(value)
                        for value in image.info.values()
                    ),
                }
            )
    return entries


def direction_sheet(direction: str) -> None:
    info = DIRECTIONS[direction]
    cells = []
    for filename, title in zip(
        info["files"],
        ("方向缩略图 1", "方向缩略图 2", "主视觉小样"),
    ):
        with Image.open(SOURCE / filename) as image:
            preview = image.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
        cells.append(draw_label(preview, f"{info['name']} · {title}"))
    sheet = Image.new("RGB", (sum(cell.width for cell in cells), cells[0].height), "#071312")
    x = 0
    for cell in cells:
        sheet.paste(cell, (x, 0))
        x += cell.width
    sheet.save(OUTPUT / f"gate-a-{direction}-direction.png", optimize=True)


def combined_sheet() -> None:
    rows = []
    for direction in ("a", "b", "c"):
        info = DIRECTIONS[direction]
        cells = []
        for filename, title in zip(
            info["files"],
            ("缩略图 1", "缩略图 2", "主视觉小样"),
        ):
            with Image.open(SOURCE / filename) as image:
                preview = image.convert("RGB").resize(
                    (480, 480),
                    Image.Resampling.LANCZOS,
                )
            cells.append(draw_label(preview, f"{info['name']} · {title}", height=36))
        row = Image.new("RGB", (sum(cell.width for cell in cells), cells[0].height), "#071312")
        x = 0
        for cell in cells:
            row.paste(cell, (x, 0))
            x += cell.width
        rows.append(row)
    sheet = Image.new("RGB", (rows[0].width, sum(row.height for row in rows)), "#071312")
    y = 0
    for row in rows:
        sheet.paste(row, (0, y))
        y += row.height
    sheet.save(OUTPUT / "gate-a-contact-sheet.png", optimize=True)


def map_comparison() -> None:
    with Image.open(MAP_REFERENCE) as image:
        map_image = image.convert("RGB")
        map_image.thumbnail((1200, 720), Image.Resampling.LANCZOS)
    heroes = []
    for direction in ("a", "b", "c"):
        info = DIRECTIONS[direction]
        with Image.open(SOURCE / info["files"][2]) as image:
            preview = image.convert("RGB").resize((320, 320), Image.Resampling.LANCZOS)
        heroes.append(draw_label(preview, info["name"], height=36))
    canvas = Image.new("RGB", (1200, map_image.height + heroes[0].height + 60), "#071312")
    canvas.paste(map_image, ((1200 - map_image.width) // 2, 20))
    y = map_image.height + 40
    x = 120
    for hero in heroes:
        canvas.paste(hero, (x, y))
        x += hero.width
    canvas.save(OUTPUT / "gate-a-map-comparison.png", optimize=True)


def palette_sheet() -> None:
    row_height = 126
    label_width = 260
    swatch_size = 84
    canvas = Image.new(
        "RGB",
        (label_width + 9 * swatch_size + 18, row_height * 3),
        "#071312",
    )
    draw = ImageDraw.Draw(canvas)
    for row, direction in enumerate(("a", "b", "c")):
        info = DIRECTIONS[direction]
        y = row * row_height
        draw.text(
            (18, y + 42),
            info["name"],
            fill="#F4E7B3",
            font=font(22),
        )
        for index, color in enumerate(info["palette"]):
            x = label_width + index * swatch_size
            draw.rectangle(
                (x + 4, y + 16, x + swatch_size - 4, y + 100),
                fill=color,
                outline="#E8DEAE",
                width=1,
            )
    canvas.save(OUTPUT / "gate-a-palettes.png", optimize=True)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for direction in DIRECTIONS:
        direction_sheet(direction)
    combined_sheet()
    map_comparison()
    palette_sheet()
    payload = {
        "schema_version": "aiworld-character-gate-a-evidence-v1",
        "directions": {
            direction: {
                "name": info["name"],
                "palette": info["palette"],
                "assets": describe(direction),
            }
            for direction, info in DIRECTIONS.items()
        },
        "contact_sheet": "docs/character-art-v2/gate-a-contact-sheet.png",
        "map_comparison": "docs/character-art-v2/gate-a-map-comparison.png",
        "palette_sheet": "docs/character-art-v2/gate-a-palettes.png",
    }
    (OUTPUT / "gate-a-assets.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
