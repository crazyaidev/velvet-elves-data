/**
 * Pass 2 — remaining demo-video scenes on the Willowbrook deal.
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, 'artifacts_2026-08-12_pass2')
mkdirSync(OUT, { recursive: true })

const EMAIL = 'crazyaidev20500519@gmail.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'https://app.velvetelves.com'
const DEAL = 'https://app.velvetelves.com/transactions/e17bca76-8d70-44da-be4b-f6ace2367ff6'

const findings = []
let shotIdx = 0
function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 280) : ''}`)
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
  for (const name of [/Skip tour/i, /Keep connected/i]) {
    const b = page.getByRole('button', { name }).first()
    if (await b.isVisible({ timeout: 400 }).catch(() => false)) await b.click().catch(() => {})
  }
  await page.keyboard.press('Escape').catch(() => {})
}

const run = async () => {
  const browser = await chromium.launch({
    headless: false,
    channel: 'chrome',
    slowMo: 90,
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

    // Pipeline after seeding
    await page.goto(`${APP}/transactions`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2000)
    await shot(page, 'pipeline')
    const pipe = await dump(page, 'pipeline')
    log(
      'pipeline_after_create',
      /No active transactions yet/i.test(pipe) ? 'FAIL' : 'PASS',
      /Willowbrook/i.test(pipe) ? 'Willowbrook visible' : pipe.slice(0, 400),
    )

    await page.goto(DEAL, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2500)
    await dismiss(page)

    // Add seller if missing
    const contactsTab = page.getByRole('tab', { name: /^Contacts$/i }).first()
    if (await contactsTab.isVisible({ timeout: 3000 }).catch(() => false)) await contactsTab.click()
    await page.waitForTimeout(1200)
    await shot(page, 'contacts_before_seller')
    const before = await dump(page, 'contacts_before_seller')
    if (/No seller on file/i.test(before)) {
      await page.getByRole('button', { name: /Add seller/i }).click()
      await page.waitForTimeout(800)
      const first = page.getByPlaceholder('First')
      const last = page.getByPlaceholder('Last')
      await first.fill('Harper')
      await last.fill('Devlin')
      await page.getByPlaceholder('name@company.com').fill('happydev0705@gmail.com')
      await page.getByPlaceholder('(317) 555-0000').fill('317-555-0142')
      await page.getByRole('button', { name: /Add Contact/i }).click()
      await page.waitForTimeout(2000)
      await shot(page, 'contacts_after_seller')
      const after = await dump(page, 'contacts_after_seller')
      log(
        'add_seller',
        /No seller on file/i.test(after) ? 'FAIL' : 'PASS',
        after.match(/SELLER[\s\S]{0,200}/)?.[0] || after.slice(0, 300),
      )
    } else {
      log('add_seller', 'PASS', 'Seller already on file')
    }

    // Scene 4: Ask AI with a prompt the deterministic matcher understands
    await page.goto(DEAL, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2000)
    const ask = page.getByRole('button', { name: /Ask AI/i }).first()
    if (await ask.isVisible({ timeout: 3000 }).catch(() => false)) {
      if ((await ask.getAttribute('aria-pressed')) !== 'true') await ask.click()
    }
    const composer = page.getByLabel('Message the AI agent')
    await composer.waitFor({ timeout: 8000 })
    await composer.click()
    await composer.fill('Add a task called Confirm earnest money received due 2026-08-18')
    await page.getByRole('button', { name: /^Send$/i }).click().catch(async () => {
      await page.keyboard.press('Enter')
    })
    await page.waitForTimeout(16000)
    await shot(page, 'ask_add_task')
    const propose = await dump(page, 'ask_add_task')
    const hasProposal = /Proposed action/i.test(propose)
    log('scene4_add_task_proposal', hasProposal ? 'PASS' : 'FAIL', propose.slice(-1200))
    if (hasProposal) {
      const approve = page.getByRole('button', { name: /^Approve$/i }).first()
      await approve.click()
      await page.waitForTimeout(5000)
      await shot(page, 'ask_approved')
      log('scene4_approve', 'PASS', 'Clicked Approve')
      const tasksTab = page.getByRole('tab', { name: /^Tasks$/i }).first()
      if (await tasksTab.isVisible({ timeout: 2000 }).catch(() => false)) {
        await tasksTab.click()
        await page.waitForTimeout(1500)
        await shot(page, 'tasks_after_approve')
        const tasks = await dump(page, 'tasks_after_approve')
        log(
          'scene4_result_on_deal',
          /Confirm earnest money received/i.test(tasks) ? 'PASS' : 'WARN',
          tasks.match(/Confirm earnest[\s\S]{0,200}/)?.[0] || tasks.slice(0, 400),
        )
      }
    }

    // Scene 9 calendar
    await page.goto(`${APP}/calendar`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(2500)
    await shot(page, 'calendar')
    const cal = await dump(page, 'calendar')
    log(
      'scene9_calendar',
      /Google Calendar|Connect calendar|Add my closings/i.test(cal) ? 'PASS' : 'FAIL',
      cal.slice(0, 600),
    )

    // Scene 7 compose — use #compose-intent, not a generic dialog textarea
    await page.goto(DEAL, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2000)
    const emailTab = page.getByRole('tab', { name: /^Email$/i }).first()
    if (await emailTab.isVisible({ timeout: 2000 }).catch(() => false)) await emailTab.click()
    await page.waitForTimeout(1000)
    await page.getByRole('button', { name: /^Compose$/i }).click()
    await page.waitForTimeout(1200)
    await shot(page, 'compose_open')
    const james = page.getByRole('button', { name: /James L\. Selman/i }).first()
    if (await james.isVisible({ timeout: 3000 }).catch(() => false)) await james.click()
    await page.locator('#compose-intent').fill(
      'Short test note confirming we received the signed purchase agreement for 1842 Willowbrook Lane, Carmel, IN. Closing is September 25, 2026. This is a Velvet Elves demo-video QA message — no action needed.',
    )
    await shot(page, 'compose_filled')
    await page.getByRole('button', { name: /Generate drafts/i }).click()
    await page.waitForTimeout(25000)
    await shot(page, 'after_generate')
    log('scene7_generate', 'INFO', `url=${page.url()}`)

    await page.goto(`${APP}/ai-emails?view=outbox`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2500)
    await shot(page, 'outbox')
    const outbox = await dump(page, 'outbox')
    log(
      'scene7_outbox_draft',
      /Willowbrook|James L\. Selman|Approve/i.test(outbox) ? 'PASS' : 'WARN',
      outbox.slice(0, 700),
    )

    const edit = page.getByRole('button', { name: /^Edit$/i }).first()
    if (await edit.isVisible({ timeout: 4000 }).catch(() => false)) {
      await edit.click()
      await page.waitForTimeout(600)
      const body = page.locator('textarea').filter({ hasNot: page.locator('[inert] textarea') }).last()
      // Prefer the draft editor: visible enabled textarea in the detail pane
      const editor = page.locator('textarea:not([disabled])').last()
      const cur = await editor.inputValue().catch(() => '')
      await editor.fill(`${cur}\n\n[QA edit] Please confirm receipt of this demo-video test message.`)
      await shot(page, 'draft_edited')
      log('scene7_edit', 'PASS', 'Edited draft body')
      // Leave in edit mode so the video can show persistence; cancel to avoid accidental send
      await page.getByRole('button', { name: /Cancel/i }).click().catch(() => {})
    } else {
      log('scene7_edit', 'WARN', 'Edit button not found')
    }

    const approveSend = page.getByRole('button', { name: /Approve & send/i }).first()
    log(
      'scene8_approve_send_button',
      (await approveSend.isVisible({ timeout: 2000 }).catch(() => false)) ? 'PASS' : 'WARN',
      'Button present; not clicked in this pass so the video can show the send live. Recipient would be james.l.selman13@gmail.com if selected.',
    )

    // Documents tab preview
    await page.goto(`${DEAL}?tab=documents`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(2500)
    const docsTab = page.getByRole('tab', { name: /^Documents$/i }).first()
    if (await docsTab.isVisible({ timeout: 2000 }).catch(() => false)) await docsTab.click()
    await page.waitForTimeout(2000)
    await shot(page, 'documents')
    const docs = await dump(page, 'documents')
    log('scene3_documents', /willowbrook|purchase agreement|pdf/i.test(docs) ? 'PASS' : 'WARN', docs.slice(0, 500))

    // Compliance
    const compTab = page.getByRole('tab', { name: /^Compliance$/i }).first()
    if (await compTab.isVisible({ timeout: 2000 }).catch(() => false)) await compTab.click()
    await page.waitForTimeout(1500)
    await shot(page, 'compliance')
    const comp = await dump(page, 'compliance')
    log('scene3_compliance', /checklist|missing|required/i.test(comp) ? 'PASS' : 'WARN', comp.slice(0, 500))
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
