/**
 * Local Chrome QA: All Documents hides wizard leftovers (unassigned intake).
 * One headless Chrome, small viewport. Does not Send mail.
 *
 *   $env:QA_APP='http://127.0.0.1:5173'
 *   $env:QA_API='http://127.0.0.1:8000'
 *   node all_docs_orphan_local_chrome.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, rmSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { writePaPdf } from './jake_tme_pdf_fixtures.mjs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_all_docs_orphan_local')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'shyna.elene@minafter.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const APP = (process.env.QA_APP || 'http://127.0.0.1:5173').replace(/\/$/, '')
const API = (process.env.QA_API || 'http://127.0.0.1:8000').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const MARKER = `OrphanIntakeLocalQA-${Date.now()}.pdf`

const findings = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 2000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 500) : ''}`)
}

async function dismissOverlays(page) {
  for (const name of [/Skip tour/i, /Skip for now/i, /^Skip$/i, /Not now/i, /Got it/i]) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 350 }).catch(() => false)) {
      await btn.click({ timeout: 1200 }).catch(() => {})
    }
  }
}

async function bodyText(page) {
  try {
    return await page.locator('body').innerText({ timeout: 8000 })
  } catch {
    return ''
  }
}

async function dump(page, name) {
  const text = await bodyText(page)
  writeFileSync(path.join(OUT, `${name}.txt`), `${page.url()}\n\n${text}`)
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false }).catch(() => {})
  return text
}

async function countUnassignedRows(page) {
  return page.locator('span.italic', { hasText: /^Unassigned$/ }).count()
}

async function openAllDocs(page) {
  await page.goto(`${APP}/documents`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await dismissOverlays(page)
  const allTab = page.getByRole('button', { name: /All docs/i }).first()
  await allTab.waitFor({ timeout: 25000 })
  await allTab.click()
  await page
    .locator('[data-doc-id]')
    .or(page.getByRole('heading', { name: 'No documents in this view' }))
    .first()
    .waitFor({ timeout: 25000 })
  return dump(page, 'all_docs')
}

async function ensureWizardUploadStep(page) {
  const discard = page.getByRole('button', { name: /^Discard$/i }).first()
  if (await discard.isVisible({ timeout: 8000 }).catch(() => false)) {
    await discard.click()
    await page.waitForTimeout(500)
  }
  const heading = page.getByRole('heading', { name: /Upload Documents/i })
  if (!(await heading.isVisible({ timeout: 2500 }).catch(() => false))) {
    const stepBtn = page.getByRole('button', { name: /Upload Documents/i }).first()
    if (await stepBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await stepBtn.click()
    }
  }
  await heading.waitFor({ timeout: 15000 })
}

async function apiLogin() {
  const body = new URLSearchParams({ username: EMAIL, password: PASSWORD })
  const res = await fetch(`${API}/api/v1/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  const json = await res.json().catch(() => ({}))
  return { status: res.status, json }
}

async function apiJson(token, pathAndQuery, { method = 'GET', json } = {}) {
  const res = await fetch(`${API}${pathAndQuery}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(json ? { 'Content-Type': 'application/json' } : {}),
    },
    body: json ? JSON.stringify(json) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  return { status: res.status, data }
}

async function listUnassigned(token) {
  const { status, data } = await apiJson(token, '/api/v1/documents?page=1&page_size=100')
  const items = data.items || []
  return {
    status,
    total: data.total,
    unassigned: items.filter((d) => !d.transaction_id),
    names: items.map((d) => d.file_name || d.original_name),
  }
}

async function run() {
  const session = await apiLogin()
  if (session.status !== 200 || !session.json.access_token) {
    log('login.api', 'FAIL', `status=${session.status}`)
    process.exit(1)
  }
  log('login.api', 'PASS', EMAIL)
  const token = session.json.access_token

  const before = await listUnassigned(token)
  log(
    'api.list_hides_unassigned',
    before.status === 200 && before.unassigned.length === 0 ? 'PASS' : 'FAIL',
    `http=${before.status} total=${before.total} unassigned=${before.unassigned.length}`,
  )

  const pdfPath = path.join(OUT, MARKER)
  writePaPdf(pdfPath, {
    address: 'Orphan Intake Local QA',
    accept: 'September 1, 2026',
    close: 'October 15, 2026',
  })

  const profile = path.join(OUT, `chrome-${Date.now()}`)
  mkdirSync(profile, { recursive: true })
  const context = await chromium.launchPersistentContext(profile, {
    headless: true,
    executablePath: CHROME,
    viewport: { width: 1100, height: 700 },
    deviceScaleFactor: 1,
    args: [
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--mute-audio',
      '--no-first-run',
      '--disable-extensions',
      '--renderer-process-limit=1',
      '--js-flags=--max-old-space-size=192',
    ],
  })
  await context.addInitScript(
    ({ token: t, refresh }) => {
      window.localStorage.setItem('velvet_elves_token', t)
      if (refresh) window.localStorage.setItem('velvet_elves_refresh_token', refresh)
      window.localStorage.setItem('ve_agent_workspace_v1', 'on')
    },
    { token, refresh: session.json.refresh_token || '' },
  )
  const page = context.pages()[0] || (await context.newPage())
  page.setDefaultTimeout(20000)

  try {
    await openAllDocs(page)
    const unassignedBefore = await countUnassignedRows(page)
    log(
      'ui.all_docs_no_unassigned',
      unassignedBefore === 0 ? 'PASS' : 'FAIL',
      `unassigned_rows=${unassignedBefore}`,
    )

    await page.goto(`${APP}/transactions/new`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await dismissOverlays(page)
    try {
      await ensureWizardUploadStep(page)
    } catch (err) {
      log('ui.wizard_upload_step', 'FAIL', err.message || String(err))
      await dump(page, 'wizard_missing_upload_step')
      throw err
    }
    const buyerRadio = page.getByRole('radio', { name: /^Buyer$/i }).first()
    await buyerRadio.waitFor({ state: 'attached', timeout: 15000 })
    await buyerRadio.check({ force: true })
    await page.waitForTimeout(400)
    const fileInput = page.locator('input[aria-label="Upload documents"]')
    const inputReady = await fileInput.waitFor({ state: 'attached', timeout: 15000 }).then(() => true).catch(() => false)
    if (!inputReady) {
      log('ui.wizard_upload_input', 'FAIL', page.url())
      await dump(page, 'wizard_missing_input')
    } else {
      log('ui.wizard_upload_input', 'PASS')
      const uploadWait = page.waitForResponse(
        (r) => r.url().includes('/api/v1/documents/upload') && r.request().method() === 'POST',
        { timeout: 40000 },
      )
      await fileInput.setInputFiles(pdfPath)
      const uploadRes = await uploadWait.catch(() => null)
      log(
        'ui.wizard_upload',
        uploadRes && uploadRes.ok() ? 'PASS' : 'FAIL',
        uploadRes ? `http ${uploadRes.status()}` : 'no POST',
      )
      await page.waitForTimeout(800)
      await dump(page, 'wizard_after_upload')
    }

    const afterUpload = await listUnassigned(token)
    const leaked = afterUpload.names.some((n) => String(n).includes('OrphanIntakeLocalQA'))
    log(
      'api.after_wizard_upload_hidden',
      afterUpload.unassigned.length === 0 && !leaked ? 'PASS' : 'FAIL',
      `unassigned=${afterUpload.unassigned.length} leaked_name=${leaked}`,
    )

    const docsAfter = await openAllDocs(page)
    const leakedUi = /OrphanIntakeLocalQA/i.test(docsAfter)
    const unassignedAfter = await countUnassignedRows(page)
    log(
      'ui.after_wizard_upload_hidden',
      !leakedUi && unassignedAfter === 0 ? 'PASS' : 'FAIL',
      `leaked_name=${leakedUi} unassigned_rows=${unassignedAfter}`,
    )

    const discard = await fetch(`${API}/api/v1/wizard-runs/current`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    log('api.discard_draft', discard.status === 204 || discard.status === 200 ? 'PASS' : 'FAIL', `http ${discard.status}`)
  } catch (err) {
    log('chrome.uncaught', 'FAIL', err.message || String(err))
    await dump(page, 'uncaught').catch(() => {})
  } finally {
    await context.close().catch(() => {})
    try {
      rmSync(profile, { recursive: true, force: true })
    } catch {
      /* temp profile */
    }
  }

  const failed = findings.filter((f) => f.result === 'FAIL').length
  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings }, null, 2))
  console.log(`DONE failed=${failed}`)
  process.exit(failed ? 1 : 0)
}

run().catch((e) => {
  console.error(e)
  process.exit(1)
})
