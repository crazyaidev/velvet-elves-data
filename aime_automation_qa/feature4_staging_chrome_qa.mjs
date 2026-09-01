/**
 * Staging Chrome check for Feature 4 (Overnight actions + unlinked inbox).
 * Headless, one page, Preview/Got it only — never confirm Run or Send.
 *
 *   QA_APP=https://app.stage.velvetelves.com QA_EMAIL=... QA_PASSWORD=... node feature4_staging_chrome_qa.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const APP = (process.env.QA_APP || 'https://app.stage.velvetelves.com').replace(/\/$/, '')
const EMAIL = process.env.QA_EMAIL
const PASSWORD = process.env.QA_PASSWORD
const OUT = path.join(
  __dirname,
  process.env.QA_OUT ||
    (APP.includes('localhost') || APP.includes('127.0.0.1')
      ? 'artifacts_feature4_local'
      : 'artifacts_feature4_staging'),
)
mkdirSync(OUT, { recursive: true })
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
if (!EMAIL || !PASSWORD) {
  console.error('Set QA_EMAIL and QA_PASSWORD')
  process.exit(2)
}

const findings = []
const inboxPayloads = []

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 8000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 600) : ''}`)
}

async function dismissOverlays(page) {
  for (const name of [/Skip tour/i, /Skip for now/i, /^Skip$/i, /Not now/i, /Got it/i, /Maybe later/i]) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 400 }).catch(() => false)) {
      await btn.click({ timeout: 1500 }).catch(() => {})
    }
  }
}

function summarizeInbox(payload) {
  const rows = (payload?.items || [])
    .filter((m) => m.direction !== 'outbound')
    .map((m) => ({
    id: m.id,
    from: m.sender_email,
    subject: (m.subject || '').slice(0, 120),
    linked: Boolean(m.transaction_id),
    address: m.transaction_address || null,
    draft_id: m.draft_id || null,
    draft_status: m.draft_status || null,
    category: m.category || null,
  }))
  const unlinked = rows.filter((r) => !r.linked)
  const unlinkedWithDraft = unlinked.filter((r) => r.draft_id)
  return {
    total: rows.length,
    linked: rows.filter((r) => r.linked).length,
    unlinked: unlinked.length,
    unlinked_with_draft: unlinkedWithDraft.length,
    rows,
  }
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
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(20000)

  page.on('response', async (res) => {
    const url = res.url()
    if (!url.includes('/api/v1/ai-emails/messages') || res.request().method() !== 'GET') return
    if (url.includes('/ai-emails/messages/')) return
    try {
      const json = await res.json()
      inboxPayloads.push({ url: url.slice(0, 220), status: res.status(), json })
    } catch {
      /* ignore */
    }
  })

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.locator('#login-email').waitFor({ state: 'visible', timeout: 25000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    const mfa = await page.getByLabel('Two-step verification form').waitFor({ timeout: 5000 }).then(() => true).catch(() => false)
    if (mfa) {
      log('login', 'FAIL', 'MFA form — staging check cannot continue')
      await page.screenshot({ path: path.join(OUT, 'mfa.png'), fullPage: false }).catch(() => {})
      return
    }
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 40000 }).catch(() => {})
    await dismissOverlays(page)
    if (page.url().includes('/login')) {
      const alert = await page.locator('[role="alert"]').innerText().catch(() => '')
      log('login', 'FAIL', alert || page.url())
      return
    }
    log('login', 'PASS', page.url())

    // ── Overnight ────────────────────────────────────────────────────────
    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.getByRole('heading', { name: /AI & Automation/i }).waitFor({ timeout: 25000 })
    const howItRuns = page.getByRole('button', { name: /How it runs/i }).first()
    if (await howItRuns.isVisible({ timeout: 3000 }).catch(() => false)) {
      await howItRuns.click().catch(() => {})
    }
    const previewBtn = page.getByRole('button', { name: /Preview next (run|tick)/i })
    await previewBtn.waitFor({ timeout: 25000 })
    await previewBtn.scrollIntoViewIfNeeded()

    const overnightText = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'overnight.txt'), `${page.url()}\n\n${overnightText}`)

    const previewName = /Preview next run/i.test(overnightText) ? 'Preview next run' : 'Preview next tick'
    const labels = {
      preview: await page.getByRole('button', { name: /Preview next (run|tick)/i }).isVisible().catch(() => false),
      draft: await page.getByRole('button', { name: /Draft due emails/i }).isVisible().catch(() => false),
      run: await page.getByRole('button', { name: /Run AI tasks \(sends deal email\)/i }).isVisible().catch(() => false),
      digest: await page.getByRole('button', { name: /Send me my digest/i }).isVisible().catch(() => false),
    }
    log('overnight.preview', labels.preview ? 'PASS' : 'FAIL', previewName)
    log('overnight.draft', labels.draft ? 'PASS' : 'FAIL')
    log('overnight.run', labels.run ? 'PASS' : 'FAIL', labels.run ? 'present on Overnight' : 'missing')
    log('overnight.digest', labels.digest ? 'PASS' : 'FAIL')
    log(
      'overnight.heading-workspace-actions',
      /Preview, Draft, Run, and Digest stay on this card|These four controls stay on this card|Workspace actions/i.test(overnightText)
        ? 'PASS'
        : 'FAIL',
      'four Overnight buttons explained on the same card',
    )
    log(
      'overnight.toast-copy-email-review',
      /Email review/i.test(overnightText) && !/Intelligence → Email/i.test(overnightText) ? 'WARN' : 'PASS',
      'tooltip/title still says Email review if present in DOM',
    )

    await page.getByRole('button', { name: /Preview next (run|tick)/i }).scrollIntoViewIfNeeded()
    const runBox = labels.run
      ? await page.getByRole('button', { name: /Run AI tasks \(sends deal email\)/i }).boundingBox()
      : null
    const draftBox = labels.draft
      ? await page.getByRole('button', { name: /Draft due emails/i }).boundingBox()
      : null
    const digestBox = labels.digest
      ? await page.getByRole('button', { name: /Send me my digest/i }).boundingBox()
      : null
    const previewBox = labels.preview
      ? await page.getByRole('button', { name: /Preview next (run|tick)/i }).boundingBox()
      : null
    const sameRow =
      previewBox &&
      draftBox &&
      runBox &&
      digestBox &&
      Math.abs(previewBox.y - draftBox.y) < 40 &&
      Math.abs(previewBox.y - runBox.y) < 40 &&
      Math.abs(previewBox.y - digestBox.y) < 40
    log(
      'overnight.four-buttons-one-row',
      sameRow ? 'PASS' : 'FAIL',
      sameRow ? `y=${Math.round(previewBox.y)}` : 'buttons not on one wrap row',
    )

    await page.getByRole('button', { name: /Preview next (run|tick)/i }).scrollIntoViewIfNeeded()
    await page.screenshot({ path: path.join(OUT, 'overnight.png'), fullPage: false })

    await page.getByRole('button', { name: /Preview next (run|tick)/i }).click()
    const dlg = page.getByRole('alertdialog').or(page.getByRole('dialog')).first()
    const opened = await dlg.waitFor({ state: 'visible', timeout: 60000 }).then(() => true).catch(() => false)
    if (opened) {
      const ptxt = await dlg.innerText()
      writeFileSync(path.join(OUT, 'preview.txt'), ptxt)
      log('preview.opened', 'PASS', ptxt.slice(0, 400))
      await dlg.getByRole('button', { name: /Got it/i }).click()
    } else {
      log('preview.opened', 'FAIL', 'dialog did not open')
    }

    // ── Intelligence → Email ────────────────────────────────────────────
    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.getByText(/Intelligence/i).first().waitFor({ timeout: 20000 }).catch(() => {})
    await page.getByRole('tab', { name: /Inbox/i }).waitFor({ timeout: 25000 }).catch(() => {})
    await page.waitForTimeout(2500)
    await page.screenshot({ path: path.join(OUT, 'inbox.png'), fullPage: false })
    const emailText = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'inbox.txt'), `${page.url()}\n\n${emailText}`)

    const latestInbox = inboxPayloads[inboxPayloads.length - 1]?.json
    const summary = summarizeInbox(latestInbox)
    writeFileSync(path.join(OUT, 'inbox_api.json'), JSON.stringify({ summary, raw: latestInbox }, null, 2))

    log('email.inbox-tab', /Inbox/i.test(emailText) ? 'PASS' : 'FAIL')
    log(
      'api.inbox-counts',
      'PASS',
      `items=${summary.total} linked=${summary.linked} unlinked=${summary.unlinked} unlinked_with_draft=${summary.unlinked_with_draft}`,
    )
    log(
      'email.needs-a-deal-chip',
      summary.unlinked_with_draft === 0 || /Needs a deal/i.test(emailText) ? 'PASS' : 'FAIL',
      'unlinked drafts must not look Reply ready',
    )
    log(
      'email.unlinked-banner',
      summary.unlinked === 0 || /not on a Velvet Elves file|file them to a deal|Aime will not send until/i.test(emailText)
        ? 'PASS'
        : 'FAIL',
    )

    const target = summary.rows.find((r) => !r.linked && r.draft_id) || summary.rows.find((r) => !r.linked)
    if (target) {
      const row = page.locator('li, button, a').filter({ hasText: (target.subject || '').slice(0, 24) }).first()
      const clicked = await row.click({ timeout: 8000 }).then(() => true).catch(() => false)
      if (!clicked) {
        await page.getByText(/Needs a deal|Not linked/i).first().click({ timeout: 5000 }).catch(() => {})
      }
      await page.waitForTimeout(1500)
      await page.screenshot({ path: path.join(OUT, 'unlinked_detail.png'), fullPage: false })
      const pane = await page.locator('body').innerText()
      writeFileSync(path.join(OUT, 'unlinked_detail.txt'), pane)
      const sendVisible = await page.getByRole('button', { name: /^(Send|Approve & send|Send reply)$/i }).first().isVisible().catch(() => false)
      log(
        'email.unlinked-send-control',
        sendVisible ? 'FAIL' : 'PASS',
        sendVisible
          ? 'Send is available on an unlinked message'
          : 'no Send on the open unlinked row',
      )
      log(
        'email.unlinked-reply-ready-chip',
        /Reply ready/i.test(pane) && (/Not linked/i.test(pane) || /Needs a deal/i.test(pane)) ? 'FAIL' : 'PASS',
        'green Reply ready on unmatched mail',
      )
    } else {
      log('email.unlinked-row', 'SKIP', 'no unlinked inbox item in API payload')
    }
  } catch (err) {
    log('script', 'FAIL', err && err.stack ? err.stack : String(err))
  } finally {
    await context.close().catch(() => {})
    await browser.close().catch(() => {})
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    const failed = findings.filter((f) => f.result === 'FAIL').length
    console.log(failed ? `FAILED ${failed}` : 'NO FAIL CHECKS')
    process.exit(failed ? 1 : 0)
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
