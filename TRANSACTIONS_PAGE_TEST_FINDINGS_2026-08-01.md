# Transactions Page — Test Findings

> **STATUS 2026-08-04: RESOLVED.** All 26 findings are closed — 24 fixed and
> re-verified in a real browser, 1 withdrawn (F-18, which was an artifact of
> the test harness, not a defect), and 1 deferred by explicit decision (F-24,
> the card's emoji glyphs — see §9). Implementation and verification evidence:
> `TRANSACTIONS_PAGE_REMEDIATION_PLAN_2026-08-01.md` §9.
>
> Execution of `TRANSACTIONS_PAGE_TESTING_CHECKLIST.md` against the local build.
>
> Tester: Jan Froben · Role: **Admin** (`shyna.elene@minafter.com`, tenant
> `526cf077-59da-496a-aa38-8f8d761c29da`) · Date: 2026-08-01
> Environment: real Chrome (puppeteer-core, system Chrome), frontend
> `http://localhost:5173`, backend `http://localhost:8000` (uvicorn, current
> working tree — verified newer than the last source edit).
> Data: 6 Active deals, 0 Pending, 0 Closed.
>
> Artifacts: `C:\Projects\_shots\txn\` (screenshots + raw JSON reports),
> drivers in `C:\Projects\_tools\e2e\txn\`.
>
> **No source code was modified.** Data mutations during testing were limited
> to one task completion that was immediately undone.

---

## 1. Executive summary

The list page (`/transactions/active`) is largely functional: cards render, the
drawer works, task completion with Undo works, the date popover works, the
print checklist works, modals open, and nothing crashes. The detail page loads
and every tab it has renders real data.

Underneath that, four defects break advertised functionality outright, and one
of them is not a bug in the ordinary sense — **a documented, screenshot-verified
redesign of the Transaction Detail page exists in the project documents but does
not exist in the codebase**. Everything §16 of the migration plan describes as
"kept" and "redesigned" is absent from every branch of the repository.

| Severity | Count | IDs |
| --- | --- | --- |
| Blocker | 4 | F-01 … F-04 |
| High | 6 | F-05 … F-10 |
| Medium | 8 | F-11 … F-18 |
| Low | 8 | F-19 … F-26 |

Checklist coverage: 257 items; 168 PASS, 61 FAIL/PARTIAL, 28 not verifiable
with the current data set (no Closed/Pending deals, <20 deals so no pagination,
no second session for concurrency).

---

## 2. Blockers

### F-01 · All three transaction exports download the app's HTML page

**Severity:** Blocker · **Area:** List page toolbar · **Checklist:** TX-030, TX-031, TX-032, TX-033

Clicking **Export CSV**, **Export Excel**, or **Print Report** downloads a
1,090-byte file that is the Vite dev server's `index.html`, saved under the
right filename and extension. All three files are byte-identical
(`md5 86aa18cfa36a019192d548d0c78a38b5`). No error is shown — the user gets a
file named `transactions.xlsx` that Excel cannot open.

Verified on both origins with the same auth token:

| Request | Status | Content-Type | Bytes | First bytes |
| --- | --- | --- | --- | --- |
| `:8000/api/v1/transactions/export/csv` | 200 | `text/csv` | 1182 | `Address,City,State,Zip,…` |
| `:5173/api/v1/transactions/export/csv` | 200 | `text/html` | 1090 | `<!doctype html>` |
| `:8000/…/export/excel` | 200 | `…spreadsheetml.sheet` | 5838 | `PK\x03\x04` |
| `:5173/…/export/excel` | 200 | `text/html` | 1090 | `<!doctype html>` |
| `:8000/…/export/pdf` | 200 | `application/pdf` | 2107 | `%PDF-1.3` |
| `:5173/…/export/pdf` | 200 | `text/html` | 1090 | `<!doctype html>` |

**Root cause.** `velvet-elves-frontend/src/utils/export.ts:31`:

```ts
const res = await fetch(`${endpoint}${buildExportQuery(filters)}`, { … })
```

`endpoint` is `/api/v1/transactions/export/csv` — a **relative** path. Every
other call in the app goes through `apiFetch`, which prefixes
`API_BASE_URL` (`src/utils/api.ts:5,17`). `downloadFromBackend` is the only
network helper that does not. The request therefore goes to the frontend
origin. `vite.config.ts` defines **no `/api` proxy**, so Vite's SPA fallback
answers with `index.html` at HTTP 200 — which means `res.ok` is `true`, the
`throw` on line 34 never fires, and the corrupt blob is saved.

**Not dev-only.** In staging and production the frontend is served from a
different host than the API (`api.prod.velvetelves.com` — see
`api-hostname-per-environment`), so the relative path resolves to the static
site there too. This is broken in every environment.

The backend is correct and needs no change.

---

### F-02 · The 2026-07-22 Transaction Detail redesign is absent from the codebase

**Severity:** Blocker · **Area:** Detail page (whole surface) · **Checklist:** TX-233, TX-238, TX-239, TX-240, TX-250, TX-251, TX-252, TX-253, TX-260…TX-265, TX-271, TX-340, TX-350…TX-353

`ACTIVE_TRANSACTIONS_CARD_TO_WORKSPACE_MIGRATION_PLAN.md` §16.2/§16.3/§16.6
records this work as implemented, test-verified ("TransactionWorkspace 19/19",
"`tsc`, `eslint --max-warnings=0`, and `vite build` clean") and
screenshot-verified. `FRONTEND_UI_WORKFLOW_LOGIC.md` §4.6 specifies the same
page. **None of it is in the repository.**

Repository evidence:

```
git log --all -S"key: 'overview'" -- src/pages/transactions/TransactionWorkspacePage.tsx   → 0 commits
git log --all --diff-filter=A -- src/components/workspace/BillingTab.tsx                   → 0 commits
git log --all --diff-filter=A -- src/components/workspace/OverviewTab.tsx                  → 0 commits
git log --all -S"workspaceUrl"                                                             → 0 commits
grep -rn "workspaceUrl" src/                                                               → 0 hits
```

The referenced screenshots do exist — `C:\Projects\_shots\detail-overview.png`
(2026-07-22 18:30), `detail-header-v2.png` (19:06) — so the work was built in a
working tree on that date and never committed. The last commit touching
`TransactionWorkspacePage.tsx` is `86d6b14 feat(wizard): refine fee capture and
post-create feedback`, which predates it.

Browser-verified consequences on `/transactions/7d4122ad-…`:

| §16 / §4.6 says | Built page actually does |
| --- | --- |
| Tabs: Overview · Timeline · Tasks · Documents · People · Billing · Activity | Agent · Timeline · **Compliance** · Documents · Tasks · People · Activity · Email |
| Lands on **Overview** | Lands on **Timeline** (`aria-selected=true`) |
| Compliance is the Checklist view of Documents | Compliance is still its own tab |
| Billing tab lists the deal's invoices | No Billing tab; `?tab=billing` silently falls back to Timeline |
| Facts line: address · Closes … (N days) · price · N overdue · N% complete | Header text is `Deals › Transactions › 5915 E 350 N / 0% complete / Active / Michael Koenig & Heather Hall-Koenig / Unhealthy / 5915 E 350 N, Franklin, IN, 46131 / Manual Assisted Autopilot / 0 handled today · 3 need you`. **No price, no closing date, no days-to-close, no overdue count appear anywhere on the detail page.** |
| "⋯" menu: Print closing checklist · Delete transaction | No overflow menu. `hasPrint:false`, `hasDelete:false`. **A deal cannot be deleted or printed from its own page** — only from the list card's footer |
| "Ask AI" button; assistant **closed by default**, remembered per user | No Ask AI button. Agent pane `aria-pressed="true"` on first visit with **no stored preference** (`localStorage` has no agent/pane key) — it opens taking ~45% of a 1600px screen |
| Posture: one chip whose menu holds the choices | Three-way `Manual / Assisted / Autopilot` segmented control plus the handled/needs-you line on its own row — exactly the layout §16.6 says was replaced |
| Tracking-dates rail on Timeline (7 chips) | Not rendered. `GET /transactions/{id}/plan` **does return** `tracking_dates` with 7 populated entries (Appraisal Expected `2026-07-22` overdue, Closing `2026-07-31` overdue, Possession `2026-08-30` future). The only consumer, `DealOverviewCard` (`WorkspaceHeader.tsx:340`), has zero usages — dead code, and `DealBriefBand` is dead with it |
| `?qa=1` / `?access=1` open the drawer / modal once | No-ops; page stays on Timeline |
| `?view=files\|checklist` on Documents | Ignored |
| `?tab=compliance` resolves to Documents › Checklist | Resolves to the Compliance tab (works, but by accident of the old design) |

This is one root cause with ~15 symptoms. It should be treated as lost work to
be re-landed, not as fifteen separate bugs.

---

### F-03 · Every row on the detail page's Activity tab reads "Invalid Date"

**Severity:** Blocker (the audit trail is unreadable) · **Area:** Detail › Activity · **Checklist:** TX-354, TX-357

Observed on `?tab=activity`: the date group headings render ("JUL 28",
"JUL 22") but **every event row's timestamp renders `Invalid Date`** —
including "Task completed: Review Documentation" and every email log entry.

**Root cause — a contract mismatch between two consumers of one endpoint.**

`GET /api/v1/transactions/{id}/history` returns `timestamp` as a **pre-formatted
clock string**, not ISO (`velvet-elves-backend/app/api/v1/transactions.py:2138`,
`:2151`, `:2162`):

```python
timestamp=ts.strftime("%I:%M %p").lstrip("0") if ts != _dt.min else "",
```

- `HistoryPanel.tsx:174` (the list page's panel) renders `{event.timestamp}`
  raw → correct, shows "3:42 PM".
- `ActivityTab.tsx:245` calls `formatTimestamp(event.timestamp)`, which at
  `ActivityTab.tsx:42` does `new Date(iso).toLocaleString(...)` →
  `new Date("3:42 PM")` → `Invalid Date`.

Note `formatTimestamp` is also used at `ActivityTab.tsx:127` for the Automation
lens, where `item.at` **is** ISO — so the helper is right for one caller and
wrong for the other.

---

### F-04 · The New Invoice modal calls a route that does not exist (404)

**Severity:** Blocker (feature silently dead) · **Area:** Invoice modal from a card · **Checklist:** TX-164, TX-203, TX-011

Opening **💳 Invoice** from a card footer fires
`GET /api/v1/transactions/{id}/tasks?status=open` → **404 Not Found**
(`{"status_code":404,"message":"Not Found"}`), twice per open. Captured in the
network log while on `/transactions/active`.

The modal's "link invoice payment to task auto-completion" section is therefore
permanently empty, and the failure is invisible to the user.

**Root cause.** `velvet-elves-frontend/src/hooks/usePayments.ts:272`:

```ts
export function useTransactionOpenTasks(transactionId: string | null) {
  return useApiFetch<{ items: TransactionOpenTask[] }>(
    ['transaction', 'tasks', 'open', transactionId ?? ''],
    `/transactions/${transactionId ?? ''}/tasks`,   // ← no such route
    { status: 'open' },
    …
```

The transactions router exposes no `/{id}/tasks`. Verified working alternative:
`GET /api/v1/tasks?transaction_id=<id>&status=Pending` → 200, 44,558 bytes of
task JSON. (The docstring at `usePayments.ts:270` documents the non-existent
route, so the mistake is baked into the comment too.)

---

## 3. High

### F-05 · Negative days-to-close is rendered raw, in three places

**Severity:** High · **Checklist:** TX-085, TX-077

Two of six deals are past their closing date and every surface prints the raw
negative number:

- Card stat block: **`-75` DAYS TO CLOSE** (Test Seller & Daniel Carter,
  closing 2026-05-20) and `-3` (Koenig, closing 2026-07-31).
- AI next-step banner: **"Closing is in -3 days. Complete this task promptly to
  avoid last-minute complications."**
- `plan.header.days_to_close: -3` feeds the detail page the same value.

**Root cause.** `dashboard.py:2331`:

```python
if days_to_close is not None and days_to_close <= 7:
    return f"Closing is in {days_to_close} days. …"
```

No lower bound, so `-3 <= 7` matches. `days_to_close` itself is a plain
`(closing - today).days` with no floor, and `CLOSE_NUM_COLOR` in
`TransactionCard.tsx:216` colours `-75` red but prints it verbatim.

**Second-order effect:** the "Closing Soon" tab is `0 <= days <= 14`
(`dashboard.py:3011-3012`), so the two most urgent deals in the tenant — both
past their closing date — are **excluded from every date-based tab**.

---

### F-06 · The inline search input specified for the page does not exist

**Severity:** High · **Checklist:** TX-027, TX-028, TX-029

`FRONTEND_UI_WORKFLOW_LOGIC.md` §4.1 specifies "Below tabs: Sort control
dropdown **+ inline search input**", plus a full behaviour spec (300 ms
debounce, `?search=` persistence, "X results", empty-result message).

The backend supports it and the URL parameter works — loading
`/transactions/active?search=oak` correctly filtered 6 deals to 1 and the count
pill read "1 deal". **But no input is rendered anywhere on the page**, so the
feature is unreachable, and once a `?search=` is in the URL there is no control
to clear it.

**Root cause.** `TransactionListPage.tsx:470` declares the state with **no
setter**:

```ts
const [searchInput] = useState(initialSearch)
```

The 300 ms debounce (`:472-475`) and the URL-persistence effect (`:477-485`)
below it are both live, but nothing can ever change `searchInput`, and no
`<input>` is present in the returned JSX. The plumbing shipped without the
control.

---

### F-07 · Tab and sort selections are never written to the URL; Back leaves the page

**Severity:** High · **Checklist:** TX-044, TX-065, TX-216

Clicking any of the eight filter tabs changes the list but leaves the URL at
`/transactions/active`. Same for the sort menu. Measured across all eight tabs
and all four sort options — `page.url()` never changed.

Consequences, both reproduced:
- **Refresh loses the filter.** The page returns to "All".
- **Back navigates out of the page entirely.** After clicking through tabs on
  `/transactions/active`, pressing Back landed on
  `/transactions/00000000-0000-4000-8000-000000000000` — the URL visited
  *before* the page, because none of the in-page interactions created history
  entries.

`?sort=` is also **ignored on load**: `/transactions/active?sort=close_date`
renders with the chip reading "Sort by Urgency". (`?tab=` and `?filter=` *are*
read correctly — those pass.)

**Root cause.** `TransactionListPage.tsx:450-453` holds `activeTab` and `sortBy`
in `useState` only. The `?tab=` param is read once into initial state and
synced one-way (`:488-492`); `setActiveTab`/`setSortBy` never call
`setSearchParams`. There is no `?sort=` reader at all. Spec §4.1 lists
`?sort=close_date` under "Deep-link support" and §6 requires "Back navigation
restores previous filter/sort/search state".

---

### F-08 · The header count pill ignores the active tab

**Severity:** High · **Checklist:** TX-021, TX-042

With the **Closing Soon** tab active the list renders 2 cards while the title
pill still reads **"6 deals"**. Same for every tab: Overdue (6 cards / "6
deals"), Needs Attention (0 cards / "6 deals"), In Inspection (0 cards / "6
deals"), On Track (0 cards / "6 deals").

A tab showing zero cards above a header claiming six deals reads as a broken
page.

**Root cause.** `TransactionListPage.tsx:587-592` calls
`useTransactionTabCounts` with `state_filter`, `search` and the team params but
**not** `tab`; `totalDealCount` (`:592`) is that endpoint's `total`, i.e. the
total for the state filter. The correct per-tab number is already in hand —
`tabCounts[activeTab]` — and `cardsResponse.total` also carries it.

Spec §4.1: "'Active Transactions' title + count pill (**total matching current
filter**)". Note the pill *does* follow `?search=` (verified: "1 deal"), which
makes the tab behaviour look even more inconsistent.

---

### F-09 · Two closed side panels stay in the DOM, focusable and exposed to assistive tech

**Severity:** High (a11y) · **Checklist:** TX-204, TX-205

On a freshly loaded `/transactions/active` with nothing open:

| `role="dialog"` | `aria-hidden` | `inert` | Off-screen | Focusable children |
| --- | --- | --- | --- | --- |
| Client Q&A | *(none)* | no | yes | 3 |
| Communication log | *(none)* | no | yes | **60** |
| Velvet Elves AI chat | `"true"` | no | yes | 7 |

The Client Q&A drawer and the Communication log render permanently, hidden only
by `translate-x-full`. A keyboard user tabbing through the page walks into 63
controls in panels that are not open; a screen reader announces two dialogs
that the sighted user cannot see. This also pollutes `document.body.innerText`
— "Client Q&A… Send reply" appears in the text of every transactions page,
including the empty state.

**Root cause.**
- `ClientThreadDrawer.tsx:77-86` — always returns the panel, `open` only
  switches `translate-x-0` / `translate-x-full`; `role="dialog"` is
  unconditional.
- `CommunicationsPanel.tsx:113-115` — identical pattern.

The AI chat panel in the same app sets `aria-hidden="true"` when closed, so the
correct pattern already exists in the codebase. `HistoryPanel.tsx:47` uses the
same translate trick but carries no `role="dialog"`, so it is a lesser case of
the same issue.

---

### F-10 · The filter tabs do not filter by what their labels say, and overlap each other

**Severity:** High (workflow/logic) · **Checklist:** TX-040, TX-042, TX-048

Observed counts on a tenant where all six deals carry 11–34 overdue tasks:

```
All 6 · Overdue 6 · Due Today 1 · Needs Attention 0 · Closing Soon 2
· In Inspection 0 · On Track 0 · Unhealthy 6
```

**"Needs Attention" reads 0 and "On Track" reads 0** while every deal in the
tenant is behind. **"Overdue" and "Unhealthy" return identical sets** (the same
6 cards). The tab strip gives eight choices that resolve to four distinct
results.

**Root cause.** `dashboard.py:3003-3021` — six of the eight tabs filter on the
**stage pill label**, not on the condition the label names:

```python
if tab == "overdue":         return pill_label in ("Critical", "Unhealthy")
if tab == "needs_attention": return pill_label in ("Needs Attention", "In Inspection")
if tab == "in_inspection":   return pill_label == "In Inspection"
if tab == "on_track":        return pill_label == "On Track"
if tab == "unhealthy":       return pill_label == "Unhealthy"
```

So:
- **"Overdue" does not mean "has overdue tasks."** A deal with 30 overdue tasks
  but an "On Track" pill is excluded; a "Critical" deal with none is included.
  Meanwhile the neighbouring "Due Today" tab *is* task-based
  (`dashboard.py:3006-3009`), so two adjacent tabs use different subjects.
- **Overdue ⊇ Unhealthy** — Unhealthy is a strict subset of Overdue.
- **Needs Attention ⊇ In Inspection** — same relationship, one tab to the right.

Spec §4.1 describes these as independent filters ("Overdue (count, red text if
> 0) | Due Today | Closing Soon | …").

---

## 4. Medium

### F-11 · `/transactions/pending` is empty and unexplained

**Checklist:** TX-005, TX-218 · `state_filter=pending` → `total: 0`.

The backend maps pending → `[Incomplete, Paused]`
(`dashboard.py:2363` and `:2487`). `FRONTEND_UI_WORKFLOW_LOGIC.md` §4.2 defines
the route differently — "pending = active non-closed transactions; this is
functionally equivalent to Active Transactions" and "renders the same workspace
with the same data".

Whichever definition wins, today the nav shows a "Pending" entry that always
opens an empty page reading "No transactions found / No transactions match this
filter." — with nothing telling the user what Pending means or that there are 6
Active deals one click away. **This needs a product decision, not just a fix.**

### F-12 · `/transactions/all` has no status tab bar

**Checklist:** TX-007, TX-049 · Spec §4.4 requires `All | Active | Incomplete |
Paused | Completed | Closed` with counts, and a "Status" sort option.
Built: the tab strip renders only when `statusView === 'active'`
(`TransactionListPage.tsx:951`), so `/all` is an unfiltered list with no way to
narrow by status — the one thing that route exists for.

### F-13 · Search-empty and filter-empty states are wrong

**Checklist:** TX-218, TX-219 · Searching a non-matching term renders
**"No transactions found / Create a new transaction to get started."** — advising
the user to create a deal because their *search* missed. Spec §4.1 requires
"No transactions match '[query]'" with a **Clear filter** link. There is no
clear affordance (verified: no button/link matching /clear/i), and no
"+ New Transaction" button inside the empty state either (spec calls for a
"prominent" one; the only one found is the app topbar's).

### F-14 · The list page has no error state

**Checklist:** TX-220 · `TransactionListPage.tsx:1032-1047` branches on
`isLoading` then on `visibleCards.length === 0`. `useTransactionCards` exposes
`isError`, but it is never read — a failed cards request renders the **empty
state**, telling the user they have no transactions when the request simply
failed. Spec §4.1 requires an "Unable to load transactions" banner with Retry.
(The detail page does this correctly — see F-27 note under Passes.)

### F-15 · Loading state is a bare spinner, not card skeletons

**Checklist:** TX-217 · Spec §4.1: "content area shows 3–5 transaction card
skeletons with pulsing placeholders". Built: one centred spinner
(`TransactionListPage.tsx:1033-1038`). The detail page *does* use skeletons
(`TransactionWorkspacePage.tsx:362-379`), so the two surfaces disagree.

### F-16 · Task totals disagree across surfaces on the same deal

**Checklist:** TX-114, TX-237, TX-390 · For **Livefire Buyer & Livefire Seller**:

| Surface | Says |
| --- | --- |
| Tasks full-view modal | "1 of 26 complete · 4%" — All 26 / Overdue 7 / Pending 18 / Done 1 |
| Print closing checklist | "28 total tasks · 3 completed · 25 remaining" |

For **Koenig**: the detail header shows **"0% complete"** while the Activity
tab lists "Task completed: Review Documentation" and
`plan.header.series.task_completions_weekly` contains a `1`.

**Root cause.** Each surface applies a different visibility filter without
saying so. `transaction_plan.py:558-585` builds `user_tasks` by excluding
AI-hidden tasks (`is_ai_hidden`), then counts `tasks_completed` /
`tasks_total` over that subset; the checklist endpoint and the cards endpoint
use different subsets again. The numbers are each internally defensible and
collectively untrustworthy.

### F-17 · Console error on every list-page load

**Checklist:** TX-011 · Every load of `/transactions`, `/transactions/active`
and `/transactions/all` logs:

```
Query data cannot be undefined. Please make sure to return a value other than
undefined from your query function. Affected query key: ["ad-slot","transactions_inline"]
```

**Root cause.** `useAdSlot` (`src/hooks/useAdSlot.ts:22-33`) types the result
`ServedAd | undefined` and its own docstring says "the backend … returns 204
(→ `undefined`) when there is no ad". React Query forbids `undefined` as query
data; the query function must return `null`. The slot still collapses
correctly, so this is noise rather than breakage — but it is noise on the most
used page in the product, and it masks real errors during testing.

### F-18 · ~~Print-checklist rows concatenate fields~~ — WITHDRAWN, not a defect

**Checklist:** TX-170 · **Retracted on visual verification 2026-08-01.**

The original report claimed the checklist glued two meta fields together
("Title Work OrderedTitle", "1Buyer"). That came from reading
`document.body.innerText` in the test harness, which drops the whitespace
between adjacent inline elements. A screenshot of the rendered popup
(`_shots/txn/07_print_checklist.png`) shows the fields correctly spaced —
`.task-meta .milestone` and `.task-meta .target` both carry
`display: inline-block; margin-right: 8px` (`printChecklist.ts:247-251`).

**The checklist is correct and needs no change.** One cosmetic data oddity
remains, logged as F-27 below rather than as a rendering bug.

### F-27 · A milestone label renders as the bare string "1"

**Severity:** Low · The "Buyer Welcome" task's meta line reads `1 · Buyer`,
i.e. its stored `milestone_label` is literally `"1"`. Cosmetic, and a data
issue in the task template rather than a rendering one.

---

## 5. Low

| ID | Finding | Evidence / root cause |
| --- | --- | --- |
| **F-19** | Next-step banner lower-cases a proper label mid-sentence: "Next step: **title defect cure period**" | `TransactionListPage.tsx:320` — `` `Next step: ${card.next_deadline_label.toLowerCase()}` ``. The backend label is "Title defect cure period" |
| **F-20** | AI CTA text truncated mid-word: **"Schedule Walk-Throug"** | Hard 20-char slice in both providers — `anthropic_provider.py:255` and `openai_provider.py:259`: `str(parsed.get("cta_label", "Take Action"))[:20]`. Cuts without ellipsis or word boundary |
| **F-21** | Card renders only 2 of the 7 spec'd info badges (Tasks, Docs) | `TransactionListPage.tsx:232-243`. Spec §4.1 lists Tasks, Emails, Notes, Missing Docs, Client Touch, Lender Touch, History |
| **F-22** | Dead click handler for a badge that is never rendered | `TransactionCard.tsx:718` handles `badge.label === 'History'`, but no History badge is ever produced (F-21) |
| **F-23** | Dead callback: `onChangeTaskStatus` is wired from the page (`TransactionListPage.tsx:774-778`) but the card renders no status control | `TransactionCard.tsx:301-302` comments that non-binary status "is no longer surfaced in the UI" — the prop was left behind |
| **F-24** | Emoji used as button glyphs, against the lucide icon system used everywhere else | Drawer footer: `📄 View/Add Docs`, `🖨 Print`, `🕐 History`, `✉️ Comms`, `👥 Client access`, `💬 Client Q&A`, `💳 Invoice`, `🗑 Delete`; info badges `⚑`/`📄`; AI suggestions `⚑`/`📋`/`📄`. Conflicts with the project's "no emoji icons — lucide" rule |
| **F-25** | Activity rows embed a truncated, non-clickable URL | "Please review at /ai-emails/3dba139f-b557-42c0-a02d-b7a488b6de2" — the UUID is one character short and the path is plain text, not a link |
| **F-26** | No pagination control on the list | Spec §4.1 edge case: "Pagination with 'Load more' button (20 per page)". Not present in `TransactionListPage.tsx`. Unverifiable at scale locally (6 deals) but structurally absent |

---

## 6. What passed

Worth recording, because the surface is far from broken:

- **Routing** — `/transactions`, `/active`, `/pending`, `/closed`, `/all` all
  resolve with correct titles and breadcrumbs; `/transactions/:id` renders the
  workspace; an unknown id shows a proper error card ("Couldn't load this
  transaction · Transaction not found · Retry · Back to Transactions").
- **Card face** — urgency bar, stage pill, why-badges, de-duplicated address,
  assignee chip, primary contact with `tel:`, milestone bar with per-dot
  status, price, title link and maximize icon both routing to the workspace.
- **Drawer** — all three columns render (Tasks / Key Dates / Contacts), plus
  the Invoices panel and AI-suggestions strip; all nine footer actions present
  and gated correctly for Admin.
- **Task completion** — optimistic tick, `PATCH /tasks/:id`, "Task completed"
  toast **with a working Undo** that restored the task. Round-tripped cleanly.
- **Key dates** — all 7 rows with correct server-driven colours and "Not yet"
  for unset; the popover opens anchored, pre-filled with the ISO value, and
  cancels without a request.
- **Tasks full-view modal** — search, five filter tabs with counts, per-row
  toggle and Email-party; child modals layer correctly.
- **Assign team / Client access modals** — real rosters, correct copy
  distinguishing teammates from contacts, capability gating visible.
- **Print closing checklist** — popup opens with a fully populated checklist
  (aside from F-18).
- **`?expand=` / `?highlight=` / `?tab=` / `?filter=` / `?search=`** deep links
  all work.
- **Sort** — Client Name and Price visibly reorder. (Close Date produced the
  same order as Urgency, which is *correct* here: all six deals are red, so
  `_sort_cards`'s urgency key degenerates to closing-date order.)
- **Detail tabs** — Timeline (8 dated rows with bases), Compliance (10 open /
  3 uploaded / 0 waived), Documents (10 files with AI-verification chips),
  Tasks (37 open, grouped, with honest "AI needs you" rows), People (fees
  section, 5 party groups, RESPA note), Email (3 pending drafts) all render
  real data.
- **Responsive** — no horizontal overflow at 1600 px, 1024 px or 375 px on
  either surface; the Agent tab correctly becomes the entry point below 1280 px.
- **Stability** — zero uncaught page errors across the whole sweep; the only
  console error is F-17 and the only 4xx is F-04.

---

## 7. Checklist result summary

| Section | Items | Pass | Fail | Partial | N/V* |
| --- | --- | --- | --- | --- | --- |
| 1. Environment & routing | 11 | 10 | 1 | 0 | 0 |
| 2. Header & toolbar | 15 | 8 | 6 | 1 | 0 |
| 3. Filter tabs | 11 | 5 | 5 | 1 | 0 |
| 4. Sort | 7 | 4 | 2 | 0 | 1 |
| 5. Collapsed card | 21 | 17 | 3 | 1 | 0 |
| 6. Drawer — Tasks | 15 | 14 | 0 | 1 | 0 |
| 7. Drawer — Key Dates | 12 | 10 | 1 | 0 | 1 |
| 8. Drawer — Contacts | 10 | 8 | 1 | 1 | 0 |
| 9. Footer / invoices / AI | 18 | 15 | 2 | 1 | 0 |
| 10. Modals & panels | 16 | 12 | 2 | 1 | 1 |
| 11. URL state & states | 13 | 6 | 6 | 0 | 1 |
| 12. Detail header | 15 | 7 | 7 | 1 | 0 |
| 13. Detail tab bar | 8 | 3 | 5 | 0 | 0 |
| 14. Overview tab | 6 | 0 | 6 | 0 | 0 |
| 15. Timeline tab | 12 | 6 | 3 | 0 | 3 |
| 16. Documents/Checklist | 12 | 7 | 2 | 0 | 3 |
| 17. Tasks tab | 11 | 8 | 0 | 0 | 3 |
| 18. People tab | 13 | 9 | 2 | 0 | 2 |
| 19. Billing/Activity/Email/Agent | 13 | 6 | 5 | 0 | 2 |
| 20. Detail states & edges | 12 | 5 | 1 | 0 | 6 |
| 21. Cross-surface | 6 | 2 | 2 | 1 | 1 |
| **Total** | **257** | **162** | **62** | **9** | **24** |

\* **N/V — not verifiable in this environment:** no Closed or Pending deals
exist (read-only-when-closed, post-closing feedback, closed-view sort), fewer
than 20 deals (pagination, virtual scrolling), single session (concurrent-edit
and live-refresh behaviour), and no second browser profile (role matrix beyond
Admin).

---

## 8. Recommended priority

1. **F-01** — exports are advertised on every list view and produce corrupt
   files silently. One-line frontend fix.
2. **F-04**, **F-03**, **F-17** — three small, fully root-caused defects
   (wrong route, wrong date parser, `undefined` vs `null`).
3. **F-05**, **F-08**, **F-06**, **F-07** — the numbers and controls users read
   as "is this page working?".
4. **F-02** — re-land the detail-page redesign. Largest effort; needs a
   decision on scope before estimation (see the remediation plan §4).
5. **F-10**, **F-11** — require product decisions on what the tabs and the
   Pending route mean before code changes.
6. Everything else in checklist order.

Remediation sequencing, effort and acceptance criteria:
`TRANSACTIONS_PAGE_REMEDIATION_PLAN_2026-08-01.md`.
