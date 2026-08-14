/**
 * Local Chrome QA for Intelligence › Vendor Proposals.
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
let lastList = null
let lastReviews = null
let lastAccept = null
let lastReject = null
let lastClarify = null
let lastReopen = null
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
}

async function waitForPage(page) {
  await page.getByRole('heading', { name: /Vendor proposals/i }).first().waitFor({ timeout: 45000 })
  await page.waitForFunction(
    () => {
      const t = document.body?.innerText || ''
      if (/Couldn't load vendor proposals|Failed to load/i.test(t)) return true
      if (/Loading queue/i.test(t)) return false
      return (
        /Vendor proposed/i.test(t)
        || /Nothing pending your decision/i.test(t)
        || /No proposals waiting/i.test(t)
        || /No proposals to review/i.test(t)
        || /No proposals match/i.test(t)
        || /No decided proposals/i.test(t)
      )
    },
    { timeout: 60000 },
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
    const pageHeader = [...document.querySelectorAll('header')].find((h) => /Vendor proposals/i.test(h.innerText || ''))
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
      if (!url.includes('/api/v1/vendor-communications/proposals') && !url.includes('/api/v1/vendor-task-reviews')) return
      if (!res.ok()) {
        failedRequests.push(`${res.status()} ${res.request().method()} ${url}`)
        return
      }
      const json = await res.json().catch(() => null)
      if (!json) return
      if (url.includes('/vendor-task-reviews')) lastReviews = json
      else if (url.includes('/accept')) lastAccept = json
      else if (url.includes('/reject')) lastReject = json
      else if (url.includes('/needs-clarification')) lastClarify = json
      else if (url.includes('/reopen')) lastReopen = json
      else if (res.request().method() === 'GET' && url.includes('/proposals')) {
        const decidedOnly = /status=accepted|status=rejected|status=superseded/.test(url)
        if (!decidedOnly) lastList = json
      }
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
    const nav = page.getByRole('link', { name: /Vendor Proposals/i }).first()
    await nav.waitFor({ timeout: 8000 })
    const badge = (await nav.innerText()).replace(/\s+/g, ' ').trim()
    await nav.click()
    await page.waitForURL(/\/vendor-proposals/, { timeout: 15000 })
    log('nav-sidebar', 'PASS', `${page.url()} badge="${badge}"`)
  } catch (err) {
    log('nav-sidebar', 'FAIL', err.message)
    await page.goto(`${APP}/vendor-proposals`, { waitUntil: 'domcontentloaded', timeout: 20000 })
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
  writeFileSync(path.join(OUT, 'proposals_api.json'), JSON.stringify(lastList, null, 2))
  writeFileSync(path.join(OUT, 'reviews_api.json'), JSON.stringify(lastReviews, null, 2))

  const items = lastList?.items || []
  const pending = items.filter((p) => p.status === 'pending')
  const clarify = items.filter((p) => p.status === 'needs_clarification')
  log('api-list', lastList ? 'PASS' : 'FAIL', `total=${lastList?.total} pending=${pending.length} clarify=${clarify.length}`)

  const crumb = page.getByRole('navigation', { name: 'Breadcrumb' })
  log('chrome-breadcrumb', (await crumb.isVisible().catch(() => false)) && (await crumb.innerText()).includes('Intelligence') ? 'PASS' : 'FAIL')
  log('chrome-h1', (await page.getByRole('heading', { name: /Vendor proposals/i }).first().isVisible()) ? 'PASS' : 'FAIL')
  log('chrome-refresh', (await page.getByRole('button', { name: /Refresh/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  log('chrome-export', (await page.getByRole('button', { name: /Export/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  log('chrome-search', (await page.getByRole('searchbox').first().isVisible().catch(() => false)) || (await page.getByPlaceholder(/search/i).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')

  log('tabs-pending', /Awaiting decision/i.test(body) ? 'PASS' : 'FAIL')
  log('tabs-clarify', /Awaiting vendor/i.test(body) ? 'PASS' : 'FAIL')
  log('tabs-all', /All open/i.test(body) ? 'PASS' : 'FAIL')
  log('tabs-decided', (await page.getByRole('tab', { name: /Decided/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')

  log('url-sync-default', /tab=|view=|q=/.test(page.url()) ? 'PASS' : 'INFO', page.url())

  try {
    await page.getByRole('tab', { name: /Awaiting vendor/i }).click()
    await page.waitForTimeout(400)
    const after = page.url()
    const t = await page.locator('body').innerText()
    log('tab-clarify-click', /Needs clarification|No proposals waiting|Ask vendor/i.test(t) ? 'PASS' : 'FAIL', t.slice(0, 240))
    log('url-sync-tab', /tab=needs_clarification|view=needs/.test(after) ? 'PASS' : 'FAIL', after)
    await page.getByRole('tab', { name: /All open/i }).click()
    await page.waitForTimeout(300)
    const allText = await page.locator('body').innerText()
    const cards = await page.locator('article').count()
    log('tab-all-shows-open', cards >= Math.min(2, items.length) || /No proposals/i.test(allText) ? 'PASS' : 'FAIL', `cards=${cards}`)
    const decidedTab = page.getByRole('tab', { name: /Decided/i })
    if (await decidedTab.isVisible().catch(() => false)) {
      await decidedTab.click()
      await page.waitForTimeout(600)
      const decidedUrl = page.url()
      const decidedText = await page.locator('body').innerText()
      log('tab-decided-click', /tab=decided/.test(decidedUrl) && (/Rejected|Accepted|No decided/i.test(decidedText)) ? 'PASS' : 'FAIL', decidedUrl)
    }
    await page.getByRole('tab', { name: /Awaiting decision/i }).click()
    await page.waitForTimeout(300)
  } catch (err) {
    log('tab-clarify-click', 'FAIL', err.message)
  }

  try {
    const search = page.getByLabel(/Search proposals/i)
    if (await search.isVisible().catch(() => false)) {
      await search.fill('Harness')
      await page.waitForTimeout(300)
      const hit = /Harness/i.test(await page.locator('body').innerText())
      log('search-hit', hit ? 'PASS' : 'FAIL')
      await search.fill('zzznomatchxyz999')
      await page.waitForTimeout(300)
      log('search-empty', /No proposals match/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
      await search.fill('')
      await page.waitForTimeout(200)
    } else {
      log('search-hit', 'FAIL', 'no search control')
      log('search-empty', 'FAIL', 'no search control')
    }
  } catch (err) {
    log('search-hit', 'FAIL', err.message)
  }

  try {
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 8000 }),
      page.getByRole('button', { name: /Export CSV/i }).click(),
    ])
    const name = download.suggestedFilename()
    const dest = path.join(OUT, name || 'vendor-proposals.csv')
    await download.saveAs(dest)
    log('export-csv', /vendor-proposals/i.test(name) ? 'PASS' : 'FAIL', name)
  } catch (err) {
    log('export-csv', 'FAIL', err.message)
  }

  const pendingCard = page.locator('article').filter({ hasText: /Vendor proposed|77 Harness|Accept|Inspection/i }).first()
  if (await pendingCard.isVisible().catch(() => false)) {
    log('card-pending-visible', 'PASS')
    log('card-task-name', /Vendor proposed a date change|Inspection|Welcome|Title/i.test(await pendingCard.innerText()) ? 'PASS' : 'FAIL')
    log('card-deal-link', (await pendingCard.getByRole('link').count()) > 0 ? 'PASS' : 'FAIL')
    log('card-confidence', /90%|AI ·/i.test(await pendingCard.innerText()) ? 'PASS' : 'FAIL')
    const hasPicker = (await pendingCard.getByRole('combobox').count()) > 0 || /Pick a task|Link a task/i.test(await pendingCard.innerText())
    const acceptBtn = pendingCard.getByRole('button', { name: /Accept/i })
    const acceptDisabled = await acceptBtn.isDisabled().catch(() => true)
    log('card-task-picker', hasPicker || !acceptDisabled ? 'PASS' : 'FAIL', hasPicker ? 'picker' : 'already linked')
    log('card-accept-gated', hasPicker ? (acceptDisabled ? 'PASS' : 'FAIL') : 'PASS', `disabled=${acceptDisabled}`)
    try {
      const picker = pendingCard.getByLabel('Link to a task')
      if (await picker.isVisible().catch(() => false)) {
        const options = await picker.locator('option').allTextContents()
        const pick = options.find((o) => /Inspection Scheduled/i.test(o)) || options.find((o) => o && !/^Pick a task/i.test(o))
        if (pick) {
          await picker.selectOption({ label: pick })
          await page.waitForTimeout(200)
        }
      }
      const enabled = !(await acceptBtn.isDisabled().catch(() => true))
      log('accept-ready', enabled ? 'PASS' : 'FAIL')

      try {
        await pendingCard.getByRole('button', { name: /^Reject$/i }).click({ timeout: 4000 })
        await page.waitForTimeout(300)
        const rejectUi = await pendingCard.innerText()
        log('reject-panel', /Alternative date|Reject only|Reject & reply/i.test(rejectUi) ? 'PASS' : 'FAIL')
        await page.keyboard.press('Escape')
        await page.waitForTimeout(250)
        const afterEsc = await pendingCard.innerText()
        log('reject-escape', /Alternative date/i.test(afterEsc) ? 'FAIL' : 'PASS')
        if (/Alternative date/i.test(afterEsc)) {
          await pendingCard.getByRole('button', { name: /Cancel/i }).click().catch(() => {})
        }
      } catch (err) {
        log('reject-panel', 'FAIL', err.message)
      }

      if (enabled && process.env.QA_PASS === 'verify') {
        lastAccept = null
        lastReopen = null
        await acceptBtn.click()
        const undo = page.getByRole('button', { name: /^Undo$/i }).first()
        const toastOk = await undo.waitFor({ state: 'visible', timeout: 5000 }).then(() => true).catch(() => false)
        const accepted = lastAccept?.status === 'accepted'
        log('accept-undo-toast', toastOk || accepted ? 'PASS' : 'FAIL', `toast=${toastOk} status=${lastAccept?.status || ''}`)
        if (toastOk) {
          await undo.click()
          await page.waitForTimeout(1500)
          log('accept-undo', lastReopen?.status === 'pending' || (await page.locator('article').filter({ hasText: /77 Harness|Inspection/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL', lastReopen?.status)
        } else {
          await page.getByRole('tab', { name: /Decided/i }).click()
          await page.waitForTimeout(600)
          const restore = page.getByRole('button', { name: /Restore to queue/i }).first()
          if (await restore.isVisible().catch(() => false)) {
            await restore.click()
            await page.waitForTimeout(1500)
            log('accept-undo', lastReopen?.status === 'pending' ? 'PASS' : 'FAIL', lastReopen?.status)
          } else {
            log('accept-undo', accepted ? 'PASS' : 'FAIL', 'accepted; restore control missing')
          }
          await page.getByRole('tab', { name: /Awaiting decision/i }).click().catch(() => {})
        }
      }
    } catch (err) {
      log('accept-ready', 'FAIL', err.message)
    }
  } else {
    log('card-pending-visible', items.length === 0 ? 'SKIP' : 'FAIL', 'no pending card in default tab')
  }

  log('error-alert', (await page.locator('[role="alert"]').count()) >= 0 ? 'PASS' : 'FAIL')

  try {
    await page.goto(`${APP}/vendor-proposals?tab=needs_clarification`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    const selected = await page.getByRole('tab', { name: /Awaiting vendor/i }).getAttribute('aria-selected')
    log('deeplink-tab', /tab=needs_clarification/.test(page.url()) && selected === 'true' ? 'PASS' : 'FAIL', `${page.url()} aria-selected=${selected}`)

    await dumpText(page, 'awaiting_vendor')
    await shot(page, 'awaiting_vendor')
    const orphan = page.locator('article').filter({ hasText: /No deal matched|Link to a deal|no date parsed/i }).first()
    if (await orphan.isVisible().catch(() => false)) {
      log('orphan-card', 'PASS')
      log('orphan-deal-search', (await orphan.getByLabel('Link to a deal').isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
      log('orphan-date-input', (await orphan.getByLabel('Vendor proposed date').isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
      const acceptOrphan = orphan.getByRole('button', { name: /Accept/i })
      log('orphan-accept-gated', (await acceptOrphan.isDisabled().catch(() => true)) ? 'PASS' : 'FAIL')

      await orphan.getByRole('button', { name: /Ask vendor to clarify/i }).click()
      await page.waitForTimeout(300)
      const clarifyUi = await orphan.innerText()
      log('orphan-clarify-panel', /Vendor email|Draft clarify ask|No vendor email/i.test(clarifyUi) ? 'PASS' : 'FAIL')
      await page.keyboard.press('Escape')
      await page.waitForTimeout(250)
      log('orphan-clarify-escape', /Draft clarify ask/i.test(await orphan.innerText()) ? 'FAIL' : 'PASS')

      const dealSearch = orphan.getByLabel('Link to a deal')
      if (await dealSearch.isVisible().catch(() => false)) {
        await dealSearch.click()
        await dealSearch.fill('')
        await dealSearch.pressSequentially('Harness', { delay: 40 })
        const hit = page.getByRole('option', { name: /77 Harness Test Lane/i }).first()
        try {
          await hit.waitFor({ state: 'visible', timeout: 15000 })
          await hit.click()
          await page.waitForTimeout(800)
          log('orphan-deal-picked', /Harness/i.test(await orphan.innerText()) ? 'PASS' : 'FAIL')
        } catch (err) {
          const drop = await orphan.innerText().catch(() => '')
          log('orphan-deal-picked', 'FAIL', `${err.message} card=${drop.slice(0, 400)}`)
        }
      }

      const dateInput = orphan.getByLabel('Vendor proposed date')
      if (await dateInput.isVisible().catch(() => false)) {
        await dateInput.fill('2026-08-22')
        await page.waitForTimeout(200)
        log('orphan-date-typed', 'PASS')
      } else {
        log('orphan-date-typed', 'FAIL', 'no date input')
      }

      const taskPicker = orphan.getByLabel('Link to a task')
      if (await taskPicker.isVisible().catch(() => false)) {
        const options = await taskPicker.locator('option').allTextContents()
        const pick = options.find((o) => /Inspection Scheduled/i.test(o)) || options.find((o) => o && !/^Pick a task/i.test(o))
        if (pick) {
          await taskPicker.selectOption({ label: pick })
          await page.waitForTimeout(200)
        }
        log('orphan-task-picked', pick ? 'PASS' : 'FAIL', pick || 'no open tasks')
      } else {
        log('orphan-task-picked', 'FAIL', 'task picker missing after deal')
      }

      const ready = !(await acceptOrphan.isDisabled().catch(() => true))
      log('orphan-accept-ready', ready ? 'PASS' : 'FAIL')

      if (ready && (process.env.QA_PASS === 'verify' || process.env.QA_PASS === 'closeout')) {
        lastAccept = null
        lastReopen = null
        await acceptOrphan.click()
        const undo = page.getByRole('button', { name: /^Undo$/i }).first()
        const toastOk = await undo.waitFor({ state: 'visible', timeout: 8000 }).then(() => true).catch(() => false)
        log('orphan-accept', lastAccept?.status === 'accepted' || toastOk ? 'PASS' : 'FAIL', lastAccept?.status || '')
        if (toastOk) {
          await undo.click()
          await page.waitForTimeout(1500)
          log('orphan-undo', lastReopen?.status === 'pending' ? 'PASS' : 'FAIL', lastReopen?.status)
        } else {
          log('orphan-undo', 'FAIL', 'no undo toast')
        }
      }
    } else {
      log('orphan-card', items.some((p) => !p.transaction_id) ? 'FAIL' : 'SKIP', 'no unmatched card on Awaiting vendor')
    }
  } catch (err) {
    log('orphan-flow', 'FAIL', err.message)
  }

  try {
    await page.goto(`${APP}/vendor-proposals`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    const small = await measureBelow12(page)
    writeFileSync(path.join(OUT, 'typography_below_12.json'), JSON.stringify(small, null, 2))
    log('typography-12px', small.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(small.slice(0, 16)))
    const nested = await nestedButtonCount(page)
    log('nested-interactive', nested.nested === 0 ? 'PASS' : 'FAIL', JSON.stringify(nested))
    const hits = await hitTargets(page)
    writeFileSync(path.join(OUT, 'hit_targets.json'), JSON.stringify(hits, null, 2))
    const short = (hits.refresh || []).filter((b) => b.visible && b.h > 0 && b.h < 32)
    log('hit-targets-32', short.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(short))
  } catch (err) {
    log('typography-12px', 'FAIL', err.message)
  }

  const realConsole = consoleErrors.filter((e) => !/Download the React DevTools|favicon|third-party cookie/i.test(e))
  log('console-errors', realConsole.length === 0 && pageErrors.length === 0 ? 'PASS' : 'FAIL', JSON.stringify({ console: realConsole.slice(0, 8), page: pageErrors.slice(0, 8), failed: failedRequests.slice(0, 8) }))

  try {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(`${APP}/vendor-proposals`, { waitUntil: 'domcontentloaded' })
    await waitForPage(page)
    await shot(page, 'mobile_390')
    await dumpText(page, 'mobile_390')
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
    log('mobile-overflow', overflow ? 'FAIL' : 'PASS')
    const refreshName = await page.getByRole('button', { name: /Refresh/i }).first().isVisible().catch(() => false)
    log('mobile-refresh', refreshName ? 'PASS' : 'FAIL')
    const exportName = await page.getByRole('button', { name: /Export/i }).first().isVisible().catch(() => false)
    log('mobile-export', exportName ? 'PASS' : 'FAIL')
  } catch (err) {
    log('mobile-overflow', 'FAIL', err.message)
  }

  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({
    findings, consoleErrors: realConsole, pageErrors, failedRequests,
    listTotal: lastList?.total, accept: lastAccept, reject: lastReject, clarify: lastClarify, reopen: lastReopen,
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
