/**
 * Real-browser pass for Features 8–13 on local Vite.
 * Clicks through the workspace. Does not Send. Does not confirm Terminated.
 *
 *   $env:QA_APP='http://localhost:5173'
 *   $env:QA_EMAIL='shyna.elene@minafter.com'
 *   $env:QA_PASSWORD='...'
 *   node feature8_13_browser_verify.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_feature8_13_verify')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'shyna.elene@minafter.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const APP = (process.env.QA_APP || 'http://localhost:5173').replace(/\/$/, '')
const DEAL = process.env.QA_DEAL || '4585ea3b-43d1-420e-b5d9-8193afdd3d1f'
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

const MANUAL =
  'AI suggests. You click to apply anything. Named emails wait until you switch this deal off Manual.'
const ASSISTED = 'Routine work runs. Named emails are drafted — you tap Send.'
const AUTOPILOT = 'Authorized emails send without a tap when confidence is high enough.'

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
  page.setDefaultTimeout(20000)

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.locator('#login-email').waitFor({ state: 'visible', timeout: 20000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 30000 })
    await dismissOverlays(page)
    log('login', 'PASS', page.url())

    await page.goto(`${APP}/transactions/${DEAL}`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.getByRole('heading', { level: 1 }).waitFor({ state: 'visible', timeout: 25000 })
    await dismissOverlays(page)
    const tabNames = await page
      .getByRole('tablist', { name: 'Workspace sections' })
      .getByRole('tab')
      .allInnerTexts()
      .catch(() => [])
    log('open-deal', 'PASS', `${page.url()} tabs=${JSON.stringify(tabNames)}`)

    // ── Feature 8 ──────────────────────────────────────────────────────────
    const posture = page.getByRole('button', { name: /Automation posture for this deal/i })
    await posture.click()
    let text = await menuText(page)
    await dump('f8_menu_open', text)
    await shot(page, 'f8_menu_open')
    const missing = [MANUAL, ASSISTED, AUTOPILOT].filter((n) => !text.includes(n))
    const bad = ['you manually send', 'Named letters', 'Authorized letters'].filter((n) =>
      text.toLowerCase().includes(n.toLowerCase()),
    )
    const inheritExplains =
      /Follow .+ again\. Changing the workspace setting will apply here/i.test(text)
    log(
      'f8-captions',
      missing.length || bad.length ? 'FAIL' : 'PASS',
      JSON.stringify({ missing, bad, inheritExplains }),
    )
    log(
      'f8-settings-copy',
      inheritExplains ? 'PASS' : 'FAIL',
      'Use workspace default line should say a later How it runs change applies here',
    )

    await page.getByRole('menuitem', { name: /Manual/i }).click()
    await page.waitForTimeout(800)
    const afterManual = await page.locator('body').innerText()
    await dump('f8_after_manual', afterManual)
    await shot(page, 'f8_after_manual')
    const toastManual =
      /This deal now runs manual/i.test(afterManual) || /now runs Manual/i.test(afterManual)
    await posture.click()
    text = await menuText(page)
    const manualSelected = /Manual[\s\S]{0,80}AI suggests/i.test(text) && text.includes(MANUAL)
    log(
      'f8-pin-manual',
      toastManual && manualSelected && !/you manually send/i.test(text) ? 'PASS' : 'FAIL',
      JSON.stringify({ toastManual, manualSelected, snippet: text.slice(0, 400) }),
    )
    await page.getByRole('menuitem', { name: /Autopilot/i }).click()
    await page.waitForTimeout(600)
    log('f8-restore-autopilot', 'PASS', 'put the file back on Autopilot after reading Manual')

    // ── Feature 9 ──────────────────────────────────────────────────────────
    await page.goto(`${APP}/transactions/${DEAL}?tab=contacts`, {
      waitUntil: 'domcontentloaded',
    })
    await dismissOverlays(page)
    await page.getByRole('heading', { name: 'Contacts' }).waitFor({ timeout: 15000 })
    const daniel = page.getByText('Daniel Carter', { exact: true }).first()
    const hasDaniel = await daniel.waitFor({ state: 'visible', timeout: 15000 }).then(() => true).catch(() => false)
    const contactsRoot = page.locator('section[aria-label="Contacts"]')
    const beforeExpand = await contactsRoot.innerText().catch(() => page.locator('body').innerText())
    await dump('f9_contacts_collapsed', beforeExpand)
    await shot(page, 'f9_contacts_collapsed')

    const buttons = await page.getByRole('button').evaluateAll((els) =>
      els.map((e) => (e.getAttribute('aria-label') || e.textContent || '').trim()).filter(Boolean),
    )
    await dump('f9_buttons', buttons.join('\n'))

    if (!hasDaniel) {
      log('f9-expand', 'FAIL', 'Daniel Carter not on Contacts tab though API has 4 parties')
    } else {
      const collapsedHasEmail = beforeExpand.includes('carter.buyers@testmail.com')
      const expandBtn = page.getByRole('button', { name: /Show details for Daniel Carter/i })
      const expandAlt = page.getByRole('button', { name: /Daniel Carter/i }).first()
      const expander = (await expandBtn.isVisible().catch(() => false)) ? expandBtn : expandAlt
      await expander.click()
      await page.waitForTimeout(400)
      const composeOpenAfterCard = await page.getByRole('dialog').isVisible().catch(() => false)
      const afterExpand = await contactsRoot.innerText()
      await dump('f9_contacts_expanded', afterExpand)
      await shot(page, 'f9_contacts_expanded')
      const emailVisible = afterExpand.includes('carter.buyers@testmail.com')
      const hasEdit = await page.getByRole('button', { name: /Edit contact/i }).isVisible().catch(() => false)
      log(
        'f9-expand',
        emailVisible && hasEdit && !composeOpenAfterCard ? 'PASS' : 'FAIL',
        JSON.stringify({
          collapsedHasEmail,
          emailVisible,
          hasEdit,
          composeOpenAfterCard,
        }),
      )

      if (hasEdit) {
        await page.getByRole('button', { name: /Edit contact/i }).click()
        const editTitle = await page.getByRole('heading', { name: /Edit contact/i }).isVisible({ timeout: 5000 }).catch(() => false)
        const emailField = page.getByLabel('Email Address')
        const emailVal = await emailField.inputValue().catch(() => '')
        await dump('f9_edit_modal', await page.locator('body').innerText())
        await shot(page, 'f9_edit_modal')
        log(
          'f9-edit',
          editTitle && emailVal.includes('carter.buyers@testmail.com') ? 'PASS' : 'FAIL',
          JSON.stringify({ editTitle, emailVal }),
        )
        await page.getByRole('button', { name: /Cancel/i }).click().catch(() => {})
      }

      const mail = page.getByRole('button', { name: /Email Daniel Carter/i })
      if (await mail.isVisible().catch(() => false)) {
        await mail.click()
        const dialog = page.getByRole('dialog')
        await dialog.waitFor({ state: 'visible', timeout: 8000 })
        const dlg = await dialog.innerText()
        await dump('f10_compose_preselect', dlg)
        await shot(page, 'f10_compose_preselect')
        const pressed = await dialog.locator('[aria-pressed="true"]').allInnerTexts()
        const pressedClean = pressed.map((s) => s.replace(/\s+/g, ' ').trim())
        const onlyDaniel = pressedClean.length === 1 && /Daniel|carter.buyers/i.test(pressedClean[0])
        const hasOneOff = dlg.includes('Someone not on this file')
        const notEveryone = !/All parties/i.test(dlg) || pressedClean.length === 1
        log(
          'f10-preselect',
          onlyDaniel && hasOneOff && notEveryone ? 'PASS' : 'FAIL',
          JSON.stringify({ pressedClean, hasOneOff }),
        )
        await page.getByLabel('Someone not on this file').fill('oneoff@example.com')
        await page.getByRole('button', { name: /^Add$/i }).click()
        const afterAdd = await dialog.innerText()
        log(
          'f10-one-off',
          /oneoff@example.com/i.test(afterAdd) ? 'PASS' : 'FAIL',
          afterAdd.slice(0, 800),
        )
        await page.getByRole('button', { name: /Cancel/i }).click()
      } else {
        log('f10-preselect', 'FAIL', 'Mail icon for Daniel Carter missing')
      }

      const sellerMail = await page.getByRole('button', { name: /Email Test Seller/i }).isVisible().catch(() => false)
      log(
        'f9-blank-email',
        sellerMail ? 'FAIL' : 'PASS',
        sellerMail
          ? 'Test Seller has no email — Mail icon should be absent'
          : 'No Mail icon on Test Seller (blank email)',
      )
    }

    // ── Feature 10 Email tab ───────────────────────────────────────────────
    const emailTab = page.getByRole('tab', { name: /^Email$/i })
    await emailTab.scrollIntoViewIfNeeded().catch(() => {})
    if (await emailTab.isVisible({ timeout: 8000 }).catch(() => false)) {
      await emailTab.click()
      await page.getByText(/Nothing sends until you tap Send/i).waitFor({ timeout: 10000 })
      const emailText = await page.locator('body').innerText()
      await dump('f10_email_tab', emailText)
      await shot(page, 'f10_email_tab')
      const outboxCopy = emailText.includes('Drafts you prepare land on Outbox')
      const letters = /named letters|authorized letters|inspection-reminder letters/i.test(emailText)
      const folders = /Outbox/.test(emailText) && /Sent/.test(emailText) && /Inbox/.test(emailText)
      const exactOrder =
        'Nothing sends until you tap Send. On Autopilot, named welcome / title / inspection-deadline emails may already have gone out on their own. On Assisted they wait here for Send. Drafts you prepare land on Outbox — Inbox is mail that arrived.'
      log(
        'f10-outbox-copy',
        outboxCopy && !letters && folders ? 'PASS' : 'FAIL',
        JSON.stringify({ outboxCopy, letters, folders }),
      )
      log(
        'f10-exact-sentence-order',
        emailText.includes(exactOrder) ? 'PASS' : 'FAIL',
        'A-file expected Outbox clause last; product currently puts it after the first sentence',
      )
      await page.getByRole('tab', { name: /^Sent/i }).click()
      await page.waitForTimeout(300)
      await page.getByRole('tab', { name: /^Inbox/i }).click()
      await page.waitForTimeout(300)
      await page.getByRole('tab', { name: /^Outbox/i }).click()
      log('f10-folders', 'PASS', 'clicked Outbox → Sent → Inbox → Outbox')

      const draftRow = page.getByTestId('email-draft-row').first()
      if (await draftRow.isVisible().catch(() => false)) {
        await draftRow.click()
        await page.waitForTimeout(1200)
        const editBtn = page.getByRole('button', { name: /^Edit$/i }).first()
        if (await editBtn.isVisible({ timeout: 8000 }).catch(() => false)) {
          await editBtn.click()
          const hasTo = await page.getByLabel('To').isVisible().catch(() => false)
          const hasCc = await page.getByLabel('Cc').isVisible().catch(() => false)
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
          'No Outbox draft on this file — did not Generate (would create mail to parties). Code has To/Cc on Edit.',
        )
      }

      await page.getByRole('button', { name: /^Compose$/i }).click()
      const compose = page.getByRole('dialog')
      await compose.waitFor({ state: 'visible', timeout: 8000 })
      const nonePressed = (await compose.locator('[aria-pressed="true"]').count()) === 0
      log(
        'f10-compose-blank',
        nonePressed ? 'PASS' : 'FAIL',
        'Header Compose should not preselect everyone',
      )
      await page.getByRole('button', { name: /Cancel/i }).click()
    } else {
      log('f10-outbox-copy', 'FAIL', 'Email tab not visible')
    }

    // ── Feature 11 / 12 (Pass in Audri file; confirm no regression) ───────
    const tasksTab = page.getByRole('tab', { name: /^Tasks$/i })
    await tasksTab.scrollIntoViewIfNeeded().catch(() => {})
    await tasksTab.click()
    await page.waitForTimeout(1200)
    await dump('f11_tasks', await page.locator('body').innerText())
    await shot(page, 'f11_tasks')
    const closingRow = page.getByRole('button', { name: /Expand .*Closing Information/i }).first()
    const cdDelivered = page.getByRole('button', { name: /Expand .*Closing Disclosure Delivered/i }).first()
    if (await closingRow.isVisible().catch(() => false)) {
      await closingRow.click()
      await page.waitForTimeout(400)
      const dialogAfterRow = await page.getByRole('dialog', { name: /Complete this task/i }).isVisible().catch(() => false)
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
        const opened = await complete.waitFor({ state: 'visible', timeout: 25000 }).then(() => true).catch(() => false)
        if (opened) {
          await page.getByText(/Aime can complete this for you|Couldn't load the plan|No recipient/i).waitFor({ timeout: 25000 }).catch(() => {})
          const planText = await complete.innerText()
          await dump('f11_complete', planText)
          await shot(page, 'f11_complete')
          const titleOk = planText.includes('Complete this task')
          const scrollable = await complete.evaluate((el) => el.scrollHeight > 80)
          log(
            'f11-complete-dialog',
            titleOk && scrollable ? 'PASS' : 'FAIL',
            JSON.stringify({ titleOk, scrollable, snippet: planText.slice(0, 500) }),
          )
          const cdOnPlan = /Closing Disclosure/i.test(planText) || /\bCD\.pdf\b/i.test(planText)
          log(
            'f12-no-cd-on-closing-information',
            cdOnPlan ? 'FAIL' : 'PASS',
            cdOnPlan ? 'Closing Disclosure appeared on a closing-information plan' : 'No CD on this closing-information plan',
          )
          await page.getByRole('button', { name: 'Close' }).click().catch(() => {})
        } else {
          log('f11-complete-dialog', 'FAIL', 'Email transaction party did not open Complete this task')
        }
      }
    } else {
      log('f11-row-expands-only', 'SKIP', 'No Closing Information task on Oak Ridge')
      log('f11-complete-dialog', 'SKIP', 'No Closing Information task on Oak Ridge')
      log('f12-no-cd-on-closing-information', 'SKIP', 'No Closing Information task on Oak Ridge')
    }
    if (await cdDelivered.isVisible().catch(() => false)) {
      const kebabCd = page.getByRole('button', { name: /Actions for .*Closing Disclosure Delivered/i }).first()
      await kebabCd.click()
      await page.getByRole('menuitem', { name: /Email transaction party/i }).click()
      const complete = page.getByRole('dialog', { name: 'Complete this task' })
      const opened = await complete.waitFor({ state: 'visible', timeout: 25000 }).then(() => true).catch(() => false)
      if (opened) {
        await page.waitForTimeout(2000)
        const t = await complete.innerText()
        await dump('f12_cd_delivered', t)
        await shot(page, 'f12_cd_delivered')
        const attached = /Closing Disclosure\.pdf/i.test(t)
        log(
          'f12-cd-delivered-inquiry',
          attached ? 'FAIL' : 'PASS',
          attached ? 'CD Delivered plan attached the CD' : 'CD Delivered plan did not attach Closing Disclosure.pdf',
        )
        await page.getByRole('button', { name: 'Close' }).click().catch(() => {})
      } else {
        log('f12-cd-delivered-inquiry', 'SKIP', 'Could not open CD Delivered plan')
      }
    } else {
      log('f12-cd-delivered-inquiry', 'SKIP', 'No Closing Disclosure Delivered task on this file')
    }

    const docsTab = page.getByRole('tab', { name: /^Documents$/i })
    if (await docsTab.isVisible().catch(() => false)) {
      await docsTab.click()
      await page.waitForTimeout(800)
      const docs = await page.locator('body').innerText()
      await dump('f12_documents', docs)
      await shot(page, 'f12_documents')
      log(
        'f12-documents-cd-presence',
        'PASS',
        /Closing Disclosure/i.test(docs) ? 'Documents lists a Closing Disclosure' : 'No CD filename on Documents',
      )
    }

    // ── Feature 13 ─────────────────────────────────────────────────────────
    await page.getByRole('button', { name: /^Active$/, exact: true }).click()
    await page.getByRole('menuitem', { name: /^Completed$/ }).click()
    const completedDlg = page.getByRole('alertdialog').or(page.getByRole('dialog')).first()
    await completedDlg.waitFor({ state: 'visible', timeout: 8000 })
    const completedText = await completedDlg.innerText()
    await dump('f13_completed', completedText)
    await shot(page, 'f13_completed')
    log(
      'f13-completed',
      completedText.includes('Keep the file Active until then') ? 'PASS' : 'FAIL',
      completedText.slice(0, 600),
    )
    await page.getByRole('button', { name: /^Cancel$/i }).click()
    await page.waitForTimeout(400)

    await page.getByRole('button', { name: /^Active$/, exact: true }).click()
    await page.getByRole('menuitem', { name: /^Terminated$/ }).click()
    const dialog = page.getByRole('alertdialog').or(page.getByRole('dialog'))
    await dialog.first().waitFor({ state: 'visible', timeout: 8000 })
    const dt = await dialog.first().innerText()
    await dump('f13_terminated', dt)
    await shot(page, 'f13_terminated')
    log(
      'f13-terminated',
      dt.includes('Automatic emails stop') && !dt.includes('Automatic letters stop') ? 'PASS' : 'FAIL',
      dt.slice(0, 600),
    )
    await page.getByRole('button', { name: /^Cancel$/i }).click()
    await page.waitForTimeout(400)
    const stillActive = await page.getByRole('button', { name: /^Active$/, exact: true }).isVisible().catch(() => false)
    log('f13-still-active', stillActive ? 'PASS' : 'FAIL', 'Cancelled Terminated; file should stay Active')

    await page.goto(`${APP}/transactions/all?tab=Terminated`, { waitUntil: 'domcontentloaded' })
    await dismissOverlays(page)
    await page.waitForTimeout(1200)
    const listText = await page.locator('body').innerText()
    await dump('f13_terminated_tab', listText)
    await shot(page, 'f13_terminated_tab')
    const hasTerminatedTab =
      (await page.getByRole('tab', { name: /^Terminated/i }).isVisible().catch(() => false)) ||
      /Terminated/i.test(listText)
    log(
      'f13-transactions-tab',
      hasTerminatedTab ? 'PASS' : 'FAIL',
      'Transactions list should offer a Terminated tab (empty is fine)',
    )

    await page.goto(`${APP}/dashboard/admin`, { waitUntil: 'domcontentloaded' })
    await dismissOverlays(page)
    await page.waitForTimeout(1500)
    const adminText = await page.locator('body').innerText()
    await dump('f13_admin', adminText)
    await shot(page, 'f13_admin')
    log(
      'f13-admin-tile',
      /Terminated/i.test(adminText) ? 'PASS' : 'FAIL',
      /Terminated/i.test(adminText)
        ? 'Admin home shows Terminated'
        : 'No Terminated label on /dashboard/admin (Audri saw only Closed on a different control)',
    )
  } catch (err) {
    log('script', 'FAIL', err?.stack || err?.message || err)
    await shot(page, 'crash')
  } finally {
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    await browser.close()
  }

  const failed = findings.filter((f) => f.result === 'FAIL')
  console.log(`\n${findings.length} checks, ${failed.length} FAIL`)
  process.exit(failed.length ? 1 : 0)
}

run()
