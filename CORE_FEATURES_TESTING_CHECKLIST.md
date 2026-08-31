# Core Features — Testing Checklist

**Prepared by:** Jan (sole developer)
**Date:** July 31, 2026
**For:** Audri and Jake
**Where to test:** the stage site — `https://app.stage.velvetelves.com`
**Use with:** `CORE_FEATURES_TESTING_GUIDE.md` (the same items, with the detail)

---

## How to use this

This is the tick-box version of the testing guide. Every line is one thing to
try. Work down it in order — the parts build on each other.

Against each line, write one of:

- **Pass** — it did what you expected
- **Fail** — it did not work at all
- **Needs work** — it worked, but not the way a real deal goes

Then, in the **Notes** box at the end of each part, tell us anything you would
change. A sentence is enough. The notes are worth more to us than the ticks.

**Please do not tick these — they are known and deliberate:**
automation does not run on a timer · no "Try again" on a blocked AI task · one
vendor task emailed at a time · two tasks can share a name · no in-app password
change · Sharing is a placeholder · AI Coach does nothing · the assistant's
microphone is off · "Filtered out" is mentioned but does not exist.

**Not in this round:** the New Transaction wizard; the Client, FSBO and Vendor
portals; the Attorney workspace; public links; Velvet Elves platform screens.

**Roles:** lines marked **[TL]** need a Team Lead, **[A]** an Admin or the
workspace owner. Everything else works as an Agent.

---

## Part 1 — Getting in

| # | Check | Result |
|---|---|---|
| 1.1 | `/register` shows Full name, **Role** (Agent / Team Leader / Transaction Coordinator / Admin), Organization, Email, Password, Confirm, Phone, Terms tick-box | |
| 1.2 | An email already in use is blocked, with a "sign in instead" link | |
| 1.3 | A weak password says which rules are unmet; mismatched passwords block the button | |
| 1.4 | Onboarding asks for name, phone, role — and company + logo if you are the first person in the brokerage | |
| 1.5 | Onboarding offers to connect Gmail, Outlook and DocuSign, and lets you skip | |
| 1.6 | Sign out from the avatar menu returns you to the sign-in page | |
| 1.7 | Pasting `/dashboard` while signed out sends you to sign-in | |
| 1.8 | "Forgot password?" emails you a working reset link | |

**Notes on Part 1:**

>
>
>

---

## Part 2 — The shape of the app

| # | Check | Result |
|---|---|---|
| 2.1 | Sidebar shows Deals, Workflow, Payments, Vendors, Intelligence — plus Team **[TL]** and Oversight **[A]** | |
| 2.2 | The counts beside sidebar entries match what you find when you open them | |
| 2.3 | Today's AI Briefing shows Critical / Needs Attention / On Track, and clicking one filters the deal list to exactly those deals | |
| 2.4 | Search (or ⌘K / Ctrl+K) finds a transaction, a task, a contact and a document | |
| 2.5 | The avatar menu opens Settings, the Help Center and Log Out | |
| 2.6 | Your dashboard leads with what needs deciding today, and its numbers agree with the rest of the app | |

**Notes on Part 2:**

>
>
>

---

## Part 3 — Connect your mailbox

| # | Check | Result |
|---|---|---|
| 3.1 | Settings → Email & E-signature connects Gmail (or Outlook) and shows **Connected** with your address | |
| 3.2 | **Test connection** reports "Connected as …" and sends nothing | |
| 3.3 | DocuSign connects | |
| 3.4 | When the connection expires you are told to **reconnect** — you are **not** signed out of Velvet Elves | |

**Notes on Part 3:**

>
>
>

---

## Part 4 — The deal list

| # | Check | Result |
|---|---|---|
| 4.1 | Filter tabs (All, Overdue, Due Today, Needs Attention, Closing Soon, In Inspection, On Track, Unhealthy) each show the deals they say they will | |
| 4.2 | Sort by Urgency / Close Date / Client Name / Price reorders the list sensibly | |
| 4.3 | Export CSV, Export Excel and Print Report all produce a usable file | |
| 4.4 | **[TL]** The team-member filter narrows to one person's deals | |
| 4.5 | Pending / Closed / All Transactions in the sidebar show the right deals | |
| 4.6 | Expanding a card shows Tasks, Key Dates and Contacts, and they match the deal | |
| 4.7 | You can tick a task complete and edit a key date from the card | |
| 4.8 | Card buttons work: Open workspace, View/Add Docs, Print, History, Comms, Client access, Client Q&A, Invoice | |
| 4.9 | **[TL]** Delete asks for confirmation and names the property | |

**Notes on Part 4:**

>
>
>

---

## Part 5 — One deal: the workspace

| # | Check | Result |
|---|---|---|
| 5.1 | The header shows the property, its stage, its address and how far through the tasks it is | |
| 5.2 | Changing the status works, and moving to **Closed** asks for post-closing feedback | |
| 5.3 | The AI assistant answers a plain-English question about the deal correctly | |
| 5.4 | `/` commands, `@` for people and `#` for items all work in the assistant | |
| 5.5 | Dragging a row into the assistant, or using **Ask AI** on a row, brings that item into the conversation | |
| 5.6 | The assistant **proposes** and you approve — it never changes anything on its own | |
| 5.7 | Hiding and showing the assistant panel works, and is remembered next time | |
| 5.8 | **Timeline** — changing a key date shows what else moves **before** you apply it | |
| 5.9 | **Timeline** — the derived deadlines are what you would have written from that contract | |
| 5.10 | **Compliance** — you can attach an existing file, upload a new one, and mark a row not applicable | |
| 5.11 | **Compliance** — the AI tells you when it read an uploaded document as something other than the row asked for | |
| 5.12 | **Documents** — upload from the button, and by dragging a file onto the page | |
| 5.13 | **Tasks** — the task list is the right one for this kind of deal (nothing missing, nothing you would never do) | |
| 5.14 | **Tasks** — a task showing "Waiting on an earlier step" really should be waiting | |
| 5.15 | **Tasks** — an amber "AI needs you" task explains itself clearly enough to fix | |
| 5.16 | **Contacts** — everyone is under the right heading; you can add, edit, assign a teammate and manage client access | |
| 5.17 | **Activity** — History explains what changed; the Automation lens shows only what ran without a click, with Undo | |
| 5.18 | **Email** — this deal's Outbox and Inbox show the right messages | |

**Notes on Part 5:**

>
>
>

---

## Part 6 — Needs You

| # | Check | Result |
|---|---|---|
| 6.1 | The five groups (Ready to send, To approve, To review, To decide, To handle) each filter the list when clicked | |
| 6.2 | Answering a **decision** immediately updates the tasks it was holding back | |
| 6.3 | Approving an **AI proposal** does what the preview said it would | |
| 6.4 | **Send all ready (N)** names how many recipients before it sends | |
| 6.5 | A **blocked AI task** gives a reason you can act on, and clears once you fix the cause | |
| 6.6 | Everything on this page is genuinely a decision for a person | |

**Notes on Part 6:**

>
>
>

---

## Part 7 — My Task Queue

| # | Check | Result |
|---|---|---|
| 7.1 | The counters (Critical, Attention, On track, Done today) filter the list when clicked | |
| 7.2 | Type tabs (All, Documents, Communication, Milestones, Admin) narrow the list correctly | |
| 7.3 | The Priority / Vendor grouping toggle, sort and search all work | |
| 7.4 | **Add task** creates a task on the deal you chose | |
| 7.5 | Expanding a task shows its notes, its AI assistance, and the action that finishes it | |
| 7.6 | **Draft with AI** produces suggestions you would actually use | |
| 7.7 | Reschedule works, including Tomorrow / In 3 days / Next week | |
| 7.8 | Call and Email on a task's contacts open with the right person | |
| 7.9 | **Email transaction party** pre-selects the right recipient | |
| 7.10 | The drafted subject and message fit the task | |
| 7.11 | Your edits survive into the sent email | |
| 7.12 | **Send & complete task** sends **and** marks the task complete — check your Sent folder | |
| 7.13 | **I'll handle it myself** closes the window and leaves the task alone | |
| 7.14 | Attachments on the email are the ones you expected — no more, no fewer | |

**Notes on Part 7:**

>
>
>

---

## Part 8 — All Documents

| # | Check | Result |
|---|---|---|
| 8.1 | The tabs (AI priority, All docs, Missing, Pending review, Sent for sig, Signed) each list what they claim | |
| 8.2 | The AI priority queue's top item is genuinely the most urgent thing | |
| 8.3 | The suggested actions on a row make sense for that document | |
| 8.4 | **Upload** assigns the file to a transaction and a document type | |
| 8.5 | **Preview** opens the document; **Download** saves a file rather than opening a tab | |
| 8.6 | **Send for Sig** sends through DocuSign and lands under Sent for sig | |
| 8.7 | Sync, Resend and Void work on an envelope already sent | |
| 8.8 | Email Document, Rename / Reclassify / Reassign, and Version History all work | |
| 8.9 | **Archive** removes a document, and **Restore archived** brings it back | |
| 8.10 | **[TL]** The Deletion Queue lets you approve or reject a flagged deletion | |
| 8.11 | The Missing tab does not ask for anything you have already uploaded | |
| 8.12 | Bulk actions on the Missing tab work | |
| 8.13 | **Cleared Today** only counts documents you actually resolved — not requests, calls or flags | |

**Notes on Part 8:**

>
>
>

---

## Part 9 — Email

| # | Check | Result |
|---|---|---|
| 9.1 | The **Outbox** tab lists prepared emails with correct counts | |
| 9.2 | Opening a draft shows the recipient, subject, body, what the AI based it on, and — for a reply — the original message | |
| 9.3 | **Approve & send** sends it, and it appears in your Sent folder | |
| 9.4 | **Edit** → **Send edited** sends your version, not the original | |
| 9.5 | **Regenerate** redraws a reply from the original message | |
| 9.6 | **Discard** removes the draft and leaves the original message in the log | |
| 9.7 | **Send all ready · N** names the count before sending, and only sends pre-approved drafts | |
| 9.8 | A reply sent from a **second** mailbox arrives in the **Inbox** tab, on the right deal | |
| 9.9 | Incoming mail is labelled with the right kind (money, date change, document, question, update) | |
| 9.10 | The AI's suggested reply gets the dates right and promises nothing you would not promise | |
| 9.11 | The deal filter and search work on both tabs | |
| 9.12 | Ticking rows and deleting them works, and "not mail I need" removes a message | |
| 9.13 | **No email anywhere mentions that AI wrote it** | |

**Notes on Part 9:**

>
>
>

---

## Part 10 — Closing Calendar

| # | Check | Result |
|---|---|---|
| 10.1 | Month and Agenda views both show your key dates | |
| 10.2 | **Closings only** narrows to closings | |
| 10.3 | Month navigation and **Today** work | |
| 10.4 | Every date on the calendar matches the deal it came from | |
| 10.5 | **Connect calendar** links Google or Outlook, and **Add my closings** puts them there | |

**Notes on Part 10:**

>
>
>

---

## Part 11 — Clients, Contacts and Vendors

| # | Check | Result |
|---|---|---|
| 11.1 | **Clients** lists everyone you gave portal access to, with "to answer" and "to review" counts that are right | |
| 11.2 | **Contacts** searches by name, email and company, and the type filters work | |
| 11.3 | **Vendors only** narrows Contacts to vendors | |
| 11.4 | **Vendor Directory** search and category filter work | |
| 11.5 | Opening a vendor shows its contacts, the deals it has worked, and its background details | |
| 11.6 | No duplicates that should obviously be one record | |

**Notes on Part 11:**

>
>
>

---

## Part 12 — Notifications and the morning digest

| # | Check | Result |
|---|---|---|
| 12.1 | The bell's unread count is right | |
| 12.2 | **Mark all as read** clears the badge, and it stays clear | |
| 12.3 | **View all** opens the full page, and All / Overdue / Today / Tomorrow / Upcoming filter it | |
| 12.4 | Settings → Notifications lets you choose which alerts you get | |
| 12.5 | **Morning digest** is off until you turn it on | |
| 12.6 | The sample digest arrives and lists the right work | |

**Notes on Part 12:**

>
>
>

---

## Part 13 — Settings

| # | Check | Result |
|---|---|---|
| 13.1 | The Settings search finds a card by what it does ("gmail" finds Email & E-signature) | |
| 13.2 | You only see cards you are allowed to use — none leads to a "not allowed" page | |
| 13.3 | **Profile** saves your photo, name, sign-in email, phone, bio and email signature | |
| 13.4 | **Email Templates** — you can create a template and use it | |
| 13.5 | **My Playbook** — your checklists, notes, vendors and resources save | |
| 13.6 | **Help & Tour** replays the guided tour | |
| 13.7 | **[A]** **Company** — brokerage name, plan and seats are right | |
| 13.8 | **[A]** **Branding** — your logo and colour show up in the app **and** on an outbound email | |
| 13.9 | **[A]** **Document Templates** — your own fillable PDF generates from a deal with the right fields filled | |
| 13.10 | **[A]** **Vendor Templates** — the standard vendor emails read the way you would send them | |
| 13.11 | **[TL]** **Team Playbook** — shared checklists and vendors reach team members | |
| 13.12 | **[A]** **Payment Access** — the roles that can invoice, refund and pay out are right | |
| 13.13 | **[A]** **Integrations & Webhooks** loads and saves | |
| 13.14 | Nothing you looked for was missing from Settings | |

**Notes on Part 13:**

>
>
>

---

## Part 14 — Team and oversight

| # | Check | Result |
|---|---|---|
| 14.1 | **[TL]** **Team Overview** shows your team's people and production accurately | |
| 14.2 | **[TL]** **Teams** — you can build a team, see its members and invite into it | |
| 14.3 | **[TL]** **Users & Invites** — invite someone, and the invitation arrives | |
| 14.4 | **[TL]** Changing a member's role takes effect | |
| 14.5 | **[A]** Deactivating a member removes their access | |
| 14.6 | **[A]** Transfer workspace ownership works (owner only) | |
| 14.7 | **[TL]** **Task Templates** — the task list for each deal type is the one **you** would run | |
| 14.8 | **[A]** **AI & Automation** — Manual / Assisted / Autopilot each behave as described | |
| 14.9 | **[A]** **Draft due emails** prepares drafts and sends nothing | |
| 14.10 | **[A]** **Run AI tasks** confirms first and names who will receive email | |
| 14.11 | **[A]** **Send me my digest** sends only if your digest is switched on | |
| 14.12 | **[A]** **Communication Audit** contains every message you sent, and CSV download works | |
| 14.13 | **[A]** **Audit Log** rows are understandable without a developer | |

**Notes on Part 14:**

>
>
>

---

## Part 15 — Analytics and AI Suggestions

| # | Check | Result |
|---|---|---|
| 15.1 | Analytics numbers (GCI, transactions) match what you would calculate yourself | |
| 15.2 | **Set your goals** saves, and progress shows against the goal | |
| 15.3 | **Export PDF** produces a usable report | |
| 15.4 | **AI Suggestions** — each one explains why it was flagged | |
| 15.5 | Acting on a suggestion does what it said it would; dismissing one removes it | |

**Notes on Part 15:**

>
>
>

---

## Part 16 — Invoices, Payments and Billing

| # | Check | Result |
|---|---|---|
| 16.1 | **Invoice** on a deal card creates an invoice pre-filled with that deal | |
| 16.2 | Invoices & Payments search by invoice number, payer and property works | |
| 16.3 | Opening an invoice shows the right detail | |
| 16.4 | **[A]** Billing shows the per-deal fee, and it matches the price you were told | |
| 16.5 | **[A]** Creating a deal charges once — and only once | |
| 16.6 | **[A]** Deleting a deal inside the refund window refunds it | |
| 16.7 | **[A]** Pay ahead buys prepaid deals, and they are used before your card is charged | |

**Notes on Part 16:**

>
>
>

---

## Part 17 — A day in the life

Spend one session working the way you actually work, then answer these.

**Could you finish a task without leaving My Task Queue?**

>
>

**Did Needs You show only things a person genuinely has to decide?**

>
>

**What did you have to do by hand that the system should have done?**

>
>
>

**Would you trust this to run a real deal? If not, what would have to change first?**

>
>
>

---

## Overall

**The three things that worked best**

>
>
>

**The three things that got in your way most**

>
>
>

**What you want us to build or fix next**

>
>
>
