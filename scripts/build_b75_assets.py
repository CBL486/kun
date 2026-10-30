"""从项目所有者提供的素材包生成 B7.5 运行资源与来源清单。

本脚本只做裁切、拼贴、透明背景处理和最近邻缩放。页面里的地图、建筑、
角色头像与图标都保留素材包中的原始像素，不再程序化重画造型。
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageEnhance


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets"
SOURCE_ROOT = Path(
    os.environ.get(
        "B75_SOURCE_ROOT",
        str(ROOT / "out" / "b75-source-extracted"),
    )
).resolve()

SOURCE_PACKS = [
    {
        "id": "appledog_interiors",
        "name": "Modern Interior Tileset by AppleDog",
        "archive": "Full Tileset.7z",
        "archive_sha256": "630F38A16CF8D2368612CB92AE7292F234B98EB94A57E5D351B71C937473081F",
        "role": "卧室、客厅及生活道具补充",
        "license_status": "commercial-licensed",
        "license_url": "https://apple-dog.itch.io/modern-tileset-by-appledog",
        "attribution": "Modern Interior Tileset by AppleDog",
    },
    {
        "id": "modern_exteriors",
        "name": "LimeZu Modern Exteriors",
        "archive": "modernexteriors-win.zip",
        "archive_sha256": "D12C6892ED96BC18CDA34EAFDF3EF15B1EDA10D0D6733F377730F46932F728FE",
        "role": "现代建筑外观、道路、铺装、围栏与室外道具",
        "license_status": "commercial-licensed",
        "license_url": "https://limezu.itch.io/modernexteriors",
        "attribution": "Modern Exteriors by LimeZu",
    },
    {
        "id": "clean_city_v3",
        "name": "GuttyKreum Clean City v3",
        "archive": "2106161.zip",
        "archive_sha256": "467DBFB0887B4EE605D4F4C3038B8642271C1C5CA967A8ABC4EC2247525A0DE5",
        "role": "现代建筑、商铺、道路和校园街区",
        "license_status": "project-authorized",
    },
    {
        "id": "sunnyside_world",
        "name": "Sunnyside World Assets / UI",
        "archive": "农场生活.zip",
        "archive_sha256": "B9084F961E8E78CDB8789ED72ED7383B6A9B3EBE8130F4B792A88A65C5D40CF5",
        "role": "像素 UI 状态图标",
        "license_status": "project-authorized",
    },
    {
        "id": "modern_interiors",
        "name": "Modern Interiors",
        "archive": "2104261.zip",
        "archive_sha256": "8FE691CE84881936F6B7A25E15A9847A1BFD555D21984A99939EA930A52C4C91",
        "role": "角色帧、Spine 骨骼拆分、室内图块和界面图标",
        "license_status": "project-authorized",
    },
    {
        "id": "village_pixel_pack",
        "name": "村庄田园像素游戏",
        "archive": "村庄田园像素游戏.rar",
        "archive_sha256": "E2D8D538183A9674C479C7620DE17B8F3547F2236E08604557A6E98F0A1D5F3A",
        "role": "草地、水岸、石路、树木与传统 RPG 地图布局",
        "license_status": "project-authorized",
    },
]

MEMBERS = {
    "clean_b": "RPGMakerMV/GK_B_CC_1.png",
    "clean_d": "RPGMakerMV/GK_D_CC_1.png",
    "clean_a2": "RPGMakerMV/GK_A2_CCautotile_1.png",
    "village_tiles": "Assets/Tileset.png",
    "village_objects": "Assets/Object.png",
    "village_example": "Assets/Example 1.png",
    "character_frames": (
        "Modern_Interiors/4_RPG_MAKER_MV/Characters/"
        "New_Characters 48x48.png"
    ),
    "ui_icons": "Modern_Interiors/4_User_Interface_Elements/UI_32x32.png",
    "sunnyside_confirm": (
        "SUNNYSIDE_WORLD_UI_V1.0/SUNNYSIDEWORLD_UI_V1.0/ASSETS/confirm.png"
    ),
    "sunnyside_cancel": (
        "SUNNYSIDE_WORLD_UI_V1.0/SUNNYSIDEWORLD_UI_V1.0/ASSETS/cancel.png"
    ),
    "sunnyside_basket": (
        "SUNNYSIDE_WORLD_UI_V1.0/SUNNYSIDEWORLD_UI_V1.0/ASSETS/basket.png"
    ),
}

SOURCE_FILES = {
    "me_grass": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "1_Terrains_and_Fences_Singles_48x48"
        / "ME_Singles_Terrains_and_Fences_48x48_Grass_2_9.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "1_Terrains_and_Fences_Singles_48x48/"
            "ME_Singles_Terrains_and_Fences_48x48_Grass_2_9.png"
        ),
    ),
    "me_asphalt": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "2_City_Terrains_Singles_48x48"
        / "ME_Singles_City_Terrains_48x48_Asphalt_1_Variation_18.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "2_City_Terrains_Singles_48x48/"
            "ME_Singles_City_Terrains_48x48_Asphalt_1_Variation_18.png"
        ),
    ),
    "me_sidewalk": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "2_City_Terrains_Singles_48x48"
        / "ME_Singles_City_Terrains_48x48_Sidewalk_1_25.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "2_City_Terrains_Singles_48x48/"
            "ME_Singles_City_Terrains_48x48_Sidewalk_1_25.png"
        ),
    ),
    "me_school": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "13_School_Singles_48x48"
        / "ME_Singles_School_48x48_School_1.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "13_School_Singles_48x48/ME_Singles_School_48x48_School_1.png"
        ),
    ),
    "me_modern_house": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "24_Additional_Houses_Singles_48x48"
        / "24_Additional_Houses_Modern_House_48x48.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "24_Additional_Houses_Singles_48x48/"
            "24_Additional_Houses_Modern_House_48x48.png"
        ),
    ),
    "me_japanese_house": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "24_Additional_Houses_Singles_48x48"
        / "24_Additional_Houses_Japanese_House_48x48.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "24_Additional_Houses_Singles_48x48/"
            "24_Additional_Houses_Japanese_House_48x48.png"
        ),
    ),
    "me_market_medium": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "9_Shopping_Center_and_Markets_Singles_48x48"
        / "ME_Singles_Shopping_Center_and_Markets_48x48_Market_Medium_1.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "9_Shopping_Center_and_Markets_Singles_48x48/"
            "ME_Singles_Shopping_Center_and_Markets_48x48_Market_Medium_1.png"
        ),
    ),
    "me_market_small": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "9_Shopping_Center_and_Markets_Singles_48x48"
        / "ME_Singles_Shopping_Center_and_Markets_48x48_Market_Small_1.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "9_Shopping_Center_and_Markets_Singles_48x48/"
            "ME_Singles_Shopping_Center_and_Markets_48x48_Market_Small_1.png"
        ),
    ),
    "me_bench": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "13_School_Singles_48x48"
        / "ME_Singles_School_48x48_Bench_1.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "13_School_Singles_48x48/ME_Singles_School_48x48_Bench_1.png"
        ),
    ),
    "me_tree": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "3_City_Props_Singles_48x48"
        / "ME_Singles_City_Props_48x48_Tree_3.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "3_City_Props_Singles_48x48/"
            "ME_Singles_City_Props_48x48_Tree_3.png"
        ),
    ),
    "me_shrub": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "3_City_Props_Singles_48x48"
        / "ME_Singles_City_Props_48x48_Shrub_4.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "3_City_Props_Singles_48x48/"
            "ME_Singles_City_Props_48x48_Shrub_4.png"
        ),
    ),
    "me_flower_bush": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "3_City_Props_Singles_48x48"
        / "ME_Singles_City_Props_48x48_Flower_Bush_1.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "3_City_Props_Singles_48x48/"
            "ME_Singles_City_Props_48x48_Flower_Bush_1.png"
        ),
    ),
    "me_street_lamp": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "3_City_Props_Singles_48x48"
        / "ME_Singles_City_Props_48x48_Street_Lamp_1.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "3_City_Props_Singles_48x48/"
            "ME_Singles_City_Props_48x48_Street_Lamp_1.png"
        ),
    ),
    "me_hydrant": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "3_City_Props_Singles_48x48"
        / "ME_Singles_City_Props_48x48_Hydrant_1.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "3_City_Props_Singles_48x48/"
            "ME_Singles_City_Props_48x48_Hydrant_1.png"
        ),
    ),
    "me_mailbox": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "3_City_Props_Singles_48x48"
        / "ME_Singles_City_Props_48x48_Mailbox_1.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "3_City_Props_Singles_48x48/"
            "ME_Singles_City_Props_48x48_Mailbox_1.png"
        ),
    ),
    "me_trashbin": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "3_City_Props_Singles_48x48"
        / "ME_Singles_City_Props_48x48_Trashbin_10.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "3_City_Props_Singles_48x48/"
            "ME_Singles_City_Props_48x48_Trashbin_10.png"
        ),
    ),
    "appledog_furniture": (
        "appledog_interiors",
        SOURCE_ROOT / "appledog" / "48x48" / "Inside_home_B.png",
        "Full Tileset.7z!/48x48/Inside_home_B.png",
    ),
    "appledog_beds": (
        "appledog_interiors",
        SOURCE_ROOT / "appledog" / "48x48" / "inside_home_C.png",
        "Full Tileset.7z!/48x48/inside_home_C.png",
    ),
    "clean_b": (
        "clean_city_v3",
        SOURCE_ROOT
        / "clean_city"
        / "GuttyKreum_CleanCityv3"
        / "RPGMakerMV"
        / "GK_B_CC_1.png",
        "GuttyKreum_CleanCityv3.zip!/RPGMakerMV/GK_B_CC_1.png",
    ),
    "clean_d": (
        "clean_city_v3",
        SOURCE_ROOT
        / "clean_city"
        / "GuttyKreum_CleanCityv3"
        / "RPGMakerMV"
        / "GK_D_CC_1.png",
        "GuttyKreum_CleanCityv3.zip!/RPGMakerMV/GK_D_CC_1.png",
    ),
    "clean_a2": (
        "clean_city_v3",
        SOURCE_ROOT
        / "clean_city"
        / "GuttyKreum_CleanCityv3"
        / "RPGMakerMV"
        / "GK_A2_CCautotile_1.png",
        "GuttyKreum_CleanCityv3.zip!/RPGMakerMV/GK_A2_CCautotile_1.png",
    ),
    "village_tiles": (
        "village_pixel_pack",
        SOURCE_ROOT / "village" / "Assets" / "Tileset.png",
        "Assets/Tileset.png",
    ),
    "village_objects": (
        "village_pixel_pack",
        SOURCE_ROOT / "village" / "Assets" / "Object.png",
        "Assets/Object.png",
    ),
    "village_example": (
        "village_pixel_pack",
        SOURCE_ROOT / "village" / "Assets" / "Example 1.png",
        "Assets/Example 1.png",
    ),
    "character_frames": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "4_RPG_MAKER_MV"
        / "Characters"
        / "New_Characters 48x48.png",
        (
            "Modern_Interiors/4_RPG_MAKER_MV/Characters/"
            "New_Characters 48x48.png"
        ),
    ),
    "ui_icons": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "4_User_Interface_Elements"
        / "UI_32x32.png",
        "Modern_Interiors/4_User_Interface_Elements/UI_32x32.png",
    ),
    "interior_floors": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "4_RPG_MAKER_MV"
        / "Floors_TILESET_A2_.png",
        "Modern_Interiors/4_RPG_MAKER_MV/Floors_TILESET_A2_.png",
    ),
    "interior_floors_clean": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Old_Stuff"
        / "Floors_only_48x48.png",
        "Modern_Interiors/1_Interiors/48x48/Old_Stuff/Floors_only_48x48.png",
    ),
    "interior_walls": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "4_RPG_MAKER_MV"
        / "Walls_TILESET_A4_.png",
        "Modern_Interiors/4_RPG_MAKER_MV/Walls_TILESET_A4_.png",
    ),
    "interior_bedroom": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Theme_Sorter_48x48"
        / "4_Bedroom_48x48.png",
        "Modern_Interiors/1_Interiors/48x48/Theme_Sorter_48x48/4_Bedroom_48x48.png",
    ),
    "interior_bedroom_tiles": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Theme_Sorter_48x48"
        / "4_Bedroom_48x48.png",
        (
            "Modern_Interiors/1_Interiors/48x48/"
            "Theme_Sorter_48x48/4_Bedroom_48x48.png"
        ),
    ),
    "interior_school": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Theme_Sorter_48x48"
        / "5_Classroom_and_library_48x48.png",
        (
            "Modern_Interiors/1_Interiors/48x48/"
            "Theme_Sorter_48x48/5_Classroom_and_library_48x48.png"
        ),
    ),
    "interior_kitchen": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Theme_Sorter_48x48"
        / "12_Kitchen_48x48.png",
        (
            "Modern_Interiors/1_Interiors/48x48/"
            "Theme_Sorter_48x48/12_Kitchen_48x48.png"
        ),
    ),
    "interior_grocery": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Theme_Sorter_48x48"
        / "16_Grocery_store_48x48.png",
        (
            "Modern_Interiors/1_Interiors/48x48/"
            "Theme_Sorter_48x48/16_Grocery_store_48x48.png"
        ),
    ),
    "interior_living": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Theme_Sorter_48x48"
        / "2_LivingRoom_48x48.png",
        (
            "Modern_Interiors/1_Interiors/48x48/"
            "Theme_Sorter_48x48/2_LivingRoom_48x48.png"
        ),
    ),
    "interior_generic": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Theme_Sorter_48x48"
        / "1_Generic_48x48.png",
        (
            "Modern_Interiors/1_Interiors/48x48/"
            "Theme_Sorter_48x48/1_Generic_48x48.png"
        ),
    ),
    "interior_conference": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Theme_Sorter_48x48"
        / "13_Conference_Hall_48x48.png",
        (
            "Modern_Interiors/1_Interiors/48x48/"
            "Theme_Sorter_48x48/13_Conference_Hall_48x48.png"
        ),
    ),
    "room_floors": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Room_Builder_subfiles_48x48"
        / "Room_Builder_Floors_48x48.png",
        (
            "Modern_Interiors/1_Interiors/48x48/"
            "Room_Builder_subfiles_48x48/Room_Builder_Floors_48x48.png"
        ),
    ),
    "room_walls": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Room_Builder_subfiles_48x48"
        / "Room_Builder_Walls_48x48.png",
        (
            "Modern_Interiors/1_Interiors/48x48/"
            "Room_Builder_subfiles_48x48/Room_Builder_Walls_48x48.png"
        ),
    ),
    "room_borders": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "1_Interiors"
        / "48x48"
        / "Room_Builder_subfiles_48x48"
        / "Room_Builder_borders_48x48.png",
        (
            "Modern_Interiors/1_Interiors/48x48/"
            "Room_Builder_subfiles_48x48/Room_Builder_borders_48x48.png"
        ),
    ),
    "interior_clock": (
        "modern_interiors",
        SOURCE_ROOT
        / "modern_interiors"
        / "Modern_Interiors"
        / "3_Animated_objects"
        / "48x48"
        / "spritesheets"
        / "animated_cuckoo_clock_48x48.png",
        (
            "Modern_Interiors/3_Animated_objects/48x48/spritesheets/"
            "animated_cuckoo_clock_48x48.png"
        ),
    ),
    "me_deep_water": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "1_Terrains_and_Fences_Singles_48x48"
        / "ME_Singles_Terrains_and_Fences_48x48_Deep_Water_1_9.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "1_Terrains_and_Fences_Singles_48x48/"
            "ME_Singles_Terrains_and_Fences_48x48_Deep_Water_1_9.png"
        ),
    ),
    "me_info_sign": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "3_City_Props_Singles_48x48"
        / "ME_Singles_City_Props_48x48_Info_Sign_1.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "3_City_Props_Singles_48x48/"
            "ME_Singles_City_Props_48x48_Info_Sign_1.png"
        ),
    ),
    "me_pier": (
        "modern_exteriors",
        SOURCE_ROOT
        / "modern_exteriors"
        / "full"
        / "Modern_Exteriors_48x48"
        / "ME_Theme_Sorter_48x48"
        / "11_Camping_Singles_48x48"
        / "ME_Singles_Camping_48x48_Pier_1.png",
        (
            "Modern_Exteriors_48x48/ME_Theme_Sorter_48x48/"
            "11_Camping_Singles_48x48/"
            "ME_Singles_Camping_48x48_Pier_1.png"
        ),
    ),
    "sunnyside_confirm": (
        "sunnyside_world",
        SOURCE_ROOT
        / "sunnyside"
        / "SUNNYSIDE_WORLD_UI_V1.0"
        / "SUNNYSIDEWORLD_UI_V1.0"
        / "ASSETS"
        / "confirm.png",
        (
            "SUNNYSIDE_WORLD_UI_V1.0/SUNNYSIDEWORLD_UI_V1.0/"
            "ASSETS/confirm.png"
        ),
    ),
    "sunnyside_cancel": (
        "sunnyside_world",
        SOURCE_ROOT
        / "sunnyside"
        / "SUNNYSIDE_WORLD_UI_V1.0"
        / "SUNNYSIDEWORLD_UI_V1.0"
        / "ASSETS"
        / "cancel.png",
        (
            "SUNNYSIDE_WORLD_UI_V1.0/SUNNYSIDEWORLD_UI_V1.0/"
            "ASSETS/cancel.png"
        ),
    ),
    "sunnyside_basket": (
        "sunnyside_world",
        SOURCE_ROOT
        / "sunnyside"
        / "SUNNYSIDE_WORLD_UI_V1.0"
        / "SUNNYSIDEWORLD_UI_V1.0"
        / "ASSETS"
        / "basket.png",
        (
            "SUNNYSIDE_WORLD_UI_V1.0/SUNNYSIDEWORLD_UI_V1.0/"
            "ASSETS/basket.png"
        ),
    ),
}

PALETTE = {
    "ink": "#283329",
    "ink_soft": "#445144",
    "forest": "#274c35",
    "forest_dark": "#17372a",
    "leaf": "#85bb51",
    "leaf_light": "#aede73",
    "cream": "#f7edcf",
    "paper": "#fff7df",
    "sand": "#d8b875",
    "amber": "#d39a3a",
    "water": "#36a4c8",
    "stone": "#8493a4",
    "brick": "#9c5d3f",
}

IMAGE_CACHE: dict[str, Image.Image] = {}


def source(key: str) -> Image.Image:
    if key not in IMAGE_CACHE:
        path = SOURCE_FILES[key][1]
        if not path.is_file():
            raise FileNotFoundError(
                f"缺少素材文件：{path}\n"
                "请先解压素材包到 out/b75-source-extracted，"
                "或通过 B75_SOURCE_ROOT 指定解压目录。"
            )
        IMAGE_CACHE[key] = Image.open(path).convert("RGBA")
    return IMAGE_CACHE[key]


def layer(
    key: str,
    box: tuple[int, int, int, int],
    operation: str,
    *,
    placement: dict | None = None,
) -> dict:
    pack_id, _, member = SOURCE_FILES[key]
    result = {
        "source_pack": pack_id,
        "source_archive": next(
            pack["archive"] for pack in SOURCE_PACKS if pack["id"] == pack_id
        ),
        "source_member": member,
        "crop_box": list(box),
        "modification_operation": operation,
        "original_pixel_used": True,
    }
    if placement is not None:
        result["placement"] = placement
    return result


def crop(key: str, box: tuple[int, int, int, int]) -> Image.Image:
    x, y, width, height = box
    return source(key).crop((x, y, x + width, y + height)).convert("RGBA")


def alpha_trim(image: Image.Image) -> Image.Image:
    box = image.getchannel("A").getbbox()
    return image.crop(box) if box else image


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = image.copy()
    image.thumbnail(size, Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(
        image,
        ((size[0] - image.width) // 2, size[1] - image.height),
    )
    return canvas


def save_asset(
    image: Image.Image,
    relative: str,
    *,
    webp: bool = True,
) -> list[Path]:
    output = ASSET_ROOT / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, optimize=True)
    outputs = [output]
    if webp:
        webp_path = output.with_suffix(".webp")
        image.save(webp_path, "WEBP", lossless=True, method=6)
        outputs.append(webp_path)
    return outputs


def tile_fill(
    canvas: Image.Image,
    tile: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    for y in range(y0, y1, tile.height):
        for x in range(x0, x1, tile.width):
            part = tile.crop(
                (
                    0,
                    0,
                    min(tile.width, x1 - x),
                    min(tile.height, y1 - y),
                )
            )
            canvas.alpha_composite(part, (x, y))


def place(
    canvas: Image.Image,
    sprite: Image.Image,
    xy: tuple[int, int],
    scale: int = 1,
) -> None:
    if scale != 1:
        sprite = sprite.resize(
            (sprite.width * scale, sprite.height * scale),
            Image.Resampling.NEAREST,
        )
    canvas.alpha_composite(sprite, xy)


def build_map(width: int, height: int, *, mobile: bool) -> tuple[Image.Image, list[dict]]:
    grass = crop("village_tiles", (0, 224, 32, 32))
    path = crop("clean_a2", (544, 320, 32, 32))
    sidewalk = crop("clean_a2", (576, 320, 32, 32))
    tree_a = alpha_trim(crop("village_objects", (4, 96, 60, 64)))
    tree_b = alpha_trim(crop("village_objects", (68, 96, 60, 64)))
    tree_c = alpha_trim(crop("village_objects", (132, 96, 60, 64)))
    pine = alpha_trim(crop("village_objects", (196, 96, 60, 64)))
    lamp = alpha_trim(crop("village_objects", (180, 194, 28, 40)))
    flowers_warm = crop("village_tiles", (128, 128, 32, 32))
    flowers_cool = crop("village_tiles", (160, 128, 32, 32))

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    tile_fill(canvas, grass, (0, 0, width, height))

    if mobile:
        path_boxes = [
            (94, 0, 158, height),
            (0, 250, width, 314),
            (0, 662, width, 726),
        ]
        tree_positions = [
            (5, 8, tree_a),
            (280, 16, tree_b),
            (10, 126, pine),
            (304, 154, tree_c),
            (16, 328, tree_b),
            (302, 420, tree_a),
            (8, 506, tree_c),
        ]
    else:
        path_boxes = [
            (326, 0, 390, height),
            (0, 220, width, 284),
            (0, 402, width, 466),
        ]
        tree_positions = [
            (12, 8, tree_a),
            (250, 8, tree_b),
            (462, 6, pine),
            (636, 30, tree_c),
            (12, 342, pine),
            (226, 382, tree_a),
            (540, 366, tree_b),
            (648, 278, pine),
        ]

    for box in path_boxes:
        tile_fill(canvas, path, box)

    for x, y, sprite in tree_positions:
        place(canvas, sprite, (x, y))
    for x, y in ((160, 184), (548, 292), (282, 390)) if not mobile else (
        (74, 184),
        (250, 434),
        (228, 812),
    ):
        place(canvas, lamp, (x, y))

    source_layers = [
        layer("village_tiles", (0, 224, 32, 32), "tile + repeated"),
        layer("clean_a2", (544, 320, 32, 32), "tile + repeated"),
        layer("village_objects", (4, 96, 60, 64), "crop + alpha trim"),
        layer("village_objects", (68, 96, 60, 64), "crop + alpha trim"),
        layer("village_objects", (132, 96, 60, 64), "crop + alpha trim"),
        layer("village_objects", (196, 96, 60, 64), "crop + alpha trim"),
        layer("village_objects", (180, 194, 28, 40), "crop + alpha trim"),
    ]
    return canvas, source_layers


def build_world_map() -> tuple[Image.Image, list[dict]]:
    width, height = 2400, 900
    grass = crop("me_grass", (0, 0, 48, 48))
    path = crop("me_asphalt", (0, 0, 48, 48))
    sidewalk = crop("me_sidewalk", (0, 0, 48, 48))
    water = crop("me_deep_water", (0, 0, 48, 48))
    tree = alpha_trim(crop("me_tree", (0, 0, *source("me_tree").size)))
    shrub = alpha_trim(crop("me_shrub", (0, 0, *source("me_shrub").size)))
    flowers = alpha_trim(
        crop(
            "me_flower_bush",
            (0, 0, *source("me_flower_bush").size),
        )
    )
    street_lamp = alpha_trim(
        crop("me_street_lamp", (0, 0, *source("me_street_lamp").size))
    )
    hydrant = alpha_trim(
        crop("me_hydrant", (0, 0, *source("me_hydrant").size))
    )
    mailbox = alpha_trim(
        crop("me_mailbox", (0, 0, *source("me_mailbox").size))
    )
    trashbin = alpha_trim(
        crop("me_trashbin", (0, 0, *source("me_trashbin").size))
    )
    bench = alpha_trim(crop("me_bench", (0, 0, *source("me_bench").size)))
    info_sign = alpha_trim(
        crop("me_info_sign", (0, 0, *source("me_info_sign").size))
    )

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    tile_fill(canvas, grass, (0, 0, width, height))
    tile_fill(canvas, water, (0, 800, width, height))

    water_edge = ImageEnhance.Brightness(water).enhance(0.64)
    tile_fill(canvas, water_edge, (0, 800, width, 816))

    # 横向主街贯穿小镇，两侧留出连续人行道和入户小径。
    for box in (
        (0, 332, width, 380),
        (0, 460, width, 508),
    ):
        tile_fill(canvas, sidewalk, box)
    tile_fill(canvas, path, (0, 380, width, 460))
    for box in (
        (330, 332, 378, 380),
        (720, 332, 768, 380),
        (1260, 332, 1308, 380),
        (360, 460, 408, 520),
        (1050, 460, 1098, 512),
        (2025, 460, 2073, 520),
    ):
        tile_fill(canvas, path, box)
    # 靠街的停车湾与铺装小广场让横版街道不再是一条直线。
    for box in (
        (1480, 380, 1740, 460),
        (440, 508, 760, 584),
        (1170, 508, 1450, 566),
        (1880, 508, 2180, 574),
        (0, 728, width, 800),
    ):
        tile_fill(canvas, sidewalk, box)

    # 树冠形成三段自然边界，建筑之间保有清晰入口。
    for x, y in (
        (12, 12),
        (176, 18),
        (440, 28),
        (960, 6),
        (1066, 82),
        (1424, 10),
        (1638, 14),
        (2050, 18),
        (2244, 4),
        (44, 594),
        (286, 626),
        (700, 614),
        (830, 620),
        (1474, 606),
        (1650, 628),
        (2180, 612),
        (2300, 586),
        (194, 682),
        (932, 680),
        (1372, 666),
        (2318, 664),
    ):
        place(canvas, tree, (x, y))

    for x, y in (
        (46, 304),
        (212, 292),
        (412, 300),
        (1002, 302),
        (1136, 298),
        (1404, 302),
        (1716, 298),
        (1900, 302),
        (2234, 298),
        (48, 548),
        (314, 636),
        (690, 566),
        (760, 584),
        (1496, 566),
        (1726, 568),
        (2140, 578),
        (372, 648),
        (1010, 646),
        (1464, 650),
        (2248, 652),
    ):
        place(canvas, shrub, (x, y))

    for x, y in (
        (250, 294),
        (530, 290),
        (900, 290),
        (1340, 290),
        (1605, 288),
        (1958, 286),
        (2304, 290),
        (128, 552),
        (602, 622),
        (1220, 604),
        (1790, 608),
        (758, 684),
        (1588, 674),
        (2004, 686),
    ):
        place(canvas, flowers, (x, y))

    for x, y in (
        (396, 198),
        (858, 180),
        (1468, 164),
        (1880, 170),
        (2210, 188),
        (254, 516),
        (724, 516),
        (1584, 516),
        (2148, 516),
        (278, 738),
        (900, 738),
        (1518, 738),
        (2150, 738),
        (436, 668),
        (1106, 664),
        (1728, 668),
        (2332, 664),
    ):
        place(canvas, street_lamp, (x, y))

    for x, y in (
        (300, 330),
        (792, 330),
        (1518, 330),
        (2086, 330),
        (566, 338),
        (1188, 338),
        (1742, 338),
        (2292, 338),
    ):
        place(canvas, hydrant if x in {300, 792, 1518, 2086} else trashbin, (x, y))

    for x, y in (
        (182, 324),
        (886, 324),
        (537, 324),
        (2060, 324),
    ):
        place(canvas, mailbox, (x, y))

    for x, y in (
        (238, 330),
        (915, 330),
        (1372, 330),
        (1824, 330),
        (552, 486),
        (1608, 486),
        (2172, 486),
    ):
        place(canvas, bench, (x, y))

    # The river is part of the world plane rather than a rectangular image.
    place(canvas, info_sign, (878, 694))
    place(canvas, bench, (842, 674))
    place(canvas, bench, (1352, 674))
    place(canvas, bench, (2058, 674))

    source_layers = [
        layer("me_grass", (0, 0, 48, 48), "tile + repeated"),
        layer("me_deep_water", (0, 0, 48, 48), "tile + repeated"),
        layer("me_sidewalk", (0, 0, 48, 48), "tile + repeated"),
        layer("me_asphalt", (0, 0, 48, 48), "tile + repeated"),
        layer("me_tree", (0, 0, *source("me_tree").size), "crop + alpha trim"),
        layer("me_shrub", (0, 0, *source("me_shrub").size), "crop + alpha trim"),
        layer(
            "me_flower_bush",
            (0, 0, *source("me_flower_bush").size),
            "crop + alpha trim",
        ),
        layer(
            "me_street_lamp",
            (0, 0, *source("me_street_lamp").size),
            "crop + alpha trim",
        ),
        layer(
            "me_hydrant",
            (0, 0, *source("me_hydrant").size),
            "crop + alpha trim",
        ),
        layer(
            "me_mailbox",
            (0, 0, *source("me_mailbox").size),
            "crop + alpha trim",
        ),
        layer(
            "me_trashbin",
            (0, 0, *source("me_trashbin").size),
            "crop + alpha trim",
        ),
        layer(
            "me_bench",
            (0, 0, *source("me_bench").size),
            "direct sprite placement",
        ),
        layer(
            "me_info_sign",
            (0, 0, *source("me_info_sign").size),
            "direct sprite placement",
        ),
    ]
    return canvas, source_layers


def building_asset(
    key: str,
    box: tuple[int, int, int, int],
) -> tuple[Image.Image, list[dict]]:
    image = alpha_trim(crop(key, box))
    return image, [layer(key, box, "crop + alpha trim")]


def full_source_asset(key: str) -> tuple[Image.Image, list[dict]]:
    width, height = source(key).size
    box = (0, 0, width, height)
    image = alpha_trim(crop(key, box))
    return image, [layer(key, box, "direct source sprite")]


def portrait_asset(
    box: tuple[int, int, int, int],
) -> tuple[Image.Image, list[dict]]:
    frame = alpha_trim(crop("character_frames", box))
    frame = frame.resize(
        (frame.width * 2, frame.height * 2),
        Image.Resampling.NEAREST,
    )
    canvas = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    left = max(0, (96 - frame.width) // 2)
    canvas.alpha_composite(frame, (left, 4))
    return canvas, [
        layer(
            "character_frames",
            box,
            "crop one RPG Maker character frame + alpha trim + nearest 2x",
        ),
    ]


def ui_icon_asset(
    key: str,
    box: tuple[int, int, int, int],
    *,
    size: tuple[int, int] = (32, 32),
) -> tuple[Image.Image, list[dict]]:
    icon = alpha_trim(crop(key, box))
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    fit_icon = icon.copy()
    fit_icon.thumbnail(size, Image.Resampling.NEAREST)
    canvas.alpha_composite(
        fit_icon,
        ((size[0] - fit_icon.width) // 2, (size[1] - fit_icon.height) // 2),
    )
    return canvas, [layer(key, box, "crop + alpha trim + nearest fit")]


def interior_asset(
    *,
    floor_box: tuple[int, int, int, int],
    wall_box: tuple[int, int, int, int],
    placements: list[tuple],
    wall_height: int = 96,
) -> tuple[Image.Image, list[dict]]:
    """Build a cutaway RPG room without changing the native sprite geometry.

    Source crop coordinates are kept in source pixels. Object positions are final
    canvas pixels. This prevents the accidental double scaling that previously
    cut furniture in half and made the rooms feel under-furnished.
    """

    width, height = 960, 540
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    floor_tile = crop("interior_floors_clean", floor_box)
    wall_tile = crop("room_walls", wall_box)

    tile_fill(canvas, floor_tile, (0, 0, width, height))
    # Use the clean inner wall column so the 3-column builder sheet does not
    # repeat its left/right frame lines every 144 pixels across the room.
    wall_face = wall_tile.crop(
        (
            min(48, max(0, wall_tile.width - 48)),
            0,
            min(96, wall_tile.width),
            wall_tile.height,
        )
    )
    tile_fill(canvas, wall_face, (0, 0, width, wall_height))

    # A darker skirting line and floor contact band establish the cutaway depth.
    wall_shadow = ImageEnhance.Brightness(wall_face).enhance(0.62)
    tile_fill(
        canvas,
        wall_shadow,
        (0, wall_height - 9, width, wall_height),
    )
    floor_shadow = ImageEnhance.Brightness(floor_tile).enhance(0.58)
    tile_fill(
        canvas,
        floor_shadow,
        (0, wall_height, width, wall_height + 14),
    )
    side_shadow = ImageEnhance.Brightness(floor_tile).enhance(0.48)
    tile_fill(canvas, side_shadow, (0, wall_height, 12, height))
    tile_fill(canvas, side_shadow, (width - 12, wall_height, width, height))

    layers = [
        layer("interior_floors_clean", floor_box, "tile + repeated"),
        layer("room_walls", wall_box, "crop 3x2 wall module + repeated"),
    ]

    # Place back-wall objects first and floor furniture in visual depth order.
    ordered = sorted(
        enumerate(placements),
        key=lambda item: (item[1][2][1], item[0]),
    )
    for _, placement in ordered:
        key, box, position, display_factor, *transforms = placement
        sprite = alpha_trim(crop(key, box))
        if "flip_y" in transforms:
            sprite = sprite.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        if "flip_x" in transforms:
            sprite = sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if display_factor != 1:
            sprite = sprite.resize(
                (
                    max(1, round(sprite.width * display_factor)),
                    max(1, round(sprite.height * display_factor)),
                ),
                Image.Resampling.NEAREST,
            )
        destination = (round(position[0]), round(position[1]))
        if destination[1] >= wall_height:
            shadow_alpha = sprite.getchannel("A").point(
                lambda value: min(82, value // 3)
            )
            object_shadow = Image.new("RGBA", sprite.size, (17, 15, 12, 0))
            object_shadow.putalpha(shadow_alpha)
            canvas.alpha_composite(
                object_shadow,
                (destination[0] + 5, destination[1] + 7),
            )
        place(canvas, sprite, destination)
        layers.append(
            layer(
                key,
                box,
                "crop + alpha trim + interior composition"
                + (
                    " + source-alpha contact shadow"
                    if destination[1] >= wall_height
                    else ""
                )
                + (
                    f" + {display_factor:g}x local scale"
                    if display_factor != 1
                    else ""
                )
                + (
                    " + vertical flip"
                    if "flip_y" in transforms
                    else ""
                )
                + (
                    " + horizontal flip"
                    if "flip_x" in transforms
                    else ""
                ),
                placement={
                    "destination": list(destination),
                    "trimmed_size": list(sprite.size),
                },
            )
        )

    # Low-saturation room grade and edge falloff add a quiet cinematic depth
    # while all visible structures still come from the supplied pixel sheets.
    graded = ImageEnhance.Color(canvas).enhance(0.88)
    graded = ImageEnhance.Brightness(graded).enhance(0.94)
    falloff = Image.radial_gradient("L").resize((width, height))
    falloff_alpha = falloff.point(lambda value: int(value * 0.34))
    shade = Image.new("RGBA", (width, height), (3, 6, 8, 0))
    shade.putalpha(falloff_alpha)
    graded.alpha_composite(shade)
    return graded, layers


def conference_table_set(
    x: int,
    y: int,
) -> list[tuple]:
    """Four complete chairs placed around one long conference-style table."""

    chair_box = (336, 0, 48, 48)
    table_box = (0, 96, 192, 96)
    return [
        ("interior_conference", chair_box, (x + 18, y - 34), 1),
        ("interior_conference", chair_box, (x + 126, y - 34), 1),
        ("interior_conference", table_box, (x, y), 1),
        ("interior_conference", chair_box, (x + 18, y + 78), 1, "flip_y"),
        ("interior_conference", chair_box, (x + 126, y + 78), 1, "flip_y"),
    ]


def river_scene_asset() -> tuple[Image.Image, list[dict]]:
    """Build the riverside walk as part of the same 48px RPG world."""

    width, height = 960, 540
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    grass = crop("me_grass", (0, 0, 48, 48))
    sidewalk = crop("me_sidewalk", (0, 0, 48, 48))
    water = crop("me_deep_water", (0, 0, 48, 48))
    tree = alpha_trim(crop("me_tree", (0, 0, *source("me_tree").size)))
    shrub = alpha_trim(crop("me_shrub", (0, 0, *source("me_shrub").size)))
    flowers = alpha_trim(
        crop("me_flower_bush", (0, 0, *source("me_flower_bush").size))
    )
    lamp = alpha_trim(
        crop("me_street_lamp", (0, 0, *source("me_street_lamp").size))
    )
    bench = alpha_trim(crop("me_bench", (0, 0, *source("me_bench").size)))
    pier = alpha_trim(crop("me_pier", (0, 0, *source("me_pier").size)))
    sign = alpha_trim(
        crop("me_info_sign", (0, 0, *source("me_info_sign").size))
    )

    tile_fill(canvas, grass, (0, 0, width, height))
    tile_fill(canvas, sidewalk, (0, 92, width, 214))
    tile_fill(canvas, water, (0, 214, width, 446))

    water_edge = ImageEnhance.Brightness(water).enhance(0.58)
    tile_fill(canvas, water_edge, (0, 214, width, 226))
    path_edge = ImageEnhance.Brightness(sidewalk).enhance(0.62)
    tile_fill(canvas, path_edge, (0, 202, width, 214))

    for x, y, sprite in (
        (24, 8, tree),
        (270, 2, tree),
        (588, 4, tree),
        (810, 12, tree),
        (116, 86, shrub),
        (446, 90, shrub),
        (752, 82, shrub),
        (352, 72, flowers),
        (680, 74, flowers),
        (70, 418, tree),
        (268, 430, shrub),
        (520, 424, flowers),
        (770, 412, tree),
    ):
        place(canvas, sprite, (x, y))

    for x, y in ((218, 92), (632, 90), (162, 438), (724, 432)):
        place(canvas, lamp, (x, y))
    for x, y in ((84, 142), (318, 146), (708, 144), (530, 442)):
        place(canvas, bench, (x, y))

    # A small observation landing reaches into the water and avoids the
    # rectangular "pasted map" effect from the previous river image.
    place(canvas, pier, (462, 286))
    place(canvas, sign, (420, 124))
    place(
        canvas,
        alpha_trim(crop("character_frames", (48, 0, 48, 96))),
        (610, 112),
    )

    layers = [
        layer("me_grass", (0, 0, 48, 48), "tile + repeated"),
        layer("me_sidewalk", (0, 0, 48, 48), "tile + repeated"),
        layer("me_deep_water", (0, 0, 48, 48), "tile + repeated"),
        layer("me_tree", (0, 0, *source("me_tree").size), "crop + alpha trim"),
        layer("me_shrub", (0, 0, *source("me_shrub").size), "crop + alpha trim"),
        layer(
            "me_flower_bush",
            (0, 0, *source("me_flower_bush").size),
            "crop + alpha trim",
        ),
        layer(
            "me_street_lamp",
            (0, 0, *source("me_street_lamp").size),
            "crop + alpha trim",
        ),
        layer("me_bench", (0, 0, *source("me_bench").size), "crop + alpha trim"),
        layer("me_pier", (0, 0, *source("me_pier").size), "crop + alpha trim"),
        layer(
            "me_info_sign",
            (0, 0, *source("me_info_sign").size),
            "crop + alpha trim",
        ),
        layer(
            "character_frames",
            (48, 0, 48, 96),
            "crop + alpha trim + riverside placement",
        ),
    ]
    return canvas, layers


def scenic_asset(
    key: str,
    box: tuple[int, int, int, int],
) -> tuple[Image.Image, list[dict]]:
    image = crop(key, box)
    return image, [layer(key, box, "direct scene crop")]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


COMMERCIAL_ATTRIBUTIONS = {
    "modern_exteriors": "Modern Exteriors by LimeZu",
    "appledog_interiors": "Modern Interior Tileset by AppleDog",
}


def _commercial_author(source_pack_ids: list[str]) -> str:
    authors = {
        "modern_exteriors": "LimeZu",
        "appledog_interiors": "AppleDog",
    }
    names = [
        authors[pack_id]
        for pack_id in ("modern_exteriors", "appledog_interiors")
        if pack_id in source_pack_ids
    ]
    if names:
        return f"{' / '.join(names)} 与项目内场景编排"
    return "项目方授权素材包原始像素与项目内裁切拼贴"


def _commercial_attribution(source_pack_ids: list[str]) -> str:
    licensed = [
        attribution
        for pack_id in ("modern_exteriors", "appledog_interiors")
        if pack_id in source_pack_ids
        for attribution in (COMMERCIAL_ATTRIBUTIONS[pack_id],)
    ]
    if licensed:
        return (
            "；".join(licensed)
            + "；以及 Clean City v3、Sunnyside World、Modern Interiors "
            "与《村庄田园像素游戏》素材。"
        )
    return (
        "项目方授权素材包原始像素，以及 Clean City v3、Sunnyside World、"
        "Modern Interiors 与《村庄田园像素游戏》素材。"
    )


def write_manifest(logical_assets: Iterable[dict]) -> None:
    assets = []
    for logical in logical_assets:
        source_pack_ids = sorted(
            {item["source_pack"] for item in logical["source_layers"]}
        )
        commercial_sources = {
            "modern_exteriors",
            "appledog_interiors",
        } & set(source_pack_ids)
        exports = []
        for path in logical["outputs"]:
            exports.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
        assets.append(
            {
                "id": logical["id"],
                "kind": logical["kind"],
                "role": logical["role"],
                "creation_route": "source-composite",
                "author": _commercial_author(source_pack_ids),
                "attribution": _commercial_attribution(source_pack_ids),
                "source_packs": source_pack_ids,
                "source_layers": logical["source_layers"],
                "original_pixel_used": True,
                "rights_status": (
                    "commercial-licensed"
                    if commercial_sources
                    else "project-authorized"
                ),
                "license_status": (
                    "commercial-licensed"
                    if commercial_sources
                    else "project-authorized"
                ),
                "requires_attribution": True if commercial_sources else False,
                "allowed_use": [
                    "本地开发",
                    "本项目集成",
                    "作为本项目组成部分公开分发",
                ],
                "authorization": "项目所有者于 2026-10-29 确认可直接使用或改造。",
                "raw_source_included": False,
                "canvas": logical["canvas"],
                "runtime_display": logical["display"],
                "pixel_treatment": (
                    "source crop, transparent alpha, nearest-neighbor integer scaling; "
                    "no programmatic redraw"
                ),
                "exports": exports,
            }
        )

    manifest = {
        "schema_version": "rpg-asset-manifest-v2",
        "theme": {
            "name": "青禾镇 · 田园观察手账",
            "projection": "top-down 3/4",
            "logical_tile": 32,
            "display_scale": 1,
            "image_rendering": "pixelated",
            "palette": PALETTE,
        },
        "authorization": {
            "status": "project-authorized",
            "confirmed_on": "2026-10-29",
            "note": "原始压缩包未提交；仅提交基于授权素材的裁切、组合和运行时导出资源。",
        },
        "source_packs": SOURCE_PACKS,
        "assets": assets,
        "fallback": {
            "missing_building": "assets/icons/brand.png",
            "missing_portrait": "assets/icons/character.png",
            "text_alternative": "每个图片均配套运行时中文名称和状态文本。",
        },
    }
    (ASSET_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build() -> None:
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    logical_assets: list[dict] = []

    world_map, world_layers = build_world_map()
    logical_assets.append(
        {
            "id": "town_map_world",
            "kind": "map_background",
            "role": "横向小镇大世界",
            "outputs": save_asset(world_map, "maps/town-map-world.png"),
            "canvas": [2400, 900],
            "display": [1200, 450],
            "source_layers": world_layers,
        }
    )

    buildings = {
        "dorm": full_source_asset("me_modern_house"),
        "classroom": full_source_asset("me_school"),
        "library": full_source_asset("me_japanese_house"),
        "canteen": full_source_asset("me_market_medium"),
        "shop": full_source_asset("me_market_small"),
        "river": full_source_asset("me_pier"),
    }
    building_names = {
        "dorm": "宿舍",
        "classroom": "教学楼",
        "library": "青禾书院",
        "canteen": "食堂",
        "shop": "便利店",
        "river": "河边步道",
    }
    for building_id, (image, layers) in buildings.items():
        logical_assets.append(
            {
                "id": f"building_{building_id}",
                "kind": "building",
                "role": building_names[building_id],
                "outputs": save_asset(image, f"buildings/{building_id}.png"),
                "canvas": list(image.size),
                "display": [240, 160],
                "source_layers": layers,
            }
        )

    interiors = {
        "dorm": interior_asset(
            floor_box=(288, 96, 96, 96),
            wall_box=(384, 288, 144, 96),
            placements=[
                ("interior_generic", (288, 2080, 96, 72), (90, 20), 1),
                ("interior_generic", (384, 2080, 96, 72), (770, 20), 1),
                ("interior_generic", (256, 1344, 64, 64), (430, 30), 1),
                ("interior_clock", (0, 0, 32, 64), (872, 22), 1),
                ("appledog_beds", (60, 0, 120, 177), (52, 176), 1),
                ("appledog_beds", (204, 3, 168, 177), (760, 176), 1),
                ("appledog_furniture", (627, 294, 90, 105), (354, 176), 1),
                (
                    "interior_bedroom_tiles",
                    (0, 1056, 288, 96),
                    (330, 378),
                    1,
                ),
                ("appledog_furniture", (0, 48, 141, 144), (20, 370), 1),
                ("appledog_furniture", (144, 51, 144, 141), (164, 373), 1),
                ("appledog_furniture", (27, 210, 87, 117), (714, 382), 1),
                ("appledog_furniture", (384, 480, 64, 96), (810, 342), 1),
                ("character_frames", (48, 0, 48, 96), (540, 278), 1),
            ],
        ),
        "classroom": interior_asset(
            floor_box=(0, 0, 96, 96),
            wall_box=(0, 384, 144, 96),
            placements=[
                ("interior_generic", (192, 1344, 64, 64), (74, 18), 1),
                ("interior_generic", (256, 1344, 64, 64), (820, 18), 1),
                ("interior_school", (384, 0, 192, 96), (384, 12), 1),
                ("interior_clock", (0, 0, 32, 64), (878, 18), 1),
                ("interior_school", (192, 384, 192, 96), (28, 312), 1),
                ("interior_school", (384, 384, 192, 96), (740, 312), 1),
                ("interior_school", (0, 0, 384, 192), (288, 142), 1),
                ("interior_school", (0, 0, 384, 192), (288, 326), 1),
                (
                    "interior_bedroom_tiles",
                    (0, 1056, 288, 96),
                    (24, 442),
                    1,
                ),
                ("interior_living", (496, 20, 64, 104), (894, 438), 1),
                ("character_frames", (48, 0, 48, 96), (462, 252), 1),
            ],
        ),
        "library": interior_asset(
            floor_box=(192, 192, 96, 96),
            wall_box=(384, 384, 144, 96),
            placements=[
                ("interior_school", (0, 672, 192, 192), (20, 34), 1),
                ("interior_school", (0, 672, 192, 192), (210, 34), 1),
                ("interior_school", (0, 672, 192, 192), (400, 34), 1),
                ("interior_school", (0, 672, 192, 192), (590, 34), 1),
                ("interior_generic", (256, 1344, 64, 64), (768, 10), 1),
                ("interior_clock", (0, 0, 32, 64), (878, 18), 1),
                *conference_table_set(122, 236),
                *conference_table_set(520, 236),
                (
                    "interior_bedroom_tiles",
                    (0, 1056, 288, 96),
                    (252, 388),
                    1,
                ),
                ("interior_living", (496, 20, 64, 104), (752, 438), 1),
                ("appledog_furniture", (0, 96, 192, 96), (18, 402), 1),
                ("appledog_furniture", (0, 384, 96, 96), (846, 378), 1),
                ("character_frames", (192, 0, 48, 96), (432, 318), 1),
            ],
        ),
        "canteen": interior_asset(
            floor_box=(192, 0, 96, 96),
            wall_box=(0, 480, 144, 96),
            placements=[
                ("interior_kitchen", (192, 192, 192, 192), (68, 10), 1),
                ("interior_kitchen", (384, 192, 192, 192), (260, 10), 1),
                ("interior_kitchen", (192, 192, 192, 192), (642, 10), 1),
                ("interior_generic", (384, 1344, 64, 64), (452, 10), 1),
                ("interior_clock", (0, 0, 32, 64), (882, 18), 1),
                *conference_table_set(58, 214),
                *conference_table_set(386, 214),
                *conference_table_set(714, 214),
                *conference_table_set(220, 374),
                *conference_table_set(548, 374),
                ("interior_kitchen", (256, 704, 128, 128), (760, 86), 1),
                ("interior_living", (496, 20, 64, 104), (12, 438), 1),
                ("interior_living", (496, 20, 64, 104), (894, 438), 1),
                ("character_frames", (336, 0, 48, 96), (494, 354), 1),
            ],
        ),
        "shop": interior_asset(
            floor_box=(576, 0, 96, 96),
            wall_box=(1152, 288, 144, 96),
            placements=[
                ("interior_grocery", (81, 393, 78, 108), (108, 108), 1),
                ("interior_grocery", (192, 396, 48, 105), (206, 110), 1),
                ("interior_grocery", (273, 393, 78, 108), (314, 108), 1),
                ("interior_grocery", (384, 396, 48, 105), (416, 110), 1),
                ("interior_grocery", (0, 528, 480, 69), (476, 110), 1),
                ("interior_grocery", (15, 726, 66, 138), (20, 230), 1),
                ("interior_grocery", (15, 726, 66, 138), (884, 230), 1),
                ("interior_grocery", (96, 624, 338, 48), (120, 230), 1),
                ("interior_grocery", (516, 1320, 216, 120), (500, 230), 1),
                ("interior_grocery", (675, 573, 42, 66), (808, 218), 1),
                ("interior_grocery", (675, 597, 42, 45), (808, 292), 1),
                ("interior_grocery", (128, 1344, 384, 96), (430, 414), 1),
                ("interior_generic", (320, 1344, 64, 64), (378, 10), 1),
                ("interior_clock", (0, 0, 32, 64), (882, 18), 1),
                ("interior_living", (496, 20, 64, 104), (10, 438), 1),
                ("interior_living", (496, 20, 64, 104), (894, 438), 1),
                ("character_frames", (48, 96, 48, 96), (770, 318), 1),
            ],
        ),
        "river": river_scene_asset(),
    }
    interiors_layers = {}
    for interior_id, (image, layers) in interiors.items():
        interiors_layers[interior_id] = layers
        logical_assets.append(
            {
                "id": f"interior_{interior_id}",
                "kind": "interior_scene",
                "role": f"{building_names[interior_id]}内部",
                "outputs": save_asset(
                    image,
                    f"interiors/{interior_id}.png",
                ),
                "canvas": list(image.size),
                "display": [960, 540],
                "source_layers": interiors_layers[interior_id],
            }
        )

    portraits = {
        "lin_cheng": portrait_asset((48, 0, 48, 96)),
        "chen_lan": portrait_asset((192, 0, 48, 96)),
        "su_wan": portrait_asset((336, 0, 48, 96)),
        "gao_yuan": portrait_asset((48, 96, 48, 96)),
        "gu_yan": portrait_asset((336, 192, 48, 96)),
    }
    portrait_names = {
        "lin_cheng": "林澄",
        "chen_lan": "陈岚",
        "su_wan": "苏晚",
        "gao_yuan": "高原",
        "gu_yan": "顾言",
    }
    for portrait_id, (image, layers) in portraits.items():
        logical_assets.append(
            {
                "id": f"portrait_{portrait_id}",
                "kind": "portrait",
                "role": portrait_names[portrait_id],
                "outputs": save_asset(image, f"portraits/{portrait_id}.png"),
                "canvas": list(image.size),
                "display": [96, 96],
                "source_layers": layers,
            }
        )

    hero = alpha_trim(crop("character_frames", (48, 0, 48, 96)))
    logical_assets.append(
        {
            "id": "character_lin_cheng",
            "kind": "world_character",
            "role": "林澄地图行走形象",
            "outputs": save_asset(hero, "characters/lin_cheng.png"),
            "canvas": list(hero.size),
            "display": list(hero.size),
            "source_layers": [
                layer(
                    "character_frames",
                    (48, 0, 48, 96),
                    "crop one RPG Maker character frame + alpha trim",
                )
            ],
        }
    )

    map_icon = world_map.crop((250, 330, 282, 362))
    logical_assets.append(
        {
            "id": "icon_map",
            "kind": "ui_icon",
            "role": "map 像素图标",
            "outputs": save_asset(map_icon, "icons/map.png", webp=False),
            "canvas": [32, 32],
            "display": [20, 20],
            "source_layers": world_layers,
        }
    )

    icon_specs = {
        "character": ui_icon_asset("ui_icons", (192, 0, 32, 32)),
        "timeline": ui_icon_asset("ui_icons", (320, 128, 32, 32)),
        "chat": ui_icon_asset("ui_icons", (288, 32, 32, 32)),
        "diary": ui_icon_asset("ui_icons", (352, 0, 32, 32)),
        "memory": ui_icon_asset("ui_icons", (256, 128, 32, 32)),
        "settings": ui_icon_asset("ui_icons", (352, 128, 32, 32)),
        "open": ui_icon_asset("sunnyside_confirm", (0, 0, 16, 16)),
        "closed": ui_icon_asset("sunnyside_cancel", (0, 0, 16, 16)),
        "brand": ui_icon_asset("sunnyside_basket", (0, 0, 16, 16)),
    }
    for icon_id, (image, layers) in icon_specs.items():
        logical_assets.append(
            {
                "id": f"icon_{icon_id}",
                "kind": "ui_icon",
                "role": f"{icon_id} 像素图标",
                "outputs": save_asset(
                    image,
                    f"icons/{icon_id}.png",
                    webp=False,
                ),
                "canvas": list(image.size),
                "display": [20, 20],
                "source_layers": layers,
            }
        )

    write_manifest(logical_assets)


if __name__ == "__main__":
    build()
