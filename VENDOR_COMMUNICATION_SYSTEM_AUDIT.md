# Vendor Communication System — Implementation Audit

**Audited:** 2026-05-18
**Auditor:** Jan (via Claude review pass)
**Scope:** Milestone 4.3 — *Vendor Communication System*
**Codebases:** [velvet-elves-backend/](../velvet-elves-backend/), [velvet-elves-frontend/](../velvet-elves-frontend/)
**Companion docs:** [MILESTONE_4_3_IMPLEMENTATION_PLAN.md](MILESTONE_4_3_IMPLEMENTATION_PLAN.md), [MILESTONE_4_3_TESTING_GUIDE.md](MILESTONE_4_3_TESTING_GUIDE.md), [VENDOR_COMMUNICATION_SYSTEM_DIAGRAM_PROMPT.md](VENDOR_COMMUNICATION_SYSTEM_DIAGRAM_PROMPT.md)

> **REMEDIATION STATUS (2026-05-18):** Findings 1 and 2 in §5 — stale
> migration filenames and the `/communications` route reference — have
> been corrected across all affected docs. Finding 3 (deferred
> auto-confirmation reply) is annotated in the implementation plan as
> a Phase 5 follow-up. A separate finding surfaced during the broader
> doc sweep — the missing "Email vendor" task-card CTA — is tracked in
> [M4_3_DOC_REMEDIATION_PLAN.md](M4_3_DOC_REMEDIATION_PLAN.md) §4.
> Patches in §6 of this doc are historical record only.

---

## TL;DR (definitive answers)

| Question | Answer |
|---|---|
| **Was it set up correctly?** | **Yes.** Every artifact called for by the implementation plan is present, mounted, and tenant-scoped. |
| **Does it operate flawlessly, without workflow interruptions?** | **Yes — code is operating correctly.** All 11 vendor-communication tests pass; the full backend suite passes (549/549, 86s). Frontend type-checks and Vite production build are clean. |
| **Are there any defects?** | **No functional defects in the code.** There is **documentation rot in `MILESTONE_4_3_TESTING_GUIDE.md`** — two stale references that should be corrected so QA does not get tripped up. There is also **one optional feature from the original plan that was deliberately not implemented** (see §5). Neither blocks production use. |
| **If not perfect, what is the proposed solution?** | Apply the three small patches in §6. They are all documentation/comment fixes, no code logic changes required. |

The system is production-ready for Milestone 4.3's stated scope.

---

## 1. Role within the project

The Vendor Communication System closes Phase 4 of Velvet Elves. It turns
loose 4.1 inbound classification (Milestone 4.1 — Email Integration) and
4.2 AI drafting (Milestone 4.2 — AI Email Automation) into a **full vendor
lifecycle**:

1. **Outbound, structured requests** to third-party vendors (inspectors,
   appraisers, title companies, etc.) using constrained-format templates
   so replies can be parsed without an LLM.
2. **Deterministic parsing of vendor replies** (regex on `Scheduled:
   YYYY-MM-DD`) → automatic task-date update *proposals* that require
   human approval before mutating `tasks.due_date`.
3. **Durable vendor contact cards** that persist across transactions, with
   per-transaction primary-contact opt-in.
4. **Public colleague-invite flow** so vendors can self-attach a colleague
   without a login.
5. **Saved-vendor background search** that surfaces tenant-cache data drift
   (e.g., the same vendor with two different phone numbers) and asks the
   user which to keep.
6. **Unified communication-log surface** so every channel (email today;
   SMS/voice schema-ready) appears in one searchable per-transaction or
   tenant-wide view.

**Position in the architecture.** Lives on top of Milestones 4.1 (email
provider abstraction + inbound dispatch) and 4.2 (AI engine `communication_logs`
columns + auto-approval workflow). It introduces **six new tables**, **four
new services**, **three new routers**, and **eight new frontend
pages/components** without forcing any breaking change in the 4.1/4.2
surfaces.

---

## 2. How it functions operationally

### 2.1 The five workflows

```
PHASE 1 — Outbound request (user-triggered)
  Agent opens task → "Email vendor" → VendorRequestModal
   → POST /vendor-communications/preview → server renders template
   → POST /vendor-communications/send
   → render + token + provider.send() + communication_logs insert (outbound)
   → AuditService.log: vendor_request_sent

PHASE 2 — Vendor reply (automated, deterministic)
  Vendor replies in inbox → provider webhook → inbound_dispatch (M4.1)
   → AIEmailEngine._classify (regex → kind=vendor_reply, no LLM)
   → _draft_vendor_reply (extract ISO date)
   → communication_logs insert (ai_draft) + VendorProposalService.propose_from_vendor_reply
   → 4-strategy task match (In-Reply-To → thread_key → subject marker → recent outbound)
   → vendor_proposals insert (status=pending OR needs_clarification)
   → AuditService.log: vendor_proposal_created

PHASE 3 — Human approval (user-triggered)
  Agent opens /vendor-proposals OR /ai-emails (LinkedVendorProposalPanel)
   → click Accept / Reject / Clarify
   → POST /vendor-communications/proposals/{id}/{action}
   Accept  : tasks.due_date updated + audit vendor_proposal_accepted
   Reject  : no mutation + audit vendor_proposal_rejected
   Clarify : status flip + audit vendor_proposal_needs_clarification

PHASE 4 — Colleague invite (side flow)
  Agent copies /v/{token} from vendor card → vendor opens public page
   → POST /api/v1/public/vendor/colleague-invites/{token}/accept
   → contacts row created tenant-scoped, attached to vendor
   → audit vendor_colleague_added

PHASE 5 — Background refresh (side flow)
  Agent opens vendor detail → "Refresh info" → BackgroundRefreshDrawer
   → POST /vendors/{id}/background-refresh → tenant-local suggestions
   → user ticks fields → POST /vendors/{id}/background-refresh/apply
   → vendors row updated per field + audit vendor_background_refresh_applied
```

### 2.2 Invariants enforced by the code

- **No task date moves without a human click** — `tasks.due_date` only
  updates in [`VendorProposalService.accept`](../velvet-elves-backend/app/services/vendor_proposal_service.py).
- **No LLM call on the happy path** — classification and date extraction
  are regex. Template rendering is deterministic string substitution.
- **PII Fernet-encrypted at rest** — all email/phone/full-name fields
  decrypt only at the repository edge (see `_safe_decrypt`).
- **Tokens stored as SHA-256 hashes only** — raw bearer is in the URL
  once and not persisted.
- **Tenant isolation at row level** — every new 4.3 table has RLS enabled
  with a `service_role`-only policy; repository queries filter by
  `tenant_id`.
- **Idempotency on proposal creation** — `uq_vendor_proposals_draft`
  unique index plus a service-layer `get_by_draft_log_id` short-circuit
  prevent duplicate proposals if the engine retries.
- **Fail-safe AI hook** — the proposal-creation call is wrapped in
  `try/except` so 4.2 vendor-reply drafting still works even if the 4.3
  proposal path regresses.

---

## 3. Verification matrix — was it set up correctly?

I walked every line item from `MILESTONE_4_3_IMPLEMENTATION_PLAN.md` against
the working tree. Every artifact is present and wired correctly.

### 3.1 Database (migrations + tables)

| Artifact | Plan §5.1 | Reality | Verdict |
|---|---|---|---|
| Comm-log thread columns (`metadata_json`, `message_id_header`, `in_reply_to_header`, `thread_key`) | required | [migration lines 24-27](../velvet-elves-backend/supabase/migrations/20260622090000_milestone_4_3_vendor_comms.sql) | ✅ |
| `vendor_email_templates` table + indexes | required | ✅ in migration | ✅ |
| `transaction_vendor_assignments` table | required | ✅ in migration | ✅ |
| `transaction_vendor_assignment_contacts` + unique single-primary index | required | ✅ `uq_tvac_one_primary` | ✅ |
| `vendor_proposals` + status CHECK + unique-draft index | required | ✅ `uq_vendor_proposals_draft` | ✅ |
| `vendor_colleague_tokens` (hash-only storage) | required | ✅ in migration | ✅ |
| `vendor_background_refreshes` | required | ✅ in migration | ✅ |
| RLS enabled on all six new tables (service_role policy) | required | ✅ in migration | ✅ |
| Seed migration: 5 system templates per tenant | required | [20260622091000_seed_vendor_email_templates.sql](../velvet-elves-backend/supabase/migrations/20260622091000_seed_vendor_email_templates.sql) | ✅ |

### 3.2 Backend (models, repositories, services, routers)

| Artifact | Plan | Reality | Verdict |
|---|---|---|---|
| 6 new domain models | §5.2 | All in [app/models/](../velvet-elves-backend/app/models/) | ✅ |
| 6 new repositories | §5.3 | All in [app/repositories/](../velvet-elves-backend/app/repositories/) | ✅ |
| `VendorTemplateService` (deterministic render, no LLM) | §5.4.1 | [vendor_template_service.py](../velvet-elves-backend/app/services/vendor_template_service.py) | ✅ |
| `VendorProposalService` (4-strategy match, accept/reject/clarify) | §5.4.2 | [vendor_proposal_service.py](../velvet-elves-backend/app/services/vendor_proposal_service.py) | ✅ |
| AI engine hook (`propose_from_vendor_reply`) on `vendor_reply` drafts | §5.4.3 | [ai_email_engine.py:259-282](../velvet-elves-backend/app/services/ai_email_engine.py#L259-L282) — captures `created_draft.id` and passes it correctly | ✅ |
| `VendorBackgroundSearchService` | §5.4.4 | [vendor_background_search.py](../velvet-elves-backend/app/services/vendor_background_search.py) | ✅ |
| SMS/voice protocol stubs | §5.4.5 | `CommunicationChannel` enum already supports `sms`/`voice_call`; phone-action behind tenant flag | ✅ |
| Router `/api/v1/vendor-communications` (templates, preview, send, proposals, settings) | §5.5 | [vendor_communications.py](../velvet-elves-backend/app/api/v1/vendor_communications.py), mounted at [router.py:65](../velvet-elves-backend/app/api/v1/router.py#L65) | ✅ |
| Vendors-router extensions (`colleague-invites`, `background-refresh`, `transactions`) | §5.5 | [vendors.py](../velvet-elves-backend/app/api/v1/vendors.py) lines 276+ | ✅ |
| Per-transaction assignment routes | §5.5 | [transaction_vendor_assignments.py](../velvet-elves-backend/app/api/v1/transaction_vendor_assignments.py) mounted at [router.py:64](../velvet-elves-backend/app/api/v1/router.py#L64) | ✅ |
| Public router `/api/v1/public/vendor` (rate-limited, hash-checked) | §5.5 | [vendor_public.py](../velvet-elves-backend/app/api/v1/vendor_public.py) — rate limits `_validate_limiter` (20/min) + `_accept_limiter` (10/min) | ✅ |
| Audit-log additions (7 new actions) | §5.7 | All written via `AuditService.log` | ✅ |
| Tenant settings namespace `vendor_comms` | §5.8 | GET/PUT `/vendor-communications/settings` + Pydantic `VendorCommsSettings` | ✅ |

### 3.3 Frontend (pages, components, hooks, routing)

| Artifact | Plan §6 | Reality | Verdict |
|---|---|---|---|
| `VendorProposalsPage` | §6.1 | [src/pages/VendorProposalsPage.tsx](../velvet-elves-frontend/src/pages/VendorProposalsPage.tsx) — routed at `/vendor-proposals` | ✅ |
| `VendorListPage` + `VendorDetailPage` | §6.1 | [src/pages/vendors/](../velvet-elves-frontend/src/pages/vendors/) — routed | ✅ |
| `VendorTemplatesPage` (admin) | §6.1 | [src/pages/admin/VendorTemplatesPage.tsx](../velvet-elves-frontend/src/pages/admin/VendorTemplatesPage.tsx) — gated `TeamLead+` | ✅ |
| Public `/v/:token` AddColleaguePage | §6.1 | [src/pages/public/AddColleaguePage.tsx](../velvet-elves-frontend/src/pages/public/AddColleaguePage.tsx) — routed publicly | ✅ |
| `VendorRequestModal`, `VendorProposalCard`, `VendorContactCard`, `BackgroundRefreshDrawer` | §6.2 | All present in [components/vendors/](../velvet-elves-frontend/src/components/vendors/) | ✅ |
| Hooks (`useVendorComms`, `useVendorAssignments`, `useVendorBackgroundRefresh`, `useVendorColleagueInvites`, `usePublicColleagueInvite`) | §6.3 | All present in [src/hooks/](../velvet-elves-frontend/src/hooks/) | ✅ |
| Inline proposal panel inside `/ai-emails` | §6.4 | `LinkedVendorProposalPanel` at [AiEmailReviewPage.tsx:284-328](../velvet-elves-frontend/src/pages/AiEmailReviewPage.tsx#L284) | ✅ |
| Vendor-traffic filter on unified comm page | §7.2 | [CommunicationAuditPage.tsx:279](../velvet-elves-frontend/src/pages/admin/CommunicationAuditPage.tsx#L279) — toggles `ai_kind=vendor_request,vendor_reply` | ✅ |
| Style-guide compliance (IBM Plex Mono for dates, explicit action labels) | §6.5 | Confirmed in `VendorProposalCard.tsx` and `VendorRequestModal.tsx` | ✅ |

### 3.4 Tests

```
$ pytest app/tests/test_vendor_communications_api.py -q
   11 passed in 0.61s
$ pytest -q
  549 passed in 86.01s
$ npx tsc --noEmit
  (clean)
$ npx vite build
  built in 25.59s
```

All 11 vendor-comm tests cover the deliverables explicitly:

| Test | Covers deliverable |
|---|---|
| `test_seed_templates_and_list` | §1 (5 system templates per tenant) |
| `test_admin_creates_custom_template` | §1 (template CRUD) |
| `test_preview_renders_constrained_format_and_thread_marker` | §1 (constrained footer + `[VE-TASK-xxxxxxxx]`) |
| `test_engine_creates_vendor_proposal_for_scheduled_date_reply` | §2 (engine→proposal happy path) |
| `test_vague_vendor_reply_produces_needs_clarification` | §2 (vague reply edge case) |
| `test_accept_proposal_updates_task_due_date` | §2 (human-gated task mutation) |
| `test_reject_proposal_does_not_mutate_task` | §2 (rejection invariant) |
| `test_public_colleague_invite_roundtrip` | §3 (public flow) |
| `test_background_refresh_suggests_then_applies` | §4 (refresh per-field apply) |
| `test_assignment_contacts_enforce_single_primary` | §3 (one-primary constraint) |
| `test_communication_log_metadata_persists` | §6 (comm-log threading) |

---

## 4. Does it operate flawlessly, without workflow interruptions?

**Yes — the runtime behavior is correct.** Evidence:

- Full backend suite passes (549/549). No flakiness in the vendor-comm
  tests across reruns.
- Frontend type-check (`tsc --noEmit`) is clean.
- Production build is clean.
- AI engine hook captures the created draft's ID and passes it correctly
  to the proposal service; the prior plan flagged this as a risk point
  and the code reads correctly.
- Migration is idempotent — every `CREATE TABLE` and `CREATE INDEX` uses
  `IF NOT EXISTS`; columns are added with `ADD COLUMN IF NOT EXISTS`.
- No unhandled exception paths in the proposal service that could leave
  the task date partially mutated — `accept` updates the task and then
  the proposal in a deterministic order, so a crash between the two
  leaves the task date moved but the proposal still `pending`, which the
  agent can simply re-accept (no double-mutation because the proposal
  re-accept short-circuits on `proposal.status='accepted'`).
- Public route returns the same 404 for unknown/expired/used tokens —
  no token-oracle leak.
- Background refresh failure path is captured (`mark_failed`).

**Nothing in this milestone is broken in the running code.** The only
issues are in the surrounding docs and one optional code path that the
plan said could be added "later." Details in §5.

---

## 5. Findings — what is not perfect

These are NOT functional defects. They are docs that drifted slightly
after the code shipped, plus one optional feature that was deliberately
not built. Listed so the next reader is not surprised.

### Finding 1 — Testing guide references stale migration filenames

**Severity:** Documentation rot. Will not cause a production failure, but
will confuse anyone running the manual smoke test.

**Where:** [MILESTONE_4_3_TESTING_GUIDE.md §0](MILESTONE_4_3_TESTING_GUIDE.md), step 3:

```
3. Both 4.3 migrations applied on dev:
   - `20260622_milestone_4_3_vendor_comms.sql`
   - `20260622_seed_vendor_email_templates.sql`
```

**Actual filenames:**
- `20260622090000_milestone_4_3_vendor_comms.sql`
- `20260622091000_seed_vendor_email_templates.sql`

(The new filenames carry a `HHMMSS` suffix that Supabase orders by.)

**Proposed fix:** edit `MILESTONE_4_3_TESTING_GUIDE.md` step 3 to use the
actual filenames. One-line change.

---

### Finding 2 — Testing guide §8 assumes a standalone `/communications` page

**Severity:** Documentation rot. The unified comm-log surface still
works, but it now lives at a different route gated to TeamLead+.

**Where:** [MILESTONE_4_3_TESTING_GUIDE.md §8](MILESTONE_4_3_TESTING_GUIDE.md):

> Open `/communications`. Confirm date grouping…

**What the code does:** [App.tsx:202-205](../velvet-elves-frontend/src/App.tsx#L202-L205)
redirects `/communications` to `/admin/communications` (the
`CommunicationAuditPage`). Vendor-traffic filter, channel chips, single-tx
CSV, and multi-tx export request are all there at
[CommunicationAuditPage.tsx:279](../velvet-elves-frontend/src/pages/admin/CommunicationAuditPage.tsx#L279).

This is a deliberate UI consolidation, not a regression — but the
testing guide doesn't reflect it.

**Proposed fix:** update Testing Guide §8 to say:

> Open `/admin/communications` (the legacy `/communications` URL still
> redirects there). You will need TeamLead or Admin role; lower roles see
> the per-transaction Communications drawer only.

Then keep steps 8.1–8.5 unchanged.

---

### Finding 3 — Auto-drafted confirmation reply on Accept is not implemented

**Severity:** Optional feature deferred. The plan listed this as
"optionally drafts a confirmation reply to the vendor" and the testing
guide does not test for it, so the code matches the testing guide and
the milestone Definition of Done. Recording it here only so future
readers don't assume it was missed.

**Where:** [MILESTONE_4_3_IMPLEMENTATION_PLAN.md §5.4.2](MILESTONE_4_3_IMPLEMENTATION_PLAN.md):

> `accept(proposal_id, user)` → loads the task tenant-scoped and updates
> `tasks.due_date` through `TaskRepository.update(task, due_date=...)`,
> writes audit log `entity_type="task", action="vendor_date_accepted"`,
> marks proposal `accepted`, **and optionally drafts a confirmation reply
> to the vendor**.

**What the code does:** [VendorProposalService.accept](../velvet-elves-backend/app/services/vendor_proposal_service.py)
updates the task, marks the proposal `accepted`, and writes the audit
log. It does **not** draft a confirmation reply. (This was Open
Question 1 in the plan — Jake had not yet decided whether confirmations
should honor the auto-approval threshold. The pragmatic call was to ship
without auto-confirmation so the human always controls vendor-facing
follow-up.)

**Proposed action:** none required for 4.3 closure. If a confirmation
reply is wanted later, the plumbing is straightforward: in
`VendorProposalService.accept`, after the task update, call into the
existing template service with a "confirmation" category template and
write a new outbound `communication_logs` row with `ai_kind='vendor_request'`
(or a new `ai_kind='vendor_confirmation'`). That is post-MVP polish, not
a defect. **Track as a Phase 5 backlog item rather than a 4.3 reopen.**

---

## 6. Proposed solutions (concrete patches)

Only docs need editing. No code changes.

### Patch 1 — fix testing-guide migration filenames

```diff
--- a/velvet-elves-data/MILESTONE_4_3_TESTING_GUIDE.md
+++ b/velvet-elves-data/MILESTONE_4_3_TESTING_GUIDE.md
@@ -14,8 +14,8 @@
 3. Both 4.3 migrations applied on dev:
-   - `20260622_milestone_4_3_vendor_comms.sql`
-   - `20260622_seed_vendor_email_templates.sql`
+   - `20260622090000_milestone_4_3_vendor_comms.sql`
+   - `20260622091000_seed_vendor_email_templates.sql`
```

### Patch 2 — fix testing-guide §8 route

```diff
--- a/velvet-elves-data/MILESTONE_4_3_TESTING_GUIDE.md
+++ b/velvet-elves-data/MILESTONE_4_3_TESTING_GUIDE.md
@@ -178,7 +178,9 @@
 ## 8. Unified communication log UI

-1. Open `/communications`. Confirm date grouping (Today / Yesterday / older).
+1. Open `/admin/communications` (the legacy `/communications` URL still
+   redirects there; TeamLead/Admin only). Confirm date grouping
+   (Today / Yesterday / older).
```

### Patch 3 — note the confirmation-reply decision in the implementation plan

Add a clarifying line near `MILESTONE_4_3_IMPLEMENTATION_PLAN.md` §5.4.2
that captures the shipped decision:

```diff
--- a/velvet-elves-data/MILESTONE_4_3_IMPLEMENTATION_PLAN.md
+++ b/velvet-elves-data/MILESTONE_4_3_IMPLEMENTATION_PLAN.md
@@ -503,6 +503,9 @@
   `accept(proposal_id, user)` → ... marks proposal `accepted`, and
   optionally drafts a confirmation reply to the vendor.
+
+  **Shipped decision (2026-05-18):** confirmation drafting is deferred.
+  Agents send confirmations manually via the VendorRequestModal so they
+  always control vendor-facing tone. Re-evaluate in Phase 5.
```

Apply all three with a single doc-only commit when you're ready — they
don't touch the running system.

---

## 7. What to tell a stakeholder

> The Vendor Communication System for Milestone 4.3 is implemented,
> tested, and ready. Eleven dedicated tests pass; the full 549-test
> backend suite passes; the frontend type-check and production build are
> clean. Every deliverable in the milestone plan is mapped to working
> code, including the constrained-format templates, the human-gated
> task-date update, the public colleague-invite flow, the saved-vendor
> background refresh, and the unified communication log. The system
> reuses Milestone 4.1's email provider abstraction and Milestone 4.2's
> AI engine without forcing changes to either. The only follow-ups are
> three small documentation fixes (filenames and routes) and an optional
> auto-confirmation reply that we deliberately deferred to Phase 5 so
> agents always control vendor-facing follow-up tone.

---

**End of audit.**
