/**
 * Headless shots for CASA 1.2.1 on Velvet Elves staging only.
 * Empty login/register + classic default pair rejected.
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
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '1.2.1')
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
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.locator('#login-email').waitFor({ timeout: 20000 })
  await page.waitForTimeout(800)
  await shot('CASA_1_2_1_login_empty.png')

  await page.fill('#login-email', 'admin@velvetelves.com')
  await page.fill('#login-password', 'Admin')
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.getByRole('alert').waitFor({ timeout: 20000 })
  await page.waitForTimeout(400)
  await shot('CASA_1_2_1_default_rejected.png')

  await page.goto(`${APP}/register`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.getByPlaceholder(/create a strong password/i).waitFor({ timeout: 20000 })
  await page.getByPlaceholder(/create a strong password/i).scrollIntoViewIfNeeded()
  await page.waitForTimeout(400)
  await shot('CASA_1_2_1_register.png')
} finally {
  await browser.close()
}
