# Client Portal — Frontend UI Testing & Data-Setup Guide

**Purpose:** Step-by-step instructions for a tester/QA to configure data from the
**staff side** (Admin / Agent / TC / Team Lead) so that a logged-in **Client**
sees populated, real data on every Client portal surface.

**Scope:** The four represented-client surfaces — `/client/transactions`,
`/client/documents`, `/client/milestones`, `/client/agent` — plus the two-way
"Ask a question" thread. Backed by the 2026-05-23 Client rebuild.

**Spec reference:** `FRONTEND_UI_WORKFLOW_LOGIC.md` §9. Data layer:
`app/services/client_workspace.py`, `app/api/v1/dashboard_role.py` (`GET /dashboard/client`),
`app/api/v1/client_messages.py`.

> **Read this first — the one rule that explains everything.** The Client portal
> shows *nothing* until the client user has an **active row in
> `transaction_assignments`** for a transaction. That single link is the gate
> for all four surfaces. **As of 2026-05-25 the staff side ships a UI for this:**
> open the deal's **Client access** action to invite a new client (the
> assignment is auto-created on accept) or **Add an existing client** (the
> assignment is created directly). The API call documented below in
> [§3](#step-3-link-the-client-to-the-transaction-the-critical-step) is now a
> fallback for power users / scripting — the UI is the canonical path.
>
> The agent's two-way Q&A reply ([§6](#step-6--the-ask-a-question-thread)) also
> ships in the UI now: the **Client Q&A** action on the transaction card opens a
> drawer where the agent reads the client's questions and types a reply that
> appears in the client's portal thread — no `is_client_visible = true` SQL.

---

## 0. How data reaches each surface (mental model)

Every Client surface reads from the **single canonical endpoint** `GET /api/v1/dashboard/client`
(the thread is the one exception — it uses `GET /api/v1/client/messages`). Each
field is a *real projection* of staff-entered data — no stubs. Here is exactly
what staff action drives each surface:

| Client surface | What the client sees | Driven by (staff side) |
|---|---|---|
| **My Transactions** (`/client/transactions`) | Transaction cards: address, status pill, closing date, milestone stepper, next milestone | An **active `transaction_assignments` row** linking the client to the transaction; the transaction's `status`, `closing_date`, key-date columns |
| **Milestones** (`/client/milestones`) | Vertical timeline (completed / current / upcoming) + plain-English notes + key dates | **Tasks** on the transaction (status → state, `due_date` → order). If no tasks exist, falls back to the transaction's **key dates** |
| **Documents** (`/client/documents`) | List of the client's **own** uploads + a status summary (In progress / Uploaded / Verified / Complete) | Documents whose `uploaded_by == client.id`. Staff change `status` / `review_status` / `signature_status` to move buckets. **Agent-uploaded docs never appear here.** |
| **Agent Info** (`/client/agent`) | Agent name, company, bio, photo, phone, email | An assigned **Agent** (resolved by `users.role` priority Agent→TC→TeamLead→Attorney) with `bio`, `avatar_url`, `company_name`, `phone` filled on their profile |
| **Ask a question** thread | Client's own questions + any team reply explicitly surfaced | Client POSTs a question (auto client-visible). A **team reply only appears if `communication_logs.is_client_visible = true`** — there is no staff UI for this yet (see Known gaps) |

Key-date columns that surface as "key dates" (set on the transaction):
`contract_acceptance_date`, `em_delivered_date`, `inspection_response_date`,
`appraisal_expected_date`, `cd_delivered_date`, `cleared_to_close_date`,
`possession_date`, `closing_date`.

---

## 1. Prerequisites

- **Two sessions side by side.** Use two browsers (or a normal + incognito
  window) so you can stay logged in as **staff** in one and as the **client** in
  the other without constant re-login.
- A **staff login** with role Admin, Agent, or Team Lead (you'll create
  invitations and transactions, and link the client).
- The ability to make one **authenticated API call** (Swagger UI at
  `/docs`, Postman, or `curl`). This is required for Step 3.
- Same **tenant** for staff and client (cross-tenant access is blocked by design).

---

## 2. Setup walkthrough

### Step 1 — Create the Client user

1. As **Admin** (or Agent/Team Lead), open **User Management** (`/admin/users`) or
   the team **Invite** action and click **+ Invite User**.
2. Enter the client's email, choose role **Client**, send the invite.
3. Open the invite link (check the invitation list / email), accept it, and set a
   password. The client now exists and can log in.
   - On **first login the client goes through onboarding** (external role = 3
     steps: Welcome → Profile → All set). Finish it; the client lands on
     `/client/transactions`.
4. **At this point the portal is empty** — "No transactions yet. Your agent will
   add you when your transaction begins." That is correct: the client isn't
   linked to anything yet.

> ⚠️ Inviting the client "to a transaction" does **not** link them. The invite's
> `transaction_id` field is not wired in the invite modal, and accepting an invite
> does **not** create a `transaction_assignments` row. Linking is Step 3.

### Step 2 — Create a transaction and give it dates

1. As **staff**, click **+ New Transaction** and run the wizard to create a deal
   (any property/address). Note its **transaction ID** (visible in the URL after
   creation, e.g. `/transactions?highlight=<id>`, or via the transactions list).
2. Make sure the transaction has, at minimum, a **`closing_date`** and a
   **`status`** (Active). Set whatever other key dates you want to appear
   (`contract_acceptance_date`, `inspection_response_date`, etc.). Set these in
   the transaction edit fields; if a particular key-date field isn't exposed in
   the UI, set it with `PATCH /api/v1/transactions/{id}` or directly in the DB.
3. **For the Milestones timeline:** open the transaction workspace and **Add
   Tasks** (a few, with `due_date`s). Task status maps to the client timeline:
   - `Completed` / `Skipped` → **completed**
   - `InProgress` / `Blocked` → **current**
   - anything else (Pending) → **upcoming**
   - With **no tasks**, the timeline falls back to the transaction's key dates, so
     a deal with only dates still renders a journey.

### Step 3 — Link the client to the transaction (THE critical step)

**Canonical path (UI, as of 2026-05-25).** Open the deal as staff and click the
**Client access** action on the transaction card. The modal offers three things:

- **Invite a new client.** Enter the client's email and press *Invite* (you can
  copy the invite link if email is slow). When the client accepts, an active
  `transaction_assignments` row with `role_in_transaction = 'client'` is
  auto-created — they land on a populated `/client/transactions` immediately.
- **Add an existing client.** Search the picker (active Client-role users in
  your tenant) and click *Add*. The assignment row is created right away.
- **Remove access.** Click the trash on a row in the *With portal access* list.
  The assignment is set inactive (history preserved) — the client's portal
  returns to the empty state.

There is no separate "Assign team" entry for clients on purpose: the team modal
is for **internal teammates** (Attorney/Agent/TC/Team Lead) and never pollutes
its picker with counterparties. "Client access" is the dedicated counterparty
control.

**Fallback (API, for scripting / power users).** The endpoint the UI calls is
still available:

```
POST /api/v1/transactions/{transaction_id}/assignments
Authorization: Bearer <staff JWT>
Content-Type: application/json

{
  "user_id": "<the client's user UUID>",
  "role_in_transaction": "client"
}
```

- `role_in_transaction = "client"` is what the UI writes; it does NOT pollute
  the Agent Info card (that card resolves by the joined `users.role` and skips
  the client's own row).
- The assignment is created `is_active = true` by default — that's the gate.

**Verify:** refresh the client's `/client/transactions`. The transaction card
should now appear with address, status, closing date, and the milestone stepper.

### Step 4 — Make the Agent Info card real

1. Ensure an **Agent** is assigned to the same transaction. The wizard usually
   sets the creator as `primary_agent`; otherwise use the transaction's **Assign
   team** modal to add an Agent. (TC/Team Lead/Attorney also work as fallbacks,
   but the card prefers a real Agent.)
2. Fill that agent's **profile**: name, `company_name`, `bio`, `avatar_url`,
   `phone` (via their Profile/onboarding). Empty fields render as blanks/initials
   on the client's Agent Info page, so populate them to test the full card.

### Step 5 — Documents (must be uploaded *by the client*)

The client's Documents page shows **only documents they uploaded themselves**
(`uploaded_by == client.id`). A document an Agent/TC uploads to the same
transaction will **not** show on the client portal — this is intentional scoping,
not a bug.

To populate and exercise the Documents surface:

1. As the **client**, open **Documents** → header **Upload a document** (modal).
   Pick the transaction, a document type, optional label, attach a file, submit.
2. The new doc lands in the **Uploaded** bucket.
3. As **staff**, find that document in **All Documents** and change its review
   state to move it between the client's summary buckets:
   - `status` = pending/processing/failed, **or** `review_status` = `needs_follow_up` → **In progress**
   - `review_status` = `approved` **and** a signature still in flight → **Verified**
   - `review_status` = `approved` and no pending signature → **Complete**
   - processed but unreviewed → **Uploaded**
   - (Use the staff document review/approve action, or `PATCH /api/v1/documents/{id}`.)
4. Back on the client, the **status summary** updates to match. ("Missing" is never
   shown for a represented client — required-doc tracking is the agent's job.)
5. **Flag for deletion:** the client can flag a doc (not hard-delete); it appears
   in the staff **Deletion Queue** for approve/reject.

### Step 6 — The "Ask a question" thread

1. As the **client**, open a transaction's **View details** → **Ask a question**
   (or the topbar **Ask your agent** CTA, which deep-links with `?ask=1`). Send
   a question. It persists immediately as a **client-visible** message and
   notifies the assigned staff member.
2. The client sees their own message in the thread (right-aligned, "You").
3. **Team reply (UI, as of 2026-05-25).** Open the deal as staff and click
   **Client Q&A** on the transaction card. The drawer shows the same thread the
   client sees (client questions on the left, team replies on the right) and an
   amber *"Your client is waiting for a reply"* banner when the latest message
   is from the client. Type a reply in the composer and press *Send reply*. The
   reply lands in the client's portal thread immediately. Ordinary internal
   notes/emails still never leak in (only the staff Client Q&A composer writes
   `is_client_visible = true`).
4. **Cross-deal discovery.** The new **Clients** sidebar entry opens an index
   of every represented client with two "needs me" badges per deal: an *unanswered*
   pill when the client is waiting, and a *to review* count for the client's own
   uploads that aren't approved yet. Each row deep-links straight into the Client
   Q&A drawer (or the Client access modal) on the matching deal.

---

## 3. Per-surface verification checklist

| # | On the staff side… | Then as the client, expect… |
|---|---|---|
| 1 | Create assignment row (Step 3) | `/client/transactions` shows the deal card (address, status, closing date, stepper) |
| 2 | Set `closing_date` + key-date columns | "Key dates" populate; "Next milestone" reflects soonest active/upcoming |
| 3 | Add tasks with statuses + due dates | `/client/milestones` timeline shows completed/current/upcoming with plain-English notes |
| 4 | Assign an Agent + fill their profile | `/client/agent` shows name, company, bio, photo, phone, email + call/email actions |
| 5 | Client uploads a doc; staff approves it | `/client/documents` list shows the upload; summary bucket moves Uploaded→Verified/Complete |
| 6 | Client asks a question | Thread shows the question; the deal's "Client Q&A" action carries an amber dot on the staff side, and the deal appears with an *unanswered* pill in the **Clients** hub |
| 7 | Staff opens **Client Q&A** on the deal and sends a reply | Thread shows a "Your team" reply; the badge + hub pill clear |

---

## 4. Negative checks (the boundary should hold)

Confirm the client **cannot** see staff-only data:

- **Agent-uploaded documents** do not appear on the client Documents page.
- **Internal notes, AI drafts, document-action and system rows** in
  `communication_logs` do **not** appear in the client thread (only
  `is_client_visible = true` rows do).
- **Tasks, internal comm logs, AI suggestions** are absent from every client surface.
- A client linked to transaction A **cannot** read transaction B's thread/docs
  (the `assert_client_transaction_access` 403 guard).
- Client **cannot hard-delete** a document (only "Flag for deletion").

---

## 5. Known gaps — things that look like bugs but aren't

1. ~~**No staff button links a Client to a transaction.**~~ **Resolved 2026-05-25**
   — the **Client access** modal handles invite / add-existing / remove and the
   invite-accept flow auto-creates the assignment. The Step 3 API call remains as
   a scripting fallback.
2. ~~**No staff UI for a client-visible reply.**~~ **Resolved 2026-05-25** —
   the **Client Q&A** drawer is the staff reply path. The `is_client_visible = true`
   write happens server-side when the composer is used; ordinary internal
   notes/emails still never leak in.
3. **Documents are own-uploads-only.** By design — but testers often expect
   agent docs to show. They won't. The new **Clients hub** surfaces the count of
   the client's own uploads still awaiting review per deal, which is the
   discovery surface for that scope.
4. **"Missing" document count is intentionally absent** for represented clients.
5. **No generic in-app notifications feed yet.** The `client_question` row that
   is written best-effort to the `notifications` table on every client question
   is currently consumed by nothing in the UI — discovery instead runs through
   the Client Q&A action's amber dot (per-card) and the **Clients** hub's
   per-client unanswered pill. The deep-link plumbing (`transaction_id` on the
   notification, `?clientqa=1` on the transactions list) is in place for the day
   a generic feed lands.

---

## 6. Cleanup / reset

- **Unlink a client:** set their `transaction_assignments` row `is_active = false`
  (or `DELETE /api/v1/transactions/{id}/assignments/{assignment_id}` as
  Team Lead/Admin). The portal returns to the empty state.
- Soft-deleted documents drop out of the client's list and summary automatically.
- Revoke unused invitations from the invitation list if you created throwaway
  client accounts.
