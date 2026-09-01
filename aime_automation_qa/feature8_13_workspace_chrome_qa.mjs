/**
 * Feature 8–13 local Chrome check. One page, headless, low RAM.
 * Does not Send, does not confirm status changes.
 *
 *   $env:QA_APP='http://localhost:5173'
 *   $env:QA_EMAIL='shyna.elene@minafter.com'
 *   $env:QA_PASSWORD='...'
 *   node feature8_13_workspace_chrome_qa.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_feature8_13_local')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'shyna.elene@minafter.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const APP = (process.env.QA_APP || 'http://localhost:5173').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

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

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false }).catch(() => {})
}

async function run() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME,
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
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(20000)

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.locator('#login-email').waitFor({ state: 'visible', timeout: 20000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 30000 }).catch(() => {})
    await dismissOverlays(page)
    if (page.url().includes('/login')) {
      log('login', 'FAIL', page.url())
      await shot(page, 'login_fail')
      return
    }
    log('login', 'PASS', page.url())

    await page.goto(`${APP}/transactions/4585ea3b-43d1-420e-b5d9-8193afdd3d1f`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    })
    await page.waitForURL(/\/transactions\/4585ea3b/, { timeout: 20000 })
    await dismissOverlays(page)
    const heading = page.getByRole('heading', { level: 1 }).first()
    await heading.waitFor({ state: 'visible', timeout: 25000 })
    log('open-deal', 'PASS', `${page.url()} · ${await heading.innerText()}`)

    const posture = page.getByRole('button', { name: /Automation posture for this deal/i })
    const hasPosture = await posture.isVisible({ timeout: 12000 }).catch(() => false)
    if (!hasPosture) {
      log('f8-captions', 'FAIL', `no posture chip · url=${page.url()}`)
      await shot(page, 'no_posture')
    } else {
      await posture.click()
    const menu = page.getByRole('menu')
    await menu.waitFor({ state: 'visible', timeout: 8000 }).catch(() => {})
    const menuText = (await page.locator('[role="menu"], [data-radix-menu-content]').first().innerText().catch(() => page.locator('body').innerText()))
    writeFileSync(path.join(OUT, 'posture.txt'), menuText)
    await shot(page, 'posture')
    const need = [
      'AI suggests. You click to apply anything. Named emails wait until you switch this deal off Manual.',
      'Named emails are drafted — you tap Send.',
      'Authorized emails send without a tap',
    ]
    const forbid = ['you manually send', 'Named letters', 'Authorized letters']
    const missing = need.filter((n) => !menuText.includes(n))
    const bad = forbid.filter((n) => menuText.toLowerCase().includes(n.toLowerCase()))
    log('f8-captions', missing.length || bad.length ? 'FAIL' : 'PASS', JSON.stringify({ missing, bad }))
    await page.keyboard.press('Escape')
    }

    await page.goto(`${page.url().split('?')[0]}?tab=contacts`, {
      waitUntil: 'domcontentloaded',
    })
    await dismissOverlays(page)
    await page.getByRole('heading', { name: 'Contacts' }).waitFor({ timeout: 15000 })
    const expand = page.getByRole('button', { name: /Show details for/i }).first()
    const hasParty = await expand.isVisible({ timeout: 8000 }).catch(() => false)
    if (!hasParty) {
      log('f9-expand', 'SKIP', 'no party cards on this file')
      await shot(page, 'contacts_empty')
    } else {
      const collapsed = await page.locator('section[aria-label="Contacts"]').innerText()
      await expand.click()
      const expanded = await page.locator('section[aria-label="Contacts"]').innerText()
      writeFileSync(path.join(OUT, 'contacts.txt'), expanded)
      await shot(page, 'contacts')
      const openedCompose = await page.getByRole('dialog').isVisible().catch(() => false)
      log(
        'f9-expand',
        expanded.includes('Email.') && !openedCompose ? 'PASS' : 'FAIL',
        JSON.stringify({
          openedCompose,
          hasEmailLine: expanded.includes('Email.'),
          collapsedHadPatEmail: /@/.test(collapsed) && collapsed.includes('Email.'),
        }),
      )
      const mail = page.getByRole('button', { name: /^Email /i }).first()
      if (await mail.isVisible().catch(() => false)) {
        await mail.click()
        const dialog = page.getByRole('dialog')
        await dialog.waitFor({ state: 'visible', timeout: 8000 })
        const dlg = await dialog.innerText()
        writeFileSync(path.join(OUT, 'compose.txt'), dlg)
        await shot(page, 'compose')
        const pressed = await dialog.locator('[aria-pressed="true"]').allInnerTexts()
        log(
          'f10-preselect',
          pressed.length === 1 ? 'PASS' : 'FAIL',
          JSON.stringify({ pressed, hasOneOff: dlg.includes('Someone not on this file') }),
        )
        await page.getByRole('button', { name: /Cancel/i }).click().catch(() => {})
      } else {
        log('f10-preselect', 'SKIP', 'no Mail icon on this file')
      }
    }

    const emailTab = page.getByRole('tab', { name: /^Email$/i })
    await emailTab.scrollIntoViewIfNeeded().catch(() => {})
    if (await emailTab.isVisible({ timeout: 8000 }).catch(() => false)) {
      await emailTab.click()
      await page.getByText(/Nothing sends until you tap Send/i).waitFor({ timeout: 8000 })
      const emailText = await page.locator('body').innerText()
      writeFileSync(path.join(OUT, 'email.txt'), emailText)
      await shot(page, 'email')
      log(
        'f10-outbox-copy',
        emailText.includes('Drafts you prepare land on Outbox') &&
          !/inspection-reminder letters/i.test(emailText)
          ? 'PASS'
          : 'FAIL',
        emailText.includes('Drafts you prepare land on Outbox') ? 'outbox sentence present' : 'missing outbox sentence',
      )
    } else {
      log('f10-outbox-copy', 'SKIP', 'Email tab not on this workspace')
    }

    const status = page.getByRole('button', { name: /^(Active|Completed|Closed|Terminated|Paused|Incomplete)/i }).first()
    await status.click().catch(() => {})
    const term = page.getByRole('menuitem', { name: /Terminated/i }).or(page.getByText('Terminated', { exact: true }))
    if (await term.first().isVisible({ timeout: 4000 }).catch(() => false)) {
      await term.first().click()
      const dialog = page.getByRole('alertdialog').or(page.getByRole('dialog'))
      await dialog.first().waitFor({ state: 'visible', timeout: 8000 }).catch(() => {})
      const dt = await dialog.first().innerText().catch(() => '')
      writeFileSync(path.join(OUT, 'terminated.txt'), dt)
      await shot(page, 'terminated')
      log(
        'f13-terminated',
        dt.includes('Automatic emails stop') && !dt.includes('Automatic letters stop') ? 'PASS' : 'FAIL',
        dt.slice(0, 500),
      )
      const cancel = page.getByRole('button', { name: /Cancel|Close|Keep/i }).first()
      if (await cancel.isVisible().catch(() => false)) await cancel.click()
      else await page.keyboard.press('Escape')
    } else {
      log('f13-terminated', 'FAIL', 'Terminated not on the status control')
      await shot(page, 'no_terminated')
    }
  } catch (err) {
    log('script', 'FAIL', err?.stack || err?.message || err)
    await shot(page, 'crash')
  } finally {
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    await browser.close()
  }

  process.exit(findings.some((f) => f.result === 'FAIL') ? 1 : 0)
}

run()
