/**
 * Local Chrome QA for role-identity independent workspaces.
 * One headless Chrome, one renderer, small viewport. Does not send mail.
 *
 *   $env:QA_APP='http://127.0.0.1:5173'
 *   $env:QA_API='http://127.0.0.1:8000'
 *   node identity_workspace_local_chrome.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_identity_workspace_local')
mkdirSync(OUT, { recursive: true })

const ADMIN_EMAIL = process.env.QA_EMAIL || 'shyna.elene@minafter.com'
const ADMIN_PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const APP = (process.env.QA_APP || 'http://127.0.0.1:5173').replace(/\/$/, '')
const API = (process.env.QA_API || 'http://127.0.0.1:8000').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const BACKEND_ENV = process.env.QA_BACKEND_ENV || 'C:\\Projects\\velvet-elves-backend\\.env'
const STAMP = Date.now()
const PASSWORD = process.env.QA_FOUNDER_PASSWORD || 'IdentityQA1!'
const WORKSPACE_WAIT_MS = 60000
const SKIP_REGISTER = process.env.QA_SKIP_REGISTER === '1'
const ONLY_UI = new Set(
  (process.env.QA_ONLY_UI || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean),
)
const REUSE_EMAIL = {
  Agent: process.env.QA_AGENT_EMAIL || '',
  TransactionCoordinator: process.env.QA_TC_EMAIL || '',
  TeamLead: process.env.QA_TL_EMAIL || '',
}

function wantUi(role) {
  return ONLY_UI.size === 0 || ONLY_UI.has(role)
}

const findings = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 2500) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 600) : ''}`)
}

function loadDotEnv(filePath) {
  const out = {}
  let text = ''
  try {
    text = readFileSync(filePath, 'utf8')
  } catch {
    return out
  }
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) continue
    const i = trimmed.indexOf('=')
    let value = trimmed.slice(i + 1).trim()
    if (
      value.length >= 2 &&
      ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'")))
    ) {
      value = value.slice(1, -1)
    }
    out[trimmed.slice(0, i).trim()] = value
  }
  return out
}

async function apiJson(pathAndQuery, { method = 'GET', token, json, form } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  let body
  if (form) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    body = form
  } else if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(json)
  }
  const res = await fetch(`${API}${pathAndQuery}`, { method, headers, body })
  const data = await res.json().catch(() => ({}))
  return { status: res.status, data }
}

async function login(email, password) {
  const form = new URLSearchParams({ username: email, password })
  return apiJson('/api/v1/users/login', { method: 'POST', form })
}

async function completeOnboarding(token) {
  return apiJson('/api/v1/onboarding/complete', { method: 'POST', token })
}

function gotrueHeaders(env) {
  const key = env.SUPABASE_SERVICE_ROLE_KEY || ''
  return {
    apikey: key,
    Authorization: `Bearer ${key}`,
    Accept: 'application/json',
    'Content-Type': 'application/json',
  }
}

async function findAuthUserId(env, email) {
  const base = String(env.SUPABASE_URL || '').replace(/\/$/, '')
  if (!base || !env.SUPABASE_SERVICE_ROLE_KEY) return null
  const target = email.toLowerCase()
  for (let page = 1; page <= 12; page += 1) {
    const res = await fetch(`${base}/auth/v1/admin/users?page=${page}&per_page=50`, {
      headers: gotrueHeaders(env),
    })
    if (!res.ok) return null
    const data = await res.json().catch(() => ({}))
    const users = Array.isArray(data.users) ? data.users : []
    const hit = users.find((u) => String(u.email || '').toLowerCase() === target)
    if (hit?.id) return hit.id
    if (users.length < 50) break
  }
  return null
}

async function confirmEmail(env, email) {
  const base = String(env.SUPABASE_URL || '').replace(/\/$/, '')
  const userId = await findAuthUserId(env, email)
  if (!base || !userId) {
    return { ok: false, status: 0, userId: null }
  }
  const res = await fetch(`${base}/auth/v1/admin/users/${userId}`, {
    method: 'PUT',
    headers: gotrueHeaders(env),
    body: JSON.stringify({ email_confirm: true }),
  })
  const data = await res.json().catch(() => ({}))
  const confirmed = Boolean(data.email_confirmed_at)
  return { ok: res.ok && confirmed, status: res.status, userId }
}

async function registerFounder(env, role, label) {
  const email = `idqa.${role.toLowerCase()}.${STAMP}@example.com`
  const created = await apiJson('/api/v1/users/register', {
    method: 'POST',
    json: {
      email,
      password: PASSWORD,
      full_name: `${label} QA ${STAMP}`,
      organization_name: `${label} QA Org`,
      role,
    },
  })
  let session = created.data || {}
  if (created.status === 202) {
    const confirmed = await confirmEmail(env, email)
    if (!confirmed.ok) {
      return {
        email,
        status: created.status,
        confirm: confirmed,
        session: null,
        detail: created.data.detail || created.data.message,
      }
    }
    const logged = await login(email, PASSWORD)
    session = logged.data || {}
    return {
      email,
      status: logged.status === 200 && session.access_token ? 201 : created.status,
      confirm: confirmed,
      session,
      registerStatus: created.status,
      loginStatus: logged.status,
    }
  }
  return { email, status: created.status, confirm: { ok: true, skipped: true }, session, registerStatus: created.status }
}

async function dismissOverlays(page) {
  for (const name of [/Skip tour/i, /Skip for now/i, /^Skip$/i, /Not now/i, /Got it/i, /Maybe later/i, /Close/i]) {
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

async function dump(page, name) {
  const text = await bodyText(page)
  writeFileSync(path.join(OUT, `${name}.txt`), `${page.url()}\n\n${text}`)
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false }).catch(() => {})
  return text
}

async function waitWorkspace(page) {
  const deadline = Date.now() + WORKSPACE_WAIT_MS
  while (Date.now() < deadline) {
    const href = page.url()
    if (/\/login(\?|$)/.test(href)) return false
    const ready = await page
      .getByRole('link', { name: /^Dashboard$/i })
      .first()
      .isVisible()
      .catch(() => false)
    if (ready) {
      await dismissOverlays(page)
      return true
    }
    await page.waitForTimeout(500)
  }
  return !/\/login(\?|$)/.test(page.url())
}

async function loadSession(page, session) {
  await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.evaluate(
    ({ token, refresh }) => {
      window.localStorage.clear()
      window.localStorage.setItem('velvet_elves_token', token)
      if (refresh) window.localStorage.setItem('velvet_elves_refresh_token', refresh)
    },
    { token: session.access_token, refresh: session.refresh_token || '' },
  )
  await page.goto(`${APP}/dashboard`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  const ok = await waitWorkspace(page)
  await dismissOverlays(page)
  return ok
}

async function dropDom(page) {
  await page.goto('about:blank', { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {})
}

async function go(page, pathAndQuery, dumpName, { waitDash = false, marker } = {}) {
  await page.goto(`${APP}${pathAndQuery}`, { waitUntil: 'domcontentloaded', timeout: 60000 })
  if (waitDash) await waitWorkspace(page)
  if (marker) {
    await page
      .getByText(marker, { exact: false })
      .first()
      .waitFor({ timeout: 30000 })
      .catch(() => {})
  }
  await dismissOverlays(page)
  return dump(page, dumpName)
}

function hasNav(text, label) {
  const re = new RegExp(`\\b${label}\\b`, 'i')
  return re.test(text)
}

async function run() {
  const env = loadDotEnv(BACKEND_ENV)
  log(
    'env.supabase',
    env.SUPABASE_URL && env.SUPABASE_SERVICE_ROLE_KEY ? 'PASS' : 'FAIL',
    env.SUPABASE_URL && env.SUPABASE_SERVICE_ROLE_KEY ? 'service role loaded' : 'missing SUPABASE_URL or service role',
  )

  const health = await fetch(`${API}/api/v1/health`).catch(() => null)
  log('api.up', health && health.ok ? 'PASS' : 'FAIL', health ? `http ${health.status}` : 'unreachable')
  const appUp = await fetch(APP).catch(() => null)
  log('app.up', appUp && appUp.ok ? 'PASS' : 'FAIL', appUp ? `http ${appUp.status}` : 'unreachable')
  if (!health?.ok || !appUp?.ok) process.exit(1)

  const sessions = {}

  for (const [role, label] of [
    ['Agent', 'Agent'],
    ['TransactionCoordinator', 'Coordinator'],
    ['TeamLead', 'TeamLead'],
  ]) {
    if (SKIP_REGISTER) {
      if (!REUSE_EMAIL[role]) continue
      const logged = await login(REUSE_EMAIL[role], PASSWORD)
      const user = logged.data.user || {}
      const token = logged.data.access_token
      log(
        `api.register.${role}`,
        logged.status === 200 && user.role === role && user.is_tenant_owner && token && !logged.data.mfa_required
          ? 'PASS'
          : 'FAIL',
        JSON.stringify({
          reused: true,
          http: logged.status,
          role: user.role,
          owner: user.is_tenant_owner,
          team_id: user.team_id,
          email: REUSE_EMAIL[role],
          mfa: logged.data.mfa_required,
        }),
      )
      if (!token || logged.data.mfa_required) continue
      const done = await completeOnboarding(token)
      log(
        `api.onboarding.${role}`,
        done.status === 200 && done.data.onboarding_completed ? 'PASS' : 'FAIL',
        `http=${done.status}`,
      )
      sessions[role] = {
        access_token: token,
        refresh_token: logged.data.refresh_token,
        user,
        email: REUSE_EMAIL[role],
      }
      continue
    }
    const created = await registerFounder(env, role, label)
    const user = created.session?.user || {}
    const token = created.session?.access_token
    log(
      `api.register.${role}`,
      created.status === 201 && user.role === role && user.is_tenant_owner && token ? 'PASS' : 'FAIL',
      JSON.stringify({
        http: created.status,
        register: created.registerStatus,
        login: created.loginStatus,
        confirm: created.confirm?.ok,
        role: user.role,
        owner: user.is_tenant_owner,
        team_id: user.team_id,
        email: created.email,
        message: created.detail || created.session?.detail,
      }),
    )
    if (!token) continue
    if (created.session.mfa_required) {
      log(`api.login.mfa.${role}`, 'FAIL', 'mfa_required on new founder')
      continue
    }
    const done = await completeOnboarding(token)
    log(
      `api.onboarding.${role}`,
      done.status === 200 && done.data.onboarding_completed ? 'PASS' : 'FAIL',
      `http=${done.status}`,
    )
    const me = await apiJson('/api/v1/users/me', { token })
    sessions[role] = {
      access_token: token,
      refresh_token: created.session.refresh_token,
      user: me.status === 200 ? me.data : user,
      email: created.email,
    }
  }

  if (sessions.TeamLead) {
    log(
      'api.teamlead.team_minted',
      sessions.TeamLead.user.team_id ? 'PASS' : 'FAIL',
      `team_id=${sessions.TeamLead.user.team_id}`,
    )
  }

  if (sessions.Agent) {
    const conf = await apiJson('/api/v1/confidence/tenant', {
      method: 'PUT',
      token: sessions.Agent.access_token,
      json: { global_min_floor: 0.8 },
    })
    log(
      'api.agent_owner.admin_identity_403',
      conf.status === 403 ? 'PASS' : 'FAIL',
      `confidence PUT http=${conf.status} ${JSON.stringify(conf.data).slice(0, 240)}`,
    )
  }

  const adminLogin = await login(ADMIN_EMAIL, ADMIN_PASSWORD)
  const adminUser = adminLogin.data.user || {}
  log(
    'api.login.existing_admin',
    adminLogin.status === 200 && adminUser.role === 'Admin' && !adminLogin.data.mfa_required
      ? 'PASS'
      : 'FAIL',
    JSON.stringify({
      http: adminLogin.status,
      role: adminUser.role,
      owner: adminUser.is_tenant_owner,
      mfa: adminLogin.data.mfa_required,
    }),
  )
  if (adminLogin.status === 200 && adminLogin.data.access_token && !adminLogin.data.mfa_required) {
    sessions.Admin = {
      access_token: adminLogin.data.access_token,
      refresh_token: adminLogin.data.refresh_token,
      user: adminUser,
      email: ADMIN_EMAIL,
    }
  }

  const profile = path.join(OUT, `chrome-${STAMP}`)
  mkdirSync(profile, { recursive: true })
  const context = await chromium.launchPersistentContext(profile, {
    headless: true,
    executablePath: CHROME,
    viewport: { width: 1100, height: 700 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
    args: [
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--mute-audio',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-extensions',
      '--disable-background-networking',
      '--disable-sync',
      '--disable-component-update',
      '--renderer-process-limit=1',
      '--js-flags=--max-old-space-size=192',
    ],
  })
  const page = context.pages()[0] || (await context.newPage())
  page.setDefaultTimeout(20000)
  page.on('pageerror', (err) => log('pageerror', 'FAIL', err.message || String(err)))

  try {
    const regText = await go(page, '/register', 'register')
    const hasRoles =
      /Agent/i.test(regText) &&
      /Team Leader/i.test(regText) &&
      /Transaction Coordinator/i.test(regText) &&
      /\bAdmin\b/i.test(regText)
    log('ui.register.four_identities', hasRoles ? 'PASS' : 'FAIL', page.url())

    if (sessions.Agent && wantUi('Agent')) {
      const injected = await loadSession(page, sessions.Agent)
      const dash = await dump(page, 'agent_dashboard')
      log(
        'ui.agent.landing',
        injected && page.url().includes('/dashboard/agent') ? 'PASS' : 'FAIL',
        page.url(),
      )
      log(
        'ui.agent.no_oversight',
        !/Audit Log/i.test(dash) && !/\bOversight\b/i.test(dash) ? 'PASS' : 'FAIL',
        'sidebar should not show Admin Oversight',
      )
      log(
        'ui.agent.owner_strip',
        /Change my role/i.test(dash) && /Users & Invites/i.test(dash) ? 'PASS' : 'FAIL',
        'owner strip on sidebar',
      )

      const settings = await go(page, '/settings', 'agent_settings', {
        waitDash: true,
        marker: 'My automation',
      })
      log('ui.agent.settings.my_automation', /My automation/i.test(settings) ? 'PASS' : 'FAIL')
      log(
        'ui.agent.settings.no_ai_governance',
        !/AI & Automation/i.test(settings) ? 'PASS' : 'FAIL',
      )
      log('ui.agent.settings.change_role', /Change my role/i.test(settings) ? 'PASS' : 'FAIL')

      await go(page, '/admin/confidence', 'agent_ai_governance_blocked', { waitDash: true })
      log(
        'ui.agent.blocked_ai_governance',
        !page.url().includes('/admin/confidence') ? 'PASS' : 'FAIL',
        page.url(),
      )

      await go(page, '/dashboard/coordinator', 'agent_blocked_coordinator', { waitDash: true })
      log(
        'ui.agent.blocked_coordinator',
        !page.url().includes('/dashboard/coordinator') ? 'PASS' : 'FAIL',
        page.url(),
      )

      const change = await go(page, '/settings/change-role', 'agent_change_role', {
        waitDash: true,
        marker: 'New identity',
      })
      log(
        'ui.agent.change_role_page',
        /New identity/i.test(change) || /Change my role/i.test(change) ? 'PASS' : 'FAIL',
        page.url(),
      )
    }

    await dropDom(page)
    if (sessions.TransactionCoordinator && wantUi('TransactionCoordinator')) {
      const injected = await loadSession(page, sessions.TransactionCoordinator)
      await page
        .getByText(/File desk|What to chase|Active files/i)
        .first()
        .waitFor({ timeout: 30000 })
        .catch(() => {})
      const dash = await dump(page, 'tc_dashboard')
      log(
        'ui.tc.landing',
        injected && page.url().includes('/dashboard/coordinator') ? 'PASS' : 'FAIL',
        page.url(),
      )
      log(
        'ui.tc.file_desk_copy',
        /File desk|What to chase|Open file|Active files/i.test(dash) ? 'PASS' : 'FAIL',
      )
      await go(page, '/dashboard/agent', 'tc_blocked_agent', { waitDash: true })
      log(
        'ui.tc.blocked_agent_dashboard',
        !page.url().includes('/dashboard/agent') ? 'PASS' : 'FAIL',
        page.url(),
      )
    }

    await dropDom(page)
    if (sessions.TeamLead && wantUi('TeamLead')) {
      const injected = await loadSession(page, sessions.TeamLead)
      await page
        .getByRole('button', { name: /Invite to team/i })
        .waitFor({ timeout: 30000 })
        .catch(() => {})
      const dash = await dump(page, 'tl_dashboard')
      log(
        'ui.tl.landing',
        injected && page.url().includes('/dashboard/team') ? 'PASS' : 'FAIL',
        page.url(),
      )
      log('ui.tl.invite_cta', /Invite to team/i.test(dash) ? 'PASS' : 'FAIL')
    }

    await dropDom(page)
    if (sessions.Admin && wantUi('Admin')) {
      const injected = await loadSession(page, sessions.Admin)
      await page
        .getByRole('button', { name: /Work a file/i })
        .waitFor({ timeout: 30000 })
        .catch(() => {})
      const dash = await dump(page, 'admin_dashboard')
      log(
        'ui.admin.landing',
        injected && page.url().includes('/dashboard/admin') ? 'PASS' : 'FAIL',
        page.url(),
      )
      log('ui.admin.work_a_file', /Work a file/i.test(dash) ? 'PASS' : 'FAIL')
      const settings = await go(page, '/settings', 'admin_settings', {
        waitDash: true,
        marker: 'AI & Automation',
      })
      log(
        'ui.admin.settings.ai_governance',
        /AI & Automation/i.test(settings) ? 'PASS' : 'FAIL',
      )
      log(
        'ui.admin.no_owner_strip',
        !hasNav(dash, 'Change my role') ? 'PASS' : 'FAIL',
        'Admin identity should not get the non-Admin Owner sidebar strip',
      )
    }
  } catch (err) {
    log('chrome.uncaught', 'FAIL', err.stack || err.message || String(err))
    await dump(page, 'uncaught').catch(() => {})
  } finally {
    await context.close().catch(() => {})
    try {
      rmSync(profile, { recursive: true, force: true })
    } catch {
      /* temp profile */
    }
  }

  const failed = findings.filter((f) => f.result === 'FAIL').length
  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings }, null, 2))
  console.log(`DONE failed=${failed}`)
  process.exit(failed ? 1 : 0)
}

run().catch((e) => {
  console.error(e)
  process.exit(1)
})
