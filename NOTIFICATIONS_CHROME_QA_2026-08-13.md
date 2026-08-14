# Notifications / topbar bell — Chrome QA (2026-08-13)

**Surface:** Topbar bell + `/notifications` + Settings → Notifications  
**Tester:** platform admin `shyna.elene@minafter.com`  
**Environment:** real Google Chrome (Playwright headed, `channel: "chrome"`), frontend `http://localhost:5173`, backend `http://localhost:8000`  
**Dataset (live):** 6 Active deals, **137** open due-window tasks (124 overdue / 6 due today / 5 due tomorrow / 2 upcoming), **33** AI drafts pending review, 1 outbound email today. Every task row was on an Active file.

Artifacts: `velvet-elves-data/notifications_qa/artifacts_2026-08-13_first/` (before), `artifacts_2026-08-13_verify/` (after grouping + badge), `artifacts_2026-08-13_verify3/` (tab wrap), `artifacts_2026-08-13_deep/` (panel off-screen), `artifacts_2026-08-13_deep2/` (viewport clamp + portal).

---

## 1. Executive summary

The bell was not a notification inbox. It dumped **every overdue task** (137 rows, many **97d late**) into a 400px dropdown, with 9.5px type, a 32px hit target, and a badge that would read **99+** whenever the day had not been acknowledged. That collided with the topbar AI briefing (**6 Critical deals**) and with My Task Queue (**124 overdue tasks**), so nobody could tell what the red number meant.

The dropdown is now a **deal-level triage surface**, matching requirements §4.8 compiled summaries (“You have N transactions with deadlines due today”). Chrome after the fix: **6 deal rows**, headline **“6 deals need attention”**, badge **7** (6 deals + 1 for the AI-draft queue), type ≥ 12px, bell **40×40**, mobile panel clamped in-viewport.

A later headed pass found the dialog itself at `y: -296` (tabs above the viewport) because the panel laid out in-flow for a frame and `top` was not clamped ≥ 12. That is fixed: the dialog is portaled to `document.body`, `position: fixed` from the first paint, and height-clamped. Retest: **15 pass / 0 fail**.

| Severity | Found | Status |
| --- | --- | --- |
| High | 5 | Fixed |
| Medium | 5 | Fixed |
| Low | 3 | Fixed |

---

## 2. Issues found and resolved

### N-01 · Bell dumped 137 individual overdue tasks
**Severity:** High · **Area:** Topbar panel

Opening the bell listed every past-due task (`97D LATE`, `94D LATE`, …) instead of the compiled transaction summary the spec describes. Users could not tell which *deals* needed them.

**Fix:** Group by deal. All / Overdue tabs are one row per file (`29 overdue · 4 due today`). Today / Tomorrow still list individual tasks when there are ≤ 8. Dropdown caps at 8 deals with **View N more**.

Chrome: `dropdown action rows≈6 vs 137 API tasks`.

### N-02 · Badge counted every task (+ every AI draft)
**Severity:** High · **Area:** Unread badge

Unread was `overdue.length + due_today.length + day_before.length + ai_drafts_pending` → **168 → 99+**. After “Mark all as read” it cleared, then relit the next morning with the same 99+. 33 pending drafts made the badge impossible to interpret even on a quiet task day.

**Fix:** Badge is **deal-grained** (files with overdue / due-today / due-tomorrow) plus **one** tick for an unseen AI-draft queue. Chrome: badge **7** with 6 deals + 33 drafts; **Mark all as read** cleared it to `Notifications` with no unread suffix.

### N-03 · “You’re all caught up” flashed before data arrived
**Severity:** High · **Area:** Empty / loading

If `/notifications/pending` had not resolved, the panel rendered the caught-up empty state (no skeleton). A slow 137-row payload made the bell look broken.

**Fix:** Treat “no data yet and no error” as loading. Subtitle shows **Loading…** and the list skeleton until the payload is present.

### N-04 · Click landed on `/transactions?status=` and could miss the card
**Severity:** High · **Area:** Deep links

Task rows used `?status=active&expand=&task=`. The rest of the app deep-links with `/transactions/active?highlight=`.

**Fix:** `notificationHref` / `notificationDealHref` use the path aliases and `highlight` + `task` (most urgent task on a deal row). Chrome: click on Oak Ridge opened `/transactions/active?highlight=4585ea3b-…&task=40058d3b-…`.

### N-05 · Closed / Completed files still nagged
**Severity:** Medium · **Area:** Backend feed

In-app + digest queries did not exclude Closed/Completed, so post-close leftovers could keep the bell noisy.

**Fix:** `LIVE_NOTIFICATION_TX_STATUSES = Active | Paused | Incomplete`. Live tenant is all-Active (137/137); API test proves a Closed file’s overdue task disappears from `/pending`.

### N-06 · Typography below 12px
**Severity:** Medium · **Area:** Style guide v2

Counts were 9.5px, subtitle 10.5px, tabs 11.5px, badge 9px.

**Fix:** Panel, page, pills, and badge are ≥ 12px. Chrome type walk: **min 12px, 0 offenders**.

### N-07 · Bell hit target 32×32 (30×30 on mobile)
**Severity:** Medium · **Area:** A11y / §9.1

**Fix:** Bell is **40×40** on desktop and mobile. Badge type raised to 12px.

### N-08 · Mobile panel hung off the left of the viewport
**Severity:** Medium · **Area:** Mobile

`absolute right-0` on the 32px bell wrapper with `width: 400px` (max `100vw-24px`) put the panel at `x=-88`.

**Fix:** `position: fixed`, clamped to 12px inset. Chrome 390px: `{ x: 12, w: 366 }`.

### N-09 · Filter tabs used task counts and overflowed the 400px panel
**Severity:** Medium · **Area:** Tabs

Tabs showed **All 137 / Overdue 124**. Four `min-h-10` chips in a nowrap row clipped on the right-aligned panel (Playwright: Overdue tab outside viewport).

**Fix:** Tab counts are **deal counts** (All 6 / Overdue 6 / Today 2 / Tomorrow 1). Tab list `flex-wrap`s.

### N-10 · Full Notifications page was the same 137-row dump
**Severity:** Low · **Area:** `/notifications`

**Fix:** Same deal grouping; each row expands to the tasks on that file. Header: **6 deals need attention · 124 overdue · 6 due today · 5 due tomorrow**.

### N-11 · `days_ahead` query param was ignored
**Severity:** Low · **Area:** API

**Fix:** `GET /pending?days_ahead=` is passed through to `build_daily_summary` / `get_upcoming_tasks`.

### N-12 · Overdue list had no urgency order
**Severity:** Low · **Area:** Backend

**Fix:** Overdue tasks sort by `days_overdue` descending so the focused task on a deal row is the most late.

### N-13 · Dropdown painted above the viewport (`y: -296`)
**Severity:** High · **Area:** Panel position

Deep Chrome pass (`artifacts_2026-08-13_deep/tab_boxes.json`): the dialog was `{ x: 372, y: -296, w: 400, h: 710 }`. Tabs sat at `y: -220` (`inView: false`). Playwright tab clicks timed out; only the lower list was reachable. Cause: first paint used `visibility: hidden` *without* `position: fixed`, so the 710px panel laid out in the topbar and blew the grid; `top` was `Math.min(bell.bottom + 10, …)` with no `top >= 12` floor and no cap on total dialog height.

**Fix:** Portal the dialog to `document.body`. Start `position: fixed`. Clamp with `clampNotificationPanelPosition` (pin to a 12px inset if the bell is off-screen; `maxHeight = viewport - 24`; flip above the bell when needed). Flex column so header/tabs/footer stay put and the list scrolls. `ResizeObserver` re-places after content loads. Header grid row is locked so in-flow junk cannot grow it.

Chrome (`artifacts_2026-08-13_deep2/`): dialog `{ x: 790, y: 59, w: 400, h: 710 }` on 1440×900; all four tabs in view; real clicks on Overdue / Today / a deal row; 390px panel `{ x: 12, y: 55, w: 366 }` with tabs at `y: 131`. **15 pass / 0 fail.**

---

## 3. Chrome results (after fixes)

Live payload: 124 overdue / 6 today / 5 tomorrow / 2 upcoming on **6 Active deals**; 33 AI drafts; 1 outbound email today.

| Check | Result |
| --- | --- |
| Login as platform admin | Pass |
| Pending API captured; live statuses Active-only | Pass |
| Bell 40×40, named, badge 7 = 6 deals + 1 draft tick | Pass |
| Panel headline “6 deals need attention” + compiled subline | Pass |
| 6 deal rows (not 137 tasks) | Pass |
| Type ≥ 12px in panel, page, and 390px panel | Pass |
| Tabs All / Overdue / Today / Tomorrow present with deal counts | Pass |
| ESC, outside click, Settings navigation close the panel | Pass |
| Deal click → `/transactions/active?highlight=&task=` | Pass |
| Mark all as read clears the badge | Pass |
| View all → `/notifications` grouped page | Pass |
| Settings → Notification preferences + morning digest | Pass |
| Keyboard opens the panel | Pass |
| Mobile: no h-overflow, bell 40×40, panel in viewport | Pass |
| Page / console errors | Pass |
| Panel on-screen (not `y: -296`); tabs clickable | Pass |
| Deal click expands card + target task in view | Pass |
| `/notifications` expand chevron lists tasks | Pass |
| 390px panel clamped; tabs in view | Pass |

---

## 4. Remaining (not bell-render defects)

1. **Stale Active deals.** Oak Ridge / Meadowridge / Riverstone still carry 90-day-late tasks because those files were never Completed/Closed. The bell is correct to group them; the book still needs those files closed. Same finding as My Task Queue QA.
2. **33 AI drafts.** The outbox banner is honest. The badge no longer adds 33. Clearing the actual draft queue is an AI-email hygiene task, not a bell bug.
3. **Admin dashboard KPI strip on Settings** still showed `0 Active deals` in the sidebar during an earlier pass — a dashboard-scope issue, not the notification feed (the bell’s own 6 deals matched the Deals nav badge).

---

## 5. Code touched

Frontend: `utils/notifications.ts`, `utils/notificationPanelLayout.ts`, `hooks/useNotifications.ts`, `NotificationsPanel.tsx`, `NotificationItems.tsx`, `NotificationsPage.tsx`, `TransactionCard.tsx`, `AppLayout.tsx`, unit tests (`notificationsFeed.test.ts`, `unreadNotificationCount.test.ts`, `notificationPanelLayout.test.ts`).

Backend: `task_notification_service.py` (live-status filter, overdue sort, `days_ahead`), `notifications.py`, `test_notifications_api.py`.
