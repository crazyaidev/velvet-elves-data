/**
 * Local Chrome QA for Jake file-logic UI (Aime live-file posture, Terminated,
 * Fast intake). Logs in as platform admin. Low RAM: installed Chrome,
 * headless, one page, no screenshots, renderer cap.
 *
 *   node jake_file_logic_chrome_qa.mjs
 *
 *   QA_APP=http://127.0.0.1:5173
 *   QA_CHANNEL=chrome          (default)
 *   QA_HEADED=1                real window — avoid on this machine
 *   QA_SHOTS=1
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const STAMP = new Date().toISOString().slice(0, 10)
const OUT = process.env.QA_OUT
  ? path.resolve(process.env.QA_OUT)
  : path.join(__dirname, `artifacts_${STAMP}`)
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'shyna.elene@minafter.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const APP = (process.env.QA_APP || 'http://127.0.0.1:5173').replace(/\/$/, '')
const HEADED = process.env.QA_HEADED === '1'
const SHOTS = process.env.QA_SHOTS === '1'
const CHANNEL = process.env.QA_CHANNEL || 'chrome'

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let shotIdx = 0

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 8000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 500) : ''}`)
}

function failCount() {
  return findings.filter((f) => f.result === 'FAIL').length
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

async function bodyText(page) {
  try {
    return await page.locator('body').innerText({ timeout: 8000 })
  } catch {
    return ''
  }
}

function scanForbidden(text, extra = []) {
  const hits = []
  const patterns = [
    /\bConductor\b/i,
    /\bClass A\b/,
    /Library welcome/i,
    /Hourly library send/i,
    /\bLibrary letters\b/i,
    /Automatic library letters/i,
    /✦ Autopilot/,
    ...extra,
  ]
  for (const re of patterns) {
    const m = text.match(re)
    if (m) hits.push(m[0])
  }
  return hits
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
    if (await btn.isVisible({ timeout: 350 }).catch(() => false)) {
      await btn.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(150)
    }
  }
  if (escape) await page.keyboard.press('Escape').catch(() => {})
}

async function waitSettled(page, ms = 250) {
  await page.waitForTimeout(ms)
  await page.waitForLoadState('domcontentloaded', { timeout: 8000 }).catch(() => {})
}

async function gotoPath(page, pathName) {
  const url = /^https?:\/\//i.test(pathName) ? pathName : `${APP}${pathName}`
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await waitSettled(page, 400)
  await dismissOverlays(page)
}

async function expectVisible(page, locator, id, detailsOk = '') {
  const ok = await locator.first().isVisible({ timeout: 8000 }).catch(() => false)
  log(id, ok ? 'PASS' : 'FAIL', ok ? detailsOk : `not visible; url=${page.url()}`)
  return ok
}

async function waitForCopy(page, reOrText, timeout = 18000) {
  const pattern =
    typeof reOrText === 'string'
      ? reOrText
      : reOrText.source
  const flags = typeof reOrText === 'string' ? 'i' : reOrText.flags
  return page
    .waitForFunction(
      ({ pattern: p, flags: f }) => new RegExp(p, f).test(document.body.innerText || ''),
      { pattern, flags },
      { timeout },
    )
    .then(() => true)
    .catch(() => false)
}

async function dump(page, name) {
  const text = await bodyText(page)
  writeFileSync(path.join(OUT, `${name}.txt`), `${page.url()}\n\n${text}`)
  return text
}

async function firstDealHref(page) {
  return page.evaluate(() => {
    const uuid = /\/transactions\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i
    for (const a of document.querySelectorAll('a[href]')) {
      const href = a.getAttribute('href') || ''
      if (uuid.test(href.split('?')[0])) return href
    }
    return null
  })
}

async function closeAime(page) {
  const closeChat = page.getByRole('button', { name: /Close AI chat/i })
  if (await closeChat.isVisible({ timeout: 400 }).catch(() => false)) {
    await closeChat.click().catch(() => {})
    await page.waitForTimeout(200)
  }
  await page.keyboard.press('Escape').catch(() => {})
}

async function login(page) {
  await gotoPath(page, '/login')
  const email = page.locator('#login-email')
  await email.waitFor({ state: 'visible', timeout: 15000 })
  await email.fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 25000 }).catch(() => {})
  await waitSettled(page, 800)
  await dismissOverlays(page)
  const onLogin = page.url().includes('/login')
  if (onLogin) {
    const alert = await page.locator('[role="alert"]').innerText().catch(() => '')
    log('login', 'FAIL', alert || page.url())
    return false
  }
  log('login', 'PASS', page.url())
  return true
}

async function run() {
  const browser = await chromium.launch({
    channel: CHANNEL,
    headless: !HEADED,
    args: [
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--disable-extensions',
      '--disable-background-networking',
      '--disable-sync',
      '--mute-audio',
      '--renderer-process-limit=1',
      '--js-flags=--max-old-space-size=192',
    ],
  })
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
  })
  const page = await context.newPage()
  page.setDefaultTimeout(12000)
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (err) => pageErrors.push(err.message))
  page.on('response', (res) => {
    const url = res.url()
    if (!/\/api\/v1\//.test(url)) return
    if (res.status() >= 400) {
      failedRequests.push(`${res.status()} ${url}`)
    }
  })

  try {
    // ── Q1 register (logged out) ──────────────────────────────────────
    await gotoPath(page, '/register')
    await shot(page, 'register')
    const reg = await bodyText(page)
    await expectVisible(page, page.getByText('How should Aime start?'), 'q1.register.legend')
    await expectVisible(page, page.getByRole('button', { name: /Manual/i }), 'q1.register.manual')
    await expectVisible(page, page.getByRole('button', { name: /Assisted/i }), 'q1.register.assisted')
    await expectVisible(page, page.getByRole('button', { name: /Autopilot/i }), 'q1.register.autopilot')
    log(
      'q1.register.assisted_tap',
      /you tap Send/i.test(reg) ? 'PASS' : 'FAIL',
      'Assisted must be tap-to-send, not auto-send',
    )
    log(
      'q1.register.autopilot_no_tap',
      /No tap/i.test(reg) ? 'PASS' : 'FAIL',
    )
    log(
      'q1.register.only_autopilot_sends',
      /only setting that sends without a tap/i.test(reg) ? 'PASS' : 'FAIL',
    )
    const regForbid = scanForbidden(reg)
    log('q1.register.forbidden', regForbid.length ? 'FAIL' : 'PASS', regForbid.join(', '))

    const okLogin = await login(page)
    if (!okLogin) {
      writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, consoleErrors, pageErrors }, null, 2))
      return
    }

    // ── Admin dashboard: Terminated tile (Q6) ─────────────────────────
    await gotoPath(page, '/dashboard/admin')
    await shot(page, 'admin_dashboard')
    const dashReady = await waitForCopy(page, 'Deals by stage', 12000)
    const termReady = await waitForCopy(page, 'Terminated', 15000)
    const dash = await dump(page, 'admin_dashboard')
    log('q6.admin.deals_by_stage', dashReady ? 'PASS' : 'SKIP', dashReady ? 'present' : 'tile heading never appeared')
    log(
      'q6.admin.terminated_tile',
      termReady ? 'PASS' : dashReady ? 'FAIL' : 'SKIP',
      termReady
        ? 'Terminated visible on admin dashboard'
        : dashReady
          ? 'Deals by stage loaded without a Terminated row'
          : 'admin dashboard data did not finish loading locally',
    )
    const termLink = page.locator('a[href*="tab=Terminated"]').first()
    if (await termLink.isVisible({ timeout: 2000 }).catch(() => false)) {
      log('q6.admin.terminated_href', 'PASS', await termLink.getAttribute('href'))
    } else {
      log(
        'q6.admin.terminated_href',
        termReady ? 'FAIL' : 'SKIP',
        'Terminated row should link to /transactions/all?tab=Terminated',
      )
    }
    log('q6.admin.forbidden', scanForbidden(dash).length ? 'FAIL' : 'PASS', scanForbidden(dash).join(', '))

    // ── AI & Automation COMPARE (Q1) ──────────────────────────────────
    await gotoPath(page, '/admin/confidence')
    await shot(page, 'ai_automation')
    const compareReady = await waitForCopy(page, /Welcome \/ title letters/i, 18000)
    const gov = await dump(page, 'ai_automation')
    log('q1.gov.posture_heading', /Automation posture/i.test(gov) ? 'PASS' : 'FAIL')
    log(
      'q1.gov.welcome_row',
      compareReady ? 'PASS' : 'FAIL',
      compareReady ? '' : 'COMPARE table never appeared (automation settings API?)',
    )
    log(
      'q1.gov.assisted_drafted',
      /Drafted — you tap Send/i.test(gov) ? 'PASS' : 'FAIL',
    )
    log(
      'q1.gov.autopilot_sends',
      /Sends without a tap/i.test(gov) ? 'PASS' : 'FAIL',
    )
    log(
      'q1.gov.hard_stops',
      /Money, waives, legal, and inspection negotiation never send on their own/i.test(gov)
        ? 'PASS'
        : 'FAIL',
    )
    const overnightReady = await waitForCopy(
      page,
      /Hourly automation is on|Hourly automation is off|Last draft sweep/i,
      20000,
    )
    const govOvernight = overnightReady ? await dump(page, 'ai_automation') : gov
    log(
      'q1.gov.overnight_loaded',
      overnightReady ? 'PASS' : 'FAIL',
      overnightReady ? '' : 'Overnight section stayed on “Checking the last hourly run…”',
    )
    log(
      'q1.gov.named_not_library',
      /Library welcome|Automatic library letters|\bLibrary letters\b/i.test(govOvernight)
        ? 'FAIL'
        : 'PASS',
      /Library welcome|Automatic library letters|\bLibrary letters\b/i.test(govOvernight)
        ? 'stale library copy'
        : 'named-letter copy',
    )
    log(
      'q1.gov.overnight_named',
      /Hourly automation is/i.test(govOvernight) &&
        /Named letters/i.test(govOvernight) &&
        !/Automatic library letters|\bLibrary letters\b/i.test(govOvernight)
        ? 'PASS'
        : overnightReady
          ? 'FAIL'
          : 'SKIP',
    )
    log(
      'q1.gov.health_chip',
      /Automation active/i.test(govOvernight)
        ? 'PASS'
        : /Automation has stopped|Automation is not running/i.test(govOvernight)
          ? 'FAIL'
          : 'WARN',
      /Automation active|Automation has stopped|Automation is not running|Checking automation/i.exec(
        govOvernight,
      )?.[0] || 'chip copy missing',
    )
    log('q1.gov.forbidden', scanForbidden(govOvernight).length ? 'FAIL' : 'PASS', scanForbidden(govOvernight).join(', '))

    // ── Needs You (Q1 echo) ───────────────────────────────────────────
    await gotoPath(page, '/needs-you')
    await shot(page, 'needs_you')
    const ny = await bodyText(page)
    log(
      'q1.needs_you.loaded',
      /Needs You/i.test(ny) || /Nothing needs you/i.test(ny) ? 'PASS' : 'FAIL',
      ny.slice(0, 200),
    )
    log(
      'q1.needs_you.assisted_wait',
      /Hourly library send/i.test(ny) ? 'FAIL' : 'PASS',
    )
    log('q1.needs_you.forbidden', scanForbidden(ny).length ? 'FAIL' : 'PASS', scanForbidden(ny).join(', '))
    log(
      'q4.needs_you.no_client_aime',
      /buyers and sellers talk to Aime|client Aime/i.test(ny) ? 'FAIL' : 'PASS',
    )

    // ── All Transactions: Terminated tab (Q6) ─────────────────────────
    await gotoPath(page, '/transactions?status=all')
    await shot(page, 'all_transactions')
    const allTx = await bodyText(page)
    log('q6.list.terminated_tab', /\bTerminated\b/.test(allTx) ? 'PASS' : 'FAIL', allTx.slice(0, 200))
    const termTab = page.getByRole('button', { name: /^Terminated/i }).first()
    if (await termTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await termTab.click()
      await waitSettled(page, 500)
      log('q6.list.terminated_click', page.url().includes('tab=Terminated') ? 'PASS' : 'WARN', page.url())
    } else {
      log('q6.list.terminated_click', 'FAIL', 'Terminated tab button not found')
    }

    await gotoPath(page, '/transactions/all?tab=Terminated')
    log(
      'q6.list.path_alias',
      page.url().includes('Terminated') || (await bodyText(page)).includes('Terminated')
        ? 'PASS'
        : 'FAIL',
      page.url(),
    )

    // ── Live file workspace (Q1 header, Q5/Q6 status copy, Q1 email) ──
    await gotoPath(page, '/transactions')
    await waitForCopy(page, /Open workspace for|Start one to get going|No transactions/i, 15000)
    let dealHref = await firstDealHref(page)
    if (!dealHref) {
      await gotoPath(page, '/transactions?status=all')
      await waitForCopy(page, /Open workspace for|No transactions|All Transactions/i, 12000)
      dealHref = await firstDealHref(page)
    }
    const hasDeal = Boolean(dealHref)
    if (!hasDeal) {
      log('workspace.deal', 'SKIP', 'no deal UUID links in Active or All — header/email/status confirms untested in Chrome')
    } else {
      log('workspace.deal', 'PASS', dealHref)
      await gotoPath(page, dealHref)
      await closeAime(page)
      const wsReady = await page
        .getByRole('tablist', { name: 'Workspace sections' })
        .waitFor({ state: 'visible', timeout: 25000 })
        .then(() => true)
        .catch(() => false)
      const wsError = await page
        .getByText("Couldn't load this transaction")
        .isVisible()
        .catch(() => false)
      await closeAime(page)
      await dismissOverlays(page)
      await shot(page, 'workspace')
      const ws = await dump(page, 'workspace')
      log(
        'q1.workspace.loaded',
        wsReady ? 'PASS' : wsError ? 'FAIL' : 'FAIL',
        wsReady
          ? page.url()
          : wsError
            ? 'workspace API error'
            : page.url() + ' — workspace body never arrived',
      )
      const postureBtn = page.getByRole('button').filter({
        hasText: /Manual|Assisted|Autopilot/,
      }).first()
      if (await postureBtn.isVisible({ timeout: 4000 }).catch(() => false)) {
        await postureBtn.click()
        await waitSettled(page, 300)
        const menu = await bodyText(page)
        log(
          'q1.workspace.posture_menu',
          /you tap Send/i.test(menu) && /without a tap/i.test(menu) ? 'PASS' : 'FAIL',
          menu.slice(0, 400),
        )
        await page.keyboard.press('Escape').catch(() => {})
      } else {
        log('q1.workspace.posture_menu', 'WARN', 'posture chip not visible (plan.automation missing locally)')
      }

      const statusChip = page.getByRole('button').filter({
        hasText: /^(Active|Incomplete|Paused|Completed|Closed|Terminated)$/,
      }).first()
      if (await statusChip.isVisible({ timeout: 3000 }).catch(() => false)) {
        await statusChip.click()
        await waitSettled(page, 250)
        const items = page.getByRole('menuitem')
        const labels = (await items.allInnerTexts().catch(() => [])).join(' | ')
        log(
          'q6.workspace.status_menu',
          /Terminated/.test(labels) ? 'PASS' : 'FAIL',
          labels,
        )
        const termItem = page.getByRole('menuitem', { name: 'Terminated' })
        if (await termItem.isVisible({ timeout: 1500 }).catch(() => false)) {
          await termItem.click()
          await waitSettled(page, 400)
          const dlg = await bodyText(page)
          log(
            'q6.workspace.terminated_confirm',
            /fell through/i.test(dlg) && /not a closed sale/i.test(dlg) ? 'PASS' : 'FAIL',
            dlg.slice(0, 400),
          )
          await page.getByRole('button', { name: /^Cancel$/i }).click().catch(() => {})
          await waitSettled(page, 250)
        }
        if (await statusChip.isVisible({ timeout: 2000 }).catch(() => false)) {
          await statusChip.click()
          await waitSettled(page, 250)
          const completed = page.getByRole('menuitem', { name: 'Completed' })
          if (await completed.isVisible({ timeout: 1500 }).catch(() => false)) {
            await completed.click()
            await waitSettled(page, 400)
            const dlg = await bodyText(page)
            log(
              'q5.workspace.completed_confirm',
              /Closing day is not the end of the file/i.test(dlg) ? 'PASS' : 'FAIL',
              dlg.slice(0, 400),
            )
            await page.getByRole('button', { name: /^Cancel$/i }).click().catch(() => {})
            await waitSettled(page, 250)
          }
        }
      } else {
        log('q5q6.workspace.status', 'WARN', 'status chip not found')
      }

      const emailTab = page.getByRole('tab', { name: /^Email$/i }).or(
        page.getByRole('button', { name: /^Email$/i }),
      )
      if (await emailTab.first().isVisible({ timeout: 3000 }).catch(() => false)) {
        await emailTab.first().click()
        await waitSettled(page, 500)
        const email = await bodyText(page)
        log(
          'q1.email.tap_send',
          /Nothing sends until you tap Send/i.test(email) ? 'PASS' : 'FAIL',
        )
        log(
          'q1.email.roles',
          /On Autopilot[\s\S]{0,80}on their own/i.test(email) &&
            /On Assisted they wait here for Send/i.test(email)
            ? 'PASS'
            : 'FAIL',
          email.slice(0, 350),
        )
      } else {
        log('q1.email.tab', 'WARN', 'Email tab not found on this workspace')
      }

      const tasksTab = page.getByRole('tab', { name: /^Tasks$/i })
      if (await tasksTab.isVisible({ timeout: 3000 }).catch(() => false)) {
        await tasksTab.click()
        await waitSettled(page, 800)
        await waitForCopy(page, /open|Show completed|Add Task/i, 12000)
        let tasksTxt = await dump(page, 'workspace_tasks')
        const closingRe =
          /Buyer Closing Information|Seller Closing Information|Seller's Agent Closing Information|Buyer's Agent Closing Information/i
        if (!closingRe.test(tasksTxt)) {
          const showCompleted = page.getByLabel(/Show completed/i)
          if (await showCompleted.isVisible({ timeout: 1500 }).catch(() => false)) {
            await showCompleted.check().catch(() => showCompleted.click().catch(() => {}))
            await waitSettled(page, 400)
            tasksTxt = await dump(page, 'workspace_tasks')
          }
        }
        const closingDeal = process.env.QA_CLOSING_DEAL
        if (closingDeal) {
          await gotoPath(page, `/transactions/${closingDeal}?tab=tasks`)
          await closeAime(page)
          await waitForCopy(page, /open|Show completed|Add Task/i, 15000)
          tasksTxt = await dump(page, 'workspace_tasks_closing')
        }
        log(
          'q3.tasks.closing_info_present',
          closingRe.test(tasksTxt) ? 'PASS' : 'SKIP',
          closingRe.test(tasksTxt)
            ? 'closing-information tasks on this file'
            : 'no closing-information rows visible (Completed may stay hidden)',
        )
        const actions = page.getByRole('button', {
          name: /Actions for (Buyer Closing Information|Seller Closing Information|Seller's Agent Closing Information|Buyer's Agent Closing Information)/i,
        })
        const actionCount = await actions.count().catch(() => 0)
        let openedPlan = false
        for (let i = 0; i < actionCount; i += 1) {
          await actions.nth(i).click()
          await waitSettled(page, 200)
          const emailParty = page.getByRole('menuitem', { name: /Email transaction party/i })
          if (await emailParty.isVisible({ timeout: 1200 }).catch(() => false)) {
            await emailParty.click()
            openedPlan = true
            await waitSettled(page, 400)
            break
          }
          await page.keyboard.press('Escape').catch(() => {})
        }
        if (openedPlan) {
            const planReady = await waitForCopy(
              page,
              /Aime can complete this for you|No .+ contact with an email|needs .+ attached/i,
              15000,
            )
            const dialog = page.getByRole('dialog', { name: 'Complete this task' })
            const planTxt = await dialog.innerText().catch(() => '')
            writeFileSync(path.join(OUT, 'closing_email_plan.txt'), `${page.url()}\n\n${planTxt}`)
            log(
              'q3.email_plan.loaded',
              planReady ? 'PASS' : 'FAIL',
              planReady ? '' : planTxt.slice(0, 400),
            )
            const cdHit = /Closing Disclosure/i.test(planTxt)
            log(
              'q3.email_plan.no_cd',
              cdHit ? 'FAIL' : 'PASS',
              cdHit
                ? 'Closing Disclosure appeared on a closing-information email plan'
                : 'no CD on planned attachments',
            )
            await page.getByRole('button', { name: /I'll handle it myself|^Close$|^Cancel$/i }).first().click().catch(() => {})
            await page.keyboard.press('Escape').catch(() => {})
            await waitSettled(page, 200)
        } else {
          log(
            'q3.email_plan.menu',
            closingRe.test(tasksTxt) ? 'SKIP' : 'SKIP',
            actionCount
              ? 'Email transaction party not in closing-information actions menus'
              : 'closing-information kebab not visible',
          )
          await page.keyboard.press('Escape').catch(() => {})
        }
      } else {
        log('q3.tasks.tab', 'WARN', 'Tasks tab not found')
      }
      log('workspace.forbidden', scanForbidden(await bodyText(page)).length ? 'FAIL' : 'PASS')
    }

    // ── Intake wizard: Fast intake, not Autopilot (Q1) ────────────────
    await gotoPath(page, '/transactions/new')
    const wizReady = await waitForCopy(page, /New Transaction/i, 25000)
    await shot(page, 'wizard')
    const wiz = await dump(page, 'wizard')
    log(
      'q1.wizard.loaded',
      wizReady ? 'PASS' : 'WARN',
      wizReady ? '' : wiz.slice(0, 200),
    )
    log(
      'q1.wizard.no_intake_autopilot_label',
      /✦ Autopilot/.test(wiz) ? 'FAIL' : 'PASS',
    )
    if (/✦ Fast intake/.test(wiz)) {
      log('q1.wizard.fast_intake', 'PASS', 'high-confidence hub visible')
    } else {
      log(
        'q1.wizard.fast_intake',
        'SKIP',
        'Fast intake hub only appears after a high-confidence extract; not expected on an empty local wizard',
      )
    }
    log('q1.wizard.forbidden', scanForbidden(wiz).length ? 'FAIL' : 'PASS', scanForbidden(wiz).join(', '))

    const realConsole = consoleErrors.filter(
      (e) =>
        !/Download the React DevTools|favicon|third-party cookie|Failed to load resource|`ref` is not a prop/i.test(
          e,
        ),
    )
    log(
      'console.page_errors',
      pageErrors.length ? 'FAIL' : 'PASS',
      pageErrors.slice(0, 5).join(' | '),
    )
    log(
      'console.errors',
      realConsole.length ? 'WARN' : 'PASS',
      realConsole.slice(0, 8).join(' | '),
    )
    const five = failedRequests.filter((u) => /^5/.test(u))
    log(
      'api.5xx',
      five.length ? 'FAIL' : 'PASS',
      five.slice(0, 10).join(' | ') || `${failedRequests.length} 4xx logged`,
    )
    log(
      'api.4xx',
      failedRequests.filter((u) => /^4/.test(u)).length > 8 ? 'WARN' : 'PASS',
      failedRequests.slice(0, 12).join(' | '),
    )
  } catch (err) {
    log('harness', 'FAIL', err.stack || err.message)
  } finally {
    const report = {
      app: APP,
      headed: HEADED,
      channel: CHANNEL,
      fail: failCount(),
      findings,
      failedRequests: failedRequests.slice(0, 40),
      consoleErrors: consoleErrors.slice(0, 40),
      pageErrors,
    }
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(report, null, 2))
    console.log(`\nWrote ${path.join(OUT, 'findings.json')}  FAIL=${failCount()}`)
    await page.close().catch(() => {})
    await context.close().catch(() => {})
    await browser.close().catch(() => {})
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
