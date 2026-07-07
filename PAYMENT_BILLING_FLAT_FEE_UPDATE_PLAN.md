# Payment and Billing System Update Plan: Flat Fee Per Deal

**Drafted:** 2026-07-06. **Revised:** 2026-07-06 (Rev 2, after a second source-verification pass; see Appendix A for what changed and why)
**Input:** `Q&A_PAYMENT_AND_BILLING_SYSTEM.md` (Jake's answers, 2026-06-25 to 2026-07-02; Question 6 still pending as of 2026-06-26)
**Supersedes:** the customer-facing pricing model of `COMPLETE_PLATFORM_PAYMENT_SYSTEM_CREDIT_WALLET_SUPERIOR_PLAN.md`. The wallet engine that plan built is kept unchanged; only its pricing, presentation, and scope change.
**Rule for this document:** plan only. No source code is changed by this document.

---

## 1. Sources reviewed

This plan is grounded in a full read of the decision thread, the project documents, and the currently implemented source code, so the workflow described here matches what actually runs today.

**Project documents**
- `Q&A_PAYMENT_AND_BILLING_SYSTEM.md` (the decision thread this plan answers)
- `PAYMENT_SYSTEM_GUIDE.md` (the guide Jake read; its Section 2 = invoices, Section 3 = commission payouts, Section 4 = payment access, Section 5 = credits)
- `requirements.txt` §2.5 Payment Processing, §7.7 Payment Module (Stripe), §11.1 ad billing
- `milestones.txt` Milestone 5.2 (Payment Processing) and Phase 5 scope
- `SYSTEM_DESIGN.md` (its roadmap explicitly plans "Per-intake pricing" via "Stripe payment integration" in Phase 5, so per-deal charging is the designed model, not a deviation), `FRONTEND_UI_WORKFLOW_LOGIC.md` (shared shell, settings surfaces), `STYLE_GUIDE.md` (tokens, type, spacing)
- `COMPLETE_PLATFORM_PAYMENT_SYSTEM_CREDIT_WALLET_SUPERIOR_PLAN.md`, `STRIPE_CREDIT_BILLING_LOCAL_SETUP.md`

**Backend source (velvet-elves-backend)**
- `app/services/credit_wallet_service.py` (atomic idempotent ledger, free grant, spend, reversal, clawback)
- `app/services/credit_purchase_service.py` (Stripe Checkout, webhook-only granting)
- `app/services/platform_settings_service.py` (DB-backed billing switches and knobs)
- `app/api/v1/transactions.py` lines 200 to 300 (the single credit consumption point) and lines 916 to 942 (delete-window auto refund)
- `app/api/v1/billing_credits.py` (tenant wallet/packs/checkout/ledger endpoints)
- `app/api/v1/platform_billing.py` (platform-admin settings, packs, health, grants, refunds)
- `app/api/v1/payments.py` (invoices rails, commission payouts, payment capabilities)
- `app/services/payment_access_service.py`, `app/api/v1/admin_payments.py` (capability policy + the Payment Access matrix API)
- `app/services/payment_event_dispatcher.py` (webhook branches; `_on_credit_purchase_paid` grants from the purchase row, not from pack data, at lines 249 to 292; no `checkout.session.expired` branch exists)
- `app/api/v1/invoices.py` (manual `tax_cents` on invoices)
- `app/api/v1/platform_ai_usage.py` (AI cost aggregation incl. per-transaction)
- `app/schemas/credit.py` (ledger labels, response shapes)
- `supabase/migrations/20260824090000_credit_wallet.sql` (tables, RPC, seeded placeholder packs at $20; `credit_purchases.pack_id` is nullable; `status` CHECK allows only pending/paid/failed/refunded)
- Verified there is exactly one live transaction-creation call in the whole backend: `repo.create` in `transactions.py` line 233. The auto-email sweep creates email drafts, not transactions, and the frontend `TransactionForm` direct POST is dead code rendered nowhere.

**Frontend source (velvet-elves-frontend)**
- `src/components/billing/BillingPane.tsx`, `CreditPaywallModal.tsx`, `CreditGateBlock.tsx`, `CreditBalanceBadge.tsx`
- `src/contexts/IntakeContext.tsx` (the click-time credit gate: lines 75 to 94 open the paywall instead of the wizard when the balance cannot cover one deal)
- `src/components/wizard/NewTransactionWizard.tsx` (draft autosave; Save draft posting `status: 'Incomplete'` at line 4095; 402 handling on both create and save-draft; the zero-balance entry gate `entryBlocked` at lines 3218 to 3226 rendering `CreditGateBlock`; **no** `purchase_result` handling exists in the wizard, only `BillingPane` reads it)
- `src/hooks/useCredits.ts` (incl. `useCreditPurchaseStatus`, the post-return purchase poller currently used only by BillingPane)
- `src/pages/organization/OrganizationPage.tsx` (section `billing`, labeled "Billing & Credits")
- `src/pages/platform/PlatformBillingPage.tsx`, `PlatformAIUsagePage.tsx`, `src/components/platform/TenantDetailModal.tsx`
- `src/pages/payments/CommissionPayoutsPage.tsx`, `src/pages/admin/AdminPaymentAccessPage.tsx`
- `src/layouts/AppLayout.tsx` lines 386 to 395 (Payments nav group; Commission Payouts entry keyed off `canTriggerPayout`)
- `src/utils/constants.ts` (routes)

---

## 2. Analysis of the Q&A: what was decided, and what each decision means

### Question 1: charge per deal at all
**Jake's decision.** Yes. Per deal only, because AI cost varies per deal; price must sit above the measured average so wins outweigh losses.
**What it means for the build.** The per-deal engine is the right one and stays. The blocking input is the dollar amount, which depends on measured AI cost per deal. Jake explicitly asked for the AI cost of the test deals so far, in particular the deal with 5 counter offers that was entered multiple times.
**Current state in code.** Every AI call is metered into `ai_usage_events` and `GET /api/v1/platform/ai-usage` aggregates cost by deal, tenant, feature, provider, model, and day (`platform_ai_usage.py`). The deal label is the decrypted address. Gap: a deal entered multiple times appears as several separate rows with the same address, and there is no search or export to sum them.
**Resulting work.** W7 (per-deal cost report improvements) and Deliverable D2 (the cost memo for Jake).

### Question 2: the price and the shape of the fee
**Jake's decisions.**
1. Flat fee per deal. No customer-facing credits, no per-credit pricing, no percentage volume discounts "until we have a good idea of AI impact token usage".
2. First deal free **per brokerage account**, not per login ("the brokerage gets 1 deal for free, not 60 deals if they have 60 agents").
3. One volume offer, shaped as "buy 10 deals, get 2 free" at the same flat fee, possibly limited to accounts that sign up in 2026.
**What it means for the build.** This is a re-presentation, not a rebuild, exactly as I told Jake: the wallet engine stays (1 internal credit = 1 deal), and everything the customer sees becomes dollars and deals. The four seeded packs ($20 placeholder single, 5/10/25-credit discount packs in `20260824090000_credit_wallet.sql`) do not survive; pricing collapses to one flat fee plus one optional bundle.
**Current state in code.**
- Free first deal is already account-basis: the wallet is unique per `tenant_id` and the free grant fires exactly once per tenant (`credit_wallet_service.py` lines 56 to 90, idempotency key `free:{tenant_id}`). Guests in a host workspace spend the host wallet (`billing_credits.py` docstring), so 60 agents share one free deal. **No engine change needed, only wording.**
- The bundle does not exist. The purchase machinery is generic enough (a purchase = N credits for M cents, webhook-granted, idempotent per purchase id) that the bundle is one new sellable product plus an eligibility rule, with zero engine change.
**Resulting work.** W1 (fee and bundle settings), W2 (pricing endpoint and checkout kinds, incl. the bundle), W3 (migration), W5/W6 (UI re-presentation).

### Question 3: charging model shape
**Jake's decision.** Launch with per-deal. If it does not earn, fall back to a credit-based model later.
**What it means for the build.** This is the strongest argument for keeping the credit wallet engine intact underneath the flat-fee skin: the fallback Jake named is one settings flip away instead of a rebuild. The internal `credit_cost_per_transaction` setting stays pinned at 1 and disappears from the admin UI; it is not deleted.

### Question 4: payouts, bank connection, and charge timing
**Jake's decisions (and my agreed refinement).**
1. Velvet Elves does not move commission. Brokerages collect any client fee themselves on the settlement statement. Commission Payouts and the Stripe Connect bank-connection step are **parked**, not shipped.
2. Billing happens at the **start** of a transaction: at the first save of a new deal (when the agent commits and the record is created), never at the very first click, so an abandoned intake is never charged. Jake replied "Agreed!" to exactly this trigger.
3. "Plus or minus monthly fees": a flat per-deal fee now, an optional monthly layer later. Architecture note only for now.
**Current state in code.**
- **Backend: the charge point already matches the agreed trigger.** `POST /api/v1/transactions` is the single consumption point in the system (`transactions.py` line 200, only live create call at line 233): the wizard's final "Approve & Create" posts there, and the wizard's explicit "Save draft" also posts there with `status: 'Incomplete'` (`NewTransactionWizard.tsx` line 4095) and handles a 402 the same way (line 4143). Wizard autosaves (localStorage and the server-side `wizard_runs` draft) never create a transaction record and never charge. No backend charge-point move is required.
- **Frontend: two pre-entry gates CONTRADICT the agreed trigger and must come out.** Under the prepaid-credit model I built two blockers so nobody could reach the wizard at zero balance: a click-time gate in `IntakeContext.openNewTransaction` (`IntakeContext.tsx` lines 75 to 94: paywall opens instead of the wizard) and a full-page `CreditGateBlock` that replaces the wizard form whenever the balance is below the cost (`NewTransactionWizard.tsx` lines 3218 to 3226). Those were correct when a deal required a pre-owned credit. Under the flat-fee model Jake approved, **zero prepaid balance is the normal state**: the user must be able to begin intake freely and pay at the first save. If the gates stayed, every deal after the free one would be paywalled at the very first click, the exact thing I told Jake would not happen, and the in-flow "pay at commit" loop would be unreachable. (The click-time gate was my own 2026-06-19 requirement, made for the prepay model; Jake's Question 4 decision supersedes it.)
- **The return leg from Stripe is incomplete for the wizard.** The paywall's checkout redirects back to `/transactions/new?purchase_result=success`, but nothing on that page reads `purchase_result`; only `BillingPane` does. Today the returning user is saved by the draft-resume prompt, and if the webhook has not landed yet the entry gate even hides the wizard behind the zero-balance block. The plan must add a proper wizard-side return handler (W6-3).
- Commission payouts are live code: routes in `payments.py` (list + trigger behind the `payout.trigger` capability, policy in `payment_access_service.py`), a nav entry gated by `canTriggerPayout` (`AppLayout.tsx` line 391), the dashboards' `PaymentsWidget` payout block (`showPayouts` prop), and `CommissionPayoutsPage.tsx`. Nothing connects a bank today, but the surface is visible to capable roles.
**Resulting work.** W6-0 (remove the pre-entry gates), W6-3 (wizard return handler), W4 (park payouts), W6-5 (fee disclosure on commit buttons), T-series tests.

### Question 5: refund rules
**Jake's decision.** Keep the suggestion: the 24-hour auto-refund when a brand-new deal is deleted. He pointed the bought-but-unused question back at the Question 2 outcome.
**What it means for the build.** The 24-hour window is already live and configurable (`credit_reversal_window_hours`, delete hook in `transactions.py` lines 916 to 942). But Jake's bundle re-introduces prepaid, bought-but-unused deals, so the "30-day refund for unused purchases" policy question is back for exactly one product (the bundle). Platform-admin manual refund with webhook-reconciled clawback already exists (`platform_billing.py` refund route; clawback clamps at the current balance in `credit_wallet_service.record_purchase_refund`).
**Resulting work.** Keep everything; put one policy decision to Jake (Section 10, decision 3) with a recommendation; relabel refund rows in deal terms.

### Question 6: default payment permissions and sales tax
**Status.** Unanswered ("Will be answered tomorrow", written 2026-06-26; still open on 2026-07-06).
**What it means for the build.** Nothing in this plan may depend on the answer. The existing conservative defaults stay (permissions start closed, an admin opens them per role via `/admin` Payment Access, `AdminPaymentAccessPage.tsx`; tax stays a single manual `tax_cents` amount per invoice, `invoices.py` lines 104 and 190). Both are already pure configuration, so Jake's eventual answer lands as settings changes, not code. The one interaction with this plan: while payouts are parked, the `payout.trigger` row must disappear from the Payment Access matrix so an admin cannot grant a capability that leads to a hidden page.

### Cross-cutting conclusion

The collecting-from-clients side (invoices, refunds, payment access) is untouched by this plan. The platform-charging side keeps its engine and changes its skin: **one flat dollar fee per deal, first deal free per brokerage, one optional 10+2 bundle, charged at first save, with payouts parked.** Vocabulary rule for every tenant-facing surface: say "deal" and dollars; never say "credit".

The deepest change this Q&A forces is a workflow inversion the first draft of this plan missed: the prepay model treated an empty wallet as an error state to be walled off before intake; the flat-fee model treats it as the normal state and moves the only gate to the moment of commitment. Everything in Section 5 follows from that inversion.

---

## 3. Target model: the exact rules

R1. **Billing switch.** Billing stays off platform-wide until Jake sets the fee (existing `ve_credit_billing_v1` platform setting). When off, every billing surface disappears exactly as today (wallet endpoint 404s, Billing section hidden).

R2. **Flat fee.** One platform-wide price, `deal_fee_cents`, set by the platform admin in dollars. A deal always costs exactly 1 internal credit; the customer sees only the dollar fee.

R3. **Charge trigger.** The fee applies at the first server-side save of a new deal record, whichever comes first of "Save draft" and "Approve & Create" in the wizard. Autosaved wizard progress is never charged. Corollary, new in Rev 2: **entering the wizard is never blocked by balance.** A user with zero prepaid deals opens the wizard, completes intake, and meets the fee only at commit; the backend 402 is the one and only gate. This is the trigger Jake approved; the backend already behaves this way and the frontend pre-entry gates are removed to match (W6-0).

R4. **First deal free.** Each brokerage (tenant) receives exactly one free deal, granted once on first wallet touch, shared by every member of the account. (Existing `credit_free_intake_count` = 1, account-basis by construction.)

R5. **Pay-per-deal flow.** With no prepaid deals, saving a new deal returns 402 and the user pays the flat fee through Stripe Checkout in-flow. On return, the wizard restores the saved intake, shows a "confirming your payment" state while it polls the purchase, and completes the pending save automatically once the webhook confirms, with a manual retry button as the fallback if confirmation is slow. Credits are granted only by the verified Stripe webhook, never by the success redirect (existing invariant), which is exactly why the return leg must tolerate webhook lag instead of assuming the balance is already there.

R6. **Bundle.** When enabled, a brokerage whose account was created inside the promo signup window (default: calendar year 2026) can buy "10 deals, get 2 free": one Checkout purchase of 10 x `deal_fee_cents` granting 12 prepaid deals. Prepaid deals are spent automatically before any new charge. Bundle knobs (on/off, size, bonus, signup window) are platform settings so the promo can be retired without a deploy, matching Jake's "we don't move this model forward after that" option.

R7. **Refunds.** Deleting a deal within 24 hours (configurable) automatically returns its fee or prepaid deal, exactly as built. Purchase refunds remain platform-admin manual actions with webhook-reconciled clawback. Policy for partially used bundles goes to Jake (Section 10).

R8. **Exemptions.** Platform admins are never charged (existing posture). No other exemptions.

R9. **Payouts parked.** Commission payouts and every Stripe Connect affordance are hidden behind a default-off platform setting. Code and tables remain.

R10. **Monthly layer.** Nothing is built, but nothing may block adding a Stripe subscription beside the per-deal fee later ("plus or minus any monthly fees").

R11. **Safety invariants preserved.** Single consumption point; atomic idempotent ledger (no double charge on retry or webhook replay); every charge, grant, refund, and adjustment visible as a ledger row; compensate-delete when a concurrent create loses the last prepaid deal.

R12. **Future intake paths inherit the gate.** Verified today: `transactions.py` line 233 is the only live transaction-creation call. The transaction-processing evolution work (`TRANSACTION_PROCESSING_EVOLUTION_PLAN.md`) plans automatic intake of emailed contracts later; any such path must either route through the same consumption point or carry an explicit product decision that machine-created drafts stay uncharged until a person commits them. This rule exists so a future feature cannot quietly open a free side door into billed deals.

R13. **Billing cannot be switched on unpriced.** `ve_credit_billing_v1` may not be set to true while `deal_fee_cents` is 0: the settings API rejects it and the admin UI disables the toggle with an explanation. Otherwise a paying tenant with an empty wallet would hit a 402 whose paywall cannot sell anything, a dead end.

---

## 4. Backend work plan

### W1. Settings: the flat fee and bundle knobs
File: `app/services/platform_settings_service.py` (plus `app/schemas/credit.py`, `app/api/v1/platform_billing.py` PUT mapping).
Add DB-backed keys with safe defaults (billing remains correct with an unseeded table):

| Key | Default | Meaning |
|---|---|---|
| `deal_fee_cents` | `0` | Flat fee per deal. `0` = unpriced; health check warns and checkout is refused while billing is on |
| `deal_bundle_enabled` | `false` | Bundle promo master switch |
| `deal_bundle_size` | `10` | Deals paid for |
| `deal_bundle_bonus` | `2` | Free deals granted on top |
| `deal_bundle_signup_from` | `2026-01-01` | Tenant `created_at` lower bound (inclusive) |
| `deal_bundle_signup_until` | `2027-01-01` | Upper bound (exclusive) |

`credit_cost_per_transaction` stays pinned at 1 and leaves the admin UI (kept in the DB for the Question 3 fallback). Fee changes are audited via the existing settings audit log; the UI adds a confirm step with a reason (W6-7).

### W2. Pricing endpoint and 402 payload in dollar terms
Files: `app/api/v1/billing_credits.py`, `app/schemas/credit.py`, `app/api/v1/transactions.py`.
- Replace tenant-facing `GET /billing/credits/packs` with `GET /billing/credits/pricing` returning: `fee_cents`, `fee_display`, `first_deal_free` (granted and not yet spent), `prepaid_deals` (balance), `bundle` (null, or `{size, bonus, total_deals, amount_cents, amount_display}` when the tenant is eligible), `test_mode`.
- `GET /billing/credits/wallet` keeps its shape and adds `fee_cents`/`fee_display` and `first_deal_free_remaining` so badges render without a second call.
- The 402 `details` from `create_transaction` add `fee_display` beside the existing `balance`/`cost`, so the paywall can title itself "Start this deal for $X" without an extra fetch.
- Checkout: `CreditPurchaseService.create_checkout` accepts `kind: 'single' | 'bundle'` (the tenant-facing `BuyCreditsRequest` schema swaps `pack_id` for `kind`) and computes credits and amount from settings (single: 1 credit for `deal_fee_cents`; bundle: `size + bonus` credits for `size * deal_fee_cents`). Product names in Stripe: "Velvet Elves: 1 deal" and "Velvet Elves: 12 deals (10 + 2 free)". The `credit_purchases` row records the exact credits and cents at purchase time, so a later fee change never mutates history; `pack_id` is already nullable, so no schema change. Webhook granting needs **zero dispatcher change**: verified that `_on_credit_purchase_paid` grants from the purchase row, not from pack data (`payment_event_dispatcher.py` lines 249 to 292). Refund reconciliation (`charge.refunded`) is unchanged.
- Bundle eligibility helper: tenant `created_at` inside `[deal_bundle_signup_from, deal_bundle_signup_until)` and `deal_bundle_enabled`. Evaluated server-side in both the pricing endpoint and checkout (never trust the client).
- Guard (R13): the settings PUT rejects `billing_enabled=true` while `deal_fee_cents` is 0, and checkout refuses to start while the fee is 0, so the unpriced-but-billing-on dead end cannot be configured.

### W2b. Purchase lifecycle: abandoned checkouts must not read as failures
Files: `app/services/payment_event_dispatcher.py`, `app/api/v1/platform_billing.py`, migration (W3), `STRIPE_CREDIT_BILLING_LOCAL_SETUP.md`, deploy webhook config.
Under pay-per-deal, opening Checkout and walking away becomes routine (it happens every time someone closes the Stripe tab), and today that leaves a `credit_purchases` row in `pending` forever: nothing handles `checkout.session.expired`, the status CHECK constraint does not even allow a terminal "abandoned" state, and the health card's `stuck_pending_purchases` counts **all** pending rows, so the operator signal would drown in noise. Fixes:
- New dispatcher branch for `checkout.session.expired`: mark the purchase `expired` (only from `pending`; a paid or refunded purchase is never touched). Stripe expires Checkout sessions after 24 hours by default.
- The W3 migration extends the `credit_purchases.status` CHECK from (pending, paid, failed, refunded) to include `expired`.
- `billing_health` counts as stuck only `pending` rows older than 25 hours (older than the Stripe expiry, meaning the expired event was missed), which restores the card's meaning: a nonzero count is a real webhook problem.
- The Stripe webhook endpoint subscription gains the `checkout.session.expired` event (production dashboard config and the Stripe CLI event list in `STRIPE_CREDIT_BILLING_LOCAL_SETUP.md`).

### W3. Migration
One new migration (next id after the latest applied migration, `20260907090000_agent_action_rules.sql`, so `20260908090000_flat_deal_fee.sql`), doing only:
- Deactivate the four seeded placeholder packs (`starter_1`, `pack_5`, `pack_10`, `pack_25`) so no pack-based product is sellable. Rows stay for FK integrity of old test purchases.
- Seed the new `platform_settings` keys with the W1 defaults (idempotent upsert).
- Extend the `credit_purchases.status` CHECK constraint with `expired` (W2b).
No other table shape changes: wallets, ledger, purchases, and the atomic RPC are reused as-is.

### W4. Park commission payouts and Stripe Connect
Files: `app/services/platform_settings_service.py`, `app/api/v1/payments.py`, `app/services/payment_access_service.py`, `app/api/v1/admin_payments.py`.
- New key `ve_commission_payouts_v1`, default `false`.
- When false: the two payout routes in `payments.py` return 404; the payment-capabilities response forces `can_trigger_payout=false` (which already hides the nav entry, `AppLayout.tsx` line 391, and the dashboards' `PaymentsWidget` payout block via its `showPayouts` prop); the capability policy in `payment_access_service.py` treats `payout.trigger` as denied regardless of the stored matrix, and the matrix API omits it (W6-6 hides the row in the UI).
- Nothing is deleted: tables, service code, and the page remain for the day a brokerage wants payouts, exactly as I told Jake ("park them").

### W5. Wording at the source
File: `app/schemas/credit.py` `_LEDGER_LABELS` (labels are generated server-side in one place):
`grant` becomes "Free deal", `purchase` becomes "Deals purchased", `spend` becomes "Deal started", `reversal` stays "Refunded", `adjustment` becomes "Adjustment by Velvet Elves". The free-grant reason string in `credit_wallet_service.py` becomes "Free first deal". Ledger `reason` fields keep the specifics (address on spends where available via `transaction_id`).

### W7. AI cost per deal: close Jake's Question 1 data ask
Files: `app/api/v1/platform_ai_usage.py` (tiny or none), `src/pages/platform/PlatformAIUsagePage.tsx`.
The API already returns the complete per-deal cost breakdown with decrypted address labels and a date window, but the page currently renders only the top 8 deals (`by_transaction.slice(0, 8)` at line 190): today there is no way to see, search, or total the full list, so Jake's question cannot be answered from the UI. Add, all client-side on the existing payload:
- A full by-deal table (every deal in the window, sorted by cost) replacing the top-8 list, with an address search box and a live "sum of shown deals" footer, so the deal entered multiple times (Jake's 5-counter-offer test) is one search away from a single total.
- "Average cost per deal" and "median cost per deal" stat tiles for the selected window.
- A CSV export of the by-deal table (blob + forced save, per the established download pattern).

### W8. Backend tests to add or adjust
- `test_credit_spend_gate.py`: extend to assert (a) draft save (`status='Incomplete'`) charges, (b) wizard-run autosave endpoints never charge, (c) 402 payload carries `fee_display`.
- New `test_deal_pricing.py`: fee/bundle settings round-trip; eligibility window edges (tenant created 2025-12-31, 2026-01-01, 2026-12-31, 2027-01-01); checkout refused while `deal_fee_cents=0`; settings PUT rejects `billing_enabled=true` while the fee is 0 (R13); single and bundle checkout amounts and granted credits.
- `test_credit_billing_webhook.py`: bundle purchase grants size + bonus once, replay-safe; `checkout.session.expired` marks a pending purchase `expired` and never touches a paid one. (A session cannot both complete and expire in Stripe, and the dispatcher's existing lifecycle guard already ignores paid events for purchases beyond pending/paid, so the new state slots into the guard that exists.)
- New `test_payout_parking.py`: payout routes 404 and `can_trigger_payout` is false when the flag is off (including for a role whose stored matrix row says allowed); behavior restored when on.
- Health: stuck-purchase count ignores fresh pending rows and counts only pending older than the Stripe expiry (W2b).
- Existing wallet/ledger tests stay green untouched (engine unchanged).

---

## 5. Frontend work plan

Design rules for every surface below: flat, modern specialized-tool aesthetic (flat headers, hairline dividers, sentence case, no gradient strips), `lucide-react` icons only, existing `ve-*` tokens, serif tabular numerals for the money figures (matching the current BillingPane balance treatment), all controls mouse-first, and the only typed input anywhere is the platform admin entering the fee. Screenshot verification against the rendered app is part of "done" for each item.

### W6-0. Remove the pre-entry balance gates (the workflow inversion)
Files: `src/contexts/IntakeContext.tsx`, `src/components/wizard/NewTransactionWizard.tsx`, `src/components/billing/CreditGateBlock.tsx`.
The two blockers built for the prepay model come out, because under the flat fee an empty wallet is the normal state, not an error (Section 2, Question 4):
- `IntakeContext.openNewTransaction` stops checking the balance (lines 75 to 94) and always navigates to the wizard; the context-level `CreditPaywallModal` mount (lines 198 to 202) is removed.
- The wizard's `entryBlocked` computation and the full-page `CreditGateBlock` return (lines 3218 to 3226 and 7747) are removed. `CreditGateBlock.tsx` is deleted; its zero-balance job no longer exists in the model.
- What remains before commit is disclosure, not obstruction: the rail badge (W6-4) and the fee-suffixed commit buttons (W6-5). The backend 402 stays as the single enforcement point, which the wizard already handles on both commit paths.
This consciously supersedes the 2026-06-19 click-time-gate requirement, which was correct for prepaid credits and wrong for pay-at-commit.

### W6-1. Organization > Billing pane (`BillingPane.tsx`)
Section label changes from "Billing & Credits" to "Billing" (`OrganizationPage.tsx` line 44, plus the Settings hub card; the tour step text already says just "billing" and needs no change, verified in `tourSteps.tsx`).
Layout, top to bottom, in the standard centered settings column:
1. **Plan summary.** "Pay per deal" with the fee as the hero figure ("$X per deal"), and one plain sentence: "Your first deal is free. You are charged when a new deal is saved, and a deal deleted within {reversal window} hours is refunded automatically." The hours render from the configured `reversal_window_hours`, never hardcoded, so a platform-admin change cannot make the copy lie. Test-mode badge stays.
2. **Prepaid deals** (rendered only when balance > 0): the count as the hero figure, with "Prepaid deals are used automatically before your card is charged." The free deal shows here as 1 prepaid deal with a "first deal free" tag.
3. **Bundle offer** (rendered only when eligible and enabled): a single flat tile, "Buy 10 deals, get 2 free", the total price, one Buy button straight to Stripe Checkout, and the existing return/confirming banners.
4. **History**: the ledger list with the new labels (Deal started / Deals purchased / Free deal / Refunded), unchanged pagination.
Removed entirely: the 4-pack grid, per-credit prices, and every occurrence of the word "credit". Non-manager and platform-admin-exempt notes keep their current placement with updated wording.

### W6-2. In-flow paywall (`CreditPaywallModal.tsx`)
Shown on 402 exactly as today, retitled "Start this deal for $X" (the fee comes straight from the 402 `details`, W2) with the saved-progress reassurance kept. Primary action: "Pay $X and start deal" (Checkout, `return_context='wizard'`). Secondary, only when eligible: the bundle tile ("Buy 10 deals, get 2 free"). Test-mode 4242 hint kept.
Non-managers get more than a dead end: alongside "ask a workspace owner or admin, your deal is saved", a one-click **"Notify your admin"** button sends an in-app notification through the existing notification system to the workspace owner/admins ("Agent X needs the deal fee paid to start 12 Oak Ridge Rd"). Under pay-per-deal every agent in a wallet-empty office hits this wall on every deal, so the escalation must be one click, not a hallway conversation.

### W6-3. Wizard-side Stripe return handler (new; nothing handles this today)
File: `src/components/wizard/NewTransactionWizard.tsx` (reusing `useCreditPurchaseStatus` from `useCredits.ts`, today used only by BillingPane).
Verified gap: checkout for `return_context='wizard'` redirects back to `/transactions/new?purchase_result=...`, but no code on that page reads those params; the returning user is currently saved only by the generic draft-resume prompt, and if the webhook has not granted yet they used to land on the zero-balance block. New behavior:
- On `purchase_result=success`: restore the wizard draft automatically (no prompt), show a calm "Confirming your payment with Stripe" banner while polling the purchase, and when it reports `paid`, re-run the interrupted commit exactly once, guarded against double submission; the deal completes without redoing intake. Which commit was interrupted (create versus save-draft) must survive the full-page redirect, so the paywall appends it to the checkout return URL (for example `pending_action=create`) next to `purchase_result`; the wizard state itself already survives via the draft stores. If polling exceeds ~20 seconds, keep the draft on screen with a "Finish deal" button and the banner switched to "taking longer than usual"; commit buttons stay disabled while confirming so a second checkout cannot be started.
- On `purchase_result=canceled`: restore the draft with a quiet "checkout canceled, nothing was charged" notice; the user can retry from the commit button.
- Clear the query params after handling (same pattern as BillingPane's `dismissReturn`).

### W6-4. Balance badge (`CreditBalanceBadge.tsx`)
States, in priority order: platform admin exempt ("No charge"); free deal unused ("First deal free"); prepaid > 0 ("N prepaid deals"); otherwise the fee ("$X per deal"). Still links to Organization > Billing, still renders nothing when billing is off. With the entry gates gone (W6-0), this badge and the commit-button suffix (W6-5) are the only pre-commit signals a user gets, so the badge moves from nice-to-have to required on every wizard variant, including the embedded modal.

### W6-5. Fee disclosure at the commit points (`NewTransactionWizard.tsx`)
The two charging buttons disclose the consequence inline when billing is enabled: "Approve & Create · $X" / "Save draft · $X", switching to "· uses 1 prepaid deal" or "· free deal" when the wallet covers it. This makes the agreed R3 trigger visible at the exact moment it fires, and it is the whole remaining "move the charge point" work item, since the mechanics already match Section 2 Question 4.

### W6-6. Parked payouts in the UI
With `ve_commission_payouts_v1` off: the Commission Payouts nav entry disappears (already driven by `canTriggerPayout`), the route renders a plain "not enabled" state instead of the page, the Payments dashboard widget drops its payout block, and `AdminPaymentAccessPage.tsx` hides the `payout.trigger` capability row. Invoices & Payments is untouched.

### W6-7. Platform admin billing page (`PlatformBillingPage.tsx`)
Rebuilt as three flat cards in the standard settings shell:
1. **Billing settings**: billing on/off, fee per deal (dollar input), free first deals (count, 0 disables, matching the existing `credit_free_intake_count` setting rather than inventing a separate toggle), refund window hours, and the bundle group (enable, size, bonus, signup window date pickers). Saving a fee change opens a confirm dialog showing old and new price with a required reason, written to the audit log (preserves the pack editor's price-change discipline). The billing on/off toggle is disabled with an inline explanation while the fee is $0 (R13), mirroring the server-side rejection so the dead end cannot be configured from either side.
2. **Stripe health**: existing health fields (mode, webhook configured, pending webhooks, stuck purchases); the pack-price checks are replaced by a "fee not set" warning when billing is on with `deal_fee_cents=0`.
3. **Pricing insight**: average and median AI cost per deal for the last 30 days with a link to the AI Usage page, so the person setting the fee sees the number the fee must beat, on the same screen.
The pack CRUD UI is removed. `TenantDetailModal.tsx` relabels balance to "Prepaid deals" and the grant action to "Grant deals" (same endpoints).

### W6-8. Copy sweep
Repo-wide check that no tenant-facing string says "credit" (component text, toasts, tooltips, tour steps, empty states). Platform-admin surfaces may keep the word only inside the audit log summaries.

---

## 6. Unchanged and parked (explicit non-goals)

- **Invoices, client payments, refund rails, payment access matrix, manual sales tax**: untouched (Sections 2 and 4 of the guide are live and Jake raised no change; Question 6 will land as configuration).
- **Commission payouts / Stripe Connect**: parked behind the flag, code kept (Question 4).
- **Credit wallet engine, RPC, webhook pipeline**: unchanged by design (Question 3 fallback).
- **Auto-charge with a saved card** (no Checkout redirect per deal): not built now; noted for Jake as a later convenience once volume justifies it. The bundle covers the heavy-use case in the meantime.
- **Monthly subscription layer**: not built; Stripe supports adding it beside the per-deal fee without touching the ledger.
- **Automatic tax calculation**: not built unless Jake's Question 6 answer requires it.
- **Requirements alignment note.** Parking payouts does not shrink the committed scope: `requirements.txt` §2.5/§7.7 and Milestone 5.2 ask for invoicing, payment tracking, refunds, and commission *tracking*, all of which stay live; only the money-movement leg (Stripe Transfers to a connected bank) is parked, and Jake explicitly ruled it out of launch in Question 4.
- **Future auto-intake invariant (R12).** When the transaction-processing evolution work adds automatic intake of emailed contracts, those deals must pass the same consumption point or carry an explicit no-charge-until-commit decision. Recorded here so the two plans cannot drift apart on billing.

---

## 7. Deliverables that answer Jake directly

**D1. This plan** (the system update).
**D2. AI cost per deal memo** (answers his Question 1 ask): after W7 lands, I will pull the per-deal cost table from the platform AI Usage page for the full test window, including the 5-counter-offer deal summed across every re-entry (address search), and write a one-page memo: cost per test deal, average and median, the heavy-deal versus clean-deal spread, the caveat that today's data is mostly demo deals, and a worked pricing example (fee = average AI cost times a margin multiple, checked against the heaviest observed deal). Format follows the established Jake-doc rules: answer only what was asked, every number traceable to the screen it came from.

---

## 8. End-to-end UI test script (for real-estate testers, mouse only)

Preconditions the testers receive ready-made: billing ON in test mode, fee set to a visible number (for example $50), bundle promo ON, one fresh brokerage account created after 2026-01-01, Stripe test card 4242 4242 4242 4242.

- **T1 First deal free.** Sign in on the fresh brokerage, open New Transaction, note the wizard badge says "First deal free", complete an intake, click "Approve & Create · free deal". Expect: deal created, no payment screen, Organization > Billing history shows "Free deal" then "Deal started".
- **T2 Pay per deal.** Start a second deal, click "Approve & Create · $50". Expect: "Start this deal for $50" appears, Pay leads to Stripe, card 4242 pays, the return lands back in the wizard with the intake restored and a "Confirming your payment" banner, and the deal then completes on its own without redoing any step; history shows "Deals purchased +1" then "Deal started".
- **T2b Canceled checkout.** Repeat T2 but click the browser Back / cancel link on the Stripe page. Expect: return to the wizard with the intake restored and a "checkout canceled, nothing was charged" notice; no history entry; the deal can still be committed later.
- **T3 Charge on draft save.** Start a third deal, click "Save draft · $50" mid-wizard. Expect: same paywall and charge; after paying, the draft appears in the transactions list as Incomplete and is finished from the transaction workspace (there is no wizard re-entry for a committed draft); history shows the charge.
- **T4 Abandoned intake never charges.** Start a deal, fill two steps, close the tab. Expect: no charge anywhere in history; reopening the wizard offers the draft back.
- **T4b Empty wallet never blocks the door.** With zero prepaid deals, click New Transaction from the sidebar, the dashboard button, and the search palette. Expect: the wizard opens every time and the whole intake can be completed; the fee appears only on the commit buttons and the paywall appears only when one is clicked. No screen ever says you need credits to begin.
- **T5 The oops window.** Delete the T3 draft within 24 hours (row action, confirm dialog). Expect: history shows "Refunded +1" and the prepaid count rises by one.
- **T6 Bundle.** In Organization > Billing, click Buy on "Buy 10 deals, get 2 free", pay $500. Expect: "Prepaid deals: 12" (plus any refund from T5), history shows "Deals purchased +12".
- **T7 Prepaid consumption.** Create a deal. Expect: commit button reads "· uses 1 prepaid deal", no payment screen, count decreases by one.
- **T8 Member without billing rights.** As a plain agent with zero prepaid deals, hit the paywall at commit. Expect: the "ask a workspace owner or admin, your deal is saved" state with a "Notify your admin" button and no Buy buttons; clicking it produces a notification for the owner naming the agent and the deal; after the owner buys, the agent reopens the wizard, accepts the draft-resume prompt, and commits the same deal without redoing intake.
- **T9 Ineligible for bundle.** On a brokerage created outside the promo window (platform admin can temporarily narrow the window), open Billing. Expect: no bundle tile anywhere, pay-per-deal unaffected.
- **T10 Fee change.** Platform admin changes the fee to $60 (reason required). Expect: badges, paywall, and commit buttons all show $60 on next load; T6's history still shows the old totals.
- **T11 Admin refund.** Platform admin refunds the T6 purchase from the tenant detail. Expect: history shows the clawback, balance never goes negative.
- **T12 Payouts parked.** As every role, confirm Commission Payouts appears nowhere (nav, dashboards, Payment Access matrix). Invoices & Payments works as before.
- **T13 Billing off.** Platform admin turns billing off. Expect: Billing section, badges, and paywalls disappear; deal creation is free and unlabeled.

Every step is a click path with an on-screen expected result, so a non-developer can verify the whole system from the UI alone.

---

## 9. Rollout sequence (Question 1 "when")

1. **Build** (this plan), billing off; nothing changes for any user.
2. **Internal test mode**: I enable billing in test mode on staging, run the full Section 8 script (T1 to T13 including T2b and T4b), screenshot pass.
3. **Jake's test window**: billing on in test mode in production (practice cards, no real money) while his team enters real deals for a few weeks; the AI Usage page accumulates trustworthy per-deal costs; D2 memo delivered; Jake sets the fee.
4. **Go live**: platform admin zeroes leftover test balances via the grant/adjust tool (rollout checklist item, so nobody launches with free test deals), sets the live fee, flips Stripe keys to live, billing on. The Stripe health card must show mode "live", webhook configured, zero stuck purchases.

---

## 10. Decisions I still need from Jake

1. **The fee amount**, after the D2 memo. (Blocks go-live, not the build.)
2. **Bundle scope**: 2026 signups only (the current default in this plan) or open-ended? Adjustable at any time via the signup-window settings.
3. **Bundle refunds**: my recommendation, refund a bundle only while fully unused and within 30 days, platform-admin discretion beyond that. (The 24-hour deal refund is separate and stays.)
4. **Question 6**: default payment permissions per role, and whether any market needs automatic sales tax. Lands as configuration whenever answered.
5. Later, not blocking: the optional monthly fee layer, and auto-charge with a saved card once per-deal Checkout feels like friction.

---

## 11. Execution order, dependencies, and acceptance

| # | Work item | Depends on | Acceptance |
|---|---|---|---|
| 1 | W1 settings keys + W3 migration | none | Settings round-trip via platform API; packs deactivated; status CHECK extended |
| 2 | W2 pricing endpoint, checkout kinds, 402 fee payload, R13 guard | 1 | W8 pricing tests green |
| 3 | W2b purchase lifecycle (expired webhook, stuck-count age filter) | 1 | W8 webhook/health tests green |
| 4 | W4 payout parking flag | 1 | W8 parking tests green |
| 5 | W5 ledger labels + copy at source | none | Wallet/ledger responses show deal wording |
| 6 | W6-0 remove pre-entry gates | 2 | T4b passes; `CreditGateBlock.tsx` gone; wizard reachable at zero balance |
| 7 | W6-3 wizard Stripe-return handler | 2, 6 | T2 and T2b pass, including a simulated slow webhook in dev |
| 8 | W6-1, W6-2, W6-4 tenant billing surfaces | 2, 5 | T1, T6, T8, T9 pass; screenshots match the flat settings aesthetic |
| 9 | W6-5 commit-button disclosure | 2 | T1, T3, T4, T7 pass |
| 10 | W6-6 payout UI removal | 4 | T12 passes |
| 11 | W6-7 platform billing page | 2 | T10, T11, T13 pass; billing toggle blocked at $0 fee |
| 12 | W7 AI usage table/search/average/export | none | The 5-counter-offer deal total is one search away; CSV downloads |
| 13 | W6-8 copy sweep + full T1 to T13 run (incl. T2b, T4b) + screenshot pass | all | No tenant-facing "credit"; script passes end to end |
| 14 | D2 memo to Jake | 12 + test-window data | Memo delivered with traceable numbers |
| 15 | Docs: rewrite guide Section 5 in flat-fee terms, update Section 3 as parked, refresh Section 7 with the settled answers; sweep Help Center billing articles; update `STRIPE_CREDIT_BILLING_LOCAL_SETUP.md` with the expired event | 13 | Guide matches the shipped UI, per the answer-only-what-is-asked rule |

Items 1 to 5 are backend and test-first; 6 to 11 are frontend against the running backend with screenshot verification (6 and 7 first, because every later tenant-surface test assumes the gates are gone and the return leg works); 12 to 15 close the loop with Jake. No step requires a tester to touch anything but the UI, and no step charges real money before stage 4 of the rollout.

---

## Appendix A: Rev 2 review log (what the second pass found and changed)

I re-audited Rev 1 of this plan against the implemented source before any build work, specifically hunting workflow and logic errors. Five findings, all corrected above:

1. **Rev 1 kept a gate that breaks the approved workflow (worst finding).** W6-3 originally kept `CreditGateBlock` as a "safety net for direct URL entry at zero balance", and no work item touched the click-time gate in `IntakeContext.tsx` lines 75 to 94 at all. Verified in source: both gates block the wizard whenever `balance < cost`. Under pay-per-deal, zero balance is the everyday state, so Rev 1 would have paywalled every deal at the first click, contradicting the trigger Jake approved in Question 4 and making the pay-at-commit loop unreachable after the free deal. Fixed by the new W6-0 (remove both gates, delete the component), rule R3's corollary, and test T4b.
2. **Rev 1 assumed a Stripe-return resume that does not exist.** The old T2 said "return lands back in the wizard, deal completes", but no code under `/transactions/new` reads `purchase_result` (only `BillingPane` does), and a webhook slower than the redirect would have stranded the payer on the zero-balance block. Fixed by the new W6-3 (return handler with purchase polling, one-shot auto-commit, cancel state), rule R5 rewritten, tests T2/T2b.
3. **Abandoned checkouts would have poisoned the health signal.** Nothing handles `checkout.session.expired`, the purchase status CHECK has no terminal abandoned state, and `stuck_pending_purchases` counts every pending row regardless of age; with in-flow per-deal checkouts, routine walk-aways would read as failures. Fixed by W2b and the CHECK extension in W3.
4. **Two factual errors.** The migration id baseline was stale (`20260907090000_agent_action_rules.sql` is the latest, not the `20260906*` series), and W7 implied a full by-deal table exists when `PlatformAIUsagePage.tsx` line 190 renders only the top 8 deals. Both corrected.
5. **Under-specified escalation for non-managers.** With pay-at-commit, a plain agent in a wallet-empty office hits the paywall on every deal and Rev 1 offered only "ask your admin" text. Added the one-click "Notify your admin" action in W6-2 and extended T8.

Also verified and now stated with evidence rather than assumption: the webhook grants from the purchase row so the pack-to-kind checkout change needs no dispatcher work (`payment_event_dispatcher.py` lines 249 to 292); `transactions.py` line 233 is the only live transaction-creation call (the auto-email sweep writes email drafts, not transactions; `TransactionForm`'s direct POST is dead code); committed Incomplete drafts are finished from the transaction workspace, not by re-running the wizard, so there is no double-charge path on resume; and `SYSTEM_DESIGN.md` itself lists "Per-intake pricing" via Stripe as the Phase 5 design, confirming the model.
