# Milestone 5.2 — Payment Features Testing Guide

**For:** Real Estate Agents, Transaction Coordinators, and Team Leads (non-technical testers)
**Last updated:** 2026-05-27

---

## What You Are Testing

Milestone 5.2 adds the ability to **send invoices, collect payments, and issue refunds** inside Velvet Elves. Think of it like this:

- You create an invoice for a deal (e.g., "TC fee for the Smith transaction — $495").
- You send it to the client or seller with one click.
- They receive an email with a secure "Pay Now" button.
- They pay with their credit card on a Stripe-hosted page (Stripe is the same payment company that powers many real estate tools).
- The moment payment goes through, the system automatically marks the related task as done, updates the dashboard, and logs everything — no manual steps required.

You are here to confirm this all works correctly.

---

## Before You Start

Ask the developer to confirm the following are ready before you begin. You do not need to do this yourself — just make sure they check the box.

- [ ] The test environment (`https://dev.velvetelves.com`) is running.
- [ ] Stripe is in **test mode** (no real money is used in any of these tests).
- [ ] You have login credentials for each role: **Admin, Agent, Transaction Coordinator (TC), Team Lead, and Client**.
- [ ] At least one active transaction exists in the system so you can attach an invoice to it.
- [ ] There is at least one open task on that transaction (e.g., "Collect compliance fee").
- [ ] The developer has confirmed the test card numbers below will work.
- [ ] The developer has confirmed the Stripe platform has enough **available** test balance for Scenario 9 commission payouts. Pending balance from recent card payments does not count until Stripe marks it available.

---

## Test Credit Card Numbers

During testing you will be redirected to a Stripe payment page. **No real credit card is used.** Enter the following fake card numbers exactly as shown:

| Purpose | Card Number | Expiry | CVC | ZIP |
|---|---|---|---|---|
| Successful payment | `4242 4242 4242 4242` | Any future date (e.g., `12/30`) | Any 3 digits (e.g., `123`) | Any 5 digits (e.g., `10001`) |
| Payment that gets declined | `4000 0000 0000 0002` | Any future date | Any 3 digits | Any 5 digits |

You will use the **successful card** for most tests. The **declined card** is used only in the "failed payment" scenario.

---

## How to Report a Bug

If something does not match what is described under **What You Should See**, write it down with:

1. **Which scenario** you were running (e.g., Scenario 3).
2. **Which step** you were on (e.g., Step 4).
3. **What you expected** to see.
4. **What actually happened** (copy any error message word-for-word).
5. A **screenshot** if possible.

---

## Scenarios

---

### Scenario 1 — Admin Turns On Payment Features for Agents

**Who is logged in:** Admin account

**What you are checking:** The admin can control which roles are allowed to create invoices, issue refunds, and trigger commission payouts. This scenario confirms those switches work.

**Steps:**

1. Log in as Admin.
2. Look at the **left sidebar**. Scroll down past Deals, Workflow, Payments, and Intelligence sections until you see a section labeled **Admin**.
3. Inside the Admin section click **Payment Access**. It has a credit card icon (💳). This takes you to `/admin/payment-access`.
   > **Note:** "Payment Access" is **not** inside the Settings page — it is a dedicated page accessible only from the Admin sidebar section.
4. You should see three role cards: **Agent**, **Elf (Transaction Coordinator)**, **Team Lead**.
5. Each card has three toggle switches: **Create & send invoices**, **Refund payments**, **Trigger commission payouts**.
6. Make sure the **Agent** card has the **Create & send invoices** toggle turned **ON** (green). If it is off, click it — it saves automatically.
7. You will see a small spinning indicator while it saves, then the toggle stays green.

**What You Should See:**
- The toggle moves to the green/on position and stays there (no Save button needed — it saves instantly).
- A small loading spinner appears briefly next to the toggle while the change is saved, then disappears.

**Pass:** Toggle is green and stays green after clicking.
**Fail:** Toggle bounces back to off, a red error message appears, or nothing happens when you click.

---

### Scenario 2 — Agent Creates a Draft Invoice

**Who is logged in:** Agent account

**What you are checking:** An agent can create an invoice linked to a real transaction using either of two entry points, and the form guides them naturally from deal → payer → line items rather than requiring them to know IDs or codes.

#### Entry Point A — From the Payments Page

1. Log in as Agent.
2. Go to **Payments** in the left-hand menu. (If you do not see "Payments," the admin may not have enabled it — revisit Scenario 1.)
3. Click **+ New Invoice** (top-right area of the Payments page).
4. The invoice form opens. Notice that the **first field is "Transaction"** — this is intentional. The form is designed around deals, not contacts.
5. In the **Transaction** field, start typing the property address (e.g., "123 Main") and select the correct deal from the typeahead dropdown.
6. Once a transaction is selected, the **Payer** field changes to show the people on that deal — the buyer, seller, and other parties. Click the person you want to bill.
   > **Note:** The payer list shows each person's name, their role on the deal (e.g., "Buyer," "Seller"), and their email. You do not need to search or type anything — just click.
7. Add at least one **Line Item**: Description = "TC Compliance Fee", Quantity = 1, Unit Price = $495.00.
8. Set a **Due Date** in the future.
9. Optionally, open the **Link to Tasks** section (a collapsible panel near the bottom of the form) and check the box next to the open task called something like "Collect TC fee" or "Compliance fee." This will auto-complete that task when the invoice is paid.
10. Click **Save Draft** (do NOT click "Send Now" yet — that is Scenario 3).

#### Entry Point B — From a Transaction Card (faster path)

1. Log in as Agent.
2. Go to the **Deals** or **Transactions** section.
3. Find the active transaction and click its card to expand it.
4. In the card's action bar at the bottom, look for a button labeled **💳 Invoice deal**.
5. Click **💳 Invoice deal**.

**What You Should See (Entry Point B):**
- The New Invoice form opens, but notice it already has the deal's address pre-filled in the Transaction field — you do not need to search for it.
- A highlighted banner at the top of the form reads something like **"Invoicing for: 123 Main St"** to confirm which deal you are working on.
- The Payer field immediately shows the deal's parties — just click the right person.
- Complete the Line Items, Due Date, and optional Task Link as in Entry Point A, then click **Save Draft**.

**What You Should See (both entry points, after saving):**
- You are taken to the invoice detail page or back to the invoice list.
- The new invoice appears with a gray **Draft** label.
- The invoice detail shows the **payer's name and email** (not an internal ID code) and the **property address** (not a transaction code).
- The total amount matches what you entered.

**Pass:** Invoice created with Draft status, payer name and property address are visible (not codes), correct amount shown.
**Fail:** Error on save, wrong amount, no Draft label, raw ID codes visible instead of names/addresses, or invoice does not appear in the list.

---

### Scenario 3 — Agent Sends the Invoice to the Client

**Who is logged in:** Agent account (continuing from Scenario 2)

**What you are checking:** Clicking "Send" delivers an email to the payer and changes the invoice status from Draft to Open.

**Steps:**

1. Still logged in as Agent, find the draft invoice you created in Scenario 2.
   - It should appear on the Payments page with a **Draft** label.
   - The list now shows a **Payer** column with the payer's name and a **Property** column with the deal address — not codes or IDs.
2. Click **Send** (or open the invoice and click "Send Invoice").
3. A confirmation popup may appear — click **Confirm** or **Send Now**.

**What You Should See:**
- The invoice label changes from gray **Draft** to blue **Open**.
- A brief success message such as "Invoice sent."
- The invoice detail page shows the **payer's full name** and **property address** as human-readable text.
- The payer's email inbox receives a message from Velvet Elves with:
  - The invoice details (line items, total, due date).
  - A **"Pay Now"** button.

**To check the email:** Check the test email inbox for the payer. The developer will tell you which inbox to use (it may be a test inbox tool like Mailtrap or a real email you have access to).

**Pass:** Invoice is now Open, payer name and address appear as text (not codes), email arrives with a Pay Now button.
**Fail:** Invoice stays as Draft, no email arrives, email arrives with no Pay Now button, or raw ID codes are visible on the invoice detail page.

---

### Scenario 4 — Client Pays the Invoice

**Who is logged in:** Client account (the payer) — OR open the email link in an incognito/private browser window.

**What you are checking:** The client can open the payment link, see which property the invoice is for, and successfully complete the payment.

**Steps:**

1. Open the email from Scenario 3 and click **Pay Now**.
   - This will open a Stripe-hosted payment page (you will see the Stripe logo and a secure padlock in the browser).
2. Alternatively, log in as the **Client** account and go to **Invoices** or **Payments** in the client navigation. Find the invoice and click **Pay Now**.
3. Before paying, notice that the invoice detail page shows a **property context banner** — a highlighted section near the top that reads something like "This invoice is for your transaction at 123 Main St." This helps the client confirm which deal the invoice is for.
4. On the Stripe page, enter the **successful test card**:
   - Card number: `4242 4242 4242 4242`
   - Expiry: `12/30`
   - CVC: `123`
   - ZIP: `10001`
5. Click **Pay** (the button will show the total amount, e.g., "Pay $495.00").
6. Wait a few seconds. You should be redirected back to the Velvet Elves site.

**What You Should See after payment:**
- The page shows a message like "Payment successful" or "Thank you for your payment."
- The **property context banner** is still visible on the invoice detail page, confirming which deal was paid.
- **Back in the Agent or Admin view:** The invoice label changes from blue **Open** to green **Paid**.
- The invoice detail page shows a payment record with today's date and the amount.

> **Note:** The update from "Open" to "Paid" may take up to 10 seconds while the system processes the payment. Refresh the page once if needed. If it takes more than 30 seconds, that is a bug.

**Pass:** Invoice shows Paid status, a payment record appears, client sees a success message, property context banner is visible on the client invoice page.
**Fail:** Invoice stays Open after 30 seconds, no payment record, client sees an error on the Stripe page, or no property context shown on the client invoice page.

---

### Scenario 5 — Automatic Task Completion After Payment

**Who is logged in:** Agent account (or Admin)

**What you are checking:** When the invoice is paid, any task that was linked in the invoice form's **"Link to Tasks"** section should be automatically marked as complete — without the agent having to do anything manually.

**Steps:**

1. Log in as Agent (or Admin).
2. Go to the transaction that the paid invoice is linked to.
3. Open the **Tasks** section of that transaction.
4. Find the task you linked to the invoice (e.g., "Collect TC fee" or "Compliance fee"). You linked this task using the **"Link to Tasks"** collapsible panel in the invoice form during Scenario 2, Step 9.

**What You Should See:**
- The task is marked **Complete**.
- The completion note or history shows it was completed by **"payment"** (the system did it automatically).

> **Reminder:** Task linking is done explicitly during invoice creation using the "Link to Tasks" section in the form — it is not a vague optional checkbox. If you did not link a task in Scenario 2, go back and create a new invoice with the task linked, pay it, and then check here.

**Pass:** Task is marked Complete with a payment-triggered reason.
**Fail:** Task is still open, or no record of automatic completion appears.

---

### Scenario 6 — Dashboard Updates with Collected Money

**Who is logged in:** Agent account

**What you are checking:** After a payment is collected, the agent's dashboard shows updated numbers under "Collected this month," and the outstanding invoices list shows human-readable payer and deal information.

**Steps:**

1. Log in as Agent.
2. Go to the **Dashboard** (Home or Agent Dashboard).
3. Look for a widget or tile labeled something like **"Payments"** or **"Collected This Month"**.
4. Note the dollar amount shown.

**What You Should See:**
- The widget shows a dollar amount that includes the payment you just collected in Scenario 4.
- There may also be a section showing **"Outstanding Invoices"** — any Open invoices should appear there. Each outstanding invoice row shows:
  - The **payer's name** (e.g., "John Smith")
  - The **transaction label** (e.g., "123 Main St — Listing")
  - How many days the invoice has been outstanding
  - The amount due
  > You should not see ID codes in this list — only human-readable names and addresses.
- Look for two distinct values: one labeled **"Expected"** (money you anticipate from open deals — not yet paid) and one labeled **"Collected"** (actual money received). They should be clearly different.

**Pass:** Dashboard widget reflects the paid amount; outstanding invoices show payer names and deal addresses (not codes); Expected and Collected figures are displayed separately.
**Fail:** Dashboard shows $0 or no payment widget appears, outstanding invoices show ID codes instead of names, or Expected and Collected look like the same number.

---

### Scenario 7 — Agent Issues a Partial Refund

**Who is logged in:** Agent account (only if Admin granted Agent the "Refund" permission) — or Team Lead / Admin account

**What you are checking:** A refund can be issued for part of a collected payment, and the system updates the records correctly.

**Steps:**

1. Log in with a role that has refund permission (check with the developer which role that is in the test environment).
2. Go to **Payments** and find the invoice you paid in Scenario 4.
3. Open the invoice detail page.
4. Find the **Refund** button (it may be on the payment record row, or at the top of the page).
5. Click **Refund**.
6. In the refund dialog:
   - Enter a **partial amount** — for example, if the invoice was $495.00, enter $100.00.
   - Optionally add a reason (e.g., "Overpayment adjustment").
7. Click **Confirm Refund**.

**What You Should See:**
- A success message confirming the refund was submitted.
- The payment record now shows a refund of $100.00.
- The invoice label changes from green **Paid** to something like **Partially Refunded** (it may still show as Paid — this is acceptable per system design; the important thing is the refund row is visible).
- The dashboard "Collected" figure may decrease by the refunded amount (this can take a few seconds to update).

**Pass:** Refund record appears, amount is correct, success message shown.
**Fail:** Error on submit, no refund record, or the refund amount is wrong.

---

### Scenario 8 — Preventing an Over-Refund

**Who is logged in:** Same account as Scenario 7

**What you are checking:** The system should refuse to refund more than the remaining balance.

**Steps:**

1. On the same invoice from Scenario 7 (which already has a $100 partial refund applied), try to issue another refund.
2. In the refund dialog, enter an amount that is more than the remaining balance.
   - For example: the invoice was $495.00, you already refunded $100.00, so the remaining balance is $395.00. Try entering $400.00.
3. Click **Confirm Refund**.

**What You Should See:**
- An error message saying something like "Refund amount exceeds the remaining balance" or "Cannot refund more than $395.00."
- The refund is **not** processed.

**Pass:** System shows an error and blocks the over-refund.
**Fail:** The refund goes through (this would be a serious bug — report it immediately).

---

### Scenario 9 — Admin Triggers a Commission Payout

**Who is logged in:** Admin account

**What you are checking:** An admin can send a commission payout to the brokerage's connected bank account through the system, using a deal search that works by address — not by pasting an internal code.

**Steps:**

1. Log in as Admin.
2. Look at the **left sidebar** under the **Payments** section. You should see two entries:
   - **Invoices & Payments** (the main list)
   - **Commission Payouts** (the payout page — only visible if your role has payout permission)
3. Click **Commission Payouts**. This takes you to `/payments/payouts`.
4. Click **+ New Payout** or **Trigger Payout**.
5. Fill in the payout form:
   - **Transaction:** Start typing the property address (e.g., "123 Main") in the search field. A dropdown will appear with matching deals — select the correct one. You do **not** need to paste or type any internal transaction ID.
   - **Amount:** Enter a small test amount, e.g., $50.00.
   - **Destination:** This should pre-fill with the brokerage's connected account.
6. Click **Submit** or **Trigger Payout**.

**What You Should See:**
- A success message.
- The payout appears in the Payouts list with a status of **In Transit** or **Pending**.
- After a brief moment (may be a few seconds), the status may update to **Paid**.
- The Admin dashboard's "Payments health" section should not show any errors.

> **Note:** In test mode, Stripe processes transfers quickly. If the status does not change within 30 seconds, that is fine — the developer can verify it in the Stripe Dashboard.
> **Balance note:** If the payout fails with "platform balance is insufficient," ask the developer to add Stripe test balance or wait for pending test payments to become available. Stripe transfers use available platform balance, not pending balance.

**Pass:** Payout record appears with an initial status; no error message; the Transaction field accepted a property address search (no ID pasting required).
**Fail:** Error on submit, no payout record appears, the admin's payout button is missing, or the Transaction field requires pasting a raw code.

---

### Scenario 10 — Admin Disables Invoicing for Agents

**Who is logged in:** Admin first, then Agent

**What you are checking:** When an admin turns off the "Create Invoice" permission for Agents, an agent can no longer create invoices from any entry point — including both the Payments page and the transaction card.

**Steps:**

1. Log in as **Admin**.
2. In the left sidebar, under the **Admin** section, click **Payment Access**.
3. On the Agent card, click the **Create & send invoices** toggle to turn it **OFF** (it will turn gray). It saves automatically.
4. **Log out** of the Admin account.
5. Log in as **Agent**.
6. Go to **Payments** (left sidebar, under the Payments section, click **Invoices & Payments**).
7. Look at the top-right area of the Payments page.
8. Also go to **Deals** or **Transactions**, expand a transaction card, and look at the card's action bar at the bottom.

**What You Should See:**
- The **+ New Invoice** button is **completely gone** from the Payments page — it is hidden for users who lack permission.
- The **💳 Invoice deal** button is also **completely gone** from all transaction cards — it is hidden for the same reason.
- The Agent can still **view** existing invoices and payment records; only creating new invoices is blocked.

**Pass:** Both the "+ New Invoice" button on the Payments page and the "💳 Invoice deal" button on transaction cards have disappeared; Agent can view but not create invoices.
**Fail:** Either button is still visible and the Agent can open the invoice creation form even though permission was revoked.

**Clean-up:** After this test, log back in as Admin, go to the **Admin** sidebar section → **Payment Access**, and turn the Agent **Create & send invoices** toggle back **ON** so subsequent scenarios work.

---

### Scenario 11 — Client Sees Only Their Own Invoices

**Who is logged in:** Client account

**What you are checking:** A client who logs in to the system can only see their own invoices — not invoices from other clients or other transactions. The invoice list also shows which property each invoice is for, so the client can tell at a glance which deal they are being billed for.

**Steps:**

1. Log in as the **Client** account (the payer from Scenario 4).
2. Go to the **Payments** or **Invoices** section in the client navigation (it may look different from the agent navigation — simpler, with fewer options).
3. Review the list of invoices shown.

**What You Should See:**
- The client sees the invoice from Scenario 4 (the one they paid).
- The invoice list shows a **Property** column that displays the deal's address (e.g., "123 Main St"). This helps the client immediately identify which deal the invoice is for, without needing to open each invoice to find out.
  > On a small phone screen the Property column may be hidden — it reappears on tablet and wider screens.
- The client does **not** see any invoices belonging to other clients.
- The invoice detail shows the line items, amount paid, and a "Paid" status.
- At the top of the invoice detail, a **property context banner** is visible — a highlighted section that reads something like "This invoice is for your transaction at 123 Main St."
- If the invoice is still Open, the client sees a **"Pay $X.XX Securely"** button.

**Pass:** Client sees only their own invoice(s); Property column shows the deal address; no invoices from other clients are visible.
**Fail:** Client sees invoices from other clients (this is a serious privacy bug — report it immediately), client sees none of their own invoices, or the Property column is missing entirely.

---

### Scenario 12 — Failed Payment (Declined Card)

**Who is logged in:** Client account (or use the invoice Pay link in incognito mode)

**What you are checking:** When a card is declined, the system handles it gracefully and the invoice does not get marked as Paid.

**Steps:**

1. Find an invoice that is in **Open** status (create a new one if needed by repeating Scenarios 2 and 3).
2. Open the payment link for that invoice.
3. On the Stripe payment page, enter the **declined card**:
   - Card number: `4000 0000 0000 0002`
   - Expiry: `12/30`
   - CVC: `123`
   - ZIP: `10001`
4. Click **Pay**.

**What You Should See:**
- Stripe shows an error message like "Your card was declined."
- You are **not** redirected back with a success message.
- **Back in the Agent view:** The invoice remains **Open** — it does not change to Paid.
- A failed payment record may appear under the invoice (showing status "Failed"), which is correct.

**Pass:** Card is declined on Stripe's page, invoice stays Open.
**Fail:** Invoice changes to Paid despite the declined card (serious bug), or no error message is shown.

---

### Scenario 13 — Paying the Same Invoice Twice Does Not Double-Charge

**Who is logged in:** Client account (or use the invoice Pay link)

**What you are checking:** If someone clicks "Pay Now" twice (e.g., double-clicks the button or opens the link twice in different tabs), they should not be charged twice.

**Steps:**

1. Find an invoice that is already **Paid** (the one from Scenario 4 is fine).
2. Try to access the Pay link again:
   - Either go to the client invoice page and look for a "Pay" button.
   - Or use the original email link again.

**What You Should See:**
- The invoice page shows it is already **Paid**.
- There is **no "Pay Now" button** available on a paid invoice.
- If the Pay link somehow still loads Stripe, completing a second payment should be blocked (the developer will verify this in the logs — you do not need to verify it yourself).

**Pass:** Paid invoice shows no Pay button; no way to pay again from the UI.
**Fail:** A "Pay Now" button is visible on a paid invoice.

---

### Scenario 14 — FSBO Client Sees Their Invoices

**Who is logged in:** FSBO (For Sale By Owner) client account

**What you are checking:** A FSBO client has the same invoice visibility as a regular client — they can see their own invoices and pay them, but nothing from other deals. The Property column and context banner should also be present for FSBO clients.

**Steps:**

1. Log in as the **FSBO client** account (ask the developer to set this up if one does not exist).
2. Navigate to **Payments** or **Invoices** in the FSBO client view.
3. Confirm the list shows only invoices related to their property, and that the **Property** column shows the correct address.
4. If an Open invoice exists, verify the "Pay Securely" button is visible and the property context banner appears on the invoice detail page.

**What You Should See:**
- FSBO client sees only their own invoices.
- The Property column and property context banner work the same as for a regular client.
- The pay flow works the same as Scenario 4 if they choose to pay.

**Pass:** FSBO client has the same correct, isolated view as a regular client; Property column and context banner are present.
**Fail:** FSBO sees other clients' invoices, the pay button is missing, or the Property column/banner is absent.

---

### Scenario 15 — Team Lead Sees Their Whole Team's Payments

**Who is logged in:** Team Lead account

**What you are checking:** A Team Lead's dashboard and Payments view show all invoices and payments created by any agent on their team — not just their own.

**Steps:**

1. Log in as **Team Lead**.
2. Go to the **Dashboard**.
3. Look for the payment widget — it may be labeled "Team Collected This Month" or show team-scoped numbers.
4. Go to **Payments** and review the invoice list.

**What You Should See:**
- The dashboard widget shows the combined payment activity for the team (all agents under the Team Lead).
- The outstanding invoices section of the widget shows each invoice's payer name and transaction label — not codes.
- The Payments page lists invoices from all team members, not just the Team Lead's own invoices.
- A **"Commission Payouts This Period"** metric or widget may also appear.

**Pass:** Team Lead sees team-wide data in both the dashboard and Payments list; payer names and deal addresses shown, not codes.
**Fail:** Team Lead sees only their own invoices (same as a regular agent view).

---

### Scenario 16 — Admin Payment Health Panel

**Who is logged in:** Admin account

**What you are checking:** The Admin dashboard shows a "Payments health" section that flags any problems — past-due invoices, failed charges, and any background processing issues.

**Steps:**

1. Log in as **Admin**.
2. Go to the **Admin Dashboard**.
3. Look for a "Payments Health" or "Payment Status" panel (it may be in the lower section of the dashboard).

**What You Should See after running through all prior scenarios:**
- A count of **past-due invoices** (invoices past their due date that have not been paid).
- A count of **failed charges in the last 30 days** (from Scenario 12, this should show at least 1).
- A count of **refunds in the last 30 days** (from Scenarios 7–8).
- Ideally **no "stuck" background jobs** (a stuck job would mean a payment was collected but the system did not finish updating its records — this should be 0 or empty).

**Pass:** Panel is visible and the numbers match what actually happened during testing (e.g., at least one failed charge is reflected).
**Fail:** Panel is missing, all counts show 0 when they should not, or counts are clearly wrong.

---

## Quick Checklist Summary

Use this to track your progress:

| # | Scenario | Pass / Fail / Skip | Notes |
|---|---|---|---|
| 1 | Admin turns on payment features | | |
| 2A | Agent creates a draft invoice — from Payments page | | |
| 2B | Agent creates a draft invoice — from "💳 Invoice deal" on transaction card | | |
| 3 | Agent sends the invoice (payer name & address visible, no codes) | | |
| 4 | Client pays — property context banner visible on invoice page | | |
| 5 | Task auto-completes after payment (task was linked via "Link to Tasks" section) | | |
| 6 | Dashboard updates — outstanding invoices show payer name & deal label | | |
| 7 | Agent issues a partial refund | | |
| 8 | System blocks an over-refund | | |
| 9 | Admin triggers commission payout (Transaction field uses address search) | | |
| 10 | Admin disables agent invoicing — both "+ New Invoice" and "💳 Invoice deal" disappear | | |
| 11 | Client sees only their own invoices — Property column visible | | |
| 12 | Failed payment — card declined | | |
| 13 | Paying twice does not double-charge | | |
| 14 | FSBO client sees their invoices — Property column & banner visible | | |
| 15 | Team Lead sees team-wide payments | | |
| 16 | Admin payment health panel | | |

---

## Glossary

| Term | What it means in plain English |
|---|---|
| **Invoice** | A bill you send to a client or seller for a fee (e.g., TC fee, compliance fee). |
| **Draft** | An invoice that has been created but not yet sent to anyone. |
| **Open** | An invoice that has been sent and is waiting to be paid. |
| **Paid** | An invoice that has been fully paid. |
| **Past Due** | An invoice that was not paid by its due date. |
| **Refund** | Returning money to the payer, either partially or in full. |
| **Commission Payout** | Sending the brokerage's share of a commission to their bank account. |
| **Stripe** | The payment company that securely handles card transactions. You never type a real card number into the Velvet Elves app — Stripe handles that on their own secure page. |
| **Test mode** | Stripe's practice environment. No real money moves. The fake card numbers in this guide only work in test mode. |
| **Connected Account** | The brokerage's bank account that is linked to Stripe so commission payouts can be sent there. |
| **FSBO** | For Sale By Owner — a client who is selling their property without a traditional listing agent. |
| **TC** | Transaction Coordinator — the team member who manages the paperwork and timeline for a real estate deal. |
| **Task auto-completion** | When the system automatically marks a to-do item as done because a related payment was received — no manual action needed. |
| **Payment Access** | The admin-controlled on/off switches that decide which roles (Agent, TC, Team Lead) can create invoices, issue refunds, or trigger payouts. |
| **Deal Parties** | The people attached to a transaction — buyer, seller, TC, and so on. When creating an invoice, the payer list is drawn from the deal's parties rather than requiring a global contact search. |
| **"💳 Invoice deal" button** | A shortcut button on each transaction card that opens the New Invoice form with the deal already pre-filled. Only visible when the logged-in user has invoice creation permission. |
| **Link to Tasks** | A collapsible section in the invoice creation form where you can check which open tasks on the deal should be automatically marked complete when the invoice is paid. |
| **Property context banner** | A highlighted notice shown on invoice pages (both agent-side and client-side) that states which property address the invoice is for, so neither party needs to memorize an invoice ID to identify the deal. |

---

_End of testing guide._
