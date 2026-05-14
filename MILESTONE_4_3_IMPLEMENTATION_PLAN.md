# Milestone 4.3 — Vendor Communication System: Implementation Plan

**Milestone:** 4.3 (Phase 4, Week 16 — June 22–28, 2026)
**Author:** Jan (sole developer)
**Last updated:** 2026-05-14
**Predecessors:** Milestones 4.1 (Email Integration), 4.2 (AI Email Automation)
**Successor:** Milestone 5.1 (Role-Specific Dashboards)

---

## 1. Executive Summary

Milestone 4.3 closes Phase 4 by turning the existing inbound-classification work
from 4.2 into a *full vendor lifecycle*: structured outbound vendor requests,
deterministic reply parsing, automatic proposal of task-date updates with
human approval, durable vendor contact cards that carry across transactions,
and the unified communication-log UI that consolidates every other channel
into one searchable view per transaction.

The engine already classifies inbound mail as `vendor_reply` and extracts ISO
dates — but it does **not** yet propose task updates or send the constrained
outbound template (Milestone 4.2 explicitly defers both, §15). Milestone 4.3
implements the missing pieces and ships the SMS/voice-ready data-model hooks
so Phase 6/7 SMS work needs no schema changes.

### 1.1 Deliverables (verbatim from milestones.txt §4.3)

1. Vendor email templates with constrained response format
   (`"Reply with: Scheduled: YYYY-MM-DD"`)
2. AI reply parsing for vendor responses: extract dates, propose task-date
   updates, handle vague replies (clarify or route to human)
3. Vendor contact card system: email link/button for adding additional
   contacts; connected contacts persist across transactions; primary opt-in
   selection per transaction
4. Saved vendor rep background search (offer updates to info)
5. Document and wire provider-agnostic hooks for SMS / voice integrations
6. Communication log UI: unified per-transaction view, search/filter,
   single-transaction download, admin multi-transaction request form
7. End-to-end vendor communication flow tests

**Success criteria:** Vendor communication automated with structured
responses, contact card system operational, communication log complete.

### 1.2 Review corrections applied

This plan has been checked against the current backend and frontend code.
The main corrections are:

- Add missing `communication_logs` metadata/threading columns before relying
  on `metadata_json.task_id`, `message_id_header`, or `in_reply_to_header`.
- Model per-transaction primary opt-in with a separate
  `transaction_vendor_assignment_contacts` table; do not make vendor contacts
  globally primary from a public link.
- Add a durable `vendor_background_refreshes` table instead of treating
  background refreshes as an in-memory ticket.
- Standardize new vendor communication routes on
  `/api/v1/vendor-communications`.
- Keep the existing communication export API names:
  `/communication-logs/export-requests` and
  `/communication-logs/export-requests/{id}/download?token=...`.
- Use the current `CommunicationChannel` enum values (`email`, `sms`,
  `voice_call`, `push`, `system`, `ai_draft`, `note`,
  `document_action`) unless a separate enum migration is added.
- Store colleague invite token hashes, not raw bearer tokens.
- Seed tenant system templates through the tenant-provisioning path
  (`TenantRepository.create` / self-registration provisioning), not
  `seat_service.py`.

---

## 2. Current State (what 4.1 and 4.2 already give us)

These pieces are **reusable** and must not be rebuilt:

| Capability | Where | Notes |
|---|---|---|
| Provider-agnostic email send/receive | `app/services/email/{gmail,outlook,icloud}_provider.py`, `factory.py` | Used by AI email approve-and-send. |
| Inbound dispatcher + dedupe + transaction matching | `app/services/email/inbound_dispatch.py` | Already calls `ai_email_inbound_hook`. |
| `vendor_reply` classification | `app/services/ai_email_engine.py:_classify` | Detects `Scheduled: YYYY-MM-DD` and "we can come"/"confirmed for". |
| Vendor `_draft_vendor_reply` | `ai_email_engine.py` | Extracts ISO date, confidence 0.9 if found, 0.6 otherwise. **Always `pending_review`** (4.2 §5). |
| `communication_logs` table with full AI columns | `supabase/migrations/20260507_milestone_4_2_ai_email.sql` | `ai_kind`, `ai_source_data`, `parent_log_id`, `escalation_*`, `discarded_*`. |
| Communication log API: list, filter, download, resend, multi-tx export request | `app/api/v1/communication_logs.py` | Backend has the core endpoints. 4.3 should add vendor-aware filters only where the API actually supports them, and should use the existing export-request route names. |
| Communication log panel | `src/components/active-transactions/CommunicationsPanel.tsx` | Per-transaction drawer exists. Needs vendor-aware filters + global `/communications` page. |
| Vendor CRUD | `app/api/v1/vendors.py`, `vendor_repository.py` | Company-level only; no template binding, no per-transaction opt-in yet. |
| Vendor contact card (contacts with `is_vendor=true`, `vendor_id=...`) | `vendors.py:list_vendor_contacts` | Lists but no add/opt-in link flow. |
| AI provider abstraction (refine path) | `ai_service.py`, `providers/` | Used for the polish pass. Reused for clarification drafting. |

**Already supported by data model** (no migration needed):
- `communication_logs.channel` is `TEXT` — `sms` / `voice_call` values are storable today.
- `communication_logs.provider_name`, `provider_ref_id` — generic, accept any provider.
- `tasks.due_date` is mutable through `TaskRepository.update(task, due_date=...)`.
- `tasks.metadata_json` JSONB can hold optional audit/display hints, but
  `vendor_proposals` is the source of truth for proposal state.

**Not currently supported and added by this plan:**
- `communication_logs.metadata_json`, `message_id_header`,
  `in_reply_to_header`, and `thread_key`. Existing 4.2 AI columns are present,
  but proposal threading cannot rely on these fields until the 4.3 migration
  adds them and the repository/schema layers expose them.

---

## 3. Scope Decisions and Non-Goals

### 3.1 In scope (this milestone)

- Constrained-format vendor outbound templates, sent through the existing
  email provider abstraction.
- A new `vendor_proposals` lightweight table that links inbound vendor
  replies → tasks they want to reschedule, with human approval before any
  `tasks.due_date` mutation.
- `transaction_vendor_assignments` plus
  `transaction_vendor_assignment_contacts` — which vendor company is acting
  on this deal and which opted-in contacts are eligible/primary for this
  transaction.
- "Add my colleague" public token flow so vendors can self-attach a second
  contact without a login.
- Saved-vendor background refresh: a manual admin/agent action that searches
  tenant-local cache and, when configured, provider/public sources for
  updated vendor info. Refresh runs are persisted in
  `vendor_background_refreshes` and only apply through explicit user approval.
- Comm-log unified UI: standalone `/communications` page + a richer panel for
  the Active Transactions drawer, both reading from the existing API.
- SMS/voice hooks: persist `channel`, `provider_name`, `provider_ref_id` for
  any future provider; UI affordances (phone icon with "call via …" menu)
  that are non-functional today but feature-flag-ready.
- New vendor communication API prefix:
  `/api/v1/vendor-communications`.

### 3.2 Out of scope (deferred or in another milestone)

- **Actually sending SMS/voice** — provider wiring (Twilio, etc.) waits for a
  pricing decision and is post-MVP per requirements §7.8. We ship the hooks,
  not the integration.
- **Vendor self-service portal** — there is already a thin `/client/documents`
  vendor view (Phase 3 milestone 3.3). 4.3 does not expand it; the
  "add a colleague" flow is *outbound link + form*, not a logged-in portal.
- **MLS/title-company integrations** — Phase 6, milestone 6.1.
- **Predictive timeline-violation alerts on proposed dates** — beyond 4.3.
  We only validate against the task's own date dependencies and the
  transaction `closing_date`. Predictive analytics is §8.3 (later phase).
- **AI-initiated outbound to vendors without a triggering task or human
  action** — 4.2 §15 invariant preserved. A user picks a vendor + task and
  presses Send; the AI only fills the template body.
- **Public colleague links changing transaction primary contacts.** The
  public form may create a vendor contact, but primary opt-in remains an
  internal transaction-level decision.

### 3.3 Constraints I'm honoring

- **PII at rest is Fernet-encrypted** (Jan's note in memory). Vendor contact
  emails/phones go through `decrypt` at the repository edge before send and
  before being placed in LLM context.
- **Cost-effective LLM** (Jan's note). The classification stays rule-based.
  The clarification draft uses one provider call only when an inbound is
  classified vendor_reply *and* the date regex fails — never on the happy
  path. Same dedupe pattern as 4.2.
- **No independent VCS actions** (Jan's note). Plan only; no commits.

---

## 4. End-to-End Workflow (target state)

```
Agent opens task ──▶ "Email this vendor" CTA ──▶ Vendor Request modal
   │                                                     │
   │                                                     ▼
   │                          select vendor (+ primary contact) ─┐
   │                          select task date proposal ─────────┤
   │                          tone / channel (email today) ──────┘
   │                                                     │
   │                                                     ▼
   │                           render template body from VendorTemplateService
   │                                                     │
   │                                                     ▼
   │            POST /api/v1/vendor-communications  ◀─── outbound created
   │                                                     │
   │                                                     ▼
   │                         provider.send() via user's email integration
   │                                                     │
   │                                                     ▼
   │            communication_logs (id=A, outbound, ai_kind="vendor_request")
   │                                                     │
   │                                                     ▼
   │                         add-a-colleague link includes /v/{token}
   │                                                     │
   ▼                                                     ▼
Vendor (3rd-party email)                Vendor reply lands in inbox
   │
   ▼
inbound webhook ──▶ dispatcher persists row B (parent=null, sender=vendor)
   │
   ▼
ai_email_inbound_hook ──▶ engine classifies vendor_reply
   │
   ▼
draft row C created with parent_log_id=B (4.2 happy path)
   │  +
   │  NEW in 4.3:
   ▼
vendor_proposals row P created linking row C → candidate task(s) → proposed date
   │
   ▼
Agent sees pending vendor proposal in AI Email Review *and* on the task card
   │
   ▼
Agent approves ──▶ tasks.due_date updated  +  outbound confirmation drafted
   │                                                     │
   ▼                                                     ▼
audit log: vendor_proposal_accepted        confirmation queued in AI review
```

For vague replies, the engine creates draft C with confidence ≤ 0.65 (existing
4.2 behavior) and adds an assumption "asked the vendor to re-send in
`YYYY-MM-DD` format." The proposal row is still created, but with
`proposed_due_date = NULL` and `status = "needs_clarification"` so the UI can
prompt the agent to either approve auto-send of the clarification or write
their own.

---

## 5. Backend Implementation

### 5.1 Database migration — `supabase/migrations/20260622_milestone_4_3_vendor_comms.sql`

```sql
BEGIN;

-- 5.1.0 Communication-log threading metadata.
-- 4.2 created the AI-specific columns, but not these general-purpose
-- thread fields. Add them before any proposal logic depends on them.
ALTER TABLE public.communication_logs
    ADD COLUMN IF NOT EXISTS metadata_json JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS message_id_header TEXT,
    ADD COLUMN IF NOT EXISTS in_reply_to_header TEXT,
    ADD COLUMN IF NOT EXISTS thread_key TEXT;

CREATE INDEX IF NOT EXISTS idx_communication_logs_metadata_json
    ON public.communication_logs USING GIN (metadata_json);
CREATE INDEX IF NOT EXISTS idx_communication_logs_thread_key
    ON public.communication_logs(tenant_id, thread_key)
    WHERE thread_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_communication_logs_message_id_header
    ON public.communication_logs(tenant_id, message_id_header)
    WHERE message_id_header IS NOT NULL;

-- 5.1.1 Constrained-format vendor templates (rendered server-side; admin-editable)
CREATE TABLE IF NOT EXISTS public.vendor_email_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    category        TEXT,                         -- 'inspection','appraisal','title',...
    subject_template TEXT NOT NULL,
    body_template   TEXT NOT NULL,                -- includes the "Reply with: Scheduled: YYYY-MM-DD" footer
    response_format TEXT NOT NULL DEFAULT 'scheduled_date',  -- future: 'eta_window','confirm_yes_no'
    is_system       BOOLEAN DEFAULT FALSE,        -- ships with every tenant
    is_active       BOOLEAN DEFAULT TRUE,
    created_by      UUID REFERENCES public.users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

-- Seed five system templates per tenant: inspection scheduling, inspection
-- reschedule, appraisal scheduling, title-doc request, generic vendor
-- scheduling. (Seed in a separate migration; see §5.1.6.)

-- 5.1.2 Per-transaction vendor assignments — "the vendor for this task on this deal"
CREATE TABLE IF NOT EXISTS public.transaction_vendor_assignments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    transaction_id      UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
    vendor_id           UUID NOT NULL REFERENCES public.vendors(id) ON DELETE RESTRICT,
    role                TEXT NOT NULL,            -- 'inspector','appraiser','title_co','attorney',...
    notes               TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_by          UUID REFERENCES public.users(id),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (transaction_id, vendor_id, role)
);
CREATE INDEX idx_tva_transaction ON public.transaction_vendor_assignments(tenant_id, transaction_id);
CREATE INDEX idx_tva_vendor      ON public.transaction_vendor_assignments(tenant_id, vendor_id);

-- 5.1.2a Contacts opted in for a specific transaction assignment.
-- Public colleague links may create contacts, but only internal users choose
-- which contacts are active/primary on a transaction.
CREATE TABLE IF NOT EXISTS public.transaction_vendor_assignment_contacts (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    assignment_id  UUID NOT NULL REFERENCES public.transaction_vendor_assignments(id) ON DELETE CASCADE,
    contact_id     UUID NOT NULL REFERENCES public.contacts(id) ON DELETE CASCADE,
    is_primary     BOOLEAN NOT NULL DEFAULT FALSE,
    opted_in_by    UUID REFERENCES public.users(id),
    opted_in_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (assignment_id, contact_id)
);
CREATE UNIQUE INDEX uq_tvac_one_primary
    ON public.transaction_vendor_assignment_contacts(assignment_id)
    WHERE is_primary;
CREATE INDEX idx_tvac_contact
    ON public.transaction_vendor_assignment_contacts(tenant_id, contact_id);

-- 5.1.3 Vendor proposals — links inbound vendor_reply drafts to candidate task updates
CREATE TABLE IF NOT EXISTS public.vendor_proposals (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    transaction_id      UUID REFERENCES public.transactions(id),
    task_id             UUID REFERENCES public.tasks(id),         -- nullable: ambiguous reply
    inbound_log_id      UUID REFERENCES public.communication_logs(id),  -- vendor's reply
    draft_log_id        UUID REFERENCES public.communication_logs(id),  -- AI draft, may be null on auto-approve
    vendor_id           UUID REFERENCES public.vendors(id),
    proposed_due_date   DATE,
    proposed_due_time   TIME,                                     -- optional, when vendor includes time
    original_due_date   DATE,
    status              TEXT NOT NULL DEFAULT 'pending',          -- 'pending'|'accepted'|'rejected'|'needs_clarification'|'superseded'
    decision_reason     TEXT,
    decided_by          UUID REFERENCES public.users(id),
    decided_at          TIMESTAMPTZ,
    ai_confidence       NUMERIC(3,2),
    ai_assumptions      JSONB DEFAULT '[]'::jsonb,
    metadata_json       JSONB DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_vendor_proposal_status CHECK (
        status IN ('pending', 'accepted', 'rejected', 'needs_clarification', 'superseded')
    )
);
CREATE INDEX idx_vp_pending ON public.vendor_proposals(tenant_id, status)
    WHERE status IN ('pending', 'needs_clarification');
CREATE INDEX idx_vp_task    ON public.vendor_proposals(tenant_id, task_id);
CREATE UNIQUE INDEX uq_vendor_proposals_draft
    ON public.vendor_proposals(draft_log_id)
    WHERE draft_log_id IS NOT NULL;

-- 5.1.4 Public colleague-add tokens (vendor self-attach without login)
CREATE TABLE IF NOT EXISTS public.vendor_colleague_tokens (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash          TEXT NOT NULL UNIQUE,                      -- raw bearer token is returned once
    tenant_id           UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    vendor_id           UUID NOT NULL REFERENCES public.vendors(id),
    created_by          UUID REFERENCES public.users(id),
    transaction_id      UUID REFERENCES public.transactions(id),   -- nullable: tenant-wide invite
    expires_at          TIMESTAMPTZ NOT NULL,
    used_at             TIMESTAMPTZ,
    used_by_email       TEXT,                                       -- Fernet-encrypted at rest
    revoked_at          TIMESTAMPTZ,
    revoked_by          UUID REFERENCES public.users(id),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_vct_vendor ON public.vendor_colleague_tokens(tenant_id, vendor_id);

-- 5.1.5 Background refresh runs and suggestions.
CREATE TABLE IF NOT EXISTS public.vendor_background_refreshes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    vendor_id           UUID NOT NULL REFERENCES public.vendors(id) ON DELETE CASCADE,
    requested_by        UUID REFERENCES public.users(id),
    status              TEXT NOT NULL DEFAULT 'pending',
    source_scope        TEXT NOT NULL DEFAULT 'tenant_cache',
    suggestions_json    JSONB NOT NULL DEFAULT '[]'::jsonb,
    applied_fields_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    applied_by          UUID REFERENCES public.users(id),
    applied_at          TIMESTAMPTZ,
    CONSTRAINT chk_vendor_background_refresh_status CHECK (
        status IN ('pending', 'completed', 'failed', 'applied', 'rejected')
    ),
    CONSTRAINT chk_vendor_background_refresh_scope CHECK (
        source_scope IN ('tenant_cache', 'provider_public', 'platform_admin')
    )
);
CREATE INDEX idx_vbr_vendor
    ON public.vendor_background_refreshes(tenant_id, vendor_id, created_at DESC);

-- 5.1.6 Channel/provider columns already exist
--       (channel TEXT, provider_name, provider_ref_id). No schema change here.

-- 5.1.7 RLS stays closed to anonymous clients. Backend service-role access
-- enforces tenant scope in repositories/API dependencies.
ALTER TABLE public.vendor_email_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transaction_vendor_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transaction_vendor_assignment_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vendor_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vendor_colleague_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vendor_background_refreshes ENABLE ROW LEVEL SECURITY;

CREATE POLICY service_role_vendor_email_templates ON public.vendor_email_templates
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY service_role_transaction_vendor_assignments ON public.transaction_vendor_assignments
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY service_role_transaction_vendor_assignment_contacts ON public.transaction_vendor_assignment_contacts
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY service_role_vendor_proposals ON public.vendor_proposals
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY service_role_vendor_colleague_tokens ON public.vendor_colleague_tokens
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY service_role_vendor_background_refreshes ON public.vendor_background_refreshes
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

-- 5.1.8 Seed system templates (separate file to keep this migration idempotent)

COMMIT;
```

A second seed migration `20260622_seed_vendor_email_templates.sql` inserts five
system templates per existing tenant. New tenants should receive the same
templates from the tenant-provisioning path (`TenantRepository.create` and the
self-registration provisioning flow), mirroring the existing task-template
seeding behavior rather than adding a `seat_service.py` dependency.

### 5.2 Domain models

New files under `app/models/`:

- `vendor_email_template.py` — `@dataclass VendorEmailTemplate(id, tenant_id, name, category, subject_template, body_template, response_format, is_system, is_active, created_by, created_at, updated_at)`
- `transaction_vendor_assignment.py` — `@dataclass TransactionVendorAssignment(id, tenant_id, transaction_id, vendor_id, role, notes, is_active, created_by, created_at, updated_at)`
- `transaction_vendor_assignment_contact.py` — `@dataclass TransactionVendorAssignmentContact(id, tenant_id, assignment_id, contact_id, is_primary, opted_in_by, opted_in_at, created_at)`
- `vendor_proposal.py` — `@dataclass VendorProposal(...)`
- `vendor_colleague_token.py` — `@dataclass VendorColleagueToken(id, token_hash, tenant_id, vendor_id, transaction_id, expires_at, used_at, used_by_email, revoked_at, revoked_by, created_at)`
- `vendor_background_refresh.py` — `@dataclass VendorBackgroundRefresh(...)`

Also update existing `communication_log.py`, `schemas/communication_log.py`,
`repositories/communication_log_repository.py`, and frontend `src/types/api.ts`
to expose `metadata_json`, `message_id_header`, `in_reply_to_header`, and
`thread_key`.

All new models follow the existing `app/models/*.py` shape (frozen=False, slots not used). PII fields (`used_by_email`) decrypt-on-read via repository; `token_hash` is never decrypted because the raw token is not stored.

### 5.3 Repositories

New files under `app/repositories/`:

- `vendor_email_template_repository.py` — `list_active_by_tenant`, `get_by_id`, `create`, `update`, `deactivate`. Includes a `system_seed_rows()` helper reused by the seed migration/provisioning flow.
- `transaction_vendor_assignment_repository.py` — `list_by_transaction`, `upsert(tenant, transaction, vendor, role)`, `update_notes`, `deactivate`.
- `transaction_vendor_assignment_contact_repository.py` — `list_by_assignment`, `add_contact`, `remove_contact`, `set_primary_contact(assignment_id, contact_id)`.
- `vendor_proposal_repository.py` — `create`, `get_by_id`, `list_pending_by_tenant`, `list_by_task`, `accept(id, user)`, `reject(id, user, reason)`, `mark_needs_clarification(id)`.
- `vendor_colleague_token_repository.py` — `create_with_expiry(...)` returns `{raw_token, token_row}`, `get_active_by_raw_token(raw_token)`, `consume(token_hash, used_by_email)`, `revoke(invite_id, user)`.
- `vendor_background_refresh_repository.py` — `create_pending`, `complete_with_suggestions`, `mark_failed`, `apply_fields`, `latest_for_vendor`.

Each repository mirrors the encrypt/decrypt pattern already in
`vendor_repository.py` for PII fields. `token_hash` is compared with a
constant-time hash check and is never decrypted or returned.

### 5.4 Service layer

#### 5.4.1 `app/services/vendor_template_service.py` (new)

```python
class VendorTemplateService:
    async def render(self, template_id: str, *, transaction, task, vendor,
                     primary_contact, owner_user, colleague_link: str | None) -> RenderedEmail:
        ...
```

- Loads the template, substitutes `{{property_address}}`, `{{closing_date}}`,
  `{{task_name}}`, `{{task_due_date}}`, `{{owner_name}}`,
  `{{owner_email}}`, `{{primary_contact_name}}`, `{{response_footer}}`,
  `{{colleague_invite_url}}`.
- `response_footer` is constant per `response_format`:
  - `scheduled_date` → `Reply with: Scheduled: YYYY-MM-DD`
- Returns `RenderedEmail(subject, body_text, body_html, recipients, cc)`.
- This service is deterministic on the happy path; no LLM call is needed to
  render the request template.
- Recipients are the assignment contacts selected for the transaction, with
  the primary contact first. The default CC list is the file owner only.
  Do not auto-CC every historical vendor contact across transactions.

#### 5.4.2 `app/services/vendor_proposal_service.py` (new)

Wraps the proposal workflow:

```python
class VendorProposalService:
    async def propose_from_vendor_reply(self, *, tenant_id, draft_log_id,
                                        inbound_log_id, transaction_id,
                                        vendor_id, parsed_date, ai_confidence,
                                        assumptions) -> VendorProposal:
        """Called by the AI email engine after a vendor_reply draft is persisted.

        Strategy for picking which task to update:
          1. If inbound raw headers `In-Reply-To` or `References` match a
             persisted outbound `message_id_header`, use that outbound row's
             `metadata_json.task_id`.
          2. Else if the subject contains a generated marker such as
             `[VE-TASK-<short id>]`, or if `thread_key` matches a prior
             vendor request, use that task.
          3. Else find the most recent outbound to this vendor on this
             transaction in the last 14 days.
          4. Else: open-ended proposal with `task_id=NULL` - UI prompts the
             agent to pick.
        """
```

Decision actions:

- `accept(proposal_id, user)` → loads the task tenant-scoped and updates
  `tasks.due_date` through `TaskRepository.update(task, due_date=...)`,
  writes audit log `entity_type="task", action="vendor_date_accepted"`,
  marks proposal `accepted`, and optionally drafts a confirmation reply to
  the vendor. `proposed_due_time` remains proposal metadata unless/until the
  task model gains a time-of-day field.
- `reject(proposal_id, user, reason)` → stamps `rejected`, audit log, no
  task mutation. UI may then offer "send vendor an alternative date" — that
  reopens the outbound template modal.

#### 5.4.3 AI engine extension — `app/services/ai_email_engine.py`

Add to `handle_inbound` after the existing vendor branch persists the AI draft
communication-log row. Today `AIEmailEngine.handle_inbound` returns only the
draft object and discards the `CommunicationLogRepository.create(...)` return
value, so the implementation must capture that created log (`draft_log.id`) or
return a richer result before calling the proposal service:

```python
if kind == KIND_VENDOR_REPLY:
    vendor = await self._resolve_vendor_from_inbound(inbound, transaction)
    await VendorProposalService(self._supabase).propose_from_vendor_reply(
        tenant_id=tenant_id,
        draft_log_id=draft_log_id,
        inbound_log_id=inbound_log_id,
        transaction_id=transaction_id,
        vendor_id=vendor.id if vendor else None,
        parsed_date=draft.source_data.get("scheduled_date"),
        ai_confidence=draft.confidence,
        assumptions=draft.assumptions,
    )
```

`_resolve_vendor_from_inbound` matches sender email against
`vendors.email` and `contacts.email` (where `is_vendor=true`), tenant-scoped.
Do not match against `vendor_colleague_tokens.used_by_email` as the source of
truth; token rows are an audit trail. If the colleague flow accepted the
contact, the resulting `contacts.email` + `contacts.vendor_id` match wins.

#### 5.4.4 Background search service — `app/services/vendor_background_search.py` (new)

Cheap, **opt-in**, never automatic:

```python
class VendorBackgroundSearchService:
    async def queue_refresh(self, vendor_id, requested_by) -> VendorBackgroundRefresh:
        """Create a vendor_background_refreshes row for an agent to confirm.

        Sources (in order):
          1. Tenant-local vendor/contact rows with the same `phone` or `email`.
          2. Last-known vendor metadata from this tenant's completed transactions.
          3. Optional provider/public-source lookup when tenant setting
             `background_refresh_provider_enabled` is true.
          4. Platform-wide cross-tenant suggestions only for platform-admin
             workflows or tenants that explicitly opt in.
        Each suggestion gets confidence and a source label.
        """
```

The endpoint returns the persisted refresh row and candidate updates. The UI
shows them as diff cards with Accept/Reject per field. Accepting writes through
`VendorRepository.update`, stamps `applied_fields_json`, and writes an audit
log.

This explicitly satisfies milestones.txt 4.3 deliverable "Saved vendor rep
background search (offer updates to info)" without scope-creeping into a
live web crawler.

#### 5.4.5 SMS/voice hooks (documentation + plumbing)

Concrete deliverables:

1. **`app/services/communication_providers.py` (new)** — protocol stubs:
   ```python
   class SmsProvider(Protocol):
       async def send_sms(self, *, to, body, metadata) -> SmsSendResult: ...
   class VoiceProvider(Protocol):
       async def initiate_call(self, *, to, callback_url, metadata) -> CallBridgeResult: ...
   ```
   No concrete implementation yet. Existence is enough for the comm-log
   path to accept `channel='sms'`/`channel='voice_call'` rows without surprise.

2. **`communication_logs.channel`** must continue to use the current
   `CommunicationChannel` enum values unless a separate migration updates all
   callers: `email`, `sms`, `voice_call`, `push`, `system`, `ai_draft`,
   `note`, `document_action`.

3. **`schemas/communication_log.py`** validates the same enum values and the
   frontend badge maps `voice_call` to "Voice".

4. **Contact card phone icon** in frontend renders a disabled "Call via …
   (coming soon)" menu, feature-flagged by a tenant setting
   `settings_json.vendor_comms.phone_action_enabled` (default `false`).

### 5.5 API surface (`app/api/v1/`)

New router: **`vendor_communications.py`** (mounted at `/api/v1/vendor-communications`)

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/templates` | any internal | List active vendor email templates for tenant |
| POST | `/templates` | Admin/TeamLead | Create custom template |
| PUT | `/templates/{id}` | Admin/TeamLead | Update template |
| DELETE | `/templates/{id}` | Admin | Deactivate template |
| POST | `/preview` | any internal | Render a template for a given task+vendor (no send) |
| POST | `/send` | Agent/TC/TeamLead/Admin | Render + send via user's provider; logs outbound |
| GET | `/proposals` | any internal (tenant) | List pending vendor proposals |
| GET | `/proposals/{id}` | any internal | Detail with linked task, vendor, draft, inbound |
| POST | `/proposals/{id}/accept` | Agent/TC/TeamLead/Admin | Update task date, draft confirmation |
| POST | `/proposals/{id}/reject` | Agent/TC/TeamLead/Admin | Reject + reason |
| POST | `/proposals/{id}/needs-clarification` | Agent/TC/TeamLead/Admin | Trigger clarification email |
| GET | `/settings` | Admin/TeamLead | Read `settings_json.vendor_comms` defaults |
| PUT | `/settings` | Admin/TeamLead | Update `settings_json.vendor_comms` |

Extend **`vendors.py`** with:

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/{vendor_id}/colleague-invites` | Agent/TC/TeamLead/Admin | Create a public token + URL |
| GET | `/{vendor_id}/colleague-invites` | Agent/TC/TeamLead/Admin | List active invites for vendor |
| DELETE | `/colleague-invites/{invite_id}` | Agent/TC/TeamLead/Admin | Revoke by invite id, never raw token |
| POST | `/{vendor_id}/background-refresh` | Agent/TC/TeamLead/Admin | Create persisted refresh row |
| GET | `/{vendor_id}/background-refresh` | any internal | Get latest refresh row + suggestions |
| POST | `/{vendor_id}/background-refresh/apply` | Agent/TC/TeamLead/Admin | Accept selected suggestions on latest/current row |
| GET | `/{vendor_id}/transactions` | any internal | Vendor's portfolio across transactions (read-only) |

Extend **`transactions.py`** with:

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/{transaction_id}/vendor-assignments` | any internal | List vendor assignments + opted-in contacts |
| POST | `/{transaction_id}/vendor-assignments` | Agent/TC/TeamLead/Admin | Assign a vendor (+role; optional initial contacts) |
| PUT | `/{transaction_id}/vendor-assignments/{id}` | Agent/TC/TeamLead/Admin | Change notes / active state |
| PUT | `/{transaction_id}/vendor-assignments/{id}/contacts` | Agent/TC/TeamLead/Admin | Add/remove assignment contacts and set the primary contact |
| DELETE | `/{transaction_id}/vendor-assignments/{id}` | Agent/TC/TeamLead/Admin | Remove |

New public router: **`vendor_public.py`** (mounted at `/api/v1/public/vendor`,
no auth, rate-limited):

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/colleague-invites/{token}` | public | Validate token, return tenant branding + vendor company name |
| POST | `/colleague-invites/{token}/accept` | public | Body `{ first_name, last_name, email, phone, title }` → creates `contacts` row attached to vendor; consumes token. It never marks a transaction primary contact. |

The token endpoint must not leak transaction details or any PII beyond the
vendor company name and the tenant's display name + logo. CAPTCHA hook is
deferred but the route must be rate-limited. Add a minimal
`app/core/rate_limit.py` in-process limiter if no shared limiter exists.

Wire both new routers in `app/api/v1/router.py` and keep all internal routes
behind the existing tenant/user role dependencies.

### 5.6 Engine + dispatch wiring

`app/services/email/inbound_dispatch.py` already calls
`ai_email_inbound_hook`. The hook in `ai_email_engine.py` is the only place
that needs to gain the proposal-creation side effect (see §5.4.3). No new
hooks; we ride 4.2's path.

One detail: when **outbound** vendor-template sends happen via
`POST /vendor-communications/send`, we stamp
`communication_logs.metadata_json.task_id`, `metadata_json.template_id`,
`metadata_json.vendor_id`, `metadata_json.assignment_id`, `thread_key`, and
when the provider returns one, `message_id_header` on the outbound row. The
subject should also include a stable marker such as `[VE-TASK-<short id>]`
so proposal matching has a fallback if provider threading headers are absent.

### 5.7 Audit logging additions

| action | entity_type | when |
|---|---|---|
| `vendor_request_sent` | `communication_log` | After `/vendor-communications/send` writes the outbound row |
| `vendor_proposal_created` | `vendor_proposal` | After engine persists the proposal |
| `vendor_proposal_accepted` | `task` | After `accept` updates `tasks.due_date` |
| `vendor_proposal_rejected` | `vendor_proposal` | After `reject` |
| `vendor_colleague_invite_created` | `vendor` | After token creation |
| `vendor_colleague_added` | `contact` | After public accept |
| `vendor_background_refresh_applied` | `vendor` | After apply, per applied field |

All write through the existing `AuditService.log` — no new infrastructure.

### 5.8 Settings additions

`tenants.settings_json.vendor_comms` (new namespace, all optional):

```json
{
  "auto_send_confirmation_threshold": 0.9,
  "colleague_invite_ttl_hours": 168,
  "background_refresh_provider_enabled": false,
  "preferred_response_format": "scheduled_date",
  "phone_action_enabled": false,
  "sms_provider": null,
  "voice_provider": null
}
```

Defaults are applied in `VendorTemplateService` / `VendorProposalService` /
the public router. The outbound request itself is a deterministic,
user-triggered send, so there is no request auto-send threshold. Settings
are updated through `PUT /api/v1/vendor-communications/settings` (admin /
team lead, mirrors 4.2's `PUT /ai-emails/settings`).

### 5.9 Tests

Place under `app/tests/`. Mirror existing 4.2 test layout.

- `test_vendor_template_service.py` — template substitution, default CC,
  colleague link inclusion, missing-data fallbacks.
- `test_vendor_proposal_service.py`:
  - `propose_from_vendor_reply` happy path → row created, status `pending`.
  - Vague reply path → `needs_clarification`, no date set.
  - Threading wins task selection over recency.
  - `accept` updates `tasks.due_date`, writes audit log, drafts
    confirmation only when conf ≥ threshold.
  - `reject` writes audit log, does not mutate task.
- `test_vendor_comms_api.py` — full CRUD on templates, send happy path,
  proposal listing and accept/reject, role enforcement, tenant isolation.
- `test_transaction_vendor_assignment_contacts.py` — assignment contacts,
  one-primary constraint, tenant isolation, and internal-only primary changes.
- `test_vendor_colleague_tokens.py` — token creation, expiry, single-use
  consumption, hashed-token storage, revoke-by-id, malformed token (404),
  expired (410), used (409).
- `test_vendor_public_api.py` — public accept creates a contact but never
  marks an assignment primary.
- `test_vendor_background_search.py` — suggestion ranking, apply only
  accepted fields, audit-log per applied field.
- `test_communication_log_metadata.py` — create/list/serialize
  `metadata_json`, `message_id_header`, `in_reply_to_header`, and `thread_key`.
- `test_communication_export_routes.py` — assert existing
  `/communication-logs/export-requests` and
  `/communication-logs/export-requests/{id}/download?token=...` routes remain
  wired.
- `test_ai_engine_vendor_proposal_hook.py` — integration: synthesize an
  inbound vendor reply, run the engine, assert both the draft row *and*
  the proposal row exist with correct linkage.
- `test_inbound_threading.py` — outbound has `metadata_json.task_id`, the
  vendor's `In-Reply-To` header matches, proposal lands on the right task.

Target ≥ 80 % coverage on the new modules to stay aligned with §7.1.

---

## 6. Frontend Implementation

### 6.1 New / extended pages

| Route | File | Purpose |
|---|---|---|
| `/communications` | `src/pages/CommunicationsPage.tsx` (new) | Standalone unified comm log (req §6.1: searchable cross-transaction view) |
| `/vendors` | `src/pages/vendors/VendorListPage.tsx` (new) | Tenant-wide vendor directory: list, preferred filter, "send request" launcher |
| `/vendors/:vendorId` | `src/pages/vendors/VendorDetailPage.tsx` (new) | Vendor card: company, contacts, transactions, recent activity, "background refresh" CTA |
| `/vendor-proposals` | `src/pages/VendorProposalsPage.tsx` (new) | Pending proposals review queue (sibling to `/ai-emails`; current app has no `/intelligence/*` route namespace) |
| `/v/:token` | `src/pages/public/AddColleaguePage.tsx` (new, public) | Public 1-page form: vendor self-attach colleague |
| `/admin/vendor-templates` | `src/pages/admin/VendorTemplatesPage.tsx` (new) | Admin/TeamLead template management |

### 6.2 New components

- `src/components/vendors/VendorRequestModal.tsx` — drives `POST /vendor-communications/preview` and `/vendor-communications/send`. Reuses the AI email side-by-side viewer shell from `AiEmailReviewPage.tsx`.
- `src/components/vendors/VendorProposalCard.tsx` — used in both the queue page and inline in `CommunicationsPanel.tsx` when filtering to vendor traffic.
- `src/components/vendors/VendorContactCard.tsx` — shows company + contacts; "Email primary," "Add colleague" (creates token, copies link to clipboard), "Refresh info" actions.
- `src/components/vendors/BackgroundRefreshDrawer.tsx` — diff list of candidate updates with per-field accept/reject.
- `src/components/communications/CommunicationsFilters.tsx` — extract the current panel's filter row into a reusable component used by both the standalone page and the drawer.
- `src/components/communications/ChannelBadge.tsx` — renders the channel chip (Email / SMS coming soon / Voice coming soon). Tied to the feature-flag.

### 6.3 Hooks (`src/hooks/`)

- `useVendorTemplates.ts` — list, create, update, delete, preview.
- `useVendorComms.ts` — `useSendVendorRequest`, `useVendorProposals`,
  `useAcceptVendorProposal`, `useRejectVendorProposal`,
  `useClarifyVendorProposal`.
- `useVendorColleagueInvites.ts` — create / list / revoke tokens.
- `useVendorBackgroundRefresh.ts` — queue, fetch, apply.
- `useVendorAssignments.ts` — per-transaction vendor assignments.
- Extend `useCommunicationLogs.ts` with `vendor_id` and `ai_kind` filters only
  after the backend list endpoint supports those query params. The existing
  multi-transaction list path is `GET /api/v1/communication-logs`; export
  requests are separate.

### 6.4 UX touchpoints

- **Active Transactions card → expanded drawer → contacts column.** Each
  vendor contact gets the new `VendorContactCard` actions. Phone icon shows
  the coming-soon menu when the tenant flag is off.
- **Active Transactions card → tasks column.** Each task with a vendor
  assignment gets an "Email vendor" inline button that opens
  `VendorRequestModal` pre-bound to that task.
- **AI Email Review (`/ai-emails`).** `vendor_reply` drafts already render
  there. New: when a proposal exists for the draft, show a "Linked task
  update proposal" panel under the source-data rail with a primary
  Accept and Reject CTA right there. The agent should not need to leave
  this page to update the task date.
- **Sidebar Intelligence section.** New chip "Vendor Proposals (N)" next
  to the existing "AI Email Review" chip; same polling cadence (60 s).
- **Topbar bell.** Notification taxonomy gains
  `vendor_proposal_pending` and `vendor_proposal_clarification_needed`.

### 6.5 Style guide alignment

All new UI follows `STYLE_GUIDE.md`:
- IBM Plex Sans body; IBM Plex Mono for `Scheduled: 2026-07-12` and task
  dates.
- Status pills reuse `bg-ve-amber-bg` / `bg-ve-green-bg` / `bg-ve-red-bg`
  semantic tokens (see 4.2 page for parity).
- 48×48 minimum interactive targets.
- Action buttons need explicit labels (per Jan's preference, no
  whole-card click targets — `feedback_alert_card_clickability` memory).

### 6.6 Tests

- Vitest unit tests for hooks and template preview rendering.
- Component tests for `VendorRequestModal` (preview → send happy path,
  validation errors, fallback when no email provider connected).
- Playwright (or existing E2E framework) flow:
  1. Agent sends a vendor request from a task.
  2. Simulated inbound webhook posts a `Scheduled: 2026-07-15` reply.
  3. Agent opens the vendor proposal queue, accepts.
  4. The task's `due_date` reflects the new date.
  5. The communication log shows three rows in order: outbound request,
     inbound reply, outbound confirmation.

---

## 7. Communication-Log Unified UI (Deliverable §6 explicitly)

The backend already exposes everything needed (`/api/v1/communication-logs`
with search, party_email, date_from/to, pinned, AI-only, paging, plus
single-tx CSV download and multi-tx export-request). 4.3 ships the **UI**:

### 7.1 `/communications` page (new)

Layout:
- Top filter row (parity with `CommunicationsPanel.tsx`): channel,
  direction, date range, pinned, AI only, party email, search.
- Optional transaction filter — if set, the "Download CSV" button is
  enabled (one-transaction-at-a-time policy from req §6.1). Otherwise
  shows "Request multi-transaction export" which calls the existing
  `POST /communication-logs/export-requests` flow. Non-admins see the link
  but get a "Ask an admin to run this export" tooltip.
- Result list groups by date heading (Today / Yesterday / earlier),
  matching the Transaction History panel pattern.

### 7.2 Per-transaction drawer (existing `CommunicationsPanel.tsx`)

- Add a "Vendor traffic only" filter chip that maps to
  `is_ai_generated=true&ai_kind=vendor_request,vendor_reply` plus the
  inbound rows whose sender matches an assigned vendor on that tx. Add the
  backend `ai_kind`/`vendor_id` filters first; the current frontend type has
  not exposed them yet.
- Add a "Channel" chip menu (Email today; SMS/Voice greyed with
  tooltip).

### 7.3 Admin export workflow

The page `/admin/communication-exports` already exists as
`src/pages/admin/CommunicationExportRequestsPage.tsx`; extend/polish it
instead of creating a duplicate page. It should list submitted requests with
status and use the existing download route
`/communication-logs/export-requests/{id}/download?token=...`.

---

## 8. Migration / Rollout Plan

Single-tenant rollout via existing CI on `dev.velvetelves.com` first.

1. Day 1: merge migration `20260622_milestone_4_3_vendor_comms.sql` +
   seed migration. Verify on dev — empty proposal queue, template list
   shows seeded entries.
2. Day 1–2: backend routers behind no flag (all behind auth + role checks
   already). Feature-flag the SMS/voice UI affordances only.
3. Day 2: smoke test the colleague-token public route on dev with a
   real Gmail address.
4. Day 3–4: frontend pages and hooks. Ship in feature branches behind
   `VITE_FEATURE_VENDOR_COMMS=on` while wiring up.
5. Day 5: E2E flow on dev with a real inspection-style email round-trip
   (use Gmail's "Send to self" trick + dispatcher webhook for the inbound
   half).
6. Day 6: production rollout follows the same gate. Customer-facing
   templates seeded for all existing tenants in a one-off SQL migration.

Rollback plan: disable the frontend feature flag and remove the additive
proposal-service call to return AI email behavior to 4.2. Dropping the six
new tables is possible before production data accumulates, but
`communication_logs` metadata/thread columns are additive and can safely stay.

---

## 9. Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Vendor sends reply without honoring the constrained format | High | Engine already handles this (vague reply → confidence 0.6 + assumption). 4.3 wraps it in the proposal UI with a "Send clarification" one-click. |
| Wrong task is chosen for the proposal | Medium | Match persisted provider headers first, then subject/thread markers, then most-recent outbound in 14 days; if neither matches, leave `task_id=NULL` and ask the agent. |
| Public colleague-add token leaks PII | Medium | Token reveals only vendor company name + tenant branding. No transaction context. Single-use. TTL configurable (default 7 days). Store only `token_hash`; audit-log consume. Email Fernet-encrypted at rest. |
| Background-refresh suggestions cause data drift | Medium | Strictly suggestion-only; per-field accept/reject; nothing applies without an explicit user click. Audit-logged per applied field. |
| LLM cost regression | Low | Engine still classifies with regex. Refinement and clarification calls are only on the unhappy paths and de-duped via the existing `_has_active_draft_for_parent` guard. |
| SMS/voice scope creep | Medium | Hooks are protocol stubs only. No vendor wiring. UI controls disabled behind tenant flag. |
| Vendor email provider rejects outbound | Low | Reuse the 4.2 provider-integration error handling: return a clear 409 when no provider is connected, keep the communication log/audit trail coherent, and let the user retry. |
| Multi-tenant leakage via colleague-token email collision | Low | Tokens are tenant-scoped; consumed email rows are written tenant-scoped contacts. Background refresh defaults to tenant-local/provider-public sources; cross-tenant suggestions require platform-admin workflow or explicit tenant opt-in. |

---

## 10. Definition of Done

A reasonable, single-developer-friendly checklist:

- [ ] Migration `20260622_milestone_4_3_vendor_comms.sql` lands; seed
      migration populates 5 system templates per tenant; dev verified.
- [ ] Models, repositories, and services for templates, proposals, vendor
      assignments, assignment contacts, colleague tokens, and background
      refreshes are unit-tested ≥ 80 %.
- [ ] `POST /vendor-communications/send` sends a real outbound through the user's
      connected Gmail; audit log shows `vendor_request_sent`.
- [ ] Simulated `Scheduled: YYYY-MM-DD` inbound creates an AI draft +
      a `vendor_proposals` row linked to the right task.
- [ ] Agent accepts the proposal from the AI Email Review page; the
      task's `due_date` updates and an audit log entry is written; a
      confirmation reply is drafted (auto-approved when confidence is
      high).
- [ ] Vague inbound reply produces a `needs_clarification` proposal; one
      click drafts the clarification email.
- [ ] Public `/v/:token` form successfully attaches a colleague contact to
      a vendor without marking it primary; the audit log fires.
- [ ] Vendor background refresh shows at least one tenant-cache or
      provider-public suggestion; applying a suggestion updates the vendor
      record.
- [ ] `/communications` page renders, filters, paginates, and downloads
      single-tx CSV; the admin export request flow is wired.
- [ ] SMS/voice UI affordances render with the coming-soon tooltip;
      tenant feature flag toggles them off cleanly.
- [ ] E2E test of the full round-trip passes in CI on dev.
- [ ] FRONTEND_UI_WORKFLOW_LOGIC.md §13.E updated to reflect 4.3
      vendor-proposal behavior. SYSTEM_DESIGN.md endpoints table updated
      with the new routes. milestones.txt 4.3 deliverables ticked.
- [ ] MILESTONE_4_3_TESTING_GUIDE.md authored (parallel to the 4.2 guide)
      with manual QA scripts.

---

## 11. Day-by-Day Estimate (Week 16)

| Day | Focus |
|---|---|
| Mon | Migration + models + repositories. Seed templates. |
| Tue | `VendorTemplateService`, `VendorProposalService`, engine hook. Unit tests. |
| Wed | API routers (`vendor_communications.py`, vendor extensions, public token). API tests. |
| Thu | Frontend: `VendorRequestModal`, `VendorProposalsPage`, vendor proposal panel inside `AiEmailReviewPage`. |
| Fri | Frontend: `/communications` page, `VendorListPage`, `VendorDetailPage`, `BackgroundRefreshDrawer`, public colleague form. |
| Sat | E2E flow on dev, fix-its, docs updates (FRONTEND_UI_WORKFLOW_LOGIC, SYSTEM_DESIGN, testing guide), seed for existing tenants. |
| Sun | Buffer / production cut. |

This stays within the 1-week Phase 4 closeout window and leaves Phase 5
on schedule (Milestone 5.1 starts Week 17 — June 29).

---

## 12. Open Questions for Client

These need a quick yes/no from Jake before Day 1 — they don't block
research but do change implementation specifics:

1. **Confirmation auto-approval** — should the system honor the 4.2 AI email
   auto-approval threshold for confirmation replies, or always require human
   approval for confirmations? (My recommendation: honor the same threshold
   for confirmations only; initial vendor requests remain user-triggered.)
2. **Colleague invite TTL default** — 7 days is my default. Acceptable,
   or should we mirror the FSBO milestone share TTL convention?
3. **Cross-tenant background search** — opt-in by tenant or always on
   for platform admin? (My recommendation: opt-in per tenant, defaulted
   off; the platform admin still sees the underlying data via
   `/platform/*`.)
4. **Vendor portal expansion** — the existing `/client/documents` view
   for vendors is read-only-uploads. Do we need an active "my open
   requests" tab for vendors this milestone, or is that a Phase 6
   item? (My recommendation: Phase 6.)

---

**End of Milestone 4.3 implementation plan.**
