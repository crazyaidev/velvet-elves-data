
## Questions and Answers for PAYMENT AND BILLING SYSTEM:

7. A few decisions we need you to confirm
The collecting-from-clients side (Sections 2 to 4) is built and ready. The platform-charging side (Section 5) is built but waiting on you, because the right answer is a business decision, not an engineering one. As with the transaction guide, each item below gives what it is about, how it works today, what we suggest, and the call we need from you.

### Question 1 - Whether to start charging per deal at all
What this is about. The whole credit system in Section 5 is the planned way Velvet Elves earns from each brokerage. It is finished, but switched off.
How it works today. Billing is off platform-wide. Every brokerage uses the product without spending or buying anything, and no billing screens charge real money.
What we suggest. Keep it off until the prices below are settled, then turn it on first in test mode (practice cards, no real charges) so we can watch a full buy-and-spend cycle before a single real dollar moves.
Your call. Do you want to move toward per-deal billing on this credit model, and if so, roughly when?

#### Jake:
```
We feel like this should be per deal only because AI costs so many credits that we need to be profitable and if we charge a per deal basis some deals we’re going to lose on and other deals we’re going to win on but we can count on winning at least to some level when we understand the credit usage or token usage for AI on an average deal.
```

#### Jan:
```
Per deal is exactly what the system is built to do: there is one charge point (when a deal is created), so cost tracks deals, not seats or months. The number your answer hinges on, average AI cost per deal, is already measured: we record the token cost of every AI call and the platform admin screen totals it by deal and by office. Two cautions before locking a price: that data is mostly demo deals today, so we need a few weeks of real deals in test mode to trust the average; and cost is not flat, since a heavy deal with many counters and addenda costs more to parse than a clean one. I would price with margin above the average, so we win on the typical deal even when we give a little back on the occasional heavy one. 

Are you able to give us a price per deal for our test deals so far? In particular the one with 5 counter offers that we entered multiple times. 
```

### Question 2 - The price of a credit and the cost of a deal:
What this is about. Three numbers define the economics: how many credits a new deal costs, how much a credit is sold for (and in what pack sizes), and how many free starter credits a new brokerage receives.
How it works today. The system is set to the safe placeholders of one credit per deal and one free starter credit, with no real pack prices loaded. Earlier planning floated candidate figures (for example, a platform fee in the range of fifty dollars per transaction), but nothing is locked in.
What we suggest. Set a simple, round price per credit and two or three pack sizes with a small volume discount, keep a deal at one credit so the math stays obvious to the customer, and offer one free starter credit so a new office can try a real deal first.
Your call. What should a credit cost, in what pack sizes, how many credits should a deal cost, and how many free starter credits should a new brokerage get?

#### Jake: 
```
For now let’s just charge a flat fee and not worry about credits or discounts or anything of that sort until we have a good idea of AI impact token usage and user input.
```
#### Jan: 
```
Agreed, and this is a simplification, not a rebuild. The engine underneath is the same Stripe plumbing whether we call it a credit or a flat per-deal fee, so I will drop the packs, per-credit pricing, and volume discounts and show a single flat charge per deal, with the same safety (no double charges, every charge recorded). The only open number is the dollar amount, which depends on the AI-cost data from Question 1. Two confirmations when ready: whether a new office still gets its first deal free (it does today), and whether the fee is charged per deal at the start (Question 4) rather than pre-bought. I recommend charging at the start, so there is no balance for the customer to track. 
Let's give them their first deal for free on an account basis, not login basis. Meaning, if we sign a brokerage up, the brokerage gets 1 deal for free, not 60 deals if they have 60 agents.
We can offer volume discounts, but it would be something like buy 10 transactions get 2 free kinda thing, still at the determined flat fee per deal. Can we build it to when someone purchases 10 transactions their next 2 are free? (if so, we will need to build that into our pricing. This could also be just for accounts that sign up in 2026 and we don’t move this model forward after that)
```

### Question 3 - The shape of the charging model:
What this is about. Per-deal credits is one way to charge. The alternatives are a flat monthly subscription, a per-seat price, or a blend (for example, a base subscription plus credits for volume).
How it works today. Only the per-deal credit model is built. It bills by activity, so a quiet month costs the brokerage little.
What we suggest. Lead with per-deal credits because it lines up cost with value (an office pays as it does deals) and is the simplest thing for a customer to understand. We can layer a subscription on later if the market wants predictability.
Your call. Is per-deal credits the model you want to launch with, or should we plan for seats, a subscription, or a hybrid?

#### Jake: 
```
Let’s try out the “per deal” pricing model discussed above. If we find we aren’t making any money, then we can introduce a credit based model. Pricing will be interesting due to this being a completely new product.
```

### Question 4 - Commission payouts and connecting a bank:
What this is about. Section 3 can send a commission to a brokerage's account, but only once that brokerage's bank is connected to the platform through Stripe Connect.
How it works today. The payout feature works, but no brokerage bank is connected, so a real transfer cannot complete yet. Setting up Stripe Connect is an onboarding step for each brokerage.
What we suggest. Treat payouts as an opt-in feature for offices that actually want the platform to move commission, and build the short bank-connection step only when we have a brokerage that wants it.
Your call. Do your target brokerages want Velvet Elves to move commission for them, and are they willing to connect a bank account to do it?

#### Jake:
```
For this question specifically we’re only billing through Stripe and the billing starts when they begin the transaction not at the end. They can decide to charge their client a transaction fee of whatever they ‘d like and they can collect it on the settlement statement but as far as we are concerned we charge our flat fee plus or minus any monthly fees that we decide.
```

#### Jan:
```
Understood, and this simplifies the build. First, on commission: if we are not moving brokerages' commission and they collect any client fee themselves on the settlement statement, then the Commission Payouts feature and the Stripe bank-connection step are not needed for launch, and I will park them, which removes the only piece requiring a brokerage to connect a bank. Second, on timing: today the charge fires at the end of intake (Approve and Create), not the start. To match "billing starts when they begin the transaction," I will move it to the first save of a new deal (when the agent commits and we create the record), not the very first click, so we never charge for a deal opened by mistake and abandoned. Say if you prefer a different trigger. Finally, "plus or minus monthly fees" means a flat per-deal fee now with an optional monthly fee later; Stripe handles both. That also answers most of Question 3: flat per-deal now, optional monthly layer later. 
```

#### Jake:
```
Agreed!
```

### Question 5 - Refund rules:

What this is about. Two refund questions sit open: how generously we refund a credit purchase, and how long the window should be to auto-refund the credit when a brand-new deal is deleted.
How it works today. A platform admin can refund a credit purchase by hand, and a credit is automatically returned if its deal is deleted within twenty-four hours.
What we suggest. Keep the twenty-four-hour auto-refund on deletion as a fair "oops" window, and decide a plain rule for purchase refunds (for example, unused credits refundable within thirty days).
Your call. What window should the deletion refund use, and what is your policy for refunding bought-but-unused credits?

#### Jake:
```
Good with the suggestion.
```

#### Jan:
```
Good. The 24-hour auto-refund on deleting a brand-new deal is already live and the window is adjustable, so I will leave it at 24 hours. One note: if we charge a flat fee per deal at the start (Questions 2 and 4) instead of prepaid packs, there are no bought-but-unused credits to refund, so the only refund case is that same 24-hour window, already built, and the separate 30-day policy becomes unnecessary. If you keep prepaid packs as an option later, I would enforce the 30-day rule then. 
```

#### Jake:
```
See question 2 dialogue above.
```

### Question 6 - Default invoicing permissions and sales tax:

What this is about. Two smaller defaults: which roles can invoice and refund out of the box (Section 4), and how sales tax is handled on an invoice.
How it works today. Permissions start conservative and an administrator opens them up per role. Tax is entered as a single manual amount on each invoice.
What we suggest. Confirm a sensible starting point (for instance, agents and coordinators can invoice but not refund, team leads can do both), and keep tax manual for now unless your markets need automatic tax calculation.
Your call. What should the default payment permissions be for each role, and do you need automatic sales-tax calculation on invoices?

#### Jake:
```
Will be answered tomorrow - still working on this (26-JUN-2026)
```
