# FSBO Workspace — Role & Complete Workflow

*As-built reference. Last reconciled against the repo: 2026-08-20 (rev 3, seller bell + Ask Aime).*

This document describes the For-Sale-By-Owner workspace **as shipped**. Chrome
is `AppLayout` with `shellVariant === 'fsbo'` (`dashboardShellConfig.ts` →
`ForSaleByOwner`). There is no separate FSBO layout and no Client concierge
shell. Jake’s HTML is the Overview *look* (next-step hero, property switcher,
summary cards), not a second product.

---

## 1. What the FSBO workspace is

Velvet Elves coordinates workflow for an **unrepresented seller**. The seller
never sees the task queue, AI drafts, internal notes, other sellers’ files, or
back-office approvals.

The portal answers three questions:

1. **What do I need to do next, and why does it matter?**
2. **Which documents do *I* still owe vs what Velvet is collecting?**
3. **Where does this file stand, and what’s coming up?**

### Boundary notice (always present)

> "Velvet Elves coordinates your workflow but does not act as your agent or
> provide legal advice."

Defined as `FSBO_BOUNDARY_NOTICE` on the backend and `@/utils/copy` on the
frontend. It renders in the tool-page footer, Overview support card, and the
public milestone viewer.

---

## 2. Who the customer is, and how their data is isolated

- **Role:** `ForSaleByOwner` (`UserRole.FOR_SALE_BY_OWNER`).
- **Access union:** a seller sees a deal if **either**
  - they created it (`transactions.created_by == user.id`), **or**
  - they hold an active `transaction_assignments` row with
    `role_in_transaction = for_sale_by_owner` on a tenant-owned transaction
    (invite-to-track; the agent remains `created_by`).
- **Guard:** `fsbo_workspace.assert_fsbo_transaction_access` raises **404**
  (not 403) on a miss. `list_fsbo_owned_transaction_ids` is the list-side
  union.
- **PII:** address / city / state / party contacts are Fernet-encrypted.
  Anything shown is decrypted via `_safe_decrypt`.
- **Mailbox:** `is_fsbo_mailbox_message` — outbound coordinator email/sms **or**
  `is_client_visible` notes. AI drafts, document-action, and system rows stay
  hidden. The seller’s own inbound notes are in the thread but **do not**
  create a reply NBA (`is_coordinator_mailbox_row` excludes `sender_user_id ==
  seller`).

---

## 3. The shell

`AppLayout` + `ForSaleByOwner` capability. Keep these testids:
`fsbo-shell`, `fsbo-next-action`, `fsbo-upload-cta`, `fsbo-nav-*`,
`fsbo-share`, `fsbo-property-switcher`, `fsbo-message-composer`,
`fsbo-next-action-banner`.

- **Sidebar:** standalone **Home** (`/fsbo`), then Workspace — **My
  Properties**, **Documents**, **Messages**. **Payments** is appended only when
  `open_invoice_count > 0`.
- **Footer CTA:** Share milestones (`fsbo-share`).
- **Topbar:** brand, portfolio chip, notification bell, user chip. No staff
  “New Transaction” CTA.
- **Persistent banner:** `critical_next_steps[0]` — the most urgent seller
  verb in the **portfolio**. Independent of which property tile is focused on
  Home (L1).
- **Ask Aime** is the floating button, not a nav item.

Routes that stay (no redirects):

| Path | Page |
|---|---|
| `/fsbo` | Overview |
| `/fsbo/properties` | Property list |
| `/fsbo/properties/:id` | Property workspace (six-rail) |
| `/fsbo/documents` | Document board |
| `/fsbo/milestones` | Messages inbox (route name is historical) |
| `/fsbo/invoices` | Payments (nav hidden when empty) |
| `/milestones/:shareToken` | Public viewer |

---

## 4. Backend API surface

Dashboard namespace `/api/v1/dashboard/fsbo/...` plus shared document/invoice
routes that **switch to FSBO asserts** when the caller’s role is
`ForSaleByOwner`.

| Method & path | Purpose |
|---|---|
| `GET /dashboard/fsbo/overview` | Properties with per-tile `next_action`, ranked `critical_next_steps`, seller-owed missing totals, `open_invoice_count`, listing-prep checklist, support, boundary |
| `GET /dashboard/fsbo/properties/{id}` | Seller timeline, projected docs, mailbox, contacts, `listing_go_live_date` |
| `GET /dashboard/fsbo/documents` | Boards with `seller_owed_missing` / `velvet_collecting_missing` |
| `GET /dashboard/fsbo/milestones` | Seller timelines + mailbox (`body`, `direction`, `seen`) |
| `POST /dashboard/fsbo/messages` | Seller question (`subject`: “Question from the seller”). 404 if not owned. Marks coordinator rows on **that property** seen |
| `POST /dashboard/fsbo/messages/seen` | `{ log_ids: [...] }` — only the ids the seller opened |
| Share-link CRUD | Create / list / revoke; public resolve uses seller timeline, not `tasks.name` |
| `GET /api/v1/fsbo/settings` | Includes `milestone_sharing_defaults.default_expiry_days` |
| Documents download / ack / sign | `_can_access_doc` (own upload ∪ `is_client_visible`) then `assert_fsbo` |
| `POST /documents/{id}/flag-deletion` | FSBO may flag **own uploads** on an owned tx only |
| `GET /client/invoices` | `list_fsbo_owned_transaction_ids` (created_by ∪ invite) |

Upload reuses `POST /documents` via `FsboUploadModal` (`listing_photos` is a
real `DocumentType`).

Staff PATCH may set `transactions.listing_go_live_date`. Null is informational
and **does not** block the seller NBA.

---

## 5. Next-action engine (L1–L3, L5, L7, L10)

Per-property `derive_fsbo_next_action` kinds:

`upload_document | acknowledge | review | reply | pay | none`

Rank (first match):

1. First missing **seller-owed** type
2. Acknowledge (`client_share_kind = acknowledge` and not yet acknowledged)
3. Sign **only if** a real envelope exists (`esign_envelope_id` non-empty and
   not `stub-client-*`). Stub envelopes render **Open**, not a Sign NBA
4. Review (`needs_follow_up` or shared-as-review)
5. Unseen **coordinator** mailbox rows
6. Open invoice
7. `none` — “You’re on track”

Never auto-ranked: Share, staff `tasks.name`, inspection-as-a-fake-form,
go-live date.

**Banner** = `rank_portfolio_next_steps` of those actions →
`critical_next_steps[0]`.

**Hero** on `/fsbo` = the **selected tile’s** `next_action`.

**Stay on track** = other tiles whose `kind != none`. Do not slice
`critical_next_steps[1:]`.

### Seller-owed vs file-required (L2, L14)

| Set | listing_prep | under_contract |
|---|---|---|
| **Seller-owed** (Upload NBA + “You still need”) | disclosures + `listing_photos` | disclosures **until present**; photos drop off |
| **File-required** (board Missing / “Velvet is collecting”) | disclosures + photos | PA, CD, settlement, deed |

Files often skip listing-prep (Velvet Contract is created `under_contract`).
Disclosures stay owed until they are on file.

Photos present but unreviewed: not an upload NBA; checklist shows “In review”.

---

## 6. Page-by-page workflow

### 6.1 Overview — `/fsbo`

- Summary cards (property count, seller-owed missing, live share links, days
  to close).
- Property switcher (`fsbo-property-switcher`).
- Hero next step for the focused file (`fsbo-next-action`).
- Stay-on-track for other files.
- Listing-prep checklist when that file is in `listing_prep` (disclosures,
  photos, informational go-live).
- Upcoming deadlines from **key dates only** (no task names).
- Support + boundary.

### 6.2 My Properties — `/fsbo/properties`

List of owned + invited files. Opens the six-rail workspace.

### 6.3 Property workspace — `/fsbo/properties/:id`

Left rail (`aria-label="Property sections"`): Overview, Timeline, Documents,
Contacts, Sharing, Messages.

- **Timeline** = `build_seller_timeline` (listing-prep C2a stages, or
  under-contract key-date stages). Go-live / Ready-to-list are never forced
  `active`.
- **Documents** = `project_fsbo_document` verbs: Open / Acknowledge / Sign (if
  real URL) / Flag (own uploads). Unshared staff files: status only.
- **Messages** = expand-to-read marks **that** `log_id`. Composer posts
  `POST /dashboard/fsbo/messages` (not Client Q&A).

### 6.4 Documents — `/fsbo/documents`

Split missing into **You still need** (Upload) vs **Velvet is collecting**
(no Upload). `?tx=&docType=` opens the upload modal pre-filled.
`listing_photos` is in the type list.

### 6.5 Messages — `/fsbo/milestones`

One conversation **per property**. Left file list (hidden when there is only
one file); right chronological thread with the composer pinned at the bottom
(`fsbo-message-composer`). Opening a file's thread marks that file's unseen
**coordinator** rows as seen. Property Messages rail reuses the same thread.
No native `<select>` — files are branded list buttons.

### 6.6 Payments — `/fsbo/invoices`

Same client invoice APIs, authorized with the FSBO id union. Nav hidden when
there are no open invoices.

### 6.7 Sharing + public viewer

Share-link modal default expiry comes from
`/api/v1/fsbo/settings` → `milestone_sharing_defaults.default_expiry_days`
(1→24h, 2→48h, 7→7d, else 30d).

Public viewer shows seller timeline (Completed / InProgress / Pending), key
dates, **document status cues** (no files), and the boundary notice. Never
`tasks.name`. Opening a live link writes `share_link_viewed` with
`transaction_id` so the seller bell can deep-link to that property.

### 6.8 Notifications — topbar bell

Seller-only feed (`GET /dashboard/fsbo/notifications`). Grouped, not a dump:

| Event | Bell | Click |
|---|---|---|
| Unseen coordinator mailbox | One item per file | `/fsbo/milestones?tx=` |
| Packet shared (review/ack) | `client_document_shared` | `/fsbo/documents?tx=` |
| Signature ready | `client_signature_ready` | `/fsbo/documents?tx=` |
| Open invoice | `client_invoice_open` | `/fsbo/invoices` |
| Share link viewed | grouped `share_link_viewed` | `/fsbo/properties/{id}` |
| Seller’s own inbound note | never | — |
| Staff AI drafts / overdue tasks | never | — |

**Read model:** Mark all as read dismisses bell notices (`notifications.read_at`
+ `fsbo_bell_ack`). It does **not** mark Message threads seen. Opening a
conversation still marks that file’s coordinator rows. Clicking a packet /
invoice / share row marks that notice read, then navigates.

`notify_transaction_clients` includes `for_sale_by_owner` assignments **and**
an `is_fsbo` file’s `created_by` seller.

### 6.9 Ask Aime

`POST /dashboard/ai-chat` for `ForSaleByOwner` is **rule-based**. Context loads
this seller's properties only (`format_fsbo_chat_context`). If
`listing_go_live_date` is missing on the database, the select retries without
that column so the panel never 500s. Chips (what's missing, closing, coordinator,
next step), Concierge, legal questions, and unmatched free text all return a
seller-safe reply without calling the tenant LLM. Missing-docs uses
**seller-owed** types plus listing-prep facts (photos in review, go-live
informational). Never deed / CD as seller homework, never overdue / pipeline.

---

## 7. Staff loop (v1)

- Coordinator shares packets with `client_share_kind` (`review` |
  `acknowledge` | `sign`). Ack is **not** implied by visibility alone.
- `notify_transaction_clients` includes `role_in_transaction in (client,
  for_sale_by_owner)` and the FSBO file’s `created_by` seller.
- Seller notes land on the existing staff client-thread column (`is_client_visible`
  notes). Relabel later; do not invent a second mailbox.
- No self-serve listing create in v1. Coordinators add properties.

---

## 8. What this is not

- Not a clone of the Client navy concierge.
- Not a cream/topbar-only HTML page without `AppLayout`.
- Not Chrome-QA-complete as the whole product — the harness checks chrome
  and journeys; the engine above is the contract.
- Not live DocuSign in v1: `signing_url: null` / stub envelope → Open.
- Not a place to recover deleted reconstruction plans.

---

## 9. Primary code

**Backend:** `app/services/fsbo_workspace.py`, `app/api/v1/dashboard_role.py`,
`app/schemas/dashboard_role.py`, `documents.py`, `client_documents.py`,
`client_invoices.py`, `share_link_service.py`,
`supabase/migrations/20261002090000_listing_go_live_date.sql`.

**Frontend:** `AppLayout.tsx`, `dashboardShellConfig.ts`, FSBO pages under
`src/pages/fsbo/`, `FsboDocumentActions.tsx`, `fsboNextAction.ts`,
`ShareMilestoneModal.tsx`, `MilestoneViewerPage.tsx`.
