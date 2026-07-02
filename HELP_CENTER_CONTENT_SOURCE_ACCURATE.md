# Velvet Elves Help Center — Source-Accurate Content

> **How this file was produced.** Every article below was written by reading the
> shipped frontend and backend source, not the planning documents in
> `velvet-elves-data`. Where the previously-live content
> (`20260903090000_help_center_content_rewrite.sql`) disagreed with the code, the
> code wins. The companion migration
> `20260905090000_help_center_content_source_accurate.sql` upserts this content
> in place (same collection/article slugs, so existing rows and curated related
> links are refreshed, not duplicated).

---

## Part 1 — Why the Help Center drifted from the app

The current Help Center content is not wrong so much as *written from the plan
instead of the product*. Concretely:

1. **It was authored from design/spec docs and an aspirational voice, not the
   running UI.** The header of `20260903090000_help_center_content_rewrite.sql`
   states it was written "for a busy real-estate professional who has never seen
   the app." That is exactly how it reads — it describes the product the
   `SYSTEM_DESIGN.md` / `FRONTEND_UI_WORKFLOW_LOGIC.md` documents *describe*,
   using vocabulary from those docs, rather than the labels, groups, and flows
   the code actually renders.

2. **It invented a role word the UI never uses.** The content repeatedly claims
   coordinators are "called *elves* in the app" and refers to "an agent or elf."
   In code, `formatRole('TransactionCoordinator')` returns **"Transaction
   Coordinator"** ([formatters.ts](../velvet-elves-frontend/src/utils/formatters.ts)).
   "Velvet Elves" is the *product* name; the *role* is Transaction Coordinator.
   Nothing in the shipped UI labels a person an "elf."

3. **The navigation description is stale.** The "Finding your way around"
   article lists only Dashboard / Deals / Workflow / Intelligence / Team. The
   real internal sidebar
   ([dashboardShellConfig.ts](../velvet-elves-frontend/src/layouts/dashboardShellConfig.ts),
   [AppLayout.tsx](../velvet-elves-frontend/src/layouts/AppLayout.tsx)) also has
   **Payments**, **Vendors**, and (for Admins) **Oversight** groups, and the
   account menu is **Settings / Help Center / Log Out**, not "update your name /
   preferences / sign out."

4. **It simplified flows that are richer in the product.** The "AI transaction
   wizard" article describes four generic steps and a "Choose AI Import" branch.
   The shipped wizard
   ([wizardTypes.ts](../velvet-elves-frontend/src/components/wizard/wizardTypes.ts),
   [NewTransactionWizard.tsx](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx))
   is a nine-step, phase-grouped flow (Documents → AI Parsing → Address &
   Contacts → Purchase Info → Missing Info → Confirm → Timeline → Compliance →
   Review Tasks) launched full-screen straight from **+ New Transaction** — there
   is no separate "AI Import" chooser.

5. **The app kept moving after the content was written.** Settings was
   consolidated into a single hub with ~20 cards
   ([settingsCards.ts](../velvet-elves-frontend/src/pages/settings/settingsCards.ts)),
   each deal now opens a tabbed **Workspace** with an AI Agent pane
   ([TransactionWorkspacePage.tsx](../velvet-elves-frontend/src/pages/transactions/TransactionWorkspacePage.tsx)),
   and tenant billing became a **credit wallet** ("Billing & Credits"). The
   content never caught up, and — per the project notes — it was structurally
   verified but never reconciled against the live UI.

The fix below re-grounds every article in what the code renders today.

### Ground-truth reference (verified in source)

| Area | Source of truth | What ships |
| --- | --- | --- |
| Roles | `types/enums.ts`, `formatters.ts` | Agent, Transaction Coordinator, Team Lead, Attorney, Admin, Client, For-Sale-By-Owner, Vendor. No "elf." |
| Internal sidebar | `dashboardShellConfig.ts`, `AppLayout.tsx` | KPI tiles + Dashboard, **Deals**, **Workflow**, **Payments**, **Vendors**, **Intelligence**, **Team** (TL/Admin), **Oversight** (Admin), **Platform** (platform admins). |
| Account menu | `AppLayout.tsx` | Settings · Help Center · Log Out. |
| Deals list tabs | `TransactionListPage.tsx` | All, Overdue, Due Today, Needs Attention, Closing Soon, In Inspection, On Track, Unhealthy. Sort: Urgency, Close Date, Client Name, Price. |
| Deal card | `components/shared/TransactionCard.tsx` | Expands in place to 3 columns (Tasks / Key Dates / Contacts) + milestone bar + AI next-step; opens the full workspace at `/transactions/:id`. |
| Deal workspace | `TransactionWorkspacePage.tsx` | Tabs: Agent, Timeline, Compliance, Documents, Tasks, People, Activity, Email. |
| New-transaction wizard | `wizardTypes.ts` | Steps: Documents, AI Parsing, Address & Contacts, Purchase Info, Missing Info, Confirm, Timeline, Compliance, Review Tasks. |
| Transaction status | `models/enums.py` | Active, Incomplete, Paused, Completed, Closed. |
| Closing modes | `types/enums.ts` | attorney, title_escrow, shared_approval. |
| Completion methods | `active-transactions/AddTaskModal.tsx` | Phone Call, Email, DocuSign/E-Signature, In Person, Upload Document, Online Portal, AI Agent, Other. |
| Email connect | `settingsCards.ts`, `ConnectionsPanel.tsx` | Settings → **Email & E-signature**: Gmail / Outlook + DocuSign. |
| All Documents tabs | `pages/documents/DocumentsPage.tsx` | All, Missing, Pending review, Sent, Signed. |
| Requirement status | `schemas/document_requirement.py` | `missing` \| `uploaded` \| `waived`. |
| Settings hub | `settingsCards.ts` | Personal + Workspace + Platform card groups (see Admin & Settings). |

---

## Part 2 — Corrected content

Conventions: collection `icon` ∈ {BookOpen, Rocket, LayoutDashboard, Users, Mail,
FileText, CreditCard, Settings, Calendar, Building2, ShieldCheck, Sparkles};
`tone` ∈ {green, orange, blue, purple, neutral}. Article links use
`/articles/<slug>` and `/collections/<slug>`.

---

### Collection: Getting Started  `getting-started`
Icon Rocket / green. *New to Velvet Elves? Start here — what the platform does,
how to sign in, what your role can do, and a first-deal walkthrough.*

#### `what-is-velvet-elves` — What is Velvet Elves?
*Excerpt:* The short version: you give it a contract, and it sets up and runs the whole transaction for you.

**Velvet Elves is software that does the busywork of a real estate transaction for you.** You upload the signed contract, its AI reads the document, sets up the deal, builds a to-do list with real due dates, and then helps you keep everything on track to closing.

Think of it as a transaction coordinator that never sleeps: it reads paperwork, drafts emails, watches deadlines, and tells you what needs attention today.

## What it actually does
- **Reads your paperwork.** Upload a contract and the AI pulls out the property address, the buyers and sellers, the price, the financing, and the deadlines, so you do not retype anything.
- **Builds your task list automatically.** From the deal type and the dates in the contract, it generates the tasks you need with due dates already filled in.
- **Keeps everyone on the same page.** Emails, documents, vendors, and client updates all live on the deal, with a searchable history.
- **Tells you what is urgent.** A daily AI briefing sorts your deals into Critical, Needs Attention, and On Track so you always know where to start.

## Who uses it
Velvet Elves has a workspace shaped for each role: **Agents** who run deals, **Transaction Coordinators** who keep paperwork and deadlines moving, **Team Leads** who oversee a team, **Attorneys** who review and release legal files, and **Admins** who configure the account. It also gives **Clients**, **for-sale-by-owner sellers**, and **Vendors** their own limited views.

## Where to go next
1. [Sign in and set up your account](/articles/signing-in-and-your-account).
2. Skim [Set up your first deal](/articles/quick-start-first-deal).
3. Bookmark the [Glossary of terms](/articles/glossary-of-terms).

#### `quick-start-first-deal` — Set up your first deal
*Excerpt:* Sign in, start a new transaction, let the AI read a contract, review what it found, and watch your task list appear.

**The fastest way to see what Velvet Elves does is to turn one signed contract into a fully set-up deal.**

## Before you start
You need to be signed in (see [Signing in and managing your account](/articles/signing-in-and-your-account)) and have one contract file — a PDF, a photo, or a Word document.

## Step 1: Start a new transaction
Click **+ New Transaction** in the top bar or the sidebar footer. This opens the full-screen New Transaction wizard.

## Step 2: Add the contract
On the wizard's first step (**Documents**), drag your contract into the upload area or browse for it. You can add several files, and split one combined scan into separate documents by page range.

## Step 3: Let the AI read it
The **AI Parsing** step extracts the property, the people, the price and financing, and every milestone date. The following steps (Address & Contacts, Purchase Info, Missing Info) show you what it found so you can confirm or fix each part.

## Step 4: Double-check and confirm
On **Confirm**, the wizard compares its readings and highlights anything it was unsure about, next to a preview of the source document. Edit anything before you accept it.

## Step 5: Review the plan and create
**Timeline** and **Compliance** show the dates and checklist, then **Review Tasks** lists the tasks that will be created. Finish, and Velvet Elves saves the transaction, builds the task list, and opens the deal's workspace.

> If credit billing is enabled for your workspace, creating a transaction may spend one credit.

## What to do next
- Learn the list you live in: [The Active Transactions list](/articles/active-transactions-workspace).
- Clear your day: [Working from My Task Queue](/articles/my-task-queue).
- Connect your inbox: [Connecting your email](/articles/connecting-your-email).

#### `signing-in-and-your-account` — Signing in and managing your account
*Excerpt:* How to get in the first time, sign in day to day, reset a forgotten password, and use your account menu.

**You sign in with your email and a password.** Most people first get in by accepting an invitation from their brokerage or team lead.

## The first time: accept your invitation
Open the invitation email, click the link, set a password if you are new, and you land in the workspace built for your role. No email? Check spam, then ask whoever invited you to resend it.

## Signing in day to day
Go to your sign-in page, enter your email and password, and continue. Single sign-on / magic links are handled through the same sign-in screen when your organization uses them.

## Forgot your password?
Click **Forgot password** on the sign-in screen, enter your email, and follow the link in the reset email. Reset links expire; request a fresh one if yours stopped working.

## Your account menu
Click your name or avatar (top-right, or the sidebar footer) to open the account menu. It has three items: **Settings**, **Help Center**, and **Log Out**. For internal roles, **Settings** opens the Settings hub, where you edit your profile, notifications, connections, and more. See [Setting up your profile](/articles/completing-your-profile).

## Common questions
- **Can I change my own role?** No — roles are set by an admin. See [Understanding roles](/articles/understanding-roles).
- **I am locked out.** Use **Forgot password** first; if that fails, contact your admin. See [Getting support](/articles/getting-support).

#### `understanding-roles` — Understanding roles and permissions
*Excerpt:* A plain-English guide to who can do what across the eight roles.

**Your role decides what you see and do.** Velvet Elves has eight roles, and each gets a workspace shaped for its job.

## Internal team roles
| Role | What they mainly do |
| --- | --- |
| **Agent** | Owns deals, works the task list, talks to clients and vendors. |
| **Transaction Coordinator** | Supports agents by managing tasks, documents, and messages across many deals. |
| **Team Lead** | Sees the whole team, can step into any agent's deal, and manages shared templates and members. |
| **Attorney** | Reviews legal packets in a dedicated matter workspace, signs off at approval gates, and releases files to close. |
| **Admin** | Configures the account: users, templates, AI settings, branding, billing, and integrations. |

> "Velvet Elves" is the product's name. The coordinator role is labeled **Transaction Coordinator** (sometimes shortened to TC) everywhere in the app.

## External roles
| Role | What they see |
| --- | --- |
| **Client** | A buyer or seller on an agent-led deal; sees shared milestones, documents, messages, and invoices in the client portal. |
| **For-Sale-By-Owner (FSBO)** | A seller running their own property in a simplified, property-focused workspace. |
| **Vendor** | An inspector, lender, title rep, or other provider, scoped to the specific document requests and tasks assigned to them. |

## Why this matters
Permissions are enforced everywhere. If this help center describes something you cannot find, it may simply not be part of your role. Admins assign roles in [Users & Invites](/articles/user-management).

#### `navigating-the-app` — Finding your way around
*Excerpt:* The sidebar groups, the top bar, the AI briefing, and search — learn these once and the app feels familiar.

**Every internal screen has the same frame: the navy sidebar on the left, the top bar across the top, and your work in the middle.**

## The left sidebar
At the top, KPI tiles show live numbers for your book (for an agent: Overdue tasks, Closing this week, Active deals, Pipeline value). Below them is a standalone **Dashboard** link, then grouped navigation:
- **Deals** — Active Transactions, Pending, Closed, All Transactions, Clients.
- **Workflow** — My Task Queue, All Documents, Closing Calendar.
- **Payments** — Invoices & Payments (and Commission Payouts if you can trigger payouts).
- **Vendors** — Vendor Directory.
- **Intelligence** — AI Suggestions, AI Email Review, Vendor Proposals, Analytics.

Team Leads and Admins also see a **Team** group (Team Overview, Teams). Admins see an **Oversight** group (Communication Audit, Audit Log). Attorneys get their own Workspace group (Matters, Releases Queue, Recording Calendar, State Rules).

## The top bar
Left to right: your brokerage logo, the **Today's AI Briefing** button, the Critical / Needs Attention / On Track chips, **Search** (⌘K), the **Notifications** bell, your avatar menu (Settings / Help Center / Log Out), and the **+ New Transaction** button.

## Today's AI briefing
The **Today's AI Briefing** button opens the AI assistant with a briefing prompt. Next to it, the colored chips show how many deals are **Critical**, **Needs Attention**, and **On Track**; click one to jump to that filter on the Active Transactions list.

## Search
Press ⌘K (or click Search) to open the search palette. It spans client names, vendors, companies, property addresses, and dates, so a street name or last name is usually enough.

#### `completing-your-profile` — Setting up your profile and preferences
*Excerpt:* A few minutes in the Settings hub makes your emails look professional and helps the AI work for you.

**Your account menu → Settings opens the Settings hub, the one place your personal setup lives.**

## Profile
Open **Settings → Profile** to set your photo, name, email, phone, bio, and email signature. These appear on the emails you send and the portals your clients see.

## Connect your email
**Settings → Email & E-signature** is the highest-value step: connect your Gmail or Outlook inbox (and DocuSign) so messages file themselves on the right deal and drafts can send as you. See [Connecting your email](/articles/connecting-your-email).

## Set your defaults
- **Notifications** — choose which reminders and alerts you get. See [Notification preferences](/articles/notification-preferences).
- **My Playbook** — closing-checklist templates, tagged notes, preferred vendors, and reference materials that print on your closing checklist. See [Closing checklists](/articles/closing-checklists).
- **Help & Tour** — replay the guided product tour any time.

---

### Collection: Transactions  `transactions`
Icon LayoutDashboard / blue. *Creating a deal from a contract, the list where you triage, the workspace where you run it, key dates, status, and history.*

#### `creating-a-transaction` — Creating a new transaction
*Excerpt:* Start a deal from a contract with AI, or enter the basics by hand — both open the same wizard.

**Click + New Transaction (top bar or sidebar footer) to open the full-screen New Transaction wizard.** Everything happens in one place; there is no separate "import vs. manual" chooser.

## With a contract (recommended)
On the first step, drag in the contract (PDF, photo, or Word) or browse for it. The AI reads it and pre-fills the property, people, price, financing, and dates for you to confirm. See [Using the AI transaction wizard](/articles/ai-transaction-wizard).

## Without a contract yet
You can skip the upload and fill the essentials by hand — client, property address, transaction type, price, key dates, lender/title — then add the contract later and let the AI complete the rest.

## What happens when you finish
Velvet Elves saves the deal, **builds the task list** from the deal type and dates, and **opens the deal's workspace**. See [The transaction workspace](/articles/active-transactions-workspace).

> If credit billing is on for your workspace, creating a deal may spend one credit.

#### `ai-transaction-wizard` — Using the AI transaction wizard
*Excerpt:* A nine-step, guided flow that turns a contract into a filled-in deal — and shows its work at every step.

**The New Transaction wizard walks through nine steps, grouped into phases, with a stepper at the top and a deal brief on the side.** You confirm the details as you go.

## The steps
1. **Documents** — upload the contract; add multiple files and split a combined scan by page range.
2. **AI Parsing** — the AI extracts everything it can find.
3. **Address & Contacts** — confirm the property and the people (buyers, sellers, agents, lender, title, attorney).
4. **Purchase Info** — price, financing, earnest money, and which side you represent.
5. **Missing Info** — anything the AI could not find is collected here.
6. **Confirm** — the double-check step: the wizard compares its readings and highlights low-confidence or conflicting fields next to an evidence viewer that shows the source document. Edit before you accept.
7. **Timeline** — the milestone dates that will drive your task due dates.
8. **Compliance** — the closing checklist that applies to this deal.
9. **Review Tasks** — the tasks that will be created; adjust before you finish.

If the wizard finds documents that still need signatures, you can send them for e-signature. See [Sending documents for e-signature](/articles/sending-for-signature).

## Why the double-check
The Confirm step is how the platform keeps AI mistakes from slipping through — you are never handed a finished deal you did not review. See [How AI confidence and review work](/articles/how-ai-confidence-works).

#### `active-transactions-workspace` — The transaction list and workspace
*Excerpt:* Triage every deal from the Active Transactions list, then open a deal to run it in its tabbed workspace.

**There are two surfaces: the Active Transactions list (triage) and each deal's workspace (where you work it).**

## The Active Transactions list
Each deal is a card. Collapsed, it shows the client and address, a colored status pill, "why" badges, the AI next-step, a milestone bar, days to close, overdue count, and price. **Click a card to expand it in place** into three columns — **Tasks**, **Key Dates** (edit inline), and **Contacts** (grouped, with call/email). To open the full deal, click through to its workspace.

### Filters and sorting
Tabs across the top, each with a live count: **All, Overdue, Due Today, Needs Attention, Closing Soon, In Inspection, On Track, Unhealthy**. Sort by **Urgency, Close Date, Client Name, or Price**. The **Pending**, **Closed**, and **All Transactions** sidebar links open the same list pre-filtered.

## The deal workspace (`/transactions/:id`)
Opening a deal shows a tabbed workspace:
- **Agent** — the AI assistant for this deal.
- **Timeline** — milestones and dates.
- **Compliance** — required documents and checklist status.
- **Documents** — files on the deal, with e-signature.
- **Tasks** — this deal's task list.
- **People** — the parties and vendors.
- **Activity** — the full, searchable history.
- **Email** — the deal's messages.

(Attorneys open the Attorney Matter Workspace instead.)

## The status pill
The pill is calculated from the deal's tasks, dates, and messages, so risky deals rise to the top: **Critical**, **Needs Attention**, **On Track**, or **Unhealthy**.

#### `transaction-types-and-closing-modes` — Transaction types and closing modes
*Excerpt:* Two settings decide which tasks and documents your deal needs.

**The transaction type and the closing mode shape the whole plan.**

## Transaction type
The type captures which side you represent and how it is financed. The options are buyer or seller (or both) combined with financed or cash — internally `Buy-Fin`, `Buy-Cash`, `Sell-Fin`, `Sell-Cash`, `Both-Fin`, `Both-Cash`. A cash deal skips loan-related steps; a financed one includes them. You can change the type later and Velvet Elves makes targeted updates instead of rebuilding, so completed work is preserved.

## Closing mode
| Mode | What it means |
| --- | --- |
| **Attorney closing** | A closing attorney prepares documents and handles settlement; attorney-specific tasks apply. |
| **Title / escrow closing** | A title or escrow company manages the closing. |
| **Shared approval** | Closing responsibilities are split between parties. |

## For-sale-by-owner deals
FSBO sellers get their own listing-prep and under-contract stages. See [The FSBO customer workspace](/articles/fsbo-workspace).

## Why it matters
Required sign-offs, timing, and the documents a deal needs all flow from these two settings. The mechanics are in [Where your tasks come from](/articles/how-tasks-are-generated).

#### `editing-key-dates` — Editing key dates and milestones
*Excerpt:* Update a milestone in seconds and watch dependent task dates move with it.

**Key dates are the backbone of your task list.** Change one and the deadlines that depend on it shift automatically.

## What counts as a key date
The milestone bar tracks the major moments of a deal — for example Contract, Earnest Money, Inspection Response, Appraisal, Closing Disclosure, Cleared to Close, and Closing. Some carry a time of day, not just a date.

## How to edit a date
Expand the deal card (or open the deal's Timeline tab), click the **pencil** next to a key date, pick the new date and time, and save. Overdue dates show in **red**, and every change is written to the deal's history.

## The ripple effect
Task due dates are calculated from milestone dates, so moving a milestone moves its dependent tasks. Completed tasks stay completed; only still-open dependent dates adjust. After a big change, glance at the affected tasks.

#### `transaction-status-and-history` — Transaction status and history
*Excerpt:* What each status means, and how to use the searchable activity timeline.

**Every deal has a status and a complete, tamper-evident history.**

## The statuses
| Status | Meaning |
| --- | --- |
| **Active** | In progress and on your working list. |
| **Incomplete** | Started but not yet fully set up. |
| **Paused** | Temporarily on hold. |
| **Completed** | Work done, pending final close-out. |
| **Closed** | Closed and moved into history. |

## The activity timeline
The deal's **Activity** tab (and the history panel on the card) shows one combined timeline — messages, task completions, date confirmations, document changes, and AI flags — grouped by day. Search it by keyword to find a specific email, document, or change. The history cannot be edited, which makes it the single source of truth for handoffs, client questions, and audits.

---

### Collection: Tasks & Workflow  `tasks-and-workflow`
Icon Calendar / orange. *Where tasks come from, clearing your queue, adding tasks, reminders, and printing closing checklists.*

#### `how-tasks-are-generated` — Where your tasks come from
*Excerpt:* Your task list is built from rules, the deal type, and the contract dates — not AI guesswork.

**Task generation is deterministic.** The same deal always produces the same plan, so you can trust it.

## The three ingredients
1. **A task-template library** your admins maintain (Settings → Task Templates).
2. **The deal type and closing mode**, which decide which templates apply.
3. **A dependency engine** that sets each due date relative to a milestone, with offsets like "5 days after contract" or "14 days before closing."

## Why AI does not invent tasks
To keep the plan reliable, the AI does not make up tasks at creation time. It helps in safer places: suggesting how to complete a task, drafting emails, and recommending refinements you approve. See [Reviewing AI suggestions](/articles/ai-suggestions).

## Keeping the plan current
Move a date and dependent tasks move ([Editing key dates](/articles/editing-key-dates)); switch the deal type and the plan adjusts without discarding completed work; add one-off work yourself ([Adding a task](/articles/adding-a-task)).

#### `my-task-queue` — Working from My Task Queue
*Excerpt:* One prioritized list of everything due across all your deals.

**My Task Queue pulls every open task from every deal into one screen**, so you work top to bottom instead of opening deals one by one.

## How it is organized
Tasks are grouped by timing — overdue/earlier first, then today, then upcoming — so the urgent ones are unmissable. A progress strip shows today's completions.

## Completing a task
Open a task, mark it complete, and record **how** it was done: Phone Call, Email, DocuSign/E-Signature, In Person, Upload Document, Online Portal, AI Agent, or Other. Recording the method keeps the deal's history accurate for handoffs and audits.

## Pair it with the briefing
The **Today's AI Briefing** tells you which deals are at risk; the queue tells you the exact next actions. For deadline nudges, see [Task reminders](/articles/task-reminders).

#### `adding-a-task` — Adding a task manually
*Excerpt:* Create a one-off task, choose how it will be done, and let AI catch duplicates.

**When something comes up outside the standard plan, add your own task** from a deal (or the queue).

## Create the task
Enter a name, a description, and a due date, and choose a completion method: Phone Call, Email, DocuSign/E-Signature, In Person, Upload Document, Online Portal, AI Agent, or Other.

## Let AI help
The AI can **suggest how** to complete the task, and it **checks for duplicates** — if a similar open task already exists, it offers to add the new one anyway, combine them, or disregard it, so your list does not fill with near-identical items.

## Common questions
- **Will my manual task get reminders?** Yes — the same day-before, due-today, and past-due nudges apply.
- **Repeatable work?** Put it in Task Templates so it appears on every matching deal. See [Task templates](/articles/task-templates).

#### `task-reminders` — Task reminders and notifications
*Excerpt:* Get nudged before tasks slip, bundled into summaries instead of a flood of pings.

**Velvet Elves reminds you before a task slips — in-app and by email — and only when there is something to do.**

## When reminders fire
The day before a task is due, the day it is due, and after it is past due until you handle it.

## Bundled, not noisy
Reminders are bundled into summaries like "3 transactions due tomorrow," and the daily summary email only goes out on days you actually have tasks due. Choose channels and categories in [Notification preferences](/articles/notification-preferences). Team Leads also get escalation prompts when a deadline nears with no activity.

#### `closing-checklists` — Closing checklists
*Excerpt:* Generate print-ready agent and client checklists from your playbook, filled with the deal's details.

**Closing checklists turn your close-out steps into a clean, print-ready sheet, already filled in with the deal details** — one for you and one for your client.

## What is on a checklist
It combines your **My Playbook** (or the shared **Team Playbook**) — closing-checklist templates, tagged notes, preferred vendors, and reference materials — with this deal's key dates.

## How to generate one
From a deal, use **Print Checklist**. Velvet Elves builds both the agent and client sheets from your saved templates.

## Keep your playbook sharp
Update your templates and preferred vendors in **Settings → My Playbook**; admins and team leads standardize them in **Team Playbook** so every agent's checklist is consistent.

---

### Collection: Documents & E-Signature  `documents-and-esignature`
Icon FileText / purple. *Uploading and classifying files, the All Documents center, versions, DocuSign e-signature, and required documents.*

#### `uploading-documents` — Uploading and classifying documents
*Excerpt:* Drop a file and let AI name it, identify it, and file it on the right deal.

**You can drop a document into a deal (or the All Documents center) and the AI files it for you** — it identifies the type, suggests a name, confirms the transaction, and checks whether it needs signing. You confirm each suggestion before it saves.

## Supported files
PDFs, images (JPG/PNG/GIF), and Word documents. Uploaded PDFs and images are OCR'd so their contents are searchable.

## Combined scans
If you scanned several documents into one file, split it into separate documents by page range — naming and typing each — without rescanning.

## Where it goes
Filed documents appear on the deal's Documents tab and in the cross-deal [All Documents center](/articles/all-documents-center).

#### `all-documents-center` — The All Documents center
*Excerpt:* One place to find, search, e-sign, and manage documents across every deal.

**All Documents is one screen for working with files across all your deals.** It complements the Documents tab on each deal.

## Tabs
The page is organized into **All, Missing, Pending review, Sent,** and **Signed**, so you can see at a glance what still needs attention.

## What you can do
Search across every deal (AI-assisted, by name, type, or contents); view, download, rename, and re-type; **email** a document to chosen recipients with a subject, message, and optional template; send for signature; and archive or soft-delete with restore for authorized roles.

## Related reading
- Rollbacks: [Document versions and history](/articles/document-versions).
- What a deal still needs: [Document requirements](/articles/document-requirements).

#### `document-versions` — Document versions and history
*Excerpt:* Replacing a file never deletes the old one — you always have a trail back.

**Velvet Elves keeps every version of a document.** Replace a file and the previous copy moves into version history; the newest becomes current. You can open and compare earlier versions any time.

## Signed copies
When a document comes back signed, the signed version becomes current and the unsigned original is kept in history. See [Sending for signature](/articles/sending-for-signature).

## Safety net
Soft-delete with restore means an accidental delete is recoverable by authorized roles. Clients and FSBO customers cannot delete documents outright — they can flag one for deletion, which routes to an agent or coordinator for approval. Every action is logged.

#### `sending-for-signature` — Sending documents for e-signature
*Excerpt:* Send through DocuSign, track who has signed, and let the finished copy distribute itself.

**Velvet Elves sends documents for signature through DocuSign** and handles the finished copy. You can start from the document center, a deal's Documents tab, or the wizard.

## How to send
Open the document, choose **Send for signature**, add the signers and who receives the completed copy, then send and track the status on the deal.

## When it comes back signed
The signed version replaces the original (the unsigned copy stays in history), and the completed document is distributed to the right people by naming rules — for example, purchase agreements and amendments go to all parties.

## Not connected yet?
If your DocuSign account is not connected, Velvet Elves prompts you to connect it (Settings → Email & E-signature). You only do this once.

#### `document-requirements` — Document requirements and missing documents
*Excerpt:* See exactly which documents a deal needs and what is still outstanding.

**Each deal keeps a list of required documents, built from the deal type and its contingencies** — not from memory. You can see it on the deal's Compliance tab and the All Documents **Missing** tab.

## How a requirement clears
A requirement's status is **Missing**, **Uploaded**, or **Waived**. It clears when the matching document is uploaded (and, where relevant, verified or returned signed) or when it is waived with a reason. A "cleared today" view shows recent progress.

## For admins
Admins maintain the requirement library and can upload their own fillable-PDF **Document Templates** (Settings → Document Templates); the platform fills those forms with the deal's details and flattens them at generate time, so you do not retype.

---

### Collection: Email & Communication  `email-and-communication`
Icon Mail / blue. *Connect your inbox, let AI draft replies you approve, keep a searchable record, use templates, and coordinate vendors.*

#### `connecting-your-email` — Connecting your email
*Excerpt:* Link Gmail or Outlook once so messages file themselves and drafts send as you.

**Connecting your inbox is the step that makes communication effortless.** Once linked, Velvet Elves files conversations on the right deal and can send as you.

## How to connect
Open **Settings → Email & E-signature**, choose **Gmail** or **Outlook**, and sign in through the secure provider popup to grant send/receive access. (DocuSign connects from the same page.)

## What it unlocks
Automatic filing of related email onto the matching deal, [AI-drafted replies you approve](/articles/ai-email-drafts), and one-click resend from the deal's Email tab.

## Your privacy
Only messages related to your transactions are attached to deals, and the log follows your organization's retention policy. You can disconnect any time from the same page; already-filed messages stay on their deals.

#### `ai-email-drafts` — AI email drafts and auto-responses
*Excerpt:* AI drafts routine replies and escalates anything uncertain, so nothing risky goes out alone.

**The AI drafts replies to routine emails for you to review** and is built with guardrails — anything it is unsure about comes to you instead of sending on its own. Review pending drafts under **Intelligence → AI Email Review**.

## What it can draft
Common messages from clients, FSBO customers, and vendors — document requests and factual questions about closing dates, status, and milestones. A person is always kept in the loop.

## The rules it follows
- If a requested document exists, it drafts the reply and attaches it.
- If something is missing or it is unsure, it does not send — it notifies the owner with a draft to finish.
- Any assumption in a draft is shown in **bold**, with an Approve or Edit-and-Send control and a side-by-side view against the source.

The AI uses your configured tone, never gives legal advice, and adds a disclaimer where appropriate.

#### `communication-log` — The communication log
*Excerpt:* A searchable, tamper-evident record of every message on a deal.

**Every message is recorded: who, what, when, direction, and which deal.** Because the log cannot be edited, it is a record you can rely on.

## Where to find it
On a deal, the **Email** and **Activity** tabs; across deals, admins and team leads use **Oversight → Communication Audit** to review and export.

## Searching and exporting
Filter by date, party, or keyword. You can export a single transaction's log; admins can request a multi-transaction export from the audit page. Logs follow your organization's retention policy.

> Email is logged today; the channel model also supports SMS, voice, notes, and document actions as they come online.

#### `email-templates` — Email templates
*Excerpt:* Reusable messages with placeholders that fill in the deal details for you.

**Templates let you send consistent, on-brand email without retyping the basics.** Placeholders fill in the deal's details, like the property address and closing date.

## Using and managing templates
When you compose (for example to send a document), pick a template and review the filled-in message before sending. Create and edit templates in **Settings → Email Templates**; the editor shows the available placeholder tokens. (Available to Agent, TC, Team Lead, and Admin.)

## Vendor templates
Vendor outreach uses **Vendor Templates** (Settings → Vendor Templates) that request a structured reply, so the AI can read the response and update task dates. See [Vendor communication](/articles/vendor-communication).

#### `vendor-communication` — Vendor communication and scheduling
*Excerpt:* Email vendors with structured templates and let AI turn replies into task dates you approve.

**Velvet Elves coordinates vendors with structured emails and reads their replies for you.** A scheduling reply comes back and the AI proposes an updated task date for you to approve — review these under **Intelligence → Vendor Proposals**.

## Structured outreach
Vendor templates ask for a reply in a fixed format, with categories for inspection, appraisal, title, and general scheduling, so responses are easy to parse.

## Reading replies
The AI pulls the date and proposes a task-date update; vague replies are flagged for clarification rather than guessed. Each vendor assignment has a contact card with clear actions, and a vendor can loop in a colleague on a single thread through a secure, single-use link. See [Vendor contact cards](/articles/vendor-contact-cards).

---

### Collection: AI Assistant & Intelligence  `ai-and-intelligence`
Icon Sparkles / orange. *The AI assistant, reviewing suggestions, analytics, and how the AI checks itself.*

#### `meet-the-ai-assistant` — Meet the Velvet Elves AI assistant
*Excerpt:* A chat assistant that already knows the deal you are on.

**The AI assistant is a chat panel that understands your context.** Open it from the floating button anywhere, or the **Agent** tab inside a deal, and ask in plain language.

## What you can ask
Things like "Show overdue tasks," "Draft the inspection response," or "Summarize the Young deal." The **Today's AI Briefing** button also opens it with a ready-made briefing prompt.

## It acts, not just answers
Along with its answer, the assistant offers **suggested actions** you can take in one click — open a filtered list, start a draft, and so on. Some answers, like an exact closing date, come back in a precise fixed format. The final decision, and the send button, stay with you.

#### `ai-suggestions` — Reviewing AI suggestions
*Excerpt:* Recommendations with a reason attached — nothing changes until you approve.

**AI suggestions are recommendations, not actions.** Each comes with a reason and a source, and nothing changes until you say yes.

## Where they show up
An AI suggestions strip on deal cards, and a dedicated view under **Intelligence → AI Suggestions**. A suggestion might propose a task, flag a gap, or recommend a next step.

## Approving or dismissing
Read the reason and source, then approve or dismiss. Dismissed suggestions can be restored. Team Leads can bulk-approve across the team with a preview first. After a deal closes, you can mark suggestions and tasks as useful, unnecessary, or missing to tune future recommendations.

#### `analytics-and-reporting` — Analytics and reporting
*Excerpt:* Turn your activity into numbers — completion, pipeline, and deal trends.

**Analytics live under Intelligence → Analytics** (and your personal reports at `/analytics?scope=me`).

## What you can see
Task-completion rates and where work piles up, pipeline value (the total of active purchase prices), and transaction metrics like closings over time and active-deal counts. Search and sort to focus on a range, a client, or a stage. Team Leads see team-wide rollups and can drill into any agent.

## Putting it to use
Pair analytics with the daily briefing: the briefing tells you what needs attention now, analytics show the trend behind it.

#### `how-ai-confidence-works` — How AI confidence and review work
*Excerpt:* The AI double-checks itself and routes anything uncertain to a person.

**Velvet Elves is built so the AI assists but people decide.**

## The double-check
When the AI reads a document it runs two passes and compares key fields. Where they agree, you move quickly; where they disagree or confidence is low, the field is flagged for you to confirm against the source (the wizard's Confirm step).

## Confidence thresholds
Admins set a global minimum confidence floor and team leads can set higher thresholds (Settings → AI & Automation). Anything below the threshold goes to human review rather than being applied automatically.

## Guardrails on legal work
For legal work the AI may compare versions, pull deadlines, and draft language, but it must not decide legal equivalence, release a packet, or approve same-day disbursement exceptions — those stay with a human.

## Which AI is used
Your administrator chooses the AI provider (Settings → AI & Automation) and the platform uses exactly that provider — it never silently switches to another.

---

### Collection: Contacts, Parties & Vendors  `contacts-and-vendors`
Icon Users / green. *Contacts, the parties on a deal, the vendor directory, and vendor contact cards.*

#### `adding-contacts` — Adding and managing contacts
*Excerpt:* Save the people in your business once, then reuse them across deals.

**Contacts are the people in your business — clients, co-agents, and service providers.** Save someone once (company, name, phone, email) and reuse them. Add a contact from inside a deal and it links to that deal immediately. Editing a contact updates it everywhere it is linked.

## How contacts relate to parties and vendors
A **party** is a contact in their role on a specific deal ([Transaction parties](/articles/transaction-parties)); a **vendor** is a saved provider you reuse ([The vendor directory](/articles/vendor-directory)).

#### `transaction-parties` — Transaction parties
*Excerpt:* The buyers, sellers, agents, lender, title, and attorney on a deal — mostly captured by AI.

**Parties are everyone involved in one deal**, and most are captured automatically when the AI reads your contract.

## Who counts
Buyers and sellers, the agents, the loan officer, the title rep, and the closing/settlement attorney when there is one. They appear on the deal's **People** tab and as grouped contact cards with call/email actions. Add or correct a party any time.

## Parties vs. the vendor directory
A provider acting as a party is not automatically a saved vendor. To reuse them, **save the party as a vendor**. See [The vendor directory](/articles/vendor-directory).

#### `vendor-directory` — The vendor directory
*Excerpt:* Your reusable, searchable table of inspectors, lenders, title reps, and other providers.

**The Vendor Directory (sidebar → Vendors) is your saved list of providers**, shown as a searchable, filterable table. Open a vendor to see their details and connected transactions in a modal.

## Adding vendors
Save a provider directly into the directory, or save a service-provider **party** from a deal into the directory so they are ready next time.

## Note
Not every provider on a deal is in your directory — a provider can be a party without being a saved vendor until you save them.

#### `vendor-contact-cards` — Vendor contact cards and colleague invites
*Excerpt:* Manage a vendor on a deal from one card, and let them loop in a colleague safely.

**Each vendor assignment has a contact card with explicit action buttons**, and one contact is marked **primary**.

## Colleague invites
A vendor can invite a colleague (like a scheduler) onto **one thread only** through a secure, single-use, expiring link — never your whole workspace.

## Keeping vendor info fresh
For saved vendors, a background search can offer updates to their details as suggestions you accept or reject field by field, so nothing changes without your say-so.

---

### Collection: Client & FSBO Portals  `client-and-fsbo-portals`
Icon Building2 / neutral. *Read-only progress for buyers/sellers and a simplified workspace for FSBO sellers.*

#### `sharing-milestones` — Sharing milestones with clients
*Excerpt:* Send a read-only progress link that expires, and get told when it is opened.

**Share a deal's progress through a secure, read-only milestone link.** From a deal, create a share link, set an expiry, and share it; you are notified when it is opened. Track live links and revoke any of them at any time from the **Sharing** page.

## What the viewer sees
Only the milestone timeline and key dates — never your tasks, notes, or other deals. For ongoing access to documents and messages too, use the full client portal instead. See [What clients see](/articles/client-portal).

#### `client-portal` — What clients see in the client portal
*Excerpt:* A clean view of milestones, documents, messages, and invoices — nothing internal.

**The client portal gives your buyer or seller a friendly "closing concierge" view.** Its own navy shell (not the internal app) has Home, Timeline, Documents, Payments, and Agent Info.

## What is in it
Milestones in plain language, documents to review or provide (each with a status), messages tied to the deal, invoices to pay online, and an agent bio. Clients manage their own notification preferences; you control what is shared, from inside the deal. Clients cannot delete a document outright — they can flag one for deletion, which routes to an agent or coordinator for approval.

#### `fsbo-workspace` — The FSBO customer workspace
*Excerpt:* A simplified, property-focused workspace for sellers handling their own sale.

**The FSBO workspace is a simplified space for sellers running their own sale.** Its sidebar has My Properties, Documents, Payments, and Messages, plus a persistent action banner surfacing the top next step.

## What it includes
A property portfolio (status, closing date, missing docs, new messages), document upload and tracking, plain-English milestone guidance, invoices, and read-only milestone sharing (footer "Share milestones" CTA). It supports both listing-prep and under-contract stages.

## Where the line is
Guidance is plain-English and glossary-style. Velvet Elves coordinates the workflow but does not act as the customer's agent and does not give legal advice — stated clearly in the workspace.

#### `portal-notifications` — Portal notifications and privacy
*Excerpt:* How customers control their alerts, and exactly what stays private.

**Clients and FSBO customers control their own notifications, and your internal workflow is never exposed to them.** From their portal settings they turn alerts on or off. Milestone share links carry an expiry and notify you when opened, and you can revoke access any time. Shared viewers see only milestones, shared documents, and messages — never your tasks, notes, or other deals. Document-deletion requests route to an agent or coordinator, and every action is logged.

---

### Collection: Payments & Billing  `payments-and-billing`
Icon CreditCard / green. *Collect fees through Stripe, send invoices clients pay online, and track payments and refunds.*

#### `collecting-payments` — Collecting payments with Stripe
*Excerpt:* Take card payments securely through Stripe, with access controlled per role.

**Velvet Elves collects client-facing payments through Stripe**, so card details are handled securely and never by you directly. The **Payments** sidebar group holds **Invoices & Payments** (and **Commission Payouts** if you can trigger payouts).

## Who can collect
Admins control payment capabilities per role in **Settings → Payment Access** (invoice, refund, payout). If you do not see an action, your role may not include it — all internal roles can at least view history.

## Note on billing vs. payments
Client-facing invoicing (this collection) is separate from your workspace's own **Billing & Credits** (the credit wallet in Settings → Billing & Credits).

#### `creating-invoices` — Creating and sending invoices
*Excerpt:* Bill a specific amount, send it, and let the client pay online.

**Invoices let you bill an exact amount and get paid online.** Create an invoice from **Invoices & Payments** (or from a deal card), tied to the relevant transaction, send it to the payer, and they pay securely through Stripe. The status moves from outstanding to paid automatically, and the activity is recorded on the deal. Clients and FSBO customers see and pay their invoices under **Payments** in their portal.

#### `tracking-payments` — Tracking payments and refunds
*Excerpt:* A clear record of what was paid, refunded, and still outstanding.

**The Invoices & Payments view shows payments, refunds, and history in one place**, with detail drawers for each invoice and payment. Payment data flows into your dashboards and reports. What you can view or do depends on the payment access your admin granted your role; refunds (for roles with access) show in the history here.

---

### Collection: Admin & Settings  `admin-and-settings`
Icon Settings / neutral. *Managing your team, the Settings hub, users and roles, task templates, branding, and notifications.*

#### `managing-your-team` — Managing your team
*Excerpt:* For team leads: see the whole pipeline, step into any agent, and keep one playbook.

**Team Leads run the team from a team-wide dashboard and the Team group.**

## The team view
Team-wide KPI tiles and briefing counts, a filter by team member, assignee names on every card, and an **intervention queue** ranking the deals most likely to go sideways. The **Team → Team Overview** page reviews people and production; **Team → Teams** builds and runs teams and invites members.

## Keeping everyone consistent
Shared configuration lives in the Settings hub: **Users & Invites**, **Task Templates**, **Vendor Templates**, and the **Team Playbook** every member inherits.

#### `user-management` — User management and roles
*Excerpt:* For admins and team leads: invite people, assign roles, and manage access.

**Invite people and set what they can do in Settings → Users & Invites** (Team Lead, Admin, or owner).

## Inviting users
Invite by email and assign a role; they receive a secure link to set up their account. See the recipient's side in [Signing in](/articles/signing-in-and-your-account).

## Choosing the right role
Assign the role that matches the job — Agent, Transaction Coordinator, Team Lead, Attorney, or Admin. The role decides what they see and do. See [Understanding roles](/articles/understanding-roles).

## AI thresholds
Admins set the global AI confidence floor and team leads can raise it for their team in **Settings → AI & Automation**. See [How AI confidence works](/articles/how-ai-confidence-works).

#### `task-templates` — Configuring task templates
*Excerpt:* Maintain the master library and the rules that build every task plan.

**Task Templates (Settings → Task Templates) are the library that powers deterministic task generation.**

## What you configure
Task definitions, dependencies and float (how each due date is offset from a milestone), which transaction types and closing modes each task applies to, and automation flags. A visual rule builder sets up dependencies without code.

## Why it matters
Because [task generation](/articles/how-tasks-are-generated) is deterministic, well-maintained templates mean every new deal starts with the right tasks on the right dates.

#### `white-label-branding` — White-label branding
*Excerpt:* Put your brokerage logo, color, and name across the product and customer-facing screens.

**Admins brand the product in Settings → Branding** (and Company): upload a logo, set a brand color, and set the display name shown across the app.

## Where it shows up
Branding flows across sign-in, the dashboards, email, documents, and the customer-facing client and FSBO surfaces, so clients see one consistent identity. Changes apply right away.

#### `notification-preferences` — Notification preferences
*Excerpt:* Choose exactly which alerts you get and where, including the daily summary.

**You choose your notifications in Settings → Notifications.** Pick in-app and email channels for reminders and assignment alerts, and turn categories on or off. The daily summary email only goes out on days you have tasks due; reminder timing (day before, day of, past due) is configurable. Clients and FSBO customers manage their own preferences in their portals. See [Task reminders](/articles/task-reminders).

> The full Settings hub also includes Email Templates, My Playbook, Help & Tour (personal); Company, Billing & Credits, Document Templates, Integrations & Webhooks, Payment Access, and Advertising (workspace); and Platform Billing / Advertising for platform admins.

---

### Collection: Tips, FAQ & Troubleshooting  `tips-and-faq`
Icon BookOpen / purple. *Quick answers, plain-English definitions, fixes, time-savers, and how to reach a human.*

#### `frequently-asked-questions` — Frequently asked questions
*Excerpt:* Quick answers to the questions new users ask most.

**What is Velvet Elves in one sentence?** You upload a contract and it sets up and runs the whole transaction for you. See [What is Velvet Elves?](/articles/what-is-velvet-elves).

**How do I sign in the first time?** Accept the email invitation from your team and set a password. See [Signing in](/articles/signing-in-and-your-account).

**What is a "TC"?** A Transaction Coordinator — the person who keeps paperwork and deadlines moving. See [Understanding roles](/articles/understanding-roles).

**How do I start a deal?** Click **+ New Transaction** and use the wizard — upload a contract or enter the basics. See [Creating a transaction](/articles/creating-a-transaction).

**Where do my tasks come from?** From templates, the deal type, and the contract dates — not AI guesswork. See [Where your tasks come from](/articles/how-tasks-are-generated).

**I changed a closing date — do I fix every task?** No. Dependent task dates move automatically. See [Editing key dates](/articles/editing-key-dates).

**Will the AI email my clients without me?** Only routine, factual replies, and it always keeps a person in the loop; anything uncertain waits for you in AI Email Review. See [AI email drafts](/articles/ai-email-drafts).

**Does the AI change my deals on its own?** No — it suggests, you approve. See [Reviewing AI suggestions](/articles/ai-suggestions).

#### `glossary-of-terms` — Glossary: real estate and Velvet Elves terms
*Excerpt:* Plain-English definitions for the words around the app.

## App terms
| Term | What it means |
| --- | --- |
| **Transaction Coordinator (TC)** | The role that manages paperwork and deadlines across deals (labeled "Transaction Coordinator" in the app). |
| **Transaction (deal)** | A single property sale you manage from contract to closing. |
| **Workspace** | The role-specific screens where you work; also each deal's tabbed page at `/transactions/:id`. |
| **AI briefing** | The top-bar summary sorting deals into Critical, Needs Attention, and On Track. |
| **Status pill** | The colored label on a deal (Critical / Needs Attention / On Track / Unhealthy). |
| **Milestone / key date** | A major date in a deal, like inspection response or closing. |
| **My Task Queue** | One combined list of everything due across all your deals. |
| **Completion method** | How a task was done: phone, email, DocuSign, upload, and so on. |
| **Party** | A person in their role on a specific deal. |
| **Vendor** | A saved service provider you reuse across deals. |
| **Playbook** | Your (or the team's) closing-checklist templates, tagged notes, preferred vendors, and resources. |
| **Portal** | The limited view a client, FSBO seller, or vendor sees. |
| **Tenant / workspace** | Your brokerage's own account and data. |
| **Credit wallet** | Prepaid credits used for per-transaction billing (Settings → Billing & Credits). |

## Real estate terms
| Term | What it means |
| --- | --- |
| **Contingency** | A condition that must be met for the deal to proceed. |
| **Earnest money** | A deposit the buyer puts down to show they are serious. |
| **Closing disclosure** | The final statement of loan terms and costs before closing. |
| **Cleared to close** | The lender has approved everything and the deal can close. |
| **Closing mode** | How a deal closes: attorney, or title/escrow, or shared approval. |
| **FSBO** | For Sale By Owner — a seller handling their own sale. |
| **Title / escrow** | A neutral third party that manages closing and holds funds. |
| **Disbursement** | Releasing the funds at or after closing. |

#### `troubleshooting-common-issues` — Troubleshooting: common issues and fixes
*Excerpt:* Quick fixes for the snags people hit most.

**I cannot sign in.** Use **Forgot password**; if the reset link is old, request a fresh one. Still stuck — your account may not be set up; ask your admin.

**My file will not upload.** Use a PDF, image, or Word document. Try a fresh upload or a different browser. See [Uploading documents](/articles/uploading-documents).

**The AI read my contract wrong.** Edit the field — nothing is final until you confirm on the wizard's **Confirm** step. Highlighted fields are exactly the ones it was unsure about.

**A vendor replied but the date did not update.** A vague reply is flagged for clarification, not guessed. Open **Intelligence → Vendor Proposals** and confirm the date.

**Emails are not attaching to deals.** Make sure your inbox is connected in **Settings → Email & E-signature**. Only messages related to your transactions attach, by design.

**Too many or too few notifications.** Adjust channels and categories in **Settings → Notifications**.

**I cannot find a feature this help center describes.** It may not be part of your role. See [Understanding roles](/articles/understanding-roles).

#### `tips-and-shortcuts` — Tips to work faster
*Excerpt:* Small habits that save real time.

**Start with the briefing.** Open **Today's AI Briefing** first and decide where your morning goes in ten seconds.

**Work the queue, not deal by deal.** [My Task Queue](/articles/my-task-queue) gathers everything due into one list.

**Search instead of clicking.** Press ⌘K — search spans clients, vendors, companies, addresses, and dates.

**Let AI do the first draft.** Let the wizard read contracts, let AI draft routine replies (you approve in AI Email Review), and ask the assistant to summarize a deal or pull up overdue tasks.

**Set up once.** Connect your email, keep your **My Playbook** templates and preferred vendors current, and tune your notifications.

#### `getting-support` — Getting more help and contacting support
*Excerpt:* Where to look first, how to ask the AI, and how to reach a human.

1. **Search this help center** — the search box spans every article by title and content.
2. **Ask the AI assistant in the app** — open the floating panel (or a deal's Agent tab) and ask in plain language.
3. **Check troubleshooting and the FAQ** — [Troubleshooting](/articles/troubleshooting-common-issues) and [FAQ](/articles/frequently-asked-questions).
4. **Ask your admin or team lead** — for anything account-specific (your role, permissions, whether a feature is enabled).
5. **Contact support** — use the contact/chat option in the help center. Include what you were trying to do, what happened instead, and the deal or screen where it happened.

At the bottom of every article you can mark whether it helped; that feedback is read and used to improve these articles.

---

## Part 3 — Curated related links (unchanged pairs, all slugs preserved)

The related-link graph from the prior migration still applies (every slug here matches). The companion SQL re-inserts it with `ON CONFLICT DO NOTHING`.
