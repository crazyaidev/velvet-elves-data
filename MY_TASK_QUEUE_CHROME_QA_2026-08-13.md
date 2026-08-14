# My Task Queue — Chrome QA findings (2026-08-13)

**Page:** Workflow › My Task Queue (`/tasks/queue`)  
**Tester:** platform admin `shyna.elene@minafter.com`  
**Environment:** real Google Chrome (Playwright headed, `channel: "chrome"`), frontend `http://localhost:5173`, backend `http://localhost:8000`  
**Dataset:** 6 Active deals, **203** open tasks (129 critical / 124 overdue / 3 attention / 71 on track), 0 done today. 121 of those tasks sit on deals whose closing date has already passed; every open task had `assigned_to: null`.

Artifacts: `velvet-elves-data/task_queue_qa/artifacts_2026-08-13/` (first pass), `artifacts_2026-08-13_retest/` (after fixes), and `artifacts_2026-08-13_verify/` (implementation verification, 47/47).

---

## 1. Executive summary

The page loaded and the core list worked: briefing, stats, type tabs, search, sort, expand, and the in-app email flow. It was **not** seamless. A 203-row dump with no paging, no export, no team scope, no undo, and several dead or colliding controls made daily work slow and easy to mis-click.

Those functional gaps are **fixed and re-verified in Chrome**. A later headed pass (13 Aug 2026) confirmed **47/47** checks, including the Q-17 mobile names and the extra URL / notes / overdue-alias checks.

| Severity | Found | Status |
| --- | --- | --- |
| High | 6 | Fixed |
| Medium | 8 | Fixed |
| Low / data | 4 | Documented (not queue-render bugs) |

---

## 2. Issues found and resolved

### Q-01 · No Export action
**Severity:** High · **Area:** Header

Spec §5.1 and the Contacts / Active Transactions pattern both have Export. The queue header only had Add task.

**Fix:** **Export CSV** downloads the currently visible rows (respects filters). Chrome retest saved `task-queue.csv`.

### Q-02 · No My tasks / Team tasks toggle for Admin
**Severity:** High · **Area:** Header

`GET /api/v1/tasks/queue?assignee=team` already exists. Admin/Team Lead had no way to switch. The hook was hard-coded to `me`.

**Fix:** Segmented **My tasks / Team tasks** control for Admin and Team Lead. Scope is stored on the URL (`assignee=team`).

### Q-03 · 203 cards rendered with no pagination
**Severity:** High · **Area:** List

Spec §5.1: queues over 100 tasks should paginate or virtualize. Critical alone was 129 rows. The page was sluggish and the real work was buried.

**Fix:** Each priority group shows 20 rows, then **Show N more**. Deep-linked `?task=` still expands a card below the fold by extending that cap.

### Q-04 · “Today’s progress” used every future task as the denominator
**Severity:** High · **Area:** Progress strip

Backend computed `pct_complete = done_today / (total_open + done_today)`. With 203 open and 0 done, the bar was 0% even after clearing real overdue work — on-track future tasks drowned the ratio.

**Fix:** “Today” is overdue + due-today + done-today (129 on this tenant). Completing one overdue item now moves the bar. Empty today-workload is 100%.

### Q-05 · Completing a task had no undo and no error toast
**Severity:** High · **Area:** Checkbox / Mark complete

A mis-click on a 20×20 checkbox completed work with no way back. Failed PATCHes were silent.

**Fix:** Success toast includes **Undo** (8s). Failures show an error toast. Skip is a confirmed action on the expanded card.

### Q-06 · Add task from this page did not land in My Task Queue
**Severity:** High · **Area:** Add task dialog

Manual creates omitted `assigned_to`. For Admin/Team Lead, `assignee=me` keeps tasks assigned to the current user **or** on deals they created. A task on someone else’s deal vanished from the queue that just added it.

**Fix:** Add task assigns to the signed-in user. Chrome retest: `QA Queue 333497` appeared in search, completed, and showed Undo.

### Q-07 · Search had no accessible name
**Severity:** Medium · **Area:** Toolbar

Placeholder-only input. Contacts uses `aria-label="Search contacts"`.

**Fix:** `aria-label="Search tasks"`. Search also matches vendor/target text.

### Q-08 · Stat tile “Critical” collided with the topbar deal chip
**Severity:** Medium · **Area:** Stats vs topbar

Topbar AI briefing: **6 Critical** (deals). Queue: **129 critical** (tasks). `getByRole(button, Critical)` hits the topbar first and navigates off the page. Same trap for a keyboard / voice user.

**Fix:** Queue tiles use `aria-label="{n} Critical tasks"` (and the same pattern for Attention / On track / Done today). Clicking the tile stays on `/tasks/queue?priority=critical`.

### Q-09 · Deep links were ignored
**Severity:** Medium · **Area:** URL

Build plan: `?type=`, `?sort=`, `?task=`, `?filter=overdue|completed`. None were read or written.

**Fix:** Filters, sort, vendor view, team scope, search, and the expanded card sync to the query string. Spec aliases `filter=overdue` → critical, `filter=completed` → done today. Chrome: `?task=` expands the card; `?type=doc` selects Documents.

### Q-10 · Vendor grouping flashed an empty state while loading
**Severity:** Medium · **Area:** Vendor view

`vendorCarts ?? []` treated “not loaded yet” as empty, so users saw “No vendor-assigned tasks right now” before carts appeared.

**Fix:** Skeleton while loading; empty copy only after the response.

### Q-11 · Email completion used `mailto:` as the primary CTA
**Severity:** Medium · **Area:** Expanded card

A prior E2E finding (I-09): `mailto:` leaves the SPA and writes nothing to communication logs. The in-app **Email transaction party** flow already existed on the same card.

**Fix:** Email completion method opens the in-app flow. Contact-row Call/Email `tel:`/`mailto:` stay as one-click to **that person**.

### Q-12 · Done-today rows showed a chevron but did nothing
**Severity:** Medium · **Area:** Done today filter

**Fix:** Row click opens the parent deal (`/transactions/active?highlight=`).

### Q-13 · Transaction name on a card was not a link
**Severity:** Medium · **Area:** Card

Spec: transaction name → Active Transactions highlight. Clicking the name only expanded the card.

**Fix:** The client · address control opens the deal (does not complete or expand).

### Q-14 · Add-task Type/Transaction selects used an empty string value
**Severity:** Medium · **Area:** Add task dialog

Radix Select forbids `value=""`. The type field started as `''`, which breaks the placeholder and can warn in the console.

**Fix:** Transaction uses `undefined` until chosen; type uses `auto`. Notes label is **Notes (optional)** instead of the misleading “How to complete”.

### Q-15 · Complete checkbox was 20×20 and nested in a `role="button"` row
**Severity:** Low · **Area:** A11y

Requirements §9.1 / style guide: 40–48px hit target. Nested interactive elements made keyboard expand unreliable.

**Fix:** 40×40 complete control; separate Expand/Collapse control; no wrapping `role="button"`.

### Q-16 · Type/priority/due labels were 9–11px
**Severity:** Low · **Area:** Typography

Style guide v2: no text below 12px.

**Fix:** Queue card and page chrome use ≥12px for labels, pills, and kickers.

### Q-17 · Mobile Add task had no accessible name
**Severity:** Low · **Area:** Header (viewport 390)

Visible label is `hidden sm:inline`, so a phone user (and the Chrome check) only saw a plus icon with no name.

**Fix:** `aria-label="Add task"` and `aria-label="Export CSV"` on the header actions. Found on the 390px pass; patched immediately after.

---

## 3. Chrome retest (after fixes)

| Check | Result |
| --- | --- |
| Login as platform admin | Pass |
| Breadcrumb, title, Add task, Export CSV, My/Team toggle | Pass |
| API counts 203 open / 129 critical; progress total_today **129** | Pass |
| Critical tile stays on `/tasks/queue?priority=critical` | Pass |
| Done today, search (hit + empty + a11y name), sort, Draft run order | Pass |
| Show more pagination on the 129-row critical group | Pass |
| Expand / reschedule / email flow / skip / 40×40 checkbox | Pass |
| Transaction label → deal highlight | Pass |
| Export `task-queue.csv` | Pass |
| Add task validation, create, appears in queue, complete + Undo | Pass |
| Vendor grouping (no empty-state flash) | Pass |
| `?task=` expands card; `?type=doc` selects Documents | Pass |
| Keyboard expand | Pass |
| Mobile: no horizontal overflow | Pass |
| Mobile: Add task name | Fail then fixed (Q-17) |
| Page / console errors | Pass |

---

## 4. Remaining (not queue-render defects)

These are real, but they are **data or product-scope**, not broken controls on this page:

1. **Stale Active deals.** 121 tasks belong to files whose closing date is already past (Oak Ridge, Franklin, Riverstone). The queue is correct to show Active-deal work, including post-closing tasks (Closing Gift, referrals). The book needs those files completed/closed, not a silent queue hide.
2. **Every open task is unassigned.** Sidebar overdue (124) already matched queue overdue (124). Assignment is empty across the tenant; new tasks from this page now assign to the current user.
3. **Topbar “6 Critical” vs queue “129 critical”.** Intentional split (deal-level briefing vs task-level classifier). Tiles are now labeled as **tasks** so they no longer collide.
4. **Draft run order** still does not call an AI ranker. It resets to critical-first (API order: soonest due) and opens the first card — the control is no longer a dead button.
5. **Edit / Reassign / Delete** are not on the queue card. Skip, complete+undo, email, reschedule, and Open transaction cover the daily path; full edit remains on the deal.

---

## 5. Code touched

Frontend: `TaskQueuePage.tsx`, `TaskQueueCard.tsx`, `AddTaskDialog.tsx`, `useTaskQueue.ts`, `useApiMutate.ts`, `utils/taskQueue.ts`, `utils/export.ts`, unit tests.  
Backend: `task_classifier.today_progress()`, `GET /tasks/queue` progress payload, `app/tests/test_task_classifier.py`.

---

## 6. Implementation verification (2026-08-13, later the same day)

Headed Chrome (`channel: "chrome"`) against `http://localhost:5173` as `shyna.elene@minafter.com`. Unit tests: frontend **14/14**, backend `today_progress` **4/4**. Live queue: 203 open / 129 critical / 1 done today; progress `total_today: 130`, `pct_complete: 1` (overdue + due-today + done-today).

| Intended behavior | Live result |
| --- | --- |
| Q-01 Export CSV | `task-queue.csv`; named at 390px |
| Q-02 My / Team toggle | Both radios present; Team writes `?assignee=team` |
| Q-03 Pagination | **Show N more** on the 129-row critical group |
| Q-04 Today’s progress | Denominator 130 with 1 done today (was 129 with 0 done) |
| Q-05 Complete + Undo | `QA Queue 515659` completed; Undo toast shown |
| Q-06 Add task lands in My queue | Created, searchable, completable |
| Q-07 Search a11y | `Search tasks` label; hit + empty states |
| Q-08 Critical tile | Stays on `/tasks/queue?priority=critical` |
| Q-09 Deep links | `?task=` expands; `?type=doc` selects Documents; `?filter=overdue` → critical |
| Q-10 Vendor loading | No empty-state flash |
| Q-11 Email CTA | In-app **Email transaction party** dialog (contact `mailto:` kept) |
| Q-13 Transaction label | Opens `/transactions/active?highlight=…` |
| Q-14 Notes label | **Notes (optional)** in Add task |
| Q-15 Hit target | Complete control **40×40**; keyboard Expand works |
| Q-17 Mobile names | Add task and Export CSV named at 390px; no horizontal overflow |
| Console / page errors | None |

---

## 7. Fresh Chrome pass (2026-08-13 evening)

Headed Chrome as `shyna.elene@minafter.com` against `http://localhost:5173`. Live queue: 206 open / 69 critical / 95 playbook / 2 done today; progress `total_today: 133`, `pct_complete: 2`.

First pass **46 pass / 5 fail**. After fixes, retest **53 / 53**.

| Issue | Severity | Fix |
| --- | --- | --- |
| Add task submitted with no deal (toast-only, easy to miss) | High | **Add to queue** stays disabled until name + transaction. Deal select shows Loading / empty copy. Chrome: `QA Queue 695499` created, searchable, complete + Undo. |
| My / Team radios were 31px and `hidden` below `sm` | Medium | Always visible, `h-10`. Named at 390px; no horizontal overflow. |
| AI rationale on the expanded card was 11.5px | Low | Raised to 12px. Typography walk of `main`: 0 nodes below 12px. |
| Progress check assumed today ≤ critical + done | n/a | Stale assertion. Today is overdue + due-today (including playbook) + done-today. |

Also re-verified: Export CSV, Critical tile stays on the queue, search, pagination, skip confirm, reschedule Tomorrow, email flow, `?task=` / `?type=doc` / `?filter=overdue`, keyboard expand, no nested interactives, no page/console errors.
