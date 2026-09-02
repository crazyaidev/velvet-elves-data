/**
 * Staging Chrome pass on existing 20260901 test files. Does not Send,
 * Generate, Run AI tasks, Disconnect, or Change status.
 *
 *   node feature14_32_staging_chrome_existing.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_feature14_32_staging_deploy')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const APP = (process.env.QA_APP || 'https://app.stage.velvetelves.com').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

const FILES = {
  elm: '3f469ceb-d5d1-490a-8808-c6abd3a8bc46',
  maple: '9507baaf-ad8b-41ce-912c-6d637fbb9138',
  cedar: '002b791f-ef34-4b8c-ad45-37479d447019',
  nocontract: '36507487-da17-4c37-a458-3d6faad3863c',
  dual: 'f53d0674-8322-4568-9fb9-fae7715d521d',
  confirm: 'ff800067-b769-4964-82a3-3855ea94a565',
  utility: '10e00794-5689-45d0-9c3f-8a165eff85d4',
}

const findings = []
function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 700) : ''}`)
}

async function dismissOverlays(page) {
  for (const name of [/Skip tour/i, /Skip for now/i, /^Skip$/i, /Not now/i, /Got it/i, /Maybe later/i]) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 400 }).catch(() => false)) {
      await btn.click({ timeout: 1500 }).catch(() => {})
    }
  }
}

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false }).catch(() => {})
}

async function dump(name, text) {
  writeFileSync(path.join(OUT, `${name}.txt`), String(text ?? ''))
}

async function closeDialog(page) {
  const dlg = page.getByRole('dialog').last()
  if (await dlg.isVisible().catch(() => false)) {
    await dlg.getByRole('button', { name: /close|cancel|i.ll handle it myself/i }).first().click({ timeout: 2500 }).catch(() => {})
    await page.keyboard.press('Escape').catch(() => {})
    await page.waitForTimeout(250)
  }
}

async function openDealTab(page, txId, tab) {
  const dest = `${APP}/transactions/${txId}?tab=${tab}`
  await page.goto(dest, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await dismissOverlays(page)
  try {
    await page.getByText(/Work queue|Add Task/i).first().waitFor({ state: 'visible', timeout: 25000 })
  } catch (err) {
    dump('open_deal_fail', `${page.url()}\n${await page.locator('body').innerText().catch(() => '')}`)
    await shot(page, 'open_deal_fail')
    throw new Error(`openDealTab ${dest} landed ${page.url()}: ${err.message}`)
  }
  const tabBtn = page.getByRole('tab', { name: new RegExp(`^${tab}$`, 'i') }).first()
  if (await tabBtn.isVisible({ timeout: 1500 }).catch(() => false)) {
    await tabBtn.click().catch(() => {})
  }
  await page.getByText(/Upcoming|Overdue|Due Today|Add Task/i).first().waitFor({ state: 'visible', timeout: 20000 })
}

async function openTaskEmail(page, taskName) {
  const kebab = page.getByRole('button', { name: new RegExp(`Actions for ${taskName}`, 'i') }).first()
  await kebab.scrollIntoViewIfNeeded().catch(() => {})
  if (!(await kebab.isVisible({ timeout: 8000 }).catch(() => false))) {
    return { ok: false, text: `no actions for ${taskName}` }
  }
  await kebab.click()
  const item = page.getByRole('menuitem', { name: /Email transaction party|Complete this task/i }).first()
  await item.waitFor({ state: 'visible', timeout: 5000 })
  await item.click()
  const dlg = page.getByRole('dialog').last()
  const opened = await dlg.waitFor({ state: 'visible', timeout: 20000 }).then(() => true).catch(() => false)
  if (!opened) return { ok: false, text: 'dialog missing' }
  await page.waitForTimeout(800)
  const message = await dlg.locator('textarea').first().inputValue().catch(() => '')
  const subject = await dlg.locator('input[type="text"]').first().inputValue().catch(() => '')
  return {
    ok: true,
    text: `${await dlg.innerText()}\nSUBJECT_VALUE:${subject}\nMESSAGE_VALUE:${message}`,
    message,
    subject,
  }
}

async function run() {
  console.log('APP', APP)
  const pageErrors = []
  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME,
    args: [
      '--disable-gpu',
      '--disable-software-rasterizer',
      '--disable-dev-shm-usage',
      '--disable-extensions',
      '--disable-background-networking',
      '--mute-audio',
      '--no-first-run',
      '--no-default-browser-check',
      '--renderer-process-limit=1',
      '--js-flags=--max-old-space-size=256',
    ],
  })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 800 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(18000)
  page.on('pageerror', (err) => pageErrors.push(String(err)))

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.locator('#login-email').waitFor({ state: 'visible', timeout: 20000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    const mfa = await page.getByLabel('Two-step verification form').waitFor({ timeout: 2500 }).then(() => true).catch(() => false)
    if (mfa) {
      log('login', 'FAIL', 'MFA')
      return
    }
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 30000 })
    await dismissOverlays(page)
    if (page.url().includes('/login')) {
      log('login', 'FAIL', await page.locator('[role="alert"]').innerText().catch(() => page.url()))
      return
    }
    log('login', 'PASS', page.url())

    await openDealTab(page, FILES.elm, 'tasks')
    let body = await page.locator('body').innerText()
    dump('chrome_f14_tasks', body)
    await shot(page, 'chrome_f14_tasks')
    const plan14 = await openTaskEmail(page, 'Appraisal Ordered')
    dump('chrome_f14_plan', plan14.text)
    await shot(page, 'chrome_f14_plan')
    log('f14-plan-open', plan14.ok ? 'PASS' : 'FAIL', plan14.ok ? '' : plan14.text)
    if (plan14.ok) {
      const blob = plan14.text + (plan14.message || '')
      log('f14-question-copy', /has the appraisal been ordered/i.test(blob) ? 'PASS' : 'FAIL')
      log('f14-not-staff-notes', /email the buyer and ask/i.test(blob) ? 'FAIL' : 'PASS')
    }
    await closeDialog(page)

    await openDealTab(page, FILES.maple, 'tasks')
    body = await page.locator('body').innerText()
    dump('chrome_f15_tasks', body)
    await shot(page, 'chrome_f15_tasks')
    const handledIdx = body.search(/Handled by AI/i)
    const beforeHandled = handledIdx >= 0 ? body.slice(0, handledIdx) : body
    log('f15-buyer-welcome-open', /Buyer Welcome/i.test(beforeHandled) ? 'PASS' : 'FAIL')
    log(
      'f15-not-only-in-ai-group',
      handledIdx >= 0 && /Buyer Welcome/i.test(body.slice(handledIdx)) && !/Buyer Welcome/i.test(beforeHandled)
        ? 'FAIL'
        : 'PASS',
    )

    const plan19 = await openTaskEmail(page, 'Inspection Response Reminder')
    dump('chrome_f19_plan', plan19.text)
    await shot(page, 'chrome_f19_plan')
    log('f19-plan-open', plan19.ok ? 'PASS' : 'FAIL', plan19.ok ? '' : plan19.text)
    if (plan19.ok) {
      const blob = plan19.text + (plan19.message || '')
      log('f19-not-tbd', /\bTBD\b/.test(blob) ? 'FAIL' : 'PASS')
      log('f19-has-date', /September 14, 2026/i.test(blob) ? 'PASS' : 'FAIL', (plan19.message || '').slice(0, 220))
    }
    await closeDialog(page)

    await openDealTab(page, FILES.nocontract, 'tasks')
    body = await page.locator('body').innerText()
    dump('chrome_f18_tasks', body)
    await shot(page, 'chrome_f18_tasks')
    const plan18 = await openTaskEmail(page, 'Order Title')
    dump('chrome_f18_plan', plan18.text)
    await shot(page, 'chrome_f18_plan')
    log('f18-plan-open', plan18.ok ? 'PASS' : 'FAIL', plan18.ok ? '' : plan18.text)
    if (plan18.ok) {
      const sendBtn = page.getByRole('dialog').last().getByRole('button', { name: /Send/i }).first()
      const sendEnabled = await sendBtn.isEnabled().catch(() => false)
      log('f18-send-disabled', sendEnabled ? 'FAIL' : 'PASS')
      log('f18-needs-purchase-agreement', /purchase agreement/i.test(plan18.text) ? 'PASS' : 'FAIL')
    }
    await closeDialog(page)

    await openDealTab(page, FILES.dual, 'tasks')
    body = await page.locator('body').innerText()
    dump('chrome_f28_tasks', body)
    await shot(page, 'chrome_f28_tasks')
    const titleHits = [...body.matchAll(/Deliver Title/g)].length
    log('f28-two-deliver-title-on-page', titleHits >= 2 ? 'PASS' : 'FAIL', `hits=${titleHits}`)
    log('f28-buyer-utility-on-page', /Deliver Utility Info/i.test(body) ? 'PASS' : 'FAIL')

    await openDealTab(page, FILES.confirm, 'tasks')
    const plan29 = await openTaskEmail(page, 'Confirm Title Order')
    dump('chrome_f29_plan', plan29.text)
    await shot(page, 'chrome_f29_plan')
    log('f29-plan-open', plan29.ok ? 'PASS' : 'FAIL', plan29.ok ? '' : plan29.text)
    if (plan29.ok) {
      const blob = plan29.text + (plan29.message || '')
      log('f29-courtesy-coop', /as a courtesy to TitleOther Co-op/i.test(blob) ? 'PASS' : 'FAIL', (plan29.message || '').slice(0, 220))
      log('f29-not-title-rep', /as a courtesy to TitleOther(?! Co-op)/i.test(blob) ? 'FAIL' : 'PASS')
    }
    await closeDialog(page)

    await openDealTab(page, FILES.utility, 'tasks')
    const plan30 = await openTaskEmail(page, 'Deliver Utility Info')
    dump('chrome_f30_plan', plan30.text)
    await shot(page, 'chrome_f30_plan')
    log('f30-plan-open', plan30.ok ? 'PASS' : 'FAIL', plan30.ok ? '' : plan30.text)
    if (plan30.ok) {
      const blob = plan30.text + (plan30.message || '')
      const sendBtn = page.getByRole('dialog').last().getByRole('button', { name: /Send/i }).first()
      const sendEnabled = await sendBtn.isEnabled().catch(() => false)
      log('f30-can-send', sendEnabled ? 'PASS' : 'WARN', 'listing utility should be sendable')
      log('f30-to-coop', /\+coop@/i.test(blob) ? 'PASS' : 'FAIL')
      log('f30-not-blocked-on-buyer', /needs the buyer/i.test(blob) ? 'FAIL' : 'PASS')
    }
    await closeDialog(page)

    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.getByRole('heading', { name: /Needs You/i }).waitFor({ timeout: 20000 })
    await page.getByText(/\d+ waiting/i).first().waitFor({ timeout: 45000 }).catch(() => {})
    await dismissOverlays(page)
    body = await page.locator('body').innerText()
    dump('chrome_f22_needs_you', body)
    await shot(page, 'chrome_f22_needs_you')
    log(
      'f22-recovery-verbs-on-first-screen',
      /Add contact|Upload document|Complete your profile|Change due date/i.test(body) ? 'PASS' : 'FAIL',
    )
    log(
      'f22-cedar-on-queue',
      /400 Test Cedar St/i.test(body) ? 'PASS' : 'WARN',
      'cedar should appear in Needs You',
    )

    await openDealTab(page, FILES.cedar, 'tasks')
    body = await page.locator('body').innerText()
    dump('chrome_f16_cedar_tasks', body)
    await shot(page, 'chrome_f16_cedar_tasks')
    const handledCedar = body.search(/Handled by AI/i)
    const beforeCedar = handledCedar >= 0 ? body.slice(0, handledCedar) : body
    log(
      'f16-assisted-welcome-open',
      /Buyer Welcome/i.test(beforeCedar) ? 'PASS' : 'FAIL',
      'Cedar is Assisted; named emails stay on the open list',
    )
  } catch (err) {
    log('chrome.fatal', 'FAIL', err.stack || String(err))
    await shot(page, 'chrome_fatal')
    dump('chrome_fatal', await page.locator('body').innerText().catch(() => ''))
  } finally {
    if (pageErrors.length) log('pageerrors', 'WARN', pageErrors.slice(0, 8).join('\n'))
    writeFileSync(path.join(OUT, 'chrome_findings.json'), JSON.stringify({ findings }, null, 2))
    const fails = findings.filter((f) => f.result === 'FAIL')
    console.log(`\nCHROME ${findings.length - fails.length} ok / ${fails.length} fail / ${findings.length} total`)
    await browser.close().catch(() => {})
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
