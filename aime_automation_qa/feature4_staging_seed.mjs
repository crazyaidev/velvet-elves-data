/**
 * Seed Feature 4 staging deals and pinned test-inbound (no third-party send).
 *
 *   QA_API=https://api.stage.velvetelves.com QA_EMAIL=... QA_PASSWORD=... node feature4_staging_seed.mjs
 */
import { writeFileSync, mkdirSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const API = (process.env.QA_API || 'https://api.stage.velvetelves.com').replace(/\/$/, '')
const EMAIL = process.env.QA_EMAIL
const PASSWORD = process.env.QA_PASSWORD
const OUT = path.join(__dirname, 'artifacts_feature4_staging_seed')
mkdirSync(OUT, { recursive: true })
if (!EMAIL || !PASSWORD) {
  console.error('Set QA_EMAIL and QA_PASSWORD')
  process.exit(2)
}

const stamp = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, '')

async function api(pathname, { method = 'GET', token, json, form } = {}) {
  const headers = { Accept: 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  let body
  if (form) {
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
    const err = new Error(`${method} ${pathname} → ${res.status} ${text.slice(0, 500)}`)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

async function login() {
  const form = new URLSearchParams({ username: EMAIL, password: PASSWORD }).toString()
  const data = await api('/api/v1/users/login', { method: 'POST', form })
  if (data.mfa_required) throw new Error('MFA required')
  return data
}

async function run() {
  const auth = await login()
  const token = auth.access_token
  const user = auth.user
  console.log('login', user.email, user.id)

  const sycamore = await api('/api/v1/transactions', {
    method: 'POST',
    token,
    json: {
      address: '7710 F4 Sycamore Ridge',
      city: 'Mason',
      state: 'OH',
      zip_code: '45040',
      use_case: 'Buy-Fin',
      closing_date: '2026-10-15',
      purchase_price: 325000,
      notes: `Feature 4 matcher seed ${stamp}`,
    },
  })
  console.log('tx sycamore', sycamore.id, sycamore.address)

  const willow = await api('/api/v1/transactions', {
    method: 'POST',
    token,
    json: {
      address: '1842 F4 Willowbrook Lane',
      city: 'Carmel',
      state: 'IN',
      zip_code: '46032',
      use_case: 'Buy-Fin',
      closing_date: '2026-09-25',
      purchase_price: 410000,
      notes: `Feature 4 matcher seed ${stamp}`,
    },
  })
  console.log('tx willow', willow.id, willow.address)

  const james = await api(`/api/v1/transactions/${sycamore.id}/parties`, {
    method: 'POST',
    token,
    json: {
      party_role: 'buyer',
      full_name: 'James F4 Test',
      email: `f4.james.${stamp}@example.com`,
      is_primary: true,
    },
  })
  console.log('party james', james.id, james.email)

  const willowBuyer = await api(`/api/v1/transactions/${willow.id}/parties`, {
    method: 'POST',
    token,
    json: {
      party_role: 'buyer',
      full_name: 'Harper F4 Test',
      email: `f4.harper.${stamp}@example.com`,
      is_primary: true,
    },
  })
  console.log('party harper', willowBuyer.id, willowBuyer.email)

  const inboundA = await api('/api/v1/ai-emails/test-inbound', {
    method: 'POST',
    token,
    json: { transaction_id: sycamore.id, scenario: 'closing_question' },
  })
  console.log('test-inbound sycamore', inboundA)

  const inboundB = await api('/api/v1/ai-emails/test-inbound', {
    method: 'POST',
    token,
    json: { transaction_id: willow.id, scenario: 'document_request' },
  })
  console.log('test-inbound willow', inboundB)

  const inboxAll = await api('/api/v1/ai-emails/messages?view=all&limit=50', { token })
  const inboxSycamore = await api(
    `/api/v1/ai-emails/messages?view=all&limit=50&transaction_id=${sycamore.id}`,
    { token },
  )
  const inboxWillow = await api(
    `/api/v1/ai-emails/messages?view=all&limit=50&transaction_id=${willow.id}`,
    { token },
  )

  const aOnSycamore = (inboxSycamore.items || []).some((m) => m.id === inboundA.inbound_log_id)
  const aOnWillow = (inboxWillow.items || []).some((m) => m.id === inboundA.inbound_log_id)
  const bOnWillow = (inboxWillow.items || []).some((m) => m.id === inboundB.inbound_log_id)
  const bOnSycamore = (inboxSycamore.items || []).some((m) => m.id === inboundB.inbound_log_id)

  const checks = [
    { id: 'seed.sycamore-inbound-on-sycamore', ok: aOnSycamore },
    { id: 'seed.sycamore-inbound-not-on-willow', ok: !aOnWillow },
    { id: 'seed.willow-inbound-on-willow', ok: bOnWillow },
    { id: 'seed.willow-inbound-not-on-sycamore', ok: !bOnSycamore },
    { id: 'seed.sycamore-draft', ok: inboundA.draft_created === true },
    { id: 'seed.willow-draft', ok: inboundB.draft_created === true },
  ]
  for (const c of checks) console.log(`[${c.ok ? 'PASS' : 'FAIL'}] ${c.id}`)

  const payload = {
    stamp,
    user: { id: user.id, email: user.email, tenant_id: user.tenant_id },
    sycamore: { id: sycamore.id, address: sycamore.address },
    willow: { id: willow.id, address: willow.address },
    james: { id: james.id, email: james.email, name: james.full_name },
    harper: { id: willowBuyer.id, email: willowBuyer.email, name: willowBuyer.full_name },
    inboundA,
    inboundB,
    checks,
    inbox_counts: {
      all: (inboxAll.items || []).length,
      sycamore: (inboxSycamore.items || []).length,
      willow: (inboxWillow.items || []).length,
    },
  }
  writeFileSync(path.join(OUT, 'seed.json'), JSON.stringify(payload, null, 2))
  console.log('wrote', path.join(OUT, 'seed.json'))
  if (checks.some((c) => !c.ok)) process.exit(1)
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
