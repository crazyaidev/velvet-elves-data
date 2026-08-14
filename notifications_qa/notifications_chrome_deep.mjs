/**
 * Deeper Chrome pass: notification click-through, tabs, expand, drafts, console.
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
  const OUT = path.join(__dirname, 'artifacts_2026-08-13_deep2')
mkdirSync(OUT, { recursive: true })

const EMAIL = 'shyna.elene@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://localhost:5173'

const findings = []
const consoleErrors = []
const pageErrors = []
let shotIdx = 0
let lastPending = null

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 5000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 360) : ''}`)
}

async function shot(page, name) {
  shotIdx += 1
  const file = path.join(OUT, `${String(shotIdx).padStart(2, '0')}_${name}.png`)
  try {
    await page.screenshot({ path: file, fullPage: false })
  } catch (err) {
    console.log('shot fail', name, err.message)
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

async function openBell(page) {
  const bell = page.getByRole('button', { name: /Notifications/i }).first()
  await bell.click()
  const panel = page.getByRole('dialog', { name: 'Notifications' })
  await panel.waitFor({ state: 'visible', timeout: 8000 })
  await page.waitForFunction(
    () => {
      const t = document.querySelector('[role="dialog"][aria-label="Notifications"]')?.textContent || ''
      return t.length > 40 && !/Loading…/.test(t)
    },
    { timeout: 15000 },
  )
  await page.waitForTimeout(250)
  return panel
}

async function main() {
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: false,
  })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await context.newPage()
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()) })
  page.on('pageerror', (err) => pageErrors.push(err.message))
  page.on('response', async (res) => {
    if (res.url().includes('/api/v1/notifications/pending') && res.ok()) {
      try { lastPending = await res.json() } catch { /* ignore */ }
    }
  })

  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.locator('#login-email').fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 })
  await page.waitForTimeout(1500)
  await dismissOverlays(page)
  await dismissOverlays(page)
  log('login', 'PASS', page.url())

  if (!lastPending) {
    lastPending = await page.evaluate(async () => {
      const token = localStorage.getItem('velvet_elves_token')
      const res = await fetch('http://localhost:8000/api/v1/notifications/pending', {
        headers: { Authorization: `Bearer ${token}` },
      })
      return res.ok ? res.json() : null
    })
  }
  writeFileSync(path.join(OUT, 'pending.json'), JSON.stringify(lastPending, null, 2))
  const firstOverdue = lastPending?.overdue?.[0]
  log('api', lastPending ? 'PASS' : 'FAIL', `overdue=${lastPending?.overdue?.length} drafts=${lastPending?.ai_drafts_pending}`)

  const panel = await openBell(page)
  await shot(page, 'panel')
  writeFileSync(path.join(OUT, 'panel.txt'), await panel.innerText())

  // Measure tabs vs viewport
  const tabBoxes = await panel.evaluate(() => {
    const dlg = document.querySelector('[role="dialog"][aria-label="Notifications"]')
    const dlgBox = dlg?.getBoundingClientRect()
    const tabs = [...(dlg?.querySelectorAll('[role="tab"]') || [])].map((el) => {
      const r = el.getBoundingClientRect()
      return {
        name: el.textContent.trim().replace(/\s+/g, ' '),
        x: Math.round(r.x),
        y: Math.round(r.y),
        w: Math.round(r.width),
        h: Math.round(r.height),
        inDlg: !!dlgBox && r.left >= dlgBox.left - 2 && r.right <= dlgBox.right + 2,
        inView: r.right <= window.innerWidth && r.left >= 0 && r.bottom <= window.innerHeight && r.top >= 0,
      }
    })
    return {
      dlg: dlgBox && {
        x: Math.round(dlgBox.x),
        y: Math.round(dlgBox.y),
        w: Math.round(dlgBox.width),
        h: Math.round(dlgBox.height),
      },
      tabs,
      vw: window.innerWidth,
      vh: window.innerHeight,
    }
  })
  writeFileSync(path.join(OUT, 'tab_boxes.json'), JSON.stringify(tabBoxes, null, 2))
  const panelOnScreen = tabBoxes.dlg && tabBoxes.dlg.y >= 0 && tabBoxes.dlg.y < tabBoxes.vh - 80
  const allTabsIn = tabBoxes.tabs.every((t) => t.inDlg && t.inView)
  log('panel-on-screen', panelOnScreen ? 'PASS' : 'FAIL', JSON.stringify(tabBoxes.dlg))
  log('tabs-in-viewport', allTabsIn ? 'PASS' : 'FAIL', JSON.stringify(tabBoxes))

  async function clickTab(name) {
    const tab = panel.getByRole('tab', { name: new RegExp(`^${name}`, 'i') })
    await tab.click({ timeout: 5000 })
    await page.waitForTimeout(400)
  }

  try {
    await clickTab('Overdue')
    const after = await panel.innerText()
    log('mouse-click-overdue-tab', /late|Nothing overdue/i.test(after) ? 'PASS' : 'FAIL', after.slice(0, 220))
    await shot(page, 'tab_overdue')
  } catch (err) {
    log('mouse-click-overdue-tab', 'FAIL', err.message)
  }

  try {
    await clickTab('Today')
    const after = await panel.innerText()
    const stillLateDump = (after.match(/\d+d late/gi) || []).length > 8
    log('mouse-click-today-tab', stillLateDump ? 'FAIL' : 'PASS', after.slice(0, 240))
    await shot(page, 'tab_today')
  } catch (err) {
    log('mouse-click-today-tab', 'FAIL', err.message)
  }

  try {
    await clickTab('All')
  } catch { /* ignore */ }

  try {
    const dealBtn = panel.locator('ul button').first()
    const dealLabel = (await dealBtn.innerText()).slice(0, 200)
    await dealBtn.click({ timeout: 8000 })
    await page.waitForURL(/\/transactions\/active/, { timeout: 10000 })
    await page.waitForTimeout(1500)
    const url = page.url()
    log('deal-click-url', /\/transactions\/active\?highlight=/.test(url) ? 'PASS' : 'FAIL', `${dealLabel} → ${url}`)

    const taskId = (url.match(/task=([^&]+)/) || [])[1]
    const highlightId = (url.match(/highlight=([^&]+)/) || [])[1]
    if (taskId) {
      await page.locator(`[data-task-id="${taskId}"]`).first().waitFor({ state: 'visible', timeout: 8000 }).catch(() => {})
    }
    const hasCard = await page.locator('[data-task-id]').count().catch(() => 0)
    const taskEl = taskId ? page.locator(`[data-task-id="${taskId}"]`) : null
    const taskVisible = taskEl ? await taskEl.count() : 0
    const taskInView = taskEl && taskVisible
      ? await taskEl.first().evaluate((el) => {
          const r = el.getBoundingClientRect()
          return { top: Math.round(r.top), h: Math.round(r.height), inView: r.top < window.innerHeight && r.bottom > 0 }
        }).catch(() => null)
      : null
    const expanded = await page.locator('body').innerText()
    log(
      'deal-card-expanded',
      /Overdue|Due Today|Upcoming|Add task|Tasks/i.test(expanded) ? 'PASS' : 'FAIL',
      `cards=${hasCard} taskNodes=${taskVisible} ${JSON.stringify(taskInView)}`,
    )
    log(
      'deal-task-highlighted',
      taskVisible > 0 ? 'PASS' : 'FAIL',
      `task=${taskId} highlight=${highlightId} visible=${taskVisible}`,
    )
    await shot(page, 'after_deal_click')
    writeFileSync(path.join(OUT, 'after_deal.txt'), expanded.slice(0, 8000))
  } catch (err) {
    log('deal-click-url', 'FAIL', err.message)
  }

  // AI drafts banner
  try {
    await page.goto(`${APP}/dashboard`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(800)
    await dismissOverlays(page)
    const p2 = await openBell(page)
    const drafts = p2.getByRole('button', { name: /AI draft/i }).first()
    if (await drafts.isVisible().catch(() => false)) {
      await drafts.click({ timeout: 5000 })
      await page.waitForTimeout(1500)
      log('ai-drafts-click', /ai-emails/.test(page.url()) && /outbox|Outbox|draft/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL', page.url())
      await shot(page, 'ai_outbox')
    } else {
      log('ai-drafts-click', 'INFO', 'no drafts banner')
    }
  } catch (err) {
    log('ai-drafts-click', 'FAIL', err.message)
  }

  // Notifications page expand
  try {
    await page.goto(`${APP}/notifications`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('heading', { name: 'Notifications' }).waitFor({ timeout: 15000 })
    await page.waitForTimeout(800)
    await dismissOverlays(page)
    await page.getByRole('button', { name: /Show \d+ tasks/i }).first().waitFor({ state: 'visible', timeout: 15000 })
    const expand = page.getByRole('button', { name: /Show \d+ tasks/i }).first()
    log('page-expand-control', (await expand.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    if (await expand.isVisible().catch(() => false)) {
      await expand.click()
      await page.waitForTimeout(400)
      const t = await page.locator('main').innerText()
      log('page-expand-tasks', /late|Due today|Tomorrow|Soon/i.test(t) ? 'PASS' : 'FAIL', t.slice(0, 300))
      await shot(page, 'page_expanded')
    }
  } catch (err) {
    log('page-expand-control', 'FAIL', err.message)
  }

  try {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(`${APP}/dashboard`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(800)
    await dismissOverlays(page)
    const p3 = await openBell(page)
    const box = await p3.evaluate((el) => {
      const r = el.getBoundingClientRect()
      return {
        x: Math.round(r.x),
        y: Math.round(r.y),
        w: Math.round(r.width),
        h: Math.round(r.height),
        vw: window.innerWidth,
        vh: window.innerHeight,
      }
    })
    writeFileSync(path.join(OUT, 'mobile_box.json'), JSON.stringify(box, null, 2))
    const tabsY = await p3.locator('[role="tab"]').first().evaluate((el) => Math.round(el.getBoundingClientRect().y))
    const ok =
      box.x >= 0 &&
      box.y >= 0 &&
      box.x + box.w <= box.vw &&
      box.y + 80 < box.vh &&
      tabsY >= 0 &&
      tabsY < box.vh
    log('mobile-panel-clamped', ok ? 'PASS' : 'FAIL', JSON.stringify({ ...box, tabsY }))
    await shot(page, 'mobile_panel')
    await page.keyboard.press('Escape')
  } catch (err) {
    log('mobile-panel-clamped', 'FAIL', err.message)
  }

  const interesting = consoleErrors.filter((t) => !/favicon|Download the React DevTools/i.test(t))
  log('page-errors', pageErrors.length === 0 ? 'PASS' : 'FAIL', pageErrors.join(' | '))
  log('console-errors', interesting.length === 0 ? 'PASS' : 'FAIL', interesting.slice(0, 6).join(' | '))

  const pass = findings.filter((f) => f.result === 'PASS').length
  const fail = findings.filter((f) => f.result === 'FAIL').length
  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ pass, fail, findings, consoleErrors: interesting, pageErrors }, null, 2))
  console.log(`\nRESULT ${pass} pass / ${fail} fail → ${OUT}`)
  await browser.close()
  process.exit(fail > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
