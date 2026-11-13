from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
P1 = ROOT / "art-source" / "character-v2" / "pixellab" / "P1"
SOURCE = P1 / "generated-64x96.png"
CLEANED = P1 / "cleaned-64x96.png"
PREVIEW = P1 / "sprite-preview-4x.png"
METRICS = P1 / "metrics.json"


def color_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def border_background(image: Image.Image) -> tuple[int, int, int]:
    width, height = image.size
    samples = [
        image.getpixel((x, 0))[:3]
        for x in range(width)
    ] + [
        image.getpixel((x, height - 1))[:3]
        for x in range(width)
    ]
    samples += [
        image.getpixel((0, y))[:3]
        for y in range(height)
    ] + [
        image.getpixel((width - 1, y))[:3]
        for y in range(height)
    ]
    return tuple(round(sum(pixel[channel] for pixel in samples) / len(samples)) for channel in range(3))


def remove_connected_background(
    image: Image.Image, background: tuple[int, int, int], threshold: float = 30.0
) -> Image.Image:
    width, height = image.size
    pixels = image.load()
    transparent = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        index = y * width + x
        if transparent[index]:
            continue
        if color_distance(pixels[x, y][:3], background) > threshold:
            continue
        transparent[index] = 255
        if x:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))

    cleaned = image.copy()
    cleaned_pixels = cleaned.load()
    for y in range(height):
        for x in range(width):
            if transparent[y * width + x]:
                red, green, blue, _ = cleaned_pixels[x, y]
                cleaned_pixels[x, y] = (red, green, blue, 0)
            else:
                red, green, blue, _ = cleaned_pixels[x, y]
                cleaned_pixels[x, y] = (red, green, blue, 255)
    return cleaned


def ensure_clear_border(image: Image.Image) -> Image.Image:
    pixels = image.load()
    width, height = image.size
    for x in range(width):
        for y in (0, height - 1):
            red, green, blue, _ = pixels[x, y]
            pixels[x, y] = (red, green, blue, 0)
    for y in range(height):
        for x in (0, width - 1):
            red, green, blue, _ = pixels[x, y]
            pixels[x, y] = (red, green, blue, 0)
    return image


def align_baseline(image: Image.Image, target_baseline_y: int = 88) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("Sprite has no opaque pixels")
    _, _, _, bottom = bbox
    shift_y = target_baseline_y - bottom
    if shift_y == 0:
        return image

    aligned = Image.new("RGBA", image.size, (0, 0, 0, 0))
    aligned.alpha_composite(image, (0, shift_y))
    return aligned


def quantize_rgba(image: Image.Image, colors: int = 20) -> Image.Image:
    alpha = image.getchannel("A")
    rgb = image.convert("RGB")
    quantized = rgb.quantize(
        colors=colors,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    ).convert("RGBA")
    quantized.putalpha(alpha)
    return quantized


def main() -> None:
    generated = Image.open(SOURCE).convert("RGBA")
    background = border_background(generated)
    cleaned = remove_connected_background(generated, background)
    cleaned = ensure_clear_border(cleaned)
    cleaned = align_baseline(cleaned, target_baseline_y=88)
    cleaned = quantize_rgba(cleaned, colors=20)
    cleaned.save(CLEANED)

    preview = cleaned.resize(
        (cleaned.width * 4, cleaned.height * 4),
        Image.Resampling.NEAREST,
    )
    preview.save(PREVIEW)

    alpha = cleaned.getchannel("A")
    alpha_values = sorted(set(alpha.getdata()))
    colors_rgba = cleaned.getcolors(maxcolors=1_000_000) or []
    bbox = alpha.getbbox()
    metrics = {
        "input_size": [256, 384],
        "generated_size": [generated.width, generated.height],
        "cleaned_size": [cleaned.width, cleaned.height],
        "runtime_size": [48, 72],
        "colors": len(colors_rgba),
        "alpha_values": alpha_values,
        "semi_transparent_pixels": sum(
            1 for value in alpha.getdata() if value not in (0, 255)
        ),
        "baseline_y": 88,
        "opaque_bbox": list(bbox or ()),
        "background_rgb": list(background),
        "background_threshold": 30,
        "console_errors": [],
    }
    METRICS.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False))


if __name__ == "__main__":
    main()
