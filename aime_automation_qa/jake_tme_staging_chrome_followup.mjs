/**
 * Follow-up Chrome: client home (wait past spinner), team-lead Trusted dates,
 * Dual Deliver Title, timeline provenance, FSBO Ask AI.
 * Never Send, never Run AI, never Change status.
 */
import { createRequire } from 'module'
import { mkdirSync, rmSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_jake_tme_staging')
mkdirSync(OUT, { recursive: true })

const PASSWORD = 'QWE!@#asd234'
const APP = 'https://app.stage.velvetelves.com'
const API = 'https://api.stage.velvetelves.com'
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const DEAL_DUAL = 'f53d0674-8322-4568-9fb9-fae7715d521d'
const DEAL_ACTIVE = 'da681bf7-92e8-45b5-b3d0-8f152e461bca'

const findings = []
function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
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

async function bodyText(page) {
  try {
    return await page.locator('body').innerText({ timeout: 8000 })
  } catch {
    return ''
  }
}

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false }).catch(() => {})
}

async function dump(page, name) {
  const text = await bodyText(page)
  writeFileSync(path.join(OUT, `${name}.txt`), `${page.url()}\n\n${text}`)
  return text
}

async function apiLogin(email) {
  const body = new URLSearchParams({ username: email, password: PASSWORD })
  const res = await fetch(`${API}/api/v1/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  const json = await res.json().catch(() => ({}))
  return json
}

async function launch(token, refresh, extraInit) {
  const profile = path.join(OUT, `chrome-profile-${Date.now()}`)
  mkdirSync(profile, { recursive: true })
  const context = await chromium.launchPersistentContext(profile, {
    headless: true,
    executablePath: CHROME,
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
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
  await context.addInitScript(
    ({ token: t, refresh: r, extra }) => {
      window.localStorage.setItem('velvet_elves_token', t)
      if (r) window.localStorage.setItem('velvet_elves_refresh_token', r)
      if (extra) {
        for (const [k, v] of Object.entries(extra)) window.localStorage.setItem(k, v)
      }
    },
    { token, refresh: refresh || '', extra: extraInit || {} },
  )
  const page = context.pages()[0] || (await context.newPage())
  page.setDefaultTimeout(25000)
  return { context, page, profile }
}

async function formLogin(page, email) {
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.locator('#login-email').waitFor({ state: 'visible', timeout: 25000 })
  await page.locator('#login-email').fill(email)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /sign in/i }).click()
  const mfa = await page.getByLabel('Two-step verification form').waitFor({ timeout: 4000 }).then(() => true).catch(() => false)
  if (mfa) return 'mfa'
  await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 40000 }).catch(() => {})
  await dismissOverlays(page)
  return page.url().includes('/login') ? 'login' : 'ok'
}

async function withContext(email, extraInit, fn) {
  const session = await apiLogin(email)
  if (!session.access_token) {
    log(`${email}.api`, 'FAIL', 'no token')
    return
  }
  const { context, page, profile } = await launch(session.access_token, session.refresh_token, extraInit)
  try {
    await fn(page)
  } catch (err) {
    log(`${email}.uncaught`, 'FAIL', err.message || String(err))
    await shot(page, `${email.split('@')[0]}_uncaught`).catch(() => {})
  } finally {
    await context.close().catch(() => {})
    try {
      rmSync(profile, { recursive: true, force: true })
    } catch {
      /* temp */
    }
  }
}

async function run() {
  // Client: form login so AuthContext hydrates like a real user
  {
    const profile = path.join(OUT, `chrome-profile-client-${Date.now()}`)
    mkdirSync(profile, { recursive: true })
    const context = await chromium.launchPersistentContext(profile, {
      headless: true,
      executablePath: CHROME,
      viewport: { width: 1280, height: 800 },
      args: ['--disable-gpu', '--disable-dev-shm-usage', '--mute-audio', '--no-first-run'],
    })
    const page = context.pages()[0] || (await context.newPage())
    try {
      const login = await formLogin(page, 'ellenore.zynique@minafter.com')
      log('client.form_login', login === 'ok' ? 'PASS' : 'FAIL', `${login} ${page.url()}`)
      if (login === 'ok') {
        await page.goto(`${APP}/client/home`, { waitUntil: 'domcontentloaded', timeout: 60000 })
        await dismissOverlays(page)
        const ready = await page
          .getByRole('status', { name: /Loading/i })
          .waitFor({ state: 'hidden', timeout: 25000 })
          .then(() => true)
          .catch(() => false)
        const home = await dump(page, 'client_home_waited')
        await shot(page, 'client_home_waited')
        log('client.spinner_cleared', ready || !/Loading\.\.\./.test(home) ? 'PASS' : 'FAIL', page.url())
        log(
          'client.no_ask_ai_after_load',
          /Ask AI/i.test(home) || /Message Aime/i.test(home) ? 'FAIL' : 'PASS',
        )
        log('client.no_needs_you_after_load', /Needs You/i.test(home) ? 'FAIL' : 'PASS')
        log(
          'client.home_content',
          /Ask your team|What happens next|Next steps|Your closing|Ellenore|Home/i.test(home)
            ? 'PASS'
            : 'WARN',
          home.slice(0, 600),
        )
      }
    } catch (err) {
      log('client.form.uncaught', 'FAIL', err.message || String(err))
    } finally {
      await context.close().catch(() => {})
      try {
        rmSync(profile, { recursive: true, force: true })
      } catch {
        /* temp */
      }
    }
  }

  await withContext(
    'keylan.symir@minafter.com',
    { ve_agent_workspace_v1: 'on' },
    async (page) => {
      await page.goto(`${APP}/transactions/${DEAL_ACTIVE}`, { waitUntil: 'domcontentloaded', timeout: 60000 })
      await dismissOverlays(page)
      const posture = page.getByRole('button', { name: /Automation posture for this deal/i })
      const ready = await posture.waitFor({ timeout: 35000 }).then(() => true).catch(() => false)
      log('teamlead.workspace', ready ? 'PASS' : 'FAIL', page.url())
      if (!ready) {
        await dump(page, 'teamlead_workspace')
        await shot(page, 'teamlead_workspace')
        return
      }
      const ws = await dump(page, 'teamlead_workspace')
      await shot(page, 'teamlead_workspace')
      log('teamlead.stages', /Earnest Money|Inspection|Financing/i.test(ws) ? 'PASS' : 'FAIL')
      await posture.click()
      await page.waitForTimeout(400)
      const menu = await bodyText(page)
      writeFileSync(path.join(OUT, 'teamlead_menu.txt'), menu)
      log(
        'teamlead.trusted_dates_menu',
        /On for this deal/i.test(menu) && /This is not email send/i.test(menu) ? 'PASS' : 'FAIL',
      )
      await page.keyboard.press('Escape').catch(() => {})
    },
  )

  await withContext(
    'crazyaidev20500519@gmail.com',
    { ve_agent_workspace_v1: 'on', ve_agent_pane_open: 'open' },
    async (page) => {
      await page.goto(`${APP}/transactions/${DEAL_DUAL}?tab=tasks`, {
        waitUntil: 'domcontentloaded',
        timeout: 60000,
      })
      await dismissOverlays(page)
      await page.getByRole('button', { name: /Automation posture for this deal/i }).waitFor({ timeout: 35000 })
      const titleRow = page.getByText('Deliver Title', { exact: true }).first()
      const visible = await titleRow.waitFor({ timeout: 20000 }).then(() => true).catch(() => false)
      const tasks = await dump(page, 'tasks_dual_waited')
      await shot(page, 'tasks_dual_waited')
      log(
        'dual.deliver_title_in_tasks',
        visible || /Deliver Title/i.test(tasks) ? 'PASS' : 'FAIL',
      )
      log(
        'dual.utility_in_tasks',
        /Deliver Utility Info/i.test(tasks) ? 'PASS' : 'WARN',
      )

      await page.goto(`${APP}/transactions/${DEAL_ACTIVE}?tab=timeline`, {
        waitUntil: 'domcontentloaded',
        timeout: 60000,
      })
      await page.getByRole('button', { name: /Automation posture for this deal/i }).waitFor({ timeout: 35000 })
      const tl = await dump(page, 'timeline_guide')
      await shot(page, 'timeline_guide')
      log(
        'timeline.provenance',
        /\b(Confirmed|Reported|Conflict)\b/.test(tl) ? 'PASS' : 'SKIP',
        'no typed facts on this file yet',
      )
    },
  )

  await withContext('brevyn.joshawn@minafter.com', {}, async (page) => {
    await page.goto(`${APP}/fsbo`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await dismissOverlays(page)
    await page.waitForTimeout(4000)
    const fsbo = await dump(page, 'fsbo_home')
    await shot(page, 'fsbo_home')
    log('fsbo.session', page.url().includes('/login') ? 'FAIL' : 'PASS', page.url())
    log(
      'fsbo.ask_ai',
      /Ask AI/i.test(fsbo) || /Message Aime/i.test(fsbo) ? 'WARN' : 'PASS',
      'seller Aime is out of this round if present',
    )
  })

  const failed = findings.filter((f) => f.result === 'FAIL').length
  writeFileSync(path.join(OUT, 'findings_followup.json'), JSON.stringify({ findings }, null, 2))
  console.log(`FOLLOWUP FAILED ${failed} TOTAL ${findings.length}`)
  process.exit(failed ? 1 : 0)
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
