/**
 * Local Chrome QA for Workflow › Needs You.
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
let lastQueue = null
let lastStatus = null
let lastApprove = null
let lastSend = null
let lastRelease = null
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
    if (await link.isVisible({ timeout: 400 }).catch(() => false)) {
      await link.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(200)
    }
  }
  await page.keyboard.press('Escape').catch(() => {})
  const closeChat = page.getByRole('button', { name: /Close AI chat/i })
  if (await closeChat.isVisible({ timeout: 400 }).catch(() => false)) {
    await closeChat.click({ timeout: 2000 }).catch(() => {})
  }
}

async function waitForPage(page) {
  await page.getByRole('heading', { name: /Needs You/i }).first().waitFor({ timeout: 45000 })
  await page.waitForFunction(
    () => {
      const t = document.body?.innerText || ''
      if (/Couldn't load|Failed to load Needs You/i.test(t)) return true
      if (/\bLoading\b/.test(t) && !/\d+\s+waiting/i.test(t)) return false
      return (
        /Nothing needs you right now/i.test(t)
        || /Waiting on you/i.test(t)
        || /\d+\s+waiting/i.test(t)
      )
    },
    { timeout: 90000 },
  )
  await page.waitForTimeout(500)
}

async function measureBelow12(page) {
  return page.evaluate(() => {
    const out = []
    const walk = (el) => {
      if (!el || el.nodeType !== 1) return
      const style = getComputedStyle(el)
      const size = parseFloat(style.fontSize)
      const text = ([...el.childNodes]
        .filter((n) => n.nodeType === 3)
        .map((n) => n.textContent)
        .join('') || '').trim()
      if (text && size > 0 && size < 12) {
        out.push({ text: text.slice(0, 80), size: Math.round(size * 10) / 10, tag: el.tagName })
      }
      for (const child of el.children) walk(child)
    }
    const main = document.querySelector('main') || document.body
    walk(main)
    return out.slice(0, 50)
  })
}

async function nestedButtonCount(page) {
  return page.evaluate(() => {
    const buttons = [...document.querySelectorAll('button, [role="button"]')]
    let nested = 0
    const samples = []
    for (const b of buttons) {
      if (b.querySelector('button, [role="button"], a[href]')) {
        nested += 1
        if (samples.length < 8) {
          samples.push((b.innerText || b.getAttribute('aria-label') || '').slice(0, 80))
        }
      }
    }
    return { total: buttons.length, nested, samples }
  })
}

async function hitTargets(page) {
  return page.evaluate(() => {
    const pageHeader = [...document.querySelectorAll('header')].find((h) => /Needs You/i.test(h.innerText || ''))
    const hero = [...document.querySelectorAll('button')].filter((el) =>
      /Send all ready|Approve all safe|Export/i.test(el.innerText || el.getAttribute('aria-label') || ''),
    )
    const rowActions = [...document.querySelectorAll('button')].filter((el) =>
      /^(Send|Approve|Review|Handle|Give this back)/i.test((el.innerText || '').trim()),
    )
    const map = (el) => {
      const r = el.getBoundingClientRect()
      return {
        w: Math.round(r.width),
        h: Math.round(r.height),
        text: (el.innerText || el.getAttribute('aria-label') || '').slice(0, 48),
        visible: r.height > 0,
      }
    }
    return {
      header: pageHeader ? [...pageHeader.querySelectorAll('button, a')].map(map) : [],
      hero: hero.map(map),
      rowActions: rowActions.slice(0, 12).map(map),
    }
  })
}

function kinds(items) {
  const counts = { ready_draft: 0, action: 0, draft: 0, coverage: 0, task: 0, other: 0 }
  for (const i of items || []) {
    if (counts[i.kind] != null) counts[i.kind] += 1
    else counts.other += 1
  }
  return counts
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
      if (!res.ok() && url.includes('/api/v1/')) {
        failedRequests.push(`${res.status()} ${res.request().method()} ${url}`)
        return
      }
      if (!url.includes('/api/v1/automation/')) return
      const json = await res.json().catch(() => null)
      if (!json) return
      if (url.includes('/needs-you/approve')) lastApprove = json
      else if (url.includes('/needs-you/send')) lastSend = json
      else if (/\/needs-you\/?(\?|$)/.test(url) || url.endsWith('/needs-you')) lastQueue = json
      else if (url.includes('/automation/status')) lastStatus = json
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

  try {
    const nav = page.getByRole('link', { name: /Needs You/i }).first()
    await nav.waitFor({ timeout: 8000 })
    const badge = (await nav.innerText()).replace(/\s+/g, ' ').trim()
    await nav.click()
    await page.waitForURL(/\/needs-you/, { timeout: 15000 })
    log('nav-sidebar', 'PASS', `${page.url()} badge="${badge}"`)
  } catch (err) {
    log('nav-sidebar', 'FAIL', err.message)
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded', timeout: 20000 })
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
  try {
    await waitForPage(page)
  } catch { /* already logged */ }
  await shot(page, 'desktop')
  const body = await dumpText(page, 'desktop')
  writeFileSync(path.join(OUT, 'needs_you_api.json'), JSON.stringify(lastQueue, null, 2))
  writeFileSync(path.join(OUT, 'automation_status.json'), JSON.stringify(lastStatus, null, 2))

  const items = lastQueue?.items || []
  const counts = lastQueue?.counts || {}
  const k = kinds(items)
  log('api-queue', lastQueue ? 'PASS' : 'FAIL', `total=${counts.total} ready=${counts.ready} safe=${counts.safe_approve} kinds=${JSON.stringify(k)}`)

  const stayOnPage = () => /\/needs-you/.test(page.url())

  const crumb = page.getByRole('navigation', { name: 'Breadcrumb' })
  log('chrome-breadcrumb', (await crumb.isVisible().catch(() => false)) && (await crumb.innerText()).includes('Workflow') ? 'PASS' : 'FAIL')
  log('chrome-h1', (await page.getByRole('heading', { name: /Needs You/i }).first().isVisible()) ? 'PASS' : 'FAIL')
  log('chrome-export', (await page.getByRole('button', { name: /Export CSV/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  log('hero-waiting', /Waiting on you|Nothing needs you right now/i.test(body) ? 'PASS' : 'FAIL')
  log('hero-counts-match', !lastQueue ? 'FAIL' : (
    (counts.total === 0 && /Nothing needs you/i.test(body))
    || (counts.total > 0 && new RegExp(`${counts.total}\\s+waiting`).test(body))
  ) ? 'PASS' : 'FAIL', `ui waiting vs api ${counts.total}`)

  const schedulerCopy = /Automation is not running|Automation has stopped/i.test(body)
  if (lastStatus && lastStatus.scheduler_healthy === false) {
    log('scheduler-banner', schedulerCopy ? 'PASS' : 'FAIL', JSON.stringify({ healthy: lastStatus.scheduler_healthy, state: lastStatus.scheduler_state }))
  } else {
    log('scheduler-banner', schedulerCopy ? 'FAIL' : 'PASS', 'healthy — banner should be absent')
  }

  const sendAll = page.getByRole('button', { name: /Send all ready/i }).first()
  const approveAll = page.getByRole('button', { name: /Approve all safe/i }).first()
  log('batch-send-visible', counts.ready > 0
    ? ((await sendAll.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    : ((await sendAll.isVisible().catch(() => false)) ? 'FAIL' : 'PASS'))
  log('batch-approve-visible', counts.safe_approve > 0
    ? ((await approveAll.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    : ((await approveAll.isVisible().catch(() => false)) ? 'FAIL' : 'PASS'))

  const readyTile = page.getByRole('button', { name: /Ready to send/i }).first()
  const approveTile = page.getByRole('button', { name: /To approve/i }).first()
  const reviewTile = page.getByRole('button', { name: /To review/i }).first()
  const decideTile = page.getByRole('button', { name: /To decide/i }).first()
  const handleTile = page.getByRole('button', { name: /To handle/i }).first()

  if (counts.total > 0) {
    log('stat-ready', (await readyTile.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    log('stat-approve', (await approveTile.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    log('stat-review', (await reviewTile.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    log('stat-decide', (await decideTile.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    log('stat-handle', (await handleTile.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')

    const readyAria = await readyTile.getAttribute('aria-label').catch(() => null)
    log('stat-ready-aria', readyAria && /Ready to send items/i.test(readyAria) ? 'PASS' : 'FAIL', readyAria || 'missing')

    try {
      await readyTile.click()
      await page.waitForTimeout(400)
      log('filter-ready-stays', stayOnPage() && (await readyTile.getAttribute('aria-pressed')) === 'true' ? 'PASS' : 'FAIL', page.url())
      log('url-sync-kind', /kind=ready_draft|kind=ready/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
      const filtered = await page.locator('body').innerText()
      if (k.ready_draft === 0) {
        log('filter-ready-empty', /Nothing in this view/i.test(filtered) ? 'PASS' : 'FAIL')
      } else {
        log('filter-ready-empty', /Ready to send/i.test(filtered) ? 'PASS' : 'FAIL')
      }
      await readyTile.click()
      await page.waitForTimeout(250)
    } catch (err) {
      log('filter-ready-stays', 'FAIL', err.message)
    }

    try {
      await handleTile.click()
      await page.waitForTimeout(400)
      log('filter-handle', stayOnPage() ? 'PASS' : 'FAIL', page.url())
      await handleTile.click()
      await page.waitForTimeout(200)
    } catch (err) {
      log('filter-handle', 'FAIL', err.message)
    }
  } else {
    log('stat-ready', 'SKIP', 'empty queue')
  }

  const search = page.getByLabel(/Search items/i)
  const searchFallback = page.getByPlaceholder(/Search items, deals, recipients/i)
  const searchBox = (await search.isVisible().catch(() => false)) ? search : searchFallback
  log('search-a11y-label', (await search.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  if (await searchBox.isVisible().catch(() => false)) {
    await searchBox.fill('zzzx-no-such-item-999')
    await page.waitForTimeout(400)
    log('search-empty', /Nothing in this view/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
    log('url-sync-search', /q=zzzx/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    const clear = page.getByRole('button', { name: /Clear filters/i })
    if (await clear.isVisible().catch(() => false)) await clear.click()
    else await searchBox.fill('')
    await page.waitForTimeout(300)

    const sample = items.find((i) => i.title) || items[0]
    if (sample?.title) {
      const needle = sample.title.slice(0, 18)
      await searchBox.fill(needle)
      await page.waitForTimeout(400)
      log('search-hit', (await page.locator('body').innerText()).includes(needle.slice(0, 10)) ? 'PASS' : 'FAIL', sample.title)
      await searchBox.fill('')
      await page.waitForTimeout(250)
    }
  } else {
    log('search-empty', counts.total === 0 ? 'SKIP' : 'FAIL', 'no search control')
  }

  try {
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 6000 }),
      page.getByRole('button', { name: /Export CSV/i }).click(),
    ])
    const name = download.suggestedFilename()
    const dest = path.join(OUT, name || 'needs-you.csv')
    await download.saveAs(dest)
    log('export-csv', /needs-you/i.test(name) ? 'PASS' : 'FAIL', name)
  } catch (err) {
    log('export-csv', 'FAIL', err.message)
  }

  const expandBtn = page.getByRole('button', { name: /Expand/i }).first()
  log('expand-control', (await expandBtn.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')

  const firstRowTitle = items[0]?.title
  if (firstRowTitle) {
    try {
      const titleHit = page.getByText(firstRowTitle, { exact: false }).first()
      await titleHit.click({ timeout: 4000 })
      await page.waitForTimeout(500)
      const expanded = await page.locator('body').innerText()
      const hasDetail = /Email preview|What happens if you approve|Pick one|Why the AI is asking|Open full review|Open deal/i.test(expanded)
      log('row-expand', hasDetail ? 'PASS' : 'FAIL', expanded.slice(0, 220))
      log('url-sync-item', /item=/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    } catch (err) {
      log('row-expand', 'FAIL', err.message)
    }
  }

  const sendRow = page.getByRole('button', { name: /^Send$/i }).first()
  const approveRow = page.getByRole('button', { name: /^Approve$/i }).first()
  const reviewRow = page.getByRole('button', { name: /^Review$/i }).first()
  const handleRow = page.getByRole('button', { name: /^Handle$/i }).first()
  log('row-send', k.ready_draft > 0 ? ((await sendRow.isVisible().catch(() => false)) ? 'PASS' : 'FAIL') : 'SKIP')
  log('row-approve', k.action > 0 ? ((await approveRow.isVisible().catch(() => false)) ? 'PASS' : 'FAIL') : 'SKIP')
  log('row-review', k.draft > 0 ? ((await reviewRow.isVisible().catch(() => false)) ? 'PASS' : 'FAIL') : 'SKIP')
  log('row-handle', k.task > 0 ? ((await handleRow.isVisible().catch(() => false)) ? 'PASS' : 'FAIL') : 'SKIP')

  const openDeal = page.getByRole('link', { name: /Open deal/i }).first()
  if (await openDeal.isVisible().catch(() => false)) {
    const href = await openDeal.getAttribute('href')
    log('open-deal-href', href && /\/transactions\//.test(href) ? 'PASS' : 'FAIL', href || '')
    await openDeal.click()
    await page.waitForTimeout(800)
    log('open-deal-nav', /\/transactions\//.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
  } else if (items.some((i) => i.transaction_id)) {
    log('open-deal-href', 'FAIL', 'expected Open deal on a deal group')
  } else {
    log('open-deal-href', 'SKIP', 'no attached deals')
  }

  if (await reviewRow.isVisible().catch(() => false)) {
    try {
      await reviewRow.click()
      await page.waitForTimeout(800)
      log('review-nav', /\/ai-emails|\/emails/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
      await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded' })
      await waitForPage(page)
    } catch (err) {
      log('review-nav', 'FAIL', err.message)
    }
  }

  if (await handleRow.isVisible().catch(() => false)) {
    try {
      await handleRow.click()
      await page.waitForTimeout(800)
      log('handle-nav', /\/transactions\/.+tab=tasks/.test(page.url()) || /tab=tasks/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
      await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded' })
      await waitForPage(page)
    } catch (err) {
      log('handle-nav', 'FAIL', err.message)
    }
  }

  if (await sendAll.isVisible().catch(() => false)) {
    try {
      await sendAll.click()
      await page.waitForTimeout(400)
      const dialog = page.getByRole('alertdialog')
      const dlgText = await dialog.innerText().catch(() => '')
      log('send-all-confirm', /Send .* ready email/i.test(dlgText) ? 'PASS' : 'FAIL', dlgText.slice(0, 240))
      const cancel = page.getByRole('button', { name: /Cancel|Keep|Never mind/i }).first()
      if (await cancel.isVisible().catch(() => false)) await cancel.click()
      else await page.keyboard.press('Escape')
      await page.waitForTimeout(300)
      log('send-all-cancel', stayOnPage() && lastSend == null ? 'PASS' : 'FAIL', JSON.stringify(lastSend))
    } catch (err) {
      log('send-all-confirm', 'FAIL', err.message)
    }
  } else {
    log('send-all-confirm', counts.ready > 0 ? 'FAIL' : 'SKIP')
  }

  if (await approveAll.isVisible().catch(() => false)) {
    try {
      await approveAll.click()
      await page.waitForTimeout(400)
      const dialog = page.getByRole('alertdialog')
      const visible = await dialog.isVisible().catch(() => false)
      const dlgText = visible ? await dialog.innerText() : ''
      log('approve-all-confirm', visible && /Approve/i.test(dlgText) ? 'PASS' : 'FAIL', visible ? dlgText.slice(0, 240) : 'no confirm — batch may have fired')
      if (visible) {
        const cancel = page.getByRole('button', { name: /Cancel|Keep|Never mind/i }).first()
        if (await cancel.isVisible().catch(() => false)) await cancel.click()
        else await page.keyboard.press('Escape')
      }
      await page.waitForTimeout(300)
    } catch (err) {
      log('approve-all-confirm', 'FAIL', err.message)
    }
  } else {
    log('approve-all-confirm', counts.safe_approve > 0 ? 'FAIL' : 'SKIP')
  }

  const giveBack = page.getByRole('button', { name: /Give this back to the AI|Use today's date and retry/i }).first()
  log('give-back-visible', (await giveBack.isVisible().catch(() => false)) ? 'PASS' : (k.task > 0 ? 'INFO' : 'SKIP'), 'only on releasable blocked tasks')

  const unattached = /Not linked to a deal|Re-file or discard/i.test(await page.locator('body').innerText())
  const orphanApi = items.some((i) => !i.transaction_id)
  log('unattached-group', orphanApi ? (unattached ? 'PASS' : 'FAIL') : (unattached ? 'INFO' : 'SKIP'))

  const coverageItem = items.find((i) => i.kind === 'coverage')
  if (coverageItem) {
    try {
      await page.getByText(coverageItem.title, { exact: false }).first().click({ timeout: 4000 })
      await page.waitForTimeout(400)
      const opts = coverageItem.coverage?.options || []
      const firstOpt = opts[0]?.label
      log('coverage-options', firstOpt && (await page.getByRole('button', { name: firstOpt }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL', firstOpt || 'no options')
    } catch (err) {
      log('coverage-options', 'FAIL', err.message)
    }
  } else {
    log('coverage-options', 'SKIP', 'no coverage items')
  }

  const txId = items.find((i) => i.transaction_id)?.transaction_id
  if (txId) {
    try {
      await page.goto(`${APP}/needs-you?tx=${txId}`, { waitUntil: 'domcontentloaded' })
      await waitForPage(page)
      const chip = /Showing one deal only/i.test(await page.locator('body').innerText())
      log('deeplink-tx', chip ? 'PASS' : 'FAIL', page.url())
      const clearDeal = page.getByRole('button', { name: /Clear the deal filter/i })
      log('deeplink-tx-clear', (await clearDeal.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
      if (await clearDeal.isVisible().catch(() => false)) {
        await clearDeal.click()
        await page.waitForTimeout(300)
        log('deeplink-tx-cleared', !/tx=/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
      }
    } catch (err) {
      log('deeplink-tx', 'FAIL', err.message)
    }
  }

  const expandItem = items[0]
  if (expandItem?.id) {
    try {
      await page.goto(`${APP}/needs-you?item=${encodeURIComponent(expandItem.id)}`, { waitUntil: 'domcontentloaded' })
      await waitForPage(page)
      const expanded = await page.locator('body').innerText()
      log('deeplink-item', /item=/.test(page.url()) && /Email preview|What happens if you approve|Pick one|Why the AI is asking|Open full review/i.test(expanded) ? 'PASS' : 'FAIL', page.url())
    } catch (err) {
      log('deeplink-item', 'FAIL', err.message)
    }
  }

  try {
    await page.goto(`${APP}/needs-you?kind=task`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    const pressed = await page.getByRole('button', { name: /To handle/i }).first().getAttribute('aria-pressed').catch(() => null)
    log('deeplink-kind', /kind=task/.test(page.url()) && pressed === 'true' ? 'PASS' : 'FAIL', `${page.url()} pressed=${pressed}`)
  } catch (err) {
    log('deeplink-kind', 'FAIL', err.message)
  }

  try {
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    if (await expandBtn.isVisible().catch(() => false)) {
      await expandBtn.focus()
      await page.keyboard.press('Enter')
      await page.waitForTimeout(300)
      log('keyboard-expand', /Email preview|What happens if you approve|Pick one|Why the AI is asking|Open full review/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
    } else {
      const row = page.locator('[role="button"]').filter({ hasText: /Ready to send|AI proposal|Draft to review|Decision|AI task blocked/i }).first()
      if (await row.isVisible().catch(() => false)) {
        await row.focus()
        await page.keyboard.press('Enter')
        await page.waitForTimeout(300)
        log('keyboard-expand', /Email preview|What happens if you approve|Pick one|Why the AI is asking/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
      } else {
        log('keyboard-expand', items.length === 0 ? 'SKIP' : 'FAIL', 'no expandable control')
      }
    }
  } catch (err) {
    log('keyboard-expand', 'FAIL', err.message)
  }

  const showMore = page.getByRole('button', { name: /Show .* more/i }).first()
  log('pagination', (await showMore.isVisible().catch(() => false)) ? 'PASS' : 'SKIP')

  try {
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    const small = await measureBelow12(page)
    writeFileSync(path.join(OUT, 'typography_below_12.json'), JSON.stringify(small, null, 2))
    log('typography-12px', small.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(small.slice(0, 20)))
    const nested = await nestedButtonCount(page)
    writeFileSync(path.join(OUT, 'nested.json'), JSON.stringify(nested, null, 2))
    log('nested-interactive', nested.nested === 0 ? 'PASS' : 'FAIL', JSON.stringify(nested))
    const hits = await hitTargets(page)
    writeFileSync(path.join(OUT, 'hit_targets.json'), JSON.stringify(hits, null, 2))
    const short = [...(hits.hero || []), ...(hits.header || []), ...(hits.rowActions || [])]
      .filter((b) => b.visible && b.h > 0 && b.h < 32)
    log('hit-targets-32', short.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(short.slice(0, 10)))
  } catch (err) {
    log('typography-12px', 'FAIL', err.message)
  }

  const realConsole = consoleErrors.filter((e) => !/Download the React DevTools|favicon|third-party cookie/i.test(e))
  log('console-errors', realConsole.length === 0 && pageErrors.length === 0 ? 'PASS' : 'FAIL', JSON.stringify({
    console: realConsole.slice(0, 8),
    page: pageErrors.slice(0, 8),
    failed: failedRequests.slice(0, 8),
  }))

  try {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    await shot(page, 'mobile_390')
    await dumpText(page, 'mobile_390')
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
    log('mobile-overflow', overflow ? 'FAIL' : 'PASS')
    const exportName = await page.getByRole('button', { name: /Export CSV/i }).first().isVisible().catch(() => false)
    log('mobile-export', exportName ? 'PASS' : 'FAIL')
    const sendNamed = await page.getByRole('button', { name: /Send all ready/i }).first().isVisible().catch(() => false)
    log('mobile-send-all', counts.ready > 0 ? (sendNamed ? 'PASS' : 'FAIL') : 'SKIP')
  } catch (err) {
    log('mobile-overflow', 'FAIL', err.message)
  }

  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({
    findings,
    consoleErrors: realConsole,
    pageErrors,
    failedRequests,
    counts,
    kinds: k,
    scheduler: lastStatus,
    approve: lastApprove,
    send: lastSend,
    release: lastRelease,
  }, null, 2))

  const pass = findings.filter((f) => f.result === 'PASS').length
  const fail = findings.filter((f) => f.result === 'FAIL').length
  const skip = findings.filter((f) => f.result === 'SKIP').length
  const info = findings.filter((f) => f.result === 'INFO').length
  console.log(`\n=== ${PASS} ${pass} pass / ${fail} fail / ${skip} skip / ${info} info ===`)
  console.log(`artifacts: ${OUT}`)
  await browser.close()
  process.exit(0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
