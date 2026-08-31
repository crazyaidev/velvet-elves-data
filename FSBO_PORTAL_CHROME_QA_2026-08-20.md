# FSBO Portal — browser QA findings (2026-08-20)

**Portal:** FSBO Customer Workspace (`AppLayout` `shellVariant === 'fsbo'`).  
**Tester:** FSBO `yareny.evaly@minafter.com`  
**Password (local QA):** `QWE!@#asd234`  
**Environment:** local frontend `http://127.0.0.1:5173`, backend `http://127.0.0.1:8000`  
**Browser:** installed Google Chrome via Playwright (`channel: "chrome"`), **headless**, 1280×720, media aborted, single renderer. Headed Chrome was not used because this machine is RAM-constrained.

**Dataset:** Yareny is `role_in_transaction: for_sale_by_owner` on two Active deals (staff `created_by`; portal visibility is invite-to-track):

| Transaction | Address | FSBO state | Closing |
| --- | --- | --- | --- |
| `f5dcbc04-f63d-4bb5-859d-b1cd8dd7a55c` | 14 Maple Prep Lane | `listing_prep` | — |
| `9dacae5e-cf19-4312-b976-81e587dd0df6` | 22 Velvet Contract Ave | `under_contract` | 2026-09-09 |

Nav under test: **Home · My Properties · Documents · Messages**, plus sidebar **Share milestones**, Ask Aime FAB, Account modal (`/fsbo/settings`), and the public `/milestones/:token` viewer. **Payments** stays hidden while `open_invoice_count === 0`.

Harness: `velvet-elves-data/fsbo_portal_qa/fsbo_portal_chrome_qa.mjs`  
Probes: `fsbo_portal_qa/_probe_yareny.py`, `_probe_fsbo_deep.py`, `_probe_fsbo_aime.py`

---

## 1. Executive summary

Yareny signs in, lands on `/fsbo` with both properties, seller-owed next steps (not deed/CD homework), coordinator contact, and FSBO-only chrome (no Needs You / Task Queue / New Transaction).

This pass started from a live probe that still showed two seller-facing failures on the **under-contract** file:

1. The Documents **Missing** column listed only file-required types (settlement statement, deed). Seller disclosures were still owed and ranked as the portfolio next action, but they had **no Upload row** on the board.
2. Contacts involved listed **Jordan Buyer three times** and **Pat Title three times** (duplicate `transaction_parties` rows).

Those paths are **fixed**. Headless Chrome **verify2: 56 pass / 0 fail / 0 warn / 56 checks**.

Chrome-green is not the same as “every FSBO job is done.” This account still has **no invoices** (Payments nav correctly hidden), `transactions.listing_go_live_date` is not on the live database yet (Ask Aime treats go-live as unset), and repeated QA uploads have grown the In-progress column. Do not treat this log as proof of Stripe pay or a staff-approved photo review.

| Severity | Found this cycle | Status |
| --- | --- | --- |
| High | 1 | Fixed |
| Medium | 3 | Fixed |
| Low / harness | 2 | Fixed |

---

## 2. Account notes

`yareny.evaly@minafter.com` signs in (`onboarding_completed: true`, role `ForSaleByOwner`, tenant `526cf077-59da-496a-aa38-8f8d761c29da`, user id `5044eefa-98d2-4123-a63e-afaf478d4a21`).

Live probe after the board fix:

- `GET /dashboard/fsbo/overview` → **2 properties**, `seller_owed_missing_count: 4`, next steps “Upload your sellers disclosure” (Velvet) and “Upload your lead paint disclosure” (Maple)
- Documents board Missing items now include seller-owed disclosures **and** Velvet-is-collecting settlement/deed
- `GET /client/invoices` → 0 items; sidebar Payments hidden
- Own-upload download **200**; unshared staff purchase agreement download **404**
- `POST /dashboard/fsbo/messages` → 200 (composer)

Banner vs hero (L1) is honest in Chrome: the **banner** stays on Velvet’s sellers disclosure (portfolio-urgent); the **hero** follows the selected Home tile (Maple lead-paint when Maple is first/focused).

---

## 3. Pass log

| Pass | Browser | App server | Result |
| --- | --- | --- | --- |
| `verify` | Headless Chrome | Vite 5173 + uvicorn | **54 pass / 1 fail / 1 warn** — Documents filter tab is labeled “You still need” (harness still looked for “Missing”); KPI assert ran while still on `/fsbo/documents` after the upload CTA |
| `verify2` | Headless Chrome | Vite + reloaded uvicorn | **56 pass / 0 fail / 0 warn / 56 checks** |

Re-run:

```powershell
cd c:\Projects\velvet-elves-data
$env:QA_PASS='verify'
$env:QA_CHANNEL='chrome'
# do not set QA_HEADED=1 on this machine
node fsbo_portal_qa/fsbo_portal_chrome_qa.mjs
```

---

## 4. Issues found and resolved

### FSBO-10 · Under-contract Missing board hid seller-owed disclosures
**Severity:** High · **Area:** `fsbo_workspace.build_document_board`

`22 Velvet Contract Ave` (`under_contract`) still owed sellers disclosure and lead-paint. The next-action engine ranked **Upload your sellers disclosure**. The Documents Missing column used only **file-required** types (PA / CD / settlement / deed). Disclosures are not in that set after the state flip, so the board showed “Velvet is collecting” (settlement, deed) and **no Upload** for the work the seller actually owed.

Sellers tapping the banner/hero “Upload now” could still open the modal via query params. Opening **Documents** itself looked like the file only needed title paperwork.

**Fix:** Missing column items are the ordered union of `seller_owed_missing` + `velvet_collecting_missing`. File-required `missing_doc_types` is unchanged. Counts match the column.

Tests: `test_build_document_board_counts_missing_as_absence`, `test_seller_owed_disclosures_persist_under_contract`. Chrome FS-55 / FS-56.

### FSBO-11 · Contacts involved repeated the same people
**Severity:** Medium · **Area:** `fetch_property_contacts`

Velvet Contract listed Jordan Buyer ×3 and Pat Title ×3 (duplicate party rows from seed). Call/Email looked like three buyers.

**Fix:** after sort, keep the first row per `(party_role, name, email, phone, company)`. Chrome FS-15: one Buyer + one Title.

### FSBO-12 · Property Documents pane listed uploads only
**Severity:** Medium · **Area:** `FsboPropertyDetailPage` Documents rail

The pane showed staff/QA files and **On file** / **Open**, but not the seller-owed gaps. Overview already said “N documents you still need”; the Documents section did not.

**Fix:** “You still need” (Upload → Documents with `tx` + `docType`) and “Velvet is collecting” (status only). Open Documents also seeds `?tx=`.

### FSBO-13 · Launch checklist “Upload” was not a control
**Severity:** Medium · **Area:** property Overview launch checklist

Incomplete listing-prep rows showed the word Upload twice and did not navigate. The checklist is the listing-prep job list; it must complete the upload.

**Fix:** `seller_verb === 'upload'` is an outline **Upload** button to `/fsbo/documents?tx=&docType=`. Layout of the row is unchanged.

### FSBO-14 · `GET /documents` scoped FSBO by client assignment ids only
**Severity:** Medium · **Area:** `documents.list_documents`

Invited Yareny already matched. A `created_by` seller with no assignment would get an empty list (L11). FSBO list now uses `list_fsbo_owned_transaction_ids`.

### FSBO-15 · Upload helper type below 12px
**Severity:** Low · **Area:** `FsboUploadModal`

Helper copy was `text-[11.5px]`. Style guide floor is 12px. Lifted to `text-[12px]`. No layout change.

### Harness FS-20 / FS-47
The Missing filter tab is labeled **You still need**. The CTA from Home opens Documents (modal via `?tx=` / `?docType=`), so KPI/hero asserts must return to `/fsbo` first.

---

## 5. Remaining product / data gaps (not Chrome failures)

- **Payments:** Yareny has no invoices. Empty `/fsbo/invoices` is honest; the nav item is hidden. Stripe pay was not exercised.
- **`listing_go_live_date` column:** not on the live `transactions` table (`42703`). Chat and share-link already retry without it; Ask Aime says go-live is unset. Apply `supabase/migrations/20261002090000_listing_go_live_date.sql` when migrating that database.
- **Staff purchase agreement:** present, `is_client_visible: false` → **On file**, download 404. Correct (L4). Staff must Share with client before Open/Ack/Sign.
- **QA upload residue:** many `qa-upload.txt` rows (In progress ~20). Flag-for-deletion was exercised; coordinator approval of flags was not.
- **Mailbox seed duplicates:** three identical coordinator emails on Velvet Contract (same subject/body). Composer send works; this is seed noise, not a send bug.
- **Self-serve property create:** not v1. Empty copy still says a coordinator adds the first property.
- **Bell share-link rollup:** one grouped “views on your share link” item can have `transaction_id: null` and `href: /fsbo` when views are not stamped per file.

---

## 6. Checks covered (FS-01 … FS-56)

Login and FSBO landing; sidebar (Home / My Properties / Documents / Messages; Payments hidden with 0 invoices); overview next-step + boundary + API payload; Ask Aime open + seller-safe greeting/chips + live **What's missing?** (Maple lead-paint/photos, Velvet disclosures — not deed as homework); Share milestones modal; next-step **Upload now** → upload modal/Documents; KPI strip; portfolio banner vs selected-tile hero (L1); both properties on Home; property workspace six-rail + Timeline / Documents / Contacts (deduped); unknown UUID 404; documents board + You still need + Velvet is collecting + upload + flag; Messages composer + boundary; `/fsbo/milestones` and `/fsbo/properties`; Payments empty + FSBO shell; `/client/invoices` → `/fsbo/invoices`; create share link + public seller timeline (no task names) + revoke; `/sharing` → `/fsbo`; Account modal; notification bell must not show AI drafts / outbound-on-your-behalf / Overdue tabs; staff URL bounce (`/dashboard`, `/transactions`, `/admin/users`, `/client/home`, `/ai-emails`, `/notifications`); computed type ≥ 12px in main content; no nested buttons; no page errors / console errors / unexpected network failures.

---

## 7. Code touched (this QA cycle)

**Backend:** `app/services/fsbo_workspace.py` (Missing column union; contact identity dedupe), `app/api/v1/documents.py` (FSBO list uses owned ids), tests in `test_fsbo_workspace.py`.

**Frontend:** `FsboDocumentsPage.tsx` (`fsbo-upload-cta` on the header Upload), `FsboUploadModal.tsx` (12px helper), `FsboPropertyDetailPage.tsx` (still-needed Documents pane, checklist Upload, `?tx=` on Open Documents).

**Data:** `fsbo_portal_qa/fsbo_portal_chrome_qa.mjs` (You still need tab; return to Home before KPI/hero; FS-55/FS-56; Contacts dedupe), `fsbo_portal_qa/_probe_fsbo_deep.py`, this file.

Git `commit` / `push` / `pull` were not run.
