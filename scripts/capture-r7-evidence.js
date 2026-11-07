const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

const BASE_URL = process.env.AIWORLD_EVIDENCE_URL || "http://127.0.0.1:8096";
const EDGE_PATH =
  process.env.AIWORLD_EDGE_PATH
  || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const OUTPUT = path.resolve(__dirname, "..", "docs", "screenshots");

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
    const desktop = await page.evaluate(() => ({
      presence: state.world.agent_presence,
      status: document.querySelector("#presence-status").textContent,
      player: window.qingheCharacterPlayer.getState(),
      publicText: document.body.innerText,
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    assert.equal(desktop.presence.location_id, "loc_classroom");
    assert.equal(desktop.presence.animation, "study");
    assert.equal(desktop.player.action, "study");
    assert.match(desktop.status, /学习/);
    assert.doesNotMatch(desktop.publicText, /今天学习了|reflection_memory_id/);
    assert.equal(desktop.scrollWidth, desktop.viewportWidth);
    await page.screenshot({
      path: path.join(OUTPUT, "r7-study-desktop.png"),
      fullPage: false,
      animations: "disabled",
    });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(250);
    const mobile = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
      player: window.qingheCharacterPlayer.getState(),
    }));
    assert.equal(mobile.scrollWidth, mobile.viewportWidth);
    assert.equal(mobile.player.action, "study");
    await page.screenshot({
      path: path.join(OUTPUT, "r7-study-mobile.png"),
      fullPage: false,
      animations: "disabled",
    });
    assert.deepEqual(consoleErrors, []);
    console.log(
      JSON.stringify(
        {
          desktop,
          mobile,
          consoleErrors,
          screenshots: [
            "docs/screenshots/r7-study-desktop.png",
            "docs/screenshots/r7-study-mobile.png",
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
