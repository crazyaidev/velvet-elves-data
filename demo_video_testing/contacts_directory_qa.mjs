/**
 * Local Chrome QA for Deals › Contacts directory redesign.
 * Headed Google Chrome against http://localhost:5173
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, 'artifacts_contacts_qa_2026-08-13')
mkdirSync(OUT, { recursive: true })

const EMAIL = 'shyna.elene@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://localhost:5173'
const UNIQUE = `QA Hale ${Date.now().toString().slice(-6)}`

const findings = []
const consoleErrors = []
const pageErrors = []
let shotIdx = 0

function log(id, result, details = '') {
  const row = { id, result, details: String(details).slice(0, 4000) }
  findings.push(row)
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 280) : ''}`)
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
    /Not now/i,
    /Maybe later/i,
    /Continue to (app|dashboard)/i,
    /Go to Dashboard/i,
  ]
  for (const name of labels) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 500 }).catch(() => false)) {
      await btn.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(300)
    }
    const link = page.getByRole('link', { name }).first()
    if (await link.isVisible({ timeout: 300 }).catch(() => false)) {
      await link.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(300)
    }
  }
  await page.keyboard.press('Escape').catch(() => {})
}

async function main() {
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: false,
    args: ['--start-maximized'],
  })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  })
  const page = await context.newPage()
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (err) => pageErrors.push(err.message))

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'networkidle', timeout: 30000 })
    await shot(page, 'login')
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 })
    await page.waitForTimeout(1500)
    await dismissOverlays(page)
    await dismissOverlays(page)
    log('login', 'PASS', page.url())
  } catch (err) {
    log('login', 'FAIL', err.message)
    await shot(page, 'login_fail')
    await dumpText(page, 'login_fail')
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, consoleErrors, pageErrors }, null, 2))
    await browser.close()
    process.exit(1)
  }

  try {
    await page.goto(`${APP}/contacts`, { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(1200)
    await dismissOverlays(page)
    await shot(page, 'contacts_desktop')
    const body = await dumpText(page, 'contacts_desktop')

    const breadcrumb = page.getByRole('navigation', { name: 'Breadcrumb' })
    const crumbText = (await breadcrumb.innerText().catch(() => '')) || ''
    if (/Deals/.test(crumbText) && /Contacts/.test(crumbText)) {
      log('breadcrumb_label', 'PASS', crumbText.replace(/\s+/g, ' ').trim())
    } else {
      log('breadcrumb_label', 'FAIL', crumbText || 'missing breadcrumb')
    }

    const briefcase = await breadcrumb.locator('svg.lucide-briefcase').count()
    const usersIcon = await breadcrumb.locator('svg.lucide-users').count()
    if (briefcase > 0 && usersIcon === 0) {
      log('breadcrumb_icon', 'PASS', 'Briefcase icon on Deals crumb')
    } else {
      log('breadcrumb_icon', 'FAIL', `briefcase=${briefcase} users=${usersIcon}`)
    }

    const table = page.locator('table')
    const tableVisible = await table.isVisible().catch(() => false)
    const cardGrid = await page.locator('.grid.grid-cols-1, .grid.sm\\:grid-cols-2').count()
    if (tableVisible) {
      log('directory_table', 'PASS', 'Desktop table is visible')
    } else {
      log('directory_table', 'FAIL', `tableVisible=${tableVisible} body=${body.slice(0, 400)}`)
    }
    if (cardGrid === 0) {
      log('no_card_grid', 'PASS', 'No contact card grid')
    } else {
      log('no_card_grid', 'FAIL', `found ${cardGrid} card-grid containers`)
    }

    const newBtn = page.getByRole('button', { name: /new contact/i })
    if (await newBtn.isVisible()) {
      log('new_contact_cta', 'PASS')
    } else {
      log('new_contact_cta', 'FAIL', 'New contact button missing')
    }

    const search = page.getByLabel('Search contacts')
    if (await search.isVisible()) {
      log('search', 'PASS')
    } else {
      log('search', 'FAIL')
    }
  } catch (err) {
    log('contacts_page', 'FAIL', err.message)
    await shot(page, 'contacts_fail')
  }

  // Add a contact (mouse + minimal typing)
  try {
    await page.getByRole('button', { name: /new contact/i }).click()
    const dialog = page.getByRole('dialog', { name: 'Add a contact' })
    await dialog.waitFor({ state: 'visible', timeout: 8000 })
    await shot(page, 'add_contact_modal')
    await dialog.locator('input[placeholder="Jordan Hale"]').fill(UNIQUE)
    await dialog.locator('select').selectOption('loan_officer')
    await dialog.locator('input[placeholder="Title company, lender…"]').fill('QA National Bank')
    await dialog.locator('input[type="email"]').fill(`qa.${Date.now()}@example.com`)
    await dialog.locator('input[type="tel"]').fill('3175550199')
    await dialog.getByRole('button', { name: 'Save contact' }).click()
    await dialog.waitFor({ state: 'hidden', timeout: 20000 })
    await page.getByText(UNIQUE).first().waitFor({ state: 'visible', timeout: 10000 })
    await shot(page, 'after_create')
    log('create_contact', 'PASS', UNIQUE)
  } catch (err) {
    log('create_contact', 'FAIL', err.message)
    await shot(page, 'create_fail')
  }

  // Search filters the new row
  try {
    const search = page.getByLabel('Search contacts')
    await search.fill(UNIQUE)
    await page.waitForTimeout(400)
    await shot(page, 'search_filtered')
    const hits = await page.getByText(UNIQUE).count()
    const otherLoanOfficers = await page.getByText('Alex').count()
    if (hits >= 1) {
      log('search_filter', 'PASS', `hits=${hits}`)
    } else {
      log('search_filter', 'FAIL', `hits=${hits} other=${otherLoanOfficers}`)
    }
    await search.fill('')
  } catch (err) {
    log('search_filter', 'FAIL', err.message)
  }

  // Open detail from the row
  try {
    await page.getByText(UNIQUE).first().click()
    const detail = page.getByRole('dialog', { name: `${UNIQUE} details` })
    await detail.waitFor({ state: 'visible', timeout: 8000 })
    await shot(page, 'detail_modal')
    const hasCall = await detail.getByRole('link', { name: /call/i }).isVisible().catch(() => false)
    const hasEmail = await detail.getByRole('link', { name: /email/i }).isVisible().catch(() => false)
    if (hasCall && hasEmail) {
      log('detail_actions', 'PASS', 'Call and Email present')
    } else {
      log('detail_actions', 'FAIL', `call=${hasCall} email=${hasEmail}`)
    }
    await detail.getByRole('button', { name: 'Close', exact: true }).click()
  } catch (err) {
    log('detail_modal', 'FAIL', err.message)
    await shot(page, 'detail_fail')
  }

  // Mobile viewport — compact list, not a card wall
  try {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.waitForTimeout(500)
    await shot(page, 'contacts_mobile')
    const tableHidden = await page.locator('table').isHidden()
    const mobileRow = page.locator(`li[data-contact-id]`).first()
    const listVisible = await mobileRow.isVisible().catch(() => false)
    if (tableHidden && listVisible) {
      log('mobile_list', 'PASS', 'Table hidden; compact list visible')
    } else {
      log('mobile_list', 'FAIL', `tableHidden=${tableHidden} listVisible=${listVisible}`)
    }
    const callBtn = page.getByRole('link', { name: /call /i }).first()
    if (await callBtn.isVisible().catch(() => false)) {
      log('mobile_call', 'PASS')
    } else {
      log('mobile_call', 'FAIL', 'No one-tap call control')
    }
  } catch (err) {
    log('mobile', 'FAIL', err.message)
  }

  const relevantConsole = consoleErrors.filter(
    (t) => !/Download the React DevTools/i.test(t) && !/favicon/i.test(t),
  )
  if (pageErrors.length === 0 && relevantConsole.length === 0) {
    log('js_errors', 'PASS')
  } else {
    log('js_errors', 'FAIL', JSON.stringify({ pageErrors, relevantConsole }).slice(0, 1500))
  }

  writeFileSync(
    path.join(OUT, 'findings.json'),
    JSON.stringify({ findings, pageErrors, consoleErrors: relevantConsole }, null, 2),
  )
  console.log('\nWrote', path.join(OUT, 'findings.json'))
  await browser.close()
  const failed = findings.some((f) => f.result === 'FAIL')
  process.exit(failed ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
