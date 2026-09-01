

# **VELVET ELVES**

## *AI-First Transaction Management Platform*

# **VELVET ELVES**

## **Aime and AI Automation Testing**

# **Features Currently Complete — Client Feedback Requested**

**Last Updated:** August 19, 2026   
**Test Environment:** https://app.stage.velvetelves.com   
**Recommended Browsers:** Chrome (please allow pop-ups)   
**Reviewer:** Jake and Audri — please fill in the Feedback block under each feature   
**Sign in:** with your own Velvet Elves account, in your own workspace

**Jan (1 Sep 2026):** Thank you. I compared this pass to the August 25 testing guidelines. You have filled Features 1–13 (Feature 5 has comments and no status). Features 14–26 are still open. The August 25 guidelines also add Features 27–32 for **new** Dual / title-order / utility / warranty files — please use that copy when you continue. Replies are under each of your comments.

# **How To Use This Document**

## **What is in this document**

This is the testing pass for Aime and AI automation as the product runs today. It covers:

\- How the live file is set: Manual / Assisted / Autopilot, and intake **Fast intake**

\- Named letters (welcomes, title order, pending reminder, inspection deadline reminder)

\- Needs You, drafts, inbound mail, money, dates

\- Closing Disclosure on closing-information letters, Terminated vs Closed, cash appraisal recipients

Each feature has a page address, numbered steps, a concrete example you can copy, what you should see, and a Feedback block.

Use **your** workspace and **your** files. Create a new transaction when a step needs a specific kind of file. Do not look for files created in someone else’s account.

## **How to work a feature (the method)**

Work one feature at a time, in order, like this:

1\. Read **Expected Result** first so you know what “right” looks like.

2\. Do every step under **How To Test**, including the example (or the same shape with your own street and inboxes).

3\. Compare the screen to Expected Result.

4\. Fill in Feedback before you move on. If you skip a feature, write **Skip** and one sentence why (for example “I am not Admin, so I could not open AI & Automation”).

**Pass** — the screen matched Expected Result. **Fail** — something important is wrong (wrong send, wrong person, missing copy, blank dialog). **Needs Work** — it mostly works but you would not ship it as-is (confusing wording, slow, hard to find).

Do not diagnose. Four sentences are usually enough:

\- "This is not how a deal actually goes."

\- "I would never send that to a client."

\- "I still had to do this by hand."

\- "I could not find where to do X."

**Example of a useful Fail comment**

\> Feature 12\. 100 Test Oak Lane → Tasks → Buyer Closing Information → Email transaction party. Documents has Closing Disclosure.pdf. The plan still listed Closing Disclosure.pdf under the body. I did not press Send. I expected no CD on this letter.

**Example of a useful Pass comment**

\> Feature 16\. 200 Test Maple Ave on Assisted. Buyer Welcome → Email transaction party. To was my \+buyer inbox. I sent once. One message arrived, signed as me, no “written by AI.” Nothing had gone out before I tapped Send.

## **Sample files and inboxes (use these or the same shape)**

Create these in **your** workspace. Put **only addresses you control** on the **Contacts** tab. A plus-address on the Gmail you connected is enough (for example you+buyer@gmail.com and you+coop@gmail.com).

| Suggested address | Kind of file | Pin posture | Used for |
| :---- | :---- | :---- | :---- |
| 100 Test Oak Lane | Buyer, financed, Contacts has emails you own, contract uploaded | Assisted (or workspace default) | Features 8–13 (reading, Complete this task, CD, status copy) |
| 200 Test Maple Ave | Buyer, financed, Contacts has emails you own, contract uploaded | **Manual** | Feature 15 — named letters must not send |
| 300 Test Pine Ct | Buyer, financed, Contacts has emails you own, contract uploaded | **Autopilot** | Feature 17 — named letters may send once |
| 400 Test Cedar St | Buyer, financed, **buyer email left blank** | Autopilot | Feature 18 — no guessed address |
| 500 Test Elm Dr | Buyer, cash, **Appraisal On This Cash Deal? \= Yes** | Assisted | Feature 14 Buy-Cash |
| 600 Test Birch Way | Seller, cash, co-op \+ TC on Contacts, appraisal \= Yes | Assisted | Feature 14 Sell-Cash |

You do not have to create all six on day one. Create 100 Test Oak Lane first. Add the others when you reach that feature.

**Worked example — one send-safe path vs one send path**

\- Send-safe: 100 Test Oak Lane → Tasks → kebab → Email transaction party → read To / body → close. Nobody’s inbox changes.

\- Send path (only when To is an inbox you own): same dialog → Send. Then check that inbox and the deal Email → Sent folder. If To is a real outside agent, **stop at the plan**.

## **What is not in this round**

Do not hunt for these in the product, and do not report them as misses.

\- Extra named letters beyond welcome, title-order, and inspection-reminder. Do not invent new letters that should send without a tap.

\- Buyers and sellers talking to Aime. Clients keep asking the team. A client-facing Aime chat is a fail if you see one.

\- A later amendment changing a date ("the file used to say X; this later signed document says Y"). Not shipped.

\- A countdown that then sends mail. Not built.

\- Listing or marketing after a fallen-through deal.

## **Accounts you will need**

\- **Your own account** on stage, in **your** workspace.

\- **Admin or workspace owner** for Settings → AI & Automation (How it runs, Overnight, Preview / Draft / Run, Fine-tune), **Try now (this deal only)** on Needs You, and the Terminated tile on the Admin dashboard. An Agent or Transaction Coordinator can still do mailbox, Needs You, files, and Complete this task.

\- A **connected Gmail or Outlook** mailbox on that account (Feature 1).

\- A **second address you own** for inbound tests (Feature 23). Sending from the same connected mailbox to itself proves little.

## **Safety before any send**

\- Open **Contacts** before Send. If a party is a real outside mailbox (a co-op at another brokerage, a real lender), stop at the plan. Do not press Send.

\- **Preview next tick** sends nothing. Prefer it. Example: the dialog says this tick would send 3 emails. Read who they are. Click **Got it**. Nobody is mailed.

\- **Draft due emails** writes drafts. It does not send. Example: toast says prepared 4 emails in Email review. Check Intelligence → Email. The drafts are there. Inboxes are unchanged.

\- **Run AI tasks (sends deal email)** can send named letters on **every Active Autopilot file in your workspace**, not only the file you have open. Confirm only after Preview lists addresses you own. Example: Preview lists you+buyer@gmail.com only → you may confirm. Preview lists otheragent@somebroker.com → cancel.

\- **Send** / **Send all ready** — only to mailboxes you control.

\- **Try now (this deal only)** retries one deal. It can send named letters on that Autopilot file. Admin only.

\- When a step asks you to open **Completed** or **Terminated**, read the copy. Do not click **Change status** unless you created that file only for this test.

\- If you toggle Hourly automation, Named letters, Aime signature, Inspection reminders, or How it runs, put them back when you are done.

## **Suggested order of testing**

1\. Mailbox, then (Admin / owner) Settings → AI & Automation

2\. Needs You, Fast intake on Confirm Details, and (optional) Register / onboarding cards

3\. 100 Test Oak Lane — posture, Contacts, Email, Complete this task, Closing Disclosure, Completed / Terminated

4\. Cash files (500 / 600\) for appraisal recipients

5\. Named letters on 200 / 300 / 400 (Manual, Autopilot, missing email)

6\. Drafts, blocked tasks, inbound wire mail, dates, and copy that should not appear

# **Section 1 — Mailbox and Settings**

## **1\. Email and e-signature connection**

**Route / Location**

Click your name (or avatar) in the top right → **Settings** → the **Email & E-signature** card /settings/connections

**How To Test**

1\. Open the page. The title at the top should be **Email & E-signature**.

2\. Find Gmail or Outlook. Note whether it says Connected and shows an address (example: you@gmail.com).

3\. Click **Test connection**. Watch the page. Do not expect a client email.

4\. Confirm **Disconnect** is visible next to the connected mailbox. Do **not** disconnect yet (that is Feature 20).

5\. If nothing is connected: click **Connect** on Gmail or Outlook, finish Google/Microsoft, walk the “Google hasn’t verified this app” screen if it appears (Advanced → continue), then Test connection.

**Expected Result**

\- Connected vs not connected is obvious. Example: “Connected as you@gmail.com.”

\- Test connection only checks the saved credentials. Open that mailbox: there is **no** new deal letter from this click.

\- Google’s unverified-app warning is expected on stage. If Connect has lapsed since last week, reconnect and note it — that is not a product miss.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ Needs Work

\> \> \_Comments:\_ Unable to get the “Test Connection” to work. I can click it but the email never comes through. I’ve checked inbox and spam.

**Jan:** This is not a miss on send. **Test connection does not send an email.** It only checks the saved Gmail or Outlook credentials. The result is the line under the provider on that Settings page (success or failure), not a message in inbox or spam. I will make that on-page result more obvious so the button does not look dead. If you clicked it and the page never showed a success or failure line, tell me — that would be a real Fail. 

## **2\. How it runs — Manual, Assisted, Autopilot**

**Route / Location**

Settings → **AI & Automation** (Workspace cards) → left nav **How it runs** /admin/confidence

Admin or workspace owner only. If you are an Agent, write Skip and go to Feature 5\.

**How To Test**

1\. Open How it runs. You should see three cards: **Manual**, **Assisted**, **Autopilot**, and a four-row table under them.

2\. Write down which card is currently selected. Example: “Workspace default is Autopilot.” You will put it back if you change it.

3\. Read each card’s one-line promise out loud against Expected Result.

4\. Read the four-row table the same way.

5\. Press F5 (refresh). Watch the small chip in the **page header** from the first paint — before the rest of the page settles. Example: it should say **Checking automation** (muted, not amber) for a moment, then **Automation active**.

6\. If you click a different card to see Save posture, click back to the original and **Save posture**.

**Expected Result**

\- Card promises, word for word:

\- Manual: \*AI suggests. You click to apply anything.\*

\- Assisted: \*Routine work runs. Named letters are drafted — you tap Send.\*

\- Autopilot: \*Authorized letters send when confidence is high enough. No tap.\*

\- Comparison table:

|  | Manual | Assisted | Autopilot |
| :---- | :---- | :---- | :---- |
| Routine actions | You click | Runs | Runs |
| Email drafts | You ask | Prepared — you tap Send | Ready, or Needs You if confidence is low |
| Welcome / title letters | Never auto | Drafted — you tap Send | Sends without a tap |
| Dates, waives, legal | You | You | You |

\- Fail examples: Assisted and Autopilot still describe the same send behavior; Autopilot still says you tap Send; the page says “library letters.”

\- Chip: **Checking automation** first, then the real state. Healthy: **Automation active**. Never checked in: **Automation is not running**. Was running, went stale: **Automation has stopped**.

\- Fail: the chip flashes **Automation has stopped** (amber) while the page is still loading, then flips to active.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.

\> \_Status:\_ Pass

\> \> \_Comments:\_ Please define “Inspection Reminders” in the Overnight section. Is referring to all reminder tasks, or is it specific to only the inspection tasks? Also, please confirm that regardless of automation posture, if a user turns off the notifications (toggles) that the rule we put in place to notify the user a task is due 3 days prior will still exist. 

Lastly, please switch the word letter(s) to email(s).

**Jan:** Copy only. Manual / Assisted / Autopilot send the same way. The 3-day nags were not built.

1. Overnight switch is now **Inspection deadline reminder**. Help: that deadline email to you only — not other reminder tasks, not Inspection Negotiated.
2. Turning off Notifications stops mail to you. Due dates on the file stay. The 3-day “step in” nags are not this switch and are not on staging.
3. How it runs (and matching captions) now say **named emails** / **authorized emails**. Autopilot still only sends welcomes, title order, pending reminder, and the inspection deadline reminder.

Local browser check (1 Sep 2026, Shyna): How it runs, Overnight, Always true, and Email replies all use **emails**. Overnight label is **Inspection deadline reminder** (deadline email to you only). Old “letters” / “Inspection reminders” labels are gone.

## **3\. Overnight switches and Always true**

**Route / Location**

Same page as Feature 2, the **Overnight** card, then **Always true** underneath Admin or workspace owner only.

**How To Test**

1\. Read the Overnight description at the top of the card. Example when everything is on: hourly automation is on; named welcome and title-order letters may send on Autopilot; on Assisted they are drafted for you to tap Send.

2\. Note the clocks: **Last tick** (for example “12 minutes ago”) and **Last draft sweep**. Note **Mailboxes · 1 healthy / 1 connected**, or a **Connect Gmail or Outlook** link.

3\. Write down the four switches as they are now, then leave them (or restore when a later feature is done):

| Switch | What you click | Example of Allowed / On | Example of Paused / Off |
| :---- | :---- | :---- | :---- |
| Hourly automation | Off / On | Overnight prep runs | Overnight prep will not run until you turn it on |
| Named letters | Paused / Allowed | Welcome and title-order letters may send on Autopilot; Assisted \= tap Send | Those letters will not send |
| Aime signature | Agent / Aime | Automatic named letters sign as Aime, Assistant to the agent | Automatic letters use the agent’s signature |
| Inspection reminders | Paused / Allowed | Deadline reminder may send on Autopilot | Those reminders will not send |

4\. Inspection reminders is **Paused** unless you turned it on. Named letters is **Allowed** unless you turned it off.

5\. Read **Always true** (four lines, with a red X on the wire line).

**Expected Result**

\- The Overnight story matches the switches. Example: if Named letters is Paused, the card should not promise that welcomes may send.

\- Always true, word for word:

\- Named welcome, title-order, and inspection-reminder letters may send on Autopilot when confidence is high enough. On Assisted they are drafted for one tap. Every other email is drafted for you to send.

\- Deadlines never move themselves.

\- Waives, legal calls, and packet release stay human.

\- Wire and funds mail is never drafted.

\- Fail: Named letters still labelled Autopilot; Inspection reminders promises to send repair or negotiation mail.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ Pass

\> \> \_Comments:\_ Can we change the word “Tick” to something else? The common user will not understand what that means.

**Jan:** Copy only. “Tick” was the hourly automation run. Overnight now says **Last run** / **Preview next run**. The preview dialog says **This run would send**. API names are unchanged.

Local browser check (1 Sep 2026, Shyna): chip **last run**; clocks **Last run** / **Last draft sweep**; button **Preview next run**; dialog **This run would send 0 emails** → Got it. Old “tick” labels are gone.

## **4\. Preview, Draft due emails, and Run AI tasks**

**Route / Location**

Overnight card, the row of buttons Admin or workspace owner only.

**How To Test**

Preview, Draft, Run, and Digest are **one row** on the Overnight card (Settings → AI & Automation → How it runs). They are not on Intelligence → Email and not on the deal Inbox. Scroll past the Manual / Assisted / Autopilot cards if the Overnight buttons are below the fold.

1\. Click **Preview next run**. Example of a safe dialog: “This run would send 0 emails” or a small number to addresses you recognize. Click **Got it**. Open your mailbox — nothing new from this click.

2\. If the count is greater than 0, screenshot or write the addresses. Example: you+buyer@gmail.com is fine. lender@bigbank.com means you must not Run later.

3\. Click **Draft due emails**. Wait for the toast. Example: “Draft sweep ran — Prepared 4 emails in Intelligence → Email. Nothing was sent.”

4\. Open **Intelligence → Email** (sidebar Intelligence group, item **Email**). Confirm new drafts. Unlinked rows should say **Needs a deal**, not **Reply ready**, and the pane must not offer **Approve & send**. Open **Needs You** and look for **To review** or **Ready to send**.

5\. Stay on Overnight. Click **Run AI tasks (sends deal email)**. Read the confirm. It should repeat the Preview. Click the cancel control — **do not** confirm unless every address is yours.

6\. Optional: **Send me my digest** only if Settings → Notifications has your morning digest on. That email is to **you**, not a client.

**Expected Result**

\- Preview is this workspace only. Got it sends nothing.

\- On Assisted, named letters that would otherwise send are **not** counted as would-send; they wait for a tap.

\- Draft due emails prepares drafts only. Inboxes unchanged.

\- Run AI tasks confirm is clearly a send (“real emails to real people”). Cancel sends nothing.

\- Fail: Preview or Draft puts a letter in a client inbox; Run has no confirm; Cancel still sends.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ Fail

\> \> \_Comments:\_ I don’t see where I can complete 3-6. Also, why are emails from my inbox populating into this inbox? Shouldn’t only be looking for items that are associated with the deals within VE? (see screenshot)

![][image1]

**Jan:** Steps 3–6 are still on **Overnight** (Settings → AI & Automation → How it runs), on the same card as **Preview next run**: **Draft due emails**, then the quieter **Run AI tasks (sends deal email)** and **Send me my digest**. They are not on Intelligence → Email and not on the deal Inbox. Please stay on Overnight for those clicks, then open Intelligence → Email only to confirm drafts from step 3.

Staging check (1 Sep 2026, platform admin `crazyaidev20500519@gmail.com`): Preview / Draft / Run / Digest all exist on Overnight. Staging still labeled the button **Preview next tick** (Feature 3 copy is not on staging yet). The four buttons sat below the first viewport because the How it runs cards fill the fold — scroll down the same page. Preview said “This tick would send 0 emails” → Got it. Nothing sent. Do not Fail Overnight if Preview sent nothing.

The screenshot is Intelligence → Email Inbox, not Overnight. That inbox can show inbound that has **not** matched a Velvet Elves file, so you can file or discard it. Aime must not send a reply to unmatched personal mail. The **deal** Email → Inbox should stay that file only.

Worse than “personal mail in VE”: this workspace had **0 Unlinked** chips, but mail was filed on the **wrong** deal. James Selman wrote about **1842 Willowbrook Lane** and Aime filed it on **9052 Sycamore Ridge** (unique party email on that file). Outbound library mail CC’d the connected Gmail, Gmail delivered that copy back as inbound **From** the same mailbox, and Aime drafted a reply to yourself on **12 Guide Test Way**. Both rows showed **Reply ready** and **Approve & send**. The pane even quoted the other file’s closing date.

Fixes in code (not on staging until deploy): skip inbound **From** the connected mailbox; if a unique party names a different street, leave the row unmatched; chip **Needs a deal** (never Reply ready) until linked; hide **Approve & send** until linked; server refuse send with no deal. Please do not Fail Overnight for the inbox issue — re-check Intelligence → Email after deploy.

# **Section 2 — Needs You and intake**

## **5\. Needs You**

**Route / Location**

Left sidebar → **Workflow** → **Needs You** /needs-you

**How To Test**

1\. Open Needs You. Wait until the orange count pill is a number, not **Loading**. Example: 3 waiting.

2\. Read the sentence under the title (empty state or “these items still need a person…”).

3\. If tiles are visible, click each: **Ready to send**, **To approve**, **To review**, **To decide**, **To handle**. Refresh. The same tile should stay selected.

4\. Click one row to expand it. Example of a blocked welcome: heading **Why the AI is asking**, a reason, and a link such as **Add contact**.

5\. In Search, type a street from a file **you** created (example: 100 Test Oak). The list should narrow to that deal, or show a clear empty state.

6\. If **Send all ready (N)** or **Approve all safe (N)** is enabled, click it, read the confirm, cancel. Example: confirm lists 2 Ready drafts. Cancel. Those 2 are still in the queue; nobody was mailed.

**Expected Result**

\- Breadcrumb: Workflow › Needs You. Title: Needs You.

\- Kind tiles as named above. Row pills may say Ready to send, AI proposal, Draft to review, Decision, AI task blocked.

\- Empty and healthy: \*Overnight prep ran. Nothing needs you. Named letters may still send on Autopilot deals; on Assisted they wait for Send.\* (The empty card may say “wait for you to tap Send.”)

\- Not empty: \*These items still need a person. Named letters may send on Autopilot deals; on Assisted they wait here for Send.\* Fail if the page says nothing needs you while cards are still visible.

\- Scheduler down: banner **Automation is not running** or **Automation has stopped**. Admin sees **Open AI & Automation**. There is no **Run AI tasks** button on this page.

\- Ready to send still needs Send. Example: expanding a Ready row shows Send; the party inbox does not have that letter yet.

\- Recovery verbs that exist on the card: Add contact, Upload document, Reconnect mailbox, Switch this deal off Manual.

\- Fail: buyers/sellers told to talk to Aime; “library letters”; Cancel on Send all ready still sends.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ 

\> \> \_Comments:\_ 5 does not narrow within the “Needs You” portion. It takes you to the expanded view of the transaction in the “Active Transactions” section.

**Jan:** Step 5 is the **Search** box on Needs You. Typing the street should filter the cards **on that page**. **Open deal** is a different control — it is supposed to take you to the transaction workspace. Please retry with Search only. If typing the street still leaves Needs You and opens Active Transactions, that is a Fail and I will fix Search. If Open deal was the click, that part of the test is a miss on the step, not the product.

## **6\. Fast intake**

**Route / Location**

**\+ New Transaction** → upload a contract → walk forward to **Confirm Details** /transactions/new

**How To Test**

1\. Click **\+ New Transaction**. Choose who you represent (example: **Buyer**) the way you usually do.

2\. Upload a signed purchase agreement you already use for testing. Wait until parsing finishes. Do **not** look for Fast intake on this upload step.

3\. Click through Contract Details as needed until the step title is **Confirm Details** (Verification in the stepper).

4\. Look at the **top** of that step for an orange banner.

5\. You can leave the wizard after you have seen the banner (or after you have confirmed it is absent). You do not have to finish the file for this feature.

**Expected Result**

\- Fast intake is **not** a sparkle control on upload. It is only the orange banner on Confirm Details, and only when the read is high confidence.

\- If the banner is there, example of a pass:

\- Small caps: **✦ Fast intake**

\- Heading: **Everything checks out at high confidence**

\- Body: the extraction double-check agreed, key fields cleared the confidence tier, timeline / checklist / task plan are ready below. Confirm the anchor date, then approve — or open any step from the top bar.

\- It does **not** say Autopilot. It does **not** mean Aime will email the buyer.

\- If the banner is missing, the read was not high confidence (a messy scan, missing dates, low confidence). **Skip** — not a Fail.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ Failed

\> \> \_Comments:\_ I don’t see the “Confirm Details” I only see “Verification” and never saw “Fast Intake”.

Also, please update the wizard  if the user chooses to upload a transaction right away after creating an account. It doesn’t act the same as if they had use the “New Transaction” it from the dashboard. It should be full screen and not a window within a window.

![][image2]

**Jan:** The stepper label is **Verification**. The page title on that step is **Confirm Details**. Fast intake is not a control on upload. It is only the orange **✦ Fast intake** banner at the **top of Verification / Confirm Details**, and only when the read is high confidence. If the banner is missing, that is **Skip**, not Fail (messy scan, missing dates, or low confidence). Please walk to Verification and look at the top of that page once on a clean signed contract.

The nested wizard after sign-up is a real miss. First-file upload from onboarding should be the same **full-screen** New Transaction flow as the dashboard, not a window on the onboarding cards. Recorded.

## **7\. Register and onboarding — the three cards**

**Route / Location**

Sign out (or a private Chrome window) → /register Onboarding after a new sign-up: /onboarding

Only if you can do this without disturbing a live account. A private window is safest. You do not have to finish creating an account.

**How To Test**

1\. Open /register. Scroll to **How should Aime start?**

2\. Read the three cards (Manual / Assisted / Autopilot) against Feature 2\.

3\. Leave Manual selected. You can close the tab. Skipping / leaving Manual means a new workspace starts on Manual.

4\. If you are already in onboarding on a throwaway account, read the same three cards there.

**Expected Result**

\- Same promises as Feature 2\.

\- Example: a brand-new sign-up that never changes this control lands on Manual. Named letters will not send until someone chooses Assisted or Autopilot **and** a mailbox is connected.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ Pass

\> \> \_Comments:\_ Please update “Letters” to “Emails”

**Jan:** Recorded — same as Feature 2. Register / onboarding cards will say **email** / **named emails**, and Autopilot will still mean only the authorized set.

# **Section 3 — A file you created**

Create **100 Test Oak Lane** (or any Active financed file in your workspace) for Features 8–13. Represent **Buyer**, financing **Financed**, upload a contract, put a buyer email **you** control on **Contacts**. Pin Assisted if you want named letters to wait.

## **8\. Deal posture on the workspace**

**Route / Location**

Open 100 Test Oak Lane (or your financed file) → the control in the workspace **header** next to the address

**How To Test**

1\. Open the file. Find Manual / Assisted / Autopilot in the header. Read the caption under it. Example on Assisted: \*Routine work runs. Named letters are drafted — you tap Send.\*

2\. Open the menu. If **Use workspace default** is listed, click it once. Example toast: “This deal follows the workspace default (assisted).”

3\. Pin **Manual** just to see the caption change, then put it back to Assisted (or Use workspace default) so Features 11–12 still have a usable file.

**Expected Result**

\- Manual: \*You apply AI proposals. Named letters wait until you switch this deal off Manual.\*

\- Assisted: \*Routine work runs. Named letters are drafted — you tap Send.\*

\- Autopilot: \*Authorized letters send without a tap when confidence is high enough. Everything else is drafted for you.\*

\- Use workspace default clears the custom pin. Changing How it runs in Settings later applies to this file again.

\- Fail: Autopilot’s caption still says you tap Send on named letters; Manual still promises unattended send.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ Needs Work

\> \> \_Comments:\_ Change “Named Letters” to “Emails”. Manual should read “AI suggests, you manually send the emails.”

![][image3] 

Also, can you please confirm how the settings work if you change it in settings? I’m assuming changing it deal to deal will override the settings feature, but it will default to the settings feature until the user chooses to change it within a transaction?

**Jan:** Named letters → **named emails**, same as Feature 2. Manual will not read “you manually send the emails.” On Manual, named emails **do not go out** until you take the file off Manual (or you send one yourself from Complete this task). Caption we will keep: AI suggests; you click to apply anything; named emails wait until this file is off Manual.

Your settings assumption is correct. **How it runs** is the workspace default. A pin on the file overrides that default until you choose **Use workspace default**. Changing How it runs later applies again to files that are still on the default.

## **9\. Contacts**

**Route / Location**

Same file → **Contacts** tab (the workbench tabs are Overview, Timeline, Compliance, Tasks, Documents, Contacts, Billing, Activity; Email and Agent appear when that workspace is on — there is no People tab)

**How To Test**

1\. Open **Contacts**. The page heading is **Contacts** (kicker **✦ Parties**). Groups on a buyer-rep financed file: **Buyer**, **Seller**, **Agents**, **Lender**, **Title**. Empty groups stay on the page with dashed copy (examples: \*No buyer on file\*, \*No co-op agent on file\*, \*No lender contact on file\*, \*No title contact on file\*). Title may also show the RESPA note about not requiring a particular title company.

2\. Look at the Buyer card. You should see a name (or \*Unnamed contact\*) and the role. The email address is **not** printed on the card. A **Mail** icon appears only when that party has an email. No Mail icon means the email is blank — that is allowed.

3\. Do not invent an address Aime “should have guessed” (do not look for info@titlecompany.com unless you typed it). If the buyer has no email, leave it. Feature 18 uses a dedicated file for wait-not-send.

4\. Adding uses the group buttons (**Add buyer**, **Add seller**, **Add agent**, **Add loan officer**, **Add title contact**). Clicking an existing card does not open an editor.

**Expected Result**

\- Every party Aime might email lives on this tab. Aime does not invent info@titlecompany.com.

\- Blank email is allowed (no Mail icon). That letter should wait, not send.

\- Fail: the workspace tab is still labeled People; a Mail icon on Title when you never added a title email.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ Needs Work

\> \> \_Comments:\_Please make this just like the contacts in the other view. When you click on a contact it should expand to see the contact info. Example below.

![][image4]

**Jan:** Recorded. On the deal **Contacts** tab, clicking a card should expand so you can see and edit that party (same idea as the directory). Clicking the card must not open compose. The Mail icon, when the party has an email, composes **to that party only**.

## **10\. Email tab**

**Route / Location**

Same file → **Email** tab

**How To Test**

1\. Open Email. Read the grey sentence under the header **before** you click anything.

2\. Click **Outbox**, then **Sent**, then **Inbox**. Example: Outbox shows drafts waiting; Sent is empty on a new file; Inbox is empty until Feature 23\.

3\. Do not Send unless To is an inbox you own.

**Expected Result**

\- Exact sentence: \*Nothing sends until you tap Send. On Autopilot, named welcome / title / inspection-reminder letters may already have gone out on their own. On Assisted they wait here for Send.\*

\- Three folders: Outbox, Sent, Inbox.

\- Fail: a sent body says “written by AI” or “generated by ChatGPT.”

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ Needs Work

\> \> \_Comments:\_1. Wording is confusing to a user. When you click on the email icon the contact you clicked on should already be highlighted. No one by the user should get a draft. 

I drafted an email from here  and it took be to the email “inbox” but nothing is there. How do I find my drafts? If you draft an email it should automatically take you to the draft section so you can approve/edit the email. 

![][image5]

The user should also be allowed to edit/add  the recipients in the “edit” portion of the outbox. They should be able to edit/add recipients anytime they are emailing through the system. 

They should also be able to add a recipient  not associated with the transaction as a one off situation.

**Jan:** Recorded.

1. Mail icon preselects that contact. Compose is not a draft to everyone else on the file.
2. Drafts live on **Outbox** (and Intelligence → Email), not Inbox. Inbox is inbound. After you draft, we should land you on Outbox. Today: Email tab → **Outbox**.
3. Edit / add recipients on the draft: yes.
4. A one-off To that is not on the file: yes, as a compose option you type. Autopilot still never invents an address and never sends to someone who is not on **Contacts**. 

## **11\. Complete this task stays on screen**

**Route / Location**

Same file → **Tasks**

If Buyer Closing Information is not there yet, wait until tasks generate, or use another closing-information task (Seller / Seller's Agent / Buyer's Agent Closing Information).

**How To Test**

1\. Find **Buyer Closing Information**. Click the **row**. It should only expand (instructions, dates). The email dialog should **not** open.

2\. Click the kebab (⋯) on that row → **Email transaction party**. (On My Task Queue, the same action is on the card when the task completes by email.)

3\. Wait until the plan loads (three pulse bars, then content).

4\. **Do not press Send.** Scroll from the orange Aime summary down through To, the body, and the footer buttons.

5\. Close with the X.

**Expected Result**

\- Title: **Complete this task**. Subtitle includes the task name and address (example: Buyer Closing Information · 100 Test Oak Lane).

\- When the plan can send: orange box \*Aime can complete this for you.\* plus a one-line summary.

\- **Transaction party** dropdown, then **To:** (and **Cc:** if anyone is on copy), then the message body, then Send / close in the footer.

\- You can scroll the middle. Fail example: only the header bar and the footer are visible; the middle has height zero; you cannot see who To is.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ Pass

\> \> \_Comments:\_

**Jan:** Thank you. No change on this feature.

## **12\. Closing-information emails never attach the Closing Disclosure**

**Route / Location**

Same Complete this task dialog, plus **Documents** on the file

**How To Test**

1\. Open **Documents**. Write down whether a file named like **Closing Disclosure** is on the file. Example: “Yes — Closing Disclosure.pdf” or “No CD on this file.”

2\. Re-open Buyer Closing Information → Email transaction party.

3\. Scroll under the body. Attachments only render if there is at least one. Example of a pass with a CD on Documents: you still do **not** see Closing Disclosure.pdf on this plan.

4\. Repeat for Seller Closing Information, Seller's Agent Closing Information, and Buyer's Agent Closing Information if they exist on this file.

5\. If you have a task named **Closing Disclosure Delivered**, open it separately — that letter **may** attach the CD. Do not treat that as a fail for this feature.

6\. Close without sending.

**Expected Result**

\- Buyer / seller / agent **closing information** letters never list a Closing Disclosure (or CD).

\- If Documents has a CD, it still must not appear here. If Documents has no CD, the plan must not invent one. No attachment list at all is fine.

\- Fail example: Buyer Closing Information plan shows Closing Disclosure.pdf as an attachment.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ Pass

\> \> \_Comments:\_Tested the best I could because I didn’t have a CD file. But nothing was attached to the Closing Disclosure Delivered task. Remember, this is a request/inquiry task. We aren’t delivering it. We are asking the lender if it’s been sent and signed by the buyer.

**Jan:** Closing-information with no CD on the plan is a Pass even when Documents has no CD. **Closing Disclosure Delivered** is an inquiry to the lender (has it been sent and signed), not a delivery of the CD, and it should **not** attach the CD. The test step that said that letter may attach the CD was wrong. I will correct it. Thank you.

## 

## **13\. Completed vs Terminated**

**Route / Location**

100 Test Oak Lane → status **pill** in the header (Active / Completed / …) Transactions list → **Terminated** tab Admin home (Admin only) → Terminated count tile

**How To Test**

1\. Click the status pill. Choose **Completed**. Read the dialog title **Change status to Completed?** and the paragraph. Do **not** click **Change status**. Close the dialog (X or the non-confirm action). The file should still be Active.

2\. Open the pill again. Choose **Terminated**. Read **Change status to Terminated?** Do not click **Change status**.

3\. Optionally open **Closed** the same way and read that paragraph, then close.

4\. Go to **Transactions**. Click the **Terminated** tab. An empty list is fine.

5\. If you have no Closed files, open Closed and read the empty hint.

6\. If you are Admin, open the Admin dashboard and find a **Terminated** tile separate from Closed / Completed.

**Expected Result**

\- Completed: \*Closing day is not the end of the file. Mark Completed when post-closing work is done (lockbox, MLS Sold, thank-you). Keep the file Active until then.\*

\- Terminated: \*The deal fell through. Automatic letters stop. History stays. This is not a closed sale.\*

\- Closed: \*Moves the deal off the active board and asks for post-closing feedback. Use after the file is done — not for a deal that fell through.\*

\- Closed empty hint: deals appear here once you mark them Closed or Completed. Files that fell through are Terminated, not Closed.

\- Fail: fallen-through is only offered as Closed; Completed tells you to finish the file on closing day while lockbox / MLS Sold / thank-you are still open.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.

\> \_Status:\_ Pass

\> \> \_Comments:\_ Again, “letters” should read “emails” 

![][image6]

I’m in an admin account and I don’t have the option of “Terminated”. I only have “Closed”. (screenshot”

![][image7]

**Jan:** Letters → emails, same as Feature 2. Terminated copy will say automatic **emails** stop.

Terminated: on the **file**, open the status pill in the workspace header (Active / Completed / Closed / Terminated). On **Transactions**, use the **Terminated** tab. Admin home → Pipeline “Deals by stage” also has Terminated. The create-transaction form does **not** offer Terminated — you do not open a file as fallen-through. If the **deal header pill** itself has no Terminated, that is a Fail; please confirm that was the control in the screenshot. Do not mark a live client file Terminated for this test; read the dialog and close.

---

**Jan:** Features 14–26 (and 27–32 on the August 25 guidelines) are not filled yet. Please continue from Feature 14. Use **new** files for Dual, Order Title vs Confirm Title Order, listing utility, Order Home Warranty, and cash appraisal. Stop at the plan if To is a real outside inbox.

## **14\. Cash Appraisal Ordered / Completed**

**Route / Location**

**\+ New Transaction** → cash file → Contract Details → **Appraisal On This Cash Deal?** After create: Tasks → kebab → **Email transaction party**

**How To Test**

**Buy-Cash (500 Test Elm Dr)**

1\. New Transaction. Represent **Buyer**. When financing is **Cash** (no mortgage), Contract Details shows **Appraisal On This Cash Deal?**

2\. Choose **Yes — buyer is appraising**. Helper: \*Appraisal follow-up tasks will be created.\* (If you choose **No appraisal**, helper: \*No appraisal tasks on this deal\* — those tasks will not exist. That is not a Fail; create another file with Yes.)

3\. Put the buyer email you control on **Contacts** (at intake, or **Add buyer** after create). Finish creating the file.

4\. Tasks → **Appraisal Ordered** → kebab → Email transaction party. Note **To:**. Repeat for **Appraisal Completed**. Do not Send.

**Sell-Cash (600 Test Birch Way)**

1\. New Transaction. Represent **Seller**. Cash. Appraisal \= Yes.

2\. On **Contacts**, under **Agents**, **Add agent** with you+coop@gmail.com (or another inbox you own). Use **Assign team** for a **transaction coordinator** with an inbox you own.

3\. Open Appraisal Ordered / Completed the same way. Note To and Cc.

**Both-Cash (optional):** represent Buyer & Seller, cash, appraisal Yes. Expect the same To as Buy-Cash.

**Expected Result**

\- Buy-Cash and Both-Cash: **To:** the Buyer (example: you+buyer@gmail.com). Not the loan officer. The agent may be on Cc.

\- Sell-Cash: **To:** the co-op agent. **Cc:** includes the assigned transaction coordinator. Not To the buyer. Not To the loan officer.

\- These tasks are not automatic sends. Closing the dialog sends nothing.

\- Fail: To is empty; To is the other side’s client on a listing; the task is missing even though you chose Yes — buyer is appraising.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

# **Section 4 — Named letters and drafts**

Create **new** files (200 / 300 / 400\) for this section. Pin posture on each file. A signed purchase agreement is enough unless a step says to omit it.

Letters that may send without a tap — **Autopilot only**, Named letters **Allowed**, file **Active**:

| Letter | To | Also needs |
| :---- | :---- | :---- |
| Buyer / seller / co-op welcome | That party | Their email on Contacts |
| Loan officer welcome | Lender | Email and the purchase agreement |
| Order Title / Confirm Title Order | Title company or title rep | Email and the purchase agreement. If title is already ordered, Confirm Title Order marks done — it does not mail twice |
| Pending reminder | You (the account holder), not a client | MLS pending nudge |
| Inspection response reminder | You (the account holder) | Inspection reminders **Allowed**. Deadline only. No repair or negotiation language |

Review Documentation completes with no email when the packet is signed. If signatures are missing, it drafts a chase — that chase waits for Send.

Order Home Warranty is drafted for you to send. It does not send on its own.

## **15\. Manual — named letters do not send**

**Route / Location**

Create **200 Test Maple Ave** (Buyer, financed, emails you control, contract on the file). Header posture → **Manual**. Admin: Settings → AI & Automation → Preview next tick

**How To Test**

1\. Finish the wizard. In the header, pin **Manual**. Caption should match Feature 8\.

2\. Open Tasks. **Buyer Welcome** (and Seller / Co-op if you captured them) should still be open, not completed.

3\. Admin: Preview next tick. 200 Test Maple Ave must not be in would-send. Example: “This tick would send 0 emails,” or the list is other Autopilot files only.

4\. Do **not** Run AI tasks for this feature.

5\. Check Email → Sent. No new buyer welcome from this pin.

**Expected Result**

\- Named letters stay open.

\- Needs You / Why the AI is asking can say: \*This deal is on Manual, so the AI will not send this email or complete this task on its own. Switch the deal off Manual, or complete it yourself.\* Recovery: **Switch this deal off Manual**.

\- Fail: a welcome is already in the buyer’s inbox after you pinned Manual, with no tap from you.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_

\> \> \_Comments:\_

## **16\. Assisted — you tap Send**

**Route / Location**

100 Test Oak Lane on **Assisted** (or create a new Assisted financed file) → Tasks → **Buyer Welcome** → Email transaction party

**How To Test**

1\. Confirm the header says Assisted.

2\. Open Buyer Welcome → Email transaction party. Read **To:** — example you+buyer@gmail.com.

3\. Check that mailbox **before** Send. The welcome should not be there yet.

4\. If To is yours, you may press Send **once**. Then check the mailbox and Email → Sent.

5\. If To is not yours, close the dialog.

**Expected Result**

\- To is the buyer. The letter waits. Assisted does not send with no tap.

\- Why the AI is asking can say: \*This deal is on Assisted, so Aime drafted the letter for you to tap Send. Autopilot is the setting that sends authorized letters without a tap.\*

\- After one Send from Complete this task: one message, right To, address \+ closing date in the body, **agent’s** signature (your name), no “written by AI.” If the body says a file is attached, that file is on the email.

\- A Ready named-letter draft Aime prepared overnight (Intelligence → Email, not this dialog) may still sign as Aime when Aime signature is On. That is a different path. Note it; do not Fail Complete this task for it.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

## **17\. Autopilot — named letters may send once**

**Route / Location**

Create **300 Test Pine Ct** (Buyer, financed, tester emails, contract uploaded). Pin **Autopilot**. Admin: Preview next tick, then **Run AI tasks (sends deal email)** only if would-send is entirely yours.

**How To Test**

1\. Settings → AI & Automation: Named letters **Allowed**, Hourly automation **On**.

2\. Create 300 Test Pine Ct. On **Contacts**: buyer / co-op / lender / title \= inboxes you own. Pin Autopilot.

3\. Preview next tick. Example of a go: would-send lists you+buyer@gmail.com (Buyer Welcome) only. Example of a stop: would-send lists a live lender you do not control → **Got it** / cancel Run.

4\. If the list is only yours, confirm **Run AI tasks (sends deal email)**.

5\. Check Tasks: Buyer Welcome may be completed. Check the buyer inbox: at most **one** welcome.

6\. Preview again. That welcome must not be in would-send. Do not expect a second copy if you Run again.

**Expected Result**

\- Welcomes for parties you captured may send and complete.

\- Loan officer welcome and Order Title wait without the purchase agreement; they may send if the contract is on the file.

\- At most one of each letter. Confirm Title Order does not mail again if title is already ordered.

\- Automatic named letters sign as **Aime, Assistant to the agent** when Aime signature is On.

\- Fail: second welcome; letter to someone not on Contacts; Order Title sent with no purchase agreement.

\- Paused / Terminated / Completed / Closed files are not in would-send.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

## **18\. No buyer email, and no purchase agreement**

**Route / Location**

**400 Test Cedar St** — Autopilot, buyer email **blank** A second Autopilot file with **no** purchase agreement uploaded Needs You → **To handle**

**How To Test**

**Missing email**

1\. Create 400 Test Cedar St. Leave the buyer email empty on **Contacts**. Pin Autopilot.

2\. Open Buyer Welcome on Tasks. Open Needs You → To handle. Expand the row.

3\. You should see **Add contact**, not **Give this back to the AI**.

4\. Click **Add contact**. You should land on **Contacts**. Use **Add buyer** to put you+buyer@gmail.com on a buyer and save. Clicking an existing Buyer card does not open an editor.

5\. Admin: **Try now (this deal only)** on that card, or wait for the next hourly run. Do not expect Give-back on this block.

**Missing contract**

1\. Create an Autopilot financed file and skip the purchase agreement (or do not upload it).

2\. Open **Order Title** and **Loan Officer Welcome**. Needs You should offer **Upload document**.

3\. Confirm nobody received a title-order email that claims the contract is attached.

**Expected Result**

\- No buyer email: flagged, no send to a guessed or platform address.

\- No contract: flagged missing document; no send that promises the contract without the file.

\- Give this back to the AI is **absent** on these two blocks. Try now (this deal only) is Admin only and touches **this deal only**.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

## **19\. Inspection response reminder**

**Route / Location**

Settings → AI & Automation → Inspection reminders (Admin / owner) A file with an inspection response deadline → Tasks

**How To Test**

1\. On Overnight, note Inspection reminders. It is **Paused** unless you already turned it on.

2\. Switch to **Allowed**. You will switch it back when this feature is done.

3\. Open a file that has an inspection response deadline (your financed test file if the contract had one). Find **Inspection Response Reminder** (or the same name on Tasks).

4\. On Autopilot, open the plan / wait for overnight. Read the body: it should be a deadline nudge to **you**.

5\. Pin the same file **Assisted** and confirm that letter is a draft for Send, not already in your inbox.

6\. Set Inspection reminders back to **Paused**.

**Expected Result**

\- To is you (account holder), not the buyer or seller.

\- Deadline only. Fail examples in the body: “please send repair requests,” “accept or reject the inspection,” negotiation language.

\- Inspection Negotiated (or similar) does not send on its own.

\- If you leave the switch Paused, the task is flagged that inspection response reminders are paused. That is not a Fail.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

## **20\. Mailbox down**

**Route / Location**

Settings → Email & E-signature → **Disconnect** Then 300 Test Pine Ct (Autopilot) → Tasks / Needs You

**How To Test**

1\. Disconnect Gmail or Outlook. Confirm the page now shows not connected.

2\. Preview next tick or open a named letter that was waiting on 300 Test Pine Ct. Needs You may show **Reconnect mailbox** or **Connect mailbox**.

3\. Confirm no new named letter arrived in a party inbox during the disconnected window.

4\. **Connect** again and Test connection before you leave this feature.

**Expected Result**

\- Named letter flagged (reconnect / no provider). No send while disconnected.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

## **21\. Prepared drafts and Send all ready**

**Route / Location**

After Feature 4: sidebar **Intelligence** → **Email** /ai-emails

Page title is **Email**, not “AI Emails.”

**How To Test**

1\. Open Intelligence → Email. Breadcrumb: Intelligence › Email.

2\. Open a draft that is **not** Buyer Welcome / Order Title. Example: a due-task reminder or Order Home Warranty.

3\. Note whether it is in review or marked Ready.

4\. If **Send all ready** is enabled, click it, read the recipient list, cancel. Example: “Send all ready · 2”. Cancel. Those 2 still sit there.

5\. You may Send **one** Ready draft if To is an inbox you own. Then check that inbox and the deal Email → Sent.

**Expected Result**

\- Assisted: draft sits in review (not Ready). Autopilot: it may be Ready. Ready means one tap, not already sent.

\- Cancel on Send all ready sends nothing.

\- After a real Send: one message; the row leaves Ready; deal Email → Sent shows it.

\- Fail: a non-named draft left with no Send; body says “Attached is the inspection report” with nothing attached.

\- Order Home Warranty may appear as a draft; it must not auto-send.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

## **22\. Blocked tasks — Give-back, Try now, and recovery**

**Route / Location**

Needs You → **To handle** or Tasks on the file from Feature 18 / 15

**How To Test**

Use the card in front of you; do not hunt for every code.

| What you set up | What the card should offer | What you do |
| :---- | :---- | :---- |
| Buyer email blank (400 Test Cedar St) | **Add contact** | Add the email. Then wait or (Admin) **Try now (this deal only)**. No Give-back. |
| No purchase agreement | **Upload document** | Upload the contract. Then wait or Try now. |
| Mailbox disconnected | **Reconnect mailbox** / **Connect mailbox** | Reconnect. Then wait or Try now. |
| Task more than 30 days overdue | **Use today's date and retry** | Click it. Due date moves to today. Nothing sends until the next run. |
| Execution error (if you have one) | **Give this back to the AI** | Click it. Toast: nothing was sent. |
| File on Manual (200 Test Maple Ave) | **Switch this deal off Manual** | Read it. You may leave Manual. |

**Expected Result**

\- Give this back to the AI does not send.

\- Try now (this deal only) is Admin only. Toast example: “Tried this deal — Completed 0, flagged 1\. Nothing else in the workspace was touched.” If the file is Autopilot and the block is cleared, this click **can** send that deal’s named letters — check **Contacts** first.

\- Fail: the card tells you to click a button that is not there; Give-back on a missing-email row; Give-back mails the party.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

# **Section 5 — Boundaries**

## **23\. Inbound mail and money**

**Route / Location**

100 Test Oak Lane → Email → **Inbox** Send from a **second** address you own **to** the connected mailbox (the one on Email & E-signature)

**How To Test**

1\. Put 100 Test Oak Lane (or your real test street) in the subject or first line so the mail can match the file.

2\. From a **different** inbox, send four messages to your connected mailbox, one at a time. Wait until each appears on Email → Inbox (or Needs You) before sending the next.

**Message A — factual question (should draft, must not send)**

Subject: 100 Test Oak Lane — closing date Body: When is the closing date for 100 Test Oak Lane?

**Message B — statement (must not vanish)**

Subject: 100 Test Oak Lane — title Body: The title commitment is ready.

**Message C — wire (must not draft or send)**

Subject: 100 Test Oak Lane — wire Body: Please send the wire instructions for 100 Test Oak Lane.

**Message D — banking (must not draft or send)**

Subject: 100 Test Oak Lane — banking Body: Please send banking details for closing.

3\. After C and D, open Intelligence → Email and Needs You → Ready to send. Confirm those two did not become a Ready reply you could Send all ready.

**Expected Result**

\- A: kept on the deal. A factual draft or Ready. Does **not** leave the mailbox until you Send (and you should not Send unless you mean to).

\- B: kept. Must not disappear. Draft optional.

\- C and D: **no** reply draft, **not** Ready, **does not send**. Fail if Aime replies with wiring or account numbers, or if a Ready money draft appears.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

## **24\. Dates never move themselves**

**Route / Location**

100 Test Oak Lane → **Ask AI** (agent pane on the right)

**How To Test**

1\. Note the current closing date (example: August 30, 2026\) on Timeline or the header.

2\. In Ask AI, type: Change the closing date on 100 Test Oak Lane to September 15, 2026\.

3\. Wait for a proposal with a preview of what else would move.

4\. Click **Dismiss**. Do **not** click **Approve**.

5\. Check the closing date again — it should still be August 30, 2026 (your original).

**Expected Result**

\- A preview appears. Nothing moves until **Approve**.

\- Dismiss leaves every date. Date cascade is not in Always-approve automation rules (Fine-tune → Automation rules → Never automatic).

\- Fail: the date changed with no Approve.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

## **25\. Digest, Fine-tune, and Paused files**

**Route / Location**

Settings → **Notifications** (morning digest) Settings → AI & Automation → Fine-tune: **AI model**, **Email replies**, **Automation rules**, **Confidence gates** (Admin / owner) 200 Test Maple Ave or 300 Test Pine Ct → pin **Paused**

**How To Test**

1\. Settings → Notifications. Note whether morning digest is on or off **for you**. Change How it runs (Manual ↔ Assisted) and come back — digest should be unchanged. Posture is not a team-wide digest switch.

2\. Overnight → **Send me my digest**. If digest is off, expect “Nothing to send” / turn it on in Notifications. If digest is on, you (not a client) get the email.

3\. Fine-tune: open Email replies, Automation rules, Confidence gates. Confirm there is **no** Preview next tick / Run AI tasks here. Under Automation rules, read **Never automatic** — dates, waives, and send-email still need a person.

4\. On 300 Test Pine Ct, pin **Paused**. Admin: Preview next tick. This file must not be in would-send. Named letters must not keep going.

**Expected Result**

\- Digest is per-user. Changing posture does not turn digest on for the team.

\- Fine-tune cannot put the workspace into “send named letters on Manual.”

\- Paused, Terminated, Completed, and Closed files do not keep sending named letters.

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

## **26\. Words that should not appear**

**Route / Location**

The surfaces you already opened: Settings → AI & Automation, Needs You, Confirm Details, 100 Test Oak Lane Email and Tasks

**How To Test**

1\. You do not need a special hunt. While you work Features 1–25, jot anything that matches the fail list.

2\. Extra glance: Confirm Details banner (Feature 6), How it runs cards (Feature 2), Email tab sentence (Feature 10).

**Expected Result**

Fail if you see any of these in the product:

\- “Library letters”

\- Intake banner still called Autopilot (it is **✦ Fast intake**, and only on Confirm Details when confidence is high)

\- Assisted described as “no tap,” or Autopilot described as “you tap Send” on named letters

\- A client-facing Aime for buyers or sellers

\- A countdown that will send without you

\- “Written by AI” on an outbound body

\- Wire / funds treated as a Ready draft

\- Fallen-through deals filed as Closed with no Terminated path

**Feedback**

\_Please note: Status (Pass / Fail / Needs Work), and any comments or issues you hit.\_

\> \_Status:\_ \> \> \_Comments:\_

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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>

[image3]: <data:image/png;base64,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>

[image4]: <data:image/png;base64,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>

[image5]: <data:image/png;base64,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>

[image6]: <data:image/png;base64,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>

[image7]: <data:image/png;base64,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>