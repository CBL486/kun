const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

const BASE_URL = process.env.AIWORLD_EVIDENCE_URL || "http://127.0.0.1:8093";
const EDGE_PATH =
  process.env.AIWORLD_EDGE_PATH
  || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const OUTPUT = path.resolve(__dirname, "..", "docs", "screenshots");

async function fillPersona(page) {
  await page.fill("#persona-name", "潮汐");
  await page.fill("#persona-pronouns", "她");
  await page.fill("#persona-age", "21");
  await page.fill("#persona-appearance", "深海蓝长发与半透明鳍状发饰");
  await page.fill("#persona-identity", "青禾镇夜间图书馆管理员");
  await page.fill("#persona-speech", "简洁安静，偶尔使用海洋比喻");
  await page.fill("#persona-traits", "克制，敏锐，温柔");
  await page.fill("#persona-values", "诚实，保护秘密，理解他人");
  await page.fill("#persona-interests", "潮汐记录，旧地图，鲸歌");
  await page.fill("#persona-goals", "整理青禾镇旧地图");
  await page.fill("#persona-boundaries", "不泄露私密记忆，不假装拥有现实身体");
  await page.fill("#persona-relationship", "谨慎的观察者朋友");
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
    await page.goto(`${BASE_URL}/setup`, { waitUntil: "networkidle" });
    await page.waitForSelector("#persona-panel:not([hidden])");
    const initial = await page.evaluate(() => ({
      setupStatus: document.querySelector("#setup-status").textContent.trim(),
      personaPanelVisible:
        !document.querySelector("#persona-panel").hidden,
      defaultVisible:
        !document.querySelector("#default-persona-button").hidden,
      customVisible:
        !document.querySelector("#custom-persona-button").hidden,
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
      cookie: document.cookie,
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    assert.equal(initial.personaPanelVisible, true);
    assert.equal(initial.defaultVisible, true);
    assert.equal(initial.customVisible, true);
    assert.deepEqual(initial.local, []);
    assert.deepEqual(initial.session, []);
    assert.equal(initial.cookie, "");
    assert.equal(initial.scrollWidth, initial.viewportWidth);

    await page.screenshot({
      path: path.join(OUTPUT, "r4-persona-choice-desktop.png"),
      fullPage: true,
    });

    await page.click("#custom-persona-button");
    await page.waitForSelector("#persona-form:not([hidden])");
    await fillPersona(page);
    await page.screenshot({
      path: path.join(OUTPUT, "r4-persona-form-desktop.png"),
      fullPage: true,
    });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(250);
    const mobile = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    assert.equal(mobile.scrollWidth, mobile.viewportWidth);
    await page.screenshot({
      path: path.join(OUTPUT, "r4-persona-form-mobile.png"),
      fullPage: true,
    });

    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.click("#save-persona-button");
    await page.waitForURL(`${BASE_URL}/`);
    await page.waitForSelector('body[data-ready="true"]');
    const world = await page.evaluate(() => ({
      agentName: state.agent?.agent?.name ?? null,
      agentIdentity: state.agent?.agent?.identity ?? null,
      personaRevision:
        state.agent?.agent?.persona_revision ?? null,
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    assert.equal(world.agentName, "潮汐");
    assert.equal(world.agentIdentity, "青禾镇夜间图书馆管理员");

    await page.goto(`${BASE_URL}/setup`, { waitUntil: "networkidle" });
    await page.waitForSelector("#persona-panel:not([hidden])");
    await page.screenshot({
      path: path.join(OUTPUT, "r4-persona-summary-desktop.png"),
      fullPage: true,
    });
    assert.deepEqual(consoleErrors, []);
    console.log(
      JSON.stringify(
        {
          initial,
          mobile,
          world,
          consoleErrors,
          screenshots: [
            "docs/screenshots/r4-persona-choice-desktop.png",
            "docs/screenshots/r4-persona-form-desktop.png",
            "docs/screenshots/r4-persona-form-mobile.png",
            "docs/screenshots/r4-persona-summary-desktop.png",
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
