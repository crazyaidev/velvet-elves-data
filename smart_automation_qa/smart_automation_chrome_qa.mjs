/**
 * Local Chrome QA for Smart Automation (S0–S5 / S8).
 * Headed Google Chrome against http://localhost:5173
 *
 * Safety: Preview + Draft due emails only. Never confirm Run AI tasks,
 * never Send, never POST /internal/schedules/tick.
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

const EMAIL = 'shyna.elene@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://localhost:5173'

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let lastQueue = null
let lastStatus = null
let lastPreview = null
let lastRunNow = null
let lastPlan = null
let shotIdx = 0

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 400) : ''}`)
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
  }
  await page.keyboard.press('Escape').catch(() => {})
  const closeChat = page.getByRole('button', { name: /Close AI chat/i })
  if (await closeChat.isVisible({ timeout: 400 }).catch(() => false)) {
    await closeChat.click({ timeout: 2000 }).catch(() => {})
  }
}

async function waitNeedsYou(page) {
  await page.getByRole('heading', { name: /Needs You/i }).first().waitFor({ timeout: 45000 })
  await page.waitForFunction(
    () => {
      const t = document.body?.innerText || ''
      if (/Couldn't load|Failed to load Needs You/i.test(t)) return true
      if (/\bLoading\b/.test(t) && !/\d+\s+waiting/i.test(t)) return false
      return (
        /Nothing needs you right now|Overnight prep ran/i.test(t)
        || /Waiting on you/i.test(t)
        || /\d+\s+waiting/i.test(t)
      )
    },
    { timeout: 90000 },
  )
  await page.waitForTimeout(400)
}

function realConsole() {
  return consoleErrors.filter((e) =>
    !/Download the React DevTools|favicon|third-party cookie|Failed to load resource/i.test(e),
  )
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
    return out.slice(0, 40)
  })
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
      const json = await res.json().catch(() => null)
      if (!json) return
      if (url.includes('/automation/needs-you') && !url.includes('approve') && !url.includes('send')) {
        lastQueue = json
      } else if (url.includes('/automation/status')) {
        lastStatus = json
      } else if (url.includes('/automation/preview')) {
        lastPreview = json
      } else if (url.includes('/automation/run-now')) {
        lastRunNow = json
      } else if (/\/transactions\/[^/]+\/plan/.test(url) && json.automation) {
        lastPlan = json
      }
    } catch { /* ignore */ }
  })

  // ── W0-S-01 login ────────────────────────────────────────────────────────
  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.locator('#login-email').waitFor({ timeout: 15000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 25000 })
    await page.waitForTimeout(1200)
    await dismissOverlays(page)
    await dismissOverlays(page)
    log('W0-S-01', 'PASS', page.url())
  } catch (err) {
    log('W0-S-01', 'FAIL', err.message)
    await shot(page, 'login_fail')
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, consoleErrors, pageErrors }, null, 2))
    await browser.close()
    process.exit(1)
  }

  // ── W0-S-02 / W0-N / W0-H Needs You ──────────────────────────────────────
  try {
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded', timeout: 20000 })
    await waitNeedsYou(page)
    await dismissOverlays(page)
    await shot(page, 'needs_you_desktop')
    const body = await dumpText(page, 'needs_you_desktop')
    const pill = /\d+\s+waiting/i.test(body)
    const loadingLie = /Nothing needs you right now|Overnight prep ran/i.test(body) && (lastQueue?.counts?.total > 0)
    log('W0-S-02', pill && !loadingLie ? 'PASS' : 'FAIL', `url=${page.url()} total=${lastQueue?.counts?.total}`)
    writeFileSync(path.join(OUT, 'needs_you_api.json'), JSON.stringify(lastQueue, null, 2))
    writeFileSync(path.join(OUT, 'automation_status.json'), JSON.stringify(lastStatus, null, 2))

    const banner = /Automation is not running|Automation has stopped/i.test(body)
    if (lastStatus && lastStatus.scheduler_healthy === false) {
      log('W0-H-01', banner ? 'PASS' : 'FAIL', JSON.stringify({
        healthy: lastStatus.scheduler_healthy, state: lastStatus.scheduler_state,
      }))
    } else {
      log('W0-H-01', banner ? 'FAIL' : 'PASS', 'healthy — banner should be absent')
    }
    log('W0-H-04', 'SKIP', 'local scheduler stale is expected; did not start run_schedules.py')

    const routineLie = /everything routine already ran/i.test(body)
    log('S1-02', (lastQueue?.counts?.total > 0 && routineLie) ? 'FAIL' : 'PASS',
      routineLie ? 'briefing claims routine already ran' : 'honest briefing')

    const openAi = page.getByRole('link', { name: /Open AI.*Automation|AI & Automation/i }).first()
    if (await openAi.isVisible().catch(() => false)) {
      await openAi.click()
      await page.waitForTimeout(800)
      log('W0-H-02', /\/admin\/confidence/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
      await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded' })
      await waitNeedsYou(page)
    } else if (banner) {
      log('W0-H-02', 'FAIL', 'banner present but no Open AI & Automation link')
    } else {
      log('W0-H-02', 'SKIP', 'healthy — no banner link')
    }

    const recovery = page.getByRole('link', { name: /Add contact|Upload document|Reconnect mailbox|Change due date|Open AI/i }).first()
    log('S2-recovery-link', (await recovery.isVisible().catch(() => false))
      ? 'PASS'
      : ((lastQueue?.items || []).some((i) => i.kind === 'task') ? 'INFO' : 'SKIP'),
      'blocked-task recovery control')

    const tryNow = page.getByRole('button', { name: /Try now \(this deal only\)/i }).first()
    log('S2-06-visible', (await tryNow.isVisible().catch(() => false)) ? 'PASS' : 'INFO',
      'visible is enough; not clicked (could send Class A)')

    const exportBtn = page.getByRole('button', { name: /Export CSV/i }).first()
    log('W0-N-06-named', (await exportBtn.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    const nyType = await measureBelow12(page)
    writeFileSync(path.join(OUT, 'typography_needs_you.json'), JSON.stringify(nyType, null, 2))
    log('typography-needs-you', nyType.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(nyType.slice(0, 12)))
  } catch (err) {
    log('W0-S-02', 'FAIL', err.message)
    await shot(page, 'needs_you_fail')
  }

  // ── W0-S-03 / S0 / S1 / S8 AI & Automation ───────────────────────────────
  try {
    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 20000 })
    await page.getByRole('heading', { name: /AI & Automation|Automation posture|Overnight/i }).first().waitFor({ timeout: 20000 })
    await page.getByRole('radio', { name: /Manual/i }).waitFor({ timeout: 20000 })
    await page.getByText(/Hourly automation is (on|off)/i).first().waitFor({ timeout: 20000 })
    await page.waitForFunction(
      () => {
        const t = document.body?.innerText || ''
        return /Last draft sweep/i.test(t) && /Last tick/i.test(t) && /Assisted/i.test(t) && /Autopilot/i.test(t)
      },
      { timeout: 20000 },
    )
    await dismissOverlays(page)
    await shot(page, 'admin_confidence')
    const body = await dumpText(page, 'admin_confidence')

    const cards = /Manual/.test(body) && /Assisted/.test(body) && /Autopilot/.test(body)
    const overnight = /Overnight/i.test(body)
    const compare = /Routine actions/i.test(body) && /Welcome \/ title letters/i.test(body)
    const alwaysTrue = /Always true/i.test(body)
    const preview = await page.getByRole('button', { name: /Preview next tick/i }).isVisible().catch(() => false)
    const drafts = await page.getByRole('button', { name: /Draft due emails/i }).isVisible().catch(() => false)
    const runAi = await page.getByRole('button', { name: /Run AI tasks/i }).isVisible().catch(() => false)
    log('W0-S-03', cards && preview && drafts && runAi ? 'PASS' : 'FAIL',
      JSON.stringify({ cards, preview, drafts, runAi, overnight, compare, alwaysTrue }))
    log('UX-overnight', overnight && compare && alwaysTrue ? 'PASS' : 'FAIL',
      JSON.stringify({ overnight, compare, alwaysTrue }))

    const doctrine = /library welcome and title-order letters may send/i.test(body)
      && /every other email is drafted for you to send/i.test(body)
    const blanket = /nothing (ever )?sends until you tap Send/i.test(body)
      && !/every other email/i.test(body)
    log('S1-01', doctrine && !blanket ? 'PASS' : 'FAIL', doctrine ? 'doctrine present' : body.slice(0, 400))

    const hourly = /Hourly automation is (on|off)/i.test(body)
    log('S8-02', hourly ? 'PASS' : 'FAIL', 'workspace hourly switch copy')

    const tickCounts = /Last tick ·/i.test(body)
      || /Last overnight ·/i.test(body)
      || typeof lastStatus?.last_tick_counts?.tenants_swept === 'number'
      || lastStatus?.tenant_tick != null
    log('S0-01', tickCounts || lastStatus ? 'PASS' : 'FAIL', JSON.stringify({
      counts: lastStatus?.last_tick_counts,
      tenant_tick: lastStatus?.tenant_tick,
      platformLine: /Last tick ·/i.test(body),
    }))

    const sentHere = Number(
      lastStatus?.tenant_tick?.completed ?? lastStatus?.last_tick_counts?.ai_tasks_completed ?? 0,
    )
    const sendAlert = /The hourly run sent/i.test(body)
    if (sentHere > 0) {
      if (!sendAlert) {
        await page.getByText(/The hourly run sent/i).waitFor({ timeout: 8000 }).catch(() => {})
      }
      const body2 = await page.locator('body').innerText()
      log('S0-02', /The hourly run sent/i.test(body2) ? 'PASS' : 'FAIL', 'amber send honesty')
    } else {
      log('S0-02', 'SKIP', 'last tick sent 0 for this workspace')
    }

    const clocksBody = await page.locator('body').innerText()
    const lastTick = /last tick/i.test(clocksBody)
    const lastSweep = /Last draft sweep/i.test(clocksBody)
    log('W0-H-03', lastTick && lastSweep ? 'PASS' : 'FAIL', 'two clocks')

    const adminType = await measureBelow12(page)
    writeFileSync(path.join(OUT, 'typography_admin.json'), JSON.stringify(adminType, null, 2))
    log('typography-admin', adminType.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(adminType.slice(0, 12)))

    // Preview — wait for the API (can take tens of seconds on a large tenant)
    lastPreview = null
    const previewBtn = page.getByRole('button', { name: /Preview next tick/i })
    const previewWait = page.waitForResponse(
      (r) => r.url().includes('/api/v1/automation/preview') && r.request().method() === 'GET',
      { timeout: 90000 },
    )
    await previewBtn.click()
    let previewStatus = null
    try {
      const previewRes = await previewWait
      previewStatus = previewRes.status()
      lastPreview = await previewRes.json().catch(() => lastPreview)
    } catch (err) {
      log('S0-03-api', 'FAIL', err.message)
    }
    const gotIt = page.getByRole('button', { name: /^Got it$/i }).first()
    await gotIt.waitFor({ state: 'visible', timeout: 15000 }).catch(() => {})
    const dlgVisible = await gotIt.isVisible().catch(() => false)
    const dlgText = dlgVisible
      ? await page.getByRole('alertdialog').innerText().catch(() => '')
      : ''
    const previewOk = previewStatus === 200 && dlgVisible && /would send/i.test(dlgText)
    log('S0-03', previewOk ? 'PASS' : 'FAIL',
      `status=${previewStatus} dialog=${dlgVisible} api=${JSON.stringify(lastPreview?.counts || lastPreview)} text=${dlgText.slice(0, 240)}`)
    if (dlgVisible) await gotIt.click()
    else await page.keyboard.press('Escape')
    await page.waitForTimeout(400)
    log('W0-A-03', lastRunNow == null ? 'PASS' : 'FAIL', 'Got it must not run jobs')

    // Draft due emails — no send
    lastRunNow = null
    const draftBtn = page.getByRole('button', { name: /Draft due emails/i })
    const draftWait = page.waitForResponse(
      (r) => r.url().includes('/automation/run-now') && r.request().method() === 'POST',
      { timeout: 60000 },
    )
    await draftBtn.click({ timeout: 15000 })
    try {
      const draftRes = await draftWait
      lastRunNow = await draftRes.json().catch(() => lastRunNow)
    } catch (err) {
      log('W0-B-01-api', 'FAIL', err.message)
    }
    const toastBody = await page.locator('body').innerText()
    log('W0-B-01', /Draft sweep ran|Prepared|Nothing was sent|Run failed/i.test(toastBody) || lastRunNow
      ? 'PASS' : 'FAIL', JSON.stringify(lastRunNow))
    if (lastRunNow && (lastRunNow.ai_tasks_completed || 0) > 0) {
      log('W0-B-01-send', 'FAIL', 'Draft due emails must not complete Class A sends')
    }
  } catch (err) {
    log('W0-S-03', 'FAIL', err.message)
    await shot(page, 'admin_fail')
  }

  try {
    await page.goto(`${APP}/admin/confidence?section=email`, { waitUntil: 'domcontentloaded' })
    await page.getByText(/Never marked Ready/i).waitFor({ timeout: 15000 })
    const emailBody = await page.locator('body').innerText()
    log('S4-settings', /Never marked Ready/i.test(emailBody) && /Wire and funds/i.test(emailBody) ? 'PASS' : 'FAIL')
    const previewOnEmail = await page.getByRole('button', { name: /Preview next tick/i }).isVisible().catch(() => false)
    const draftOnEmail = await page.getByRole('button', { name: /Draft due emails/i }).isVisible().catch(() => false)
    log('UX-finetune-no-send', !previewOnEmail && !draftOnEmail ? 'PASS' : 'FAIL',
      JSON.stringify({ previewOnEmail, draftOnEmail }))
  } catch (err) {
    log('S4-settings', 'FAIL', err.message)
  }

  // ── W0-S-04 connections ──────────────────────────────────────────────────
  try {
    await page.goto(`${APP}/settings/connections`, { waitUntil: 'domcontentloaded', timeout: 20000 })
    await page.waitForTimeout(1200)
    await dismissOverlays(page)
    await shot(page, 'connections')
    const body = await dumpText(page, 'connections')
    const providers = /Gmail/i.test(body) && /Outlook/i.test(body)
    log('W0-S-04', providers ? 'PASS' : 'FAIL', body.slice(0, 400))
  } catch (err) {
    log('W0-S-04', 'FAIL', err.message)
  }

  // ── W0-S-05 / W0-P deal workspace ────────────────────────────────────────
  let dealUrl = null
  try {
    await page.goto(`${APP}/transactions/active`, { waitUntil: 'domcontentloaded', timeout: 20000 })
    await page.waitForTimeout(1500)
    await dismissOverlays(page)
    const dealLink = page.getByRole('link', { name: /Open workspace for/i }).first()
    await dealLink.waitFor({ state: 'visible', timeout: 20000 }).catch(() => {})
    if (await dealLink.isVisible().catch(() => false)) {
      await dealLink.click()
      await page.waitForURL(/\/transactions\/[0-9a-f-]{8,}/i, { timeout: 15000 })
      dealUrl = page.url()
      await page.waitForTimeout(1200)
      await dismissOverlays(page)
      await shot(page, 'deal_workspace')
      const body = await dumpText(page, 'deal_workspace')
      const postureChip = page.getByRole('button', { name: /Automation posture for this deal/i })
      await postureChip.waitFor({ state: 'visible', timeout: 15000 })
      const tabs = /Tasks/i.test(body) && /Email/i.test(body) && /Contacts/i.test(body)
      log('W0-S-05', (await postureChip.isVisible().catch(() => false)) && tabs ? 'PASS' : 'FAIL', dealUrl)

      await postureChip.click()
      await page.waitForTimeout(400)
      const menu = page.getByRole('menu')
      const menuText = await menu.innerText()
      log('W0-P-01-menu', /Manual/.test(menuText) && /Assisted/.test(menuText) && /Autopilot/.test(menuText) ? 'PASS' : 'FAIL')
      log('S1-01-deal', /Library welcome and title-order letters may send/i.test(menuText) ? 'PASS' : 'FAIL')

      async function choosePosture(label) {
        const item = page.getByRole('menuitem', { name: new RegExp(`^${label}`, 'i') })
        if (!(await item.isVisible().catch(() => false))) {
          await page.keyboard.press('Escape').catch(() => {})
          await postureChip.click({ timeout: 8000 })
          await item.waitFor({ state: 'visible', timeout: 8000 })
        }
        await item.click({ timeout: 8000 })
        await page.waitForFunction(
          (want) => {
            const btn = document.querySelector('[aria-label="Automation posture for this deal"]')
            const first = (btn?.innerText || '').split('\n')[0].trim()
            return first.toLowerCase() === String(want).toLowerCase()
          },
          label,
          { timeout: 12000 },
        )
        return (await postureChip.innerText()).split('\n')[0].trim()
      }

      try {
        const manualText = await choosePosture('Manual')
        log('W0-P-02', /^Manual\b/i.test(manualText) ? 'PASS' : 'FAIL', manualText)
      } catch (err) {
        log('W0-P-02', 'FAIL', err.message)
      }

      try {
        const assistedText = await choosePosture('Assisted')
        log('W0-P-03', /^Assisted\b/i.test(assistedText) ? 'PASS' : 'FAIL', assistedText)
      } catch (err) {
        log('W0-P-03', 'FAIL', err.message)
      }

      try {
        const autoText = await choosePosture('Autopilot')
        log('W0-P-04', /^Autopilot\b/i.test(autoText) ? 'PASS' : 'FAIL', autoText)
      } catch (err) {
        log('W0-P-04', 'FAIL', err.message)
      }

      try {
        await page.keyboard.press('Escape').catch(() => {})
        await postureChip.click({ timeout: 8000 })
        const inherit = page.getByRole('menuitem', { name: /Use workspace default/i }).first()
        if (await inherit.isVisible().catch(() => false)) {
          await inherit.click()
          await page.waitForTimeout(800)
          log('W0-P-05', 'PASS', 'inherit clicked')
          log('S1-05', 'PASS', 'inherit control exists and applied')
        } else {
          await page.keyboard.press('Escape').catch(() => {})
          log('W0-P-05', 'SKIP', 'already inheriting')
          log('S1-05', 'SKIP', 'no deal pin to clear')
        }
      } catch (err) {
        log('W0-P-05', 'FAIL', err.message)
        log('S1-05', 'FAIL', err.message)
      }

      // Email tab doctrine banner
      const emailTab = page.getByRole('tab', { name: /^Email$/i }).first()
      if (await emailTab.isVisible().catch(() => false)) {
        await emailTab.click()
        await page.waitForTimeout(800)
        await page.getByText(/Nothing sends until you tap Send/i).waitFor({ timeout: 10000 }).catch(() => {})
        const emailBody = await page.locator('body').innerText()
        log('S1-01-email-tab', /Nothing sends until you tap Send/i.test(emailBody) && /Library welcome/i.test(emailBody) ? 'PASS' : 'FAIL', emailBody.slice(0, 400))
      }
      const dealType = await measureBelow12(page)
      writeFileSync(path.join(OUT, 'typography_deal.json'), JSON.stringify(dealType, null, 2))
      log('typography-deal', dealType.length === 0 ? 'PASS' : 'FAIL', JSON.stringify(dealType.slice(0, 12)))
    } else {
      log('W0-S-05', 'FAIL', 'no Open workspace link on /transactions/active')
    }
  } catch (err) {
    log('W0-S-05', 'FAIL', err.message)
    await shot(page, 'deal_fail')
  }

  // ── S5 AI Emails filtered + unmatched ────────────────────────────────────
  try {
    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 20000 })
    await page.waitForFunction(
      () => {
        const t = document.body?.innerText || ''
        return /Nothing here|Pick a message|No matches|Filtered/i.test(t)
          && !/Couldn't load/i.test(t)
      },
      { timeout: 25000 },
    ).catch(() => {})
    await dismissOverlays(page)
    await shot(page, 'ai_emails')
    const filteredTab = page.getByRole('tab', { name: /Filtered/i }).first()
    log('S5-03-tab', (await filteredTab.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    if (await filteredTab.isVisible().catch(() => false)) {
      await filteredTab.click()
      await page.waitForTimeout(800)
      await shot(page, 'ai_emails_filtered')
      const body = await page.locator('body').innerText()
      log('S5-03', /Filtered|Undo filter|Nothing filtered|envelope/i.test(body) ? 'PASS' : 'FAIL', body.slice(0, 240))
    }
    const inboxTab = page.getByRole('tab', { name: /Inbox/i }).first()
    if (await inboxTab.isVisible().catch(() => false)) {
      await inboxTab.click()
      await page.waitForTimeout(600)
      const why = /Filed on this deal because|Why this deal/i.test(await page.locator('body').innerText())
      log('S5-01', why ? 'PASS' : 'INFO', 'evidence line appears when a filed inbound is selected')
    }
  } catch (err) {
    log('S5-03', 'FAIL', err.message)
  }

  // ── Console on desktop surfaces ──────────────────────────────────────────
  const cons = realConsole()
  log('console-errors', cons.length === 0 && pageErrors.length === 0 ? 'PASS' : 'FAIL',
    JSON.stringify({ console: cons.slice(0, 10), page: pageErrors.slice(0, 8), failed: failedRequests.slice(0, 10) }))

  // ── W0-S-06 / W0-M mobile ────────────────────────────────────────────────
  try {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded' })
    await waitNeedsYou(page)
    await shot(page, 'needs_you_390')
    const overflowNy = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
    log('W0-S-06', overflowNy ? 'FAIL' : 'PASS', overflowNy ? 'horizontal overflow' : 'ok')
    log('W0-N-12-export', (await page.getByRole('button', { name: /Export CSV/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')

    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /Preview next tick/i }).waitFor({ timeout: 20000 })
    await page.getByRole('button', { name: /Draft due emails/i }).waitFor({ timeout: 20000 })
    await shot(page, 'admin_390')
    const overflowAd = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
    const previewM = await page.getByRole('button', { name: /Preview next tick/i }).isVisible().catch(() => false)
    const draftM = await page.getByRole('button', { name: /Draft due emails/i }).isVisible().catch(() => false)
    log('W0-M-01', !overflowAd && previewM && draftM ? 'PASS' : 'FAIL',
      JSON.stringify({ overflowAd, previewM, draftM }))

    if (dealUrl) {
      try {
        await page.goto(dealUrl, { waitUntil: 'domcontentloaded' })
        const chip = page.getByRole('button', { name: /Automation posture for this deal/i })
        await chip.waitFor({ state: 'visible', timeout: 15000 })
        await chip.click()
        await page.waitForTimeout(300)
        const items = await page.getByRole('menuitem').count()
        log('W0-M-02', items >= 3 ? 'PASS' : 'FAIL', `menuitems=${items}`)
        await page.keyboard.press('Escape')
      } catch (err) {
        log('W0-M-02', 'FAIL', err.message)
      }
    }

    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(1000)
    await shot(page, 'ai_emails_390')
    const overflowEm = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
    log('W0-M-03', overflowEm ? 'FAIL' : 'PASS')
  } catch (err) {
    log('W0-S-06', 'FAIL', err.message)
  }

  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({
    findings,
    consoleErrors: cons,
    pageErrors,
    failedRequests,
    lastQueue,
    lastStatus,
    lastPreview,
    lastRunNow,
    lastPlan,
  }, null, 2))

  const pass = findings.filter((f) => f.result === 'PASS').length
  const fail = findings.filter((f) => f.result === 'FAIL').length
  const skip = findings.filter((f) => f.result === 'SKIP').length
  const info = findings.filter((f) => f.result === 'INFO').length
  console.log(`\n=== ${PASS} ${pass} pass / ${fail} fail / ${skip} skip / ${info} info ===`)
  console.log(`artifacts: ${OUT}`)
  await browser.close()
  process.exit(fail > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
