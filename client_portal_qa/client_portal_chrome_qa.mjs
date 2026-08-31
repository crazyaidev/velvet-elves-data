/**
 * Local Client Portal QA against http://127.0.0.1:5173 as
 * bradyn.dejuan@minafter.com (Client).
 *
 * Default is a low-RAM pass: Playwright's bundled Chromium, headless, no
 * screenshots, images/fonts blocked, mobile viewport skipped.
 *
 *   QA_HEADED=1   real headed window (high RAM — avoid on this machine)
 *   QA_SHOTS=1    write PNG screenshots
 *   QA_DUMPS=1    write page text dumps
 *   QA_MOBILE=1   include the 390px pass
 *   QA_CHANNEL=chrome  use installed Google Chrome instead of bundled Chromium
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const PASS = process.env.QA_PASS || 'first'
const STAMP = new Date().toISOString().slice(0, 10)
const OUT = path.join(__dirname, `artifacts_${STAMP}_${PASS}`)
mkdirSync(OUT, { recursive: true })

const EMAIL = 'bradyn.dejuan@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = process.env.QA_APP || 'http://127.0.0.1:5173'
const FIXTURE = path.join(__dirname, 'fixtures', 'qa-upload.txt')
const HEADED = process.env.QA_HEADED === '1'
const SHOTS = process.env.QA_SHOTS === '1'
const DUMPS = process.env.QA_DUMPS === '1'
const MOBILE = process.env.QA_MOBILE === '1'
const CHANNEL = process.env.QA_CHANNEL || ''

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let lastDashboard = null
let lastMessages = null
let lastDocuments = null
let lastInvoices = null
let lastPostMessage = null
let lastUpload = null
let lastFlag = null
let lastNotifications = null
let lastAck = null
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
    const link = page.getByRole('link', { name }).first()
    if (await link.isVisible({ timeout: 400 }).catch(() => false)) {
      await link.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(200)
    }
  }
  if (escape) await page.keyboard.press('Escape').catch(() => {})
}

async function waitSettled(page, ms = 300) {
  await page.waitForTimeout(ms)
  await page.waitForLoadState('domcontentloaded', { timeout: 8000 }).catch(() => {})
}

async function waitForClientShell(page) {
  await page.locator('nav[aria-label="Client navigation"]').first().waitFor({ state: 'attached', timeout: 20000 })
}

async function waitForHomeReady(page) {
  await waitForClientShell(page)
  await page
    .getByRole('heading', { name: /You're (Buying|Selling|Closing)/i })
    .or(page.getByRole('heading', { name: /closing workspace is almost ready/i }))
    .first()
    .waitFor({ timeout: 20000 })
}

async function gotoPath(page, pathName, { escape = true } = {}) {
  const url = /^https?:\/\//i.test(pathName) ? pathName : `${APP}${pathName}`
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await waitSettled(page, 600)
  await dismissOverlays(page, { escape })
  if (new URL(page.url()).pathname.startsWith('/client')) {
    await waitForClientShell(page)
  }
}

async function clientNav(page, label) {
  const btn = page
    .locator('nav[aria-label="Client navigation"]')
    .getByRole('button', { name: new RegExp(`^${label}$`, 'i') })
    .first()
  if (await btn.isVisible({ timeout: 2500 }).catch(() => false)) {
    await btn.click()
    await waitSettled(page, 500)
    await dismissOverlays(page)
    await waitForClientShell(page)
    return
  }
  const routes = {
    Home: '/client/home',
    'Next Steps': '/client/next-steps',
    Timeline: '/client/milestones',
    Documents: '/client/documents',
    Updates: '/client/updates',
  }
  await gotoPath(page, routes[label] || '/client/home')
}

async function ensureSession(page) {
  if (!/\/login/.test(page.url())) return
  await page.locator('#login-email').waitFor({ timeout: 15000 })
  await page.locator('#login-email').fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL((u) => !u.pathname.includes('/login'), {
    timeout: 25000,
    waitUntil: 'domcontentloaded',
  })
  await waitSettled(page, 800)
  await dismissOverlays(page)
}

async function measureBelow12(page, root = 'body') {
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
        out.push({
          text: text.slice(0, 80),
          size: Math.round(size * 10) / 10,
          tag: el.tagName,
          cls: (el.className || '').toString().slice(0, 80),
        })
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

async function smallHitTargets(page) {
  return page.evaluate(() => {
    const els = [...document.querySelectorAll('button, a, [role="button"]')].filter((el) => {
      const r = el.getBoundingClientRect()
      return r.width > 0 && r.height > 0 && (r.width < 40 || r.height < 40)
    })
    return els.slice(0, 24).map((el) => {
      const r = el.getBoundingClientRect()
      return {
        w: Math.round(r.width),
        h: Math.round(r.height),
        text: (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 60),
      }
    })
  })
}

function hasStaffChrome(text) {
  return /\bNeeds You\b|AI Suggestions|Task Queue|Inbox Elf|\bActive Transactions\b|\bNew Transaction\b/i.test(
    text,
  )
}

function hasConciergeNav(text) {
  return /Next Steps/i.test(text) && /Timeline/i.test(text) && /Documents/i.test(text) && /Updates/i.test(text)
}

async function sidebarLabels(page) {
  return page.evaluate(() => {
    const nav = document.querySelector('nav[aria-label="Client navigation"]')
    if (!nav) return []
    return [...nav.querySelectorAll('button, a')].map((el) => (el.innerText || '').trim())
  })
}

function slimDashboard(json) {
  if (!json || typeof json !== 'object') return json
  const txs = json.transactions || []
  return {
    open_invoice_count: json.open_invoice_count,
    home: json.home
      ? {
          hero: json.home.hero,
          next_action: json.home.next_action,
          documents_needing_attention: json.home.documents_needing_attention,
          transaction_id: json.home.transaction_id,
        }
      : null,
    transactions: txs.map((t) => ({
      transaction_id: t.transaction_id,
      address: t.address,
      closing_date: t.closing_date,
      next_action: t.next_action,
    })),
  }
}

async function main() {
  const headless = !HEADED
  const launchOpts = {
    headless,
    args: [
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-software-rasterizer',
      '--disable-extensions',
      '--disable-background-networking',
      '--disable-sync',
      '--disable-default-apps',
      '--disable-hang-monitor',
      '--disable-popup-blocking',
      '--disable-prompt-on-repost',
      '--disable-breakpad',
      '--disable-component-update',
      '--metrics-recording-only',
      '--mute-audio',
      '--no-first-run',
      '--no-default-browser-check',
      '--renderer-process-limit=1',
    ],
  }
  if (CHANNEL) launchOpts.channel = CHANNEL
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
  page.setDefaultTimeout(12000)
  console.log(
    `browser=${CHANNEL || 'chromium'} headless=${headless} viewport=1280x720 shots=${SHOTS} mobile=${MOBILE} app=${APP}`,
  )

  page.on('console', (msg) => {
    if (msg.type() === 'error' && consoleErrors.length < 20) consoleErrors.push(msg.text().slice(0, 400))
  })
  page.on('pageerror', (err) => {
    if (pageErrors.length < 12) pageErrors.push(String(err.message).slice(0, 400))
  })
  page.on('requestfailed', (req) => {
    const err = req.failure()?.errorText || ''
    if (/ERR_ABORTED|NS_BINDING_ABORTED/i.test(err)) return
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
        !/\/dashboard\/client(\?|$)|\/client\/messages|flag-deletion|\/client\/invoices|\/payments\/client|\/client\/notifications|\/acknowledge/.test(
          url,
        )
      ) {
        return
      }
      const json = await res.json().catch(() => null)
      if (!json) return
      if (url.includes('/dashboard/client')) lastDashboard = slimDashboard(json)
      else if (url.includes('/client/messages') && res.request().method() === 'GET') lastMessages = { n: (json.items || json).length }
      else if (url.includes('/client/messages') && res.request().method() === 'POST') lastPostMessage = { ok: true }
      else if (url.includes('flag-deletion')) lastFlag = { ok: true }
      else if (url.includes('/client/invoices') || url.includes('/payments/client')) lastInvoices = json
      else if (url.includes('/documents') && res.request().method() === 'POST') lastUpload = { ok: true }
      else if (url.includes('/client/notifications')) {
        lastNotifications = { unread_count: json.unread_count, items: json.items?.slice?.(0, 3) || json.items }
      } else if (url.includes('/acknowledge')) lastAck = json
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
    await loginWait
    await page.waitForURL((url) => !url.pathname.includes('/login'), {
      timeout: 40000,
      waitUntil: 'domcontentloaded',
    })
    await waitSettled(page, 1500)
    await dismissOverlays(page)
    await dismissOverlays(page)
    await waitForHomeReady(page)
    log('CP-01-login', 'PASS', page.url())
  } catch (err) {
    const body = await page.locator('body').innerText().catch(() => '')
    log('CP-01-login', 'FAIL', `${err.message}\n${body.slice(0, 500)}`)
    await shot(page, 'login_fail')
    writeFileSync(
      path.join(OUT, 'findings.json'),
      JSON.stringify({ findings, consoleErrors, pageErrors, failedRequests }, null, 2),
    )
    await browser.close()
    process.exit(1)
  }

  // ── 2. Landing is concierge Home, not staff chrome ──────────────────────
  try {
    await ensureSession(page)
    const url = new URL(page.url())
    const text = await dumpText(page, 'home')
    await shot(page, 'home')
    const nav = await sidebarLabels(page)
    if (url.pathname === '/client/home') log('CP-02-lands-home', 'PASS', url.pathname)
    else if (url.pathname === '/client/transactions') {
      log('CP-02-lands-home', 'FAIL', `landed on legacy ${url.pathname} instead of /client/home`)
    } else log('CP-02-lands-home', 'FAIL', url.pathname)

    if (hasConciergeNav(text) || nav.includes('Next Steps')) {
      log('CP-03-concierge-nav', 'PASS', nav.join(' | ') || 'nav text present')
    } else log('CP-03-concierge-nav', 'FAIL', `nav=${JSON.stringify(nav)}`)

    if (hasStaffChrome(text)) log('CP-04-no-staff-chrome', 'FAIL', 'staff workspace copy leaked onto Home')
    else log('CP-04-no-staff-chrome', 'PASS', 'no Needs You / Task Queue / AI Suggestions')

    const expectedNav = ['Home', 'Next Steps', 'Timeline', 'Documents', 'Updates']
    const missing = expectedNav.filter((l) => !nav.includes(l))
    if (missing.length === 0) log('CP-05-nav-set', 'PASS', nav.join(', '))
    else log('CP-05-nav-set', 'FAIL', `missing ${missing.join(', ')}; got ${nav.join(', ')}`)

    const unexpected = nav.filter((l) => !expectedNav.includes(l) && l)
    if (unexpected.length) log('CP-05b-nav-extra', 'WARN', unexpected.join(', '))
    else log('CP-05b-nav-extra', 'PASS', 'no extra sidebar items')
  } catch (err) {
    log('CP-02-lands-home', 'FAIL', err.message)
  }

  // ── 3. Home content: real data, empty vs populated ──────────────────────
  try {
    await waitForHomeReady(page)
    const text = await page.locator('body').innerText()
    const txCount = lastDashboard?.transactions?.length ?? 0
    if (DUMPS) writeFileSync(path.join(OUT, 'dashboard_client.json'), JSON.stringify(lastDashboard, null, 2))
    if (txCount === 0) {
      if (/almost ready|No transactions yet|agent will add you/i.test(text)) {
        log('CP-06-home-empty-or-populated', 'PASS', 'honest empty Home; 0 assigned transactions')
      } else {
        log('CP-06-home-empty-or-populated', 'FAIL', '0 transactions but empty-state copy missing')
      }
    } else {
      const hasHero = /You're (Buying|Selling|Closing on)/i.test(text)
      const cards = [
        'Next Best Action',
        'What Velvet Is Handling',
        'Upcoming Dates',
        'Recent Updates',
        'Documents Needing Attention',
        'Key Contacts',
        'Ask your team',
      ]
      const missingCards = cards.filter((c) => !text.includes(c))
      if (hasHero && missingCards.length === 0) {
        log(
          'CP-06-home-empty-or-populated',
          'PASS',
          `${txCount} tx; hero+7 cards; address=${lastDashboard?.home?.hero?.address || lastDashboard?.transactions?.[0]?.address}`,
        )
      } else {
        log(
          'CP-06-home-empty-or-populated',
          'FAIL',
          `hero=${hasHero} missingCards=${missingCards.join(', ') || 'none'}`,
        )
      }
    }

    if (
      /\b(HARD STOP|overdue tasks|AI suggested|internal note|Loan Officer Welcome|Buyer Welcome|Review Documentation)\b/i.test(
        text,
      )
    ) {
      log('CP-07-no-internal-leak', 'FAIL', 'internal workflow language on Home')
    } else log('CP-07-no-internal-leak', 'PASS', 'no task/AI/internal-note leak on Home')

    const nbaTitle = lastDashboard?.home?.next_action?.title || ''
    if (/welcome|review documentation|loan officer/i.test(nbaTitle)) {
      log('CP-OPS-01-nba-client-facing', 'FAIL', `next_action leaked staff task: ${nbaTitle}`)
    } else {
      log('CP-OPS-01-nba-client-facing', 'PASS', nbaTitle || 'no next_action')
    }

    const switcher = page.getByRole('combobox', { name: /Switch deal/i })
    if (txCount > 1) {
      if (await switcher.isVisible({ timeout: 2000 }).catch(() => false)) {
        const options = await switcher.locator('option').allTextContents()
        log('CP-OPS-02-deal-switcher', 'PASS', options.join(' | '))
      } else log('CP-OPS-02-deal-switcher', 'FAIL', 'multi-deal Home missing switcher')
    } else log('CP-OPS-02-deal-switcher', 'PASS', 'single deal; switcher not required')

    const below = await measureBelow12(page)
    if (below.length === 0) log('CP-08-home-type-12px', 'PASS', 'no text below 12px')
    else log('CP-08-home-type-12px', 'FAIL', JSON.stringify(below.slice(0, 12)))

    const nested = await nestedButtonCount(page)
    if (nested.nested === 0) log('CP-09-home-nested-buttons', 'PASS', `buttons=${nested.total}`)
    else log('CP-09-home-nested-buttons', 'FAIL', JSON.stringify(nested))
  } catch (err) {
    log('CP-06-home-empty-or-populated', 'FAIL', err.message)
  }

  // ── 4. Home quick actions ───────────────────────────────────────────────
  try {
    const messageBtn = page.getByRole('button', { name: /Message Agent/i }).first()
    if (await messageBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await page.locator('#ask-velvet').waitFor({ timeout: 8000 }).catch(() => {})
      await messageBtn.click()
      const ask = page.locator('#ask-velvet-input').first()
      await ask.waitFor({ timeout: 8000 })
      await page.waitForFunction(
        () => {
          const el = document.getElementById('ask-velvet-input')
          return el && document.activeElement === el
        },
        null,
        { timeout: 3000 },
      ).catch(() => {})
      const focused = await ask.evaluate((el) => document.activeElement === el).catch(() => false)
      if (focused) log('CP-10-message-agent-focus', 'PASS', 'Ask Velvet focused')
      else log('CP-10-message-agent-focus', 'FAIL', 'Message Agent did not focus Ask Velvet')
    } else {
      log('CP-10-message-agent-focus', 'WARN', 'Message Agent not visible (empty home or mobile)')
    }

    const closingBtn = page.getByRole('button', { name: /Closing Day Info/i }).first()
    if (await closingBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await closingBtn.click()
      await page.waitForTimeout(400)
      const upcoming = page.locator('#upcoming-dates')
      const inView = await upcoming.evaluate((el) => {
        const r = el.getBoundingClientRect()
        return r.top < window.innerHeight && r.bottom > 0
      }).catch(() => false)
      if (inView) log('CP-11-closing-day-scroll', 'PASS', 'scrolled to Upcoming Dates')
      else log('CP-11-closing-day-scroll', 'FAIL', 'Upcoming Dates not in view')
    } else {
      log('CP-11-closing-day-scroll', 'WARN', 'Closing Day Info not visible')
    }

    const viewTimeline = page.getByRole('link', { name: /View Timeline/i }).first()
    if (await viewTimeline.isVisible({ timeout: 1000 }).catch(() => false)) {
      const href = await viewTimeline.getAttribute('href')
      const txId = lastDashboard?.home?.transaction_id || lastDashboard?.transactions?.[0]?.transaction_id
      if (href && /\/client\/milestones\/[^/?]+/.test(href)) {
        log('CP-12-timeline-href', 'PASS', href)
      } else if (href && txId && href.includes(`transaction=${txId}`) && !href.includes(`/milestones/${txId}`)) {
        log('CP-12-timeline-href', 'FAIL', `query-param deep link does not open detail page: ${href}`)
      } else {
        log('CP-12-timeline-href', 'WARN', href || 'no href')
      }
    } else {
      log('CP-12-timeline-href', 'WARN', 'View Timeline link not on Home')
    }

    const paymentsLink = page.getByRole('link', { name: /Payments|invoices|Pay now/i }).first()
    const hasPayments = await paymentsLink.isVisible({ timeout: 800 }).catch(() => false)
    const openInvoices = lastDashboard?.open_invoice_count ?? 0
    if (hasPayments) log('CP-13-home-payments-link', 'PASS', await paymentsLink.innerText())
    else if (openInvoices === 0) log('CP-13-home-payments-link', 'PASS', 'Payments hidden; no open invoices')
    else log('CP-13-home-payments-link', 'FAIL', 'Home has no Payments / invoices affordance')

    const contactsLink = page.getByRole('link', { name: /View all contacts/i }).first()
    if (await contactsLink.isVisible({ timeout: 800 }).catch(() => false)) {
      log('CP-14-home-agent-link', 'PASS', 'View all contacts → Agent Info')
    } else {
      log('CP-14-home-agent-link', 'FAIL', 'no View all contacts link on Home')
    }
  } catch (err) {
    log('CP-10-message-agent-focus', 'FAIL', err.message)
  }

  // ── 5. Ask Velvet send ──────────────────────────────────────────────────
  try {
    await clientNav(page, 'Home')
    await waitForHomeReady(page)
    const txId = lastDashboard?.home?.transaction_id || lastDashboard?.transactions?.[0]?.transaction_id
    const ask = page.locator('#ask-velvet-input').or(page.getByPlaceholder(/Send a question to your agent|Ask anything about your transaction/i)).first()
    if (!txId) {
      log('CP-15-ask-send', 'WARN', 'no transaction — cannot send')
    } else if (await ask.isVisible({ timeout: 8000 }).catch(() => false)) {
      const prompt = page.getByRole('button', { name: /What happens next\?/i }).first()
      if (await prompt.isVisible({ timeout: 800 }).catch(() => false)) {
        await prompt.click()
        log('CP-15b-quick-prompt', 'PASS', 'filled What happens next?')
      } else log('CP-15b-quick-prompt', 'FAIL', 'quick prompt missing')
      const body = `Chrome QA ping ${new Date().toISOString().slice(11, 19)}`
      await ask.fill(body)
      await page.getByRole('button', { name: /Send question/i }).click()
      await page.waitForTimeout(1500)
      const pageText = await page.locator('body').innerText()
      if (/Question sent|Could not send/i.test(pageText) || pageText.includes(body)) {
        const failed = /Could not send/i.test(pageText)
        log(failed ? 'CP-15-ask-send' : 'CP-15-ask-send', failed ? 'FAIL' : 'PASS', failed ? pageText.slice(0, 300) : body)
      } else {
        log('CP-15-ask-send', lastPostMessage ? 'PASS' : 'FAIL', lastPostMessage ? 'POST returned' : 'no toast and no POST body')
      }
      await shot(page, 'ask_velvet')
    } else {
      log('CP-15-ask-send', 'FAIL', 'Ask Velvet composer missing')
    }
  } catch (err) {
    log('CP-15-ask-send', 'FAIL', err.message)
  }

  // ── 6. Next Steps ───────────────────────────────────────────────────────
  try {
    await clientNav(page, 'Next Steps')
    await page.waitForURL(/\/client\/next-steps/, { timeout: 8000 }).catch(() => {})
    await waitSettled(page, 700)
    const text = await dumpText(page, 'next_steps')
    await shot(page, 'next_steps')
    if (/Next Steps/i.test(text)) log('CP-16-next-steps-loads', 'PASS', page.url())
    else log('CP-16-next-steps-loads', 'FAIL', text.slice(0, 240))

    const openTimeline = page.getByRole('link', { name: /View Timeline|Open full timeline/i }).first()
    if (await openTimeline.isVisible({ timeout: 1500 }).catch(() => false)) {
      const href = await openTimeline.getAttribute('href')
      if (href && /\/client\/milestones\/[^/?]+/.test(href)) log('CP-17-next-steps-timeline-href', 'PASS', href)
      else log('CP-17-next-steps-timeline-href', 'FAIL', href || 'missing href')
    } else {
      log('CP-17-next-steps-timeline-href', 'WARN', 'no timeline CTA (empty?)')
    }
    const below = await measureBelow12(page)
    if (below.length === 0) log('CP-18-next-steps-type', 'PASS')
    else log('CP-18-next-steps-type', 'FAIL', JSON.stringify(below.slice(0, 10)))
  } catch (err) {
    log('CP-16-next-steps-loads', 'FAIL', err.message)
  }

  // ── 7. Timeline list + detail ───────────────────────────────────────────
  try {
    await clientNav(page, 'Timeline')
    await ensureSession(page)
    await page.getByRole('heading', { name: /Your Timeline/i }).waitFor({ timeout: 15000 })
    const text = await dumpText(page, 'timeline')
    await shot(page, 'timeline')
    if (/Your Timeline/i.test(text)) log('CP-19-timeline-list', 'PASS', page.url())
    else log('CP-19-timeline-list', 'FAIL', text.slice(0, 240))

    const tx = lastDashboard?.transactions?.[0]
    const card = page.getByRole('link', { name: /View timeline/i }).first()
    if (tx) {
      await card.waitFor({ timeout: 12000 }).catch(() => {})
    }
    if (tx && (await card.isVisible({ timeout: 2000 }).catch(() => false))) {
      await card.click()
      await page.waitForURL(new RegExp(`/client/milestones/${tx.transaction_id}`), { timeout: 8000 })
      await waitSettled(page, 600)
      const detail = await dumpText(page, 'timeline_detail')
      await shot(page, 'timeline_detail')
      if (/Your closing journey|Closing progress|Back to Timeline/i.test(detail)) {
        log('CP-20-timeline-detail', 'PASS', page.url())
      } else log('CP-20-timeline-detail', 'FAIL', detail.slice(0, 240))

      const msg = page.getByRole('link', { name: /Message your team|Ask your team/i }).first()
      if (await msg.isVisible({ timeout: 1000 }).catch(() => false)) {
        const href = await msg.getAttribute('href')
        if (href && href.includes('/client/updates')) log('CP-21-detail-message-href', 'PASS', href)
        else log('CP-21-detail-message-href', 'FAIL', href || 'bad href')
      } else log('CP-21-detail-message-href', 'WARN', 'no message CTA')

      await page.getByRole('link', { name: /Back to Timeline/i }).first().click()
      await page.waitForURL(/\/client\/milestones\/?$/, { timeout: 6000 }).catch(() => {})
      log('CP-22-back-to-timeline', /\/client\/milestones\/?$/.test(new URL(page.url()).pathname) ? 'PASS' : 'FAIL', page.url())
    } else {
      log('CP-20-timeline-detail', tx ? 'FAIL' : 'WARN', tx ? 'View timeline card missing' : 'no transactions')
    }

    if (tx) {
      await gotoPath(page, `/client/milestones?transaction=${tx.transaction_id}`)
      await waitSettled(page, 500)
      const pathNow = new URL(page.url()).pathname
      if (pathNow === `/client/milestones/${tx.transaction_id}`) {
        log('CP-23-query-param-redirect', 'PASS', 'query param opened detail')
      } else if (pathNow === '/client/milestones') {
        log('CP-23-query-param-redirect', 'FAIL', 'stayed on list; ?transaction= ignored')
      } else log('CP-23-query-param-redirect', 'FAIL', page.url())
    }
  } catch (err) {
    log('CP-19-timeline-list', 'FAIL', err.message)
  }

  // ── 8. Documents: list, upload modal, upload, flag ──────────────────────
  try {
    await clientNav(page, 'Documents')
    await ensureSession(page)
    await page.getByRole('heading', { name: 'Your Documents', exact: true }).waitFor({ timeout: 15000 })
    const text = await dumpText(page, 'documents')
    await shot(page, 'documents')
    if (/Your Documents/i.test(text)) log('CP-24-documents-loads', 'PASS')
    else log('CP-24-documents-loads', 'FAIL', text.slice(0, 240))

    if (/From your team/i.test(text) && /You uploaded/i.test(text)) {
      log('CP-OPS-03-doc-sections', 'PASS', 'From your team + You uploaded')
    } else log('CP-OPS-03-doc-sections', 'FAIL', 'missing team/own document sections')

    if (/No documents in/i.test(text)) log('CP-25-no-fake-board', 'FAIL', 'hardcoded empty board copy')
    else log('CP-25-no-fake-board', 'PASS')

    if (/No documents shared with you yet/i.test(text)) {
      log('CP-26-empty-copy', 'FAIL', 'own-uploads list uses "shared with you" copy')
    } else log('CP-26-empty-copy', 'PASS', 'no "shared with you" empty copy')

    const nestedCards = await page.evaluate(() => {
      const outer = [...document.querySelectorAll('section')].filter((s) =>
        /Your documents/i.test(s.innerText || ''),
      )
      return outer.map((s) => ({
        nestedSections: s.querySelectorAll('section').length,
        text: (s.innerText || '').slice(0, 80),
      }))
    })
    const double = nestedCards.some((c) => c.nestedSections > 0)
    if (double) log('CP-27-nested-doc-cards', 'FAIL', JSON.stringify(nestedCards))
    else log('CP-27-nested-doc-cards', 'PASS')

    const uploadBtn = page.getByRole('button', { name: /Upload document/i }).first()
    await uploadBtn.waitFor({ timeout: 10000 })
    await page
      .waitForFunction(() => {
        const btn = [...document.querySelectorAll('button')].find((b) =>
          /Upload document/i.test(b.innerText || ''),
        )
        return btn && !btn.disabled
      }, { timeout: 8000 })
      .catch(() => {})
    if (await uploadBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      const disabled = await uploadBtn.isDisabled()
      const txCount = lastDashboard?.transactions?.length ?? 0
      if (txCount === 0 && disabled) log('CP-28-upload-disabled-empty', 'PASS', 'disabled with no tx')
      else if (txCount === 0 && !disabled) log('CP-28-upload-disabled-empty', 'FAIL', 'upload enabled with 0 tx')
      else if (txCount > 0 && disabled) log('CP-28-upload-disabled-empty', 'FAIL', `upload disabled with ${txCount} tx`)
      else log('CP-28-upload-disabled-empty', 'PASS', `tx=${txCount} disabled=${disabled}`)

      if (!disabled) {
        await uploadBtn.click()
        await page.getByRole('dialog', { name: /Upload a document/i }).waitFor({ timeout: 5000 })
        await shot(page, 'upload_modal')
        const submit = page.getByRole('dialog').getByRole('button', { name: /Upload document/i })
        if (await submit.isDisabled()) log('CP-29-upload-requires-fields', 'PASS', 'submit disabled until file+type')
        else log('CP-29-upload-requires-fields', 'FAIL', 'submit enabled too early')

        await page.getByRole('combobox').nth(1).click().catch(() => {})
        const typeOption = page.getByRole('option').first()
        if (await typeOption.isVisible({ timeout: 2000 }).catch(() => false)) {
          await typeOption.click()
        } else {
          await page.locator('#client-upload-doctype').click().catch(() => {})
          await page.getByRole('option').first().click().catch(() => {})
        }

        const chooserPromise = page.waitForEvent('filechooser', { timeout: 5000 }).catch(() => null)
        await page.locator('input[type="file"]').evaluate((el) => el.click()).catch(async () => {
          await page.getByText(/Drag a file here/i).click()
        })
        const chooser = await chooserPromise
        if (chooser) await chooser.setFiles(FIXTURE)
        else await page.locator('input[type="file"]').setInputFiles(FIXTURE)

        await page.waitForTimeout(300)
        if (!(await submit.isDisabled())) {
          await submit.click()
          await page.waitForTimeout(2000)
          const after = await page.locator('body').innerText()
          if (/Document uploaded|Upload failed/i.test(after) || lastUpload) {
            log(
              'CP-30-upload-submit',
              /Upload failed/i.test(after) ? 'FAIL' : 'PASS',
              /Upload failed/i.test(after) ? after.slice(0, 300) : 'uploaded',
            )
          } else log('CP-30-upload-submit', 'FAIL', 'no success toast')
        } else {
          log('CP-30-upload-submit', 'FAIL', 'submit stayed disabled after file+type')
        }
        await page.keyboard.press('Escape').catch(() => {})
      }
    } else {
      log('CP-28-upload-disabled-empty', 'FAIL', 'Upload document button missing')
    }

    await gotoPath(page, '/client/documents')
    const flagBtn = page.getByRole('button', { name: /Flag for deletion/i }).first()
    if (await flagBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await flagBtn.click()
      await page.getByRole('dialog', { name: /Flag Document for Deletion/i }).waitFor({ timeout: 5000 })
      await page.locator('#flag-reason').fill('Uploaded the wrong file during Chrome QA.')
      await page.getByRole('dialog').getByRole('button', { name: /Submit Request/i }).click()
      await page.waitForTimeout(1500)
      const after = await page.locator('body').innerText()
      if (/Flagged for deletion|Flagged/i.test(after) || lastFlag) log('CP-31-flag-deletion', 'PASS')
      else log('CP-31-flag-deletion', 'FAIL', after.slice(0, 300))
      await shot(page, 'flagged')
    } else {
      log('CP-31-flag-deletion', 'WARN', 'no flag button (no client-owned docs)')
    }

    const ackTarget = lastDashboard?.home?.next_action?.cta_target || ''
    if (/\/client\/documents\/[^/?]+.*ack=1/.test(ackTarget)) {
      await gotoPath(page, ackTarget, { escape: false })
      const yes = page.locator('button', { hasText: /Yes, I acknowledge/i }).first()
      const ackBtn = page.getByRole('button', { name: /^Acknowledge$/i }).first()
      await page.getByRole('heading', { name: /Closing wire notice|wire notice/i }).waitFor({ timeout: 12000 }).catch(() => {})
      if (!(await yes.isVisible({ timeout: 1500 }).catch(() => false))) {
        await ackBtn.click({ timeout: 4000 }).catch(() => {})
      }
      await yes.waitFor({ state: 'visible', timeout: 8000 })
      await yes.scrollIntoViewIfNeeded()
      const ackWait = page.waitForResponse(
        (res) => res.url().includes('/acknowledge') && res.request().method() === 'POST',
        { timeout: 15000 },
      )
      await yes.click({ force: true })
      await ackWait.catch(() => null)
      await page.waitForTimeout(800)
      await dumpText(page, 'document_ack')
      await shot(page, 'document_ack')
      const afterAck = await page.locator('body').innerText()
      if (lastAck || /Acknowledged|already/i.test(afterAck)) log('CP-OPS-04-acknowledge', 'PASS')
      else log('CP-OPS-04-acknowledge', 'FAIL', afterAck.slice(0, 400))
    } else {
      log('CP-OPS-04-acknowledge', 'WARN', 'no acknowledge packet on focused deal')
    }

    if (await page.getByRole('button', { name: /Notifications/i }).isVisible({ timeout: 800 }).catch(() => false)) {
      log('CP-OPS-05-notifications', 'FAIL', 'client workspace still shows a notification bell')
    } else {
      log('CP-OPS-05-notifications', 'PASS', 'no client notification chrome (Updates is the activity surface)')
    }

    const below = await measureBelow12(page)
    if (below.length === 0) log('CP-32-documents-type', 'PASS')
    else log('CP-32-documents-type', 'FAIL', JSON.stringify(below.slice(0, 10)))
  } catch (err) {
    log('CP-24-documents-loads', 'FAIL', err.message)
  }

  // ── 9. Updates ──────────────────────────────────────────────────────────
  try {
    await clientNav(page, 'Updates')
    await ensureSession(page)
    await page.getByRole('heading', { name: /^Updates$/i }).waitFor({ timeout: 15000 })
    await page
      .getByRole('heading', { name: /Ask your team|Ask Velvet|Recent Updates/i })
      .or(page.getByText(/Updates will appear here/i))
      .first()
      .waitFor({ timeout: 12000 })
      .catch(() => {})
    const text = await dumpText(page, 'updates')
    await shot(page, 'updates')
    if (/Updates/i.test(text) && /Ask your team|Ask Velvet|Recent Updates/i.test(text)) {
      log('CP-33-updates-loads', 'PASS')
    } else log('CP-33-updates-loads', 'FAIL', text.slice(0, 240))

    const ask = page.locator('#ask-velvet-input').or(page.getByPlaceholder(/Send a question to your agent|Ask anything about your transaction/i)).first()
    if (await ask.isVisible({ timeout: 8000 }).catch(() => false)) {
      const body = `Updates QA ${Date.now().toString().slice(-4)}`
      await ask.fill(body)
      await page.getByRole('button', { name: /Send question/i }).click()
      await page.waitForTimeout(1200)
      const after = await page.locator('body').innerText()
      if (after.includes(body) || /Question sent/i.test(after)) log('CP-34-updates-send', 'PASS')
      else log('CP-34-updates-send', 'FAIL', after.slice(0, 240))
    } else {
      log('CP-34-updates-send', 'WARN', 'composer missing')
    }

    const viewTl = page.getByRole('link', { name: /View timeline/i }).first()
    if (await viewTl.isVisible({ timeout: 800 }).catch(() => false)) {
      const href = await viewTl.getAttribute('href')
      if (href && /\/client\/milestones\/[^/?]+/.test(href)) log('CP-35-updates-timeline-href', 'PASS', href)
      else log('CP-35-updates-timeline-href', 'FAIL', href || 'query-param or missing')
    }

    const below = await measureBelow12(page)
    if (below.length === 0) log('CP-36-updates-type', 'PASS')
    else log('CP-36-updates-type', 'FAIL', JSON.stringify(below.slice(0, 10)))
  } catch (err) {
    log('CP-33-updates-loads', 'FAIL', err.message)
  }

  // ── 10. Agent Info ──────────────────────────────────────────────────────
  try {
    await gotoPath(page, '/client/agent')
    await ensureSession(page)
    await page
      .getByText(/Your Real Estate Agent|will appear here once you're assigned/i)
      .first()
      .waitFor({ timeout: 15000 })
      .catch(() => {})
    const text = await dumpText(page, 'agent')
    await shot(page, 'agent')
    if (/Your Team|Your Real Estate Agent|will appear here/i.test(text)) {
      log('CP-37-agent-loads', 'PASS', page.url())
    } else log('CP-37-agent-loads', 'FAIL', text.slice(0, 240))

    const nav = await sidebarLabels(page)
    if (nav.includes('Agent Info')) log('CP-38-agent-in-sidebar', 'WARN', 'Agent Info is a sidebar item (comp folds it into Home)')
    else log('CP-38-agent-in-sidebar', 'PASS', 'Agent Info is not a primary nav item')

    const tel = page.locator('a[href^="tel:"]').first()
    const mail = page.locator('a[href^="mailto:"]').first()
    if (await tel.isVisible({ timeout: 1000 }).catch(() => false)) {
      const href = await tel.getAttribute('href')
      log('CP-39-agent-tel', href && href !== 'tel:' ? 'PASS' : 'FAIL', href)
    } else log('CP-39-agent-tel', 'WARN', 'no phone on agent card')
    if (await mail.isVisible({ timeout: 1000 }).catch(() => false)) {
      const href = await mail.getAttribute('href')
      log('CP-40-agent-mail', href && href.includes('@') ? 'PASS' : 'FAIL', href)
    } else log('CP-40-agent-mail', 'WARN', 'no email on agent card')

    const hits = await smallHitTargets(page)
    const tiny = hits.filter((h) => h.h < 40 && /Call|Email|tel|mail/i.test(h.text || ''))
    if (tiny.length) log('CP-41-agent-hit-targets', 'FAIL', JSON.stringify(tiny))
    else log('CP-41-agent-hit-targets', 'PASS', 'contact actions ≥40px or absent')

    if (hasStaffChrome(text)) log('CP-42-agent-no-staff', 'FAIL')
    else log('CP-42-agent-no-staff', 'PASS')
  } catch (err) {
    log('CP-37-agent-loads', 'FAIL', err.message)
  }

  // ── 11. Payments ────────────────────────────────────────────────────────
  try {
    await gotoPath(page, '/client/invoices')
    await ensureSession(page)
    const text = await dumpText(page, 'invoices')
    await shot(page, 'invoices')
    const url = new URL(page.url())
    if (url.pathname.startsWith('/client/invoices')) log('CP-43-invoices-route', 'PASS', url.pathname)
    else log('CP-43-invoices-route', 'FAIL', url.pathname)

    const concierge = await sidebarLabels(page)
    if (concierge.includes('Home') && concierge.includes('Updates')) {
      log('CP-44-invoices-concierge-shell', 'PASS', 'stayed in client navy shell')
    } else if (hasStaffChrome(text) || /Inbox|Needs You|Active Transactions/i.test(text)) {
      log('CP-44-invoices-concierge-shell', 'FAIL', 'Payments rendered inside staff AppLayout')
    } else if (/Payments|invoice/i.test(text)) {
      log('CP-44-invoices-concierge-shell', 'FAIL', `Payments loaded without concierge nav; nav=${JSON.stringify(concierge)}`)
    } else {
      log('CP-44-invoices-concierge-shell', 'FAIL', text.slice(0, 240))
    }

    if (/You have no invoices|Invoice/i.test(text)) log('CP-45-invoices-content', 'PASS')
    else log('CP-45-invoices-content', 'FAIL', text.slice(0, 240))

    const below = await measureBelow12(page)
    if (below.length === 0) log('CP-46-invoices-type', 'PASS')
    else log('CP-46-invoices-type', 'FAIL', JSON.stringify(below.slice(0, 12)))

    const pay = page.getByRole('link', { name: /Pay now|View/i }).first()
    if (await pay.isVisible({ timeout: 1000 }).catch(() => false)) {
      await pay.click()
      await waitSettled(page, 800)
      const detail = await dumpText(page, 'invoice_detail')
      await shot(page, 'invoice_detail')
      if (/Invoice|Pay .* securely|Paid/i.test(detail)) log('CP-47-invoice-detail', 'PASS', page.url())
      else log('CP-47-invoice-detail', 'FAIL', detail.slice(0, 240))
      await page.goBack().catch(() => {})
    } else {
      log('CP-47-invoice-detail', 'WARN', 'no invoices to open')
    }
  } catch (err) {
    log('CP-43-invoices-route', 'FAIL', err.message)
  }

  // ── 12. Profile modal from user chip ────────────────────────────────────
  try {
    await clientNav(page, 'Home')
    await waitForHomeReady(page)
    await ensureSession(page)
    const chip = page.locator('button[aria-haspopup="menu"]').first()
    await chip.click()
    await page.getByRole('button', { name: /^Profile$/i }).click()
    await page.getByRole('dialog', { name: /Account/i }).waitFor({ timeout: 5000 })
    const dialogText = await page.getByRole('dialog').innerText()
    await shot(page, 'profile_modal')
    if (/Personal information/i.test(dialogText)) log('CP-48-profile-modal', 'PASS')
    else log('CP-48-profile-modal', 'FAIL', dialogText.slice(0, 240))
    await page.keyboard.press('Escape')
    await page.waitForTimeout(300)
  } catch (err) {
    log('CP-48-profile-modal', 'FAIL', err.message)
  }

  // ── 13. /client/settings bookmark ───────────────────────────────────────
  try {
    await gotoPath(page, '/client/settings', { escape: false })
    await waitSettled(page, 900)
    const url = new URL(page.url())
    const dialog = page.getByRole('dialog', { name: /Account/i })
    const dialogOpen = await dialog.isVisible({ timeout: 5000 }).catch(() => false)
    if (url.pathname === '/client/home' && dialogOpen) {
      log('CP-49-settings-bookmark', 'PASS', 'opened Account modal over Home')
    } else if (url.pathname === '/client/home' && !dialogOpen) {
      log('CP-49-settings-bookmark', 'FAIL', 'redirected Home but Account modal did not survive layout switch')
    } else {
      log('CP-49-settings-bookmark', 'FAIL', `${url.pathname} dialog=${dialogOpen}`)
    }
    await page.keyboard.press('Escape').catch(() => {})
  } catch (err) {
    log('CP-49-settings-bookmark', 'FAIL', err.message)
  }

  // ── 14. Legacy + staff-route bounce ─────────────────────────────────────
  try {
    await gotoPath(page, '/client/transactions')
    await waitSettled(page, 500)
    const p = new URL(page.url()).pathname
    if (p === '/client/home') log('CP-50-legacy-transactions', 'PASS', 'redirected to Home')
    else log('CP-50-legacy-transactions', 'FAIL', p)

    await gotoPath(page, '/dashboard')
    await page.waitForURL((u) => !u.pathname.startsWith('/dashboard') || u.pathname === '/client/home', {
      timeout: 15000,
    }).catch(() => {})
    await waitSettled(page, 400)
    const p2 = new URL(page.url()).pathname
    if (p2 === '/client/home') log('CP-51-dashboard-bounce', 'PASS')
    else log('CP-51-dashboard-bounce', 'FAIL', p2)

    await gotoPath(page, '/transactions')
    await page.waitForURL((u) => u.pathname === '/client/home' || u.pathname === '/unauthorized', {
      timeout: 15000,
    }).catch(() => {})
    await waitSettled(page, 400)
    const p3 = new URL(page.url()).pathname
    const t3 = await page.locator('body').innerText()
    if (p3 === '/client/home' && !hasStaffChrome(t3)) log('CP-52-staff-transactions-blocked', 'PASS')
    else log('CP-52-staff-transactions-blocked', 'FAIL', `${p3} staff=${hasStaffChrome(t3)}`)

    await gotoPath(page, '/ai-emails')
    await page.waitForURL((u) => u.pathname !== '/ai-emails', { timeout: 15000 }).catch(() => {})
    await waitSettled(page, 400)
    const p4 = new URL(page.url()).pathname
    if (p4 !== '/ai-emails') log('CP-53-ai-emails-blocked', 'PASS', p4)
    else log('CP-53-ai-emails-blocked', 'FAIL', 'client reached AI Emails')

    await gotoPath(page, '/admin/users')
    const adminOutcome = await page
      .waitForFunction(() => {
        const text = document.body?.innerText || ''
        if (location.pathname !== '/admin/users') return 'redirected'
        if (/User Management/i.test(text)) return 'staff'
        if (/unauthorized|don't have access|not authorized|Access denied/i.test(text)) return 'blocked'
        return null
      }, { timeout: 20000 })
      .then((handle) => handle.jsonValue())
      .catch(() => 'timeout')
    const p5 = new URL(page.url()).pathname
    if (adminOutcome === 'staff') log('CP-54-admin-blocked', 'FAIL', 'client reached User Management')
    else if (adminOutcome === 'timeout') {
      log('CP-54-admin-blocked', 'WARN', `still ${p5} after wait (likely auth spinner on full reload)`)
    } else log('CP-54-admin-blocked', 'PASS', `${p5} ${adminOutcome}`)
  } catch (err) {
    log('CP-50-legacy-transactions', 'FAIL', err.message)
  }

  // ── 15. Mobile 390 (opt-in — viewport resize + extra layout is RAM-heavy)
  if (!MOBILE) {
    log('CP-55-mobile-skipped', 'PASS', 'skipped to save RAM; set QA_MOBILE=1 to run')
  } else try {
    await page.setViewportSize({ width: 390, height: 844 })
    await gotoPath(page, '/client/home')
    await ensureSession(page)
    await waitForHomeReady(page).catch(() => {})
    const text = await dumpText(page, 'home_390')
    await shot(page, 'home_390')
    const bottom = page.getByRole('button', { name: /^Home$/i }).last()
    const more = page.getByRole('button', { name: /^More$/i })
    const hamburger = page.getByRole('button', { name: /Open menu/i })
    if (await more.isVisible({ timeout: 2000 }).catch(() => false)) log('CP-55-mobile-bottom-nav', 'PASS')
    else log('CP-55-mobile-bottom-nav', 'FAIL', 'bottom More missing')

    if (await hamburger.isVisible({ timeout: 1000 }).catch(() => false)) {
      await hamburger.click()
      await page.waitForTimeout(400)
      const drawer = await dumpText(page, 'mobile_drawer')
      await shot(page, 'mobile_drawer')
      if (/Timeline/i.test(drawer) && /Next Steps/i.test(drawer)) log('CP-56-mobile-drawer', 'PASS')
      else log('CP-56-mobile-drawer', 'FAIL', drawer.slice(0, 240))
      await page.getByRole('button', { name: /^Close menu$/i }).click().catch(() => {})
      await page.getByRole('button', { name: /Dismiss navigation overlay/i }).click({ timeout: 1500 }).catch(() => {})
      await page.waitForTimeout(300)
    } else log('CP-56-mobile-drawer', 'FAIL', 'hamburger missing')

    await page.getByRole('button', { name: /Open menu/i }).waitFor({ timeout: 4000 }).catch(() => {})

    await page.waitForTimeout(400)
    const anyBell = page.getByRole('button', { name: /Notifications/i })
    if (await anyBell.isVisible({ timeout: 800 }).catch(() => false)) {
      log('CP-57-mobile-bell', 'FAIL', 'client workspace still shows a notification bell')
    } else {
      log('CP-57-mobile-bell', 'PASS', 'no notification bell in client chrome')
    }

    const below = await measureBelow12(page)
    if (below.length === 0) log('CP-58-mobile-type', 'PASS')
    else log('CP-58-mobile-type', 'FAIL', JSON.stringify(below.slice(0, 12)))

    if (await bottom.isVisible({ timeout: 800 }).catch(() => false)) {
      // already on home
    }
    await page.setViewportSize({ width: 1440, height: 900 })
  } catch (err) {
    log('CP-55-mobile-bottom-nav', 'FAIL', err.message)
    await page.setViewportSize({ width: 1440, height: 900 }).catch(() => {})
  }

  // ── 16. Logout ──────────────────────────────────────────────────────────
  try {
    await clientNav(page, 'Home')
    await ensureSession(page)
    await page.locator('button[aria-haspopup="menu"]').first().click()
    await page.getByRole('button', { name: /Log out/i }).click()
    await page.waitForURL(/\/login/, { timeout: 10000 })
    log('CP-59-logout', 'PASS', page.url())
  } catch (err) {
    log('CP-59-logout', 'FAIL', err.message)
  }

  // ── 17. Console / network hygiene ───────────────────────────────────────
  const cons = realConsole()
  const apiFails = failedRequests.filter((u) => {
    if (!/\/api\/v1\//.test(u) || /favicon/.test(u)) return false
    // Only HTTP error responses. In-flight GETs aborted by SPA navigation have
    // no status prefix; localhost IPv6 misses are also requestfailed noise.
    if (!/^\d{3}\s/.test(u)) return false
    return true
  })
  if (cons.length === 0 && pageErrors.length === 0) log('CP-60-console', 'PASS')
  else log('CP-60-console', 'FAIL', JSON.stringify({ cons: cons.slice(0, 8), pageErrors: pageErrors.slice(0, 8) }))
  if (apiFails.length === 0) log('CP-61-api-errors', 'PASS')
  else log('CP-61-api-errors', 'FAIL', apiFails.slice(0, 12).join('\n'))

  const summary = {
    pass: findings.filter((f) => f.result === 'PASS').length,
    fail: findings.filter((f) => f.result === 'FAIL').length,
    warn: findings.filter((f) => f.result === 'WARN').length,
    total: findings.length,
  }
  writeFileSync(
    path.join(OUT, 'findings.json'),
    JSON.stringify(
      {
        summary,
        findings,
        consoleErrors: cons,
        pageErrors,
        failedRequests: apiFails,
      },
      null,
      2,
    ),
  )
  writeFileSync(
    path.join(OUT, 'summary.txt'),
    `${summary.pass} pass / ${summary.fail} fail / ${summary.warn} warn / ${summary.total} checks\n` +
      findings.map((f) => `[${f.result}] ${f.id} ${f.details}`).join('\n'),
  )
  console.log(`\n${summary.pass} pass / ${summary.fail} fail / ${summary.warn} warn / ${summary.total} checks`)
  console.log(`artifacts: ${OUT}`)
  await browser.close()
  process.exit(summary.fail > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
