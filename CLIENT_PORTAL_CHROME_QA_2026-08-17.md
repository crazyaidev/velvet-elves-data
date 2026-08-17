# Client Portal — browser QA findings (2026-08-17)

**Portal:** Represented Client Workspace (`ClientWorkspaceLayout` / closing concierge)  
**Tester:** client `bradyn.dejuan@minafter.com`  
**Password (local QA):** `QWE!@#asd234`  
**Environment:** local frontend `http://127.0.0.1:5173`, backend `http://127.0.0.1:8000`  
**Browser:** Google Chrome via Playwright (`channel: "chrome"`). Headed Chrome exhausted this machine earlier; the recorded pass is **headless Chrome** (`QA_HEADLESS=1`).

**Dataset (live, seeded for this pass):** Bradyn is `role_in_transaction: client` on two Active deals:

| Transaction | Address | Closing |
| --- | --- | --- |
| `f8bf6263-99cd-4ed6-8225-b9a5a951de07` | 77 Harness Test Lane | 2026-09-15 |
| `8045898a-4e17-4af7-aa74-ffa76fbab96f` | 88 Livefire Test Lane | 2026-09-30 |

Nav under test: **Home · Next Steps · Timeline · Documents · Updates**. Payments and Agent Info are reachable from Home, not as duplicate staff chrome.

Harness: `velvet-elves-data/client_portal_qa/client_portal_chrome_qa.mjs`  
(`QA_HEADLESS=1` is required on this box; unset it only if the machine has RAM for a visible window.)

---

## 1. Executive summary

The represented Client Portal is a **closing-concierge shell**, not `AppLayout`. After account repair (deactivated user + out-of-sync password) and two deal assignments, Bradyn lands on `/client/home` with a real hero, seven Home cards, Ask Velvet, Payments, and View all contacts.

The first populated Chrome pass was **not** seamless: timeline deep links used `?transaction=` that the list page ignored; `/client/invoices` and `/client/settings` leaked into staff `AppLayout`; Home had no Payments affordance; type sat at the app’s compact **11.5px** `text-xs`; Ask Velvet / Timeline cards raced the dashboard fetch; `/client/settings` bookmarks closed the Account modal; staff URLs painted Agent chrome while `/users/me` loaded (default role `Agent`).

Those product gaps are **fixed**. Headless Chrome **final3: 62 pass / 0 fail / 1 warn / 63 checks**. The only remaining warn is no invoices on this account (honest empty Payments).

**Operational follow-up (implemented 2026-08-17):** chrome-green is not the same as closing-complete. See `CLIENT_PORTAL_OPERATIONAL_REBUILD_PLAN.md` for shared documents, Sign/Acknowledge, one next-action ranker, Ask-your-team copy, deal switcher, bell, and hiding Payments when there are no open invoices. Do not treat this QA log as proof those journeys already passed.

| Severity | Found | Status |
| --- | --- | --- |
| High | 3 | Fixed |
| Medium | 7 | Fixed |
| Low / harness / data | 5 | Documented |

---

## 2. Account notes (required before any real QA)

`bradyn.dejuan@minafter.com` could not sign in at the start of this work:

1. Profile was **`is_active: false`**. Reactivated via platform admin API as `shyna.elene@minafter.com` (`POST /api/v1/platform/users/{id}/reactivate`). Bradyn’s user id: `d3c6a5fd-4b33-4390-a252-24000d917789`.
2. After reactivation, login still **401** (Supabase Auth password out of sync with the documented QA password). Reset with backend service-role: `auth.admin.update_user_by_id(..., { password: 'QWE!@#asd234', email_confirm: True })`.
3. Dashboard had **0 transactions**. Assigned Bradyn as `role_in_transaction: 'client'` on the two Active deals in the table above.

Working Client login was also confirmed for `binisha.sophi@minafter.com` (not used for this pass). Admin `shyna.elene@minafter.com` is a platform admin. Agent `keison.londyn@minafter.com` shares the same local QA password.

---

## 3. Pass log

| Pass | Browser | App server | Result |
| --- | --- | --- | --- |
| headed first | Headed Chrome | `npm run dev` | Login **401** (deactivated / bad password) |
| headed second | Headed Chrome | `npm run dev` | Interrupted after ~9.5 minutes (RAM) |
| `verify` | Headless Chrome | `npm run dev` | **36 pass / 15 fail / 5 warn** — dashboard race + 11.5px type + settings modal + composer missing |
| `verify3` | Headless Chrome | `npm run dev` | **58 pass / 1 fail / 4 warn** — product checks green; CP-61 counted aborted in-flight GETs |
| `final2` | Headless Chrome | `npm run dev` | **61 pass / 1 fail / 1 warn / 63 checks** — remaining fail: `/admin/users` still showed staff chrome during auth restore |
| `final3` | Headless Chrome | `npm run dev` | **62 pass / 0 fail / 1 warn / 63 checks** — AppLayout Client bounce; `/admin/users` → `/client/home` |

Artifacts: `velvet-elves-data/client_portal_qa/artifacts_2026-08-17_<pass>/`

Re-run:

```powershell
cd c:\Projects\velvet-elves-data
$env:QA_PASS='verify'; $env:QA_HEADLESS='1'; node client_portal_qa/client_portal_chrome_qa.mjs
```

---

## 4. Issues found and resolved

### CP-01 · Timeline deep links used `?transaction=` (list ignored it)
**Severity:** High · **Area:** Home / Next Steps / Updates / backend `milestones_route`

Home next-action and “View Timeline” pointed at `/client/milestones?transaction=<id>`. The list page did not open the detail route `/client/milestones/:id`.

**Fix:** Backend `milestones_route` is now `/client/milestones/{tid}` (`app/services/client_workspace.py`, including demo home). Frontend `clientTimelineHref` / `resolveClientCtaTarget` in `src/pages/client/timeline-utils.ts`. List page **redirects** `?transaction=` → detail. Tests: `app/tests/test_client_workspace.py`, `src/tests/unit/ClientWorkspace.test.tsx`.

**Retest:** CP-12, CP-17, CP-20, CP-23, CP-35 PASS. Query-param bookmarks open detail.

### CP-02 · `/client/invoices` rendered inside staff AppLayout
**Severity:** High · **Area:** Payments

Client invoices used `AppLayout` (Needs You / Task Queue chrome). Spec: Payments from Home, still in the navy concierge shell.

**Fix:** Client invoices mounted under `ClientWorkspaceLayout`. FSBO moved to `/fsbo/invoices` and `/fsbo/invoices/:id`. Gates `ClientPortalInvoicesRoute` / `ClientPortalInvoiceDetailRoute` wait on `useAuth().isLoading` (a null user must not bounce to `/dashboard`). Pages use **ConciergePage** for Client.

**Retest:** CP-13 Payments on Home, CP-43 `/client/invoices`, CP-44 stayed in client navy shell, CP-45 content.

### CP-03 · `/client/settings` killed the Account modal
**Severity:** High · **Area:** Account bookmark

`OpenAccountModalRoute` returned `<Navigate />` on first render. React Router’s Navigate `useEffect` unmounted the route **before** `open()` ran. Harness `dismissOverlays` also pressed Escape after goto, which closed a modal that had just opened.

**Fix:** Open the modal in `useLayoutEffect` (runs before Navigate’s effect); wait for `user` before navigating. QA `gotoPath(..., { escape: false })` on `/client/settings`.

**Retest:** CP-48 Profile from user chip, CP-49 bookmark opens Account over Home.

### CP-04 · Staff chrome while `/users/me` loads (`role` defaulted to Agent)
**Severity:** High · **Area:** `AppLayout`

`AppLayout` used `user?.role ?? 'Agent'`. A full reload of `/admin/users` (or `/transactions`) as a Client painted **Agent** sidebar — including User Management — until `/users/me` returned. Bradyn’s avatar is a large `data:` URL, so that wait is long. Chrome also crashed once on this route (`0xC0000409`) with ProductTour + staff chrome + the data-URI avatar.

**Fix:** While auth is loading, `AppLayout` renders `PageSpinner` (no Agent default). If `user.role === 'Client'`, `<Navigate to={ROUTES.CLIENT_HOME} />`. Client product tour is not started from this layout.

**Retest:** CP-51 dashboard bounce, CP-52 `/transactions` blocked, CP-53 `/ai-emails` blocked, CP-54 `/admin/users` → `/client/home`.

### CP-05 · Type below 12px
**Severity:** Medium · **Area:** Style guide v2

Tailwind `text-xs` is **11.5px** in this app. Concierge lockup, mobile bottom nav, chips, and “Transaction OS” all failed the 12px floor.

**Fix:** `.concierge-scope .text-xs { font-size: 12px; }` in `src/index.css`. Chrome labels use `text-[12px]`. Invoice status pill, upload helper, and concierge eyebrow/back link lifted earlier in this work.

**Retest:** CP-08, CP-18, CP-32, CP-36, CP-46, CP-58 — no text below 12px on concierge surfaces.

### CP-06 · No Payments affordance on Home
**Severity:** Medium · **Area:** Home topbar

**Fix:** Topbar **Payments** link → `/client/invoices`.

**Retest:** CP-13 PASS.

### CP-07 · Mobile Notifications bell was a no-op; overlay intercepted clicks
**Severity:** Medium · **Area:** Mobile chrome

Bell now navigates to `/client/updates`. Overlay `aria-label` is **Dismiss navigation overlay** (no longer clashes with **Close menu**).

**Retest:** CP-55–57 PASS (bell → `/client/updates`).

### CP-08 · Documents empty copy and nested cards
**Severity:** Medium · **Area:** Documents

Empty list said “shared with you”; cards nested. Copy is own-uploads. `PortalDocumentList` takes `embedded` + `emptyMessage`.

**Retest:** CP-25, CP-26, CP-27 PASS. Upload enables when deals exist (CP-28); submit requires file+type (CP-29); Chrome QA file uploaded (CP-30).

### CP-09 · Ask Velvet / Message Agent / dashboard race
**Severity:** Medium · **Area:** Home + harness

QA measured Home before `GET /dashboard/client` returned (`lastDashboard` null → “0 transactions”). Message Agent ran against a skeleton; composer missing after a full `page.goto`.

**Fix:** Ask Velvet focuses on `requestAnimationFrame` + timeout; input id `ask-velvet-input`. Timeline cards have `aria-label="View timeline for {address}"`. Harness waits for hero / Ask Velvet / in-app nav instead of full reloads where possible. API calls from a `127.0.0.1` page rewrite `localhost` → `127.0.0.1` (`loopbackAlignedBaseUrl`) so Windows IPv6 `::1` misses stop breaking the dashboard.

**Retest:** CP-06 2 tx + hero + 7 cards; CP-10 focus; CP-15 send; CP-20 detail; CP-33–35 Updates.

### CP-10 · Loopback API host mismatch
**Severity:** Medium · **Area:** `src/utils/api.ts`

Vite defaults `VITE_API_BASE_URL` to `http://localhost:8000`. Uvicorn bound to `127.0.0.1`. Chrome’s `localhost` → `::1` logged as `requestfailed` even when IPv4 succeeded.

**Fix:** Align API host with `window.location.hostname` for loopback.

**Retest:** CP-61 ignores aborted in-flight GETs; remaining HTTP errors would still fail the check.

---

## 5. Remaining warnings / data gaps (not treated as render bugs)

| Check | Notes |
| --- | --- |
| CP-47 invoice detail | Bradyn has **no invoices**. Payments list empty-state is honest. Seed an invoice if pay-now QA is needed. |
| Account modal kickers | Shared Account modal still uses 9px / 11.5px chrome **outside** `.concierge-scope`. Not part of the portal type walk. |
| Data-URI avatar | Bradyn’s `avatar_url` is a large inline JPEG. It slows `/users/me` on every full reload. Worth storing as a URL, not a data URI, in a later pass. |

---

## 6. What was verified green

- Login as Client → `/client/home` (not staff dashboard, not legacy `/client/transactions`).
- Concierge nav only: Home, Next Steps, Timeline, Documents, Updates.
- No Needs You / Task Queue / AI Suggestions / New Transaction staff copy on Home (word-boundary check so “needs your signature” does not false-fail).
- Two assigned properties; hero “You're Buying 77 Harness Test Lane”; seven cards; Ask Velvet send; Message Agent focuses the composer; Closing Day Info scrolls to Upcoming Dates.
- Timeline list → detail `/client/milestones/:id`; Back to Timeline; `?transaction=` redirect.
- Documents: no fake board, own-uploads empty copy, upload modal, successful fixture upload.
- Updates: Ask Velvet + Recent Updates; timeline href is a path param.
- Agent Info is **not** a sidebar item; tel/mail hit targets ≥40px.
- Payments stay in the navy shell.
- Profile modal and `/client/settings` bookmark.
- Legacy `/client/transactions` → Home. `/dashboard`, `/transactions`, `/ai-emails` bounce out of staff tools.
- Mobile 390: bottom nav, drawer, bell → Updates, type ≥12px.
- Logout → `/login`. No page errors. No console errors after filtering the known framer-motion `ref` warning on staff-layout bounces.

---

## 7. How to re-run on a low-RAM machine

1. Backend: `uvicorn` on `127.0.0.1:8000`.
2. Frontend: `npm run dev -- --host 127.0.0.1 --port 5173` (or `vite preview` if headed Chrome OOMs).
3. Confirm Bradyn is active, password is `QWE!@#asd234`, and the two deal assignments still exist.
4. From `velvet-elves-data`:

```powershell
$env:QA_PASS='light'; $env:QA_HEADLESS='1'; node client_portal_qa/client_portal_chrome_qa.mjs
```

Do **not** git commit/push these QA artifacts or account-repair scripts unless asked.
