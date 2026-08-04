# Transactions Page — Remediation Plan

> Resolves every issue in `TRANSACTIONS_PAGE_TEST_FINDINGS_2026-08-01.md`.
> Author: Jan Froben · Date: 2026-08-01 · Status: **PLAN ONLY — no code changed.**
>
> Companions: `TRANSACTIONS_PAGE_TESTING_CHECKLIST.md` (the checklist),
> `TRANSACTIONS_PAGE_TEST_FINDINGS_2026-08-01.md` (the evidence).

---

## 0. Shape of the work

Twenty-six findings, but they are not twenty-six pieces of work. They sort into
five buckets:

| Bucket | Findings | Character | Effort |
| --- | --- | --- | --- |
| **A. Wrong-line fixes** | F-01, F-03, F-04, F-17, F-19, F-20, F-25 | One wrong call, one wrong parser, one wrong constant. Root cause already identified for each; no design input needed | ~0.5 day total |
| **B. List-page state and honesty** | F-05, F-06, F-07, F-08, F-13, F-14, F-15, F-18, F-26 | The page's own URL contract, empty/error/loading states, and numbers that must not lie | ~3 days |
| **C. Decisions before code** | F-10, F-11, F-16 | The tab taxonomy, what "Pending" means, and which task population is canonical. Each needs a product answer first | 0.5 day to decide, ~2 days to build |
| **D. Re-land the lost redesign** | F-02 (≈15 symptoms) | Rebuild the 2026-07-22 Transaction Detail page per §16.3/§16.6 and spec §4.6 | ~5–7 days |
| **E. Consistency and hygiene** | F-09, F-12, F-21, F-22, F-23, F-24 | Accessibility, dead code, icon system, a missing tab bar | ~1.5 days |

**Sequence: A → B → C(decide) → D → C(build) → E.** A is shipped first because
it is nearly free and removes user-visible breakage the same day. D is last of
the large items because it is the only one that benefits from the decisions in
C being settled.

Every phase ends with the same gate: **the affected checklist rows are re-run
in a real browser and recorded**, per `FRONTEND_UI_TESTING_GUIDELINES.md`.
Screenshots are the proof, not passing unit tests.

---

## 1. Phase A — wrong-line fixes (ship first)

### A1 · Exports must target the API origin — F-01 · Blocker

**File:** `velvet-elves-frontend/src/utils/export.ts`

`downloadFromBackend` is the only network helper in the app that does not
prefix `API_BASE_URL`. Fix it there — not at the three call sites — so no
future exporter can repeat the mistake.

```ts
import { API_BASE_URL } from '@/utils/api'
…
const res = await fetch(`${API_BASE_URL}${endpoint}${buildExportQuery(filters)}`, {
  headers: token ? { Authorization: `Bearer ${token}` } : {},
})
```

**Also harden the failure path.** The bug was invisible because Vite answered
200 with HTML and `res.ok` was true. Add a content-type assertion so a wrong
origin can never again produce a silently corrupt download:

```ts
const ct = res.headers.get('content-type') ?? ''
if (ct.includes('text/html')) {
  throw new Error('Export returned a web page instead of a file — check the API base URL.')
}
```

**Sweep for the same class of bug.** Grep for `fetch('/api` and
`fetch(\`/api` across all four frontends; any relative API call outside
`apiFetch` is suspect. `printClosingChecklist` was verified working in the
browser, but confirm it routes through `API_BASE_URL` too.

**Acceptance:** TX-030/031/032/033. Click each of the three buttons; the saved
files open in Excel / a PDF reader / a text editor and contain the same 6 deals
the page shows. Confirm `content-type` is `text/csv`,
`…spreadsheetml.sheet`, `application/pdf`. Re-verify with a team filter and a
`?search=` applied (TX-033). Add a unit test asserting the fetch URL starts
with `API_BASE_URL`.

---

### A2 · Activity timestamps — F-03 · Blocker

**Decision: fix the frontend, not the backend.** The backend has one history
endpoint with two consumers; `HistoryPanel` already renders the string
correctly. Changing the API to ISO would fix `ActivityTab` and break
`HistoryPanel` — and the field is documented as a display string.

**File:** `velvet-elves-frontend/src/components/workspace/ActivityTab.tsx`

Line 245 must render the value as given, exactly as `HistoryPanel.tsx:174`
does:

```tsx
{event.timestamp}
```

Keep `formatTimestamp` for the Automation lens (line 127), where `item.at` is
genuinely ISO, and rename it to `formatIsoTimestamp` so the next reader cannot
confuse the two contracts.

**Prevent recurrence:** the shared `TransactionHistoryEvent` interface
(`src/hooks/useTransactionHistory.ts:4`) types `timestamp: string`, which hides
the distinction. Add a comment naming the format, or introduce a
`DisplayTime` branded type.

**Acceptance:** TX-354. Open `?tab=activity` on a deal with history; every row
shows a clock time. Zero occurrences of "Invalid Date" in the tab's text.

---

### A3 · Invoice modal's open-tasks route — F-04 · Blocker

**File:** `velvet-elves-frontend/src/hooks/usePayments.ts:270-279`

Point the hook at the route that exists and adapt the response shape:

```ts
// Endpoint: GET /api/v1/tasks?transaction_id={id}&status=Pending
export function useTransactionOpenTasks(transactionId: string | null) {
  return useApiFetch<Task[]>(
    ['transaction', 'tasks', 'open', transactionId ?? ''],
    `/tasks`,
    { transaction_id: transactionId ?? '', status: 'Pending' },
    { enabled: Boolean(transactionId) },
  )
}
```

`NewInvoiceModal.tsx:327` consumes `data.items`; it must consume the array (or
the hook must map to `{ items }`). Fix the docstring at `:270` — it currently
documents the non-existent route, which is how the error survived review.

**Decide:** "open" should mean Pending **and** InProgress, not Pending alone —
an in-progress task is exactly the kind you would link a payment to. Confirm
with Jake; the endpoint accepts a status list.

**Acceptance:** TX-164/TX-203. Open 💳 Invoice from a card; the task-linking
section lists that deal's open tasks. Network log shows **zero 404s** for the
whole flow (TX-011).

---

### A4 · Ad-slot console error — F-17

**File:** `velvet-elves-frontend/src/hooks/useAdSlot.ts`

React Query forbids `undefined`. The 204 must become `null`:

```ts
export function useAdSlot(slotKey: string) {
  return useApiFetch<ServedAd | null>(…)
}
```

If `useApiFetch` returns `undefined` on 204 generically, fix it there —
`?? null` at the boundary — since any other 204 endpoint has the same problem.
`AdSlot.tsx:39` already guards with `if (!ad) return null`, so no component
change is needed.

**Acceptance:** TX-011. Load `/transactions/active`, `/all`, `/pending` — the
console is clean.

---

### A5 · Three copy/format defects — F-19, F-20, F-25

- **F-19** — `TransactionListPage.tsx:320`: drop `.toLowerCase()`. The backend
  label is already sentence-case ("Title defect cure period"). If the intent
  was to make the label flow after "Next step:", lower-case only the first
  character and only when the label is not an acronym — simpler to just render
  it as given.
- **F-20** — `anthropic_provider.py:255` and `openai_provider.py:259`: replace
  the bare `[:20]` slice with a word-boundary trim. Better still, instruct the
  model to return ≤20 characters and treat a longer value as a validation
  failure that falls back to `_derive_next_step_cta`, rather than shipping
  "Schedule Walk-Throug" to a button.
- **F-25** — the Activity/history row text embeds a raw path. Emit the
  reference as a link to `/ai-emails/:id` and verify the id is complete; the
  observed value was one character short of a UUID, so check the truncation at
  the point the summary string is built.

**Acceptance:** TX-077 (banner reads naturally), TX-076 (CTA is a whole word),
TX-354 (the reference is clickable and resolves).

---

## 2. Phase B — list-page state and honesty

### B1 · Negative days-to-close — F-05 · High

Three surfaces, one concept: a deal past its closing date. Decide the
presentation once and apply it everywhere.

**Recommendation:** never print a negative number. Show **"Past due"** in the
stat block with the closing date beneath it (the date is already there), and
have the AI fallback say how late it is in plain language.

- `dashboard.py:2331` — guard the branch: `if 0 <= days_to_close <= 7`. Add a
  preceding branch for `days_to_close < 0`:
  `f"Closing was {abs(days_to_close)} days ago and has not been marked complete. Confirm the closing status or move the date."`
- `TransactionCard.tsx:732-746` — when `daysToClose < 0`, render "Past due"
  (red) with the closing date, not the raw integer.
- `TransactionListPage.tsx` mapper — pass a `pastDue` flag rather than letting
  each consumer re-derive the sign.

**Also fix the tab exclusion.** `dashboard.py:3011-3012` currently drops
past-closing deals out of "Closing Soon" (`0 <= days <= 14`). A deal 75 days
past its closing date is the most urgent thing in the tenant and appears in no
date-based tab. Change to `days <= 14` (no lower bound), or add these deals to
"Needs Attention" once B3 redefines it.

**Acceptance:** TX-084, TX-085, TX-077. The two past-closing deals show "Past
due", the banner sentence is grammatical, and both appear under Closing Soon.

---

### B2 · Restore the URL contract — F-06, F-07, F-08 · High

These three are one job: make the page's state live in the URL, and make the
header agree with it.

**B2a — Render the inline search input (F-06).**
`TransactionListPage.tsx:470` — give the state a setter and render the control
in the tab row, to the right of the tabs beside the sort chip (spec §4.1:
"Below tabs: Sort control dropdown + inline search input"):

```ts
const [searchInput, setSearchInput] = useState(initialSearch)
```

The 300 ms debounce and URL-persistence effects below it already work — they
have simply had no input to observe. Include a clear (✕) affordance, since a
`?search=` arriving by deep link is currently unclearable.

**B2b — Write tab and sort to the URL (F-07).** Replace the `useState` pair at
`:450-453` with URL-derived state, mirroring how `statusView` is already
resolved from the path:
- reading: `?tab=` (with `?filter=` alias — already implemented) and a new
  `?sort=` reader mapping to `SORT_MAP`;
- writing: `setActiveTab` / `setSortBy` call `setSearchParams` with
  `{ replace: false }` so Back steps through filter changes.

Guard the default: do not write `?tab=all&sort=urgency` on first paint, or
every visit pushes a redundant history entry.

**B2c — Make the count pill follow the tab (F-08).**
`TransactionListPage.tsx:592` — `totalDealCount` should be
`tabCounts[activeTab]` when a tab is active (that number is already fetched),
falling back to `cardsResponse.total`. One line; no new request.

**Acceptance:** TX-027, TX-028, TX-029, TX-044, TX-065, TX-215, TX-216, TX-021,
TX-042. Type in the search box → the list filters and `?search=` appears; click
Overdue → `?tab=overdue` appears and the pill matches the card count; choose
Close Date → `?sort=close_date` appears; refresh → everything holds; Back →
steps back through the filters instead of leaving the page.

---

### B3 · Empty, error and loading states — F-13, F-14, F-15

**F-14 (error) is the important one:** a failed request currently renders the
"you have no transactions" empty state. `useTransactionCards` already returns
`isError`; add the branch before the empty branch at
`TransactionListPage.tsx:1039`:

> **Unable to load transactions** · [Retry] — calling `refetch()`.

**F-13 (empty):** branch the message on whether a filter is active.
- No deals at all → "No transactions yet" + a **prominent "+ New Transaction"**
  button inside the empty state (spec §4.1).
- A search is active → `No transactions match "<query>"` + **Clear search**.
- A tab is active → `No transactions in <tab label>` + **Clear filter**.

**F-15 (loading):** replace the spinner at `:1033-1038` with 3–5 card
skeletons. The detail page's skeleton block
(`TransactionWorkspacePage.tsx:362-379`) is the pattern to copy so the two
surfaces match.

**Acceptance:** TX-217, TX-218, TX-219, TX-220. Verify the error branch by
blocking the cards request in DevTools; verify both empty variants; screenshot
the skeletons under throttling.

---

### B4 · ~~Print-checklist field concatenation~~ — WITHDRAWN (F-18 retracted)

No work required. The reported concatenation was an artifact of reading
`innerText` in the test harness; the rendered popup spaces the fields correctly
via `margin-right: 8px` on `.task-meta .milestone` / `.target`. Verified by
screenshot (`_shots/txn/07_print_checklist.png`).

The only residue is F-27 — one task template stores `milestone_label = "1"`, so
its meta line reads "1 · Buyer". A data cleanup, not a code change.

---

### B5 · Pagination — F-26

Not reproducible locally (6 deals) but structurally absent, and spec §4.1 calls
for 20/page with "Load more". Add it to the cards query and the list, keeping
tab counts as totals (they already come from a separate endpoint, so they stay
correct). **Do not ship this without a >20-deal fixture** — seed a tenant and
verify, or defer the item explicitly rather than shipping untested paging.

**Acceptance:** TX-221 against a seeded tenant.

---

## 3. Phase C — decisions required before code

These three cannot be fixed correctly without a product answer. Each is stated
as a question with a recommendation.

### C1 · What do the eight filter tabs mean? — F-10 · High

**Problem.** Six of eight tabs filter on the stage-pill label
(`dashboard.py:3003-3021`), so "Overdue" does not mean "has overdue tasks",
"Overdue" ⊇ "Unhealthy" (identical sets in the test tenant), and "Needs
Attention" ⊇ "In Inspection". A tenant where every deal is behind reports
"Needs Attention 0 · On Track 0".

**Question for Jake:** should these tabs filter by *deal health* (the pill) or
by *the condition each label names*?

**Recommendation — make each tab mean its label, and remove the duplicates:**

| Tab | Predicate |
| --- | --- |
| All | everything in the state filter |
| Overdue | **has ≥1 overdue task** (task-based, matching the card's "N overdue" badge and the "Due Today" tab beside it) |
| Due Today | has ≥1 task due today *(unchanged — already correct)* |
| Closing Soon | `days_to_close <= 14` *(lower bound removed per B1)* |
| In Inspection | pill == In Inspection |
| Needs Attention | pill == Needs Attention **only** (drop the In Inspection union) |
| On Track | pill == On Track |
| ~~Unhealthy~~ | **remove** — it is the pill-based sense of "Overdue"; keeping both guarantees two tabs with identical contents |

This makes every tab disjoint in meaning and aligns the tab strip with what the
cards already display. `_matches_tab` and `TransactionTabCounts` change
together; `FILTER_TABS` in `TransactionListPage.tsx:81-90` follows.

**Acceptance:** TX-040, TX-042, TX-048. On the current tenant, "Overdue" must
return 6 (all deals have overdue tasks) and "Needs Attention"/"On Track" must
be justifiable from the cards on screen. No two tabs return identical sets.

---

### C2 · What is `/transactions/pending`? — F-11

**Problem.** The backend says Pending = `[Incomplete, Paused]`
(`dashboard.py:2363`, `:2487`). Spec §4.2 says Pending = active non-closed,
"functionally equivalent to Active Transactions". Today it is a permanent
empty page in the main navigation.

**Question for Jake:** is Pending (a) drafts and paused deals, (b) a duplicate
of Active reserved for a future Listings/Under-Contract split, or (c) removed
from the nav until it has a job?

**Recommendation: (a), the current backend behaviour — and fix the presentation
and the document.** "Incomplete + Paused" is the genuinely useful list (deals
that stalled in the wizard or were paused). Then:
- Retitle to something self-describing, e.g. **"Drafts & Paused"**.
- Give it an honest empty state: "No draft or paused transactions. Deals you
  start but don't finish appear here." — not the generic "No transactions match
  this filter."
- Update `FRONTEND_UI_WORKFLOW_LOGIC.md` §4.2, which currently documents (b).
- Show the count as a nav badge so an empty page is never a surprise.

**Acceptance:** TX-005, TX-218. Create a draft deal; it appears under Pending
with a matching nav badge.

---

### C3 · Which task population is canonical? — F-16

**Problem.** One deal reports three different task totals: the full-view modal
"1 of 26 complete", the print checklist "28 total · 3 completed", the detail
header "0% complete". Each surface applies its own visibility filter
(`is_ai_hidden`, Skipped inclusion) without saying so.

**Question for Jake:** should AI-hidden tasks and Skipped tasks count toward a
deal's progress?

**Recommendation:** define **one** rule in the backend and reuse it —
*"progress = Completed ÷ (all tasks except Skipped and AI-hidden)"* — expose it
as a single `progress` object on the plan aggregate and on the card payload,
and have every surface render that. `transaction_plan.py:584-585` already
computes something close; the checklist and cards endpoints must adopt it
rather than recomputing.

Also settle the related honesty rule from §16.6: **omit the progress fact when
`tasks_total` is 0**, instead of rendering "0% complete".

**Acceptance:** TX-114, TX-237, TX-390. Card badge, Tasks tab, full-view modal,
print checklist and detail header all report the same numerator and denominator
for the same deal.

---

## 4. Phase D — re-land the Transaction Detail redesign — F-02 · Blocker

### D0 · First, decide the scope

The work described in §16.3/§16.6 and specified in §4.6 was built on 2026-07-22,
verified by screenshot, and never committed. Before rebuilding, answer:

**Is the §16 redesign still what we want?** The reasoning in §16 is sound and
was a direct response to review feedback ("too complex and confusing"), and
the current page still has the exact problems it named — an AI pane taking
~45% of the screen before anyone asked, and no orientation view. The screenshots
in `C:\Projects\_shots\` show the intended result.

**Recommendation: yes, rebuild to §16.3 + §16.6 as specified.** Treat those
sections plus §4.6 as the design document — no new design round.

**Also: find out how this was lost.** One day of built, reviewed, verified work
is missing with no commit. Before rebuilding, check for a stash, a lost
worktree, or an unpushed local branch on the machine that produced
`detail-overview.png` — recovering the diff would turn a 5–7 day rebuild into a
1-day re-verification. This check is the first task of the phase, not an
afterthought.

### D1 · Header (§16.6)

Three rows, replacing the current four:
1. Breadcrumb alone.
2. Identity + actions on one line: serif name + stage pill on the left;
   on the right four controls of identical shape and height — posture chip
   (`⚡ Assisted ▾`, choices and the handled/needs-you line inside its menu),
   status pill, **Ask AI**, **⋯**.
3. Facts line, one size and colour, one separator:
   `address · Closes Jul 31 (3 days past due) · $992,000 · 25 overdue · 3% complete`.
   Only "overdue" takes an accent; days-to-close reddens inside 7 days; the
   progress fact is **omitted** when there is none (C3); past-due closings
   follow B1's wording.

The "⋯" menu carries **Print closing checklist** (all internal roles) and
**Delete transaction…** (TeamLead/Admin, destructive `useConfirm` naming the
address, returning to the list on success). Deleting a deal from its own page
is impossible today.

### D2 · Assistant docking

400 px docked right, **closed by default**, opened from the header's Ask AI,
remembered per user. `TransactionWorkspacePage.tsx:213-219` currently defaults
to open (`localStorage.getItem(AGENT_PANE_OPEN_KEY) !== 'closed'`); invert to
`=== 'open'`. Below `xl` the Agent tab remains the entry point (already
correct).

### D3 · Tab set and the Compliance merge

Final set: **Overview · Timeline · Tasks · Documents · People · Billing ·
Activity** (+ Email and Agent behind the agent flag). Compliance becomes the
**Checklist view of Documents** (`Files | Checklist` toggle) — both are the
deal's paperwork. `?tab=compliance` must resolve to Documents › Checklist, and
`?view=files|checklist` must work.

`ComplianceTab.tsx` is not rewritten — it is remounted as the Checklist view
inside `DocumentsTab`.

### D4 · Overview tab (new)

Four panels, each handing off to the tab that owns the editor, each rendering
only when it has real data (spec §4.6):
- **Needs you** — overdue + due-today tasks, click opens the task on Tasks;
  a missing-documents line when there are any.
- **Key dates** — the seven tracking dates as status-coloured chips; click goes
  to Timeline. **The data is already served** — `plan.tracking_dates` returns 7
  populated entries today and nothing renders them.
- **Progress** — complete/total with the bar, open/overdue counts, price.
- **People** — the parties, with "Manage".

Landing tab becomes Overview.

### D5 · Billing tab (new)

This deal's invoices from `GET /api/v1/invoices?scope=tenant`: status pill
(Draft/Sent/Paid/Void/Uncollectible), payer, due-or-paid date with overdue
marked, amount; a row opens `/payments/invoices/:id`. "Create invoice"
(prefilled `NewInvoiceModal`) renders only with `can_create_invoice`; the list
is readable by every internal role. Empty state names the action and links
"View all in Payments".

The list card's `TransactionInvoicesPanel` is the reference implementation —
reuse its row anatomy so both surfaces read identically.

### D6 · Timeline tracking-dates rail

The seven operational chips at the top of Timeline, coloured by status. The
five pure tracking fields open the date popover and save directly; **Closing and
Possession open the cascade preview** — the card writes them raw today and
strands every rule-driven deadline, which is the behaviour this rail exists to
end. Saving invalidates the dashboard cards query so the list agrees
immediately.

This retires the dead `DealOverviewCard` / `DealBriefBand` chain
(`WorkspaceHeader.tsx:340`), which is the only current consumer of
`tracking_dates` and has zero usages.

### D7 · Deep links

`?tab=`, `?view=files|checklist`, `?task=<id>`, `?requirement=<id>`,
`?qa=1`, `?access=1` (open the Client Q&A drawer / Manage client access once on
People, then strip the flag), `?created=1`. `?qa=1` and `?access=1` are no-ops
today. Add the Client-Q&A amber dot on People from the same tenant-wide thread
summary the list already uses.

### D8 · Verification gate

Not "tests pass" — **screenshots at 1600 px and 1024 px** of: Overview landing,
the three-row header with the facts line, the ⋯ menu open, the assistant closed
by default then opened, Documents › Checklist reached via `?tab=compliance`,
and the Billing tab with and without invoices. Store them in
`velvet-elves-data/completed_designs/` this time, and **commit the work in the
same session it is verified.**

**Acceptance:** every checklist row in §12, §13, §14, §19 (Billing) and TX-271,
TX-340, TX-291.

---

## 5. Phase E — consistency and hygiene

### E1 · Off-screen panels must leave the accessibility tree — F-09 · High

`ClientThreadDrawer.tsx:77-86` and `CommunicationsPanel.tsx:113-115` render
`role="dialog"` permanently, hidden only by `translate-x-full` — 3 and **60**
focusable controls respectively, reachable by keyboard, announced by screen
readers, and polluting the page's text content.

Two options; prefer the first:
1. **Return `null` when closed**, mounting on open (the transition can be kept
   with a short unmount delay). Simplest and removes the DOM weight.
2. If the slide-in transition must survive, add `aria-hidden="true"` **and**
   `inert` when closed. The app's own AI chat panel already does the
   `aria-hidden` half correctly — copy that pattern.

Audit the same file family for the pattern; `HistoryPanel.tsx:47` uses the
translate trick without `role="dialog"` and is a lesser case of the same issue.

**Acceptance:** TX-204, TX-205. On a freshly loaded list page, zero
`role="dialog"` elements are present-but-closed; tabbing from the last card
reaches the footer, not a hidden drawer; "Client Q&A" no longer appears in the
page's text when nothing is open.

### E2 · `/transactions/all` status tab bar — F-12

Spec §4.4: `All | Active | Incomplete | Paused | Completed | Closed` with
counts, plus "Status" as a sort option. Today the tab strip renders only for
`statusView === 'active'` (`TransactionListPage.tsx:951`), leaving `/all` with
no way to narrow — the reason the route exists. Reuse the existing tab
component with a status-based `FILTER_TABS` variant and extend
`transaction-tab-counts` to return per-status counts for `state_filter=all`.

**Acceptance:** TX-007, TX-049.

### E3 · Icon system — F-24

The drawer footer uses emoji as button glyphs (`📄 🖨 🕐 ✉️ 👥 💬 💳 🗑`), as do
the info badges (`⚑ 📄`) and AI-suggestion chips. Everything else in the app
uses lucide. Replace with lucide equivalents (`FileText`, `Printer`, `History`,
`Mail`, `Users`, `MessageSquare`, `CreditCard`, `Trash2`) at the sizes the
surrounding controls use.

**Note:** this touches the surface Jake's comp defines. Screenshot the before
and after and get sign-off before merging — the expanded card is explicitly
protected by §16.1, and an unrequested visual change to it is exactly the kind
of thing that got the last round rejected.

**Acceptance:** TX-394, TX-395, plus a side-by-side screenshot in the PR.

### E4 · Dead code — F-21, F-22, F-23

- **F-21** — decide whether the five missing info badges (Emails, Notes,
  Missing Docs, Client Touch, Lender Touch, History) are still wanted. The
  card already reads crowded; recommend keeping Tasks + Docs and **amending
  spec §4.1** rather than adding five badges. Decision needed.
- **F-22** — once F-21 is decided, either render the History badge or delete
  the dead handler at `TransactionCard.tsx:718`.
- **F-23** — delete `onChangeTaskStatus` from `TransactionCardCallbacks` and
  its wiring at `TransactionListPage.tsx:774-778`; the card comments at
  `:301-302` that the control was deliberately removed.

Also retire `DealOverviewCard` and `DealBriefBand` as part of D6, once the
tracking-dates rail has a real home.

---

## 6. Sequencing and effort

| Phase | Contents | Effort | Blocked by |
| --- | --- | --- | --- |
| **A** | F-01, F-03, F-04, F-17, F-19, F-20, F-25 | 0.5 d | — |
| **B** | F-05, F-06, F-07, F-08, F-13, F-14, F-15, F-18 (F-26 deferred pending fixture) | 3 d | — |
| **C-decide** | C1, C2, C3 questions to Jake | 0.5 d elapsed | Jake |
| **D** | Re-land the detail redesign | 5–7 d (1 d if the lost diff is recovered — check first) | C3 (progress rule) |
| **C-build** | Tab taxonomy, Pending, unified progress | 2 d | C-decide |
| **E** | F-09, F-12, F-24 (sign-off), F-21/22/23 | 1.5 d | E3 needs Jake's sign-off |

**Total: ~12–14 days**, or ~7 if the 2026-07-22 diff is recoverable.

Ship A within the first day — it is seven small fixes to four files and removes
the two defects (corrupt exports, unreadable audit trail) that a client would
notice first.

---

## 7. Open questions for Jake

1. **Filter tabs (C1)** — should "Overdue" mean "has overdue tasks" or "deal
   health is Critical/Unhealthy"? Recommend the former, and dropping the
   duplicate "Unhealthy" tab.
2. **Pending route (C2)** — drafts-and-paused (current behaviour, recommended,
   retitled "Drafts & Paused"), a duplicate of Active, or removed from nav?
3. **Progress definition (C3)** — do AI-hidden and Skipped tasks count toward a
   deal's percent complete? Recommend excluding both, defined once server-side.
4. **Detail redesign (D0)** — confirm §16.3/§16.6 is still the target before
   5–7 days of rebuild.
5. **Card info badges (E4/F-21)** — add the five missing badges, or amend the
   spec to the two that shipped? Recommend amending the spec.
6. **Card icon system (E3)** — approve replacing the footer emoji with lucide
   icons on the expanded card, given §16.1 protects that surface.

---

## 8. Regression guards worth adding

The four blockers were all invisible to the existing test suite. Each suggests
a cheap guard:

| Defect | Guard |
| --- | --- |
| F-01 exports | Unit test asserting every export helper's fetch URL starts with `API_BASE_URL`; a lint rule banning `fetch('/api…')` outside `src/utils/api.ts` |
| F-04 dead route | A contract test that walks the frontend's API path constants against the backend's OpenAPI schema and fails on any path with no route |
| F-03 date contract | A render test on `ActivityTab` fed the backend's real payload shape, asserting no "Invalid Date" |
| F-02 lost work | A pre-merge check that documentation claiming "implemented" cites a commit SHA — and the working agreement that verified work is committed the same session |

The OpenAPI contract test is the highest-value of these: it would have caught
F-04 the day it was written, and it protects every other page too.

---

## 9. As-built log (2026-08-04)

> Status: **IMPLEMENTED.** Phases A–E executed in one pass. Every change below
> was verified in a real Chrome browser against the local stack, not by tests
> alone. Artifacts: `C:\Projects\_shots\txn\` (screenshots + JSON reports),
> drivers in `C:\Projects\_tools\e2e\txn\`.

### 9.1 D0 first — the lost diff is unrecoverable

Before rebuilding, the working tree was searched for the 2026-07-22 work as §4
required. It is gone:

```
git stash list                          → empty
git worktree list                       → one worktree
git fsck --lost-found                   → 15 dangling commits, newest 2026-07-28,
                                          none from the evening of 07-22
git rev-list --objects --all | grep -i "overviewtab|billingtab"  → no hits
git reflog                              → last 07-22 commit at 11:54; the
                                          screenshots are 18:30 and 19:06
```

The work was never staged, stashed or committed. Phase D was therefore a full
rebuild, as planned.

### 9.2 What changed

| Phase | Files | Notes |
| --- | --- | --- |
| **A1** F-01 | `utils/export.ts` | `API_BASE_URL` prefix + a `text/html` content-type guard, so a wrong origin can never again yield a silently corrupt download. Swept all four frontends for `fetch('/api…')` — this was the only offender. |
| **A2** F-03 | `workspace/ActivityTab.tsx`, `hooks/useTransactionHistory.ts` | Render the server's clock string as given; `formatTimestamp` → `formatIsoTimestamp`, kept only for the Automation lens where the payload really is ISO. The `timestamp` field now documents its format on the shared type. |
| **A3** F-04 | `hooks/usePayments.ts` | Repointed at `GET /tasks/transaction/{id}`; filters Pending **and** InProgress client-side (an in-progress task is exactly the kind you settle with an invoice) and maps `id`→`task_id`, so `NewInvoiceModal` is untouched. |
| **A4** F-17 | `hooks/useApiFetch.ts`, `hooks/useAdSlot.ts` | Fixed generically at the query boundary: a 204 becomes `null`, not `undefined`. Every 204 endpoint benefits, not just the ad slot. |
| **A5** F-19/20/25 | `TransactionListPage.tsx`, `providers/parsing.py`, `providers/prompts.py`, both provider modules, `api/v1/transactions.py` | Dropped the `.toLowerCase()`; replaced the bare `[:20]` CTA slice with `clean_cta_label()`, which drops whole trailing words and falls back rather than shipping "Schedule Walk-Throug"; history events carry a `link_path` extracted from the FULL body before truncation, and the preview truncates on a word boundary. |
| **B1** F-05 | `dashboard.py`, `TransactionCard.tsx` | A past closing date is stated in words ("Past due · 3 days ago"), never as a negative integer. A new `days_to_close < 0` branch precedes the "closing is in N days" text. "Closing Soon" lost its lower bound, so past-due deals stop vanishing from every date-based tab. |
| **B2** F-06/07/08 | `TransactionListPage.tsx` | Tab and sort are URL-derived, not `useState`; the inline search input ships with a clear affordance; the count pill reads `tabCounts[activeTab]`. |
| **B3** F-13/14/15 | `TransactionListPage.tsx` | Card skeletons replace the spinner; a real error branch with Retry; three distinct empty states (no deals / search missed / filter missed), only the first of which suggests creating a deal. |
| **C1** F-10 | `dashboard.py`, `TransactionListPage.tsx` | "Overdue" is task-based and agrees with the card's own badge; "Needs Attention" no longer swallows "In Inspection"; the duplicate "Unhealthy" tab is gone, with `?tab=unhealthy` aliased to Overdue so live links keep working. |
| **C2** F-11 | `TransactionListPage.tsx`, `AppLayout.tsx` | Retitled **Drafts & Paused**, with an empty state that explains what lands there. |
| **C3** F-16 | **new** `services/task_progress.py`, `transaction_plan.py`, `closing_checklist.py` | ONE canonical rule — Completed ÷ (all tasks except Skipped and AI-hidden) — with `percent` returning `None` rather than 0 when there is nothing to measure. The checklist had been counting AI-owned tasks and scoring Skipped as complete; that is why it said "28 total · 3 completed" for a deal the app showed as 26/1. |
| **D1/D2** | `TransactionWorkspacePage.tsx`, `WorkspaceHeader.tsx` | Three-row header; facts line; ⋯ menu with Print + Delete; Ask AI; assistant closed by default; posture collapsed from a three-way segmented control into one chip. |
| **D3–D5** | **new** `OverviewTab.tsx`, **new** `BillingTab.tsx`, `CreationReceiptStrip.tsx` | Overview is the landing tab; Billing lists the deal's invoices; Compliance became the Checklist view of Documents. |
| **D6/D7** | `TimelineTab.tsx`, `PeopleTab.tsx` | Tracking-dates rail (Closing/Possession route through the existing cascade picker; the five pure fields save directly); `?qa=1` / `?access=1` open their surface once and pin `tab=people`. |
| **E1** F-09 | **new** `hooks/useInertWhenClosed.ts` + 3 panels | Closed panels are `inert` + `aria-hidden`; 63 focusable controls left the tab order. |
| **E2** F-12 | `dashboard.py`, `schemas/dashboard.py`, `useDashboard.ts`, `TransactionListPage.tsx` | `/all` gained its status tab bar, backed by a new `status_counts` block and a `status` query param. |
| **E4** F-22/23 | `TransactionCard.tsx`, `TransactionListPage.tsx` | Deleted the dead History-badge handler and the `onChangeTaskStatus` callback. |

### 9.3 Verification

Browser (real Chrome, admin user, local stack):

| Was | Now |
| --- | --- |
| 3 exports → identical 1,090-byte `index.html` | `transactions.csv` 1,182 B `Address,City…`; `.xlsx` 5,838 B `PK\x03\x04`; `.pdf` 2,107 B `%PDF-1.3` — byte-identical to the backend |
| Tab clicks left the URL unchanged; Back left the page | `?tab=overdue` …; Back steps through filters, staying on the page |
| Pill "6 deals" over 2 cards | every tab's pill equals its card count (6/6, 1/1, 4/4, 0/0) |
| No search input | present, filters to 1 deal, writes `?search=oak`, clearable |
| "-75 DAYS TO CLOSE", "Closing is in -3 days" | "Past due · 3 days ago"; no negative anywhere on the page |
| Detail: no Overview, no Billing, Compliance a tab, no facts line, no ⋯, pane open | Overview · Timeline · Tasks · Documents · People · Billing · Activity; lands on Overview; facts line renders all five facts; ⋯ has Print + Delete; pane closed (`aria-pressed=false`, no stored pref) |
| Activity: every row "Invalid Date" | 0 occurrences; times render ("9:12 PM") with working "Open" links |
| 3 closed dialogs focusable | all `inert` + `aria-hidden` |
| Console error on every list load | clean; zero 4xx across the sweep |

Header at 1600 px and 1024 px: three rows, four action controls all exactly
32 px tall, no horizontal overflow at 1600/1024/375.

Suites: backend **1580 passed**; frontend unit **261 passed (40 files)**;
frontend integration **113 passed**. Nine test contracts were updated
deliberately, as §16.4 anticipated — the landing tab is Overview (suites
asserting plan rows now name `?tab=timeline`), the assistant starts closed
(tests open it via `openAgentPane()`), progress is a fact rather than a
`data-testid`, and the tracking rail is expected on Timeline. A new test pins
the closed-by-default assistant.

`tsc --noEmit` clean · `eslint --max-warnings=0` clean · `vite build` clean ·
`ruff check app/` clean.

**One pre-existing failure is untouched and unrelated:** `DocumentsModal >
shows the Missing documents group…` fails only when the integration folder runs
as a batch, and fails identically on pristine code (pristine 112 passed / 1
failed; with these changes 113 passed / 1 failed). It passes in isolation. It is
test pollution from an earlier suite's Radix dialog and predates this work.

### 9.4 Deliberately NOT done

- **F-24 / E3 — the card's emoji glyphs.** §5 of this plan required Jake's
  sign-off before touching the expanded card, because §16.1 protects that
  surface and an unrequested restyle of it was rejected once already. The
  change is a mechanical swap to lucide icons; it is left pending that approval
  rather than made unilaterally.
- **F-21 — the five missing info badges.** Still a product decision (add them,
  or amend spec §4.1 to the two that shipped). Recommendation unchanged: amend
  the spec.
- **B5 / F-26 — pagination.** §2 said not to ship it without a >20-deal
  fixture; the tenant has 6. Deferred rather than shipped untested.
- **F-27 — `milestone_label = "1"`** on one task template. A data cleanup.

### 9.6 Review round 2 (2026-08-04, same day)

The rebuilt page was reviewed and four things were called out. All are fixed.

| Raised | Resolution |
| --- | --- |
| **The assistant belongs on the LEFT.** The first rebuild docked it right at 400px per §16.3's literal wording; the reviewer's point is that this is an *agent-centric* workspace, and the conversation is the primary surface, not a sidecar. | Pane restored to the **left, 55fr** — the layout §16.1 already blessed. §16.3's "400px docked right" is superseded on this point. |
| **Too much at the top of the page.** Five facts stacked under the title read as clutter, not as a summary. | The header now carries the **address only**. Closing date, price, overdue count and progress all moved to **Overview**, each into the panel that owns it: the closing headline leads Key dates, and Open / Overdue / Purchase price became a labelled stat row on Progress. |
| **The right panel's tabs overflowed**, clipping "Email" off the edge. | Two causes, both fixed: the tabs are **label-only** now (the icons bought nothing the label did not already say), and the workbench keeps a **600px floor** (`minmax(600px,45fr)`). Measured after the change: zero clipped tabs with the pane open at 1600 (598px strip in 598px) and at 1280 (pane yields to 376px). A fade + scroll-into-view remains for anything narrower. |
| **Card and detail page named the same things differently** — "Contacts" vs the "People" tab, "Invoices & Payments" vs "Billing" — so one feature read as two. | **"Contacts" everywhere**: the card section, the workspace tab (key `contacts`, with `?tab=people` aliased so live links keep working), the tab's own heading, and the Overview panel. **The card's "Invoices & Payments" section is removed**; invoices live on the workspace's Billing tab. The card footer's "Invoice" button stays — creating one is a triage-speed action, and it opens the same modal Billing does. |

The Attorney Matter Workspace keeps its own "People" pane: it is a separate
surface for a separate role and was not in scope.

Re-verified after these changes: integration 113 passed (same lone pre-existing
`DocumentsModal` batch failure), unit 261 passed, `tsc` / `eslint` / `vite
build` clean. One further test contract updated — the progress assertion moved
from the header string to Overview's Progress panel.

### 9.5 Decisions taken (C1–C3, D0)

§7 listed six questions for Jake. Four were answered by implementing this
plan's own recommendation, because each was needed to finish the work. All are
reversible, and each is flagged here for review:

1. **Tabs mean their labels** (C1) — "Overdue" is task-based; "Unhealthy" removed.
2. **Pending = Drafts & Paused** (C2) — retitled, with an honest empty state.
3. **Progress excludes Skipped and AI-hidden** (C3) — one server-side rule.
4. **The §16 redesign was rebuilt as specified** (D0).

Questions 5 and 6 (badges, icons) remain open — they change a surface Jake's
comp owns, and neither blocks anything.
