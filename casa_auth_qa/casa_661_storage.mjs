/**
 * Staging logout: record localStorage key presence (never values).
 *   $env:QA_PASSWORD='…'; node casa_661_storage.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
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
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '6.6.1')
mkdirSync(OUT, { recursive: true })

async function keys(page) {
  return page.evaluate(() => {
    const names = []
    for (let i = 0; i < localStorage.length; i++) {
      names.push(localStorage.key(i))
    }
    return {
      token: localStorage.getItem('velvet_elves_token') !== null,
      refresh: localStorage.getItem('velvet_elves_refresh_token') !== null,
      names: names.filter(Boolean).sort(),
    }
  })
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

const result = {
  before: null,
  after: null,
  url_after: '',
  path: 'unknown',
  error: null,
}

try {
  await page.goto(`${APP}/login?nocache=${Date.now()}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  })
  await page.locator('#login-email').waitFor({ timeout: 20000 })
  await page.locator('#login-email').fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /^sign in$/i }).click()
  await page.waitForTimeout(3000)

  const signOutBtn = page.getByRole('button', { name: /sign out/i })
  const mfa = await page.getByRole('heading', { name: /two-step verification/i }).isVisible().catch(() => false)
  const stillLogin = page.url().includes('/login') && !mfa

  result.before = await keys(page)

  if (await signOutBtn.isVisible().catch(() => false)) {
    result.path = 'mfa_sign_out'
    await signOutBtn.click()
  } else if (stillLogin) {
    result.path = 'still_login'
    result.error = `still on login: ${page.url()}`
  } else {
    result.path = 'menu_log_out'
    await page.locator('header img').first().waitFor({ timeout: 15000 }).catch(() => {})
    await page.waitForTimeout(1500)
    const name = page.locator('p').filter({ hasText: /@|Admin|Owner/ }).first()
    await name.click({ timeout: 15000 })
    await page.getByRole('menuitem', { name: /log out/i }).waitFor({ timeout: 10000 })
    await page.getByRole('menuitem', { name: /log out/i }).click()
  }

  await page.getByRole('heading', { name: /welcome back/i }).waitFor({ timeout: 20000 })
  await page.waitForTimeout(400)
  result.after = await keys(page)
  result.url_after = page.url().split('?')[0]
  await page.screenshot({ path: path.join(OUT, 'CASA_6_6_1_after_logout.png'), fullPage: false })
} catch (err) {
  result.error = String(err).slice(0, 240)
} finally {
  await browser.close()
}

writeFileSync(path.join(OUT, '_storage.json'), JSON.stringify(result, null, 2))
console.log('path', result.path)
console.log('error', result.error)
console.log('before_token', result.before?.token, 'before_refresh', result.before?.refresh)
console.log('after_token', result.after?.token, 'after_refresh', result.after?.refresh)
console.log('url_after', result.url_after)
if (result.error || !result.after || result.after.token || result.after.refresh) {
  process.exit(1)
}
