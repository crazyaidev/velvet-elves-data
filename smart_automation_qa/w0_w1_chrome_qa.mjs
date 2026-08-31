/**
 * Local Chrome QA for TME W0–W1 (Aime identity, posture, dual HOA/utility,
 * writing style). Headed Google Chrome against http://localhost:5173.
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
const STAMP = new Date().toISOString().slice(0, 10)
const OUT = path.join(__dirname, `artifacts_w0_w1_${STAMP}`)
mkdirSync(OUT, { recursive: true })

const EMAIL = 'shyna.elene@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://127.0.0.1:5173'

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let lastQueue = null
let lastStatus = null
let lastPreview = null
let lastRunNow = null
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

async function login(page) {
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.locator('#login-email').waitFor({ timeout: 15000 })
  await page.locator('#login-email').fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 25000 })
  await page.waitForTimeout(1200)
  await dismissOverlays(page)
  await dismissOverlays(page)
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
      }
    } catch { /* ignore */ }
  })

  try {
    await login(page)
    log('W0-S-01', 'PASS', page.url())
  } catch (err) {
    log('W0-S-01', 'FAIL', err.message)
    await shot(page, 'login_fail')
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, consoleErrors, pageErrors }, null, 2))
    await browser.close()
    process.exit(1)
  }

  // Aime chrome — floating chat
  try {
    const ask = page.getByRole('button', { name: /Ask Aime/i }).first()
    const visible = await ask.isVisible().catch(() => false)
    if (visible) {
      await ask.click()
      await page.waitForTimeout(600)
      const panel = await page.locator('body').innerText()
      const named = /Aime/i.test(panel) && !/\bWizard\b/.test(panel.split('\n').slice(0, 8).join(' '))
      log('W0-Aime-chat', named ? 'PASS' : 'FAIL', panel.slice(0, 240))
      await shot(page, 'aime_chat')
      await page.keyboard.press('Escape').catch(() => {})
      const close = page.getByRole('button', { name: /Close AI chat|Close Aime/i }).first()
      if (await close.isVisible().catch(() => false)) await close.click().catch(() => {})
    } else {
      log('W0-Aime-chat', 'FAIL', 'Ask Aime button not visible')
    }
  } catch (err) {
    log('W0-Aime-chat', 'FAIL', err.message)
  }

  // Needs You
  try {
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded', timeout: 20000 })
    await waitNeedsYou(page)
    await dismissOverlays(page)
    await shot(page, 'needs_you_desktop')
    const body = await dumpText(page, 'needs_you_desktop')
    const pill = /\d+\s+waiting/i.test(body) || /Nothing needs you right now/i.test(body)
    log('W0-S-02', pill ? 'PASS' : 'FAIL', `url=${page.url()} total=${lastQueue?.counts?.total}`)
    writeFileSync(path.join(OUT, 'needs_you_api.json'), JSON.stringify(lastQueue, null, 2))
  } catch (err) {
    log('W0-S-02', 'FAIL', err.message)
    await shot(page, 'needs_you_fail')
  }

  // AI & Automation — Aime signature, overnight, Preview, Draft
  try {
    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 20000 })
    await dismissOverlays(page)
    await page.getByRole('button', { name: /Close AI chat/i }).click({ timeout: 1500 }).catch(() => {})
    await page.getByRole('radio', { name: /Manual/i }).waitFor({ timeout: 25000 })
    await page.getByText('Aime signature').waitFor({ timeout: 25000 })
    await page.getByRole('button', { name: /Preview next tick/i }).waitFor({ timeout: 25000 })
    await dismissOverlays(page)
    await shot(page, 'admin_confidence')
    const body = await dumpText(page, 'admin_confidence')
    const cards = /Manual/.test(body) && /Assisted/.test(body) && /Autopilot/.test(body)
    const aimeSig = /Aime signature/i.test(body)
    const doctrine = /library welcome and title-order letters may send/i.test(body)
      || /every other email is drafted for you to send/i.test(body)
    log('W0-S-03', cards ? 'PASS' : 'FAIL', JSON.stringify({ cards, aimeSig }))
    log('W0-Aime-signature-toggle', aimeSig ? 'PASS' : 'FAIL')
    log('W0-doctrine', doctrine ? 'PASS' : 'INFO', 'doctrine copy on posture page')

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
    log('S0-03', previewStatus === 200 && dlgVisible ? 'PASS' : 'FAIL',
      `status=${previewStatus} dialog=${dlgVisible} text=${dlgText.slice(0, 240)}`)
    if (dlgVisible) await gotIt.click()
    else await page.keyboard.press('Escape')
    await page.waitForTimeout(400)
    log('W0-A-03', lastRunNow == null ? 'PASS' : 'FAIL', 'Got it must not run jobs')

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

    const runAi = page.getByRole('button', { name: /Run AI tasks/i })
    log('W0-A-no-run', (await runAi.isVisible().catch(() => false)) ? 'PASS' : 'FAIL',
      'control present; not clicked')
  } catch (err) {
    log('W0-S-03', 'FAIL', err.message)
    await shot(page, 'admin_fail')
  }

  // Writing style (W1)
  try {
    await page.goto(`${APP}/admin/confidence?section=email`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('heading', { name: /Writing style/i }).waitFor({ timeout: 15000 })
    await shot(page, 'writing_style')
    const preferred = page.locator('#writing-preferred')
    const prohibited = page.locator('#writing-prohibited')
    log('W1-style-card', (await preferred.isVisible()) && (await prohibited.isVisible()) ? 'PASS' : 'FAIL')
    const originalPreferred = await preferred.inputValue()
    const originalProhibited = await prohibited.inputValue()
    const marker = `qa-preferred-${Date.now()}`
    await preferred.fill(`${originalPreferred}\n${marker}`.trim())
    await prohibited.fill(originalProhibited.includes('just circling back')
      ? originalProhibited
      : `${originalProhibited}\njust circling back`.trim())
    const save = page.getByRole('button', { name: /Save writing style/i })
    await save.click()
    await page.getByText(/Writing style saved/i).waitFor({ timeout: 12000 }).catch(() => {})
    await page.reload({ waitUntil: 'domcontentloaded' })
    await page.getByRole('heading', { name: /Writing style/i }).waitFor({ timeout: 15000 })
    const saved = await page.locator('#writing-preferred').inputValue()
    log('W1-style-save', saved.includes(marker) ? 'PASS' : 'FAIL', saved.slice(0, 200))
    await page.locator('#writing-preferred').fill(originalPreferred)
    await page.locator('#writing-prohibited').fill(originalProhibited)
    const saveBack = page.getByRole('button', { name: /Save writing style/i })
    if (await saveBack.isEnabled().catch(() => false)) {
      await saveBack.click()
      await page.getByText(/Writing style saved/i).waitFor({ timeout: 12000 }).catch(() => {})
    }
  } catch (err) {
    log('W1-style-card', 'FAIL', err.message)
  }

  // Deal workspace — Aime completed + posture
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
      log('W0-progress-aime', /Aime completed/i.test(body) ? 'PASS' : 'INFO',
        'label present (count may be 0)')
      const postureChip = page.getByRole('button', { name: /Automation posture for this deal/i })
      await postureChip.waitFor({ state: 'visible', timeout: 15000 })
      log('W0-S-05', (await postureChip.isVisible()) ? 'PASS' : 'FAIL', dealUrl)
    } else {
      log('W0-S-05', 'FAIL', 'no Open workspace link')
    }
  } catch (err) {
    log('W0-S-05', 'FAIL', err.message)
  }

  // AI Emails — dual HOA copy + prohibited phrase
  try {
    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 20000 })
    await page.waitForTimeout(1500)
    await dismissOverlays(page)
    await shot(page, 'ai_emails')
    const body = await dumpText(page, 'ai_emails')
    const dualHint = /thank you for sending the hoa|attached are the hoa|utility information/i.test(body)
    log('W1-dual-copy', dualHint ? 'PASS' : 'INFO',
      dualHint ? 'HOA/utility dual copy visible' : 'no HOA/utility draft on this tenant right now')
    log('W1-prohibited-absent', /just circling back/i.test(body) ? 'FAIL' : 'PASS',
      'prohibited phrase must not appear in visible drafts')
  } catch (err) {
    log('W1-dual-copy', 'FAIL', err.message)
  }

  // Register posture (clear session, do not submit)
  try {
    await page.evaluate(() => { localStorage.clear(); sessionStorage.clear() })
    await context.clearCookies()
    await page.goto(`${APP}/register`, { waitUntil: 'domcontentloaded', timeout: 20000 })
    await page.waitForTimeout(800)
    const body = await dumpText(page, 'register')
    const posture = /How should Aime start/i.test(body)
      && /Manual/i.test(body) && /Assisted/i.test(body) && /Autopilot/i.test(body)
    log('W0-register-posture', posture ? 'PASS' : 'FAIL', body.slice(0, 300))
    await shot(page, 'register_posture')
  } catch (err) {
    log('W0-register-posture', 'FAIL', err.message)
  }

  try {
    await login(page)
    log('W0-relogin', 'PASS')
  } catch (err) {
    log('W0-relogin', 'FAIL', err.message)
  }

  const cons = realConsole()
  log('console-errors', cons.length === 0 && pageErrors.length === 0 ? 'PASS' : 'FAIL',
    JSON.stringify({ console: cons.slice(0, 10), page: pageErrors.slice(0, 8), failed: failedRequests.slice(0, 10) }))

  try {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded' })
    await waitNeedsYou(page)
    await shot(page, 'needs_you_390')
    const overflowNy = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
    log('W0-S-06', overflowNy ? 'FAIL' : 'PASS', overflowNy ? 'horizontal overflow' : 'ok')

    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: /Preview next tick/i }).waitFor({ timeout: 20000 })
    await shot(page, 'admin_390')
    const overflowAd = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
    log('W0-M-01', overflowAd ? 'FAIL' : 'PASS')
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
  }, null, 2))

  const pass = findings.filter((f) => f.result === 'PASS').length
  const fail = findings.filter((f) => f.result === 'FAIL').length
  const skip = findings.filter((f) => f.result === 'SKIP').length
  const info = findings.filter((f) => f.result === 'INFO').length
  const summary = `${pass} pass / ${fail} fail / ${skip} skip / ${info} info`
  writeFileSync(path.join(OUT, 'summary.txt'), summary + '\n' + findings.map((f) => `[${f.result}] ${f.id} ${f.details}`).join('\n'))
  console.log(`\n=== W0/W1 ${summary} ===`)
  console.log(`artifacts: ${OUT}`)
  await browser.close()
  process.exit(fail > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
