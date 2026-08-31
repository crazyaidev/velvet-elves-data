

# **VELVET ELVES**

## *AI-First Transaction Management Platform*

# **AIME AND YOUR TRANSACTION FILE**

## **Questions**

| Prepared for | Jake |
| :---- | :---- |
| **Prepared by** | Jan Froben |
| **Date** | August 17, 2026 |
| **About** | How Aime should work a live transaction file |
| **What I need from you** | 8 answers (tick the boxes in this doc) |

# **Before you start**

I have read your AI architecture and Audri’s answers. I am not re-asking anything already decided.

This doc is only the file-logic questions that still change what an agent, buyer, or seller experiences. Tick a box under each question. If the recommendation is wrong, use **Different** and write the rule you want.

Already decided — not in this doc: automatic letters signed as Aime; new offices start on Manual; inspection \*reminders\* may send and inspection \*negotiation\* waits for you; every person in a role is on that email; assigned TCs can work that file operationally; delayed auto-send is deferred.

# **At a glance**

| \# | Question | Blocking? | My recommendation |
| :---- | :---- | :---- | :---- |
| 1 | The word Autopilot is used for two different things. What should agents see? | No | Keep **Manual** / **Assisted** for the live file. Do not use Autopilot for intake and the live file. Call intake **Fast intake**. |
| 2 | After the current named letters, which emails may leave without a tap? | Yes | Do not guess. Add only the letters you list below, in that order. |
| 3 | Buyer / seller closing-information email: attach the Closing Disclosure? | Yes | No. The lender sends the CD. |
| 4 | Should buyers and sellers talk to Aime in this phase? | Yes | Not in this phase. They keep asking the team. Aime may give status and next steps later. Legal and “should I…?” always go to the agent. |
| 5 | After closing day, is the file still active until post-closing work is done? | Yes | Yes. Closing day is not the end of the file. |
| 6 | If the deal falls through, what should Aime do? | Yes | Stop automatic mail. Keep the history. Treat it as failed, not closed. Do not start listing or marketing. |
| 7 | A later signed amendment changes a date. Who confirms it? | Yes | Aime shows old date vs new date. You confirm, unless the language is explicit, complete, and non-conflicting **and** the file is on Autopilot. Fuzzy always waits. |
| 8 | On a cash file, who (if anyone) gets “Appraisal Ordered”? | Yes | Do not email a client about an appraisal on a cash deal. Make it an agent reminder, or do not create the task. |

## **Question 1 — Autopilot currently means two different things**

**What I found.** When you drop a contract in, Autopilot only means “the read is confident enough to skip extra confirming.” It does **not** mean Aime will email anyone.

On the live file, Autopilot means drafts arrive ready for one tap, and the named welcome / title letters may send on their own. You still tap Send on everything else.

Agents will mix these up if both are called Autopilot.

**Why it matters.** This is a label, not a new behavior. The two actions stay separate either way.

**What I suggest.** Keep **Manual** (you click) and **Assisted** (Aime does routine work; named letters may send; other mail is drafted for you) for the live file. Give the live-file third setting a name that still means “ready for one tap,” not “Aime sends everything.” Call the intake shortcut **Fast intake**, not Autopilot.

I am **not** proposing that Autopilot start moving dates or sending extra letters. That would be a different product.

**Your answer:**

\- \[ \] Keep Manual / Assisted / Autopilot for the live file, and call intake **Fast intake**

\- \[ \] Keep Autopilot for intake, and rename the live-file setting: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\- \[ \] Different names: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Where exactly does the user see these options, outside of the settings page? 

Also, in the automation posture section of the settings page we need to change the verbiage. Autopilot is as automated as it can be based on AI confidence for each task. No need for the user to approve/”tap to send”. That is an “assisted” feature. 

When saving “Assisted” and “Autopilot” the automation rules and confidence gates are the same. These should be two different automation roles. 

![][image1]

## 

**Jan’s response (18 Aug 2026\)**

You are right, and the copy on that settings card is wrong. We treated Autopilot as “drafts arrive Ready, you still tap Send.” That is Assisted. Autopilot is the high-automation role: when a task is authorized and confidence is high enough, Aime sends without a tap.

**Where the three options appear today (besides Settings → AI & Automation → How it runs):**

1\. **Account creation** — Manual / Assisted / Autopilot on Register. Skipping leaves Manual.

2\. **Onboarding** — the same three cards, with “you can change this anytime in Settings.”

3\. **The live file** — the automation chip in the deal workspace header. The agent can set this deal to Manual, Assisted, or Autopilot, or inherit the workspace default.

4\. **Echoes only (not choosers)** — Email tab, overnight status line, and the “Running on Autopilot” note. Those will be rewritten to match the new meanings.

Intake “Autopilot” (skip extra confirming when the contract read is confident) stays a **different control**. We will stop using the word Autopilot there so it is not confused with the live-file setting. Working name: **Fast intake**.

**Two different roles (what we will implement):**

|  | Manual | Assisted | Autopilot |
| :---- | :---- | :---- | :---- |
| Routine file work | You click | Runs | Runs |
| Mail that is authorized and above the confidence gate | You send | Drafted; you tap Send | Sends without a tap |
| Mail below the confidence gate, or missing a fact | You | Needs You / draft | Needs You / draft |
| Money, waives, legal, inspection \*negotiation\* | You | You | You |

Today Assisted and Autopilot really do share the same send rules. That is the bug you caught. After the split, Autopilot is not “Assisted plus a Ready badge.” It is a different role.

**Hard stops that still apply on Autopilot** (already decided with Audri; confidence cannot override them): no mailbox → no send; incomplete Aime profile → no automatic letter; money / wire / legal / inspection negotiation never auto-sends; a letter not on the authorized list (Question 2 / your spreadsheet) does not send just because confidence is high.

**One confirmation I still need from you on Autopilot:** when confidence is \*below\* the gate, should Aime leave a draft in AI Emails for one tap (same pile as Assisted), or only a Needs You row with no draft? Recommendation: **both** — draft plus Needs You — so the agent can send it without re-writing.

## 

## **Question 2 — Which letters may leave without a human tap?**

**What I found.** Today, and only on Assisted or Autopilot, only when that person’s email is on the file and a mailbox is connected, these may send on their own:

\- Buyer welcome

\- Seller welcome

\- Co-op agent welcome

\- Loan officer welcome

\- Order Title

\- Confirm Title Order

\- MLS pending reminder (to the agent, not a client)

Audri already approved inspection **reminders** (“the response deadline is tomorrow,” no repair language). She also wants more automatic letters, with the list still to come.

**Why it matters.** A letter we cannot unsend is not something I should invent.

**What I suggest.** I will add inspection reminders unless you say no. I will not add any other automatic letter until you name it here, in the order you want it.

**Your answer:**

\- \[ \] Stop after the current list plus inspection reminders

\- \[ \] Add these next, in this order: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\- \[ \] Do not add inspection reminders either

\- \[X \] Different: We’ll send you the updated task spreadsheet with how each task should work.

**Jan’s response (18 Aug 2026\)**

Understood. I will **not** invent any further automatic letters.

Until the spreadsheet arrives, the only letters \*authorized\* to leave without a tap remain:

– Buyer / seller / co-op / loan-officer welcome

– Order Title / Confirm Title Order

– MLS pending reminder (to the agent)

– Inspection **reminders** (deadline only; repair and negotiation language never sends)

Question 1 still applies to \*how\* they leave:

– **Assisted:** even an authorized letter is drafted; you tap Send.

– **Autopilot:** an authorized letter that clears the confidence gate sends without a tap. Below the gate, or missing a mailbox / recipient / fact → Needs You / draft.

The spreadsheet is the grant list for everything else. Autopilot confidence is a second gate, not a blank check. I will implement each row as written (who it goes to, attachments, call vs email, whether it may auto-send). I will not promote a row to unattended send unless that row says so.

Inspection reminders stay on the authorized list because Audri already approved them and they were already decided at the top of this doc. If the spreadsheet later says otherwise, the spreadsheet wins.

## **Question 3 — Closing-information emails and the Closing Disclosure**

**What I found.** The buyer and seller closing-information tasks send closing and walkthrough details. The attachment sheet does not say whether the Closing Disclosure should ride along when it is on the file.

**Why it matters.** The lender is responsible for delivering the CD. Attaching the wrong CD, or an old one, is worse than attaching nothing.

**What I suggest.** Do not attach the Closing Disclosure. The lender handles it.

**Your answer:**

\- \[ \] No attachment — the lender handles the CD

\- \[ \] Attach the Closing Disclosure when it is on the file

\- \[ \] Different: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Can you please confirm the task ID you’re referring to? These appear to be two different tasks. 

**Jan’s response (18 Aug 2026\)**

Yes,  they are two different tasks. I was asking about **both**, because both send closing / walkthrough information and neither has an attachment rule on the sheet yet:

| ID | Name | Goes to | Use cases |
| :---- | :---- | :---- | :---- |
| **420** | Buyer Closing Information | Buyer | Buy-Fin, Buy-Cash |
| **430** | Seller Closing Information | Seller | Sell-Fin, Sell-Cash |

Related, but **not** what I meant: **440** (seller’s agent closing information) and **450** (buyer’s agent closing information) go to the co-op agent.

**Working rule until you say otherwise:** do **not** attach the Closing Disclosure on 420 or 430\. The lender is responsible for delivering the CD. Attaching the wrong version, or an old one, is worse than attaching nothing.

Please tick one:

– No CD on 420 or 430 (recommended)

– Attach the CD on 420 only / 430 only / both, and only when the file has a current CD

18-AUG-2026 Response:

This will be cleared up with the new task spreadsheet.

## **Question 4 — Should buyers and sellers talk to Aime in this phase?**

**What I found.** Today they ask the team. Your architecture wants them to be able to ask Aime for status and next steps, and to route professional questions to the agent.

**Why it matters.** If Aime answers clients before that line is settled, she can wander into legal advice, negotiation, or speaking for a co-buyer.

**What I suggest.** In this phase, clients keep asking the team. Next phase, Aime may give **known** status and **known** next steps only. “Can I back out?”, waives, repairs, and anything like it always go to you.

**Your answer:**

\- \[ \] This phase: ask the team. Next phase: status and next steps only

\- \[X\] This phase: Aime may answer “where is my file?” (status only)

\- \[ \] Clients should not talk to Aime

\- \[ \] Different: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

She should never answer legal questions, or interpretive questions. She should ONLY answer 100% factual, informative questions. 

**Jan’s response (18 Aug 2026\)**

Recorded: this phase, buyers and sellers may ask Aime **“where is my file?”** Status only. Never legal. Never interpretive. Never “should I…?”

**What “100% factual” means in code (so she cannot wander):**

– She may repeat **known file facts** with a source: dates already on the file, documents already uploaded, task status, scheduled closing/walkthrough times, who is on the file.

– She may **not** infer a date from an email (“appraisal is Tuesday”), interpret a clause, compare offers, speak for a co-buyer, or tell someone they can back out, waive, or accept repairs.

– Anything she cannot ground in a stored fact goes to the agent, with the client’s question attached.

This is not in the product today — clients still message the team. Your rule is accepted. We will not turn client Aime on until that factual cage exists, so she cannot wander into legal or interpretive answers. When it ships, it is status-only, not a second agent.

**One confirmation:** when she cannot answer, should she name **you** (“I’ll have \[Agent\] get back to you”), or only say “your agent”? Recommendation: use the agent’s name.

18-AUG-2026

– She may **not** infer a date from an email (“appraisal is Tuesday”), interpret a clause, compare offers, speak for a co-buyer, or tell someone they can back out, waive, or accept repairs.

She should be able to communicate info that she receives from emails, in the following manner:

“The latest information I have is the appraisal is Tuesday. I will confirm with (Agent) and if anything is different (Agent) or I will reach back out to you.”

**Question 5 — After closing day, is the file still active?**

**What I found.** The file can look finished on closing day, while lockbox pickup, MLS to Sold, tax exemptions, and thank-yous are still open. Your architecture says closing does not finish Aime’s job.

**Why it matters.** If closing day hides those chores, they get skipped. If the file stays active forever, it never looks done.

**What I suggest.** Closing day is the closing event. The file stays active until the post-closing work is finished or you close it on purpose.

**Your answer:**

\- \[X \] Yes — the file stays active until post-closing work is done

\- \[ \] Closing day is the end. Post-closing is a reminder list only

\- \[ \] Different: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Jan’s response (18 Aug 2026\)**

Agreed. Closing day is the closing **event**. The file stays **Active** until the post-closing work is finished, or you close it on purpose.

That includes lockbox / sign pickup (**453**), MLS to Sold (**455**), tax-exemption thank-you (**480**), seller thank-you (**490**), and any other open post-close row. Completing those is what makes the file look done — not the calendar date alone. A file can still look Active a few weeks after closing while 480/490 wait; that is the point.

We will not hide those chores when the closing date passes, and we will not leave the file Active forever with no way to close it.

## **Question 6 — If the deal falls through, what should Aime do?**

**What I found.** A dead deal can look the same as a closed deal. We are not building listing or marketing in this phase.

**Why it matters.** Automatic welcome or title letters must not keep going on a dead file. A failed deal should not be filed as if it closed.

**What I suggest.** Stop automatic letters. Keep the history (dates, decisions, documents, communication). Mark it failed / terminated, not closed. Leave you a note. Do not start listing or marketing.

**Your answer:**

\- \[X\] Yes — stop mail, keep history, mark failed, no listing behavior

\- \[ \] Also notify these parties: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\- \[ \] Different: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Jan’s response (18 Aug 2026\)**

Agreed. On a fallen-through file Aime will:

1\. **Stop** automatic letters and overnight drafts immediately, the same as if the file were on Manual.

2\. **Keep** the history — dates, decisions, documents, mail.

3\. **Mark it failed / terminated**, not Closed. Closed is for a deal that actually closed.

4\. **Leave you a note** on the file. No extra party emails unless you later name them.

5\. **Not** start listing or marketing. That is a different product.

Today the statuses are Active / Incomplete / Paused / Completed / Closed. There is no Failed. We will add a distinct failed/terminated status so reporting and Aime never treat a dead file as a closed one.

## **Question 7 — A later amendment changes a date**

**What I found.** At intake, you confirm the dates Aime reads from the contract. After that, a signed amendment that moves closing or inspection is just another document. The old dates can stay on the file until someone notices.

**Why it matters.** The later signed document is what controls. Aime should not overwrite the file in the dark, and should not ignore the amendment.

**What I suggest.** Aime prepares “the contract used to say X; this later signed document says Y.” On Manual and Assisted, you confirm before the new date is official. On Autopilot, she may apply it **only** if the language is explicit, complete, and does not conflict with another document. If anything is fuzzy, she waits.

**Your answer:**

\- \[ \] Always wait for me to confirm the new date

\- \[X\] Confirm on Manual and Assisted; on Autopilot, apply it only when the amendment is explicit and does not conflict

\- \[ \] If the amendment is explicit, apply it on any setting

\- \[ \] Different: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Jan’s response (18 Aug 2026\)**

Agreed. The later signed document controls. Aime never overwrites dates in the dark.

**Rule we will implement:**

– Aime prepares: “the file used to say X; this later signed document says Y,” with both sources.

– **Manual and Assisted:** you confirm before the new date is official.

– **Autopilot:** she may apply it **only** if the language is explicit, complete, and does not conflict with another document on the file.

– **Fuzzy, incomplete, or conflicting:** she always waits — including on Autopilot.

This is not in the product yet. Intake still confirms dates once; a later amendment is just another document until we ship this.

## **Question 8 — “Appraisal Ordered” on a cash file**

**What I found.** The financed version of this task writes the loan officer. The cash version has no recipient. Audri said to write the represented client (buyer and/or seller).

**Why it matters.** On a cash file there is often no appraisal. Emailing a buyer or seller that an appraisal was ordered can look like a mistake.

**What I suggest.** Do not send that as a client email on a cash deal. Either it is an agent-only reminder, or the task does not belong on cash files.

**Your answer:**

\- \[ \] Agent-only reminder on cash files — no client email

\- \[ \] Do not create this task on cash files

\- \[ \] Email the represented client, as Audri said

\- \[X\] Different: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Treat this just like a financed deal. We will still have the “Appraisal Ordered” task and “Appraisal Completed” task. However, we will change the target from the loan officer to the buyer. This will allow the agent to be reminded in case the buyer fails to order the appraisal.

**Jan’s response (18 Aug 2026\)**

Recorded, with one correction to how the cash rows work today, and one question.

**What already exists**

| ID | Name | Files | Target today |
| :---- | :---- | :---- | :---- |
| **260** | Appraisal Ordered | Buy-Fin, Sell-Fin | Loan officer |
| **270** | Appraisal Completed | Buy-Fin, Sell-Fin | Loan officer |
| **265** | Appraisal Ordered | Buy-Cash, Sell-Cash | \*(blank — call co-op or buyer by who we represent)\* |
| **271** | Appraisal Completed | Buy-Cash, Sell-Cash | \*(blank — same shape as 265)\* |

Cash rows already exist as a pair. They already **do not** fire if the cash buyer waived the appraisal, or if we have not yet recorded whether they elected one. Financed 260/270 stay aimed at the loan officer.

**What we will change (cash only):** set **265** and **271** Target \= **Buyer**, keep Agent (and co-op) on copy. The agent is reminded because they are on the thread and the task stays open / reschedules if the buyer has not ordered. This is **not** an automatic send until your spreadsheet (Question 2\) says so.

**Question I still need:** on a **Sell-Cash** listing (we represent the seller), should that email still go to the **buyer**, or to the co-op / represented seller? Emailing the other side’s client from our file is a different letter than reminding \*our\* buyer on a Buy-Cash deal.

Recommendation if you want one rule: **Buy-Cash → Buyer; Sell-Cash → co-op agent** (today’s 265 instructions), still with the agent in copy. If you want Buyer on both sides, say so and we will do that.

18-AUG-2026

Target should be co agent and TC  for task 265 and 271 if your client is the seller.

[image1]: <data:image/png;base64,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>