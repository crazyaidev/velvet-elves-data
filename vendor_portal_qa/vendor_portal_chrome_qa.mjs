/**
 * Local Vendor Portal QA against http://127.0.0.1:5173 as
 * tessa.grant@minafter.com (Vendor / mortgage loan officer).
 *
 * Default is a low-RAM pass: system Google Chrome, headless, no screenshots,
 * images/fonts blocked, single renderer. Override:
 *
 *   QA_HEADED=1        real headed window (high RAM — avoid on this machine)
 *   QA_CHANNEL=chrome  (default) use installed Google Chrome
 *   QA_SHOTS=1         write PNG screenshots
 *   QA_DUMPS=1         write page text dumps
 */
import { createRequire } from 'module'
import { copyFileSync, mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire(path.join(path.dirname(fileURLToPath(import.meta.url)), 'package.json'))
const { chromium } = require('playwright-core')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const PASS = process.env.QA_PASS || 'first'
const STAMP = new Date().toISOString().slice(0, 10)
const OUT = path.join(__dirname, `artifacts_${STAMP}_${PASS}`)
mkdirSync(OUT, { recursive: true })

const EMAIL = 'tessa.grant@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = process.env.QA_APP || 'http://127.0.0.1:5173'
const FIXTURE = path.join(__dirname, 'fixtures', 'qa-upload.txt')
const HEADED = process.env.QA_HEADED === '1'
const SHOTS = process.env.QA_SHOTS === '1'
const DUMPS = process.env.QA_DUMPS === '1'
const CHANNEL = process.env.QA_CHANNEL || 'chrome'
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let lastOverview = null
let lastTasks = null
let lastDocuments = null
let lastFile = null
let lastUpload = null
let lastRequest = null
let lastCompletion = null
let lastUndo = null
let lastNote = null
let shotIdx = 0

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 6000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 420) : ''}`)
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

async function dumpText(page, name) {
  try {
    const text = await page.locator('body').innerText({ timeout: 8000 })
    if (DUMPS) writeFileSync(path.join(OUT, `${name}.txt`), text)
    return text
  } catch {
    return ''
  }
}

function realConsole() {
  return consoleErrors.filter(
    (e) =>
      !/Download the React DevTools|favicon|third-party cookie|Failed to load resource|`ref` is not a prop/i.test(
        e,
      ),
  )
}

function hasStaffChrome(text) {
  return /AI Suggestions|Task Queue|Inbox Elf|\bActive Transactions\b|\bNew Transaction\b|Vendor Proposals/i.test(
    text,
  )
}

async function dismissOverlays(page, { escape = true } = {}) {
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
  if (escape) await page.keyboard.press('Escape').catch(() => {})
}

async function waitSettled(page, ms = 400) {
  await page.waitForTimeout(ms)
  await page.waitForLoadState('domcontentloaded', { timeout: 8000 }).catch(() => {})
}

async function waitForJson(page, predicate, ms = 25000) {
  const deadline = Date.now() + ms
  while (Date.now() < deadline) {
    if (predicate()) return true
    await page.waitForTimeout(250)
  }
  return false
}

async function waitForVendorShell(page) {
  await page.getByRole('navigation', { name: 'Vendor navigation' }).waitFor({ timeout: 25000 })
}

async function sidebarLabels(page) {
  return page.evaluate(() => {
    const nav = document.querySelector('nav[aria-label="Vendor navigation"]')
    if (!nav) return []
    return [...nav.querySelectorAll('button, a')].map((el) => (el.innerText || '').trim()).filter(Boolean)
  })
}

async function main() {
  const headless = !HEADED
  const launchOpts = {
    headless,
    executablePath: CHROME,
    args: [
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-software-rasterizer',
      '--disable-extensions',
      '--disable-background-networking',
      '--disable-sync',
      '--disable-default-apps',
      '--mute-audio',
      '--no-first-run',
      '--no-default-browser-check',
      '--renderer-process-limit=1',
    ],
  }
  const browser = await chromium.launch(launchOpts)
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
    acceptDownloads: false,
    reducedMotion: 'reduce',
    serviceWorkers: 'block',
  })
  await context.route(/\.(png|jpe?g|gif|webp|svg|ico|woff2?|ttf|otf|mp4|mp3)(\?|$)/i, (route) =>
    route.abort(),
  )
  const page = await context.newPage()
  page.setDefaultTimeout(14000)
  console.log(
    `browser=${CHANNEL || 'chrome'} headless=${headless} viewport=1280x720 shots=${SHOTS} app=${APP}`,
  )

  page.on('console', (msg) => {
    if (msg.type() === 'error' && consoleErrors.length < 20) consoleErrors.push(msg.text().slice(0, 400))
  })
  page.on('pageerror', (err) => {
    if (pageErrors.length < 12) pageErrors.push(String(err.message).slice(0, 400))
  })
  page.on('requestfailed', (req) => {
    const err = req.failure()?.errorText || ''
    if (/ERR_ABORTED|NS_BINDING_ABORTED|fonts\.gstatic|\.woff2|logo-removebg|favicon/i.test(`${req.url()} ${err}`)) return
    if (failedRequests.length < 40) failedRequests.push(`${req.method()} ${req.url()} ${err}`.trim().slice(0, 300))
  })
  page.on('response', async (res) => {
    try {
      const url = res.url()
      if (!url.includes('/api/v1/')) return
      if (!res.ok()) {
        if (failedRequests.length < 40) {
          failedRequests.push(`${res.status()} ${res.request().method()} ${url}`.slice(0, 300))
        }
        return
      }
      if (
        !/\/vendor-portal\/|\/documents\/upload|\/users\/login/.test(url)
      ) {
        return
      }
      const json = await res.json().catch(() => null)
      if (!json) return
      if (url.includes('/vendor-portal/overview')) lastOverview = json
      else if (url.includes('/vendor-portal/tasks') && res.request().method() === 'GET') lastTasks = json
      else if (url.includes('/vendor-portal/documents/request')) lastRequest = json
      else if (url.includes('/vendor-portal/documents') && res.request().method() === 'GET') lastDocuments = json
      else if (/\/vendor-portal\/files\/[^/]+$/.test(url) && res.request().method() === 'GET') lastFile = json
      else if (url.includes('/documents/upload') && res.request().method() === 'POST') lastUpload = { ok: true, id: json.id, tx: json.transaction_id }
      else if (url.includes('/completion-request')) lastCompletion = json
      else if (url.includes('/task-actions/') && res.request().method() === 'DELETE') lastUndo = { ok: true }
      else if (url.includes('/note') && res.request().method() === 'POST') lastNote = json
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
    const loginWait = page.waitForResponse(
      (res) => res.url().includes('/users/login') && res.request().method() === 'POST',
      { timeout: 30000 },
    )
    await page.getByRole('button', { name: /sign in/i }).click()
    const loginRes = await loginWait
    log('VP-01 login', loginRes.ok() ? 'PASS' : 'FAIL', `status=${loginRes.status()}`)
  } catch (err) {
    log('VP-01 login', 'FAIL', err.message)
  }

  try {
    await page.waitForURL(/\/portal\/vendor/, { timeout: 25000 })
    await waitForVendorShell(page)
    await waitForJson(page, () => lastOverview?.greeting_name, 35000)
    await page.getByRole('heading', { name: /Good day, Tessa/i }).waitFor({ timeout: 20000 })
    await dismissOverlays(page)
    log('VP-02 lands on vendor portal', 'PASS', page.url())
  } catch (err) {
    log('VP-02 lands on vendor portal', 'FAIL', `${page.url()} ${err.message}`)
  }
  await shot(page, 'files_home')

  // ── 2. Shell + greeting ─────────────────────────────────────────────────
  const homeText = await dumpText(page, 'files_home')
  const nav = await sidebarLabels(page)
  log(
    'VP-03 vendor nav is Files / Documents / Tasks',
    nav.some((n) => /loan files|title files|your files/i.test(n)) &&
      nav.some((n) => /documents/i.test(n)) &&
      nav.some((n) => /tasks/i.test(n))
      ? 'PASS'
      : 'FAIL',
    JSON.stringify(nav),
  )
  log(
    'VP-04 no staff chrome on files home',
    hasStaffChrome(homeText) ? 'FAIL' : 'PASS',
    hasStaffChrome(homeText) ? homeText.slice(0, 240) : '',
  )
  log(
    'VP-05 greeting uses Tessa and mortgage role',
    /Good day, Tessa/i.test(homeText) && /Mortgage Loan Officer/i.test(homeText) ? 'PASS' : 'FAIL',
    homeText.slice(0, 280),
  )
  log(
    'VP-06 assigned Meadowridge file is listed',
    /4567 Meadowridge/i.test(homeText) ? 'PASS' : 'FAIL',
  )
  log(
    'VP-07 boundary notice present',
    /You only see requests addressed to you/i.test(homeText) ? 'PASS' : 'FAIL',
  )
  log(
    'VP-08 overview API scoped as mortgage',
    lastOverview?.scope_family === 'mortgage' && lastOverview?.stats?.files === 1 ? 'PASS' : 'FAIL',
    JSON.stringify(lastOverview?.stats),
  )
  const badge = lastOverview?.files?.[0]?.milestone_label
  log(
    'VP-09 file badge is a real stage, not "1"',
    badge && badge !== '1' && !/^\d+$/.test(String(badge)) ? 'PASS' : 'FAIL',
    `milestone_label=${badge}`,
  )
  const milestoneLabels = (lastOverview?.files?.[0]?.milestones || []).map((m) => m.label)
  log(
    'VP-10 progress strip has no Title Work / junk "1" / Deadline dots',
    !milestoneLabels.some((l) => l === '1' || /^deadline$/i.test(l) || /title work/i.test(l))
      ? 'PASS'
      : 'FAIL',
    JSON.stringify(milestoneLabels),
  )

  // ── 3. Expand file card ─────────────────────────────────────────────────
  try {
    const card = page.locator('section').filter({ hasText: 'Assigned' }).locator('button[aria-expanded]').first()
    await card.click()
    await page.getByText(/Limited view|Contacts/i).first().waitFor({ timeout: 8000 })
    await waitSettled(page, 500)
    const expanded = await dumpText(page, 'file_expanded')
    log(
      'VP-11 expand file shows contacts / tasks / documents panels',
      /Contacts/i.test(expanded) && /documents/i.test(expanded) ? 'PASS' : 'FAIL',
      expanded.slice(0, 360),
    )
    log(
      'VP-12 mortgage vendor does not see the seller',
      /\bSeller\b/i.test(expanded) && /Jordan Seller|Pat Seller/i.test(expanded)
        ? 'FAIL'
        : /Seller/i.test(expanded) && /Maya Ellis|Luis Romero/i.test(expanded)
          ? 'PASS'
          : /Maya Ellis/i.test(expanded)
            ? 'PASS'
            : 'WARN',
      'seller-section presence checked against buyer-side names',
    )
    const tessaContacts = (lastFile?.contacts || []).filter((c) => /tessa grant/i.test(c.name || ''))
    log(
      'VP-13 Tessa is listed once in contacts (no party+vendor duplicate)',
      tessaContacts.length <= 1 ? 'PASS' : 'FAIL',
      `tessaContacts=${tessaContacts.length} total=${(lastFile?.contacts || []).length}`,
    )
    const hasReachable = (lastFile?.contacts || []).some((c) => c.email || c.phone)
    log(
      'VP-14 contact rows show email or phone',
      hasReachable && /maya\.ellis@minafter\.com|\(614\) 555-9900/i.test(expanded) ? 'PASS' : hasReachable ? 'WARN' : 'FAIL',
    )
    log(
      'VP-15 coordinator tasks are not on the expanded card',
      /Deliver HOA|Internal Thank You|Buyer Welcome|Closing Gift/i.test(expanded) ? 'FAIL' : 'PASS',
    )
  } catch (err) {
    log('VP-11 expand file shows contacts / tasks / documents panels', 'FAIL', err.message)
  }

  try {
    await page.getByPlaceholder(/Send a quick update/i).fill('QA: appraisal scheduled for Friday.')
    await page.getByRole('button', { name: /^send$/i }).click()
    await waitSettled(page, 800)
    log('VP-16 send file update', lastNote?.id || /Sent to your coordinator|QA: appraisal/i.test(await dumpText(page, 'after_note')) ? 'PASS' : 'WARN', JSON.stringify(lastNote))
  } catch (err) {
    log('VP-16 send file update', 'FAIL', err.message)
  }

  // ── 4. Documents ────────────────────────────────────────────────────────
  try {
    await page.getByRole('button', { name: /^Documents$/i }).click()
    await page.waitForURL(/\/portal\/vendor\/documents/, { timeout: 12000 })
    await waitSettled(page, 600)
    const docsText = await dumpText(page, 'documents')
    log(
      'VP-17 documents page loads',
      /Documents/i.test(docsText) && /Today's briefing/i.test(docsText) ? 'PASS' : 'FAIL',
      docsText.slice(0, 240),
    )
    log('VP-18 documents page has no staff chrome', hasStaffChrome(docsText) ? 'FAIL' : 'PASS')
    for (const tab of ['Needs attention', 'All', 'Shared with you', 'Your uploads', 'Awaiting']) {
      const btn = page.getByRole('button', { name: new RegExp(tab, 'i') }).first()
      const visible = await btn.isVisible().catch(() => false)
      log(`VP-19 tab "${tab}" present`, visible ? 'PASS' : 'FAIL')
      if (visible) {
        await btn.click()
        await waitSettled(page, 250)
      }
    }
  } catch (err) {
    log('VP-17 documents page loads', 'FAIL', err.message)
  }

  try {
    await page.getByRole('button', { name: /request a document/i }).click()
    await page.getByPlaceholder(/e\.g\. Appraisal report|What do you need/i).waitFor({ timeout: 5000 })
    await page.getByRole('button', { name: /pre-approval letter/i }).click()
    await page.getByRole('button', { name: /send request/i }).click()
    await waitSettled(page, 900)
    log(
      'VP-20 request a document',
      lastRequest?.status === 'awaiting' || /Request sent|Awaiting/i.test(await dumpText(page, 'after_request'))
        ? 'PASS'
        : 'FAIL',
      JSON.stringify(lastRequest),
    )
    await page.keyboard.press('Escape').catch(() => {})
  } catch (err) {
    log('VP-20 request a document', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  const uniqueUploadName = `qa-upload-${Date.now()}.txt`
  const uniqueUploadPath = path.join(OUT, uniqueUploadName)
  try {
    copyFileSync(FIXTURE, uniqueUploadPath)
    const fileInput = page.locator('input[type="file"]:not([disabled])').first()
    await fileInput.waitFor({ state: 'attached', timeout: 15000 })
    const uploadWait = page.waitForResponse(
      (res) => res.url().includes('/documents/upload') && res.request().method() === 'POST',
      { timeout: 25000 },
    )
    await fileInput.setInputFiles({
      name: uniqueUploadName,
      mimeType: 'text/plain',
      buffer: Buffer.from(`vendor-portal-qa ${uniqueUploadName}\n`),
    })
    const uploadRes = await uploadWait
    const uploadBody = await uploadRes.json().catch(() => null)
    lastUpload = {
      ok: uploadRes.ok(),
      status: uploadRes.status(),
      id: uploadBody?.id ?? null,
      tx: uploadBody?.transaction_id ?? null,
    }
    log(
      'VP-21 upload attaches to the assigned file',
      lastUpload.ok && lastUpload.tx ? 'PASS' : 'FAIL',
      JSON.stringify(lastUpload),
    )
    await page.getByRole('button', { name: /your uploads/i }).click()
    await page.getByText(uniqueUploadName).first().waitFor({ timeout: 15000 })
    const uploadsText = await dumpText(page, 'uploads')
    log(
      'VP-22 uploaded file appears under Your uploads',
      uploadsText.includes(uniqueUploadName) ? 'PASS' : 'FAIL',
      uploadsText.slice(0, 280),
    )
  } catch (err) {
    log('VP-21 upload attaches to the assigned file', 'FAIL', err.message)
  }

  // ── 5. Tasks ────────────────────────────────────────────────────────────
  try {
    await page.getByRole('button', { name: /^Tasks$/i }).click()
    await page.waitForURL(/\/portal\/vendor\/tasks/, { timeout: 12000 })
    await page.getByText(/Appraisal Completed|Loan application due/i).first().waitFor({ timeout: 15000 })
    await waitForJson(page, () => Array.isArray(lastTasks?.tasks) && lastTasks.tasks.length > 0, 20000)
    await waitSettled(page, 400)
    const tasksText = await dumpText(page, 'tasks')
    log(
      'VP-23 tasks page is Mortgage Tasks',
      /Mortgage Tasks/i.test(tasksText) ? 'PASS' : 'FAIL',
      tasksText.slice(0, 200),
    )
    log(
      'VP-24 tasks page hides coordinator checklist',
      /Deliver HOA|Internal Thank You|Closing Gift|Buyer Welcome/i.test(tasksText) ? 'FAIL' : 'PASS',
    )
    log(
      'VP-25 mortgage work is listed',
      /Appraisal|Loan application|Financing/i.test(tasksText) ? 'PASS' : 'FAIL',
    )
  } catch (err) {
    log('VP-23 tasks page is Mortgage Tasks', 'FAIL', err.message)
  }

  try {
    const fileToggle = page.getByRole('button', { name: /4567 Meadowridge/i }).first()
    if ((await fileToggle.getAttribute('aria-expanded').catch(() => 'false')) !== 'true') {
      await fileToggle.click()
      await waitSettled(page, 400)
    }
    const openTask = (lastTasks?.tasks || []).find(
      (t) => t.action_status !== 'pending' && t.group !== 'done',
    )
    const taskName = openTask?.name || 'Appraisal Completed'
    const taskToggle = page.getByRole('button', { name: new RegExp(taskName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i') }).first()
    await taskToggle.click()
    const markDone = page.getByRole('button', { name: /^Mark done$/i }).first()
    await markDone.waitFor({ timeout: 12000 })
    await markDone.click()
    await page.getByRole('heading', { name: /Mark task done/i }).waitFor({ timeout: 8000 })
    const reasonChip = page.getByRole('button', { name: 'Appraisal received' })
    if (await reasonChip.isVisible().catch(() => false)) {
      await reasonChip.click()
    } else {
      await page.getByRole('button', { name: /^Completed$/i }).click()
    }
    const closeWait = page.waitForResponse(
      (res) => res.url().includes('/completion-request') && res.request().method() === 'POST',
      { timeout: 20000 },
    )
    await page.getByRole('button', { name: /request to close/i }).click()
    const closeRes = await closeWait
    lastCompletion = await closeRes.json().catch(() => lastCompletion)
    log(
      'VP-26 mark done submits a close-out',
      lastCompletion?.status === 'pending' ? 'PASS' : 'FAIL',
      JSON.stringify(lastCompletion),
    )
    const undo = page.getByRole('button', { name: /undo request/i }).first()
    try {
      await undo.waitFor({ state: 'visible', timeout: 8000 })
      const undoWait = page.waitForResponse(
        (res) => res.url().includes('/task-actions/') && res.request().method() === 'DELETE',
        { timeout: 15000 },
      )
      await undo.click()
      const undoRes = await undoWait
      lastUndo = { ok: undoRes.ok() }
      log('VP-27 undo pending close-out', lastUndo.ok ? 'PASS' : 'FAIL', JSON.stringify(lastUndo))
    } catch (undoErr) {
      log('VP-27 undo pending close-out', 'WARN', undoErr.message)
    }
  } catch (err) {
    log('VP-26 mark done submits a close-out', 'FAIL', err.message)
  }

  // ── 6. File detail route + helper links + profile ───────────────────────
  const txId = lastOverview?.files?.[0]?.transaction_id
  if (txId) {
    try {
      await page.goto(`${APP}/portal/vendor/files/${txId}`, { waitUntil: 'domcontentloaded' })
      await waitForVendorShell(page)
      await page.getByText(/Back to files/i).waitFor({ timeout: 10000 })
      await page.getByText(/4567 Meadowridge/i).waitFor({ timeout: 20000 })
      const detail = await dumpText(page, 'file_detail')
      log(
        'VP-28 file detail deep link',
        /Back to files/i.test(detail) && /4567 Meadowridge/i.test(detail) ? 'PASS' : 'FAIL',
        detail.slice(0, 200),
      )
    } catch (err) {
      log('VP-28 file detail deep link', 'FAIL', err.message)
    }
  } else {
    log('VP-28 file detail deep link', 'WARN', 'no transaction id')
  }

  try {
    await page.goto(`${APP}/portal/vendor`, { waitUntil: 'domcontentloaded' })
    await waitForVendorShell(page)
    await page.getByRole('link', { name: /upload requested documents/i }).click()
    await page.waitForURL(/\/portal\/vendor\/documents/, { timeout: 8000 })
    log('VP-29 helper card opens Documents', 'PASS', page.url())
  } catch (err) {
    log('VP-29 helper card opens Documents', 'FAIL', err.message)
  }

  try {
    await page.goto(`${APP}/portal/vendor`, { waitUntil: 'domcontentloaded' })
    await waitForVendorShell(page)
    await page.getByRole('button', { name: /tessa grant/i }).click()
    await page.getByRole('button', { name: /profile/i }).click()
    await waitSettled(page, 500)
    const profile = await dumpText(page, 'profile')
    log(
      'VP-30 profile modal opens',
      /profile/i.test(profile) && /tessa\.grant@minafter\.com/i.test(profile) ? 'PASS' : 'FAIL',
      profile.slice(0, 240),
    )
    await page.keyboard.press('Escape')
  } catch (err) {
    log('VP-30 profile modal opens', 'FAIL', err.message)
  }

  // ── 7. Scope wall: staff URLs bounce ────────────────────────────────────
  for (const [id, path, expectStay] of [
    ['VP-31 bounce /settings', '/settings', false],
    ['VP-32 bounce /dashboard', '/dashboard', false],
    ['VP-33 bounce /ai-emails', '/ai-emails', false],
    ['VP-34 bounce /transactions', '/transactions', false],
    ['VP-35 bounce /client/home', '/client/home', false],
  ]) {
    try {
      await page.goto(`${APP}${path}`, { waitUntil: 'domcontentloaded', timeout: 20000 })
      await page.waitForURL(/\/portal\/vendor/, { timeout: 12000 })
      await waitSettled(page, 400)
      const url = page.url()
      const text = await dumpText(page, id.replace(/\W+/g, '_'))
      const bounced = /\/portal\/vendor/.test(url)
      const leaked = hasStaffChrome(text)
      log(
        id,
        bounced && !leaked ? 'PASS' : 'FAIL',
        `url=${url} leakedStaff=${leaked}`,
      )
    } catch (err) {
      log(id, 'FAIL', `${page.url()} ${err.message}`)
    }
  }

  // ── 8. Console / network ────────────────────────────────────────────────
  const cons = realConsole()
  log('VP-36 no page errors', pageErrors.length === 0 ? 'PASS' : 'FAIL', pageErrors.join(' | '))
  log(
    'VP-37 no unexpected API failures',
    failedRequests.length === 0 ? 'PASS' : 'WARN',
    failedRequests.join(' | '),
  )
  log(
    'VP-38 console is clean of app errors',
    cons.length === 0 ? 'PASS' : 'WARN',
    cons.join(' | '),
  )

  const summary = {
    pass: findings.filter((f) => f.result === 'PASS').length,
    fail: findings.filter((f) => f.result === 'FAIL').length,
    warn: findings.filter((f) => f.result === 'WARN').length,
    total: findings.length,
  }
  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ summary, findings, lastOverview, lastTasks, lastDocuments }, null, 2))
  console.log(`\nSUMMARY ${JSON.stringify(summary)}`)
  await browser.close()
  if (summary.fail > 0) process.exitCode = 1
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
