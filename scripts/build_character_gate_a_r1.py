"""Author native 64x96 four-direction proofs for character Gate A R1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "art-source" / "character-v2" / "gate-a-r1"
FRAME_SIZE = (64, 96)
RUNTIME_SIZE = (48, 72)
BASELINE_Y = 88
DIRECTIONS = ("down", "left", "right", "up")

STYLES = {
    "a": {
        "name": "深海童话",
        "colors": {
            "outline": "#04131C",
            "hair_dark": "#09243A",
            "hair_mid": "#164D69",
            "hair_light": "#2B899F",
            "hair_tip": "#5BC7C9",
            "fin_dark": "#0B5661",
            "fin_mid": "#32BFC5",
            "fin_light": "#C5FFF5",
            "coat_dark": "#0A263D",
            "coat_mid": "#173F59",
            "coat_light": "#326C80",
            "blouse": "#F0FFFC",
            "dress": "#9BE4E0",
            "skin": "#F1C8B8",
            "skin_shadow": "#D6958B",
            "eye": "#062733",
            "eye_light": "#74EAE4",
            "mouth": "#9C4755",
            "blush": "#E69EA8",
            "gold_dark": "#9B7543",
            "gold": "#D5B56D",
            "shadow": "#112026",
        },
    },
    "b": {
        "name": "海玻璃学院",
        "colors": {
            "outline": "#061722",
            "hair_dark": "#092A41",
            "hair_mid": "#185976",
            "hair_light": "#3B96A8",
            "fin_dark": "#0F6269",
            "fin_mid": "#59D2CD",
            "fin_light": "#D0FFF6",
            "coat_dark": "#0D2F48",
            "coat_mid": "#1A4B64",
            "coat_light": "#3A7C90",
            "blouse": "#F7FFFD",
            "dress": "#AAE9E4",
            "skin": "#F3CEBE",
            "skin_shadow": "#DCA095",
            "eye": "#08313B",
            "eye_light": "#79E8DF",
            "blush": "#E7A2AC",
            "gold": "#D7B66E",
            "shoe": "#0A2638",
            "shadow": "#152329",
        },
    },
    "c": {
        "name": "潮汐海报",
        "colors": {
            "outline": "#020914",
            "hair_dark": "#06182F",
            "hair_mid": "#0F3A5E",
            "hair_light": "#1F7892",
            "hair_edge": "#54D8D5",
            "fin_dark": "#095A6A",
            "fin_mid": "#3ECFCE",
            "fin_light": "#D4FFF8",
            "coat_dark": "#071C34",
            "coat_mid": "#103552",
            "coat_light": "#23677D",
            "blouse": "#F5FFFB",
            "dress": "#8EDDD9",
            "skin": "#F0C8B6",
            "skin_shadow": "#D58F88",
            "eye": "#032633",
            "eye_light": "#72F1E4",
            "blush": "#E39AA7",
            "gold": "#C99D56",
            "shadow": "#101C26",
        },
    },
}


def rgba(value: str) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
        255,
    )


def palette(style: str) -> dict[str, tuple[int, int, int, int]]:
    return {
        name: rgba(value)
        for name, value in STYLES[style]["colors"].items()
    }


def draw_back_hair(
    draw: ImageDraw.ImageDraw,
    style: str,
    direction: str,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    outline = colors["outline"]
    hair = colors["hair_dark"]
    mid = colors["hair_mid"]
    light = colors["hair_light"]
    if style == "b":
        shape = [(19, 25), (21, 18), (31, 16), (43, 19), (47, 25), (46, 51), (42, 61), (33, 58), (24, 62), (18, 51)]
    elif style == "c":
        shape = [(17, 26), (19, 18), (30, 16), (44, 19), (49, 24), (46, 52), (41, 64), (34, 59), (28, 64), (19, 55), (13, 43)]
    else:
        shape = [(17, 27), (20, 18), (31, 16), (43, 19), (48, 27), (46, 52), (41, 63), (34, 59), (27, 64), (18, 54), (14, 43)]
    draw.polygon(shape, fill=outline)
    inset = [(x + (1 if x >= 31 else -1), max(15, y + 2)) for x, y in shape]
    draw.polygon(inset, fill=hair)
    draw.polygon([(22, 25), (25, 18), (33, 15), (41, 20), (37, 28), (31, 24), (27, 31)], fill=mid)
    draw.line((20, 31, 22, 52), fill=light, width=1)
    if direction in {"left", "right"}:
        side = 43 if direction == "left" else 21
        draw.polygon(
            [(side, 27), (side + (5 if direction == "left" else -5), 47), (side, 60), (side + (-3 if direction == "left" else 3), 45)],
            fill=mid,
        )


def draw_legs_and_boots(
    draw: ImageDraw.ImageDraw,
    style: str,
    direction: str,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    outline = colors["outline"]
    skin = colors["skin"]
    shadow = colors["skin_shadow"]
    shoe = colors.get("shoe", colors.get("coat_dark", outline))
    gold = colors.get("gold", colors.get("coat_light", outline))
    if direction in {"left", "right"}:
        draw.rectangle((26, 68, 31, 83), fill=outline)
        draw.rectangle((27, 68, 30, 82), fill=skin)
        draw.rectangle((27, 78, 30, 82), fill=shadow)
        draw.rectangle((35, 68, 40, 83), fill=outline)
        draw.rectangle((36, 68, 39, 82), fill=skin)
        draw.rectangle((36, 78, 39, 82), fill=shadow)
        draw.rectangle((24, 82, 32, 87), fill=outline)
        draw.rectangle((25, 82, 31, 85), fill=shoe)
        draw.rectangle((35, 82, 42, 87), fill=outline)
        draw.rectangle((36, 82, 41, 85), fill=shoe)
    else:
        draw.rectangle((25, 68, 30, 83), fill=outline)
        draw.rectangle((26, 68, 29, 82), fill=skin)
        draw.rectangle((26, 78, 29, 82), fill=shadow)
        draw.rectangle((34, 68, 39, 83), fill=outline)
        draw.rectangle((35, 68, 38, 82), fill=skin)
        draw.rectangle((35, 78, 38, 82), fill=shadow)
        draw.rectangle((23, 82, 31, 87), fill=outline)
        draw.rectangle((24, 82, 30, 85), fill=shoe)
        draw.rectangle((34, 82, 42, 87), fill=outline)
        draw.rectangle((35, 82, 41, 85), fill=shoe)
    if style in {"a", "b"}:
        draw.point((27, 84), fill=gold)
        draw.point((36, 84), fill=gold)


def draw_body_front(
    draw: ImageDraw.ImageDraw,
    style: str,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    outline = colors["outline"]
    coat_dark = colors["coat_dark"]
    coat = colors["coat_mid"]
    coat_light = colors["coat_light"]
    blouse = colors["blouse"]
    dress = colors["dress"]
    skin = colors["skin"]
    gold = colors.get("gold", coat_light)

    draw.rectangle((29, 40, 35, 46), fill=outline)
    draw.rectangle((30, 41, 34, 45), fill=skin)
    draw.polygon([(20, 43), (44, 43), (43, 64), (21, 64)], fill=outline)
    draw.polygon([(22, 44), (42, 44), (40, 62), (24, 62)], fill=coat)
    draw.polygon([(22, 44), (29, 44), (28, 62), (23, 61)], fill=coat_light)
    draw.polygon([(35, 44), (42, 44), (41, 61), (36, 62)], fill=coat_dark)
    draw.polygon([(28, 44), (36, 44), (38, 59), (34, 63), (30, 59)], fill=blouse)
    draw.rectangle((30, 56, 34, 60), fill=dress)
    draw.line((26, 58, 38, 58), fill=outline, width=1)
    draw.rectangle((31, 57, 33, 59), fill=gold)
    draw.polygon([(15, 46), (21, 44), (22, 62), (18, 64), (14, 60)], fill=outline)
    draw.polygon([(16, 47), (20, 46), (20, 60), (17, 61), (15, 59)], fill=coat)
    draw.polygon([(43, 44), (49, 46), (50, 60), (46, 64), (42, 62)], fill=outline)
    draw.polygon([(44, 46), (48, 47), (48, 59), (46, 61), (43, 60)], fill=coat)
    draw.rectangle((17, 60, 20, 63), fill=skin)
    draw.rectangle((46, 60, 49, 63), fill=skin)
    draw.polygon([(19, 62), (45, 62), (42, 73), (22, 73)], fill=outline)
    draw.polygon([(21, 63), (43, 63), (40, 71), (24, 71)], fill=dress)
    draw.line((26, 65, 27, 71), fill=blouse, width=1)
    draw.line((32, 65, 32, 71), fill=blouse, width=1)
    draw.line((38, 65, 37, 71), fill=blouse, width=1)


def draw_body_side(
    draw: ImageDraw.ImageDraw,
    style: str,
    direction: str,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    outline = colors["outline"]
    coat_dark = colors["coat_dark"]
    coat = colors["coat_mid"]
    coat_light = colors["coat_light"]
    blouse = colors["blouse"]
    dress = colors["dress"]
    skin = colors["skin"]
    gold = colors.get("gold", coat_light)
    facing_right = direction == "right"
    if facing_right:
        draw.polygon([(21, 44), (42, 43), (45, 63), (23, 64)], fill=outline)
        draw.polygon([(23, 45), (40, 44), (42, 61), (24, 62)], fill=coat)
        draw.polygon([(23, 45), (29, 46), (28, 61), (24, 60)], fill=blouse)
        draw.polygon([(31, 46), (40, 45), (41, 59), (33, 62)], fill=coat_light)
        draw.rectangle((40, 47, 47, 61), fill=outline)
        draw.rectangle((41, 48, 45, 59), fill=coat)
        draw.rectangle((42, 59, 46, 63), fill=skin)
        draw.polygon([(20, 62), (43, 62), (40, 72), (22, 73)], fill=outline)
        draw.polygon([(22, 63), (41, 63), (39, 70), (24, 71)], fill=dress)
        draw.line((25, 65, 25, 71), fill=coat_dark, width=1)
    else:
        draw.polygon([(21, 43), (42, 44), (40, 64), (18, 63)], fill=outline)
        draw.polygon([(23, 44), (40, 45), (38, 62), (21, 61)], fill=coat)
        draw.polygon([(23, 44), (31, 45), (30, 60), (21, 59)], fill=coat_light)
        draw.polygon([(32, 45), (40, 46), (38, 61), (32, 61)], fill=blouse)
        draw.rectangle((17, 47, 24, 61), fill=outline)
        draw.rectangle((18, 48, 22, 59), fill=coat)
        draw.rectangle((18, 59, 22, 63), fill=skin)
        draw.polygon([(21, 62), (44, 62), (42, 72), (23, 73)], fill=outline)
        draw.polygon([(23, 63), (42, 63), (40, 70), (25, 71)], fill=dress)
        draw.line((39, 65, 39, 71), fill=coat_dark, width=1)
    draw.point((33 if facing_right else 30, 57), fill=gold)


def draw_body_back(
    draw: ImageDraw.ImageDraw,
    style: str,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    outline = colors["outline"]
    coat_dark = colors["coat_dark"]
    coat = colors["coat_mid"]
    coat_light = colors["coat_light"]
    dress = colors["dress"]
    gold = colors.get("gold", coat_light)
    draw.polygon([(19, 43), (45, 43), (43, 64), (21, 64)], fill=outline)
    draw.polygon([(21, 44), (43, 44), (41, 62), (23, 62)], fill=coat)
    draw.polygon([(21, 44), (28, 45), (29, 62), (22, 61)], fill=coat_dark)
    draw.polygon([(38, 45), (43, 44), (42, 61), (37, 62)], fill=coat_light)
    draw.polygon([(16, 46), (22, 44), (22, 62), (18, 64), (14, 60)], fill=outline)
    draw.polygon([(17, 47), (21, 46), (21, 60), (18, 61), (15, 59)], fill=coat)
    draw.polygon([(44, 44), (50, 46), (51, 60), (47, 64), (43, 62)], fill=outline)
    draw.polygon([(45, 46), (49, 47), (49, 59), (46, 61), (44, 60)], fill=coat)
    draw.polygon([(20, 62), (45, 62), (42, 73), (22, 73)], fill=outline)
    draw.polygon([(22, 63), (43, 63), (40, 71), (24, 71)], fill=dress)
    draw.line((24, 46, 24, 60), fill=coat_light)
    draw.line((40, 46, 40, 60), fill=coat_dark)
    draw.rectangle((31, 53, 33, 56), fill=gold)


def draw_head_front(
    draw: ImageDraw.ImageDraw,
    style: str,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    outline = colors["outline"]
    hair = colors["hair_dark"]
    mid = colors["hair_mid"]
    light = colors["hair_light"]
    skin = colors["skin"]
    shadow = colors["skin_shadow"]
    eye = colors["eye"]
    glint = colors["eye_light"]
    blush = colors.get("blush", shadow)
    mouth = colors.get("mouth", shadow)
    draw.rounded_rectangle((22, 18, 42, 43), radius=7, fill=outline)
    draw.rounded_rectangle((24, 20, 40, 42), radius=6, fill=skin)
    draw.rectangle((26, 37, 38, 40), fill=shadow)
    draw.polygon([(21, 26), (24, 19), (31, 17), (41, 20), (42, 28), (37, 24), (33, 29), (28, 24)], fill=hair)
    draw.polygon([(25, 19), (33, 17), (40, 22), (35, 27), (31, 23), (27, 28)], fill=mid)
    draw.line((21, 31, 22, 51), fill=light)
    draw.line((43, 31, 42, 52), fill=mid)
    draw.rectangle((27, 28, 29, 30), fill=eye)
    draw.rectangle((36, 28, 38, 30), fill=eye)
    draw.point((28, 28), fill=glint)
    draw.point((37, 28), fill=glint)
    draw.line((31, 35, 34, 35), fill=mouth)
    draw.point((25, 33), fill=blush)
    draw.point((40, 33), fill=blush)
    if style == "a":
        draw.point((23, 25), fill=colors["hair_tip"])
        draw.point((41, 31), fill=colors["hair_tip"])
    elif style == "c":
        draw.line((23, 23, 27, 18), fill=colors["hair_edge"])
        draw.line((40, 24, 44, 31), fill=colors["hair_edge"])


def draw_head_side(
    draw: ImageDraw.ImageDraw,
    style: str,
    direction: str,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    outline = colors["outline"]
    hair = colors["hair_dark"]
    mid = colors["hair_mid"]
    light = colors["hair_light"]
    skin = colors["skin"]
    shadow = colors["skin_shadow"]
    eye = colors["eye"]
    glint = colors["eye_light"]
    blush = colors.get("blush", shadow)
    left = direction == "left"
    if left:
        draw.rounded_rectangle((22, 19, 42, 42), radius=7, fill=outline)
        draw.rounded_rectangle((24, 21, 40, 41), radius=6, fill=skin)
        draw.polygon([(21, 31), (23, 35), (24, 39), (26, 36)], fill=skin)
        draw.polygon([(22, 27), (25, 19), (34, 17), (42, 21), (43, 29), (37, 25), (32, 29)], fill=hair)
        draw.rectangle((25, 29, 27, 31), fill=eye)
        draw.point((26, 29), fill=glint)
        draw.point((24, 34), fill=blush)
        draw.line((27, 36, 30, 36), fill=colors.get("mouth", shadow))
        draw.line((43, 31, 41, 53), fill=mid)
    else:
        draw.rounded_rectangle((22, 19, 42, 42), radius=7, fill=outline)
        draw.rounded_rectangle((24, 21, 40, 41), radius=6, fill=skin)
        draw.polygon([(40, 31), (41, 35), (40, 39), (38, 36)], fill=skin)
        draw.polygon([(22, 27), (24, 19), (36, 17), (43, 23), (42, 30), (36, 25), (31, 29)], fill=hair)
        draw.rectangle((36, 29, 38, 31), fill=eye)
        draw.point((37, 29), fill=glint)
        draw.point((40, 34), fill=blush)
        draw.line((33, 36, 36, 36), fill=colors.get("mouth", shadow))
        draw.line((21, 31, 23, 52), fill=light)
    if style == "a":
        draw.point((22 if left else 42, 24), fill=colors["hair_tip"])
    elif style == "c":
        draw.line((21 if left else 42, 24, 18 if left else 45, 34), fill=colors["hair_edge"])


def draw_head_back(
    draw: ImageDraw.ImageDraw,
    style: str,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    outline = colors["outline"]
    hair = colors["hair_dark"]
    mid = colors["hair_mid"]
    light = colors["hair_light"]
    draw.rounded_rectangle((20, 17, 44, 44), radius=8, fill=outline)
    draw.rounded_rectangle((22, 19, 42, 42), radius=7, fill=hair)
    draw.polygon([(24, 21), (31, 16), (40, 20), (36, 28), (31, 25), (27, 30)], fill=mid)
    draw.line((29, 23, 31, 49), fill=light)
    if style == "a":
        draw.line((24, 30, 23, 54), fill=colors["hair_tip"])
        draw.line((39, 29, 40, 55), fill=colors["hair_tip"])
    elif style == "c":
        draw.line((24, 26, 21, 55), fill=colors["hair_edge"])
        draw.line((39, 24, 43, 55), fill=colors["hair_edge"])


def draw_fins(
    draw: ImageDraw.ImageDraw,
    style: str,
    direction: str,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    outline = colors["outline"]
    dark = colors["fin_dark"]
    mid = colors["fin_mid"]
    light = colors["fin_light"]
    gold = colors.get("gold", light)
    if direction != "left":
        draw.polygon([(24, 23), (12, 19), (15, 31), (23, 35)], fill=outline)
        draw.polygon([(22, 24), (14, 21), (17, 29), (22, 32)], fill=mid)
        draw.line((18, 23, 20, 29), fill=light)
        draw.point((22, 27), fill=gold)
    if direction != "right":
        draw.polygon([(40, 23), (52, 19), (49, 31), (40, 35)], fill=outline)
        draw.polygon([(41, 24), (50, 21), (47, 29), (41, 32)], fill=mid)
        draw.line((47, 23, 44, 29), fill=light)
        draw.point((41, 27), fill=gold)
    if direction in {"down", "up"}:
        draw.line((20, 30, 21, 35), fill=dark)
        draw.line((44, 30, 43, 35), fill=dark)


def draw_style_accents(
    draw: ImageDraw.ImageDraw,
    style: str,
    direction: str,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    if style == "a":
        if direction in {"down", "up"}:
            draw.polygon([(20, 46), (24, 57), (20, 67), (16, 57)], fill=colors["coat_light"])
            draw.polygon([(44, 46), (40, 57), (44, 67), (48, 57)], fill=colors["coat_light"])
            draw.line((20, 49, 20, 58), fill=colors["fin_light"])
            draw.line((44, 49, 44, 58), fill=colors["fin_light"])
        draw.point((31, 46), fill=colors["gold_dark"])
        draw.point((33, 46), fill=colors["gold_dark"])
        draw.point((33, 55), fill=colors["gold"])
    elif style == "b":
        if direction in {"down", "up"}:
            draw.line((22, 45, 28, 48), fill=colors["blouse"])
            draw.line((42, 45, 36, 48), fill=colors["blouse"])
        draw.rectangle((30, 45, 34, 48), fill=colors["gold"])
        draw.point((32, 47), fill=colors["blouse"])
    else:
        draw.line((21, 44, 27, 49), fill=colors["fin_light"])
        draw.line((43, 44, 37, 49), fill=colors["fin_light"])
        draw.rectangle((29, 46, 34, 48), fill=colors["gold"])
        if direction in {"down", "up"}:
            draw.line((24, 64, 28, 69), fill=colors["hair_edge"])
            draw.line((40, 64, 36, 69), fill=colors["hair_edge"])


def draw_shadow(
    draw: ImageDraw.ImageDraw,
    colors: dict[str, tuple[int, int, int, int]],
) -> None:
    draw.ellipse((18, 86, 46, 90), fill=colors["shadow"])


def draw_frame(style: str, direction: str) -> Image.Image:
    colors = palette(style)
    image = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw_shadow(draw, colors)
    draw_back_hair(draw, style, direction, colors)
    draw_legs_and_boots(draw, style, direction, colors)
    if direction == "down":
        draw_body_front(draw, style, colors)
        draw_head_front(draw, style, colors)
    elif direction in {"left", "right"}:
        draw_body_side(draw, style, direction, colors)
        draw_head_side(draw, style, direction, colors)
    else:
        draw_body_back(draw, style, colors)
        draw_head_back(draw, style, colors)
    draw_fins(draw, style, direction, colors)
    draw_style_accents(draw, style, direction, colors)
    return image


def palette_image(style: str) -> Image.Image:
    colors = list(STYLES[style]["colors"].items())
    canvas = Image.new("RGB", (700, 160), "#081514")
    draw = ImageDraw.Draw(canvas)
    labels = _font(15)
    for index, (name, value) in enumerate(colors):
        x = 12 + (index % 7) * 98
        y = 10 + (index // 7) * 73
        draw.rectangle((x, y, x + 74, y + 40), fill=value, outline="#E7DDAA")
        draw.text((x, y + 46), value.upper(), fill="#F5EAB8", font=labels)
        draw.text((x, y + 59), name[:12], fill="#A7C6C1", font=labels)
    return canvas


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ):
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def metrics(style: str, sheet: Image.Image) -> dict:
    pixels = list(sheet.get_flattened_data())
    colors = sorted({pixel for pixel in pixels})
    alpha_values = sorted({pixel[3] for pixel in pixels})
    shadow = palette(style)["shadow"]
    frame_data = []
    for index, direction in enumerate(DIRECTIONS):
        frame = sheet.crop((index * 64, 0, (index + 1) * 64, 96))
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
                    pixel[3] == 255 for pixel in frame.get_flattened_data()
                ),
            }
        )
    return {
        "style": style,
        "name": STYLES[style]["name"],
        "sheet_size": list(sheet.size),
        "frame_size": list(FRAME_SIZE),
        "runtime_size": list(RUNTIME_SIZE),
        "colors": len(colors),
        "opaque_colors": len([color for color in colors if color[3] == 255]),
        "alpha_values": alpha_values,
        "directions": list(DIRECTIONS),
        "baseline_y": BASELINE_Y,
        "bbox": list(sheet.getbbox() or (0, 0, 0, 0)),
        "semi_transparent_pixels": sum(0 < pixel[3] < 255 for pixel in pixels),
        "anti_aliased_pixels": sum(0 < pixel[3] < 255 for pixel in pixels),
        "frames": frame_data,
    }


def main() -> None:
    for style in STYLES:
        output = OUTPUT_ROOT / style
        source = output / "source"
        source.mkdir(parents=True, exist_ok=True)
        frames = []
        for direction in DIRECTIONS:
            frame = draw_frame(style, direction)
            frame.save(source / f"{direction}.png", optimize=True)
            frames.append(frame)
        sheet = Image.new("RGBA", (64 * 4, 96), (0, 0, 0, 0))
        for index, frame in enumerate(frames):
            sheet.alpha_composite(frame, (index * 64, 0))
        sheet.save(output / "sprite-4dir.png", optimize=True)
        frames[0].save(output / "sprite-down-1x.png", optimize=True)
        frames[0].resize((256, 384), Image.Resampling.NEAREST).save(
            output / "sprite-preview-4x.png",
            optimize=True,
        )
        palette_image(style).save(output / "palette.png", optimize=True)
        (output / "metrics.json").write_text(
            json.dumps(metrics(style, sheet), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
