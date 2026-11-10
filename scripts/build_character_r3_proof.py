"""Build the R3 four-direction proof from the licensed Modern Interiors base."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(
    os.environ.get(
        "B75_SOURCE_ROOT",
        str(ROOT / "out" / "b75-source-extracted"),
    )
).resolve()
SOURCE_PACK = SOURCE_ROOT / "modern_interiors"
MEMBERS = {
    "body": (
        "Modern_Interiors/2_Characters/Character_Generator/"
        "Bodies/48x48/Body_2_48x48.png"
    ),
    "outfit": (
        "Modern_Interiors/2_Characters/Character_Generator/"
        "Outfits/48x48/Outfit_17_Nurse_48x48.png"
    ),
    "hair": (
        "Modern_Interiors/2_Characters/Character_Generator/"
        "Hairstyles/48x48/Hairstyle_4_48x48_1.png"
    ),
    "eyes": (
        "Modern_Interiors/2_Characters/Character_Generator/"
        "Eyes/48x48/Eyes_2_48x48.png"
    ),
}
SOURCE_FILES = {
    name: SOURCE_PACK / member
    for name, member in MEMBERS.items()
}
OUTPUT = ROOT / "art-source" / "character-v2" / "r3-proof"
FRAME = (64, 96)
RUNTIME = (48, 72)
BASELINE_Y = 88
DIRECTIONS = ("down", "left", "right", "up")
SOURCE_FRAMES = {
    "down": (3, (144, 0, 192, 96)),
    "left": (2, (96, 0, 144, 96)),
    "right": (0, (0, 0, 48, 96)),
    "up": (1, (48, 0, 96, 96)),
}

COLOR_MAP = {
    (171, 103, 54, 255): (8, 40, 91, 255),
    (179, 123, 63, 255): (13, 65, 137, 255),
    (204, 150, 89, 255): (35, 105, 199, 255),
    (58, 58, 80, 255): (4, 16, 31, 255),
    (70, 70, 94, 255): (7, 28, 58, 255),
    (86, 89, 114, 255): (15, 50, 92, 255),
    (108, 110, 133, 255): (21, 76, 132, 255),
    (255, 203, 176, 255): (243, 201, 186, 255),
    (246, 174, 159, 255): (226, 161, 154, 255),
    (246, 151, 132, 255): (230, 145, 162, 255),
    (225, 179, 155, 255): (196, 125, 121, 255),
    (166, 182, 233, 255): (10, 42, 89, 255),
    (193, 210, 238, 255): (21, 76, 132, 255),
    (248, 248, 248, 255): (246, 255, 255, 255),
    (86, 141, 97, 255): (57, 218, 232, 255),
}
PALETTE_NAMES = {
    (4, 16, 31, 255): "outline",
    (7, 28, 58, 255): "coat_dark",
    (8, 40, 91, 255): "hair_mid",
    (9, 35, 78, 255): "coat",
    (10, 42, 89, 255): "coat_dark_2",
    (13, 65, 137, 255): "hair",
    (7, 31, 74, 255): "hair_dark",
    (15, 50, 92, 255): "coat_light",
    (24, 120, 146, 255): "fin_dark",
    (35, 105, 199, 255): "hair_light",
    (57, 218, 232, 255): "fin_mid",
    (84, 215, 235, 255): "hair_tip",
    (196, 125, 121, 255): "skin_deep",
    (196, 243, 250, 255): "apron_shadow",
    (197, 243, 250, 255): "apron_shadow",
    (216, 249, 253, 255): "apron_mid",
    (21, 76, 132, 255): "coat_highlight",
    (221, 179, 87, 255): "gold",
    (226, 161, 154, 255): "skin_shadow",
    (230, 252, 255, 255): "apron",
    (230, 145, 162, 255): "blush",
    (243, 201, 186, 255): "skin",
    (246, 255, 255, 255): "white",
}


def rgba(value: str) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4)) + (255,)


def put_rows(
    image: Image.Image,
    rows: list[tuple[int, int, int, tuple[int, int, int, int]]],
) -> None:
    pixels = image.load()
    for y, start, end, color in rows:
        for x in range(start, end + 1):
            pixels[x, y] = color


def recolor_base(frame: Image.Image) -> Image.Image:
    result = Image.new("RGBA", FRAME, (0, 0, 0, 0))
    source_pixels = frame.load()
    target_pixels = result.load()
    for y in range(frame.height):
        for x in range(frame.width):
            source = source_pixels[x, y]
            if source[3] == 0:
                continue
            target_x = x + 8
            target_y = y - 8
            if 12 <= target_x <= 51 and 18 <= target_y <= 88:
                target_pixels[target_x, target_y] = COLOR_MAP[source]
    return result


def add_long_hair(image: Image.Image, direction: str) -> None:
    outline = rgba("#04101F")
    dark = rgba("#071F4A")
    mid = rgba("#0D4189")
    light = rgba("#2469C7")
    tip = rgba("#54D7EB")
    if direction in {"down", "up"}:
        left = [
            (42, 21, 22, outline),
            (43, 20, 23, dark),
            (44, 20, 24, dark),
            (45, 21, 24, mid),
            (46, 21, 25, mid),
            (47, 22, 25, dark),
            (48, 22, 25, dark),
            (49, 23, 25, mid),
            (50, 23, 26, mid),
            (51, 24, 26, dark),
            (52, 24, 27, dark),
            (53, 25, 27, mid),
            (54, 25, 28, mid),
            (55, 26, 28, dark),
            (56, 26, 29, dark),
            (57, 27, 29, mid),
            (58, 27, 30, mid),
            (59, 28, 30, dark),
            (60, 28, 31, dark),
            (61, 29, 31, mid),
            (62, 29, 32, mid),
            (63, 30, 32, dark),
            (64, 30, 33, dark),
            (65, 31, 33, mid),
            (66, 31, 34, tip),
            (67, 32, 34, tip),
        ]
        right = [
            (42, 41, 42, outline),
            (43, 40, 43, dark),
            (44, 40, 43, dark),
            (45, 39, 43, mid),
            (46, 39, 43, mid),
            (47, 39, 42, dark),
            (48, 39, 42, dark),
            (49, 39, 42, mid),
            (50, 38, 42, mid),
            (51, 38, 42, dark),
            (52, 38, 42, dark),
            (53, 37, 42, mid),
            (54, 37, 42, mid),
            (55, 37, 42, dark),
            (56, 37, 42, dark),
            (57, 37, 42, mid),
            (58, 37, 42, mid),
            (59, 37, 42, dark),
            (60, 37, 42, dark),
            (61, 37, 42, mid),
            (62, 37, 42, mid),
            (63, 38, 42, dark),
            (64, 38, 42, dark),
            (65, 38, 42, mid),
            (66, 39, 42, tip),
            (67, 39, 42, tip),
        ]
    elif direction == "left":
        left = [(y, 23, 26, dark if y < 59 else mid) for y in range(42, 68)]
        right = [
            (y, 40, 45, dark if y < 54 else mid)
            for y in range(42, 70)
        ]
    else:
        left = [
            (y, 18, 23, dark if y < 54 else mid)
            for y in range(42, 70)
        ]
        right = [(y, 38, 41, dark if y < 59 else mid) for y in range(42, 68)]
    put_rows(image, left + right)
    if direction == "up":
        put_rows(
            image,
            [
                (64, 25, 38, dark),
                (65, 24, 39, mid),
                (66, 25, 38, mid),
                (67, 26, 37, dark),
                (68, 27, 36, mid),
                (69, 28, 35, dark),
                (70, 29, 34, tip),
            ],
        )


def add_fins(image: Image.Image, direction: str) -> None:
    outline = rgba("#04101F")
    dark = rgba("#127DA0")
    mid = rgba("#32D5E8")
    pale = rgba("#D8FFFF")
    left = [
        (21, 20, 22, outline),
        (22, 17, 22, outline),
        (23, 15, 22, dark),
        (24, 14, 21, mid),
        (25, 14, 21, mid),
        (26, 14, 22, mid),
        (27, 15, 22, dark),
        (28, 16, 21, dark),
        (29, 17, 21, mid),
        (30, 18, 21, mid),
        (31, 18, 20, dark),
        (32, 19, 20, outline),
    ]
    right = [
        (21, 41, 43, outline),
        (22, 41, 46, outline),
        (23, 41, 48, dark),
        (24, 42, 49, mid),
        (25, 42, 49, mid),
        (26, 41, 49, mid),
        (27, 41, 48, dark),
        (28, 42, 47, dark),
        (29, 42, 46, mid),
        (30, 42, 45, mid),
        (31, 43, 45, dark),
        (32, 43, 44, outline),
    ]
    if direction == "left":
        put_rows(image, left)
    elif direction == "right":
        put_rows(image, right)
    else:
        put_rows(image, left + right)
    # Two deliberate highlight pixels per visible fin.
    image.putpixel((18, 25), pale)
    image.putpixel((19, 26), pale)
    if direction != "left":
        image.putpixel((46, 25), pale)
        image.putpixel((45, 26), pale)


def add_tail(image: Image.Image, direction: str) -> None:
    outline = rgba("#04101F")
    dark = rgba("#0B357F")
    mid = rgba("#1E69D4")
    light = rgba("#63E1EF")
    if direction == "right":
        rows = [
            (61, 19, 22, outline),
            (62, 17, 24, dark),
            (63, 16, 25, mid),
            (64, 16, 25, mid),
            (65, 17, 24, dark),
            (66, 18, 23, mid),
            (67, 17, 22, dark),
            (68, 15, 22, mid),
            (69, 14, 21, mid),
            (70, 14, 20, dark),
            (71, 15, 20, outline),
        ]
    else:
        rows = [
            (61, 40, 43, outline),
            (62, 38, 46, dark),
            (63, 37, 48, mid),
            (64, 37, 48, mid),
            (65, 38, 47, dark),
            (66, 39, 46, mid),
            (67, 40, 46, dark),
            (68, 40, 50, mid),
            (69, 41, 51, mid),
            (70, 42, 51, dark),
            (71, 43, 50, outline),
        ]
    put_rows(image, rows)
    image.putpixel((41 if direction != "right" else 18, 66), light)


def add_apron_and_eye_details(image: Image.Image, direction: str) -> None:
    white = rgba("#F7FFFF")
    pale = rgba("#C5F6FA")
    navy = rgba("#0A2A59")
    cyan = rgba("#58DEEB")
    eye_dark = rgba("#042137")
    eye_light = rgba("#73F2FF")
    if direction == "down":
        # Maid apron and collar; the base legs and arms remain untouched.
        put_rows(
            image,
            [
                (55, 29, 35, white),
                (56, 27, 37, white),
                (57, 26, 38, white),
                (58, 25, 39, white),
                (59, 25, 39, white),
                (60, 25, 39, white),
                (61, 25, 39, pale),
                (62, 25, 39, pale),
                (63, 26, 38, white),
                (64, 27, 37, white),
                (65, 28, 36, pale),
            ],
        )
        # Larger blue eyes, consistent with the approved reference.
        put_rows(
            image,
            [
                (53, 24, 27, eye_dark),
                (54, 24, 27, eye_dark),
                (54, 25, 26, eye_light),
                (53, 35, 38, eye_dark),
                (54, 35, 38, eye_dark),
                (54, 36, 37, eye_light),
            ],
        )
        image.putpixel((31, 54), rgba("#DCA49B"))
        image.putpixel((32, 56), rgba("#A05261"))
    elif direction == "up":
        put_rows(
            image,
            [
                (56, 27, 36, navy),
                (57, 25, 38, navy),
                (58, 24, 39, navy),
                (59, 24, 39, navy),
                (60, 24, 39, navy),
                (61, 25, 38, cyan),
            ],
        )
        image.putpixel((31, 59), rgba("#E2B65D"))
    else:
        face_x = 23 if direction == "left" else 37
        put_rows(
            image,
            [
                (53, face_x, face_x + 2, eye_dark),
                (54, face_x, face_x + 2, eye_dark),
                (54, face_x + 1, face_x + 1, eye_light),
                (63, 25 if direction == "left" else 31, 32, pale),
                (64, 25 if direction == "left" else 31, 36, pale),
                (65, 26 if direction == "left" else 32, 37, white),
            ],
        )


def quantize_palette(image: Image.Image) -> Image.Image:
    colors = list(PALETTE_NAMES)
    result = Image.new("RGBA", image.size, (0, 0, 0, 0))
    source = image.load()
    target = result.load()
    for y in range(image.height):
        for x in range(image.width):
            pixel = source[x, y]
            if pixel[3] == 0:
                continue
            nearest = min(
                colors,
                key=lambda candidate: (
                    (pixel[0] - candidate[0]) ** 2
                    + (pixel[1] - candidate[1]) ** 2
                    + (pixel[2] - candidate[2]) ** 2
                ),
            )
            target[x, y] = nearest
    return result


def build_frames() -> dict[str, Image.Image]:
    layers = {
        name: Image.open(path).convert("RGBA")
        for name, path in SOURCE_FILES.items()
    }
    frames = {}
    for direction in DIRECTIONS:
        _, box = SOURCE_FRAMES[direction]
        composed = Image.new("RGBA", (48, 96), (0, 0, 0, 0))
        for name in ("body", "outfit", "hair", "eyes"):
            composed.alpha_composite(layers[name].crop(box))
        frame = recolor_base(composed)
        add_long_hair(frame, direction)
        add_fins(frame, direction)
        add_tail(frame, direction)
        add_apron_and_eye_details(frame, direction)
        frame = quantize_palette(frame)
        frame.save(OUTPUT / "source" / f"{direction}.png", optimize=True)
        frames[direction] = frame
    return frames


def frame_metrics(frame: Image.Image) -> dict:
    colors = sorted(set(frame.get_flattened_data()))
    opaque = [
        (index % FRAME[0], index // FRAME[0])
        for index, pixel in enumerate(frame.get_flattened_data())
        if pixel[3] == 255
    ]
    bbox = [
        min(x for x, _ in opaque),
        min(y for _, y in opaque),
        max(x for x, _ in opaque) + 1,
        max(y for _, y in opaque) + 1,
    ]
    return {
        "bbox": bbox,
        "character_width": bbox[2] - bbox[0],
        "character_height": bbox[3] - bbox[1],
        "sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
    }


def silhouette(sheet: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", sheet.size, "#F7F4E9")
    black = Image.new("RGB", sheet.size, "#081118")
    canvas.paste(black, (0, 0), sheet.getchannel("A"))
    return canvas


def main() -> None:
    missing = [
        str(path)
        for path in SOURCE_FILES.values()
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(
            f"licensed Modern Interiors base not found: {missing}"
        )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "source").mkdir(exist_ok=True)
    frames = build_frames()
    sheet = Image.new("RGBA", (256, 96), (0, 0, 0, 0))
    for index, direction in enumerate(DIRECTIONS):
        sheet.alpha_composite(frames[direction], (index * 64, 0))
    sheet.save(OUTPUT / "sprite-4dir.png", optimize=True)
    frames["down"].save(OUTPUT / "sprite-down-1x.png", optimize=True)
    frames["down"].resize((256, 384), Image.Resampling.NEAREST).save(
        OUTPUT / "sprite-preview-4x.png",
        optimize=True,
    )
    silhouette(sheet).save(
        OUTPUT / "silhouette-4dir.png",
        optimize=True,
    )
    payload = {
        "schema_version": "rpg-character-r3-base-source-v1",
        "source_pack": {
            "id": "modern_interiors",
            "name": "Modern Interiors",
            "archive": "2104261.zip",
            "archive_sha256": (
                "8FE691CE84881936F6B7A25E15A9847A1BFD555D21984A99939EA930A52C4C91"
            ),
            "license_status": "project-authorized",
        },
        "members": {
            name: {
                "path": MEMBERS[name],
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "role": {
                    "body": "adult female body and standing proportions",
                    "outfit": "base outfit silhouette",
                    "hair": "base hair silhouette",
                    "eyes": "base face alignment",
                }[name],
            }
            for name, path in SOURCE_FILES.items()
        },
        "crop": {
            direction: {
                "source_frame": SOURCE_FRAMES[direction][0],
                "box_48x96": list(SOURCE_FRAMES[direction][1]),
            }
            for direction in DIRECTIONS
        },
        "base_asset": {
            "body": "Body_2_48x48.png",
            "outfit": "Outfit_17_Nurse_48x48.png",
            "hair": "Hairstyle_4_48x48_1.png",
            "eyes": "Eyes_2_48x48.png",
        },
        "base_role": (
            "adult female body, face proportions and neutral standing pose; "
            "hair, outfit colors, fins, tail and apron are Lin Cheng overlays"
        ),
        "edits": [
            "crop four source frames",
            "compose licensed body, outfit, hair and eye layers",
            "recolor the composed 15-color base",
            "center 48x96 base frames in a 64x96 canvas",
            "shift bottom to y=88 baseline",
            "add long hair, fin ears, white apron and whale tail overlay pixels",
            "do not re-create body or legs with geometry",
        ],
        "final_source_sha256": {
            direction: hashlib.sha256(
                (OUTPUT / "source" / f"{direction}.png").read_bytes()
            ).hexdigest()
            for direction in DIRECTIONS
        },
    }
    (OUTPUT / "base-source.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    metrics = {
        "schema_version": "rpg-character-r3-proof-metrics-v1",
        "sheet_size": list(sheet.size),
        "frame_size": list(FRAME),
        "runtime_size": list(RUNTIME),
        "baseline_y": BASELINE_Y,
        "creation_route": "authorized-base-overlay",
        "colors": len(set(sheet.get_flattened_data())),
        "alpha_values": sorted(
            {pixel[3] for pixel in sheet.get_flattened_data()}
        ),
        "semi_transparent_pixels": sum(
            0 < pixel[3] < 255 for pixel in sheet.get_flattened_data()
        ),
        "anti_aliased_pixels": sum(
            0 < pixel[3] < 255 for pixel in sheet.get_flattened_data()
        ),
        "directions": {
            direction: frame_metrics(frame)
            for direction, frame in frames.items()
        },
    }
    (OUTPUT / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
