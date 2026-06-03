# Milestone 6.2 — Advertising Hooks & Consumer Site: Implementation Plan

| | |
| --- | --- |
| **Milestone** | 6.2 — Advertising Hooks & Consumer Site (Phase 6, Week 21) |
| **Status** | 🟡 **PLANNED — not started** · drafted 2026-06-02 · **rev 1.1 (2026-06-02): the consumer-facing advertising site is re-scoped as a separate, standalone frontend project — its own GitHub repo + its own server/domain — per client direction (see §8, OD-10). OD-10 backend sub-question resolved 2026-06-02: standalone frontend, SHARED backend (no second backend). · **rev 1.2 (2026-06-02): post-review code re-verification — corrected the Stripe webhook path to `/api/v1/webhooks/stripe` (the `payments` router has no prefix); added a "create a package first" prerequisite to the consumer test loop (§13.2) so testers never hit an empty landing page; hardened the post-pay creative upload against the background-webhook race (§9.2); added an explicit slot↔format validation rule (§5.1). All other grounding claims re-verified against current source and confirmed accurate.** · **rev 1.3 (2026-06-03): IMPLEMENTED. OD-10 REVERSED — the consumer storefront is **not** a separate standalone project; it ships as **public routes in the main app** (`/advertise`, `/advertise/checkout/:id`, `/advertise/complete`), reusing the public invoice-pay precedent. Rationale: the original standalone decision was premised on it being a "marketing site"; it is actually a thin public Stripe-redirect ad-purchase flow, so a second repo/host/DNS/CORS added cost without benefit. Backend was already shared (so no data-plane change); Stripe success/cancel now use `frontend_url` + a token carried through the round-trip. A polished product **marketing** site (velvetelves.com) remains separate, out-of-scope, and not yet built. §8 (standalone-project sections) is superseded by this note.** |
| **Calendar** | Week 21 (2026-07-27 → 2026-08-02), immediately after M6.1 White-Label & Multi-Tenant |
| **Authoritative sources** | `milestones.txt` §6.2 · `requirements.txt` §11 (Advertising & Monetization), §2.5/§7.7 (Stripe), §1.2h (Vendor role), §9.5 (white-label), §10.5 (admin UI), §10.2/§10.3 (security/audit) · `SYSTEM_DESIGN.md` §1.4 (multi-tenant), §2.4 (RLS), §3.3 (permission matrix), §2341 (advertising roadmap line) · `STYLE_GUIDE.md` (all sections) · `MILESTONE_5_2_IMPLEMENTATION_PLAN.md` §2.3 ("Ad-purchase Stripe checkout… reuse this module's Stripe client + webhook handler") · `MILESTONE_6_1_IMPLEMENTATION_PLAN.md` (the grounding discipline + tester click-path format this plan mirrors) |
| **Approved HTML comps** | **None.** No advertising or consumer-site comp exists in `completed_designs/`. Every surface is net-new and must be designed in-flight against `STYLE_GUIDE.md` and the visual-consistency anchors below. This is called out as a risk (R-7) and an open decision (OD-9: do we want a client design pass before build?). |
| **Visual-consistency anchors** | `AdminIntegrationsPage.tsx` (card-per-capability admin surface), `OrganizationPage.tsx` (Branding studio — upload + live preview), `PublicInvoicePayPage.tsx` / `PublicInvoicePaymentCompletePage.tsx` (public, unauthenticated Stripe redirect + status polling), `PaymentsListPage.tsx` (tracking table), `NewTransactionWizard.tsx` (wizard right panel where an in-app slot lives), `TaskQueuePage.tsx` (task screen where an in-app slot lives). |
| **External dependencies** | Stripe account + keys **already provisioned for M5.2** — 6.2 adds **no new external integration**, only a new product line on the existing Stripe client. A new public storage bucket (`ad-creatives`) is created the same way as the existing `logos` bucket. **New for rev 1.1:** the consumer site is a **separate standalone frontend** in its **own GitHub repo**, deployed to its **own server/host + domain** (e.g. `advertise.velvetelves.com`) — so this milestone now also requires a new repo, a new CI/CD pipeline + server, a DNS record + TLS cert, and a backend **CORS allowlist** entry for the new origin. The standalone site consumes the **existing** backend's public ad API (no second backend — OD-10). |

---

## 0. Why this plan exists (read this first)

Per repeated client feedback, prior plans broke during front-end testing because
they were written **before** a full reading of (a) the requirements and
system-design documents and (b) **the code that is actually deployed today**. The
result was plans that assumed work was missing when it was shipped, or assumed work
was shipped when it was only a dormant stub — and testers (who are **real-estate
professionals, not engineers**) then hit dead-end buttons, empty placeholders, and
flows that broke mid-stream instead of completing.

This plan is written **after** a line-by-line review of the 6.2 surface area.
Section 2 is a **grounded current-state inventory with file citations**, so every
task below is anchored to what truly exists. The governing rule, restated from the
6.1 plan and from standing client feedback, is:

> **If a real-estate professional cannot exercise it end-to-end with a mouse,
> through the product UI — with no engineer, no API client, and no fake data — it is
> not done.**

Five standing constraints from prior client feedback are hard requirements here:

1. **No mock/demo ads on real surfaces** (`[[no-demo-data-without-real-data]]`).
   Every ad a tester sees must be a **real creative they (or an advertiser) actually
   uploaded**, scheduled, and approved. An empty slot **collapses to nothing** — it
   never renders a "Your ad here" placeholder, a fake banner, or a broken box.
2. **Professional-tool aesthetic, not a billboard.** Velvet Elves is a calm,
   premium, AI-assisted workspace (`STYLE_GUIDE §1`; `[[ve-design-comp-fidelity]]`).
   Third-party ads inside a paid professional tool are intrusive by default, so
   **workspace ad display is OFF by default per tenant** and ads are visually
   restrained and unmistakably labeled.
3. **Ads must be clearly delineated from system content AND from AI content.**
   `milestones.txt` §6.2 requires clear delineation; `STYLE_GUIDE §10` reserves the
   champagne (`ve-orange*`) accent for **AI-touched** surfaces. Ads therefore **must
   not** borrow the AI accent or imitate the AI next-step banner / AI Suggestions
   panel. Every ad carries an explicit `SPONSORED` label.
4. **Minimum data entry / one-click convenience.** Creating a house ad = pick a
   slot + upload an image + pick dates. Buying an ad on the consumer site = pick a
   package + pay (Stripe hosted Checkout — no card fields in our app). Approving a
   creative = one click.
5. **Reuse, don't reinvent.** The Stripe client, the public-checkout pattern, the
   webhook dispatcher, the logo-upload/storage pipeline, the admin page shell, and
   the existing `advertising_hooks` table already exist. 6.2 composes them.

**Scope guard (`milestones.txt` Risk #6):** the advertising module and consumer
site are explicitly scoped **minimally for MVP** — "architecture hooks" + "basic"
management + a "basic" consumer site. This plan delivers a complete, testable loop
without over-building a full ad-exchange. Everything beyond that is documented as a
future-expansion hook (Deliverable G, §11).

---

## 1. What Milestone 6.2 must deliver (from `milestones.txt`)

| # | Deliverable (verbatim) | Requirement anchor |
| --- | --- | --- |
| 1 | Advertising module architecture hooks: modular ad slots in wizard and task screens; ad format support (banners, text links, sponsored suggestions); responsive ad rendering | Req §11.1; SYSTEM_DESIGN §2341 |
| 2 | Basic ad management API: package creation/pricing; creative asset upload/approval; scheduling (where/when ads appear); impression/click tracking | Req §11.1; §10.5 (admin UI) |
| 3 | Basic consumer-facing advertising site: landing page; Stripe integration for ad purchases | Req §11.2; §2.5/§7.7 (Stripe) |
| 4 | Clearly delineate ads from system content | Req §11.1 ("Clearly delineated from system content"); STYLE_GUIDE §10/§13 |
| 5 | Ad billing connected to Stripe payment module | Req §11.1; M5.2 §2.3 (downstream consumer) |
| 6 | Document advertising API for future expansion | Req §11.1; §13.5 (modular, documented APIs) |

**Success criteria (`milestones.txt`):** *"Ad slot architecture in place, basic ad
management working, consumer site live with Stripe."*

---

## 2. Grounded current-state inventory

Reviewed: `velvet-elves-backend/app` (models, routers, services, schemas,
migrations) and `velvet-elves-frontend/src` (pages, components, routing, constants).
Every citation below is to a file that exists today.

### 2.1 Deliverable-by-deliverable reality

| # | Deliverable | Real status today | Evidence |
| --- | --- | --- | --- |
| 1 | **Ad slots in wizard/task screens** | **Greenfield in the UI.** No ad component, no slot, no rendering anywhere in the frontend. The wizard and task screens exist and are stable insertion points. | No `ads`/`advert`/`sponsor` component in `src/components`; `components/wizard/NewTransactionWizard.tsx`, `pages/tasks/TaskQueuePage.tsx` exist as the host surfaces. |
| 2 | **Ad management API** | **Dormant data only.** A `advertising_hooks` **table** and a bare **`AdvertisingHook` dataclass** exist, but there is **no router, no service, no repository, no schema** — nothing reads or writes the table. | Table: `supabase/migrations/202603110000_new_vendors_and_ad_hooks.sql` (cols: `slot_name, slot_location, ad_format, title, content_url, click_url, creative_asset, is_active, start_date, end_date, impressions, clicks, metadata_json, tenant_id`). Model: `app/models/advertising_hook.py`; registered in `app/models/__init__.py`. **No** `advertising`/`ad_*` router in `app/api/v1`, **no** service in `app/services`, **no** schema in `app/schemas`, **no** repository. |
| 3 | **Consumer-facing site + Stripe** | **Pattern fully exists; the ad site itself does not.** The public, unauthenticated, signed-token → Stripe-Checkout → status-poll flow is shipped for invoices and is the exact template for a consumer ad-purchase page. | `app/api/v1/public_payments.py` (prefix `/public/pay`); `src/pages/public/PublicInvoicePayPage.tsx`, `PublicInvoicePaymentCompletePage.tsx`; public routes `App.tsx:254-258`. No `/advertise` route, no consumer landing page. |
| 4 | **Ad/system delineation** | **Not started**, but the rule set exists: `STYLE_GUIDE §10` (champagne = AI only) and §13 anti-patterns govern how an ad must look distinct. | `STYLE_GUIDE.md §10`, §13. |
| 5 | **Ad billing via Stripe** | **Stripe module shipped and explicitly earmarked for reuse by 6.2.** The Stripe client, the webhook receiver, and the idempotent event dispatcher all exist. | `app/services/stripe_client.py` (`create_checkout_session`, `verify_webhook_signature`, …); webhook `app/api/v1/payments.py:267` (`POST /api/v1/webhooks/stripe` — the `payments` router carries **no** path prefix, so the receiver mounts at `/api/v1/webhooks/stripe`, *not* under `/payments`; verified in `router.py` + `payments.py:267`) → `app/services/payment_event_dispatcher.py` (`dispatch()` switches on `event.type`, reads `metadata.invoice_id`/`tenant_id`). M5.2 plan §2.3 names "Ad-purchase Stripe checkout" as a downstream consumer of this module. |
| 6 | **Advertising API documentation** | **Not started.** No `docs/ADVERTISING_*.md`. | `velvet-elves-backend/docs/` has no advertising doc. |

### 2.2 Reusable assets already in the codebase (do **not** rebuild)

- **`advertising_hooks` table** — already created, indexed (`idx_ad_hooks_tenant`,
  `_slot`, `_active`), RLS-enabled (service-role + tenant-isolation policy in
  `20260511094000_rls_tenant_isolation.sql`), and already **cascade-deleted on tenant
  deletion** (`app/services/tenant_deletion_service.py:61` lists `"advertising_hooks"`).
  We **extend** this table (it maps almost 1:1 to a "creative placed in a slot with
  counters"); we do not create a parallel one.
- **Stripe client** (`app/services/stripe_client.py`) — `create_checkout_session`
  takes `line_items` (price_data), `success_url`, `cancel_url`, `metadata`,
  `idempotency_key`; runs in safe **stub mode** when no key is set (tests/CI). Reuse
  verbatim for ad-package checkout.
- **Stripe webhook + dispatcher** (`payments.py:267`,
  `payment_event_dispatcher.py`) — already idempotent (unique-index gate on
  `webhook_events`), already returns 200 fast then works in `BackgroundTasks`, already
  branches on `metadata`. Ad orders ride the **same endpoint** with new metadata; we
  add a dispatcher branch, **no new webhook endpoint**.
- **Public-checkout pattern** (`public_payments.py`, `PublicInvoicePayPage.tsx`,
  `PublicInvoicePaymentCompletePage.tsx`) — signed token → `/checkout` →
  `checkout_url` → redirect → `?paid=1` poll of `checkout-session-status`. The
  consumer ad flow is a structural clone (order token instead of invoice token).
- **Logo upload pipeline** (`app/services/logo_storage.py`, `POST /onboarding/logo`,
  `POST /tenants/current/logo`, public `logos` bucket, 2 MB + image MIME allowlist) —
  clone it for an `ad-creatives` bucket + `POST /ads/placements/{id}/asset`.
- **Accounting event emitter** (`accounting_event_emitter.py`) — emit
  `ad_order.paid` / `ad_order.refunded` alongside the existing payment events.
- **Admin page shell + cards** — `AdminIntegrationsPage.tsx` (keys/webhooks/
  connections "card-per-capability" layout), `AdminPageHeader`, `STYLE_GUIDE §15–16`.
  The Ad Management admin page composes from these — no new primitives.
- **Platform console + guard** — `PlatformAdminGuard.tsx`, `pages/platform/*`,
  `ROUTES.PLATFORM_TENANTS`. Platform-level ad packages + creative approval live here
  (they are cross-tenant, sold by the platform operator).
- **Audit service** (`audit_service.py`, `AuditService.log(...)`) — every ad write
  audited, same as every other mutation.
- **Notifications** (`notifications.py`, M4.1 prefs) — "your ad is live", "creative
  needs approval", "creative rejected".
- **Branding studio + live preview** (`OrganizationPage.tsx`,
  `branding/TenantThemeSync`) — the upload + live-preview UX is the model for the
  creative-upload + preview in the Ad Management page.
- **Vendor model** (`app/models/vendor.py`, `vendors` table) — a brokerage's
  **preferred vendors** are the natural advertisers for tenant-level "house ads",
  letting us deliver a real, paymentless E2E test loop (§4.4, §13.1).

### 2.3 Net gap (what 6.2 actually has to build)

1. **A backend advertising domain** on top of the existing table: a slot **registry**
   (code constant, like `SUPPORTED_WEBHOOK_EVENTS`), two **new tables** (`ad_packages`,
   `ad_orders`), an **ALTER** to `advertising_hooks` (creative/approval/order columns),
   a **repository + service + router**, an **ad-serving** endpoint (returns the ad for a
   slot + records an impression), a **click-tracking** redirect, and a **creative-upload**
   endpoint. *(Deliverables 1, 2.)*
2. **A reusable `<AdSlot>` React component** that fetches and renders the active ad for
   a slot key, supports the three formats, is responsive, is **unmistakably labeled
   `SPONSORED`**, and **collapses cleanly** when there is no ad — placed into the wizard
   right panel and the task queue. *(Deliverables 1, 4.)*
3. **An Ad Management admin UI** — split cleanly along the existing tenant/platform
   boundary: tenant Admin manages their **own house ads** + the **workspace ad-display
   toggle** at `/admin/advertising`; platform admin manages **sellable packages +
   creative approval + global tracking** at `/platform/advertising`. *(Deliverable 2.)*
4. **A standalone consumer-facing advertising site** — built as a **separate frontend
   project in its own GitHub repo, deployed to its own server/host + domain** (per client
   direction; §8): public landing + package browse + order form + **Stripe Checkout**
   purchase + completion page. It reuses the public invoice-pay flow as a **structural
   reference** and calls the **existing** backend's public ad API over CORS (it does
   **not** add routes to the established frontend app). *(Deliverables 3, 5.)*
5. **A dispatcher branch** so paid ad orders flow through the existing Stripe webhook
   and activate placements (pending admin approval). *(Deliverable 5.)*
6. **`docs/ADVERTISING_API.md`** documenting the model, slot registry, serving/tracking
   contract, billing webhook contract, and extension points. *(Deliverable 6.)*

---

## 3. Guiding design principles (acceptance gates, not aspirations)

**P1 — Front-end-testable or it does not exist.** Every backend capability ships with
a UI surface and a documented mouse-only click-path (§13). Nothing is "done" if the
only way to exercise it is curl/Swagger.

**P2 — Two independent, real, testable loops.** The module must be verifiable **without
real Stripe money and without a real external advertiser** (the *house-ad* loop:
tenant Admin creates → uploads → approves → enables workspace ads → sees it render),
**and** with Stripe in test mode (the *consumer-purchase* loop: advertiser buys a
package → pays with a test card → admin approves → ad goes live). If one loop is
blocked (e.g., Stripe sandbox hiccup on demo day), the other still proves the feature.

**P3 — No mock ads; honest empty/eligibility states.** Real creatives only. An empty
slot renders nothing. Crucially, the admin UI shows a **"why this ad is / isn't
showing"** diagnostic for every creative (Live now / Scheduled for <date> / Pending
approval / Rejected / **Not showing — workspace ads are disabled for this brokerage** /
Expired). This single feature is what prevents the "it silently didn't work" testing
breakdown the client has complained about.

**P4 — One-click over data entry (P2 of 6.1).** House ad = slot + image + date range.
Approve = one button. Buy = pick package + Stripe hosted Checkout (zero card fields in
our app). Workspace ads toggle = one switch with a clear explanation.

**P5 — Brand-consistent, modern, professional, and unmistakably "an ad".** Conform to
`STYLE_GUIDE.md`: `ve-*` tokens only, IBM Plex Sans/Lora/Plex Mono hierarchy,
`rounded-xl` cards, `lucide` icons, no native `<select>`, no `window.confirm`, 48px
targets. **Ads are visually quarantined**: a `SPONSORED` mono kicker, a neutral
hairline frame, and — per `STYLE_GUIDE §10` — **never** the champagne AI accent and
**never** the shape of the AI next-step banner or the AI Suggestions panel (§10, §13).

**P6 — Tenant safety + ad neutrality.** Every tenant-scoped write is tenant-scoped,
audit-logged, and Fernet-encrypts advertiser PII (email) at rest like other secrets.
Workspace ad display is **OFF by default** for every tenant; a brokerage that never
opts in never sees a third-party ad. Platform ads (tenant_id NULL) render only in
tenants that opted in.

**P7 — Never strand the user.** Every CTA resolves to a real route/action. Loading,
empty, error, and permission-denied states are designed up front. A clicked ad always
lands somewhere valid (tracked redirect validates the URL). A non-admin never sees an
ad-admin button that 403s.

---

## 4. Conceptual model & key product decisions

The single biggest source of "workflow breakdown" risk in this milestone is
**ambiguity about who advertises, to whom, and in what scope**. We resolve it
explicitly here so every downstream task is unambiguous.

### 4.1 The two ad scopes (mirrors `advertising_hooks.tenant_id` being nullable)

| Scope | `tenant_id` | Who creates it | Who pays | Where it can show | Approval |
| --- | --- | --- | --- | --- | --- |
| **Platform ad** | `NULL` | An external advertiser via the **consumer site**; catalog/pricing set by **platform admin** | The advertiser, via **Stripe** | Any tenant **that has opted in** to workspace ads | **Platform admin** approves the creative |
| **Tenant "house" ad** | tenant's id | The brokerage's own **Admin** (promoting a preferred vendor, an open house, an internal notice) | No payment — it's the brokerage's own slot | **Only that tenant's** workspace | The tenant Admin (self-approve) |

Both are stored in the **same** `advertising_hooks` placement rows and rendered by the
**same** `<AdSlot>`. The only differences are ownership, billing, and approver.

### 4.2 The advertiser is a "vendor/sponsor", consistent with the spec

`requirements.txt §11.1` says admins "approve **vendor** creative assets". The natural
platform advertiser is a real-estate-adjacent vendor (home warranty, title company,
inspector, lender). The consumer site addresses that buyer. This also keeps the module
honest: ads are relevant professional services, not arbitrary banners — reinforcing the
"professional tool" positioning (P5).

### 4.3 Ad lifecycle state machine (the spine of the whole milestone)

```
                       (house ad)                         (platform ad / consumer site)
 Admin creates creative ─┐                    advertiser picks package ─┐
                         ▼                                              ▼
                    [draft] ── upload asset ──▶ [pending_approval]   create ad_order [pending_payment]
                         │                            │                    │ Stripe Checkout
                         │ (tenant self-approve)      │                    ▼
                         ▼                            │              [paid] ──webhook──▶ creative [pending_approval]
                   [approved] ◀─ platform admin ──────┘                                       │ platform admin
                         │                                                                    ▼
       within [start,end] AND workspace ads enabled ──▶ [live]  ◀──────────────────────── [approved]
                         │
            end_date passes │ or Admin pauses │ or order refunded
                         ▼
                   [expired / paused / canceled]
```

Terminal/again-editable states are explicit so the admin "why not showing" diagnostic
(P3) can name the exact reason.

**OD-7 reconciliation (an explicit "awaiting creative" gap).** On the consumer path the
placement is created at **payment** with **no creative yet**, because OD-7 lets the
advertiser upload the creative *after* paying. So `pending_approval` in the diagram means
"creative uploaded, not yet approved", and a paid order with no creative shows as
**"Paid — awaiting creative"**, *not* in the approval queue. The platform approval-queue
query is therefore `approval_status='pending' AND content_url IS NOT NULL`. There is no
`scheduled`/`active`/`expired` **order** state — live vs. scheduled vs. expired is
**derived** from the placement's `start_date`/`end_date` + approval (there is no scheduler
in MVP, so we don't model states nothing transitions).

### 4.4 Workspace ad display: OFF by default (the brand-respecting default)

A white-label brokerage paying for a premium tool should not be ambushed by third-party
ads. So `tenants.settings_json.advertising.workspace_ads_enabled` defaults **false**.
A tenant Admin turns it on at `/admin/advertising` with a plain-English explanation of
what changes. **House ads (the tenant's own) are governed by the same toggle** so the
brokerage controls every slot in its own workspace from one switch. This is also what
makes the house-ad test loop (P2) fully self-contained.

### 4.5 Open decisions (resolve early in build; recommendations given)

- **OD-1 — Reuse `advertising_hooks` (ALTER) vs. new `ad_creatives` table.** *Recommend*
  **ALTER** the existing table (add `order_id`, `approval_status`, `approved_by`,
  `approved_at`, `rejected_reason`, `headline`, `body_text`). It already has tenant
  scoping, RLS, indexes, counters, dates, and tenant-deletion cascade — a parallel
  table duplicates all of that. (If the team prefers a clean split, the placement/
  counter row stays in `advertising_hooks` and creative metadata moves to a child
  table; costs one extra join. ALTER is simpler for "basic" MVP.)
- **OD-2 — Slot catalog: code registry vs. DB table.** *Recommend* a **code-level
  registry** (`SUPPORTED_AD_SLOTS`, mirroring `SUPPORTED_WEBHOOK_EVENTS`). Slots are a
  developer concern (they correspond to real render locations); a DB table would let an
  admin "create" a slot that has no render site — a dead-end. Adding a slot is a small,
  reviewed code change + doc update (§11).
- **OD-3 — Platform-fee/marketplace economics.** Out of scope (and M5.2 OD already set
  "no platform fee"). The advertiser pays the platform operator directly for platform
  ads; revenue accounting is the existing accounting webhook hook. *Recommend* no
  Stripe Connect split for ads at MVP.
- **OD-4 — Consumer-site theming.** The consumer site sells **platform** ad space, so it
  is **Velvet-Elves-branded, not tenant-themed** (unlike the tenant-branded login from
  M6.1). As a separate standalone app (OD-10) it does **not** import the tenant theming
  system at all; it ships a fixed Velvet Elves brand. *Recommend* platform branding;
  document clearly so QA doesn't file a "branding didn't apply" bug.
- **OD-5 — Ad rotation when multiple ads qualify for one slot.** *Recommend* a simple,
  deterministic precedence for MVP: tenant house ad > platform ad; ties broken by
  soonest `end_date`, then `created_at`. Weighted rotation / auction is a documented
  future hook (§11). One ad per slot render.
- **OD-6 — Impression integrity.** *Recommend* server-side increment on each
  `GET /ads/slot/{key}` serve, with a documented MVP limitation that refresh/bot
  inflation is not yet de-duplicated; a per-session dedupe token is a future hook.
- **OD-7 — Self-serve creative upload timing on the consumer site.** *Recommend* allow
  the advertiser to upload the creative **after** payment (order confirmation page has
  an "Upload your creative" step) so a failed upload never blocks the sale; the order is
  `paid` and the creative sits `pending_approval`. Platform admin can also upload on the
  advertiser's behalf.
- **OD-8 — Vendor-role self-service.** For MVP, the platform advertiser is **not** a
  logged-in Velvet Elves user; they use the public consumer site. A future hook lets the
  existing **Vendor** RBAC role (`requirements §1.2h`) manage their own creatives in-app.
  *Recommend* public-site-only for MVP.
- **OD-9 — Design pass before build.** No comp exists (R-7). *Recommend* a one-page
  Figma/HTML mock of (a) the `<AdSlot>` in the wizard and (b) the consumer-site landing,
  reviewed by the client (1–2 day turnaround per `milestones.txt` feedback-loop note),
  before frontend build — to avoid a post-build "this doesn't feel like our brand"
  rework.
- **OD-10 — Consumer-site topology. ✅ RESOLVED (client, 2026-06-02): standalone
  frontend + SHARED backend.** The consumer site is a **standalone frontend project** —
  its **own GitHub repo**, its **own server/host + domain** — **not** a route in
  `velvet-elves-frontend`; and it calls the **existing** backend's `/api/v1/public/ads/*`
  endpoints over **CORS** (§8.0). The backend is **not** duplicated: ad orders created on
  the consumer site land in the same database the platform-admin **approval queue** reads
  and the in-app **ad-serving** reads, so the order→approval→serve loop and the Stripe
  webhook/dispatcher stay unified. "New repo + new server" applies to the **frontend
  deployment** only. *(A fully separate backend was considered and **rejected** — it
  would duplicate the Stripe wiring + webhook and force a cross-service order/placement
  sync for no benefit.)*

---

## 5. Deliverable A — Advertising data model & backend

**Goal:** a tenant-safe, audit-logged backend that stores packages, orders, and
creatives/placements; serves the right ad for a slot; and tracks impressions/clicks —
all reusing existing patterns.

### 5.1 Slot registry (code constant — OD-2)

`app/services/advertising_service.py` defines:

```python
SUPPORTED_AD_SLOTS = {
    "wizard_confirmation": SlotSpec(location="wizard", formats={"banner", "text_link"},
                                    label="New Transaction wizard — confirmation step"),
    "wizard_parsing":      SlotSpec(location="wizard", formats={"banner"},
                                    label="New Transaction wizard — AI parsing step"),
    "task_queue_inline":   SlotSpec(location="tasks",  formats={"banner", "text_link",
                                    "sponsored_suggestion"}, label="My Task Queue — inline card"),
}
```

The registry is the single source of truth for: which slots exist, where they render,
and which formats each accepts. `GET /ads/slots` returns it (admin pickers consume it),
and `docs/ADVERTISING_API.md` documents how to add a slot.

**Validation rule (enforced in the service at create time, not just trusted from the
UI).** Every package's `slot_keys` must all be members of `SUPPORTED_AD_SLOTS`, **and**
every placement/package `ad_format` must be in the chosen slot's `formats` set. A request
to schedule, e.g., a `text_link` into the banner-only `wizard_parsing` slot is rejected
with a clear 422 (and the admin picker only offers compatible formats for the slot it
just chose). This guarantees `<AdSlot>` is never asked to render a format the slot was not
designed for — closing a quiet "the ad rendered wrong / didn't render" class of tester
breakage.

### 5.2 Database migration — `supabase/migrations/20260810090000_milestone_6_2_advertising.sql`

**Timestamp note:** latest existing migration is `20260805090000_tenant_api_keys.sql`;
Supabase applies in filename order, so use a strictly-greater timestamp. Bump if other
migrations land first.

**New table `ad_packages`** (what the consumer site sells; tenant_id NULL = platform):

| Column | Notes |
| --- | --- |
| `id uuid pk` | |
| `tenant_id uuid null references tenants(id)` | NULL ⇒ platform package |
| `name text not null`, `description text` | |
| `price_cents bigint not null`, `currency char(3) default 'usd' check (currency='usd')` | integer cents, USD-only (matches M5.2 §8) |
| `duration_days int not null` | order `ends_at = starts_at + duration_days` |
| `slot_keys text[] not null` | values validated against `SUPPORTED_AD_SLOTS` in the service |
| `ad_format text not null default 'banner'` | banner / text_link / sponsored_suggestion |
| `is_active bool default true`, `created_by uuid`, `created_at/updated_at` | |

**New table `ad_orders`** (the billing + advertiser + schedule anchor; mirrors `invoices`):

| Column | Notes |
| --- | --- |
| `id uuid pk`, `tenant_id uuid null` | NULL for platform orders from the consumer site |
| `package_id uuid not null references ad_packages(id)` | |
| `advertiser_company text not null`, `advertiser_name text`, `advertiser_email_encrypted text` | email Fernet-encrypted (`[[project_ve_pii_fernet_at_rest]]`) |
| `status text not null default 'pending_payment'` | **pending_payment / paid / canceled / refunded** only. Live/scheduled/expired is **derived** from the placement's `start_date`/`end_date` + approval — there is no scheduler in MVP, so we do **not** store states nothing transitions (§4.3). |
| `amount_cents bigint`, `currency char(3) default 'usd'` | snapshot of package price at purchase |
| `stripe_checkout_session_id text`, `stripe_payment_intent_id text unique` | webhook idempotency anchor |
| `starts_at date`, `ends_at date` | computed from package duration |
| `created_at/updated_at` | |

**ALTER `advertising_hooks`** (becomes the creative + placement + counter row — OD-1):

```sql
ALTER TABLE public.advertising_hooks
  ADD COLUMN IF NOT EXISTS order_id        uuid REFERENCES public.ad_orders(id),
  ADD COLUMN IF NOT EXISTS approval_status text NOT NULL DEFAULT 'pending',  -- pending/approved/rejected
  ADD COLUMN IF NOT EXISTS approved_by     uuid,
  ADD COLUMN IF NOT EXISTS approved_at     timestamptz,
  ADD COLUMN IF NOT EXISTS rejected_reason text,
  ADD COLUMN IF NOT EXISTS headline        text,   -- text_link / sponsored_suggestion
  ADD COLUMN IF NOT EXISTS body_text       text;   -- sponsored_suggestion
CREATE INDEX IF NOT EXISTS idx_ad_hooks_approval ON public.advertising_hooks (approval_status);
CREATE INDEX IF NOT EXISTS idx_ad_hooks_order ON public.advertising_hooks (order_id);
```

Existing columns reused as-is: `slot_name` (= slot key), `slot_location`, `ad_format`,
`title`, `content_url` (banner image URL), `click_url`, `creative_asset` (storage path),
`is_active`, `start_date`, `end_date`, `impressions`, `clicks`, `metadata_json`,
`tenant_id`.

**RLS:** `ad_packages`, `ad_orders` get the standard `service_role_all` +
`tenant_isolation` policies mirroring `20260511094000_rls_tenant_isolation.sql`.
Platform rows (`tenant_id IS NULL`) are reachable only by service-role/platform-admin
(app-layer guard is the live control per M6.1 OD-8). `advertising_hooks` already has
both policies.

**Tenant deletion:** add `ad_packages` and `ad_orders` to the
`tenant_deletion_service.py` table list (tenant-scoped rows only — platform rows with
`tenant_id IS NULL` survive). `advertising_hooks` is already listed.

**Storage bucket:** create public `ad-creatives` bucket (image MIME allowlist, ≤5 MB),
modeled on the `logos` bucket migration (`20260506_logos_bucket.sql`).

**Tenant setting:** no migration needed — `tenants.settings_json.advertising.workspace_ads_enabled`
(default treated as `false` when absent), read by the serving query (parallels how
M6.1 stored `settings_json.branding.*`).

### 5.3 Repository + service

- `app/repositories/advertising_repository.py` — CRUD for packages/orders/placements,
  plus the **serving query**: "active approved placement for slot `S` visible to tenant
  `T`", honoring scope precedence (OD-5) and the tenant toggle, all in one tenant-safe
  call.
- `app/services/advertising_service.py` — business logic:
  - `create_package / update_package / list_packages(scope)` (platform-admin for
    platform packages; tenant Admin for tenant packages — but house ads typically skip
    packages and create placements directly).
  - `create_house_placement(...)` — tenant Admin path: creates an `advertising_hooks`
    row directly (no order); on self-approve sets `approval_status='approved'` **and
    `is_active=true`** together (so the ad can serve), `tenant_id` = their tenant.
  - `record_order_from_checkout(...)` — called by the dispatcher branch (§9): flips
    order → `paid`, computes `starts_at/ends_at`, creates the placement row(s) in
    `pending` approval.
  - `approve_creative / reject_creative` — platform-admin (platform ads) or tenant
    Admin (house ads); approve sets `approval_status='approved'` **and `is_active=true`**
    (the placement was created `is_active=false` at payment, §9.2); reject sets
    `approval_status='rejected'` + `rejected_reason`; both audit-log and notify. "Pause"
    is a separate action that only flips `is_active=false` (keeps the approval).
  - `serve(slot_key, tenant) -> placement | None` — applies the eligibility predicate
    (`approval_status='approved'` AND `is_active` AND within `[start_date, end_date]` AND
    (tenant match OR platform) AND the tenant's `workspace_ads_enabled`) and precedence;
    **increments `impressions`** on the chosen row (OD-6).
  - `record_click(hook_id) -> validated click_url` — increments `clicks`, validates the
    URL with the existing `app/utils/url_safety.assert_safe_url` (reused from M6.1
    webhooks), returns it for redirect.
  - `eligibility_explanation(hook) -> str` — powers the admin "why not showing"
    diagnostic (P3): "Live now" / "Scheduled for Aug 3" / "Pending approval" /
    "Rejected: <reason>" / "Not showing — workspace ads are disabled for this
    brokerage" / "Expired Jul 30".
- `app/schemas/advertising.py` — request/response models (`AdPackage*`, `AdOrder*`,
  `AdCreative*`, `AdSlotServeResponse`, `AdTrackingRow`).

### 5.4 API contract — `app/api/v1/advertising.py` + `public_advertising.py`

```
# ── Slot registry (internal) ─────────────────────────────────────────────
GET    /api/v1/ads/slots                                  → SUPPORTED_AD_SLOTS catalog

# ── Ad serving (auth: any internal user; tenant-scoped) ───────────────────
GET    /api/v1/ads/slot/{slot_key}                        → active ad for this slot (or 204/empty) + records impression; response is `Cache-Control: no-store` so a proxy can't suppress/inflate counts

# ── Click tracking (PUBLIC, no auth — see note below) ─────────────────────
GET    /api/v1/ads/{hook_id}/click                        → 302 redirect to the stored, server-validated click_url + records click

# ── Tenant house-ad management (auth: tenant Admin) ───────────────────────
GET    /api/v1/ads/placements?scope=tenant                → this tenant's house ads
POST   /api/v1/ads/placements                             → create house placement (draft)
PUT    /api/v1/ads/placements/{id}                        → edit (while not live)
POST   /api/v1/ads/placements/{id}/asset                  → upload creative image (ad-creatives bucket)
POST   /api/v1/ads/placements/{id}/approve                → tenant self-approve (house) / platform approve
POST   /api/v1/ads/placements/{id}/reject                 → reject with reason
DELETE /api/v1/ads/placements/{id}                        → soft-delete (is_active=false)
GET    /api/v1/ads/tracking?scope=&period=                → impressions/clicks/CTR rows
GET    /api/v1/admin/advertising/settings                 → workspace_ads_enabled
PUT    /api/v1/admin/advertising/settings                 → toggle workspace_ads_enabled

# ── Platform ad management (auth: platform admin) ─────────────────────────
GET/POST/PUT  /api/v1/platform/ads/packages[/{id}]        → package catalog + pricing
GET    /api/v1/platform/ads/orders                        → paid orders queue
GET    /api/v1/platform/ads/placements?approval=pending   → creative approval queue
POST   /api/v1/platform/ads/placements/{id}/approve|reject
GET    /api/v1/platform/ads/tracking                      → global impressions/clicks/CTR

# ── Consumer site (PUBLIC, unauthenticated — public_advertising.py) ───────
GET    /api/v1/public/ads/packages                        → active platform packages (price, slots, duration)
POST   /api/v1/public/ads/orders                          → create pending order (company, email, package, start)
POST   /api/v1/public/ads/orders/{id}/checkout?token=     → Stripe Checkout session → { checkout_url }
GET    /api/v1/public/ads/orders/{id}/status?token=       → { order_status, paid } (poll after redirect)
POST   /api/v1/public/ads/orders/{id}/creative?token=     → advertiser uploads creative after paying (OD-7)
```

The public order routes use a **signed order token** exactly like
`invoice_pay_link_tokens.py` (new `ad_order_tokens.py`), so an unauthenticated buyer has
a clean URL without a login and cannot tamper with another order. Register both routers
in `app/api/v1/router.py` under a new "Milestone 6.2 — Advertising" block.

**Public-endpoint hardening (workflow-correctness notes).**
- The **click redirect** `GET /ads/{hook_id}/click` is **deliberately unauthenticated**:
  it is opened as a normal `<a target="_blank">` navigation, which **cannot** carry the
  app's `localStorage` JWT (you can't attach an `Authorization` header to a link
  navigation). An authed click endpoint would 401 and the buyer/agent would never reach
  the advertiser. It is safe because it only ever 302s to the **stored, pre-validated**
  `click_url` for that hook (no user-supplied target → no open-redirect) and only bumps a
  counter.
- The public **order-create** (`POST /public/ads/orders`) is rate-limited via the
  existing `app/core/rate_limit.py` to deter spam orders; `POST .../creative` is
  token-gated (only the buyer who holds the signed order token can attach a creative).

**Cross-origin note (OD-10):** the `public_advertising.py` routes are called from the
**standalone consumer site on a different origin** (§8). Add that origin to the
backend's CORS allowlist, and add a `consumer_site_url` setting in `app/core/config.py`
(used for the Stripe `success_url`/`cancel_url`, §9.1). The `/api/v1/ads/*` (internal,
authed) and `/api/v1/platform/ads/*` routes are same-origin with the main app and need
no CORS change.

### 5.5 Backend tests (`app/tests/`)

- `test_advertising_service.py` — package/order/placement CRUD; serving eligibility
  matrix (approved×active×dates×scope×toggle); precedence (OD-5); impression/click
  increments; `eligibility_explanation` strings.
- `test_advertising_isolation.py` — Brokerage A's house ad/order/tracking invisible to
  Brokerage B; A cannot serve into B; platform ad serves only into opted-in tenants
  (mirrors existing `test_*_isolation.py`).
- `test_ad_order_payment.py` — dispatcher branch (§9): paid order → placement created
  `pending`; refund → placement deactivated; idempotent on webhook replay.
- `test_public_advertising.py` — token gating, package listing, order→checkout→status,
  post-pay creative upload.
- Target net suite **stays green**; +40–60 tests (parity with M5.2/M6.1 additions).

---

## 6. Deliverable B — Ad-slot rendering hooks (wizard + task screens)

**Goal:** a single, modular, responsive, clearly-delineated `<AdSlot>` placed in the
wizard and task screens; renders a **real** ad or **nothing**.

### 6.1 The `<AdSlot>` component — `src/components/ads/AdSlot.tsx`

```tsx
<AdSlot slotKey="wizard_confirmation" />
```

Behavior:
1. `useAdSlot(slotKey)` (a `hooks/useAdSlot.ts` React-Query hook) calls
   `GET /ads/slot/:slotKey`. The server records the impression on serve (OD-6).
2. **No ad → render `null`** (the slot collapses; no box, no placeholder) — honoring
   `STYLE_GUIDE §11` and `[[no-demo-data-without-real-data]]`.
3. Ad present → render by `ad_format`:
   - **banner** — image (`content_url`) inside a neutral hairline card, responsive
     (`w-full h-auto`, max dimensions per slot), `alt` = title.
   - **text_link** — `headline` as a link row with a small external-link `lucide` icon.
   - **sponsored_suggestion** — a single restrained row (`headline` + one-line
     `body_text`) **in its own framed card** — never inserted into the AI Suggestions
     list.
4. Every variant shows the delineation treatment (§10): a `✦`-free `SPONSORED` mono
   kicker, neutral framing, no champagne accent.
5. Click → a plain `<a href="{API}/ads/:hookId/click" target="_blank" rel="noopener">`
   pointing at the **public** tracked-redirect endpoint (§5.4). It must be a real link
   navigation, **not** an authed `fetch` + `window.open` — a new tab can't carry the
   `localStorage` JWT, and a deferred `window.open` after an async fetch gets eaten by
   popup blockers. The advertiser's site opens without losing the user's wizard/task
   context. Keyboard-accessible, `aria-label="Sponsored: <title> (opens in new tab)"`.
6. Loading → a tiny skeleton matching the slot height (no layout shift); error →
   render `null` (an ad failing to load must never break the host page — P7).

### 6.2 Placements (MVP — modular via the registry)

- **Wizard** (`components/wizard/NewTransactionWizard.tsx`): one `<AdSlot
  slotKey="wizard_confirmation" />` in the confirmation step's right panel
  (`max-w-2xl`), below the confirm card and above the footer actions — where it cannot
  be confused with a data field; and optionally `wizard_parsing` during the AI-parse
  wait. Banner scales to the panel width.
- **Task screens** (`pages/tasks/TaskQueuePage.tsx`): one `<AdSlot
  slotKey="task_queue_inline" />` rendered as a card **after** the "Upcoming" group (not
  interleaved with tasks, so it never looks like a task). Supports all three formats.

Adding a future slot = add to `SUPPORTED_AD_SLOTS` + drop one `<AdSlot>` — that is the
"modular ad slots" architecture hook (Deliverable 1).

### 6.3 Front-end acceptance (tester-runnable)

- With an approved, active house ad and workspace ads ON: open the New Transaction
  wizard → a clearly-labeled `SPONSORED` banner appears in the confirmation step; open
  My Task Queue → the same/other ad appears below Upcoming. Click it → the advertiser's
  link opens in a new tab and the click count increments in tracking.
- Turn workspace ads OFF (or with no active ad): both slots render **nothing** — no
  empty boxes, no placeholders, no layout shift.

---

## 7. Deliverable C — Ad management admin UI

Split cleanly along the existing tenant/platform boundary so each surface matches its
data scope and its guard, and no role ever sees a control it can't use (P7).

### 7.1 Tenant Admin — `/admin/advertising` (`pages/admin/AdminAdvertisingPage.tsx`)

Standard admin page shell (`AdminPageHeader`, breadcrumb, `STYLE_GUIDE §15`), three
cards (composed like `AdminIntegrationsPage`):

1. **Workspace ads** card — one toggle: *"Show sponsored placements in your team's
   workspace"* with a plain-English note ("Off by default. When on, your own house ads
   and approved Velvet Elves partner ads can appear in the New Transaction wizard and
   Task Queue. They are always labeled *Sponsored* and never mixed with AI
   suggestions."). Wired to `PUT /admin/advertising/settings` with optimistic toggle +
   rollback.
2. **Your house ads** card — table of the tenant's own placements with the **"why
   showing / not showing"** status chip (P3) per row; `+ New house ad` opens a modal
   (slot picker from `/ads/slots`, format, **drag-and-drop image upload with live
   preview** mirroring the Branding studio, headline/body for text formats, click URL,
   date range). `Approve`/`Pause`/`Edit` row actions. Empty state: *"No house ads yet —
   promote a preferred vendor or post a team notice in your workspace."*
3. **Performance** card — impressions / clicks / CTR for the tenant's ads over a period
   selector, reusing the analytics table/empty-state pattern; chart has an explicit
   empty state (`STYLE_GUIDE §11`, §16.6).

Nav: add an **"Advertising"** item to the **Admin** sidebar group in
`layouts/AppLayout.tsx` (alongside AI Governance / Integrations / Audit Log, gated
`isAdmin`). Add `ROUTES.ADMIN_ADVERTISING = '/admin/advertising'` and the route in
`App.tsx` under `ProtectedRoute requiredRole="Admin"`.

### 7.2 Platform Admin — `/platform/advertising` (`pages/platform/PlatformAdvertisingPage.tsx`)

Under `PlatformAdminGuard` (cross-tenant; 404s for non-platform users), three cards:

1. **Packages & pricing** — CRUD for sellable platform packages (name, description,
   price, duration, slot keys, format, active). This is the catalog the consumer site
   reads.
2. **Creative approval queue** — placements that are `approval_status='pending'` **and
   have a creative uploaded** (`content_url` set, per §4.3): a preview of the creative +
   advertiser + package + requested window, with `Approve` / `Reject (reason)` buttons
   (one-click; `<AlertDialog>`, never `window.confirm`). Approve → set `is_active=true` so
   the ad serves for its date window; Reject → advertiser notified. Paid orders **without**
   a creative yet show in a separate "Awaiting creative from advertiser" list (not the
   approval queue), so the admin never sees an empty creative to approve.
3. **Global performance** — platform-wide impressions/clicks/CTR by package/order.

Nav: add a **"Advertising"** entry to the platform console (alongside
`PLATFORM_TENANTS`), gated by `PlatformAdminGuard`. `ROUTES.PLATFORM_ADVERTISING =
'/platform/advertising'`.

### 7.3 Front-end acceptance (tester-runnable)

- Tenant Admin creates a house ad end-to-end (slot + uploaded image + dates), self-
  approves, flips workspace ads on, and the "why showing" chip reads **"Live now"**; the
  ad then appears in the wizard/task slot (§6.3).
- Platform admin sets a $X package, sees a paid order's creative in the approval queue,
  approves it, and the ad goes live in opted-in tenants.
- Every status chip explains itself; no control 403s for the role that can see it.

---

## 8. Deliverable D — Consumer-facing advertising site (**standalone project**)

**Architecture (rev 1.1, per client direction).** The consumer site is a **separate,
standalone frontend project** with its **own GitHub repository**, deployed to its **own
server/host on its own domain** (e.g. `advertise.velvetelves.com`). It is **not** a route
inside the established `velvet-elves-frontend` app, and adds **no** routes to its
`App.tsx`. It is Velvet-Elves-branded (OD-4), not tenant-themed.

**Backend stays shared (OD-10).** The standalone site calls the **existing** backend's
public advertising API (`/api/v1/public/ads/*`, §5.4) over CORS. Orders, Stripe checkout,
the webhook/dispatcher, the platform-admin approval queue, and in-app ad-serving all live
in the **one** platform backend — a second backend would have to replicate that
order→approval→serve loop and is explicitly **not** recommended. So "new repo + new
server" applies to the **frontend deployment**; the data plane stays unified.

It still reuses the **public invoice-pay flow as a structural reference**
(`PublicInvoicePayPage.tsx` + `PublicInvoicePaymentCompletePage.tsx` +
`public_payments.py`) — same signed-token → Stripe-Checkout → status-poll shape — but as
an independent codebase.

### 8.0 New repository & deployment (net-new ops surface)

- **Repo:** a new private repository (working name `velvet-elves-advertise`), using the
  **same toolchain** as the main frontend (Vite + React + TS + Tailwind) for familiarity
  and brand fidelity.
- **Brand fidelity:** copy the `ve-*` token set from `tailwind.config.js`, the font/CSS
  variable setup from `index.css`, and the few UI primitives it needs (`Button`,
  `MoneyAmount`, dialog) into the new repo so it is visually identical to Velvet Elves
  and conforms to `STYLE_GUIDE.md`. (A shared design-token npm package is a documented
  future hook; for MVP, copy the tokens.)
- **Deployment:** a new server/host + CI/CD pipeline (mirror the existing
  `velvet-elves-frontend/deploy` config), a new DNS record, and a TLS certificate.
- **Backend wiring:** add the consumer-site origin to the backend **CORS allowlist** and
  add a `consumer_site_url` setting (used for Stripe `success_url`/`cancel_url`, §9.1).
- **Env:** the new app's only config is the **backend API base URL** (the existing
  platform API). It needs **no Stripe key at all** — collection is hosted Stripe Checkout
  (the backend creates the session and returns `checkout_url`; the site just redirects),
  so there is no Stripe.js/Elements and no publishable key to fetch. No secrets live in the
  consumer app.

### 8.1 Routes (the standalone app's **own** routes, on its **own** domain)

```
/                      → landing: value prop + audience + package grid (AdvertiseLandingPage)
/checkout/:orderId     → order form + "Continue to secure payment" (AdvertiseCheckoutPage)
/complete              → ?order=&session= status poll + "Upload your creative" step (AdvertiseCompletePage)
```

(No `/advertise/*` routes are added to the main app's `App.tsx`. The main app's only
touchpoint is an optional "Advertise with us" footer link pointing at the external
consumer-site URL — §12.)

### 8.2 Flow (minimum data entry — P4; all API calls hit the existing backend over CORS)

1. **Landing** (`AdvertiseLandingPage`) — `GET /public/ads/packages` renders a
   brand-consistent package grid (name, which slots it appears in, duration, price via a
   copied `MoneyAmount`). One primary CTA per package: **"Advertise with this package"**.
2. **Order form** — minimal fields: company, contact email, optional contact name,
   preferred start ("As soon as approved" default). `POST /public/ads/orders` creates a
   `pending_payment` order + returns a signed token → navigate to `/checkout/:orderId?token=`.
3. **Checkout** — review summary → **"Continue to secure payment"** →
   `POST /public/ads/orders/:id/checkout` → `checkout_url` → `window.location` to Stripe
   hosted Checkout (zero card fields in the app; PCI SAQ-A inherited from M5.2 §4.5).
4. **Complete** (`AdvertiseCompletePage`) — Stripe `success_url` returns to **this app's**
   `/complete`; it polls `GET /public/ads/orders/:id/status` for ≤30s (clone of the
   invoice complete page), then shows **"Payment received — upload your creative"**
   (`POST /public/ads/orders/:id/creative`, drag-drop image, headline/body for text
   formats, click URL) and *"Our team reviews creatives within 1 business day; you'll get
   an email when it goes live."* (OD-7).

### 8.3 Front-end acceptance (tester-runnable)

- Open the **standalone consumer site at its own URL** (logged out) → see real packages →
  pick one → fill company+email → pay with Stripe test card `4242 4242 4242 4242` → land
  on the site's `/complete` page → status flips to **paid** → upload a creative → see
  "pending review". The order then appears in the platform approval queue **in the main
  app** (§7.2) — proving the shared backend (OD-10) end-to-end across the two frontends.

---

## 9. Deliverable E — Ad billing via Stripe (reuse, don't rebuild)

**Goal:** ad orders are charged and reconciled through the **existing** Stripe client,
webhook, and dispatcher — no second payment stack.

### 9.1 Checkout

`POST /public/ads/orders/{id}/checkout` calls `stripe_client.create_checkout_session`:
- `line_items` = one `price_data` line from the package (`unit_amount = price_cents`,
  product name = package name).
- `metadata = {"kind": "ad_order", "ad_order_id": <id>, "tenant_id": <tenant or "">}`.
- **Retry-safe like the invoice flow** (`public_payments.py` `create_public_invoice_checkout`):
  if the order already has a stored `checkout_url` and is still `pending_payment`, return
  it; otherwise create a new session with a fresh
  `idempotency_key = f"ad_checkout:{order_id}:{attempt_ts}"`. A **fixed** key would pin the
  buyer to a possibly-expired session on retry.
- `success_url = {CONSUMER_SITE_URL}/complete?order={id}&session={CHECKOUT_SESSION_ID}`,
  `cancel_url = {CONSUMER_SITE_URL}/checkout/{id}` — where `CONSUMER_SITE_URL` is the new
  `consumer_site_url` config (§8.0), **not** `frontend_url`. These point at the standalone
  consumer site's own domain so Stripe returns the buyer to the right app.

### 9.2 Webhook (dispatcher branch — **no new endpoint**)

Extend `app/services/payment_event_dispatcher.py`. In `_on_checkout_completed` and
`_on_payment_intent_succeeded`, branch **before** the invoice path:

```python
md = obj.get("metadata") or {}
if md.get("kind") == "ad_order" or md.get("ad_order_id"):
    return await self._on_ad_order_paid(md, obj)   # new handler
```

`_on_ad_order_paid`:
1. Idempotently mark the order `paid` (guard on `stripe_payment_intent_id` unique
   index, same pattern as invoices), set `starts_at/ends_at` from the package duration.
2. Create the `advertising_hooks` placement row(s) for the package's `slot_keys`,
   **inheriting the order's scope** (`tenant_id` = order's `tenant_id`, **NULL for a
   platform order**), `approval_status='pending'`, `is_active=false`, **no creative yet**
   (`content_url` is filled by the advertiser's post-pay upload — OD-7), dates = order
   window. The placement enters the platform approval queue only once `content_url` is
   set (§4.3, §7.2).
3. Notify platform admin ("New ad creative awaiting approval").
4. Emit accounting event `kind='ad_order.paid'` via the existing
   `AccountingEventEmitter`.

**Upload-before-placement race (workflow-correctness fix).** This handler runs in
`BackgroundTasks` *after* the webhook has already returned 200, while the advertiser is
simultaneously redirected to the consumer site's `/complete` page to upload a creative
(§8.2 step 4). So `POST /public/ads/orders/{id}/creative` can arrive **before** this
handler has created the placement row(s). To prevent a sporadic 404 / lost-creative on a
fast advertiser, the upload handler is **self-healing**: it looks up the order's
placement row(s); if none exist yet it **creates** them (same scope/dates/slots as the
paid order, `approval_status='pending'`, `is_active=false`) and attaches the creative; if
they already exist it just sets `content_url`. Either ordering converges on the same
state, and the placement enters the approval queue exactly when `content_url` is set
(§4.3). `record_order_from_checkout` and the creative-upload endpoint therefore share one
idempotent "ensure placements for order" helper.

Refund branch: in `_sync_refund_state`, if the payment maps to an ad order, set order
`refunded` and deactivate its placements (so a refunded ad stops serving). Idempotent on
replay (the existing tests' replay scenario is extended in `test_ad_order_payment.py`).

### 9.3 Why this is safe

The dispatcher is already idempotent, already returns 200 fast, already runs side
effects in `BackgroundTasks`, and already ignores unknown metadata. Adding a metadata
branch is the minimal, low-risk change M5.2 §2.3 anticipated.

### 9.4 Acceptance

- A Stripe test-card payment on the **standalone consumer site** produces a `paid` ad
  order, a `pending` placement, a platform-admin notification, and an accounting event —
  verified via the
  platform approval queue (§7.2) and the admin "Payments health" / dead-letter views
  from M5.2. Webhook replay (Stripe "Resend") produces no duplicates.

---

## 10. Deliverable F — Clear ad/system (and ad/AI) delineation

This is a first-class deliverable (`milestones.txt` §6.2: "Clearly delineate ads from
system content") with a precise, enforceable rule set:

1. **`SPONSORED` label, always.** Every ad variant renders a mono kicker
   (`font-mono text-[9px] tracking-[1.8px] uppercase text-ve-text-muted`) reading
   `SPONSORED`. Non-negotiable, on every format.
2. **No champagne / no AI mimicry.** Per `STYLE_GUIDE §10`, the champagne `ve-orange*`
   accent is reserved for AI-touched surfaces. Ads use **neutral** framing
   (`border-ve-border`, `bg-white`/`ve-surface-2`) and **must not** reproduce the AI
   next-step banner gradient or sit inside the AI Suggestions panel. A `sponsored_suggestion`
   lives in its **own** framed card with the `SPONSORED` kicker, clearly separated from
   any AI suggestion list (§13 anti-patterns).
3. **Quarantined placement.** Ads render only in the registry's defined slots, never
   interleaved with tasks, transactions, contacts, or documents, and never inside a
   data form field region.
4. **Honest empty state.** No ad ⇒ no rendered element (P3).
5. **Accessible.** `aria-label` marks it as sponsored and that the link opens in a new
   tab; 48px target; keyboard-focusable.

A short subsection of `docs/ADVERTISING_API.md` codifies these as the "delineation
contract" so future slots/formats can't quietly violate it.

---

## 11. Deliverable G — Document the advertising API for future expansion

Create `velvet-elves-backend/docs/ADVERTISING_API.md` covering:

- **Data model** — `ad_packages`, `ad_orders`, the extended `advertising_hooks`
  placement row, the tenant `workspace_ads_enabled` setting, and the two scopes (§4.1).
- **Slot registry** — `SUPPORTED_AD_SLOTS`, and a **step-by-step "how to add a new
  slot"** (add registry entry → drop an `<AdSlot>` → document → the admin pickers update
  automatically).
- **Serving & tracking contract** — `GET /ads/slot/{key}` (eligibility predicate,
  precedence OD-5, impression-on-serve OD-6), `GET /ads/{id}/click` (tracked redirect +
  URL safety), the `eligibility_explanation` states.
- **Billing webhook contract** — the `metadata.kind="ad_order"` convention and the
  dispatcher branch (§9), so a future programmatic ad-buy API plugs into the same path.
- **Delineation contract** (§10).
- **Documented future-expansion hooks (explicitly NOT built in MVP):** weighted
  rotation / auctioned slots; geo/role/transaction-type **targeting**; per-session
  impression de-dup; the **Vendor RBAC role** self-serving its own creatives in-app
  (OD-8); programmatic/bulk ad-buy API; advertiser self-serve performance dashboard;
  Stripe Connect revenue-share if the platform ever takes a cut (OD-3). Each is named so
  the table/registry shapes already accommodate it.

This satisfies Req §11.1 ("Document advertising API for future expansion") and §13.5
(modular, documented APIs).

---

## 12. Navigation & information architecture (where everything lives)

- **In-app ad slots** → inside the New Transaction wizard and My Task Queue via
  `<AdSlot>` (no nav entry; they are embedded surfaces).
- **Tenant Advertising admin** → **Admin** sidebar group (`AppLayout.tsx`), `isAdmin`-
  gated, `/admin/advertising`.
- **Platform Advertising** → platform console under `PlatformAdminGuard`,
  `/platform/advertising`.
- **Consumer site** → a **separate standalone deployment on its own domain** (e.g.
  `advertise.velvetelves.com`), with its own `/`, `/checkout/:id`, `/complete` routes —
  **not** in the main app's `App.tsx` (rev 1.1, OD-10).
- **Footer link (optional):** an "Advertise with us" link on the main app's public
  login/landing footer pointing at the **external** consumer-site URL, so it is
  discoverable.

Every new internal nav entry is role-gated so non-eligible roles never see a link that
leads to a 403 (P7), consistent with the M6.1 IA discipline.

---

## 13. Front-end testing guide for non-developer testers (click-paths)

Every script is **mouse-only, in-product, no API client, no fake data** — these double
as the milestone demo acceptance scripts. Two independent loops (P2).

### 13.1 House-ad loop (no Stripe, fully self-contained) — Deliverables 1, 2, 4
1. As a brokerage **Admin** → sidebar **Admin → Advertising**.
2. Toggle **"Show sponsored placements in your team's workspace"** ON.
3. **+ New house ad** → pick slot **"My Task Queue — inline card"**, format **Banner**,
   drag in a real image (see the live preview), set start = today, end = +30 days, set a
   click URL (e.g. a preferred vendor's site) → **Save**.
4. **Approve** the ad → its status chip reads **"Live now."**
5. Open **My Task Queue** → the `SPONSORED` banner shows below Upcoming. Click it → the
   vendor site opens in a new tab.
6. Back to **Admin → Advertising → Performance** → impressions ≥ 1, clicks ≥ 1.
7. Toggle workspace ads **OFF** → reload Task Queue → the slot is **gone** (no empty box).

### 13.2 Consumer purchase loop (Stripe test mode) — Deliverables 3, 5
**Prerequisite (one-time, do this first):** as **platform admin** → **Platform →
Advertising → Packages & pricing** (§7.2) → create at least one **active** package (name,
price, duration, slot keys, format). Per the no-mock-data rule (P3) the consumer landing
shows an honest *empty* package list until a real package exists — so without this step
the tester opens the site, sees nothing to buy, and (wrongly) concludes it's broken. This
prerequisite is what keeps the loop from dead-ending on step 1.
1. Open the **standalone consumer site at its own URL** (e.g. `advertise.velvetelves.com`),
   logged out → see real packages → choose one.
2. Enter company + email → **Continue to secure payment** → Stripe Checkout → pay with
   `4242 4242 4242 4242`.
3. Land on the consumer site's **/complete** page → status flips to **Paid** → **upload a
   creative** → "pending review".
4. As **platform admin** → **Platform → Advertising → Creative approval queue** → see the
   creative → **Approve**.
5. In a tenant that has workspace ads **ON**, open the wizard/Task Queue → the approved
   platform ad now serves (clearly labeled `SPONSORED`).

### 13.3 Delineation & safety checks — Deliverable 4 / P5/P7
1. Confirm every ad shows the `SPONSORED` kicker, uses **no** champagne accent, and is
   never inside the AI Suggestions panel or the AI next-step banner.
2. As a **non-Admin** internal user → there is **no** Advertising nav item; typing
   `/admin/advertising` lands on a clean permission/not-found state, never a 403 button.
3. As **Brokerage B**, confirm none of Brokerage A's house ads, orders, or performance
   numbers are visible anywhere.

### 13.4 "Why isn't my ad showing?" diagnostic — P3
1. Create a house ad with a **future** start date → chip reads **"Scheduled for <date>."**
2. Leave it **unapproved** → chip reads **"Pending approval."**
3. Turn workspace ads **OFF** with an approved ad → chip reads **"Not showing —
   workspace ads are disabled for this brokerage."**
   (Each explanation matches reality, so a tester is never confused about state.)

---

## 14. Implementation sequencing & effort

Ordered by dependency and visible value. Sizes: S ≈ ≤1d, M ≈ 2–4d, L ≈ 1wk+.
Target: the full week (Mon 2026-07-27 → Sun 2026-08-02), Day 7 = buffer + manual QA.

| Order | Work | Deliverable | Size | Rationale |
| --- | --- | --- | --- | --- |
| 0 | (Pre-week) Confirm Stripe test mode still wired from M5.2; create `ad-creatives` bucket migration; **scaffold the standalone consumer-site repo + CI/CD + server/host + DNS + TLS + backend CORS allowlist + `consumer_site_url` config**; resolve OD-1/OD-2/OD-9/OD-10 | D (infra) | M | New repo + server is net-new ops — do it first so build has a target |
| 1 | Migration (`ad_packages`, `ad_orders`, ALTER `advertising_hooks`, RLS, tenant-deletion list); slot registry | A | M | Foundation for all else |
| 2 | Repository + service (serving predicate, precedence, tracking, eligibility explanation) + isolation tests | A | M | The logic core; tested before any UI |
| 3 | `<AdSlot>` component + `useAdSlot` + placements in wizard & Task Queue + delineation treatment | B, F | M | Highest-visibility tester win; works with house ads alone |
| 4 | Tenant Admin `/admin/advertising` (toggle, house-ad CRUD + upload, performance) | C | M | Completes the no-Stripe E2E loop (§13.1) |
| 5 | Dispatcher branch for `ad_order` paid/refunded + tests | E | S | Small, reuses M5.2 plumbing |
| 6 | Build the **standalone consumer-site app in its own repo** (landing, order, checkout, complete + creative upload) against the shared public API + brand-token copy | D | M/L | Net-new **separate** frontend + deploy; clones invoice-pay UX; depends on the Slice 0 repo/server scaffold |
| 7 | Platform `/platform/advertising` (packages, approval queue, global tracking) | C | M | Closes the consumer loop (§13.2) |
| 8 | `docs/ADVERTISING_API.md` + delineation contract | G | S | Documentation deliverable |
| 9 | Full manual QA via §13 scripts; `/security-review` on the diff; `tsc`/ESLint/build clean (both repos) | all | S/M | Definition of Done |

**Critical path:** 1 → 2 → 3 → 4 delivers a complete, demoable, **Stripe-free** feature
(house ads) **entirely in the existing app**. The consumer-purchase track (Slice 0 infra →
5 → 6 → 7) stands up the **separate** consumer repo/server and builds against the shared
backend once the service exists. **The standalone repo/server scaffold (Slice 0) is a hard
prerequisite for Slice 6** and adds calendar/ops time beyond a single in-app page — factor
it into the Week-21 plan (and consider scaffolding it during M6.1 if capacity allows).

---

## 15. Risks & open decisions

Open decisions OD-1…OD-10 are in §4.5. Additional risks:

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R-1 | Ads clash with the "calm professional tool" brand and the client rejects them on sight | Med | High | Workspace ads OFF by default (§4.4); strict delineation contract (§10); OD-9 design pass before build |
| R-2 | Tester sees no ad and assumes it's broken (the classic "workflow breakdown") | High | High | The "why showing / not showing" diagnostic (P3, §13.4) names the exact reason every time |
| R-3 | Ad/AI confusion violates the §10 champagne rule | Med | Med | Neutral framing only; no champagne; `sponsored_suggestion` quarantined from AI panel; codified in the delineation contract + a render test |
| R-4 | Stripe ad-order webhook duplicates or mis-routes | Low | Med | Reuse the idempotent dispatcher; metadata-keyed branch; replay test in `test_ad_order_payment.py` |
| R-5 | Cross-tenant leak of ads / orders / tracking | Low | Critical | New tables get the standard tenant_isolation policies; `test_advertising_isolation.py`; platform rows guarded app-layer (M6.1 OD-8) |
| R-6 | Creative upload (SSRF/abuse via click URL or image) | Low | Med | Reuse `assert_safe_url` on click URLs (rejects private/loopback/metadata); image MIME allowlist + size cap on the `ad-creatives` bucket; creatives gated behind approval before serving |
| R-7 | No approved comp → post-build rework | Med | Med | OD-9 one-page mock + client review (`milestones.txt` 2–3 day feedback loop) |
| R-8 | Scope creep into a full ad platform (targeting, auctions, advertiser dashboards) | Med | Med | `milestones.txt` Risk #6 caps scope at "basic"; every advanced feature is a documented hook in §11, not a build item |
| R-9 | Impression inflation on re-render / bots | Med | Low | Server-side increment on serve (OD-6); documented MVP limitation; per-session dedupe is a named future hook |
| R-10 | **Standalone consumer site adds a whole new ops surface** (new repo, new server/host, CI/CD, DNS, TLS, CORS) → real calendar/timeline risk inside a one-week milestone | Med | Med | Scaffold in Slice 0 / pre-week (ideally during M6.1); keep the app tiny (3 pages, no secrets); **share the backend** (OD-10) so there is no second API to stand up; reuse the existing frontend's deploy config + design tokens. **Backend stays shared (OD-10 resolved), so there is no second API/service to build** — the added ops is purely the static frontend's repo/host/DNS. |

---

## 16. Definition of Done

Milestone 6.2 is complete when **all** of the following are true and demonstrated
**through the UI by a non-engineer** using §13:

1. **House-ad loop (no Stripe):** a tenant Admin creates, uploads, approves, and
   enables a real house ad that then renders — clearly labeled `SPONSORED` — in the New
   Transaction wizard and the Task Queue; clicking it records a click; performance shows
   real impressions/clicks; turning workspace ads off makes the slot disappear cleanly.
2. **Consumer purchase loop (Stripe test mode):** an advertiser buys a package on the
   **standalone consumer site — a separate frontend deployed at its own domain (own repo
   + own server)** — pays via Stripe hosted Checkout, uploads a creative, and a platform
   admin approves it from the platform console **in the main app**; the approved platform
   ad then serves into opted-in tenants. The two frontends share the one backend (OD-10);
   webhook replay produces no duplicates.
3. **Ad slot architecture:** slots are defined in `SUPPORTED_AD_SLOTS`, rendered by one
   reusable responsive `<AdSlot>`, support banner / text-link / sponsored-suggestion,
   and adding a slot is a one-line registry + one `<AdSlot>` change (the "architecture
   hook" requirement).
4. **Delineation:** every ad carries `SPONSORED`, uses no AI/champagne accent, is never
   interleaved with system content or AI suggestions, and an empty slot renders nothing —
   verified against the delineation contract.
5. **Billing:** ad orders are charged and reconciled entirely through the existing M5.2
   Stripe client + webhook + dispatcher (a metadata branch, no second payment stack);
   refunds deactivate placements; accounting events emit.
6. **Isolation & safety:** the new surfaces are tenant-scoped with cross-tenant-denied
   tests; advertiser PII is Fernet-encrypted; click URLs pass `assert_safe_url`;
   `/security-review` is clean on the diff.
7. **Documentation:** `docs/ADVERTISING_API.md` documents the model, slot registry,
   serving/tracking/billing/delineation contracts, and the future-expansion hooks.
8. **Quality bars:** backend suite stays green (+~40–60 tests); **both frontend repos
   (the main app and the standalone consumer site)** pass `tsc`, ESLint
   (`--max-warnings 0`), and a clean production `build`; 0 console errors when
   navigating every new route; every new surface conforms to `STYLE_GUIDE.md`; every CTA
   resolves to a real action; every non-eligible role sees a clean permission state, not
   a button that errors.

---

## 17. Source references (reviewed for this plan)

- **Requirements:** `requirements.txt` §11 (Advertising & Monetization), §1.2h (Vendor),
  §2.5/§7.7 (Stripe), §9.5 (white-label), §10.2/§10.3 (security/audit), §10.5 (admin UI),
  §13.5 (modular/documented APIs).
- **Milestones:** `milestones.txt` Milestone 6.2; Risk #6 (scope guard); feedback-loop note.
- **Architecture:** `SYSTEM_DESIGN.md` §1.4 (multi-tenant), §2.4 (RLS), §3.3 (permission
  matrix), §2341 (advertising roadmap), Appendix C ("Per-intake pricing → Stripe").
- **Adjacent plans:** `MILESTONE_5_2_IMPLEMENTATION_PLAN.md` §2.3 (ad checkout reuses the
  Stripe module), §4.5 (PCI SAQ-A), §8 (money conventions); `MILESTONE_6_1_IMPLEMENTATION_PLAN.md`
  (grounding discipline, tester click-path format, IA/role-gating discipline, OD pattern).
- **Style:** `STYLE_GUIDE.md` (§1 brand voice, §2 color, §10 AI-adjacent UI, §11 empty
  states, §13 anti-patterns, §15 page shells, §16 dashboards).
- **Code (current state, reviewed):**
  - Dormant ad assets: `app/models/advertising_hook.py`, `app/models/__init__.py`,
    `supabase/migrations/202603110000_new_vendors_and_ad_hooks.sql`,
    `supabase/migrations/20260511094000_rls_tenant_isolation.sql`,
    `app/services/tenant_deletion_service.py:61`.
  - Stripe foundation: `app/services/stripe_client.py`, `app/api/v1/payments.py:267`
    (webhook), `app/services/payment_event_dispatcher.py`,
    `app/services/accounting_event_emitter.py`, `app/core/config.py` (stripe + frontend_url),
    `app/api/v1/public_payments.py`, `app/services/invoice_pay_link_tokens.py`.
  - Public-checkout UI: `src/pages/public/PublicInvoicePayPage.tsx`,
    `PublicInvoicePaymentCompletePage.tsx`; routing `src/App.tsx` (public routes,
    role-gating), `src/utils/constants.ts` (ROUTES).
  - Reuse patterns: `app/services/logo_storage.py` + `POST /onboarding/logo` +
    `POST /tenants/current/logo` (upload), `app/api/v1/webhooks.py` +
    `app/utils/url_safety.assert_safe_url` (URL safety), `src/pages/admin/AdminIntegrationsPage.tsx`
    (admin card layout), `src/pages/organization/OrganizationPage.tsx` (upload + live
    preview), `src/components/payments/MoneyAmount.tsx` (money formatting),
    `src/components/platform/PlatformAdminGuard.tsx`, `src/pages/platform/*`.
  - Host surfaces for slots: `src/components/wizard/NewTransactionWizard.tsx`,
    `src/pages/tasks/TaskQueuePage.tsx`; nav `src/layouts/AppLayout.tsx` (Admin group).
- **Standing client feedback honored:** `[[no-demo-data-without-real-data]]`,
  `[[ve-design-comp-fidelity]]`, `[[ui-visual-verification-method]]`.

*End of Milestone 6.2 implementation plan.*
