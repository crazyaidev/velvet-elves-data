/**
 * Local Chrome QA for the topbar notification bell + /notifications page.
 * Headed Google Chrome against http://localhost:5173 as platform admin.
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
let lastPending = null
let lastSeen = null
let shotIdx = 0

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 6000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 320) : ''}`)
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

function summarizePending(data) {
  if (!data) return null
  const buckets = {
    overdue: data.overdue || [],
    due_today: data.due_today || [],
    day_before: data.day_before || [],
    upcoming: data.upcoming || [],
  }
  const all = Object.values(buckets).flat()
  const txs = new Map()
  const statuses = {}
  for (const n of all) {
    const id = n.transaction_id || 'none'
    if (!txs.has(id)) {
      txs.set(id, {
        address: n.transaction_address,
        status: n.transaction_status,
        overdue: 0,
        due_today: 0,
        day_before: 0,
        upcoming: 0,
      })
    }
    const row = txs.get(id)
    if (n.notification_type === 'past_due' || buckets.overdue.includes(n)) row.overdue += 1
    statuses[n.transaction_status || 'null'] = (statuses[n.transaction_status || 'null'] || 0) + 1
  }
  for (const n of buckets.due_today) {
    const row = txs.get(n.transaction_id)
    if (row) row.due_today += 1
  }
  for (const n of buckets.day_before) {
    const row = txs.get(n.transaction_id)
    if (row) row.day_before += 1
  }
  for (const n of buckets.upcoming) {
    const row = txs.get(n.transaction_id)
    if (row) row.upcoming += 1
  }
  return {
    overdue: buckets.overdue.length,
    due_today: buckets.due_today.length,
    day_before: buckets.day_before.length,
    upcoming: buckets.upcoming.length,
    total_tasks: all.length,
    unique_deals: txs.size,
    statuses,
    ai_drafts_pending: data.ai_drafts_pending,
    ai_drafts_latest_at: data.ai_drafts_latest_at,
    external_communications_today: data.external_communications_today,
    compiled_summary: data.compiled_summary,
    transaction_summaries: (data.transaction_summaries || []).length,
    deals: [...txs.entries()].map(([id, v]) => ({ id, ...v })),
  }
}

async function minFontSize(page, rootSelector) {
  return page.evaluate((sel) => {
    const root = sel ? document.querySelector(sel) : document.body
    if (!root) return { min: null, offenders: [] }
    const nodes = [root, ...root.querySelectorAll('*')]
    let min = 99
    const offenders = []
    for (const el of nodes) {
      if (!(el instanceof HTMLElement)) continue
      const t = (el.innerText || '').trim()
      if (!t) continue
      const cs = getComputedStyle(el)
      if (cs.display === 'none' || cs.visibility === 'hidden') continue
      const size = parseFloat(cs.fontSize)
      if (!Number.isFinite(size)) continue
      if (size < min) min = size
      if (size < 12 && offenders.length < 12) {
        offenders.push({
          tag: el.tagName,
          size: Math.round(size * 10) / 10,
          text: t.slice(0, 80),
        })
      }
    }
    return { min, below12: offenders.length, offenders }
  }, rootSelector)
}

async function hitSize(page, locator) {
  const box = await locator.boundingBox().catch(() => null)
  if (!box) return null
  return { w: Math.round(box.width), h: Math.round(box.height) }
}

async function openBell(page) {
  const bell = page.getByRole('button', { name: /Notifications/i }).first()
  await bell.click()
  const panel = page.getByRole('dialog', { name: 'Notifications' })
  await panel.waitFor({ state: 'visible', timeout: 8000 })
  await panel.getByText(/deals need attention|caught up|Loading/i).first().waitFor({ timeout: 8000 })
  await page.waitForFunction(
    () => {
      const dlg = document.querySelector('[role="dialog"][aria-label="Notifications"]')
      const t = dlg?.textContent || ''
      return t.length > 0 && !/Loading…/.test(t)
    },
    { timeout: 15000 },
  ).catch(() => {})
  await page.waitForTimeout(300)
  return { bell, panel }
}

async function main() {
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: false,
    args: ['--start-maximized'],
  })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    acceptDownloads: true,
  })
  const page = await context.newPage()

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (err) => pageErrors.push(err.message))
  page.on('requestfailed', () => {})
  page.on('response', async (res) => {
    try {
      if (res.url().includes('/api/v1/notifications/pending') && res.ok()) {
        lastPending = await res.json().catch(() => lastPending)
      }
      if (res.url().includes('/api/v1/notifications/last-seen') && res.ok()) {
        lastSeen = await res.json().catch(() => lastSeen)
      }
      if (res.url().includes('/api/v1/notifications/') && res.status() >= 400) {
        failedRequests.push(`${res.status()} ${res.request().method()} ${res.url()}`)
      }
    } catch {
      /* ignore */
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
    await page.waitForTimeout(1500)
    if (!lastPending) {
      lastPending = await page.evaluate(async () => {
        const token = localStorage.getItem('velvet_elves_token')
        const res = await fetch('http://localhost:8000/api/v1/notifications/pending', {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) return null
        return res.json()
      }).catch(() => null)
    }
  } catch (err) {
    log('login', 'FAIL', err.message)
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, consoleErrors, pageErrors }, null, 2))
    await browser.close()
    process.exit(1)
  }

  await page.waitForTimeout(1500)
  const summary = summarizePending(lastPending)
  writeFileSync(path.join(OUT, 'pending_api.json'), JSON.stringify(lastPending, null, 2))
  writeFileSync(path.join(OUT, 'pending_summary.json'), JSON.stringify({ summary, lastSeen }, null, 2))
  log('api-pending', lastPending ? 'PASS' : 'FAIL', JSON.stringify(summary && {
    overdue: summary.overdue,
    due_today: summary.due_today,
    day_before: summary.day_before,
    upcoming: summary.upcoming,
    total_tasks: summary.total_tasks,
    unique_deals: summary.unique_deals,
    statuses: summary.statuses,
    ai_drafts_pending: summary.ai_drafts_pending,
    compiled: (summary.compiled_summary || '').slice(0, 180),
  }))

  const closedish = summary
    ? (summary.statuses.Completed || 0) + (summary.statuses.Closed || 0)
    : 0
  log(
    'api-live-deals-only',
    closedish === 0 ? 'PASS' : 'FAIL',
    `completed+closed task rows=${closedish} statuses=${JSON.stringify(summary?.statuses)}`,
  )
  log(
    'api-compiled-summary',
    summary?.compiled_summary ? 'PASS' : 'FAIL',
    summary?.compiled_summary || 'missing',
  )

  // ── Bell chrome ────────────────────────────────────────────────────────
  const bell = page.getByRole('button', { name: /Notifications/i }).first()
  log('bell-present', (await bell.isVisible()) ? 'PASS' : 'FAIL')
  const bellLabel = await bell.getAttribute('aria-label')
  log('bell-aria', bellLabel ? 'PASS' : 'FAIL', bellLabel)
  const bellBox = await hitSize(page, bell)
  log(
    'bell-hit-target',
    bellBox && bellBox.w >= 40 && bellBox.h >= 40 ? 'PASS' : 'FAIL',
    JSON.stringify(bellBox),
  )

  const badgeText = await page.evaluate(() => {
    const btn = document.querySelector('[data-tour="topbar-notifications"] button')
    if (!btn) return null
    const badge = btn.querySelector('span')
    return badge ? badge.textContent.trim() : ''
  })
  const taskUnread = (summary?.overdue || 0) + (summary?.due_today || 0) + (summary?.day_before || 0)
  const dealUnread = summary?.unique_deals || 0
  log(
    'badge-vs-tasks',
    'INFO',
    `badge="${badgeText}" taskUnread=${taskUnread} dealCount=${dealUnread} drafts=${summary?.ai_drafts_pending}`,
  )
  const badgeNum = badgeText === '99+' ? 99 : Number.parseInt(badgeText || '0', 10) || 0
  log(
    'badge-not-task-dump',
    badgeNum === 0 || badgeNum <= Math.max(dealUnread + (summary?.ai_drafts_pending ? 1 : 0), 12)
      ? 'PASS'
      : 'FAIL',
    `badge=${badgeText} deals=${dealUnread} — a smart bell counts deals (or a small unread set), not every overdue task`,
  )

  await shot(page, 'dashboard_bell')

  // ── Open panel ─────────────────────────────────────────────────────────
  let panel
  try {
    ;({ panel } = await openBell(page))
    log('panel-open', 'PASS')
  } catch (err) {
    log('panel-open', 'FAIL', err.message)
  }
  await shot(page, 'panel_open')
  const panelText = panel ? await panel.innerText() : ''
  writeFileSync(path.join(OUT, 'panel.txt'), panelText)

  log(
    'panel-shows-compiled',
    /transaction\(s\) with/i.test(panelText) || /deals? need/i.test(panelText)
      ? 'PASS'
      : 'FAIL',
    'compiled summary / deal-level headline should appear in the dropdown',
  )

  const panelRows = panel ? await panel.locator('ul button').count() : 0
  log(
    'panel-not-task-dump',
    panelRows > 0 && panelRows <= 20 ? 'PASS' : 'FAIL',
    `dropdown action rows≈${panelRows} vs ${summary?.total_tasks} API tasks — dropdown should group by deal / cap`,
  )

  const typewalk = panel ? await minFontSize(page, '[role="dialog"][aria-label="Notifications"]') : { min: null, offenders: [] }
  log(
    'panel-type-12px',
    typewalk.min != null && typewalk.min >= 12 ? 'PASS' : 'FAIL',
    JSON.stringify(typewalk),
  )

  // Tabs
  if (panel) {
    for (const name of ['All', 'Overdue', 'Today', 'Tomorrow']) {
      const tab = panel.getByRole('tab', { name: new RegExp(`^${name}`, 'i') }).first()
      const vis = await tab.isVisible().catch(() => false)
      log(`tab-${name.toLowerCase()}`, vis ? 'PASS' : 'FAIL')
    }
    try {
      const overdueTab = panel.getByRole('tab', { name: /Overdue/i }).first()
      await overdueTab.evaluate((el) => el.click())
      await page.waitForTimeout(250)
      const overdueText = await panel.innerText()
      log(
        'tab-overdue-filter',
        /Overdue|Nothing overdue|late/i.test(overdueText) ? 'PASS' : 'FAIL',
        overdueText.slice(0, 200),
      )
      await panel.getByRole('tab', { name: /^Today/i }).first().evaluate((el) => el.click())
      await page.waitForTimeout(250)
      const todayText = await panel.innerText()
      log(
        'tab-today-filter',
        /Nothing due today|Today is clear|due today|\bTODAY\b/i.test(todayText) ? 'PASS' : 'FAIL',
        todayText.slice(0, 200),
      )
      await panel.getByRole('tab', { name: /^Tomorrow/i }).first().evaluate((el) => el.click())
      await page.waitForTimeout(250)
      const tmText = await panel.innerText()
      log(
        'tab-tomorrow-filter',
        /tomorrow|wide open|Due tomorrow/i.test(tmText) ? 'PASS' : 'FAIL',
        tmText.slice(0, 200),
      )
      await panel.getByRole('tab', { name: /^All/i }).first().evaluate((el) => el.click())
      await page.waitForTimeout(200)
    } catch (err) {
      log('tab-overdue-filter', 'FAIL', err.message)
    }
  }

  // ESC close
  try {
    await page.keyboard.press('Escape')
    await page.waitForTimeout(200)
    const still = await page.getByRole('dialog', { name: 'Notifications' }).isVisible().catch(() => false)
    log('esc-closes', still ? 'FAIL' : 'PASS')
  } catch (err) {
    log('esc-closes', 'FAIL', err.message)
  }

  // Reopen + outside click
  try {
    await openBell(page)
    await page.mouse.click(20, 200)
    await page.waitForTimeout(250)
    const still = await page.getByRole('dialog', { name: 'Notifications' }).isVisible().catch(() => false)
    log('outside-click-closes', still ? 'FAIL' : 'PASS')
  } catch (err) {
    log('outside-click-closes', 'FAIL', err.message)
  }

  // Account menu should not leave panel floating
  try {
    await openBell(page)
    const account = page.getByRole('button', { name: /account|profile|shyna|admin/i }).first()
    const accountAlt = page.locator('[data-tour="account-menu"]')
    const acc = (await account.isVisible().catch(() => false)) ? account : accountAlt
    await acc.click()
    await page.waitForTimeout(400)
    const settingsItem = page.getByRole('menuitem', { name: /settings/i }).first()
    if (await settingsItem.isVisible().catch(() => false)) {
      await settingsItem.click()
      await page.waitForTimeout(800)
      const floating = await page.getByRole('dialog', { name: 'Notifications' }).isVisible().catch(() => false)
      log('panel-closes-on-navigate', floating ? 'FAIL' : 'PASS', page.url())
    } else {
      await page.keyboard.press('Escape')
      log('panel-closes-on-navigate', 'INFO', 'no settings menuitem')
    }
  } catch (err) {
    log('panel-closes-on-navigate', 'FAIL', err.message)
  }

  await page.goto(`${APP}/dashboard`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(800)
  await dismissOverlays(page)

  // Click-through
  try {
    const { panel: p2 } = await openBell(page)
    const row = p2.locator('ul button').first()
    const rowLabel = (await row.innerText().catch(() => '')).slice(0, 180)
    await row.click({ timeout: 4000 })
    await page.waitForTimeout(1500)
    const url = page.url()
    const landedOnDeal = /\/transactions/.test(url) && /(expand=|highlight=)/.test(url)
    const landedOnQueue = /\/tasks\/queue/.test(url)
    const landedOnAi = /\/ai-emails/.test(url)
    log(
      'click-through',
      landedOnDeal || landedOnQueue || landedOnAi ? 'PASS' : 'FAIL',
      `url=${url} row=${rowLabel}`,
    )
    log(
      'click-path-alias',
      /\/transactions\/(active|pending|closed|all)\?highlight=/.test(url) || landedOnQueue || landedOnAi
        ? 'PASS'
        : 'FAIL',
      url,
    )
    const panelGone = !(await page.getByRole('dialog', { name: 'Notifications' }).isVisible().catch(() => false))
    log('click-closes-panel', panelGone ? 'PASS' : 'FAIL')
    if (landedOnDeal) {
      const body = await page.locator('body').innerText()
      const expandMatch = url.match(/(?:expand|highlight)=([^&]+)/)
      log(
        'click-deal-visible',
        /Active Transactions|Drafts|Closed|All Transactions/i.test(body) ? 'PASS' : 'FAIL',
        `expand=${expandMatch?.[1]}`,
      )
      log(
        'click-uses-highlight-or-expand',
        /(expand=|highlight=)/.test(url) ? 'PASS' : 'FAIL',
        url,
      )
    }
    await shot(page, 'after_click_through')
  } catch (err) {
    log('click-through', 'FAIL', err.message)
  }

  // Mark all as read
  try {
    await page.goto(`${APP}/dashboard`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(800)
    await dismissOverlays(page)
    const { panel: p3 } = await openBell(page)
    const mark = p3.getByRole('button', { name: /Mark all as read|All read/i }).first()
    log('mark-all-present', (await mark.isVisible()) ? 'PASS' : 'FAIL')
    const beforeLabel = await bell.getAttribute('aria-label')
    if (await mark.isEnabled()) {
      await mark.click()
      await page.waitForTimeout(800)
      const toast = /marked as read|Couldn't update/i.test(await page.locator('body').innerText())
      log('mark-all-toast', toast ? 'PASS' : 'FAIL')
      await page.keyboard.press('Escape')
      await page.waitForTimeout(300)
      const afterLabel = await page.getByRole('button', { name: /Notifications/i }).first().getAttribute('aria-label')
      log(
        'mark-all-clears-badge',
        /unread/i.test(afterLabel || '') ? 'FAIL' : 'PASS',
        `before=${beforeLabel} after=${afterLabel}`,
      )
    } else {
      log('mark-all-toast', 'INFO', 'already All read')
      log('mark-all-clears-badge', /unread/i.test(beforeLabel || '') ? 'FAIL' : 'PASS', beforeLabel)
    }
  } catch (err) {
    log('mark-all-clears-badge', 'FAIL', err.message)
  }

  // View all
  try {
    await page.goto(`${APP}/dashboard`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(600)
    await dismissOverlays(page)
    const { panel: p4 } = await openBell(page)
    await p4.getByRole('button', { name: /View all/i }).click()
    await page.waitForTimeout(1000)
    log('view-all-route', /\/notifications/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    const h1 = await page.getByRole('heading', { name: /Notifications/i }).first().isVisible()
    log('notifications-page-h1', h1 ? 'PASS' : 'FAIL')
    await shot(page, 'notifications_page')
    await dumpText(page, 'notifications_page')
    const pageType = await minFontSize(page, 'main')
    log(
      'page-type-12px',
      pageType.min != null && pageType.min >= 12 ? 'PASS' : 'FAIL',
      JSON.stringify(pageType),
    )
    const grouped = /overdue ·|due today|deals? need/i.test(await page.locator('main').innerText().catch(() => ''))
    log(
      'page-grouped-or-headline',
      grouped ? 'PASS' : 'FAIL',
      'full page should group by deal or show a compiled headline, not only a flat task dump',
    )
  } catch (err) {
    log('view-all-route', 'FAIL', err.message)
  }

  // Settings notifications
  try {
    await page.goto(`${APP}/settings/notifications`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(1000)
    await dismissOverlays(page)
    const t = await page.locator('body').innerText()
    log(
      'settings-prefs',
      /Notification preferences|email|in-app|push/i.test(t) ? 'PASS' : 'FAIL',
      t.slice(0, 240),
    )
    log(
      'settings-digest',
      /Morning digest|digest/i.test(t) ? 'PASS' : 'FAIL',
    )
    await shot(page, 'settings_notifications')
  } catch (err) {
    log('settings-prefs', 'FAIL', err.message)
  }

  // Keyboard: bell focus + enter
  try {
    await page.goto(`${APP}/dashboard`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(600)
    await dismissOverlays(page)
    await page.getByRole('button', { name: /Notifications/i }).first().focus()
    await page.keyboard.press('Enter')
    await page.waitForTimeout(400)
    const open = await page.getByRole('dialog', { name: 'Notifications' }).isVisible()
    log('keyboard-open', open ? 'PASS' : 'FAIL')
    await page.keyboard.press('Escape')
  } catch (err) {
    log('keyboard-open', 'FAIL', err.message)
  }

  // Mobile
  try {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(`${APP}/dashboard`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(800)
    await dismissOverlays(page)
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
    log('mobile-no-h-overflow', overflow ? 'FAIL' : 'PASS')
    const mBell = page.getByRole('button', { name: /Notifications/i }).first()
    log('mobile-bell-named', (await mBell.isVisible()) ? 'PASS' : 'FAIL')
    const mBox = await hitSize(page, mBell)
    log('mobile-bell-hit', mBox && mBox.w >= 32 && mBox.h >= 32 ? 'PASS' : 'FAIL', JSON.stringify(mBox))
    await mBell.click()
    await page.waitForTimeout(400)
    const mPanel = page.getByRole('dialog', { name: 'Notifications' })
    log('mobile-panel-open', (await mPanel.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    await shot(page, 'mobile_panel')
    if (await mPanel.isVisible().catch(() => false)) {
      const mType = await minFontSize(page, '[role="dialog"][aria-label="Notifications"]')
      log('mobile-type-12px', mType.min >= 12 ? 'PASS' : 'FAIL', JSON.stringify(mType))
      const panelBox = await mPanel.boundingBox()
      log(
        'mobile-panel-in-viewport',
        panelBox && panelBox.x >= -4 && panelBox.x + panelBox.width <= 394 ? 'PASS' : 'FAIL',
        JSON.stringify(panelBox && { x: Math.round(panelBox.x), w: Math.round(panelBox.width) }),
      )
    }
  } catch (err) {
    log('mobile-panel-open', 'FAIL', err.message)
  }

  const interestingConsole = consoleErrors.filter(
    (t) => !/favicon|Download the React DevTools|Failed to load resource/i.test(t),
  )
  const interestingFailed = failedRequests.filter(
    (t) => /\/notifications\//.test(t) && / [45]\d\d /.test(` ${t}`),
  )
  log('page-errors', pageErrors.length === 0 ? 'PASS' : 'FAIL', pageErrors.join(' | '))
  log('console-errors', interestingConsole.length === 0 ? 'PASS' : 'FAIL', interestingConsole.slice(0, 8).join(' | '))
  log('failed-requests', interestingFailed.length === 0 ? 'PASS' : 'FAIL', interestingFailed.slice(0, 8).join(' | '))

  const pass = findings.filter((f) => f.result === 'PASS').length
  const fail = findings.filter((f) => f.result === 'FAIL').length
  const info = findings.filter((f) => f.result === 'INFO').length
  const report = { pass, fail, info, findings, consoleErrors: interestingConsole, pageErrors, failedRequests, summary }
  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(report, null, 2))
  console.log(`\nRESULT ${pass} pass / ${fail} fail / ${info} info → ${OUT}`)
  await browser.close()
  process.exit(fail > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
