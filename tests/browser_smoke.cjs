const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { resolve } = require('node:path');
const { pathToFileURL } = require('node:url');
(async () => {
  const browser = await chromium.launch({executablePath:process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:true});
  try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  await page.goto('http://localhost:8000', {waitUntil:'networkidle'});
  assert.equal(await page.title(), 'DIC-2 · Regression Analysis Dashboard');
  assert.equal(await page.locator('[role="tabpanel"]:visible').count(), 1);
  assert.equal(await page.locator('#dataset').isDisabled(), true);
  console.log('RUN PASS: served shell renders; one initial panel; dataset disabled');
  for (const width of [1440, 375]) {
    await page.setViewportSize({width, height:900});
    for (const id of ['features', 'evaluation', 'overview']) {
      await page.locator(`[aria-controls="${id}"]`).click();
      assert.equal(await page.locator(`#${id}`).isVisible(), true);
      assert.equal(await page.locator('[role="tabpanel"]:visible').count(), 1);
    }
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  }
  await page.locator('#tab-overview').focus();
  for (const [key, id] of [['ArrowRight','tab-features'], ['End','tab-evaluation'], ['ArrowRight','tab-overview'], ['ArrowLeft','tab-evaluation'], ['Home','tab-overview']]) {
    await page.keyboard.press(key);
    assert.equal(await page.locator(':focus').getAttribute('id'), id);
    assert.equal(await page.locator(`#${id}`).getAttribute('aria-selected'), 'true');
  }
  await page.goto(pathToFileURL(resolve(__dirname, '../web/index.html')).href, {waitUntil:'load'});
  await page.locator('#tab-evaluation').click();
  assert.equal(await page.locator('#evaluation').isVisible(), true);
  assert.deepEqual(errors, []);
  console.log('TEST PASS: desktop/mobile tabs, no overflow, keyboard navigation, direct file opening; zero console/page errors');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode=1; });
