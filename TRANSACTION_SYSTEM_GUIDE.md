# Transaction Generation System - A Guide for Real Estate Professionals

**Audience:** Transaction coordinators, agents, team leads, and brokers (no technical background needed)
**What this covers:** The full journey through the actual screens, with what each page looks like, from setting up your task list in Settings, to opening a new deal in the AI Wizard, to the task list the system builds, to working the deal on its transaction page
**Last updated:** June 23, 2026

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
| Build and approve the task list | The wizard's last step, "Tasks & create" | A summary banner, the full task list grouped by milestone, and an orange "Approve & Create" button |
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

- On the **left** is a **dark branded rail** that shows your progress: a label like **"Step 3 of 5 · Timeline"** and a row of dots that fill in orange and turn to checkmarks as you complete each phase. You can click a completed step to jump back to it.
- In the **center** is your working area for the current step.
- On the **right** is the **source document viewer** showing the contract itself, so you can check the system's reading against the original. (On the last two steps the contract viewer steps aside for a slim read-only timeline of the deal's deadlines.)
- Along the **bottom** is a **Back** button and one orange **primary button** whose label changes by step: "Start Intake", then "Continue" or "Confirm Details", then "Confirm Timeline", "Confirm Checklist", and finally "Approve & Create".

The five phases are described below.

### Step 1 - Upload

You drag the signed contract onto the page (plus any counters or addenda). A short **AI Parsing** view shows the system reading the documents. The bottom button reads **"Start Intake"**.

### Step 2 - Review details

The center shows the facts the system pulled from the contract as simple **Name / Value rows** (property address, parties, purchase price, and the deal's specifics such as HOA, inspection, and who orders title). The contract sits in the **viewer on the right**.

Three things on this screen make it trustworthy:

- **Every value links to the contract.** Next to a value the AI found, a small magnifier opens a strip that reads, for example, **"Source: 'The above offer is Accepted ...' Page 9 · AI confidence 93%"** with a **"View in Document"** button. Clicking it switches the right-hand viewer to that page and draws a highlight box over the quoted text. (When more than one file is uploaded, the viewer shows a tab per file plus page controls, zoom, and a "Search document text" box.)
- **It double-checks the critical fields.** A panel titled **"Double-check found N values to verify"** appears only when the system's two independent readings of an important field genuinely disagree. It no longer flags differences that are only formatting, for example a street address with and without the city and zip.
- **It points out genuinely missing documents.** A note like **"5 referenced documents not uploaded"** lists documents the contract refers to but that you did not include. It only appears when a document is truly missing, not when it is already in your upload.

Anything the system could not find is gathered into a short **Missing Info** step so you can fill it in, with a **"Double-check found 1 value to verify"** style prompt where needed.

### Step 3 - Timeline ("Review your timeline")

At the top is an orange **anchor card** asking **"Does this Date of Acceptance look right?"** with the date shown large, because every deadline is counted from it.

- If the date came from the contract, a **"View in document"** link shows where.
- If the system could not find that date, the card says so plainly and shows a **date picker**. **It never makes up a date.**
- The deadline list below stays **dimmed and locked** until you click **"Looks good"** to confirm the date; only then does it unlock.
- Each deadline row shows its name, its date, and **how it was worked out** (for example "5 days after Date of Acceptance"). Core dates like Closing and Possession have no Remove button.
- **"Edit date"** on the anchor card lets you pick a different day and shows a summary of how many deadlines move. **"+ Add deadline"** adds a custom item. If the contract held a deal-specific deadline, an **"AI suggestions"** group appears with cards, each showing the rule, a **confidence chip**, and a citation link; you **Add** or **Skip** each one.

The bottom button reads **"Confirm Timeline"**.

### Step 4 - Compliance

The center lists the standard documents this type of deal needs so you can track what has been collected. You can **Add document**, attach files, or load **"Use your own checklist"**. The bottom button reads **"Confirm Checklist"**.

### Step 5 - Tasks & create

This is where you review the full proposed task list and approve it. Because it is the moment the deal is created, it has its own section below.

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
5. **Sets each deadline** by counting from the Contract Acceptance date or the Closing date. If a deadline lands on a weekend or a recognized holiday, it moves to the next business day, the way contracts expect.
6. **Assigns each task to the right person** (you, the co-op agent, the buyer, the seller, the loan officer, or the title company).

### Two guarantees that protect you

- **What you preview is exactly what gets created.** The list on the Step 5 screen is produced by the very same process that creates the tasks, so there are no surprises after you approve.
- **The system is honest about anything it cannot schedule.** If a needed date or window is missing, it does not invent a deadline. It leaves that task **undated** and shows a clear reason, and it raises a **coverage note** if a required workflow produced no task at all (described next).

---

## 5. Reviewing and approving (the "Tasks & create" screen)

Step 5 shows the complete proposed list before anything is created.

### What the screen looks like

- **A summary banner** at the top in a soft card: a headline like **"24 tasks · Mar 12 - Jul 18"**, then small chips: **"24 will be created"**, **"2 undated"** (amber when above zero), and **"6 milestones"**.
- **An amber "undated" notice** when some tasks could not be dated yet, explaining why (for example a missing key date) and that you can add it now or set it later.
- **An amber "coverage" notice** when a required workflow produced no task, for example **"No title task was generated, confirm who orders title."**
- **A "Search tasks" box**, and below it the **tasks grouped by milestone**. Each task shows its due date, who it is for, and **why it was included**; you uncheck the ones you do not want (unchecked tasks will not be created).
- **A "Suggest more tasks" action** asks the AI for optional extras, which you add or skip one by one.

When the list looks right, the bottom button reads **"Approve & Create"**. Clicking it creates exactly the list you reviewed and opens the deal's transaction page.

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
- **It fits the deal.** Only the tasks that apply to this specific transaction appear, with deadlines counted from the contract and rolled to business days.
- **You stay in control.** You review and adjust the full list on the Step 5 "Tasks & create" screen before a single task is created, and what you preview is exactly what gets created.
- **It is honest about gaps.** When the system is missing a date or a piece of information, it tells you plainly (a locked timeline, an undated task with a reason, a coverage notice) and leaves the task undated rather than guessing, so a confident-looking but wrong deadline never reaches you.

---

## 8. A few decisions we need you to confirm

The system is built to be honest rather than to guess. In a handful of places, the best default depends on how your brokerage and your local contracts actually work. We have already built a sensible, safe default for each one, so nothing here blocks day-to-day use. These questions simply let us fine-tune the system to your office. For each one below you will find what it is about, how the system behaves today, what we suggest, and the decision we need from you.

### Question 1 - When the contract does not say who orders title

**What this is about.** Every deal needs to know whether your side or the other side is responsible for ordering the title work. That single answer decides which task you get: an **"Order Title"** task (your office orders it) or a **"Confirm Title Order"** task (you follow up to make sure the other side ordered it).

**How it works today.** The system reads this straight from the contract whenever the contract states it. When the contract is silent and the question was not answered in the wizard, the system does not guess. It leaves it blank and shows a notice on the "Tasks & create" screen: "No title task was generated, confirm who orders title." That way a deal can never quietly launch with no title task.

**What we suggest.** Keep that honest notice as the safety net, and, if you like, let your brokerage set a default side for the silent case, since most offices have a usual arrangement.

**Your call.** When the contract does not say who orders title, would you like the system to assume a side by default (and which side: your side or the other side), or keep prompting you to choose each time?

### Question 2 - Standard deadline windows when the contract does not list them

**What this is about.** A few deadlines are counted from a number of days the contract usually spells out: the inspection period, the inspection-response window, the HOA-document delivery window, and the insurance-commitment window.

**How it works today.** The system uses the number written in the contract. When that number is missing, it does not invent one. It leaves that single deadline undated with a short note, so you can fill it in.

**What we suggest.** Let your brokerage set standard fallback windows that pre-fill (visibly, so you can still change them) when the contract is silent. As a starting point, in calendar days: inspection 10, inspection response 5, HOA documents 10, insurance commitment 10.

**Your call.** What standard day counts should we use for your market? Please confirm or adjust the four suggested numbers above.

### Question 3 - Appraisal on cash deals

**What this is about.** Financed deals always include appraisal tasks (ordered, then completed) because the lender requires the appraisal. Cash deals usually have no lender and no appraisal.

**How it works today.** Cash deals get no appraisal tasks by default.

**What we suggest.** Keep cash deals appraisal-free by default. If some of your cash buyers do choose to appraise, we add a simple one-click "this cash deal has an appraisal" option on the deal, rather than always creating the tasks.

**Your call.** Do your cash deals usually involve an appraisal?

### Question 4 - Calendar days versus business days

**What this is about.** Some contract deadlines are written in calendar days (every day counts) and some in business days (weekends and holidays are skipped). The two can land on different dates, so it matters which way each deadline is counted.

**How it works today.** Every deadline is counted in calendar days, and if a deadline happens to land on a weekend or a recognized holiday, it is moved to the next business day.

**What we suggest.** Switch only the specific deadlines your contracts actually write in business days to count that way. The likely candidates are the inspection-response deadline and the financing or clear-to-close deadline, but we want your confirmation rather than guessing.

**Your call.** Which of your contract deadlines are written in business days rather than calendar days?

### Question 5 - Which states to support next

**What this is about.** Closings work differently from state to state. In title-company states (such as Indiana, your primary market) the title company runs the closing. In attorney-closing states (for example New York, Georgia, or South Carolina) an attorney is involved and the task list is different.

**How it works today.** The system is set up for title-company states, with Indiana fully supported. The attorney-state tasks (attorney review period, attorney-ordered title, attorney closing) are not built yet.

**What we suggest.** Build the attorney-state workflow once you tell us which states your next brokerages are in, so we model the right one first instead of guessing.

**Your call.** Which states are your next brokerages in, and are there any attorney-closing states you would like supported first?

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
