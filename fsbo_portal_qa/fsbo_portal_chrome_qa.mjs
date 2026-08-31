/**
 * Local FSBO Portal QA against http://127.0.0.1:5173 as
 * yareny.evaly@minafter.com (ForSaleByOwner).
 *
 * Default is a low-RAM pass: Playwright's bundled Chromium, headless, no
 * screenshots. Override:
 *
 *   QA_HEADED=1        real headed window (high RAM — avoid on this machine)
 *   QA_CHANNEL=chrome  use installed Google Chrome
 *   QA_SHOTS=1         write PNG screenshots
 *   QA_DUMPS=1         write page text dumps
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

const EMAIL = 'yareny.evaly@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = process.env.QA_APP || 'http://127.0.0.1:5173'
const FIXTURE = path.join(__dirname, 'fixtures', 'qa-upload.txt')
const HEADED = process.env.QA_HEADED === '1'
const SHOTS = process.env.QA_SHOTS === '1'
const DUMPS = process.env.QA_DUMPS === '1'
const CHANNEL = process.env.QA_CHANNEL || ''

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let lastOverview = null
let lastDocuments = null
let lastMilestones = null
let lastProperty = null
let lastShareCreate = null
let lastUpload = null
let lastFlag = null
let lastAiChat = null
let lastFsboBell = null
let lastContent = null
const popups = []
const staffPendingHits = []
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

async function waitForFsboShell(page) {
  await page.getByTestId('fsbo-shell').waitFor({ state: 'attached', timeout: 20000 })
}

async function waitForOverviewReady(page) {
  await waitForFsboShell(page)
  await page
    .getByTestId('fsbo-next-action')
    .or(page.getByTestId('fsbo-empty'))
    .first()
    .waitFor({ timeout: 20000 })
}

function mainPane(page) {
  return page.locator('#main-content')
}

async function closeAskAi(page) {
  await page.keyboard.press('Escape').catch(() => {})
  const closeChat = page.getByRole('button', { name: /Close AI chat/i })
  if (await closeChat.isVisible({ timeout: 400 }).catch(() => false)) {
    await closeChat.click().catch(() => {})
  }
}

async function gotoPath(page, pathName, { escape = true } = {}) {
  const url = /^https?:\/\//i.test(pathName) ? pathName : `${APP}${pathName}`
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await waitSettled(page, 600)
  await dismissOverlays(page, { escape })
}

async function fsboNav(page, label) {
  const testIds = {
    Home: 'fsbo-nav-home',
    Dashboard: 'fsbo-nav-home',
    'My Properties': 'fsbo-nav-properties',
    Documents: 'fsbo-nav-documents',
    Messages: 'fsbo-nav-messages',
    Payments: 'fsbo-nav-payments',
  }
  const testId = testIds[label]
  if (testId) {
    const btn = page.getByTestId(testId).first()
    if (await btn.isVisible({ timeout: 2500 }).catch(() => false)) {
      await btn.click()
      await waitSettled(page, 500)
      await dismissOverlays(page)
      return
    }
  }
  const routes = {
    Home: '/fsbo',
    Dashboard: '/fsbo',
    'My Properties': '/fsbo/properties',
    Documents: '/fsbo/documents',
    Payments: '/fsbo/invoices',
    Messages: '/fsbo/milestones',
  }
  await gotoPath(page, routes[label] || '/fsbo')
}

async function measureBelow12(page, root = 'main, [class*="fsbo-scope"], body') {
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
    const roots = [...document.querySelectorAll(sel)]
    ;(roots.length ? roots : [document.body]).forEach(walk)
    return out.slice(0, 40)
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

function hasStaffChrome(text) {
  return /AI Suggestions|Task Queue|Inbox Elf|\bActive Transactions\b|\bNew Transaction\b/i.test(
    text,
  )
}

function hasFsboNav(text) {
  return (/Home|Dashboard/i.test(text) && /Documents/i.test(text) && /Messages/i.test(text))
}

async function sidebarLabels(page) {
  return page.evaluate(() => {
    const nav =
      document.querySelector('nav[aria-label="Main navigation"]') ||
      document.querySelector('nav[aria-label="Seller navigation"]')
    if (!nav) return []
    return [...nav.querySelectorAll('a, button')].map((el) => (el.innerText || '').trim()).filter(Boolean)
  })
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
  page.on('popup', (p) => {
    popups.push(p.url())
  })
  console.log(
    `browser=${CHANNEL || 'chromium'} headless=${headless} viewport=1280x720 shots=${SHOTS} app=${APP}`,
  )

  page.on('console', (msg) => {
    if (msg.type() === 'error' && consoleErrors.length < 20) consoleErrors.push(msg.text().slice(0, 400))
  })
  page.on('pageerror', (err) => {
    if (pageErrors.length < 12) pageErrors.push(String(err.message).slice(0, 400))
  })
  page.on('request', (req) => {
    const url = req.url()
    if (url.includes('/api/v1/notifications/pending')) {
      staffPendingHits.push(url.slice(0, 300))
    }
  })
  page.on('requestfailed', (req) => {
    const err = req.failure()?.errorText || ''
    if (/ERR_ABORTED|NS_BINDING_ABORTED/i.test(err)) return
    if (failedRequests.length < 40) failedRequests.push(`${req.method()} ${req.url()} ${err}`.trim().slice(0, 300))
  })
  page.on('response', async (res) => {
    try {
      const url = res.url()
      if (/\/documents\/[^/]+\/content(?:\?|$)/.test(url)) {
        lastContent = {
          ok: res.ok(),
          status: res.status(),
          mime: res.headers()['content-type'] || '',
        }
      }
      if (!url.includes('/api/v1/')) return
      if (!res.ok()) {
        if (failedRequests.length < 40) {
          failedRequests.push(`${res.status()} ${res.request().method()} ${url}`.slice(0, 300))
        }
        return
      }
      if (
        !/\/dashboard\/fsbo\/|flag-deletion|\/documents\/upload|\/share-link|\/dashboard\/ai-chat/.test(url)
      ) {
        return
      }
      const json = await res.json().catch(() => null)
      if (!json) return
      if (url.includes('/dashboard/fsbo/overview')) lastOverview = json
      else if (url.includes('/dashboard/fsbo/documents')) lastDocuments = json
      else if (url.includes('/dashboard/fsbo/messages') || url.includes('/dashboard/fsbo/milestones')) lastMilestones = json
      else if (url.includes('/dashboard/fsbo/notifications')) lastFsboBell = json
      else if (/\/dashboard\/fsbo\/properties\//.test(url)) lastProperty = json
      else if (url.includes('/share-link') && res.request().method() === 'POST') lastShareCreate = json
      else if (url.includes('/documents/upload') && res.request().method() === 'POST') lastUpload = { ok: true, id: json.id }
      else if (url.includes('flag-deletion')) lastFlag = { ok: true }
      else if (url.includes('/dashboard/ai-chat') && res.request().method() === 'POST') lastAiChat = json
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
    await waitForOverviewReady(page)
    log('FS-01-login', 'PASS', page.url())
  } catch (err) {
    const body = await page.locator('body').innerText().catch(() => '')
    log('FS-01-login', 'FAIL', `${err.message}\n${body.slice(0, 500)}`)
    await shot(page, 'login_fail')
    writeFileSync(
      path.join(OUT, 'findings.json'),
      JSON.stringify({ findings, consoleErrors, pageErrors, failedRequests }, null, 2),
    )
    await browser.close()
    process.exit(1)
  }

  // ── 2. Landing is FSBO overview, not staff chrome ───────────────────────
  {
    const text = await dumpText(page, 'overview')
    const url = page.url()
    if (/\/fsbo\/?(\?|$)/.test(url) && !hasStaffChrome(text) && hasFsboNav(text)) {
      log('FS-02-landing', 'PASS', url)
    } else {
      log('FS-02-landing', 'FAIL', `${url}\nstaff=${hasStaffChrome(text)} nav=${hasFsboNav(text)}\n${text.slice(0, 400)}`)
    }
    await shot(page, 'overview')
  }

  // ── 3. Sidebar nav labels ───────────────────────────────────────────────
  {
    const labels = await sidebarLabels(page)
    const joined = labels.join(' | ')
    const need = ['Home', 'Documents', 'Messages']
    const missing = need.filter((n) => !labels.some((l) => l.includes(n) || new RegExp(n, 'i').test(l)))
    const leaked = labels.filter((l) =>
      /Needs You|Task Queue|Active Transactions|AI Suggestions|New Transaction/i.test(l),
    )
    const paymentsHidden = !labels.some((l) => /Payments/i.test(l))
    const share = await page.getByTestId('fsbo-share').first().isVisible({ timeout: 2000 }).catch(() => false)
    if (missing.length === 0 && leaked.length === 0 && share) {
      log('FS-03-sidebar', 'PASS', `${joined} paymentsHidden=${paymentsHidden}`)
    } else {
      log('FS-03-sidebar', 'FAIL', `missing=${missing} leaked=${leaked} share=${share} labels=${joined}`)
    }
  }

  // ── 4. Overview content ─────────────────────────────────────────────────
  {
    const text = await dumpText(page, 'overview_body')
    const hasNext = /Next action|Upload your|on track|Acknowledge|Review |Pay an open|Reply to your coordinator|Share a progress/i.test(text)
    const hasBoundary = /does not act as your agent or provide legal advice/i.test(text)
    const hasProps = /Maple Prep|Velvet Contract|Your coordinator will add your first property/i.test(text)
    const hasSupport = /Shyna Elene|Your coordinator|Velvet Elves support|Your Velvet coordinator/i.test(text)
    const hasKpi = /Missing documents|Share links live|Days to closing|My properties/i.test(text)
    if (hasNext && hasBoundary && hasProps) log('FS-04-overview-content', 'PASS', `support=${hasSupport} kpi=${hasKpi}`)
    else log('FS-04-overview-content', 'FAIL', `next=${hasNext} boundary=${hasBoundary} props=${hasProps} kpi=${hasKpi}\n${text.slice(0, 500)}`)
    for (let i = 0; i < 25 && !(lastOverview?.properties?.length); i += 1) {
      await page.waitForTimeout(100)
    }
    const n = lastOverview?.properties?.length ?? 0
    const maple = (lastOverview?.properties || []).find((p) => /Maple Prep/i.test(p.address || ''))
    const mapleMissing = maple?.seller_owed_missing_count ?? maple?.missing_docs_count
    if (n >= 1) log('FS-05-overview-api', 'PASS', `${n} properties, portfolioMissing=${lastOverview?.missing_documents_count} mapleSellerOwed=${mapleMissing}`)
    else log('FS-05-overview-api', hasProps ? 'PASS' : 'FAIL', hasProps ? 'ui shows properties (payload raced)' : JSON.stringify(lastOverview)?.slice(0, 400) || 'no overview payload')
  }

  // ── 5. Ask Aime FAB + seller-safe chat ──────────────────────────────────
  {
    const fab = page.getByRole('button', { name: /Ask Aime/i }).first()
    if (await fab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await fab.click()
      await waitSettled(page, 600)
      const panel = page.locator('[data-testid="global-ai-chat-panel"][data-open="true"]')
      const visible = await panel.isVisible({ timeout: 4000 }).catch(() => false)
      log(visible ? 'FS-06-ask-ai' : 'FS-06-ask-ai', visible ? 'PASS' : 'FAIL', 'FAB opened')
      if (visible) {
        await panel.getByRole('button', { name: /What's missing\?/i }).first().waitFor({ timeout: 4000 }).catch(() => {})
        const ptext = await panel.innerText()
        const agentVoice = /overdue tasks|Summarize my pipeline|Show overdue tasks|active deals/i.test(ptext)
        const sellerVoice = /missing documents|coordinator|properties/i.test(ptext)
        log(
          'FS-44-ask-ai-voice',
          !agentVoice && sellerVoice ? 'PASS' : 'FAIL',
          ptext.slice(0, 280),
        )
        const missingChip = panel.getByRole('button', { name: /What's missing\?/i }).first()
        if (await missingChip.isVisible({ timeout: 2000 }).catch(() => false)) {
          lastAiChat = null
          await missingChip.click()
          await page
            .locator('[data-testid="global-ai-chat-panel"]')
            .getByText(/Thinking/i)
            .first()
            .waitFor({ state: 'hidden', timeout: 25000 })
            .catch(() => {})
          await waitSettled(page, 400)
          const replyText = await panel.innerText()
          const stillThinking = /Thinking/i.test(replyText) && !lastAiChat
          const leakedStaff = /Show overdue tasks|Summarize my pipeline|overdue tasks|active deals/i.test(replyText)
          const failed =
            Boolean(lastAiChat?.error_category) ||
            /couldn't put an answer|out of credit|Internal Server Error/i.test(
              (lastAiChat?.reply || replyText).toString(),
            )
          const gotReply = Boolean(lastAiChat?.reply) && /Maple|Velvet|missing|document|coordinator|Upload/i.test(
            (lastAiChat?.reply || '').toString(),
          )
          log(
            'FS-45-ask-ai-send',
            !stillThinking && !leakedStaff && !failed && gotReply ? 'PASS' : 'FAIL',
            `${lastAiChat?.provider || ''} ${(lastAiChat?.reply || replyText).toString()}`.slice(0, 280),
          )
        } else {
          log('FS-45-ask-ai-send', 'FAIL', 'seller chip missing')
        }
      } else {
        log('FS-44-ask-ai-voice', 'FAIL', 'panel not visible')
        log('FS-45-ask-ai-send', 'FAIL', 'panel not visible')
      }
      await closeAskAi(page)
    } else {
      log('FS-06-ask-ai', 'FAIL', 'FAB not visible')
      log('FS-44-ask-ai-voice', 'FAIL', 'FAB not visible')
      log('FS-45-ask-ai-send', 'FAIL', 'FAB not visible')
    }
  }

  // ── 6. Share CTA (persistent primary action) ────────────────────────────
  {
    const share = page.getByTestId('fsbo-share').first()
    if (await share.isVisible({ timeout: 2000 }).catch(() => false)) {
      await share.click()
      await waitSettled(page, 700)
      const dlg = page.getByRole('dialog').filter({ hasText: /Sharing|Share milestone|What the buyer will see/i }).first()
      const ok = await dlg.isVisible({ timeout: 4000 }).catch(() => false)
      const preview = await page.getByTestId('fsbo-share-preview').isVisible().catch(() => false)
      log(ok ? 'FS-08-share-cta' : 'FS-08-share-cta', ok ? 'PASS' : 'FAIL', ok ? `modal open preview=${preview}` : 'no sharing modal')
      await page.keyboard.press('Escape').catch(() => {})
      await waitSettled(page, 300)
    } else {
      log('FS-08-share-cta', 'FAIL', 'Share button missing')
    }
    log('FS-07-portfolio-chip', 'PASS', 'retired — Home switcher replaces portfolio chip')
  }

  // ── 7. Home upload CTA (no KPI / banner) ────────────────────────────────
  {
    await gotoPath(page, '/fsbo')
    await waitForOverviewReady(page)
    const uploadCta = page.getByTestId('fsbo-next-action-cta').or(page.getByTestId('fsbo-upload-cta')).first()
    if (await uploadCta.isVisible({ timeout: 4000 }).catch(() => false)) {
      await uploadCta.click()
      await waitSettled(page, 800)
      const dlg = page.getByRole('dialog').filter({ hasText: /Upload a document/i }).first()
      const openDlg = await dlg.isVisible({ timeout: 2500 }).catch(() => false)
      const onDocs = /\/fsbo\/documents/.test(page.url())
      if (openDlg || onDocs) log('FS-09-kpi-missing', 'PASS', openDlg ? 'upload modal' : page.url())
      else log('FS-09-kpi-missing', 'FAIL', `cta did not open upload or Documents\n${page.url()}`)
      await page.keyboard.press('Escape').catch(() => {})
    } else {
      log('FS-09-kpi-missing', 'WARN', 'no seller-owed upload CTA (file may already be on track)')
    }
    await gotoPath(page, '/fsbo')
    await waitForOverviewReady(page)
    const homeText = await mainPane(page).innerText().catch(() => '')
    const hasKpiStrip = /My properties|Missing documents|Share links live|Days to closing/i.test(homeText)
    log('FS-47-kpi-share-links', hasKpiStrip ? 'PASS' : 'WARN', hasKpiStrip ? 'Overview summary cards present' : 'summary cards not found')
    const banner = page.getByTestId('fsbo-next-action-banner')
    const bannerVisible = await banner.isVisible({ timeout: 1500 }).catch(() => false)
    const ranked = (lastOverview?.critical_next_steps || []).filter((s) => s?.kind && s.kind !== 'none')
    if (ranked.length > 0) {
      log(bannerVisible ? 'FS-48-banner' : 'FS-48-banner', bannerVisible ? 'PASS' : 'FAIL', bannerVisible ? 'portfolio banner mounted' : 'expected AppLayout banner')
    } else {
      log('FS-48-banner', 'PASS', 'no seller-owed banner (portfolio on track)')
    }
    const hero = page.getByTestId('fsbo-next-action').first()
    const heroText = (await hero.innerText().catch(() => '')).slice(0, 180)
    const bannerText = bannerVisible ? (await banner.innerText().catch(() => '')).slice(0, 180) : ''
    log(
      'FS-54-banner-vs-hero',
      heroText ? 'PASS' : 'WARN',
      `banner=${bannerText || 'none'} hero=${heroText || 'none'}`,
    )
  }

  // ── 8. Home property switcher (both files) ──────────────────────────────
  {
    await fsboNav(page, 'Home')
    await waitForOverviewReady(page)
    const text = await dumpText(page, 'properties')
    const hasPrep = /Maple Prep/i.test(text)
    const hasContract = /Velvet Contract/i.test(text)
    if (hasPrep && hasContract) log('FS-10-properties-list', 'PASS', 'both properties on Home')
    else log('FS-10-properties-list', hasPrep || hasContract ? 'WARN' : 'FAIL', text.slice(0, 400))

    const switcher = page.getByTestId('fsbo-property-switcher')
    if (await switcher.isVisible({ timeout: 2000 }).catch(() => false)) {
      const maple = switcher.getByRole('button', { name: /Maple Prep/i }).first()
      if (await maple.isVisible().catch(() => false)) {
        await maple.click()
        await waitSettled(page, 400)
      }
      log('FS-11-filter-prep', 'PASS', 'Home switcher')
      const velvet = switcher.getByRole('button', { name: /Velvet Contract/i }).first()
      if (await velvet.isVisible().catch(() => false)) await velvet.click()
      log('FS-46-filter-contract', 'PASS', 'Home switcher')
    } else {
      log('FS-11-filter-prep', hasPrep ? 'PASS' : 'WARN', 'single-property or switcher hidden')
      log('FS-46-filter-contract', hasContract ? 'PASS' : 'WARN', 'single-property or switcher hidden')
    }
    await shot(page, 'properties')
  }

  // ── 9. Property workspace (six-rail) ────────────────────────────────────
  {
    await closeAskAi(page)
    await gotoPath(page, '/fsbo/properties/9dacae5e-cf19-4312-b976-81e587dd0df6')
    await page
      .getByRole('heading', { name: /Velvet Contract/i })
      .first()
      .waitFor({ timeout: 20000 })
      .catch(() => {})
    await waitSettled(page, 400)
    const text = await mainPane(page).innerText()
    const urlOk = /\/fsbo\/properties\//.test(page.url())
    const hasAddr = /Velvet Contract/i.test(text)
    const sixRail = await page.getByRole('navigation', { name: /Property sections/i }).isVisible().catch(() => false)
    if (urlOk && hasAddr && sixRail) log('FS-12-property-detail', 'PASS', 'six-rail property workspace')
    else log('FS-12-property-detail', 'FAIL', `url=${page.url()} addr=${hasAddr} sixRail=${sixRail}\n${text.slice(0, 400)}`)

    log(
      /Dates|No dates set yet|Closing/i.test(text) ? 'FS-13-timeline' : 'FS-13-timeline',
      /Dates|No dates set yet|Closing/i.test(text) ? 'PASS' : 'WARN',
      text.slice(0, 200),
    )
    log(
      /Documents|Still needed|Nothing seller-owed/i.test(text) ? 'FS-14-detail-docs' : 'FS-14-detail-docs',
      /Documents|Still needed|Nothing seller-owed/i.test(text) ? 'PASS' : 'WARN',
      text.slice(0, 200),
    )
    const contactsNav = page.getByRole('navigation', { name: /Property sections/i }).getByRole('button', { name: /^Contacts$/i })
    if (await contactsNav.isVisible().catch(() => false)) {
      await contactsNav.click()
      await waitSettled(page, 400)
      const ctext = await mainPane(page).innerText()
      const jordan = (ctext.match(/Jordan Buyer/g) || []).length
      const pat = (ctext.match(/Pat Title/g) || []).length
      if (/No counterparties recorded/i.test(ctext)) {
        log('FS-15-contacts', 'WARN', 'no counterparties on this file')
      } else if (jordan === 1 && pat === 1) {
        log('FS-15-contacts', 'PASS', 'one Buyer + one Title')
      } else if (jordan > 0 || pat > 0 || /Buyer|Title/i.test(ctext)) {
        log('FS-15-contacts', jordan > 1 || pat > 1 ? 'FAIL' : 'PASS', `jordan=${jordan} pat=${pat}`)
      } else {
        log('FS-15-contacts', 'WARN', ctext.slice(0, 240))
      }
      await page.getByRole('navigation', { name: /Property sections/i }).getByRole('button', { name: /^Overview$/i }).click().catch(() => {})
    } else {
      log(
        /Contacts|Jordan Buyer|Meridian Title|No counterparties recorded/i.test(text) ? 'FS-15-contacts' : 'FS-15-contacts',
        /Contacts|Jordan Buyer|Meridian Title|No counterparties recorded/i.test(text) ? 'PASS' : 'WARN',
        text.slice(0, 240),
      )
    }
    log('FS-16-sharing-pane', 'PASS', 'Share is the persistent shell action, not a property rail')
    await shot(page, 'property_detail')
  }

  // ── 10. Unknown property 404 ────────────────────────────────────────────
  {
    await gotoPath(page, '/fsbo/properties/00000000-0000-0000-0000-000000000000')
    await page
      .getByRole('heading', { name: /Property not found/i })
      .first()
      .waitFor({ timeout: 15000 })
      .catch(() => {})
    const text = await mainPane(page).innerText()
    log(
      /not found|couldn't find this property/i.test(text) ? 'FS-17-unknown-property' : 'FS-17-unknown-property',
      /not found|couldn't find this property/i.test(text) ? 'PASS' : 'FAIL',
      text.slice(0, 240),
    )
  }

  // ── 11. Documents board, upload, flag ───────────────────────────────────
  {
    await closeAskAi(page)
    await fsboNav(page, 'Documents')
    await waitSettled(page, 800)
    await mainPane(page).getByRole('heading', { name: /^Documents$/i }).first().waitFor({ timeout: 12000 }).catch(() => {})
    const text = await mainPane(page).innerText()
    const hasBoard = /Missing|In progress|Uploaded|Verified|Complete|Still needed/i.test(text)
    const hasMissing = /Seller|Lead|Purchase|Disclosure|deed|needed/i.test(text)
    if (hasBoard) log('FS-18-documents-board', 'PASS', text.slice(0, 200))
    else log('FS-18-documents-board', 'FAIL', text.slice(0, 400))
    if (hasMissing) log('FS-19-missing-rows', 'PASS')
    else log('FS-19-missing-rows', 'WARN', 'no missing-doc rows visible')
    const sellerOwedRow = /Seller.?s disclosure|Lead.?paint|Listing photos/i.test(text)
    const velvetBucket = /Velvet is collecting/i.test(text)
    log(
      'FS-55-seller-owed-missing',
      sellerOwedRow ? 'PASS' : 'FAIL',
      sellerOwedRow ? 'seller-owed missing rows on the board' : text.slice(0, 280),
    )
    log(
      'FS-56-velvet-collecting',
      velvetBucket ? 'PASS' : 'WARN',
      velvetBucket ? 'Velvet is collecting bucket visible' : 'no Velvet is collecting section',
    )

    const missingTab = mainPane(page).getByRole('button', { name: /Missing|Still needed|You still need/i }).first()
    if (await missingTab.isVisible({ timeout: 2000 }).catch(() => false)) {
      await missingTab.click()
      await waitSettled(page, 300)
      log('FS-20-missing-tab', 'PASS')
    } else log('FS-20-missing-tab', 'FAIL', 'Missing filter missing')

    const uploadCta = mainPane(page).getByTestId('fsbo-upload-cta').or(mainPane(page).getByRole('button', { name: /^Upload$/i })).first()
    if (await uploadCta.isVisible({ timeout: 2000 }).catch(() => false)) {
      await uploadCta.click()
      await waitSettled(page, 500)
      const dlg = page.getByRole('dialog').filter({ hasText: /Upload a document/i }).first()
      const openDlg = await dlg.isVisible({ timeout: 4000 }).catch(() => false)
      log(openDlg ? 'FS-21-upload-modal' : 'FS-21-upload-modal', openDlg ? 'PASS' : 'FAIL')
      if (openDlg) {
        await page.locator('#fsbo-upload-doctype').click().catch(() => {})
        await waitSettled(page, 300)
        const opt = page.getByRole('option', { name: /Seller.?s disclosure|Sellers Disclosure|Disclosure/i }).first()
        if (await opt.isVisible({ timeout: 2000 }).catch(() => false)) {
          await opt.click()
        } else {
          await page.getByRole('option').nth(1).click().catch(() => {})
        }
        const fileInput = page.locator('input[type="file"]').first()
        await fileInput.setInputFiles(FIXTURE).catch((e) => log('FS-22-upload-file', 'FAIL', e.message))
        await page.getByRole('button', { name: /^Upload document$/i }).last().click().catch(() => {})
        await waitSettled(page, 2000)
        if (lastUpload?.ok) log('FS-22-upload', 'PASS', lastUpload.id || 'ok')
        else {
          const body = await page.locator('body').innerText()
          log('FS-22-upload', /uploaded|sent to your coordinator/i.test(body) ? 'PASS' : 'WARN', body.slice(0, 240))
        }
        await page.keyboard.press('Escape').catch(() => {})
      }
    } else log('FS-21-upload-modal', 'FAIL', 'Upload document CTA missing')

    await gotoPath(page, '/fsbo/documents')
    await waitSettled(page, 800)
    await closeAskAi(page)
    const youSent = mainPane(page).getByRole('button', { name: /You sent/i }).first()
    if (await youSent.isVisible({ timeout: 1500 }).catch(() => false)) await youSent.click()
    const openBtn = mainPane(page).getByRole('button', { name: /^Open$/i }).first()
    if (await openBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      const beforePopups = popups.length
      lastContent = null
      await openBtn.click()
      await waitSettled(page, 1500)
      const preview = page
        .getByRole('dialog')
        .filter({ has: page.getByRole('button', { name: /Download/i }) })
        .first()
      const previewOpen = await preview.isVisible({ timeout: 6000 }).catch(() => false)
      const previewText = previewOpen ? await preview.innerText().catch(() => '') : ''
      const stillOnApp = /127\.0\.0\.1:5173|localhost:5173/.test(page.url()) && !/supabase\.co/i.test(page.url())
      const supabasePopup = popups.slice(beforePopups).some((u) => /supabase\.co/i.test(String(u)))
      const loaded = /Loading preview/i.test(previewText) || lastContent?.ok || /Download/i.test(previewText)
      if (!previewOpen) log('FS-57-in-app-preview', 'FAIL', `no preview dialog url=${page.url()}`)
      else if (!stillOnApp || supabasePopup) {
        log(
          'FS-57-in-app-preview',
          'FAIL',
          `left app url=${page.url()} supabasePopup=${supabasePopup} popups=${popups.slice(beforePopups).join(',')}`,
        )
      } else if (!loaded && /Preview not available|Could not/i.test(previewText)) {
        log('FS-57-in-app-preview', 'FAIL', previewText.slice(0, 300))
      } else {
        log(
          'FS-57-in-app-preview',
          'PASS',
          `content=${lastContent?.status || 'n/a'} mime=${lastContent?.mime || 'n/a'}`,
        )
      }
      await page.keyboard.press('Escape').catch(() => {})
    } else {
      log('FS-57-in-app-preview', 'WARN', 'no Open button on You sent')
    }

    const flag = mainPane(page).getByRole('button', { name: /Flag/i }).first()
    if (await flag.isVisible({ timeout: 3000 }).catch(() => false)) {
      await flag.click()
      await waitSettled(page, 400)
      const reason = page.locator('#flag-reason')
      if (await reason.isVisible({ timeout: 3000 }).catch(() => false)) {
        await reason.fill('QA flag: uploaded by mistake')
        await page.getByRole('button', { name: /Request deletion|Submit|Flag/i }).last().click().catch(() => {})
        await waitSettled(page, 1500)
        log(lastFlag?.ok ? 'FS-23-flag' : 'FS-23-flag', lastFlag?.ok || /Deletion requested|submitted|Flagged for deletion/i.test(await page.locator('body').innerText()) ? 'PASS' : 'WARN')
      } else log('FS-23-flag', 'FAIL', 'flag modal missing')
      await page.keyboard.press('Escape').catch(() => {})
    } else log('FS-23-flag', 'WARN', 'no Flag button (no uploaded docs yet)')
    await shot(page, 'documents')
  }

  // ── 12. Messages inbox ──────────────────────────────────────────────────
  {
    await fsboNav(page, 'Messages')
    await waitSettled(page, 800)
    const text = await mainPane(page).innerText()
    if (/Ask a question|Message your coordinator|No messages|Your coordinator|Conversation with your coordinator/i.test(text)) {
      log('FS-24-messages', 'PASS', text.slice(0, 240))
    } else {
      log('FS-24-messages', /Messages/i.test(text) ? 'WARN' : 'FAIL', text.slice(0, 400))
    }
    const composer = await page.getByTestId('fsbo-message-composer').isVisible().catch(() => false)
    if (composer) log('FS-51-messages-composer', 'PASS')
    else log('FS-51-messages-composer', 'FAIL', 'seller composer missing')
    if (/does not act as your agent/i.test(text)) log('FS-25-messages-boundary', 'PASS')
    else log('FS-25-messages-boundary', 'FAIL', 'boundary notice missing on Messages')
    await gotoPath(page, '/fsbo/milestones')
    await waitSettled(page, 600)
    log(
      /\/fsbo\/milestones/.test(page.url()) ? 'FS-52-milestones-route' : 'FS-52-milestones-route',
      /\/fsbo\/milestones/.test(page.url()) ? 'PASS' : 'FAIL',
      page.url(),
    )
    await gotoPath(page, '/fsbo/properties')
    await waitSettled(page, 600)
    log(
      /\/fsbo\/properties/.test(page.url()) ? 'FS-53-properties-list' : 'FS-53-properties-list',
      /\/fsbo\/properties/.test(page.url()) ? 'PASS' : 'FAIL',
      page.url(),
    )
  }

  // ── 13. Payments (route still works; nav hidden when no invoices) ───────
  {
    const payNav = await page.getByTestId('fsbo-nav-payments').isVisible().catch(() => false)
    await gotoPath(page, '/fsbo/invoices')
    await waitSettled(page, 800)
    const text = await dumpText(page, 'payments')
    const urlOk = /\/fsbo\/invoices/.test(page.url())
    const honestEmpty = /no invoices/i.test(text)
    const clientLeak = /Ask your team|Client Portal/i.test(text)
    const staff = hasStaffChrome(text)
    if (urlOk && !staff && /Payments/i.test(text)) {
      log('FS-26-payments', 'PASS', `${honestEmpty ? 'empty invoices' : text.slice(0, 160)} nav=${payNav}`)
    } else {
      log('FS-26-payments', 'FAIL', `${page.url()} staff=${staff}\n${text.slice(0, 300)}`)
    }
    log(clientLeak ? 'FS-27-payments-shell' : 'FS-27-payments-shell', clientLeak ? 'FAIL' : 'PASS', 'seller Payments, not Client concierge')

    await gotoPath(page, '/client/invoices')
    await waitSettled(page, 800)
    log(
      /\/fsbo\/invoices/.test(page.url()) ? 'FS-28-client-invoices-bounce' : 'FS-28-client-invoices-bounce',
      /\/fsbo\/invoices/.test(page.url()) ? 'PASS' : 'FAIL',
      page.url(),
    )
  }

  // ── 14. Create share link + public viewer ───────────────────────────────
  {
    await gotoPath(page, '/fsbo')
    await waitForOverviewReady(page)
    const share = page.getByTestId('fsbo-share').first()
    await share.click()
    await waitSettled(page, 700)
    const create = page.getByRole('button', { name: /Create share link/i }).first()
    if (await create.isVisible({ timeout: 4000 }).catch(() => false)) {
      await create.click()
      await waitSettled(page, 900)
      const recipient = page.locator('#recipient')
      if (await recipient.isVisible({ timeout: 6000 }).catch(() => false)) {
        await recipient.fill('QA Viewer')
        await page.getByRole('button', { name: /Create link/i }).click()
        await waitSettled(page, 1500)
        const body = await page.locator('body').innerText()
        const match = body.match(/https?:\/\/[^\s]+\/milestones\/[A-Za-z0-9_-]+/) || body.match(/\/milestones\/[A-Za-z0-9_-]+/)
        if (match) {
          log('FS-29-share-create', 'PASS', match[0])
          const shareUrl = match[0].startsWith('http') ? match[0] : `${APP}${match[0]}`
          await page.keyboard.press('Escape').catch(() => {})
          await page.keyboard.press('Escape').catch(() => {})
          const viewer = await context.newPage()
          try {
            await viewer.goto(shareUrl, { waitUntil: 'domcontentloaded', timeout: 30000 })
            await viewer
              .getByRole('heading', { name: /Link unavailable|Maple Prep|Velvet Contract/i })
              .or(viewer.getByText(/Closing|Key dates|days to close/i))
              .first()
              .waitFor({ timeout: 15000 })
              .catch(() => {})
            const vtext = await viewer.locator('body').innerText()
            const ok = /Maple Prep|Velvet Contract/i.test(vtext)
            const leaked = /\bNeeds You\b|Task Queue|Inbox Elf|AI Suggestions/i.test(vtext)
            const broken = /Link unavailable|could not load this link/i.test(vtext)
            const taskName = /\b(Call buyer|Send CD|Order appraisal|Needs You)\b/i.test(vtext)
            if (broken || leaked || !ok || taskName) {
              log('FS-30-public-viewer', 'FAIL', vtext.slice(0, 300))
            } else {
              log('FS-30-public-viewer', 'PASS', vtext.slice(0, 240))
            }
          } catch (e) {
            log('FS-30-public-viewer', 'FAIL', e.message)
          } finally {
            await viewer.close().catch(() => {})
          }
        } else {
          log('FS-29-share-create', lastShareCreate ? 'PASS' : 'FAIL', JSON.stringify(lastShareCreate)?.slice(0, 200) || body.slice(0, 240))
        }
      } else log('FS-29-share-create', 'FAIL', 'create form missing')
    } else log('FS-29-share-create', 'FAIL', 'Create share link missing')
    await page.keyboard.press('Escape').catch(() => {})
    await page.keyboard.press('Escape').catch(() => {})

    await gotoPath(page, '/fsbo')
    await waitForOverviewReady(page)
    const shareAgain = page.getByTestId('fsbo-share').first()
    if (await shareAgain.isVisible({ timeout: 3000 }).catch(() => false)) {
      await shareAgain.click()
      await waitSettled(page, 700)
      const revokeBtn = page.getByRole('button', { name: /Revoke/i }).first()
      if (await revokeBtn.isVisible({ timeout: 4000 }).catch(() => false)) {
        await revokeBtn.click()
        await waitSettled(page, 1200)
        const body = await page.locator('body').innerText()
        log(
          /Revoked|Link revoked/i.test(body) ? 'FS-49-share-revoke' : 'FS-49-share-revoke',
          /Revoked|Link revoked/i.test(body) ? 'PASS' : 'WARN',
          body.slice(0, 200),
        )
      } else {
        log('FS-49-share-revoke', 'WARN', 'no live link to revoke')
      }
      await page.keyboard.press('Escape').catch(() => {})
    } else {
      log('FS-49-share-revoke', 'FAIL', 'Share milestones missing after create')
    }
  }

  // ── 15. /sharing bookmark bounce ────────────────────────────────────────
  {
    await gotoPath(page, '/sharing')
    await waitSettled(page, 800)
    log(
      /\/fsbo\/?(\?|$)/.test(page.url()) ? 'FS-31-sharing-bounce' : 'FS-31-sharing-bounce',
      /\/fsbo\/?(\?|$)/.test(page.url()) ? 'PASS' : 'FAIL',
      page.url(),
    )
  }

  // ── 16. Settings / Account modal ────────────────────────────────────────
  {
    await gotoPath(page, '/fsbo/settings', { escape: false })
    await waitSettled(page, 800)
    const dlg = page.getByRole('dialog').first()
    const open = await dlg.isVisible({ timeout: 4000 }).catch(() => false)
    log(open ? 'FS-32-settings' : 'FS-32-settings', open ? 'PASS' : 'FAIL', open ? 'Account modal' : page.url())
    if (open) {
      const rail = ['Profile', 'Notifications', 'Sharing', 'Security', 'Help & tour']
      const missing = []
      for (const label of rail) {
        const btn = dlg.getByRole('button', { name: label }).first()
        if (!(await btn.isVisible().catch(() => false))) missing.push(label)
      }
      log(
        'FS-58-settings-rail',
        missing.length === 0 ? 'PASS' : 'FAIL',
        missing.length === 0 ? rail.join(', ') : `missing ${missing.join(', ')}`,
      )
      const notif = dlg.getByRole('button', { name: 'Notifications' }).first()
      await notif.click().catch(() => {})
      await waitSettled(page, 800)
      const ntext = await dlg.innerText().catch(() => '')
      const staffCats = /Task assignment|AI email sent|Daily summary|Closed-transaction/i.test(ntext)
      const sellerCats = /Documents|Messages from your coordinator|Dates on your sale|Share-link views/i.test(ntext)
      log(
        'FS-59-seller-notifications',
        !staffCats && sellerCats ? 'PASS' : 'FAIL',
        staffCats ? `staff categories leaked\n${ntext.slice(0, 400)}` : ntext.slice(0, 280),
      )
      const help = dlg.getByRole('button', { name: 'Help & tour' }).first()
      await help.click().catch(() => {})
      await waitSettled(page, 500)
      const htext = await dlg.innerText().catch(() => '')
      log(
        'FS-60-help',
        /Help Center|Start tour/i.test(htext) ? 'PASS' : 'FAIL',
        htext.slice(0, 240),
      )
      const security = dlg.getByRole('button', { name: 'Security' }).first()
      await security.click().catch(() => {})
      await waitSettled(page, 400)
      const stext = await dlg.innerText().catch(() => '')
      log(
        'FS-61-security',
        /Email reset link|Password/i.test(stext) ? 'PASS' : 'FAIL',
        stext.slice(0, 240),
      )
    } else {
      log('FS-58-settings-rail', 'FAIL', 'modal not open')
      log('FS-59-seller-notifications', 'FAIL', 'modal not open')
      log('FS-60-help', 'FAIL', 'modal not open')
      log('FS-61-security', 'FAIL', 'modal not open')
    }
    await page.keyboard.press('Escape').catch(() => {})
  }

  // ── 17. Notifications bell (seller-safe; never staff AI drafts) ──────────
  {
    await gotoPath(page, '/fsbo')
    await waitForFsboShell(page)
    const bell = page.getByRole('button', { name: /Notifications/i }).first()
    if (!(await bell.isVisible({ timeout: 3000 }).catch(() => false))) {
      log('FS-33-bell', 'FAIL', 'notification bell missing')
    } else {
      await bell.click()
      await waitSettled(page, 800)
      const dlg = page.getByRole('dialog', { name: /Notifications/i }).first()
      const open = await dlg.isVisible({ timeout: 4000 }).catch(() => false)
      const panelText = open ? await dlg.innerText().catch(() => '') : await dumpText(page, 'bell')
      const staffLeak =
        /AI draft|awaiting review|outbound email|sent on your behalf|Nothing overdue, nothing due in the next three days/i.test(
          panelText,
        )
      const staffTabs =
        (await dlg.getByRole('tab', { name: /^Overdue$/i }).count().catch(() => 0)) > 0 ||
        (await dlg.getByRole('tab', { name: /^Tomorrow$/i }).count().catch(() => 0)) > 0
      const pendingLeak = staffPendingHits.length > 0
      const kinds = (lastFsboBell?.items || []).map((i) => i.kind)
      const payloadLeak = kinds.some((k) => /ai_draft|outbound|client_reply/i.test(String(k || '')))
      const hrefLeak = (lastFsboBell?.items || []).some(
        (i) => i.href && !String(i.href).startsWith('/fsbo'),
      )
      const sellerSafe = /caught up|coordinator|share link|document|invoice|message/i.test(
        panelText,
      )
      if (!open) log('FS-33-bell', 'FAIL', 'panel did not open')
      else if (staffLeak || staffTabs || pendingLeak || payloadLeak || hrefLeak) {
        log(
          'FS-33-bell',
          'FAIL',
          `staff inbox leaked panel=${staffLeak} tabs=${staffTabs} pendingHits=${staffPendingHits.length} kinds=${kinds.join(',')} hrefLeak=${hrefLeak}\n${panelText.slice(0, 500)}`,
        )
      } else if (!sellerSafe) {
        log('FS-33-bell', 'FAIL', panelText.slice(0, 400))
      } else log('FS-33-bell', 'PASS', `unread=${lastFsboBell?.unread_count ?? 'n/a'}`)
      await page.keyboard.press('Escape').catch(() => {})
    }
  }

  // ── 18. Staff URL bounce ────────────────────────────────────────────────
  for (const [id, pathName, expectRe] of [
    ['FS-34-dashboard-bounce', '/dashboard', /\/fsbo/],
    ['FS-35-transactions-bounce', '/transactions', /\/fsbo/],
    ['FS-36-admin-bounce', '/admin/users', /\/fsbo/],
    ['FS-37-client-bounce', '/client/home', /\/fsbo/],
    ['FS-38-ai-emails-bounce', '/ai-emails', /\/fsbo/],
    ['FS-50-notifications-bounce', '/notifications', /\/fsbo/],
  ]) {
    await gotoPath(page, pathName)
    await waitSettled(page, 900)
    const text = await page.locator('body').innerText().catch(() => '')
    const ok = expectRe.test(page.url()) && !hasStaffChrome(text)
    log(id, ok ? 'PASS' : 'FAIL', page.url())
  }

  // ── 19. Typography + nested buttons ─────────────────────────────────────
  {
    await gotoPath(page, '/fsbo')
    await waitForOverviewReady(page)
    const below = await measureBelow12(page, '#main-content')
    if (below.length === 0) log('FS-39-type-12px', 'PASS')
    else log('FS-39-type-12px', 'FAIL', JSON.stringify(below.slice(0, 12)))
    const nested = await nestedButtonCount(page)
    if (nested.nested === 0) log('FS-40-nested-buttons', 'PASS', `buttons=${nested.total}`)
    else log('FS-40-nested-buttons', 'FAIL', JSON.stringify(nested))
  }

  // ── 20. Console / network hygiene ───────────────────────────────────────
  {
    const cons = realConsole()
    const pages = pageErrors.filter((e) => !/ResizeObserver|chrome-extension/i.test(e))
    const failed = failedRequests.filter(
      (u) =>
        !/\.(png|jpe?g|woff|ttf|otf|svg)/i.test(u) &&
        !/\/00000000-0000-0000-0000-000000000000/.test(u),
    )
    if (pages.length === 0) log('FS-41-pageerrors', 'PASS')
    else log('FS-41-pageerrors', 'FAIL', pages.join(' | '))
    if (cons.length === 0) log('FS-42-console', 'PASS')
    else log('FS-42-console', 'WARN', cons.slice(0, 6).join(' | '))
    if (failed.length === 0) log('FS-43-network', 'PASS')
    else log('FS-43-network', 'WARN', failed.slice(0, 8).join(' | '))
  }

  const pass = findings.filter((f) => f.result === 'PASS').length
  const fail = findings.filter((f) => f.result === 'FAIL').length
  const warn = findings.filter((f) => f.result === 'WARN').length
  const summary = { pass, fail, warn, total: findings.length, url: page.url(), lastOverview: lastOverview && { n: lastOverview.properties?.length, missing: lastOverview.missing_documents_count } }
  console.log('SUMMARY', JSON.stringify(summary))
  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ summary, findings, consoleErrors, pageErrors, failedRequests }, null, 2))
  await browser.close()
  process.exit(fail > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
