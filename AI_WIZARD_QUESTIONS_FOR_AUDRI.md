# AI Wizard — Questions & Answers for Audri

**Prepared:** July 23, 2026
**Subject:** Follow-ups from the July 22 testing round
**How to reply:** A "yes" is enough where the default is right; otherwise tell me what to change and I'll update it and re-verify in the browser.

---

## Overview

Thank you for the detailed testing notes. Everything you raised is implemented and verified in a real browser. The items below need your confirmation before we call them final. For each one I've written the **question**, a plain **example**, what I built as the **proposed answer (default)**, and the exact thing to **confirm**.

Two earlier questions are already answered and closed:

- **Parsing screen** — you confirmed: four fixed steps + spinner. Done.
- **Document scrolling** — you confirmed: turn the page at the edge. Done (delivered as smooth, continuous scrolling through all pages).

---

## Question 1 — "Create a task to collect this information": which roles get the button?

**Your note:** the button should appear on all roles **except** Buyer, Seller, and Co Agent.

**Proposed answer (default):** The button appears on **vendor contacts only** — Title Company, Lender / Loan Officer, Inspector, Appraiser, Closing Attorney. It is **hidden** on the Buyer, the Seller, the buyer's agent, and the listing agent. In other words, both principals and **both** agents always require an email and phone and can never be deferred.

**Why I want to confirm:** You named "Co Agent" (the other side's agent) but did not mention your **own** side's agent. My default hides the button on both agents, because a deal is worked **through** the agents, so their contact details should never be skippable.

**Example:** Representing the Buyer, you add the Title Company but don't have their email yet. The "Create a task to collect this information" button shows; you click it, and the deal is created with a task to chase the title rep's details. On the Buyer's Agent card (you or your teammate) the button does **not** show.

**Please confirm:**

- Is it correct that **both** agents (your side and the co-agent) are always required and never get the button? **or**
- Should your **own** side's agent also be allowed to defer (button shows)?

---

## Question 2 — Expiration dates: never shown at all, or renamed?

**Your note:** the "Counter offer expiration" box should say "Counter Offer 1 Expiration" — and also: "Regardless of document, it should never call out expiration dates. If a user is uploading the transaction the expiration dates are irrelevant."

**Proposed answer (default):** I read your stronger statement as the real intent, so the system now **never surfaces an expiration date at all**. Offer expiration, counter-offer expiration, "offer void if not accepted by", acceptance deadline, and pre-approval / financing pre-qualification letter expiration are all suppressed. The box never appears — instead of appearing with a better name.

**Why I want to confirm:** By the time a deal is uploaded, those dates have already passed, so they can never be a deadline anyone must act on. Suppressing them entirely felt more correct than renaming a box the user should never see — but your first sentence asked for a rename, so I want to be sure.

**Example:** You upload a purchase agreement plus four counter offers. In testing, **no** expiration box appeared at all, even though each counter offer had an expiration clause.

**Please confirm:**

- Suppress **all** expiration dates entirely (my default — the box never appears)? **or**
- Would you rather it still appear, just correctly named ("Counter Offer 1 Expiration")?
- Also: is it right to include the **pre-approval / financing pre-qual letter** expiration in the "never show" list, or is a pre-approval expiration something you'd actually want flagged?

---

## Question 3 — Seller / dual-representation fees: is the model right?

**Your new request:** when representing the Seller (or Buyer & Seller), ask for the listing professional fee **and** the buyer agent's professional fee, and ask whether the seller is paying any of the buyer agent's fee (and how much).

**Proposed answer (default):**

- **Buyer rep** — one "Professional fee" card (your fee), unchanged.
- **Seller rep** — two cards:
    - "Listing professional fee" (paid by the seller)
    - "Buyer agent professional fee", plus the question "Is the seller paying any of the buyer agent's fee?" (Yes / No) → if Yes: "How much is the seller paying?"
- **Buyer & Seller (dual)** — the same two-card layout; the buyer-agent fee is noted as "also you" since you hold both sides.

**The split assumption:** when the seller pays **part** of the buyer agent's fee, I assume the buyer pays the remainder. On the Verification screen it reads, for example: "Buyer agent professional fee: 2.5% — Paid by Seller 2%, rest Paid by Buyer".

**Please confirm:**

- Is the two-card seller / dual layout what you had in mind?
- Is "the seller pays X, the buyer pays the rest" the correct way to split the buyer agent's fee — or is there another arrangement you see in practice (e.g. the seller pays a flat dollar amount and anything above that is the buyer's)?
- On a Buyer & Seller (dual) deal, should we still ask "is the seller paying any of the buyer agent's fee?" — or is that question only meaningful when the two agents are different people?

---

## Question 4 — "Paid by Buyer / Paid by Seller" wording on split fees

**Your note:** use "Paid by Buyer" / "Paid by Seller" instead of "buyer" / "seller". Done. One wording choice to confirm for a fee split between both sides.

**Proposed answer (default):**

- Paid by one side: "3% — Paid by Seller" / "$495 — Paid by Buyer"
- Split between both: "Paid by Buyer $250 — Paid by Seller 2%"

**Please confirm:** is that split wording clear, or would you phrase the both-sides case differently?

---

## Question 5 — The collect-info task itself (naming and timing)

When you defer a vendor's contact info, a task is created at upload — a plain to-do on the deal.

**Proposed answer (default):**

- Task name: "Collect contact details for [Vendor Name]"
- Description: "Get the email and phone for [Vendor] ([company]) — the [role] on this deal — and add them on the People tab."
- It is a manual task (no auto-email, since there is no email yet), due a couple of days after contract acceptance, and it shows on the Verification summary before upload so you know it was created.

**Please confirm:**

- Is that task wording good, or would you word it differently?
- Is "a couple of days after acceptance" a fine default due date, or should these have no due date / different timing?

---

## Question 6 — "Needs your eyes" wording (feedback welcome, not blocking)

You said the boxes at the top were bold and prominent (good) but unclear on what was wrong or what to fix. I added a one-line explanation to each section plus a "Why you're seeing this:" line on every card, in plain English. For example:

- **Seller surrender possession time** — AI · 74%
- Deadline: not stated
- Why you're seeing this: AI found the obligation but no date or day count for it, so there is nothing to put on the calendar yet.
- Buttons: Add deadline / Dismiss

**Please confirm:** is this level of explanation clear enough now, or is there specific wording you'd like changed? (Not blocking — just want your read.)

---

## Summary of what's open

| # | Topic | Status |
| --- | --- | --- |
| 1 | Collect-info button — exact excluded roles | Needs confirm |
| 2 | Expiration dates — suppress vs. rename; pre-approval expiry | Needs confirm |
| 3 | Seller / dual fee model + split assumption | Needs confirm |
| 4 | "Paid by" wording on split fees | Quick confirm |
| 5 | Collect-info task wording / due date | Quick confirm |
| 6 | "Needs your eyes" wording | Feedback only |
