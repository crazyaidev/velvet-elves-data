/**
 * Headless Qualys SSL Labs shots for CASA 4.1.1 (and reusable on 4.1.2).
 * One host per run. Usage:
 *   node casa_411_ssllabs.mjs app
 *   node casa_411_ssllabs.mjs api
 */
import { createRequire } from 'module'
import { mkdirSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const TARGETS = {
  app: {
    host: 'app.velvetelves.com',
    overview: 'CASA_4_1_1_ssllabs_app.png',
    proto: 'CASA_4_1_1_ssllabs_app_protocols.png',
  },
  api: {
    host: 'api.prod.velvetelves.com',
    overview: 'CASA_4_1_1_ssllabs_api.png',
    proto: 'CASA_4_1_1_ssllabs_api_protocols.png',
  },
}

const which = process.argv[2]
if (!TARGETS[which]) {
  console.error('Usage: node casa_411_ssllabs.mjs app|api')
  process.exit(2)
}

const { host, overview, proto } = TARGETS[which]
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '4.1.1')
mkdirSync(OUT, { recursive: true })

const url = `https://www.ssllabs.com/ssltest/analyze.html?d=${encodeURIComponent(host)}&latest`

async function dismissCookies(page) {
  const candidates = [
    '#onetrust-accept-btn-handler',
    'button:has-text("Accept All")',
    'button:has-text("Accept all")',
    'button:has-text("I Accept")',
    'button:has-text("Accept")',
    'button:has-text("Agree")',
  ]
  for (const sel of candidates) {
    const btn = page.locator(sel).first()
    if (await btn.isVisible({ timeout: 800 }).catch(() => false)) {
      await btn.click({ timeout: 3000 }).catch(() => {})
      await page.waitForTimeout(400)
      return
    }
  }
}

const browser = await chromium.launch({
  executablePath: CHROME,
  headless: true,
  args: [
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--disable-extensions',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-blink-features=AutomationControlled',
  ],
})
const page = await browser.newPage({
  viewport: { width: 1280, height: 1400 },
  userAgent:
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
})

try {
  console.log('goto', url)
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await dismissCookies(page)

  await page.getByText(host, { exact: false }).first().waitFor({ timeout: 30000 })
  const gradeAlt = page.getByText('A+', { exact: true }).first()
  await gradeAlt.waitFor({ timeout: 25000 })
  await page.waitForTimeout(400)
  const overviewPath = path.join(OUT, overview)
  await page.screenshot({ path: overviewPath, fullPage: false })
  console.log('wrote', overviewPath)

  const ep = page.locator('a[href*="s="]').first()
  await ep.waitFor({ timeout: 15000 })
  const href = await ep.getAttribute('href')
  if (!href) {
    throw new Error('no endpoint href')
  }
  const abs = href.startsWith('http') ? href : new URL(href, 'https://www.ssllabs.com/ssltest/').toString()
  console.log('open endpoint', abs)
  await page.goto(abs, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.waitForTimeout(1200)
  await dismissCookies(page)
  const protocols = page.getByText('Protocols', { exact: true }).first()
  await protocols.waitFor({ timeout: 25000 })
  await protocols.scrollIntoViewIfNeeded()
  await page.waitForTimeout(400)
  const protoPath = path.join(OUT, proto)
  await page.screenshot({ path: protoPath, fullPage: false })
  console.log('wrote', protoPath)
  console.log('final_url', page.url())
} finally {
  await browser.close()
}
