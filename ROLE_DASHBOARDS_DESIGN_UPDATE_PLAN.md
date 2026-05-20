# Role Dashboards — Design Update Plan (rev 3)

## Context

The Solo Agent Dashboard (`/dashboard/agent`) has now been rebuilt and
hardened through several rounds of design review. That work — not the
original Admin rebuild — is the **reference implementation** for every
remaining role dashboard. It also overturned the core assumption of this
plan's rev 2, so the strategy below is rewritten accordingly.

### The correction that drove this revision

Rev 2 said: *"One vocabulary across every dashboard"* and *"all five
dashboards look like one family."* In practice, copying the Admin
Dashboard's **layout** onto Solo Agent was explicitly rejected:

> "Applying the exact same layout and elements as the Admin Dashboard to
> the Solo Agent Dashboard was a mistake. You must build a dashboard for
> each role that highlights the unique characteristics of that specific
> role. Review both Jake's initial design and my updated version, and
> rebuild the dashboard to incorporate all the features present in those
> designs."

So the principle is now split in two:

- **Shared visual *vocabulary*** — the `DashboardCard` / `DashboardStat`
  / `DashboardKpiCard` primitives, the tone palette, the § 15.1 shell,
  the sticky bottom-aligned two-column scroll. These stay identical
  across every dashboard so the product feels coherent.
- **Role-specific *layout and content*** — driven by each role's design
  HTML (Jake's initial **and** the updated `completed_designs/` version),
  not by cloning Admin. Each dashboard surfaces the metrics, queues, and
  panels that matter to *that* role, arranged the way *that* role's
  design shows them.

The Admin Dashboard is now **in scope** as well: the patterns the Solo
Agent build established (extended tone palette, sticky bottom-alignment,
card proportionality, colored rail cards, lazy-fetched detail panels) are
to be back-applied to Admin so it stays consistent with — not ahead of —
the family.

---

## Design sources (authoritative for role intent)

Per `MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md` § 1, the HTML mockups
are "authoritative for role intent, not pixel-perfect law." For each
role, **read both** the initial and the updated mockup and incorporate
**every feature** in them (minus explicit exclusions):

| Role | Jake's initial | Updated (preferred) |
| --- | --- | --- |
| Solo Agent | `VE-HomepageDashboard-SoloAgent.html` | `completed_designs/ve-homepage_dashboard-solo_agent.html` |
| Team Leader | `VE-HomepageDashboard_TeamLeader.html` | `completed_designs/ve-homepage_dashboard-team_leader.html` |
| Attorney | `VE-AttorneyDashboard.html` | `completed_designs/ve-attorney_dashboard.html` |
| FSBO | `VE-FSBODashboard.html` | `completed_designs/ve-fsbo_dashboard.html` |
| Admin | *(none — rebuilt directly)* | live `AdminDashboardPage.tsx` |

Where the two mockups disagree, the updated `completed_designs/` version
wins; where STYLE_GUIDE § 16 disagrees with both, the style guide wins on
chrome but the mockups win on *which role-specific blocks exist*.

---

## Established design system (the canonical reference)

Everything below is already implemented and verified on Solo Agent. Treat
it as the spec the other dashboards must match.

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

### 2. Shared primitives — now with an extended tone palette

`@/components/dashboard/shared/`:

- `DashboardCard` — the one card shell (icon tile → mono eyebrow → serif
  title → optional description; `action` / `trailing` header slots;
  `compact`, `flush`, `bodyTint='soft'` variants).
- `DashboardStat` — inner stat tile.
- `DashboardKpiCard` — KPI strip card.

**Tone palette (extended during the Solo Agent build):**
`neutral · brand · green · amber · blue · purple · red`. Both
`DashboardCard` and `DashboardKpiCard` accept these. The admin
`Admin*` files are thin re-export shims of these — Admin keeps working
unchanged, but new work imports from the shared kit.

### 3. Color is a design tool — no all-neutral stacks

> "The Filters, Recent Documents, and Quick Actions cards are all
> rendered in black, resulting in a visually unappealing and lackluster
> aesthetic. Please select appropriate colors to present them in a more
> artistic manner."

Every card carries an intentional tone. A rail of identical neutral
("black") icon tiles is a defect. Assign tones by *meaning*: green =
health/positive, amber = drift/warning, blue = filters/utility, purple =
documents/activity, red = critical, brand (orange) = AI / hero /
monetization. Solo Agent's rail is the reference:
Portfolio health → `green`, Portfolio intelligence → `brand`, Drift →
`amber`, Filters → `blue`, Recent documents → `purple`, Quick actions →
`brand`.

### 4. Card proportionality — chrome must fit content

> "Numerous cards' dimensions do not align with their content — many are
> disproportionately large or small. You simply mimicked the Admin
> Dashboard layout; this is incorrect. Position cards in the most
> appropriate locations with the most suitable proportions."

Rules derived from that feedback:

- **No duplicate blocks.** Solo Agent's "Production snapshot" duplicated
  the KPI strip's numbers and was deleted. Audit every dashboard for the
  same.
- **Narrow content → rail; substantial content → main.** Drift
  diagnostics (a few count rows) moved from the main column to the
  `compact` rail. Lists/queues/expandable cards stay in main.
- **Trim verbose descriptions.** Self-explanatory blocks (tile grids,
  deal cards) drop their `description` so the header doesn't dwarf the
  body.
- **Don't wrap thin content in oversized chrome.** Shrink ring/tile
  sizes in `compact` rail cards.

### 5. Rail width + content wrapping

> "The cards on the right are too narrow relative to their content …
> Recent Documents in particular is far too narrow."

Rail is **440px** at `lg+` (`lg:grid-cols-[minmax(0,1fr)_440px]`), up
from the old 320px. Rail content **wraps** (`line-clamp-2` / `-1`) rather
than truncating mid-word; pills move beside titles so the title gets full
width.

### 6. Two-column scroll with bottom-aligned baselines

> "When the dashboard is scrolled, the taller column scrolls first; only
> once it reaches the bottom should the shorter column begin to scroll.
> At the bottom, the final card on the left and the final card on the
> right align along the same horizontal line. No scrollbars on either
> side. Smart coding, not hard-coding."

CSS-only mechanism (no JS, no measured padding):

- Grid `align-items: stretch` → both cells share the row height (=
  the taller column's natural height).
- **Both** columns are `lg:sticky lg:top-0 lg:self-start`. Only the
  *shorter* column has empty room in its cell, so only it can sticky-
  shift — it "waits" pinned to the top while the taller column scrolls.
  When its sticky budget is spent, its bottom is flush with the cell
  bottom = the taller column's bottom.

Result: bottoms always meet at the same baseline, in *either* direction
(main taller or rail taller), with a single page scroll and no
per-column scrollbars.

### 7. Detail panels need lazy-fetched data, not the dashboard payload

> "The Show tasks/dates/contacts feature is not functioning — not a
> single task is displayed."

The role-dashboard payloads (`useAgentDashboard`, etc.) are intentionally
**minimal** — e.g. `priority_transactions` carries no tasks/dates/
contacts. Rich detail comes from `/dashboard/transaction-cards`
(`useTransactionCards`). The pattern: fetch the rich cards, build a
`transaction_id → card` map, and **merge** `inline_tasks` / `key_dates` /
`contacts` into each summary item before rendering its expandable body.
No backend change required.

### 8. Progressive disclosure for contact details

> "Under Key Contacts, only the labels 'Email' and 'Call' appear … show
> the actual email and phone." → then: "have them appear only when the
> small contact card is clicked to expand it."

Show **real** data (actual address / number as `mailto:` / `tel:`
links), but collapsed by default — name + role visible, a chevron hints
expandability, click reveals the contact lines. Rows with no info aren't
expandable.

### 9. Alert / action cards: explicit buttons, not whole-card clicks

Action-queue and alert rows must expose explicit, role-aware action
buttons (e.g. "Open deal →"), never a single whole-card click target.
(Consistent with the standing alert-card clickability rule.)

### 10. Role-specific monetization & banners

Solo Agent and Team Leader carry the **AI Coach upsell** (a paid add-on,
one teaser only — never activated UI). On Solo Agent it landed as a
**full-width, compact banner at the very top**, rendered as a two-column
hero (icon + eyebrow + serif title + pitch + CTAs on the left; "Today's
coaching move" callout + benefit bullets on the right) with enough height
to read as a hero, not a strip. The "Today's coaching move" copy is
**dynamic** (keys off `stale_comm`). Attorney/FSBO/Admin do **not** get
this banner.

### 11. Shell CTA placement (cross-cutting, already fixed)

The "+ New Transaction" CTA renders in **both** the sidebar footer **and**
the topbar for internal roles (Agent / TransactionCoordinator / TeamLead)
— matching the design HTML. Implemented via
`showSidebarFooterCta: true` on those roles in
`src/layouts/dashboardShellConfig.ts`, and
`showTopbarCta = primaryCta.action !== 'none' && shellVariant !== 'fsbo'`
in `src/layouts/AppLayout.tsx`. FSBO stays sidebar-only; Attorney's CTA
is "Upload Legal Packet"; Client/Vendor have no transaction-creation CTA.
(Note: "Solo Agent" is **not** a distinct role — it is an `Agent` with no
`team_id`. Any shell-config change to `Agent` affects both solo and
team-affiliated agents.)

### 12. Empty states everywhere

Every list/feed/chart that can render empty needs an explicit non-loading
empty state (`EmptyState`, `tone='brand'` for hero blocks), distinct from
the loading skeleton.

---

## Scope

**In scope (5 dashboards):**

1. ~~Solo Agent (`/dashboard/agent`)~~ — **done**, reference impl.
2. Team Leader (`/dashboard/team`)
3. Attorney (`/dashboard/attorney`)
4. FSBO Overview (`/fsbo`)
5. **Admin (`/dashboard/admin`)** — retrofit the new patterns.

**Out of scope:**

- Client portal (`/client/transactions`) and Vendor portal
  (`/portal/vendor`) — list / document portals, not dashboards.
- Backend / data-contract changes. All enrichment uses existing
  endpoints (`/dashboard/transaction-cards`, etc.).
- New LLM calls or aggregations (honors the cost-effective-LLM rule —
  reuse cached payloads, never re-call for data already on the page).
- AI Coach product activation — one locked teaser only.
- Shell-level concerns beyond the already-shipped CTA fix (sidebar nav,
  search scope, notification scope) — M5.1's territory.

---

## What's already landed

- **Phase 0 — primitives in the shared kit.** `DashboardCard` /
  `DashboardStat` / `DashboardKpiCard` live in
  `src/components/dashboard/shared/`; the admin `Admin*` files are
  re-export shims. Tone palette extended to
  `neutral · brand · green · amber · blue · purple · red`.
- **Phase 1 — Solo Agent**, fully rebuilt to all 12 patterns above.
- **Shell CTA fix** (pattern 11).

---

## Phase A — Team Leader Dashboard

**File:** `src/pages/dashboards/TeamLeaderDashboardPage.tsx`
**Designs:** `VE-HomepageDashboard_TeamLeader.html` +
`completed_designs/ve-homepage_dashboard-team_leader.html`

Closest sibling to Solo Agent — start from the Solo Agent file as the
structural template, then swap in team-scoped content.

1. **§ 15.1 shell**, single page scroll, sticky bottom-aligned two-column
   grid (pattern 6), 440px rail (pattern 5).

2. **Personal / Team view toggle** — content-level tab strip at the top
   of the scroll body (not chrome), § 16.1.1 bleed
   (`-mx-3 md:-mx-6 px-3 md:px-6 border-b-[1.5px] border-ve-border`).
   Confirm with the user the toggle stays before building. Drives
   `useTeamDashboard(view)`.

3. **AI Coach upsell banner** at the very top, same compact two-column
   hero as Solo Agent (pattern 10), "Today's coaching move" keyed off the
   team's stale-comm metric.

4. **KPI strip** — four `DashboardKpiCard`s:

   | KPI | Source | Tone |
   | --- | --- | --- |
   | Pending GCI | `team_financials.pending_gci` | `green` |
   | Pipeline volume | `team_financials.pending_volume` | `blue` |
   | Annual pace | `team_financials.annual_pace` | `orange` |
   | Pipeline health | `team_financials.pipeline_health` | `red` if `< 70`, else `green` |

5. **Main column (substantial content):**
   - **Hero — Intervention queue** (`DashboardCard tone='brand'`, icon
     `ShieldAlert`, `eyebrow='✦ Team priority'`, `bodyTint='soft'`).
     Reuse `ActionQueueList`; explicit per-row buttons (pattern 9).
     `SinceBadges` renders at the top of this block.
   - **Agent board** (`DashboardCard`, icon `Users`, `flush` body —
     `AgentBoard` paints to edges).
   - **Pipeline health** (`DashboardCard`, icon `Activity`,
     `PipelineHealthPanel`).

6. **Rail (compact, colored — pattern 3):**
   - Team health — `green`, icon `Activity`, `HealthScoreRing`.
   - Drift diagnostics — `amber`, icon `AlertCircle`.
   - Fast filters — `blue`, icon `Filter`, `TeamFastFilters` restyled to
     ghost chips on a tinted body if its borders compete.
   - Closings next 14d — `purple`, icon `CalendarRange`.
   - AI Coach (locked teaser) — `brand`, icon `Sparkles`, exactly once
     (per M5.1 § 4.2); click opens existing modal.

7. **Agent-board / per-row detail** — if rows expand to per-agent
   tasks/contacts, lazy-fetch via `useTransactionCards` and merge
   (pattern 7). Contact rows collapsible (pattern 8).

8. Empty states for the intervention queue, agent board, and every rail
   list (pattern 12).

**Acceptance:** no chrome; toggle is content-level; AI Coach teaser
appears once; colored rail; sticky bottoms align; `tsc` + `eslint` clean.

---

## Phase B — Attorney Dashboard

**File:** `src/pages/dashboards/AttorneyDashboardPage.tsx`
**Designs:** `VE-AttorneyDashboard.html` +
`completed_designs/ve-attorney_dashboard.html`

Adds URL-driven filter tabs. **No AI Coach banner.** Attorney's primary
CTA is "Upload Legal Packet" (shell), so the legal-packet intake card
stays on the page.

1. **§ 15.1 shell** + sticky bottom-aligned grid + 440px rail.

2. **Filter tab strip — content-level** (§ 16.1.1): first row of the
   scroll body, gutter bleed. Reads `filter` from the URL: `all`,
   `needs-review`, `missing-docs`, `ready-to-release`, `clean-files`.
   Counts from `data.filter_counts`. Ship the **§ 16.1.1 STYLE_GUIDE
   addendum** in this phase (text below).

3. **KPI strip:**

   | KPI | Source | Tone |
   | --- | --- | --- |
   | Legal health | `legal_health_score` (%) | `red <70` · `amber <90` · else `green` |
   | Pending review | `filter_counts.needs_review` | `amber` |
   | Missing docs | `filter_counts.missing_docs` | `red` if `>0`, else `neutral` |
   | Ready to release | `filter_counts.ready_to_release` | `green` |

4. **Main column:**
   - **Hero — Matters needing legal judgment** (`tone='brand'`, icon
     `Scale`, `eyebrow='✦ Counsel decides'`, `bodyTint='soft'`).
   - **Matter card stack** (`DashboardCard flush bodyTint='soft'`). Each
     matter row expands to `MatterSummaryRow` / `MatterDocChecklist` /
     `MatterTimeline` / `MatterActivity` / `AiLegalBrief` /
     `MatterPeoplePanel`. People panel uses collapsible contact rows
     with real email/phone (pattern 8).
   - **Legal-packet upload intake** (`tone='brand'`, icon `Upload`,
     `eyebrow='✦ Legal packets'`) — `UploadIntakeCard` with attorney
     copy. *(Attorney is the one role where upload stays on the
     dashboard — contrast Solo Agent, where upload was excluded.)*

5. **Rail (compact, colored):**
   - Critical approval gates — `red` (or `brand`), icon `AlertOctagon`.
   - State rules summary — `blue`, icon `ShieldCheck`; "Open state rules"
     → `StateRulesModal` via `?panel=state-rules`.

6. **Deep links preserved:** `?filter=needs-review` activates the tab and
   filters the stack; `?panel=state-rules` / `?panel=upload` open the
   modal / focus the upload card. **No AI control** checks sign-offs or
   releases packets.

7. Proportionality pass (pattern 4) — drop any block that duplicates a
   KPI; push narrow summaries to the rail.

**STYLE_GUIDE § 16.1.1 addendum (ship here):**

> **§ 16.1.1 Tab strips on dashboards.** A dashboard may render a
> URL-driven tab strip *at the top of its content*. Style it per § 15.2
> (bleeds to the gutter via `-mx-3 md:-mx-6`), but render it inside the
> scroll body, not a sticky header. No breadcrumb, no greeting, no
> page-title row above it. Attorney's `?filter=` tabs and Team Leader's
> personal/team toggle are the canonical examples.

Bump the STYLE_GUIDE footer revision note.

**Acceptance:** content-level tab strip; deep links intact; colored rail;
sticky bottoms align; no AI sign-off automation; `tsc` + `eslint` clean.

---

## Phase C — FSBO Overview

**File:** `src/pages/fsbo/FsboOverviewPage.tsx`
**Shell:** `src/pages/fsbo/_shell.tsx` (portal tabs live here — keep)
**Designs:** `VE-FSBODashboard.html` +
`completed_designs/ve-fsbo_dashboard.html`

A *portal*, not an internal dashboard. **No AI Coach banner.** Upload uses
the M5.1-scoped FSBO handlers — **never** `intake.openNewTransaction()`.

1. **Keep the portal shell** (`_shell.tsx`) — dark sidebar, mandatory
   portal tabs (Overview / Properties / Documents / Support), FSBO brand
   descriptor.

2. **Inside the Overview tab:** drop the per-page greeting/chrome; adopt
   the § 15.1 inner shell; apply the sticky bottom-aligned grid + 440px
   rail.

3. **KPI strip:**

   | KPI | Source | Tone |
   | --- | --- | --- |
   | My properties | `properties.length` | `orange` |
   | Days to close (nearest) | `days_to_close_nearest` | `red ≤7` · `amber ≤21` · else `green` |
   | Missing documents | `missing_documents_count` | `amber` if `>0`, else `neutral` |
   | New messages | `new_messages_count` | `blue` if `>0`, else `neutral` |

4. **Main column:**
   - **Hero — Critical next steps** (`tone='brand'`, icon `ShieldAlert`,
     `eyebrow='✦ Up next'`, `bodyTint='soft'`) — `critical_next_steps`
     in the action-queue pattern, explicit buttons (pattern 9).
   - **Properties** (`DashboardCard`, icon `Home`, `flush` if a card
     list).
   - **AI guidance** (`tone='brand'`, icon `Sparkles`) —
     `FsboContextualLearnCard` + `ai_guidance.next_decision` / glossary.
   - **Recent milestones** (`DashboardCard`, icon `CalendarCheck`,
     `FsboClosingTimeline`).

5. **Rail (compact, colored):**
   - Concierge / support — `blue` (or `green`), icon `MessageSquare`,
     `ConciergeStrip` with support contact info (collapsible per
     pattern 8 if it lists people).
   - Boundary notice — keep visible in its card.

6. Empty states throughout (pattern 12).

**Acceptance:** portal tabs unchanged; overview opens with KPI row, no
greeting; `UploadIntakeCard` always has a real `onFilesSelected`; boundary
notice + support contact present; colored rail; sticky bottoms align.

> Properties / Documents / Support sub-pages are out of scope — they are
> list / document / contact surfaces, not dashboards.

---

## Phase D — Admin Dashboard retrofit

**File:** `src/pages/dashboards/AdminDashboardPage.tsx`

Admin was the original template, but it predates patterns 3, 5, 6, and 8.
Bring it forward without changing *what* it shows.

1. **Colored rail (pattern 3).** Admin's rail cards (Health, Deals by
   stage, Recent activity, Integrations) currently lean neutral. Assign
   tones: Health → `green`, Deals by stage → `blue`, Recent activity →
   `purple`, Integrations → `neutral`/`brand`. The hero (action queue) and
   AI governance stay `brand`.

2. **Rail width (pattern 5).** Admin uses `railSize='lg'` (380px). Adopt
   the 440px rail for parity, and let any truncating rail content wrap.

3. **Sticky bottom-aligned scroll (pattern 6).** Admin currently uses the
   plain `MainRailGrid`. Move to the inline sticky-both-columns grid so
   its columns bottom-align like the others. (If `MainRailGrid` is
   promoted to support this mode, Admin can keep using it — see Cleanup.)

4. **Detail-panel data (pattern 7) + collapsible contacts (pattern 8)** —
   apply only where Admin rows expand to tasks/people; otherwise skip.

5. **Proportionality audit (pattern 4)** — confirm no Admin block
   duplicates a KPI; keep narrow summaries in the rail.

**Acceptance:** Admin visually matches the family (colored rail, 440px,
bottom-aligned), same data and routes as today; existing Admin tests
(`AdminActionQueue`, `AdminDashboardPanels`) still pass.

---

## Phase E — Cleanup + style-guide bump

1. **Promote the sticky two-column grid into the shared kit.** The
   sticky-both-columns + `align-items: stretch` pattern is currently
   inline in Solo Agent. Extract it into `MainRailGrid` behind a prop
   (e.g. `stickyAlign` + `railSize='xl'` for 440px) so every dashboard
   shares one implementation and Admin/Team/Attorney/FSBO opt in instead
   of copy-pasting.

2. **Audit & retire legacy shared kit** (`DashboardPage`,
   `DashboardHeader`, `KpiStrip`, `KpiCard`, `SectionCard`, `RailCard`):
   delete if no dashboard imports them; otherwise JSDoc-mark them
   *"Legacy — non-dashboard surfaces only; dashboards use `DashboardCard`
   / `DashboardKpiCard` per STYLE_GUIDE § 16.2."*

3. **Remove `WidgetOrderManager`** from dashboard imports (confirm no one
   relies on per-dashboard layout persistence first).

4. **Tests:**
   - `AppLayout` role-matrix test still passes (shell CTA fix already in).
   - Remove per-dashboard assertions on greeting / Customize / chrome.
   - Add render tests asserting each dashboard's hero uses
     `DashboardCard tone='brand'`, and that rail cards carry non-neutral
     tones.
   - Add a test for the lazy-fetch merge (priority/matter detail shows
     tasks when `transaction-cards` returns them).

5. **STYLE_GUIDE § 16.2** — replace `AdminCard` names with the
   role-neutral `DashboardCard` / `DashboardStat` / `DashboardKpiCard`;
   document the extended tone palette and the sticky bottom-alignment
   rule. Land § 16.1.1 (from Phase B). Bump to **rev 3** with a footer
   note referencing this work.

6. **Visual QA** — before/after screenshots of all five dashboards at
   desktop + tablet width; confirm bottoms align in both
   taller-main and taller-rail cases.

---

## Per-phase verification

- `npx tsc --noEmit -p tsconfig.app.json` — clean.
- `npx eslint <changed files>` — clean.
- `npx vitest run <dashboard tests>` — passes.
- Manual, logged in as the matching role:
  - No sticky top chrome; page opens with the role's banner/KPI row.
  - Every block is a `DashboardCard` (or `compact`); hero is `brand`.
  - Rail cards are colored, not all-neutral; rail content wraps, no
    mid-word truncation.
  - Single page scroll, no per-column scrollbars; columns bottom-align at
    the same baseline (test with both more main content and more rail
    content).
  - Expandable detail panels show real tasks/dates/contacts; contact rows
    collapsed-by-default, expand to real email/phone.
  - URL-driven tabs / panels deep-link correctly (Attorney, FSBO).

Cross-cutting (final): `npm run build` clean; all five dashboards read as
one family while each still foregrounds its role's own content.

---

## Execution order

1. **Phase A — Team Leader** (closest to Solo Agent; reuses the template).
   ~½–1 day.
2. **Phase B — Attorney** (URL filter tabs + § 16.1.1 addendum + upload
   intake stays). ~1 day.
3. **Phase C — FSBO** (portal-tab awareness; FSBO-scoped upload). ~½ day.
4. **Phase D — Admin retrofit** (colored rail, 440px, sticky bottoms).
   ~½ day.
5. **Phase E — Cleanup, shared-grid extraction, style-guide rev 3.**
   ~½–1 day.

Total: ~3–4 dev days, plus QA. No backend work.

---

## Risks / open items

1. **Sub-component fit.** `AgentBoard`, `MatterCard*`, `PipelineHealthPanel`,
   `FsboClosingTimeline`, `TeamFastFilters` each rendered inside the old
   `SectionCard`. Verify padding and table edge-bleed (`flush`) inside
   `DashboardCard`.
2. **Filter-chip styling.** `TeamFastFilters` / `FastFilterStack` borders
   may compete with the card border — restyle to ghost chips on a tinted
   body.
3. **Team toggle.** Confirm the personal/team toggle stays before moving
   it to a content tab.
4. **`useTransactionCards` cost.** The lazy-fetch enrichment adds one
   query per dashboard. Scope it (`state_filter`, `page_size`) and rely on
   React Query caching — do not refetch data already on the page (cost-
   effective-LLM/API rule).
5. **Admin regressions.** Admin is live; retrofit behind the same tests
   and screenshot-diff before/after.
6. **Shared-grid extraction (Phase E)** touches every dashboard at once —
   do it last, after all four role pages have proven the inline pattern.

---

*Plan revised: 2026-05-20 (rev 3). Supersedes rev 2's "one identical
layout" strategy. Reference implementation: `SoloAgentDashboardPage.tsx`.
Cross-reference: `STYLE_GUIDE.md` (§ 15, § 16);
`project_ve_admin_dashboard_rebuilt.md`;
`MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md`.*
