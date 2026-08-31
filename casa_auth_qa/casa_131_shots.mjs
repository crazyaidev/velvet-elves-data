/**
 * Headless shots for CASA 1.3.1 on Velvet Elves staging only.
 * Forgot-password form, 1-hour copy after request, expired reset page.
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
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '1.3.1')
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

async function shot(name) {
  const file = path.join(OUT, name)
  await page.screenshot({ path: file, fullPage: false })
  console.log('wrote', file)
}

try {
  await page.goto(`${APP}/forgot-password`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.getByRole('heading', { name: /forgot your password/i }).waitFor({ timeout: 20000 })
  await page.waitForTimeout(600)
  await shot('CASA_1_3_1_forgot_password.png')

  await page.locator('#forgot-email').fill('casa.evidence@example.com')
  await page.getByRole('button', { name: /send reset link/i }).click()
  await page.getByText(/link expires in 1 hour/i).waitFor({ timeout: 20000 })
  await page.waitForTimeout(400)
  await shot('CASA_1_3_1_expires_1h.png')

  await page.goto(`${APP}/reset-password`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.getByRole('heading', { name: /invalid or expired link/i }).waitFor({ timeout: 20000 })
  await page.waitForTimeout(400)
  await shot('CASA_1_3_1_reset_expired.png')
} finally {
  await browser.close()
}
