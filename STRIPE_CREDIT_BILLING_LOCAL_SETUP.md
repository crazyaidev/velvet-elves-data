# Stripe Credit Billing - Local/Dev Setup (Stripe CLI + ngrok)

Last verified against source: 2026-06-19

This is the exact setup to make the platform credit-billing system
(COMPLETE_PLATFORM_PAYMENT_SYSTEM_CREDIT_WALLET_SUPERIOR_PLAN.md) work end to
end in Stripe TEST mode on a local or dev machine. It is grounded in the live
code, not assumptions.

The headline: the credit system needs very little Stripe-side configuration.
It uses inline `price_data` (no Stripe Products/Prices to create) and does not
use Stripe Connect. The whole job is: test keys in `.env`, the feature flag on,
and webhook forwarding.

---

## 0. What you do NOT need to configure

- No Stripe Products or Prices. Credit packs live in the database table
  `credit_packs` (seeded by migration `20260824090000_credit_wallet.sql` with
  placeholder packs 1/5/10/25 at $20/credit). Checkout builds the Stripe line
  item dynamically from the pack row. Change prices in the app at
  Platform -> Billing, never in the Stripe dashboard.
- No Stripe Connect / connected account. That is only used by the older
  commission-payout flow; credits never touch it.
- No client-side Stripe.js keys beyond the publishable key. Card entry is on
  Stripe's hosted Checkout page (full-page redirect), so Velvet Elves never
  sees card data (PCI SAQ-A).

---

## 1. Keys and flag in the backend `.env`

The backend (`app/core/config.py`) reads these names. Use TEST keys only.

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=            # filled in step 3
VE_CREDIT_BILLING_V1=true         # REQUIRED. Without it, /billing/credits/* returns 404
                                  # and the Billing UI is hidden everywhere.
```

Optional overrides (defaults shown):

```
CREDIT_FREE_INTAKE_COUNT=1        # free starter credits granted once per tenant
CREDIT_COST_PER_TRANSACTION=1     # credits spent when a transaction is created
CREDIT_REVERSAL_WINDOW_HOURS=24   # delete-a-just-created-deal refunds its credit within this window
```

Apply the migration first if you have not: run
`supabase/migrations/20260824090000_credit_wallet.sql` (it is idempotent and
safe to re-run).

---

## 2. Authenticate the Stripe CLI

Either pair the CLI through the browser, or use the secret key directly (no
`stripe login` needed):

```
stripe login                          # browser pairing (test mode), OR
export STRIPE_API_KEY=sk_test_...     # the CLI reads this; or pass --api-key on each command
```

---

## 3. Webhook forwarding

`stripe listen` tunnels events straight to localhost, so for local dev ngrok is
not needed at all. Pick ONE of the two options below.

### Option A (recommended): `stripe listen`

```
stripe listen \
  --events checkout.session.completed,checkout.session.expired,payment_intent.succeeded,charge.refunded,refund.updated \
  --forward-to localhost:8000/api/v1/webhooks/stripe
```

- Replace `8000` with the port your uvicorn actually runs on (this project has
  also used 8001; match whatever you launch).
- On start it prints `Your webhook signing secret is whsec_...`. Put that value
  into `STRIPE_WEBHOOK_SECRET` in `.env`.
- Keep this process running while testing.
- The `--events` filter is optional; forwarding everything also works.

These five events are exactly what the billing path needs:
`checkout.session.completed` and `payment_intent.succeeded` both grant the
purchased deals (Stripe fires both for a `mode=payment` purchase; the grant is
idempotent so it only counts once), `checkout.session.expired` closes out an
abandoned checkout so it never reads as a stuck purchase, and
`charge.refunded` / `refund.updated` reconcile refunds.

### Option B: ngrok + a Dashboard endpoint

Use this instead of Option A, not in addition.

```
ngrok http 8000
# Stripe Dashboard -> Developers -> Webhooks -> Add endpoint
#   URL:    https://<id>.ngrok-free.app/api/v1/webhooks/stripe
#   events: checkout.session.completed, checkout.session.expired, payment_intent.succeeded, charge.refunded, refund.updated
# Copy that endpoint's Signing secret (whsec_...) into STRIPE_WEBHOOK_SECRET
```

The signing secret from a Dashboard endpoint is different from the one
`stripe listen` prints. Use whichever matches the option you chose. When the
ngrok URL changes, update the Dashboard endpoint URL.

---

## 4. Restart the backend

`.env` is read at startup and `--reload` does NOT pick up `.env` changes. Fully
restart uvicorn after setting the keys, the webhook secret, and the flag.

---

## 5. Verify the wiring

- `GET /api/v1/payments/config` returns your publishable key.
- As a platform admin, open Platform -> Billing. Health should show
  `stripe_mode: test` and `webhook: OK`.
- As an owner/admin, open Organization -> Billing & credits (the nav entry only
  appears when `VE_CREDIT_BILLING_V1=true`). Click a pack and pay with test card
  `4242 4242 4242 4242`, any future expiry, any CVC. On return the balance
  should rise, and the `stripe listen` terminal should show
  `checkout.session.completed` and `payment_intent.succeeded` forwarded with
  `200` responses.

---

## 6. Testing caveat

Test by clicking Buy in the UI, not with `stripe trigger checkout.session.completed`.
The grant is keyed off our own `purchase_id` metadata, which only exists when a
real checkout session is created through the app. A bare `stripe trigger` event
carries no `purchase_id`, so it is (correctly) ignored.

To exercise a refund end to end: buy a pack, then as a platform admin open the
tenant's Credits card (Platform -> Tenants -> the tenant) and click Refund on
the purchase row. Stripe sends `charge.refunded`, and the webhook claws the
credits back and marks the purchase refunded.

---

## 7. Quick reference: the full happy-path loop

1. Owner/admin: Organization -> Billing & credits -> Buy a pack -> pay with
   `4242 4242 4242 4242` -> balance rises (granted on webhook).
2. Create a transaction -> balance drops by 1, a "Used" row appears in history.
3. Spend to zero, start another deal -> calm paywall in the wizard; the deal is
   saved as a draft. Buy credits, return to /transactions/new, resume the draft.
4. Delete a just-created deal (Admin/Team Lead) within the reversal window ->
   the credit is refunded ("Refunded" row).
5. Platform admin: refund a purchase or grant/adjust credits from the tenant
   Credits card.

All of it is mouse-first and visible in the UI; no terminal, database, or
Stripe dashboard knowledge is required after this one-time setup.
