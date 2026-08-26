# Vendor Portal — browser QA findings (2026-08-26)

**Portal:** Mortgage Partner Workspace (`VendorWorkspaceLayout` / `/portal/vendor`)  
**Tester:** Vendor `tessa.grant@minafter.com` (Mortgage Loan Officer)  
**Password (local QA):** `QWE!@#asd234`  
**Environment:** local frontend `http://127.0.0.1:5173`, backend `http://127.0.0.1:8000`  
**Browser:** installed Google Chrome via Playwright (`playwright-core` + `C:\Program Files\Google\Chrome\Application\chrome.exe`), **headless**, 1280×720, images/fonts aborted, single renderer, Vite `--max-old-space-size=512`. Headed Chrome was not used because this machine is RAM-constrained.

**Dataset:** Tessa is `role=Vendor` on tenant `526cf077-59da-496a-aa38-8f8d761c29da`, user `0fe1fe81-f291-4e34-91cd-3afab9ce1a0e`, assigned to one Active deal:

| Transaction | Address | Buyer | Agent |
| --- | --- | --- | --- |
| `29e4c7f3-de4a-430b-ac11-9284c8bdebab` | 4567 Meadowridge Avenue, Boardman, OH | Maya Ellis | Luis Romero |

Nav under test: **Loan Files · Documents · Tasks**, plus file detail, helper cards, Account / Profile, and staff-URL bounces.

Harness: `velvet-elves-data/vendor_portal_qa/vendor_portal_chrome_qa.mjs`  
Probe: `vendor_portal_qa/_probe_tessa.py`

---

## 1. Executive summary

Tessa signs in and lands on `/portal/vendor` with a mortgage-scoped shell (no Task Queue / Needs You / New Transaction). Before this cycle the portal was **not** seamless: the mortgage officer saw the coordinator’s full checklist, junk milestone dots (`"1"`, `Deadline`, Title Work), a duplicate of her own contact, documents that uploaded with no file, staff Settings/Dashboard chrome, and helper cards that were not links.

Those functional gaps are **fixed**. Headless Chrome **verify6: 42 pass / 0 fail / 0 warn / 42 checks**.

Chrome-green is not the same as “every mortgage job on Meadowridge is done.” Several appraisal/loan tasks are honestly overdue from July 2026 contract dates, repeated QA uploads and document requests have piled up under Documents, and close-out still waits on coordinator/AI review. Do not treat this log as proof of a staff-approved appraisal or a production-clean document tray.

| Severity | Found this cycle | Status |
| --- | --- | --- |
| High | 4 | Fixed |
| Medium | 7 | Fixed |
| Low / harness | 5 | Fixed |

---

## 2. Account notes

`tessa.grant@minafter.com` signs in (`role=Vendor`, mortgage loan officer). Live overview after the scope wall:

- `GET /api/v1/vendor-portal/overview` → **1 file**, family `mortgage`, badge **Appraisal Ordered**, progress **Appraisal Ordered / Appraisal Completed**
- Tasks dropped from **36 leaked coordinator items** to **8 mortgage-visible tasks** (`needs_attention`: 6)
- Contacts: **one** Tessa Grant row (party + vendor assignment no longer duplicate); Maya Ellis email/phone visible; seller hidden
- Staff bookmarks `/settings`, `/dashboard`, `/ai-emails`, `/transactions`, `/client/home` bounce to `/portal/vendor` with no Agent chrome

---

## 3. Pass log

| Pass | Browser | App server | Result |
| --- | --- | --- | --- |
| `verify` | Headless Chrome | Vite 5173 + uvicorn | **20 pass / 19 fail** — scope leak, settings leak, collapsed tasks, upload `transaction_id` null |
| `verify2` | Headless Chrome | Vite + reloaded uvicorn | **35 pass / 4 fail / 1 warn / 40 checks** — expand locator, collapsed task groups, upload listener, mark-done on in-review task |
| `verify3` | Headless Chrome | Vite | **39 pass / 2 fail / 41 checks** — upload listener still raced; Mark done timed out on an already in-review task |
| `verify4` | Headless Chrome | Vite (overview slow after reload) | **32 pass / 8 fail** — home dump ran before overview; hidden file input waited as visible |
| `verify5` | Headless Chrome | Vite | **40 pass / 2 fail / 42 checks** — unique upload name not yet painted; file-detail dump raced the file GET |
| `verify6` | Headless Chrome | Vite + uvicorn | **42 pass / 0 fail / 0 warn / 42 checks** |

Artifacts: `velvet-elves-data/vendor_portal_qa/artifacts_2026-08-26_<pass>/`

Re-run (do **not** set `QA_HEADED=1` on this machine):

```powershell
cd c:\Projects\velvet-elves-data\vendor_portal_qa
$env:QA_PASS='verify'
$env:QA_CHANNEL='chrome'
node vendor_portal_chrome_qa.mjs
```

---

## 4. Issues found and resolved

### VP-H1 · Mortgage vendor saw the coordinator checklist
**Severity:** High · **Area:** `GET /vendor-portal/tasks`, overview `needs_attention`, file card

Tessa received **36** deal tasks, including Deliver HOA, Internal Thank You, Buyer Welcome, Closing Gift, inspection, and other TC work. `needs_attention` was 22. Keyword-miss tasks were treated as GENERIC and shown to every vendor.

**Fix:** `is_task_visible_to_family` in `app/services/vendor_workspace.py`. Mortgage/title see own-family work plus a short shared set (clear-to-close, rate lock). Coordinator “welcome” mail and unmatched TC tasks stay hidden. Out-of-family completion-requests 404.

### VP-H2 · File badge and progress strip used wizard junk
**Severity:** High · **Area:** overview file card

`milestone_label` was `"1"`. The strip mixed Title Work, repeated `Deadline`, and a bare `"1"`.

**Fix:** `is_displayable_milestone_label` skips numeric labels and `Deadline`. Milestones are built only from tasks the vendor can see. Completed tasks no longer get `due_label: Overdue`. Task row `related_to` uses the same displayable filter so a row does not read “Deadline”.

### VP-H3 · Vendor could open staff chrome
**Severity:** High · **Area:** routing / `AppLayout`

`/settings` was universally allowed. Vendors hitting `/dashboard`, `/transactions`, `/ai-emails`, or `/settings` painted Agent `AppLayout`. Clients already bounced; vendors did not.

**Fix:** `isAllowedForRole` no longer treats Settings as universal for Vendor/Client/FSBO. `RoleRoute allowedRoles={['Vendor']}` wraps the vendor layout. `AppLayout` navigates Vendor → `/portal/vendor`. Chrome VP-31–VP-35 all bounce with `leakedStaff=false`.

### VP-H4 · Vendor upload was not bound to the assigned file
**Severity:** High · **Area:** Documents upload

Uploads could POST with `transaction_id` omitted (overview still loading, or no file picker when only one deal). The document then sat unlinked. The portal also did not block a vendor from uploading to an out-of-scope id.

**Fix:** Documents page always sends the assigned file id and disables Upload until that id is known. `POST /api/v1/documents/upload` requires a vendor `transaction_id` in scope (400 without it, 403 if not assigned). After upload, `['vendor-portal']` queries invalidate so Your uploads refreshes.

### VP-M1 · Duplicate Tessa Grant in contacts
**Severity:** Medium · **Area:** file contacts

The same person appeared twice (transaction party + vendor assignment).

**Fix:** Contact projection dedupes by email on the vendor file payload. Chrome: `tessaContacts=1`.

### VP-M2 · Contact rows hid email and phone
**Severity:** Medium · **Area:** `VendorLoanCard`

The API returned Maya’s email/phone; the card did not render them.

**Fix:** Contact rows show email or phone when present. Layout of the card otherwise unchanged.

### VP-M3 · Portal queries stayed stale after mutations
**Severity:** Medium · **Area:** React Query

Task close-out, undo, document request, and upload did not invalidate `['vendor-portal']`, so Files/Tasks/Documents could show pre-action counts.

**Fix:** `useVendorPortal` mutations and `useUploadDocument` invalidate `['vendor-portal']`.

### VP-M4 · Helper cards were not links
**Severity:** Medium · **Area:** Files home

Upload / dates / history cards looked tappable but did not navigate.

**Fix:** Cards are `Link`s to Documents, Files, and Tasks. Chrome VP-29: helper opens Documents.

### VP-M5 · Pending file-card tasks had no Undo
**Severity:** Medium · **Area:** `VendorLoanCard` / Tasks

Mark done sent a pending close-out with no way to pull it back from the file card. Tasks used “Undo request” only after expand.

**Fix:** In-review tasks expose Undo on the file card and on the task row. Chrome VP-26/VP-27: mark done → pending → Undo request DELETE 200.

### VP-M6 · Closed mobile drawer still exposed a second nav
**Severity:** Medium · **Area:** `VendorWorkspaceLayout`

Two `nav[aria-label="Vendor navigation"]` nodes (desktop + `aria-hidden` drawer) broke Playwright strict mode and duplicated the landmark.

**Fix:** Desktop nav is `"Vendor navigation"`; mobile menu is `"Vendor menu"`; closed drawer is `aria-hidden`.

### VP-M7 · Documents request / flag paths were incomplete
**Severity:** Medium · **Area:** Documents

Request-a-document could run without a file. Own uploads in the review modal could not be flagged. Empty-file copy was missing.

**Fix:** Request binds to the assigned file; empty-file copy; flag-for-deletion on the vendor’s own uploads. Chrome VP-20 records an awaiting Pre-approval letter on Meadowridge.

### VP-L1 · Single-file task groups started collapsed
**Severity:** Low · **Area:** Tasks

With one assigned deal, Appraisal Completed was on the page only after expanding the file group. Easy to miss Mark done.

**Fix:** Auto-expand when there is only one file group.

### VP-L2 · Files home flashed “Your files” before overview
**Severity:** Low · **Area:** Files home

While `scope_family` was unknown, the assigned heading read “Assigned Your files” / “Files you can access” with no greeting.

**Fix:** Assigned section stays on the existing skeleton until overview returns. Greeting band was already skeletoned.

### VP-L3 · Hidden file input failed visible waits
**Severity:** Low · **Area:** QA harness

Upload is a visually hidden `<input type="file">`. Playwright’s default `waitFor` requires visible, so VP-21 timed out even when the control was enabled.

**Fix:** Harness waits `{ state: 'attached' }` and sends a uniquely named in-memory file so Your uploads cannot pass on a leftover `qa-upload.txt`.

### VP-L4 · File detail dump raced the file GET
**Severity:** Low · **Area:** QA harness

`dumpText` immediately after `goto` sometimes returned empty (navigation) or skeleton-only (no Meadowridge yet).

**Fix:** Wait for “Back to files” and the Meadowridge address before asserting. Chrome VP-28: address + Appraisal Ordered + Maya Ellis + Luis Romero.

### VP-L5 · Home assertions ran before overview
**Severity:** Low · **Area:** QA harness

After a uvicorn reload, overview could take longer than the greeting wait. VP-05–VP-09 dumped the loading shell.

**Fix:** Wait until the overview JSON (greeting name) is captured, then assert Good day, Tessa.

---

## 5. What Chrome verified (verify6)

- Login as Tessa → `/portal/vendor`, Mortgage Partner Portal, Loan Files / Documents / Tasks
- Greeting, Meadowridge file, boundary notice, mortgage-scoped overview (1 file)
- Badge **Appraisal Ordered**; progress without Title Work / `"1"` / Deadline
- Expand file: contacts (email/phone), one Tessa, no seller, no HOA/thank-you/gift tasks, send note
- Documents tabs, request a document onto the assigned file, upload **with that transaction id**, file listed under Your uploads
- Mortgage Tasks, coordinator checklist hidden, Mark done → pending close-out → Undo
- File detail deep link, helper card → Documents, Profile (`tessa.grant@minafter.com`)
- Staff URLs bounce; no page errors; no unexpected API failures; console clean of app errors

---

## 6. Remaining (data / operational, not Chrome failures)

- Meadowridge still has **honestly overdue** July 2026 appraisal/loan tasks. The portal surfaces them; it does not invent completion.
- Repeated QA passes left extra `qa-upload*.txt` rows and extra “Pre-approval letter” requests. A coordinator can ignore or clear them; they are not product defects.
- Close-out is **pending review**, not auto-closed (AI auto-close stays off by default).
- No invoices, calendar, or SMS were in scope for this portal.

---

## 7. Code touched (not committed)

Backend: `app/services/vendor_workspace.py`, `app/api/v1/vendor_workspace.py`, `app/api/v1/documents.py`, `app/tests/test_vendor_workspace.py`, `app/tests/test_vendor_portal_api.py`

Frontend: `src/utils/returnLocation.ts`, `src/App.tsx`, `src/layouts/AppLayout.tsx`, `src/layouts/VendorWorkspaceLayout.tsx`, `src/hooks/useVendorPortal.ts`, `src/hooks/useDocuments.ts`, `src/pages/vendor/VendorFilesPage.tsx`, `src/pages/vendor/VendorPortalDocumentsPage.tsx`, `src/pages/vendor/VendorPortalTasksPage.tsx`, `src/components/vendor-portal/VendorLoanCard.tsx`, `src/tests/unit/returnLocation.test.ts`

Layout and visual style were left in place; changes are scope, wiring, and loading/disabled states.
