# Transaction Processing & Workflow Automation - How the System Works Today, and Decisions We Need From You

**Date:** July 10, 2026
**Revised:** July 10, 2026 - reflects the redesigned Needs You page and the final placement of the Run now control
**Audience:** Jake (product owner) and the testing team
**Prepared by:** Jan
**Status:** Describes the software as it is actually built and running today. Every behavior in this document was verified in the live system before writing.

---

This document has three parts. Part 1 walks through the life of a deal in the platform, from dropping in a contract to closing day. Part 2 explains the new workflow automation system: what the AI now does on its own, what it never does, and where you control it. Part 3 is a list of decisions we need from you, each with enough background to answer it without a follow-up call.

Wherever a screen is mentioned, the exact click path is shown like this: **Left sidebar → Workflow → Needs You**.

---

## Part 1 - The life of a deal

A deal moves through three stages: you start it, the system builds its plan, and then the deal runs day to day. Here is each stage as a user experiences it.

### Stage 1: Starting a deal (the New Transaction wizard)

**Where:** the orange **+ New Transaction** button, top-right corner of every page.

1. **Drop in the paperwork.** Drag the purchase agreement (plus any counters, amendments, or disclosures) into the upload area. You can also skip the AI entirely and type everything by hand; the "enter details manually" option is always there.
2. **The AI reads the whole packet at once.** It does not read each file in isolation. It reads everything together, so a counter offer that changes the price wins over the original agreement, exactly the way a person would resolve it. It reads checked boxes (who orders title, financing type), finds the deadline day-counts wherever they appear, and treats a blank or "N/A" section as a no, never a yes.
3. **It double-checks itself.** A second, independent AI pass re-reads the packet and compares answers on the critical facts: address, price, closing date, acceptance date, buyer and seller names, signatures. If the two reads disagree on anything, the wizard flags it for you instead of guessing. Every important value also carries a "show me where" link that jumps to the exact page and line in the document it came from.
4. **You review in three steps.** The wizard walks Upload → Review details → Documents. It only asks about things it could not read; a decision like "who orders title?" is a one-click choice, not a form.
5. **Clean packets take the fast path.** When a packet is fully signed and the AI's confidence clears the bar you set, the wizard compresses to a single Confirm screen: check the dates, click Create, done.

### Stage 2: What gets created the moment you click Create

The instant the deal exists, the system builds its whole working plan. None of this is AI improvisation; it is your playbook applied mechanically:

- **The task list.** Built from the task playbook for the deal type (buy or sell, financed or cash). Conditional tasks appear only when they apply: HOA tasks only if there is an HOA, "Order title" only if your side orders it, "Confirm title order" if the other side does.
- **The deadlines.** Every date is computed from the contract's anchor dates (acceptance and closing) using the contract's own day counts. Per your earlier decision, a deadline that lands on a weekend or holiday stays exactly where the count puts it; the system never quietly moves a deadline later.
- **The document checklist.** The compliance list of documents this deal must collect, each with its due date. If you removed an item in the wizard, it is recorded as waived, never silently deleted.
- **The people.** Buyers, sellers, agents, lender, and title contacts from the contract, ready to reuse.

One rule ties this together: **what you saw in the wizard preview is exactly what gets created.** The preview and the creation run the same engine, so there are no surprises after the click.

### Stage 3: Running the deal day to day (the deal workspace)

**Where:** **Left sidebar → Deals → Active Transactions**, then click any deal.

The workspace is one screen with the AI assistant on the left and tabs on the right:

- **Timeline** - every date on the deal: contract dates, contingency deadlines, and custom deadlines, each showing where it came from ("10 days after acceptance", "from the contract, page 3").
- **Compliance** - the document checklist: what is in, what is missing, what is waived.
- **Documents** - every file on the deal; drag a new file anywhere on the page to add it.
- **Tasks** - the working task list, with due dates and a checkbox per task to auto-draft its email (more on this in Part 2).
- **People** - everyone on the deal; service providers can be saved to your vendor directory in one click.
- **Activity** - the full history of everything that happened, who did it, and when.
- **Email** - the deal's email: AI drafts waiting for review, sent mail, and the inbound thread.

Two behaviors worth calling out:

- **Move one date, everything moves with you.** Change the closing date and the system shows a preview first: "these 14 deadlines will move, these 3 will not (already completed, or pinned)". You approve it, and there is an Undo if you change your mind. Deadlines never move themselves.
- **Unanswered decisions surface as banners.** If a deal is missing a decision that gates tasks (for example "who orders title?"), a banner at the top of the workspace asks it with one-click answer buttons. Answering it creates the right tasks immediately.

---

## Part 2 - The workflow automation system

This is the new layer. The goal: you set one dial, everything routine happens on its own, and the small number of things that genuinely need a person collapse into one list you can clear with a few clicks, even from your phone.

### One dial: the Automation posture

**Where (workspace default):** click your name in the bottom-left corner → **Settings → AI & Automation**. The posture is the first thing on the page: three cards, one click, Save.

**Where (per deal):** open any deal; the **Manual / Assisted / Autopilot** switch sits right under the deal's name. Any single deal can differ from your workspace default (a small orange dot marks it as custom).

| Posture | What runs on its own | What waits for you |
|---------|----------------------|--------------------|
| **Manual** | Nothing. The AI still suggests, but every suggestion waits for your click. | Everything |
| **Assisted** (recommended) | Safe, reversible actions: adding tasks and deadlines, advancing task status, re-labeling documents. Routine emails are drafted automatically when their task comes due and wait in your review queue. | Every email send, every waived checklist item, every date change, anything unusual |
| **Autopilot** | Everything in Assisted, plus the drafted emails arrive pre-approved ("Ready"), so sending the day's mail is one tap on "Send all ready". | The send tap itself, waives, date changes, legal judgment |

The posture is a real control, not a label. A deal switched to Manual genuinely stops the AI from applying anything on that deal, even if the rest of your workspace runs on Autopilot.

**Important rollout note:** every workspace starts on **Manual**. Nothing about your team's current experience changes until an admin deliberately picks Assisted or Autopilot on the settings page.

### The safety rules that never change

These hold at every posture, on every deal, and no setting can override them:

- **No email ever leaves without a person's tap.** The AI drafts and can pre-approve; a human always sends. (Part 3, Question 3 asks whether you want to change this in one narrow case.)
- **Deadlines never move themselves.** Date changes always go through the preview-and-approve flow.
- **Waiving a checklist item, legal decisions, and releasing documents are always human.**
- **Everything the AI applies on its own is reversible.** One click of Undo puts it back.

### Needs You: the one list of things waiting on a person

**Where:** **Left sidebar → Workflow → Needs You** (the count badge shows how many items are waiting across all your deals).

Instead of hunting through deals for what needs attention, everything lands here. The page is built in the same visual language as My Task Queue, top to bottom:

- **A briefing banner** summarizes the whole queue in one sentence ("1 email is ready to send, 1 proposal to approve, 1 decision to make") and carries the two batch buttons: **"Send all ready"** (with a confirmation that names the recipients) and **"Approve all safe"**. Only safe, reversible actions are ever included in the batch; waives and date changes always stay individual, and the banner says so.
- **Four counters** act as one-click filters: **Ready to send**, **To approve**, **To review**, **To decide**. Click one to see just that kind; click again to clear. A search box next to them finds items by name, deal, or recipient.
- **Items are grouped by deal.** Each deal gets its own card headed by the property address, a count, and an **Open deal** button that jumps straight to that deal's workspace.

Every row tells you what it is at a glance: a colored type label, the AI's confidence where it applies ("AI 95%"), who an email is addressed to, and how long the item has been waiting. **Click any row to expand it** for the full picture before acting:

- An **email that is ready** expands to show the message preview, the recipient list, the AI's confidence, and a reminder that nothing sends until you tap Send. A **Send** button sits right on the row.
- An **AI proposal** expands to show exactly what will happen if you approve, why the AI suggests it, and whether it is reversible with one click of Undo. An **Approve** button sits on the row.
- A **draft to review** shows its preview inline and links to the full review screen with one click.
- An **open decision** expands to answer cards that explain each choice (for example "Buyer orders title: your side - an Order Title task will be created"). Picking one creates the right tasks immediately.

When the list is empty you see exactly that: "Nothing needs you right now."

One thing this page deliberately does **not** have: a button to trigger the automation. Needs You is where the automation's output lands; the trigger and health check live on the settings page (next section), so each screen has one job.

### Routine emails, end to end

1. **Which tasks get an email?** On Assisted or Autopilot, any task whose recipient is a person on the deal (buyer, seller, co-op agent, loan officer, title) is automatically marked for email drafting. You can flip any individual task's checkbox on the deal's **Tasks** tab: "Auto-draft the email when due (review before send)."
2. **When the task comes due,** the system writes the email for you: grounded in the deal's real facts, in your chosen voice, addressed to the right person, with you copied. It never invents facts; anything it was unsure about is flagged for the reviewer.
3. **Where drafts wait:** **Left sidebar → Intelligence → AI Email Review** (all deals), or the deal's **Email** tab (that deal only). One draft per task per due date, never duplicates.
4. **Sending:** on Assisted you review and click send per email. On Autopilot, drafts arrive pre-approved and both the deal's Email tab and the Needs You page offer **"Send all ready"**. Either way, a person taps send.

### Watching the AI work (and undoing it)

**Where:** open a deal → **Activity** tab → click the **Automation** chip.

This lens shows only what ran without a click, in plain language: "Advanced 'Order title' to In progress", "Drafted email: Welcome to your home purchase at 412 Harvest Lane". Anything reversible has an **Undo** button right on the row. Everything a person approved lives in the normal History view, so the two are never mixed up.

### Proving the automation is running

**Where:** **Settings → AI & Automation**, top of the page. This is the only place the trigger lives, by design.

A status chip shows "Automation active, last run 12 minutes ago" in green, or turns amber with "Automation hasn't run recently" if the background schedule has stalled. Next to it, a **Run now** button (admins only) runs the whole cycle immediately and reports what it did ("Drafted 3 emails"). It is safe to click repeatedly: it only drafts and pre-approves, never sends, and it can never create duplicate drafts for the same task. Testers never have to wait for the clock or take anyone's word for it.

---

## Part 3 - Decisions we need from you

Each question below includes the background needed to answer it. None of them block what is already built; they shape defaults, naming, and the one remaining feature that is deliberately unbuilt.

### Question 1: What should new customers start on: Manual or Assisted?

**Background.** Today every workspace starts on Manual: the AI suggests but touches nothing until an admin visits Settings → AI & Automation and picks a posture. That is the cautious choice: nobody's behavior changes without an explicit opt-in. The alternative is to start new sign-ups on Assisted, so the product feels automated from day one; the Assisted card is already labeled "Recommended" either way.

**The trade-off.** Manual-by-default means some customers may never discover the automation and conclude the product is passive. Assisted-by-default means a brand-new user's first deal starts drafting emails into their review queue before they have formed a mental model of the system (nothing sends by itself either way).

**My recommendation:** keep existing workspaces on Manual, but start newly created workspaces on Assisted, and show a one-time "here is what runs on its own, change it here" note on their first deal.

### Question 2: Naming: is "Autopilot" the right word, used this way?

**Background.** The word Autopilot now appears in two places, and possibly a third: (a) the wizard's fast path when a clean, signed contract skips straight to Confirm; (b) the highest automation posture; (c) if Question 3 is approved, the future "actually send by itself" email option. All three are the same brand promise at different depths, so the shared word can feel coherent, or it can confuse ("I enabled Autopilot, why did the wizard not fast-path?").

**Options.**
- Keep **Autopilot** for the posture (my preference: it is the word a user reaches for), call the Question 3 feature **"Full-send Autopilot"**, and leave the wizard's banner as is.
- Or rename the posture to **"Hands-off"** so Autopilot only ever means the wizard fast path.

**Needed before:** we freeze the copy on the settings page and the deal header.

### Question 3: Should we build "Full-send Autopilot" (the AI actually sends, with a hold window)?

**Background.** Today the AI never sends an email; a person always taps. There is one designed-but-unbuilt exception on the table: when a client emails a routine factual question ("what is our closing date?") and the AI's answer is fully grounded in the file with very high confidence, the reply could send itself, with these guardrails already designed:

- Off by default; a per-workspace opt-in with plain-language warning copy.
- Limited to grounded factual replies and document delivery, nothing else.
- Every auto-send waits on screen with a visible countdown (default 5 minutes) and a prominent **"Hold it"** button that turns it back into a normal draft.
- Always carries the AI disclaimer, is clearly labeled auto-sent in the log, and is fully audited.

**What we need from you:** a yes/no on building this, and if yes, whether the 5-minute hold window feels right. If no, everything else in this document still stands; the current one-tap "Send all ready" remains the ceiling.

### Question 4: Which recipients should routine auto-drafted emails cover by default?

**Background.** When a posture turns email drafting on, it currently applies to tasks addressed to: **Buyer, Seller, Co-op Agent, Loan Officer, Title**. That includes client-facing mail (buyer and seller), not just professional-to-professional coordination. Every draft is still reviewed or explicitly batch-sent by a person, but the question is what the default should reach.

**Options.**
- Keep all five (my recommendation: the buyer welcome and update emails are the most valuable time-savers).
- Or default to professionals only (Co-op Agent, Loan Officer, Title), and let each office turn client-facing drafting on per deal via the task checkboxes.

### Question 5: Is the "Approve all safe" batch list right?

**Background.** The Needs You page's "Approve all safe" button will only ever batch-approve these action types: add a task, add a deadline, change a task's status, toggle a task's auto-email, draft an email, draft a document request, re-label a document. Everything on that list is reversible with one click. Waiving checklist items, adopting a different document type, moving dates, and anything the AI itself flagged as uncertain are excluded and always stay individual.

**What we need from you:** does that boundary match your comfort level? Anything on the list you would pull out, or anything excluded you would add?

### Question 6: Where should "Needs You" sit in the daily routine?

**Background.** Needs You currently lives in the left sidebar under Workflow, above My Task Queue, with a live count badge. Separately, Audri has asked for the Transactions page to be radically simplified ("users should only see where the transaction is and what is coming up next"). The deal header already shows a line like "Autopilot: 6 handled today, 2 need you", and the "need you" part links straight into the queue.

**Options.**
- Keep Needs You as a sidebar destination (current state).
- Make it the centerpiece of the redesigned dashboard or Transactions page, so the daily routine becomes: open the app, clear Needs You, done.
- Both: keep the sidebar entry and feature the same list on the redesigned landing page.

**Why it matters now:** we are about to design the new Transactions page, and this decision shapes it.

### Question 7: When should the routine emails be drafted: continuously, or in a morning batch?

**Background.** Today the background cycle runs every hour: any task that has come due gets its email drafted within the hour, around the clock. The alternative is a single daily batch at a set local time (for example 8:00 AM, like the morning digest), so a user opens the app each morning to the full day's drafts in one stack rather than a trickle.

**Trade-off.** Hourly means drafts are ready as early as possible and the queue never piles up; a morning batch matches how most agents actually process email and makes "Send all ready" a satisfying once-a-day ritual. (Sending is unaffected either way; this is only about when drafts appear.)

**My recommendation:** keep hourly drafting, since drafts waiting a few extra hours in a queue cost nothing, and revisit only if testers find the trickle noisy.

---

## Quick reference: where everything lives

| What | Click path |
|------|-----------|
| Start a deal | **+ New Transaction** (top-right, any page) |
| Workspace automation default | Your name (bottom-left) → **Settings → AI & Automation** |
| Per-deal automation switch | Open the deal → the **Manual / Assisted / Autopilot** switch under the deal name |
| Everything waiting on a person | **Left sidebar → Workflow → Needs You** |
| Email drafts, all deals | **Left sidebar → Intelligence → AI Email Review** |
| One deal's email + "Send all ready" | Open the deal → **Email** tab |
| Turn one task's email drafting on/off | Open the deal → **Tasks** tab → the checkbox under the task |
| What the AI did on its own (+ Undo) | Open the deal → **Activity** tab → **Automation** chip |
| Prove the automation is running | **Settings → AI & Automation** → status chip + **Run now** |
