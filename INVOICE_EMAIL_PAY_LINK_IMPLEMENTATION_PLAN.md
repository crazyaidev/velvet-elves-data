# Invoice Email Pay Link Implementation Plan

Last updated: 2026-05-28

## 1. Purpose

This plan defines the standard invoice sending workflow for Velvet Elves:

```text
Internal user creates invoice
-> Velvet Elves creates Stripe Checkout Session
-> Velvet Elves emails payer a "Pay Now" link
-> Payer pays on Stripe Checkout
-> Stripe sends payment receipt
-> Velvet Elves records payment and updates invoice/task/dashboard state
```

The current implementation creates and stores a Stripe Checkout URL, but it does
not yet send the payer email. This plan closes that gap.

## 2. Product Decision

Use this standard ownership split:

- Velvet Elves sends the initial invoice email with a secure "Pay Now" button.
- Stripe hosts the checkout page and processes card details.
- Stripe sends the processor receipt after successful payment.
- Velvet Elves records all invoice-send and payment events in audit and
  communication history.

Do not rely on Stripe to send the initial invoice email unless the product later
switches to Stripe Invoicing as the source of truth. In the current architecture,
Velvet Elves invoices are the source of truth and Stripe Checkout is the payment
collection surface.

## 3. Current State

Backend:

- `InvoiceService.send_invoice(...)` creates/reuses a Stripe Customer.
- It creates a Stripe Checkout Session.
- It saves `stripe_checkout_session_id`, `stripe_payment_intent_id`,
  `checkout_url`, `sent_at`, and sets invoice status to `open`.
- It passes `receipt_email` into Stripe, which is for the post-payment receipt.
- It does not send an email to the payer.
- It does not create an outbound email communication log for the invoice send.

Frontend:

- The Send action calls `POST /api/v1/invoices/{invoice_id}/send`.
- The response includes `checkout_url`.
- The UI copies or exposes the secure pay link.
- The UI says the link is ready to share, not that email delivery completed.

Documentation:

- `MILESTONE_5_2_IMPLEMENTATION_PLAN.md` expects `send_invoice(...)` to send an
  email through the existing M4.1 email service.
- `MILESTONE_5_2_TESTING_GUIDE.md` expects the payer inbox to receive a message
  with a Pay Now button.

## 4. Desired User Experience

When an Agent, TC, Team Lead, or Admin clicks Send Invoice:

1. The backend validates invoice send permission.
2. The backend validates the invoice has a payer contact with an email address.
3. The backend creates or reuses the Stripe Checkout Session.
4. The backend sends an email to the payer.
5. The invoice status becomes `open`.
6. The frontend shows:

```text
Invoice sent
The payer received a secure payment link.
```

If the Stripe Checkout Session is created but email delivery fails:

1. The invoice remains `open`.
2. The Checkout URL remains available.
3. A failed communication log is stored.
4. The frontend shows:

```text
Invoice link created, but email was not sent.
Copy the secure pay link or reconnect your email account.
```

This is safer than rolling back the Stripe session because the user can still
share the link manually.

## 5. Sender Strategy

Preferred MVP behavior:

- Send from the logged-in user's connected email provider.
- Supported providers are the existing Gmail, Outlook, and iCloud integrations.
- Use the provider email address as the sender where available.

Fallback behavior:

- If the user has no connected email provider, return a clear API warning/error
  that the checkout link was created but email delivery was skipped.
- Do not silently pretend the email was sent.

Future optional behavior:

- Add a tenant-level branded sender such as `billing@tenant-domain.com`.
- Add SendGrid/postmark-style transactional fallback for tenants that do not
  want invoices sent from individual agent inboxes.
- Add a product setting:

```text
Invoice email sender:
- User connected email
- Tenant billing email
- Velvet Elves transactional email
```

## 6. Backend Implementation

### 6.1 Create Invoice Email Composer

Add a small service module:

```text
app/services/invoice_email_service.py
```

Responsibilities:

- Build subject, plain text body, and HTML body.
- Include payer name when available.
- Include invoice number or short invoice ID.
- Include transaction address when available.
- Include total amount.
- Include due date when available.
- Include secure Pay Now URL.
- Avoid exposing internal UUIDs as primary user-facing labels.

Example subject:

```text
Invoice for 154 E Washington St
```

Example plain text body:

```text
Hi Alex,

You have a new invoice from Jane Agent for 154 E Washington St.

Amount due: $495.00
Due date: June 15, 2026

Pay securely here:
https://checkout.stripe.com/...

Thank you,
Jane Agent
```

Example HTML content:

- Simple branded header.
- Invoice summary.
- Button linking to Stripe Checkout.
- Plain URL fallback below the button.
- Short note that card details are handled securely by Stripe.

### 6.2 Add Email Send Helper

Reuse the existing provider factory:

```text
app/services/email/factory.py::get_email_provider_for_user
```

Use the existing `OutboundEmail` type and provider `.send(...)` method.

Create helper signature:

```python
async def send_invoice_email(
    *,
    supabase: AsyncClient,
    sender_user: User,
    invoice: Invoice,
    payer_email: str,
    payer_name: str | None,
    checkout_url: str,
    transaction_address: str | None,
) -> InvoiceEmailSendResult:
    ...
```

Result fields:

```python
class InvoiceEmailSendResult(BaseModel):
    attempted: bool
    accepted: bool
    sender_email: str | None
    provider_name: str | None
    provider_ref_id: str | None
    error_message: str | None
```

### 6.3 Log Communication Result

Create an outbound `communication_logs` row for every invoice email attempt.

On success:

```text
channel = email
direction = outbound
status = sent
sender_user_id = current_user.id
sender_email = connected provider email
recipient_emails = [payer email]
subject = invoice email subject
body/body_html = rendered invoice email
transaction_id = invoice.transaction_id
provider_name = provider name
provider_ref_id = provider message id
```

On failure:

```text
status = failed
error_message = provider or configuration error
```

This keeps the communication history truthful and auditable.

### 6.4 Update Invoice Send Service

Modify:

```text
app/services/invoice_service.py::InvoiceService.send_invoice
```

After the Checkout Session is created and invoice fields are saved:

1. Resolve payer contact email.
2. Resolve display context such as transaction address.
3. Call `send_invoice_email(...)`.
4. Return both invoice and email delivery metadata.

Avoid hard-failing the whole send after the Stripe session is created. At that
point the payment link is valid and should remain available.

### 6.5 Update API Response Schema

Current response:

```python
class InvoiceSendResponse(BaseModel):
    invoice: InvoiceResponse
    checkout_url: str
```

Extend it:

```python
class InvoiceEmailDeliveryResponse(BaseModel):
    attempted: bool
    accepted: bool
    sender_email: str | None = None
    provider_name: str | None = None
    error_message: str | None = None

class InvoiceSendResponse(BaseModel):
    invoice: InvoiceResponse
    checkout_url: str
    email_delivery: InvoiceEmailDeliveryResponse | None = None
```

Keep `checkout_url` for backwards compatibility with existing frontend code.

### 6.6 Handle Missing Payer Email

If payer contact has no email:

- Create Checkout Session.
- Mark invoice `open`.
- Return `email_delivery.accepted = false`.
- Error message:

```text
Payer contact has no email address.
```

Frontend should prompt the user to copy the pay link or update the contact.

### 6.7 Handle Missing User Email Integration

If the user has no Gmail/Outlook/iCloud integration:

- Create Checkout Session.
- Mark invoice `open`.
- Return `email_delivery.accepted = false`.
- Error message:

```text
User has no active email integration.
```

This matches existing integration behavior and avoids an invisible failure.

## 7. Frontend Implementation

### 7.1 Update Payment Types

Modify:

```text
src/types/payments.ts
```

Add:

```ts
export interface InvoiceEmailDelivery {
  attempted: boolean
  accepted: boolean
  sender_email: string | null
  provider_name: string | null
  error_message: string | null
}

export interface InvoiceSendResponse {
  invoice: Invoice
  checkout_url: string
  email_delivery: InvoiceEmailDelivery | null
}
```

### 7.2 Update Send Toasts

Update:

```text
src/components/payments/InvoiceDetailModal.tsx
src/pages/payments/InvoiceDetailPage.tsx
src/components/payments/NewInvoiceModal.tsx
src/pages/payments/InvoiceNewPage.tsx
```

Success:

```text
Invoice sent
Secure payment link emailed to payer.
```

Partial success:

```text
Pay link created
Email was not sent. The secure link has been copied so you can share it manually.
```

Failure before Checkout Session creation:

```text
Could not send invoice
<API error>
```

### 7.3 Keep Manual Copy Link

Keep the visible Secure Pay Link card after send. It is still useful for:

- Resending manually.
- Sharing through another channel.
- Support/debugging.
- Client portal fallback.

### 7.4 Email Integration Prompt

If `email_delivery.error_message` indicates no active email integration, show an
action that links to the existing email integration settings page.

Suggested copy:

```text
Connect Gmail, Outlook, or iCloud to send invoice emails from your account.
```

## 8. Stripe Receipt Policy

For MVP, keep Stripe receipts enabled unless product decides otherwise.

Expected payer email sequence:

1. Velvet Elves invoice email before payment.
2. Stripe receipt after payment succeeds.

Do not send a second Velvet Elves payment receipt until product explicitly wants
branded receipts. Otherwise the payer may receive duplicate receipt-style emails.

Future decision:

- If branded Velvet Elves receipts are preferred, disable or avoid Stripe
  automatic receipt behavior and own the receipt email ourselves.

## 9. Testing Plan

### 9.1 Backend Unit Tests

Add tests for:

- `send_invoice` creates Checkout Session and sends email.
- Response includes `email_delivery.accepted = true`.
- Communication log is created with `status = sent`.
- Missing email integration returns partial success metadata.
- Missing payer email returns partial success metadata.
- Provider failure logs `status = failed`.
- Stripe failure before Checkout Session creation still returns API error and
  does not mark invoice open.

Suggested test file:

```text
app/tests/test_invoice_email_send.py
```

### 9.2 Backend Integration Tests

Extend existing invoice tests:

```text
app/tests/test_invoice_service.py
```

Update the current send test so it asserts:

- `checkout_url` is returned.
- Invoice status is `open`.
- Email delivery metadata exists.
- The email helper was called with payer email and checkout URL.

### 9.3 Frontend Tests

Add or update component tests for:

- Successful send toast.
- Partial success toast when email delivery fails.
- Copy link fallback still works.
- Missing email integration prompt appears.

Suggested test file:

```text
src/tests/unit/PaymentComponents.test.tsx
```

### 9.4 Manual QA

Scenario A: Happy path

1. Connect Gmail/Outlook/iCloud for the sender.
2. Create invoice with payer contact email.
3. Click Send.
4. Confirm invoice status is Open.
5. Confirm payer inbox receives Velvet Elves email with Pay Now button.
6. Click Pay Now.
7. Confirm Stripe Checkout opens.
8. Pay with test card.
9. Confirm Stripe receipt arrives after payment.
10. Confirm invoice becomes Paid.

Scenario B: No connected email

1. Use a sender with no email integration.
2. Create invoice.
3. Click Send.
4. Confirm Checkout URL is created.
5. Confirm UI warns that email was not sent.
6. Confirm Copy Link works.

Scenario C: Missing payer email

1. Create/select payer contact without email.
2. Click Send.
3. Confirm Checkout URL is created.
4. Confirm UI warns that payer has no email address.

Scenario D: Provider failure

1. Use an expired or invalid email integration.
2. Click Send.
3. Confirm partial success message.
4. Confirm failed communication log stores the provider error safely.

## 10. Security And Compliance Notes

- Never include Stripe secret keys in email content or logs.
- Never include card data in Velvet Elves UI, logs, or emails.
- Use the hosted Stripe Checkout URL only.
- Do not expose internal-only UUIDs as the main payer-facing label.
- Store only provider message IDs and safe error strings in communication logs.
- Keep audit logs for invoice send events.
- Keep email delivery logs tenant-scoped.

## 11. Acceptance Criteria

This feature is complete when:

- Clicking Send creates a Stripe Checkout Session.
- The payer receives an email with a Pay Now button when the sender has an
  active email integration and the payer has an email address.
- The email is sent from the connected user email account.
- The invoice status changes from Draft to Open.
- The Checkout URL remains visible/copyable in the app.
- Email success/failure is represented in the API response.
- Communication logs record sent and failed invoice email attempts.
- Stripe handles payment collection on hosted Checkout.
- Stripe sends the post-payment receipt.
- Webhook processing still marks invoice paid and completes linked tasks.
- Tests cover success and partial-failure paths.

## 12. Implementation Order

1. Add backend invoice email rendering helper.
2. Add backend invoice email send helper using existing email provider factory.
3. Add communication log creation for success/failure.
4. Extend invoice send response schema with email delivery metadata.
5. Wire helper into `InvoiceService.send_invoice`.
6. Add backend tests.
7. Update frontend payment types.
8. Update send toasts and partial-success UI.
9. Add frontend tests.
10. Run end-to-end QA against test Stripe and a real/test email inbox.

## 13. Open Product Questions

1. Should invoice emails always come from the user, or should tenants be able to
   choose a shared billing sender?
2. Should Team Leads/Admins sending on behalf of an Agent use their own email or
   the invoice creator's email?
3. Should invoice emails include tenant branding in MVP or wait for white-label
   work?
4. Should Stripe receipts remain enabled once Velvet Elves adds branded payment
   confirmation emails?
5. Should failed invoice email sends be shown in a dashboard health panel?

