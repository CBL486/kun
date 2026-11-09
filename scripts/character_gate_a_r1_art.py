"""Native pixel-authoring for the Gate A R1 Lin Cheng candidates."""

from __future__ import annotations

from typing import Iterable

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


FRAME_SIZE = (64, 96)
DIRECTIONS = ("down", "left", "right", "up")
TRANSPARENT = (0, 0, 0, 0)

STYLE_NAMES = {
    "a": "深海童话",
    "b": "海玻璃学院",
    "c": "潮汐海报",
}
STYLE_SHORT_NAMES = {
    "a": "STORYBOOK",
    "b": "SEAGLASS",
    "c": "TIDAL GRAPHIC",
}

PALETTES = {
    "a": {
        "outline": "#061622",
        "hair_dark": "#082B43",
        "hair_mid": "#124C68",
        "hair_light": "#2A7E96",
        "hair_tip": "#58C8C7",
        "fin_dark": "#0B5966",
        "fin_mid": "#35BFC4",
        "fin_light": "#C8FFF6",
        "coat_dark": "#0A243C",
        "coat": "#173F59",
        "coat_light": "#2E6A7B",
        "blouse": "#F3FFFC",
        "dress": "#99E4E0",
        "skin": "#F1C8B7",
        "skin_shadow": "#D4948A",
        "eye": "#062732",
        "eye_light": "#61E6E4",
        "mouth": "#9F4D5B",
        "blush": "#E8A0AA",
        "gold": "#D8B46C",
        "shoe": "#0B2638",
        "shadow": "#162A2D",
    },
    "b": {
        "outline": "#061722",
        "hair_dark": "#082B43",
        "hair_mid": "#175A75",
        "hair_light": "#3693A5",
        "fin_dark": "#0D626A",
        "fin_mid": "#53D2CF",
        "fin_light": "#D2FFF8",
        "coat_dark": "#0C2B43",
        "coat": "#194960",
        "coat_light": "#39798B",
        "blouse": "#F7FFFD",
        "dress": "#A9E9E4",
        "skin": "#F3CEBD",
        "skin_shadow": "#DCA095",
        "eye": "#072E3A",
        "eye_light": "#74EAE1",
        "mouth": "#A4515E",
        "blush": "#E7A2AC",
        "gold": "#D7B66E",
        "shoe": "#092638",
        "shadow": "#172A2D",
    },
    "c": {
        "outline": "#020B15",
        "hair_dark": "#06182E",
        "hair_mid": "#0F3A5D",
        "hair_light": "#1F7891",
        "hair_edge": "#55D8D5",
        "fin_dark": "#075B68",
        "fin_mid": "#3ACECB",
        "fin_light": "#D6FFF8",
        "coat_dark": "#071C33",
        "coat": "#103551",
        "coat_light": "#24687D",
        "blouse": "#F5FFFB",
        "dress": "#8FDFDA",
        "skin": "#F0C8B6",
        "skin_shadow": "#D58F88",
        "eye": "#032633",
        "eye_light": "#72F1E4",
        "mouth": "#9B4555",
        "blush": "#E39AA7",
        "gold": "#C99D56",
        "shoe": "#071A2A",
        "shadow": "#101C26",
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
        for name, value in PALETTES[style].items()
    }


def _mask(points: Iterable[tuple[int, int]]) -> Image.Image:
    image = Image.new("L", FRAME_SIZE, 0)
    ImageDraw.Draw(image).polygon(list(points), fill=255)
    return image


def _ellipse_mask(box: tuple[int, int, int, int]) -> Image.Image:
    image = Image.new("L", FRAME_SIZE, 0)
    ImageDraw.Draw(image).ellipse(box, fill=255)
    return image


def cap_top(
    points: Iterable[tuple[int, int]],
    minimum_y: int = 18,
) -> list[tuple[int, int]]:
    return [(x, max(y, minimum_y)) for x, y in points]


class CharacterPainter:
    def __init__(
        self,
        style: str,
        direction: str,
        colors: dict[str, tuple[int, int, int, int]],
    ) -> None:
        self.style = style
        self.direction = direction
        self.colors = colors
        self.image = Image.new("RGBA", FRAME_SIZE, TRANSPARENT)
        self.draw = ImageDraw.Draw(self.image)

    def outline_size(self) -> int:
        return 5 if self.style == "c" else 3

    def shape(
        self,
        points: Iterable[tuple[int, int]],
        fill: str,
        *,
        outline: bool = True,
        outline_size: int | None = None,
    ) -> Image.Image:
        mask = _mask(points)
        if outline:
            size = outline_size or self.outline_size()
            expanded = mask.filter(ImageFilter.MaxFilter(size))
            edge = ImageChops.subtract(expanded, mask)
            self.image.paste(self.colors["outline"], (0, 0), edge)
        self.image.paste(self.colors[fill], (0, 0), mask)
        return mask

    def ellipse(
        self,
        box: tuple[int, int, int, int],
        fill: str,
        *,
        outline: bool = False,
    ) -> Image.Image:
        mask = _ellipse_mask(box)
        if outline:
            expanded = mask.filter(ImageFilter.MaxFilter(self.outline_size()))
            edge = ImageChops.subtract(expanded, mask)
            self.image.paste(self.colors["outline"], (0, 0), edge)
        self.image.paste(self.colors[fill], (0, 0), mask)
        return mask

    def paint(self, points: Iterable[tuple[int, int]], fill: str) -> None:
        mask = _mask(points)
        self.image.paste(self.colors[fill], (0, 0), mask)

    def line(
        self,
        points: Iterable[tuple[int, int]],
        color: str,
        width: int = 1,
    ) -> None:
        self.draw.line(list(points), fill=self.colors[color], width=width)

    def pixel(self, point: tuple[int, int], color: str) -> None:
        self.draw.point(point, fill=self.colors[color])


def draw_shadow(painter: CharacterPainter) -> None:
    painter.ellipse((20, 86, 44, 91), "shadow")
    painter.paint([(24, 88), (30, 87), (31, 90), (23, 91)], "shadow")
    painter.paint([(35, 87), (41, 88), (42, 91), (35, 90)], "shadow")


def back_hair_shape(style: str, direction: str) -> list[tuple[int, int]]:
    if direction == "left":
        if style == "a":
            return [
                (20, 20), (25, 15), (35, 14), (43, 18),
                (47, 25), (46, 35), (48, 45), (45, 57),
                (48, 64), (42, 67), (38, 60), (34, 64),
                (28, 57), (23, 58), (19, 47), (17, 35),
            ]
        if style == "b":
            return [
                (21, 19), (28, 15), (38, 16), (44, 21),
                (45, 32), (43, 41), (41, 50), (37, 55),
                (33, 51), (28, 55), (23, 51), (20, 41),
            ]
        return [
            (18, 21), (25, 15), (34, 13), (43, 17),
            (47, 24), (44, 35), (48, 48), (43, 61),
            (38, 56), (32, 61), (27, 55), (21, 58),
            (17, 48), (16, 34),
        ]
    if direction == "right":
        if style == "a":
            return [
                (21, 20), (28, 15), (39, 16), (45, 21),
                (47, 31), (45, 43), (48, 54), (43, 64),
                (36, 58), (32, 64), (27, 57), (21, 61),
                (16, 49), (18, 37), (17, 28),
            ]
        if style == "b":
            return [
                (20, 18), (28, 15), (39, 16), (45, 21),
                (46, 32), (43, 41), (42, 50), (38, 55),
                (33, 51), (28, 55), (23, 51), (19, 41),
            ]
        return [
            (17, 21), (25, 15), (39, 13), (46, 18),
            (48, 28), (45, 37), (49, 49), (43, 62),
            (37, 57), (31, 63), (26, 57), (20, 61),
            (16, 49), (18, 35),
        ]
    if style == "a":
        return [
            (18, 21), (23, 15), (32, 13), (41, 15),
            (47, 21), (48, 33), (46, 44), (49, 55),
            (44, 65), (39, 61), (34, 67), (29, 61),
            (23, 66), (18, 60), (15, 49), (17, 39),
            (14, 30),
        ]
    if style == "b":
        return [
            (20, 19), (27, 15), (37, 15), (44, 20),
            (45, 30), (43, 40), (41, 49), (37, 55),
            (33, 51), (28, 56), (23, 52), (19, 42),
            (18, 31),
        ]
    return [
        (17, 21), (24, 15), (32, 13), (41, 15),
        (47, 22), (46, 35), (49, 48), (43, 62),
        (38, 57), (31, 64), (26, 58), (20, 62),
        (17, 50), (16, 35),
    ]


def draw_back_hair(painter: CharacterPainter) -> None:
    points = cap_top(
        back_hair_shape(painter.style, painter.direction)
    )
    painter.shape(points, "hair_dark")
    if painter.direction == "left":
        painter.paint(
            [(24, 24), (31, 18), (39, 20), (41, 33), (36, 37), (30, 29)],
            "hair_mid",
        )
        painter.line([(21, 31), (22, 48), (25, 56)], "hair_light")
        painter.line([(41, 29), (44, 45), (43, 55)], "hair_dark")
    elif painter.direction == "right":
        painter.paint(
            [(24, 20), (34, 17), (41, 23), (38, 37), (31, 30), (25, 34)],
            "hair_mid",
        )
        painter.line([(23, 31), (24, 48), (27, 55)], "hair_light")
        painter.line([(40, 33), (42, 47), (40, 58)], "hair_light")
    else:
        painter.paint(
            [(23, 21), (31, 15), (40, 19), (39, 31), (34, 27), (29, 33)],
            "hair_mid",
        )
        painter.line([(20, 30), (22, 50), (25, 58)], "hair_light")
        painter.line([(44, 29), (43, 48), (39, 58)], "hair_light")
    if painter.style == "a":
        painter.line([(18, 39), (20, 54), (25, 62)], "hair_tip")
        painter.line([(45, 38), (44, 54), (38, 63)], "hair_tip")
    elif painter.style == "c":
        painter.line([(17, 31), (20, 45), (22, 53)], "hair_edge")
        painter.line([(46, 30), (46, 43), (42, 52)], "hair_edge")


def draw_fin(
    painter: CharacterPainter,
    side: str,
    *,
    high: bool = False,
    back: bool = False,
) -> None:
    y = 20 if high else 22
    if back:
        y += 2
    if side == "left":
        if painter.style == "b":
            outer = [(14, y + 2), (21, y + 1), (20, y + 7), (16, y + 14), (14, y + 9)]
            inner = [(16, y + 4), (20, y + 3), (19, y + 7), (17, y + 11)]
        elif painter.style == "c":
            outer = [(14, y + 2), (21, y + 3), (20, y + 9), (15, y + 15), (17, y + 8)]
            inner = [(16, y + 4), (20, y + 5), (19, y + 8), (16, y + 12)]
        else:
            outer = [(14, y + 2), (21, y), (20, y + 7), (15, y + 15), (17, y + 8)]
            inner = [(16, y + 4), (20, y + 3), (19, y + 7), (16, y + 12)]
        painter.shape(outer, "fin_dark")
        painter.paint(inner, "fin_mid")
        painter.line([(17, y + 5), (18, y + 9)], "fin_light")
        painter.line([(15, y + 8), (17, y + 11)], "fin_dark")
    else:
        if painter.style == "b":
            outer = [(43, y + 1), (50, y + 2), (50, y + 9), (46, y + 14), (44, y + 7)]
            inner = [(45, y + 4), (49, y + 3), (48, y + 7), (46, y + 11)]
        elif painter.style == "c":
            outer = [(43, y + 3), (49, y + 1), (48, y + 16), (44, y + 9), (47, y + 8)]
            inner = [(45, y + 5), (48, y + 3), (47, y + 8), (45, y + 12)]
        else:
            outer = [(43, y), (50, y + 2), (49, y + 16), (44, y + 8), (47, y + 8)]
            inner = [(45, y + 3), (49, y + 4), (48, y + 9), (45, y + 12)]
        painter.shape(outer, "fin_dark")
        painter.paint(inner, "fin_mid")
        painter.line([(47, y + 5), (46, y + 9)], "fin_light")
        painter.line([(49, y + 8), (47, y + 12)], "fin_dark")


def draw_legs(painter: CharacterPainter) -> None:
    if painter.direction == "left":
        legs = [
            ((27, 68), (30, 68), (30, 82), (27, 82)),
            ((35, 67), (39, 67), (39, 82), (35, 82)),
        ]
        boots = [
            ((23, 81), (31, 81), (31, 87), (23, 87)),
            ((34, 81), (41, 81), (41, 87), (34, 87)),
        ]
    elif painter.direction == "right":
        legs = [
            ((28, 67), (32, 67), (32, 82), (28, 82)),
            ((37, 68), (40, 68), (40, 82), (37, 82)),
        ]
        boots = [
            ((24, 81), (32, 81), (32, 87), (24, 87)),
            ((37, 81), (44, 81), (44, 87), (36, 87)),
        ]
    else:
        legs = [
            ((27, 67), (30, 67), (30, 82), (27, 82)),
            ((34, 67), (37, 67), (37, 82), (34, 82)),
        ]
        boots = [
            ((24, 81), (31, 81), (31, 87), (23, 87)),
            ((34, 81), (41, 81), (41, 87), (33, 87)),
        ]
    for leg in legs:
        painter.shape(leg, "skin")
    for index, boot in enumerate(boots):
        painter.shape(boot, "shoe")
        sole = [
            (boot[0][0], 86),
            (boot[1][0], 86),
            (boot[1][0], 88),
            (boot[0][0], 88),
        ]
        painter.paint(sole, "outline")
        painter.pixel(
            ((boot[0][0] + 3, 84) if index == 0 else (boot[1][0] - 3, 84)),
            "gold",
        )


def body_shape(style: str, direction: str) -> list[tuple[int, int]]:
    if direction == "left":
        if style == "a":
            return [
                (24, 44), (41, 44), (46, 50), (45, 60),
                (43, 67), (38, 69), (33, 65), (29, 68),
                (24, 64), (21, 58), (22, 49),
            ]
        if style == "b":
            return [
                (25, 44), (41, 44), (44, 50), (43, 61),
                (40, 66), (35, 67), (31, 64), (27, 66),
                (23, 62), (21, 53),
            ]
        return [
            (23, 44), (42, 44), (47, 50), (45, 58),
            (47, 65), (40, 68), (35, 62), (29, 67),
            (22, 63), (20, 55),
        ]
    if direction == "right":
        if style == "a":
            return [
                (23, 44), (40, 44), (43, 49), (42, 58),
                (45, 64), (40, 69), (35, 65), (31, 68),
                (26, 67), (18, 60), (19, 50),
            ]
        if style == "b":
            return [
                (23, 44), (39, 44), (42, 50), (42, 61),
                (39, 66), (34, 67), (30, 64), (25, 66),
                (20, 62), (19, 53),
            ]
        return [
            (22, 44), (41, 44), (44, 55), (42, 63),
            (36, 67), (31, 62), (25, 68), (18, 65),
            (16, 58), (19, 50),
        ]
    if style == "a":
        return [
            (22, 44), (42, 44), (47, 51), (46, 59),
            (43, 66), (38, 69), (34, 66), (32, 68),
            (29, 66), (25, 68), (20, 64), (18, 56),
            (20, 49),
        ]
    if style == "b":
        return [
            (23, 44), (41, 44), (44, 51), (43, 61),
            (40, 66), (35, 68), (32, 66), (29, 68),
            (24, 66), (21, 61), (20, 52),
        ]
    return [
        (22, 44), (42, 44), (46, 50), (44, 57),
        (46, 64), (40, 68), (35, 63), (32, 67),
        (28, 62), (22, 66), (18, 58), (20, 49),
    ]


def draw_body(painter: CharacterPainter) -> None:
    style = painter.style
    direction = painter.direction
    painter.shape([(29, 41), (35, 41), (36, 47), (28, 47)], "skin")
    painter.shape(body_shape(style, direction), "coat")

    if direction == "down":
        painter.paint(
            [(29, 45), (35, 45), (37, 59), (33, 64), (28, 59)],
            "blouse",
        )
        painter.paint([(30, 45), (32, 45), (30, 54)], "coat_light")
        painter.paint([(36, 47), (41, 49), (39, 62), (34, 64)], "coat_dark")
        painter.line([(28, 48), (27, 59), (31, 64)], "blouse")
        painter.line([(36, 48), (37, 59), (34, 64)], "coat_light")
        painter.paint(
            [(24, 61), (40, 61), (43, 68), (39, 72), (25, 72), (21, 68)],
            "dress",
        )
        painter.line([(27, 64), (27, 70)], "blouse")
        painter.line([(32, 63), (32, 71)], "blouse")
        painter.line([(37, 64), (36, 70)], "blouse")
        painter.shape([(18, 62), (23, 62), (23, 68), (19, 70), (16, 66)], "skin")
        painter.shape([(41, 62), (46, 62), (48, 66), (45, 70), (41, 68)], "skin")
        painter.paint([(19, 62), (23, 63), (23, 66), (19, 66)], "blouse")
        painter.paint([(41, 63), (45, 62), (45, 66), (41, 66)], "blouse")
        painter.paint([(31, 55), (35, 57), (36, 55), (35, 60), (31, 59)], "gold")
        painter.pixel((32, 57), "coat_dark")
        painter.pixel((34, 57), "coat_dark")
    elif direction == "up":
        painter.paint([(24, 46), (40, 47), (39, 64), (34, 67), (28, 64)], "coat")
        painter.paint([(22, 47), (27, 46), (28, 62), (24, 64)], "coat_light")
        painter.paint([(38, 47), (42, 51), (40, 63), (35, 66)], "coat_dark")
        painter.line([(29, 47), (30, 64)], "coat_light")
        painter.line([(36, 47), (35, 64)], "coat_dark")
        painter.paint(
            [(24, 62), (41, 62), (43, 69), (38, 72), (25, 72), (21, 69)],
            "dress",
        )
        painter.line([(28, 65), (27, 70)], "blouse")
        painter.line([(36, 65), (37, 70)], "blouse")
        painter.shape([(18, 62), (23, 62), (23, 68), (19, 69), (16, 66)], "skin")
        painter.shape([(41, 62), (46, 62), (48, 66), (45, 69), (41, 68)], "skin")
        painter.paint([(30, 54), (34, 54), (35, 57), (32, 59), (29, 57)], "gold")
        painter.pixel((32, 56), "coat_dark")
    else:
        facing_left = direction == "left"
        if facing_left:
            painter.paint([(24, 45), (32, 46), (31, 61), (27, 64), (23, 59)], "blouse")
            painter.paint([(33, 46), (41, 47), (39, 64), (33, 66)], "coat_light")
            painter.paint([(25, 61), (43, 62), (42, 69), (39, 72), (25, 71), (22, 68)], "dress")
            painter.shape([(45, 49), (48, 49), (47, 64), (44, 63)], "skin")
            painter.paint([(44, 48), (47, 50), (47, 55), (44, 54)], "coat_dark")
            painter.shape([(20, 63), (24, 63), (24, 67), (20, 68), (18, 66)], "skin")
        else:
            painter.paint([(32, 46), (40, 45), (41, 60), (36, 64), (33, 60)], "blouse")
            painter.paint([(23, 46), (31, 46), (30, 64), (24, 63)], "coat_light")
            painter.paint([(23, 61), (41, 61), (43, 68), (39, 72), (25, 71), (21, 68)], "dress")
            painter.shape([(16, 49), (19, 49), (20, 64), (17, 63)], "skin")
            painter.paint([(17, 48), (20, 50), (20, 55), (17, 54)], "coat_dark")
            painter.shape([(40, 63), (45, 63), (47, 66), (44, 68), (40, 67)], "skin")
        painter.paint([(31, 55), (34, 56), (35, 58), (32, 60), (29, 58)], "gold")
        painter.pixel((32, 57), "coat_dark")

    painter.line([(24, 59), (40, 59)], "coat_dark")
    painter.line([(24, 60), (40, 60)], "coat_light")


def draw_head_down(painter: CharacterPainter) -> None:
    painter.shape(
        [(23, 23), (27, 19), (38, 19), (42, 23), (42, 32), (40, 38),
         (36, 42), (32, 43), (28, 41), (24, 37), (22, 31)],
        "skin",
    )
    painter.paint([(24, 35), (27, 40), (31, 42), (31, 40), (27, 37)], "skin_shadow")
    painter.shape(
        cap_top([
            (20, 24), (23, 20), (27, 17), (32, 15), (40, 16),
            (45, 22), (44, 31), (42, 34), (40, 30), (41, 25),
            (37, 29), (35, 24), (31, 29), (28, 24), (25, 31),
            (23, 35), (21, 31),
        ]),
        "hair_dark",
    )
    painter.paint([(24, 22), (31, 17), (39, 19), (40, 24), (35, 26), (32, 23), (28, 27)], "hair_mid")
    painter.paint([(36, 24), (42, 23), (41, 29), (38, 30)], "hair_light")
    if painter.style == "b":
        painter.paint([(23, 27), (20, 33), (21, 43), (24, 51), (27, 48), (26, 36)], "hair_dark")
        painter.paint([(40, 27), (44, 33), (43, 45), (39, 51), (38, 44), (39, 36)], "hair_dark")
    else:
        painter.paint([(23, 27), (20, 33), (21, 45), (23, 52), (26, 58), (27, 48), (26, 36)], "hair_dark")
        painter.paint([(40, 27), (44, 33), (44, 46), (42, 55), (39, 58), (38, 47), (39, 36)], "hair_dark")
    painter.line([(24, 31), (23, 45), (26, 54)], "hair_light")
    painter.line([(41, 31), (42, 46), (39, 55)], "hair_light")

    painter.paint([(27, 31), (30, 32), (29, 35), (27, 34)], "eye")
    painter.paint([(35, 32), (38, 31), (38, 34), (35, 35)], "eye")
    painter.pixel((28, 32), "eye_light")
    painter.pixel((37, 32), "eye_light")
    painter.pixel((33, 36), "skin_shadow")
    painter.line([(30, 38), (32, 39), (34, 38)], "mouth")
    painter.pixel((25, 37), "blush")
    painter.pixel((39, 37), "blush")
    if painter.style == "b":
        painter.pixel((27, 30), "hair_dark")
        painter.pixel((38, 30), "hair_dark")
    elif painter.style == "c":
        painter.line([(27, 29), (30, 30)], "hair_dark")
        painter.line([(35, 30), (38, 29)], "hair_dark")


def draw_head_left(painter: CharacterPainter) -> None:
    painter.shape(
        [(19, 29), (20, 24), (24, 20), (33, 18), (40, 20), (42, 25),
         (41, 32), (39, 38), (35, 41), (30, 42), (25, 39), (21, 35)],
        "skin",
    )
    painter.paint([(18, 31), (21, 31), (21, 35), (19, 36)], "skin")
    painter.paint([(22, 36), (28, 41), (33, 42), (33, 40), (28, 37)], "skin_shadow")
    painter.shape(
        cap_top([
            (19, 28), (22, 22), (29, 17), (38, 16), (44, 21),
            (45, 30), (42, 35), (40, 30), (40, 24), (35, 29),
            (32, 24), (28, 30), (24, 26), (23, 34), (20, 35),
        ]),
        "hair_dark",
    )
    painter.paint([(23, 24), (30, 18), (39, 20), (40, 26), (35, 27), (32, 23), (27, 28)], "hair_mid")
    painter.line([(23, 29), (22, 46), (25, 55)], "hair_light")
    painter.paint([(26, 31), (29, 32), (28, 35), (26, 34)], "eye")
    painter.pixel((27, 32), "eye_light")
    painter.pixel((20, 34), "skin_shadow")
    painter.line([(23, 37), (26, 37)], "mouth")
    painter.pixel((24, 36), "blush")
    if painter.style == "b":
        painter.paint([(39, 27), (43, 31), (43, 40), (39, 48), (38, 40)], "hair_dark")
    else:
        painter.paint([(39, 27), (43, 31), (44, 43), (42, 51), (39, 54), (38, 42)], "hair_dark")
    painter.line([(41, 31), (42, 44), (40, 50)], "hair_light")


def draw_head_right(painter: CharacterPainter) -> None:
    painter.shape(
        [(23, 20), (31, 18), (39, 20), (44, 24), (45, 30), (45, 34),
         (42, 39), (38, 42), (32, 42), (27, 40), (23, 35), (22, 28)],
        "skin",
    )
    painter.paint([(44, 31), (47, 31), (47, 35), (44, 36)], "skin")
    painter.paint([(31, 36), (36, 42), (38, 40), (35, 37)], "skin_shadow")
    painter.shape(
        cap_top([
            (20, 28), (21, 21), (27, 17), (36, 16), (43, 21),
            (45, 28), (44, 34), (42, 35), (40, 30), (36, 25),
            (33, 30), (29, 25), (25, 29), (23, 35), (20, 34),
        ]),
        "hair_dark",
    )
    painter.paint([(23, 24), (31, 18), (40, 20), (39, 27), (33, 24), (29, 28), (25, 24)], "hair_mid")
    if painter.style == "b":
        painter.paint([(22, 27), (19, 33), (20, 43), (24, 49), (26, 47), (25, 35)], "hair_dark")
    else:
        painter.paint([(22, 27), (19, 33), (20, 44), (23, 55), (26, 58), (27, 47), (25, 35)], "hair_dark")
    painter.line([(22, 31), (21, 45), (24, 53)], "hair_light")
    painter.paint([(36, 31), (39, 32), (38, 35), (36, 34)], "eye")
    painter.pixel((37, 32), "eye_light")
    painter.pixel((45, 34), "skin_shadow")
    painter.line([(38, 37), (41, 37)], "mouth")
    painter.pixel((41, 36), "blush")
    painter.line([(39, 28), (43, 33), (43, 43)], "hair_light")


def draw_head_up(painter: CharacterPainter) -> None:
    painter.shape(
        cap_top([
            (20, 24), (23, 18), (32, 15), (41, 18), (45, 24),
            (44, 32), (42, 40), (37, 44), (27, 44), (22, 39),
            (20, 31),
        ]),
        "hair_dark",
    )
    painter.paint(
        [(23, 23), (29, 17), (39, 19), (41, 26), (36, 28), (33, 24), (28, 30), (25, 26)],
        "hair_mid",
    )
    painter.paint([(27, 30), (31, 26), (33, 34), (29, 38)], "hair_mid")
    painter.line([(22, 28), (20, 43), (23, 53)], "hair_light")
    if painter.style == "b":
        painter.line([(42, 27), (42, 43), (39, 51)], "hair_light")
    else:
        painter.line([(42, 27), (43, 45), (39, 57)], "hair_light")
    painter.line([(30, 20), (31, 39)], "hair_dark")
    if painter.style == "a":
        painter.line([(18, 38), (19, 54), (24, 62)], "hair_tip")
        painter.line([(45, 38), (44, 54), (39, 62)], "hair_tip")
    elif painter.style == "c":
        painter.line([(17, 31), (19, 47), (22, 55)], "hair_edge")
        painter.line([(46, 31), (45, 47), (41, 56)], "hair_edge")


def draw_collar_and_head(painter: CharacterPainter) -> None:
    if painter.direction == "down":
        draw_head_down(painter)
    elif painter.direction == "left":
        draw_head_left(painter)
    elif painter.direction == "right":
        draw_head_right(painter)
    else:
        draw_head_up(painter)


def draw_fins(painter: CharacterPainter) -> None:
    if painter.direction in {"down", "up"}:
        draw_fin(painter, "left", high=painter.style == "b")
        draw_fin(painter, "right", high=painter.style == "b")
    elif painter.direction == "left":
        draw_fin(painter, "left", high=True)
        draw_fin(painter, "right", back=True)
    else:
        draw_fin(painter, "left", back=True)
        draw_fin(painter, "right", high=True)


def build_frame(style: str, direction: str) -> Image.Image:
    colors = palette(style)
    painter = CharacterPainter(style, direction, colors)
    painter.image = Image.new("RGBA", FRAME_SIZE, TRANSPARENT)
    painter.draw = ImageDraw.Draw(painter.image)
    draw_shadow(painter)
    draw_back_hair(painter)
    draw_legs(painter)
    draw_body(painter)
    draw_collar_and_head(painter)
    draw_fins(painter)
    painter.image.paste(TRANSPARENT, (0, 0, 64, 17))
    painter.image.paste(TRANSPARENT, (0, 89, 64, 96))
    return painter.image


def build_palette_image(sheet: Image.Image) -> Image.Image:
    used = sorted(
        {
            pixel
            for pixel in sheet.get_flattened_data()
            if pixel[3] == 255
        },
        key=lambda value: tuple(value[:3]),
    )
    columns = 7
    rows = max(1, (len(used) + columns - 1) // columns)
    canvas = Image.new(
        "RGB",
        (700, 26 + rows * 80),
        "#081514",
    )
    draw = ImageDraw.Draw(canvas)
    font = _font(14)
    for index, color in enumerate(used):
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


def build_reference_board(
    style: str,
    sheet: Image.Image,
) -> Image.Image:
    canvas = Image.new("RGBA", (1024, 1024), rgba("#071720"))
    draw = ImageDraw.Draw(canvas)
    title_font = _font(32)
    label_font = _font(18)
    small_font = _font(14)

    draw.rectangle((0, 0, 1024, 112), fill=rgba("#0B2B3A"))
    draw.rectangle((0, 108, 1024, 112), fill=rgba("#49C9C5"))
    draw.text(
        (52, 30),
        f"LIN CHENG / {style.upper()}",
        fill=rgba("#F2FFFC"),
        font=title_font,
    )
    draw.text(
        (54, 72),
        f"{STYLE_SHORT_NAMES[style]} / 64x96 NATIVE DIRECTION PROOF",
        fill=rgba("#91C8C7"),
        font=label_font,
    )

    front = sheet.crop((0, 0, 64, 96))
    main = front.resize((448, 672), Image.Resampling.NEAREST)
    canvas.alpha_composite(main, (66, 156))
    draw.rectangle((56, 142, 532, 846), outline=rgba("#2C7685"), width=2)
    draw.text((68, 852), "DOWN / GAMEPLAY SILHOUETTE", fill=rgba("#D8FFF8"), font=small_font)

    positions = {
        "left": (590, 156),
        "right": (786, 156),
        "up": (590, 470),
    }
    for index, (name, (x, y)) in enumerate(positions.items()):
        direction_index = DIRECTIONS.index(name)
        image = sheet.crop((direction_index * 64, 0, (direction_index + 1) * 64, 96))
        image = image.resize((192, 288), Image.Resampling.NEAREST)
        canvas.alpha_composite(image, (x, y))
        draw.rectangle((x - 6, y - 6, x + 198, y + 294), outline=rgba("#2C7685"), width=2)
        draw.text((x, y + 302), name.upper(), fill=rgba("#D8FFF8"), font=small_font)

    palette_image = build_palette_image(sheet)
    palette_image.thumbnail((392, 180), Image.Resampling.NEAREST)
    canvas.alpha_composite(palette_image.convert("RGBA"), (590, 810))
    draw.text((590, 786), "USED PALETTE", fill=rgba("#D8FFF8"), font=small_font)
    draw.text(
        (66, 912),
        "NATIVE PIXEL SOURCE / CLEAN REFERENCE BOARD",
        fill=rgba("#86B5B5"),
        font=small_font,
    )
    return canvas.convert("RGB")
