# Staging Test Run — Task Lists & Email

**Prepared by:** Jan (sole developer)
**Date:** July 28, 2026
**Environment:** stage — `app.stage.velvetelves.com` / `api.stage.velvetelves.com`
**Account:** `crazyaidev20500519@gmail.com` (Admin, platform admin)
**Method:** worked `TASK_LIST_AND_EMAIL_TESTING_GUIDE.md` end to end in a real
Chrome browser, exactly as written

---

## Result

**All eight parts of the guide pass on stage.** Zero failed API calls and zero
browser console errors across every screen touched. Four emails were sent and
delivered through the real Gmail connection, all of them to a mailbox we control.

The run also corrected **two mistakes in the guide** and **cleared one open
question** — details in §3 and §4.

| Guide part | Result |
|---|---|
| 1 — Connect your mailbox | **Pass** |
| 2 — Upload a deal, see the task list | **Pass** (guide wording corrected) |
| 3 — Welcome emails send themselves | **Pass** (guide wording corrected) |
| 4 — Send a task email yourself | **Pass** |
| 5 — AI Email Review | **Pass** |
| 6 — Replies coming back in | **Pass** — previously unverified |
| 7 — The morning digest | **Pass** |
| 8 — A day in the life | Not applicable to a scripted run |

---

## 1. What was tested, and how the blast radius was controlled

Stage carries other tenants' deals with real-looking party addresses. Every send
in this run was confined to one mailbox by construction:

- A dedicated test deal, **"12 Guide Test Way"**, was created with **all five
  parties addressed to `crazyaidev20500519@gmail.com`** — the same mailbox the
  account sends from.
- **No tenant-wide job was run.** No scheduler tick, and no "Run AI tasks".
  Task generation triggers the AI for *that deal only*, which is what makes this
  safe.
- The three pre-existing deals in the tenant were not touched.

**Four emails were sent, all to that one mailbox:**

| # | Subject | How it was sent |
|---|---|---|
| 1 | Welcome — we're under way on 12 Guide Test Way | AI, on its own |
| 2 | Working together on 12 Guide Test Way | AI, on its own |
| 3 | Inspection Scheduled — 12 Guide Test Way | Me, via "Send & complete task" |
| 4 | Re: Inspection Scheduled — 12 Guide Test Way | Me, via "Approve & send" |

Nothing reached a third party.

---

## 2. Part-by-part detail

### Part 1 — Connect your mailbox ✅

Gmail already connected and reporting **healthy**. **Test connection** returned
*"Connected as crazyaidev20500519@gmail.com."* inline, without sending anything.

### Part 2 — The task list ✅

The deal generated **28 tasks** with dates derived from the contract. Blocked AI
tasks carried the amber **"AI needs you"** badge and a plain-English reason, e.g.
*"This email needs the purchase agreement attached, but it isn't in the deal's
documents yet. Upload it and the AI will send this for you."*

Only **one** task was left undated (*Insurance Reminder*), correctly — its
timing depends on a wizard field this deal did not answer.

### Part 3 — Welcome emails send themselves ✅

Seconds after the deal was created, with no human action:

```
Buyer Welcome        Completed   sent -> crazyaidev20500519@gmail.com
Co-op Agent Welcome  Completed   sent -> crazyaidev20500519@gmail.com
Loan Officer Welcome Pending     needs the purchase agreement
Order Title          Pending     needs the purchase agreement
Review Documentation Pending     no documents to review yet
```

Both sends are recorded with real Gmail message ids (`19fab12babd8e391`,
`19fab12c45ae27f6`). The three that waited did so for correct reasons — this
deal deliberately had no documents uploaded.

### Part 4 — Send a task email yourself ✅

Opened *Inspection Scheduled* → **Email transaction party**. The recipient was
pre-filled from the task's target. Pressed **Send & complete task**:

- the email sent through Gmail
- the task flipped to **Completed** with the note *"Sent to
  crazyaidev20500519@gmail.com — confirmed by you"*
- **the session stayed signed in**

### Part 5 — AI Email Review ✅

- Reply drafts listed, each showing the original message above the draft.
- **Approve & send** sent one; it left the queue and appears in the log as sent.
- **"Send all ready" was correctly absent** — this tenant runs on *Assisted*,
  and the page explains why rather than leaving a gap.
- Session stayed signed in throughout.

### Part 6 — Replies coming back in ✅ (this is the notable one)

**Previously unverified — now confirmed working end to end on stage.** The
emails the deal sent were received back, the Gmail watch fired, the webhook
processed them, they were **matched to the correct deal**, and the AI prepared
contextual replies that correctly cited the deal's September 30 closing date.

### Part 7 — The morning digest ✅

Present under Settings → Notifications, and **off** until switched on
(`{"enabled": false}` confirmed directly). That is the intended default, and the
fix made earlier today means the admin "run" buttons now honour it.

---

## 3. Two corrections the run forced into the guide

Both were my errors, caught by following my own instructions literally.

**Part 3 told Audri to look for "Buyer Welcome" in the task list.** She would not
have found it. When the AI finishes one of its own tasks it *removes it from the
list* — that is the whole point of them. The task list showed **26 open** of 28;
the two completed welcomes sit in a collapsed **"Handled by AI"** group.
Following the guide as written, she would have concluded the emails never sent.
Now the guide says to open that group, and points at the **Sent folder** as the
real proof.

**Part 6 was hedged as "check with Jan first."** That hedge is now removed, since
the round trip demonstrably works. The guide instead tells her to read the
suggested reply critically — it is the AI answering a client on her behalf, and
therefore the highest-risk thing in the product.

I also added a testing note I only learned by hitting it: **use a second mailbox
for Part 6.** If a deal emails the same account it sends from, the message
returns to your own inbox and the AI answers itself. Harmless, but it clutters
the queue and proves nothing.

---

## 4. Observations worth knowing (not defects)

**Staging is already running today's fixes.** I checked before testing and both
markers are present — `scheduler_state` on the automation status, and the
`/integrations/{provider}/test` probe. So this run exercised the fixed code, not
the code Audri hit last week.

**The scheduler still is not running on stage.** `automation/status` reports
`scheduler_healthy: false` with the last tick on **July 23**. Everything in the
guide works because it is trigger-driven — creating a deal, uploading documents,
pressing a button. Nothing time-based will fire until the runbook steps are done.
This is expected and is already item **A1** on the todo list.

**A self-addressed deal makes the AI reply to itself.** An artifact of the test
setup, not a defect: the Gmail watch only sees the INBOX, and Gmail only inboxes
mail addressed *to* you. A normal deal emails a third party, so this will not
occur. Flagged in the guide anyway, because a tester would otherwise report it.

---

## 5. What I left behind on stage

The test deal **"12 Guide Test Way"** (`da681bf7…`) is still there, with its 28
tasks, 4 sent emails and 2 remaining reply drafts. I left it deliberately — it is
a worked example Audri can look at before creating her own. **Say the word and I
will delete it.**

I did **not** run the backlog purge or the scheduler steps on stage; those are
the operational items in `SCHEDULER_AND_STAGE_ENABLEMENT_RUNBOOK.md` and they
need the mail-integration audit first.

---

## 6. Recommendation

**The guide is accurate and stage is ready for Audri to work through Parts 1-7
today.** Part 8 — using it the way she actually works — is where the useful
feedback will come from, and nothing blocks that.

The one thing to tell her up front: **the AI will not act on its own overnight
yet.** Welcome emails fire when she uploads a deal, and everything else responds
to what she does. If she is expecting to log in tomorrow and find that the system
worked a deal by itself, she will report that as a bug, and it is simply not
switched on.
