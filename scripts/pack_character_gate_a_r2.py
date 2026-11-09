"""Pack hand-authored Gate A R2 pixel matrices without drawing the character."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "art-source" / "character-v2" / "gate-a-r2"
FRAME_SIZE = (64, 96)
RUNTIME_SIZE = (48, 72)
BASELINE_Y = 88
DIRECTIONS = ("down", "left", "right", "up")
STYLES = ("a", "b", "c")
STYLE_NAMES = {
    "a": "叙事长外套",
    "b": "海玻璃学院",
    "c": "潮汐图形",
}
STYLE_BOARD_NAMES = {
    "a": "NARRATIVE LONGLINE",
    "b": "SEAGLASS ACADEMY",
    "c": "TIDAL GRAPHIC",
}


def rgba(value: str) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
        int(value[6:8], 16) if len(value) == 8 else 255,
    )


def load_source(style: str, direction: str) -> tuple[Image.Image, dict]:
    source_root = OUTPUT_ROOT / style / "source"
    palette_data = json.loads(
        (source_root / "palette.json").read_text(encoding="utf-8")
    )
    symbols = palette_data["symbols"]
    lines = (source_root / f"{direction}.txt").read_text(
        encoding="utf-8"
    ).splitlines()
    if len(lines) != 96 or any(len(line) != 64 for line in lines):
        raise ValueError(
            f"{style}/{direction} pixel matrix must be exactly 64x96"
        )

    image = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(lines):
        for x, symbol in enumerate(row):
            if symbol == ".":
                continue
            if symbol not in symbols:
                raise ValueError(
                    f"unknown palette symbol {symbol!r} in "
                    f"{style}/{direction}"
                )
            pixels[x, y] = rgba(symbols[symbol])
    return image, palette_data


def indexed_copy(image: Image.Image, palette_data: dict) -> Image.Image:
    rgba_colors = [
        rgba(value)
        for symbol, value in palette_data["symbols"].items()
        if symbol != "."
    ]
    colors = [(0, 0, 0, 0), *rgba_colors]
    color_index = {value: index for index, value in enumerate(colors)}
    indexed = Image.new("P", image.size, 0)
    indexed_pixels = indexed.load()
    for y in range(image.height):
        for x in range(image.width):
            source = image.getpixel((x, y))
            if source[3] == 0:
                indexed_pixels[x, y] = 0
            else:
                indexed_pixels[x, y] = color_index[source]
    palette_bytes = []
    for red, green, blue, _ in colors:
        palette_bytes.extend((red, green, blue))
    indexed.putpalette(palette_bytes)
    indexed.info["transparency"] = 0
    return indexed


def palette_image(sheet: Image.Image) -> Image.Image:
    colors = sorted(
        {
            pixel
            for pixel in sheet.get_flattened_data()
            if pixel[3] == 255
        },
        key=lambda value: tuple(value[:3]),
    )
    columns = 7
    rows = max(1, (len(colors) + columns - 1) // columns)
    canvas = Image.new("RGB", (700, 26 + rows * 80), "#081514")
    draw = ImageDraw.Draw(canvas)
    font = _font(14)
    for index, color in enumerate(colors):
        x = 12 + (index % columns) * 98
        y = 10 + (index // columns) * 80
        value = "#{:02X}{:02X}{:02X}".format(*color[:3])
        draw.rectangle(
            (x, y, x + 74, y + 40),
            fill=value,
            outline="#E7DDAA",
        )
        draw.text((x, y + 47), value, fill="#F5EAB8", font=font)
    return canvas


def silhouette(sheet: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", sheet.size, "#F7F4E9")
    black = Image.new("RGB", sheet.size, "#081118")
    mask = sheet.getchannel("A")
    canvas.paste(black, (0, 0), mask)
    return canvas


def metrics(style: str, sheet: Image.Image, palette_data: dict) -> dict:
    pixels = list(sheet.get_flattened_data())
    colors = sorted({pixel for pixel in pixels})
    alpha_values = sorted({pixel[3] for pixel in pixels})
    names = palette_data["names"]
    shadow_symbol = next(
        symbol for symbol, name in names.items() if name == "shadow"
    )
    shadow = rgba(palette_data["symbols"][shadow_symbol])
    frame_data = []
    for index, direction in enumerate(DIRECTIONS):
        frame = sheet.crop(
            (index * 64, 0, (index + 1) * 64, FRAME_SIZE[1])
        )
        body_points = [
            (pixel_index % 64, pixel_index // 64)
            for pixel_index, pixel in enumerate(frame.get_flattened_data())
            if pixel[3] == 255 and pixel != shadow
        ]
        character_bbox = [
            min(point[0] for point in body_points),
            min(point[1] for point in body_points),
            max(point[0] for point in body_points) + 1,
            max(point[1] for point in body_points) + 1,
        ]
        frame_data.append(
            {
                "direction": direction,
                "sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
                "bbox": list(frame.getbbox() or (0, 0, 0, 0)),
                "character_bbox": character_bbox,
                "character_height": (
                    character_bbox[3] - character_bbox[1]
                ),
                "character_width": (
                    character_bbox[2] - character_bbox[0]
                ),
                "opaque_pixels": sum(
                    pixel[3] == 255
                    for pixel in frame.get_flattened_data()
                ),
            }
        )
    return {
        "style": style,
        "name": STYLE_NAMES[style],
        "creation_route": "manual-pixel-matrix",
        "source_matrix": {
            direction: (
                f"art-source/character-v2/gate-a-r2/{style}/source/"
                f"{direction}.txt"
            )
            for direction in DIRECTIONS
        },
        "sheet_size": list(sheet.size),
        "frame_size": list(FRAME_SIZE),
        "runtime_size": list(RUNTIME_SIZE),
        "colors": len(colors),
        "opaque_colors": len(
            [color for color in colors if color[3] == 255]
        ),
        "alpha_values": alpha_values,
        "directions": list(DIRECTIONS),
        "baseline_y": BASELINE_Y,
        "bbox": list(sheet.getbbox() or (0, 0, 0, 0)),
        "semi_transparent_pixels": sum(
            0 < pixel[3] < 255 for pixel in pixels
        ),
        "anti_aliased_pixels": sum(
            0 < pixel[3] < 255 for pixel in pixels
        ),
        "frames": frame_data,
    }


def reference_board(
    style: str,
    sheet: Image.Image,
    palette_data: dict,
) -> Image.Image:
    canvas = Image.new("RGBA", (1024, 1024), rgba("#071720ff"))
    draw = ImageDraw.Draw(canvas)
    title_font = _font(32)
    label_font = _font(18)
    small_font = _font(14)

    draw.rectangle((0, 0, 1024, 112), fill=rgba("#0B2B3Aff"))
    draw.rectangle((0, 108, 1024, 112), fill=rgba("#49C9C5ff"))
    draw.text(
        (52, 30),
        f"LIN CHENG / {style.upper()}",
        fill=rgba("#F2FFFCff"),
        font=title_font,
    )
    draw.text(
        (54, 72),
        f"{STYLE_BOARD_NAMES[style]} / 64x96 HAND-AUTHORED PIXELS",
        fill=rgba("#91C8C7ff"),
        font=label_font,
    )

    front = sheet.crop((0, 0, 64, 96))
    main = front.resize((448, 672), Image.Resampling.NEAREST)
    canvas.alpha_composite(main, (66, 156))
    draw.rectangle((56, 142, 532, 846), outline=rgba("#2C7685ff"), width=2)
    draw.text(
        (68, 854),
        "DOWN / NARRATIVE SILHOUETTE",
        fill=rgba("#D8FFF8ff"),
        font=small_font,
    )

    positions = {
        "left": (590, 156),
        "right": (786, 156),
        "up": (590, 470),
    }
    for name, (x, y) in positions.items():
        direction_index = DIRECTIONS.index(name)
        image = sheet.crop(
            (
                direction_index * 64,
                0,
                (direction_index + 1) * 64,
                96,
            )
        )
        image = image.resize((192, 288), Image.Resampling.NEAREST)
        canvas.alpha_composite(image, (x, y))
        draw.rectangle(
            (x - 6, y - 6, x + 198, y + 294),
            outline=rgba("#2C7685ff"),
            width=2,
        )
        draw.text(
            (x, y + 302),
            name.upper(),
            fill=rgba("#D8FFF8ff"),
            font=small_font,
        )

    swatches = palette_image(sheet)
    swatches.thumbnail((392, 180), Image.Resampling.NEAREST)
    canvas.alpha_composite(swatches.convert("RGBA"), (590, 810))
    draw.text(
        (590, 786),
        "USED PALETTE",
        fill=rgba("#D8FFF8ff"),
        font=small_font,
    )
    draw.text(
        (66, 912),
        "MANUAL PIXEL MATRIX / NO GENERATED ILLUSTRATION",
        fill=rgba("#86B5B5ff"),
        font=small_font,
    )
    return canvas.convert("RGB")


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    for style in STYLES:
        style_root = OUTPUT_ROOT / style
        source_root = style_root / "source"
        frames = []
        palette_data = None
        for direction in DIRECTIONS:
            frame, palette_data = load_source(style, direction)
            indexed_copy(frame, palette_data).save(
                source_root / f"{direction}.png",
                optimize=True,
            )
            frame.save(source_root / f"{direction}-rgba.png", optimize=True)
            frames.append(frame)

        sheet = Image.new("RGBA", (64 * 4, 96), (0, 0, 0, 0))
        for index, frame in enumerate(frames):
            sheet.alpha_composite(frame, (index * 64, 0))
        sheet.save(style_root / "sprite-4dir.png", optimize=True)
        frames[0].save(style_root / "sprite-down-1x.png", optimize=True)
        frames[0].resize((256, 384), Image.Resampling.NEAREST).save(
            style_root / "sprite-preview-4x.png",
            optimize=True,
        )

        silhouette_sheet = silhouette(sheet)
        silhouette_sheet.save(
            style_root / "silhouette-4dir.png",
            optimize=True,
        )
        for index, direction in enumerate(DIRECTIONS):
            frame = silhouette_sheet.crop(
                (index * 64, 0, (index + 1) * 64, 96)
            )
            frame.save(
                style_root / f"silhouette-{direction}.png",
                optimize=True,
            )

        palette_image(sheet).save(
            style_root / "palette.png",
            optimize=True,
        )
        reference_board(style, sheet, palette_data).save(
            style_root / "hero-reference.png",
            optimize=True,
        )
        (style_root / "metrics.json").write_text(
            json.dumps(
                metrics(style, sheet, palette_data),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
