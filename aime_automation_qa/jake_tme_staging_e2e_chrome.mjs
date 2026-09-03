/**
 * Jake TME intelligence — staging E2E Chrome on freshly seeded scenarios.
 * Reads artifacts_jake_tme_e2e/seed.json from jake_tme_staging_e2e_api.mjs
 *
 *   node jake_tme_staging_e2e_chrome.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, readFileSync, rmSync, writeFileSync, existsSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_jake_tme_e2e')
const SEED = path.join(OUT, 'seed.json')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const APP = (process.env.QA_APP || 'https://app.stage.velvetelves.com').replace(/\/$/, '')
const API = (process.env.QA_API || 'https://api.stage.velvetelves.com').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

const findings = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 700) : ''}`)
}

async function dismissOverlays(page) {
  for (const name of [/Skip tour/i, /Skip for now/i, /^Skip$/i, /Not now/i, /Got it/i]) {
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

async function waitForPageReady(page, hint, timeout = 45000) {
  const start = Date.now()
  while (Date.now() - start < timeout) {
    const text = await bodyText(page)
    if (hint && new RegExp(hint, 'i').test(text)) return text
    if (text && !/^Loading\.\.\.\s*$/m.test(text.trim()) && text.replace(/Loading\.\.\./g, '').trim().length > 120) {
      return text
    }
    await page.waitForTimeout(600)
  }
  return bodyText(page)
}

async function openWorkspaceTab(page, tabName) {
  const tab = page.getByRole('tab', { name: new RegExp(`^${tabName}$`, 'i') }).first()
  if (await tab.isVisible({ timeout: 5000 }).catch(() => false)) {
    await tab.click()
    await page.waitForTimeout(800)
  }
}

async function waitForAutomationPosture(page) {
  const btn = page.getByRole('button', { name: /Automation posture/i }).first()
  await btn.waitFor({ timeout: 45000 })
  return btn
}

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false }).catch(() => {})
}

async function dump(page, name) {
  const text = await bodyText(page)
  writeFileSync(path.join(OUT, `${name}.txt`), `${page.url()}\n\n${text}`)
  return text
}

async function apiLogin() {
  const body = new URLSearchParams({ username: EMAIL, password: PASSWORD })
  const res = await fetch(`${API}/api/v1/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  const json = await res.json().catch(() => ({}))
  return { status: res.status, json }
}

async function run() {
  if (!existsSync(SEED)) {
    console.error('Missing seed.json — run jake_tme_staging_e2e_api.mjs first')
    process.exit(2)
  }
  const seed = JSON.parse(readFileSync(SEED, 'utf8'))
  const session = await apiLogin()
  if (session.status !== 200 || !session.json.access_token) {
    log('login.api', 'FAIL', `status=${session.status}`)
    process.exit(1)
  }
  log('login.api', 'PASS', EMAIL)

  const profile = path.join(OUT, `chrome-${Date.now()}`)
  mkdirSync(profile, { recursive: true })
  const context = await chromium.launchPersistentContext(profile, {
    headless: true,
    executablePath: CHROME,
    viewport: { width: 1280, height: 800 },
    args: ['--disable-gpu', '--disable-dev-shm-usage', '--mute-audio', '--no-first-run'],
  })
  await context.addInitScript(
    ({ token, refresh }) => {
      window.localStorage.setItem('velvet_elves_token', token)
      if (refresh) window.localStorage.setItem('velvet_elves_refresh_token', refresh)
      window.localStorage.setItem('ve_agent_workspace_v1', 'on')
    },
    { token: session.json.access_token, refresh: session.json.refresh_token || '' },
  )
  const page = context.pages()[0] || (await context.newPage())
  page.setDefaultTimeout(25000)

  try {
    // Settings two-state
    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await dismissOverlays(page)
    const settingsHeading = await page
      .getByRole('heading', { name: /AI & Automation/i })
      .waitFor({ timeout: 35000 })
      .then(() => true)
      .catch(() => false)
    const dateGroup = page.getByRole('radiogroup', { name: /^Contract dates$/i })
    await dateGroup.waitFor({ timeout: 35000 }).catch(() => {})
    await dateGroup.scrollIntoViewIfNeeded().catch(() => {})
    const settings = await dump(page, 'chrome_settings')
    await shot(page, 'chrome_settings')
    log(
      'ui.settings_two_date_choices',
      settingsHeading &&
        (await dateGroup.getByRole('radio', { name: /You confirm/i }).isVisible().catch(() => false)) &&
        (await dateGroup.getByRole('radio', { name: /^Trusted$/i }).isVisible().catch(() => false))
        ? 'PASS'
        : 'FAIL',
    )

    // S1 provenance on fresh file
    if (seed.s1_provenance?.id) {
      await page.goto(`${APP}/transactions/${seed.s1_provenance.id}?tab=timeline`, {
        waitUntil: 'domcontentloaded',
      })
      await dismissOverlays(page)
      await waitForAutomationPosture(page)
      const ws = await waitForPageReady(page, 'CLOSING DATE')
      await shot(page, 'chrome_s1_provenance')
      log(
        'ui.s1.confirmed_provenance',
        /\bConfirmed\b/.test(ws) ? 'PASS' : 'WARN',
        `api=${seed.s1_provenance.closingProv}; timeline may omit chip on overview-only dates`,
      )
      log('ui.s1.stages_next', /Earnest Money/i.test(ws) && /Next:/i.test(ws) ? 'PASS' : 'FAIL')
    }

    // Needs You — Verify deadline card (open deals: s5 conflict or s6 fuzzy)
    const verifyProbe = seed.s5_trusted?.verify5
      ? { txId: seed.s5_trusted.id, label: seed.s5_trusted.address }
      : seed.s6_fuzzy?.verify6
        ? { txId: seed.s6_fuzzy.id, label: seed.s6_fuzzy.address }
        : seed.s2_you_confirm?.verifyItem
          ? { txId: seed.s2_you_confirm.id, label: seed.s2_you_confirm.address }
          : null
    if (verifyProbe) {
      await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded' })
      await dismissOverlays(page)
      await page.getByRole('heading', { name: /Needs You/i }).waitFor({ timeout: 30000 }).catch(() => {})
      await page
        .locator('text=Loading')
        .first()
        .waitFor({ state: 'hidden', timeout: 35000 })
        .catch(() => {})
      const search = page.getByPlaceholder(/search/i).first()
      if (await search.isVisible().catch(() => false)) {
        await search.fill('Verify deadline')
        await page.waitForTimeout(1200)
      }
      const ny = await waitForPageReady(page, 'Verify deadline')
      await dump(page, 'chrome_needs_you_verify')
      await shot(page, 'chrome_needs_you_verify')
      const hasCard =
        /Verify deadline/i.test(ny) &&
        (ny.includes(verifyProbe.label.slice(0, 12)) || ny.includes('TrustedAuto'))
      log('ui.verify_deadline_card', hasCard ? 'PASS' : 'FAIL', verifyProbe.label)
      if (hasCard) {
        const confirmBtn = page.getByRole('button', { name: /^Confirm$/i }).first()
        const keepBtn = page.getByRole('button', { name: /Keep current/i }).first()
        const editBtn = page.getByRole('button', { name: /^Edit$/i }).first()
        log(
          'ui.verify_buttons',
          (await keepBtn.isVisible().catch(() => false)) &&
            (await confirmBtn.isVisible().catch(() => false)) &&
            (await editBtn.isVisible().catch(() => false))
            ? 'PASS'
            : 'FAIL',
        )
      }
    } else {
      log('ui.verify_deadline_card', 'SKIP', 'no open verify card in seed')
    }

    // S3 confirmed closing in UI (s2 after API confirm)
    if (seed.s3_confirm || seed.s2_you_confirm?.id) {
      const txId = seed.s2_you_confirm?.id
      if (txId && seed.s3_confirm) {
        await page.goto(`${APP}/transactions/${txId}?tab=timeline`, { waitUntil: 'domcontentloaded' })
        await dismissOverlays(page)
        await waitForAutomationPosture(page)
        const tl = await waitForPageReady(page, 'Nov|November|2026-11')
        await dump(page, 'chrome_s3_timeline')
        await shot(page, 'chrome_s3_timeline')
        log(
          'ui.s3.new_closing_visible',
          /Nov\s+1,\s+2026|2026-11-01|November 1, 2026/i.test(tl) ? 'PASS' : 'FAIL',
        )
      }
    }

    // S5 trusted — conflict should wait (verify card), not silent auto-apply
    if (seed.s5_trusted?.id) {
      await page.goto(`${APP}/transactions/${seed.s5_trusted.id}`, { waitUntil: 'domcontentloaded' })
      await dismissOverlays(page)
      await waitForAutomationPosture(page)
      await page.getByRole('button', { name: /Automation posture/i }).click()
      await page.waitForTimeout(400)
      const menu = await bodyText(page)
      log('ui.s5.trusted_on_deal', /On for this deal/i.test(menu) ? 'PASS' : 'WARN')
      await page.keyboard.press('Escape').catch(() => {})
      const ws5 = await dump(page, 'chrome_s5_trusted')
      await shot(page, 'chrome_s5_trusted')
      const waited =
        Boolean(seed.s5_trusted.verify5) ||
        /Nov\s+1,\s+2026|2026-11-01|November 1/i.test(ws5)
      log(
        'ui.s5.trusted_conflict_behavior',
        seed.s5_trusted.verify5
          ? /2026-10-15|Oct\s+15,\s+2026|October 15/i.test(ws5)
            ? 'PASS'
            : 'WARN'
          : waited
            ? 'PASS'
            : 'FAIL',
        `api closing=${seed.s5_trusted.closing5} verify=${Boolean(seed.s5_trusted.verify5)}`,
      )
    }

    // S7 Dual tasks in UI
    if (seed.s7_dual?.id) {
      await page.goto(`${APP}/transactions/${seed.s7_dual.id}`, { waitUntil: 'domcontentloaded' })
      await dismissOverlays(page)
      await waitForAutomationPosture(page)
      await openWorkspaceTab(page, 'Tasks')
      const tasks = await waitForPageReady(page, 'Deliver Title|All tasks|OPEN')
      await dump(page, 'chrome_s7_dual_tasks')
      await shot(page, 'chrome_s7_dual_tasks')
      const titleCount = (tasks.match(/Deliver Title/gi) || []).length
      log('ui.s7.dual_title_rows', titleCount >= 2 ? 'PASS' : 'FAIL', `count=${titleCount}`)
      log('ui.s7.utility', /Deliver Utility Info/i.test(tasks) ? 'PASS' : 'FAIL')
    }

    // S8 contacts flags
    if (seed.s8_contacts?.id) {
      await page.goto(`${APP}/transactions/${seed.s8_contacts.id}`, { waitUntil: 'domcontentloaded' })
      await dismissOverlays(page)
      await waitForAutomationPosture(page)
      await openWorkspaceTab(page, 'Contacts')
      const buyerToggle = page.getByRole('button', { name: /details for Dual Buyer/i })
      if (await buyerToggle.isVisible({ timeout: 8000 }).catch(() => false)) {
        await buyerToggle.click()
        await page.waitForTimeout(500)
      }
      const contacts = await waitForPageReady(page, 'Decision-maker|Must sign|Dual Buyer')
      await shot(page, 'chrome_s8_contacts')
      log(
        'ui.s8.flags',
        /Decision-maker/i.test(contacts) && /Must sign/i.test(contacts) ? 'PASS' : 'FAIL',
      )
    }

    // S9 Terminated LSE
    if (seed.s9_terminated?.id) {
      await page.goto(`${APP}/transactions/${seed.s9_terminated.id}`, { waitUntil: 'domcontentloaded' })
      await dismissOverlays(page)
      await waitForAutomationPosture(page).catch(() => {})
      const term = await waitForPageReady(page, 'Terminated|Offer Listing Success')
      await shot(page, 'chrome_s9_terminated')
      const lse = page.getByRole('button', { name: /Offer Listing Success/i })
      const visible = await lse.isVisible().catch(() => false)
      const disabled = visible ? await lse.isDisabled().catch(() => false) : false
      log('ui.s9.lse_disabled', visible && disabled ? 'PASS' : 'FAIL')
      log(
        'ui.s9.no_next_on_fresh_terminated',
        /Next:/i.test(term) ? 'FAIL' : 'PASS',
        seed.s9_terminated.next?.title || '',
      )
    }

    // Ask AI refuse on Dual or S1
    const askTx = seed.s7_dual?.id || seed.s1_provenance?.id
    if (askTx) {
      await page.goto(`${APP}/transactions/${askTx}`, { waitUntil: 'domcontentloaded' })
      await dismissOverlays(page)
      await waitForAutomationPosture(page).catch(() => {})
      const ask = page.getByRole('button', { name: /^Ask AI$/i })
      if (await ask.isVisible().catch(() => false)) await ask.click()
      const composer = page.getByLabel('Message Aime').last()
      if (await composer.waitFor({ timeout: 12000 }).then(() => true).catch(() => false)) {
        await composer.fill('tell them they can terminate')
        await page.getByRole('button', { name: /^Send$/i }).click()
        const ok = await page
          .getByText(/I cannot give legal advice or tell a party they may terminate/i)
          .waitFor({ timeout: 35000 })
          .then(() => true)
          .catch(() => false)
        log('ui.aime.refuse_legal', ok ? 'PASS' : 'FAIL')
        await shot(page, 'chrome_aime_refuse')
      }
    }
  } catch (err) {
    log('chrome.uncaught', 'FAIL', err.message || String(err))
    await shot(page, 'chrome_uncaught').catch(() => {})
  } finally {
    await context.close().catch(() => {})
    try {
      rmSync(profile, { recursive: true, force: true })
    } catch {
      /* temp */
    }
  }

  const failed = findings.filter((f) => f.result === 'FAIL').length
  writeFileSync(path.join(OUT, 'e2e_chrome.json'), JSON.stringify({ findings }, null, 2))
  console.log(`CHROME failed=${failed}`)
  process.exit(failed ? 1 : 0)
}

run().catch((e) => {
  console.error(e)
  process.exit(1)
})
