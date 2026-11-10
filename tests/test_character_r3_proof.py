from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "art-source" / "character-v2" / "r3-proof"
REPORT = (
    ROOT
    / "docs"
    / "character-art-v2"
    / "r3-proof-map-evidence.json"
)
DIRECTIONS = ("down", "left", "right", "up")


def test_r3_base_and_overlay_sources_are_traceable() -> None:
    source = json.loads(
        (PROOF / "base-source.json").read_text(encoding="utf-8")
    )
    assert source["source_pack"]["id"] == "modern_interiors"
    assert source["source_pack"]["license_status"] == (
        "project-authorized"
    )
    assert source["base_asset"] == {
        "body": "Body_2_48x48.png",
        "outfit": "Outfit_17_Nurse_48x48.png",
        "hair": "Hairstyle_4_48x48_1.png",
        "eyes": "Eyes_2_48x48.png",
    }
    assert set(source["members"]) == {
        "body",
        "outfit",
        "hair",
        "eyes",
    }
    for member in source["members"].values():
        assert len(member["sha256"]) == 64
    assert set(source["crop"]) == set(DIRECTIONS)
    for direction in DIRECTIONS:
        path = PROOF / "source" / f"{direction}.png"
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == (
            source["final_source_sha256"][direction]
        )


def test_r3_sprite_is_runtime_ready() -> None:
    with Image.open(PROOF / "sprite-4dir.png") as sheet:
        assert sheet.size == (256, 96)
        assert sheet.mode == "RGBA"
        colors = set(sheet.get_flattened_data())
        assert 16 <= len(colors) <= 24
        assert {pixel[3] for pixel in colors} == {0, 255}
        frames = [
            sheet.crop((index * 64, 0, (index + 1) * 64, 96))
            for index in range(4)
        ]
        for index, direction in enumerate(DIRECTIONS):
            source = Image.open(
                PROOF / "source" / f"{direction}.png"
            ).convert("RGBA")
            assert source.tobytes() == frames[index].tobytes()
            bbox = source.getbbox()
            assert bbox is not None
            assert 32 <= bbox[2] - bbox[0] <= 40
            assert 64 <= bbox[3] - bbox[1] <= 72
            assert bbox[0] >= 3
            assert bbox[1] >= 3
            assert bbox[2] <= 61
            assert bbox[3] <= 93

        assert frames[1].tobytes() != frames[2].tobytes()
        assert frames[1].tobytes() != ImageOps.mirror(frames[2]).tobytes()

    with Image.open(PROOF / "sprite-down-1x.png") as down:
        assert down.size == (64, 96)
        assert down.tobytes() == frames[0].tobytes()

    with Image.open(PROOF / "sprite-preview-4x.png") as preview:
        assert preview.size == (256, 384)
        expected = frames[0].resize(
            (256, 384),
            Image.Resampling.NEAREST,
        )
        assert preview.tobytes() == expected.tobytes()

    with Image.open(PROOF / "silhouette-4dir.png") as silhouette:
        assert silhouette.size == (256, 96)
        assert silhouette.mode == "RGB"
        for index in range(4):
            shape = silhouette.crop(
                (index * 64, 0, (index + 1) * 64, 96)
            )
            assert ImageChops.difference(
                shape,
                Image.new("RGB", (64, 96), "#F7F4E9"),
            ).getbbox() is not None

    metrics = json.loads(
        (PROOF / "metrics.json").read_text(encoding="utf-8")
    )
    assert metrics["creation_route"] == "authorized-base-overlay"
    assert metrics["frame_size"] == [64, 96]
    assert metrics["runtime_size"] == [48, 72]
    assert metrics["baseline_y"] == 88
    assert metrics["alpha_values"] == [0, 255]
    assert metrics["semi_transparent_pixels"] == 0
    assert metrics["anti_aliased_pixels"] == 0


def test_r3_real_map_evidence() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["schema_version"] == "rpg-character-r3-map-evidence-v1"
    assert report["page"] == "web/index.html"
    assert len(report["evidence"]) == 2
    expected = {
        "desktop": [1440, 1000],
        "mobile": [390, 844],
    }
    for evidence in report["evidence"]:
        assert evidence["size"] == expected[evidence["viewport"]]
        assert evidence["runtime_display"] == [48, 72]
        assert evidence["console_errors"] == []
        player = evidence["player_bounds"]
        stage = evidence["stage_bounds"]
        assert player["width"] == 48
        assert player["height"] == 72
        assert stage["left"] <= player["left"] < player["right"] <= stage["right"]
        assert stage["top"] <= player["top"] < player["bottom"] <= stage["bottom"]
        with Image.open(ROOT / evidence["path"]) as screenshot:
            assert screenshot.size == tuple(
                expected[evidence["viewport"]]
            )
