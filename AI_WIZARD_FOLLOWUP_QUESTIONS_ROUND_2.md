# AI Wizard - Round 2: My Responses and Remaining Questions

**Prepared by:** Jan (sole developer)
**Date:** July 25, 2026
**Subject:** What I built from your replies, and the few questions still open

You answered all six of my questions. What was clear I built and verified in the browser. A few pieces depend on a real-estate choice I should not guess, so I built everything up to that choice and kept the question. Those are marked **QUESTION** and listed at the end. "Built" means it is in the product now; "waiting on you" means it is designed but held for your answer.

One larger item, Team Leads and Brokerage Owners connecting agents and assigning them transactions, is a feature in its own right. I have logged it separately, not as part of this round.

---

## Question 1 - "Collect this information" button: which roles get it?

**Audri's answer.** The co-agent is mandatory, no button. The account holder's own details should come from their profile, and if the profile is empty the wizard should collect them and save them back. Agents, FSBO users and attorneys enter their own deals; TCs, Team Leads and Brokerage Owners can enter deals for others, and a TC fills in both agents with no button on either.

**Built.**

- The button shows on vendor roles only. The buyer, the seller, and both agents always require an email and phone. (This already matched your intent.)
- Your own agent card is prefilled from your profile and marked "From your profile". Only empty fields are filled, so anything the contract states wins.
- If your profile is missing a phone or brokerage, the card asks for them once and saves them back for next time. Name and email already come from your account.
- Prefill and save-back happen only on your own deals, and save-back never overwrites a field you already had.
- FSBO and dual deals have no separate co-agent, so the wizard does not ask for one.

**On filing for someone else.** When a TC, Team Lead or Owner files for another agent, both agent cards are typed and none of the uploader's own details are stamped on the deal. Automatically pulling the assigned agent's details from *their* profile is the connect-and-assign feature I logged separately; until it lands, that agent is typed by hand, which never blocks anything.

**No question here.**

---

## Question 2 - Expiration dates: never shown, or renamed?

**Audri's answer.** Suppress all expiration dates, except pre-approval and financing letters, which are worth calling out for compliance. Also, the AI's findings need to be clearer.

**Built.**

- All offer, counter-offer and acceptance expirations are suppressed. Verified: a purchase agreement with four counter offers showed no expiration box.
- The clearer findings are Question 6, and that is done.

**Waiting on you.** The pre-approval and financing expiration is suppressed too, for now. To surface it as a compliance note it needs its own small card, because our current surfaces are calendar deadlines and waivable checklist items, and neither fits a date that has already passed. It also depends on whether it should create a task, which is QUESTION 1. So I am holding it rather than putting it in the wrong place.

**QUESTION 1.** When a pre-approval letter is expired or expiring, should the system also create a task to request an updated one, addressed to the loan officer? Or is a compliance flag with the date enough, and the agent decides whether to chase it?

---

## Question 3 - Seller / dual-representation fees

**Audri's answer.** The two-card layout is good. Do not assume anyone pays, ask who pays what, so the title company can build the seller settlement statement. Dual deals apply too. And when representing the buyer, the buyer may pay part of their own agent's fee on top of what the seller pays.

**Built.**

- Two cards on seller and dual deals: the listing fee (seller-paid by the listing agreement, so no payer toggle), and the buyer agent fee, followed by "Is the seller paying any part of the buyer agent's fee?" It starts unanswered, so we never save a silent "no", and asks how much only when the answer is Yes.
- On a buyer-rep deal, the professional-fee card asks who pays it: Buyer, Seller, or Both. When it is Both, each side's amount is entered separately. That is the case you raised.
- Every amount is a percentage or a flat dollar figure, chosen per side.
- Fees are optional and never block an upload. What is entered is saved on the deal and shown on Verification and in the workspace.

**Waiting on you.** The title-company script is exactly what QUESTION 4 decides, so the fee data is captured but nothing about who-pays-what is written into an outbound email yet.

**One thing to flag.** On a seller or dual deal, once the seller pays part of the buyer agent's fee, the summary reads, for example, "2.5% · Paid by Seller 2%, rest Paid by Buyer". That "rest" is the one place the tool infers a remainder instead of asking, which is what QUESTION 2 checks.

**QUESTION 2.** Is entering each side's share the right shape, or is the buyer-agent fee more often written as "the seller pays up to X, and the buyer pays anything above that"? If that is the common form I would rather build it directly than have people compute a remainder.

**QUESTION 3.** Should I ask who pays the listing fee, or is seller-paid safe to assume? It is seller-paid in every deal I have seen, which is why the listing card has no payer toggle today, but you said not to assume, so I want to check.

**QUESTION 4.** For the title company email, should the split be stated as entered ("seller pays 2 percent"), or converted into dollars against the purchase price? Dollars are more directly usable, but it means calculating a figure on the title company's behalf, so I want your call. This is the piece the email copy is held on.

---

## Question 4 - "Paid by Buyer / Paid by Seller" wording

**Audri's answer.** You asked what the difference was between my two options, since both showed a buyer and a seller line.

**My answer.** That was a badly written example. There was only one question. The first line was a single fee paid by one side (I showed a seller and a buyer version of the same case, which looked like two). The second was the real other case, a fee split so both sides pay part.

**Built.** Since Question 3 asks each side explicitly, the summary now spells the payer out. The exact strings on screen:

- One side pays it all: "3% · Paid by Seller" or "$495 · Paid by Buyer".
- Both sides pay part: "Paid by Buyer $250 · Paid by Seller 2%".

**No question here.** Shout if you would word it differently now that you can see it.

---

## Question 5 - The collect-info task: naming and timing

**Audri's answer.** Name and description are correct. Make it due immediately. If there is an email but no phone, AI should ask for the phone and any extra contacts. If there is no contact at all, AI should ask the co-agent, since an unknown vendor is probably theirs. Use AI to remove manual work wherever possible.

**Built.**

- The name and description are unchanged: "Collect contact details for [Vendor]" and "Get the email and phone for [Vendor] ([company]), the [role] on this deal, and add them on the Contacts tab."
- It is now due immediately, on the upload day, not a couple of days after acceptance. It is addressed to nobody, so it can never auto-send by accident.

**Waiting on you.** The AI actively working the task, emailing the vendor for a phone, asking the co-agent when there is nothing, and filling in the reply, is not switched on yet. It depends on the deal's automation setting (send on its own, or wait as a draft) and on QUESTION 5. The task exists the moment you defer; the chasing turns on once those are settled.

**QUESTION 5.** Asking the co-agent makes sense for an unknown vendor. But a user can also add their own title company or inspector before they have the details. In that case, is asking the co-agent still right, or should it stay with the user to fill in?

---

## Question 6 - "Needs your eyes" wording

**Audri's answer.** The explanation style is right. Keep the page number and the in-document search. Add the name of the document the finding refers to, for example "Date Missing in Lead Based Paint Disclosure".

**Built.**

- Every finding that points at a document now names it beside the page link, as one clickable line, for example "Lead Based Paint Disclosure · page 5". The page number and the click-through into the document are unchanged; the name is added on top.
- I use the document type ("Lead Based Paint Disclosure") because it reads better than a file name, fall back to the file name when the type is uncertain, and to the plain page link when neither is known. It never invents a name.
- This covers every finding that carries a citation, not just compliance items. The one exception is the double-check panel, which compares two reads of the same value and points at no single document.
- The blank-title card in your screenshots was a real bug: waive suggestions read the wrong field. They now show what is being waived and why, and the document name is in.

**No question here.**

---

## The five questions, in one place

1. Should an expired or expiring pre-approval create a task for an updated letter, addressed to the loan officer, or is a compliance flag with the date enough? *(Gates how I surface the pre-approval expiry.)*
2. Is entering each side's share the right shape for the buyer-agent fee, or is it more often "the seller pays up to X and the buyer pays the excess"?
3. Should I ask who pays the listing fee, or is seller-paid safe to assume?
4. For the title company email, should the split be stated as entered, or converted into dollars? *(Gates the title-company email copy.)*
5. When the vendor with no details is one we added on our own side, is asking the co-agent still right, or should it stay with the user? *(Gates the AI chasing the collect-info task.)*

Everything else is built and verified. The three held items, the pre-approval compliance note, the title-company fee script, and the AI working the collect-info task, each wait on one of these questions.
