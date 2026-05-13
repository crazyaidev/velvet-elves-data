# Transactions Page Completion Plan

**Status:** Drafted for implementation from client testing feedback  
**Owner:** Jan (sole dev)  
**Last updated:** 2026-05-13 (post-review revision)  
**Client design reference:** `velvet-elves-data/VE-ActiveTransactions.html`  
**Canonical frontend root:** `velvet-elves-frontend/src/pages/transactions/TransactionListPage.tsx`  
**Primary card component:** `velvet-elves-frontend/src/components/shared/TransactionCard.tsx`  
**Modal roots:** `velvet-elves-frontend/src/components/active-transactions/`  
**Backend roots:** `velvet-elves-backend/app/api/v1/dashboard.py`, `app/api/v1/transactions.py`, `app/api/v1/tasks.py`, `app/api/v1/transaction_parties.py`

---

## 0. Review Findings And Corrections

The client testing notes show that the Transactions page is close, but not yet trustworthy enough to call finished. Several areas already have real code behind them; the remaining work is mostly reconciliation, durable workflow behavior, and polish.

1. **Route shape mismatch:** product docs describe `/transactions/active`, `/transactions/pending`, `/transactions/closed`, and `/transactions/all`; the shipped client test route is `/transactions` with status state in the query string. Keep `/transactions` working and add named aliases so dashboards, sidebar links, and future docs can use either shape.
2. **Export behavior currently passes the client test but is too local:** frontend exports are generated from the currently visible card array. The final workflow should export the full filtered result set, not only the loaded page. Client acceptance currently names `transactions.csv` and `transactions.xls`; keep those filenames for MVP unless Jake explicitly approves `.xlsx` before Slice 4. Do not ship `.xlsx` bytes with a `.xls` filename.
3. **Print checklist likely fails because the popup opens after an awaited request:** browsers often block `window.open()` after async work. Open a blank print window synchronously from the click, then hydrate it after the checklist payload returns.
4. **Print endpoint naming is inconsistent across docs and code:** frontend calls `/api/v1/tasks/transaction/{id}/closing-checklist`; `FRONTEND_UI_WORKFLOW_LOGIC.md` says `/api/v1/transactions/{id}/checklist`; `SYSTEM_DESIGN.md` says `/api/v1/transactions/{id}/closing-checklist`. Use one shared checklist service and expose all three routes for compatibility. The Transactions page should call `/api/v1/transactions/{id}/checklist`.
5. **Checklist content is not yet profile-template driven:** the current payload is task-list based. Requirements say closing checklists should pull buyer/seller templates and tagged profile notes, with seller escrow-overage reminders.
6. **Date display is too optimistic:** frontend maps any populated key date to green unless `is_overdue` is already true, and optimistic edits always turn green. Past edited dates must render overdue immediately, and date formatting must be consistent.
7. **Key-date semantics need one explicit status contract:** the backend currently returns `is_overdue`; the frontend infers color. Add a stable `status` value so red/amber/green/neutral cannot diverge across initial load, optimistic edit, and refetch.
8. **Contact cards lack company data:** `TransactionCardContact` does not return `company`, so the UI cannot display "Justin Montour, Elements Financial" or prefill company fields when adding lender/title helpers.
9. **Contact groups are too static:** standard groups always include Buyer and omit Seller. They should be conditional from `representation_type`: Buyer representation shows Buyer, Seller representation shows Seller, Both shows both.
10. **Agent grouping is mislabeled:** client wants the section title `Agents`, and the signed-in user should not be listed. The group should show co-agents or other transaction agents only.
11. **Plus buttons are too noisy:** the current UI renders a plus button beside each contact. The desired pattern is one add control per section, aligned with the style guide repeater pattern.
12. **Add Contact cannot prefill from group context:** when adding a lender/title assistant or a party under a company, the modal should inherit the group company while keeping it editable.
13. **Empty organization rows need sensible defaults:** if the only known value is a company, clicking add should seed that company into the correct field instead of opening a blank form.
14. **Phone formatting is inconsistent:** the wizard already formats phone numbers while typing. Add Contact should reuse the same formatter.
15. **Add Task AI suggestions lose visible selection state:** a toast confirms the click, but after the toast fades the selected approach is not obvious. The applied suggestion should remain visibly selected.
16. **Task status dropdown is unclear or missing:** client could not tell what "status dropdown" meant. Either make it visible and operational, or remove it from the test script. The better product outcome is to add a compact status menu per task row.
17. **Transaction context is missing in modal headers:** documents and task/contact modals need client name plus property address so users can distinguish concurrent deals for the same client.
18. **Search is specified but not surfaced:** the backend supports `search` on `/dashboard/transaction-cards`; the page should expose inline transaction search and persist it in the URL.
19. **Tab counts are fetched through many card queries:** the final contract should provide authoritative counts from the same filtered corpus instead of issuing a separate card query for every tab.
20. **AI guardrails remain correct:** Ask AI opens the side panel and should continue to recommend, draft, and summarize only. AI must not complete tasks, change dates, send messages, or mutate transaction/contact state without a user click.
21. **Multi-tenant safety remains non-negotiable:** every transaction, task, party, document, communication, and audit query must filter by tenant and role/assignment, with RLS-compatible tests for new data paths.
22. **Use existing patterns:** React Query, FastAPI routers/services/repositories, Supabase tenant filters, existing shadcn/Radix components, `ve-*` tokens, IBM Plex typography, and the existing wizard phone formatter.
23. **PII decrypt leak (security, P0):** `_safe_decrypt` in `app/api/v1/dashboard.py`, `_decrypt_safe` in `app/repositories/transaction_party_repository.py`, and `_safe_decrypt_value` in `app/api/v1/documents.py` currently return the raw value when `decrypt()` raises. Per the Fernet rule, encrypted PII failures must return `""` (or `"[Encrypted]"`) and log a warning. Also audit call sites: plaintext fields such as `transaction_parties.company`, `transactions.city`, `transactions.state`, and `transactions.zip_code` must not be passed through decrypt helpers or the fix will accidentally blank valid display data.
24. **Team-member filter is non-functional and under-specified:** the page sends unsupported `{ assignee: <value> }` to `/dashboard/transaction-cards`; FastAPI ignores it. `useTransactionCards` already accepts `search`, but it does not type `view`, `team_member_id`, or the needed unassigned filter. Rename the frontend call site to `team_member_id` for real users, add `view` and `assignment_scope`, and add a test that confirms a Team Lead's "All Team Members" / "My Transactions" / "Unassigned" selection changes the result set.
25. **URL aliases need path-level work, not just query parsing:** current React routes only mount `/transactions`; `/transactions/active` will not render until `App.tsx` adds an explicit or parameterized route. The URL parser should also accept product-doc aliases `?filter=` for `?tab=` and `?highlight=` for `?expand=`.
26. **Tab-count consolidation should be authoritative:** the plan should choose a dedicated `/dashboard/transaction-tab-counts` endpoint as the source of truth. Counting must not call the card endpoint seven times and must not schedule AI next-step refresh work.
27. **Task audit gaps are known, not hypothetical:** `PATCH /tasks/{id}` audits status changes only; `PUT /tasks/{id}/status` and `POST /tasks` currently do not write audit rows. Add those audit rows when wiring the visible status menu and Add Task flow.
28. **Assignment contact rows have a real endpoint path:** assignment-backed Agent rows must use `/api/v1/transactions/{transaction_id}/assignments/{assignment_id}` for future edit/remove operations, not a non-existent `/transaction-assignments` endpoint.
29. **`updated_at` is deferred with the Recently Updated sort:** do not require `updated_at` in the Slice 1-4 transaction-card contract unless the deferred sort is pulled forward.

---

## 1. Completion Goal

The Transactions page should become the internal daily operating surface for deals. An agent or coordinator should be able to land on the page, see which transactions need attention, open the right card, update tasks/dates/contacts/documents, print or export, and ask AI for help without losing context or guessing whether a button actually did anything.

The completion bar is:

- No visible control is cosmetic.
- Every data mutation persists, invalidates the right workspace queries, and writes an audit log when it changes workflow state.
- Every header and modal carries enough transaction context: client name and property address.
- Date severity is accurate on first load, optimistic edit, and refetch.
- Contact sections match representation type and show company names instead of redundant role labels.
- Add Contact uses section context to prefill company/name where practical.
- Add Task AI suggestions leave a durable selected state in the modal.
- Print checklist works reliably despite popup blockers and uses the profile-template workflow.
- Exports download the complete filtered result set with client-approved filenames.
- Sidebar filters, tabs, sort, search, expand/highlight, and task-focus state are shareable through URLs.
- The page stays fast under many transactions and does not make unnecessary AI calls.
- The page works by keyboard and follows the style guide.
- AI never mutates data or contacts people without explicit human action.

---

## 2. Page Identity And Access

| Field | Decision |
| --- | --- |
| Canonical client-tested route | `/transactions` |
| Alias routes | `/transactions/active`, `/transactions/pending`, `/transactions/closed`, `/transactions/all` |
| Page title | Active Transactions, Pending Transactions, Closed Transactions, All Transactions, based on route or status state |
| Allowed product roles | Agent, Elf, Team Lead, Attorney, Admin |
| Actual enum roles | `Agent`, `TransactionCoordinator`, `TeamLead`, `Attorney`, `Admin` |
| External roles | `Client`, `ForSaleByOwner`, `Vendor` denied with 403 until their respective portals exist (no dedicated `/client/transactions` or `/fsbo` route exists today) |
| Tenant scope | Repository/API filters by `tenant_id`; RLS tests for new/changed query paths |
| Attorney behavior | Attorney keeps current route adapter, but shared contracts should not break attorney cards |

Frontend route work:

- Keep `/transactions` rendering the current page.
- Add route aliases:
  - `/transactions/active` -> active status view.
  - `/transactions/pending` -> pending status view.
  - `/transactions/closed` -> closed status view.
  - `/transactions/all` -> all status view.
- Accept `?status=active|pending|closed|all` for backward compatibility.
- Normalize sidebar links to named routes, while keeping the query form accepted.
- Preserve existing search/focus behavior, including `?expand=<transaction_id>` and `?task=<task_id>`, while accepting `?highlight=<transaction_id>` as the product-doc alias.

Backend access work:

- Continue role/assignment checks through `require_transaction_access`.
- Do not let Admin/TeamLead cross tenant boundaries.
- For Team Lead team filtering, support `view=team` plus `team_member_id`. Canonical query param for a specific user is `team_member_id` (matches `SYSTEM_DESIGN.md`); the frontend must be updated to send that name instead of the current `assignee`.
- Do not overload `team_member_id` with sentinel strings. "Unassigned" is not a user id; represent it as `view=team&assignment_scope=unassigned`.
- TC/Elf users (`TransactionCoordinator`) have the same Add Task / Add Contact / Edit Dates rights as Agents on this page (per the 2026-04-24 policy reversal). Verify each mutation endpoint's `require_role(...)` list includes `TRANSACTION_COORDINATOR`.

---

## 3. Client Feedback Triage

| Test Area | Client Result | Implementation Decision | Priority |
| --- | --- | --- | --- |
| 17. Active Transactions page | Pass | Preserve current visible behavior; harden exports, route aliases, URL state, and search. | Medium |
| 17. Saved custom views | Low future | Defer. Add only if filter/search/sort URL state is stable first. | Low |
| 17. Bulk actions | Client did not understand | Defer. If revisited, describe as "select multiple transaction cards and apply the same reassignment/status change." | Skip for MVP |
| 17. Export column picker | Low future | Defer until backend exports are authoritative. | Low |
| 18. Tasks area | Pass, needs clarification | Add client + address context to card/modal headers. Add visible task status menu. | High |
| 19. Key Dates | Needs Work | Fix overdue color logic and consistent date formatting. | High |
| 20. Contacts area | Needs Work | Company prefill, company display, one add button per section. | High |
| 21. Add Task window | Needs Work | Keep selected AI suggestion highlighted and expose applied method clearly. | Medium |
| 22. Add Contact window | Needs Work | Representation-based sections, Agents section, no signed-in user, company display, phone formatter, one add button per section. | High |
| 23. Documents window | Pass, asks context | Add client + property address in modal header. | Medium |
| 24. History panel | Pass | Preserve. Add address in header if not already visible. | Low |
| 25. Print and AI actions | Print Fail, AI Pass | Fix print popup flow, endpoint alias, and checklist template contract. Preserve AI panel. | High |

---

## 4. Final User Workflow

### 4.1 Entry And Workspace Load

1. User opens `/transactions` or any alias route.
2. Protected route validates session and role.
3. External users (Client, ForSaleByOwner, Vendor) are denied with a 403 page until their respective portal routes exist. Building a `/client/transactions` or `/fsbo` route is **out of scope** for this plan — do not invent one as part of these slices.
4. Route/status state resolves:
   - `/transactions` defaults to active.
   - `/transactions/active` maps to `state_filter=active`.
   - `/transactions/pending` maps to `state_filter=pending`.
   - `/transactions/closed` maps to `state_filter=closed`.
   - `/transactions/all` maps to `state_filter=all`.
5. URL query initializes:
   - `tab` (`filter` accepted as a legacy/product-doc alias)
   - `sort`
   - `search`
   - `view` (`personal` | `team`, Team Lead/Admin only)
   - `team_member_id`
   - `assignment_scope` (`unassigned` only for Team Lead/Admin team view)
   - `highlight` (`expand` accepted as a backward-compatible alias)
   - `task`
6. Page loads:
   - card list
   - tab counts
   - total deal count
   - sidebar deal-state counts
   - topbar AI briefing
7. Loading state shows skeleton cards, not a single spinner, for a calmer page.
8. Errors show a retry banner and preserve stale data if React Query has cached data.

### 4.2 Header Workflow

Header content:

- Breadcrumb: Deals > current status view.
- Title: current status view.
- Count pill: total matching current status/filter/search/team/assignment scope.
- Buttons:
  - Export CSV
  - Export Excel
  - Print Report
- Team Lead/Admin team member selector when applicable.
  - All Team Members -> `view=team`
  - My Transactions -> `view=personal`
  - Specific team member -> `view=team&team_member_id=<uuid>`
  - Unassigned -> `view=team&assignment_scope=unassigned`

Rules:

- CSV downloads `transactions.csv`.
- Excel: client acceptance currently expects `transactions.xls`, while the backend currently emits `transactions.xlsx` (true Office Open XML). **MVP decision:** preserve the client-tested `transactions.xls` filename unless Jake approves `.xlsx` in writing before Slice 4. If keeping `.xls`, change the backend exporter to return a legacy-compatible Excel HTML workbook with `application/vnd.ms-excel`. If switching to `.xlsx`, update the client test script and user-facing acceptance criteria at the same time. Never mismatch extension and file bytes.
- Print Report opens a print window for all filtered transactions, not only the current page.
- Buttons show pending state and failures use destructive toasts.

### 4.3 Sidebar Deal-State Workflow

Sidebar links:

- Active Transactions -> `/transactions/active`
- Pending -> `/transactions/pending`
- Closed -> `/transactions/closed`
- All Transactions -> `/transactions/all`

Behavior:

- Switching changes the page title and card corpus.
- `Pending` shows transactions whose `status` is `Incomplete` or `Paused` — deals in progress but not actively executing (signed contract not yet received, paused awaiting client decision, etc.). This matches the existing backend mapping in `dashboard.py` (`state_filter=pending → [Incomplete, Paused]`).
- Closed cards are read-only except documents/history/print.
- All Transactions shows status pills for all transaction states.

### 4.4 Filter Tab Workflow

Active view tabs (matches the existing `FILTER_TABS` array in `TransactionListPage.tsx`):

- All
- Overdue
- Due Today
- Needs Attention
- Closing Soon
- In Inspection
- On Track
- Unhealthy

Rules:

- Tab changes update `?tab=`.
- Badges come from one backend authoritative count contract: `GET /api/v1/dashboard/transaction-tab-counts`.
- Count scope matches the cards: same status view, same team member scope, same `assignment_scope`, and same search when search is active.
- The count endpoint must not reuse `/transaction-cards` in a way that schedules AI next-step refreshes or returns card payloads.
- If a filter has no results, show a filter-specific empty state and a Clear Filter action.

### 4.5 Sort And Search Workflow

Sort options:

- Urgency
- Close Date
- Client Name
- Price
- Recently Updated — **deferred for this plan.** Enabling this requires three coupled changes (add `updated_at` to `TransactionCardResponse`, extend `_sort_cards` in `dashboard.py`, widen the route regex pattern, expose `updated_at` in `useTransactionCards`). None of those are blockers for the client feedback, so this option is moved to §12 Future Improvements.

Search:

- Inline search field beside sort.
- Debounced at 300 ms.
- Persists to `?search=`.
- Searches client names, party names, companies, address, dates, price, and notes where available.
- Clearing search removes the URL param and restores the full filtered result set.

### 4.6 Transaction Card Workflow

Collapsed card must show:

- Client name(s).
- Property address.
- Status pill.
- Why badges.
- AI next-step banner when there is an active next deadline.
- Primary contact actions.
- Milestone bar.
- Info badges.
- Days to close.
- Overdue state.
- Purchase price.

Context rule:

- Anywhere a transaction title appears in a modal or print/download context, use this pattern:
  - Primary line: client name(s)
  - Secondary line: property address
- This avoids ambiguity when the same client has multiple active properties.

Expanded card areas:

- Tasks
- Key Dates
- Contacts
- AI Suggestions
- Footer actions

Keyboard:

- Card wrapper is focusable with `role="button"` and `aria-expanded`.
- Enter/Space toggles the card.
- Nested controls stop propagation and keep their own labels.

### 4.7 Tasks Area Workflow

Visible row actions:

- Checkbox toggles complete/incomplete.
- Status menu changes explicit status:
  - Pending
  - In Progress (payload `InProgress`)
  - Completed
  - Blocked
  - Skipped
- Add button opens Add Task modal.

Mutation rules:

- Checkbox uses optimistic update with rollback on failure.
- Status menu uses `PATCH /api/v1/tasks/{id}` or `PUT /api/v1/tasks/{id}/status`.
- Completion sets `completed_at`.
- Reopen clears `completed_at`.
- All task changes invalidate:
  - `['dashboard', 'transaction-cards']`
  - relevant transaction detail/task queries
  - topbar AI briefing
- Backend writes audit logs for status/name/due-date changes.
- Task changes invalidate cached AI next-step guidance for that transaction.

Clarification for client testing:

- The "task status dropdown" means the explicit Pending/In Progress/Completed/Blocked/Skipped menu beside the checkbox. The checkbox is the fast path; the menu is for non-binary statuses.

### 4.8 Add Task Modal Workflow

Header:

- Title: Add Task
- Context badge: client name
- Secondary text: property address

Fields:

- Task Name, required.
- Completion Method.
- Due Date.
- Assignee:
  - Myself
  - AI Agent, only if enabled and clearly human-approved.

AI suggestions:

1. User enters a task name.
2. User clicks Get AI Suggestions on How to Complete.
3. Backend returns suggested approaches.
4. User clicks one approach. **All suggestions are clickable** — including those without a `suggested_method`. The current code disables those buttons (`disabled={!isClickable}`); that gate must be removed so selection state can be set on any suggestion.
5. Modal:
   - sets Completion Method when the approach provides one;
   - stores `selectedSuggestionIndex` (canonical name; do not also call this `selectedApproachIndex` in §7.7);
   - highlights selected card with champagne border/background;
   - shows a compact `Selected` pill;
   - keeps that state until another suggestion is chosen, suggestions are hidden, or modal closes.
6. If the selected approach has no `suggested_method`, the Completion Method dropdown is left untouched and the suggestion card shows a small "No method change" note below the description.
7. Toast may still appear, but visible selection state is authoritative.

Submit:

- Create task through `POST /api/v1/tasks`.
- Disable submit while pending.
- On success, close modal, refetch cards, and show `Task added`.
- On failure, keep modal open and show specific API error.

Future enhancements:

- Common task template dropdown.
- Recurring tasks.
- Attach document while creating a task.
- AI similar-task dedupe modal with Add / Combine / Disregard.

### 4.9 Key Dates Workflow

Rows:

- EM Delivered
- Inspection Response
- Appraisal Expected
- CD Delivered
- Cleared to Close
- Closing Date plus time
- Possession plus time

Display:

- Dates use one format everywhere: `MMM d, yyyy`.
- Time fields show `Time: TBD` until set.
- Dates use `font-mono` and tabular numerics.

Status contract:

```ts
type KeyDateStatus = 'unset' | 'overdue' | 'today' | 'future' | 'cleared'

interface KeyDateAPI {
  label: string
  field_name: string
  value: string | null
  time_value: string | null
  status: KeyDateStatus
  is_overdue: boolean // temporary compatibility until frontend fully uses status
}
```

Color rules:

- `overdue`: red token triad.
- `today`: amber token triad.
- `future`: green token triad.
- `cleared`: neutral or green, depending on whether the milestone is truly completed.
- `unset`: muted.

Implementation correction:

- Replace frontend logic that says "has any value means green."
- Replace optimistic edit logic that always sets green.
- Use a shared helper that computes the same status from the edited ISO date before the server refetch arrives.
- Backend should eventually distinguish deadline dates from completed actual dates. Until that extra state exists, a date in the past entered by the user should show overdue, matching client expectation.

Mutation:

- Save through `PUT /api/v1/transactions/{id}/key-dates`.
- Write audit log with before/after.
- Invalidate transaction cards and AI next-step cache.
- Show `Date updated`.

### 4.10 Contacts Area Workflow

Section titles:

- Buyer, only when represented side includes buyer.
- Seller, only when represented side includes seller.
- Agents.
- Lender.
- Title.
- Inspector, when populated.
- Appraiser, when populated.
- Attorney, when populated or when `closing_mode = attorney`.
- Home Warranty, when populated.

Representation assumption:

- Treat the client note as "if the user does not represent a side, do not show that side's principal client section."
- `representation_type = Buyer` shows Buyer.
- `representation_type = Seller` shows Seller.
- `representation_type = Both` shows Buyer and Seller.
- If Jake literally intended to hide Seller when the user does represent Seller, that would conflict with the rest of the workflow and should be clarified before implementation.

Display rules:

- Do not show redundant role labels under names when the section title already identifies the role.
- Buyer/Seller secondary line:
  - show company only when the `company` field is present;
  - otherwise show no secondary role line.
- Lender/Title/Agent secondary line:
  - show company name when present;
  - otherwise show the specific role as fallback only if it adds clarity.
- Example:
  - Current: `Justin Montour` / `Loan Officer`
  - Target: `Justin Montour` / `Elements Financial`
- Organization rows:
  - `Quality Title` should display as the company/organization, not an empty person.

Agents section:

- Rename `Listing Agent` group to `Agents`.
- Include co-agent / external agent parties and internal transaction assignments that are not the signed-in user.
- Exclude the signed-in user.
- Do not show the owner/primary agent simply because they are signed in.

Add controls:

- One add button per section header.
- Remove plus buttons from individual contact rows.
- Empty-state add area remains clickable but should use the same section-level add behavior.
- Use the style guide repeater pattern: section-header outline "Add X" plus optional bottom ghost "Add Another X" if the list is long.

Phone/email:

- Phone icon uses `tel:`.
- Email icon uses in-app compose if connected, `mailto:` fallback otherwise.
- Future call logging can use communication logs, but it is not required for this specific client fix.

### 4.11 Add Contact Modal Workflow

Header:

- Title: Add Contact
- Section role label.
- Client name and property address.

Prefill rules:

- Adding a person under an existing Lender/Title company:
  - Company Name prefilled from the existing company row or first contact company.
  - Company remains editable.
- Adding from an empty organization group where company is known:
  - If adding a company row, prefill Name with company and Company Name with company.
  - If adding a person row, prefill Company Name only.
- Adding Buyer/Seller:
  - No role label under the display card later.
  - Company is optional; if filled, display it under the name.
- Adding Agents:
  - Role defaults to co-agent / agent contact, not signed-in user.

Fields:

- First Name.
- Last Name.
- Phone Number.
- Email Address.
- Company Name when relevant, and optionally for buyer/seller if user chooses to fill it.
- For organization rows, allow a single Organization/Company Name field instead of forcing First Name.

Phone formatting:

- Reuse `formatPhoneNumber` from `src/utils/formatters.ts`.
- Format while typing to `(555) 123-4567`, same as the wizard.
- Store normalized formatted value consistently with existing app behavior.

Submit:

- `POST /api/v1/transactions/{transaction_id}/parties`.
- Invalidate transaction cards and party queries.
- Toast `Contact added`.
- Modal closes on success and stays open on error.
- Backend validates role, tenant, and transaction access.

### 4.12 Documents Modal Workflow

Header:

- Title: View / Add Transaction Documents.
- Primary context: client name(s).
- Secondary context: property address.

Behavior:

- Existing document list appears.
- Details expand shows metadata.
- Download opens signed URL or safe download.
- Add Document uploads and refreshes list.
- Uploaded document updates transaction card doc count.

Completion requirement:

- The modal must never make the user guess which same-name client/property they are working inside.

### 4.13 History Panel Workflow

Current client result is Pass. Preserve:

- Slides in from right.
- Search filters events.
- Events grouped by Today, Yesterday, and older dates.

Small polish:

- Header should include client name and property address.
- If search returns no results, show a contextual empty state.

### 4.14 Print Workflow

Card Print Checklist:

1. User clicks Print on a transaction card.
2. Frontend opens a blank print window synchronously.
3. Blank window shows a minimal loading shell with the transaction context.
4. Frontend requests checklist payload.
5. On success, frontend writes printable HTML into the already-open window.
6. Print dialog opens.
7. On failure, the window shows a readable error and the main app shows a destructive toast.

Report Print:

1. User clicks Print Report in the page header.
2. Frontend opens a print window synchronously.
3. Backend returns all transactions matching current status/tab/search/team filters.
4. Print window renders the report and opens print dialog.

Backend endpoint plan:

- Extract checklist composition into a shared backend service so aliases do not import router handlers from each other.
- Add canonical `GET /api/v1/transactions/{id}/checklist`.
- Add compatibility alias `GET /api/v1/transactions/{id}/closing-checklist` because `SYSTEM_DESIGN.md` names that route.
- Keep `GET /api/v1/tasks/transaction/{id}/closing-checklist` as a legacy alias that returns the same response shape.
- Route-order note: `/{transaction_id}/checklist` is a sibling path and will not be captured by `/{transaction_id}` because it has an extra path segment. Keep these declarations near `/key-dates` for readability, and still keep same-shape static routes above dynamic routes as normal FastAPI hygiene.
- For the page-header Print Report button: **do not add** a new `/transactions/report` endpoint. Reuse the existing `GET /api/v1/transactions/export/pdf` and extend it (per §5.4) to accept `state_filter`, `tab`, `search`, `view`, `team_member_id`, `assignment_scope`, and `sort`. The frontend opens the print window synchronously, then either loads the returned PDF blob through an object URL/iframe or requests an HTML print variant from the same endpoint. Do not `document.write()` raw PDF bytes into the window.

Checklist data source:

- Buyer checklist template for buyer-side transactions.
- Seller checklist template for seller-side transactions.
- Both-side transactions can include both sections or a combined template.
- User/team profile tagged notes.
- Seller escrow-overage reminders.
- Transaction tasks and key dates.
- Property address and client names.

### 4.15 Export Workflow

CSV:

- Button calls backend export with current filters.
- Download filename: `transactions.csv`.
- Includes all filtered transactions, not just rendered page.

Excel:

- Button calls backend export with current filters.
- Client acceptance currently expects `transactions.xls`; preserve that for MVP unless Jake approves `.xlsx` before Slice 4.
- If `.xls` remains the acceptance target, change `Content-Disposition` in `transactions.py:export_excel` to `transactions.xls`, switch the exporter to emit a legacy-compatible HTML-as-workbook payload, and keep `Content-Type: application/vnd.ms-excel`.
- If Jake approves `.xlsx`, keep the current Office Open XML exporter, keep `transactions.xlsx`, and update the test script and DoD together.

Future:

- Column picker is deferred.
- Saved export presets are deferred.

### 4.16 Ask AI Workflow

Current client result is Pass. Preserve:

- Floating Ask AI button opens side panel.
- Card AI next-step CTA opens AI with transaction context.
- AI suggestions in expanded drawer open AI with transaction context.

Guardrails:

- AI may rank, summarize, recommend, draft, and explain.
- AI may not complete tasks, change dates, add contacts, send email, call, print, export, or mutate data without explicit user action.
- Attorney/legal questions must stay within the attorney guardrails already in requirements.

---

## 5. Backend Response Contracts

### 5.1 Transaction Cards Endpoint

Keep the BFF endpoint:

`GET /api/v1/dashboard/transaction-cards`

Parameters:

```ts
{
  state_filter?: 'active' | 'pending' | 'closed' | 'all'
  tab?: 'all' | 'overdue' | 'today' | 'needs_attention' | 'closing_soon' | 'in_inspection' | 'on_track' | 'unhealthy'
  sort?: 'urgency' | 'close_date' | 'client_name' | 'price'   // 'updated_at' deferred — see §4.5
  search?: string
  view?: 'personal' | 'team'
  team_member_id?: string
  assignment_scope?: 'all' | 'unassigned'
  page?: number
  page_size?: number
}
```

`useTransactionCards` in `src/hooks/useDashboard.ts` already accepts `search`, but it must be updated to type and forward `view`, `team_member_id`, and `assignment_scope` (and the page must use `team_member_id`, replacing the current unsupported `assignee`).

Return:

```ts
{
  items: TransactionCardAPI[]
  total: number
  generated_at: string
}
```

Tab counts are a separate source-of-truth endpoint:

`GET /api/v1/dashboard/transaction-tab-counts`

Parameters:

```ts
{
  state_filter?: 'active' | 'pending' | 'closed' | 'all'
  search?: string
  view?: 'personal' | 'team'
  team_member_id?: string
  assignment_scope?: 'all' | 'unassigned'
}
```

Return:

```ts
{
  counts: TransactionTabCounts
  total: number
  generated_at: string
}

interface TransactionTabCounts {
  all: number
  overdue: number
  today: number
  needs_attention: number
  closing_soon: number
  in_inspection: number
  on_track: number
  unhealthy: number
}
```

**Tab-count delivery strategy.** Do not inline required `tab_counts` inside `/transaction-cards`; every card fetch, including each keystroke of inline search, would pay for counting work even when the user only wants one tab. Use `GET /api/v1/dashboard/transaction-tab-counts` for counts and drop the seven redundant `useTransactionCards({ tab: ... })` calls currently in `TransactionListPage.tsx`. The counts endpoint must share the same filtering helper as cards/exports, but it must not schedule AI next-step refreshes.

Additions to `TransactionCardAPI`:

```ts
{
  client_names: string[]
  display_title: string          // "Jason Young"
  display_subtitle: string       // "1616 Walker Ave, Indianapolis, IN 462..."
  representation_type: 'Buyer' | 'Seller' | 'Both' | string
  contact_groups: TransactionContactGroupAPI[]
  key_dates: KeyDateAPI[]
}
```

Additions to contacts:

```ts
interface TransactionCardContactAPI {
  id: string | null               // transaction_parties.id when source === 'party', otherwise null
  source: 'party' | 'assignment'  // tells the frontend which API to call for edit/remove
  assignment_id: string | null    // transaction_assignments.id when source === 'assignment'
  name: string
  role: string
  role_label: string
  company: string | null
  email: string | null
  phone: string | null
  is_organization: boolean
  is_current_user: boolean        // true only when source === 'assignment' and user_id === current_user.id
}

interface TransactionContactGroupAPI {
  label: string
  empty_label: string | null
  add_label: string
  default_party_role: string
  default_company: string | null
  show_company_field: boolean
  can_add: boolean
  contacts: TransactionCardContactAPI[]
}
```

Rules:

- `contact_groups` is backend-authored so representation rules are consistent.
- Backend decrypts encrypted PII before returning and leaves plaintext fields as plaintext.
- **Backend never returns ciphertext if decrypt fails.** Fix `_safe_decrypt` in `app/api/v1/dashboard.py`, `_decrypt_safe` in `app/repositories/transaction_party_repository.py`, and `_safe_decrypt_value` in `app/api/v1/documents.py` so encrypted PII failures return `""` (or a fixed `"[Encrypted]"` placeholder) and log a `warning` with the field name. Do not run decrypt on plaintext fields such as party `company`, transaction `city`, `state`, or `zip_code`; otherwise the P0 fix will remove valid company/address display data. Treat this sweep as the first task of Slice 1.
- Contacts from unrecognized roles should not silently disappear without logging.
- `transaction-tab-counts` uses the same status/team/search/assignment scope as `items`.
- **Agents group source union.** The Agents group composes from two sources: (1) `transaction_parties` rows with canonical role in `{listing_agent, buyers_agent}` plus legacy `co_agent` inputs normalized through `party_roles.py` (set `source: 'party'`), and (2) active `transaction_assignments` rows whose `user_id != current_user.id` and whose normalized `role_in_transaction` is agent-facing (`primary_agent`, `agent`, `Agent`, `co_agent`, `listing_agent`, `buyers_agent`; include `TransactionCoordinator` only if product wants coordinators visible in Agents rather than internal assignee context). Set `source: 'assignment'` for assignment rows. The `is_current_user` flag only evaluates against assignment rows, since external parties are not staff users; set it `false` for every `source: 'party'` contact.

### 5.2 Key Date Contract

Use:

```ts
interface KeyDateAPI {
  label: string
  field_name: string
  value: string | null
  time_value: string | null
  status: 'unset' | 'overdue' | 'today' | 'future' | 'cleared'
  is_overdue: boolean
}
```

Rules:

- Keep `is_overdue` during transition for compatibility.
- Frontend uses `status` for color.
- All date values are ISO dates.
- Frontend handles display formatting.

### 5.3 Checklist Contract

Canonical:

`GET /api/v1/transactions/{transaction_id}/checklist`

Compatibility:

`GET /api/v1/transactions/{transaction_id}/closing-checklist`

`GET /api/v1/tasks/transaction/{transaction_id}/closing-checklist`

Return:

```ts
{
  transaction_id: string
  client_names: string[]
  address: string
  closing_date: string | null
  template_source: 'user_profile' | 'team_profile' | 'fallback_task_list'
  checklist_type: 'buyer' | 'seller' | 'both'
  sections: Array<{
    title: string
    items: Array<{
      label: string
      status: 'pending' | 'completed' | 'skipped' | 'overdue'
      due_date: string | null
      source: 'template' | 'task' | 'profile_note' | 'system_reminder'
      target: string | null
      note: string | null
    }>
  }>
  summary: {
    total_items: number
    completed_items: number
    overdue_items: number
  }
}
```

Rules:

- If no user/team template exists, return a fallback task-list checklist and a non-blocking warning string.
- Do not fail print solely because a profile template is incomplete.
- Preserve tenant/assignment access.
- Route registration: declare `GET /transactions/{transaction_id}/checklist` and `GET /transactions/{transaction_id}/closing-checklist` near `PUT /transactions/{transaction_id}/key-dates` in `transactions.py`, and have all aliases call the same service function. These sibling routes have an extra path segment and are not captured by `GET /transactions/{transaction_id}`; keep same-shape static routes above dynamic routes as normal FastAPI hygiene.
- Add a `test_checklist_endpoint_denies_cross_tenant` integration test.

### 5.4 Export Contract

Canonical:

- `GET /api/v1/transactions/export/csv`
- `GET /api/v1/transactions/export/excel`
- `GET /api/v1/transactions/export/pdf`

Enhance accepted filters:

```ts
{
  state_filter?: 'active' | 'pending' | 'closed' | 'all'
  tab?: string
  sort?: string
  search?: string
  view?: 'personal' | 'team'
  team_member_id?: string
  assignment_scope?: 'all' | 'unassigned'
}
```

Rules:

- Export uses the same visibility and filtering logic as card list.
- File naming matches client expectation (`transactions.csv`, `transactions.xls`) unless product approves `.xlsx` before Slice 4.

---

## 6. Data Model

No large migration is required for the client-feedback fixes if existing tables are used correctly. The plan should avoid new tables unless the implementation discovers a durable gap.

Existing tables involved:

- `transactions`
- `tasks`
- `transaction_parties`
- `transaction_assignments`
- `users`
- `documents`
- `communication_logs`
- `audit_logs`
- `task_templates`
- `users.profile_settings_json` for user checklist templates and tagged notes
- `teams.settings_json` or `tenants.settings_json` for team/tenant defaults if user templates are missing

Potential small additions:

1. **Transaction checklist templates**
   - Prefer existing `users.profile_settings_json` for MVP because the schema already documents checklist templates and tagged notes there.
   - If team-level defaults are needed, use `teams.settings_json` or `tenants.settings_json` with a documented shape; do not create a new table unless the JSON shape proves too brittle.
2. **Party organization clarity**
   - Current org detection is role-based (`title_company`).
   - If Lender companies need first-class org rows, add support through role or a non-breaking `is_organization` field.
   - Do not break existing `transaction_parties` rows.
3. **Contact display metadata**
   - Prefer computing display fields in the dashboard BFF response over storing redundant labels.

Tenant safety:

- All added queries must filter by `tenant_id`.
- Mutations must verify transaction access before writing.
- New RLS integration tests are required for any new table, policy, or storage path.

Audit (state, not target):

- Key date changes already write audit rows with before/after (in `update_key_dates`, `transactions.py`). Preserve.
- Task create/status/name/due-date changes: current `PATCH /tasks/{id}` audits status changes only; add missing audit rows for `POST /tasks`, `PUT /tasks/{id}/status`, and non-status task updates without double-writing the existing `PATCH` status audit.
- Contact create/update/delete currently has **no** audit logging in `transaction_parties.py` — this is the real gap and must be added.
- Print and export may be logged as read/report events if compliance wants that; not required to alter workflow state.

---

## 7. Frontend Work

### 7.1 Routing And URL State

- Add route aliases for named transaction views in `App.tsx` (for example `path="/transactions/:statusView?"` or explicit sibling routes). Updating only `TransactionListPage.tsx` is not enough because `/transactions/active` does not currently mount.
- Initialize state from path plus query. Path status wins over `?status=` when both are present; invalid path segments should fall through to 404 or intentionally redirect to `/transactions/active`.
- Persist these to URL:
  - `tab` (`filter` accepted on read as an alias)
  - `sort`
  - `search`
  - `view` (Team Lead/Admin only)
  - `team_member_id` (replaces today's `assignee` param name)
  - `assignment_scope`
  - `highlight` (`expand` accepted on read as an alias)
  - `task`
- Keep `/transactions?status=...` compatible.
- Keep existing `?expand=` deep links compatible while writing `?highlight=` for new links.
- Back button restores prior filter/sort/search/card state.
- Extend `useTransactionCards` in `src/hooks/useDashboard.ts` to declare `view`, `team_member_id`, and `assignment_scope`. `search` is already typed in the hook; the missing work is passing it from the page and including it in URL state.

### 7.2 Query And Invalidation Helper

Add one helper:

```ts
function invalidateTransactionsWorkspace(queryClient, transactionId?: string) {
  queryClient.invalidateQueries({ queryKey: ['dashboard', 'transaction-cards'] })
  queryClient.invalidateQueries({ queryKey: ['dashboard', 'transaction-tab-counts'] })
  queryClient.invalidateQueries({ queryKey: ['dashboard', 'ai-briefing'] })
  queryClient.invalidateQueries({ queryKey: ['dashboard', 'deal-state-counts'] })
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.TRANSACTIONS() })
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.TASKS() })
  if (transactionId) {
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.TRANSACTION(transactionId) })
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.TRANSACTION_PARTIES(transactionId) })
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.TRANSACTION_ASSIGNMENTS(transactionId) })
  }
}
```

Use after:

- task create/update/status
- key date save
- contact create/update/delete
- document upload/delete that changes card counts
- status change

### 7.3 Header And Export Buttons

- Keep buttons visible as tested.
- Replace client-only export for final implementation with backend-backed exports (`/api/v1/transactions/export/csv|excel|pdf`).
- Filenames follow the §4.2 / §4.15 decision: `transactions.csv` and, unless Jake approves `.xlsx`, `transactions.xls`.
- Add pending states on each export button.
- Add destructive toast on failure.

### 7.4 Inline Search

- Add search input beside sort.
- Debounce.
- Persist to `?search=`.
- Use backend `search` param.
- Use the tab-count endpoint for badges while searching; do not fan out seven card queries on each debounced search change.
- Show empty result copy with Clear Search.

### 7.5 Transaction Card Header Context

- Ensure card top line remains client + address.
- Pass both `dealName` and `dealAddress` into:
  - Add Task modal
  - Add Contact modal
  - Documents modal
  - History panel
  - Communications panel
  - Print loading window

### 7.6 Tasks UI

- Add compact status menu per task row.
- Keep checkbox as fast complete/reopen action.
- Disable row action while mutation pending.
- Add accessible labels:
  - `Mark {task} complete`
  - `Change status for {task}`
- Use lucide icons rather than emoji/new inline SVG where practical.

### 7.7 Add Task AI Selection

- Add `selectedSuggestionIndex` state (canonical name, matches §4.8 — do not call this `selectedApproachIndex`).
- Highlight selected approach with champagne border/background.
- Add `aria-pressed` on each suggestion button.
- Add visible `Selected` pill on the chosen card.
- Completion Method select should visibly update when the approach provides a `suggested_method`.
- **Remove the `disabled={!isClickable}` gate** on suggestion buttons in `AddTaskModal.tsx`. Suggestions without a `suggested_method` must still be clickable so the user can pick them as the "chosen approach" even if the method dropdown is left alone. Render "No method change" copy under those suggestions.

### 7.8 Key Dates UI

- Replace local `formatShortDate` variants with shared date formatter that includes year.
- Add `getKeyDateStatus(isoDate, today)` helper for optimistic edits.
- Map `status` to `ve-*` token triads.
- Do not hard-code green for any populated value.
- If saving fails, rollback optimistic override or refetch immediately.

### 7.9 Contacts UI

- Render backend-authored contact groups.
- Show one Add button in each section header.
- Remove per-contact plus buttons (currently rendered at `TransactionCard.tsx` lines ~720-725).
- Display secondary line as company when available.
- Hide redundant Buyer/Seller/Lender/Title role labels where the section title already gives the context.
- Rename agent grouping to `Agents` (backend label change in `STANDARD_CONTACT_GROUPS`).
- Exclude current user contacts flagged by backend as `is_current_user`.
- Use `formatPhoneNumber` for display and input.
- **Remove hardcoded label string comparisons.** Today the card uses `group.label === 'Lender' || group.label === 'Title'` to decide whether to show the Company field. After backend authors `show_company_field` and `default_company` per group, replace these comparisons with the group metadata flags. Renaming "Listing Agent" → "Agents" silently breaks any consumer that compares against group labels — sweep for them.
- For Agents section rows whose `source === 'assignment'`, the edit/remove path goes through `/api/v1/transactions/{transaction_id}/assignments/{assignment_id}`, not `/api/v1/transactions/{transaction_id}/parties/{party_id}`. Don't show a Remove control on assignment rows unless the user has the right role; do not call the parties endpoint for them.

### 7.10 Add Contact Modal

- Keep existing prop names that callers already pass (`roleLabel`, `showCompany`, `transactionId`, `open`, `onClose`) — renaming would force changes at every call site (`TransactionListPage.tsx`, `TransactionCard.tsx` x2). Add the new props *alongside* them:
  - `dealName?: string`
  - `dealAddress?: string`
  - `defaultCompany?: string` (replaces the inferred "no prefill" behavior)
  - `defaultPartyRole?: string` (backend-supplied canonical role; falls back to `ROLE_LABEL_TO_API[roleLabel]`)
  - `organizationMode?: boolean` (renders a single Company-only field instead of First/Last Name)
- Reinitialize form state on open based on props.
- Phone formatter applied on every keystroke; persist digits-only to the backend, format on display.
- Submit company-only when `organizationMode` is true (sends `full_name: company` and `party_role: 'title_company'` or the relevant org role).
- Only enable `organizationMode` for groups whose `default_party_role` is a supported organization role. Title can use `title_company`; Lender should stay person-mode with `defaultCompany` prefilled until a supported lender-organization role exists.
- Keep Company Name editable even when prefilled.
- Use Radix Dialog or add focus trap and focus restoration.

Phone-storage convention: the input formats to `(555) 123-4567` for display, but the submit payload sends digits-only (`5551234567`). The backend stores digits encrypted; the dashboard BFF reformats on read.

### 7.11 Documents Modal

- Add address subtitle.
- Ensure upload success invalidates transaction cards.
- Ensure download action handles missing signed URL with useful error.

### 7.12 Print

- Card-print (`printClosingChecklist`): open `window.open()` synchronously inside the click handler — *before* awaiting any fetch. Then await the checklist payload, then write HTML into the already-open window. The current implementation awaits first, which causes Chromium/Safari to block the popup.
- Update `printClosingChecklist` to call `/api/v1/transactions/{id}/checklist`; keep the legacy tasks URL only as a backend compatibility alias.
- Apply the same rule to the page-header Print Report: synchronous open, then fetch. If `/export/pdf` returns PDF bytes, load them through a Blob URL in an iframe/object or assign the print window to the Blob URL; do not write PDF bytes as HTML. If auto-printing PDFs proves unreliable, add `?format=html` to the same `/export/pdf` endpoint and write that HTML into the already-open window.
- Avoid raw hex in generated in-app UI; printable HTML may use explicit CSS but should still match brand enough for client handoff.
- Use IBM Plex if available, with system fallback for printed windows.

### 7.13 Accessibility And Style

- Use `ve-*` tokens for new UI.
- Replace raw `#C8322F` delete button with `ve-red` or the canonical destructive dialog pattern.
- Use Radix Dialog/AlertDialog for modals.
- Every icon-only button has `aria-label`.
- Escape closes modals and restores focus.
- Enter submits primary forms.
- No nested native buttons.
- Hit targets meet the style guide.

---

## 8. Backend Work

### 8.1 Dashboard Transaction Cards

Update `/dashboard/transaction-cards` to:

- Fix the decrypt helpers used by transaction-card, party, and document-context surfaces: on encrypted PII decrypt failure, return `""` (and `logger.warning`). Do **not** return raw Fernet ciphertext. While doing this, remove accidental decrypt calls around plaintext fields such as `company`, `city`, `state`, and `zip_code`.
- Return `representation_type`.
- Return `client_names`.
- Return `display_title` and `display_subtitle`.
- Add sibling `/dashboard/transaction-tab-counts` endpoint (see §5.1); do not require `tab_counts` in every card response.
- Return contact company fields.
- Build contact groups based on representation and desired labels.
- Build `Agents` group from `transaction_parties` *union* `transaction_assignments`; exclude signed-in user; set the new `source`, `assignment_id`, and `is_current_user` fields.
- Include `default_company`, `default_party_role`, `show_company_field`, and `add_label` metadata per group.
- Return `KeyDateAPI.status`.
- Accept `team_member_id` (canonical) and `assignment_scope=unassigned`; frontend will be renamed from `assignee` to match.

### 8.2 Contact Group Logic

Backend grouping rules:

- Principal sections:
  - Buyer: roles `buyer`, only if representation includes buyer.
  - Seller: roles `seller`, only if representation includes seller.
- Agents:
  - external `listing_agent`, `buyers_agent`, and legacy `co_agent` input normalized through `party_roles.py`;
  - internal assignments when they represent an agent-facing role and are not current user;
  - exclude current signed-in user.
- Lender:
  - `loan_officer` and lender organization if supported.
- Title:
  - `title_company`, `title_rep`.
- Attorney:
  - `closing_attorney`, `settlement_attorney`.
- Supplemental:
  - `inspector`, `appraiser`, `home_warranty`, `other` only when populated.

Company derivation:

- If a contact has `company`, return it as plaintext; do not run it through Fernet decrypt helpers.
- For a group default company:
  - use organization contact name first;
  - then first non-empty `company`;
  - then known transaction field if available.

Frontend mapping cleanup:

- `ROLE_LABEL_TO_API` in `AddContactModal.tsx` maps "Listing Agent" → `listing_agent`. After the rename to `Agents`, this entry stops matching the section title. The cleanest fix is to **stop mapping by label** in the frontend — the backend now emits `default_party_role` on each group, and the modal should consume that directly. Keep `ROLE_LABEL_TO_API` only as a fallback for legacy callers that don't pass `defaultPartyRole`.

### 8.3 Transaction Parties API

Enhance as needed:

- Accept company-only org creation cleanly for `title_company`. Do not introduce a lender organization role unless `party_roles.py`, schemas, tests, and seed data are updated together.
- **Add audit logging** for create/update/delete — none of these endpoints currently audit. Follow the `_audit(...)` pattern already used in `update_key_dates` (`transactions.py`) for before/after snapshots.
- Preserve current role validation.
- Keep tenant and transaction access checks (the existing `_get_authorized_transaction` helper).
- Return the created/updated party with decrypted encrypted fields and plaintext `company`.

### 8.4 Key Dates

- Add backend helper to compute date status.
- Consider task/milestone completion in future; for this fix, date less than today should return `overdue` unless explicitly cleared.
- Update tests for past/today/future/unset.

### 8.5 Print Checklist

- Add canonical `GET /api/v1/transactions/{transaction_id}/checklist`.
- Add transaction-level compatibility alias `GET /api/v1/transactions/{transaction_id}/closing-checklist`.
- Compose checklist from:
  - transaction metadata;
  - transaction parties;
  - task list;
  - user/team profile checklist templates;
  - tagged profile notes;
  - seller escrow overage reminders.
- Keep fallback task-list response when templates are absent.
- Preserve old tasks endpoint as alias.
- Put checklist composition in a service module so all aliases return one response contract.

### 8.6 Exports

- Make exports use the same card filtering logic.
- Add filters for status/tab/search/team/team-member/assignment-scope/sort.
- Keep role/tenant access identical to page data.
- Ensure CSV escaping, Excel encoding, and PDF text wrapping for long addresses/names.

### 8.7 Audit And Communication Logs

Audit work is a **delta against existing coverage** — do not double-write.

Already audited (preserve):

- Key date update — written by `update_key_dates` in `transactions.py`.

Known task audit gaps:

- `task_created` for `POST /tasks`.
- `task_status_changed` for `PUT /tasks/{id}/status`.
- `task_updated` for non-status changes in `PATCH /tasks/{id}`.
- Preserve the existing `PATCH /tasks/{id}` status audit and do not double-write it.

Newly required (no existing coverage):

- `contact_added` (POST `/transactions/{id}/parties`)
- `contact_updated` (PUT `/transactions/{id}/parties/{party_id}`)
- `contact_removed` (DELETE `/transactions/{id}/parties/{party_id}`)

Optional / compliance-only:

- `transaction_exported`
- `transaction_checklist_printed`

Do not use communication logs for internal UI-only actions unless an actual communication occurred.

---

## 9. Edge Cases

| Case | Required Behavior |
| --- | --- |
| Same client has two active properties | Every card/modal/print surface shows property address beside client name. |
| User edits key date into past | Date turns red immediately and remains red after refetch. |
| Date is today | Date shows amber consistently. |
| Date has no year in old UI | All key dates display with year. |
| Add lender assistant from lender section | Company Name prefilled from current lender company and editable. |
| Empty Title section has known company | Add Contact opens with Quality Title prefilled, not blank. |
| User represents buyer only | Seller principal section hidden by default. |
| User represents seller only | Buyer principal section hidden by default. |
| User represents both | Buyer and Seller sections both show. |
| Signed-in user appears in parties/assignments | Agents section excludes them. |
| Team Lead chooses Unassigned | Frontend sends `view=team&assignment_scope=unassigned`; backend returns transactions with no active assignment rows. |
| Existing contact has no company | Secondary line is omitted or falls back to useful role only for non-principal sections. |
| Phone pasted as digits | Input formats to `(555) 123-4567`. |
| AI suggestion selected then toast disappears | Selected suggestion remains highlighted. |
| Print popup blocked | Frontend opens window synchronously; if still blocked, toast explains to allow popups. |
| Checklist template missing | Fallback task-list checklist prints with a calm warning. |
| Transaction deleted in another tab | Toast and refetch; expanded card closes. |
| Export with many transactions | Backend streams/export all filtered rows; frontend does not freeze. |
| Excel export filename | File extension matches bytes: `.xls` uses legacy Excel HTML workbook, `.xlsx` uses Office Open XML only if approved. |
| Closed transaction | Read-only task/date/contact controls; documents/history/print still available. |
| Offline | Mutations disabled or queued only if existing offline queue is active; show offline banner. |
| PII decrypt fails | Show safe placeholder; do not leak ciphertext. |
| Plaintext company/city/state/zip fields | Continue to display; they are not passed through Fernet decrypt helpers. |
| Old deep links use `expand` or `filter` | Page accepts them and maps to canonical `highlight` / `tab` state without breaking. |
| Cross-tenant transaction id in URL | 404/403 with no data leakage. |

---

## 10. Test Plan

### Backend

- `test_safe_decrypt_returns_empty_on_decrypt_failure` *(security regression test for the PII fix)*
- `test_party_repository_decrypt_failure_does_not_return_ciphertext`
- `test_plaintext_company_city_state_zip_survive_decrypt_sweep`
- `test_dashboard_team_member_id_filter_actually_changes_results` *(catches the silent-drop bug)*
- `test_dashboard_assignment_scope_unassigned_filters_to_unassigned_transactions`
- `test_transaction_cards_include_client_names_address_and_representation_type`
- `test_transaction_tab_counts_match_filtered_scope`
- `test_transaction_tab_counts_search_counts_match_items`
- `test_transaction_tab_counts_does_not_schedule_ai_refresh`
- `test_transaction_card_response_includes_source_and_assignment_id_fields`
- `test_key_dates_return_overdue_today_future_unset_statuses`
- `test_contact_groups_hide_unrepresented_buyer_or_seller_sections`
- `test_contact_groups_show_both_principal_sections_for_both_representation`
- `test_agents_group_includes_co_agent_party_and_other_assignments`
- `test_agents_group_excludes_signed_in_user_from_assignments`
- `test_contact_groups_include_company_and_default_company`
- `test_contact_group_emits_default_party_role_and_show_company_field`
- `test_create_party_allows_company_prefill_payload`
- `test_create_party_writes_audit_log`
- `test_update_party_writes_audit_log`
- `test_delete_party_writes_audit_log`
- `test_create_task_writes_audit_log`
- `test_put_task_status_writes_audit_log`
- `test_transactions_checklist_endpoint_returns_profile_template_when_available`
- `test_transactions_checklist_endpoint_falls_back_to_task_list`
- `test_checklist_endpoint_denies_cross_tenant`
- `test_transactions_closing_checklist_alias_still_works`
- `test_legacy_tasks_closing_checklist_endpoint_still_works`
- `test_export_csv_respects_state_tab_search_filters`
- `test_export_excel_respects_state_tab_search_filters`
- `test_export_excel_filename_and_content_type_match_approved_extension`
- `test_export_pdf_respects_state_tab_search_filters` *(supports Print Report)*
- `test_transaction_card_access_denies_cross_tenant_data`
- RLS integration test for transaction/task/party read isolation if any policy/query changes are made.

### Frontend Unit / Integration

- `TransactionListPage initializes status view from /transactions/active alias`
- `TransactionListPage preserves /transactions?status=closed compatibility`
- `TransactionListPage accepts ?filter as a tab alias and ?highlight as an expand alias`
- `TransactionListPage honors ?tab ?sort ?search on first render`
- `TransactionListPage sends backend search param after debounce`
- `TransactionListPage sends view team_member_id and assignment_scope instead of assignee`
- `TransactionListPage uses tab-counts endpoint instead of seven card count queries`
- `TransactionListPage export buttons request backend filtered exports`
- `TransactionListPage Print Report opens a window synchronously before fetching`
- `TransactionCard shows client name and address together`
- `TransactionCard date row renders past date in red with year`
- `TransactionCard optimistic date edit uses overdue color for past date`
- `TransactionCard contact secondary line shows company not role`
- `TransactionCard hides per-contact plus buttons and shows one add per section`
- `AddTaskModal keeps selected AI suggestion highlighted`
- `AddTaskModal applies suggested completion method`
- `AddContactModal preloads default company for lender/title`
- `AddContactModal formats phone while typing`
- `AddContactModal supports company-only organization add`
- `DocumentsModal header shows client and property address`
- `printClosingChecklist opens window before awaiting API`
- `printClosingChecklist calls the canonical transactions checklist endpoint`
- Keyboard path: expand card, open Add Contact, submit, Escape close.

### E2E

One Playwright path for core client fixes:

1. Log in as Agent.
2. Open `/transactions`.
3. Confirm header title and total count.
4. Expand a transaction where the same client name appears in another deal.
5. Confirm card/modal context shows client plus property address.
6. Edit a key date to yesterday.
7. Confirm it turns red and displays year.
8. Open Add Task.
9. Get AI suggestions and select one.
10. Confirm selected suggestion remains highlighted.
11. Open Add Contact from Lender.
12. Confirm Company Name is prefilled and phone formats while typing.
13. Submit contact and confirm it appears with company under name.
14. Click Print.
15. Confirm a printable window opens without a popup-blocker error.
16. Click Ask AI and confirm side panel opens.
17. Open `/transactions/active?filter=overdue&highlight=<transactionId>` and confirm the alias URL expands the matching card.
18. Export CSV and Excel and confirm filenames/bytes match the approved extension.

Second Playwright path for representation:

1. Create or seed buyer-represented transaction.
2. Confirm Buyer section renders and Seller principal section does not.
3. Create or seed seller-represented transaction.
4. Confirm Seller section renders and Buyer principal section does not.
5. Create or seed both-side transaction.
6. Confirm both sections render.

---

## 11. Rollout Sequence

### Slice 1 - Critical Fixes, Context, Dates, And Print Reliability (1-2 days)

Lead with the security and silent-bug fixes, then the visible client feedback:

1. **Decrypt safety sweep** — return `""` and `logger.warning` on encrypted PII decrypt failure in dashboard/party/document-context helpers, and stop decrypting plaintext company/city/state/zip fields. Add decrypt-failure and plaintext-survival tests.
2. **`assignee` → `team_member_id` rename plus `assignment_scope`** — update `TransactionListPage.tsx` to send `view`, `team_member_id`, and `assignment_scope=unassigned`; extend `useTransactionCards` typing accordingly. Add tests for Team Lead "All Team Members" / "My Transactions" / "Unassigned".
3. **Print popup synchronous open** — restructure `printClosingChecklist` so `window.open()` runs *before* `await apiFetch(...)`.
4. **Canonical checklist endpoint** — add `GET /api/v1/transactions/{id}/checklist`, transaction-level `/closing-checklist` alias, and legacy tasks alias backed by one service.
5. **Route aliases** — `/transactions/active|pending|closed|all` in `App.tsx`, with `?status=`, `?filter=`, `?tab=`, `?highlight=`, and `?expand=` compatibility.
6. **Client + address context** — pass `dealName` and `dealAddress` through Add Task / Add Contact / Documents / History / Communications / Print loading window.
7. **Key date status contract** — backend returns `KeyDateAPI.status`; frontend uses it for color and the optimistic-edit helper.
8. Focused tests for the four above (decrypt, team filter, print sequencing, key dates).

### Slice 2 - Contact Workflow Completion (2 days)

- Extend dashboard contact contract with company/group metadata.
- Implement representation-based sections.
- Rename Agents group and exclude current user.
- Remove per-contact plus buttons.
- Add section-level add controls.
- Prefill Add Contact from group context.
- Phone formatting in Add Contact.
- Contact audit logs.
- Backend/frontend tests for contact grouping and modal prefill.

### Slice 3 - Task UX And Page Controls (1-2 days)

- **Consolidate tab counts before adding search** — split out `/dashboard/transaction-tab-counts` and drop the 7 redundant per-tab `useTransactionCards` calls. Doing this first prevents every keystroke of inline search from fanning out 7x into the cards endpoint and prevents count refreshes from scheduling AI next-step work.
- Add inline search with URL state and 300 ms debounce.
- Add task status dropdown using canonical `TaskStatus` enum values (`Pending`, `InProgress`, `Completed`, `Blocked`, `Skipped`) with user-facing labels that add spaces where needed.
- Keep checkbox fast path; menu is for non-binary statuses.
- Add `selectedSuggestionIndex` selection state on AI suggestions; remove the disabled-when-no-method gate.
- Tests for task status, AI selection, URL state, and the tab-count consolidation.

### Slice 4 - Exports And Checklist Templates (2 days)

- Preserve `.xls` for MVP unless Jake approves `.xlsx` before Slice 4; whichever path is chosen, extension, bytes, content type, and tests must match.
- Backend-backed CSV/Excel/PDF exports using full filtered corpus; extend `/export/csv|excel|pdf` to accept `state_filter`, `tab`, `search`, `view`, `team_member_id`, `assignment_scope`, and `sort` (matches the cards endpoint).
- Use the extended `/export/pdf` for the page-header Print Report — no new `/transactions/report` endpoint. Load PDF bytes via Blob URL/iframe or add an HTML variant on the same endpoint.
- Filename follows the §4.15 decision.
- Checklist response uses profile/team template data with `template_source` indicator and a calm fallback when templates are missing.
- Tests for export filters and checklist fallback/template source.

### Slice 5 - Accessibility, Polish, And Client QA (1 day)

- Replace custom modal/focus gaps where necessary.
- Remove raw color literals in touched UI.
- Verify keyboard paths.
- Sweep the product tour (`tourSteps.tsx`) for references to per-row "+" buttons that no longer exist after Slice 2.
- Screenshot pass against `VE-ActiveTransactions.html` and `STYLE_GUIDE.md`.
- Run focused backend tests, frontend tests, and Playwright smoke.

---

## 12. Future Improvements

These should not block the client-feedback fixes unless Jake reprioritizes them.

| Suggestion | Priority | Plan |
| --- | --- | --- |
| Recently Updated sort | Low | Add `updated_at` to `TransactionCardResponse`, extend `_sort_cards`, widen the route pattern, and expose in `useTransactionCards`. Deferred from §4.5 because it's three coupled changes for a low-value sort. |
| Saved custom filter views | Low | Implement after URL state is stable; save named combinations of status/tab/search/sort/team filters. |
| Bulk actions | Skip for MVP | Revisit only after client understands and requests it; define as selecting multiple transaction cards to reassign or change status. |
| Export column picker | Low | Add after backend export contract is authoritative. |
| Inline task rename | Low | Use task PATCH; avoid if it crowds the task row. |
| Drag-and-drop task reordering | Low | Requires `sort_order` mutation and dependency safety. |
| Snooze task | Medium later | Needs task snooze columns and reminder logic. |
| Contact last contacted | Medium later | Derive from communication logs; display in contact group. |
| Log a call shortcut | Medium later | Use `communication_logs` with `channel='voice_call'`; can pair with future call provider. |
| Pick from existing contacts | Medium | Use contact directory search and link existing contact to transaction. |
| Common task templates | Medium | Use task template library with one-click create. |
| Recurring tasks | Low | Requires recurrence model. |
| Attach document while creating task | Low | Link task creation to existing document upload flow. |
| Rename document from modal | Low | Already exists elsewhere; add inline modal action later. |
| Auto-suggest document type on upload | Medium | Reuse AI intake classification. |
| Download all documents as zip | Low | Requires backend zip stream and storage read fan-out. |
| History event type chips | Low | Client passed history; add later if timeline grows noisy. |
| Export history PDF | Low | Later reporting feature. |
| Print template picker | Low | Depends on checklist template system. |
| Choose print sections | Low | Add after template picker. |

---

## 13. Definition Of Done

The Transactions page is complete when:

- `/transactions`, `/transactions/active`, `/transactions/pending`, `/transactions/closed`, and `/transactions/all` work.
- Existing deep links using `?status=`, `?filter=`, and `?expand=` still work; new links can use `?tab=` and `?highlight=`.
- Header title and total count match the active status/filter/search/team/assignment scope.
- Filter tab badges come from one count endpoint and match the active status/search/team/assignment scope.
- Export CSV and Excel download the full filtered result set with approved filenames and matching file bytes.
- Print checklist opens reliably and never fails because the popup opened after async work.
- Print checklist uses profile/team templates or a clear fallback.
- Ask AI opens the side panel and never mutates data without user approval.
- Expanded card headers and all related modals show client name plus property address.
- Task checkbox and task status menu both persist and refetch correctly.
- Add Task AI selection remains highlighted after selection.
- Past key dates render red; dates are formatted consistently with year.
- Contact sections match representation type.
- Agents section is titled `Agents` and excludes the signed-in user.
- Lender, Title, and Agent contacts show company under the name when present.
- Buyer and Seller contacts do not show redundant role text; company displays only when filled.
- Add Contact prefills company/name from group context where available.
- Phone numbers format while typing in Add Contact.
- One add control appears per contact section, not per person row.
- Documents modal shows the property address beside the client name.
- History panel still passes current behavior.
- Team Lead "Unassigned" sends `assignment_scope=unassigned` and returns only unassigned transactions.
- All mutations are tenant-scoped, role/assignment checked, and audited where they change data.
- Fernet decrypt failures never return ciphertext, and plaintext company/address component fields still display.
- No touched modal uses browser `alert`, `confirm`, or `prompt`.
- Keyboard-only usage works for card expand, task update, date edit, add contact, add task, documents, history, print, and AI panel.
- Focus rings, tokens, spacing, and copy follow `STYLE_GUIDE.md`.
