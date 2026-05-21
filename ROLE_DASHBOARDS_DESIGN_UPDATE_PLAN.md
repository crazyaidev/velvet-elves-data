# Role Dashboards — Design Update Plan (rev 5)

## Context

The Solo Agent Dashboard (`/dashboard/agent`) remains the **reference
implementation** for every other role dashboard. Phase A (Team Leader)
and Phase D (Admin retrofit) shipped during this revision cycle —
the patterns they exercised, the deviations they forced, and the
backend work they uncovered are folded into this rev 4 plan.

### Corrections that drove rev 4

Three things changed our model since rev 3:

1. **Pure-CSS sticky bottom-alignment has a hard geometric limit.**
   Rev 3 described pattern 6 as "smart coding, not hard-coding" and
   "works dynamically regardless of which column is taller." That is
   only true when **both columns clear the viewport**. When the
   shorter column is shorter than `viewport − bottom-padding`, sticky
   can't bottom-align it — the sticky element runs out of "travel."
   No JS hybrid resolves the conflict between *"pinned at top while
   the other scrolls"* and *"ends level at the bottom"* for a single
   page scroll; the geometry forbids it.

   The right way to bottom-align is **structural parity with the
   Agent Dashboard** (same number and approximate height of cards in
   each column), not a clever mechanism. A failed attempt to switch
   between sticky and stretch-distribute modes via `ResizeObserver`
   was rejected — it diverged the Team Leader's scroll behaviour
   from the Agent reference and the user explicitly asked us to
   *reference the Agent Dashboard UI*. **Codified as pattern 13.**

2. **Backend was not out of scope.** Rev 3's Scope said *"No backend
   work."* Multiple backend issues surfaced during Phase A and the
   Admin pass: team-dashboard scoping that excluded admin-created
   transactions, implicit-team handling for unconfigured workspaces,
   sidebar endpoints defaulting to personal scope regardless of role,
   and an AgentDrillDownDrawer that was structurally a centered modal
   pretending to be a drawer. Phase F (Backend companion) is added
   to record what shipped and what remains.

3. **User-facing chrome assumptions need per-phase confirmation.**
   Rev 3 prescribed a Personal/Team toggle for Team Leader; after
   building it, the user removed it as "unnecessary chrome." Going
   forward, any toggle / customize / view-switcher / role-switcher
   is gated on a one-line confirmation with the user before build.
   **Codified as pattern 15.**

   A parallel rule emerged for *copy*: customer-facing strings must
   never reference internal milestone numbers, version numbers, or
   roadmap artifacts. The original Team Leader build carried over
   *"Activation opens in Milestone 5.2 (billing)"* from the legacy
   page — that text leaks internal scheduling to end users. Replaced
   with neutral *"paid add-on / coming soon"* phrasing. **Codified
   as pattern 14.**

---

## Design sources (authoritative for role intent)

Per `MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md` § 1, the HTML
mockups are "authoritative for role intent, not pixel-perfect law."
For each role, **read both** the initial and the updated mockup and
incorporate **every feature** in them (minus explicit exclusions):

| Role | Jake's initial | Updated (preferred) |
| --- | --- | --- |
| Solo Agent | `VE-HomepageDashboard-SoloAgent.html` | `completed_designs/ve-homepage_dashboard-solo_agent.html` |
| Team Leader | `VE-HomepageDashboard_TeamLeader.html` | `completed_designs/ve-homepage_dashboard-team_leader.html` |
| Attorney | `VE-AttorneyDashboard.html` | `completed_designs/ve-attorney_dashboard.html` |
| FSBO | `VE-FSBODashboard.html` | `completed_designs/ve-fsbo_dashboard.html` |
| Admin | *(none — rebuilt directly)* | live `AdminDashboardPage.tsx` |

Where the two mockups disagree, the updated `completed_designs/`
version wins; where STYLE_GUIDE § 16 disagrees with both, the style
guide wins on chrome but the mockups win on *which role-specific
blocks exist*.

---

## Established design system (the canonical reference)

Patterns 1–12 are unchanged from rev 3 except pattern 6, which is
restated below to reflect its actual geometric envelope. Patterns
13–15 capture the rev 4 corrections; pattern 16 captures the rev 5
priority-row standardization.

### 1. Page shell (§ 15.1) — no chrome

```jsx
<div className="flex h-full min-h-0 flex-col overflow-hidden bg-ve-bg">
  <div className="flex-1 min-h-0 overflow-y-auto px-3 md:px-6 pt-5 pb-12">
    <div className="space-y-4 md:space-y-5">
      {/* role-specific banner (optional) */}
      {/* KPI strip */}
      {/* main + rail grid */}
    </div>
  </div>
  <FloatingAskAi hint="…" />
</div>
```

No `DashboardPage`, no `DashboardHeader`, no greeting, no Customize
button, no `WidgetOrderManager`, no `max-w-[1400px]`. A single
page-level scroll — never per-column scroll containers.

### 2. Shared primitives — extended tone palette

`@/components/dashboard/shared/`:

- `DashboardCard` — the one card shell (icon tile → mono eyebrow →
  serif title → optional description; `action` / `trailing` header
  slots; `compact`, `flush`, `bodyTint='soft'` variants).
- `DashboardStat` — inner stat tile.
- `DashboardKpiCard` — KPI strip card.

**Tone palette:** `neutral · brand · green · amber · blue · purple ·
red`. Both `DashboardCard` and `DashboardKpiCard` accept these.

### 3. Color is a design tool — no all-neutral stacks

Every card carries an intentional tone. A rail of identical neutral
icon tiles is a defect. Assign tones by *meaning*: green = health /
positive, amber = drift / warning, blue = filters / utility, purple =
documents / activity, red = critical, brand (orange) = AI / hero /
monetization. Solo Agent's rail is the reference.

**Component-level corollary** (added in rev 4): identifier tiles
(avatars, role chips, status pills) inside cards need actual contrast
against the card background. `bg-X-soft/30 text-X` (30%-opacity
pale) renders unreadable at small sizes. Use the brand pairing the
DashboardCard family uses: `bg-X-soft text-X-xdark font-semibold
ring-1 ring-inset ring-X-border`. The AgentBoard avatar fix
(`UsersByRoleBars` role bars, `AgentBoard` avatar tile) is the
reference.

### 4. Card proportionality — chrome must fit content

Rules derived from review feedback:

- **No duplicate blocks.** Solo Agent's "Production snapshot"
  duplicated the KPI strip and was deleted. Audit every dashboard.
- **Narrow content → rail; substantial content → main.**
- **Trim verbose descriptions.** Self-explanatory blocks drop their
  `description` so the header doesn't dwarf the body.
- **Don't wrap thin content in oversized chrome.** Shrink ring / tile
  sizes in `compact` rail cards.

### 5. Rail width + content wrapping

Rail is **440px** at `lg+` (`lg:grid-cols-[minmax(0,1fr)_440px]`).
Rail content **wraps** (`line-clamp-2` / `-1`) rather than truncating
mid-word; pills move beside titles so the title gets full width.

### 6. Two-column scroll with bottom-aligned baselines (with caveat)

The mechanism (CSS-only) — unchanged:

- Grid `align-items: stretch` → both cells share the row height
  (= the taller column's natural height).
- **Both** columns are `lg:sticky lg:top-0 lg:self-start`. Only the
  shorter column has empty room in its cell, so only it can sticky-
  shift — it "waits" pinned to the top while the taller column
  scrolls past. When its sticky budget is spent, its bottom is flush
  with the cell bottom = the taller column's bottom.

**Hard geometric envelope** (rev 4): the mechanism produces a
perfect bottom-align **iff** the shorter column's natural height
`R ≥ viewportHeight − bottomPadding`. When the shorter column is
shorter than the viewport (sparse data, tall monitor), there is not
enough scroll distance for it to traverse to its area bottom — its
bottom floats above the taller column's bottom by `(V − P − R)` px.
No CSS or JS that preserves *pin-at-top during scroll* can close that
gap on a single page scroll — see the rev-4 correction note above.

The lever to pull is **pattern 13**, not the mechanism: bring the
columns into structural parity so neither is meaningfully shorter
than the viewport.

### 7. Detail panels need lazy-fetched data, not the dashboard payload

Role-dashboard payloads (`useAgentDashboard`, etc.) are intentionally
**minimal** — e.g. `priority_transactions` carries no tasks/dates/
contacts. Rich detail comes from `/dashboard/transaction-cards`
(`useTransactionCards`). Fetch the rich cards, build a
`transaction_id → card` map, and **merge** `inline_tasks` /
`key_dates` / `contacts` into each summary item before rendering its
expandable body. No backend change required.

### 8. Progressive disclosure for contact details

Show **real** data (actual address / number as `mailto:` / `tel:`
links), but collapsed by default — name + role visible, a chevron
hints expandability, click reveals the contact lines. Rows with no
info aren't expandable.

### 9. Alert / action cards: explicit buttons, not whole-card clicks

Action-queue and alert rows must expose explicit, role-aware action
buttons (e.g. "Open deal →"), never a single whole-card click target.
(Consistent with the standing alert-card clickability rule.)

### 10. Role-specific monetization & banners

Solo Agent and Team Leader carry the **AI Coach upsell** (a paid
add-on, **one teaser only — never activated UI**). It lands as a
**full-width, compact banner at the very top**, rendered as a
two-column hero. The "Today's coaching move" copy is **dynamic**
(keys off the role's stale-comm / coaching-needed metric).
Attorney / FSBO / Admin do **not** get this banner.

> Phase A clarified an internal contradiction in rev 3's wording
> (item 3 placed the banner at the top *and* item 6 listed a separate
> rail teaser). The "exactly once" rule from M5.1 § 4.2 governs:
> banner only, no rail teaser. The existing locked-explainer modal
> is wired to the banner's CTAs.

### 11. Shell CTA placement (cross-cutting)

The "+ New Transaction" CTA renders in **both** the sidebar footer
**and** the topbar for internal roles (Agent / TransactionCoordinator
/ TeamLead). FSBO stays sidebar-only; Attorney's CTA is "Upload Legal
Packet"; Client / Vendor have no transaction-creation CTA.

### 12. Empty states everywhere

Every list / feed / chart that can render empty needs an explicit
non-loading empty state (`EmptyState`, `tone='brand'` for hero
blocks), distinct from the loading skeleton.

### 13. Reference, don't reinvent — structural parity is the lever

When a new dashboard should *match* an existing one's behaviour
(scroll, alignment, scope), match its **structure byte-for-byte**:
same grid markup, same column class names, the same approximate
**count and height of cards** in each column. Don't introduce a
new mechanism (custom hooks, mode switching, ResizeObservers) when
the reference works.

**Concrete corollary for pattern 6:** the sticky bottom-alignment
needs equivalent column heights. The Team Leader rail originally
had 5 cards while the Agent reference has 6; on a tall monitor the
shorter Team Leader rail couldn't reach its cell bottom via sticky
travel. The fix was to add a 6th rail card (`Quick actions`,
mirroring Agent's) so the rails are structurally peers — not a JS
hybrid that switched modes by viewport height.

If a future dashboard's data shape genuinely produces a much shorter
rail, the *lever* is content: move a block from main → rail, split
a dense block into two, or accept that the bottoms won't perfectly
align on tall monitors. Do **not** layer JS over the CSS-sticky
contract — that path was attempted and reverted.

### 14. Customer-facing copy never references internal milestones

Banners, modals, toasts, tooltips, button sub-lines, and any other
string that an end user sees must not name internal milestones
(*"Milestone 5.2"*, *"M5.x"*, *"Phase 5"*), version numbers, or
roadmap artifacts. Use neutral, customer-appropriate phrasing —
*"paid add-on"*, *"coming soon"*, *"available next release"*, etc.

Reference: the rev-3 AI Coach copy carried *"Locked · activates in
Milestone 5.2"* on the banner and *"Activation opens in Milestone
5.2 (billing)"* in the modal / toast. Both were replaced with
*"Locked · paid add-on"* and *"AI Coach is a paid add-on —
activation is coming soon."* Internal milestone references stay
in *internal* documents (this plan, the milestone tracker), never
in shipping product UI.

### 15. Confirm chrome before adding

Before building any user-facing chrome whose necessity isn't already
universally agreed — view toggles, customize / widget-order buttons,
role-switchers, dashboard layout pickers, "edit dashboard"
affordances — confirm with the user in one line that it should
exist on this surface. The Personal/Team toggle was prescribed in
rev 3, confirmed during build, then removed post-build as
unnecessary chrome; that round-trip is exactly what this rule is
designed to skip.

URL-driven filter tab strips (Attorney's `?filter=`) are a separate
category — they're navigation, not chrome — and don't need this
confirmation step.

### 16. Priority / action-queue rows share one vocabulary

The "priority" / "action queue" sections across every role
dashboard — Admin Priority, Team Priority, Today Action Queue —
render rows against a single visual contract. The contract lives
inline in three components today (`AdminActionQueue`,
`ActionQueueList`, `InterventionQueueItem`); a shared
`PriorityQueueRow` extraction is queued for Phase E.

**Row markup contract:**

- `<article>` shell — `overflow-hidden rounded-xl border
  border-ve-border bg-white shadow-card` + hover lift
  (`hover:-translate-y-[1px] hover:border-ve-border-strong
  hover:shadow-card-hover`).
- **4 px severity rail** on the left edge, color keyed off
  `status_color` (Agent / Team) or `severity` (Admin).
- **44×44 tinted circular icon tile** with `ring-1 ring-inset`,
  matched to the rail tone.
- **Pill row** inline above the title — status / severity pill in
  the matching tone, then optional secondary badges (Team's
  closing-date badge, Admin's category badge, Agent's subtitle).
- **Serif title** (`font-serif text-[15px] leading-snug`).
- **Muted next-step / why line** (`text-[12.5px]
  text-ve-text-muted`).
- **Exactly one filled brand-orange primary `Button`** via `asChild`
  + `<Link>`, with trailing `ArrowRight`. Label is consistent
  across roles for the same target — *"Open deal"* for transaction-
  linked rows on Agent / Team; the Admin row reuses its own
  `action_label` for role-targeted destinations. Never a whole-
  card click target (pattern 9 still in force).

**One CTA per row.** Per-row affordances unique to a single queue —
like Team's earlier *"Upload here"* + inline upload flyout — are
removed in favor of routing through the primary CTA to the deal
page, where role-appropriate actions live. Consistency outranks
per-row convenience. Secondary information (closing-date, category)
stays in the pill row as a badge, not a second button.

Shared tone palette (keyed by `status_color`):
`red / amber / blue / green / purple → bg-ve-X` rail +
`bg-ve-X-bg ring-ve-X-border text-ve-X-text` tile +
`border-ve-X-border bg-ve-X-bg text-ve-X-text` pill.
Neutral fallback when the row's status key is unrecognized.

---

## Scope

**In scope (5 dashboards + backend companion):**

1. ~~Solo Agent (`/dashboard/agent`)~~ — **done**, reference impl.
2. ~~Team Leader (`/dashboard/team`)~~ — **done** (Phase A).
3. Attorney (`/dashboard/attorney`) — Phase B.
4. FSBO Overview (`/fsbo`) — Phase C.
5. ~~Admin (`/dashboard/admin`)~~ — **done** (Phase D).
6. Backend companion — Phase F (partially done; follow-ups remain).

**Out of scope:**

- Client portal (`/client/transactions`) and Vendor portal
  (`/portal/vendor`) — list / document portals, not dashboards.
- Backend AI / data-contract changes beyond what Phase F lists. All
  enrichment uses existing endpoints (`/dashboard/transaction-cards`,
  etc.).
- New LLM calls or aggregations (honours the cost-effective-LLM rule
  — reuse cached payloads, never re-call for data already on the
  page).
- AI Coach product activation — one locked teaser only.

---

## What's already landed

### Phase 0 — primitives in the shared kit
`DashboardCard` / `DashboardStat` / `DashboardKpiCard` in
`src/components/dashboard/shared/`; admin `Admin*` files are
re-export shims. Tone palette `neutral · brand · green · amber ·
blue · purple · red`.

### Phase 1 — Solo Agent
Fully rebuilt to all 12 patterns.

### Shell CTA fix (pattern 11)
Landed before this revision.

### Phase A — Team Leader (DONE, with deviations from rev 3 recorded)

What actually shipped vs. rev 3's prescription:

- ✓ § 15.1 shell, single page scroll, sticky bottom-aligned 440px
  grid (mechanism per pattern 6).
- ✗ **NO Personal/Team toggle.** Removed post-build per pattern 15
  (user judged it unnecessary chrome). `useTeamDashboard()` is
  called without a view argument; defaults to `'team'`. The
  § 16.1.1 canonical example was updated to drop the toggle —
  Attorney's `?filter=` tabs are now the sole example.
- ✓ AI Coach upsell banner at top (single teaser, pattern 10).
  **Copy follows pattern 14:** *"Locked · paid add-on"* on the
  banner, *"AI Coach is a paid add-on — activation is coming soon."*
  in the modal. CTAs open the existing modal.
- ✓ KPI strip per the plan (Pending GCI green · Pipeline volume blue
  · Annual pace orange · Pipeline health red/green).
- ✓ Main column: Intervention queue (hero, brand), Agent board,
  Pipeline health.
- ✓ Rail (compact, colored, **6 cards** — see pattern 13): Team
  health (green), Team intelligence (brand — Solo-Agent-parallel
  AiPortfolioIntel; not in rev 3's rail list, added during Phase A
  to preserve `ai_intelligence` payload), Drift (amber), Fast filters
  (blue), Closings 14d (purple), **Quick actions (brand, 6th card)**
  — added so the rail height matches Agent's, satisfying pattern 6's
  geometric envelope on tall monitors.
- ✓ `InterventionQueueItem` shares the AdminActionQueue /
  ActionQueueList row vocabulary and exposes a single **"Open deal"**
  primary action — matching Solo Agent's Action queue. The earlier
  *"Open file"* + *"Upload here"* + inline upload flyout combo was
  removed per the consistency rule (uploads belong on the deal page,
  not as a per-row affordance on every intervention). The only
  team-specific row content remaining is the **closing-date badge**
  ("Closes Mar 24" — red ≤7d / amber ≤14d / neutral) inline with the
  status pill. Pattern 9 still satisfied by the explicit "Open deal"
  button.
- ✓ `TeamFastFilters` and `PipelineHealthPanel` given `embedded`
  variants so they sit inside `DashboardCard` without nesting card-
  in-a-card (resolves rev 3 risks 1 & 2).
- ✓ Empty states throughout.
- ✓ Avatar contrast fix on `AgentBoard` (pattern 3 corollary):
  `bg-ve-orange-soft text-ve-orange-xdark font-semibold ring-1
  ring-inset ring-ve-orange-border`.
- ✓ `AgentDrillDownDrawer` repositioned as a real right-side drawer:
  override the centered-modal positioning utility family
  (`fixed inset-y-0 right-0 left-auto top-0 translate-x-0
  translate-y-0 flex flex-col gap-0`); drop the redundant local
  close button (Radix renders one); add `flex-1` to the scrollable
  content.

### Phase D — Admin Dashboard retrofit (DONE)

- ✓ 440px rail (pattern 5).
- ✓ Sticky bottom-aligned grid via the inline two-column-sticky
  pattern (committed: `3fb27fd`). `MainRailGrid` still used by other
  surfaces; Admin uses the inline form pending Phase E extraction.
- ✓ Colored rail (pattern 3) — Health → green, Deals by stage →
  blue, Recent activity → purple. `UsersByRoleBars` now colors each
  bar by role (Admin orange, TeamLead blue, TC purple, Agent green,
  Attorney charcoal, Client neutral, FSBO charcoal-soft, Vendor
  amber) — same palette as the role chips on Team Members page.
- Other rev-3 Phase D items (proportionality audit, lazy-fetch
  detail) found no regressions and were left as-is.

### Priority queue row vocabulary — cross-cutting (DONE)

Pattern 16's row contract landed across all three priority sections
on Admin, Team, and Agent dashboards:

- ✓ `AdminActionQueue` (Admin Priority) — already shipped in
  Phase D; this is the reference implementation.
- ✓ `ActionQueueList` (Solo Agent — *Today Action Queue*) rewritten
  to render rows in the AdminActionQueue `<article>` shell:
  severity rail keyed off `status_color`, tinted 44×44 icon tile,
  pill row (status_pill + optional subtitle badge), serif title,
  muted `next_step`, single filled *"Open deal"* `Button` →
  `/transactions/active?highlight=<tx>`. The legacy status-dot +
  outline-link layout is gone.
- ✓ `InterventionQueueItem` (Team Leader — *Team Priority*) aligned
  to the same shell. The team-specific **closing-date badge**
  ("Closes Mar 24" — red ≤7d / amber ≤14d / neutral) sits in the
  pill row alongside the status pill. The earlier *"Open file"* +
  *"Upload here"* + inline upload flyout combo was **removed in
  favour of a single *"Open deal"* primary action** — uploads
  belong on the deal page, not as a per-row affordance on every
  intervention row. Pattern 9 still satisfied by the explicit
  primary button.

The shared `PriorityQueueRow` extraction is **queued for Phase E**
(same reason the grid extraction is sequenced there: it touches
three live components at once and is safer to land after Phase B /
C have proven their priority-queue surfaces against the inline
vocabulary).

### Phase F — Backend companion (partially DONE; rev 3 said this was
out of scope, which was wrong)

What shipped during Phase A / Admin work:

a. **Team-dashboard scope — tenant + assignment-aware attribution**
   (`app/services/dashboard_aggregator.py::fetch_team`).
   - `all_tx` is now **tenant-scoped**, matching the Transactions
     page's `view=team` behaviour, so the dashboard never silently
     undercounts transactions the Transactions page already shows.
   - **Two-pass agent board**: first pass attributes each transaction
     via `created_by` / `transaction_assignments`; unattributed
     tenant transactions are then **folded into the current Team
     Leader's row** (small-business owner-of-record semantics — the
     leader's row matches what the Transactions page shows for
     "their" deals).
   - **Team totals** (`team_financials.pending_gci` /
     `pending_volume`) summed over `all_tx` directly, not over
     agent-board rows — admin-created / unattributed transactions
     count toward team totals even when attribution is imperfect.

b. **Implicit-team fallback** (`fetch_team` + `/api/v1/users`
   list endpoint).
   - When a TeamLead has no `team_id`, or has a `team_id` set but
     no *other* users carry it, the dashboard and `/users` list
     fall back to **tenant active team-eligible users** (`Agent` +
     `TeamLead` + `TransactionCoordinator`). Strict team scoping
     resumes when the team is properly populated.
   - `Agent` / `TC` without `team_id` still get "teammate-of-one"
     (`agent_payload_as_team_shape`).

c. **Sidebar scope — Admin + TeamLead → team scope** (frontend
   hooks).
   - `useDealStateCounts` and `useSidebarKpis` accept a `view` param;
     `AppLayout` passes `'team'` for Admin and TeamLead, `'personal'`
     for Agent / TC. The query key includes `view` so the cache
     differentiates. The backend `_user_filter` resolves
     `view=team + team_member_id=None` to no user filter (tenant
     scope) for both Admin and TeamLead.

d. **Sub-component `embedded` variants** for `TeamFastFilters` and
   `PipelineHealthPanel` (resolves risks 1 & 2; required to satisfy
   pattern 2 inside `DashboardCard`).

e. **`AgentDrillDownDrawer` repositioning** — see Phase A above.

**Phase F open follow-ups** (see *Phase F — Backend companion*
below).

---

## Phase B — Attorney Dashboard

**File:** `src/pages/dashboards/AttorneyDashboardPage.tsx`
**Designs:** `VE-AttorneyDashboard.html` +
`completed_designs/ve-attorney_dashboard.html`

Adds URL-driven filter tabs (navigation, not chrome — exempt from
pattern 15). **No AI Coach banner.** Attorney's primary CTA is
"Upload Legal Packet" (shell), so the legal-packet intake card
stays on the page. Internal milestone references in upload-flow
copy must follow pattern 14.

1. **§ 15.1 shell** + sticky bottom-aligned grid + 440px rail.
   Verify column-height parity per pattern 13: if the rail is
   visibly shorter than the matter stack on a typical monitor,
   add a 6th rail card (e.g. `Recent activity` or `Office hours`)
   before falling back to "bottoms can't align."

2. **Filter tab strip — content-level** (§ 16.1.1): first row of
   the scroll body, gutter bleed. Reads `filter` from the URL:
   `all`, `needs-review`, `missing-docs`, `ready-to-release`,
   `clean-files`. Counts from `data.filter_counts`. Ship the
   **§ 16.1.1 STYLE_GUIDE addendum** in this phase.

3. **KPI strip:**

   | KPI | Source | Tone |
   | --- | --- | --- |
   | Legal health | `legal_health_score` (%) | `red <70` · `amber <90` · else `green` |
   | Pending review | `filter_counts.needs_review` | `amber` |
   | Missing docs | `filter_counts.missing_docs` | `red` if `>0`, else `neutral` |
   | Ready to release | `filter_counts.ready_to_release` | `green` |

4. **Main column:**
   - **Hero — Matters needing legal judgment** (`tone='brand'`,
     icon `Scale`, `eyebrow='✦ Counsel decides'`,
     `bodyTint='soft'`).
   - **Matter card stack** (`DashboardCard flush bodyTint='soft'`).
     Each matter row expands to `MatterSummaryRow` /
     `MatterDocChecklist` / `MatterTimeline` / `MatterActivity` /
     `AiLegalBrief` / `MatterPeoplePanel`. People panel uses
     collapsible contact rows with real email/phone (pattern 8).
   - **Legal-packet upload intake** (`tone='brand'`, icon `Upload`,
     `eyebrow='✦ Legal packets'`) — `UploadIntakeCard` with attorney
     copy. *(Attorney is the one role where upload stays on the
     dashboard — contrast Solo Agent, where upload was excluded.)*

5. **Rail (compact, colored):**
   - Critical approval gates — `red` (or `brand`), icon
     `AlertOctagon`.
   - State rules summary — `blue`, icon `ShieldCheck`; "Open state
     rules" → `StateRulesModal` via `?panel=state-rules`.
   - Add a 6th card if needed for pattern-13 parity (see #1).

6. **Deep links preserved:** `?filter=needs-review` activates the
   tab and filters the stack; `?panel=state-rules` / `?panel=upload`
   open the modal / focus the upload card. **No AI control** checks
   sign-offs or releases packets.

7. Proportionality pass (pattern 4) — drop any block that duplicates
   a KPI; push narrow summaries to the rail.

8. Audit *all* user-facing strings on this page against pattern 14
   — no internal milestone or version references in any tooltip /
   modal / toast / button sub-line.

**STYLE_GUIDE § 16.1.1 addendum (ship here):**

> **§ 16.1.1 Tab strips on dashboards.** A dashboard may render a
> URL-driven tab strip *at the top of its content*. Style it per
> § 15.2 (bleeds to the gutter via `-mx-3 md:-mx-6`), but render it
> inside the scroll body, not a sticky header. No breadcrumb, no
> greeting, no page-title row above it. Attorney's `?filter=` tabs
> are the canonical example. (Tab strips are navigation; user-
> facing toggles — view switchers, customize buttons — follow
> § 16.x / pattern 15 instead and are gated on a build-time
> confirmation with the user.)

Bump the STYLE_GUIDE footer revision note.

**Acceptance:** content-level tab strip; deep links intact; colored
rail; sticky bottoms align (or rebalanced per pattern 13); no AI
sign-off automation; no internal milestone strings; `tsc` +
`eslint` clean; Python `pytest -k attorney` clean.

---

## Phase C — FSBO Overview

**File:** `src/pages/fsbo/FsboOverviewPage.tsx`
**Shell:** `src/pages/fsbo/_shell.tsx` (portal tabs live here — keep)
**Designs:** `VE-FSBODashboard.html` +
`completed_designs/ve-fsbo_dashboard.html`

A *portal*, not an internal dashboard. **No AI Coach banner.**
Upload uses the M5.1-scoped FSBO handlers — **never**
`intake.openNewTransaction()`.

1. **Keep the portal shell** (`_shell.tsx`) — dark sidebar, mandatory
   portal tabs (Overview / Properties / Documents / Support), FSBO
   brand descriptor.

2. **Inside the Overview tab:** drop the per-page greeting/chrome;
   adopt the § 15.1 inner shell; apply the sticky bottom-aligned
   grid + 440px rail. Verify pattern-13 parity — FSBO is the one
   role with the thinnest rail today; if the natural rail is short,
   add a "Recent updates" or similar 4th–5th card before falling
   back.

3. **KPI strip:**

   | KPI | Source | Tone |
   | --- | --- | --- |
   | My properties | `properties.length` | `orange` |
   | Days to close (nearest) | `days_to_close_nearest` | `red ≤7` · `amber ≤21` · else `green` |
   | Missing documents | `missing_documents_count` | `amber` if `>0`, else `neutral` |
   | New messages | `new_messages_count` | `blue` if `>0`, else `neutral` |

4. **Main column:**
   - **Hero — Critical next steps** (`tone='brand'`, icon
     `ShieldAlert`, `eyebrow='✦ Up next'`, `bodyTint='soft'`) —
     `critical_next_steps` in the action-queue pattern, explicit
     buttons (pattern 9).
   - **Properties** (`DashboardCard`, icon `Home`, `flush` if a card
     list).
   - **AI guidance** (`tone='brand'`, icon `Sparkles`) —
     `FsboContextualLearnCard` + `ai_guidance.next_decision` /
     glossary.
   - **Recent milestones** (`DashboardCard`, icon `CalendarCheck`,
     `FsboClosingTimeline`).

5. **Rail (compact, colored):**
   - Concierge / support — `blue` (or `green`), icon `MessageSquare`,
     `ConciergeStrip` with support contact info (collapsible per
     pattern 8 if it lists people).
   - Boundary notice — keep visible in its card.
   - Add a 4th–5th card if needed for pattern-13 parity (see #2).

6. Empty states throughout (pattern 12).

7. Audit copy against pattern 14 — concierge / support copy in
   particular tends to leak roadmap language.

**Acceptance:** portal tabs unchanged; overview opens with KPI row,
no greeting; `UploadIntakeCard` always has a real `onFilesSelected`;
boundary notice + support contact present; colored rail; sticky
bottoms align (or rebalanced per pattern 13); no internal milestone
strings.

> Properties / Documents / Support sub-pages are out of scope —
> they are list / document / contact surfaces, not dashboards.

---

## Phase E — Cleanup + style-guide bump

1. **Promote the sticky two-column grid into the shared kit.** The
   sticky-both-columns + `align-items: stretch` pattern is currently
   inline on Solo Agent, Team Leader, and Admin. Extract it into
   `MainRailGrid` behind a prop (`stickyAlign` + `railSize='xl'` for
   440px) so every dashboard shares one implementation. Phase E was
   sequenced last in rev 3 because "shared-grid extraction touches
   every dashboard at once" — that's still true; do it after Phase
   B and C have proven the inline pattern.

2. **Extract `PriorityQueueRow` shared component.** Pattern 16's row
   vocabulary is currently inlined in three places
   (`AdminActionQueue`, `ActionQueueList`, `InterventionQueueItem`).
   Extract a single
   `src/components/dashboard/shared/PriorityQueueRow.tsx` that takes
   the contract's inputs — `status_color` / severity, icon, pill
   label, optional secondary badges, title, description, primary
   action `{ to, label }` — and renders the `<article>` shell. Each
   call site becomes a thin wrapper that maps its payload into row
   props.

   Subtleties:
   - `AdminActionQueue` uses an `AdminActionSeverity` enum
     (`critical / high / medium / low`); `ActionQueueList` and
     `InterventionQueueItem` use `status_color` strings
     (`red / amber / green / blue / purple`). Normalize on
     `status_color` in the shared component; have Admin map its
     severity to a color in its wrapper (the severity *label* —
     "Critical" / "High" / "Review" / "FYI" — stays in Admin's
     wrapper too).
   - Secondary badges are role-specific: Team's closing-date badge,
     Admin's category badge, Agent's `subtitle`. Accept these as a
     `secondaryBadges?: ReactNode` slot rather than codifying them
     in the shared component.
   - The `bodyTint='soft'` parent `DashboardCard` background must
     keep enough contrast with the row's `bg-white` so the cards
     pop — verified during Phase A and Admin retrofit; revisit
     during Phase B if attorney matters use a different parent
     tint.

   Do this **after** Phase B and Phase C have proven their priority
   surfaces against the inline vocabulary (same rationale as item
   1: cross-cutting extractions land last).

3. **Audit & retire legacy shared kit** (`DashboardPage`,
   `DashboardHeader`, `KpiStrip`, `KpiCard`, `SectionCard`,
   `RailCard`): delete if no dashboard imports them; otherwise
   JSDoc-mark *"Legacy — non-dashboard surfaces only; dashboards use
   `DashboardCard` / `DashboardKpiCard` per STYLE_GUIDE § 16.2."*

4. **Remove `WidgetOrderManager`** from dashboard imports (confirm
   no one relies on per-dashboard layout persistence first).

5. **Tests:**
   - `AppLayout` role-matrix test still passes (shell CTA fix
     already in).
   - Remove per-dashboard assertions on greeting / Customize /
     chrome.
   - Add render tests asserting each dashboard's hero uses
     `DashboardCard tone='brand'` and that rail cards carry non-
     neutral tones.
   - Add a test for the lazy-fetch merge (priority/matter detail
     shows tasks when `transaction-cards` returns them).
   - Add a test for **pattern 14**: scan dashboard files for the
     literal strings `"Milestone 5"`, `"M5."`, or `/Milestone \d/`
     and fail if found.
   - Add render tests for **pattern 16**: each of the three priority
     surfaces (Admin Priority, Team Priority, Today Action Queue)
     renders the same `<article>`-shell vocabulary and exactly one
     primary `Button` per row (no "Upload here"-style secondaries
     regressing).

6. **STYLE_GUIDE § 16.2** — replace `AdminCard` names with the
   role-neutral `DashboardCard` / `DashboardStat` /
   `DashboardKpiCard`; document the extended tone palette and the
   sticky bottom-alignment rule (including the geometric envelope
   from pattern 6's rev-4 caveat). Land § 16.1.1 (from Phase B).
   Add § 16.1.2 codifying patterns 13–16. Bump to **rev 5** with
   a footer note referencing this work.

7. **Visual QA** — before/after screenshots of all five dashboards
   at desktop + tablet width; confirm bottoms align in both
   taller-main and taller-rail cases. Where columns are
   intentionally not parity-matched (rare), record the decision.
   Verify all three priority surfaces render rows identically
   (pattern 16).

---

## Phase F — Backend companion

Recorded as a real phase in rev 4 because rev 3's "no backend work"
proved wrong. Parts (a)–(e) shipped during Phase A / Admin; the
remaining items are follow-ups.

### Shipped

See *What's already landed → Phase F* above for the five items that
shipped: tenant-scope `fetch_team` + unattributed fold; implicit-
team fallback on `fetch_team` and `/users`; `view=team` sidebar
scoping for Admin + TeamLead; sub-component `embedded` variants;
drawer reposition.

### Open follow-ups

1. **`closings_next_14d.agent_id` attribution.** Currently uses
   `tx.get("created_by")` only — for transactions the team gets
   only via assignment, the labelled agent is the original creator
   (often an Admin), which is misleading. Use the most-active
   assignment when available, fall back to `created_by`.

2. **Multi-team isolation on `/dashboard/transaction-tab-counts`
   and `/dashboard/transaction-cards`.** Today `_user_filter`
   resolves `view=team + team_member_id=None` to `user_id=None`
   → no filter → all-tenant. That's fine for single-team
   workspaces (the common case) and matches what the dashboard now
   shows, but in a multi-team workspace it leaks. Apply the same
   implicit-team logic from `fetch_team` (creator IN team OR id IN
   team-assigned) to these endpoints so multi-team can be
   reintroduced without breaking the unconfigured-workspace flow.

3. **`team_financials.annual_pace`.** Hard-coded `0` in
   `fetch_team`. Compute from YTD closed deals + remaining-months
   projection so the "Annual pace" KPI on Team Leader stops being
   a placeholder.

4. **Inviter UX.** Long-term fix for the root cause behind several
   rev-4 frontend patches: when an Admin invites a user, the
   invitation flow should let the admin specify the target team
   (and the new user's `team_id` should be set on accept). When
   that ships, the implicit-team fallback becomes a defensive
   backstop rather than the primary path.

5. **`UserRepository.list_by_tenant` role filter.** When called by
   the dashboard's implicit-team fallback we role-filter in Python;
   pushing the role filter down to the SQL query would save a small
   amount of bandwidth for large tenants.

---

## Per-phase verification

- `npx tsc --noEmit -p tsconfig.app.json` — clean.
- `npx eslint <changed files>` — clean.
- `npx vitest run <dashboard tests>` — passes.
- `venv/Scripts/python.exe -m pytest app/tests/ -k "dashboard or
  team or users"` — passes (Phase F-affected surfaces).
- Manual, logged in as the matching role:
  - No sticky top chrome; page opens with the role's banner / KPI row.
  - Every block is a `DashboardCard` (or `compact`); hero is `brand`.
  - Rail cards are colored, not all-neutral; rail content wraps, no
    mid-word truncation.
  - Single page scroll, no per-column scrollbars; columns bottom-
    align at the same baseline (test with both more main content
    and more rail content; record pattern-13 deviations).
  - Expandable detail panels show real tasks / dates / contacts;
    contact rows collapsed-by-default, expand to real email / phone.
  - URL-driven tabs / panels deep-link correctly (Attorney, FSBO).
  - **Copy audit (pattern 14):** no string visible to end users
    references a milestone or version number.
  - **Identifier contrast (pattern 3 corollary):** avatars, role
    chips, status pills read clearly against the card background.

Cross-cutting (final): `npm run build` clean; all five dashboards
read as one family while each still foregrounds its role's own
content.

---

## Execution order

1. ~~Phase A — Team Leader~~ — **done**.
2. **Phase B — Attorney** (URL filter tabs + § 16.1.1 addendum +
   upload intake stays). ~1 day.
3. **Phase C — FSBO** (portal-tab awareness; FSBO-scoped upload).
   ~½ day.
4. ~~Phase D — Admin retrofit~~ — **done**.
5. **Phase E — Cleanup, shared-grid extraction, style-guide rev 4
   bump.** ~½–1 day.
6. **Phase F — Backend companion follow-ups** (closings agent_id,
   multi-team scoping, annual_pace, inviter UX). Run alongside
   Phase B / C as a thin parallel track. ~1 day spread across
   phases.

Total remaining: ~3 dev days, plus QA.

---

## Risks / open items

1. **Sub-component fit.** `AgentBoard`, `MatterCard*`,
   `PipelineHealthPanel`, `FsboClosingTimeline`, `TeamFastFilters`
   each rendered inside the old `SectionCard`. Verify padding and
   table edge-bleed (`flush`) inside `DashboardCard`. *(Resolved
   for `TeamFastFilters` and `PipelineHealthPanel` in Phase A via
   `embedded` variants; remaining components verified during
   Phase B / C.)*

2. **Filter-chip styling.** `TeamFastFilters` / `FastFilterStack`
   borders may compete with the card border — restyle to ghost
   chips on a tinted body. *(Resolved for `TeamFastFilters` in
   Phase A.)*

3. ~~**Team toggle.**~~ **Closed.** Toggle was prescribed,
   confirmed during build, then removed post-build per pattern 15.
   Recorded as the canonical example of *"confirm chrome before
   adding."*

4. **`useTransactionCards` cost.** The lazy-fetch enrichment adds
   one query per dashboard. Scope it (`state_filter`, `page_size`)
   and rely on React Query caching — do not refetch data already on
   the page (cost-effective-LLM/API rule).

5. **Admin regressions.** Admin is live; retrofit behind the same
   tests and screenshot-diff before/after. *(Phase D shipped with
   `AdminActionQueue` + `AdminDashboardPanels` tests passing.)*

6. **Shared-grid extraction (Phase E)** touches every dashboard at
   once — do it last, after all four role pages have proven the
   inline pattern.

7. **Pattern-13 column-height parity is data-dependent.** Card
   heights vary with content; on a sparsely-populated workspace a
   rail that's parity-matched on paper can still be short. Accept
   slight misalignment in extreme low-data cases rather than
   reintroducing a JS hybrid.

8. **Multi-team scoping (Phase F item 2).** The tenant-scope
   defaults applied to `fetch_team`, the Transactions page, and the
   sidebar endpoints are correct for single-team workspaces and
   leak across teams in multi-team workspaces. The implicit-team
   logic from `fetch_team` is the template to apply on the tx-cards
   side.

9. **Copy audit drift.** Pattern 14 is currently enforced by review
   and the Phase E test in #4. Until that test lands, new strings
   added to dashboard files may reintroduce milestone references —
   call this out during PR review.

---

*Plan revised: 2026-05-21 (rev 5). Supersedes rev 4.*

*Rev-5 changes vs rev 4:*
- *Pattern 16 (priority / action-queue row vocabulary) codified.
  The same `<article>` shell, severity rail, tinted icon tile,
  pill row, serif title, muted description, and single filled
  primary `Button` now span AdminActionQueue, ActionQueueList, and
  InterventionQueueItem.*
- *Phase A "InterventionQueueItem" record updated — single "Open
  deal" CTA replaces the earlier "Open file" + "Upload here" combo;
  inline upload flyout removed (consistency outranks per-row
  convenience). The closing-date badge is the only team-specific
  row content remaining.*
- *New "Priority queue row vocabulary" subsection in *What's
  already landed* records the cross-cutting standardization across
  the three priority surfaces.*
- *Phase E gains item 2 ("Extract `PriorityQueueRow` shared
  component"); existing items renumbered 3–7. Phase E test list
  gains a pattern-16 assertion. STYLE_GUIDE bump in Phase E item 6
  is now to rev 5.*

*Rev-4 changes vs rev 3 (still in force):*
- *Pattern 6 carries an explicit geometric envelope; pattern 13
  (structural parity), pattern 14 (no internal milestone copy), and
  pattern 15 (confirm chrome) added.*
- *Phase A and Phase D recorded as done with deviations.*
- *Phase F (Backend companion) added; rev 3's "no backend work"
  claim retracted.*
- *Risk 3 (Team toggle) closed; risks 7 (parity is data-dependent),
  8 (multi-team scoping), 9 (copy-audit drift) added.*

*Reference implementation: `SoloAgentDashboardPage.tsx` (structural
peers: `TeamLeaderDashboardPage.tsx`, `AdminDashboardPage.tsx`).
Reference for pattern 16: `AdminActionQueue` (the shell every
priority row now uses). Cross-reference: `STYLE_GUIDE.md` (§ 15,
§ 16); `project_ve_admin_dashboard_rebuilt.md`;
`MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md`.*
