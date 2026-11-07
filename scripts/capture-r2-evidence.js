const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

const BASE_URL = process.env.AIWORLD_EVIDENCE_URL || "http://127.0.0.1:8094";
const EDGE_PATH =
  process.env.AIWORLD_EDGE_PATH
  || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const OUTPUT = path.resolve(__dirname, "..", "docs", "screenshots");

async function step(page, presence, frames = 8) {
  return page.evaluate(
    ({ currentPresence, count }) => {
      for (let index = 0; index < count; index += 1) {
        window.qingheCharacterPlayer.update(100, currentPresence, false);
      }
      return window.qingheCharacterPlayer.getState();
    },
    { currentPresence: presence, count: frames },
  );
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
    await page.waitForFunction(
      () => document.body.dataset.characterPlayer === "ready",
    );
    await page.evaluate(() => stopMapAnimation());
    const base = await page.evaluate(() => ({
      controls: document.querySelectorAll("[data-move]").length,
      nav: document.querySelectorAll(".mobile-nav [data-view]").length,
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
      player: window.qingheCharacterPlayer.getState(),
    }));
    assert.equal(base.controls, 0);
    assert.equal(base.nav, 5);
    assert.equal(base.scrollWidth, base.viewportWidth);
    await page.screenshot({
      path: path.join(OUTPUT, "r2-idle-desktop.png"),
      fullPage: true,
    });

    const rightWalk = {
      facing: "right",
      animation: "walk",
      moving: true,
    };
    const walking = await step(page, rightWalk);
    assert.equal(walking.action, "walk");
    assert.equal(walking.direction, "right");
    await page.screenshot({
      path: path.join(OUTPUT, "r2-walk-desktop.png"),
      fullPage: true,
    });

    const upWalk = {
      facing: "up",
      animation: "walk",
      moving: true,
    };
    const upward = await step(page, upWalk, 3);
    assert.equal(upward.direction, "up");

    const stopping = await step(
      page,
      { facing: "up", animation: "idle", moving: false },
      1,
    );
    assert.equal(stopping.action, "stop");
    const settled = await step(
      page,
      { facing: "up", animation: "idle", moving: false },
      4,
    );
    assert.equal(settled.action, "idle");

    await page.setViewportSize({ width: 390, height: 844 });
    await step(page, rightWalk, 8);
    await page.waitForTimeout(250);
    const mobile = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
      player: window.qingheCharacterPlayer.getState(),
    }));
    assert.equal(mobile.scrollWidth, mobile.viewportWidth);
    await page.screenshot({
      path: path.join(OUTPUT, "r2-walk-mobile.png"),
      fullPage: true,
    });
    assert.deepEqual(consoleErrors, []);
    console.log(
      JSON.stringify(
        {
          base,
          walking,
          upward,
          stopping,
          settled,
          mobile,
          consoleErrors,
          screenshots: [
            "docs/screenshots/r2-idle-desktop.png",
            "docs/screenshots/r2-walk-desktop.png",
            "docs/screenshots/r2-walk-mobile.png",
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
