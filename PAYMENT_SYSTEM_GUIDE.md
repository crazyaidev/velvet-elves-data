# Payment and Billing System - A Guide to How Velvet Elves Handles Money

**Audience:** Jake and Audri, reviewing how the product handles money (no technical background needed)
**What this covers:** Every place money moves through Velvet Elves today, screen by screen: how an office bills a client and gets paid online, how a commission payout works, who is allowed to take payment actions, and how the platform would charge a brokerage per deal once pricing is set
**Last updated:** June 24, 2026

---

## 1. The big picture

Two different kinds of money move through Velvet Elves, and it helps to keep them apart from the start:

1. **Money your clients pay you.** A brokerage can bill a client, send them a secure link, take the card payment online, and pay a commission out to the brokerage's account, all without leaving the app. This is a finished, working part of the product.
2. **What it costs to use Velvet Elves.** Separately, the platform can charge each brokerage to use the software, on a simple "one credit per new deal" basis. This is fully built but deliberately turned **off** until you set the prices. Nothing charges anyone today.

The rest of this guide walks through both, screen by screen. Four promises hold the whole thing together:

- **Card details never touch Velvet Elves.** Every card number is typed on Stripe's own secure, hosted page, not on ours. We only ever see a confirmation and the last four digits. This keeps the platform at the lightest possible level of card-security obligation.
- **The money record follows the bank, not the browser.** An invoice is marked paid only when Stripe confirms the money actually moved. Closing a tab, refreshing the page, or a link being clicked twice can never create a false "paid" or charge anyone twice.
- **It is honest when it is not set up.** If the payment keys are not in place, the system says plainly that payments are not configured rather than pretending to work. The same is true of credit billing: until it is switched on with real prices, it stays invisible and inert.
- **Every money action is recorded.** Creating an invoice, taking a payment, issuing a refund, triggering a payout, and granting credits are all written to the audit log with who did it and when.

### Where this lives in the app

| What you are doing | Where it lives | What it looks like |
|---|---|---|
| Bill a client | Payments, then Invoices & Payments (`/payments`) | A searchable table of invoices with colored status pills and a "New invoice" button |
| Take a card payment | The secure link in the invoice email, or the client's own portal | A clean, single-amount "Secure Payment" card that hands off to Stripe |
| Pay a commission out | Payments, then Commission Payouts (`/payments/payouts`) | A table of payouts and a "Trigger payout" button |
| Decide who may take payment actions | Settings, then Payment Access (`/admin/payment-access`) | A per-role grid of three on/off payment powers |
| See what a deal costs your office | Settings, then Organization, then Billing (`/organization`) | A credit balance, packs you can buy, and a history list |
| Run the money settings (Velvet Elves staff only) | Platform, then Billing (`/platform/billing`) | Packs, prices, the master on/off switch, and a health strip |

---

## 2. Collecting money from your clients (invoices)

This is the everyday flow: an office bills someone on a deal (a buyer, a seller, or anyone else), the client pays online by card, and the deal moves forward.

### The Invoices & Payments page

**How to get there:** the **Payments** group in the left sidebar, then **Invoices & Payments** (`/payments`).

- **Header:** the title "Invoices & Payments", a small count badge ("12 invoices"), and an orange **"New invoice"** button on the right. The button only appears if your role is allowed to invoice (see Section 4).
- **A row of filter tabs:** **All Invoices**, **Open**, **Paid**, **Drafts**, **Void**, and a separate **Payments** tab that lists the individual card payments that have come in.
- **A search box** that finds an invoice by its number, the payer's name, or the property address.
- **The list itself:** each invoice is a row showing its number, the payer, the property, a colored **status pill**, the total, and the due date. Click any row to open it.

If you have not made an invoice yet, the empty page tells you how to start: the **"New invoice"** button here, or the **"Invoice deal"** action inside any transaction, which opens the same form already filled in for that deal.

### Creating an invoice

Clicking **New invoice** opens a single form:

- **Transaction (optional).** Search for the deal by address. Picking one lets the form show you exactly who is on that deal to bill, and lets you tie the invoice to a task. You can also leave it blank to bill someone outside of any deal.
- **Bill to (the payer).** When a deal is selected, you choose from the people already on it (the buyer, seller, co-op agent, and so on). You can also search your whole contact list, or bill someone who is not on the deal at all.
- **Due date, tax, and a short terms note** ("Net 7. Payment due upon receipt.").
- **Line items.** One row per thing you are charging for: a description, a quantity, and a unit price. The form adds up the **subtotal, tax, and total** live as you type.
- **Link to a task (optional).** If you tie the invoice to one or more open tasks on the deal, those tasks are **marked complete automatically the moment the invoice is paid**.

At the bottom you can **Save draft** (keep it private for now) or **Send now** (create the secure link and email it straight away).

### Sending it

When you send an invoice, three things happen:

- The system creates a **secure Stripe Checkout link** for the exact amount.
- It **emails that link to your client from your own connected email account**, the same Gmail, Outlook, or email service you use elsewhere in the app, so it comes from you, not from a stranger.
- It also produces a **clean Velvet Elves payment page** the client can open without logging in.

If your email is not connected yet, the invoice is still created and the secure link is **copied to your clipboard** so you can paste it to your client yourself. The invoice moves from **Draft** to **Open**. Resending later reuses the same link rather than making a new one.

### How your client pays

Your client does not need an account. They have two equally good ways in:

- **The secure link** (from the email) opens a simple page headed **"Secure Payment, Velvet Elves Invoice"**. It shows the property, the amount due, and the due date, with one button: **"Continue to Secure Checkout."** The page reassures them in plain words: **"Velvet Elves never sees your card details."** It hands them straight to Stripe's hosted checkout to enter their card.
- **The client portal.** Buyers and sellers who are signed in to their own Velvet Elves portal see their invoices under **Payments** and can pay an open one there.

### Getting paid (what happens on its own)

Once the card clears, the system does the rest without anyone clicking anything:

- The invoice flips to **Paid**.
- A **payment record** is saved, including the card brand and last four digits, the amount, and the date.
- Any **linked tasks are marked complete** (and stamped as completed by payment).
- A short **"Invoice paid"** note is added to the deal's activity history.
- An **accounting event** is sent to any bookkeeping tool the office has connected, so the books can stay in sync.

Because this is driven by Stripe's confirmation and not by the client's browser, it is safe against double clicks, refreshes, and retries.

### Refunds

From a paid payment, someone with the right permission can issue a **full or partial refund** with a reason. Stripe processes it and the payment's status updates to **Partially refunded** or **Refunded**. If a refund is ever done directly inside Stripe instead of in our app, the system still notices it and keeps our records in step.

### What the status words mean

| Status | Meaning |
|---|---|
| **Draft** | Created but not sent. Only drafts can be edited or deleted freely. |
| **Open** | Sent and waiting to be paid. The secure link is live. |
| **Paid** | The money has cleared. Linked tasks are completed. |
| **Void** | Canceled before payment, so it can no longer be paid. |
| **Partially refunded / Refunded** | Some or all of a paid amount has been returned. |

---

## 3. Paying a commission out (commission payouts)

The flip side of taking money in is sending money out. The **Commission Payouts** page (`/payments/payouts`, under Payments) lets an authorized person send a commission to the brokerage's own connected account.

- A **"Trigger payout"** button opens a small form: the **amount**, a **payee label** ("Brokerage, Q3 commission"), an optional **deal** to attach it to, and a note.
- Submitting it starts a **transfer to the brokerage's connected bank account through Stripe**. The payout shows as **Pending**, then **In transit**, then **Paid** as Stripe reports each step back.

One honest caveat: this requires the brokerage's bank to be **connected to the platform through Stripe Connect** first. Until that connection exists, the button is there but a transfer cannot actually complete. Whether brokerages want the platform to move their commission this way, and will connect a bank to do it, is one of the questions in Section 7.

---

## 4. Who is allowed to touch money (Payment Access)

Not everyone in an office should be able to bill clients or move money, so payment powers are controlled in one place: **Settings, then Payment Access** (`/admin/payment-access`, administrators only).

It is a simple grid. For each internal role, **Agent**, **Elf (Transaction Coordinator)**, and **Team Lead**, an administrator can switch on or off three powers:

- **Create and send invoices**
- **Refund payments**
- **Trigger commission payouts**

Two safety rules are built in and cannot be toggled away:

- **Administrators and the workspace owner always have every power.**
- **Outside parties, attorneys, vendors, clients, and for-sale-by-owner sellers, never have any of them**, so a stray setting can never hand invoicing to someone outside the brokerage.

These switches decide both what buttons a person sees and what the system will let them do.

---

## 5. What it costs to use Velvet Elves (credits)

Everything above is about your clients' money. This section is about **how the platform charges the brokerage** to use the software. It is fully built, runs on the same trusted Stripe plumbing, and is **turned off by default**. Nothing here charges anyone until you decide the prices and switch it on.

The model is deliberately simple: a brokerage buys **credits**, and **creating a new deal spends one credit**.

### The wallet

Each workspace has **one shared credit wallet**. Credits **never expire**, and the whole team draws from the same balance. A brand-new workspace is given a small number of **free starter credits** (one, by default) so it can try the product before buying anything.

### Where a credit is spent

There is exactly **one** place in the entire system where credits are used: the moment you **Approve and Create** a new deal at the end of the AI Wizard. That keeps the cost predictable, one deal, one credit (by default), and nothing else ever quietly draws the balance down.

### Running out in the middle of a deal

If the wallet is empty when someone tries to create a deal, they see a calm **"You're out of credits"** panel, not an error and not a lockout. Crucially, **the in-progress deal is already saved as a draft**, so nothing is lost. From there:

- Someone who can buy credits picks a pack, pays through Stripe, and is returned right back to finish the same deal.
- Someone who cannot buy is told plainly to ask a workspace owner or admin, and reassured the deal is parked safely until then.

### Buying credits

The brokerage's billing home is **Settings, then Organization, then Billing**. It shows:

- A big **credit balance** and a reminder of how many credits a deal costs.
- A row of **packs** to buy, each showing the number of credits, the price, and the price per credit.
- A **credit history** list: every grant, purchase, spend, and reversal, with the running balance.

Buying a pack hands off to **Stripe's hosted checkout**. The credits are added **only after Stripe confirms the payment**, never just because the person clicked back, so a closed tab or a double click can never hand out free or double credits.

### Getting a credit back

If a deal is deleted shortly after it was created (within a window the platform sets, **24 hours** by default), the credit that was spent on it is **automatically refunded** to the wallet.

### The platform controls (Velvet Elves staff only)

Behind the scenes, a Velvet Elves platform administrator runs the whole credit system from **Platform, then Billing** (`/platform/billing`). From there they can:

- **Turn credit billing on or off** for the whole platform (it is off today).
- Set the **price and size of each pack**, how many **free starter credits** a new workspace gets, **how many credits a deal costs**, and the **refund window**.
- View **any brokerage's wallet**, and **grant or adjust** credits by hand when needed.
- **Refund a credit purchase.**
- Read a **health strip**: whether Stripe is in test or live mode, whether the confirmation channel is connected, and whether anything is stuck.

Platform staff accounts are never themselves charged credits.

### Test mode

While the platform is connected to Stripe's practice (test) keys rather than live ones, every billing screen wears a small **"Test mode, provisional pricing"** badge and even tells the tester which practice card to type. This makes it obvious at a glance that no real money is moving yet.

---

## 6. How the money actually moves (in plain terms)

You do not need the technical detail, but a few design choices are worth knowing because they are the reason the system is safe to hand to clients:

- **One payment company: Stripe.** All card handling, online checkout, payouts, and refunds run through Stripe. The product is built so that if a second payment company were ever needed, it could be added in one place.
- **Card numbers are entered on Stripe's page, not ours.** Because we never collect or store card data ourselves, the platform stays at the lightest tier of card-security responsibility. We hold only safe references and the last four digits for display.
- **The bank's confirmation is the single source of truth.** Invoices are marked paid, credits are added, and refunds are recorded only when Stripe sends a verified confirmation. These confirmations are checked for authenticity and handled so that the same message arriving twice has no extra effect. This is what makes double charges and false "paid" states impossible.
- **Everything is written down.** Every invoice, payment, refund, payout, and credit change lands in the audit log, attributed to the person (or to Stripe, when the bank is the actor).

---

## 7. A few decisions we need you to confirm

The collecting-from-clients side (Sections 2 to 4) is built and ready. The platform-charging side (Section 5) is built but waiting on you, because the right answer is a business decision, not an engineering one. As with the transaction guide, each item below gives what it is about, how it works today, what we suggest, and the call we need from you.

### Question 1 - Whether to start charging per deal at all

**What this is about.** The whole credit system in Section 5 is the planned way Velvet Elves earns from each brokerage. It is finished, but switched off.

**How it works today.** Billing is off platform-wide. Every brokerage uses the product without spending or buying anything, and no billing screens charge real money.

**What we suggest.** Keep it off until the prices below are settled, then turn it on first in test mode (practice cards, no real charges) so we can watch a full buy-and-spend cycle before a single real dollar moves.

**Your call.** Do you want to move toward per-deal billing on this credit model, and if so, roughly when?

**Jake's answer**: We feel like this should be per deal only because AI costs so many credits that we need to be profitable and if we charge a per deal basis some deals we’re going to lose on and other deals we’re going to win on but we can count on winning at least to some level when we understand the credit usage or token usage for AI on an average deal.

**Response:** Per deal is exactly what the system is built to do: there is one charge point (when a deal is created), so cost tracks deals, not seats or months. The number your answer hinges on, average AI cost per deal, is already measured: we record the token cost of every AI call and the platform admin screen totals it by deal and by office. Two cautions before locking a price: that data is mostly demo deals today, so we need a few weeks of real deals in test mode to trust the average; and cost is not flat, since a heavy deal with many counters and addenda costs more to parse than a clean one. I would price with margin above the average, so we win on the typical deal even when we give a little back on the occasional heavy one.


### Question 2 - The price of a credit and the cost of a deal

**What this is about.** Three numbers define the economics: how many credits a new deal costs, how much a credit is sold for (and in what pack sizes), and how many free starter credits a new brokerage receives.

**How it works today.** The system is set to the safe placeholders of one credit per deal and one free starter credit, with no real pack prices loaded. Earlier planning floated candidate figures (for example, a platform fee in the range of fifty dollars per transaction), but nothing is locked in.

**What we suggest.** Set a simple, round price per credit and two or three pack sizes with a small volume discount, keep a deal at one credit so the math stays obvious to the customer, and offer one free starter credit so a new office can try a real deal first.

**Your call.** What should a credit cost, in what pack sizes, how many credits should a deal cost, and how many free starter credits should a new brokerage get?

**Jake's answer**: For now let’s just charge a flat fee and not worry about credits or discounts or anything of that sort until we have a good idea of AI impact token usage and user input.

**Response:** Agreed, and this is a simplification, not a rebuild. The engine underneath is the same Stripe plumbing whether we call it a credit or a flat per-deal fee, so I will drop the packs, per-credit pricing, and volume discounts and show a single flat charge per deal, with the same safety (no double charges, every charge recorded). The only open number is the dollar amount, which depends on the AI-cost data from Question 1. Two confirmations when ready: whether a new office still gets its first deal free (it does today), and whether the fee is charged per deal at the start (Question 4) rather than pre-bought. I recommend charging at the start, so there is no balance for the customer to track.


### Question 3 - The shape of the charging model

**What this is about.** Per-deal credits is one way to charge. The alternatives are a flat monthly subscription, a per-seat price, or a blend (for example, a base subscription plus credits for volume).

**How it works today.** Only the per-deal credit model is built. It bills by activity, so a quiet month costs the brokerage little.

**What we suggest.** Lead with per-deal credits because it lines up cost with value (an office pays as it does deals) and is the simplest thing for a customer to understand. We can layer a subscription on later if the market wants predictability.

**Your call.** Is per-deal credits the model you want to launch with, or should we plan for seats, a subscription, or a hybrid?

**Jake's answer**: 


### Question 4 - Commission payouts and connecting a bank

**What this is about.** Section 3 can send a commission to a brokerage's account, but only once that brokerage's bank is connected to the platform through Stripe Connect.

**How it works today.** The payout feature works, but no brokerage bank is connected, so a real transfer cannot complete yet. Setting up Stripe Connect is an onboarding step for each brokerage.

**What we suggest.** Treat payouts as an opt-in feature for offices that actually want the platform to move commission, and build the short bank-connection step only when we have a brokerage that wants it.

**Your call.** Do your target brokerages want Velvet Elves to move commission for them, and are they willing to connect a bank account to do it?

**Jake's answer**: For this question specifically we’re only billing through Stripe and the billing starts when they begin the transaction not at the end. They can decide to charge their client a transaction fee of whatever they ‘d like and they can collect it on the settlement statement but as far as we are concerned we charge our flat fee plus or minus any monthly fees that we decide.

**Response:** Understood, and this simplifies the build. First, on commission: if we are not moving brokerages' commission and they collect any client fee themselves on the settlement statement, then the Commission Payouts feature and the Stripe bank-connection step are not needed for launch, and I will park them, which removes the only piece requiring a brokerage to connect a bank. Second, on timing: today the charge fires at the end of intake (Approve and Create), not the start. To match "billing starts when they begin the transaction," I will move it to the first save of a new deal (when the agent commits and we create the record), not the very first click, so we never charge for a deal opened by mistake and abandoned. Say if you prefer a different trigger. Finally, "plus or minus monthly fees" means a flat per-deal fee now with an optional monthly fee later; Stripe handles both. That also answers most of Question 3: flat per-deal now, optional monthly layer later.

### Question 5 - Refund rules

**What this is about.** Two refund questions sit open: how generously we refund a credit purchase, and how long the window should be to auto-refund the credit when a brand-new deal is deleted.

**How it works today.** A platform admin can refund a credit purchase by hand, and a credit is automatically returned if its deal is deleted within twenty-four hours.

**What we suggest.** Keep the twenty-four-hour auto-refund on deletion as a fair "oops" window, and decide a plain rule for purchase refunds (for example, unused credits refundable within thirty days).

**Your call.** What window should the deletion refund use, and what is your policy for refunding bought-but-unused credits?

**Jake's answer**: Good with the suggestion.

**Response:** Good. The 24-hour auto-refund on deleting a brand-new deal is already live and the window is adjustable, so I will leave it at 24 hours. One note: if we charge a flat fee per deal at the start (Questions 2 and 4) instead of prepaid packs, there are no bought-but-unused credits to refund, so the only refund case is that same 24-hour window, already built, and the separate 30-day policy becomes unnecessary. If you keep prepaid packs as an option later, I would enforce the 30-day rule then.


### Question 6 - Default invoicing permissions and sales tax

**What this is about.** Two smaller defaults: which roles can invoice and refund out of the box (Section 4), and how sales tax is handled on an invoice.

**How it works today.** Permissions start conservative and an administrator opens them up per role. Tax is entered as a single manual amount on each invoice.

**What we suggest.** Confirm a sensible starting point (for instance, agents and coordinators can invoice but not refund, team leads can do both), and keep tax manual for now unless your markets need automatic tax calculation.

**Your call.** What should the default payment permissions be for each role, and do you need automatic sales-tax calculation on invoices?

**Jake's answer**:

---

## 8. Quick reference

### Pages used in this workflow

| Page | Where to find it | What it looks like |
|---|---|---|
| Invoices & Payments | Sidebar, Payments group (`/payments`) | A searchable table of invoices with status pills, filter tabs, and "New invoice" |
| Commission Payouts | Sidebar, Payments group (`/payments/payouts`) | A table of payouts and a "Trigger payout" button |
| Secure pay page | The link in the invoice email (`/pay/invoices/...`) | A single-amount "Secure Payment" card that hands off to Stripe; no login |
| Client invoices | The client's own portal, Payments | A buyer or seller's own invoices, with a pay button on open ones |
| Payment Access | Settings, then Payment Access (`/admin/payment-access`) | A per-role grid of three payment powers |
| Organization, Billing | Settings, then Organization (`/organization`) | The credit balance, packs to buy, and credit history |
| Platform Billing | Platform, then Billing (`/platform/billing`) | Packs, prices, the on/off switch, per-tenant wallets, and a health strip |

### Glossary

- **Invoice** - a bill you send a client, with line items and a total, payable online by card.
- **Stripe Checkout** - Stripe's own secure, hosted page where the client actually types their card. Velvet Elves never sees the card.
- **Payment** - a recorded card payment against an invoice, showing the amount, card brand, and last four digits.
- **Commission payout** - money sent from the platform to a brokerage's connected bank account through Stripe.
- **Refund** - returning some or all of a paid amount to the payer.
- **Payment Access** - the per-role switches that decide who may invoice, refund, or trigger payouts.
- **Credit** - the unit the platform sells to a brokerage; creating a deal spends one (by default).
- **Credit wallet** - the workspace's shared, never-expiring credit balance, used only when a deal is created.
- **Credit pack** - a sellable bundle of credits at a set price.
- **Reversal window** - the short period (twenty-four hours by default) in which deleting a new deal refunds its credit.
- **Test mode** - the practice state, using Stripe's test keys and test cards, where no real money moves.
