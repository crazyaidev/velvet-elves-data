# All Documents — Chrome QA findings (2026-08-13)

**Page:** Workflow › All Documents (`/documents`, alias `/documents/all`)  
**Tester:** platform admin `shyna.elene@minafter.com`  
**Environment:** real Google Chrome (Playwright headed, `channel: "chrome"`), frontend `http://localhost:5173`, backend `http://localhost:8000`  
**Dataset:** 6 Active deals, **~330** uploaded documents. After DocuSign connect: live send/void exercised; Signed tab still empty until a signer completes an envelope.

Artifacts: `velvet-elves-data/all_documents_qa/artifacts_2026-08-13_first/` (before list-page fixes), `artifacts_2026-08-13_retest/` / `verify2/` (list-page verification), `artifacts_2026-08-13_esign-retest/` (DocuSign pass after D-14–D-16).

---

## 1. Executive summary

The page loaded and the AI-priority hero, tabs, upload, preview, email, archive, and Cleared Today strip all worked. It was **not** seamless. A **328-row dump** with no paging, no export, no list filter, and document cards wrapped in `role="button"` made daily work slow and made keyboard / automation hit the whole card instead of Preview / More / Sign.

Those functional gaps are **fixed and re-verified in Chrome**. A later headed pass confirmed export, 20-row paging, named breadcrumb, required transaction on upload, archive Undo, transaction links, Cmd+K, the page filter, mobile names, and the `?focus=` deep link.

After the tenant connected DocuSign, a second Chrome pass sent a real sandbox envelope, synced it, and voided it. Send itself worked; **void had no confirm**, the row **did not flip to Voided/Resend**, and the modal **flashed “not connected”**. Those three are fixed and retested.

| Severity | Found | Status |
| --- | --- | --- |
| High | 7 | Fixed (D-01–D-04, D-12, D-15, D-16) |
| Medium | 9 | Fixed (D-05–D-11, D-13, D-14) |
| Low / data | 4 | Documented (not page-render bugs) |

---

## 2. Issues found and resolved

### D-01 · No Export action
**Severity:** High · **Area:** Header

Spec §5.4 and the Contacts / My Task Queue pattern both have Export. The All Documents header only had Refresh, Restore, Send for Sig, and Upload.

**Fix:** **Export CSV** downloads the currently visible tab (respects filters / search). Chrome retest saved `documents.csv`.

### D-02 · 328 cards rendered with no pagination
**Severity:** High · **Area:** All docs tab

Spec §5.4: 30 per page; the task-queue rule is the same at high volume. All docs painted **323–328 Preview buttons** in one scroll. The page was sluggish; More / Sign / Email targeting became unreliable.

**Fix:** Each list shows **20** rows, then **Show N more · remaining**. Chrome: All docs renders 20 rows with Show more.

### D-03 · Document cards used `role="button"` around nested buttons
**Severity:** High · **Area:** All docs / Pending / Signed cards

The same trap as My Task Queue before Q-15. The card was a giant `role="button"` wrapping Preview, Download, Sign, and More. Playwright (and keyboard users) resolved “More actions” / “Send for Sig” to the **card**, not the control. 325 nested interactive cards on the first pass.

**Fix:** Card is a layout container. Preview is the explicit primary control. Nested `role="button"` count is **0**.

### D-04 · Upload did not require a transaction
**Severity:** High · **Area:** Upload modal

“Assign to Transaction” was optional. A file could land **Unassigned** (`transaction_id: null`). The library already has unassigned files (e.g. `test.pdf` from 2026-06-10). Spec: assign to a transaction, then classify.

**Fix:** Transaction is `required`. Submit without one shows **Choose a transaction before uploading.** Chrome: selected a deal, uploaded `qa-upload.txt`, toast **Document uploaded**.

### D-05 · Breadcrumb had no accessible name
**Severity:** Medium · **Area:** Header

My Task Queue uses `aria-label="Breadcrumb"`. This page’s `<nav>` did not, so `getByRole('navigation', { name: 'Breadcrumb' })` missed it. Type was also 11.5px (below the 12px floor).

**Fix:** `aria-label="Breadcrumb"` and 12.5px type.

### D-06 · Missing-tab checkboxes were 16×16
**Severity:** Medium · **Area:** Missing tab

Requirements §9.1 / style guide: 40–48px hit target. Bulk select used `h-4 w-4`.

**Fix:** 40×40 checkboxes. Chrome: **40×40**.

### D-07 · Header actions were 28px tall and unnamed on a phone
**Severity:** Medium · **Area:** Header / mobile

Upload measured **82×28**. Send for Sig / Upload labels are `hidden sm:inline` with no `aria-label`. Restore archived was `hidden md:inline-flex`.

**Fix:** `h-10` (40px) header actions; `aria-label` on Upload, Send for signature, Restore archived, Export CSV. Restore is visible at 390px.

### D-08 · Page chrome used 9–11px type
**Severity:** Medium · **Area:** Typography

Style guide v2: no text below 12px. Count pill, tab badges, status pills, sort control, and kickers were 10–11.5px.

**Fix:** Page chrome and cards use ≥12px. Ask AI’s `⌘L` kicker on this surface is 12px as well.

### D-09 · No list filter on a 328-document library
**Severity:** Medium · **Area:** Toolbar

Spec §5.4 wants on-page AI search. The completion plan deferred that to Cmd+K, which works — but a 328-row tab still had no way to narrow the list. Empty search had no dedicated empty state.

**Fix:** **Filter documents** input (`aria-label="Filter documents"`), synced to `?q=`. No matches shows **No documents match your search** with Clear search. Cmd+K remains for cross-entity search.

### D-10 · Transaction address was not a link
**Severity:** Medium · **Area:** Doc card

Spec: transaction name in a row navigates to `/transactions/:id?tab=documents`. The address was plain text (the first-pass “pass” was a false positive from other `/transactions` links on the shell).

**Fix:** Address is a `Link` to the deal’s Documents tab.

### D-11 · Archive had no Undo
**Severity:** Medium · **Area:** More › Archive

A mis-click archived with only a toast. Restore archived is a separate panel.

**Fix:** Success toast includes **Undo** (restore). Chrome: archive confirm → **Document archived** → **Undo**.

### D-12 · `?focus=` deep link lost the row after highlighting
**Severity:** High · **Area:** Cmd+K / URL

Cmd+K correctly sends `/documents?focus=:id`. The page switched to All docs, scrolled, then **stripped `focus` from the URL**. With pagination, that row was not in the first 20, so it vanished before the user could act.

**Fix:** Pin the highlighted document in the list after the query param is consumed; wait until documents have loaded before starting the find loop; 4s timeout.

### D-13 · Sort / tab / cleared-scope URL sync
**Severity:** Medium (verified working; kept)

`?tab=`, `?sort=`, `?cleared_scope=`, `?sheet=cleared-all`, and `/documents/all` already worked. Re-verified after the other changes so paging / search did not break them.

---

## 3. Chrome retest (after fixes)

| Check | Result |
| --- | --- |
| Login as platform admin | Pass |
| Sidebar **All Documents** → `/documents` | Pass |
| Breadcrumb, title, Upload, Send for Sig, Restore, Export CSV, Refresh | Pass |
| Export `documents.csv` | Pass |
| API ~328 docs / 23 AI-priority; count pill matches | Pass |
| Tabs: AI priority, All docs, Missing, Pending, Sent, Signed + URL sync | Pass |
| All docs pagination: **20** Preview rows + Show more | Pass |
| Missing bulk select 40×40; Mark N/A / Request / Upload / Assign bar | Pass |
| Sort → `?sort=close_date` | Pass |
| `/documents/all` alias | Pass |
| `?tab=signed&sort=doc_name` | Pass |
| `?sheet=cleared-all` opens 7-day sheet | Pass |
| `?focus=` keeps the document on All docs | Pass |
| Hero **Show alternatives**; queue primary CTA | Pass |
| Cleared Today legend + Me scope (`?cleared_scope=me`) | Pass |
| Upload requires a transaction; `qa-upload.txt` uploaded | Pass |
| Preview; More: Version History, Edit, Email, Archive | Pass |
| Email modal; archive confirm + Undo | Pass |
| Restore archived panel | Pass (row Restore flaked once when the list was still empty) |
| Send for signature modal | Pass |
| No nested `role="button"` cards | Pass |
| Transaction address → `/transactions/:id?tab=documents` | Pass |
| Cmd+K search | Pass |
| Filter documents; empty state; `?q=` | Pass |
| Page type ≥12px (scoped to the page, not the shared sidebar) | Pass |
| Upload hit target 40px | Pass |
| Keyboard Upload (Enter) | Pass |
| Mobile 390px: Upload, Send for signature, Restore named; no horizontal overflow | Pass |
| Console / page errors | Pass |

---

## 4. Remaining (not All Documents render defects)

These are real, but they are **data, shared-shell, or test-harness** issues:

1. **Signed tab is still empty.** Completing a live DocuSign envelope (signer finishes in DocuSign) was not part of this pass. After the e-sign retest, Sent for sig holds **voided** QA envelopes with Resend. The count pill can still read `0 of N complete`.
2. **Legacy unassigned files.** Older uploads with `transaction_id: null` still appear as **Unassigned**. New uploads from this page cannot repeat that.
3. **Shared shell type below 12px** (sidebar kickers, `⌘K`, briefing chips) is outside this page. Only the All Documents canvas was in scope for D-08.
4. **Aborted document GETs during fast SPA navigation.** The QA harness recorded cancelled `/documents` and priority-queue requests when jumping tabs. No console errors; the page recovered. Not a user-facing failure.

---

## 5. Code touched

Frontend: `DocumentsPage.tsx`, `documentsLibrary.ts`, `export.ts`, `AskAiFab.tsx`, `RestoreArchivedPanel.tsx`, `useEsign.ts`, unit tests `documentsLibrary.test.ts` (8/8 with RecentlyDoneStrip **20/20**).

Backend: `app/api/v1/esign.py` (ignore stale in-flight events on a voided/declined/signed envelope), `app/tests/test_esign_api.py`.

---

## 6. Implementation verification (2026-08-13, later the same day)

Headed Chrome (`channel: "chrome"`) against `http://localhost:5173` as `shyna.elene@minafter.com`. Live library: 328 documents / 23 AI-priority / 11 missing.

| Intended behavior | Live result |
| --- | --- |
| D-01 Export CSV | `documents.csv` |
| D-02 Pagination | **20** Preview rows on All docs; Show more |
| D-03 Nested role=button | **0** wrapping cards |
| D-04 Upload requires transaction | Required select; `qa-upload.txt` uploaded |
| D-05 Breadcrumb | Named **Breadcrumb** nav |
| D-06 Missing checkboxes | **40×40** |
| D-07 Header / mobile names | Upload, Send for signature, Restore, Export named at 390px |
| D-08 Min 12px on the page | Pass |
| D-09 Filter documents | Empty + `?q=` |
| D-10 Transaction link | `/transactions/:id?tab=documents` |
| D-11 Archive Undo | Toast **Undo** |
| D-12 `?focus=` | Document stays on All docs |
| Console / page errors | None |

---

## 7. DocuSign e-sign pass (same day, after account connect)

**Tester:** platform admin `shyna.elene@minafter.com`  
**Environment:** headed Chrome (`channel: "chrome"`), `http://localhost:5173`  
**Provider:** DocuSign **demo / sandbox** (`is_demo: true`) — UI shows the watermark note.  
**Script:** `velvet-elves-data/all_documents_qa/all_documents_esign_chrome_qa.mjs`  
**Artifacts:** `all_documents_qa/artifacts_2026-08-13_esign-retest/`

Live send used a clearly named QA PDF on **4567 Oak Ridge Avenue, Boardman, OH** to deal-party **Daniel Carter** (`carter.buyers@testmail.com`). Both test envelopes were **voided** so nothing is left in-flight.

### First send (before fixes)

DocuSign send **worked** (`POST /documents/:id/esign` → **202**, toast **Sent for signature**, Sent tab **Awaiting: Daniel Carter**, Sync **200**). Three product bugs showed up immediately:

| ID | Severity | What happened | Fix |
| --- | --- | --- | --- |
| D-14 | Medium | Opening **Send for Signature** flashed **No e-signature provider connected** until `/esign/provider-status` returned. | Prefetch provider status on the page. Show **Checking DocuSign connection…** while loading; only show the red banner after a confirmed disconnect. Display **Connected to DocuSign** (not `docusign`). |
| D-15 | High | **More › Void Envelope** ran with no confirm — one mis-click cancels a live envelope. | **Void this envelope?** alert (same pattern as Archive). Confirm button: **Void envelope**. |
| D-16 | High | Void API returned `voided` and the toast said **Envelope voided**, but the card stayed **SENT FOR SIG** with Sync (no Resend). Cause: 330-doc list refetch lagged; a late sync/webhook could also write `sent` over `voided`. | Patch the documents cache on send/sync/void. Ignore stale in-flight events when the document is already voided/declined/signed. |

### Retest (after D-14–D-16)

| Check | Result |
| --- | --- |
| Connected banner, no disconnected flash | Pass — **Connected to DocuSign** |
| Demo / sandbox watermark note | Pass (info) |
| Send disabled until tx + doc + signers | Pass |
| Row **Sign** preselects the QA PDF + deal | Pass |
| Party chips add a signer | Pass — Daniel Carter (buyer) |
| Live DocuSign send `202` + toast **Sent for signature** | Pass |
| Sent for sig tab, **Awaiting:**, `?tab=sent_for_signature&q=` | Pass |
| **Sync** → toast **Signature status refreshed** | Pass |
| **Void Envelope** asks **Void this envelope?** | Pass |
| After confirm: **Voided** pill + **Resend** | Pass |
| Cleared today shows a **Voided** row | Pass |
| Resend modal prefills the prior signer | Pass (product) — `carter.buyers@testmail.com` |
| Signed tab does not list the voided file | Pass |
| Console / page errors | Pass |

Harness-only misses on that run (not product): sidebar nav wait timed out then recovered via `/documents`; upload toast was sampled before **Document uploaded** appeared (the QA PDF was on the list); resend assertion originally required the admin email instead of the party that was actually sent.

### Still not exercised

- A signer **completing** the envelope in DocuSign (Signed tab, green **Signed** badge, `N of M complete`, Cleared today **Signed**). `simulate-complete` is stub-only and correctly refuses a real envelope.
- A signer **declining** (Declined pill + Resend copy).
- Sending from the header modal (transaction + document picks) — row Sign was the live path; header modal was checked for connection + disabled Send.
