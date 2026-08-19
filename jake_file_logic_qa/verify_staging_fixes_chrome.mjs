/**
 * Staging verify for the two 18 Aug deploys:
 *  1. AI & Automation health chip must not say "stopped" while status is loading
 *  2. Closing-information email plan must not list a Closing Disclosure
 *
 *   QA_APP / QA_EMAIL / QA_PASSWORD / QA_CHANNEL / QA_OUT / QA_CLOSING_DEAL
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = process.env.QA_OUT
  ? path.resolve(process.env.QA_OUT)
  : path.join(__dirname, 'artifacts_staging_deploy_verify')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#qwe123'
const APP = (process.env.QA_APP || 'https://app.stage.velvetelves.com').replace(/\/$/, '')
const CHANNEL = process.env.QA_CHANNEL || 'chrome'
const CLOSING_DEAL =
  process.env.QA_CLOSING_DEAL || 'ee6134e7-9753-41cb-b334-770eb8d9e803'

const findings = []
const failedRequests = []
const pageErrors = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 400) : ''}`)
}

async function dismissOverlays(page) {
  const labels = [/Skip tour/i, /Skip for now/i, /^Skip$/i, /Got it/i, /Not now/i]
  for (const name of labels) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 300 }).catch(() => false)) {
      await btn.click({ timeout: 1500 }).catch(() => {})
    }
  }
  await page.keyboard.press('Escape').catch(() => {})
}

async function run() {
  const browser = await chromium.launch({
    channel: CHANNEL,
    headless: true,
    args: [
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--renderer-process-limit=1',
      '--js-flags=--max-old-space-size=192',
    ],
  })
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } })
  const page = await context.newPage()
  page.setDefaultTimeout(12000)
  page.on('pageerror', (err) => pageErrors.push(err.message))
  page.on('response', (res) => {
    if (/\/api\/v1\//.test(res.url()) && res.status() >= 400) {
      failedRequests.push(`${res.status()} ${res.url()}`)
    }
  })

  let holdStatus = true
  await page.route('**/api/v1/automation/status**', async (route) => {
    if (holdStatus) {
      await new Promise((r) => setTimeout(r, 4500))
    }
    await route.continue()
  })

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.locator('#login-email').waitFor({ state: 'visible', timeout: 15000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 25000 }).catch(() => {})
    await dismissOverlays(page)
    log('login', page.url().includes('/login') ? 'FAIL' : 'PASS', page.url())
    if (page.url().includes('/login')) return

    holdStatus = true
    const nav = page.goto(`${APP}/admin/confidence`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    })
    const chipPending = await page
      .waitForFunction(
        () => {
          const t = document.body?.innerText || ''
          return (
            /Checking automation/i.test(t) ||
            /Automation has stopped/i.test(t) ||
            /Automation active/i.test(t) ||
            /Automation is not running/i.test(t)
          )
        },
        null,
        { timeout: 8000 },
      )
      .then(async () => page.locator('body').innerText())
      .catch(() => '')
    const pendingHit = (chipPending.match(
      /Checking automation|Automation has stopped|Automation active|Automation is not running/i,
    ) || [''])[0]
    log(
      'chip.while_status_held',
      /Checking automation/i.test(chipPending)
        ? 'PASS'
        : /Automation has stopped/i.test(chipPending)
          ? 'FAIL'
          : 'WARN',
      pendingHit || chipPending.slice(0, 200),
    )
    await nav.catch(() => {})
    holdStatus = false
    await page.waitForTimeout(500)
    await page
      .waitForFunction(
        () => /Hourly automation is on|Hourly automation is off|Last draft sweep/i.test(
          document.body?.innerText || '',
        ),
        null,
        { timeout: 20000 },
      )
      .catch(() => {})
    const loaded = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'ai_automation.txt'), `${page.url()}\n\n${loaded}`)
    log(
      'chip.after_status',
      /Automation active/i.test(loaded) ? 'PASS' : 'FAIL',
      (loaded.match(/Automation active|Automation has stopped|Automation is not running|Checking automation/i) || [''])[0],
    )

    await page.goto(`${APP}/transactions/${CLOSING_DEAL}?tab=tasks`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    })
    await page.waitForTimeout(800)
    const closeChat = page.getByRole('button', { name: /Close AI chat/i })
    if (await closeChat.isVisible({ timeout: 400 }).catch(() => false)) {
      await closeChat.click().catch(() => {})
    }
    await page.keyboard.press('Escape').catch(() => {})
    await page
      .getByRole('tablist', { name: 'Workspace sections' })
      .waitFor({ state: 'visible', timeout: 20000 })
      .catch(() => {})
    const tasksTab = page.getByRole('tab', { name: /^Tasks$/i })
    if (await tasksTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await tasksTab.click().catch(() => {})
    }
    await page.waitForTimeout(800)
    const tasksTxt = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'workspace_tasks.txt'), `${page.url()}\n\n${tasksTxt}`)
    log(
      'q3.tasks.closing_info',
      /Buyer Closing Information/i.test(tasksTxt) ? 'PASS' : 'FAIL',
    )
    const actions = page.getByRole('button', {
      name: /Actions for (Buyer Closing Information|Seller's Agent Closing Information)/i,
    })
    const n = await actions.count().catch(() => 0)
    let opened = false
    for (let i = 0; i < n; i += 1) {
      await actions.nth(i).click()
      await page.waitForTimeout(200)
      const emailParty = page.getByRole('menuitem', { name: /Email transaction party/i })
      if (await emailParty.isVisible({ timeout: 1200 }).catch(() => false)) {
        await emailParty.click()
        opened = true
        break
      }
      await page.keyboard.press('Escape').catch(() => {})
    }
    if (!opened) {
      log('q3.email_plan', 'FAIL', 'could not open Email transaction party')
    } else {
      await page
        .waitForFunction(
          () =>
            /Aime can complete this for you|No .+ contact with an email|needs .+ attached/i.test(
              document.body?.innerText || '',
            ),
          null,
          { timeout: 15000 },
        )
        .catch(() => {})
      const dialog = page.getByRole('dialog', { name: 'Complete this task' })
      const planTxt = await dialog.innerText().catch(() => '')
      writeFileSync(path.join(OUT, 'closing_email_plan.txt'), `${page.url()}\n\n${planTxt}`)
      log('q3.email_plan.loaded', /Aime can complete this for you|No .+ contact/i.test(planTxt) ? 'PASS' : 'FAIL', planTxt.slice(0, 300))
      log(
        'q3.email_plan.no_cd',
        /Closing Disclosure/i.test(planTxt) ? 'FAIL' : 'PASS',
        /Closing Disclosure/i.test(planTxt) ? 'CD listed on closing-information plan' : 'no CD',
      )
      await page.getByRole('button', { name: /I'll handle it myself|^Close$/i }).first().click().catch(() => {})
    }
    log('api.4xx', failedRequests.length ? 'WARN' : 'PASS', failedRequests.slice(0, 8).join(' | '))
    log('page_errors', pageErrors.length ? 'FAIL' : 'PASS', pageErrors.slice(0, 5).join(' | '))
  } catch (err) {
    log('harness', 'FAIL', err.stack || err.message)
  } finally {
    const fail = findings.filter((f) => f.result === 'FAIL').length
    writeFileSync(
      path.join(OUT, 'findings.json'),
      JSON.stringify({ app: APP, fail, findings, failedRequests, pageErrors }, null, 2),
    )
    console.log(`\nWrote ${path.join(OUT, 'findings.json')}  FAIL=${fail}`)
    await page.close().catch(() => {})
    await context.close().catch(() => {})
    await browser.close().catch(() => {})
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
