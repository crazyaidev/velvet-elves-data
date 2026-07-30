# Billing System and Minimum Price per Credit

**Prepared for:** Jake
**Prepared by:** Jan Froben
**Date:** 2026-07-29
**Status:** Awaiting your approval
**Decision needed:** Confirm the price per credit before launch

---

## Before you read further

This document does two things:

1. Explains exactly how the billing system we have already built works, in plain language.
2. Shows what it costs us to run the platform and to process one transaction, and what the lowest safe price is.

**The short version:** the billing system is built and working. It charges a flat fee per transaction, the first one is free, and there is an optional bulk discount. Nothing needs to be rebuilt. The only open item is the number.

**My recommendation is $29 per transaction. The lowest figure I would be comfortable with is $25.** Section 3 shows exactly how I arrived at those, and Section 5 lists what I need you to approve.

Every cost figure in this document is measured from our own accounts and our own usage records. Section 2 shows the full working, line by line, so you can check any number rather than take it on trust.

---

## 1. How the billing system works today

### 1.1 The basic idea

Think of it like a book of tickets. A customer buys tickets in advance, and each new transaction they create uses up one ticket.

Internally we call a ticket a **credit**. The rule is simple and fixed:

**1 credit = 1 transaction = the flat fee.**

Customers never see the word "credit" in a pricing sense and never have to work out an exchange rate. They see a single dollar figure: "$X per transaction". The credit is just the accounting mechanism behind the scenes that lets someone pay in advance and lets us handle refunds cleanly.

### 1.2 What a customer experiences

1. A brokerage signs up. Their account is created with a wallet holding **1 free credit**.
2. They upload their first contract and create their first transaction. That uses the free credit. **Their first deal costs them nothing.**
3. When they go to create their second transaction, the system sees an empty wallet and stops them with a payment prompt.
4. They pay through a standard Stripe checkout page. They can buy a single transaction, or take the bulk bundle.
5. Payment confirms, credits land in their wallet, and they continue exactly where they left off. If they were partway through the upload wizard, they are returned to the wizard and the transaction is created automatically.

That last point matters for conversion. Paying does not kick them out of what they were doing.

### 1.3 What we currently charge

These are the settings live in the system right now, visible on the platform admin billing page:

| Setting | Current value | What it means |
| --- | --- | --- |
| Fee per transaction | **$50.00** | The flat price of one credit |
| Free transactions | **1 per brokerage** | The first deal is free, once per account |
| Credits used per transaction | 1 | One deal consumes one credit |
| Bulk bundle | **Buy 10, get 12** | Pay for 10, receive 12 credits |
| Bundle availability | Sign-ups between 2026-01-01 and 2027-01-01 | A launch-period offer, not permanent |
| Refund window | 24 hours | See below |
| Charge for team members | **None** | Extra users are free |
| Commission payouts | Turned off | Built but parked, per your earlier decision |

### 1.4 Things worth knowing

**Team members are free.** We do not charge per seat. A brokerage with 2 agents and one with 20 pay exactly the same, because they pay per deal. This is a deliberate match to how the competition prices, and it removes a common objection from team leads.

**Refunds are automatic within 24 hours.** If a transaction is deleted within a day of being created, the credit goes back to the wallet automatically. This protects a customer who uploads the wrong contract, and it means we do not field support requests over honest mistakes.

**Credits do not expire.** Once bought, they sit in the wallet indefinitely.

**Every charge is recorded permanently.** There is a full ledger showing every free grant, purchase, spend, and refund, with a running balance. Nothing is ever silently adjusted, and the same charge can never be applied twice even if a payment notification arrives more than once. This matters for disputes.

**The bundle is a real discount, not a marketing line.** Buying 10 and receiving 12 means the customer pays for 12 transactions at 83.3 cents on the dollar. At a $30 list price the bundle buyer effectively pays $25 per deal. Section 3 factors this in, because if most customers take the bundle, that is our real revenue per deal.

### 1.5 What changing the price involves

**One number.** The fee lives in a settings field, not in code and not in the pricing catalogue at Stripe. Changing it takes a minute and requires no deployment, no migration, and no downtime.

Past purchases are unaffected. Each purchase records the amount that was actually paid, so if someone bought a bundle at one price, a later price change never reaches back and re-prices it.

---

## 2. Baseline cost calculation

### 2.1 Our costs come in two kinds, and they behave very differently

This distinction drives the entire pricing decision, so it is worth being precise about it.

| | **Variable cost** | **Fixed cost** |
| --- | --- | --- |
| What it is | Cost incurred only when a deal is processed | Cost that arrives whether we process 1 deal or 1,000 |
| Examples | Reading the contract, AI extraction, AI email drafts | Servers, database, email service, e-signature, domains |
| Our figure | **$2.50 per transaction** | **$341 per month** |
| Effect on price | Sets the absolute floor below which each sale loses money | Sets how many sales we need to be profitable |

**Nothing is counted in both columns.** Document reading is our largest single running expense, and because it happens per deal, it sits entirely in the variable column and is deliberately excluded from the monthly fixed figure. Section 2.3 flags this again where it matters.

### 2.2 Variable cost: what one transaction costs us

Every transaction costs us money in two places: reading the documents, and thinking about them.

| Cost component | What it is | Cost |
| --- | --- | --- |
| Document reading, intake | Amazon's document service reads the contract packet page by page, including checkboxes and signatures | $1.00 |
| Document reading, later docs | Inspection reports, appraisals, addenda added during the deal | $0.43 |
| AI extraction | Pulling the dates, parties, prices and terms out of the contract | $0.14 |
| AI during the deal | Email drafts, task suggestions, chat answers, daily briefings across 30 to 60 days | $0.59 |
| **Total per transaction** | | **$2.16** |

**I use $2.50 as the planning figure** to leave headroom, and I have tested every conclusion in this document against a worst case of $4.00. Neither figure changes any recommendation.

**How this was measured.** I used the real Honey Creek packet from our test files as the benchmark, because it is an actual deal rather than an invented one: 10 documents, 23 pages. I then checked it against every document the platform has processed to date, which average 2.39 pages each. The benchmark is therefore representative rather than flattering.

The per-page and per-word rates are taken from our actual bills, not from list prices, so the $1.43 of document reading reflects what we are really charged.

**The headline is that paperwork costs more than AI.** Reading documents is about two thirds of the total. The AI itself is under a dollar per deal. This is the opposite of what most people assume about an AI product, and it is the reason our price is not really driven by our costs at all.

### 2.3 Fixed cost: what the platform costs per month

This is what arrives every month regardless of sales. Every line below is measured from our own July bill.

**Hosting and infrastructure**

| What it is | Plain description | Monthly |
| --- | --- | --- |
| Application containers | The 3 containers running the platform: 2 for production, 1 for staging | $52.91 |
| Legacy servers | 2 older servers from the previous architecture, now running at about 1% capacity | $80.12 |
| Load balancers | Direct incoming traffic to the application, one per environment | $32.30 |
| Network gateway | Lets the platform reach outside services such as the database, Stripe and email | $34.22 |
| Public network addresses | 7 addresses across the load balancers, gateway and servers | $25.23 |
| Disk storage and backups | Server disks plus stored snapshots | $15.64 |
| Password storage, DNS, data transfer | Small supporting services | $1.87 |
| **Hosting subtotal** | | **$242.29** |

**Third-party services**

| Service | What we use it for | Monthly |
| --- | --- | --- |
| Supabase | The database holding all transaction and customer data | $25.00 |
| SendGrid | Sending every automated email the platform produces | $19.95 |
| DocuSign | Electronic signature | $45.00 |
| Google Cloud and domains | Inbound email monitoring, plus domain registration | $9.00 |
| **Services subtotal** | | **$98.95** |

**Total fixed cost: $341 per month.**

**Note on document reading.** Our document reading service also bills us about $55 a month at present. That figure is **not** included in the $341 above, because it is a per-deal cost already captured in Section 2.2. Including it in both places would overstate our costs and push the recommended price up for no reason. Almost all of that $55 is currently our own testing rather than customer work.

### 2.4 Payment processing

Stripe charges **2.9% plus 30 cents** on each payment. This is charged per *payment*, not per transaction, which matters for the bundle: a customer buying 10 credits at once generates one Stripe fee, not ten. Section 3 accounts for this.

### 2.5 Savings already identified

I have audited the hosting bill in detail and found roughly **$138 a month** of the $242 that we do not need to be spending:

| Action | Monthly saving |
| --- | --- |
| Retire the 2 legacy servers (about 1% capacity, superseded by the current architecture) | $80.12 |
| Delete their disks and 4-year-old backups | $14.63 |
| Release 2 network addresses that go with them | $7.30 |
| Run staging on discounted capacity, which is appropriate for a test environment | $12.35 |
| Combine the 2 load balancers into 1 with routing rules | $23.45 |
| **Total** | **$137.85** |

That would bring hosting from $242 to about **$104**, and total fixed cost from **$341 to about $203 per month**.

None of this touches production capacity or reliability. It is written up in full in a separate document, `AWS_COST_ATTRIBUTION_AND_REDUCTION_PLAN_2026-07-29.md`, which is the technical companion to this one.

As Section 3 shows, this work is worth $14 per transaction of pricing freedom, which makes it the single most valuable thing we can do before setting a price.

---

## 3. The minimum price, calculated three ways

You asked for the lowest price we can charge without making a loss. That has three different answers depending on what kind of loss you mean, so I have worked out all three.

### 3.1 Floor 1: never lose money on an individual transaction

This is the hard floor. Below it, every single sale costs us money no matter how many we make.

We need the fee to cover the $2.50 of running costs plus Stripe's cut:

*Fee, minus $2.50, minus (2.9% of the fee plus 30 cents), must be above zero.*

That gives **$2.88**. However, a bundle customer only pays for 10 of their 12 transactions, so the true floor is a little higher:

**$3.12 per transaction is the absolute floor.**

We are obviously not going to price near this. I include it because it establishes something important: **at any realistic price we keep about 90 cents of every dollar as gross profit.** Our running costs do not meaningfully constrain our pricing. What constrains it is the monthly fixed cost, which is what the next two floors address.

### 3.2 Floor 2: cover the monthly fixed cost (break-even)

Here volume enters. The fewer transactions we sell, the more each one has to carry.

Minimum fee to break even, assuming the worst case where every customer takes the bundle discount:

| Transactions per month | At $341 fixed | At $203 fixed (after the savings in 2.5) |
| --- | --- | --- |
| 10 | $45.78 | $28.72 |
| 15 | $31.73 | **$20.36** |
| 20 | $24.71 | $16.18 |
| 30 | $17.68 | $12.00 |
| 50 | $12.06 | $8.65 |

### 3.3 Floor 3: stay profitable in a slow month

Breaking even in an average month is not a stable business, because a quiet month then puts us in the red. So the figure that actually answers your question is: what is the lowest price that still turns a profit in a **slow** month of 12 transactions?

| Scenario | Minimum price |
| --- | --- |
| At $341 fixed, before the savings | **$38.75** |
| At $203 fixed, after the savings | **$24.54** |

### The answer: $25 per credit, once we complete the hosting cleanup

Before that cleanup, the same standard requires **$39**. That comparison is the strongest reason to do the infrastructure work first: it is worth $14 per transaction in pricing freedom.

### 3.4 What $25 delivers

Monthly profit at $25, worst case where every customer buys the bundle, at $203 fixed:

| Transactions per month | 12 | 15 | 20 | 25 | 30 |
| --- | --- | --- | --- | --- | --- |
| Monthly profit | $4 | $56 | $143 | $229 | $316 |

It never goes negative in any plausible month. By contrast, at $20 we would still be $44 down at 12 transactions and would only break even at 15. That is why $20 is a break-even price rather than a safe one.

### 3.5 Two things that quietly raise the floor

**The bundle is the binding constraint.** Because 10-for-12 is a 16.7% discount, the worst case for us is that everybody takes it. Every figure above assumes they do. At a $25 list price, after the bundle discount, Stripe's cut, the $2.50 running cost, and the free first deal, **$17.29 of that $25 reaches the bottom line.** Roughly 31% of the list price is consumed before it becomes profit.

**The free first deal has a real cost.** Every new brokerage consumes about $2.50 of document processing before paying us anything. I am not suggesting we remove it, since it is our strongest answer to the competition, but it is not free to us and it is included in the figures above.

---

## 4. My recommendation

### Launch at $29 per transaction, first transaction free, with the buy-10-get-12 bundle

The reasoning, in order of importance:

**1. It is safely above the floor.** $25 is the minimum for stability. $29 gives a $4 cushion, plus room to discount in a negotiation without going underwater.

**2. It is priced against the one public benchmark we have.** ListedKit publishes $14.99 per transaction, first free, no monthly fee, unlimited team members. They are the only competitor with a public price, so buyers will compare us to them whether we like it or not.

**3. Roughly 2x their price is defensible. Our current $50 is harder to defend.** We do considerably more than ListedKit: the full task engine, vendor communication, client portal, electronic signature, invoicing and payments, analytics, role dashboards. At about double their price we read as a serious upgrade. At $50 we are 3.3x their price, and a buyer has to justify that gap before they have seen what we do. We do not yet have a pricing page, testimonials, or case studies to help them justify it.

**4. It is easy to raise later, and painful to cut.** Raising a price once we have proof points is a normal move. Cutting from $50 after launch signals the first price was wrong.

**5. The bundle stays meaningful.** At $29, ten credits cost $290 and deliver twelve transactions, an effective $24.17 each. A visible discount that still sits above ListedKit's list price.

### On keeping $50

$50 is not unprofitable. It carries the best margin of any option and breaks even at only 8 transactions a month. My concern is purely whether buyers arrive at $50 in the first place.

If you would like to keep it, my suggestion is to keep it as the **team and brokerage tier** rather than the entry price:

| Package | Who it is for | Price |
| --- | --- | --- |
| Transaction AI | Solo agents and transaction coordinators | **$29 per transaction**, first free |
| Team Operating System | Small teams and TC companies | $50 per transaction, or a monthly base |
| Brokerage / white label | Brokerages and platform buyers | Negotiated |

This is the packaging already sketched in our competitive analysis. It lets us compete on price at the entry point without giving away the higher figure where it is justified.

---

## 5. What I need from you

Please confirm the following so I can set the value and close this out.

1. **The price per credit.** My recommendation is **$29**. The floor is $25 and I would not go below it. $20 is viable only if we complete the hosting cleanup and are confident of 20 or more transactions a month from launch.
2. **Keep the first transaction free?** My recommendation is yes. It costs us about $2.50 per new brokerage and directly matches the competition's strongest hook.
3. **Keep the buy-10-get-12 bundle, and for how long?** It currently applies to sign-ups between 2026-01-01 and 2027-01-01. My recommendation is to keep it as a launch-period offer and review it at the end of the window.
4. **A single price now, or the three tiers in Section 4?** My recommendation is a single price at launch for simplicity, with tiers introduced once we have customers to segment.
5. **Approval to proceed with the hosting cleanup in Section 2.5.** This is worth about $138 a month and is what makes a $25 price safe. It needs a decision on the two legacy servers, which I believe are obsolete but cannot confirm from the outside without checking what still points at them.

Once you confirm item 1, the change takes a minute and no deployment.

---

## 6. Assumptions and things to be aware of

I would rather flag these than have them surface later.

- **These are infrastructure and service costs only.** No salary, support time, or engineering cost is included. A full profit-and-loss break-even is higher than the figures here.
- **The $2.50 per-transaction cost is calculated from usage records rather than read off a single report.** Our internal cost dashboard cannot yet report a per-deal figure because of a measurement bug I have documented and can fix quickly. I rebuilt the number from the underlying usage data and cross-checked it two ways, and both landed in the same place. Fixing the dashboard would let you verify this in the product rather than in a document.
- **We have almost no real sales data yet.** Lifetime revenue is $14 across 26 test transactions. Every monthly volume figure in this document is a scenario, not a forecast. The per-transaction cost figures are solid, because they are rates. The volume figures are not.
- **Stripe's fees are assumed at the standard 2.9% plus 30 cents.** If we have negotiated rates, the floors drop slightly.
- **The four third-party service costs in Section 2.3** (Supabase, SendGrid, DocuSign, Google Cloud and domains) are current list prices rather than our own invoices, which I do not have access to. They are $99 of the $341 total. If our real invoices differ, tell me and I will update the figures.

---

## 7. Summary in one table

| Question | Answer |
| --- | --- |
| What does one transaction cost us to run? | $2.50 |
| What does the platform cost per month regardless of sales? | $341 |
| What could that be reduced to? | About $203 |
| Absolute floor, below which every sale loses money | $3.12 |
| Minimum for a stable profit, after the cleanup | **$25** |
| Minimum for a stable profit, before the cleanup | $39 |
| What the competition charges | $14.99 |
| What we charge today | $50 |
| **What I recommend** | **$29** |
