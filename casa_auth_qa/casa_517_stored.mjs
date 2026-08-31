/**
 * Staging stored-XSS UI evidence (CASA 5.1.7). Creates a contact, screenshots
 * the name as text, then deletes it. Not an exploit.
 *
 *   $env:QA_PASSWORD='…'; node casa_517_stored.mjs
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
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '5.1.7')
mkdirSync(OUT, { recursive: true })

const MARKER = 'CASA517'
const STORED = `${MARKER} <script>alert(1)</script>`

async function api(method, urlPath, token, body) {
  const headers = { Accept: 'application/json', Authorization: `Bearer ${token}` }
  const opts = { method, headers }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  const resp = await fetch(`${API}${urlPath}`, opts)
  const text = await resp.text()
  let json = null
  try {
    json = text ? JSON.parse(text) : null
  } catch {
    json = null
  }
  return { status: resp.status, json, text }
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

let contactId = null
const meta = {
  url: '',
  dialog: false,
  text_visible: false,
  script_elements: 0,
  deleted: false,
}

try {
  const created = await api('POST', '/api/v1/contacts/', token, {
    contact_type: 'other',
    full_name: STORED,
    company: MARKER,
    notes: 'CASA 5.1.7 stored-text check; delete after shot',
  })
  if (created.status !== 201 || !created.json?.id) {
    console.error('create contact failed', created.status, created.text.slice(0, 200))
    process.exit(1)
  }
  contactId = created.json.id

  const browser = await chromium.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--disable-gpu', '--disable-dev-shm-usage', '--no-first-run'],
  })
  const page = await browser.newPage({
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  })
  page.on('dialog', async (d) => {
    meta.dialog = true
    await d.dismiss()
  })

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.evaluate(
      ({ t, r }) => {
        localStorage.setItem('velvet_elves_token', t)
        if (r) localStorage.setItem('velvet_elves_refresh_token', r)
      },
      { t: token, r: typeof refresh === 'string' ? refresh : null },
    )
    await page.goto(`${APP}/contacts?focus=${contactId}`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    })
    if (page.url().includes('/login')) {
      throw new Error(`redirected to login: ${page.url()}`)
    }
    await page.getByLabel('Search contacts').waitFor({ timeout: 25000 })
    await page.getByLabel('Search contacts').fill(MARKER)
    await page.getByRole('button', { name: new RegExp(MARKER) }).first().waitFor({ timeout: 20000 })
    const row = page.locator(`tr[data-contact-id="${contactId}"]`)
    if (await row.count()) {
      await row.click()
    } else {
      await page.getByRole('button', { name: new RegExp(MARKER) }).first().click()
    }
    await page.getByRole('heading', { name: new RegExp(MARKER) }).waitFor({ timeout: 15000 })
    await page.waitForTimeout(600)
    meta.url = page.url()
    meta.text_visible = (await page.getByText(MARKER, { exact: false }).count()) > 0
    meta.script_elements = await page.evaluate(() =>
      [...document.querySelectorAll('script')].filter((s) => (s.textContent || '').includes('alert(1)'))
        .length,
    )
    const raw = path.join(OUT, 'CASA_5_1_7_stored_raw.png')
    await page.screenshot({ path: raw, fullPage: false })
    console.log('wrote', raw, 'url', meta.url)
  } finally {
    await browser.close()
  }
} finally {
  if (contactId) {
    const del = await api('DELETE', `/api/v1/contacts/${contactId}`, token)
    meta.deleted = del.status === 204 || del.status === 200
    console.log('delete', del.status, meta.deleted)
  }
  await fetch(`${API}/api/v1/users/logout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  }).catch(() => {})
}

writeFileSync(path.join(OUT, '_stored_meta.json'), JSON.stringify(meta, null, 2))
if (meta.dialog || meta.script_elements > 0 || !meta.text_visible || !meta.deleted) {
  console.error('stored XSS check failed', meta)
  process.exit(1)
}
console.log('ok', meta)
