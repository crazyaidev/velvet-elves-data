/**
 * Staging pass for Audri Features 8–13 after deploy.
 * Clicks through the workspace. Does not Send, Generate, pin posture, or Change status.
 *
 *   $env:QA_APP='https://app.stage.velvetelves.com'
 *   $env:QA_EMAIL='crazyaidev20500519@gmail.com'
 *   $env:QA_PASSWORD='...'
 *   node feature8_13_staging_verify.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_feature8_13_staging')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const APP = (process.env.QA_APP || 'https://app.stage.velvetelves.com').replace(/\/$/, '')
const DEAL = process.env.QA_DEAL || 'bf1b3bbf-32cd-4215-801e-82eede4c52dd'
const CONTACT = process.env.QA_CONTACT || 'Devon Wallace'
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

const MANUAL =
  'AI suggests. You click to apply anything. Named emails wait until you switch this deal off Manual.'
const ASSISTED = 'Routine work runs. Named emails are drafted — you tap Send.'
const AUTOPILOT = 'Authorized emails send without a tap when confidence is high enough.'
const OLD_MANUAL = 'You apply AI proposals'
const REGISTER = {
  manual: 'AI suggests. You click to apply anything.',
  assisted: 'Routine work runs. Named emails are drafted — you tap Send.',
  autopilot: 'Authorized emails send when confidence is high enough. No tap.',
}

const findings = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 5000) })
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

async function menuText(page) {
  const loc = page.locator('[role="menu"], [data-radix-menu-content]').first()
  if (await loc.isVisible().catch(() => false)) return loc.innerText()
  return page.locator('body').innerText()
}

async function closeTaskDialog(page) {
  const dlg = page.getByRole('dialog', { name: 'Complete this task' })
  if (await dlg.isVisible().catch(() => false)) {
    await dlg.getByRole('button', { name: 'Close' }).click({ force: true, timeout: 3000 }).catch(() => {})
    await page.keyboard.press('Escape').catch(() => {})
    await page.waitForTimeout(400)
  }
}

async function run() {
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
    // Feature 7 (public) — Letters → Emails on register cards
    await page.goto(`${APP}/register`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    const legend = page.getByText('How should Aime start?', { exact: true })
    const hasRegister = await legend.waitFor({ state: 'visible', timeout: 20000 }).then(() => true).catch(() => false)
    if (hasRegister) {
      await legend.scrollIntoViewIfNeeded()
      const fieldset = page.locator('fieldset').filter({ hasText: 'How should Aime start?' }).first()
      const text = ((await fieldset.innerText().catch(() => '')) || '').replace(/\s+/g, ' ')
      await dump('f7_register', text)
      await shot(page, 'f7_register')
      const missing = Object.values(REGISTER).filter((line) => !text.includes(line))
      const letters = /named letters|authorized letters|library letters/i.test(text)
      log(
        'f7-register-emails',
        missing.length || letters ? 'FAIL' : 'PASS',
        JSON.stringify({ missing, letters }),
      )
    } else {
      log('f7-register-emails', 'FAIL', 'Register cards not on /register')
      await shot(page, 'f7_register')
    }

    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.locator('#login-email').waitFor({ state: 'visible', timeout: 25000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    const mfa = await page
      .getByLabel('Two-step verification form')
      .waitFor({ timeout: 5000 })
      .then(() => true)
      .catch(() => false)
    if (mfa) {
      log('login', 'FAIL', 'MFA form — cannot continue without TOTP')
      await shot(page, 'mfa')
      return
    }
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 40000 })
    await dismissOverlays(page)
    log('login', 'PASS', page.url())

    await page.goto(`${APP}/transactions/${DEAL}`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.getByRole('heading', { level: 1 }).waitFor({ state: 'visible', timeout: 30000 })
    await dismissOverlays(page)
    const tabNames = await page
      .getByRole('tablist', { name: 'Workspace sections' })
      .getByRole('tab')
      .allInnerTexts()
      .catch(() => [])
    log('open-deal', 'PASS', `${page.url()} tabs=${JSON.stringify(tabNames)}`)

    // ── Feature 8: read captions only; do not pin ──────────────────────────
    const posture = page.getByRole('button', { name: /Automation posture for this deal/i })
    await posture.click()
    const f8 = await menuText(page)
    await dump('f8_menu', f8)
    await shot(page, 'f8_menu')
    const missingCaptions = [MANUAL, ASSISTED, AUTOPILOT].filter((n) => !f8.includes(n))
    const bad = [OLD_MANUAL, 'you manually send', 'Named letters', 'Authorized letters'].filter((n) =>
      f8.toLowerCase().includes(n.toLowerCase()),
    )
    const inheritExplains = /Changing the workspace setting will apply here/i.test(f8)
    log(
      'f8-captions',
      missingCaptions.length || bad.length ? 'FAIL' : 'PASS',
      JSON.stringify({ missingCaptions, bad, inheritExplains }),
    )
    if (inheritExplains) {
      log('f8-settings-copy', 'PASS', 'Use workspace default explains How it runs override')
    } else if (/Use workspace default/i.test(f8)) {
      log('f8-settings-copy', 'FAIL', f8.slice(0, 800))
    } else {
      log(
        'f8-settings-copy',
        'SKIP',
        'File is on the workspace default — inherit line only shows when pinned',
      )
    }
    await page.keyboard.press('Escape')
    await page.waitForTimeout(300)

    // ── Feature 9 ──────────────────────────────────────────────────────────
    await page.goto(`${APP}/transactions/${DEAL}?tab=contacts`, {
      waitUntil: 'domcontentloaded',
      timeout: 60000,
    })
    await dismissOverlays(page)
    await page.getByRole('heading', { name: 'Contacts' }).waitFor({ timeout: 20000 })
    const person = page.getByText(CONTACT, { exact: true }).first()
    const hasPerson = await person
      .waitFor({ state: 'visible', timeout: 20000 })
      .then(() => true)
      .catch(() => false)
    const contactsRoot = page.locator('section[aria-label="Contacts"]')
    const beforeExpand = await contactsRoot.innerText().catch(() => '')
    await dump('f9_collapsed', beforeExpand)
    await shot(page, 'f9_collapsed')

    if (!hasPerson) {
      log('f9-expand', 'FAIL', `${CONTACT} not on Contacts tab`)
    } else {
      const emailOnCard = /devon\.wallace@minafter\.com/i.test(beforeExpand)
      const expandBtn = page.getByRole('button', { name: new RegExp(`Show details for ${CONTACT}`, 'i') })
      await expandBtn.click()
      await page.waitForTimeout(400)
      const composeOpenAfterCard = await page.getByRole('dialog').isVisible().catch(() => false)
      const afterExpand = await contactsRoot.innerText()
      await dump('f9_expanded', afterExpand)
      await shot(page, 'f9_expanded')
      const emailVisible = /devon\.wallace@minafter\.com/i.test(afterExpand)
      const hasEdit = await page.getByRole('button', { name: /Edit contact/i }).isVisible().catch(() => false)
      log(
        'f9-expand',
        emailVisible && hasEdit && !composeOpenAfterCard && !emailOnCard ? 'PASS' : 'FAIL',
        JSON.stringify({ emailOnCard, emailVisible, hasEdit, composeOpenAfterCard }),
      )

      if (hasEdit) {
        await page.getByRole('button', { name: /Edit contact/i }).click()
        const editTitle = await page
          .getByRole('heading', { name: /Edit contact/i })
          .isVisible({ timeout: 5000 })
          .catch(() => false)
        const emailVal = await page.locator('input[type="email"]').inputValue().catch(() => '')
        await dump('f9_edit', await page.locator('body').innerText())
        await shot(page, 'f9_edit')
        log(
          'f9-edit',
          editTitle && /devon\.wallace@minafter\.com/i.test(emailVal) ? 'PASS' : 'FAIL',
          JSON.stringify({ editTitle, emailVal }),
        )
        await page.getByRole('button', { name: /Cancel/i }).click().catch(() => {})
        await page.waitForTimeout(300)
      }

      const mail = page.getByRole('button', { name: new RegExp(`Email ${CONTACT}`, 'i') })
      if (await mail.isVisible().catch(() => false)) {
        await mail.click()
        const dialog = page.getByRole('dialog')
        await dialog.waitFor({ state: 'visible', timeout: 10000 })
        await dump('f10_compose_preselect', await dialog.innerText())
        await shot(page, 'f10_compose_preselect')
        const pressed = (await dialog.locator('[aria-pressed="true"]').allInnerTexts()).map((s) =>
          s.replace(/\s+/g, ' ').trim(),
        )
        const onlyDevon = pressed.length === 1 && /Devon/i.test(pressed[0])
        const hasOneOff = await page.getByLabel('Someone not on this file').isVisible().catch(() => false)
        log(
          'f10-preselect',
          onlyDevon && hasOneOff ? 'PASS' : 'FAIL',
          JSON.stringify({ pressed, hasOneOff }),
        )
        if (hasOneOff) {
          await page.getByLabel('Someone not on this file').fill('oneoff@example.com')
          await page.getByRole('button', { name: /^Add$/i }).click()
          const afterAdd = await dialog.innerText()
          log(
            'f10-one-off',
            /oneoff@example.com/i.test(afterAdd) ? 'PASS' : 'FAIL',
            'typed one-off To; did not Generate',
          )
        }
        await page.getByRole('button', { name: /Cancel/i }).click()
      } else {
        log('f10-preselect', 'FAIL', `Mail icon for ${CONTACT} missing`)
      }
    }

    // ── Feature 10 Email tab ───────────────────────────────────────────────
    const emailTab = page.getByRole('tab', { name: /^Email$/i })
    await emailTab.scrollIntoViewIfNeeded().catch(() => {})
    if (await emailTab.isVisible({ timeout: 8000 }).catch(() => false)) {
      await emailTab.click()
      await page.getByText(/Nothing sends until you tap Send/i).waitFor({ timeout: 15000 })
      const emailText = await page.locator('body').innerText()
      await dump('f10_email_tab', emailText)
      await shot(page, 'f10_email_tab')
      const outboxCopy = emailText.includes('Drafts you prepare land on Outbox')
      const letters = /named letters|authorized letters|inspection-reminder letters/i.test(emailText)
      const folders = /Outbox/.test(emailText) && /Sent/.test(emailText) && /Inbox/.test(emailText)
      log(
        'f10-outbox-copy',
        outboxCopy && !letters && folders ? 'PASS' : 'FAIL',
        JSON.stringify({ outboxCopy, letters, folders }),
      )
      await page.getByRole('tab', { name: /^Sent/i }).click()
      await page.waitForTimeout(250)
      await page.getByRole('tab', { name: /^Inbox/i }).click()
      await page.waitForTimeout(250)
      await page.getByRole('tab', { name: /^Outbox/i }).click()
      log('f10-folders', 'PASS', 'clicked Outbox → Sent → Inbox → Outbox')

      const draftRow = page.getByTestId('email-draft-row').first()
      if (await draftRow.isVisible().catch(() => false)) {
        await draftRow.click()
        await page.waitForTimeout(1500)
        const editBtn = page.getByRole('button', { name: /^Edit$/i }).first()
        if (await editBtn.isVisible({ timeout: 8000 }).catch(() => false)) {
          await editBtn.click()
          const hasTo = await page.locator('input[aria-label="To"]').isVisible().catch(() => false)
          const hasCc = await page.locator('input[aria-label="Cc"]').isVisible().catch(() => false)
          await dump('f10_draft_edit', await page.locator('body').innerText())
          await shot(page, 'f10_draft_edit')
          log(
            'f10-edit-recipients',
            hasTo && hasCc ? 'PASS' : 'FAIL',
            JSON.stringify({ hasTo, hasCc, url: page.url() }),
          )
          await page.getByRole('button', { name: /Cancel/i }).first().click().catch(() => {})
        } else {
          log('f10-edit-recipients', 'FAIL', 'opened a draft but Edit was not on screen')
        }
        await page.goto(`${APP}/transactions/${DEAL}?tab=email`, { waitUntil: 'domcontentloaded' })
        await dismissOverlays(page)
      } else {
        log(
          'f10-edit-recipients',
          'SKIP',
          'No Outbox draft on this file — did not Generate',
        )
      }

      const composeBtn = page.getByRole('button', { name: /^Compose$/i })
      if (await composeBtn.isVisible().catch(() => false)) {
        await composeBtn.click()
        const compose = page.getByRole('dialog')
        await compose.waitFor({ state: 'visible', timeout: 8000 })
        const nonePressed = (await compose.locator('[aria-pressed="true"]').count()) === 0
        log(
          'f10-compose-blank',
          nonePressed ? 'PASS' : 'FAIL',
          'Header Compose should not preselect everyone',
        )
        await page.getByRole('button', { name: /Cancel/i }).click()
      }
    } else {
      log('f10-outbox-copy', 'FAIL', 'Email tab not visible')
    }

    // ── Feature 11 / 12 ────────────────────────────────────────────────────
    const tasksTab = page.getByRole('tab', { name: /^Tasks$/i })
    await tasksTab.scrollIntoViewIfNeeded().catch(() => {})
    await tasksTab.click()
    await page.waitForTimeout(1500)
    await dump('f11_tasks', await page.locator('body').innerText())
    await shot(page, 'f11_tasks')
    const closingRow = page.getByRole('button', { name: /Expand .*Closing Information/i }).first()
    if (await closingRow.isVisible().catch(() => false)) {
      await closingRow.click()
      await page.waitForTimeout(400)
      const dialogAfterRow = await page
        .getByRole('dialog', { name: /Complete this task/i })
        .isVisible()
        .catch(() => false)
      log(
        'f11-row-expands-only',
        dialogAfterRow ? 'FAIL' : 'PASS',
        dialogAfterRow ? 'Row click opened Complete this task' : 'Row click did not open the email dialog',
      )
      const kebab = page.getByRole('button', { name: /Actions for .*Closing Information/i }).first()
      if (await kebab.isVisible().catch(() => false)) {
        await kebab.click()
        await page.getByRole('menuitem', { name: /Email transaction party/i }).click()
        const complete = page.getByRole('dialog', { name: 'Complete this task' })
        const opened = await complete
          .waitFor({ state: 'visible', timeout: 25000 })
          .then(() => true)
          .catch(() => false)
        if (opened) {
          await page
            .getByText(/Aime can complete this for you|Couldn't load the plan|No recipient|no contact/i)
            .waitFor({ timeout: 25000 })
            .catch(() => {})
          const planText = await complete.innerText()
          await dump('f11_complete', planText)
          await shot(page, 'f11_complete')
          log(
            'f11-complete-dialog',
            planText.includes('Complete this task') ? 'PASS' : 'FAIL',
            planText.slice(0, 500),
          )
          const cdOnPlan = /Closing Disclosure\.pdf/i.test(planText)
          log(
            'f12-no-cd-on-closing-information',
            cdOnPlan ? 'FAIL' : 'PASS',
            cdOnPlan ? 'CD on closing-information plan' : 'No CD.pdf on closing-information plan',
          )
          await closeTaskDialog(page)
        } else {
          log('f11-complete-dialog', 'FAIL', 'Email transaction party did not open')
        }
      }
    } else {
      log('f11-row-expands-only', 'SKIP', 'No Closing Information task on this file')
      log('f11-complete-dialog', 'SKIP', 'No Closing Information task on this file')
      log('f12-no-cd-on-closing-information', 'SKIP', 'No Closing Information task on this file')
    }

    const cdName = page.getByText('Closing Disclosure Delivered', { exact: true }).first()
    if (await cdName.isVisible().catch(() => false)) {
      await cdName.scrollIntoViewIfNeeded()
      const kebabCd = page.getByRole('button', { name: 'Actions for Closing Disclosure Delivered' })
      await kebabCd.scrollIntoViewIfNeeded()
      await kebabCd.click({ force: true })
      await page.getByRole('menuitem', { name: /Email transaction party/i }).click()
      const complete = page.getByRole('dialog', { name: 'Complete this task' })
      const opened = await complete
        .waitFor({ state: 'visible', timeout: 25000 })
        .then(() => true)
        .catch(() => false)
      if (opened) {
        await page.waitForTimeout(2500)
        const t = await complete.innerText()
        await dump('f12_cd_delivered', t)
        await shot(page, 'f12_cd_delivered')
        log(
          'f12-cd-delivered-inquiry',
          /Closing Disclosure\.pdf/i.test(t) ? 'FAIL' : 'PASS',
          t.slice(0, 700),
        )
        await closeTaskDialog(page)
      }
    } else {
      log('f12-cd-delivered-inquiry', 'SKIP', 'No Closing Disclosure Delivered task visible')
    }

    // ── Feature 13 ─────────────────────────────────────────────────────────
    const statusBtn = page.getByRole('button', { name: /^(Active|Completed|Closed|Terminated|Paused|Incomplete)$/ }).first()
    await statusBtn.click()
    await page.getByRole('menuitem', { name: /^Completed$/ }).click()
    const completedDlg = page.getByRole('alertdialog')
    await completedDlg.waitFor({ state: 'visible', timeout: 8000 })
    const completedText = await completedDlg.innerText()
    await dump('f13_completed', completedText)
    await shot(page, 'f13_completed')
    log(
      'f13-completed',
      completedText.includes('Keep the file Active until then') ? 'PASS' : 'FAIL',
      completedText.slice(0, 500),
    )
    await completedDlg.getByRole('button', { name: /^Cancel$/i }).click()
    await page.waitForTimeout(400)

    await page.getByRole('button', { name: /^(Active|Completed|Closed|Terminated|Paused|Incomplete)$/ }).first().click()
    await page.getByRole('menuitem', { name: /^Terminated$/ }).click()
    const termDlg = page.getByRole('alertdialog')
    await termDlg.waitFor({ state: 'visible', timeout: 8000 })
    const dt = await termDlg.innerText()
    await dump('f13_terminated', dt)
    await shot(page, 'f13_terminated')
    log(
      'f13-terminated',
      dt.includes('Automatic emails stop') && !dt.includes('Automatic letters stop') ? 'PASS' : 'FAIL',
      dt.slice(0, 500),
    )
    await termDlg.getByRole('button', { name: /^Cancel$/i }).click()
    await page.waitForTimeout(400)
    log('f13-still-active', 'PASS', 'Cancelled Terminated; did not Change status')

    await page.goto(`${APP}/transactions/all?tab=Terminated`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await dismissOverlays(page)
    await page.waitForTimeout(2000)
    const listText = await page.locator('body').innerText()
    await dump('f13_terminated_tab', listText)
    await shot(page, 'f13_terminated_tab')
    log(
      'f13-transactions-tab',
      /\bTerminated\b/.test(listText) ? 'PASS' : 'FAIL',
      'All Transactions should list a Terminated filter',
    )

    await page.goto(`${APP}/dashboard/admin`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await dismissOverlays(page)
    await page.waitForTimeout(2000)
    const adminText = await page.locator('body').innerText()
    await dump('f13_admin', adminText)
    await shot(page, 'f13_admin')
    log(
      'f13-admin-tile',
      /Terminated/i.test(adminText) ? 'PASS' : 'FAIL',
      /Deals by stage/i.test(adminText) ? 'Deals by stage includes Terminated' : adminText.slice(0, 400),
    )
  } catch (err) {
    log('script', 'FAIL', err?.stack || err?.message || err)
    await shot(page, 'crash')
  } finally {
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    await browser.close()
  }

  const failed = findings.filter((f) => f.result === 'FAIL')
  const skipped = findings.filter((f) => f.result === 'SKIP')
  console.log(`\n${findings.length} checks, ${failed.length} FAIL, ${skipped.length} SKIP`)
  process.exit(failed.length ? 1 : 0)
}

run()
