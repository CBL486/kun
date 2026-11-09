from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


ROOT = Path(__file__).resolve().parents[1]
GATE_ROOT = ROOT / "art-source" / "character-v2" / "gate-a-r2"
REPORT = (
    ROOT
    / "docs"
    / "character-art-v2"
    / "gate-a-r2-map-evidence.json"
)
STYLES = ("a", "b", "c")
DIRECTIONS = ("down", "left", "right", "up")


def frame(sheet: Image.Image, index: int) -> Image.Image:
    return sheet.crop((index * 64, 0, (index + 1) * 64, 96))


def rgba(value: str) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
        int(value[6:8], 16) if len(value) == 8 else 255,
    )


def matrix_image(style: str, direction: str) -> Image.Image:
    source = GATE_ROOT / style / "source"
    data = json.loads(
        (source / "palette.json").read_text(encoding="utf-8")
    )
    rows = (source / f"{direction}.txt").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(rows) == 96
    assert all(len(row) == 64 for row in rows)
    image = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, symbol in enumerate(row):
            if symbol != ".":
                pixels[x, y] = rgba(data["symbols"][symbol])
    return image


def test_00b_contracts_are_frozen() -> None:
    identity = (
        ROOT / "docs" / "character-art-v2" / "identity-lock.md"
    )
    asset_map = (
        ROOT / "docs" / "character-art-v2" / "asset-map.json"
    )
    assert identity.is_file()
    data = json.loads(asset_map.read_text(encoding="utf-8"))
    assert data["logical_canvas"]["width"] == 64
    assert data["logical_canvas"]["height"] == 96
    assert data["runtime_display"]["width"] == 48
    assert data["runtime_display"]["height"] == 72
    assert set(data["directions"]) == set(DIRECTIONS)
    assert set(data["actions"]) == {
        "idle",
        "walk",
        "turn",
        "stop",
        "study",
        "sit",
        "talk",
    }
    assert set(data["expressions"]) == {
        "calm",
        "happy",
        "low",
        "focus",
        "tired",
        "curious",
        "shy",
    }


def test_gate_a_r2_uses_manual_pixel_matrices() -> None:
    for style in STYLES:
        package = GATE_ROOT / style
        required = {
            "hero-reference.png",
            "sprite-4dir.png",
            "sprite-down-1x.png",
            "sprite-preview-4x.png",
            "silhouette-4dir.png",
            "palette.png",
            "metrics.json",
            "map-desktop.png",
            "map-mobile.png",
        }
        assert required.issubset(
            {path.name for path in package.iterdir() if path.is_file()}
        )

        with Image.open(package / "hero-reference.png") as hero:
            assert hero.size == (1024, 1024)
            assert hero.mode == "RGB"
            assert "TC260:AIGC" not in hero.info.get(
                "XML:com.adobe.xmp",
                "",
            )

        with Image.open(package / "sprite-4dir.png") as sheet:
            assert sheet.size == (256, 96)
            assert sheet.mode == "RGBA"
            colors = set(sheet.get_flattened_data())
            assert 16 <= len(colors) <= 24
            assert {pixel[3] for pixel in colors} == {0, 255}
            frames = [frame(sheet, index) for index in range(4)]

            for index, direction in enumerate(DIRECTIONS):
                source = package / "source" / f"{direction}.png"
                with Image.open(source) as indexed:
                    assert indexed.mode == "P"
                    assert indexed.convert("RGBA").tobytes() == (
                        frames[index].tobytes()
                    )
                assert matrix_image(style, direction).tobytes() == (
                    frames[index].tobytes()
                )

            with Image.open(package / "sprite-down-1x.png") as down:
                assert down.size == (64, 96)
                assert down.tobytes() == frames[0].tobytes()

            with Image.open(package / "sprite-preview-4x.png") as preview:
                assert preview.size == (256, 384)
                expected = frames[0].resize(
                    (256, 384),
                    Image.Resampling.NEAREST,
                )
                assert preview.tobytes() == expected.tobytes()

            left = frames[DIRECTIONS.index("left")]
            right = frames[DIRECTIONS.index("right")]
            assert left.tobytes() != right.tobytes()
            assert left.tobytes() != ImageOps.mirror(right).tobytes()

        metrics = json.loads(
            (package / "metrics.json").read_text(encoding="utf-8")
        )
        assert metrics["creation_route"] == "manual-pixel-matrix"
        assert metrics["sheet_size"] == [256, 96]
        assert metrics["frame_size"] == [64, 96]
        assert metrics["runtime_size"] == [48, 72]
        assert metrics["alpha_values"] == [0, 255]
        assert metrics["semi_transparent_pixels"] == 0
        assert metrics["anti_aliased_pixels"] == 0
        for direction in metrics["frames"]:
            assert 32 <= direction["character_width"] <= 40
            assert 64 <= direction["character_height"] <= 72


def test_three_directions_have_distinct_silhouettes() -> None:
    silhouettes = {}
    for style in STYLES:
        with Image.open(
            GATE_ROOT / style / "silhouette-4dir.png"
        ) as image:
            silhouettes[style] = image.convert("RGB")
            assert (
                GATE_ROOT
                / style
                / f"silhouette-{DIRECTIONS[0]}.png"
            ).is_file()
            hashes = {
                hashlib.sha256(
                    frame(image, index).tobytes()
                ).hexdigest()
                for index in range(4)
            }
            assert len(hashes) == 4

    for first, second in (("a", "b"), ("a", "c"), ("b", "c")):
        changed = ImageChops.difference(
            silhouettes[first],
            silhouettes[second],
        )
        assert changed.getbbox() is not None
        assert sum(value != 0 for value in changed.get_flattened_data()) > 100


def test_gate_a_r2_map_evidence_covers_all_directions() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["schema_version"] == (
        "rpg-character-gate-a-r2-map-evidence-v1"
    )
    assert report["page"] == "web/index.html"
    assert report["runtime_display"] == [48, 72]
    assert len(report["evidence"]) == 24

    expected_views = {
        "desktop": [1440, 1000],
        "mobile": [390, 844],
    }
    seen = set()
    for item in report["evidence"]:
        seen.add((item["style"], item["viewport"], item["direction"]))
        assert item["size"] == expected_views[item["viewport"]]
        assert item["background_size"] == "48px 72px"
        assert item["image_rendering"] == "pixelated"
        assert item["console_errors"] == []
        player = item["player_bounds"]
        stage = item["stage_bounds"]
        assert player["width"] == 48
        assert player["height"] == 72
        assert stage["left"] <= player["left"] < player["right"] <= stage["right"]
        assert stage["top"] <= player["top"] < player["bottom"] <= stage["bottom"]

    assert seen == {
        (style, viewport, direction)
        for style in STYLES
        for viewport in expected_views
        for direction in DIRECTIONS
    }
