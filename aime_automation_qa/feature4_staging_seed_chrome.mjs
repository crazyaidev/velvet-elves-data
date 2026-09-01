/**
 * Chrome: seeded Feature 4 deals on staging. Preview / Got it only.
 * Never confirm Run AI tasks, Send all ready, or Approve & send.
 *
 *   QA_APP=https://app.stage.velvetelves.com QA_EMAIL=... QA_PASSWORD=... node feature4_staging_seed_chrome.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const APP = (process.env.QA_APP || 'https://app.stage.velvetelves.com').replace(/\/$/, '')
const EMAIL = process.env.QA_EMAIL
const PASSWORD = process.env.QA_PASSWORD
const SEED_PATH = process.env.QA_SEED || path.join(__dirname, 'artifacts_feature4_staging_seed', 'seed.json')
const SCENARIOS_PATH = path.join(__dirname, 'artifacts_feature4_staging_scenarios', 'scenarios.json')
const OUT = path.join(__dirname, 'artifacts_feature4_staging_seed_chrome')
mkdirSync(OUT, { recursive: true })
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
if (!EMAIL || !PASSWORD) {
  console.error('Set QA_EMAIL and QA_PASSWORD')
  process.exit(2)
}

const findings = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 8000) })
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

async function paneSendVisible(page) {
  return page
    .getByRole('button', { name: /^(Approve & send|Send edited reply|Send edited email|Send reply)$/i })
    .first()
    .isVisible()
    .catch(() => false)
}

async function openDealInbox(page, txId, label) {
  await page.goto(`${APP}/transactions/${txId}?tab=email`, {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  })
  await page.getByRole('heading', { name: /This deal's email/i }).waitFor({ timeout: 25000 })
  await dismissOverlays(page)
  const folders = page.getByRole('tablist', { name: /Email folders/i })
  await folders.getByRole('tab', { name: /Inbox/i }).click()
  await page.waitForTimeout(1500)
  const text = await page.locator('body').innerText()
  writeFileSync(path.join(OUT, `${label}.txt`), `${page.url()}\n\n${text}`)
  await page.screenshot({ path: path.join(OUT, `${label}.png`), fullPage: false })
  return text
}

async function run() {
  if (!existsSync(SEED_PATH)) {
    console.error('Missing seed file', SEED_PATH)
    process.exit(2)
  }
  const seed = JSON.parse(readFileSync(SEED_PATH, 'utf8'))
  const scenarios = existsSync(SCENARIOS_PATH)
    ? JSON.parse(readFileSync(SCENARIOS_PATH, 'utf8'))
    : null

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
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(20000)

  try {
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
      log('login', 'FAIL', 'MFA form')
      await page.screenshot({ path: path.join(OUT, 'mfa.png'), fullPage: false }).catch(() => {})
      return
    }
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 40000 }).catch(() => {})
    await dismissOverlays(page)
    if (page.url().includes('/login')) {
      log('login', 'FAIL', await page.locator('[role="alert"]').innerText().catch(() => page.url()))
      return
    }
    log('login', 'PASS', page.url())

    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.getByRole('heading', { name: /AI & Automation/i }).waitFor({ timeout: 25000 })
    const howItRuns = page.getByRole('button', { name: /How it runs/i }).first()
    if (await howItRuns.isVisible({ timeout: 3000 }).catch(() => false)) {
      await howItRuns.click().catch(() => {})
    }
    await page.getByRole('button', { name: /Preview next (run|tick)/i }).waitFor({ timeout: 25000 })
    await page.getByRole('button', { name: /Preview next (run|tick)/i }).scrollIntoViewIfNeeded()
    const overnightText = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'overnight.txt'), overnightText)
    await page.screenshot({ path: path.join(OUT, 'overnight.png'), fullPage: false })
    log('overnight.four-actions', /Draft due emails/i.test(overnightText) && /Send me my digest/i.test(overnightText) ? 'PASS' : 'FAIL')
    log('overnight.heading', /Preview, Draft, Run, and Digest stay on this card/i.test(overnightText) ? 'PASS' : 'WARN')
    await page.getByRole('button', { name: /Preview next (run|tick)/i }).click()
    const dlg = page.getByRole('alertdialog').or(page.getByRole('dialog')).first()
    const opened = await dlg.waitFor({ state: 'visible', timeout: 60000 }).then(() => true).catch(() => false)
    if (!opened) {
      log('preview.opened', 'FAIL', 'dialog did not open')
    } else {
      const ptxt = await dlg.innerText()
      writeFileSync(path.join(OUT, 'preview.txt'), ptxt)
      log('preview.this-run', /This run would send/i.test(ptxt) ? 'PASS' : 'FAIL', ptxt.slice(0, 300))
      await dlg.getByRole('button', { name: /Got it/i }).click()
      log('preview.got-it', 'PASS', 'nothing sent')
    }

    const sycamoreText = await openDealInbox(page, seed.sycamore.id, 'sycamore_inbox')
    log(
      'deal.sycamore-has-closing-question',
      /Quick question about closing|when is closing for this deal/i.test(sycamoreText) ? 'PASS' : 'FAIL',
    )
    log(
      'deal.sycamore-not-willow-document-request',
      /Could you please send me the inspection report/i.test(sycamoreText) ? 'FAIL' : 'PASS',
    )

    const willowText = await openDealInbox(page, seed.willow.id, 'willow_inbox')
    log(
      'deal.willow-has-document-request',
      /Document request|inspection report/i.test(willowText) ? 'PASS' : 'FAIL',
    )
    log(
      'deal.willow-not-sycamore-closing-body',
      /when is closing for this deal/i.test(willowText) ? 'FAIL' : 'PASS',
    )

    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.getByRole('tab', { name: /Inbox/i }).waitFor({ timeout: 25000 })
    await page.waitForTimeout(2500)
    await page.screenshot({ path: path.join(OUT, 'intelligence_inbox.png'), fullPage: false })
    const intel = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'intelligence_inbox.txt'), intel)

    const unmatched = (scenarios?.created || []).find(
      (c) => c.kind === 'matcher.james-names-unknown-street-unmatched' && c.inbound_log_id,
    )
    if (unmatched?.inbound_log_id) {
      const loc = page.locator('ul li').filter({ hasText: /Neverland Parkway/i }).first()
      const clicked = await loc.click({ timeout: 5000 }).then(() => true).catch(() => false)
      if (!clicked) {
        log('intel.unmatched.open', 'WARN', 'could not click Neverland Parkway')
      } else {
        await page.waitForTimeout(1800)
        await page.screenshot({ path: path.join(OUT, 'unmatched_pane.png'), fullPage: false })
        const pane = await page.locator('body').innerText()
        writeFileSync(path.join(OUT, 'unmatched_pane.txt'), pane)
        const send = await paneSendVisible(page)
        log('intel.unmatched.needs-a-deal', /Needs a deal/i.test(pane) ? 'PASS' : 'FAIL')
        log('intel.unmatched.no-approve-send', send ? 'FAIL' : 'PASS', send ? 'Approve & send visible' : 'hidden')
        log(
          'intel.unmatched.match-copy',
          /Match this to a deal before sending/i.test(pane) ? 'PASS' : 'FAIL',
        )
        log(
          'intel.unmatched.not-reply-ready',
          /Reply ready/i.test(pane) ? 'FAIL' : 'PASS',
        )
      }
    } else {
      log('intel.unmatched.open', 'SKIP', 'matcher unmatched row not created on this staging build')
    }

    const linkedNeedle = page.locator('ul li').filter({ hasText: /Quick question about closing/i }).first()
    if (await linkedNeedle.isVisible({ timeout: 3000 }).catch(() => false)) {
      await linkedNeedle.click()
      await page.waitForTimeout(1500)
      const pane = await page.locator('body').innerText()
      writeFileSync(path.join(OUT, 'linked_pane.txt'), pane)
      await page.screenshot({ path: path.join(OUT, 'linked_pane.png'), fullPage: false })
      log(
        'intel.linked.draft-chip',
        /Draft to review|Reply ready/i.test(pane) ? 'PASS' : 'WARN',
      )
      log(
        'intel.linked.approve-visible',
        (await paneSendVisible(page)) ? 'PASS' : 'WARN',
        'linked test-inbound may show Approve & send — do not click it',
      )
    }
  } catch (err) {
    log('script', 'FAIL', err && err.stack ? err.stack : String(err))
  } finally {
    await context.close().catch(() => {})
    await browser.close().catch(() => {})
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    const failed = findings.filter((f) => f.result === 'FAIL').length
    const warn = findings.filter((f) => f.result === 'WARN').length
    console.log(failed ? `FAILED ${failed} WARN ${warn}` : `NO FAIL CHECKS WARN ${warn}`)
    process.exit(failed ? 1 : 0)
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
