# Attorney Workspace — UI Redesign Plan

*Drafted 2026-05-22. Companion to the existing `ATTORNEY_WORKSPACE_PLAN.md`
(rev 3, May 2026), which is the **functional / structural / backend** plan.
This document is the **UI redesign** plan — visual vocabulary, layout, density,
and navigation patterns — informed by the FSBO workspace redesign and the
feedback gathered during it.*

---

## 0. Why this plan

The Attorney workspace was rebuilt in May 2026 to its current functional shape
(`ATTORNEY_WORKSPACE_PLAN.md` rev 3). That work fixed the *structure* — the
right pages exist, the right endpoints flow into them, sign-offs persist,
releases work. What it did **not** do is bring the *visual language* of those
pages up to the new bar set during the FSBO redesign.

The FSBO redesign produced a clear, lived-in set of rules for what a
"professional tool used by real estate experts" looks like in this codebase —
*and* a clear list of what it doesn't. The Attorney surfaces (especially the
Matter Workspace) still carry several of the patterns we flagged and removed
from FSBO:

- Dashboard chrome on working pages (`✦` eyebrows, serif card titles, tinted
  icon tiles, big serif KPI numerals).
- A mosaic of floating shadowed cards in a main + rail grid, scrolled as a
  single page canvas.
- Dense `divide-y` rows when standalone bordered cards would carry more
  information per glance.
- Detail pages laid out as scrolling reports rather than full-height app
  workspaces.

This plan applies the FSBO lessons systematically to every page in the
Attorney workspace, plus a short list of attorney-specific risks captured in
the May 2026 v1 review (sidebar/filter overlap, upload modal shape,
breadcrumb iconography).

---

## 1. Lessons from the FSBO redesign — the design vocabulary to apply

These are the rules the FSBO work crystallised, in the order they were
hammered out. Each is non-negotiable for Attorney.

### 1.1 Dashboards are exempt. Working pages are not.

The role dashboard (`/dashboard/attorney`) keeps the canonical
`DashboardCard` + `DashboardKpiCard` vocabulary. Every other surface — the
matters list, the matter workspace, releases, recording calendar, state
rules — is a **working page**. Working pages don't get dashboard chrome.

What that means concretely for working pages:

- **No `✦` mono eyebrow + serif card title + tinted icon tile** combo. That's
  celebratory chrome; it reads as a marketing/summary view.
- **No KPI tile strip at the top.** KPI tiles are for the role's dashboard
  (which already has them); a working page surfacing the same KPIs is
  redundant and visually mis-labels the page as a dashboard.
- **No "main column + right rail" grid of equal shadowed cards.** That layout
  *is* the dashboard skeleton.
- **No big serif numerals as decoration.** Numbers belong in tabular sans
  with status accents.

### 1.2 Working pages share the §15.2 tool-page header anatomy

Every list / detail / tool page uses the same header:

| Slot | Style |
|---|---|
| Breadcrumb (above title) | `text-[11.5px]`, group icon + group name → `›` → current page in `text-ve-text-muted font-medium`. |
| Title | `font-serif text-[16px] md:text-[20px] text-ve-text-primary`. |
| Inline badge | A pill next to the title (count / status). Use the orange-light pill for neutral counts, red for urgent (`12 missing`), green for "All clear". |
| Right-aligned actions | Bordered white buttons (`border-[1.5px] border-ve-border rounded-lg px-[13px] py-[6px]`). |
| Optional tab strip | Below the title row, full-bleed via `border-t-[1.5px] -mx-3 md:-mx-6 px-3 md:px-6`. Tabs use `border-b-[2.5px]` active orange + count badges (red badges for urgent buckets). |

Reference implementations: `TransactionListPage`, `DocumentsPage`,
`AiEmailReviewPage`. The FSBO shell `FsboPortalShell` (after the redesign)
implements this anatomy and is the cleanest reference.

### 1.3 Cards at "All Documents density"

The FSBO redesign aligned all working-page card vocabulary to the
`QueueRow` shape on All Documents:

- Standalone bordered cards (`rounded-xl border-[1.5px] border-ve-border`)
  with a **left status accent** (`border-l-[3px] border-l-{ve-color}`).
- `px-4 py-4` (or `py-[14px]`) — taller than `divide-y` rows.
- `shadow-card` and a hover lift (`hover:border-ve-orange
  hover:shadow-card-hover`).
- Multi-line content: title row (label + status pill) → meta line
  (entity tag · date · type) → chips row (severity-toned chips for the most
  actionable signals).
- Spaced between cards (`flex flex-col gap-2.5`), not joined as a
  `divide-y` list.

This is the visual that lets a card carry enough information to scan
without opening the underlying object.

### 1.4 Detail pages are full-height app workspaces

A detail page is **not** a long-scrolling canvas of stacked sections. It's an
app surface, viewport-bounded, with independent scroll regions:

```
┌ Sticky record header (breadcrumb + title + status + actions + facts chips)
├─────────────┬────────────────────────────────────────────────────────────
│             │
│ Section     │  Work pane — fills the remaining viewport, scrolls on its
│ rail        │  own. Renders one section at a time.
│ (left)      │
│             │
├─────────────┴────────────────────────────────────────────────────────────
└ Optional pinned footer (compliance / boundary notice / global action)
```

Reference: `AiEmailReviewPage` (the canonical master/detail in the codebase)
and `FsboPropertyDetailPage` (the FSBO Matter Workspace built during this
cycle).

The page header is sticky; the section rail is persistent on `lg`+ and
collapses to a horizontal section strip at the top of the work pane on
smaller widths.

### 1.5 Timeline visuals follow Jake's `.timeline` / `.stage` format

When a milestone / step timeline appears anywhere in the Attorney workspace,
it uses the same visual format the FSBO MilestoneTimeline now carries:

- Single continuous spine (`absolute left-[8px] top-[18px] bottom-[18px]
  w-[2px] bg-ve-border`).
- 18 px markers: done → green filled + white ✓; current → white border with
  orange ring halo + 8 px inner orange dot; upcoming → hollow gray.
- 3-column row: marker · body · date.
- Right-aligned mono date carrying a status word
  (`Done · Mar 8`, `Current · Due Mar 21`).
- No "Now" pill, no per-item highlight box — the marker halo + orange title +
  orange date are the only "current" affordances.

Source: `VE-FSBODashboard.html` (`.timeline` / `.stage`). The
`MilestoneTimeline` component already implements it.

### 1.6 Sidebar items vs filter tabs

Attorney-workspace v1 review rule (still hard): **filters belong on the
list page's filter-tab strip; the sidebar must not duplicate them.** The
fix landed in the rev 3 functional plan (sidebar items point at
`/transactions/active?tab=…` rather than at filtered dashboard variants),
but the visual contract — filter tabs use the All Documents tab strip; the
sidebar uses the workspace-level shell — needs to be enforced visually too,
not just route-wise.

### 1.7 Sidebar items lead to *pages*

Another v1 review rule: a sidebar entry must navigate to a page, not open a
modal. Modal launchers live inline on the page that needs them. This means
"Upload Legal Packet" must not be a sidebar entry; it's a topbar primary
CTA or an inline action on the matter workspace (the topbar branch already
exists per the functional plan).

### 1.8 Upload flows are modals, with the AI Wizard's step-by-step shape

A v1 review rule worth restating because it's the kind of rule that's easy
to drift away from: **upload-style flows are modals, not pages, and the
modal must use the AI Wizard's split-panel + vertical stepper shape.** A
single page form stacked inside a modal is rejected even if all the steps
are there — the shape has to be:

```
┌ branded left rail ──┬ right panel ──────────────────────────────────────
│ ① Choose matter    │ Step header
│ ● ② Packet type    │
│ ○ ③ Drop files     │ Scrollable body for the current step only
│ ○ ④ Review facts   │
│ ○ ⑤ Confirm        │ Sticky footer: progress bar + Back / Continue
└────────────────────┴──────────────────────────────────────────────────
```

The legal packet intake modal already exists (`UploadLegalPacketModal`); this
plan audits whether it follows that shape and rebuilds if it does not.

### 1.9 Breadcrumb icons match the destination group

Attorney pages use the **Scale** icon as the group crumb icon (not the
generic `Home`/`Briefcase` icon used in other workspaces). This is a v1
review rule and applies to every attorney working page in this plan.

### 1.10 Confirm structural forks before implementing

A pattern that emerged from FSBO: when the redesign of a page has a real
structural fork (e.g. tile grid vs. dense list rows; per-property mini
boards vs. tab-filtered flat list; KPI strip + card mosaic vs. matter
workspace), present the forks with concrete previews and let the reviewer
pick before writing the code. The plan below lists those forks under
**Open questions** in §6.

### 1.11 Eliminate feature duplication

The FSBO redesign repurposed Milestones & Messages → Messages-only once it
became clear the page was ~90 % duplicative of Property Detail's Timeline +
Messages sections. The Attorney workspace has at least one analogous
question: are the **Releases queue** and the matter workspace's
**Releases section** duplicating the same surface? Flagged in §6.

---

## 2. Scope

| # | Page / Surface | Route | File | Treatment |
|---|---|---|---|---|
| 1 | Attorney Dashboard | `/dashboard/attorney` | `pages/dashboards/AttorneyDashboardPage.tsx` | **Exempt** — keep dashboard vocabulary. Light audit (no working-page chrome leaked back in). |
| 2 | Attorney Matters list | `/transactions/active` | `pages/transactions/AttorneyWorkspacePage.tsx` *(to be renamed `AttorneyTransactionsListPage.tsx` per rev 3 §B.1)* | **Audit + density bump.** Confirm §15.2 anatomy; bring matter rows to All Documents density. |
| 3 | Attorney Matter Workspace | `/transactions/:id` | `pages/transactions/AttorneyMatterWorkspacePage.tsx` | **Major rebuild** — full-height matter workspace (section rail + work pane). |
| 4 | Releases Queue | `/attorney/releases` | `pages/legal/AttorneyReleasesPage.tsx` | **Restyle** to All Documents density + §15.2 filter-tab anatomy. |
| 5 | Recording Calendar | `/attorney/recording-calendar` | `pages/dashboards/AttorneyRecordingCalendarPage.tsx` | **Restyle** — calendar as a clean tool surface, no dashboard chrome. |
| 6 | State Rules | `/attorney/state-rules` | `pages/legal/AttorneyStateRulesPage.tsx` | **Restyle** — reference/lookup tool page; cards or a single divided panel. |
| 7 | Legal Packet Intake | (modal) | `components/attorney/UploadLegalPacketModal.tsx` | **Audit + possible rebuild** — must follow AI Wizard step-by-step shape (§1.8). |
| — | Legal page shell | n/a | `pages/legal/LegalPageLayout.tsx` | **Upgrade** to §15.2 anatomy if it isn't already. Parameterise breadcrumb icon (Scale). |

### Pages explicitly **out of scope** for this redesign

- Backend changes (the rev 3 functional plan covers those — un-mocking PATCH,
  adding `/attorney/matters`, etc.).
- Page tree / routing changes (those are also in rev 3).
- Page deletions or new pages (this is a restyle, not a re-IA).

If a UI redesign exposes a missing data field or a backend gap, it's filed
back to the functional plan rather than fixed here.

---

## 3. Design principles for the redesign

Distilled, the rules from §1 plus the attorney v1 review rules:

1. **Dashboards keep dashboard vocabulary. Working pages don't.**
2. **§15.2 header anatomy** on every working page (breadcrumb + serif title
   + inline badge + actions + optional filter-tab strip).
3. **All Documents card density** for every standalone card.
4. **Full-height matter workspace** for detail pages (no scrolling-card
   canvas).
5. **Connected-spine timeline** wherever a sequence of dated steps is shown.
6. **Filter tabs on list pages — never duplicated as sidebar entries.**
7. **Sidebar entries → pages.** Modals open inline from page bodies / the
   topbar.
8. **Upload modals follow the AI Wizard step-by-step shape.** Never a
   stacked single-page form inside a modal.
9. **Scale breadcrumb icon** on every attorney page.
10. **Confirm structural forks** with the reviewer (Jan) before writing
    code.
11. **Reuse, don't duplicate.** If two surfaces show the same thing, fold
    one into the other or differentiate it explicitly.
12. **No new LLM calls** for cosmetic UI (rev 3 functional rule still
    applies).

---

## 4. Per-page redesign approach

### 4.1 Attorney Dashboard (`/dashboard/attorney`) — exempt, light audit

No visual redesign. Audit only:

- Confirm no inline filter-tab strip remained from earlier iterations
  (rev 3 §3.1 removed it; verify it didn't creep back).
- Confirm no `UploadIntakeCard` block on the dashboard (rev 3 §3.2 removed
  it; verify).
- Verify hero "Matters needing legal judgment" rows still have explicit
  "Review matter" buttons (pattern 9 — per-row explicit button, not whole
  card click).
- Verify the "Recent matter activity" rail card uses per-row "Open matter"
  buttons or `aria-label`'d whole-row links (not a whole-card click
  target).

**Exit criteria:** the dashboard reads as an overview only, no filter
chrome, no functional surfaces, all card-click affordances explicit.

---

### 4.2 Attorney Matters list (`/transactions/active`)

The Attorney variant of the All Transactions list. The functional plan
already aligns its filters and routing to `?tab=…`. The UI work here is
narrower:

- **Header**: §15.2 (Scale breadcrumb · "Attorney Matters" serif title ·
  inline count pill · actions: Export / Print / "+ Upload Packet" topbar
  CTA · filter-tab strip with badges: All / Needs review / Missing docs /
  Ready to release / Clean files — red counts for "Needs review" and
  "Missing docs").
- **Cards**: Each matter renders at All Documents density — `rounded-xl
  border-[1.5px]` + severity left accent + `py-4` + multi-line meta. Where
  the existing implementation uses dense `divide-y` rows or
  `TransactionCard`-style cards, audit against the FSBO Properties row /
  All Documents `QueueRow` pattern and bring up to parity.
- **Per-card content**:
  - Title row: address + status pill (matter status) + optional flagged
    badge.
  - Meta line: client names · closing date · days remaining · attorney
    assignee.
  - Chips row: blocking docs (red), sign-offs needed (amber), ready to
    release (green), missing docs (red).
  - Inline actions: Review matter (primary), Open packet (secondary).
- **No KPI strip** at the top — KPIs live on the dashboard.
- **Page title**: not "Attorney Dashboard"; it's the matters *list*.
  Rev 3 §A.10 already calls this out.

**Reference visual**: `DocumentsPage` (`QueueRow`) + the redesigned FSBO
Properties list (`PropertyRow`).

---

### 4.3 Attorney Matter Workspace (`/transactions/:id`) — major rebuild

This is the largest piece of work. It mirrors the FSBO Property Detail
redesign: a **full-height app workspace** (sticky record header + section
rail + scrolling work pane), not a page of stacked cards.

#### 4.3.1 Sticky record header

A bespoke header (not the §15.2 shell — like FSBO Property Detail, this
page builds its own header inline so it can carry richer record context):

- **Breadcrumb**: Scale icon · "Matters" → `/transactions/active` · matter
  address (current crumb, `text-ve-text-muted font-medium`).
- **Title row**:
  - Serif address (`font-serif text-[16px] md:text-[20px]`).
  - Inline status pill — drives off `filter_key` (`needs_review`,
    `missing_docs`, `ready_to_release`, `clean_files`, `blocked`,
    `on_hold`). Each uses the FSBO_TONE_PILL pattern (red / amber / green
    / neutral / blue triads).
  - Right-aligned actions: **Back** (ghost), **Send packet** (primary,
    opens `SendPacketModal`), **Hold / Release hold** (secondary, opens an
    inline reason field per the existing implementation).
- **Sub-line**: client names · closing date · attorney assignee.
- **Facts chips row** — inline chips, not KPI tiles. One row of
  `FactChip`-style chips (severity-toned):
  - `⏱` Days to close — red if ≤ 7
  - `📄` Blocking docs — amber if > 0
  - `✓` Sign-offs needed — amber if > 0
  - `🔗` Packet status — `Ready` (green) / `Released N · ago` (neutral) /
    `Held` (red)
  - `⚖` Recording window — only if a recording is scheduled within 14 days

#### 4.3.2 Section rail (left, `lg:` only) + work pane

```
Workspace › Matters › 123 Oak St
123 Oak St, Austin       [Needs Review]   [Back] [Send packet] [Hold]
⏱ 12 days · 📄 2 blocking · ✓ 3 sign-offs needed · 🔗 Packet ready
─────────────────────────────────────────────────────────────────────
 ▸ Overview            │ Section content fills the viewport and
 ▸ Review            ⁵ │ scrolls on its own. Section rail stays put.
 ▸ Brief               │
 ▸ Timeline            │
 ▸ People              │
 ▸ Activity         •  │
 ▸ Releases            │
─────────────────────────────────────────────────────────────────────
 Compliance footer (boundary notice / required disclosures, if any)
```

Section rail items, each with optional badges:

| Section | Badge | Source data |
|---|---|---|
| Overview | — | (none) |
| Review | review_items needing sign-off | `detail.review_items` where `signed_off === false` |
| Brief | — | `detail.ai_legal_brief` |
| Timeline | upcoming deadlines within 14d | `detail.timeline` |
| People | — | `detail.contacts` |
| Activity | unseen items in last 24h (if available) | `detail.activity` |
| Releases | "Ready" or "Held" | derived from `detail.matter_state` + release rows |

On `lg-`, the rail collapses into a horizontal section strip at the top of
the work pane (FSBO Property Detail pattern).

#### 4.3.3 Section content

Each section is one focused work area on a white work surface. Reuse the
existing matter sub-components but render them *without* the dashboard
card chrome.

- **Overview**:
  - **Command strip** — a single severity-tinted strip at the top: one
    sentence stating the single most-urgent legal action + one primary CTA.
    Red on hard-stop, amber on same-day soft, green on "no attorney action
    required, next checkpoint <date>". Jake's design pattern; new component
    (`MatterCommandStrip`) since the FSBO equivalent does not exist.
  - **AI brief teaser** — first paragraph of the AI legal brief, with
    "Read full brief" link → `Brief` section.
  - **Upcoming deadlines** — next 3 timeline items as a compact list with
    Jake-style markers (green ✓ / orange dot / hollow).
  - **Missing documents nudge** — if blocking docs > 0, a clickable amber
    box linking to the Review section.
  - **Quick actions** — "Open packet", "Upload docs to this matter",
    "Open recording calendar". Inline buttons, not separate cards.

- **Review**: the file checklist with sign-off toggles. Re-render the
  existing `MatterDocChecklist` as All Documents-density rows — each row
  carries the doc label, the severity-accented left border (red for
  blocking, amber for sign-off needed, green for signed off), a meta line
  (doc type · last updated · uploaded by), and **explicit per-row
  buttons** ("View draft", "Sign off", "Hold") — never a whole-row click
  target (pattern 9 + attorney rule echoed from FSBO). The drop zone for
  per-matter uploads sits as a separate compact bordered panel below the
  list (the rev 3 plan's `MatterUploadDropZone`), not embedded inside the
  checklist component.

- **Brief**: the AI legal brief on a clean work surface. Subtle "AI" mono
  kicker (Sparkles + tracking, like the AI Email Review "AI Verified
  From" treatment). Brief text in a single column. No card mosaic.

- **Timeline**: `MilestoneTimeline`-shape component (Jake's `.timeline` /
  `.stage` format — §1.5). Use the existing FSBO `MilestoneTimeline` if
  the attorney's milestone data shape is compatible (same status taxonomy:
  done / active / upcoming). If the attorney's data is meaningfully
  different (e.g. each step has a "legal hold" sub-status), create a
  variant `LegalMatterTimeline` that shares the same visual.

- **People**: contacts as standalone cards in a 2-col grid (FSBO Property
  Detail People pane pattern). Per-card: avatar (party_role tone) · name ·
  role · company · email/phone buttons.

- **Activity**: ordered event list (audit-log rows). Standalone bordered
  rows with severity left accent (red on hold-applied, amber on
  sign-off-needed, green on signed-off / released), `py-3.5`, mono
  timestamp + actor avatar/initials.

- **Releases**: matter-scoped release history + the **Send packet** CTA
  (this duplicates the header CTA — keep both, since the section is a
  dedicated release view). Each past release renders as a card with
  recipients, document list, sent timestamp. **NB: the cross-matter
  Releases queue lives at `/attorney/releases` — see §6 Q3 for the
  duplication question.**

#### 4.3.4 Compliance / pinned footer

Optional. If there's a per-tenant compliance disclosure (analogous to the
FSBO boundary notice), pin it. If not, omit.

#### 4.3.5 Mobile

- Below `lg`: section rail collapses to a horizontal scrollable strip at
  the top of the work pane (matching FSBO Property Detail behavior).
- Facts chips wrap.
- Right-aligned header actions move below the title row.

#### 4.3.6 Loading / error / 404 / 403 states

- 404 / 403 — show a `StateFrame` (header + back to matters · "We couldn't
  find this matter" / "You don't have access to this matter").
- Error — show a banner with retry inside the work pane.
- Loading — section rail visible (so the user has navigation context),
  work pane shows a `Skeleton` block per the active section.

---

### 4.4 Releases Queue (`/attorney/releases`)

A list page — filter tabs ARE appropriate here.

- **Header**: §15.2 (Scale crumb · "Releases" serif title · inline count
  pill · filter-tab strip: All / Ready / Released).
- **Tabs**:
  - **All** — every matter in the attorney's portfolio with packet
    activity.
  - **Ready** — matters where all sign-offs are clear, no packet released
    yet. Red count badge if > 0.
  - **Released** — historical releases (newest first).
- **Cards** — All Documents density, one per matter:
  - **Ready** rows: green left accent + matter address + clients +
    closing date + "Sign-offs clear" chip + primary action **"Release
    packet"** (opens `SendPacketModal`) + secondary **"Open matter"**.
  - **Released** rows: neutral left accent + recipients chip + release
    timestamp + document count + secondary **"View packet"** /
    **"Resend"** (if endpoint exists).
- No KPI strip at the top.

**Reference visual**: All Documents `QueueRow` and the FSBO Documents page
post-redesign.

---

### 4.5 Recording Calendar (`/attorney/recording-calendar`)

A tool page. The calendar visual itself is the substance; everything around
it is a §15.2 wrapper.

- **Header**: §15.2 (Scale crumb · "Recording calendar" serif title ·
  inline pill showing the *active jurisdiction* (e.g. `TX`) · actions:
  state selector dropdown, "Print calendar").
- **Body**: a quiet bordered calendar grid (white surface, divider lines
  between days). Each day cell:
  - Day number in mono (top-left).
  - Recording window pills (compact, color-coded by the county / window
    type — neutral chips, not heavy KPI chrome).
  - Holiday / closed days dimmed.
- **No floating cards over the calendar.** The calendar is the whole work
  surface.
- **Mobile**: stack days in a list view (one card per day with windows
  inline), since a 7-col grid breaks below `md`.

**Backend caveat**: the recording calendar endpoint currently returns a
hard-coded "weekdays open / weekends closed" payload (rev 3 §7.1 gap). The
redesign honours the data it gets; if the placeholder data is too thin to
exercise the layout, mock realistic data in dev and surface a "Calendar
data not yet wired for this jurisdiction" message when the API returns the
placeholder.

---

### 4.6 State Rules (`/attorney/state-rules`)

A reference / lookup tool page.

- **Header**: §15.2 (Scale crumb · "State rules" serif title · state
  selector pill + filter chip group, e.g. *Closing · Recording ·
  Disclosure · Trust · Fees*).
- **Body**: rules rendered as a **single tool-page panel with internal
  sections divided by rules** (the FSBO Property Detail "the file" pattern
  — one bordered surface, sections split by `border-t`). Each section
  header is `text-[13px] font-semibold` + a small section icon. Content
  inside each section is a `<dl>` of label + value pairs (`font-mono` for
  values where appropriate), or a short paragraph for prose rules.
- **No card mosaic.** The page reads as one continuous rules document, not
  a dashboard.

**Backend caveat**: the state-rules endpoint currently returns a hardcoded
payload regardless of state (rev 3 §7.1 gap). Same handling as §4.5 —
visual is the deliverable here; data accuracy is filed back to the
functional plan.

---

### 4.7 Legal Packet Intake (`UploadLegalPacketModal`)

**Audit + possible rebuild.** The attorney v1 review rule (§1.8) is hard:
upload flows must use the **AI Wizard step-by-step shape**, not a stacked
single-page form inside a modal. The first work item is to read the
existing `UploadLegalPacketModal` and answer:

1. Does it use a split-panel layout (branded left rail with vertical
   stepper, right panel rendering one step at a time)?
2. Does each step have a sticky footer with a progress bar + Back /
   Continue?
3. Are the steps cleanly separated (no "all fields visible at once on a
   single page")?

If the answer to any is **no**, rebuild to match. The reference
implementation is the AI Wizard / `NewTransactionWizard` (the canonical
example called out in the attorney rules memory). Concretely:

- Steps for legal packet intake:
  1. **Choose matter** — searchable dropdown of the attorney's active
     matters. Required.
  2. **Packet type** — single-select chip group (Title commitment /
     Disclosure package / Settlement statement / Amendment / Recording
     packet / Other).
  3. **Drop files** — drag-drop zone, multi-file (PDF / DOCX / PNG / JPG).
  4. **Review extracted facts** — after AI parse completes, show the
     extracted facts (deadlines, parties, dollar amounts) for human
     verification before they become review items.
  5. **Confirm** — summary + primary CTA "Create review items & open
     matter".
- Reuses `UploadIntakeCard` for the drop zone primitive (rev 3 §5.3).
- AI parse runs in the background after the drop step; the "Review
  extracted facts" step waits on it (or shows a polling skeleton).
- Honesty rule (rev 3 §7.2 gap 9): never claim "indexed" until the
  parse job completes; show "queued for indexing" while it runs.

**Topbar entry**: the topbar primary CTA already points here per rev 3
§5.4 / §A.8. Verify it opens the modal on top of whatever route the
attorney is currently on (FSBO and other intake flows do this).

---

### 4.8 Shared shell — `LegalPageLayout`

The existing `pages/legal/LegalPageLayout.tsx` is the shared wrapper for
the legal pages (Releases, State Rules, possibly Recording Calendar). The
redesign:

- **Upgrade to §15.2 anatomy** if it isn't already there (breadcrumb +
  serif title + inline badge + actions + optional filter-tab strip).
- **Parameterise breadcrumb icon** to default to **Scale** (lucide
  `Scale`) for attorney pages. Other roles using `LegalPageLayout` can
  pass their own icon.
- **No subtitle line** by default — the title + inline badge carries the
  state (consistent with the reference pages and the post-redesign
  `FsboPortalShell`).
- **Tab support** identical to the FSBO shell (full-bleed `-mx-3 md:-mx-6
  border-t-[1.5px]`, `border-b-[2.5px]` active orange, count badges with
  redCount support).

If `LegalPageLayout` is already §15.2-compliant, the audit lands as a
no-op + a `Scale` default-icon change.

---

## 5. Shared components to build / reuse

| Component | Source | Purpose |
|---|---|---|
| `MilestoneTimeline` | existing `components/fsbo/MilestoneTimeline.tsx` | Reuse on Matter Workspace → Timeline if the FSBO milestone shape is compatible. If not, create `LegalMatterTimeline` with the same visual contract. |
| `MatterCommandStrip` | **new** | One-sentence + one-CTA strip at the top of Matter Workspace → Overview. Severity-toned (red / amber / green). Modelled on Jake's command strip. |
| `MatterUploadDropZone` | per rev 3 §4.3 | Per-matter compact drop zone below the Review checklist. Wraps `UploadIntakeCard`, pre-fills matter id. |
| `FactChip` | extract from `FsboPropertyDetailPage.tsx` | Already used for FSBO chips; promote to `components/shared/FactChip.tsx` so Matter Workspace can use it. |
| `LegalPageShell` (upgraded `LegalPageLayout`) | existing + upgrade | §15.2 anatomy + Scale crumb icon. |
| `AttorneyMatterRow` / `AttorneyReleaseRow` | **new** | All Documents-density row components for the matters list and releases queue. |
| `LegalPacketIntakeWizard` (rebuild of `UploadLegalPacketModal`) | existing + audit/rebuild | AI Wizard step-by-step shape per §1.8. |

---

## 6. Open questions / forks (confirm before implementing)

These are the genuine forks where I'll ask for direction before writing
code. Each is structural; guessing wrong is costly.

### Q1. Matter switcher placement

Jake's design has the matter switcher as a left-rail chip list. The
current implementation has a `MatterSwitcher` component (rev 3 §4.3) that
isn't currently wired in the dashboard but exists. With the new section
rail on the left, where should the switcher live?

- **A (recommended)**: Switcher as a **top-of-page dropdown** in the
  header row (next to the title), or as a short inline list on the
  Overview section. Keeps the section rail as the only persistent left
  rail (one nav surface — clean).
- **B**: A second left rail (matter switcher) + section rail = three-pane
  layout. Closest to Jake's design but adds complexity and squeezes the
  work pane.
- **C**: Switcher only inside the Matters list page; you navigate from
  the Matters list to a single matter at a time, no in-workspace
  switching.

### Q2. Section breakdown for the Matter Workspace

Proposed sections: Overview / Review / Brief / Timeline / People /
Activity / Releases. Confirm or rebalance:

- **A (recommended)**: Use the 7 sections as listed. Releases is its own
  section because it's a frequent destination and has its own action
  surface (Send packet, history).
- **B**: Fold Releases into Overview (with a single "Releases" group
  inside the Overview pane). Fewer sections; matches "Releases is just
  one of many things to do on a matter."
- **C**: Fold Activity into Overview (most attorneys probably won't
  switch tabs just to see activity).

### Q3. Releases — workspace section vs. dedicated page (duplication?)

The Matter Workspace has a "Releases" section (per-matter); the standalone
`/attorney/releases` page is the cross-matter queue. Is the cross-matter
page genuinely useful, or — as with FSBO Milestones — is it ~90 %
duplicative of the per-matter Releases section?

- **A (recommended)**: **Keep both.** The cross-matter queue's value is
  the "Ready" tab — the attorney's prioritised list of files clear to
  release across every matter they own. That's not derivable from a
  single matter's workspace. The per-matter section covers the *history*
  for one file.
- **B**: Drop the cross-matter page; rely on the matters list (filtered
  by `Ready to release`) for the queue.
- **C**: Drop the per-matter section; rely on the cross-matter page +
  the header **Send packet** CTA.

### Q4. State Rules — single panel vs. card grid

- **A (recommended)**: **Single divided panel** — rules render as one
  continuous reference document, sections split by `border-t`. This is
  the "professional tool" feel (Stripe docs / Clio state-rule reference).
- **B**: A grid of cards, one card per rule category. Closer to a
  dashboard layout but easier to scan if many rules.

### Q5. Recording Calendar — calendar grid vs. list

- **A (recommended)**: **Calendar grid** on `md+` (one cell per day,
  recording windows as inline chips) + **list view** on smaller widths.
- **B**: List only (one row per upcoming window). Simpler, easier to make
  accessible, but loses the at-a-glance "what's available this week" feel.

### Q6. Legal Packet Intake — is it already AI Wizard-shaped?

Before committing to a rebuild, **audit** the existing
`UploadLegalPacketModal`:

- If yes (split-panel + vertical stepper + one step at a time), the
  intake is in scope only for **light restyling** (token alignment with
  the redesign).
- If no, it's a **rebuild** to the AI Wizard shape. This is the largest
  single piece of work outside the Matter Workspace.

The audit is itself a small task; the answer determines whether intake
is **~½ day of restyling** or **~1.5 days of rebuild**.

### Q7. Reuse FSBO `MilestoneTimeline` directly, or create `LegalMatterTimeline`?

The FSBO milestone shape is `{ label, status: 'done'|'active'|'upcoming',
due_date, explanation }`. The attorney matter timeline shape is likely
similar (legal deadlines have the same status taxonomy). If shapes match,
**reuse the FSBO component directly**. If they diverge (e.g. legal
milestones carry a `signed_off` flag or a "hold" state), create
`LegalMatterTimeline` with the same visual contract (continuous spine,
18px markers, 3-col row, mono date) but its own status mapping.

---

## 7. Execution phasing & exit criteria

Each phase is committable as its own PR. Phases sequenced by impact +
risk: the Matter Workspace lands first (highest impact), then the
satellites, then the shared shell + audit pass.

### Phase A — Matter Workspace rebuild *(~2.5–3 days)*

Highest-impact, longest single piece of work. The rest of the workspace
gets a lot of visual lift just from this landing.

Work items:

1. Bespoke full-height layout (sticky record header + section rail + work
   pane). Mirror `FsboPropertyDetailPage` structure.
2. Sticky record header with breadcrumb (Scale icon), serif title +
   status pill, actions, facts chips row.
3. Section rail + responsive collapse to horizontal strip on `lg-`.
4. `MatterCommandStrip` component (new).
5. Section panes:
   - Overview (command strip + AI brief teaser + upcoming deadlines +
     missing-docs nudge + quick actions)
   - Review (file checklist at All Documents density + per-matter drop
     zone panel below)
   - Brief (AI legal brief on a clean work surface)
   - Timeline (reuse `MilestoneTimeline` or build `LegalMatterTimeline`
     per Q7)
   - People (contact cards, 2-col grid)
   - Activity (event row list)
   - Releases (per-matter history + Send packet CTA)
6. Loading / error / 404 / 403 states (StateFrame pattern).

**Exit criteria:**

- The page has no `DashboardCard`/`DashboardKpiCard` usage and no `✦`
  eyebrows or serif card titles.
- The body fills the viewport on `lg+`; the section rail and work pane
  scroll independently; no single page-level scroll of stacked cards.
- The work pane renders one focused section at a time and is on a clean
  white work surface.
- All explicit click affordances are buttons or `aria-label`'d links —
  no whole-card click targets except where the entire card is a single
  button (pattern 9).
- All data wiring intact (`useAttorneyMatterDetail`, sign-off mutation,
  send-packet, hold, mark-seen if applicable).
- Lint clean; tsc clean.

### Phase B — Matters list audit + density bump *(~0.5–0.75 day)*

1. Audit `AttorneyWorkspacePage.tsx` (or its post-rename file) for §15.2
   header anatomy.
2. Replace any dense `divide-y` matter rows / dashboard-style matter
   cards with the All Documents-density row component
   (`AttorneyMatterRow`).
3. Confirm filter tabs use the redesigned filter-tab strip style (red
   counts where appropriate).
4. Confirm the page title is **not** "Attorney Dashboard".

**Exit criteria:**

- Matter rows match the visual contract of `QueueRow` / FSBO `PropertyRow`.
- Filter-tab strip matches the All Documents / FSBO Properties pattern.
- No KPI tile strip on the page.

### Phase C — Releases Queue redesign *(~0.75 day)*

1. Rebuild `AttorneyReleasesPage.tsx` to the All Documents card density.
2. Filter-tab strip (All / Ready / Released).
3. `AttorneyReleaseRow` component for both ready + released variants.
4. Verify Send packet CTA wires `SendPacketModal` (rev 3 already wired).

**Exit criteria:**

- Each row is a standalone card with severity left accent + multi-line
  meta + explicit primary action.
- Red count badge on the Ready tab when > 0.

### Phase D — State Rules + Recording Calendar restyle *(~0.5–0.75 day)*

1. **State Rules** — rebuild to a single divided panel (per Q4 answer);
   §15.2 header with state pill + filter chips.
2. **Recording Calendar** — restyle as a quiet bordered calendar grid (per
   Q5 answer); §15.2 header with state selector + Print CTA.

**Exit criteria:**

- Neither page reads as a dashboard.
- Both share the upgraded `LegalPageLayout` shell.

### Phase E — Shared shell + Legal Packet Intake audit / rebuild *(~0.25 day audit, +1–1.5 days if rebuild)*

1. Upgrade `LegalPageLayout` to the §15.2 anatomy (if not already).
   Default breadcrumb icon to Scale.
2. **Audit `UploadLegalPacketModal`** against §1.8 (Q6).
3. **If non-compliant**: rebuild as `LegalPacketIntakeWizard` with
   split-panel + vertical stepper + sticky footer + step-by-step body
   per §4.7.
4. **If compliant**: light restyling only — token alignment.

**Exit criteria:**

- All attorney working pages use the upgraded `LegalPageLayout` (or
  bespoke layout in the case of the Matter Workspace) with Scale crumb
  icon.
- The intake modal opens from the topbar primary CTA and follows the AI
  Wizard step-by-step shape.

### Phase F — QA & audit pass *(~0.5 day)*

1. Pattern compliance check across every attorney working page:
   - Pattern 6 (sticky bottom-alignment for dashboards) — N/A for
     working pages but verify the Attorney Dashboard still complies.
   - Pattern 9 (explicit per-row buttons, not whole-card click).
   - Pattern 14 (no internal milestone references).
   - Pattern 16 (priority queue row vocabulary on file-checklist rows).
2. Attorney v1 review rules audit:
   - Sidebar items vs filter tabs (no duplication).
   - Sidebar items lead to pages, not modals.
   - Upload flow is a modal with the AI Wizard shape.
   - Breadcrumb icons match the group (Scale on every attorney working
     page).
3. Lint clean across all changed files.
4. tsc clean.
5. Manual run-through as an Attorney user, hitting each page.

**Total estimate**: ~4.5–6.5 dev days depending on Q6 outcome (intake
audit-only vs. rebuild) and Q7 (timeline reuse vs. variant).

---

## 8. Risks / known traps

1. **Re-introducing dashboard chrome on working pages.** The most
   recurring FSBO-redesign failure mode. Watch especially for
   `DashboardCard` / `DashboardKpiCard` / `MainRailGrid` / serif card
   titles / `✦` eyebrows / tinted icon tiles. **Working pages don't
   import from `@/components/dashboard/shared`.**
2. **Reintroducing a filter-tab strip on the dashboard.** Rev 3 removed
   it. Any new "Attorney Matters" filter UI lives on
   `/transactions/active`, not on `/dashboard/attorney`.
3. **Building the Matter Workspace as a scrolling page.** The May 2026
   v1 implementation was flagged as "looking like a dashboard" because
   it was. The Matter Workspace is a full-height app workspace; if
   `min-h-0 overflow-hidden bg-ve-bg` isn't on the outer container and
   each scroll region doesn't carry `min-h-0 overflow-y-auto`, the
   skeleton is wrong.
4. **Whole-card click targets.** Pattern 9 + the FSBO `feedback-alert-card-clickability`
   memory: every alert / row / card needs explicit per-row buttons,
   never a single whole-card click as the only affordance.
5. **Sidebar items duplicating filter tabs.** Attorney v1 review rule.
6. **A "page" whose only purpose is to open a modal.** Attorney v1
   review rule. State Rules used to be modal-only opened from a sidebar
   item; now it's a real page. Don't regress.
7. **A stacked single-page form inside a modal pretending to be a
   wizard.** Attorney v1 review rule. The intake modal audit (Q6) must
   catch this.
8. **Reusing `Home` / `Briefcase` as the attorney breadcrumb icon**
   instead of Scale. Attorney v1 review rule.
9. **No new LLM calls** for cosmetic UI. Rev 3 functional rule still
   applies; reuse cached AI-derived fields. The matter workspace
   especially should not trigger a fresh LLM call on every navigation.
10. **Duplication.** Watch the Matter Workspace → Releases section vs.
    the cross-matter Releases page (Q3). If both ship, the per-matter
    section must justify its existence with the per-matter *history*
    that the cross-matter queue doesn't carry.

---

## 9. Verification checklist (per phase)

- `npx eslint <changed files> --ext ts,tsx` — clean.
- `npx tsc -p tsconfig.app.json --noEmit` — clean.
- `npx vitest run <relevant tests>` — passes.
- Manual run-through as an Attorney user covering:
  - Dashboard reads as overview only (no filter strip, no upload card).
  - Topbar primary CTA opens the Legal Packet Intake modal in AI Wizard
    shape.
  - Matters list reads at All Documents density; filter tabs work.
  - Matter Workspace fills the viewport; section rail + work pane scroll
    independently; one focused section at a time.
  - Releases queue shows Ready + Released; row CTAs open the existing
    modals.
  - Recording Calendar renders the grid view on `md+` and the list view
    below.
  - State Rules renders as a single divided reference panel.
  - Every attorney page's breadcrumb uses the Scale icon.

---

## 10. Cross-references

- **Functional plan**: `ATTORNEY_WORKSPACE_PLAN.md` (rev 3, May 2026) —
  authoritative for routes, endpoints, backend, page tree.
- **Style guide**: `STYLE_GUIDE.md` §15 (page shells) + §16 (dashboards).
- **Design benchmarks**: `TransactionListPage`, `DocumentsPage`,
  `AiEmailReviewPage`, `FsboPortalShell`, `FsboPropertyDetailPage`
  (post-FSBO-redesign).
- **Timeline source of truth**: `VE-FSBODashboard.html` `.timeline` /
  `.stage` spec, implemented in
  `velvet-elves-frontend/src/components/fsbo/MilestoneTimeline.tsx`.
- **Attorney design refs**: `VE-AttorneyDashboard.html` (Jake's initial
  design — read as a per-matter workspace draft, not a dashboard) and
  `completed_designs/ve-attorney_dashboard.html` (updated version).
- **Hard-rules memory** (operator-side, not in this repo): the FSBO
  redesign feedback rules — dashboard-vs-tool aesthetic, design
  benchmarks, root-cause over patches, alert-card clickability — and the
  attorney v1 review rules (sidebar vs filter, sidebar vs modal, upload
  modal shape, breadcrumb icons).

---

## 11. What this plan does **not** decide

- The answers to **Q1–Q7** in §6. Those are forks for the reviewer (Jan)
  to pick. Phase A cannot start before Q1, Q2, and Q7 are answered;
  Phase E (intake) cannot start before Q6's audit result is in.
- Any backend change (filed back to the rev 3 functional plan).
- Any page tree change (filed back to rev 3).

Once §6 is resolved, this plan is concrete enough to start work at
**Phase A**.

---

*Plan drafted 2026-05-22. Awaiting decisions on §6 before Phase A begins.*
