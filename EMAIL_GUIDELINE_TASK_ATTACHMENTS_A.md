

# **VELVET ELVES**

## *AI-First Transaction Management Platform*

# **EMAIL GUIDELINE & TASK ATTACHMENTS**

## **Questions for Jake**

# **Before you start**

Thank you for both documents. The email guideline is genuinely good and I can build against it almost as written. I have read it line by line and mapped every section against what the product actually does today.

I have two kinds of question for you.

The first kind is housekeeping: your attachment spreadsheet and the task list inside the system do not line up perfectly. Three task IDs in your sheet do not exist in the system, two have different names, and 32 tasks in the system are not in your sheet at all. You asked me to send back anything you missed, so that is Part 1 and Appendix A.

The second kind is a real product decision that I do not want to make on your behalf, because it changes what your clients see in their inbox. That is Part 2\.

**Nothing is stalled while you read this.** Roughly half the work does not depend on your answers and I have already started it. Appendix B says what that is.

# **At a glance**

| \# | Question | Blocking? | My recommendation |
| :---- | :---- | :---- | :---- |
| 1 | Task 235 does not exist. Which task did you mean? | Yes | Probably 240 or 245 |
| 2 | Tasks 453 and 455 do not exist. Add them? | Yes | Yes, add both |
| 3 | Tasks 460/470 are called "Request Referrals", not "Request Testimonials" | Yes | Rename to Testimonials |
| 4 | 32 tasks have no attachment rule (Appendix A) | Yes | Confirm my pre-filled list |
| 5 | Four tasks are phone calls in the system, but your sheet treats them as emails | Yes | Keep the call, add the email |
| 6 | Should auto-sent emails be signed "Aime" instead of the agent? | Yes | Yes, as your guideline says |
| 7 | Inspection tasks: your sheet says automate, the guideline says always review | Yes | Automate reminders only |
| 8 | Each task needs an exact "how to reply" instruction | No | Add a column to the sheet |
| 9 | Should writing-style preferences be per agent or per brokerage? | No | Per agent |

# **Part 1 — Your spreadsheet and the task list**

A quick note on how the system works, so the questions make sense. Every task in Velvet Elves has a permanent ID number, and that number is how the software finds the task. Names can be edited by a brokerage, but IDs never change. So when your sheet and the system disagree on an ID, the rule simply never gets applied to anything.

## **Question 1 — Task 235 "Buyer's Inspection Response Due"**

**What I found.** There is no task 235 in the system. The inspection tasks run 230, 240, 245, 250, 255, 257\. Nothing sits at 235\.

The closest matches are:

\- **230 — Inspection Completed.** Goes to the buyer. Currently: "Call the buyer to follow up to confirm that the inspection was completed as scheduled."

\- **240 and 245 — Inspection Response Reminder.** Both go to the agent. 240 is for the buyer side, 245 for the seller side. 245's text reads: "The deadline for the inspection response for this transaction is tomorrow."

**Why it matters.** Your sheet lists 235 with no attachments, which is easy, but I cannot attach "nothing" to a task that does not exist. If 235 is meant to be a new task I need to add it properly, with a due date rule and a recipient.

**What I suggest.** Given the name you used, I believe you meant 240 or 245\. Both already do exactly what "Buyer's Inspection Response Due" describes.

**Your answer:**

\- \[ \] I meant task 240

\- \[ \] I meant task 245

\- \[ \] I meant task 230

\- \[ \] 235 is a brand new task — details below

If it is new, I need: who receives it, what triggers its due date, and how many days before or after that trigger it should land.

## **Question 2 — Tasks 453 and 455 do not exist**

**What I found.** Your sheet lists two tasks that are not in the system at all:

\- **453 — Schedule Pick Up of Sign and Lockbox**

\- **455 — Change MLS Listing Status to Sold**

Both are sensible post-closing tasks and I suspect they simply have not been added yet. The numbers you chose sit neatly between 450 and 460, which suggests you intended them as new.

**Why it matters.** These are new tasks, not new attachment rules. Adding a task means deciding when it appears, who it goes to, and whether it applies to buyer-side deals, seller-side deals, or both.

**What I suggest.** Add both. My proposed settings, for you to correct:

|  | 453 Schedule Pick Up of Sign and Lockbox | 455 Change MLS Listing Status to Sold |
| :---- | :---- | :---- |
| Goes to | The agent (a reminder to themselves) | The agent (a reminder to themselves) |
| Applies to | Seller-side deals only | Seller-side deals only |
| Timing | Day of closing | Day of closing |
| Attachments | None | None |

**Your answer:**

\- \[ \] Add both with the settings above

\- \[ \] Add both, but change: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\- \[ \] Do not add them

## **Question 3 — "Request Testimonials" vs "Request Referrals"**

**What I found.** Tasks 460 and 470 are called **Request Referrals** in the system, not "Request Testimonials". Their instructions read: "Send an email to the buyer to request social media and online referrals."

Your sheet calls both of them Request Testimonials.

**Why it matters.** Testimonials and referrals are different asks. A testimonial is a review of the agent. A referral is an introduction to a new client. The email the agent sends is not the same message, so I need to know which one this task is actually for.

There is also a technical reason to settle it now. Right now the automation finds a task by its name, so renaming a task quietly breaks its automation. I am fixing that as part of this work so names become safe to edit, but I need the correct name before I write the email copy.

**What I suggest.** Given that "Testimonials" is what you wrote in a document about email content, I think that is the intent, and the current task text is stale. Rename to Request Testimonials and rewrite the email to ask for a review.

**Your answer:**

\- \[ \] Rename to "Request Testimonials" and write the email as a review request

\- \[ \] Keep "Request Referrals" and write the email as a referral request

\- \[ \] Split into two tasks, one for each

## **Question 4 — 32 tasks have no attachment rule**

**What I found.** Your sheet covers 28 real tasks. The system has 60\. That leaves 32 with no rule.

Some of these matter a great deal:

\- **Task 80, Confirm Title Order.** This one already sends automatically today, and it already

attaches documents. Its own instructions list Purchase Agreement, all Counters, BLC or Tax Sheet, and Sellers Disclosure. That is identical to task 70, which you did specify.

\- **Task 8, Review Documentation.** Also automated today. Its instructions say "Attach any unsigned

documents to the email."

\- **Tasks 110, 115, 120 — Deliver HOA Docs.** These deliver the HOA documents to the buyer. They

obviously need to attach them, and there is no rule saying so.

\- **Tasks 150, 155, 160 — Deliver Utility Info.** Same situation.

**Why it matters.** My rule is that a task with no attachment rule attaches nothing. That is the safe default, but for the delivery tasks above it is plainly wrong: an email that says "here are your HOA documents" with nothing attached is worse than no email.

**What I suggest.** I have pre-filled all 32 in **Appendix A**, using each task's own instructions wherever they already say what to attach. Most of them just need a tick.

**Your answer:** Please work through Appendix A. If you agree with everything, just reply "Appendix A approved" and I will proceed.

## **Question 5 — Four tasks are phone calls, not emails**

**What I found.** Four tasks in your sheet are written as phone calls in the system:

| Task | What the system says today | What your sheet implies |
| :---- | :---- | :---- |
| 260 — Appraisal Ordered | "Call the loan officer and ask if the appraisal has been ordered…" | Send an email with the purchase agreement attached |
| 270 — Appraisal Completed | "Call the loan officer and ask if the appraisal has been completed…" | Send an email |
| 330 — Clear to Close | "Call the loan officer to find out if the transaction has been cleared to close…" | Send an email |
| 340 — Closing Disclosure Delivered | "Call the loan officer to ensure the final closing disclosure has been delivered…" | Send an email |

Two more, tasks 130 and 140, are already hybrids: "call the listing agent to request the utility information **and send a follow up email**."

**Why it matters.** This is a workflow change, not an attachment rule, and it changes what the agent is expected to do. A phone call gets an answer today; an email might sit for two days. For "Clear to Close" in particular, that difference matters.

I do not want to silently convert your call tasks into emails on my own reading of a spreadsheet.

**What I suggest.** Follow the pattern tasks 130 and 140 already use: keep the call as the primary action, and have the system send the email as the follow-up or the fallback. The agent gets the fast answer, and there is still a written record on the file.

**Your answer:**

\- \[ \] Keep the call, add the email as a follow-up (my recommendation)

\- \[ \] Convert these fully to email, drop the call

\- \[ \] Leave them as phone-only, ignore the attachment rows

\- \[ \] Different per task: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

# **Part 2 — Two decisions in the guideline**

## **Question 6 — Should automatic emails be signed "Aime"?**

**This is the most important question in this document.** It changes what real buyers, sellers, lenders, and title reps see in their inbox on live deals.

**What your guideline says.** Section 15.2 requires every automatically sent email to be signed:

Aime

Assistant to {Agent Name}

{Agent Brokerage}

{Agent Phone} | {Agent Email}

RE: {Topic} – {Property Address}

And section 6.2 says these emails should be written as Aime, in the first person, without impersonating the agent.

**What happens today.** Automatic emails are signed **as the agent**, with the agent's own signature. A recipient has no way of knowing the agent did not type it. This came from a decision on July 10: recipients are never told that AI wrote the message.

**Do these conflict?** I do not think so, and this matters. "Aime, Assistant to Morgan Lee" names an assistant, not a computer. A client reading that learns there is an assistant on the file, exactly as they would with a human transaction coordinator. The July decision was about never disclosing AI, and nothing in your signature block discloses AI.

So the two rules can both hold. But the change itself is real, and it is visible to your clients.

**The trade-off, honestly stated.**

| Signing as the agent (today) | Signing as Aime (your guideline) |
| :---- | :---- |
| Feels personal; client believes their agent wrote it | Honest about who is doing the coordinating |
| Client may reply expecting the agent read it | Sets the right expectation for routine coordination |
| Awkward if the client later learns otherwise | Matches how a brokerage with a real assistant works |
| Agent's name on wording they did not choose | Agent's name still appears, on the second line |

**What I suggest.** Do it as your guideline says. It is the more honest option and it protects the agent, because the agent's name is no longer attached to sentences they never saw. I will also add an automatic safeguard that blocks the words "AI", "artificial intelligence", "bot", "automated", and "Velvet Elves" from ever appearing in an outbound email, so the assistant never becomes a disclosure.

I will build it with an off switch, so you can revert brokerage-wide in seconds if the reaction is bad.

**Your answer:**

\- \[ \] Yes, sign automatic emails as Aime (my recommendation)

\- \[ \] No, keep signing as the agent

\- \[ \] Yes, but let each brokerage choose

\- \[ \] Try it on a few accounts first

## **Question 7 — Inspection tasks: automate or always review?**

**What I found.** Your guideline and your spreadsheet disagree on this one.

Section 8 of the guideline lists **"Inspection responses"** and **"Repair demands"** as always requiring human review, "regardless of confidence score or user category authorization."

Your spreadsheet marks tasks 235 and 240 as "(To Be Automated)".

The system also has tasks 245 (another Inspection Response Reminder) and 250, 255, 257 (Inspection Negotiated).

**Why it matters.** Inspection negotiation is where deals die. An automatic email that phrases a repair position badly could commit your agent to something, or read as an acceptance. Your guideline is right to fence it off. But a reminder that a deadline is tomorrow is not a negotiation, and forcing a human to approve every one of those defeats the purpose.

**What I suggest.** Draw the line at content, not at task name:

\- **Reminders may send automatically** (tasks 240 and 245). These say "the response deadline is

tomorrow" and nothing more. I will add an automatic check that blocks the send if the text ever contains response, repair, or negotiation language.

\- **Inspection Negotiated always requires review** (tasks 250, 255, 257). These communicate an

outcome of a negotiation and will always land in the agent's queue for approval.

**Your answer:**

\- \[ \] Agreed, split it that way (my recommendation)

\- \[ \] Require review for all inspection tasks

\- \[ \] Automate all of them

\- \[ \] Different: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

# **Part 3 — Two things I can work around**

These do not block me. I can pick a sensible default and you can correct it later.

## **Question 8 — Exact "how to reply" instructions**

**What your guideline says.** Section 13.4 requires each email to tell the recipient exactly how to complete the request, using the method stored with the task, and never to invent one. Section 4.2 lists it as required input.

**What I found.** There is a field in the system for this, but it is empty for every task.

**Why it matters.** Without it, the email has to fall back on generic wording like "please let me know", which is exactly what your guideline is trying to eliminate. With it, the email says "please reply to this email and attach the signed disclosure" — a specific instruction the recipient can act on.

**What I suggest.** Add one more column to the attachment spreadsheet: **How should the recipient respond?** For most tasks the answer is short:

\- Reply to this email with the document attached

\- Reply All so everyone stays on the thread

\- Call the office

\- No response needed

**Your answer:**

\- \[ \] I will add a "How should the recipient respond?" column

\- \[ \] You choose sensible defaults and I will correct them

\- \[ \] Skip it for now

## **Question 9 — Writing style: per agent or per brokerage?**

**What your guideline says.** Section 11 supports a saved language preference, preferred phrases the agent likes to use, and prohibited phrases they never want sent.

**Why it matters.** It decides where the setting lives in the app. Per agent means every agent has their own; per brokerage means the admin sets it once and everyone inherits it.

**What I suggest.** Per agent. These emails go out under an individual agent's name, and voice is personal. A brokerage-wide default that individuals can override is more work than it is worth right now, and can be added later if a brokerage asks.

**Your answer:**

\- \[ \] Per agent (my recommendation)

\- \[ \] Per brokerage, set by the admin

\- \[ \] Brokerage default, agents may override

# **Appendix A — The 32 tasks with no attachment rule**

I have grouped these by how much thought they need. Most just need a tick.

A reminder on how I read the columns: **Attach** means the email carries these files. **Leave out** means the file may exist on the deal but must never ride this particular email.

## **A1 — Tasks whose own instructions already say what to attach**

These ten already state their attachment rule in the task text. I propose to use exactly that. Please confirm or correct.

| ID | Task | Goes to | Attach | Leave out |
| :---- | :---- | :---- | :---- | :---- |
| 8 | Review Documentation | Agent | Any unsigned documents found in the review | n/a |
| 80 | Confirm Title Order | Title | Purchase Agreement, all Counters, BLC or Tax Sheet, Sellers Disclosure, Lead Based Paint, Amendments & Addendums | Preapproval |
| 110 | Deliver HOA Docs (buy side) | Buyer | HOA documents | n/a |
| 115 | Deliver HOA Docs (both sides) | Buyer | HOA documents | n/a |
| 120 | Deliver HOA Docs (sell side) | Co-op Agent | HOA documents | n/a |
| 150 | Deliver Utility Info (buy side) | Buyer | Utility information | n/a |
| 155 | Deliver Utility Info (both sides) | Buyer | Utility information | n/a |
| 160 | Deliver Utility Info (sell side) | Seller | Utility information | n/a |
| 170 | Order Home Warranty | Home Warranty Company | Home warranty invoice, sent on to the title company once invoice is uploaded. | n/a |
| 265 | Appraisal Ordered (cash deals) | Not yet set — see note | Purchase Agreement, to match task 260, Counter Offer(s) and amendments | n/a |

**Two notes on this group.**

First, tasks 110/115/120 and 150/155/160 actually describe **two** emails, not one. For example task 110 reads: "1. Send a thank you email to the listing agent to acknowledge that the docs have been received. 2\. Email a copy of the docs to the buyer." Today one task sends one email. Do you want both emails, or is the thank-you optional?

\- \[X \] Send both emails

\- \[ \] Just deliver the documents, drop the thank-you

Second, task **265 has no recipient set** in the system, which means it cannot send anything. It is the cash-deal version of Appraisal Ordered. Who should it go to?

\- \[ \] Loan Officer, same as task 260

\- \[ \] Co-op Agent

\- \[ \] The agent, as a reminder

\- \[X \] Other: \_\_Buyer and/or Seller. Whomever you’re repping\_\_\_\_

## **A2 — Tasks I believe need no attachment**

These seventeen are notifications, confirmations, or reminders. Nothing to attach. Please confirm.

| ID | Task | Goes to | Why no attachment |
| :---- | :---- | :---- | :---- |
| 50 | Pending Reminder | Agent | A reminder to the agent to update the MLS |
| 210 | Inspection Scheduled (buy side) | Buyer/Agent/TC/Co-Agent | Confirms a date and time |
| 215 | Inspection Scheduled (both sides) | Buyer/Seller/Agent/TC/ Co-agent | Confirms a date and time |
| 220 | Inspection Scheduled (sell side) | Seller/Agent/TC/Co-agent | Confirms a date and time |
| 230 | Inspection Completed | Buyer/Agent/TC | Confirms the inspection happened |
| 245 | Inspection Response Reminder (sell side) | Agent/TC | Deadline reminder, same as 240 |
| 250 | Inspection Negotiated (both sides) | Seller/Buyer/Agent/TC/Co-agent | Milestone notification |
| 255 | Inspection Negotiated (buy side) | Buyer/Agent/TC/Co-agent | Milestone notification |
| 257 | Inspection Negotiated (sell side) | Seller/Agent/TC/Co-agent | Milestone notification |
| 350 | Schedule Closing | Client/Agent/TC/Co-op Agent | Walkthrough and closing times |
| 420 | Buyer Closing Information | Buyer/Agent/TC | Closing and walkthrough details |
| 430 | Seller Closing Information | Seller/Agent/TC | Closing and walkthrough details |
| 440 | Seller's Agent Closing Information | Co-op Agent/Agent/TC | Closing details |
| 450 | Buyer's Agent Closing Information | Co-op Agent/Agent/TC | Closing details |
| 500 | Internal Thank You | Agent/TC  | Feedback and rating request |
| 505 | Internal Thank You (both sides) | Agent/TC | Feedback and rating request |
| 510 | Internal Thank You (co-op) | Co-op Agent | Feedback and rating request |

**One to double check.** Tasks 420 and 430 send closing information to your clients. Should the Closing Disclosure be attached, or does the lender always send that separately?

\- \[ \] No attachment, the lender handles it

\- \[ \] Attach the Closing Disclosure when it is on file

## **A3 — Tasks that send no email at all**

These five need no rule. Listed only so you can see the full 32 accounted for.

| ID | Task | Why no email |
| :---- | :---- | :---- |
| 5 | Contract Acceptance Date | A date marker other tasks count from |
| 370 | Closing Gift (buy side) | A reminder to prepare a physical gift |
| 375 | Closing Gift (both sides) | A reminder to prepare a physical gift |
| 380 | Closing Gift (sell side) | A reminder to prepare a physical gift |
| 1000 | Closing Date | A date marker other tasks count from |

**Also worth confirming.** Tasks 480 "Exemptions and Thank You" and 490 "Thank You" are in your sheet with no attachments, which is right, but their instructions describe sending a physical **Thank You card**, not an email. Should the system email them, or just remind the agent to post a card?

\- \[ \] Remind the agent to send a card, no email

\- \[X \] Send an email as well This is intended for the system to send an email reminding the Buyer to file their tax exemptions. This email should go to the buyer(s)/agent/TC.

Also, any time buyer/seller/co agent is referenced above, all other co contacts should be included. e.g. If I said buyer and there are two buyers, both should be address and included on the emails. 

# **Appendix B — What I am building while I wait**

So you can see nothing is idle. None of this depends on your answers.

**Fixing which documents get attached.** I found a real bug while checking your spreadsheet against the code. The system currently matches documents by looking for words in the filename, and the word it looks for to find the Sellers Disclosure is simply "disclosure". That also matches "Lead-Based Paint Disclosure" and "Closing Disclosure". So today, an Order Title email attaches the lead paint disclosure and the closing disclosure even though neither belongs there. The word it uses for counters is "counter", which also catches "Counter Offer Addendum" — an addendum, which your sheet explicitly excludes.

Your spreadsheet is what made this visible, and I am rebuilding that matching properly. This is also what makes your "Documents to Exclude" column possible: right now the system has no way to say a document must be left out.

**Building the guideline as enforceable rules.** The seven categories, two delivery modes, fifteen auto-send gates, seventeen always-review topics, and the subject line patterns all become code that every email must pass through, rather than instructions we hope are followed.

**The missing information markers.** Section 17 of your guideline asks for markers like \[MISSING: VERIFIED DEADLINE\] and says such an email must not be sendable. I am wiring that so the Send button is genuinely disabled until the gap is filled, on every screen.

**The seventeen acceptance tests** in section 22 of your guideline become automatic tests that run on every change, so the behaviour you specified cannot quietly regress later.

# **What happens next**

Once I have Part 1 and Part 2 back from you, I can finish the attachment rules and the email rewrites. Part 3 I will start with sensible defaults and adjust when you get to it.

Thanks Jake.

Jan

