/**
 * Headless CASA shots for Settings enroll, platform setup/code, then
 * turn MFA back off so the admin account stays unlocked.
 *
 *   $env:QA_PASSWORD='…'; node casa_mfa_feature_shots.mjs
 */
import { createRequire } from 'module'
import crypto from 'crypto'
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
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '3.3.1')
mkdirSync(OUT, { recursive: true })

const TARGETS = [
  { id: 'stage', app: 'https://app.stage.velvetelves.com', api: 'https://api.stage.velvetelves.com' },
  { id: 'prod', app: 'https://app.velvetelves.com', api: 'https://api.prod.velvetelves.com' },
]

function totp(secret, now = Date.now()) {
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
  const key = Buffer.from(bytes)
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

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

async function waitNextWindow() {
  const remain = 30 - (Date.now() / 1000) % 30 + 1.5
  console.log(`waiting ${remain.toFixed(1)}s for a fresh TOTP window`)
  await sleep(remain * 1000)
}

async function apiLogin(api) {
  const body = new URLSearchParams({ username: EMAIL, password: PASSWORD })
  const resp = await fetch(`${api}/api/v1/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  const json = await resp.json()
  if (!resp.ok || !json.access_token) {
    throw new Error(`login ${resp.status} ${JSON.stringify(json)}`)
  }
  return json
}

async function apiFactors(api, token) {
  const resp = await fetch(`${api}/api/v1/users/mfa/factors`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const json = await resp.json()
  return json.factors || []
}

async function apiDisable(api, token, secret) {
  await waitNextWindow()
  const resp = await fetch(`${api}/api/v1/users/mfa/disable`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ code: totp(secret) }),
  })
  if (resp.status !== 204) {
    const text = await resp.text()
    throw new Error(`disable ${resp.status} ${text}`)
  }
}

async function apiDeleteFactor(api, token, factorId) {
  const resp = await fetch(`${api}/api/v1/users/mfa/factors/${factorId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (resp.status !== 204) {
    const text = await resp.text()
    throw new Error(`delete factor ${resp.status} ${text}`)
  }
}

async function restoreUnlocked(api, secret) {
  const session = await apiLogin(api)
  const factors = await apiFactors(api, session.access_token)
  const verified = factors.find((f) => f.factor_type === 'totp' && f.status === 'verified')
  if (verified) {
    if (!secret) {
      throw new Error('verified TOTP is still on and we have no setup key to turn it off')
    }
    await apiDisable(api, session.access_token, secret)
  }
  const after = verified ? await apiLogin(api) : session
  const leftover = await apiFactors(api, after.access_token)
  for (const f of leftover.filter((x) => x.factor_type === 'totp' && x.status !== 'verified')) {
    await apiDeleteFactor(api, after.access_token, f.id)
  }
  const check = await apiLogin(api)
  const remaining = await apiFactors(api, check.access_token)
  console.log(
    `[PASS] ${api} restored mfa_required=${check.mfa_required} factors=${remaining.length}`,
  )
  if (check.mfa_required || remaining.length) {
    throw new Error('account is still not MFA-off after cleanup')
  }
}

async function shot(page, name) {
  const file = path.join(OUT, name)
  await page.screenshot({ path: file, fullPage: false })
  console.log('wrote', file)
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
  ]
  for (const name of labels) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 400 }).catch(() => false)) {
      await btn.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(200)
    }
  }
  await page.keyboard.press('Escape').catch(() => {})
}

async function capture({ id, app, api }) {
  console.log(`--- ${id} ---`)
  const browser = await chromium.launch({
    executablePath: CHROME,
    headless: true,
    args: [
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--disable-extensions',
      '--no-first-run',
      '--no-default-browser-check',
    ],
  })
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
  let secret = null
  try {
    const before = await apiLogin(api)
    const beforeFactors = await apiFactors(api, before.access_token)
    console.log(
      `${id} start mfa_required=${before.mfa_required} factors=${beforeFactors.length}`,
    )
    if (before.mfa_required) {
      throw new Error(`${id} still has verified MFA; refusing to enroll a second factor`)
    }

    await page.goto(`${app}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.getByLabel(/email address/i).waitFor({ timeout: 20000 })
    await shot(page, `CASA_3_3_1_${id}_login.png`)
    await page.getByLabel(/email address/i).fill(EMAIL)
    await page.getByLabel(/^password$/i).fill(PASSWORD)
    await page.getByRole('button', { name: /^sign in$/i }).click()

    await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 30000 })
    await page.waitForTimeout(800)
    await dismissOverlays(page)
    await dismissOverlays(page)

    await page.goto(`${app}/platform/users`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.getByRole('heading', { name: /platform console requires two-step/i }).waitFor({
      timeout: 20000,
    })
    await page.getByRole('link', { name: /open security settings/i }).waitFor({ timeout: 5000 })
    await shot(page, `CASA_3_3_1_${id}_platform_setup.png`)

    await page.goto(`${app}/settings/security`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await dismissOverlays(page)
    const setupBtn = page.getByRole('button', { name: /set up authenticator app/i })
    await setupBtn.waitFor({ timeout: 20000 })
    await shot(page, `CASA_3_3_1_${id}_security_off.png`)
    await setupBtn.click()
    await page.getByRole('img', { name: /QR code for authenticator/i }).waitFor({ timeout: 20000 })
    secret = (await page.locator('code').first().innerText()).trim()
    await shot(page, `CASA_3_3_1_${id}_security_enroll.png`)
    await page.getByLabel(/code from your app/i).fill(totp(secret))
    await page.getByRole('button', { name: /activate two-step verification/i }).click()
    await page.getByText(/authenticator app is on/i).waitFor({ timeout: 20000 })
    await shot(page, `CASA_3_3_1_${id}_security_on.png`)

    await page.goto(`${app}/platform/users`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.getByRole('heading', { name: 'Users', exact: true }).waitFor({ timeout: 25000 })
    await shot(page, `CASA_3_3_1_${id}_platform_unlocked.png`)

    const aal1 = await apiLogin(api)
    await page.evaluate((token) => {
      localStorage.setItem('velvet_elves_token', token)
      localStorage.removeItem('velvet_elves_refresh_token')
    }, aal1.access_token)
    await page.goto(`${app}/platform/users`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.getByRole('heading', { name: /platform console requires two-step/i }).waitFor({
      timeout: 20000,
    })
    await page.getByLabel(/verification code/i).waitFor({ timeout: 5000 })
    await shot(page, `CASA_3_3_1_${id}_platform_code.png`)
  } catch (err) {
    await shot(page, `CASA_3_3_1_${id}_FAIL.png`).catch(() => {})
    console.error(`[FAIL] ${id} url=${page.url()}`)
    throw err
  } finally {
    try {
      await restoreUnlocked(api, secret)
    } catch (cleanupErr) {
      console.error(`[CRITICAL] ${id} could not turn MFA back off:`, cleanupErr)
    }
    await browser.close()
  }
}

for (const t of TARGETS) {
  await capture(t)
}
