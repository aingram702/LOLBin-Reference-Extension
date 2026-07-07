// Launches the real unpacked extension in Chromium and screenshots the actual
// popup.html (not a mockup) so store screenshots reflect real UI.
// Usage: node capture_popup.js <search-query> <os-filter> <output.png>
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');

(async () => {
  const [,, query, osFilter, outFile] = process.argv;
  const extPath = path.resolve(__dirname, '../../extension');
  const userDataDir = '/tmp/claude-0/-home-user-LOLBin-Reference-Extension/4ef71c53-e60c-5fea-a82e-dadb60343928/scratchpad/chrome-profile-' + Date.now();

  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    executablePath: '/opt/pw-browsers/chromium',
    args: [
      `--disable-extensions-except=${extPath}`,
      `--load-extension=${extPath}`,
      '--no-sandbox',
    ],
  });

  let [background] = context.serviceWorkers();
  if (!background) background = await context.waitForEvent('serviceworker');
  const extensionId = background.url().split('/')[2];

  const page = await context.newPage();
  await page.setViewportSize({ width: 440, height: 620 });
  await page.goto(`chrome-extension://${extensionId}/popup.html`);
  await page.waitForTimeout(500);

  if (osFilter && osFilter !== 'all') {
    await page.click(`.filter-btn[data-os="${osFilter}"]`);
  }
  if (query) {
    await page.fill('#searchBox', query);
    await page.waitForTimeout(200);
  }

  const body = await page.$('body');
  await body.screenshot({ path: outFile });
  await context.close();
  console.log('Captured', outFile, 'extensionId=', extensionId);
})();
