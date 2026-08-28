/**
 * Local Chrome QA for CASA auth updates + AI Wizard PDF extraction.
 *
 *   node casa_auth_chrome_qa.mjs
 *
 * Env:
 *   QA_HEADED=1   headed Google Chrome (default 1 for this pass)
 *   QA_SHOTS=1    write PNGs
 */
import { createRequire } from 'module'
import crypto from 'crypto'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const PASS = process.env.QA_PASS || 'chrome1'
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
const PDF = process.env.QA_PDF || path.join(__dirname, '../demo_video_testing/willowbrook_purchase_agreement.pdf')
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
let lastLogout = null
let lastPacketPost = null
let lastPacketStatus = null

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

async function main() {
  console.log(`headed=${HEADED} app=${APP} pdf=${PDF}`)
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
      else if (url.includes('/users/mfa/enroll') && method === 'POST') lastMfaEnroll = { status: res.status(), json }
      else if (url.includes('/users/mfa/verify') && method === 'POST') lastMfaVerify = { status: res.status(), json }
      else if (url.includes('/users/logout') && method === 'POST') lastLogout = { status: res.status() }
      else if (url.includes('/parse-document-packet') && method === 'POST') lastPacketPost = { status: res.status(), json }
      else if (url.includes('/parse-document-packet/') && url.includes('/status')) {
        lastPacketStatus = { status: res.status(), json }
      }
    } catch {
      /* ignore */
    }
  })

  // ── 1. Login ────────────────────────────────────────────────────────────
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
      log('login-mfa-step', 'WARN', 'Account already has TOTP; login asked for a code')
    } else {
      await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 25000 })
      log(
        'login',
        /dashboard|transactions|platform/i.test(page.url()) ? 'PASS' : 'FAIL',
        `login_status=${lastLogin?.status} url=${page.url()}`,
      )
    }
  } catch (err) {
    log('login', 'FAIL', err.message)
  }
  await dismissOverlays(page)
  await shot(page, 'after_login')

  let totpSecret = ''

  // ── 2. Standard MFA: enroll in Settings; platform is code-only ──────────
  try {
    await page.goto(`${APP}/platform/tenants`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await dismissOverlays(page)
    const gate = page.getByRole('heading', { name: /Platform console requires two-step verification/i })
    const gateVisible = await gate.waitFor({ timeout: 20000 }).then(() => true).catch(() => false)
    const enrollOnPlatform = await page.getByText(/Scan with Google Authenticator/i).isVisible().catch(() => false)
    if (enrollOnPlatform) {
      log('platform-mfa-no-enroll', 'FAIL', 'Platform still shows authenticator enrollment UI')
    } else if (gateVisible) {
      const settingsCta = await page.getByRole('link', { name: /open security settings/i }).isVisible().catch(() => false)
      const codeOnly = await page.locator('#platform-mfa-code').isVisible().catch(() => false)
      if (settingsCta) log('platform-mfa-gate', 'PASS', 'Unenrolled: platform sent admin to Settings')
      else if (codeOnly) log('platform-mfa-gate', 'PASS', 'Enrolled: platform asked for a code only')
      else log('platform-mfa-gate', 'FAIL', 'Gate with neither Settings CTA nor code field')
    } else {
      log('platform-mfa-gate', 'WARN', `No gate — session may already be AAL2 url=${page.url()}`)
    }
  } catch (err) {
    const body = await dump(page, 'platform_gate_miss')
    log('platform-mfa-gate', 'FAIL', `${err.message} url=${page.url()} body=${body.slice(0, 400)}`)
  }
  await shot(page, 'mfa_gate')

  try {
    const settingsCta = page.getByRole('link', { name: /open security settings/i })
    if (await settingsCta.isVisible().catch(() => false)) {
      await settingsCta.click()
    } else {
      await page.goto(`${APP}/settings/security`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    }
    await page.waitForURL(/\/settings\/security/, { timeout: 15000 })
    const setupBtn = page.getByRole('button', { name: /set up authenticator app/i })
    const alreadyOn = await page.getByText(/authenticator app is on/i).isVisible().catch(() => false)
    if (await setupBtn.waitFor({ timeout: 15000 }).then(() => true).catch(() => false)) {
      await setupBtn.click()
      await page.getByAltText(/QR code for authenticator app enrollment/i).waitFor({ timeout: 20000 })
      const secret = (await page.locator('code').first().innerText({ timeout: 8000 })).trim()
      totpSecret = secret
      log(
        'mfa-enroll-secret',
        secret.length >= 16 ? 'PASS' : 'FAIL',
        `secret_len=${secret.length} enroll_status=${lastMfaEnroll?.status}`,
      )
      await page.locator('#settings-mfa-enroll-code').fill(totp(secret))
      await page.getByRole('button', { name: /activate two-step verification/i }).click()
      let on = await page.getByText(/authenticator app is on/i).waitFor({ timeout: 15000 }).then(() => true).catch(() => false)
      if (!on) {
        await page.locator('#settings-mfa-enroll-code').fill(totp(secret, Date.now() + 30000))
        await page.getByRole('button', { name: /activate two-step verification/i }).click()
        on = await page.getByText(/authenticator app is on/i).waitFor({ timeout: 15000 }).then(() => true).catch(() => false)
      }
      log('mfa-enroll-verify', on ? 'PASS' : 'FAIL', `verify_status=${lastMfaVerify?.status}`)
    } else if (alreadyOn) {
      log('mfa-enroll-secret', 'WARN', 'Settings already shows authenticator on')
    } else {
      log('mfa-enroll-secret', 'FAIL', `Unexpected Security page url=${page.url()}`)
    }
  } catch (err) {
    log('mfa-enroll-verify', 'FAIL', err.message)
  }

  try {
    await page.goto(`${APP}/platform/tenants`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await dismissOverlays(page)
    const stillEnroll = await page.getByText(/Scan with Google Authenticator/i).isVisible().catch(() => false)
    if (stillEnroll) {
      log('platform-after-settings', 'FAIL', 'Platform still showing enrollment QR')
    } else {
      const gated = await page
        .getByRole('heading', { name: /Platform console requires two-step verification/i })
        .isVisible()
        .catch(() => false)
      if (gated) {
        const codeVisible = await page.locator('#platform-mfa-code').isVisible().catch(() => false)
        log('platform-after-settings', codeVisible ? 'PASS' : 'FAIL', 'Gate is verify-only after Settings enroll')
      } else {
        log('platform-after-settings', /tenants/i.test(page.url()) ? 'PASS' : 'WARN', `console url=${page.url()}`)
      }
    }
  } catch (err) {
    log('platform-after-settings', 'FAIL', err.message)
  }
  await shot(page, 'after_mfa')
  await dump(page, 'after_mfa')

  // ── 3. AI Wizard PDF extraction ─────────────────────────────────────────
  try {
    await page.goto(`${APP}/transactions/new`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.waitForTimeout(800)
    await dismissOverlays(page)
    await page.getByRole('radiogroup', { name: /representing/i }).waitFor({ timeout: 20000 })
    await page.getByRole('radiogroup', { name: /representing/i }).getByText('Buyer', { exact: true }).click()
    log('wizard-rep', 'PASS', 'Picked Buyer')
  } catch (err) {
    log('wizard-rep', 'FAIL', `${err.message} url=${page.url()}`)
  }
  await shot(page, 'wizard_upload')

  try {
    const input = page.locator('input[aria-label="Upload documents"]')
    await input.setInputFiles(PDF)
    await page.getByText(/willowbrook_purchase_agreement\.pdf/i).waitFor({ timeout: 30000 })
    log('wizard-upload', 'PASS', 'PDF listed after upload')
  } catch (err) {
    log('wizard-upload', 'FAIL', err.message)
  }
  await shot(page, 'wizard_file_listed')

  try {
    const start = page.getByRole('button', { name: /Start AI extraction/i })
    await start.waitFor({ timeout: 45000 })
    await start.click()
    log('wizard-start-extract', lastPacketPost?.status === 200 || lastPacketPost?.status === 202 ? 'PASS' : 'WARN', `packet_post=${lastPacketPost?.status}`)
  } catch (err) {
    log('wizard-start-extract', 'FAIL', err.message)
  }
  await shot(page, 'wizard_extracting')

  try {
    const deadline = Date.now() + 180000
    let done = false
    while (Date.now() < deadline) {
      const st = lastPacketStatus?.json?.status || lastPacketStatus?.json?.job_status
      const body = await page.locator('body').innerText().catch(() => '')
      const advanced =
        /Contacts & Fees|Contract Details|Street address|Purchase price/i.test(body) &&
        !/Reading your documents/i.test(body)
      if (st === 'completed' || st === 'succeeded' || st === 'done' || advanced) {
        done = true
        break
      }
      if (st === 'failed' || st === 'error') break
      await page.waitForTimeout(2000)
    }
    const st = lastPacketStatus?.json
    const body = await dump(page, 'wizard_after_extract')
    const hasAddress = /Street address|Property address|Willowbrook|Purchase price|\$/.test(body)
    const failed = (st && /fail|error/i.test(String(st.status || st.job_status || ''))) || /could not read|extraction failed|unavailable/i.test(body)
    log(
      'wizard-extract-complete',
      done && !failed ? 'PASS' : 'FAIL',
      `done=${done} packet=${JSON.stringify(st)?.slice(0, 500)} hasAddressLike=${hasAddress} url=${page.url()}`,
    )
  } catch (err) {
    log('wizard-extract-complete', 'FAIL', err.message)
  }
  await shot(page, 'wizard_result')

  // ── 4. Logout revocation (wizard has no AppLayout, so leave it first) ──
  try {
    const exitBtn = page.getByRole('button', { name: /Exit to transactions|^Exit$/i }).first()
    if (await exitBtn.isVisible().catch(() => false)) {
      await exitBtn.click()
      await page.waitForTimeout(800)
    }
    // Keep the test account password-only so the next login is not locked
    // behind a discarded TOTP. Disable requires a fresh authenticator code.
    await page.goto(`${APP}/settings/security`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    const turnOff = page.getByRole('button', { name: /turn off two-step verification/i })
    if (await turnOff.isVisible({ timeout: 8000 }).catch(() => false)) {
      await turnOff.click()
      const confirmOff = page.getByRole('button', { name: /^turn off$/i })
      if (await confirmOff.isVisible({ timeout: 4000 }).catch(() => false)) {
        await confirmOff.click()
      }
      const codeInput = page.locator('#settings-mfa-remove-code')
      if (await codeInput.isVisible({ timeout: 8000 }).catch(() => false) && totpSecret) {
        await codeInput.fill(totp(totpSecret))
        await page.getByRole('button', { name: /confirm and turn off/i }).click()
        await page.waitForTimeout(1500)
      }
      log('mfa-unenroll-cleanup', totpSecret ? 'PASS' : 'WARN', 'Removed test authenticator from Settings')
    }
    await page.goto(`${APP}/dashboard/admin`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await dismissOverlays(page)
    const avatar = page.locator('button[data-tour="account-menu"]').first()
    await avatar.waitFor({ timeout: 15000 })
    await avatar.click()
    await page.getByRole('menuitem', { name: /log out/i }).click({ timeout: 8000 })
    await page.waitForTimeout(1500)
    log(
      'logout',
      lastLogout?.status === 204 || lastLogout?.status === 200 ? 'PASS' : 'WARN',
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

  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, apiLog, lastPacketStatus }, null, 2))
  const failed = findings.filter((f) => f.result === 'FAIL')
  console.log(`\n${findings.length} checks · ${failed.length} fail · artifacts ${OUT}`)
  await browser.close()
  process.exit(failed.length ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
