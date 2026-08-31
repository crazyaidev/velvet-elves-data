# FSBO Portal — browser QA findings (2026-08-19)

**Portal:** FSBO Customer Workspace (`AppLayout` `shellVariant === 'fsbo'`). The operational rebuild (`FSBO_WORKSPACE_OPERATIONAL_REBUILD_PLAN.md`) is **not** live; this pass tests the current shell, not a redesigned Home / composer / property-file layout.

**Tester:** FSBO `yareny.evaly@minafter.com`  
**Password (local QA):** `QWE!@#asd234`  
**Environment:** local frontend `http://127.0.0.1:5173`, backend `http://127.0.0.1:8000`  
**Browser:** Google Chrome via Playwright (`channel: "chrome"`), **headless**, 1280×720, media aborted, single renderer — headed Chrome was avoided because this machine is RAM-constrained.

**Dataset:** Yareny is `role_in_transaction: for_sale_by_owner` on two Active deals (staff `created_by`; portal visibility is invite-to-track):

| Transaction | Address | FSBO state | Closing |
| --- | --- | --- | --- |
| `f5dcbc04-f63d-4bb5-859d-b1cd8dd7a55c` | 14 Maple Prep Lane | `listing_prep` | — |
| `9dacae5e-cf19-4312-b976-81e587dd0df6` | 22 Velvet Contract Ave | `under_contract` | 2026-09-09 |

Nav under test: **Dashboard · My Properties · Documents · Payments · Messages**, plus sidebar **Share milestones**, Ask Aime FAB, Account modal (`/fsbo/settings`), and the public `/milestones/:token` viewer.

Harness: `velvet-elves-data/fsbo_portal_qa/fsbo_portal_chrome_qa.mjs`  
Seed/probe: `velvet-elves-data/fsbo_portal_qa/_seed_fsbo.py`, `_probe_yareny.py`

---

## 1. Executive summary

Yareny signs in, lands on `/fsbo` with both properties, missing-document next steps, coordinator contact, and FSBO-only chrome (no Needs You / Task Queue / New Transaction).

This pass started from a live probe that still showed several seller-facing failures: invited-seller overview could go empty, the bell could load the staff AI-draft inbox, Ask Aime could greet sellers like agents, Payments could render the Client “Your Workspace” shell, nested dialogs blocked minting a share link, and the public viewer 500’d on a non-existent `tenants.brand_color` column.

Those paths are **fixed**. Headless Chrome **verify3: 52 pass / 0 fail / 1 warn / 53 checks**. The warn is FS-51 (Messages is outbound-only — no seller composer on the current shell).

Chrome-green is not the same as “every FSBO job is done.” This account still has **no invoices**, FSBO cannot self-create a property, and Messages has no in-portal reply box. Do not treat this log as proof those operational journeys already shipped.

| Severity | Found this cycle | Status |
| --- | --- | --- |
| High | 3 | Fixed |
| Medium | 5 | Fixed |
| Low / product gap | 3 | Fixed or documented |

---

## 2. Account notes

`yareny.evaly@minafter.com` signs in (`onboarding_completed: true`, role `ForSaleByOwner`, tenant `526cf077-59da-496a-aa38-8f8d761c29da`, user id `5044eefa-98d2-4123-a63e-afaf478d4a21`).

Live probe after seed:

- `GET /dashboard/fsbo/overview` → **2 properties**, 3 missing docs, next step “Upload your missing documents”
- `GET /dashboard/fsbo/notifications` → coordinator messages + `share_link_viewed` (no AI drafts)
- `GET /notifications/pending` → empty staff payload (`ai_drafts_pending: 0`)
- `GET /client/invoices` → 0 items (honest empty Payments)

Re-assigning the same `for_sale_by_owner` row during seed still returned **500**. The seller already had access; this is a staff re-seed bump, not an empty portal. It is not a Chrome failure.

---

## 3. Pass log

| Pass | Browser | App server | Result |
| --- | --- | --- | --- |
| `verify` | Headless Chrome | Vite 5173 + uvicorn | **49 pass / 2 fail / 1 warn** — next-step CTA goes to Documents (not an upload modal); nested Sharing dialog hid the create-link form |
| `verify2` | Headless Chrome | Vite + uvicorn | **51 pass / 1 fail / 1 warn** — share create worked; public viewer 500 (`tenants.brand_color`) |
| `verify3` | Headless Chrome | Vite + reloaded uvicorn | **52 pass / 0 fail / 1 warn / 53 checks** — viewer shows address + Under contract / Closing steps |

Re-run:

```powershell
cd c:\Projects\velvet-elves-data
$env:QA_PASS='verify'; $env:QA_CHANNEL='chrome'
# do not set QA_HEADED=1 on this machine
node fsbo_portal_qa/fsbo_portal_chrome_qa.mjs
```

---

## 4. Issues found and resolved

### FSBO-01 · Invited sellers missing from overview APIs
**Severity:** High · **Area:** `dashboard_role._fsbo_owned_transactions`

Overview / documents / milestones listed only `created_by ==` the FSBO user. Invited sellers got an empty dashboard while property-detail by UUID already allowed them.

**Fix:** load ids via `list_fsbo_owned_transaction_ids` (creator **or** active `for_sale_by_owner` assignment), then `select *` `.in_("id", ids)`. Test: `test_overview_lists_invited_assignment_properties`.

### FSBO-02 · Bell showed tenant AI drafts
**Severity:** High · **Area:** `GET /notifications/pending` + `NotificationsPanel`

The topbar bell loaded the staff pending inbox (AI drafts, outbound-on-your-behalf, Overdue / Today / Tomorrow). That feed is tenant-wide and does not belong on a seller portal.

**Fix:** portal roles get an empty staff pending payload. New `GET/POST /dashboard/fsbo/notifications` lists coordinator messages on owned/invited files plus this user’s `share_link_viewed` rows. The panel uses that feed; View all → `/fsbo/milestones`. `/notifications` is RoleRoute-gated; FSBO bookmarks bounce to `/fsbo`. Frontend does not call `/notifications/pending` for FSBO.

Tests: `test_fsbo_bell_http_omits_tenant_ai_drafts`, `test_fsbo_pending_omits_agent_inbox`. Chrome FS-33: seller copy, no Overdue tabs, no pending hits.

### FSBO-03 · Ask Aime used agent pipeline language
**Severity:** Medium · **Area:** `AIChatPanel` + `POST /dashboard/ai-chat`

Greeting/chips said “overdue tasks / pipeline / active deals”. The chat endpoint loaded the staff portfolio for non-attorneys.

**Fix:** FSBO greeting/chips talk about properties, missing documents, dates, and the coordinator. Backend uses `format_fsbo_chat_context` + `FSBO_CHAT_SYSTEM_PROMPT` and answers “What's missing?” deterministically via `match_fsbo_seller_question`. Live Chrome send listed Maple Prep (lead paint disclosure) and Velvet Contract (deed, settlement statement).

Tests: `src/tests/unit/fsboAiChat.test.ts`, `test_match_fsbo_seller_question_lists_missing_docs`.

### FSBO-04 · Payments used the Client shell
**Severity:** Medium · **Area:** `ClientInvoicesPage` / `ClientInvoiceDetailPage`

`/fsbo/invoices` mounted `ClientPortalShell` (“Your Workspace”). FSBO now uses `FsboPortalShell`. This account has no invoices — empty copy is honest. `/client/invoices` bookmarks map to `/fsbo/invoices` before the generic landing bounce.

### FSBO-05 · Nested Remove control in the upload drop zone
**Severity:** Low · **Area:** `FsboUploadModal`

A Remove `<button>` sat inside the file `<label>`. The drop zone is now a `<div>`; Remove is a sibling of the file `<label>`. Chrome FS-40: 0 nested buttons.

### FSBO-06 · Create share link never showed the recipient form
**Severity:** Medium · **Area:** `FsboShareManagementModal`

“Create share link” opened `ShareMilestoneModal` **on top of** the still-open Sharing dialog. The nested Radix dialog did not become interactable (`#recipient` never visible; POST never fired).

**Fix:** close the management modal, then open the create form. Chrome FS-29 minted `http://127.0.0.1:5173/milestones/…`.

### FSBO-07 · Public viewer 500 on `tenants.brand_color`
**Severity:** High · **Area:** `share_link_service.resolve_token`

`GET /api/v1/milestones/shared/{token}` selected `tenants.brand_color`, which does not exist (`42703`). The UI showed “Link unavailable / Try again later.”

**Fix:** select `name, primary_color` and map it to `tenant_branding.brand_color`. Tenant lookup uses `limit(1)` and degrades instead of 500. When the file has no staff tasks, the viewer still shows the live FSBO stage (**Listing prep** / **Under contract**) and **Closing** when a closing date exists.

Tests: `test_resolve_token_uses_primary_color_not_brand_color`. Chrome FS-30: Velvet Contract Ave, Under contract, Closing due 9/9/2026.

### FSBO-08 · Type below 12px on seller work area
**Severity:** Medium · **Area:** `index.css` `.fsbo-scope #main-content`

Style guide floor is 12px. Compact `text-xs` and arbitrary `text-[7`…`text-[11` sizes inside `#main-content` are lifted. The navy sidebar lockup is unchanged. Chrome FS-39 passed on `#main-content`.

### FSBO-09 · Layout height 0 / 404 retries / staff URL bounce
**Severity:** High (layout) · **Area:** `AppLayout`, `App.tsx` QueryClient, `ProtectedRoute`

Carried from 2026-08-17 and reconfirmed: outlet wrapped in `flex-1 min-h-0`; QueryClient does not retry 400/404; unknown property shows “Property not found”; staff URLs and `/notifications` bounce to `/fsbo`.

---

## 5. Remaining product / data gaps (not Chrome failures)

- **Payments:** Yareny has no invoices. Empty state is correct; paying via Stripe was not exercised.
- **Messages composer:** Messages is an outbound email/sms inbox. There is no seller reply box on the current shell (FS-51 WARN). Staff `channel=note` threads do not appear (by design).
- **Self-serve property create:** FSBO cannot open a deal. Empty copy still tells the seller a coordinator will add the first property.
- **Repeated QA uploads:** this pass uploaded several `qa-upload.txt` files (board “In progress” grew). Flag-for-deletion was exercised; coordinator approval of flags was not.
- **Staff re-seed assignment 500:** posting the same `for_sale_by_owner` assignment again 500’d; the seller already had the row. Not visible in the portal.

The operational rebuild (Home-only nav, in-portal composer, `/fsbo/messages` redirect) was **not** implemented. Do not fail the current portal for missing that shell.

---

## 6. Checks covered (FS-01 … FS-53)

Login and FSBO landing; sidebar labels (Dashboard / My Properties / Documents / Payments / Messages); overview next-step + boundary + API payload; Ask Aime open + seller-safe greeting/chips + live **What's missing?**; Share milestones modal; next-step **Upload missing documents** → Documents; both properties on Dashboard; property workspace six-rail + Timeline / Documents / Contacts; unknown UUID 404; documents board + Missing tab + upload + flag; Messages (outbound inbox) + boundary; `/fsbo/milestones` stays on Messages; Payments empty + FSBO shell; `/client/invoices` → `/fsbo/invoices`; create share link + public viewer + revoke; `/sharing` → `/fsbo`; Account modal; notification bell must not show AI drafts / outbound-on-your-behalf / Overdue tabs; staff URL bounce (`/dashboard`, `/transactions`, `/admin/users`, `/client/home`, `/ai-emails`, `/notifications`); `/fsbo/properties` is a real list; computed type ≥ 12px in main content; no nested buttons; no page errors / console errors / unexpected network failures.

---

## 7. Code touched (this QA cycle)

**Backend:** `app/api/v1/dashboard_role.py`, `app/api/v1/dashboard.py` (FSBO Ask Aime branch), `app/api/v1/notifications.py`, `app/services/fsbo_workspace.py` (seller-safe chat + bell), `app/services/share_link_service.py` (`primary_color` + stage/closing steps), tests in `test_fsbo_workspace.py`, `test_notifications_api.py`, `test_share_link_service.py`.

**Frontend:** `AppLayout.tsx` (KPI buttons, `fsbo-shell` / nav test ids, outlet height, Ask Aime FAB), `App.tsx` (QueryClient 404 skip; `/notifications` RoleRoute), `ProtectedRoute.tsx`, `returnLocation.ts`, `index.css`, `AIChatPanel.tsx`, `FloatingAskAi.tsx`, `NotificationsPanel.tsx`, `useNotifications.ts`, `FsboOverviewPage.tsx`, `FsboPropertyDetailPage.tsx`, `FsboUploadModal.tsx`, `FsboShareManagementModal.tsx`, `ClientInvoicesPage` / detail (`FsboPortalShell`), `src/tests/unit/fsboAiChat.test.ts`, `returnLocation.test.ts`.

**Data:** `fsbo_portal_qa/fsbo_portal_chrome_qa.mjs` (aligned to the live AppLayout shell), this file.

Git `commit` / `push` / `pull` were not run.
