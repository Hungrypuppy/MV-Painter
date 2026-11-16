// Render planner.html -> Atelier-Planner-2027.pdf (+ PNG previews)
// usage: node render.js [--previews] [--scale=2]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const args = process.argv.slice(2);
  const previews = args.includes('--previews');
  const scale = Number((args.find(a => a.startsWith('--scale=')) || '--scale=1').split('=')[1]);
  const here = __dirname;
  const url = 'file://' + path.join(here, 'planner.html');
  const browser = await chromium.launch();

  const pdfPage = await browser.newPage();
  await pdfPage.goto(url, { waitUntil: 'load' });
  await pdfPage.evaluate(() => document.fonts.ready);
  await pdfPage.pdf({
    path: path.join(here, 'Atelier-Planner-2027.pdf'),
    width: '1366px', height: '1024px', printBackground: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 }, preferCSSPageSize: true,
  });
  console.log('pdf done');

  if (previews) {
    const outDir = path.join(here, 'previews');
    fs.mkdirSync(outDir, { recursive: true });
    const ctx = await browser.newContext({ viewport: { width: 1366, height: 1024 }, deviceScaleFactor: scale });
    const p = await ctx.newPage();
    await p.goto(url, { waitUntil: 'load' });
    await p.evaluate(() => document.fonts.ready);
    const ids = await p.$$eval('section.page', els => els.map(e => e.id));
    for (let i = 0; i < ids.length; i++) {
      await (await p.$(`section[id="${ids[i]}"]`)).screenshot({ path: path.join(outDir, `${String(i + 1).padStart(2, '0')}-${ids[i]}.png`) });
    }
    console.log('previews', ids.length);
  }
  await browser.close();
})();
