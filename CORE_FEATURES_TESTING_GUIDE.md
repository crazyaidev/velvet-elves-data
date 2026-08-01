# Core Features — Testing Guide

**Prepared by:** Jan (sole developer)
**Date:** July 31, 2026
**For:** Audri and Jake
**Where to test:** the stage site — `https://app.stage.velvetelves.com`
**Browser:** Chrome or Edge. Please allow pop-ups and downloads.
**Companion documents:** `CORE_FEATURES_TESTING_CHECKLIST.md` (tick-box version of this guide) and `todo_list.md` (what is deliberately **not** in this round)

---

## Before you start

### What this round covers

This is the **core of the product** — the screens you would live in every day
running real deals. It covers everything from signing in through to closing a
file: the deal list, the deal workspace, tasks, documents, email, calendar,
people, settings, and the team and admin screens behind them.

**The New Transaction wizard is deliberately not in this round.** You have
already been through three rounds on it and it has its own guide. Here, when a
step says "create a deal", just run the wizard the way you normally would and
carry on — we are testing what happens **after** it, not the wizard itself.

Also not in this round, and covered later: the Client, FSBO and Vendor portals,
the Attorney workspace, the public links (milestone viewer, invoice payment,
advertising storefront), and the internal Velvet Elves platform screens.

### What we are asking you for

Not a bug hunt. We want to know whether this **works the way a real transaction
works**. The most useful feedback is usually one of these four sentences:

- "This is not how a deal actually goes."
- "I would never send that to a client."
- "I still had to do this by hand."
- "I could not find where to do X."

### How to report something

Please tell us:

- **Where you were** — the page name is enough ("My Task Queue")
- **What you did** — "clicked Send & complete task"
- **What you expected**, and **what happened instead**
- **The property address** on the deal, so we can find it
- A screenshot if it is quick

You do not need to diagnose it. "This felt wrong" is a useful report.

### Two things to know up front, because they explain most of what you will see

1. **Nothing is emailed to a client without a person pressing send.** The one
   exception is the small set of tasks marked *Automated* in the task database —
   the AI sends those itself and ticks the task off. Everything else waits for
   you.
2. **The AI does not act overnight yet.** It reacts to things you do — creating
   a deal, uploading a document, pressing a button. The hourly timer that would
   let it work an old deal on its own is not switched on. Please do not report
   that as a bug; it is item A1 in `todo_list.md`.

### Accounts

| Account | What it unlocks |
|---|---|
| **Agent** or **Transaction Coordinator** | The whole day-to-day workflow. Start here. |
| **Team Lead** | Team Overview, Teams, the team-member filter on the deal list, Task Templates. |
| **Admin** or workspace owner | The Workspace settings cards, Audit Log, Communication Audit, AI & Automation, Delete Organization. |

If you only have one account, use the Admin one — it sees everything. Where a
step needs a specific role, it says so.

---

## Part 1 — Getting in

### 1.1 Create an account

1. Go to `/register`.
2. Fill in **Full name**, pick a **Role**, optionally an **Organization**, then
   **Email**, **Password**, **Confirm password**, optionally **Phone**, and tick
   the Terms / Privacy box.

**Expect:**

- The **Role** dropdown offers **Agent**, **Team Leader**, **Transaction
  Coordinator**, and **Admin**. It sets up your workspace for how you work, and
  you can change it on the next screen.
- Typing an email that is already in use blocks **Create account** and offers a
  "sign in instead" link.
- A weak password tells you which rules are still unmet, and mismatched
  passwords block the button.
- Typing a brokerage name in **Organization** creates a **new** workspace with
  you as its admin. It does **not** join you to an existing brokerage — for that
  you need an invite link.
- There is also a **Google** button that signs you up with your Google account.

**Worth reporting:** a role in the list that does not match how your office is
organised; the Organization wording being unclear about creating vs joining.

### 1.2 Onboarding

After you register you land on a short setup flow.

**Expect:** it asks for your name and phone, lets you confirm or change your
role, and — if you are the first person in a new brokerage — asks for your
company name and lets you upload a logo. It then offers to connect **Gmail**,
**Outlook** and **DocuSign**.

You can skip the connections here and do them later in Settings.

### 1.3 Sign in, sign out, and forgotten passwords

1. Sign out from the avatar menu (top right) → **Log Out**.
2. Sign back in at `/login`.
3. Try **Forgot password?** and follow the email through.

**Expect:** signing out returns you to the sign-in page and a protected page
like `/dashboard` sends you back to sign-in if you paste it in while signed out.

**Please note:** there is **no way to change your password from inside the
app** yet. Use "Forgot password?" on the sign-in page. This is item B2 in
`todo_list.md` — no need to report it.

---

## Part 2 — The shape of the app

Spend two minutes here before testing anything. It will save you time later.

### 2.1 The left sidebar

**Expect** these groups (what you see depends on your role):

| Group | Entries |
|---|---|
| — | **Dashboard** |
| **Deals** | Active Transactions · Pending · Closed · All Transactions · Clients |
| **Workflow** | Needs You · My Task Queue · All Documents · Closing Calendar |
| **Payments** | Invoices & Payments · Commission Payouts (payout permission only) |
| **Vendors** | Vendor Directory |
| **Intelligence** | AI Suggestions · **Email** · Vendor Proposals · Analytics |
| **Team** (Team Lead / Admin) | Team Overview · Teams |
| **Oversight** (Admin) | Communication Audit · Audit Log |
| — | **Settings**, at the bottom |

Orange or red numbers next to an entry are live counts — overdue tasks, items
waiting on you, drafts to read.

> **A naming change worth knowing:** what used to be called *AI Email Review* is
> now simply **Email**, because that screen now carries incoming mail as well as
> outgoing drafts. If you have an older document that says "AI Email Review",
> it means this.

### 2.2 The top bar

**Expect:**

- **Today's AI Briefing** on the left, with **Critical**, **Needs Attention**
  and **On Track** counts beside it. Clicking a count filters the deal list to
  exactly those deals; clicking the briefing itself opens the AI.
- A **search box** (or ⌘K / Ctrl+K) that searches transactions, tasks, contacts
  and documents.
- A **bell** with your unread count.
- Your **avatar**, which opens Settings, the Help Center, and Log Out.
- **+ New Transaction** on the far right.

**Worth reporting:** a count in the briefing bar that does not match what you
find when you click it.

### 2.3 Your dashboard

**Expect** a different landing page depending on your role — a solo agent view,
a team-leader view, or an admin view. Each one leads with what needs deciding
today, then pipeline health, then quick links.

**Worth reporting:** numbers on the dashboard that disagree with the same
numbers elsewhere in the app; a section you would never look at.

**Already known:** the solo-agent dashboard carries an **"Add the AI Real
Estate Coach"** promotion. That is a future paid add-on and its buttons do
nothing yet (item B3 in `todo_list.md`).

---

## Part 3 — Connect your mailbox

**Do this before Parts 8 and 9.** Nothing outbound works until it is done,
because the AI sends from **your** mailbox, not from a Velvet Elves address.

1. Go to **Settings → Email & E-signature**.
2. Next to **Gmail** (or **Outlook**), click **Connect** and sign in.
3. Google will warn you the app is not verified. That is expected — we are in
   Google's review queue. Continue through the warning.
4. Back in Velvet Elves, click **Test connection**.

**Expect:** the provider shows **Connected** with your address, and Test
connection reports *"Connected as &lt;your address&gt;"* without sending anything.

**Also on this page:** **DocuSign**, which you need before Send for Signature
works on the Documents screen.

### The weekly reconnect — please expect this

Until Google finishes verifying the app, **your connection will expire roughly
every week**. You will see **Expired — reconnect**. Click **Connect** again and
anything the AI was holding goes out afterwards.

**Worth reporting:** the connection expiring much more often than weekly; Test
connection saying it is fine when sending then fails; being **signed out of
Velvet Elves** instead of being told to reconnect.

---

## Part 4 — The deal list

Open **Active Transactions**.

### 4.1 The list itself

**Expect:**

- A **deal count** beside the title.
- Filter tabs: **All · Overdue · Due Today · Needs Attention · Closing Soon ·
  In Inspection · On Track · Unhealthy**, each with a count. Overdue and Due
  Today count in red.
- A **Sort by** control offering **Urgency**, **Close Date**, **Client Name**
  and **Price**.
- **Export CSV**, **Export Excel** and **Print Report** buttons.
- A **team-member filter** if you are a Team Lead (All Team Members / My
  Transactions / Unassigned / each member).

The **Pending**, **Closed** and **All Transactions** entries in the sidebar are
the same page filtered to those states. Those views have no filter tabs — that
is intentional.

**Worth reporting:** a deal in the wrong tab; a tab count that does not match
the rows; a sort that is not how you would prioritise.

### 4.2 The deal card

Click a card to expand it.

**Expect** three columns — **Tasks**, **Key Dates** and **Contacts** — plus an
invoices section and, where the AI has something to offer, a strip of suggested
actions for that deal.

Inside the card you can:

- tick a task complete, or open **View all** for the full task list
- edit a key date in place
- call or email a contact directly, or add a missing one
- open the AI on a suggestion

Along the bottom: **Open workspace**, **View/Add Docs**, **Print**,
**History**, **Comms**, **Client access**, **Client Q&A**, **Invoice**, and —
for Team Lead and Admin — **Delete**.

**Worth reporting:** contacts filed under the wrong heading; a key date you
cannot edit; the card showing a different number of tasks than the workspace.

---

## Part 5 — One deal: the workspace

Click **Open workspace** on any deal, or click through from anywhere else in
the app. This is where a deal actually gets worked.

### 5.1 The header

**Expect** the property, the stage it is in, its address, how far through the
task list it is, and a **status** control offering Active / Incomplete / Paused
/ Completed / Closed. Moving a deal to **Closed** asks you to confirm and then
asks for post-closing feedback.

Below that is the deal's **automation setting** — how much this particular deal
is allowed to do without you.

### 5.2 The AI assistant

On a wide screen the assistant sits **beside** your work as a permanent panel.
On a laptop or tablet it becomes its own **Agent** tab. The panel button in the
header hides and shows it, and it remembers your choice.

Try:

1. Ask it something about the deal in plain English.
2. Use **/** for commands, **@** for people on the deal, **#** for items.
3. Drag a task or document row into it, or use the **Ask AI** button on a row.
4. When it proposes something, read the preview and **Approve** or **Dismiss**.

**Expect:** the assistant never changes anything by itself — every change is a
proposal you approve. When you approve one, the tab that owns it updates so you
can see the result. Clicking a reference it mentions jumps you to that row.

**Worth reporting:** a proposal you would not have approved being described as
safe; the assistant claiming it did something you cannot find; an answer that
invents a date or a fact.

**Already known:** the microphone button is switched off ("coming soon") — typing
works fully.

### 5.3 The tabs

| Tab | What to check |
|---|---|
| **Timeline** | The dates and deadlines the contract produced. Change a key date — you should see **what else moves** before you apply it. Are the derived deadlines what you would have written? |
| **Compliance** | The document checklist. Attach an existing file, upload a new one, or mark a row **not applicable**. Each fresh upload gets checked by the AI, which tells you if it read the document as something other than what the row asked for. |
| **Documents** | Every file on the deal. Upload from the button, or **drag a file anywhere on the page**. The AI analyses it and reports in the assistant. |
| **Tasks** | Overdue / Due Today / Upcoming / Completed, plus a collapsed **Handled by AI** group. Each task shows why it is due when it is due. **Email transaction party** is the action that finishes most of them. |
| **People** | Everyone on the deal, grouped by side and role. Add or edit a party, assign a teammate, manage a client's portal access, and see the deal's fees. |
| **Activity** | Two lenses: **History** (everything that happened, including "Closing moved — 6 deadlines recomputed") and **Automation** (strictly what ran without a click, with **Undo** where possible). |
| **Email** | This deal's **Outbox** and **Inbox**. |

**The most valuable questions in this part:**

- Are the **tasks** the right ones for this kind of deal? Is anything missing
  that you would always do? Is anything there you would never do?
- Are the **dates** right against the contract?
- On a task that says **"Waiting on an earlier step"** instead of a date — do
  you agree it should be waiting?
- On a task badged amber **"AI needs you"** — is the reason it gives clear
  enough for you to fix it?

---

## Part 6 — Needs You

This is the single list of everything the system cannot do without a person.

**Expect** five groups across the top, each clickable as a filter:

| Group | What it is |
|---|---|
| **Ready to send** | An email already approved, waiting for the tap. |
| **To approve** | Something the AI wants to change on a deal. |
| **To review** | A drafted email nobody has read yet. |
| **To decide** | A question about the deal that is holding tasks back. |
| **To handle** | One of the AI's own tasks that it could not finish safely. |

Where the list allows it you also get **Send all ready (N)** and **Approve all
safe (N)** at the top.

Try each kind: answer a decision, approve a proposal, open a draft, and — on a
blocked AI task — read the reason and fix the cause on the deal.

**Expect:** answering a decision immediately updates the tasks it was gating.
A blocked AI task clears itself once you fix the cause, next time that deal is
touched.

**Worth reporting:** an item here that is not really a decision for a person; a
decision whose two options do not cover what actually happened; **Send all
ready** listing something you would not send.

**Already known:** a blocked AI task has no "Try again" button (item A2).

---

## Part 7 — My Task Queue

Everything across all your deals, in one list.

**Expect:**

- A badge reading *N open · N critical*.
- Today's AI briefing, with a **Draft run order** button.
- Four counters — **Critical**, **Attention**, **On track**, **Done today** —
  each one a filter when clicked.
- Type tabs: **All · Documents · Communication · Milestones · Admin**.
- A **Priority / Vendor** grouping toggle, a sort control, and a search box.
- **Add task**.

Expand a task and you get:

- its notes, and an **AI Assistance** box with **Draft with AI**
- the main action for that task
- **Email transaction party** — the action that actually closes most tasks
- **Mark task complete**
- the contacts for that task, with **Call** and **Email**
- reschedule: a date field plus **Tomorrow**, **In 3 days**, **Next week**

### The task email flow

Click **Email transaction party**.

**Expect:** a window that already knows who it should go to — the person that
task is about — with a subject and message already written, and any documents
that will be attached. Change the recipient if it picked wrong, edit freely, then
**Send & complete task**.

**Expect:** the email goes out from your mailbox **and the task is marked
complete for you**. Check your Sent folder — that is the real proof.

If you would rather handle it outside the system, **I'll handle it myself**
closes the window and leaves the task alone.

**Worth reporting:** the wrong person pre-selected; a message that does not fit
the task; your edits not surviving into the sent email; the task not completing;
an unexpected attachment.

**Already known:** you can only email **one task at a time** from a vendor's
group — there is no "email all of these at once" yet (item A3). Two tasks can
share a name and differ only by who they go to; the small label next to the
address tells you which is which (item A4).

---

## Part 8 — All Documents

Every document across every deal.

**Expect** at the top: a count of what needs attention and how many are
complete, plus **Refresh**, **Restore archived**, **Send for Sig**, **Upload**,
and — when there is anything in it — a **Deletion Queue** button with a count.

**Tabs:** AI priority · All docs · Missing · Pending review · Sent for sig ·
Signed.

### What to try

1. **The AI priority queue.** Read the top item and its suggested actions —
   Request, Upload, Mark N/A, Generate, Call, Nudge, Resend, Review, Approve,
   Forward, Flag, Replace, Void. Do the ones that fit.
2. **Upload a document** and assign it to a transaction and a type.
3. **Preview** and **Download** one. Download must save a file, not open a tab.
4. **Send for Signature** (needs DocuSign connected). Then find it under **Sent
   for sig** and try **Sync**, **Resend** and **Void**.
5. **Email a document**, **rename / reclassify / reassign** one, and look at its
   **version history**.
6. **Archive** one, then get it back with **Restore archived**.
7. On the **Missing** tab, try the bulk actions.
8. **Cleared Today** — the strip that shows what you actually resolved today.
   Note that sending a request or logging a call does **not** count as cleared;
   only actually resolving the document does.

**Worth reporting:** an action offered on a document where it makes no sense; a
document filed under the wrong type; the Missing tab asking for something you
already uploaded; a download that opens instead of saving.

---

## Part 9 — Email

Open **Email** from the Intelligence group. This one screen carries two streams.

### 9.1 Outbox — what the AI wants to send

**Expect** a list of prepared emails. Open one and you see who it is going to,
the subject and body, what the AI based it on, and — where it is a reply — the
original message above the draft.

Actions on an open draft:

- **Approve & send** — sends it as written
- **Edit** → **Send edited reply** / **Send edited email**
- **Regenerate** — only on replies; redraws from the original message
- **Discard** — removes the draft; the original message stays in the log

If some drafts have been pre-approved, a **Send all ready · N** button appears
above the list, behind a confirmation that names how many recipients it will hit.
**Please read the recipients before using it.**

### 9.2 Inbox — mail coming back in

Send an email from a deal to **a second mailbox you can receive at** — not the
address you connected — then reply from that mailbox as a client would. Wait a
couple of minutes and open the **Inbox** tab.

**Expect:** the reply appears, attached to the right deal, labelled with what
kind of message it is (money, a date change, a document, a question, an update),
often with a suggested reply already prepared.

**Read a suggested reply very carefully.** This is the AI answering a client
question on your behalf, so it is the highest-risk thing in the system. Check the
dates against the deal, and check it has not promised anything you would not
promise.

You can also tick rows and delete them, and mark a message as **not mail you
need**.

**Both tabs** share a **deal filter** and a **search box**, and there is a
**Refresh** button. Admins also get a link to the email audit log.

**Worth reporting:** a message attached to the wrong deal or to no deal; a
suggested reply that misreads the question or invents a date; the same email
appearing twice; wording you would not send to a client; **anything that
mentions AI wrote it**.

> **A known wording problem:** when you mark a message as not relevant, the
> confirmation says you can restore it from "Filtered out". There is no Filtered
> out screen in the app today — that view was removed. The message is recoverable
> by us, but not by you. No need to report it; it is on our list.

---

## Part 10 — Closing Calendar

**Expect:** a **Month** and an **Agenda** view, a **Closings only** toggle,
month navigation with a **Today** button, and a **Connect calendar** menu
offering **Google Calendar** and **Outlook Calendar**. Once one is connected,
**Add my closings** pushes your closing dates into it.

**Worth reporting:** a date on the calendar that does not match the deal; a
kind of date you expected to see and do not.

---

## Part 11 — Clients, Contacts and Vendors

### 11.1 Clients

Everyone you have given portal access to, across all your deals — with what is
waiting on you. Badges show questions **to answer** and documents **to review**.

If it is empty, that is correct until you have used **Client access** on a deal
to invite a buyer or seller.

### 11.2 Contacts

Everyone in your workspace, searchable by name, email or company, with filter
chips per contact type and a **Vendors only** filter.

### 11.3 Vendor Directory

Your vendor companies with category, phone, website and email; searchable, with
a category filter. Open one to see its contacts, the deals it has worked, and
its background information.

**Worth reporting:** a contact that should have become a vendor and did not;
duplicates that should be one record.

---

## Part 12 — Notifications and the morning digest

1. Click the **bell** in the top bar.
2. Read a few items and click **Mark all as read**.
3. Click **View all** for the full page, which filters by **All / Overdue /
   Today / Tomorrow / Upcoming**.

**Expect:** the unread badge clears when you mark all as read, and stays clear.

Then go to **Settings → Notifications**:

- Choose which reminders and alerts you receive.
- Find **Morning digest**. It is **off** unless you turn it on. Turn it on, pick
  a time, and send yourself a sample.

**Expect:** from the next morning, one email listing what is overdue and due
today across your deals. If you have nothing actionable, you correctly get
nothing.

**Worth reporting:** a badge that comes back after you cleared it; a digest
arriving when you never switched it on; a digest missing deals or listing things
already done.

---

## Part 13 — Settings

Open **Settings** from the sidebar or the avatar menu. It is one page of cards
with a search box, grouped into **Personal** and — for Admins and the workspace
owner — **Workspace**.

### Personal

| Card | What to check |
|---|---|
| **Profile** | Your photo, name, email address, phone, bio and email signature. Changing your sign-in email works here. |
| **Notifications** | Covered in Part 12. |
| **Email & E-signature** | Covered in Part 3. |
| **Email Templates** | Create reusable templates and your signature. |
| **My Playbook** | Your own closing checklists, tagged notes, preferred vendors and resources. |
| **Help & Tour** | Replay the guided tour and reach support. |

### Workspace (Admin / owner)

**Company** · **Branding** · **Billing** · **Users & Invites** · **Task
Templates** · **Document Templates** · **Vendor Templates** · **Team Playbook**
· **Integrations & Webhooks** · **AI & Automation** · **Payment Access** ·
**Advertising** · **Delete Organization**.

Two worth spending time on:

- **Branding** — set your logo, brand colour and display name, then look at the
  app and at an outbound email. Does it look like your brokerage?
- **Document Templates** — upload one of your own fillable PDF forms, then
  generate it from a deal and check the fields it filled.

**Expect:** the search box finds a card by what it does, not just its name
("gmail" should find Email & E-signature). You should only see cards you are
allowed to use — no card should lead to a "not allowed" page.

**Worth reporting:** a setting you looked for and could not find; a card that
takes you somewhere you cannot act.

---

## Part 14 — Team and oversight

**Needs a Team Lead or Admin account.**

### 14.1 People

- **Team Overview** — your team's people and their production.
- **Teams** — build and run teams, see members inline, invite into a team.
- **Settings → Users & Invites** — the active members list and pending
  invitations. Invite someone, change a role, deactivate a member, and (as the
  workspace owner) transfer ownership.

### 14.2 Task Templates

The reusable task checklists applied to new deals. Open one and read its tasks.

**The question we most want answered here:** is this the list of tasks *you*
would run for that kind of deal?

### 14.3 AI & Automation

This is where you decide how much the AI does on its own. Sections: **posture**,
**provider**, **email**, **rules**, **confidence**.

The posture choice:

- **Manual** — the AI suggests; you apply everything.
- **Assisted** — routine work applies itself; emails still wait for you.
- **Autopilot** — drafts are pre-approved, so **Send all ready** can send them
  in one tap. Even here, nothing goes out without that tap.

At the top of the page is an automation status chip and three buttons, which we
have deliberately separated by how dangerous they are:

| Button | What it does |
|---|---|
| **Draft due emails** | Prepares due emails as drafts in Email. **Sends nothing.** Safe to press. |
| **Run AI tasks (sends deal email)** | Sends the Automated task emails that are due, to real parties on every active deal in the workspace. Confirms first. |
| **Send me my digest** | Sends your own morning digest, if you have it on. |

**Expect:** the status chip currently reads that automation is **not running**
on stage. That is correct and expected (item A1).

**If you want to see Autopilot in action:** switching the posture is not enough
on its own — it applies to emails prepared *from that point on*. Press **Draft
due emails** afterwards to produce drafts that show as ready.

### 14.4 Oversight (Admin)

- **Communication Audit** — every message the workspace sent or received, with
  search, transaction filter, CSV download.
- **Audit Log** — every change, filterable by what was changed and what action
  was taken.

**Worth reporting:** a message you sent that is missing from the audit; an audit
row you cannot make sense of.

---

## Part 15 — Analytics and AI Suggestions

### 15.1 Analytics

Your production: GCI earned, transactions, and the trends behind them, with a
**Set your goals** dialog (annual GCI, quarterly GCI, annual transaction goal)
and **Export PDF**.

**Worth reporting:** a number you do not trust, and what you would compare it
against to check it.

### 15.2 AI Suggestions

The AI's cross-deal observations. Each one explains **why it flagged this**, and
you can act on it or dismiss it.

**Worth reporting:** a suggestion that is obviously wrong for the deal; a
suggestion you acted on that did not do what it said.

---

## Part 16 — Invoices, Payments and Billing

### 16.1 Invoices & Payments

Search by invoice number, payer or property. Create an invoice from a deal via
**Invoice** on the deal card. Open one to see its detail.

**Commission Payouts** only appears if your role has the payout permission.

### 16.2 Billing

**Admin or owner only, and only if Billing appears in Settings.**

**Expect** a per-deal flat fee — no seats, no subscription — charged when a new
deal is saved, with a refund if the deal is deleted within the refund window.
You can optionally **pay ahead** to buy prepaid deals, which are used
automatically before your card is charged and are shared by the whole team.

**Two things worth knowing before you test this:**

- A platform-admin account is **never charged**, so to see the fee and the
  paywall you need an ordinary workspace account.
- If **Billing** does not appear in Settings, billing is switched off in the
  environment you are testing. Tell us and we will turn it on for you.

**Worth reporting:** the price shown anywhere disagreeing with what you were
told; being charged for something you did not create; a deal you deleted not
refunding.

---

## Part 17 — A day in the life

Once the parts above work, please spend one session using it **the way you
actually work**, rather than following steps. This is where the real feedback
comes from.

Suggested shape:

1. Start at **Needs You**. Does it show the things a person genuinely has to
   decide, and nothing else?
2. Work **My Task Queue** top to bottom. Can you finish a task without leaving
   the page?
3. Clear the **Email** outbox.
4. Open one deal and work it properly in the workspace.
5. At the end, answer two questions:
   - **Would I trust this to run a real deal?**
   - **What did I have to do by hand that the system should have done?**

Those two answers are the most valuable thing you can send us.

---

## Things you may notice that we already know about

Please do not spend time writing these up:

- Automation does **not** run on a timer yet — everything is triggered by
  something you do.
- A blocked AI task has no **Try again** button; it clears once you fix the cause.
- You email **one vendor task at a time**; there is no multi-task vendor email.
- Two tasks can share a name and differ only by who they go to.
- There is no in-app **password change**; use "Forgot password?".
- The **Sharing** page in the sidebar is a "Coming Soon" placeholder.
- **AI Coach** is a future paid add-on; its buttons do nothing.
- The **microphone** in the deal assistant is switched off.
- Marking an email "not relevant" mentions a **Filtered out** screen that does
  not exist in the app.

The full list, with why each one is where it is, is in `todo_list.md`.

---

## Quick reference

| I want to… | Go to |
|---|---|
| Connect or fix my mailbox | Settings → Email & E-signature |
| See what needs a decision | Needs You |
| Work my tasks | My Task Queue |
| Read and send prepared emails | Email |
| See mail that came back in | Email → Inbox |
| Work one deal properly | Open the deal → its workspace |
| See one deal's tasks | Open the deal → Tasks tab |
| Add a missing party email | Open the deal → People tab |
| See what the AI did on its own | Open the deal → Activity → Automation |
| Chase missing paperwork | All Documents → Missing |
| Change how much the AI does | Settings → AI & Automation |
| Turn the morning summary on | Settings → Notifications |
| Invite a colleague | Settings → Users & Invites |
| Change the logo and colours | Settings → Branding |
