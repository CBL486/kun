from __future__ import annotations

import hashlib
import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "art-source/character-v2/pixellab/P2-4"
MAP_HTML = OUTPUT_DIR / "map-preview-4dir.html"
METRICS_PATH = OUTPUT_DIR / "metrics-4dir-clean.json"
VISUAL_REVIEW_PATH = OUTPUT_DIR / "visual-review.json"
BROWSER_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
)


def browser_path() -> Path:
    for candidate in BROWSER_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("no supported Chromium browser found")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def capture(
    page: Page,
    viewport: tuple[int, int],
    screenshot_path: Path,
    *,
    is_mobile: bool = False,
) -> dict[str, object]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text)
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(MAP_HTML.as_uri(), wait_until="load")
    page.wait_for_function("window.__p2Evidence !== undefined")
    page.wait_for_timeout(700)
    evidence = page.evaluate("window.__p2Evidence")
    page.screenshot(path=str(screenshot_path), full_page=False)
    return {
        "viewport": list(viewport),
        "is_mobile": is_mobile,
        "screenshot": screenshot_path.relative_to(ROOT).as_posix(),
        "player_rect": evidence["playerRect"],
        "max_horizontal_delta": evidence["maxHorizontalDelta"],
        "direction_samples": evidence["samples"],
        "console_errors": errors,
        "screenshot_sha256": sha256(screenshot_path),
    }


def main() -> None:
    if not MAP_HTML.is_file():
        raise FileNotFoundError(MAP_HTML)

    desktop_path = OUTPUT_DIR / "map-desktop-4dir.png"
    mobile_path = OUTPUT_DIR / "map-mobile-4dir.png"
    evidence_path = OUTPUT_DIR / "map-capture.json"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(browser_path()),
            headless=True,
        )
        desktop_page = browser.new_page(viewport={"width": 1440, "height": 1000})
        desktop = capture(
            desktop_page,
            (1440, 1000),
            desktop_path,
        )
        mobile_page = browser.new_page(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            device_scale_factor=1,
        )
        mobile = capture(
            mobile_page,
            (390, 844),
            mobile_path,
            is_mobile=True,
        )
        browser.close()

    for name, result in (("desktop", desktop), ("mobile", mobile)):
        if result["player_rect"] != [48, 72]:
            raise AssertionError(f"{name} player rect is {result['player_rect']}")
        if result["max_horizontal_delta"] != 0:
            raise AssertionError(
                f"{name} direction switch moved horizontally by "
                f"{result['max_horizontal_delta']} px"
            )
        if result["console_errors"]:
            raise AssertionError(f"{name} console errors: {result['console_errors']}")

    report = {
        "schema_version": "rpg-character-pixellab-p2-4-map-capture-v1",
        "html": MAP_HTML.relative_to(ROOT).as_posix(),
        "desktop": desktop,
        "mobile": mobile,
        "all_console_errors": desktop["console_errors"] + mobile["console_errors"],
    }
    evidence_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    metrics["map_evidence"] = {
        "map_preview": MAP_HTML.relative_to(ROOT).as_posix(),
        "runtime_size": [48, 72],
        "desktop": desktop,
        "mobile": mobile,
        "console_errors": report["all_console_errors"],
    }
    METRICS_PATH.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    visual = json.loads(VISUAL_REVIEW_PATH.read_text(encoding="utf-8"))
    visual["checks"]["map_readable_48x72"] = True
    visual["checks"]["console_errors_zero"] = True
    visual["status"] = "technical-pass-pending-user-confirmation"
    VISUAL_REVIEW_PATH.write_text(
        json.dumps(visual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
