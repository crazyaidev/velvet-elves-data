# Velvet Elves — Still Being Built (Not Yet Ready for Client Feedback)

**Last Updated:** July 31, 2026

This is the companion list to the testing guides. Those guides only cover features that
are **fully complete** and ready for your feedback. The items below are still being built,
are waiting on a decision, or are intentionally switched off — so we are **not** asking
for feedback on them yet. They are listed so you can see what is coming and so nobody
spends time testing something unfinished.

Every item below was re-checked against the live source code on **July 31, 2026**, when
`CORE_FEATURES_TESTING_GUIDE.md` was written.

- **Section A** — automation and email.
- **Section B** — everything else, carried forward and re-checked.
- **Section C** — what has moved **off** this list since the last version, so you know
  what is now fair game.

If any item below is more urgent for you than its current position suggests, tell us and
we will re-prioritise it.

---

## Section A — Automation & email

### A1. Automation does not yet run on a timer

**Where:** anywhere the AI is meant to act on its own over time.

**Current state:** the AI acts when something *triggers* it — creating a deal, uploading
documents to one, pressing a button. Those triggers work today and are covered in the
testing guide. What is **not** switched on is the hourly timer that would let the AI act
on a deal where nothing has happened recently. Settings → AI & Automation says so
honestly at the top of the page: *"Automation is not running — the scheduler has never
checked in."*

**What this means for testing:** you will see welcome emails send themselves when you
create a deal. You will **not** see the AI act overnight on an older deal. Please do not
report that as a bug.

**What is still needed:** Jan to switch on the scheduled run in stage. It is deliberately
being done by hand first — one manual run, counts read, mailboxes audited — because the
job sweeps every workspace and sends real email. The steps are in
`SCHEDULER_AND_STAGE_ENABLEMENT_RUNBOOK.md`.

---

### A2. A blocked AI task has no "Try again" button

**Where:** Needs You, and the Tasks tab on a deal.

**Current state:** when the AI cannot finish one of its own tasks it tells you why — a
missing email address, a missing contract. Once you fix the cause it picks the task back
up on its own the next time that deal is touched. What is missing is a button to say
"try it again now".

**What this means for testing:** after you fix the cause, the task may not clear
instantly. That is expected for now.

---

### A3. Emailing a whole group of vendor tasks at once

**Where:** My Task Queue → the **Vendor** grouping.

**Current state:** you can email **one task at a time** from a vendor's group, and that
email is sent from your mailbox and recorded on the deal. What does not exist is a single
email covering several outstanding tasks for the same vendor.

**Why it is not there:** the previous version of this button opened your computer's own
mail program. Nothing it sent was recorded against the deal, which defeats the point, so
we removed it rather than leave it misleading.

---

### A4. Two tasks can still share a name

**Where:** any task list.

**Current state:** a few tasks in the task database share a name and differ only in who
they are addressed to — for example two "Internal Thank You" tasks, one to your own client
and one to the co-op agent. They show a small label saying who each one goes to, so they
can be told apart.

**Open question for Jake:** would you rather we **rename** them outright — "Internal Thank
You — Your Client" and "Internal Thank You — Co-op Agent"? That is a change to the task
database itself, so we want your decision before making it.

---

### A5. "Filtered out" is named in the app but does not exist in it

**Where:** Email → Inbox, when you mark a message as not relevant.

**Current state:** the confirmation says the message *"moves to Filtered out"* and that you
can *"restore it there any time"*. There is no Filtered out screen. The view existed
briefly and was removed on request; the machinery behind it survives, so the message is
recoverable **by us** but not **by you**.

**What is still needed:** either bring the view back, or change the wording so it does not
promise a screen that is not there. This is a wording bug we already know about — please
do not spend time writing it up.

---

### A6. iCloud mailboxes

**Where:** Settings → Email & E-signature.

**Current state:** only **Gmail** and **Outlook** are offered. iCloud is intentionally
hidden because Apple does not offer a standard one-click sign-in and needs an
"app-specific password" flow we still want to review. It also has no equivalent of the
**Test connection** check the other two have.

---

## Section B — Everything else

### B1. Sharing page (internal staff) — placeholder

**Where:** the **Sharing** entry, `/sharing`.

**Current state:** still a "Coming Soon" placeholder. It does not yet let staff create or
manage share links from a dedicated page.

**Note:** sharing milestone links with sellers already works today **for FSBO customers**
through the "Share milestones" button in their own workspace. Only the separate internal
staff Sharing page is unfinished.

---

### B2. In-app password change — not built yet

**Where:** Settings → Profile.

**Current state:** you can edit your photo, name, phone, bio, email signature, and your
sign-in **email address**. The one piece still missing is changing your **password** from
inside the app.

**For now:** use the "Forgot password?" link on the sign-in page.

---

### B3. AI Coach — intentionally switched off

**Where:** the "Add the AI Real Estate Coach" block on the solo-agent dashboard, and the
locked **AI Coach** entry Team Leaders see in the sidebar.

**Current state:** deliberately off. AI Coach is planned as a future paid add-on, so it is
not part of this release. The promotional block is visible but its **Add AI Coach** and
**See how it works** buttons do nothing.

---

### B4. AI deal workspace — a few extras still on the way

**Where:** the deal workspace that opens when you click a single transaction.

**Current state:** the workspace itself is **complete and in this round's testing guide**
— the AI assistant, its proposals and approvals, the safe date moves, document analysis on
upload, and all seven tabs (Timeline, Compliance, Documents, Tasks, People, Activity,
Email). A few extras around it are still being built:

- **Voice input.** A microphone button is shown in the assistant's message box but is
  switched off ("coming soon"). Typing works fully today.
- **A built-in document viewer.** The assistant points you to the Documents tab to open a
  file; opening it inside the assistant window is still being built.
- **Re-filing an email onto the right deal.** The Email tab's Outbox and Inbox are
  complete, and the machinery to move a misfiled email exists — but there is no button for
  it yet.
- **Team-lead oversight, "always approve" rules, and merging documents.** Planned for a
  later stage. Today every AI action requires your explicit approval, one at a time, which
  is by design.

---

### B5. New Transaction wizard — address type-ahead is switched off

**Where:** New Transaction wizard, the Street Address field.

**Current state:** the field still suggests addresses you have used before, and AI parsing
fills the address from an uploaded contract. The **live address type-ahead** (Google-powered
"start typing and pick a real address") is **switched off** in every environment because
the map-service key is not configured.

**What is still needed:** add the address-service key and switch it back on.

> The wizard as a whole is not part of the current testing round — it has its own guide.

---

### B6. Belonging to more than one workspace — waiting on a billing decision

**Where:** the workspace switcher near the top of the sidebar, and the "guest" invite flow
(being invited into another brokerage with an email you already use).

**Current state:** this is now **on by default** in every environment, so the switcher
appears and guest invitations work. What is still outstanding is the **billing rule for
guest members** — who pays when someone from another brokerage is working in your
workspace. That is a pricing decision, not code. Until it is settled, a guest occupies no
seat in the host workspace.

**What is still needed:** Jake to confirm the guest-member billing rule.

---

### B7. Help Center content

**Where:** the Help Center link in the avatar menu and Settings → Help & Tour.

**Current state:** the Help Center is a separate website with its own authoring tools
behind the platform screens. The rewritten article set exists but has not been loaded into
the live database, so what you see may be thin or out of date.

**What is still needed:** load the article set, then re-check the links from inside the app.

---

## Section C — What has moved off this list

These were on the previous version of this list and are now **ready for your feedback**.
They are covered in `CORE_FEATURES_TESTING_GUIDE.md`.

| Was | Now |
|---|---|
| **Credit wallet & billing — switched off behind a flag** | **Live.** Billing is now a flat fee per deal, no seats and no subscription, with optional prepaid deals. It appears in Settings → Billing for Admins and owners. Covered in Part 16. |
| **Replies coming back in — unverified** | **Verified end to end on stage** on July 28. Covered in Part 9. |
| **Changing your sign-in email address** | **Done.** Settings → Profile. Only the password change is still missing (B2). |
| **Belonging to more than one workspace — flag off** | The feature is **on**; only the guest-billing rule is outstanding (B6). |

---

## How this list is kept honest

Every item was checked against the live source code on July 31, 2026 — not against an
earlier plan document. Where a plan and the code disagreed, the code won and this list
follows the code. As each item is finished it moves out of this list and into a testing
guide with step-by-step instructions.
