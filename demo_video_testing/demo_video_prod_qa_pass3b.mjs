/**
 * Pass 3b — Scene 6 inbound match + remaining surfaces after Scene 4 auto-apply.
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, 'artifacts_2026-08-12_pass3b')
mkdirSync(OUT, { recursive: true })

const EMAIL = 'crazyaidev20500519@gmail.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'https://app.velvetelves.com'
const DEAL = 'https://app.velvetelves.com/transactions/e17bca76-8d70-44da-be4b-f6ace2367ff6'

const findings = []
let shotIdx = 0
function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 6000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 360) : ''}`)
}
async function shot(page, name) {
  shotIdx += 1
  const file = path.join(OUT, `${String(shotIdx).padStart(2, '0')}_${name}.png`)
  await page.screenshot({ path: file, fullPage: false }).catch(() => {})
}
async function dump(page, name) {
  const text = await page.locator('body').innerText({ timeout: 8000 }).catch(() => '')
  writeFileSync(path.join(OUT, `${name}.txt`), text)
  return text
}
async function dismiss(page) {
  for (const name of [/Skip tour/i, /Keep connected/i, /Got it/i, /Not now/i]) {
    const b = page.getByRole('button', { name }).first()
    if (await b.isVisible({ timeout: 400 }).catch(() => false)) await b.click().catch(() => {})
  }
  await page.keyboard.press('Escape').catch(() => {})
}

function inboxHasInbound(text) {
  return /Question about 1842 Willowbrook Lane closing/i.test(text)
}

const run = async () => {
  const browser = await chromium.launch({
    headless: false,
    channel: 'chrome',
    slowMo: 70,
    args: ['--start-maximized'],
  })
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } })
  const page = await context.newPage()
  page.setDefaultTimeout(25000)

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.locator('button[type=submit]').click()
    await page.waitForURL(/\/(dashboard|transactions)/, { timeout: 45000 })
    await page.waitForTimeout(1200)
    await dismiss(page)

    // Confirm Scene 4 task landed
    await page.goto(`${DEAL}?tab=tasks`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2500)
    await dismiss(page)
    const tasksTab = page.getByRole('tab', { name: /^Tasks$/i }).first()
    if (await tasksTab.isVisible({ timeout: 2000 }).catch(() => false)) await tasksTab.click()
    await page.waitForTimeout(1500)
    const searchTasks = page.getByPlaceholder(/search/i).first()
    if (await searchTasks.isVisible({ timeout: 1500 }).catch(() => false)) {
      await searchTasks.fill('title commitment')
      await page.waitForTimeout(800)
    }
    await shot(page, 'tasks_title_commitment')
    const tasks = await dump(page, 'tasks_title_commitment')
    log(
      'scene4_result_on_deal',
      /Confirm title commitment reviewed/i.test(tasks) ? 'PASS' : 'FAIL',
      tasks.match(/Confirm title commitment[\s\S]{0,240}/)?.[0] || tasks.slice(0, 600),
    )

    // Scene 6 inbox
    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await dismiss(page)
    const inboxTab = page.getByRole('tab', { name: /^Inbox$/i }).first()
    if (await inboxTab.isVisible({ timeout: 2000 }).catch(() => false)) await inboxTab.click()
    await page.waitForTimeout(800)

    let inboxText = ''
    let foundInbound = false
    for (let attempt = 1; attempt <= 6; attempt += 1) {
      const refresh = page.getByRole('button', { name: /Refresh email/i }).first()
      if (await refresh.isVisible({ timeout: 1500 }).catch(() => false)) await refresh.click().catch(() => {})
      await page.waitForTimeout(attempt === 1 ? 5000 : 15000)
      const search = page.getByLabel('Search email')
      if (await search.isVisible({ timeout: 1500 }).catch(() => false)) {
        await search.fill('')
        await search.fill('Willowbrook')
        await page.waitForTimeout(1500)
      }
      await shot(page, `inbox_attempt_${attempt}`)
      inboxText = await dump(page, `inbox_attempt_${attempt}`)
      foundInbound = inboxHasInbound(inboxText)
      log('scene6_inbox_poll', foundInbound ? 'PASS' : 'INFO', `attempt=${attempt}; found=${foundInbound}; has_1842=${/1842/i.test(inboxText)}; has_selman=${/selman/i.test(inboxText)}`)
      if (foundInbound) break
    }

    log(
      'scene6_message_present',
      foundInbound ? 'PASS' : 'FAIL',
      foundInbound
        ? 'Inbound Willowbrook closing question is in Intelligence → Email → Inbox'
        : inboxText.slice(0, 1500),
    )

    if (foundInbound) {
      const row = page.getByText('Question about 1842 Willowbrook Lane closing', { exact: false }).first()
      await row.click({ timeout: 8000 }).catch(async () => {
        await page.locator('li, button').filter({ hasText: /Question about 1842 Willowbrook/i }).first().click()
      })
      await page.waitForTimeout(1800)
      await shot(page, 'inbox_detail')
      const detail = await dump(page, 'inbox_detail')
      const notLinked = /Not linked to a deal yet/i.test(detail) || (/Not linked/i.test(detail) && /Question about 1842/i.test(detail))
      const matched = /1842 Willowbrook/i.test(detail) && !/Not linked to a deal yet/i.test(detail)
      log(
        'scene6_matched_to_deal',
        matched && !notLinked ? 'PASS' : 'FAIL',
        `matched=${matched}; notLinked=${notLinked}; ${detail.slice(-1400)}`,
      )
      log(
        'scene6_ai_category',
        /Question|Date change|Update|FYI|Document|Needs a read|Money/i.test(detail) ? 'PASS' : 'WARN',
        detail.slice(-1200),
      )
    } else {
      log('scene6_matched_to_deal', 'FAIL', 'Inbound never appeared after 6 refresh attempts')
      log('scene6_ai_category', 'FAIL', 'Cannot inspect category')
    }

    // Deal Email tab
    await page.goto(DEAL, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2200)
    await dismiss(page)
    const emailTab = page.getByRole('tab', { name: /^Email$/i }).first()
    if (await emailTab.isVisible({ timeout: 2500 }).catch(() => false)) await emailTab.click()
    await page.waitForTimeout(1200)
    const dealInbox = page.getByRole('button', { name: /^Inbox$/i }).first()
    if (await dealInbox.isVisible({ timeout: 2500 }).catch(() => false)) await dealInbox.click()
    await page.waitForTimeout(1800)
    await shot(page, 'deal_email_inbox')
    const dealEmail = await dump(page, 'deal_email_inbox')
    const onDeal = /Question about 1842 Willowbrook Lane closing/i.test(dealEmail)
    log(
      'scene6_deal_email_tab',
      onDeal ? 'PASS' : 'FAIL',
      onDeal ? 'Same inbound on deal Email tab' : dealEmail.match(/Inbox[\s\S]{0,900}/)?.[0] || dealEmail.slice(0, 900),
    )

    // Activity / communications
    const activityTab = page.getByRole('tab', { name: /^Activity$/i }).first()
    if (await activityTab.isVisible({ timeout: 2000 }).catch(() => false)) {
      await activityTab.click()
      await page.waitForTimeout(1800)
      await shot(page, 'deal_activity')
      const activity = await dump(page, 'deal_activity')
      log('scene6_deal_activity', /email|Willowbrook|Selman|communication/i.test(activity) ? 'PASS' : 'WARN', activity.slice(0, 800))
      const commsBtn = page.getByRole('button', { name: /Communication/i }).first()
      if (await commsBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await commsBtn.click()
        await page.waitForTimeout(1800)
        await shot(page, 'deal_communications_panel')
        const comms = await dump(page, 'deal_communications_panel')
        log(
          'scene6_communication_history',
          /Question about 1842|james\.l\.selman13|Willowbrook/i.test(comms) ? 'PASS' : 'WARN',
          comms.slice(-1400),
        )
      } else {
        log('scene6_communication_history', 'WARN', 'Communications control not found on Activity tab')
      }
    }

    await page.goto(`${APP}/admin/communications`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await dismiss(page)
    const auditSearch = page.locator('input[type=search], input[placeholder*="Search" i]').first()
    if (await auditSearch.isVisible({ timeout: 2500 }).catch(() => false)) {
      await auditSearch.fill('Willowbrook')
      await page.waitForTimeout(1800)
    }
    await shot(page, 'communication_audit')
    const audit = await dump(page, 'communication_audit')
    log(
      'scene6_communication_audit',
      /Question about 1842|james\.l\.selman13|1842 Willowbrook/i.test(audit) ? 'PASS' : 'WARN',
      audit.slice(0, 1000),
    )

    // Outbox / send button
    await page.goto(`${APP}/ai-emails?view=outbox`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2200)
    await shot(page, 'outbox')
    const outbox = await dump(page, 'outbox')
    log('scene7_outbox_draft', /Willowbrook|James L\. Selman|Approve/i.test(outbox) ? 'PASS' : 'WARN', outbox.slice(0, 700))
    const approveSend = page.getByRole('button', { name: /Approve & send/i }).first()
    log(
      'scene8_approve_send_button',
      (await approveSend.isVisible({ timeout: 2500 }).catch(() => false)) ? 'PASS' : 'WARN',
      'Not clicked — left for camera',
    )

    // Connections / calendar — informational, not blockers
    await page.goto(`${APP}/settings/connections`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2000)
    await dismiss(page)
    await shot(page, 'connections')
    const conn = await dump(page, 'connections')
    log(
      'gmail_connected_state',
      'INFO',
      /Connected/i.test(conn)
        ? 'Gmail already connected. Not a QA blocker for this pass.'
        : conn.slice(0, 500),
    )

    await page.goto(`${APP}/calendar`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await shot(page, 'calendar')
    const cal = await dump(page, 'calendar')
    log(
      'scene9_calendar_ui',
      /Add my closings|Google Calendar|Connect calendar/i.test(cal) ? 'PASS' : 'FAIL',
      /Willowbrook|1842/i.test(cal) ? 'Willowbrook on in-app calendar' : cal.slice(0, 500),
    )
  } catch (err) {
    log('fatal', 'FAIL', err.stack || err.message)
    await shot(page, 'fatal').catch(() => {})
  } finally {
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings }, null, 2))
    await context.close()
    await browser.close()
    console.log('Wrote', path.join(OUT, 'findings.json'))
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
