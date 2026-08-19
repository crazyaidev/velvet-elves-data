

# **VELVET ELVES**

## *AI-First Transaction Management Platform*

# **SMART AI AUTOMATION**

## **What It Does, What's Next, and What I Need From You**

| Prepared for | Jake |
| :---- | :---- |
| **Prepared by** | Jan Froben |
| **Date** | August 14, 2026 |
| **Status** | Built and running on staging. Not on the live site yet. |
| **What I need** | Your decisions in Section 6 so we can finish this cleanly and take it to production with your backing. |

# **Before you start**

This is the document I promised this morning: a plain-English picture of the smart AI automation we have been building, what an agent actually experiences, what we will improve next, and the decisions I will not make on your behalf.

**The short version**

Velvet Elves is not trying to "send more email." It is trying to work a file the way a good transaction coordinator does: do the routine letters that are always the same, prepare everything else overnight, and put the exceptions on one list for a human in the morning.

A small, named set of library letters — welcomes, title order / confirm title order, and the MLS pending reminder — may go out on their own when a deal is on **Assisted** or **Autopilot**. Every other email is drafted for the agent to read and send. Wire and funds mail is never drafted. Dates never move themselves. Legal calls, waives, and packet release stay human.

That system is live on **staging** today. It is **not** on production yet. I want your answers before we turn it on for real brokerages.

Nothing is stalled while you read this. The product already behaves the way this document describes. Your answers decide the next letters, how automatic mail is signed, how inspection is handled, and whether we ever add a countdown auto-send.

The attachment-sheet questions from the **Email Guideline & Task Attachments** Google Doc are still open. I have restated the ones that affect automation here so you can answer in one place. The 32-row attachment list can stay in that other doc.

# **1\. What "smart" means here**

Think of a coordinator who comes in at 7:30am, has already:

1\. Sent the standard welcome and title-order letters on files that were ready.

2\. Written the other emails that were due, and left them in a stack for you.

3\. Flagged every file that could not be finished — missing buyer email, missing purchase agreement, mailbox disconnected — with a reason and a next click.

That stack is **Needs You**. If the overnight run was healthy and nothing is waiting, the page simply says overnight prep ran and nothing needs you.

That is the product claim I want us to stand behind at conference: **the morning queue is prepared; you still send anything that is not a named library letter.** It is not "the AI works the file unsupervised."

ListedKit's public bar is still "you review and send." We already go further on a **narrow, named** exception (the library letters you asked for on July 13). The way to stay honest is to keep that exception tiny, and to make everything around it recoverable — not to widen unattended send until you explicitly say so.

# 

# **2\. How outgoing mail is handled**

Every outbound deal email falls into one of three buckets.

| Bucket | Examples | May the system send it by itself? |
| :---- | :---- | :---- |
| **Library letters** | Buyer / seller / co-op / loan-officer welcome; Order Title; Confirm Title Order; MLS pending reminder to the agent | **Yes**, on Assisted or Autopilot, if the deal is Active, the person's email is on the file, and a mailbox is connected |
| **Prepared drafts** | Due-task emails, replies to inbound mail, signature chases, vendor replies | **Never.** Autopilot only marks them Ready. Someone still taps Send. |
| **Delayed auto-send** | A countdown, then send, for factual / document-delivery mail only | **Not built.** I will not build it unless you approve it in Section 6\. |

The library-letter list is **closed**. Adding a new automatic letter is a product decision, not a toggle. There are currently 35 task templates labelled "to be automated" in the system. Those are a **promise**, not live send. The AI will not email them until we promote them one at a time, with a template, attachment rule, and your yes.

**Manual** is a real kill-switch. On Manual, library letters do not go out.

# **3\. The three settings: Manual, Assisted, Autopilot**

One choice for the whole workspace. Any single deal can override it from the deal header, or go back to "use the workspace default."

|  | Manual | Assisted (recommended) | Autopilot |
| :---- | :---- | :---- | :---- |
| Routine AI actions (add a contact, rename a file, draft an email) | You click | Runs | Runs |
| Email drafts | You ask | Prepared for review | Arrive Ready — you still tap Send |
| Welcome / title letters | Never auto | May send | May send |
| Dates, waives, legal | You | You | You |

Two things that look similar and are not:

\- **Wizard Autopilot** is only the intake shortcut when the contract parse is very confident. It does not mean the deal will send mail on its own.

\- **Deal Autopilot** is the setting above. Ready still means "ready for you," not "already sent."

I have not renamed these. Whether "Autopilot" should mean three different things is one of the questions below.

# 

# **4\. What is live today**

This is the system as built, running on staging.

## **4.1 The library letters that may send on their own**

Only these, and only on Assisted or Autopilot:

| Letter | Who receives it | What it needs |
| :---- | :---- | :---- |
| Buyer welcome | Buyer | Their email on Contacts |
| Seller welcome | Seller | Their email on Contacts |
| Co-op agent welcome | Co-op agent | Their email on Contacts |
| Loan officer welcome | Lender | Their email, plus the purchase agreement on the file |
| Order Title | Title company or title rep | Their email, plus the purchase agreement |
| Confirm Title Order | Title company or title rep | Same as Order Title |
| Pending reminder | The agent (not a client) | A nudge to mark the listing pending in the MLS |

**Review Documentation** is also an Automated task. It completes the review or, if signatures are missing, **drafts** a chase. That chase does not send until someone taps Send.

Guards that already apply:

\- Active deals only. Paused / closed files are left alone.

\- Recipients come only from **Contacts**. The system never guesses an address and never uses a platform "noreply" address for deal mail.

\- A connected Gmail or Outlook mailbox is required. No mailbox → the task is flagged, not sent.

\- **Manual** stops the send.

\- A task more than **30 days** overdue is flagged instead of surprising someone months later.

\- If that letter already left the mailbox, it is not sent again.

\- If title has already been ordered, Confirm Title Order is marked done instead of mailing twice.

\- The recipient is never told that AI wrote the message. Legacy "written by AI" disclaimers are stripped if they appear.

\- If the body says a file is attached, the file actually has to be on the email.

These letters use locked templates (address, closing date, the right packet) — not free-written AI prose. That is why they are allowed to send unattended. Wrong address or wrong attachment is still the risk, which is why Contacts and the purchase agreement are hard requirements.

## **4.2 Everything else waits for Send**

When a due task should produce an email that is **not** on the library list, the system writes a draft.

\- On **Assisted**, the draft sits in review.

\- On **Autopilot**, it can be marked Ready so Send is one tap — still a tap.

\- **Send all ready** always shows who will receive the mail and asks you to confirm.

The same rule applies to replies the AI writes to incoming mail, signature chases, and vendor replies.

## **4.3 Needs You — the morning list**

**Workflow → Needs You** is the one leftover pile:

\- Ready drafts (tap Send)

\- Drafts that still need a read

\- AI proposals that need Approve

\- Blocked AI tasks that need a person (missing email, missing document, mailbox, and so on)

The briefing on that page matches the doctrine: library letters may already have gone; everything else is waiting here. The count on Needs You is the same idea as the "needs you" number on a deal, so the badge and the file do not tell two different stories.

Batch actions still confirm. Cancel means nothing happens.

## **4.4 Overnight, once an hour**

A scheduled hourly run walks Active deals and:

\- Sends any library letters that are allowed and ready

\- Prepares due-task drafts

\- Flags what it cannot finish

\- Renews Gmail watches

\- Leaves a visible scoreboard in **Settings → AI & Automation**

On that page you can see:

\- Whether automation is active, and when it last ran

\- How many library letters went out versus how many were flagged for a person

\- How many mailboxes are connected and healthy

\- A workspace switch for **Hourly automation** (on/off)

\- A workspace switch for **Library letters** (allowed / paused)

Safe buttons come first: **Preview next tick** (read-only — names who would be emailed, sends nothing) and **Draft due emails** (creates drafts, does not send). **Run AI tasks** is the one that can send library letters. It always confirms, and it can be cancelled.

If the last run actually sent library letters, the page says so in plain language. It does not hide that.

A daily digest email is a **per-person opt-in**. Changing posture does not secretly turn digests on for the whole office.

## **4.5 When the AI stops, it says why — and it tries again**

This was the gap that made the old stack feel like a sorter, not a coordinator. It is closed on staging.

If a library letter cannot go out, the task lands in Needs You with a reason that matches a real button:

| The AI stopped because | What you actually click |
| :---- | :---- |
| No email on that party | **Add contact** on Contacts |
| Purchase agreement (or other required file) is missing | **Upload document** |
| Mailbox disconnected or unauthorized | **Reconnect mailbox** in Email & E-signature |
| Task is more than 30 days overdue | **Change due date** |
| Deal is on Manual | Switch the deal to Assisted or Autopilot, or complete it yourself |
| Library letters are paused for the workspace | Turn them back on in AI & Automation |

Fixing the cause retries **that deal**. You do not wait for the next hourly run, and you do not have to press a hidden "give it back" just to add a buyer email. **Give this back to the AI** is still there when the error was a one-off failure.

**Try now (this deal only)** is available for admins. It never ticks every brokerage at once.

## **4.6 Incoming mail**

Inbound mail is filed to a deal when we can tell which file it belongs to. The Email pane shows **why this deal**. If it landed on the wrong file, **Refile** moves it in one step.

\- A factual question ("when is closing?") gets a draft. It does not send.

\- A statement that matters ("the title commitment is ready") is kept on the file even if it is not a question. It is not dropped.

\- **Wire instructions, routing numbers, banking details, earnest-money direction, payoff figures** are held. No reply draft. Never Ready. This now also catches wording like "please send banking details for closing," not only the phrase "wire instructions."

\- Newsletters and junk can be filtered. Filtered mail shows the envelope only. **Undo filter** puts it back.

Inspection-response language stays in human review. I have not automated inspection negotiation. That waits on your answer in Section 6\.

## **4.7 Rules that no setting can turn off**

These are on the AI & Automation page under **Always true**:

\- Library welcome and title-order letters may send on Assisted and Autopilot. Every other email is drafted for you to send.

\- Deadlines never move themselves. A date change always goes through a preview you confirm.

\- Waives, legal calls, and packet release stay human.

\- Wire and funds mail is never drafted.

The AI agent on a deal can propose work and, on Assisted/Autopilot, apply a small set of low-risk actions (draft an email, add a party, rename a file). It **cannot** send mail as an agent action. Sending, when it happens, goes through the same guarded delivery path as a human Send: honest attachments, no AI disclosure, the user's mailbox.

## **4.8 Where an agent actually clicks**

| To… | Go here |
| :---- | :---- |
| See what still needs a person | Workflow → **Needs You** |
| Change how much runs on its own | Settings → **AI & Automation** |
| Connect or reconnect Gmail / Outlook | Settings → **Email & E-signature** |
| Read and send drafts | Intelligence → **Email**, or the deal's Email tab |
| Override one file | The posture control on the deal header |
| See what ran without a click | The deal's Activity tab, Automation filter |

# **5\. What we will not do unless you say so**

I am stating these as commitments, because they are how we keep your agents out of trouble and keep the conference story honest.

\- We will **not** turn the 35 "to be automated" templates into automatic letters in one deploy.

\- We will **not** let the AI change dates, waive contingencies, give legal advice, or release a packet.

\- We will **not** draft or Ready-mark wire / banking / earnest-money-direction mail.

\- We will **not** add a countdown that sends mail while the agent is away, unless you approve that feature below.

\- We will **not** grow the library-letter list without a written yes for that specific letter.

\- We will **not** put those letters on a brand-new production workspace that is still on Manual and has no mailbox.

As long as these are NOT hard stops and just for the conference. Most of these will be easy to automate once we get you additional information on exactly how each task will be completed. They will become common sense after we get through 4-5 of them.

# **6\. What I need from you**

Please tick one box per question. The first five change what buyers, sellers, lenders, and title reps see.

## **6.1 Please answer these first**

**Question A — How should automatic letters be signed?**

Today they are signed **as the agent**, with the agent's own signature. Recipients have no signal that the agent did not type them. That came from the July 10 rule: never tell the recipient that AI wrote the mail.

Your email guideline says they should be signed:

Aime Assistant to {Agent Name} {Brokerage} {Phone} | {Email}

"Aime, Assistant to Morgan Lee" names an assistant, not a computer. It does not disclose AI. It does change what clients see.

| Sign as the agent (today) | Sign as Aime (your guideline) |
| :---- | :---- |
| Feels personal | Honest about who is coordinating |
| Client may reply expecting the agent read it | Sets the right expectation |
| Agent's name on wording they never saw | Agent's name still appears, on the second line |

**My recommendation:** Sign as Aime, with an off switch so we can revert brokerage-wide if the reaction is bad. Until you answer, automatic letters stay signed as the agent.

\- \[X \] Yes, sign automatic emails as Aime (my recommendation)

\- \[ \] No, keep signing as the agent

\- \[ \] Yes, but let each brokerage choose

\- \[ \] Try it on a few accounts first

**Question B — Inspection: automate reminders, or always review?**

Your guideline lists inspection responses and repair demands as always-review. Your attachment spreadsheet marks some inspection tasks "to be automated." Inspection negotiation is where deals die. A reminder that a deadline is tomorrow is not a negotiation.

**My recommendation:** Reminders may send automatically (deadline only, no repair language). Inspection Negotiated always requires review. Until you answer, **all inspection stays human** — no Ready draft on an inspection response.

\- \[X\] Agreed: automate reminders only (my recommendation)

\- \[ \] Require review for all inspection tasks

\- \[ \] Automate all of them

\- \[ \] Different: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Question C — Keep the automatic-letter list closed?**

Confirm that the only unattended deal letters are the named set in Section 4.1, and that we will not add a seventh without a written yes for that template.

**My recommendation:** Yes. A surprise extra letter on live files is the kind of mistake we cannot unsend.

\- \[ \] Yes, freeze the list. Promote new letters one at a time with my written yes (my recommendation)

\- \[X \] I want additional letters automatic now — list: \_\_to be provided\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Question D — Delayed auto-send (countdown \+ Hold)?**

This would be the only **new** unattended send: for factual and document-delivery drafts only, tenant opt-in, a visible countdown (about five minutes), and a Hold button that puts it back in review. Off by default. Money and inspection-response would never enter the window.

**My recommendation:** Do not build this until the current system has soaked on production. Staging already does overnight prep. The conference story should be Needs You in the morning, not "mail left while you slept" beyond the named library letters.

\- \[X\] Defer. Do not build it yet (my recommendation)

\- \[ \] Build it, off by default, for factual / document-delivery only

\- \[ \] Do not build it at all

**Question E — What should a new workspace start on?**

The code default is **Manual**. Staging is currently set to **Autopilot** so we could prove the full path. Autopilot-as-default means Ready drafts and library letters on create for every new file.

**My recommendation:** Every environment starts **Manual**. Assisted or Autopilot is an explicit choice, and library letters stay off on a brand-new production workspace until Assisted is chosen **and** a mailbox is healthy.

\- \[X \] Start Manual; Autopilot is opt-in only (my recommendation) Add this as an option to the account creation screen when a user creates an account.  This will allow them to choose their preference right away and notify them that they can change their preferences at any time in “settings”. 

\- \[ \] Start Assisted

\- \[ \] Start Autopilot

## **6.2 These finish the task list and attachment rules**

These are the same questions as in the Email Guideline Google Doc. Answering them here is enough; you do not need to answer twice. They block promoting any more letters, because I will not guess task IDs or attachment rules.

**Question F — Task 235 "Buyer's Inspection Response Due" does not exist.** Closest matches: 230 Inspection Completed, 240 / 245 Inspection Response Reminder.

\- \[ \] I meant task 240

\- \[ \] I meant task 245

\- \[ \] I meant task 230

\- \[ \] 235 is a new task — details: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Task 235 is the seller version of Task 230\. The slight differences in the tasks are the operational functions. The use case for task 235 are Seller Finance and Seller Cash. 

**Question G — Add tasks 453 (pick up sign and lockbox) and 455 (MLS to Sold)?** Both as agent self-reminders on seller-side deals, day of closing, no attachments.

\- \[X \] Add both with those settings (my recommendation)

\- \[ \] Add both, but change: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\- \[ \] Do not add them

**Question H — Tasks 460 / 470 are "Request Referrals" in the product, "Request Testimonials" on your sheet.**

\- \[X \] Rename to Request Testimonials and write a review request (my recommendation)

\- \[ \] Keep Request Referrals and write a referral request

\- \[ \] Split into two tasks

**Question I — 32 tasks have no attachment rule.** I pre-filled them in Appendix A of the Email Guideline doc. A task with no rule attaches nothing, which is wrong for HOA / utility delivery.

\- \[ \] Appendix A approved

\- \[ \] Appendix A approved with notes: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\- \[X \] I will mark it up in the Google Doc

**Question J — Four tasks are phone calls in the system (appraisal ordered / completed, clear to close, CD delivered) but emails on your sheet.**

\- \[X \] Keep the call, add the email as a follow-up (my recommendation)

	We prefer the email go out and then the hope is the user calls the client shortly after the email notification.

\- \[ \] Convert fully to email, drop the call

\- \[ \] Leave them phone-only

\- \[ \] Different per task: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Until F–J are answered, those tasks stay **prepared drafts or human work**. They will not become automatic letters. 

## **6.3 These I can start without — correct me when you can**

**Question K — Exact "how to reply" line on each task?** (Your guideline wants "reply with the signed disclosure attached," not "please let me know.")

\- \[ \] I will add a column to the sheet

\- \[X \] You choose sensible defaults and I will correct them (my recommendation if you are short on time)

\- \[ \] Skip it for now

**Question L — Writing style: per agent or per brokerage?**

\- \[X \] Per agent (my recommendation) Really it’s per user. TC, TL, Admin, etc. user

\- \[ \] Per brokerage, set by the admin

\- \[ \] Brokerage default, agents may override

**Question M — The name "Autopilot" is used for intake, for deal posture, and (if we ever built it) for full send.** That confuses testers and will confuse agents.

\- \[ \] Keep the current names

\- \[ \] Rename deal Autopilot to something else — suggestion: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\- \[X\] Let's discuss on a call (my recommendation) Agreed and I would love to hear your thoughts/concerns about this. Should we use our AI name for this? (Aime)

**Question N — After a library letter sends, should the deal progress bar count that AI task, or only the Automation activity line?** Today progress often ignores Automated rows on purpose so the human bar stays honest.

\- \[ \] Keep progress as the human bar; show AI work on Automation / handled today (my recommendation)

\- \[X \] Count Automated completions in progress % as well This will show a user that AI is working on their files while they have been away, which is a staple to our marketing campaign and general product as a whole.

# **7\. What I will build next, in order**

Your answers in Section 6 decide the later items. This is the sequence I am asking you to support.

**Already on staging (this week)**

The hourly run is visible and honest. Copy on every screen tells the same story. Needs You counts match the deal. When the AI stops, the reason matches a real button and the deal retries. Duplicate library letters are skipped. Money-adjacent inbound is held. Incoming mail can be refiled. New production workspaces can start with library send off.

**Before conference (September 12 lock / September 22 conference)**

Keep soaking this on staging, then promote to production **after** Questions A–E. Conference claim: overnight preparation, Needs You in the morning, library letters named and bounded. Not "Ava works the file."

**After conference, still without growing automatic send**

Smarter "this is already done" checks (for example: do not request something the inbound already answered). Stronger inbound filing so every kept message is on the right file or honestly unmatched.

**Only with your answers**

Promote additional letters **one per week**, after a stage soak, using your attachment sheet once the IDs match. Aime signature if you choose it. Inspection reminders if you choose that split.

**Only with an explicit yes on Question D**

The countdown delayed auto-send.

# **8\. How this compares with "the AI just emails everyone"**

| What people fear | What Velvet Elves actually does |
| :---- | :---- |
| The AI invents a letter and sends it | Only named library templates, from deal facts |
| It emails a guessed address | Only captured Contacts emails |
| It talks about wires | Those messages are held, never drafted |
| It moves a closing date | Dates never move without your confirm |
| It keeps sending after something is wrong | It stops, names the cause, and retries when that cause is gone |
| You cannot tell what it did | Needs You, the Overnight scoreboard, and the deal's Automation activity |
| A new brokerage starts firing letters on day one | Manual \+ library letters off until they opt in and connect a mailbox |

# **What happens next**

Once I have Section 6.1 (Questions A–E), I can take this from staging to production with a story every agent can repeat in one sentence:

**On Assisted and Autopilot, Velvet Elves may send the library welcome and title-order letters by itself. Every other email is drafted for you to send.**

Section 6.2 lets me finish the attachment rules and, later, promote more letters safely. Section 6.3 I will start with the recommendations above unless you correct them.

If you want to click through it together on staging before production, say the word and I will walk you.

Thank you, Jake.

Jan

