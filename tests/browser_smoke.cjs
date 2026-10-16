// Development-only dependency: see web/README.md. No app dependencies required.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { resolve } = require('node:path');
const { pathToFileURL } = require('node:url');
const { mkdir, writeFile } = require('node:fs/promises');

const sizes = [
  ['desktop', 1920, 1080], ['desktop', 1440, 900], ['tablet', 768, 1024],
  ['mobile', 390, 844], ['mobile', 375, 812],
];
const panels = ['overview', 'features', 'evaluation'];
const output = resolve(__dirname, '../docs/screenshots');

async function checkState(page, active) {
  assert.equal(await page.locator('[role="tabpanel"]:visible').count(), 1);
  for (const id of panels) {
    const tab = page.locator(`[aria-controls="${id}"]`);
    assert.equal(await tab.getAttribute('aria-selected'), String(id === active));
    assert.equal(await tab.getAttribute('tabindex'), id === active ? '0' : '-1');
    assert.equal(await page.locator(`#${id}`).isVisible(), id === active);
    assert(await tab.isEnabled());
  }
  const colors = await page.locator('[role="tab"]').evaluateAll(tabs =>
    tabs.map(tab => getComputedStyle(tab).backgroundColor));
  const selected = panels.indexOf(active);
  assert(colors.every((color, index) => index === selected || color !== colors[selected]),
    'Selected button must have a distinct background');
}

async function checkLayout(page) {
  const layout = await page.evaluate(() => {
    const overflow = [];
    for (const el of document.querySelectorAll('main, header, section, h1, h2, p, label, select, button, footer, [role="tablist"]')) {
      if (!el.getClientRects().length) continue;
      const rect = el.getBoundingClientRect();
      if (rect.left < -1 || rect.right > innerWidth + 1 || el.scrollWidth > el.clientWidth + 1) {
        overflow.push(el.id || el.tagName);
      }
    }
    // Check rendered text line boxes as well as element boxes; native select
    // option popups are excluded because the dataset control is disabled.
    const walker = document.createTreeWalker(document.querySelector('main'), NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.textContent.trim() || node.parentElement.closest('select')) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      for (const rect of range.getClientRects()) {
        if (rect.width && (rect.left < -1 || rect.right > innerWidth + 1)) {
          overflow.push(`text: ${node.textContent.trim().slice(0, 60)}`);
        }
      }
    }
    window.scrollTo(10000, 0);
    const horizontalScroll = scrollX;
    window.scrollTo(0, 0);
    return { viewportWidth: innerWidth, documentWidth: document.documentElement.scrollWidth,
      documentHeight: document.documentElement.scrollHeight, horizontalScroll, overflow };
  });
  assert.equal(layout.documentWidth, layout.viewportWidth, JSON.stringify(layout));
  assert.equal(layout.horizontalScroll, 0, JSON.stringify(layout));
  assert.deepEqual(layout.overflow, [], JSON.stringify(layout));
  return layout;
}

(async () => {
  await mkdir(output, { recursive: true });
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
  });
  const report = { status: 'RUNNING', timestamp: new Date().toISOString(),
    browser: browser.version(), playwright: require('playwright/package.json').version,
    platform: process.platform, viewportOnly: true, scenarios: [] };
  try {
    for (const [device, width, height] of sizes) {
      for (const protocol of ['http', 'file']) {
        const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
        const errors = [], warnings = [];
        page.on('pageerror', error => errors.push(`JavaScript: ${error.message}`));
        page.on('console', msg => {
          if (msg.type() === 'error') errors.push(`Console: ${msg.text()}`);
          if (msg.type() === 'warning') warnings.push(msg.text());
        });
        page.on('response', response => {
          if (response.status() >= 400) errors.push(`HTTP ${response.status()}: ${response.url()}`);
        });
        page.on('requestfailed', request => errors.push(`Request failed: ${request.url()}`));
        const url = protocol === 'http' ? 'http://localhost:8000/index.html'
          : pathToFileURL(resolve(__dirname, '../web/index.html')).href;
        await page.goto(url, { waitUntil: 'networkidle' });
        await page.evaluate(() => document.fonts.ready);
        assert.equal(await page.title(), 'DIC-2 · Regression Analysis Dashboard');
        assert(await page.locator('#dataset').isDisabled());
        assert.deepEqual(await page.locator('#dataset option').allTextContents(),
          ['50 Startups', 'Boston Housing', 'Custom Dataset']);
        // Initial markup omits tabindex=0 on the selected native button.
        assert.equal(await page.locator('[aria-selected="true"]').evaluate(el => el.tabIndex), 0);
        const scenario = { device, width, height, protocol, tabs: [], errors, warnings };
        report.scenarios.push(scenario);
        for (const id of panels) {
          await page.locator(`[aria-controls="${id}"]`).click();
          await checkState(page, id);
          const layout = await checkLayout(page);
          const screenshot = `${device}-${width}x${height}-${id}.png`;
          if (protocol === 'http') {
            await page.screenshot({ path: resolve(output, screenshot), fullPage: true });
          }
          scenario.tabs.push({ id, ...layout, ...(protocol === 'http' ? { screenshot } : {}) });
        }
        await page.locator('#tab-overview').focus();
        for (const [key, id] of [['ArrowRight', 'features'], ['End', 'evaluation'],
          ['ArrowRight', 'overview'], ['ArrowLeft', 'evaluation'], ['Home', 'overview']]) {
          await page.keyboard.press(key);
          assert.equal(await page.locator(':focus').getAttribute('aria-controls'), id);
          await checkState(page, id);
        }
        for (const key of ['Enter', 'Space']) {
          await page.keyboard.press(key);
          await checkState(page, 'overview');
        }
        await page.keyboard.press('Tab');
        assert.equal(await page.locator(':focus').getAttribute('id'), 'overview');
        await page.keyboard.press('Shift+Tab');
        assert.equal(await page.locator(':focus').getAttribute('id'), 'tab-overview');
        await checkLayout(page);
        assert.deepEqual(errors, []);
        console.log(`PASS ${device} ${width}x${height} ${protocol}: tabs/state/keyboard/layout; errors=0, warnings=${warnings.length}`);
        await page.close();
      }
    }
    report.status = 'PASS';
  } catch (error) {
    report.status = 'FAIL';
    report.failure = error.stack;
    throw error;
  } finally {
    await writeFile(resolve(output, 'verification.json'), JSON.stringify(report, null, 2) + '\n');
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
