# Milestone 5.2 — Payment Processing
## Comprehensive Implementation Plan

| | |
| --- | --- |
| Milestone | **5.2 — Payment Processing** (Week 18, 2026-07-06 → 2026-07-12) |
| Phase | Phase 5 — Dashboards, Payments & Profiles |
| Plan version | 1.1 (2026-05-25 — drafted post-M4.3 completion; revised same-day to correct source citations, replace nonexistent `audit_log_service` / `CommunicationChannel.SYSTEM` references with the real `audit_service` + free-form `channel` string, drop the multi-provider abstraction in favour of a single-provider Stripe wrapper, fix migration timestamp ordering, replace single `triggers_task_completion_id` FK with `invoice_task_links` join table, defer webhook side effects to BackgroundTasks for fast 200, remove misleading "EM received" trigger example, bump Stripe SDK pin to current major) |
| Authoritative sources | `milestones.txt` §5.2 · `requirements.txt` §1.2 (RBAC payment toggles), §2.5 (Payment Processing), §7.7 (Payment Module Stripe), §10.3 (Audit & Compliance Logging), §8.1a (AI provider abstraction pattern — referenced as the analogue, not as a payments mandate) · `SYSTEM_DESIGN.md` §1.4 (Multi-tenant architecture), §2.4 (RLS policies), §3.3 (Permission Matrix), Appendix C row "Per-intake pricing" · `MULTI_TENANCY_IMPLEMENTATION_PLAN.md` §4.5 (RLS activation) · `MILESTONE_5_1_IMPLEMENTATION_PLAN.md` §2.2 (declares payment widget owned by M5.2) |
| Approved HTML references | None for this milestone — payment surfaces are net-new and must be designed in-flight against `STYLE_GUIDE.md` and the visual-consistency anchors below. |
| Visual-consistency anchors | Admin Dashboard (`/dashboard/admin`), Active Transactions workspace (`/transactions`), All Documents (`/documents`), AI Email Review (`/ai-emails`), Settings (`/settings`) — keep the quiet "professional tool" card aesthetic per `[[feedback_tool_vs_dashboard_aesthetic]]`. |
| External dependencies | Stripe API account + restricted API keys (test + live), Stripe Connect platform onboarding (for commission payouts), webhook endpoint secret. Per `milestones.txt` Key Dependency #2 these must be available by Week 18. |

---

## 1. Executive Summary

Milestone 5.2 ships **money movement** for Velvet Elves: the ability for an internal user (Agent, TC, Team Lead, Admin — gated by Admin toggle) to invoice an external party, collect funds via Stripe, refund those funds, track receivables and payouts inside the platform, and have those money events both **trigger workflow updates** (e.g., "Compliance fee paid → mark fee task complete") and **report up to the dashboards built in 5.1**.

A naming note: throughout this document **"TC"** is shorthand for the **`UserRole.TRANSACTION_COORDINATOR`** role whose stored value is `"TransactionCoordinator"` (legacy spec text — including `requirements.txt` §1.2b — calls this role "Elf (Transaction Coordinator)"). All role checks in code must use the enum, not the string "TC".

The milestone has four functional pillars:

1. **Stripe integration layer.** Direct Stripe integration via the `stripe` Python SDK with a thin internal wrapper module (`app/services/stripe_client.py`) that centralises key loading, idempotency-key construction, and webhook signature verification — **not** a generalised multi-provider Protocol/registry. Requirements §7.7 names Stripe as *the* payment module; unlike AI (§8.1a, which mandates both OpenAI and Claude), there is no requirement for a second processor. The wrapper keeps the seams tidy for a future swap without spending MVP time on abstraction surface area we do not need. Card data never touches our servers — collection is exclusively via **Stripe Checkout (hosted redirect)**, so we inherit PCI SAQ-A scope. No `client_secret` is handled in our frontend (that would be Stripe Elements, which is out of scope per §4.5).
2. **Invoicing & payment records.** First-class `invoices`, `invoice_line_items`, `payments`, `refunds`, and `commission_payouts` tables, tenant-scoped under RLS, audit-logged on every write, with Fernet encryption applied to PII fields per `[[project_ve_pii_fernet_at_rest]]`.
3. **Payment-triggered workflow.** A dispatcher switching on Stripe webhook event types marks linked tasks complete (e.g., "Collect compliance fee paid → mark fee task complete"), transitions transaction sub-state where applicable via the existing M2.1 status-update hook, and emits notifications + `channel='system'` communication-log entries consistent with `[[project_ve_client_workspace_buildnotes]]`. **EM (Earnest Money) is explicitly NOT in this path** — EM is escrow-regulated and never flows through Stripe (see §2.2 and §5.E).
4. **Reporting + access control.** A `payment_access_policy` table lets the Admin toggle invoicing/refund/payout capability on/off per role (Agent, TC, Team Lead) as `requirements.txt` §1.2 mandates. Dashboard payment widgets (Solo Agent, Team Leader, Admin) consume new aggregation endpoints; the FSBO/Client workspaces gain a read-only "Payments" section.

The milestone is **bounded** — it is intentionally NOT a full general ledger. Accounting integration is a documented hook (`POST /api/v1/payments/accounting-events` outbound webhook) for the future "Specific CRM integrations" item on the post-MVP roadmap.

Every deliverable in `milestones.txt` §5.2 maps to an explicit workstream item, file path, and acceptance test below.

---

## 2. Scope

### 2.1 In scope — `milestones.txt` §5.2 deliverables

| # | Deliverable | Workstream |
| --- | --- | --- |
| 1 | Stripe API integration: secure credit-card processing, transaction fee collection, commission payouts | §5.A + §5.B · Slice 1 |
| 2 | Invoicing system (create, send, track invoices) | §5.C · Slice 2 |
| 3 | Payment tracking UI (payments, refunds, history) | §6.B + §6.C · Slice 2–3 |
| 4 | Payment-triggered task / status updates | §5.E · Slice 3 |
| 5 | Admin payment access controls (on/off per role) | §5.F + §6.E · Slice 1 + Slice 4 |
| 6 | Payment reporting in dashboards | §5.G + §6.D · Slice 4 |
| 7 | Payment hooks for future accounting integration | §5.H · Slice 4 |
| 8 | Security testing for payment flows (PCI compliance) | §10.4 · Slice 5 |

### 2.2 Explicitly excluded (do **not** scope-creep)

- **Platform SaaS billing** (charging tenants for seats/plans). The `tenants.plan` / `seat_limit` / `trial_ends_at` fields exist for that, but tenant subscription billing is out of scope here — it remains a documented future hook.
- **Advertising / ad-slot billing** — owned by Milestone 6.2.
- **Tax document generation** (1099-K, year-end statements) — post-MVP.
- **Full double-entry general ledger** — we record payment events and emit an outbound hook; downstream GL/QuickBooks/Xero integration is post-MVP.
- **In-product agent KYC / Stripe Connect onboarding UI beyond the minimum** required to receive a single brokerage payout. Multi-agent Connect express onboarding (each agent has their own connected account) is post-MVP; for MVP the brokerage (tenant) is the single payout destination and commission splits are recorded internally.
- **Cryptocurrency, ACH micro-deposit verification, wire instructions surfacing.** Cards-only for MVP via Stripe Checkout. ACH appears only as a Stripe-native bank-transfer option on the Checkout page if Stripe enables it on the account — no custom plaid/bank-link UI.
- **Earnest money escrow processing.** Real-estate EM goes to a regulated escrow account, NOT to Stripe. The platform records an EM *acknowledgment* (date, amount, holder) for workflow purposes — it does NOT collect EM funds.
- **Profile editor expansion, brokerage profile, AI checklist generator** — owned by Milestone 5.3.

### 2.3 Boundary with adjacent milestones

| Provides upstream of 5.2 | Already shipped |
| --- | --- |
| Tenant model + RLS isolation (payment tables must be tenant-scoped) | M1.2 / multi-tenancy hardening |
| Role hierarchy + permission middleware (Agent/TC/TeamLead/Attorney/Admin/Client/FSBO/Vendor) | M1.3 (`app/models/enums.py::UserRole`, `role_has_permission`) |
| Transaction model + statuses + key dates (payments reference transactions; "EM received" updates a key date) | M2.1 |
| Task model + completion APIs (payment events complete tasks) | M2.2 |
| Communication log (payment notifications log to comm log) | M4.1 (`communication_logs.channel` already enum-includes `system`) |
| AI Email Automation (payment receipt emails reuse the email infra) | M4.2 |
| Dashboard aggregator + widget shell (payment widget plugs into existing command grid) | M5.1 (`dashboard_aggregator.py`, `CommandGrid`, `MetricCard`) |
| Audit log infra (every payment write audited) | M1.2 / `app/models/audit_log.py` |
| PII encryption helpers (Fernet `_safe_decrypt`) | per `[[project_ve_pii_fernet_at_rest]]` |
| Notification preferences | M4.1 |

| Consumed downstream of 5.2 | Owned by |
| --- | --- |
| Profile reporting tab adds payment reports | M5.3 (extend existing `/api/v1/analytics/profile-report`) |
| White-label re-themed payment surfaces (logo on invoice PDF, brand color on Checkout) | M6.1 |
| Ad-purchase Stripe checkout (reuse this module's Stripe client + webhook handler) | M6.2 |
| Final security audit, PCI verification | M7.1 |

---

## 3. Foundation Audit (what exists vs. what we add)

### 3.1 Backend — current state (relative to payments)

| Existing | Notes |
| --- | --- |
| `app/services/dashboard_aggregator.py` | Computes `pending_gci` / `pending_volume` from `commission_pct` × active purchase prices. **Pipeline-only — no actual collected revenue.** Need to differentiate pipeline (expected) vs collected (actual) in 5.2 dashboard widgets. |
| `app/models/tenant.py` | Has `plan`, `seat_limit`, `trial_ends_at` — for future SaaS billing, **not** in scope here. |
| `app/services/audit_service.py` (`class AuditService`, `await audit.log(user=..., action=..., entity_type=..., entity_id=..., before_state=..., after_state=..., summary=...)`) | Reuse for every payment-write audit. (Note: the file is `audit_service.py` — there is no `audit_log_service.py`.) |
| `app/models/communication_log.py` | `channel` is a **free-form `str` field**, not a Python enum — recent M4.3 work added `'sms'` and `'voice_call'` as conventional values. Payments will emit `channel='system'` entries by the same convention. **There is no `CommunicationChannel.SYSTEM` enum to import.** |
| `app/services/dashboard_aggregator.py` | Currently computes `pending_gci` / `pending_volume` from `purchase_price × dc.currency_default_commission_pct()` — a **flat tenant-wide default** (NOT a per-agent stored `commission_pct`). New "collected" metrics live beside this; we do not modify the pipeline calculation. |
| `app/models/task.py` | `completion_method` is a **free-form `str`** with conventional values (`'phone_call'`, `'email'`, `'e_signature'`, …) — **not an enum.** Adding `'payment'` is a new convention; no migration needed for an enum extension. |
| `supabase/migrations/*` | **No payment tables exist.** Latest existing migration is `20260723090000_client_message_visibility.sql`; the new payments migration must use a later timestamp (see §5.J). |
| `app/services/providers/` (AI providers) | Architectural analogue we *cite* but do **not** duplicate — see Pillar 1 above for the rationale on keeping payments single-provider. |
| `requirements.txt` (backend pip) | `stripe` SDK **not** present — add `stripe>=12,<13` (current major as of plan date; previous-major code samples on the web may need adjustment). |

### 3.2 Frontend — current state

| Existing | Notes |
| --- | --- |
| `components/shared/{CommandGrid,MetricCard,InnerPanel,KpiTile}` (M5.1) | Payment dashboard widgets compose from these — no new primitives needed for the dashboard surface. |
| `components/AppLayout.tsx` (M2.3) | Add a sidebar "Payments" entry under the existing structure (gated by `payment_access_policy`). |
| `pages/Settings.tsx` / Admin Dashboard | Host the role-toggle UI for payment access. |
| `package.json` | `@stripe/stripe-js` and `@stripe/react-stripe-js` are **not** present — add them. Use Stripe Checkout (hosted redirect) as primary collection surface; Elements only if we need an embedded card form. Checkout has zero PCI surface for us. |

### 3.3 Reusable design fragments anchored to the reference pages

- **Invoice list view**: All Documents table layout (sortable columns, status pills, row-level actions). Status pills reuse the semantic tokens from `STYLE_GUIDE.md`: paid (healthy green), open (info blue), past_due (warning amber), failed/refunded (critical red), draft (neutral gray).
- **Invoice detail / payment record drawer**: Transaction expanded-card drawer pattern (3-column grid: details · line items · history timeline).
- **Payment widget on Solo Agent / Team Leader dashboard**: `MetricCard` for "Collected MTD" + small list of "Outstanding invoices" — sits in the existing command grid, NOT a new panel.
- **Admin role-toggle**: Settings page row pattern (label · description · toggle), same as the existing confidence-threshold settings.

---

## 4. Architecture Overview

### 4.1 Stripe client module (single-provider, deliberate)

```
app/services/stripe_client.py    # Thin wrapper: key loading, idempotency-key builder,
                                  # webhook-signature verifier, typed helper methods
                                  # (create_customer, create_checkout_session,
                                  # create_refund, create_transfer).
app/services/stripe_errors.py    # PaymentError hierarchy → mapped to 4xx/5xx in API layer.
```

**Why not a Protocol/registry?** Requirements §7.7 names Stripe as *the* payment module. Unlike AI providers (§8.1a, which mandates BOTH OpenAI and Claude), there is no second-processor requirement. Building a `PaymentProvider` Protocol + `StripePaymentProvider` + `registry.py` for a single implementation is YAGNI within MVP budget. The thin wrapper keeps Stripe-specific imports out of routers and service layers, which is sufficient to swap providers later if the requirement appears. The AI-provider module stays the cited *analogue*, not the cited *mandate*.

If Phase 6+ adds a second processor, the refactor at that point is a 1–2 day mechanical lift, not a re-architecture.

### 4.2 Money movement model

```
[external payer (client/seller)]
        │  Stripe Checkout (hosted page — no card UI in our app)
        ▼
   Checkout Session ──webhook──▶ /api/v1/webhooks/stripe
                                       │ (1) signature verify
                                       │ (2) persist webhook_events row (idempotent)
                                       │ (3) return 200 immediately
                                       ▼
                              background dispatch (FastAPI BackgroundTasks
                              at MVP scale; lift to a queue if SLA tightens)
                                       │
                              ┌────────┼─────────────┐
                              ▼        ▼             ▼
                       update Invoice  complete Tasks   log Communication
                       insert Payment  update Tx state  send Notification
                       audit log       (M2.1 hooks)     (channel='system' string)
                              │
                              ▼
                       emit accounting_event (outbound webhook hook, §5.H)

[brokerage / connected account]
        ▲
        │  Stripe Connect transfer (platform → connected; brokerage is the
        │  single connected account at MVP; per-agent Connect Express
        │  onboarding is post-MVP — see §2.2)
        │
[platform balance]
        (No application/platform fee is collected by Velvet Elves at MVP
         — the platform is the broker's own tooling, not a marketplace.
         If business introduces a fee later, it's added on the
         Checkout Session via `application_fee_amount`. Open question
         flagged in §11 risk #11.)
```

### 4.3 Data flow per pillar

| Pillar | Trigger | Path |
| --- | --- | --- |
| **Collect fee** | Internal user clicks "Send invoice" on a transaction | `POST /api/v1/invoices` → DB row (status=draft) → `POST /api/v1/invoices/{id}/send` → Stripe PaymentIntent + Checkout Session → email to payer with hosted link → webhook on success → mark paid → trigger task |
| **Refund** | Internal user clicks "Refund" on a payment row (must have refund permission) | `POST /api/v1/payments/{id}/refund` → Stripe Refund → DB row (status=pending) → webhook → status=succeeded → audit + notification |
| **Commission payout** | Closing event OR admin manual trigger | `POST /api/v1/commission-payouts` → Stripe Transfer to connected brokerage account → webhook → record payout → dashboard widget updates |
| **Role toggle** | Admin opens settings | `PUT /api/v1/admin/payment-access` → updates `payment_access_policy` row → permission middleware re-checks on next request |

### 4.4 Permissions (extends the M5.1 permission matrix)

| Action | Default allowed roles | Admin can toggle? |
| --- | --- | --- |
| View own transactions' payment history | Agent, TC (assigned), Team Lead, Attorney (assigned matter), Admin | No (always on) |
| Create / send invoice | Agent, Team Lead, TC (only if standalone — `requirements.txt` §1.2b), Admin | **Yes** (per role) |
| Refund a payment | Team Lead, Admin | **Yes** (per role) |
| Trigger commission payout | Admin | **Yes** (can additionally grant to Team Lead) |
| Configure payment access policy | Admin only | No |
| Client / FSBO: view their own invoices + pay them | Client, FSBO | No (always on for the payer) |
| Vendor | No payment surface at all | N/A |

Implementation: a single `payment_access_policy` row per tenant stores the toggle state for the three configurable rows; the existing permission middleware gains a `requires_payment_capability("invoice.create")` decorator that checks role-default → tenant-override → per-user override.

### 4.5 PCI scope

Using **Stripe Checkout** (hosted redirect) for collection keeps us at **PCI SAQ-A** — we never see card data, never store a PAN, never proxy a card field. The only sensitive data the platform stores is the Stripe `customer_id`, `payment_method_id` (tokenized), and `payment_intent_id` strings. The accepted-by-Stripe last-4 + brand may be cached for receipt display.

If a future iteration needs embedded card capture (Stripe Elements), PCI scope upgrades to **SAQ-A-EP** — explicitly out of scope.

### 4.6 AI-vs-human guardrail

Payments are **not** an AI-decided surface. AI may:
- Draft an invoice description / line item text when an agent says "invoice the Young deal for the $495 compliance fee" via the chatbot.
- Summarize "what payments are outstanding for the Smith deal" in the AI chat panel.

AI must NOT:
- Initiate a charge, refund, or payout without explicit human click-through.
- Set or override the payment access policy.
- Decide commission splits.

Consistent with the Attorney guardrail in M5.1 and the AI safeguards in M4.2.

---

## 5. Workstream A — Backend

### 5.A `stripe_client.py` (single-provider wrapper)

| File | Purpose |
| --- | --- |
| `app/services/stripe_client.py` | Thin wrapper. Methods: `create_customer`, `create_checkout_session`, `retrieve_session`, `retrieve_payment_intent`, `create_refund`, `create_transfer`, `verify_webhook_signature`. Loads keys from env at import; `idempotency_key` is **passed in by the caller** (because the right key depends on the action — e.g. the refund-create path uses `f"refund:{refund_id}"` where `refund_id` is generated server-side per request, so a double-clicked "Refund" button does not silently no-op a second legitimate partial refund). |
| `app/services/stripe_errors.py` | `PaymentError`, `PaymentValidationError`, `PaymentProviderError` hierarchy mapped to clean API responses (4xx vs 5xx). User-facing strings are mapped from Stripe error codes — raw Stripe `decline_code` / `failure_message` strings are never returned to the API caller. |

Idempotency-key conventions (caller responsibility):

| Action | Key |
| --- | --- |
| `create_customer` | `f"customer:{tenant_id}:{contact_id}"` (one Stripe Customer per tenant+contact) |
| `create_checkout_session` for an invoice | `f"checkout:{invoice_id}:{send_attempt_n}"` |
| `create_refund` | `f"refund:{refund_id}"` (our `refunds.id` UUID, generated before the Stripe call) |
| `create_transfer` for a commission payout | `f"transfer:{commission_payout_id}"` |

### 5.B Stripe wiring

- New env vars in `.env.example`: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_CONNECT_PLATFORM_ACCOUNT_ID`, `STRIPE_PUBLISHABLE_KEY` (the publishable key is exposed via `GET /api/v1/payments/config` for the frontend; secrets stay server-side only).
- Webhook endpoint: `POST /api/v1/webhooks/stripe`. Pattern:
  1. Verify Stripe signature using `STRIPE_WEBHOOK_SECRET`.
  2. Insert a `webhook_events` row (`stripe_event_id` has a unique index — a duplicate insert is the idempotency check; on conflict do nothing, set `processing_status='skipped_duplicate'`, return 200).
  3. Return **HTTP 200 within ~1 second**, before any side-effect work.
  4. Hand off the actual dispatch to a FastAPI `BackgroundTasks` job (or, if `BackgroundTasks` proves too lightweight under retry load, a `arq`/`Celery`-style worker — call this out as an upgrade hook, not a Slice 3 build).

  **Rationale:** Stripe expects a 2xx within ~10 seconds and will retry otherwise. A synchronous handler that does task completion + comm log + audit + notification + accounting webhook fan-out inside the request will sometimes exceed that window, causing Stripe-driven duplicate processing. The duplicate is *idempotent* (per the unique index in step 2) but burns DB churn and confuses retry logs. Respond fast, defer work.
- Idempotency: every call to Stripe includes a caller-supplied idempotency key (§5.A table). Every webhook handler is additionally idempotent at the row level — `payments.stripe_payment_intent_id`, `refunds.stripe_refund_id`, `commission_payouts.stripe_transfer_id` each carry unique indexes; the dispatcher upserts rather than blind-inserts.
- Test mode flag on `tenants` (`payment_test_mode bool default true`) — gates which API key is used; production tenants are flipped manually by platform admin.

### 5.C Invoicing service — `app/services/invoice_service.py`

- `create_invoice(tenant_id, transaction_id, created_by, line_items[], payer_contact_id, due_date, terms_note, linked_task_ids: list[str] | None)` — returns draft `Invoice`. `linked_task_ids` is a list because a single invoice may complete multiple tasks (e.g., compliance fee + admin fee on the same charge) — see §5.J for the join-table schema.
- `send_invoice(invoice_id, sender_user)` — creates/reuses Stripe Customer, creates Stripe Checkout Session in `mode='payment'`, persists `stripe_checkout_session_id` + `stripe_payment_intent_id` + `checkout_url`, sends an email through the existing M4.1 email service with a "Pay now" button (the hosted Checkout URL). Logs to `communication_logs` as `channel='email'`, `direction='outbound'`.
- `mark_invoice_paid(invoice_id, payment_id)` — called by the webhook dispatcher.
- `void_invoice(invoice_id, reason, user)` — allowed only while `status in ('draft','open')`.
- All writes audit-logged via `await audit.log(user=..., action='create'|'update'|'send'|'void', entity_type='invoice', entity_id=invoice.id, before_state=..., after_state=..., summary='...')` (signature per `app/services/audit_service.py`).

### 5.D Refund service — `app/services/refund_service.py`

- `create_refund(payment_id, amount_cents, reason, user)` — partial or full, only by users with `refund.create`. Generates the refund row UUID **before** calling Stripe so the idempotency key `f"refund:{refund_id}"` is stable across retries (§5.A).
- Webhook dispatcher records terminal status from `charge.refunded` / `refund.updated`.
- **Business choice (not Stripe default):** refund of a fully-paid invoice does NOT auto-reopen the invoice — the invoice stays `paid` with a refunded payment row underneath; reporting differentiates net vs gross. Stripe leaves the invoice-side state to the platform, so this is our policy.

### 5.E Payment event dispatcher — `app/services/payment_event_dispatcher.py`

Handled events and their effects (the dispatcher is a switch on `event.type`, not a pub/sub system; it must be idempotent because Stripe may resend any of these):

| Stripe event | Side effects |
| --- | --- |
| `checkout.session.completed` | Upsert `payments` row, mark invoice paid, complete linked tasks (all rows in `invoice_task_links` for this invoice), insert `communication_logs` row with `channel='system'`, send in-app notification to invoice owner. |
| `payment_intent.succeeded` | Reconcile `payments.status='succeeded'`. Order with `checkout.session.completed` is **not guaranteed** (Stripe may deliver in either order); both handlers must be safe to run first. |
| `payment_intent.payment_failed` | Update payment row status, log failure, notify owner. Do NOT auto-mark invoice past_due (a separate scheduled job, out of scope here, handles aging). |
| `charge.refunded` / `refund.updated` | Upsert refund row, audit, notify. |
| `transfer.created` / `transfer.paid` | Update `commission_payouts.status`. |
| `payout.paid` / `payout.failed` | Inform the brokerage owner (platform → connected account level). |

**Payment-triggered task / status updates** (`milestones.txt` deliverable #4):

- A new join table `invoice_task_links (invoice_id, task_id)` (see §5.J) records 0..N tasks that an invoice marks complete when paid. A single invoice can complete multiple tasks; a single task should typically map to one invoice but the schema does not forbid more.
- On the **first** terminal success event for an invoice (whichever of `checkout.session.completed` / `payment_intent.succeeded` arrives first and finds `invoices.status != 'paid'`), the dispatcher invokes the existing task-completion path as a synthetic system actor with `completion_method='payment'`. **`completion_method` is a free-form `str` on `app/models/task.py:29`, not an enum** — no migration is needed to add the `'payment'` convention, but the value MUST be documented in the model docstring alongside the existing conventional values.
- Transaction-status side effects (e.g., flipping a Tx out of "needs payment" sub-state) reuse the existing M2.1 status-update hook. The dispatcher does NOT independently mutate `transactions.status`.
- **EM (Earnest Money) is explicitly NOT a payment trigger.** Earnest money is regulated escrow and never flows through Stripe (§2.2). The existing "EM Delivered" key date from M2.1 is updated by manual user action or by other workflow events; the payment-event dispatcher never touches it. Earlier drafts of this plan referenced an "EM received" trigger — that was incorrect and has been removed.

### 5.F Payment access policy — `app/models/payment_access_policy.py`

```python
@dataclass
class PaymentAccessPolicy:
    tenant_id: str
    role: UserRole
    can_create_invoice: bool
    can_refund: bool
    can_trigger_payout: bool
    updated_by: str | None
    updated_at: datetime | None
```

- One row per `(tenant, role)`; seeded with the §4.4 defaults on tenant provisioning.
- Permission middleware adds `requires_payment_capability(capability: str)` decorator.
- Admin override stored at `(tenant, user_id)` granularity if per-user override is needed — same table with nullable `user_id` and a unique index on `(tenant, role, user_id)`.

### 5.G Reporting aggregation — extend `app/services/dashboard_aggregator.py`

New functions (NOT a new file — composition):

| Function | Returns | Consumed by |
| --- | --- | --- |
| `payments_collected(tenant, scope, period)` | `{gross_cents, net_cents, count}` where scope ∈ `{me, my_team, tenant}` | Solo Agent / Team Lead / Admin dashboards |
| `outstanding_invoices(tenant, scope, top_n=5)` | List of `{invoice_id, payer, transaction_label, amount_cents, days_outstanding, status}` | Same dashboards |
| `commission_payouts_summary(tenant, scope, period)` | `{paid_cents, scheduled_cents, last_payout_at}` | Solo Agent, Team Lead, Admin |
| `payment_health(tenant)` | `{past_due_count, refunded_count_30d, failed_charge_count_30d, webhook_pending_older_than_5m}` | Admin dashboard health strip |

These are **separate** from the existing `pending_gci` calculation, which today multiplies `purchase_price` × `dc.currency_default_commission_pct()` (a **flat tenant-wide default**, not a per-agent stored field — see [dashboard_common.py:191](velvet-elves-backend/app/services/dashboard_common.py#L191)). `pending_gci` remains the **pipeline expectation**; the new aggregations measure **actual money collected**. The dashboard must visually distinguish the two ("Expected (pipeline)" vs "Collected"). If `STYLE_GUIDE.md` doesn't already cover this terminology, add it.

Out-of-scope cleanup that a future milestone may want to consider: making `commission_pct` per-agent (today it isn't) so "Expected" reflects real splits. That work is **not** in M5.2.

### 5.H Outbound accounting hook — `app/services/accounting_event_emitter.py`

For each terminal payment event, emit a JSON event to any tenant-configured webhook URL stored at `tenants.settings_json['accounting_webhook_url']`. Event shape:

```json
{
  "id": "evt_...",
  "tenant_id": "...",
  "kind": "payment.succeeded | refund.succeeded | payout.paid",
  "occurred_at": "...",
  "payment": { ... canonical payment summary ... },
  "links": { "invoice_id": "...", "transaction_id": "..." }
}
```

- HMAC-SHA256 signed using `tenants.settings_json['accounting_webhook_secret']`.
- Retry policy: 3 attempts with exponential backoff, then dead-letter to `accounting_dead_letter` table for admin review.
- This is the **hook only** — no specific QuickBooks/Xero adapter ships in MVP.

### 5.I API contract

```
GET    /api/v1/payments/config                  → { publishable_key, currency, supported_payment_methods }
GET    /api/v1/invoices?scope=me|team|tenant&status=&transaction_id=&page=
POST   /api/v1/invoices                          (requires invoice.create)
GET    /api/v1/invoices/{id}
PUT    /api/v1/invoices/{id}                     (only while draft)
POST   /api/v1/invoices/{id}/send                (requires invoice.create)
POST   /api/v1/invoices/{id}/void                (requires invoice.create)
GET    /api/v1/payments?scope=&period=&page=
GET    /api/v1/payments/{id}
POST   /api/v1/payments/{id}/refund              (requires refund.create)
GET    /api/v1/commission-payouts?scope=&period=
POST   /api/v1/commission-payouts                (requires payout.trigger)
GET    /api/v1/dashboard/payments-summary?scope=
GET    /api/v1/admin/payment-access              (Admin only)
PUT    /api/v1/admin/payment-access              (Admin only)
POST   /api/v1/webhooks/stripe                   (public, signature-verified)

# Client / FSBO read-side
GET    /api/v1/client/invoices                   (filtered to the caller's payer scope)
GET    /api/v1/client/invoices/{id}/pay-link     (redirect token to Stripe Checkout)
```

All non-webhook endpoints respect tenant RLS; webhook handler enters Supabase as service role with explicit tenant_id check from the resolved invoice.

### 5.J Database migration — `supabase/migrations/20260726090000_milestone_5_2_payments.sql`

**Filename timestamp note:** the latest existing migration is `20260723090000_client_message_visibility.sql`. Supabase applies migrations in filename order, so a new migration MUST use a timestamp strictly greater than the latest existing one. `20260726090000` is the convention here; bump if other migrations land first.

Tables (all with `tenant_id uuid not null` + RLS policy mirroring existing tables, all with `created_at` / `updated_at`):

| Table | Key columns |
| --- | --- |
| `stripe_customers` | `id`, `tenant_id`, `contact_id`, `stripe_customer_id`, `email_encrypted` (Fernet per `[[project_ve_pii_fernet_at_rest]]`). Unique on `(tenant_id, contact_id)`. |
| `invoices` | `id`, `tenant_id`, `transaction_id`, `created_by_user_id`, `payer_contact_id`, `status` (draft/open/paid/void/uncollectible), `currency` CHAR(3) DEFAULT 'usd' CHECK = 'usd', `subtotal_cents` bigint, `tax_cents` bigint DEFAULT 0, `total_cents` bigint, `due_date`, `terms_note`, `stripe_checkout_session_id`, `stripe_payment_intent_id`. **No** `triggers_task_completion_id` — link tasks via `invoice_task_links`. |
| `invoice_line_items` | `id`, `invoice_id`, `description`, `quantity`, `unit_amount_cents`, `subtotal_cents`, `sort_order` |
| `invoice_task_links` | `invoice_id` (FK), `task_id` (FK), `created_at`. PK `(invoice_id, task_id)`. Many-to-many: one invoice may complete several tasks; one task referenced by at most one open invoice in practice but the schema does not enforce that. |
| `payments` | `id`, `tenant_id`, `invoice_id` (nullable — direct charges allowed), `stripe_payment_intent_id` UNIQUE, `stripe_charge_id`, `amount_cents`, `currency`, `status`, `payment_method_brand`, `payment_method_last4`, `received_at` |
| `refunds` | `id`, `tenant_id`, `payment_id`, `stripe_refund_id` UNIQUE, `amount_cents`, `reason`, `status`, `initiated_by_user_id` |
| `commission_payouts` | `id`, `tenant_id`, `transaction_id`, `payee_user_id`, `amount_cents`, `stripe_transfer_id` UNIQUE, `status`, `paid_at`, `initiated_by_user_id` |
| `payment_access_policy` | `tenant_id`, `role` (varchar — stores `UserRole` enum string value, e.g. `'Agent'`, `'TransactionCoordinator'`, `'TeamLead'`), `user_id` (nullable for per-user override), `can_create_invoice`, `can_refund`, `can_trigger_payout`, `updated_by_user_id`, `updated_at`. Unique on `(tenant_id, role, user_id)` (with `user_id` allowing NULL — partial unique index to make NULLs distinct as needed). |
| `webhook_events` | `id`, `tenant_id` (nullable until resolved), `provider` ('stripe'), `stripe_event_id` UNIQUE, `event_type`, `payload_jsonb`, `processing_status` (pending/processed/failed/skipped/skipped_duplicate), `received_at`, `processed_at`, `attempts`, `error_text` |
| `accounting_dead_letter` | `id`, `tenant_id`, `payment_id`, `event_payload_jsonb`, `last_error`, `attempts`, `created_at` |

Audit logging is performed at the **service layer** via `AuditService.log(...)` (see §5.C); we do not add SQL audit triggers. This matches the existing M2.1 / M4.x pattern in the codebase.

RLS: tenant_id check on every table; payer (Client/FSBO) read access on `invoices` and `payments` scoped by `payer_contact_id` via the existing `client_workspace` linkage table per `[[project_ve_client_workspace_buildnotes]]`. Recreate the **same RLS conventions** used in `20260511094000_rls_tenant_isolation.sql` so behavior matches the rest of the schema.

Seed: `payment_access_policy` rows for every existing tenant × role (Agent, TransactionCoordinator, TeamLead) at the §4.4 defaults, run inside the same migration transaction. Also register a tenant-provisioning hook so future tenants get the same seed automatically (mirror the M4.3 `seed_vendor_email_templates` pattern).

---

## 6. Workstream B — Frontend

### 6.A Routing

```
/payments                       — Payments list (invoices + payments tabs); sidebar entry, gated
/payments/invoices/new          — Create invoice modal (or full page if multi-line)
/payments/invoices/:id          — Invoice detail / payment history drawer
/payments/payments/:id          — Payment detail (refund action lives here)
/payments/payouts               — Commission payouts (Team Lead / Admin only)
/admin/payment-access           — Role toggle settings (Admin only) — lives under existing Admin section
/client/invoices                — Client-facing invoices list (read + pay)
/client/invoices/:id            — Client invoice detail with "Pay" button → Stripe Checkout redirect
```

### 6.B `/payments` workspace

- Reuse Active Transactions filter/tab/search pattern: tabs = "All Invoices", "Open", "Paid", "Past Due", "Refunded", "Drafts"; sort by date / amount / payer; search by payer name, transaction, invoice number.
- Quiet "professional tool" aesthetic per `[[feedback_tool_vs_dashboard_aesthetic]]` — no KPI strip on top, just the table.
- Row actions: View, Send (if draft), Resend (if open), Refund (if paid, gated), Void (if draft/open).
- Empty state: "No invoices yet — create your first invoice from a transaction."

### 6.C Invoice creation modal

- Three entry points: (1) `/payments` "+ New Invoice" CTA; (2) Active Transactions expanded card → "Invoice this deal" footer action; (3) AI chatbot quick action "Invoice the Young deal $495 compliance fee" → opens the modal pre-filled.
- Fields: payer (autocomplete over transaction parties / contacts), transaction (defaulted from entry context), line items (description + qty + unit price), due date, terms note, optional checkbox "Mark task X complete when this invoice is paid" (lists open tasks on the transaction).
- Submit: "Save draft" OR "Send now" — the latter calls send immediately and shows a toast with the hosted Checkout URL for copy/paste fallback.
- AI suggestion: a small "✦ Suggest from history" link offers prior invoice line items for the same transaction type (read-only suggestion, human accepts).

### 6.D Dashboard payment widgets

- **Solo Agent dashboard** (`/dashboard/agent`): add to the existing command grid a `MetricCard` "Collected this month" + an `InnerPanel` "Outstanding invoices" (top 5 with row tap → invoice detail). Render only if the user has `invoice.create` OR has any payment history.
- **Team Leader dashboard** (`/dashboard/team`): team-scoped versions of the same two widgets + a `MetricCard` "Commission payouts this period".
- **Attorney dashboard**: no payment widget — payments are not an attorney surface.
- **Admin dashboard**: a dedicated "Payments health" panel — past-due count, failed-charge count (30d), refunded count (30d), webhook backlog (count of `webhook_events` where `processing_status='pending'` older than 5 min).
- **FSBO / Client workspace**: read-only "Payments" section listing their invoices with status + "Pay now" CTA where applicable.

All widgets pull from `GET /api/v1/dashboard/payments-summary?scope=`.

### 6.E `/admin/payment-access`

- Single page; mirrors the existing confidence-threshold settings layout (label · description · toggle per row).
- Rows: for each of Agent, TC, Team Lead — three toggles (Create Invoice, Refund, Trigger Payout).
- "Per-user overrides" expandable section below — small table of any rows where `user_id is not null`.
- Save button is sticky-footer; changes are atomic per row (PATCH-style on toggle, with optimistic UI + rollback on error).

### 6.F Client/FSBO pay flow

- `/client/invoices/:id` shows the invoice (line items, total, due date) and a "Pay $X.XX securely" primary button.
- Click → server-side fresh Checkout Session creation (`POST /api/v1/client/invoices/:id/pay-link`) → 302 to Stripe-hosted Checkout. **No card fields rendered in our app.**
- Stripe's `success_url` returns to `/client/invoices/:id?paid=1`; the page polls/listens for the webhook-driven status update for ≤ 30 s before falling back to "Processing — we'll email confirmation."
- Receipt is sent by Stripe by default; we additionally append the invoice line items in our own confirmation email via the M4.1 email service.

### 6.G Components

| New shared component | Used in |
| --- | --- |
| `components/payments/InvoiceStatusPill.tsx` | Tables, drawers, dashboard widget |
| `components/payments/MoneyAmount.tsx` | Everywhere — wraps `Intl.NumberFormat` with tabular-nums per `STYLE_GUIDE.md` |
| `components/payments/InvoiceLineItemEditor.tsx` | Create / edit invoice modal |
| `components/payments/RefundDialog.tsx` | Payment detail page |
| `components/payments/StripeCheckoutRedirect.tsx` | Tiny wrapper for `/client/invoices/:id` redirect handoff |
| `hooks/usePaymentAccess.ts` | Returns `{canCreateInvoice, canRefund, canTriggerPayout}` resolved from `/api/v1/users/me` payload (extend that endpoint to include resolved payment capabilities) |

### 6.H Sidebar entry

Add a "Payments" item in the existing sidebar grouping (between "Workflow" and "Intelligence"), only rendered if the user has any payment capability OR if any historical payment exists for the user/team. Customer-shell (Client/FSBO) gets the same entry under their existing nav per `[[project_ve_client_workspace_plan]]`.

---

## 7. Workstream Tickets — Sequenced Backlog

Total: **7 working days** within the calendar week (Mon–Sun 2026-07-06 → 2026-07-12). Treat Day 7 as buffer + manual QA.

### Slice 0 — Tooling / Guardrails (Day 0, pre-week)

- [ ] Confirm Stripe account is created, restricted API keys generated (`rk_test_...` for dev, `rk_live_...` for prod with only the scopes we use: PaymentIntents, Checkout, Refunds, Transfers, Customers, Webhook Endpoints — nothing more), Stripe CLI installed for local webhook forwarding, Stripe Connect onboarded for the platform.
- [ ] Add `stripe>=12,<13`, confirm `cryptography` is present, confirm `httpx` is present (used by the M4.x email/integration code; reuse for outbound accounting webhooks).
- [ ] Add `@stripe/stripe-js` to frontend `package.json` (only needed if we add Elements later — for Checkout-only MVP we technically don't need the JS SDK, just the redirect URL. Keep the dep so the frontend can call `loadStripe()` for any embedded surface added post-MVP. Skip if you want a zero-dep MVP).
- [ ] Add `.env.example` entries: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_CONNECT_PLATFORM_ACCOUNT_ID`, `STRIPE_PUBLISHABLE_KEY`.
- [ ] Decide and document the **platform-fee policy** (see §11 risk #11) — yes/no, and if yes, the % or fixed amount. Block Slice 4's commission-payouts wiring until decided.

### Slice 1 — Schema + Stripe wrapper + Policy (Days 1–2)

- [ ] Write & apply migration `20260726090000_milestone_5_2_payments.sql` (§5.J — bump timestamp if other migrations land first).
- [ ] Implement `app/services/stripe_client.py` (§5.A) covering Customer / Checkout Session / Refund / Transfer / webhook signature verification.
- [ ] Implement `payment_access_policy` model + repository + `requires_payment_capability` middleware (§5.F).
- [ ] Backend tests: Stripe client unit tests against `stripe-mock` or VCR fixtures; policy middleware tests; **`test_payment_rls_isolation.py`** asserting cross-tenant `/invoices/{id}` returns 404 (mirrors existing isolation tests).

### Slice 2 — Invoicing + Send Flow (Days 2–3)

- [ ] `app/services/invoice_service.py` (§5.C) — create, send, void, mark-paid.
- [ ] `POST/GET/PUT /api/v1/invoices*` endpoints.
- [ ] Frontend `/payments` list page (§6.B) + invoice creation modal (§6.C).
- [ ] Backend tests for CRUD + send flow (mocked Stripe).
- [ ] Frontend render tests for list + modal.

### Slice 3 — Webhook + Payment Event Dispatcher (Days 3–5)

- [ ] `POST /api/v1/webhooks/stripe` endpoint with signature verification and `webhook_events` idempotency.
- [ ] `payment_event_dispatcher.py` (§5.E) — wire all six event types.
- [ ] Task-completion-on-payment integration (§5.E final paragraph).
- [ ] Refund flow (§5.D) end-to-end including UI.
- [ ] Manual test via Stripe CLI `stripe trigger checkout.session.completed`.

### Slice 4 — Dashboard Widgets + Admin Toggles + Accounting Hook (Days 5–6)

- [ ] Extend `dashboard_aggregator.py` with §5.G functions; add `GET /api/v1/dashboard/payments-summary`.
- [ ] Render widgets on Solo Agent, Team Lead, Admin dashboards (§6.D); explicitly differentiate "Expected" vs "Collected".
- [ ] `/admin/payment-access` page (§6.E) + backend endpoints.
- [ ] `accounting_event_emitter.py` (§5.H) + dead-letter table + simple admin view of dead-letter rows.
- [ ] Commission payouts page `/payments/payouts` + Stripe Transfer wiring.

### Slice 5 — Client/FSBO Pay Flow + Security Hardening (Days 6–7)

- [ ] `/client/invoices` + `/client/invoices/:id` + pay-link redirect endpoint (§6.F).
- [ ] PCI checklist walkthrough: confirm no card data in logs, no card data in audit logs, no card data in error messages, Stripe Checkout used everywhere, webhook secret loaded from env.
- [ ] OWASP focused review on payment endpoints (IDOR on `/invoices/{id}`, mass-assignment on invoice PUT, replay on `/refund`).
- [ ] Run security review skill (`/security-review`) on the diff.
- [ ] End-to-end test: create invoice → send → pay via Stripe test card → webhook fires → task completes → dashboard widget updates → email sent → audit log written.

---

## 8. Money & Numeric Conventions

- All monetary values stored as **integer cents** (no floats) in PostgreSQL `bigint`.
- All API responses include both `amount_cents` (integer) and `amount_display` (formatted string with currency code) to avoid client-side float rounding.
- Currency: USD-only at MVP (constant `'USD'`); column exists for future expansion but is checked == `'USD'` at boundary.
- Display: `Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })` with `tabular-nums` per `STYLE_GUIDE.md`.
- Timezone: all timestamps UTC in DB; render in user's tenant timezone with the existing date helper.

---

## 9. Visual Consistency Rules

1. **Quiet aesthetic** — payment surfaces are operational tools. Use white card backgrounds, neutral table rows, semantic status pills. No KPI strip atop the `/payments` list, no DashboardCard chrome on the working pages — per `[[feedback_tool_vs_dashboard_aesthetic]]`.
2. **Action buttons** — explicit verbs: "Send invoice", "Refund $X", "Trigger payout", "Mark as paid". Avoid the alert-card anti-pattern in `[[feedback_alert_card_clickability]]` — never make a whole row clickable as a single ambiguous target; every row has a "View" button + secondary actions.
3. **Status pills** — reuse the M5.1 semantic tokens; never invent new colors.
4. **Money typography** — `tabular-nums lining-nums` always; right-align amounts in tables; `$0.00` baseline (never `$0` or `$-`).
5. **Audit-trail visibility** — every payment detail page has a "Activity" timeline section showing audit + communication-log entries for that invoice/payment, matching the Transaction History pattern from M2.1.
6. **No celebratory chrome on success** — a paid invoice shows the paid pill, the payment row, and the receipt; no confetti, no big green hero. This is a professional tool.

---

## 10. Testing Strategy

### 10.1 Backend unit + integration

- `pytest` suites:
  - `test_payment_providers.py` — Stripe provider methods against `stripe-mock` or recorded fixtures.
  - `test_invoice_service.py` — CRUD, send flow, paid transitions, void rules.
  - `test_refund_service.py` — full + partial, permission checks.
  - `test_payment_event_dispatcher.py` — every webhook event type produces the right side effects (task complete, comm log, notification, audit row).
  - `test_payment_access_policy.py` — role defaults, admin override, per-user override, middleware decorator.
  - `test_accounting_event_emitter.py` — HMAC signature, retry, dead-letter.
- Aim for parity with existing service-test coverage (current backend has 549–633 tests per `[[project_ve_client_workspace_plan]]`). Target: **+50–70 new tests**; net suite stays green.

### 10.2 Frontend

- React Testing Library: render tests for `/payments` list, invoice modal, refund dialog, admin toggle page, client invoice page.
- `tsc --noEmit` + `eslint --max-warnings 0`.
- 0 console errors in the dev server when navigating every new route.

### 10.3 Manual QA — end-to-end via Stripe test mode

Run on `https://dev.velvetelves.com` (per `[[project_ve_dev_deployment]]`) with Stripe in test mode:

1. Admin enables Agent invoicing for the tenant.
2. Agent creates an invoice on a real transaction, links it to the "Collect TC fee" task.
3. Send invoice → email arrives in inbox with Pay button.
4. Open in incognito → Stripe Checkout loads with brand color (verify white-label hook fires) → pay with `4242 4242 4242 4242`.
5. Within ~5 s the dashboard widget increments, the task is marked complete with `completion_method='payment'`, the comm log shows a system entry, and the audit log records the write.
6. Agent issues a partial refund → status updates, comm log entry created, dashboard adjusts.
7. Admin disables Agent invoicing → next "Send invoice" attempt returns 403.
8. FSBO/Client login → sees only their own invoice, can pay it.
9. Webhook replay test (Stripe dashboard "Resend") → no duplicate side effects (idempotency holds).

### 10.4 Security testing (`milestones.txt` deliverable #8 — PCI compliance)

- **PCI SAQ-A checklist** confirmed: no card data touches our infra; Stripe Checkout used; webhook secret verified on every request; restricted API keys with only the scopes we use.
- OWASP Top 10 pass on the new endpoints (focused review): IDOR on invoice GET, broken function-level auth on refund/payout, mass-assignment on invoice PUT, replay on webhook, SSRF on accounting webhook URL (validate it's a public URL, reject private IP ranges and metadata endpoints), log injection on Stripe metadata fields.
- Run `/security-review` skill on the diff at end of Slice 5.
- Confirm no payment fields are logged at INFO level; confirm error messages don't surface raw Stripe error strings (map to safe user-facing strings).

---

## 11. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| 1 | Stripe account / Connect onboarding not complete by Week 18 start | Med | High | Begin onboarding during M5.1 (Week 17). Onboarding can take days for identity verification. Slice 0 confirms readiness before code starts. |
| 2 | Webhook delivery delays / Stripe outage on QA day | Low | Med | Stripe CLI for local; in QA, the Admin dashboard "Payments health" panel (§6.D) monitors `webhook_events.processing_status='pending'` older than 5 min. The polling fallback on the client pay page (§6.F) handles UX. |
| 3 | Scope creep into platform subscription billing | Med | Med | §2.2 explicitly excludes; if the client requests it, treat as Phase 6+ ticket. |
| 4 | Scope creep into multi-agent Stripe Connect Express onboarding | Med | Med | §2.2 explicitly excludes; brokerage is the single connected account for MVP. Commission splits recorded internally; cash is moved later via brokerage's own process. |
| 5 | Payment-triggered task completion creates a feedback loop with AI Email Automation (M4.2) auto-sending a receipt that triggers a task that triggers another email | Low | Med | Dispatcher uses `completion_method='payment'` and the M4.2 engine already short-circuits on `channel='system'` comm logs; verify in integration test. |
| 6 | PCI scope drift if a future task adds an embedded card form | Low | High | Document in `stripe_client.py` module docstring that any move from Checkout to Elements requires SAQ-A-EP re-scoping. |
| 7 | RLS misconfiguration leaks invoices across tenants | Low | Critical | Migration includes RLS policies mirroring `20260511094000_rls_tenant_isolation.sql`; `test_payment_rls_isolation.py` asserts cross-tenant 404 — already scheduled in Slice 1. |
| 8 | Refund of a closed transaction confuses dashboard reporting | Med | Low | Reporting uses net (after refunds) by default; gross available via toggle. UI clearly labels both. |
| 9 | Currency / locale bug at brokerages outside US (eventual) | Low | Low | USD-only at MVP, hard-checked at API boundary (and as a `CHECK` constraint at the DB level per §5.J); logged as a known limitation. |
| 10 | Accounting webhook URL set to internal IP → SSRF | Low | High | URL validator rejects private/loopback/metadata addresses on save (block `127.0.0.0/8`, `10/8`, `172.16/12`, `192.168/16`, `169.254.169.254`, IPv6 link-local). |
| 11 | **No platform-fee policy decided** — Stripe Connect transfer wiring depends on whether VE deducts a platform fee from each invoice | High | Med | Decide in Slice 0 (see §7 Slice 0 last bullet). Default position: **no platform fee at MVP** (VE is the broker's own tooling, not a marketplace). If business changes its mind later, the change is adding `application_fee_amount` to the Checkout Session — a localised diff. |
| 12 | Webhook handler runs too long → Stripe retries → duplicate side effects | Med | Med | Handler returns 200 within ~1s after the unique-index idempotency check; real work runs in `BackgroundTasks` (§5.B). All side-effect writes are upserts keyed on Stripe IDs. |
| 13 | Receipt email collides with Stripe's automatic receipt → payer gets two emails | Med | Low | Decide once: either disable Stripe's automatic receipt on the Checkout Session (`receipt_email=None` + Stripe dashboard setting) and own the email ourselves, OR rely on Stripe's receipt and skip our own. Plan currently sends both (§6.F) — flag for product decision in Slice 2. |

---

## 12. Acceptance Criteria — mapped to `milestones.txt` §5.2

| Deliverable | Verification |
| --- | --- |
| **Stripe API integration: secure card processing** | Test-mode Checkout completes a $1 payment, webhook fires, payment row persisted, audit logged. PCI SAQ-A confirmed (no card data in our DB/logs). |
| **Transaction fee collection** | Agent creates an invoice tied to a transaction; payer pays; the invoice is marked paid; the linked task (if any) is auto-completed. |
| **Commission payouts** | Admin triggers a payout to the brokerage's connected Stripe account; `transfer.paid` webhook updates `commission_payouts.status`; dashboard widget reflects. |
| **Invoicing system (create / send / track)** | End-to-end flow from `/payments/invoices/new` to paid status, with Drafts / Open / Paid / Past Due tabs all populated. |
| **Payment tracking UI (payments, refunds, history)** | `/payments` shows all three with sort/filter/search; each row drills into a detail page with the activity timeline. |
| **Payment-triggered task / status updates** | Marking an invoice paid auto-completes its linked task (`completion_method='payment'`) and creates the appropriate comm-log + audit entries. |
| **Admin payment access controls (on/off per role)** | `/admin/payment-access` toggles cause the next request from that role to return 403 on the gated action; per-user overrides also enforce. |
| **Payment reporting in dashboards** | Solo Agent / Team Lead / Admin dashboards show new widgets; numbers reconcile to the underlying `payments` / `commission_payouts` tables; "Expected" vs "Collected" visually distinct. |
| **Payment hooks for future accounting integration** | Setting `accounting_webhook_url` on a tenant causes signed JSON events to POST to that URL on every terminal payment event; failures land in `accounting_dead_letter`. |
| **Security testing for payment flows (PCI compliance)** | PCI SAQ-A checklist signed off in the milestone closeout note; `/security-review` skill output attached; OWASP focused review notes attached; all critical/high findings resolved. |

---

## 13. Out-of-Band Notes & References

- **Existing `commission_pct`** in `dashboard_aggregator.py` continues to drive the **pipeline** GCI estimate. It is *not* replaced — it sits beside the new "Collected" metric. Future Milestone 5.3 / post-MVP can reconcile the two more tightly.
- **Earnest money** is intentionally NOT collected via Stripe — EM is escrow-regulated. The platform's existing "EM Delivered" key date in M2.1 remains the source of truth for the workflow side; this milestone does not change EM handling.
- **White-label invoice PDFs** are deferred to M6.1; MVP uses a plain HTML email + Stripe's hosted receipt. The invoice email template lives in the existing email template store from M4.1.
- **Vendor role** has no payment surface at all (vendor read scope is documents only per `[[project_ve_client_linkage_no_ui]]`).
- **AI provider abstraction parallel — NOT replicated for payments.** `app/services/providers/` exists for AI because `requirements.txt` §8.1a explicitly mandates both OpenAI and Claude with admin-configurable switching. Payments has no equivalent requirement (§7.7 names Stripe specifically), so payments uses a thin single-provider wrapper (`stripe_client.py`) rather than a Protocol/registry. If a second processor is ever required, the wrapper is the seam to lift into a Protocol — a 1–2 day refactor, not a re-architecture.
- **Post-MVP roadmap items unblocked by this milestone**: per-agent Stripe Connect Express onboarding, 1099-K tax document generation, QuickBooks/Xero adapter on top of the accounting webhook hook, multi-currency, embedded Elements with SAQ-A-EP.

---

_End of plan._
