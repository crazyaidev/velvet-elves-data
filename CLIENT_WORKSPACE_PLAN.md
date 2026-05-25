# Client Workspace — Rebuild Plan (rev 1)

*Drafted: 2026-05-23. Grounded in the current state of the repo and in the
lessons from the FSBO and Attorney workspace rebuilds.*

> **STATUS: Client portal rebuild IMPLEMENTED 2026-05-23 (this plan).** The
> two open items §8 #8 + §11 #7 flagged — the missing staff reply write-path
> and the absence of a staff UI to link a Client to a deal — were closed on
> **2026-05-25** by the staff-side build documented in
> `CLIENT_WORKSPACE_UI_BUILD_PLAN.md`: the **Client access** modal (Gap A)
> and the **Client Q&A** drawer (Gap B), plus a cross-deal **Clients** hub.
> Together they make the whole client lifecycle run through the UI — no
> Swagger or SQL — which is the bar the original prompt set. The
> `is_client_visible` migration this rebuild added is the column those staff
> surfaces now write through; the visibility model didn't change.

This plan covers the **represented-client portal** — the buyer/seller who is
represented by an Agent/TC (the structural sibling of the FSBO portal, which
serves the *un*represented seller). Spec home: `FRONTEND_UI_WORKFLOW_LOGIC.md`
§9 (Client Portal). Routes: `/client/transactions`, `/client/documents`,
`/client/milestones`, `/client/agent`.

> **Why this is a *rebuild*, not a *remediation*.** The FSBO rebuild was mostly
> visual cleanup because FSBO's backend had already shipped real projections.
> The Client portal is the opposite: its shell carries the same visual defects
> FSBO had, **and** its data layer is still stubbed. The single endpoint that
> feeds all four surfaces —
> [`GET /api/v1/dashboard/client`](velvet-elves-backend/app/api/v1/dashboard_role.py#L659) —
> returns `documents_summary` hardcoded to all zeros, `recent_messages=[]`, a
> `bio: None` agent card, and `upcoming_milestones` that is just the closing
> date relabeled "Closing." So this rebuild has a real backend half, not only a
> restyle. That matches the root-cause-over-patches expectation: fix the model
> (write + read + backfill), don't paint over the stub.

---

## 1. Goals

The Client workspace should feel like a calm, branded portal for a represented
buyer/seller: *what's happening on my deal, what do I owe, who do I contact.*
It must never leak internal workflow (tasks, internal notes, AI drafts, audit
chatter, other parties' data).

Concretely, the rebuild must:

1. **Run one navigation system.** Today the AppLayout sidebar group and the
   in-shell tab bar list the **exact same four destinations** — a textbook
   duplicate-nav violation. Pick one.
2. **Make every surface tell the truth.** Replace the stubbed
   `documents_summary` / `recent_messages` / milestones / agent bio with real
   projections, or remove the affordance until it's real. No hardcoded-zero
   boards.
3. **Reconcile the client↔transaction linkage.** The dashboard endpoint and the
   messaging endpoint resolve "which transactions is this client on?" two
   different ways; one of them likely blocks legitimate clients (see §4.2 #9).
4. **Honor the customer boundary.** Harden client-visible message filtering;
   audit PII decryption on every field shown.
5. **Adopt the FSBO/Attorney UI vocabulary.** Standard gutters, `Group > [Page]`
   breadcrumb, tool-vs-dashboard aesthetic, modal-shaped upload, explicit
   action buttons on cards.
6. **No new LLM calls** for rendering.

This is **not** a redesign of the product surface. The four surfaces in §9 stay;
they get a real backend and the now-standard portal chrome.

---

## 2. Lessons inherited from the FSBO + Attorney rebuilds

The prompt asks me to carry forward the feedback from those two builds. Each rule
below is a thing that was flagged on review there; the right column is how it
lands on the Client portal.

| # | Rule (where it came from) | Application to Client |
|---|---|---|
| L1 | **No duplicate sidebar + tabs** (`feedback-attorney-workspace-rules` #1; `project-ve-attorney-matters-sidebar-filters`) | The Client sidebar and the `_shell.tsx` tab bar are a 1:1 duplicate. Collapse to **one** nav. In-page tabs are reserved for *status filters within a single list*, which the Client portal does not have. |
| L2 | **Upload is a modal shaped like the AI Wizard, not a bare on-page dropzone** (`feedback-attorney-workspace-rules` #2) | `ClientDocumentsPage` renders a bare `<UploadIntakeCard/>`. Replace with a modal that collects **transaction + doc_type** before upload. |
| L3 | **Sidebar items navigate to pages, never open a modal** (`feedback-attorney-workspace-rules` #3) | Keep the four sidebar items as page navigations. The upload modal is launched from the topbar CTA / in-page button, not a sidebar entry. |
| L4 | **Breadcrumb icon matches the destination group** (`feedback-attorney-workspace-rules` #4) | Adopt a single Client group crumb (e.g. **"Your Workspace"**) with a consistent icon on all four sub-pages. |
| L5 | **Tool pages ≠ dashboards** (`feedback-tool-vs-dashboard-aesthetic`) | Documents / Milestones / Agent Info are working surfaces → quiet `<section>` cards, not `DashboardCard`/`DashboardKpiCard` chrome. |
| L6 | **Root-cause, doc-grounded fixes — reconcile docs vs as-built** (`feedback-root-cause-over-patches`) | The core of this plan: un-stub the backend, reconcile the §9 spec endpoints vs the as-built `/dashboard/client`, fix the linkage + visibility model — not a restyle over the stub. |
| L7 | **Match the design benchmarks** (`feedback-design-benchmarks`) | No Client design exists from Jake or me, so the visual north star is the **FSBO portal** (now the good sibling) + All Documents / Transactions / the role dashboards. Invent no new card or breadcrumb patterns. |
| L8 | **Alert/nav cards need explicit buttons, not whole-card click** (`feedback-alert-card-clickability`) | The transaction cards are whole-`<button>` click targets. Give each an explicit "View details / Open documents / Ask a question" affordance. |
| L9 | **Cost-effective LLM** (`feedback-cost-effective-llm`) | No LLM call to render any Client surface; reuse cached/derived fields. |
| L10 | **PII is Fernet-encrypted at rest** (`project-ve-pii-fernet-at-rest`) | Every client-visible field (address, agent name/email/phone, message body if encrypted) must pass through `_safe_decrypt`. The dashboard endpoint already does for address/agent; the message thread must too. |
| L11 | **Flag the nav model for product; don't silently flip it** (FSBO plan §3.3 posture) | The sidebar-vs-tabs collapse is a visible product-design choice. Recommend in the Phase A PR and let it be signed off, exactly as the FSBO plan did. |

---

## 3. Authoritative sources

- `FRONTEND_UI_WORKFLOW_LOGIC.md` §9 (Client Portal — the user-journey spec to
  reconcile against the as-built).
- `SYSTEM_DESIGN.md` (Client role, permission matrix, route tree, dashboard API
  namespace).
- `STYLE_GUIDE.md` §15 (shell/gutters) and §16 (cards).
- `FSBO_WORKSPACE_PLAN.md` — the sibling portal; mirror its shell consolidation,
  tool-vs-dashboard split, upload-modal discipline, and boundary-notice pattern.
- `ATTORNEY_WORKSPACE_PLAN.md` — source of the navigation, modal-vs-page, and
  doc-reconciliation discipline.
- `ROLE_DASHBOARDS_DESIGN_UPDATE_PLAN.md` and
  `MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md` (portal shells, customer-scope
  search/notification safety, role-matrix tests).
- The feedback memories enumerated in §2.
- Current frontend: `src/pages/client/*`, `src/layouts/AppLayout.tsx`,
  `src/layouts/dashboardShellConfig.ts`, `src/hooks/useDashboard.ts`,
  `src/components/documents/PortalDocumentList.tsx`,
  `src/components/shared/UploadIntakeCard.tsx`, `src/utils/copy.ts`,
  `src/utils/constants.ts`.
- Current backend: `app/api/v1/dashboard_role.py` (Client block),
  `app/api/v1/client_messages.py`, `app/api/v1/documents.py`,
  `app/schemas/dashboard_role.py`.
- **Visual benchmark:** the FSBO portal (`src/pages/fsbo/*`) once its own
  rebuild lands. There is **no** `VE-ClientDashboard.html` from Jake and no
  `ve-client_*.html` update from me — the Client portal was never designed
  standalone, so do not wait on a comp; mirror FSBO + the benchmark pages (L7).

---

## 4. Current state (verified against the repo)

### 4.1 Shipped / usable — keep

- The four routes are registered under `AppLayout`
  ([App.tsx:297-313](velvet-elves-frontend/src/App.tsx#L297)), role-gated to
  `Client`.
- Shell capability config exists
  ([dashboardShellConfig.ts:116-129](velvet-elves-frontend/src/layouts/dashboardShellConfig.ts#L116)):
  `client` shell variant, `client-owned` search scope, `client` notification
  scope, `ask-agent` primary CTA, AI briefing bar off, global search off — all
  the right customer-safety defaults.
- The centralized boundary notice
  ([copy.ts:10-11](velvet-elves-frontend/src/utils/copy.ts#L10)) renders in the
  shell footer ([_shell.tsx:49](velvet-elves-frontend/src/pages/client/_shell.tsx#L49)).
- `POST /api/v1/client/messages` *attempts* to write a communication-log row and
  notify the primary assignee
  ([client_messages.py:32-92](velvet-elves-backend/app/api/v1/client_messages.py#L32)).
  ⚠️ **Correction:** this does **not** work today — it 403s on the broken linkage
  check (#9) and, even past that, the insert targets non-existent columns (#15),
  so it persists *nothing*. The notify-assignee branch is sound and reusable once
  the row actually writes. (Moved here from "usable" because it isn't.)
- The dashboard endpoint **does** decrypt address / agent name / email / phone
  via `_safe_decrypt`
  ([dashboard_role.py:689,724-728](velvet-elves-backend/app/api/v1/dashboard_role.py#L689)) (L10 satisfied there).
- `PortalDocumentList` already renders the real, role-safe document list and is
  reused on the documents page
  ([ClientDocumentsPage.tsx:49](velvet-elves-frontend/src/pages/client/ClientDocumentsPage.tsx#L49)).

### 4.2 Defects — in scope

**Navigation / shell (visual; same family as the FSBO defects):**

1. **Sidebar and portal tabs are an exact duplicate (L1).** The AppLayout
   `client` group lists *My Transactions / Documents / Milestones / Agent Info*
   ([AppLayout.tsx:387-396](velvet-elves-frontend/src/layouts/AppLayout.tsx#L387));
   `_shell.tsx` renders its own tab bar with the same four destinations
   ([_shell.tsx:6-11,30-46](velvet-elves-frontend/src/pages/client/_shell.tsx#L6)).
   Both render simultaneously (pages are nested under `<AppLayout/>`,
   [App.tsx:216](velvet-elves-frontend/src/App.tsx#L216)). This is the headline fix.
2. **Centered max-width gutters.** `_shell.tsx:23` uses
   `mx-auto w-full max-w-[1200px] … p-6` — the same divergence the FSBO plan
   flagged at 1300px. Should use the project's standard edge padding.
3. **Bespoke shell header anatomy.** `_shell.tsx:25` uses the mono eyebrow
   `Your workspace · {title}` + serif title + a hand-rolled tab bar — the exact
   `FsboPortalShell` anatomy the FSBO rebuild retired. No `Group > [Page]`
   breadcrumb.

**Data layer (stubbed — the root-cause core, L6):**

4. **`documents_summary` is hardcoded to all zeros**
   ([dashboard_role.py:737-739](velvet-elves-backend/app/api/v1/dashboard_role.py#L737)).
   Every count badge the UI shows is fake.
5. **The Documents board bodies are hardcoded placeholders.**
   `ClientDocumentsPage` renders five status columns whose body is literally
   *"No documents in {title}."* for every bucket
   ([ClientDocumentsPage.tsx:33-47](velvet-elves-frontend/src/pages/client/ClientDocumentsPage.tsx#L33)) —
   the same "every column hardcoded to 0" placeholder FSBO had. A *real*
   `PortalDocumentList` is rendered right below it
   ([ClientDocumentsPage.tsx:49](velvet-elves-frontend/src/pages/client/ClientDocumentsPage.tsx#L49)),
   so the page shows two document representations, one of them fake.
6. **`recent_messages=[]` always**
   ([dashboard_role.py:740](velvet-elves-backend/app/api/v1/dashboard_role.py#L740)) —
   the client never sees their own thread or the agent's replies (see #8).
7. **`upcoming_milestones` is just the closing date relabeled "Closing"**
   ([dashboard_role.py:695-700](velvet-elves-backend/app/api/v1/dashboard_role.py#L695)).
   `ClientMilestonesPage` therefore shows a flat label+date list
   ([ClientMilestonesPage.tsx:17-24](velvet-elves-frontend/src/pages/client/ClientMilestonesPage.tsx#L17)),
   but §9.3 specs a timeline with status (completed/current/upcoming),
   plain-English descriptions, and a share-link option — none present.
8. **`agent_card` is thin and possibly wrong-person.** `bio` is always `None`
   and there is no company or photo
   ([dashboard_role.py:730](velvet-elves-backend/app/api/v1/dashboard_role.py#L730)),
   but §9.4 specs a "Learn About Your Agent" bio + company + photo. Worse, the
   card picks `rows[0]` of *any* non-client active assignee
   ([dashboard_role.py:706-714](velvet-elves-backend/app/api/v1/dashboard_role.py#L706))
   without filtering `role_in_transaction == 'agent'`, so a client could see
   their **TC or attorney** under "Your agent."

**Linkage / visibility (correctness + security, L6/L10):**

9. **The client↔transaction linkage is resolved two different ways — and one of
   them queries a column that does not exist.** The dashboard resolves it via
   **`transaction_assignments.user_id`** and its own comment says
   *"transaction_parties is keyed on contact_id, not user_id"*
   ([dashboard_role.py:664-675](velvet-elves-backend/app/api/v1/dashboard_role.py#L664)).
   The messaging endpoint instead gates access via **`transaction_parties.user_id`**
   ([client_messages.py:40-49,103-111](velvet-elves-backend/app/api/v1/client_messages.py#L40)).
   **The comment is correct, and verified:** `transaction_parties` has no
   `user_id` column — its columns are `contact_id` / `party_role` / `full_name`
   / … and it's indexed on `contact_id`
   ([20260305_phase1_schema.sql:179-196](velvet-elves-backend/supabase/migrations/20260305_phase1_schema.sql#L179)),
   with no later migration adding `user_id`. So the message endpoint's
   `.eq("user_id", current_user.id)` filters a non-existent column → PostgREST
   errors → the bare `except` swallows it → **the POST 403s and the GET returns
   `[]` for every client.** This is not "likely"; it is the current behavior.
   The canonical link is already known — `transaction_assignments.user_id` (what
   the working dashboard uses) — so both endpoints must standardize on it.
10. **`GET /api/v1/client/messages` has no client-visibility filter — but the
    flag it would filter on was never persisted, and nothing calls the endpoint
    yet.** The GET returns every `communication_logs` row in channels
    `note`/`email`/`system` for the transaction
    ([client_messages.py:116-126](velvet-elves-backend/app/api/v1/client_messages.py#L116)).
    Two corrections to the original framing:
    - **`is_client_visible` is not a real column.** The POST *tries* to write it
      (and `actor_id`, and `occurred_at`), but none of those three exist on
      `communication_logs` (#15) — so no row is ever tagged, and a
      `.eq("is_client_visible", True)` filter would itself error. The fix is not
      "add the filter."
    - **The leak is latent, not live.** No frontend code calls `GET
      /client/messages` (only the POST is wired,
      [ClientTransactionsPage.tsx:25](velvet-elves-frontend/src/pages/client/ClientTransactionsPage.tsx#L25)),
      and the GET errors on `occurred_at` anyway → `[]`. The boundary risk goes
      *live* the moment Phase D surfaces the thread, so the visibility model must
      be designed **before** that wiring.
    FSBO's `_fsbo_visible_messages` is **not** a drop-in to mirror here: it's a
    one-way model (channel ∈ {email, sms} AND `direction == "outbound"`, subjects
    only) that would hide the client's own `note`/inbound questions. See D6.

**Schema mismatch — messaging writes/reads non-existent columns (root cause; grouped with #9/#10):**

15. **`client_messages.py` writes and reads three columns that aren't on
    `communication_logs`.** The POST insert sets `actor_id`, `occurred_at`, and
    `is_client_visible`
    ([client_messages.py:57-66](velvet-elves-backend/app/api/v1/client_messages.py#L57));
    the GET selects/orders by `occurred_at`
    ([client_messages.py:116-126](velvet-elves-backend/app/api/v1/client_messages.py#L116)).
    But `communication_logs` has **`sender_user_id`** (not `actor_id`),
    **`created_at`** (not `occurred_at`), and **no `is_client_visible`** at all
    ([20260305_phase1_schema.sql:325-358](velvet-elves-backend/supabase/migrations/20260305_phase1_schema.sql#L325));
    no later migration adds any of the three (the only `actor_id`/`occurred_at`
    in the schema belong to `document_priority_events` / `platform_audit`).
    Consequence: even if #9's linkage 403 were fixed, the insert would still fail
    and be swallowed by the bare `except`, so **a client's question is never
    persisted** while the POST still returns `{"status":"queued"}` — a false
    success. This is the root cause #10's "just add a filter" framing skipped:
    there is **no persisted client-visibility concept**, and the write path is
    broken at the column level. Fix is a schema/endpoint reconciliation, not a
    one-line filter (§8.2, D6).

**Functional gaps / broken affordances:**

11. **The "Ask your agent" topbar CTA dead-ends.** It navigates to
    `/client/transactions?ask=1`
    ([AppLayout.tsx:573-574](velvet-elves-frontend/src/layouts/AppLayout.tsx#L573)),
    but `ClientTransactionsPage` never reads `?ask=1`, and the ask box only
    appears after a transaction is selected (`openTxId` is required to send,
    [ClientTransactionsPage.tsx:22,72-94](velvet-elves-frontend/src/pages/client/ClientTransactionsPage.tsx#L22)).
    So the primary CTA lands the user on a list with nothing opened.
12. **No per-transaction Detail surface.** The transaction "expand" is inline
    `setOpenTxId` state showing only address + closing date + an ask box
    ([ClientTransactionsPage.tsx:72-96](velvet-elves-frontend/src/pages/client/ClientTransactionsPage.tsx#L72)).
    §9.1 allows an inline expanded view, but it should carry key dates, next
    milestone, recent updates, and a per-transaction documents/milestones link.
13. **`/client/documents` is overloaded for the Vendor role.** It returns
    `<VendorDocumentPortalPage/>` when `user.role === 'Vendor'`
    ([ClientDocumentsPage.tsx:19-22](velvet-elves-frontend/src/pages/client/ClientDocumentsPage.tsx#L19)),
    even though Vendor already has its own `/vendor` portal route
    ([App.tsx:314-316](velvet-elves-frontend/src/App.tsx#L314)). A smell to
    untangle so the Client page is single-purpose.

**Doc drift (L6):**

14. §9 specs per-surface endpoints (`GET /api/v1/client/transactions`,
    `/client/documents`) that **do not exist**; everything is funneled through
    `/api/v1/dashboard/client`. The namespace decision must be made and the doc
    reconciled, exactly as FSBO did for `/api/v1/dashboard/fsbo/...`.

---

## 5. Functional inventory

| Capability | Status today | Plan |
|---|---|---|
| Transaction list | Live (from `/dashboard/client`) | Keep; restyle cards with explicit buttons (L8); decrypt-safe |
| Transaction expanded view | Thin inline expand | Enrich: key dates, next milestone, recent updates, docs/milestones links, thread |
| "Ask a question" | **Broken**: POST 403s on bad linkage (#9) and inserts dead columns (#15) → never persists; CTA dead-ends | Fix linkage (#9) + write path/columns (#15), choose visibility model (D6), wire `?ask=1`, show the thread (GET) |
| Documents board (counts) | **Hardcoded 0** | Real `documents_summary` projection, or drop the board and lead with the real list |
| Documents list | Live (`PortalDocumentList`) | Keep; this becomes the single doc representation |
| Document upload | Bare on-page dropzone | Modal collecting transaction + doc_type (L2) |
| Flag-for-deletion | Via `PortalDocumentList` | Preserve through restyle |
| Milestones | Closing-date-only flat list | Real timeline: status + plain-English + share link (§9.3) |
| Agent Info | bio/company/photo missing; wrong-person risk | Real agent projection; filter to the Agent; add bio/company/avatar |
| Boundary notice | Live in footer | Keep on every surface |
| Sidebar vs tabs | **Duplicated** | Collapse to one nav (L1, decision in Phase A) |
| Shell gutters/header | Centered max-w + bespoke eyebrow | Standard gutters + `Group > [Page]` breadcrumb (L4) |

---

## 6. Page tree (current + intended) + decision register

```text
/client/transactions          My Transactions (landing) — list + enriched expand   (live, thin)
/client/documents             Documents list + upload modal                        (live, board is fake)
/client/milestones            Milestones timeline                                  (live, closing-only)
/client/agent                 Agent Info                                           (live, thin)
```

Not routes (intentional):
- **Upload** — a modal launched from the topbar CTA / a Documents-page button,
  mirroring the AI-Wizard stepper shape (L2/L3). No `/client/upload` page.
- **Ask your agent** — inline on the transaction expand + the topbar CTA; no
  dedicated chat page.

**Decision register (flag in the Phase A PR; do not flip silently — L11):**

- **D1 — One navigation system.** *Recommended: sidebar-only.* Drop the
  `_shell.tsx` tab bar; keep the AppLayout `client` group as the single nav.
  Rationale: the four destinations are top-level sections, not status filters of
  one list, so they belong in the sidebar — matching the settled Attorney model
  where in-page tabs exist *only* for status filtering. §9.1 itself describes a
  *sidebar* (My Transactions | Documents | Milestones | Agent Info) under a
  "simplified Client shell" with no tab bar, so sidebar-only is also the
  spec-aligned choice. Alternative: tabs-only (drop the sidebar group). Either
  way the duplicate must go.
- **D2 — Transaction Detail: inline expand vs route.** *Recommended: enrich the
  inline expand first* (it's §9.1-compliant and avoids scope creep), and only
  promote to `/client/transactions/:id` if the expand outgrows a card. Mirrors
  the FSBO time-box discipline.
- **D3 — API namespace.** *Recommended: keep `/api/v1/dashboard/client`* as the
  canonical read namespace (consistent with FSBO's `/api/v1/dashboard/fsbo/...`
  decision) and reconcile §9's per-surface endpoint language to match — rather
  than build new `/api/v1/client/transactions` endpoints. Messaging stays under
  `/api/v1/client/messages`.
- **D4 — Documents board.** *Recommended: replace the five fake status columns
  with a single real list* (`PortalDocumentList`) plus a slim real status
  summary, rather than keep a board that duplicates the list. Decide whether the
  status summary is worth a real projection or should be cut for MVP.
- **D5 — Vendor hijack.** Remove the Vendor branch from `ClientDocumentsPage`
  and let `/vendor` own the vendor portal; confirm no live link routes vendors
  to `/client/documents` before deleting.
- **D6 — Messaging visibility model + thread direction.** *Recommended: add a
  real `is_client_visible` column and build a two-way thread (Option A in §8.2).*
  The Client "Ask a question" is a two-way Q&A (§9.1) — a different interaction
  from FSBO's one-way "messages from your coordinator" list — so do **not** reuse
  FSBO's outbound-email predicate. This decision drives whether the rebuild ships
  a migration (it does, under Option A) and how agent replies are surfaced. Note
  `/api/v1/client/messages` is role-gated for **both** Client and FSBO but only
  the Client UI calls it today; keep that in mind if the model changes. Flag in
  the Phase B PR.

---

## 7. Per-surface plan

### 7.1 Shell, nav, gutters, breadcrumb (Phase A — lands first)
- Implement **D1**: collapse to one nav. If sidebar-only, strip the tab bar from
  `_shell.tsx` and keep the footer boundary notice + a standard page header.
- Replace `max-w-[1200px] mx-auto p-6` with the project's standard edge padding.
- Replace the mono eyebrow with the `Group > [Page]` breadcrumb pattern and a
  single consistent Client group icon (L4), mirroring the FSBO header.
- Keep `_shell.tsx` as a thin layout (header + boundary footer) reused by all
  four pages, or fold it into the page header — one location, consistently.

### 7.2 My Transactions `/client/transactions` (Phase D)
- Restyle transaction cards as **non-interactive containers with explicit
  buttons** ("View details", "Open documents", "Ask a question") per L8 — not a
  whole-card `<button>`.
- Enrich the expanded view (D2): key dates, next milestone, recent updates, and
  links to `/client/documents?transaction=:id` and
  `/client/milestones?transaction=:id` (the `?transaction=` filter is already in
  §9.1's contract).
- Wire `?ask=1` so the topbar CTA opens the ask box (and, if exactly one
  transaction exists, pre-selects it) — fixing defect #11.
- Render the **message thread** from `GET /api/v1/client/messages` so "Ask a
  question" is a conversation, not a void (depends on the §8 backend fix).
- Tool aesthetic (L5) — quiet sections, not `DashboardCard`.

### 7.3 Documents `/client/documents` (Phase C)
- Implement **D4/D5**: delete the hardcoded board + the Vendor branch; lead with
  the real `PortalDocumentList`. If the status summary stays, drive it from the
  real `documents_summary` projection (§8).
- Replace the bare `<UploadIntakeCard/>` with an **upload modal** (L2) that
  collects **transaction + doc_type** (+ optional label) before submitting via
  `useUploadDocument({ transactionId, docType, docLabel })`. Mirror the FSBO
  upload-modal resolution and the AI-Wizard stepper shape.
- Preserve `PortalDocumentList`'s flag-for-deletion wiring.

### 7.4 Milestones `/client/milestones` (Phase D)
- Render a real **timeline** with status (completed/current/upcoming),
  plain-English descriptions, and key dates from the new milestone projection
  (§8) — replacing the closing-date-only list.
- Add the **share-milestone** option (§9.3) reusing the existing share
  infrastructure if it's client-eligible; otherwise flag as a separate decision
  rather than building a parallel share system.
- Tool aesthetic (L5).

### 7.5 Agent Info `/client/agent` (Phase D)
- Render the real agent projection (§8): name, **company**, **bio**, photo/avatar,
  phone, email, one-click call/email (§9.4).
- Ensure the projection resolves the **Agent specifically** (not the first
  non-client assignee) — defect #8.

### 7.6 Doc reconciliation (Phase E)
- Reconcile `FRONTEND_UI_WORKFLOW_LOGIC.md` §9 to the as-built: the canonical
  read namespace (D3), upload-as-modal, one navigation system (D1), the real
  milestone/agent/documents projections, and the message-thread surface.
- Update any `SYSTEM_DESIGN.md` Client route/endpoint stragglers.

---

## 8. Backend touchpoints

All on `app/api/v1/dashboard_role.py` (Client block) and
`app/api/v1/client_messages.py` unless noted. No new LLM calls (L9).

1. **One canonical client↔transaction resolver (defect #9).** Extract a single
   helper (e.g. `list_client_transaction_ids(supabase, user)`) and use it in
   both the dashboard endpoint and the message access checks. The true link is
   **`transaction_assignments.user_id`** — `transaction_parties` has no `user_id`
   column, so the message endpoint's current check queries a non-existent column
   and 403s every client. Standardize on `transaction_assignments`; this is a
   *known* answer, not a "decide between two tables" question. The only thing
   left to **verify** is that Clients reliably get an `is_active` assignments row
   at invite/onboarding — confirm against the onboarding code before shipping.
   On its own this un-403s the endpoint, but the thread still won't function
   until #15's column mismatch is fixed (touchpoint #8).
2. **Decide the client-visibility model, then harden `GET /client/messages`
   (defects #10 + #15; D6).** You cannot just `.eq("is_client_visible", True)` —
   that column doesn't exist. Pick **one** canonical model and implement it end
   to end:
   - **Option A (recommended) — add a real `is_client_visible` column** to
     `communication_logs` via migration; fix the POST to write valid columns
     (`sender_user_id`/`created_at`; drop `occurred_at`/`actor_id`); and tag
     `is_client_visible=True` on *both* the client's questions **and** the
     agent's replies. The GET then filters on it. This is the only option that
     supports the two-way "Ask a question" thread §9.1 describes.
   - **Option B — reuse FSBO's predicate** (`is_portal_visible_message`: channel
     ∈ {email, sms} AND `direction == "outbound"`). But this **excludes**
     `note`-channel and all inbound rows, so it would hide the client's own
     questions and any `note`-based reply. FSBO is a *one-way* "messages from
     your coordinator" list (subjects, no bodies), not a two-way Q&A — so it is
     not a drop-in here.
   Either way: add a pytest that an internal / non-visible row is excluded; and
   verify whether `communication_logs.body` is Fernet-encrypted — if so
   `_safe_decrypt` before returning (L10).
3. **Real `documents_summary` (defect #4/#5).** Compute the Missing / In progress
   / Uploaded / Verified / Complete counts for the client's transactions —
   reuse the same document-status projection FSBO's documents board uses, scoped
   to client-visible documents. If a real projection is out of scope for MVP,
   **remove the board** rather than ship zeros (D4).
4. **Real milestone projection (defect #7).** Return milestones with status
   (completed/current/upcoming), a plain-English label, and date — derived from
   the same milestone/task source other roles use, filtered to client-safe
   items (no task internals). Replace the closing-date-only stub.
5. **Real agent projection (defect #8).** Filter to
   `role_in_transaction == 'agent'` (fallback to TC only if no agent), and
   populate `company` + `bio` + avatar from the user/profile record. Decrypt
   all PII (L10).
6. **`recent_messages` (defect #6).** Either populate it from the hardened
   client-visible thread, or drop it from `ClientDashboardResponse` and read the
   thread directly via `GET /client/messages` on the transactions page. Pick one
   to avoid a second stub.
7. **Schema sync.** Update `ClientDashboardResponse`
   ([useDashboard.ts:951-959](velvet-elves-frontend/src/hooks/useDashboard.ts#L951))
   and `app/schemas/dashboard_role.py` for any added fields (agent `company`,
   milestone `status`). Keep the front/back shapes in lockstep.
8. **Fix the message write path + define how a reply becomes client-visible
   (defects #15 + #6).** Correct the POST to insert real columns
   (`sender_user_id`, `created_at`; drop `actor_id`/`occurred_at`) so questions
   actually persist. Then decide how an **agent reply** is tagged client-visible:
   there is currently **no** code path that marks any reply visible to the
   client, so "Ask a question" cannot become the two-way conversation the UI
   implies. Either route agent replies through a comms action that sets the
   visibility flag, or explicitly scope the thread and say so — but don't ship a
   thread UI (Phase D) over a one-directional write path.

No new endpoints if D3 holds (keep `/api/v1/dashboard/client` +
`/api/v1/client/messages`). **Correction:** this is *not* "field additions
only" — under D6 Option A the rebuild includes a `communication_logs` migration
(add `is_client_visible`) plus the POST column fix.

---

## 9. Execution order (~5.0 dev days + QA)

### Phase A — Shell + navigation consolidation (~0.75 day)
- Implement D1 (one nav), standard gutters, `Group > [Page]` breadcrumb + Client
  group icon. PR description asks product to confirm sidebar-only vs tabs-only
  (L11).
- **Exit:** no duplicate nav; no `max-w-[1200px]` wrapper; breadcrumbs consistent
  across the four pages. `tsc`/eslint clean; render test asserts a single nav.

### Phase B — Backend truthfulness + linkage/visibility/messaging (~2.0 days)
- One canonical linkage resolver (#1); decide + implement the visibility model,
  incl. the `is_client_visible` migration if D6 = Option A (#2/#15); fix the
  message write path + reply-visibility (#8/#15); real `documents_summary` (#3);
  real milestone projection (#4); real agent projection (#5); resolve
  `recent_messages` (#6); schema sync (#7).
- **Exit:** `pytest -k "client"` covers: dashboard scoped to the current client;
  linkage resolver parity between dashboard and messages; a posted question
  **persists and round-trips**; an internal / non-visible row is excluded from
  the thread; documents/milestones/agent projections return real data;
  cross-client 403 on messages.

### Phase C — Documents surface (~0.75 day)
- Delete the fake board + Vendor branch (D4/D5); lead with `PortalDocumentList`;
  upload modal collecting transaction + doc_type (L2), preserving
  flag-for-deletion.
- **Exit:** no hardcoded "No documents in …" body anywhere; upload modal
  requires transaction + doc_type; flag-for-deletion still visible.

### Phase D — Transactions, Milestones, Agent surfaces (~1.0 day)
- Transactions: explicit card buttons (L8), enriched expand (D2), `?ask=1`
  wiring, message thread.
- Milestones: real timeline + plain-English + share option.
- Agent Info: bio/company/photo + correct-person.
- **Exit:** topbar "Ask your agent" opens a working ask box and shows the thread;
  milestones show status; agent card shows the Agent with bio/company.

### Phase E — Doc reconciliation + manual QA (~0.5 day)
- Reconcile §9 (and `SYSTEM_DESIGN.md`) to the as-built (D1/D3, upload-as-modal,
  real projections). Manual QA per §10. Screenshots in the PR.

**Total: ~5.0 dev days + QA.**

---

## 10. Verification checklist

**Frontend**
- `npx tsc --noEmit -p tsconfig.app.json` — clean.
- `npx eslint <changed files>` — clean.
- Render tests: exactly one navigation system (no `_shell.tsx` tab bar if D1 =
  sidebar-only); no `max-w-[1200px]`; no hardcoded "No documents in …" body;
  upload modal requires transaction + doc_type; transaction cards expose
  explicit buttons (not a whole-card `<button>`); `?ask=1` opens the ask box.

**Backend**
- `venv/Scripts/python.exe -m pytest app/tests -k "client"` — passes.
- Covers: client dashboard scoped to the current user; **linkage parity** between
  the dashboard and the message endpoints; a posted question **persists and
  round-trips** (guards against the #15 column regression); `GET /client/messages`
  excludes internal / non-client-visible rows per the chosen D6 model;
  cross-client 403 on POST/GET messages; real documents/milestones/agent
  projections; PII decrypted (no `gAAAAAB…` in any response).

**Manual QA, logged in as a Client**
- One navigation system — no sidebar-and-tabs duplication.
- Standard gutters; `Group > [Page]` breadcrumb with the Client icon.
- "Ask your agent" (topbar) opens a working ask box; the sent question and any
  agent reply appear in the thread.
- Documents page shows real document statuses (no fake zero board); upload is a
  modal tagging transaction + doc_type; flag-for-deletion works; no vendor UI.
- Milestones show a timeline with status + plain-English + key dates + share
  option.
- Agent Info shows the **Agent** (not the TC/attorney) with name, company, bio,
  photo, call/email.
- Boundary notice on every surface. No internal tasks, notes, AI drafts, audit
  chatter, version/milestone strings, or other parties' data anywhere.

---

## 11. Risks & open decisions

1. **Linkage is known; only onboarding attachment needs confirming (Phase B
   #1).** The link is `transaction_assignments.user_id` (the dashboard already
   uses it; `transaction_parties` has no `user_id` column). Standardize the
   resolver on it — no "union the two tables" guessing. The one verification left
   is that Clients reliably receive an `is_active` assignments row at
   invite/onboarding; confirm against the onboarding code, then write the shared
   helper.
2. **Documents `documents_summary` cost.** A real five-bucket projection per
   client may be non-trivial; if it slips, ship the real **list** (D4) and cut
   the status summary for MVP rather than keep zeros.
3. **Share-milestone for clients (§9.3).** Reuse the existing share system only
   if it's client-eligible; if it's FSBO-scoped today, treat client sharing as a
   separate, explicitly-decided slice — don't fork a parallel share path under
   the rebuild banner.
4. **Vendor hijack removal (D5).** Confirm nothing links a Vendor to
   `/client/documents` before deleting the branch, so vendors aren't stranded.
5. **Nav model sign-off (D1).** Surface in the Phase A PR; if product wants
   tabs-only instead of sidebar-only, swap in the same PR — don't ship both.
6. **No Client design comp.** Because there's no Jake/Jan Client design, the bar
   is "matches the FSBO portal + benchmark pages" (L7). If product later wants a
   distinct Client visual language, that's a separate design pass, not this
   rebuild.
7. **Messaging is broken at the column level, not just unstyled (Phase B
   #15/#8).** "Ask a question" writes to non-existent columns and silently drops
   the message, and there is no reply-visibility path — so this is real backend
   work (migration + write-path fix + reply model), not a projection tweak.
   Budget Phase B accordingly, and do not surface the thread UI (Phase D) until a
   test round-trips a posted question **and** a visible reply.

---

## 12. Cross-references

- `FSBO_WORKSPACE_PLAN.md` — sibling portal; shell consolidation, tool-vs-
  dashboard split, upload-modal discipline, boundary-notice pattern, namespace
  decision precedent.
- `ATTORNEY_WORKSPACE_PLAN.md` — navigation, modal-vs-page, and doc-
  reconciliation discipline.
- `FRONTEND_UI_WORKFLOW_LOGIC.md` §9 — the Client user-journey spec to reconcile
  (Phase E).
- `SYSTEM_DESIGN.md` — Client role, permission matrix, route tree, dashboard API
  namespace.
- `STYLE_GUIDE.md` §15–§16 — shell, gutters, cards.
- Feedback memories: `feedback-attorney-workspace-rules`,
  `project-ve-attorney-matters-sidebar-filters`,
  `feedback-tool-vs-dashboard-aesthetic`, `feedback-root-cause-over-patches`,
  `feedback-design-benchmarks`, `feedback-alert-card-clickability`,
  `feedback-cost-effective-llm`, `project-ve-pii-fernet-at-rest`.

---

*Plan drafted: 2026-05-23 (rev 1), grounded in the current repo state and the
FSBO/Attorney rebuild lessons.*
