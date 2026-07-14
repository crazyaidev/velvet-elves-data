# Milestone 4.2 — AI Email Automation: Testing Guide

**Scope:** Verify the AI email response engine, draft review workflow, escalation reminders, in-app notifications, tone-rule safeguards, and tenant settings introduced in Milestone 4.2.

**Last updated:** 2026-05-07

---

## 1. Prerequisites

Before running any tests, make sure your environment is in a known-good state.

### 1.1 Apply the new database migration

The migration adds seven columns to `communication_logs` and three indexes.

```powershell
# From velvet-elves-backend (assumes Supabase CLI is configured)
supabase db push
# or, if applying directly:
psql "$env:SUPABASE_DB_URL" -f supabase/migrations/20260507_milestone_4_2_ai_email.sql
```

Verify the columns exist:

```sql
SELECT column_name FROM information_schema.columns
 WHERE table_name = 'communication_logs'
   AND column_name IN (
     'ai_kind','ai_source_data','parent_log_id',
     'escalation_due_at','escalation_sent_at',
     'discarded_at','discarded_by'
   );
-- Expect: 7 rows returned.
```

### 1.2 Backend dependencies

```powershell
cd c:\Projects\velvet-elves-backend
.\venv\Scripts\pip install -r requirements.txt
```

### 1.3 Frontend dependencies

```powershell
cd c:\Projects\velvet-elves-frontend
npm install
```

### 1.4 Required environment variables

The engine works in stub mode without external credentials, but real send-side testing needs at least one connected provider:

| Variable | Purpose | Required for |
|---|---|---|
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Gmail OAuth | End-to-end send via Gmail |
| `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET` | Outlook OAuth | End-to-end send via Outlook |
| `EMAIL_WEBHOOK_SECRET` | Inbound webhook auth | Inbound webhook tests |
| `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` | Provider chat completion | Realistic draft refinement |
| `AI_PROVIDER` | `openai` or `anthropic` | Default provider selection |

The engine still produces drafts when AI keys are absent — it falls back to deterministic rule-based templates.

---

## 2. Automated tests

### 2.1 Run the new test module

```powershell
cd c:\Projects\velvet-elves-backend
.\venv\Scripts\python.exe -m pytest app/tests/test_ai_email_api.py -v
```

**Expected:** `10 passed`. Each test exercises a specific deliverable from the milestone:

| Test | Deliverable verified |
|---|---|
| `test_engine_drafts_factual_reply_with_high_confidence` | AI engine drafts factual replies with grounded source data, AI disclaimer appended |
| `test_engine_routes_uncertain_to_pending_review` | Uncertain inbound never auto-sends |
| `test_drafts_endpoint_lists_pending_drafts` | `/ai-emails/drafts` returns pending queue |
| `test_approve_and_send_uses_provider` | `POST /approve` sends via the user's connected provider and stamps approval metadata |
| `test_edit_and_send_replaces_body_and_clears_assumptions` | `POST /edit-and-send` replaces body, clears flagged assumptions |
| `test_discard_marks_soft_discarded_and_hides_from_list` | Soft-discard preserves audit trail and hides from the queue |
| `test_settings_round_trip` | Tenant `ai_email` settings persist via GET/PUT |
| `test_escalation_runner_marks_due_drafts` | Escalation runner stamps `escalation_sent_at` and emits a SYSTEM log |
| `test_notifications_pending_includes_ai_draft_count` | `/notifications/pending` exposes `ai_drafts_pending` |
| `test_tone_rules_redact_legal_advice` | Forbidden phrasing is redacted from the body, disclaimer is preserved |

### 2.2 Run the full backend suite

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

**Expected:** 415+ passing. Two pre-existing failures (`test_inbound_webhook_persists_log`, `test_outlook_provider_parse_webhook_fetches_changed_message`) are caused by `EMAIL_WEBHOOK_SECRET` env state leakage from `.env` and are unrelated to Milestone 4.2.

### 2.3 Frontend type check, lint, and build

```powershell
cd c:\Projects\velvet-elves-frontend
npx tsc --noEmit
npx eslint src/pages/AiEmailReviewPage.tsx src/hooks/useAiEmails.ts `
            src/components/shared/NotificationsPanel.tsx `
            src/layouts/AppLayout.tsx src/App.tsx `
            src/utils/constants.ts src/hooks/useNotifications.ts
npx vite build
```

All three must complete without errors.

---

## 3. Manual end-to-end testing

These walkthroughs use the dev environment (`https://dev.velvetelves.com` or `http://localhost:5173`) with the FastAPI backend on `http://localhost:8000`.

### 3.1 Engine ➜ pending draft (happy path: factual question)

1. Sign in as an Agent who owns at least one Active transaction (e.g. demo "123 Maple St", closing date set).
2. Connect Gmail (or iCloud) under **Settings → Integrations** so the user has an active provider.
3. Trigger an inbound email by hitting the webhook directly (or actually sending a real email if Gmail Pub/Sub is wired):

```powershell
$body = @{ message = @{ data = "stub" } } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/integrations/email/webhook/gmail?user_id=$userId" `
                  -Method POST -Body $body -ContentType 'application/json' `
                  -Headers @{ 'X-VE-Webhook-Secret' = $env:EMAIL_WEBHOOK_SECRET }
```

   For local testing without a provider, insert a fake inbound directly:

```sql
INSERT INTO communication_logs
  (id, tenant_id, channel, direction, transaction_id,
   sender_email, recipient_emails, subject, body, status, is_ai_generated)
VALUES
  (gen_random_uuid(), '<your-tenant-id>', 'email', 'inbound',
   '<your-tx-id>', 'client@example.com', ARRAY['agent@firm.com'],
   'Quick question', 'When is closing for the Maple St deal?',
   'received', false);
```

   Then call the engine directly:

```python
from app.services.ai_email_engine import AIEmailEngine
from app.services.email.base import InboundEmail
# build InboundEmail and call engine.handle_inbound(...)
```

4. **Verify** in the UI:
   - Topbar bell shows a new badge increment.
   - Sidebar **Intelligence → AI Email Review** has the badge updated.
   - Open `/ai-emails` — the draft is at the top of the list with kind `factual`, confidence ≥ 90%.
5. **Verify** in the database:

```sql
SELECT id, ai_kind, ai_confidence, approval_status, status,
       parent_log_id, escalation_due_at,
       jsonb_pretty(ai_source_data) AS source
  FROM communication_logs
 WHERE is_ai_generated = true
 ORDER BY created_at DESC LIMIT 1;
```

   `ai_source_data` should contain `closing_date` matching the transaction.

### 3.2 Side-by-side review and approve

1. Open the draft from the list.
2. Confirm:
   - **Left pane** shows the draft with assumptions highlighted in amber.
   - **Right pane** shows a "Source data the AI cited" panel with each value (closing_date, status, address) and below it the original inbound message.
   - The kind chip, confidence pill, and recipient line are all populated.
3. Click **Approve & Send**. Toast shows "Sent". The list moves to the next draft (or the empty state if none remain).
4. **Verify** in the database:

```sql
SELECT approval_status, status, approved_by, approved_at, provider_name, provider_ref_id
  FROM communication_logs WHERE id = '<draft-id>';
-- Expected: approval_status = 'approved', status = 'sent',
--           approved_by = current user, provider attribution populated.
```

5. **Verify audit log entry:**

```sql
SELECT action, summary FROM audit_logs
 WHERE entity_type = 'ai_email' AND entity_id = '<draft-id>'
 ORDER BY created_at DESC;
-- Expected: at least one 'approve_and_send' row.
```

### 3.3 Edit & send

1. Open a draft, click **Edit**.
2. Change the subject and body.
3. Click **Send Edit**. Toast confirms send.
4. Verify the edited body landed in the log and `ai_assumptions` is now empty (human-approved content has no flagged assumptions).

### 3.4 Regenerate

1. Open a draft of kind `uncertain` or any draft you want fresh.
2. Click **Regenerate**.
3. Verify:
   - Old draft row has `discarded_at` populated and `approval_status = 'regenerated'`.
   - A new draft was created against the same `parent_log_id`.
   - The list refreshes and the new draft is selectable.

### 3.5 Discard

1. Click **Discard** on a draft. Confirm in the browser dialog.
2. Verify the draft disappears from the list.
3. Verify in DB the row still exists with `discarded_at`, `discarded_by`, `approval_status = 'discarded'`.

### 3.6 AI safeguards (assumptions + forbidden phrases)

Seed an inbound that triggers an uncertain reply (e.g. legal-question wording):

```sql
INSERT INTO communication_logs (...) VALUES
  (..., 'I'd like your legal advice on the inspection report.', ...);
```

Verify:
- The persisted draft has `ai_assumptions` populated with the safeguard message about redacting legal-advice phrasing.
- The body contains `[redacted by safeguard — see agent]` in place of the forbidden phrase.
- The Velvet Elves disclaimer is appended at the end.
- `approval_status = 'pending_review'` (never auto-sends).

### 3.7 Escalation reminders

1. Insert a stale draft with `escalation_due_at` in the past:

```sql
UPDATE communication_logs
   SET escalation_due_at = now() - interval '2 hours'
 WHERE id = '<draft-id>';
```

2. As an Admin, call the runner:

```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/ai-emails/escalations/run' `
                  -Method POST `
                  -Headers @{ Authorization = "Bearer $token" }
```

3. Verify:
   - Response: `{ escalations_sent: 1, tenant_id: "<tenant>" }`.
   - The draft now has `escalation_sent_at` set.
   - A SYSTEM channel log was emitted (`channel = 'system'`, `parent_log_id = <draft-id>`, body mentions "pending your review").
   - In the UI, the draft card shows a red "Escalated" pill.
   - Re-running the endpoint within the same hour returns `escalations_sent: 0` (idempotent).

### 3.8 Tenant settings

1. As Admin or TeamLead, navigate to the AI email settings page (or call the API):

```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/ai-emails/settings' `
                  -Method PUT `
                  -ContentType 'application/json' `
                  -Body (@{
                      tone = 'friendly'
                      disclaimer = 'Custom note from our brokerage.'
                      escalation_hours = 24
                      auto_send_threshold = 0.95
                  } | ConvertTo-Json) `
                  -Headers @{ Authorization = "Bearer $token" }
```

2. Trigger a new inbound and confirm the new draft uses the friendly sign-off (`Cheers,`) and the custom disclaimer.
3. Confirm `auto_send_threshold = 0.95` causes more drafts to land in `pending_review` rather than auto-approve.

### 3.9 Notifications panel surfacing

1. Click the topbar bell.
2. Confirm:
   - The header callout reads `N AI drafts awaiting review` (only when N > 0). Clicking it routes to `/ai-emails`.
   - A second callout reads `N outbound emails sent on your behalf today` when applicable.
3. Confirm the bell badge counts pending AI drafts toward unread (alongside due-date task notifications).
4. Click "Mark all as read" — the bell badge goes to zero (drafts included) and a confirmation toast appears. The badge only re-lights when a genuinely new draft or task notification arrives; a still-pending draft you already acknowledged does not keep it lit.

### 3.10 Auto-send threshold (high confidence path)

This is a focused test of the auto-proceed rule.

1. Lower the threshold for testing:

```powershell
Invoke-RestMethod ... -Body (@{ tone='professional'; disclaimer=''; escalation_hours=24; auto_send_threshold=0.5 } | ConvertTo-Json)
```

2. Trigger an inbound that the engine resolves as `document_request` AND the requested document exists on the transaction.
3. The draft should land with `approval_status = 'auto_approved'` (not `pending_review`).
4. Confirm CC always includes the responsible internal owner — the agent's email should be in `cc_emails`.

> **Note:** Auto-approval still requires zero flagged assumptions. The intent is "the AI is confident AND grounded AND not making interpretations" before bypassing human review.

---

## 4. Cross-feature integration

### 4.1 Audit trail completeness

Every action (approve, edit-and-send, discard, regenerate, settings update, escalate) writes an `audit_logs` row with `entity_type = 'ai_email'` (or `tenant`/`update_ai_email_settings`).

```sql
SELECT user_id, action, entity_type, entity_id, summary, created_at
  FROM audit_logs
 WHERE entity_type IN ('ai_email','tenant')
   AND tenant_id = '<your-tenant>'
 ORDER BY created_at DESC LIMIT 50;
```

### 4.2 Communication log immutability

Even though we update specific AI workflow fields (approval, escalation), the body and assumptions on a sent draft must remain intact post-send. Verify by retrieving the row before and after approve.

### 4.3 RBAC

| Endpoint | Allowed roles |
|---|---|
| `GET /ai-emails/drafts` | Any authenticated user (tenant-scoped) |
| `GET /ai-emails/{id}` | Any authenticated user with tenant access |
| `POST /ai-emails/{id}/approve` etc. | Any authenticated user with tenant access |
| `POST /ai-emails/escalations/run` | **Admin** only |
| `PUT /ai-emails/settings` | **Admin** or **TeamLead** |

Smoke-test by attempting each endpoint with an Agent token and confirming 403 on the privileged routes.

### 4.4 Tenant isolation

Create two tenants. Seed drafts in tenant A. Sign in as a user from tenant B and verify:
- `GET /ai-emails/drafts` returns 0.
- `GET /ai-emails/{tenant-a-draft-id}` returns 403/404.

---

## 5. Edge cases

| Scenario | Expected behavior |
|---|---|
| Inbound has no transaction context | Engine still drafts, but assumes "no transaction context found" (logged in `ai_assumptions`). Confidence drops to ~0.5. |
| Document requested but not on file | Draft says "the agent will follow up", `pending_review`, NOT auto-sent. |
| Vendor reply with malformed date | Draft asks the vendor to re-send in `YYYY-MM-DD` format. |
| User has no connected email provider | `Approve & Send` returns 409 with a clear error toast. The draft remains pending. |
| Draft already discarded | Approve / edit / regenerate return 400 "Draft has been discarded." |
| Draft already approved | Same 400 — no double-send. |
| Tenant settings missing the `ai_email` key | Engine falls back to defaults (professional tone, default disclaimer, 36h escalation, 0.90 threshold). |
| AI provider unreachable | Rule-based draft still persists; assumptions list flags the absence. |

---

## 6. Performance / load

Lightweight smoke test:

```powershell
# Seed 100 inbound emails and confirm engine processes within ~5s each
for ($i = 0; $i -lt 100; $i++) {
    # send webhook or insert directly
}
# Verify no draft is missing and no log row has corrupt JSON in ai_source_data
SELECT count(*) FROM communication_logs WHERE is_ai_generated;
```

Indexes added by the migration ensure the pending-drafts and escalation-due queries stay efficient at scale:
- `idx_comm_logs_pending_review` (partial index on `approval_status = 'pending_review'`)
- `idx_comm_logs_escalation_due` (partial index for the cron query)
- `idx_comm_logs_parent_log` (parent inbound lookup)

---

## 7. Production readiness checklist

Before promoting Milestone 4.2 to production:

- [ ] Migration applied and verified in production.
- [ ] `EMAIL_WEBHOOK_SECRET` rotated and stored in secrets manager.
- [ ] At least one tenant has `ai_email` settings reviewed and approved.
- [ ] Cron job (or scheduled worker) calls `POST /ai-emails/escalations/run` every 1–2 hours.
- [ ] Frontend production build deployed; sidebar **Intelligence → AI Email Review** link visible to authorized roles.
- [ ] Audit log retention covers `ai_email` entity type.
- [ ] Smoke test on production: trigger a real inbound, verify draft appears, approve, confirm send, confirm communication log entry.
- [ ] AI provider credentials valid and rate limits monitored.

---

## 8. Rollback plan

If a regression is found post-deploy:

1. Disable the inbound hook by commenting out the `register_inbound_hook(ai_email_inbound_hook)` line in `app/main.py` and redeploying. New inbounds are still logged; AI drafting stops.
2. UI side: hide the sidebar entry by gating it behind a feature flag.
3. Pending drafts in the queue can be discarded in bulk:

```sql
UPDATE communication_logs
   SET discarded_at = now(), approval_status = 'discarded',
       discarded_by = '<admin-user-id>'
 WHERE is_ai_generated AND approval_status = 'pending_review';
```

The migration itself is additive (new columns + indexes) and does not need to be rolled back to disable the feature.

---

## Appendix A — Reference: the new `communication_logs` columns

| Column | Type | Purpose |
|---|---|---|
| `ai_kind` | TEXT | Classification: `factual` / `document_request` / `vendor_reply` / `uncertain` / `other` / `escalation` |
| `ai_source_data` | JSONB | Source values the AI cited (closing_date, document name, etc.) |
| `parent_log_id` | UUID | Link a draft to the inbound it replies to |
| `escalation_due_at` | TIMESTAMPTZ | When an unactioned draft should escalate |
| `escalation_sent_at` | TIMESTAMPTZ | Set when escalation reminder fires (idempotency guard) |
| `discarded_at` | TIMESTAMPTZ | Soft-discard timestamp |
| `discarded_by` | UUID | User who discarded the draft |

## Appendix B — Reference: tenant `ai_email` settings

Stored at `tenants.settings_json -> 'ai_email'`:

```json
{
  "tone": "professional",
  "disclaimer": "This message was prepared by Velvet Elves AI...",
  "escalation_hours": 36,
  "auto_send_threshold": 0.90
}
```

Defaults are applied when the key is missing.
