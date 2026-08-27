# Vendor Portal — attention/counts workflow redesign & implementation plan (2026-08-26)

**Status:** Implemented 2026-08-26. Backend buckets + request lifecycle, frontend KPIs/surfaces, duplicate-request cleanup, Chrome QA 59/59.
**Trigger:** Live report on the Loan Files page — "Needs Attention says 19 but the items are nowhere to be found; Open docs says 11 but clicking it lands on a Documents tab full of identical 'Pre-approval letter / Awaiting team' cards."
**Sources:** Live API probe as `tessa.grant@minafter.com` (2026-08-26 21:07 UTC), `velvet-elves-backend/app/api/v1/vendor_workspace.py`, `app/api/v1/transaction_vendor_assignments.py`, `app/schemas/vendor_workspace.py`, `velvet-elves-frontend/src/layouts/VendorWorkspaceLayout.tsx`, `src/pages/vendor/VendorFilesPage.tsx`, `src/pages/vendor/VendorPortalDocumentsPage.tsx`, `src/components/vendor-portal/VendorLoanCard.tsx`, plus `VENDOR_WORKSPACE_SUPERIOR_PLAN.md`, `VENDOR_PORTAL_LOGIC_WORKFLOW_REVIEW_2026-08-26.md`, `VENDOR_PORTAL_FINALIZE_IMPLEMENTATION_PLAN_2026-08-26.md`.

---

## 0 · Verdict: why the system produces these results

Every symptom the user reported is real, reproducible, and traceable to four design defects. None of them is a data glitch.

1. **"Needs attention" has no single definition.** The overview API, the Files-home list, and the Documents tab each compute "attention" with a different formula, so the same portal shows **19**, **4**, and **12** for the "same" concept at the same moment.
2. **The headline counts are computed from different data than the lists they sit on.** The API reports `stats.needs_attention = 19` but returns only the first **4** items (`attention[:4]`). The other 15 items are counted but never rendered anywhere as a list of 19 — they are literally "nowhere to be found."
3. **"Needs attention" mixes two opposite things:** work **the vendor must do** (6 overdue tasks) and work **the vendor is waiting on the team for** (12 document requests + 1 close-out in review). Thirteen of Tessa's 19 "attention" items are items she *cannot act on at all*. A number that mixes "your move" with "their move" can never look right.
4. **"Request a document" is a create-only lifecycle.** Every submit inserts a new `communication_logs` row with `status="awaiting"`. There is **no dedupe, no vendor cancel, no staff decline, and resolution is optional** (a `request_id` query param staff may or may not pass when sharing). Our own QA reruns of the request flow created **12 identical "Pre-approval letter" requests**, and the system has no mechanism to ever remove them. That is the wall of identical, ambiguous cards.

And one labeling defect: **"Open docs = 11" counts every document visible on the deal — including the vendor's own uploads.** Tessa has 11 documents total: **11 are her own QA uploads, 0 were shared with her.** The KPI labels them "Open docs," the loan card labels the same number "11 shared docs," and clicking the KPI lands on the Documents page's *default tab* — "Needs attention" — which shows none of those 11 documents, only the 12 awaiting request cards.

The features themselves (files, tasks, close-out review, documents, requests, notes, date proposals, notifications) match Jake's plan and survive the audit in §3. What is broken is the **information architecture on top of them**: counts, buckets, labels, links, and one missing lifecycle. That layer is what this document redesigns.

---

## 1 · Live evidence (probe, 2026-08-26 21:07 UTC)

Read-only API probe as Tessa (mortgage vendor, one file — 4567 Meadowridge Avenue):

| API fact | Value |
| --- | --- |
| `stats` | `{"files": 1, "open_documents": 11, "needs_attention": 19}` |
| `needs_attention` array actually returned | **4 items** (all overdue tasks; stat says 19) |
| Composition of the 19 | 6 overdue tasks + 12 awaiting doc requests + 1 pending close-out |
| Document requests | 12, **all** `status="awaiting"`, **all** label `"Pre-approval letter"` |
| Documents | 11 total — **11 own uploads, 0 shared**, all `status="pending"` |
| Tasks by group | overdue 6 · upcoming 1 · done 1; close-outs pending review: 1 |
| File summary | `open_tasks 7, overdue_tasks 6, open_documents 11, needs_attention true` |

What each surface renders from this:

| Surface | Shows | Why |
| --- | --- | --- |
| Sidebar KPI "Attention" | **19** → links to Files home | `stats.needs_attention` |
| Files home banner "Needs attention" | **19** | same stat |
| Files home "Urgent loan items" badge | "**19 active**" over a list of **4 rows** | badge uses the stat, list uses the sliced array |
| Sidebar KPI "Open docs" | **11** → links to `/portal/vendor/documents` | `open_documents`; Documents defaults to the **Needs attention** tab |
| Documents "Needs attention" tab badge | **12** | 0 attention docs + 12 awaiting requests |
| Documents "Needs attention" tab body | 12 identical rows "Pre-approval letter · Awaiting team" | `AwaitingList` renders label + badge only |
| Loan card pill | "**11 shared docs**" | same `open_documents`; 0 are actually shared |

Three different "attention" numbers (19 / 4 / 12), an 11 that means "your own uploads," and 12 identical cards. Every user-visible symptom is reproduced.

---

## 2 · Root causes in code

### RC1 — Stat counts the full list; the response slices it to 4

```638:643:c:\Projects\velvet-elves-backend\app\api\v1\vendor_workspace.py
        stats=VendorStat(
            files=len(files),
            open_documents=open_docs_total,
            needs_attention=len(attention),
        ),
        needs_attention=attention[:4],
```

The Files page then prints the stat on the badge and maps the sliced array below it (`VendorFilesPage.tsx` lines 89–94). With 19 items, 15 are counted but unrenderable — on any page.

### RC2 — "Attention" mixes vendor-actionable and team-blocked items

`get_overview` appends three kinds into one `attention` list: overdue tasks (lines 576–589), **every awaiting document request** (lines 598–612), and **every pending close-out** (lines 619–631). The requests and close-outs are *waiting on staff*; the vendor has no action. This mixing was introduced deliberately by the finalize plan (Phase C item L5: "Mix of overdue tasks, awaiting requests, pending close-outs") — the plan itself was wrong on this point and this redesign supersedes it.

### RC3 — `open_documents` counts every visible document, including the vendor's own uploads

```530:530:c:\Projects\velvet-elves-backend\app\api\v1\vendor_workspace.py
        open_documents=len(shared_docs),
```

`shared_docs` is `_visible_deal_documents(...)` — the union of family-visible deal documents and explicitly-shared ones. The vendor's own uploads are family-visible, so they count. Nothing about the number is "open" (no status filter) and nothing is necessarily "shared" (Tessa: 0 of 11). Two different UI labels ("Open docs", "N shared docs") both misdescribe it.

### RC4 — KPI link targets don't show what the KPI counts

```176:184:c:\Projects\velvet-elves-frontend\src\layouts\VendorWorkspaceLayout.tsx
  const kpiTiles: KpiTile[] = [
    { label: 'Files', value: overview?.stats.files ?? 0, color: 'blue', to: ROUTES.VENDOR_PORTAL },
    { label: 'Open docs', value: openDocs, color: 'orange', to: ROUTES.VENDOR_DOCUMENTS },
    {
      label: 'Attention',
      value: overview?.stats.needs_attention ?? 0,
      color: 'red',
      to: ROUTES.VENDOR_PORTAL,
    },
```

"Open docs" lands on Documents, whose default tab is `attention` (`VendorPortalDocumentsPage.tsx` line 58) — a tab whose count comes from a *different* formula (attention docs + awaiting requests). "Attention 19" lands on a page that can render at most 4.

### RC5 — Request lifecycle is create-only in practice

- **Create** (`vendor_workspace.py` `request_document`, line 1225+): inserts a new awaiting row every time; no dedupe against existing awaiting requests with the same label on the same deal.
- **Resolve** (`transaction_vendor_assignments.py` lines 288–345): sharing a document flips a request to `shared` **only if** staff passed `?request_id=...`. Sharing without it leaves the request awaiting forever.
- **Decline / cancel:** the schema documents `awaiting | shared | declined | in_progress` (`schemas/vendor_workspace.py` line 241), but **no endpoint can produce `declined`**, and the vendor has no cancel. `in_progress` is equally unreachable.
- Result: requests only accumulate. 12 QA reruns → 12 permanent cards, each also inflating the overview "attention" count (RC2).

### RC6 — The awaiting card carries no distinguishing information

`AwaitingList` (`VendorPortalDocumentsPage.tsx` lines 336–345) renders **label + "Awaiting team" badge** — no file address, no requested date, no reason, no action. Twelve requests with the same label are pixel-identical, and even two *legitimate* requests on different files would be indistinguishable.

---

## 3 · Are the current features necessary? (audit)

Verdict per feature, against Jake's intent (`VENDOR_WORKSPACE_SUPERIOR_PLAN.md`) and the 26 Aug logic review:

| Feature | Verdict | Rationale |
| --- | --- | --- |
| Files home + expandable loan/title card (tasks, dates, contacts, docs, activity) | **Keep** | Core of "vendor sees only their files." Proven in Chrome QA. |
| Tasks close-out loop (mark done → staff review → approve/send back, Undo) | **Keep** | Jake's central loop; staff side (`VendorTaskReviewQueue`) exists. |
| Documents: upload-to-file, shared docs, in-app preview | **Keep** | The daily job. |
| Request a document | **Keep, complete the lifecycle** | Legitimate need (vendors chase paperwork), but as built it is create-only (RC5) and must gain dedupe/cancel/decline/resolve. |
| Date updates as proposals | **Keep** | Implemented per finalize Phase A; correct pattern (staff Accept/Reject). |
| File notes | **Keep** | Low-friction ping; staff notification path exists. |
| Vendor bell + notification prefs | **Keep** | Implemented per finalize Phase D; the "something happened" surface. |
| Sidebar KPI **"Open docs"** | **Remove as built** | Counts all visible docs incl. own uploads (RC3); label is false; click target incoherent (RC4). Replace per §4.3. |
| Overview **"needs attention" stat + 4-item slice** | **Replace** | RC1 + RC2. Split into two honest buckets, return full lists. |
| "N shared docs" pill on loan card | **Fix label + formula** | Says "shared," counts everything. |
| Awaiting requests **inside** the attention count | **Remove** | They are the team's queue, not the vendor's. Show them as status ("Waiting on the team"), never count them as vendor attention. |
| `in_progress` request status | **Drop from design** | Unreachable; no staff UI sets it. Keep the string tolerated on read. |

Bottom line: **no feature needs to be deleted from the product; the measurement/labeling layer on top of them must be rebuilt.** The portal's credibility problem comes from numbers that argue with each other, not from wrong features.

---

## 4 · The redesign

### 4.1 Vocabulary — two buckets, never mixed

Every item on the vendor home is exactly one of:

| Bucket | Definition (exact) | Vendor can act? |
| --- | --- | --- |
| **Needs your action** (`needs_action`) | Overdue vendor-visible open tasks · close-outs **sent back** by staff · documents **shared to you** not yet resolved (`needsAttention()` predicate: `source == 'shared'` and status not in RESOLVED) | **Yes — every item has a next click** |
| **Waiting on the team** (`waiting_on_team`) | Your awaiting document requests (deduped) · your close-outs pending staff review · your date proposals pending review | No — informational status |

Rules:

- An item appears in **exactly one** bucket (sent-back close-out = needs action; pending close-out = waiting).
- "Waiting" items are **never** styled red and **never** counted in any "attention" number.
- Nothing else (own uploads, resolved docs, upcoming tasks) is in either bucket.

### 4.2 Counting invariants (the contract every surface must obey)

1. **I1 — A number is a list.** Every count shown in the UI equals `length` of a list the user reaches in one click, and the destination visibly renders exactly that many rows (or the rows plus an explicit filter that reproduces the number).
2. **I2 — One formula per concept.** `needs_action` and `waiting_on_team` are computed **once, in the backend**, and every surface (sidebar, banner, section badge, tab badge) reads the same field. The frontend never re-derives a headline count from a different source than the list it renders.
3. **I3 — No hidden truncation.** The API returns full lists. If a page wants to preview N items, it shows "View all {total}" linking to the full list. `attention[:4]` is abolished.
4. **I4 — Labels tell the truth.** No pill or KPI may say "shared"/"open" about a quantity that includes non-shared/non-open items.

### 4.3 Surface-by-surface specification

**Sidebar KPIs (`VendorWorkspaceLayout`)** — three tiles, same order:

| Tile | Value | Click target | Target shows |
| --- | --- | --- | --- |
| Files | `stats.files` | `/portal/vendor` | The file cards (count matches) |
| Needs action (red) | `stats.needs_action` | `/portal/vendor` (home, "Needs your action" section) | That section, full list |
| Waiting (amber/neutral) | `stats.waiting_on_team` | `/portal/vendor` home "Waiting" section | That section, full list |

"Open docs" tile is deleted. (If a docs tile is wanted later, it must be "Docs to review" = shared-unresolved only, linking to `Documents?view=attention` — which is already a `needs_action` subset, so v1 omits it.)

**Files home (`VendorFilesPage`)**

- Banner stats: `Shared files` · `Needs your action` (red accent) · `Waiting on the team`. Same three fields as the sidebar (I2).
- Section **"Needs your action"**: renders the **full** `needs_action` list. Badge = `needs_action.length`. Each row deep-links to the item itself: tasks → `/portal/vendor/tasks?task={id}` (page expands + scrolls to that row), docs → `/portal/vendor/documents?view=attention`. Empty state: hide the section.
- New slim section **"Waiting on the team"** (collapsed by default, neutral styling): grouped one-liners — "Pre-approval letter — requested {date} · Cancel", "Close-out of {task} — in review". Badge = `waiting_on_team.length`. This is where the 12-requests class of item becomes *findable* without pretending to be urgent.

**Documents page (`VendorPortalDocumentsPage`)**

- "Needs attention" tab badge = **attention docs only** (shared, unresolved). Awaiting requests no longer count into the red badge (they are not the vendor's attention).
- The "Awaiting the team" block stays on that tab (it is a docs-related waiting room) but under a neutral heading with richer cards (§4.4) and its **own** count displayed on the block header, not in the tab badge.
- `?view=requests|awaiting` keeps scrolling to the block (already implemented).

**Loan card (`VendorLoanCard`)**

- Pill `"{open_documents} shared docs"` → two honest pills: `"{docs_shared} shared"` (only if > 0) and `"{docs_uploaded} yours"`. Backend supplies both (§4.5).
- `needs_attention` flag on the summary stays overdue-driven (it already is).

**Tasks page** — accept `?task={id}`: expand that task's row and scroll to it. This makes attention deep-links honest (today every task row on home links to the generic Tasks page).

**Staff requests panel (`VendorRequestsPanel`)** — add **Decline (with reason)** next to Share, and show the request's age. Share keeps auto-resolving via `request_id`; §4.4 adds auto-matching.

### 4.4 Request lifecycle — complete the state machine

```
            vendor submits (deduped)
                    │
                    ▼
               ┌─────────┐   staff shares doc (request_id or doc-type auto-match)
               │ awaiting │ ─────────────────────────────► shared
               └─────────┘   staff declines (reason)  ───► declined
                    │
                    └─ vendor cancels ───────────────────► cancelled
```

- **Dedupe on create:** normalize the label (`trim`, collapse whitespace, casefold). If this vendor already has an **awaiting** request with the same normalized label on the same transaction, return the existing row (HTTP 200, idempotent) instead of inserting. Toast copy: "You already have this request open — we've bumped it to the team." (Also fixes QA reruns: the 12-duplicate scenario becomes impossible.)
- **Vendor cancel:** `DELETE /api/v1/vendor-portal/documents/request/{request_id}` → sets `metadata_json.status="cancelled"`. Guard: only the requester, only while `awaiting`. Cancelled requests disappear from the vendor's awaiting list and the staff panel.
- **Staff decline:** `POST /api/v1/transactions/{tx}/vendor-document-requests/{request_id}/decline` body `{ "reason": str }` (staff roles, transaction access). Sets `status="declined"`, `declined_reason`. Emits vendor notification `document_request_declined` ("The team can't provide {label}: {reason}"). Vendor UI shows a dismissible "Declined" chip with the reason in the awaiting block for 7 days, never counted anywhere.
- **Share auto-match:** when staff share a document to an assignment **without** `request_id`, auto-resolve any awaiting requests on that deal+assignment whose `doc_type` equals the shared document's `doc_type` (exact match only — label fuzzy-matching stays manual). Existing `document_request_resolved` notification fires.
- **Vendor awaiting card** gains: file address (when the vendor has >1 file), "Requested {relative date}", the reason if provided, and a **Cancel** button.
- `in_progress` is dropped from the design; readers tolerate the string as "awaiting".

### 4.5 API contract (before → after)

`VendorStat` (breaking change — FE and BE ship together, as this repo pair always does):

```
before: { files, open_documents, needs_attention }
after:  { files, needs_action, waiting_on_team }
```

`VendorOverviewResponse`:

```
before: needs_attention: VendorAttentionItem[]   # sliced to 4
after:  needs_action:    VendorAttentionItem[]   # FULL list, only vendor-actionable
        waiting_on_team: VendorWaitingItem[]     # FULL list
```

`VendorWaitingItem` (new): `{ id, transaction_id, kind: 'doc_request' | 'closeout' | 'date_proposal', title, address, since: datetime, cancellable: bool, href }`.

`VendorAttentionItem.href` becomes a real deep link (`/portal/vendor/tasks?task={id}`, `/portal/vendor/documents?view=attention`).

`VendorFileSummary`: `open_documents` → `docs_shared` + `docs_uploaded` (computed from the same `_visible_deal_documents` union, split by `uploaded_by == vendor`).

`VendorDocumentRequest`: add `declined_reason: str | null`, `cancellable: bool`.

No change to task, note, date-proposal, notification, or preview endpoints.

---

## 5 · Implementation plan

Three phases; each leaves the system consistent. Total estimate ≈ 1.5–2 dev-days including tests and the Chrome pass.

### Phase 1 — Backend: honest buckets + request lifecycle (~0.5–1 day)

`app/api/v1/vendor_workspace.py`

1. In `get_overview`: build `needs_action` (overdue tasks + sent-back close-outs + shared-unresolved docs) and `waiting_on_team` (awaiting requests + pending close-outs + pending date proposals) as separate lists. Delete the `[:4]` slice. Populate `VendorStat(files, needs_action=len(...), waiting_on_team=len(...))`.
2. Task attention hrefs → `/portal/vendor/tasks?task={task_id}`.
3. `_build_file_summary`: replace `open_documents` with `docs_shared` / `docs_uploaded`.
4. `request_document`: dedupe-on-create (normalized label + transaction + requester, status awaiting → return existing).
5. New `cancel_document_request` endpoint (vendor, own+awaiting only).

`app/api/v1/transaction_vendor_assignments.py`

6. New `decline_vendor_document_request` endpoint (staff) + `document_request_declined` vendor notification via `vendor_notify`.
7. `share_document_with_vendor`: after the explicit `request_id` handling, auto-resolve awaiting requests with matching `doc_type` on the deal+assignment.

`app/schemas/vendor_workspace.py` — `VendorStat`, `VendorWaitingItem`, request fields per §4.5.

**Tests (`app/tests/test_vendor_portal_api.py` + assignments tests):** stats equal list lengths; buckets don't overlap; awaiting requests appear only in `waiting_on_team`; duplicate create returns the existing id (count stays 1); cancel → gone from vendor list and staff panel; decline → status + reason + notification; share with `request_id` and share with matching `doc_type` both resolve; declined/cancelled never re-enter any count.

### Phase 2 — Frontend: surfaces obey the invariants (~0.5 day)

1. `useVendorPortal.ts` — types per §4.5; add cancel-request mutation.
2. `VendorWorkspaceLayout.tsx` — KPI tiles: Files / Needs action / Waiting (delete "Open docs"); values from the new stats; targets per §4.3.
3. `VendorFilesPage.tsx` — banner stats renamed; "Needs your action" renders the full list with badge = `list.length`; new collapsed "Waiting on the team" section with cancel buttons on doc requests.
4. `VendorPortalDocumentsPage.tsx` — attention tab badge = attention docs only; awaiting block shows richer cards (address when multi-file, requested date, reason, Cancel, Declined chip w/ reason).
5. `VendorPortalTasksPage.tsx` — support `?task={id}` (expand + scroll).
6. `VendorLoanCard.tsx` — pills `"{docs_shared} shared"` / `"{docs_uploaded} yours"`.
7. `VendorRequestsPanel.tsx` (staff) — Decline-with-reason action + request age.

**Tests (Vitest):** update `VendorPortalPages.test.tsx` / `VendorWorkspaceLayout.test.tsx` fixtures to the new stats; new: badge equals rendered row count on home; waiting section lists a request with Cancel; documents attention badge excludes awaiting; tasks page honors `?task=`.

### Phase 3 — Data cleanup + browser verification (~0.5 day)

1. **One-off cleanup script** (backend `scripts/` or maintenance snippet): for each `(tenant, transaction, sender, normalized label)` group of awaiting doc-request logs, keep the newest, set older ones `metadata_json.status = "superseded"`. Tessa's 12 → 1. Log what changed.
2. **Chrome QA (`vendor_portal_chrome_qa.mjs`) additions:**
   - *Count-consistency checks:* read each sidebar KPI number → click → count visible rows → assert equal (I1, the exact regression the user hit).
   - *Request idempotency:* submit the same request twice → assert one card; **cancel** it at the end of the run so QA stops polluting data.
   - Documents attention badge equals attention-doc rows; awaiting block count separate.
3. Full pass as Tessa; document results in `vendor_portal_qa/`.

**Deploy order:** backend first (old FE reads `stats.needs_attention` → temporarily undefined-safe `?? 0`), then frontend immediately after — or ship together as usual for this pair.

---

## 6 · Acceptance criteria

1. Every number in the sidebar, banner, and section badges equals the number of rows revealed by clicking it (verified by the new Chrome checks).
2. With Tessa's current data (post-cleanup): Needs action = **6** (the overdue tasks), Waiting on the team = **2** (1 deduped pre-approval request + 1 close-out in review), Files = 1. No 19, no 11, anywhere.
3. Submitting "Pre-approval letter" twice yields **one** card, with file address, request date, and a working Cancel.
4. Staff declining a request shows the vendor a Declined chip with the reason and fires a bell notification; the item never counts as attention.
5. Staff sharing a matching-type document resolves the awaiting request without staff having to know about `request_id`.
6. No UI label says "shared" or "open" about a count that includes the vendor's own uploads.
7. All existing suites stay green: backend pytest, frontend Vitest + tsc + ESLint, Chrome QA script.

---

## 7 · Symptom → root cause → fix map

| Reported symptom | Root cause | Fix |
| --- | --- | --- |
| "19 need attention but items nowhere to be found" | RC1 (stat vs `[:4]` slice) + RC2 (mixed buckets) | §4.1 buckets, full lists (I3), home renders all of `needs_action` (§4.3) |
| "Sidebar and section agree on 19 yet list shows a few tasks" | RC1; badge reads stat, list reads slice | I2: one field feeds both; badge = rendered length |
| "Open docs 11 → lands on Needs-attention tab" | RC3 (vanity count) + RC4 (mis-wired target, default tab) | Delete the KPI; docs pills split shared/yours (§4.3) |
| "Identical ambiguous 'Pre-approval letter / Awaiting team' cards" | RC5 (create-only lifecycle, QA reruns) + RC6 (info-free card) | Dedupe, cancel, decline, auto-resolve (§4.4); richer card; data cleanup (§5 Phase 3) |
| "Features feel unnecessary / fundamentally incorrect" | Measurement layer contradicts itself, not the features | §3 audit: keep the features, rebuild counts/labels/links to the invariants in §4.2 |

---

## 8 · References

- `VENDOR_WORKSPACE_SUPERIOR_PLAN.md` — Jake's intent; §5.1 home cards, §6.4 sharing, §9.2 requests.
- `VENDOR_PORTAL_LOGIC_WORKFLOW_REVIEW_2026-08-26.md` — L4/L5 first flagged the count mismatch; this doc supersedes its L5 remedy (which mixed waiting items into attention).
- `VENDOR_PORTAL_FINALIZE_IMPLEMENTATION_PLAN_2026-08-26.md` — Phases A–G status; Phase C item L5 is superseded by §4 here.
- Code: `vendor_workspace.py` lines 530, 576–631, 638–643, 1225+; `transaction_vendor_assignments.py` lines 288–345, 383–427; `schemas/vendor_workspace.py` line 241; `VendorWorkspaceLayout.tsx` lines 176–184; `VendorFilesPage.tsx` lines 59–94; `VendorPortalDocumentsPage.tsx` lines 39–41, 58, 85–91, 196–203, 336–345; `VendorLoanCard.tsx` line 145.
- Live probe output, 2026-08-26 21:07 UTC (§1).
