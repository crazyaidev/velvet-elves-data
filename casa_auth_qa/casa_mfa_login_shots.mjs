/**
 * Low-RAM headless Chrome screenshots for CASA 3.3.1.
 * This account already has a verified TOTP, so we can only reach the
 * login page and the post-password code prompt without a live authenticator.
 *
 *   $env:QA_PASSWORD='…'; node casa_mfa_login_shots.mjs
 */
import { createRequire } from 'module'
import { mkdirSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD
if (!PASSWORD) {
  console.error('Set QA_PASSWORD')
  process.exit(2)
}

const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const OUT = path.join(
  __dirname,
  '..',
  'casa_al1_evidence',
  'm9',
  'tac_images',
  '3.3.1',
)
mkdirSync(OUT, { recursive: true })

const TARGETS = [
  { id: 'stage', app: 'https://app.stage.velvetelves.com' },
  { id: 'prod', app: 'https://app.velvetelves.com' },
]

async function shot(page, name) {
  const file = path.join(OUT, name)
  await page.screenshot({ path: file, fullPage: false })
  console.log('wrote', file)
}

async function capture(id, app) {
  const browser = await chromium.launch({
    executablePath: CHROME,
    headless: true,
    args: [
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--disable-extensions',
      '--disable-background-networking',
      '--no-first-run',
      '--no-default-browser-check',
    ],
  })
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
  try {
    await page.goto(`${app}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.getByLabel(/email address/i).waitFor({ timeout: 20000 })
    await shot(page, `CASA_3_3_1_${id}_login.png`)

    await page.getByLabel(/email address/i).fill(EMAIL)
    await page.getByLabel(/^password$/i).fill(PASSWORD)
    await page.getByRole('button', { name: /^sign in$/i }).click()

    await page.getByRole('heading', { name: /two-step verification/i }).waitFor({ timeout: 25000 })
    await shot(page, `CASA_3_3_1_${id}_mfa_prompt.png`)
    console.log(`[PASS] ${id} reached MFA prompt`)
  } finally {
    await browser.close()
  }
}

for (const t of TARGETS) {
  await capture(t.id, t.app)
}
