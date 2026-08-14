# Intelligence › AI Suggestions — Chrome QA findings (2026-08-13)

**Page:** Intelligence › AI Suggestions (`/ai-suggestions`)  
**Tester:** platform admin `shyna.elene@minafter.com`  
**Environment:** real Google Chrome (Playwright headed, `channel: "chrome"`), frontend `http://localhost:5173`, backend `http://localhost:8000`  
**Dataset (after engine refresh):** 4 pending suggestions (2 risk / 2 task), 0 critical, 3 acted-on today, 0 snoozed. Live cards are stale-comms check-ins and predicted-missed tasks (`send_text`). This tenant has no pending `add_task` / `send_email` cards, so Edit & Accept / scope radios / Send Email were exercised in code and skipped in the live pass.

Artifacts: `velvet-elves-data/ai_suggestions_qa/artifacts_2026-08-13_first/` (31/23), later retest folders, and `artifacts_2026-08-13_verify5/` (implementation verification, **61 pass / 0 fail / 4 skip**).

---

## 1. Executive summary

The page loaded and the briefing, stats, category pills, expand, and Send Text primary action worked. It was **not** seamless. Missing Export/search/URL sync, dead Acted-on and Snoozed tiles, sub-12px type, unnamed mobile actions, no dismiss Undo, deal context that was not a link, and **broken engine copy plus duplicate cards** on the same detector+deal made daily work noisy and easy to mis-read.

Those functional gaps are **fixed and re-verified in Chrome**. The headed verify5 pass confirmed **61/61 applicable checks**, including Export CSV, search, URL filters, 2-week snooze, dismiss Undo + restore, copy (`no logged contact yet` / `1 days` / `day(s)` gone), keyboard expand, 12px type, 32px hits, and named mobile actions.

| Severity | Found | Status |
| --- | --- | --- |
| High | 6 | Fixed |
| Medium | 8 | Fixed |
| Low / data | 4 | Documented (not page-render bugs) |

---

## 2. Issues found and resolved

### S-01 · No Export action
**Severity:** High · **Area:** Header

Contacts / Active Transactions / Task Queue all have Export. This header only had Refresh and Act on all.

**Fix:** **Export CSV** downloads the currently visible rows as `ai-suggestions.csv`. Chrome retest saved the file; the control is named at 390px.

### S-02 · No search
**Severity:** High · **Area:** Toolbar

A 14-card (then 4-card) inbox with no filter-by-address/title made finding a deal’s nudge slow.

**Fix:** Search input with `type="search"` and `aria-label="Search suggestions"`. Hits title, address, reason, and description. Empty state: “No suggestions match”. URL writes `q=`.

### S-03 · Stat tile “Critical alerts” collided with the topbar “6 Critical”
**Severity:** Medium · **Area:** Stats vs topbar

Topbar AI briefing: **6 Critical** (deals). Page: **0 Critical alerts** (suggestion priority). `getByRole(button, Critical)` hits the topbar first and navigates off the page.

**Fix:** Page tile `aria-label="{n} Critical alerts"`. Click stays on `/ai-suggestions?category=critical` and filters `priority=critical` (honest 0 on this tenant).

### S-04 · No URL deep links
**Severity:** High · **Area:** Filters / share

Category, view, search, dismissed, confidence, and expanded card were React-only. Refresh or a pasted link reset the inbox.

**Fix:** URL sync for `category`, `view=pending|accepted|snoozed`, `q`, `dismissed=1`, `suggestion=`, `minc=75|90`. `?suggestion=` expands the card (and extends pagination if needed).

### S-05 · Acted on today / Snoozed tiles were dead
**Severity:** High · **Area:** Stats

The counts rendered; the buttons did nothing. Snoozed work was unreachable from this page.

**Fix:** Both tiles are real views (`status=accepted|snoozed`). Snoozed cards expose **Wake now** (restore). URL writes `view=snoozed`.

### S-06 · Type below 12px
**Severity:** Medium · **Area:** Chrome / cards

STYLE_GUIDE floor is 12px. Kickers and confidence meta were 11px.

**Fix:** Page chrome and cards are ≥ 12px. Verify5 typography walk of `main` found **0** nodes below 12px.

### S-07 · Hit targets / mobile unnamed actions
**Severity:** Medium · **Area:** Header / 390px

Refresh was icon-only on small screens; Act on all / Export were easy to miss. Several header controls were shorter than 32px.

**Fix:** Header actions are `h-10`. Refresh has `aria-label="Refresh"`; Act on all and Export stay named at 390px. No horizontal overflow.

### S-08 · Snooze missing 2 weeks
**Severity:** Medium · **Area:** Card

Plan F14 / design: 2 hours / Tomorrow / 1 week / **2 weeks**. The picker stopped at 1 week. Escape also did not close the inline picker.

**Fix:** 2 weeks is in the picker. Escape and **Cancel** close it without applying a snooze.

### S-09 · Dismiss had no Undo
**Severity:** High · **Area:** Card / toast

A mis-click dismissed work with restore buried behind Show dismissed. The success toast used a render-prop button that Chrome did not reliably expose as **Undo**.

**Fix:** Dismiss toast includes an `aria-label="Undo"` control (8s) that calls restore. Show dismissed still lists **Restore**. Restore is idempotent if the row is already pending (double Undo / race no longer 409s). Chrome verify5: dismiss → Undo visible → Restore → `status=pending`.

### S-10 · Deal context was not a link until expand; briefing titles were not jumpable
**Severity:** Medium · **Area:** Collapsed row / briefing

The collapsed row was one large control, so the address could not be a deal link. Briefing `critical_items` chips did not scroll to the card.

**Fix:** Collapsed row is no longer a single button. Context is a **Link** to `/transactions/:id`. Briefing chips jump to the card. Nested interactive count on verify5: **0**.

### S-11 · Broken copy: `no logged contact yet`, `1 days`, `day(s)`
**Severity:** High · **Area:** Engine copy

Detectors produced unreadable titles (`No client contact in no logged contact yet — closing in 1 days`, `"Deliver Utility Info" due in 0 day(s)`). Helpers `_in_days` / never-contacted title were already in code, but **Refresh did not rewrite existing pending rows**.

**Fix:** `_in_days` → “today” / “in 1 day” / “in N days”. Never-contacted title is **“No client contact logged yet”**. Persist now **refreshes copy in place**. Verify5: `copy-never-contacted` and `copy-plural-days` pass after Refresh.

### S-12 · Duplicate cards for the same detector + deal
**Severity:** High · **Area:** Persist / dedup

Identity used to include title, so a copy tweak forked a second card. This tenant had three `risk.stale_client_comms` rows on one transaction. PostgREST `.in_("status", …)` also returned **zero** pending rows in local runs, so persist skipped every refresh and unique-violated on insert (`generated=0`, old titles stayed).

**Fix:** Dedup is **detector + transaction only**. Persist loads the tenant’s rows and filters status in Python, collapses extras to `superseded`, updates the keeper’s copy (without rewriting `dedup_hash`, which collided with leftover hashes), revives superseded/expired when the detector fires again, and supersedes orphans on deals that were scanned but no longer match. Live inbox went **12 → 4** with no duplicate keys.

### S-13 · Scope radios / Edit & Accept missing on this tenant’s cards
**Severity:** Medium · **Area:** Accept (task-kind only)

Spec §10.6: Apply to this transaction / all future, and Edit & Accept. Those controls only apply to `add_task` (and kin) with a `proposedTask`. Almost every live card is `send_email` / `send_text`.

**Fix:** Radios + task name/due + Edit & Accept render when `proposedTask` exists. Chrome: **SKIP** (no `add_task` on this book). Backend accept already takes `edited_task_name` / `edited_task_due_date`.

### S-14 · Send Email toast used a router Link inside the toaster
**Severity:** Low · **Area:** Accept email

`Link` inside the hot-toast host threw. Accept-email was flaky in earlier passes.

**Fix:** Draft-ready toast uses a plain `<a href="/ai-emails">`. Live verify5 skipped Send Email because the remaining cards are `send_text` only.

---

## 3. Chrome retest (verify5)

Headed Chrome against `http://localhost:5173` as `shyna.elene@minafter.com`. Frontend unit tests **4/4**. Backend `test_suggestion_engine.py` **24/24** (detectors + persist collapse/refresh/dismiss/revive/orphan). Live inbox after generate: **4 pending**, 0 critical.

| Check | Result |
| --- | --- |
| Login / sidebar / page load | Pass |
| Grouped API + briefing | Pass (4 items; headline matches) |
| Export CSV | `ai-suggestions.csv` |
| Search hit + empty | Pass (`Harness` → 1 card) |
| Critical tile vs topbar | Distinct aria-label; stays on page |
| Acted on / Snoozed clickable | Pass; `view=snoozed` |
| Category pill filters **cards** (briefing may still mention other items) | Pass (Risk → 2 cards, no task-card leak) |
| Expand / reason / draft / primary | Pass (Send Text) |
| Snooze 2h / Tomorrow / 1 week / 2 weeks | Pass |
| Dismiss + Undo toast + Restore | Pass (`dismissed` → `pending`) |
| View deal | `/transactions/{id}` |
| Bulk Act on all dialog (cancelled) | Pass; no `window.confirm` |
| Refresh + copy | Pass; no `1 days` / `day(s)` / `no logged contact yet` |
| `?suggestion=` deep link | Pass |
| Keyboard expand | Pass |
| Typography ≥ 12px / nested interactive / 32px hits | Pass |
| Mobile 390: overflow, Act on all, Refresh, Export named | Pass |
| Page / console errors | None (aborted GETs during navigation only) |

Skipped on this dataset (not missing UI): scope radios, Edit & Accept, accept-task, accept-email.

---

## 4. Remaining (not page-render defects)

1. **Topbar “6 Critical” vs page “0 Critical alerts”.** Intentional split (deal-level briefing vs suggestion `priority=critical`). Tiles are labeled **alerts** so they no longer collide.
2. **No `add_task` / `send_email` pending on this tenant.** Scope radios, Edit & Accept, and the Send Email draft path need a deal that the engine classifies that way (closing-gift window, or a risk card with `send_email`). The controls are implemented; this book’s four cards are `send_text`.
3. **Briefing narrative is not category-filtered.** Switching the Risk pill hides task **cards** but the hero can still quote a task title. That is the daily summary, not a leak in the list.
4. **Market / Marketing / Coaching** stay flag-gated per the completion plan. Honest empty — no fabricated MLS/social/coach cards.
5. **Stale Active deals** still drive stale-comms and predicted-missed nudges. The engine is correct to flag them; the book still needs files closed when they are actually done.

---

## 5. Code touched

Frontend: `AISuggestionsPage.tsx`, `utils/aiSuggestions.ts`, `utils/export.ts` (`exportAiSuggestionsCsv`), `src/tests/unit/aiSuggestions.test.ts`.  
Backend: `app/services/suggestion_engine.py` (copy helpers + persist rewrite), `app/api/v1/ai_suggestions.py` (accept edits, restore snoozed/pending), `app/tests/test_suggestion_engine.py`.  
QA: `velvet-elves-data/ai_suggestions_qa/ai_suggestions_chrome_qa.mjs`.

No git commit/push was made (per project notes).
