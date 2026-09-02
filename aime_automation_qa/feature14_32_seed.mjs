/**
 * Seed Feature 14–32 files on staging. Does not send mail.
 *
 *   $env:QA_API='https://api.stage.velvetelves.com'
 *   $env:QA_EMAIL='crazyaidev20500519@gmail.com'
 *   $env:QA_PASSWORD='...'
 *   node feature14_32_seed.mjs
 */
import { writeFileSync, mkdirSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const API = (process.env.QA_API || 'https://api.stage.velvetelves.com').replace(/\/$/, '')
const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const OUT = path.join(__dirname, 'artifacts_feature14_32')
mkdirSync(OUT, { recursive: true })

const plus = (tag) => EMAIL.replace('@', `+${tag}@`)
const STAMP = new Date().toISOString().slice(0, 10).replace(/-/g, '')
const ACCEPT = '2026-09-01'
const CLOSE = '2026-10-15'

async function api(pathname, { method = 'GET', token, json, form, formData } = {}) {
  const headers = { Accept: 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  let body
  if (formData) {
    body = formData
  } else if (form) {
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
    data = { raw: text }
  }
  if (!res.ok) {
    const err = new Error(`${method} ${pathname} → ${res.status} ${text.slice(0, 800)}`)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

function baseTx(overrides) {
  return {
    city: 'Austin',
    state: 'TX',
    zip_code: '78701',
    purchase_price: 425000,
    earnest_money: 5000,
    earnest_money_days: 3,
    contract_acceptance_date: ACCEPT,
    closing_date: CLOSE,
    has_inspection: true,
    inspection_days: 10,
    inspection_response_days: 3,
    has_hoa: false,
    closing_mode: 'title_escrow',
    is_owner_occupied: true,
    status: 'Active',
    notes: `Feature 14-32 QA ${STAMP}`,
    ...overrides,
  }
}

async function addParty(token, txId, party) {
  return api(`/api/v1/transactions/${txId}/parties`, {
    method: 'POST',
    token,
    json: { is_primary: true, source: 'manual', ...party },
  })
}

async function uploadDoc(token, txId, fileName, docType, contents) {
  const fd = new FormData()
  fd.append('file', new Blob([contents], { type: 'text/plain' }), fileName)
  fd.append('transaction_id', txId)
  fd.append('doc_type', docType)
  fd.append('doc_label', fileName)
  return api('/api/v1/documents/upload', { method: 'POST', token, formData: fd })
}

async function generateTasks(token, txId) {
  try {
    return await api(`/api/v1/transactions/${txId}/tasks/generate`, {
      method: 'POST',
      token,
      json: {},
    })
  } catch (err) {
    if (err.status === 409) return { already: true }
    throw err
  }
}

async function setPosture(token, txId, posture) {
  return api(`/api/v1/transactions/${txId}/automation`, {
    method: 'PUT',
    token,
    json: { posture },
  })
}

async function listTasks(token, txId) {
  return api(`/api/v1/tasks/transaction/${txId}?include_ai=true`, { token })
}

async function emailPlan(token, taskId) {
  return api(`/api/v1/tasks/${taskId}/email-plan`, { token })
}

function taskNames(tasks) {
  return (tasks || []).map((t) => t.name)
}

function findTask(tasks, name) {
  return (tasks || []).find((t) => String(t.name || '').toLowerCase() === name.toLowerCase())
}

function findTasks(tasks, re) {
  return (tasks || []).filter((t) => re.test(t.name || ''))
}

async function createFile(token, spec) {
  const tx = await api('/api/v1/transactions', {
    method: 'POST',
    token,
    json: baseTx(spec.tx),
  })
  for (const p of spec.parties || []) {
    await addParty(token, tx.id, p)
  }
  for (const d of spec.docs || []) {
    await uploadDoc(token, tx.id, d.fileName, d.docType, d.contents)
  }
  if (spec.tcUserId) {
    try {
      await api(`/api/v1/transactions/${tx.id}/assignments`, {
        method: 'POST',
        token,
        json: { user_id: spec.tcUserId, role_in_transaction: 'transaction_coordinator' },
      })
    } catch (err) {
      tx.tcError = String(err.message || err).slice(0, 400)
    }
  }
  const gen = await generateTasks(token, tx.id)
  if (spec.posture) await setPosture(token, tx.id, spec.posture)
  const tasks = await listTasks(token, tx.id)
  const plans = {}
  for (const name of spec.planNames || []) {
    const task = findTask(tasks, name)
    if (!task) {
      plans[name] = { missing: true }
      continue
    }
    try {
      plans[name] = await emailPlan(token, task.id)
    } catch (err) {
      plans[name] = { error: String(err.message || err).slice(0, 500) }
    }
  }
  return {
    id: tx.id,
    address: tx.address,
    use_case: tx.use_case,
    posture: spec.posture || null,
    tcError: tx.tcError || null,
    generated: gen,
    task_names: taskNames(tasks),
    task_count: (tasks || []).length,
    plans,
  }
}

async function run() {
  const auth = await api('/api/v1/users/login', {
    method: 'POST',
    form: new URLSearchParams({ username: EMAIL, password: PASSWORD }).toString(),
  })
  if (auth.mfa_required) throw new Error('MFA required')
  const token = auth.access_token
  const me = auth.user
  console.log('login', me.email, me.id)

  let tcUserId = null
  try {
    const assignable = await api('/api/v1/users/assignable', { token })
    const staff = assignable.items || assignable.users || assignable
    const list = Array.isArray(staff) ? staff : []
    const tc = list.find((u) => /transaction.?coord/i.test(u.role || ''))
    if (tc) tcUserId = tc.id
    console.log('assignable', list.length, 'tc', tcUserId, tc?.email)
  } catch (err) {
    console.log('assignable skip', err.message)
  }

  const buyer = plus('buyer')
  const seller = plus('seller')
  const coop = plus('coop')
  const lender = plus('lender')
  const title = plus('title')
  const contract = {
    fileName: 'Purchase-Agreement.txt',
    docType: 'purchase_agreement',
    contents: `Purchase Agreement\nBuyer financed or cash test file ${STAMP}\nClosing ${CLOSE}\n`,
  }
  const utility = {
    fileName: 'Utility-Information.txt',
    docType: 'utility_info',
    contents: `Utility information for listing ${STAMP}\nElectric and water accounts.\n`,
  }

  const files = {}

  files.buyCash = await createFile(token, {
    tx: {
      address: `500 Test Elm Dr ${STAMP}`,
      use_case: 'Buy-Cash',
      financing_type: 'Cash',
      representation_type: 'Buyer',
      has_appraisal: true,
      title_ordered_by: 'Buyer',
      has_home_warranty: true,
      warranty_ordered_by: 'Buyer',
    },
    parties: [
      { party_role: 'buyer', full_name: 'Elm Buyer', email: buyer },
    ],
    docs: [contract],
    posture: 'assisted',
    planNames: ['Appraisal Ordered', 'Appraisal Completed'],
  })
  console.log('buyCash', files.buyCash.id, files.buyCash.task_names.filter((n) => /appraisal/i.test(n)))

  files.sellCash = await createFile(token, {
    tx: {
      address: `600 Test Birch Way ${STAMP}`,
      use_case: 'Sell-Cash',
      financing_type: 'Cash',
      representation_type: 'Seller',
      has_appraisal: true,
      title_ordered_by: 'Seller',
      has_home_warranty: false,
    },
    parties: [
      { party_role: 'seller', full_name: 'Birch Seller', email: seller },
      { party_role: 'buyers_agent', full_name: 'Birch Co-op', email: coop },
    ],
    docs: [contract],
    tcUserId,
    posture: 'assisted',
    planNames: ['Appraisal Ordered', 'Appraisal Completed'],
  })
  console.log('sellCash', files.sellCash.id, files.sellCash.tcError || 'tc ok')

  files.maple = await createFile(token, {
    tx: {
      address: `200 Test Maple Ave ${STAMP}`,
      use_case: 'Buy-Fin',
      financing_type: 'Financed',
      representation_type: 'Buyer',
      title_ordered_by: 'Buyer',
      has_home_warranty: true,
      warranty_ordered_by: 'Buyer',
    },
    parties: [
      { party_role: 'buyer', full_name: 'Maple Buyer', email: buyer },
      { party_role: 'loan_officer', full_name: 'Maple Lender', email: lender },
      { party_role: 'title_rep', full_name: 'Maple Title', email: title },
    ],
    docs: [contract],
    posture: 'manual',
    planNames: ['Buyer Welcome'],
  })
  console.log('maple', files.maple.id)

  files.pine = await createFile(token, {
    tx: {
      address: `300 Test Pine Ct ${STAMP}`,
      use_case: 'Buy-Fin',
      financing_type: 'Financed',
      representation_type: 'Buyer',
      title_ordered_by: 'Buyer',
      has_home_warranty: true,
      warranty_ordered_by: 'Buyer',
    },
    parties: [
      { party_role: 'buyer', full_name: 'Pine Buyer', email: buyer },
      { party_role: 'loan_officer', full_name: 'Pine Lender', email: lender },
      { party_role: 'title_rep', full_name: 'Pine Title', email: title },
    ],
    docs: [contract],
    posture: 'autopilot',
    planNames: ['Buyer Welcome', 'Order Title', 'Loan Officer Welcome', 'Inspection Response Reminder'],
  })
  console.log('pine', files.pine.id)

  files.cedar = await createFile(token, {
    tx: {
      address: `400 Test Cedar St ${STAMP}`,
      use_case: 'Buy-Fin',
      financing_type: 'Financed',
      representation_type: 'Buyer',
      title_ordered_by: 'Buyer',
    },
    parties: [{ party_role: 'buyer', full_name: 'Cedar Buyer' }],
    docs: [contract],
    posture: 'autopilot',
    planNames: ['Buyer Welcome'],
  })
  console.log('cedar', files.cedar.id)

  files.noContract = await createFile(token, {
    tx: {
      address: `410 Test No Contract Ln ${STAMP}`,
      use_case: 'Buy-Fin',
      financing_type: 'Financed',
      representation_type: 'Buyer',
      title_ordered_by: 'Buyer',
    },
    parties: [
      { party_role: 'buyer', full_name: 'NoContract Buyer', email: buyer },
      { party_role: 'loan_officer', full_name: 'NoContract Lender', email: lender },
      { party_role: 'title_rep', full_name: 'NoContract Title', email: title },
    ],
    posture: 'autopilot',
    planNames: ['Order Title', 'Loan Officer Welcome'],
  })
  console.log('noContract', files.noContract.id)

  files.dual = await createFile(token, {
    tx: {
      address: `700 Test Dual Ave ${STAMP}`,
      use_case: 'Both-Fin',
      financing_type: 'Financed',
      representation_type: 'Both',
      title_ordered_by: 'Buyer',
      has_home_warranty: true,
      warranty_ordered_by: 'Buyer',
      has_hoa: true,
      hoa_doc_days: 10,
    },
    parties: [
      { party_role: 'buyer', full_name: 'Dual Buyer', email: buyer },
      { party_role: 'seller', full_name: 'Dual Seller', email: seller },
      { party_role: 'loan_officer', full_name: 'Dual Lender', email: lender },
      { party_role: 'title_rep', full_name: 'Dual Title', email: title },
    ],
    docs: [contract],
    posture: 'assisted',
    planNames: ['Buyer Welcome', 'Seller Welcome', 'Order Title', 'Confirm Title Order', 'Co-op Agent Welcome'],
  })
  console.log('dual', files.dual.id)

  files.titleUs = await createFile(token, {
    tx: {
      address: `710 Order Title Ln ${STAMP}`,
      use_case: 'Buy-Fin',
      financing_type: 'Financed',
      representation_type: 'Buyer',
      title_ordered_by: 'Buyer',
      has_home_warranty: true,
      warranty_ordered_by: 'Buyer',
    },
    parties: [
      { party_role: 'buyer', full_name: 'TitleUs Buyer', email: buyer },
      { party_role: 'title_rep', full_name: 'TitleUs Rep', email: title },
    ],
    docs: [contract],
    posture: 'assisted',
    planNames: ['Order Title', 'Confirm Title Order', 'Order Home Warranty', 'Closing Gift'],
  })
  console.log('titleUs', files.titleUs.id)

  files.titleOther = await createFile(token, {
    tx: {
      address: `720 Confirm Title Ln ${STAMP}`,
      use_case: 'Buy-Fin',
      financing_type: 'Financed',
      representation_type: 'Buyer',
      title_ordered_by: 'Seller',
    },
    parties: [
      { party_role: 'buyer', full_name: 'TitleOther Buyer', email: buyer },
      { party_role: 'buyers_agent', full_name: 'TitleOther Co-op', email: coop },
      { party_role: 'title_rep', full_name: 'TitleOther Rep', email: title },
    ],
    docs: [contract],
    posture: 'assisted',
    planNames: ['Order Title', 'Confirm Title Order'],
  })
  console.log('titleOther', files.titleOther.id)

  files.utility = await createFile(token, {
    tx: {
      address: `800 Test Utility Ln ${STAMP}`,
      use_case: 'Sell-Fin',
      financing_type: 'Financed',
      representation_type: 'Seller',
      title_ordered_by: 'Seller',
      has_home_warranty: true,
      warranty_ordered_by: 'Buyer',
    },
    parties: [
      { party_role: 'seller', full_name: 'Utility Seller', email: seller },
      { party_role: 'buyers_agent', full_name: 'Utility Co-op', email: coop },
    ],
    docs: [contract, utility],
    tcUserId,
    posture: 'assisted',
    planNames: [
      'Deliver Utility Info',
      'Order Home Warranty',
      'Confirm Home Warranty',
      'Closing Gift',
      'Schedule Pick Up of Sign and Lockbox',
      'Change MLS Listing Status to Sold',
    ],
  })
  console.log('utility', files.utility.id)

  files.warrantyUs = await createFile(token, {
    tx: {
      address: `810 Order Warranty Ln ${STAMP}`,
      use_case: 'Buy-Fin',
      financing_type: 'Financed',
      representation_type: 'Buyer',
      title_ordered_by: 'Buyer',
      has_home_warranty: true,
      warranty_ordered_by: 'Buyer',
    },
    parties: [{ party_role: 'buyer', full_name: 'Warranty Buyer', email: buyer }],
    docs: [contract],
    tcUserId,
    posture: 'assisted',
    planNames: ['Order Home Warranty', 'Confirm Home Warranty'],
  })
  console.log('warrantyUs', files.warrantyUs.id)

  const preview = await api('/api/v1/automation/preview', { token }).catch((err) => ({
    error: String(err.message || err).slice(0, 800),
  }))

  const inbound = {}
  try {
    inbound.question = await api('/api/v1/ai-emails/test-inbound', {
      method: 'POST',
      token,
      json: {
        transaction_id: files.maple.id,
        sender_email: 'second.inbox.qa@example.com',
        subject: `${files.maple.address} — closing date`,
        body: `When is the closing date for ${files.maple.address}?`,
      },
    })
    inbound.statement = await api('/api/v1/ai-emails/test-inbound', {
      method: 'POST',
      token,
      json: {
        transaction_id: files.maple.id,
        sender_email: 'second.inbox.qa@example.com',
        subject: `${files.maple.address} — title`,
        body: 'The title commitment is ready.',
      },
    })
    inbound.wire = await api('/api/v1/ai-emails/test-inbound', {
      method: 'POST',
      token,
      json: {
        transaction_id: files.maple.id,
        sender_email: 'second.inbox.qa@example.com',
        subject: `${files.maple.address} — wire`,
        body: `Please send the wire instructions for ${files.maple.address}.`,
      },
    })
    inbound.banking = await api('/api/v1/ai-emails/test-inbound', {
      method: 'POST',
      token,
      json: {
        transaction_id: files.maple.id,
        sender_email: 'second.inbox.qa@example.com',
        subject: `${files.maple.address} — banking`,
        body: 'Please send banking details for closing.',
      },
    })
  } catch (err) {
    inbound.error = String(err.message || err).slice(0, 800)
  }

  const seed = {
    stamped: STAMP,
    emails: { buyer, seller, coop, lender, title, account: EMAIL },
    tcUserId,
    files,
    preview,
    inbound,
  }
  writeFileSync(path.join(OUT, 'seed.json'), JSON.stringify(seed, null, 2))
  console.log('wrote', path.join(OUT, 'seed.json'))
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
