/**
 * Local Chrome QA for Workflow › All Documents.
 * Headed Google Chrome against http://localhost:5173
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const PASS = process.env.QA_PASS || 'first'
const OUT = path.join(__dirname, `artifacts_2026-08-13_${PASS}`)
mkdirSync(OUT, { recursive: true })

const EMAIL = 'shyna.elene@minafter.com'
const PASSWORD = 'QWE!@#asd234'
const APP = 'http://localhost:5173'
const QA_LABEL = `QA AllDocs ${Date.now().toString().slice(-6)}`
const FIXTURE = path.join(__dirname, 'fixtures', 'qa-upload.txt')

const findings = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let lastQueue = null
let lastDocs = null
let shotIdx = 0

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 320) : ''}`)
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
    const link = page.getByRole('link', { name }).first()
    if (await link.isVisible({ timeout: 200 }).catch(() => false)) {
      await link.click({ timeout: 2000 }).catch(() => {})
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
  await page.waitForTimeout(500)
}

function stayOnDocs(page) {
  try {
    const u = new URL(page.url())
    return u.pathname === '/documents' || u.pathname === '/documents/all'
  } catch {
    return /\/documents/.test(page.url())
  }
}

async function tinyTextBelow12(page) {
  return page.evaluate(() => {
    const out = []
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT)
    while (walker.nextNode()) {
      const el = walker.currentNode
      if (!(el instanceof HTMLElement)) continue
      if (el.closest('[data-radix-portal], [role="tooltip"]')) continue
      const style = getComputedStyle(el)
      if (style.display === 'none' || style.visibility === 'hidden') continue
      const own = [...el.childNodes]
        .filter((n) => n.nodeType === Node.TEXT_NODE && n.textContent && n.textContent.trim())
        .map((n) => n.textContent.trim())
        .join(' ')
      if (!own) continue
      const fs = parseFloat(style.fontSize)
      if (Number.isFinite(fs) && fs < 12) {
        out.push({
          fs: Math.round(fs * 10) / 10,
          text: own.slice(0, 60),
          tag: el.tagName.toLowerCase(),
        })
      }
    }
    return out.slice(0, 25)
  })
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
    try {
      if (res.url().includes('/api/v1/dashboard/documents-priority-queue') && res.ok() && !res.url().includes('/cleared')) {
        lastQueue = await res.json()
      }
      if (
        /\/api\/v1\/documents(\?|$)/.test(res.url()) &&
        res.request().method() === 'GET' &&
        res.ok() &&
        !res.url().includes('is_deleted')
      ) {
        lastDocs = await res.json()
      }
    } catch {
      /* ignore */
    }
    if (res.url().includes('/api/v1/') && res.status() >= 400) {
      failedRequests.push(`${res.status()} ${res.request().method()} ${res.url()}`)
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

  // Sidebar nav
  try {
    const navLink = page.getByRole('link', { name: /All Documents/i }).first()
    log('sidebar-nav-link', (await navLink.isVisible()) ? 'PASS' : 'FAIL')
    await navLink.click()
    await waitForDocs(page)
    log('sidebar-nav-lands', stayOnDocs(page) ? 'PASS' : 'FAIL', page.url())
  } catch (err) {
    log('sidebar-nav', 'FAIL', err.message)
    await page.goto(`${APP}/documents`, { waitUntil: 'domcontentloaded' })
    await waitForDocs(page).catch(() => {})
  }

  await dismissOverlays(page)
  await shot(page, 'docs_desktop')
  await dumpText(page, 'docs_desktop')
  writeFileSync(path.join(OUT, 'queue_api.json'), JSON.stringify(lastQueue, null, 2))
  writeFileSync(path.join(OUT, 'docs_api.json'), JSON.stringify(lastDocs, null, 2))

  const counts = lastQueue?.tab_counts || {}
  const briefing = lastQueue?.briefing || {}
  log('api-priority-queue', lastQueue ? 'PASS' : 'FAIL', JSON.stringify(counts))
  log('api-briefing', briefing.title ? 'PASS' : 'FAIL', briefing.title || '')

  // Chrome / spec header
  const crumbNav = page.getByRole('navigation', { name: 'Breadcrumb' })
  log(
    'chrome-breadcrumb',
    (await crumbNav.isVisible().catch(() => false)) ? 'PASS' : 'FAIL',
    (await crumbNav.innerText().catch(() => '')) || 'no named breadcrumb nav',
  )
  log('chrome-h1', (await page.getByRole('heading', { name: /All Documents/i }).first().isVisible()) ? 'PASS' : 'FAIL')
  log('chrome-upload', (await page.getByRole('button', { name: /Upload/i }).first().isVisible()) ? 'PASS' : 'FAIL')
  log(
    'chrome-send-for-sig',
    (await page.getByRole('button', { name: /Send for Sig/i }).first().isVisible()) ? 'PASS' : 'FAIL',
  )
  log(
    'chrome-export',
    (await page.getByRole('button', { name: /Export/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL',
    'spec §5.4 and Contacts/Task Queue pattern',
  )
  log(
    'chrome-restore',
    (await page.getByRole('button', { name: /Restore archived/i }).first().isVisible().catch(() => false))
      ? 'PASS'
      : 'FAIL',
  )
  log(
    'chrome-refresh',
    (await page.getByRole('button', { name: /Refresh/i }).first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL',
  )

  try {
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 8000 }),
      page.getByRole('button', { name: /Export CSV/i }).click(),
    ])
    log('export-csv', /\.csv$/i.test(download.suggestedFilename()) ? 'PASS' : 'FAIL', download.suggestedFilename())
  } catch (err) {
    log('export-csv', 'FAIL', err.message)
  }

  const headerText = await page.locator('h1').first().innerText()
  log('chrome-count-pill', /need attention|complete/i.test(headerText) ? 'PASS' : 'FAIL', headerText)

  // Hero + briefing
  const body = await page.locator('body').innerText()
  log('hero-today', /Today's priority|Pipeline is unblocked|All clear/i.test(body) ? 'PASS' : 'FAIL')
  log('briefing-card', /briefing|Clear the top|severity|critical/i.test(body) ? 'PASS' : 'FAIL')
  log(
    'cleared-today',
    /Cleared today/i.test(body) ? 'PASS' : 'FAIL',
    /Nothing cleared in the last 24 hours/i.test(body) ? 'empty placeholder' : 'has items',
  )

  // Tabs
  const tabNames = ['AI priority', 'All docs', 'Missing', 'Pending review', 'Sent for sig', 'Signed']
  for (const name of tabNames) {
    const tab = page.getByRole('button', { name: new RegExp(`^${name}`, 'i') }).first()
    log(`tab-present-${name.replace(/\s+/g, '-')}`, (await tab.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  }

  // Switch tabs + URL sync
  try {
    await page.getByRole('button', { name: /^All docs/i }).first().click()
    await page.waitForTimeout(600)
    await shot(page, 'tab_all_docs')
    await dumpText(page, 'tab_all_docs')
    log('url-sync-tab-all', /tab=all_docs/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    const allBody = await page.locator('body').innerText()
    log(
      'tab-all-content',
      /Preview|No documents in this view|Unassigned/i.test(allBody) ? 'PASS' : 'FAIL',
    )
    const previewCount = await page.getByRole('button', { name: /^Preview$/i }).count()
    log('tab-all-rows', previewCount > 0 ? 'PASS' : previewCount === 0 && /No documents/i.test(allBody) ? 'PASS' : 'FAIL', `${previewCount} preview buttons`)
    const showMore = page.getByRole('button', { name: /Show \d+ more/i }).first()
    log(
      'tab-all-pagination',
      previewCount <= 20 || (await showMore.isVisible().catch(() => false))
        ? 'PASS'
        : 'FAIL',
      `${previewCount} rows rendered`,
    )
  } catch (err) {
    log('tab-all-docs', 'FAIL', err.message)
  }

  try {
    await page.getByRole('button', { name: /^Missing/i }).first().click()
    await page.waitForTimeout(500)
    await shot(page, 'tab_missing')
    log('url-sync-tab-missing', /tab=missing/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    const missingChecks = await page.locator('input[type="checkbox"][aria-label^="Select"]').count()
    log('missing-multiselect', missingChecks > 0 || /No missing documents/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL', `${missingChecks} checkboxes`)
    if (missingChecks > 0) {
      const box = await page.locator('input[type="checkbox"][aria-label^="Select"]').first().boundingBox()
      log(
        'missing-checkbox-size',
        box && box.width >= 24 && box.height >= 24 ? 'PASS' : 'FAIL',
        box ? `${Math.round(box.width)}x${Math.round(box.height)}` : '',
      )
      await page.locator('input[type="checkbox"][aria-label^="Select"]').first().check()
      await page.waitForTimeout(200)
      const selectedBar = await page.locator('body').innerText()
      log('missing-bulk-bar', /item selected|Mark N\/A|Request|Upload \/ Assign/i.test(selectedBar) ? 'PASS' : 'FAIL')
      const clearSel = page.getByRole('button', { name: /^Clear$/i }).first()
      if (await clearSel.isVisible().catch(() => false)) await clearSel.click()
    }
  } catch (err) {
    log('tab-missing', 'FAIL', err.message)
  }

  for (const [label, key] of [
    ['Pending review', 'pending_review'],
    ['Sent for sig', 'sent_for_signature'],
    ['Signed', 'signed'],
  ]) {
    try {
      await page.getByRole('button', { name: new RegExp(`^${label}`, 'i') }).first().click()
      await page.waitForTimeout(450)
      await shot(page, `tab_${key}`)
      log(`url-sync-tab-${key}`, page.url().includes(`tab=${key}`) ? 'PASS' : 'FAIL', page.url())
      log(`tab-${key}-stays`, stayOnDocs(page) ? 'PASS' : 'FAIL')
    } catch (err) {
      log(`tab-${key}`, 'FAIL', err.message)
    }
  }

  // Sort
  try {
    await page.getByRole('button', { name: /^AI priority/i }).first().click()
    await page.waitForTimeout(400)
    const sortBtn = page.getByRole('button', { name: /Sort:/i }).first()
    log('sort-control', (await sortBtn.isVisible()) ? 'PASS' : 'FAIL')
    await sortBtn.click()
    await page.waitForTimeout(300)
    const closeDate = page.getByRole('menuitem', { name: /Close date/i }).first()
    if (await closeDate.isVisible().catch(() => false)) {
      await closeDate.click()
      await page.waitForTimeout(400)
      log('url-sync-sort', /sort=close_date/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    } else {
      log('url-sync-sort', 'FAIL', 'Close date menuitem not visible')
    }
    await page.getByRole('button', { name: /Sort:/i }).first().click()
    await page.waitForTimeout(200)
    const aiImpact = page.getByRole('menuitem', { name: /AI impact/i }).first()
    if (await aiImpact.isVisible().catch(() => false)) await aiImpact.click()
    else await page.keyboard.press('Escape')
  } catch (err) {
    log('sort', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // Alias route
  try {
    await page.goto(`${APP}/documents/all`, { waitUntil: 'domcontentloaded' })
    await waitForDocs(page)
    log('alias-documents-all', stayOnDocs(page) && (await page.getByRole('heading', { name: /All Documents/i }).first().isVisible()) ? 'PASS' : 'FAIL', page.url())
  } catch (err) {
    log('alias-documents-all', 'FAIL', err.message)
  }

  // Deep links
  try {
    await page.goto(`${APP}/documents?tab=signed&sort=doc_name`, { waitUntil: 'domcontentloaded' })
    await waitForDocs(page)
    await page.waitForTimeout(400)
    log('deeplink-tab-sort', /tab=signed/.test(page.url()) && /sort=doc_name/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
    const signedTab = page.getByRole('button', { name: /^Signed/i }).first()
    const signedClass = await signedTab.getAttribute('class')
    log('deeplink-signed-active', /border-ve-orange|text-ve-orange/i.test(signedClass || '') || /tab=signed/.test(page.url()) ? 'PASS' : 'FAIL')
  } catch (err) {
    log('deeplink-tab-sort', 'FAIL', err.message)
  }

  try {
    await page.goto(`${APP}/documents?sheet=cleared-all`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(1500)
    const sheetOpen = await page.getByRole('dialog', { name: /Cleared in the last 7 days/i }).isVisible().catch(() => false)
    log('deeplink-cleared-sheet', sheetOpen ? 'PASS' : 'FAIL')
    await page.keyboard.press('Escape').catch(() => {})
    await page.waitForTimeout(300)
  } catch (err) {
    log('deeplink-cleared-sheet', 'FAIL', err.message)
  }

  // Focus deep link
  const firstDocId =
    (Array.isArray(lastDocs?.items) ? lastDocs.items[0]?.id : null) ||
    (Array.isArray(lastDocs) ? lastDocs[0]?.id : null) ||
    lastQueue?.items?.find((it) => it.document_id)?.document_id
  if (firstDocId) {
    try {
      await page.goto(`${APP}/documents?focus=${firstDocId}`, { waitUntil: 'domcontentloaded' })
      await waitForDocs(page)
      const loc = page.locator(`[data-doc-id="${firstDocId}"]`).first()
      await loc.waitFor({ state: 'attached', timeout: 8000 }).catch(() => {})
      log('deeplink-focus', (await loc.count()) > 0 ? 'PASS' : 'FAIL', `${firstDocId} ${page.url()}`)
    } catch (err) {
      log('deeplink-focus', 'FAIL', err.message)
    }
  } else {
    log('deeplink-focus', 'SKIP', 'no document id in API payload')
  }

  // Hero actions + queue row
  try {
    await page.goto(`${APP}/documents`, { waitUntil: 'domcontentloaded' })
    await waitForDocs(page)
    const showAlt = page.getByRole('button', { name: /Show alternatives/i }).first()
    if (await showAlt.isVisible().catch(() => false)) {
      await showAlt.click()
      await page.waitForTimeout(600)
      await shot(page, 'priority_detail')
      const dlgText = await page.locator('body').innerText()
      log('hero-show-alternatives', /Why|Mark N\/A|Request|Upload|Close/i.test(dlgText) ? 'PASS' : 'FAIL')
      await page.keyboard.press('Escape')
      await page.waitForTimeout(300)
    } else {
      log('hero-show-alternatives', 'SKIP', 'no hero alternatives (inbox zero?)')
    }

    const queuePrimary = page.locator('article button').filter({ hasText: /Request|Upload|Generate|Nudge|Approve|Review|Call|Forward/i }).first()
    log('queue-primary-cta', (await queuePrimary.isVisible().catch(() => false)) ? 'PASS' : 'SKIP')
  } catch (err) {
    log('hero-actions', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // Cleared today legend / filters
  try {
    const legend = page.getByRole('button', { name: /What do the badges mean/i }).first()
    if (await legend.isVisible().catch(() => false)) {
      await legend.click()
      await page.waitForTimeout(300)
      log('cleared-legend', /Signed|Approved|Marked N\/A|Uploaded/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
      await page.keyboard.press('Escape')
    } else {
      log('cleared-legend', /Nothing cleared/i.test(await page.locator('body').innerText()) ? 'SKIP' : 'FAIL', 'legend trigger missing')
    }
    const meFilter = page.getByRole('button', { name: /^Me$/i }).first()
    if (await meFilter.isVisible().catch(() => false)) {
      await meFilter.click()
      await page.waitForTimeout(400)
      log('cleared-scope-me', /cleared_scope=me/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
      const allFilter = page.getByRole('button', { name: /^All$/i }).first()
      if (await allFilter.isVisible().catch(() => false)) await allFilter.click()
    } else {
      log('cleared-scope-me', 'SKIP', 'actor filter hidden on empty strip')
    }
    const whyLink = page.getByRole('button', { name: /What counts as cleared/i }).or(page.getByText(/Why isn't an item/i)).first()
    if (await whyLink.isVisible().catch(() => false)) {
      await whyLink.click()
      await page.waitForTimeout(400)
      log('cleared-rules', /Counts as cleared|Does NOT count/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
      await page.keyboard.press('Escape')
    } else {
      log('cleared-rules', 'SKIP')
    }
  } catch (err) {
    log('cleared-today-controls', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // Upload modal — validation + real upload
  try {
    await page.getByRole('button', { name: /Upload/i }).first().click()
    await page.waitForTimeout(500)
    const uploadDlg = page.getByRole('dialog')
    log('upload-dialog', (await uploadDlg.isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    await shot(page, 'upload_modal')
    const txSelect = uploadDlg.locator('#upload-transaction')
    log('upload-tx-required-attr', (await txSelect.getAttribute('required')) !== null ? 'PASS' : 'FAIL', 'empty transaction is allowed')
    const options = await txSelect.locator('option').count()
    log('upload-tx-options', options > 1 ? 'PASS' : 'FAIL', `${options} options`)
    if (options > 1) {
      await txSelect.selectOption({ index: 1 })
    }
    const typeChip = uploadDlg.getByRole('button').filter({ hasText: /Purchase|Contract|Disclosure|Other|Addendum/i }).first()
    if (await typeChip.isVisible().catch(() => false)) await typeChip.click()

    const chooserPromise = page.waitForEvent('filechooser', { timeout: 8000 })
    await uploadDlg.getByRole('button', { name: /Upload Document/i }).click()
    const chooser = await chooserPromise
    await chooser.setFiles(FIXTURE)
    await page.waitForTimeout(4000)
    const afterUpload = await page.locator('body').innerText()
    log(
      'upload-submit',
      /Document uploaded|Choose a transaction/i.test(afterUpload) || !(await uploadDlg.isVisible().catch(() => false))
        ? /Choose a transaction|Upload failed/i.test(afterUpload)
          ? 'FAIL'
          : 'PASS'
        : 'FAIL',
      afterUpload.match(/Document uploaded[\s\S]{0,80}|Upload failed[\s\S]{0,120}|Choose a transaction[\s\S]{0,80}/)?.[0] || '',
    )
    await page.keyboard.press('Escape').catch(() => {})
  } catch (err) {
    log('upload', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // All docs: preview / more / archive / restore
  try {
    await page.getByRole('button', { name: /^All docs/i }).first().click()
    await page.waitForTimeout(800)
    await dumpText(page, 'tab_all_after_upload')
    const preview = page.getByRole('button', { name: /^Preview$/i }).first()
    if (await preview.isVisible().catch(() => false)) {
      await preview.click()
      await page.waitForTimeout(1200)
      await shot(page, 'preview_modal')
      const previewOpen =
        (await page.getByRole('dialog').isVisible().catch(() => false)) ||
        /Download|Close|Preview/i.test(await page.locator('body').innerText())
      log('preview-open', previewOpen ? 'PASS' : 'FAIL')
      await page.keyboard.press('Escape')
      await page.waitForTimeout(400)

      const more = page.getByRole('button', { name: /More actions/i }).first()
      log('doc-more-menu', (await more.isVisible()) ? 'PASS' : 'FAIL')
      await more.click()
      await page.waitForTimeout(300)
      const menuText = await page.locator('[role="menu"]').innerText().catch(() => '')
      log('doc-more-email', /Email Document/i.test(menuText) ? 'PASS' : 'FAIL', menuText)
      log('doc-more-rename', /Edit Document/i.test(menuText) ? 'PASS' : 'FAIL')
      log('doc-more-versions', /Version History/i.test(menuText) ? 'PASS' : 'FAIL')
      log('doc-more-archive', /Archive Document/i.test(menuText) ? 'PASS' : 'FAIL')

      const emailItem = page.getByRole('menuitem', { name: /Email Document/i })
      if (await emailItem.isVisible().catch(() => false)) {
        await emailItem.click()
        await page.waitForTimeout(700)
        await shot(page, 'email_modal')
        log(
          'email-modal',
          (await page.getByRole('dialog').isVisible().catch(() => false)) || /To|Subject|Send/i.test(await page.locator('body').innerText())
            ? 'PASS'
            : 'FAIL',
        )
        await page.keyboard.press('Escape')
        await page.waitForTimeout(400)
      }

      await page.getByRole('button', { name: /More actions/i }).first().click()
      await page.waitForTimeout(250)
      const archiveItem = page.getByRole('menuitem', { name: /Archive Document/i })
      if (await archiveItem.isVisible().catch(() => false)) {
        await archiveItem.click()
        await page.waitForTimeout(400)
        log(
          'archive-confirm',
          (await page.getByRole('alertdialog').isVisible().catch(() => false)) ||
            /Archive this document/i.test(await page.locator('body').innerText())
            ? 'PASS'
            : 'FAIL',
        )
        await page.getByRole('button', { name: /^Archive$/i }).click()
        await page.waitForTimeout(1200)
        const toast = await page.locator('body').innerText()
        log('archive-success', /Document archived/i.test(toast) ? 'PASS' : 'FAIL')
        log('archive-undo', /Undo/i.test(toast) ? 'PASS' : 'FAIL')
      }
    } else {
      log('preview-open', 'SKIP', 'no Preview buttons on All docs')
    }
  } catch (err) {
    log('all-docs-actions', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // Restore archived
  try {
    const restore = page.getByRole('button', { name: /Restore archived/i }).first()
    await restore.click()
    await page.waitForTimeout(1000)
    await shot(page, 'restore_panel')
    const restoreText = await page.locator('body').innerText()
    log(
      'restore-panel',
      /Restore archived documents|No archived documents/i.test(restoreText) ? 'PASS' : 'FAIL',
    )
    const restoreBtn = page.getByRole('button', { name: /^Restore$/i }).first()
    if (await restoreBtn.isVisible().catch(() => false)) {
      await restoreBtn.click()
      await page.waitForTimeout(1200)
      log('restore-action', /Restored /i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
    } else {
      log('restore-action', 'SKIP', 'no archived rows')
    }
    await page.keyboard.press('Escape')
    await page.waitForTimeout(300)
  } catch (err) {
    log('restore', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // Send for signature modal
  try {
    await page.keyboard.press('Escape').catch(() => {})
    await page.waitForTimeout(300)
    await page.locator('header').getByRole('button', { name: /Send for signature/i }).click()
    await page.waitForTimeout(700)
    await shot(page, 'esign_modal')
    const sigText = await page.locator('body').innerText()
    log(
      'esign-modal',
      /Send for Signature|Connect an e-signature|Select a transaction/i.test(sigText) ? 'PASS' : 'FAIL',
    )
    await page.keyboard.press('Escape')
    await page.waitForTimeout(300)
  } catch (err) {
    log('esign-modal', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // Transaction link from a card (All docs)
  try {
    await page.getByRole('button', { name: /^All docs/i }).first().click()
    await page.waitForTimeout(500)
  } catch (err) {
    log('transaction-link-tab', 'FAIL', err.message)
  }

  // Nested interactive: DocCard role=button wrapping buttons
  try {
    const nested = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('[role="button"][data-doc-id]')]
      return cards.filter((c) => c.querySelector('button')).length
    })
    log('a11y-nested-role-button', nested === 0 ? 'PASS' : 'FAIL', `${nested} cards wrap inner buttons`)
    const txOnCard = page.locator('[data-doc-id] a[href*="/transactions/"]')
    log('transaction-link-on-card', (await txOnCard.first().isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
  } catch (err) {
    log('a11y-nested-role-button', 'FAIL', err.message)
  }

  // Global search Cmd+K
  try {
    await page.keyboard.press('Control+k')
    await page.waitForTimeout(500)
    const palette = page.getByRole('dialog').or(page.getByPlaceholder(/search/i)).first()
    log('cmdk-opens', (await palette.isVisible().catch(() => false)) || /Open All Documents|Search/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search" i]').last()
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill('purchase')
      await page.waitForTimeout(1200)
      await shot(page, 'cmdk_search')
      log('cmdk-results', /Document|Transaction|No results/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
    }
    await page.keyboard.press('Escape')
    await page.waitForTimeout(200)
  } catch (err) {
    log('cmdk', 'FAIL', err.message)
    await page.keyboard.press('Escape').catch(() => {})
  }

  // Page-level search (spec §5.4)
  try {
    await page.goto(`${APP}/documents`, { waitUntil: 'domcontentloaded' })
    await waitForDocs(page)
    const pageSearch = page.getByLabel('Filter documents')
    log(
      'page-search',
      (await pageSearch.isVisible().catch(() => false)) ? 'PASS' : 'FAIL',
    )
    if (await pageSearch.isVisible().catch(() => false)) {
      await pageSearch.fill('zzzx-no-such-document-999')
      await page.waitForTimeout(400)
      log('search-empty', /No documents match your search/i.test(await page.locator('body').innerText()) ? 'PASS' : 'FAIL')
      log('url-sync-search', /[?&]q=/.test(page.url()) ? 'PASS' : 'FAIL', page.url())
      await page.getByRole('button', { name: /Clear search/i }).first().click()
      await page.waitForTimeout(300)
    }
  } catch (err) {
    log('page-search', 'FAIL', err.message)
  }

  // Typography
  try {
    const small = await page.evaluate(() => {
      const root = document.querySelector('h1')?.closest('.flex.h-full')
      if (!root) return []
      const out = []
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT)
      while (walker.nextNode()) {
        const el = walker.currentNode
        if (!(el instanceof HTMLElement)) continue
        const style = getComputedStyle(el)
        if (style.display === 'none' || style.visibility === 'hidden') continue
        const own = [...el.childNodes]
          .filter((n) => n.nodeType === Node.TEXT_NODE && n.textContent && n.textContent.trim())
          .map((n) => n.textContent.trim())
          .join(' ')
        if (!own) continue
        const fs = parseFloat(style.fontSize)
        if (Number.isFinite(fs) && fs < 12) {
          out.push({ fs: Math.round(fs * 10) / 10, text: own.slice(0, 60), tag: el.tagName.toLowerCase() })
        }
      }
      return out.slice(0, 25)
    })
    writeFileSync(path.join(OUT, 'tiny_text.json'), JSON.stringify(small, null, 2))
    log('a11y-min-12px', small.length === 0 ? 'PASS' : 'FAIL', small.slice(0, 8).map((s) => `${s.fs}px "${s.text}"`).join(' | '))
  } catch (err) {
    log('a11y-min-12px', 'FAIL', err.message)
  }

  // Hit targets on header Upload
  try {
    const uploadBox = await page.getByRole('button', { name: /Upload/i }).first().boundingBox()
    log(
      'a11y-upload-hit-target',
      uploadBox && uploadBox.height >= 40 ? 'PASS' : 'FAIL',
      uploadBox ? `${Math.round(uploadBox.width)}x${Math.round(uploadBox.height)}` : '',
    )
  } catch (err) {
    log('a11y-upload-hit-target', 'FAIL', err.message)
  }

  // Error banner retry — force by going while checking refresh works
  try {
    await page.getByRole('button', { name: /Refresh/i }).first().click()
    await page.waitForTimeout(800)
    log('refresh-action', stayOnDocs(page) ? 'PASS' : 'FAIL')
  } catch (err) {
    log('refresh-action', 'FAIL', err.message)
  }

  // Keyboard: tab to Upload
  try {
    await page.getByRole('button', { name: /Upload/i }).first().focus()
    await page.keyboard.press('Enter')
    await page.waitForTimeout(400)
    log('keyboard-upload', (await page.getByRole('dialog').isVisible().catch(() => false)) ? 'PASS' : 'FAIL')
    await page.keyboard.press('Escape')
  } catch (err) {
    log('keyboard-upload', 'FAIL', err.message)
  }

  // Mobile
  try {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(`${APP}/documents`, { waitUntil: 'domcontentloaded' })
    await waitForDocs(page)
    await dismissOverlays(page)
    await shot(page, 'docs_mobile')
    await dumpText(page, 'docs_mobile')
    log('mobile-upload-name', (await page.getByRole('button', { name: /Upload/i }).first().isVisible()) ? 'PASS' : 'FAIL')
    log(
      'mobile-send-for-sig-name',
      (await page.getByRole('button', { name: /Send for Sig/i }).first().isVisible()) ? 'PASS' : 'FAIL',
    )
    log(
      'mobile-restore',
      (await page.getByRole('button', { name: /Restore archived/i }).first().isVisible().catch(() => false))
        ? 'PASS'
        : 'FAIL',
      'hidden md:inline-flex',
    )
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 8,
    )
    log('mobile-no-h-overflow', overflow ? 'FAIL' : 'PASS')
  } catch (err) {
    log('mobile', 'FAIL', err.message)
  }

  const interesting = consoleErrors.filter(
    (e) => !/Download the React DevTools/i.test(e) && !/Failed to load resource/i.test(e),
  )
  log('console-errors', interesting.length === 0 ? 'PASS' : 'FAIL', interesting.slice(0, 8).join(' | '))
  log('page-errors', pageErrors.length === 0 ? 'PASS' : 'FAIL', pageErrors.slice(0, 4).join(' | '))
  const apiFails = failedRequests.filter(
    (u) => /\/api\/v1\//.test(u) && /\/documents|documents-priority-queue/.test(u),
  )
  log('api-4xx', apiFails.length === 0 ? 'PASS' : 'FAIL', apiFails.slice(0, 6).join(' | '))

  const summary = findings.reduce((acc, f) => {
    acc[f.result] = (acc[f.result] || 0) + 1
    return acc
  }, {})
  writeFileSync(
    path.join(OUT, 'findings.json'),
    JSON.stringify({ summary, findings, consoleErrors, pageErrors, failedRequests, qaLabel: QA_LABEL }, null, 2),
  )
  console.log('\nSUMMARY', summary)
  await browser.close()
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
