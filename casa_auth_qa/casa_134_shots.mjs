/**
 * Headless shot for CASA 1.3.4 on Velvet Elves staging only.
 */
import { createRequire } from 'module'
import { mkdirSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const APP = 'https://app.stage.velvetelves.com'
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '1.3.4')
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
  await page.goto(`${APP}/reset-password`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.getByRole('heading', { name: /invalid or expired link/i }).waitFor({ timeout: 20000 })
  await page.waitForTimeout(400)
  const file = path.join(OUT, 'CASA_1_3_4_reset_expired.png')
  await page.screenshot({ path: file, fullPage: false })
  console.log('wrote', file)
} finally {
  await browser.close()
}
