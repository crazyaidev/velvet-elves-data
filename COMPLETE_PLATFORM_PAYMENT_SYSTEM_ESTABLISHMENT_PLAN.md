# Complete Platform Payment System Establishment Plan

Created: 2026-06-18
Reviewed and corrected: 2026-06-18

Purpose: establish a complete, Stripe test-mode payment system for Velvet Elves before launch, using provisional base prices while final pricing remains undecided. The first objective is not to finalize commercial pricing. The first objective is to let Jake and real-estate professional testers verify, through the frontend UI, that every payment workflow works reliably in local and dev environments.

This plan does not change source code. It defines the build and test path.

---

## 1. Executive Decision

Build a feature-flagged platform billing system in test mode now, with base prices stored in configuration/database records and mirrored to Stripe test Price objects. The exact live launch prices must remain editable without source-code changes.

This supersedes the earlier "no online checkout until pricing is finalized" stance only for a controlled local/dev billing test slice. The UI must keep the beta/test-mode language honest: pricing is provisional, checkout uses Stripe test mode, and final pricing will be confirmed later.

The system must separate three payment lanes:

1. Platform billing: the workspace pays Velvet Elves for SaaS subscription, seats, add-ons, and optional credit packs.
2. Tenant workflow payments: a brokerage/team invoices clients or transaction parties and collects money through Stripe Checkout.
3. Advertising revenue: advertisers buy public ad packages and pay through Stripe Checkout.

These lanes may share Stripe infrastructure and webhook ingestion, but they must not share reporting labels, entitlement logic, or accounting meaning.

---

## 2. Source Review Summary

This plan is based on a review of the project documentation and the current frontend/backend implementation.

Reviewed product and design documents:

- `requirements.txt`
- `SYSTEM_DESIGN.md`
- `milestones.txt`
- `FRONTEND_UI_WORKFLOW_LOGIC.md`
- `STYLE_GUIDE.md`
- `STRIPE_LOCAL_CONFIGURATION.md`
- `MILESTONE_5_2_IMPLEMENTATION_PLAN.md`
- `MILESTONE_5_2_UX_IMPROVEMENT_PLAN.md`
- `MILESTONE_5_2_TESTING_GUIDE.md`
- `INVOICE_EMAIL_PAY_LINK_IMPLEMENTATION_PLAN.md`
- `REVENUE_GENERATION_SYSTEM_PLAN.md`
- `MULTI_TENANCY_IMPLEMENTATION_PLAN.md`
- `MULTI_WORKSPACE_MEMBERSHIP_DESIGN_PLAN.md`
- `AUDRI_THREAD_CONFIRMED_RESOLUTION_PLAN.md`
- AI wizard, auto-email, and AI agent planning documents for the shared UI-testability and non-developer QA requirements.

Reviewed backend areas:

- Stripe wrapper: `app/services/stripe_client.py`
- Invoice services and APIs: `invoice_service.py`, `invoices.py`, `client_invoices.py`, `public_payments.py`
- Payment services and APIs: `payments.py`, `refund_service.py`, `payment_event_dispatcher.py`
- Payment repositories and models: invoices, payments, refunds, payouts, Stripe customers, webhook events
- Admin payment access: `admin_payments.py`, `payment_access_service.py`
- Payment dashboards: `payments_aggregator.py`
- Tenant plan and seat model: tenant schemas, tenant APIs, tenant plan migrations
- Advertising checkout path: public advertising APIs, advertising service, ad-order webhook handling
- AI usage metering: `ai_usage_events`, `platform_ai_usage.py`, `ai_usage.py`

Reviewed frontend areas:

- Tenant invoice/payment pages and modals
- Public invoice pay pages
- Client/FSBO invoice pages
- Payment dashboard widget and health strip
- Admin Payment Access page
- Organization page plan/AI placeholders
- Platform Tenant Detail manual plan/seat editor
- Platform Advertising page and public ad checkout pages
- Route constants and app routing

Important finding: the open IDE tab `PLATFORM_PAYMENT_SYSTEM_CREDIT_WALLET_BUILD_AND_TEST_PLAN.md` was still not present on disk during this review. This plan therefore does not rely on that missing file.

### 2.1 Workflow and logic corrections from this review

The review found several workflow risks in the first draft. The body of this plan has been corrected for these points:

| Finding | Why it was a flaw | Correction |
| --- | --- | --- |
| Trial was listed like a Stripe checkout price. | The current tenant model already supports `trial` with `trial_ends_at` and seat limits. A zero-dollar Stripe subscription would add avoidable webhook and cancellation states during testing. | Treat trial as a local entitlement state by default. Only create a card-on-file trial checkout if Jake explicitly approves it. |
| Billing authority was described too generically. | Source now has `is_tenant_owner` in backend auth, frontend guards, and AppLayout owner affordance. Organization editing still has narrower legacy checks in places. | Billing must use an explicit `canManageBilling = is_tenant_owner || Admin || platform admin acting with audit context`, not the older Organization edit check. |
| Return routes could become isolated pages. | The product rules require no dead-end pages, and Organization already uses query-param sections. | Stripe return should land back in `Organization -> Billing` by default; standalone `/billing/*` routes may exist only as thin redirects/status shells. |
| Failed renewal and webhook-delay UAT assumed developer tooling. | Non-developer testers cannot be expected to pause webhooks, use Stripe CLI, or use Stripe Dashboard. | Add a local/dev-only frontend Billing Test Harness for simulated past-due, delayed webhook, replay, and recovery states. |
| Customer Portal permissions were too broad for provisional pricing. | Portal-hosted cancellation or plan switching can bypass the base-price review workflow. | First version of Customer Portal should allow payment-method and invoice/receipt management only; cancellation and plan changes stay disabled until Jake approves policy. |
| Credit wallet units were ambiguous. | The draft mixed cents, credits, and AI cost. | Credit wallet is optional and must use an explicit unit model and immutable ledger; no automatic AI consumption until Jake approves the conversion rule. |
| Platform billing routes were not tied to existing navigation. | Platform routes currently include Tenants, AI usage, and Advertising only. | Add explicit route constants, App routes, and Platform sidebar entries for Billing Prices and Billing Health when those UIs are built. |
| Multi-workspace billing scope was under-specified. | Project docs require billing to follow the active workspace, not always the user's home workspace. | Billing APIs must resolve tenant/workspace through the existing active-workspace mechanism and honor `X-Workspace-Id` where enabled. |

---

## 3. Current Implementation Audit

### 3.1 What already works and should be preserved

The existing Milestone 5.2 payment system is already a strong foundation for tenant workflow payments:

- Stripe test-mode configuration is documented in `STRIPE_LOCAL_CONFIGURATION.md`.
- Backend has a centralized Stripe wrapper and falls back to stub mode when Stripe keys are absent.
- Tenant invoice creation supports transaction context, payer contacts, line items, tax, terms, due dates, and linked task IDs.
- Sending an invoice creates/reuses a Stripe Checkout link, sends an email when email integration is available, and exposes a copy-link fallback.
- Public pay links use signed tokens and do not require login.
- Client/FSBO users can view and pay their own visible invoices from the frontend.
- Stripe webhooks are signature-verified and idempotent through `webhook_events`.
- Successful payments create/update payment rows, mark invoices paid, complete linked tasks, write communication log entries, and emit accounting events.
- Refunds validate refundable balance, use Stripe refunds, and reconcile from webhooks.
- Commission payouts use Stripe Transfers to the configured connected account.
- Admin payment access controls who can create invoices, refund, and trigger payouts.
- Payment dashboards expose collected amounts, outstanding invoices, payout summaries, and webhook health.
- Advertising orders already reuse Stripe Checkout with `kind=ad_order` metadata and separate ad-order settlement logic.

These existing flows must remain regression-protected while platform billing is added.

### 3.2 What is missing for complete platform billing

The current system does not yet provide a complete SaaS/platform payment system:

- No tenant-facing subscription checkout for a workspace to pay Velvet Elves.
- No Stripe subscription mirror tables.
- No local billing customer model for the organization itself. Existing `stripe_customers` is contact/payer focused for tenant invoices.
- No platform billing price catalog or Stripe Price sync.
- No Customer Portal session endpoint for owners/admins to manage payment methods, invoices, and receipts. Cancellation or plan changes should be a later policy-gated portal configuration.
- No subscription webhook dispatcher for `customer.subscription.*`, `invoice.paid`, `invoice.payment_failed`, or subscription-mode `checkout.session.completed`.
- No entitlement service that derives app access from subscription state, plan, seats, trial, and overrides.
- No tenant-facing billing history for platform subscription invoices.
- No billing health console for platform admins.
- No credit wallet or tenant-visible AI usage/credit ledger. AI usage is measured, but explicitly marked "not billing."
- Organization settings currently show an honest manual-plan placeholder and AI usage placeholder, not online billing.
- Platform Tenant Detail currently has manual plan/seat editing, not Stripe-backed billing state.

### 3.3 Existing constraints that the new plan must respect

- Current tenant plan values are `trial`, `solo`, `team`, and `enterprise`. Do not introduce new plan keys until a database migration and product decision approve them.
- `trial` is already a local tenant lifecycle state with `trial_ends_at`; do not create a zero-dollar Stripe subscription for trials unless Jake explicitly approves a card-on-file trial flow.
- Existing docs emphasize that billing follows the workspace. In future multi-workspace membership, the active workspace determines billing scope.
- Billing APIs must use the active workspace/tenant resolved by the existing auth layer, including `X-Workspace-Id` when multi-workspace is enabled. They must not accidentally bill or display the user's home workspace when the active workspace is different.
- Current source already implements `is_tenant_owner` and treats owners like Admins for workspace-management surfaces. Billing management must honor that owner anchor even when the user's visible role is Agent, Team Lead, or Transaction Coordinator.
- Staff seats include Admin, Team Lead, Agent, Transaction Coordinator, and Attorney. Client, FSBO, and Vendor portal accounts are not paid staff seats.
- Real-estate professional testers must validate the full workflow through the frontend UI, without database IDs, terminal commands, Stripe Dashboard requirements, or developer-only setup after preflight.
- Existing tenant invoice payments and advertiser payments must not be confused with SaaS subscription billing.

---

## 4. Product Principles

### 4.1 Honest pricing language

Because final pricing is not determined:

- Use "Base test price" or "Provisional beta price" language in local/dev billing UI.
- Never label a test amount as the final launch price.
- Never hardcode a price in frontend components.
- Store price configuration in a catalog and Stripe test Price IDs.
- Include a visible test-mode banner anywhere checkout can start in local/dev.
- Make Jake's review task explicit: he should be able to change or approve base prices from a platform-admin UI or a clearly documented seed/config surface.

### 4.2 Mouse-first billing

Real-estate professionals should not have to understand Stripe objects, UUIDs, webhooks, or database tables.

Every core action must be possible by mouse:

- Choose a base plan.
- Start test checkout.
- Return from checkout and see status.
- Open billing portal.
- View platform invoices.
- View payment failure recovery actions.
- Buy a test credit pack if credit wallet is included.
- See seat usage and plan limits.
- Copy a support bundle only when needed.

Minimal data entry is allowed only where unavoidable, such as billing email or card entry inside Stripe Checkout.

### 4.3 Hosted Stripe surfaces

Use Stripe Checkout and Stripe Customer Portal for card entry, subscription confirmation, payment method management, and invoice payment collection. Velvet Elves must never store, process, log, or render raw card data.

For the first provisional-pricing version, Customer Portal should be configured for payment-method management, invoice history, and receipts only. Portal-hosted cancellation, upgrade, downgrade, and quantity changes should stay disabled until Jake approves final pricing, cancellation policy, and proration behavior.

### 4.4 Entitlements should degrade carefully

Failed platform billing must not strand users in active transaction work without warning. Suggested policy:

- `trialing` or `active`: full allowed access for plan.
- `past_due`: show owner/admin recovery banner; keep core transaction access.
- `grace`: keep read/write access for active transaction work; block plan upgrades, optional AI credit purchases, and new paid add-ons.
- `restricted`: read-only or limited creation for non-critical actions, depending on Jake's policy.
- `suspended`: block paid workspace operations only after explicit owner/admin notices and platform-admin override options.

### 4.5 Platform billing is not tenant invoice billing

UI copy, API names, database tables, and dashboards must make this distinction plain:

- "Billing" or "Subscription" means the workspace paying Velvet Elves.
- "Invoices & Payments" means the workspace collecting money from clients/transaction parties.
- "Advertising" means public advertiser purchases.

---

## 5. Base Price Strategy for Test Mode

### 5.1 Price catalog

Create a platform price catalog that is the source of truth for base prices in local/dev and later for live prices.

Recommended table: `platform_price_catalog`

Recommended fields:

| Field | Purpose |
| --- | --- |
| `id` | Internal UUID. |
| `price_key` | Stable key such as `solo_monthly_base`, `team_monthly_base`, `ai_credit_pack_100`. |
| `plan_key` | Existing plan key: `trial`, `solo`, `team`, or `enterprise`; nullable for add-ons. |
| `display_name` | UI label, for example "Solo base" or "Team base". |
| `description` | Short UI copy. |
| `amount_cents` | Provisional amount in cents. |
| `currency` | Start with `usd`. |
| `interval` | `month`, `year`, or `one_time`. |
| `stripe_product_id_test` | Stripe test Product ID. |
| `stripe_price_id_test` | Stripe test Price ID. |
| `stripe_product_id_live` | Empty until launch approval. |
| `stripe_price_id_live` | Empty until launch approval. |
| `is_test_base_price` | True for provisional review prices. |
| `is_active` | Whether selectable. |
| `requires_jake_approval` | True until Jake approves the value/copy. |
| `effective_from` | Optional pricing start date. |
| `effective_until` | Optional pricing end date. |
| `metadata_json` | Seat limit, feature bundle, notes, Stripe sync checksum. |
| `created_by_user_id` | Audit context. |
| `updated_by_user_id` | Audit context. |
| `created_at`, `updated_at` | Timestamps. |

### 5.2 Initial catalog entries

Use existing plan keys unless Jake approves new plan taxonomy:

| Price key | Type | Notes |
| --- | --- | --- |
| `trial_local_state` | Local entitlement, not Stripe checkout by default | Uses existing `tenants.plan='trial'`, `seat_limit`, and `trial_ends_at`. Add card-on-file trial checkout only if Jake approves it. |
| `solo_monthly_base` | Subscription | Provisional monthly base price for a solo workspace. |
| `team_monthly_base` | Subscription | Provisional monthly base price for a team workspace. |
| `enterprise_manual` | Manual | Display "Contact/account team" in production; test checkout optional only if Jake wants it. |
| `ai_credit_pack_base` | One-time add-on | Optional phase; funds credit wallet for AI usage testing. |

The exact dollar values should be set by Jake in the platform-admin Base Price Console or by a seed file that is clearly marked local/dev. The important rule is that the code reads `price_key` and Stripe Price IDs, not hardcoded amounts.

Do not generate a Stripe Price for `trial_local_state` in the default flow. Trial start, trial expiry, and plan visibility are already supported by tenant plan fields; Stripe subscription state begins when the tenant chooses a paid base plan.

### 5.3 Stripe sync rule

Stripe Price amounts are immutable. If a base price changes:

1. Create a new Stripe test Price.
2. Mark the old catalog row inactive or versioned.
3. Preserve old subscriptions on their original Price unless an explicit plan-change flow migrates them.
4. Show platform admins which Stripe Price ID is active.

---

## 6. Target Backend Architecture

### 6.1 New billing tables

Add platform-billing-specific tables instead of reusing tenant workflow payment tables:

| Table | Purpose |
| --- | --- |
| `billing_customers` | One Stripe Customer per tenant/workspace for Velvet Elves SaaS billing. |
| `billing_subscriptions` | Local mirror of Stripe Subscription state. |
| `billing_subscription_items` | Plan, seat, add-on, and metered subscription items. |
| `billing_invoices` | Stripe subscription invoice mirror for UI and reporting. |
| `billing_checkout_sessions` | Checkout attempts, return status, selected base price, and user who started it. |
| `billing_entitlements` | Computed current capabilities and limits. |
| `billing_events` | Optional normalized event log; can reference `webhook_events`. |
| `tenant_plan_overrides` | Platform-admin manual/grandfathered exceptions. |
| `platform_price_catalog` | Base price catalog and Stripe test/live Price mapping. |
| `credit_wallets` | Optional tenant credit balance with explicit units such as `ai_credits`; do not store an ambiguous cents balance as the primary credit value. |
| `credit_wallet_ledger` | Optional immutable credit transactions: purchase, grant, consume, refund, adjustment, each with unit amount, optional dollar value, and conversion metadata. |

Do not reuse `stripe_customers`, because that table maps tenant contacts/payers to Stripe Customers for tenant-created invoices. Workspace SaaS billing needs a tenant-level customer model.

### 6.2 New services

Recommended backend services:

- `platform_billing_service.py`
  - Get current billing state.
  - Create or reuse billing customer.
  - Create subscription Checkout Session.
  - Create Customer Portal Session.
  - Return invoice history.
  - Reconcile checkout status after return.

- `platform_price_service.py`
  - List active base prices.
  - Validate catalog rows.
  - Sync Stripe test Products/Prices.
  - Prevent live-price edits unless live mode is explicitly enabled.

- `billing_event_dispatcher.py`
  - Handle subscription and subscription-invoice events.
  - Update billing mirrors.
  - Recompute entitlements.
  - Update `tenants.plan`, `seat_limit`, and `trial_ends_at` only as derived operational fields.

- `entitlement_service.py`
  - Return the current effective limits for the active workspace.
  - Merge Stripe subscription state, tenant plan overrides, trial state, and platform-admin exceptions.
  - Provide one API used by feature gates and the frontend.

- `credit_wallet_service.py` if credit wallet is included:
  - Maintain immutable credit ledger.
  - Apply purchases after Stripe payment.
  - Consume credits from recorded AI usage only after Jake approves the conversion rules.
  - Reverse credits on refund.

- `billing_test_harness_service.py` for local/dev only:
  - Simulate delayed webhook processing without requiring Stripe CLI.
  - Simulate subscription `past_due`, `grace`, `restricted`, and recovery states.
  - Simulate webhook replay against an already-processed event ID.
  - Reset a test tenant's billing state to a clean trial/base state.
  - Refuse to run in production.

### 6.3 Stripe wrapper expansion

Extend the existing centralized Stripe wrapper with methods for:

- Create subscription Checkout Session (`mode=subscription`) through a new method such as `create_subscription_checkout_session`.
- Create one-time Checkout Session for credit packs (`mode=payment`) through a method that preserves the existing tenant-invoice/ad-order payment behavior.
- Create Customer Portal Session through a new method such as `create_customer_portal_session`.
- Retrieve Subscription.
- Retrieve Invoice.
- List Customer invoices.
- Sync Product/Price objects for test catalog entries.

Keep existing tenant invoice payment methods intact. Do not turn the current `create_checkout_session` helper into a loosely-polymorphic method unless every existing caller is updated and regression-tested; current invoice and advertising flows rely on `mode='payment'` and specific metadata behavior.

### 6.4 Webhook events

Add handlers for platform billing events:

- `checkout.session.completed`
  - Branch first by metadata `kind`.
  - Route `platform_subscription` and `credit_pack` before the legacy invoice fallback.
  - Existing `kind=ad_order` and invoice metadata logic must keep working.

- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.finalized`
- `invoice.paid`
- `invoice.payment_failed`
- `invoice.payment_action_required`
- `charge.refunded` for credit pack reversal where applicable.

Webhook metadata requirements:

| Metadata key | Required for |
| --- | --- |
| `kind` | Must distinguish `invoice_payment`, `ad_order`, `platform_subscription`, `credit_pack`. |
| `tenant_id` | Tenant/workspace being billed. |
| `started_by_user_id` | Owner/admin/platform admin who initiated checkout. |
| `price_key` | Base price selected. |
| `checkout_session_id` | Local checkout attempt mapping when available. |

Dispatch order matters. The current dispatcher treats `kind=ad_order` specially, then falls through to invoice metadata. The platform billing implementation must extend that same branch point so subscription or credit-pack sessions never attempt to mark a tenant invoice paid and never create tenant workflow `payments` rows.

For Stripe subscription invoice events where metadata can be sparse, the dispatcher must resolve the tenant through the local `billing_subscriptions` or `billing_customers` mapping by Stripe customer/subscription ID. Do not assume every recurring invoice event will carry the original Checkout Session metadata.

### 6.5 Entitlement outputs

Recommended `GET /api/v1/billing/entitlements` response:

```json
{
  "tenant_id": "tenant-id",
  "plan": "team",
  "billing_state": "active",
  "staff_seat_limit": 10,
  "staff_seats_used": 4,
  "can_invite_staff": true,
  "can_use_ai": true,
  "can_buy_credits": true,
  "credit_balance_units": 0,
  "credit_unit_label": "credits",
  "trial_ends_at": null,
  "past_due_since": null,
  "grace_ends_at": null,
  "source": "stripe_subscription"
}
```

The frontend should use this for billing banners and paid feature gates. Backend authorization must also enforce it.

Because the current seat service and tenant APIs still read `tenants.plan`, `seat_limit`, and `trial_ends_at`, entitlement recomputation must also keep those operational tenant fields synchronized with the effective billing state. Treat Stripe plus overrides as the billing source of truth, but keep the existing tenant fields correct until the rest of the app reads only from `entitlement_service`.

---

## 7. Target API Surface

### 7.1 Tenant/owner billing APIs

Prefix: `/api/v1/billing`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/config` | Publishable key, environment mode, enabled features, active base prices. |
| `GET` | `/current` | Current subscription, plan, seat usage, invoices, payment method summary, entitlements. |
| `POST` | `/checkout-session` | Start subscription checkout for selected `price_key`. |
| `POST` | `/customer-portal` | Open Stripe Customer Portal for payment methods, invoices, and receipts. Cancellation/plan changes remain disabled until policy is approved. |
| `GET` | `/checkout-sessions/{id}` | Poll checkout completion after return. |
| `GET` | `/invoices` | Platform subscription invoice history. |
| `GET` | `/entitlements` | Effective current entitlement state. |

Permissions:

- Tenant owner (`is_tenant_owner`) and Admin can view billing and start checkout.
- Platform admin can act on behalf of a tenant with explicit audit context.
- Team Lead can view plan/seat state only if product approves.
- Agents, TCs, Attorneys, Clients, FSBO sellers, and Vendors should not manage platform billing unless separately approved.
- Every endpoint must use the active workspace/tenant resolved for the request. When multi-workspace is enabled, `X-Workspace-Id` must point billing actions at the selected workspace, not the user's home workspace.

### 7.2 Platform-admin billing APIs

Prefix: `/api/v1/platform/billing`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/prices` | List base price catalog and Stripe sync status. |
| `POST` | `/prices` | Create a local/dev base price entry. |
| `PUT` | `/prices/{id}` | Edit display/copy/active state; create new Stripe Price when amount changes. |
| `POST` | `/prices/{id}/sync-stripe` | Create/sync Stripe test Product/Price. |
| `GET` | `/tenants` | Cross-tenant billing status dashboard. |
| `GET` | `/tenants/{tenant_id}` | Tenant billing detail, subscription, invoices, events, entitlements. |
| `POST` | `/tenants/{tenant_id}/refresh-stripe` | Pull fresh Stripe subscription/customer/invoice state. |
| `POST` | `/tenants/{tenant_id}/override` | Add or update manual entitlement/plan override with reason. |
| `POST` | `/tenants/{tenant_id}/grant-credits` | Optional test credit grant with required reason. |
| `GET` | `/health` | Webhook backlog, failed subscription payments, catalog sync gaps, key mode check. |
| `POST` | `/test-harness/{tenant_id}/simulate` | Local/dev only. Simulate delayed webhook, past-due, replay, recovery, and reset states from the frontend QA panel. Must return 404 or 403 in production. |

### 7.3 Credit wallet APIs, optional phase

Prefix: `/api/v1/billing/credits`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/wallet` | Current tenant credit balance and recent ledger. |
| `POST` | `/checkout-session` | Buy a configured credit pack through Stripe Checkout. |
| `GET` | `/ledger` | Paginated credit ledger. |
| `GET` | `/usage` | Tenant-visible AI usage cost/credit consumption summary. |

Credit wallet should ship only after Jake approves whether usage should be prepaid credits, included quota, overage billing, or read-only reporting.

---

## 8. Frontend UI Plan

### 8.1 Organization Billing section

Add a dedicated `Billing` section to the Organization page, next to Company, Branding, Email, E-signature, and AI configuration.

This should be the primary tenant-facing platform billing surface.

Implementation alignment with the current frontend:

- Extend the existing Organization page section model with `SectionId = 'billing'` and make it deep-linkable with `?section=billing`.
- Use an explicit `canManageBilling` check: `user.is_tenant_owner || hasMinimumRole(user.role, 'Admin') || user.is_platform_admin`.
- Do not reuse the current `canEditTenant` variable as the billing authority unless it is first updated to include `is_tenant_owner`; otherwise Agent/TC founders who own their workspace could see billing but be unable to act.
- Show the active workspace/organization name in the billing header when multi-workspace is enabled, so testers can see which workspace will be charged.

Required sections:

1. Plan summary
   - Current plan: Trial, Solo, Team, or Enterprise.
   - Billing state: Trialing, Active, Past due, Grace, Restricted, Suspended, Canceled.
   - Staff seats used and limit.
   - Renewal date or trial end date.
   - Test-mode/provisional-price badge in local/dev.

2. Base price selector
   - Visible when billing checkout is enabled and user can manage billing.
   - Use plan cards or segmented plan rows, not raw Stripe IDs.
   - Each option shows plan label, base test price, seat limit, and included feature summary.
   - CTA: "Start test checkout" in local/dev; production copy changes only after launch approval.

3. Checkout status panel
   - After return from Stripe, show "Confirming payment with Stripe" and poll backend status.
   - Then show success, pending, failed, or canceled.
   - Include one-click retry for failed/canceled checkout.

4. Payment method and portal
   - Button: "Manage billing in Stripe".
   - Opens Customer Portal in a new window or redirects safely.
   - Explain that card details are managed by Stripe.
   - In the provisional-pricing version, portal capabilities are limited to payment methods, invoices, and receipts.

5. Billing history
   - Table of platform subscription invoices.
   - Columns: invoice date, plan/description, amount, status, receipt/invoice action.
   - Hide Stripe IDs behind an expandable "Support details" drawer.

6. Seat usage
   - Show paid staff seats used.
   - Link to Team/Admin Users page when user can manage seats.
   - Explain which roles count as staff seats.

7. AI usage and credits, if enabled
   - Replace the current AI placeholder with a real read-only usage meter or credit wallet.
   - Show usage by feature/deal only after data exists.
   - Keep "measurement only" language until Jake approves billing conversion.

### 8.2 Billing return pages

Default Stripe return target should be the existing Organization billing section:

- Success URL: `/organization?section=billing&billing_result=success&session_id={CHECKOUT_SESSION_ID}`
- Cancel URL: `/organization?section=billing&billing_result=canceled&session_id={CHECKOUT_SESSION_ID}`

Optional standalone routes may exist:

- `/billing/complete`
- `/billing/canceled`

If added, these routes must be thin status shells that immediately link or redirect back to `Organization -> Billing`. They must not become a second billing workspace.

The return experience should:

- Show current checkout state.
- Poll backend for subscription status.
- Provide "Open Billing", "Retry checkout", and "Go to dashboard" actions.
- Show test card reminders only in local/dev test mode.

### 8.3 Platform-admin Base Price Console

Add a platform-admin UI to manage base prices for local/dev and later live readiness.

Recommended location: Platform Admin -> Billing -> Base Prices.

Required capabilities:

- List price catalog entries.
- Show active/inactive state.
- Show test/live mode.
- Show Stripe Product/Price sync status.
- Create a base price entry by selecting plan, interval, amount, and display copy.
- Sync to Stripe test mode.
- Mark price active/inactive.
- Require a reason when changing an amount.
- Show "Jake approval" status.
- Prevent accidental live-price edits unless a live-mode gate is explicitly enabled.

Implementation alignment with current platform navigation:

- Add route constants such as `/platform/billing/prices` and `/platform/billing/health`.
- Register routes inside the existing `PlatformAdminGuard`.
- Add Platform sidebar entries alongside Tenants, AI usage, and Advertising.
- Use the existing `PlatformPageHeader`/platform layout conventions and `ve-*` tokens instead of the older gray Card styling where practical.

### 8.4 Platform Tenant Detail billing card

Enhance Platform Tenant Detail with a Billing card:

- Current billing customer.
- Subscription status.
- Current price key.
- Current plan and seat limit.
- Last invoice status.
- Failed payment count.
- Entitlement source: Stripe, trial, manual override, or grandfathered.
- Actions:
  - Refresh from Stripe.
  - Open Stripe customer in dashboard only for platform admins.
  - Add manual override with reason.
  - Grant test credits, if enabled.

The current manual Plan & Seats editor should remain available as an override path but should be visually distinct from Stripe-backed billing.

### 8.5 Platform Billing Health page

Add a health console for test readiness:

- Stripe key mode: test or live.
- Webhook endpoint status: configured/missing.
- Webhook pending older than five minutes.
- Failed billing webhooks.
- Active base prices without Stripe Price IDs.
- Stripe Prices without local catalog mapping.
- Subscription count by status.
- Recent failed invoice payments.
- Recent checkout sessions stuck in pending.

This page is for platform admins and QA leads. It should convert infrastructure problems into plain-language actions.

### 8.6 Test-mode QA panel

In local/dev only, show a collapsible "Test payment tools" panel on billing pages:

- Successful card: `4242 4242 4242 4242`
- Declined card: `4000 0000 0000 0002`
- 3D Secure card: `4000 0025 0000 3155`
- Any future expiration date and any CVC.
- Current Stripe mode: test.
- Last webhook event received for this checkout, if available.
- Simulate delayed webhook processing.
- Simulate subscription past-due, grace, restricted, and recovered states.
- Simulate webhook replay for the current checkout/subscription.
- Reset this test tenant's billing state.

This panel must be hidden in production.

### 8.7 Visual design requirements

Follow `STYLE_GUIDE.md`:

- Use existing `ve-*` design tokens.
- Keep the app light, quiet, and professional.
- Match existing Organization page section-rail layout.
- Use IBM Plex Sans/Mono and Lora heading patterns already in the app.
- Use dense but readable operational surfaces, not marketing-style pricing pages.
- Keep cards to real grouped information, not nested decoration.
- Use lucide icons for actions.
- Use tabular numbers for money and dates.
- Do not show raw IDs by default.
- Ensure mobile layout keeps CTA buttons and prices readable without overlap.

---

## 9. Backend Build Workstreams

### Workstream A: billing foundations

1. Add `platform_price_catalog`.
2. Add `billing_customers`.
3. Add `billing_checkout_sessions`.
4. Add `billing_subscriptions`.
5. Add `billing_subscription_items`.
6. Add `billing_invoices`.
7. Add `billing_entitlements`.
8. Add `tenant_plan_overrides`.
9. Add RLS policies scoped by tenant and platform-admin role.
10. Add indexes for tenant, Stripe customer, Stripe subscription, Stripe invoice, billing status, and created date.
11. Add local/dev-only billing test harness storage if needed to simulate states without touching live Stripe state.

Acceptance:

- Tables migrate cleanly.
- Existing tenant invoice payment tests still pass.
- Tenant isolation cannot be bypassed.
- Platform admin can query cross-tenant billing tables through approved APIs only.

### Workstream B: Stripe subscription service

1. Extend Stripe wrapper for subscription Checkout and Customer Portal.
2. Create `platform_billing_service.py`.
3. Create tenant billing customer if missing.
4. Create subscription Checkout Session from active `price_key`.
5. Store checkout attempt before redirecting to Stripe.
6. Reconcile return status from checkout session.
7. List subscription invoice history.
8. Provide safe user-facing Stripe error messages.
9. Keep Customer Portal capabilities restricted to payment methods, invoices, and receipts until Jake approves cancellation/plan-change behavior.

Acceptance:

- Owner/Admin can start Stripe test subscription checkout from the API.
- Checkout metadata includes tenant, user, and price key.
- A canceled checkout returns to the app without creating a false active subscription.
- Stripe API failures return actionable UI-safe errors.

### Workstream C: subscription webhooks

1. Extend event dispatcher branching by metadata `kind`.
2. Add subscription event handlers.
3. Update billing mirrors idempotently.
4. Recompute entitlements after subscription changes.
5. Mirror Stripe invoice payment state.
6. Record failed payment state and recovery windows.
7. Keep existing invoice/ad-order webhook behavior unchanged.
8. Resolve recurring subscription invoice events by Stripe customer/subscription ID when metadata is missing.
9. Ensure `platform_subscription` and `credit_pack` never fall through into tenant invoice payment handling.

Acceptance:

- Replayed Stripe events do not duplicate side effects.
- `checkout.session.completed` for tenant invoice, ad order, subscription, and credit pack routes to the correct handler.
- `invoice.payment_failed` creates a visible past-due billing state.
- `customer.subscription.deleted` cancels/restricts entitlements according to policy.

### Workstream D: entitlement service

1. Define plan limits for `trial`, `solo`, `team`, and `enterprise`.
2. Compute effective plan from subscription, trial, and overrides.
3. Expose `/billing/entitlements`.
4. Integrate with seat invitation checks.
5. Add owner/admin recovery banners based on billing state.
6. Keep manual platform overrides auditable and time-bounded where possible.
7. Synchronize `tenants.plan`, `seat_limit`, and `trial_ends_at` after subscription or override changes because current seat checks still use those fields.

Acceptance:

- Changing a subscription changes entitlements without code deployment.
- Manual override can rescue a tenant during test failures.
- Seat limits remain consistent with existing team management logic.
- Non-owner staff cannot silently manage billing.

### Workstream E: optional credit wallet

Only build this in the first release if Jake wants prepaid or purchased credits tested before launch.

1. Add `credit_wallets`.
2. Add immutable `credit_wallet_ledger`.
3. Add one-time Stripe Checkout for configured credit packs.
4. Apply credits on payment success.
5. Reverse credits on refund.
6. Connect AI usage to read-only cost reporting first.
7. Convert usage into credit consumption only after Jake approves the formula.

Acceptance:

- Buying a test credit pack increases visible balance.
- Ledger shows purchase, grant, consume, refund, and adjustment events.
- Credit balance cannot go negative unless product explicitly approves overage.
- AI usage failures never break document parsing or transaction work.

---

## 10. Frontend Build Workstreams

### Workstream F: billing hooks and types

Add typed frontend models and React Query hooks:

- `useBillingConfig`
- `useCurrentBilling`
- `useCreateBillingCheckoutSession`
- `useCreateCustomerPortalSession`
- `useBillingCheckoutStatus`
- `useBillingInvoices`
- `useBillingEntitlements`
- `usePlatformBillingPrices`
- `useSyncStripePrice`
- Optional `useCreditWallet`

Acceptance:

- Query keys invalidate after checkout return, portal return, price changes, and webhook reconciliation.
- Hooks use existing `useApiFetch` and `useApiMutate` patterns.
- No component directly constructs Stripe URLs.

### Workstream G: tenant billing UI

1. Add Billing section to Organization page.
2. Add plan summary.
3. Add base price selector.
4. Add checkout CTA and return-state polling.
5. Add Customer Portal button.
6. Add platform invoice history.
7. Add seat usage card.
8. Add AI usage/credits surface if enabled.
9. Use `canManageBilling` based on owner/admin/platform-admin authority, and show read-only billing state for users who can view but not manage.

Acceptance:

- A tester can go from Organization -> Billing -> choose base plan -> Stripe Checkout -> success return -> active plan visible.
- No raw Stripe IDs appear in normal UI.
- Failed and canceled checkout states provide next actions.
- Billing remains hidden or read-only for users without manage-billing permission.

### Workstream H: platform-admin billing UI

1. Add Base Price Console.
2. Add Billing Health page.
3. Add Billing card to Platform Tenant Detail.
4. Add platform tenant billing list filtered by status.
5. Add override modal with reason.
6. Add test credit grant modal if credit wallet is enabled.
7. Add local/dev Billing Test Harness actions for delayed webhook, past-due, replay, recovery, and reset.

Acceptance:

- Jake or a platform admin can inspect base prices and sync Stripe test Price IDs without developer tooling.
- Platform admin can diagnose webhook/catalog/subscription issues from the UI.
- Platform admin can recover a tenant from test billing issues through a visible override, with audit log.

### Workstream I: billing return UX

1. Return Stripe success/cancel to `/organization?section=billing`.
2. Add `/billing/complete` and `/billing/canceled` only as optional redirect/status shells.
3. Poll checkout status from the Organization Billing section.
4. Keep links back to Organization -> Billing, dashboard, and retry checkout.
5. Show local/dev test card help.
6. Handle delayed webhook state gracefully.

Acceptance:

- Returning from Stripe never lands on a blank page.
- If webhook is delayed, the UI says it is confirming and keeps polling.
- If checkout fails, the user can retry without support.

---

## 11. Non-Developer UAT Plan

All tests below must be executable from the frontend UI after environment preflight is complete.

### 11.1 Preflight checklist

Platform admin verifies:

1. App shows Stripe test mode.
2. Backend reports Stripe test publishable key.
3. Webhook endpoint is configured.
4. Billing feature flag is enabled in local/dev.
5. Base price catalog has active test prices for Solo and Team.
6. Each active base price is synced to a Stripe test Price.
7. A test tenant owner/admin account exists.
8. A platform admin account exists.
9. Existing tenant invoice payment flow still has test configuration.
10. No live Stripe key is used on local/dev.
11. Local/dev Billing Test Harness is visible to platform admins and hidden from production.

### 11.2 Jake feedback scenarios

Scenario 1: review base price presentation

- Log in as platform admin.
- Open Platform -> Billing -> Base Prices.
- Confirm Solo and Team base prices are visible.
- Edit display copy or amount if needed.
- Sync Stripe test Price.
- Mark the price "Ready for Jake review."

Pass criteria:

- Jake can understand what will be charged in the test.
- The UI clearly says the amount is provisional/test-mode.
- No code change is required to change a base price.

Scenario 2: owner starts subscription checkout

- Log in as tenant owner/admin.
- Open Organization -> Billing.
- Choose Solo or Team base plan.
- Click "Start test checkout."
- Use Stripe test card `4242 4242 4242 4242`.
- Return to Velvet Elves.

Pass criteria:

- Checkout opens in Stripe.
- Return page confirms payment or shows confirming state.
- Organization -> Billing shows active subscription after webhook reconciliation.
- Seat limit and plan reflect selected base plan.

Scenario 3: declined checkout recovery

- Start checkout again with a declined test card.
- Use `4000 0000 0000 0002`.
- Cancel or return to the app after Stripe refuses the card.

Pass criteria:

- UI does not claim the plan is active.
- Owner/admin sees plain-language canceled/failed checkout state and retry action.
- Platform Billing Health shows the checkout attempt as not completed.
- No tenant invoice payment records are incorrectly created.

Scenario 3B: failed renewal or past-due recovery

- Log in as platform admin.
- Open Platform -> Billing Health or the tenant Billing card.
- Use the local/dev Billing Test Harness to simulate `invoice.payment_failed` or `past_due` for the test tenant.
- Log in as tenant owner/admin and open Organization -> Billing.

Pass criteria:

- Owner/admin sees a plain-language past-due recovery banner.
- Core transaction work is not suddenly stranded.
- Retry/recovery action is visible.
- Platform admin can simulate recovery and the tenant UI returns to active/healthy state.

Scenario 4: Customer Portal management

- From Organization -> Billing, click "Manage billing in Stripe."
- Open Customer Portal.
- View payment method and subscription invoice.
- Return to Velvet Elves.

Pass criteria:

- Customer Portal opens safely.
- Billing page remains understandable after return.
- No card data appears in Velvet Elves.

Scenario 5: subscription invoice history

- After successful test subscription, open Organization -> Billing -> Billing history.

Pass criteria:

- Platform subscription invoice appears.
- Amount, date, and status are visible.
- Stripe IDs are hidden unless support details are expanded.

Scenario 6: entitlement and seat enforcement

- Subscribe tenant to Solo base plan.
- Try inviting staff beyond Solo seat limit.
- Switch to Team base plan or platform override.
- Try invite again.

Pass criteria:

- Seat-limit messaging is clear.
- Plan change or override updates allowed seats.
- Client/FSBO/Vendor portal users do not count as staff seats.

Scenario 7: platform-admin tenant billing view

- Log in as platform admin.
- Open Platform -> Tenants -> selected tenant.
- Review Billing card.
- Click "Refresh from Stripe."
- Add manual override with reason.

Pass criteria:

- Billing state is visible without Stripe Dashboard.
- Override requires a reason.
- Tenant-facing billing state updates after override.

Scenario 8: webhook delay handling

- Log in as platform admin.
- Use the local/dev Billing Test Harness to mark the current checkout or subscription event as delayed.
- As tenant owner/admin, complete checkout and return to Velvet Elves.

Pass criteria:

- UI shows "confirming" instead of a false failure.
- Health page shows pending webhook/backlog.
- When webhook arrives, subscription becomes active.
- Replaying the same event from the test harness does not duplicate subscription, invoice, credit, or tenant payment records.

Scenario 9: existing tenant invoice payment regression

- As Agent/Admin, create and send a transaction invoice.
- Pay through public/client pay link with `4242 4242 4242 4242`.
- Confirm invoice paid, linked task completed, dashboard updated.

Pass criteria:

- Tenant invoice workflow still works.
- Platform subscription billing did not contaminate tenant payment records.

Scenario 10: advertising checkout regression

- Create or use an ad package.
- Start public ad checkout.
- Pay with Stripe test card.
- Confirm ad order paid and creative upload/approval flow still works.

Pass criteria:

- Advertising checkout still routes through `kind=ad_order`.
- Platform subscription events do not alter ad orders.

Scenario 11: credit pack purchase, if enabled

- Open Organization -> Billing -> Credits.
- Buy a test credit pack.
- Pay with Stripe test card.
- Return to Velvet Elves.

Pass criteria:

- Credit balance increases.
- Ledger shows purchase.
- A platform-admin test refund/reversal action adjusts the ledger without deleting history.

Scenario 12: tenant isolation

- Log in to Tenant A and Tenant B.
- Complete billing checkout for Tenant A.
- Open billing for Tenant B.

Pass criteria:

- Tenant B cannot see Tenant A subscription, invoices, customer, or credits.
- Platform admin can see both only from platform-admin routes.

Scenario 13: active workspace billing, if multi-workspace is enabled

- Log in as a user with access to two workspaces.
- Switch to Workspace A and open Organization -> Billing.
- Switch to Workspace B and open Organization -> Billing.
- Start checkout only for Workspace B.

Pass criteria:

- The Billing page clearly displays the active workspace being charged.
- Checkout metadata and resulting subscription attach to Workspace B.
- Workspace A billing state does not change.

---

## 12. Automated Test Plan

### 12.1 Backend tests

Add unit and integration tests for:

- Price catalog validation.
- Stripe Price sync service.
- Billing customer creation and reuse.
- Subscription checkout session creation.
- Checkout metadata.
- Customer Portal session creation.
- Billing webhook branching by `kind`.
- Billing webhook does not fall through into tenant invoice/ad-order handlers for subscription or credit-pack events.
- Subscription created/updated/deleted reconciliation.
- Invoice paid/payment_failed reconciliation.
- Subscription invoice event reconciliation when metadata is missing and only Stripe customer/subscription IDs are available.
- Idempotent webhook replay.
- Entitlement calculation from active subscription.
- Entitlement calculation from trial.
- Entitlement calculation from manual override.
- Seat-limit enforcement through entitlements.
- Synchronization from entitlements to `tenants.plan`, `seat_limit`, and `trial_ends_at`.
- Tenant isolation.
- Active-workspace billing scope with `X-Workspace-Id`.
- Platform-admin authorization.
- Local/dev test harness refuses to run in production.
- Existing invoice payment webhook regression.
- Existing ad-order payment webhook regression.
- Optional credit wallet purchase/refund/ledger integrity.

### 12.2 Frontend unit tests

Add tests for:

- Billing section renders current plan and test-mode badge.
- Base price selector disables unavailable/inactive prices.
- Checkout CTA calls backend and redirects only when URL exists.
- Return page handles success, pending, canceled, and failed states.
- Customer Portal button handles missing portal URL gracefully.
- Billing history hides raw IDs by default.
- Platform Base Price Console edit/sync states.
- Platform Billing Health warning states.
- Local/dev Billing Test Harness renders only for platform admins in non-production mode.
- Permission gating for owner/admin vs other roles.
- Active workspace label and checkout scope render correctly when multi-workspace is enabled.
- Optional credit wallet balance and ledger rendering.

### 12.3 Playwright E2E tests

Use mocked Stripe redirects for CI and real Stripe test mode for local/dev release verification:

1. Owner starts checkout and returns success.
2. Owner sees active plan.
3. Declined checkout shows retry.
4. Customer Portal button starts portal session.
5. Platform admin updates base price catalog.
6. Platform admin views tenant billing state.
7. Platform admin simulates past-due and recovery through the test harness.
8. Active workspace checkout attaches to the selected workspace.
9. Tenant invoice payment flow still works.
10. Public ad checkout still works.

### 12.4 Visual regression

Capture desktop and mobile screenshots for:

- Organization -> Billing empty/trial state.
- Billing active subscription state.
- Billing past-due state.
- Billing history table.
- Billing complete return page.
- Platform Base Price Console.
- Platform Tenant Detail Billing card.
- Billing Health page.

Pass criteria:

- No text overlap.
- Money values fit on mobile.
- CTA buttons remain visible and readable.
- No raw IDs appear in primary UI.
- Style matches existing Velvet Elves professional tool aesthetic.

---

## 13. Security, Compliance, and Audit

### 13.1 PCI scope

- Use Stripe Checkout and Customer Portal only.
- Do not collect card data inside Velvet Elves.
- Do not log card data or full payment method details.
- Store only safe payment method summaries returned by Stripe, such as brand and last4 when needed.
- Keep the system in SAQ-A style scope.

### 13.2 Key safety

- Local/dev must use Stripe test keys only.
- Production live keys must be separate and never documented in markdown.
- UI must show test/live mode in platform health surfaces.
- Prevent live checkout until launch readiness is approved.
- Webhook signatures must be verified before dispatch.

### 13.3 Authorization

- Tenant owners (`is_tenant_owner`) and Admins manage their own active workspace billing.
- Platform admins manage cross-tenant billing.
- Platform admins acting on behalf of a tenant must choose the tenant explicitly and create audit entries that identify both platform admin and target tenant.
- Staff roles may view plan/seat info only as approved.
- Client, FSBO, Vendor, and public users cannot access platform billing.
- Public pay links remain token-scoped for tenant invoice and ad-order payment only.
- Billing reads and writes must resolve against the active workspace/tenant, not a stale user home tenant, whenever multi-workspace support is enabled.

### 13.4 Audit logging

Audit these actions:

- Base price create/update/deactivate/sync.
- Checkout session started.
- Customer Portal session started.
- Subscription status changed from webhook.
- Entitlement changed.
- Manual override added/changed/removed.
- Credit granted/adjusted/refunded, if enabled.
- Billing key mode or webhook health warnings acknowledged, if implemented.
- Local/dev Billing Test Harness simulations and resets.

### 13.5 Data retention and support

Provide a support details drawer with:

- Tenant name.
- Billing customer ID.
- Subscription ID.
- Last checkout session ID.
- Last webhook event ID.
- Active price key.
- Billing state.

This drawer is hidden from normal users unless they are owner/admin or platform admin.

---

## 14. Deployment and Environment Plan

### 14.1 Local

- Use Stripe test keys.
- Use Stripe CLI or ngrok for webhook forwarding.
- Seed base price catalog.
- Sync Stripe test Prices from platform-admin console or setup command.
- Show local/dev test-mode panel.
- Enable Billing Test Harness for platform admins.

### 14.2 Dev server

- Use Stripe test keys.
- Configure a stable dev webhook endpoint.
- Keep base prices editable.
- Enable Jake review accounts.
- Keep health page visible to platform admins.
- Enable Billing Test Harness only if the environment is clearly marked non-production.

### 14.3 Production prelaunch

- Keep feature flag off or read-only.
- Create live Stripe Products/Prices only after Jake approves pricing.
- Do not expose live checkout until launch checklist is complete.
- Confirm Billing Test Harness endpoints return 404 or 403.
- Run full regression against tenant invoice payments and advertising checkout.

### 14.4 Launch

- Enable production billing for selected tenants or all new tenants based on rollout decision.
- Monitor billing health.
- Monitor subscription webhook failures.
- Keep platform overrides available for support.

---

## 15. Launch Readiness Checklist

The payment system is launch-ready when all of the following are true:

1. Jake can review and adjust base prices without code changes.
2. Owner/Admin can complete Stripe test subscription checkout from frontend.
3. Billing page updates after checkout through webhook reconciliation.
4. Failed payment path is visible and recoverable from frontend.
5. Customer Portal works from frontend.
6. Subscription invoice history is visible from frontend.
7. Entitlements and seat limits reflect subscription state.
8. Platform admin can inspect tenant billing state from frontend.
9. Platform admin can diagnose webhook/catalog/subscription issues from frontend.
10. Tenant invoice payments still work end to end.
11. Advertising checkout still works end to end.
12. Credit wallet works end to end if included in first release.
13. No card data is handled by Velvet Elves.
14. No live Stripe key is used in local/dev.
15. All Stripe events are idempotent.
16. No raw IDs appear in primary tester workflows.
17. Mobile and desktop UI are visually stable.
18. Automated backend, frontend, and E2E tests cover the main success/failure paths.
19. A non-developer tester can run the UAT guide without terminal/database/Stripe Dashboard steps after preflight.
20. Production live checkout remains gated until final pricing and legal/finance policy are approved.
21. Billing Test Harness is unavailable in production.
22. Active-workspace billing behavior is verified when multi-workspace is enabled.

---

## 16. Open Decisions for Jake

These decisions can remain open while building test-mode mechanics, but they must be resolved before live launch:

1. Final Solo base price.
2. Final Team base price.
3. Whether Enterprise is manual-only or checkout-enabled.
4. Monthly-only vs annual plan option.
5. Trial length and whether a card is required for trial.
6. Seat limits per plan.
7. Whether staff seats are billed as a quantity in Stripe or enforced only inside Velvet Elves for the first version.
8. Grace period for failed subscription payments.
9. What features, if any, become restricted during past-due state.
10. Whether AI usage is included, metered, credit-based, or read-only at launch.
11. Whether to ship credit wallet before launch or later.
12. Credit conversion formula, if any.
13. Refund policy for subscriptions and credit packs.
14. Tax handling and Stripe Tax decision.
15. Whether platform fees apply to tenant-created invoices.
16. Whether advertising billing stays independent from SaaS billing.
17. Whether vendor organizations need their own subscription plan in the first release.
18. Whether plan names remain `solo`, `team`, `enterprise` or expand later.
19. Which roles may view billing but not manage it.
20. Whether Customer Portal can allow cancellation/plan change directly, or only payment method/invoice management.
21. Whether card-on-file trials should be introduced later, or trial should remain local until a paid checkout starts.
22. Whether local/dev Billing Test Harness should be available on shared dev for Jake's review accounts, or limited to internal QA accounts.

---

## 17. Recommended Build Order

### Phase 0: preserve and document existing rails

Goal: make sure the current payment system remains stable.

Deliverables:

- Current payment regression checklist.
- Stripe local/dev preflight screen or documented health output.
- Existing invoice/ad-order payment tests passing.

### Phase 1: base price catalog and platform billing foundation

Goal: store provisional pricing safely and prepare Stripe subscription checkout.

Deliverables:

- Price catalog table.
- Billing customer/subscription/invoice tables.
- Platform price service.
- Platform-admin Base Price Console.
- Stripe test Price sync.
- Platform Billing Health route/sidebar foundation.

### Phase 2: subscription checkout and return UX

Goal: let a workspace owner complete a test subscription checkout.

Deliverables:

- Billing APIs.
- Organization -> Billing UI.
- Stripe subscription Checkout.
- Stripe returns to `Organization -> Billing`; optional `/billing/complete` and `/billing/canceled` redirect/status shells.
- Customer Portal session.

### Phase 3: subscription webhooks and entitlements

Goal: make Stripe state drive Velvet Elves billing state.

Deliverables:

- Subscription webhook handlers.
- Billing mirrors.
- Entitlement service.
- Seat-limit integration.
- Past-due/grace/restricted state handling.

### Phase 4: platform operations and QA readiness

Goal: make the system testable and diagnosable by non-developers.

Deliverables:

- Platform Billing Health page.
- Platform Tenant Detail Billing card.
- Manual overrides.
- Local/dev Billing Test Harness.
- Full UAT guide.
- Playwright test coverage.

### Phase 5: optional credit wallet

Goal: test AI/usage credits only if Jake wants credit-based pricing before launch.

Deliverables:

- Credit wallet and ledger.
- Credit pack checkout.
- Tenant-visible usage/credit UI.
- Refund/reversal handling.

### Phase 6: live launch preparation

Goal: switch from test-mode mechanics to approved production billing.

Deliverables:

- Final price approval.
- Live Stripe Product/Price creation.
- Live webhook endpoint verification.
- Legal/tax/refund policy confirmation.
- Production feature flag rollout.

---

## 18. Acceptance Definition

This plan is successful when Jake can sit with a tester, open only the Velvet Elves frontend, and validate the full payment system in test mode:

- Configure or review base prices.
- Subscribe a workspace through Stripe Checkout.
- Return to Velvet Elves and see the active plan.
- View platform invoice history.
- Manage payment method through Stripe Portal.
- Recover from failed payment.
- Confirm entitlements and seat limits.
- Confirm existing client invoice payments still work.
- Confirm advertising checkout still works.
- Confirm billing health and webhook status from platform admin UI.

The system should feel like a professional real-estate operations tool, not a developer demo. The user should never need to know what a webhook, UUID, Stripe Price ID, or database row is unless they intentionally open support details.
