# Vendor Workspace — Superior Build Plan (Mortgage + Title)

> Status: PLAN ONLY. No source changed. This document is the single reference
> for building the complete Vendor Workspace into the main Velvet Elves app.
>
> Author: Jan. Date: 2026-06-15. Source comp: `vendor-workspace/` (Jake's
> Mortgage Partner Portal prototype). Primary email thread: Jake's two notes on
> the Mortgage vs Title vendor views (reproduced in §1.2).

> **Revision note (2026-06-15, self-review pass).** I re-checked every
> load-bearing claim against the current source and corrected eight
> workflow/logic errors before this plan goes to build. The substantive fixes:
> (1) the assignment + email-vendor components are already wired into the
> wizard and transaction workspace, so Phase 1 is now about the real gap, not
> re-wiring them; (2) the canonical assignment roles are `loan_officer` /
> `title_rep` / `title_company` (the comp's `mortgage`/`lender`/`escrow` are
> alias inputs only); (3) the authoritative vendor-user→deal link is
> `transaction_assignments`, joined to `transaction_vendor_assignments` for the
> mortgage/title role; (4) portal date-updates need a small new
> `propose_from_portal()` method because the proposal service currently
> requires an inbound email; (5) tasks carry no scope field today, so scope is
> derived; (6) "invite to portal" reuses the existing `POST /invitations`
> (role `Vendor`). Each fix is marked **[corrected]** at its section.

---

## 0 · How to read this plan

This plan is written so that a real-estate tester (not a developer) can validate
every deliverable through the browser, with the mouse, and with almost no typing.
Each build phase in §12 ends with a **UI Test Script** written for that audience.

The plan is deliberately grounded in what already exists. Before drafting it I
read the prototype Jake handed off, the project requirements and system design,
the live design system, and the actual vendor code already in the backend and
frontend. §1 records that grounding so we never again build on assumptions that
break end-to-end. Where the live app already has a working piece, I reuse it and
say so; I only add new objects when there is a real gap.

A note on style: I write "I will…" for implementation steps because I am the one
building this. I avoid long dashes by preference.

---

## 1 · Grounding (what I reviewed, and the current state)

### 1.1 Documents and source reviewed

- **Prototype (the comp):** `vendor-workspace/src/MortgagePartnerPortal.tsx`
  (2,470 lines), `mortgage-partner-preview.html`, `DEVELOPER_HANDOFF.md`,
  `AGENTS.md`. This is the layout and interaction reference.
- **Product docs:** `requirements.txt`, `SYSTEM_DESIGN.md`,
  `FRONTEND_UI_WORKFLOW_LOGIC.md`, `STYLE_GUIDE.md`, `milestones.txt`,
  `VENDOR_POSITION_IN_TRANSACTION.md`, `VENDOR_COMMUNICATION_SYSTEM_AUDIT.md`,
  `MILESTONE_4_3_IMPLEMENTATION_PLAN.md`, `AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md`.
- **Backend source:** the `vendor*` models (`vendor.py`,
  `transaction_vendor_assignment.py`, `transaction_vendor_assignment_contact.py`,
  `vendor_proposal.py`, `vendor_email_template.py`, `vendor_colleague_token.py`),
  the routers `vendors.py`, `vendor_communications.py`, `vendor_public.py`,
  `transaction_vendor_assignments.py`, the `GET /api/v1/dashboard/vendor`
  endpoint in `dashboard_role.py`, the `UserRole.VENDOR` enum and role hierarchy
  in `models/enums.py`, and the document model.
- **Frontend source:** `App.tsx` routing, `layouts/ClientWorkspaceLayout.tsx`
  (the dedicated-portal pattern I will mirror), `layouts/AppLayout.tsx` +
  `dashboardShellConfig.ts` (current vendor nav), `pages/vendor/VendorDocumentPortalPage.tsx`
  (the thin portal that exists today), the vendor components
  (`AddVendorModal`, `EmailVendorFlow`, `VendorRequestModal`, `VendorContactCard`,
  `VendorProposalCard`, `SaveAsVendorDialog`, `BackgroundRefreshDrawer`) and the
  vendor hooks (`useVendors`, `useVendorAssignments`, `useVendorComms`,
  `useSaveAsVendor`, `useVendorColleagueInvites`, `useVendorBackgroundRefresh`),
  plus `utils/copy.ts` (`VENDOR_BOUNDARY_NOTICE`), `utils/constants.ts`
  (`VENDOR_PORTAL = '/portal/vendor'`), `utils/roles.ts`, `utils/returnLocation.ts`.

### 1.2 Jake's intent (the requirement, in his words)

From Jake's notes, condensed to the rules that drive scope:

**Mortgage Vendor**
- Easy to navigate, easy to complete tasks. View limited to mortgage-related
  tasks and information.
- Doc center: can access documents shared with them; can **request** documents
  not yet shared with them.
- Can **request to close out tasks** by performing an action (upload a document)
  or by leaving a comment ("appraisal was received" — no upload, just a comment).
  **AI then determines whether the task was truly completed and closes it.**
- Contacts: read-only access to contact information, can **add contact(s) to
  their own (mortgage) portion only**. No seller contact information is ever
  shown. A mortgage vendor on a deal represents the buyer side, so seller
  contacts have no reason to appear.

**Title Vendor** (mirror of mortgage, with these differences)
- Sees only title-related tasks and documents.
- Same shared-document access and same task close-out flow.
- Contacts: **full** contact card, read-only, **except** the title portion, where
  they can add contact(s).

My reply to Jake confirmed all of this and flagged that I may ask one or two
small scope questions while wiring it in. Those are collected in §15.

### 1.3 What already exists in the app (so we do not rebuild it)

This is the part prior plans skipped, and it is why earlier builds broke in
testing. The vendor domain is already substantial:

| Capability | Already built | Where |
| --- | --- | --- |
| `Vendor` user role + role hierarchy | Yes | `models/enums.py` (`UserRole.VENDOR`) |
| Vendor companies (durable, cross-deal) | Yes | `vendors` table, `vendors.py`, `useVendors` |
| Per-deal vendor assignment + role + contacts | Yes | `transaction_vendor_assignments(_contacts)`, `transaction_vendor_assignments.py`, `useVendorAssignments` |
| Vendor contact records (`is_vendor=true`, `vendor_id`) | Yes | `contacts`, colleague-invite accept flow |
| Constrained vendor email templates + send/preview | Yes | `vendor_communications.py`, `EmailVendorFlow`, `VendorRequestModal` |
| Vendor reply → task-date **proposal** + internal review queue | Yes (inbound-email origin only) | `vendor_proposal.py`, `vendor_proposal_service.py`, `VendorProposalsPage` |
| Public colleague self-attach (single-use token, creates a **contact**) | Yes | `vendor_public.py`, `/v/:token`, `AddColleaguePage` |
| Invite a counterparty as a portal **user** (role `Vendor`, seat-exempt) | Yes | `invitations.py` (`POST /invitations`, `role=Vendor`, `transaction_id`) |
| Assign a vendor to a deal + email a vendor, **reachable from the UI** | Yes **[corrected]** | `EmailVendorFlow` in `TasksTab` ("Email a vendor") + `TransactionListPage`; `useVendorAssignments`/`SaveAsVendorDialog` in the wizard, `TasksTab`, `TasksFullViewModal` |
| Vendor portal page (thin) + vendor dashboard endpoint | Partial | `VendorDocumentPortalPage`, `GET /dashboard/vendor` |
| Dedicated portal layout pattern to copy | Yes | `ClientWorkspaceLayout` (navy rail, mobile nav) |

> **[corrected]** An earlier draft (and the 2026-05-18
> `VENDOR_POSITION_IN_TRANSACTION.md` audit) said `VendorRequestModal` /
> `useVendorAssignments` were "built but never imported." That is no longer
> true: the email-a-vendor and assignment flows are now reachable from the
> wizard and the transaction workspace. Phase 1 therefore does **not** re-wire
> them; it adds the one thing still missing (a vendor *login* + scope linkage).

**The load-bearing gap.** Today a Vendor user who logs in lands on
`/portal/vendor`, and the `GET /dashboard/vendor` endpoint scopes their view by
"communication_logs where my email is a recipient" plus "documents I uploaded."
The deal-access link actually exists once a vendor is invited: invite-accept
writes a `transaction_assignments` row (`role_in_transaction='vendor'`, the same
table `require_transaction_access` already trusts). **What is missing is the join
from that user to the `transaction_vendor_assignments` row that says which role
(mortgage vs title) they play, and therefore what to scope and what to hide.**
That join runs through the user's `is_vendor` contact (email match) to a
`vendor_id`; it is implicit, can desync, and is never stamped at invite time.
Closing that join deterministically (Phase 0) is what everything else depends on,
and §3.1 specifies it.

The prototype, by contrast, is a self-contained mock with hard-coded loan files
and a separate visual language (IBM Plex Sans, raw `#E26812`/`#2C4C7F`). I take
its **layout, information architecture, and interaction model** as the design
brief, and render it in the **live Velvet Elves design system** (`ve-*` tokens,
Lora serif, the comfort scale). That split (layout from the comp, styling from
the in-app analog) is the house rule and §11 specifies it precisely.

---

## 2 · Product vision and non-negotiable principles

The Vendor Workspace is a **scoped, single-purpose concierge** for an outside
service provider (a mortgage loan officer or a title rep) who is helping one or
more of this brokerage's deals reach closing. It is not a shrunken agent
dashboard. It answers four questions in five seconds, mirroring the Client
portal contract in `AGENTS.md`:

1. Which of my deals need me right now?
2. What exactly is being asked of me, and why?
3. What do I do about it (upload, confirm a date, leave a note)?
4. Who do I contact, and what is already handled?

**Principles (enforced in every phase):**

- **Mouse-first, minimal typing.** Every action completes with clicks and at
  most a short free-text note. Defaults are pre-filled; the vendor confirms
  rather than constructs. (`STYLE_GUIDE.md` v2.6.)
- **Scope is a wall, not a filter.** A vendor sees only their role's tasks and
  documents and only the contacts their role is allowed to see. Scope is
  enforced on the **backend**, not just hidden in the UI. The boundary notice
  (`VENDOR_BOUNDARY_NOTICE`) is shown on every surface.
- **One parametric workspace, two configurations.** Mortgage and Title are the
  same code path driven by the vendor's assignment role. This avoids a forked
  codebase and guarantees the two views stay consistent.
- **Honest empty states, real data only.** No mock loan files on a real surface
  (per the standing "no demo data" rule). Where testers need data, §13 seeds a
  real demo vendor behind an explicit flag.
- **AI shows its work and never lies.** When AI judges a task complete it shows
  its confidence and reasoning; below the auto-close threshold it routes to a
  human instead of silently closing. When the configured AI provider is down,
  the UI says so honestly and falls back to human review.
- **Every deliverable is UI-validatable end to end.** A tester can set up a deal,
  assign and invite a vendor, log in as that vendor, and complete the loop
  without touching an API or the database.

---

## 3 · The architecture decision that makes the rest work: vendor scope resolution

### 3.1 How a Vendor user is linked to their deals

A Vendor user authenticates like any other user (Supabase auth, `UserRole.VENDOR`,
a `tenant_id`, an `email`). The scope resolver answers: **which transactions, in
which role, can this vendor user act on?**

**[corrected] Two links, combined.** There is no single table that says
"this vendor user, on this deal, plays the mortgage role." The resolver derives
it from two existing links and must reconcile them:

```
A) DEAL ACCESS (authoritative, user-linked — written at invite-accept):
   vendor_user.id
      └─► transaction_assignments (user_id, role_in_transaction='vendor', is_active)
             └─► transactions (status in Active/…)            → the deals

B) SCOPE ROLE (mortgage vs title — derived through the vendor company):
   vendor_user.email
      └─► contacts (is_vendor=true, email = vendor_user.email) → vendor_id(s)
             └─► transaction_vendor_assignments (vendor_id, transaction_id, is_active)
                    → role  (per the deal in A)
```

Link **A** is the gate (a deal the vendor was not invited to is never visible,
even if their company is assigned). Link **B** supplies the mortgage/title role
for the deals in A. To make B deterministic rather than email-dependent, Phase 0
**stamps the resolved `vendor_id`/`assignment_id` at invite time**. The
`transaction_assignments` model has no field for this today, so this is a small
migration: a nullable `vendor_assignment_id` column on `transaction_assignments`
(written when a `role=Vendor` invite is accepted). The email→`is_vendor`-contact
join remains as the fallback for rows created before the stamp exists, so a
renamed or re-cased email cannot silently strip a vendor's scope. (If we want to
ship v1 with zero migration, the email-join + the A/B-disagree fallback below is
sufficient on its own; stamping is the durability upgrade. See J6.)

**[corrected] Role vocabulary.** `transaction_vendor_assignments.role` is free
`TEXT` (no DB check constraint). The values the app actually writes come from
`SaveAsVendorDialog` / `AddContactModal`: `loan_officer`, `title_rep`,
`title_company` (plus `inspector`, `appraiser`, `home_warranty`,
`closing_attorney`). The comp's `mortgage` / `lender` / `escrow` are **alias
inputs** in `party_roles.PARTY_ROLE_ALIASES` that normalize to the canonical
values; they are never stored. The resolver therefore normalizes the role with
the same `normalize_party_role()` helper before mapping it:

| Normalized `assignment.role` | Scope family | Workspace label |
| --- | --- | --- |
| `loan_officer` | **Mortgage** | "Loan Files" |
| `title_rep`, `title_company` | **Title** | "Title Files" |
| `inspector`, `appraiser`, `home_warranty`, `closing_attorney`, other | Generic (future, see J5) | "Your Files" |

A single vendor company can be Mortgage on one deal and something else on
another; scope is resolved **per (deal, assignment)**, never globally. The same
person can belong to two vendor companies; the resolver unions across `vendor_id`s.

When A and B disagree (the vendor user is invited to a deal but no matching
`transaction_vendor_assignment`/contact exists yet), the resolver grants deal
access from A and shows an honest "your role on this file is being set up"
state rather than guessing mortgage vs title or leaking the wrong contacts.

I will implement this as one backend service, `VendorScopeService`
(`app/services/vendor_workspace.py`, new), with a single entry point
`resolve(vendor_user) -> VendorScope` returning the list of
`(transaction, assignment, role, scope_family)` tuples. Every vendor-facing
endpoint calls it first and 403s on anything outside the returned set. This is
the same shape as `client_workspace.py` and `fsbo_workspace.py`, so it fits the
existing pattern.

### 3.2 Mortgage vs Title scope mapping (tasks and documents)

A vendor must see only the tasks and documents that belong to their scope
family. I define the mapping in two layers, defensive by default:

**Layer 1 — explicit association always wins.** A task or document is visible to
a vendor only if it is associated with that vendor's assignment. **[corrected]**
The association is not hypothetical: it already exists in the data. A vendor
request sent from `EmailVendorFlow`/`VendorRequestModal` writes a
`communication_logs` row whose `metadata_json` carries `task_id` + `vendor_id` +
`assignment_id` (see `vendor_communications.send`). That row is the authoritative
"this task was put in front of this vendor" signal. A document is associated when
the vendor uploaded it (`documents.uploaded_by = vendor_user.id`) or an internal
user shared it to the assignment (§6.4). This is the wall and it guarantees no
accidental leak even if the category map below is imperfect.

**Layer 2 — scope family (derived, because no task field exists yet).**
**[corrected]** The `tasks` table has **no** `vendor_scope`/category column today
(it has `name`, `milestone_label`, `target`, `completion_method`). So scope is
*derived*, not read: from the task's `milestone_label`/`name` keywords
(appraisal/financing/loan → mortgage; title/settlement/recording/CD → title) and,
more reliably, from the normalized role of the assignment the task was sent to
(Layer 1). For documents, scope is derived from `doc_type` (the default map
below). This derivation only orders and groups what Layer 1 already permits; it
never widens visibility. A real, admin-authored `vendor_scope` column on tasks /
templates is net-new work and is scheduled in Phase 5, not assumed here.

Default document-type map (admin-curatable in a later phase; explicit per-document
shares override it):

| `vendor_scope` | `documents.doc_type` (from `enums.DocumentType`) |
| --- | --- |
| Mortgage | `pre_approval`, `closing_disclosure`, `earnest_money`, `wire_transfer_authorization` (handled as sensitive, see §9.3) |
| Title | `title_work`, `title_commitment`, `settlement_statement`, `affidavit`, `deed`, `recording_packet`, `signed_amendment`, `power_of_attorney` |
| Both (shareable to either, agent's choice) | `purchase_agreement`, `amendment`, `addendum`, `counter_offer`, `home_warranty`, `insurance` |
| Internal (never auto-listed to a vendor) | everything else, including raw extraction artifacts |

Default task scope: tasks carry (or inherit from their `task_template`) a
`vendor_scope`. Until the task engine exposes that field cleanly (see
`SMART_TRANSACTION_PROCESSING_AND_TASK_ENGINE_PLAN.md`), I derive scope from the
task's linked document requirement / category and from any existing vendor
assignment on the task. Phase 5 adds an admin mapping screen; Phases 2 to 4 ship
with the deterministic default map plus explicit per-assignment association.

### 3.3 Contact visibility matrix (the most sensitive rule)

This is where Mortgage and Title differ, and it is enforced server-side.

| Contact group | Mortgage vendor | Title vendor |
| --- | --- | --- |
| Buyer (principal) | Read-only | Read-only |
| Buyer's agent | Read-only | Read-only |
| Listing / seller's agent | Read-only | Read-only |
| **Seller (principal)** | **Hidden** | Read-only |
| Title company / escrow | Read-only | Read-only **except own section** (can add) |
| Mortgage / lender | Read-only **except own section** (can add) | Read-only |
| Other vendors | Hidden | Hidden |
| Internal team (TC, team lead, admin) | Show only the **named point of contact** (the agent + coordinator on the deal), not the full roster | Same |

"Own section" means: a mortgage vendor may add or edit contacts only within the
mortgage/lender group on the deals they are assigned to; a title vendor only
within the title/escrow group. The add-contact action reuses the colleague
pattern (a `contacts` row with `is_vendor=true`, `vendor_id`, linked to the
assignment) so it flows back into the internal contact directory cleanly.

**[corrected] Two contact sources, one filter.** The deal's people come from two
tables: contract parties live in `transaction_parties` (`party_role` of
buyer/seller/listing_agent/buyers_agent), while vendor contacts live in
`contacts` (`is_vendor=true`) linked through
`transaction_vendor_assignment_contacts`. The serializer in `visible_contacts`
must merge both and apply the matrix to each. The Mortgage "no seller" rule
therefore filters the seller out of **both** sources: any
`transaction_parties.party_role = 'seller'` row and any `contacts` row whose
`contact_type = ContactType.SELLER`. The filtered payload never leaves the
server, so the frontend cannot leak it.

---

## 4 · Information architecture and navigation

### 4.1 A dedicated layout, not AppLayout

Like the Client portal, the Vendor Workspace gets its own shell,
`VendorWorkspaceLayout` (`src/layouts/VendorWorkspaceLayout.tsx`, new), modeled
1:1 on `ClientWorkspaceLayout`: a deep-navy rail (`ve-sidebar #1E3356`), the VE
logo + serif wordmark with a "Vendor Portal" mono descriptor, a vertical nav, a
bottom user chip with Profile / Log out, a mobile off-canvas drawer, and a mobile
bottom nav. This satisfies the standing rule that portal redesigns are distinct
surfaces with their own chrome, not folded into AppLayout. The current
AppLayout-mounted `VendorDocumentPortalPage` is retired (its route is preserved,
see §4.3). **[corrected]** Because the vendor portal currently renders *inside*
AppLayout, moving it out also means removing the now-orphaned vendor entries in
`dashboardShellConfig.ts` (the `Vendor` shell config, "Document Requests" / "My
Uploads" nav) and the vendor branch in `AppLayout.tsx`, so there is no dead nav
or duplicate shell left behind. That cleanup is part of Phase 2.

### 4.2 Navigation (parametric by scope family)

The comp's nav is **Loan Files / Documents / Tasks**. I keep that spine and add a
Home/Overview entry, and I relabel "Loan Files" to "Title Files" for title
vendors. The nav config is derived from the vendor's scope family.

| Nav item | Route | Mortgage label | Title label |
| --- | --- | --- | --- |
| Overview | `/portal/vendor` | Overview | Overview |
| Files | `/portal/vendor/files` | Loan Files | Title Files |
| Documents | `/portal/vendor/documents` | Documents | Documents |
| Tasks | `/portal/vendor/tasks` | Tasks | Tasks |

Mobile bottom nav: Home · Files · Docs · Tasks · More (mirrors the client mobile
pattern). Using real routes (not the comp's in-page section state) makes every
surface deep-linkable and independently testable, and lets notifications link
straight to a task or document.

### 4.3 Route + role gating

All four routes are gated `<RoleRoute allowedRoles={['Vendor']}>` and mounted
under `VendorWorkspaceLayout`, parallel to the client route group in `App.tsx`.
`utils/returnLocation.ts` and `dashboardShellConfig.ts` already treat
`VENDOR_PORTAL` as the vendor landing route; I extend `isAllowedForRole` so the
three new sub-routes are also vendor-allowed, and I keep `/portal/vendor` as the
Overview so existing links and the `?panel=upload` / `?view=uploads` deep links
keep working (forwarded to Documents).

---

## 5 · The vendor-facing surfaces (page by page)

Each surface below maps a section of the comp to a real, scoped, data-backed page.

### 5.1 Overview (Home)

Mirrors the comp's hero band + "Needs Attention" + assigned-files summary.

- **Hero band** (navy, matches comp): greeting by name, role chip
  ("Mortgage Loan Officer" / "Title & Escrow"), and three stat tiles computed
  from real scope: assigned files, open documents needed, items needing
  attention. No invented numbers; tiles read 0 with an honest empty state.
- **Needs Attention**: up to four urgent cards (overdue task, requested document,
  date confirmation, an open request). Each card's primary button deep-links to
  the exact task/document. This is the "five second" answer.
- **Your files**: a compact list of the vendor's assigned deals (address, buyer
  for mortgage, milestone chip, count of open items), each linking to the file
  detail. Empty state: "No active files are shared with you yet."

### 5.2 Files (Loan Files / Title Files)

The comp's expandable loan card, rebuilt with real data and scoped panels. Each
file card shows address, a milestone timeline, key date tiles, and the "next
step" callout. **[corrected]** The comp's seven fixed stages (Contract → EM →
Inspection → Appraisal → CD → CTC → Close) are a presentation device, not a
guaranteed data model: the app tracks progress through tasks' `milestone_label`
and the transaction's key dates, not a fixed seven-stage pipeline. So I render
the timeline from the real `milestone_label` values and key dates present on the
deal and degrade gracefully (fewer stages, or a simple "in progress" state) when
a stage has no backing data, rather than hard-coding the comp's labels. On expand
the card reveals three panels plus a document area and an activity area:

- **Tasks panel**: this vendor's open tasks on this deal (scoped), grouped
  Overdue / Upcoming, each with the close-out action (§8).
- **Key dates panel**: read-only dates relevant to the vendor's scope, with a
  single "Submit a date update" affordance that creates a date proposal (reuses
  the existing vendor-proposal pipeline, §8.4).
- **Contacts panel**: the visibility matrix from §3.3, with an "Add to my
  section" button when allowed.
- **Document area**: documents shared on this deal within scope, plus upload and
  "Request a document" (§9).
- **Activity area**: the request/response history for this deal scoped to the
  vendor (from `communication_logs` where the vendor is a participant), plus a
  short note composer that routes to the deal's coordinator.

### 5.3 Documents

The comp's documents page: a priority hero, a "today's briefing" count card,
status filter tabs (Needs attention / All / Requested / Uploaded / Reviewed /
Accepted), and documents grouped by file. Two real sources only: documents
**shared to this vendor** and documents **this vendor uploaded**. The review
modal shows a real preview when the document service returns one, an honest
placeholder otherwise, and a "Forward to" list limited to the contacts the
vendor is allowed to see. Upload reuses `UploadIntakeCard` + `useUploadDocument`,
which already route an upload to the right transaction.

### 5.4 Tasks

The comp's grouped, expandable task list across all the vendor's files. Each task
expands to show: why it matters, who requested it, what it relates to, the due
date, and the route its completion request will take. The action set is the
close-out flow in §8. A header summary shows counts (need action / waiting /
done) computed from real scope.

---

## 6 · Backend plan

New objects are kept minimal and justified. Reuse-first.

### 6.1 New service: `VendorScopeService` (Phase 0)

`app/services/vendor_workspace.py`. Resolves a vendor user to their
`(transaction, assignment, role, scope_family)` set (§3.1), and exposes helpers:
`visible_tasks(scope)`, `visible_documents(scope)`, `visible_contacts(scope, family)`
(applies the §3.3 matrix and strips seller contacts for mortgage),
`assert_can_act_on(scope, transaction_id)`.

### 6.2 New router: `vendor_workspace.py` (Phases 2 to 6)

`app/api/v1/vendor_workspace.py`, mounted under the API prefix as
`/api/v1/vendor-portal` (named with a hyphen so it does not read as the SPA route
`/portal/vendor`), every route guarded by `require_exact_roles(UserRole.VENDOR)`
(this dependency exists in `core/auth.py`) and scope-checked via
`VendorScopeService`. This supersedes the thin data in `GET /dashboard/vendor`
(which I keep returning, populated from the real scope now, so nothing that
consumes it breaks):

- `GET  /overview` — hero stats, needs-attention, file summaries.
- `GET  /files` — assigned files with milestone + counts.
- `GET  /files/{transaction_id}` — one file with scoped tasks, dates, contacts,
  documents, activity. 403 if outside scope.
- `GET  /documents` — shared-to-me + my-uploads, with status + scope grouping.
- `POST /documents/request` — vendor requests a document not yet shared (§9).
- `GET  /tasks` — scoped tasks across files.
- `POST /tasks/{task_id}/completion-request` — upload- or comment-based close-out
  request (§8). Body: `{ kind: 'document' | 'comment', note?, document_id? }`.
- `POST /contacts` — add a contact to the vendor's own section (scope-checked to
  the mortgage/title group, §3.3).
- `POST /date-update` — submit a date update (creates a vendor proposal, §8.4).

### 6.3 New lightweight table: `vendor_task_actions` (Phase 5)

The close-out request needs a durable record and an internal review queue.
Rather than overload `vendor_proposals` (which is typed for date proposals), I
add `vendor_task_actions`:

```
vendor_task_actions
  id, tenant_id, transaction_id, task_id, vendor_id, assignment_id,
  created_by (vendor user), kind ('document'|'comment'),
  note (text|null), document_id (fk|null),
  ai_verdict ('complete'|'incomplete'|'uncertain'|null),
  ai_confidence (float|null), ai_reasoning (text|null),
  status ('pending'|'auto_completed'|'approved'|'rejected'|'needs_info'),
  decided_by (user|null), decided_at, created_at, updated_at
```

This mirrors the `vendor_proposals` shape and review lifecycle, so the internal
review queue and the audit trail reuse established patterns. (Alternative
considered: a `proposal_type` column on `vendor_proposals`. I rejected it because
the date-proposal service has date-specific logic that would get muddy. If Jake
prefers consolidation I can revisit, see J3.)

### 6.4 Document sharing to a vendor assignment (Phase 4)

To honor "documents shared with them," sharing must be explicit. I add a thin
join recorded in document `metadata_json.shared_with_assignments: [assignment_id]`
(no new table needed initially), written by the internal "Share to vendor" action
and by the vendor-request approval. `visible_documents(scope)` reads it. If we
later need richer share semantics (revocation, audit per share), I promote it to a
`document_vendor_shares` table; the read path stays the same.

### 6.5 AI verification (Phase 6)

A new method on the existing AI layer, `verify_task_completion(task, evidence)`,
in `app/services/ai_service.py` (or a small `vendor_task_verifier.py` that calls
it), returning `{verdict, confidence, reasoning}`. Evidence is the uploaded
document's classification + extracted fields (already produced by
`document_processing.py`) and/or the vendor's comment, evaluated against the
task's definition and any document requirement. It uses the tenant's
**configured** AI provider (never an auto-switch) and the existing
confidence-tier settings (`confidence_settings.py`, `agent_policy.py`) to decide
auto-close vs human review. On provider error it returns a clean failure and the
action stays `pending` for a human, surfaced honestly in both UIs.

### 6.6 Internal-side wiring (Phase 1)

No new backend needed. **[corrected]** The assignment and email-vendor flows are
already wired into the wizard and the transaction workspace (see §1.3), so this
phase does not re-wire them. The genuine gap is turning an assignment contact
into a **logged-in Vendor user** and stamping the scope linkage (§3.1, link B).
Inviting reuses the **existing** `POST /api/v1/invitations` endpoint, which
already accepts `role=Vendor` + `transaction_id` and is seat-exempt for portal
roles (`invitations.py`); I do not add a new invite endpoint. I add only a thin
UI affordance ("Invite to portal") on an assignment contact that calls it with
the primary contact's email (so the resulting user's email matches the
`is_vendor` contact), plus a small Phase 0 step that records the resolved
`vendor_id`/`assignment_id` on the created `transaction_assignments` row so role
resolution is deterministic rather than email-dependent.

### 6.7 Notifications and audit

Every vendor action (upload, completion request, document request, contact added,
date update) writes a `communication_logs` / notification row to the deal's
coordinator and an `audit_logs` entry, reusing `task_notification_service.py`,
`notification_prefs_service.py`, and `audit_service.py`. Every internal decision
(approve/reject a completion request, share a document) notifies the vendor.

---

## 7 · Frontend plan

### 7.1 New files (all under the live design system)

- `src/layouts/VendorWorkspaceLayout.tsx` (navy rail, parametric nav, mobile nav).
- `src/pages/vendor/VendorOverviewPage.tsx`
- `src/pages/vendor/VendorFilesPage.tsx` and `VendorFileDetailPage.tsx`
- `src/pages/vendor/VendorDocumentsPage.tsx`
- `src/pages/vendor/VendorTasksPage.tsx`
- Components in `src/components/vendor-portal/`: `VendorFileCard`,
  `MilestoneTimeline`, `VendorTaskCard`, `TaskCompletionDialog`,
  `RequestDocumentDialog`, `VendorContactsPanel`, `AddVendorContactDialog`,
  `DocumentReviewDrawer`, `VendorActivityFeed`, `NeedsAttentionGrid`.
- Hooks in `src/hooks/`: `useVendorOverview`, `useVendorFiles`,
  `useVendorFileDetail`, `useVendorTasks`, `useVendorTaskAction`,
  `useVendorDocumentRequest`, `useAddVendorContact`. These wrap the §6.2 endpoints
  through the existing `utils/api` client and React Query, matching the client
  hooks' conventions.

### 7.2 Reuse

`UploadIntakeCard`, `useUploadDocument`, `Skeleton`, `useToast`, the confirm
dialog, the Account modal (Profile / Log out from the user chip), the status-pill
and chip primitives. On the internal side I reuse `VendorRequestModal`,
`useVendorAssignments`, `AddVendorModal`, `SaveAsVendorDialog`,
`VendorProposalCard`, and the proposals queue pattern.

### 7.3 State, loading, error, empty

Every async surface gets a skeleton, an honest empty state (the §13 copy), and an
error state with a retry. No surface shows a number it cannot back with data.
The boundary notice footer (`VENDOR_BOUNDARY_NOTICE`) appears on every page.

---

## 8 · The task close-out flow (with AI verification)

This is the heart of Jake's request. The flow is identical for Mortgage and
Title; only scope differs.

### 8.1 What the vendor sees

On any open task, the vendor has two ways to ask for it to be closed, both
mouse-first:

1. **Upload to complete.** Click "Upload & request complete," drop the file. The
   upload attaches to the task's transaction (reusing `useUploadDocument`), and a
   `completion-request` of kind `document` is created referencing the new
   `document_id`.
2. **Comment to complete.** Click "Mark done with a note," pick a suggested
   reason chip (for example "Appraisal received," "Title commitment issued",
   "Cleared to close") or type a short note, and submit. This creates a
   `completion-request` of kind `comment`. No upload required (Jake's
   "appraisal was received" case).

The task immediately shows a "Submitted for review" state with an inline Undo
(undoable per the comfort-scale rule) until AI or a human acts.

### 8.2 What AI does

`verify_task_completion` evaluates the evidence against the task:

- **Confident complete** (at or above the tenant's auto-close tier): the task is
  set to `Completed`, the action is `auto_completed`, the vendor sees a confirmed
  state with the AI confidence chip ("Closed by AI · 95%") and reasoning on
  expand, and the coordinator is notified.
- **Uncertain / below tier**: the action stays `pending` and lands in the
  internal review queue with the AI's recommendation and confidence shown. The
  vendor sees "Sent to the team for confirmation."
- **Incomplete**: AI explains, in plain language, what is still missing, and the
  vendor can act again. Nothing is closed.

AI never silently closes below the configured tier, and a provider outage degrades
to human review with an honest message, consistent with the standing AI rules.

### 8.3 What the internal team sees

A review queue (the existing Vendor Proposals page pattern, extended or a sibling
tab "Task completions") lists pending `vendor_task_actions` with the evidence, the
AI verdict + confidence + reasoning, and one-click Approve (closes the task) /
Reject (with a reason that returns to the vendor) / Ask for more. Approve and
reject both notify the vendor and write audit entries.

### 8.4 Date updates reuse the proposal *review* queue, with a new creation path

"Submit a date update" from the Key Dates panel creates a vendor date
**proposal** that lands in the already-built `VendorProposalsPage` queue with
accept/reject. **[corrected]** This is not zero-change: the only creation method
on `VendorProposalService` today is `propose_from_vendor_reply(...,
inbound_log_id: str, ...)`, which requires an inbound email and so cannot serve a
portal-originated update. I add a small sibling, `propose_from_portal(...)`, that
writes a `vendor_proposals` row with `inbound_log_id = NULL` (the column is
already nullable), the proposed date, and `metadata_json.origin = 'portal'`. The
existing `accept` / `reject` / `needs_clarification` lifecycle and the
`VendorProposalsPage` queue are reused unchanged; only the creation entry point
is new. The queue UI gets a small "via portal" origin chip so reviewers can tell
a portal submission from an email-parsed one.

---

## 9 · The request-a-document flow

### 9.1 Vendor side

From the Documents surface or a file's document area, "Request a document" opens a
dialog: pick a document type from the vendor's scope list (§3.2) or choose
"Something else" and type a short label, optionally add a one-line reason, submit.
This calls `POST /portal/vendor/documents/request`, which records the request and
notifies the deal's coordinator. The vendor sees the request in an "Awaiting"
state.

### 9.2 Internal side

The coordinator gets a notification and an inline action: if the requested
document already exists and is in scope, "Share to vendor" is one click (writes
the §6.4 share association and notifies the vendor). If it does not exist, the
request becomes a normal task/checklist item for the team. Either way the vendor's
"Awaiting" turns into "Shared" or "In progress" with no dead ends.

### 9.3 Sensitive documents

Wire-transfer authorizations and anything carrying bank or routing detail are
never auto-listed and never one-click shareable to a vendor; they require an
explicit internal confirmation step. This protects against the wire-fraud surface
called out across the security docs.

---

## 10 · Contacts: add to your own section

Per §3.3, a mortgage vendor can add contacts only to the mortgage/lender group; a
title vendor only to the title/escrow group. "Add to my section" opens a tiny
form (name, email, optional phone, role within the section). On submit it creates
a `contacts` row (`is_vendor=true`, `vendor_id`, linked to the assignment) and a
`transaction_vendor_assignment_contacts` link, reusing the colleague-add data path
so the new contact appears in the internal directory too. All other contacts are
read-only, and the seller group is absent entirely for mortgage vendors.

---

## 11 · Design system and visual specification

The comp's look (IBM Plex Sans, raw `#E26812` / `#2C4C7F`, very round 3xl cards)
is **not** shipped as-is. I take the comp's **layout and interaction** and render
it in the **live Velvet Elves system** (`STYLE_GUIDE.md`), exactly as the Client
and Attorney portals do. Concretely:

| Element | Comp | Shipped (VE system) |
| --- | --- | --- |
| Body font | IBM Plex Sans | `font-sans` (IBM Plex Sans) — same family, via token |
| Titles | Plex Sans black | `font-serif` (Lora), section titles serif 20px semibold |
| Kickers / labels | Plex Sans uppercase | `font-mono` 12px, 1.5px tracking, `ve-text-ghost` |
| Primary accent | `#E26812` literal | `ve-orange` token (same hue, tokenized) |
| Sidebar navy | `#2C4C7F` literal | `ve-sidebar` `#1E3356` (the app rail navy) |
| Cards | `rounded-3xl`, heavy shadow | 12px radius, single `shadow-card`, hairline `ve-border` |
| Status pills | ad hoc tones | the `ve-*` status triads (bg+border+text), min 12px |
| Page background | `#F4F4F4` | `ve-bg` `#F4F4F4` |
| Vendor accent | n/a | `ve-purple` triad (the app's vendor color) for vendor chips |

Hard rules carried from the style guide: nothing below 12px; no meaning carried by
the smallest size; muted ink only at 14px and larger; 48px interactive minimum;
mouse-first; one soft shadow; whitespace separates, borders only group. The
Calendar page is the in-app modernity benchmark for header, cards, pills, and
stat tiles, and I match its rhythm. Internal vendor pages keep the breadcrumb
header convention; the vendor portal, being a standalone concierge surface like
the client portal, uses the portal header pattern instead.

I will not build any of this blind. Every page is rendered and screenshotted with
the headless-Chrome method and compared against the comp's layout before it is
called done (the standing visual-verification rule).

---

## 12 · Phased delivery (each phase is independently UI-testable)

Phases are ordered so the **setup loop is testable before the vendor-facing build**,
which is what keeps end-to-end from breaking. Everything ships behind the flag
`ve_vendor_workspace_v1` (off in production until Jake approves), following the
existing flag pattern.

### Phase 0 — Scope foundation (backend, no visible UI)
- `VendorScopeService` (§3.1, §6.1): combine link A (`transaction_assignments`,
  role `vendor`) with link B (`transaction_vendor_assignments` via the
  `is_vendor` contact), with role normalization (`normalize_party_role`) and the
  A/B-disagree fallback. Scope-family derivation; the §3.3 two-source contact
  filter; the §3.2 derived maps; `ve_vendor_workspace_v1` flag.
- **Stamp the linkage at invite time** so role resolution is deterministic: a
  small migration adds a nullable `vendor_assignment_id` to `transaction_assignments`,
  written when a `role=Vendor` invite is accepted (email-join fallback retained;
  see J6). This is the only migration before Phase 5.
- Repopulate `GET /dashboard/vendor` from real scope so the existing portal stops
  showing only email-matched messages.
- **UI test:** none yet (covered by Phase 1's loop). Backend tests assert a
  mortgage vendor never receives seller contacts (from **either** source), never
  sees out-of-scope tasks/documents, and that a role written as the alias
  `mortgage`/`lender` still resolves to the Mortgage family.

### Phase 1 — Internal setup loop (so testers can create a vendor login)
- **[corrected]** The assignment + email-vendor flows are already reachable from
  the wizard and `TasksTab` ("Email a vendor"), so this phase adds only what is
  missing: an **"Invite to portal"** affordance on an assignment contact that
  calls the existing `POST /api/v1/invitations` with `role=Vendor` +
  `transaction_id` (§6.6), and surfaces the contact's invite state. Where the
  assignment panel itself is thin, I extend it in place rather than rebuild it.
- **UI Test Script (tester):**
  1. Open an active transaction; confirm the vendor it is assigned to (or assign
     one: choose a company and role "Mortgage").
  2. On the vendor's primary contact, click "Invite to portal."
  3. Confirm the invite email arrives and the contact shows "Invited."
  Pass = you turned an assigned mortgage vendor into an invited portal user
  entirely by mouse.

### Phase 2 — Vendor shell + Overview + Files list (read-only)
- `VendorWorkspaceLayout`, routes, parametric nav, Overview page, Files list.
- **UI Test Script:**
  1. Accept the invite from Phase 1, set a password, land on the Vendor Overview.
  2. Confirm the greeting, the role chip ("Mortgage Loan Officer"), and three
     stat tiles that match the deal you were assigned.
  3. Click your file; confirm address and milestone show. Confirm no other
     brokerage deals are visible.
  Pass = a vendor sees exactly their assigned deal and nothing else.

### Phase 3 — File detail (dates, contacts, milestone) read-only
- File detail with key dates, the contacts panel honoring §3.3, the milestone
  timeline, and the scoped activity feed.
- **UI Test Script (mortgage):**
  1. Open your file, expand it.
  2. Confirm the buyer and agents appear and **the seller does not**.
  3. Confirm key dates relevant to mortgage are shown.
  Repeat invited as a **title** vendor and confirm the seller **does** appear and
  only the title section is editable.
  Pass = the contact matrix is correct for both types.

### Phase 4 — Documents (shared + uploads + request a document)
- Documents page, review drawer, upload, "Request a document" (§9), internal
  "Share to vendor" one-click.
- **UI Test Script:**
  1. As internal user, share a mortgage document to the vendor.
  2. As vendor, see it appear under "Shared with you," open the review drawer.
  3. As vendor, click "Request a document," choose "Pre-approval letter," submit.
  4. As internal user, see the request and click "Share."
  5. As vendor, confirm it flips from "Awaiting" to "Shared."
  Pass = the share + request loop works both directions by mouse.

### Phase 5 — Tasks + close-out request (human review, no AI yet)
- Tasks page, `TaskCompletionDialog` (upload-to-complete and comment-to-complete),
  the `vendor_task_actions` record, the internal review queue (approve/reject).
- **UI Test Script:**
  1. As vendor, open a task, click "Mark done with a note," pick "Appraisal
     received," submit; confirm "Sent to the team."
  2. As internal user, open the review queue, see the note, click "Approve."
  3. As vendor, confirm the task now shows Completed.
  Pass = a vendor can request closure and a human can confirm it, by mouse.

### Phase 6 — AI verification (auto-close above tier, honest fallback)
- `verify_task_completion`, confidence-tier auto-close, AI verdict shown in both
  UIs, provider-outage fallback to human review.
- **UI Test Script:**
  1. As vendor, upload the document a task asks for, click "Upload & request
     complete."
  2. Confirm the task closes with "Closed by AI · NN%" and, on expand, a reason.
  3. Submit a vague note on another task; confirm it does **not** auto-close and
     routes to the team instead.
  Pass = AI closes only when confident and otherwise defers to a human, visibly.

### Phase 7 — Add-contact (own section) + activity notes + polish
- `AddVendorContactDialog` scoped to the vendor's section, the deal note composer,
  notifications both directions, audit entries, empty/loading/error states across
  all surfaces, mobile nav, accessibility pass.
- **UI Test Script:**
  1. As mortgage vendor, "Add to my section," add a loan processor; confirm it
     appears and the internal directory shows it too.
  2. Confirm you cannot add to any other section.
  Pass = section-scoped contact editing works and stays inside the wall.

### Phase 8 — QA, screenshots, acceptance
- Render + screenshot every surface (desktop + mobile), compare to the comp
  layout, fix drift; full regression of frontend + backend suites; finalize the
  testing guide (a sibling `VENDOR_WORKSPACE_TESTING_GUIDE.md`) and the Jake
  screenshot gate.

---

## 13 · Seed and demo-data strategy (real data, flag-gated)

No mock loan files on a real surface. For testers, I add an opt-in seed (behind
`ve_vendor_workspace_v1` plus an explicit `seed_vendor_demo` switch) that creates
**real** rows: a demo vendor company, a real assignment on a real demo
transaction, a real invited vendor contact, one shared document, and two open
tasks. Because these are real records flowing through the real endpoints, what the
tester validates is exactly what a production vendor would experience. Outside the
demo switch, every surface shows honest empty states.

---

## 14 · Testing and acceptance

- **Backend:** unit tests for `VendorScopeService` (the scope wall, the seller-hide
  rule, the scope maps), the close-out lifecycle, the AI-verdict tiering (mocked
  provider, including the outage path), and the document-share read path.
- **Frontend:** component tests for the contact matrix, the task dialog states,
  and the request-document states; route-guard tests that a Vendor cannot reach
  internal routes and a non-vendor cannot reach the portal.
- **End-to-end (the tester scripts in §12):** each phase is signed off only when
  its mouse-first script passes in the browser with real data.
- **Acceptance gate:** Jake reviews desktop + mobile screenshots of all four
  surfaces for both vendor types, plus the internal setup and review screens.

---

## 15 · Open questions for Jake (small, scoped)

- **J1 — Title "full contact card."** Confirm the title vendor's read-only "full"
  card still **excludes other outside vendors** (inspector, appraiser, etc.) and
  shows internal staff only as the named point of contact, not the full roster.
  (My §3.3 assumes yes.)
- **J2 — Mortgage and the closing disclosure / wire authorization.** Confirm a
  mortgage vendor should see the Closing Disclosure when shared, and that
  wire-transfer authorizations are never one-click shareable to them (§9.3).
- **J3 — AI auto-close authority.** Should AI be allowed to close a task outright
  above the confidence tier (my default), or should **every** vendor close-out
  always require a one-click human confirmation, with AI only recommending?
- **J4 — Scope of date updates.** Confirm vendors submit date **proposals**
  (reviewed before they change the deal), never direct date writes (my §8.4
  assumption).
- **J5 — Vendor types beyond mortgage/title.** Inspector/appraiser/etc. exist as
  vendor roles. Do you want the generic "Your Files" config live now, or should
  the portal admit only Mortgage and Title for the first release?
- **J6 — Scope-link durability (small migration vs none).** I recommend the small
  `transaction_assignments.vendor_assignment_id` stamp (§3.1) so a vendor's
  mortgage/title scope never depends on a stable email. The zero-migration
  alternative is the email→contact join plus the A/B-disagree fallback. Confirm
  you are fine with the one small migration; it is the only schema change before
  the Phase 5 close-out table.

---

## 16 · Out of scope (for this build)

- Vendor-to-vendor messaging, vendor billing/invoicing inside the portal, and any
  cross-tenant vendor identity.
- Editing the task engine's categorization model itself (I consume it; the admin
  scope-map screen in Phase 5 is the only authoring surface I add).
- Mobile native apps (the portal is responsive web, matching the client portal).

---

## 17 · Why this plan does not break in testing (the summary)

1. It is built on the **real** vendor data model and the **real** auth role, not a
   mock, and it closes the one missing link (vendor user to assignment) first.
2. The **setup loop is testable before the vendor build**, so a real-estate tester
   can create the exact conditions every later phase needs, by mouse.
3. **Scope is a server-side wall**, so the seller-hide and mortgage/title rules
   cannot leak through a UI bug.
4. Every phase is a **complete vertical slice** with a mouse-first acceptance
   script, so we never hand testers a half-wired surface.
5. The look is the **live design system**, so the workspace lands as part of
   Velvet Elves, not a bolt-on, and is verified by screenshot before sign-off.
