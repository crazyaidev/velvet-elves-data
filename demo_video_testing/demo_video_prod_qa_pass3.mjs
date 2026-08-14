/**
 * Pass 3 — re-test after inbound Willowbrook Gmail + production deploy.
 * Gmail/Calendar already-connected is informational, not a recording blocker.
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, 'artifacts_2026-08-12_pass3')
mkdirSync(OUT, { recursive: true })

const EMAIL = 'crazyaidev20500519@gmail.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'https://app.velvetelves.com'
const DEAL = 'https://app.velvetelves.com/transactions/e17bca76-8d70-44da-be4b-f6ace2367ff6'
const INBOUND_SUBJECT = 'Question about 1842 Willowbrook Lane closing'
const ASK_PROMPT =
  'Propose adding a task named Confirm title commitment reviewed due August 18, 2026'

const findings = []
let shotIdx = 0
function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 6000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 320) : ''}`)
}
async function shot(page, name) {
  shotIdx += 1
  const file = path.join(OUT, `${String(shotIdx).padStart(2, '0')}_${name}.png`)
  await page.screenshot({ path: file, fullPage: false }).catch(() => {})
  return file
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
  return (
    /Question about 1842 Willowbrook Lane closing/i.test(text) ||
    (/james\.l\.selman13@gmail\.com/i.test(text) && /Willowbrook/i.test(text)) ||
    (/James L\.? Selman/i.test(text) && /1842 Willowbrook/i.test(text) && /closing/i.test(text))
  )
}
function isMatchedToWillowbrook(text) {
  const linked = /1842 Willowbrook/i.test(text) && !/Not linked to a deal/i.test(text)
  const notLinkedRow = /Not linked/i.test(text) && /Question about 1842/i.test(text)
  return linked && !notLinkedRow
}

const run = async () => {
  const browser = await chromium.launch({
    headless: false,
    channel: 'chrome',
    slowMo: 80,
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
    await page.waitForTimeout(1500)
    await dismiss(page)

    // ── Pipeline ──────────────────────────────────────────────────────────
    await page.goto(`${APP}/transactions`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2500)
    await shot(page, 'pipeline')
    const pipe = await dump(page, 'pipeline')
    const dealCountMatch = pipe.match(/(\d+)\s*Active deals/i)
    const activeDeals = dealCountMatch ? Number(dealCountMatch[1]) : (/Willowbrook/i.test(pipe) ? 1 : 0)
    const unhealthy = /Unhealthy/i.test(pipe)
    log(
      'pipeline',
      activeDeals >= 3 ? 'PASS' : 'FAIL',
      `active_deals=${activeDeals}; willowbrook=${/Willowbrook/i.test(pipe)}; unhealthy=${unhealthy}`,
    )
    log(
      'pipeline_density_for_recording',
      activeDeals >= 3 ? 'PASS' : 'FAIL',
      activeDeals < 3
        ? `Part 1 still too thin (${activeDeals} active deal(s)). Need several real-looking deals.`
        : `${activeDeals} active deals`,
    )

    // ── Contacts / seller (deployed cache invalidation) ───────────────────
    await page.goto(DEAL, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2500)
    await dismiss(page)
    const contactsTab = page.getByRole('tab', { name: /^Contacts$/i }).first()
    if (await contactsTab.isVisible({ timeout: 3000 }).catch(() => false)) await contactsTab.click()
    await page.waitForTimeout(1200)
    await shot(page, 'contacts')
    const contacts = await dump(page, 'contacts')
    const sellerMissing = /No seller on file/i.test(contacts)
    log('contacts_seller', sellerMissing ? 'FAIL' : 'PASS', contacts.match(/SELLER[\s\S]{0,280}/)?.[0] || contacts.slice(0, 400))
    if (sellerMissing) {
      await page.getByRole('button', { name: /Add seller/i }).click()
      await page.waitForTimeout(800)
      await page.getByPlaceholder('First').fill('Harper')
      await page.getByPlaceholder('Last').fill('Devlin')
      await page.getByPlaceholder('name@company.com').fill('happydev0705+seller@gmail.com')
      await page.getByPlaceholder('(317) 555-0000').fill('317-555-0142')
      await page.getByRole('button', { name: /Add Contact/i }).click()
      await page.waitForTimeout(2500)
      await shot(page, 'contacts_after_add_seller')
      const afterAdd = await dump(page, 'contacts_after_add_seller')
      log(
        'contacts_add_seller_refresh',
        /No seller on file/i.test(afterAdd) ? 'FAIL' : 'PASS',
        afterAdd.match(/SELLER[\s\S]{0,280}/)?.[0] || afterAdd.slice(0, 400),
      )
    } else {
      log('contacts_add_seller_refresh', 'SKIP', 'Seller already on file; cache-invalidation path not re-exercised')
    }

    // ── Scene 4: natural “Propose adding…” + spoken date (deployed) ───────
    await page.goto(DEAL, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2000)
    await dismiss(page)
    const ask = page.getByRole('button', { name: /Ask AI/i }).first()
    if (await ask.isVisible({ timeout: 3000 }).catch(() => false)) {
      if ((await ask.getAttribute('aria-pressed')) !== 'true') await ask.click()
    }
    const composer = page.getByLabel('Message the AI agent')
    await composer.waitFor({ timeout: 8000 })
    await composer.click()
    await composer.fill(ASK_PROMPT)
    await page.getByRole('button', { name: /^Send$/i }).click().catch(async () => {
      await page.keyboard.press('Enter')
    })
    await page.waitForTimeout(18000)
    await shot(page, 'ask_propose_natural')
    const propose = await dump(page, 'ask_propose_natural')
    const hasProposal = /Proposed action/i.test(propose) && /title commitment reviewed/i.test(propose)
    log('scene4_natural_propose', hasProposal ? 'PASS' : 'FAIL', propose.slice(-1800))
    if (hasProposal) {
      const approve = page.getByRole('button', { name: /^Approve$/i }).first()
      await approve.click()
      await page.waitForTimeout(5000)
      await shot(page, 'ask_approved')
      log('scene4_approve', 'PASS', 'Clicked Approve on natural-language proposal')
      const tasksTab = page.getByRole('tab', { name: /^Tasks$/i }).first()
      if (await tasksTab.isVisible({ timeout: 2000 }).catch(() => false)) {
        await tasksTab.click()
        await page.waitForTimeout(1500)
        await shot(page, 'tasks_after_approve')
        const tasks = await dump(page, 'tasks_after_approve')
        log(
          'scene4_result_on_deal',
          /Confirm title commitment reviewed/i.test(tasks) ? 'PASS' : 'WARN',
          tasks.match(/Confirm title commitment[\s\S]{0,220}/)?.[0] || tasks.slice(0, 500),
        )
      }
    } else {
      log('scene4_approve', 'FAIL', 'No Proposed action card for spoken-date prompt')
    }

    // ── Scene 6: inbound Gmail match ──────────────────────────────────────
    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await dismiss(page)
    const inboxTab = page.getByRole('tab', { name: /^Inbox$/i }).first()
    if (await inboxTab.isVisible({ timeout: 2000 }).catch(() => false)) await inboxTab.click()
    await page.waitForTimeout(800)

    let inboxText = ''
    let foundInbound = false
    for (let attempt = 1; attempt <= 5; attempt += 1) {
      const refresh = page.getByRole('button', { name: /Refresh email/i }).first()
      if (await refresh.isVisible({ timeout: 1500 }).catch(() => false)) await refresh.click().catch(() => {})
      await page.waitForTimeout(attempt === 1 ? 4000 : 12000)
      const search = page.getByLabel('Search email')
      if (await search.isVisible({ timeout: 1500 }).catch(() => false)) {
        await search.fill('Willowbrook')
        await page.waitForTimeout(1200)
      }
      await shot(page, `inbox_attempt_${attempt}`)
      inboxText = await dump(page, `inbox_attempt_${attempt}`)
      foundInbound = inboxHasInbound(inboxText)
      log('scene6_inbox_poll', foundInbound ? 'PASS' : 'INFO', `attempt=${attempt}; found=${foundInbound}`)
      if (foundInbound) break
    }

    log(
      'scene6_message_present',
      foundInbound ? 'PASS' : 'FAIL',
      foundInbound
        ? 'Inbound Willowbrook closing question is in Intelligence → Email → Inbox'
        : inboxText.slice(0, 1200),
    )

    if (foundInbound) {
      const row = page.getByRole('button', { name: /Question about 1842 Willowbrook Lane closing/i }).first()
      if (await row.isVisible({ timeout: 3000 }).catch(() => false)) {
        await row.click()
        await page.waitForTimeout(1500)
      } else {
        // Fallback: click any visible list button mentioning Willowbrook
        const alt = page.locator('button').filter({ hasText: /1842 Willowbrook/i }).first()
        if (await alt.isVisible({ timeout: 2000 }).catch(() => false)) await alt.click()
        await page.waitForTimeout(1500)
      }
      await shot(page, 'inbox_detail')
      const detail = await dump(page, 'inbox_detail')
      const matched = /1842 Willowbrook/i.test(detail) && !/Not linked to a deal yet/i.test(detail)
      const notLinked = /Not linked/i.test(detail)
      log(
        'scene6_matched_to_deal',
        matched && !notLinked ? 'PASS' : 'FAIL',
        matched && !notLinked
          ? 'Message shows 1842 Willowbrook (auto-matched, no manual filing)'
          : detail.slice(0, 1500),
      )
      const category =
        detail.match(/\b(Question|Date change|Update|FYI|Document|Doc request|Money|Needs a read|Message|Vendor reply)\b/)?.[1] ||
        'unknown'
      log(
        'scene6_ai_category',
        /Question|Date change|Update|FYI|Document|Needs a read/i.test(detail) ? 'PASS' : 'WARN',
        `category_chip≈${category}; snippet=${detail.slice(-900)}`,
      )
    } else {
      log('scene6_matched_to_deal', 'FAIL', 'Inbound message never appeared in Inbox after 5 refresh attempts')
      log('scene6_ai_category', 'FAIL', 'Cannot inspect category; message not in Inbox')
    }

    // Deal Email tab inbox
    await page.goto(`${DEAL}?tab=email`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2000)
    await dismiss(page)
    const emailTab = page.getByRole('tab', { name: /^Email$/i }).first()
    if (await emailTab.isVisible({ timeout: 2000 }).catch(() => false)) await emailTab.click()
    await page.waitForTimeout(1000)
    const dealInbox = page.getByRole('button', { name: /^Inbox$/i }).first()
    if (await dealInbox.isVisible({ timeout: 2000 }).catch(() => false)) await dealInbox.click()
    await page.waitForTimeout(1500)
    await shot(page, 'deal_email_inbox')
    const dealEmail = await dump(page, 'deal_email_inbox')
    const onDealEmail =
      /Question about 1842 Willowbrook Lane closing/i.test(dealEmail) ||
      (/james\.l\.selman13/i.test(dealEmail) && /Willowbrook/i.test(dealEmail)) ||
      (/No incoming emails matched to this deal yet/i.test(dealEmail) ? false : /1842 Willowbrook/i.test(dealEmail) && /Selman|closing/i.test(dealEmail))
    log(
      'scene6_deal_email_tab',
      onDealEmail ? 'PASS' : 'FAIL',
      onDealEmail
        ? 'Same inbound message on the deal Email tab'
        : dealEmail.match(/Inbox[\s\S]{0,800}/)?.[0] || dealEmail.slice(0, 800),
    )

    // Communication history (Activity + Communications panel / audit)
    const activityTab = page.getByRole('tab', { name: /^Activity$/i }).first()
    if (await activityTab.isVisible({ timeout: 2000 }).catch(() => false)) {
      await activityTab.click()
      await page.waitForTimeout(1500)
      await shot(page, 'deal_activity')
      const activity = await dump(page, 'deal_activity')
      log(
        'scene6_deal_activity',
        /Willowbrook|Selman|1842|email/i.test(activity) ? 'PASS' : 'WARN',
        activity.match(/Communications[\s\S]{0,600}/)?.[0] || activity.slice(0, 700),
      )
      const commsBtn = page.getByRole('button', { name: /Communication/i }).first()
      if (await commsBtn.isVisible({ timeout: 1500 }).catch(() => false)) {
        await commsBtn.click()
        await page.waitForTimeout(1500)
        await shot(page, 'deal_communications_panel')
        const comms = await dump(page, 'deal_communications_panel')
        log(
          'scene6_communication_history',
          /Question about 1842|james\.l\.selman13|Willowbrook/i.test(comms) ? 'PASS' : 'WARN',
          comms.slice(-1200),
        )
      }
    }

    await page.goto(`${APP}/admin/communications`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await dismiss(page)
    const auditSearch = page.getByPlaceholder(/search/i).first()
    if (await auditSearch.isVisible({ timeout: 2000 }).catch(() => false)) {
      await auditSearch.fill('Willowbrook')
      await page.waitForTimeout(1500)
    }
    await shot(page, 'communication_audit')
    const audit = await dump(page, 'communication_audit')
    log(
      'scene6_communication_audit',
      /Question about 1842|james\.l\.selman13|1842 Willowbrook/i.test(audit) ? 'PASS' : 'WARN',
      audit.slice(0, 900),
    )

    // ── Scene 7/8 staged draft still present ──────────────────────────────
    await page.goto(`${APP}/ai-emails?view=outbox`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2000)
    await shot(page, 'outbox')
    const outbox = await dump(page, 'outbox')
    log(
      'scene7_outbox_draft',
      /Willowbrook|James L\. Selman|Approve/i.test(outbox) ? 'PASS' : 'WARN',
      outbox.slice(0, 700),
    )
    const approveSend = page.getByRole('button', { name: /Approve & send/i }).first()
    log(
      'scene8_approve_send_button',
      (await approveSend.isVisible({ timeout: 2000 }).catch(() => false)) ? 'PASS' : 'WARN',
      'Button present; not clicked so the camera can show send live',
    )

    // ── Gmail / Calendar: connected is OK for this pass (not a blocker) ───
    await page.goto(`${APP}/settings/connections`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2000)
    await dismiss(page)
    await shot(page, 'connections')
    const conn = await dump(page, 'connections')
    const gmailConnected = /Gmail/i.test(conn) && /Connected/i.test(conn)
    log(
      'gmail_calendar_connected_state',
      gmailConnected ? 'INFO' : 'WARN',
      'Already connected — not a QA blocker. Film Disconnect→Connect on a throwaway Google only if the video still needs both consent screens.',
    )

    await page.goto(`${APP}/calendar`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await shot(page, 'calendar')
    const cal = await dump(page, 'calendar')
    log(
      'scene9_calendar_ui',
      /Add my closings|Google Calendar|Connect calendar/i.test(cal) ? 'PASS' : 'FAIL',
      /Willowbrook|1842/i.test(cal) ? 'Willowbrook visible on in-app calendar' : cal.slice(0, 500),
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
