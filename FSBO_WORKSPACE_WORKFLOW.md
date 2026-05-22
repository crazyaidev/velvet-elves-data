# FSBO Workspace — Role & Complete Workflow

*As-built reference. Last reconciled against the repo: 2026-05-22.*

This document explains what the FSBO (For-Sale-By-Owner) workspace is, the role
it plays in Velvet Elves, and the complete end-to-end workflow a customer moves
through. It describes the system **as built**, not as originally mocked — where
the two differ, the as-built is authoritative and the difference is called out.

---

## 1. What the FSBO workspace is

Velvet Elves is an AI-assisted real-estate transaction-coordination platform.
Most roles (Agent, Transaction Coordinator, Team Lead, Admin, Attorney) are
**internal** operators who run deals on behalf of clients. The FSBO workspace is
the one surface built for an **external, unrepresented seller** — a homeowner
selling their own property without a listing agent.

The FSBO customer is not a Velvet Elves operator. They do not see the internal
sidebar, the task queue, AI briefings, internal notes, other parties' data, or
any workflow machinery. They see a calm, plain-English portal that answers three
questions:

1. **What do I need to do next, and why does it matter?**
2. **Which documents are missing, in review, or done?**
3. **Where does my sale stand, and what's coming up?**

The guiding principle is *calm external portal*: show the next action, surface
what's missing or under review, explain milestones in plain English, and never
leak internal workflow data.

### Boundary notice (always present)

Every FSBO surface carries a boundary notice:

> "Velvet Elves coordinates your workflow but does not act as your agent or
> provide legal advice."

This is a legal/relationship guardrail. It renders in the shell footer on every
tool sub-page and in the coordinator/support card on the Overview. The string is
defined once on the backend (`FSBO_BOUNDARY_NOTICE`) and once on the frontend
(`@/utils/copy` → `FSBO_BOUNDARY_NOTICE`); the backend value flows through the
API and the frontend constant is only a loading-state fallback.

---

## 2. Who the customer is, and how their data is isolated

- **Role:** `ForSaleByOwner` (enum `UserRole.FOR_SALE_BY_OWNER`).
- **Ownership model:** an FSBO customer owns the transactions they created
  (`transactions.created_by == user.id`) within their tenant. There is no
  agent/assignment indirection for the seller's own access.
- **Authorization:** every FSBO read is scoped to the customer's own
  properties. The single guard is
  `fsbo_workspace.assert_fsbo_transaction_access(user, transaction_id, supabase)`,
  which raises **404 (not 403)** on any cross-owner or cross-tenant miss — the
  portal never even confirms that another seller's property exists.
- **PII at rest:** address, city, state, full_name, company, phone, email are
  Fernet-encrypted in the database. Anything shown to the customer (or fed to an
  LLM) must be decrypted via `_safe_decrypt` first. `_safe_decrypt` returns `""`
  on failure — it never leaks ciphertext.
- **Message visibility:** coordinator messages are filtered through
  `is_portal_visible_message` — only real outbound coordinator→customer messages
  on external channels (email/sms) are shown. Internal notes, AI-draft
  internals, document-action events, system events, and inbound replies are
  never surfaced.

---

## 3. The shell (navigation chrome)

The FSBO shell variant (`shellVariant: 'fsbo'`, see
`layouts/dashboardShellConfig.ts`) is deliberately leaner than the internal
shell.

- **Sidebar:** a standalone "Dashboard" link at the top, then a single
  **Workspace** group — *My Properties*, *Documents*, *Milestones & Messages* —
  then Settings. There is **no Help group**. (Earlier drafts had Ask-AI,
  Notifications, and Sharing as sidebar entries; those were removed.)
- **Sidebar footer CTA:** "Share milestones" — opens the share-management modal
  (see §5.6). FSBO is the one role whose primary CTA lives in the sidebar
  footer, not the topbar.
- **Topbar:**
  - Brand lockup.
  - **Portfolio status chip** (center) — an aggregate health pill computed
    client-side from the overview: red "Closing in N days" when the nearest
    closing is ≤ 7 days, amber "Action needed · N docs missing" when any docs are
    missing, else green "On track". Clicking it navigates to `/fsbo`.
  - Notification bell (notifications scope = `fsbo`).
  - User chip.
- **Persistent action banner** — a second row directly below the topbar that
  surfaces the single top critical step (`critical_next_steps[0]`) on **every**
  FSBO page, not just the Overview. It has a primary "Open"/"Upload" button
  (chosen by the step's `action_kind`) and a `×` dismiss. Dismissal is
  session-scoped (`sessionStorage`, keyed on `transaction_id + title`), so a new,
  different top step will re-surface. Implemented in `AppLayout` and gated on the
  FSBO shell variant.
- **No portal tabs.** The sidebar is the navigation; a tab bar would duplicate
  it. (Two competing tab implementations were consolidated away.)

Tool sub-pages use `FsboPortalShell` — a canonical header with a
`Workspace › [Page]` breadcrumb (Property Detail extends it to
`Workspace › My Properties › {Address}`), standard edge gutters, and the
boundary-notice footer. The Overview is a *dashboard* and omits the page-title
row.

---

## 4. Backend API surface

All FSBO data lives under the dashboard namespace `/api/v1/dashboard/fsbo/...`.
There are no `/api/v1/fsbo/...` endpoints.

| Method & path | Purpose |
|---|---|
| `GET /api/v1/dashboard/fsbo/overview` | Landing payload — properties, ranked next steps, upcoming deadlines, closing-timeline rollup, KPIs, recent milestones, AI guidance, support contact, boundary notice. |
| `GET /api/v1/dashboard/fsbo/properties/{id}` | Ownership-checked deep view — milestone timeline, key dates, document board + list, share links, messages (with `seen`), **contacts ("People involved")**, AI guidance, support contact. |
| `GET /api/v1/dashboard/fsbo/documents` | Per-property document board across all owned properties + totals. |
| `GET /api/v1/dashboard/fsbo/milestones` | Timeline + key dates per property + portal-visible coordinator messages (with `seen`). |
| `POST /api/v1/dashboard/fsbo/messages/seen` | Mark a batch of coordinator messages as seen (idempotent, cross-owner-filtered). |
| `GET /api/v1/dashboard/fsbo/share-link?transaction_id=` | List the customer's share links. |
| `POST /api/v1/dashboard/fsbo/share-link` | Create a share link (returns the raw token exactly once). |
| `DELETE /api/v1/dashboard/fsbo/share-link/{id}` | Revoke a share link. |
| `GET /api/v1/milestones/shared/{token}` | **Public, unauthenticated** read-only milestone viewer. |
| `POST /api/v1/milestones/shared/{token}/viewed` | Record a public view (drives the view count + viewer-open signal). |

Document upload reuses the shared documents endpoint via
`useUploadDocument({ transactionId, docType, docLabel })`; there is no
FSBO-specific upload route.

All projections are computed in `app/services/fsbo_workspace.py`. No LLM call is
made at render time — `ai_guidance.next_decision` and milestone explanations are
**deterministic** text derived from real model state.

---

## 5. Page-by-page workflow

### 5.1 Overview — `/fsbo`

The dashboard landing surface. Reads `useFsboOverview()`. Composition top-to-bottom:

1. **KPI strip (4 tiles):** My Properties, Missing Documents, Share Links Live,
   Days to Closing. Each tile is clickable and routes to the relevant surface.
2. **Closing-timeline rollup strip** (under the KPIs): for the nearest-closing
   property, shows the address plus `Stage · {current_stage_label}` and
   `File · {file_status_label}` chips. Derived server-side in
   `closing_timeline_summary`.
3. **Hero "Next step" card** (brand tone): the single top item from
   `critical_next_steps[0]` — title, plain-English body, "why it matters",
   deadline, and a primary action that is either "Upload missing documents" or
   "Open this property" (chosen by the data), plus a secondary "Share
   milestones".
4. **"Upcoming deadlines" card:** up to 5 rows from `upcoming_deadlines[]` (next
   ~21 days, sourced from key dates + task due dates). Each row is click-to-
   expand and reveals a plain-English **consequence** of missing that date.
   Hidden when empty.
5. **"Stay on track" card:** the secondary ranked steps
   (`critical_next_steps[1..5]`) as rows, each with its own inline action
   (Upload / Open property) driven by the step's `action_kind`. Hidden when only
   one step exists.
6. **Property portfolio strip:** `FsboPropertyTile` in *select* mode — clicking
   a tile focuses it (re-anchors the hero/next-step), it does **not** navigate.
7. **Rail:** coordinator/support card (with boundary notice), plain-English
   guide card (`ai_guidance.next_decision` + glossary chips, link into Ask AI),
   and the demoted Concierge upsell strip (its CTA opens Ask AI with a
   concierge-themed prompt — there is no `/settings#concierge` route).

Empty state: a welcome card prompting the customer to wait for their coordinator
to add the first property.

### 5.2 Property portfolio — `/fsbo/properties`

A tool page listing every owned property as `FsboPropertyTile` in *open* mode
(clicking navigates to detail). A status filter (All / Listing prep / Under
contract) narrows the list. Reads `useFsboOverview()` and filters client-side.

### 5.3 Property Detail — `/fsbo/properties/:id`

The deep view for one property. Reads its **own** ownership-checked endpoint
(`useFsboProperty(id)`), so cross-owner access returns 404. Layout:

- **Summary tiles:** Days to closing, Documents needed, Share links.
- **Milestone timeline:** done / active / upcoming markers with plain-English
  explanations, derived from tasks (falling back to key dates so an active
  property is never blank).
- **Key dates** list.
- **Documents** section: the 5-column board summary + a flat list for this
  property; flag-for-deletion is preserved.
- **Rail:**
  - **AI guidance** card (cached deterministic text).
  - **Share links** for this property + a "Manage" link that opens the share
    modal pre-scoped to this property.
  - **Messages** from the coordinator (unread dot for `seen === false`).
  - **People involved** — the buyer, buyer's agent, title company, attorney,
    etc., sourced from `transaction_parties` with decrypted PII. Each contact
    shows a role-coloured initials avatar, name/company, role label, and inline
    Call / Email buttons. Empty contacts (no name/email/phone/company) are
    dropped server-side.
  - **Support** card + boundary notice (the notice renders once, in the shell
    footer).

On mount, the page fires `POST /messages/seen` for any unseen visible messages.

### 5.4 Documents — `/fsbo/documents`

The document status board across all properties. Reads `useFsboDocuments()`.

- **Totals row:** five columns — Missing, In progress, Uploaded, Verified,
  Complete.
- **Per-property boards:** each property's board with the same five columns and
  a "Still needed: …" strip listing missing required doc types.
- **Flat list:** `PortalDocumentList`, which preserves the flag-for-deletion UX.
- **Upload:** the header "Upload document" button opens `FsboUploadModal` — a
  modal requiring **property + doc_type + file** (label optional). It supports
  click-to-browse and drag-and-drop. The required doc_type discipline is what
  keeps the board's Missing/In-Progress mapping accurate; a silent default to
  the first property is explicitly prevented.

### 5.5 Milestones & Messages — `/fsbo/milestones`

Reads `useFsboMilestones()`. Per-property milestone timelines (same tile pattern
as Property Detail) with a key-dates chip strip, plus a rail panel of
coordinator messages (unread dot for `seen === false`). Marks messages seen on
mount.

### 5.6 Sharing — modal, not a page

There is no `/fsbo/share` route. Share-link management is the global
`FsboShareManagementModal`, mounted once inside `FsboShareProvider` and opened
via `useFsboShare().open()` from:

- the sidebar-footer "Share milestones" CTA,
- the Overview "Share links live" KPI tile,
- the Property Detail "Manage" rail link (which seeds `defaultPropertyId`).

The modal lists active links, supports revoke, and opens a nested
`ShareMilestoneModal` for creation (recipient + expiry + one-time raw-token
reveal). Frontend route attempts to `/sharing` by an FSBO user are redirected
back to `/fsbo`.

### 5.7 Public milestone viewer — `/milestones/:shareToken`

The destination of a share link — a public, **unauthenticated**, read-only page
showing the milestone timeline and key dates only. Shared viewers cannot edit
tasks, delete documents, see contacts, or view any internal workflow. Opening it
records a view (`POST /milestones/shared/{token}/viewed`), incrementing the
owner's view count.

### 5.8 Ask AI / Notifications

- **Ask Velvet Elves AI** is the floating `FloatingAskAi` button on every FSBO
  page (no `/fsbo/ask-ai` route). It opens the shared AI chat panel scoped to the
  customer. The AI may explain steps, documents, and timelines in plain English;
  it must not give legal advice, act as the customer's agent, or make workflow
  decisions.
- **Notifications** live in the topbar bell (no sidebar entry, no page).

---

## 6. The transaction lifecycle (what the customer experiences)

An FSBO property carries an `fsbo_state`:

- **`listing_prep`** — the seller is still assembling the listing. Required docs
  for this state: seller's disclosure, lead-paint disclosure. The portal shows
  prep-oriented milestones and doesn't nag about closing-only documents.
- **`under_contract`** — an offer is accepted and the deal is moving to closing.
  Required docs: purchase agreement, closing disclosure, settlement statement,
  deed. The timeline shows transaction milestones (Offer accepted → Earnest
  money → Inspection → Repair agreement → Cleared to close → Closing day).

The "Missing documents" count is **absence-of-requirement**, computed per state —
a listing-prep seller is never told their deed is missing months early.

### Document board states (per document row)

`classify_document_board_state` maps each document to a column:

- **Missing** — a *required* doc_type with no current document (computed at the
  property level, not a row state).
- **In progress** — still processing, or a reviewer asked for follow-up.
- **Uploaded** — processed, awaiting first review.
- **Verified** — content approved, but a signature is still in flight.
- **Complete** — content approved and no signature obligation remains.

The Verified-vs-Complete split is the explicit "signature still out" rule: a doc
can be content-approved yet not Complete until its e-signature envelope is no
longer pending.

### Next-step derivation (deterministic, ranked)

`derive_next_steps` produces real, ranked actions — never hardcoded "plausible"
guidance. Ranking priority: (1) missing required documents, (2) an active/overdue
task, (3) closing within 7 days with nothing else flagged. Each step carries an
`action_kind` (`upload_documents` | `open_property`) so the UI renders the right
inline action without parsing strings.

### Support contact resolution (per-tenant)

`resolve_support_contact` resolves the coordinator the seller sees, in order:
(1) the active TC/Admin assigned to the transaction via `transaction_assignments`,
(2) the tenant's first Admin/TeamLead/TC, (3) the default constant. Earlier this
was a single hardcoded contact for every tenant; it is now per-tenant.

### Unread messages

`communication_log_views (log_id, user_id, seen_at)` tracks which logs a user has
seen. Property Detail and Milestones project a `seen` flag per message and render
an orange dot for unseen ones; on mount they POST the visible log_ids to
`/messages/seen` (idempotent, cross-owner-filtered) so the dot clears on the next
refetch.

---

## 7. What is intentionally *not* in the FSBO workspace

- No internal sidebar, task queue, AI briefing bar, or communications panel.
- No internal notes, audit chatter, or other parties' private data.
- No portal tabs (sidebar is the nav).
- No `/fsbo/share` or `/fsbo/ask-ai` pages (modal + floating widget instead).
- No `/settings#concierge` route (the Concierge CTA opens Ask AI).

## 8. Source-of-truth note

Jake's mockup (`VE-FSBODashboard.html`) is the visual-intent reference for the
transaction-management surface, but it is **not** exhaustive. Two notable
capabilities are milestone-scope deliverables (`milestones.txt`) that are absent
from his mockup and intentionally kept:

- **Milestone sharing** (read-only links with expiry + viewer-open
  notifications, the "Share milestones" CTA, the "share links live" KPI).
- The **portfolio status chip** and **persistent action banner** are as-built
  refinements layered on top of the mockup's intent.

Where Jake's design and `milestones.txt` disagree, `milestones.txt` governs the
scope; Jake's design governs the look and feel.

---

## 9. Key files

**Backend**
- `app/services/fsbo_workspace.py` — all projections, ownership guard,
  next-step/deadline derivation, support-contact resolution, message filtering,
  seen-tracking.
- `app/api/v1/dashboard_role.py` — FSBO endpoints (overview / property /
  documents / milestones / messages-seen).
- `app/api/v1/milestones.py` — share-link CRUD + public viewer.
- `app/services/share_link_service.py` — share-link auth (cross-owner denial).
- `app/schemas/dashboard_role.py` — response models.

**Frontend**
- `src/pages/fsbo/` — `FsboOverviewPage`, `FsboPropertiesPage`,
  `FsboPropertyDetailPage`, `FsboDocumentsPage`, `FsboMilestonesPage`, `_shell`.
- `src/components/fsbo/` — `FsboPropertyTile`, `FsboUploadModal`,
  `FsboShareManagementModal`, `fsboStatus`.
- `src/contexts/FsboShareContext.tsx` — global share-modal provider.
- `src/hooks/useDashboard.ts` — `useFsboOverview`, `useFsboProperty`,
  `useFsboDocuments`, `useFsboMilestones`, `useMarkFsboMessagesSeen` + types.
- `src/layouts/AppLayout.tsx` — status chip + persistent banner.
- `src/pages/public/MilestoneViewerPage.tsx` — public viewer.
