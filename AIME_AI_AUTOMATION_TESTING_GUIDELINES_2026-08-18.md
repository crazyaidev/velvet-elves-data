# Velvet Elves — Aime and AI Automation Testing

## Features Currently Complete — Client Feedback Requested

**Last Updated:** August 25, 2026  
**Test Environment:** https://app.stage.velvetelves.com  
**Recommended Browsers:** Chrome (please allow pop-ups)  
**Reviewer:** Jake and Audri — please fill in the Feedback block under each feature  
**Sign in:** with your own Velvet Elves account, in your own workspace  
**This round:** the updated task library is on staging. Create **new** files for Features 14 and 27–32. Open tasks on older files keep their old names, targets, and history until you complete them.

---

## How To Use This Document

### What is in this document

This is the testing pass for Aime and AI automation as the product runs today. It covers:

- How the live file is set: Manual / Assisted / Autopilot, and intake **Fast intake**
- Named letters that may send on Autopilot (welcomes, title order, pending reminder, inspection deadline reminder)
- The updated task library on **new** files: Dual (Both), Order Title vs Confirm Title Order, cash appraisal split, Deliver Utility Info to the buyer’s agent, Order Home Warranty as an internal reminder, Closing Gift, no seller Inspection Completed
- Needs You, drafts, inbound mail, money, dates
- Closing Disclosure on closing-information letters, Terminated vs Closed

Each feature has a page address, numbered steps, a concrete example you can copy, what you should see, and a Feedback block.

Use **your** workspace and **your** files. Create a new transaction when a step needs a specific kind of file. Do not look for files created in someone else’s account.

### How to work a feature (the method)

Work one feature at a time, in order, like this:

1. Read **Expected Result** first so you know what “right” looks like.
2. Do every step under **How To Test**, including the example (or the same shape with your own street and inboxes).
3. Compare the screen to Expected Result.
4. Fill in Feedback before you move on. If you skip a feature, write **Skip** and one sentence why (for example “I am not Admin, so I could not open AI & Automation”).

**Pass** — the screen matched Expected Result.  
**Fail** — something important is wrong (wrong send, wrong person, missing copy, blank dialog).  
**Needs Work** — it mostly works but you would not ship it as-is (confusing wording, slow, hard to find).

Do not diagnose. Four sentences are usually enough:

- "This is not how a deal actually goes."
- "I would never send that to a client."
- "I still had to do this by hand."
- "I could not find where to do X."

**Example of a useful Fail comment**

> Feature 12. 100 Test Oak Lane → Tasks → Buyer Closing Information → Email transaction party. Documents has Closing Disclosure.pdf. The plan still listed Closing Disclosure.pdf under the body. I did not press Send. I expected no CD on this letter.

**Example of a useful Pass comment**

> Feature 16. 200 Test Maple Ave on Assisted. Buyer Welcome → Email transaction party. To was my +buyer inbox. I sent once. One message arrived, signed as me, no “written by AI.” Nothing had gone out before I tapped Send.

### Sample files and inboxes (use these or the same shape)

Create these in **your** workspace. Put **only addresses you control** on the **Contacts** tab. A plus-address on the Gmail you connected is enough (for example `you+buyer@gmail.com` and `you+coop@gmail.com`).

| Suggested address | Kind of file | Pin posture | Used for |
| --- | --- | --- | --- |
| 100 Test Oak Lane | Buyer, financed, Contacts has emails you own, contract uploaded | Assisted (or workspace default) | Features 8–13 (reading, Complete this task, CD, status copy) |
| 200 Test Maple Ave | Buyer, financed, Contacts has emails you own, contract uploaded | **Manual** | Feature 15 — named letters must not send |
| 300 Test Pine Ct | Buyer, financed, Contacts has emails you own, contract uploaded | **Autopilot** | Feature 17 — named letters may send once |
| 400 Test Cedar St | Buyer, financed, **buyer email left blank** | Autopilot | Feature 18 — no guessed address |
| 500 Test Elm Dr | Buyer, cash, **Appraisal On This Cash Deal? = Yes** | Assisted | Feature 14 Buy-Cash |
| 600 Test Birch Way | Seller, cash, co-op + TC on Contacts, appraisal = Yes | Assisted | Feature 14 Sell-Cash |
| 700 Test Dual Ave | Buyer **and** seller (Both), financed, Contacts has emails you own | Assisted | Feature 28 Dual |
| 800 Test Utility Ln | Seller, financed, utility information uploaded on Documents | Assisted | Feature 30 Deliver Utility Info |

You do not have to create every file on day one. Create 100 Test Oak Lane first. Add Dual, cash, and listing files when you reach those features.

**Worked example — one send-safe path vs one send path**

- Send-safe: 100 Test Oak Lane → Tasks → kebab → Email transaction party → read To / body → close. Nobody’s inbox changes.
- Send path (only when To is an inbox you own): same dialog → Send. Then check that inbox and the deal Email → Sent folder. If To is a real outside agent, **stop at the plan**.

### What is not in this round

Do not hunt for these in the product, and do not report them as misses.

- Request / deliver / Clear to Close / Closing Disclosure check / closing-information / Request Testimonials sending **without a tap**. Those Autopilot letters are not authorized yet. Welcomes, title-order, pending reminder, and inspection **deadline** reminder still may send on Autopilot.
- Next-day 10am follow-up, or daily “step in” nags three days before a request is due. Not built.
- A December 1 year-end exemption blast (1010). Not built.
- A lien / judgment “cloud summary” in Deliver Title. The title commitment may still go out; the cloud list is later.
- Buyers and sellers talking to Aime. Clients keep asking the team. A client-facing Aime chat is a fail if you see one.
- A later amendment changing a date ("the file used to say X; this later signed document says Y"). Not shipped.
- A countdown that then sends mail. Not built.
- Listing or marketing after a fallen-through deal.
- Spreadsheet numbers from 360 onward on the screen. The work follows the updated list; the **number on the task stays the live ID** (for example Closing Gift stays **370**, lockbox / MLS Sold stay **453** / **455**, seller Inspection Negotiated stays **257**).

### Accounts you will need

- **Your own account** on stage, in **your** workspace.
- **Admin or workspace owner** for Settings → AI & Automation (How it runs, Overnight, Preview / Draft / Run, Fine-tune), **Try now (this deal only)** on Needs You, and the Terminated tile on the Admin dashboard. An Agent or Transaction Coordinator can still do mailbox, Needs You, files, and Complete this task.
- A **connected Gmail or Outlook** mailbox on that account (Feature 1).
- A **second address you own** for inbound tests (Feature 23). Sending from the same connected mailbox to itself proves little.

### Safety before any send

- Open **Contacts** before Send. If a party is a real outside mailbox (a co-op at another brokerage, a real lender), stop at the plan. Do not press Send.
- **Preview next run** sends nothing. Prefer it. Example: the dialog says this run would send 3 emails. Read who they are. Click **Got it**. Nobody is mailed.
- **Draft due emails** writes drafts. It does not send. Example: toast says prepared 4 emails in Email review. Check Intelligence → Email. The drafts are there. Inboxes are unchanged.
- **Run AI tasks (sends deal email)** can send named letters on **every Active Autopilot file in your workspace**, not only the file you have open. Confirm only after Preview lists addresses you own. Example: Preview lists `you+buyer@gmail.com` only → you may confirm. Preview lists `otheragent@somebroker.com` → cancel.
- **Send** / **Send all ready** — only to mailboxes you control.
- **Try now (this deal only)** retries one deal. It can send named letters on that Autopilot file. Admin only.
- When a step asks you to open **Completed** or **Terminated**, read the copy. Do not click **Change status** unless you created that file only for this test.
- If you toggle Hourly automation, Named emails, Aime signature, Inspection deadline reminder, or How it runs, put them back when you are done.

### Suggested order of testing

1. Mailbox, then (Admin / owner) Settings → AI & Automation
2. Needs You, Fast intake on Confirm Details, and (optional) Register / onboarding cards
3. 100 Test Oak Lane — posture, Contacts, Email, Complete this task, Closing Disclosure, Completed / Terminated
4. **New** files for the updated library: Dual (700), title 70 vs 80, listing utility (800), Order Home Warranty, cash appraisal (500 / 600)
5. Named letters on 200 / 300 / 400 (Manual, Autopilot, missing email) — still only the authorized Autopilot set
6. Drafts, blocked tasks, inbound wire mail, dates, and copy that should not appear

---

## Section 1 — Mailbox and Settings

### 1. Email and e-signature connection

**Route / Location**

Click your name (or avatar) in the top right → **Settings** → the **Email & E-signature** card  
/settings/connections

**How To Test**

1. Open the page. The title at the top should be **Email & E-signature**.
2. Find Gmail or Outlook. Note whether it says Connected and shows an address (example: `you@gmail.com`).
3. Click **Test connection**. Watch the page. Do not expect a client email.
4. Confirm **Disconnect** is visible next to the connected mailbox. Do **not** disconnect yet (that is Feature 20).
5. If nothing is connected: click **Connect** on Gmail or Outlook, finish Google/Microsoft, walk the “Google hasn’t verified this app” screen if it appears (Advanced → continue), then Test connection.

**Expected Result**

- Connected vs not connected is obvious **for this user**. Overnight’s “Mailboxes · N healthy / N connected” is the workspace census and can include other people’s inboxes. Example: Overnight says 4 connected, but Email & E-signature still shows **Connect** on Gmail — this account is not connected. Connect it before any Send test.
- Test connection only appears after a mailbox is connected. It only checks the saved credentials. Open that mailbox: there is **no** new deal letter from this click.
- Google’s unverified-app warning is expected on stage. If Connect has lapsed since last week, reconnect and note it — that is not a product miss.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 2. How it runs — Manual, Assisted, Autopilot

**Route / Location**

Settings → **AI & Automation** (Workspace cards) → left nav **How it runs**  
/admin/confidence  

Admin or workspace owner only. If you are an Agent, write Skip and go to Feature 5.

**How To Test**

1. Open How it runs. You should see three cards: **Manual**, **Assisted**, **Autopilot**, and a four-row table under them.
2. Write down which card is currently selected. Example: “Workspace default is Autopilot.” You will put it back if you change it.
3. Read each card’s one-line promise out loud against Expected Result.
4. Read the four-row table the same way.
5. Press F5 (refresh). Watch the small chip in the **page header** from the first paint — before the rest of the page settles. Example: it should say **Checking automation** (muted, not amber) for a moment, then **Automation active**.
6. If you click a different card to see Save posture, click back to the original and **Save posture**.

**Expected Result**

- Card promises, word for word:
  - Manual: *AI suggests. You click to apply anything.*
  - Assisted: *Routine work runs. Named emails are drafted — you tap Send.*
  - Autopilot: *Authorized emails send when confidence is high enough. No tap.*
- Comparison table:

| | Manual | Assisted | Autopilot |
| --- | --- | --- | --- |
| Routine actions | You click | Runs | Runs |
| Email drafts | You ask | Prepared — you tap Send | Ready, or Needs You if confidence is low |
| Welcome / title emails | Never auto | Drafted — you tap Send | Sends without a tap |
| Dates, waives, legal | You | You | You |

- Fail examples: Assisted and Autopilot still describe the same send behavior; Autopilot still says you tap Send; the page says “library letters.”
- Chip: **Checking automation** first, then the real state. Healthy: **Automation active**. Never checked in: **Automation is not running**. Was running, went stale: **Automation has stopped**.
- Fail: the chip flashes **Automation has stopped** (amber) while the page is still loading, then flips to active.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 3. Overnight switches and Always true

**Route / Location**

Same page as Feature 2, the **Overnight** card, then **Always true** underneath  
Admin or workspace owner only.

**How To Test**

1. Read the Overnight description at the top of the card. Example when everything is on: hourly automation is on; named welcome and title-order emails may send on Autopilot; on Assisted they are drafted for you to tap Send.
2. Note the clocks: **Last run** (for example “12 minutes ago”) and **Last draft sweep**. Note **Mailboxes · 1 healthy / 1 connected**, or a **Connect Gmail or Outlook** link.
3. Write down the four switches as they are now, then leave them (or restore when a later feature is done):

| Switch | What you click | Example of Allowed / On | Example of Paused / Off |
| --- | --- | --- | --- |
| Hourly automation | Off / On | Overnight prep runs | Overnight prep will not run until you turn it on |
| Named emails | Paused / Allowed | Welcome and title-order emails may send on Autopilot; Assisted = tap Send | Those emails will not send |
| Aime signature | Agent / Aime | Automatic named emails sign as Aime, Assistant to the agent | Automatic emails use the agent’s signature |
| Inspection deadline reminder | Paused / Allowed | Deadline reminder to you may send on Autopilot. Not other reminder tasks; not Inspection Negotiated | That reminder will not send |

4. Inspection deadline reminder is **Paused** on a brand-new workspace. On a workspace that is already in use it may already be **Allowed** — write down what you see, and put it back if you change it. Named emails is **Allowed** unless you turned it off.
5. Read **Always true** (four lines, with a red X on the wire line).

**Expected Result**

- The Overnight story matches the switches. Example: if Named emails is Paused, the card should not promise that welcomes may send.
- Always true, word for word:
  - Named welcome, title-order, and inspection-deadline emails may send on Autopilot when confidence is high enough. On Assisted they are drafted for one tap. Every other email is drafted for you to send.
  - Deadlines never move themselves.
  - Waives, legal calls, and packet release stay human.
  - Wire and funds mail is never drafted.
- Fail: Named emails still labelled Autopilot; Inspection deadline reminder promises to send repair or negotiation mail.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 4. Preview, Draft due emails, and Run AI tasks

**Route / Location**

Overnight card, the row of buttons  
Admin or workspace owner only.

**How To Test**

Preview, Draft, Run, and Digest are **one row** on the Overnight card (Settings → AI & Automation → How it runs). They are not on Intelligence → Email and not on the deal Inbox. Scroll past the Manual / Assisted / Autopilot cards if the Overnight buttons are below the fold.

1. Click **Preview next run**. Example of a safe dialog: “This run would send 0 emails” or a small number to addresses you recognize. Click **Got it**. Open your mailbox — nothing new from this click.
2. If the count is greater than 0, screenshot or write the addresses. Example: `you+buyer@gmail.com` is fine. `lender@bigbank.com` means you must not Run later.
3. Click **Draft due emails**. Wait for the toast. Example: title **Draft sweep ran**, description “Prepared 4 emails in Intelligence → Email. Nothing was sent.”
4. Open **Intelligence → Email** (sidebar Intelligence group, item **Email**). Confirm new drafts. Unlinked rows (no Velvet Elves file) should say **Needs a deal**, not **Reply ready**, and the pane must not offer **Approve & send**. Open **Needs You** and look for **To review** or **Ready to send**.
5. Stay on Overnight. Click **Run AI tasks (sends deal email)**. Read the confirm. It should repeat the Preview. Click the cancel control — **do not** confirm unless every address is yours.
6. Optional: **Send me my digest** only if Settings → Notifications has your morning digest on. That email is to **you**, not a client.

**Expected Result**

- Preview is this workspace only. Got it sends nothing.
- On Assisted, named emails that would otherwise send are **not** counted as would-send; they wait for a tap.
- Draft due emails prepares drafts only. Inboxes unchanged.
- Run AI tasks confirm is clearly a send (“real emails to real people”). Cancel sends nothing.
- Intelligence → Email may show inbound that has not matched a deal yet so you can file or discard it. Aime must not send a reply until it is linked. The **deal** Email → Inbox stays that file only.
- Fail: Preview or Draft puts an email in a client inbox; Run has no confirm; Cancel still sends; unlinked mail shows **Reply ready** or **Approve & send**.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

## Section 2 — Needs You and intake

### 5. Needs You

**Route / Location**

Left sidebar → **Workflow** → **Needs You**  
/needs-you

**How To Test**

1. Open Needs You. Wait until the orange count pill is a number, not **Loading**. Example: `31 waiting · 8 ready to send`.
2. Read the sentence under the title (empty state or “these items still need a person…”).
3. If tiles are visible, click each: **Ready to send**, **To approve**, **To review**, **To decide**, **To handle**. Refresh. The same tile should stay selected.
4. Click one row to expand it. Example of a blocked welcome: heading **Why the AI is asking**, a reason, and a link such as **Add contact**.
5. In Search, type a street from a file **you** created (example: `100 Test Oak`). The list should narrow to that deal, or show a clear empty state.
6. If **Send all ready (N)** or **Approve all safe (N)** is enabled, click it, read the confirm, cancel. Example: confirm lists 2 Ready drafts. Cancel. Those 2 are still in the queue; nobody was mailed.

**Expected Result**

- Breadcrumb: Workflow › Needs You. Title: Needs You, with a pill like **31 waiting · 8 ready to send** (the number is live; Loading must go away).
- Kind tiles as named above. Row pills may say Ready to send, AI proposal, Draft to review, Decision, AI task blocked.
- Empty and healthy: *Overnight prep ran. Nothing needs you. Named emails may still send on Autopilot deals; on Assisted they wait for Send.* (The empty card may say “wait for you to tap Send.”)
- Not empty: *These items still need a person. Named emails may send on Autopilot deals; on Assisted they wait here for Send.* Fail if the page says nothing needs you while cards are still visible.
- Scheduler down: banner **Automation is not running** or **Automation has stopped**. Admin sees **Open AI & Automation**. There is no **Run AI tasks** button on this page.
- Ready to send still needs Send. Example: expanding a Ready row shows Send; the party inbox does not have that letter yet.
- Recovery verbs that exist on the card: **Add contact** (opens that deal’s **Contacts** tab, not the sidebar directory), **Upload document**, **Reconnect mailbox** / **Connect mailbox**, **Change due date**, **Switch this deal off Manual**. A more-than-30-days-overdue card also shows **Use today's date and retry**. Other cards may say **Review signatures**, **Open tasks**, or **Complete your profile** — use the verb on the card. The white box under **Why the AI is asking** is the reason; the muted line under it can be shorter. Do not Fail if both are present.
- Fail: buyers/sellers told to talk to Aime; “library letters”; Cancel on Send all ready still sends.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 6. Fast intake

**Route / Location**

**+ New Transaction** → upload a contract → walk forward to **Confirm Details**  
/transactions/new

**How To Test**

1. Click **+ New Transaction**. Choose who you represent (example: **Buyer**) the way you usually do.
2. Upload a signed purchase agreement you already use for testing. Wait until parsing finishes. Do **not** look for Fast intake on this upload step.
3. Click through Contract Details as needed until the step title is **Confirm Details** (Verification in the stepper).
4. Look at the **top** of that step for an orange banner.
5. You can leave the wizard after you have seen the banner (or after you have confirmed it is absent). You do not have to finish the file for this feature.

**Expected Result**

- Fast intake is **not** a sparkle control on upload. It is only the orange banner on Confirm Details, and only when the read is high confidence.
- If the banner is there, example of a pass:
  - Small caps: **✦ Fast intake**
  - Heading: **Everything checks out at high confidence**
  - Body: The extraction double-check agreed, every key field cleared the confidence tier, and the timeline, checklist, and task plan are ready below. Confirm the anchor date, then approve — or open any step from the top bar to drill in.
  - It does **not** say Autopilot. It does **not** mean Aime will email the buyer.
- If the banner is missing, the read was not high confidence (a messy scan, missing dates, low confidence). **Skip** — not a Fail.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 7. Register and onboarding — the three cards

**Route / Location**

Sign out (or a private Chrome window) → /register  
Onboarding after a new sign-up: /onboarding  

Only if you can do this without disturbing a live account. A private window is safest. You do not have to finish creating an account.

**How To Test**

1. Open /register. Scroll to **How should Aime start?**
2. Read the three cards (Manual / Assisted / Autopilot) against Feature 2.
3. Leave Manual selected. You can close the tab. Skipping / leaving Manual means a new workspace starts on Manual.
4. If you are already in onboarding on a throwaway account, read the same three cards there.

**Expected Result**

- Same promises as Feature 2.
- Example: a brand-new sign-up that never changes this control lands on Manual. Named emails will not send until someone chooses Assisted or Autopilot **and** a mailbox is connected.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

## Section 3 — A file you created

Create **100 Test Oak Lane** (or any Active financed file in your workspace) for Features 8–13. Represent **Buyer**, financing **Financed**, upload a contract, put a buyer email **you** control on **Contacts**. Pin Assisted if you want named letters to wait.

### 8. Deal posture on the workspace

**Route / Location**

Open 100 Test Oak Lane (or your financed file) → the control in the workspace **header** next to the address

**How To Test**

1. Open the file. Find the **Autopilot / Assisted / Manual** control in the header (zap icon). The one-line caption is **inside that menu**, not printed under the chip. Open the menu and read the caption on the current choice. Example on Autopilot: *Authorized emails send without a tap when confidence is high enough. Everything else is drafted for you.*
2. In the same menu, if **Use workspace default** is listed, you may click it once. Example toast: “This deal follows the workspace default (autopilot).” Put the pin back if you need a custom posture for later features.
3. Open the menu again only to read the other captions, then press Escape. Do not leave a live client file on Manual.

**Expected Result**

- Manual: *AI suggests. You click to apply anything. Named emails wait until you switch this deal off Manual.*
- Assisted: *Routine work runs. Named emails are drafted — you tap Send.*
- Autopilot: *Authorized emails send without a tap when confidence is high enough. Everything else is drafted for you.*
- Use workspace default clears the custom pin. Changing How it runs in Settings later applies to this file again.
- Fail: Autopilot’s caption still says you tap Send on named emails; Manual still promises unattended send.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 9. Contacts

**Route / Location**

Same file → workbench tab **Contacts** (next to Documents). Do **not** use the sidebar item **Contacts** — that is the workspace contact directory (`/contacts`), not this deal.

**How To Test**

1. On the open file, click the workbench tab **Contacts**. Confirm the URL stays on `/transactions/…` (not `/contacts`). The page heading is **Contacts** (kicker **✦ Parties**). Groups on a buyer-rep financed file: **Buyer**, **Seller**, **Agents**, **Lender**, **Title**. Empty groups stay on the page with dashed copy (examples: *No buyer on file*, *No co-op agent on file*, *No lender contact on file*, *No title contact on file*). Title may also show the RESPA note about not requiring a particular title company.
2. Look at the Buyer card. You should see a name (or *Unnamed contact*) and the role. The email address is **not** printed on the card. A **Mail** icon appears only when that party has an email. No Mail icon means the email is blank — that is allowed.
3. Do not invent an address Aime “should have guessed” (do not look for `info@titlecompany.com` unless you typed it). If the buyer has no email, leave it. Feature 18 uses a dedicated file for wait-not-send.
4. Adding uses the group buttons (**Add buyer**, **Add seller**, **Add agent**, **Add loan officer**, **Add title contact**). Clicking an existing card expands it so you can see and edit that party. The Mail icon, when the party has an email, composes **to that party only**.

**Expected Result**

- Every party Aime might email lives on this tab. Aime does not invent `info@titlecompany.com`.
- Blank email is allowed (no Mail icon). That letter should wait, not send.
- Clicking a card expands it (email / phone / company + Edit). The Mail icon composes to that party only.
- Fail: you landed on the sidebar Contacts directory (`/contacts`); a Mail icon on Title when you never added a title email.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 10. Email tab

**Route / Location**

Same file → **Email** tab. Folders are **tabs** labeled Outbox, Sent, Inbox (not separate pages).

**How To Test**

1. Open Email. Read the grey sentence under the header **before** you click anything.
2. Click **Outbox**, then **Sent**, then **Inbox**. Example: Outbox shows drafts waiting; Sent is empty on a new file; Inbox is empty until Feature 23.
3. Do not Send unless To is an inbox you own.

**Expected Result**

- Exact sentence: *Nothing sends until you tap Send. Drafts you prepare land on Outbox — Inbox is mail that arrived. On Autopilot, named welcome / title / inspection-deadline emails may already have gone out on their own. On Assisted they wait here for Send.*
- Three folders: Outbox, Sent, Inbox.
- Fail: a sent body says “written by AI” or “generated by ChatGPT.”

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 11. Complete this task stays on screen

**Route / Location**

Same file → **Tasks**

If Buyer Closing Information is not there yet, wait until tasks generate, or use another closing-information task (Seller / Seller's Agent / Buyer's Agent Closing Information).

**How To Test**

1. Find **Buyer Closing Information**. Click the **row**. It should only expand (instructions, dates). The email dialog should **not** open.
2. Click the kebab (⋯) on that row → **Email transaction party**. (On My Task Queue, the same action is on the card when the task completes by email.)
3. Wait until the plan loads (three pulse bars, then content).
4. **Do not press Send.** Scroll from the orange Aime summary down through To, the body, and the footer buttons.
5. Close with the X.

**Expected Result**

- Title: **Complete this task**. Subtitle includes the task name and address (example: Buyer Closing Information · 100 Test Oak Lane).
- When the plan can send: orange box *Aime can complete this for you.* plus a one-line summary.
- **Transaction party** dropdown, then **To:** (and **Cc:** if anyone is on copy), then the message body, then Send / close in the footer.
- You can scroll the middle. Fail example: only the header bar and the footer are visible; the middle has height zero; you cannot see who To is.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 12. Closing-information emails never attach the Closing Disclosure

**Route / Location**

Same Complete this task dialog, plus **Documents** on the file

**How To Test**

1. Open **Documents**. Write down whether a file named like **Closing Disclosure** is on the file. Example: “Yes — Closing Disclosure.pdf” or “No CD on this file.”
2. Re-open Buyer Closing Information → Email transaction party.
3. Scroll under the body. Attachments only render if there is at least one. Example of a pass with a CD on Documents: you still do **not** see Closing Disclosure.pdf on this plan.
4. Repeat for Seller Closing Information, Seller's Agent Closing Information, and Buyer's Agent Closing Information if they exist on this file.
5. If you have a task named **Closing Disclosure Delivered**, open it separately. That email is an inquiry to the lender (has it been sent and signed). It should **not** attach the CD.
6. Close without sending.

**Expected Result**

- Buyer / seller / agent **closing information** emails never list a Closing Disclosure (or CD).
- **Closing Disclosure Delivered** is an inquiry to the lender and also must not attach the CD.
- If Documents has a CD, it still must not appear here. If Documents has no CD, the plan must not invent one. No attachment list at all is fine.
- Fail example: Buyer Closing Information plan shows `Closing Disclosure.pdf` as an attachment.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 13. Completed vs Terminated

**Route / Location**

100 Test Oak Lane → status **pill** in the header (Active / Completed / …)  
Transactions list → **Terminated** tab  
Admin home (Admin only) → Terminated count tile

**How To Test**

1. Click the status pill. Choose **Completed**. Read the dialog title **Change status to Completed?** and the paragraph. Do **not** click **Change status**. Close the dialog (X or the non-confirm action). The file should still be Active.
2. Open the pill again. Choose **Terminated**. Read **Change status to Terminated?** Do not click **Change status**.
3. Optionally open **Closed** the same way and read that paragraph, then close.
4. Go to **Transactions**. Click the **Terminated** tab. An empty list is fine.
5. If you have no Closed files, open Closed and read the empty hint.
6. If you are Admin, open the Admin dashboard and find a **Terminated** tile separate from Closed / Completed.

**Expected Result**

- Completed: *Closing day is not the end of the file. Mark Completed when post-closing work is done (lockbox, MLS Sold, thank-you). Keep the file Active until then.*
- Terminated: *The deal fell through. Automatic emails stop. History stays. This is not a closed sale.*
- Closed: *Moves the deal off the active board and asks for post-closing feedback. Use after the file is done — not for a deal that fell through.*
- Closed empty hint: deals appear here once you mark them Closed or Completed. Files that fell through are Terminated, not Closed.
- Fail: fallen-through is only offered as Closed; Completed tells you to finish the file on closing day while lockbox / MLS Sold / thank-you are still open.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 14. Cash Appraisal Ordered / Completed

**Route / Location**

**+ New Transaction** → cash file → Contract Details → **Appraisal On This Cash Deal?**  
After create: Tasks → kebab → **Email transaction party**

**How To Test**

**Buy-Cash (500 Test Elm Dr)**

1. New Transaction. Represent **Buyer**. When financing is **Cash** (no mortgage), Contract Details shows **Appraisal On This Cash Deal?**
2. Choose **Yes — buyer is appraising**. Helper: *Appraisal follow-up tasks will be created.* (If you choose **No appraisal**, helper: *No appraisal tasks on this deal* — those tasks will not exist. That is not a Fail; create another file with Yes.)
3. Put the buyer email you control on **Contacts** (at intake, or **Add buyer** after create). Finish creating the file.
4. Tasks → **Appraisal Ordered** → kebab → Email transaction party. Note **To:**. Repeat for **Appraisal Completed**. Do not Send.

**Sell-Cash (600 Test Birch Way)**

1. New Transaction. Represent **Seller**. Cash. Appraisal = Yes.
2. On **Contacts**, under **Agents**, **Add agent** with `you+coop@gmail.com` (or another inbox you own). Use **Assign team** for a **transaction coordinator** with an inbox you own.
3. Open Appraisal Ordered / Completed the same way. Note To and Cc.

**Both-Cash (optional):** represent Buyer & Seller, cash, appraisal Yes. Expect the same To as Buy-Cash (buyer). Do **not** expect a co-op appraisal letter on Dual — there is no co-op on a Both file.

**Expected Result**

- Buy-Cash: **Appraisal Ordered** and **Appraisal Completed** (live IDs 265 / 271). **To:** the Buyer (example: `you+buyer@gmail.com`). Not the loan officer. The agent may be on Cc.
- Sell-Cash: the same **names** on Tasks, live IDs **267** / **275**. **To:** the co-op agent. **Cc:** includes the assigned transaction coordinator. Not To the buyer. Not To the loan officer.
- These tasks are not automatic sends. Closing the dialog sends nothing.
- Fail: To is empty; To is the other side’s client on a listing; Buy-Cash still emails the co-op; Sell-Cash still emails the buyer; the task is missing even though you chose Yes — buyer is appraising.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

## Section 4 — Named letters and drafts

Create **new** files (200 / 300 / 400) for this section. Pin posture on each file. A signed purchase agreement is enough unless a step says to omit it.

Letters that may send without a tap — **Autopilot only**, Named letters **Allowed**, file **Active**:

| Letter | To | Also needs |
| --- | --- | --- |
| Buyer / seller / co-op welcome | That party | Their email on Contacts |
| Loan officer welcome | Lender | Email and the purchase agreement |
| Order Title / Confirm Title Order | Title company or title rep | Email and the purchase agreement. Wizard chooses **Order Title** when your side orders title, **Confirm Title Order** when the co-op orders. Confirm Title Order is the courtesy-order letter (“as a courtesy to … engage you as the escrow agent”), not a “has title been ordered?” follow-up. Both withhold personal-property and monetary addenda / amendments. |
| Pending reminder | You (the account holder), not a client | MLS pending nudge |
| Inspection response reminder | You (the account holder) | Inspection deadline reminder **Allowed**. Deadline only. No repair or negotiation language |

Review Documentation completes with no email when the packet is signed. If signatures are missing, it drafts a chase — that chase waits for Send.

Order Home Warranty is an **internal reminder** to the transaction agent (TC on copy when assigned). It is drafted for you to send. It does not email a warranty company, and it does not send on its own.

### 15. Manual — named letters do not send

**Route / Location**

Create **200 Test Maple Ave** (Buyer, financed, emails you control, contract on the file). Header posture → **Manual**.  
Admin: Settings → AI & Automation → Preview next run

**How To Test**

1. Finish the wizard. In the header, pin **Manual**. Caption should match Feature 8.
2. Open Tasks. **Buyer Welcome** (and Seller / Co-op if you captured them) should still be open, not completed.
3. Admin: Preview next run. 200 Test Maple Ave must not be in would-send. Example: “This run would send 0 emails,” or the list is other Autopilot files only.
4. Do **not** Run AI tasks for this feature.
5. Check Email → Sent. No new buyer welcome from this pin.

**Expected Result**

- Named letters stay open.
- Needs You / Why the AI is asking (white box) can say: *This deal is on Manual, so the AI will not send this email or complete this task on its own. Switch the deal off Manual, or complete it yourself.* The muted line under the box is shorter: *This deal is on Manual, so the AI will not send. Switch the deal off Manual, or complete the task yourself.* Recovery: **Switch this deal off Manual**.
- Fail: a welcome is already in the buyer’s inbox after you pinned Manual, with no tap from you.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 16. Assisted — you tap Send

**Route / Location**

100 Test Oak Lane on **Assisted** (or create a new Assisted financed file) → Tasks → **Buyer Welcome** → Email transaction party

**How To Test**

1. Confirm the header says Assisted.
2. Open Buyer Welcome → Email transaction party. Read **To:** — example `you+buyer@gmail.com`.
3. Check that mailbox **before** Send. The welcome should not be there yet.
4. If To is yours, you may press Send **once**. Then check the mailbox and Email → Sent.
5. If To is not yours, close the dialog.

**Expected Result**

- To is the buyer. The letter waits. Assisted does not send with no tap.
- Why the AI is asking can say: *This deal is on Assisted, so Aime drafted the email for you to tap Send. Autopilot is the setting that sends authorized emails without a tap.*
- **Give this back to the AI** should not appear on that Assisted letter. If it does, do not click it; note Needs Work and use Send or close.
- After one Send from Complete this task: one message, right To, address + closing date in the body, **agent’s** signature (your name), no “written by AI.” If the body says a file is attached, that file is on the email.
- A Ready named-letter draft Aime prepared overnight (Intelligence → Email, not this dialog) may still sign as Aime when Aime signature is On. That is a different path. Note it; do not Fail Complete this task for it.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 17. Autopilot — named letters may send once

**Route / Location**

Create **300 Test Pine Ct** (Buyer, financed, tester emails, contract uploaded). Pin **Autopilot**.  
Admin: Preview next run, then **Run AI tasks (sends deal email)** only if would-send is entirely yours.

**How To Test**

1. Settings → AI & Automation: Named letters **Allowed**, Hourly automation **On**.
2. Create 300 Test Pine Ct. On **Contacts**: buyer / co-op / lender / title = inboxes you own. Pin Autopilot.
3. Preview next run. Example of a go: would-send lists `you+buyer@gmail.com` (Buyer Welcome) only. Example of a stop: would-send lists a live lender you do not control → **Got it** / cancel Run.
4. If the list is only yours, confirm **Run AI tasks (sends deal email)**.
5. Check Tasks: Buyer Welcome may be completed. Check the buyer inbox: at most **one** welcome.
6. Preview again. That welcome must not be in would-send. Do not expect a second copy if you Run again.

**Expected Result**

- Welcomes for parties you captured may send and complete.
- Loan officer welcome and Order Title wait without the purchase agreement; they may send if the contract is on the file.
- Order Title / Confirm Title Order must not attach personal-property or monetary addenda / amendments even when those files are on Documents.
- At most one of each letter. The wizard picks Order Title **or** Confirm Title Order, not both.
- Automatic named letters sign as **Aime, Assistant to the agent** when Aime signature is On.
- Fail: second welcome; letter to someone not on Contacts; Order Title sent with no purchase agreement.
- Paused / Terminated / Completed / Closed files are not in would-send.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 18. No buyer email, and no purchase agreement

**Route / Location**

**400 Test Cedar St** — Autopilot, buyer email **blank**  
A second Autopilot file with **no** purchase agreement uploaded  
Needs You → **To handle**

**How To Test**

**Missing email**

1. Create 400 Test Cedar St. Leave the buyer email empty on **Contacts**. Pin Autopilot.
2. Open Buyer Welcome on Tasks. Open Needs You → To handle. Expand the row.
3. You should see **Add contact**, not **Give this back to the AI**.
4. Click **Add contact**. You should land on **Contacts**. Use **Add buyer** to put `you+buyer@gmail.com` on a buyer and save. Clicking an existing Buyer card does not open an editor.
5. Admin: **Try now (this deal only)** on that card, or wait for the next hourly run. Do not expect Give-back on this block.

**Missing contract**

1. Create an Autopilot financed file and skip the purchase agreement (or do not upload it).
2. Open **Order Title** and **Loan Officer Welcome**. Needs You should offer **Upload document**.
3. Confirm nobody received a title-order email that claims the contract is attached.

**Expected Result**

- No buyer email: flagged, no send to a guessed or platform address.
- No contract: flagged missing document; no send that promises the contract without the file.
- Give this back to the AI is **absent** on these two blocks. Try now (this deal only) is Admin only and touches **this deal only**.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 19. Inspection response reminder

**Route / Location**

Settings → AI & Automation → Inspection deadline reminder (Admin / owner)  
A file with an inspection response deadline → Tasks

**How To Test**

1. On Overnight, write down Inspection deadline reminder as you find it (**Paused** or **Allowed**). A workspace already in use may already be **Allowed**.
2. If it is Paused, switch to **Allowed** for this feature. You will restore the original setting when you finish.
3. Open a file that has an inspection response deadline (your financed test file if the contract had one). Find **Inspection Response Reminder** (or the same name on Tasks).
4. On Autopilot, open the plan / wait for overnight. Read the body: it should be a deadline nudge to **you**.
5. Pin the same file **Assisted** and confirm that letter is a draft for Send, not already in your inbox.
6. Put Inspection deadline reminder back to what you wrote in step 1. Do not leave it Paused if it was already Allowed.

**Expected Result**

- To is you (account holder), not the buyer or seller.
- Deadline only. Fail examples in the body: “please send repair requests,” “accept or reject the inspection,” negotiation language.
- **Inspection Negotiated** does not send on its own in this round (Aime is an intermediary when you open the plan — it does not propose repair terms).
- On a Dual (Both) **new** file you should see **both** the buyer and seller Inspection Response Reminder and Inspection Negotiated rows (Feature 28). A listing-only file gets the seller pair; a buyer-only file gets the buyer pair.
- If you leave the switch Paused, the task is flagged that inspection response reminders are paused. That is not a Fail.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 20. Mailbox down

**Route / Location**

Settings → Email & E-signature → **Disconnect**  
Then 300 Test Pine Ct (Autopilot) → Tasks / Needs You

**How To Test**

1. Disconnect Gmail or Outlook. Confirm the page now shows not connected.
2. Preview next run or open a named letter that was waiting on 300 Test Pine Ct. Needs You may show **Reconnect mailbox** or **Connect mailbox**.
3. Confirm no new named letter arrived in a party inbox during the disconnected window.
4. **Connect** again and Test connection before you leave this feature.

**Expected Result**

- Named letter flagged (reconnect / no provider). No send while disconnected.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 21. Prepared drafts and Send all ready

**Route / Location**

After Feature 4: sidebar **Intelligence** → **Email**  
/ai-emails  

Page title is **Email**, not “AI Emails.”

**How To Test**

1. Open Intelligence → Email. Breadcrumb: Intelligence › Email.
2. Open a draft that is **not** Buyer Welcome / Order Title. Example: a due-task reminder or Order Home Warranty.
3. Note whether it is in review or marked Ready.
4. If **Send all ready** is enabled, click it, read the recipient list, cancel. Example: “Send all ready · 2”. Cancel. Those 2 still sit there.
5. You may Send **one** Ready draft if To is an inbox you own. Then check that inbox and the deal Email → Sent.

**Expected Result**

- Assisted: draft sits in review (not Ready). Autopilot: it may be Ready. Ready means one tap, not already sent.
- Cancel on Send all ready sends nothing.
- After a real Send: one message; the row leaves Ready; deal Email → Sent shows it.
- Fail: a non-named draft left with no Send; body says “Attached is the inspection report” with nothing attached.
- Order Home Warranty may appear as a draft; it must not auto-send. To should be the transaction agent (you), not a warranty company.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 22. Blocked tasks — Give-back, Try now, and recovery

**Route / Location**

Needs You → **To handle**  
or Tasks on the file from Feature 18 / 15

**How To Test**

Use the card in front of you; do not hunt for every code.

| What you set up | What the card should offer | What you do |
| --- | --- | --- |
| Buyer email blank (400 Test Cedar St) | **Add contact** | Add the email. Then wait or (Admin) **Try now (this deal only)**. No Give-back. |
| No purchase agreement | **Upload document** | Upload the contract. Then wait or Try now. |
| Mailbox disconnected | **Reconnect mailbox** / **Connect mailbox** | Reconnect. Then wait or Try now. |
| Task more than 30 days overdue | **Use today's date and retry**. There may also be **Change due date**, which opens Tasks. | Click **Use today's date and retry**. Due date moves to today. Nothing sends until the next run. |
| Execution error (if you have one) | **Give this back to the AI** | Click it. Toast: nothing was sent. |
| File on Manual (200 Test Maple Ave) | **Switch this deal off Manual** | Read it. You may leave Manual. |

**Expected Result**

- Give this back to the AI does not send.
- Try now (this deal only) is Admin only. Toast title **Tried this deal**. Description example: “Completed 0, flagged 1. Nothing else in the workspace was touched.” If the file is Autopilot and the block is cleared, this click **can** send that deal’s named letters — check **Contacts** first.
- Fail: the card tells you to click a button that is not there; Give-back on a missing-email row; Give-back mails the party.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

## Section 5 — Boundaries

### 23. Inbound mail and money

**Route / Location**

100 Test Oak Lane → Email → **Inbox**  
Send from a **second** address you own **to** the connected mailbox (the one on Email & E-signature)

**How To Test**

1. Put 100 Test Oak Lane (or your real test street) in the subject or first line so the mail can match the file.
2. From a **different** inbox, send four messages to your connected mailbox, one at a time. Wait until each appears on Email → Inbox (or Needs You) before sending the next.

**Message A — factual question (should draft, must not send)**

Subject: `100 Test Oak Lane — closing date`  
Body: `When is the closing date for 100 Test Oak Lane?`

**Message B — statement (must not vanish)**

Subject: `100 Test Oak Lane — title`  
Body: `The title commitment is ready.`

**Message C — wire (must not draft or send)**

Subject: `100 Test Oak Lane — wire`  
Body: `Please send the wire instructions for 100 Test Oak Lane.`

**Message D — banking (must not draft or send)**

Subject: `100 Test Oak Lane — banking`  
Body: `Please send banking details for closing.`

3. After C and D, open Intelligence → Email and Needs You → Ready to send. Confirm those two did not become a Ready reply you could Send all ready.

**Expected Result**

- A: kept on the deal. A factual draft or Ready. Does **not** leave the mailbox until you Send (and you should not Send unless you mean to).
- B: kept. Must not disappear. Draft optional.
- C and D: **no** reply draft, **not** Ready, **does not send**. Fail if Aime replies with wiring or account numbers, or if a Ready money draft appears.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 24. Dates never move themselves

**Route / Location**

100 Test Oak Lane → **Ask AI** (agent pane on the right)

**How To Test**

1. Note the current closing date (example: August 30, 2026) on Timeline or the header.
2. In Ask AI, type: `Change the closing date on 100 Test Oak Lane to September 15, 2026.`
3. Wait for a proposal with a preview of what else would move.
4. Click **Dismiss**. Do **not** click **Approve**.
5. Check the closing date again — it should still be August 30, 2026 (your original).

**Expected Result**

- A preview appears. Nothing moves until **Approve**.
- Dismiss leaves every date. Date cascade is not in Always-approve automation rules (Fine-tune → Automation rules → Never automatic).
- Fail: the date changed with no Approve.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 25. Digest, Fine-tune, and Paused files

**Route / Location**

Settings → **Notifications** (morning digest)  
Settings → AI & Automation → Fine-tune: **AI model**, **Email replies**, **Automation rules**, **Confidence gates** (Admin / owner)  
200 Test Maple Ave or 300 Test Pine Ct → pin **Paused**

**How To Test**

1. Settings → Notifications. Note whether morning digest is on or off **for you**. Change How it runs (Manual ↔ Assisted) and come back — digest should be unchanged. Posture is not a team-wide digest switch.
2. Overnight → **Send me my digest**. If digest is off, expect “Nothing to send” / turn it on in Notifications. If digest is on, you (not a client) get the email.
3. Fine-tune: open Email replies, Automation rules, Confidence gates. Confirm there is **no** Preview next run / Run AI tasks here. On Automation rules, wait until the **Ask me / Always** rows load (not a grey placeholder). Then read **Never automatic** — dates (cascade), auto-send email, waives, legal, and packet release still need a person.
4. On 300 Test Pine Ct, pin **Paused**. Admin: Preview next run. This file must not be in would-send. Named letters must not keep going.

**Expected Result**

- Digest is per-user. Changing posture does not turn digest on for the team.
- Fine-tune cannot put the workspace into “send named letters on Manual.”
- Paused, Terminated, Completed, and Closed files do not keep sending named letters.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 26. Words that should not appear

**Route / Location**

The surfaces you already opened: Settings → AI & Automation, Needs You, Confirm Details, 100 Test Oak Lane Email and Tasks, plus any Dual / title / warranty files from Section 6

**How To Test**

1. You do not need a special hunt. While you work Features 1–32, jot anything that matches the fail list.
2. Extra glance: Confirm Details banner (Feature 6), How it runs cards (Feature 2), Email tab sentence (Feature 10).

**Expected Result**

Fail if you see any of these in the product:

- “Library letters”
- Intake banner still called Autopilot (it is **✦ Fast intake**, and only on Confirm Details when confidence is high)
- Assisted described as “no tap,” or Autopilot described as “you tap Send” on named letters
- A client-facing Aime for buyers or sellers
- A countdown that will send without you
- “Written by AI” on an outbound body
- Wire / funds treated as a Ready draft
- Fallen-through deals filed as Closed with no Terminated path
- Confirm Title Order still written as “has title been ordered?” instead of a courtesy order when the co-op is ordering
- Dual (Both) new file missing the seller Inspection Response Reminder or Inspection Negotiated, or still generating a co-op welcome

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

## Section 6 — Updated task library (new files)

Use a **new** transaction for each of these. Older open tasks can still show yesterday’s target and copy — that is expected. The number on the row is the live ID (not the spreadsheet number from 360 onward).

### 27. Live IDs stay; Closing Gift is one row

**Route / Location**

New Buyer financed file and new Seller financed file → **Tasks**

**How To Test**

1. Create a new Buy-Fin file (100 Test Oak Lane is fine if you created it **after** this round went live). Open Tasks. Find **Closing Gift**. Note any ID shown on the row or in Complete this task.
2. Create a new Sell-Fin file. Find **Closing Gift** again. Also find **Schedule Pick Up of Sign and Lockbox** and **Change MLS Listing Status to Sold** if those names are on the listing.
3. Confirm you do **not** have extra Closing Gift rows that exist only because the file is Dual or listing-only.

**Expected Result**

- One **Closing Gift** on buyer files and on seller files (live **370**). It is an agent reminder, not an Autopilot client email.
- On a listing, lockbox and MLS Sold stay under live **453** / **455** if an ID is visible. Do not Fail because they are not numbered 470 / 480.
- Fail: no Closing Gift on a new listing; two Closing Gift rows on a Dual file; the screen renumbered Closing Gift to spreadsheet 360.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 28. Dual agency (Both)

**Route / Location**

Create **700 Test Dual Ave**. Represent **Buyer and Seller**. Financed. Contract uploaded. Contacts you control. Pin Assisted.

**How To Test**

1. Finish the wizard. Open **Tasks**.
2. Confirm **Buyer Welcome** and **Seller Welcome** both exist. Confirm **Co-op Agent Welcome** does **not**.
3. Confirm **one** Order Title **or** one Confirm Title Order (not both), and **one** Loan Officer Welcome.
4. Confirm **both** Inspection Scheduled (buyer and seller), **both** Inspection Response Reminder, and **both** Inspection Negotiated.
5. If you answered HOA = Yes in the wizard: Request HOA from the **seller**, Deliver HOA to the **buyer**. No request/deliver HOA to a co-op.
6. Open Co-op-target letters only to confirm they are absent (Deliver Utility Info to the buyer’s agent, Confirm Home Warranty, Buyer’s Agent Closing Information).

**Expected Result**

- Title and Loan Officer once. Buyer and seller party work both populate. No co-op letters (a Both file has no co-op).
- Fail: Co-op Agent Welcome on Dual; only the buyer inspection reminder; extra Dual-only copies of Deliver Title, Closing Gift, or Internal Thank You that exist only because the file is Both.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 29. Order Title vs Confirm Title Order

**Route / Location**

Two **new** Buyer financed files → Contract Details (who orders title) → Tasks → kebab → **Email transaction party**  
Do not Send unless To is an inbox you own.

**How To Test**

1. File A: wizard says **your side** orders title. Tasks should show **Order Title**, not Confirm Title Order.
2. File B: wizard says the **other side / co-op** orders title. Tasks should show **Confirm Title Order**, not Order Title.
3. On each, Email transaction party. Read the body. On Confirm Title Order, look for courtesy-order language (example: as a courtesy to the co-op agent, engage the escrow agent). It must **not** read as “has title been ordered?”
4. If Documents has a personal-property or monetary addendum / amendment, confirm it is **not** listed under the plan. The executed agreement package may still be there.

**Expected Result**

- Same document package on both letters. Difference is the script and which wizard answer created the row.
- Fail: both 70 and 80 on one file; Confirm Title Order is still a follow-up “was it ordered?”; addenda listed on the plan.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 30. Deliver Utility Info on a listing (160)

**Route / Location**

Create **800 Test Utility Ln**. Represent **Seller**. Financed. Upload a utility-information document on **Documents**. Pin Assisted.

**How To Test**

1. Open Tasks. Find **Deliver Utility Info**.
2. Kebab → Email transaction party. Note **To:**.
3. Close without sending if To is not yours.

**Expected Result**

- **To:** the co-op / buyer’s agent, not your seller.
- Fail: To is the seller; To is the buyer client; the letter is missing on a new listing that has utility info.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 31. Order Home Warranty is an internal reminder

**Route / Location**

New file where the wizard says **your side** orders the home warranty → Tasks → **Order Home Warranty** → Email transaction party

**How To Test**

1. Create a financed file with home warranty = yes, ordered by us.
2. Open Order Home Warranty. Read To, Cc, and the body.
3. If the wizard says the **other side** orders warranty, expect **Confirm Home Warranty** instead (To = co-op; TC on copy when a TC is assigned).

**Expected Result**

- Order Home Warranty: **To:** the transaction agent (you). TC on copy when assigned. Body is an internal reminder to place the order and send the invoice to title and the co-op. Not a letter to a warranty company.
- It waits for Send (or stays a draft). It does not send unattended.
- Fail: To is a warranty company; Autopilot already sent it; Dual still created a co-op Confirm Home Warranty (no co-op).

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---

### 32. No seller Inspection Completed on new listings

**Route / Location**

New Sell-Fin or Dual file → Tasks

**How To Test**

1. On a **new** listing, search Tasks for **Inspection Completed**.
2. You should still see seller **Inspection Scheduled** (notify the seller) and seller **Inspection Response Reminder** / **Inspection Negotiated**.
3. On a Dual new file, buyer Inspection Completed may still exist (the buyer has the inspection). The extra seller Inspection Completed row must not.

**Expected Result**

- New files do not get seller Inspection Completed (old live ID 235). Open 235 rows on **old** files can stay until someone completes them.
- Fail: a new listing generates Inspection Completed for the seller.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit._

> _Status:_ 
> 
> _Comments:_ 

---
