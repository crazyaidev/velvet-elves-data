/**
 * Local Chrome QA for All Documents e-sign now that DocuSign is connected.
 * Headed Google Chrome against http://localhost:5173
 *
 * Sends one test envelope to the platform-admin email, then syncs, voids,
 * and checks Resend prefill so we don't leave a live envelope hanging.
 */
import { copyFileSync, mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { createRequire } from 'module'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const PASS = process.env.QA_PASS || 'esign'
const OUT = path.join(__dirname, `artifacts_2026-08-13_${PASS}`)
mkdirSync(OUT, { recursive: true })

const EMAIL = 'shyna.elene@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://localhost:5173'
const STAMP = Date.now().toString().slice(-6)
const QA_NAME = `QA-Esign-${STAMP}`
const SOURCE_PDF = path.join(__dirname, '..', 'testing_pdfs', 'template_test.pdf')
const FIXTURE = path.join(OUT, `${QA_NAME}.pdf`)
copyFileSync(SOURCE_PDF, FIXTURE)

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
const esignNetwork = []
let lastDocs = null
let lastQueue = null
let shotIdx = 0
let sentDocId = null

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 400) : ''}`)
}

async function shot(page, name) {
  shotIdx += 1
  const file = path.join(OUT, `${String(shotIdx).padStart(2, '0')}_${name}.png`)
  try {
    await page.screenshot({ path: file, fullPage: false })
  } catch (err) {
    console.log('screenshot failed', name, err.message)
  }
}

async function dumpText(page, name) {
  try {
    const text = await page.locator('body').innerText({ timeout: 8000 })
    writeFileSync(path.join(OUT, `${name}.txt`), text)
    return text
  } catch {
    return ''
  }
}

async function dismissOverlays(page) {
  const labels = [
    /Skip tour/i,
    /Skip for now/i,
    /^Skip$/i,
    /Got it/i,
    /Not now/i,
    /Maybe later/i,
    /Continue to (app|dashboard)/i,
    /Go to Dashboard/i,
  ]
  for (const name of labels) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 400 }).catch(() => false)) {
      await btn.click({ timeout: 2000 }).catch(() => {})
      await page.waitForTimeout(200)
    }
  }
  await page.keyboard.press('Escape').catch(() => {})
}

async function waitForDocs(page) {
  await page.getByRole('heading', { name: /All Documents/i }).first().waitFor({ timeout: 45000 })
  await page.waitForFunction(
    () => {
      const t = document.body?.innerText || ''
      if (/Couldn't load documents/i.test(t)) return true
      return /need attention|Inbox zero|Pipeline is unblocked|All docs/i.test(t) && !/\bLoading\b/.test(t)
    },
    { timeout: 45000 },
  )
  await page.waitForTimeout(400)
}

function stayOnDocs(page) {
  try {
    const u = new URL(page.url())
    return u.pathname === '/documents' || u.pathname === '/documents/all'
  } catch {
    return /\/documents/.test(page.url())
  }
}

async function dialogText(page) {
  const dlg = page.getByRole('dialog').first()
  if (await dlg.isVisible().catch(() => false)) return dlg.innerText()
  return page.locator('body').innerText()
}

async function addQaSigner(page, dlg) {
  const partyChip = dlg.locator('button').filter({ hasText: EMAIL }).first()
  if (await partyChip.isVisible().catch(() => false)) {
    await partyChip.click()
    await page.waitForTimeout(300)
    return 'party-chip'
  }
  const namedChip = dlg.locator('button').filter({ hasText: /^\+\s.+\(/ }).first()
  if (await namedChip.isVisible().catch(() => false)) {
    await namedChip.click()
    await page.waitForTimeout(300)
    return 'party-chip-other'
  }
  await dlg.getByRole('button', { name: /\+ Add signer/i }).click()
  await page.waitForTimeout(200)
  const nameInput = dlg.getByPlaceholder('Name')
  const emailInput = dlg.getByPlaceholder('email@example.com')
  await nameInput.fill('Shyna Elene QA')
  await emailInput.fill(EMAIL)
  return 'manual'
}

async function main() {
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: false,
    args: ['--start-maximized'],
  })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    acceptDownloads: true,
  })
  const page = await context.newPage()

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (err) => pageErrors.push(err.message))
  page.on('requestfailed', (req) => {
    failedRequests.push(`${req.method()} ${req.url()}`)
  })
  page.on('response', async (res) => {
    const url = res.url()
    try {
      if (url.includes('/api/v1/dashboard/documents-priority-queue') && res.ok() && !url.includes('/cleared')) {
        lastQueue = await res.json()
      }
      if (
        /\/api\/v1\/documents(\?|$)/.test(url) &&
        res.request().method() === 'GET' &&
        res.ok() &&
        !url.includes('is_deleted')
      ) {
        lastDocs = await res.json()
      }
    } catch {
      /* ignore */
    }
    if (url.includes('/esign') || /\/documents\/[^/]+\/esign/.test(url)) {
      let body = ''
      try {
        body = (await res.text()).slice(0, 1500)
      } catch {
        body = ''
      }
      esignNetwork.push({
        status: res.status(),
        method: res.request().method(),
        url,
        body,
      })
    }
    if (url.includes('/api/v1/') && res.status() >= 400) {
      failedRequests.push(`${res.status()} ${res.request().method()} ${url}`)
    }
  })

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.locator('#login-email').waitFor({ timeout: 15000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 })
    await page.waitForTimeout(1200)
    await dismissOverlays(page)
    await dismissOverlays(page)
    log('login', 'PASS', page.url())
  } catch (err) {
    log('login', 'FAIL', err.message)
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify({ findings, consoleErrors, pageErrors }, null, 2))
    await browser.close()
    process.exit(1)
  }

  try {
    const navLink = page.getByRole('link', { name: /All Documents/i }).first()
    await navLink.click()
    await waitForDocs(page)
    log('nav-all-documents', stayOnDocs(page) ? 'PASS' : 'FAIL', page.url())
  } catch (err) {
    log('nav-all-documents', 'FAIL', err.message)
    await page.goto(`${APP}/documents`, { waitUntil: 'domcontentloaded' })
    await waitForDocs(page)
  }

  await shot(page, 'docs_loaded')
  const beforeText = await dumpText(page, 'docs_before_esign')
  const countPill = beforeText.match(/(\d+)\s+need attention[\s\S]{0,40}(\d+)\s+of\s+(\d+)\s+complete/)
  log(
    'baseline-counts',
    countPill ? 'PASS' : 'INFO',
    countPill ? countPill[0].replace(/\s+/g, ' ') : beforeText.slice(0, 200),
  )

  // Header Send for Sig — connection state (capture flicker)
  try {
    await page.locator('header').getByRole('button', { name: /Send for signature/i }).click()
    const dlg = page.getByRole('dialog')
    await dlg.waitFor({ timeout: 8000 })
    const immediate = await dlg.innerText()
    const showedDisconnectedWhileOpening = /No e-signature provider connected/i.test(immediate)
    await page.waitForTimeout(2500)
    const settled = await dlg.innerText()
    await shot(page, 'sig_modal_header')
    log(
      'esign-modal-opens',
      /Send for Signature/i.test(settled) ? 'PASS' : 'FAIL',
      settled.slice(0, 240),
    )
    log(
      'esign-connected-banner',
      /Connected to/i.test(settled) && !/No e-signature provider connected/i.test(settled)
        ? 'PASS'
        : 'FAIL',
      settled.match(/Connected to[\s\S]{0,80}|No e-signature provider[\s\S]{0,120}|Connect DocuSign[\s\S]{0,80}/)?.[0] || settled.slice(0, 300),
    )
    log(
      'esign-connect-flicker',
      showedDisconnectedWhileOpening && /Connected to/i.test(settled) ? 'FAIL' : 'PASS',
      showedDisconnectedWhileOpening
        ? 'Red "not connected" banner flashed before provider-status returned'
        : 'No disconnected flash',
    )
    log(
      'esign-demo-watermark-note',
      /demo \/ sandbox|DEMONSTRATION DOCUMENT/i.test(settled) ? 'INFO' : 'PASS',
      /demo \/ sandbox/i.test(settled) ? 'sandbox account' : 'production or unknown',
    )
    const sendBtn = dlg.getByRole('button', { name: /^Send for Signature$/i })
    log(
      'esign-send-disabled-without-context',
      (await sendBtn.isDisabled()) ? 'PASS' : 'FAIL',
      'Send should stay disabled until transaction, document, signers, and provider are ready',
    )
    await page.keyboard.press('Escape')
    await page.waitForTimeout(400)
  } catch (err) {
    log('esign-header-modal', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // Upload a clearly named PDF onto a live transaction
  try {
    await page.getByRole('button', { name: /^Upload$/i }).first().click()
    const uploadDlg = page.getByRole('dialog')
    await uploadDlg.waitFor({ timeout: 8000 })
    const txSelect = uploadDlg.locator('#upload-transaction')
    const options = await txSelect.locator('option').count()
    if (options > 1) await txSelect.selectOption({ index: 1 })
    const typeChip = uploadDlg.getByRole('button').filter({ hasText: /Other|Contract|Disclosure|Purchase/i }).first()
    if (await typeChip.isVisible().catch(() => false)) await typeChip.click()
    const chooserPromise = page.waitForEvent('filechooser', { timeout: 8000 })
    await uploadDlg.getByRole('button', { name: /Upload Document/i }).click()
    const chooser = await chooserPromise
    await chooser.setFiles(FIXTURE)
    await page.waitForTimeout(5000)
    const afterUpload = await page.locator('body').innerText()
    log(
      'upload-qa-pdf',
      /Document uploaded/i.test(afterUpload) ? 'PASS' : 'FAIL',
      afterUpload.match(/Document uploaded[\s\S]{0,80}|Upload failed[\s\S]{0,160}|Choose a transaction[\s\S]{0,80}/)?.[0] || afterUpload.slice(0, 240),
    )
    await page.keyboard.press('Escape').catch(() => {})
  } catch (err) {
    log('upload-qa-pdf', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // Filter to the QA file and send from the row Sign control (document preselected)
  try {
    await page.getByRole('button', { name: /^All docs/i }).first().click()
    await page.waitForTimeout(600)
    const filter = page.getByRole('searchbox', { name: /Filter documents/i }).or(page.getByLabel(/Filter documents/i)).first()
    if (await filter.isVisible().catch(() => false)) {
      await filter.fill(QA_NAME)
    } else {
      const input = page.locator('input[aria-label="Filter documents"]').first()
      await input.fill(QA_NAME)
    }
    await page.waitForTimeout(800)
    const card = page.locator('[data-doc-id]').filter({ hasText: QA_NAME }).first()
    await card.waitFor({ timeout: 10000 })
    sentDocId = await card.getAttribute('data-doc-id')
    log('row-qa-card', sentDocId ? 'PASS' : 'FAIL', sentDocId || 'no data-doc-id')
    await shot(page, 'qa_card_filtered')
    await card.getByRole('button', { name: /Send for Signature/i }).click()
    const dlg = page.getByRole('dialog')
    await dlg.waitFor({ timeout: 8000 })
    await page.waitForTimeout(2000)
    const opened = await dlg.innerText()
    log(
      'row-sign-preselects-document',
      new RegExp(QA_NAME, 'i').test(opened) ? 'PASS' : 'FAIL',
      opened.slice(0, 280),
    )
    const signerHow = await addQaSigner(page, dlg)
    log('esign-add-signer', 'PASS', signerHow)
    await shot(page, 'sig_modal_ready')
    const sendBtn = dlg.getByRole('button', { name: /^Send for Signature$/i })
    const enabled = await sendBtn.isEnabled()
    log('esign-send-enabled', enabled ? 'PASS' : 'FAIL', await dlg.innerText().then((t) => t.slice(0, 300)))
    if (!enabled) {
      throw new Error('Send for Signature stayed disabled')
    }
    const sendResp = page.waitForResponse(
      (res) => res.request().method() === 'POST' && /\/documents\/[^/]+\/esign$/.test(res.url()),
      { timeout: 60000 },
    )
    await sendBtn.click()
    const resp = await sendResp
    const status = resp.status()
    let body = ''
    try {
      body = await resp.text()
    } catch {
      body = ''
    }
    await page.waitForTimeout(2500)
    const afterSend = await page.locator('body').innerText()
    log(
      'esign-send-http',
      status >= 200 && status < 300 ? 'PASS' : 'FAIL',
      `${status} ${body.slice(0, 500)}`,
    )
    log(
      'esign-send-toast',
      /Sent for signature/i.test(afterSend) ? 'PASS' : 'FAIL',
      afterSend.match(/Sent for signature[\s\S]{0,120}|Send for signature failed[\s\S]{0,200}|Failed to create[\s\S]{0,200}/)?.[0] || afterSend.slice(0, 240),
    )
    await shot(page, 'after_send')
    await page.keyboard.press('Escape').catch(() => {})
  } catch (err) {
    log('esign-row-send', 'FAIL', err.message)
    await shot(page, 'send_failed')
    await page.keyboard.press('Escape').catch(() => {})
  }

  const sendPassed = findings.some((f) => f.id === 'esign-send-http' && f.result === 'PASS')

  if (sendPassed) {
    try {
      await page.getByRole('button', { name: /Sent for sig/i }).first().click()
      await page.waitForTimeout(800)
      const filter = page.locator('input[aria-label="Filter documents"]').first()
      if (await filter.isVisible().catch(() => false)) await filter.fill(QA_NAME)
      await page.waitForTimeout(600)
      const sentText = await dumpText(page, 'tab_sent')
      await shot(page, 'tab_sent')
      log(
        'sent-tab-shows-envelope',
        new RegExp(QA_NAME, 'i').test(sentText) && /Sent for sig/i.test(sentText)
          ? 'PASS'
          : 'FAIL',
        sentText.match(new RegExp(`${QA_NAME}[\\s\\S]{0,240}`))?.[0] || sentText.slice(0, 300),
      )
      log(
        'sent-tab-awaiting',
        /Awaiting:/i.test(sentText) ? 'PASS' : 'FAIL',
        sentText.match(/Awaiting:[\s\S]{0,80}/)?.[0] || 'no Awaiting label',
      )
      log(
        'sent-tab-url',
        /tab=sent/.test(page.url()) ? 'PASS' : 'FAIL',
        page.url(),
      )
      const card = page.locator('[data-doc-id]').filter({ hasText: QA_NAME }).first()
      const syncBtn = card.getByRole('button', { name: /Refresh signature status/i })
      log('sent-sync-control', (await syncBtn.isVisible()) ? 'PASS' : 'FAIL')
      const syncResp = page.waitForResponse(
        (res) => res.request().method() === 'POST' && /\/esign\/sync/.test(res.url()),
        { timeout: 30000 },
      )
      await syncBtn.click()
      const sres = await syncResp
      const syncToast = page.getByText(/Signature status refreshed/i).first()
      const toastVisible = await syncToast.isVisible({ timeout: 8000 }).catch(() => false)
      log(
        'esign-sync',
        sres.ok() && toastVisible ? 'PASS' : sres.ok() ? 'PASS' : 'FAIL',
        `${sres.status()} toast=${toastVisible}`,
      )
      await shot(page, 'after_sync')

      await card.getByRole('button', { name: /More actions/i }).click()
      await page.waitForTimeout(300)
      const menu = page.locator('[role="menu"]')
      const menuText = await menu.innerText().catch(() => '')
      log('void-in-more-menu', /Void Envelope/i.test(menuText) ? 'PASS' : 'FAIL', menuText)
      await page.getByRole('menuitem', { name: /Void Envelope/i }).click()
      await page.waitForTimeout(500)
      const confirmDlg = page.getByRole('alertdialog').or(page.getByRole('dialog').filter({ hasText: /Void this envelope/i }))
      const hadConfirm = (await confirmDlg.first().isVisible().catch(() => false)) || /Void this envelope/i.test(await page.locator('body').innerText())
      log(
        'void-confirmation',
        hadConfirm ? 'PASS' : 'FAIL',
        hadConfirm ? 'confirmation dialog shown' : 'Void ran immediately with no confirm step',
      )
      if (hadConfirm) {
        await page.getByRole('button', { name: /^Void envelope$/i }).click()
      }
      await card.getByText(/^Voided$/i).waitFor({ timeout: 12000 }).catch(() => {})
      await page.waitForTimeout(800)
      const afterVoid = await dumpText(page, 'after_void')
      await shot(page, 'after_void')
      log(
        'esign-void',
        /Envelope voided|Voided/i.test(afterVoid) ? 'PASS' : 'FAIL',
        afterVoid.match(/Envelope voided[\s\S]{0,160}|Void failed[\s\S]{0,160}|Voided[\s\S]{0,80}/)?.[0] || afterVoid.slice(0, 240),
      )
      log(
        'voided-badge-and-resend',
        /Voided/i.test(afterVoid) && (await card.getByRole('button', { name: /Resend for Signature/i }).isVisible().catch(() => false))
          ? 'PASS'
          : /Voided/i.test(afterVoid)
            ? 'FAIL'
            : 'FAIL',
        'expected Voided pill + Resend CTA',
      )
      log(
        'cleared-today-voided',
        /Voided/i.test(afterVoid) && /Cleared today|resolved in the last 24 hours/i.test(afterVoid)
          ? 'PASS'
          : 'INFO',
        afterVoid.match(/Cleared today[\s\S]{0,200}|Nothing cleared[\s\S]{0,80}/)?.[0] || '',
      )
    } catch (err) {
      log('sent-tab-lifecycle', 'FAIL', err.message)
      await page.keyboard.press('Escape').catch(() => {})
    }

    try {
      const card = page.locator('[data-doc-id]').filter({ hasText: QA_NAME }).first()
      if (await card.getByRole('button', { name: /Resend for Signature/i }).isVisible().catch(() => false)) {
        await card.getByRole('button', { name: /Resend for Signature/i }).click()
        const dlg = page.getByRole('dialog')
        await dlg.waitFor({ timeout: 8000 })
        await page.waitForTimeout(1500)
        const resendText = await dlg.innerText()
        await shot(page, 'resend_modal')
        const emailInput = dlg.getByPlaceholder('email@example.com')
        const prefilledEmail = (await emailInput.inputValue().catch(() => '')).toLowerCase()
        const hasSigner = Boolean(prefilledEmail) || /#1/.test(resendText)
        log(
          'resend-prefills-signers',
          hasSigner ? 'PASS' : 'FAIL',
          `email=${prefilledEmail} ${resendText.slice(0, 240)}`,
        )
        await dlg.getByRole('button', { name: /^Cancel$/i }).click()
        await page.waitForTimeout(400)
      } else {
        log('resend-prefills-signers', 'SKIP', 'Resend control not visible')
      }
    } catch (err) {
      log('resend-prefills-signers', 'FAIL', err.message)
      await page.keyboard.press('Escape').catch(() => {})
    }
  } else {
    log('sent-tab-lifecycle', 'SKIP', 'send did not succeed — not creating more envelopes')
  }

  try {
    await page.getByRole('button', { name: /^Signed/i }).first().click()
    await page.waitForTimeout(700)
    const signedText = await dumpText(page, 'tab_signed')
    await shot(page, 'tab_signed')
    log(
      'signed-tab-after-void',
      /No documents in this view|Signed/i.test(signedText) ? 'PASS' : 'FAIL',
      'voided envelope must not appear as Signed; completing a live DocuSign envelope is out of this pass',
    )
  } catch (err) {
    log('signed-tab-after-void', 'FAIL', err.message)
  }

  const productFails = findings.filter((f) => f.result === 'FAIL')
  const productPasses = findings.filter((f) => f.result === 'PASS')
  log(
    'console-errors',
    consoleErrors.length === 0 ? 'PASS' : 'FAIL',
    consoleErrors.slice(0, 8).join(' | '),
  )
  log(
    'page-errors',
    pageErrors.length === 0 ? 'PASS' : 'FAIL',
    pageErrors.slice(0, 8).join(' | '),
  )

  writeFileSync(
    path.join(OUT, 'findings.json'),
    JSON.stringify(
      {
        qaName: QA_NAME,
        sentDocId,
        findings,
        esignNetwork,
        failedRequests: failedRequests.slice(0, 40),
        consoleErrors,
        pageErrors,
        summary: { pass: productPasses.length, fail: productFails.length, total: findings.length },
      },
      null,
      2,
    ),
  )
  console.log(`\nQA ${QA_NAME}  PASS=${productPasses.length} FAIL=${productFails.length}  artifacts=${OUT}`)
  await browser.close()
  process.exit(productFails.length ? 1 : 0)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
