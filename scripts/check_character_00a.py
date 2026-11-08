"""Validate the ART-V2 00A smoke assets without network calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "art-source" / "character-v2" / "candidates"


def describe(name: str) -> dict:
    path = CANDIDATES / name
    with Image.open(path) as image:
        alpha = image.getchannel("A") if image.mode in {"RGBA", "LA"} else None
        histogram = alpha.histogram() if alpha else []
        return {
            "file": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "format": image.format,
            "mode": image.mode,
            "size": list(image.size),
            "alpha_extrema": list(alpha.getextrema()) if alpha else None,
            "alpha_zero_pixels": histogram[0] if histogram else 0,
            "alpha_partial_pixels": sum(histogram[1:255]) if histogram else 0,
            "has_aigc_metadata": any(
                "TC260:AIGC" in str(value)
                for value in image.info.values()
            ),
        }


def main() -> None:
    payload = {
        "schema_version": "aiworld-character-00a-evidence-v1",
        "original": describe("00a-001.png"),
        "transparent": describe("00a-001-alpha.png"),
        "reference_variation": describe("00a-002-preview.png"),
    }
    output = (
        ROOT / "docs" / "character-art-v2" / "00a-assets.json"
    )
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
