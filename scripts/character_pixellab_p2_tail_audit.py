from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image


EXPECTED_SIZE = (96, 96)
EXPECTED_ORIGINAL_BBOX = (29, 26, 67, 90)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit the single PixelLab P2-1R north-tail edit attempt."
    )
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("art-source/character-v2/pixellab/P2"),
    )
    parser.add_argument("--preview-scale", type=int, default=8)
    args = parser.parse_args()

    original = Image.open(args.original).convert("RGBA")
    result = Image.open(args.result).convert("RGBA")
    if original.size != EXPECTED_SIZE or result.size != EXPECTED_SIZE:
        raise ValueError(
            f"unexpected dimensions: original={original.size} result={result.size}"
        )
    if original.getbbox() != EXPECTED_ORIGINAL_BBOX:
        raise ValueError(f"unexpected original bbox: {original.getbbox()}")

    additions: list[tuple[int, int]] = []
    removals: list[tuple[int, int]] = []
    color_changed = 0
    for y in range(result.height):
        for x in range(result.width):
            before = original.getpixel((x, y))
            after = result.getpixel((x, y))
            if before != after:
                color_changed += 1
            if before[3] == 0 and after[3] != 0:
                additions.append((x, y))
            elif before[3] != 0 and after[3] == 0:
                removals.append((x, y))

    result_palette = {
        result.getpixel((x, y))
        for y in range(result.height)
        for x in range(result.width)
    }
    alpha_values = sorted({color[3] for color in result_palette})
    if alpha_values != [0, 255]:
        raise ValueError(f"unexpected alpha values: {alpha_values}")

    result_bbox = result.getbbox()
    tail_visible = result_bbox is not None and (
        result_bbox[2] > EXPECTED_ORIGINAL_BBOX[2]
        or result_bbox[0] < EXPECTED_ORIGINAL_BBOX[0]
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.output_dir / "north-tail-edit-attempt.png"
    preview_path = args.output_dir / "north-tail-edit-attempt-preview-8x.png"
    metrics_path = args.output_dir / "metrics-p2-1r-attempt.json"

    shutil.copyfile(args.result, result_path)
    result.resize(
        (
            result.width * args.preview_scale,
            result.height * args.preview_scale,
        ),
        Image.Resampling.NEAREST,
    ).save(preview_path)

    metrics: dict[str, object] = {
        "schema_version": "rpg-character-pixellab-p2-1r-attempt-v1",
        "status": "blocked" if not tail_visible else "candidate",
        "blocker": (
            None
            if tail_visible
            else "north whale tail silhouette did not extend beyond the original dress"
        ),
        "tool": "PixelLab Edit Image",
        "model": "Standard",
        "generation_count": 1,
        "displayed_cost": "1 generation",
        "image_size": list(result.size),
        "colors": len(result_palette),
        "opaque_colors": sum(1 for color in result_palette if color[3] != 0),
        "alpha_values": alpha_values,
        "original_bbox": list(EXPECTED_ORIGINAL_BBOX),
        "result_bbox": list(result_bbox) if result_bbox else None,
        "new_opaque_pixels": len(additions),
        "removed_opaque_pixels": len(removals),
        "color_changed_pixels": color_changed,
        "new_opaque_coordinates": additions,
        "tail_silhouette_extended": tail_visible,
        "visual_acceptance": {
            "back_hair": "pass",
            "back_clothing": "pass",
            "waist_bow": "pass",
            "whale_tail": "fail-not-visible",
        },
        "result_sha256": sha256(result_path),
        "cleaned_spritesheet_created": False,
        "map_screenshots_created": False,
        "animation_started": False,
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
