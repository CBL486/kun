from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
GATE_ROOT = ROOT / "art-source" / "character-v2" / "gate-a-r1"
REPORT = (
    ROOT
    / "docs"
    / "character-art-v2"
    / "gate-a-r1-map-evidence.json"
)
STYLES = ("a", "b", "c")
DIRECTIONS = ("down", "left", "right", "up")


def frame(sheet: Image.Image, index: int) -> Image.Image:
    return sheet.crop((index * 64, 0, (index + 1) * 64, 96))


def test_gate_a_r1_packages_are_native_pixel_assets() -> None:
    for style in STYLES:
        package = GATE_ROOT / style
        required = {
            "hero-reference.png",
            "sprite-4dir.png",
            "sprite-down-1x.png",
            "sprite-preview-4x.png",
            "palette.png",
            "metrics.json",
            "map-desktop.png",
            "map-mobile.png",
        }
        assert required.issubset(
            {path.name for path in package.iterdir() if path.is_file()}
        ), style

        with Image.open(package / "hero-reference.png") as hero:
            assert hero.size == (1024, 1024)
            assert hero.mode == "RGB"
            assert "TC260:AIGC" in hero.info.get(
                "XML:com.adobe.xmp",
                "",
            )

        with Image.open(package / "sprite-4dir.png") as sheet:
            assert sheet.size == (256, 96)
            assert sheet.mode == "RGBA"
            colors = set(sheet.get_flattened_data())
            assert 16 <= len(colors) <= 24
            assert {pixel[3] for pixel in colors} == {0, 255}
            assert sheet.getbbox() is not None

            frames = [frame(sheet, index) for index in range(4)]
            for candidate in frames:
                assert candidate.getbbox() is not None
                bbox = candidate.getbbox()
                assert bbox[0] >= 3
                assert bbox[1] >= 3
                assert bbox[2] <= 61
                assert bbox[3] <= 93

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
        assert metrics["sheet_size"] == [256, 96]
        assert metrics["frame_size"] == [64, 96]
        assert metrics["runtime_size"] == [48, 72]
        assert metrics["colors"] == len(colors)
        assert metrics["alpha_values"] == [0, 255]
        assert metrics["directions"] == list(DIRECTIONS)
        assert metrics["semi_transparent_pixels"] == 0
        assert metrics["anti_aliased_pixels"] == 0


def test_gate_a_r1_map_screenshots_cover_every_direction() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["page"] == "web/index.html"
    assert report["runtime_display"] == [48, 72]
    assert len(report["evidence"]) == 24

    expected_views = {
        "desktop": [1440, 1000],
        "mobile": [390, 844],
    }
    seen = set()
    for item in report["evidence"]:
        key = (item["style"], item["viewport"], item["direction"])
        seen.add(key)
        assert item["size"] == expected_views[item["viewport"]]
        assert item["runtime_display"] == [48, 72]
        assert item["background_size"] == "48px 72px"
        assert item["image_rendering"] == "pixelated"
        assert item["console_errors"] == []

        player = item["player_bounds"]
        stage = item["stage_bounds"]
        assert player["width"] == 48
        assert player["height"] == 72
        assert stage["left"] <= player["left"] < player["right"] <= stage["right"]
        assert stage["top"] <= player["top"] < player["bottom"] <= stage["bottom"]

        with Image.open(ROOT / item["path"]) as screenshot:
            assert screenshot.size == tuple(expected_views[item["viewport"]])

    assert seen == {
        (style, viewport, direction)
        for style in STYLES
        for viewport in expected_views
        for direction in DIRECTIONS
    }
