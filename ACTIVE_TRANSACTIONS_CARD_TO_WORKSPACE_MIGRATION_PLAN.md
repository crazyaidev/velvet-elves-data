# Active Transactions Card to Transaction Workspace Migration Plan

> Comparative analysis of the expanded transaction card on the Active
> Transactions list page versus the Transaction Detail page (the Transaction
> Workspace at `/transactions/:transactionId`), and the complete plan to
> migrate the card's functions into the workspace, close the workspace's
> remaining gaps, and revamp the card into a fast, modern triage surface.
>
> Status: **PARTLY SUPERSEDED 2026-07-22 — read §16 FIRST.** All five phases
> were implemented, then the premise was rejected on review: the expanded card
> stays. §16 records what was reverted, what was kept, and the redesign of the
> Transaction Detail page that replaced the removal work. §15 is the as-built
> log of the original implementation and is retained for the reasoning, not as
> a description of the current code.
>
> This plan executes what TRANSACTION_PAGE_REDESIGN_SUPERIORITY_PLAN.md
> called "Phase D: the portfolio sheds weight" (deferred there, gated on
> decisions T2/T3/T6), but it re-grounds every claim in the CURRENT source
> code rather than inheriting that plan's 2026-06-12 snapshot. Project
> documents were treated as references; where a document and the source
> disagree, the source is cited and wins.

---

## 1. Grounding

### 1.1 Documents reviewed (velvet-elves-data)

| Document | What this plan takes from it |
| --- | --- |
| requirements.txt, notes-active_transactions_page.txt | Product-owner asks that live on this surface: print closing checklist from profile templates, AI chat filter/suggest, drag-a-document-anywhere, deal-state sidebar filters, "In Inspection" definition |
| TRANSACTION_PAGE_REDESIGN_SUPERIORITY_PLAN.md | Phase D scope and the T2/T3/T6 recommendations (navigate on click, retire the drawer, retarget calendar links); §13 rule that the workspace never calls the cards endpoint |
| TRANSACTIONS_PAGE_COMPLETION_PLAN.md | The list page's standing contracts: routes and aliases, URL state (`?expand`, `?task`, `?highlight`), export/print entry points, "no visible control is cosmetic" |
| FRONTEND_UI_WORKFLOW_LOGIC.md | Every producer of deep links into the list page (dashboards, task queue, calendar, clients hub, notifications); "no dead-end pages" |
| STYLE_GUIDE.md (v2 comfort scale, §4.5 action bars, §6 components, §13 anti-patterns) | Type, spacing, selector, and dialog rules for the new surfaces |
| LISTEDKIT_COMPETITIVE_ANALYSIS_AND_FEATURE_IMPROVEMENT_PLAN.md | The industry pattern this plan converges on: list = triage, one workspace per deal = work |
| TRANSACTION_WORKSPACE_TESTING_GUIDE.md, FRONTEND_UI_TESTING_GUIDELINES.md | The mouse-only testing format Phase 5 extends |
| VE-ActiveTransactions.html | Jake's canonical comp for the card FACE and milestone bar; the face survives this plan, the drawer does not |

### 1.2 Source reviewed (current code, load-bearing findings)

| Finding | Where |
| --- | --- |
| The list page mounts 9 modal/panel components, TaskEmailFlow, an invoice modal, and a delete dialog, all reachable only through the card | `src/pages/transactions/TransactionListPage.tsx` (1,190 lines) |
| The card itself is 1,280 lines: collapsed face, 3-column drawer (Tasks / Key Dates / Contacts), invoices panel, AI suggestions strip, 8-button emoji footer | `src/components/shared/TransactionCard.tsx` |
| The workspace is live for all internal ops roles and is agent-first by default (`agentWorkspaceEnabled()` defaults on; localStorage `ve_agent_workspace_v1='off'` is only an escape hatch) | `src/App.tsx:177-184`, `src/components/agent/agentRefs.ts:33-42` |
| The workspace renders 8 tabs (Agent, Timeline, Compliance, Documents, Tasks, People, Activity, Email) over the plan aggregate | `src/pages/transactions/TransactionWorkspacePage.tsx` |
| The plan aggregate header ALREADY carries `days_to_close`, `closing_date`, `purchase_price`, `ai_next_step`, task/doc counts | `src/hooks/useTransactionPlan.ts:36-65` |
| `tracking_dates` is in the plan aggregate but rendered NOWHERE: `TrackingDatesCard`, `WorkspaceStatBand`, `WorkspaceQuickActions` are dead exports since the 2026-06-13 restyle | `src/hooks/useTransactionPlan.ts:190`, `src/components/workspace/WorkspaceHeader.tsx` (only `STAGE_PILL_CLASS` and `WorkspacePostureControl` are imported by the page) |
| The workspace has NO invoices surface and NO delete-transaction control | grep for `invoice` in `src/components/workspace/` returns nothing; delete exists only in the card footer |
| Card Key Dates edits write `PUT /transactions/{id}/key-dates` directly, with NO cascade offer, while the workspace routes closing/possession through preview/apply | `TransactionListPage.tsx:616-625` vs `TimelineTab.tsx` + `CascadeEditor.tsx` |
| The card's per-deal "unanswered client question" dot comes from one cheap summary call | `useClientThreadSummary`, `TransactionListPage.tsx:538-549` |
| Roughly 20 files produce `?expand=` / `?highlight=` deep links into the list page | grep inventory in §7.1 below |
| Backend endpoints for every card function are transaction-scoped and already callable from the workspace | `app/api/v1/`: transactions.py (delete 919, key-dates 1054, status 1013, checklist 1134, history 2060, exports 527-628), invoices.py, tasks.py, transaction_parties.py, transaction_assignments.py, client_messages.py, communication_logs.py, documents.py, transaction_plan.py |
| The cards endpoint serializes drawer-only payloads (task_sections, key_dates, contact_groups) for every card on every list load; it ALSO returns `inline_tasks` (top 5 active tasks with `task_id`, name, status, due, overdue flag) | `app/api/v1/dashboard.py:2443` (transaction-cards), `_build_key_dates:3153`, `_build_task_sections:3188`, inline tasks `:2740-2754` |
| The list page is NOT the only consumer of the cards endpoint: the Solo Agent dashboard fetches it and merges `inline_tasks`, `key_dates`, and `contacts` into the Priority-transactions detail panel | `src/pages/dashboards/SoloAgentDashboardPage.tsx:64,258-278` (`PriorityDealCard` enrichment, with a graceful `rich ? enriched : d` fallback) |

### 1.3 Review corrections (2026-07-22 second pass, R1-R10)

A workflow-and-logic review of the first draft against the source found the
following errors. Each is corrected in place below; this log records what
was wrong so reviewers can verify the fix.

- **R1 (critical, hidden consumer).** The Phase 4 payload diet claimed the
  drawer payloads had no consumer after the card slims. False: the Solo
  Agent dashboard merges `key_dates` (plus `inline_tasks` and `contacts`,
  which survive the diet) into its Priority-transactions panel
  (`SoloAgentDashboardPage.tsx:258-278`). §9.1 now names both consumers,
  keeps `inline_tasks` and `contacts` in the slim response, and specifies
  the dashboard change that rides the same release.
- **R2 (workflow, G2).** The next-step CTA cannot open TaskEmailFlow with a
  task id alone: the flow requires `taskLabel` (`TaskEmailFlow` props; the
  card passes `next_deadline_label`). The backend addition is `task_id`
  AND `task_label` on the header's `ai_next_step` block. §6.2/§9.3 fixed.
- **R3 (factual).** "Contact decryption drops out of the list path
  entirely" was wrong: the card face's primary contact and the Solo
  dashboard's panel still consume the decrypted `contacts` list
  (`dashboard.py:2767-2779`). Only the `contact_groups` duplication drops.
  §9.1 reworded.
- **R4 (sequencing gap).** The peek row's data source was unspecified for
  the release window between Phase 3 (drawer gone) and Phase 4 (diet).
  Resolved, and simplified: the existing `inline_tasks` field already
  carries exactly what the peek needs (task_id for quick-complete, name,
  due, overdue), in both phases. The invented `top_tasks`/`next_deadline`
  additions are DELETED from §9.1: no new backend fields are needed for
  the peek at all.
- **R5 (missing fallback).** The face banner's CTA spec assumed a backing
  task id; the cards endpoint returns `next_deadline_task_id = null` for
  banners derived without a dated task. §8.1 adds the fallback (navigate
  to the workspace root, where the agent pane owns the conversation).
- **R6 (deep-link fidelity).** The Task Queue retarget dropped the task
  id its rows carry; §7.1 now flashes the task. Also verified: the
  Communication Audit page's `?log=` param is ALREADY ignored by the list
  page today (no reader in `TransactionListPage.tsx`), so retargeting to
  the Activity tab loses nothing that works now.
- **R7 (phase dependency understated).** Phase 2's `?tab=billing` and
  `qa=1`/`access=1` targets only exist after Phase 1 ships. §14 now states
  Phase 2 lands after Phase 1 (they can be built in parallel, merged in
  order).
- **R8 (cache coherence, G3).** A tracking-date save from the workspace
  must invalidate the dashboard cards query as well as the plan query, or
  the list card shows the stale date until its 60s staleTime lapses. §6.3
  fixed.
- **R9 (parity detail, G3).** Closing/Possession carry stored times
  (`closing_time`, `possession_time`); the card popover never edited
  times and the rail must not pretend to. §6.3 now shows times read-only
  on those two chips, matching the card.
- **R10 (mobile completeness).** With the peek row md-and-up, phones lost
  the Print/Delete entry points the footer used to give them. Intentional
  and now stated in §8.2: on phones those whole-deal actions live in the
  workspace header overflow (G6), one tap away.

Verified-good claims worth recording (no change needed): the plan header
already returns `days_to_close`, `closing_date`, `purchase_price`,
`ai_next_step`, and `tracking_dates` (`transaction_plan.py:555,650-669`,
reusing the dashboard's `_build_key_dates` via the dict adapter); no
canonical planner anchor references the five tracking columns
(`intake_intelligence.py:39-47`), so their popover edit stays
cascade-free; `GET /invoices` is readable by any internal role (only
`get_current_user`, `invoices.py:114-148`) with create gated by the
capability matrix, so the Billing tab's read-for-all/create-gated split is
sound; `DELETE /transactions/{id}` is `require_role(ADMIN, TEAM_LEAD)`
(`transactions.py:919-942`); `PUT key-dates` accepts exactly the seven
card fields plus the two times and includes TC in its role gate
(`transactions.py:1054-1068`); `HistoryPanel` and `TasksFullViewModal`
have no consumers outside the card/list pair, so their retirement is safe;
`CascadeEditor` already treats `possession_date` as a core date
(`CascadeEditor.tsx:147`).

---

## 2. The problem, stated precisely

The expanded card is a second, older transaction-detail surface embedded in
the list page. Every deal-scoped action it offers now has a better-designed
home in the workspace, except three (invoices, delete, tracking-date quick
edit) that have no workspace home at all. The consequences:

1. **Cramped execution.** Real work happens inside a card drawer squeezed
   between other cards, through 9 stacked modals, with a 260 px scroll box
   for tasks. The workspace gives the same actions a full page.
2. **Split brains.** Two surfaces answer "what is the state of this deal"
   from two different aggregates (cards endpoint vs plan aggregate), and the
   card's date editor bypasses the cascade the workspace teaches. A user who
   edits closing on the card silently strands every rule-driven deadline.
3. **Payload waste.** The list loads task sections, key dates, and contact
   groups for every visible card even though most cards are never expanded.
4. **Style drift.** The card footer is emoji buttons (🖨 🕐 ✉️ 💬 💳 🗑),
   which the style guide's iconography rules and the flat modern tool
   direction both forbid on new work.
5. **Industry mismatch.** Every comparable TC tool (ListedKit, Open To
   Close, SkySlope, Dotloop) treats the list as a triage/filter surface and
   routes all work into one page per deal. Our list currently tries to BE
   the deal page.

The goal state: the card face stays (Jake's comp) as a rich summary and a
door; the workspace is the only place transaction work happens; the list
page keeps only portfolio-level tools (filters, sort, search, exports).

---

## 3. Function inventory A: the expanded card today

Everything a user can DO from the card, with the component and endpoint
behind it. "Face" = collapsed card; "Drawer" = expanded area; "Footer" =
the button row under the drawer.

### 3.1 Face (collapsed card)

| # | Function | Component / endpoint |
| --- | --- | --- |
| A1 | Open workspace (title link + maximize icon) | `Link to /transactions/:id` |
| A2 | Expand/collapse drawer (click anywhere) | local state |
| A3 | Urgency border + stage pill + why badges | cards endpoint `stage_pill`, `why_badges` |
| A4 | AI next-step banner with CTA (task-backed opens TaskEmailFlow; otherwise AI chat with prompt) | `next_deadline_task_id`, `TaskEmailFlow`, `useAiChat` |
| A5 | Primary contact with tel: link | cards endpoint `contacts` |
| A6 | Milestone bar | `MilestoneTimeline`, `milestone_timeline` |
| A7 | Info badges: Tasks count; Docs count opens DocumentsModal | `onOpenDocs` |
| A8 | Stats: days to close, overdue count, price | cards endpoint |
| A9 | Assignee chip | `assignee_name` |

### 3.2 Drawer

| # | Function | Component / endpoint |
| --- | --- | --- |
| B1 | Tasks column: Overdue / Due Today / Upcoming / Completed sections, checkbox complete/reopen with optimistic toggle + Undo toast | `PATCH /tasks/{id}` |
| B2 | Per-task email button (party pre-resolved from the task's matrix target) | `TaskEmailFlow` |
| B3 | Tasks full-view modal (search + filter across sections) | `TasksFullViewModal` |
| B4 | Add Task (with AI similar-task/approach suggestions) | `AddTaskModal`, `POST /tasks` |
| B5 | Key Dates column: 7 fields (EM Delivered, Inspection Response, Appraisal Expected, CD Delivered, Cleared to Close, Closing, Possession) with click-to-edit popover | `DateEditPopover`, `PUT /transactions/{id}/key-dates` (no cascade) |
| B6 | Sync deadlines to external calendar | `SyncDeadlinesButton`, `POST /calendar/push/transaction/{id}` |
| B7 | Contacts column: representation-aware groups, expandable rows, tel:/mailto:, per-group Add | `AddContactModal`, parties API |
| B8 | Assign team | `AssignTeamModal`, assignments API |
| B9 | Invoices & Payments panel: per-deal invoice list, status pills, links to invoice detail, View all, Create Invoice | `useInvoices({transaction_id, scope:'tenant'})`, `NewInvoiceModal` |
| B10 | AI suggestions strip (3 heuristic chips into the chat drawer) | client-side `buildAiSuggestions`, `useAiChat` |

### 3.3 Footer

| # | Function | Component / endpoint |
| --- | --- | --- |
| C1 | Open workspace | link |
| C2 | View/Add Docs: the full documents manager (upload, rename/classify, versions, email, delete, parse-confirm, missing-docs panel) | `DocumentsModal` (886 lines) |
| C3 | Print closing checklist (profile templates) | `printClosingChecklist`, `GET /transactions/{id}/closing-checklist` |
| C4 | History (audit feed panel) | `HistoryPanel`, history endpoint |
| C5 | Comms (communication logs: search, resend, export, compose, test inbound) | `CommunicationsPanel` |
| C6 | Client access (invite / add / remove portal client) | `ManageClientAccessModal` |
| C7 | Client Q&A thread (with unanswered amber dot) | `ClientThreadDrawer`, `useClientThreadSummary` |
| C8 | Invoice deal | `NewInvoiceModal` (capability-gated) |
| C9 | Delete transaction (TeamLead/Admin, confirm dialog) | `DELETE /transactions/{id}` |

### 3.4 List-page chrome (NOT card functions; stays regardless)

Filter tabs with counts, sort menu, team-member filter, debounced search,
CSV/Excel/PDF exports, AdSlot, AskAiFab, deep-link handling
(`?expand`, `?highlight`, `?task`, `?clientqa`, `?clientaccess`), the
silent AI next-step refresh.

---

## 4. Function inventory B: the Transaction Workspace today

| Surface | Functions |
| --- | --- |
| Header | Breadcrumb; % complete progress; "Saving…" in-flight pill; status dropdown with confirm (Closed triggers post-closing feedback modal); agent-pane toggle; serif identity + stage pill + address; automation posture control with "handled / needs you" line; creation receipt (`?created=1`); coverage banners (resolve-in-place decisions) |
| Page-wide | Drag-drop a file anywhere routes to Documents and uploads; deep links `?tab`, `?task` (flash), `?requirement` (flash) |
| Agent pane / tab | Deal-scoped AI conversation; reference chips that navigate and flash rows in the owning tab; document analysis streaming |
| Timeline tab | Core dates with cascade preview → Apply → Undo → re-sync chip; term rows ("7 days" edits through the same cascade); deadline tasks with the wizard's rule editor (server-resolved basis); Add deadline; Remove = Skipped + Undo; cash-appraisal decision flip; AI evidence chips; SyncDeadlinesButton |
| Compliance tab | Requirement rows: attach (existing file or upload in place), waive/unwaive, inline rule edits, add via AddDocumentModal, one-click standard checklist on empty, AI verification chips, per-row email |
| Documents tab | Document list with verification chips; classified upload dialog; download; print closing checklist; full DocumentsModal manager mount; per-row Ask AI |
| Tasks tab | Grouped sections; colored status selector (Pending/In progress/Completed/Skipped); basis chips; auto-email toggle (eligibility = target resolves to a captured party email); task email flow; Add Task modal; rule editor for due dates; related-requirement links; AI-handled tasks surfaced honestly |
| People tab | Representation-aware party groups; add/edit via AddContactModal with prefill; tel: links; compose email; per-row Ask AI; Client Q&A drawer; Assign team; Manage client access; Deal fees section with edit dialog |
| Activity tab | History audit feed inline; Automation lens (what ran without a click, with Undo); Communications panel mount |
| Email tab | Outbox-first AI drafts (nothing sends without approval), send-all-ready, inbound thread, compose, links to /ai-emails |

---

## 5. The comparative matrix and disposition

Disposition legend:
- **COVERED**: already in the workspace, nothing to build; the card copy retires.
- **GAP**: must be built in the workspace BEFORE the card sheds it (Phase 1).
- **FACE**: stays on the slim card face (summary/triage value).
- **LIST**: stays as list-page chrome.
- **RETIRE**: removed with no replacement (justified inline).

| Card function | Workspace home | Disposition |
| --- | --- | --- |
| A1 Open workspace | is the workspace | FACE (the whole card becomes the door) |
| A2 Expand drawer | n/a | RETIRE, replaced by navigate + optional peek (§8.2, decision D1) |
| A3 Pills/badges | header stage pill | FACE (list triage value) |
| A4 AI next-step banner + CTA | **not rendered** (header block carries `ai_next_step` unused) | GAP G2 + FACE (banner stays on card; CTA becomes a deep link) |
| A5 Primary contact | People tab | FACE (read-only) |
| A6 Milestone bar | Timeline tab (richer) | FACE (Jake's comp) |
| A7 Docs/Tasks badges | Documents/Tasks tabs | FACE as deep links, modal opener retires |
| A8 Stats (days/overdue/price) | **header shows % complete only**; data already in plan header | GAP G1 (compact header stats) + FACE |
| A9 Assignee chip | People tab (Assign team) | FACE |
| B1 Task sections + complete toggle | Tasks tab | COVERED (peek MAY keep quick-complete, decision D2) |
| B2 Task email flow | Tasks tab | COVERED |
| B3 Tasks full-view modal | Tasks tab IS the full view | COVERED, `TasksFullViewModal` retires |
| B4 Add Task | Tasks tab (same modal) | COVERED |
| B5 Key Dates quick edit (7 fields) | **not rendered anywhere** (`tracking_dates` unused; card edit bypasses cascade) | GAP G3 (tracking rail on Timeline; closing/possession via cascade) |
| B6 Sync deadlines | Timeline tab | COVERED |
| B7 Contact groups + add | People tab | COVERED |
| B8 Assign team | People tab | COVERED |
| B9 Invoices & Payments panel + create | **absent** | GAP G4 (Billing tab) |
| B10 AI suggestions strip | Agent pane owns suggestions | RETIRE (heuristic chips; the agent pane is the strictly better surface) |
| C1 Open workspace | n/a | FACE |
| C2 Documents manager | Documents tab (mounts the same modal) | COVERED |
| C3 Print checklist | Documents tab | COVERED (also added to header overflow, §6.5) |
| C4 History panel | Activity tab (inline, richer) | COVERED, `HistoryPanel` retires |
| C5 Communications panel | Activity tab (mounts the same panel) | COVERED |
| C6 Client access | People tab | COVERED |
| C7 Client Q&A + unanswered dot | People tab has the drawer; **no unanswered dot** | GAP G5 (dot on People trigger + card face chip) |
| C8 Invoice deal | with G4 | COVERED after G4 |
| C9 Delete transaction | **absent** | GAP G6 (header overflow menu) |
| Exports, filters, sort, search, team filter, AdSlot, AskAiFab | portfolio-level | LIST |

Summary: 17 of 24 card functions are already fully covered by the
workspace. 6 gaps (G1 to G6) must be closed first; 1 function retires
outright. Nothing migrates until its workspace home exists: at no point in
the phasing is any function unreachable.

---

## 6. Phase 1: close the workspace gaps (parity before removal)

All gaps are frontend-only except one optional field addition (G2). Every
item lists its acceptance check in the mouse-only format testers use.

### 6.1 G1: Deal stat strip in the header

A single quiet stat row in the workspace header (identity row, right side,
or directly under it): **Days to close** (with closing date), **Overdue
tasks**, **Price**. All three values are already in `plan.header`
(`days_to_close`, `closing_date`, `purchase_price`,
`counts.overdue_tasks`); zero new requests. Styling follows the existing
% complete indicator (11.5px medium, tabular numerals), NOT the retired
`WorkspaceStatBand` sparkline card (delete that dead code in Phase 4).
Overdue > 0 renders in `ve-red`; days ≤ 7 red, ≤ 21 amber (mirror
`CLOSE_NUM_COLOR` thresholds from the card).

Accept: open any deal; the header shows the same three numbers the card
face shows for that deal; no layout shift on mobile (stats wrap under the
title).

### 6.2 G2: AI next-step strip

Render `plan.header.ai_next_step` as the champagne strip under the identity
row (the card's A4 banner, restyled to the workspace voice: `ve-orange-light`
background, lucide `Zap`, no emoji). CTA behavior:

- If the backend can name the backing task, the CTA opens the existing
  TaskEmailFlow exactly as the card does today. This needs one small
  backend addition: include `task_id` AND `task_label` in the plan
  header's `ai_next_step` block (TaskEmailFlow requires a label; the card
  passes `next_deadline_label`). The header builder already iterates the
  task that becomes the next deadline (`transaction_plan.py:615-628`), so
  both values are one assignment away.
- Fallback (no task id, which the cards endpoint also produces for
  banners without a dated task): CTA switches to the Tasks tab.

Dismissal is not needed (the strip reflects live state and disappears when
nothing is pending). If the backend addition is deferred, ship the fallback
first; the strip is still honest.

Accept: a deal whose card shows "Next step: …" shows the same text in the
workspace header; clicking the CTA opens the email flow (or lands on Tasks)
without leaving the page.

### 6.3 G3: Tracking dates rail on the Timeline tab

A compact chip rail at the top of the Timeline tab rendering
`plan.tracking_dates` (7 chips, color by `status`: unset/overdue/today/
future/cleared, same map as `DATE_CHIP_CLASS` in the dead
`TrackingDatesCard`; revive and simplify that component rather than
rewriting).

Interaction, preserving the cascade doctrine (T5):

- The 5 pure tracking fields (EM Delivered, Inspection Response, Appraisal
  Expected, CD Delivered, Cleared to Close): click opens `DateEditPopover`,
  saves via `PUT /transactions/{id}/key-dates`, then invalidates BOTH the
  plan query and the dashboard cards query (`['dashboard']`), so the list
  card face agrees the moment the user returns to it (R8). No cascade
  needed: no planner anchor references these columns
  (`intake_intelligence.py:39-47`).
- Closing and Possession chips do NOT open the popover; they open the
  existing `CoreDateChangePicker`/`CascadeEditor` flow (preview, Apply,
  Undo), the same as the core-date rows below. Their stored times
  (`closing_time`, `possession_time`) render read-only on the chip,
  exactly as the card displayed them; time editing was never offered on
  the card and is not added here (R9).

This closes the card's most dangerous behavior: today the card lets a user
move Closing with a raw field write and no cascade offer. After Phase 3 the
raw path is unreachable from the UI.

Accept: click "Inspection Response" chip, pick a date, chip recolors and
the list page's card shows the same date after refresh; click "Closing
Date" chip, get the cascade preview (not a bare date input), Apply, see the
moved deadlines listed.

### 6.4 G4: Billing tab (Invoices & Payments)

New workspace tab `billing` (lucide `Receipt`, label "Billing") porting the
card's `TransactionInvoicesPanel` content to a full surface:

- Invoice rows: status pill (Draft/Sent/Paid/Void/Uncollectible), payer,
  due/paid date, amount, row click to `/payments/invoices/:id`. Data:
  existing `useInvoices({ transaction_id, scope: 'tenant', page_size })`.
- "Create Invoice" (primary, top-right) mounts the existing
  `NewInvoiceModal` prefilled with the deal. Gate the button by
  `usePaymentCapabilities().canCreateInvoice` exactly as the card does;
  the tab itself renders for all internal roles (read access).
- Empty state per style guide §11: dashed card, one-line explanation, the
  Create button when permitted.
- "View all in Payments" link to `/payments`.

Tab list grows to 9 with the flag-on Agent tab; the tab bar already
horizontal-scrolls (`overflow-x-auto`), so no layout work.

Accept: a deal with invoices shows them under Billing with the same
statuses as `/payments`; Create Invoice opens prefilled; a TC without
invoice capability sees the list but no Create button.

### 6.5 G5: Client Q&A unanswered signal

- People tab: amber dot on the "Client Q&A" button when this deal's client
  has an unanswered question. Data: reuse `useClientThreadSummary` (one
  cheap tenant-wide call, already cached for the list page) and filter by
  this transaction id. No backend change.
- Deep-link params on the People tab: `?tab=people&qa=1` auto-opens the
  Client Q&A drawer; `?tab=people&access=1` auto-opens Manage client
  access. One-shot: strip the param after opening (mirror the list page's
  `clientqa`/`clientaccess` handling). These params are what §7 retargets
  the Clients-hub links to.

Accept: ask a question as the portal client, open the deal as staff: People
tab button carries the dot; the Clients-hub "Q&A" button lands directly in
the open drawer.

### 6.6 G6: Delete transaction (and header overflow menu)

Add a "⋯" overflow `DropdownMenu` at the end of the header controls
(next to the status pill), with:

- **Print closing checklist** (all internal roles): the same
  `printClosingChecklist` call the Documents tab makes. Duplicated entry
  point on purpose: printing is a whole-deal action, not a documents-only
  action, and the card offered it one click from the face.
- **Delete transaction…** (TeamLead/Admin only, red, `useConfirm` with
  destructive tone, description naming the address and warning about
  attached documents): `DELETE /transactions/{id}`; on success toast +
  navigate to `/transactions/active`. 403 handling mirrors the list page's
  copy ("You don't have permission to delete transactions").

Accept: as Agent the menu shows Print only; as TeamLead it shows Delete,
which confirms, deletes, and lands back on the list without the deal.

---

## 7. Phase 2: deep-link retargeting

### 7.1 Producer inventory and new targets

A shared helper `src/utils/transactionLinks.ts`:

```ts
workspaceUrl(id, opts?: { tab?, task?, requirement?, qa?, access? })
```

All producers switch to it. Current producers (grep inventory, 2026-07-22):

| Producer | Today | New target |
| --- | --- | --- |
| `useNotifications.ts:40` | `/transactions?status=…&expand=&task=` | `workspaceUrl(id, { tab:'tasks', task })` |
| `ClientsHubPage.tsx:54` (+`clientqa`/`clientaccess`) | list + one-shot flags | `workspaceUrl(id, { tab:'people', qa:1 })` / `{ access:1 }` |
| `CalendarPage.tsx:240` | `?status=all&expand=` | `workspaceUrl(id, { tab:'timeline' })` (T6 resolved) |
| `TaskQueuePage.tsx:162,512` | `?highlight=` | `workspaceUrl(id, { tab:'tasks', task })` where the queue row carries a task id, else `{ tab:'tasks' }` (R6) |
| Invoice/payment surfaces (`InvoiceDetailPage.tsx:379`, `InvoiceDetailModal.tsx:271`, `PaymentDetailModal.tsx:302`, `PayoutDetailModal.tsx:199`) | `?highlight=` | `workspaceUrl(id, { tab:'billing' })` |
| Dashboards (`ActionQueueList`, `PriorityTransactionList`, `PriorityDealCard`, `InterventionQueueItem`, `TeamLeaderDashboardPage:399`, `DashboardPage:55,85`, `AnalyticsPage:193`) | `?highlight=`/`?expand=` | `workspaceUrl(id)` |
| Create flows (`TransactionForm:58`, `TransactionList:209`, `NewTransactionModal:86`, `OnboardingWizard:499`, wizard fallback `NewTransactionWizard:4701`) | `?highlight=` | `workspaceUrl(id)` (the wizard's primary path already lands on the workspace with `?created=1`) |
| `VendorDetailModal.tsx:73` | `?expand=` | `workspaceUrl(id)` |
| `CommunicationAuditPage.tsx:859` | `?highlight=&log=` | `workspaceUrl(id, { tab:'activity' })`. No regression: the list page never read `?log=` (no consumer in `TransactionListPage.tsx`), so per-log flash is new polish, not lost behavior (R6) |

### 7.2 Back-compat shim on the list page

Old bookmarks, notification emails, and stale clients still carry
`?expand=`/`?highlight=`. The list page keeps parsing them, but instead of
expanding a card it issues a replace-navigate to `workspaceUrl`, translating
`?task`, `?clientqa`, `?clientaccess` on the way. This preserves the
"no dead-end pages" contract with zero server work. The shim stays
permanently (it is 15 lines).

Accept: paste an old `?expand=<id>&task=<tid>` URL: you land on the
workspace Tasks tab with the task flashed.

---

## 8. Phase 3: the revamped card and list page

Design doctrine for this phase: the list is for scanning, deciding, and
jumping. Every control on it must be justified by triage value. Anything
that EDITS the deal lives in the workspace.

### 8.1 The card face (kept, with four changes)

The face keeps Jake's comp: title, stage pill, why badges, address,
assignee chip, AI next-step banner, primary contact, milestone bar, info
badges, stat cluster (days to close / overdue / price). Changes:

1. **Click = navigate.** Clicking anywhere on the card opens the workspace
   (T2 recommendation). The title link and maximize icon remain for
   middle-click/new-tab affordance. Keyboard: the card gets `role="link"`
   and Enter opens it.
2. **Badges become doors.** The Docs badge deep-links to
   `?tab=documents`; the Tasks badge to `?tab=tasks`. No modal opens from
   the list anymore.
3. **AI banner CTA becomes a door.** The CTA navigates to
   `workspaceUrl(id, { tab:'tasks', task: next_deadline_task_id })`; the
   workspace's own next-step strip (G2) offers the email flow there. When
   `next_deadline_task_id` is null (banner without a dated task), the CTA
   navigates to `workspaceUrl(id)` and the agent pane owns the
   conversation, replacing today's chat-drawer fallback (R5). The list
   page stops mounting TaskEmailFlow.
4. **Client-question chip.** When the deal has an unanswered client
   question, an amber "Client question" why-badge appears and deep-links to
   `?tab=people&qa=1` (replaces the footer dot).

### 8.2 The peek row (replaces the drawer)

The chevron remains, but expansion now reveals a single compact strip, not
a 3-column workspace clone:

- **Next deadline** (label + date, colored by status).
- **Top 3 open tasks** by urgency, each with a quick-complete checkbox
  (optimistic, Undo toast: `PATCH /tasks/{id}`, the ONE mutation that
  stays on the list because check-off-from-triage is the highest-frequency
  action in this product).
- **Counts line**: open tasks, docs, missing docs.
- **"Open workspace" primary button** plus a lucide `MoreVertical` kebab
  with: Tasks, Documents, People, Billing (deep links), Print checklist,
  and Delete… (TeamLead/Admin, red, confirm). All kebab items are either
  navigation or the two whole-deal actions; nothing mounts a form.

Peek data source (R4): the existing cards-endpoint `inline_tasks` field
(top 5 active tasks, each with `task_id`, name, status, due date, overdue
flag) serves the peek in BOTH phases: Phase 3 reads it from the payload
that already ships today, and Phase 4's diet keeps it. The "next deadline"
line is the first row of `inline_tasks` (earliest due), so no new backend
field is needed anywhere in this plan for the peek.

Everything else in the current drawer and footer is removed from the list
page: the Tasks/Key Dates/Contacts columns, the invoices panel, the AI
suggestions strip, and the emoji footer. The 9 modal/panel mounts,
TaskEmailFlow, NewInvoiceModal, and the delete dialog leave
`TransactionListPage.tsx` (the delete confirm moves into the card kebab
flow using `useConfirm`). Expected size: the page drops from ~1,190 to
roughly 500 lines; the card from ~1,280 to roughly 450.

If Jake prefers zero expansion (pure navigate), the peek row is the only
thing cut; the kebab moves onto the face. That is decision D1; the peek is
the recommended default because it preserves the two genuinely fast list
behaviors (glance at next work, tick a task) without recreating a detail
surface.

### 8.3 Visual and interaction standards

- Icons: lucide only on all new controls; the emoji glyph buttons retire
  (matches the no-emoji-icon rule and the existing workspace voice).
- Selectors and menus: existing shadcn `DropdownMenu`/`Select` voices
  already on the page (sort chip, team filter) are the reference.
- Flat modern tool aesthetic: the AI-suggestions gradient strip dies with
  the drawer; no gradient panels return.
- Density: card vertical rhythm tightens (the face currently reserves
  space for drawer affordances); target is more deals per viewport without
  dropping the milestone bar.
- Mobile: navigate-on-tap replaces the cramped drawer entirely; the peek
  row is desktop/tablet only (`md:` up). This is strictly better than
  today's phone experience of a 3-column drawer collapsed to one column.
  Consequence, intentional (R10): on phones the Print and Delete entry
  points live in the workspace header overflow (G6), one tap past the
  card, instead of on the card itself.
- Empty/loading states, scroll ownership, and the ad slot are unchanged.
- **Approval gate:** before implementation is declared done, headless
  screenshots (desktop + mobile, collapsed + peek) go to Jake as
  before/after pairs. The card face is Jake's comp territory; no visual
  delta ships without that sign-off.

### 8.4 What the list page keeps (explicit non-goals)

Filter tabs + counts endpoint, sort, team-member filter, search with URL
persistence, CSV/Excel/PDF exports, Print Report, AdSlot, AskAiFab, the
silent AI next-step refresh, and all `TRANSACTIONS_PAGE_COMPLETION_PLAN`
contracts not explicitly retargeted in §7.

---

## 9. Phase 4: backend slimming and dead-code retirement

Sequenced one release AFTER Phase 3 ships, so no in-flight client breaks.

### 9.1 Cards endpoint payload diet

`GET /dashboard/transaction-cards` has TWO consumers (R1): the list page
and the Solo Agent dashboard (`SoloAgentDashboardPage.tsx:64`, which
merges `inline_tasks`, `key_dates`, and `contacts` into the
Priority-transactions detail panel). The diet accounts for both:

- **Drops**: `task_sections`, `contact_groups`, `key_dates`. Nothing
  invented in their place: the peek row runs on the existing
  `inline_tasks` (R4), and the face keeps `contacts` for the primary
  contact line.
- **Keeps**: everything the face and peek consume: identity fields,
  pills/badges, `milestone_timeline`, stats, `next_deadline_label`/
  `next_deadline_task_id`/`next_step_cta`, `contacts`, `inline_tasks`,
  counts, assignee.
- **Solo dashboard change (same release)**: its enrichment keeps the
  `inline_tasks` and `contacts` merges unchanged and drops only the
  `key_dates` list from the panel, replaced by a "Timeline" deep link
  into the workspace (`workspaceUrl(id, { tab:'timeline' })`), consistent
  with this plan's doctrine. The component already degrades gracefully
  when enrichment fields are absent (`rich ? enriched : d`), so the
  ordering within the release is safe.
- **Transition mechanics**: add `?include=drawer` (default ON) in the same
  release as Phase 3; the updated list page and dashboard omit it; the
  param and the `_build_task_sections`/`_build_key_dates`/
  `_build_contact_groups` card-path calls are removed only after BOTH
  consumers ship.

Wins: the heaviest per-card builders stop running for every card on every
list load, filter change, and search keystroke-settle; per-contact
decryption shrinks to the `contacts` list alone (the `contact_groups`
duplication of the same decrypted rows disappears) (R3). `_build_key_dates`
itself stays: the plan aggregate reuses it for `tracking_dates`.

### 9.2 Frontend retirement list

| Retires | Reason |
| --- | --- |
| `TasksFullViewModal.tsx` | Tasks tab is the full view |
| `HistoryPanel.tsx` | Activity tab renders history inline |
| Drawer/footer sections + 10 callback props in `TransactionCard.tsx` | replaced by peek + kebab |
| `buildAiSuggestions` + suggestions strip | agent pane owns suggestions |
| `WorkspaceStatBand`, `WorkspaceQuickActions`, dead parts of `WorkspaceHeader.tsx`, `DealOverviewCard` remnants | dead since the 2026-06-13 restyle; G1/G3 revive only `TrackingDatesCard` (simplified) |
| List-page mounts of AddTaskModal, DocumentsModal, AddContactModal, AssignTeamModal, ManageClientAccessModal, ClientThreadDrawer, CommunicationsPanel, TaskEmailFlow, NewInvoiceModal, delete AlertDialog | all mount from workspace tabs already (Billing tab adds the invoice mount) |

Components that STAY shared (workspace still mounts them):
`AddTaskModal`, `AddContactModal`, `AssignTeamModal`,
`ManageClientAccessModal`, `ClientThreadDrawer`, `CommunicationsPanel`,
`ComposeEmailModal`, `DocumentsModal` + `MissingDocumentsPanel`,
`DateEditPopover`, `PostClosingFeedbackModal`, `TestInboundButton`,
`NewTransactionModal` (onboarding), `AIChatPanel` (global chat in
AppLayout). The `active-transactions/` directory is renamed in spirit only;
keep the path to avoid a 30-file import churn, or rename to
`components/deal/` as a mechanical follow-up. Recommendation: keep the path.

### 9.3 Small backend additions recap

1. `ai_next_step.task_id` + `ai_next_step.task_label` in the plan header
   (G2/R2; both values are in scope in the header builder's
   next-deadline loop, `transaction_plan.py:615-628`). Optional for the
   first release: the strip ships with the Tasks-tab fallback CTA.
2. The `?include=drawer` transition param on the cards endpoint (9.1).
3. Nothing else: invoices, delete, key-dates, checklist, history, comms,
   client access, thread, assignments, parties, tasks, and exports all have
   existing transaction-scoped endpoints verified in §1.2, and the peek row
   needs no new fields (R4).

---

## 10. Phase 5: verification (mouse-only, tester-facing)

Testers are real-estate professionals; every acceptance below is a click
path, no dev tools.

### 10.1 Parity walkthrough (the core script)

For each row of the §5 matrix, the guide names the OLD click path and the
NEW click path. Sample rows:

| I used to… | Now I… |
| --- | --- |
| Expand the card and tick a task | Same on the peek row, or open the deal, Tasks tab |
| Expand the card and click "Inspection Response" to set it | Open the deal, Timeline tab, click the chip |
| Change Closing on the card | Open the deal, Timeline: Closing chip shows a preview of everything that moves before I apply |
| Click 💳 Invoice on the card | Open the deal, Billing tab, Create Invoice |
| Click 🗑 Delete on the card | Open the deal, "⋯" menu, Delete transaction |
| Click 💬 Client Q&A | Amber "Client question" chip on the card, or People tab |

### 10.2 Regression scripts

1. **Deep links**: one click from each producer surface in §7.1 lands on
   the right workspace tab with the right row flashed; one legacy
   `?expand=` URL redirects.
2. **Role gates**: Agent / TC / TeamLead / Admin each walk the kebab, the
   header overflow, Billing, and People: only permitted actions render
   (matrix in the guide). Attorney still gets the Matter Workspace.
3. **Mobile pass** (390 px): card tap opens the workspace; list chrome
   usable; workspace tabs scroll.
4. **Honesty checks**: empty Billing tab, deal with no next step (no
   strip), deal with no tasks (peek shows counts only), closed deal.
5. **List performance smoke**: 50-deal tenant, filter and search stay
   responsive (payload diet verification is a network-tab check Jan runs,
   not a tester step).

### 10.3 Engineering verification

- Frontend integration tests: list page (navigate-on-click, peek
  quick-complete, kebab gating, shim redirect), workspace (Billing tab,
  delete flow, tracking rail popover vs cascade routing, qa dot, next-step
  strip), every endpoint stubbed per house rule.
- Backend tests: plan header `task_id`/`task_label`, slim cards response
  shape, `include=drawer` back-compat.
- Solo Agent dashboard integration test: the Priority-transactions panel
  renders (tasks + contacts + Timeline link) against the slim response
  with `include=drawer` omitted (R1).
- Headless screenshots before/after for Jake (desktop + mobile), per the
  approval gate in §8.3.
- Update FRONTEND_UI_WORKFLOW_LOGIC.md sections for both pages, and mark
  the retargeted links in TRANSACTIONS_PAGE_COMPLETION_PLAN.md as
  superseded by this plan.

---

## 11. Decisions for Jake (D-series)

| # | Decision | Recommendation |
| --- | --- | --- |
| D1 | Card expansion after the revamp: peek row vs pure navigate | Peek row: keeps glance + quick-complete without recreating a detail surface |
| D2 | Quick-complete checkboxes on the peek row | Yes: highest-frequency action, one click, undoable |
| D3 | AI banner CTA target | Workspace Tasks tab with the task flashed (email flow offered there); no modals on the list |
| D4 | New tab name: "Billing" vs "Invoices" | "Billing": room for payouts/receipts later |
| D5 | Client-question chip on the card face | Yes: it is triage signal, and the footer dot dies with the footer |
| D6 | Cards-endpoint diet timing | One release after Phase 3 (the `include=drawer` bridge) |

T2/T3/T6 from the prior plan are hereby resolved by D1/D3 and §7.1
(calendar → Timeline tab) pending Jake's sign-off on this document.

---

## 12. Invariants this plan obeys

1. Nothing is removed before its workspace home ships (Phase 1 before 3).
2. The server is the only place date arithmetic happens; closing and
   possession edits ALWAYS route through cascade preview/apply, and Phase 3
   removes the UI's last raw write path to those fields.
3. The workspace never calls the cards endpoint; the list never calls the
   plan aggregate.
4. No ghost endpoints: every call named here is cited to an existing route
   in §1.2, except the additions in §9.3, which are specified with the
   exact builder locations they extend.
5. Role checks include TransactionCoordinator on every mutation; delete
   stays TeamLead/Admin; tenant isolation untouched.
6. Honest surfaces: no fabricated data, empty states name the action that
   fills them.
7. URL-shareable state for every surface a tester can reach; all legacy
   URLs redirect rather than dead-end.
8. Mouse-only operability for every migrated function; minimal typing
   (dates via pickers, contacts via prefilled modals).
9. Card-face visual changes ship only after screenshot approval from Jake.
10. Tests stub every endpoint a component calls.

---

## 13. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Muscle-memory disruption for current testers | §10.1 old-path/new-path table; peek row preserves the two fastest habits; Jake reviews before/after screenshots before anything ships |
| A missed `?expand` producer dead-ends | Permanent list-page shim (§7.2) catches ANY straggler, including external bookmarks |
| Stale clients after the payload diet | `include=drawer` bridge, removed only after BOTH consumers (list page and Solo Agent dashboard) are fully rolled out |
| Tab crowding (9 tabs with agent flag on) | Tab bar already scrolls; Billing sits last; if crowding bites, fold Email into Activity later (separate decision, not this plan) |
| Workspace load becomes the hot path for actions that used to be one click on the list | The plan aggregate is one deterministic request and the page skeleton renders instantly; peek row keeps true one-click actions on the list |
| Cascade friction for users who liked the card's instant date edit | Only closing/possession gain the preview step, and that friction is the point: silent deadline drift was a bug, not a convenience |

---

## 14. Phase order and rough effort

| Phase | Contents | Effort |
| --- | --- | --- |
| 1 | G1 stats, G2 next-step strip, G3 tracking rail, G4 Billing tab, G5 Q&A signal, G6 delete + overflow menu | 2-3 days |
| 2 | Link helper, 20 producer retargets, shim | 1 day |
| 3 | Card face changes, peek row, kebab, list-page purge, screenshots + Jake gate | 2-3 days |
| 4 | Cards endpoint diet + `include=drawer`, Solo-dashboard panel update, dead-code retirement | 1-2 days |
| 5 | Testing guide, integration tests, doc updates | 1-2 days |

Phases 1 and 2 are invisible to Jake's comp and can start immediately, but
Phase 2 MERGES after Phase 1: its `?tab=billing` and `qa=1`/`access=1`
targets only exist once Phase 1 ships (R7). Phase 3 waits for the D-series
answers and the screenshot gate. Phase 4 ships one release after Phase 3
and touches both cards-endpoint consumers in the same release (§9.1).

---

## 15. As-built log (2026-07-22)

All five phases are implemented and uncommitted. Verification: backend
**1,338 passed** (ruff clean); frontend **targeted suites green** —
TransactionWorkspace 17/17, the new TransactionListCard 10/10, the new
transactionLinks 12/12, plus WizardFlow / AuthFlow / AgentWorkspace /
ComplianceAddDocument / ClientStaff 97/97; `tsc`, `eslint --max-warnings=0`,
and `vite build` all clean. Card face and workspace header were rendered and
screenshotted (`C:\Projects\_shots\migration-card.png`,
`migration-workspace.png`) rather than shipped blind; those are the pair for
Jake's §8.3 approval gate.

### 15.1 Two deliberate departures from the plan

- **A1 — the peek counts line.** §8.2 specified "open tasks, docs, missing
  docs". The cards endpoint has no missing-docs count (only `task_count`,
  `doc_count`, `overdue_count`), and inventing one would have meant a new
  backend field for a triage line. Shipped as **open · docs · overdue**,
  which is the same information the face's badges already source. No
  fabricated numbers, no new endpoint work.
- **A2 — the wizard's save-draft exit.** The Phase 2 sweep retargeted
  `NewTransactionWizard`'s draft exit to the deal workspace along with every
  other producer. That was wrong: a saved draft has no plan yet, the toast
  says "finish it any time from your transactions", and the existing
  WizardFlow test pins the list. Reverted to `ROUTES.TRANSACTIONS`. Only
  Accept & Create lands on a workspace. The lesson generalizes: "go to the
  list" navigation is not "focus this deal" navigation, and a blanket sweep
  cannot tell them apart.

### 15.2 Fixes found by building it

- **`DateEditPopover` had no accessible name on its date input.** The visible
  title sat in a plain `div`, so a screen reader announced an unlabeled date
  field. This popover is now how every tracking date is edited, so it got an
  explicit `aria-label`.
- **Duplicate control names on the Timeline tab.** With the rail mounted, the
  Closing Date chip and the Closing Date core row both exposed "Edit Closing
  Date". The chip now names its current value ("Edit Closing Date, currently
  Jul 16"), which is both unambiguous and more useful when announced.
- **Tracking-date saves left the list stale (R8, confirmed in code).**
  `useSaveTrackingDate` now invalidates `['dashboard']` alongside the plan
  query, so the card face agrees the moment the user goes back.

### 15.3 What shipped, by file

**Backend**
- `api/v1/transaction_plan.py` — `ai_next_step` gained `task_id` +
  `task_label`, populated from the same next-deadline loop that already
  produced the guidance text (G2/R2).
- `api/v1/dashboard.py` + `schemas/dashboard.py` — `?include=drawer` bridge;
  `task_sections`, `contact_groups`, and `key_dates` are no longer built for
  the card path unless asked for. `inline_tasks` and `contacts` stay (§9.1).
- Tests: `test_transaction_plan.py` asserts the task hand-off;
  `test_dashboard_api.py` gained `test_transaction_cards_omit_drawer_payloads_by_default`
  (slim by default, bridge still serves older clients).

**Frontend — workspace (Phase 1)**
- `components/workspace/WorkspaceHeader.tsx` — new `WorkspaceHeaderStats`
  (G1), `WorkspaceNextStepStrip` (G2), `WorkspaceOverflowMenu` (G6);
  `TrackingDatesRow` revived with the dashboard-cache fix and read-only
  times; `WorkspaceStatBand`, `WorkspaceQuickActions`, `DealOverviewCard`,
  `StatCell`, `Sparkline` deleted as dead code.
- `components/workspace/BillingTab.tsx` — new (G4), read for all internal
  roles, Create gated on `canCreateInvoice`.
- `components/workspace/TimelineTab.tsx` — mounts the tracking rail (G3).
- `components/workspace/PeopleTab.tsx` — unanswered-question dot and the
  `?qa=1` / `?access=1` one-shot deep links (G5).
- `pages/transactions/TransactionWorkspacePage.tsx` — Billing tab, header
  stats/strip/overflow, delete flow with `useConfirm`, TaskEmailFlow mount.

**Frontend — links (Phase 2)**
- `utils/transactionLinks.ts` — new `workspaceUrl()` + `legacyExpandRedirect()`.
- 19 producers retargeted across notifications, Clients hub, Calendar, Task
  Queue, four payment surfaces, seven dashboard surfaces, create flows, the
  vendor modal, and the communication audit page.
- `hooks/useNotifications.ts` — notifications open the task in the deal;
  `transactionStatusBucket` deleted (its only consumer was that URL).

**Frontend — card and list (Phase 3)**
- `components/shared/TransactionCard.tsx` — rewritten: 1,280 → ~590 lines.
  Face is the door (`role="link"` + Enter), badges and banner are deep links,
  peek row with quick-complete and a kebab; drawer, invoices panel, AI
  suggestions strip, and emoji footer removed.
- `pages/transactions/TransactionListPage.tsx` — 1,190 → ~700 lines. All nine
  modal/panel mounts, TaskEmailFlow, NewInvoiceModal, the key-date mutation,
  and the delete AlertDialog removed; legacy shim added.
- Deleted: `TasksFullViewModal.tsx`, `HistoryPanel.tsx`.

**Frontend — Phase 4**
- `PriorityDealCard` / `SoloAgentDashboardPage` — the panel's key-dates column
  became a Timeline door; task and contact merges unchanged (R1).

### 15.4 Still open

- **Jake's D1-D6 answers and the §8.3 screenshot approval.** The card face is
  his comp territory; the two PNGs above are ready to send. If D1 comes back
  "pure navigate", the peek row is one deletion — the kebab moves to the face.
- **The `include=drawer` bridge removal.** Per D6 it stays one release, then
  the param and the three builder calls come out of `dashboard.py`.
- **Testing-guide rewrite** (§10.1's old-path/new-path table) for the
  real-estate testers, as a companion doc.

---

## 16. Course correction (2026-07-22, same day)

On review of the shipped UI the direction was rejected: **the expanded card
keeps the functionality it has in `ve-active_transactions.html`**, and the
problem to solve was the Transaction Detail page itself, which read as
overly complex and non-standard.

That verdict is right, and the plan's central assumption was wrong. This
document argued the card and the detail page were duplicates and one had to
go. They are not duplicates; they answer different questions:

- The **list + drawer** is a triage surface. A coordinator working twelve
  deals wants to scan, tick a task, set a date, call someone, and move on
  without a page load per deal. The drawer is the fastest possible version of
  that, and Jake's comp designed it deliberately.
- The **detail page** is a work surface for one deal: the plan with the
  cascade, the checklist, the document manager, billing, the audit trail.

Removing the first to justify the second traded a fast path for a page
navigation and called it simplification. The real complexity was on the
detail page: an AI pane taking 55% of the screen before anyone asked for it,
nine tabs, and the sections rendered in a card nested in a grid nested in a
padded body.

### 16.1 Reverted (the card and its data are back, unchanged)

- `TransactionCard.tsx` and `TransactionListPage.tsx` restored from HEAD: the
  three-column drawer (Tasks / Key Dates / Contacts), the invoices panel, the
  AI-suggestions strip, the footer actions, and all nine modal mounts.
- `TasksFullViewModal.tsx` and `HistoryPanel.tsx` restored (not deleted).
- The cards-endpoint diet (§9.1) reverted: `task_sections`, `contact_groups`,
  and `key_dates` are built and returned again, with no `?include=drawer`
  param. The Solo Agent dashboard's key-dates merge is restored with it.
- The legacy `?expand=` redirect shim is gone: those URLs expand a card again,
  which is what they were always for.

### 16.2 Kept (they were gaps regardless of where the card lands)

Every Phase 1 addition stands on its own merit, because the detail page
needed them whether or not the card kept its drawer:

- **Billing tab** — the workspace had no invoices surface at all.
- **Tracking-dates rail on Timeline** — `plan.tracking_dates` was rendered
  nowhere, and closing/possession now route through the cascade there.
- **Header stats + next-step strip** — the data was already in the aggregate.
- **Delete + Print in a "⋯" menu** — the workspace could not delete a deal.
- **Client-Q&A dot and the `?qa=1` / `?access=1` deep links on People.**
- **`ai_next_step.task_id` + `task_label`** on the plan header (backend).
- **`workspaceUrl()` and the 19 retargeted producers** — a link that is about
  one deal should open that deal's page. `?expand=` still works for the list.

### 16.3 The Transaction Detail redesign (what replaced the removal work)

Standard record-detail shape, verified by screenshot before being called done
(`C:\Projects\_shots\detail-overview.png`, `detail-docs.png`, `detail-ai.png`):

| Before | After |
| --- | --- |
| AI pane fixed at 55% of the page, open by default | A 400px panel docked right, **closed by default**, opened from a header "Ask AI" button, remembered per user |
| Sections inside a bordered card, inside a grid, inside a padded body | ONE content column (max 1180px) on the page background; tabs live on the header surface |
| Landed on Timeline — a plan editor before any orientation | Lands on **Overview**: Needs you · Key dates · Progress · People, each handing off to its tab |
| Nine tabs including Compliance | Seven (+Email/Agent with the flag). Compliance became the **Checklist view of Documents**; `?tab=compliance` still resolves |
| Header: breadcrumb, identity, stats, posture, next-step strip stacked | Breadcrumb, identity + stage, one facts line, posture, then tabs; the next action moved into the body where the eye lands |

### 16.4 Verification after the correction

Frontend: TransactionWorkspace 19/19, AgentWorkspace 9/9, plus
ComplianceAddDocument / WizardFlow / AuthFlow / ClientStaff /
transactionLinks / DealBriefBand 97/97. `tsc`, `eslint --max-warnings=0`, and
`vite build` clean. Backend: the touched suites 36/36, ruff clean.

Test contracts that changed with the design, each updated deliberately: the
default tab is Overview (suites asserting plan rows now name `?tab=timeline`),
and the assistant starts closed (the agent suite opens it, and a new test
pins the closed default and the one-click open).

### 16.5 The lesson worth keeping

Two surfaces overlapping is not automatically duplication. Before removing
one, name the question each answers; if the questions differ, the overlap is
convenience, not redundancy. The correct target here was the surface that was
hard to use, not the one that was fast.

### 16.6 Header simplification (second review pass, same day)

The redesigned page was reviewed again: the top was still "too complex and
confusing". It was — five stacked rows, and the action cluster mixed a
progress *chart* with buttons:

| Was | Now |
| --- | --- |
| Breadcrumb row with the actions right-aligned against it | Breadcrumb alone; actions moved down to sit beside the title, which is the real anchor |
| A `%` label + progress bar wedged between the status and menu buttons | Progress is a fact in the facts line ("56% complete"); the bar lives on the Overview tab's Progress panel, where it already existed |
| A three-way Manual / Assisted / Autopilot segmented control plus "3 handled today · 2 need you" on its own row | One chip ("⚡ Assisted ▾") in the action cluster; the choices, their captions, and the handled/needs-you line live inside its menu |
| Address on one line, then four stats in mixed sizes and colours | ONE facts line: address · Closes Jul 28 (6 days) · $485,000 · 2 overdue · 56% complete — same size, same muted colour, one separator, one accent |
| Five rows before the tabs | Three: breadcrumb, identity + actions, facts |

The action cluster is now four controls of identical shape and height, which
is what makes a header read as professional rather than assembled. Header
height dropped roughly 55px, and nothing was removed from the product — the
posture control and the progress number are both still one glance or one
click away.

Honesty note: the progress fact renders only when the deal HAS task totals.
The old header computed `Math.max(total, 1)` and showed "0% complete" for a
deal with no tasks; the facts line omits it instead.

Verified at 1600px and 1024px (`C:\Projects\_shots\detail-header-v2.png`,
`detail-header-narrow.png`): the identity/actions row holds one line at both
widths, and below xl the "Ask AI" button gives way to the Agent tab.
