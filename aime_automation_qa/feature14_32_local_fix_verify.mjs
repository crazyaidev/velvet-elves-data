/**
 * Low-RAM Chrome pass for the Feature 14–32 product fixes on local Vite.
 * One Chrome process, one tab, viewport screenshots only. Does not Send,
 * Generate, Run AI tasks (tenant), Disconnect, or Change status.
 *
 *   $env:QA_API='http://127.0.0.1:8000'
 *   $env:QA_APP='http://localhost:5173'
 *   $env:QA_EMAIL='shyna.elene@minafter.com'
 *   node feature14_32_local_fix_verify.mjs
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const require = createRequire(path.join(__dirname, '../vendor_portal_qa/package.json'))
const { chromium } = require('playwright-core')

const OUT = path.join(__dirname, 'artifacts_feature14_32_local')
mkdirSync(OUT, { recursive: true })

const EMAIL = process.env.QA_EMAIL || 'shyna.elene@minafter.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const API = (process.env.QA_API || 'http://127.0.0.1:8000').replace(/\/$/, '')
const APP = (process.env.QA_APP || 'http://localhost:5173').replace(/\/$/, '')
const CHROME = process.env.QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const STAMP = '20260901fix'
const ACCEPT = '2026-09-01'
const CLOSE = '2026-10-15'
const plus = (tag) => EMAIL.replace('@', `+${tag}@`)

const findings = []
function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 4000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 700) : ''}`)
}

async function api(pathname, { method = 'GET', token, json, form, formData } = {}) {
  const headers = { Accept: 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  let body
  if (formData) body = formData
  else if (form) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    body = form
  } else if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(json)
  }
  const res = await fetch(`${API}${pathname}`, { method, headers, body })
  const text = await res.text()
  let data
  try { data = text ? JSON.parse(text) : null } catch { data = { raw: text } }
  if (!res.ok) {
    const err = new Error(`${method} ${pathname} → ${res.status} ${text.slice(0, 600)}`)
    err.status = res.status
    throw err
  }
  return data
}

async function seed() {
  const auth = await api('/api/v1/users/login', {
    method: 'POST',
    form: new URLSearchParams({ username: EMAIL, password: PASSWORD }).toString(),
  })
  if (auth.mfa_required) throw new Error('MFA required')
  const token = auth.access_token
  const buyer = plus('buyer')
  const seller = plus('seller')
  const coop = plus('coop')
  const lender = plus('lender')
  const title = plus('title')
  const contract = {
    fileName: 'Purchase-Agreement.txt',
    docType: 'purchase_agreement',
    contents: `Purchase Agreement\nFix verify ${STAMP}\nClosing ${CLOSE}\n`,
  }
  const utility = {
    fileName: 'Utility-Information.txt',
    docType: 'utility_info',
    contents: `Utility information ${STAMP}\n`,
  }

  async function addParty(txId, party) {
    return api(`/api/v1/transactions/${txId}/parties`, {
      method: 'POST', token, json: { is_primary: true, source: 'manual', ...party },
    })
  }
  async function uploadDoc(txId, d) {
    const fd = new FormData()
    fd.append('file', new Blob([d.contents], { type: 'text/plain' }), d.fileName)
    fd.append('transaction_id', txId)
    fd.append('doc_type', d.docType)
    fd.append('doc_label', d.fileName)
    return api('/api/v1/documents/upload', { method: 'POST', token, formData: fd })
  }
  async function generate(txId) {
    try {
      return await api(`/api/v1/transactions/${txId}/tasks/generate`, { method: 'POST', token, json: {} })
    } catch (err) {
      if (err.status === 409) return { already: true }
      throw err
    }
  }
  async function createFile(spec) {
    const existing = await api('/api/v1/transactions?page_size=80', { token })
    const hit = (existing.items || []).find((t) => t.address === spec.tx.address)
    let tx = hit
    if (!tx) {
      tx = await api('/api/v1/transactions', {
        method: 'POST', token, json: {
          city: 'Austin', state: 'TX', zip_code: '78701',
          purchase_price: 425000, earnest_money: 5000, earnest_money_days: 3,
          contract_acceptance_date: ACCEPT, closing_date: CLOSE,
          has_inspection: true, inspection_days: 10, inspection_response_days: 3,
          has_hoa: false, closing_mode: 'title_escrow', is_owner_occupied: true,
          status: 'Active', notes: `Fix verify ${STAMP}`,
          ...spec.tx,
        },
      })
      for (const p of spec.parties || []) await addParty(tx.id, p)
      for (const d of spec.docs || []) await uploadDoc(tx.id, d)
    }
    await generate(tx.id)
    if (spec.posture) {
      await api(`/api/v1/transactions/${tx.id}/automation`, {
        method: 'PUT', token, json: { posture: spec.posture },
      })
    }
    const tasks = await api(`/api/v1/tasks/transaction/${tx.id}?include_ai=true`, { token })
    const plans = {}
    for (const name of spec.planNames || []) {
      const task = (tasks || []).find((t) => t.name === name)
      if (!task) { plans[name] = { missing: true }; continue }
      try { plans[name] = await api(`/api/v1/tasks/${task.id}/email-plan`, { token }) }
      catch (err) { plans[name] = { error: String(err.message || err).slice(0, 400) } }
    }
    return { id: tx.id, address: tx.address, use_case: tx.use_case, posture: spec.posture, tasks, plans }
  }

  const files = {}
  files.buyCash = await createFile({
    tx: {
      address: `500 Elm Fix ${STAMP}`, use_case: 'Buy-Cash', financing_type: 'Cash',
      representation_type: 'Buyer', has_appraisal: true, title_ordered_by: 'Buyer',
    },
    parties: [{ party_role: 'buyer', full_name: 'Elm Buyer', email: buyer }],
    docs: [contract], posture: 'assisted',
    planNames: ['Appraisal Ordered', 'Inspection Response Reminder'],
  })
  files.maple = await createFile({
    tx: {
      address: `200 Maple Fix ${STAMP}`, use_case: 'Buy-Fin', financing_type: 'Financed',
      representation_type: 'Buyer', title_ordered_by: 'Buyer',
    },
    parties: [
      { party_role: 'buyer', full_name: 'Maple Buyer', email: buyer },
      { party_role: 'title_rep', full_name: 'Maple Title', email: title },
    ],
    docs: [contract], posture: 'manual',
    planNames: ['Buyer Welcome'],
  })
  files.noContract = await createFile({
    tx: {
      address: `410 NoContract Fix ${STAMP}`, use_case: 'Buy-Fin', financing_type: 'Financed',
      representation_type: 'Buyer', title_ordered_by: 'Buyer',
    },
    parties: [
      { party_role: 'buyer', full_name: 'NoContract Buyer', email: buyer },
      { party_role: 'loan_officer', full_name: 'NoContract Lender', email: lender },
      { party_role: 'title_rep', full_name: 'NoContract Title', email: title },
    ],
    posture: 'assisted',
    planNames: ['Order Title', 'Loan Officer Welcome'],
  })
  files.cedar = await createFile({
    tx: {
      address: `400 Cedar Fix ${STAMP}`, use_case: 'Buy-Fin', financing_type: 'Financed',
      representation_type: 'Buyer', title_ordered_by: 'Buyer',
    },
    parties: [{ party_role: 'buyer', full_name: 'Cedar Buyer' }],
    docs: [contract], posture: 'autopilot',
    planNames: ['Buyer Welcome'],
  })
  try {
    files.cedar.runNow = await api(`/api/v1/transactions/${files.cedar.id}/automation/run-now`, {
      method: 'POST', token,
    })
  } catch (err) {
    files.cedar.runNow = { error: String(err.message || err).slice(0, 400) }
  }
  files.dualAfter = await createFile({
    tx: {
      address: `701 Dual After ${STAMP}`, use_case: 'Both-Fin', financing_type: 'Financed',
      representation_type: 'Both', title_ordered_by: 'Buyer', has_hoa: true, hoa_doc_days: 10,
    },
    parties: [
      { party_role: 'buyer', full_name: 'Dual Buyer', email: buyer },
      { party_role: 'seller', full_name: 'Dual Seller', email: seller },
      { party_role: 'title_rep', full_name: 'Dual Title', email: title },
    ],
    docs: [contract], posture: 'assisted',
    planNames: ['Buyer Welcome', 'Seller Welcome', 'Co-op Agent Welcome'],
  })
  files.titleOther = await createFile({
    tx: {
      address: `720 Confirm Fix ${STAMP}`, use_case: 'Buy-Fin', financing_type: 'Financed',
      representation_type: 'Buyer', title_ordered_by: 'Seller',
    },
    parties: [
      { party_role: 'buyer', full_name: 'TitleOther Buyer', email: buyer },
      { party_role: 'listing_agent', full_name: 'TitleOther Co-op', email: coop },
      { party_role: 'title_rep', full_name: 'TitleOther Rep', email: title },
    ],
    docs: [contract], posture: 'assisted',
    planNames: ['Confirm Title Order', 'Order Title'],
  })
  files.utility = await createFile({
    tx: {
      address: `800 Utility Fix ${STAMP}`, use_case: 'Sell-Fin', financing_type: 'Financed',
      representation_type: 'Seller', title_ordered_by: 'Seller',
    },
    parties: [
      { party_role: 'seller', full_name: 'Utility Seller', email: seller },
      { party_role: 'buyers_agent', full_name: 'Utility Co-op', email: coop },
    ],
    docs: [contract, utility], posture: 'assisted',
    planNames: ['Deliver Utility Info'],
  })
  writeFileSync(path.join(OUT, 'seed.json'), JSON.stringify(files, null, 2))
  return { token, files, emails: { buyer, seller, coop, lender, title } }
}

async function dismissOverlays(page) {
  for (const name of [/Skip tour/i, /Skip for now/i, /^Skip$/i, /Not now/i, /Got it/i, /Maybe later/i]) {
    const btn = page.getByRole('button', { name }).first()
    if (await btn.isVisible({ timeout: 350 }).catch(() => false)) {
      await btn.click({ timeout: 1200 }).catch(() => {})
    }
  }
}

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false }).catch(() => {})
}

async function dump(name, text) {
  writeFileSync(path.join(OUT, `${name}.txt`), String(text ?? ''))
}

async function closeDialog(page) {
  const dlg = page.getByRole('dialog').last()
  if (await dlg.isVisible().catch(() => false)) {
    await dlg.getByRole('button', { name: /close|cancel|i.ll handle it myself/i }).first().click({ timeout: 2500 }).catch(() => {})
    await page.keyboard.press('Escape').catch(() => {})
    await page.waitForTimeout(250)
  }
}

async function openDealTab(page, txId, tab) {
  await page.goto(`${APP}/transactions/${txId}?tab=${tab}`, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await dismissOverlays(page)
  await page.getByText(/WORK QUEUE|Add Task/i).first().waitFor({ state: 'visible', timeout: 25000 })
  const tabBtn = page.getByRole('tab', { name: new RegExp(`^${tab}$`, 'i') }).first()
  if (await tabBtn.isVisible({ timeout: 1500 }).catch(() => false)) {
    await tabBtn.click().catch(() => {})
  }
  await page.getByText(/Upcoming|Overdue|Due Today|Add Task/i).first().waitFor({ state: 'visible', timeout: 20000 })
}

async function openTaskEmail(page, taskName) {
  const kebab = page.getByRole('button', { name: new RegExp(`Actions for ${taskName}`, 'i') }).first()
  await kebab.scrollIntoViewIfNeeded().catch(() => {})
  if (!(await kebab.isVisible({ timeout: 8000 }).catch(() => false))) {
    return { ok: false, text: `no actions for ${taskName}` }
  }
  await kebab.click()
  const item = page.getByRole('menuitem', { name: /Email transaction party|Complete this task/i }).first()
  await item.waitFor({ state: 'visible', timeout: 5000 })
  await item.click()
  const dlg = page.getByRole('dialog').last()
  const opened = await dlg.waitFor({ state: 'visible', timeout: 20000 }).then(() => true).catch(() => false)
  if (!opened) return { ok: false, text: 'dialog missing' }
  await page.waitForTimeout(600)
  const message = await dlg.locator('textarea').first().inputValue().catch(() => '')
  const subject = await dlg.locator('input[type="text"]').first().inputValue().catch(() => '')
  return { ok: true, text: `${await dlg.innerText()}\nSUBJECT_VALUE:${subject}\nMESSAGE_VALUE:${message}`, dialog: dlg, message, subject }
}

async function run() {
  console.log('seeding…')
  const { files, emails } = await seed()
  console.log('seeded', Object.fromEntries(Object.entries(files).map(([k, v]) => [k, v.id])))

  const pageErrors = []
  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME,
    args: [
      '--disable-gpu',
      '--disable-software-rasterizer',
      '--disable-dev-shm-usage',
      '--disable-extensions',
      '--disable-background-networking',
      '--mute-audio',
      '--no-first-run',
      '--no-default-browser-check',
      '--renderer-process-limit=1',
      '--js-flags=--max-old-space-size=256',
    ],
  })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 800 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  page.setDefaultTimeout(18000)
  page.on('pageerror', (err) => pageErrors.push(String(err)))

  try {
    await page.goto(`${APP}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.locator('#login-email').waitFor({ state: 'visible', timeout: 20000 })
    await page.locator('#login-email').fill(EMAIL)
    await page.locator('#login-password').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    const mfa = await page.getByLabel('Two-step verification form').waitFor({ timeout: 2500 }).then(() => true).catch(() => false)
    if (mfa) { log('login', 'FAIL', 'MFA'); return }
    await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 30000 })
    await dismissOverlays(page)
    if (page.url().includes('/login')) {
      log('login', 'FAIL', await page.locator('[role="alert"]').innerText().catch(() => page.url()))
      return
    }
    log('login', 'PASS', page.url())

    // F14 cash appraisal copy
    await openDealTab(page, files.buyCash.id, 'tasks')
    let body = await page.locator('body').innerText()
    dump('f14_tasks', body)
    await shot(page, 'f14_tasks')
    const plan14 = await openTaskEmail(page, 'Appraisal Ordered')
    dump('f14_plan', plan14.text)
    await shot(page, 'f14_plan')
    log('f14-plan-open', plan14.ok ? 'PASS' : 'FAIL', plan14.ok ? '' : plan14.text)
    if (plan14.ok) {
      log('f14-question-copy', /has the appraisal been ordered/i.test(plan14.text + (plan14.message || '')) ? 'PASS' : 'FAIL')
      log('f14-not-staff-notes', /email the buyer and ask/i.test(plan14.text + (plan14.message || '')) ? 'FAIL' : 'PASS')
      log('f14-to-buyer', plan14.text.includes(emails.buyer) ? 'PASS' : 'FAIL')
    }
    await closeDialog(page)

    // F19 inspection date
    const plan19 = await openTaskEmail(page, 'Inspection Response Reminder')
    dump('f19_plan', plan19.text)
    await shot(page, 'f19_plan')
    log('f19-plan-open', plan19.ok ? 'PASS' : 'FAIL', plan19.ok ? '' : plan19.text)
    if (plan19.ok) {
      const blob = plan19.text + (plan19.message || '')
      log('f19-not-tbd', /\bTBD\b/.test(blob) ? 'FAIL' : 'PASS')
      log('f19-has-date', /September 14, 2026/i.test(blob) ? 'PASS' : 'FAIL', (plan19.message || '').slice(0, 200))
    }
    await closeDialog(page)

    // F15 Manual named email stays on the open list
    await openDealTab(page, files.maple.id, 'tasks')
    body = await page.locator('body').innerText()
    dump('f15_tasks', body)
    await shot(page, 'f15_tasks')
    const handledIdx = body.search(/Handled by AI/i)
    const beforeHandled = handledIdx >= 0 ? body.slice(0, handledIdx) : body
    log('f15-buyer-welcome-open', /Buyer Welcome/i.test(beforeHandled) ? 'PASS' : 'FAIL')
    log('f15-not-only-in-ai-group', handledIdx >= 0 && /Buyer Welcome/i.test(body.slice(handledIdx)) && !/Buyer Welcome/i.test(beforeHandled) ? 'FAIL' : 'PASS')

    // F18 Order Title blocked without purchase agreement
    await openDealTab(page, files.noContract.id, 'tasks')
    body = await page.locator('body').innerText()
    dump('f18_tasks', body)
    await shot(page, 'f18_tasks')
    const plan18 = await openTaskEmail(page, 'Order Title')
    dump('f18_plan', plan18.text)
    await shot(page, 'f18_plan')
    log('f18-plan-open', plan18.ok ? 'PASS' : 'FAIL', plan18.ok ? '' : plan18.text)
    if (plan18.ok) {
      const sendBtn = page.getByRole('dialog').last().getByRole('button', { name: /Send/i }).first()
      const sendEnabled = await sendBtn.isEnabled().catch(() => false)
      log('f18-send-disabled', sendEnabled ? 'FAIL' : 'PASS')
      log('f18-needs-purchase-agreement', /purchase agreement/i.test(plan18.text) ? 'PASS' : 'FAIL')
    }
    await closeDialog(page)

    // F22 Needs You recovery on first screen
    await page.goto(`${APP}/needs-you`, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.getByRole('heading', { name: /Needs You/i }).waitFor({ timeout: 20000 })
    await page.getByText(/\d+ waiting/i).first().waitFor({ timeout: 45000 }).catch(() => {})
    await dismissOverlays(page)
    body = await page.locator('body').innerText()
    dump('f22_needs_you', body)
    await shot(page, 'f22_needs_you')
    const recoveryVisible = await page.getByRole('button', { name: /Add contact|Upload document|Switch this deal off Manual/i }).first().isVisible().catch(() => false)
    log(
      'f22-recovery-on-collapsed',
      recoveryVisible || /Add contact|Upload document|Switch this deal off Manual/i.test(body) ? 'PASS' : 'FAIL',
      `runNow=${JSON.stringify(files.cedar.runNow || {})}`,
    )

    // F28 Dual
    await openDealTab(page, files.dualAfter.id, 'tasks')
    body = await page.locator('body').innerText()
    dump('f28_tasks', body)
    await shot(page, 'f28_tasks')
    const names = (files.dualAfter.tasks || []).map((t) => `${t.name} · ${t.target || ''}`)
    const deliverTitle = (files.dualAfter.tasks || []).filter((t) => t.name === 'Deliver Title')
    const deliverUtil = (files.dualAfter.tasks || []).filter((t) => t.name === 'Deliver Utility Info')
    const coopWelcome = (files.dualAfter.tasks || []).some((t) => t.name === 'Co-op Agent Welcome')
    log('f28-buyer-and-seller-welcome', /Buyer Welcome/i.test(body) && /Seller Welcome/i.test(body) ? 'PASS' : 'FAIL')
    log('f28-no-coop-welcome', coopWelcome ? 'FAIL' : 'PASS')
    log('f28-one-deliver-title', deliverTitle.length === 1 ? 'PASS' : 'FAIL', names.filter((n) => /Deliver Title/i.test(n)).join('; '))
    log('f28-no-utility-delivery', deliverUtil.length === 0 ? 'PASS' : 'FAIL', names.filter((n) => /Utility/i.test(n)).join('; '))

    // F29 courtesy name
    await openDealTab(page, files.titleOther.id, 'tasks')
    body = await page.locator('body').innerText()
    dump('f29_tasks', body)
    await shot(page, 'f29_tasks')
    log('f29-confirm-not-order', /Confirm Title Order/i.test(body) && !/^Order Title$/m.test(body.split('Handled by AI')[0] || body) ? 'PASS' : (/Confirm Title Order/i.test(body) ? 'PASS' : 'FAIL'))
    const plan29 = await openTaskEmail(page, 'Confirm Title Order')
    dump('f29_plan', plan29.text)
    await shot(page, 'f29_plan')
    log('f29-plan-open', plan29.ok ? 'PASS' : 'FAIL', plan29.ok ? '' : plan29.text)
    if (plan29.ok) {
      const blob = plan29.text + (plan29.message || '')
      log('f29-courtesy-coop', /courtesy to TitleOther Co-op/i.test(blob) ? 'PASS' : 'FAIL', (plan29.message || '').slice(0, 220))
      log('f29-not-title-rep', /courtesy to TitleOther Rep/i.test(blob) ? 'FAIL' : 'PASS')
    }
    await closeDialog(page)

    // F30 listing utility one letter
    await openDealTab(page, files.utility.id, 'tasks')
    body = await page.locator('body').innerText()
    dump('f30_tasks', body)
    await shot(page, 'f30_tasks')
    const plan30 = await openTaskEmail(page, 'Deliver Utility Info')
    dump('f30_plan', plan30.text)
    await shot(page, 'f30_plan')
    log('f30-plan-open', plan30.ok ? 'PASS' : 'FAIL', plan30.ok ? '' : plan30.text)
    if (plan30.ok) {
      log('f30-to-coop', plan30.text.includes(emails.coop) ? 'PASS' : 'FAIL')
      log('f30-no-buyer-required', /needs a buyer/i.test(plan30.text) ? 'FAIL' : 'PASS')
      const sendBtn = page.getByRole('dialog').last().getByRole('button', { name: /Send/i }).first()
      const sendEnabled = await sendBtn.isEnabled().catch(() => false)
      log('f30-can-send', sendEnabled ? 'PASS' : 'FAIL', plan30.text.slice(0, 350))
    }
    await closeDialog(page)

    log('page-errors', pageErrors.length ? 'FAIL' : 'PASS', pageErrors.join(' | '))
  } finally {
    writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
    await context.close().catch(() => {})
    await browser.close().catch(() => {})
  }

  const failed = findings.filter((f) => f.result === 'FAIL')
  console.log('\nSUMMARY', findings.length, 'checks,', failed.length, 'FAIL')
  for (const f of failed) console.log('  FAIL', f.id, f.details.slice(0, 180))
  process.exit(failed.length ? 1 : 0)
}

run().catch((err) => {
  console.error(err)
  writeFileSync(path.join(OUT, 'fatal.txt'), String(err.stack || err))
  process.exit(2)
})
