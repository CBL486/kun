from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets"


def _manifest() -> dict:
    return json.loads(
        (ASSET_ROOT / "manifest.json").read_text(encoding="utf-8")
    )


def test_manifest_covers_maps_buildings_characters_and_ui() -> None:
    assets = _manifest()["assets"]
    ids = {item["id"] for item in assets}
    required = {
        "town_map_world",
        "building_dorm",
        "building_classroom",
        "building_library",
        "building_canteen",
        "building_shop",
        "building_river",
        "interior_dorm",
        "interior_classroom",
        "interior_library",
        "interior_canteen",
        "interior_shop",
        "interior_river",
        "portrait_lin_cheng",
        "portrait_chen_lan",
        "portrait_su_wan",
        "portrait_gao_yuan",
        "portrait_gu_yan",
        "character_lin_cheng",
        "spine_lin_cheng",
        "icon_map",
        "icon_character",
        "icon_timeline",
        "icon_chat",
        "icon_diary",
        "icon_memory",
        "icon_settings",
        "icon_open",
        "icon_closed",
    }
    assert required <= ids


def test_manifest_checksums_and_files_match() -> None:
    for asset in _manifest()["assets"]:
        assert asset["exports"]
        for export in asset["exports"]:
            path = ROOT / export["path"]
            assert path.is_file(), path
            assert path.stat().st_size == export["bytes"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == export["sha256"]


def test_assets_are_authorized_and_raw_source_not_committed() -> None:
    manifest = _manifest()
    assert manifest["authorization"]["status"] == "project-authorized"
    assert manifest["source_packs"]
    assert all(pack["archive_sha256"] for pack in manifest["source_packs"])
    for asset in manifest["assets"]:
        assert asset["license_status"] in {
            "project-authorized",
            "commercial-licensed",
        }
        assert asset["raw_source_included"] is False
        assert asset["author"]
        assert asset["attribution"]
        assert asset["allowed_use"]
    forbidden = {".zip", ".rar", ".psd", ".aseprite"}
    assert not [
        path
        for path in ASSET_ROOT.rglob("*")
        if path.suffix.lower() in forbidden
    ]


def test_every_runtime_asset_is_composed_from_original_pixels() -> None:
    for asset in _manifest()["assets"]:
        if asset["kind"] == "spine_skeleton":
            assert asset["creation_route"] == "spine-json-composite"
        else:
            assert asset["creation_route"] == "source-composite", asset["id"]
        assert asset["original_pixel_used"] is True, asset["id"]
        assert asset["source_layers"], asset["id"]
        assert "重绘" not in asset["author"]
        for source_layer in asset["source_layers"]:
            assert source_layer["source_pack"]
            assert source_layer["source_archive"]
            assert source_layer["source_member"]
            assert len(source_layer["crop_box"]) == 4
            assert source_layer["original_pixel_used"] is True
            assert source_layer["modification_operation"]


def test_map_and_building_sources_match_supplied_packs() -> None:
    assets = {asset["id"]: asset for asset in _manifest()["assets"]}
    expected_members = {
        "building_dorm": "Modern_House_48x48.png",
        "building_classroom": "School_1.png",
        "building_library": "Japanese_House_48x48.png",
        "building_canteen": "Market_Medium_1.png",
        "building_shop": "Market_Small_1.png",
        "building_river": "Pier_1.png",
        "interior_dorm": "4_Bedroom_48x48.png",
        "interior_classroom": "5_Classroom_and_library_48x48.png",
        "interior_library": "5_Classroom_and_library_48x48.png",
        "interior_canteen": "12_Kitchen_48x48.png",
        "interior_shop": "16_Grocery_store_48x48.png",
        "interior_river": "Deep_Water_1_9.png",
        "portrait_lin_cheng": "New_Characters 48x48.png",
    }
    for asset_id, member in expected_members.items():
        layers = assets[asset_id]["source_layers"]
        assert any(member in item["source_member"] for item in layers)

    dorm_layers = assets["interior_dorm"]["source_layers"]
    assert any("inside_home_C.png" in item["source_member"] for item in dorm_layers)
    assert any(
        "Inside_home_B.png" in item["source_member"] for item in dorm_layers
    )

    title_map = assets["town_map_world"]
    assert title_map["source_packs"] == ["modern_exteriors"]
    assert title_map["canvas"] == [2400, 900]
    assert len(title_map["source_layers"]) >= 10


def test_interior_furniture_uses_complete_crops_and_stays_on_canvas() -> None:
    assets = {asset["id"]: asset for asset in _manifest()["assets"]}

    dorm_windows = [
        item["crop_box"]
        for item in assets["interior_dorm"]["source_layers"]
        if "1_Generic_48x48.png" in item["source_member"]
        and item["crop_box"][0] in {288, 384}
        and item["crop_box"][1] == 2080
    ]
    assert dorm_windows == [
        [288, 2080, 96, 72],
        [384, 2080, 96, 72],
    ]

    for asset_id in (
        "interior_dorm",
        "interior_classroom",
        "interior_library",
    ):
        assert any(
            item["crop_box"] == [0, 1056, 288, 96]
            for item in assets[asset_id]["source_layers"]
        )

    dorm_layers = assets["interior_dorm"]["source_layers"]
    rug = next(
        item
        for item in dorm_layers
        if "4_Bedroom_48x48.png" in item["source_member"]
        and item["crop_box"] == [0, 1056, 288, 96]
    )
    sofa_right_edges = [
        item["placement"]["destination"][0]
        + item["placement"]["trimmed_size"][0]
        for item in dorm_layers
        if "Inside_home_B.png" in item["source_member"]
        and item["crop_box"] in ([0, 48, 141, 144], [144, 51, 144, 141])
    ]
    assert sofa_right_edges
    assert rug["placement"]["destination"][0] >= max(sofa_right_edges)

    clipped_plant_crops = {
        (320, 0, 64, 64),
        (384, 0, 64, 64),
    }
    for asset_id in (
        "interior_dorm",
        "interior_classroom",
        "interior_library",
        "interior_canteen",
        "interior_shop",
    ):
        canvas_width, canvas_height = assets[asset_id]["canvas"]
        for item in assets[asset_id]["source_layers"]:
            assert tuple(item["crop_box"]) not in clipped_plant_crops
            placement = item.get("placement")
            if placement is None:
                continue
            x, y = placement["destination"]
            width, height = placement["trimmed_size"]
            assert x >= 0 and y >= 0
            assert x + width <= canvas_width
            assert y + height <= canvas_height


def test_spine_assets_and_runtime_are_complete() -> None:
    manifest = _manifest()
    asset = next(
        item for item in manifest["assets"] if item["id"] == "spine_lin_cheng"
    )
    assert asset["animations"] == ["idle", "walk"]
    assert asset["original_pixel_used"] is True
    assert asset["source_layers"]
    runtime = manifest["spine_runtime"]
    assert runtime["version"] == "4.3.13"
    assert (ROOT / runtime["file"]).is_file()
    assert (ROOT / runtime["license_file"]).is_file()


def test_runtime_canvases_match_supplied_asset_dimensions() -> None:
    for asset in _manifest()["assets"]:
        if asset["kind"] == "spine_skeleton":
            texture = ROOT / "assets" / "spine" / "lin_cheng.png"
            with Image.open(texture) as image:
                assert image.size == (128, 64)
            continue
        export = ROOT / asset["exports"][0]["path"]
        with Image.open(export) as image:
            assert list(image.size) == asset["canvas"], asset["id"]


def test_runtime_image_budget_is_small_enough() -> None:
    exports = {
        export["path"]: export["bytes"]
        for asset in _manifest()["assets"]
        for export in asset["exports"]
    }
    assert exports["assets/maps/town-map-world.webp"] < 350_000
    for building in (
        "dorm",
        "classroom",
        "library",
        "canteen",
        "river",
        "shop",
    ):
        assert exports[f"assets/buildings/{building}.webp"] < 20_000
    for interior in (
        "dorm",
        "classroom",
        "library",
        "canteen",
        "river",
        "shop",
    ):
        assert exports[f"assets/interiors/{interior}.webp"] < 120_000
    assert exports["assets/spine/lin_cheng.json"] < 20_000
    assert exports["assets/spine/lin_cheng.atlas"] < 5_000
    assert exports["assets/spine/lin_cheng.png"] < 30_000


def test_art_budget_records_desktop_and_mobile_layout() -> None:
    report = json.loads(
        (ROOT / "docs" / "art-budget-b7-5.json").read_text(encoding="utf-8")
    )
    assert report["desktop"]["scrollWidth"] == report["desktop"]["viewportWidth"]
    assert report["mobile"]["scrollWidth"] == report["mobile"]["viewportWidth"]
    for viewport in ("desktop", "mobile"):
        assert {
            item["label"] for item in report[viewport]["buildings"]
        } == {"宿舍", "教学楼", "青禾书院", "食堂", "河边步道", "便利店"}
        assert report[viewport]["consoleErrors"] == []
        movement = report[viewport]["cameraMovement"]
        assert movement["before"] != movement["after"]
        assert movement["playerBefore"]["x"] != movement["playerAfter"]["x"]
        assert movement["spineMoving"]["animation"] == "walk"
        assert movement["spineIdle"]["animation"] == "idle"
        assert movement["spineMoving"]["frames"] > 0
        assert movement["dialogueBefore"] != movement["dialogueAfter"]
    assert report["desktop_interior"]["title"] == "宿舍"
    assert report["mobile_interior"]["title"] == "宿舍"
    assert "/assets/interiors/" in report["desktop_interior"]["image"]
    assert (ROOT / report["interior_overview"]).is_file()
    assert (
        ROOT / report["east_town"]["screenshot"]
    ).is_file()
    assert (ROOT / report["river_walk"]["screenshot"]).is_file()
    assert report["river_walk"]["player"]["y"] >= 700
    assert "河边步道" in report["river_walk"]["label"]
    assert (
        report["east_town"]["cameraAfter"]
        != report["east_town"]["cameraBefore"]
    )
    assert report["first_screen_transfer_bytes"]["desktop"] < 250_000
    assert report["first_screen_transfer_bytes"]["mobile"] < 200_000
