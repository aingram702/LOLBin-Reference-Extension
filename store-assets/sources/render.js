// One-off render script for Chrome Web Store promo tiles / screenshots.
// Usage: node render.js <input.html> <output.png> <width> <height>
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');

(async () => {
  const [,, inputFile, outputFile, width, height] = process.argv;
  const w = parseInt(width, 10);
  const h = parseInt(height, 10);

  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(inputFile));
  await page.screenshot({ path: outputFile, clip: { x: 0, y: 0, width: w, height: h } });
  await browser.close();
  console.log('Rendered', outputFile);
})();
