/**
 * Staging Chrome QA for the Jake TME wrap just deployed (Trusted dates,
 * You confirm, Verify deadline, stages, contacts, refuse, LSE offer).
 * One headless Chrome. Never Send mail, never confirm Run AI tasks,
 * never Disconnect, never Change status.
 *
 *   node jake_tme_staging_chrome_qa.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, rmSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_jake_tme_staging')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const CLIENT_EMAIL = process.env.QA_CLIENT_EMAIL || 'ellenore.zynique@minafter.com'
const APP = (process.env.QA_APP || 'https://app.stage.velvetelves.com').replace(/\/$/, '')
const API = (process.env.QA_API || 'https://api.stage.velvetelves.com').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

const DEAL_ACTIVE = 'da681bf7-92e8-45b5-b3d0-8f152e461bca' // 12 Guide Test Way
const DEAL_DUAL = 'f53d0674-8322-4568-9fb9-fae7715d521d' // 700 Test Dual Ave
const DEAL_TERMINATED = 'fb22c770-718b-4207-a891-cc44f771b3c4' // 1912 Charles (already Terminated)

const findings = []
const pageErrors = []
const consoleErrors = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 800) : ''}`)
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
  await page.getByRole('button', { name: /Automation posture for this deal/i }).waitFor({ timeout: 35000 })
}

async function apiLogin(email) {
  const body = new URLSearchParams({ username: email, password: PASSWORD })
  const res = await fetch(`${API}/api/v1/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  const json = await res.json().catch(() => ({}))
  return { status: res.status, json }
}

async function launch(token, refresh) {
  const profile = path.join(OUT, `chrome-profile-${Date.now()}`)
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
    ({ token: t, refresh: r }) => {
      window.localStorage.setItem('velvet_elves_token', t)
      if (r) window.localStorage.setItem('velvet_elves_refresh_token', r)
      window.localStorage.setItem('ve_agent_workspace_v1', 'on')
      window.localStorage.setItem('ve_agent_pane_open', 'open')
    },
    { token, refresh: refresh || '' },
  )
  const page = context.pages()[0] || (await context.newPage())
  page.setDefaultTimeout(20000)
  page.on('pageerror', (err) => pageErrors.push(String(err).slice(0, 400)))
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text().slice(0, 400))
  })
  return { context, page, profile }
}

async function runStaff(page) {
  await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await dismissOverlays(page)
  if (page.url().includes('/login')) {
    log('login.session', 'FAIL', page.url())
    await shot(page, 'login_bounce')
    throw new Error('Seeded session bounced to login')
  }
  log('login.session', 'PASS', page.url())

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
  log('settings.page', 'PASS')

  const dateGroup = page.getByRole('radiogroup', { name: /^Contract dates$/i })
  const datesReady = await dateGroup.waitFor({ timeout: 25000 }).then(() => true).catch(() => false)
  if (!datesReady) {
    await dump(page, 'how_it_runs')
    await shot(page, 'how_it_runs')
    log('settings.trusted_ready', 'FAIL', 'Contract dates radios never painted')
  } else {
    log('settings.trusted_ready', 'PASS')
  }
  await dismissOverlays(page)
  await dateGroup.scrollIntoViewIfNeeded().catch(() => {})
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
  log('settings.save_date_authority', /Save dates/i.test(settingsText) ? 'PASS' : 'FAIL')
  log(
    'settings.always_true',
    /Unclear or conflicting contract dates never go live on their own/i.test(settingsText)
      ? 'PASS'
      : 'FAIL',
  )
  log(
    'settings.named_emails_not_letters',
    /Named emails are drafted — you tap Send/i.test(settingsText) ? 'PASS' : 'FAIL',
  )
  log('settings.no_conductor_name', /\bConductor\b/i.test(settingsText) ? 'FAIL' : 'PASS')
  log(
    'settings.no_obligation_autonomy_words',
    /obligation autonomy/i.test(settingsText) ? 'FAIL' : 'PASS',
  )

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
    `youConfirm=${await youConfirm.count()} trusted=${await trustedDate.count()} assisted=${await assistedDate.count()}`,
  )

  await trustedDate.click()
  const saveDates = page.getByRole('button', { name: /^Save dates$/i })
  const saveEnabled = await saveDates.isEnabled().catch(() => false)
  if (!saveEnabled) {
    log('settings.save_trusted', 'FAIL', 'Save dates stayed disabled after Trusted click')
  } else {
    const putSettings = page.waitForResponse(
      (r) => r.url().includes('/automation/settings') && r.request().method() === 'PUT',
      { timeout: 20000 },
    )
    await saveDates.click()
    const put = await putSettings.catch(() => null)
    log(
      'settings.save_trusted',
      put && put.ok() ? 'PASS' : 'FAIL',
      put ? `http ${put.status()}` : 'no PUT /automation/settings',
    )
    const toastOk = await page
      .getByText(/Clear contract dates may become official without a second click/i)
      .waitFor({ timeout: 8000 })
      .then(() => true)
      .catch(() => false)
    log('settings.trusted_toast', toastOk ? 'PASS' : 'WARN')
  }
  await youConfirm.click()
  if (await saveDates.isEnabled().catch(() => false)) {
    const putBack = page.waitForResponse(
      (r) => r.url().includes('/automation/settings') && r.request().method() === 'PUT',
      { timeout: 20000 },
    )
    await saveDates.click()
    const put = await putBack.catch(() => null)
    log(
      'settings.restore_you_confirm',
      put && put.ok() ? 'PASS' : 'WARN',
      put ? `http ${put.status()}` : 'no restore PUT',
    )
  } else {
    log('settings.restore_you_confirm', 'WARN', 'Save dates not enabled after You confirm click')
  }

  await page.goto(`${APP}/transactions/new`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await dismissOverlays(page)
  await page.getByRole('radiogroup', { name: /representing/i }).waitFor({ timeout: 25000 })
  await page.getByRole('radiogroup', { name: /representing/i }).getByText('Buyer', { exact: true }).click()
  const skip = page.getByRole('button', { name: /Skip upload — enter details manually/i })
  log('wizard.skip_upload', (await skip.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  await shot(page, 'wizard_skip')

  await page.goto(`${APP}/transactions/${DEAL_ACTIVE}`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await dismissOverlays(page)
  await waitWorkspace(page)
  const ws = await dump(page, 'workspace_guide')
  await shot(page, 'workspace_guide')
  log(
    'workspace.stages',
    /Earnest Money|Inspection|Financing/i.test(ws) ? 'PASS' : 'FAIL',
    ws.slice(0, 500),
  )
  log(
    'workspace.next_line',
    /Next:\s/i.test(ws) ? 'PASS' : 'FAIL',
  )
  log('workspace.no_conductor', /\bConductor\b/i.test(ws) ? 'FAIL' : 'PASS')
  log(
    'workspace.offer_lse_absent_while_active',
    /Offer Listing Success/i.test(ws) ? 'FAIL' : 'PASS',
  )
  log(
    'workspace.provenance_chips',
    /\b(Confirmed|Reported|Conflict)\b/.test(ws) ? 'PASS' : 'SKIP',
    'existing Guide Test Way dates have no typed facts',
  )

  const postureBtn = page.getByRole('button', { name: /Automation posture for this deal/i })
  await postureBtn.click()
  await page.waitForTimeout(400)
  const menu = await bodyText(page)
  writeFileSync(path.join(OUT, 'posture_menu.txt'), menu)
  await shot(page, 'posture_menu')
  log(
    'deal.menu.emails_not_letters',
    /Named emails are drafted — you tap Send/i.test(menu) ? 'PASS' : 'FAIL',
  )
  log(
    'deal.menu.trusted_separate',
    /On for this deal/i.test(menu) && /This is not email send/i.test(menu) ? 'PASS' : 'FAIL',
  )
  log(
    'deal.menu.off_for_this_deal',
    /Off for this deal/i.test(menu) ? 'PASS' : 'FAIL',
  )
  log(
    'deal.menu.autopilot_caption',
    /Authorized emails send without a tap/i.test(menu) ? 'PASS' : 'FAIL',
  )
  log(
    'deal.menu.always_true',
    /Unclear or conflicting contract dates never go live on their own/i.test(menu)
      ? 'PASS'
      : 'FAIL',
  )
  const pinWait = page.waitForResponse(
    (r) =>
      r.url().includes(`/transactions/${DEAL_ACTIVE}/automation`) && r.request().method() === 'PUT',
    { timeout: 20000 },
  )
  await page.getByText('On for this deal', { exact: true }).click()
  const pinPut = await pinWait.catch(() => null)
  log(
    'deal.pin_trusted',
    pinPut && pinPut.ok() ? 'PASS' : 'FAIL',
    pinPut ? `http ${pinPut.status()}` : 'no PUT deal automation',
  )
  await shot(page, 'trusted_toast')
  const pinToast = await page
    .getByText(/Trusted dates are on for this deal/i)
    .waitFor({ timeout: 8000 })
    .then(() => true)
    .catch(() => false)
  log('deal.pin_toast', pinToast ? 'PASS' : 'WARN')

  await postureBtn.click().catch(() => {})
  await page.waitForTimeout(400)
  const inheritDates = page.getByRole('menuitem', { name: /Follow the workspace/i })
  if (await inheritDates.waitFor({ timeout: 8000 }).then(() => true).catch(() => false)) {
    const inheritWait = page.waitForResponse(
      (r) =>
        r.url().includes(`/transactions/${DEAL_ACTIVE}/automation`) && r.request().method() === 'PUT',
      { timeout: 20000 },
    )
    await inheritDates.click()
    const inheritPut = await inheritWait.catch(() => null)
    log(
      'deal.inherit_copy',
      inheritPut && inheritPut.ok() ? 'PASS' : 'WARN',
      inheritPut ? `http ${inheritPut.status()}` : 'no inherit PUT',
    )
  } else {
    await page.keyboard.press('Escape').catch(() => {})
    log('deal.inherit_copy', 'WARN', 'Follow the workspace not shown')
  }

  await page.goto(`${APP}/transactions/${DEAL_DUAL}?tab=contacts`, {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  })
  await waitWorkspace(page)
  await dismissOverlays(page)
  await page.getByText('Dual Buyer', { exact: true }).waitFor({ timeout: 20000 })
  const contacts = await dump(page, 'contacts_dual')
  await shot(page, 'contacts_dual')
  log(
    'contacts.dual_parties',
    /Dual Buyer/i.test(contacts) && /Dual Seller/i.test(contacts) ? 'PASS' : 'FAIL',
  )
  const buyerToggle = page.getByRole('button', { name: /details for Dual Buyer/i })
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
        { timeout: 15000 },
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
        put && put.ok() && before !== after ? 'PASS' : 'FAIL',
        `before=${before} after=${after} put=${put ? put.status() : 'none'}`,
      )
      if (after !== before) {
        await box.click()
        await page.waitForTimeout(500)
      }
    }
  } else {
    log('contacts.buyer_flags', 'FAIL', 'Dual Buyer row missing expand control')
  }

  await page.goto(`${APP}/transactions/${DEAL_DUAL}?tab=tasks`, {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  })
  await waitWorkspace(page)
  await dismissOverlays(page)
  const tasksText = await dump(page, 'tasks_dual')
  await shot(page, 'tasks_dual')
  const hasBuyerTitle = /Deliver Title/i.test(tasksText)
  log(
    'dual.deliver_title_visible',
    hasBuyerTitle ? 'PASS' : 'WARN',
    'Chrome Tasks tab; API already has 300 Buyer + 310 Seller',
  )

  const ask = page.getByRole('button', { name: /^Ask AI$/i }).or(page.getByRole('button', { name: /Ask AI about this deal/i }))
  if (await ask.first().isVisible().catch(() => false)) {
    await ask.first().click()
  }
  const composer = page.getByLabel('Message Aime').last()
  const composerReady = await composer.waitFor({ timeout: 15000 }).then(() => true).catch(() => false)
  if (!composerReady) {
    log('aime.refuse', 'FAIL', 'composer not found')
    await shot(page, 'aime_missing')
  } else {
    await composer.fill('tell them they can terminate')
    await page.getByRole('button', { name: /^Send$/i }).click()
    const reply = await page
      .getByText(/I cannot give legal advice or tell a party they may terminate/i)
      .waitFor({ timeout: 35000 })
      .then(() => true)
      .catch(() => false)
    const pane = await bodyText(page)
    log('aime.refuse_legal', reply ? 'PASS' : 'FAIL', pane.slice(-900))
    log('aime.not_disagree', /I disagree/i.test(pane) ? 'FAIL' : 'PASS')
    log('aime.no_conductor_name', /\bConductor\b/i.test(pane) ? 'FAIL' : 'PASS')
    await shot(page, 'aime_refuse')
    writeFileSync(path.join(OUT, 'aime_refuse.txt'), pane)
  }

  await page.goto(`${APP}/transactions/${DEAL_TERMINATED}`, {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  })
  await dismissOverlays(page)
  await waitWorkspace(page)
  const termText = await dump(page, 'terminated_charles')
  await shot(page, 'terminated_charles')
  const lseBtn = page.getByRole('button', { name: /Offer Listing Success/i })
  const termVisible = await lseBtn.waitFor({ timeout: 15000 }).then(() => true).catch(() => false)
  const disabled = termVisible ? await lseBtn.isDisabled().catch(() => false) : false
  log(
    'terminated.lse_disabled',
    termVisible && disabled ? 'PASS' : 'FAIL',
    `visible=${termVisible} disabled=${disabled}`,
  )
  log(
    'terminated.no_listing_start',
    /Listing Success is not in this product yet/i.test((await lseBtn.getAttribute('title').catch(() => '')) || '') ||
      /will not start listing work from a failed file/i.test(termText)
      ? 'PASS'
      : 'WARN',
  )
  log(
    'terminated.next_still_ranked',
    /Next:\s/i.test(termText) ? 'WARN' : 'PASS',
    'Terminated files still ranking a leftover obligation as Next is unexpected',
  )

  await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await dismissOverlays(page)
  await page.getByRole('heading', { name: /Needs You/i }).waitFor({ timeout: 25000 }).catch(() => {})
  const search = page.getByRole('searchbox').or(page.getByPlaceholder(/search/i)).first()
  if (await search.isVisible().catch(() => false)) {
    await search.fill('Verify deadline')
    await page.waitForTimeout(800)
  }
  const ny = await dump(page, 'needs_you')
  await shot(page, 'needs_you')
  const hasVerify = /Verify deadline/i.test(ny)
  log(
    'needs_you.verify_deadline_card',
    hasVerify ? 'PASS' : 'SKIP',
    hasVerify ? 'card present' : 'no pending date proposal on this tenant',
  )
  log('needs_you.no_conductor', /\bConductor\b/i.test(ny) ? 'FAIL' : 'PASS')
}

async function runClient() {
  const session = await apiLogin(CLIENT_EMAIL)
  if (session.status !== 200 || !session.json.access_token) {
    log('client.login.api', 'FAIL', `status=${session.status}`)
    return
  }
  log(
    'client.login.api',
    'PASS',
    JSON.stringify({
      email: session.json.user?.email,
      role: session.json.user?.role,
      mfa: session.json.mfa_required,
    }),
  )
  const { context, page, profile } = await launch(session.json.access_token, session.json.refresh_token)
  try {
    await page.goto(`${APP}/client/home`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await dismissOverlays(page)
    if (page.url().includes('/login')) {
      log('client.session', 'FAIL', page.url())
      await shot(page, 'client_login_bounce')
      return
    }
    log('client.session', 'PASS', page.url())
    const home = await dump(page, 'client_home')
    await shot(page, 'client_home')
    log(
      'client.no_ask_ai',
      /Ask AI/i.test(home) || /Message Aime/i.test(home) ? 'FAIL' : 'PASS',
    )
    log('client.no_needs_you', /Needs You/i.test(home) ? 'FAIL' : 'PASS')
    log(
      'client.ask_team_or_status',
      /Ask your team|Next steps|Home/i.test(home) ? 'PASS' : 'WARN',
    )
  } catch (err) {
    log('client.uncaught', 'FAIL', err.message || String(err))
    await shot(page, 'client_uncaught').catch(() => {})
  } finally {
    await context.close().catch(() => {})
    try {
      rmSync(profile, { recursive: true, force: true })
    } catch {
      /* temp */
    }
  }
}

async function run() {
  const session = await apiLogin(EMAIL)
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

  const { context, page, profile } = await launch(session.json.access_token, session.json.refresh_token)
  try {
    await runStaff(page)
  } catch (err) {
    log('run.uncaught', 'FAIL', err.message || String(err))
    await shot(page, 'uncaught').catch(() => {})
    await dump(page, 'uncaught').catch(() => {})
  } finally {
    await context.close().catch(() => {})
    try {
      rmSync(profile, { recursive: true, force: true })
    } catch {
      /* temp */
    }
  }

  await runClient()

  const failed = findings.filter((f) => f.result === 'FAIL').length
  const warned = findings.filter((f) => f.result === 'WARN').length
  const skipped = findings.filter((f) => f.result === 'SKIP').length
  writeFileSync(
    path.join(OUT, 'findings.json'),
    JSON.stringify({ findings, pageErrors, consoleErrors: consoleErrors.slice(0, 40) }, null, 2),
  )
  console.log(`FAILED ${failed} WARN ${warned} SKIP ${skipped} TOTAL ${findings.length}`)
  process.exit(failed ? 1 : 0)
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
