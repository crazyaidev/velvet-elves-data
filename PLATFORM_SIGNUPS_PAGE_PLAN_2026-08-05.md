# Platform › Signups: Implementation Plan

Date: 2026-08-05
Author: Jan (with Claude)
Status: **IMPLEMENTED 2026-08-06, uncommitted** — Jan commits. §14 records what shipped, what changed versus this plan, and how it was verified.
Requirements source: JAKE_REQUIREMENTS_NEW_USER_REGISTRATION_ALERTS_2026-08-05.md (referred to below as R1–R7 / C1–C5 / Q1–Q4).

> **Naming:** shipped as **Account Registrations** at `/platform/registrations`, not "Signups". The API prefix is `/api/v1/platform/registrations` to match. Everything below that says "Signups" refers to this page.

---

## 1. What changes versus Jake's ask, and why

Jake asked for an email alert and explicitly declined a UI ("we don't need a whole UI right now", R6). This plan builds the UI anyway, as a page in the Platform group. That is a deliberate reversal and it should be said out loud rather than buried:

| | Email alert alone | Platform › Signups page |
|---|---|---|
| Answers "did anyone sign up?" | Yes, once, at the moment it happens | Yes, at any time after |
| Answers "who was it, and did they actually try the product?" | No | Yes — workspace, role, whether they ever signed in, whether they created a transaction |
| Survives a missed/filtered/deleted email | No | Yes |
| Lets Jake check on demand before a pitch call | No | Yes |
| Costs us | ~half a day | ~1.5 days (this plan) |

The two are complements, not alternatives. **The plan therefore keeps a minimal email alert (§9)** — it is what Jake actually asked for, and it is the only piece that reaches him without him going to look. The page is the record; the email is the signal.

Cost discipline per R7 (priority stays on the task engine and go-live): everything here reuses existing infrastructure. **No new table, no migration, no new dependency, no feature flag.** The page is a near-copy of `/platform/waitlist`, and the API is a near-copy of `platform_marketing.py`.

---

## 2. Current state (audited 2026-08-05)

### 2.1 The Platform group this page joins

- **Nav** — `velvet-elves-frontend/src/layouts/AppLayout.tsx:465-476`, `buildSection('platform')`, rendered only when `inputs.isPlatformAdmin`. Current items: Tenants, Waitlist, AI usage, Costs & pricing, Help center.
- **Routes** — `velvet-elves-frontend/src/utils/constants.ts:231-245` (`ROUTES.PLATFORM_*`), mounted in `velvet-elves-frontend/src/App.tsx:889-913` inside `<PlatformAdminGuard />`, which 404s the whole subtree for non-platform users.
- **Page chrome** — `velvet-elves-frontend/src/components/platform/PlatformPageHeader.tsx`: breadcrumb (`Platform › <title>`) + serif H1 + optional count badge.
- **Backend gate** — `require_platform_admin` from `app/core/auth.py`; routers registered in `app/api/v1/router.py:121-149`.

### 2.2 The design template: `/platform/waitlist`

`velvet-elves-frontend/src/pages/platform/PlatformWaitlistPage.tsx` is the closest existing page in both purpose and shape, and it is what "harmonizes with the other pages in the platform group" means concretely:

- `PlatformPageHeader` with a `{n} total` mono chip badge.
- Page-owns-its-scroll shell: `flex h-full min-h-0 flex-col` + inner `min-h-0 flex-1 overflow-y-auto px-3 py-4 md:px-6`.
- A 4-up `KpiCard` strip (`@/components/analytics/AnalyticsCharts`) with `eyebrow / value / sub / color`.
- A controls row **above** the list, no intro prose: search input on the left, `SegmentedControl` + Refresh + CSV on the right.
- One `rounded-xl border border-ve-border bg-white shadow-card` table card: `min-w-[760px]` inside `overflow-x-auto`, mono `9px` uppercase tracked column heads, `12.5px` body, per-row bottom borders.
- A footer strip with "Showing a–b of n" and prev/next pagination.
- Client-side CSV built from the same payload, exporting **the current filter**, not the visible page.

The backend counterpart is `app/api/v1/platform_marketing.py` (75 lines): one GET, `require_platform_admin`, `_MAX_LIMIT = 1000`, returns `items` + filter-scoped `total` + whole-table `counts`, and deliberately has **no export endpoint** because the CSV is built client-side.

### 2.3 Why the Costs console's Users tab does not already do this

`app/api/v1/platform_costs.py:334-520` (`GET /platform/costs/users`) does list users across tenants. It is not a substitute:

- It is sourced from the `cost_usage_by_user` RPC over `ai_usage_events` — a **spend** lens. It sorts by cost, calls, or last activity; it cannot sort by signup time and does not carry a signup date at all.
- It has no notion of founder vs invited, no tenant plan/trial context, no "never signed in" state.
- It is gated behind `ve_cost_console_v1` and framed as cost analytics — the wrong place for Jake to answer "did the pitch committee create an account?".

What it does prove is the PII pattern this page must copy: `_safe_pii()` (`platform_costs.py:55-67`) Fernet-decrypts `users.full_name` / `users.email` for display, because those columns are ciphertext at rest.

### 2.4 How a registration actually happens (the data this page reads)

Two paths, both writing `users`:

1. **Self-registration** — `app/services/auth_service.py:51-249`. Provisions a brand-new tenant (`provision_for_self_registration`), creates the `users` row, sets `tenants.owner_user_id`, writes `platform_audit` `tenant_created` + `audit_logs` `user_registered`. `joined_via_invitation_id` stays **NULL** — this is the founder marker. Roles are constrained to `SELF_SIGNUP_ROLES_NOW` (Agent / Team Leader / Transaction Coordinator).
   Note: when Supabase email confirmation is on, `register` returns **202 with no session** — the `users` row already exists before the address is confirmed. So an unconfirmed registration is visible, which is exactly the early-warning signal Jake wants.
2. **Invitation accept** — `app/api/v1/invitations.py:705-753`. Creates the `users` row inside an **existing** tenant with `joined_via_invitation_id` set.

Columns available on `users` (`app/models/user.py`): `created_at`, `last_login_at` (stamped by `touch_last_login`), `onboarding_completed`, `welcome_email_sent_at`, `joined_via_invitation_id`, `role`, `tenant_id`, `is_active`, `is_platform_admin`.
On `tenants` (`app/models/tenant.py`): `name`, `plan`, `trial_ends_at`, `owner_user_id`, `created_at`, `is_active`.
On `transactions` (`app/models/transaction.py:18-19`): `tenant_id`, `created_by` — the "did they actually use it?" signal.

**Constraint that shapes the API:** `users.email` and `users.full_name` are Fernet-encrypted (`app/repositories/user_repository.py`), so search **cannot** be an SQL `ilike`. `get_by_email` already compares decrypted values in Python. This page must fetch → decrypt → filter → paginate, in that order (§4.3).

---

## 3. The page

**Route** `/platform/signups` · **Nav label** "Signups" · **Icon** `UserPlus` (lucide) · **Position** directly under Tenants, above Waitlist — the sidebar then reads top-down as the funnel: workspaces → accounts → waitlist.

Naming note: "Signups" is Jake's own framing ("if anybody registers"). The Waitlist entry keeps its label, so the two never collide in the sidebar. See Q-A in §13 if you prefer "Registrations".

### 3.1 Layout

```
Platform › Signups                                    [ 47 accounts ]
─────────────────────────────────────────────────────────────────────
┌ New this week ┐ ┌ New workspaces ┐ ┌ Signed in ┐ ┌ Outside signups ┐
│      6        │ │       4        │ │   38/47   │ │        3        │
│ 2 in last 24h │ │ founders, 7d   │ │ ever      │ │ non-internal    │
└───────────────┘ └────────────────┘ └───────────┘ └─────────────────┘

[ 🔍 Search name, email, workspace… ]   [ All | Founders | Invited | Outside ] [↻ Refresh] [↓ CSV]

┌───────────────────────────────────────────────────────────────────────────────┐
│ PERSON            WORKSPACE        ROLE   JOINED VIA   ACTIVITY      SIGNED UP │
│ Dana Whitfield    Whitfield Realty Agent  Self sign-up ● 2 deals    Aug 5      │
│ dana@…com         trial · 12d left                     last seen 2h  2h ago    │
│ ─────────────────────────────────────────────────────────────────────────────  │
│ Sam Ortega        Whitfield Realty TC     Invited      ○ Never signed in  Aug 4│
│ sam@…com          trial · 12d left        by Dana W.                     1d ago│
└───────────────────────────────────────────────────────────────────────────────┘
  Showing 1–47 of 47                                          [‹] Page 1/1 [›]
```

### 3.2 Columns

| Column | Content | Source |
|---|---|---|
| **Person** | `full_name` (medium, primary) over `email` (11px, ghost). An `Internal` chip renders inline when §6 classifies the row as ours. | `users.full_name`, `users.email` (both decrypted) |
| **Workspace** | Tenant name over a `plan · trial Nd left` sub-line (or `suspended` in red when `is_active` is false) | `tenants.name`, `plan`, `trial_ends_at`, `is_active` |
| **Role** | Role label chip, house `rounded-full bg-ve-surface-2` pill | `users.role` |
| **Joined via** | `Self sign-up` (founder) or `Invited` + inviter name sub-line | `joined_via_invitation_id` NULL vs set |
| **Activity** | Status dot + label (§3.3), with `last seen <rel>` sub-line | derived |
| **Signed up** | Right-aligned `Aug 5, 2026` over `2h ago`, tabular-nums | `users.created_at` |

No row modal in v1 — R7. Everything a platform admin would open a modal for (plan, seats, wallet, lifecycle) already lives in `TenantDetailModal` on `/platform/tenants`; the Workspace cell links there instead.

### 3.3 Activity status — derived only from columns that exist

Honest states, no invented telemetry:

| State | Rule | Dot |
|---|---|---|
| `Never signed in` | `last_login_at IS NULL` | hollow / ghost |
| `Signed in, not onboarded` | `last_login_at` set, `onboarding_completed = false` | amber |
| `Onboarded` | `onboarding_completed = true`, zero transactions created | blue |
| `N deals` | `transactions.created_by = user.id` count > 0 | green |
| `Deactivated` | `is_active = false` | red, overrides the above |

`Never signed in` is the interesting one for Jake's question: a pitch-committee member who registers and stalls at the confirmation email shows up here, and nowhere else in the product today.

### 3.4 Segments (the `SegmentedControl`)

`All` · `Founders` (new workspace = `joined_via_invitation_id IS NULL`) · `Invited` · `Outside` (default-selected, §6). Default is **Outside**, mirroring how `/platform/waitlist` defaults to the segment that is the reason the screen exists. The count chips in the KPI strip stay whole-table regardless of segment, as on the waitlist page.

### 3.5 Empty state

`No accounts match "…"` when searching; otherwise `No signups yet.` — never demo rows.

---

## 4. Backend

### 4.1 New module: `app/api/v1/platform_signups.py`

```python
router = APIRouter(prefix="/platform/signups", tags=["platform"])

@router.get("", response_model=PlatformSignupsResponse)
async def list_signups(
    segment: Literal["all", "founders", "invited", "outside"] = Query("all"),
    search: str | None = Query(None, max_length=200),
    since: str | None = Query(None, description="ISO date; created_at >= this"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_platform_admin),
    supabase: AsyncClient = Depends(get_supabase),
) -> PlatformSignupsResponse: ...
```

Registered in `app/api/v1/router.py` next to the other platform routers (import at ~line 43, `include_router` at ~line 149).

No feature flag. The Costs console has one because it is a large surface with cost implications; this is a read-only list already invisible behind `require_platform_admin` + `PlatformAdminGuard`. Adding a flag would be ceremony that R7 does not pay for.

### 4.2 Response shape

```python
class SignupRow(BaseModel):
    user_id: str
    email: str | None            # decrypted
    full_name: str | None        # decrypted
    role: str | None
    is_active: bool
    tenant_id: str | None
    tenant_name: str | None
    tenant_plan: str | None
    tenant_trial_ends_at: str | None
    tenant_is_active: bool
    joined_via_invitation: bool
    invited_by_name: str | None  # tenant owner's name; None for founders
    is_internal: bool            # §6
    last_login_at: str | None
    onboarding_completed: bool
    deal_count: int
    created_at: str | None

class SignupsSummary(BaseModel):
    total: int                # every account, unfiltered
    outside: int              # non-internal
    new_7d: int
    new_24h: int
    new_workspaces_7d: int    # founders only
    ever_signed_in: int

class PlatformSignupsResponse(BaseModel):
    items: list[SignupRow]
    total: int                # matches the CURRENT filter → honest pagination
    summary: SignupsSummary   # always whole-table → tiles don't shift on filter
```

### 4.3 Data path (and why it is fetch-then-filter)

1. **Users** — range-paginated read of `users` ordered by `created_at desc`, service-role client (bypasses RLS, which is the point of a platform endpoint). Copy the `_fetch_all_events` chunking pattern from `platform_costs.py:78-90` — never a single unpaginated `.execute()`, which silently truncates at the PostgREST max-rows cap. That bug is already on the record (G-7).
2. **Decrypt** `email` / `full_name` through a local `_safe_pii` (same body as `platform_costs.py:55`; a bad token yields `None`, never leaked ciphertext).
3. **Tenants** — one bulk select of `id, name, plan, trial_ends_at, is_active, owner_user_id` for the distinct `tenant_id`s in hand, into a dict. No per-row query.
4. **Deal counts** — one bulk select of `transactions(created_by)` (+ range pagination), counted in Python into `{user_id: n}`.
5. **Classify** `is_internal` (§6), then **filter** by segment / search / since, then **sort** by `created_at desc`, then **slice** to `offset:offset+limit`.

Search must run after decryption (§2.4) — this is the one place the endpoint knowingly trades scalability for correctness. At current volume (double-digit accounts, low-hundreds of transactions) it is three bulk reads. **Documented upgrade path when it stops being cheap:** a `signup_directory` Postgres RPC doing the joins and the deal-count group-by SQL-side, with search still applied in Python over the decrypted page. Put that sentence in the module docstring so the next person does not have to rediscover the constraint.

### 4.4 Tests

`app/tests/test_platform_signups_api.py`, mirroring `test_platform_marketing_api.py`: 403/404 for a non-platform user; founder vs invited classification; internal classification incl. plus-addressing; search matches decrypted name and email; `total` tracks the filter while `summary` does not; pagination slices correctly.

---

## 5. Frontend files

| File | Change |
|---|---|
| `src/hooks/usePlatformSignups.ts` | **New.** `usePlatformSignups(filters)` via `useApiFetch`, plus `useFetchAllSignups()` for CSV — both copied from `usePlatformMarketingLeads.ts`, including the paging loop that stops at `total` so an export is never silently truncated. |
| `src/pages/platform/PlatformSignupsPage.tsx` | **New.** The page in §3. |
| `src/utils/constants.ts` | Add `PLATFORM_SIGNUPS: '/platform/signups'` beside the other `PLATFORM_*` routes (~line 237). |
| `src/App.tsx` | Import + `<Route path={ROUTES.PLATFORM_SIGNUPS} element={<PlatformSignupsPage />} />` inside the `PlatformAdminGuard` block (~line 895). |
| `src/layouts/AppLayout.tsx` | Add `{ to: ROUTES.PLATFORM_SIGNUPS, icon: UserPlus, label: 'Signups' }` after Tenants in `buildSection('platform')` (~line 470). |

CSV columns: `name,email,role,workspace,plan,joined_via,internal,last_login_at,onboarded,deal_count,created_at` — RFC-4180 quoting via the existing `csvField` helper shape; blob + `<a download>`, `URL.revokeObjectURL` on a 60s timer (never navigate to the URL).

---

## 6. Internal vs outside — the answer to R4

Jake's own objection is the crux: our testing creates accounts constantly, so an unfiltered list is noise. The rule set, cheapest first:

1. `is_platform_admin = true` → internal.
2. Email domain ∈ `internal_signup_domains` → internal. New `Settings` field, comma-separated, default `velvetelves.com`.
3. Email (normalized: lowercased, `+tag` stripped, gmail dots collapsed) ∈ `internal_signup_emails` → internal. New `Settings` field for the personal addresses we test with, including the ones already on the record such as the waitlist test entry.
4. Everything else → outside.

Two rules that matter:

- **The page labels, it never hides.** A misclassified real signup that silently vanishes would defeat the entire purpose. The `Outside` segment filters the view; the `All` segment always shows everything, with an `Internal` chip on the rows we classified as ours.
- **Classification is display-time, not stored.** Adding a tester later reclassifies history correctly, with no migration and no backfill.

---

## 7. Design conformance checklist

Everything here is an existing house rule, listed so the build can be checked against it rather than argued about after:

- `PlatformPageHeader` for chrome; no bespoke header.
- Page owns its scroll: `h-full min-h-0` shell + inner `overflow-y-auto`.
- Controls row above the list; **no intro prose** on a list page.
- Table + (existing) modal, not cards; lucide icons only, never emoji.
- Flat modern surfaces — `border-ve-border`, `bg-white`, `shadow-card`; no gradient strips.
- VE tokens only (`ve-text-primary/secondary/muted/ghost`, `ve-surface-2`, `ve-orange` focus ring), sizes matched to the waitlist page (`12.5px` body, `9px` mono heads, `h-9` controls).
- Table scrolls inside `overflow-x-auto`; the page body never scrolls horizontally.
- Verify by rendering and screenshotting the real page before calling it done — not by reading the JSX.

---

## 8. Acceptance criteria

1. A platform admin sees `Platform › Signups` in the sidebar; a non-platform user gets a 404 on `/platform/signups` and no nav entry.
2. Every account in the database appears exactly once, newest first, across both registration paths (self-registration and invitation accept).
3. A registration that has not confirmed its email or never signed in is visible and reads `Never signed in`.
4. Search matches decrypted name, email, and workspace name.
5. The `Outside` segment excludes every internal address configured in §6; the `All` segment shows them, chipped `Internal`.
6. CSV exports the current filter in full, not the visible page, and the browser saves a file.
7. Screenshot compared side by side with `/platform/waitlist`: same header, tile strip, controls row, table card, and footer rhythm.

---

## 9. Companion: the minimal email alert (keeps Jake's actual ask alive)

Small, and worth keeping — it is the only part that reaches Jake without him looking.

- **Hook point:** `AuthService.register`, `app/services/auth_service.py`, immediately after the audit writes (~line 195) so it fires on both the 202-confirmation branch and the immediate-session branch. Fire-and-forget in a `try/except` — a mail failure must never fail a registration, exactly as the welcome-email call beside it is written.
- **Transport:** `send_platform_email(purpose=EmailPurpose.NOTIFICATION, …)` — support@, already domain-authenticated, and it never raises. Body via `platform_email_rendering.shell/p/bullets/signoff` so it looks like the rest of our mail.
- **Gate:** `settings.is_production` only (C1) **and** not classified internal (§6, shared classifier — one function, two call sites).
- **Content (C2):** email, full name, role, workspace name, signup time, and the `Never signed in` / activity state at send time, plus a deep link to `/platform/signups`.
- **Recipients:** new `Settings.signup_alert_recipients` (comma-separated). Pending Q2.
- Invitation-accept signups do **not** alert — an invite is us or a customer adding their own teammate, which is not the question Jake asked. They still appear on the page.

---

## 10. Security and privacy

- Platform-admin only on both ends (`PlatformAdminGuard` + `require_platform_admin`); the route tree does not exist for anyone else.
- The endpoint returns decrypted PII by design — same posture as the Costs console Users tab, and the reason both are platform-gated. Do not log decrypted values.
- Read-only. No mutation endpoint, no deactivate/impersonate action on this page.
- No new PII is stored; the internal classification is computed per request.

---

## 11. Sequencing and estimate

| # | Step | Est. |
|---|---|---|
| 1 | Backend module + schemas + router registration | 3h |
| 2 | Internal classifier + 2 `Settings` fields (shared with §9) | 1h |
| 3 | Backend tests | 1.5h |
| 4 | Hook + types | 1h |
| 5 | Page, table, tiles, controls, CSV | 4h |
| 6 | Route + nav wiring | 0.5h |
| 7 | Browser verification + screenshot vs `/platform/waitlist` | 1h |
| 8 | §9 email alert | 2h |
| | **Total** | **~2 days, incl. the alert** |

Steps 1–7 ship independently of step 8; if the task-engine work needs the room (R7), ship the page and land the alert after.

---

## 12. Out of scope

- Charts, funnels, cohort or conversion analytics.
- Any write action on an account (deactivate, resend confirmation, impersonate).
- Per-user detail page or modal — the Workspace cell links to the existing `/platform/tenants` modal.
- Changes to `/platform/waitlist`, `/platform/costs`, or the registration flow itself.
- Notifying on invitation-accept signups (§9).

---

## 13. Decisions needed

| # | Question | Recommendation |
|---|---|---|
| Q-A | Nav label: "Signups", "Registrations", or "Accounts"? | **Signups** — Jake's own word, and it does not collide with "Tenants" (workspaces) |
| Q-B | Default segment on open: `Outside` or `All`? | **Outside** — it is the reason the page exists; `All` is one click away |
| Q-C | Which addresses/domains seed `internal_signup_emails` (§6)? | Needed before the alert is trustworthy — list our test addresses |
| Q-D | Still send the §9 alert, or page only? | **Send it.** Jake asked for push, not pull; the page alone silently re-introduces "go look" |
| Q-E | Jake's production account email for platform admin (C5/Q3) | Still outstanding with Jake — without it he cannot open this page either |

---

## 14. What shipped (2026-08-06)

Uncommitted on the working tree; Jan commits. No migration — the page reads columns that already exist.

### 14.1 Files

**Backend**
| File | What |
|---|---|
| `app/api/v1/platform_registrations.py` | **New.** `GET /api/v1/platform/registrations`, platform-admin only. Params: `segment`, `activity`, `search`, `since`, `until`, `sort`, `direction`, `limit`, `offset`. Returns `items` + filter-scoped `total` + whole-table `summary`. |
| `app/services/internal_signups.py` | **New.** The one internal-vs-outside classifier, shared by the page and the alert. `normalize_email` folds `+tag` subaddresses and gmail dots. |
| `app/services/signup_alert_email.py` | **New.** Production-only new-registration alert. Gates run synchronously; only a real send goes to the background. |
| `app/core/config.py` | `internal_signup_domains`, `internal_signup_emails`, `signup_alert_recipients` + list properties. |
| `app/services/auth_service.py` | Alert hooked into `register`, before the confirmation branch so it fires on both exits. Fire-and-forget, swallowed. |
| `app/api/v1/router.py` | Router registered. |
| `app/tests/test_platform_registrations_api.py`, `app/tests/test_signup_alert_email.py` | **New.** 17 tests. |

**Frontend**
| File | What |
|---|---|
| `src/pages/platform/PlatformRegistrationsPage.tsx` | **New.** The page. |
| `src/hooks/usePlatformRegistrations.ts` | **New.** Query hook + `useFetchAllRegistrations` for CSV. |
| `src/utils/constants.ts`, `src/App.tsx`, `src/layouts/AppLayout.tsx` | Route `PLATFORM_REGISTRATIONS`, guarded route, sidebar entry "Registrations" (`UserPlus`) between Tenants and Waitlist. |

### 14.2 Added beyond the plan (requested during the build)

- **Column sorting** — Person / Workspace / Role / Joined via / Activity / Registered, click to sort, click again to reverse, `aria-sort` on the active header. **Server-side**, because paging is: sorting the visible page would reorder a slice rather than the list.
- **Activity filter** — Never signed in / Signed in, not onboarded / Onboarded / Created a transaction / Deactivated.
- **Date-range filter** — All time / 24 hours / 7 / 30 / 90 days (`since`; `until` also exists on the API).
- **Page size 10 / 50 / 100**, default 50, alongside the existing prev/next paging.
- **`activity_state` is now derived once, on the server** (`_activity_state`) and rendered by the client. Filter, sort order and on-screen label therefore cannot disagree — the client no longer has its own copy of the rule.

### 14.3 Two fixes the browser round produced

1. **`example.com` / `.org` / `.net` are internal by default.** RFC 2606 reserves them, so they can never be a real customer, yet the console was counting our own fixture accounts as genuine outside signups — exactly the noise the page exists to remove.
2. **The table no longer blanks on every interaction.** Each filter/sort/page change is a new query key, so react-query showed a full-height spinner in place of the table on every click. Now `placeholderData: keepPreviousData` holds the previous rows while the next load lands; the footer spinner signals the refresh.

### 14.4 Verification

- **Backend:** 42 tests pass (`test_platform_registrations_api.py`, `test_signup_alert_email.py`, `test_auth_api.py`, `test_platform_marketing_api.py`).
- **Frontend:** `npm run build` exits 0 (typecheck included).
- **Real Chrome, 31 checks, all passing** (`_tools/platform-registrations-e2e.mjs`, screenshots in `C:/Projects/_shots/registrations`), against 77 real accounts in the dev database: both guards (anonymous → `/login`; signed-in tenant user gets neither page nor nav entry), page chrome and breadcrumb, all four segments, both activity filters, the date filter (77 → 4 for last 24h) and its restore, search by workspace / decrypted person name / no-match empty state, whole-list sort asc+desc on Person and Registered plus engagement order on Activity, page sizes 10/50/100 with next/prev and no row overlap, CSV export (correct header, forced save, honours the active filter), no horizontal body overflow at 900px, KPI tiles matching the API payload, and a clean console.

Verified rows: the founder shows "Self sign-up" + "1 transaction"; the invited teammate shows "Invited by Dana Whitfield" + **"Never signed in"** — the state that appears nowhere else in the product.

### 14.5 Still open

- **Q-C / Q3 remain with Jake:** which addresses seed `INTERNAL_SIGNUP_EMAILS`, and which production account gets platform admin. In the dev database 69 of 77 accounts still classify as "outside" because our older fixtures use ordinary-looking domains; the classifier is correct, the tester list is simply not filled in yet.
- `SIGNUP_ALERT_RECIPIENTS` is unset, so the alert is inert until someone is named (Q2).
