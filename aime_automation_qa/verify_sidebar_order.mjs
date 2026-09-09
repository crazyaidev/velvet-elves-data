/**
 * Verify sidebar group order + TC brand lockup against Admin/Agent layout.
 *
 *   node verify_sidebar_order.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_sidebar_order')
mkdirSync(OUT, { recursive: true })

const APP = (process.env.QA_APP || 'http://127.0.0.1:5173').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'

const ACCOUNTS = [
  { id: 'admin', email: 'shyna.elene@minafter.com', expectBrand: 'Admin Console', expectCore: ['Deals', 'Workflow', 'Payments', 'Vendors'] },
  { id: 'tc', email: 'thanos.malakie@minafter.com', expectBrand: 'Transaction OS', expectCore: ['Deals', 'Workflow', 'Payments', 'Vendors'] },
  { id: 'teamlead', email: 'levi.theus@minafter.com', expectBrand: 'Team Command', expectCore: ['Deals', 'Workflow', 'Payments', 'Vendors'] },
]

const CORE = ['Deals', 'Workflow', 'Payments', 'Vendors']
const findings = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 800) : ''}`)
}

async function login(page, email) {
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.evaluate(() => {
    localStorage.clear()
    sessionStorage.clear()
  })
  await page.reload({ waitUntil: 'domcontentloaded' })
  const emailField = page.locator('#login-email, input[type="email"]').first()
  const passField = page.locator('#login-password, input[type="password"]').first()
  await emailField.waitFor({ state: 'visible', timeout: 20000 })
  await emailField.fill(email)
  await passField.fill(PASSWORD)
  await page.getByRole('button', { name: /sign in|log in/i }).click()
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 })
  await page.waitForTimeout(1500)
}

async function readChrome(page) {
  const brand = await page.evaluate(() => {
    const brandEl = document.querySelector('header a[href="/dashboard"] .uppercase, header a .tracking-\\[2px\\]')
    const all = [...document.querySelectorAll('header a div')]
    const mono = all.find((el) => /transaction os|team command|admin console|file desk|attorney/i.test(el.textContent || ''))
    return (mono?.textContent || brandEl?.textContent || '').replace(/\s+/g, ' ').trim()
  })
  const groups = await page.evaluate(() => {
    const nav = document.querySelector('nav[aria-label="Main navigation"]')
    if (!nav) return []
    return [...nav.querySelectorAll(':scope > div > div:first-child')]
      .map((el) => (el.textContent || '').trim())
      .filter((t) => t && t === t.toUpperCase() || ['Deals', 'Workflow', 'Payments', 'Vendors', 'Intelligence', 'Team', 'Oversight', 'Settings', 'Platform'].includes(t))
      .map((t) => t.replace(/\s+/g, ' '))
  })
  // The labels are uppercase via CSS; textContent stays title case from React.
  const labels = await page.locator('nav[aria-label="Main navigation"] > div > div:first-child').allTextContents()
  return { brand, groups: labels.map((s) => s.trim()).filter(Boolean) }
}

async function run() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME,
    args: ['--disable-gpu', '--disable-dev-shm-usage', '--mute-audio', '--no-first-run'],
  })

  let failed = false
  for (const account of ACCOUNTS) {
    const context = await browser.newContext({ viewport: { width: 1366, height: 768 } })
    const page = await context.newPage()
    try {
      await login(page, account.email)
      await page.screenshot({ path: path.join(OUT, `${account.id}.png`) })
      const chrome = await readChrome(page)
      const coreIdx = CORE.map((g) => chrome.groups.indexOf(g))
      const coreInOrder = coreIdx.every((n) => n >= 0) && coreIdx.every((n, i) => i === 0 || n > coreIdx[i - 1])
      const brandOk = chrome.brand.toUpperCase().includes(account.expectBrand.toUpperCase())
      log(`${account.id}_brand`, brandOk ? 'PASS' : 'FAIL', JSON.stringify({ got: chrome.brand, expect: account.expectBrand, url: page.url() }))
      log(`${account.id}_groups`, coreInOrder ? 'PASS' : 'FAIL', JSON.stringify({ groups: chrome.groups, coreIdx }))
      if (account.id === 'tc' && /file desk/i.test(chrome.brand)) {
        log('tc_file_desk_gone', 'FAIL', chrome.brand)
        failed = true
      }
      if (!brandOk || !coreInOrder) failed = true
    } catch (err) {
      log(account.id, 'FAIL', err?.stack || String(err))
      failed = true
    }
    await context.close()
  }

  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
  await browser.close()
  process.exit(failed ? 1 : 0)
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
