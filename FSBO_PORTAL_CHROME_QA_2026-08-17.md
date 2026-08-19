# FSBO Portal — browser QA findings (2026-08-17)

**Portal:** FSBO Customer Workspace (`AppLayout` `shellVariant === 'fsbo'`)  
**Tester:** FSBO `yareny.evaly@minafter.com`  
**Password (local QA):** `QWE!@#asd234`  
**Environment:** local frontend `http://127.0.0.1:5173`, backend `http://127.0.0.1:8000`  
**Browser:** Google Chrome via Playwright (`channel: "chrome"`). Headed Chrome exhausted this machine earlier; the recorded pass is **headless Chrome**.

**Dataset (live, seeded for this pass):** Yareny is `role_in_transaction: for_sale_by_owner` on two Active deals (she does not `created_by` them — portal visibility is invite-to-track):

| Transaction | Address | FSBO state | Closing |
| --- | --- | --- | --- |
| `f5dcbc04-f63d-4bb5-859d-b1cd8dd7a55c` | 14 Maple Prep Lane | `listing_prep` | — |
| `9dacae5e-cf19-4312-b976-81e587dd0df6` | 22 Velvet Contract Ave | `under_contract` | 2026-09-07 |

Nav under test: **Dashboard · My Properties · Documents · Payments · Messages**, plus the sidebar-footer **Share milestones** modal, Ask Aime FAB, Account modal (`/fsbo/settings`), and the public `/milestones/:token` viewer.

Harness: `velvet-elves-data/fsbo_portal_qa/fsbo_portal_chrome_qa.mjs`  
Seed/probe: `velvet-elves-data/fsbo_portal_qa/_seed_fsbo.py`, `_probe_yareny.py`

---

## 1. Executive summary

Yareny logs in, lands on `/fsbo` with two properties, five missing-document requirements, a coordinator banner, and FSBO-only chrome (no Needs You / Task Queue / New Transaction).

The first Chrome pass was **not** seamless. Invited sellers were invisible to overview APIs until ownership was unioned with `for_sale_by_owner` assignments. Tool pages (`h-full overflow-hidden`) collapsed to height 0 inside `AppLayout`, which clipped the property-section rail, the Documents **Upload document** button, and the unknown-property 404. Public share links 500'd because the viewer selected a non-existent `tenants.brand_color` column. `/client/invoices` bookmarks bounced to `/fsbo` instead of Payments.

Those product gaps are **fixed**. A later Chrome pass then found Ask Aime still greeting FSBO sellers like agents (“overdue tasks”, “pipeline”). That path now uses seller-safe context, greeting, and chips.

A review after that pass found the **notification bell still showing the staff AI-draft inbox** (39 drafts awaiting review, outbound emails sent on the agent’s behalf, Overdue/Today/Tomorrow). That feed is tenant-wide and does not belong on the FSBO portal. It is now a seller-only bell (coordinator messages + share-link views). `GET /notifications/pending` returns an empty staff payload for portal roles.

Headless Chrome **bellfix: 49 pass / 0 fail / 1 warn / 50 checks** (FS-01…FS-50). The warn is the existing Listing-prep filter tab (FS-11), not the bell.

Chrome-green is not the same as “every FSBO job is done.” This account still has **no invoices** (honest empty Payments), the public viewer’s timeline is empty until staff tasks exist, and FSBO cannot self-create a property. Do not treat this log as proof those operational journeys already passed.

| Severity | Found | Status |
| --- | --- | --- |
| High | 4 | Fixed |
| Medium | 7 | Fixed |
| Low / harness / data | 4 | Documented |

---

## 2. Account notes

`yareny.evaly@minafter.com` could sign in from the start (`onboarding_completed: true`, role `ForSaleByOwner`, tenant `526cf077-59da-496a-aa38-8f8d761c29da`, user id `5044eefa-98d2-4123-a63e-afaf478d4a21`).

The first API probe returned **0 properties**. FSBO customers do not own deals via `created_by` (staff creates the file). Portal visibility is `transaction_assignments.role_in_transaction = 'for_sale_by_owner'`. The two rows in the table above were seeded as admin `shyna.elene@minafter.com` (buyer + title parties and a staff-uploaded purchase agreement on the contract file).

Duplicate assignment of the same role used to 500; create-assignment is now idempotent for the same role (409 only when the active role differs).

---

## 3. Pass log

| Pass | Browser | App server | Result |
| --- | --- | --- | --- |
| `first` | Headless Chrome | Vite + uvicorn | **Login/overview green; property rail, 404, upload CTA failed** — then harness crashed filling Ask Aime’s disabled textarea instead of the flag reason |
| `verify` | Headless Chrome | Vite + uvicorn (layout fix) | **41 pass / 1 fail / 1 warn** — `/client/invoices` → `/fsbo`; public viewer 500 (`tenants.brand_color`) |
| `final` | Headless Chrome | Vite + restarted uvicorn | **42 pass / 1 fail** — FS-05 overview payload raced; viewer still loading when asserted |
| `final2` | Headless Chrome | Vite + uvicorn | **42 pass / 1 fail** — viewer actually rendered Maple Prep; harness treated the privacy line “internal notes” as staff leakage |
| `final3` | Headless Chrome | Vite + uvicorn | **43 pass / 0 fail / 0 warn / 43 checks** |
| `aime` | Headless Chrome | Vite + restarted uvicorn | **48 pass / 0 fail / 1 warn** — next-step **Upload missing documents** was covered by the Sharing dialog left open from the Share Links Live KPI |
| `aime2` | Headless Chrome | Vite + uvicorn | **49 pass / 0 fail / 0 warn / 49 checks** |
| `bellfix` | Headless Chrome | Vite + restarted uvicorn | **49 pass / 0 fail / 1 warn / 50 checks** — FS-33 now asserts no staff AI-draft inbox; FS-50 `/notifications` → `/fsbo`. Warn is FS-11 Listing-prep tab. |

Re-run:

```powershell
cd c:\Projects\velvet-elves-data
$env:QA_PASS='verify'; $env:QA_CHANNEL='chrome'
node fsbo_portal_qa/fsbo_portal_chrome_qa.mjs
```

Do not set `QA_HEADED=1` on this machine unless it has RAM for a visible Chrome window.

---

## 4. Issues found and resolved

### FSBO-01 · Invited sellers were missing from overview / documents / milestones
**Severity:** High · **Area:** backend `dashboard_role._fsbo_owned_transactions`

Overview listed only transactions with `created_by ==` the FSBO user. Invited sellers (assignment `for_sale_by_owner`) got an empty dashboard while `GET /dashboard/fsbo/properties/{id}` already allowed them.

**Fix:** list ids via `fw.list_fsbo_owned_transaction_ids` (creator **or** active assignment), then fetch those rows. Test: `test_overview_lists_invited_assignment_properties`. Stale uvicorn did not hot-reload this; a restart was required before overview returned 2 properties.

### FSBO-02 · Duplicate assignment 500
**Severity:** Medium · **Area:** `POST /transaction-assignments`

Re-seeding the same FSBO assignment crashed. Duplicate **same role** now returns the existing row; a **different** role on an active assignment is 409.

### FSBO-03 · Tool pages painted at height 0
**Severity:** High · **Area:** `AppLayout` `<main>` / `FsboPortalShell` / property detail

`#main-content` was `flex flex-col overflow-hidden` with the `<Outlet />` as a sibling of `PendingInvitesBanner`. FSBO tool pages use `h-full overflow-hidden`. Percentage height collapsed to 0, so Playwright (and a seller at 1280×720) could not see:

- Property Detail section rail (Overview / Timeline / Documents / Contacts / Sharing / Messages)
- Documents header **Upload document**
- “Property not found” copy (React Query also retried 404s, so the page sat on Loading…)

**Fix:** wrap the outlet in `flex-1 min-h-0`; give FSBO shells `flex-1`; do not retry 400/404 globally; show an honest 404 without three backoff retries.

### FSBO-04 · Payments used the Client “Your Workspace” shell
**Severity:** Medium · **Area:** `ClientInvoicesPage` / `ClientInvoiceDetailPage`

`/fsbo/invoices` mounted `ClientPortalShell`. FSBO now uses `FsboPortalShell` (title Payments, FSBO breadcrumb). This account has no invoices — empty copy is honest.

### FSBO-05 · `/client/invoices` bookmark dropped the seller on Overview
**Severity:** Medium · **Area:** `ProtectedRoute`

Portal bounce ran before (and then instead of) `ClientPortalInvoicesRoute`’s FSBO → `/fsbo/invoices` redirect, so `/client/invoices` became `/fsbo`.

**Fix:** `portalBookmarkRedirect()` maps `/client/invoices` and `/client/invoices/:id` to the FSBO payment routes **before** the generic landing bounce. Portal roles also bounce to landing **before** a staff `requiredRole` gate would send them to `/unauthorized`.

### FSBO-06 · Public milestone viewer 500
**Severity:** High · **Area:** `share_link_service.resolve_token`

`GET /api/v1/milestones/shared/{token}` selected `tenants.brand_color`, which does not exist (`42703`). The UI showed “Link unavailable / Try again later” for a brand-new link.

**Fix:** select `name, primary_color` and map it to the existing `tenant_branding.brand_color` JSON field. Tenant/transaction lookups use `limit(1)` and degrade instead of 500. Test: `test_resolve_token_maps_tenant_primary_color`.

### FSBO-07 · Property Documents pane hid missing requirements
**Severity:** Medium · **Area:** `FsboPropertyDetailPage` Documents pane

The pane listed uploaded files only, so a property with three missing docs looked empty. It now shows a **Still needed** list plus **Upload missing documents**.

### FSBO-08 · Nested file-remove control inside the upload drop zone
**Severity:** Low · **Area:** `FsboUploadModal`

A `<button>` sat inside the file `<label>` (activate-both, nested interactive). Selected-file state is now a separate row with Remove outside the drop zone.

### FSBO-09 · Type below 12px
**Severity:** Medium · **Area:** `index.css` `.fsbo-scope`

Style guide forbids text below 12px. Compact `text-[7.5px]` lockup badges were not caught by the previous `text-[8`…`text-[11` override. The lift now includes `text-[7`. Property-detail 9px column kickers were raised in source as well.

### FSBO-10 · Sidebar KPIs were a `button | div` with `type=`
**Severity:** Low · **Area:** `AppLayout`

FSBO KPI tiles are real `<button type="button">`; other shells stay `<div>`.

### FSBO-11 · Ask Aime used agent pipeline language and agent context
**Severity:** Medium · **Area:** `AIChatPanel` + `POST /dashboard/ai-chat`

The FAB opened, but the greeting and chips were agent-centric (“active deals”, “Show overdue tasks”, “Summarize my pipeline”). The chat endpoint loaded the staff portfolio / task dump for non-attorneys, so an invited FSBO seller could be coached like a coordinator.

**Fix:** FSBO greeting/chips talk about properties, missing documents, dates, and the coordinator. Backend loads seller-safe context via `format_fsbo_chat_context` (owned + invited properties only — not the rest of the tenant) and a seller system prompt. Follow-up chips never mention overdue tasks or pipeline. Live Chrome send of **What's missing?** listed Maple Prep (2) and Velvet Contract (3) correctly.

Tests: `test_fsbo_chat_context_includes_invited_property_not_tenant_dump`, `src/tests/unit/fsboAiChat.test.ts`.

### FSBO-12 · Bell showed tenant AI drafts as FSBO notifications
**Severity:** High · **Area:** `GET /notifications/pending` + `NotificationsPanel`

The FSBO topbar bell loaded the **staff** pending inbox (`list_pending_ai_drafts(tenant_id)` plus “outbound emails sent on your behalf”). Yareny’s panel showed **39 AI drafts awaiting review**, **2 outbound emails**, and Overdue/Today/Tomorrow tabs while the body said she was caught up. The red badge was the tenant AI-draft unread bit, not a seller notice. **View all** went to `/notifications` (staff task queue).

That logic is wrong for a customer workspace: drafts and “sent on your behalf” belong to coordinators, not invited sellers.

**Fix:**
- Portal roles (FSBO / Client / Vendor / Attorney) get an empty staff pending payload — no drafts, no outbound-on-your-behalf, no task buckets.
- New `GET/POST /dashboard/fsbo/notifications` (`list_fsbo_bell_notifications`) lists unread coordinator messages on owned/invited files plus this user’s `share_link_viewed` rows. `ai_draft_pending` and other owners’ logs are excluded.
- The panel uses that feed: no staff tabs, no AI-draft banner, empty copy about coordinator messages / share-link views. View all → `/fsbo/milestones`. `/notifications` is RoleRoute-gated and removed from the FSBO URL allow-list.

Live probe: pending `ai_drafts_pending: 0`; FSBO bell returned share-link views only. Chrome FS-33 opened the dialog with `unread=6` and no AI-draft/outbound/Overdue copy; FS-50 bounced `/notifications` to `/fsbo`. The session did not call `/notifications/pending`.

Tests: `test_fsbo_pending_omits_agent_inbox`, `test_fsbo_bell_lists_unread_coordinator_message_not_other_owners`, `test_fsbo_bell_http_omits_tenant_ai_drafts`, `isStaffNotificationRole` / `fsboBellHref` unit tests.

---

## 5. Remaining product / data gaps (not Chrome failures)

- **Payments:** Yareny has no invoices. Empty state is correct; paying an invoice was not exercised.
- **Public viewer timeline:** Share links resolve and show the address + privacy line. Milestone steps stay empty until the file has tasks. Listing-prep Maple Prep has no closing date (`Closing —`).
- **Messages:** FSBO Messages only show outbound `email` / `sms`. Staff `channel=note` threads do not appear (by design).
- **Self-serve property create:** FSBO cannot open a deal. Empty copy still tells the seller a coordinator will add the first property — true, but there is no in-portal request flow.
- **Repeated QA uploads:** this pass uploaded several `qa-upload.txt` files (board “In progress” grew). Flag-for-deletion was exercised; coordinator approval of flags was not.

---

## 6. Checks covered (FS-01 … FS-50)

Login and FSBO landing; sidebar labels; overview next-step + boundary + API payload; Ask Aime open + seller-safe greeting/chips + live **What's missing?** reply; portfolio chip; Share milestones modal; Missing-docs KPI → `/fsbo/documents`; Share Links Live KPI → Sharing modal; next-step **Upload missing documents** → Documents; both properties; Listing prep and Under contract filters; property workspace rail + Timeline / Documents / Contacts / Sharing; unknown UUID 404; documents board + Missing tab + upload + flag; Messages (main pane) + boundary; Payments empty + FSBO shell; `/client/invoices` → `/fsbo/invoices`; create share link + public viewer + revoke; `/sharing` → `/fsbo`; Account modal; notification bell **must not** show AI drafts / outbound-on-your-behalf / Overdue tabs; staff URL bounce (`/dashboard`, `/transactions`, `/admin/users`, `/client/home`, `/ai-emails`, `/notifications`); computed type ≥ 12px; no nested buttons; no page errors / console errors / unexpected network failures.

---

## 7. Code touched (this QA cycle)

**Backend:** `app/api/v1/dashboard_role.py`, `app/api/v1/dashboard.py` (FSBO Ask Aime branch), `app/api/v1/transaction_assignments.py`, `app/api/v1/notifications.py` (empty pending for portal roles), `app/api/v1/client_notifications.py` (`share_link_viewed`), `app/services/share_link_service.py`, `app/services/fsbo_workspace.py` (seller-safe chat context + bell feed), `app/schemas/dashboard_role.py`, tests in `test_fsbo_workspace.py`, `test_transaction_assignments_api.py`, `test_share_link_service.py`, `test_notifications_api.py`.

**Frontend:** `AppLayout.tsx`, `App.tsx` (QueryClient 404 skip; `/notifications` RoleRoute), `ProtectedRoute.tsx`, `returnLocation.ts`, `index.css`, `AIChatPanel.tsx`, `NotificationsPanel.tsx`, `NotificationsPage.tsx`, `useNotifications.ts`, FSBO pages/shell/upload modal, `ClientInvoicesPage` / detail (FSBO shell), `FsboShareManagementModal.tsx` (12px type), public `MilestoneViewerPage.tsx`, `src/tests/unit/fsboAiChat.test.ts`, `unreadNotificationCount.test.ts`, `returnLocation.test.ts`.

**Data:** `fsbo_portal_qa/*`, this file.

Git `commit` / `push` / `pull` were not run.
