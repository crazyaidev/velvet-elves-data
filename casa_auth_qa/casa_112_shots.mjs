/**
 * Headless shots for CASA 1.1.2: expired/invalid activation and reset links,
 * plus the forgot-password form (no generated initial password).
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
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '1.1.2')
mkdirSync(OUT, { recursive: true })

const browser = await chromium.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--disable-gpu', '--disable-dev-shm-usage', '--no-first-run'],
})
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })

async function shot(name, selector) {
  const file = path.join(OUT, name)
  if (selector) {
    const el = page.locator(selector).first()
    await el.waitFor({ timeout: 20000 })
    await el.screenshot({ path: file })
  } else {
    await page.screenshot({ path: file, fullPage: false })
  }
  console.log('wrote', file)
}

try {
  await page.goto(`${APP}/invite/accept?token=00000000000000000000000000000000`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  })
  await page.getByRole('heading', { name: /invalid invitation/i }).waitFor({ timeout: 20000 })
  await shot('CASA_1_1_2_invite_expired.png')

  await page.goto(`${APP}/forgot-password`, {
    waitUntil: 'domcontentloaded',
    timeout: 30000,
  })
  await page.getByLabel(/email address/i).waitFor({ timeout: 20000 })
  await shot('CASA_1_1_2_forgot_password.png')

  await page.goto(`${APP}/reset-password`, {
    waitUntil: 'domcontentloaded',
    timeout: 30000,
  })
  await page.getByRole('heading', { name: /invalid or expired link/i }).waitFor({ timeout: 20000 })
  await shot('CASA_1_1_2_reset_expired.png')
} finally {
  await browser.close()
}
