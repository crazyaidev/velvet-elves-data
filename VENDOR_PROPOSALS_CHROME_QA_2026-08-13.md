# Intelligence › Vendor Proposals — Chrome QA findings (2026-08-13)

**Page:** Intelligence › Vendor Proposals (`/vendor-proposals`)  
**Tester:** platform admin `shyna.elene@minafter.com`  
**Environment:** real Google Chrome (Playwright headed, `channel: "chrome"`), frontend `http://localhost:5173`, backend `http://localhost:8000`  
**Dataset:** 2 open proposals (1 pending date change on 77 Harness Test Lane, 1 unmatched `needs_clarification` with no deal/date) plus 8 decided rows (accepted/rejected) that the first-pass UI could not reach.

Artifacts: `velvet-elves-data/vendor_proposals_qa/artifacts_2026-08-13_first/` (21 pass / 16 fail) and `artifacts_2026-08-13_verify/` (implementation verification, **40 pass / 0 fail / 1 info**).

---

## 1. Executive summary

The page loaded, the three open-status tabs switched, and Accept / Reject / Clarify were wired to the API. It was **not** seamless. There was no Export or search, tab state died on refresh, decided history was unreachable, unmatched proposals could not be linked to a task (Accept returned 400), type sat below the 12px floor, deal context was not a link, and a mis-click had no Undo.

Those functional gaps are **fixed and re-verified in Chrome**. The headed verify pass confirmed **40/40 applicable checks**, including Export CSV, search, URL tabs, a Decided view with Restore, a task picker, Accept → Undo (toast + reopen, task date reverted), Escape on the reject panel, 12px type, 32px header hits, and named mobile Export/Refresh.

A follow-up closeout pass (2026-08-13 evening) closed the remaining dead-end: unmatched / dateless rows can now pick a deal, type a date, and draft a clarify ask. Headed Chrome: **50 pass / 0 fail**.

| Severity | Found | Status |
| --- | --- | --- |
| High | 6 | Fixed |
| Medium | 7 | Fixed |
| Low / data | 3 | Documented (not page-render bugs) |

---

## 2. Issues found and resolved

### P-01 · No Export action
**Severity:** High · **Area:** Header

Contacts / Active Transactions / Task Queue / AI Suggestions all have Export. This header only had Refresh.

**Fix:** **Export CSV** downloads the currently visible rows as `vendor-proposals.csv`. Chrome retest saved the file; the control is named at 390px.

### P-02 · No search
**Severity:** High · **Area:** Toolbar

Two open cards and a hidden decided history with no filter-by-address/task/vendor made finding a deal’s proposal slow.

**Fix:** Search input with `type="search"` and `aria-label="Search proposals"`. Hits task, vendor, address, dates, status, and original email. Empty state: “No proposals match”. URL writes `q=`.

### P-03 · No URL deep links
**Severity:** High · **Area:** Filters / share

Tab state was React-only. Refresh or a pasted link reset the inbox. `?tab=needs_clarification` stayed in the URL but did not select the tab.

**Fix:** URL sync for `tab=pending|needs_clarification|all|decided`, `q=`, and `proposal=`. Chrome retest: `?tab=needs_clarification` selects **Awaiting vendor** (`aria-selected=true`).

### P-04 · Decided work was unreachable
**Severity:** High · **Area:** Tabs / API

The list API already accepts `status=accepted|rejected|superseded` (8 rows on this tenant). The page never asked for them. After Accept/Reject the card vanished with no history.

**Fix:** **Decided** tab loads those statuses. Decided cards expose **Restore to queue**. The hook now actually sends the `status` query (it previously accepted the param and ignored it).

### P-05 · Unmatched Accept was a dead 400
**Severity:** High · **Area:** Card / accept

Live pending row: proposed `2026-08-15`, `task_id=null`, `match_strategy=unmatched`, deal = 77 Harness Test Lane. Accept was enabled. Click → `400` “Proposal has no linked task. Pick a task before accepting.” No picker.

**Fix:** When a deal is known but no task is linked, the card shows **Link to a task** (open tasks on that deal). Accept stays disabled with an honest reason until a task is picked. Accept sends `task_id`; the backend attaches then updates the due date. Chrome: picker → Inspection Scheduled → Accept enabled.

### P-06 · Accept / Reject / Clarify had no undo
**Severity:** High · **Area:** Toast / decided

A mis-click updated a live task date with no way back. Failed calls toasted; success did not offer Undo.

**Fix:** Success toast includes **Undo** (8s) via `POST /proposals/{id}/reopen` (reverts the task date when the row was accepted). Decided cards also have **Restore to queue**. Chrome: Accept → Undo toast → status `pending`, original date restored.

### P-07 · Type below 12px
**Severity:** Medium · **Area:** Chrome / cards

STYLE_GUIDE floor is 12px. Breadcrumb 11–11.5px, count pill 11px, tab counts 9.5–10px, date labels 10.5px, status badge 11px.

**Fix:** Page chrome and cards are ≥ 12px. Verify typography walk of `main` found **0** nodes below 12px.

### P-08 · Deal / task were not links
**Severity:** Medium · **Area:** Card

Address rendered as plain text. Opening the deal meant leaving the queue and searching.

**Fix:** Property is a link to `/transactions/:id`. Linked task name goes to My Task Queue `?task=`. Close-out request addresses link the same way.

### P-09 · No confidence chip
**Severity:** Medium · **Area:** Card

`ai_confidence` is on every row (0.9 / 0.45 on this tenant) and never shown.

**Fix:** `AI · 90%` chip on the card, 12px mono.

### P-10 · Escape did not close the reject panel
**Severity:** Medium · **Area:** Reject

Opening Reject then pressing Escape left the alternative-date panel open.

**Fix:** Escape closes the panel. Chrome retest: panel gone after Escape.

### P-11 · Breadcrumb was not a named nav
**Severity:** Medium · **Area:** Header

AI Suggestions uses `<nav aria-label="Breadcrumb">`. This page used a plain div, so the crumb was invisible to the accessibility tree.

**Fix:** Same breadcrumb nav pattern, 12.5px.

### P-12 · Sidebar badge counted “awaiting vendor”
**Severity:** Medium · **Area:** Nav

Badge used `total` (pending + needs_clarification). The agent’s actionable queue is pending.

**Fix:** Badge is pending-only. Chrome: `Vendor Proposals 1` with one awaiting-you row.

### P-13 · “Ask vendor to clarify” did not draft mail
**Severity:** Medium · **Area:** Clarify

The button only flipped status. Reject-with-date already drafts a counter-offer.

**Fix:** Clarify drafts a “reply with `Scheduled: YYYY-MM-DD`” email when a recipient exists (best-effort; still marks the row if there is no address). Toast: “Clarification draft is in Email.” when a draft id is stored.

### P-14 · Hit targets / mobile unnamed Export
**Severity:** Medium · **Area:** Header / 390px

Refresh was the only header action. Export did not exist. Several labels were below 12px.

**Fix:** Header actions are `h-10`. Export and Refresh are named (`aria-label`). No horizontal overflow at 390px.

---

## 3. Data / product notes (not page-render bugs)

### D-01 · Unmatched clarification with no deal — **fixed**
The `needs_clarification` row (`b175e687-…`) had no transaction, task, vendor, or parsed date. Accept was a dead-end.

**Fix:** Card shows **Link to a deal** (global transaction search), **Vendor proposed date**, then **Link to a task**. Accept sends `transaction_id` / `task_id` / `proposed_due_date`. Clarify with no inbound address opens a **Vendor email** panel and drafts the ask. Chrome closeout: search “Harness” → Inspection Scheduled → date `2026-08-22` → Accept → Undo (status `pending`, task date reverted).

### D-02 · Login-time 4xx on public tenant/branding
Several `GET /api/v1/public/tenant-branding`, `/tenants/current`, and dashboard calls 4xx before the session is ready. Same noise as other local Chrome passes. Not caused by this page.

### D-03 · Decided history is old reject-from-queue rows
Eight decided rows (mostly “Rejected from queue” on 8104 Riverstone Place) are now visible under **Decided**. They are real history, not new defects.

---

## 4. Verify pass (40 / 0)

| Area | Result |
| --- | --- |
| Login, sidebar nav (badge = 1), page load | Pass |
| Breadcrumb, H1, Refresh, Export, Search | Pass |
| Tabs: Awaiting decision / vendor / All open / Decided + URL sync | Pass |
| Search hit (Harness) / empty (`No proposals match`) | Pass |
| Export CSV (`vendor-proposals.csv`) | Pass |
| Card: task name, deal link, AI · 90%, Accept gated until linked | Pass |
| Reject panel + Escape | Pass |
| Accept → Undo toast → reopen pending | Pass |
| `?tab=needs_clarification` selects Awaiting vendor | Pass |
| Typography ≥ 12px, no nested interactives, header hits ≥ 32px | Pass |
| Mobile 390: no overflow, named Refresh + Export | Pass |

---

## 4b. Closeout pass (50 / 0)

Artifacts: `velvet-elves-data/vendor_proposals_qa/artifacts_2026-08-13_closeout/`

| Area | Result |
| --- | --- |
| Prior verify checks (export, search, tabs, reject Escape, 12px, mobile) | Pass |
| Orphan card: deal search, date input, Accept gated | Pass |
| Clarify panel + Escape when no vendor email | Pass |
| Pick 77 Harness Test Lane → Inspection Scheduled → type date | Pass |
| Accept orphan → Undo toast → reopen `pending` | Pass |

---

## 4c. Requested retest (2026-08-13 evening)

Headed Chrome as `shyna.elene@minafter.com`. Live set: **2 pending** (both on 77 Harness Test Lane / Inspection Scheduled), 0 awaiting vendor, 9 decided. The earlier unmatched clarification row is no longer a dead-end — it is pending with deal, task, and date.

| Pass | Result |
| --- | --- |
| Direct (chrome, search, tabs, export, reject Escape, 12px, mobile) | **38 pass / 0 fail** (orphan card skipped — none left) |
| Verify (same + Accept → Undo on a live pending row) | **40 pass / 0 fail** |

No new page defects. Login-time public branding 4xx is the same pre-session noise as other local passes.

---

## 5. What changed

**Backend**
- `POST /api/v1/vendor-communications/proposals/{id}/reopen` — undo a decision; revert task `due_date` when the row was accepted
- Clarify drafts a constrained-format ask when a recipient exists; `recipient_email` + optional `transaction_id` on the clarify body
- Accept accepts `task_id`, `transaction_id`, and `proposed_due_date` so unmatched / dateless rows can be finished
- Attaching a task also copies the task's deal onto the proposal
- Tests: unmatched accept is 400 until `task_id` is sent; dateless accept is 400 until a date is sent; orphan accept with task+date; clarify with typed email drafts; reopen reverts the date

**Frontend**
- `src/utils/vendorProposals.ts` — URL, search, CSV, pagination helpers, accept-gate + email helpers
- Vendor Proposals page: Export, search, Decided tab, URL sync, Undo toast, error alert, 12px chrome
- Card: deal search, date input, task picker, deal/task links, confidence chip, disabled reasons, Escape, Restore, clarify-email panel
- Hook actually sends `status=`; sidebar badge = pending only
