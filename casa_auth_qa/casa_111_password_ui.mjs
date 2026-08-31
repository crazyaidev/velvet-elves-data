/**
 * Headless shot of the public register password rules (CASA 1.1.1 option 2.4 UI).
 */
import { createRequire } from 'module'
import { mkdirSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const OUT = path.join(__dirname, '..', 'casa_al1_evidence', 'm9', 'tac_images', '1.1.1')
mkdirSync(OUT, { recursive: true })

const browser = await chromium.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--disable-gpu', '--disable-dev-shm-usage', '--no-first-run'],
})
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
try {
  await page.goto('https://app.stage.velvetelves.com/register', {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  })
  const password = page.locator('#reg-password')
  await password.waitFor({ timeout: 20000 })
  await password.fill('pass')
  const rules = page.getByText(/at least 8 characters/i)
  await rules.waitFor({ timeout: 10000 })
  await rules.scrollIntoViewIfNeeded()
  const block = page.locator('#reg-password').locator('xpath=ancestor::div[contains(@class,"space-y")][1]')
  await block.screenshot({
    path: path.join(OUT, 'CASA_1_1_1_password_rules.png'),
  })
  console.log('wrote password rules shot')
} finally {
  await browser.close()
}
