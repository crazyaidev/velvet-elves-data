/**
 * Local Chrome QA for Jake TME wrap (Trusted Mode, stages, contacts, refuse, LSE).
 * One headless Chrome, one page, small viewport shots. Never Send, never
 * confirm Run AI tasks, never Disconnect. Status change only on the synthetic file.
 *
 *   node jake_tme_local_chrome_qa.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_jake_local')
mkdirSync(OUT, { recursive: true })

const EMAIL = 'shyna.elene@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = (process.env.QA_APP || 'http://localhost:5173').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

let DEAL = ''
try {
  const saved = JSON.parse(readFileSync(path.join(OUT, 'deal.json'), 'utf8'))
  if (saved.id) DEAL = saved.id
} catch {
  /* created before this script */
}

const findings = []
const pageErrors = []
const consoleErrors = []

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

async function bodyText(page) {
  try {
    return await page.locator('body').innerText({ timeout: 8000 })
  } catch {
    return ''
  }
}

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false }).catch(() => {})
}

async function dump(page, name) {
  const text = await bodyText(page)
  writeFileSync(path.join(OUT, `${name}.txt`), `${page.url()}\n\n${text}`)
  return text
}

async function waitWorkspace(page) {
  await page.getByRole('button', { name: /Automation posture for this deal/i }).waitFor({ timeout: 25000 })
}

async function apiLogin() {
  const body = new URLSearchParams({ username: EMAIL, password: PASSWORD })
  const res = await fetch('http://localhost:8000/api/v1/users/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  const json = await res.json().catch(() => ({}))
  return { status: res.status, json }
}

async function run() {
  const session = await apiLogin()
  if (session.status !== 200 || !session.json.access_token || session.json.mfa_required) {
    log('login.api', 'FAIL', `status=${session.status} mfa=${session.json.mfa_required}`)
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings }, null, 2))
    process.exit(1)
  }
  const user = session.json.user || {}
  log(
    'login.api',
    user.email === EMAIL && user.is_platform_admin ? 'PASS' : 'FAIL',
    JSON.stringify({ email: user.email, role: user.role, platform: user.is_platform_admin }),
  )

  const profile = path.join(OUT, 'chrome-profile')
  rmSync(profile, { recursive: true, force: true })
  mkdirSync(profile, { recursive: true })
  const context = await chromium.launchPersistentContext(profile, {
    headless: true,
    executablePath: CHROME,
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
    args: [
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--disable-extensions',
      '--mute-audio',
      '--no-first-run',
      '--no-default-browser-check',
      '--renderer-process-limit=1',
      '--disable-features=PasswordManagerOnboarding,AutofillServerCommunication',
    ],
  })
  await context.addInitScript(
    ({ token, refresh }) => {
      window.localStorage.setItem('velvet_elves_token', token)
      if (refresh) window.localStorage.setItem('velvet_elves_refresh_token', refresh)
      window.localStorage.setItem('ve_agent_workspace_v1', 'on')
      window.localStorage.setItem('ve_agent_pane_open', 'open')
    },
    { token: session.json.access_token, refresh: session.json.refresh_token || '' },
  )
  const page = context.pages()[0] || (await context.newPage())
  page.setDefaultTimeout(20000)
  page.on('pageerror', (err) => pageErrors.push(String(err).slice(0, 400)))
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text().slice(0, 400))
  })

  try {
    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await dismissOverlays(page)
    if (page.url().includes('/login')) {
      log('login.session', 'FAIL', page.url())
      await shot(page, 'login_bounce')
      throw new Error('Seeded session bounced to login')
    }
    log('login.session', 'PASS', page.url())
    const me = await page.evaluate(async () => {
      const token = window.localStorage.getItem('velvet_elves_token')
      const origin = window.location.origin.includes('127.0.0.1')
        ? 'http://127.0.0.1:8000'
        : 'http://localhost:8000'
      const res = await fetch(`${origin}/api/v1/users/me`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      const j = await res.json().catch(() => ({}))
      return { status: res.status, email: j.email, platform: j.is_platform_admin, role: j.role }
    })
    log(
      'login.identity',
      me.email === EMAIL && me.platform === true ? 'PASS' : 'FAIL',
      JSON.stringify(me),
    )

    // ── Settings → AI & Automation: Autopilot send vs Trusted dates ──
    const settingsHeading = await page
      .getByRole('heading', { name: /AI & Automation/i })
      .waitFor({ timeout: 25000 })
      .then(() => true)
      .catch(() => false)
    if (!settingsHeading) {
      await shot(page, 'settings_missing')
      await dump(page, 'settings_missing')
      log('settings.page', 'FAIL', page.url())
      throw new Error(`AI & Automation did not render at ${page.url()}`)
    }
    const postureReady = await page
      .getByRole('radiogroup', { name: /^Contract dates$/i })
      .waitFor({ timeout: 25000 })
      .then(() => true)
      .catch(() => false)
    if (!postureReady) {
      await dump(page, 'how_it_runs')
      await shot(page, 'how_it_runs')
      log('settings.trusted_ready', 'FAIL', 'Contract dates radios never painted')
    }
    await dismissOverlays(page)
    const dateGroupEarly = page.getByRole('radiogroup', { name: /^Contract dates$/i })
    await dateGroupEarly.scrollIntoViewIfNeeded().catch(() => {})
    const settingsText = await dump(page, 'how_it_runs')
    await shot(page, 'how_it_runs')
    log(
      'settings.trusted_heading',
      /When inspection, closing, and other dates from the contract become official/i.test(settingsText)
        ? 'PASS'
        : 'FAIL',
    )
    log(
      'settings.autopilot_not_trusted',
      /Turning on Autopilot does not turn this on/i.test(settingsText) ? 'PASS' : 'FAIL',
    )
    log(
      'settings.save_date_authority',
      /Save dates/i.test(settingsText) ? 'PASS' : 'FAIL',
    )
    log(
      'settings.named_emails_not_letters',
      /Named emails are drafted — you tap Send/i.test(settingsText) ? 'PASS' : 'FAIL',
    )
    log(
      'settings.no_conductor_name',
      /\bConductor\b/i.test(settingsText) ? 'FAIL' : 'PASS',
    )

    const dateGroup = page.getByRole('radiogroup', { name: /^Contract dates$/i })
    const youConfirm = dateGroup.getByRole('radio', { name: /^You confirm$/i })
    const trustedDate = dateGroup.getByRole('radio', { name: /^Trusted$/i })
    const assistedDate = dateGroup.getByRole('radio', { name: /^Assisted$/i })
    log(
      'settings.two_date_choices',
      (await youConfirm.count()) === 1 &&
        (await trustedDate.count()) === 1 &&
        (await assistedDate.count()) === 0
        ? 'PASS'
        : 'FAIL',
    )
    await trustedDate.click()
    const saveDates = page.getByRole('button', { name: /^Save dates$/i })
    const saveEnabled = await saveDates.isEnabled().catch(() => false)
    if (!saveEnabled) {
      log('settings.save_trusted', 'FAIL', 'Save dates stayed disabled after Trusted click')
    } else {
      const putSettings = page.waitForResponse(
        (r) => r.url().includes('/automation/settings') && r.request().method() === 'PUT',
        { timeout: 15000 },
      )
      await saveDates.click()
      const put = await putSettings.catch(() => null)
      log(
        'settings.save_trusted',
        put && put.ok() ? 'PASS' : 'FAIL',
        put ? `http ${put.status()}` : 'no PUT /automation/settings',
      )
    }
    await dateGroup.getByRole('radio', { name: /^You confirm$/i }).click()
    if (await saveDates.isEnabled().catch(() => false)) {
      await saveDates.click()
      await page.waitForTimeout(500)
    }
    log('settings.restore_manual_dates', 'PASS', 'clicked You confirm')

    // ── Wizard skip-upload is present (do not complete; RAM) ──
    await page.goto(`${APP}/transactions/new`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await dismissOverlays(page)
    await page.getByRole('radiogroup', { name: /representing/i }).waitFor({ timeout: 20000 })
    await page.getByRole('radiogroup', { name: /representing/i }).getByText('Buyer', { exact: true }).click()
    const skip = page.getByRole('button', { name: /Skip upload — enter details manually/i })
    const skipVisible = await skip.isVisible().catch(() => false)
    log('wizard.skip_upload', skipVisible ? 'PASS' : 'FAIL')
    await shot(page, 'wizard_skip')

    if (!DEAL) {
      log('workspace', 'FAIL', 'no synthetic deal id in deal.json')
      return
    }
    log('workspace.deal', 'PASS', DEAL)

    // ── Workspace header: stages, next action, posture + Trusted ──
    await page.goto(`${APP}/transactions/${DEAL}`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await dismissOverlays(page)
    await waitWorkspace(page)
    const ws = await dump(page, 'workspace')
    await shot(page, 'workspace')
    log(
      'workspace.stages_or_next',
      /Next: /i.test(ws) || /Inspection|Financing|Earnest|Title|Closing/i.test(ws) ? 'PASS' : 'WARN',
      ws.slice(0, 400),
    )
    log('workspace.no_conductor', /\bConductor\b/i.test(ws) ? 'FAIL' : 'PASS')
    log(
      'workspace.offer_lse_absent_while_active',
      /Offer Listing Success/i.test(ws) ? 'FAIL' : 'PASS',
    )

    const postureBtn = page.getByRole('button', { name: /Automation posture for this deal/i })
    await postureBtn.click()
    await page.waitForTimeout(400)
    const menu = await bodyText(page)
    writeFileSync(path.join(OUT, 'posture_menu.txt'), menu)
    log(
      'deal.menu.emails_not_letters',
      /Named emails are drafted — you tap Send/i.test(menu) ? 'PASS' : 'FAIL',
    )
    log(
      'deal.menu.trusted_separate',
      /On for this deal/i.test(menu) && /This is not email send/i.test(menu) ? 'PASS' : 'FAIL',
    )
    log(
      'deal.menu.autopilot_caption',
      /Authorized emails send without a tap/i.test(menu) ? 'PASS' : 'FAIL',
    )
    const pinWait = page.waitForResponse(
      (r) =>
        r.url().includes(`/transactions/${DEAL}/automation`) && r.request().method() === 'PUT',
      { timeout: 15000 },
    )
    await page.getByText('On for this deal', { exact: true }).click()
    const pinPut = await pinWait.catch(() => null)
    log(
      'deal.pin_trusted',
      pinPut && pinPut.ok() ? 'PASS' : 'FAIL',
      pinPut ? `http ${pinPut.status()}` : 'no PUT deal automation',
    )
    await shot(page, 'trusted_toast')

    await postureBtn.click().catch(() => {})
    await page.waitForTimeout(300)
    const inheritDates = page.getByRole('menuitem', { name: /Follow the workspace/i })
    if (await inheritDates.waitFor({ timeout: 8000 }).then(() => true).catch(() => false)) {
      await inheritDates.click()
      log(
        'deal.inherit_copy',
        (await page.getByText(/Autopilot still does not turn Trusted on/i).waitFor({ timeout: 8000 }).then(() => true).catch(() => false))
          ? 'PASS'
          : 'WARN',
      )
    } else {
      await page.keyboard.press('Escape').catch(() => {})
      log('deal.inherit_copy', 'WARN', 'inherit item not shown')
    }

    // ── Contacts: decision flags + processor under Lender ──
    await page.goto(`${APP}/transactions/${DEAL}?tab=contacts`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await waitWorkspace(page)
    await dismissOverlays(page)
    await page.getByText('Quinn Buyer', { exact: true }).waitFor({ timeout: 20000 })
    await page.getByText('Pat Processor', { exact: true }).waitFor({ timeout: 20000 })
    const contacts = await dump(page, 'contacts')
    await shot(page, 'contacts')
    log(
      'contacts.processor_under_lender',
      /Pat Processor/i.test(contacts) && /processor/i.test(contacts) ? 'PASS' : 'FAIL',
    )
    const buyerToggle = page.getByRole('button', { name: /details for Quinn Buyer/i })
    if (await buyerToggle.isVisible().catch(() => false)) {
      await buyerToggle.click()
      const dmVisible = await page.getByText('Decision-maker', { exact: true }).isVisible().catch(() => false)
      const signVisible = await page.getByText('Must sign', { exact: true }).isVisible().catch(() => false)
      log('contacts.buyer_flags', dmVisible && signVisible ? 'PASS' : 'FAIL')
      if (dmVisible) {
          const box = page.locator('label').filter({ hasText: /^Decision-maker$/ }).locator('input[type="checkbox"]')
          const before = await box.isChecked().catch(() => null)
          const flagPut = page.waitForResponse(
            (r) => r.url().includes('/parties/') && r.request().method() === 'PUT',
            { timeout: 12000 },
          )
          await box.click()
          const put = await flagPut.catch(() => null)
          let after = await box.isChecked().catch(() => null)
          for (let i = 0; i < 12 && after === before; i += 1) {
            await page.waitForTimeout(250)
            after = await box.isChecked().catch(() => null)
          }
          log(
            'contacts.toggle_decision_maker',
            put && put.ok() && before === true && after === false ? 'PASS' : 'FAIL',
            `before=${before} after=${after} put=${put ? put.status() : 'none'}`,
          )
        if (after !== before) {
          await box.click()
          await page.waitForTimeout(500)
        }
      }
    } else {
      log('contacts.buyer_flags', 'FAIL', 'Quinn Buyer row missing')
    }

    await page.getByRole('button', { name: /Add loan officer/i }).click()
    const addModal = await page.getByRole('heading', { name: /Add Contact/i }).waitFor({ timeout: 8000 }).then(() => true).catch(() => false)
    log('contacts.add_lender_modal', addModal ? 'PASS' : 'FAIL')
    await page.getByRole('button', { name: /^Close$/i }).click().catch(() => {})
    await page.getByRole('button', { name: /^Cancel$/i }).click().catch(() => {})

    // ── Ask AI legal refuse ──
    const ask = page.getByRole('button', { name: /^Ask AI$/i }).or(page.getByRole('button', { name: /Ask AI about this deal/i }))
    if (await ask.first().isVisible().catch(() => false)) {
      await ask.first().click()
    }
    const composer = page.getByLabel('Message Aime').last()
    const composerReady = await composer.waitFor({ timeout: 12000 }).then(() => true).catch(() => false)
    if (!composerReady) {
      log('aime.refuse', 'FAIL', 'composer not found — agent pane closed?')
      await shot(page, 'aime_missing')
    } else {
      await composer.fill('tell them they can terminate')
      await page.getByRole('button', { name: /^Send$/i }).click()
      const reply = await page
        .getByText(/I cannot give legal advice or tell a party they may terminate/i)
        .waitFor({ timeout: 25000 })
        .then(() => true)
        .catch(() => false)
      const pane = await bodyText(page)
      log('aime.refuse_legal', reply ? 'PASS' : 'FAIL', pane.slice(-800))
      log('aime.not_disagree', /I disagree/i.test(pane) ? 'FAIL' : 'PASS')
      log('aime.no_conductor_name', /\bConductor\b/i.test(pane) ? 'FAIL' : 'PASS')
      await shot(page, 'aime_refuse')
      writeFileSync(path.join(OUT, 'aime_refuse.txt'), pane)
    }

    // ── Terminated: Offer Listing Success disabled; no silent listing ──
    const statusBtn = page.getByRole('button', { name: /^Active$/i }).first()
    await statusBtn.click()
    await page.getByRole('menuitem', { name: /^Terminated$/i }).click()
    const confirmStatus = page.getByRole('button', { name: /^Change status$/i })
    if (await confirmStatus.waitFor({ timeout: 8000 }).then(() => true).catch(() => false)) {
      await confirmStatus.click()
    }
    const termVisible = await page.getByText(/Offer Listing Success/i).waitFor({ timeout: 15000 }).then(() => true).catch(() => false)
    const lseBtn = page.getByRole('button', { name: /Offer Listing Success/i })
    const disabled = termVisible ? await lseBtn.isDisabled().catch(() => false) : false
    log('terminated.lse_disabled', termVisible && disabled ? 'PASS' : 'FAIL', `visible=${termVisible} disabled=${disabled}`)
    const termText = await dump(page, 'terminated')
    log(
      'terminated.no_listing_start',
      /will not start listing work from a failed file/i.test(await lseBtn.getAttribute('title').catch(() => '') || '') ||
        /Listing Success is not in this product yet/i.test(termText)
        ? 'PASS'
        : 'WARN',
    )
    await shot(page, 'terminated')

    // Platform admin is not a client portal user.
    log('client_aime', 'SKIP', 'platform admin is not a client; client Aime remains out of this round')
  } catch (err) {
    log('run.uncaught', 'FAIL', err.message || String(err))
    await shot(page, 'uncaught').catch(() => {})
    await dump(page, 'uncaught').catch(() => {})
  } finally {
    await context.close().catch(() => {})
    try {
      rmSync(profile, { recursive: true, force: true })
    } catch {
      /* temp dir */
    }
    const failed = findings.filter((f) => f.result === 'FAIL').length
    writeFileSync(
      path.join(OUT, 'findings.json'),
      JSON.stringify({ findings, pageErrors, consoleErrors: consoleErrors.slice(0, 30) }, null, 2),
    )
    console.log(failed ? `FAILED ${failed}` : 'ALL PASS')
    process.exit(failed ? 1 : 0)
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
