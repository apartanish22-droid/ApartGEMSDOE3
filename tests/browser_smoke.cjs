/* Optional browser integration test: npm ci && npm run test:browser */
const { chromium: playwright } = require('playwright-core');
const chromium = require('@sparticuz/chromium');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'registry/focus_sites.json')));
const refs = Object.fromEntries(manifest.sites.map(row => [row.repo, row.ref]));
const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.md': 'text/plain' };

async function main() {
  const server = http.createServer((req, res) => {
    let route;
    try { route = decodeURIComponent(new URL(req.url, 'http://local').pathname); } catch (_) { res.writeHead(400).end(); return; }
    const file = path.resolve(root, `.${route === '/' ? '/index.html' : route}`);
    if (!file.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
    fs.readFile(file, (err, bytes) => {
      if (err) { res.writeHead(404).end(); return; }
      res.writeHead(200, { 'content-type': types[path.extname(file)] || 'application/octet-stream' });
      res.end(bytes);
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await playwright.launch({ executablePath: await chromium.executablePath(), args: chromium.args, headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.route('https://fonts.googleapis.com/**', route => route.abort());
    await page.route('https://fonts.gstatic.com/**', route => route.abort());
    let mode = 'unchanged';
    await page.route('https://api.github.com/repos/**/commits/main', route => {
      const repo = new URL(route.request().url()).pathname.match(/^\/repos\/(.+)\/commits\/main$/)?.[1];
      if (mode === 'unknown' && repo === manifest.sites[0].repo) return route.fulfill({ status: 403, body: '{}' });
      const sha = mode === 'changed' && repo === manifest.sites[0].repo ? 'f'.repeat(40) : refs[repo];
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ sha }) });
    });
    await page.goto(base, { waitUntil: 'domcontentloaded' });
    await page.getByText('All nine historical source heads unchanged', { exact: false }).waitFor();
    assert.equal(await page.locator('tbody tr').count(), 9);
    assert.equal(await page.locator('button[disabled]').count(), 1);
    assert.equal(await page.locator('a[download$=".tif"]').count(), 0);
    assert.match(await page.locator('body').innerText(), /No competition-ready TIFF is available/);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    if (process.env.SCREENSHOTS) await page.screenshot({ path: path.join(root, '.cache/overview-desktop.png'), fullPage: true });
    mode = 'changed';
    await page.getByRole('button', { name: 'Check again' }).click();
    await page.getByText('1 source(s) changed', { exact: false }).waitFor();
    mode = 'unknown';
    await page.getByRole('button', { name: 'Check again' }).click();
    await page.getByText('Freshness unknown', { exact: false }).waitFor();
    await page.getByRole('link', { name: 'Submission guide', exact: true }).click();
    assert.match(await page.locator('body').innerText(), /No new submission file is authorized/);
    assert.match(await page.locator('body').innerText(), /range \[0, 1\]/);
    await page.getByRole('link', { name: 'Research', exact: true }).click();
    assert.match(await page.locator('body').innerText(), /HOLDOUT-DTI 0\.194164/);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base, { waitUntil: 'domcontentloaded' });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'mobile document should not overflow horizontally');
    assert.equal(await page.locator('tbody tr').count(), 9);
    assert.equal(await page.locator('.scroll-hint').isVisible(), true);
    await page.locator('.table-wrap').focus();
    await page.keyboard.press('ArrowRight');
    await page.waitForFunction(() => document.querySelector('.table-wrap').scrollLeft > 0);
    if (process.env.SCREENSHOTS) await page.screenshot({ path: path.join(root, '.cache/overview-mobile.png'), fullPage: true });
    assert.deepEqual(errors, []);
    console.log('Browser smoke: desktop, mobile, navigation, source freshness and fail-closed status passed.');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
