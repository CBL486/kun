const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

const BASE_URL = process.env.AIWORLD_EVIDENCE_URL || "http://127.0.0.1:8092";
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
    await page.goto(`${BASE_URL}/setup`, { waitUntil: "networkidle" });
    await page.waitForSelector("#key-form");
    const storage = await page.evaluate(() => ({
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
      cookie: document.cookie,
      keyType: document.querySelector("#deepseek-key")?.type,
      autocomplete: document.querySelector("#deepseek-key")?.autocomplete,
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    assert.deepEqual(storage.local, []);
    assert.deepEqual(storage.session, []);
    assert.equal(storage.cookie, "");
    assert.equal(storage.keyType, "password");
    assert.equal(storage.autocomplete, "off");
    assert.equal(storage.scrollWidth, storage.viewportWidth);

    await page.screenshot({
      path: path.join(OUTPUT, "r3-setup-desktop.png"),
      fullPage: true,
    });
    await page.click("#help-button");
    await page.waitForSelector("#help-dialog[open]");
    await page.screenshot({
      path: path.join(OUTPUT, "r3-setup-tutorial.png"),
      fullPage: true,
    });
    await page.click("#help-close");

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(250);
    const mobileWidth = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    assert.equal(mobileWidth.scrollWidth, mobileWidth.viewportWidth);
    await page.screenshot({
      path: path.join(OUTPUT, "r3-setup-mobile.png"),
      fullPage: true,
    });
    assert.deepEqual(consoleErrors, []);
    console.log(
      JSON.stringify(
        {
          storage,
          mobileWidth,
          consoleErrors,
          screenshots: [
            "docs/screenshots/r3-setup-desktop.png",
            "docs/screenshots/r3-setup-tutorial.png",
            "docs/screenshots/r3-setup-mobile.png",
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
