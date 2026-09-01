/**
 * Staging deploy check after Feature 2–4. Headless, one page.
 * Preview / Got it only — never confirm Run or Approve & send.
 *
 *   QA_APP=https://app.stage.velvetelves.com QA_EMAIL=... QA_PASSWORD=... node feature4_staging_deploy_verify.mjs
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
const OUT = path.join(__dirname, 'artifacts_feature4_staging_deploy')
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

function expectedChip(row) {
  if (!row.draft_id) return null
  if (row.draft_status === 'sent' || row.draft_status === 'approved') return 'Replied'
  if (!row.linked) return 'Needs a deal'
  if (row.draft_status === 'auto_approved') return 'Reply ready'
  return 'Draft to review'
}

function inboundRows(payload) {
  return (payload?.items || [])
    .filter((m) => m.direction !== 'outbound')
    .map((m) => ({
      id: m.id,
      from: m.sender_email,
      subject: (m.subject || '').slice(0, 140),
      linked: Boolean(m.transaction_id),
      address: m.transaction_address || null,
      draft_id: m.draft_id || null,
      draft_status: m.draft_status || null,
      expected_chip: null,
    }))
    .map((row) => ({ ...row, expected_chip: expectedChip(row) }))
}

async function openRow(page, needle) {
  const loc = page.locator('ul li').filter({ hasText: needle }).first()
  const visible = await loc.isVisible({ timeout: 4000 }).catch(() => false)
  if (!visible) {
    const any = page.getByText(needle, { exact: false }).first()
    const ok = await any.click({ timeout: 5000 }).then(() => true).catch(() => false)
    return ok
  }
  await loc.click({ timeout: 5000 })
  return true
}

async function paneSendVisible(page) {
  return page.getByRole('button', { name: /^(Approve & send|Send edited reply|Send edited email|Send reply)$/i }).first().isVisible().catch(() => false)
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
      inboxPayloads.push({ url: url.slice(0, 220), status: res.status(), json: await res.json() })
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
      log('login', 'FAIL', 'MFA form')
      await page.screenshot({ path: path.join(OUT, 'mfa.png'), fullPage: false }).catch(() => {})
      return
    }
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 40000 }).catch(() => {})
    await dismissOverlays(page)
    if (page.url().includes('/login')) {
      log('login', 'FAIL', await page.locator('[role="alert"]').innerText().catch(() => page.url()))
      return
    }
    log('login', 'PASS', page.url())

    await page.goto(`${APP}/admin/confidence`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.getByRole('heading', { name: /AI & Automation/i }).waitFor({ timeout: 25000 })
    const howItRuns = page.getByRole('button', { name: /How it runs/i }).first()
    if (await howItRuns.isVisible({ timeout: 3000 }).catch(() => false)) {
      await howItRuns.click().catch(() => {})
    }
    await page.getByRole('button', { name: /Preview next (run|tick)/i }).waitFor({ timeout: 25000 })
    await page.getByRole('button', { name: /Preview next (run|tick)/i }).scrollIntoViewIfNeeded()

    const overnightText = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'overnight.txt'), `${page.url()}\n\n${overnightText}`)
    await page.screenshot({ path: path.join(OUT, 'overnight.png'), fullPage: false })

    log('copy.named-emails', /Named emails/i.test(overnightText) ? 'PASS' : 'FAIL')
    log('copy.gone-named-letters', /\bNamed letters\b/i.test(overnightText) ? 'FAIL' : 'PASS')
    log('copy.inspection-deadline', /Inspection deadline reminder/i.test(overnightText) ? 'PASS' : 'FAIL')
    log('copy.last-run', /\bLast run\b/i.test(overnightText) ? 'PASS' : 'FAIL')
    log('copy.gone-last-tick', /\bLast tick\b/i.test(overnightText) ? 'FAIL' : 'PASS')
    log('copy.preview-next-run', /Preview next run/i.test(overnightText) ? 'PASS' : 'FAIL')
    log('copy.gone-preview-tick', /Preview next tick/i.test(overnightText) ? 'FAIL' : 'PASS')
    log(
      'overnight.heading',
      /Preview, Draft, Run, and Digest stay on this card/i.test(overnightText) ? 'PASS' : 'FAIL',
    )

    const previewBtn = page.getByRole('button', { name: /Preview next (run|tick)/i })
    const boxes = {
      preview: await previewBtn.boundingBox(),
      draft: await page.getByRole('button', { name: /Draft due emails/i }).boundingBox().catch(() => null),
      run: await page.getByRole('button', { name: /Run AI tasks \(sends deal email\)/i }).boundingBox().catch(() => null),
      digest: await page.getByRole('button', { name: /Send me my digest/i }).boundingBox().catch(() => null),
    }
    const sameRow =
      boxes.preview &&
      boxes.draft &&
      boxes.run &&
      boxes.digest &&
      Math.abs(boxes.preview.y - boxes.draft.y) < 40 &&
      Math.abs(boxes.preview.y - boxes.run.y) < 40 &&
      Math.abs(boxes.preview.y - boxes.digest.y) < 40
    log(
      'overnight.four-buttons-one-row',
      sameRow ? 'PASS' : 'FAIL',
      Object.fromEntries(Object.entries(boxes).map(([k, b]) => [k, b ? Math.round(b.y) : null])),
    )

    await previewBtn.click()
    const dlg = page.getByRole('alertdialog').or(page.getByRole('dialog')).first()
    const opened = await dlg.waitFor({ state: 'visible', timeout: 60000 }).then(() => true).catch(() => false)
    if (!opened) {
      log('preview.opened', 'FAIL', 'dialog did not open')
    } else {
      const ptxt = await dlg.innerText()
      writeFileSync(path.join(OUT, 'preview.txt'), ptxt)
      log('preview.this-run', /This run would send/i.test(ptxt) ? 'PASS' : 'FAIL', ptxt.slice(0, 400))
      log('preview.gone-this-tick', /This tick would send/i.test(ptxt) ? 'FAIL' : 'PASS')
      await dlg.getByRole('button', { name: /Got it/i }).click()
      log('preview.got-it', 'PASS', 'nothing sent')
    }

    await page.goto(`${APP}/ai-emails`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.getByRole('tab', { name: /Inbox/i }).waitFor({ timeout: 25000 })
    await page.waitForTimeout(2500)
    await page.screenshot({ path: path.join(OUT, 'inbox.png'), fullPage: false })
    const emailText = await page.locator('body').innerText()
    writeFileSync(path.join(OUT, 'inbox.txt'), `${page.url()}\n\n${emailText}`)

    const latest = inboxPayloads[inboxPayloads.length - 1]?.json
    const rows = inboundRows(latest)
    writeFileSync(path.join(OUT, 'inbox_api.json'), JSON.stringify({ rows, rawCount: latest?.items?.length }, null, 2))

    const unlinked = rows.filter((r) => !r.linked)
    const unlinkedDrafts = unlinked.filter((r) => r.draft_id)
    const replyReadyOnUnlinked = unlinkedDrafts.filter((r) => r.draft_status === 'auto_approved')
    log(
      'inbox.counts',
      'PASS',
      `inbound=${rows.length} linked=${rows.filter((r) => r.linked).length} unlinked=${unlinked.length} unlinked_with_draft=${unlinkedDrafts.length}`,
    )
    log(
      'inbox.unlinked-not-auto-approved',
      replyReadyOnUnlinked.length === 0 ? 'PASS' : 'FAIL',
      replyReadyOnUnlinked.map((r) => `${r.from} | ${r.subject}`).join('; ') || 'none',
    )
    log(
      'inbox.needs-a-deal-chip',
      unlinkedDrafts.length === 0 || /Needs a deal/i.test(emailText) ? 'PASS' : 'FAIL',
    )
    log(
      'inbox.unlinked-banner',
      unlinked.length === 0 || /not on a Velvet Elves file|file them to a deal|Aime will not send until/i.test(emailText)
        ? 'PASS'
        : 'FAIL',
    )
    log(
      'inbox.reply-ready-on-pending',
      rows.some((r) => r.linked && r.draft_status === 'pending_review') && /Reply ready/i.test(emailText)
        ? 'WARN'
        : 'PASS',
      'Reply ready should be auto_approved + linked only; pending_review is Draft to review',
    )

    const james = rows.find((r) => /james/i.test(r.from || '') || /Willowbrook/i.test(r.subject || ''))
    const selfFrom = rows.find((r) => /crazyaidev/i.test(r.from || ''))
    log('inbox.james-row', james ? (james.linked ? 'WARN' : 'PASS') : 'SKIP', james ? JSON.stringify(james) : 'not in current inbox page')
    log('inbox.self-from-row', selfFrom ? (selfFrom.linked ? 'WARN' : 'PASS') : 'SKIP', selfFrom ? JSON.stringify(selfFrom) : 'not in current inbox page')

    async function inspect(label, row, extraNeedles) {
      const needle = extraNeedles.find((n) => n) || (row?.subject || '').slice(0, 28)
      if (!needle) {
        log(`${label}.open`, 'SKIP', 'no needle')
        return
      }
      const clicked = await openRow(page, needle)
      if (!clicked) {
        log(`${label}.open`, 'SKIP', `could not click ${needle}`)
        return
      }
      await page.waitForTimeout(1800)
      await page.screenshot({ path: path.join(OUT, `${label}.png`), fullPage: false })
      const pane = await page.locator('body').innerText()
      writeFileSync(path.join(OUT, `${label}.txt`), pane)
      const send = await paneSendVisible(page)
      const notLinked = /Not linked to a deal/i.test(pane)
      const matchFirst = /Match this to a deal before sending/i.test(pane)
      log(`${label}.open`, 'PASS', needle)
      log(`${label}.not-linked`, notLinked ? 'PASS' : row && !row.linked ? 'FAIL' : 'PASS', notLinked ? 'Not linked' : 'linked or no badge')
      log(`${label}.approve-send`, send ? (row && !row.linked ? 'FAIL' : 'WARN') : 'PASS', send ? 'Approve & send visible' : 'no Approve & send')
      log(`${label}.match-copy`, !row || row.linked || matchFirst ? 'PASS' : 'FAIL')
      log(`${label}.reply-ready`, /Reply ready/i.test(pane) && (notLinked || (row && !row.linked)) ? 'FAIL' : 'PASS')
    }

    if (unlinkedDrafts[0]) {
      await inspect('unlinked', unlinkedDrafts[0], [unlinkedDrafts[0].subject.slice(0, 24), 'Needs a deal'])
    } else if (unlinked[0]) {
      await inspect('unlinked', unlinked[0], [unlinked[0].subject.slice(0, 24)])
    } else {
      log('unlinked.open', 'SKIP', 'no unlinked inbound on this page')
    }

    if (james) {
      await inspect('james', james, ['James Selman', 'Willowbrook', james.subject.slice(0, 24)])
    }
    if (selfFrom) {
      await inspect('self', selfFrom, ['Confirming title order', selfFrom.subject.slice(0, 24)])
    }
  } catch (err) {
    log('script', 'FAIL', err && err.stack ? err.stack : String(err))
  } finally {
    await context.close().catch(() => {})
    await browser.close().catch(() => {})
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    const failed = findings.filter((f) => f.result === 'FAIL').length
    const warn = findings.filter((f) => f.result === 'WARN').length
    console.log(failed ? `FAILED ${failed} WARN ${warn}` : `NO FAIL CHECKS WARN ${warn}`)
    process.exit(failed ? 1 : 0)
  }
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
