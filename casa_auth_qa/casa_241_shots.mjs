/**
 * Headless shots for CASA 2.4.1 on Velvet Elves staging only.
 * Injects an API login JWT (no /login screenshot). Does not change email or MFA.
 *
 *   $env:QA_PASSWORD='…'; node casa_241_shots.mjs
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
const API = 'https://api.stage.velvetelves.com'
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '2.4.1')
mkdirSync(OUT, { recursive: true })

const loginResp = await fetch(`${API}/api/v1/users/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded', Accept: 'application/json' },
  body: new URLSearchParams({ username: EMAIL, password: PASSWORD }),
})
const loginJson = await loginResp.json()
const token = loginJson.access_token
if (!loginResp.ok || typeof token !== 'string') {
  console.error('login failed', loginResp.status, loginJson.mfa_required ? 'mfa_required' : '')
  process.exit(1)
}

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
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.evaluate((t) => {
    localStorage.setItem('velvet_elves_token', t)
  }, token)
  await page.goto(`${APP}/settings/account`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.getByText(/personal information/i).waitFor({ timeout: 25000 })
  await page.waitForTimeout(800)
  if (page.url().includes('/login')) {
    throw new Error(`redirected to login: ${page.url()}`)
  }
  await shot('CASA_2_4_1_profile.png')

  await page.goto(`${APP}/settings/security`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  const turnOff = page.getByRole('button', { name: /turn off two-step verification/i })
  try {
    await turnOff.waitFor({ timeout: 20000 })
    await turnOff.click()
    await page.getByRole('button', { name: /^turn off$/i }).click()
    await page.getByText(/enter a current code to turn two-step verification off/i).waitFor({
      timeout: 15000,
    })
    await page.waitForTimeout(400)
    await shot('CASA_2_4_1_mfa_stepup.png')
    await page.getByRole('button', { name: /keep it on/i }).click()
  } catch (err) {
    console.error('mfa step-up shot skipped:', err.message)
  }
} finally {
  await browser.close()
  await fetch(`${API}/api/v1/users/logout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  }).catch(() => {})
}
