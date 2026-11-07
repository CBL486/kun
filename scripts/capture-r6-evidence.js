const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

const BASE_URL = process.env.AIWORLD_EVIDENCE_URL || "http://127.0.0.1:8095";
const EDGE_PATH =
  process.env.AIWORLD_EDGE_PATH
  || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const OUTPUT = path.resolve(__dirname, "..", "docs", "screenshots");

async function sendMessage(page, message) {
  await page.fill("#chat-message", message);
  await page.click("#chat-submit");
  await page.waitForFunction(
    () => !document.querySelector("#chat-submit").disabled,
  );
  return page.evaluate(() => {
    const replies = [...document.querySelectorAll(".chat-message")];
    return replies.slice(-2).map((item) => ({
      text: item.querySelector("p")?.textContent || "",
      note: item.querySelector("small")?.textContent || "",
    }));
  });
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
    await page.click('.mobile-nav [data-view="chat"]');
    const normal = await sendMessage(page, "我想听听你最近在想什么。");
    assert.equal(normal.length, 2);
    assert.equal(normal[1].note, "林澄回应");
    assert.match(normal[1].text, /我听见了/);
    assert.doesNotMatch(normal[1].text, /免责声明|系统提示|数据库/);
    await page.screenshot({
      path: path.join(OUTPUT, "r6-in-world-chat-desktop.png"),
      fullPage: true,
    });

    const identity = await sendMessage(page, "你是不是 AI？");
    assert.match(identity[1].text, /我是林澄/);
    assert.doesNotMatch(identity[1].text, /我是 AI/);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(250);
    const mobile = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    assert.equal(mobile.scrollWidth, mobile.viewportWidth);
    await page.screenshot({
      path: path.join(OUTPUT, "r6-in-world-chat-mobile.png"),
      fullPage: true,
    });
    assert.deepEqual(consoleErrors, []);
    console.log(
      JSON.stringify(
        {
          normal,
          identity,
          mobile,
          consoleErrors,
          screenshots: [
            "docs/screenshots/r6-in-world-chat-desktop.png",
            "docs/screenshots/r6-in-world-chat-mobile.png",
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
