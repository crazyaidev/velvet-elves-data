# Transaction Generation System - A Guide for Real Estate Professionals

**Audience:** Transaction coordinators, agents, team leads, and brokers (no technical background needed)
**What this covers:** The full journey through the actual screens, with what each page looks like, from setting up your task list in Settings, to opening a new deal in the AI Wizard, to the task list the system builds, to working the deal on its transaction page
**Last updated:** July 3, 2026 (Jake's five decisions from Section 8 are now built in; deadlines no longer move off weekends or holidays)

---

## 1. The big picture

When you start a new deal, the system does three things for you, in order:

1. It reads the signed contract and pulls out the key facts (the property, the people, the important dates, and the deal's specifics).
2. It takes your brokerage's own master task list and fits it to this exact deal, picking only the tasks that apply, assigning each one to the right person, and giving each a due date.
3. It shows you the complete proposed list so you can adjust it, and only creates the deal once you approve.

Three promises hold this together, and the rest of this guide shows you, screen by screen, how each one plays out:

- **It follows your playbook.** Every task comes from your master task list. The system never invents tasks.
- **It fits the deal.** Only the tasks that apply to this specific transaction appear, with deadlines counted from the contract.
- **You stay in control, and it stays honest.** You review and adjust everything before a single task is created, and when the system is missing a piece of information it tells you plainly instead of guessing.

### Where this lives in the app, and what the app looks like

Once you sign in, the screen has three constant areas:

- A **left sidebar** with your navigation, grouped into **Deals** (Active Transactions, Pending, Closed, All Transactions, Clients) and **Workflow** (My Task Queue, All Documents, Closing Calendar). At the very bottom is your **profile card**; clicking it opens a menu with **Settings** and Log out.
- A **top bar** with global search, a notification bell, and a prominent orange **"+ New Transaction"** button on the right.
- The **main area** in the center, which changes as you move between pages.

Here is the map of the workflow before we walk through each page:

| What you are doing | Where it lives | What the page looks like |
|---|---|---|
| Set up your task list | Settings, then Task Templates (`/admin/task-templates`) | A searchable library of task cards with colored "automation" chips, plus a "New template" button |
| Start a new deal | The "+ New Transaction" button, which opens the AI Wizard (`/transactions/new`) | A full-screen, two-panel wizard: a dark progress rail on the left, your work in the center, the contract on the right |
| Verify and create the deal | The wizard's last step, "Verification" | The full summary with citations, the AI's proposals, and a full-width orange "Upload Transaction" button under a confirmation line |
| Work the deal | The transaction page (`/transactions/:id`) | A deal header, then a white card with tabs (Timeline, Compliance, Documents, Tasks, People, Activity) and an AI Agent panel |
| See work across all deals | Active Transactions, My Task Queue, Closing Calendar (sidebar) | A list of deal cards, a single list of your tasks, and a calendar of deadlines |

---

## 2. Your master task list (the Task Templates page)

Your master task list is the heart of the system: your brokerage's standard operating procedure written down once, so the system can apply it to every deal automatically.

**How to get there:** Click your profile card (bottom-left), choose **Settings**, then **Task Templates** (administrators and team leads only; the address is `/admin/task-templates`). Team leads also have a **Task Templates** link in the sidebar's Team section.

### What the page looks like

- **Header:** the title "Task Templates", a small **back link to Settings**, a count badge (for example "96 templates"), and an orange **"New template"** button on the right.
- **A row of four summary tiles** across the top: **Templates** (how many you have), **Active** (applied to new deals), **Categories** (groups in use), and **Automated** (AI-assisted or hands-off).
- **A toolbar:** a **"Search templates..."** box on the left, and a row of **category filter chips** ("All" plus one per category) you can click to narrow the list.
- **The library list:** every task is a row showing its name, who it is for, and a colored **automation chip**, so you can see at a glance how each is handled:
  - green for **Automated**
  - orange for **AI-assisted**
  - amber for **To be automated**
  - gray for **Manual**
- Each row has a **pencil** (edit) and a **trash** (retire) control.

### What each task holds (the edit form)

Clicking **New template** or a row's pencil opens a form where you set:

- **Task name** (for example "Order Title" or "Inspection Response Reminder").
- **Who it is for**: you (the agent or coordinator), the co-op agent, the buyer, the seller, the loan officer, or the title company.
- **When it is due**: a rule, not a fixed date. Each deadline is counted from one of the deal's two anchor dates, the **Contract Acceptance date** or the **Closing date**, for example "10 days before closing" or "the day after acceptance".
- **Which deal types it belongs to** (the six are below).
- **When it applies**: an optional condition, for example only when there is an HOA, only when there is an inspection, or only when your side orders title.
- **What it waits on**: an optional dependency on another task, so a chain stays in order.
- **How it is handled**: manual or an automated step.

### The six deal types

Every task is tagged with the deal types it belongs to. The system recognizes six:

| Deal type | Plain meaning |
|---|---|
| Buying / Financed | You represent a buyer who is getting a mortgage |
| Buying / Cash | You represent a cash buyer |
| Selling / Financed | You represent a seller; the buyer is financing |
| Selling / Cash | You represent a seller; the buyer is paying cash |
| Dual Agency / Financed | You represent both sides; the buyer is financing |
| Dual Agency / Cash | You represent both sides; cash deal |

"Dual Agency" (representing both buyer and seller) is handled intelligently: instead of creating two copies of every task, the system combines duplicates into one and drops tasks that no longer apply, for example a "Co-op Agent Welcome" is skipped because in dual agency there is no co-op agent.

### Adding, editing, retiring, or importing

- **Add** with the orange "New template" button.
- **Edit** with a row's pencil; changes apply to deals created afterward.
- **Retire** with the trash icon. A confirmation explains it plainly: "This removes the template from your library so it is no longer applied to new transactions. Existing deals keep the tasks they already have."
- **Import** your own list from a spreadsheet (`/admin/task-templates/import`). The current import handles the basics; the advanced settings (conditions and dual-agency behavior) are best confirmed in the editor afterward, since richer one-step importing is an active improvement.

---

## 3. Starting a new deal (the AI Wizard)

Click the orange **"+ New Transaction"** button (top bar). After you upload a contract, the **AI Wizard** opens full screen at `/transactions/new`.

### The shape of the wizard screen

The wizard is a **two-panel workspace**:

- On the **left** is a **dark branded rail** that shows your progress: a label like **"Step 2 of 4 · Contract Details"** and a row of dots that fill in orange and turn to checkmarks as you complete each phase. You can click a completed step to jump back to it.
- In the **center** is your working area for the current step.
- On the **right** is the **source document viewer** showing the contract itself, so you can check the system's reading against the original.
- Along the **bottom** is a **Back** button and, on the middle steps, one orange **Continue** button. On the final step the create button is not in the footer at all: it is a full-width **"Upload Transaction"** button in the review column itself, directly under a short confirmation line.

The four phases are described below.

### Step 1 - Upload

You drag the signed contract onto the page (plus any counters or addenda). A short **AI Parsing** view shows the system reading the documents.

### Step 2 - Contract Details

The center shows the facts the system pulled from the contract as simple **Name / Value rows**: the property address, then the deal's pricing, key dates, financing, contingencies, terms, and notes. The contract sits in the **viewer on the right**.

Three things on this screen make it trustworthy:

- **Every value links to the contract.** Next to a value the AI found, a small magnifier opens a strip that reads, for example, **"Source: 'The above offer is Accepted ...' Page 9 · AI confidence 93%"** with a **"View in Document"** button. Clicking it switches the right-hand viewer to that page and draws a highlight box over the quoted text. (When more than one file is uploaded, the viewer shows a tab per file plus page controls, zoom, and a "Search document text" box.)
- **Anything uncertain is flagged, not buried.** A **"✦ Found in the contract - needs your eyes"** band at the top lists every low-confidence or unanswered field as a chip; clicking a chip scrolls to and focuses that field. A value the AI read at low confidence still fills the field - the confidence only controls the flag, never whether you see the reading.
- **It double-checks the critical fields.** A panel titled **"Double-check found N values to verify"** appears only when the system's two independent readings of an important field genuinely disagree. It does not flag differences that are only formatting.

Fixed decisions such as **who orders title** (and, on a cash deal, the appraisal election) are one-click choices rather than free typing, and the deal cannot be created while one is unanswered - the answer changes which tasks are generated.

### Step 3 - Contacts & Fees

The center shows a card for every party on the deal (buyers, sellers, both agents, loan officer, title company, closing attorney), each with its citation and pre-filled from your vendor directory where the system recognizes a contact.

Below the contacts are the two **fee cards**: your **professional fee** and any **transaction fee** (a broker, team, or brokerage admin fee collected on the deal - separate from the app's own per-deal billing fee). For each: click **Buyer**, **Seller**, or **Both**, type one number, and click **%** or **$**. When both sides pay, each side keeps its own amount and its own unit, so "seller 2%, buyer $250" is expressible. A fee the contract itself mentions appears as a read-only hint - the number is always yours to enter. The cards prefill from your last deal and are held back from the deal until you confirm or edit them.

### Step 4 - Verification

The full summary of everything you verified, with citations and Edit jumps back to the step that owns each row, plus the AI's proposed deadlines and checklist rows to accept or dismiss, and the deal's watch-outs.

If the paperwork is not fully signed, this step offers the action that matches **whose** signature is missing: your own client's side gets the **e-signature queue**; the other side gets **"request the signed copy from the other agent"**, which becomes a real task addressed to the co-op agent instead of an e-signature sent to someone else's client. Referenced-but-missing documents offer the same one-click request.

At the bottom of the review column sits a short confirmation line and the full-width **"Upload Transaction"** button. Because that click is the moment the deal is created, it has its own section below.

**Note on the document checklist:** it is no longer a step you walk. The checklist is still built for the deal and committed when you click Upload Transaction, with your uploaded files already matched to their rows, and you edit it afterwards on the deal's **Compliance** tab - where it stays useful for the whole transaction rather than only at intake.

### What the AI does, and does not, do

- **The AI reads the contract and can suggest a few extra tasks** that may be specific to this deal. Suggestions are always optional and only added if you click to add them.
- **The AI never decides your task list.** The core list is built strictly from your master task list. The system is called an "AI Wizard" because AI reads the paperwork and assists you, not because it improvises the tasks.

---

## 4. How the task list is built

When you reach Step 5, the system fits your master task list to this deal. It does this the same way every time, which is why you can trust the result. In plain terms, it:

1. **Picks the right tasks for the deal type.** For a dual-agency deal it gathers both the buy-side and sell-side tasks, then combines the duplicates.
2. **Applies the deal's specifics.** No HOA, no HOA tasks. If your side orders title, "Order Title" appears; if the other side orders it, "Confirm Title Order" appears instead.
3. **Handles dual agency** by merging duplicate tasks into one and skipping tasks that have no meaning when you represent both sides.
4. **Applies the closing style** (a title-company closing versus an attorney closing).
5. **Sets each deadline** by counting from the Contract Acceptance date or the Closing date. Every deadline counts in **calendar days** and lands exactly where the count says, weekends and holidays included; a real-estate timeline can end on a Sunday, and a deadline that arrives early is always safer than one that slips late. A deadline counts in **business days** only when the contract writes it that way, and its label says so plainly ("5 business days after Date of Acceptance"). A small gray "lands on Sat" tag appears on weekend deadlines so nothing surprises you.
6. **Assigns each task to the right person** (you, the co-op agent, the buyer, the seller, the loan officer, or the title company).

### Two guarantees that protect you

- **What you preview is exactly what gets created.** The list on the Step 5 screen is produced by the very same process that creates the tasks, so there are no surprises after you approve.
- **The system is honest about anything it cannot schedule.** If a needed date or window is missing, it does not invent a deadline. It leaves that task **undated** and shows a clear reason, and it raises a **coverage note** if a required workflow produced no task at all (described next).

---

## 5. Creating the deal (the Verification screen)

Step 4 is the last screen, and the only place a deal is created.

### What the screen looks like

- **The full summary** of everything you verified, grouped property / dates / financing / terms / parties / fees, every row carrying its citation and an **Edit** jump back to the step that owns it.
- **The AI's proposals** - deal-specific deadlines, checklist rows, and coordination tasks - each with the rule it came from and a citation, accepted or dismissed one click at a time.
- **The deal's watch-outs**, kept with their citations for the life of the deal.
- **The signature decision**, when the paperwork is not fully signed: the e-signature queue for your own client's missing signature, or "request the signed copy from the other agent" when the missing signature is the other side's.
- **A confirmation line and a full-width "Upload Transaction" button** at the end of the review column. The footer on this step carries only **Back** - there is one create button, never two.

Clicking **Upload Transaction** creates the deal, generates the full task plan and timeline from your master task list, commits the document checklist with your uploads already attached, and opens the deal's transaction page. A one-time line across the top of that page tells you exactly what was built and links each number to the tab that holds it.

The deal cannot be created while a decision-critical answer is missing (who orders title; the appraisal election on a cash deal), while the double-check has an unresolved disagreement, or before at least one document is uploaded.

---

## 6. Managing the transaction (the transaction page)

After the deal is created you work it on its **transaction page** (`/transactions/:id`). You also reach it from the **Active Transactions** list by clicking a deal.

### What the page looks like

- **A header band** across the top shows the property and the deal's key dates.
- **A white card with a tab strip.** The active tab is underlined in orange. The tabs are:
  - **Timeline** - the deal's deadlines in order.
  - **Compliance** - the document checklist from the wizard, with what is still outstanding.
  - **Documents** - the deal's files, with an Upload button.
  - **Tasks** - the task list the wizard built (detailed below).
  - **People** - the parties on the deal (buyer, seller, agents, lender, title).
  - **Activity** - the history of what has happened on the deal.
- **An AI Agent panel.** On a wide screen it sits to the right of the card as a working assistant (you can ask it about the deal or have it take actions); on a narrow screen it is an **Agent** tab. An **Email** area handles the deal's correspondence.

### The Tasks tab in detail

The Tasks tab groups the work so the urgent items are obvious: **Overdue**, **Due Today**, **Upcoming**, and **Completed**. Each task row shows:

- A colored **status pill** you change from a dropdown: **Pending** (gray), **In progress** (blue), **Completed** (green), **Skipped** (gray). ("Blocked", in red, is set by the system when a task is waiting on another.)
- A small **basis chip** that explains the deadline, for example **"3 days before Closing Date"**.
- A **link to the related compliance item** where one exists, an **Auto-Email** toggle for tasks whose recipient has an email on file, and an **AI chip** with a citation where the task came from the contract.
- A **pencil** to edit the due date and a **"..." menu** for more actions.
- An **"Add Task"** button lets you add your own task or a one-off deadline.

### Two behaviors that keep the list correct

- **When a date changes, the deadlines follow.** If an addendum moves the closing or acceptance date and you update it, the system recomputes the affected deadlines and shows you exactly which dates moved (old date to new date) before anything sticks, so completed work is preserved.
- **If the deal type changes** (for example a financed deal becomes cash), the system updates the task list to match: it keeps your completed tasks, removes tasks that no longer apply, and adds the ones that now do.

### Seeing work across all your deals

The same tasks and deadlines feed the sidebar views, so you do not have to open each deal:

- **My Task Queue** (`/tasks/queue`, under Workflow) - every task assigned to you, across all deals, in one list.
- **Closing Calendar** (under Workflow) - your deadlines laid out on a calendar.
- **Active Transactions** (`/transactions/active`, under Deals) - all your active deals as cards; click one to open its transaction page.

---

## 7. Why you can trust it

Pulling the promises from the start of this guide back together, now that you have seen them on screen:

- **It follows your playbook.** Tasks come from your master list on the Task Templates page, never invented by the AI.
- **It fits the deal.** Only the tasks that apply to this specific transaction appear, with deadlines counted from the contract in calendar days that land exactly where the count says.
- **You stay in control.** You review and adjust the full list on the Step 5 "Tasks & create" screen before a single task is created, and what you preview is exactly what gets created.
- **It is honest about gaps.** When the system is missing a date or a piece of information, it tells you plainly (a locked timeline, an undated task with a reason, a coverage notice) and leaves the task undated rather than guessing, so a confident-looking but wrong deadline never reaches you.

---

## 8. Decisions from your brokerage, now built in

Earlier versions of this guide ended with five open questions. Jake answered
all five (the full exchange is preserved in
`Q&A_Transaction_Generation_System.md`), and the system now works exactly as
decided:

1. **When the contract does not say who orders title, the system asks you —
   never a default.** "Who Orders Title" is a required question on the
   wizard's review screen: two clear cards ("Buyer orders title" / "Seller
   orders title"), each telling you which task it will create. There is no
   brokerage default to overlook. The "no title task" notice remains as the
   safety net for deals created outside the wizard, and answering it there
   creates the right task on the spot. Attorney closings skip the question
   entirely — the attorney owns title work there.

2. **No standard deadline windows, ever.** The inspection, inspection
   response, HOA document, and insurance windows come from the contract or
   from you. When the AI is at least 90% sure, the value is filled in with
   its citation. When it is fairly sure but not certain (roughly 70-89%),
   the field stays EMPTY and an amber "AI suggests: 10 days · 82% · page 4"
   chip appears — one click accepts it, or you type your own. Below that,
   the field is simply blank for you to fill. Your admin can tune these
   levels under AI & Automation.

3. **Cash deals: the appraisal follows the contract's election.** On every
   cash deal, in every state, the AI looks for whether the buyer elected or
   waived an appraisal. Elected: the appraisal tasks appear. Waived: they do
   not. Silent: the wizard asks you ("Appraisal on this cash deal?") before
   the deal can be created — no guessing. On a live deal, the Timeline tab
   shows the recorded decision with a one-click switch; flipping it adds or
   removes the appraisal tasks while completed work stays untouched.

4. **Calendar days, landing exactly where the count says.** Deadlines no
   longer move off weekends or holidays: 5 days after a Monday acceptance is
   Saturday, and it stays Saturday — hitting early always beats slipping
   late. A deadline counts in business days only when the contract writes it
   that way, and its label says so ("5 business days after Date of
   Acceptance"). Weekend deadlines carry a small gray "lands on Sat" tag so
   you see it coming.

5. **Attorney states, per your workbook.** The product now carries two base
   workflows instead of one list per state. In North Carolina, South
   Carolina, Georgia, and Delaware the attorney owns the legal, title, and
   closing steps — your coordination task is "Confirm Closing Attorney
   Selected" and "Send Executed Contract to Closing Attorney", never "Order
   Title" — and state-specific steps (like the North Carolina title
   opinions) appear only where verified. New Jersey gets its 3-business-day
   attorney-review deadline counted from delivery of the signed contracts,
   and only when a licensee prepared the contract. New York (and anywhere
   else) gets a review deadline only when the contract itself creates one.
   Every other state runs the standard title-company workflow until its
   rules are verified — no state is ever guessed into the attorney column.

---

## 9. Quick reference

### Pages used in this workflow

| Page | Where to find it | What it looks like |
|---|---|---|
| Task Templates | Settings, or Team sidebar (`/admin/task-templates`) | Library of task rows with colored automation chips, search, category chips, "New template" |
| AI Wizard | "+ New Transaction" button (`/transactions/new`) | Two-panel wizard: dark progress rail, center work area, contract viewer; step-specific orange button |
| Transaction page | A deal card in Active Transactions (`/transactions/:id`) | Deal header, white card with tabs (Timeline, Compliance, Documents, Tasks, People, Activity), AI Agent panel |
| Active Transactions | Sidebar, Deals group (`/transactions/active`) | All active deals as cards |
| My Task Queue | Sidebar, Workflow group (`/tasks/queue`) | Every task assigned to you, across deals |
| Closing Calendar | Sidebar, Workflow group | Your deadlines on a calendar |

### Glossary

- **Master task list (playbook)** - your brokerage's standard set of tasks on the Task Templates page, applied automatically to every deal.
- **Deal type** - one of the six combinations of buying or selling, financed or cash, including dual agency.
- **Anchor dates** - the two dates every deadline is counted from: Contract Acceptance and Closing.
- **Condition** - a rule that makes a task appear only when something is true (HOA, inspection, who orders title, home warranty).
- **Dual agency** - representing both the buyer and the seller; the system combines duplicate tasks instead of doubling them.
- **Automation chip** - the colored label on a task showing how it is handled (green Automated, orange AI-assisted, amber To-be-automated, gray Manual).
- **Basis chip** - the small label on a task that explains its deadline rule, for example "3 days before Closing Date".
- **Undated task** - a task the system could not schedule because a needed date is missing; shown with a clear reason rather than a made-up date.
- **Coverage note** - a heads-up on the "Tasks & create" screen that a required workflow produced no task, so you can confirm nothing was missed.
