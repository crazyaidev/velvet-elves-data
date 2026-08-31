/**
 * Staging AddDocumentModal allowlist (CASA 5.2.1). Opens Compliance, screenshots
 * accepted formats. Does not upload a file.
 *
 *   $env:QA_PASSWORD='…'; node casa_521_picker.mjs
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
const API = 'https://api.stage.velvetelves.com'
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '5.2.1')
mkdirSync(OUT, { recursive: true })
const FORMATS = 'PDF, DOC/DOCX, JPEG, PNG, WEBP, GIF, TXT'

async function api(method, urlPath, token) {
  const resp = await fetch(`${API}${urlPath}`, {
    method,
    headers: { Accept: 'application/json', Authorization: `Bearer ${token}` },
  })
  const text = await resp.text()
  let json = null
  try {
    json = text ? JSON.parse(text) : null
  } catch {
    json = null
  }
  return { status: resp.status, json }
}

const loginResp = await fetch(`${API}/api/v1/users/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded', Accept: 'application/json' },
  body: new URLSearchParams({ username: EMAIL, password: PASSWORD }),
})
const loginJson = await loginResp.json()
const token = loginJson.access_token
const refresh = loginJson.refresh_token
if (!loginResp.ok || typeof token !== 'string') {
  console.error('login failed', loginResp.status, loginJson.mfa_required ? 'mfa_required' : '')
  process.exit(1)
}

const listed = await api('GET', '/api/v1/transactions?page=1&page_size=5', token)
const items = listed.json?.items || listed.json?.data || []
const dealId = items[0]?.id
if (!dealId) {
  console.error('no staging transaction for picker shot', listed.status)
  await fetch(`${API}/api/v1/users/logout`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } }).catch(
    () => {},
  )
  process.exit(1)
}

const dealUrl = `${APP}/transactions/${dealId}?tab=compliance`
const browser = await chromium.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--disable-gpu', '--disable-dev-shm-usage', '--no-first-run'],
})
const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, ignoreHTTPSErrors: true })

try {
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.evaluate(
    ({ t, r }) => {
      localStorage.setItem('velvet_elves_token', t)
      if (r) localStorage.setItem('velvet_elves_refresh_token', r)
    },
    { t: token, r: typeof refresh === 'string' ? refresh : null },
  )
  await page.goto(dealUrl, { waitUntil: 'domcontentloaded', timeout: 45000 })
  if (page.url().includes('/login')) {
    throw new Error(`redirected to login: ${page.url()}`)
  }
  const addBtn = page.getByRole('button', { name: /Add (a )?document/i }).first()
  await addBtn.waitFor({ timeout: 25000 })
  await addBtn.click()
  await page.getByText(FORMATS, { exact: false }).waitFor({ timeout: 15000 })
  const dialog = page.getByRole('dialog')
  await dialog.waitFor({ timeout: 10000 })
  const raw = path.join(OUT, 'CASA_5_2_1_picker_raw.png')
  await dialog.screenshot({ path: raw })
  writeFileSync(path.join(OUT, '_picker_url.txt'), dealUrl)
  console.log('wrote', raw, 'url', dealUrl)
} finally {
  await browser.close()
  await fetch(`${API}/api/v1/users/logout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  }).catch(() => {})
}
