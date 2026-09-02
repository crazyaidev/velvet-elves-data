/**
 * Staging Chrome pass for Features 14–32.
 * Opens wizard fields, Tasks, Complete this task, Settings, Needs You, Email.
 * Does not Send, Generate, Run AI tasks, Disconnect, or Change status.
 *
 *   node feature14_32_staging_verify.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_feature14_32')
mkdirSync(OUT, { recursive: true })
const SEED_PATH = path.join(OUT, 'seed.json')

const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const APP = (process.env.QA_APP || 'https://app.stage.velvetelves.com').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

const findings = []
function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 6000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 900) : ''}`)
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

async function pickSelect(page, aria, optionRe) {
  const trigger = page.getByLabel(aria).first()
  await trigger.scrollIntoViewIfNeeded()
  await trigger.click()
  const opt = page.getByRole('option', { name: optionRe }).first()
  await opt.waitFor({ state: 'visible', timeout: 8000 })
  await opt.click()
}

async function login(page) {
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.locator('#login-email').waitFor({ state: 'visible', timeout: 25000 })
  await page.locator('#login-email').fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /sign in/i }).click()
  const mfa = await page.getByLabel('Two-step verification form').waitFor({ timeout: 4000 }).then(() => true).catch(() => false)
  if (mfa) {
    log('login', 'FAIL', 'MFA form')
    return false
  }
  await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 40000 }).catch(() => {})
  await dismissOverlays(page)
  if (page.url().includes('/login')) {
    log('login', 'FAIL', await page.locator('[role="alert"]').innerText().catch(() => page.url()))
    return false
  }
  log('login', 'PASS', page.url())
  return true
}

async function openDealTab(page, txId, tab) {
  const url = `${APP}/transactions/${txId}${tab ? `?tab=${tab}` : ''}`
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.waitForTimeout(1200)
  await dismissOverlays(page)
  if (tab) {
    const tabBtn = page.getByRole('tab', { name: new RegExp(tab, 'i') }).first()
    if (await tabBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await tabBtn.click().catch(() => {})
      await page.waitForTimeout(800)
    }
  }
}

async function closeDialog(page) {
  const dlg = page.getByRole('dialog').last()
  if (await dlg.isVisible().catch(() => false)) {
    await dlg.getByRole('button', { name: /close|cancel|i.ll handle it myself/i }).first().click({ timeout: 3000 }).catch(() => {})
    await page.keyboard.press('Escape').catch(() => {})
    await page.waitForTimeout(400)
  }
}

async function openTaskEmail(page, taskName) {
  const row = page.locator('li, article, div').filter({ hasText: new RegExp(`^${taskName}|${taskName}`) }).filter({ has: page.getByRole('button', { name: /Actions for/i }) }).first()
  const kebab = page.getByRole('button', { name: new RegExp(`Actions for ${taskName}`, 'i') }).first()
  await kebab.scrollIntoViewIfNeeded().catch(() => {})
  const visible = await kebab.isVisible({ timeout: 8000 }).catch(() => false)
  if (!visible) return { ok: false, text: await page.locator('body').innerText() }
  await kebab.click()
  const item = page.getByRole('menuitem', { name: /Email transaction party/i })
  await item.waitFor({ state: 'visible', timeout: 5000 })
  await item.click()
  const dlg = page.getByRole('dialog').last()
  const opened = await dlg.waitFor({ state: 'visible', timeout: 25000 }).then(() => true).catch(() => false)
  if (!opened) return { ok: false, text: 'dialog missing' }
  await page.waitForTimeout(1500)
  const text = await dlg.innerText()
  return { ok: true, text, dialog: dlg }
}

async function previewOvernight(page) {
  await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.getByRole('heading', { name: /AI & Automation/i }).waitFor({ timeout: 25000 })
  const how = page.getByRole('button', { name: /How it runs/i }).first()
  if (await how.isVisible({ timeout: 2000 }).catch(() => false)) await how.click().catch(() => {})
  const previewBtn = page.getByRole('button', { name: /Preview next (run|tick)/i }).first()
  await previewBtn.scrollIntoViewIfNeeded()
  const overnight = await page.locator('body').innerText()
  await previewBtn.click()
  const dlg = page.getByRole('alertdialog').or(page.getByRole('dialog')).first()
  const opened = await dlg.waitFor({ state: 'visible', timeout: 60000 }).then(() => true).catch(() => false)
  const ptxt = opened ? await dlg.innerText() : ''
  if (opened) await dlg.getByRole('button', { name: /Got it/i }).click().catch(() => {})
  return { overnight, preview: ptxt, opened }
}

function bannedHits(text) {
  const hits = []
  if (/library letters/i.test(text)) hits.push('library letters')
  if (/written by AI/i.test(text)) hits.push('written by AI')
  if (/named letters/i.test(text) && !/named emails/i.test(text)) hits.push('named letters leftover')
  return hits
}

async function run() {
  if (!existsSync(SEED_PATH)) {
    console.error('Missing seed.json. Run feature14_32_seed.mjs first.')
    process.exit(2)
  }
  const seed = JSON.parse(readFileSync(SEED_PATH, 'utf8'))
  const f = seed.files

  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME,
    args: [
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--disable-extensions',
      '--mute-audio',
      '--no-first-run',
      '--no-default-browser-check',
      '--renderer-process-limit=1',
    ],
  })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(25000)

  try {
    if (!(await login(page))) return

    const section = async (name, fn) => {
      try {
        await fn()
      } catch (err) {
        log(name, 'FAIL', err.stack || String(err))
        await dump(`${name}_err`, await page.locator('body').innerText().catch(() => ''))
        await shot(page, `${name}_err`)
        await page.keyboard.press('Escape').catch(() => {})
        await closeDialog(page)
      }
    }

    await section('f14-wizard', async () => {
      await page.goto(`${APP}/transactions/new`, { waitUntil: 'domcontentloaded', timeout: 60000 })
      await page.waitForTimeout(1500)
      const discard = page.getByRole('button', { name: /Discard/i }).first()
      if (await discard.isVisible({ timeout: 2500 }).catch(() => false)) {
        await discard.click()
        await page.waitForTimeout(800)
      }
      await page.getByRole('radiogroup', { name: /Who are you representing/i }).waitFor({ timeout: 20000 })
      await page.getByRole('radio', { name: /^Buyer$/ }).click()
      await page.getByRole('button', { name: /Skip upload/i }).click()
      await page.getByLabel('Is the buyer getting a mortgage?').waitFor({ timeout: 20000 })
      log(
        'f14-wizard-appraisal-hidden-on-financed',
        (await page.getByLabel('Appraisal on this cash deal?').count()) === 0 ? 'PASS' : 'FAIL',
      )
      await pickSelect(page, 'Is the buyer getting a mortgage?', /^No$/)
      await page.waitForTimeout(500)
      const appr = page.getByLabel('Appraisal on this cash deal?')
      const apprVisible = await appr.isVisible().catch(() => false)
      log('f14-wizard-appraisal-shown-on-cash', apprVisible ? 'PASS' : 'FAIL')
      if (apprVisible) {
        await pickSelect(page, 'Appraisal on this cash deal?', /Yes/)
        const helper = await page.getByText(/Appraisal follow-up tasks will be created/i).isVisible().catch(() => false)
        log('f14-wizard-yes-helper', helper ? 'PASS' : 'FAIL')
        await dump('f14_wizard', await page.locator('body').innerText())
        await shot(page, 'f14_wizard')
      }
      await pickSelect(page, 'Who orders title', /Buyer/)
      const titleCaption = await page.getByText(/Order Title|Confirm Title Order/i).first().innerText().catch(() => '')
      log('f29-wizard-title-caption-present', /Order Title|Confirm Title Order/i.test(titleCaption) ? 'PASS' : 'WARN', titleCaption)
      await page.getByRole('button', { name: /Exit/i }).click().catch(() => {})
      const discard2 = page.getByRole('button', { name: /Discard|Leave|Don't save/i }).first()
      if (await discard2.isVisible({ timeout: 2500 }).catch(() => false)) await discard2.click().catch(() => {})
    })

    async function checkPlan(id, tx, taskName, expectTo, expectNotTo, extraRe) {
      try {
        await openDealTab(page, tx.id, 'tasks')
        await page.waitForTimeout(1500)
        const bodyText = await page.locator('body').innerText()
        dump(`${id}_tasks`, `${tx.address}\n${bodyText}`)
        await shot(page, `${id}_tasks`)
        const hasTask = new RegExp(taskName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i').test(bodyText)
        log(`${id}-task-listed`, hasTask ? 'PASS' : 'FAIL', taskName)
        if (!hasTask) return
        const plan = await openTaskEmail(page, taskName)
        dump(`${id}_plan`, plan.text)
        await shot(page, `${id}_plan`)
        if (!plan.ok) {
          log(`${id}-plan-open`, 'FAIL', String(plan.text).slice(0, 300))
          return
        }
        log(`${id}-plan-open`, 'PASS')
        if (expectTo) {
          const ok = expectTo.every((e) => plan.text.includes(e))
          log(`${id}-to`, ok ? 'PASS' : 'FAIL', plan.text.match(/To:[\s\S]{0,200}/)?.[0] || plan.text.slice(0, 250))
        }
        if (expectNotTo) {
          const toBlock = plan.text.split(/Cc:/i)[0] || plan.text
          const bad = expectNotTo.some((e) => new RegExp(e, 'i').test(toBlock))
          log(`${id}-not-to`, bad ? 'FAIL' : 'PASS')
        }
        if (extraRe) log(`${id}-copy`, extraRe.test(plan.text) ? 'PASS' : 'FAIL')
        log(`${id}-left-unsent`, 'PASS')
        await closeDialog(page)
      } catch (err) {
        log(`${id}-plan-open`, 'FAIL', err.message || String(err))
        await shot(page, `${id}_err`)
        await closeDialog(page)
      }
    }

    await section('f14-plans', async () => {
      await checkPlan(
        'f14-buy',
        f.buyCash,
        'Appraisal Ordered',
        [seed.emails.buyer],
        [seed.emails.lender, seed.emails.coop, 'elf@'],
        /Appraisal Ordered/i,
      )
      const buyPlan = existsSync(path.join(OUT, 'f14-buy_plan.txt'))
        ? readFileSync(path.join(OUT, 'f14-buy_plan.txt'), 'utf8')
        : ''
      log(
        'f14-buy-not-instruction-leak',
        /email the buyer and ask/i.test(buyPlan) ? 'FAIL' : buyPlan ? 'PASS' : 'FAIL',
        'client letter must not narrate the agent instruction',
      )
      await checkPlan('f14-buy-completed', f.buyCash, 'Appraisal Completed', [seed.emails.buyer], [seed.emails.coop])
      await checkPlan(
        'f14-sell',
        f.sellCash,
        'Appraisal Ordered',
        [seed.emails.coop],
        [seed.emails.buyer, seed.emails.lender],
      )
      const sellPlan = existsSync(path.join(OUT, 'f14-sell_plan.txt'))
        ? readFileSync(path.join(OUT, 'f14-sell_plan.txt'), 'utf8')
        : ''
      log('f14-sell-cc-tc', /Cc:[\s\S]*elf@cbstiles\.com|Transaction Coordinator/i.test(sellPlan) ? 'PASS' : 'WARN', 'do not Send; TC is a live mailbox')
    })

    await section('f15-25', async () => {
    await openDealTab(page, f.maple.id, 'tasks')
    await page.waitForTimeout(1200)
    const mapleTasks = await page.locator('body').innerText()
    dump('f15_tasks', mapleTasks)
    await shot(page, 'f15_tasks')
    log('f15-buyer-welcome-open', /Buyer Welcome/i.test(mapleTasks) && !/Buyer Welcome[\s\S]{0,80}Completed/i.test(mapleTasks) ? 'PASS' : 'WARN')
    const zap = page.getByRole('button', { name: /How it runs|Manual|Assisted|Autopilot/i }).first()
    if (await zap.isVisible({ timeout: 3000 }).catch(() => false)) {
      await zap.click()
      const menu = await page.locator('[role="menu"], [data-radix-menu-content]').first().innerText().catch(() => '')
      dump('f15_posture', menu)
      log('f15-manual-caption', /Named emails wait until you switch this deal off Manual/i.test(menu) ? 'PASS' : 'FAIL', menu.slice(0, 400))
      await page.keyboard.press('Escape')
    }
    const prev15 = await previewOvernight(page)
    dump('f15_preview', prev15.preview)
    await shot(page, 'f15_preview')
    log('f15-preview-opened', prev15.opened ? 'PASS' : 'FAIL')
    log(
      'f15-maple-not-in-would-send',
      /200 Test Maple/i.test(prev15.preview) && /would send/i.test(prev15.preview) && !/0 emails/i.test(prev15.preview)
        ? 'FAIL'
        : 'PASS',
      prev15.preview.slice(0, 500),
    )

    // Feature 16 Assisted welcome plan
    await checkPlan('f16', f.maple, 'Buyer Welcome', [seed.emails.buyer], [])
    const f16 = existsSync(path.join(OUT, 'f16_plan.txt')) ? readFileSync(path.join(OUT, 'f16_plan.txt'), 'utf8') : ''
    log('f16-give-back-absent', /Give this back to the AI/i.test(f16) ? 'FAIL' : 'PASS')
    log('f16-written-by-ai', /written by AI/i.test(f16) ? 'FAIL' : 'PASS')

    // Feature 17 Preview only (do not Run)
    await openDealTab(page, f.pine.id)
    await shot(page, 'f17_header')
    const prev17 = await previewOvernight(page)
    dump('f17_preview', `${prev17.overnight.slice(0, 3000)}\n---\n${prev17.preview}`)
    await shot(page, 'f17_preview')
    log('f17-preview-only', prev17.opened ? 'PASS' : 'FAIL', 'Got it; did not confirm Run AI tasks')
    log('f17-named-emails-allowed', /Named emails|Named letters/i.test(prev17.overnight) ? 'PASS' : 'WARN')

    // Feature 18 missing email
    await openDealTab(page, f.cedar.id, 'tasks')
    const cedarBody = await page.locator('body').innerText()
    dump('f18_cedar_tasks', cedarBody)
    await shot(page, 'f18_cedar_tasks')
    const cedarPlan = await openTaskEmail(page, 'Buyer Welcome')
    dump('f18_cedar_plan', cedarPlan.text)
    await shot(page, 'f18_cedar_plan')
    log('f18-no-guessed-to', /can_send|No Buyer contact with an email|no contact on file/i.test(cedarPlan.text) || !/@gmail\.com/.test((cedarPlan.text.match(/To:[\s\S]{0,120}/) || [''])[0]) ? 'PASS' : 'FAIL')
    await closeDialog(page)
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2000)
    await dismissOverlays(page)
    const ny = await page.locator('body').innerText()
    dump('f18_needs_you', ny)
    await shot(page, 'f18_needs_you')
    log('f18-needs-you-add-contact', /Add contact/i.test(ny) ? 'PASS' : 'WARN', 'look for Cedar / missing email recovery')
    log('f18-no-giveback-on-missing-email', /Give this back to the AI/i.test(ny) && /400 Test Cedar/i.test(ny) ? 'WARN' : 'PASS')

    await openDealTab(page, f.noContract.id, 'tasks')
    const ncPlan = await openTaskEmail(page, 'Order Title')
    dump('f18_nocontract_plan', ncPlan.text)
    await shot(page, 'f18_nocontract_plan')
    log(
      'f18-nocontract-blocked-or-no-attach-claim',
      /Upload document|blocked|follow up with the contract/i.test(ncPlan.text) && !/Attached you'll find/i.test(ncPlan.text)
        ? /can complete this for you/i.test(ncPlan.text)
          ? 'FAIL'
          : 'PASS'
        : /Attached you'll find/i.test(ncPlan.text)
          ? 'FAIL'
          : 'WARN',
      'Order Title must not send a promised contract that is not on the file',
    )
    await closeDialog(page)

    // Feature 19 inspection reminder
    await checkPlan('f19', f.pine, 'Inspection Response Reminder', [EMAIL], [seed.emails.buyer])
    const insp = existsSync(path.join(OUT, 'f19_plan.txt')) ? readFileSync(path.join(OUT, 'f19_plan.txt'), 'utf8') : ''
    log('f19-deadline-only', /repair request|accept or reject the inspection|negotiat/i.test(insp) ? 'FAIL' : 'PASS')
    log('f19-deadline-filled', /deadline is TBD/i.test(insp) ? 'NEEDS_WORK' : 'PASS')

    // Feature 20 skip disconnect
    await page.goto(`${APP}/settings/connections`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(1500)
    dump('f20_connections', await page.locator('body').innerText())
    await shot(page, 'f20_connections')
    log('f20-disconnect-visible', /Disconnect/i.test(await page.locator('body').innerText()) ? 'PASS' : 'WARN')
    log('f20-did-not-disconnect', 'SKIP', 'OAuth reconnect is not available in this pass')

    // Feature 21 Intelligence Email
    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2000)
    const intel = await page.locator('body').innerText()
    dump('f21_intel', intel)
    await shot(page, 'f21_intel')
    log('f21-title-email', /^Email$/m.test(intel) || /Intelligence › Email|Intelligence > Email/i.test(intel) ? 'PASS' : 'WARN')
    const sendAll = page.getByRole('button', { name: /Send all ready/i }).first()
    if (await sendAll.isEnabled().catch(() => false)) {
      await sendAll.click()
      const dlg = page.getByRole('alertdialog').or(page.getByRole('dialog')).first()
      const opened = await dlg.waitFor({ state: 'visible', timeout: 10000 }).then(() => true).catch(() => false)
      dump('f21_send_all', opened ? await dlg.innerText() : 'no dialog')
      await shot(page, 'f21_send_all')
      if (opened) {
        await dlg.getByRole('button', { name: /cancel|close/i }).first().click().catch(() => {})
        log('f21-send-all-cancelled', 'PASS')
      } else {
        log('f21-send-all-cancelled', 'WARN', 'no confirm dialog')
      }
    } else {
      log('f21-send-all-idle', 'PASS', 'Send all ready not enabled or not present')
    }

    // Feature 22 Needs You recoveries
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2000)
    const ny2 = await page.locator('body').innerText()
    dump('f22_needs_you', ny2)
    await shot(page, 'f22_needs_you')
    log('f22-add-contact', /Add contact/i.test(ny2) ? 'PASS' : 'WARN')
    log('f22-upload-document', /Upload document/i.test(ny2) ? 'PASS' : 'WARN')
    log('f22-switch-off-manual', /Switch this deal off Manual/i.test(ny2) ? 'PASS' : 'WARN')
    log('f22-try-now-admin', /Try now \(this deal only\)/i.test(ny2) ? 'PASS' : 'WARN')

    // Feature 23 inbound on Maple Email tab
    await openDealTab(page, f.maple.id, 'email')
    await page.waitForTimeout(1500)
    const folders = page.getByRole('tablist', { name: /Email folders/i })
    if (await folders.getByRole('tab', { name: /Inbox/i }).isVisible().catch(() => false)) {
      await folders.getByRole('tab', { name: /Inbox/i }).click()
      await page.waitForTimeout(1200)
    }
    const inbox = await page.locator('body').innerText()
    dump('f23_inbox', inbox)
    await shot(page, 'f23_inbox')
    log('f23-question-kept', /closing date/i.test(inbox) ? 'PASS' : 'WARN')
    log('f23-statement-kept', /title commitment is ready/i.test(inbox) ? 'PASS' : 'WARN')
    log('f23-wire-kept', /wire instructions/i.test(inbox) ? 'PASS' : 'WARN')
    log('f23-banking-kept', /banking details/i.test(inbox) ? 'PASS' : 'WARN')
    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(1500)
    const readyTab = page.getByRole('tab', { name: /Ready/i }).first()
    if (await readyTab.isVisible().catch(() => false)) await readyTab.click().catch(() => {})
    const readyTxt = await page.locator('body').innerText()
    dump('f23_ready', readyTxt)
    await shot(page, 'f23_ready')
    log(
      'f23-money-not-ready',
      /wire instructions|banking details/i.test(readyTxt) && /Ready to send/i.test(readyTxt)
        ? 'FAIL'
        : 'PASS',
    )

    // Feature 24 Ask AI
    await openDealTab(page, f.maple.id)
    const ask = page.getByRole('button', { name: /Ask AI|Ask Aime/i }).first()
    if (await ask.isVisible({ timeout: 4000 }).catch(() => false)) await ask.click()
    const pane = page.getByTestId('agent-pane')
    const paneOpen = await pane.waitFor({ state: 'visible', timeout: 8000 }).then(() => true).catch(() => false)
    if (paneOpen) {
      const box = pane.locator('textarea, [contenteditable="true"], input[placeholder*="Ask"]').last()
      await box.click({ timeout: 5000 }).catch(() => {})
      await box.fill(`Change the closing date on ${f.maple.address} to September 15, 2026.`).catch(async () => {
        await page.keyboard.type(`Change the closing date on ${f.maple.address} to September 15, 2026.`)
      })
      await page.keyboard.press('Enter')
      await page.waitForTimeout(12000)
      dump('f24_ask', await pane.innerText().catch(() => page.locator('body').innerText()))
      await shot(page, 'f24_ask')
      const paneTxt = await pane.innerText().catch(() => '')
      const dismiss = page.getByRole('button', { name: /Dismiss/i }).first()
      if (await dismiss.isVisible().catch(() => false)) {
        await dismiss.click()
        log('f24-preview-then-dismiss', 'PASS')
      } else {
        log('f24-preview-then-dismiss', /preview|would move|closing date/i.test(paneTxt) ? 'WARN' : 'FAIL', paneTxt.slice(0, 500))
      }
    } else {
      log('f24-preview-then-dismiss', 'FAIL', 'Ask AI pane did not open')
    }
    const header = await page.locator('body').innerText()
    log('f24-date-unchanged', /Sep(tember)? 15, 2026/i.test(header) && /Approve/i.test(header) ? 'WARN' : /Oct(ober)? 15, 2026/i.test(header) ? 'PASS' : 'WARN', 'header should still show October 15, 2026')

    // Feature 25 digest / fine-tune
    await page.goto(`${APP}/settings/notifications`, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {})
    await page.waitForTimeout(1000)
    dump('f25_notifications', await page.locator('body').innerText().catch(() => page.url()))
    await shot(page, 'f25_notifications')
    const prev25 = await previewOvernight(page)
    dump('f25_overnight', prev25.overnight)
    await shot(page, 'f25_overnight')
    const fine = page.getByRole('button', { name: /Fine-tune|Email replies|Automation rules|Confidence gates/i }).first()
    if (await fine.isVisible().catch(() => false)) await fine.click().catch(() => {})
    const fineTxt = await page.locator('body').innerText()
    dump('f25_finetune', fineTxt)
    await shot(page, 'f25_finetune')
    log('f25-no-run-in-finetune', /Run AI tasks \(sends deal email\)/i.test(fineTxt) && /Never automatic/i.test(fineTxt) ? 'WARN' : 'PASS')
    log('f25-never-automatic', /Never automatic/i.test(fineTxt) ? 'PASS' : 'WARN')

    })

    await section('f27-32', async () => {
    async function listTasks(id, tx, checks) {
      await openDealTab(page, tx.id, 'tasks')
      await page.waitForTimeout(1500)
      const text = await page.locator('body').innerText()
      dump(`${id}_tasks`, text)
      await shot(page, `${id}_tasks`)
      for (const [cid, re, want] of checks) {
        const hit = re.test(text)
        log(`${id}-${cid}`, hit === want ? 'PASS' : 'FAIL', `${re} want=${want}`)
      }
    }

    await listTasks('f27-buy', f.titleUs, [
      ['closing-gift-once', /Closing Gift/g, true],
    ])
    const giftBuy = existsSync(path.join(OUT, 'f27-buy_tasks.txt'))
      ? (readFileSync(path.join(OUT, 'f27-buy_tasks.txt'), 'utf8').match(/Closing Gift/g) || []).length
      : 0
    log('f27-buy-one-gift', giftBuy === 1 ? 'PASS' : 'FAIL', String(giftBuy))
    await listTasks('f27-sell', f.utility, [
      ['closing-gift', /Closing Gift/, true],
      ['lockbox', /Schedule Pick Up of Sign and Lockbox/, true],
      ['mls-sold', /Change MLS Listing Status to Sold/, true],
    ])

    await listTasks('f28', f.dual, [
      ['buyer-welcome', /Buyer Welcome/, true],
      ['seller-welcome', /Seller Welcome/, true],
      ['no-coop-welcome', /Co-op Agent Welcome/, false],
      ['order-title', /Order Title/, true],
      ['both-insp-reminder', /Inspection Response Reminder/, true],
      ['both-insp-neg', /Inspection Negotiated/, true],
    ])
    const dualTxt = existsSync(path.join(OUT, 'f28_tasks.txt'))
      ? readFileSync(path.join(OUT, 'f28_tasks.txt'), 'utf8')
      : ''
    log('f28-two-insp-reminders', (dualTxt.match(/Inspection Response Reminder/g) || []).length >= 2 ? 'PASS' : 'FAIL')
    log('f28-no-utility-to-coop', /Deliver Utility Info/i.test(dualTxt) ? 'FAIL' : 'PASS')
    log('f28-one-closing-gift', (dualTxt.match(/Closing Gift/g) || []).length === 1 ? 'PASS' : 'FAIL')
    log('f28-one-deliver-title', (dualTxt.match(/Deliver Title/g) || []).length <= 2 ? 'WARN' : 'FAIL', 'Deliver Title duplicated?')

    await checkPlan('f29-order', f.titleUs, 'Order Title', [seed.emails.title], [])
    await checkPlan('f29-confirm', f.titleOther, 'Confirm Title Order', [seed.emails.title], [])
    const confirmBody = existsSync(path.join(OUT, 'f29-confirm_plan.txt'))
      ? readFileSync(path.join(OUT, 'f29-confirm_plan.txt'), 'utf8')
      : ''
    log('f29-courtesy', /as a courtesy/i.test(confirmBody) ? 'PASS' : 'FAIL')
    log('f29-not-followup', /has title been ordered/i.test(confirmBody) ? 'FAIL' : 'PASS')

    await checkPlan('f30', f.utility, 'Deliver Utility Info', [seed.emails.coop], [seed.emails.seller])
    const utilPlan = existsSync(path.join(OUT, 'f30_plan.txt')) ? readFileSync(path.join(OUT, 'f30_plan.txt'), 'utf8') : ''
    log(
      'f30-can-send-to-coop',
      /needs a buyer on the file/i.test(utilPlan) ? 'FAIL' : /To:[\s\S]*coop@gmail/i.test(utilPlan) ? 'PASS' : 'WARN',
    )

    await checkPlan('f31', f.warrantyUs, 'Order Home Warranty', [EMAIL], [/warranty\.com|ahs\.com|first american/i])
    const wh = existsSync(path.join(OUT, 'f31_plan.txt')) ? readFileSync(path.join(OUT, 'f31_plan.txt'), 'utf8') : ''
    log('f31-internal-reminder', /reminder to order the home warranty|send the invoice to the title company/i.test(wh) ? 'PASS' : 'FAIL')
    await openDealTab(page, f.utility.id, 'tasks')
    const utilTasks = await page.locator('body').innerText()
    log('f31-listing-confirm-warranty', /Confirm Home Warranty/i.test(utilTasks) ? 'PASS' : 'FAIL')

    await listTasks('f32-list', f.utility, [['no-seller-insp-completed', /Inspection Completed/, false]])
    await listTasks('f32-dual', f.dual, [['buyer-insp-completed-ok', /Inspection Completed/, true]])
    })

    // Feature 26 banned words across captured surfaces
    const scans = ['f15_preview', 'f17_preview', 'f21_intel', 'f25_overnight', 'f25_finetune', 'f14_wizard']
    const allHits = []
    for (const n of scans) {
      const pth = path.join(OUT, `${n}.txt`)
      if (!existsSync(pth)) continue
      allHits.push(...bannedHits(readFileSync(pth, 'utf8')).map((h) => `${n}:${h}`))
    }
    log('f26-banned-words', allHits.length ? 'FAIL' : 'PASS', allHits.join('; ') || 'none')
  } catch (err) {
    log('harness', 'FAIL', err.stack || String(err))
    await shot(page, 'harness_fail')
  } finally {
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    const counts = findings.reduce((a, fnd) => {
      a[fnd.result] = (a[fnd.result] || 0) + 1
      return a
    }, {})
    console.log('counts', counts)
    await browser.close()
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
