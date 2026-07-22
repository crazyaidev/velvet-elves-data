# Transaction Processing Logic and Workflow - From Contract Upload to Closing Day

**Date:** July 14, 2026
**Audience:** Jake (product owner)
**Prepared by:** Jan
**Purpose:** A complete, step-by-step account of how the platform processes a transaction, from the moment a deal is created through everything that happens afterward, so we can discuss the core logic in detail. The AI Wizard and the automation system are covered in depth, a feature comparison against ListedKit is included, and the last section lists concrete improvement proposals I would like your feedback on.
**Sources:** Everything in Parts 1 through 6 describes the software as it is actually built and running today; I verified each behavior in the live system and its source code before writing it down. The ListedKit comparison is based on ListedKit's public website (listedkit.com, including the features and pricing pages) as of July 14, 2026.

---

Every screen I mention includes its direct URL so you can open it while reading. The production application lives at `https://app.velvetelves.com`; all URLs below are given from that base. Where a URL contains `<deal-id>`, open any deal and the browser shows the real value.

---

## Part 1 - The big picture

A transaction moves through three stages:

1. **Intake.** The New Transaction wizard collects the paperwork, the AI reads it, and you confirm the facts. URL: `https://app.velvetelves.com/transactions/new`
2. **Creation.** One click turns the confirmed facts into the full working plan: the task list, every deadline, the compliance document checklist, and the people on the deal.
3. **Day-to-day processing.** The deal runs in its workspace, where the automation system drafts and sends routine communications, advances tasks, and collapses everything that genuinely needs a person into one queue.

Four principles hold everywhere, and I treat them as rules of the system rather than features:

- **What you preview is exactly what gets created.** The wizard preview and the actual creation run the same deterministic engine. The AI proposes; fixed code decides dates and what is created. The AI never computes a deadline.
- **Every AI claim carries evidence.** Extracted values, proposed deadlines, and watch-outs keep a citation to the exact page and line of the contract they came from, for the life of the deal, so the workspace can always answer "why does this exist."
- **Honest degradation.** If any AI pass fails, the system falls back to the deterministic baseline and says so with a banner. A provider outage can never strand a transaction.
- **Everything is audited.** Creation, date changes, task changes, and every email are logged and visible on the deal's Activity tab.

---

## Part 2 - The AI Wizard, step by step

**Where:** the orange **+ New Transaction** button in the top-right corner of every page, or directly at `https://app.velvetelves.com/transactions/new`. The wizard is a full-screen workspace with a four-phase stepper across the top: **Upload**, **Contract Details**, **Contacts & Fees**, **Verification**.

### 2.1 Upload

You first choose which side you represent (Buyer, Seller, or Both), then drag in the paperwork: the purchase agreement plus any counters, amendments, and disclosures. Each file shows its own upload status, a multi-page PDF can be split into separate documents, and there is always an "enter details manually" escape hatch that skips the AI entirely.

### 2.2 What happens while the AI reads (the parsing pipeline)

When you click to start, the wizard shows a live progress timeline while the backend runs a multi-stage pipeline. This is the part I want you to understand well, because it is the foundation everything else stands on.

**Stage 1: Reading the pages (OCR).** Every page is read with Amazon Textract, including form fields, signatures, and checkboxes. Checkboxes get special treatment: Textract reports a checkbox separately from the sentence it belongs to, so I re-insert each one into the page text at its exact visual position as `[X]` or `[ ]`. That means a clause like "the parties agree that [ ] Seller [X] Buyer will select a title insurance company" reaches the AI as one readable sentence with the checked box in context. This is what makes "who orders title," financing type, and similar checked-box decisions reliable.

**Stage 2: Extraction, first pass.** The whole packet is read as one unit, not file by file, against a strict schema. The instructions encode real-estate rules, including:

- A later accepted counter or amendment overrides only the fields it actually changes; everything else still comes from the base agreement.
- A blank, "N/A," or unchecked section is a **no**, never a guess. The AI is forbidden from fabricating contingencies.
- A tax record, assessor page, or deed names the current owner, which is the seller. It may never be used as a source for buyer names.
- Read the box that is checked, never the first option listed.
- Deadline day-counts are searched for on every page, not just the obvious ones, and each one records whether the contract counts calendar or business days.

Every extracted value comes back with a **citation** (which document, which page, the exact snippet) and a confidence score.

**Stage 3: The independent double-check.** A second AI pass re-reads the same packet with a different prompt and compares answers on the critical facts: address, price, closing date, acceptance date, buyer names, seller names, and whether all parties signed. If the two reads disagree on anything, the wizard flags the packet for human review instead of picking a winner. A single-pass answer can never silently ship on a critical field.

**Stage 4: Intake Intelligence.** A third pass asks the AI only for what the standard plan cannot know: deal-specific deadlines, deal-specific checklist documents, coordination tasks, and watch-outs. Crucially, the AI returns **proposals with rules and citations, never finished dates**. Deterministic code then verifies each proposal: the citation must actually locate in the scanned text, dates must fall in a sane window around acceptance and closing, and a proposal that contradicts the standard plan becomes a blocking conflict for you to resolve rather than a silent overwrite. A proposal whose document is already uploaded is auto-accepted and auto-attached instead of asking you for something you already gave it.

**Signatures.** Whether the deal is fully executed is judged on the controlling chain, not just the base document. A countered purchase agreement plus a fully-signed counter offer counts as fully executed. A deterministic backstop corrects the AI if its own per-document inventory contradicts its packet-level answer.

**Multi-document conflicts.** For packets with several documents, a resolver flags which document controls, which are superseded, and which referenced documents (a counter offer #2 mentioned but not uploaded, for example) are missing. Each real gap is reported exactly once.

### 2.3 The Autopilot fast path

After a clean parse, the wizard checks whether the extraction cleared the confidence bar you configure (Settings, AI & Automation, Confidence gates) on every critical field, with all parties signed. If so, the journey compresses to the **Verification** screen: check the anchor dates, click Upload Transaction, done. Anything that did not clear the bar surfaces for one-click review. If not, the wizard walks the normal review path below.

### 2.4 Contract Details (stage 2)

Everything the contract says about the property and the deal, on one screen:

- **Property details.** The extracted address, with a "show me where" link on every value that opens the document viewer scrolled to the exact source line, text highlighted.
- **Deal type and pricing, key dates, financing, contingencies, terms and notes.** Price, earnest money, financing, the anchor dates, and every contingency. Day-count and date fields stay in sync: edit "14 days" and the date recomputes, edit the date and the count recomputes. The contract's own earnest-money delivery window (including whether it counts business days) rides through to the committed deadline. Cash deals ask whether the buyer elected an appraisal.
- **"Found in the contract - needs your eyes."** Anything the AI read at low confidence, or could not read at all, is flagged here as a chip that jumps to the field. Fixed decisions such as "who orders title" are one-click choices, never free typing, and a deal cannot be created while one of them is unanswered: the answer changes which tasks get generated.

### 2.5 Contacts & Fees (stage 3)

- **Contacts.** A card for every party: buyers, sellers, both agents, loan officer, title company, closing attorney, each with its citation. Cards pre-fill from your vendor directory when the AI-read name, email, or phone matches a vendor you already know, and your own agent card fills from your profile. Marking a deal FSBO is only offered when you represent the buyer, and the wizard warns you if the packet itself names a listing agent, since a represented seller is not a FSBO.
- **Fees.** Your professional fee and any transaction fee (a broker/team admin fee, separate from the app's own per-deal billing fee). Each is paid by the buyer, the seller, or both, and **each paying side carries its own amount and its own unit**, so a split can be "seller 2%, buyer $250". A fee the contract mentions shows as a read-only hint - the number is always yours to enter. The cards prefill from your last deal and are withheld from the deal until you confirm or edit them, so a stale number never rides through unseen.

A natural-language command bar is available throughout ("change the closing date to March 3," "add a buyer named..."), and every command previews its change before applying, with undo.

### 2.6 Verification (stage 4) - where the deal is created

The review hub, and the only place a deal is created:

- **The full summary:** every fact with its citation, grouped property / dates / financing / terms / parties / fees, each row with an Edit jump back to the stage that owns it.
- **The double-check panel** and the AI proposals (deadlines, checklist rows, tasks) to accept or dismiss.
- **The signature decision, scoped to your client.** If the packet is not fully signed, the wizard offers the action that fits *whose* signature is missing: your own client's side gets the e-signature queue; the **other** side gets "request the signed copy from the other agent," which becomes a real task addressed to the co-op agent rather than an e-signature sent to someone else's client. Referenced-but-missing documents (a Counter #2 the packet mentions but you don't have) offer the same one-click request.
- **A confirmation line and a full-width "Upload Transaction" button.** Nothing is created until you click it.

**The compliance checklist is no longer a step you walk.** It is still built for the deal and committed at creation, with your uploads auto-matched to their rows (the wizard never asks for a document you already gave it, matching by AI-detected type first, then by filename; a manual match always wins). Editing the checklist - add, attach, waive, request by email - now lives on the deal's **Compliance** tab in the workspace, where it stays useful for the life of the deal instead of only at intake.

Your work is saved continuously: a local draft plus a server-side draft, so you can resume on another device, and "Save draft" stores the deal as an Incomplete shell you can finish later.

### 2.6 If the AI is unavailable

The wizard says so honestly and runs "floor only": the standard plan still works, manual entry still works, and nothing pretends to be AI-verified. There is no silent fallback to a different AI provider; the provider is whichever one is deliberately configured.

---

## Part 3 - The moment of creation

Clicking **Upload Transaction** runs a precise sequence. The important property: the deterministic planner that generated the preview is re-run to produce the committed rows, so the preview and the database always agree.

1. **The transaction is created**, including the fees you entered and a record of the decisions you made on Verification (your signature choice, which roles the packet showed unsigned, and any missing documents you asked for). That record is what stops the automation from contradicting you an hour later - see Part 6.8. When billing is enabled, this is the single moment a deal is charged: one flat fee at creation, with team members always free. If the wallet is empty the wizard shows an in-flow paywall, sends you to Stripe, and finishes the exact same commit when you return. A failed creation is never charged.
2. **The people are saved.** Every buyer, seller, agent, lender, title contact, and attorney becomes a party on the deal. Each service provider is also silently added to your master vendor directory (matched by email, then phone, then company name), so the directory builds itself and future wizard runs pre-fill from it. Nobody is asked to "save vendors" mid-flow anymore.
3. **Welcome emails** are the agent's own Automated tasks, sent from your connected mailbox so replies land in your normal thread (Part 6.3). The platform does not send transaction introductions from its own address.
4. **FSBO invitation.** On a FSBO deal, the unrepresented seller receives a transaction-scoped invitation to a limited seller portal. The deal remains yours.
5. **Documents are linked** to the new deal, and the compliance checklist is committed, including waived rows and accepted AI rows with their citations, with your uploads already auto-matched to their rows.
6. **E-signature** is queued only if the packet was not fully signed, you chose to queue it, and a signature provider is connected.
7. **The full task plan is generated** (Part 4). Any "request from the other agent" action you accepted on Verification becomes a real task here: addressed to the co-op agent, due two days after acceptance, and tagged so the AI knows that ask already has an owner.
8. **Watch-outs are persisted** with their citations, so the workspace can show them for the life of the deal.

You land in the new deal's workspace, and a one-time line across the top tells you exactly what was built - "23 tasks (5 handled by AI) · 12 checklist items, 3 documents attached · Fees captured · 1 request to the other agent" - with every segment linking to the tab whose rows back that number. It is the receipt for what Verification promised, and it appears only on that first visit.

---

## Part 4 - The task engine (the deterministic heart)

This is where your task playbook becomes a live plan. There is deliberately **no AI creativity** in this engine; it applies the template library mechanically, and the same code produces the wizard preview and the committed tasks.

**Where the playbook lives:** `https://app.velvetelves.com/admin/task-templates` (your master task templates, per deal type, with conditions, day-counts, dependencies, recipients, and automation levels).

The engine, in order:

1. **Select templates for the deal type** (Buy or Sell, financed or cash; a dual-agency deal assembles both sides and de-duplicates).
2. **Evaluate each template's conditions.** HOA tasks appear only when the deal has an HOA. "Order Title" fires when your side orders title; "Confirm Title Order" fires when the other side does. The contract says "Buyer" or "Seller"; the engine translates that into "us" or "the other side" using which side you represent. A condition on a question that was never answered excludes the task rather than guessing, and the workspace then asks the question with a banner (Part 5).
3. **Dual-agency adjustments.** Consolidated task versions replace their two-sided siblings, and tasks that make no sense in dual agency (a co-op agent welcome, for example) are suppressed.
4. **State rules** add or remove state-specific tasks, such as statutory attorney-review items, only in verified states.
5. **Compute every date.** The two anchors are contract acceptance and closing. Every other date is derived: "closing minus 14 days," "10 days after acceptance," "3 days after the inspection task." A deadline the contract counts in business days skips weekends and federal holidays; everything else counts calendar days.
6. **Weekends and holidays.** Per your decision: a computed deadline that lands on a weekend or holiday **stays exactly where the count puts it**. The system never quietly moves a deadline later; hitting too early beats hitting late.
7. **Honesty about unknowns.** If an anchor date is missing, dependent tasks stay undated rather than being faked off today's date, and each one is surfaced as a warning.

Every task records why it exists ("Property has an HOA"), what its date is based on ("Closing - 14d"), who its recipient is (the Target column from your task matrix: buyer, seller, co-op agent, loan officer, title, or you), and its automation level from your playbook: **Automated**, **To Be Automated**, **AI Assisted**, or **Manual**. These levels are not labels; Part 6 describes exactly what the AI does with Automated tasks. To Be Automated rows deliberately stay visible in your list, since nothing executes them yet; hiding them would silently drop real work.

The compliance checklist (Part 2.5) is planned by the same machinery: same conditions, same anchors, same date arithmetic, with waived rows preserved as an audit record.

---

## Part 5 - Day to day: the Transaction Workspace

**Where:** `https://app.velvetelves.com/transactions` (Active Transactions), then any deal, which opens `https://app.velvetelves.com/transactions/<deal-id>`. Pending, closed, and all deals are one filter away (`/transactions?status=pending`, `?status=closed`, `?status=all`).

The workspace is one screen: the AI assistant pane beside a tabbed workbench. The tabs:

- **Timeline** - every date on the deal: contract dates, contingency deadlines, and custom deadlines, each showing its basis ("10 days after acceptance") and, for AI-proposed rows, the citation chip that jumps to the contract source.
- **Compliance** - the document checklist: what is in, what is missing, what is waived. A missing document can be requested by email in one click; the request becomes a reviewable draft, and nothing sends without approval.
- **Documents** - every file on the deal; drag a file anywhere to add it. New uploads are parsed and matched against the checklist.
- **Tasks** - the working task list. Tasks the AI handles are collapsed into their own "Handled by AI" group so your list shows only what is actually yours (more in Part 6).
- **People** - everyone on the deal, with vendor-directory integration.
- **Activity** - the full audited history, plus an Automation lens showing only what the AI did on its own, each row with Undo where applicable.
- **Email** - this deal's mail: drafts waiting for review, sent mail, and the inbound thread.

Behaviors worth understanding in detail:

- **Move one date, everything moves with you.** Change the closing date and the system first shows a preview: "these deadlines move, these do not (already completed, or pinned, or have no rule)." You approve, it applies, and an Undo chip reverses it. Completed tasks are history and are never touched. Deadlines never move themselves.
- **Unanswered decisions become banners.** If "who orders title" was never answered, a banner asks it with one-click options, and answering immediately creates the right tasks. Changing an answer, or even the whole deal type, retargets only the affected template tasks; anything you added manually is never touched.
- **Key milestone dates** (earnest money delivered, inspection response, appraisal expected, CD delivered, cleared to close) are recorded as the deal progresses, each edit audited.
- **Cross-deal views.** Your work across all deals lives in **My Task Queue** (`https://app.velvetelves.com/tasks/queue`), **All Documents** (`https://app.velvetelves.com/documents`), and the **Closing Calendar** (`https://app.velvetelves.com/calendar`). Closings and task deadlines can be pushed to a connected Google or Outlook calendar.
- **Closing out.** The deal moves Active to Completed to Closed, each transition audited, with an optional client-feedback prompt at closing. The transaction list exports to CSV, Excel, or PDF.

---

## Part 6 - The automation system in detail

This is the newest layer and the one I most want to walk through with you. The design goal: you set one dial, everything routine happens on its own, and the small number of things that genuinely need a person collapse into one list.

### 6.1 The posture dial: Manual, Assisted, Autopilot

**Workspace default:** `https://app.velvetelves.com/admin/confidence` (reached in the app via Settings, AI & Automation). The posture is the first section: three cards, one click, save. The same page holds the expert sections behind a small menu: AI provider, Email replies, Automation rules, and Confidence gates.

**Per deal:** the Manual / Assisted / Autopilot switch sits directly under the deal's name in the workspace header, with a "N handled today, M need you" line. Any single deal can differ from the workspace default; a deal switched to Manual genuinely stops the AI from applying anything there.

| Posture | Runs on its own | Waits for you |
|---------|-----------------|---------------|
| **Manual** | Nothing. The AI still suggests; every suggestion waits for your click. | Everything |
| **Assisted** (recommended) | Safe, reversible actions: adding tasks and deadlines, advancing task status, re-labeling documents. Routine emails are drafted when their task comes due and wait in review. | Every send, every waive, every date change |
| **Autopilot** | Everything in Assisted, plus drafts arrive pre-approved ("Ready"), so the day's mail is one tap on "Send all ready." | The send tap, waives, date changes, legal judgment |

Every workspace starts on Manual. Nothing changes for a team until an admin deliberately picks a posture.

### 6.2 The heartbeat, and proving it runs

A background cycle runs every hour. The AI & Automation page header always shows a live status chip ("Automation active, last run 12 minutes ago," or amber if the schedule stalled) and an admin-only **Run now** button that executes a full cycle immediately and reports what it did. Run now is safe to press repeatedly: it can never duplicate a draft for the same task.

### 6.3 Tasks the AI completes by itself (the task executor)

This is the July upgrade that came from your feedback, and it changes what "Automated" means. Previously the automation level from your task matrix was stored and displayed but nothing executed it, which is why testers saw overdue "Buyer Welcome" tasks. Now there is an executor with a fixed playbook, keyed by task name, that runs every task your playbook marks **Automated** end to end:

- **Buyer Welcome, Seller Welcome, Co-op Agent Welcome, Loan Officer Welcome:** the executor composes the library-template email, addresses it to the actual party captured on the deal, attaches the relevant documents (the controlling purchase agreement, counters, disclosures as applicable), sends it **through your own connected mailbox** so replies land in your normal thread, then marks the task complete.
- **Order Title / Confirm Title Order:** the title-side email with the contract attached, sent and completed the same way.
- **Review Documentation:** not an email but a verification: on every document parse the executor checks buyer and seller signatures from the extraction evidence. All signed means the task auto-completes with a note; anything unsigned prepares a document-request email to the co-op agent with the unsigned documents attached, kept as a draft for you to edit, because a chase email deserves a human look.
- **Pending Reminder:** emails you (the account holder) a summary of what is pending, then completes itself.

I want to be explicit about one thing: **these sends happen without a per-email tap.** That is a deliberate exception you asked for, and it applies only to tasks your playbook marks Automated. Everything else keeps the human-tap rule. The guardrails around the exception:

- Active deals only, and only tasks on the fixed playbook; the executor cannot invent an email.
- Recipients are only ever the parties captured on the deal, never looked up elsewhere.
- A task more than 30 days overdue is never auto-run (no surprise mail on stale deals).
- If the AI cannot proceed (no recipient email, missing document, unsigned paperwork), the task turns visible with an amber "AI needs you" badge, states the reason, and lands in Needs You. Once you fix the cause, the next cycle retries without ever double-sending.
- Every executed task is fully audited, and the sent email sits in the deal's Email tab like any other.

Tasks the AI is handling are hidden from your day-to-day lists (My Task Queue, dashboards, counts) and collapsed into a "Handled by AI" group on the deal's Tasks tab, so what you see is only what needs a person. The milestone timeline keeps the full set on purpose, so AI-completed milestones still advance the deal's progress dots. One operational note: the playbook switch that marks Review Documentation, Confirm Title Order, and Pending Reminder as Automated in the template library is a database update I still need to apply to the shared environment; the logic itself is complete and tested.

### 6.4 Completing any other task by email (the task email flow)

For every non-automated task, the Tasks tab and the transaction card offer "Complete this task." The dialog opens **pre-addressed to the task's designated recipient from your task matrix**: the buyer for a buyer task, the co-op agent for a co-op task, you for a self-reminder. All same-family contacts ride along (a title company's processors and closers are always included), the CC list follows the matrix, and the body is pre-written from the task's template or description. You can edit everything, switch the recipient to another transaction party, or take the AI's offer to send it as planned. "Send and complete task" does exactly that in one motion; "I'll handle it myself" backs out. The "next step" button on a transaction card opens this flow for the deal's next due task directly.

### 6.5 Routine email drafting and review

On Assisted or Autopilot, any task addressed to a person on the deal is marked for auto-drafting. When the task comes due, the hourly cycle writes the email: grounded in the deal's real facts, in your configured voice, addressed to the right person, with you copied. It never invents facts, and anything uncertain is flagged for the reviewer. One draft per task per due date, never duplicates.

Drafts wait in **AI Email Review** (`https://app.velvetelves.com/ai-emails`, all deals) and on the deal's Email tab (that deal only). On Assisted you review and send each one; on Autopilot they arrive pre-approved and "Send all ready" sends the day's stack in one confirmed tap. Inbound replies on deal threads land on the deal's Email tab, and the AI can draft a grounded reply for review. Outbound mail reads as normal correspondence from your mailbox; recipients are never told an AI drafted it.

### 6.6 Needs You: the one queue

**Where:** `https://app.velvetelves.com/needs-you` (left sidebar, Workflow group, with a live count badge).

Everything waiting on a person, across every deal, lands here:

- A briefing banner summarizes the queue in one sentence and carries the two batch buttons: **Send all ready** (confirming recipients by name) and **Approve all safe**. Only reversible actions are ever batchable; waives and date changes always stay individual, and the banner says so.
- Four counters filter by kind: Ready to send, To approve, To review, To decide. A search box finds items by name, deal, or recipient.
- Items group by deal, each card headed by the property address with an "Open deal" button.
- Every row expands in place: an email shows its full preview, recipients, and confidence before you tap Send; a proposal shows exactly what will happen and that it is undoable; a decision shows answer cards that explain each choice. "AI needs you" items from the task executor land here too, with their reason.

This page deliberately has no trigger button; it is where automation output lands. The trigger and health check live on the settings page, so each screen has one job.

### 6.7 The safety rules

At every posture, on every deal:

- Routine and client-facing drafts never send without a person's tap. The single exception is Part 6.3: playbook tasks you explicitly marked Automated.
- Deadlines never move themselves; date changes always go through preview-and-approve with undo.
- Waiving a checklist item, legal decisions, and releasing documents are always human.
- Everything the AI applies on its own is reversible and visible in the Automation lens.

### 6.8 The AI does not overrule what you decided at intake

The signature decision you make on Verification is stored with the deal, and the **Review Documentation** task (Part 6.3) reads it before it does anything. One ask has one owner:

| What you chose on Verification | What the AI does when documents are still unsigned |
|---|---|
| **Mark not required** | Closes the review with a note saying you marked signatures not required. No chase, ever. |
| **I'll handle signing later** | Keeps the finding visible so it is not lost, but drafts nothing. You asked it to hold off. |
| **Request the signed copy from the other agent** | Points at the task that already covers it ("your request task covers this") and drafts nothing. If you complete that task while documents are still unsigned, the normal chase resumes - a stalled ask is never silently dropped. |
| **Queue e-signature** | Waits on the envelope and reports its progress. |
| Nothing (you didn't answer), or a deal created outside the wizard | Unchanged from before: the AI drafts the request email for your review. |

One related correction: a document that is simply **out for e-signature** is never chased to the co-op agent on any deal. A pending envelope is our own channel in flight, not the other side's failure, so the AI reports it as "awaiting e-signature" instead of asking someone else's agent about your client's signature.

## Part 7 - Quick reference: where everything lives

| Surface | URL |
|---------|-----|
| Start a deal (AI Wizard) | `https://app.velvetelves.com/transactions/new` |
| Active Transactions | `https://app.velvetelves.com/transactions` |
| A deal's workspace | `https://app.velvetelves.com/transactions/<deal-id>` |
| Needs You (automation queue) | `https://app.velvetelves.com/needs-you` |
| My Task Queue | `https://app.velvetelves.com/tasks/queue` |
| All Documents | `https://app.velvetelves.com/documents` |
| Closing Calendar | `https://app.velvetelves.com/calendar` |
| AI Email Review | `https://app.velvetelves.com/ai-emails` |
| AI Suggestions | `https://app.velvetelves.com/ai-suggestions` |
| Vendor Directory | `https://app.velvetelves.com/vendors` |
| Analytics | `https://app.velvetelves.com/reports` |
| Settings hub | `https://app.velvetelves.com/settings` |
| AI & Automation (posture, provider, confidence, Run now) | `https://app.velvetelves.com/admin/confidence` |
| Task playbook (templates) | `https://app.velvetelves.com/admin/task-templates` |
| Client portal (what a client sees) | `https://app.velvetelves.com/client/home` |
| FSBO seller workspace | `https://app.velvetelves.com/fsbo` |
| Vendor portal | `https://app.velvetelves.com/portal/vendor` |

---

## Part 8 - Feature comparison: Velvet Elves vs. ListedKit

Based on ListedKit's public website (listedkit.com, features and pricing pages, July 14, 2026). Their help center blocks automated reading, so this reflects what they publicly claim; I note where a claim is theirs rather than something I have tested.

| Capability | ListedKit (public claims) | Velvet Elves (built today) |
|------------|---------------------------|-----------------------------|
| AI contract reading | Yes; "every state," CAR/TREC/custom forms, handwritten | Yes; any state, whole packet read as one unit, checked boxes read in context; handwriting depends on scan quality |
| Counters and amendments resolved against the base contract | Not publicly described | Yes; later accepted documents override only the fields they change, with a controlling-document resolver |
| Independent AI double-check of critical fields | Not publicly described | Yes; a second pass re-reads the packet, disagreements force human review |
| Click-to-source evidence | Yes; verify fields next to source text | Yes; per-field citations to page and line, kept for the life of the deal, not just at intake |
| Timeline and checklist generation | Yes; "state-aware," under 2 minutes | Yes; deterministic playbook engine, preview equals commit, business-day counting, explicit no-roll weekend policy |
| Firm-controlled task playbook | Positioned as "no templates, no setup" | Yes; master templates with conditions, dependencies, dual-agency handling, state rules, admin-governed |
| Compliance document checklist with waive audit | Checklist features publicly claimed | Yes; waived rows preserved as audit records, uploads auto-matched, never asks for what you gave it |
| Email drafting with human review | Yes; drafts, auto-replies, scheduled reminders | Yes; grounded drafts, review queue, batch "Send all ready," per-deal posture control |
| AI executes routine tasks end to end | Ava "handles" tasks (mechanics not public) | Yes; playbook-marked Automated tasks are emailed and completed by the AI with guardrails and full audit |
| One queue of what needs a person | "What is urgent today" across deals | Yes; Needs You with batch approve/send and per-item evidence |
| Files any inbound email to the right deal | Yes; flagship claim, by context | Partially; deal threads are filed, but brand-new unrelated inbound mail is not yet auto-filed (Proposal 1) |
| SMS access | Yes; ask Ava by text | No (Proposal 3) |
| Calendar sync | Yes; event per deadline, parties invited | Partially; closings and task deadlines push to connected Google/Outlook calendars, no party invites yet (Proposal 4) |
| Client portal for represented buyers/sellers | Not publicly offered | Yes; next steps, milestones, documents, invoices, agent info |
| FSBO seller workspace | Not publicly offered | Yes; invited, transaction-scoped seller portal |
| Vendor directory and vendor portal | Not publicly offered | Yes; self-building directory plus a scoped vendor portal |
| Attorney workspace | Yes; attorney solution advertised | Yes; attorney intake, queue, matter workspace, state rules |
| Payments, invoicing, commission payouts | Not publicly offered | Yes; invoices, client payment links, payouts |
| Multi-tenant white-label and platform administration | Not publicly offered | Yes; tenant branding, platform console, cost and AI-usage analytics |
| Audit trail | Not publicly detailed | Yes; every create, change, send, and AI action is logged and reviewable |
| Team roles | Super Admin / Admin / User, unlimited members | Yes; role-specific dashboards (agent, TC, team lead, attorney, admin), unlimited members free |
| Pricing model | $14.99 per credit, first free, credits never expire, unlimited members | Flat fee per transaction charged at creation, members free; the price point is still our open decision |
| Public proof (testimonials, state guides, public pricing) | Strong; 50-state guides, reviews, press | Weak so far; the marketing site is being built out and we have no public proof yet |

My reading of this chart: we are ahead on depth (verification, evidence, playbook control, portals, payments, auditability) and behind on three convenience surfaces that make ListedKit's demo feel magical: filing any inbound email to the right deal, SMS, and per-deadline calendar events with invited parties. Those three are exactly where I would invest next, and they are Proposals 1, 3, and 4 below.

---

## Part 9 - Proposed improvements (I need your feedback on these)

Each proposal says what I would build, why, and the specific decision I need from you. None of them block what is already running.

### Proposal 1: File every inbound email to the right deal

Today, replies on threads the system started are filed to their deal automatically. Mail that arrives cold (a lender emails you first, subject line "loan update") is not. I would add a filing pass: the AI matches inbound mail to a deal by the people on it, the property references, and prior threads, files what it is confident about, and puts the rest in a small "needs filing" list you can clear with one click each. This is ListedKit's flagship convenience and, in my view, our biggest gap for daily TC work.
**What I need from you:** a yes/no on priority, and whether auto-filing at high confidence is acceptable or whether every filing should be confirmed at first.

### Proposal 2: Full-send Autopilot for grounded replies, with a hold window

Designed but deliberately unbuilt. When a client asks a routine factual question ("what is our closing date?") and the AI's answer is fully grounded in the file with very high confidence, the reply could send itself with these guardrails: off by default per workspace, limited to grounded factual replies and document delivery, a visible countdown (default 5 minutes) with a "Hold it" button that turns it back into a draft, and full audit labeling.
**What I need from you:** build or not; if yes, whether 5 minutes is the right hold window.

### Proposal 3: SMS, in two directions

First, outbound: deadline reminders and task notifications by text to the parties who prefer it. Second, inbound: you text a question about a deal and get a grounded answer without opening the app. You have also mentioned a courtesy email to the co-op agent when we represent the buyer, with a sign-up pitch; I would fold that into the same outreach work.
**What I need from you:** whether SMS matters to your testers now or after launch, and which direction (outbound reminders vs. ask-by-text) comes first.

### Proposal 4: A calendar event for every deadline, with invited parties

Today closings and task deadlines push to your connected calendar as your events. ListedKit claims an event per deadline with the relevant parties invited. I would extend our push so each deadline event can carry invitees from the deal's people, per your rules about which parties see which deadlines.
**What I need from you:** whether party-invited events are desirable (some coordinators consider their calendar private), and if so, which deadline types should invite whom by default.

### Proposal 5: Default posture for new workspaces

Everything starts on Manual today; the automation is invisible until an admin turns it on. I recommend keeping existing workspaces on Manual but starting newly created workspaces on Assisted, with a one-time "here is what runs on its own, change it here" note on their first deal. Nothing sends by itself either way.
**What I need from you:** confirm Assisted-by-default for new sign-ups, or keep Manual everywhere.

### Proposal 6: Drafting cadence: hourly or a morning batch

Drafts are written within the hour their task comes due, around the clock. The alternative is one daily batch at a set local time (8:00 AM), so the morning routine becomes: open Needs You, review the stack, one tap. My recommendation is to keep hourly (drafts waiting in a queue cost nothing) and revisit only if testers find the trickle noisy.
**What I need from you:** confirm hourly, or pick a batch hour.

### Proposal 7: The word "Autopilot" is doing three jobs

It names the wizard's fast path for clean signed packets, the highest automation posture, and (if Proposal 2 is approved) the future full-send option. My preference: keep Autopilot for the posture, call Proposal 2 "Full-send Autopilot," and leave the wizard banner as is. The alternative is renaming the posture ("Hands-off") so Autopilot only ever means the wizard fast path.
**What I need from you:** a naming decision before I freeze the copy on the settings page and deal header.

### Proposal 8: Two intake conveniences that are currently switched off

The wizard's street-address autocomplete is fully wired for Google Places, but I switched it off because Google is rejecting our current API key (the Places API is not enabled for it, and the key's website restrictions do not cover our domain); rather than show Google's error inside the address field, the street input now works as a plain field with recent-address suggestions. Turning it back on is a Google Cloud configuration fix plus a small per-lookup cost, not a build. Separately, the "AI search" button on the Missing Info step is a stub that returns nothing, because no real public-record data source is connected yet.
**What I need from you:** for the autocomplete, confirm I should fix the key's configuration and turn it on. For the AI search, build it against a real data source later or remove the button for now; my recommendation is to remove it until there is a real source, so nothing on the screen is decorative.

### Proposal 9: Public proof

Not a product feature, but it shows up in every comparison: ListedKit has public pricing, a first-transaction-free offer, 50-state guide content, testimonials, and press. Once you settle our per-transaction price, I can put pricing and a first-deal-free offer on the marketing site, and we should start collecting tester quotes now so the site has real voices at launch.
**What I need from you:** the price point, and whether first-transaction-free fits your business model.

---

That is the whole machine as it stands today, end to end. Parts 2, 3, 4, and 6 are the ones I would most like to walk through together, and the nine proposals are where your answers directly set my build order. Mark up anything in this document where the built behavior does not match how you want the product to work; that feedback is exactly what this walkthrough is for.
