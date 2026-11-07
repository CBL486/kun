from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets" / "characters" / "whale-girl"


def manifest() -> dict:
    return json.loads(
        (ASSET / "whale-girl-manifest.json").read_text(encoding="utf-8")
    )


def test_whale_girl_manifest_has_all_required_deliverables() -> None:
    data = manifest()
    assert data["character_id"] == "char_lin_cheng"
    assert data["creation_route"] == "native-pixel-authoring"
    assert data["license"] == "project-original"
    assert data["original_pixel_used"] is True
    assert set(data["expressions"]) == {"calm", "happy", "low", "focus"}
    assert set(data["directions"]) == {"down", "left", "right", "up"}
    for direction in data["directions"].values():
        assert set(direction) == {"idle", "walk", "turn", "stop", "study"}
        assert direction["idle"]["frames"] == 4
        assert 4 <= direction["walk"]["frames"] <= 8
        assert direction["turn"]["frames"] >= 2
        assert direction["stop"]["frames"] >= 2
        assert direction["study"]["frames"] >= 2


def test_whale_girl_files_match_manifest_and_alpha_contract() -> None:
    data = manifest()
    entries = [
        data["hero_portrait"],
        data["static_fallback"],
        *data["expressions"].values(),
    ]
    for direction in data["directions"].values():
        entries.extend(direction.values())
    for entry in entries:
        path = ROOT / entry["path"]
        assert path.is_file(), path
        assert path.stat().st_size == entry["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]

    with Image.open(ROOT / data["hero_portrait"]["path"]) as hero:
        assert hero.size == (1024, 1024)
        assert hero.mode == "RGBA"
        assert hero.getextrema()[3][0] == 0
    for expression in data["expressions"].values():
        with Image.open(ROOT / expression["path"]) as portrait:
            assert portrait.size == (512, 512)
            assert portrait.mode == "RGBA"
            assert portrait.getextrema()[3][0] == 0


def test_each_direction_has_distinct_walk_frames() -> None:
    data = manifest()
    for direction, sheets in data["directions"].items():
        walk = sheets["walk"]
        with Image.open(ROOT / walk["path"]) as sheet:
            assert sheet.size == (
                walk["frames"] * walk["frame_width"],
                walk["frame_height"],
            )
            frames = [
                sheet.crop(
                    (
                        index * walk["frame_width"],
                        0,
                        (index + 1) * walk["frame_width"],
                        walk["frame_height"],
                    )
                ).tobytes()
                for index in range(walk["frames"])
            ]
        assert len(set(frames)) >= 4, direction


def test_player_is_server_state_driven_and_dead_move_css_is_removed() -> None:
    javascript = (ROOT / "web" / "character-player.js").read_text(
        encoding="utf-8"
    )
    css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
    app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    assert "presence.facing" in javascript
    assert "presence.moving" in javascript
    assert "turn" in javascript
    assert "stop" in javascript
    assert "qingheCharacterPlayer" in app
    assert "data-move" not in css
    assert ".map-controls" not in css
    assert ".map-move-hint" not in css
