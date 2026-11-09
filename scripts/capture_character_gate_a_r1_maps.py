"""Capture Gate A R1 candidate sprites inside the real local game page."""

from __future__ import annotations

import base64
import json
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

import uvicorn
from PIL import Image
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import create_app
from app.persona import PersonaStore
from app.setup import DeepSeekSetupStore


OUTPUT_ROOT = ROOT / "art-source" / "character-v2" / "gate-a-r1"
REPORT_PATH = ROOT / "docs" / "character-art-v2" / "gate-a-r1-map-evidence.json"
STYLES = ("a", "b", "c")
DIRECTIONS = ("down", "left", "right", "up")
VIEWPORTS = {
    "desktop": {"width": 1440, "height": 1000},
    "mobile": {"width": 390, "height": 844},
}
HOST = "127.0.0.1"
PORT = 8127
EDGE_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
)


class FakeValidator:
    def validate(self, api_key: str) -> None:
        if api_key != "sk-test-character-gate-a-r1":
            raise AssertionError("unexpected evidence key")


def wait_for_port(port: int, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.4)
            if sock.connect_ex((HOST, port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError("Gate A R1 local API did not start in time")


def build_application():
    evidence_root = Path(
        tempfile.mkdtemp(prefix="aiworld-character-gate-a-r1-")
    )
    setup = DeepSeekSetupStore(
        evidence_root / "setup",
        secure_acl=False,
    )
    setup.save_key("sk-test-character-gate-a-r1", FakeValidator())
    persona = PersonaStore(evidence_root / "persona")
    persona.use_default()
    setup.complete(persona_configured=True)
    application = create_app(
        setup_store=setup,
        setup_validator=FakeValidator(),
        persona_store=persona,
        setup_gate=True,
    )
    return application


def data_url(path: Path) -> str:
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{payload}"


def prepare_page(page: Page) -> dict:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: (
            console_errors.append(message.text)
            if message.type == "error"
            else None
        ),
    )
    page.goto(f"http://{HOST}:{PORT}/", wait_until="networkidle")
    page.wait_for_selector('body[data-ready="true"]')
    page.wait_for_selector('body[data-map-ready="true"]')
    page.wait_for_selector('body[data-character-player="ready"]')
    page.wait_for_timeout(500)
    page.evaluate(
        """
        () => {
          window.qingheCharacterPlayer.update = () => {};
          const sprite = document.querySelector("#map-player-sprite");
          const fallback = document.querySelector("#map-player-fallback");
          const player = document.querySelector("#map-player");
          const stage = document.querySelector(".world-map-stage");
          sprite.hidden = false;
          fallback.hidden = true;
          sprite.style.backgroundRepeat = "no-repeat";
          sprite.style.backgroundPosition = "0 0";
          sprite.style.backgroundSize = "48px 72px";
          sprite.style.imageRendering = "pixelated";
          player.hidden = false;
          if (getComputedStyle(stage).display === "none") {
            throw new Error("map stage is hidden");
          }
        }
        """
    )
    return {"console_errors": console_errors}


def apply_direction(page: Page, style: str, direction: str) -> dict:
    frame_path = OUTPUT_ROOT / style / "source" / f"{direction}.png"
    encoded = data_url(frame_path)
    return page.evaluate(
        """
        ({ source, direction }) => {
          const sprite = document.querySelector("#map-player-sprite");
          sprite.style.backgroundImage = `url("${source}")`;
          sprite.dataset.direction = direction;
          sprite.dataset.action = "idle";
          sprite.dataset.frame = "0";
          const stage = document
            .querySelector(".world-map-stage")
            .getBoundingClientRect();
          const player = document
            .querySelector("#map-player")
            .getBoundingClientRect();
          return {
            stage: {
              left: stage.left,
              top: stage.top,
              right: stage.right,
              bottom: stage.bottom,
            },
            player: {
              left: player.left,
              top: player.top,
              right: player.right,
              bottom: player.bottom,
              width: player.width,
              height: player.height,
            },
            backgroundSize:
              getComputedStyle(sprite).backgroundSize,
            imageRendering:
              getComputedStyle(sprite).imageRendering,
          };
        }
        """,
        {"source": encoded, "direction": direction},
    )


def capture_style(browser, style: str) -> list[dict]:
    evidence = []
    for viewport_name, viewport in VIEWPORTS.items():
        page = browser.new_page(viewport=viewport)
        try:
            telemetry = prepare_page(page)
            for direction in DIRECTIONS:
                bounds = apply_direction(page, style, direction)
                player = bounds["player"]
                stage = bounds["stage"]
                if (
                    player["width"] != 48
                    or player["height"] != 72
                    or player["left"] < stage["left"]
                    or player["right"] > stage["right"]
                    or player["top"] < stage["top"]
                    or player["bottom"] > stage["bottom"]
                ):
                    raise AssertionError(
                        f"{style}/{viewport_name}/{direction} player "
                        f"is outside the runtime map bounds: {bounds}"
                    )
                output = (
                    OUTPUT_ROOT
                    / style
                    / f"map-{viewport_name}-{direction}.png"
                )
                page.screenshot(path=str(output), full_page=False)
                canonical = OUTPUT_ROOT / style / f"map-{viewport_name}.png"
                if direction == "down":
                    canonical.write_bytes(output.read_bytes())
                with Image.open(output) as screenshot:
                    if screenshot.size != (
                        viewport["width"],
                        viewport["height"],
                    ):
                        raise AssertionError(
                            f"unexpected screenshot size: {screenshot.size}"
                        )
                evidence.append(
                    {
                        "style": style,
                        "viewport": viewport_name,
                        "direction": direction,
                        "path": output.relative_to(ROOT).as_posix(),
                        "canonical_path": (
                            canonical.relative_to(ROOT).as_posix()
                            if direction == "down"
                            else None
                        ),
                        "size": [
                            viewport["width"],
                            viewport["height"],
                        ],
                        "runtime_display": [48, 72],
                        "background_size": bounds["backgroundSize"],
                        "image_rendering": bounds["imageRendering"],
                        "player_bounds": bounds["player"],
                        "stage_bounds": bounds["stage"],
                        "console_errors": telemetry["console_errors"],
                    }
                )
            if telemetry["console_errors"]:
                raise AssertionError(
                    f"{style}/{viewport_name} console errors: "
                    f"{telemetry['console_errors']}"
                )
        finally:
            page.close()
    return evidence


def main() -> int:
    browser_path = next(
        (path for path in EDGE_CANDIDATES if path.is_file()),
        None,
    )
    if browser_path is None:
        raise RuntimeError("Edge or Chrome is required for screenshot capture")

    application = build_application()
    config = uvicorn.Config(
        application,
        host=HOST,
        port=PORT,
        log_level="warning",
        lifespan="on",
    )
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    wait_for_port(PORT)

    evidence: list[dict] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_path),
                headless=True,
            )
            try:
                for style in STYLES:
                    evidence.extend(capture_style(browser, style))
            finally:
                browser.close()
    finally:
        server.should_exit = True
        server_thread.join(timeout=10)
        if server_thread.is_alive():
            raise RuntimeError("Gate A R1 local API did not shut down")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "schema_version": "rpg-character-gate-a-r1-map-evidence-v1",
                "page": "web/index.html",
                "server_route": "/",
                "runtime_display": [48, 72],
                "viewports": VIEWPORTS,
                "styles": list(STYLES),
                "directions": list(DIRECTIONS),
                "evidence": evidence,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"captured {len(evidence)} Gate A R1 map screenshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
