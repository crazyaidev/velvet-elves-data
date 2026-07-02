# How We Process Transactions - The Working Method

**The question this answers:** "How are we looking to actually start using the system to process transactions?"
**In one sentence:** A deal is created from the signed contract in the AI Wizard, then processed day to day on its own transaction page, where the AI agent watches the deal, flags what needs attention, and does routine work for you with your approval on every change.
**Also covered:** a brief outlook on where transaction processing develops next
**Written by:** Jan
**Date:** July 2, 2026

---

## The method at a glance

Processing a transaction in the system is three steps:

1. **Create the deal from the contract.** Upload the signed contract; the AI Wizard reads it, builds the full task plan from your master task list, and you approve it. A few minutes.
2. **Process the deal on its transaction page.** Every deal has one page with everything on it: deadlines, the document checklist, files, tasks, people, emails, and history. The AI agent sits on that page and works the deal with you. This is where the day-to-day processing happens, and most of this document describes it.
3. **Close it.** When a date or a term changes you update one fact and confirm the recomputed deadlines; when the deal is done you set its status to Closed and it leaves your active list.

---

## Step 1 - Create the deal from the contract

Click **"+ New Transaction"** (always in the top bar) and drag in the signed contract with any counters and addenda. The wizard then walks five short screens:

1. **Upload** - the AI reads the whole package and works out which document controls each term (a counter beats the contract, an amendment beats both).
2. **Review details** - every fact it pulled (property, parties, price, dates, deal specifics) shown next to the contract itself. Each AI-read value links to the exact clause it came from; anything uncertain is highlighted; anything not found is left blank and asked for.
3. **Timeline** - the deal's deadlines in order, each showing how it was counted (for example "10 days after acceptance").
4. **Checklist** - the document checklist this deal must satisfy.
5. **Tasks & create** - the complete proposed task list, grouped by milestone, each task with its due date, owner, and why it is included. Untick what you do not want, then click **"Approve & Create"**.

The list you approve is exactly the list that gets created, and the tasks come only from your master task list; the AI never invents tasks.

---

## Step 2 - Process the deal on its transaction page

Every deal lives at one page you reach by clicking it in Active Transactions. The page has a header with the property, the key dates, and a status pill, then a row of tabs:

| Tab | What you do there |
|---|---|
| Timeline | The deal's deadlines in order; editing a core date shows a preview of every deadline that would move before anything changes |
| Compliance | The document checklist: what is uploaded, what is missing, what was waived and why |
| Documents | The deal's files, with upload, and e-signature status |
| Tasks | The task list, grouped Overdue / Due Today / Upcoming / Completed; one click changes a status |
| People | Everyone on the deal (buyer, seller, agents, lender, title), with their contact details |
| Email | The deal's correspondence: inbound mail, sent mail, and AI drafts waiting for your review |
| Activity | The audit trail: every change, who made it, and when |

Daily processing is simple: you start in **My Task Queue** (one list of your tasks across all deals, urgent first), and you open a deal's page when you need its full picture. On the page, the AI agent is your working partner.

---

## The AI agent on the transaction page

On a wide screen the agent is a panel on the right of the transaction page, titled **"Velvet Elves AI - Your deal assistant"**; on a narrow screen it is the **Agent** tab. It has three jobs: it **watches** the deal, it **answers** questions about it, and it **does** routine work for you. Each job has firm rules, described below exactly as they are built.

### It watches the deal

At the top of the panel is an **AI suggestions** block with a one-line summary, for example "1 blocker · 2 to review · 1 draft waiting · 4 due this week", or "Nothing needs you right now" when the deal is clean. Under it are suggestion cards, each color-coded by severity (blocker, warning, or watch).

These findings do not come from AI guesswork. They come from a fixed set of checks that read the deal's actual records, so the panel can never contradict the tabs next to it. The checks are:

1. **Wrong document attached** - a checklist item looks satisfied, but the attached file reads as a different document type (the most dangerous case, because it looks done).
2. **Required document missing** - overdue, or due within the next 7 days.
3. **Overdue tasks** and **blocked tasks** (waiting on an upstream step).
4. **An AI email draft waiting for your review.**
5. **An inbound email that may need a reply** (nothing has gone out since it arrived).
6. **A person on the deal with no email on file** (so requests cannot reach them).
7. **A document still out for e-signature.**
8. **A deadline that lands after the closing date.**
9. **Closing readiness** - inside the last 14 days before closing, a summary card: "Closing in 9 days with 1 blocker and 2 warnings."

Each card names the exact items involved (clicking one jumps to it in the right tab) and, where a fix exists, offers it as a button: a missing document card offers **"Draft a request"**, a wrong-document card offers **"Detach & request correct doc"**. A **Scan** button re-runs all checks on demand.

### It answers questions

The panel is a chat, and the conversation is saved with the deal, so context is never lost between visits. You can ask anything about the deal ("what is still open with the lender?", "summarize this deal") and the answer is grounded strictly in this deal's own data. Three details worth knowing:

- **Precise references.** Type **#** to attach a specific document, task, deadline, checklist item, or email to your question, and **@** to reference a person on the deal. Every row in the Tasks, Compliance, and Documents tabs also has a small sparkle button ("Ask AI about this") that drops that exact item into the chat.
- **Key dates get exact answers.** A question about the closing date is answered from the stored dates in a fixed format, never reworded by the AI, so it is always right.
- **Honesty when it cannot help.** If the AI service is down it says so plainly. The panel's footer permanently reads: "The AI can make mistakes. Verify important information."

### It does routine work, with your approval on every change

You can tell the agent to do things, in plain words or via the **/** command menu (/scan, /readiness, /summarize, /draft-email, /request-document, /add-deadline, /move-date). What it can do today:

| You say | What the agent prepares |
|---|---|
| "Draft an email to the lender about the appraisal" | An email draft addressed to that person |
| "Request the septic inspection from the seller" | A document-request draft tied to that checklist item |
| "Add a task called order home warranty, due Friday" | A new task ("Friday" is resolved to the actual date in code, not by the AI) |
| "Add a deadline 10 days before closing" | A new deadline counted from the anchor date |
| "Move closing to 2026-05-27" | A date change with a full preview of every deadline that moves |
| "Set inspection to 10 days" | The same, for a contract term |
| "Mark the earnest money task completed" | A task status change |
| "Waive the HOA docs requirement because there is no HOA" | A checklist waiver, which always requires a stated reason |

Every one of these follows the same strict lifecycle, which is the heart of the safety design:

1. **The agent never writes anything directly.** Your request becomes a **proposal card** in the chat showing a preview of exactly what would change.
2. **You click Approve** (or Dismiss). Only then is the change applied, and it is applied through the same code paths as the buttons on the tabs, so an agent-made change behaves identically to a hand-made one.
3. **If the deal changed while a proposal sat open**, approving it does not blindly apply; the card refreshes with the message "The deal changed since this was proposed - review the refreshed preview."
4. **Most applied actions have an Undo button** on the card (undoing a created task marks it Skipped, undoing a waiver restores the requirement).
5. **Everything is audit-logged** - proposals approved, dismissed, and undone all land in the Activity tab with your name on them.

And some things are forbidden to the agent outright, hard-coded and not configurable: it can never **send** an email (it only writes drafts; sending happens in the Email tab, which itself states "Nothing sends without your approval"), never delete a document, never move a date without the cascade preview, and never make legal determinations. The AI's only creative role is understanding what you asked and wording explanations; every fact on a card comes from the deal's records, and every change goes through your click.

---

## Step 3 - Changes and closing

- **A date changes** (an addendum moves closing): update it on the Timeline tab or tell the agent; either way you see every affected deadline, old date next to new date, before confirming. Completed work is preserved.
- **The deal type changes** (financed becomes cash): the task list is updated to match, keeping completed tasks.
- **The deal closes:** set the status pill to **Closed**. The deal leaves your active lists, and everything on it (documents, tasks, emails, the agent conversation, the audit trail) stays on record.

---

## How we start

Three short stages, so no live deal is ever at risk:

1. **Confirm the task list** (one afternoon): you review the master task list with me and we adjust it to how you actually run deals, since every plan is built from it.
2. **Dry-run two or three closed deals** (a few days): we feed in their real contract packages and compare what the system builds against what actually happened. Nothing is emailed and the practice deals are deleted afterward.
3. **Pilot on the next two or three new contracts** (two to three weeks): real deals processed in the system, your current tracking kept in parallel as a safety net, with me reviewing every contract read. When they run clean, all new deals start in the system.

To begin I need your task list (any format) and two or three past contract packages as PDFs.

---

## Where this goes next

The method above is approval-first: the system reads, builds, and proposes, and you confirm every change. The next stage of development makes it more **proactive** (it notices and acts between your visits) and more **user-friendly** (fewer clicks from "something happened" to "it is handled"). In priority order:

1. **Process the inbox, not just the contract.** The system watches your connected mailbox, matches each deal-related email and attachment to the right transaction, and offers to start intake when a new contract arrives by mail, so nothing sits in your inbox waiting to be filed. The mailbox connection and the per-deal email surface are already live; the proactive matching loop on top of them is the build.
2. **Act on the calendar, not only on request.** The system drafts a task's email automatically when the task comes due, and sends you a short morning digest of everything due across your deals. Most of the drafting machinery is already built and waiting on the go-decision.
3. **Graduated autonomy.** Approval stays the default, and you can then mark specific routine actions as "always approve" so they run themselves from that point on, with the same preview, undo, and audit trail, so the time saved never costs you control.
4. **State-aware processing in all 50 states.** The five decisions you made are being built in now: the required who-orders-title answer, no invented deadlines, the cash appraisal election, exact day counting, and real attorney-state workflows. Deals then generate correctly for the state they are in, not just generically.
5. **Round out the circle around the deal.** A polished progress view your client can follow on every deal, closing analytics across deals, and the form library filling documents with contract data and routing them straight into e-signature.

The direction in one sentence: evolve from a system that answers when asked into one that notices, proposes, and, where you allow it, acts on its own, while keeping the approval-first discipline that makes it trustworthy enough to run real closings.
