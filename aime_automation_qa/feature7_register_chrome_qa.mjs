/**
 * Feature 7: Register three cards — emails not letters, Manual selected.
 * Public /register only. No account creation. Headless Chrome, one page, low RAM.
 *
 *   node feature7_register_chrome_qa.mjs
 *   QA_APP=http://127.0.0.1:5173 QA_APP_STAGE=https://app.stage.velvetelves.com node feature7_register_chrome_qa.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_feature7_register')
mkdirSync(OUT, { recursive: true })

const LOCAL = (process.env.QA_APP || 'http://127.0.0.1:5173').replace(/\/$/, '')
const STAGE = (process.env.QA_APP_STAGE || 'https://app.stage.velvetelves.com').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

const EXPECTED = {
  manual: 'AI suggests. You click to apply anything.',
  assisted: 'Routine work runs. Named emails are drafted — you tap Send.',
  autopilot: 'Authorized emails send when confidence is high enough. No tap.',
}

const findings = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 800) : ''}`)
}

async function checkRegister(page, label, origin) {
  await page.goto(`${origin}/register`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  const legend = page.getByText('How should Aime start?', { exact: true })
  await legend.waitFor({ state: 'visible', timeout: 20000 })
  await legend.scrollIntoViewIfNeeded()

  const fieldset = page.locator('fieldset').filter({ hasText: 'How should Aime start?' }).first()
  const text = (await fieldset.innerText()).replace(/\s+/g, ' ')
  writeFileSync(path.join(OUT, `${label}.txt`), text)
  await fieldset.screenshot({ path: path.join(OUT, `${label}.png`) })

  const manual = page.getByRole('button', { name: /Manual/i }).first()
  const pressed = await manual.getAttribute('aria-pressed')

  const missing = Object.values(EXPECTED).filter((line) => !text.includes(line))
  const hasNamedLetters = /named letters/i.test(text)
  const hasAuthorizedLetters = /authorized letters/i.test(text)
  const hasLibraryLetters = /library letters/i.test(text)
  const hasNamedEmails = /named emails/i.test(text)
  const hasAuthorizedEmails = /authorized emails/i.test(text)

  if (missing.length || hasNamedLetters || hasAuthorizedLetters || hasLibraryLetters || pressed !== 'true') {
    log(
      label,
      'FAIL',
      JSON.stringify({
        missing,
        hasNamedLetters,
        hasAuthorizedLetters,
        hasLibraryLetters,
        hasNamedEmails,
        hasAuthorizedEmails,
        pressed,
        text: text.slice(0, 1200),
      }),
    )
    return
  }

  log(
    label,
    'PASS',
    JSON.stringify({ hasNamedEmails, hasAuthorizedEmails, pressed, origin, url: page.url() }),
  )
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
    viewport: { width: 1280, height: 900 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(20000)

  try {
    await checkRegister(page, 'local', LOCAL)
    await checkRegister(page, 'staging', STAGE)
  } catch (err) {
    log('script', 'FAIL', err?.stack || err?.message || err)
    await page.screenshot({ path: path.join(OUT, 'crash.png'), fullPage: false }).catch(() => {})
  } finally {
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    await browser.close()
  }

  const failed = findings.some((f) => f.result === 'FAIL')
  process.exit(failed ? 1 : 0)
}

run()
