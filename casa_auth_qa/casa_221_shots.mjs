/**
 * Headless shots for CASA 2.2.1 on Velvet Elves staging only.
 *   $env:QA_PASSWORD='…'; node casa_221_shots.mjs
 */
import { createRequire } from 'module'
import { mkdirSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD
if (!PASSWORD) {
  console.error('Set QA_PASSWORD')
  process.exit(2)
}

const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const APP = 'https://app.stage.velvetelves.com'
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '2.2.1')
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
  console.log('wrote', file, 'url', page.url())
}

try {
  await page.goto(`${APP}/login?nocache=${Date.now()}`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.locator('#login-email').waitFor({ timeout: 20000 })
  await page.locator('#login-email').fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /^sign in$/i }).click()
  await page.waitForTimeout(2500)

  const stillLogin = page.url().includes('/login')
  const signOutBtn = page.getByRole('button', { name: /sign out/i })
  if (await signOutBtn.isVisible().catch(() => false)) {
    await shot('CASA_2_2_1_logout_menu.png')
    await signOutBtn.click()
  } else if (stillLogin) {
    await shot('CASA_2_2_1_logout_menu.png')
    throw new Error(`still on login: ${page.url()}`)
  } else {
    // Let TenantThemeSync apply so a bad logo_url would already have swapped src.
    await page.locator('header img').first().waitFor({ timeout: 15000 })
    await page.waitForTimeout(2500)
    const logoSrc = await page.locator('header img').first().getAttribute('src')
    console.log('header logo src', logoSrc)
    const name = page.locator('p').filter({ hasText: /@|Admin|Owner/ }).first()
    await name.click({ timeout: 15000 })
    await page.getByRole('menuitem', { name: /log out/i }).waitFor({ timeout: 10000 })
    await shot('CASA_2_2_1_logout_menu.png')
    await page.getByRole('menuitem', { name: /log out/i }).click()
  }

  await page.getByRole('heading', { name: /welcome back/i }).waitFor({ timeout: 20000 })
  await page.waitForTimeout(400)
  await shot('CASA_2_2_1_after_logout.png')
} finally {
  await browser.close()
}
