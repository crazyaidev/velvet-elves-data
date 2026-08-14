# Workflow › Needs You — Chrome QA findings (2026-08-13)

**Page:** Workflow › Needs You (`/needs-you`)  
**Tester:** platform admin `shyna.elene@minafter.com`  
**Environment:** real Google Chrome (Playwright headed, `channel: "chrome"`), frontend `http://localhost:5173`, backend `http://localhost:8000`  
**Dataset (live):** 6 Active deals, **49** Needs You items (0 ready to send / 1 safe-to-approve proposal / **33** drafts to review / 0 coverage decisions / **15** blocked AI tasks). Sidebar badge **49**. Scheduler **stale** (last tick 16 days ago; tenant last run earlier today).

Artifacts: `velvet-elves-data/needs_you_qa/artifacts_2026-08-13_first/` (too-early dump while the 10s API was in flight), `artifacts_2026-08-13_diag/` (API timing + layout), `artifacts_2026-08-13_verify/` (after fixes, 48/5), and `artifacts_2026-08-13_verify2/` (implementation verification, **52 pass / 0 fail / 5 skip**).

---

## 1. Executive summary

The route loaded and, once the payload arrived, the briefing, scheduler banner, kind filters, deal groups, expand, Review / Handle / Open deal, Give-back, and unattached-draft group all worked. It was **not** seamless. The queue takes ~10s, the header had no loading pill, there was no Export, filters died on refresh, **Approve all safe** fired with no confirm, type sat at 9–11.5px, and the row was a `role="button"` wrapping Send/Approve/Review/Handle.

Those functional gaps are **fixed and re-verified in Chrome**. Verify2 confirmed **52/52 applicable checks**, including Export CSV, URL sync (`kind`, `q`, `item`, `tx`), Approve-all confirm (cancelled), Review → AI Emails, Handle → deal Tasks, 12px type, 0 nested interactives, named Export at 390px, and no page/console errors.

| Severity | Found | Status |
| --- | --- | --- |
| High | 5 | Fixed |
| Medium | 6 | Fixed |
| Low / data | 4 | Documented (not queue-render bugs) |

---

## 2. Issues found and resolved

### NY-01 · No Export action
**Severity:** High · **Area:** Header

Contacts / Active Transactions / My Task Queue / All Documents / AI Suggestions / Vendor Proposals all have Export. Needs You had none, so a 49-row inbox could not leave the page.

**Fix:** **Export CSV** downloads the currently visible rows (`needs-you.csv`, respects kind / search / deal filters). Named at 390px (`aria-label="Export CSV"`). Chrome verify2 saved the file.

### NY-02 · Kind, search, and expanded card were React-only
**Severity:** High · **Area:** URL

Only `?tx=` (deal deep link) was read. Kind filter, search, and the open card reset on refresh or a pasted link.

**Fix:** URL sync for `kind`, `q`, `item`, and `tx`. Chrome: `?kind=ready_draft` / `?kind=task` select the tile; `?q=` follows search; `?item=` expands the card; `?tx=` still shows one deal with a clear chip.

### NY-03 · Ten-second load looked like a blank page
**Severity:** High · **Area:** Loading / API

`GET /automation/needs-you` took **~10.2s** (actions, drafts, and tasks were sequential). The header count pill rendered only after `data` arrived, so the first headed pass screenshotted an empty body. Failed loads would have shown the empty-state lie “Nothing needs you right now.”

**Fix:** Header pill shows **Loading** immediately. `ErrorAlert` on failure. Backend fetches actions / drafts / blocked tasks **in parallel**. Chrome: pill reads `49 waiting · 0 ready to send`; scheduler banner is visible while loading finishes.

### NY-04 · “Approve all safe” had no confirmation
**Severity:** High · **Area:** Batch approve

“Send all ready” already used `ConfirmDialog`. Approve-all applied reversible proposals on one click — easy to misfire next to the briefing.

**Fix:** Confirm names the count and the safe-action boundary (waives / date changes stay individual). Chrome: dialog **Approve 1 safe proposal?**; Cancel left the queue unchanged.

### NY-05 · Whole row was `role="button"` wrapping the CTAs
**Severity:** Medium · **Area:** A11y / nested interactives

Send / Approve / Review / Handle sat inside a clickable row. Keyboard expand was unreliable; `getByRole(button, Review)` could hit the “To review” tile instead of the draft CTA.

**Fix:** Title block toggles expand; dedicated **Expand item / Collapse item** control (40×40); no wrapping `role="button"`. Chrome: nested interactive count **0**; keyboard Expand works.

### NY-06 · Type below 12px
**Severity:** Medium · **Area:** Style guide v2

Breadcrumb 11.5px, count pill 11px, kind pills / kickers 9–10px, captions 11.5px.

**Fix:** Page chrome, pills, kickers, waiting-since, and captions are ≥ 12px. Verify2 typography walk of `main`: **0 offenders**.

### NY-07 · Search had no accessible name
**Severity:** Medium · **Area:** Toolbar

Placeholder-only input. Task Queue uses `aria-label="Search tasks"`.

**Fix:** `type="search"` and `aria-label="Search items"`. Hits title, deal, summary, recipients. Empty state: “Nothing in this view.” URL writes `q=`.

### NY-08 · Stat tiles had no unique names
**Severity:** Medium · **Area:** Stats vs rows

Visible labels were “To review” / “To handle”. A `/Review/` role query hit the tile and wrote `?kind=draft` instead of opening AI Emails.

**Fix:** Tiles use `aria-label="{n} {statLabel} items"` (e.g. `33 To review items`). Click stays on `/needs-you?kind=…`. Chrome: Review **row** opens `/ai-emails/:id`; Handle opens `/transactions/:id?tab=tasks&task=`.

### NY-09 · Hit targets were 32px
**Severity:** Medium · **Area:** A11y / §9.1

Row CTAs and the expand chevron were `h-8` / `h-6`. Style guide / other Workflow pages moved primary controls to 40px.

**Fix:** Header Export, batch actions, row Send/Approve/Review/Handle, Give-back, Open deal, Expand, and search are **h-10**. Chrome hit-target walk: **0** visible controls under 32px.

### NY-10 · API errors looked like an empty queue
**Severity:** Medium · **Area:** Empty / error

No `ErrorAlert`. `groups.length === 0` after a failed fetch would show “Nothing needs you right now.”

**Fix:** Error banner; empty copy only when the query succeeded with zero rows.

### NY-11 · No per-group pagination
**Severity:** Medium · **Area:** List

Spec / Task Queue paginate groups over 20. This tenant’s clustered groups are all under 20 (Oak Ridge’s 22 similar drafts collapse to one row), so **Show N more** is skipped in Chrome. The cap is in place for larger books and `?item=` still extends it.

### NY-12 · Deal name was not a link
**Severity:** Low · **Area:** Group header

Only **Open deal** jumped to the workspace. Task Queue’s transaction label is a control.

**Fix:** Group title is a link to the deal (unattached group stays text + “Re-file or discard from Email review”).

### NY-13 · No Ask AI control on the page
**Severity:** Low · **Area:** Header / FAB

My Task Queue mounts `AskAiFab`. Needs You did not, so ⌘L / the charcoal chip were the only ways in.

**Fix:** Same floating **Ask AI** control as the rest of Workflow.

---

## 3. Chrome retest (after fixes)

| Check | Result |
| --- | --- |
| Login as platform admin | Pass |
| Breadcrumb, title, Export CSV, loading then `49 waiting · 0 ready to send` | Pass |
| API 49 total / 0 ready / 1 safe; kinds 33 draft / 15 task / 1 action | Pass |
| Stale scheduler banner + Open AI & Automation | Pass |
| Approve all safe confirm (cancelled) | Pass |
| Kind tiles stay on `/needs-you?kind=`; Ready empty state | Pass |
| Search a11y, hit, empty, `q=` | Pass |
| Export `needs-you.csv` | Pass |
| Expand / keyboard Expand / 40×40 control | Pass |
| Review → `/ai-emails/:id`; Handle → deal Tasks; Open deal | Pass |
| Give-back on stale-overdue tasks | Pass |
| Unattached drafts group (3) | Pass |
| `?tx=` chip + clear; `?item=` expands; `?kind=task` | Pass |
| Type ≥ 12px; nested interactives 0; hits ≥ 32px | Pass |
| Mobile 390: no overflow; Export named | Pass |
| Page / console errors | Pass |

Skipped (honest, not broken): **Send** / Send all ready (0 ready on Manual-heavy book), coverage options (0 decisions), Show more (no group over 20 clustered rows), mobile Send all.

---

## 4. Remaining (not queue-render defects)

These are real, but they are **data, ops, or product-scope**, not broken controls on this page:

1. **Automation scheduler is stale (16 days).** The banner is correct. Admins still trigger a cycle from Settings → AI & Automation (Run now is intentionally not on this page).
2. **0 ready to send.** Autopilot pre-approval is off for this book; drafts wait as **To review**. Send all ready is hidden until `ready_draft` rows exist.
3. **15 blocked AI tasks.** Missing purchase agreement, Manual posture, or stale-overdue (&gt;30 days). The queue is right to show them; Give-back / Handle are the recovery path.
4. **Duplicate inbound drafts.** Oak Ridge has **22 similar** “Quick question about closing” drafts collapsed to one row. Clearing the pile is Email review work, not a list-render bug.
5. **Three unattached drafts** (“Not linked to a deal”) — surfaced on purpose (earlier E2E I-11) so they cannot ride a batch send.

---

## 5. Code touched

Frontend: `NeedsYouPage.tsx`, `needsYouCluster.ts`, `export.ts`, `GiveBackToAiButton.tsx`, unit tests.  
Backend: `app/api/v1/automation.py` (`GET /needs-you` loads actions, drafts, and blocked tasks concurrently).

---

## 6. Implementation verification (2026-08-13, later the same day)

Headed Chrome (`channel: "chrome"`) against `http://localhost:5173` as `shyna.elene@minafter.com`. Unit tests: frontend `needsYouCluster` **7/7**, backend `test_needs_you_queue_and_batch_approve` + `test_plan_needs_you_includes_blocked_ai_tasks` **2/2**. Live queue: 49 waiting / 0 ready / 1 safe; kinds 33 draft / 15 task / 1 action.

| Intended behavior | Live result |
| --- | --- |
| NY-01 Export CSV | `needs-you.csv`; named at 390px |
| NY-02 URL sync | `kind=`, `q=`, `item=`, `tx=` |
| NY-03 Loading pill / not blank | Header **Loading** then **49 waiting · 0 ready to send** |
| NY-04 Approve all confirm | Dialog shown; Cancel did not apply |
| NY-05 Expand control | Named Expand/Collapse; nested **0** |
| NY-06 Type | **0** nodes below 12px |
| NY-07 Search a11y | `Search items`; hit + empty |
| NY-08 Stat tiles | Stay on `/needs-you?kind=`; Review/Handle rows do not collide |
| NY-09 Hit targets | **0** under 32px |
| NY-12 Deal title | Link + Open deal |
| NY-13 Ask AI | FAB on desktop and 390px |
| Review / Handle | `/ai-emails/…` and `/transactions/…?tab=tasks&task=` |
| Unattached group | 3 drafts, no Open deal |
| Console / page errors | None |

---

## 7. Fresh Chrome pass (2026-08-13 evening)

Headed Chrome as `shyna.elene@minafter.com` against `http://localhost:5173`. Live queue: **49** waiting / 0 ready / 1 proposal / 33 drafts / 15 blocked AI tasks; scheduler stale.

After the fixes above, retest **52 pass / 0 fail / 5 skip**.
