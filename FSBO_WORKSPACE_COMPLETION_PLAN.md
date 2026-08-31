# FSBO Workspace — Product Design & Completion Plan

*Rev 3 · 2026-08-20. Logic-reviewed against `requirements.txt`, `SYSTEM_DESIGN.md`,
`FRONTEND_UI_WORKFLOW_LOGIC.md` §8, `milestones.txt`, live
`fsbo_workspace.py` / `documents.py` / `client_documents.py` / `client_staff.py`
/ `client_invoices.py` / `AppLayout.tsx` / FSBO pages. Rev 2 mixed several
workflows that the code cannot execute as written. This rev keeps the product
intent and repairs the logic.*

> **Jake’s HTML is the Overview look, not the product.** A fully operational
> FSBO workspace has not been built. Chrome stays `AppLayout` `shellVariant ===
> 'fsbo'`. The work starts here.

---

## 0. Logic review (rev 2 → rev 3)

These were real workflow/logic errors, not style nits. Each is corrected in
the body below.

| ID | Flaw in rev 2 | Why it is wrong | Correction |
|---|---|---|---|
| **L1** | Banner, hero, and Property Overview share “the same payload,” defaulting to the focused tile | Overview focus is **React state** on `/fsbo`. `AppLayout` banner reads `critical_next_steps[0]` and cannot see that state. Claiming they stay in lockstep is false. | **Banner** = most urgent seller action in the portfolio (API `[0]`). **Hero** = the **selected** property’s `next_action`. **Stay-on-track** = other files. Optional `?tx=` later; not required for v1. |
| **L2** | `under_contract` seller-owed set is **empty** | Files often skip listing-prep (Velvet Contract is created `under_contract`). Disclosures would never be requested after the flip. | Seller-owed **disclosures persist until present**, regardless of `fsbo_state`. `listing_photos` is seller-owed only while `listing_prep`. |
| **L3** | Acknowledge = `is_client_visible` ∧ not acknowledged | Live `_document_action` uses `client_share_kind` (`review` \| `acknowledge` \| `sign`) plus in-flight signature. Ack-on-every-share would mis-label Sign packets. | Reuse `_document_action` (or the same rules) on FSBO rows. |
| **L4** | Every present board row gets **Open** (signed download) | `_can_access_doc` for FSBO is **own upload ∪ `is_client_visible`**, then `assert_client_transaction_access`. `_fsbo_documents_for` lists **all** tx docs. Open on a staff PA that is not shared **404s**. | Open only when download is authorized. Unshared staff files: status only (“On file”). Extend download/ack/sign guards to **`assert_fsbo_transaction_access`** (invited **or** `created_by`). |
| **L5** | Ranker `reply` = “unanswered coordinator mailbox item” | No `needs_reply` flag exists. Any outbound email would be a permanent NBA. | `reply` = at least one **unseen** (`seen === false`) mailbox row on that file. Opening/expanding that row marks it seen and clears the NBA. |
| **L6** | Mark-seen on “thread open” | `FsboMilestonesPage` is a **flat list**, not threads. Visiting Messages today marks **all** unseen on mount. “Thread open” is undefined. | Mark **that message** when the seller expands/opens it (or sends). Do **not** mark the whole inbox on page mount. |
| **L7** | Auto-rank `share` when no live link | Share is optional chrome (`requirements.txt` §9.4a), not a job that blocks “on track.” | Do not auto-rank `share`. Footer / KPI / Property Sharing remain the CTAs. |
| **L8** | Viewer uses C5 stages **when tasks are empty** | Contradicts “never `tasks.name`.” If tasks exist, viewers would still see staff language. | Public viewer and Property Timeline **always** use `build_seller_timeline`. Never task names. |
| **L9** | “Four boolean rows” vs “five stages” vs six table rows | Internal inconsistency. | Checklist = 3 seller uploads (disclosure, lead paint, photos) + 1 staff date (go-live, informational). Timeline = File opened → those items → Ready to list. |
| **L10** | Ready-to-list requires go-live **or TBD** | Contradicts “done when date is set.” A null date must not invent TBD. | Go-live is **informational**. Null = checklist row incomplete; it does **not** block seller NBA. Staff sets the date via PATCH. |
| **L11** | Reuse `/client/documents` and `/client/invoices` as-is | Those call `assert_client_transaction_access` / `list_client_transaction_ids` (assignments only). A `created_by` seller with no assignment 403s/empty list. Invited Yareny works. | When role is FSBO, authorize with **`assert_fsbo_transaction_access`** / `list_fsbo_owned_transaction_ids`. |
| **L12** | Flag “own uploads only” | `POST /documents/{id}/flag-deletion` does **not** check uploader or FSBO ownership today. UI can flag any board row with an id. | Enforce: FSBO may flag only docs they uploaded on an owned tx. |
| **L13** | Inspection as a seller job implied by Jake’s HTML / key dates, but no verb | Emitting staff task names is forbidden; inventing “Respond to inspection” with no form is a fake CTA. | Inspection arrives as a **mailbox item** or a **shared packet** (`client_share_kind`). No synthetic inspection NBA. |
| **L14** | Documents badge = seller-owed count, Missing column = file checklist | Seller taps “2 missing” and sees deed/CD rows. | Missing splits into **You still need** (seller-owed) and **Velvet is collecting** (file-required, not seller-owed, no Upload). |
| **L15** | Staff loop “don’t use Client Q&A” | Seller writes `is_client_visible` notes. Staff `GET/POST …/client-thread` is already the mirror of that column on **any** deal the staff can access (no client-role check). | v1: reuse that drawer as the staff side of the seller mailbox. Relabel later. |
| **L16** | Photos type added in Phase 2 while Phase 1 can NBA `upload_document` for photos | Dead CTA until the modal lists the type. | Enum + modal option in Phase 0. |
| **L17** | “Every FSBO mutation uses `assert_fsbo`” | Upload, download, flag, ack, sign, pay go through **document/invoice** APIs with different guards. | Dashboard FSBO routes use `assert_fsbo`. Document/pay routes must be **aligned** (L4, L11, L12). |
| **L18** | Board select list omits share/ack fields | `_fsbo_documents_for` does not select `uploaded_by`, `is_client_visible`, `client_share_kind`, `acknowledged_at`. Row verbs cannot be derived. | Expand the select. |

Lead-paint is **always** in today’s `required_doc_types_for(listing_prep)` (no `year_built` on `transactions`). Rev 3 keeps that platform rule; it does not invent a federal year gate.

---

## 0b. How to read this document

| Layer | Source of truth |
|---|---|
| **What the seller must be able to do** | §2–§8 |
| **How `/fsbo` looks** | Jake’s HTML, in `STYLE_GUIDE` tokens, inside `AppLayout` |
| **How tool pages look** | `STYLE_GUIDE.md` §15 `FsboPortalShell` |
| **What is as-built after ship** | Update `FSBO_WORKSPACE_WORKFLOW.md` |
| **How we QA** | Extend `fsbo_portal_qa/fsbo_portal_chrome_qa.mjs`; journeys in §8 |

Do **not** recover deleted reconstruction plans. Chrome stays the current workspace.

---

## 1. What Jake’s HTML is — and is not

Jake’s mock is a **dashboard composition**: persistent next-step banner,
property switcher, four summary cards, illustrated documents/comms/contacts,
Share, Support.

It is **not** the listing-prep model, document authorization, mailbox,
share-link system, invoices, Ask Aime, settings, invite vs self-listing, or
the staff loop. Those are designed from requirements + live code below.

---

## 2. Product definition

### 2.1 Who this is for

An **unrepresented seller** (`UserRole.FOR_SALE_BY_OWNER`). Velvet Elves
coordinates workflow and does **not** act as agent or give legal advice
(`requirements.txt` §1.2g, §1.7). The seller never sees the task queue, AI
drafts, internal notes, other sellers’ files, or back-office approvals.

### 2.2 Three questions

1. What do I need to do next, and can I finish it here?
2. What does this property still need (documents, dates, people)?
3. Where does my sale stand, and who do I talk to?

### 2.3 Two property states (`requirements.txt` §2.1)

| `fsbo_state` | Meaning | Seller’s job |
|---|---|---|
| `listing_prep` | Pre-contract. No closing date required. | Disclosures, listing photos; watch go-live if staff set it |
| `under_contract` | Offer accepted. | Any **still-missing disclosures**; review/ack/sign shared packets; reply; pay; watch dates |

**State flip is staff-owned in v1** (`PATCH` `fsbo_state`, already on the
transaction schema). Do **not** auto-flip when a purchase agreement appears.

Staff may collect PA / CD / settlement / deed on the **file**. Those are
file-required. They are not Upload-this-now unless staff **shares** them
(`is_client_visible` + `client_share_kind`).

### 2.4 How a seller gets a file

| Path | Today | This plan |
|---|---|---|
| **Invite-to-track** | Staff creates the deal, assigns `for_sale_by_owner`. Overview unions `created_by` **or** that assignment. | **v1. Complete this path.** |
| **Self-listing** | Empty state implies a coordinator. Self-signup is off. | Designed in C2b. **After v1.** No dead “Add Property” button. |

v1 done: invited seller (Maple Prep `listing_prep` + Velvet Contract
`under_contract`) can complete every **seller-owed** verb in-portal.

### 2.5 What “complete” means

- Seller-owed actions are completable (upload, review, ack, sign-if-URL,
  reply, pay, flag-own).
- Listing-prep has a real stage model (not a blank timeline).
- Under-contract does not nag Upload on title/buyer artifacts.
- Mailbox is two-way; seen is per-message.
- Payments / share / Ask Aime / settings / staff notify actually close.
- Chrome remains `AppLayout` fsbo.

---

## 3. Constraints (frozen)

1. **Chrome.** `AppLayout` + `ForSaleByOwner` capability. Sidebar: Dashboard,
   My Properties, Documents, Payments (if open invoices), Messages. Share in
   the footer. Ask Aime FAB. Seller bell. Persistent banner.
2. **Look.** `STYLE_GUIDE` §15–§16. No cream/topbar-only shell. No text below
   12px.
3. **Honest data.** No invented dates, TBD go-live, or fake Sign.
4. **Isolation.** FSBO reads **404** on cross-owner. Bell is not the staff
   pending inbox.
5. **Download/ack/sign/pay** follow **FSBO ownership**, not “all blobs on the
   tx are openable.”

---

## 4. Honest as-built (2026-08-20)

A shell with projections exists. An operating workspace does not.

| Area | Shipped | Not operational because |
|---|---|---|
| Access | Invite union, 404, onboarding, `/api/v1/fsbo/settings` | Self-listing absent (v1 OK). Document/pay APIs still client-assignment gated |
| Overview | KPI, hero, deadlines, tiles, banner | Hero ignores `action_kind`; missing count is file-checklist; banner ≠ tile focus (and must not pretend to be) |
| Properties | List + six-rail | Timeline = `tasks.name` or empty key dates |
| Documents | Board, upload modal, flag | No authorized Open/Ack/Sign; flag not owned-only; select list lacks share fields |
| Messages | Outbound email/sms | No composer; `is_client_visible` hidden; mark-seen **on mount** |
| Share | Modal CRUD + viewer | `document_status_cues: []`; viewer can show task names |
| Payments | `/fsbo/invoices` + Stripe | Always in nav; list uses assignment ids only |
| Ask Aime | Seller-safe chips | “What’s missing?” uses file-required types |
| Notify | Bell = unread email + share views | `notify_transaction_clients` is `role=client` only; bell ignores invoice/doc kinds |
| Ranker | `upload_documents` \| `open_property` | File-missing + staff task titles |

Chrome QA 2026-08-17 is not evidence these jobs work. Adding `listing_photos`
as required will **change Maple’s missing count** (today 2). The harness must
be updated in Phase 6.

---

## 5. Core capability design

### C1 — Identity, access, isolation

Keep `list_fsbo_owned_transaction_ids` and `assert_fsbo_transaction_access`
(404). Keep onboarding and `/fsbo/settings` (wire share-create to
`default_expiry_days`).

**Align other APIs (v1, not later):**

| API | Today | Required |
|---|---|---|
| `GET/POST /client/documents/{id}/…` | `assert_client_transaction_access` | If role is FSBO → `assert_fsbo_transaction_access` |
| `GET /client/invoices` | `list_client_transaction_ids` | Union / replace with `list_fsbo_owned_transaction_ids` for FSBO |
| `GET /documents/{id}/download` | own ∪ `is_client_visible` + **client** assignment | FSBO: same visibility **+ `assert_fsbo`** |
| `POST /documents/{id}/flag-deletion` | any id | FSBO: own upload on owned tx |

Staff URLs bounce to `/fsbo` (keep).

---

### C2 — Property file

Keep `/fsbo/properties` and six-rail `/fsbo/properties/:id` as Open
transaction. Overview tiles **select**; list tiles **open**. Empty v1 copy:
coordinator adds the first property.

---

### C2a — Listing-prep operating model

Required by `requirements.txt` §2.1 and `FRONTEND_UI_WORKFLOW_LOGIC.md` §8
(disclosures, photo approval, go-live, launch checklist).

**Seller-owed uploads (ordered):**

1. `sellers_disclosure`
2. `lead_paint_disclosure` (platform always-on; no year-built field)
3. `listing_photos` — **only if `fsbo_state == listing_prep`**

**Staff-visible, seller-read-only:** `listing_go_live_date` (new nullable
date on `transactions`, staff PATCH).

**Launch checklist (Overview + Property Overview) — four rows:**

| Row | Complete when | Seller verb |
|---|---|---|
| Seller disclosure | type present | Upload if missing |
| Lead-paint disclosure | type present | Upload if missing |
| Listing photos | ≥1 `listing_photos` **and** `review_status=approved` | Upload if none; **wait** if uploaded/unreviewed (not an NBA; checklist shows “In review”) |
| Go-live target | `listing_go_live_date` not null | none (staff) |

**Timeline (`listing_prep`):** File opened → Seller disclosure → Lead paint
→ Listing photos → Go-live (done iff date set) → Ready to list (done iff
the three uploads are satisfied; photos approved). Never `tasks.name`.

**Data:** enum `listing_photos`; column `listing_go_live_date`. One-or-more
files, not a gallery. Approval = existing `review_status`.

---

### C2b — Self-listing (not v1)

Minimal create (address, city, state, zip), `is_fsbo`, `listing_prep`,
`created_by=seller`. After v1 so L11 (`created_by` pay/ack) is already
fixed.

---

### C3 — Next-action engine

```
derive_fsbo_next_action(property) →
  kind: upload_document | review | acknowledge | reply | pay | none
  title, body, why_it_matters, deadline?
  transaction_id
  doc_type? document_id? invoice_id?
```

No `share` kind in the auto-ranker (L7). No `open_property` as a fake verb.
No `tasks.name`.

**Seller-owed types (function, not a frozen-by-state empty set):**

```
seller_owed_doc_types_for(fsbo_state) -> ordered tuple
  always, until present: sellers_disclosure, lead_paint_disclosure
  if listing_prep: listing_photos
```

File-required (`required_doc_types_for`) stays: listing_prep = disclosures +
photos; under_contract = PA, CD, settlement, deed. Board uses file-required.
NBA / chip / Ask Aime use seller-owed.

**Rank (per property):**

1. First missing seller-owed `doc_type` → `upload_document`
2. Derived `_document_action` == Acknowledge → `acknowledge`
3. Derived action == Sign **and** `sign-url` is non-null → `review`
   (if URL null, row is Open; **not** an NBA)
4. Derived action == Review (needs_follow_up / share_kind=review) → `review`
   (Open/re-upload)
5. Any mailbox row on this file with `seen === false` → `reply`
6. Open invoice on this file → `pay`
7. `none`

**Surfaces (L1):**

| Surface | Source |
|---|---|
| AppLayout banner | Portfolio `critical_next_steps[0]` (most urgent file) |
| Overview hero | `next_action` of the **selected** tile (client-side from each property’s action, or `properties[].next_action`) |
| Stay-on-track | Other properties with `kind != none` |
| Property Overview pane | That property’s `next_action` |

API: each property card includes `next_action`. Overview also returns
`critical_next_steps` sorted by urgency for the banner (unchanged field
name). Hero **must not** use portfolio missing count.

Closing-soon with no seller verb is `none` plus the deadline card.

---

### C4 — Documents

**Board columns:** Missing | In progress | Uploaded | Verified | Complete.

**Missing is two buckets (L14):**

- **You still need** — seller-owed types absent → Upload (prefilled).
- **Velvet is collecting** — file-required, not seller-owed, absent → no
  Upload.

**Present rows:**

| Condition | Controls |
|---|---|
| Download authorized (own ∪ `is_client_visible`, FSBO access) | **Open** |
| `_document_action` Acknowledge | **Acknowledge** |
| `_document_action` Sign and URL present | **Review & Sign**; else Open |
| `_document_action` Review | Open + Upload replacement |
| Staff file, not visible, not own | Status only — **no Open** |
| Own upload | **Flag for deletion** (API-enforced) |

**Select list** must include `id, uploaded_by, is_client_visible,
client_share_kind, acknowledged_at, signature_status, review_status, …`

**Staff share path:** existing **Share with client**
(`POST …/share-with-client`, `client_share_kind` in review|acknowledge|sign)
already sets `is_client_visible` on any deal the staff can access — including
FSBO-only files. v1 reuses it. Expand `notify_transaction_clients` so the
**seller** is belled. Relabel the menu later.

**Upload:** `FsboUploadModal` + `defaultDocType` including `listing_photos`.

---

### C5 — Seller timeline

`build_seller_timeline(tx, documents)` — **always**, including the public
viewer (L8).

- `listing_prep`: C2a stages.
- `under_contract`: Offer accepted → Earnest money → Inspection → Appraisal
  → Closing disclosure → Cleared to close → Closing day. Status from **key
  dates** (and PA present ⇒ Offer accepted done). No dates ⇒ upcoming, not
  invented.

Staff tasks never appear on FSBO Timeline, Messages, or `/milestones/:token`.

`/fsbo/milestones` remains the **Messages inbox**.

---

### C6 — Mailbox

**Read (`is_fsbo_mailbox_message`):** outbound email/sms **or**
`is_client_visible` notes on owned files. Project `id, body, direction,
seen, transaction_id, created_at, subject`.

**Write:** `POST /api/v1/dashboard/fsbo/messages` `{ transaction_id, body }`
→ inbound `note`, `is_client_visible=true`, subject **“Question from the
seller”**, `assert_fsbo` (404). Notify assigned staff.

Do **not** wire the UI to `POST /client/messages` (wrong subject). Optionally
leave that role allow-list.

**Seen (L6):** `POST /fsbo/messages/seen` with the **ids the seller opened**.
UI: expand/click a row to read body → mark that id. Composer send may mark
the thread’s unseen coordinator rows on that property only — do not mark
unrelated files. **Remove** the mount `useEffect` that marks all unseen.

**Staff side (L15):** those rows are the same `is_client_visible` set as
`GET/POST /transactions/{id}/client-thread`. Staff already has a drawer.
v1 does not build a second seller Q&A. Relabel “Portal Q&A” later.

**Reply NBA (L5):** unseen mailbox rows on that property.

**§6.3 auto-email:** Later. Ask Aime stays in-panel Q&A.

---

### C7 — Milestone sharing

Keep modal CRUD, expiry options, one-time token, revoke, viewer-open notice,
`/sharing` → `/fsbo`. Honor `default_expiry_days`.

Viewer: `build_seller_timeline` + file-required **status cues** (name +
missing/in/complete, **no download**) + `boundary_notice`. No contacts, no
tasks.

---

### C8 — Payments

`open_invoice_count` on overview (open invoices on FSBO-owned txs). Hide
sidebar Payments when 0. Ranker `pay` when an open invoice exists on that
file. Stripe pay-link unchanged. Invoice list uses FSBO-owned ids (L11).

---

### C9 — Ask Aime

Keep FAB + seller-safe prompt. Context / “what’s missing?” use **seller-owed**
types + listing-prep checklist facts (photos in review, go-live date or
unset). Never deed/CD as seller homework.

---

### C10 — Notifications

Seller-only bell (`GET /dashboard/fsbo/notifications`). Actionable and grouped:

- Unseen coordinator mailbox (never the seller’s own inbound notes), **one item per file**
- `client_document_shared`, `client_signature_ready`, `client_invoice_open`
- `share_link_viewed` grouped per file (deep-link includes `transaction_id`)
- Never `client_reply` (duplicate of mailbox), AI drafts, overdue tasks, or other
  owners’ rows

Click: Messages `?tx=`, Documents `?tx=`, Payments, or the property page for
share views.

**Read model:** Mark all as read (and dismissing a packet/invoice/share notice)
writes `notifications.read_at` or a `fsbo_bell_ack` row. It does **not**
bulk-mark `communication_log_views`. Opening a conversation still marks that
file’s coordinator rows seen (L6). Unread badge = unread grouped bell items.

View-all in the panel: Messages.

---

### C11 — Contacts and support

Keep Contacts pane and coordinator card. “Send a message” navigates to
Messages with `?tx=` (or opens composer scoped to the focused property).
Boundary notice once per tool page + Overview card.

---

### C12 — Staff loop

| Staff action | Seller effect | v1 |
|---|---|---|
| Create file + assign `for_sale_by_owner` | Property appears | Exists |
| Review `listing_photos` | Photos checklist completes | New type |
| PATCH `listing_go_live_date` / `fsbo_state` | Timeline / checklist | New date field |
| Share with client (review/ack/sign) | Open/Ack/Sign + NBA | Notify FSBO (L11 notify) |
| Email/SMS or client-thread reply | Mailbox | Exists + C6 read filter |
| Open invoice | Payments + pay NBA | Count + notify FSBO |
| Resolve flag | Email already | Restrict flag to own uploads |

`notify_transaction_clients`: also `role_in_transaction = 'for_sale_by_owner'`.

---

## 6. Domain model (v1)

```
UserRole.FOR_SALE_BY_OWNER
  └── properties[]  (created_by ∪ assignment for_sale_by_owner)
        ├── fsbo_state, listing_go_live_date?
        ├── next_action                         # per property (C3)
        ├── key dates
        ├── documents[]                         # board; Open only if authorized
        ├── seller_timeline[]                   # C5, never tasks
        ├── mailbox[]
        ├── contacts[], share_links[]
```

**Two counts:**

- `seller_owed_missing_count` → chip, Documents badge, Ask Aime, NBA
- File-required absences → “Velvet is collecting” only

---

## 7. Information architecture

Unchanged AppLayout map. Banner is portfolio-urgent; it will **not** always
match the Overview tile (L1). That is correct.

---

## 8. Seller journeys

**J-L1** Maple missing seller disclosure → **hero** (if Maple selected) and
**banner** (if Maple is the most urgent file) → upload prefilled → NBA moves
to lead paint or photos.

**J-L2** Upload `listing_photos` → checklist “In review” until staff
approves → go-live date is staff-set and visible → timeline is C2a stages,
never “Order Title.”

**J-U1** Velvet missing deed/CD → Velvet is collecting, **no** Upload. NBA is
not `upload_document` for those types. If seller disclosure is still missing
on Velvet, NBA **is** upload disclosure (L2).

**J-U2** Select Maple vs Velvet: **hero** follows the tile; **banner** stays
on the portfolio-urgent file until that job is done.

**J-M** Unread dot survives visiting Messages without expanding a row.
Expand marks that id. Composer send works. Staff sees it in client-thread.

**J-D** Staff Share with client / acknowledge → row Acknowledge → POST ack
via FSBO-authorized client document route → NBA clears.

**J-P** No invoices → no Payments nav. Invoice on an FSBO-owned tx → nav +
pay. `created_by`-only seller (after C2b) still sees it (L11).

**J-S** Share link; viewer = seller timeline + N of M cues + boundary; no
task names.

**J-A** “What’s missing?” = seller-owed + listing-prep facts.

---

## 9. Decision register

| ID | Decision | Recommendation | Rejected |
|---|---|---|---|
| **P1** | HTML vs product | HTML = Overview look | HTML as feature list |
| **P2** | Chrome | Frozen AppLayout | New layout / Client concierge |
| **P3** | v1 population | Invite-to-track | Dead Add Property |
| **P4** | Listing-prep | Photos type + go-live date in v1 | Blank Maple timeline |
| **P5** | Seller vs file missing | Two buckets (L14) | One count that nags deed |
| **P5b** | Disclosures after state flip | Persist until present (L2) | Empty under_contract owed set |
| **P6** | Timeline | Always `build_seller_timeline` (L8) | Task names when present |
| **P7** | Messages route | Inbox at `/fsbo/milestones` | Second milestone page |
| **P8** | Mailbox write | `POST /dashboard/fsbo/messages` | “Question from your client” |
| **P9** | Mark-seen | Per expanded message (L6) | Mount-all |
| **P10** | Packets | Reuse share-with-client + client doc actions **with FSBO assert** (L3, L4, L11) | Open-all-docs; ack-all-visible |
| **P11** | Payments nav | Hide when count 0 | Always-on empty door |
| **P12** | Photos | Document type | Gallery |
| **P13** | Go-live | Staff date, informational (L10) | Fake TBD; seller date-picker in v1 |
| **P14** | §6.3 auto-email | Later | LLM outbound |
| **P16** | Banner vs hero | Split (L1) | One payload |
| **P17** | Share NBA | Not auto-ranked (L7) | Nag to share |
| **P18** | Inspection NBA | Packet or mailbox only (L13) | Task-name CTA |
| **P19** | Staff Q&A | Reuse client-thread (L15) | Parallel seller drawer in v1 |

---

## 10. Build sequence

Do not show a verb until the guard that completes it exists.

### Phase 0 — Foundation

- Routes stay under `AppLayout`. Lift type &lt; 12px.
- Delete unused unimported `src/components/dashboard/fsbo/*`.
- Enum `listing_photos` (backend + frontend + **upload modal list**).
- Migration `listing_go_live_date`.
- `seller_owed_doc_types_for` as in C3 (disclosures persist).
- Expand `_fsbo_documents_for` select (L18).

### Phase 1 — Action engine + honest CTAs

- Per-property `next_action`; `critical_next_steps` for banner only.
- Hero uses selected property’s action; fix portfolio-missing CTA bug.
- `open_invoice_count`, `seller_owed_missing_count`.
- `defaultDocType` + Documents query params.
- Ask Aime seller-owed context.

### Phase 2 — Listing-prep stages + document buckets

- `build_seller_timeline`; Property Timeline + viewer.
- Launch checklist; staff PATCH go-live.
- Documents Missing: You still need / Velvet is collecting.

### Phase 3 — Mailbox

- Mailbox predicate + POST messages + body/direction.
- Expand-to-read; remove mount mark-all.
- Staff client-thread already mirrors the column.

### Phase 4 — Authorized row verbs + notify

- Open/Ack/Sign/Review only when authorized; FSBO assert on client doc +
  download + flag-own.
- `notify_transaction_clients` includes `for_sale_by_owner`.
- Bell lists those kinds.

### Phase 5 — Payments + share viewer

- Hide Payments nav; invoice ids = FSBO-owned.
- Viewer = seller timeline + cues + boundary; share default expiry.

### Phase 6 — QA

- Tests: L2 (disclosure still owed under_contract); L4 (Open 404 on
  unshared staff doc); L5/L6 seen; listing-prep timeline without tasks;
  photos type; go-live null does not block NBA; invoice `created_by`.
- Chrome: keep `fsbo-*` testids; update Maple missing count; J-L1, J-U1,
  J-U2 (banner vs hero), expand-to-read, Payments absence, viewer has no
  task names.

### Phase 7 — As-built doc

- Rewrite `FSBO_WORKSPACE_WORKFLOW.md`.

### After v1

- C2b self-listing + registration.
- Seller-proposed go-live.
- Photo gallery.
- §6.3 auto-email.
- Live DocuSign URL.
- Relabel Share with client / Client Q&A to portal copy.

---

## 11. API / schema deltas (v1)

| Change | Notes |
|---|---|
| `DocumentType.listing_photos` | Enum + modal |
| `transactions.listing_go_live_date` | Staff PATCH, FSBO read |
| `properties[].next_action` | C3 |
| Keep `critical_next_steps` | Banner only |
| `seller_owed_missing_count`, `open_invoice_count` | Overview |
| `POST /dashboard/fsbo/messages` | C6 |
| Mailbox `body`, `direction`, `seen` | |
| Timeline from `build_seller_timeline` | Same item shape, new labels |
| Viewer cues + boundary | No tasks |
| `notify_transaction_clients` | `for_sale_by_owner` too |
| Client doc/invoice/download/flag | FSBO assert / own-only flag |

---

## 12. Primary files

**Backend:** `fsbo_workspace.py`, `dashboard_role.py`, `dashboard_role`
schemas, `enums.py`, `transaction` schema + PATCH, `documents.py`
(`_can_access_doc`, flag), `client_documents.py`, `client_invoices.py`,
`client_workspace.py` (notify + optionally `_document_action` reuse),
`share_link_service.py`, tests, migration.

**Frontend:** `AppLayout.tsx` (banner = steps[0] only), `FsboOverviewPage.tsx`
(hero from selected `next_action`), documents/messages/property/upload,
`MilestoneTimeline.tsx`, `useDashboard.ts`, `enums.ts`,
`MilestoneViewerPage.tsx`. **Not** a new layout.

---

## 13. Implementation notes

1. This is **rev 3**. Do not implement rev 2’s “same payload” banner/hero or
   empty under-contract owed set.
2. If a change exists only because the HTML has no sidebar, do not make it.
3. Keep `fsbo-shell`, `fsbo-next-action`, `fsbo-upload-cta`, `fsbo-nav-*`,
   `fsbo-share`, `fsbo-property-switcher`.
4. Do not commit unless asked.
5. Local seller: `yareny.evaly@minafter.com`. App often
   `http://127.0.0.1:5173`, API `http://127.0.0.1:8000`.
)
