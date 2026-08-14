/**
 * Local Chrome QA for Intelligence › AI Suggestions.
 * Headed Google Chrome against http://localhost:5173
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const PASS = process.env.QA_PASS || 'first'
const OUT = path.join(__dirname, `artifacts_2026-08-13_${PASS}`)
mkdirSync(OUT, { recursive: true })

const EMAIL = 'shyna.elene@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://localhost:5173'

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let lastGrouped = null
let lastBriefing = null
let lastDismissed = null
let lastAccept = null
let lastSnooze = null
let lastDismiss = null
let lastRestore = null
let lastGenerate = null
let shotIdx = 0

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 360) : ''}`)
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
  const labels = [
    /Skip tour/i, /Skip for now/i, /^Skip$/i, /Got it/i, /Not now/i,
    /Maybe later/i, /Continue to (app|dashboard)/i, /Go to Dashboard/i,
  ]
  for (const name of labels) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 400 }).catch(() => false)) {
      await btn.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(200)
    }
    const link = page.getByRole('link', { name }).first()
    if (await link.isVisible({ timeout: 200 }).catch(() => false)) {
      await link.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(200)
    }
  }
  await page.keyboard.press('Escape').catch(() => {})
}

async function waitForPage(page) {
  await page.getByRole('heading', { name: /AI Suggestions/i }).first().waitFor({ timeout: 45000 })
  await page.waitForFunction(
    () => {
      const t = document.body?.innerText || ''
      if (/Couldn't load AI suggestions|Suggestions are unavailable/i.test(t)) return true
      if (/Loading/.test(t) && /AI Suggestions/.test(t) && !/need attention|on top of everything|No active suggestions|No suggestions match|Intelligence summary/i.test(t)) return false
      return (
        /need attention/i.test(t)
        || /on top of everything/i.test(t)
        || /No active suggestions/i.test(t)
        || /Intelligence summary/i.test(t)
        || /No suggestions match/i.test(t)
      )
    },
    { timeout: 60000 },
  )
  await page.waitForTimeout(600)
}

function flatten(grouped) {
  return (grouped?.groups || []).flatMap((g) => g.items || [])
}

async function measureBelow12(page) {
  return page.evaluate(() => {
    const out = []
    const walk = (el) => {
      if (!el || el.nodeType !== 1) return
      const style = getComputedStyle(el)
      const size = parseFloat(style.fontSize)
      const text = (el.childNodes && [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join('') || '').trim()
      if (text && size > 0 && size < 12) {
        out.push({ text: text.slice(0, 80), size: Math.round(size * 10) / 10, tag: el.tagName })
      }
      for (const child of el.children) walk(child)
    }
    const main = document.querySelector('main') || document.body
    walk(main)
    return out.slice(0, 40)
  })
}

async function nestedButtonCount(page) {
  return page.evaluate(() => {
    const buttons = [...document.querySelectorAll('button, [role="button"]')]
    let nested = 0
    for (const b of buttons) {
      if (b.querySelector('button, [role="button"], a[href]')) nested += 1
    }
    return { total: buttons.length, nested }
  })
}

async function hitTargets(page) {
  return page.evaluate(() => {
    const pick = (sel) => {
      const el = document.querySelector(sel)
      if (!el) return null
      const r = el.getBoundingClientRect()
      return { w: Math.round(r.width), h: Math.round(r.height), text: (el.innerText || '').slice(0, 40) }
    }
    const pageHeader = [...document.querySelectorAll('header')].find((h) => /Export CSV|Act on all/i.test(h.innerText || ''))
    if (!pageHeader) return { refresh: [] }
    return {
      refresh: [...pageHeader.querySelectorAll('button')].map((el) => {
        const r = el.getBoundingClientRect()
        return { w: Math.round(r.width), h: Math.round(r.height), text: (el.innerText || el.getAttribute('aria-label') || '').slice(0, 40), visible: r.height > 0 }
      }),
    }
  })
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
      const url = res.url()
      if (!url.includes('/api/v1/ai/suggestions')) return
      if (!res.ok()) {
        failedRequests.push(`${res.status()} ${res.request().method()} ${url}`)
        return
      }
      const json = await res.json().catch(() => null)
      if (!json) return
      if (url.includes('/suggestions/grouped')) lastGrouped = json
      else if (url.includes('/suggestions/briefing')) lastBriefing = json
      else if (url.includes('/suggestions/generate')) lastGenerate = json
      else if (url.includes('/act-all-high-confidence')) lastAccept = json
      else if (url.includes('/accept')) lastAccept = json
      else if (url.includes('/snooze')) lastSnooze = json
      else if (url.includes('/restore')) lastRestore = json
      else if (url.includes('/dismiss')) lastDismiss = json
      else if (url.includes('status=dismissed')) lastDismissed = json
    } catch { /* ignore */ }
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

  // Sidebar nav
  try {
    const nav = page.getByRole('link', { name: /AI Suggestions/i }).first()
    await nav.waitFor({ timeout: 8000 })
    await nav.click()
    await page.waitForURL(/\/ai-suggestions/, { timeout: 15000 })
    log('nav-sidebar', 'PASS', page.url())
  } catch (err) {
    log('nav-sidebar', 'FAIL', err.message)
    await page.goto(`${APP}/ai-suggestions`, { waitUntil: 'domcontentloaded', timeout: 20000 })
  }

  try {
    await waitForPage(page)
    log('page-load', 'PASS', page.url())
  } catch (err) {
    await shot(page, 'load_timeout')
    await dumpText(page, 'load_timeout')
    log('page-load', 'FAIL', err.message)
  }
  await dismissOverlays(page)
  await shot(page, 'desktop')
  const body = await dumpText(page, 'desktop')
  writeFileSync(path.join(OUT, 'grouped_api.json'), JSON.stringify(lastGrouped, null, 2))
  writeFileSync(path.join(OUT, 'briefing_api.json'), JSON.stringify(lastBriefing, null, 2))

  const items = flatten(lastGrouped)
  log('api-grouped', lastGrouped ? 'PASS' : 'FAIL', `total=${lastGrouped?.total} groups=${(lastGrouped?.groups || []).map((g) => `${g.category}:${g.count}`).join(',')}`)
  log('api-briefing', lastBriefing ? 'PASS' : 'FAIL', JSON.stringify(lastBriefing?.counts || {}))

  // Chrome
  const crumb = page.getByRole('navigation', { name: 'Breadcrumb' })
  log('chrome-breadcrumb', (await crumb.isVisible().catch(() => false)) && (await crumb.innerText()).includes('Intelligence') ? 'PASS' : 'FAIL')
  log('chrome-h1', (await page.getByRole('heading', { name: /AI Suggestions/i }).first().isVisible()) ? 'PASS' : 'FAIL')
  log('chrome-refresh', (await page.getByRole('button', { name: /Refresh/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  const actAll = page.getByRole('button', { name: /Act on all/i }).first()
  log('chrome-act-all', (await actAll.isVisible().catch(() => false)) ? 'PASS' : 'FAIL', await actAll.innerText().catch(() => ''))
  log('chrome-export', (await page.getByRole('button', { name: /Export/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  log('chrome-search', (await page.getByRole('searchbox').first().isVisible().catch(() => false)) || (await page.getByPlaceholder(/search/i).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')

  // Briefing
  log('briefing-kicker', /Intelligence summary/i.test(body) ? 'PASS' : 'FAIL')
  log('briefing-headline', lastBriefing?.headline && body.includes(lastBriefing.headline.slice(0, 24)) ? 'PASS' : 'FAIL', lastBriefing?.headline)
  log('briefing-plan', (await page.getByRole('button', { name: /Draft action plan/i }).isVisible()) ? 'PASS' : 'FAIL')

  // Stats
  log('stats-new', /New suggestions/i.test(body) ? 'PASS' : 'FAIL')
  log('stats-critical', /Critical alerts/i.test(body) ? 'PASS' : 'FAIL')
  log('stats-acted', /Acted on today/i.test(body) ? 'PASS' : 'FAIL')
  log('stats-snoozed', /Snoozed/i.test(body) ? 'PASS' : 'FAIL')

  // Collision: topbar Critical vs page Critical alerts
  try {
    const critBtns = page.getByRole('button', { name: /Critical/i })
    const n = await critBtns.count()
    const labels = []
    for (let i = 0; i < n; i++) {
      const el = critBtns.nth(i)
      labels.push({
        text: (await el.innerText().catch(() => '')).slice(0, 60),
        aria: await el.getAttribute('aria-label'),
      })
    }
    const pageCrit = await page.getByRole('button', { name: /\d+ Critical alerts/i }).count()
    log('a11y-critical-collision', pageCrit === 1 ? 'PASS' : 'FAIL', JSON.stringify({ count: n, pageCrit, labels }))
  } catch (err) {
    log('a11y-critical-collision', 'FAIL', err.message)
  }

  // Click Critical alerts — must stay on page and filter
  try {
    const before = page.url()
    await page.getByRole('button', { name: /Critical alerts/i }).click({ timeout: 3000 })
    await page.waitForTimeout(400)
    const after = page.url()
    const stillHere = after.includes('/ai-suggestions')
    log('stats-critical-click', stillHere ? 'PASS' : 'FAIL', `${before} → ${after}`)
    log('url-sync-category', /category=critical|category=risk/.test(after) ? 'PASS' : 'FAIL', after)
  } catch (err) {
    log('stats-critical-click', 'FAIL', err.message)
    log('url-sync-category', 'FAIL', err.message)
  }

  // Click Acted on today / Snoozed — should filter, not be dead
  try {
    const acted = page.getByRole('button', { name: /Acted on today/i })
    const snoozed = page.getByRole('button', { name: /Snoozed/i })
    const actedDisabled = await acted.isDisabled().catch(() => true)
    const snoozedDisabled = await snoozed.isDisabled().catch(() => true)
    log('stats-acted-clickable', actedDisabled ? 'FAIL' : 'PASS', `disabled=${actedDisabled}`)
    log('stats-snoozed-clickable', snoozedDisabled ? 'FAIL' : 'PASS', `disabled=${snoozedDisabled}`)
    await snoozed.click()
    await page.waitForTimeout(500)
    log('url-sync-snoozed', /view=snoozed/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    await page.getByRole('button', { name: /\d+ New suggestions/i }).click()
    await page.waitForTimeout(400)
  } catch (err) {
    log('stats-acted-clickable', 'FAIL', err.message)
  }

  try {
    const search = page.getByLabel('Search suggestions')
    const sample = flatten(lastGrouped)[0]
    const needle = (sample?.context_label || sample?.title || 'contact').split(/[\s,—]+/).find((w) => w.length >= 5) || 'contact'
    await search.fill(needle)
    await page.waitForTimeout(300)
    const hitCount = await page.locator('[data-testid="suggestion-card"]').count()
    log('search-hit', hitCount > 0 ? 'PASS' : 'FAIL', `needle=${needle} cards=${hitCount}`)
    await search.fill('zzznomatchxyz999')
    await page.waitForTimeout(300)
    log('search-empty', /No suggestions match/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
    await search.fill('')
    await page.waitForTimeout(200)
  } catch (err) {
    log('search-hit', 'FAIL', err.message)
  }

  try {
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 10000 }),
      page.getByRole('button', { name: /Export CSV/i }).click(),
    ])
    const name = download.suggestedFilename()
    const dest = path.join(OUT, name || 'ai-suggestions.csv')
    await download.saveAs(dest)
    log('export-csv', /ai-suggestions/i.test(name) ? 'PASS' : 'FAIL', name)
  } catch (err) {
    log('export-csv', 'FAIL', err.message)
  }

  // Reset to All
  const allPill = page.getByRole('button', { name: /^All\b/ }).first()
  if (await allPill.isVisible().catch(() => false)) {
    await allPill.click().catch(() => {})
    await page.waitForTimeout(300)
  }

  // Category pills
  const cats = (lastGrouped?.groups || []).map((g) => g.category)
  log('filters-pills', cats.length > 0 || items.length === 0 ? 'PASS' : 'FAIL', cats.join(','))
  if (cats.length > 0) {
    try {
      const firstCat = lastGrouped.groups[0]
      const pill = page.getByRole('button', { name: new RegExp(firstCat.category === 'risk' ? 'Risk' : firstCat.category, 'i') }).first()
      await pill.click()
      await page.waitForTimeout(300)
      const other = lastGrouped.groups.find((g) => g.category !== firstCat.category)
      const cardTitles = await page.locator('[data-testid="suggestion-card"]').allInnerTexts()
      const leaked = other && other.items[0] && cardTitles.some((t) => t.includes(other.items[0].title))
      log('filters-category-switch', leaked ? 'FAIL' : 'PASS', `active=${firstCat.category} leaked=${leaked} cards=${cardTitles.length}`)
      await page.getByRole('button', { name: /^All\b/ }).first().click()
      await page.waitForTimeout(200)
    } catch (err) {
      log('filters-category-switch', 'FAIL', err.message)
    }
  }

  log('show-dismissed', (await page.getByTestId('toggle-dismissed').isVisible().catch(() => false)) || /Show dismissed|Hide dismissed/i.test(body) ? 'PASS' : 'FAIL')

  // Expand first card
  if (items.length > 0) {
    try {
      const title = items[0].title
      const expandBtn = page.getByRole('button', { name: new RegExp(`^Expand ${title.slice(0, 24).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`) }).first()
      await expandBtn.click({ timeout: 5000 })
      await page.waitForTimeout(400)
      const expanded = await page.locator('body').innerText()
      log('card-expand', /Why AI flagged this/i.test(expanded) ? 'PASS' : 'FAIL')
      log('card-reason', items[0].reason ? (/Why AI flagged this/i.test(expanded) ? 'PASS' : 'FAIL') : 'SKIP')
      log('card-draft', items[0].draft_body ? (/Drafted (email|message|caption)/i.test(expanded) ? 'PASS' : 'FAIL') : 'SKIP')
      log('card-snooze', (await page.getByRole('button', { name: /Snooze/i }).first().isVisible()) ? 'PASS' : 'FAIL')
      log('card-dismiss', (await page.getByRole('button', { name: /^Dismiss$/i }).first().isVisible()) ? 'PASS' : 'FAIL')
      const primary = page.getByRole('button', { name: /Send Email|Send Text|Add Task|Add Reminder|Add to Template|Copy|Mark Done/i }).first()
      log('card-primary', (await primary.isVisible().catch(() => false)) ? 'PASS' : 'FAIL', await primary.innerText().catch(() => ''))
      log('card-scope-radio', /This transaction|All future/i.test(expanded) ? 'PASS' : (items[0].action_kind === 'add_task' ? 'FAIL' : 'SKIP'))
      log('card-edit-accept', /Edit task name|Due date|Edit & Accept/i.test(expanded) ? 'PASS' : (items[0].suggested_action?.task ? 'FAIL' : 'SKIP'))
      log('card-view-deal', (await page.getByRole('link', { name: /View deal/i }).first().isVisible().catch(() => false)) || (items[0].context_label && await page.getByRole('link', { name: items[0].context_label }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
      await shot(page, 'card_expanded')
    } catch (err) {
      log('card-expand', 'FAIL', err.message)
    }
  } else {
    log('card-expand', 'SKIP', 'no pending suggestions')
  }

  // Snooze durations
  try {
    const snoozeBtn = page.getByRole('button', { name: /^Snooze$/i }).first()
    if (await snoozeBtn.isVisible().catch(() => false)) {
      await snoozeBtn.click()
      await page.waitForTimeout(300)
      const picker = await page.locator('body').innerText()
      log('snooze-2h', /2 hours/i.test(picker) ? 'PASS' : 'FAIL')
      log('snooze-tomorrow', /Tomorrow/i.test(picker) ? 'PASS' : 'FAIL')
      log('snooze-1week', /1 week/i.test(picker) ? 'PASS' : 'FAIL')
      log('snooze-2weeks', /2 week/i.test(picker) ? 'PASS' : 'FAIL')
      await page.keyboard.press('Escape').catch(() => {})
      await page.waitForTimeout(200)
    } else {
      log('snooze-2weeks', 'SKIP', 'no snooze button')
    }
  } catch (err) {
    log('snooze-2weeks', 'FAIL', err.message)
  }

  // Dismiss + restore (use last pending item to avoid wrecking first card if we still need it)
  const pendingForDismiss = flatten(lastGrouped)
  if (pendingForDismiss.length > 0) {
    try {
      lastDismiss = null
      lastRestore = null
      const target = pendingForDismiss[pendingForDismiss.length - 1]
      const card = page.locator(`[data-suggestion-id="${target.id}"]`)
      await card.getByRole('button', { name: new RegExp(`^Expand `) }).first().click({ timeout: 4000 }).catch(() => {})
      await page.waitForTimeout(300)
      await card.getByTestId('dismiss-suggestion').click({ timeout: 4000 })
      const started = Date.now()
      while (lastDismiss == null && Date.now() - started < 8000) {
        await page.waitForTimeout(250)
      }
      log('dismiss-action', lastDismiss?.status === 'dismissed' ? 'PASS' : 'FAIL', lastDismiss?.status)
      const undoVisible = await page.getByRole('button', { name: /^Undo$/i }).first().isVisible({ timeout: 5000 }).catch(() => false)
      log('dismiss-undo', undoVisible ? 'PASS' : 'FAIL')

      const toggle = page.getByTestId('toggle-dismissed')
      if (await toggle.isVisible().catch(() => false)) {
        const t = await toggle.innerText()
        if (/Show dismissed/i.test(t)) await toggle.click()
        await page.waitForTimeout(700)
      }
      const restore = page.locator('[data-testid="dismissed-item"]').filter({ hasText: target.title.slice(0, 24) }).getByTestId('restore-suggestion')
      const restoreBtn = (await restore.count()) > 0 ? restore.first() : page.getByTestId('restore-suggestion').first()
      log('restore-visible', (await restoreBtn.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
      if (await restoreBtn.isVisible().catch(() => false)) {
        lastRestore = null
        await restoreBtn.click()
        const r0 = Date.now()
        while (lastRestore == null && Date.now() - r0 < 8000) {
          await page.waitForTimeout(250)
        }
        log('restore-action', lastRestore?.status === 'pending' || /restored/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL', lastRestore?.status)
      }
    } catch (err) {
      log('dismiss-action', 'FAIL', err.message)
    }
  } else {
    log('dismiss-action', 'SKIP', 'no pending')
  }

  // Accept a task-kind suggestion if present (create unique observable side effect)
  const fresh = flatten(lastGrouped)
  const taskSug = fresh.find((s) => ['add_task', 'add_seller_call_task', 'schedule_message'].includes(s.action_kind))
  if (taskSug) {
    try {
      await page.getByRole('button', { name: /^All\b/ }).first().click().catch(() => {})
      await page.waitForTimeout(200)
      await page.getByText(taskSug.title, { exact: false }).first().click()
      await page.waitForTimeout(400)
      const acceptBtn = page.getByRole('button', { name: /Add Task|Add Reminder|Confirm:/i }).first()
      await acceptBtn.click({ timeout: 4000 })
      await page.waitForTimeout(1200)
      const afterText = await page.locator('body').innerText()
      if (/Confirm:/i.test(await acceptBtn.innerText().catch(() => '')) || lastAccept?.status === 'requires_confirmation') {
        await acceptBtn.click({ timeout: 4000 }).catch(() => {})
        await page.waitForTimeout(1200)
      }
      log('accept-task', lastAccept?.status === 'accepted' || /Task added|Reminder task|Done/i.test(afterText) ? 'PASS' : 'FAIL', JSON.stringify({ status: lastAccept?.status, message: lastAccept?.message }))
      log('accept-undo', (await page.getByRole('button', { name: /Undo/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    } catch (err) {
      log('accept-task', 'FAIL', err.message)
    }
  } else {
    log('accept-task', 'SKIP', 'no add_task suggestion')
  }

  // Send Email path
  const emailSug = flatten(lastGrouped).find((s) => s.action_kind === 'send_email')
  if (emailSug && lastAccept?.suggestion?.id !== emailSug.id) {
    try {
      await page.locator(`[data-suggestion-id="${emailSug.id}"]`).getByRole('button', { name: /^Expand / }).first().click()
      await page.waitForTimeout(400)
      const send = page.getByRole('button', { name: /Send Email|Confirm: Send Email/i }).first()
      await send.click({ timeout: 4000 })
      await page.waitForTimeout(1200)
      if (/Confirm:/i.test(await send.innerText().catch(() => ''))) {
        await send.click({ timeout: 4000 }).catch(() => {})
        await page.waitForTimeout(1200)
      }
      const t = await page.locator('body').innerText()
      log('accept-email', lastAccept?.draft_log_id || /Draft ready/i.test(t) ? 'PASS' : 'FAIL', JSON.stringify({ status: lastAccept?.status, draft: lastAccept?.draft_log_id }))
    } catch (err) {
      log('accept-email', 'FAIL', err.message)
    }
  } else {
    log('accept-email', emailSug ? 'SKIP' : 'SKIP', 'no unused send_email or already accepted')
  }

  // View deal
  try {
    await page.goto(`${APP}/ai-suggestions`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    const withTx = flatten(lastGrouped).find((s) => s.transaction_id)
    if (withTx) {
      const href = await page.getByRole('link', { name: withTx.context_label || /View deal/i }).first().getAttribute('href')
      await page.getByRole('link', { name: withTx.context_label || /View deal/i }).first().click()
      await page.waitForTimeout(1500)
      const dest = page.url()
      const ok = dest.includes(withTx.transaction_id) || dest.includes('highlight=') || dest.includes('/transactions/')
      log('view-deal', ok && !dest.includes('/ai-suggestions') ? 'PASS' : 'FAIL', `${href} → ${dest}`)
      await page.goBack({ waitUntil: 'domcontentloaded' }).catch(() => {})
      await waitForPage(page).catch(() => {})
    } else {
      log('view-deal', 'SKIP', 'no transaction_id')
    }
  } catch (err) {
    log('view-deal', 'FAIL', err.message)
  }

  // Bulk act dialog (cancel — do not actually bulk-apply)
  try {
    await page.goto(`${APP}/ai-suggestions`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    await page.getByRole('button', { name: /Act on all/i }).click()
    await page.waitForTimeout(400)
    const dlg = await page.locator('body').innerText()
    const hasDialog = /Act on all high-confidence|safe to auto-apply|never auto-sent/i.test(dlg)
    log('bulk-dialog', hasDialog ? 'PASS' : 'FAIL')
    log('bulk-no-window-confirm', hasDialog ? 'PASS' : 'FAIL')
    const cancel = page.getByRole('button', { name: /Cancel|Close/i }).first()
    if (await cancel.isVisible().catch(() => false)) await cancel.click()
    else await page.keyboard.press('Escape')
    await page.waitForTimeout(300)
  } catch (err) {
    log('bulk-dialog', 'FAIL', err.message)
  }

  // Refresh
  try {
    lastGenerate = null
    await page.getByRole('button', { name: /Refresh/i }).click()
    const started = Date.now()
    while (lastGenerate == null && Date.now() - started < 25000) {
      await page.waitForTimeout(400)
    }
    log('refresh', lastGenerate != null || /caught up|new suggestion/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL', JSON.stringify({ generated: lastGenerate?.generated, ms: Date.now() - started }))
    await page.waitForTimeout(800)
    const afterRefresh = flatten(lastGrouped)
    const titles = afterRefresh.map((s) => `${s.title} ${s.timing_label || ''}`).join('\n')
    log('copy-never-contacted', /no logged contact yet/i.test(titles) ? 'FAIL' : 'PASS')
    log('copy-plural-days', /day\(s\)|\b1 days\b/.test(titles) ? 'FAIL' : 'PASS', titles.split('\n').filter((t) => /day\(s\)|\b1 days\b/.test(t)).slice(0, 4).join(' | '))
  } catch (err) {
    log('refresh', 'FAIL', err.message)
  }

  // Deep link
  try {
    const sample = flatten(lastGrouped)[0]
    if (sample) {
      await page.goto(`${APP}/ai-suggestions?suggestion=${sample.id}`, { waitUntil: 'domcontentloaded' })
      await waitForPage(page)
      const t = await page.locator('body').innerText()
      const expanded = /Why AI flagged this/i.test(t)
      log('deeplink-suggestion', expanded ? 'PASS' : 'FAIL')
    } else {
      log('deeplink-suggestion', 'SKIP', 'no items')
    }
  } catch (err) {
    log('deeplink-suggestion', 'FAIL', err.message)
  }

  // Keyboard expand
  try {
    await page.goto(`${APP}/ai-suggestions`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    const firstCard = page.locator('article').first()
    if (await firstCard.isVisible().catch(() => false)) {
      await firstCard.locator('button').first().focus()
      await page.keyboard.press('Enter')
      await page.waitForTimeout(400)
      log('keyboard-expand', /Why AI flagged this/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
    } else {
      log('keyboard-expand', 'SKIP', 'no cards')
    }
  } catch (err) {
    log('keyboard-expand', 'FAIL', err.message)
  }

  // Typography + nested interactive + hit targets
  try {
    await page.goto(`${APP}/ai-suggestions`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    const small = await measureBelow12(page)
    writeFileSync(path.join(OUT, 'typography_below_12.json'), JSON.stringify(small, null, 2))
    log('typography-12px', small.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(small.slice(0, 12)))
    const nested = await nestedButtonCount(page)
    log('nested-interactive', nested.nested === 0 ? 'PASS' : 'FAIL', JSON.stringify(nested))
    const hits = await hitTargets(page)
    writeFileSync(path.join(OUT, 'hit_targets.json'), JSON.stringify(hits, null, 2))
    const short = (hits.refresh || []).filter((b) => b.visible && b.h > 0 && b.h < 32)
    log('hit-targets-32', short.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(short))
  } catch (err) {
    log('typography-12px', 'FAIL', err.message)
  }

  // Console
  const realConsole = consoleErrors.filter((e) => !/Download the React DevTools|favicon/i.test(e))
  log('console-errors', realConsole.length === 0 && pageErrors.length === 0 ? 'PASS' : 'FAIL', JSON.stringify({ console: realConsole.slice(0, 8), page: pageErrors.slice(0, 8), failed: failedRequests.slice(0, 8) }))

  // Mobile 390
  try {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(`${APP}/ai-suggestions`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    await shot(page, 'mobile_390')
    await dumpText(page, 'mobile_390')
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
    log('mobile-overflow', overflow ? 'FAIL' : 'PASS')
    const actName = await page.getByRole('button', { name: /Act on all/i }).first().isVisible().catch(() => false)
    const refreshName = await page.getByRole('button', { name: /Refresh/i }).first().isVisible().catch(() => false)
    log('mobile-act-all-name', actName ? 'PASS' : 'FAIL')
    log('mobile-refresh', refreshName ? 'PASS' : 'FAIL')
    const exportName = await page.getByRole('button', { name: /Export/i }).first().isVisible().catch(() => false)
    log('mobile-export', exportName ? 'PASS' : 'FAIL')
  } catch (err) {
    log('mobile-overflow', 'FAIL', err.message)
  }

  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({
    findings, consoleErrors: realConsole, pageErrors, failedRequests,
    groupedTotal: lastGrouped?.total, briefing: lastBriefing?.counts,
  }, null, 2))

  const pass = findings.filter((f) => f.result === 'PASS').length
  const fail = findings.filter((f) => f.result === 'FAIL').length
  const skip = findings.filter((f) => f.result === 'SKIP').length
  console.log(`\n=== ${PASS} ${pass} pass / ${fail} fail / ${skip} skip ===`)
  console.log(`artifacts: ${OUT}`)
  await browser.close()
  process.exit(fail > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
