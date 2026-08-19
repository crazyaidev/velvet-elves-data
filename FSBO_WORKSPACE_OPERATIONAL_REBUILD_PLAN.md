# FSBO Workspace — Operational Reconstruction Plan

*Drafted: 2026-08-18. Logic-reviewed rev 2 the same day. Rev 3 (same day):
no production sellers, so the seller shell is in scope now — not a late
compat pass.*
*Grounded in `requirements.txt` §1.2g / §1.7 / §2.1,
`FRONTEND_UI_WORKFLOW_LOGIC.md` §8, `FSBO_WORKSPACE_WORKFLOW.md`,
`FSBO_WORKSPACE_PLAN.md` (rev 4, visual/shell leftover), `SYSTEM_DESIGN.md` §4.3.1f,
`CLIENT_PORTAL_OPERATIONAL_REBUILD_PLAN.md`, `FSBO_PORTAL_CHROME_QA_2026-08-17.md`,
and the live code in `velvet-elves-backend` / `velvet-elves-frontend`.*

> **Relationship to prior FSBO plans.** Rev-4 (`FSBO_WORKSPACE_PLAN.md`) is a
> *presentation* leftover: tab bars, gutters, Property Detail body, doc
> reconciliation. Most of that chrome already shipped **inside AppLayout**,
> which is the wrong product. **This plan replaces the FSBO shell.** There
> are no production sellers to migrate. Completeness of jobs still outranks
> pixel polish; the layout change is information architecture (short nav,
> one Home, property as a file page), not a new visual system or a copy of
> Client's navy "Ask your team" concierge.

---

## 0. Rev-2 logic corrections (vs the 2026-08-18 first draft)

Checked against `fsbo_workspace.py`, `client_workspace.py`, `client_staff.py`,
`client_documents.py`, `FsboOverviewPage.tsx`, `FsboMilestonesPage.tsx`,
`FsboPropertyDetailPage.tsx`, and the wizard FSBO invite.

1. **Phase order was inverted.** Draft-1 put a full Sign/Ack/Reply ranker
   (Phase 2) *before* the mailbox (Phase 3) and shared packets (Phase 5). A
   ranker must not emit a verb the seller cannot finish. Ranker is now
   **Phase 5**, after messages and packets exist. Early phases only use
   verbs that already work (upload, share footer, hide empty Payments).
2. **J11 said "Phase 4" for listing-prep photos.** After this reorder, Phase 3
   is the public share viewer and Phase 4 is shared packets. Extra listing-prep
   items stay in **Later**, not in any numbered phase.
3. **"Add your first property" is the empty-hero description**, not an
   unfocused-tile state. With any property, the hero focuses `properties[0]`.
4. **Mark-seen fires on Messages *and* Property Detail.** Stopping it on
   one page is not enough.
5. **Wizard auto-invite is buyer-rep + `is_fsbo` only.** A seller-rep FSBO
   file does not email the owner. Staff fallback is Assign / invite, not
   the represented-client "Client Access" panel (`role_in_transaction =
   'client'` only).
6. **`notify_transaction_clients` only writes to `role_in_transaction =
   'client'`.** Sharing a packet on an FSBO file currently bells nobody.
   Phase 4 (packets) must notify `for_sale_by_owner` too.
7. **`GET /client/documents/{id}/sign-url` returns `signing_url: null`**
   (download mode / stub envelope). Journey 7.4 must not promise DocuSign.
   Sign means open the file (and later a real URL when Client grows one).
8. **Under-contract "missing" includes purchase agreement, CD, settlement,
   deed.** Those are often title/buyer artifacts. NBA must use
   **seller-owed** types, not the full file checklist. Frozen-set iteration
   is unordered — pick a stable type order when prefilling upload.
9. **Singular NBA is per focused property.** Do not delete the
   other-file "also needs you" line or a two-property seller will miss Maple
   while focused on Velvet. Same pattern as Client deal switcher.
10. **Target IA was deferred to Phase 6** so `/fsbo/properties` and the
    Chrome harness would keep working. That assumed live users and bookmarks.
    There are none. Rev 3 puts the seller shell in **Phase 1** and rewrites
    the harness in the same slice.
11. **"Six-door" was sloppy.** Sidebar is Dashboard + My Properties +
    Documents + Payments + Messages (five destinations), plus a six-pane
    property record.

---

## 0b. Rev-3 UI decision (no production sellers)

The reconstruction is **necessary as a UI change**, not only as backend
verbs. Today's unfriendly product is the shell:

- `AppLayout` is Transaction OS: KPI strip (Missing Docs, Share Links Live,
  Days To Close), Dashboard vs Workspace, tours, Concierge.
- Property Detail is a six-rail **matter file** (Overview / Timeline /
  Documents / Contacts / Sharing / Messages), documented as Dotloop / Clio
  for legal pros — the wrong audience.
- `FsboPortalShell` breadcrumbs say `Workspace › …` (internal tool
  language). Duplicate tab bars were already a rev-4 defect.
- Client already left `AppLayout` for `ClientWorkspaceLayout`. FSBO is
  still the staff clone with a Share footer.

**Constraint that no longer applies:** preserve current routes, AppLayout
KPI chrome, or Chrome selectors across Phases 1–5. Redirects are still
cheap (`/fsbo/properties` → Home, `/fsbo/milestones` → Messages). The
harness is updated when the shell is.

**Constraint that still applies:** do not invent a second visual language
or copy Client's "your agent" concierge. Reuse Velvet tokens, type scale,
and the Share modal / upload modal / FAB. Jobs must still ship in verb
order (mailbox before Reply in the ranker).

---

## 1. Verdict

**Keep a distinct FSBO identity. Reconstruct the product. Do not merge it into
the Client portal, and do not keep the current five-destination AppLayout
clone plus a six-pane property file.**

The original spec (`requirements.txt` §1.2g) is a **self-guided seller**:
property-centric listing prep, documents, milestones, read-only share links,
a coordinator who is *not* their agent. The as-built product is something
else: an **invite-to-track** portal on a deal the agent created
(`transaction_assignments.role_in_transaction = 'for_sale_by_owner'`). Yareny
does not `created_by` her files. She cannot add a property. Chrome-green
does not mean the workspace is useful.

A represented Client already has Home, Timeline, Documents, Ask-your-team,
shared packets (sign / acknowledge), and pay-when-invoiced. If FSBO only
mirrors that with different CSS, the extra workspace is waste. It is *not*
only CSS. Three jobs do not belong on Client and are why FSBO stays:

1. **Unrepresented legal voice.** Every surface must say Velvet coordinates
   and does not act as the seller's agent. Client copy says "your agent."
2. **Listing-prep before a contract.** Required docs and milestones are
   disclosures / go-live, not CD / deed / inspection response.
3. **Buyer-facing milestone share.** The seller is the one who sends a
   read-only timeline to a buyer or attorney. Client share was explicitly
   deferred (`CLIENT_PORTAL_OPERATIONAL_REBUILD_PLAN.md` non-goals).

Everything else in today's FSBO shell is either a duplicate of Client, a
status board that cannot complete the named job, or a door that opens onto
an empty room (Payments with no invoices, public viewer with no steps,
Messages with no reply).

**North star:** every named FSBO action is completable in-portal, on *this
seller's* files, without leaking staff workflow, without pretending the
seller can self-list until product ships that, **and without making the
seller operate a staff dashboard to do it.**

---

## 2. What we measured (docs vs code vs live)

| Claim in docs | As-built | Live (Yareny / Chrome QA 2026-08-17) |
| --- | --- | --- |
| Self-guided seller; empty state "Add your first property" (`FRONTEND_UI_WORKFLOW_LOGIC.md` §8.1) | `canCreateTransaction: false`; empty **body** already says the coordinator will add the first property | No create. The hero **description** still says "Add your first property to get started" when `properties.length === 0` |
| Ownership = `created_by` (`FSBO_WORKSPACE_WORKFLOW.md` §2) | Union of `created_by` **or** active `for_sale_by_owner` assignment | Yareny is assignment-only; overview is empty without that union |
| Listing-prep milestones: photos, marketing, launch checklist (`requirements.txt` §2.1) | Required docs = seller disclosure + lead paint. Timeline = staff tasks, else key dates | Maple Prep is `listing_prep` with 2 missing disclosures; no photo/launch items |
| Messages = talk to the coordinator | Messages page is **outbound email/sms only**. Mark-seen on **Messages mount and Property Detail mount**. No composer | 2 coordinator emails visible; seller cannot reply; visiting either page clears unread |
| Two-way thread already exists for Client *and* FSBO (`client_messages.py` allows `ForSaleByOwner`) | FSBO UI never calls it. Portal filter `is_portal_visible_message` **drops** inbound/`note`, so a posted question would be invisible on Messages even if the API accepted it | Dead capability |
| Share a live milestone timeline | Create/revoke works; public viewer is honest about privacy | Viewer address + "timeline will appear once the first milestone is set." Listing-prep has `Closing —` |
| Next step is completable | Ranker: missing docs → overdue *staff* task → "confirm closing." CTA is Upload **or** Open property. Staff-task rows are **latent** (they only appear when `missing_docs_count == 0`) | Yareny always sees upload because both files still have gaps. "Stay on track" can still list the second property's upload. Banner duplicates the hero |
| Payments | Sidebar always shows Payments; APIs already allow FSBO via `list_client_transaction_ids` (any active assignment) | Empty table. Client **Home** hides the Payments control when `open_invoice_count === 0`; FSBO nav does not |
| Notifications | Topbar bell | Until 2026-08-17 it showed tenant AI drafts. Now seller-safe (share views + coordinator messages). Still no reply/sign/pay kinds |
| Ask Aime | FAB; FSBO-safe greeting after QA | Explains missing docs. Cannot upload, share, or message for the seller. Concierge rail opens the same chat |
| Document board Verified / Complete | Staff review + e-sign envelope state | Seller sees "In progress" on files they just uploaded and cannot tell what *they* must do next vs what the coordinator is reviewing |
| Contacts / Call / Email | Property Detail rail from `transaction_parties` | Present; no in-portal next step attached |
| Staff invite | Wizard auto-invite **only** if `is_fsbo` **and** representation is Buyer. Seller-rep FSBO files skip it. Failure toast points at "Client Access" (`role_in_transaction = 'client'`), which will not list this seller | Buyer-rep invite works. True unrepresented-seller files need a manual ForSaleByOwner invite |

Chrome **bellfix: 49 pass / 0 fail / 1 warn**. That is "the doors open." It is
not "the jobs finish."

---

## 3. Is the workspace necessary?

### Keep it if we reconstruct

The customer is an **unrepresented seller on a Velvet-coordinated file**. They
are not an agent, not a represented Client, not a vendor. Folding them into
`/client/home` would:

- Address them as if they had a listing agent ("Ask your team" / Agent Info).
- Hide listing-prep required docs behind buyer/seller Client rankers.
- Drop buyer-facing share links (not in Client).
- Mix `for_sale_by_owner` assignments into Client "party" language.

The role `ForSaleByOwner`, `/fsbo/*`, and `/api/v1/dashboard/fsbo/*` stay.
`AppLayout` as the FSBO chrome does **not**. Client already has a dedicated
workspace layout; FSBO gets `FsboWorkspaceLayout` in Phase 1.

### Kill the *current shape* of the workspace

Today's information architecture is an internal dashboard wearing customer
clothes:

```
Dashboard  +  My Properties  +  Documents  +  Payments  +  Messages
+ property workspace (Overview / Timeline / Documents / Contacts / Sharing / Messages)
+ Overview hero + persistent banner + Documents CTA
+ Ask Aime + Concierge upsell + Share modal
```

That is too many doors for three real jobs (upload, share, hear from
coordinator), one of which cannot be completed (reply). **Rev 3: replace
this shape in Phase 1.** There are no production sellers to onboard through
the old doors first. Putting completable jobs onto AppLayout and then
moving them is wasted double-touch.

### Explicitly out of this reconstruction

**Self-serve "I listed my house and opened a Velvet account"** (`requirements.txt`
self-guided seller, marketing `/fsbo` early-access). Shipping create-property
without a coordinator, pricing, and intake is a different product. Empty
states must stop promising it. If product later wants that, it is a new
phase after the invite-to-track jobs work.

---

## 4. Jobs that earn a seat

A feature stays only if a seller can **finish** it without staff, and if
removing it would make the sale worse.

| Job | Useful? | Today | Reconstruction |
| --- | --- | --- | --- |
| **J1. See my properties and the one next action** | Yes | Overview + banner + KPIs + property list + property Overview pane — five copies, inside staff AppLayout | Dedicated seller Home (Phase 1). Deal switcher if 2+ properties. Focused NBA **plus** a compact "other file needs you" line. No KPI strip. Banner goes away |
| **J2. Upload a named missing document** | Yes | Works (property + doc_type + file). Ranker always "upload missing" when any **file-required** gap exists, including CD / deed / settlement on under-contract files | Keep. CTA prefills a **seller-owed** `doc_type` (S15). Never "Upload closing disclosure" unless staff marked that type seller-completable |
| **J3. Share a truthful timeline with a buyer** | Yes — unique vs Client | Create/revoke works; viewer often empty | Keep as **sidebar-footer CTA always** (do not hide it behind the ranker). Viewer must show key dates / listing-prep checklist even with zero staff tasks |
| **J4. Read and reply to the coordinator** | Yes | Read-only outbound email/sms. Marks unread on Messages **and** Property Detail mount so the Unread tab lies after first visit | Two-way thread (`is_client_visible` + portal-visible outbound). Composer on Messages. Do not auto-mark-all-seen on either mount. Seller's own notes are not unread |
| **J5. Sign / acknowledge what was sent to *me*** | Yes (parity with Client) | `client_documents` already allows FSBO. `sign-url` always returns `signing_url: null` / `mode: "download"`. Staff share notify only hits `role_in_transaction = 'client'`, so an FSBO-only file bells nobody. Documents projection does not list `is_client_visible` packets | Reuse Client packet columns + Acknowledge. Sign CTA opens/views the file until a real signing URL exists. Extend notify to `for_sale_by_owner` |
| **J6. Pay an invoice** | Yes when one exists | Nav always visible; empty | Hide Payments unless `open` count > 0. NBA may rank Pay |
| **J7. Know Velvet is not my agent** | Yes — legal | Boundary notice exists | Keep on Home + share viewer + Ask Aime. Remove Concierge upsell that implies a product they cannot buy in-portal |
| **J8. Call/email people on the file** | Mild | Six-rail Contacts pane | Keep as a **section on the property file page**, not a nav destination |
| **J9. Ask Aime** | Mild, after J2–J4 work | Seller-safe explanations | Keep FAB. Never as a substitute for upload/share/reply. No Concierge prompt until Concierge is a real FSBO SKU |
| **J10. Flag a mistaken upload** | Yes | Works | Keep on own uploads only, not shared packets |
| **J11. Listing-prep beyond two disclosures** | Spec yes, product no | Not implemented | **Later:** photo / go-live only if staff can assign those as *seller-completable* items. Do not invent a fake launch checklist. Not Phase 3 (share) and not Phase 4 (packets) |
| **J12. Self-create a property** | Spec yes, ops no | Disabled + dishonest empty copy | Honest wait-state. Optional "Email my coordinator" using J4, not a wizard |

---

## 5. Logical / workflow flaws (root cause, not UI nits)

### F1 — Two products in one role
Docs describe a self-guided lister. Code implements invite-to-track. Empty
copy, marketing, and `canCreateTransaction: false` disagree. **Pick
invite-to-track for this reconstruction.**

### F2 — Next steps that are not the seller's
`derive_next_steps` can surface an overdue **staff** task (`action_kind:
open_property`) with the task's internal name. Opening Property Detail does
not complete it. Same class of bug as Client "Choose your inspection time"
opening the timeline.

### F3 — One job, six surfaces
"Upload missing documents" appears as Overview hero, persistent banner
(hidden only on `/fsbo` and `/fsbo/documents`), Documents page, Property
Documents pane, Ask Aime, and the Missing Docs KPI. The seller does not need
a dashboard *about* the upload; they need the upload.

### F4 — Messages is a broadcast log, labeled as a mailbox
`is_portal_visible_message` keeps only outbound email/sms. Inbound and
`channel=note` are stripped. `POST /client/messages` already allows FSBO
and gates on *any* active assignment (so Yareny would pass) — but a
successful post would still not render on `/fsbo/milestones`. Mark-seen
fires on **Messages mount and Property Detail mount**, so "Unread" is a
one-shot. After two-way mail ships, the seller's own inbound notes must
not count as unread.

### F5 — Share is the unique feature and the weakest destination
Primary CTA is "Share milestones." Public viewer is empty until staff
tasks exist. Listing-prep files have no closing date. Sharing an empty
timeline trains buyers that Velvet is a blank page.

### F6 — Document board speaks coordinator
Missing / In progress / Uploaded / Verified / Complete is the staff review
pipeline. The seller's questions are: *What do I still owe? What did I
send? What did they send me to sign?* Client just rebuilt that. FSBO still
shows "In progress" for unreviewed uploads.

### F7 — Payments and Agent-shaped chrome
Payments is a permanent nav item (Client **Home** hides the Payments control
when `open_invoice_count === 0`; Client's concierge nav is Home / Next
Steps / Timeline / Documents / Updates). Overview "Learn about Concierge"
opens Ask Aime. Contact info belongs on the property file page;
Agent Info must never appear.

### F8 — Property workspace is an internal matter file
Overview / Timeline / Documents / Contacts / Sharing / Messages on one
property clones the staff deal workspace (the page docstring cites Dotloop /
Clio). A seller with one house should live on Home; the property record is
a **scrolling file page**, not a second app.

### F9 — Listing-prep is a label, not a workflow
`fsbo_state = listing_prep` only changes two required doc types. No photo
approval, marketing target, or launch checklist (`requirements.txt` §2.1).
Timeline falls back to key dates that listing-prep often lacks.

### F10 — Doc drift
`FSBO_WORKSPACE_WORKFLOW.md` still says created_by-only ownership, portal
tabs vs sidebar fights between rev-4 and the workflow doc, `/fsbo/share`
lingers in `SYSTEM_DESIGN.md`, empty state still says Add Property in
`FRONTEND_UI_WORKFLOW_LOGIC.md` §8.1.

### F11 — File-required docs are not seller-owed docs
`required_doc_types_for` (and its docstring) treats under-contract
purchase agreement, closing disclosure, settlement statement, and deed as
what "an FSBO seller is expected to provide." Those are file-completeness
types. NBA and the upload CTA must use a separate **seller-owed** ordered
list (listing-prep: the two disclosures). Do not iterate a `frozenset`
when prefilling — order is undefined.

### F12 — Staff chrome is the UX
`AppLayout` KPI strip, standalone Dashboard link, Workspace group,
`FsboPortalShell` "Workspace ›" breadcrumbs, Concierge strip, and the
persistent banner are agent-product furniture. A first-time seller should
never see them. Client already escaped this; FSBO has not.

---

## 6. Decision register

Recommendations. Flag in the implementing PR if product overrides.

| ID | Decision | Recommendation | Rejected alternative |
| --- | --- | --- | --- |
| **S1** | Does FSBO stay a separate workspace? | **Yes.** Separate role, shell, routes, legal copy, share links, listing-prep docs | Merge into Client with a flag. Cheaper, wrong voice, loses buyer-share |
| **S2** | Who creates the file? | **Staff / wizard invite-to-track** this slice. Seller cannot self-create | Shipping a seller listing wizard now (no coordinator, no pricing, contradicts `canCreateTransaction`) |
| **S3** | Information architecture | **Seller layout in Phase 1.** Leave `AppLayout`. New `FsboWorkspaceLayout`: Home · Documents · Messages; Payments only when invoiced; Share as the persistent primary action (desktop header/footer + mobile fourth slot). `/fsbo/properties` redirects to Home immediately. Chrome harness is rewritten in Phase 1. Property file is a drill-in, not a nav item | Keep AppLayout until a late "collapse" phase because of the harness / hypothetical bookmarks. Four portal tabs (rev-4 open question). Copy Client's navy "Ask your team" shell |
| **S4** | Next-action brain | One `derive_fsbo_next_action` **per focused property** (Phase 5, after its verbs exist). Ranking: Review/Ack (shared packet) → named **seller-owed** missing doc → unpaid invoice → unanswered coordinator thread → optional share-if-timeline-ready → soft "you're on track". Compact "other property needs you" line on Home. Share action stays visible even when NBA is not share | Rank Sign/Reply before those jobs exist. Hide Share when NBA is upload |
| **S5** | Upload CTA | Opens `FsboUploadModal` with `transactionId` **and** the first **seller-owed** missing `doc_type` in a **stable order** (listing-prep: `sellers_disclosure`, then `lead_paint_disclosure`) | Navigate to `/fsbo/documents`. Prefill from unordered `frozenset` iteration. Prefill CD / deed |
| **S6** | Messages | One two-way thread per property. Visible = `is_client_visible` OR portal-visible outbound email/sms. Composer posts through a **FSBO-scoped** send that uses `list_fsbo_owned_transaction_ids`, not Client copy that says "Question from your client". Seller's own inbound notes do **not** count as unread | Keep read-only log. Call Client messages as-is (subject line and Client access helper are wrong) |
| **S7** | Seen / unread | Bell and Messages unread = coordinator items the seller has not opened. Stop mark-all-seen on **Messages mount and Property Detail mount**. Unify seen via `communication_log_views`. Mark a thread when they open it or send | Current fire-and-forget seen-on-mount. Counting the seller's own notes as unread |
| **S8** | Share / public viewer | Viewer always shows: address, listing-prep vs under-contract, key dates if any, required-doc progress ("2 of 2 disclosures in"), boundary notice. Tasks optional. Do not share a blank "awaiting first milestone" as the success state. Persistent Share action is always available; NBA "share-if-ready" is optional and must not hide it | Keep viewer empty until staff tasks |
| **S9** | Shared packets | Reuse `documents.is_client_visible` + Acknowledge now; Sign = open/download until `signing_url` is real (live `GET /client/documents/{id}/sign-url` always returns `mode: "download"`). Access: FSBO assignment already passes `assert_client_transaction_access` — the gap is the FSBO documents **projection/UI** and **notify**. Extend `notify_transaction_clients` to `for_sale_by_owner`. Staff Client Hub (`role_in_transaction = 'client'` only) must include FSBO sellers or staff will not see unanswered seller notes there | A second FSBO share-document table. Promising live DocuSign. Assuming share-with-client already bells the seller |
| **S10** | Document list language | Seller buckets: **Still needed** / **You sent** / **Needs your signature** / **Done**. Map from **seller-owed** gaps + own uploads + shared packets. Keep staff Verified/Complete off this UI | Keep five-column staff board as the primary Documents page |
| **S11** | Payments | Hide nav and Home tile unless open invoice count > 0 (Client **Home** `showPayments` when `open_invoice_count === 0`; not a sixth Client nav item) | Permanent empty Payments |
| **S12** | Ask Aime | Keep FAB. Remove Concierge upsell. Do not start an LLM slice until J2–J5 complete in production | Making Ask Aime the product |
| **S13** | Persistent banner | **Remove.** Home owns the single next action | Keep banner except on `/fsbo` and `/fsbo/documents` |
| **S14** | Property file page | One scrolling page: next action, dates/progress, this file's documents, people (call/email), share. Header CTA = that property's next seller action. No six-rail matter shell | Keep Overview / Timeline / Documents / Contacts / Sharing / Messages as the default |
| **S15** | Seller-owed vs file-required | Split the sets. File-required (`required_doc_types_for`) may stay for coordinator completeness / share-viewer progress. Seller NBA and upload prefill use an ordered **seller-owed** list: listing-prep = `sellers_disclosure`, `lead_paint_disclosure`. Under contract = **empty by default** (PA / CD / settlement / deed are not automatically the seller's job). Staff may later flag a type seller-completable | Using `_UNDER_CONTRACT_REQUIRED` as the upload NBA |
| **S16** | Staff sees seller replies | Seller send writes `is_client_visible` inbound notes onto the **deal communication log**. Extend `notify_transaction_clients` and staff Client Hub / Q&A links to `for_sale_by_owner`, or unanswered FSBO questions never appear on the represented-client surfaces | Assuming Client Q&A already lists this seller. Pointing wizard failures at "Client Access" |
| **S17** | Messages URL | Canonical route `/fsbo/messages`. `/fsbo/milestones` redirects in Phase 1 (same slice as the shell) | Inventing a second mailbox or leaving `/fsbo/milestones` as the live URL |
| **S18** | Compatibility vs usability | **No production FSBO users.** Prefer the seller-friendly shell now. Update Chrome QA when the layout changes. Keep only cheap redirects | Freeze AppLayout for "safety" until jobs land |
| **S19** | Visual language | Sibling of Client: calm, external, short nav, no staff KPIs. FSBO copy + Share CTA + boundary notice. Reuse Velvet tokens, serif titles, upload modal, share modal, FAB. Do **not** clone Client navy / "Ask your team." Do **not** invent a third design system. Do **not** reopen rev-4 "four portal tabs vs sidebar" — nav count follows jobs (three + Share) | Pixel-restyle AppLayout. Restore `completed_designs/ve-fsbo_dashboard.html` KPI dashboard |

---

## 7. Target journeys (definition of done)

Chrome checks are not enough. These stories must run on a live invite.

### 7.1 Invited seller lands and uploads the named disclosure

1. Agent creates an FSBO file and invites the seller as `ForSaleByOwner`.
   **Buyer-rep + `is_fsbo` auto-invites.** Seller-rep FSBO does **not** —
   staff must invite/assign manually (not the represented-client "Client
   Access" panel).
2. Seller accepts, lands on Home (`/fsbo`). If they have properties, focus
   is `properties[0]` — not an "Add property" hero.
3. Next action names a **seller-owed** type ("Upload Seller's Disclosure"),
   not CD / deed, and not a generic "missing documents."
4. CTA opens the upload modal with property + `sellers_disclosure` selected.
5. After upload, that item leaves Still needed; NBA moves to the next
   seller-owed gap or "on track."

### 7.2 Share a timeline a buyer can actually read

1. Seller taps Share (**persistent primary action**, always present, or Home).
2. If the file has no dates and no required-doc progress, the modal warns and
   still allows share — viewer shows listing-prep checklist + boundary, not a
   blank timeline.
3. Under contract with dates: viewer lists those dates in plain English.
4. Seller bell gets `share_link_viewed` (already live).

### 7.3 Reply to the coordinator

1. Coordinator sends a portal-visible email/sms **or** a client-visible note.
2. Home NBA and Messages show it unread. The seller's own later replies do
   not re-badge the bell.
3. Seller replies in Messages. Staff sees the note on the **deal
   communication log**. Staff Client Hub / Q&A also sees it only after S16.
4. Unread clears when they open that thread, not when Messages or Property
   Detail mounts.

### 7.4 Review / acknowledge what was sent

1. Staff shares a packet (`is_client_visible`). The FSBO seller is notified
   (`notify_transaction_clients` includes `for_sale_by_owner`).
2. Home NBA = "Review {label}" or "Acknowledge {label}" — **not** a live
   DocuSign promise. CTA opens/views/downloads the file (`sign-url` today
   returns `signing_url: null`). Acknowledge remains a real in-portal POST
   when `client_share_kind` asks for it.
3. Documents row shows Needs your signature / review → Done.

### 7.5 Two properties

1. Seller assigned to listing-prep Maple and under-contract Velvet.
2. Home switcher lists both; **focused** NBA is that file's ranker.
3. A compact "also needs you" line (or Stay on track until Phase 5) names
   the other file so focusing Velvet does not hide Maple's disclosure.
4. My Properties is not a destination; both houses live on the Home switcher.

### 7.6 Honest empty

- No assignment → "Your coordinator will add your first property." No Add
  button. Optional "Contact coordinator" if support email exists.
- Assigned, nothing waiting, no invoice → on track + Messages + Share.
- No invoices → Payments absent.

### 7.7 First login never looks like Transaction OS

1. After invite accept, the seller sees `FsboWorkspaceLayout`: Home, Documents,
   Messages, Share — not Dashboard / My Properties / a KPI strip.
2. Opening a property is a file page (next action + progress + people), not
   six matter-file rails.
3. Boundary notice is visible. Concierge upsell is not.

---

## 8. Target seller UI and routes

This is a product-shell change, not a stylesheet pass. Client's lesson:
leave `AppLayout` once, land jobs on the new surfaces.

### 8.1 Layout anatomy (`FsboWorkspaceLayout`)

```text
Desktop
  Brand (Velvet Elves — seller workspace, not "Transaction OS")
  Nav:  Home · Documents · Messages · [Payments if open invoices]
  Utility: bell · account
  Primary action: Share (always)
  Main: page
  Persistent: legal boundary (footer or Home card, not a dismissible banner)
  FAB: Ask Aime (explanations only)

Mobile
  Same main
  Bottom nav: Home · Documents · Messages · Share
  Payments: Home tile / route only when invoiced
```

**Home (`/fsbo`)** — one next-action card for the focused property, property
switcher when `properties.length > 1`, "other file needs you" chip, key
dates, coordinator contact, boundary. Not a KPI dashboard. Not a second
Dashboard route.

**Documents (`/fsbo/documents`)** — seller buckets (S10). Upload CTA
prefills seller-owed type. Shared packets appear here from Phase 4.

**Messages (`/fsbo/messages`)** — mailbox with composer from Phase 2.

**Property file (`/fsbo/properties/:id`)** — scrolling page (S14). Back to
Home. Header CTA = this file's next action.

**Payments (`/fsbo/invoices`)** — linked only when open count > 0.

**Public viewer (`/milestones/:token`)** — truthful even with zero staff
tasks (Phase 3). Same calm external voice; still not AppLayout.

### 8.2 Routes

```text
/fsbo                         Home (seller shell)
/fsbo/documents               Still needed / You sent / Needs signature / Done
/fsbo/messages                Two-way thread (canonical)
/fsbo/milestones              Redirect → /fsbo/messages   (Phase 1)
/fsbo/properties              Redirect → /fsbo            (Phase 1)
/fsbo/properties/:id          Property file page
/fsbo/invoices                Only linked when open invoices exist
/milestones/:token            Public viewer
```

Not routes: `/fsbo/share`, `/fsbo/ask-ai`. Not chrome: KPI strip, persistent
next-step banner, Concierge upsell, six-rail matter file, `Workspace ›`
tool breadcrumbs as the primary wayfinding.

### 8.3 What we keep from the current UI

Upload modal (property + doc_type), share create/revoke modal, boundary
string, seller-safe FAB, seller-safe bell. Retire FSBO use of `AppLayout`,
`FsboPortalShell` as the page frame, Overview `KpiStrip` / Concierge strip,
and the Property Detail section rail.

---

## 9. Phases

Implement in order. Each phase is mergeable. Do not skip Phase 1. **Do not
ship a ranker verb before the seller can finish it.** Share stays a
persistent primary action in every phase. **The seller shell ships in
Phase 1** so later jobs land on the real IA.

### Phase 1 — Seller shell + honest contract

Leave `AppLayout` for FSBO. Stand up `FsboWorkspaceLayout` (§8.1). Small
backend: ordered seller-owed `doc_type` on the existing upload next-step
payload.

1. Routes: Home is `/fsbo`. Redirect `/fsbo/properties` → `/fsbo` and
   `/fsbo/milestones` → `/fsbo/messages`. Wire App routes so FSBO pages
   render inside the new layout (same pattern as `ClientWorkspaceLayout`).
2. Nav: Home · Documents · Messages; Payments only if open invoices > 0;
   Share always; mobile four-slot bar.
3. Home: focused next-action card, property switcher if 2+, honest empty
   ("coordinator will add your first property") — delete "Add your first
   property." No KPI strip. No Concierge upsell. No persistent banner.
4. Property file: single scrolling page (S14), not six rails.
5. Documents page: start seller-bucket labels even if shared packets wait
   until Phase 4 (Still needed / You sent; Needs signature can stay empty).
6. Stop mark-all-seen on **Messages mount and Property Detail mount**.
7. Home CTA for `upload_documents` opens the upload modal with the first
   **seller-owed** `doc_type` (S5 / S15). If the focused file has no
   seller-owed gap, do **not** prefill CD / deed / purchase agreement.
8. Do **not** yet remove `open_property` from the payload — ranker is Phase 5.
   Home must not *present* staff task names as the hero if an upload CTA
   exists; if only `open_property` remains, show a soft on-track / "your
   coordinator is working" until Phase 5.
9. Rewrite Chrome QA selectors for the new shell (S18).

**Exit:** Journey 7.6–7.7. A first login cannot see Transaction OS chrome.
Upload CTA prefills a seller-owed type. Unread is not cleared by visiting
Messages or the property file.

### Phase 2 — Messages that are a mailbox

1. FSBO send endpoint (or a thin wrapper) that:
   - authorizes via `list_fsbo_owned_transaction_ids` (`assert_fsbo_transaction_access` → **404** on cross-seller, not Client 403);
   - writes `is_client_visible=true`, inbound, subject "Question from the
     seller" (not "from your client");
   - notifies the assigned TC/Admin from `resolve_support_contact`.
2. Messages list = union of that thread and portal-visible outbound
   email/sms, newest first, grouped by property if 2+.
3. Unread = coordinator items not seen; seen on thread open via
   `communication_log_views`. Seller's own notes never count as unread.
4. Staff: deal communication log shows the note; S16 so Client Hub / Q&A
   and `notify_transaction_clients` include `for_sale_by_owner`.
5. Canonical URL already `/fsbo/messages` from Phase 1.

**Exit:** Journey 7.3. Chrome: composer present; a send round-trips; staff
can see it.

### Phase 3 — Share destination is useful

1. Public viewer: listing-prep checklist (required docs in/out), key dates,
   under-contract timeline when tasks/dates exist, boundary notice.
2. Create-share modal: short preview of what the buyer will see.
3. Do not block share if tasks are empty.

**Exit:** Journey 7.2. A listing-prep share is not a blank page.

### Phase 4 — Shared packets (reuse Client columns, seller copy)

1. FSBO documents projection lists `is_client_visible` packets on owned
   files (assignment already passes Client document APIs; UI/projection is
   the gap).
2. Acknowledge in-portal. Sign/Review CTA opens or downloads the file
   until a real `signing_url` exists — do not claim DocuSign.
3. `notify_transaction_clients` writes to `for_sale_by_owner` as well as
   `client`.
4. Flag-for-deletion stays on own uploads only.
5. Home may show a packet row; the **singular ranker** still waits for
   Phase 5 so we do not advertise Sign before this UI exists.

**Exit:** Journey 7.4. No second document-share schema.

### Phase 5 — One seller ranker (all verbs now exist)

Replace list-of-staff-tasks with `derive_fsbo_next_action` (S4).

- Inputs: seller-owed missing types, shared packets needing review/ack,
  open invoices, unread coordinator thread, share-ready flag, closing
  window.
- Outputs: `{ title, body, action_kind, transaction_id, doc_type?,
  document_id?, invoice_id?, href }`.
- `action_kind` ∈ `upload_document` | `review` | `acknowledge` | `reply` |
  `pay` | `share` | `none`.
- Never copy a staff task name onto the seller. Never emit Sign as live
  e-sign while `signing_url` is null.
- Focused property owns the Home hero. Compact "other property needs you"
  on Home (the switcher already exists from Phase 1).

**Exit:** Home and the property-file header render the same object. No
`open_property` as a fake verb. Two-file sellers still see the other file.

### Phase 6 — removed (folded into Phase 1)

Nav collapse, `/fsbo/properties` redirect, and retirement of the matter-file
rail are Phase 1. Remaining doc reconciliation (`FRONTEND_UI_WORKFLOW_LOGIC.md`
§8, `FSBO_WORKSPACE_WORKFLOW.md` §2, `SYSTEM_DESIGN.md` stale `/fsbo/share`)
ships with Phase 1 and is checked again when Phases 2–5 change routes/copy.

### Later (not this reconstruction)

- Self-serve property create and FSBO tenant (`fsbo_workspace` org type in
  the revenue plan).
- Listing-prep photo / marketing / launch items — only with staff-assignable
  seller-completable records, not hardcoded theatre. **This is J11; it is
  not Phase 3 or Phase 4.**
- LLM "Ask Aime" as a closer of jobs.
- Real DocuSign recipient URL on `sign-url` (shared with Client O3 when
  that actually ships).

---

## 10. What we keep

| Keep | Where |
| --- | --- |
| Role `ForSaleByOwner` + dedicated seller layout | `FsboWorkspaceLayout` (new); `shellVariant: 'fsbo'` until AppLayout is unused for this role |
| Invite-to-track assignment | Wizard auto-invite only for buyer-rep + `is_fsbo`; otherwise staff Assign / ForSaleByOwner invite. `list_fsbo_owned_transaction_ids` |
| Ownership 404 (not 403) on cross-seller reads | `assert_fsbo_transaction_access` |
| Required docs by `fsbo_state` | `required_doc_types_for` as **file** completeness; reconstruction adds ordered **seller-owed** types (S15) |
| Upload modal with property + doc_type | `FsboUploadModal` |
| Flag for deletion on own uploads | Documents page |
| Share create/revoke + view notification | `share_link_service`; bell `share_link_viewed` |
| Boundary notice string | `FSBO_BOUNDARY_NOTICE` |
| Seller-safe Ask Aime context | `format_fsbo_chat_context` |
| Seller-safe pending notifications | `_PORTAL_PENDING_ROLES` + `/dashboard/fsbo/notifications` |
| Invoice APIs already allowing FSBO | `client_invoices.py` |
| Chrome harness | `velvet-elves-data/fsbo_portal_qa/` — **rewrite in Phase 1** with the new layout |

---

## 11. Backend touchpoints (small, specific)

1. **Seller-owed ordered types** — do not treat `_UNDER_CONTRACT_REQUIRED` as
   the upload NBA. Listing-prep order: `sellers_disclosure`, then
   `lead_paint_disclosure`.
2. **`doc_type` on existing upload steps** (Phase 1) so the modal can prefill.
3. **`derive_fsbo_next_action`** (Phase 5) — replace consumer of
   `derive_next_steps` on overview. Keep a compact other-file list until then.
4. **FSBO message send** + list union; do not reuse Client subject/copy;
   authorize with `assert_fsbo_transaction_access` (**404**), not Client
   `assert_client_transaction_access` (**403**). Today any assignment passes
   the Client helper — too coarse to be the FSBO write gate.
5. **Seen state** — `communication_log_views`; exclude the seller's own
   inbound notes from unread.
6. **Public viewer payload** — required-doc progress + key dates when tasks
   are empty (`share_link_service` / milestones shared GET).
7. **Shared packet projection** — list `is_client_visible` rows on FSBO
   documents. Extend `notify_transaction_clients` (and staff hub links) to
   `for_sale_by_owner`. Sign-url stays download-mode until Client grows a
   real URL.
8. **No new LLM. No new `/api/v1/fsbo/` namespace.**

### Frontend touchpoints (Phase 1 shell)

1. **`FsboWorkspaceLayout`** — new layout, same routing idea as
   `ClientWorkspaceLayout`. FSBO routes stop rendering inside `AppLayout`.
2. **Home** — rewrite `FsboOverviewPage` off `DashboardPage` / `KpiStrip` /
   Concierge. One next-action card + switcher.
3. **Property file** — rewrite `FsboPropertyDetailPage`: drop the six-rail
   matter shell; stacked sections.
4. **Documents** — seller buckets on `FsboDocumentsPage`; keep
   `FsboUploadModal`.
5. **Messages** — composer on the `/fsbo/messages` page (Phase 2).
6. **Retire** FSBO use of `FsboPortalShell` as the frame, Overview
   `PageTabBar`, and AppLayout FSBO KPI/banner/nav branches.
7. **Chrome QA** — rewrite selectors in the same PR as the layout.

---

## 12. Verification

Backend: `pytest -k "fsbo or share_link or client_messages or client_documents"`.

New tests:

- Ranker never returns a staff task name; listing-prep missing disclosure
  carries ordered `doc_type`; under-contract NBA does not demand CD / deed
  as seller-owed.
- FSBO can post a seller question on an assigned tx; other FSBO in-tenant
  **404s** (`assert_fsbo_transaction_access`).
- Messages list includes inbound seller notes; those notes are not unread
  for the author; `channel=ai_draft` still hidden.
- Shared viewer JSON includes listing-prep required-doc progress with zero tasks.
- Packet share notifies `for_sale_by_owner`; pending notifications stay
  empty of AI drafts (regression).
- `sign-url` for FSBO stays download-mode until a real URL exists (no fake
  Sign success).

Frontend: seller is not in AppLayout; nav is Home / Documents / Messages;
Share always present; Home CTA opens upload with type; Payments absent at
0 invoices; Messages has composer (Phase 2); no persistent banner;
mark-seen does not fire on property-file mount.

Manual / Chrome (**rewrite** `fsbo_portal_chrome_qa.mjs` in Phase 1):

- 7.1–7.7 journeys, not only "bell exists."
- No KPI strip / My Properties nav / six-rail property file.
- Public viewer not blank on listing-prep Maple Prep.
- `/fsbo/milestones` and `/fsbo/properties` redirect.
- `/notifications` and `/ai-emails` still bounce.
- Type ≥ 12px; no staff chrome.

---

## 13. Risks

1. **Product wants self-serve listing after all.** Then S2 flips and Phase
   "Later" moves up — after J2–J5, not instead of them.
2. **Share preview might leak staff task names.** Public viewer must use the
   same plain-English key dates / required-doc labels, never raw task queue.
3. **Two-way messages vs email.** Coordinator outbound email should still
   show; seller reply is in-portal unless we later add SMS/email send. Do
   not silently drop email history when adding the note thread.
4. **Client document APIs.** Reuse the columns, not the Client Home. Copy
   and notify must stay FSBO-scoped. Do not treat Client O3 as already
   shipping a live DocuSign URL — the endpoint currently always returns
   download mode.
5. **Wizard invite gap.** Seller-rep FSBO files will not auto-invite.
   Reconstruction does not add a listing wizard; ops docs must describe the
   manual ForSaleByOwner invite.
6. **Shell double-touch if we delay the layout.** Landing jobs on AppLayout
   and restyling later costs twice. Phase 1 takes the layout cost once.
   Chrome QA must move with it or the harness will fail on purpose.

---

## 14. Cross-references

- `CLIENT_PORTAL_OPERATIONAL_REBUILD_PLAN.md` — action-model (completable
  CTAs, hide empty Payments, shared packets) and the precedent of leaving
  `AppLayout` for a dedicated layout. Do not copy Client copy or navy
  "Ask your team" chrome.
- `FSBO_WORKSPACE_PLAN.md` rev 4 — presentation leftover; do not reopen
  four-portal-tab vs sidebar. Nav follows jobs (S3 / S19).
- `FSBO_WORKSPACE_WORKFLOW.md` — as-built reference; §2 ownership is stale.
- `FRONTEND_UI_WORKFLOW_LOGIC.md` §8 — reconcile in Phase 1 with the new
  shell.
- `FSBO_PORTAL_CHROME_QA_2026-08-17.md` — FSBO-12 bell leak; remaining
  product gaps. Harness rewrite is Phase 1.

---

*Plan drafted: 2026-08-18. Logic-reviewed rev 2; seller-shell rev 3 the same
day. Not implemented. Git commit / push were not run.*
