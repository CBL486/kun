const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

const BASE_URL = process.env.AIWORLD_EVIDENCE_URL || "http://127.0.0.1:8091";
const EDGE_PATH =
  process.env.AIWORLD_EDGE_PATH
  || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const OUTPUT = path.resolve(
  __dirname,
  "..",
  "docs",
  "screenshots",
);

async function readPlayerState(page) {
  return page.evaluate(() => ({
    x: mapState.x,
    y: mapState.y,
    targetX: mapState.targetX,
    targetY: mapState.targetY,
    presenceRevision: mapState.presenceRevision,
    stateRevision: state.world?.world?.state_revision ?? null,
    presence: Boolean(state.world?.agent_presence),
    moveControls: document.querySelectorAll("[data-move]").length,
    navigationItems: document.querySelectorAll(".mobile-nav [data-view]").length,
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
  }));
}

async function main() {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const browser = await chromium.launch({
    executablePath: EDGE_PATH,
    headless: true,
  });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
  });
  const consoleErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));

  try {
    await page.goto(BASE_URL, { waitUntil: "networkidle" });
    await page.waitForSelector('body[data-ready="true"]');
    await page.waitForSelector("#map-player:not([hidden])");
    await page.waitForTimeout(500);

    const before = await readPlayerState(page);
    assert.equal(before.moveControls, 0);
    assert.equal(before.navigationItems, 5);
    assert.equal(before.presence, true);
    assert.equal(before.presenceRevision, before.stateRevision);
    assert.equal(before.scrollWidth, before.viewportWidth);

    await page.keyboard.press("ArrowRight");
    await page.keyboard.press("KeyW");
    await page.waitForTimeout(350);
    const afterKeyboard = await readPlayerState(page);
    assert.equal(afterKeyboard.targetX, before.targetX);
    assert.equal(afterKeyboard.targetY, before.targetY);

    await page.screenshot({
      path: path.join(OUTPUT, "r1-observer-desktop.png"),
      fullPage: true,
    });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(300);
    const mobile = await readPlayerState(page);
    assert.equal(mobile.navigationItems, 5);
    assert.equal(mobile.scrollWidth, mobile.viewportWidth);
    await page.screenshot({
      path: path.join(OUTPUT, "r1-observer-mobile.png"),
      fullPage: true,
    });

    assert.deepEqual(consoleErrors, []);
    console.log(
      JSON.stringify(
        {
          before,
          afterKeyboard,
          mobile,
          consoleErrors,
          screenshots: [
            "docs/screenshots/r1-observer-desktop.png",
            "docs/screenshots/r1-observer-mobile.png",
          ],
        },
        null,
        2,
      ),
    );
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
