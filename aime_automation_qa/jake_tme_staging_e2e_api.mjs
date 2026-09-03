/**
 * Jake TME intelligence — staging E2E (API + document flow).
 * Creates fresh transactions and exercises new architecture features.
 * Does not Send mail or Run AI tasks overnight.
 *
 *   $env:QA_API='https://api.stage.velvetelves.com'
 *   $env:QA_APP='https://app.stage.velvetelves.com'
 *   $env:QA_EMAIL='crazyaidev20500519@gmail.com'
 *   $env:QA_PASSWORD='...'
 *   node jake_tme_staging_e2e_api.mjs
 */
import { mkdirSync, readFileSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { writePaPdf, writeAmendmentPdf } from './jake_tme_pdf_fixtures.mjs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const API = (process.env.QA_API || 'https://api.stage.velvetelves.com').replace(/\/$/, '')
const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const OUT = path.join(__dirname, 'artifacts_jake_tme_e2e')
mkdirSync(OUT, { recursive: true })

const STAMP = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 14)
const ACCEPT = '2026-09-01'
const CLOSE_A = '2026-10-15'
const CLOSE_B = '2026-11-01'

const findings = []
const scenarios = {}

function log(id, result, details = '') {
  findings.push({ id, result, details: String(details).slice(0, 6000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 900) : ''}`)
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
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = { raw: text.slice(0, 2000) }
  }
  if (!res.ok) {
    const err = new Error(`${method} ${pathname} → ${res.status} ${text.slice(0, 600)}`)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

function paText(address) {
  return `RESIDENTIAL PURCHASE AGREEMENT
Property: ${address}
Purchase Price: $425,000
Financing: Conventional
Date of Acceptance: ${ACCEPT}
Closing Date: ${CLOSE_A}
Possession Date: 2026-10-16
Earnest Money: $5,000 due within 3 business days
Inspection period ends: 2026-09-11
`
}

function amendmentText(newClosing = CLOSE_B) {
  return `AMENDMENT TO PURCHASE AGREEMENT
Date: 2026-09-03

The Closing Date in the Purchase Agreement is hereby amended and changed to ${newClosing}.
All other terms and conditions remain in full force and effect.

Buyer signature: ____________________
Seller signature: ____________________
`
}

function fuzzyAmendmentText() {
  return `AMENDMENT TO PURCHASE AGREEMENT
Date: 2026-09-03

Closing may occur on or about November 1, 2026, subject to lender approval and mutual agreement.
`
}

async function login() {
  const auth = await api('/api/v1/users/login', {
    method: 'POST',
    form: new URLSearchParams({ username: EMAIL, password: PASSWORD }).toString(),
  })
  if (auth.mfa_required) throw new Error('MFA required')
  return auth
}

async function uploadDoc(token, txId, fileName, docType, contents, mime = 'application/pdf') {
  const fd = new FormData()
  const body = contents instanceof Uint8Array || Buffer.isBuffer(contents) ? contents : contents
  fd.append('file', new Blob([body], { type: mime }), fileName)
  fd.append('transaction_id', txId)
  fd.append('doc_type', docType)
  fd.append('doc_label', fileName)
  return api('/api/v1/documents/upload', { method: 'POST', token, formData: fd })
}

async function parseDocBackground(token, docId, { timeoutMs = 420000 } = {}) {
  await api(`/api/v1/ai/parse-document/${docId}?background=true`, {
    method: 'POST',
    token,
    json: {},
  })
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    const st = await api(`/api/v1/ai/parse-document/${docId}/status`, { token })
    if (st.status === 'completed') {
      const conf = st.result?.confidence ?? st.result?.extracted?.overall_confidence
      const ocr = st.result?.extracted?._ocr
      if (ocr?.supported === false || (conf !== undefined && conf < 0.5)) {
        const err = new Error(
          st.result?.extracted?._review_reasons?.[0] || `low confidence ${conf}`,
        )
        err.status = 'low_quality'
        err.data = st
        throw err
      }
      return st
    }
    if (st.status === 'failed') {
      const err = new Error(st.error || 'parse failed')
      err.status = 'failed'
      err.data = st
      throw err
    }
    await new Promise((r) => setTimeout(r, 5000))
  }
  throw new Error(`parse timeout for ${docId}`)
}

async function resolveDocs(token, docIds) {
  return api('/api/v1/ai/resolve-documents', {
    method: 'POST',
    token,
    json: { document_ids: docIds },
  })
}

async function getPlan(token, txId) {
  return api(`/api/v1/transactions/${txId}/plan`, { token })
}

async function getNeedsYou(token) {
  return api('/api/v1/automation/needs-you', { token })
}

async function getTasks(token, txId) {
  return api(`/api/v1/tasks/transaction/${txId}?include_ai=true`, { token })
}

async function verifyDeadline(token, txId, decision) {
  return api(`/api/v1/transactions/${txId}/verify-deadline`, {
    method: 'POST',
    token,
    json: { decision },
  })
}

function prov(plan, field) {
  const tracking = plan.tracking_dates || []
  const core = plan.core_dates || []
  const t = tracking.find((x) => x.field_name === field || x.field === field)
  if (t?.provenance) return t.provenance
  const c = core.find((x) => x.field === field)
  return c?.provenance ?? null
}

function closingFromPlan(plan) {
  const row = (plan.core_dates || []).find((x) => x.field === 'closing_date')
  return row?.date || null
}

function findVerifyItem(items, txId) {
  return (items || []).find(
    (it) =>
      it.transaction_id === txId &&
      (it.block_code === 'amendment_date_confirm' ||
        /verify deadline/i.test(it.title || '') ||
        (it.date_changes && it.date_changes.length)),
  )
}

async function createBaseTx(token, label, overrides = {}) {
  const address = `${label} Jake TME E2E ${STAMP}`
  const tx = await api('/api/v1/transactions', {
    method: 'POST',
    token,
    json: {
      address,
      city: 'Austin',
      state: 'TX',
      zip_code: '78701',
      use_case: 'Buy-Fin',
      financing_type: 'Financed',
      representation_type: 'Buyer',
      purchase_price: 425000,
      earnest_money: 5000,
      contract_acceptance_date: ACCEPT,
      closing_date: CLOSE_A,
      possession_date: '2026-10-16',
      has_inspection: true,
      inspection_days: 10,
      status: 'Active',
      notes: `Jake TME E2E ${label} ${STAMP}`,
      ...overrides,
    },
  })
  await api(`/api/v1/transactions/${tx.id}/parties`, {
    method: 'POST',
    token,
    json: {
      party_role: 'buyer',
      full_name: `${label} Buyer`,
      email: EMAIL.replace('@', `+${label.toLowerCase()}@`),
      is_primary: true,
      source: 'manual',
    },
  })
  await api(`/api/v1/transactions/${tx.id}/tasks/generate`, { method: 'POST', token, json: {} }).catch(
    (e) => {
      if (e.status !== 409) throw e
    },
  )
  return tx
}

async function uploadParsePair(token, txId, address, { fuzzy = false, paPdfPath = null } = {}) {
  const paPath = paPdfPath || path.join(OUT, `pa-${txId.slice(0, 8)}.pdf`)
  const amdPath = path.join(OUT, `amd-${txId.slice(0, 8)}.pdf`)
  if (!paPdfPath) {
    writePaPdf(paPath, {
      address,
      accept: 'September 1, 2026',
      close: 'October 15, 2026',
    })
  }
  writeAmendmentPdf(amdPath, { newClose: 'November 1, 2026', fuzzy })
  const paBuf = paPdfPath ? readFileSync(paPdfPath) : readFileSync(paPath)
  const amdBuf = readFileSync(amdPath)
  const pa = await uploadDoc(token, txId, 'Purchase-Agreement.pdf', 'purchase_agreement', paBuf)
  const amd = await uploadDoc(
    token,
    txId,
    fuzzy ? 'Amendment-Fuzzy.pdf' : 'Amendment-Closing.pdf',
    'amendment',
    amdBuf,
  )
  let paParse = 'skip'
  let amdParse = 'skip'
  try {
    await parseDocBackground(token, pa.id)
    paParse = 'ok'
  } catch (e) {
    paParse = `fail:${e.message?.slice(0, 120)}`
  }
  try {
    await parseDocBackground(token, amd.id)
    amdParse = 'ok'
  } catch (e) {
    amdParse = `fail:${e.message?.slice(0, 120)}`
  }
  let resolution = null
  try {
    resolution = await resolveDocs(token, [pa.id, amd.id])
  } catch (e) {
    resolution = { error: e.message, status: e.status }
  }
  return { pa, amd, paParse, amdParse, resolution }
}

async function run() {
  const auth = await login()
  const token = auth.access_token
  log('login', 'PASS', auth.user?.email)

  const settingsBefore = await api('/api/v1/automation/settings', { token })
  const obBefore = settingsBefore.obligation_autonomy

  // ── S1: fresh create → verified provenance on wizard dates ──
  const s1 = await createBaseTx(token, 'Prov')
  const plan1 = await getPlan(token, s1.id)
  const closingProv = prov(plan1, 'closing_date')
  const acceptProv = prov(plan1, 'contract_acceptance_date')
  log(
    's1.wizard_verified_provenance',
    closingProv === 'verified' && acceptProv === 'verified' ? 'PASS' : 'FAIL',
    `closing=${closingProv} acceptance=${acceptProv}`,
  )
  log(
    's1.stages_and_next',
    plan1.header?.tme_stages_line && plan1.header?.next_action?.title ? 'PASS' : 'WARN',
    JSON.stringify({ stages: plan1.header?.tme_stages_line, next: plan1.header?.next_action?.title }),
  )
  scenarios.s1_provenance = { id: s1.id, address: s1.address, closingProv, acceptProv }

  // ── S2: You confirm + amendment → Verify deadline pending ──
  await api('/api/v1/automation/settings', {
    method: 'PUT',
    token,
    json: { obligation_autonomy: 'manual' },
  })
  const s2 = await createBaseTx(token, 'YouConfirm')
  await api(`/api/v1/transactions/${s2.id}/automation`, {
    method: 'PUT',
    token,
    json: { posture: 'autopilot', obligation_autonomy: 'inherit' },
  })
  const docs2 = await uploadParsePair(token, s2.id, s2.address)
  const plan2 = await getPlan(token, s2.id)
  const ny2 = await getNeedsYou(token)
  const verify2 = findVerifyItem(ny2.items, s2.id)
  const tasks2 = await getTasks(token, s2.id)
  const verifyTask2 = tasks2.find(
    (t) =>
      t.name === 'Verify deadline' ||
      t.metadata_json?.ai_needs_user?.code === 'amendment_date_confirm',
  )
  log(
    's2.autopilot_not_trusted_dates',
    plan2.automation?.posture === 'autopilot' &&
      displayOb(plan2.automation?.obligation_autonomy) === 'manual'
      ? 'PASS'
      : 'FAIL',
    JSON.stringify(plan2.automation),
  )
  log(
    's2.verify_deadline_pending',
    verify2 || verifyTask2 ? 'PASS' : 'FAIL',
    `needs_you=${Boolean(verify2)} task=${verifyTask2?.name || 'none'} parse=${docs2.amdParse}`,
  )
  log(
    's2.closing_unchanged_before_confirm',
    closingFromPlan(plan2) === CLOSE_A ? 'PASS' : 'FAIL',
    `closing=${closingFromPlan(plan2)} expected=${CLOSE_A}`,
  )
  scenarios.s2_you_confirm = {
    id: s2.id,
    address: s2.address,
    verifyItem: verify2,
    docs2,
    closingBefore: closingFromPlan(plan2),
  }

  // ── S2b: amendment-only after intake (clear supersede) ──
  const s2b = await createBaseTx(token, 'AmendOnly')
  await api(`/api/v1/transactions/${s2b.id}/automation`, {
    method: 'PUT',
    token,
    json: { obligation_autonomy: 'inherit' },
  })
  const amdOnlyPath = path.join(OUT, `amd-only-${s2b.id.slice(0, 8)}.pdf`)
  writeAmendmentPdf(amdOnlyPath, { newClose: CLOSE_B })
  const amdOnly = await uploadDoc(token, s2b.id, 'Amendment-Only.pdf', 'amendment', readFileSync(amdOnlyPath))
  let amdOnlyParse = 'skip'
  try {
    await parseDocBackground(token, amdOnly.id)
    amdOnlyParse = 'ok'
  } catch (e) {
    amdOnlyParse = `fail:${e.message?.slice(0, 120)}`
  }
  let resOnly = null
  try {
    resOnly = await resolveDocs(token, [amdOnly.id])
  } catch (e) {
    resOnly = { error: e.message }
  }
  const plan2b = await getPlan(token, s2b.id)
  const ny2b = await getNeedsYou(token)
  const verify2b = findVerifyItem(ny2b.items, s2b.id)
  log(
    's2b.amendment_only_verify',
    verify2b ? 'PASS' : 'FAIL',
    `parse=${amdOnlyParse} closing=${closingFromPlan(plan2b)}`,
  )
  scenarios.s2b_amend_only = { id: s2b.id, address: s2b.address, verify2b, resOnly, amdOnlyParse }
  if (verify2b) {
    try {
      await verifyDeadline(token, s2b.id, 'confirm')
      const plan2c = await getPlan(token, s2b.id)
      log(
        's2b.confirm_applies',
        closingFromPlan(plan2c) === CLOSE_B ? 'PASS' : 'FAIL',
        closingFromPlan(plan2c),
      )
      scenarios.s3_confirm = { closingAfter: closingFromPlan(plan2c), provAfter: prov(plan2c, 'closing_date') }
    } catch (e) {
      log('s2b.confirm_applies', 'FAIL', e.message)
    }
  }

  // ── S3: Confirm applies new date ──
  if (verify2 || verifyTask2) {
    try {
      await verifyDeadline(token, s2.id, 'confirm')
      const plan2b = await getPlan(token, s2.id)
      const closingAfter = closingFromPlan(plan2b)
      const provAfter = prov(plan2b, 'closing_date')
      log(
        's3.confirm_applies_closing',
        closingAfter === CLOSE_B ? 'PASS' : 'FAIL',
        `closing=${closingAfter} expected=${CLOSE_B}`,
      )
      log(
        's3.confirmed_provenance_after_confirm',
        provAfter === 'verified' ? 'PASS' : 'WARN',
        `provenance=${provAfter}`,
      )
      scenarios.s3_confirm = { closingAfter, provAfter }
    } catch (e) {
      log('s3.confirm_applies_closing', 'FAIL', e.message)
    }
  } else {
    log('s3.confirm_applies_closing', 'SKIP', 'no verify card from amendment parse')
  }

  // ── S4: Keep current leaves date ──
  const s4 = await createBaseTx(token, 'KeepCurrent')
  const willowPdf = path.join(__dirname, '../demo_video_testing/willowbrook_purchase_agreement.pdf')
  const docs4 = await uploadParsePair(token, s4.id, s4.address, {
    paPdfPath: willowPdf,
  })
  const ny4 = await getNeedsYou(token)
  const verify4 = findVerifyItem(ny4.items, s4.id)
  if (verify4) {
    try {
      await verifyDeadline(token, s4.id, 'keep')
      const plan4 = await getPlan(token, s4.id)
      log(
        's4.keep_current_date',
        closingFromPlan(plan4) === CLOSE_A ? 'PASS' : 'FAIL',
        `closing=${closingFromPlan(plan4)}`,
      )
      scenarios.s4_keep = { id: s4.id, address: s4.address, docs4 }
    } catch (e) {
      log('s4.keep_current_date', 'FAIL', e.message)
    }
  } else {
    log('s4.keep_current_date', 'SKIP', `parse=${docs4.amdParse}`)
    scenarios.s4_keep = { id: s4.id, address: s4.address, docs4 }
  }

  // ── S5: Trusted explicit amendment auto-applies ──
  const s5 = await createBaseTx(token, 'TrustedAuto')
  await api(`/api/v1/transactions/${s5.id}/automation`, {
    method: 'PUT',
    token,
    json: { obligation_autonomy: 'trusted' },
  })
  const docs5 = await uploadParsePair(token, s5.id, s5.address)
  const plan5 = await getPlan(token, s5.id)
  const ny5 = await getNeedsYou(token)
  const verify5 = findVerifyItem(ny5.items, s5.id)
  const closing5 = closingFromPlan(plan5)
  log(
    's5.trusted_auto_apply',
    closing5 === CLOSE_B && !verify5 ? 'PASS' : verify5?.date_changes?.[0]?.conflict ? 'PASS' : 'FAIL',
    `closing=${closing5} verify=${Boolean(verify5)} conflict=${verify5?.date_changes?.[0]?.conflict}`,
  )
  scenarios.s5_trusted = { id: s5.id, address: s5.address, closing5, verify5, docs5 }

  // ── S6: Trusted fuzzy still waits ──
  const s6 = await createBaseTx(token, 'TrustedFuzzy')
  await api(`/api/v1/transactions/${s6.id}/automation`, {
    method: 'PUT',
    token,
    json: { obligation_autonomy: 'trusted' },
  })
  const docs6 = await uploadParsePair(token, s6.id, s6.address, { fuzzy: true })
  const plan6 = await getPlan(token, s6.id)
  const ny6 = await getNeedsYou(token)
  const verify6 = findVerifyItem(ny6.items, s6.id)
  log(
    's6.trusted_fuzzy_waits',
    verify6 || closingFromPlan(plan6) === CLOSE_A ? 'PASS' : 'FAIL',
    `closing=${closingFromPlan(plan6)} verify=${Boolean(verify6)} parse=${docs6.amdParse}`,
  )
  scenarios.s6_fuzzy = { id: s6.id, address: s6.address, docs6, verify6 }

  // ── S7: Dual Q1 task rows ──
  const s7 = await createBaseTx(token, 'Dual', {
    use_case: 'Both-Fin',
    representation_type: 'Dual',
    address: `Dual Jake TME E2E ${STAMP}`,
  })
  await api(`/api/v1/transactions/${s7.id}/parties`, {
    method: 'POST',
    token,
    json: {
      party_role: 'seller',
      full_name: 'Dual Seller',
      email: EMAIL.replace('@', '+dualseller@'),
      is_primary: true,
      source: 'manual',
    },
  })
  await api(`/api/v1/transactions/${s7.id}/tasks/generate`, { method: 'POST', token, json: {} }).catch(
    (e) => {
      if (e.status !== 409) throw e
    },
  )
  const tasks7 = await getTasks(token, s7.id)
  const deliverTitle = tasks7.filter((t) => /^Deliver Title$/i.test(t.name || ''))
  const utilityBuyer = tasks7.find((t) => /Deliver Utility Info/i.test(t.name) && t.target === 'Buyer')
  const bothTitle305 = tasks7.find((t) => (t.metadata_json?.legacy_task_id ?? t.legacy_task_id) === 305)
  log(
    's7.dual_deliver_title_per_side',
    deliverTitle.length >= 2 ? 'PASS' : 'FAIL',
    deliverTitle.map((t) => `${t.name}:${t.target}`).join('; '),
  )
  log('s7.dual_utility_buyer', utilityBuyer ? 'PASS' : 'FAIL')
  log('s7.no_both_only_305', bothTitle305 ? 'FAIL' : 'PASS')
  scenarios.s7_dual = { id: s7.id, address: s7.address, deliverTitle: deliverTitle.map((t) => t.target) }

  // ── S8: party flags persist ──
  const parties8 = await api(`/api/v1/transactions/${s7.id}/parties`, { token })
  const list8 = Array.isArray(parties8) ? parties8 : parties8.items || parties8.parties || []
  const buyer8 = list8.find((p) => p.party_role === 'buyer')
  const buyerId = buyer8?.id
  if (buyerId) {
    await api(`/api/v1/transactions/${s7.id}/parties/${buyerId}`, {
      method: 'PUT',
      token,
      json: { is_decision_maker: false },
    })
    const after = await api(`/api/v1/transactions/${s7.id}/parties`, { token })
    const listAfter = Array.isArray(after) ? after : after.items || after.parties || []
    const buyerAfter = listAfter.find((p) => p.id === buyerId)
    log(
      's8.decision_maker_toggle',
      buyerAfter && buyerAfter.is_decision_maker === false ? 'PASS' : 'FAIL',
    )
    await api(`/api/v1/transactions/${s7.id}/parties/${buyerId}`, {
      method: 'PUT',
      token,
      json: { is_decision_maker: true },
    })
  } else {
    log('s8.decision_maker_toggle', 'FAIL', 'buyer party missing')
  }
  scenarios.s8_contacts = { id: s7.id }

  // ── S9: Terminated → LSE handoff + Next line ──
  const s9 = await createBaseTx(token, 'Terminated')
  await api(`/api/v1/transactions/${s9.id}/status`, {
    method: 'PUT',
    token,
    json: { status: 'Terminated' },
  })
  const plan9 = await getPlan(token, s9.id)
  log(
    's9.lse_handoff',
    plan9.lse_handoff?.offer_lse === true && plan9.lse_handoff?.silent_listing_forbidden === true
      ? 'PASS'
      : 'FAIL',
    JSON.stringify(plan9.lse_handoff),
  )
  log(
    's9.terminated_next_line',
    plan9.header?.status === 'Terminated' && plan9.header?.next_action?.title ? 'FAIL' : 'PASS',
    JSON.stringify(plan9.header?.next_action),
  )
  scenarios.s9_terminated = { id: s9.id, address: s9.address, next: plan9.header?.next_action }

  // restore workspace dates default
  await api('/api/v1/automation/settings', {
    method: 'PUT',
    token,
    json: { obligation_autonomy: obBefore || 'manual' },
  })

  const failed = findings.filter((f) => f.result === 'FAIL').length
  const payload = {
    stamp: STAMP,
    email: EMAIL,
    api: API,
    findings,
    scenarios,
    failed,
  }
  writeFileSync(path.join(OUT, 'e2e_api.json'), JSON.stringify(payload, null, 2))
  writeFileSync(path.join(OUT, 'seed.json'), JSON.stringify(scenarios, null, 2))
  console.log(`DONE failed=${failed} scenarios=${Object.keys(scenarios).length}`)
  process.exit(failed ? 1 : 0)
}

function displayOb(v) {
  return v === 'trusted' ? 'trusted' : 'manual'
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
