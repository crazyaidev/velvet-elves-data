/**
 * Production Chrome QA for GOOGLE_DEMO_VIDEO_REQUIREMENTS.md
 * Headed Google Chrome (channel: "chrome") against https://app.velvetelves.com
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync, existsSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, 'artifacts_2026-08-12')
const PDF = path.join(__dirname, 'willowbrook_purchase_agreement.pdf')
mkdirSync(OUT, { recursive: true })

const EMAIL = 'crazyaidev20500519@gmail.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'https://app.velvetelves.com'
const MARKETING = 'https://velvetelves.com'
const PROPERTY = '1842 Willowbrook Lane'
const TEST_EMAILS = [
  'james.l.selman13@gmail.com',
  'happydev0705@gmail.com',
  'developer.defi0782@gmail.com',
  'gotohigher0705@gmail.com',
]

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let shotIdx = 0
let dealUrl = null

function log(id, result, details = '') {
  const row = { id, result, details: String(details).slice(0, 4000) }
  findings.push(row)
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 240) : ''}`)
}

async function shot(page, name) {
  shotIdx += 1
  const file = path.join(OUT, `${String(shotIdx).padStart(2, '0')}_${name}.png`)
  try {
    await page.screenshot({ path: file, fullPage: false })
  } catch (err) {
    console.log('screenshot failed', name, err.message)
  }
  return file
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
    /Skip tour/i,
    /Skip for now/i,
    /^Skip$/i,
    /Got it/i,
    /Accept all/i,
    /Accept cookies/i,
    /I agree/i,
    /Close/i,
    /Not now/i,
    /Maybe later/i,
  ]
  for (const name of labels) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 600 }).catch(() => false)) {
      await btn.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(400)
    }
  }
  // Escape any leftover dialog
  await page.keyboard.press('Escape').catch(() => {})
}

async function clickIfVisible(page, locator, timeout = 2500) {
  try {
    if (await locator.isVisible({ timeout })) {
      await locator.click({ timeout: 4000 })
      return true
    }
  } catch {
    /* ignore */
  }
  return false
}

async function enabledContinue(page) {
  const buttons = page.getByRole('button', { name: /^(Continue|Confirm Timeline)$/ })
  const n = await buttons.count()
  for (let i = n - 1; i >= 0; i -= 1) {
    const b = buttons.nth(i)
    if (await b.isEnabled().catch(() => false)) return b
  }
  return null
}

async function resolveDoubleChecks(page) {
  const panel = page.getByLabel(/AI double-check/i)
  if (!(await panel.isVisible({ timeout: 1500 }).catch(() => false))) return 0
  let resolved = 0
  for (let round = 0; round < 8; round += 1) {
    const firstBtns = page.getByRole('button', { name: /First read/i })
    const secondBtns = page.getByRole('button', { name: /Second read/i })
    const n = await firstBtns.count()
    if (n === 0) break
    let clicked = false
    for (let i = 0; i < n; i += 1) {
      const first = firstBtns.nth(i)
      const second = secondBtns.nth(i)
      const firstText = ((await first.innerText().catch(() => '')) || '').toLowerCase()
      const secondText = ((await second.innerText().catch(() => '')) || '').toLowerCase()
      const firstEmpty = firstText.includes('not found') || firstText.includes('none')
      const secondEmpty = secondText.includes('not found') || secondText.includes('none')
      const target = firstEmpty && !secondEmpty ? second : first
      if (await target.getAttribute('aria-pressed') === 'true') continue
      await target.click().catch(() => {})
      clicked = true
      resolved += 1
      await page.waitForTimeout(400)
    }
    if (!clicked) break
  }
  return resolved
}

async function fillEmptyPartyContacts(page) {
  let filled = 0
  for (let i = 1; i <= 12; i += 1) {
    const email = page.getByLabel(`Party ${i} email`)
    const phone = page.getByLabel(`Party ${i} phone`)
    if (!(await email.isVisible({ timeout: 400 }).catch(() => false))) continue
    const emailVal = await email.inputValue().catch(() => '')
    const phoneVal = await phone.inputValue().catch(() => '')
    if (!emailVal.trim()) {
      await email.fill(TEST_EMAILS[(i - 1) % TEST_EMAILS.length])
      filled += 1
    }
    if (!phoneVal.trim()) {
      await phone.fill(`317-555-01${String(10 + i).slice(-2)}`)
      filled += 1
    }
  }
  return filled
}

async function fillRequiredDates(page) {
  const accept = page.locator('#p-contract')
  const closing = page.locator('#p-closing')
  if (await accept.isVisible({ timeout: 800 }).catch(() => false)) {
    const v = await accept.inputValue().catch(() => '')
    if (!v) await accept.fill('2026-08-08')
  }
  if (await closing.isVisible({ timeout: 800 }).catch(() => false)) {
    const v = await closing.inputValue().catch(() => '')
    if (!v) await closing.fill('2026-09-25')
  }
  const price = page.locator('#p-price, input[id*="price"]').first()
  if (await price.isVisible({ timeout: 400 }).catch(() => false)) {
    const v = await price.inputValue().catch(() => '')
    if (!v || v === '0') {
      await price.fill('485000')
    }
  }
}

async function waitForWizardStep(page, title, timeout = 120000) {
  await page.getByRole('heading', { name: title }).first().waitFor({ timeout })
}

const run = async () => {
  if (!existsSync(PDF)) {
    throw new Error(`Missing PDF: ${PDF}`)
  }

  const browser = await chromium.launch({
    headless: false,
    channel: 'chrome',
    slowMo: 80,
    args: ['--start-maximized', '--disable-blink-features=AutomationControlled'],
  })
  const context = await browser.newContext({
    viewport: { width: 1600, height: 1000 },
    recordVideo: { dir: path.join(OUT, 'video'), size: { width: 1600, height: 1000 } },
  })
  const page = await context.newPage()
  page.setDefaultTimeout(25000)

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (err) => pageErrors.push(err.message))
  page.on('response', (res) => {
    const url = res.url()
    if (res.status() >= 400 && url.includes('velvetelves')) {
      failedRequests.push(`${res.status()} ${url.slice(0, 220)}`)
    }
  })

  try {
    // ── Scene 1: Identity ──────────────────────────────────────────────
    await page.goto(MARKETING, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2000)
    await dismissOverlays(page)
    await shot(page, 'scene1_marketing_home')
    const homeText = await dumpText(page, 'scene1_home')
    log(
      'scene1_marketing',
      /velvet elves/i.test(homeText) ? 'PASS' : 'FAIL',
      `title=${await page.title()} url=${page.url()}`,
    )

    await page.goto(`${MARKETING}/privacy`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(1500)
    await dismissOverlays(page)
    const googleHeading = page.locator('#google, [id*="google"]').first()
    if (await googleHeading.isVisible({ timeout: 2000 }).catch(() => false)) {
      await googleHeading.scrollIntoViewIfNeeded().catch(() => {})
    } else {
      await page.getByText(/Google user data/i).first().scrollIntoViewIfNeeded().catch(() => {})
    }
    await shot(page, 'scene1_privacy_google')
    const privacyText = await dumpText(page, 'scene1_privacy')
    log(
      'scene1_privacy_google_section',
      /Google user data/i.test(privacyText) ? 'PASS' : 'FAIL',
      privacyText.match(/Google user data[\s\S]{0,280}/)?.[0] || 'section not found',
    )

    // ── Scene 2: Sign in + pipeline ────────────────────────────────────
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(1500)
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await shot(page, 'scene2_login_filled')
    await page.locator('button[type=submit]').click()
    await page.waitForURL(/\/(dashboard|transactions|onboarding)/, { timeout: 45000 })
    await page.waitForTimeout(2500)
    await dismissOverlays(page)
    await shot(page, 'scene2_after_login')
    log('scene2_login', 'PASS', `landed ${page.url()}`)

    await page.goto(`${APP}/transactions`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await dismissOverlays(page)
    await shot(page, 'scene2_active_transactions')
    const listText = await dumpText(page, 'scene2_pipeline')
    const emptyPipeline = /No active transactions yet/i.test(listText)
    const tabBits = ['All', 'Overdue', 'Due Today', 'Closing Soon', 'On Track']
      .filter((t) => listText.includes(t))
      .join(', ')
    log(
      'scene2_pipeline',
      emptyPipeline ? 'FAIL' : 'PASS',
      emptyPipeline
        ? 'Active Transactions empty — demo-blocking'
        : `tabs: ${tabBits || 'n/a'}; snippet: ${listText.slice(0, 400)}`,
    )

    // ── Create flagship deal via AI wizard ─────────────────────────────
    await page.goto(`${APP}/transactions/new`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2000)
    await dismissOverlays(page)
    if (await page.getByRole('button', { name: /^Discard$/i }).isVisible({ timeout: 2500 }).catch(() => false)) {
      await page.getByRole('button', { name: /^Discard$/i }).click()
      await page.waitForTimeout(1200)
      log('wizard_discard_draft', 'INFO', 'Discarded previous wizard draft')
    }
    await shot(page, 'wizard_start')

    const buyerRadio = page.getByRole('radio', { name: /^Buyer$/i }).first()
    if (await buyerRadio.isVisible({ timeout: 4000 }).catch(() => false)) {
      await buyerRadio.check({ force: true }).catch(async () => {
        await page.getByText(/^Buyer$/).first().click()
      })
    } else {
      await page.getByText(/^Buyer$/).first().click()
    }
    await page.waitForTimeout(800)
    await shot(page, 'wizard_buyer_selected')
    log('wizard_representation_buyer', 'PASS', 'Selected Buyer')

    const fileInput = page.locator('input[type=file][aria-label="Upload documents"]')
    await fileInput.setInputFiles(PDF)
    await page.waitForTimeout(2500)
    const uploadedLabel = page.getByText(/Uploaded ·/i).first()
    await uploadedLabel.waitFor({ timeout: 45000 }).catch(() => {})
    const uploadCountText = (await uploadedLabel.innerText().catch(() => '')) || ''
    await shot(page, 'wizard_uploaded')
    log('wizard_upload', /Uploaded · 1/.test(uploadCountText) ? 'PASS' : 'WARN', uploadCountText)

    const startAi = page.getByRole('button', { name: /Start AI extraction/i })
    await startAi.waitFor({ timeout: 45000 })
    await startAi.click()
    log('wizard_start_ai', 'INFO', 'Clicked Start AI extraction')
    await shot(page, 'wizard_parsing')

    const parsingDeadline = Date.now() + 8 * 60 * 1000
    let reachedContract = false
    while (Date.now() < parsingDeadline) {
      const heading = await page
        .getByRole('heading', { name: /Contract Details|AI Extraction|Fill In The Gaps|Contacts & Fees/i })
        .first()
        .innerText()
        .catch(() => '')
      if (/Contract Details/i.test(heading)) {
        reachedContract = true
        break
      }
      if (/Fill In The Gaps|Contacts & Fees/i.test(heading)) {
        reachedContract = true
        break
      }
      const err = await page.getByText(/extraction failed|could not read|unavailable/i).first().isVisible().catch(() => false)
      if (err) {
        log('wizard_ai_extraction', 'FAIL', 'Extraction error visible')
        await shot(page, 'wizard_extract_error')
        break
      }
      await page.waitForTimeout(4000)
    }
    await shot(page, 'wizard_after_parse')
    const afterParse = await dumpText(page, 'wizard_after_parse')
    log(
      'wizard_ai_extraction',
      reachedContract ? 'PASS' : 'FAIL',
      reachedContract
        ? `landed review; has Willowbrook=${/Willowbrook/i.test(afterParse)} price=${/485/.test(afterParse)}`
        : 'Timed out waiting for Contract Details',
    )

    if (reachedContract) {
      await resolveDoubleChecks(page)
      await fillRequiredDates(page)
      await shot(page, 'wizard_contract_details')

      // Advance through remaining wizard steps
      for (let step = 0; step < 8; step += 1) {
        const h = await page
          .getByRole('heading', { name: /Contract Details|Contacts & Fees|Fill In The Gaps|Confirm Details/i })
          .first()
          .innerText()
          .catch(() => '')
        log('wizard_step', 'INFO', h || page.url())
        await resolveDoubleChecks(page)
        if (/Contract Details/i.test(h)) {
          await fillRequiredDates(page)
          // Who orders title if empty
          const titleSelect = page.getByLabel(/Who orders title/i)
          if (await titleSelect.isVisible({ timeout: 600 }).catch(() => false)) {
            const val = await titleSelect.innerText().catch(() => '')
            if (/Select/i.test(val) || !val.trim()) {
              await titleSelect.click().catch(() => {})
              await page.getByRole('option', { name: /^Seller$/i }).click().catch(() => {})
            }
          }
        }
        if (/Contacts & Fees/i.test(h)) {
          await fillEmptyPartyContacts(page)
          await shot(page, 'wizard_contacts')
        }
        const uploadBtn = page.getByRole('button', { name: /Upload Transaction/i })
        if (await uploadBtn.isVisible({ timeout: 800 }).catch(() => false)) {
          await shot(page, 'wizard_confirm')
          await dumpText(page, 'wizard_confirm')
          if (await uploadBtn.isEnabled()) {
            await uploadBtn.click()
            log('wizard_create_click', 'INFO', 'Clicked Upload Transaction')
            break
          }
        }
        const cont = await enabledContinue(page)
        if (cont) {
          await cont.click()
          await page.waitForTimeout(1800)
        } else {
          await shot(page, `wizard_stuck_step_${step}`)
          log('wizard_continue_blocked', 'WARN', `Continue disabled on: ${h}`)
          // last resort: try Upload Transaction anyway
          if (await uploadBtn.isVisible({ timeout: 500 }).catch(() => false)) {
            await uploadBtn.click({ force: true }).catch(() => {})
            break
          }
        }
      }

      try {
        await page.waitForURL(/\/transactions\/[0-9a-f-]{8,}/i, { timeout: 90000 })
        dealUrl = page.url()
        log('wizard_create_deal', 'PASS', dealUrl)
      } catch {
        await shot(page, 'wizard_create_failed')
        log('wizard_create_deal', 'FAIL', `still at ${page.url()}`)
      }
    }

    // ── Scene 3: Inside a transaction ──────────────────────────────────
    if (!dealUrl) {
      // Fall back to first existing deal
      await page.goto(`${APP}/transactions`, { waitUntil: 'domcontentloaded' })
      await page.waitForTimeout(2000)
      const firstDeal = page.locator('a[href*="/transactions/"]').first()
      if (await firstDeal.isVisible({ timeout: 4000 }).catch(() => false)) {
        await firstDeal.click()
        await page.waitForTimeout(2500)
        dealUrl = page.url()
        log('scene3_fallback_deal', 'INFO', dealUrl)
      }
    } else {
      await page.goto(dealUrl, { waitUntil: 'domcontentloaded' })
      await page.waitForTimeout(2500)
    }
    await dismissOverlays(page)
    await shot(page, 'scene3_overview')
    const overviewText = await dumpText(page, 'scene3_overview')
    log(
      'scene3_workspace_loaded',
      /Overview|Timeline|Tasks|Documents|Contacts/i.test(overviewText) ? 'PASS' : 'FAIL',
      `url=${page.url()} willowbrook=${/Willowbrook/i.test(overviewText)}`,
    )

    const tabs = ['Timeline', 'Tasks', 'Documents', 'Compliance', 'Contacts', 'Email', 'Activity', 'Billing']
    for (const tab of tabs) {
      const tabBtn = page.getByRole('tab', { name: new RegExp(`^${tab}$`, 'i') }).first()
      const alt = page.getByRole('button', { name: new RegExp(`^${tab}$`, 'i') }).first()
      const link = page.getByRole('link', { name: new RegExp(`^${tab}$`, 'i') }).first()
      let clicked = false
      for (const loc of [tabBtn, alt, link, page.getByText(tab, { exact: true }).first()]) {
        if (await loc.isVisible({ timeout: 800 }).catch(() => false)) {
          await loc.click().catch(() => {})
          clicked = true
          break
        }
      }
      await page.waitForTimeout(1200)
      await shot(page, `scene3_tab_${tab.toLowerCase()}`)
      const t = await dumpText(page, `scene3_tab_${tab.toLowerCase()}`)
      log(
        `scene3_tab_${tab.toLowerCase()}`,
        clicked ? 'PASS' : 'FAIL',
        clicked ? t.slice(0, 350).replace(/\s+/g, ' ') : `${tab} control not found`,
      )
    }

    // ── Scene 4: Ask AI + approve ──────────────────────────────────────
    // Return to overview / deal root
    if (dealUrl) await page.goto(dealUrl, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2000)
    const askAi = page.getByRole('button', { name: /Ask AI/i }).first()
    if (await askAi.isVisible({ timeout: 4000 }).catch(() => false)) {
      const pressed = await askAi.getAttribute('aria-pressed')
      if (pressed !== 'true') await askAi.click()
      await page.waitForTimeout(1000)
    }
    const composer = page.getByLabel('Message the AI agent')
    if (await composer.isVisible({ timeout: 5000 }).catch(() => false)) {
      await composer.click()
      await composer.fill(
        'What is the property address, purchase price, and closing date for THIS transaction?',
      )
      await page.getByRole('button', { name: /^Send$/i }).click().catch(async () => {
        await page.keyboard.press('Enter')
      })
      await page.waitForTimeout(12000)
      await shot(page, 'scene4_ask_facts')
      const factReply = await dumpText(page, 'scene4_ask_facts')
      const grounded =
        /1842|Willowbrook|485|September 25|2026-09-25/i.test(factReply)
      log(
        'scene4_ask_ai_deal_grounded',
        grounded ? 'PASS' : 'FAIL',
        grounded
          ? 'Reply cites Willowbrook / price / closing'
          : factReply.slice(0, 600),
      )

      await composer.click()
      await composer.fill(
        'Propose adding a task named Confirm earnest money received, due August 18, 2026.',
      )
      await page.getByRole('button', { name: /^Send$/i }).click().catch(async () => {
        await page.keyboard.press('Enter')
      })
      await page.waitForTimeout(14000)
      await shot(page, 'scene4_ask_propose')
      const proposeText = await dumpText(page, 'scene4_ask_propose')
      const hasProposal = /Proposed action|Approve/i.test(proposeText)
      log(
        'scene4_ai_proposal',
        hasProposal ? 'PASS' : 'FAIL',
        hasProposal ? 'Proposal card visible' : proposeText.slice(0, 600),
      )
      if (hasProposal) {
        const approveBtn = page.getByRole('button', { name: /^Approve$/i }).first()
        if (await approveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
          await approveBtn.click()
          await page.waitForTimeout(4000)
          await shot(page, 'scene4_approved')
          log('scene4_approve_action', 'PASS', 'Clicked Approve on proposed action')
          const tasksTab = page.getByRole('tab', { name: /^Tasks$/i }).first()
          if (await tasksTab.isVisible({ timeout: 2000 }).catch(() => false)) {
            await tasksTab.click()
            await page.waitForTimeout(1500)
            await shot(page, 'scene4_tasks_after_approve')
            const tasksText = await dumpText(page, 'scene4_tasks_after_approve')
            log(
              'scene4_result_on_deal',
              /earnest money/i.test(tasksText) ? 'PASS' : 'WARN',
              tasksText.slice(0, 400),
            )
          }
        } else {
          log('scene4_approve_action', 'FAIL', 'Approve button not found on proposal')
        }
      }
    } else {
      await shot(page, 'scene4_no_composer')
      log('scene4_ask_ai_deal_grounded', 'FAIL', 'Deal-scoped AI composer not visible')
    }

    // ── Scene 5: Gmail connect UI ──────────────────────────────────────
    await page.goto(`${APP}/settings/connections`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await dismissOverlays(page)
    await shot(page, 'scene5_connections')
    const connText = await dumpText(page, 'scene5_connections')
    const gmailConnected = /Gmail[\s\S]{0,200}Connected/i.test(connText) || /Connected[\s\S]{0,80}gmail/i.test(connText)
    log(
      'scene5_gmail_ui',
      /Gmail/i.test(connText) ? 'PASS' : 'FAIL',
      `connected=${gmailConnected}; snippet=${connText.slice(0, 500)}`,
    )

    const testConn = page.getByRole('button', { name: /Test connection/i }).first()
    if (await testConn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await testConn.click()
      await page.waitForTimeout(5000)
      await shot(page, 'scene5_test_connection')
      const afterTest = await dumpText(page, 'scene5_test_connection')
      log('scene5_test_connection', /fail|error|expired/i.test(afterTest) && !/ok|success|working|healthy|connected/i.test(afterTest) ? 'WARN' : 'PASS', afterTest.slice(0, 400))
    } else {
      log('scene5_test_connection', 'WARN', 'Test connection button not visible (Gmail may be disconnected)')
    }

    const disconnectBtn = page.getByRole('button', { name: /^Disconnect$/i }).first()
    if (await disconnectBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await disconnectBtn.click()
      await page.waitForTimeout(800)
      await shot(page, 'scene5_disconnect_dialog')
      const dlg = await dumpText(page, 'scene5_disconnect_dialog')
      log(
        'scene10_disconnect_dialog',
        /Disconnect Gmail/i.test(dlg) || /stop syncing inbound mail/i.test(dlg) ? 'PASS' : 'WARN',
        dlg.slice(0, 400),
      )
      const keep = page.getByRole('button', { name: /Keep connected/i })
      if (await keep.isVisible({ timeout: 1500 }).catch(() => false)) {
        await keep.click()
      } else {
        await page.keyboard.press('Escape')
      }
      log('scene5_oauth_consent', 'NOT_RUN', 'Gmail already connected — do not disconnect in this pass; reconnect throwaway Google on camera for the video')
    } else {
      log('scene5_oauth_consent', 'INFO', 'Gmail not connected — Connect is available for filming consent screens')
      await shot(page, 'scene5_gmail_disconnected')
    }

    // ── Scene 6: Intelligence Email inbox ──────────────────────────────
    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await dismissOverlays(page)
    const inboxTab = page.getByRole('tab', { name: /^Inbox$/i }).first()
    if (await inboxTab.isVisible({ timeout: 2000 }).catch(() => false)) await inboxTab.click()
    await page.waitForTimeout(1000)
    await shot(page, 'scene6_inbox')
    const inboxText = await dumpText(page, 'scene6_inbox')
    log(
      'scene6_inbox_ui',
      /Inbox|Email/i.test(inboxText) ? 'PASS' : 'FAIL',
      inboxText.slice(0, 500),
    )
    const matchedWillow = /Willowbrook|1842/i.test(inboxText)
    log(
      'scene6_gmail_readonly_match',
      matchedWillow ? 'PASS' : 'NOT_RUN',
      matchedWillow
        ? 'Willowbrook already present in inbox'
        : 'Needs inbound Gmail to crazyaidev20500519@gmail.com mentioning 1842 Willowbrook Lane',
    )

    const outboxTab = page.getByRole('tab', { name: /^Outbox$/i }).first()
    if (await outboxTab.isVisible({ timeout: 1500 }).catch(() => false)) {
      await outboxTab.click()
      await page.waitForTimeout(1000)
      await shot(page, 'scene7_outbox')
    }

    // Compose a real draft to a tester mailbox (Scenes 7–8 prep)
    if (dealUrl) {
      await page.goto(dealUrl, { waitUntil: 'domcontentloaded' })
      await page.waitForTimeout(2000)
      const emailTab = page.getByRole('tab', { name: /^Email$/i }).first()
      if (await emailTab.isVisible({ timeout: 2000 }).catch(() => false)) await emailTab.click()
      await page.waitForTimeout(1000)
      const composeBtn = page.getByRole('button', { name: /Compose/i }).first()
      if (await composeBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await composeBtn.click()
        await page.waitForTimeout(1200)
        await shot(page, 'scene7_compose_modal')
        const james = page.getByText('james.l.selman13@gmail.com').first()
        if (await james.isVisible({ timeout: 2000 }).catch(() => false)) {
          await james.click()
        } else {
          // click first recipient chip / checkbox
          const firstParty = page.locator('[role=dialog] button, [role=dialog] label').filter({ hasText: /@gmail\.com/ }).first()
          await firstParty.click().catch(() => {})
        }
        const intent = page.getByPlaceholder(/describe|intent|what should/i).first()
        const intentAlt = page.locator('[role=dialog] textarea').first()
        if (await intent.isVisible({ timeout: 1500 }).catch(() => false)) {
          await intent.fill('Send a short test note confirming we received the signed purchase agreement for 1842 Willowbrook Lane, Carmel, IN. Closing is September 25, 2026. This is a Velvet Elves demo-video QA message.')
        } else if (await intentAlt.isVisible({ timeout: 1500 }).catch(() => false)) {
          await intentAlt.fill('Send a short test note confirming we received the signed purchase agreement for 1842 Willowbrook Lane, Carmel, IN. Closing is September 25, 2026. This is a Velvet Elves demo-video QA message.')
        }
        const generate = page.getByRole('button', { name: /Generate/i }).first()
        if (await generate.isVisible({ timeout: 2000 }).catch(() => false)) {
          await generate.click()
          await page.waitForTimeout(20000)
          await shot(page, 'scene7_after_generate')
          log('scene7_compose_generate', 'INFO', `after generate url=${page.url()}`)
        }
      } else {
        log('scene7_compose', 'WARN', 'Compose button not found on deal Email tab')
      }
    }

    await page.goto(`${APP}/ai-emails?view=outbox`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2500)
    await shot(page, 'scene7_outbox_after_compose')
    const outboxText = await dumpText(page, 'scene7_outbox')
    const hasDraft = /Approve & send|Approve/i.test(outboxText) && /draft|outbox|to /i.test(outboxText)
    log('scene7_draft_present', hasDraft || /james\.l\.selman13|Willowbrook/i.test(outboxText) ? 'PASS' : 'WARN', outboxText.slice(0, 500))

    const editBtn = page.getByRole('button', { name: /^Edit$/i }).first()
    if (await editBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await editBtn.click()
      await page.waitForTimeout(800)
      const bodyBox = page.locator('textarea').last()
      if (await bodyBox.isVisible({ timeout: 2000 }).catch(() => false)) {
        const cur = await bodyBox.inputValue().catch(() => '')
        await bodyBox.fill(`${cur}\n\n[QA edit] Please confirm receipt of this demo-video test message.`)
        await shot(page, 'scene7_edit_persisted')
        log('scene7_edit', 'PASS', 'Edited draft body')
        await page.getByRole('button', { name: /Cancel/i }).click().catch(() => {})
      }
    } else {
      log('scene7_edit', 'NOT_RUN', 'No Edit button — no pending draft in Outbox')
    }

    // Do NOT Approve & send in this automated pass unless a clearly-ours recipient is selected.
    // Sending from production Gmail is reserved for a controlled Scene 8 rehearsal.
    log(
      'scene8_gmail_send',
      'NOT_RUN',
      'Left unsent so the video can show Approve & send live. Draft (if created) is in Outbox.',
    )

    // ── Scene 9: Calendar ──────────────────────────────────────────────
    await page.goto(`${APP}/calendar`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await dismissOverlays(page)
    await shot(page, 'scene9_calendar')
    const calText = await dumpText(page, 'scene9_calendar')
    const calConnected = /Google Calendar[\s\S]{0,120}Connected|Connected[\s\S]{0,80}Google Calendar/i.test(calText)
    log(
      'scene9_calendar_ui',
      /Google Calendar|Connect calendar|Add my closings/i.test(calText) ? 'PASS' : 'FAIL',
      `connected=${calConnected}; ${calText.slice(0, 400)}`,
    )
    log(
      'scene9_calendar_oauth_consent',
      'NOT_RUN',
      calConnected
        ? 'Already connected — Disconnect→Connect on camera for the second consent screen'
        : 'Connect Google Calendar is available for filming',
    )
    const addClosings = page.getByRole('button', { name: /Add my closings/i })
    if (await addClosings.isVisible({ timeout: 2000 }).catch(() => false)) {
      log('scene9_add_my_closings_button', 'PASS', 'Button present')
    } else {
      log('scene9_add_my_closings_button', 'WARN', 'Add my closings not visible')
    }

    // ── Dashboard density check ────────────────────────────────────────
    await page.goto(`${APP}/transactions`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2000)
    await shot(page, 'final_pipeline')
    const finalList = await dumpText(page, 'final_pipeline')
    log('final_pipeline_density', /No active transactions yet/i.test(finalList) ? 'FAIL' : 'PASS', finalList.slice(0, 500))

    // ── Admin dashboard ────────────────────────────────────────────────
    await page.goto(`${APP}/dashboard/admin`, { waitUntil: 'domcontentloaded' }).catch(() => {})
    await page.waitForTimeout(2000)
    await shot(page, 'admin_dashboard')
  } catch (err) {
    log('fatal', 'FAIL', err.stack || err.message)
    await shot(page, 'fatal').catch(() => {})
  } finally {
    writeFileSync(
      path.join(OUT, 'findings.json'),
      JSON.stringify(
        {
          dealUrl,
          findings,
          consoleErrors: consoleErrors.slice(0, 40),
          pageErrors: pageErrors.slice(0, 20),
          failedRequests: [...new Set(failedRequests)].slice(0, 40),
        },
        null,
        2,
      ),
    )
    await context.close()
    await browser.close()
    console.log('Wrote', path.join(OUT, 'findings.json'))
    console.log('DEAL_URL', dealUrl)
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
