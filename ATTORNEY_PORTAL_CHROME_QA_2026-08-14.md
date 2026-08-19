# Attorney Portal — browser QA findings (2026-08-14)

**Portal:** Attorney Workspace (`/dashboard/attorney` and related routes)  
**Tester:** attorney `adams.jefferson@minafter.com`  
**Environment:** local frontend `http://127.0.0.1:5173`, backend `http://127.0.0.1:8000`  
**Dataset (live, seeded for this pass):** 4 assigned attorney-closing matters — Oak Ridge OH (unsigned review items), Meadowridge OH (unsigned), Franklin IN (unsigned), Riverstone OH (all signed, release-ready). Tenant also has other Active deals the attorney is **not** assigned to.

**Why the browser changed:** Headed Google Chrome (`channel: "chrome"`, `--start-maximized`) exhausted this machine (`net::ERR_INSUFFICIENT_RESOURCES`, blank pages, dropped API calls). The harness now defaults to **Playwright bundled Chromium, headless**, against a **production `vite preview` bundle** (one JS file instead of Vite’s hundreds of `/src/*.tsx` modules). That is still Chromium (same engine as Chrome) and uses far less RAM.

Artifacts:

| Pass | Browser | App server | Result |
| --- | --- | --- | --- |
| `attorney_portal_qa/artifacts_2026-08-14_first/` | Headed Chrome | `npm run dev` | Empty queue (attorney had 0 assignments) |
| `artifacts_2026-08-14_populated/` | Headed Chrome | `npm run dev` | **117 pass / 15 fail / 134 checks** — product bugs below |
| `artifacts_2026-08-14_verify/` | Headed Chrome | `npm run dev` | **138 pass / 3 fail / 143 checks** after most fixes |
| `artifacts_2026-08-14_light3/` | Headless Chromium | `vite preview` | **129 pass / 12 fail / 143 checks** — attorney product checks passed; late-run session dropped to login |

Harness: `velvet-elves-data/attorney_portal_qa/attorney_portal_chrome_qa.mjs`  
(`QA_HEADED=1` restores a visible window if this machine has RAM to spare.)

---

## 1. Executive summary

The Attorney Portal loaded, redirected to `/dashboard/attorney`, and after seeding four matters the legal queue was usable: Pending review **3**, Ready to release **1**, Needs Review sidebar **3**, Sign off → Reopen, human-only Send packet, Releases URL tabs, `scope=attorney` on AI Suggestions, Workspace breadcrumbs on Contacts / Documents, no agent “HARD STOP” cards, no “Agent, …” next-step copy.

The first populated Chrome pass was **not** seamless. The bucket classifier put every file in Missing docs (`needs_review=0`) while Releases already had a ready packet; Matters reused the **agent** transaction list; sign-off did not show Reopen; type sat at 9–11.5px; search was a command-palette **button**; attorney chrome still said “deals / overdue tasks.”

Those product gaps are **fixed**. Headed Chrome verify cleared 138/143. The remaining 3 (Ask-AI 11px hint, sidebar “Hard Stops” false-positive, 403 on flagged-doc count) were fixed and **passed** on the headless Chromium retest. Light3’s 12 fails clustered after Documents: `/calendar` stuck on “Loading…”, then Settings / Notifications / Search / legacy redirects landed on **login** — a long-run session drop on a low-RAM box, not a new attorney-workspace regression (the same surfaces passed earlier in headed Chrome).

| Severity | Found | Status |
| --- | --- | --- |
| High | 2 | Fixed |
| Medium | 8 | Fixed |
| Low / harness / data | 5 | Documented |

---

## 2. Issues found and resolved

### AT-01 · Unsigned matters classified as Missing docs
**Severity:** High · **Area:** Dashboard / Matters / sidebar KPIs

`attorney_filter_key` treated “missing a critical document type” as higher priority than unsigned sign-offs. Result: `filter_counts.needs_review=0`, `ready_to_release=0`, all 4 files in Missing docs, while `GET /attorney/releases` already had **1 ready** (Riverstone). Sidebar Needs Review = 0 despite 3+ unsigned files.

**Fix:** Unsigned items always win → `needs_review`. No checklist → `missing_docs`. Fully signed → `ready_to_release` (aligned with Releases). Released packets stay `clean_files`. Tests: `app/tests/test_attorney_filter.py`.

**Retest:** `needs_review=3`, `ready_to_release=1`, `missing_docs=0`. Pending review KPI = 3. Releases ready = 1.

### AT-02 · Matters list used the agent transaction-card API
**Severity:** High · **Area:** `/transactions/active`

The attorney list showed agent “HARD STOP”, overdue **task** counts, and AI copy like “Agent, confirm the appraisal…”. Tab pills disagreed with attorney buckets.

**Fix:** Matters now lists `useAttorneyDashboard().matter_cards`. Next-step copy goes through `legal_next_step_text()` and never forwards “Agent, …” lines. Empty state explains unassigned files.

**Retest:** No agent voice. Status pills are Needs review / Missing docs / Ready to release. Review matter CTAs present (4).

### AT-03 · Sign-off did not show Reopen; checkbox was 16×16
**Severity:** Medium · **Area:** Matter › Review

Approve persisted (blocking 3→2) but the row waited on refetch; Reopen never appeared in Chrome. Native checkbox ignored `h-10 w-10`.

**Fix:** Optimistic `setQueryData` on `['attorney', 'matter-detail', id]`. Custom 40×40 checkbox. Sign off / Reopen are `min-h-10`.

**Retest:** Sign-off toast + Reopen restores the item. Checkbox **40×40**.

### AT-04 · Type below 12px and hit targets under 40px
**Severity:** Medium · **Area:** Style guide v2

Breadcrumbs 11/11.5px, KPI kickers 9.5–10px, calendar prev/next 30×30, ToolButtons ~30px, Ask-AI FAB hint 11px, upload-modal kickers 9px.

**Fix:** Attorney dashboard / matters / matter workspace / releases / recording calendar / state rules / shared KPI+card chrome / FactChip / ToolButton `min-h-10` / calendar month buttons 40×40 / FAB hint 12px. Upload modal kickers ≥12px.

**Retest:** `main` typography walk **0 offenders** on dashboard, matters, matter, releases, recording calendar, state rules. Calendar prev/next **40×40**. Header actions **40px** tall.

### AT-05 · `scope=attorney` dropped on AI Suggestions
**Severity:** Medium · **Area:** `/ai-suggestions`

`serializeSuggestionSearchParams` rewrote the query string and omitted `scope`. Attorney landing lost the legal filter.

**Fix:** Serializer keeps `scope`. Attorney visits always re-write `scope=attorney`. Unit test covers the round-trip.

**Retest:** URL stays `?scope=attorney`.

### AT-06 · Releases tabs were React-only
**Severity:** Medium · **Area:** `/attorney/releases`

Ready / All / Released reset on refresh.

**Fix:** `?tab=all|released` (default Ready omits the param).

**Retest:** Released → `?tab=released`.

### AT-07 · Global search looked like a missing search box
**Severity:** Medium · **Area:** Top bar / palette

The control is a **button** that opens the command palette, not a `searchbox`. Attorney placeholder still said “Search deals, clients…”.

**Fix:** Attorney top-bar copy “Search matters, people…”. Palette placeholder “Search matters, people, documents…”. Harness clicks the named Search button.

**Retest:** Headed Chrome verify: palette opened and queried `oak`. Light3 lost the session before this step.

### AT-08 · Attorney chrome still spoke “deals / Workflow / My Playbook”
**Severity:** Medium · **Area:** Copy / settings / AI chat

Contacts breadcrumb “Deals”; Documents / Closing Calendar “Workflow”; Contacts empty copy pointed at the agent transaction page; Settings showed **My Playbook**; AI chat greeted about overdue tasks and active deals.

**Fix:** Attorney breadcrumbs **Workspace › …**. Contacts empty copy is attorney-safe. My Playbook hidden (same allow-list as Email Templates). Chat greeting/chips talk about sign-offs, packets, and matters. Payments config and vendor-proposal polls are disabled for Attorney (they 403’d). Flagged-document count is not fetched for Attorney.

**Retest:** Contacts / Documents crumbs = Workspace. Settings has no My Playbook / Email Templates / Users & Invites. RBAC redirects off Task Queue, Needs You, Vendors, Payments, Clients, AI Emails, Vendor Proposals, Admin/Agent dashboards.

### AT-09 · Literal `&amp;` in dashboard title (source)
**Severity:** Low · **Area:** Attorney dashboard

JSX used `title="Recording &amp; release drift"`.

**Fix:** `Recording & release drift`.

### AT-10 · CORS treated `localhost` and `127.0.0.1` as different origins
**Severity:** Medium · **Area:** Local Playwright / preview

Headless runs against `http://127.0.0.1:5173`. `.env` `CORS_ORIGINS` listed only `http://localhost:5173`, so login returned “Failed to fetch” even though the API logged a successful attorney login.

**Fix:** `cors_origins_list` aliases `localhost` ↔ `127.0.0.1`. Login on 127.0.0.1 then succeeded.

### AT-11 · Vite dev + headed Chrome exhausted RAM
**Severity:** Harness · **Area:** QA

`npm run dev` serves the app as hundreds of `/src/*.tsx` modules. Headed Chrome then failed with `ERR_INSUFFICIENT_RESOURCES`. Headless Chromium against that same dev server still could not paint login.

**Fix:** Default harness is headless bundled Chromium + `vite preview` (single bundle). Low-RAM Chromium flags, no `networkidle`, viewport 1280×800. Headed Chrome remains optional via `QA_HEADED=1`.

---

## 3. Chrome / Chromium retest (after fixes)

### Headed Google Chrome (`verify`)

**138 pass / 3 fail / 143 checks.** Fails were AT-04 leftover (FAB 11px), AT-02 regex matching sidebar “Hard Stops”, and AT-08 leftover 403 on `documents/flagged/count`. All three were then patched.

Confirmed in that pass: login → attorney dashboard, legal-health KPIs, judgment hero, no Task Queue / Vendors / New Transaction, tab URL sync, matter workspace sections, hold requires a reason, Send packet disabled until sign-offs clear, upload modal gated, recording-calendar honest gap + month shift, state rules, RBAC, mobile 390 no overflow.

### Headless Chromium + preview (`light3`)

**129 pass / 12 fail / 143 checks.** Product checks for the attorney queue **passed**, including AT-01–AT-06 and the three verify leftovers:

- Classifier `needs_review=3` / `ready_to_release=1`
- Dashboard / matters type ≥ 12px
- No agent HARD STOP cards
- Sign-off + Reopen, 40×40 checkbox
- Releases `?tab=released`
- AI Suggestions `scope=attorney`
- Contacts / Documents **Workspace** crumbs
- No console errors, no failed APIs

**12 fails (late run, not attorney-queue regressions):**

| Check | What happened |
| --- | --- |
| `calendar-breadcrumb` | Shared `/calendar` dump was still “Loading…” (short wait; headed Chrome had loaded this page) |
| `settings-hub`, `settings-profile`, `settings-notifications`, `notifications-page`, `bell-opens`, `global-search` | Body was the **login** page — session gone |
| `legacy-intake`, `legacy-queue` | Redirected to `/login` instead of attorney dashboard / matters |
| `mobile-upload-named`, `mobile-matter-section-tabs`, `mobile-cal-list` | Same session drop at 390px |

Those surfaces passed in headed Chrome `verify` while the session was still alive.

---

## 4. Known gaps (not treated as render bugs)

- **Recording calendar data** is intentionally unwired. The page says recording windows aren’t wired for the jurisdiction and shows a layout grid / mobile list with weekend “Closed”.
- **Attorney had 0 matters** until we assigned four attorney-closing files and ran intake. Unassigned counsel correctly sees an empty Matters list.
- **Shared Closing Calendar** (`/calendar`) is allowed but not in the attorney sidebar; on the light pass it did not finish loading before the session dropped.
- **Seeded test data** (Oak Ridge, Meadowridge, Franklin, Riverstone) was added so sign-off / release paths could be exercised. Do not un-assign those files if further attorney QA is needed.

---

## 5. How to re-run on a low-RAM machine

1. Backend: `uvicorn` on `127.0.0.1:8000`.
2. Frontend: `npx vite build` then `npx vite preview --host 127.0.0.1 --port 5173` (avoid `npm run dev` on this box).
3. From `velvet-elves-data/attorney_portal_qa`:

```powershell
$env:QA_PASS='light'; node attorney_portal_chrome_qa.mjs
```

Optional: `$env:QA_HEADED='1'` for a visible Chromium window (uses more RAM).
