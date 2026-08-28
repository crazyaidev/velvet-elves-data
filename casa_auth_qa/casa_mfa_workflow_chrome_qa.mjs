/**
 * Headed Chrome QA for the standard MFA workflow (Settings enroll,
 * platform code-only / setup prompt, disable requires a fresh TOTP).
 *
 *   $env:QA_PASSWORD='…'; node casa_mfa_workflow_chrome_qa.mjs
 */
import { createRequire } from 'module'
import crypto from 'crypto'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const PASS = process.env.QA_PASS || 'mfa1'
const STAMP = new Date().toISOString().slice(0, 10)
const OUT = path.join(__dirname, `artifacts_${STAMP}_${PASS}`)
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'shyna.elene@minafter.com'
const PASSWORD = process.env.QA_PASSWORD
if (!PASSWORD) {
  console.error('Set QA_PASSWORD before running this harness.')
  process.exit(2)
}
const APP = process.env.QA_APP || 'http://127.0.0.1:5173'
const HEADED = process.env.QA_HEADED !== '0'
const SHOTS = process.env.QA_SHOTS !== '0'
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

const findings = []
const consoleErrors = []
const pageErrors = []
const apiLog = []
let shotIdx = 0
let lastLogin = null
let lastMfaEnroll = null
let lastMfaVerify = null
let lastMfaDisable = null
let lastLogout = null

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 8000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 500) : ''}`)
}

async function shot(page, name) {
  if (!SHOTS) return
  shotIdx += 1
  const file = path.join(OUT, `${String(shotIdx).padStart(2, '0')}_${name}.png`)
  try {
    await page.screenshot({ path: file, fullPage: false })
  } catch (err) {
    console.log('screenshot failed', name, err.message)
  }
}

function base32ToBuffer(secret) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
  const clean = String(secret).replace(/[\s=]/g, '').toUpperCase()
  let bits = ''
  for (const ch of clean) {
    const val = alphabet.indexOf(ch)
    if (val < 0) continue
    bits += val.toString(2).padStart(5, '0')
  }
  const bytes = []
  for (let i = 0; i + 8 <= bits.length; i += 8) {
    bytes.push(parseInt(bits.slice(i, i + 8), 2))
  }
  return Buffer.from(bytes)
}

function totp(secret, now = Date.now()) {
  const key = base32ToBuffer(secret)
  const counter = BigInt(Math.floor(now / 1000 / 30))
  const buf = Buffer.alloc(8)
  buf.writeBigUInt64BE(counter)
  const hmac = crypto.createHmac('sha1', key).update(buf).digest()
  const offset = hmac[hmac.length - 1] & 0xf
  const bin =
    ((hmac[offset] & 0x7f) << 24) |
    ((hmac[offset + 1] & 0xff) << 16) |
    ((hmac[offset + 2] & 0xff) << 8) |
    (hmac[offset + 3] & 0xff)
  return String(bin % 1_000_000).padStart(6, '0')
}

async function dismissOverlays(page) {
  const labels = [
    /Skip tour/i,
    /Skip for now/i,
    /^Skip$/i,
    /Got it/i,
    /Not now/i,
    /Maybe later/i,
    /Continue to (app|dashboard)/i,
    /Go to Dashboard/i,
    /Close tour/i,
    /I'll do this later/i,
  ]
  for (const name of labels) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 400 }).catch(() => false)) {
      await btn.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(250)
    }
  }
  await page.keyboard.press('Escape').catch(() => {})
}

async function dump(page, name) {
  try {
    const text = await page.locator('body').innerText({ timeout: 8000 })
    writeFileSync(path.join(OUT, `${name}.txt`), text)
    return text
  } catch {
    return ''
  }
}

async function fillTotp(locator, secret) {
  await locator.fill(totp(secret))
}

async function main() {
  console.log(`headed=${HEADED} app=${APP}`)
  const browser = await chromium.launch({
    headless: !HEADED,
    executablePath: CHROME,
    args: [
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-extensions',
      '--no-first-run',
      '--no-default-browser-check',
    ],
  })
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    acceptDownloads: false,
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(20000)

  page.on('console', (msg) => {
    if (msg.type() === 'error' && consoleErrors.length < 30) {
      consoleErrors.push(msg.text().slice(0, 500))
    }
  })
  page.on('pageerror', (err) => {
    if (pageErrors.length < 20) pageErrors.push(String(err).slice(0, 500))
  })
  page.on('response', async (res) => {
    const url = res.url()
    const method = res.request().method()
    if (!url.includes('/api/v1/')) return
    const rec = { method, status: res.status(), url: url.replace(APP, '').slice(0, 180) }
    if (apiLog.length < 80) apiLog.push(rec)
    try {
      const ct = res.headers()['content-type'] || ''
      const json = ct.includes('json') ? await res.json().catch(() => null) : null
      if (url.includes('/users/login') && method === 'POST') lastLogin = { status: res.status(), json }
      else if (url.includes('/users/mfa/enroll') && method === 'POST') lastMfaEnroll = { status: res.status() }
      else if (url.includes('/users/mfa/verify') && method === 'POST') lastMfaVerify = { status: res.status() }
      else if (url.includes('/users/mfa/disable') && method === 'POST') lastMfaDisable = { status: res.status() }
      else if (url.includes('/users/logout') && method === 'POST') lastLogout = { status: res.status() }
    } catch {
      /* ignore */
    }
  })

  let totpSecret = ''

  // ── 1. Login (password only; account should have no verified TOTP) ──
  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.locator('#login-email').waitFor({ timeout: 20000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /^sign in$/i }).click()
    const mfaLogin = await page
      .getByLabel('Two-step verification form')
      .waitFor({ timeout: 8000 })
      .then(() => true)
      .catch(() => false)
    if (mfaLogin) {
      log('login', 'FAIL', 'Login asked for TOTP; clear factors before this harness')
    } else {
      await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 25000 })
      log(
        'login',
        /dashboard|transactions|platform|settings/i.test(page.url()) ? 'PASS' : 'FAIL',
        `login_status=${lastLogin?.status} url=${page.url()}`,
      )
    }
  } catch (err) {
    log('login', 'FAIL', err.message)
  }
  await dismissOverlays(page)
  await shot(page, 'after_login')

  // ── 2. Platform while unenrolled: Settings CTA, no QR ──
  try {
    await page.goto(`${APP}/platform/tenants`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await dismissOverlays(page)
    const gate = page.getByRole('heading', { name: /Platform console requires two-step verification/i })
    await gate.waitFor({ timeout: 20000 })
    const enrollOnPlatform = await page.getByText(/Scan with Google Authenticator/i).isVisible().catch(() => false)
    const settingsCta = await page.getByRole('link', { name: /open security settings/i }).isVisible().catch(() => false)
    if (enrollOnPlatform) log('platform-unenrolled-no-qr', 'FAIL', 'Platform still shows enrollment QR')
    else if (settingsCta) log('platform-unenrolled-no-qr', 'PASS', 'Unenrolled: sent to Settings')
    else log('platform-unenrolled-no-qr', 'FAIL', await dump(page, 'platform_unenrolled'))
  } catch (err) {
    log('platform-unenrolled-no-qr', 'FAIL', `${err.message} ${await dump(page, 'platform_unenrolled')}`)
  }
  await shot(page, 'platform_unenrolled')

  // ── 3. Enroll in Settings ──
  try {
    const settingsCta = page.getByRole('link', { name: /open security settings/i })
    if (await settingsCta.isVisible().catch(() => false)) await settingsCta.click()
    else await page.goto(`${APP}/settings/security`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.waitForURL(/\/settings\/security/, { timeout: 15000 })
    await page.getByRole('button', { name: /set up authenticator app/i }).click({ timeout: 15000 })
    await page.getByAltText(/QR code for authenticator app enrollment/i).waitFor({ timeout: 20000 })
    totpSecret = (await page.locator('code').first().innerText({ timeout: 8000 })).trim()
    log(
      'settings-enroll-qr',
      totpSecret.length >= 16 ? 'PASS' : 'FAIL',
      `secret_len=${totpSecret.length} enroll_status=${lastMfaEnroll?.status}`,
    )
    await fillTotp(page.locator('#settings-mfa-enroll-code'), totpSecret)
    await page.getByRole('button', { name: /activate two-step verification/i }).click()
    let on = await page.getByText(/authenticator app is on/i).waitFor({ timeout: 15000 }).then(() => true).catch(() => false)
    if (!on) {
      await fillTotp(page.locator('#settings-mfa-enroll-code'), totpSecret)
      await page.getByRole('button', { name: /activate two-step verification/i }).click()
      on = await page.getByText(/authenticator app is on/i).waitFor({ timeout: 15000 }).then(() => true).catch(() => false)
    }
    log('settings-enroll-activate', on ? 'PASS' : 'FAIL', `verify_status=${lastMfaVerify?.status}`)
  } catch (err) {
    log('settings-enroll-activate', 'FAIL', err.message)
  }
  await shot(page, 'settings_enrolled')
  await dump(page, 'settings_enrolled')

  // ── 4. Platform after enroll: console (aal2) or code-only, never QR ──
  try {
    await page.goto(`${APP}/platform/tenants`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await dismissOverlays(page)
    const qr = await page.getByText(/Scan with Google Authenticator/i).isVisible().catch(() => false)
    const setupCta = await page.getByRole('link', { name: /open security settings/i }).isVisible().catch(() => false)
    const codeOnly = await page.locator('#platform-mfa-code').isVisible().catch(() => false)
    const gated = await page
      .getByRole('heading', { name: /Platform console requires two-step verification/i })
      .isVisible()
      .catch(() => false)
    if (qr) log('platform-after-enroll', 'FAIL', 'QR still on platform after Settings enroll')
    else if (setupCta) log('platform-after-enroll', 'FAIL', 'Still setup-required after enroll')
    else if (codeOnly && gated) log('platform-after-enroll', 'PASS', 'Code-only gate (session still AAL1)')
    else if (!gated && /tenants/i.test(page.url())) log('platform-after-enroll', 'PASS', `console url=${page.url()}`)
    else log('platform-after-enroll', 'FAIL', await dump(page, 'platform_after_enroll'))
  } catch (err) {
    log('platform-after-enroll', 'FAIL', err.message)
  }
  await shot(page, 'platform_after_enroll')

  // ── 5. Disable: confirm dialog, then a fresh code even on aal2 ──
  try {
    await page.goto(`${APP}/settings/security`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.getByRole('button', { name: /turn off two-step verification/i }).click({ timeout: 15000 })
    const dialog = page.getByRole('alertdialog')
    await dialog.waitFor({ timeout: 8000 })
    log('disable-confirm-dialog', 'PASS', 'Confirmation alert shown')
    await page.getByRole('button', { name: /^turn off$/i }).click()
    const codeInput = page.locator('#settings-mfa-remove-code')
    await codeInput.waitFor({ timeout: 8000 })
    log('disable-requires-code', 'PASS', 'aal2 session still asked for a TOTP code')
    await fillTotp(codeInput, totpSecret)
    await page.getByRole('button', { name: /confirm and turn off/i }).click()
    const off = await page
      .getByRole('button', { name: /set up authenticator app/i })
      .waitFor({ timeout: 15000 })
      .then(() => true)
      .catch(() => false)
    if (!off) {
      await fillTotp(codeInput, totpSecret)
      await page.getByRole('button', { name: /confirm and turn off/i }).click()
    }
    const setupAgain = await page.getByRole('button', { name: /set up authenticator app/i }).isVisible().catch(() => false)
    log(
      'disable-with-code',
      setupAgain && lastMfaDisable?.status === 204 ? 'PASS' : setupAgain ? 'WARN' : 'FAIL',
      `disable_status=${lastMfaDisable?.status}`,
    )
  } catch (err) {
    log('disable-with-code', 'FAIL', err.message)
  }
  await shot(page, 'settings_after_disable')
  await dump(page, 'settings_after_disable')

  // ── 6. Platform after disable: leftover aal2 must not open the console ──
  try {
    await page.goto(`${APP}/platform/tenants`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await dismissOverlays(page)
    const settingsCta = await page
      .getByRole('link', { name: /open security settings/i })
      .waitFor({ timeout: 20000 })
      .then(() => true)
      .catch(() => false)
    const qr = await page.getByText(/Scan with Google Authenticator/i).isVisible().catch(() => false)
    const gated = await page
      .getByRole('heading', { name: /Platform console requires two-step verification/i })
      .isVisible()
      .catch(() => false)
    if (qr) log('platform-after-disable', 'FAIL', 'QR shown after MFA off')
    else if (settingsCta && gated) log('platform-after-disable', 'PASS', 'Stale aal2 blocked; sent to Settings')
    else log('platform-after-disable', 'FAIL', await dump(page, 'platform_after_disable'))
  } catch (err) {
    log('platform-after-disable', 'FAIL', err.message)
  }
  await shot(page, 'platform_after_disable')

  // ── 7. Logout ──
  try {
    await page.goto(`${APP}/dashboard/admin`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await dismissOverlays(page)
    const avatar = page.locator('button[data-tour="account-menu"]').first()
    await avatar.waitFor({ timeout: 15000 })
    await avatar.click()
    await page.getByRole('menuitem', { name: /log out/i }).click({ timeout: 8000 })
    await page.waitForTimeout(1500)
    log(
      'logout',
      lastLogout?.status === 204 || lastLogout?.status === 200 || /login/i.test(page.url()) ? 'PASS' : 'WARN',
      `logout_status=${lastLogout?.status} url=${page.url()}`,
    )
  } catch (err) {
    log('logout', 'FAIL', err.message)
  }
  await shot(page, 'after_logout')

  const realConsole = consoleErrors.filter(
    (e) => !/Download the React DevTools|favicon|third-party cookie/i.test(e),
  )
  if (realConsole.length) log('console-errors', 'WARN', realConsole.join(' | '))
  if (pageErrors.length) log('page-errors', 'FAIL', pageErrors.join(' | '))

  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, apiLog }, null, 2))
  const failed = findings.filter((f) => f.result === 'FAIL')
  console.log(`\n${findings.length} checks · ${failed.length} fail · artifacts ${OUT}`)
  await browser.close()
  process.exit(failed.length ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
