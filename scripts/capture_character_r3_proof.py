"""Capture the R3 proven character in the real game map."""

from __future__ import annotations

import base64
import json
import socket
import tempfile
import threading
import time
from pathlib import Path

import uvicorn
from PIL import Image
from playwright.sync_api import Page, sync_playwright

from app.main import create_app
from app.persona import PersonaStore
from app.setup import DeepSeekSetupStore


ROOT = Path(__file__).resolve().parents[1]
PROOF_ROOT = ROOT / "art-source" / "character-v2" / "r3-proof"
REPORT = (
    ROOT
    / "docs"
    / "character-art-v2"
    / "r3-proof-map-evidence.json"
)
HOST = "127.0.0.1"
PORT = 8129
VIEWPORTS = {
    "desktop": {"width": 1440, "height": 1000},
    "mobile": {"width": 390, "height": 844},
}
EDGE_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
)


class FakeValidator:
    def validate(self, api_key: str) -> None:
        if api_key != "sk-test-character-r3-proof":
            raise AssertionError("unexpected evidence key")


def wait_for_port(port: int, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.4)
            if sock.connect_ex((HOST, port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError("R3 local API did not start in time")


def build_application():
    temp_root = Path(tempfile.mkdtemp(prefix="aiworld-r3-proof-"))
    setup = DeepSeekSetupStore(temp_root / "setup", secure_acl=False)
    setup.save_key("sk-test-character-r3-proof", FakeValidator())
    persona = PersonaStore(temp_root / "persona")
    persona.use_default()
    setup.complete(persona_configured=True)
    return create_app(
        setup_store=setup,
        setup_validator=FakeValidator(),
        persona_store=persona,
        setup_gate=True,
    )


def data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def prepare_page(page: Page) -> list[str]:
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
          sprite.hidden = false;
          fallback.hidden = true;
          sprite.style.backgroundImage =
            `url("${window.__r3SpriteData}")`;
          sprite.style.backgroundSize = "48px 72px";
          sprite.style.backgroundPosition = "0 0";
          sprite.style.imageRendering = "pixelated";
        }
        """
    )
    return console_errors


def main() -> int:
    browser_path = next(
        (path for path in EDGE_CANDIDATES if path.is_file()),
        None,
    )
    if browser_path is None:
        raise RuntimeError("Edge or Chrome is required")

    application = build_application()
    server = uvicorn.Server(
        uvicorn.Config(
            application,
            host=HOST,
            port=PORT,
            log_level="warning",
            lifespan="on",
        )
    )
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    wait_for_port(PORT)
    evidence = []
    source = data_url(PROOF_ROOT / "source" / "down.png")
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_path),
                headless=True,
            )
            try:
                for name, viewport in VIEWPORTS.items():
                    page = browser.new_page(viewport=viewport)
                    try:
                        page.add_init_script(
                            f"window.__r3SpriteData = {json.dumps(source)};"
                        )
                        errors = prepare_page(page)
                        bounds = page.evaluate(
                            """
                            () => {
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
                              };
                            }
                            """
                        )
                        if errors:
                            raise AssertionError(errors)
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
                            raise AssertionError(bounds)
                        output = PROOF_ROOT / f"map-{name}-down.png"
                        page.screenshot(path=str(output), full_page=False)
                        with Image.open(output) as image:
                            assert image.size == (
                                viewport["width"],
                                viewport["height"],
                            )
                        evidence.append(
                            {
                                "viewport": name,
                                "path": output.relative_to(ROOT).as_posix(),
                                "size": [
                                    viewport["width"],
                                    viewport["height"],
                                ],
                                "runtime_display": [48, 72],
                                "player_bounds": bounds["player"],
                                "stage_bounds": bounds["stage"],
                                "console_errors": errors,
                            }
                        )
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        server.should_exit = True
        server_thread.join(timeout=10)
        if server_thread.is_alive():
            raise RuntimeError("R3 local API did not shut down")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            {
                "schema_version": "rpg-character-r3-map-evidence-v1",
                "page": "web/index.html",
                "source": (
                    "art-source/character-v2/r3-proof/source/down.png"
                ),
                "evidence": evidence,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"captured {len(evidence)} R3 map screenshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
