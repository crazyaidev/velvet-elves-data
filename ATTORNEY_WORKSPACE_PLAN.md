# Attorney Workspace — Functional & UI Plan (rev 3)

## Review corrections in rev 3

- **Topbar AI briefing corrected.** The current shell disables the shared
  AI briefing bar for Attorney (`dashboardShellConfig.ts` sets
  `showAiBriefingBar: false`). This plan no longer claims an attorney
  briefing chip is already wired through `useAttorneyDashboard`.
- **Topbar upload CTA corrected.** The Attorney `upload-legal-packet`
  primary-CTA branch already exists, but it currently navigates to
  `/dashboard/attorney?panel=upload`. The fix is to retarget it to
  `/attorney/intake`, not to add a new branch.
- **URL tabs standardized.** Attorney matter-list deep links use the
  UI tab keys (`?tab=needs-review`, `?tab=missing-docs`,
  `?tab=ready-to-release`, `?tab=clean-files`) and map those keys to
  API tab values (`needs_review`, etc.) internally.
- **Transaction-detail route gap added.** The backend supports
  `GET /api/v1/transactions/{id}` and the docs describe
  `/transactions/:id`, but the frontend router does not currently
  register `/transactions/:id`, and `ROUTES.TRANSACTION_DETAIL(id)` is
  absent from `utils/constants.ts`.
- **Intake selector corrected.** The old
  `GET /api/v1/transactions?role=attorney&state=active` wording was
  stale. Existing transaction listing already scopes by the current
  user's token; after Phase B, the preferred selector source is the new
  lightweight `GET /api/v1/attorney/matters`.
- **Recent activity backend dependency added.** A "Recent matter
  activity" rail card needs a new read projection on the dashboard
  payload; it cannot be shipped as a pure frontend Phase A change.
- **Upload/indexing gap added.** `POST /api/v1/documents/upload` stores
  a document; it does not by itself run AI parsing or create
  `attorney_review_items`. The intake flow must orchestrate upload,
  parse/index, and review-item creation honestly.
- **Attorney hold storage renamed.** The plan no longer recommends
  `transactions.legal_hold`, because `legal_hold` already means tenant
  retention/platform hold elsewhere in the system. Use a dedicated
  `attorney_matter_state` row or an attorney-specific field name.
- **Communication log shortcut fixed.** The current `/communications`
  route redirects to Admin Communication Audit, and
  `/dashboard/attorney?panel=communications` has no implemented panel.
  Attorney communication-log UI is deferred to the Matter Workspace.

## Changes since rev 1

- **§1.2 / §1.4 / §5.4** — "+ Upload Packet" placement corrected from sidebar
  to topbar per `SYSTEM_DESIGN.md` §3.4 (`'+ Upload Packet' CTA instead of
  '+ New Transaction'`). The dashboard rail keeps a secondary "Upload a
  legal packet" shortcut but the primary CTA is the topbar.
- **§3.3** — dropped the "All open matters" list-card. A list-shaped block
  on the dashboard reintroduces exactly the boundary the plan exists to
  fix. Replaced with an expanded "Matters needing judgment" hero (top 5
  by urgency) plus a thin "Recent matter activity" rail card.
- **§3.3 / Phase A** — folded Phase E's `expandedMatter` /
  `matterRowRefs` / `MatterCardItem` / `focusMatter` / `uploadCardRef` /
  `?panel=upload` cleanup into Phase A so each phase is committable as a
  single PR.
- **§4.3 / §4.4** — clarified that `MatterDocChecklist` has no drop zone
  today; per-matter upload moves to a separate `MatterUploadDropZone`
  panel inside the workspace, not into the checklist component.
- **§4.4 / §7.2** — replaced the proposed
  `GET /api/v1/attorney/matters/{id}` with the spec'd
  `GET /api/v1/transactions/{id}/attorney-detail`
  (`FRONTEND_UI_WORKFLOW_LOGIC.md` §3.4 already names this path).
- **§4.4 / §7.2** — flagged `PATCH /api/v1/attorney/matters/{id}` as
  currently a no-op mock (audits but writes no state); Phase B now
  includes un-mocking it.
- **§4.4** — removed the "inline drop zone in the file checklist" claim
  (the existing component has no drop zone) and made the per-matter
  upload an explicit separate panel.
- **§7.1 / §7.2** — flagged that
  `GET /api/v1/attorney/state-rules` and
  `GET /api/v1/attorney/recording-calendar` return hardcoded payloads today;
  added an MVP truthfulness note.
- **§7.2** — added a gap for the matter-switcher list endpoint
  (`GET /api/v1/attorney/matters` — formerly an open risk).
- **§7.2** — added a gap for the Attorney variant of
  `/transactions/active` reading filter state from the URL
  (`?tab=needs-review`) instead of `useState`. Phase A requires this so
  dashboard KPI click-throughs work.
- **§2 / Phase E** — `/attorney/queue` (spec'd in `SYSTEM_DESIGN.md`
  §7.1 as a redirect to `/dashboard/attorney`) is re-pointed to
  `/transactions/active`.
- **Phase E** — broadened the doc-update commitment to include
  `SYSTEM_DESIGN.md` §3.4, §4.3.1e, §7.1 prose and
  `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.4 — not just the page tree.
- **Phase per-phase** — added explicit test bullets
  (vitest + pytest) to each phase's exit criteria.
- **Time estimate** — bumped from ~3 dev days to ~5.25 dev days plus QA
  to reflect un-mocking the PATCH, the spec doc updates, the new
  matter-switcher endpoint, the intake orchestration, the
  transaction-detail route, and tests.
- **Risks** — risk #2 (matter switcher data source) and risk #6
  (AttorneyWorkspacePage naming) promoted from open items to decisions
  baked into Phase B; rev 3 replaces the AI briefing risk with a
  no-topbar-briefing decision.

## Context

The current Attorney landing page (`/dashboard/attorney`) tries to be two
things at once: a portfolio overview *and* the place where an attorney
does per-matter legal work. That overload produced two concrete defects:

1. **A filter tab strip on the dashboard.** Filter strips belong on
   list/workflow surfaces (Transactions page, Releases queue), not on
   a dashboard. A dashboard is an overview surface; the moment it gains
   a primary filter strip, it stops behaving like a dashboard and
   starts behaving like a filtered list view.

2. **An "Upload a legal packet" card on the dashboard.** Upload is a
   function — the attorney is *executing* a workflow when they upload.
   A dashboard surfaces state; it doesn't host primary functional
   surfaces. The upload card belongs on a dedicated intake page (or
   on the per-matter workspace), not on the role's landing page.

Both defects share one root cause: the dashboard absorbed work that
should belong to a separate **Attorney Matter Workspace** — the
per-matter detail surface that Jake's initial design
(`VE-AttorneyDashboard.html`) was actually drafting, even though it
was labelled "dashboard."

Jake's HTML is, structurally, **not** a dashboard. The sidebar is a
matter switcher; the main pane renders the *selected matter* (command
strip → summary cards → file checklist → upcoming actions → activity
feed → AI legal brief → review queue → contacts). That's a per-matter
workspace with a matter-list sidebar — semantically a *transaction
detail page for an attorney*, not a role-level dashboard.

The cleanest fix is to split the two surfaces:

- **`/dashboard/attorney`** — a true overview: KPIs, judgment-needed
  hero, drift/blockers rail. No filters, no upload, no inline expand.
- **Attorney Matter Workspace** — a per-matter detail page where the
  file checklist, sign-off toggles, release flow, AI legal brief, and
  people panel live. This is where Jake's design intent lands.

Plus two narrow supporting surfaces:

- **Legal Packet Intake** — the new home for the upload functionality.
- **Releases queue** — the human-initiated packet release surface.

The Recording Calendar (already at `/attorney/recording-calendar`) and
State Rules reference (already a modal opened from the dashboard) stay
as they are.

---

## Part 1 — Functional analysis: what an attorney actually does

Authoritative sources read for this analysis:

- `SYSTEM_DESIGN.md` (Attorney role definition, permission matrix,
  endpoint inventory, page tree)
- `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.4 (Attorney Dashboard) and §7
  (Attorney Workspace — Queue / Releases / State Rules / Recording
  Calendar)
- `MILESTONE_5_1_IMPLEMENTATION_PLAN.md` (attorney-specific KPIs and
  drift summary)
- `MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md` (current rails &
  upload-card-on-dashboard prescription, which this plan now overrides)
- `ROLE_DASHBOARDS_DESIGN_UPDATE_PLAN.md` rev 5 (current Attorney
  dashboard scope — Phase B)
- Jake's initial design `VE-AttorneyDashboard.html`
- My update `completed_designs/ve-attorney_dashboard.html`
- Existing backend `app/api/v1/attorney.py`
- Existing frontend `pages/dashboards/AttorneyDashboardPage.tsx`,
  `pages/transactions/AttorneyWorkspacePage.tsx`,
  `pages/dashboards/AttorneyRecordingCalendarPage.tsx`, and
  `components/dashboard/attorney/*` sub-components.

### 1.1 Attorney's role in a real-estate transaction (Velvet Elves)

From the permission matrix and role definition:

- The Attorney is an **internal user** whose deliverable is a clean,
  release-ready legal packet for each matter they're assigned to.
- AI does the preparation (extract deadlines, index exhibits, compare
  versions, flag missing formal documents, draft response shells).
  **A human attorney makes the legal call** — sign-off on each review
  item, release the packet, hold the file, decide what legal position
  to take. This boundary is a hard rule: no AI auto-release.
- The attorney works through **matters** (the role-specific framing
  for transactions they are assigned to via
  `transaction_assignments.role_in_transaction = 'attorney'`).
- The attorney does not create transactions, does not invite users,
  does not manage tasks for the whole team. Their write surface is
  scoped to their assigned matters and to release/sign-off actions.

### 1.2 Inventory of capabilities, mapped to the four sources

For each capability, I noted whether Jake's design surfaces it, whether
my update surfaces it, whether the system/workflow docs require it, and
whether I judge it *necessary* for the Attorney role to be functional.

| # | Capability | Jake | My update | Docs | Necessary? | Lives where |
|---|---|---|---|---|---|---|
| 1 | KPI strip: legal health, pending review, missing docs, ready to release | ✗ | ✓ | ✓ §3.4 | **Yes** | Dashboard |
| 2 | "Matters needing legal judgment" hero — files AI staged but counsel still owes the call | ✗ | ✓ | ✓ §3.4 | **Yes** | Dashboard |
| 3 | Critical approval gates (rail) — open blocking sign-offs across matters | ✗ | ✓ | ✓ §3.4 | **Yes** | Dashboard rail |
| 4 | Drift summary (rail) — blocked / release-ready / missing formal docs | ✗ | ✓ | ✓ §3.4 | **Yes** | Dashboard rail |
| 5 | State rules summary + modal | ✗ | ✓ | ✓ §7.3 | **Yes** | Dashboard rail + standalone modal |
| 6 | Filter tab strip (All / Needs review / Missing docs / Ready / Clean) | ✗ | ✓ | ✓ §3.4 | **No, on dashboard** — belongs on `/transactions/active` | Transactions page (already there) |
| 7 | Per-matter file checklist with sign-off toggles | ✓ | ✓ (inline expand) | ✓ §3.4 | **Yes** | Matter Workspace |
| 8 | Per-matter AI legal brief (what AI did / why a human is still needed / recommended next move) | ✓ | ✓ | ✓ §3.4 | **Yes** | Matter Workspace |
| 9 | Per-matter timeline of upcoming legal deadlines | ✓ | ✓ | ✓ §3.4 | **Yes** | Matter Workspace |
| 10 | Per-matter activity feed ("what changed since you last looked") | ✓ | ✓ | ✓ §3.4 | **Yes** | Matter Workspace |
| 11 | Per-matter people panel — sellers, buyers, lender, title co, support | ✓ | ✓ | ✓ §3.4 | **Yes** | Matter Workspace |
| 12 | Per-matter command strip — single most-urgent next action | ✓ | partly (hero row) | — | **Yes** (top-of-workspace) | Matter Workspace |
| 13 | Per-matter summary cards (blocking docs / next deadline / AI-ready / completeness %) | ✓ | partly (KPIs) | — | **Yes** (matter-scoped, distinct from dashboard KPIs) | Matter Workspace |
| 14 | Legal packet upload (drag-drop, PDF/DOCX, AI indexing) | sidebar btn | dashboard card | ✓ §3.4 (topbar CTA) | **Yes**, but not as a dashboard card | Topbar CTA + Legal Packet Intake page + Matter Workspace (separate panel) |
| 15 | Send-for-release modal (recipient list, document list, sign-off check) | sidebar btn | wired via SendPacketModal | ✓ §7.2 | **Yes** | Matter Workspace + Releases queue |
| 16 | Releases queue (release-ready packets across all matters) | ✗ | quick-action link only | ✓ §7.2 | **Yes** | Standalone `/attorney/releases` page |
| 17 | Recording calendar | ✗ | quick-action link | ✓ §7.4 | **Yes** | Already at `/attorney/recording-calendar` |
| 18 | State Rules reference page | ✗ | modal only | ✓ §7.3 | **Modal is enough for MVP**; standalone page can wait | Modal (existing) |
| 19 | Filing log / per-matter audit trail | ✓ topbar btn | ✗ | — | **Defer** — surfaces from the matter audit feed already; no separate UI yet | Matter Workspace activity feed |
| 20 | "+ New matter" button | ✓ sidebar btn | ✗ | ✗ — Attorney does not create transactions per §3.3 permission matrix | **No, cut** — attorney does not create matters | — |
| 21 | "Filter" button inside file checklist | ✓ | ✗ | — | **No, cut** — checklist is short enough; filtering is over-engineering | — |
| 22 | "Full audit trail" button | ✓ | ✗ | — | **Defer** — out of scope until audit log viewer exists | — |
| 23 | Per-matter sidebar (matter switcher chip list) | ✓ | ✗ | — | **Yes** — keep as a left-rail/inline switcher in the Matter Workspace; Jake's pattern is correct here | Matter Workspace (left rail or top dropdown) |

### 1.3 Cuts (with reasoning)

- **#20 "+ New matter."** Permission matrix in `SYSTEM_DESIGN.md`
  §3.3 explicitly denies attorneys the *Create transaction* permission.
  Jake's button is a leftover from the generic dashboard skeleton.
- **#21 In-checklist filter button.** Files have ~4–8 items; filtering
  is overhead, not signal.
- **#22 "Full audit trail" page.** No audit-log viewer surface exists
  yet anywhere in the product. The matter Activity feed gives
  attorneys what they need today; a dedicated audit viewer is a
  separate future feature.
- **#19 Standalone filing log.** Same reasoning — the matter activity
  feed is sufficient.
- **#18 Standalone State Rules page.** The modal already opens from
  the dashboard rail. A standalone page can wait until tenants start
  asking for per-state cross-reference views.
- **#6 Filter tab strip on the dashboard.** This is the primary
  defect being fixed. Filters belong on `/transactions/active` (the
  Attorney variant of the Transactions list page), which already
  exists as `AttorneyWorkspacePage.tsx` and already carries the
  attorney filter tabs. That page is the right home for filter-driven
  list browsing.

### 1.4 Keeps (the necessary set)

**Dashboard (`/dashboard/attorney`) — overview only:**

- KPI strip (legal health, pending review, missing docs, ready to release)
- "Matters needing legal judgment" hero — expanded to top ~5 by urgency
  (was top 3). Read-only rows with explicit "Review matter" buttons
  (pattern 9) that click through to the Matter Workspace.
- "Recent matter activity" rail card — a thin event feed (sign-offs
  recorded, packets released, holds applied) across the attorney's
  matters. Overview-shaped, not list-shaped.
- Critical approval gates rail card
- Drift summary rail card
- State rules summary rail card (opens the existing State Rules modal)
- Legal health ring rail card
- Quick actions rail card (Recording Calendar, State rules,
  AI suggestions, **+ Upload a legal packet** — secondary shortcut;
  the primary upload CTA is in the topbar, see §5.4). Do **not** link
  "Communication log" from the dashboard until an attorney-scoped
  communication surface exists; the current `/communications` route is
  admin/team-lead oriented.

**Shell topbar (Attorney role):**

- **Primary CTA:** "+ Upload Legal Packet" / "+ Upload Packet"
  (choose one label and align docs + `dashboardShellConfig.ts`) replaces
  "+ New Transaction" per `SYSTEM_DESIGN.md` §3.4. The
  `upload-legal-packet` branch already exists in `AppLayout`; retarget
  it from `/dashboard/attorney?panel=upload` to `/attorney/intake`.
- **No shared topbar AI briefing bar for MVP.** The current shell
  intentionally sets `showAiBriefingBar: false` for Attorney so the
  internal transaction briefing does not leak into the legal workflow.
  If an attorney-specific briefing chip is reintroduced later, derive
  it from `GET /api/v1/dashboard/attorney` counts; do not add a fresh
  LLM call.

**Attorney Matter Workspace — per-matter detail (new dedicated page):**

- Matter switcher (left rail chip list, mirroring Jake's pattern)
- Command strip — the single most-urgent legal action for this matter
- Matter-scoped summary cards (blocking docs, next deadline,
  AI-ready, completeness %)
- File checklist with sign-off toggles (existing `MatterDocChecklist`)
- AI legal brief (existing `AiLegalBrief`)
- Timeline (existing `MatterTimeline`)
- Activity feed (existing `MatterActivity`)
- People panel (existing `MatterPeoplePanel`)
- Release-packet action (existing `SendPacketModal`)
- Hold-matter action (existing `PATCH /api/v1/attorney/matters/{id}`)

**Legal Packet Intake (`/attorney/intake`) — new dedicated page:**

- Drag-drop upload zone
- File-type guidance, AI indexing badge
- Assignment selector — which matter (transaction) does this packet
  belong to? (Required, because the attorney cannot create
  transactions; the matter must already exist.)
- Upload orchestration: upload the document, run the existing AI parse
  job, and create/update attorney review items from the extracted
  packet facts. Do not show "AI indexed" success copy until the parse
  job has actually been queued or completed.
- Post-upload toast + deep-link back to the matter

**Releases queue (`/attorney/releases`) — wire the existing endpoint:**

- List of release-ready and recently released matters from
  `GET /api/v1/attorney/releases?status=ready|released` after the
  endpoint extension in Phase D
- Per-row "Release packet" primary action (opens `SendPacketModal`)
- Per-row "Hold" secondary action

**Already wired / no change needed:**

- Recording Calendar (`/attorney/recording-calendar`)
- State Rules (modal at `?panel=state-rules`)

---

## Part 2 — Page tree decision

```
/dashboard/attorney              — Attorney Dashboard (overview)
/transactions/active             — Attorney's matter list (filter tabs OK here)
/transactions/:id (attorney UI)  — Attorney Matter Workspace (new frontend route; generic backend detail exists)
/attorney/intake                 — Legal Packet Intake (new — upload)
/attorney/releases               — Release Queue (new wiring of existing endpoint)
/attorney/recording-calendar     — Recording Calendar (exists)
/attorney/queue                  — REDIRECT to /transactions/active (was: redirect to dashboard)
?panel=state-rules               — State Rules modal (exists)
```

**`/attorney/queue` re-pointed.** `SYSTEM_DESIGN.md` §7.1 currently
spec's this route as a redirect to `/dashboard/attorney`, on the
assumption that the dashboard hosts the queue. Under this plan the
queue lives at `/transactions/active`, so the redirect target moves
there. Phase E updates the §7.1 prose accordingly.

**Notes on `/transactions/:id`:** the product docs specify this route
and the backend already exposes `GET /api/v1/transactions/{id}`, but
the current frontend router only registers the list aliases
(`/transactions`, `/transactions/active`, `/transactions/pending`,
`/transactions/closed`, `/transactions/all`). Phase B must add the
frontend `/transactions/:id` route and a `ROUTES.TRANSACTION_DETAIL(id)`
helper before dashboard/matter-list click-throughs can target the
Matter Workspace. The recommendation is still **`/transactions/:id`
with an `AttorneyMatterWorkspace` layout that activates when
`user.role === 'Attorney'`**, because (a) the underlying domain object
is the same transaction, and (b) other roles can later share the same
route for their own transaction-detail layouts.

---

## Part 3 — Attorney Dashboard fixes

**Goal:** turn `/dashboard/attorney` back into a true overview.

### 3.1 Remove the URL-driven filter tab strip

- Delete `FilterTabStrip` and the `?filter=` query handling from
  `AttorneyDashboardPage.tsx`.
- Drop `FilterKey` / `FILTER_TABS` / `deriveFilterKey` / the
  `filteredMatters` memo and the matter-card stack that consumed it.
- KPI tile `onClick` handlers that previously set the filter (e.g.
  `setFilter('needs-review')`) become *navigation* handlers that
  push to `/transactions/active?tab=needs-review` (UI tab key). The
  Attorney list page maps that key to the API value `needs_review`.

**Rationale:** the dashboard's KPI tiles are scope indicators, not
filter controls. Clicking a KPI takes you to the filtered list view,
not to a filtered version of the dashboard itself.

### 3.2 Remove the "Upload a legal packet" card

- Delete the entire `<DashboardCard tone="brand" icon={<Upload />} …>`
  block (lines wrapping the `UploadIntakeCard`) and the
  `uploadCardRef` plumbing.
- Drop the `?panel=upload` deep-link handler.
- Replace any reference to the dashboard upload affordance with a
  navigation to `/attorney/intake` (Part 5).

**Rationale:** the dashboard surfaces *state*. Uploading is
*execution*. They don't share a surface.

### 3.3 Slim the main column

The dashboard's main column had two big blocks today. Rev 3 removes
both list-shaped surfaces from the dashboard:

- **Keep:** "Matters needing legal judgment" hero — but the "Review
  matter" button now *navigates* to the Matter Workspace
  (`/transactions/${transactionId}`) instead of triggering an inline
  expand. Expand
  the row count from top 3 to top ~5 by urgency so the hero carries
  the weight that the deleted "Matter queue" used to.
- **Delete (not replace) the "Matter queue" stack.** Rev 1 proposed an
  "All open matters" list-card as a slim substitute. That re-introduces
  exactly the boundary the plan exists to fix — a list-shaped block on a
  dashboard. If the user wants to browse all matters, they navigate to
  `/transactions/active` via the KPI tile click-through or the "View
  matter list" link in the hero header.
- **In the rail, add "Recent matter activity"** — a thin overview-shaped
  feed (last ~5 events across the attorney's matters: sign-offs recorded,
  packets released, holds applied). This is *event* content, not *list*
  content — it tells the attorney what changed since they last looked,
  not what work is queued. It also lets the rail keep parity with the
  expanded main column (pattern 13). This requires a new
  `recent_activity` read projection on `GET /api/v1/dashboard/attorney`;
  it cannot be done from the current frontend payload alone.
- **Phase A cleanup (folded in from rev 1's Phase E):**
  - Delete `expandedMatter` state, `setExpandedMatter`, `MatterCardItem`,
    `matterRowRefs`, and `focusMatter` —
    [AttorneyDashboardPage.tsx:100-146](velvet-elves-frontend/src/pages/dashboards/AttorneyDashboardPage.tsx#L100-L146).
  - Delete `uploadCardRef`, `?panel=upload` handling, and the
    `useEffect` that scrolls to the upload card —
    [AttorneyDashboardPage.tsx:101-108](velvet-elves-frontend/src/pages/dashboards/AttorneyDashboardPage.tsx#L101-L108).
  - Delete the `<DashboardCard tone="brand" icon={<Upload />} …>` block.
  - The result: the main column has one block (the expanded hero) plus
    the existing rail; the rail has one new card (Recent activity).

### 3.4 Rail composition

- Legal health (ring, green)
- Open approval blockers (red)
- Recording & release drift (amber, opens State Rules modal)
- Per-state closing posture (blue, opens State Rules modal)
- **Recent matter activity (new — purple/neutral tone)** — last ~5
  events from the audit log scoped to the attorney's matters
  (sign-off recorded, packet released, hold applied). Each row is a
  one-line event with a timestamp; clicking the row deep-links to the
  Matter Workspace at the affected matter. Sourced from existing
  `audit_logs` rows already produced by `_audit()` in
  [attorney.py:34](velvet-elves-backend/app/api/v1/attorney.py#L34).
  No new write path is needed, but the dashboard endpoint needs a new
  read query.
- Quick actions (brand — Recording Calendar / State rules /
  AI suggestions — plus a secondary **"Upload a legal packet"** entry
  that navigates to `/attorney/intake`; the primary upload affordance
  is the topbar CTA per §5.4). Defer "Communication log" until the
  Matter Workspace exposes a matter-scoped communications/activity
  surface.

### 3.5 Pattern compliance check

- §15.1 shell: still satisfied.
- Pattern 6 sticky bottom-alignment: with the main column collapsed to
  one block (expanded hero), the rail (legal health → blockers → drift
  → state → recent activity → quick actions = 6 cards) is now the
  taller column. The hero's row count flexes to ~5 to keep the rail
  bounded; if the rail still overhangs, fold "Per-state closing
  posture" into the Drift card.
- Pattern 9 (alert-card clickability): "Matters needing legal
  judgment" rows already have an explicit "Review matter" button —
  [AttorneyDashboardPage.tsx:744-747](velvet-elves-frontend/src/pages/dashboards/AttorneyDashboardPage.tsx#L744-L747). Keep.
  The new "Recent matter activity" rail rows are event rows, not
  alert cards — each row needs an explicit "Open matter" button (or
  whole-row link with `aria-label`), not a whole-card click target.
- Pattern 14 (no internal milestone copy): audit all visible strings
  during the edit pass. None expected in the current attorney
  dashboard, but verify.

---

## Part 4 — Attorney Matter Workspace (new)

**Goal:** a per-matter detail page that is the attorney's working
surface for a single file.

### 4.1 Route + entry

- **Route:** `/transactions/:id` (add this frontend route in Phase B;
  render the Attorney layout when `user.role === 'Attorney'`).
- **Entry:** click-through from
  - `/dashboard/attorney` "Matters needing legal judgment" rows
  - `/transactions/active` (Attorney list) matter cards
  - `/attorney/releases` rows
  - notifications and AI suggestion deep-links

### 4.2 Layout

A three-region layout, all on a single page-level scroll (per §15.1):

```
┌─────────────────────────────────────────────────────────────────┐
│ Topbar (shared shell)                                            │
├──────────────┬──────────────────────────────────────────────────┤
│              │  Matter command strip (most-urgent legal action) │
│              │  — single CTA, severity-tinted                    │
│              ├──────────────────────────────────────────────────┤
│  Matter      │  Matter summary cards (4 KPI-style tiles,         │
│  switcher    │  matter-scoped)                                   │
│  (left rail, │                                                   │
│  scrollable  │  File checklist  (with sign-off toggles)          │
│  chip list)  │                                                   │
│              │  AI legal brief  (collapsible card)               │
│              │                                                   │
│              │  Timeline                                         │
│              │                                                   │
│              │  Activity feed                                    │
│              │                                                   │
│              │  People on matter                                 │
└──────────────┴──────────────────────────────────────────────────┘
```

### 4.3 Components — reused or adapted

Reusable or nearly reusable from the current Attorney dashboard work:

- `components/dashboard/attorney/MatterSwitcher.tsx` — already exists;
  re-purpose for the left rail. It is not currently wired into
  `AttorneyDashboardPage`, and its props expect `AttorneyMatterCard`.
  Phase B should either (a) make the new matter-list endpoint return
  enough fields to satisfy that shape, or (b) extract a smaller
  `AttorneyMatterListItem` type for the switcher.
- `components/dashboard/attorney/MatterSummaryRow.tsx` — matter
  summary tiles. Verify during Phase B that it composes cleanly as a
  standalone top-of-workspace block; it's currently rendered inside
  `MatterCardItem`'s expanded body.
- `components/dashboard/attorney/MatterDocChecklist.tsx` — file
  checklist with `POST /api/v1/attorney/approve` toggles. See
  [MatterDocChecklist.tsx:16](velvet-elves-frontend/src/components/dashboard/attorney/MatterDocChecklist.tsx#L16).
- `components/dashboard/attorney/AiLegalBrief.tsx` — AI legal brief.
- `components/dashboard/attorney/MatterTimeline.tsx` — timeline.
- `components/dashboard/attorney/MatterActivity.tsx` — activity feed.
- `components/dashboard/attorney/MatterPeoplePanel.tsx` — people.
- `components/dashboard/SendPacketModal.tsx` — release modal.
- `components/dashboard/StateRulesModal.tsx` — state rules modal.

**New component (small):**

- `components/dashboard/attorney/MatterUploadDropZone.tsx` — a
  per-matter drop zone for adding documents to the open matter. Wraps
  the existing `components/shared/UploadIntakeCard.tsx` primitive and
  pre-fills the matter id so the attorney doesn't need to re-select
  in the intake page. Lives as a separate panel below the file
  checklist (rev 1 placed this *inside* `MatterDocChecklist`; that
  component has no drop zone today and extending it conflates
  sign-off rendering with upload chrome).

### 4.4 Per-matter actions

| Action | Endpoint | Surface |
|---|---|---|
| Approve / hold a review item | `POST /api/v1/attorney/approve` (set `action='approve'` or `'hold'`) | Checkbox in file checklist |
| Release packet | `POST /api/v1/attorney/release-packet` | `SendPacketModal` from a primary CTA in the command strip |
| Hold matter (with reason) | `PATCH /api/v1/attorney/matters/{id}` — **currently a no-op mock**, see §7.2 gap 3 | Secondary CTA next to release |
| Open state rules | `StateRulesModal` fed by dashboard/detail payload today; `GET /api/v1/attorney/state-rules` exists but is hardcoded, see §7.1 | Inline link from command strip when state-rule context is relevant |
| Upload more docs to matter | `POST /api/v1/documents/upload` + `POST /api/v1/ai/parse-document/{document_id}?background=true` + attorney review-item creation | New `MatterUploadDropZone` panel below the file checklist |

**Sign-off semantic note.** `POST /api/v1/attorney/approve` takes
`action: 'approve' | 'hold'` per
[attorney.py:54](velvet-elves-backend/app/api/v1/attorney.py#L54).
It is not a toggle endpoint — the client passes the *target* state
based on the row's current `signed_off` value. The existing
`toggleSignOff` helper in
[AttorneyDashboardPage.tsx:148-167](velvet-elves-frontend/src/pages/dashboards/AttorneyDashboardPage.tsx#L148-L167)
already implements this correctly and can be lifted to the workspace
verbatim.

### 4.5 Matter command strip

Jake's design centred the per-matter UX on a single, severity-tinted
"command strip" at the top of the workspace — one sentence stating the
single next legal action, plus one primary CTA. Keep this. It's a
high-value UI for an attorney scanning multiple files per day.

- Red tone when there's a hard-stop (e.g. unsigned response due today)
- Amber when there's a same-day soft deadline
- Green when the file is clean (collapsed message: "No attorney
  action required · Next checkpoint: <date>")

The command strip is **per-matter**, not the cross-portfolio
`CommandStrip` used on Solo Agent / Team Lead. Different component,
similar visual contract.

### 4.6 Patterns to follow

- §15.1 shell.
- Single page-level scroll.
- File-checklist rows follow pattern 16 (priority queue row
  vocabulary): severity rail, tinted icon tile, pill row, serif
  title, muted next-step, single filled primary action button.
- People panel uses pattern 8 progressive disclosure (collapsed
  contact rows, expand on click).
- Pattern 9 (explicit button per row, not whole-card click) — the
  checklist rows already have explicit "Review draft" / "Open draft"
  / "View" buttons per Jake's design and the existing component.
- Pattern 14 — strip any milestone references; the file-checklist
  copy in Jake's design is clean on this axis.

---

## Part 5 — Legal Packet Intake (`/attorney/intake`)

**Goal:** the home for the upload functionality that should not live on
the dashboard.

### 5.1 Why a dedicated page

The attorney's upload flow has two requirements the dashboard cannot
serve:

1. **Matter assignment.** The packet has to attach to a transaction
   the attorney is assigned to. The dashboard upload card lacks any
   way to do this — it just accepts files. A dedicated page makes
   matter selection a first-class field.
2. **AI indexing context.** After upload, the AI extracts deadlines,
   indexes exhibits, and creates review items. The success state for
   this is "what AI did + here are the new review items + open the
   matter." The dashboard doesn't have room for that response surface.

### 5.2 Layout

- Page header: "Legal packet intake" + short description.
- Form region:
  - **Matter selector** (required) — searchable dropdown of the
    attorney's active matters. Preferred source after Phase B:
    `GET /api/v1/attorney/matters`. If Phase C is implemented before
    that endpoint exists, fall back to `GET /api/v1/transactions`
    with `status=Active` and the attorney's token; do not add a
    `role=attorney` query param.
  - **Packet type** (optional) — single-select chip group: Title
    commitment / Disclosure package / Settlement statement / Amendment
    / Recording packet / Other.
  - **Drop zone** — drag-drop, multi-file, PDF / DOCX / PNG / JPG.
- After upload:
  - Inline progress + per-file extraction summary. Implementation
    uploads each file with `useUploadDocument` /
    `POST /api/v1/documents/upload`, then queues AI parsing with
    `POST /api/v1/ai/parse-document/{document_id}?background=true`
    and polls `/status`.
  - Create or update `attorney_review_items` from the parse result
    through a dedicated attorney-intake orchestration path. If that
    mapping does not exist yet, add it explicitly; do not imply that
    generic document upload creates legal sign-off rows.
  - Toast: "Packet received — N files queued for indexing" when jobs
    are queued; use "indexed" only after completed parse status.
  - Primary CTA: "Open matter" → `/transactions/:id`.

### 5.3 Reuse

- `components/shared/UploadIntakeCard.tsx` for the drop zone primitive.
- Existing `POST /api/v1/documents/upload` endpoint for file storage.
- Existing `POST /api/v1/ai/parse-document/{document_id}` endpoint
  for AI extraction/indexing. Add a small attorney-intake service if
  parse results need to be converted into `attorney_review_items`.

### 5.4 Entry points

- **Topbar primary CTA "+ Upload Packet" / "+ Upload Legal Packet"**
  (replaces "+ New Transaction" for the Attorney role, per
  `SYSTEM_DESIGN.md` §3.4 line 888: *"'+ Upload Packet' CTA instead
  of '+ New Transaction'"*). This is the canonical entry; rev 1's
  "sidebar shell CTA" was a mis-read. Implementation: the topbar
  already renders `primaryCta.action === 'upload-legal-packet'`; change
  the handler from `/dashboard/attorney?panel=upload` to
  `ROUTES.ATTORNEY_INTAKE`.
- Dashboard rail "Quick actions" → "Upload a legal packet" (secondary
  shortcut).
- Matter Workspace `MatterUploadDropZone` panel is an *additional*
  surface for same-matter uploads (skips matter selection because the
  matter id is already in scope).

---

## Part 6 — Releases queue (`/attorney/releases`)

**Goal:** wire the existing endpoints into a real list page.

The backend `GET /api/v1/attorney/releases` already returns released
matters. For MVP, this page can render a thin list:

- Header: "Release queue" + count pill.
- Two sections (or a single tab strip):
  - **Ready to release** — matters where all sign-offs are clear and
    no packet has been released yet. Each row: matter name, closing
    date, packet contents, "Release packet" primary CTA (opens
    `SendPacketModal`).
  - **Recently released** — last N releases (existing endpoint
    payload). Each row: matter name, release timestamp, recipients,
    document count.

Filter tabs are appropriate here — this *is* a list page, not a
dashboard.

---

## Part 7 — Backend touchpoints

### 7.1 What already exists

- `POST /api/v1/attorney/approve` — sign-off (set, not toggle).
- `POST /api/v1/attorney/release-packet` — packet release.
- `PATCH /api/v1/attorney/matters/{id}` — **currently a no-op**: writes
  an audit row, returns `{patched: true, …}`, but does not mutate any
  matter state. See
  [attorney.py:165-179](velvet-elves-backend/app/api/v1/attorney.py#L165-L179).
- `GET /api/v1/attorney/releases` — returns *all* rows in
  `attorney_packet_releases` for the tenant. The table is functionally
  released-only today because every insert hardcodes
  `status: "released"`, but the endpoint itself has no status filter.
  See
  [attorney.py:182-198](velvet-elves-backend/app/api/v1/attorney.py#L182-L198).
- `GET /api/v1/attorney/state-rules?state=` — **returns a hardcoded
  static payload regardless of `state`**
  ([attorney.py:201-213](velvet-elves-backend/app/api/v1/attorney.py#L201-L213)).
  MVP-acceptable for the modal but the rail card's per-state
  differentiation is currently a placeholder.
- `GET /api/v1/attorney/recording-calendar?start=&end=` — **returns
  a hardcoded "weekdays open, weekends closed" pattern**, not real
  calendar data
  ([attorney.py:216-232](velvet-elves-backend/app/api/v1/attorney.py#L216-L232)).
- `GET /api/v1/dashboard/attorney` — aggregated dashboard payload
  (legal_health_score, drift_summary, matter_cards, state_rules_summary,
  matters_needing_judgment, filter_counts, critical_approval_gates).
  It does **not** currently carry a topbar AI briefing payload or a
  `recent_activity` list.

### 7.2 Gaps to address

1. **"Ready to release" view of `/attorney/releases`.** Today the
   endpoint returns rows from `attorney_packet_releases`, which is
   released-only by virtue of every insert hardcoding
   `status: "released"`. The Releases queue needs a *ready-to-release*
   view derived from a *different* table: assigned attorney matters
   where all required `attorney_review_items` are signed-off, at least
   one review item exists, and no `attorney_packet_releases` row has
   been written yet. Extend
   `GET /api/v1/attorney/releases` with a `?status=ready|released`
   query; for `ready` the handler queries `attorney_review_items`
   grouped by transaction and excludes transactions present in
   `attorney_packet_releases`. Apply tenant and transaction-assignment
   access checks in both modes. Single endpoint, two derivations.

2. **Per-matter detail endpoint — use the spec'd path.** The Matter
   Workspace needs richer per-matter data than the dashboard payload
   carries. `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.4 already specs
   `GET /api/v1/transactions/:id/attorney-detail` for this purpose
   (line 956; implement as FastAPI
   `/api/v1/transactions/{id}/attorney-detail`). Implement that path
   rather than the
   `/api/v1/attorney/matters/{id}` rev 1 invented — keeps the doc
   surface and the code surface aligned. Response shape: `review_items`,
   `ai_legal_brief`, `timeline`, `activity`, `contacts`,
   `state_rule_context`, `summary_tiles`. Implementation can reuse the
   same underlying services that feed the dashboard payload's
   `matter_cards`.

3. **Un-mock `PATCH /api/v1/attorney/matters/{id}`.** The endpoint
   currently writes an audit row and returns a fabricated success
   body without touching matter state
   ([attorney.py:165-179](velvet-elves-backend/app/api/v1/attorney.py#L165-L179)).
   For the workspace "Hold matter" CTA to be honest, this needs real
   storage. Recommend a dedicated `attorney_matter_state` row keyed on
   `(tenant_id, transaction_id)` to persist
   `{status, hold_reason, note, updated_at, updated_by}`. Avoid naming
   this field/table `legal_hold`: the platform already uses
   `tenants.legal_hold` / `platform_legal_holds` for retention and
   compliance holds, and overloading that vocabulary will confuse
   operators and tests. Also avoid reusing `transactions.status`; an
   attorney hold is a legal-review state, not the global transaction
   lifecycle.

4. **Matter-switcher list endpoint.** The workspace's left rail needs
   a lightweight list of the attorney's matters that doesn't depend on
   loading the full dashboard payload. Add
   `GET /api/v1/attorney/matters` returning enough data for the
   switcher and intake selector:
   `[{id, address, client_names, status_pill, filter_key, closing_date,
   blocking_count, ai_next_step}]`. Cache via React Query
   (`['attorney', 'matters']`) so the workspace and intake page can
   share the same query. The dashboard should continue using
   `GET /api/v1/dashboard/attorney` for its overview payload.
   (Rev 1 left this as risk #2; rev 3 keeps it as a Phase B item.)

5. **URL-driven tab state on `/transactions/active` (Attorney view).**
   [AttorneyWorkspacePage.tsx:60-64](velvet-elves-frontend/src/pages/transactions/AttorneyWorkspacePage.tsx#L60-L64)
   currently uses `useState` for the active tab, ignoring the `?tab=`
   query string. Phase A re-points dashboard KPI/sidebar clicks to
   `/transactions/active?tab=needs-review` etc.; that target page must
   read the URL or the click-through breaks silently. Phase A includes
   the `useState → useSearchParams` migration, accepting both `?tab=`
   and legacy `?filter=` if needed.

6. **`GET /api/v1/transactions` already filters per-user for
   Attorneys.** Verified at
   [transactions.py:269-274](velvet-elves-backend/app/api/v1/transactions.py#L269-L274):
   non-admin/non-team-lead callers get `user_id=current_user.id`
   passed to the repo. No `role=attorney` query param is needed for
   the intake matter selector — the existing endpoint already returns
   the attorney's assigned matters when called with the attorney's
   token. Drop the rev 1 "add a role query param" suggestion.

7. **No new LLM calls.** The honest-LLM-cost rule still applies. Reuse
   existing AI-derived fields (`ai_prepared_next_step`, parsed document
   results, cached dashboard counts) when navigating into the Matter
   Workspace. Do not call the LLM just to render the workspace or a
   topbar chip.

8. **Recent dashboard activity projection.** To render the new
   "Recent matter activity" rail card, extend
   `GET /api/v1/dashboard/attorney` with `recent_activity[]` sourced
   from `audit_logs` for the attorney's assigned matters. Shape:
   `{id, transaction_id, label, action, actor_name, created_at}`. This
   is a read-only dashboard projection; no new audit writes are needed.

9. **Legal packet intake orchestration.** Generic upload does not create
   attorney review rows. Add either:
   - a dedicated `POST /api/v1/attorney/intake` orchestration endpoint
     that accepts a matter id + uploaded document ids and creates
     `attorney_review_items` from parse output; OR
   - a backend service called after `parse-document` completes that maps
     extracted packet facts into review items.
   The UI should not claim "indexed" or "review checklist created"
   until this path has run or queued successfully.

10. **Frontend detail route and constants.** Add a
    `ROUTES.TRANSACTION_DETAIL(id)` helper that returns
    `/transactions/${id}`, plus a protected `/transactions/:transactionId`
    route in `App.tsx`.
    This is required before any dashboard, matter-list, release-queue,
    or intake success CTA can deep-link to the Matter Workspace.

11. **Attorney sidebar routes.** Current Attorney sidebar links point
    to `/dashboard/attorney?filter=...`, and "Communication Log" points
    to an unimplemented `?panel=communications`. After removing
    dashboard filters, update those links to:
    - Attorney Queue → `/transactions/active?tab=all`
    - Pending Review → `/transactions/active?tab=needs-review`
    - Ready To Release → `/transactions/active?tab=ready-to-release`
    - Clean Files → `/transactions/active?tab=clean-files`
    - Missing Documents → `/transactions/active?tab=missing-docs`
    - Communication Log → remove/defer until a matter-scoped surface
      exists, or link only from an individual Matter Workspace.

---

## Part 8 — Execution order

Phases are sequenced so the dashboard defect fix lands first (small,
high-value), then the workspace gets built up incrementally.

### Phase A — Dashboard remediation + route hygiene (lands first)
1. Remove `FilterTabStrip`, `?filter=` handling, `FilterKey` /
   `FILTER_TABS` / `deriveFilterKey` / `isFilterKey` /
   `filteredMatters`. KPI `onClick` re-points to
   `/transactions/active?tab=needs-review` / `missing-docs` /
   `ready-to-release` / `clean-files`.
2. Remove the "Upload a legal packet" `DashboardCard`, `uploadCardRef`,
   and the `?panel=upload` scroll-into-view effect — all in one PR.
3. Delete `expandedMatter`, `setExpandedMatter`, `MatterCardItem`,
   `matterRowRefs`, `focusMatter`, and the `MatterDocChecklist`
   `onSendPacket` wiring inside the inline expand. **Do not** add an
   "All open matters" replacement card.
4. Expand the "Matters needing legal judgment" hero from top 3 to top
   ~5 by urgency; give the card header a "View matter list" link to
   `/transactions/active`.
5. Backend companion: extend `GET /api/v1/dashboard/attorney` with
   `recent_activity[]` from `audit_logs`, then add the rail card.
   Without this backend payload, omit the card rather than rendering
   fake activity.
6. Update "Quick actions" rail card to include a secondary "Upload a
   legal packet" → `/attorney/intake`; remove/defer "Communication
   log" because its current route is not attorney-scoped.
7. Add `ROUTES.ATTORNEY_INTAKE = '/attorney/intake'` and a minimal
   protected route shell so the upload CTA is never a dead link after
   the dashboard upload card is deleted. Phase C completes the actual
   upload/indexing workflow.
8. **Topbar primary CTA** — retarget the existing
   `upload-legal-packet` handler from `/dashboard/attorney?panel=upload`
   to `ROUTES.ATTORNEY_INTAKE`. Do not add a second Attorney branch.
9. **Attorney sidebar** — move filter links off the dashboard:
   `Attorney Queue` → `/transactions/active?tab=all`,
   `Pending Review` → `/transactions/active?tab=needs-review`,
   `Ready To Release` → `/transactions/active?tab=ready-to-release`,
   `Clean Files` → `/transactions/active?tab=clean-files`,
   `Missing Documents` → `/transactions/active?tab=missing-docs`.
   Remove/defer "Communication Log" until a matter-scoped surface
   exists.
10. **`/transactions/active` Attorney view — URL-driven tabs.** Migrate
   `AttorneyWorkspacePage` (or the wrapper that routes to it) from
   `useState(activeTab)` to `useSearchParams('tab')`. Update the page
   header title from "Attorney Dashboard" to "Attorney Matters" so the
   page no longer claims to be a dashboard.
11. Pattern-13 column-height re-check; fold "Per-state closing
   posture" into the Drift card if needed.
12. Update `ROLE_DASHBOARDS_DESIGN_UPDATE_PLAN.md` Phase B entry —
    record the deviations from rev 5.
13. **Tests.** Vitest: cover the topbar role branch + the dashboard's
    KPI click-through (with `MemoryRouter`); add a smoke test that
    `?panel=upload` no longer scrolls anywhere (it's been removed).
    Pytest: cover the `recent_activity` payload when audit rows exist
    and verify tenant/assignment scoping.

**~1.25 days.** Includes a small backend dashboard projection and a
route-shell cleanup so the dashboard remediation is shippable by itself.

### Phase B — Attorney Matter Workspace skeleton
1. Add `ROUTES.TRANSACTION_DETAIL(id)` and register
   `/transactions/:transactionId` in `App.tsx`. New page:
   `pages/transactions/AttorneyMatterWorkspacePage.tsx`.
   Rename the existing
   `pages/transactions/AttorneyWorkspacePage.tsx` to
   `AttorneyTransactionsListPage.tsx` (the file's role is *the list*,
   not *the workspace*). Add a `TransactionDetailRouter` that renders
   the Attorney workspace for Attorney users and the generic transaction
   detail layout for other roles when that layout exists.
2. Backend: add `GET /api/v1/transactions/{id}/attorney-detail`
   returning the full per-matter payload (§7.2 gap 2). Use the spec'd
   path, not the `/attorney/matters/{id}` rev 1 invented.
3. Backend: un-mock `PATCH /api/v1/attorney/matters/{id}` (§7.2
   gap 3). Add the `attorney_matter_state` sidecar table (or equivalent
   attorney-specific state column) the gap defines; have the handler
   upsert real state and surface it in the detail endpoint's response.
4. Backend: add `GET /api/v1/attorney/matters` for the
   matter-switcher list (§7.2 gap 4).
5. New component `components/dashboard/attorney/MatterUploadDropZone.tsx`
   wrapping `UploadIntakeCard` with a pre-filled matter id.
6. Wire `MatterSwitcher` to the new list endpoint via a shared React
   Query key (`['attorney', 'matters']`) for the workspace and intake
   page. If the endpoint returns a lightweight shape, update
   `MatterSwitcher` props instead of forcing it to accept a partial
   `AttorneyMatterCard`.
7. Compose existing matter sub-components in the layout described
   in §4.2 — confirm `MatterSummaryRow` works as a standalone top
   block (it's currently embedded inside `MatterCardItem`'s expanded
   body).
8. Wire `SendPacketModal` for release; wire the un-mocked
   `PATCH /api/v1/attorney/matters/{id}` for hold.
9. Pattern-16 audit on the file-checklist rows.
10. **Tests.** Pytest: cover the new
    `/transactions/{id}/attorney-detail` endpoint (happy path, 404,
    cross-tenant 403); cover the un-mocked PATCH (state actually
    persists; audit row still written); cover the new
    `/attorney/matters` list endpoint. Vitest: render-only test for
    the workspace skeleton with a mocked detail response.

**~2 days.** Three backend additions plus storage change.

### Phase C — Legal Packet Intake
1. Complete the `pages/legal/LegalPacketIntakePage.tsx` route shell
   added in Phase A.
2. Matter selector pulling from `GET /api/v1/attorney/matters`. If
   Phase C is pulled forward before Phase B, temporarily use
   `GET /api/v1/transactions?status=Active`; no `role=attorney` param
   is needed (§7.2 gap 6).
3. Drop zone reusing `UploadIntakeCard` and `useUploadDocument`.
4. Queue `POST /api/v1/ai/parse-document/{document_id}?background=true`
   after each upload and poll status.
5. Add the attorney-intake orchestration path from §7.2 gap 9 so parse
   output creates/updates `attorney_review_items` for the selected
   matter.
6. **Tests.** Vitest: render-only test confirming the matter selector
   is required before upload submits; render-only test for the
   success toast + "Open matter" deep-link. Pytest: cover the
   review-item creation path if implemented as a new endpoint/service.

**~1 day.** More than a visual upload page because the flow must
honestly queue parsing and create attorney review state.

### Phase D — Releases queue wiring
1. Backend: extend `GET /api/v1/attorney/releases` with
   `?status=ready|released` (§7.2 gap 1). For `ready`, query
   `attorney_review_items` grouped by transaction with an anti-join
   against `attorney_packet_releases`.
2. New page `pages/legal/AttorneyReleasesPage.tsx` at
   `/attorney/releases`.
3. Two-section layout (or tab strip — filter tabs are appropriate on
   list pages, per §1.1).
4. Per-row release CTA wires `SendPacketModal`.
5. Add `ATTORNEY_RELEASES` to `utils/constants.ts`.
6. **Tests.** Pytest: cover `?status=ready` returns matters with all
   sign-offs cleared and no release row; cover `?status=released`
   returns existing payload. Vitest: render-only test for the
   two-section layout.

**~1 day.**

### Phase E — Spec doc updates and final QA
1. Verify route constants in `utils/constants.ts` cover
   `ATTORNEY_INTAKE`, `ATTORNEY_RELEASES`, and
   `TRANSACTION_DETAIL(id)`. The matter workspace path is the shared
   `/transactions/:id` route; do not add a separate
   `ATTORNEY_MATTER_WORKSPACE` route constant unless the shared route
   proves unworkable.
2. Manual QA per the §3.4 checklist in `FRONTEND_UI_WORKFLOW_LOGIC.md`
   — confirm each new surface behaves per spec.
3. **Spec doc updates** (broader than rev 1 committed):
   - `SYSTEM_DESIGN.md` §3.4 (Attorney Dashboard description) — drop
     the filter-tab spec; replace with the overview-only contract.
   - `SYSTEM_DESIGN.md` §4.3.1e (Attorney Dashboard Landing Page) —
     same drop; refresh the page-structure diagram.
   - `SYSTEM_DESIGN.md` §7.1 — re-point `/attorney/queue` redirect
     target from `/dashboard/attorney` to `/transactions/active`.
   - `SYSTEM_DESIGN.md` page tree + route table — add
     `/transactions/:id` (Attorney layout), `/attorney/intake`,
     `/attorney/releases`.
   - `SYSTEM_DESIGN.md` §3 API inventory — record the new
     `/transactions/{id}/attorney-detail`, `/attorney/matters` list,
     `/attorney/releases?status=` extensions.
   - `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.4 — drop the filter-tab and
     filter-button copy; add the new "Matters needing judgment" hero
     spec (top 5) and the new "Recent matter activity" rail card spec.
   - `FRONTEND_UI_WORKFLOW_LOGIC.md` §7.1 — update the redirect note.
   - `MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md` — record that the
     upload-card-on-dashboard prescription was overridden.

**~½ day.**

**Total: ~5.25 dev days plus QA.**

---

## Verification checklist (per phase)

- `npx tsc --noEmit -p tsconfig.app.json` — clean.
- `npx eslint <changed files>` — clean.
- `npx vitest run <attorney tests>` — passes.
- `venv/Scripts/python.exe -m pytest app/tests/ -k "attorney"` — passes.
- Manual, logged in as an Attorney:
  - Dashboard opens with KPI strip + expanded judgment-needed hero
    (top 5) + rail (with new "Recent matter activity" card).
    **No filter strip. No upload card. No "all open matters" list.**
  - Topbar primary action reads "+ Upload Packet" (not "+ New
    Transaction") and navigates to `/attorney/intake`.
  - Clicking a KPI lands on `/transactions/active?tab=…` AND the
    target page reflects the requested tab (URL-driven).
  - Clicking a matter row in the hero lands on the Matter Workspace.
  - Matter Workspace renders the matter switcher + command strip +
    summary tiles + file checklist + AI brief + timeline + activity +
    people.
  - Sign-off toggles persist in `attorney_review_items` and write an
    audit row.
  - "Release packet" opens `SendPacketModal` and routes through the
    release endpoint.
  - `/attorney/intake` accepts uploads, requires matter selection,
    and deep-links back to the matter.
  - `/attorney/releases` shows ready-to-release + recently-released
    sections.
  - No string visible to end users references a milestone or version
    number (pattern 14 audit).
  - No inline filter strip on the dashboard (pattern 6 corollary — a
    dashboard is an overview, not a list page).

---

## Risks / open items

1. **Shared transaction-detail route complexity.** The plan now chooses
   `/transactions/:id` for the Matter Workspace. The risk is that the
   eventual generic transaction detail page may have different layout
   needs. Mitigation: route through a small `TransactionDetailRouter`
   and keep `AttorneyMatterWorkspacePage` isolated behind the Attorney
   role branch.

2. **"Ready to release" defining condition.** Today, the backend
   marks a packet released only after the explicit release call.
   "Ready to release" needs a derived definition: at least one review
   item exists, all required `attorney_review_items` are signed-off, and
   no `attorney_packet_releases` row exists yet. Verify this matches
   what the dashboard's `drift_summary.release_ready_count` reports.

3. **State Rules as a standalone page** can be deferred. The modal
   covers the MVP need — *with the caveat that the modal is currently
   fed by a hardcoded backend response* (§7.1). If multi-state
   attorneys start wanting a cross-reference view, the per-state
   handler needs real data first, then a page can wrap it.

4. **No topbar AI briefing for Attorney.** This is now a deliberate
   MVP decision, not an unresolved data-source question. If product
   later wants an Attorney briefing chip, derive it from dashboard
   counts / cached AI fields and keep `showAiBriefingBar` role-safe.

5. **Attorney hold storage shape (Phase B gap 3).** The recommendation
   is a dedicated `attorney_matter_state` row keyed on transaction_id.
   Avoid `legal_hold` naming because tenant/platform legal holds
   already exist. Decide the exact columns before writing the migration.

6. **Dashboard slimming creates a load-bearing rail.** With the main
   column reduced to the expanded hero plus the new "Recent matter
   activity" card on the rail, the rail is now the page's primary
   surface area. If real-world attorney data turns out to have very
   few recent events (slow firms, quiet weeks), the activity card
   will frequently be empty and the rail will feel hollow. Acceptable
   for MVP — if it becomes a recurring complaint, fall back to
   surfacing the *last N events* across a longer window (90 days
   instead of 14) before reintroducing list content on the main column.

7. **Legal packet intake may expose a deeper backend gap.** Uploading
   and parsing documents exists, but mapping parse output into
   attorney-specific review items may not. If that service is larger
   than expected, Phase C should ship only once the orchestration is
   honest, not as a cosmetic upload page.

8. **Attorney communication log remains unresolved.** Jake's design and
   the current sidebar both imply communication review, but the live
   route points to admin/team communication audit. Keep communication
   history inside the Matter Workspace activity/context panels until a
   proper attorney-scoped communication surface is designed.

**Decisions baked into rev 3 (no longer open):**

- **Matter switcher data source.** Rev 1 risk #2 → decided. The
  workspace and intake page subscribe to a new
  `GET /api/v1/attorney/matters` list endpoint via the React Query
  key `['attorney', 'matters']`. See Phase B step 4.

- **Existing `AttorneyWorkspacePage.tsx` naming.** Rev 1 risk #6 →
  decided. Phase B renames the file to
  `AttorneyTransactionsListPage.tsx` and gives the per-matter detail
  page the `AttorneyMatterWorkspacePage.tsx` name. "Workspace"
  semantically belongs to the per-matter surface.

- **Per-matter detail endpoint path.** Rev 1 §7 gap 2 → decided.
  Implement `GET /api/v1/transactions/{id}/attorney-detail` — the
  path already named in `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.4 line 956.
  Do not introduce `/api/v1/attorney/matters/{id}` for the detail
  endpoint (the `matters` namespace is reserved for the list endpoint
  and the un-mocked PATCH).

- **Topbar upload target.** The Attorney primary CTA uses the existing
  `upload-legal-packet` action and navigates to `/attorney/intake`;
  dashboard `?panel=upload` is removed with the dashboard upload card.

---

*Plan drafted: 2026-05-21 (rev 1). Revised: 2026-05-21 (rev 2), then
review-corrected: 2026-05-21 (rev 3).*

*Reference implementations to mirror:*
- *`pages/dashboards/SoloAgentDashboardPage.tsx` (overview discipline:
  no filter strip, no functional surfaces).*
- *`pages/fsbo/FsboOverviewPage.tsx` (overview that links out to
  list / document / support surfaces rather than hosting them
  inline).*
- *Jake's `VE-AttorneyDashboard.html` — read as a per-matter workspace
  draft, not as a dashboard.*

*Cross-reference: `SYSTEM_DESIGN.md` (Attorney role, permission matrix,
endpoint inventory); `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.4 and §7;
`ROLE_DASHBOARDS_DESIGN_UPDATE_PLAN.md` rev 5 (Phase B prescription
that this plan now refines); `STYLE_GUIDE.md` (§15, §16).*
