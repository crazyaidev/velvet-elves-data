# Transaction Page Redesign Superiority Plan

> The Transaction Workspace: one page per deal where everything the AI wizard
> creates stays visible, editable, and evidenced for the life of the
> transaction. This plan covers the complete UI redesign of the transaction
> surface plus the small data-layer work without which the redesign would be
> cosmetic.
>
> Status: PLAN ONLY. No source code has been changed. Drafted 2026-06-12.
> Companion to AI_WIZARD_SUPERIORITY_COMPLETION_PLAN.md (Parts I + II,
> implemented and awaiting commit) and successor to
> TRANSACTIONS_PAGE_COMPLETION_PLAN.md (implemented; its contracts are
> preserved, not replaced, until the phases below say otherwise).

---

## 0. Grounding

### 0.1 What was reviewed before drafting

Documentation (velvet-elves-data):

| Document | What this plan takes from it |
| --- | --- |
| requirements.txt + notes-active_transactions_page.txt | The product owner's own asks for this surface: print closing checklist from profile templates, AI chat that filters/sorts/suggests, drag-a-document-anywhere upload, deadline notifications, sidebar deal states (Active is a placeholder for v2 Listings) |
| SYSTEM_DESIGN.md | Role model, tenant scoping, `team_member_id` conventions, audit-log expectations |
| TRANSACTIONS_PAGE_COMPLETION_PLAN.md | The current page's full contract: routes and aliases, URL state (`?expand`, `?task`, `?highlight`), client feedback triage rows 17-25, export/print/checklist contracts, the completion bar ("no visible control is cosmetic") |
| AI_WIZARD_SUPERIORITY_COMPLETION_PLAN.md | Parts I + II architecture: rules not dates, preview == commit, verifier gates, confidence tiers, Autopilot, command bar intents, v2 comfort scale, decisions D1-D16 |
| LISTEDKIT_COMPETITIVE_ANALYSIS_AND_FEATURE_IMPROVEMENT_PLAN.md | Where ListedKit is strong (urgency surfacing, integrated action channels) and where we beat them (deterministic engine, portals, human-in-the-loop) |
| STYLE_GUIDE.md including the v2 Comfort Scale | Type, contrast, spacing, motion, AI-surface elements; v2 ships wizard-first pending D13 and this page is the natural second surface |
| TRANSACTION_CARD_TYPOGRAPHY_AUDIT.md | Jake's exacting card type scale; the card face is his territory |
| WIZARD_TESTING_GUIDE.md | The mouse-only testing format this plan's testing guide will extend |
| VE-ActiveTransactions.html | Jake's canonical comp for the portfolio page and the milestone bar; this plan does NOT redraw that comp |
| jake_email_response_10.txt | TC-becomes-a-vendor direction (post-MVP); the People tab must not hard-code assumptions that block it |

Source code (both repos), with the load-bearing findings:

| Finding | Where |
| --- | --- |
| `/transactions/:transactionId` already routes, but non-attorney roles get NotFound: "until a generic transaction detail layout exists" | frontend `src/App.tsx`, `TransactionDetailRouter` |
| The de facto detail surface is a 1,163-line expandable card plus 16 modal/panel components | `src/components/shared/TransactionCard.tsx`, `src/components/active-transactions/*` (DocumentsModal, AddTaskModal, AddContactModal, HistoryPanel, AIChatPanel, CommunicationsPanel, AssignTeamModal, ManageClientAccessModal, ComposeEmailModal, ClientThreadDrawer, DateEditPopover, MissingDocumentsPanel, NewTransactionModal, PostClosingFeedbackModal, ...) |
| The milestone bar renders a fixed 7-stage sequence and silently drops every dot whose label does not keyword-match a canonical stage; wizard deadline dots (label "Deadline") are all dropped | `src/components/shared/MilestoneTimeline.tsx:53-64` |
| The cards endpoint serializes tasks as name + due date + status only; the persisted rule (`metadata.basis`) never reaches any client | backend `app/api/v1/dashboard.py` `_build_task_sections`, `TaskSectionTask` |
| Wizard deadline tasks persist `metadata.kind = 'deadline'`, `metadata.basis = {days, direction, anchor}`, `metadata.auto_draft_email`, `metadata.related_requirement_id` and nothing reads any of it back | `app/services/task_generation_service.py:422-448` |
| Requirement rows persist their due RULE (`due_days`, `due_direction`, `due_anchor`) but have no columns for citation evidence | `supabase/migrations/20260817090000_document_requirements.sql` |
| AI citations, confidence, the deal brief, and watch-outs are discarded at Approve & Create; they exist only in wizard state | `src/components/wizard/NewTransactionWizard.tsx` (submit path), `WizardDealBrief.tsx` |
| Key Dates is a fixed list of 7 operational fields; 5 cannot be known at intake | `app/api/v1/dashboard.py:3088` `_build_key_dates` |
| Post-create date edits do not cascade; `PUT /transactions/{id}/key-dates` and `PATCH /transactions/{id}` write fields only | `app/api/v1/transactions.py` |
| The deterministic planner that resolves rules to dates already exists and is payload-driven | `app/services/timeline_planner.py`, `app/services/requirement_planner.py`, `POST /transactions/preview-tasks` |
| A deal-scoped, stateless AI chat endpoint already exists | `POST /api/v1/dashboard/ai-chat`, `src/components/active-transactions/AIChatPanel.tsx` |
| Closed-intent command classification already exists and is context-free | `POST /api/v1/ai/wizard-command`, `app/services/ai_service.py` `parse_wizard_command` |
| Calendar push per transaction exists | `POST /api/v1/calendar/push/transaction/{id}`, `SyncDeadlinesButton` |
| Task APIs cover everything but metadata editing needs verification | `app/api/v1/tasks.py`: GET by transaction, PATCH, PUT status, POST similar |
| History and communications surfaces exist as panels | `useTransactionHistory`, `CommunicationsPanel` |
| The Closing Calendar deep-links to the card-expand URL state | `src/pages/CalendarPage.tsx` header comment |

### 0.2 Lessons applied from previous plan reviews

Every prior plan review (C1-C17, P1-P10) found the same failure classes. This
plan obeys these rules from the start; reviewers should hold it to them:

1. **The server is the only place date arithmetic happens.** No client-side
   deadline math anywhere in the redesign. The cascade reuses the planner.
2. **Preview equals commit.** Any diff shown to the user is produced by the
   same code path that will apply it.
3. **No ghost endpoints.** Section 8 lists every endpoint this plan calls,
   split into "exists today (verified, path cited)" and "new (specified
   here)". If a UI element in section 5 has no row in section 8, that is a
   plan bug.
4. **Idempotent mutations.** The cascade apply carries a client `commit_id`
   exactly like the requirements bulk endpoint; replays are safe.
5. **AI never applies anything by itself.** Same Part II doctrine: classify
   or propose, preview, one human click, undoable.
6. **Role checks include TransactionCoordinator** on every mutation (the
   2026-04-24 policy: TC = Agent rights on this surface), and nothing lets
   Admin or TeamLead cross tenants.
7. **Honest surfaces.** No demo data, no fabricated sparklines, no invented
   dates. Empty states say what is missing and what action creates it.
8. **URL-shareable state** for every view the tester can reach.
9. **Tests stub every endpoint a component calls** (msw passthrough
   destabilizes suites; learned twice).
10. **Migrations are listed in one place** (section 8.4) for Jan to apply,
    and the plan states what degrades gracefully when they are not applied.

### 0.3 Review corrections (2026-06-12 second pass, W1-W12)

A full workflow-and-logic review against the source found the following
errors in the first draft. Each is corrected in place in the sections
below; this log records what was wrong so reviewers can verify the fix.

- **W1 (critical, cascade logic).** The cascade only moved tasks carrying
  `metadata.basis` and would have listed every template-generated task as
  "not moved (manually set)". That is wrong twice: template tasks are the
  MAJORITY of a deal's dated tasks, and they are rule-generated, not
  manually set - their rules live in the template library, and the created
  rows persist `template_id` + `source="template"`
  (`task_generation_service.py:359-377`). Corrected in 7.2: preview/apply
  re-plans the template set under the OLD anchors and the NEW anchors
  (`plan_tasks_for_transaction` is pure and reusable); a task whose current
  due date equals its old-plan date is rule-bound and moves to its new-plan
  date; one that differs was pinned by a human (review-step override or
  later edit - storage cannot distinguish these, and the comparison makes
  the distinction unnecessary) and is listed under "not moved (pinned)".
- **W2 (critical, self-contradiction).** Section 5.1 sourced the header's
  `client_names`, stage pill, and AI next step from the cards endpoint
  while section 13 (correctly) forbids the workspace from calling the cards
  endpoint. Corrected: the plan aggregate (7.1) gains a `header` block
  (display title, client names, stage pill, days to close, the cached
  `ai_next_step_*` columns that live on the transaction row with the same
  rule-based fallback the cards endpoint uses, and the KPI counts/series).
- **W3 (high, dead-end workflow).** The empty-state button "Generate the
  standard checklist" had no callable path: the D7 hook runs inside
  `POST /transactions/{id}/tasks/generate`, which 409s when tasks already
  exist (`transactions.py:1216-1220`) - and every legacy deal has tasks.
  Corrected: new endpoint `POST /transactions/{id}/document-requirements/defaults`
  wrapping the existing service `instantiate_default_requirements_if_absent`
  (`requirement_planner.py:243`); idempotent by definition of the service.
  Added to 8.2 (Phase A).
- **W4 (factual claim).** 5.1 justified direct edits on the five tracking
  fields with "the planner anchors on acceptance/closing only". False:
  `CANONICAL_ANCHORS` (`intake_intelligence.py:39-47`) also contains
  `possession_date` plus four DERIVED anchors (`inspection_deadline`,
  `inspection_response_deadline`, `hoa_docs_deadline`,
  `insurance_deadline`). The conclusion survives in corrected form: no
  anchor references any of the five tracking COLUMNS, so their direct edit
  stays cascade-free; `possession_date` IS an anchor and was already
  routed through the cascade. New consequence recorded in 7.2: the cascade
  must resolve CHAINED anchors (a basis on `inspection_deadline` moves
  when acceptance moves) by resolving bases through the planner, exactly
  as `resolve_added_task_basis` already does.
- **W5 (ghost flow).** The header quick action "Share" had no existing
  per-deal flow for internal roles: share links are FSBO-scoped
  (`milestones.py`: `/dashboard/fsbo/share-link`) and client visibility is
  the Manage Client Access flow, which already lives in the People tab.
  Corrected: Share removed from the quick actions; nothing is lost.
- **W6 (work overstated; now cited as existing).** Compliance "full
  editing parity" needs NO new backend: `PATCH /{requirement_id}` already
  accepts name, description, status, and due rule with server-side
  re-resolution (`document_requirements.py:260+`), and post-create ADD is
  `POST /bulk` with a fresh `commit_id` and one item - bulk APPENDS;
  idempotency is a per-commit lookup (`document_requirements.py:149-157`),
  verified. The remaining work is frontend-only: the
  `PatchRequirementInput` hook type currently exposes only
  status/matched/unmatch (`useDocumentRequirements.ts:50-58`) and must be
  extended to the fields the backend already accepts. 5.5 and 8.x updated.
- **W7 (workflow gap, calendars).** After a cascade apply, events
  previously pushed to a connected external calendar are stale. Corrected
  in 7.2: the apply response includes `calendar_resync_recommended: true`
  when the user has calendar connections, and the UI follows the Apply
  confirmation with a one-click "Re-sync deadlines" chip (the existing
  push endpoint). Also clarified for honesty: the IN-APP Closing Calendar
  reads live transaction fields, so it agrees automatically - but it shows
  core/tracking events only (`EventKind` list in `CalendarPage.tsx`);
  deadline TASKS are not on the in-app calendar today, and adding a
  deadlines lane there is out of scope for this plan (noted under T6).
- **W8 (consistency).** 5.4's command-bar executor said "toggle_auto_email
  -> task metadata PATCH", contradicting 7.4 (no generic metadata writes
  exist or will exist). Corrected: it routes through the new explicit
  `auto_draft_email` patch field.
- **W9 (clarity).** 8.1 implied the client calls `PATCH /transactions/{id}`
  for term edits. In Phase B+ the client never patches derived-from terms
  directly; `/plan/apply` writes fields server-side. Row reworded.
- **W10 (undo precision).** Undo of a cascade is a fresh `/plan/apply`
  with the inverse field changes and a NEW `commit_id`; planner determinism
  restores rule-bound rows, and the W1 pinned-detection comparison protects
  any manual edits made between Apply and Undo (they read as pinned and are
  listed, not clobbered).
- **W11 (already corrected in the first revision).** `TaskUpdateRequest`
  has no metadata field (`task.py:38-53`); explicit `auto_draft_email` /
  `basis` patch fields are specified in 7.4.
- **W12 (KPI data source).** The KPI strip needed counts before any lazy
  tab query runs. Corrected: counts (open tasks, overdue, missing docs)
  and the two honest sparkline series (weekly task completions, weekly
  document uploads, 8 buckets) are computed server-side into the plan
  aggregate's `header` block.

---

## 1. Why a redesign, stated precisely

The AI wizard (Parts I + II) now produces a rich, evidenced plan: a timeline
of rules, a compliance checklist, linked tasks, a deal brief with cited
watch-outs. At Approve & Create that plan is compiled into normalized records
and the presentation of it is discarded. The post-create surfaces were
designed years (in product time) before the wizard and cannot show what it
made:

- **The container problem.** There is no transaction detail page for the
  roles that do the work. The route exists and 404s. The card drawer plus 16
  stacked modals is the detail surface, and a 3-column drawer cannot host a
  plan view, an evidence trail, a compliance editor, and a cascade diff.
- **The mental-model break.** The wizard teaches "dates are rules; move the
  anchor and everything moves." Post-create, editing a date edits one field.
  Rules persist in the database and silently stop governing anything.
- **The vocabulary problem.** "Timeline" (wizard), "Key Dates" (card),
  "Deadlines" (calendar) are three names over two different concepts, and
  empty operational fields ("Inspection Response: Not yet") sit next to a
  wizard that just confirmed an inspection deadline, reading as data loss.
- **The evidence problem.** Citations and confidence die at create. The AI's
  work becomes indistinguishable from manual entry exactly when it starts to
  matter.
- **The confirm-blind problem.** Autopilot creates thirty artifacts in three
  clicks and the user can never again see what was approved in the shape
  they approved it.

ListedKit's answer is re-enterable intake steps. Ours is better if we do it
right: a workspace that renders the LIVE records (not a stale intake
snapshot) in the wizard's visual language, with the evidence attached and
the rules still in force. That is the superiority claim of this plan:
ListedKit re-shows what was extracted; we show what is currently true, why
it is true, and what happens if you change it.

---

## 2. Goal, completion bar, non-goals

### 2.1 Goal

One URL per deal: `/transactions/:transactionId` renders the **Transaction
Workspace** for Agent, TransactionCoordinator, TeamLead, Admin (Attorney
keeps the existing Matter Workspace on the same route). Everything the
wizard creates is visible there for the life of the deal; everything
editable in the wizard is editable there with identical editors; every AI
artifact keeps its evidence; every date edit offers the same cascade the
wizard taught. The portfolio page (`/transactions`) remains Jake's card
grid and becomes the index that links in.

### 2.2 Completion bar

- A tester can answer, with mouse clicks only, for any deal: "what is the
  plan, why does each deadline exist, what changed since I approved it,
  what does the AI think I should do next, and what happens if the closing
  moves" - without opening the wizard, a modal stack, or the calendar.
- Editing the anchor or closing date offers a full old-to-new diff and one
  Apply; after Apply, tasks, requirement due dates, and the calendar agree.
- Every AI-created row shows its chip, confidence, and a working citation
  (for transactions created after evidence persistence ships; older deals
  show an honest "created before evidence retention" note instead of fake
  data).
- No information that the wizard displayed is unreachable post-create.
- Every control mutates real data, invalidates the right queries, and
  writes an audit entry when it changes workflow state (same bar as the
  previous completion plan).
- The page is fully usable by a non-developer real-estate tester: mouse
  first, typing only to name things, nothing below 12px, WCAG AA.

### 2.3 Non-goals

- No redesign of Jake's portfolio card face or milestone bar in Phases A-C.
  Changes there are Phase D and gated on his comp approval (T2, T3).
- No new AI engine, no new LLM call types. The workspace reuses the
  existing chat, command classification, and (read-only) persisted
  proposals. LLM cost per page view: zero.
- No changes to the Attorney Matter Workspace, Client portal, or FSBO
  workspace beyond leaving their routes untouched.
- No blocking dependency on the TC-as-vendor model; the People tab is
  designed so that party sources can later include vendor-org links
  (jake_email_response_10) without layout changes.
- The "drag a document anywhere on the screen" requirement is scoped to a
  workspace-wide drop target in this plan; an app-global drop zone is a
  separate decision (T8).

---

## 3. Experience principles (the convenience doctrine)

These extend STYLE_GUIDE v2.6 and bind every screen in section 5:

1. **Mouse-only completeness.** Every flow finishes without typing except
   naming things. Date changes are pickers and steppers; choices are chips
   and dropdowns; confirmation is one button.
2. **The system proposes, the user confirms.** Defaults everywhere a
   default is computable. The cascade diff arrives pre-computed; the user
   approves rather than reconstructs.
3. **Confirm once, undo inline.** One Apply per intent. Destructive actions
   produce the Undo chip, never a vanished row.
4. **Evidence on demand, never in the way.** AI chips are quiet; one click
   expands citation + confidence + "view in document". The brand promise
   "the AI shows its work" now has a permanent home.
5. **One name per concept.** "Timeline" is the plan (rules + dates).
   "Key Dates" is renamed in copy to "Tracking Dates" (recommendation,
   decision T4) because that is what it is: operational milestones recorded
   as they happen. The calendar keeps "Deadlines" only as a lane label.
6. **Honest emptiness.** A deal created before the checklist feature shows
   "No compliance checklist exists for this deal" with a one-click
   "Generate the standard checklist" (the D7 default-instantiation hook
   already exists server-side). Never an unexplained blank.
7. **Speed is a feature.** The workspace must paint its header and Timeline
   skeleton from one aggregate call (section 7.1); no request waterfalls;
   target < 1s to interactive on the dev environment.

---

## 4. Information architecture

### 4.1 Two surfaces, one mental model

```
/transactions                      /transactions/:transactionId
+--------------------------+      +------------------------------------+
| PORTFOLIO (Jake's grid)  |      | TRANSACTION WORKSPACE (new)        |
| - find the deal that     | ---> | - everything about ONE deal        |
|   needs me               | card | - the wizard's plan, alive         |
| - cross-deal urgency     | link | - all editing, all evidence        |
+--------------------------+      +------------------------------------+
```

- The portfolio answers "which deal needs me"; the workspace answers
  "everything about this deal". No content is exclusive to the drawer once
  Phase D completes; until then the drawer remains untouched.
- Routing: `TransactionDetailRouter` in App.tsx gains an internal-roles
  branch rendering `TransactionWorkspacePage`; the Attorney branch is
  untouched. The NotFound fallback remains for external roles.
- Deep links: `?tab=timeline|compliance|documents|tasks|people|activity`
  plus `?task=<id>` (scrolls + flashes the task) and `?requirement=<id>`.
  Existing `?expand=<txId>` portfolio links keep working unchanged; the
  Closing Calendar's deep links retarget to the workspace in Phase D (T6).
- Breadcrumb (mandatory for internal pages per the design-replication
  rule): `Transactions / 1912 Charles St`.

### 4.2 Where existing modals go

| Today (modal on card) | Workspace home | Phase |
| --- | --- | --- |
| DocumentsModal + MissingDocumentsPanel | Documents tab + Compliance tab | A (read), B (edit) |
| AddTaskModal | Tasks tab (same modal, launched in page context) | A |
| AddContactModal / AssignTeamModal / ManageClientAccessModal | People tab | A |
| HistoryPanel | Activity tab | A |
| CommunicationsPanel / ClientThreadDrawer / ComposeEmailModal | Activity tab (Communications section) + quick action | A |
| AIChatPanel | AI rail (persistent) | A |
| DateEditPopover (Key Dates) | Header tracking-dates strip + Timeline tab | A (same popover), B (cascade) |
| PostClosingFeedbackModal | Triggered from header when status -> Closed (unchanged) | A |

The modals are not rewritten in Phase A; they are mounted from the new page
with the same props. Page-native replacements come tab by tab in Phase B so
each step stays small and testable.

---

## 5. The Transaction Workspace, region by region

### 5.0 Layout

```
+--------------------------------------------------------------------------+
| Breadcrumb: Transactions / 1912 Charles St                    [actions]  |
| Jane & Amos Buyer                          STAGE PILL   Days to close 34 |
| 1912 Charles St, Springfield, OH 45501     Buy-Fin      Closing Jul 16   |
| AI next step: "Send the appraisal reminder today" [Do it ->]             |
+--------------------------------------------------------------------------+
| [KPI: Price] [KPI: Days to close] [KPI: Open tasks] [KPI: Missing docs]  |
+--------------------------------------------------------------------------+
| DEAL BRIEF  "Cash deal, no financing contingency. Watch out: ..."  [v]   |
+--------------------------------------------------------------------------+
| Timeline | Compliance | Documents | Tasks | People | Activity   || AI    |
|                                                                 || rail  |
|  <active tab content>                                           ||       |
|                                                                 ||       |
+--------------------------------------------------------------------------+
```

- Two-column on xl screens: content + a 360px AI rail. The rail collapses
  to a floating button below xl (same pattern the app already uses for the
  chat panel).
- Styling: tokens and composition from the Closing Calendar page (Jake's
  in-app benchmark) and All Documents (breadcrumb header pattern); type on
  the v2 comfort scale. Section 10 specifies it.

### 5.1 Header band

- Client names in serif, address + city/state/zip as the subtitle, stage
  pill, status control (the existing `PUT /transactions/{id}/status` flow
  with its confirmation), days-to-close in large serif tabular numerals.
  All header data comes from the plan aggregate's `header` block (7.1),
  never from the cards endpoint (W2).
- The AI next step line uses the cached `ai_next_step_*` columns on the
  transaction row with the same rule-based fallback the cards endpoint
  uses, served by the plan aggregate; clicking the CTA deep-links to the
  matching tab (never mutates anything, per the existing rule).
- Quick actions (icon buttons with labels, 48px targets): Add Task, Upload
  Document, Compose Email, Print closing checklist, Sync deadlines (the
  existing `SyncDeadlinesButton` with its invite-parties checkbox).
  "Share" was removed in review (W5): no per-deal share flow exists for
  internal roles; client visibility is Manage Client Access in the People
  tab, where it stays.
- Tracking-dates strip (the renamed Key Dates): the 7 operational fields as
  compact chips; set ones show the date with the existing severity colors,
  unset ones show "Not yet". Click opens the existing DateEditPopover. In
  Phase B, edits to `closing_date` / `possession_date` route through the
  cascade preview (5.4) because both are canonical anchors; the 5 pure
  tracking fields keep the direct edit because no basis anchor references
  any tracking COLUMN (W4: the anchor set is acceptance, closing,
  possession, plus four derived deadline anchors - none of which is a
  tracking field).

### 5.2 KPI strip

Four cards: Purchase price, Days to close, Open tasks (n overdue in red),
Missing documents (n overdue in red). Charts rule applied honestly: a
sparkline only where a real series exists in the data we already store -
task completions per week (`completed_at`) and documents uploaded per week
(`created_at`), 8 weekly buckets. Price and days-to-close get no decorative
sparkline. Counts and series are computed server-side into the plan
aggregate's `header` block (W12) so the strip renders before any lazy tab
query. Big numbers in `font-serif tabular-nums` per the chart conventions.

### 5.3 Deal Brief band

- For deals created after Phase C: the persisted brief (section 7.3), one
  short paragraph plus watch-out lines, each watch-out with a citation chip
  that opens the source viewer at the cited page.
- The factual sentences are re-assembled code-side from CURRENT transaction
  fields on every render (same assembler the wizard uses, extracted to a
  shared module), so the brief can never contradict the page around it.
  Only the watch-outs are stored text, because only they came from the LLM.
- Older deals: the band shows the code-assembled summary alone, no
  watch-outs, with no apology and no fake content.
- Collapsible; collapsed state remembered per user (localStorage).

### 5.4 Timeline tab (the centerpiece)

The wizard's timeline, alive. Reuses the wizard's components (mini-map,
row list, basis chips, rule editor) extracted to shared modules.

- **Mini-map** on top: the existing `TimelineMiniMap` SVG fed from live
  data; navy core dates, orange AI-created, champagne term-derived, dashed
  "today" marker.
- **Rows**, chronological, each showing: name, date, the basis in plain
  English ("14 days after Date of Acceptance" from `metadata.basis` /
  requirement rule / term field; "From the contract" for extracted dates;
  "Tracked manually" for operational dates the user opted to pin here),
  status (upcoming / today / overdue / done via linked task status), and
  the AI chip + citation where evidence exists.
- **Sources of rows** (all already persisted, assembled by the plan
  endpoint, section 7.1): core transaction dates; term-derived deadlines
  recomputed by the planner from the persisted term fields; deadline tasks
  (`metadata.kind = 'deadline'`); requirement due dates (toggleable layer,
  off by default to avoid double-listing what Compliance shows).
- **Anchor / core-date editing with cascade.** "Edit" on acceptance or
  closing opens the wizard's date editor, then calls
  `POST /transactions/{id}/plan/preview` (new, section 7.2) and renders the
  wizard's diff UI: "N deadlines and M task dates move", old struck
  through, new beside it, weekend rolls flagged. One Apply calls
  `/plan/apply` with a `commit_id`; an Undo chip offers one-click revert
  (the apply response carries the inverse diff). Per-row rule editing
  (change "7 days" to "10 days") uses the same preview/apply with a
  single-row scope.
- **Add deadline**: the wizard's deadline editor (name + rule stepper or
  specific date); creates a deadline task through the same server path the
  wizard uses, never client-computed.
- **Remove**: only rows backed by removable artifacts (custom/AI deadline
  tasks). Term-derived rows are non-removable here exactly as in the wizard
  (removal would silently mutate confirmed contract terms); the row's
  overflow menu links to "Edit contract terms" instead.
- **Command bar** at the top of the tab ("Tell me what to change"): the
  Part II closed-intent bar, post-create edition. Same
  `POST /ai/wizard-command` classification, executors mapped to the
  workspace's own mutations (add_deadline -> deadline task create;
  set_core_date -> cascade preview; waive_requirement -> requirement PATCH;
  toggle_auto_email -> the explicit `auto_draft_email` task patch field
  from 7.4, never generic metadata (W8); unknown -> honest refusal with
  capability list). Preview-then-apply and undo identical to the wizard.

### 5.5 Compliance tab

The wizard checklist step grown into a permanent surface, replacing the
buried MissingDocumentsPanel as the primary home (the panel remains in the
modal until Phase D).

- Open rows with due chip and basis, "Mark uploaded" picker, "Request by
  email" party picker (drafts into AI Email Review; nothing sends),
  Waive with Undo; collapsible Waived group with Un-waive; Uploaded group
  with the matched document link.
- **Full editing parity with the wizard** (Phase B), and the backend
  already supports all of it (W6): edit uses `PATCH /{requirement_id}`,
  which accepts name, description, status, and due rule with server-side
  re-resolution (`document_requirements.py:260+`); add uses `POST /bulk`
  with a fresh `commit_id` and a single item (bulk appends; idempotency is
  per-commit, verified). The work is frontend-only: extend the
  `PatchRequirementInput` hook type (today it exposes only
  status/matched/unmatch) and reuse the wizard's editor plus the checklist
  import modal as-is.
- AI-created rows show the chip; after Phase C, citation + confidence from
  the new columns.
- Empty state per principle 6 with the one-click standard-checklist
  generation. NOT via `tasks/generate` (it 409s when tasks exist, which
  every legacy deal does - W3): a dedicated
  `POST /transactions/{id}/document-requirements/defaults` endpoint wraps
  the existing `instantiate_default_requirements_if_absent` service.

### 5.6 Documents tab

The DocumentsModal content as a page surface.

- The existing list (download, version history, rename/classify, email,
  delete per role), upload button, and the post-upload parse-confirm flow
  ("Confirm AI-parsed document details" -> apply updates) unchanged.
- **Workspace-wide drop target**: dropping a file anywhere on the workspace
  routes here, uploads, parses, and (existing behavior) proposes a
  requirement match chip when the detected type matches an open row. This
  implements the requirements.txt "drag a document anywhere" ask within the
  deal's own page; the app-global version is decision T8.
- Side-by-side source viewer on xl screens when a document is selected
  (reuses the wizard's viewer with OCR search), so citation chips from any
  tab land somewhere visible without a modal.

### 5.7 Tasks tab

- The grouped sections (Overdue / Due Today / Upcoming / Completed) with
  the existing toggle, status menu, vendor-email button, and Add Task modal
  (with its AI-similar check, `POST /tasks/similar`).
- **What the redesign adds** (Phase B): each task row exposes what is
  already in its metadata and currently invisible: the basis chip ("3 days
  before Closing Date" from `metadata.basis`), the related compliance item
  (link to the Compliance row via `related_requirement_id`), the Auto-Email
  toggle (eligible tasks only, same eligibility rule as the wizard:
  target resolves to a captured party email), and the AI chip + citation
  where evidence exists.
- The rule editor from ReviewTasksStep is reused for due-date editing:
  pick a rule or a date, server resolves, mutually exclusive exactly as in
  the wizard.

### 5.8 People tab

- Party cards grouped by the existing representation-aware contact groups
  (Buyer/Seller principals, Agents, Lender, Title), with the existing
  add/edit flows (AddContactModal with section prefill), Assign team, and
  Manage client access.
- Each party shows the communication affordances that exist today (email
  compose, client thread) in place.
- Forward-compatibility note (not built now): groups are rendered from the
  backend's `contact_groups` contract, so when TC-as-vendor lands, a new
  group arriving from the server renders without frontend surgery.

### 5.9 Activity tab

- History (the audit feed from `useTransactionHistory`) and Communications
  (the existing panel) as two sections with a shared filter row.
- Cascade applies (section 7.2) write audit entries ("Closing moved
  Jul 16 -> Jul 23; 9 deadlines recomputed") so the answer to "what changed
  since I approved it" lives here.

### 5.10 AI rail

- The existing deal-scoped AIChatPanel, persistent on xl screens.
- One addition in copy, not capability: the rail's empty state lists the
  things the command bar can DO ("add a deadline", "waive a requirement",
  "move the closing"), teaching the closed-intent vocabulary.
- The chat stays read-only/advisory (existing rule: AI never mutates);
  mutations only flow through the command bar's preview-then-apply.

### 5.11 States

- Skeletons for every async region (one shimmer style per STYLE_GUIDE
  v2.4); error states with retry; empty states per principle 6.
- A deal with no wizard history (quick-create) renders fully: planner
  recomputes term deadlines, D7 gives it a checklist on demand, the brief
  band shows the code-assembled summary. The workspace must never assume
  wizard provenance.

---

## 6. The portfolio page after the split

Phase A adds exactly one element to the card: an "Open workspace" action
(card header + drawer footer), and makes the card title row a link. Nothing
else changes on Jake's surface without his comp approval:

- Phase D (gated on T2/T3): the drawer's Tasks/Key Dates/Contacts columns
  are replaced by a compact summary (next deadline, open counts, top 3
  tasks) with "Open workspace" as the primary affordance; the 16 modals
  stop being reachable from the card (they live in the workspace); the
  milestone bar stays exactly as designed.
- The sidebar deal-state filters, tabs, sort, search, URL state, exports,
  and print entry points are untouched by this plan (their contracts live
  in TRANSACTIONS_PAGE_COMPLETION_PLAN.md).

---

## 7. The data layer (without which the UI is paint)

### 7.1 The plan aggregate: `GET /transactions/{id}/plan` (new)

One deterministic, LLM-free response powering the header, mini-map, and
Timeline tab in a single request:

```jsonc
{
  "header":       { "display_title": "Jane & Amos Buyer",
                    "client_names": ["..."], "address_line": "...",
                    "stage_pill": { "label": "...", "color": "..." },
                    "days_to_close": 34,
                    "ai_next_step": { "text": "...", "cta": "...",
                                       "source": "ai" | "rule" },
                    "counts": { "open_tasks": 12, "overdue_tasks": 2,
                                 "missing_docs": 4, "overdue_docs": 1 },
                    "series": { "task_completions_weekly": [0,2,1,4,3,5,2,1],
                                 "documents_weekly": [1,0,2,1,0,3,1,0] } },
  "core_dates":   [ { "field": "closing_date", "label": "Closing Date",
                      "date": "2026-07-16", "source": "contract" } ],
  "term_rows":    [ { "label": "Home Inspection Deadline", "date": "...",
                      "basis": "7 days after Date of Acceptance",
                      "term_field": "inspection_days" } ],
  "deadline_tasks": [ { "task_id": "...", "name": "Septic evaluation",
                        "date": "...", "status": "Pending",
                        "basis": { "days": 14, "direction": "after",
                                   "anchor": "contract_acceptance_date" },
                        "ai": { "confidence": 0.93, "source_page": 4,
                                 "snippet": "..." } | null } ],
  "requirements_due": [ ... ],          // for the optional layer
  "tracking_dates": [ ... ],            // the 7 operational fields
  "brief": { "summary_inputs": {...}, "watchouts": [...] | null }
}
```

- Server-side: load transaction + tasks + requirements (existing repos),
  run `timeline_planner` on the persisted terms for `term_rows`, read task
  metadata for bases and evidence. Same `require_transaction_access` and
  tenant scoping as every transaction read.
- This endpoint is also the regression oracle: a test asserts that for a
  wizard-created fixture, the plan response contains every row the wizard
  committed (the create-boundary invariant, made executable).

### 7.2 The cascade: `POST /transactions/{id}/plan/preview` and `/plan/apply` (new)

- `preview` body: `{ changes: { contract_acceptance_date?, closing_date?,
  possession_date?, term_fields? }, scope?: { task_id } }`. The server
  clones the transaction state, applies the changes, and recomputes THREE
  rule populations (W1, W4):
  1. **Term rows**: rerun `timeline_planner` on the changed terms.
  2. **Template tasks** (`source = "template"`, `template_id` set): rerun
     `plan_tasks_for_transaction` twice - under the OLD anchors and the
     NEW anchors. A task whose current due date equals its old-plan date
     is rule-bound and moves to its new-plan date; one that differs was
     pinned by a human and is listed under "not moved (pinned)". This
     comparison is what makes review-step pins safe without any schema
     change, since storage cannot distinguish them.
  3. **Basis-bearing tasks and requirements** (`metadata.basis` /
     `due_days` + `due_anchor`): re-resolve through the planner. Chained
     anchors resolve transitively (a basis on `inspection_deadline` moves
     when acceptance moves), exactly as `resolve_added_task_basis` already
     resolves canonical anchors.
  Returns a diff: per item `{ kind, id, label, old_date, new_date,
  rolled_weekend }`, the field changes themselves, and the pinned list.
- `apply` body: the same `changes` plus `commit_id` (UUID). The server
  recomputes (never trusts client dates), writes the transaction fields,
  task due dates, and requirement due dates, records one audit entry with
  the diff, and returns the applied diff plus the inverse `changes` for
  the Undo chip. Replaying the same `commit_id` returns the original
  result without re-applying. The response also carries
  `calendar_resync_recommended: true` when the user has calendar
  connections, and the UI follows the Apply confirmation with a one-click
  "Re-sync deadlines" chip (existing push endpoint) so externally pushed
  events do not go quietly stale (W7). The in-app Closing Calendar reads
  live transaction fields and needs nothing.
- Undo (W10): a fresh `/plan/apply` with the inverse `changes` and a NEW
  `commit_id`. Planner determinism restores rule-bound rows; anything the
  user edited between Apply and Undo reads as pinned under the same
  comparison and is listed, never clobbered.
- Tasks with neither template linkage nor basis are listed under "not
  moved (no rule)" - the honest version of a cascade.
- Policy recommendation (decision T5): always preview + confirm, never
  silent auto-apply, including edits made from the tracking-dates strip.

### 7.3 Evidence persistence at the create boundary

The only data genuinely lost today. Three small changes, all at wizard
commit time (no new AI calls):

1. **Tasks**: include the citation in the existing `metadata_json`
   (`{ confidence, source_page, snippet, document_id? }`). No migration;
   the wizard already holds these values at submit.
2. **Requirements**: migration adds `confidence NUMERIC`, `source_page
   INTEGER`, `snippet TEXT` to `transaction_document_requirements`; the
   bulk endpoint accepts and stores them (it already receives source
   `'ai'`).
3. **Brief**: new table `transaction_briefs` (one row per transaction:
   `watchouts JSONB` with citations, `created_at`, `commit_id`), written at
   create when the wizard has a generated brief. The summary text is NOT
   stored (re-assembled from live fields per 5.3).

Older transactions degrade honestly per the completion bar.

### 7.4 Small verified gaps to close

- `PATCH /tasks/{id}`: VERIFIED 2026-06-12 - `TaskUpdateRequest`
  (`app/schemas/task.py:38-53`) has no metadata field at all, so generic
  metadata writes are impossible today. The plan therefore specifies the
  explicit route: add `auto_draft_email: bool | None` and
  `basis: TaskBasisInput | None` to the patch schema; the endpoint merges
  them into `metadata_json` server-side and, when `basis` changes,
  re-resolves the due date through the planner (server-only date math,
  rule 1). Generic client-written metadata stays impossible on purpose.
- The plan endpoint needs task `metadata_json` in the task list response it
  consumes internally (repo already returns full rows; only the new
  response schema exposes the curated subset).
- Key-date label copy change ("Tracking Dates") is frontend copy plus the
  testing guides; the API field names do not change (T4).

---

## 8. Work inventory

### 8.1 Endpoints used, existing (verified in source)

| Endpoint | Used by |
| --- | --- |
| `GET /transactions/{id}` | header, all tabs |
| `PATCH /transactions/{id}` | non-derived field edits only (e.g. notes); the client never patches anchor dates or terms directly in Phase B+ - `/plan/apply` writes those server-side (W9) |
| `PUT /transactions/{id}/status` | header status control |
| `PUT /transactions/{id}/key-dates` | tracking-date edits (Phase A direct; Phase B via cascade for closing/possession) |
| `GET /transactions/{id}/checklist` + print contract | Print closing checklist |
| `GET /tasks/transaction/{id}`, `PATCH /tasks/{id}`, `PUT /tasks/{id}/status`, `POST /tasks/similar` | Tasks tab |
| `GET/PATCH /transactions/{id}/document-requirements`, `/bulk`, relink | Compliance tab |
| `GET /documents/transaction/{id}` + upload/parse/version endpoints | Documents tab |
| `GET /transactions/{id}/parties` + party mutations | People tab |
| `POST /ai-emails/compose` | request-document drafts |
| `POST /dashboard/ai-chat` | AI rail |
| `POST /ai/wizard-command` | workspace command bar |
| `POST /api/v1/calendar/push/transaction/{id}` | Sync deadlines |
| transaction history + communications endpoints (existing hooks) | Activity tab |
| `GET /confidence/` | ship-it threshold for chip rendering |

### 8.2 New endpoints (specified in section 7)

| Endpoint | Phase |
| --- | --- |
| `GET /transactions/{id}/plan` | A |
| `POST /transactions/{id}/document-requirements/defaults` (wraps the existing `instantiate_default_requirements_if_absent` service; W3) | A |
| `POST /transactions/{id}/plan/preview` | B |
| `POST /transactions/{id}/plan/apply` | B |
| `PATCH /tasks/{id}` gains explicit `auto_draft_email` / `basis` fields (7.4; W11) | B |
| Wizard commit passes evidence through (tasks metadata, requirements columns, brief insert) | C |

### 8.3 Frontend inventory

- New: `src/pages/transactions/TransactionWorkspacePage.tsx` + one file per
  tab under `src/components/workspace/`; `useTransactionPlan`,
  `usePlanPreview/Apply` hooks; router branch in `TransactionDetailRouter`.
- Extracted to shared (moves, not rewrites; wizard imports update):
  `TimelineMiniMap`, the deadline/rule editor, the basis-chip row renderer,
  `WizardDealBrief`'s assembler, `ChecklistImportModal`, the source viewer,
  the command bar shell (executors injected per surface).
- Reused in place: every modal listed in 4.2.
- Test impact: WizardFlow tests must keep passing after extraction
  (import-path churn only); new workspace integration suite stubs every
  endpoint in 8.1 from day one (lesson 9).

### 8.4 Migrations (for Jan, in order)

1. `20260817090000_document_requirements.sql` (pending from Part I)
2. `20260817100000_document_requirement_templates_seed.sql` (pending)
3. `20260818090000_requirement_source_ai.sql` (pending from Part II)
4. NEW (Phase C): requirement evidence columns
5. NEW (Phase C): `transaction_briefs`

Phases A and B function with 1-3 only; Phase C needs 4-5. The workspace
renders without any of them for legacy deals (honest empty states).

---

## 9. Visual specification

- **Layout reference**: this page is a NEW comp. Per the established
  replication rule, layout comes from the agreed wireframe (5.0, to be
  blessed by Jake as T1 via side-by-side screenshots), styling comes from
  the in-app benchmarks: Closing Calendar (header, cards, pills, stat
  blocks) and All Documents (breadcrumb header).
- **Type**: v2 comfort scale throughout; this is the first non-wizard
  surface on v2 and serves as the D13 pilot. Body 15px/1.6, labels 12.5px,
  kickers 12px mono 1.5px tracking, section titles serif 20px, hero
  numerals serif 24-28px tabular, nothing below 12px, muted ink rules per
  v2.2.
- **Color and AI language**: champagne AI surfaces, the four standard
  elements from v2.5 (confidence chip, citation chip, pre-confirmed check,
  banner) used identically to the wizard so the visual vocabulary carries
  across the create boundary.
- **Shape and motion**: cards 12px radius, one shadow token, 150/250ms,
  single shimmer, skeletons everywhere async (v2.3-2.4).
- **Density**: rows 52px minimum, 48px hit areas, whitespace over
  hairlines. The workspace is a daily tool for professionals: calm, not
  cute.

---

## 10. Rollout phases

Each phase is independently shippable, additive, and ends with a testing
guide section plus screenshots for Jake.

- **Phase A - The workspace exists (read + existing editors).**
  Plan endpoint; workspace page with all six tabs in read mode; modals
  mounted from page context; "Open workspace" on the card; deep links.
  Risk: near zero (no existing surface changes behavior).
- **Phase B - The plan is alive (editing parity + cascade).**
  Preview/apply endpoints; cascade UX on core dates and rules; Compliance
  full editor; Tasks basis/auto-email/rule editing; workspace command bar.
- **Phase C - Evidence survives (persistence + chips).**
  Commit-time evidence pass-through; migrations 4-5; citation chips and
  brief band live for new deals.
- **Phase D - The portfolio sheds weight (Jake-gated).**
  Card/drawer slimming per approved comp; calendar deep links retarget;
  modals reachable only in the workspace.
- **Phase E - Comfort scale goes global (D13 executed).**
  With wizard + workspace both proving v2, the app-wide token remap ships
  per the STYLE_GUIDE v2 rollout note.

Suggested order of decisions before code: T1 (wireframe), T5 (cascade
policy), T4 (naming). T2/T3/T6 can wait until Phase D planning.

---

## 11. Decisions for Jake (T-series)

| # | Decision | Recommendation |
| --- | --- | --- |
| T1 | Approve the workspace wireframe (5.0) via side-by-side screenshots | Approve with Calendar-page styling |
| T2 | Card click behavior after Phase D: expand drawer (today) vs navigate to workspace | Navigate; keep a small expander for the summary |
| T3 | Drawer retirement scope and timing | Retire in Phase D, keep milestone bar + summary |
| T4 | Rename "Key Dates" copy to "Tracking Dates" | Yes; ends the vocabulary collision with Timeline |
| T5 | Cascade policy: always preview + one confirm vs silent auto-apply | Always preview; silence moves deadlines invisibly |
| T6 | Calendar deep-link target after Phase D | Workspace Timeline tab with the date flashed |
| T7 | Notes (the card's `note_count` placeholder): build into Activity tab now or defer | Defer; separate scope |
| T8 | App-global drag-and-drop upload (requirements.txt ask) vs workspace-wide only | Workspace-wide now; global is its own project |
| T9 | Fold D13 (global comfort scale) into Phase E of this plan | Yes; this page is the pilot D13 was waiting for |
| T10 | Print closing checklist profile-template completion (prior plan slice 4) priority relative to Phase B | Keep independent; no dependency either way |

---

## 12. Testing plan

- **Backend**: unit tests for the plan aggregate (wizard-fixture invariant:
  nothing the wizard committed is missing from the plan response; header
  block counts/series correct); cascade preview/apply (template tasks at
  their old-plan dates move, a template task with an edited date is listed
  as pinned and untouched, basis tasks with chained anchors move
  transitively, requirement rules re-resolve, weekend rolls, idempotent
  `commit_id` replay, undo restores via inverse changes, audit entry
  written, `calendar_resync_recommended` set only with connections, tenant
  + role denials); the defaults endpoint (creates the library rows once,
  no-ops on replay and on wizard-created deals); evidence pass-through
  (metadata citation present, requirement columns populated, brief row
  written once).
- **Frontend**: a `TransactionWorkspace.test.tsx` integration suite with
  every endpoint stubbed (lesson 9): renders all tabs from the plan
  fixture; cascade diff -> Apply -> Undo; auto-email toggle; command bar
  preview/apply/refusal; requirement waive/un-waive; deep links land on the
  right tab; legacy-deal empty states.
- **Testing guide**: new `TRANSACTION_WORKSPACE_TESTING_GUIDE.md` in the
  WIZARD_TESTING_GUIDE format - mouse-only scripts: "open a deal and answer
  the five questions" (2.2), "move the closing and watch everything move",
  "waive a requirement and undo it", "ask the bar to add a deadline",
  "verify an AI deadline against the contract", plus a regression section
  for the portfolio page (unchanged behaviors).
- **Visual verification**: every phase ends with rendered screenshots
  (Chrome headless flow per the established method) compared against the
  approved wireframe before Jake review; no UI is built blind.

---

## 13. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Touching Jake's most-iterated surface | Phases A-C add without altering it; D is comp-gated (T2/T3) |
| Extraction churn breaks the 67-test wizard suite | Extraction is move-only with import updates; suite must stay green per phase gate |
| Five pending migrations stack up | 8.4 sequencing; A/B run on 1-3; page degrades honestly without 4-5 |
| Stale dev backend on :8000 masks new endpoints | Test against the fresh-uvicorn :8001 flow (established practice) |
| Cards endpoint performance habits leak into the workspace | The workspace never calls the cards endpoint; one plan call + per-tab lazy queries |
| Pre-redesign deals look "worse" than new ones | Honest notes, not fake evidence; D7 one-click checklist generation; planner recomputes term rows for every deal |
| Scope creep into notes/global-drop/SMS | Explicit non-goals + T7/T8 |

---

## 14. Superiority scorecard (the bar this plan is judged against)

| Capability | ListedKit | Velvet Elves after this plan |
| --- | --- | --- |
| See the intake plan after creation | Re-open intake steps (snapshot) | Live plan from current records, one URL |
| Why does this deadline exist | Not evidenced | Basis chip + AI citation into the document, forever |
| Move the closing date | Edit fields | Full cascade diff, one Apply, undo, audit entry |
| Compliance checklist after create | Static list | Living checklist: edit, import, waive/undo, request-by-email drafts |
| AI actions on a live deal | Generic assistant | Closed-intent command bar: preview, apply, undo, never guesses |
| Trust story | "AI extracted this" | "AI proposed, engine verified, here is the page in the contract" |
| Eye comfort | Standard SaaS | v2 comfort scale, nothing below 12px, AA at rendered size |

---

## 15. Hardcoding audit

Asked directly: "are there any hardcoded elements?" Yes. They fall into
three classes, and the plan's disposition for each is explicit so none of
them is an accident.

### 15.1 Deliberately closed sets (kept closed; this is the safety design)

| Element | Where | Why it stays hardcoded |
| --- | --- | --- |
| Command-bar intent schema | `WIZARD_COMMAND_INTENTS` (`app/services/ai_service.py`), executors in the frontend | The closed schema is WHY the bar can never guess or mutate unsupervised. Extending it is a code change by design; the workspace edition reuses the same list. |
| Rule anchors | `CANONICAL_ANCHORS` / `COMMAND_ANCHORS` | Anchors are contract concepts (acceptance, closing, possession). An open set would let arbitrary strings into date arithmetic. |
| Verifier thresholds and windows | `citation_check.MATCH_THRESHOLD`, date-sanity windows | Verifier constants; admin-tunable variants are a future decision, not silent config. The user-facing confidence threshold is already NOT hardcoded (`GET /confidence/`). |
| Basis phrasing | plan endpoint / planner templates | Deterministic English from rule parts; templated on purpose so previews are reproducible. |
| v2 type scale values | STYLE_GUIDE v2 tokens | Design tokens are definitionally fixed; rollout is governed by D13/T9. |

### 15.2 Schema-bound lists (hardcoded because the database is)

| Element | Where | Disposition |
| --- | --- | --- |
| The 7 tracking-date fields | `_build_key_dates` (`dashboard.py:3088`), mirrored by the Calendar's `EventKind` | Each entry maps to a real transaction column. Adding an 8th means a migration regardless, so a config table buys nothing. Kept; copy renamed per T4. |
| Derived-deadline rule set | `timeline_planner.py` term fields | The deterministic floor. Deliberate; the AI layer (not config) is the extension mechanism, per Part II architecture. |
| Requirement seed library | `20260817100000_..._seed.sql` | Already data-driven (DB templates, tenant-extensible). The frontend's `STANDARD_REQUIREMENT_NAMES` mirror exists only for dedupe display and must not grow; the workspace reads templates from the API instead. |

### 15.3 Incidental hardcoding (debt; this plan addresses it)

| Element | Where | Action in this plan |
| --- | --- | --- |
| Role lists duplicated with semantic drift | `INTERNAL_ROLES` defined separately in `App.tsx` (excludes Attorney, plus `INTERNAL_AND_ATTORNEY`), `DocumentsModal.tsx` (includes Attorney), `DocumentsPage.tsx`, `OnboardingWizard.tsx` | Phase A consolidates into one constants module with NAMED semantics (`INTERNAL_OPS_ROLES`, `INTERNAL_PLUS_ATTORNEY`) before the workspace adds a fifth copy. Pure refactor, no behavior change, covered by existing route tests. |
| Milestone-bar keyword bucketing | `MilestoneTimeline.tsx:53-64` (`jakeStageIndexForLabel`) | Kept in Phases A-C (Jake's canonical card visual; the workspace, not the bar, is now the home of deal-specific rows). Phase D may replace keyword matching with an explicit `stage` field on milestone dots from the backend - listed as part of the T3 scope so it rides the comp approval. |
| Calendar deep-link URL shape | `CalendarPage.tsx` builds `?expand=` links by hand | Phase D (T6) replaces with a shared route helper when links retarget to the workspace. |

Rule for implementation reviews: any NEW hardcoded list introduced by the
workspace must be classifiable under 15.1 or 15.2 in its PR description, or
it does not merge.

---

*Drafted 2026-06-12 by Jan's dev pass, grounded in the documents and source
cited in section 0. Revised same day (first revision): 7.4 verified against
`app/schemas/task.py` (no metadata field on TaskUpdateRequest; explicit
patch fields specified), section 15 hardcoding audit added. Revised same
day (second revision): full workflow-and-logic review pass; corrections
W1-W12 logged in section 0.3 and applied in place (template-task cascade,
plan-aggregate header block, defaults endpoint, anchor-set fact fix, Share
removed, requirement editing cited as existing, calendar re-sync prompt,
executor consistency, undo semantics). No source code was changed for this
plan.*
