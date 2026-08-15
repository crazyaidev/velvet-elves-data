/**
 * Chrome QA for the STYLE_GUIDE-aligned Attorney workspace.
 * Uses installed Google Chrome against http://127.0.0.1:5173.
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, 'artifacts_style_2026-08-15')
mkdirSync(OUT, { recursive: true })

const EMAIL = 'adams.jefferson@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://127.0.0.1:5173'

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let shotIdx = 0

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 280) : ''}`)
}

async function shot(page, name) {
  shotIdx += 1
  const file = path.join(OUT, `${String(shotIdx).padStart(2, '0')}_${name}.png`)
  await page.screenshot({ path: file, fullPage: false }).catch((err) => {
    console.log('screenshot failed', name, err.message)
  })
}

async function dismissOverlays(page) {
  const labels = [
    /Skip tour/i, /Skip for now/i, /^Skip$/i, /Got it/i, /Not now/i,
    /Maybe later/i, /Continue to (app|dashboard)/i, /Go to Dashboard/i,
    /Close tour/i,
  ]
  for (const name of labels) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 400 }).catch(() => false)) {
      await btn.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(200)
    }
  }
  await page.keyboard.press('Escape').catch(() => {})
  const closeChat = page.getByRole('button', { name: /Close AI chat/i })
  if (await closeChat.isVisible({ timeout: 400 }).catch(() => false)) {
    await closeChat.click({ timeout: 2000 }).catch(() => {})
  }
}

async function measureBelow12(page, root = 'body') {
  return page.evaluate((sel) => {
    const out = []
    const walk = (el) => {
      if (!el || el.nodeType !== 1) return
      if (el.closest && el.closest('[data-brand-lockup]')) return
      const style = getComputedStyle(el)
      const size = parseFloat(style.fontSize)
      const text = ([...el.childNodes]
        .filter((n) => n.nodeType === 3)
        .map((n) => n.textContent)
        .join('') || '').trim()
      if (text && size > 0 && size < 12) {
        out.push({
          text: text.slice(0, 80),
          size: Math.round(size * 10) / 10,
          tag: el.tagName,
          cls: (el.className || '').toString().slice(0, 80),
        })
      }
      for (const child of el.children) walk(child)
    }
    walk(document.querySelector(sel) || document.body)
    return out.slice(0, 40)
  }, root)
}

async function dismissToasts(page) {
  const closes = page.locator('[toast-close], [data-hot-toast] button[aria-label="Close"]')
  const n = await closes.count().catch(() => 0)
  for (let i = 0; i < n; i += 1) {
    await closes.nth(i).click({ timeout: 800 }).catch(() => {})
  }
  await page.keyboard.press('Escape').catch(() => {})
}

async function waitSettled(page, ms = 600) {
  await page.waitForTimeout(ms)
  await page.waitForLoadState('load', { timeout: 8000 }).catch(() => {})
}

async function main() {
  let browser
  try {
    browser = await chromium.launch({
      channel: 'chrome',
      headless: true,
      args: ['--disable-dev-shm-usage', '--disable-gpu', '--no-first-run'],
    })
    console.log('browser=chrome channel')
  } catch (err) {
    console.log('chrome channel failed, falling back to chromium:', err.message)
    browser = await chromium.launch({
      headless: true,
      args: ['--disable-dev-shm-usage', '--disable-gpu', '--no-first-run'],
    })
  }

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(15000)

  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()) })
  page.on('pageerror', (err) => pageErrors.push(err.message))
  page.on('requestfailed', (req) => failedRequests.push(`${req.method()} ${req.url()}`))
  page.on('response', (res) => {
    const url = res.url()
    if (!res.ok() && url.includes('/api/v1/')) {
      failedRequests.push(`${res.status()} ${res.request().method()} ${url}`)
    }
  })

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'load', timeout: 60000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 25000 })
    await waitSettled(page, 1200)
    await dismissOverlays(page)
    await dismissOverlays(page)
    log('login', 'PASS', page.url())
  } catch (err) {
    log('login', 'FAIL', err.message)
    await shot(page, 'login_fail')
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, consoleErrors, pageErrors, failedRequests }, null, 2))
    await browser.close()
    process.exit(1)
  }

  await page.goto(`${APP}/dashboard`, { waitUntil: 'domcontentloaded' })
  await page.waitForURL(/\/dashboard\/attorney|\/transactions\/[0-9a-f-]{8,}/i, { timeout: 15000 }).catch(() => {})
  await page.getByText(/Loading matters/i).first().waitFor({ state: 'hidden', timeout: 25000 }).catch(() => {})
  await page.waitForURL(/\/transactions\/[0-9a-f-]{8,}/i, { timeout: 15000 }).catch(() => {})
  await waitSettled(page, 800)
  await dismissOverlays(page)
  await shot(page, 'workspace')

  const body = await page.locator('body').innerText()
  log('landed-on-desk', /\/transactions\/[0-9a-f-]{8,}/i.test(page.url()) || /No matters assigned/i.test(body) ? 'PASS' : 'FAIL', page.url())
  log('brand-descriptor', /Attorney Workspace/i.test(body) ? 'PASS' : 'FAIL')
  log('brand-ai-chip', await page.locator('header').getByText('AI', { exact: true }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')
  const headerText = await page.locator('header').first().innerText()
  log('no-matter-crumb', /Matters\s*\//i.test(headerText) || /review today/i.test(headerText) ? 'FAIL' : 'PASS', headerText.slice(0, 240))
  log('glance-need-review', /Need review/i.test(body) ? 'PASS' : 'FAIL')
  log('glance-ready', /Ready to release/i.test(body) ? 'PASS' : 'FAIL')
  log('glance-clean', /Filed & clean/i.test(body) ? 'PASS' : 'FAIL')
  log('ask-ai-fab', await page.locator('[data-tour="ask-ai-fab"]').isVisible().catch(() => false) ? 'PASS' : 'FAIL')
  log('ask-ai-not-topbar', (await page.locator('header').getByRole('button', { name: /Ask AI/i }).count()) === 0 ? 'PASS' : 'FAIL')
  log('upload-topbar', await page.locator('header').getByRole('button', { name: /Upload documents/i }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')
  log('upload-sidebar', await page.locator('aside[aria-label="Matters"]').getByRole('button', { name: /Upload documents/i }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')
  log('no-upload-packet-label', /Upload packet/i.test(body) ? 'FAIL' : 'PASS')
  log('search', await page.getByRole('button', { name: /^Search$/i }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')
  log('no-task-queue', /\bMy Task Queue\b|\bNeeds You\b/.test(body) ? 'FAIL' : 'PASS')
  log('no-new-tx', /New Transaction/i.test(body) ? 'FAIL' : 'PASS')
  log('no-kpi-mosaic', /Legal health|Hard Stops/i.test(body) ? 'FAIL' : 'PASS')

  const aside = page.locator('aside[aria-label="Matters"]')
  log('caseload-aside', await aside.isVisible().catch(() => false) ? 'PASS' : 'FAIL')
  const asideBg = await aside.evaluate((el) => getComputedStyle(el).backgroundColor).catch(() => '')
  log('caseload-navy', /rgb\(\s*30,\s*51,\s*86\s*\)/.test(asideBg) ? 'PASS' : 'FAIL', asideBg)

  const headerBg = await page.locator('header').first().evaluate((el) => getComputedStyle(el).backgroundColor).catch(() => '')
  log('topbar-white', /rgb\(\s*255,\s*255,\s*255\s*\)/.test(headerBg) ? 'PASS' : 'FAIL', headerBg)

  const typeHits = await measureBelow12(page, 'body')
  const typeHitsVisible = typeHits.filter((t) => !/sr-only/i.test(t.cls))
  log('type-12px', typeHitsVisible.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(typeHitsVisible.slice(0, 15)))

  const matterLinks = aside.locator('a')
  const nMatters = await matterLinks.count()
  log('matter-list', nMatters > 0 || /No matters assigned/i.test(body) ? 'PASS' : 'FAIL', `links=${nMatters}`)

  if (nMatters > 0) {
    await matterLinks.first().click()
    await page.waitForURL(/\/transactions\/[0-9a-f-]{8,}/i, { timeout: 12000 }).catch(() => {})
    await waitSettled(page, 1000)
    await shot(page, 'matter')
    const mText = await page.locator('body').innerText()
    log('command-strip', /blocking sign-off|ready to release|No review items|Matter on hold|Packet released/i.test(mText) ? 'PASS' : 'FAIL')
    log('checklist', /File checklist/i.test(mText) ? 'PASS' : 'FAIL')
    log('ai-brief', /AI legal brief/i.test(mText) ? 'PASS' : 'FAIL')
    log('review-queue', /Review queue/i.test(mText) ? 'PASS' : 'FAIL')
    log('people', /People on this matter/i.test(mText) ? 'PASS' : 'FAIL')
    log('activity', /What changed since you last looked/i.test(mText) ? 'PASS' : 'FAIL')
    log('upcoming', /Upcoming actions/i.test(mText) ? 'PASS' : 'FAIL')
    log('hold', await page.getByRole('button', { name: /Hold|Clear hold/i }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')
    log('checklist-upload', await page.getByRole('button', { name: /^Upload$/i }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')

    const signOff = page.getByRole('button', { name: /^Sign off$/i }).first()
    if (await signOff.isVisible({ timeout: 800 }).catch(() => false)) {
      await signOff.click()
      await page.waitForTimeout(1200)
      const toastOk = /Approved|Sign-off recorded/i.test(await page.locator('body').innerText())
      log('sign-off', toastOk ? 'PASS' : 'FAIL')
      const reopen = page.getByRole('button', { name: /^Reopen$/i }).first()
      if (await reopen.isVisible({ timeout: 4000 }).catch(() => false)) {
        await reopen.click()
        await page.waitForTimeout(800)
        log('reopen', 'PASS')
      } else {
        log('reopen', 'FAIL', 'no Reopen after sign-off')
      }
    } else {
      log('sign-off', 'PASS', 'no unsigned items')
      log('reopen', 'PASS', 'n/a')
    }

    const holdBtn = page.getByRole('button', { name: /^Hold$/i }).first()
    if (await holdBtn.isVisible({ timeout: 800 }).catch(() => false)) {
      await holdBtn.click()
      await page.waitForTimeout(300)
      const apply = page.getByRole('button', { name: /Apply hold/i })
      log('hold-requires-reason', (await apply.isDisabled().catch(() => null)) === true ? 'PASS' : 'FAIL')
      await page.getByRole('button', { name: /Cancel/i }).first().click().catch(() => {})
    } else {
      log('hold-requires-reason', 'PASS', 'already on hold or no Hold')
    }
  }

  try {
    await dismissOverlays(page)
    await dismissToasts(page)
    await page.locator('header [data-tour="upload-legal-packet"]').click({ timeout: 8000 })
    await page.waitForTimeout(500)
    const dialog = page.getByRole('dialog').first()
    const visible = await dialog.isVisible().catch(() => false)
    log('upload-modal', visible ? 'PASS' : 'FAIL')
    if (visible) {
      await shot(page, 'upload_modal')
      const dText = await dialog.innerText()
      log('upload-cannot-create', /can.?t create transactions|assigned matters|Choose a matter/i.test(dText) ? 'PASS' : 'FAIL')
      await page.keyboard.press('Escape')
    }
  } catch (err) {
    log('upload-modal', 'FAIL', err.message)
  }

  try {
    await page.getByRole('button', { name: /^Search$/i }).first().click()
    const pal = page.getByPlaceholder(/Search matters/i)
    await pal.waitFor({ timeout: 4000 })
    await pal.fill('oak')
    await page.waitForTimeout(600)
    await shot(page, 'search')
    log('search-palette', 'PASS')
    await page.keyboard.press('Escape')
    const searchDialog = page.getByRole('dialog', { name: 'Search' })
    await searchDialog.waitFor({ state: 'hidden', timeout: 4000 }).catch(async () => {
      await page.keyboard.press('Escape')
      await searchDialog.waitFor({ state: 'hidden', timeout: 2000 }).catch(() => {})
    })
    await page.waitForTimeout(200)
  } catch (err) {
    log('search-palette', 'FAIL', err.message)
  }

  try {
    await page.getByRole('dialog', { name: 'Search' }).waitFor({ state: 'hidden', timeout: 2000 }).catch(() => {})
    await page.getByRole('button', { name: /Close AI chat/i }).click({ timeout: 800 }).catch(() => {})
    await page.locator('[data-tour="ask-ai-fab"]').click({ timeout: 8000 })
    await page.locator('[data-testid="global-ai-chat-panel"][data-open="true"]').waitFor({ timeout: 5000 })
    const chat = await page.locator('[data-testid="global-ai-chat-panel"]').innerText()
    log('ask-ai-opens', /Velvet Elves AI/i.test(chat) ? 'PASS' : 'FAIL')
    await page.getByRole('button', { name: /Close AI chat/i }).click().catch(() => page.keyboard.press('Escape'))
  } catch (err) {
    log('ask-ai-opens', 'FAIL', err.message)
  }

  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`${APP}/dashboard/attorney`, { waitUntil: 'domcontentloaded' })
  await waitSettled(page, 800)
  await dismissOverlays(page)
  await shot(page, 'mobile')
  const overflow = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
  }))
  log('mobile-overflow', overflow.scroll <= overflow.client + 2 ? 'PASS' : 'FAIL', JSON.stringify(overflow))
  log('mobile-matters-btn', await page.getByRole('button', { name: /Matters/i }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')

  const interestingConsole = consoleErrors.filter((e) =>
    !/favicon|Download the React DevTools|Warning: |403 \(Forbidden\)/i.test(e),
  )
  const interestingFailed = failedRequests.filter((e) => {
    if (/favicon|chrome-extension|hot-update|tenant-branding/i.test(e)) return false
    if (/^(GET|POST|PATCH|PUT|DELETE) /i.test(e) && !/^\d{3} /.test(e)) return false
    if (/^403 /.test(e) && /payments\/config|vendor-communications|documents\/flagged/i.test(e)) return false
    return true
  })
  log('page-errors', pageErrors.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(pageErrors.slice(0, 8)))
  log('console-errors', interestingConsole.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(interestingConsole.slice(0, 8)))
  log('failed-api', interestingFailed.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(interestingFailed.slice(0, 12)))

  const pass = findings.filter((f) => f.result === 'PASS').length
  const fail = findings.filter((f) => f.result === 'FAIL').length
  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, consoleErrors, pageErrors, failedRequests }, null, 2))
  writeFileSync(path.join(OUT, 'summary.txt'), `${pass} pass / ${fail} fail / ${findings.length} checks\n`)
  console.log(`\n=== ${pass} pass / ${fail} fail / ${findings.length} checks ===`)
  await browser.close()
  process.exit(fail > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
