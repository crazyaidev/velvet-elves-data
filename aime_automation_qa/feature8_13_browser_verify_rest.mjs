/**
 * Finish F12 CD Delivered + F13 surfaces after the first pass left Complete this task open.
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

async function closeTaskDialog(page) {
  const dlg = page.getByRole('dialog', { name: 'Complete this task' })
  if (await dlg.isVisible().catch(() => false)) {
    await dlg.getByRole('button', { name: 'Close' }).click({ timeout: 3000 }).catch(() => {})
    await page.keyboard.press('Escape').catch(() => {})
    await page.waitForTimeout(400)
  }
}

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false }).catch(() => {})
}

async function dump(name, text) {
  writeFileSync(path.join(OUT, `${name}.txt`), String(text ?? ''))
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

    await page.goto(`${APP}/transactions/${DEAL}?tab=tasks`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('heading', { level: 1 }).waitFor({ state: 'visible', timeout: 25000 })
    await dismissOverlays(page)
    await closeTaskDialog(page)

    const kebabCd = page.getByRole('button', { name: 'Actions for Closing Disclosure Delivered' })
    const hasCdTask = await kebabCd.isVisible().catch(() => false)
    if (hasCdTask) {
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
        const attached = /Closing Disclosure\.pdf/i.test(t) || /Attachments/i.test(t) && /Closing Disclosure/i.test(t)
        log(
          'f12-cd-delivered-inquiry',
          attached ? 'FAIL' : 'PASS',
          attached
            ? 'CD Delivered plan attached the CD'
            : t.slice(0, 800),
        )
        await complete.getByRole('button', { name: 'Close' }).click({ force: true }).catch(() => {})
        await page.keyboard.press('Escape').catch(() => {})
        await closeTaskDialog(page)
      } else {
        log('f12-cd-delivered-inquiry', 'FAIL', 'Could not open Complete this task')
      }
    } else {
      log('f12-cd-delivered-inquiry', 'SKIP', 'No Closing Disclosure Delivered kebab')
    }

    await closeTaskDialog(page)
    await page.getByRole('button', { name: /^Active$/, exact: true }).click()
    await page.getByRole('menuitem', { name: /^Completed$/ }).click()
    const completedDlg = page.getByRole('alertdialog')
    await completedDlg.waitFor({ state: 'visible', timeout: 8000 })
    const completedText = await completedDlg.innerText()
    await dump('f13_completed', completedText)
    await shot(page, 'f13_completed')
    log(
      'f13-completed',
      completedText.includes('Keep the file Active until then') &&
        completedText.includes('Change status to Completed')
        ? 'PASS'
        : 'FAIL',
      completedText.slice(0, 600),
    )
    await completedDlg.getByRole('button', { name: /^Cancel$/i }).click()
    await page.waitForTimeout(400)

    await page.getByRole('button', { name: /^Active$/, exact: true }).click()
    await page.getByRole('menuitem', { name: /^Terminated$/ }).click()
    const termDlg = page.getByRole('alertdialog')
    await termDlg.waitFor({ state: 'visible', timeout: 8000 })
    const dt = await termDlg.innerText()
    await dump('f13_terminated', dt)
    await shot(page, 'f13_terminated')
    log(
      'f13-terminated',
      dt.includes('Automatic emails stop') && !dt.includes('Automatic letters stop') ? 'PASS' : 'FAIL',
      dt.slice(0, 600),
    )
    await termDlg.getByRole('button', { name: /^Cancel$/i }).click()
    await page.waitForTimeout(400)
    const stillActive = await page.getByRole('button', { name: /^Active$/, exact: true }).isVisible().catch(() => false)
    log('f13-still-active', stillActive ? 'PASS' : 'FAIL', 'Cancelled; file stayed Active')

    await page.goto(`${APP}/transactions/all?tab=Terminated`, { waitUntil: 'domcontentloaded' })
    await dismissOverlays(page)
    await page.waitForTimeout(1500)
    const listText = await page.locator('body').innerText()
    await dump('f13_terminated_tab', listText)
    await shot(page, 'f13_terminated_tab')
    const tab = page.getByRole('tab', { name: /^Terminated/i })
    const tabOn = await tab.isVisible().catch(() => false)
    const selected = tabOn ? (await tab.getAttribute('aria-selected')) === 'true' : false
    log(
      'f13-transactions-tab',
      tabOn ? 'PASS' : 'FAIL',
      JSON.stringify({ tabOn, selected, emptyHint: /no terminated|fallen through|Terminated/i.test(listText) }),
    )

    await page.goto(`${APP}/dashboard/admin`, { waitUntil: 'domcontentloaded' })
    await dismissOverlays(page)
    await page.waitForTimeout(2000)
    const adminText = await page.locator('body').innerText()
    await dump('f13_admin', adminText)
    await shot(page, 'f13_admin')
    log(
      'f13-admin-tile',
      /Terminated/i.test(adminText) ? 'PASS' : 'FAIL',
      /Deals by stage/i.test(adminText)
        ? 'Deals by stage present; Terminated mentioned'
        : adminText.includes('Terminated')
          ? 'Terminated on admin home'
          : 'No Terminated on /dashboard/admin',
    )
  } catch (err) {
    log('script', 'FAIL', err?.stack || err?.message || err)
    await shot(page, 'crash_rest')
  } finally {
    writeFileSync(path.join(OUT, 'findings_rest.json'), JSON.stringify(findings, null, 2))
    await browser.close()
  }

  const failed = findings.filter((f) => f.result === 'FAIL')
  console.log(`\n${findings.length} checks, ${failed.length} FAIL`)
  process.exit(failed.length ? 1 : 0)
}

run()
