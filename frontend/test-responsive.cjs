const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const devices = [
  { name: 'iPhone-SE', width: 375, height: 667, mobile: true },
  { name: 'iPhone-14', width: 390, height: 844, mobile: true },
  { name: 'iPhone-14-Pro-Max', width: 430, height: 932, mobile: true },
  { name: 'iPad-Mini', width: 768, height: 1024, mobile: true },
  { name: 'iPad-Pro', width: 1024, height: 1366, mobile: true },
  { name: 'Desktop-Small', width: 1280, height: 800, mobile: false },
  { name: 'Desktop-Large', width: 1920, height: 1080, mobile: false },
];

const pages = [
  { name: 'sample-size', path: '/' },
  { name: 'analyze', path: '/analyze' },
  { name: 'timing', path: '/timing' },
  { name: 'diff-in-diff', path: '/diff-in-diff' },
];

async function testResponsive() {
  const screenshotsDir = path.join(__dirname, 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir);
  }

  const browser = await puppeteer.launch({ headless: true });
  
  for (const device of devices) {
    console.log(`\nTesting on ${device.name} (${device.width}x${device.height})...`);
    
    const page = await browser.newPage();
    await page.setViewport({
      width: device.width,
      height: device.height,
      isMobile: device.mobile,
      hasTouch: device.mobile,
    });

    for (const pageInfo of pages) {
      const url = `http://localhost:5173${pageInfo.path}`;
      console.log(`  - Loading ${pageInfo.name}...`);
      
      try {
        await page.goto(url, { waitUntil: 'networkidle0', timeout: 10000 });
        await new Promise(r => setTimeout(r, 500));
        
        const filename = `${device.name}_${pageInfo.name}.png`;
        await page.screenshot({
          path: path.join(screenshotsDir, filename),
          fullPage: true,
        });
        console.log(`    Saved: ${filename}`);
      } catch (err) {
        console.log(`    Error: ${err.message}`);
      }
    }
    
    await page.close();
  }

  await browser.close();
  console.log(`\nDone! Screenshots saved to: ${screenshotsDir}`);
}

testResponsive().catch(console.error);
