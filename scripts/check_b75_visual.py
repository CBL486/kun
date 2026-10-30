"""启动本地 API，检查 B7.5 首屏并生成视觉与体积证据。"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_ROOT = ROOT / "docs" / "screenshots"
REPORT_PATH = ROOT / "docs" / "art-budget-b7-5.json"
EDGE_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
)


def wait_for_port(port: int, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.4)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError("本地 API 未在限定时间内启动")


def overlaps(first: dict, second: dict) -> bool:
    return not (
        first["right"] <= second["left"]
        or second["right"] <= first["left"]
        or first["bottom"] <= second["top"]
        or second["bottom"] <= first["top"]
    )


def inspect_page(page, name: str) -> dict:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: (
            console_errors.append(message.text)
            if message.type == "error"
            else None
        ),
    )
    started = time.perf_counter()
    page.goto("http://127.0.0.1:8110/", wait_until="networkidle")
    page.wait_for_selector('body[data-ready="true"]')
    page.wait_for_selector('body[data-spine-ready="true"]', timeout=15000)
    page.wait_for_timeout(500)
    wall_time_ms = round((time.perf_counter() - started) * 1000, 2)

    layout = page.evaluate(
        """
        () => {
          const stage = document.querySelector('.world-map-stage').getBoundingClientRect();
          const plane = document.querySelector('.world-plane').getBoundingClientRect();
          const buildings = [...document.querySelectorAll('.map-building')].map((node) => {
            const rect = node.getBoundingClientRect();
            return {
              id: node.dataset.location,
              label: node.querySelector('strong')?.textContent,
              left: rect.left - plane.left,
              right: rect.right - plane.left,
              top: rect.top - plane.top,
              bottom: rect.bottom - plane.top,
            };
          });
          const assets = performance.getEntriesByType('resource')
            .filter((entry) => entry.name.includes('/assets/'))
            .map((entry) => ({
              name: entry.name.split('/').slice(-2).join('/'),
              transferBytes: entry.transferSize,
              decodedBytes: entry.decodedBodySize,
            }));
          const navigation = performance.getEntriesByType('navigation')[0];
          const sidebar = document.querySelector('.sidebar');
          const agentPreview = document.querySelector('.agent-preview');
          const locationGrid = document.querySelector('.location-grid');
          return {
            viewportWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth,
            stage: {
              left: stage.left,
              right: stage.right,
              top: stage.top,
              bottom: stage.bottom,
            },
            worldPlane: {
              width: plane.width,
              height: plane.height,
              transform: document.querySelector('.world-plane').style.transform,
            },
            dashboardPanelsHidden:
              getComputedStyle(sidebar).display === 'none'
              && getComputedStyle(agentPreview).display === 'none'
              && getComputedStyle(locationGrid).display === 'none',
            buildings,
            assetRequests: assets,
            domContentLoadedMs: Math.round(navigation.domContentLoadedEventEnd),
            loadMs: Math.round(navigation.loadEventEnd),
          };
        }
        """
    )
    page.screenshot(
        path=str(SCREENSHOT_ROOT / f"b75-{name}.png"),
        full_page=False,
    )
    labels = [item["label"] for item in layout["buildings"]]
    expected = ["宿舍", "教学楼", "青禾书院", "食堂", "河边步道", "便利店"]
    if sorted(labels) != sorted(expected):
        raise AssertionError(f"{name} 建筑标签不完整：{labels}")
    for building in layout["buildings"]:
        if not (
            0 <= building["left"] < building["right"] <= layout["worldPlane"]["width"]
            and 0 <= building["top"] < building["bottom"] <= layout["worldPlane"]["height"]
        ):
            raise AssertionError(f"{name} 建筑越界：{building}")
    for index, first in enumerate(layout["buildings"]):
        for second in layout["buildings"][index + 1 :]:
            if overlaps(first, second):
                raise AssertionError(
                    f"{name} 建筑重叠：{first['id']} / {second['id']}"
                )
    if layout["scrollWidth"] != layout["viewportWidth"]:
        raise AssertionError(f"{name} 页面存在横向溢出")
    if not layout["dashboardPanelsHidden"]:
        raise AssertionError(f"{name} 仍显示多余仪表盘面板")
    stage_width = layout["stage"]["right"] - layout["stage"]["left"]
    if layout["worldPlane"]["width"] <= stage_width:
        raise AssertionError(f"{name} 地图视口一次展示了完整大世界")
    if console_errors:
        raise AssertionError(f"{name} 控制台错误：{console_errors}")

    player_before = page.locator("#map-player").evaluate(
        "(node) => ({ x: parseFloat(node.style.left), y: parseFloat(node.style.top) })"
    )
    camera_before = layout["worldPlane"]["transform"]
    dialogue_before = page.locator("#scene-dialogue-line").text_content()
    spine_before = page.evaluate("() => window.qingheSpinePlayer.getState()")
    page.keyboard.down("ArrowRight")
    page.wait_for_timeout(3400)
    spine_moving = page.evaluate("() => window.qingheSpinePlayer.getState()")
    page.screenshot(
        path=str(SCREENSHOT_ROOT / f"b75-spine-walk-{name}.png"),
        full_page=False,
    )
    page.keyboard.up("ArrowRight")
    page.wait_for_timeout(260)
    spine_idle = page.evaluate("() => window.qingheSpinePlayer.getState()")
    player_after = page.locator("#map-player").evaluate(
        "(node) => ({ x: parseFloat(node.style.left), y: parseFloat(node.style.top) })"
    )
    dialogue_after = page.locator("#scene-dialogue-line").text_content()
    camera_after = page.locator("#world-plane").evaluate(
        "(node) => node.style.transform"
    )
    if (
        not player_before
        or not player_after
        or camera_before == camera_after
        or player_before["x"] == player_after["x"]
        or dialogue_before == dialogue_after
    ):
        raise AssertionError(f"{name} 地图移动或镜头跟随未生效")
    if (
        not spine_moving["ready"]
        or spine_moving["animation"] != "walk"
        or spine_idle["animation"] != "idle"
        or spine_moving["frames"] <= spine_before["frames"]
        or spine_moving["leftLegRotation"] in (None, 0)
    ):
        raise AssertionError(f"{name} Spine 动画状态异常")
    page.screenshot(
        path=str(SCREENSHOT_ROOT / f"b75-map-moved-{name}.png"),
        full_page=False,
    )
    layout["consoleErrors"] = console_errors
    layout["wallTimeMs"] = wall_time_ms
    layout["pointer"] = "desktop" if name == "desktop" else "mobile"
    layout["cameraMovement"] = {
        "before": camera_before,
        "after": camera_after,
        "playerBefore": player_before,
        "playerAfter": player_after,
        "spineBefore": spine_before,
        "spineMoving": spine_moving,
        "spineIdle": spine_idle,
        "dialogueBefore": dialogue_before,
        "dialogueAfter": dialogue_after,
    }
    return layout


def inspect_interior_dialog(
    page,
    name: str,
    location_id: str,
    expected_title: str,
) -> dict:
    page.evaluate(
        "(locationId) => document.querySelector("
        "`.map-building[data-location=\"${locationId}\"]`).click()",
        location_id,
    )
    dialog = page.locator("#location-dialog")
    dialog.wait_for(state="visible")
    page.wait_for_function(
        """
        () => {
          const image = document.querySelector("#location-dialog-art");
          return image && image.complete && image.naturalWidth > 0;
        }
        """
    )
    title = page.locator("#location-dialog-title").text_content()
    if title != expected_title:
        raise AssertionError(f"{name} 内部标题错误：{title}")
    image_src = page.locator("#location-dialog-art").get_attribute("src")
    if not image_src or "/assets/interiors/" not in image_src:
        raise AssertionError(f"{name} 内部图片未指向资源目录：{image_src}")
    page.screenshot(
        path=str(SCREENSHOT_ROOT / f"b75-interior-{name}.png"),
        full_page=False,
    )
    result = {
        "location": location_id,
        "title": title,
        "image": image_src,
        "description": page.locator("#location-dialog-description").text_content(),
    }
    page.locator("#location-dialog-close").click()
    dialog.wait_for(state="hidden")
    return result


def capture_east_town(browser) -> dict:
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto("http://127.0.0.1:8110/", wait_until="networkidle")
    page.wait_for_selector('body[data-ready="true"]')
    page.wait_for_selector('body[data-spine-ready="true"]', timeout=15000)
    page.wait_for_timeout(300)
    camera_before = page.locator("#world-plane").evaluate(
        "(node) => node.style.transform"
    )
    page.keyboard.down("ArrowRight")
    page.wait_for_timeout(11000)
    page.keyboard.up("ArrowRight")
    page.keyboard.down("ArrowDown")
    page.wait_for_timeout(1500)
    page.keyboard.up("ArrowDown")
    page.wait_for_timeout(260)
    page.screenshot(
        path=str(SCREENSHOT_ROOT / "b75-town-east-desktop.png"),
        full_page=False,
    )
    camera_after = page.locator("#world-plane").evaluate(
        "(node) => node.style.transform"
    )
    player = page.locator("#map-player").evaluate(
        "(node) => ({ x: parseFloat(node.style.left), y: parseFloat(node.style.top) })"
    )
    page.close()
    if camera_before == camera_after or not player:
        raise AssertionError("东侧街区截图前镜头移动未生效")
    return {
        "cameraBefore": camera_before,
        "cameraAfter": camera_after,
        "player": player,
        "screenshot": "docs/screenshots/b75-town-east-desktop.png",
    }


def capture_river_walk(browser) -> dict:
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto("http://127.0.0.1:8110/", wait_until="networkidle")
    page.wait_for_selector('body[data-ready="true"]')
    page.wait_for_selector('body[data-spine-ready="true"]', timeout=15000)
    page.wait_for_timeout(250)
    page.keyboard.down("ArrowRight")
    page.wait_for_timeout(3000)
    page.keyboard.up("ArrowRight")
    page.keyboard.down("ArrowDown")
    page.wait_for_timeout(3000)
    page.keyboard.up("ArrowDown")
    page.wait_for_timeout(250)
    page.screenshot(
        path=str(SCREENSHOT_ROOT / "b75-river-walk-desktop.png"),
        full_page=False,
    )
    camera = page.locator("#world-plane").evaluate(
        "(node) => node.style.transform"
    )
    player = page.locator("#map-player").evaluate(
        "(node) => ({ x: parseFloat(node.style.left), y: parseFloat(node.style.top) })"
    )
    label = page.locator("#map-view-label").text_content()
    page.close()
    if not player or player["y"] < 700 or "河边步道" not in (label or ""):
        raise AssertionError("河边步道截图前移动未到达河边区域")
    return {
        "camera": camera,
        "player": player,
        "label": label,
        "screenshot": "docs/screenshots/b75-river-walk-desktop.png",
    }


def write_interior_overview() -> str:
    labels = [
        ("dorm", "宿舍"),
        ("classroom", "教学楼"),
        ("library", "青禾书院"),
        ("canteen", "食堂"),
        ("river", "河边步道"),
        ("shop", "便利店"),
    ]
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
    except OSError:
        font = ImageFont.load_default()
    cell_width = 330
    cell_height = 240
    overview = Image.new(
        "RGBA",
        (cell_width * 3, cell_height * 2),
        (30, 63, 47, 255),
    )
    draw = ImageDraw.Draw(overview)
    for index, (asset_name, label) in enumerate(labels):
        source = Image.open(
            ROOT / "assets" / "interiors" / f"{asset_name}.png"
        ).convert("RGBA")
        source.thumbnail((306, 172), Image.Resampling.NEAREST)
        x = (index % 3) * cell_width + 12
        y = (index // 3) * cell_height + 36
        draw.rectangle(
            (x - 5, y - 27, x + 311, y + 198),
            fill=(255, 243, 209, 255),
            outline=(117, 87, 46, 255),
            width=3,
        )
        draw.text((x, y - 25), label, fill=(36, 55, 40, 255), font=font)
        overview.alpha_composite(source, (x, y))
    output = SCREENSHOT_ROOT / "b75-interiors-overview.png"
    overview.save(output)
    return output.relative_to(ROOT).as_posix()


def main() -> int:
    browser_path = next((path for path in EDGE_CANDIDATES if path.is_file()), None)
    if not browser_path:
        raise RuntimeError("找不到 Edge 或 Chrome，无法执行视觉检查")

    environment = os.environ.copy()
    dependency_path = ROOT / ".b6-deps"
    if dependency_path.is_dir():
        environment["PYTHONPATH"] = (
            str(dependency_path)
            + os.pathsep
            + environment.get("PYTHONPATH", "")
        )
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8110",
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        wait_for_port(8110)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_path),
                headless=True,
            )
            desktop_page = browser.new_page(
                viewport={"width": 1440, "height": 1000},
            )
            desktop = inspect_page(desktop_page, "desktop")
            desktop_interior = inspect_interior_dialog(
                desktop_page,
                "desktop",
                "loc_dorm",
                "宿舍",
            )
            east_town = capture_east_town(browser)
            river_walk = capture_river_walk(browser)
            mobile_page = browser.new_page(
                viewport={"width": 390, "height": 844},
                is_mobile=True,
            )
            mobile = inspect_page(mobile_page, "mobile")
            mobile_interior = inspect_interior_dialog(
                mobile_page,
                "mobile",
                "loc_dorm",
                "宿舍",
            )
            fallback_page = browser.new_page(
                viewport={"width": 390, "height": 844},
                is_mobile=True,
            )
            fallback_page.route(
                "**/assets/buildings/library.webp",
                lambda route: route.abort(),
            )
            fallback_page.goto(
                "http://127.0.0.1:8110/",
                wait_until="networkidle",
            )
            fallback_page.wait_for_selector('body[data-ready="true"]')
            library = fallback_page.locator(
                '[data-location="loc_library"]'
            )
            fallback_verified = (
                library.locator("strong").text_content() == "青禾书院"
                and library.locator("img.map-building-art").get_attribute(
                    "src"
                )
                == "/assets/icons/brand.png"
            )
            if not fallback_verified:
                raise AssertionError("建筑图片失败后没有保留名称和占位资源")
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)

    report = {
        "schema_version": "rpg-art-budget-v1",
        "captured_on": date.today().isoformat(),
        "desktop": desktop,
        "mobile": mobile,
        "desktop_interior": desktop_interior,
        "mobile_interior": mobile_interior,
        "east_town": east_town,
        "river_walk": river_walk,
        "first_screen_transfer_bytes": {
            "desktop": sum(
                item["transferBytes"] for item in desktop["assetRequests"]
            ),
            "mobile": sum(
                item["transferBytes"] for item in mobile["assetRequests"]
            ),
        },
        "missing_building_fallback_verified": fallback_verified,
        "interior_overview": write_interior_overview(),
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(REPORT_PATH)
    print(json.dumps(report["first_screen_transfer_bytes"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
