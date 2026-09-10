# Welcome email delivery by automation posture

**Prepared by:** Jan Froben
**Date:** 10 September 2026
**About:** How named welcome letters leave the file today, under Manual, Assisted, and Autopilot
**What this is not:** The hello@ account welcome that goes out when someone first gets a Velvet Elves login. That is a separate platform email. It does not use posture, and it does not come from the agent’s mailbox.

---

## What “welcome emails” means on the live file

When staff say welcome emails, they mean the **named letters Aime sends as the agent**, from the **deal owner’s connected mailbox** (Gmail, then Outlook). They are first-person, signed as the agent, and they never mention AI.

There are four of them. Each is an Automated task in the task library:

| Letter | Who it goes to | Contract packet required? |
|---|---|---|
| Buyer Welcome | Every captured buyer with an email | No |
| Seller Welcome | Every captured seller with an email | No |
| Co-op Agent Welcome | The agent on the other side | No |
| Loan Officer Welcome | The loan officer | Yes — the purchase agreement must be on the file |

The platform used to also send a hello@ “party introduction” at deal create. That was retired on 16 July 2026 so each party is welcomed once, from the agent.

Subjects and opening lines (library templates, not free-written):

- Buyer: *Welcome — we're under way on {address}*
- Seller: *Your sale of {address} is under way*
- Co-op: *Working together on {address}*
- Loan officer: *New file: {address} — contract documents*

---

## Where posture is chosen

Posture is **who may send named emails**. It is not Trusted dates, and turning Autopilot on does not turn Trusted on.

**Workspace default** lives at **Settings → AI & Automation → How it runs → Automation posture**. The three cards are Manual, Assisted (marked Recommended), and Autopilot. New offices start on Manual until an admin picks one.

**One deal** can differ from the office. The chip in the deal header opens Manual / Assisted / Autopilot, or Follow the workspace. The deal choice wins when it is set.

A second workspace switch, **Hourly library send**, sits next to posture. When it is off, Autopilot still does not send welcome or title-order letters. New production signups start with this off until Assisted or Autopilot is chosen **and** a healthy mailbox is connected.

---

## What is the same on every posture

These rules do not change when the card changes.

**Who writes the letter.** Aime fills a fixed library template from facts already on the deal (names, address, closing date, attached documents). She does not invent a new letter each time.

**Who it is from.** The deal owner’s connected mailbox. Replies go back to that inbox. Velvet Elves hello@ is not the sender.

**Who it is to.** Only parties already captured on Contacts, with an email address. No email → the task waits as **Needs You** (*No … email is on file*). Adding the address retries the letter. Co-op is side-aware: on a buyer-side file it is the listing agent; on a seller-side file it is the buyer’s agent. Dual files can suppress the co-op welcome so the same office is not emailed as if it were the other side.

**When it tries.** As soon as the deal is Active and the welcome task is due — usually at create, then again on the hourly tick, on **Run AI tasks**, after a document parse, and after someone adds a missing party email. The deal must still be Active. A task overdue more than 30 days is not mailed; it waits for a person.

**Attachments.** Buyer, seller, and co-op welcomes attach the purchase package that is already on the file. They still go out if the packet is empty. The loan-officer welcome will not go out until the purchase agreement is uploaded.

**One letter per task.** If that welcome already left the mailbox, the task completes as already done. It does not mail twice.

**Hard stops (any posture).** No mailbox, or a mailbox that will not send. Incomplete Aime signature. The body hitting a topic that always needs a person (legal / terminate language). The recipient address rejected. Those land in Needs You with a sentence that names the fix. They do not go out.

**What you see on the deal.** Once Aime finishes a welcome, it leaves the open task list and sits under **Handled by AI**. If she cannot finish, it stays visible in **Needs You** with the reason.

---

## Manual — nothing named goes out on its own

**Promise on the card:** *AI suggests. You click to apply anything.*

**What happens to welcomes.** Aime does **not** write the letter and does **not** send it. The Automated welcome task stays open with:

> This deal is on Manual, so the AI will not send this email or complete this task on its own. Switch the deal off Manual, or complete it yourself.

There is no ready draft sitting in Email review from this path. The person on the file sends the welcome themselves (the ordinary **Email transaction party** / Send & complete flow), or they switch the deal (or the workspace) off Manual so Aime can pick the task up again.

**Hourly tick.** The hold is re-checked every pass. If someone later pins the deal to Assisted or Autopilot, the next run uses that new rule. Manual is a send kill-switch, not a diagnosis that has to be cleared by hand.

**What does not change.** Routine file work that is not a named letter still waits for a click on Manual. Waives, legal advice, and repair credits stay with the agent on every posture.

---

## Assisted — Aime writes it; a person taps Send

**Promise on the card:** *Routine work runs. Named emails are drafted — you tap Send.*

**What happens to welcomes.**

1. The same checks run as Autopilot (due date, party email, loan-officer contract, mailbox not required yet to *draft*).
2. Aime composes the library letter, addresses it to the captured party, attaches what the playbook allows, and stores it as a **ready-to-send** draft on the deal.
3. She does **not** put it on the wire.
4. The task stays open in **Needs You** as *tap to send*:

> This deal is on Assisted, so Aime drafted the email for you to tap Send. Autopilot is the setting that sends authorized emails without a tap.

5. The person taps **Send** (Needs You, Email review, or Send all ready). Delivery uses the deal owner’s mailbox, the same guarded send path Autopilot would have used (no AI disclosure, attachment honesty).
6. After a successful tap-send, that welcome task completes and moves to Handled by AI. The proof is the agent’s **Sent** folder, and the deal’s communication log at status `sent`.

**Hourly tick.** Assisted does not compose a second draft of the same welcome. The ready letter waits. If the deal is later switched to Autopilot, the next run may send that letter without another tap.

**Library send off.** If hourly library send is off for the workspace, Assisted behaves like a hold: the welcome waits with the library-send-off reason until an admin turns the switch on (after a mailbox is connected). No draft is produced on that hold.

**What you will not see.** A letter in the client’s inbox, or in the agent Sent folder, until someone taps Send. The draft in Email review / Needs You is the letter; it has not gone out yet.

---

## Autopilot — authorized welcomes send without a tap

**Promise on the card:** *Authorized emails send when confidence is high enough. No tap.*

**What “authorized” means here.** The four welcome letters are on the named playbook. Autopilot may send those (and the other named playbook letters: title order, confirm title, pending reminder, and — when the workspace flag is on — inspection response reminders). Every other email is still drafted for a tap. Waives and legal stay with the agent.

**What happens to welcomes.**

1. Same guards as Assisted (Active deal, due, party email, required docs for the loan-officer letter, not stale).
2. Aime composes the same library letter into a draft.
3. Because the deal (or the workspace it follows) is Autopilot **and** library send is on, she sends it immediately through the deal owner’s mailbox. No one taps Send.
4. The welcome task completes and hides under Handled by AI.

**Confidence.** These bodies are the library template filled with deal facts, not an LLM draft. The Autopilot confidence gate applies to other mail. A welcome still stops if a hard stop fires (no recipient, missing purchase agreement on the lender letter, dead mailbox, signature incomplete, mandatory-review language). Unclear or conflicting **contract dates** are a different setting (You confirm vs Trusted) and do not block the welcome letter.

**Mailbox.** Send uses the deal owner’s connected account, in order Gmail → Outlook. A lapsed Gmail grant is skipped so a healthy Outlook mailbox can still send. If every connected mailbox is dead, the task surfaces as reconnect-required and retries after Settings → Email & E-signature is healthy.

**Hourly tick / create.** This is the “sends themselves” behaviour: it runs at deal create when the welcome is due, and again on the scheduler if something was missing the first time (buyer email added later, contract uploaded for the lender letter, mailbox reconnected).

**Switching away.** Pin the deal to Assisted and later Autopilot letters wait for a tap. Pin it to Manual and they do not even draft. Follow the workspace uses the office card again.

---

## Side-by-side

| | Manual | Assisted | Autopilot |
|---|---|---|---|
| Aime writes the welcome | No | Yes | Yes |
| Letter sits as a ready draft | No | Yes — tap Send | Only if a hard stop blocked the send |
| Letter leaves the agent mailbox by itself | Never | Never | Yes, when the playbook and the guards pass |
| Welcome task after a clean run | Open — Needs You, *Manual* | Open — Needs You, *tap to send*, until someone sends | Completed — Handled by AI |
| How the human sends it | Compose/send from the task themselves | Send the prepared draft | Not required |
| Library send off | Hold | Hold — no draft | Hold — no send |
| Proof it went out | Agent Sent folder | Agent Sent folder after the tap | Agent Sent folder; task in Handled by AI |

---

## What you will see when it did not send

Needs You names the reason. The common ones for welcomes:

| Reason | Meaning |
|---|---|
| Manual | Deal or workspace is Manual. Switch it, or send it yourself. |
| Tap to send | Assisted. The draft is ready. Send it. |
| Hourly library send is off | Workspace switch. An admin turns it on after a mailbox is connected. |
| No … email is on file | Add the buyer / seller / co-op / lender on Contacts. |
| Needs the purchase agreement attached | Loan officer welcome only. Upload the contract. |
| Mailbox reconnect / no connected mailbox | Settings → Email & E-signature. |
| Overdue too long | More than 30 days past due. A person completes it or changes the date. |

A welcome that **did** send will not stay on the open list. Check **Handled by AI** on the Tasks tab, the deal’s Email / activity log, and the agent’s Sent folder. The task list alone is not proof — Sent is.

---

## Account welcome (not posture)

Separately, **hello@velvetelves.com** (SendGrid) sends *Welcome to Velvet Elves* when an **account** becomes usable: register without email confirmation, accept an invite, or the first sign-in after confirming. That letter is once per user. It is not the buyer/seller packet, it is not sent from the agent mailbox, and Manual / Assisted / Autopilot do not apply to it.

---

I am not treating this note as permission to reverse: one Aime, chat cannot send, Assisted does not send named emails on its own, unclear dates always wait, closing day is not the end of the file, Terminated not Closed, Dual as already set, no listing or buyer search in TME, no silent negotiation intelligence, and private chats are not training data.
