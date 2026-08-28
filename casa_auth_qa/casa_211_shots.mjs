/**
 * Headless shot for CASA 2.1.1 on Velvet Elves staging only.
 * Login URL has no password or session token query parameters.
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const APP = 'https://app.stage.velvetelves.com'
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '2.1.1')
mkdirSync(OUT, { recursive: true })

const browser = await chromium.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--disable-gpu', '--disable-dev-shm-usage', '--no-first-run'],
})
const page = await browser.newPage({
  viewport: { width: 1280, height: 900 },
  ignoreHTTPSErrors: true,
})

try {
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.locator('#login-email').waitFor({ timeout: 20000 })
  await page.waitForTimeout(600)
  const href = page.url()
  writeFileSync(path.join(OUT, 'login_url.txt'), href, 'utf8')
  console.log('live_url', href)
  const file = path.join(OUT, 'CASA_2_1_1_login_raw.png')
  await page.screenshot({ path: file, fullPage: false })
  console.log('wrote', file)
} finally {
  await browser.close()
}
