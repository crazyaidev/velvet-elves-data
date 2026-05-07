# Milestone 4.2 — UI Testing Guide

Two complementary walkthroughs for verifying Milestone 4.2 (AI Email Automation):

- **Part A — Swagger UI** (backend API verification at `/api/docs`)
- **Part B — Frontend UI** (browser verification at `http://localhost:5173` or `https://dev.velvetelves.com`)

Both parts assume the backend migration `20260507_milestone_4_2_ai_email.sql` has been applied. See `MILESTONE_4_2_TESTING_GUIDE.md` §1 for prerequisites.

---

# Part A — Swagger UI Testing

## A.1 Start the backend and open Swagger

```powershell
cd c:\Projects\velvet-elves-backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/api/docs** in a browser. The new endpoint group is **`ai-emails`** (next to `communication-logs` and `notifications`).

## A.2 Authenticate

Every endpoint is bearer-token protected. You need three tokens for a complete test:

| Token slot | Role | How to obtain |
|---|---|---|
| `agentToken` | `Agent` | `POST /api/v1/users/register` (or `/login`) |
| `adminToken` | `Admin` | Same, with `role: "Admin"` |
| `teamLeadToken` | `TeamLead` | Same, with `role: "TeamLead"` |

### Steps to authenticate in Swagger

1. Expand **`POST /api/v1/users/register`**.
2. Click **Try it out**, paste:

   ```json
   {
     "email": "agent.qa@example.com",
     "password": "QaPass1!",
     "role": "Agent",
     "tenant_id": "qa-tenant"
   }
   ```

3. Click **Execute**. Copy the `access_token` from the response.
4. Scroll to the top of the page, click the **Authorize** button (lock icon).
5. Paste the token (without the `Bearer ` prefix — Swagger adds it). Click **Authorize**, then **Close**.
6. Repeat steps 1–5 for the Admin and TeamLead users (use different emails, same `tenant_id`).

> Save each token in a scratch note. Re-authorizing in Swagger replaces the active token, so you'll switch between them as you test role-gated endpoints.

## A.3 Seed a transaction (one-time)

The engine grounds drafts in a transaction's data. Quick way:

1. Expand **`POST /api/v1/transactions`** ➜ **Try it out**.
2. Use this minimal payload:

   ```json
   {
     "use_case": "Buy-Fin",
     "address": "123 Maple St",
     "city": "Indianapolis",
     "state": "IN",
     "zip_code": "46204",
     "purchase_price": 425000,
     "closing_date": "2026-06-15",
     "representation_type": "Buyer"
   }
   ```

3. Execute. Copy the returned transaction `id` — call it **`<txId>`**.

## A.4 Seed an inbound email + AI draft

The fastest way to produce a draft for review is via the email webhook. We stub the provider so no real Gmail/Outlook account is needed.

### Option 1 — via the inbound webhook (recommended)

1. Expand **`POST /api/v1/integrations/connect`** ➜ Try it out:

   ```json
   { "provider": "gmail", "provider_email": "agent.qa@example.com" }
   ```

   Execute. This creates a stub Gmail integration so the webhook factory finds an active provider.

2. Expand **`POST /api/v1/integrations/email/webhook/{provider}`**:
   - `provider` = `gmail`
   - `user_id` query param = your Agent user's id (from the register response)
   - Add header **`X-VE-Webhook-Secret`** if `EMAIL_WEBHOOK_SECRET` is set in your environment

   Body:

   ```json
   { "message": { "data": "stub" } }
   ```

3. Execute. Expected: `200`, `{ "accepted": true, "persisted": 1 }` (or `0` on the second call — dedupe).

> The stub Gmail provider returns a hard-coded inbound. For richer scenarios, use Option 2 below.

### Option 2 — direct DB seed (richest scenarios)

Run this SQL against your database to seed an inbound message of any shape:

```sql
INSERT INTO communication_logs
  (id, tenant_id, channel, direction, transaction_id,
   sender_email, recipient_emails, subject, body, status, is_ai_generated)
VALUES
  (gen_random_uuid(),
   '<your-tenant-uuid>',
   'email', 'inbound',
   '<txId>',
   'client@example.com',
   ARRAY['agent.qa@example.com'],
   'Quick question',
   'When is closing for the Maple St deal?',
   'received', false);
```

Then call the engine via the regenerate endpoint of an existing draft, or run `AIEmailEngine.handle_inbound` from a Python REPL.

## A.5 Walk through every `ai-emails` endpoint

### A.5.1 `GET /api/v1/ai-emails/drafts` — list pending

- **Auth:** Agent token
- **Try it out** ➜ optionally set `transaction_id = <txId>` to scope ➜ Execute.
- **Expected:** `200` with `{ items: [...], total: N }`. Each item has `is_ai_generated: true`, `approval_status: "pending_review"`, an `ai_kind` (e.g. `factual`), an `ai_confidence`, and an `ai_source_data` object.
- Copy one draft `id` — call it **`<draftId>`**.

### A.5.2 `GET /api/v1/ai-emails/{log_id}` — single draft

- Path `log_id = <draftId>` ➜ Execute.
- **Expected:** Same row, including `parent_log_id`, `ai_assumptions`, `escalation_due_at`.
- **Negative:** swap to a random UUID ➜ `404 AI draft not found`.

### A.5.3 `GET /api/v1/ai-emails/{log_id}/parent` — original inbound

- Execute with `<draftId>`.
- **Expected:** `200` returning the inbound row whose `id == draft.parent_log_id`. Direction is `"inbound"`, `is_ai_generated` is `false`.
- **Negative:** if the draft has no parent, returns `404 Draft has no inbound parent`.

### A.5.4 `GET /api/v1/ai-emails/settings` — read tenant config

- **Expected:** Defaults if the tenant has no `ai_email` block yet:

  ```json
  {
    "tone": "professional",
    "disclaimer": "This message was prepared by Velvet Elves AI...",
    "escalation_hours": 36,
    "auto_send_threshold": 0.9
  }
  ```

### A.5.5 `PUT /api/v1/ai-emails/settings` — update tenant config

- **Auth:** switch to **Admin** or **TeamLead** token (re-Authorize at the top).
- Body:

  ```json
  {
    "tone": "friendly",
    "disclaimer": "Custom note from QA tenant.",
    "escalation_hours": 24,
    "auto_send_threshold": 0.85
  }
  ```

- **Expected:** `200`, returns the saved config.
- Re-call `GET /settings` ➜ confirm persistence.
- **Negative — RBAC:** switch back to Agent token, retry PUT ➜ `403 Forbidden`.

### A.5.6 `POST /api/v1/ai-emails/{log_id}/edit-and-send` — replace body and send

- **Auth:** Agent token. The Agent must have a connected provider for the actual send to succeed (e.g. iCloud connect first).
- Path `log_id = <draftId>`, body:

  ```json
  {
    "subject": "Re: Status — confirmed by QA",
    "body_text": "Hi — closing is on track for June 15. Let me know if you need anything else.",
    "cc": ["copilot@example.com"]
  }
  ```

- **Expected:** `200`. Response shows `approval_status: "approved"`, `status: "sent"`, `body` matches the new text, `ai_assumptions: []`.
- **Negative:** call again on the same `<draftId>` ➜ `400 Draft is in state 'approved' and cannot be modified.`

### A.5.7 `POST /api/v1/ai-emails/{log_id}/approve` — approve as-is

Generate a fresh draft (re-seed via §A.4) and use a different `<draftId>`.

- **Expected (provider connected):** `200` with `approval_status: "approved"`, `provider_name`, `provider_ref_id`.
- **Negative (no provider):** disconnect via `DELETE /integrations/{provider}` first ➜ retry approve ➜ `409 No active <provider> integration for this user.`

### A.5.8 `POST /api/v1/ai-emails/{log_id}/regenerate` — re-run engine

- Re-seed and use `<draftId>`.
- **Expected:** `200` with `{ new_log_id: "<id>", confidence: <float>, discarded_log_id: "<old>" }`.
- Verify via `GET /drafts` ➜ old draft is gone, new draft is present.
- Verify the old row in DB has `discarded_at` set, `approval_status = 'regenerated'`.

### A.5.9 `POST /api/v1/ai-emails/{log_id}/discard` — soft-discard

- Re-seed and use `<draftId>`.
- Body:

  ```json
  { "reason": "QA test discard" }
  ```

- **Expected:** `200` with `discarded_at` populated and `approval_status: "discarded"`. The draft no longer appears in `GET /drafts`.

### A.5.10 `POST /api/v1/ai-emails/escalations/run` — admin escalation runner

- **Auth:** **Admin** token.
- Make a draft "stale" first by editing its `escalation_due_at` to the past. With Supabase running, easiest is direct SQL:

  ```sql
  UPDATE communication_logs
     SET escalation_due_at = now() - interval '2 hours'
   WHERE id = '<draftId>';
  ```

- Execute the endpoint ➜ **Expected:** `{ "escalations_sent": 1, "tenant_id": "<your-tenant>" }`.
- Re-execute immediately ➜ `escalations_sent: 0` (idempotent because `escalation_sent_at` is now set).
- **Negative — RBAC:** call with Agent token ➜ `403 Forbidden`.
- **Verify side effect:** `GET /communication-logs?direction=internal&channel=system` shows the new SYSTEM-channel notification row, with `parent_log_id == <draftId>`.

### A.5.11 Notifications integration

- **Auth:** Agent token.
- Expand **`GET /api/v1/notifications/pending`** ➜ Execute.
- **Expected:** Response includes the new fields:

  ```json
  {
    "ai_drafts_pending": <int>,
    "external_communications_today": <int>,
    "compiled_summary": "...",
    "overdue": [], "due_today": [], "day_before": [], "upcoming": [],
    "transaction_summaries": []
  }
  ```

- The `ai_drafts_pending` value should match `total` from `GET /ai-emails/drafts`.

## A.6 Negative-path quick reference

| Action | Expected status |
|---|---|
| Any endpoint without auth | 401 |
| Agent calls `PUT /settings` | 403 |
| Agent calls `POST /escalations/run` | 403 |
| Approve / edit / regenerate on already-approved draft | 400 |
| Approve / edit / regenerate on discarded draft | 400 |
| `GET /{logId}` with random UUID | 404 |
| Approve while user has no email integration | 409 |
| Tenant access mismatch (cross-tenant draft) | 403 |

## A.7 Success criteria for Part A

- [ ] All 10 `ai-emails` endpoints return the expected shape and status.
- [ ] Settings PUT/GET round-trip persists across requests.
- [ ] Approve and Edit-and-Send actually deliver via the connected provider (or fail gracefully if not connected).
- [ ] Discard / regenerate / escalation each leave the right audit trail (verifiable via `GET /audit-logs`).
- [ ] `notifications/pending.ai_drafts_pending` matches `ai-emails/drafts.total`.

---

# Part B — Frontend UI Testing

## B.1 Start the stack

```powershell
# Terminal 1 — backend
cd c:\Projects\velvet-elves-backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd c:\Projects\velvet-elves-frontend
npm run dev
```

Open **http://localhost:5173**. Log in as the same Agent user you registered in Part A (`agent.qa@example.com` / `QaPass1!`).

> If you prefer the deployed dev environment, use https://dev.velvetelves.com — the same workflow applies. Skip Step B.1.

## B.2 Pre-flight setup

Before testing the AI email screens, you need:

1. **A connected email provider** for the logged-in user.
   - Open **Settings → Integrations**.
   - Click **Connect** under Gmail (or use **iCloud** with an app-specific password if your env has no Google credentials).
   - Stub-mode connect is fine — the UI just needs an active integration row to allow Approve & Send to make a request.

2. **At least one Active transaction owned by this user.**
   - Click **+ New Transaction** in the topbar.
   - Use the AI Quick-Create modal or fill manually. Set a closing date in the next 60 days so the engine has a date to cite.

3. **One or more AI drafts in the queue.**
   - Easiest: use Swagger Step §A.4 (Option 1 webhook OR Option 2 SQL) to seed an inbound, then refresh the browser.
   - Or, in dev with a real Gmail account, send yourself an email like "When is closing on 123 Maple?" and wait for the webhook to fire.

## B.3 Topbar bell (notifications panel)

### What to verify

1. **Badge count.** The bell shows a red badge with the unread count. AI drafts always count toward unread until the panel is opened.
2. **Click the bell.** A dropdown panel opens.
3. At the top of the panel, look for two callouts (only visible when applicable):
   - 🟠 **"N AI drafts awaiting review"** — clickable.
   - 📧 **"N outbound emails sent on your behalf today"** — informational.
4. **Click the AI drafts callout** ➜ panel closes, you navigate to `/ai-emails`.
5. **Mark all seen.** Click **Mark all seen** at the bottom. The bell badge clears (or shrinks to just the AI draft count if any remain).

### Edge cases

- **Zero drafts, zero comms today:** the callouts are hidden entirely. Only the task list renders.
- **Many drafts:** the callout is a single row with the total — drafts are not enumerated in the panel itself.

## B.4 Sidebar nav entry

1. In the dark sidebar, expand the **Intelligence** section.
2. You should see three items:
   - ✦ **AI Suggestions**
   - ✉ **AI Email Review** ← new in 4.2
   - 📊 **Analytics**
3. **Badge:** the AI Email Review row shows the pending-draft count in an orange chip.
4. **Click it** ➜ navigates to `/ai-emails` and the row gets the active-state amber accent.

> Attorney and ForSaleByOwner roles use different sidebars — they will not see this entry. Verify by signing in as an Attorney/FSBO user; the Intelligence section is replaced/simplified for those roles.

## B.5 AI Email Review page (`/ai-emails`)

### Page structure

```
┌─────────────────────────────────────────────────────────────────┐
│ ✦ AI Email Review     [N pending]                       [↻]   │  Header
├──────────┬──────────────────────────┬──────────────────────────┤
│ Drafts   │  Draft body (left pane) │  Source data (right pane)│
│ list     │                          │                          │
│          │  Highlighted assumptions│  Each cited value         │
│ • A      │  Recipient + CC         │                          │
│ • B      │  Confidence pill         │  ─────                    │
│          │                          │  Original inbound        │
│          │ [Approve] [Edit] [Regen][Discard]                   │
└──────────┴──────────────────────────┴──────────────────────────┘
```

### B.5.1 Draft list (left column)

Verify each row shows:

- **Status dot** — orange (default), amber (uncertain), red (escalated).
- **Subject** (bold, single line, truncates with ellipsis).
- **Recipient line** — `To client@example.com`.
- **Kind chip** — colored pill (`Factual question` blue, `Document request` amber, `Vendor reply` green, `Uncertain` red).
- **Confidence chip** — monospace `90%`.
- **"Escalated" pill** when `escalation_sent_at` is set.

Click a draft ➜ it becomes the active row (warm orange highlight) and the right pane updates.

### B.5.2 Draft body pane (center)

For the active draft:

- Header shows:
  - `✦ AI Draft` chip
  - Kind chip (colored)
  - Confidence chip
  - Subject (serif, bold)
  - To / CC line in monospace
- The body text is rendered with **assumption phrases highlighted in amber**. Hover or read — these are exact substrings from the `ai_assumptions` array.
- Below the body, a yellow **"Flagged assumptions"** panel lists each assumption explicitly. This always appears when the array is non-empty.

### B.5.3 Source data pane (right)

- Each cited value (closing_date, status, address, matched_document, scheduled_date, etc.) gets its own card with:
  - Label in monospace, uppercase, letter-spaced.
  - Value in monospace, tabular-nums for dates/numbers.
- If `ai_source_data` is empty, you see an italic note: "No source data was cited for this draft. Treat the body as a generic response and verify the facts manually before approving."
- Below source data, an **"Original inbound"** section renders the parent email (sender, subject, body) so you can compare draft to source side-by-side.

### B.5.4 Action buttons (footer)

#### **Approve & Send**
1. Click ➜ button shows loading state, then a green toast: **Sent — AI reply approved and delivered.**
2. The list refetches. The selected draft disappears.
3. Selection auto-advances to the next draft, or shows the empty state.

#### **Edit**
1. Click ➜ the body view replaces with two inputs (Subject, Body textarea) plus **Send Edit** / **Cancel**.
2. Modify both. Click **Send Edit**.
3. Toast: **Sent — Edited reply delivered.** List refetches.

#### **Regenerate**
1. Click ➜ button shows loading.
2. Toast: **Regenerated — A fresh draft is ready for review.**
3. The old draft disappears; a new one (often higher confidence on a re-roll) takes its place.

#### **Discard**
1. Click ➜ browser `confirm()` dialog. Click OK.
2. Toast: **Discarded — Draft removed.**
3. Draft disappears from the list.

### B.5.5 Empty state

When no drafts remain:

- Right pane shows a centered message: **"Pick a draft to review"** ➜ once the list is empty, the left list shows: **"No drafts to review"** with a subtitle "When AI prepares a reply that needs your sign-off, it shows up here."
- The header pill shows `0 pending`.

### B.5.6 Refresh

- The header **↻** refresh button manually refetches. It animates while loading.
- The list also auto-refetches every 60 seconds.

## B.6 Cross-page integrations to verify

### B.6.1 Notifications panel ↔ AI Email Review

1. Trigger 3 inbounds via Swagger §A.4.
2. **Bell badge** should show 3 (or 3 + task count, depending on tasks due).
3. **Click bell** ➜ callout reads "3 AI drafts awaiting review".
4. **Click callout** ➜ lands on `/ai-emails` with all 3 in the list.

### B.6.2 Sidebar badge updates after action

1. Note the badge count on **AI Email Review** in the sidebar (say it reads `3`).
2. Approve one draft.
3. Within ~60 s (or on next bell open) the badge drops to `2`.

### B.6.3 Audit trail visibility

1. Sign in as Admin.
2. Visit **Admin → Audit Logs** (if exposed in your build) or query directly via Swagger `GET /api/v1/audit-logs`.
3. Filter for `entity_type=ai_email`. Each Approve / Edit / Discard / Regenerate / Escalate action should be present with the user, action verb, and summary.

## B.7 Visual / UX checklist

- [ ] All copy uses sentence case (no ALL CAPS labels).
- [ ] Buttons match the rest of the app: primary orange (Approve / Send Edit), neutral white (Edit / Cancel / Regenerate), red-tinted destructive (Discard).
- [ ] Confidence pill uses monospace + tabular nums so percentages align.
- [ ] Mobile (< 1024px width): the right pane stacks under the body pane; the page remains usable. Verify by resizing the browser.
- [ ] Keyboard navigation works: Tab moves between the list, the body, and the action buttons.
- [ ] Loading skeletons appear before drafts load — no flash of empty state.
- [ ] Toast errors are red-tinted with a clear "Try again" affordance when applicable.

## B.8 Negative paths in the UI

| Scenario | Expected UI behavior |
|---|---|
| Approve when no email provider is connected | Red toast: **Send failed — No active gmail integration for this user.** Draft stays pending. |
| Network error during Approve | Red toast with the underlying error message. Draft stays pending. The retry path is to click Approve again. |
| Two browsers approve the same draft | Second one shows: **Send failed — Draft is in state 'approved' and cannot be modified.** |
| Discard then refresh | The draft is gone from the list. SQL still shows the row with `discarded_at`. |
| Tenant settings haven't been configured | Drafts still arrive with the default professional disclaimer. |

## B.9 Success criteria for Part B

- [ ] Bell badge accurately reflects AI drafts pending plus unread tasks.
- [ ] Notifications panel callouts appear/disappear correctly with state.
- [ ] Sidebar **Intelligence → AI Email Review** is visible to Agent / TeamLead / Admin and shows the badge count.
- [ ] All four actions (Approve, Edit & Send, Regenerate, Discard) succeed end-to-end with toast feedback.
- [ ] Side-by-side review correctly highlights assumptions and lists source data.
- [ ] List auto-refreshes after each action; selection auto-advances.
- [ ] Empty / loading / error states render the right copy and don't block subsequent actions.
- [ ] Visual regression: no layout shifts, mobile viewport remains usable.

---

## Part C — Combined smoke test (15 minutes)

Use this as a final pre-deploy gate.

| # | Step | Where | Expected |
|---|---|---|---|
| 1 | Apply migration | DB | 7 columns + 3 indexes added |
| 2 | Start backend + frontend | Terminals | Both running clean |
| 3 | Register Agent + connect provider | Frontend | Settings shows active integration |
| 4 | Create a transaction | Frontend or Swagger | Transaction visible in workspace |
| 5 | Seed inbound (webhook or SQL) | Swagger | `200 persisted: 1` |
| 6 | Open `/ai-emails` | Frontend | Draft visible with kind/confidence |
| 7 | Click draft | Frontend | Side-by-side renders, assumptions highlighted |
| 8 | Approve & Send | Frontend | Toast "Sent", draft leaves list |
| 9 | Bell badge | Frontend | Decremented |
| 10 | Audit log | Swagger `GET /audit-logs` | `ai_email approve_and_send` entry exists |
| 11 | Update settings to friendly + threshold 0.95 | Swagger PUT /settings | Returns saved config |
| 12 | Trigger another inbound | Swagger | New draft uses friendly sign-off |
| 13 | Make it stale + run escalation | Swagger | `escalations_sent: 1` |
| 14 | Refresh `/ai-emails` | Frontend | Draft shows red "Escalated" pill |
| 15 | Discard the stale draft | Frontend | Toast "Discarded", list refreshes |

If all 15 pass, Milestone 4.2 is verified for the AI Email Automation workflow.
