# Stripe Local Configuration

Last verified: 2026-05-27 UTC

This document captures the current local Stripe test-mode setup for Velvet Elves payment workflows. Runtime environment variables and secret values are intentionally excluded.

## Scope

This setup supports Milestone 5.2 payment workflows:

- Invoice payment collection through Stripe Checkout.
- Stripe webhook ingestion and idempotent event dispatch.
- Payment success/failure reconciliation.
- Refund creation and refund webhook reconciliation.
- Commission payout records backed by Stripe Transfers to a connected account.
- Platform payout event visibility for payment-health monitoring.

The current implementation is a single-provider Stripe integration. It uses hosted Checkout for card collection, so card data does not touch Velvet Elves infrastructure.

## Local Stripe Mode

- Mode: test.
- Platform account: `acct_1Mj3pmHVNub9Y0bE`.
- Country: United States.
- Default currency: USD.
- Platform charges: enabled.
- Platform payouts: enabled.
- Platform details: submitted.

## Connected Account

The local MVP payout destination is a single connected account:

- Account ID: `acct_1TbP0GHVNuWaCt8m`.
- Account email: `crazyaidev20500519@gmail.com`.
- Country: United States.
- Website: `https://dev.velvetelves.com/`.
- Statement descriptor: `VELVET ELVES`.
- Charges: enabled.
- Payouts: enabled.
- Details: submitted.
- External account: one Stripe test bank account attached.
- Card payments capability: active.
- Transfers capability: active.
- Current requirements due: none.
- Past-due requirements: none.

This connected account has both Merchant and Recipient configurations in Stripe. For the current Velvet Elves workflow, the Recipient/Transfers side is the important part: the platform collects funds first, then sends a transfer to the connected account for commission payout testing.

## Webhook Endpoint

Stripe Dashboard endpoint:

- Endpoint ID: `we_1TbNRGHVNub9Y0bEYYi8PfHb`.
- Status: enabled.
- Description: `Velvet Elves local test webhook via ngrok`.
- URL: `https://6131-91-239-130-102.ngrok-free.app/api/v1/webhooks/stripe`.
- API version override: none; Stripe uses the account default.

The webhook URL points to the local backend through ngrok. When ngrok changes, update the Stripe endpoint URL before testing webhook delivery.

## Webhook Events

The enabled events are:

- `checkout.session.completed`
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `charge.refunded`
- `refund.updated`
- `transfer.created`
- `transfer.updated`
- `transfer.reversed`
- `transfer.canceled`
- `payout.paid`
- `payout.failed`

The backend dispatcher also accepts `transfer.paid` defensively, but Stripe's configured endpoint uses the actual transfer event names above.

## Backend Payment Surface

Backend router: `velvet-elves-backend/app/api/v1/payments.py`

Local payment-related API surface:

- `GET /api/v1/payments/config`
- `GET /api/v1/payments`
- `GET /api/v1/payments/{payment_id}`
- `POST /api/v1/payments/{payment_id}/refund`
- `GET /api/v1/commission-payouts`
- `POST /api/v1/commission-payouts`
- `POST /api/v1/webhooks/stripe`

Invoice creation/sending is handled through the invoice API/service layer. Payment collection starts when an invoice is sent and the service creates a Stripe Checkout Session.

## Stripe Client Wrapper

Backend wrapper: `velvet-elves-backend/app/services/stripe_client.py`

The wrapper centralizes:

- Stripe SDK configuration.
- Customer creation.
- Checkout Session creation in `mode='payment'`.
- Checkout Session retrieval.
- PaymentIntent retrieval.
- Refund creation.
- Transfer creation.
- Webhook signature verification.
- Stripe error mapping into Velvet Elves payment error classes.

Installed local SDK:

- Python package: `stripe`
- Version: `12.5.1`

## Checkout Flow

Implementation path:

- `InvoiceService.send_invoice(...)`
- `StripeClient.create_customer(...)`
- `StripeClient.create_checkout_session(...)`
- Stripe hosted Checkout
- `POST /api/v1/webhooks/stripe`
- `PaymentEventDispatcher.dispatch(...)`

Checkout Session behavior:

- Mode: `payment`.
- Currency: USD.
- Line items use inline `price_data`.
- Tax is appended as a separate line item when present.
- Success redirect: `/client/invoices/{invoice_id}?paid=1`.
- Cancel redirect: `/client/invoices/{invoice_id}?canceled=1`.
- Metadata attached to the Checkout Session and PaymentIntent includes tenant, invoice, transaction, and workflow kind.
- Receipt email is passed when the payer contact has an email.

Primary idempotency key pattern:

- Customer creation: `customer:{tenant_id}:{contact_id}`
- Checkout session creation: `checkout:{invoice_id}:{send_attempt_n}`

After Checkout Session creation, the local invoice is updated to `open` with the Stripe session ID, PaymentIntent ID, hosted Checkout URL, and sent timestamp.

## Webhook Receiver Logic

Endpoint: `POST /api/v1/webhooks/stripe`

Receiver behavior:

1. Read the raw request body.
2. Require a Stripe signature header.
3. Verify the webhook signature.
4. Extract the Stripe event ID, event type, and tenant metadata when present.
5. Insert a `webhook_events` row.
6. Short-circuit duplicate events and return HTTP 200.
7. Defer event side effects to a background task.

This keeps Stripe acknowledgement fast while preserving idempotency through the `webhook_events` table.

## Event Dispatch Logic

Dispatcher: `velvet-elves-backend/app/services/payment_event_dispatcher.py`

Handled event behavior:

- `checkout.session.completed`
  - Requires invoice and tenant metadata.
  - Upserts a succeeded payment row keyed by PaymentIntent.
  - Marks the invoice paid on the first terminal success.
  - Completes linked tasks with `completion_method='payment'`.
  - Writes a system communication log entry.
  - Emits an accounting event.

- `payment_intent.succeeded`
  - Reconciles succeeded payments.
  - Handles events that arrive before or after Checkout completion.
  - Can record direct charges when tenant metadata is present but no invoice is resolved.

- `payment_intent.payment_failed`
  - Upserts a failed payment row.
  - Preserves a safe truncated failure message in metadata.

- `charge.refunded`
  - Reads refund objects nested under the charge.
  - Syncs local refund rows and aggregate refunded amounts.

- `refund.updated`
  - Syncs the status of a single Stripe Refund object.

- `transfer.created`, `transfer.updated`, `transfer.reversed`, `transfer.canceled`, `transfer.paid`
  - Looks up local commission payout rows by Stripe transfer ID.
  - Updates payout status to in-transit, paid, or canceled depending on Stripe transfer state.

- `payout.paid`, `payout.failed`
  - Logs platform-to-bank payout visibility.
  - Does not create local commission payout records.

Unsupported event types are logged and skipped.

## Refund Flow

Implementation path:

- `POST /api/v1/payments/{payment_id}/refund`
- `RefundService.create_refund(...)`
- `StripeClient.create_refund(...)`
- Stripe refund webhook reconciliation

Rules:

- Refund amount must be greater than zero.
- Payment must belong to the user's tenant.
- Only succeeded, partially refunded, or refunded payments are refundable.
- Refund amount cannot exceed the remaining refundable balance.
- A pending local refund row is created before calling Stripe.
- The invoice remains paid even when the payment is refunded; reporting distinguishes gross versus net.

Primary idempotency key pattern:

- Refund creation: `refund:{refund_id}`

## Commission Payout Flow

Implementation path:

- `POST /api/v1/commission-payouts`
- Local pending commission payout row.
- Audit log entry.
- `StripeClient.create_transfer(...)`
- Stripe transfer webhook reconciliation.

Current local model:

- One default connected account is used for MVP payout testing.
- A request may also provide an explicit destination account.
- Transfers are created in USD.
- Transfer metadata includes tenant, commission payout, and transaction IDs.

Primary idempotency key pattern:

- Transfer creation: `transfer:{commission_payout_id}`

Expected status progression:

- Local row starts as `pending`.
- Successful Stripe transfer creation stores the transfer ID.
- Local row moves to `in_transit`.
- Later transfer webhook events can move it to `paid` or `canceled`.

## Local Testing Notes

- Restart the backend after local configuration changes so the process reloads settings.
- Keep the Stripe Dashboard webhook URL aligned with the active ngrok tunnel.
- For manual webhook tests, use Stripe CLI trigger commands only after the local backend and tunnel are running.
- Connected account payouts/transfers are ready for test-mode flow testing because transfers and payouts are active.
- Platform balance must have enough **available** USD test balance before transfer creation succeeds. Recently collected card payments can sit in pending balance first; pending balance cannot fund a transfer unless the transfer is explicitly tied to a charge with `source_transaction`, which the current MVP payout form does not do.
- If a transfer fails because available balance is insufficient, add Stripe test balance and submit a fresh payout request. Stripe does not automatically retry a failed transfer after balance is added.

## Security And Compliance Notes

- No card data should be logged or stored by Velvet Elves.
- Hosted Stripe Checkout is the payment collection surface.
- Webhook signatures are verified before event processing.
- Duplicate Stripe event delivery is handled idempotently.
- Secrets and runtime environment variables are excluded from this document by design.
