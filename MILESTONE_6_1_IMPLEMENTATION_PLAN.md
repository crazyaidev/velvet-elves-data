# Milestone 6.1 — White-Label & Multi-Tenant: Implementation Plan

**Milestone:** 6.1 — White-Label & Multi-Tenant (Phase 6, Week 20)
**Status:** Draft for approval · **Drafted:** 2026-06-02
**Scope discipline:** This document is a *plan only*. No source code is changed by it.

---

## 0. Why this plan exists (read this first)

Previous milestone plans broke during front-end testing because they were written
*before* a full reading of (a) the requirements and system-design documents and
(b) the **code that is actually deployed today**. The result was plans that
assumed work was missing when it was already shipped, or assumed work was shipped
when it was only a static mockup. Testers — who are **real-estate professionals,
not engineers** — then hit dead-end buttons, "Coming soon" placeholders, and
flows that 403'd or silently did nothing.

This plan is written *after* a line-by-line review of the Milestone 6.1 surface
area. Section 2 is a **grounded current-state inventory** with file citations, so
every task below is anchored to what truly exists. The governing rule for every
deliverable is the one the client keeps repeating:

> **If a real-estate professional cannot exercise it end-to-end with a mouse,
> through the product UI, with no engineer, no API client, and no fake data — it
> is not done.**

Three standing constraints from prior client feedback are treated as hard
requirements throughout:

1. **No demo/mock data on real surfaces.** Every value a tester sees must come
   from real model state, or show an honest empty state. The current Branding and
   AI-credits panels violate this and are explicitly remediated below.
2. **Pixel-respecting, brand-consistent UI.** Every new surface conforms to
   `STYLE_GUIDE.md` (token system, type hierarchy, card vocabulary, no native
   `<select>`, no dead buttons) and, where an approved comp exists (the Closing
   Calendar), reproduces it faithfully.
3. **Minimum data entry.** Connections are one-click OAuth popups, not
   token-paste forms. Branding has a live preview. Calendar push is one button.
   CRM setup is copy-a-URL + a "Send test event" button.

---

## 1. What Milestone 6.1 must deliver (from `milestones.txt`)

| # | Deliverable | Requirement anchor |
|---|---|---|
| 1 | Multi-tenant data isolation (Supabase RLS policies) | Req §9.5, §10.2; SYSTEM_DESIGN §2.4 |
| 2 | White-label configuration UI: logo upload, brand colors, theme selection, custom domain/subdomain | Req §9.5, §10.5 (Tenant Settings) |
| 3 | Apply branding across: login, all role dashboards (Solo Agent, Team Leader, Attorney, FSBO), email templates, documents | Req §9.5 |
| 4 | Tenant management admin panel | Req §10.5 |
| 5 | CRM integration webhooks (generic RESTful): contact sync, task sync, two-way data flow architecture | Req §7.3 |
| 6 | MLO / title-company integration hooks | Req §7.5, §7.6 |
| 7 | Calendar API integration (Google Calendar, Outlook): schedule appointments, send reminders, manage events | Req §7.1 |
| 8 | Integration tests for multi-tenant isolation | Success criteria |

**Success criteria (milestones.txt):** *"Multiple tenants with isolated data and
custom branding, integration hooks operational and documented."*

---

## 2. Grounded current-state inventory

Reviewed: `velvet-elves-backend/app` (routers, services, schemas, migrations) and
`velvet-elves-frontend/src` (pages, components, hooks, contexts). Citations are to
files that exist today.

### 2.1 Deliverable-by-deliverable reality

| # | Deliverable | Real status today | Evidence |
|---|---|---|---|
| 1 | **RLS data isolation** | **Isolation already enforced at the app/repository layer (tenant_id filtering); DB-level RLS is authored but dormant by default.** The request-level dispatcher `get_user_supabase_or_service` flips between user-scoped and service-role, but `settings.use_user_scoped_supabase` **defaults to `False`** (`app/core/config.py:70`), so policies do not yet execute. 6.1 work = decide/verify activation + prove isolation in the UI. | `supabase/migrations/20260511094000_rls_tenant_isolation.sql`, `20260512098000_rls_fixes_task_templates_and_share_tokens.sql`; `app/core/supabase_client.py` (`get_supabase`, `get_user_supabase`, `get_user_supabase_or_service`); `app/core/config.py:70` (`use_user_scoped_supabase=False`); tests `test_rls_dispatcher.py`, `test_task_tenant_isolation.py` |
| 2 | **White-label config UI** | **Static mockup — the core gap.** Backend tenant model already stores branding; the UI does not save it. | Backend: `app/api/v1/tenants.py` `PATCH /tenants/current` accepts `logo_url`/`primary_color`/`secondary_color`/`domain`; **Frontend mockup:** `OrganizationPage.tsx` Branding pane — logo "Upload logo" button has **no handler**, color & display-name inputs are `defaultValue` only, **"Save branding" has no `onClick`** |
| 3 | **Apply branding everywhere** | **Engine exists but is not wired to tenant data.** `ThemeContext` maps colors→CSS vars, but reads **localStorage only**, never the tenant record; login screen has no tenant branding. Invite email is already per-tenant branded. | `contexts/ThemeContext.tsx` (`STORAGE_KEY` localStorage, no fetch of `tenants.primary_color`); `app/services/branded_invite_email.py` (email already branded) |
| 4 | **Tenant management admin panel** | **Substantially built.** Platform-admin list/detail pages + suspend/reactivate/legal-hold/archive endpoints exist. | `pages/platform/PlatformTenantsPage.tsx`, `PlatformTenantDetailPage.tsx`, `hooks/usePlatformTenants.ts`, `components/platform/PlatformAdminGuard.tsx`; `app/api/v1/platform_tenants.py`, `tenants.py` |
| 5 | **CRM webhooks (contacts/tasks, two-way)** | **Greenfield. Nothing exists.** No CRM router, no outbound webhook dispatcher, no inbound sync endpoints, no API-key model. | No `crm`/`webhook`/`sync` router or service in `app/api/v1` or `app/services` |
| 6 | **MLO / title-company hooks** | **Greenfield. Nothing exists.** | (same) |
| 7 | **Calendar integration** | **Route, nav entry, and page shell already exist — content is a placeholder.** `ROUTES.CALENDAR = '/calendar'` is routed for internal+attorney roles, and the AppLayout **Workflow** group already shows "Closing Calendar" → `/calendar`; the page itself is a `ComingSoonPage`. No calendar router/service yet. Google/Microsoft OAuth *popup mechanism* exists (email) and is reusable. **An approved design comp exists.** | `pages/CalendarPage.tsx` (ComingSoonPage); `utils/constants.ts:120` (`CALENDAR: '/calendar'`); `App.tsx:533` (route); `layouts/AppLayout.tsx:298` (Workflow nav item); reusable OAuth in `app/api/v1/integrations.py`; comp `completed_designs/ve-workflow-closing_calendar.html` |
| 8 | **Multi-tenant isolation tests** | **Partially built (backend).** Several isolation/lifecycle tests pass; no UI-driven, tester-runnable verification yet; no full RLS-against-real-Postgres lane confirmed. | `test_task_tenant_isolation.py`, `test_tenant_deletion.py`, `test_platform_archive_and_legal_hold.py`, `test_tenant_invite_base_url.py` |

### 2.2 Reusable assets already in the codebase (do not rebuild)

- **Tenant entity + branding columns**: `tenants` row stores `name, slug, domain,
  logo_url, primary_color, secondary_color, settings_json, domain_status,
  domain_verified_at, owner_user_id, plan, seat_limit, legal_hold, …`
  (`app/schemas/tenant.py`). `settings_json` already carries AI-provider config
  per SYSTEM_DESIGN §2.2.1.
- **Logo upload pipeline**: public `logos` storage bucket (2 MB cap, image MIME
  allowlist) + `POST /onboarding/logo` already uploads and returns a URL
  (`20260506_logos_bucket.sql`, `app/api/v1/onboarding.py`). **Reuse this for
  Branding — do not invent a second upload path.**
- **OAuth popup pattern**: Gmail/Outlook/DocuSign use an authorize-url → popup →
  `postMessage` → token-persist flow (`integrations.py`, `hooks/useIntegrations.ts`,
  `useOAuth.ts`). Google Calendar / Outlook Calendar reuse this **popup mechanism**,
  but scopes are module-level constants today (`GMAIL_SCOPES`, `OUTLOOK_SCOPES`), so
  calendar requires its **own scope set and a separate user consent** (a new
  `google_calendar` / `outlook_calendar` provider), not silent reuse of the existing
  email token.
- **`integrations` table**: per-user provider rows with Fernet-encrypted tokens +
  `metadata_json` JSONB (`20260228_onboarding_integrations.sql`,
  `20260421_integration_metadata.sql`). Calendar connections slot in as new
  `provider` values; no new table needed for the connection itself.
- **Theming engine**: `ThemeContext` already converts hex→HSL and writes
  `--ve-orange`, `--ring`, `--ve-sidebar-bg`, `--radius`, etc. It just needs a
  real data source (the tenant) instead of localStorage.
- **Audit + platform_audit**: `AuditService.log_lifecycle` already records tenant
  mutations; reuse for every new admin/config action.
- **Key dates / milestones**: transaction key dates (EM, Inspection, Appraisal,
  CD, CTC, Closing, Possession) already exist and feed the Active Transactions
  workspace — these are the **source data for the Closing Calendar and calendar
  push**; no new date model is required.

### 2.3 Net gap (what 6.1 actually has to build)

1. **Turn the Branding mockup into a working white-label studio** (logo, colors,
   theme, display name, domain/subdomain) wired to `PATCH /tenants/current` with a
   live preview — and **make the theme load from the tenant on every session and at
   login**. *(Deliverables 2 & 3 — highest priority; it is visible and currently
   fake.)*
2. **Build the Closing Calendar workspace** (visual calendar of closings/key
   dates, per the approved comp) **and** Google/Outlook calendar connect + one-click
   push/sync. *(Deliverable 7 — largest net-new build.)*
3. **Build a generic CRM/integration webhook surface**: outbound event webhooks
   (contact/task create/update) + inbound REST sync endpoints secured by per-tenant
   API keys, with a **self-serve Integrations admin page** (create key, copy webhook
   URL, pick events, "Send test event", view delivery log). *(Deliverables 5 & 6;
   MLO/Title are modeled as named connection profiles on the same surface.)*
4. **Finish and prove RLS isolation in a way a non-engineer can witness in the
   UI**, plus a real-Postgres integration lane. *(Deliverables 1 & 8.)*
5. **Verify/polish the existing tenant-management panel** and connect plan/seat and
   domain-verification controls into it. *(Deliverable 4.)*

---

## 3. Guiding design principles for every task

These apply to **all** sub-deliverables and are acceptance gates, not aspirations.

**P1 — Front-end-testable or it does not exist.** Every backend capability ships
with a UI surface and a documented click-path (Section 11). No deliverable is
"done" if the only way to exercise it is curl/Swagger.

**P2 — One-click over data entry.** Connections = OAuth popups. Branding = color
swatch + file picker + live preview. Calendar push = one button. Webhooks = copy a
URL + "Send test". Never ask a real-estate professional to paste a token, a JSON
blob, or a tenant UUID.

**P3 — No mock data, honest empty states.** Remove the hardcoded "250 of 1,000 AI
credits" and the dead branding inputs. If a number isn't wired, show a real empty
state, not a fake figure (`STYLE_GUIDE §11`, client feedback "No demo data without
real data").

**P4 — Brand-consistent, modern, professional.** Conform to `STYLE_GUIDE.md`:
`ve-*` tokens only, IBM Plex Sans / Lora / Plex Mono hierarchy, `rounded-xl` card
vocabulary, paired status triads, no native `<select>`, no `window.confirm`, 48px
targets. Where a comp exists (Closing Calendar), match it.

**P5 — Never strand the user.** Every CTA resolves to a real route/action. Loading,
empty, error, and permission-denied states are designed up front (the
permission-denied state matters most here — branding/CRM/calendar admin is
Admin-only; non-admins must see a clear read-only or "ask your admin" state, never a
button that 403s).

**P6 — Tenant safety first.** Every new write is tenant-scoped, audit-logged, and
respects the RLS posture. New webhook/calendar tokens are Fernet-encrypted at rest
like existing integration tokens.

---

## 4. Deliverable A — Multi-tenant data isolation (RLS) made provable

**Goal:** Tenant data is provably isolated, and a non-engineer can watch it work
from the UI. **Important framing:** isolation is *already* enforced today at the
**application/repository layer** — every tenant-scoped query filters on
`tenant_id` (e.g. `tasks.tenant_id`, transaction/contact/document scoping). DB-level
RLS is the *defense-in-depth* layer, and it is currently **dormant** because
`settings.use_user_scoped_supabase` defaults to `False`, so all queries run as
service-role (which bypasses RLS) (`app/core/supabase_client.py`,
`app/core/config.py:70`). So the success criterion "isolated data" is met
functionally today; 6.1's RLS task is to **either activate and verify the
DB-enforced layer, or consciously keep it dormant with app-layer enforcement as the
stated guarantee** — and in both cases to make isolation *witnessable in the UI*.

### 4.1 Current state
- Tenant-isolation policies and the precursor fixes (system task-template
  visibility, share-token carveout) are authored and migrated.
- The request-level dispatcher `get_user_supabase_or_service` can run user-scoped
  reads as the `authenticated` Postgres role, **gated by `use_user_scoped_supabase`
  (default `False` → service-role → RLS bypassed)**.
- Backend isolation tests exist and pass against the mock client.

### 4.2 Gaps
- **Activation decision is unresolved.** With the flag off, RLS adds nothing yet.
  The team must decide: turn it on (and complete the service-role carveout sweep for
  cron/webhooks/auth-bootstrap/public-share-token/platform-admin/storage) or keep it
  off with app-layer enforcement as the documented guarantee (*open decision OD-8*).
- **No real-Postgres RLS lane.** Mock-client tests do not execute policies, so they
  prove nothing about actual RLS behavior — only meaningful once the flag is on.
- **No UI-level demonstration** a tester can run (true regardless of the flag).

### 4.3 Work (verification + hardening only — no schema redesign)
**Backend / ops:**
1. Resolve OD-8 (activate RLS vs. keep app-layer enforcement). If activating: audit
   each user-scoped router for the correct client dependency and document the
   service-role carveouts (cron, webhooks, auth bootstrap, public share-token,
   platform-admin, storage proxies) so reviewers can see the boundary; flip the flag
   in a staging deploy first.
2. Stand up an **isolation integration lane** against a local Supabase/Postgres
   (Docker). If RLS is activated, it asserts policy behavior directly (cross-tenant
   read denied; same-tenant allowed; platform-admin exempt; system-default
   `task_templates` readable; public share-token route works via carveout). If RLS
   stays dormant, the same lane asserts the **app-layer** guarantee end-to-end
   (cross-tenant API requests are denied/empty), which is the effective control.
   Either way this satisfies Deliverable 8 with tests that exercise the live control,
   not the mock client.

**Frontend (the UI-provable part — this is what testers use):**
3. No new isolation *mechanism* in the UI, but provide a **repeatable two-account
   test recipe** (Section 11.1) that proves isolation with ordinary screens: log in
   as Brokerage A, note transactions/contacts/documents; log in as Brokerage B in a
   separate session; confirm none of A's data appears in any list, search, document
   center, or deep-link. A forged deep-link to A's transaction id while logged in as
   B must yield a not-found/forbidden state, **not** A's data.

### 4.4 Front-end acceptance (tester-runnable)
- Two brokerages created via normal self-registration show **zero** cross-visibility
  across Active Transactions, Contacts, Documents, Search, Analytics, and Calendar.
- Pasting Brokerage A's transaction URL into Brokerage B's session shows a clean
  "not found / you don't have access" page (designed state), never A's content.

---

## 5. Deliverable B — White-Label Branding Studio (replace the mockup)

**This is the highest-visibility gap and the clearest example of the dead-end
problem.** Today `OrganizationPage` → *Branding* renders inputs that save nothing
and a "Save branding" button with no handler.

### 5.1 Target experience (Organization → Branding)
A single **Branding studio** pane, Admin-editable, with a **live preview** so the
user sees the effect before saving — minimal data entry, maximum confidence.

Layout (conforms to `OrganizationPage` section-rail shell + `STYLE_GUIDE` cards):

```
Organization › Branding
┌─────────────────────────────────────────┬───────────────────────────┐
│ EDIT                                     │ LIVE PREVIEW              │
│ Logo            [ logo ] [Upload] [Remove]│  ┌───────────────────┐    │
│   PNG/SVG, ≤2 MB                          │  │  (sidebar swatch) │    │
│ Brand color     [▮ swatch] [#E26812]      │  │  ▮ Logo  Acme…    │    │
│   (swatch opens picker; hex syncs)        │  │  ● Active nav     │    │
│ Display name    [ Acme Realty AI       ]  │  │  [ Primary CTA ]  │    │
│ Workspace URL   acme .velvet-elves.com    │  │  status pills…    │    │
│   [Use a custom domain ▸]  (advanced)     │  └───────────────────┘    │
│                                           │  Reflects unsaved edits   │
│ [ Reset to default ]      [ Save branding ]│                          │
└─────────────────────────────────────────┴───────────────────────────┘
```

### 5.2 Backend (mostly exists — thin additions)
- **Reuse** `PATCH /api/v1/tenants/current` (Admin-only) for `logo_url`,
  `primary_color`, `secondary_color`, and a `display_name` (store under
  `settings_json.branding.display_name` to avoid a migration, or add a column if
  the team prefers a first-class field — *open decision OD-1*).
- **Reuse** the logo upload bucket. Expose a tenant-logo upload endpoint
  (`POST /api/v1/tenants/current/logo`) modeled on `POST /onboarding/logo` so logo
  changes outside onboarding work; it returns the public URL the PATCH then
  persists. (If reuse of the onboarding endpoint post-onboarding is acceptable, no
  new endpoint is needed — *open decision OD-2*.)
- **Custom domain/subdomain**: surface existing `domain` / `domain_status` /
  `domain_verified_at`. The **subdomain** (`slug.APP_BASE_DOMAIN`) needs no DNS and
  is the default white-label URL; the **custom domain** path shows DNS records to
  add and a "Verify" action that flips `domain_status`. Full DNS challenge/cert
  issuance is an ops runbook (*open decision OD-3*); the UI must clearly show
  `unverified / pending / verified / failed` and only use the custom domain once
  `verified`.

### 5.3 Frontend
1. **Rebuild the Branding pane** in `OrganizationPage.tsx` against real state:
   load `GET /tenants/current`; bind logo/color/display-name/domain to controlled
   inputs; wire **Save** to `PATCH /tenants/current` (+ logo upload first if a new
   file was chosen); toast success; refetch.
2. **Color picker**: a `ve-*`-styled swatch + hex input that stay in sync; validate
   hex on blur (`STYLE_GUIDE §9.2`). No raw `<input type=color>` styling that breaks
   brand — wrap it.
3. **Live preview** component renders a miniature sidebar + nav item + primary
   button + status pills using the *draft* values via the existing
   `ThemeContext.applyThemeToDOM` math (scoped to the preview, not the whole app,
   until Save).
4. **Permission state**: non-Admins see the pane **read-only** with "Only an Admin
   can change branding" (mirror the existing Company-name pattern already in the
   file) — never a 403 button.
5. **Remove the fake AI-credits block and dead toggles** in the AI pane, or wire
   them to real settings; do not ship hardcoded "250 of 1,000" (P3). (If AI-credit
   metering isn't in 6.1 scope, replace with an honest "Usage metering coming with
   billing" empty state — *open decision OD-4*.)

### 5.4 Convenience features (P2)
- Logo **drag-and-drop** onto the logo tile, not just a file dialog.
- "**Reset to default**" returns to Velvet Elves brand in one click (clears
  overrides).
- Preview updates **instantly** as colors change; Save persists.

### 5.5 Front-end acceptance (tester-runnable)
- As an Admin: upload a logo, pick a new brand color, set a display name, Save →
  page reloads and the **real sidebar/topbar/buttons** reflect the new brand; logging
  out and back in keeps it (proves persistence, not localStorage).
- As a non-Admin in the same brokerage: Branding pane is visibly read-only.
- No control on the pane is inert; every button does something.

---

## 6. Deliverable C — Apply branding across all surfaces

**Goal:** The saved brand shows up everywhere the requirement names: login, every
role dashboard, email templates, documents.

### 6.1 Wire the theme to the tenant (not localStorage)
- On authenticated load, fetch `GET /tenants/current` and call `setTheme(...)` from
  the tenant's `logo_url`/`primary_color`/`secondary_color`/display-name. The
  localStorage cache may remain as a fast-paint hint, but **the tenant record is the
  source of truth** and overwrites it on load. (`ThemeContext` already applies the
  vars; it just needs this real feed — see `contexts/ThemeContext.tsx`,
  `hooks/useTenant.ts`.)
- The shared `AppLayout` sidebar/topbar logo + the customer shells (FSBO, Client)
  read `useTheme().logoUrl` / `logoText` so all role dashboards inherit the brand
  automatically.

### 6.2 Login / pre-auth branding
- The login screen has no JWT, so brand must resolve from the **host**: if the
  request arrives on `slug.APP_BASE_DOMAIN` or a verified custom domain, a small
  **public, unauthenticated** endpoint (`GET /api/v1/public/tenant-branding?host=…`
  or `/by-domain/{host}`) returns just `{logo_url, primary_color, display_name}`
  (no PII). The login page applies it before render. On the bare platform domain it
  shows Velvet Elves default. (*Open decision OD-5: ship host-based login branding in
  6.1, or defer to the domain runbook and brand login only post-auth.*)

### 6.3 Email + documents
- **Email**: invite email is already tenant-branded (`branded_invite_email.py`).
  Extend the same brand context (logo, color, display-name, reply-to sender) to the
  other transactional emails in scope (notifications/reminders) via the existing
  email service templates. Verify per-tenant sender identity.
- **Documents**: generated/printed artifacts (closing checklists, transaction
  exports/PDFs) stamp the tenant logo + display name in the header. These already
  pull from profile/tenant data; the change is to source the logo/brand from the
  tenant brand fields rather than any hardcoded VE mark.

### 6.4 Front-end acceptance
- Brokerage A and Brokerage B, each with distinct logo+color, render their **own**
  brand across: login (on their subdomain), Solo-Agent/Team/Attorney/FSBO
  dashboards, the invite email, and a generated closing checklist/export — with **no
  cross-bleed**.

---

## 7. Deliverable D — Tenant management admin panel (verify + complete)

**Goal:** A platform operator runs the tenant fleet entirely from the UI; a tenant
Admin manages their own org from Organization settings.

### 7.1 Current state (substantially built)
- `/platform/tenants` (list, filters active/suspended/legal-hold) and
  `/platform/tenants/{id}` (detail) exist with suspend/reactivate, legal-hold
  set/clear, archive view, behind `PlatformAdminGuard`.

### 7.2 Work (gap-closing + polish, no teardown)
1. **Audit the panel against the data contract**: confirm columns (owner, member
   count, plan, seat usage, deletion-scheduled date, legal-hold) render from real
   fields already on `TenantResponse` (`plan`, `seat_limit`, `staff_seat_count`,
   `deletion_scheduled_at`, `legal_hold`).
2. **Plan / seat controls**: surface platform-admin editing of `plan`, `seat_limit`,
   `trial_ends_at` on the tenant detail page. **These are readable on
   `TenantResponse` but the write path does not exist yet** — `TenantUpdateRequest`
   (used by `PUT /tenants/{id}`) currently accepts only name/slug/domain/logo/colors/
   settings_json/is_active, so a **small backend addition** is required: extend
   `TenantUpdateRequest` (and the platform-admin `PUT` handler) to accept `plan`,
   `seat_limit`, `trial_ends_at`, platform-admin-gated and audit-logged. Tenant-side:
   show "4 / 5 staff seats" in the team/invite UI (the count already ships on
   `GET /tenants/current` via `staff_seat_count`).
3. **Domain verification surfacing**: show `domain_status` and a "Verify" affordance
   on tenant detail (pairs with §5.2).
4. **Style-guide pass**: ensure the panel uses the standard page-shell + breadcrumb
   header and the one-card vocabulary (`STYLE_GUIDE §15–16`); replace any stray
   default-palette badges with `ve-*` triads.

### 7.3 Front-end acceptance
- A platform admin can: list/filter tenants, open one, suspend/reactivate, set/clear
  a legal hold, change plan/seat limit, and see archive/audit entries — all with
  buttons that work and confirmation dialogs (no `window.confirm`).
- A non-platform user navigating to `/platform/*` gets a clean not-found (guard
  already exists) — verify it doesn't leak existence.

---

## 8. Deliverable E — Calendar integration (Google Calendar + Outlook) & Closing Calendar UI

**Two halves:** (1) a **Closing Calendar workspace** — the visual calendar testers
have been promised (placeholder today) — and (2) **two-way sync** with the user's
Google/Outlook calendar. There is an **approved comp**:
`completed_designs/ve-workflow-closing_calendar.html`; reproduce it faithfully (P4).

### 8.1 Closing Calendar workspace (frontend-first; works with zero external connect)
- **The route, the Workflow nav item ("Closing Calendar" → `ROUTES.CALENDAR` =
  `/calendar`), and the page shell already exist** (`App.tsx:533`,
  `AppLayout.tsx:298`); the only gap is content. Replace the `ComingSoonPage` body of
  `CalendarPage.tsx` with a real month/week view of the user's transactions' **key
  dates** (EM, Inspection, Appraisal, CD Delivered, Cleared-to-Close, Closing,
  Possession) and closings, sourced from existing transaction/key-date data — **no
  external calendar required to see value**.
- Each event: color by type/urgency (status triads), click → deep-link to the
  transaction in the Active Transactions workspace (never a dead cell). Filters:
  my deals / team (for Team Lead), date-type, status.
- The page is gated to internal + attorney roles today (`INTERNAL_AND_ATTORNEY`);
  keep that gating. Honest empty state when no upcoming dates (`STYLE_GUIDE §11`).
  Use lucide icons inside the page per `STYLE_GUIDE §7` (the sidebar's emoji glyph is
  pre-existing and out of scope here).

### 8.2 Connect Google/Outlook calendar (reuse existing OAuth)
- Add **Calendar** rows to Organization → (a new) *Calendar* or extend *Email/
  Integrations* with provider rows for "Google Calendar" and "Outlook Calendar".
  Connect = the **same one-click OAuth popup** already used for Gmail/Outlook, with
  calendar scopes added; tokens persist in `integrations` as new providers
  (`google_calendar`, `outlook_calendar`) — no new table (§2.2 reuse).
- Backend: a new `calendar` service/router with provider adapters that
  create/update/delete events (Google Calendar API / Microsoft Graph), mirroring the
  email provider abstraction. Schedule appointments, send reminders (event reminder
  overrides), manage events — exactly the Req §7.1 verbs.

### 8.3 Push & sync (one-click convenience, P2)
- From the Closing Calendar and from a transaction: "**Add closing & key dates to my
  calendar**" — one button creates/updates events in the connected calendar; store
  the external event ids in `metadata_json`/a light `calendar_event_links` map so
  re-push **updates** rather than duplicates, and date changes in VE propagate.
- Reminders: default reminder offsets (e.g., day-before) configurable per user.
- Two-way is bounded for MVP: VE→calendar push is authoritative; inbound is limited
  to honoring user deletes/declines (don't resurrect a deleted event) unless a
  fuller two-way is approved (*open decision OD-6 — scope of inbound sync*).

### 8.4 Front-end acceptance (tester-runnable)
- Open Closing Calendar with no calendar connected → see real closings/key dates
  from your deals; click an event → land on that transaction.
- Connect Google (or Outlook) in one popup → "Add to my calendar" → the closing
  appears in the real Google/Outlook calendar; change the closing date in VE →
  re-push updates the same event (no duplicate).

---

## 9. Deliverable F & G — CRM webhooks + MLO/Title hooks (one self-serve Integrations surface)

Requirement §7.3 asks for *generic, open* REST/webhook endpoints with two-way
contact/task sync — **no specific CRM**. §7.5/§7.6 ask for MLO and title-company
**hooks** (file/status exchange, loan status). We satisfy all three with **one
generic, brandless integration surface** plus named connection "profiles," so the
client can wire Follow Up Boss, a title company, or an MLO portal later without new
code. This is architecture-and-hooks scope, kept MVP-minimal (per milestones.txt
risk note #6).

### 9.1 Backend
1. **Per-tenant API keys** (`tenant_api_keys`: id, tenant_id, label, hashed key,
   scopes, created_by, last_used_at, revoked_at). Keys authenticate inbound sync
   calls; shown once on creation. Fernet/hash at rest like other secrets.
2. **Outbound webhooks** (`tenant_webhooks`: id, tenant_id, target_url, secret,
   event types, is_active, created_by; `webhook_deliveries`: attempt log with
   status/response for the UI). A dispatcher fires signed (HMAC) JSON on domain
   events: `contact.created/updated`, `task.created/updated/completed`,
   (extensible: `document.status_changed`, `transaction.milestone_reached`). Retry
   with backoff; every attempt logged for UI visibility.
3. **Inbound generic sync** (`POST /api/v1/integrations/crm/contacts`,
   `/tasks`) authenticated by tenant API key, tenant-scoped, validated, audit-logged
   — the "two-way" inbound half. Upsert semantics keyed on an external id stored on
   the contact/task.
4. **MLO / Title profiles**: model as a typed connection profile
   (`integration_connections`: tenant_id, kind ∈ {crm, mlo, title}, label, config
   JSON, status) so MLO "share loan status/documents" and Title "exchange files/
   status" reuse the same webhook + inbound-sync plumbing, just with a named profile
   and (for MLO/Title) a document-share scope. MVP delivers the **hook surface**; a
   specific vendor integration is post-MVP.

### 9.2 Frontend — Admin → Integrations (the part testers click)
A new Admin "Integrations / Developers" page (Admin-only), style-guide-conformant:

- **API keys** card: "Create key" → modal (label, scopes) → key shown once with a
  copy button + "store this now" notice; table of keys with last-used + Revoke.
- **Webhooks** card: "Add webhook" → modal (paste target URL, multi-select event
  types via `ve-*` `Select`, not native). Each webhook row: status, **"Send test
  event"** button (fires a sample payload so the user *sees* it work), and a
  **Deliveries** drawer showing recent attempts with status codes — so a non-engineer
  can confirm "it's connected" without reading logs.
- **Connections** card: "Connect a CRM / MLO / Title company" → choose kind, label,
  paste their endpoint/credentials → creates an `integration_connections` profile.
  Clear copy that MVP provides the open hook; named-vendor automations come later.
- **Copy-paste minimalism (P2)**: the inbound base URL and the tenant's webhook
  signing secret are one-click copyable. No JSON authoring required to get a working
  contact/task sync.

### 9.3 Front-end acceptance (tester-runnable)
- Admin creates an API key (copies it), adds a webhook to a test URL
  (e.g., a webhook.site link the tester pastes), selects "contact.created", clicks
  **Send test event** → sees a 200 in the Deliveries drawer **and** the payload at
  the test URL.
- Creating a contact in VE fires a real `contact.created` delivery (visible in the
  drawer).
- Posting a sample contact to the inbound URL with the API key creates a tenant-
  scoped contact that then appears in the Contacts page. (For non-engineer testers,
  ship a tiny in-product "Test inbound sync" helper button that performs this call
  for them, so they never touch curl — *recommended, OD-7*.)

---

## 10. Deliverable H — Integration tests for multi-tenant isolation

**Goal:** Automated proof + a tester-runnable proof.

- **Automated:** the real-Postgres isolation lane from §4.3.2 (asserting the live
  control — RLS policies if OD-8 activates them, else app-layer enforcement) plus
  extend isolation tests to the **new** surfaces built here — webhooks, API keys,
  calendar links, and branding all must be tenant-scoped (a key/webhook/calendar
  token from Brokerage A is invisible and unusable in Brokerage B). Add
  cross-tenant-denied tests for each new table/endpoint. These new-surface tests hold
  regardless of the RLS flag, because the surfaces are tenant-scoped in app code.
- **Tester-runnable:** the two-account recipe in §4.4 plus: Brokerage A's API key
  cannot write into Brokerage B; A's branding never appears for B; A's calendar
  connection never pushes B's deals.

---

## 11. Front-end testing guide for non-developer testers (click-paths)

Every script below is **mouse-only, in-product, no API client, no fake data**. These
double as the acceptance scripts for the milestone demo.

### 11.1 Tenant isolation (Deliverables 1, 8)
1. Register Brokerage A (self-serve), create 2 transactions + 2 contacts + upload 1
   document.
2. In a separate browser/profile, register Brokerage B; create different data.
3. As B, open Active Transactions, Contacts, Documents, Search, Calendar →
   **confirm none of A's items appear.**
4. As B, paste A's transaction URL → **confirm a clean not-found/forbidden page.**

### 11.2 White-label branding (Deliverables 2, 3)
1. As A's Admin → Organization → Branding: drag in a logo, pick a brand color, set
   display name → **Save**.
2. Confirm the sidebar/topbar/buttons adopt the brand; log out/in → still branded.
3. Open A's login on its subdomain → branded login (if OD-5 in scope).
4. Send a teammate invite → branded email. Generate a closing checklist → branded
   header. Repeat with Brokerage B's different brand → **no cross-bleed.**
5. As a non-Admin → Branding is read-only (no dead/403 buttons).

### 11.3 Tenant management panel (Deliverable 4)
1. As platform admin → /platform/tenants: filter, open a tenant, suspend → confirm
   that tenant's users are blocked; reactivate. Set a legal hold → confirm
   delete/schedule is blocked. Change plan/seat limit → reflected on the tenant.

### 11.4 Closing Calendar + calendar sync (Deliverable 7)
1. Open Closing Calendar → real closings/key dates show; click one → land on the
   transaction.
2. Connect Google/Outlook (one popup). Click "Add to my calendar" → event appears in
   the real external calendar. Change the closing date in VE, re-push → same event
   updates (no duplicate).

### 11.5 CRM / integrations (Deliverables 5, 6)
1. Admin → Integrations: create API key (copy), add webhook to a pasted test URL,
   pick "contact.created", **Send test event** → 200 in Deliveries + payload at the
   URL.
2. Create a contact in VE → see a live `contact.created` delivery.
3. Use the in-product "Test inbound sync" button → a new contact appears in
   Contacts.

---

## 12. Navigation & information architecture (where these live)

- **Closing Calendar** → Workflow group (`ROUTES.CALENDAR` = `/calendar`), alongside
  My Task Queue / All Documents — **already present in the sidebar and routed**; only
  the page content changes.
- **Branding / Company / Email / E-sign / Calendar connect / AI** → Organization
  (existing section-rail page); add a **Calendar** connect row and keep
  Integrations(connect) here for end-users.
- **Integrations / Developers (API keys, webhooks, CRM/MLO/Title)** → Admin group
  (Admin-only), as a sibling of Audit Logs / AI Governance (a developer/integration
  surface, not an end-user one).
- **Tenant fleet** → `/platform/*` (platform-admin only, guarded).

Every new nav entry is role-gated so non-eligible roles never see a link that leads
to a 403.

---

## 13. Implementation sequencing & effort

Ordered by visible value, risk, and dependency. Sizes: S ≈ ≤1d, M ≈ 2–4d, L ≈ 1wk+.

| Order | Work | Deliverable | Size | Rationale |
|---|---|---|---|---|
| 1 | Wire ThemeContext to tenant record (load on session) | C | S | Unblocks every branding test; small, foundational |
| 2 | Branding Studio: real save + logo upload + live preview; remove AI-credit mock | B | M | Highest-visibility dead-end; fixes the mockup |
| 3 | Brand application: dashboards/email/documents + login host-branding (OD-5) | C | M | Completes the white-label promise |
| 4 | Tenant panel: verify + plan/seat/domain surfacing + style pass | D | S/M | Mostly polish on built code |
| 5 | Closing Calendar workspace (real key dates, comp-faithful) | E | M/L | Big tester-facing win; no external dep |
| 6 | Calendar connect + push/sync (reuse OAuth) | E | M | Builds on #5 |
| 7 | CRM/integration surface: keys, webhooks, deliveries, inbound sync | F/G | L | Net-new backend + admin UI |
| 8 | MLO/Title connection profiles on the same surface | G | S | Reuses #7 plumbing |
| 9 | Isolation verification (OD-8 decision) + real-Postgres integration lane + new-surface isolation tests | A/H | M | Confirms the safety story end-to-end against the live control |

**Critical path:** 1 → 2 → 3 (white-label) can ship and demo independently of the
calendar/CRM tracks, which can proceed in parallel once the team has capacity.

---

## 14. Risks & open decisions (resolve before/early in build)

- **OD-1** Display name: `settings_json.branding.display_name` (no migration) vs a
  first-class `tenants.display_name` column. *Recommend* `settings_json` for MVP.
- **OD-2** Tenant logo upload: reuse `POST /onboarding/logo` post-onboarding vs add
  `POST /tenants/current/logo`. *Recommend* the explicit tenant endpoint for clarity.
- **OD-3** Custom-domain DNS/cert workflow: full automated verification vs subdomain-
  only for 6.1 with a manual verify + ops runbook for custom domains. *Recommend*
  subdomain default + manual custom-domain verify in 6.1.
- **OD-4** AI-credit metering: wire real usage vs replace the mock with an honest
  "coming with billing" empty state. *Recommend* the empty state (billing is M5.2/
  post-MVP), never the hardcoded figure.
- **OD-5** Login-screen host-based branding in 6.1 vs defer with the domain runbook.
  *Recommend* ship subdomain-based login branding; custom-domain login follows DNS.
- **OD-6** Calendar inbound sync depth: push-authoritative + honor deletes
  (recommended MVP) vs full bi-directional. Full two-way risks conflict-resolution
  scope creep.
- **OD-7** In-product "Test inbound sync" helper so non-engineer testers verify CRM
  inbound without curl. *Recommend* yes — it's the difference between a testable and
  an untestable deliverable for this audience.
- **OD-8** RLS activation: flip `use_user_scoped_supabase` on (with the full
  service-role carveout sweep + staging verification) vs. keep DB-RLS dormant and
  rely on the existing app-layer tenant filtering as the documented isolation
  guarantee. *Recommend* keeping app-layer enforcement as the 6.1 guarantee and
  treating full RLS activation as a hardening pass, given the carveout sweep is
  multi-day and app-layer isolation already passes the success criterion — but make
  the choice explicit and test whichever control is the live one.
- **Cron primitive**: calendar reminder pushes and webhook retries add scheduled
  work to the same host as existing crons (escalations, retention purge, tenant
  deletion). Confirm the scheduler choice can take more jobs.
- **Scope guard**: CRM/MLO/Title are **hooks**, not full vendor integrations
  (milestones.txt risk #6). Keep named-vendor automations post-MVP.

---

## 15. Definition of Done

Milestone 6.1 is complete when **all** of the following are true and demonstrated
**through the UI by a non-engineer** using Section 11:

1. Two self-registered brokerages have fully isolated data across every screen,
   proven by the two-account recipe and by automated isolation tests against a real
   Postgres that exercise the **live** control (RLS policies if OD-8 activates them,
   otherwise the app-layer tenant filtering); the new 6.1 surfaces (branding,
   webhooks, API keys, calendar links) are each tenant-scoped with cross-tenant-denied
   tests.
2. An Admin sets logo + brand color + display name (+ workspace subdomain) in the
   Branding studio, saves, and the **real** app + login + invite email + generated
   documents reflect the brand and persist across sessions — with no mock data and no
   dead controls anywhere on the Organization page.
3. Branding renders correctly and independently for two different brokerages, with no
   cross-bleed, on login and on Solo-Agent/Team/Attorney/FSBO dashboards.
4. A platform admin runs the tenant fleet (list/filter/suspend/reactivate/legal-
   hold/plan-seat/domain-verify/archive) entirely from `/platform/*`.
5. The Closing Calendar shows real closings/key dates (comp-faithful), deep-links to
   transactions, and — once Google/Outlook is connected in one click — pushes and
   updates closings in the external calendar without duplicates.
6. An Admin creates an API key and a webhook, fires a visible test delivery, sees a
   real `contact.created` delivery, and completes an inbound contact sync — all from
   the Integrations admin page; MLO/Title connection profiles exist on the same
   surface.
7. Every new surface conforms to `STYLE_GUIDE.md`, every CTA resolves to a real
   action, and every non-eligible role sees a clear read-only/permission state rather
   than a button that errors.

---

## 16. Source references (reviewed for this plan)

- Requirements: `requirements.txt` §7.1 (calendar), §7.3 (CRM), §7.5/§7.6
  (Title/MLO), §9.5 (white-label), §10.2/§10.3 (security/audit), §10.5 (admin/tenant
  settings).
- Architecture: `SYSTEM_DESIGN.md` §2.2.1 (tenants/branding/AI-provider config),
  §2.2.15 (integrations), §2.4 (RLS), white-label color propagation, route map.
- Milestones: `milestones.txt` Milestone 6.1; risk notes (scope guard, crons).
- Multi-tenancy backend: `MULTI_TENANCY_IMPLEMENTATION_PLAN.md` (the source of the
  RLS/seat/lifecycle work now largely shipped).
- Style: `STYLE_GUIDE.md` (tokens, type, cards, anti-patterns, page shells,
  dashboards).
- Code (current state): `app/api/v1/{tenants,platform_tenants,integrations,
  onboarding}.py`, `app/schemas/tenant.py`, `app/services/branded_invite_email.py`,
  `app/core/supabase_client.py`, `supabase/migrations/2026051*` (RLS, lifecycle,
  seats, archive), `20260506_logos_bucket.sql`, `20260228_onboarding_integrations.sql`;
  `src/pages/organization/OrganizationPage.tsx`, `src/pages/CalendarPage.tsx`,
  `src/pages/platform/*`, `src/contexts/ThemeContext.tsx`,
  `src/hooks/{useTenant,useIntegrations,usePlatformTenants}.ts`.
- Approved comp: `completed_designs/ve-workflow-closing_calendar.html`.
- Standing client feedback honored: "No demo data without real data," design-comp
  fidelity, UI visual-verification method.

*End of Milestone 6.1 implementation plan.*
