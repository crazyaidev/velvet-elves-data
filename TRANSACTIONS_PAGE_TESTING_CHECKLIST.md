# Transactions Page — Comprehensive Feature Testing Checklist

> **Run 1 (2026-08-01):** executed in full — 162 pass, 62 fail, 9 partial,
> 24 not verifiable. Results in `TRANSACTIONS_PAGE_TEST_FINDINGS_2026-08-01.md`.
>
> **Run 2 (2026-08-04), post-fix:** the rows covering the 24 fixed findings were
> re-run in a real browser and all now pass — §2 (toolbar/exports/search), §3
> (tabs/counts), §4 (sort deep link), §5 (days-to-close), §11 (URL state, empty
> and error states), §12–§14 (detail header, tab bar, Overview), §15 (tracking
> rail), §16 (Documents ▸ Checklist), §18 (`?qa=`/`?access=`), §19 (Billing,
> Activity timestamps), §20 (responsive) and §10/TX-204–205 (panel a11y).
> The 24 "not verifiable" rows still need a seeded tenant (Closed/Pending deals,
> >20 deals, a second session). Evidence: remediation plan §9.3.
>
> Scope: the `/transactions` surface family and the transaction detail page.
> Routes covered: `/transactions`, `/transactions/active`, `/transactions/pending`,
> `/transactions/closed`, `/transactions/all`, `/transactions/:transactionId`.
>
> Author: Jan Froben · Date: 2026-08-01 · Environment: local
> (frontend `http://localhost:5173`, backend `http://localhost:8000`)
> Tester role: **Admin** (`shyna.elene@minafter.com`)
>
> Method: mouse-driven testing in a real Chrome browser, per
> `FRONTEND_UI_TESTING_GUIDELINES.md`. Every item is validated by what renders
> and what the network does — never by reading code alone.
>
> Companion documents:
> - Results → `TRANSACTIONS_PAGE_TEST_FINDINGS_2026-08-01.md`
> - Remediation → `TRANSACTIONS_PAGE_REMEDIATION_PLAN_2026-08-01.md`

---

## 0. How to read this checklist

Each row has a stable ID (`TX-###`). The **Expected** column states the
behaviour the product is supposed to have, and every expectation is grounded in
one of these sources — cited inline where the expectation is not self-evident:

| Tag | Source of truth |
| --- | --- |
| `[SPEC]` | `FRONTEND_UI_WORKFLOW_LOGIC.md` §4.1–4.6 (the page specification) |
| `[PLAN]` | `TRANSACTION_PAGE_REDESIGN_SUPERIORITY_PLAN.md`, `ACTIVE_TRANSACTIONS_CARD_TO_WORKSPACE_MIGRATION_PLAN.md` §16 |
| `[STYLE]` | `STYLE_GUIDE.md` |
| `[SRC]` | Behaviour the current frontend/backend source commits to |
| `[UX]` | General correctness — no negative/nonsense values, no dead controls |

Result codes: **PASS** · **FAIL** · **PARTIAL** · **BLOCKED** · **N/A**

---

## 1. Environment, access and routing

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-001 | Local stack health | Backend `/health`, frontend root respond | Backend `{"status":"ok"}`, frontend HTTP 200 |
| TX-002 | Admin login | Log in through the real login form | Lands authenticated; `velvet_elves_token` present |
| TX-003 | `/transactions` base route | Navigate to `/transactions` | Renders the Active Transactions list (default status view) `[SRC]` |
| TX-004 | `/transactions/active` alias | Navigate | Title "Active Transactions", breadcrumb `Deals › Active Transactions` `[SPEC §4.1]` |
| TX-005 | `/transactions/pending` alias | Navigate | Title "Pending Transactions"; same card list as Active `[SPEC §4.2]` |
| TX-006 | `/transactions/closed` alias | Navigate | Title "Closed Transactions"; no filter tab bar `[SPEC §4.3]` |
| TX-007 | `/transactions/all` alias | Navigate | Title "All Transactions"; status tab bar All/Active/Incomplete/Paused/Completed/Closed `[SPEC §4.4]` |
| TX-008 | Detail route | Navigate to `/transactions/:id` | Transaction detail page for that deal, not a 404 |
| TX-009 | Unknown transaction id | Navigate to `/transactions/<random-uuid>` | Friendly "not found / no access" state, not a blank page or crash `[SPEC §4.6]` |
| TX-010 | Role routing | Admin role | Internal list + workspace render (Attorney would get the Matter Workspace) `[SRC]` |
| TX-011 | Console/network hygiene | Watch console + XHR through a full sweep | No uncaught errors, no 4xx/5xx from page-owned calls |

---

## 2. List page — header and toolbar

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-020 | Breadcrumb | Inspect header | `Deals › <view name>`; hidden on phone widths `[SPEC §4.1]` |
| TX-021 | Page title + count pill | Inspect header | Serif title + mono count pill; count equals total matching the current filter `[SPEC §4.1]` |
| TX-022 | Count pill pluralisation | View with 1 vs many deals | "1 deal" / "N deals" |
| TX-023 | Team-member filter (TeamLead/Admin) | Open the select | Options: All Team Members · My Transactions · Unassigned · each roster member `[SRC]` |
| TX-024 | Team filter — My Transactions | Select | List re-queries with `view=personal`; only own deals |
| TX-025 | Team filter — Unassigned | Select | Re-queries with `assignment_scope=unassigned` |
| TX-026 | Team filter — specific member | Select a member | Re-queries with `team_member_id=<uuid>` |
| TX-027 | **Inline search input** | Look below the tab bar | A search input exists and filters the list, debounced 300 ms, persisted to `?search=` `[SPEC §4.1 "Below tabs: Sort control dropdown + inline search input"]` |
| TX-028 | Search deep link | Load `/transactions/active?search=<term>` | List filtered by the term; input pre-filled with it |
| TX-029 | Search empty result | Search a term with no match | "No transactions match '<query>'" + a clear affordance `[SPEC §4.1]` |
| TX-030 | Export CSV | Click | File downloads; success feedback; failure raises a toast |
| TX-031 | Export Excel | Click | `.xlsx` downloads (hidden below `md`) |
| TX-032 | Print Report | Click | PDF of the current filtered set `[SPEC §4.1 "Print report: PDF summary of all visible transactions (respecting current filter)"]` |
| TX-033 | Exports honour filters | Apply a team filter/search, then export | Export request carries the same `state_filter`/`search`/team params `[SRC]` |
| TX-034 | Header responsiveness | 1600 px → 1024 px → 375 px | Title row stacks on phone; count chip never collides with the filter `[SRC]` |

---

## 3. List page — filter tabs and counts

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-040 | Tab set | Inspect the strip on `/transactions/active` | All · Overdue · Due Today · Needs Attention · Closing Soon · In Inspection · On Track · Unhealthy `[SRC]` |
| TX-041 | Tab counts source | Watch network | One `GET /dashboard/transaction-tab-counts` call feeds every badge (not one call per tab) `[SRC]` |
| TX-042 | Counts are accurate | Compare each badge with the cards the tab returns | Badge count == number of cards the tab renders |
| TX-043 | Tab click filters | Click each tab in turn | Card list re-queries with the tab's `apiTab`; active tab styled orange |
| TX-044 | Tab click updates the URL | Click a tab | URL reflects the tab so refresh/back restores it `[SPEC §4.1 "URL updates to ?filter=overdue"; §6 "Back navigation: browser back restores previous filter/sort/search state"]` |
| TX-045 | `?tab=` deep link | Load `/transactions/active?tab=overdue` | Overdue tab pre-selected |
| TX-046 | `?filter=` alias | Load `?filter=overdue` | Same as `?tab=` `[SRC]` |
| TX-047 | Red-count styling | Inspect Overdue / Due Today badges | Rendered in the red badge treatment `[SRC]` |
| TX-048 | Mutually consistent counts | Compare All vs the sum/subsets | No tab may exceed All; a deal counted "Unhealthy" must not also read "On Track" |
| TX-049 | Tabs hidden off the Active view | Visit pending/closed/all | Active-only tab strip is not shown on pending/closed `[SRC]`; `/all` should have its own status tabs `[SPEC §4.4]` |
| TX-050 | Tab strip scrolls on mobile | 375 px | Tabs scroll horizontally; the sort chip stays reachable `[SRC]` |

---

## 4. List page — sort

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-060 | Sort menu opens | Click the sort chip | Menu with Urgency · Close Date · Client Name · Price; current option check-marked |
| TX-061 | Sort by Urgency | Select | Re-queries `sort=urgency`; most critical first |
| TX-062 | Sort by Close Date | Select | Re-queries `sort=close_date`; ordering visibly changes |
| TX-063 | Sort by Client Name | Select | Alphabetical by display title |
| TX-064 | Sort by Price | Select | Ordered by purchase price |
| TX-065 | Sort persists in the URL | Select a sort, refresh | Selection survives `[SPEC §4.1 "URL updates to ?sort=close_date"]` |
| TX-066 | Sort applies to Closed view | On `/transactions/closed` | Sort control available; default newest-closed first `[SPEC §4.3]` |

---

## 5. List page — card collapsed face

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-070 | Urgency left bar | Inspect cards | Red/amber/green left border matching the stage pill colour |
| TX-071 | Deal title links to the workspace | Click the title | Navigates to `/transactions/:id` (does not toggle the drawer) |
| TX-072 | Stage pill | Inspect | Icon + label, coloured by urgency |
| TX-073 | Why badges | Inspect | Reason chips (e.g. "34 overdue tasks", "No documents") |
| TX-074 | Address line | Inspect | Composed address with no duplicated city/state/zip `[SRC · address-compose invariant]` |
| TX-075 | Assignee chip | Inspect | Shows the assigned staff name when set |
| TX-076 | AI next-step banner | Inspect | "Next step: …" + context sentence + CTA button `[SPEC §4.1]` |
| TX-077 | Next-step label casing | Read the banner text | Reads as natural product copy, not a mangled lower-cased label `[UX]` |
| TX-078 | Next-step CTA | Click | Opens the task email flow for the backing task, else the AI chat `[SRC]` |
| TX-079 | Primary contact line | Inspect | Avatar, name, role, `tel:` link; clicking the phone does not toggle the card |
| TX-080 | Milestone bar | Inspect | Contract → EM → Inspection → Appraisal → CD Del. → CTC → Close with per-dot status `[SPEC §4.1]` |
| TX-081 | Info badges | Inspect | Tasks and Docs at minimum; spec also names Emails, Notes, Missing Docs, Client Touch, Lender Touch, History `[SPEC §4.1]` |
| TX-082 | Docs badge click | Click the Docs badge | Opens the Documents modal |
| TX-083 | History badge click | Click the History badge | Opens the History panel `[SRC — handler exists]` |
| TX-084 | Days-to-close stat | Inspect | Number + "DAYS TO CLOSE" + closing date; colour reddens near closing |
| TX-085 | **Days-to-close for a past date** | Find a deal whose closing date has passed | Must not display a raw negative number; needs an "overdue/past" treatment `[UX]` |
| TX-086 | Overdue stat | Inspect | Count or "No Overdue"/"Pending"/"Complete" with matching colour |
| TX-087 | Price stat | Inspect | Currency formatted, no decimals |
| TX-088 | Maximize icon | Click | Opens `/transactions/:id` |
| TX-089 | Expand chevron / card body click | Click the card body | Drawer expands; chevron rotates |
| TX-090 | Collapsed-face responsiveness | 375 px | Stats row wraps below; milestone bar behaviour per spec |

---

## 6. List page — expanded drawer, column 1 (Tasks)

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-100 | Tasks column renders | Expand a card | "Tasks" heading, full-view expander, "+ Add" |
| TX-101 | Task grouping | Inspect section headers | Grouped Overdue / Due Today / Upcoming / Completed `[SPEC §4.1]` |
| TX-102 | Task row anatomy | Inspect | Checkbox, name, due text (mono, red when overdue), email button |
| TX-103 | Complete a task | Click an unchecked checkbox | Optimistic tick; `PATCH /tasks/:id {status:'Completed'}`; toast "Task completed" with **Undo** |
| TX-104 | Undo a completion | Click Undo in the toast | Task returns to Pending |
| TX-105 | Reopen a completed task | Click a ticked checkbox | Sets Pending; toast "Task reopened" |
| TX-106 | Completed styling | Inspect a done row | Green filled box + strikethrough |
| TX-107 | Skipped task styling | Find a Skipped task | Not shown as completed; its state is legible `[SRC]` |
| TX-108 | Task email button | Click the mail icon on a row | Opens the Task Email Flow with the party pre-resolved `[SRC]` |
| TX-109 | Task list scrolls | Deal with many tasks | Column scrolls internally at ~260 px, page does not jump |
| TX-110 | "+ Add" / "+ Add Task" | Click either | Opens Add Task modal with deal context |
| TX-111 | Full-view expander | Click the maximize icon | TasksFullViewModal opens with search + filter over every task |
| TX-112 | Full view — toggle a task | Tick a row inside the modal | Same optimistic completion path |
| TX-113 | Full view — Add Task | Click Add inside the modal | Add Task modal layers on top and is usable |
| TX-114 | Task counts agree | Compare the Tasks badge with the drawer | Overdue count on the badge equals the overdue rows shown |

---

## 7. List page — expanded drawer, column 2 (Key Dates)

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-120 | Key Dates column | Expand a card | Heading + "Click to edit" hint |
| TX-121 | Date rows | Inspect | EM Delivered · Inspection Response · Appraisal Expected · CD Delivered · Cleared to Close · Closing Date · Possession `[SPEC §4.1]` |
| TX-122 | Colour by status | Inspect | Red overdue · amber today · green future · neutral unset (server-driven) `[SRC]` |
| TX-123 | Unset date | Inspect an empty row | Shows "Not yet" rather than a blank |
| TX-124 | Time value | Inspect Closing/Possession | Stored time rendered when present |
| TX-125 | Open the editor | Click a row | `DateEditPopover` anchored to the row, pre-filled with the current ISO value |
| TX-126 | Save a date | Pick a date, Save | Optimistic value + colour; `PUT /transactions/:id/key-dates`; toast "Date updated" |
| TX-127 | Save a past date | Set a date in the past | Renders red immediately (optimistic mirrors the server contract) `[SRC]` |
| TX-128 | Cancel the editor | Open, Cancel | No change, no request |
| TX-129 | Closing-date edit and the plan | Edit Closing Date from the card | Rule-driven deadlines must not be silently stranded — the cascade is the documented owner of closing/possession `[PLAN §16.2]` |
| TX-130 | Date edit refreshes counts | After saving | Card badges/tab counts reflect the new state |
| TX-131 | Sync deadlines button | Click | Calendar sync action available per connected-calendar state |

---

## 8. List page — expanded drawer, column 3 (Contacts)

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-140 | Contacts column | Expand a card | Heading + "Assign team" button (Agent/TeamLead/Admin) |
| TX-141 | Representation-aware groups | Inspect | Buyer · Seller · Agents · Lender · Title, per the backend's group contract |
| TX-142 | Contact row | Inspect | Avatar (round person / square org), name, company-or-role, phone + email icons |
| TX-143 | Expand a contact | Click the row | Detail panel with `tel:` and `mailto:` links |
| TX-144 | Per-group Add | Click "Add" in a group header | Add Contact modal pre-set to that role, company field per group |
| TX-145 | Empty group placeholder | Find an empty group | Dashed "Add …" affordance that opens the same modal |
| TX-146 | Create a contact | Submit the modal | `POST /transactions/:id/parties`; card refreshes; toast |
| TX-147 | Edit / remove a contact | Look for the affordance | Spec and plan both describe managing parties from this surface `[SPEC §4.6 People]` |
| TX-148 | Assign team modal | Click "Assign team" | Roster with assignable roles; Admin may add; TeamLead/Admin may remove |
| TX-149 | Assignment reflected on the card | After assigning | Assignee chip updates |

---

## 9. List page — drawer footer, invoices and AI strip

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-160 | Invoices panel | Expand a card | "Invoices & Payments" with count, rows lazy-fetched at `scope=tenant` |
| TX-161 | Invoice row anatomy | Inspect | Status pill (Draft/Sent/Paid/Void/Uncollectible), payer, due-or-paid date, amount |
| TX-162 | Invoice row link | Click a row | Opens the invoice detail |
| TX-163 | "View all" overflow | Deal with >5 invoices | Link to `/payments` |
| TX-164 | Create invoice from the panel | Click the create affordance | NewInvoiceModal prefilled with the deal |
| TX-165 | Invoices empty state | Deal with none | Honest empty state, no fabricated rows `[SRC · no-demo-data rule]` |
| TX-166 | AI suggestions strip | Expand a card | Up to 3 contextual chips |
| TX-167 | AI suggestion click | Click a chip | Opens the AI chat with the deal context and that prompt |
| TX-168 | Footer — Open workspace | Click | Navigates to `/transactions/:id` |
| TX-169 | Footer — View/Add Docs | Click | Documents modal |
| TX-170 | Footer — Print | Click | Closing checklist print flow; failure raises a toast |
| TX-171 | Footer — History | Click | History panel |
| TX-172 | Footer — Comms | Click | Communications panel |
| TX-173 | Footer — Client access | Click | Manage Client Access modal |
| TX-174 | Footer — Client Q&A | Click | Client thread drawer; amber dot when the client is waiting |
| TX-175 | Footer — Invoice | Click | NewInvoiceModal prefilled |
| TX-176 | Footer — Delete (TeamLead/Admin) | Click | Confirm dialog naming the address; delete removes the card; 403 handled with its own message |
| TX-177 | Footer price | Inspect | Matches the collapsed-face price |

---

## 10. List page — modals and panels

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-190 | Add Task modal | Open | Task Name (required), Completion Method, Due Date, Assign To `[SPEC §4.1]` |
| TX-191 | Add Task — AI suggestions | Click "Get AI Suggestions…" | Approach cards; clicking one fills Completion Method + toast |
| TX-192 | Add Task — submit | Submit | `POST /tasks`; card refreshes; modal closes; toast |
| TX-193 | Add Task — validation | Submit empty | Blocked with a clear message |
| TX-194 | Documents modal | Open | Document list with upload, rename/classify, download, email, versions, delete |
| TX-195 | Documents modal — upload | Upload a file | Appears in the list; parse/verification behaviour visible |
| TX-196 | Documents modal — missing docs | Inspect | Missing-documents panel present |
| TX-197 | Add Contact modal | Open | Company (role-dependent), First (required), Last, Phone, Email |
| TX-198 | Manage Client Access modal | Open | Invite / add / remove portal client; pending invite state |
| TX-199 | Client Q&A drawer | Open | Client questions left, team replies right; reply posts and appears |
| TX-200 | History panel | Open | Event timeline grouped by date, searchable |
| TX-201 | Communications panel | Open | Communication log with filters and actions |
| TX-202 | Task Email Flow | Open from a task | Recipient pre-resolved; AI draft; send-and-complete offer |
| TX-203 | New Invoice modal | Open | Prefilled transaction; creates an invoice |
| TX-204 | Modal close hygiene | Open/close each | One close control only; ESC and backdrop behave; text selection drag does not close `[SRC]` |
| TX-205 | Modal a11y | Tab through | Focus trapped, labels present |

---

## 11. List page — URL state, empty/loading/error

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-210 | `?expand=<id>` | Load with the param | That card auto-expands and scrolls into view |
| TX-211 | `?highlight=<id>` alias | Load | Same as `?expand=` `[SRC]` |
| TX-212 | `?expand=<id>&task=<id>` | Load | Card expands, task row scrolls into view and flashes |
| TX-213 | `?expand=` + `?clientqa=1` | Load | Client Q&A drawer opens once, flag stripped |
| TX-214 | `?expand=` + `?clientaccess=1` | Load | Client access modal opens once, flag stripped |
| TX-215 | Params combine | `?tab=overdue&sort=price&search=oak` | All three take effect together `[SPEC §4.1 "All query params are independently combinable"]` |
| TX-216 | Back/forward | Change tab, sort, search then press Back | Previous state restored `[SPEC §4.1 §6]` |
| TX-217 | Loading state | Throttle and reload | Card skeletons per spec (spec asks for skeletons, not a bare spinner) `[SPEC §4.1]` |
| TX-218 | Empty state | Filter to nothing | Message + a "+ New Transaction" action `[SPEC §4.1]` |
| TX-219 | Filtered empty state | Tab with 0 results | "No transactions match '<filter>'" + Clear filter `[SPEC §4.1]` |
| TX-220 | Error state | Force the cards call to fail | "Unable to load transactions" banner + Retry `[SPEC §4.1]` |
| TX-221 | Pagination / large sets | >20 deals | "Load more" or equivalent; tab counts still reflect the total `[SPEC §4.1 edge cases]` |
| TX-222 | Live refresh | Change data in another session | List refreshes (polling/realtime) `[SPEC §4.1 §8]` |

---

## 12. Detail page — header and shell

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-230 | Route renders | Open a deal | Workspace for that deal |
| TX-231 | Breadcrumb | Inspect | `Deals › Transactions › <street>`; the Transactions crumb links back |
| TX-232 | Identity row | Inspect | Serif deal name + stage pill + address |
| TX-233 | **Facts line** | Inspect | ONE line: address · Closes <date> (<N> days) · price · N overdue · N% complete `[PLAN §16.6]` |
| TX-234 | Status control | Open the dropdown | All lifecycle statuses; changing asks for confirmation |
| TX-235 | Status change → Closed | Set Closed | Confirm dialog explains the move; post-closing feedback modal opens |
| TX-236 | Saving indicator | Trigger a mutation | "Saving…" pill appears while in flight |
| TX-237 | Task progress | Inspect | Progress shown as a fact; omitted (not "0%") when the deal has no tasks `[PLAN §16.6]` |
| TX-238 | **"⋯" overflow menu** | Inspect the header | Print closing checklist (all internal roles) + Delete transaction (TeamLead/Admin) `[PLAN §16.2, SPEC §4.6]` |
| TX-239 | **"Ask AI" button** | Inspect the header | Opens the docked assistant `[PLAN §16.3]` |
| TX-240 | **AI pane default state** | First visit on a wide screen | Assistant is **closed by default**, 400 px when opened, remembered per user `[PLAN §16.3]` |
| TX-241 | Automation posture control | Inspect | One chip with the three choices and "N handled · M need you" |
| TX-242 | Coverage banners | Deal with an unanswered gating decision | Amber banner with option buttons; answering saves and updates tasks |
| TX-243 | Creation receipt | Open with `?created=1` | Receipt strip + one-time celebration; dismiss clears the param |
| TX-244 | Header height / composition | Inspect at 1600 px and 1024 px | Three rows (breadcrumb, identity+actions, facts); action controls share one shape and height `[PLAN §16.6]` |

---

## 13. Detail page — tab bar

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-250 | **Tab set** | Inspect | Overview · Timeline · Tasks · Documents · People · Billing · Activity (+ Email, + Agent on narrow) `[SPEC §4.6, PLAN §16.3]` |
| TX-251 | **Landing tab** | Open a deal fresh | Lands on **Overview** `[PLAN §16.3]` |
| TX-252 | **Compliance placement** | Look for Compliance | Compliance is the **Checklist view of Documents**, not its own tab `[SPEC §4.6, PLAN §16.3]` |
| TX-253 | `?tab=compliance` legacy link | Load it | Resolves to Documents › Checklist `[SPEC §4.6]` |
| TX-254 | `?tab=<key>` deep links | Load each tab key | Correct tab selected |
| TX-255 | Tab click updates the URL | Click each tab | `?tab=` updates; Back returns to the previous tab |
| TX-256 | Lazy loading | Watch network per tab | Each tab loads its own data on first open |
| TX-257 | Tab bar overflow | 1024 px / 375 px | Tabs scroll; no clipped labels |

---

## 14. Detail page — Overview tab

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-260 | **Needs you panel** | Inspect | Overdue + due-today tasks; click opens the task on Tasks; missing-documents line when any `[SPEC §4.6]` |
| TX-261 | **Key dates panel** | Inspect | Seven tracking dates as status-coloured chips; click goes to Timeline `[SPEC §4.6]` |
| TX-262 | **Progress panel** | Inspect | Tasks complete/total with a bar, open/overdue counts, purchase price `[SPEC §4.6]` |
| TX-263 | **People panel** | Inspect | Parties on the deal + "Manage" `[SPEC §4.6]` |
| TX-264 | Honest panels | Deal with sparse data | A panel renders only when it has real data `[SPEC §4.6]` |
| TX-265 | **AI next-step strip** | Inspect the body | Champagne strip; CTA opens the task email flow for the backing task `[SPEC §4.6]` |

---

## 15. Detail page — Timeline tab

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-270 | Timeline renders | Open the tab | Core dates, term-derived deadlines, deadline tasks |
| TX-271 | **Tracking-dates rail** | Inspect | Seven operational chips (EM Delivered … Possession) coloured by status `[PLAN §16.2, SPEC §4.6]` |
| TX-272 | Pure tracking fields save directly | Edit one of the five | Date popover saves directly; list agrees immediately `[SPEC §4.6]` |
| TX-273 | Closing/Possession use the cascade | Edit either | Cascade preview instead of a raw write `[SPEC §4.6]` |
| TX-274 | Cascade preview → Apply | Change a core date | Preview lists affected deadlines; Apply commits; Undo available |
| TX-275 | Term edit | Change "7 days" → "10 days" | Same cascade path with a `term_fields` change |
| TX-276 | Deadline task edit | Edit a deadline row | Rule editor; server resolves the date |
| TX-277 | Add deadline | Click Add deadline | Modal creates a `kind='deadline'` task |
| TX-278 | Remove a deadline | Remove a row | Marked Skipped with an Undo chip |
| TX-279 | Cash-appraisal decision row | Cash deal | One-click flip with confirm; tasks adjust |
| TX-280 | AI evidence chips | Rows with AI provenance | Chip + citation |
| TX-281 | Sync deadlines | Click | Calendar sync path available |

---

## 16. Detail page — Documents (+ Checklist) tab

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-290 | Document list | Open the tab | Name, type, date, size, version, download |
| TX-291 | `?view=files\|checklist` | Load each | Files / Checklist view selected `[SPEC §4.6]` |
| TX-292 | Upload dialog | Click Upload | File + name + type classified upload |
| TX-293 | Drag-drop anywhere | Drop a file on the page | Routes to Documents and uploads; overlay shows "Drop to upload to this deal" |
| TX-294 | AI verification chip | After upload | checking → confirmed / mismatch with one-click corrections |
| TX-295 | Documents manager | Click "Open documents manager" | Full modal: rename/classify, versions, email, delete, parse-confirm, missing docs |
| TX-296 | Checklist groups | Checklist view | Open / Uploaded / Waived with due chips |
| TX-297 | Attach document | Row action | Pick an existing file OR upload in place |
| TX-298 | Request by email | Row action | Drafts into AI Email Review |
| TX-299 | Waive + Undo | Row action | Waives with an Undo affordance |
| TX-300 | Inline edit of a requirement | Row action | Rule re-resolves server-side |
| TX-301 | Checklist empty state | Deal with none | One-click "Generate the standard checklist" or "Add a document" |

---

## 17. Detail page — Tasks tab

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-310 | Grouped sections | Open the tab | Overdue / Due Today / Upcoming / Completed |
| TX-311 | Status selector | Open a row's menu | Pending · In progress · Completed · Skipped (Blocked shown but not selectable) |
| TX-312 | Status change persists | Change one | Persists after refresh; header progress updates |
| TX-313 | Basis chip | Inspect | e.g. "3 days before Closing Date" |
| TX-314 | Related compliance link | Inspect | Opens the requirement on the checklist |
| TX-315 | Auto-Email toggle | Eligible task | Toggle present only when the target resolves to a captured party email |
| TX-316 | Task email flow | Row action | Opens with the party pre-resolved |
| TX-317 | Due-date rule editor | Edit a due date | Server resolves the date |
| TX-318 | Add Task | Click Add | Modal creates the task on this deal |
| TX-319 | `?task=<id>` flash | Load the deep link | Row scrolls into view and flashes |
| TX-320 | AI evidence chip | Rows with evidence | Chip + citation |

---

## 18. Detail page — People tab

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-330 | Deal fees at the top | Open the tab | Professional + transaction fee rows, editable in place `[SPEC §4.6]` |
| TX-331 | Fee edit dialog | Click the pencil | Buyer/Seller/Both, amount + %/$ per paying side, "Remove fee" |
| TX-332 | Fees empty state | Deal with none | Editing role sees "+ Add fees"; a viewer without rights sees nothing |
| TX-333 | Fee edit audited | After saving | Entry appears in Activity |
| TX-334 | Party groups | Inspect | Buyer · Seller · Agents · Lender · Title · Other contacts |
| TX-335 | Unknown role fallback | Party with an unmapped role | Renders under "Other contacts", never disappears `[SRC]` |
| TX-336 | Add / edit a party | Use the controls | AddContactModal with section prefill |
| TX-337 | Assign team | Click | Modal from page context |
| TX-338 | Manage client access | Click | Modal from page context |
| TX-339 | Client Q&A + badge | Click / inspect | Drawer opens; amber dot when the client is waiting `[SPEC §4.6]` |
| TX-340 | `?qa=1` / `?access=1` | Load each | Opens the drawer / modal once, then strips the flag `[SPEC §4.6, PLAN §16.2]` |
| TX-341 | Compose email | Click | ComposeEmailModal |
| TX-342 | RESPA guardrail note | Title group | Neutral compliance note rendered `[SRC]` |

---

## 19. Detail page — Billing, Activity, Email, Agent

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-350 | **Billing tab** | Open | This deal's invoices: status pill, payer, due-or-paid date, amount `[SPEC §4.6, PLAN §16.2]` |
| TX-351 | Billing row opens the invoice | Click a row | `/payments/invoices/:id` |
| TX-352 | Create invoice capability gate | Inspect | Button only with `can_create_invoice`; the list readable by every internal role |
| TX-353 | Billing empty state | Deal with none | Names the action + "View all in Payments" |
| TX-354 | Activity — history feed | Open | Audit + task events with search |
| TX-355 | Activity — automation lens | Toggle the chip | Only actions that ran without a click, with Undo where supported |
| TX-356 | Activity — communications | Inspect | Communications panel mounts from page context |
| TX-357 | Activity — cascade entries | After a cascade apply | "Closing moved … N deadlines recomputed" appears |
| TX-358 | Email tab | Open | Pending AI drafts for this deal + sent/discarded logs + inbound thread |
| TX-359 | Email row → full review | Click a row | Opens `/ai-emails/:id` |
| TX-360 | Agent pane | Open | Conversation pane; row "Ask AI" reveals it |
| TX-361 | Agent reference navigation | Click a reference | Switches to the owning tab and flashes the row |
| TX-362 | Narrow-screen Agent tab | <1280 px | Agent tab is the entry; pane is not split |

---

## 20. Detail page — states, permissions, edge cases

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-370 | Loading skeleton | Reload | Header + body skeletons |
| TX-371 | Error shell | Force the plan call to fail | "Couldn't load this transaction" + Retry + Back link |
| TX-372 | Closed deal is read-only | Open a Closed deal | Editing disabled across tabs `[SPEC §4.6]` |
| TX-373 | Paused deal | Open one | Editing enabled, auto-generation paused `[SPEC §4.6]` |
| TX-374 | Deleted while viewing | Delete from another session | Redirect to the list with a toast `[SPEC §4.6]` |
| TX-375 | Admin write scope | Attempt edits as Admin | Behaviour matches the documented Admin capability |
| TX-376 | Post-closing feedback | Close a deal | Modal with useful/unnecessary/missing-tasks |
| TX-377 | Deep-link `?requirement=<id>` | Load | Requirement row flashes |
| TX-378 | Detail ↔ list agreement | Compare the same deal on both | Days-to-close, overdue count, price and stage agree `[PLAN §16.2]` |
| TX-379 | Responsive 1024 px | Inspect | No horizontal scroll, no clipped controls |
| TX-380 | Responsive 375 px | Inspect | Single-column, tabs scroll, no overflow |
| TX-381 | Page owns its scroll | Scroll the body | Shell header stays; page scrolls internally `[SRC]` |

---

## 21. Cross-surface consistency

| ID | Feature | Steps | Expected |
| --- | --- | --- | --- |
| TX-390 | Card vs workspace numbers | Same deal, both surfaces | Same stage, price, days-to-close, overdue count |
| TX-391 | Task completion propagates | Complete on one surface | Reflected on the other after refetch |
| TX-392 | Date edit propagates | Edit on the card | Workspace timeline agrees |
| TX-393 | Nav badge agreement | Sidebar "Active Transactions" badge vs the page count | Same number |
| TX-394 | Style conformance | Inspect both surfaces | Flat modern aesthetic, lucide icons, no emoji nav icons `[STYLE]` |
| TX-395 | Emoji in UI controls | Inspect the card footer and badges | Emoji used as button glyphs is inconsistent with the icon system `[STYLE]` |

---

## 22. Summary table (filled in during execution)

| Section | Items | Pass | Fail | Partial | Blocked | N/A |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Environment & routing | 11 | | | | | |
| 2. Header & toolbar | 15 | | | | | |
| 3. Filter tabs | 11 | | | | | |
| 4. Sort | 7 | | | | | |
| 5. Collapsed card | 21 | | | | | |
| 6. Drawer — Tasks | 15 | | | | | |
| 7. Drawer — Key Dates | 12 | | | | | |
| 8. Drawer — Contacts | 10 | | | | | |
| 9. Footer / invoices / AI | 18 | | | | | |
| 10. Modals & panels | 16 | | | | | |
| 11. URL state & states | 13 | | | | | |
| 12. Detail header | 15 | | | | | |
| 13. Detail tab bar | 8 | | | | | |
| 14. Overview tab | 6 | | | | | |
| 15. Timeline tab | 12 | | | | | |
| 16. Documents/Checklist | 12 | | | | | |
| 17. Tasks tab | 11 | | | | | |
| 18. People tab | 13 | | | | | |
| 19. Billing/Activity/Email/Agent | 13 | | | | | |
| 20. Detail states & edges | 12 | | | | | |
| 21. Cross-surface | 6 | | | | | |
| **Total** | **257** | | | | | |
