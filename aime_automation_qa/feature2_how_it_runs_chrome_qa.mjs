/**
 * Local Chrome check for Feature 2 How it runs copy (Audri).
 * Headless Google Chrome, one page, one viewport shot, low RAM.
 *
 *   QA_APP=http://127.0.0.1:5173 QA_EMAIL=... QA_PASSWORD=... node feature2_how_it_runs_chrome_qa.mjs
 *   QA_TOTP_SECRET=...  if login asks for an authenticator code
 */
import { createRequire } from 'module'
import crypto from 'crypto'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_feature2_local')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL
const PASSWORD = process.env.QA_PASSWORD
const TOTP_SECRET = process.env.QA_TOTP_SECRET || ''
const APP = (process.env.QA_APP || 'http://127.0.0.1:5173').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
if (!EMAIL || !PASSWORD) {
  console.error('Set QA_EMAIL and QA_PASSWORD')
  process.exit(2)
}

const findings = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 500) : ''}`)
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
  for (const name of [/Skip tour/i, /Skip for now/i, /^Skip$/i, /Not now/i, /Got it/i, /Maybe later/i]) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 400 }).catch(() => false)) {
      await btn.click({ timeout: 1500 }).catch(() => {})
    }
  }
}

async function run() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME,
    args: [
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--disable-extensions',
      '--mute-audio',
      '--no-first-run',
      '--no-default-browser-check',
      '--renderer-process-limit=1',
    ],
  })
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(15000)

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.locator('#login-email').waitFor({ state: 'visible', timeout: 20000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()

    const mfaForm = page.getByLabel('Two-step verification form')
    const askedMfa = await mfaForm.waitFor({ timeout: 8000 }).then(() => true).catch(() => false)
    if (askedMfa) {
      if (!TOTP_SECRET) {
        log('login', 'FAIL', 'MFA form — set QA_TOTP_SECRET to continue')
        await page.screenshot({ path: path.join(OUT, 'mfa_block.png'), fullPage: false }).catch(() => {})
        return
      }
      await page.locator('#mfa-code').fill(totp(TOTP_SECRET))
      await page.getByRole('button', { name: /verify code/i }).click()
    }

    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 30000 }).catch(() => {})
    await dismissOverlays(page)

    if (page.url().includes('/login')) {
      const alert = await page.locator('[role="alert"]').innerText().catch(() => '')
      log('login', 'FAIL', alert || page.url())
      return
    }
    log('login', 'PASS', page.url())

    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.getByRole('heading', { name: /AI & Automation/i }).waitFor({ timeout: 20000 })
    await dismissOverlays(page)
    await page.getByText('Inspection deadline reminder', { exact: true }).waitFor({ timeout: 20000 })

    const overnight = page.getByText('Inspection deadline reminder', { exact: true }).first()
    await overnight.scrollIntoViewIfNeeded().catch(() => {})
    await page.screenshot({ path: path.join(OUT, 'how_it_runs.png'), fullPage: false })

    const text = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'how_it_runs.txt'), `${page.url()}\n\n${text}`)

    const must = [
      'Named emails are drafted — you tap Send.',
      'Authorized emails send when confidence is high enough. No tap.',
      'Welcome / title emails',
      'Named emails',
      'Inspection deadline reminder',
      'Named welcome, title-order, and inspection-deadline emails may send on Autopilot',
    ]
    for (const needle of must) {
      log(`copy.has:${needle.slice(0, 52)}`, text.includes(needle) ? 'PASS' : 'FAIL', needle)
    }

    const mustNot = [
      'Named letters are drafted',
      'Authorized letters send',
      'Welcome / title letters',
      'Inspection reminders',
    ]
    for (const needle of mustNot) {
      log(`copy.gone:${needle}`, text.includes(needle) ? 'FAIL' : 'PASS', needle)
    }

    const inspectionHelp =
      text.includes('Only the inspection-response deadline reminder, to you') ||
      text.includes('That deadline reminder will not send until you turn this on')
    log('copy.inspection-help', inspectionHelp ? 'PASS' : 'FAIL')

    await page.goto(`${APP}/admin/confidence?section=email`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    })
    await page.getByRole('heading', { name: /AI email replies/i }).waitFor({ timeout: 20000 })
    await page
      .getByText('Named emails on Autopilot may send without a tap', { exact: false })
      .waitFor({ timeout: 15000 })
      .catch(() => {})
    const emailText = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'email_replies.txt'), `${page.url()}\n\n${emailText}`)
    await page.screenshot({ path: path.join(OUT, 'email_replies.png'), fullPage: false })
    log(
      'copy.email-replies-named',
      emailText.includes('Named emails on Autopilot may send without a tap') ? 'PASS' : 'FAIL',
    )
    log(
      'copy.email-replies-no-letters',
      /named letters/i.test(emailText) ? 'FAIL' : 'PASS',
    )
  } finally {
    await context.close().catch(() => {})
    await browser.close().catch(() => {})
    const failed = findings.filter((f) => f.result === 'FAIL').length
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    console.log(failed ? `FAILED ${failed}` : 'ALL PASS')
    process.exit(failed ? 1 : 0)
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
