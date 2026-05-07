# AI Email Automation — End-to-End Workflow

**Milestone:** 4.2 (Phase 4, Week 15)
**Last updated:** 2026-05-07

This document defines the canonical workflow for AI Email Automation in Velvet Elves: how an inbound email becomes a draft, how the draft becomes a sent reply, who acts at each stage, and what guarantees the system enforces.

It complements:
- **Implementation:** `app/services/ai_email_engine.py`, `app/api/v1/ai_emails.py`
- **Frontend:** `src/pages/AiEmailReviewPage.tsx`, `src/hooks/useAiEmails.ts`
- **Spec reference:** `FRONTEND_UI_WORKFLOW_LOGIC.md` §13.E (Communication & AI Email Flow)
- **Testing:** `MILESTONE_4_2_TESTING_GUIDE.md`, `MILESTONE_4_2_UI_TESTING_GUIDE.md`

---

## 1. High-level flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Inbound    │ ──▶ │   Provider   │ ──▶ │  Inbound     │ ──▶ │ Communication│
│    email     │     │   webhook    │     │  dispatcher  │     │ log (inbound)│
│  (Gmail/     │     │  /integra-   │     │  + dedupe +  │     │   row #1     │
│   Outlook/   │     │  tions/email │     │  tx matching │     │              │
│   iCloud)    │     │  /webhook/{p}│     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                       │
                                                                       │ inbound hook
                                                                       ▼
                                                              ┌──────────────────┐
                                                              │  AI Email Engine │
                                                              │ (handle_inbound) │
                                                              │                  │
                                                              │  1 Classify      │
                                                              │  2 Load context  │
                                                              │    (tx + docs)   │
                                                              │  3 Draft body    │
                                                              │  4 Tone + safe-  │
                                                              │    guards        │
                                                              │  5 Decide auto-  │
                                                              │    send vs       │
                                                              │    pending       │
                                                              └──────┬───────────┘
                                                                     │
                                            ┌────────────────────────┴───────────────────┐
                                            │                                            │
                                            ▼                                            ▼
                              ┌─────────────────────────┐               ┌────────────────────────────┐
                              │  approval_status        │               │  approval_status           │
                              │  = "auto_approved"      │               │  = "pending_review"        │
                              │  status =               │               │  status = "pending_review" │
                              │  "ready_to_send"        │               │  escalation_due_at = +36h  │
                              │                         │               │                            │
                              │  → human approves to    │               │  → human reviews in        │
                              │    actually send (we    │               │    /ai-emails              │
                              │    NEVER bypass         │               │                            │
                              │    human send button)   │               │                            │
                              └────────────┬────────────┘               └─────────────┬──────────────┘
                                           │                                          │
                                           └────────────────────┬─────────────────────┘
                                                                ▼
                                                  ┌──────────────────────────┐
                                                  │  Reviewer action         │
                                                  │   • Approve & Send       │
                                                  │   • Edit & Send          │
                                                  │   • Regenerate           │
                                                  │   • Discard              │
                                                  └────────────┬─────────────┘
                                                               │ Approve / Edit
                                                               ▼
                                                  ┌──────────────────────────┐
                                                  │  Email provider .send()  │
                                                  │  (Gmail / Outlook /      │
                                                  │   iCloud)                │
                                                  └────────────┬─────────────┘
                                                               │
                                                               ▼
                                                  ┌──────────────────────────┐
                                                  │  Communication log       │
                                                  │  row #1 updated:         │
                                                  │   approval_status =      │
                                                  │     "approved"           │
                                                  │   status = "sent"        │
                                                  │   approved_by, _at       │
                                                  │   provider_name,         │
                                                  │   provider_ref_id        │
                                                  │                          │
                                                  │  Audit log: ai_email     │
                                                  │   approve_and_send       │
                                                  └──────────────────────────┘
```

---

## 2. Roles and responsibilities

| Actor | Owns | Cannot do |
|---|---|---|
| **Inbound provider** (Gmail/Outlook/iCloud) | Delivering raw messages to our webhook | Decide what we reply with |
| **Inbound dispatcher** (`inbound_dispatch.py`) | Persisting one immutable inbound row, tenant resolution, transaction matching, hook fan-out | Generate replies — pure plumbing |
| **AI Email Engine** (`ai_email_engine.py`) | Classification, drafting, tone safeguards, persisting the outbound draft row | Send the email — that's the API layer's job |
| **Reviewer** (Agent / TC / TeamLead / Admin who owns the file) | Approving, editing, regenerating, or discarding drafts | Bypass the audit log or send without a connected provider |
| **Escalation runner** (Admin / cron) | Paging stale drafts (24–48 h with no human action) | Mutate the draft body itself |
| **Tenant Admin / TeamLead** | Configuring tone, disclaimer, escalation hours, auto-send threshold | Lower the threshold below tenant policy |

The system enforces an **AI-assists-humans-decide** boundary throughout: the engine produces drafts, but every external send is preceded by an explicit user action (Approve / Edit & Send) that hits the user's connected provider with their own credentials.

---

## 3. Inbound classification (Stage 1)

The engine classifies every inbound message into one of five buckets. Classification is rule-based (regex over subject + body) — not an LLM call — because keyword signals are very strong on routine real-estate traffic and we don't want to spend tokens on triage.

| Kind | Trigger phrases | Auto-send eligible? |
|---|---|---|
| `factual` | "when is closing", "closing date", "what time", "status", "any update", "where do we stand" | ✅ if confidence ≥ threshold and no assumptions |
| `document_request` | "send me the", "could you send", "do you have the", "share a copy", "where is the" | ✅ if matched document exists on file and confidence ≥ threshold |
| `vendor_reply` | `Scheduled: YYYY-MM-DD`, "we can come", "confirmed for", any ISO date in body | ❌ (always pending — affects task dates) |
| `uncertain` | A `?` in the subject or body but none of the above keywords match | ❌ (always pending) |
| `other` | Everything else (no question mark, no triggers) | Engine returns early; **no draft created** |

> The `other` bucket is intentional: not every inbound deserves an AI response. Acknowledgments, FYI emails, and chatter are logged but not drafted against.

---

## 4. Drafting (Stage 2)

For each non-`other` kind, the engine produces a draft using:

### 4.1 Inputs

- The inbound `subject`, `body_text`, `sender_email`.
- The matched **transaction** (loaded by `parent_log_id → transaction_id`): address, status, closing_date, key dates.
- The transaction's **non-deleted documents**: `name` and `type`.
- The **owner** user (the agent who owns the file): their email is added to CC so they're never blind to a send.
- The tenant's **AI email settings** (tone, disclaimer, threshold, escalation_hours).

### 4.2 Per-kind drafters

| Kind | What the drafter produces |
|---|---|
| `factual` | Pulls `closing_date` and `status` from the transaction. Replies with the requested fact in plain English; confidence 0.92 if both date + question phrasing align, 0.70 otherwise. |
| `document_request` | Maps the requested-doc keyword (`contract`, `inspection`, `disclosure`, …) to a `DocumentType`. If a matching, non-deleted document exists, says "Attached is the X." (confidence 0.93). If no match, says "the agent will follow up" (confidence 0.55, flagged assumption). |
| `vendor_reply` | Extracts an ISO date from the body. If found, confirms the schedule (confidence 0.90). If not, asks the vendor to re-send in `YYYY-MM-DD` format (confidence 0.60, flagged assumption). |
| `uncertain` | Generic acknowledgment: "the agent will follow up." Confidence 0.45, flagged assumption. |

### 4.3 Provider refinement (optional polish pass)

After the rule-based body is built, the engine optionally pipes it through `AIService.chat()` with this system prompt:

> "You are a Velvet Elves transaction coordinator drafting a concise email reply. Stay strictly on the facts you are given. Do not invent dates, prices, or names. Never give legal advice. Keep tone professional and warm."

The provider sees the inbound, the transaction summary, and the rule-based draft. It may only **rephrase** — never add new facts. If the provider is unavailable or returns empty, the rule-based body is used as-is.

### 4.4 Tone rules (`_apply_tone_rules`)

Applied to every draft body before persistence:

1. **Forbidden-phrase redaction** — patterns like `legal advice`, `you should sue`, `guaranteed`, `I/we advise you to` are replaced with `[redacted by safeguard — see agent]` and an assumption is added explaining the redaction.
2. **Sign-off** — appended based on tenant `tone`: `Cheers,` (friendly), `Best,` (concise), `Best regards,` (professional, default).
3. **Disclaimer** — the tenant's `disclaimer` is appended after a `—` separator. The default disclaimer states explicitly that VE does not provide legal advice.

The reviewer always sees the post-safeguard body, with redacted phrases highlighted.

---

## 5. Decision: auto-send vs pending review (Stage 3)

After the draft is built, the engine evaluates three conditions:

```python
auto_approve = (
    draft.confidence >= tenant.auto_send_threshold
    AND draft.kind in (factual, document_request)
    AND len(draft.assumptions) == 0
)
```

| Auto-send eligible | Outcome |
|---|---|
| ✅ All three pass | `approval_status = "auto_approved"`, `status = "ready_to_send"`. Still requires the human Approve click — we never bypass the user's email account. The auto-approved label tells the reviewer "this is safe to one-click send." |
| ❌ Any condition fails | `approval_status = "pending_review"`, `status = "pending_review"`. Surfaced in the bell badge, sidebar count, and review queue. |

Both states get an **`escalation_due_at`** timestamp = `now + tenant.escalation_hours` (default 36, range 24–48 per requirements).

> **Policy:** even auto-approved drafts route through the same Approve & Send button so the user's audit trail and CC list are identical regardless of confidence. The threshold tunes "how visible" the draft is, not "whether a human signs off."

---

## 6. Reviewer actions (Stage 4)

The reviewer opens `/ai-emails` and sees the queue. For the active draft, four actions are available.

### 6.1 Approve & Send

```
POST /api/v1/ai-emails/{log_id}/approve
```

1. Verifies the user has an active email provider; otherwise 409.
2. Resolves the provider via `get_email_provider_for_user`.
3. Builds an `OutboundEmail` from the draft (recipients, cc, subject, body, transaction_id, AI metadata).
4. Calls `provider.send(message)`.
5. Updates the same `communication_logs` row:
   - `status = "sent"` (or `"failed"` on provider rejection)
   - `approval_status = "approved"`
   - `approved_by`, `approved_at`
   - `provider_name`, `provider_ref_id`
   - `error_message` if applicable
6. Writes an audit log entry (`action=approve_and_send`, `entity_type=ai_email`).

The communication log row remains the single source of truth for this conversation — pre-approval and post-send live in the same row, which preserves chronology and idempotency.

### 6.2 Edit & Send

```
POST /api/v1/ai-emails/{log_id}/edit-and-send
{ "subject": "...", "body_text": "...", "cc": ["..."] }
```

1. Replaces `body`, optionally `subject` and `cc_emails`.
2. **Clears `ai_assumptions`** — a human approved the content, so the flagged-assumption display is no longer relevant.
3. Continues with the same send path as Approve & Send.
4. Audit log entry: `action=edit_and_send`.

### 6.3 Regenerate

```
POST /api/v1/ai-emails/{log_id}/regenerate
```

1. Soft-discards the current draft (`discarded_at`, `approval_status="regenerated"`).
2. Re-runs the engine on the original inbound (`parent_log_id`).
3. Returns the new draft id and confidence.
4. Audit log entry: `action=regenerate`.

The original inbound is **never** modified. Multiple regenerations produce multiple discarded drafts in the audit trail.

### 6.4 Discard

```
POST /api/v1/ai-emails/{log_id}/discard
{ "reason": "..." }
```

1. Stamps `discarded_at`, `discarded_by`, `approval_status="discarded"`, `status="discarded"`.
2. Records the reason in `error_message` (overloaded since it's already a free-text field).
3. Hides the draft from the queue but preserves the row for audit.
4. Audit log entry: `action=discard`.

---

## 7. State machine

```
                                     ┌─────────────────┐
                                     │   pending_      │
              ┌─────────────────────▶│   review        │◀─────────────────────┐
              │                      └────────┬────────┘                      │
              │                               │                               │
   (engine creates                            │                               │
    draft, low conf                           │                               │
    or assumptions)                           │                               │
                                              │                               │
                                              │  Approve / Edit & Send        │
                                              │  (provider .send succeeds)    │
                                              ▼                               │
                                     ┌─────────────────┐                      │
   ┌─────────────────┐               │   approved      │                      │
   │  auto_approved  │──────────────▶│   status=sent   │                      │
   │  status=        │  Approve      │                 │                      │
   │  ready_to_send  │  (one-click)  └─────────────────┘                      │
   └─────────┬───────┘                                                         │
             ▲                                                                 │
             │                                                                 │
             │ (engine creates                                                 │
             │  draft, high conf,                                              │
             │  no assumptions,                                                │
             │  factual/doc_req)                                               │
                                                                               │
                                              ┌────────────┐                   │
                                              │  Regenerate│ creates new      │
                                              │  on draft  │ pending_review ──┘
                                              └─────┬──────┘
                                                    │
                                                    ▼
                                          ┌────────────────┐
                                          │  regenerated   │ (terminal — old draft)
                                          │  discarded_at  │
                                          └────────────────┘

                                          ┌────────────────┐
                                          │   discarded    │ (terminal)
                                          │  discarded_at  │
                                          └────────────────┘

                                          ┌────────────────┐
                                          │     failed     │ (Approve attempted but
                                          │  status=failed │  provider .send rejected;
                                          │  error_message │  draft stays pending_review
                                          │                │  for retry)
                                          └────────────────┘
```

**Invariants:**
- `approval_status` and `status` move forward only; no draft re-enters `pending_review` after `approved`.
- `discarded_at` is set-once. The same row never un-discards.
- A failed send leaves the draft in `pending_review` so the user can retry without losing the body.

---

## 8. Escalation (Stage 5)

If a draft sits in `pending_review` past `escalation_due_at`, the escalation runner pages the responsible user.

### 8.1 Trigger

```
POST /api/v1/ai-emails/escalations/run
```

- **Auth:** Admin only.
- **Default cadence:** scheduled cron every 1–2 hours.
- **Scope:** the calling Admin's tenant only (use `tenant_only=false` to run cross-tenant — only meaningful for the operator).

### 8.2 What it does

For every draft where `escalation_due_at <= now()` AND `escalation_sent_at IS NULL` AND `discarded_at IS NULL`:

1. Stamps `escalation_sent_at = now()` (idempotency guard — re-running the endpoint won't re-page).
2. Inserts a `channel='system'`, `direction='internal'` row in `communication_logs` linked via `parent_log_id` back to the draft, with a body like *"An AI-prepared reply has been waiting for your approval since X. Please review at /ai-emails/{id}."*
3. Writes an audit log entry: `action=escalate`.

In the UI, the draft card gets a red **Escalated** pill. The next bell badge refresh increments by the number of escalations.

### 8.3 Configuration

`tenants.settings_json["ai_email"].escalation_hours` — clamped to 24–48 by the API schema. Default 36.

---

## 9. Notification touchpoints

The same draft surfaces in three places, all driven by a single source query (`list_pending_ai_drafts`):

| Surface | Where | Updates |
|---|---|---|
| **Topbar bell badge** | All internal pages | Polled every 60 s via `/notifications/pending`. Drafts always count toward unread until acted on. |
| **Notifications panel** | Click the bell | Top callout: "N AI drafts awaiting review" (clickable to `/ai-emails`). Secondary callout: "N outbound emails sent on your behalf today." |
| **Sidebar Intelligence** | Left rail, all internal pages except Attorney/FSBO | Orange chip with the live count next to "AI Email Review." |

---

## 10. Tenant configuration

Stored at `tenants.settings_json -> 'ai_email'`:

```json
{
  "tone": "professional",      // 'professional' | 'friendly' | 'concise'
  "disclaimer": "...",          // Appended to every draft body
  "escalation_hours": 36,       // 24–48
  "auto_send_threshold": 0.9    // 0.0–1.0
}
```

Defaults are applied when the key is missing. **Admin** and **TeamLead** roles can update via:

```
PUT /api/v1/ai-emails/settings
```

Every settings change is audit-logged (`entity_type=tenant`, `action=update_ai_email_settings`).

---

## 11. End-to-end example: factual closing-date question

### Step 1 — inbound arrives

Client sends: *"Hi — when is closing for the Maple St deal? Thanks!"*

```
POST /integrations/email/webhook/gmail?user_id=<agent_user>
```

Gmail Pub/Sub routes the push; webhook re-fetches the message; dispatcher persists:

```sql
communication_logs (id=A, channel=email, direction=inbound,
                    transaction_id=<txMaple>, sender=client@…,
                    subject="Quick question",
                    body="Hi — when is closing for the Maple St deal?")
```

### Step 2 — inbound hook fires

`ai_email_inbound_hook(A, inbound, txMaple)` is invoked.

### Step 3 — engine classifies

`_classify(inbound) → "factual"` (matched on "when is closing").

### Step 4 — engine drafts

```
Hi {first name},

Quick update on 123 Maple St: we are tracking to a Monday, June 15, 2026 closing.

Best regards,
Velvet Elves

— This message was prepared by Velvet Elves AI ...
```

`confidence = 0.92`, `assumptions = []`, `source_data = {address, closing_date, status}`.

### Step 5 — engine persists

```sql
communication_logs (id=B, parent_log_id=A,
                    direction=outbound, is_ai_generated=true,
                    ai_kind="factual", ai_confidence=0.92,
                    approval_status="auto_approved",
                    status="ready_to_send",
                    escalation_due_at=now()+36h,
                    cc=["agent@firm.com"])
```

### Step 6 — reviewer sees the queue

Agent's bell badge increments. Sidebar **Intelligence → AI Email Review (1)**. They open `/ai-emails`, see the draft, verify the closing date in the right pane matches the transaction, and click **Approve & Send**.

### Step 7 — system sends

API resolves the agent's Gmail integration, sends via `provider.send()`, updates row B:

```sql
UPDATE communication_logs
   SET status="sent", approval_status="approved",
       approved_by=<agent>, approved_at=now(),
       provider_name="gmail", provider_ref_id=<gmailId>
 WHERE id=B;
```

Audit log entry written. Toast shows "Sent." Draft disappears from the queue. Badge decrements on next poll.

### Step 8 — reply lands in the client's inbox

The reply is sent from the agent's actual Gmail account (not a no-reply address), CC'd to the agent's own email so they have a clean copy in their Sent folder.

---

## 12. Edge-case branches

| Scenario | Path | Outcome |
|---|---|---|
| Inbound with no transaction context | dispatcher matches by sender/cc → if no party email matches, leaves `transaction_id` null | Engine still drafts (`kind=factual`/`uncertain`), but flags "no transaction context found" assumption. Always `pending_review`. |
| Document request, document not on file | `_guess_document` returns None | Body says "agent will follow up", confidence 0.55, assumption flagged. `pending_review`. |
| Vendor reply with vague date | regex finds no ISO date | Body asks vendor to re-send in `YYYY-MM-DD`, confidence 0.60, assumption flagged. `pending_review`. |
| AI provider down | `chat_completion` raises | Rule-based body persists; no exception bubbles to dispatch. Refinement is best-effort. |
| Reviewer has no email integration | Approve hits 409 | Toast: "No active gmail integration." Draft stays `pending_review`. User reconnects, retries. |
| Reviewer in two tabs approves twice | First call wins (status flips to `approved`); second hits the actionable-draft guard | 400: "Draft is in state 'approved' and cannot be modified." |
| Inbound is a duplicate | `provider_ref_id` unique index hit | Dispatcher returns `None`, no inbound row created, no engine call. |
| Tenant has `auto_send_threshold = 1.0` | No draft can ever auto-approve | Every draft is `pending_review` (effectively disables auto-send). |
| Forbidden phrase in inbound spills into draft | Tone rules redact and flag | Draft cannot auto-approve (assumptions list non-empty). |

---

## 13. Auditing and compliance

Every state transition writes to `audit_logs`:

| Action | Actor | Entity | When |
|---|---|---|---|
| `approve_and_send` | Reviewer | `ai_email` (draft id) | After successful send |
| `edit_and_send` | Reviewer | `ai_email` | After successful send of edited body |
| `regenerate` | Reviewer | `ai_email` (old id) | After old draft is discarded |
| `discard` | Reviewer | `ai_email` | After soft-discard |
| `escalate` | Admin (or system user) | `ai_email` | After escalation row created |
| `update_ai_email_settings` | Admin / TeamLead | `tenant` | After PUT /settings |

The `communication_logs` table itself is append-only for body content; only AI-workflow fields (approval, escalation, discard) are updated. The engine never deletes rows.

---

## 14. SLAs and operational policy

| Metric | Target |
|---|---|
| Time from inbound webhook to draft persisted | < 5 s (rule-based path), < 15 s (with provider polish) |
| Time from inbound to bell badge update | ≤ 60 s (next poll) |
| Escalation latency | runner cadence + ≤ 2 min |
| Auto-send threshold | Tenant policy (default 0.90) — never below 0.85 in production |
| Escalation hours | 24–48 (req 4.2) |
| Communication log retention | 2 years (req 6.1) |

If any draft sits in `pending_review` longer than `escalation_hours × 2` without action, that's a process incident — investigate the responsible user's notification setup.

---

## 15. Out of scope (preserved for later milestones)

These are intentionally **not** in 4.2:

- **Vendor template parsing for date proposals** (Milestone 4.3) — the engine recognizes `vendor_reply` kind but does not yet propose task-date updates from the parsed dates.
- **SMS / voice replies** — the data model already supports SMS metadata (`channel`, `provider_name`), but no SMS provider is wired.
- **Auto-distribution after send** — the e-sign auto-distribution from Milestone 3.4 stays in its own pipeline; AI replies are addressed only to the inbound's sender + the file owner CC.
- **Cross-tenant escalation** — the runner is tenant-scoped by default. Multi-tenant ops should call it per tenant from a scheduler.
- **AI-driven outbound initiation** — the engine only responds to inbound mail. Drafting an outbound from scratch (e.g. proactive client update) is a future capability.

---

## 16. Quick reference

| Need | File / Endpoint |
|---|---|
| Trigger an inbound (test) | `POST /api/v1/integrations/email/webhook/{provider}?user_id=...` |
| List pending drafts | `GET /api/v1/ai-emails/drafts` |
| Approve and send | `POST /api/v1/ai-emails/{id}/approve` |
| Edit and send | `POST /api/v1/ai-emails/{id}/edit-and-send` |
| Regenerate | `POST /api/v1/ai-emails/{id}/regenerate` |
| Discard | `POST /api/v1/ai-emails/{id}/discard` |
| Run escalations | `POST /api/v1/ai-emails/escalations/run` (admin) |
| Read tenant settings | `GET /api/v1/ai-emails/settings` |
| Update tenant settings | `PUT /api/v1/ai-emails/settings` (admin/team_lead) |
| Browse pending in UI | `/ai-emails` |
| Bell badge feed | `GET /api/v1/notifications/pending` |
| Engine implementation | `app/services/ai_email_engine.py` |
| API implementation | `app/api/v1/ai_emails.py` |
| Frontend page | `src/pages/AiEmailReviewPage.tsx` |
| DB migration | `supabase/migrations/20260507_milestone_4_2_ai_email.sql` |

---

**End of workflow specification.**
