/**
 * Chrome probe: Attorney Workspace specialized-scope leaks.
 * Logs into the attorney portal and records search, notifications,
 * and direct URL access to default-workspace surfaces.
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, 'artifacts_scope_2026-08-15')
mkdirSync(OUT, { recursive: true })

const EMAIL = 'adams.jefferson@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://127.0.0.1:5173'

const findings = []
const consoleErrors = []
const pageErrors = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 6000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 320) : ''}`)
}

async function shot(page, name) {
  const file = path.join(OUT, `${name}.png`)
  await page.screenshot({ path: file, fullPage: false }).catch(() => {})
}

async function dismissOverlays(page) {
  const labels = [
    /Skip tour/i, /Skip for now/i, /^Skip$/i, /Got it/i, /Not now/i,
    /Maybe later/i, /Close tour/i, /Dismiss/i,
  ]
  for (const name of labels) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 300 }).catch(() => false)) {
      await btn.click({ timeout: 1500 }).catch(() => {})
    }
  }
  await page.keyboard.press('Escape').catch(() => {})
}

async function waitSettled(page, ms = 700) {
  await page.waitForTimeout(ms)
  await page.waitForLoadState('load', { timeout: 8000 }).catch(() => {})
}

async function login(page) {
  await page.goto(`${APP}/login`, { waitUntil: 'load', timeout: 60000 })
  await page.locator('#login-email').fill(EMAIL)
  await page.locator('#login-password').fill(PASSWORD)
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 25000 })
  await waitSettled(page, 800)
  await dismissOverlays(page)
  await page.getByText(/ATTORNEY WORKSPACE/i).first().waitFor({ timeout: 20000 })
  await page.getByText(/Loading matters/i).first().waitFor({ state: 'hidden', timeout: 25000 }).catch(() => {})
}

async function waitForAuthChrome(page) {
  await Promise.race([
    page.getByText(/ATTORNEY WORKSPACE/i).first().waitFor({ timeout: 12000 }),
    page.locator('#login-email').waitFor({ timeout: 12000 }),
    page.getByText(/Page not found/i).first().waitFor({ timeout: 12000 }),
  ]).catch(() => {})
}

async function gotoPath(page, pathName) {
  await page.goto(`${APP}${pathName}`, { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {})
  await waitSettled(page, 500)
  await waitForAuthChrome(page)
  if (page.url().includes('/login')) {
    await login(page)
    await page.goto(`${APP}${pathName}`, { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {})
    await waitSettled(page, 500)
    await waitForAuthChrome(page)
  }
  await dismissOverlays(page)
}

function pathStem(pathName) {
  return pathName.split('?')[0]
}

const AGENT_PAGE_RE =
  /All Documents|Task Queue|Needs You|New Transaction|AI Suggestions|My Playbook|Email & E-signature|Commission|Vendor directory|Closing calendar|Contacts/i

const DEFAULT_WORKSPACE_PATHS = [
  '/documents',
  '/documents/all',
  '/calendar',
  '/contacts',
  '/ai-suggestions',
  '/analytics',
  '/tasks/queue',
  '/needs-you',
  '/payments',
  '/vendors',
  '/clients',
  '/ai-emails?view=outbox',
  '/dashboard/agent',
  '/dashboard/admin',
  '/dashboard/team',
  '/settings/connections',
  '/settings/my-playbook',
  '/email-templates',
]

const COUNSEL_PATHS = [
  '/dashboard/attorney',
  '/attorney/releases',
  '/attorney/state-rules',
  '/attorney/recording-calendar',
  '/settings',
  '/settings/account',
  '/settings/notifications',
  '/settings/help',
  '/notifications',
]

async function main() {
  let browser
  try {
    browser = await chromium.launch({
      channel: 'chrome',
      headless: true,
      args: ['--disable-dev-shm-usage', '--disable-gpu', '--no-first-run'],
    })
  } catch {
    browser = await chromium.launch({ headless: true, args: ['--disable-dev-shm-usage'] })
  }
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' })
  const page = await context.newPage()
  page.setDefaultTimeout(15000)
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()) })
  page.on('pageerror', (err) => pageErrors.push(err.message))

  await login(page)
  await page.waitForURL(/\/transactions\/[0-9a-f-]{8,}/i, { timeout: 15000 }).catch(() => {})
  log('login', page.url().includes('/login') ? 'FAIL' : 'PASS', page.url())

  const topbarBriefing = page.locator('header').getByRole('button', { name: /Today's AI Briefing/i })
  log('topbar-ai-briefing', (await topbarBriefing.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  if (await topbarBriefing.isVisible().catch(() => false)) {
    await topbarBriefing.click()
    await page.waitForTimeout(800)
    const chatText = await page.locator('body').innerText()
    log(
      'topbar-ai-briefing-opens-chat',
      /legal queue|Velvet Elves AI/i.test(chatText) ? 'PASS' : 'FAIL',
      chatText.slice(0, 400),
    )
    await page.getByRole('button', { name: /Close AI chat/i }).click().catch(() => {})
    await page.keyboard.press('Escape').catch(() => {})
    await page.waitForTimeout(300)
  }

  // ── Search palette ────────────────────────────────────────────────────
  await page.getByRole('button', { name: /^Search$/i }).first().click()
  const pal = page.getByPlaceholder(/Search matters/i)
  await pal.waitFor({ timeout: 4000 })
  await page.waitForTimeout(400)
  const searchText = await page.getByRole('dialog', { name: 'Search' }).innerText()
  await shot(page, '01_search_empty')
  log('search-open-all-documents', /Open All Documents/i.test(searchText) ? 'LEAK' : 'PASS')
  log('search-create-tx', /Create new transaction/i.test(searchText) ? 'LEAK' : 'PASS')
  log('search-task-queue', /Open My Task Queue/i.test(searchText) ? 'LEAK' : 'PASS')
  log('search-ai-briefing', /Today's AI Briefing/i.test(searchText) ? 'PASS' : 'NOTE', 'briefing chip present')
  log('search-actions', 'INFO', searchText.slice(0, 1200))

  await pal.fill('oak')
  await page.getByText(/Searching/i).first().waitFor({ state: 'hidden', timeout: 8000 }).catch(() => {})
  await page.waitForTimeout(400)
  const searchHits = await page.getByRole('dialog', { name: 'Search' }).innerText()
  await shot(page, '02_search_hits')
  log('search-hits-tasks-section', /\bTasks\b/i.test(searchHits) && /Due /i.test(searchHits) ? 'LEAK' : 'PASS', searchHits.slice(0, 800))

  const firstHit = page.getByRole('dialog', { name: 'Search' }).locator('button').filter({ hasText: /Oak|Avenue|Lane|Street/i }).first()
  if (await firstHit.isVisible().catch(() => false)) {
    await firstHit.click()
    await waitSettled(page, 1000)
    const hitUrl = page.url()
    log(
      'search-hit-lands-on-matter',
      /\/transactions\/[0-9a-f-]{8,}/i.test(hitUrl) && !/\/documents/i.test(hitUrl) ? 'PASS' : 'LEAK',
      hitUrl,
    )
  } else {
    await page.keyboard.press('Escape')
    log('search-hit-lands-on-matter', 'NOTE', 'no address hit for oak')
  }

  const allDocs = page.getByRole('button', { name: /Open All Documents/i })
  if (await allDocs.isVisible().catch(() => false)) {
    await allDocs.click()
    await waitSettled(page, 1200)
    log('search-all-docs-landed', /\/documents/i.test(page.url()) ? 'LEAK' : 'PASS', page.url())
    await shot(page, '03_all_documents_page')
  } else {
    log('search-all-docs-landed', 'PASS', 'action hidden')
  }

  await gotoPath(page, '/dashboard/attorney')
  await page.getByText(/Loading matters/i).first().waitFor({ state: 'hidden', timeout: 20000 }).catch(() => {})
  await waitSettled(page, 800)
  await dismissOverlays(page)

  // ── Notifications ─────────────────────────────────────────────────────
  await page.getByRole('button', { name: /Notifications/i }).first().click()
  const notifDialog = page.getByRole('dialog', { name: 'Notifications' })
  await notifDialog.waitFor({ timeout: 4000 }).catch(() => {})
  await page.waitForTimeout(800)
  const notifText = (await notifDialog.innerText().catch(() => page.locator('body').innerText()))
  await shot(page, '04_notifications')
  log('notif-ai-drafts', /AI draft/i.test(notifText) ? 'LEAK' : 'PASS')
  log('notif-outbound-email', /outbound email/i.test(notifText) ? 'LEAK' : 'PASS')
  log('notif-overdue-tab', /\bOverdue\b/.test(notifText) ? 'LEAK' : 'PASS', 'task-queue filter chrome')
  log('notif-panel', 'INFO', notifText.slice(0, 1500))

  const seeAll = notifDialog.getByRole('button', { name: /View all/i }).first()
  if (await seeAll.isVisible().catch(() => false)) {
    await seeAll.click()
    await waitSettled(page, 800)
    log('notif-see-all-url', page.url().includes('/notifications') ? 'PASS' : 'NOTE', page.url())
    const pageText = await page.locator('body').innerText()
    log('notif-page-ai-drafts', /AI draft/i.test(pageText) ? 'LEAK' : 'PASS')
    await shot(page, '05_notifications_page')
  }

  // ── Direct URLs ───────────────────────────────────────────────────────
  for (const pathName of DEFAULT_WORKSPACE_PATHS) {
    await gotoPath(page, pathName)
    const url = page.url().replace(APP, '')
    const body = (await page.locator('body').innerText().catch(() => '')).slice(0, 400)
    const stem = pathStem(pathName)
    const stillThere = url.split('?')[0] === stem || url.startsWith(`${stem}/`) || url.startsWith(`${stem}?`)
    const looksInternal = AGENT_PAGE_RE.test(body) && stillThere
    const loggedOut = url.includes('/login')
    log(
      `url:${pathName}`,
      loggedOut ? 'FAIL' : stillThere || looksInternal ? 'LEAK' : 'PASS',
      `${url} :: ${body.replace(/\s+/g, ' ').slice(0, 220)}`,
    )
  }

  for (const pathName of COUNSEL_PATHS) {
    await gotoPath(page, pathName)
    const url = page.url().replace(APP, '')
    const bounced = url.includes('/login')
    const onDesk = /ATTORNEY WORKSPACE/i.test(await page.locator('body').innerText().catch(() => ''))
    log(`counsel-url:${pathName}`, bounced || !onDesk ? 'FAIL' : 'PASS', url)
  }

  await gotoPath(page, '/settings')
  const settingsText = await page.locator('body').innerText()
  log('settings-email-esign', /Email & E-signature/i.test(settingsText) ? 'LEAK' : 'PASS')
  log('settings-playbook', /My Playbook/i.test(settingsText) ? 'LEAK' : 'PASS')
  log('settings-profile', /Profile/i.test(settingsText) ? 'PASS' : 'FAIL')

  await gotoPath(page, '/dashboard/attorney')
  await page.locator('[data-tour="account-menu"]').click()
  await page.waitForTimeout(300)
  const menuText = await page.locator('[role="menu"]').innerText().catch(() => '')
  log('account-menu', /All Documents|Analytics|Reports|Task Queue/i.test(menuText) ? 'LEAK' : 'PASS', menuText)

  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, consoleErrors, pageErrors }, null, 2))
  const leak = findings.filter((f) => f.result === 'LEAK').length
  const fail = findings.filter((f) => f.result === 'FAIL').length
  const pass = findings.filter((f) => f.result === 'PASS').length
  writeFileSync(path.join(OUT, 'summary.txt'), `${pass} pass / ${leak} leak / ${fail} fail / ${findings.length} checks\n`)
  console.log(`\n=== ${pass} pass / ${leak} leak / ${fail} fail / ${findings.length} checks ===`)
  await browser.close()
  process.exit(leak + fail > 0 ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
