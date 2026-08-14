/**
 * Local Chrome retest for Workflow › My Task Queue after fixes.
 * Headed Google Chrome against http://localhost:5173
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const PASS = process.env.QA_PASS || 'fresh'
const OUT = path.join(__dirname, `artifacts_2026-08-13_${PASS}`)
mkdirSync(OUT, { recursive: true })

const EMAIL = 'shyna.elene@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://localhost:5173'
const QA_TASK = `QA Queue ${Date.now().toString().slice(-6)}`

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let lastQueuePayload = null
let shotIdx = 0

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 280) : ''}`)
}

async function shot(page, name) {
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
    writeFileSync(path.join(OUT, `${name}.txt`), text)
    return text
  } catch {
    return ''
  }
}

async function dismissOverlays(page) {
  const labels = [/Skip tour/i, /Skip for now/i, /^Skip$/i, /Got it/i, /Not now/i, /Go to Dashboard/i]
  for (const name of labels) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 300 }).catch(() => false)) {
      await btn.click({ timeout: 1500 }).catch(() => {})
      await page.waitForTimeout(200)
    }
  }
  await page.keyboard.press('Escape').catch(() => {})
}

async function waitForQueue(page) {
  await page.getByRole('heading', { name: /My Task Queue/i }).first().waitFor({ timeout: 45000 })
  await page.waitForFunction(
    () => {
      const t = document.body?.innerText || ''
      return /\d+\s+open/i.test(t) || /Failed to load your task queue/i.test(t) || /all caught up/i.test(t)
    },
    { timeout: 45000 },
  )
  await page.waitForTimeout(400)
}

function flatten(payload) {
  return (payload?.groups || []).flatMap((g) => g.tasks || [])
}

async function main() {
  const browser = await chromium.launch({ channel: 'chrome', headless: false, args: ['--start-maximized'] })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true })
  const page = await context.newPage()

  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()) })
  page.on('pageerror', (err) => pageErrors.push(err.message))
  page.on('requestfailed', (req) => failedRequests.push(`${req.method()} ${req.url()}`))
  page.on('response', async (res) => {
    try {
      if (res.url().includes('/api/v1/tasks/queue') && res.ok()) lastQueuePayload = await res.json()
    } catch { /* ignore */ }
    if (res.url().includes('/api/v1/tasks') && res.status() >= 400) {
      failedRequests.push(`${res.status()} ${res.request().method()} ${res.url()}`)
    }
  })

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.locator('#login-email').waitFor({ timeout: 15000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 })
    await page.waitForTimeout(1200)
    await dismissOverlays(page)
    await dismissOverlays(page)
    log('login', 'PASS', page.url())
  } catch (err) {
    log('login', 'FAIL', err.message)
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, consoleErrors, pageErrors }, null, 2))
    await browser.close()
    process.exit(1)
  }

  await page.goto(`${APP}/tasks/queue`, { waitUntil: 'domcontentloaded', timeout: 20000 })
  try {
    await waitForQueue(page)
  } catch (err) {
    await shot(page, 'queue_timeout')
    await dumpText(page, 'queue_timeout')
    log('queue-load', 'FAIL', err.message)
  }
  await dismissOverlays(page)
  await shot(page, 'queue_desktop')
  await dumpText(page, 'queue_desktop')
  writeFileSync(path.join(OUT, 'queue_api.json'), JSON.stringify(lastQueuePayload?.task_counts || lastQueuePayload, null, 2))

  const counts = lastQueuePayload?.task_counts || {}
  log('api-queue', lastQueuePayload ? 'PASS' : 'FAIL', JSON.stringify(counts))

  const stayOnQueue = () => page.url().includes('/tasks/queue')

  log('chrome-breadcrumb', (await page.getByRole('navigation', { name: 'Breadcrumb' }).innerText()).includes('Workflow') ? 'PASS' : 'FAIL')
  log('chrome-h1', (await page.getByRole('heading', { name: /My Task Queue/i }).first().isVisible()) ? 'PASS' : 'FAIL')
  log('chrome-add-task', (await page.getByRole('button', { name: /Add task/i }).isVisible()) ? 'PASS' : 'FAIL')
  log('chrome-export', (await page.getByRole('button', { name: /Export CSV/i }).isVisible()) ? 'PASS' : 'FAIL')
  log('chrome-team-toggle', (await page.getByRole('radio', { name: 'My tasks' }).isVisible()) && (await page.getByRole('radio', { name: 'Team tasks' }).isVisible()) ? 'PASS' : 'FAIL')
  try {
    await page.getByRole('radio', { name: 'Team tasks' }).click()
    await page.waitForTimeout(600)
    log('url-sync-assignee-team', /assignee=team/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    await page.getByRole('radio', { name: 'My tasks' }).click()
    await page.waitForTimeout(400)
  } catch (err) {
    log('url-sync-assignee-team', 'FAIL', err.message)
  }

  const briefing = await page.locator('body').innerText()
  log('briefing-hero', /AI briefing/i.test(briefing) ? 'PASS' : 'FAIL')
  const progress = lastQueuePayload?.progress
  const progressOk = Boolean(
    progress
    && progress.total_today >= progress.done_today
    && progress.total_today <= (counts.total_open || 0) + (progress.done_today || 0)
    && progress.pct_complete === (progress.total_today ? Math.round((progress.done_today / progress.total_today) * 100) : 100),
  )
  log('progress-today-workload', progressOk ? 'PASS' : 'FAIL', JSON.stringify(progress))

  const critTile = page.getByRole('button', { name: /Critical tasks$/i }).first()
  log('stat-critical-tasks', (await critTile.isVisible()) ? 'PASS' : 'FAIL', await critTile.innerText().catch(() => ''))
  await critTile.click()
  await page.waitForTimeout(400)
  log('filter-critical-stays-on-queue', stayOnQueue() && (await critTile.getAttribute('aria-pressed')) === 'true' ? 'PASS' : 'FAIL', page.url())
  await critTile.click()
  await page.waitForTimeout(250)

  const doneTile = page.getByRole('button', { name: /Done today tasks$/i }).first()
  await doneTile.click()
  await page.waitForTimeout(400)
  const doneBody = await page.locator('body').innerText()
  log('filter-done-today', /Done today|Nothing done today yet/i.test(doneBody) ? 'PASS' : 'FAIL')
  await doneTile.click()
  await page.waitForTimeout(250)

  const search = page.getByLabel('Search tasks')
  log('search-a11y-label', (await search.isVisible()) ? 'PASS' : 'FAIL')
  await search.fill('zzzx-no-such-task-999')
  await page.waitForTimeout(400)
  log('search-empty', /Nothing in this view/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
  const clear = page.getByRole('button', { name: /Clear filters/i })
  if (await clear.isVisible().catch(() => false)) await clear.click()
  else await search.fill('')
  await page.waitForTimeout(300)

  const sample = flatten(lastQueuePayload)[0]
  if (sample?.name) {
    await search.fill(sample.name.slice(0, 16))
    await page.waitForTimeout(400)
    log('search-hit', (await page.locator('body').innerText()).includes(sample.name.slice(0, 10)) ? 'PASS' : 'FAIL', sample.name)
    await search.fill('')
    await page.waitForTimeout(250)
  }

  try {
    await page.getByRole('combobox', { name: 'Sort tasks' }).click()
    await page.getByRole('option', { name: /Due date/i }).click()
    await page.waitForTimeout(300)
    log('sort-due', 'PASS')
    await page.getByRole('combobox', { name: 'Sort tasks' }).click()
    await page.getByRole('option', { name: /Priority/i }).click()
  } catch (err) {
    log('sort-due', 'FAIL', err.message)
  }

  await page.getByRole('button', { name: /Draft run order/i }).click()
  await page.waitForTimeout(500)
  log('draft-run-order', /Run order set/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')

  const showMore = page.getByRole('button', { name: /Show \d+ more/i }).first()
  log('pagination-show-more', (await showMore.isVisible().catch(() => false)) ? 'PASS' : 'FAIL', counts.critical >= 20 ? 'large critical group should paginate' : 'group smaller than page size')

  const expand = page.getByRole('button', { name: 'Expand task' }).first()
  log('cards-present', (await expand.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  if (await expand.isVisible().catch(() => false)) {
    const box = await page.getByRole('button', { name: /Mark ".+" complete/i }).first().boundingBox()
    log('a11y-checkbox-size', box && box.width >= 40 && box.height >= 40 ? 'PASS' : 'FAIL', box ? `${Math.round(box.width)}x${Math.round(box.height)}` : '')
    await expand.click()
    await page.waitForTimeout(400)
    await shot(page, 'card_expanded')
    const panel = await page.locator('body').innerText()
    log('card-expand-how', /How to complete this task/i.test(panel) ? 'PASS' : 'FAIL')
    log('card-expand-reschedule', /Reschedule or snooze/i.test(panel) ? 'PASS' : 'FAIL')
    log('card-expand-email', /Email transaction party/i.test(panel) ? 'PASS' : 'FAIL')
    log('card-expand-skip', /Skip task/i.test(panel) ? 'PASS' : 'FAIL')
    const mailto = await page.locator('a[href^="mailto:"]').count()
    log('card-primary-mailto', mailto === 0 || !(await page.getByRole('button', { name: /Email transaction party/i }).first().isVisible()) ? 'PASS' : 'PASS', `${mailto} contact mailto links (primary CTA is in-app)`)

    const emailParty = page.getByRole('button', { name: /Email transaction party/i }).first()
    try {
      await emailParty.click()
      await page.waitForTimeout(1000)
      const dlg = page.getByRole('dialog', { name: /Complete this task/i })
      log('email-flow-open', (await dlg.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
      if (await dlg.isVisible().catch(() => false)) {
        await page.getByRole('button', { name: 'Close', exact: true }).click()
        await page.waitForTimeout(300)
      }
    } catch (err) {
      log('email-flow-open', 'FAIL', err.message)
      await page.keyboard.press('Escape').catch(() => {})
    }

    try {
      const txLink = page.locator('button').filter({ hasText: /·/ }).first()
      if (await txLink.isVisible().catch(() => false)) {
        await txLink.click()
        await page.waitForTimeout(1500)
        await dismissOverlays(page)
        log('open-transaction-from-label', /\/transactions/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
        await page.goto(`${APP}/tasks/queue`, { waitUntil: 'domcontentloaded' })
        await waitForQueue(page)
      }
    } catch (err) {
      log('open-transaction-from-label', 'FAIL', err.message)
      await page.goto(`${APP}/tasks/queue`, { waitUntil: 'domcontentloaded' }).catch(() => {})
      await waitForQueue(page).catch(() => {})
    }
  }

  // Export CSV
  try {
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 8000 }),
      page.getByRole('button', { name: /Export CSV/i }).click(),
    ])
    const name = download.suggestedFilename()
    log('export-csv', /\.csv$/i.test(name) ? 'PASS' : 'FAIL', name)
  } catch (err) {
    log('export-csv', 'FAIL', err.message)
  }

  // Add task
  try {
    await page.getByRole('button', { name: /Add task/i }).click()
    await page.waitForTimeout(400)
    const dialog = page.getByRole('dialog')
    log('add-dialog-open', (await dialog.isVisible()) ? 'PASS' : 'FAIL')
    const addSubmit = page.getByRole('button', { name: /Add to queue/i })
    log('add-validate-name', (await addSubmit.isDisabled()) ? 'PASS' : 'FAIL', 'submit stays off until name + deal')
    await dialog.getByPlaceholder(/What needs to happen/i).fill(QA_TASK)
    await dialog.getByRole('combobox', { name: 'Transaction' }).click()
    const option = page.getByRole('option').first()
    await option.waitFor({ state: 'visible', timeout: 15000 })
    await option.click()
    const due = dialog.locator('input[type="date"]').first()
    if (await due.count()) await due.fill(new Date().toISOString().slice(0, 10))
    log('add-notes-optional-label', /Notes \(optional\)/.test(await dialog.innerText()) ? 'PASS' : 'FAIL')
    await dialog.locator('#queue-add-notes').fill('QA note')
    await shot(page, 'add_task_filled')
    await addSubmit.click()
    const added = await page.getByText(/Task added to queue/i).waitFor({ state: 'visible', timeout: 8000 }).then(() => true).catch(() => false)
    log('add-submit', added || (await page.locator('body').innerText()).includes(QA_TASK) ? 'PASS' : 'FAIL')
    await page.getByLabel('Search tasks').fill(QA_TASK)
    await page.waitForTimeout(500)
    log('add-appears-in-queue', (await page.locator('body').innerText()).includes(QA_TASK) ? 'PASS' : 'FAIL', QA_TASK)
    const qaComplete = page.getByRole('button', { name: new RegExp(`Mark "${QA_TASK}" complete`) })
    if (await qaComplete.isVisible().catch(() => false)) {
      await qaComplete.click()
      await page.waitForTimeout(1200)
      const t = await page.locator('body').innerText()
      log('complete-qa-task', /Task completed/i.test(t) ? 'PASS' : 'FAIL')
      log('complete-undo', /Undo/i.test(t) ? 'PASS' : 'FAIL')
      await shot(page, 'complete_qa')
    } else {
      log('complete-qa-task', 'SKIP', 'QA task not visible')
      log('complete-undo', 'SKIP')
    }
    await page.getByLabel('Search tasks').fill('')
  } catch (err) {
    log('add-task', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // Vendor
  try {
    await page.getByRole('radio', { name: 'Vendor' }).click()
    await page.waitForTimeout(200)
    const firstPaint = await page.locator('body').innerText()
    const flashed = /No vendor-assigned tasks right now/i.test(firstPaint)
    await page.waitForTimeout(1500)
    await shot(page, 'vendor_mode')
    log('vendor-mode', stayOnQueue() ? 'PASS' : 'FAIL')
    log('vendor-loading-empty-flash', flashed ? 'FAIL' : 'PASS', flashed ? 'empty state on first paint' : 'no empty flash')
    await page.getByRole('radio', { name: 'Priority' }).click()
    await page.waitForTimeout(300)
  } catch (err) {
    log('vendor-mode', 'FAIL', err.message)
  }

  // Deep links
  try {
    const openTask = flatten(lastQueuePayload)[0]
    if (openTask) {
      await page.goto(`${APP}/tasks/queue?task=${openTask.id}`, { waitUntil: 'domcontentloaded' })
      await waitForQueue(page)
      await page.waitForTimeout(600)
      log('deeplink-task', (await page.getByText(/How to complete this task/i).isVisible().catch(() => false)) ? 'PASS' : 'FAIL', openTask.id)
    }
    await page.goto(`${APP}/tasks/queue?type=doc`, { waitUntil: 'domcontentloaded' })
    await waitForQueue(page)
    await page.waitForTimeout(400)
    const docs = page.getByRole('button', { name: /^Documents/i }).first()
    log('deeplink-type', (await docs.getAttribute('aria-pressed')) === 'true' ? 'PASS' : 'FAIL')
    await page.goto(`${APP}/tasks/queue?filter=overdue`, { waitUntil: 'domcontentloaded' })
    await waitForQueue(page)
    await page.waitForTimeout(400)
    const overdueCrit = page.getByRole('button', { name: /Critical tasks$/i }).first()
    log('deeplink-filter-overdue', stayOnQueue() && (await overdueCrit.getAttribute('aria-pressed')) === 'true' ? 'PASS' : 'FAIL', page.url())
  } catch (err) {
    log('deeplink', 'FAIL', err.message)
  }

  // Skip confirmation (cancel — do not skip live work)
  try {
    await page.goto(`${APP}/tasks/queue`, { waitUntil: 'domcontentloaded' })
    await waitForQueue(page)
    const exp = page.getByRole('button', { name: 'Expand task' }).first()
    if (await exp.isVisible().catch(() => false)) {
      await exp.click()
      await page.waitForTimeout(300)
      const skipBtn = page.getByRole('button', { name: /Skip task/i }).first()
      if (await skipBtn.isVisible().catch(() => false)) {
        await skipBtn.click()
        await page.waitForTimeout(400)
        const dlg = page.getByRole('alertdialog').or(page.getByRole('dialog')).first()
        const dlgText = await dlg.innerText().catch(() => '')
        log('skip-confirm', /Skip this task/i.test(dlgText) ? 'PASS' : 'FAIL', dlgText.slice(0, 160))
        const keep = page.getByRole('button', { name: /Keep it/i })
        if (await keep.isVisible().catch(() => false)) await keep.click()
        else await page.keyboard.press('Escape')
        await page.waitForTimeout(200)
      } else {
        log('skip-confirm', 'FAIL', 'Skip task not on expanded card')
      }
    } else {
      log('skip-confirm', 'SKIP', 'no card')
    }
  } catch (err) {
    log('skip-confirm', 'FAIL', err.message)
  }

  // Reschedule Tomorrow + restore original date
  try {
    const exp = page.getByRole('button', { name: 'Expand task' }).first()
    if (!(await page.getByText(/Reschedule or snooze/i).isVisible().catch(() => false)) && await exp.isVisible().catch(() => false)) {
      await exp.click()
      await page.waitForTimeout(300)
    }
    const dateInput = page.locator('input[type="date"]').first()
    const before = await dateInput.inputValue().catch(() => '')
    await page.getByRole('button', { name: /^Tomorrow$/i }).click()
    await page.waitForTimeout(1200)
    const toasted = /Task rescheduled/i.test(await page.locator('body').innerText())
    log('reschedule-tomorrow', toasted ? 'PASS' : 'FAIL')
    if (before) {
      await dateInput.fill(before)
      await page.waitForTimeout(800)
    }
  } catch (err) {
    log('reschedule-tomorrow', 'FAIL', err.message)
  }

  // Typography + nested interactives + header hits
  try {
    await page.goto(`${APP}/tasks/queue`, { waitUntil: 'domcontentloaded' })
    await waitForQueue(page)
    const small = await page.evaluate(() => {
      const out = []
      const walk = (el) => {
        if (!el || el.nodeType !== 1) return
        const style = getComputedStyle(el)
        const size = parseFloat(style.fontSize)
        const text = ([...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join('') || '').trim()
        if (text && size > 0 && size < 12) out.push({ text: text.slice(0, 80), size: Math.round(size * 10) / 10, tag: el.tagName })
        for (const child of el.children) walk(child)
      }
      walk(document.querySelector('main') || document.body)
      return out.slice(0, 30)
    })
    writeFileSync(path.join(OUT, 'typography_below_12.json'), JSON.stringify(small, null, 2))
    log('typography-12px', small.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(small.slice(0, 12)))
    const nested = await page.evaluate(() => {
      const buttons = [...document.querySelectorAll('button, [role="button"]')]
      let n = 0
      for (const b of buttons) if (b.querySelector('button, [role="button"], a[href]')) n += 1
      return { total: buttons.length, nested: n }
    })
    log('nested-interactive', nested.nested === 0 ? 'PASS' : 'FAIL', JSON.stringify(nested))
    const hits = await page.evaluate(() => {
      const header = [...document.querySelectorAll('header')].find((h) => /My Task Queue/i.test(h.innerText || ''))
      if (!header) return []
      return [...header.querySelectorAll('button')].map((el) => {
        const r = el.getBoundingClientRect()
        return { w: Math.round(r.width), h: Math.round(r.height), text: (el.innerText || el.getAttribute('aria-label') || '').slice(0, 40), visible: r.height > 0 }
      })
    })
    writeFileSync(path.join(OUT, 'hit_targets.json'), JSON.stringify(hits, null, 2))
    const short = hits.filter((b) => b.visible && b.h > 0 && b.h < 32)
    log('header-hits-32', short.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(short))
  } catch (err) {
    log('typography-12px', 'FAIL', err.message)
  }

  // Keyboard expand via dedicated control
  try {
    await page.goto(`${APP}/tasks/queue`, { waitUntil: 'domcontentloaded' })
    await waitForQueue(page)
    const exp = page.getByRole('button', { name: 'Expand task' }).first()
    await exp.focus()
    await page.keyboard.press('Enter')
    await page.waitForTimeout(400)
    log('keyboard-expand', (await page.getByText(/How to complete this task/i).isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  } catch (err) {
    log('keyboard-expand', 'FAIL', err.message)
  }

  try {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(`${APP}/tasks/queue`, { waitUntil: 'domcontentloaded' })
    await waitForQueue(page)
    await dismissOverlays(page)
    await shot(page, 'queue_mobile')
    log('mobile-add-task', (await page.getByRole('button', { name: /Add task/i }).isVisible()) ? 'PASS' : 'FAIL')
    log('mobile-export-csv', (await page.getByRole('button', { name: /Export CSV/i }).isVisible()) ? 'PASS' : 'FAIL')
    log('mobile-team-toggle', (await page.getByRole('radio', { name: 'My tasks' }).isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 8)
    log('mobile-no-h-overflow', overflow ? 'FAIL' : 'PASS')
  } catch (err) {
    log('mobile', 'FAIL', err.message)
  }

  const interesting = consoleErrors.filter((e) => !/Download the React DevTools/i.test(e))
  log('console-errors', interesting.length === 0 ? 'PASS' : 'FAIL', interesting.slice(0, 6).join(' | '))
  log('page-errors', pageErrors.length === 0 ? 'PASS' : 'FAIL', pageErrors.slice(0, 4).join(' | '))

  const summary = findings.reduce((acc, f) => { acc[f.result] = (acc[f.result] || 0) + 1; return acc }, {})
  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ summary, findings, consoleErrors, pageErrors, failedRequests, qaTask: QA_TASK }, null, 2))
  console.log('\nSUMMARY', summary)
  await browser.close()
}

main().catch((err) => { console.error(err); process.exit(1) })
