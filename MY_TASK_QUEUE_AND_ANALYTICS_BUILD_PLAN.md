# My Task Queue & Analytics — Definitive Build Plan

**Status:** Plan only (no source changes). Authoritative build spec for the two pages.
**Author:** Engineering review, 2026-06-03.
**Revision:** Rev B (2026-06-03) — corrected after a code-grounded plan review. See **§0.1 Review corrections** for what changed and why; the corrections are folded into the body below.
**Pages in scope:** `My Task Queue` and `Analytics`.
**Design comps:** `VE-Workflow-MyTaskQueue.html`, `VE-Intelligence-Analytics.html`.
**Spec sections:** `FRONTEND_UI_WORKFLOW_LOGIC.md` §5.1 (Task Queue), §6.2 (Analytics).

---

## 0. Why earlier plans broke during testing — and what is different here

Previous drafts were written from the design comp alone. They assumed the
backend already returned what the comp draws. It does not. When a real-estate
tester clicked through, the workflow stalled because the data behind a control
did not exist, was a stub, or did not agree with the number shown elsewhere.

This plan is built from a *line-by-line* read of **both comps, the workflow-logic
spec, the live backend routes, the task/transaction data models, and the existing
frontend data layer.** Its core discipline is one rule:

> **No control ships until its data source is real, tested in the running app,
> and consistent with every other place the same number appears.**

Concretely, this plan fixes the four root causes found in the current code:

| # | Root cause found in code | Consequence in testing | Fix in this plan |
|---|--------------------------|------------------------|------------------|
| 1 | Both pages are `ComingSoonPage` stubs (`TaskQueuePage.tsx`, `AnalyticsPage.tsx`). | Nothing to test. | Full build, phased. |
| 2 | No `GET /tasks/queue` endpoint; `GET /tasks` returns flat rows with no transaction name, client name, contacts, or priority. | Cards render blank/"undefined"; grouping impossible. | New **`GET /tasks/queue`** enriched, grouped endpoint (§A2). |
| 3 | Priority (Critical/Attention/On-track) and task type (Document/Comm/Milestone/Admin) are **not stored fields**; and the AI briefing classifies **deals, not tasks** (`compute_stage_pill`). | Per-page invented priority disagreed with `/tasks/summary`; binding a *task* badge to *deal* counts can never reconcile. | **One task-level classifier** (extends `/tasks/summary`) drives the queue groups + sidebar task badge; the deal-level briefing is kept separate and only supplies the focus sentence (§A2.3, §C). |
| 4 | Analytics backend `profile-report` has a real bug (`avg_days_to_close` always `0`) and three stub fields; no storage for goals, referral source, comms, or response time. | KPIs showed 0/blank or were back-filled with mock data (violates "no demo data"). | Per-metric **data-source decision matrix** (§B2): build it, defer it honestly, or lock it behind Pro — never fake it. |

**Design-honesty rule (Jake, recorded):** never render sample/mock data on a
real authenticated surface. Where a metric has no data yet, show an honest
empty/zero state or a Pro lock — not a fabricated number. (See
`no-demo-data-without-real-data`.)

### 0.1 Review corrections (Rev A → Rev B)

A code-grounded review of Rev A found and fixed the following — each was a real
workflow/logic error that would have broken a tester walk-through:

- **C1 — Briefing counts are deal-level, not task-level (MAJOR).** `GET /dashboard/ai-briefing` classifies *transactions* (it runs `compute_stage_pill()` per deal and counts deals — `dashboard.py:528-541`), **not** tasks. Rev A told the Task Queue to bind its three *task* group counts and the sidebar *task* badge to the briefing's *deal* counts "so they agree" — they never could (a deal-level "2 critical" ≠ "2 critical tasks"). **Fix:** the Task Queue's groups + badge are computed by a **task-level** classifier (an extension of `GET /tasks/summary`); the deal-level briefing is reused **only** for the `suggested_focus` sentence and is labelled as deal context. See §A2.1, §A2.3, §A5, §C.
- **C2 — The `/profile` redirect is NOT broken.** It navigates to `` `${ROUTES.ANALYTICS}?scope=me` `` → `/reports?scope=me`, which **is** mounted (`App.tsx:449-452`). Rev A wrongly called it a dead link. **Fix:** the only issue is cosmetic (path string `/reports` vs the label "Analytics"); standardizing to `/analytics` is *optional* and must also move the redirect/sidebar/deep-links. Reuse the **existing** `?scope=me` param for personal scope. See §B1.
- **C3 — Goals/layout persistence is `PATCH /users/me`, not PUT.** The user model has `profile_settings_json` and `PATCH /users/me` exposes a `profile_settings` partial-merge entry point (`users.py:338-383`). **Fix:** store goals + layout order under `profile_settings_json` via `PATCH /users/me { profile_settings: {...} }`. See §B3, §B4.
- **C4 — Existing task serializers drop `completion_method`/`assigned_to`.** `_task_to_response[_from_row]` omit both fields (and the frontend `Task` type omits them), even though the DB + `TaskResponse` schema have them. **Fix:** the new `/tasks/queue` endpoint must select/surface them explicitly (type-derivation and "assigned-to-me" depend on them); also fix the shared helpers + FE type. See §A2.1, §A2.4, §A8.
- **C5 — Two spec features were missing.** Added the **vendor-cart** grouping (spec §5.1; backend `GET /tasks/vendor-carts` already exists — one email to one vendor across deals = high convenience) and the Analytics **chart→table drill-down + supporting table** (spec §6.2). See §A2.2, §A4, §B2, §B4.
- **C6 — Reuse find.** `compute_stage_pill()` already yields the deal health pill (Critical / Needs Attention / In Inspection / On Track) — reuse it for the Analytics **Active pipeline** status column instead of inventing logic. See §B2, §B3.

### 0.2 Fidelity to Jake's design comps (Rev B → Rev C)

**The two comps are Jake's foundational requirements** — every affordance he drew
is a requirement, not a suggestion (`ve-design-comp-fidelity`: reproduce every
element; don't trim affordances without flagging). A pass made *specifically*
against the comps found places where Rev A/B followed the written **spec** instead
of Jake's **comp**, or under-specified. All are now folded into the body:

- **F1 — Export is PDF.** Jake's Analytics topbar button reads **"Export PDF"**; Rev A/B silently swapped it for "CSV first, PDF later." Corrected: primary export = **PDF** (the button as drawn); CSV is an optional secondary. §B1/§B2/§B4.
- **F2 — Period control = Jake's quarter model.** Jake's period bar is **Q1–Q4 tabs + a year selector (2024–2026) + "Full Year YTD" + a "Compare to prior period" checkbox** — not the spec's generic "Month/Quarter/Year/Custom." Rebuilt to Jake's model, mapped onto the backend `period`/custom `start`/`end`. §B1/§B2/§B4.
- **F3 — Compare-to-prior overlay.** The compare checkbox overlays the prior period as ghost bars on the GCI chart (and other comparable charts). Now specified. §B2/§B4.
- **F4 — "Avg GCI per Transaction" KPI** (Jake's 8th KPI card, `$11,607 across 7 deals`) was missing. Added as REAL (GCI ÷ closings). §B2.
- **F5 — Pro coaching section is pinned.** Jake pins "AI Coach Pro — Advanced Analytics" **above** the draggable grid and marks it 📌 Pinned (non-reorderable). Now explicit. §B2/§B4.
- **F6 — AI Insight strip.** Reproduced. Its factual parts ("avg days to close dropped 38→31") are REAL; its forward projection ("on pace for $162K") is rendered as a **clearly-labelled estimate** or routed into the locked forecast — never an unlabelled fabricated figure (honors both Jake's design and the no-demo-data rule). §B2/§B4.
- **F7 — Referral Sources donut is Jake's element.** The best way to honour it is to capture a `lead_source` on the transaction so the donut becomes REAL; until then it's an honest empty, **not removed**. Recommended as a small backend add. §B2.
- **F8 — "Draft run order."** Jake's briefing-strip button (AI task prioritization, spec §5.1) is now an explicit action, wired so it is never a dead button. §A4/§A5.
- **F9 — Two expand variants.** Jake's critical/attention cards use the rich two-column "Notes + AI Assistance" panel; his on-track cards use a compact "Steps" panel. Both reproduced. §A3.
- **F10 — Preserve every affordance, even with no data.** Aligning honesty with fidelity: where data is absent, show an honest state **in place** (e.g. "No AI script yet — draft one"; a Call button that opens the contact to add a number) rather than deleting the element Jake drew. §A5/§C.

---

## 1. What was reviewed to write this plan

- **Comps (full markup + JS):** `VE-Workflow-MyTaskQueue.html` (1964 lines — collapse/expand cards, 4-zone expand panel, priority groups, progress bar, type filter tabs, sort, completed section, Add-Task modal, floating AI, toasts). `VE-Intelligence-Analytics.html` (1183 lines — period bar, goal banner, AI insight, Pro-gated coaching section, 16-block drag-reorder grid of KPI + chart cards, Set-Goals modal, Export, charts as lightweight SVG/CSS).
- **Spec:** `FRONTEND_UI_WORKFLOW_LOGIC.md` §5.1, §5.2 (Task Detail), §6.2.
- **Backend routes:** `app/api/v1/tasks.py`, `analytics_extras.py`, `dashboard.py` (`/ai-briefing`, `/sidebar-kpis`, `/agent/production`), `dashboard_role.py`, `ai.py` (`/suggest-task-approach`, `/parse-nl-task`), `ai_suggestions.py`.
- **Models/enums:** `models/task.py`, `models/transaction.py`, `models/enums.py` (`TaskStatus`, `AutomationLevel`, `TransactionStatus`, `TransactionUseCase`).
- **Frontend data layer:** `hooks/useApiFetch.ts`, `useApiMutate.ts`, `types/api.ts` (`Task`), `utils/constants.ts` (`ROUTES`, `QUERY_KEYS`), existing task components (`components/tasks/TaskList.tsx`, `TaskForm.tsx`, `AiNlpTaskModal.tsx`), shared components (`KpiTile`, `SectionCard`, `EmptyState`, `AskAiFab`, `ContactCard`, `TasksFullViewModal`), `pages/CalendarPage.tsx` (design benchmark).
- **Design system memory:** `calendar-page-design-reference`, `ve-design-comp-fidelity`, `ui-visual-verification-method`, `no-demo-data-without-real-data`.

---

## 2. Design system & shell conventions (applies to both pages)

These pages live **inside the shared internal `AppLayout`** (sidebar + topbar) —
they are *not* standalone portal redesigns, so they use the app shell, not the
comp's own sidebar/topbar chrome. (Contrast with the Client/FSBO portal builds in
`ve-design-comp-fidelity`, which intentionally replace the shell. Task Queue and
Analytics are core internal surfaces and must stay in the shell for nav
consistency.) Reproduce the comp's **content area** faithfully; drop the comp's
sidebar/topbar.

**Tokens (real Tailwind tokens — do not port the comp's raw hex):**
- Surfaces/cards: `rounded-xl border border-ve-border bg-white shadow-soft`.
- Brand: `ve-orange`, `ve-orange-dark`, `ve-orange-xdark` (accent numbers), `ve-sidebar` (#1E3356), `ve-navy` (#06244A).
- Status triads (bg/border/text) for pills: red/amber/green/blue/purple/teal — already standardized in the dashboards; reuse the existing pill/`StatusBadge` patterns.
- Type: serif = `font-serif` (Lora) for titles; mono uppercase eyebrows; `tabular-nums` for stat numbers.
- **Typography gotcha:** `tailwind.config.js` overrides the font scale smaller than stock and sets IBM Plex Sans. The comps are built against stock sizes. **Do not** port the comp's `text-[px]` values blindly — use the app's existing components/sizes (match `CalendarPage`/dashboards), or the proportions will distort. (See `ve-design-comp-fidelity`.)
- **Benchmark:** match `/calendar` (`CalendarPage.tsx`) for header, pills, cards, stat treatment, and empty states (`calendar-page-design-reference`).

**Header pattern (both pages):** breadcrumb (group › page) + serif title + right-aligned controls, on a `border-b` white bar — same as Calendar.

**Verification (mandatory before "done"):** render the real page and screenshot
it with Chrome headless, compare to the comp, fix, re-shoot. Never declare a visual
match from reading markup. (See `ui-visual-verification-method`.)

---

# PART A — MY TASK QUEUE

## A1. Identity, route, access

- **Route:** `ROUTES.TASK_QUEUE` = `/tasks/queue` (already wired in `App.tsx` → `TaskQueuePage`, `RoleRoute` `INTERNAL_ROLES`). ✅ keep.
- **Title / breadcrumb:** "My Task Queue" · `Workflow › My Task Queue`.
- **Allowed roles:** Agent, Transaction Coordinator (Elf), Team Lead, Attorney. Client/FSBO/Vendor never reach it (portal redirects already exist).
- **Deep links:** `?filter=overdue|due_today|upcoming|completed`, `?type=doc|comm|milestone|admin`, `?sort=priority|due|transaction|type`, `?task=<id>` (open that card expanded).

## A2. Data contract — the heart of the fix

### A2.1 New endpoint: `GET /api/v1/tasks/queue`

The comp needs per-task: transaction display name, client name, address, due
state, derived **priority** group, derived **type**, AI reason, and contacts.
`GET /tasks` returns none of the display joins. Build one purpose-made endpoint so
the frontend makes **one call** and renders the whole page (user-convenience +
testability: one source of truth, nothing assembled client-side from three calls).

**Query params:** `assignee=me|team` (default `me`), `filter`, `type`, `sort`,
`search`, `include_completed=bool`, `page`, `page_size`.

**Response shape (`TaskQueueResponse`):**
```
{
  task_counts: {              # TASK-level, computed here (NOT the deal-level briefing)
    critical, attention, track,   # = sizes of the three groups below
    done_today, total_open
  },
  focus: {                    # deal-level context, from GET /dashboard/ai-briefing
    suggested_focus,          # e.g. "2 overdue tasks on 123 Main St"
    updated_at
  },
  progress: { done_today, total_today, pct_complete },
  groups: [
    { key: "critical"|"attention"|"track",
      label, count,
      tasks: [ TaskQueueItem, ... ] }
  ],
  completed_today: [ TaskQueueItem(min) ],   # for the "Completed today" section
  type_counts: { all, doc, comm, milestone, admin }
}
```

**`TaskQueueItem`:**
```
id, name, description, notes,
status, due_date, completed_at, sort_order,
priority,            # derived: "critical" | "attention" | "track"  (A2.3)
type,                # derived: "doc" | "comm" | "milestone" | "admin" (A2.4)
due_state,           # "overdue" | "due_today" | "due_soon" | "on_track"
due_label,           # e.g. "Due 1:00 PM today", "Due Mar 20 — closing the next day"
transaction_id, transaction_name, transaction_address,
client_name,
closing_date, days_to_close,
ai_reason, ai_confidence, source,
contacts: [ { name, role, hint, phone?, email?, contact_id? } ],
target               # vendor, if any
}
```

`transaction_name`/`client_name`/`contacts` come from the existing transaction +
`transaction_parties`/`contacts` tables (the same data the Active Transactions
drawer already uses). Do the joins server-side — do **not** make the client fetch
each transaction.

**Must surface `completion_method` + `assigned_to` (C4).** The existing
`_task_to_response[_from_row]` helpers drop both fields, and the FE `Task` type
omits them — yet the type classifier (§A2.4) and the "assigned-to-me" filter
depend on them. The new endpoint must `select` and return them explicitly; also
patch the shared helpers + FE `Task` type so they stop silently nulling.

**"Assigned to me" semantics (logic fix):** filter `tasks.assigned_to == me`;
for solo agents whose tasks predate assignment, fall back to
`transactions.created_by == me`. `assignee=team` (Team Lead/Admin only) returns
the whole team with an added `assignee_name`/`assignee_avatar` per item.

> **Counts are TASK-level here.** `task_counts` and the three group sizes are
> computed by the task-level classifier (§A2.3), which is an extension of
> `GET /tasks/summary` — **not** the deal-level `GET /dashboard/ai-briefing`
> (`critical_count` there counts *deals*). Re-use the briefing only for the
> `focus.suggested_focus` sentence. Conflating the two is corrected item **C1**.

### A2.2 Endpoints reused as-is (no change)
- `PATCH /api/v1/tasks/{id}` — complete / reschedule (`due_date`) / reassign (`assigned_to`) / skip (`status: Skipped`). Already sets `completed_at`, audits, and emits events.
- `POST /api/v1/tasks` — Add Task (manual). Already authorized for Agent/TC/Lead/Admin.
- `POST /api/v1/ai/suggest-task-approach` → `{ approaches: [{ description, suggested_method, rationale }] }` — powers the expand panel's **"How to complete this task"** + AI assistance copy.
- `POST /api/v1/ai/parse-nl-task` → `ParsedTaskDraft` — powers "type a sentence to add a task" (already wired in `AiNlpTaskModal.tsx`).
- `GET /api/v1/dashboard/ai-briefing` → the navy **AI briefing strip** *focus sentence only* (`suggested_focus`). Its `critical_count/needs_attention_count/on_track_count` are **deal** counts — do not show them as task numbers (C1).
- `GET /api/v1/dashboard/sidebar-kpis` → sidebar portfolio mini-stats (shell already renders these).
- `GET /api/v1/tasks/vendor-carts` → **"Group by vendor" view** (spec §5.1). Already returns tasks grouped by `target` (vendor) across transactions with overdue counts. Powers the convenience flow: follow up *every* task for one vendor in **one** email. Exposed as a grouping mode in the controls bar (C5).
- `POST /api/v1/tasks/similar` — dedupe hint in the Add-Task modal (optional, nice-to-have).

### A2.3 Task-level priority classifier (Critical / Attention / On-track)

Add **one task-level classifier** and use it in exactly two places: the new
`/tasks/queue` endpoint and the refactored `GET /tasks/summary`. It drives the
three group headers, the progress stats, and the sidebar **task** badge — which
are therefore always mutually consistent. Deterministic rule (per task):

- **Critical** = not completed AND ( `due_date < today` (overdue) OR (`due_date == today` AND parent transaction `closing_date` within 7 days) ).
- **Attention** = not completed, not critical, AND ( `due_date in {today, tomorrow}` OR a drift flag is set (e.g. no comms logged in 72h, blocking a milestone) ).
- **On-track** = not completed, due later than tomorrow.
- **Done today** = `status == Completed` AND `completed_at::date == today`.

**Manual override (resolves a comp contradiction).** The Add-Task modal exposes a
Priority field, but a purely-derived priority would silently ignore the user's
choice (set "Critical", see "On track"). So: the Priority field **defaults to
"Auto (by due date)"** (no data entry needed — honors §convenience), and a user
who explicitly picks a level stores `metadata_json.priority_override`; the
classifier checks the override **first**, else derives. This keeps the comp's
affordance without the "my choice was ignored" bug. (No new column — reuse the
existing `metadata_json`.)

> **Do NOT reuse `compute_stage_pill` / `GET /dashboard/ai-briefing` here (C1).**
> That classifier is **deal-level** — it labels whole transactions and counts
> *deals*, not tasks. The briefing strip on this page reuses it only for the
> one-line `suggested_focus` ("2 overdue tasks on 123 Main St"), which is itself
> derived from task-overdue counts, so it stays consistent with the groups. The
> deal-level pill **is** correctly reused on the *Analytics* pipeline table
> (§B2/§C6), where deal-level is what's wanted.

(This is an evolution of the existing `GET /tasks/summary` overdue/due_today/
upcoming buckets — extend that one function, keep it in one place.)

### A2.4 Type classifier (Document / Communication / Milestone / Admin)

Derive from fields already on the task; precedence order:
1. `milestone_label` present → **milestone**.
2. `completion_method in {e_signature, document_*}` OR name matches document verbs (upload/send/sign/disclosure/amendment/title/HOA docs) → **doc**.
3. `completion_method in {phone_call, email, sms}` OR name matches contact verbs (call/follow up/check-in/schedule/confirm with) → **comm**.
4. else → **admin**.

Persist the resolved value on write (set a `category` column or store under
`metadata_json.category`) so the type tab counts are stable and don't re-flip
between requests. Until persisted, derive on read with the rule above — but the
rule must be identical everywhere.

## A3. Component hierarchy (maps 1:1 to the comp's content area)

```
TaskQueuePage
├─ TaskQueueHeader            breadcrumb · "My Task Queue" + total pill · Export · (Team/My toggle for leads)
├─ AiBriefingStrip           navy gradient; suggested_focus; "Updated N min ago"; "Draft run order"
├─ QueueProgressBar          4 clickable stat buttons (Critical/Attention/On-track/Done today) + progress fill
├─ QueueControls             type filter tabs (All/Documents/Communication/Milestones/Admin) · Group toggle (Priority | Vendor) · Sort select · Show completed · "+ Add task"
├─ TaskGroup (×3: critical, attention, track)
│   └─ TaskCard (collapsed row → expand panel)
│       ├─ Collapsed row     row-checkbox · title · type badge · priority pill · txn·address · due label · chevron
│       └─ ExpandPanel (4 zones)
│           ├─ Zone 1 "How to complete"   Notes + AI Assistance (drafts/scripts) + primary CTA + Mark-complete row
│           ├─ Zone 2 "Contacts"          contact rows with Call / Email buttons
│           ├─ Zone 3 "Reschedule/snooze" date input + snooze chips
│           └─ Zone 4 footer              "Created by…" meta + "Open <txn> transaction →"
├─ CompletedSection          collapsible "Completed today (N)"
├─ EmptyState                honest, per filter
├─ AddTaskModal              manual add (+ "type a sentence" AI path)
└─ AskAiFab                  existing floating AI assistant (reuse shared component)
```

**Two expand variants (F9 — reproduce both).** Jake draws Zone 1 two ways:
- **Rich variant** (critical/attention tasks): a two-column **Notes + AI Assistance** panel — the AI box has a title ("Script ready", "Document pre-verified by AI"), a paragraph, and chip actions (Draft email / Get script / Preview document / Use draft / Send this / Edit first), then a **contextual primary CTA** ("Open file & send amendment", "Call Karen Moss now", "Attach disclosure now"), then the Mark-complete row.
- **Compact variant** (on-track tasks): a single **"Steps"** block + one primary CTA + Mark-complete row.

The primary CTA label/action is **task-specific**, driven by `completion_method` /
the AI `suggested_method` (call → "Call X now"; e_signature → "Send via DocuSign";
upload → "Attach now"; review → "Open checklist"). Zones 2–4 are identical across
both variants.

Reuse: `ContactCard`/contact-row pattern, `StatusBadge`, `EmptyState`, `AskAiFab`,
`TaskForm` (inside Add-Task modal), `AiNlpTaskModal` (the NL add path).

## A4. Interaction & workflow spec — every click maps to a real call

| User action | UI behavior | Backend call | Consistency / side-effects |
|---|---|---|---|
| Click row checkbox | Optimistic check; row dims, then collapses; counts + progress + sidebar badge update | `PATCH /tasks/{id}` `{status:Completed}` | On failure roll back + toast. Moves to "Completed today". |
| Click anywhere on row (not checkbox/button) | Expand/collapse the card (only one open at a time) | — (data already loaded) | — |
| Expand → "Mark task as complete" | Same as checkbox, with Undo link | `PATCH /tasks/{id}` | Undo = `PATCH {status:Pending}` (clears `completed_at`). |
| Click a priority stat (Critical/Attention/On-track) | Filter list to that group; toggles off on re-click | client-side filter of loaded data | Clears the type-tab selection (mutually exclusive, matches comp). |
| Click "Done today" stat / "Show completed" | Reveal Completed section | `include_completed=true` (or already in payload) | — |
| Type filter tab | Filter by `type` | client-side | Clears priority filter. |
| Sort select | Re-order (Priority/Due/Transaction/Type) | client-side (server `sort` for deep-link) | — |
| Search box | Filter by title/transaction/contact | client-side; server `search` for large queues | — |
| Reschedule date / snooze chip | Inline; toast "Task rescheduled" | `PATCH /tasks/{id}` `{due_date}` | May re-bucket the task's priority → refetch queue. |
| "+ Add task" | Modal: description, transaction (select), type, priority(optional), due date, notes — **or** one-line NL box | `POST /tasks` (or `POST /ai/parse-nl-task` → confirm → `POST /tasks`) | New task appears in the right group. Dedupe via `POST /tasks/similar`. |
| Contact "Call"/"Email" | `tel:`/`mailto:` (and log via comms if a contact_id exists) | optional `POST /communication-logs` | Buttons always present (F10); when no number/email, the button opens the contact to add one rather than being removed. |
| "Draft email"/"Get script" (AI assist) | Opens AI draft using approach text | `POST /ai/suggest-task-approach` | Reuse AI Suggestions plumbing. |
| **"Draft run order"** (briefing strip, F8) | AI proposes the order to clear today's tasks; applies it as a one-click sort/highlight of the queue | AI panel; v1 = deterministic "critical → attention → soonest due" ordering so it is **never a dead button** (spec §5.1 "AI can suggest task prioritization order") | Non-destructive — re-orders the view only. |
| "Open <txn> transaction →" | Navigate `/transactions/active?highlight=<txn_id>` | — | Matches spec §5.1 outbound nav. |
| "Reassign" (Team Lead, team view) | Dropdown of team members | `PATCH /tasks/{id}` `{assigned_to}` | Task leaves "My" queue; notifies assignee. |
| "Skip task" | Confirm popover | `PATCH /tasks/{id}` `{status:Skipped}` | Goes to collapsed Skipped area; does not unblock dependents. |
| **Group toggle → "Vendor"** | Shows vendor-targeted tasks grouped by vendor (one stack per vendor, overdue count per vendor); non-vendor tasks are out of this view by design | `GET /tasks/vendor-carts` (open tasks with `target` set) | Convenience flow: "Email all" drafts one follow-up covering every task for that vendor across deals. |
| Export | Download CSV of the current queue | client-side CSV from loaded data (PDF later) | — |

## A5. AI integration points
- **Briefing strip:** the headline numbers ("14 open tasks", "2 critical") come from `task_counts` (task-level, §A2.1). The `suggested_focus` sentence comes from `/dashboard/ai-briefing` (which derives it from task-overdue counts, so it stays consistent). The strip may add deal context ("across 6 transactions") but must **label deal vs task** so a tester is never confused by a "2 deals" number sitting next to a "14 tasks" number (C1). If the focus text is unavailable, fall back to a deterministic sentence built from `task_counts` — never blank, never fabricated specifics.
- **Per-task "How to complete":** `POST /ai/suggest-task-approach` with `{task_name, completion_method, transaction_id}`. Render `approaches[].description` as Notes and `rationale` as the AI-assist copy; map `suggested_method` to the primary CTA label.
- **Confidence:** show `ai_confidence` as a small pill only on AI-sourced tasks (`source != "template"`).
- **"Draft run order"** (briefing strip, F8): proposes today's clearing order; v1 applies a deterministic critical→attention→soonest-due sort so it always does something real.
- **Honesty + fidelity together (F10):** honor `no-demo-data` *without deleting Jake's affordances*. If there's no AI output, **keep the AI Assistance box in place** with an honest state ("No AI script yet — Draft one") and show the manual Notes (`task.notes`) — do **not** remove the box. Likewise keep Call/Email present; if a contact has no number, the button opens the contact to add one (disabled-with-reason, not absent).

## A6. Loading / empty / error states
- **Loading:** 8–10 row skeletons under group headers (spec §5.1).
- **Empty (no open tasks):** soft orange ✓ circle + "You're all caught up." + "New tasks appear here as deals progress." (honest; matches Calendar empty-state style.)
- **Empty (filter hides all):** "Nothing in this view." + button to clear the filter.
- **Error:** inline `ErrorAlert` with retry.

## A7. Backend work items (Task Queue)
1. **`GET /api/v1/tasks/queue`** (new) — enriched, grouped, role-scoped; shape in A2.1. Must `select`/return `completion_method` + `assigned_to` (C4).
2. **Task-level classifier service** — priority (A2.3) + type (A2.4); used by the queue endpoint **and** the refactored `GET /tasks/summary`. **Do not** route it through `/dashboard/ai-briefing` — that one stays deal-level (C1).
3. **Fix shared serializers** — add `completion_method`/`assigned_to` to `_task_to_response[_from_row]` (currently dropped, C4) so other task surfaces are consistent.
4. **Contacts join** — surface each task's transaction parties/contacts (reuse existing party reads).
5. (Optional) persist resolved `category` on task create/update to stabilize type-tab counts.
6. No new endpoints for complete/reschedule/reassign/skip/add/vendor-group — all exist (`PATCH /tasks/{id}`, `POST /tasks`, `GET /tasks/vendor-carts`).

## A8. Frontend work items (Task Queue)
1. Replace `TaskQueuePage` stub with the real page (A3).
2. New `useTaskQueue` hook (there is currently **no** `useTasks*` hook) wrapping `useApiFetch` for `/tasks/queue`, plus `useApiMutate` for PATCH/POST with optimistic updates + `QUERY_KEYS` invalidation (mirror `TaskList.tsx`'s optimistic pattern).
3. Components: `AiBriefingStrip`, `QueueProgressBar`, `QueueControls`, `TaskGroup`, `TaskCard` (collapsed + 4-zone expand), `CompletedSection`, `AddTaskModal` (wrap existing `TaskForm` + `AiNlpTaskModal`).
4. Wire `?filter/type/sort/task` deep-links; add the Priority|Vendor group toggle (Vendor mode → `GET /tasks/vendor-carts`).
5. Sidebar badge: bind to `task_counts.total_open` (the task-level source — **not** the deal-level briefing) so the badge equals the sum of the page's groups.

## A9. UI acceptance script (a real-estate tester can run this end-to-end)
1. Open **Workflow › My Task Queue**. → Briefing strip, three priority groups, progress bar, and a sidebar badge that equals the **sum of the three group counts** (task-level). Any deal-level number in the strip (e.g. "across 6 transactions") is clearly labelled as deals, not tasks.
2. Click **Critical** stat. → Only critical tasks show; click again → all return.
2b. Switch **Group → Vendor**. → Tasks regroup by vendor with an overdue count per vendor; "Email all" drafts one follow-up per vendor.
3. Click a task row. → Expands to the 4 zones; "How to complete" shows real notes/AI text; contacts have working Call/Email only where a number/email exists.
4. Click the row **checkbox**. → Task checks, slides to "Completed today", counts + badge drop by one. Click **Undo**. → It returns.
5. Open a task → **Snooze / change date**. → Toast confirms; if it changes urgency the task moves groups after refresh.
6. **+ Add task** → fill description + pick a transaction + due date → **Add to queue**. → New card appears in the correct group. Try the one-line NL box too.
7. Type in **search**, switch **type tabs**, change **sort**. → List filters/reorders with no blanks or "undefined".
8. Click **Open <txn> transaction →**. → Lands on Active Transactions with that deal highlighted.
9. **Empty path:** complete everything in a filter → honest empty state, not a fake row.

---

# PART B — ANALYTICS

## B1. Identity, route, access

- **The page already works at `ROUTES.ANALYTICS = '/reports'`** (mounted in `App.tsx`), and the `/profile` redirect navigates to `` `${ROUTES.ANALYTICS}?scope=me` `` → `/reports?scope=me`, which **is** mounted. **So there is no broken link** (corrects Rev A's C2 error). The only mismatch is cosmetic: the path string is `/reports` while the sidebar/spec/comp call it "Analytics".
- **Decision (optional, low priority):** standardizing the path to `/analytics` is a *nice-to-have*, not a fix. If done, it must move the constant **and** the `/profile` redirect, the sidebar link, and any `?scope=me` deep-links together; keep `/reports` as a back-compat redirect. **Do not block the build on this** — build the page at the existing route first.
- **Reuse the existing `?scope=me` param** for personal scope (it already drives the "per-user reports tab"); add `?scope=team` / `?agent_id=` for the team/per-agent views rather than inventing new params.
- **Title / breadcrumb:** "Analytics" · `Intelligence › Analytics`.
- **Allowed roles:** Agent, TC (Elf), Team Lead, Admin, Attorney (already `INTERNAL_AND_ATTORNEY`). Team Lead/Admin get an agent filter; Admin gets tenant-wide.
- **Top controls = Jake's comp, not the generic spec (F1–F3):**
  - **Period bar:** **Q1–Q4 quarter tabs** (the current quarter carries a "YTD" badge) + **year selector** (2024–2026) + **"Full Year YTD"** + a **"Compare to prior period"** checkbox. Build it exactly as drawn — *not* the spec's "Month/Quarter/Year/Custom." Map a chosen quarter+year to the backend via custom `start`/`end` (or extend `_period_range` to accept an explicit `quarter`+`year`); "Full Year YTD" → `period=year`; compare → fetch the prior period too.
  - **Topbar action = "Export PDF"** (Jake's button label). Primary export is **PDF**; CSV is an optional secondary, not a substitute.

## B2. Data-source decision matrix — **the antidote to fake KPIs**

Every comp block is classified: **REAL now**, **BUILD (small backend add)**,
**DEFER (honest empty state)**, or **PRO (locked, not faked)**. Build only REAL +
BUILD for v1; render DEFER as honest empty states; keep PRO locked exactly as the
comp already shows (blurred + upgrade CTA — that is *intended*, not mock data).

| Comp block | Data today | Decision | Source / action |
|---|---|---|---|
| GCI (period) | `agent/production.pending_gci`, closings; `profile-report.revenue_trend` | **REAL** | purchase_price × commission pct (already in `dashboard_common`). |
| **Avg GCI per Transaction** (KPI, F4) | derivable | **REAL** | GCI ÷ closings count — Jake's 8th KPI card; was missing from Rev A/B. |
| Pipeline value | `agent/production.pending_volume`, active count | **REAL** | reuse production snapshot. |
| Closings (count) | `profile-report.closings_count`, `closings_by_month` | **REAL** | as-is. |
| GCI by month (bar) | `profile-report.revenue_trend` | **REAL** | as-is. |
| Transaction volume by month (bar) | `closings_by_month` (+ split by `representation_type`) | **BUILD** | add buyer/listing split (field exists on transaction). |
| Transaction type distribution (donut) | `profile-report.transaction_type_distribution` | **REAL** | as-is (`use_case`). |
| **Avg days to close** | `profile-report.avg_days_to_close` is **hard-coded 0 (bug)** | **BUILD (bugfix)** | compute `closing_date − contract_acceptance_date` per closed deal; populate the list that's currently never filled. |
| Days-to-close per transaction (bar) | none | **BUILD** | same computation, per-deal series. |
| On-time close rate (KPI + line) | derivable: `closing_date ≤ scheduled` | **BUILD** | compare actual vs scheduled close; needs the scheduled date captured at contract (store `metadata_json.scheduled_closing_date` or use first closing_date). |
| Task completion rate (KPI + bar) | `profile-report.task_completion_rate` (real); on-time/late/missed split is new | **REAL + BUILD** | KPI real now; the on-time/late/missed monthly bars need `completed_at` vs `due_date`. |
| Overdue tasks (KPI) | `GET /tasks/summary.overdue` | **REAL** | reuse summary. |
| Active pipeline table (close date, value, doc progress, status) | transactions + closing-checklist % | **BUILD (reuse C6)** | join active transactions + checklist completion %; the **status pill reuses `compute_stage_pill()`** (the deal-level classifier from the AI briefing) — do not invent At-Risk/Docs-Missing logic. |
| Avg client response time (KPI) | no source (no inbound→reply timing captured) | **DEFER** | honest "Not enough data yet" until comms timing is tracked. Do **not** invent 9.2h. |
| Referral sources (donut) — *Jake's donut, F7* | no `lead_source` field | **DEFER → recommend BUILD** | best honoured by adding a `lead_source` on the transaction so the donut becomes REAL; until then an honest empty — **never** the comp's mock slices. |
| AI Insight strip (F6) | period deltas (real) + forward projection | **REAL + labelled estimate** | factual deltas (e.g. avg days 38→31) are REAL; "on pace for $162K" renders as a clearly-labelled *estimate* or routes to the locked forecast — never unlabelled. |
| Client communication heatmap | `communication_logs` exist, but per-client-per-week rollup isn't built | **DEFER or BUILD** | BUILD only if comms volume is real for the tenant; else honest empty. **Never** the comp's mock 5×12 grid. |
| AI suggestion acceptance rate | `profile-report.ai_suggestion_acceptance_rate` is **stub 0.0**; real accept/dismiss exist in `ai_suggestions` | **BUILD** | compute from `accept`/`dismiss` counts (data already recorded). |
| Deal drift reasons (h-bar) | `profile-report.drift_reasons` is **stub []** | **BUILD or DEFER** | compute from drift flags if present; else honest empty. |
| Goal banner + Set-Goals modal | **no goal storage anywhere** | **BUILD** | store targets under `users.profile_settings_json.analytics_goals` (no new table) via **`PATCH /users/me { profile_settings: {...} }`** (the existing partial-merge entry point — C3). |
| Supporting data table + chart drill-down | transactions list | **BUILD** | spec §6.2: a sortable transaction-level table below the charts; clicking a bar/segment filters it (C5). |
| AI Coach Pro: Forecast / Funnel / Benchmarking | intentionally gated | **PRO (pinned + locked, F5)** | keep blurred + "Unlock" CTA exactly as comp; **pinned above the draggable grid and non-reorderable** (📌 Pinned). Honest (a real locked feature), not mock data. |
| Period bar (Q-tabs + year + YTD + Compare) (F2/F3) | n/a | **BUILD (controls)** | Jake's period model; Compare overlays the prior period as ghost bars on the GCI (and comparable) charts. |
| Export (F1) | n/a | **BUILD** | Jake's button = **"Export PDF"** → PDF; CSV optional secondary. |
| Customize-layout drag reorder | comp uses localStorage | **REAL (client)** | persist block order in `profile_settings_json` via `PATCH /users/me` (cross-device); localStorage only as v1 fallback. |

**Backend bug to fix (called out explicitly):** in `analytics_extras.py`
`get_profile_report`, `days_to_close` is declared but **never appended to**, so
`avg_days_to_close` is always `0.0`. Populate it for each closed transaction with a
valid `contract_acceptance_date` and `closing_date`.

## B3. Backend work items (Analytics)
1. **Fix `avg_days_to_close`** (B2 bug) and add per-deal days-to-close series.
2. **Extend `GET /analytics/dashboard`** (or add `GET /analytics/overview`) to return the v1 chart set in one call: KPI row, GCI-by-month, volume split, type donut, on-time line, task-rate bars, active-pipeline table, AI-acceptance, plus `goals` and per-metric `available: bool` flags so the UI can show honest empty states without guessing.
3. **Goals storage:** read/write GCI (annual+quarterly), txn count, on-time %, task-completion %, response-time target under `users.profile_settings_json.analytics_goals` via **`PATCH /api/v1/users/me { profile_settings: { analytics_goals: {...} } }`** — the existing partial-merge entry point (C3). No new endpoint, no new table.
4. **AI acceptance + drift** from real `ai_suggestions` data (replace the two stubs) or mark `available:false`.
5. **Active-pipeline status** reuses `compute_stage_pill()` (C6); **supporting table** returns transaction-level rows for drill-down (C5).
6. **Role scope:** `agent_id` (Team Lead per-agent), tenant-wide for Admin (already partially supported via `agent_id`/tenant scoping); accept `scope=me|team` aligned with the existing `?scope` param.
7. **Period mapping (F2/F3):** accept an explicit quarter+year (or custom `start`/`end`) so Jake's Q-tab + year selector resolve to a precise window; support a `compare` flag that also returns the immediately-prior period for the overlay.
8. **Add the `Avg GCI per Transaction` figure** (GCI ÷ closings — F4) to the payload.
9. **(Recommended, small) add a `lead_source` field** to the transaction (set at intake) so Jake's **Referral Sources donut becomes REAL** rather than a permanent empty (F7).

## B4. Frontend work items (Analytics)
1. Replace `AnalyticsPage` stub with the real page.
2. `useAnalytics(period, agentId, compare)` hook over `useApiFetch`; refetch on period/agent change.
3. Components: `PeriodBar` (**Q1–Q4 tabs + year select + Full Year YTD + Compare checkbox** — F2), `GoalBanner`, `AiInsightStrip` (F6), KPI cards incl. **`AvgGciPerTxn`** (F4) reusing shared `KpiTile` + sparkline, chart cards (`GciBarChart`, `VolumeBarChart`, `TypeDonut`, `OnTimeLineChart`, `TaskRateBars`, `DaysToCloseBars`, `ActivePipelineTable`), `ProGateSection` (**pinned above the grid, non-draggable** — F5), `SetGoalsModal`, `CustomizeLayout` (drag reorder of the non-pinned blocks only).
3b. **Compare-to-prior (F3):** when checked, fetch the prior period and overlay it as ghost bars on the GCI chart (and other comparable charts); reveal the "Prior period" legend.
4. **Charting:** verify `package.json` first. If a chart lib (e.g. recharts) is **already** a dependency, use it (spec §6.2 suggests recharts). If not, **do not add a heavy dep** — use the comp's lightweight inline SVG/CSS approach (consistent with `KpiTile` sparklines). Decide at build time based on what's already installed.
5. **Honest empties:** any metric with `available:false` (or value 0 because no data) renders the Calendar-style empty state, not a number. Pro blocks render locked.
6. **Supporting table + drill-down (spec §6.2):** a sortable transaction-level table under the charts; clicking a bar/segment filters it to those transactions.
7. **Export = PDF** (Jake's "Export PDF" button — F1); CSV optional secondary. **Customize-layout** persists block order under `profile_settings_json` via `PATCH /users/me` (cross-device; localStorage acceptable only as a v1 fallback — C3).

## B5. Loading / empty / error states
- **Loading:** chart-placeholder skeletons (pulsing rectangles), KPI skeletons.
- **First-run empty (no closed deals):** charts render axes at zero with "Complete your first transaction to see analytics" (spec §6.2) — explicitly allowed honest zero-state.
- **Per-metric DEFER:** "Not enough data yet" tile, never mock.
- **Error:** inline `ErrorAlert` + retry.

## B6. UI acceptance script (real-estate tester)
1. Open **Intelligence › Analytics**. → Period bar, goal banner, KPI row, charts; Pro section visibly **locked** (blurred + Unlock), not fake.
2. Switch quarter (**Q1–Q4**), change the **year** selector, try **Full Year YTD**. → Every KPI and chart reloads for that window; no stale numbers.
2b. Tick **Compare to prior period**. → Ghost bars for the prior period appear on the GCI (and comparable) charts with a "Prior period" legend.
3. Click **Set Goals**, enter an annual GCI, **Save**. → Goal banner progress recomputes; reload page → goal persists.
4. Confirm KPIs match other surfaces: GCI/closings equal the dashboard's production snapshot; overdue equals the Task Queue. (These are deal-level vs task-level by design and are labelled as such — no false equivalence.)
5. Click a **chart bar/segment** → the supporting table below filters to those transactions.
6. **Customize layout** → drag a card → reload → order remembered. The **AI Coach Pro** section stays pinned on top and cannot be dragged.
7. Any "Not enough data yet" tile is honestly empty (e.g. response time / referral) — **no invented numbers**.
8. **Export PDF** (Jake's button) downloads a report that matches the on-screen figures.
9. (Team Lead) switch the **agent filter** → numbers change per agent. (Admin) tenant-wide view loads.

---

# PART C — Cross-cutting requirements

1. **Single source of truth — and never mix the two levels.** There are two distinct families of numbers; keep each internally consistent and **never equate across families**:
   - **Task-level** (open/critical task counts → Task Queue groups, sidebar task badge, the strip's task headline, Analytics overdue-tasks/task-completion) all derive from the **one task-level classifier** (§A2.3).
   - **Deal-level** (critical *deals*, GCI, closings, pipeline value, pipeline status pill → dashboard production snapshot, AI briefing, Analytics pipeline table) all derive from the **deal-level** services (`compute_stage_pill`, production snapshot).
   A tester seeing "14" in one place and "12" in another is the #1 trust-breaker — so each family is wired to a single service, and any place both appear together is **explicitly labelled** ("14 tasks across 6 deals") so the two are never read as one inconsistent number. (This is the corrected C1.)
2. **No demo data, ever, on these surfaces.** Empty = honest empty or Pro-locked. (`no-demo-data-without-real-data`.)
3. **Minimal data entry / mouse-first.** Completing, snoozing, rescheduling, reassigning, filtering, and adding-by-sentence are all 1–2 clicks. Add-Task pre-selects the obvious transaction and defaults type/priority from the description.
4. **Role behavior is explicit, not implicit.** Agent/TC = own tasks / own production; Team Lead = My/Team toggle + per-agent analytics; Admin = tenant-wide; Attorney = legal-relevant tasks + read analytics.
5. **Accessibility & responsive:** task rows → cards on mobile (checkbox stays prominent); charts stack vertically; keyboard: Esc closes modals, Enter submits Add-Task.
6. **Design fidelity verified by screenshot** against each comp before sign-off (`ui-visual-verification-method`).
7. **Reproduce every affordance Jake drew (F10).** The comps are the requirement: build every button, chip, KPI, chart, toggle, and modal field they show (incl. Draft run order, Compare, year selector, Export PDF, Avg GCI per Transaction, the pinned Pro section). Where data is absent, render an honest in-place state (empty / disabled-with-reason / Pro-locked) — never silently delete an element to dodge a "dead button." Flag, don't trim.

---

# PART D — Build sequence (small, independently testable slices)

**Phase 0 — Foundations**
- Fix `avg_days_to_close` bug; add the **task-level** priority+type classifier; fix the `_task_to_response` serializers to include `completion_method`/`assigned_to` (C4). (Each is independently verifiable. The `/reports`→`/analytics` rename is *optional* and explicitly out of the critical path — B1.)

**Phase 1 — Task Queue backend**
- `GET /tasks/queue` (enriched/grouped, surfacing `completion_method`/`assigned_to`) + contacts join; refactor `GET /tasks/summary` onto the same task-level classifier. **Verify via Swagger that the queue group sizes equal the summary buckets** — and that the deal-level briefing is intentionally a *different* number.

**Phase 2 — Task Queue frontend**
- Page shell → groups + cards (collapsed) → 4-zone expand → complete/undo → reschedule/snooze → Add-Task (form + NL) → filters/sort/search → completed section → empty states. Screenshot-verify against comp. Run A9 end-to-end.

**Phase 3 — Analytics backend**
- Extend `/analytics/overview` with the v1 REAL+BUILD metrics + `available` flags + goals read/write. Verify each figure in Swagger against dashboard/summary.

**Phase 4 — Analytics frontend**
- Period bar (**Q-tabs + year + Full Year YTD + Compare** — F2/F3) → goal banner + Set-Goals → KPI row (incl. **Avg GCI per Transaction** — F4) → REAL charts → honest empties for DEFER → **pinned** Pro-locked section (F5) → customize-layout → **Export PDF** (F1). Screenshot-verify. Run B6 end-to-end.

**Phase 5 — Polish & cross-checks**
- Cross-surface number reconciliation (Part C #1), responsive/mobile, a11y, deep-links, final comp screenshots, `tsc` + `eslint` + `vite build` green.

---

# PART E — Definition of Done

A page is "done" only when **all** hold:
- [ ] Every control on screen triggers a real, tested backend call or a real client action — no dead buttons, no placeholders.
- [ ] Every number is sourced from a real service; shared numbers agree across Task Queue, Analytics, dashboard, and sidebar.
- [ ] No mock/sample data on the authenticated surface; empties are honest; Pro blocks are honestly locked.
- [ ] The non-developer acceptance script (A9 / B6) passes start-to-finish with no broken step.
- [ ] Screenshot of the running page matches the comp's content area (verified per `ui-visual-verification-method`).
- [ ] Loading, empty, and error states all implemented.
- [ ] `tsc`, `eslint`, and `vite build` pass; backend tests for the new endpoints pass.

---

## Appendix — Element → data-source quick map

**Task Queue**
- Progress stats / group counts / sidebar **task** badge → `GET /tasks/queue` `task_counts` (task-level classifier; **not** the briefing — C1)
- Briefing strip *focus sentence* → `GET /dashboard/ai-briefing.suggested_focus` (deal-level; label deal context as such)
- Task cards (name, txn, client, due, contacts, completion_method, assigned_to) → `GET /tasks/queue`
- Group by vendor → `GET /tasks/vendor-carts`
- "How to complete" / drafts → `POST /ai/suggest-task-approach`
- Complete / reschedule / reassign / skip → `PATCH /tasks/{id}`
- Add task → `POST /tasks` (+ `POST /ai/parse-nl-task`, `POST /tasks/similar`)
- Open transaction → `/transactions/active?highlight=<id>`

**Analytics**
- GCI / **Avg GCI per txn** / pipeline / closings KPIs → `GET /dashboard/agent/production` + `GET /analytics/*` (F4)
- GCI-by-month / volume / type donut → `GET /analytics/*` (`revenue_trend`, `closings_by_month`, `transaction_type_distribution`)
- Avg days-to-close / per-deal / on-time → `GET /analytics/*` (after bugfix)
- Task completion / overdue → `GET /analytics/*` + `GET /tasks/summary`
- AI Insight strip → real period deltas; forward projection labelled estimate / locked forecast (F6)
- Period (Q-tabs + year + YTD) + Compare-to-prior → `GET /analytics/*` with quarter/year or custom range + prior period (F2/F3)
- Active pipeline table → active transactions + closing-checklist %; status pill via `compute_stage_pill()` (C6)
- Supporting table + chart drill-down → transaction-level rows (C5)
- AI acceptance / drift → real `ai_suggestions` data (replace stubs) or `available:false`
- Goals + layout order → `users.profile_settings_json` via `PATCH /users/me { profile_settings }` (C3)
- **Export PDF** → client/report render of loaded figures (F1)
- Referral donut → **DEFER → recommend `lead_source` field** to make it REAL (F7)
- Response time / heatmap → **DEFER** (honest empty) until a real source exists
- Forecast / funnel / benchmarking → **PRO**, pinned above the grid (F5)
