"""生成林澄的 Spine 源纹理与可导入骨架数据。"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE_IMAGE = ROOT / "assets" / "characters" / "lin_cheng.png"
SOURCE_DIR = ROOT / "spine" / "lin_cheng" / "source"
PROJECT_PATH = ROOT / "spine" / "lin_cheng" / "lin_cheng.spine"
EXPORT_DIR = ROOT / "assets" / "spine"
MANIFEST_PATH = ROOT / "assets" / "manifest.json"


def make_textures() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE_IMAGE).convert("RGBA")
    source = source.crop(source.getchannel("A").getbbox())
    if source.size != (48, 66):
        source = source.resize((48, 66), Image.Resampling.NEAREST)

    body = source.crop((0, 0, 48, 45))
    body.save(SOURCE_DIR / "lin_cheng_body.png")

    source.crop((0, 45, 24, 66)).save(
        SOURCE_DIR / "lin_cheng_leg_left.png"
    )
    source.crop((24, 45, 48, 66)).save(
        SOURCE_DIR / "lin_cheng_leg_right.png"
    )

    shadow = Image.new("RGBA", (32, 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.ellipse((1, 1, 30, 7), fill=(24, 35, 23, 96))
    shadow.save(SOURCE_DIR / "lin_cheng_shadow.png")


def skeleton_data() -> dict:
    return {
        "skeleton": {
            "spine": "4.3.08",
            "x": -24,
            "y": -4,
            "width": 48,
            "height": 70,
            "images": ".",
        },
        "bones": [
            {"name": "root"},
            {"name": "torso", "parent": "root", "y": 21, "length": 24},
            {"name": "head", "parent": "torso", "y": 24, "length": 21},
            {"name": "leg_left", "parent": "torso", "x": -12, "length": 21},
            {"name": "leg_right", "parent": "torso", "x": 12, "length": 21},
        ],
        "slots": [
            {"name": "shadow", "bone": "root", "attachment": "shadow"},
            {"name": "leg_left", "bone": "leg_left", "attachment": "leg_left"},
            {"name": "leg_right", "bone": "leg_right", "attachment": "leg_right"},
            {"name": "torso", "bone": "torso", "attachment": "body"},
        ],
        "skins": [
            {
                "name": "default",
                "attachments": {
                    "shadow": {
                        "shadow": {
                            "path": "lin_cheng_shadow",
                            "x": 0,
                            "y": -4,
                            "width": 32,
                            "height": 8,
                        }
                    },
                    "leg_left": {
                        "leg_left": {
                            "path": "lin_cheng_leg_left",
                            "x": 0,
                            "y": -10.5,
                            "width": 24,
                            "height": 21,
                        }
                    },
                    "leg_right": {
                        "leg_right": {
                            "path": "lin_cheng_leg_right",
                            "x": 0,
                            "y": -10.5,
                            "width": 24,
                            "height": 21,
                        }
                    },
                    "torso": {
                        "body": {
                            "path": "lin_cheng_body",
                            "x": 0,
                            "y": 22.5,
                            "width": 48,
                            "height": 45,
                        }
                    },
                },
            }
        ],
        "animations": {
            "idle": {
                "bones": {
                    "root": {
                        "translate": [
                            {"time": 0, "x": 0, "y": 0},
                            {
                                "time": 0.7,
                                "x": 0,
                                "y": 1,
                                "curve": [0.25, 0, 0.75, 1],
                            },
                            {"time": 1.4, "x": 0, "y": 0},
                        ]
                    },
                    "torso": {
                        "rotate": [
                            {"time": 0, "value": 0},
                            {
                                "time": 0.7,
                                "value": -1.2,
                                "curve": [0.25, 0, 0.75, 1],
                            },
                            {"time": 1.4, "value": 0},
                        ]
                    },
                    "head": {
                        "rotate": [
                            {"time": 0, "value": 0},
                            {
                                "time": 0.7,
                                "value": 1.5,
                                "curve": [0.25, 0, 0.75, 1],
                            },
                            {"time": 1.4, "value": 0},
                        ]
                    },
                },
            },
            "walk": {
                "bones": {
                    "root": {
                        "translate": [
                            {"time": 0, "x": 0, "y": 0},
                            {
                                "time": 0.15,
                                "x": 0,
                                "y": 2,
                                "curve": "stepped",
                            },
                            {
                                "time": 0.3,
                                "x": 0,
                                "y": 0,
                                "curve": "stepped",
                            },
                            {
                                "time": 0.45,
                                "x": 0,
                                "y": 2,
                                "curve": "stepped",
                            },
                            {
                                "time": 0.6,
                                "x": 0,
                                "y": 0,
                                "curve": "stepped",
                            },
                        ]
                    },
                    "torso": {
                        "rotate": [
                            {"time": 0, "value": -1.5},
                            {"time": 0.3, "value": 1.5},
                            {"time": 0.6, "value": -1.5},
                        ]
                    },
                    "leg_left": {
                        "rotate": [
                            {"time": 0, "value": -18},
                            {"time": 0.3, "value": 18},
                            {"time": 0.6, "value": -18},
                        ]
                    },
                    "leg_right": {
                        "rotate": [
                            {"time": 0, "value": 18},
                            {"time": 0.3, "value": -18},
                            {"time": 0.6, "value": 18},
                        ]
                    },
                },
            },
        },
    }


def pack_runtime_assets() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    regions = [
        ("lin_cheng_body", (2, 2)),
        ("lin_cheng_leg_left", (54, 2)),
        ("lin_cheng_leg_right", (82, 2)),
        ("lin_cheng_shadow", (54, 28)),
    ]
    atlas = Image.new("RGBA", (128, 64), (0, 0, 0, 0))
    lines = [
        "lin_cheng.png",
        "size: 128,64",
        "format: RGBA8888",
        "filter: Nearest,Nearest",
        "repeat: none",
    ]
    for region_name, position in regions:
        image = Image.open(SOURCE_DIR / f"{region_name}.png").convert("RGBA")
        atlas.alpha_composite(image, position)
        lines.extend(
            [
                region_name,
                "  rotate: false",
                f"  xy: {position[0]}, {position[1]}",
                f"  size: {image.width}, {image.height}",
                f"  orig: {image.width}, {image.height}",
                "  offset: 0, 0",
                "  index: -1",
            ]
        )
    atlas.save(EXPORT_DIR / "lin_cheng.png")
    (EXPORT_DIR / "lin_cheng.atlas").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    shutil.copy2(SOURCE_DIR / "lin_cheng.json", EXPORT_DIR / "lin_cheng.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assets = [
        asset
        for asset in manifest["assets"]
        if asset["id"] != "spine_lin_cheng"
    ]
    exports = []
    for relative in (
        "assets/spine/lin_cheng.json",
        "assets/spine/lin_cheng.atlas",
        "assets/spine/lin_cheng.png",
    ):
        path = ROOT / relative
        exports.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    assets.append(
        {
            "id": "spine_lin_cheng",
            "kind": "spine_skeleton",
            "role": "林澄 Spine 待机与行走动画",
            "creation_route": "spine-json-composite",
            "author": "项目方授权角色像素与项目内 Spine 骨骼拆分",
            "attribution": "角色纹理来自 Modern Interiors 授权角色帧。",
            "source_packs": ["modern_interiors"],
            "source_layers": [
                {
                    "source_pack": "modern_interiors",
                    "source_archive": "2104261.zip",
                    "source_member": (
                        "Modern_Interiors/4_RPG_MAKER_MV/Characters/"
                        "New_Characters 48x48.png"
                    ),
                    "crop_box": [48, 0, 48, 96],
                    "modification_operation": (
                        "alpha trim, split torso and two leg regions, "
                        "Spine 4.3 JSON rig"
                    ),
                    "original_pixel_used": True,
                }
            ],
            "original_pixel_used": True,
            "rights_status": "project-authorized",
            "license_status": "project-authorized",
            "allowed_use": [
                "本地开发",
                "本项目集成",
                "作为本项目组成部分公开分发",
            ],
            "authorization": "项目所有者授权使用并改造原始角色素材。",
            "raw_source_included": False,
            "canvas": [48, 66],
            "runtime_display": [48, 70],
            "pixel_treatment": "Spine WebGL, nearest-neighbor atlas, 2x render",
            "animations": ["idle", "walk"],
            "spine_editor": "Spine Trial 4.3.26",
            "editor_export_status": (
                "trial license blocks project save and animation export; "
                "runtime-compatible Spine JSON generated from native rig"
            ),
            "exports": exports,
        }
    )
    manifest["assets"] = assets
    manifest["spine_runtime"] = {
        "package": "@esotericsoftware/spine-webgl",
        "version": "4.3.13",
        "file": "web/vendor/spine-webgl.min.js",
        "license_file": "web/vendor/SPINE-RUNTIMES-LICENSE.txt",
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    make_textures()
    (SOURCE_DIR / "lin_cheng.json").write_text(
        json.dumps(
            skeleton_data(),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    pack_runtime_assets()
    update_manifest()
    print(SOURCE_DIR / "lin_cheng.json")
    print(EXPORT_DIR / "lin_cheng.json")


if __name__ == "__main__":
    main()
