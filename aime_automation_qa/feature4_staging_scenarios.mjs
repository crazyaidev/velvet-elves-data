/**
 * Feature 4 staging scenarios against the seeded Sycamore / Willowbrook files.
 * Never Approve & send / Send all ready / Run AI tasks to a live mailbox.
 *
 *   QA_API=https://api.stage.velvetelves.com QA_EMAIL=... QA_PASSWORD=... node feature4_staging_scenarios.mjs
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const API = (process.env.QA_API || 'https://api.stage.velvetelves.com').replace(/\/$/, '')
const EMAIL = process.env.QA_EMAIL
const PASSWORD = process.env.QA_PASSWORD
const SEED_PATH = process.env.QA_SEED || path.join(__dirname, 'artifacts_feature4_staging_seed', 'seed.json')
const OUT = path.join(__dirname, 'artifacts_feature4_staging_scenarios')
mkdirSync(OUT, { recursive: true })
if (!EMAIL || !PASSWORD) {
  console.error('Set QA_EMAIL and QA_PASSWORD')
  process.exit(2)
}

const stamp = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, '')
const findings = []
const created = []

function log(id, result, details = '') {
  findings.push({ id, result, details: details == null ? '' : String(details).slice(0, 8000) })
  console.log(`[${result}] ${id}${details ? ' — ' + String(details).slice(0, 700) : ''}`)
}

function errText(data, fallback = '') {
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  if (typeof data.message === 'string') return data.message
  if (Array.isArray(data.detail)) return JSON.stringify(data.detail).slice(0, 500)
  try {
    return JSON.stringify(data).slice(0, 500)
  } catch {
    return fallback
  }
}

async function api(pathname, { method = 'GET', token, json, form, allow } = {}) {
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
  if (!res.ok && !(allow || []).includes(res.status)) {
    const err = new Error(`${method} ${pathname} → ${res.status} ${text.slice(0, 500)}`)
    err.status = res.status
    err.data = data
    throw err
  }
  return { status: res.status, data }
}

async function login() {
  const form = new URLSearchParams({ username: EMAIL, password: PASSWORD }).toString()
  const { data } = await api('/api/v1/users/login', { method: 'POST', form })
  if (data.mfa_required) throw new Error('MFA required')
  return data
}

function expectedChip(row) {
  if (!row.draft_id) return null
  if (row.draft_status === 'sent' || row.draft_status === 'approved') return 'Replied'
  if (!row.transaction_id) return 'Needs a deal'
  if (row.draft_status === 'auto_approved') return 'Reply ready'
  return 'Draft to review'
}

async function run() {
  if (!existsSync(SEED_PATH)) {
    console.error('Missing seed file', SEED_PATH)
    process.exit(2)
  }
  const seed = JSON.parse(readFileSync(SEED_PATH, 'utf8'))
  const auth = await login()
  const token = auth.access_token
  log('login', 'PASS', auth.user?.email)

  const sycamoreId = seed.sycamore.id
  const willowId = seed.willow.id

  const partiesS = (await api(`/api/v1/transactions/${sycamoreId}/parties`, { token })).data
  const partiesW = (await api(`/api/v1/transactions/${willowId}/parties`, { token })).data
  const james = (Array.isArray(partiesS) ? partiesS : partiesS?.items || []).find(
    (p) => /james/i.test(p.full_name || '') || /f4\.james/i.test(p.email || ''),
  )
  const harper = (Array.isArray(partiesW) ? partiesW : partiesW?.items || []).find(
    (p) => /harper/i.test(p.full_name || '') || /f4\.harper/i.test(p.email || ''),
  )
  log('seed.james-party', james?.email ? 'PASS' : 'FAIL', james?.email || 'missing')
  log('seed.harper-party', harper?.email ? 'PASS' : 'FAIL', harper?.email || 'missing')

  const inboxS = (await api(
    `/api/v1/ai-emails/messages?view=all&limit=100&transaction_id=${sycamoreId}`,
    { token },
  )).data
  const inboxW = (await api(
    `/api/v1/ai-emails/messages?view=all&limit=100&transaction_id=${willowId}`,
    { token },
  )).data
  const aOnS = (inboxS.items || []).some((m) => m.id === seed.inboundA.inbound_log_id)
  const aOnW = (inboxW.items || []).some((m) => m.id === seed.inboundA.inbound_log_id)
  const bOnW = (inboxW.items || []).some((m) => m.id === seed.inboundB.inbound_log_id)
  const bOnS = (inboxS.items || []).some((m) => m.id === seed.inboundB.inbound_log_id)
  log('isolation.sycamore-inbound-on-sycamore', aOnS ? 'PASS' : 'FAIL')
  log('isolation.sycamore-inbound-not-on-willow', !aOnW ? 'PASS' : 'FAIL')
  log('isolation.willow-inbound-on-willow', bOnW ? 'PASS' : 'FAIL')
  log('isolation.willow-inbound-not-on-sycamore', !bOnS ? 'PASS' : 'FAIL')

  const all = (await api('/api/v1/ai-emails/messages?view=all&limit=200', { token })).data
  const inbound = (all.items || []).filter((m) => m.direction !== 'outbound')
  const seeded = inbound.filter(
    (m) => m.id === seed.inboundA.inbound_log_id || m.id === seed.inboundB.inbound_log_id,
  )
  for (const row of seeded) {
    const chip = expectedChip(row)
    log(
      `chip.seeded-${row.id.slice(0, 8)}`,
      chip === 'Draft to review' || chip === 'Reply ready' ? 'PASS' : 'FAIL',
      `${chip} linked=${Boolean(row.transaction_id)} ${row.subject}`,
    )
    log(
      `chip.seeded-not-needs-a-deal-${row.id.slice(0, 8)}`,
      chip !== 'Needs a deal' ? 'PASS' : 'FAIL',
      'pinned test-inbound is on a deal',
    )
  }

  const unlinked = inbound.filter((m) => !m.transaction_id)
  log('inbox.unlinked-count', 'PASS', String(unlinked.length))
  for (const row of unlinked.filter((m) => m.draft_id).slice(0, 5)) {
    log(
      `chip.unlinked-${row.id.slice(0, 8)}`,
      expectedChip(row) === 'Needs a deal' ? 'PASS' : 'FAIL',
      `${expectedChip(row)} ${row.sender_email} ${row.subject}`,
    )
  }

  const probe = await api('/api/v1/ai-emails/test-inbound', {
    method: 'POST',
    token,
    json: {
      run_matcher: true,
      sender_email: 'f4.probe.unknown@example.com',
      subject: `F4 probe ${stamp} no deal street`,
      body: 'This is a matcher probe with no known party and no tenant street.',
    },
    allow: [200, 400, 422],
  })
  const matcherLive =
    probe.status === 200 && (probe.data?.skipped === true || 'match_basis' in (probe.data || {}))
  log(
    'matcher.endpoint',
    matcherLive ? 'PASS' : 'WARN',
    matcherLive
      ? `live status=${probe.status} skipped=${probe.data?.skipped} basis=${probe.data?.match_basis}`
      : `not deployed yet (${probe.status} ${errText(probe.data)}) — unique-party / self-CC cases need this harness on staging`,
  )
  if (matcherLive && probe.data?.inbound_log_id) {
    created.push({ kind: 'probe', ...probe.data })
  }

  const integrations = (await api('/api/v1/integrations', { token, allow: [200, 404] })).data
  const mailbox = (Array.isArray(integrations) ? integrations : [])
    .map((i) => i.provider_email)
    .find((e) => e && /@/.test(e))
  log('mailbox.connected', mailbox ? 'PASS' : 'WARN', mailbox || 'no provider_email')

  async function matcherCase(id, payload, assertFn) {
    if (!matcherLive) {
      log(id, 'SKIP', 'matcher harness not on staging')
      return null
    }
    const res = await api('/api/v1/ai-emails/test-inbound', {
      method: 'POST',
      token,
      json: { run_matcher: true, ...payload },
    })
    created.push({ kind: id, ...res.data })
    try {
      assertFn(res.data)
      log(id, 'PASS', JSON.stringify({
        skipped: res.data.skipped,
        basis: res.data.match_basis,
        tx: res.data.transaction_id,
        inbound: res.data.inbound_log_id,
        draft: res.data.draft_id,
      }))
    } catch (err) {
      log(id, 'FAIL', `${err.message} body=${JSON.stringify(res.data).slice(0, 600)}`)
    }
    return res.data
  }

  await matcherCase(
    'matcher.james-names-willowbrook-not-sycamore',
    {
      sender_email: james?.email,
      subject: `F4 ${stamp} 1842 F4 Willowbrook Lane closing`,
      body: `When is closing on 1842 F4 Willowbrook Lane? Seed ${stamp}`,
      scenario: 'closing_question',
    },
    (data) => {
      if (!james?.email) throw new Error('no James party email')
      if (data.skipped) throw new Error(`skipped ${data.skip_reason}`)
      if (data.transaction_id === sycamoreId) {
        throw new Error('filed on Sycamore — unique party won over the named street')
      }
      if (data.transaction_id && data.transaction_id !== willowId) {
        throw new Error(`filed on unexpected ${data.transaction_id}`)
      }
    },
  )

  const unknownStreet = await matcherCase(
    'matcher.james-names-unknown-street-unmatched',
    {
      sender_email: james?.email,
      subject: `F4 ${stamp} 9999 F4 Neverland Parkway closing`,
      body: `When is closing on 9999 F4 Neverland Parkway? This is not a Velvet Elves file. Seed ${stamp}`,
      scenario: 'closing_question',
    },
    (data) => {
      if (!james?.email) throw new Error('no James party email')
      if (data.skipped) throw new Error(`skipped ${data.skip_reason}`)
      if (data.transaction_id) throw new Error(`filed on ${data.transaction_id}`)
      if (data.match_basis && data.match_basis !== 'unmatched') {
        throw new Error(`basis ${data.match_basis}`)
      }
    },
  )

  await matcherCase(
    'matcher.james-no-street-files-sycamore',
    {
      sender_email: james?.email,
      subject: `F4 ${stamp} closing question no street`,
      body: 'We have 30 days until closing — what is next?',
      scenario: 'closing_question',
    },
    (data) => {
      if (!james?.email) throw new Error('no James party email')
      if (data.skipped) throw new Error(`skipped ${data.skip_reason}`)
      if (data.transaction_id !== sycamoreId) {
        throw new Error(`expected sycamore, got ${data.transaction_id}`)
      }
      if (data.match_basis && data.match_basis !== 'party_email') {
        throw new Error(`basis ${data.match_basis}`)
      }
    },
  )

  await matcherCase(
    'matcher.james-names-sycamore-files-sycamore',
    {
      sender_email: james?.email,
      subject: `F4 ${stamp} 7710 F4 Sycamore Ridge closing`,
      body: 'When is closing for 7710 F4 Sycamore Ridge in Mason?',
      scenario: 'closing_question',
    },
    (data) => {
      if (data.skipped) throw new Error(`skipped ${data.skip_reason}`)
      if (data.transaction_id !== sycamoreId) {
        throw new Error(`expected sycamore, got ${data.transaction_id}`)
      }
    },
  )

  await matcherCase(
    'matcher.address-only-files-willow',
    {
      sender_email: `f4.stranger.${stamp}@example.com`,
      subject: `F4 ${stamp} title for 1842 F4 Willowbrook Lane`,
      body: 'Please confirm closing for 1842 F4 Willowbrook Lane, Carmel, IN 46032.',
    },
    (data) => {
      if (data.skipped) {
        throw new Error(`skipped/filtered ${data.skip_reason}`)
      }
      if (data.transaction_id !== willowId) {
        throw new Error(`expected willow, got ${data.transaction_id} basis=${data.match_basis}`)
      }
    },
  )

  if (mailbox) {
    await matcherCase(
      'matcher.self-cc-skipped',
      {
        sender_email: mailbox,
        subject: `F4 ${stamp} Confirming title order self copy`,
        body: 'Thanks, this confirms the title order.',
      },
      (data) => {
        if (!data.skipped) throw new Error('expected skip of connected mailbox')
        if (data.skip_reason !== 'connected_mailbox') {
          throw new Error(`skip_reason ${data.skip_reason}`)
        }
        if (data.inbound_log_id) throw new Error('should not persist a log')
      },
    )
  } else {
    log('matcher.self-cc-skipped', 'SKIP', 'no connected mailbox email')
  }

  const approveTarget =
    unknownStreet?.draft_id && !unknownStreet.transaction_id ? unknownStreet.draft_id : null
  if (approveTarget) {
    const approve = await api(`/api/v1/ai-emails/${approveTarget}/approve`, {
      method: 'POST',
      token,
      allow: [200, 400, 409, 422],
    })
    const text = errText(approve.data)
    log(
      'send.unlinked-approve-blocked',
      approve.status === 400 && /deal/i.test(text) ? 'PASS' : 'FAIL',
      `${approve.status} ${text}`,
    )
  } else if (matcherLive) {
    log(
      'send.unlinked-approve-blocked',
      unknownStreet && !unknownStreet.transaction_id ? 'WARN' : 'SKIP',
      unknownStreet
        ? `no draft to refuse (basis=${unknownStreet.match_basis} tx=${unknownStreet.transaction_id})`
        : 'unknown-street case missing',
    )
  } else {
    log('send.unlinked-approve-blocked', 'SKIP', 'needs matcher harness')
  }

  const payload = {
    stamp,
    seed: {
      sycamore: seed.sycamore,
      willow: seed.willow,
      inboundA: seed.inboundA,
      inboundB: seed.inboundB,
      james: james ? { id: james.id, email: james.email } : null,
      harper: harper ? { id: harper.id, email: harper.email } : null,
    },
    matcherLive,
    mailbox: mailbox || null,
    created,
    findings,
  }
  writeFileSync(path.join(OUT, 'scenarios.json'), JSON.stringify(payload, null, 2))
  writeFileSync(path.join(OUT, 'findings.json'), JSON.stringify(findings, null, 2))
  const failed = findings.filter((f) => f.result === 'FAIL').length
  const warn = findings.filter((f) => f.result === 'WARN').length
  const skip = findings.filter((f) => f.result === 'SKIP').length
  console.log(failed ? `FAILED ${failed} WARN ${warn} SKIP ${skip}` : `NO FAIL CHECKS WARN ${warn} SKIP ${skip}`)
  console.log('wrote', path.join(OUT, 'scenarios.json'))
  process.exit(failed ? 1 : 0)
}

run().catch((err) => {
  console.error(err)
  process.exit(1)
})
