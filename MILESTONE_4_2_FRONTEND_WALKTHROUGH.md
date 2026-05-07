# AI Email Automation — Frontend UI Step-by-Step Walkthrough

**Audience:** QA testers, developers, and product reviewers verifying Milestone 4.2 end-to-end through the browser.
**Time required:** ~45 minutes for the full pass.
**Last updated:** 2026-05-07

This guide walks you through every AI email automation behavior using a single concrete scenario: **Agent Sarah Chen managing the buyer-side closing for 742 Oak Ridge Drive**. Every input value, address, name, and date below is real test data you can copy verbatim.

> **Prerequisite:** Backend running on `http://localhost:8000`, frontend running on `http://localhost:5173`, migration `20260507_milestone_4_2_ai_email.sql` applied. See `MILESTONE_4_2_TESTING_GUIDE.md` §1 if you need help getting there.

---

## Test scenario at a glance

| Detail | Value |
|---|---|
| Agent | Sarah Chen — `sarah.chen@oakridge-realty.test` / `OakRidge1!` |
| Tenant | `oakridge-realty` |
| Transaction | 742 Oak Ridge Drive, Indianapolis, IN 46220 |
| Purchase price | $385,000 |
| Closing date | June 15, 2026 (Monday) |
| Buyer | Marcus Reed — `marcus.reed@example.com` |
| Vendor | Apex Home Inspections — `scheduling@apexinspect.test` |

We will trigger 6 different inbound emails against this transaction and watch each one flow through the system.

---

## Step 1 — Sign in as Sarah

**What you do:**

1. Open `http://localhost:5173` in a fresh browser window.
2. If Sarah doesn't exist yet, click **"Don't have an account? Register"** and fill in:
   - Email: `sarah.chen@oakridge-realty.test`
   - Password: `OakRidge1!`
   - Role: **Agent**
   - Tenant: `oakridge-realty`
3. Otherwise click **Sign In** and use the credentials above.

**What you should see:**

- Redirect to `/dashboard` after login.
- Topbar shows brand lockup and an empty bell icon (no unread badge yet).
- Left sidebar shows the dark navy panel with KPI tiles all reading `0`.
- Sidebar **Intelligence** section contains three rows: ✦ AI Suggestions, ✉ AI Email Review, 📊 Analytics. The "AI Email Review" row has **no badge** (no pending drafts).

**Verify:**

- [ ] You are logged in as Sarah (avatar in topbar shows her initials "SC").
- [ ] The "AI Email Review" sidebar row exists and is clickable but has no badge yet.

---

## Step 2 — Connect an email provider

The Approve & Send action requires Sarah's account to have at least one connected email provider.

**What you do:**

1. Click your **avatar in the bottom-left of the sidebar** ➜ **Settings**.
2. Scroll to **Integrations** (or click the Integrations tab if your build separates them).
3. Click **Connect** under iCloud (simplest for testing — no OAuth round-trip needed).
4. In the dialog, enter:
   - Email: `sarah.chen@icloud.test`
   - App-specific password: `abcd-efgh-ijkl-mnop` (any 16-character string for stub mode)
5. Click **Connect**.

**What you should see:**

- The iCloud row flips to **Connected** with a green checkmark.
- A toast appears: **"iCloud connected."**

**Verify:**

- [ ] An iCloud integration is visible and active for Sarah.
- [ ] If you prefer Gmail/Outlook and have OAuth credentials in your env, that path also works — the rest of the walkthrough is provider-agnostic.

---

## Step 3 — Create the test transaction

**What you do:**

1. Click **+ New Transaction** in the topbar.
2. In the quick-create modal, enter:
   - Client Name: `Marcus Reed`
   - Property Address: `742 Oak Ridge Drive`
   - City / ZIP: `Indianapolis 46220`
   - Transaction Type: **Buyer**
   - Purchase Price: `385000`
   - Contract Date: today's date
   - Projected Closing Date: `2026-06-15`
   - Lender / Title Company: `First National Title`
   - Notes: `Test transaction for AI email walkthrough`
3. Click **Create with AI Checklist**.

**What you should see:**

- Modal closes; toast: **"Transaction created — Oak Ridge Drive."**
- Sidebar KPI tiles update: **Active deals** now reads `1`.
- The new transaction card appears in the Active Transactions workspace.

**Verify:**

- [ ] The transaction card shows "742 Oak Ridge Drive" with closing date "Jun 15".
- [ ] Pipeline value tile shows `$385K` (or `$385,000`).
- [ ] Open the transaction expanded view briefly to confirm the Buyer "Marcus Reed" is on it as a party.

> Copy the transaction's id from the URL or expanded view (e.g. `tx-9c3a…`) — you'll seed inbound emails against it. Call this **`<txId>`**.

---

## Step 4 — Add Marcus as a transaction party

The engine matches inbound emails to transactions by checking party email addresses. Marcus needs to be on the file with his email.

**What you do:**

1. From the transaction card, click **Add Contact**.
2. Fill in:
   - Type: **Buyer**
   - First Name: `Marcus`
   - Last Name: `Reed`
   - Email: `marcus.reed@example.com`
   - Phone: `(317) 555-0142`
3. Save.

**Verify:**

- [ ] The expanded card now lists Marcus under **Contacts** with his email.
- [ ] No errors in the browser console.

---

## Step 5 — Test 1: Factual question (high confidence, auto-approved)

This is the happy path: the AI should produce an auto-approved draft because the file has a known closing date.

### 5a. Seed the inbound email

Open a second tab and load Swagger at `http://localhost:8000/api/docs`. (Or skip to the SQL alternative below.)

1. Click **Authorize** at the top.
2. In another window, run this in the browser console while logged in to grab Sarah's token:

```js
copy(localStorage.getItem('velvet_elves_token'))
```

3. Paste it into the Swagger Authorize dialog. Close.
4. Expand **`POST /api/v1/integrations/email/webhook/gmail`** ➜ Try it out.
5. Set query parameters:
   - `provider`: `gmail`
   - `user_id`: Sarah's user id (visible in Settings or pull from `/api/v1/users/me`)
6. If your env has `EMAIL_WEBHOOK_SECRET` set, add header `X-VE-Webhook-Secret`.
7. Body:

```json
{ "message": { "data": "stub" } }
```

8. Execute.

> **Or, the SQL alternative** (faster, fully under your control):
>
> ```sql
> INSERT INTO communication_logs
>   (id, tenant_id, channel, direction, transaction_id,
>    sender_email, recipient_emails, subject, body, status, is_ai_generated,
>    ai_assumptions, ai_source_data)
> VALUES
>   (gen_random_uuid(), '<oakridge-tenant-id>', 'email', 'inbound',
>    '<txId>', 'marcus.reed@example.com',
>    ARRAY['sarah.chen@oakridge-realty.test'],
>    'Quick question about closing',
>    'Hi Sarah — when exactly is closing? Just want to make sure I have it on my calendar. Thanks, Marcus',
>    'received', false, '{}'::text[], '{}'::jsonb);
> ```
>
> Then call the engine via `POST /api/v1/ai-emails/{some-existing-draft}/regenerate` against any draft to force a fresh engine pass — or simply restart the backend so the inbound hook fires on next webhook.

### 5b. Watch the badges light up

Switch back to the frontend tab.

**Within ~60 seconds you should see:**

- The topbar bell badge shows a red **`1`**.
- The sidebar **Intelligence → AI Email Review** row gets an orange **`1`** badge.

**Verify:**

- [ ] Bell badge increments without a page refresh (it polls every 60s — refresh manually if you don't want to wait).
- [ ] Sidebar badge matches the bell.

### 5c. Open the notifications panel

**What you do:**

1. Click the bell icon.

**What you should see:**

- A dropdown panel opens, anchored to the bell.
- At the top, a **champagne-colored callout** reads: **"1 AI draft awaiting review — Approve, edit, or discard before they go out."**
- Below it (if any outbound has been sent today): a smaller row says **"N outbound emails sent on your behalf today."**
- Below those, the regular task notification list (likely empty for this test transaction).

**Verify:**

- [ ] The AI draft callout is clearly visible at the top of the panel.
- [ ] Hovering the callout shows it's clickable (right-arrow appears).

### 5d. Open the AI Email Review page

**What you do:**

1. Click the **"1 AI draft awaiting review"** callout.

**What you should see:**

- Panel closes; route changes to `/ai-emails`.
- Page header reads: **"✦ AI Email Review · 1 pending"** with a refresh button on the right.
- Three-pane layout:

```
┌──────────┬─────────────────────────┬───────────────────────┐
│  Drafts  │  Draft body             │  Source data          │
│  list    │                         │                       │
│ • Re:    │  ✦ AI Draft  Factual    │  CLOSING DATE         │
│   Quick  │  Confidence 92%         │   2026-06-15          │
│   ques…  │                         │  STATUS               │
│          │  Re: Quick question…    │   Active              │
│          │  To marcus.reed@…       │  ADDRESS              │
│          │  CC sarah.chen@…        │   742 Oak Ridge Drive │
│          │                         │                       │
│          │  Hi Marcus,             │  ─── Original inbound │
│          │  Quick update on 742    │  From: marcus.reed@…  │
│          │  Oak Ridge Drive: we    │  Subject: Quick…      │
│          │  are tracking to a      │  Body: Hi Sarah—when… │
│          │  Monday, June 15, 2026  │                       │
│          │  closing.               │                       │
│          │                         │                       │
│          │  Best regards,          │                       │
│          │  Velvet Elves           │                       │
│          │                         │                       │
│          │  — This message was     │                       │
│          │  prepared by Velvet     │                       │
│          │  Elves AI…              │                       │
│          │                         │                       │
│          │  [Approve & Send]       │                       │
│          │  [Edit]                 │                       │
│          │  [Regenerate] [Discard] │                       │
└──────────┴─────────────────────────┴───────────────────────┘
```

**Verify:**

- [ ] The kind chip reads **"Factual question"** in blue.
- [ ] The confidence pill shows **92%** (or close — between 70% and 100%).
- [ ] The body mentions **"742 Oak Ridge Drive"** and **"Monday, June 15, 2026"** explicitly — these came from the transaction record, not the inbound.
- [ ] The CC line shows Sarah's own email (the engine adds the file owner to CC automatically).
- [ ] The right pane lists `closing_date: 2026-06-15`, `status: Active`, `address: 742 Oak Ridge Drive`.
- [ ] The original inbound is rendered below the source data with Marcus's exact words.
- [ ] No yellow "Flagged assumptions" panel is visible (because there are none — high confidence, grounded answer).

### 5e. Approve & Send

**What you do:**

1. Click **Approve & Send**.

**What you should see:**

- Button shows a brief loading state.
- Green toast: **"Sent — AI reply approved and delivered."**
- The draft disappears from the left list.
- Right pane shows the empty state: **"Pick a draft to review"** (because the queue is now empty).
- Sidebar AI Email Review badge clears.
- Bell badge decrements.

**Verify:**

- [ ] Toast appeared with the success copy.
- [ ] The communication log shows the sent email — open the transaction history to confirm a row labeled `[AI]` outbound to Marcus.

---

## Step 6 — Test 2: Document request with matching document on file

To test this, the transaction needs a document the AI can match.

### 6a. Upload an inspection report

**What you do:**

1. From the transaction card, click **+ Add Documents**.
2. Drag any PDF (or pick one) into the upload zone.
3. When prompted by the AI intake flow, set:
   - Type: **Inspection Report**
   - Name: `Apex Inspection Report — 742 Oak Ridge`
4. Confirm.

**Verify:** The document appears under the transaction's Documents tab with status `processed`.

### 6b. Seed the inbound

Use the same SQL/webhook approach as Step 5, with this body:

```sql
INSERT INTO communication_logs
  (id, tenant_id, channel, direction, transaction_id,
   sender_email, recipient_emails, subject, body, status, is_ai_generated,
   ai_assumptions, ai_source_data)
VALUES
  (gen_random_uuid(), '<oakridge-tenant-id>', 'email', 'inbound',
   '<txId>', 'marcus.reed@example.com',
   ARRAY['sarah.chen@oakridge-realty.test'],
   'Could you send the inspection report?',
   'Hi Sarah, could you send me a copy of the inspection report when you have a chance? Thanks!',
   'received', false, '{}'::text[], '{}'::jsonb);
```

Trigger the engine (webhook or restart).

### 6c. Verify the draft

**What you should see in `/ai-emails`:**

- A new draft with kind chip **"Document request"** (amber).
- Confidence around **93%**.
- Body reads something like:

  > Hi Marcus,
  >
  > Attached is the Apex Inspection Report — 742 Oak Ridge for 742 Oak Ridge Drive. Let me know if you need anything else from this file.

- Right pane shows `matched_document: Apex Inspection Report — 742 Oak Ridge`.

**Verify:**

- [ ] The draft correctly identifies the document by name.
- [ ] No flagged assumptions (high-confidence match).
- [ ] Approving and sending succeeds the same way as Step 5e.

---

## Step 7 — Test 3: Document request **without** a matching document (pending review)

This proves the AI refuses to claim it has a document it doesn't actually have on file.

### 7a. Seed the inbound

```sql
INSERT INTO communication_logs (...)
VALUES
  (..., 'marcus.reed@example.com', ARRAY['sarah.chen@oakridge-realty.test'],
   'HOA documents',
   'Hi Sarah — could you forward me the HOA documents? Want to read through them this weekend.',
   'received', false, '{}'::text[], '{}'::jsonb);
```

(There are no HOA docs on this transaction.)

### 7b. Verify the draft

**What you should see:**

- Kind chip: **"Document request"** (amber).
- Confidence around **55%**.
- Body reads:

  > Hi Marcus,
  >
  > Thanks for reaching out. The agent will review what you've asked for and follow up with the document shortly.

- A yellow **"Flagged assumptions"** panel below the body lists:
  > Could not find the requested document on this file — routed to the agent.

- The body no longer claims a document is attached — the safeguard kicked in.

**Verify:**

- [ ] The draft is `pending_review`, NOT auto-approved.
- [ ] The flagged assumption is highlighted in **amber** within the body where the assumption text appears.
- [ ] Source data shows `matched_document: null`.

### 7c. Decision time

You can either:
- **Edit & Send** to add the actual answer ("We don't have HOA docs on file yet — I'll request them from the seller's agent."), OR
- **Discard** if Marcus actually meant a different document.

Try **Edit & Send**:

1. Click **Edit**.
2. Change the body to:

   > Hi Marcus,
   >
   > Thanks for reaching out — we don't have the HOA documents on file yet. I'll request them from the seller's agent today and send them over as soon as they're back. They typically arrive within 2 business days.
   >
   > Talk soon,
   > Sarah

3. Click **Send Edit**.

**Verify:**

- [ ] Toast: **"Sent — Edited reply delivered."**
- [ ] The draft leaves the queue.
- [ ] Open the audit log (Admin only — see Step 13) and confirm an `edit_and_send` entry exists for this draft.

---

## Step 8 — Test 4: Vendor reply with a parseable date

### 8a. Seed the inbound

```sql
INSERT INTO communication_logs (...)
VALUES
  (..., 'scheduling@apexinspect.test',
   ARRAY['sarah.chen@oakridge-realty.test'],
   'RE: Inspection scheduling — 742 Oak Ridge',
   'Confirming inspection. Scheduled: 2026-05-22 at 9:00 AM. Tech: D. Patel. Please ensure utilities are on. — Apex Home Inspections',
   'received', false, '{}'::text[], '{}'::jsonb);
```

### 8b. Verify the draft

**What you should see:**

- Kind chip: **"Vendor reply"** (green).
- Confidence around **90%**.
- Body reads:

  > Thanks for confirming — I have you on the schedule for 2026-05-22. I'll update the file and circle back if anything changes on our side.

- Right pane source data shows `scheduled_date: 2026-05-22`.
- **Important:** even at 90% confidence, vendor replies are **never auto-approved** because they affect task dates — they always require human review (you can see this in the badge: it counts toward `pending_review`, not `auto_approved`).

**Verify:**

- [ ] The extracted date matches the inbound's `Scheduled: 2026-05-22`.
- [ ] No flagged assumptions (clean parse).
- [ ] Approve & Send works normally.

---

## Step 9 — Test 5: Vendor reply with vague wording

### 9a. Seed the inbound

```sql
INSERT INTO communication_logs (...)
VALUES
  (..., 'scheduling@apexinspect.test',
   ARRAY['sarah.chen@oakridge-realty.test'],
   'Re: Inspection follow-up',
   'Hey Sarah — we can probably get there sometime late next week, will let you know. — Apex',
   'received', false, '{}'::text[], '{}'::jsonb);
```

### 9b. Verify the draft

**What you should see:**

- Kind chip: **"Vendor reply"** (green).
- Confidence around **60%**.
- Body asks for clarification:

  > Thanks for the reply. Could you confirm the exact date in the format YYYY-MM-DD so I can lock it on the file?

- Yellow **"Flagged assumptions"** panel:
  > Could not parse a calendar date from the vendor reply — asked for clarification.

**Verify:**

- [ ] The draft is `pending_review`.
- [ ] The flagged assumption is highlighted within the body.
- [ ] You can either Edit (to write a more specific request) or Approve as-is to push the AI's clarification ask.

---

## Step 10 — Test 6: Uncertain / sensitive question (forbidden phrase safeguard)

This proves the AI refuses to overstep its boundary.

### 10a. Seed the inbound

```sql
INSERT INTO communication_logs (...)
VALUES
  (..., 'marcus.reed@example.com',
   ARRAY['sarah.chen@oakridge-realty.test'],
   'Concerns from the inspection',
   'Hey Sarah — the inspection report mentions some foundation cracks. Should I be worried? Do you think I have grounds to back out, or what would your legal advice be on this?',
   'received', false, '{}'::text[], '{}'::jsonb);
```

### 10b. Verify the draft

**What you should see:**

- Kind chip: **"Uncertain — review carefully"** (red).
- Confidence around **45%**.
- Body says something generic like:

  > Thanks for reaching out — I want to make sure we get this right, so the agent will follow up with the specifics shortly.

- Yellow **"Flagged assumptions"** panel may show:
  > Drafted without a confident match to a known intent.

- **Critical check:** the body does NOT contain the phrase "legal advice" or "I advise you to" anywhere except the disclaimer footer. The safeguard layer redacts these.
- The disclaimer at the bottom explicitly states: "*…Velvet Elves does not provide legal advice.*"

**Verify:**

- [ ] The draft is `pending_review` (uncertain kind never auto-approves).
- [ ] No mention of legal advice in the body — only in the disclaimer.
- [ ] **Discard** this one and let Sarah handle it personally.

---

## Step 11 — Test 7: Regenerate

Sometimes the first draft just isn't right and you want a fresh attempt without writing it yourself.

### 11a. Seed and find a draft

Use any of the previous inbound seeds (e.g. re-run the closing-date question with slightly different wording).

### 11b. Regenerate

**What you do:**

1. Open the draft in `/ai-emails`.
2. Click **Regenerate**.

**What you should see:**

- Brief loading state on the button.
- Toast: **"Regenerated — A fresh draft is ready for review."**
- The list refreshes; the old draft is gone.
- A new draft (with a new id) appears in its place — it should reference the same source data but the body wording may differ slightly.

**Verify:**

- [ ] The list count stays the same after regenerate (one out, one in).
- [ ] In the database, the old row has `discarded_at` populated and `approval_status = 'regenerated'` — the audit trail keeps both versions.

---

## Step 12 — Test 8: Tenant settings change

Sarah is the agent, not Admin — so she can't change tenant settings. Promote a test Admin user (or sign in as an existing one) to test this.

### 12a. Sign in as Admin

Register or use an Admin user in the same `oakridge-realty` tenant: `admin@oakridge-realty.test`.

### 12b. Update settings via API

Open Swagger ➜ `PUT /api/v1/ai-emails/settings`, body:

```json
{
  "tone": "friendly",
  "disclaimer": "Sent on behalf of Sarah at Oak Ridge Realty.",
  "escalation_hours": 24,
  "auto_send_threshold": 0.95
}
```

Execute.

### 12c. Trigger a new draft and observe the change

Sign back in as Sarah. Seed another factual question:

```sql
INSERT INTO communication_logs (...)
VALUES (..., '...', '...', 'Status check?', 'Hi Sarah — any updates on closing? — Marcus', ...);
```

**What you should see:**

- The new draft uses **"Cheers,"** as sign-off (friendly tone) instead of "Best regards,".
- The disclaimer reads: *"Sent on behalf of Sarah at Oak Ridge Realty."*
- The draft is now **`pending_review`** instead of `auto_approved`, because the threshold is 0.95 — most factual replies hover around 0.92, which is now below the line.

**Verify:**

- [ ] Sign-off and disclaimer changed.
- [ ] The same kind of inbound that was auto-approved in Step 5 now requires human review under the stricter threshold.

---

## Step 13 — Test 9: Escalation reminder

Stale drafts that nobody acts on get paged back to the file owner.

### 13a. Make a draft "stale"

In the database, pick any pending draft and force its `escalation_due_at` into the past:

```sql
UPDATE communication_logs
   SET escalation_due_at = now() - interval '2 hours'
 WHERE id = '<pick-a-pending-draft-id>'
   AND is_ai_generated = true;
```

### 13b. Run the escalation runner

Sign in as the Admin user. In Swagger:

```
POST /api/v1/ai-emails/escalations/run
```

Execute.

**Expected response:**

```json
{ "escalations_sent": 1, "tenant_id": "<oakridge-tenant>" }
```

### 13c. Switch back to Sarah's UI

**What you should see:**

- The escalated draft now has a **red "Escalated"** pill in the left list.
- Bell badge persists — the escalation row counts as a new system notification.
- A SYSTEM-channel communication log was emitted; you can see it in the transaction's history timeline as a system event.

**Verify:**

- [ ] Re-running the escalation endpoint immediately returns `escalations_sent: 0` (idempotent — the same draft doesn't page twice).

---

## Step 14 — Test 10: Discard

For the messes you don't want sent, edited, or regenerated.

**What you do:**

1. Pick any remaining pending draft.
2. Click **Discard** at the bottom-right.
3. Browser confirm dialog: "Discard this AI draft? It will be removed from the queue."
4. Click **OK**.

**What you should see:**

- Toast: **"Discarded — Draft removed."**
- The draft disappears from the left list.
- Sidebar badge decrements.

**Verify:**

- [ ] In the DB, the row still exists with `discarded_at`, `discarded_by = Sarah's id`, `approval_status = 'discarded'`.
- [ ] Audit log has a `discard` entry for `entity_type=ai_email`.

---

## Step 15 — Final cleanup checks

### 15a. Confirm queue is empty

Navigate to `/ai-emails`. You should see:

- **"No drafts to review"** in the left column.
- **"Pick a draft to review"** in the right pane.
- Sidebar badge gone.
- Bell badge cleared (or only counting unread tasks, not drafts).

### 15b. Confirm the audit trail is complete

Sign in as Admin. In Swagger:

```
GET /api/v1/audit-logs?entity_type=ai_email&page_size=50
```

**Verify the trail contains entries for:**

- [ ] `approve_and_send` (Step 5e)
- [ ] `approve_and_send` (Step 6c)
- [ ] `edit_and_send` (Step 7c)
- [ ] `approve_and_send` (Step 8b)
- [ ] `discard` or `edit_and_send` (Step 9b / 10b)
- [ ] `regenerate` (Step 11b)
- [ ] `update_ai_email_settings` on the tenant entity (Step 12b)
- [ ] `escalate` (Step 13b)
- [ ] `discard` (Step 14)

### 15c. Confirm communication log immutability

Pick the row from Step 5 (the closing-date approve & send). In SQL:

```sql
SELECT id, body, ai_confidence, approval_status, status,
       approved_by, approved_at, provider_name, provider_ref_id
  FROM communication_logs
 WHERE parent_log_id = '<the inbound from Step 5a>';
```

**Verify:**

- [ ] `approval_status = 'approved'`, `status = 'sent'`.
- [ ] `approved_by` is Sarah's user id, `approved_at` is when you clicked Approve.
- [ ] `body` matches the AI's drafted text (the one you saw before approving).
- [ ] `provider_name`, `provider_ref_id` are populated.

---

## Step 16 — Visual / UX sanity pass

Walk through `/ai-emails` one last time and check:

- [ ] **Empty state copy** is friendly and explanatory ("When AI prepares a reply that needs your sign-off, it shows up here.")
- [ ] **Loading skeletons** appear briefly when the list refetches (try the refresh button).
- [ ] **Mobile / narrow viewport:** resize the browser to ~800px wide. The right "source data" pane stacks below the body pane; everything stays usable.
- [ ] **Keyboard navigation:** Tab through the list ➜ Enter selects a draft ➜ Tab through the action buttons ➜ Enter triggers the focused action.
- [ ] **Error toasts** are red-tinted, not green. (Force one by disconnecting the iCloud integration and trying to Approve.)
- [ ] **Toast positioning** is consistent — bottom-right or wherever your design system places them.

---

## Walkthrough completion checklist

If you reach the end with all checkboxes ticked:

- [ ] **Step 1–4:** Setup complete (sign-in, provider, transaction, party).
- [ ] **Step 5:** Factual question auto-approved and sent.
- [ ] **Step 6:** Document request matched on file, sent.
- [ ] **Step 7:** Document request without match correctly stays in pending review.
- [ ] **Step 8:** Vendor reply with date parsed correctly.
- [ ] **Step 9:** Vague vendor reply asks for clarification.
- [ ] **Step 10:** Forbidden-phrase safeguard removes legal-advice language.
- [ ] **Step 11:** Regenerate produces a fresh draft and discards the old one.
- [ ] **Step 12:** Tenant settings change visibly affects new drafts.
- [ ] **Step 13:** Escalation runner pages a stale draft.
- [ ] **Step 14:** Discard removes a draft from the queue but preserves the audit row.
- [ ] **Step 15:** Audit trail and communication log are complete and immutable.
- [ ] **Step 16:** UI passes visual / accessibility / responsive checks.

---

## Common gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| Bell badge doesn't update | Polling delay (60 s) | Refresh the page or wait. |
| Approve & Send returns 409 | No connected email integration | Reconnect Gmail / iCloud / Outlook in Settings. |
| Draft never appears after seeding inbound | Inbound hook not registered | Restart the backend; check `app/main.py` startup logs for "register_inbound_hook". |
| Draft appears but has no transaction context | Marcus's email not on the transaction | Add him as a party (Step 4). |
| Approve fails with "Draft is in state 'approved'" | Two browser tabs raced | Reload — the first action won. |
| Regenerate returns the same body | The rule-based drafter is deterministic | This is expected without an LLM key; with `OPENAI_API_KEY` set, the polish pass varies output. |

---

**End of frontend walkthrough.** The next milestone (4.3 Vendor Communication System) builds on the `vendor_reply` kind we exercised in Steps 8 and 9 — the engine will then propose date updates to the linked task, not just confirm receipt.
