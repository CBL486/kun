"""Author the original blue-whale character assets without external imagery."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "characters" / "whale-girl"
PORTRAITS = OUTPUT / "portraits"
SHEETS = OUTPUT / "sheets"
FRAME = (64, 96)
DIRECTIONS = ("down", "left", "right", "up")
ANIMATIONS = {
    "idle": (4, 5.0, True),
    "walk": (6, 9.0, True),
    "turn": (4, 10.0, False),
    "stop": (3, 10.0, False),
    "study": (4, 5.0, True),
}
PALETTE = {
    "outline": "#06171f",
    "deep": "#0d2d42",
    "hair": "#174d70",
    "hair_light": "#2e7d9e",
    "fin": "#75d8d8",
    "fin_light": "#c9fbf1",
    "skin": "#f0c7b8",
    "skin_shadow": "#d79d92",
    "coat": "#183d55",
    "coat_light": "#2d6177",
    "dress": "#a8e8e5",
    "white": "#e9fffb",
    "eye": "#092332",
    "blush": "#e99ba4",
}


def rgba(hex_color: str) -> tuple[int, int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(bytes.fromhex(value)) + (255,)


def draw_frame(
    direction: str,
    action: str,
    frame_index: int,
    frame_count: int,
    *,
    expression: str = "calm",
) -> Image.Image:
    image = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    phase = frame_index / max(1, frame_count)
    bob = 0
    lean = 0
    stride = 0
    arm = 0
    if action == "idle":
        bob = [0, -1, 0, 1][frame_index % 4]
    elif action == "walk":
        bob = [0, -1, -2, -1, 0, 1][frame_index % 6]
        stride = [-4, -1, 3, 4, 1, -3][frame_index % 6]
        arm = [3, 1, -2, -3, -1, 2][frame_index % 6]
    elif action == "turn":
        bob = [0, -1, -1, 0][frame_index % 4]
        lean = [-4, -1, 3, 0][frame_index % 4]
    elif action == "stop":
        bob = [0, -1, 0][frame_index % 3]
        stride = [2, -1, 0][frame_index % 3]

    cx = 32 + lean
    top = 10 + bob
    outline = rgba(PALETTE["outline"])
    hair = rgba(PALETTE["hair"])
    hair_light = rgba(PALETTE["hair_light"])
    fin = rgba(PALETTE["fin"])
    fin_light = rgba(PALETTE["fin_light"])
    skin = rgba(PALETTE["skin"])
    skin_shadow = rgba(PALETTE["skin_shadow"])
    coat = rgba(PALETTE["coat"])
    coat_light = rgba(PALETTE["coat_light"])
    dress = rgba(PALETTE["dress"])
    white = rgba(PALETTE["white"])
    eye = rgba(PALETTE["eye"])
    blush = rgba(PALETTE["blush"])

    draw.ellipse((cx - 14, 83, cx + 15, 89), fill=(1, 12, 17, 80))

    # Flowing hair mass and whale-fin silhouette.
    draw.polygon(
        [
            (cx - 13, top + 9),
            (cx - 20, top + 25),
            (cx - 17, top + 51),
            (cx - 7, top + 58),
            (cx + 7, top + 58),
            (cx + 17, top + 51),
            (cx + 20, top + 25),
            (cx + 13, top + 9),
        ],
        fill=outline,
    )
    draw.polygon(
        [
            (cx - 12, top + 10),
            (cx - 17, top + 28),
            (cx - 13, top + 52),
            (cx - 5, top + 56),
            (cx + 5, top + 56),
            (cx + 13, top + 52),
            (cx + 17, top + 28),
            (cx + 12, top + 10),
        ],
        fill=hair,
    )
    draw.polygon(
        [
            (cx - 6, top + 15),
            (cx - 11, top + 29),
            (cx - 8, top + 45),
            (cx - 2, top + 40),
            (cx + 1, top + 26),
        ],
        fill=hair_light,
    )
    draw.polygon(
        [(cx - 17, top + 20), (cx - 23, top + 28), (cx - 16, top + 35)],
        fill=fin,
    )
    draw.polygon(
        [(cx + 17, top + 20), (cx + 23, top + 28), (cx + 16, top + 35)],
        fill=fin,
    )
    draw.line((cx - 18, top + 26, cx - 16, top + 34), fill=fin_light, width=1)
    draw.line((cx + 18, top + 26, cx + 16, top + 34), fill=fin_light, width=1)

    # Head and face.
    draw.rounded_rectangle(
        (cx - 10, top + 10, cx + 10, top + 35),
        radius=7,
        fill=outline,
    )
    draw.rounded_rectangle(
        (cx - 8, top + 12, cx + 8, top + 33),
        radius=6,
        fill=skin,
    )
    draw.rectangle((cx - 7, top + 28, cx + 7, top + 31), fill=skin_shadow)
    if direction != "up":
        eye_y = top + 22
        if direction == "left":
            draw.rectangle((cx - 6, eye_y, cx - 4, eye_y + 2), fill=eye)
            draw.rectangle((cx + 1, eye_y, cx + 3, eye_y + 2), fill=eye)
        elif direction == "right":
            draw.rectangle((cx - 3, eye_y, cx - 1, eye_y + 2), fill=eye)
            draw.rectangle((cx + 4, eye_y, cx + 6, eye_y + 2), fill=eye)
        else:
            draw.rectangle((cx - 5, eye_y, cx - 3, eye_y + 2), fill=eye)
            draw.rectangle((cx + 3, eye_y, cx + 5, eye_y + 2), fill=eye)
        if expression == "happy":
            draw.line((cx - 4, top + 28, cx, top + 30, cx + 4, top + 28), fill=eye, width=1)
        elif expression == "low":
            draw.line((cx - 4, top + 29, cx + 4, top + 27), fill=eye, width=1)
        elif expression == "focus":
            draw.line((cx - 6, eye_y - 2, cx - 2, eye_y - 1), fill=hair, width=1)
            draw.line((cx + 2, eye_y - 1, cx + 6, eye_y - 2), fill=hair, width=1)

    # Coat, dress, arms and legs.
    torso_top = top + 35
    draw.polygon(
        [
            (cx - 11, torso_top),
            (cx - 15, torso_top + 23),
            (cx + 15, torso_top + 23),
            (cx + 11, torso_top),
        ],
        fill=outline,
    )
    draw.polygon(
        [
            (cx - 9, torso_top + 1),
            (cx - 12, torso_top + 21),
            (cx + 12, torso_top + 21),
            (cx + 9, torso_top + 1),
        ],
        fill=coat,
    )
    draw.polygon(
        [(cx - 7, torso_top + 1), (cx, torso_top + 9), (cx + 7, torso_top + 1)],
        fill=white,
    )
    draw.rectangle((cx - 1, torso_top + 8, cx + 1, torso_top + 19), fill=dress)
    draw.polygon(
        [
            (cx - 12, torso_top + 21),
            (cx - 16, torso_top + 36),
            (cx + 16, torso_top + 36),
            (cx + 12, torso_top + 21),
        ],
        fill=outline,
    )
    draw.polygon(
        [
            (cx - 10, torso_top + 21),
            (cx - 13, torso_top + 34),
            (cx + 13, torso_top + 34),
            (cx + 10, torso_top + 21),
        ],
        fill=dress,
    )
    draw.line((cx - 8, torso_top + 2, cx - 14, torso_top + 20 + arm), fill=outline, width=4)
    draw.line((cx + 8, torso_top + 2, cx + 14, torso_top + 20 - arm), fill=outline, width=4)
    draw.line((cx - 14, torso_top + 20 + arm, cx - 14, torso_top + 25 + arm), fill=skin, width=2)
    draw.line((cx + 14, torso_top + 20 - arm, cx + 14, torso_top + 25 - arm), fill=skin, width=2)

    foot_y = torso_top + 38
    left_x = cx - 7 + stride
    right_x = cx + 4 - stride
    draw.rectangle((left_x, foot_y, left_x + 4, foot_y + 10), fill=outline)
    draw.rectangle((right_x, foot_y, right_x + 4, foot_y + 10), fill=outline)
    draw.rectangle((left_x, foot_y + 7, left_x + 5, foot_y + 10), fill=hair_light)
    draw.rectangle((right_x, foot_y + 7, right_x + 5, foot_y + 10), fill=hair_light)

    # Direction cues: back hair covers the face, side view adds a trailing fin.
    if direction == "up":
        draw.rectangle((cx - 8, top + 12, cx + 8, top + 31), fill=hair)
        draw.polygon(
            [(cx - 5, top + 17), (cx, top + 29), (cx + 5, top + 17)],
            fill=hair_light,
        )
    if direction == "left":
        draw.polygon([(cx + 12, torso_top + 13), (cx + 22, torso_top + 18), (cx + 13, torso_top + 23)], fill=fin)
    elif direction == "right":
        draw.polygon([(cx - 12, torso_top + 13), (cx - 22, torso_top + 18), (cx - 13, torso_top + 23)], fill=fin)

    if expression in {"happy", "focus"} and direction != "up":
        draw.point((cx - 8, top + 27), fill=blush)
        draw.point((cx + 8, top + 27), fill=blush)
    if action == "study":
        book_y = torso_top + 14
        draw.rectangle((cx - 9, book_y, cx + 9, book_y + 7), fill=outline)
        draw.rectangle((cx - 8, book_y + 1, cx, book_y + 6), fill=white)
        draw.rectangle((cx + 1, book_y + 1, cx + 8, book_y + 6), fill=dress)
        draw.line((cx - 13, torso_top + 18, cx - 8, book_y + 3), fill=skin, width=2)
        draw.line((cx + 13, torso_top + 18, cx + 8, book_y + 3), fill=skin, width=2)
    return image


def draw_portrait(expression: str) -> Image.Image:
    size = 128
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outline = rgba(PALETTE["outline"])
    hair = rgba(PALETTE["hair"])
    hair_light = rgba(PALETTE["hair_light"])
    fin = rgba(PALETTE["fin"])
    fin_light = rgba(PALETTE["fin_light"])
    skin = rgba(PALETTE["skin"])
    skin_shadow = rgba(PALETTE["skin_shadow"])
    coat = rgba(PALETTE["coat"])
    coat_light = rgba(PALETTE["coat_light"])
    white = rgba(PALETTE["white"])
    eye = rgba(PALETTE["eye"])
    blush = rgba(PALETTE["blush"])

    draw.ellipse((32, 104, 96, 116), fill=(1, 12, 17, 90))
    draw.polygon(
        [(31, 30), (17, 58), (25, 105), (43, 111), (85, 111), (103, 105), (111, 58), (97, 30)],
        fill=outline,
    )
    draw.polygon(
        [(35, 32), (22, 60), (30, 101), (47, 107), (81, 107), (98, 101), (106, 60), (93, 32)],
        fill=hair,
    )
    draw.polygon([(24, 55), (9, 68), (25, 82)], fill=fin)
    draw.polygon([(104, 55), (119, 68), (103, 82)], fill=fin)
    draw.line((23, 64, 25, 80), fill=fin_light, width=2)
    draw.line((105, 64, 103, 80), fill=fin_light, width=2)
    draw.polygon(
        [(42, 38), (32, 60), (34, 92), (48, 102), (54, 96), (47, 78), (52, 55)],
        fill=hair_light,
    )
    draw.polygon(
        [(86, 38), (96, 60), (94, 92), (80, 102), (74, 96), (81, 78), (76, 55)],
        fill=hair_light,
    )
    draw.rounded_rectangle((39, 28, 89, 86), radius=18, fill=outline)
    draw.rounded_rectangle((42, 31, 86, 83), radius=16, fill=skin)
    draw.polygon(
        [(41, 39), (51, 24), (72, 22), (87, 35), (78, 49), (70, 37), (57, 45), (48, 35)],
        fill=hair,
    )
    draw.polygon(
        [(54, 30), (68, 24), (78, 31), (70, 36), (60, 34), (50, 39)],
        fill=hair_light,
    )
    draw.rectangle((61, 59, 67, 67), fill=skin_shadow)
    draw.rectangle((48, 53, 56, 59), fill=white)
    draw.rectangle((72, 53, 80, 59), fill=white)
    draw.rectangle((51, 55, 54, 60), fill=eye)
    draw.rectangle((74, 55, 77, 60), fill=eye)
    draw.point((52, 56), fill=fin_light)
    draw.point((75, 56), fill=fin_light)
    if expression == "happy":
        draw.line((59, 72, 64, 76, 70, 72), fill=eye, width=2)
        draw.rectangle((42, 67, 48, 69), fill=blush)
        draw.rectangle((80, 67, 86, 69), fill=blush)
    elif expression == "low":
        draw.line((59, 75, 70, 72), fill=eye, width=2)
        draw.line((46, 48, 56, 46), fill=hair, width=2)
        draw.line((72, 46, 82, 48), fill=hair, width=2)
    elif expression == "focus":
        draw.line((59, 74, 70, 74), fill=eye, width=2)
        draw.line((45, 48, 56, 50), fill=hair, width=2)
        draw.line((72, 50, 83, 48), fill=hair, width=2)
        draw.point((52, 56), fill=fin_light)
    else:
        draw.line((59, 73, 70, 73), fill=eye, width=1)

    draw.polygon([(32, 86), (96, 86), (111, 128), (17, 128)], fill=outline)
    draw.polygon([(35, 88), (93, 88), (104, 128), (24, 128)], fill=coat)
    draw.polygon([(49, 86), (64, 101), (79, 86)], fill=white)
    draw.polygon([(58, 99), (70, 99), (76, 128), (52, 128)], fill=coat_light)
    draw.line((36, 96, 26, 119), fill=fin, width=3)
    draw.line((92, 96, 102, 119), fill=fin, width=3)
    return image.resize((512, 512), Image.Resampling.NEAREST)


def save_sheet(direction: str, action: str) -> dict:
    frame_count, fps, loop = ANIMATIONS[action]
    sheet = Image.new(
        "RGBA",
        (FRAME[0] * frame_count, FRAME[1]),
        (0, 0, 0, 0),
    )
    for index in range(frame_count):
        sheet.alpha_composite(
            draw_frame(direction, action, index, frame_count),
            (FRAME[0] * index, 0),
        )
    path = SHEETS / f"{action}-{direction}.webp"
    sheet.save(path, "WEBP", lossless=True, quality=100, method=6)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "frames": frame_count,
        "fps": fps,
        "loop": loop,
        "frame_width": FRAME[0],
        "frame_height": FRAME[1],
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> None:
    PORTRAITS.mkdir(parents=True, exist_ok=True)
    SHEETS.mkdir(parents=True, exist_ok=True)
    expressions = {}
    for expression in ("calm", "happy", "low", "focus"):
        image = draw_portrait(expression)
        path = PORTRAITS / f"lin-cheng-{expression}.png"
        image.save(path)
        expressions[expression] = {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    hero = draw_portrait("calm").resize((1024, 1024), Image.Resampling.NEAREST)
    hero_path = PORTRAITS / "lin-cheng-hero.png"
    hero.save(hero_path)

    directions = {}
    for direction in DIRECTIONS:
        directions[direction] = {
            action: save_sheet(direction, action)
            for action in ANIMATIONS
        }
    idle_down = OUTPUT / "lin-cheng-map.png"
    sheet_path = SHEETS / "idle-down.webp"
    with Image.open(sheet_path) as sheet:
        sheet.crop((0, 0, FRAME[0], FRAME[1])).save(idle_down)

    manifest = {
        "schema_version": "rpg-whale-girl-assets-v1",
        "character_id": "char_lin_cheng",
        "name": "林澄",
        "creation_route": "native-pixel-authoring",
        "source_reference": "taskbook abstract blue-whale direction only",
        "original_pixel_used": True,
        "author": "Agent B / project-original pixel art",
        "license": "project-original",
        "palette": PALETTE,
        "logical_canvas": {"width": FRAME[0], "height": FRAME[1]},
        "runtime_display": {"width": 48, "height": 72},
        "hero_portrait": {
            "path": hero_path.relative_to(ROOT).as_posix(),
            "size": [1024, 1024],
            "bytes": hero_path.stat().st_size,
            "sha256": hashlib.sha256(hero_path.read_bytes()).hexdigest(),
        },
        "expressions": expressions,
        "directions": directions,
        "static_fallback": {
            "path": idle_down.relative_to(ROOT).as_posix(),
            "size": [FRAME[0], FRAME[1]],
            "bytes": idle_down.stat().st_size,
            "sha256": hashlib.sha256(idle_down.read_bytes()).hexdigest(),
        },
    }
    manifest_path = OUTPUT / "whale-girl-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(manifest_path)


if __name__ == "__main__":
    main()
