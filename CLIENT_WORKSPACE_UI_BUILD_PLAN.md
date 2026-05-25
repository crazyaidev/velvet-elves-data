# Client Workspace — End-to-End UI Workflow Build Plan

**Date:** 2026-05-25
**Status:** **IMPLEMENTED 2026-05-25.** WS1 + WS2 shipped plus the §8.1-broader
**Clients hub** the user chose. The whole client lifecycle — grant access →
client uploads/asks → agent replies → review → remove access — now runs through
the staff UI. No Swagger or SQL.
**Related:** `CLIENT_WORKSPACE_PLAN.md` (2026-05-23 rebuild), `CLIENT_PORTAL_TESTING_GUIDE.md`,
`FRONTEND_UI_WORKFLOW_LOGIC.md` §9.

> **§8 decisions, confirmed before building:** 8.1 = **Broader Client hub**
> (with the user's add-on: only the Cross-deal Clients index — not
> promote-contact, not self-serve sharing, not per-client activity). 8.2 =
> **Dedicated drawer** for Client Q&A. 8.3 = **Include "Add existing client"**
> in WS1. 8.4 = labels **"Client access" + "Client Q&A"**.
>
> **Scope deltas worth flagging:**
>
> - **WS3 (document-review legibility).** Approve/Verify + the deletion
>   approve/reject loop were already wired in All Documents via
>   `useApproveDocumentReview` / `useApproveDeletion` / `useRejectDeletion` —
>   Gap C is verified-closed. The "Uploaded by client" badge/filter retrofit
>   into the 2,000-line `DocumentsPage` was *not* built: the broader hub the
>   user added already surfaces *"N docs to review"* per client, which is a
>   strictly better discovery surface for the same need. The retrofit can be
>   added later on top of the existing approve path; it would be a contained
>   slice, not a rebuild.
>
> - **Notifications deep-link (original WS2 #5).** The repository has no
>   migration creating a generic `notifications` table and no endpoint reads
>   it — the `client_question` insert in `client_messages.py` is a best-effort
>   no-op today. Rather than build a generic notifications feed, discovery is
>   driven from real thread state: an amber dot on the per-card *Client Q&A*
>   action (fed by `GET /clients/thread-summary`) plus the Clients hub's
>   per-client *unanswered* pill. The `transaction_id` field is now carried on
>   the `client_question` best-effort write, so the day a generic feed lands,
>   deep-linking to the Client Q&A drawer is trivial — the
>   `?expand=<id>&clientqa=1` (and `&clientaccess=1`) handler is already in
>   `TransactionListPage`.

---

## 1. Problem statement

The client-facing portal (`/client/*`) was rebuilt 2026-05-23 with real
projections and works. But the **staff-side controls that feed it do not exist in
the UI.** Today, making the portal show anything requires a developer:

| Workflow step | Today | Acceptable for a real-estate agent? |
|---|---|---|
| Give a client access to a deal | `POST /transactions/{id}/assignments` (curl/Swagger) or DB insert | ❌ No |
| Reply to a client's question | Manual `is_client_visible=true` SQL insert | ❌ No |
| Review client uploads / move status | Mostly exists in All Documents | ⚠️ Verify |
| Milestones / key dates / agent card | Auto-derived from existing tx data | ✅ Yes |

The user is an **agent, not a developer.** "Fully functional" means the entire
client lifecycle — grant access → client uploads/asks → agent reviews/answers →
remove access at close — runs through the frontend with **no API calls or SQL.**

**Two blocking gaps** to close, plus one to verify:

- **Gap A — Client linkage has no UI.** The `transaction_assignments` row is the
  single gate for the whole portal, but no staff button creates it for a Client
  (`AssignTeamModal` excludes Client by design; invite-accept creates the user but
  no assignment row).
- **Gap B — No client-visible reply path.** The agent is notified of a client
  question but has no UI (and no backend write-path) to answer *into the client
  thread*. The `is_client_visible` column exists; nothing writes it except the
  client's own POST.
- **Verify C — Client document review.** Confirm the agent can find client uploads
  and move them through review buckets entirely in the UI.

---

## 2. The workflow we are enabling (agent's story)

1. Agent creates a transaction (exists).
2. From the deal, agent clicks **Client access → Invite client** (or **Add existing
   client**). The client gets a transaction-scoped invite.
3. Client accepts, completes the 3-step external onboarding, lands on a populated
   `/client/transactions` (assignment auto-created on accept).
4. Client uploads paperwork and asks a question.
5. Agent gets a notification; opens the **Client Q&A** thread on the deal and
   **replies** — the reply appears in the client's thread.
6. Agent reviews the client's uploaded docs and marks them verified/complete; the
   client's status summary updates.
7. Milestones, key dates, and the Agent Info card populate automatically from the
   deal's tasks/dates and the assigned agent's profile.
8. At closing, agent **removes client access** (or it's archived with the deal).

Everything above is a button in the staff UI. No Swagger, no SQL.

---

## 3. Design constraints (must follow)

- **No new detail pages.** Transaction Detail is de-scoped (deep-link only). All
  new staff UI = **modals/drawers launched from the transaction card**, exactly
  like `Assign team`, `Add contact`, and `Comms`.
- **No duplicate nav; upload/compose = modal; quiet "professional tool" styling**
  (per attorney-workspace + tool-aesthetic rules).
- **Clients are a counterparty, not staff** — keep client-access UI separate from
  the internal "Assign team" modal (which is explicitly "teammates who get this in
  their own workspace"). Don't pollute that picker.
- **Notification cards get explicit buttons** ("View question" / "Reply"), not a
  whole-card click target.
- **Reuse, don't fork:** the `is_client_visible` column and the
  `client_workspace`/`client_messages` projections already exist — extend them;
  don't build a parallel store.

---

## 4. Workstreams

### WS1 — Client access management (closes Gap A) — *the unblocker, build first*

**Backend**
1. **Assignment-on-accept.** In `invitations.accept_invitation`, after the user
   profile is created: if `invitation.transaction_id` is set, create an **active
   `transaction_assignments` row** for the new user with
   `role_in_transaction` derived from the invited role (`"client"` for Client).
   Idempotent (skip if an active row already exists). This makes "invite a client
   to a deal" actually link them.
2. **Existing-client picker endpoint.** Add `GET /api/v1/users/assignable-clients`
   (or extend `/users/assignable?kind=client`) returning active Client-role users
   in the tenant, so an agent can attach a client who already has an account
   without seeing the full user directory.
3. The direct assignment endpoint (`POST /transactions/{id}/assignments`) already
   accepts any `user_id` — reuse it for "add existing client."

**Frontend**
4. New **`ManageClientAccessModal.tsx`** (in `components/active-transactions/`),
   launched from a new transaction-card action **"Client access"** (wire
   `onOpenClientAccess` callback through `TransactionCard.tsx` →
   `TransactionListPage.tsx`, mirroring `onOpenAssignTeam`). The modal:
   - Lists clients **currently with portal access** to this deal (active
     `role_in_transaction='client'` assignments) + a **Remove access** action.
   - **Invite a new client:** email field → transaction-scoped Client invitation
     (`POST /invitations` with `transaction_id` + `role: Client`). Surfaces a
     copy-link in case email is slow.
   - **Add an existing client:** searchable picker from the new
     assignable-clients endpoint → `POST /transactions/{id}/assignments`.
5. New hook **`useClientAccess.ts`** (list/invite/add/remove).
6. Optional polish: an **"Invite client"** step/CTA in the New Transaction wizard's
   success screen so access can be granted at creation.

**Acceptance:** An agent can grant a brand-new or existing client access to a deal,
see them listed, and revoke it — entirely in the UI. Client invites do **not**
consume a staff seat (Client is non-billable).

---

### WS2 — Two-way client messaging in the staff UI (closes Gap B)

**Backend**
1. **Staff reply write-path.** New endpoint, e.g.
   `POST /api/v1/transactions/{id}/client-thread` (or add a staff-authorized reply
   route in `client_messages.py`). Writes a `communication_logs` row with
   `is_client_visible=true`, `direction='outbound'`, `channel='note'`,
   `sender_user_id=<staff>`. Authz: `require_transaction_access` + staff role
   (Agent/TC/TeamLead/Admin). This is the missing reply path the rebuild plan
   flagged as "not built."
2. **Staff thread read.** `GET` of the same client-visible thread for the deal
   (mirror `list_client_messages`, staff-authorized) so both sides see one thread.
3. Mark the existing `client_question` notification actionable (carry
   `transaction_id` so the UI can deep-link).

**Frontend**
4. **Client Q&A view** — recommend a dedicated **`ClientThreadDrawer.tsx`** opened
   from a new card action **"Client Q&A"** (badge when unanswered questions exist),
   mirroring `ClientAskThread.tsx` so staff and client see the same bubbles +
   a reply composer. *(Alternative: a "Client thread" tab inside the existing
   `CommunicationsPanel`. See Decisions.)*
5. **Notification entry point.** The `client_question` notification renders explicit
   **"View question"** / **"Reply"** buttons that deep-link to the deal's Client Q&A
   drawer.
6. Hooks: `useTransactionClientThread` (staff list + reply).

**Acceptance:** Agent sees a client's question in-app, replies in the UI, and the
client sees the reply — no SQL. Internal notes/emails still never leak into the
client thread (only `is_client_visible` rows appear).

---

### WS3 — Client document review legibility (verify/close Gap C)

**Frontend (mostly verification + small adds)**
1. In **All Documents** and the per-deal **Docs drawer**, confirm a staff
   **Approve/Verify** control exists and is reachable for client-uploaded docs;
   if missing, add it (drives the client's Uploaded→Verified→Complete summary).
2. Add an **"Uploaded by client"** badge/filter so the agent can find client
   submissions quickly.
3. Confirm the **flag-for-deletion → Deletion Queue** approve/reject loop is
   surfaced in the UI (it is, per `documents.py`; just verify the screen).

**Acceptance:** Agent can locate a client's upload, verify/approve it, and approve
or reject a deletion flag, all in the UI.

---

### WS4 — Out of scope (call out, don't build now)

- **Client self-serve milestone sharing.** The share system
  (`/dashboard/fsbo/share-link`) is not client-eligible; the portal currently shows
  an honest "ask your agent" note. Building client share is a separate, explicitly
  scoped decision (`CLIENT_WORKSPACE_PLAN.md` §11.3) — leave as-is.
- **Linking an existing `transaction_parties` contact ↔ a client login.** Contacts
  (no login) and client users (login + assignment) are different tables. A future
  "promote contact to portal client" affordance is a nice-to-have, not MVP.

---

## 5. Sequencing & estimate

| Phase | Workstream | Why this order | Est. |
|---|---|---|---|
| 1 | WS1 backend (assignment-on-accept + clients picker) | Unblocks *all* portal data | ~1.0 d |
| 2 | WS1 frontend (Client access modal + card wiring) | First fully-UI workflow | ~1.0 d |
| 3 | WS2 backend (reply write-path + staff thread read) | Completes the two-way loop | ~1.0 d |
| 4 | WS2 frontend (Client Q&A drawer + notification deep-link) | Agent can answer in-app | ~1.5 d |
| 5 | WS3 verify + small adds | Low risk, mostly confirmation | ~0.5–1.0 d |
| 6 | Tests + doc reconciliation + QA pass | Per root-cause-over-patches | ~1.0 d |

**Rough total: ~6 dev days.** WS1 alone makes the portal demoable end-to-end; WS2
makes it complete.

---

## 6. Tests

- **Backend:** invite-accept creates the assignment (and is idempotent); client
  appears on `/dashboard/client` after accept; staff reply writes
  `is_client_visible=true` and is authz-gated to assigned staff; non-party staff
  get 403; internal notes still excluded from the thread.
- **Frontend:** Client access modal (invite / add existing / remove) render +
  interaction tests; Client Q&A drawer renders thread + posts reply; notification
  deep-link. Keep tsc/eslint clean (the rebuild's bar).

---

## 7. Docs to reconcile (don't skip)

- **`FRONTEND_UI_WORKFLOW_LOGIC.md`:** add the staff-side flows — Client access
  modal and Client Q&A drawer — to the transaction-workspace section, and update
  §9 to note the reply path now exists.
- **`CLIENT_WORKSPACE_PLAN.md`:** mark the reply-write path and client-linkage UI
  as built; close those risk items.
- **`CLIENT_PORTAL_TESTING_GUIDE.md`:** replace the curl/SQL steps (3 and 6) with
  the new UI steps once shipped.

---

## 8. Decisions to confirm before building

1. **Scope:** MVP = close Gap A + Gap B + verify C (this plan). Or a broader staff
   "Client hub"? *(Recommend: MVP as scoped.)*
2. **Client Q&A home:** dedicated **drawer from the card** (recommended — keeps the
   client thread distinct and uncluttered) vs. a **tab inside the existing
   Communications panel** (fewer surfaces, but mixes internal + client traffic).
3. **"Add existing client"** in WS1: build now, or MVP = invite-new-client only and
   defer the existing-user picker? *(Recommend: include it — it's a small endpoint
   and agents reuse clients across deals.)*
4. **Naming:** the client-facing thing is the "Client portal"; the staff-side
   controls here are "Client access" + "Client Q&A." Confirm the labels.
