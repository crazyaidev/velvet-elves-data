# Aime and Your Transaction File — Questions

**Prepared for:** Jake
**Prepared by:** Jan Froben
**Date:** August 17, 2026
**About:** How Aime should work a live transaction file
**What I need from you:** 8 answers (tick the boxes in this doc)

---

## Before you start

I have read your AI architecture and Audri’s answers. I am not re-asking anything already decided.

This doc is only the file-logic questions that still change what an agent, buyer, or seller experiences. Tick a box under each question. If the recommendation is wrong, use **Different** and write the rule you want.

Already decided — not in this doc: automatic letters signed as Aime; new offices start on Manual; inspection *reminders* may send and inspection *negotiation* waits for you; every person in a role is on that email; assigned TCs can work that file operationally; delayed auto-send is deferred.

---

## At a glance

| # | Question | Blocking? | My recommendation |
| --- | --- | --- | --- |
| 1 | The word Autopilot is used for two different things. What should agents see? | No | Keep **Manual** / **Assisted** for the live file. Do not use Autopilot for intake and the live file. Call intake **Fast intake**. |
| 2 | After the current named letters, which emails may leave without a tap? | Yes | Do not guess. Add only the letters you list below, in that order. |
| 3 | Buyer / seller closing-information email: attach the Closing Disclosure? | Yes | No. The lender sends the CD. |
| 4 | Should buyers and sellers talk to Aime in this phase? | Yes | Not in this phase. They keep asking the team. Aime may give status and next steps later. Legal and “should I…?” always go to the agent. |
| 5 | After closing day, is the file still active until post-closing work is done? | Yes | Yes. Closing day is not the end of the file. |
| 6 | If the deal falls through, what should Aime do? | Yes | Stop automatic mail. Keep the history. Treat it as failed, not closed. Do not start listing or marketing. |
| 7 | A later signed amendment changes a date. Who confirms it? | Yes | Aime shows old date vs new date. You confirm, unless the language is explicit, complete, and non-conflicting **and** the file is on Autopilot. Fuzzy always waits. |
| 8 | On a cash file, who (if anyone) gets “Appraisal Ordered”? | Yes | Do not email a client about an appraisal on a cash deal. Make it an agent reminder, or do not create the task. |

---

### Question 1 — Autopilot currently means two different things

**What I found.** When you drop a contract in, Autopilot only means “the read is confident enough to skip extra confirming.” It does **not** mean Aime will email anyone.

On the live file, Autopilot means drafts arrive ready for one tap, and the named welcome / title letters may send on their own. You still tap Send on everything else.

Agents will mix these up if both are called Autopilot.

**Why it matters.** This is a label, not a new behavior. The two actions stay separate either way.

**What I suggest.** Keep **Manual** (you click) and **Assisted** (Aime does routine work; named letters may send; other mail is drafted for you) for the live file. Give the live-file third setting a name that still means “ready for one tap,” not “Aime sends everything.” Call the intake shortcut **Fast intake**, not Autopilot.

I am **not** proposing that Autopilot start moving dates or sending extra letters. That would be a different product.

**Your answer:**

- [ ] Keep Manual / Assisted / Autopilot for the live file, and call intake **Fast intake**
- [ ] Keep Autopilot for intake, and rename the live-file setting: ________________
- [ ] Different names: ________________________________

---

### Question 2 — Which letters may leave without a human tap?

**What I found.** Today, and only on Assisted or Autopilot, only when that person’s email is on the file and a mailbox is connected, these may send on their own:

- Buyer welcome
- Seller welcome
- Co-op agent welcome
- Loan officer welcome
- Order Title
- Confirm Title Order
- MLS pending reminder (to the agent, not a client)

Audri already approved inspection **reminders** (“the response deadline is tomorrow,” no repair language). She also wants more automatic letters, with the list still to come.

**Why it matters.** A letter we cannot unsend is not something I should invent.

**What I suggest.** I will add inspection reminders unless you say no. I will not add any other automatic letter until you name it here, in the order you want it.

**Your answer:**

- [ ] Stop after the current list plus inspection reminders
- [ ] Add these next, in this order: ________________________________
- [ ] Do not add inspection reminders either
- [ ] Different: ________________________________

---

### Question 3 — Closing-information emails and the Closing Disclosure

**What I found.** The buyer and seller closing-information tasks send closing and walkthrough details. The attachment sheet does not say whether the Closing Disclosure should ride along when it is on the file.

**Why it matters.** The lender is responsible for delivering the CD. Attaching the wrong CD, or an old one, is worse than attaching nothing.

**What I suggest.** Do not attach the Closing Disclosure. The lender handles it.

**Your answer:**

- [ ] No attachment — the lender handles the CD
- [ ] Attach the Closing Disclosure when it is on the file
- [ ] Different: ________________________________

---

### Question 4 — Should buyers and sellers talk to Aime in this phase?

**What I found.** Today they ask the team. Your architecture wants them to be able to ask Aime for status and next steps, and to route professional questions to the agent.

**Why it matters.** If Aime answers clients before that line is settled, she can wander into legal advice, negotiation, or speaking for a co-buyer.

**What I suggest.** In this phase, clients keep asking the team. Next phase, Aime may give **known** status and **known** next steps only. “Can I back out?”, waives, repairs, and anything like it always go to you.

**Your answer:**

- [ ] This phase: ask the team. Next phase: status and next steps only
- [ ] This phase: Aime may answer “where is my file?” (status only)
- [ ] Clients should not talk to Aime
- [ ] Different: ________________________________

---

### Question 5 — After closing day, is the file still active?

**What I found.** The file can look finished on closing day, while lockbox pickup, MLS to Sold, tax exemptions, and thank-yous are still open. Your architecture says closing does not finish Aime’s job.

**Why it matters.** If closing day hides those chores, they get skipped. If the file stays active forever, it never looks done.

**What I suggest.** Closing day is the closing event. The file stays active until the post-closing work is finished or you close it on purpose.

**Your answer:**

- [ ] Yes — the file stays active until post-closing work is done
- [ ] Closing day is the end. Post-closing is a reminder list only
- [ ] Different: ________________________________

---

### Question 6 — If the deal falls through, what should Aime do?

**What I found.** A dead deal can look the same as a closed deal. We are not building listing or marketing in this phase.

**Why it matters.** Automatic welcome or title letters must not keep going on a dead file. A failed deal should not be filed as if it closed.

**What I suggest.** Stop automatic letters. Keep the history (dates, decisions, documents, communication). Mark it failed / terminated, not closed. Leave you a note. Do not start listing or marketing.

**Your answer:**

- [ ] Yes — stop mail, keep history, mark failed, no listing behavior
- [ ] Also notify these parties: ________________________________
- [ ] Different: ________________________________

---

### Question 7 — A later amendment changes a date

**What I found.** At intake, you confirm the dates Aime reads from the contract. After that, a signed amendment that moves closing or inspection is just another document. The old dates can stay on the file until someone notices.

**Why it matters.** The later signed document is what controls. Aime should not overwrite the file in the dark, and should not ignore the amendment.

**What I suggest.** Aime prepares “the contract used to say X; this later signed document says Y.” On Manual and Assisted, you confirm before the new date is official. On Autopilot, she may apply it **only** if the language is explicit, complete, and does not conflict with another document. If anything is fuzzy, she waits.

**Your answer:**

- [ ] Always wait for me to confirm the new date
- [ ] Confirm on Manual and Assisted; on Autopilot, apply it only when the amendment is explicit and does not conflict
- [ ] If the amendment is explicit, apply it on any setting
- [ ] Different: ________________________________

---

### Question 8 — “Appraisal Ordered” on a cash file

**What I found.** The financed version of this task writes the loan officer. The cash version has no recipient. Audri said to write the represented client (buyer and/or seller).

**Why it matters.** On a cash file there is often no appraisal. Emailing a buyer or seller that an appraisal was ordered can look like a mistake.

**What I suggest.** Do not send that as a client email on a cash deal. Either it is an agent-only reminder, or the task does not belong on cash files.

**Your answer:**

- [ ] Agent-only reminder on cash files — no client email
- [ ] Do not create this task on cash files
- [ ] Email the represented client, as Audri said
- [ ] Different: ________________________________
