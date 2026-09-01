/**
 * Local Chrome check for Feature 3 Overnight clocks (Audri: drop “Tick”).
 * Headless Google Chrome, one page, two viewport shots, Preview only (sends nothing).
 *
 *   QA_APP=http://127.0.0.1:5173 QA_EMAIL=... QA_PASSWORD=... node feature3_overnight_chrome_qa.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_feature3_local')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL
const PASSWORD = process.env.QA_PASSWORD
const APP = (process.env.QA_APP || 'http://127.0.0.1:5173').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
if (!EMAIL || !PASSWORD) {
  console.error('Set QA_EMAIL and QA_PASSWORD')
  process.exit(2)
}

const findings = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 500) : ''}`)
}

async function dismissOverlays(page) {
  for (const name of [/Skip tour/i, /Skip for now/i, /^Skip$/i, /Not now/i, /Got it/i, /Maybe later/i]) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 400 }).catch(() => false)) {
      await btn.click({ timeout: 1500 }).catch(() => {})
    }
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
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(15000)

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.locator('#login-email').waitFor({ state: 'visible', timeout: 20000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 30000 }).catch(() => {})
    await dismissOverlays(page)
    if (page.url().includes('/login')) {
      const alert = await page.locator('[role="alert"]').innerText().catch(() => '')
      log('login', 'FAIL', alert || page.url())
      return
    }
    log('login', 'PASS', page.url())

    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.getByRole('heading', { name: /AI & Automation/i }).waitFor({ timeout: 20000 })
    await page.getByRole('button', { name: /Preview next run/i }).waitFor({ timeout: 20000 })
    await page.getByRole('button', { name: /Preview next run/i }).scrollIntoViewIfNeeded()
    await page.screenshot({ path: path.join(OUT, 'overnight.png'), fullPage: false })

    const text = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'overnight.txt'), `${page.url()}\n\n${text}`)

    log('copy.last-run', /\bLast run\b/i.test(text) ? 'PASS' : 'FAIL')
    log('copy.preview-next-run', /Preview next run/i.test(text) ? 'PASS' : 'FAIL')
    log('copy.last-draft-sweep', /Last draft sweep/i.test(text) ? 'PASS' : 'FAIL')
    log('copy.chip-last-run', /last run /i.test(text) ? 'PASS' : 'FAIL')
    log('copy.gone-last-tick', /\bLast tick\b/i.test(text) ? 'FAIL' : 'PASS')
    log('copy.gone-preview-tick', /Preview next tick/i.test(text) ? 'FAIL' : 'PASS')

    const previewBtn = page.getByRole('button', { name: /Preview next run/i })
    await previewBtn.click()
    const dlg = page.getByRole('alertdialog').or(page.getByRole('dialog')).first()
    const opened = await dlg.waitFor({ state: 'visible', timeout: 60000 }).then(() => true).catch(() => false)
    if (!opened) {
      log('preview.dialog', 'FAIL', 'dialog did not open')
      return
    }
    const ptxt = await dlg.innerText()
    writeFileSync(path.join(OUT, 'preview.txt'), ptxt)
    await page.screenshot({ path: path.join(OUT, 'preview.png'), fullPage: false })
    log(
      'preview.title-this-run',
      /This run would send/i.test(ptxt) ? 'PASS' : 'FAIL',
      ptxt.slice(0, 300),
    )
    log('preview.gone-this-tick', /This tick would send/i.test(ptxt) ? 'FAIL' : 'PASS')
    log('preview.got-it', /Got it/i.test(ptxt) ? 'PASS' : 'FAIL')
    await dlg.getByRole('button', { name: /Got it/i }).click()
    log('preview.closed', 'PASS', 'Got it — nothing sent')
  } finally {
    await context.close().catch(() => {})
    await browser.close().catch(() => {})
    const failed = findings.filter((f) => f.result === 'FAIL').length
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    console.log(failed ? `FAILED ${failed}` : 'ALL PASS')
    process.exit(failed ? 1 : 0)
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
