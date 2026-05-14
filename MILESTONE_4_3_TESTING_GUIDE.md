# Milestone 4.3 — Vendor Communication System: Testing Guide

**Last updated:** 2026-05-14
**Companion to:** `MILESTONE_4_3_IMPLEMENTATION_PLAN.md`
**Audience:** Jan (developer + QA) running manual smoke tests on
`dev.velvetelves.com` before cutting to production.

---

## 0. Pre-flight checklist

1. Backend tests green: `pytest app/tests/test_vendor_communications_api.py`
   (11 tests). Full suite: `pytest` → 549 passing.
2. Frontend builds clean: `npx tsc --noEmit && npx vite build`.
3. Both 4.3 migrations applied on dev:
   - `20260622_milestone_4_3_vendor_comms.sql`
   - `20260622_seed_vendor_email_templates.sql`
4. At least one connected email provider (Gmail or Outlook) on the test
   agent's account.
5. At least one transaction with a task assigned to the test agent.

---

## 1. Template seeding + admin CRUD

Goal: confirm every tenant has the five system templates and that admins can
add/edit custom templates.

1. Sign in as Admin → sidebar **Team → Vendor Templates**.
2. Expect five rows tagged "System template":
   - Inspection — Schedule Visit
   - Inspection — Reschedule
   - Appraisal — Schedule Visit
   - Title — Document Request
   - Generic Vendor — Scheduling
3. Click any system template; verify the body contains
   `Reply with: Scheduled: YYYY-MM-DD`. Edit a value and save — toast
   reads "Template updated."
4. Click **New template**; create a custom one (e.g. category
   `survey`); confirm the "Custom" pill appears and it shows up in
   the template picker inside `VendorRequestModal`.
5. Sign out and back in as Agent; reopen the template list — the new
   custom template is visible (template list is tenant-wide).

**Pass criteria:** five system templates per tenant, custom CRUD round-trip
works, agents can use admin-created templates.

---

## 2. Outbound vendor request (the happy path)

Goal: send a real email through the user's provider and confirm the
communication log captures all the threading metadata.

1. Sign in as Agent. Open a transaction with at least one open task.
2. Open the transaction drawer → Tasks column → click **Email vendor**
   on a task (button only renders when a vendor assignment exists; see §3).
3. `VendorRequestModal` opens. Pick a template; the right pane shows
   the rendered subject and body with the constrained-format footer.
4. Verify the **thread marker** chip looks like `VE-TASK-xxxxxxxx`
   matching the first 8 chars of the task id.
5. Click **Send request**.
6. Open the Communications panel for that transaction. Expect a new
   outbound row with channel "Email", `ai_kind=vendor_request`,
   thread_key starting with `VE-TASK-`, and the body containing the
   constrained footer.
7. Open Gmail/Outlook in another tab — the actual email landed in the
   vendor address inbox.

**Pass criteria:** real send succeeds; log row captures
`metadata_json.task_id`, `thread_key`, and `message_id_header`.

---

## 3. Per-transaction vendor assignment + contacts

Goal: ensure a vendor company can be linked to a transaction, contacts
opt in/out, and the one-primary rule holds.

1. Choose a vendor company (or create one under **Vendors**).
2. Hit `POST /api/v1/transactions/{tx}/vendor-assignments` from the
   API console (or the Transactions UI when the assignment manager
   surfaces it) with `vendor_id`, `role=inspector`, two `contact_ids`,
   and `primary_contact_id=<first>`.
3. Confirm the response lists both contacts, exactly one with
   `is_primary=true`.
4. Switch the primary to the second contact via
   `PUT /transactions/{tx}/vendor-assignments/{id}/contacts`; verify
   only one row carries `is_primary=true`.
5. The integration test
   `test_assignment_contacts_enforce_single_primary` covers this in CI.

---

## 4. Inbound vendor reply → proposal

Goal: confirm the engine creates a proposal row and the AI Email Review
page shows the Linked Task Proposal panel.

1. From the dev mailbox associated with the test vendor, reply to the
   request email you sent in §2 with a body of:
   ```
   Scheduled: 2026-07-12
   ```
2. Wait for the inbound webhook to ingest. Refresh `/ai-emails`.
3. Expect a new draft with `ai_kind=vendor_reply` and confidence ≥ 0.9.
4. Open the draft. The right rail now shows **Linked Task Proposal**
   with:
   - Original date (the current task due date)
   - Vendor proposed `2026-07-12` (mono font)
   - Accept / Clarify / Reject CTAs
5. The sidebar's **Vendor Proposals** chip shows a count of 1.

Variant: send a vague reply (`We can come sometime next week.`) → the
engine should still create a draft AND a proposal with status
`needs_clarification` and `proposed_due_date=null`.

**Pass criteria:** proposals.json contains the new row linked to the
correct task; sidebar badge updates within 60 s.

---

## 5. Proposal accept / reject / clarify

Goal: confirm task date updates only via the human-approval gate.

1. From `/vendor-proposals`, click **Accept & update task** on a
   pending proposal.
2. Refresh the transaction's tasks tab — the task's due date now
   matches the proposed date.
3. Open `/admin/audit-logs` (admin) and confirm there's a
   `vendor_proposal_accepted` entry (entity_type=task) with
   before/after `due_date`.
4. On a separate proposal, click **Reject** — task date is unchanged;
   audit log shows `vendor_proposal_rejected`.
5. On a `needs_clarification` proposal, click **Ask vendor to clarify**;
   confirm the proposal status flips and the audit log records the
   transition.

---

## 6. Public colleague-invite flow

Goal: a vendor can attach a colleague without a login.

1. From `/vendors/:vendorId`, click **Add colleague (public link)**.
   The link is copied to the clipboard and a toast confirms.
2. Open the link in a private browsing window (no auth). The page
   displays the vendor company name + tenant branding only — no
   transaction details.
3. Submit `first_name`, `last_name`, `email`, `phone`, `title`.
4. The success card reads "You're on the thread."
5. Back in the authenticated app, reload `/vendors/:vendorId` →
   Contacts list now includes the new colleague (not marked primary).
6. Re-open the link → page now shows the "no longer valid"
   message (single-use enforced).
7. Try 25 rapid GETs against the same `/v/:token` path — the 21st+
   should return HTTP 429.

---

## 7. Background refresh

Goal: tenant-local suggestions surface and apply per field with audit.

1. On a vendor with at least one linked contact whose phone differs
   from the vendor's, click **Refresh info** on the vendor detail page.
2. Drawer opens; click **Run refresh**. Suggestions appear as diff
   cards with `current` vs `suggested`, confidence, and source label.
3. Tick one suggestion → click **Apply selected**.
4. Vendor detail's "At a glance" section now reflects the new value.
5. `/admin/audit-logs` shows `vendor_background_refresh_applied` per
   accepted field.

---

## 8. Unified communication log UI

1. Open `/communications`. Confirm date grouping (Today / Yesterday /
   older).
2. Toggle **Vendor traffic only** — list filters to rows with
   `ai_kind` of `vendor_request` or `vendor_reply`.
3. Toggle the channel chip to **SMS (soon)** — list goes empty and
   the chip looks visibly muted.
4. Paste a transaction id into the filter and click **CSV** —
   downloads a single-transaction CSV.
5. Click **Multi-tx export** — lands on `/admin/communication-exports`
   (Admin-only; lower roles still see the link with a tooltip).

---

## 9. SMS / voice hooks (no-op visual check)

1. On a vendor contact card, hover the **Call** button — tooltip
   reads "Call via Twilio (coming soon)" and the button is greyed.
2. Flip `tenants.settings_json.vendor_comms.phone_action_enabled=true`
   for the tenant (PUT `/vendor-communications/settings`).
3. Reload the page — the **Call** button is now enabled (no provider
   wired yet; clicking does nothing today).
4. Confirm communication logs can be inserted with `channel='sms'` or
   `channel='voice_call'` without 500s (covered by
   `test_communication_log_metadata_persists`).

---

## 10. Production rollout gate

- [ ] Migrations applied on production.
- [ ] System templates seeded on every existing tenant.
- [ ] Smoke flow §2 + §4 + §5 run on a production-like deal.
- [ ] No new errors in the backend log for the
      `app.services.vendor_proposal_service` and
      `app.api.v1.vendor_communications` modules over a 24h window.
- [ ] Sidebar **Vendor Proposals** badge clears to 0 when the queue
      is empty.
- [ ] FRONTEND_UI_WORKFLOW_LOGIC.md §13.E reflects 4.3 behavior.
- [ ] SYSTEM_DESIGN.md endpoint tables list the new routes.
- [ ] milestones.txt §4.3 deliverables ticked off.

---

**End of testing guide.**
