import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')
const OUT = path.join(__dirname, 'artifacts_feature4_staging')
mkdirSync(OUT, { recursive: true })
const EMAIL = process.env.QA_EMAIL
const PASSWORD = process.env.QA_PASSWORD
const APP = 'https://app.stage.velvetelves.com'
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

;(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME,
    args: ['--disable-gpu', '--disable-dev-shm-usage', '--disable-extensions', '--mute-audio', '--renderer-process-limit=1'],
  })
  const page = await (await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' })).newPage()
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.locator('#login-email').fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 40000 })
  await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.getByRole('tab', { name: /Inbox/i }).waitFor({ timeout: 25000 })
  await page.waitForTimeout(2000)

  await page.getByText('James Selman').first().click()
  await page.waitForTimeout(2000)
  await page.screenshot({ path: path.join(OUT, 'james_pane.png'), fullPage: false })
  writeFileSync(path.join(OUT, 'james_pane.txt'), await page.locator('body').innerText())

  const send1 = await page.getByRole('button', { name: /^(Send|Approve & send|Send reply)$/i }).first().isVisible().catch(() => false)
  console.log('james_send', send1)

  await page.getByText('Confirming title order for 1842 Willowbrook').first().click()
  await page.waitForTimeout(2000)
  await page.screenshot({ path: path.join(OUT, 'self_pane.png'), fullPage: false })
  writeFileSync(path.join(OUT, 'self_pane.txt'), await page.locator('body').innerText())
  const send2 = await page.getByRole('button', { name: /^(Send|Approve & send|Send reply)$/i }).first().isVisible().catch(() => false)
  console.log('self_send', send2)

  await browser.close()
})().catch((e) => { console.error(e); process.exit(1) })
