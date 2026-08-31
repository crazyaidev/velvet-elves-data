# Task Lists & Email — Testing Guide

**Prepared by:** Jan (sole developer)
**Date:** July 28, 2026
**For:** Audri and Jake
**Where to test:** the stage site (Jan will confirm it is ready before you start)

---

## Before you start

This guide covers the two things you asked to test: **the task list a deal
produces**, and **the emails that go with it**. It is written to be worked
through in order — each part builds on the one before.

You do not need to know anything technical. Every step is something you do on
screen, and every step says what you should expect to see. When what you see
does not match, that is exactly what we want to hear about.

**Three things to know first, because they explain most of what you will see:**

1. **Some tasks belong to the AI, and it sends their emails without asking.**
   These are the eight tasks Jake marked "Automated" in the task database.
   They do not sit in your list waiting — the AI sends the email and ticks the
   task off. You only see one if the AI got stuck.
2. **Everything else waits for you.** Ordinary tasks stay in your list, and any
   email the AI prepares for them lands in **AI Email Review** for you to read
   and send. Nothing is emailed to a client without a person pressing send.
3. **The AI sends from your own mailbox**, not from a Velvet Elves address. So
   nothing outbound works until you connect Gmail. That is Part 1.

### The eight tasks the AI handles itself

| Task | Who it emails | Needs the contract uploaded first? |
|---|---|---|
| Buyer Welcome | Buyer | No |
| Seller Welcome | Seller | No |
| Co-op Agent Welcome | The agent on the other side | No |
| Loan Officer Welcome | Loan officer | **Yes** |
| Order Title | Title company | **Yes** |
| Confirm Title Order | Title company | **Yes** |
| Pending Reminder | You | No |
| Review Documentation | Nobody — it checks signatures | It reads them |

The "needs the contract" column matters: the AI will not send an email that
promises the contract without the contract attached. If those tasks are waiting,
that is usually why, and it will say so.

### How to report what you find

For anything that looks wrong, please tell us:

- **Where you were** (page name is enough — "My Task Queue")
- **What you did** ("clicked Send & complete task")
- **What you expected** and **what happened instead**
- **The property address** on the deal, so we can find it
- A screenshot if it is quick

You do not need to diagnose it. "This felt wrong" is a useful report.

---

## Part 1 — Connect your mailbox

**Why first:** nothing outbound works until this is done.

1. Go to **Settings → Email & E-signature**.
2. Next to **Gmail**, click **Connect** and sign in with the Google account you
   want deal emails to come from.
3. Google will warn you that the app is not verified. That is expected — we are
   still in Google's review queue. Continue through the warning.
4. Back in Velvet Elves, Gmail should now show **Connected** with your address.
5. Click **Test connection**.

**Expect:** a line appears saying *"Connected as <your address>."* No email is
sent — this only checks the connection.

### The weekly reconnect (please expect this)

Until Google finishes verifying the app, **your connection will expire roughly
every week.** This is a Google restriction on unverified apps, not a bug.

When it expires you will see **"Expired — reconnect"** where "Connected" used to
be. Click **Connect** again and you are back in business. Anything the AI was
holding will go out on its own afterwards.

If you ever try to send and see a message about your mailbox connection having
expired, that is the same thing — reconnect and try again. **Please tell us if
you are ever signed out of Velvet Elves instead of seeing that message.**

**Worth reporting:** the connection expiring more than about once a week; "Test
connection" saying it is fine when sending then fails; being signed out of the
app instead of being told to reconnect.

---

## Part 2 — Upload a deal and watch the task list appear

1. Click **+ New Transaction** and run a deal through the wizard as you normally
   would. Use a real contract packet — the more complete it is, the more of the
   task list you will see.
2. When the wizard finishes, you land on the deal's workspace.
3. Open the **Tasks** tab.

**Expect:** a full task list, grouped by urgency, with dates already filled in
from the contract.

### What to look at

- **Are the tasks the right ones for this deal?** A cash deal should not be
  asking about the loan officer; a deal with no HOA should not ask for HOA docs.
- **Are the dates right?** They are calculated from the contract's acceptance
  and closing dates.
- **Is anything missing that you would always do on a deal like this?**
- **Is anything there that you would never do?**

### Two labels you will see

- **"Waiting on an earlier step"** instead of a date. This means the task cannot
  be scheduled yet because something it depends on has not been answered or
  finished. This is normal — but if a task sits like this and you think it
  should have a date, tell us.
- **"AI needs you"** in amber, with a sentence explaining the problem. That is
  one of the eight AI tasks that got stuck. The sentence tells you what to fix.

**Worth reporting:** wrong or missing tasks for the deal type; dates that do not
match the contract; two tasks that look identical (they should differ by the
"who it goes to" label next to the address).

---

## Part 3 — The welcome emails should send themselves

This is the headline behaviour. It happens **immediately when the deal is
created** — you do not have to do anything.

1. On the deal you just created, open the **Tasks** tab.
2. **Do not expect to see "Buyer Welcome" in the list.** Once the AI finishes
   one of its own tasks it takes it out of your way — that is the point of
   them. Scroll down to the collapsed **Handled by AI** group and open it.

**Expect:** *Buyer Welcome* and *Co-op Agent Welcome* are in there, already
completed, marked as done by the AI.

3. Now check your Gmail **Sent** folder. **This is the real proof** — the task
   list only tells you what the AI believes it did.

**Expect:** the welcome emails are there, sent from you, addressed to the buyer
and the other agent, with you copied in.

4. Read one of them properly.

**Expect:** it reads like something you would send. The property address, the
closing date and the names should all be correct, and it must **never** mention
that AI wrote it.

### If they have not sent

Open **Needs You** from the left menu. A stuck AI task appears there with the
reason. The two most common:

- *"No … email is on file for this deal"* — that party has no email address yet.
  Add it on the deal's **Contacts** tab, and the AI will pick the task back up.
- *"This email needs the purchase agreement attached"* — upload the contract to
  the deal, and it will send.

**Worth reporting:** wording you would not send to a client; the wrong person
receiving an email; an email that says a document is attached when it is not;
any message that mentions AI; a welcome email going out twice.

---

## Part 4 — Send a task email yourself

Most tasks are yours, and most of them are really "send this person an email".

1. Open **My Task Queue** from the left menu, or the **Tasks** tab on a deal.
2. Pick any open task and expand it.
3. Click **Email transaction party**.

**Expect:** a window opens that already knows who the email should go to — the
person the task is about, chosen for you. You will see:

- who it is going to, and who is copied
- a subject and a message, already written
- any documents that will be attached

4. Change the party in the dropdown if the wrong person is pre-selected.
5. Edit the subject or message however you like.
6. Click **Send & complete task**.

**Expect:** the email goes out from your mailbox, and **the task is marked
complete for you**. You should not have to tick it off separately.

7. Check your Sent folder to confirm it arrived as written, with your edits.

If you would rather handle it outside the system, **I'll handle it myself**
closes the window and leaves the task alone.

**Worth reporting:** the wrong person pre-selected; a message that does not fit
the task; edits not surviving into the sent email; the task not completing; an
attachment you did not expect.

---

## Part 5 — AI Email Review

This is where every email the AI prepares — but has not sent — waits for you.

1. Open **AI Email Review** from the left menu.
2. Click any draft to read it.

**Expect:** the full message, who it is going to, and — where it is a reply — the
original message above it.

3. On one you are happy with, click **Approve & send**.
4. On another, click **Edit**, change something, and send it.
5. On one you do not want, click **Discard**.

**Expect:** sent drafts leave the list and appear in your Gmail Sent folder.
Discarded ones leave the list without sending.

### About "Send all ready"

You will normally **not** see a "Send all ready" button. That is correct. It only
appears when there are drafts that have been **pre-approved**, and the only
setting that pre-approves anything is **Autopilot**. On **Manual** and
**Assisted** every email waits for your individual tap, and the page says so.

An Admin sets this under **Settings → AI & Automation**:

- **Manual** — the AI suggests; you apply everything.
- **Assisted** — routine work applies itself; emails still wait for you.
- **Autopilot** — drafts are pre-approved, so "Send all ready" sends them in one
  tap. Even here, nothing goes out without that tap.

**If you want to see this in action,** switching to Autopilot is not enough on
its own — it applies to emails prepared *from that point on*, and it does not
change drafts already sitting in your queue. On the same
**Settings → AI & Automation** page an Admin can then press **Draft due emails**,
which prepares the emails that are currently due. Those are the ones that will
show as ready.

**Please read the recipients before using "Send all ready".** It sends
everything in the list.

**Worth reporting:** a draft you cannot explain the existence of; the same email
appearing more than once; a draft with no deal attached; "Send all ready"
appearing when you are not on Autopilot.

---

## Part 6 — Replies coming back in

This is working on stage — Jan confirmed it end to end on July 28.

**Use a second mailbox for this — not the address you connected.** If a deal
emails the same account it sends from, the message lands back in your own inbox
and the AI treats it as a client reply, so you end up watching it answer itself.
It is harmless, but it clutters the queue and it is not a real test.

1. From the deal, send an email to a **different** address you can receive at.
2. Reply to it from that mailbox, as the client would.
3. Wait a couple of minutes, then open **AI Email Review**.

**Expect:** the reply appears as a new item, attached to the right deal, with a
suggested response already prepared. Open it — the original message is shown
above the draft so you can see what is being answered.

**Read the suggested reply carefully.** This is the AI answering a client
question on your behalf, so it is the highest-risk thing in the system. Check it
against the deal: are the dates right, and has it avoided promising anything you
would not promise?

**Worth reporting:** replies not arriving at all; a reply attached to the wrong
deal or to no deal; a suggested response that misreads the question, invents a
date, or commits you to something.

---

## Part 7 — The emails you receive yourself

Separate from deal email: Velvet Elves can send **you** a morning summary of what
is due.

1. Go to **Settings → Notifications**.
2. Find **Morning digest**. It is **off** unless you turn it on.
3. Turn it on and pick a time.

**Expect:** from the next morning, one email listing what is overdue and due
today across your deals. If you have nothing actionable, you correctly get
nothing.

**Worth reporting:** a digest arriving when you never switched it on; a digest
that is missing deals or lists things that are already done.

---

## Part 8 — A day in the life

Once the parts above work, please spend a session using it the way you actually
work, rather than following steps. That is where the real feedback comes from.

Suggested shape:

1. Start at **Needs You**. Does it show the things a person genuinely has to
   decide, and nothing else?
2. Work **My Task Queue** top to bottom. Can you finish a task without leaving
   the page?
3. Clear **AI Email Review**.
4. At the end, ask yourself: **would I trust this to run a real deal?** And:
   **what did I have to do by hand that the system should have done?**

Those two answers are the most valuable thing you can send us.

---

## Things you may notice that we already know about

Please do not spend time writing these up — they are on our list:

- A stuck AI task has no "try again" button. It clears itself once you fix the
  underlying cause (add the email address, upload the document).
- On a vendor's group of tasks you email **one task at a time**; there is no
  "email all of them at once" yet.
- Two tasks can share a name and differ only by who they go to (the small label
  next to the address tells you which is which).

The full list is in **todo_list.md** alongside this guide.

---

## Quick reference

| I want to… | Go to |
|---|---|
| Connect or fix my mailbox | Settings → Email & E-signature |
| See what needs a decision | Needs You |
| Work my tasks | My Task Queue |
| Read and send prepared emails | AI Email Review |
| See one deal's tasks | Open the deal → Tasks tab |
| Add a missing party email | Open the deal → Contacts tab |
| Change how much the AI does | Settings → AI & Automation |
| Turn the morning summary on | Settings → Notifications |
