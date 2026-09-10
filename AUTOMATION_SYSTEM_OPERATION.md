# How the automation system operates

**Date:** 10 September 2026  
**Audience:** reviewers checking the live product  
**Source of truth:** the current frontend and backend. Other files in this folder are background only and may be out of date.

This document explains what the product actually does today. It is organized around the three automation postures — Manual, Assisted, and Autopilot — then lists the settings a person must verify, then the features that sit on top of those postures.

---

## 1. The three postures

Posture answers one question: **how much may Velvet Elves do on its own on a file?**

It is a send-and-routine-work control. It is **not** Trusted dates (when a contract date becomes official). Turning Autopilot on does **not** turn Trusted on.

| Posture | Promise on the card | Routine file work | Named emails (welcome, title order, inspection-deadline reminder) | Everything else (replies, most task mail) | Waives, legal, money |
|---|---|---|---|---|---|
| **Manual** | AI suggests. You click to apply anything. | You click | Never auto. No draft from this path. | You ask | You |
| **Assisted** (Recommended) | Routine work runs. Named emails are drafted — you tap Send. | Runs | Drafted. You tap Send. | Prepared. You tap Send. | You |
| **Autopilot** | Authorized emails send when confidence is high enough. No tap. | Runs | Sends without a tap when confidence is high enough and every other gate is clear | Ready, or Needs You if confidence is low. You still send those. | You |

Workspace default for new files starts as **Manual** until someone with permission picks a card and saves **Save posture**. Any single deal can differ from that default.

Aime chat (**Ask AI**) does not send mail on any posture. The transaction agent is not allowed to send email as an action. Sending is a dedicated mail path (playbook executor, tap-send, or a person composing).

---

## 2. What is always true

These hold at every posture. No setting on AI & Automation turns them off. They are listed on the page as **Always true**.

- Named welcome, title-order, and inspection-deadline emails may send on Autopilot when confidence is high enough. On Assisted they are drafted for one tap. Every other email is drafted for you to send.
- Unclear or conflicting contract dates never go live on their own.
- Waives, legal calls, and packet release stay human.
- Wire and funds mail is never drafted.

Also true in the running code, even though they are not on that list:

- Named letters come from the **deal owner’s connected mailbox**, not from hello@.
- Named letters use **library templates**. They do not invent a new letter each time, and they do not disclose AI.
- A body that hits a mandatory-review topic (wire, banking, legal interpretation, terminate language, and the rest of that list) does not send on its own.
- Inactive deals are not mailed. A named task overdue more than **30 days** waits for a person instead of sending.
- Inspection **negotiation** (repair language, Inspection Negotiated) never sends on its own. The Overnight switch only covers the inspection-response **deadline reminder to the agent**.

---

## 3. Prerequisites — what to verify so automation works

If named letters do not send, or Assisted drafts never appear, check these in order. Each item names the exact page.

### 3.1 Posture is not Manual on this file

The deal uses its own chip if one is set; otherwise it uses the workspace default.

| Who | Where | Path |
|---|---|---|
| Admin | Settings → AI & Automation → **How it runs** → Automation posture | `/admin/confidence` |
| Team Lead | Settings → **My automation** (same posture cards) | `/settings/my-automation` |
| Agent / Transaction Coordinator | Settings → **My automation** (workspace default is read-only after a second staff member is hired) | `/settings/my-automation` |
| Staff on the deal | Deal workspace header chip → Manual / Assisted / Autopilot, or **Use workspace default** | `/transactions/{deal-id}` |

After a second internal staff user, only **Admin** or **Team Lead** can save the workspace default. Agent and TC still change a single file from the header chip.

**Manual on this deal** is a send kill-switch. The Automated welcome (or title) task stays open with: *This deal is on Manual, so the AI will not send this email or complete this task on its own.* There is no ready draft from that path. Switch the deal (or the workspace) off Manual, or complete the task yourself from **Tasks**.

### 3.2 Named emails are Allowed

If this is Paused, Autopilot will not send those letters, and Assisted will not draft them either. The task waits on Needs You until an Admin allows named emails.

| Control | Page | Path |
|---|---|---|
| **Named emails** → Allowed / Paused | Settings → AI & Automation → How it runs → **Overnight** | `/admin/confidence` |

The Allowed / Paused control is **Admin-only**. It is not on My automation. It is not every email on the file — welcome and title-order (and other named library letters). Inspection-deadline reminders have a second switch on the same card; they still also need this one Allowed before they send or draft.

New production offices often start with this **Paused**. Saving **Assisted** or **Autopilot** (Admin, Team Lead, or a solo Agent/TC) turns hourly automation On, and turns Named emails Allowed only if a healthy mailbox is already connected. After that, only an Admin can Pause or Allow them from Overnight.

### 3.3 Hourly automation is On (if you are waiting for the clock)

| Control | Page | Path |
|---|---|---|
| **Hourly automation** → On / Off | Settings → AI & Automation → How it runs → **Overnight** | `/admin/confidence` |

When Off, this workspace is skipped for the draft sweep and the named-letter executor. Morning digests, unreviewed-draft reminders, and Gmail watch renewal still run. Named letters can still run at deal create, after a parse, after a contact email is added, after mailbox reconnect, or when an Admin clicks **Run AI tasks** or **Try now**.

The health chip at the top of AI & Automation should read **Automation active**, with a recent last run. **Automation is not running** or **Automation has stopped** means the scheduler has never checked in or has gone quiet.

### 3.4 The deal owner has a healthy mailbox

Named letters send as the **deal owner**, not as whoever is looking at the file.

| Check | Page | Path |
|---|---|---|
| Connect Gmail or Outlook | Settings → **Email & E-signature** | `/settings/connections` |
| **Test connection** on each connected mailbox | same page | `/settings/connections` |
| Overnight mailbox census | Settings → AI & Automation → How it runs → Overnight | `/admin/confidence` |

**Test connection** checks saved credentials. It does not send mail. It tests **that** mailbox. Send tries Gmail, then Outlook. A lapsed Gmail grant is skipped so a healthy Outlook mailbox can still send.

If Gmail shows expired and it is the only mailbox, reconnect it. Google unverified-app grants expire on the order of a week in test environments. A failed send surfaces as **Reconnect mailbox** or **Connect mailbox** on Needs You.

### 3.5 The deal is Active, and the task is due and not stale

- Status must be **Active**. Paused, Completed, Closed, Terminated, Incomplete are not mailed.
- The Automated task must be due (welcome tasks are usually due at create).
- If the due date is more than **30 days** past, the task waits as Needs You (*stale*) instead of sending.

Open the file: `/transactions/{deal-id}`. Tasks: `/transactions/{deal-id}?tab=tasks`.

### 3.6 The recipient has an email on Contacts

| Letter | Who must have an email | Extra document needed |
|---|---|---|
| Buyer Welcome | Each captured buyer | None (packet attaches if present) |
| Seller Welcome | Each captured seller | None (packet attaches if present) |
| Co-op Agent Welcome | The agent on the other side | None |
| Loan Officer Welcome | The loan officer | Purchase agreement on the file |
| Order Title / Confirm Title Order | Title company or title rep | Purchase agreement |
| Pending Reminder | — (goes to the account holder) | None |
| Inspection response reminder | — (goes to the account holder) | Overnight **Inspection deadline reminder** = Allowed |
| Order Home Warranty | — (account holder) | Not mailed to a warranty company |

Add the address on **Contacts**: `/transactions/{deal-id}?tab=contacts`. Adding it retries that deal without waiting for the next hour.

Co-op is side-aware: buyer-side file → listing agent; seller-side file → buyer’s agent. On a dual (both-sides) file the Co-op Agent Welcome task is not generated, so the same office is not emailed as if it were the other side.

No email → Needs You *No … email is on file* (**Add contact**).

### 3.7 Inspection deadline reminder is Allowed (that letter only)

| Control | Page | Path |
|---|---|---|
| **Inspection deadline reminder** → Allowed / Paused | Overnight on AI & Automation | `/admin/confidence` |

This is only the reminder to **you** that the inspection-response deadline is coming. It is not other reminder tasks, and it is not Inspection Negotiated. Production workspaces start this Paused until it is turned on. To send or draft that reminder, **Named emails** must also be Allowed.

### 3.8 Aime signature is complete if automatic letters sign as Aime

| Control | Page | Path |
|---|---|---|
| **Aime signature** → Aime / Agent | Overnight on AI & Automation | `/admin/confidence` |
| Profile used for the signature | Settings → Account | `/settings/account` |

When the switch is **Aime**, automatic named emails sign as Aime, Assistant to the agent. Incomplete profile data blocks send (**Complete your profile**). Reviewed drafts you tap Send on stay in the agent’s voice.

### 3.9 Assisted still needs a tap

On Assisted, a correct setup produces a **ready** draft. It does not leave the mailbox until someone taps Send.

| Where to tap | Path |
|---|---|
| Sidebar → **Needs You** → Ready to send → **Send all ready**, or **Send** on the row | `/needs-you` |
| Intelligence → **Email** → **Approve & send**, **Send edited email** / **Send edited reply**, or **Send all ready** | `/ai-emails` |
| Deal workspace → **Email** tab (Send all ready for that file) | `/transactions/{deal-id}?tab=email` |

Those clicks are not on the deal **Inbox** of incoming mail. After Send, the linked Automated task completes (the welcome no longer sits in Needs You as “tap to send”).

### 3.10 Quick “will this Autopilot welcome send?” list

All of these must be true:

1. Workspace or this deal is **Autopilot** (not Manual, not Assisted).
2. **Named emails** = Allowed.
3. Deal **Active**; welcome task due; not > 30 days stale.
4. Deal owner mailbox **Test connection** healthy (or Outlook is healthy if Gmail is expired).
5. Party email on **Contacts** (and purchase agreement for LO / title).
6. Letter is not signature-incomplete or mandatory-review. Inspection-deadline reminder also needs its own Overnight switch Allowed.

If any item fails, the task shows on **Needs You** with a sentence and a button that opens the fix.

---

## 4. Where the controls live (page paths)

### Workspace — Admin

**Settings** (`/settings`) → card **AI & Automation** → `/admin/confidence`.

Page title: **AI & Automation**. Left nav:

| Section | URL | What is on it |
|---|---|---|
| How it runs (default) | `/admin/confidence` | Posture cards, Contract dates, Overnight, Always true |
| Fine-tune → Email replies | `/admin/confidence?section=email` | Voice, Ready-to-send threshold, reminder hours, writing style |
| Fine-tune → Automation rules | `/admin/confidence?section=rules` | Always / Ask me per low-risk action |
| Fine-tune → Confidence gates | `/admin/confidence?section=confidence` | Auto-apply, review floor, recommendation floor |

Run controls (**Preview next run**, **Draft due emails**, **Run AI tasks**, **Send me my digest**) live only on Overnight. Fine-tune tabs are not a send console.

### Workspace — Agent, TC, Team Lead

**Settings** → **My automation** → `/settings/my-automation`.

Posture cards only. Overnight switches, Preview, and Run stay on the Admin AI & Automation page.

### Deal

Open any file: `/transactions/{deal-id}`.

The header chip is the one deal-level control. Menu:

- **How much runs on its own:** Manual / Assisted / Autopilot
- **Use workspace default** (only if this deal is pinned)
- **Trusted dates:** On for this deal / Off for this deal / **Follow the workspace**

Deal tabs used by automation recovery:

| Tab | Path |
|---|---|
| Overview | `/transactions/{deal-id}` or `?tab=overview` |
| Timeline | `?tab=timeline` |
| Tasks | `?tab=tasks` (optional `&task={task-id}`) |
| Documents | `?tab=documents` |
| Contacts | `?tab=contacts` |
| Email | `?tab=email` |

### First-run

On **Create account**, the owner picks How should Aime start? Default is Manual. Named emails will not send until a mailbox is connected.

Onboarding for a tenant owner also includes posture, then Gmail/Outlook, then e-signature: the wizard at first login.

### Everyday queues

| Product name | Sidebar | Path |
|---|---|---|
| Needs You | Workflow → Needs You | `/needs-you` |
| My Task Queue | Workflow → My Task Queue (Team Lead: **Team task queue**) | `/tasks/queue` |
| Intelligence → Email | Intelligence → Email | `/ai-emails` |
| Intelligence → AI Suggestions | Intelligence → AI Suggestions | `/ai-suggestions` |
| Vendor Proposals | Intelligence → Vendor Proposals | `/vendor-proposals` |
| Email & E-signature | Settings | `/settings/connections` |
| Notifications (morning digest) | Settings | `/settings/notifications` |
| Account (signature / profile) | Settings | `/settings/account` |

Filter Needs You to one file: `/needs-you?tx={deal-id}`.

---

## 5. How named letters actually run

Named letters are **Automated** tasks in the playbook (Buyer Welcome, Seller Welcome, and the rest in §6). A separate executor owns them. The ordinary auto-draft sweep **skips** Automated tasks so the same letter is not drafted twice.

### When it tries

- Right after tasks are generated for a new file
- After a document finishes parsing
- After someone adds or edits a party email
- After documents/signatures that were the blocker are supplied
- After the deal owner reconnects a mailbox (whole workspace retry)
- On the **hourly** tick, if Hourly automation is On
- When an Admin clicks **Run AI tasks (sends deal email)** on Overnight
- When an Admin clicks **Try now (this deal only)** on Needs You

Manual is checked **before compose**. Assisted composes a ready draft and parks it (`posture_tap_to_send`). The hourly tick does **not** write a second draft while it stays Assisted. Switching that deal to Autopilot lets the next pass send.

Autopilot sends through the deal owner’s mailbox, then completes the task. Completed named work leaves the open task list and sits under **Handled by AI**.

### Hard stops (any posture)

These surface on Needs You instead of sending:

| Reason you see | Typical fix | Opens |
|---|---|---|
| No … email is on file | Add the address | Contacts |
| Missing required document | Upload (purchase agreement for LO / title) | Documents |
| Unsigned documents | Review signatures | Documents |
| Connect / Reconnect mailbox | Connect or Test connection | `/settings/connections` |
| This deal is on Manual | Switch the chip off Manual | Overview |
| Named-email send is off | Named emails → Allowed (Admin) | `/admin/confidence` |
| Inspection reminders paused | Inspection deadline reminder → Allowed (Admin) | same Overnight card |
| Complete your profile | Finish Aime / agent signature fields | `/settings/account` |
| Mandatory review language | A person sends from Email review | Intelligence → Email |
| Overdue too long | Change the due date | Tasks |
| Give this back to the AI | After an execution error, or complete it yourself | Needs You / Tasks |

### Mailbox order

Send uses Gmail, then Outlook. An expired Gmail grant is skipped so Outlook can still send. **Test connection** on Email & E-signature still tests the mailbox you click, including a dead Gmail, so the page can tell you that grant is expired.

---

## 6. Named playbook features

These are the Automated-task letters and checks implemented today.

### Welcome letters

Four letters. From the deal owner. First person. No AI disclosure.

| Task name | To | Packet | Purchase agreement required? |
|---|---|---|---|
| Buyer Welcome | Buyers with email | Attaches if on file | No |
| Seller Welcome | Sellers with email | Attaches if on file | No |
| Co-op Agent Welcome | Other-side agent | Attaches if on file | No |
| Loan Officer Welcome | Loan officer | Lender package | Yes |

Subjects follow the library (address filled from the file). One letter per task: if it already left the mailbox, the task completes as already done.

### Title

| Task name | To | Required |
|---|---|---|
| Order Title | Title company or title rep | Purchase agreement |
| Confirm Title Order | Same | Purchase agreement |

Same Named emails switch as welcomes. Addenda/amendments are withheld from the title package.

### Reminders that may send (narrow)

| Task name | To | Extra switch |
|---|---|---|
| Pending Reminder | Account holder (MLS pending reminder) | Named emails Allowed. Autopilot may send; Assisted drafts for a tap. |
| Inspection Response Reminder | Account holder | **Inspection deadline reminder** Allowed |

Inspection Response Reminder copy is locked. Repair / negotiation language still trips mandatory review.

### Draft-only / not mail

| Task name | What it does |
|---|---|
| Order Home Warranty | Does not email a warranty company. The executor leaves the Automated task for a person (Needs You). It is not a named letter the AI sends on its own. |
| Review Documentation | Not a welcome letter. Checks purchase agreement / counter / addendum / amendment for signatures. Missing docs or unsigned paperwork go to Needs You; a signature-request draft may be prepared in Intelligence → Email for you to edit. Ambiguous signatures are not treated as a problem. When the file is clean, Assisted and Autopilot complete the task. Manual does not complete it on its own. |

---

## 7. Overnight and other automation (not only named letters)

Overnight on `/admin/confidence` is the Admin health card: switches, last run, and Preview / Draft / Run / Digest. The hourly jobs themselves are listed next. Digest opt-in lives on Notifications. Dual HOA/utility letters are playbook behavior, not a switch on that card.

### Hourly tick (platform)

About once an hour the scheduler:

1. Reminds owners about AI drafts left untouched (escalation hours from Fine-tune → Email replies) — not gated by Hourly automation
2. Sends morning digests to people who opted in — not gated by Hourly automation
3. If **Hourly automation** is On for the workspace: drafts due **non-Automated** task emails (auto-draft sweep)
4. If **Hourly automation** is On: runs the named-letter executor
5. Renews Gmail inbox watches so idle mailboxes do not go deaf after about seven days — not gated by Hourly automation

**Preview next run** — dry run. Sends nothing. Shows how many Automated emails would send.  
**Draft due emails** — runs the sweep only. Drafts land in Intelligence → Email. Sends nothing.  
**Run AI tasks (sends deal email)** — real named letters to real people. Confirms first.  
**Send me my digest** — the caller’s digest only, if Settings → Notifications has morning digest On.

### Auto-draft sweep

For Assisted and Autopilot deals, many ordinary tasks with a known party target get `auto_draft_email`. When the task is due, the sweep composes a draft for review. Manual deals are skipped even if an old flag remains.

These drafts do **not** send on their own. They wait in Intelligence → Email / Needs You for a tap. They are not the named welcome path.

### Dual HOA / utility letters

Some playbook tasks are one row but two letters (thank-you to whoever sent the packet, and delivery to the represented side). The sweep files two drafts, or two Needs You reasons. On Autopilot a dual-send draft may be marked **Ready** when the body is not mandatory-review and attachments match the prose. Ready still needs **Send** or **Send all ready**.

### Morning digest

Off until the user turns it on.

Settings → Notifications → **Morning digest** (`/settings/notifications`): Daily email On, send time, timezone. Sends only when there is something due.

### Gmail watch renewal

The hourly tick re-registers Gmail `users.watch`. Without it, an idle connected Gmail stops receiving inbound mail after about seven days even though send might still work.

---

## 8. Needs You

Sidebar → **Needs You** → `/needs-you`.

This is the residual queue: everything automation could not finish safely. Five kinds:

| Kind on the page | Meaning |
|---|---|
| Ready to send | Assisted (or ready) drafts. Tap **Send**. |
| AI proposal | Low-risk agent actions waiting for **Approve** |
| Draft to review | Drafts that are not yet ready — **Review** opens Intelligence → Email |
| Decision | Coverage / choose an option |
| AI task blocked | Named task waiting on a contact, document, mailbox, posture, and so on |

Batch actions (with confirm):

- **Send all ready**
- **Approve all safe** (proposals that are allowed to batch)

Per deal / per row:

- **Send** / **Approve**
- **Try now (this deal only)** — Admin only. Runs the executor on this file now
- **Give this back to the AI** — clear a terminal error so the executor may retry (does not send by itself)
- On a **Verify deadline** row: **Confirm**, **Keep current**, or **Edit** (opens Timeline)
- Recovery buttons: Add contact, Upload document, Reconnect mailbox, Switch this deal off Manual, Open automation, Complete your profile

Needs You copy for a paused named-email switch tells staff an Admin can turn it on from AI & Automation. Non-Admin **Open automation** opens `/settings/my-automation`, which cannot flip that switch.

---

## 9. Intelligence → Email and Suggestions

### Email — `/ai-emails`

One surface, two streams:

- **Incoming mail** on matched deals, with a draft reply when the engine wrote one
- **Outgoing drafts** from named letters, the auto-draft sweep, and replies

Tabs: Inbox, Outbox, Sent, plus Filtered.

On this page, a person still sends: **Approve & send**, **Send edited reply**, **Send all ready** (ready drafts only, behind a confirm that names the recipient count). Autopilot named letters that already sent do not wait here; they appear in Sent.

This is not the deal’s incoming Inbox tab. Overnight says: open Intelligence → Email only to confirm drafts.

### Suggestions — `/ai-suggestions`

Page title **AI Suggestions**. Deterministic cards from live file data (missing email, overdue task, and similar). Accepting a **Send Email** card still goes through the guarded send path after a person clicks. Coaching / AI Coach is off.

### Deal Email tab — `/transactions/{deal-id}?tab=email`

Deal-scoped mail and **Send all ready** for that file.

### Vendor proposals — `/vendor-proposals`

Inbound vendor scheduling proposals. Accept / clarify / reject. Not posture-driven named mail.

---

## 10. Contract dates (Trusted) — separate from send

**Settings → AI & Automation → How it runs → Contract dates** (`/admin/confidence`). Workspace default is on that Admin page. Staff still set Trusted on or off for one file from the deal header chip.

| Choice | Promise |
|---|---|
| **You confirm** (Recommended) | Aime prepares the date. You click before it is official. |
| **Trusted** | Clear contract dates may go live. Unclear or conflicting dates still wait. |

Save with **Save dates**. This does not send email. Autopilot does not turn this on.

On the deal header, Trusted dates can be On / Off / Follow the workspace, independently of Manual / Assisted / Autopilot.

When a later signed amendment disagrees with dates already on the file, Aime never overwrites in the dark. She prepares “the file used to say X; this document says Y.” That waits on Needs You as a **Verify deadline** item (**Confirm** / **Keep current** / **Edit**) and on Timeline (`/transactions/{deal-id}?tab=timeline`) unless Trusted, the language is explicit and complete, and there is no conflict. Fuzzy always waits.

---

## 11. Fine-tune

Admin only: `/admin/confidence?section=…`

### Email replies — `?section=email`

How AI drafts **replies**. A person still approves every send on this queue. Named Autopilot letters are a different path.

- **Voice** — tone of replies
- **Mark drafts ready to send at** — overnight drafts get a Ready label at this confidence. Ready on this queue never mails anyone. Named emails on Autopilot may still send without a tap.
- **Remind me about unreviewed drafts after** — 24–48 hours, then the draft returns to its owner
- **Writing style** — the agent’s sample writing, used when drafting

### Automation rules — `?section=rules`

Let the transaction agent apply specific low-risk actions without asking. Saving **Manual** as the workspace posture turns these off; **Assisted** or **Autopilot** turns the eligible set on. Each row can still be **Always** or **Ask me**.

May be set to Always (code-enforced list):

- Add a task, Add a deadline, Update a task, Change a task’s status, Toggle a task’s auto-email
- Draft an email, Draft a document request
- Re-label a document, Rename a document
- Add a contact, Update a contact

**Never automatic** (cannot be enabled): waive / un-waive a checklist item, adopt the AI’s document type, move a date (cascade), attach or detach requirement documents, resolve a mismatch, plus forbidden actions (send email, auto-send email, legal determination, release packet, disbursement exception, delete/merge documents, schedule send).

Every auto-applied action still previews, can be undone, and is logged.

On **Manual**, the deal-level chip also blocks auto-apply on that file even if tenant rules are on.

### Confidence gates — `?section=confidence`

Workspace floors for how sure the AI must be before it acts on its own.

- **Apply AI suggestions automatically at**
- **Always ask a person below**
- **Show AI recommendations at**
- **Workspace minimum** — fixed by plan; teams may tighten, never loosen below this floor

Help text on auto-apply: task suggestions this confident are applied without asking. Email and text drafts are never sent automatically **by this gate**. Named Autopilot letters still use their own send rule (Autopilot + Named emails Allowed + the hard stops in §5).

---

## 12. Ask AI

**Ask AI** is the floating button (also labelled Ask Aime) and the deal assistant pane. It answers from the file. It does not send named letters. Suggested chips open a follow-up question or a page; they are not a send-email tool. The transaction agent cannot take a send-email action.

FSBO **Ask Aime** explains that seller’s file from confirmed context. It does not send mail and must not claim to have sent or changed anything.

---

## 13. What this system is not

**Account welcome from hello@.** When a person first gets a Velvet Elves login, a platform email may go out from hello@. That path does not use posture, Named emails, or the deal owner’s mailbox. Do not confuse it with Buyer/Seller/Co-op/LO Welcome.

**Inspection Negotiated / repair credits / legal advice.** Always a person.

**Listing or buyer search in TME, silent negotiation, training on private chats.** Not implemented as automation features.

---

## 14. New office behavior

A brand-new production workspace starts:

- Posture **Manual**
- Hourly automation **Off**
- Named emails **Paused**

until an Admin or Team Lead (or a solo Agent/TC before anyone else is hired) saves **Assisted** or **Autopilot**. Saving that posture turns Hourly automation On. Named emails become Allowed only if a healthy mailbox is already connected; otherwise connect the mailbox, then set Named emails to Allowed (or save Assisted/Autopilot again after the mailbox is healthy).

Existing workspaces that never stored those flags keep hourly jobs and named-letter send **on**, so older offices are not frozen by the new-office cage.

---

## 15. Reviewer walkthrough (shortest path)

1. Sign in as Admin.
2. Open `/admin/confidence`. Confirm the health chip, posture card, Contract dates, and Overnight switches.
3. Open `/settings/connections` as the **deal owner**. **Test connection**.
4. Open the file `/transactions/{deal-id}`. Confirm Active. Confirm the header chip. Open Contacts and Tasks.
5. Open `/needs-you?tx={deal-id}`. Read the blocker sentence. Use the recovery button.
6. Open `/ai-emails` only to confirm drafts or tap Send on Assisted.
7. To force a pass without waiting (Admin): Overnight → **Preview next run**, then either **Draft due emails** (no send) or **Run AI tasks** (real send), or Needs You → **Try now**.
