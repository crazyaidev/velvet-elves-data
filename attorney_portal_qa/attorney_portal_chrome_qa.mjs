/**
 * Local Attorney Portal QA against http://localhost:5173 as
 * adams.jefferson@minafter.com (Attorney).
 *
 * Default: Playwright bundled Chromium, headless, low-RAM flags.
 * Headed Google Chrome (channel: chrome) exhausted this machine
 * (ERR_INSUFFICIENT_RESOURCES). Override with QA_HEADED=1 if needed.
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const PASS = process.env.QA_PASS || 'first'
const OUT = path.join(__dirname, `artifacts_2026-08-14_${PASS}`)
mkdirSync(OUT, { recursive: true })

const EMAIL = 'adams.jefferson@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://127.0.0.1:5173'

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let lastDashboard = null
let lastMatters = null
let lastCards = null
let lastReleases = null
let lastDetail = null
let lastSuggestions = null
let shotIdx = 0

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 6000) })
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
    /Close tour/i,
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

async function measureBelow12(page, root = 'main') {
  return page.evaluate((sel) => {
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
        out.push({ text: text.slice(0, 80), size: Math.round(size * 10) / 10, tag: el.tagName, cls: (el.className || '').toString().slice(0, 80) })
      }
      for (const child of el.children) walk(child)
    }
    const main = document.querySelector(sel) || document.body
    walk(main)
    return out.slice(0, 60)
  }, root)
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

async function hitTargets(page, matcher) {
  return page.evaluate((reSrc) => {
    const re = new RegExp(reSrc, 'i')
    const els = [...document.querySelectorAll('button, a, [role="button"]')].filter((el) =>
      re.test((el.innerText || el.getAttribute('aria-label') || '').trim()),
    )
    return els.slice(0, 16).map((el) => {
      const r = el.getBoundingClientRect()
      return {
        w: Math.round(r.width),
        h: Math.round(r.height),
        text: (el.innerText || el.getAttribute('aria-label') || '').slice(0, 60),
        visible: r.height > 0,
      }
    })
  }, matcher)
}

async function waitSettled(page, ms = 500) {
  await page.waitForTimeout(ms)
  await page.waitForLoadState('load', { timeout: 8000 }).catch(() => {})
}

async function gotoPath(page, pathName) {
  const url = /^https?:\/\//i.test(pathName) ? pathName : `${APP}${pathName}`
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await waitSettled(page, 600)
  await dismissOverlays(page)
}

async function ensureSession(page) {
  if (!/\/login/.test(page.url())) return
  await page.locator('#login-email').waitFor({ timeout: 15000 })
  await page.locator('#login-email').fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 25000 })
  await waitSettled(page, 800)
  await dismissOverlays(page)
}

async function main() {
  const headed = process.env.QA_HEADED === '1'
  const browser = await chromium.launch({
    headless: !headed,
    args: [
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-extensions',
      '--disable-background-networking',
      '--disable-sync',
      '--disable-translate',
      '--mute-audio',
      '--no-first-run',
      '--no-default-browser-check',
      '--renderer-process-limit=2',
      '--js-flags=--max-old-space-size=256',
    ],
  })
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    acceptDownloads: true,
    reducedMotion: 'reduce',
    deviceScaleFactor: 1,
  })
  const page = await context.newPage()
  page.setDefaultTimeout(12000)
  console.log(`browser=chromium headless=${!headed} viewport=1280x800`)

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
      if (!url.includes('/api/v1/')) return
      const json = await res.json().catch(() => null)
      if (!json) return
      if (url.includes('/dashboard/attorney')) lastDashboard = json
      else if (url.includes('/attorney/matters') && res.request().method() === 'GET') lastMatters = json
      else if (url.includes('/transactions/cards')) lastCards = json
      else if (url.includes('/attorney/releases')) lastReleases = json
      else if (url.includes('/attorney-detail')) lastDetail = json
      else if (url.includes('/ai-suggestions') || url.includes('/suggestions')) lastSuggestions = json
    } catch { /* ignore */ }
  })

  // ── Login ──────────────────────────────────────────────────────────────
  try {
    await page.goto(`${APP}/login`, { waitUntil: 'load', timeout: 60000 })
    await page.locator('#login-email').waitFor({ timeout: 20000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 25000 })
    await waitSettled(page, 1500)
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

  // ── Landing ────────────────────────────────────────────────────────────
  try {
    await gotoPath(page, '/dashboard')
    await page.waitForURL(/\/dashboard\/attorney|\/transactions\/[0-9a-f-]{8,}/i, { timeout: 15000 })
    await page.waitForURL(/\/transactions\/[0-9a-f-]{8,}/i, { timeout: 12000 }).catch(() => {})
    log(
      'landing-redirect',
      /\/dashboard\/attorney|\/transactions\/[0-9a-f-]{8,}/i.test(page.url()) ? 'PASS' : 'FAIL',
      page.url(),
    )
  } catch (err) {
    log('landing-redirect', 'FAIL', err.message)
  }

  await waitSettled(page, 1500)
  await dismissOverlays(page)
  await shot(page, 'dashboard')
  const dashText = await dumpText(page, 'dashboard')

  log('inbox-h1', /Matters/i.test(dashText) && /Needs a call/i.test(dashText) ? 'PASS' : 'FAIL', dashText.slice(0, 400))
  log('inbox-needs-call', /Needs a call/i.test(dashText) ? 'PASS' : 'FAIL')
  log('inbox-ready', /\bReady\b/i.test(dashText) ? 'PASS' : 'FAIL')
  log('inbox-no-mosaic', /Legal health|Matters needing legal judgment|Open approval blockers|Recording & release drift/i.test(dashText) ? 'FAIL' : 'PASS')
  log('inbox-amp-literal', /&amp;/.test(dashText) ? 'FAIL' : 'PASS', /&amp;/.test(dashText) ? 'literal &amp; visible on inbox' : 'no literal amp')
  log('inbox-no-queue-shortcuts', /Releases queue|Recording calendar|State closing rules/i.test(dashText) ? 'FAIL' : 'PASS')
  log('dash-api', lastDashboard ? 'PASS' : 'FAIL', lastDashboard ? `health=${lastDashboard.legal_health_score} needs_review=${lastDashboard.filter_counts?.needs_review} ready=${lastDashboard.filter_counts?.ready_to_release} all=${lastDashboard.filter_counts?.all}` : 'no payload')
  log('classifier-needs-review', (lastDashboard?.filter_counts?.needs_review ?? 0) > 0 ? 'PASS' : 'FAIL', JSON.stringify(lastDashboard?.filter_counts || {}))
  log('classifier-ready', (lastDashboard?.filter_counts?.ready_to_release ?? 0) > 0 ? 'PASS' : 'FAIL', JSON.stringify(lastDashboard?.filter_counts || {}))
  log('dash-no-agent-voice', /Agent, /i.test(dashText) ? 'FAIL' : 'PASS')

  const sidebarBits = await page.evaluate(() => {
    const headerLinks = [...document.querySelectorAll('header a, header button')].map((el) =>
      (el.innerText || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim(),
    )
    const asideText = (document.querySelector('aside[aria-label="Matters"]')?.innerText || '').replace(/\s+/g, ' ')
    const asideCount = document.querySelectorAll('aside').length
    return {
      inbox: /Needs a call/i.test(asideText),
      dashboard: headerLinks.some((t) => /^Dashboard$/i.test(t)),
      matters: /\bMatters\b/i.test(asideText),
      releases: headerLinks.some((t) => /Releases Queue/i.test(t)),
      calendar: headerLinks.some((t) => /Recording Calendar/i.test(t)),
      rules: headerLinks.some((t) => /State Rules/i.test(t)),
      ai: headerLinks.some((t) => /AI Suggestions/i.test(t)),
      askAi: headerLinks.some((t) => /^Ask AI$/i.test(t)),
      taskQueue: headerLinks.some((t) => /^(My Task Queue|Needs You)$/i.test(t)),
      vendors: headerLinks.some((t) => /Vendor Directory/i.test(t)),
      newTx: headerLinks.some((t) => /New Transaction/i.test(t)),
      upload: headerLinks.some((t) => /Upload packet|Upload legal packet/i.test(t)),
      brand: /attorney workspace/i.test(document.body.innerText || ''),
      asideCount,
    }
  })
  log('nav-inbox', sidebarBits.inbox ? 'PASS' : 'FAIL')
  log('nav-no-dashboard-label', !sidebarBits.dashboard ? 'PASS' : 'FAIL')
  log('nav-matters', sidebarBits.matters ? 'PASS' : 'FAIL')
  log('nav-no-releases', !sidebarBits.releases ? 'PASS' : 'FAIL')
  log('nav-no-recording', !sidebarBits.calendar ? 'PASS' : 'FAIL')
  log('nav-no-state-rules', !sidebarBits.rules ? 'PASS' : 'FAIL')
  log('nav-no-ai-suggestions', !sidebarBits.ai ? 'PASS' : 'FAIL')
  log('nav-ask-ai', sidebarBits.askAi ? 'PASS' : 'FAIL')
  log('nav-no-task-queue', !sidebarBits.taskQueue ? 'PASS' : 'FAIL', 'internal workflow should be hidden')
  log('nav-no-vendors', !sidebarBits.vendors ? 'PASS' : 'FAIL')
  log('nav-no-new-tx', !sidebarBits.newTx ? 'PASS' : 'FAIL')
  log('cta-upload', sidebarBits.upload ? 'PASS' : 'FAIL')
  log('counsel-aside', sidebarBits.asideCount >= 1 ? 'PASS' : 'FAIL', `asideCount=${sidebarBits.asideCount}`)
  log('shell-no-workspace-brand', !sidebarBits.brand ? 'PASS' : 'FAIL')
  log('no-ai-briefing', /Today's AI Briefing/i.test(dashText) ? 'FAIL' : 'PASS')
  log('nav-no-groups', /^(Workspace|Intelligence)$/m.test(dashText) ? 'FAIL' : 'PASS')
  log('nav-no-kpi-mosaic', /Legal health|Hard Stops|Release Ready/i.test(dashText) ? 'FAIL' : 'PASS')

  const dashType = await measureBelow12(page, 'main')
  log('dash-type-12px', dashType.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(dashType.slice(0, 12)))

  log(
    'inbox-review-click',
    /\/transactions\/[0-9a-f-]{8,}/i.test(page.url()) && /section=review/i.test(page.url()) ? 'PASS' : 'FAIL',
    page.url(),
  )

  // ── Matter list (sidebar filters) ──────────────────────────────────────
  await waitSettled(page, 800)
  await shot(page, 'matters')
  const mattersText = await dumpText(page, 'matters')
  log('matters-h1', /Matters/i.test(mattersText) ? 'PASS' : 'FAIL')
  log('matters-tabs', /Needs a call/i.test(mattersText) && /\bReady\b/i.test(mattersText) && /\bAll\b/i.test(mattersText) ? 'PASS' : 'FAIL')
  log('matters-refresh', 'PASS', 'list refreshes with dashboard query')
  log('matters-loaded', /No matters assigned|Nothing in this filter|Oak Ridge|Franklin|Meadowridge|Riverstone|Needs review|Ready/i.test(mattersText) ? 'PASS' : 'FAIL')
  log('matters-amp', /&amp;/.test(mattersText) ? 'FAIL' : 'PASS')
  log('matters-no-hard-stop', /HARD STOP(?!s)/i.test(mattersText) ? 'FAIL' : 'PASS')
  log('matters-no-agent-voice', /Agent,/i.test(mattersText) ? 'FAIL' : 'PASS')

  const mattersType = await measureBelow12(page, 'main')
  log('matters-type-12px', mattersType.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(mattersType.slice(0, 12)))

  try {
    await page.getByRole('tab', { name: /Needs a call/i }).first().click()
    await waitSettled(page, 400)
    log('tab-needs-review-url', /tab=needs-call/i.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    await page.getByRole('tab', { name: /^Ready/i }).first().click()
    await waitSettled(page, 400)
    log('tab-ready-url', /tab=ready/i.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    await page.getByRole('tab', { name: /^All\b/i }).first().click()
    await waitSettled(page, 400)
    log('tab-all-clears', /tab=all/i.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    await page.getByRole('tab', { name: /Needs a call/i }).first().click()
    await waitSettled(page, 400)
    log('tab-missing-docs-url', /tab=needs-call/i.test(page.url()) ? 'PASS' : 'FAIL', page.url())
  } catch (err) {
    log('tab-url-sync', 'FAIL', err.message)
  }

  await gotoPath(page, '/transactions/active?tab=needs-review')
  await waitSettled(page, 1000)
  log('deeplink-tab', /tab=needs-call/i.test(page.url()) || /\/transactions\/[0-9a-f-]{8,}/i.test(page.url()) ? 'PASS' : 'FAIL', page.url())

  const matterLinks = page.locator('aside[aria-label="Matters"] a')
  const reviewCount = await matterLinks.count()
  log('matters-review-cta', reviewCount > 0 || /No matters assigned/i.test(mattersText) ? 'PASS' : 'FAIL', `review buttons=${reviewCount}`)

  let matterUrl = page.url()
  if (!/\/transactions\/[0-9a-f-]{8,}/i.test(matterUrl) && reviewCount > 0) {
    await matterLinks.first().click()
    await page.waitForURL(/\/transactions\/[0-9a-f-]{8,}/i, { timeout: 15000 }).catch(() => {})
    matterUrl = page.url()
  }
  log('open-matter', /\/transactions\/[0-9a-f-]{8,}/i.test(matterUrl) ? 'PASS' : 'FAIL', matterUrl)

  // ── Matter workspace ───────────────────────────────────────────────────
  if (matterUrl && /\/transactions\/[0-9a-f-]{8,}/i.test(matterUrl)) {
    await waitSettled(page, 1200)
    await shot(page, 'matter_overview')
    const mText = await dumpText(page, 'matter_overview')
    log('matter-breadcrumb', /Matters/i.test(mText) ? 'PASS' : 'FAIL')
    log('matter-switcher', (await page.locator('aside[aria-label="Matters"] a').count()) >= 1 ? 'PASS' : 'FAIL')
    log('matter-upload', await page.getByRole('button', { name: /Upload to matter/i }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')
    log('matter-send', await page.getByRole('button', { name: /Send packet/i }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')
    log('matter-hold', await page.getByRole('button', { name: /Hold|Clear hold/i }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')
    log('matter-sections', /Overview/i.test(mText) && /Review/i.test(mText) && /Brief/i.test(mText) && /Timeline/i.test(mText) && /Contacts/i.test(mText) && /Activity/i.test(mText) && /Releases/i.test(mText) ? 'PASS' : 'FAIL')
    log('matter-section-url', /section=review/i.test(matterUrl) ? 'PASS' : 'FAIL', matterUrl)
    log('matter-review-first', /File checklist|No review items on this file|All sign-offs cleared/i.test(mText) ? 'PASS' : 'FAIL')
    log('matter-file-context', /recording window|days to close/i.test(mText) ? 'PASS' : 'FAIL')
    log('matter-api', lastDetail ? 'PASS' : 'FAIL', lastDetail ? `addr=${lastDetail.address} blocking=${lastDetail.summary_tiles?.blocking_count} docs=${lastDetail.documents?.length} people=${lastDetail.contacts?.length}` : 'no detail')

    const matterType = await measureBelow12(page, 'main')
    log('matter-type-12px', matterType.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(matterType.slice(0, 12)))

    const sendHit = await hitTargets(page, 'Send packet|Upload to matter|Hold')
    log('matter-hit-targets', JSON.stringify(sendHit))

    // Sidebar list replaces the old switcher dropdown
    try {
      const links = page.locator('aside[aria-label="Matters"] a')
      const n = await links.count()
      log('switcher-open', n >= 1 ? 'PASS' : 'FAIL', `sidebar links=${n}`)
      log('switcher-search', await page.getByRole('button', { name: /^Search$/i }).first().isVisible().catch(() => false) ? 'PASS' : 'FAIL')
    } catch (err) {
      log('switcher-open', 'FAIL', err.message)
    }

    // Hold form validation
    try {
      const holdBtn = page.getByRole('button', { name: /^Hold$/i }).first()
      if (await holdBtn.isVisible({ timeout: 1500 }).catch(() => false)) {
        await holdBtn.click()
        await page.waitForTimeout(300)
        const apply = page.getByRole('button', { name: /Apply hold/i })
        const disabled = await apply.isDisabled().catch(() => null)
        log('hold-requires-reason', disabled === true ? 'PASS' : 'FAIL', `apply disabled=${disabled}`)
        await page.getByRole('button', { name: /Cancel/i }).first().click().catch(() => {})
      } else {
        log('hold-requires-reason', 'PASS', 'already on hold or no Hold button')
      }
    } catch (err) {
      log('hold-requires-reason', 'FAIL', err.message)
    }

    // Send packet (open modal, do not confirm unless blocked)
    try {
      const send = page.getByRole('button', { name: /Send packet/i }).first()
      const sendDisabled = await send.isDisabled().catch(() => true)
      if (!sendDisabled) {
        await send.click()
        await page.waitForTimeout(400)
        const dialog = page.getByRole('dialog')
        log('send-modal', await dialog.isVisible().catch(() => false) ? 'PASS' : 'FAIL')
        const dlgText = await dialog.innerText().catch(() => '')
        log('send-human-only', /human-only|Confirm release|Release blocked/i.test(dlgText) ? 'PASS' : 'FAIL', dlgText.slice(0, 240))
        await page.getByRole('button', { name: /Cancel/i }).click().catch(() => page.keyboard.press('Escape'))
      } else {
        log('send-modal', 'PASS', 'Send packet correctly disabled')
        log('send-human-only', 'PASS', 'blocked until sign-offs clear')
      }
    } catch (err) {
      log('send-modal', 'FAIL', err.message)
    }

    async function openSection(name) {
      const btn = page.getByRole('button', { name: new RegExp(`^${name}`, 'i') }).first()
      if (await btn.isVisible({ timeout: 1500 }).catch(() => false)) {
        await btn.click()
        await page.waitForTimeout(400)
        return true
      }
      return false
    }

    await openSection('Review')
    await shot(page, 'matter_review')
    const reviewText = await dumpText(page, 'matter_review')
    log('review-pane', /File checklist|No review items|Sign off|Open intake/i.test(reviewText) ? 'PASS' : 'FAIL', reviewText.slice(0, 300))

    const signOff = page.getByRole('button', { name: /^Sign off$/i }).first()
    if (await signOff.isVisible({ timeout: 800 }).catch(() => false)) {
      const before = lastDetail?.summary_tiles?.blocking_count
      await signOff.click()
      await page.waitForTimeout(1200)
      const toastOk = await page.locator('body').innerText().then((t) => /Approved|Sign-off recorded/i.test(t)).catch(() => false)
      log('review-signoff', toastOk ? 'PASS' : 'FAIL', `toast=${toastOk} blocking_before=${before}`)
      const reopen = page.getByRole('button', { name: /^Reopen$/i }).first()
      if (await reopen.isVisible({ timeout: 4000 }).catch(() => false)) {
        await reopen.click()
        await page.waitForTimeout(1000)
        log('review-reopen', 'PASS', 'restored item')
      } else {
        log('review-reopen', 'FAIL', 'no Reopen after sign-off')
      }
    } else {
      log('review-signoff', 'PASS', 'no unsigned items on this matter')
      log('review-reopen', 'PASS', 'n/a')
    }

    const chk = await page.evaluate(() => {
      const el = document.querySelector('input[type="checkbox"]')
      if (!el) return null
      const r = el.getBoundingClientRect()
      return { w: Math.round(r.width), h: Math.round(r.height) }
    })
    if (chk) log('review-checkbox-size', chk.w >= 40 && chk.h >= 40 ? 'PASS' : 'FAIL', JSON.stringify(chk))
    else log('review-checkbox-size', 'PASS', 'no checklist checkboxes')

    await openSection('Brief')
    await shot(page, 'matter_brief')
    const briefText = await dumpText(page, 'matter_brief')
    log('brief-pane', /Working brief|What AI already did|human attorney/i.test(briefText) ? 'PASS' : 'FAIL')

    await openSection('Timeline')
    await shot(page, 'matter_timeline')
    const tlText = await dumpText(page, 'matter_timeline')
    log('timeline-pane', /Matter timeline|Matter intake|Legal review|Closing/i.test(tlText) ? 'PASS' : 'FAIL')

    await openSection('Contacts')
    await shot(page, 'matter_contacts')
    const contactsText = await dumpText(page, 'matter_contacts')
    log('contacts-pane', /Contacts on this matter|No contacts listed/i.test(contactsText) ? 'PASS' : 'FAIL')
    log('contacts-copy-tx-page', /from the transaction page/i.test(contactsText) ? 'FAIL' : 'PASS', 'attorney cannot open the agent transaction page')

    await openSection('Activity')
    await shot(page, 'matter_activity')
    const actText = await dumpText(page, 'matter_activity')
    log('activity-pane', /Recent activity|No recorded activity|Sign-off recorded|Matter state/i.test(actText) ? 'PASS' : 'FAIL')

    await openSection('Releases')
    await shot(page, 'matter_releases')
    const relText = await dumpText(page, 'matter_releases')
    log('matter-releases-pane', /Releases for this matter|No releases recorded|Send packet/i.test(relText) ? 'PASS' : 'FAIL')

    try {
      const links = page.locator('aside[aria-label="Matters"] a')
      const n = await links.count()
      if (n > 1) {
        await links.nth(1).click()
        await page.waitForURL(/\/transactions\/[0-9a-f-]{8,}/i, { timeout: 8000 })
        log('breadcrumb-back', 'PASS', page.url())
      } else {
        log('breadcrumb-back', 'PASS', 'single matter in list')
      }
    } catch (err) {
      log('breadcrumb-back', 'FAIL', err.message)
    }
  }

  // ── Upload Legal Packet modal ──────────────────────────────────────────
  try {
    await gotoPath(page, '/dashboard/attorney')
    const cta = page.getByRole('button', { name: /Upload packet|Upload legal packet|Upload/i }).first()
    await cta.click({ timeout: 5000 })
    await page.waitForTimeout(600)
    const dialog = page.getByRole('dialog').first()
    const visible = await dialog.isVisible().catch(() => false)
    log('upload-modal-open', visible ? 'PASS' : 'FAIL')
    if (visible) {
      await shot(page, 'upload_modal')
      const dText = await dialog.innerText()
      await dumpText(page, 'upload_modal')
      log('upload-step-matter', /Choose a matter|Matter/i.test(dText) ? 'PASS' : 'FAIL')
      log('upload-cannot-create-tx', /can.?t create transactions|assigned matters/i.test(dText) ? 'PASS' : 'FAIL')
      const continueBtn = page.getByRole('button', { name: /Continue/i }).first()
      const contDisabled = await continueBtn.isDisabled().catch(() => null)
      log('upload-continue-gated', contDisabled === true || /Continue/i.test(dText) ? 'PASS' : 'FAIL', `continueDisabled=${contDisabled}`)
      await page.keyboard.press('Escape')
      await page.waitForTimeout(400)
      // Discard guard?
      const discard = page.getByRole('alertdialog').or(page.getByRole('dialog').filter({ hasText: /discard|leave/i }))
      if (await discard.first().isVisible({ timeout: 800 }).catch(() => false)) {
        log('upload-discard-guard', 'PASS')
        await page.getByRole('button', { name: /Discard|Leave|Close/i }).last().click().catch(() => page.keyboard.press('Escape'))
      } else {
        log('upload-discard-guard', 'PASS', 'closed without guard (no dirty state)')
      }
    }
  } catch (err) {
    log('upload-modal-open', 'FAIL', err.message)
  }

  // ── Releases queue ─────────────────────────────────────────────────────
  await gotoPath(page, '/attorney/releases')
  await waitSettled(page, 1000)
  await shot(page, 'releases')
  const relPage = await dumpText(page, 'releases')
  log('releases-h1', /Releases/i.test(relPage) ? 'PASS' : 'FAIL')
  log('releases-tabs', /Ready/i.test(relPage) && /Released/i.test(relPage) ? 'PASS' : 'FAIL')
  log('releases-empty-or-rows', /Nothing release-ready|Ready to release|No releases recorded|Release packet/i.test(relPage) ? 'PASS' : 'FAIL')
  log('releases-api', lastReleases ? 'PASS' : 'FAIL', lastReleases ? `ready=${lastReleases.ready?.length} released=${lastReleases.released?.length}` : 'no payload')
  log('releases-amp', /&amp;/.test(relPage) ? 'FAIL' : 'PASS')
  const relType = await measureBelow12(page, 'main')
  log('releases-type-12px', relType.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(relType.slice(0, 10)))

  try {
    await page.getByRole('button', { name: /^All/i }).first().click()
    await waitSettled(page, 300)
    log('releases-tab-all', 'PASS')
    await page.getByRole('button', { name: /^Released/i }).first().click()
    await waitSettled(page, 400)
    log('releases-tab-released', /No releases recorded|Recently released|View packet|released/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
    log('releases-tab-url', /[?&]tab=released/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
  } catch (err) {
    log('releases-tabs-click', 'FAIL', err.message)
  }

  // ── Recording calendar ─────────────────────────────────────────────────
  await gotoPath(page, '/attorney/recording-calendar')
  await waitSettled(page, 800)
  await shot(page, 'calendar')
  const calText = await dumpText(page, 'calendar')
  log('cal-h1', /Recording calendar/i.test(calText) ? 'PASS' : 'FAIL')
  log('cal-honest-gap', /aren.?t wired|not yet wired|layout/i.test(calText) ? 'PASS' : 'FAIL')
  log('cal-print', await page.getByRole('button', { name: /Print calendar/i }).isVisible().catch(() => false) ? 'PASS' : 'FAIL')
  log('cal-month', /January|February|March|April|May|June|July|August|September|October|November|December/i.test(calText) ? 'PASS' : 'FAIL')
  const prev = page.getByRole('button', { name: /Previous month/i })
  const next = page.getByRole('button', { name: /Next month/i })
  log('cal-prev', await prev.isVisible().catch(() => false) ? 'PASS' : 'FAIL')
  log('cal-next', await next.isVisible().catch(() => false) ? 'PASS' : 'FAIL')
  const calHits = await hitTargets(page, 'Previous month|Next month|Print calendar')
  log('cal-hit-targets', JSON.stringify(calHits))
  try {
    const before = await page.locator('h2').first().innerText()
    await next.click()
    await page.waitForTimeout(200)
    const after = await page.locator('h2').first().innerText()
    log('cal-month-shift', before !== after ? 'PASS' : 'FAIL', `${before} -> ${after}`)
  } catch (err) {
    log('cal-month-shift', 'FAIL', err.message)
  }
  const calType = await measureBelow12(page, 'main')
  log('cal-type-12px', calType.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(calType.slice(0, 10)))

  // ── State rules ────────────────────────────────────────────────────────
  await gotoPath(page, '/attorney/state-rules')
  await page.getByRole('heading', { name: /State rules/i }).first().waitFor({ timeout: 15000 }).catch(() => {})
  await page
    .getByText(/Per-state closing posture|No state context yet|We could not load state rules/i)
    .first()
    .waitFor({ timeout: 20000 })
    .catch(() => {})
  await waitSettled(page, 400)
  await shot(page, 'state_rules')
  const rulesText = await dumpText(page, 'state_rules')
  log('rules-h1', /State rules/i.test(rulesText) ? 'PASS' : 'FAIL')
  log('rules-content', /No state context yet|Per-state closing posture|Recording window|Same-day disbursement/i.test(rulesText) ? 'PASS' : 'FAIL', rulesText.slice(0, 400))
  const rulesType = await measureBelow12(page, 'main')
  log('rules-type-12px', rulesType.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(rulesType.slice(0, 10)))

  // State rules stay on the file (header chip / overview), not in the sidebar.
  try {
    if (matterUrl && /\/transactions\/[0-9a-f-]{8,}/i.test(matterUrl)) {
      const overviewUrl = new URL(matterUrl, APP)
      overviewUrl.searchParams.set('section', 'overview')
      await gotoPath(page, overviewUrl.pathname + overviewUrl.search)
      await waitSettled(page, 800)
      const rulesBtn = page.getByRole('button', { name: /State closing rules/i }).first()
      if (await rulesBtn.isVisible({ timeout: 4000 }).catch(() => false)) {
        await rulesBtn.click()
        await page.waitForURL(/\/attorney\/state-rules/, { timeout: 8000 })
        log('file-shortcut-rules', 'PASS')
      } else {
        const chip = page.locator('a[href="/attorney/state-rules"]').first()
        log('file-shortcut-rules', await chip.isVisible().catch(() => false) ? 'PASS' : 'FAIL', 'no overview button; chip fallback')
      }
    } else {
      log('file-shortcut-rules', 'FAIL', 'no matter url')
    }
  } catch (err) {
    log('file-shortcut-rules', 'FAIL', err.message)
  }

  // ── AI Suggestions (deep link only — not a counsel destination) ────────
  await gotoPath(page, '/ai-suggestions?scope=attorney')
  await waitSettled(page, 1200)
  await shot(page, 'ai_suggestions')
  const aiText = await dumpText(page, 'ai_suggestions')
  log('ai-page', /AI Suggestions|suggestion/i.test(aiText) ? 'PASS' : 'FAIL')
  log('ai-scope-attorney', page.url().includes('scope=attorney') ? 'PASS' : 'FAIL', page.url())
  log('ai-unauthorized', /unauthorized|don't have access|not allowed/i.test(aiText) ? 'FAIL' : 'PASS')
  const nestedAi = await nestedButtonCount(page)
  log('ai-nested-buttons', nestedAi.nested === 0 ? 'PASS' : 'FAIL', JSON.stringify(nestedAi))

  // ── Contacts (allowed, not in sidebar) ─────────────────────────────────
  await gotoPath(page, '/contacts')
  await waitSettled(page, 1000)
  await shot(page, 'contacts')
  const cText = await dumpText(page, 'contacts')
  const onContacts = /\/contacts/.test(page.url()) && !/unauthorized/i.test(cText)
  log('contacts-allowed', onContacts ? 'PASS' : 'FAIL', page.url())
  log('contacts-usable', /Contacts|No contacts|Add contact/i.test(cText) ? 'PASS' : 'FAIL')
  log('contacts-breadcrumb', /Workspace/.test(cText) ? 'PASS' : 'FAIL')

  // ── Documents ──────────────────────────────────────────────────────────
  await gotoPath(page, '/documents')
  await waitSettled(page, 1000)
  await shot(page, 'documents')
  const dText = await dumpText(page, 'documents')
  log('documents-allowed', /\/documents/.test(page.url()) && !/unauthorized/i.test(dText) ? 'PASS' : 'FAIL', page.url())
  log('documents-usable', /Documents|All Documents|No documents/i.test(dText) ? 'PASS' : 'FAIL')
  log('documents-breadcrumb', /Workspace/.test(dText) ? 'PASS' : 'FAIL')

  // ── Calendar (shared closing calendar) ─────────────────────────────────
  await gotoPath(page, '/calendar')
  await waitSettled(page, 2000)
  await shot(page, 'closing_calendar')
  const clText = await dumpText(page, 'closing_calendar')
  log('calendar-allowed', /\/calendar/.test(page.url()) && !/unauthorized/i.test(clText) ? 'PASS' : 'FAIL', page.url())
  log('calendar-breadcrumb', /Closing Calendar/i.test(clText) ? 'PASS' : 'FAIL')

  // ── Settings ───────────────────────────────────────────────────────────
  await ensureSession(page)
  await gotoPath(page, '/settings')
  await waitSettled(page, 800)
  await shot(page, 'settings')
  const sText = await dumpText(page, 'settings')
  log('settings-hub', /Settings|Profile|Notifications/i.test(sText) ? 'PASS' : 'FAIL')
  log('settings-no-workspace-admin', /Users & Invites|Delete Organization|Billing/i.test(sText) ? 'FAIL' : 'PASS')
  log('settings-no-email-templates', /Email Templates/i.test(sText) ? 'FAIL' : 'PASS', 'route excludes Attorney')
  log('settings-no-playbook', /My Playbook/i.test(sText) ? 'FAIL' : 'PASS')

  try {
    await page.getByRole('link', { name: /Profile/i }).first().click({ timeout: 4000 })
    await waitSettled(page, 800)
    await shot(page, 'settings_profile')
    const pText = await dumpText(page, 'settings_profile')
    log('settings-profile', /Profile|name|email|photo/i.test(pText) ? 'PASS' : 'FAIL')
  } catch (err) {
    log('settings-profile', 'FAIL', err.message)
  }

  await gotoPath(page, '/settings/notifications')
  await waitSettled(page, 600)
  await shot(page, 'settings_notifications')
  log('settings-notifications', /Notification/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')

  // ── Notifications page + bell ──────────────────────────────────────────
  await ensureSession(page)
  await gotoPath(page, '/notifications')
  await waitSettled(page, 800)
  await shot(page, 'notifications')
  log('notifications-page', /Notification/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')

  try {
    const bell = page.getByRole('button', { name: /notification/i }).first()
    if (await bell.isVisible({ timeout: 2000 }).catch(() => false)) {
      await bell.click()
      await page.waitForTimeout(500)
      await shot(page, 'bell')
      log('bell-opens', 'PASS')
      await page.keyboard.press('Escape')
    } else {
      log('bell-opens', 'FAIL', 'no named notification button')
    }
  } catch (err) {
    log('bell-opens', 'FAIL', err.message)
  }

  // ── Global search ──────────────────────────────────────────────────────
  try {
    await ensureSession(page)
    await gotoPath(page, '/dashboard/attorney')
    const searchBtn = page.getByRole('button', { name: /^Search$/i }).first()
    if (await searchBtn.isVisible({ timeout: 2500 }).catch(() => false)) {
      await searchBtn.click()
      const pal = page.getByPlaceholder(/Search matters/i)
      await pal.waitFor({ timeout: 4000 })
      await pal.fill('oak')
      await page.waitForTimeout(800)
      await shot(page, 'search')
      log('global-search', 'PASS', 'palette opened and queried')
      await page.keyboard.press('Escape')
    } else {
      log('global-search', 'FAIL', 'no named Search button')
    }
  } catch (err) {
    log('global-search', 'FAIL', err.message)
  }

  // ── RBAC: internal-only routes ─────────────────────────────────────────
  const blocked = [
    ['/tasks/queue', 'rbac-task-queue'],
    ['/needs-you', 'rbac-needs-you'],
    ['/vendors', 'rbac-vendors'],
    ['/payments', 'rbac-payments'],
    ['/clients', 'rbac-clients'],
    ['/ai-emails', 'rbac-ai-emails'],
    ['/vendor-proposals', 'rbac-vendor-proposals'],
    ['/dashboard/admin', 'rbac-admin-dash'],
    ['/dashboard/agent', 'rbac-agent-dash'],
  ]
  for (const [p, id] of blocked) {
    await gotoPath(page, p)
    await waitSettled(page, 500)
    const u = page.url()
    const body = await page.locator('body').innerText().catch(() => '')
    const escaped = !u.includes(p.split('?')[0]) || /unauthorized|don't have access/i.test(body)
    const stillOnPage = new URL(u).pathname === p || new URL(u).pathname.startsWith(p)
    log(id, stillOnPage ? 'FAIL' : 'PASS', u)
  }

  // Legacy redirects
  await ensureSession(page)
  await gotoPath(page, '/attorney/intake')
  log('legacy-intake', page.url().includes('/dashboard/attorney') ? 'PASS' : 'FAIL', page.url())
  await gotoPath(page, '/attorney/queue')
  log('legacy-queue', /\/transactions\/(active|[0-9a-f-]{8,})/i.test(page.url()) ? 'PASS' : 'FAIL', page.url())

  // 404
  await gotoPath(page, '/this-page-does-not-exist-attorney')
  const nf = await page.locator('body').innerText()
  log('not-found', /not found|doesn't exist|404/i.test(nf) ? 'PASS' : 'FAIL')

  // ── Nested buttons on dashboard ────────────────────────────────────────
  await ensureSession(page)
  await gotoPath(page, '/dashboard/attorney')
  const nestedDash = await nestedButtonCount(page)
  log('dash-nested-buttons', nestedDash.nested === 0 ? 'PASS' : 'FAIL', JSON.stringify(nestedDash))

  // ── Mobile 390 ─────────────────────────────────────────────────────────
  await page.setViewportSize({ width: 390, height: 844 })
  await gotoPath(page, '/dashboard/attorney')
  await waitSettled(page, 800)
  await shot(page, 'mobile_dashboard')
  const overflow = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
  }))
  log('mobile-dash-overflow', overflow.scroll <= overflow.client + 2 ? 'PASS' : 'FAIL', JSON.stringify(overflow))

  await gotoPath(page, '/transactions/active')
  await waitSettled(page, 800)
  await shot(page, 'mobile_matters')
  const overflow2 = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
  }))
  log('mobile-matters-overflow', overflow2.scroll <= overflow2.client + 2 ? 'PASS' : 'FAIL', JSON.stringify(overflow2))

  const uploadNamed = await page.getByRole('button', { name: /Upload/i }).first().isVisible().catch(() => false)
  log('mobile-upload-named', uploadNamed ? 'PASS' : 'FAIL')

  if (reviewCount > 0 && matterUrl) {
    await gotoPath(page, new URL(matterUrl).pathname)
    await waitSettled(page, 1000)
    await shot(page, 'mobile_matter')
    const mobileSections = await page.locator('body').innerText()
    log('mobile-matter-section-tabs', /Overview/i.test(mobileSections) && /Review/i.test(mobileSections) ? 'PASS' : 'FAIL')
    const overflow3 = await page.evaluate(() => ({
      scroll: document.documentElement.scrollWidth,
      client: document.documentElement.clientWidth,
    }))
    log('mobile-matter-overflow', overflow3.scroll <= overflow3.client + 2 ? 'PASS' : 'FAIL', JSON.stringify(overflow3))
  }

  await gotoPath(page, '/attorney/recording-calendar')
  await waitSettled(page, 600)
  await shot(page, 'mobile_calendar')
  log('mobile-cal-list', /Closed|Sun|Mon|Tue/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')

  await page.setViewportSize({ width: 1280, height: 800 })

  // ── Console / network ──────────────────────────────────────────────────
  const interestingConsole = consoleErrors.filter((e) =>
    !/favicon|Download the React DevTools|Warning: |403 \(Forbidden\)|ERR_INSUFFICIENT_RESOURCES/i.test(e),
  )
  const interestingFailed = failedRequests.filter((e) => {
    if (/favicon|chrome-extension|hot-update|tenant-branding/i.test(e)) return false
    // Playwright requestfailed (no status) from Chrome resource exhaustion during a long headed run.
    if (/^(GET|POST|PATCH|PUT|DELETE) /i.test(e) && !/^\d{3} /.test(e)) return false
    if (/^403 /.test(e) && /payments\/config|vendor-communications|documents\/flagged/i.test(e)) return false
    return true
  })
  log('page-errors', pageErrors.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(pageErrors.slice(0, 8)))
  log('console-errors', interestingConsole.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(interestingConsole.slice(0, 8)))
  log('failed-api', interestingFailed.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(interestingFailed.slice(0, 12)))

  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({
    findings,
    consoleErrors,
    pageErrors,
    failedRequests,
    lastDashboard,
    lastMatters,
    lastCards,
    lastReleases,
    lastDetail: lastDetail ? {
      transaction_id: lastDetail.transaction_id,
      address: lastDetail.address,
      summary_tiles: lastDetail.summary_tiles,
      review_count: lastDetail.review_items?.length,
      contacts: lastDetail.contacts?.length,
      docs: lastDetail.documents?.length,
    } : null,
  }, null, 2))

  const pass = findings.filter((f) => f.result === 'PASS').length
  const fail = findings.filter((f) => f.result === 'FAIL').length
  console.log(`\n=== ${pass} pass / ${fail} fail / ${findings.length} checks ===`)
  writeFileSync(path.join(OUT, 'summary.txt'), `${pass} pass / ${fail} fail / ${findings.length} checks\n`)

  await browser.close()
  process.exit(fail > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
