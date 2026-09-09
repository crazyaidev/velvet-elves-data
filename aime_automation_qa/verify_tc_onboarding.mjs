/**
 * Reproduce TC onboarding complete with a stale ve_active_workspace left over
 * from another account (common during QA). Verifies login clears the header.
 *
 *   node verify_tc_onboarding.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, readFileSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_tc_onboarding')
mkdirSync(OUT, { recursive: true })

const APP = (process.env.QA_APP || 'http://127.0.0.1:5173').replace(/\/$/, '')
const API = (process.env.QA_API || 'http://127.0.0.1:8000').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const BACKEND_ENV = process.env.QA_BACKEND_ENV || 'C:\\Projects\\velvet-elves-backend\\.env'
const EMAIL = process.env.QA_TC_EMAIL || 'thanos.malakie@minafter.com'
const PASSWORD = process.env.QA_TC_PASSWORD || 'QWE!@#asd234'
const STALE_WORKSPACE = process.env.QA_STALE_WORKSPACE || '2b339640-31a7-4005-bef8-5a5f7ba2d205'

const findings = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 800) : ''}`)
}

function loadDotEnv(filePath) {
  const out = {}
  try {
    for (const line of readFileSync(filePath, 'utf8').split(/\r?\n/)) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) continue
      const i = trimmed.indexOf('=')
      out[trimmed.slice(0, i).trim()] = trimmed.slice(i + 1).trim().replace(/^["']|["']$/g, '')
    }
  } catch {
    /* optional */
  }
  return out
}

async function apiForm(pathname, body) {
  const res = await fetch(`${API}${pathname}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams(body).toString(),
  })
  const text = await res.text()
  let json = null
  try {
    json = JSON.parse(text)
  } catch {
    json = { raw: text }
  }
  return { status: res.status, json }
}

async function resetOnboarding(userId) {
  const env = loadDotEnv(BACKEND_ENV)
  const url = env.SUPABASE_URL
  const key = env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !key) {
    log('reset_onboarding', 'SKIP', 'No SUPABASE_URL / SERVICE_ROLE in backend .env')
    return false
  }
  const res = await fetch(`${url}/rest/v1/users?id=eq.${userId}`, {
    method: 'PATCH',
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
      Prefer: 'return=minimal',
    },
    body: JSON.stringify({ onboarding_completed: false }),
  })
  if (!res.ok) {
    log('reset_onboarding', 'FAIL', `${res.status} ${await res.text()}`)
    return false
  }
  log('reset_onboarding', 'PASS', userId)
  return true
}

async function reachCompleteStep(page) {
  await page.getByRole('button', { name: /Let's go/i }).click()
  for (let i = 0; i < 8; i += 1) {
    if (await page.getByRole('button', { name: /Go straight to your dashboard/i }).isVisible().catch(() => false)) {
      return
    }
    const skip = page.getByRole('button', { name: /Skip for now/i })
    if (await skip.isVisible().catch(() => false)) {
      await skip.click()
      continue
    }
    const cont = page.getByRole('button', { name: /^Continue$/i })
    if (await cont.isVisible().catch(() => false)) {
      await cont.click()
      await page.waitForTimeout(600)
      continue
    }
    break
  }
  await page.getByRole('button', { name: /Go straight to your dashboard/i }).waitFor({
    state: 'visible',
    timeout: 30000,
  })
}

async function run() {
  const login = await apiForm('/api/v1/users/login', { username: EMAIL, password: PASSWORD })
  if (login.status !== 200 || !login.json?.user?.id) {
    log('api_login', 'FAIL', JSON.stringify(login))
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    process.exit(1)
  }
  const userId = login.json.user.id
  const tenantId = login.json.user.tenant_id
  log('api_login', 'PASS', `${EMAIL} tenant=${tenantId} onboarding=${login.json.user.onboarding_completed}`)

  await resetOnboarding(userId)

  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME,
    args: ['--disable-gpu', '--disable-dev-shm-usage', '--mute-audio', '--no-first-run'],
  })
  const context = await browser.newContext({ viewport: { width: 1366, height: 768 } })
  const page = await context.newPage()

  const completeResponses = []
  page.on('response', async (response) => {
    if (response.url().includes('/api/v1/onboarding/complete')) {
      completeResponses.push({
        status: response.status(),
        body: await response.text().catch(() => ''),
      })
    }
  })

  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.evaluate((stale) => {
    localStorage.setItem('ve_active_workspace', stale)
  }, STALE_WORKSPACE)

  await page.getByLabel(/email/i).fill(EMAIL)
  await page.getByLabel(/^password$/i).fill(PASSWORD)
  await page.getByRole('button', { name: /sign in|log in/i }).click()

  await page.waitForURL(/\/onboarding/, { timeout: 45000 })
  const activeAfterLogin = await page.evaluate(() => localStorage.getItem('ve_active_workspace'))
  log('workspace_after_login', activeAfterLogin ? 'FAIL' : 'PASS', `active=${activeAfterLogin}`)

  await reachCompleteStep(page)
  await page.screenshot({ path: path.join(OUT, '01_complete_step.png') })

  await page.getByRole('button', { name: /Go straight to your dashboard/i }).click()
  await page.waitForURL(/\/dashboard/, { timeout: 45000 }).catch(() => null)
  await page.screenshot({ path: path.join(OUT, '02_after_dashboard.png') })

  const onDashboard = /\/dashboard/.test(page.url())
  const completeOk = completeResponses.some((r) => r.status === 200)
  const toastText = await page.locator('[role="alert"]').allTextContents().catch(() => [])

  log(
    'onboarding_complete_api',
    completeOk ? 'PASS' : 'FAIL',
    JSON.stringify(completeResponses),
  )
  log('dashboard_navigation', onDashboard ? 'PASS' : 'FAIL', page.url())
  if (toastText.length) log('toasts', 'INFO', toastText.join(' | '))

  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
  await browser.close()
  process.exit(onDashboard && completeOk && !activeAfterLogin ? 0 : 1)
}

run().catch((err) => {
  log('runner', 'FAIL', err?.stack || String(err))
  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
  process.exit(1)
})
