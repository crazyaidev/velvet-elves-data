# Velvet Elves — Still Being Built (Not Yet Ready for Client Feedback)

**Last Updated:** July 28, 2026

This is the companion list to the testing guides. Those guides only cover features that
are **fully complete** and ready for your feedback. The items below are still being built,
are waiting on a decision, or are intentionally switched off — so we are **not** asking
for feedback on them yet. They are listed so you can see what is coming and so nobody
spends time testing something unfinished.

**Section A** covers the current round (task lists and email). **Section B** carries over
the items from the earlier round, re-checked against the code today.

If any item below is more urgent for you than its current position suggests, tell us and
we will re-prioritise it.

---

## Section A — Task lists & email (current round)

## A1. Automated emails do not yet fire on a schedule

**Where:** anywhere the AI is meant to act on its own over time.

**Current state:** The AI sends an Automated task's email when something *triggers* it —
creating a deal, or uploading documents to one. Those triggers work today and are covered
in the testing guide. What is **not** switched on yet is the hourly timer that would make
the AI act on a deal where nothing has happened recently.

**What this means for testing:** you will see welcome emails send themselves when you
upload a deal. You will **not** see the AI act overnight on an older deal. Please do not
report that as a bug yet.

**What is still needed:** Jan to switch on the scheduled run in stage. It is deliberately
being done by hand first so we can read exactly what it would send before it sends it.

---

## A2. A stuck AI task has no "Try again" button

**Where:** Needs You, and the Tasks tab on a deal.

**Current state:** When the AI cannot finish one of its own tasks it tells you why — a
missing email address, a missing contract. Once you fix the cause, it picks the task back
up on its own the next time that deal is touched. What is missing is a button to say
"try it again now".

**What this means for testing:** after you fix the cause, the task may not clear
instantly. That is expected for now.

**What is still needed:** a "Try again" action on the task.

---

## A3. Emailing a whole group of vendor tasks at once

**Where:** My Task Queue → the **Vendor** grouping.

**Current state:** You can email **one task at a time** from a vendor's group, and that
email is sent from your mailbox and recorded on the deal. What does not exist is a single
email covering several outstanding tasks for the same vendor.

**Why it is not there:** the previous version of this button opened your computer's own
mail program. Nothing it sent was recorded against the deal, which defeats the point, so
we removed it rather than leave it misleading.

**What is still needed:** a proper multi-task email that is still sent and logged through
Velvet Elves.

---

## A4. Two tasks can still share a name

**Where:** any task list.

**Current state:** A few tasks in the task database share a name and differ only in who
they are addressed to — for example two "Internal Thank You" tasks, one to your own client
and one to the co-op agent. They now show a small label saying who each one goes to, so
they can be told apart.

**Open question for Jake:** would you rather we **rename** them outright — "Internal Thank
You — Your Client" and "Internal Thank You — Co-op Agent"? That is a change to the task
database itself, so we want your decision before making it.

---

## A5. iCloud mailboxes cannot be tested for connection health

**Where:** Settings → Email & E-signature.

**Current state:** Gmail and Outlook both have a **Test connection** button that checks
your mailbox without sending anything. iCloud does not — Apple does not offer the same
kind of check. iCloud is not shown in the interface at all today (see item B5), so this
only matters if we switch it on later.

---

## A6. Replies coming back in — now confirmed working on stage

**Where:** AI Email Review.

**Status (July 28, 2026): resolved — this is now testable.** Jan verified the full
round trip on stage: an email sent from a deal was received back, matched to the
correct deal, and a suggested reply was prepared. Part 6 of the testing guide no
longer needs checking with Jan first.

---

## Section B — Earlier round (re-checked July 28, 2026)

## B1. Sharing page (internal staff) — placeholder

**Where:** `/sharing` (the internal "Sharing" surface for Agents / Team Leads / Admins)

**Current state:** This page is still a "Coming Soon" placeholder. It does not yet let
staff create or manage share links from a dedicated page.

**Note:** Sharing milestone links with sellers already works today **for FSBO customers**
through the "Share milestones" button in their own workspace — that flow is complete and
is covered in the testing review. Only the separate internal staff Sharing page is unfinished.

**What is still needed:** A real share-link manager (create a link, see live links, revoke
a link) for internal staff.

---

## B2. In-app password change — not built yet

**Where:** Settings → Profile.

**Current state:** You can now edit your name, photo, phone, bio, email signature, and even
your sign-in **email address** from Settings → Profile (this is complete and covered in the
review, feature 28.1). The one piece still missing is changing your **password** from inside
the app — there is no password field on the Profile page yet.

**What is still needed:** An account-security control to change your password while signed in.
For now, use the "Forgot password?" link on the sign-in page to reset it.

> This replaces the earlier "change email / change password" item — changing your email
> address inside the app is now done.

---

## B3. Credit wallet & billing — switched off for now

**Where:** Settings → **Billing & Credits** (workspace Admins / owners) and the
Settings hub's **Platform** group → **Platform Billing** (internal Velvet Elves staff).

**Current state:** The credit-wallet billing system — buying credits, per-transaction
pricing, the Stripe checkout flow, credit history, and the platform-side credit-pack pricing
and billing-health screens — is built but **switched off behind a feature flag** while
pricing is being finalised. With the flag off, the **Billing & Credits** card does not appear
in the Settings hub and creating a transaction is free.

**What is still needed:** Final pricing sign-off, then switch the flag on. Until then we are
not asking for feedback on the billing screens.

---

## B4. AI Coach / "AI Coach Pro" advanced analytics — intentionally switched off

**Where:** The sidebar "AI Coach" entry (Team dashboards) and the "AI Coach Pro — Advanced
Analytics" block on the Analytics page.

**Current state:** These coaching surfaces are deliberately turned **off** for now. AI Coach
is planned as a future paid add-on, so it is not part of this release and not ready for
feedback.

**What is still needed:** Build and enable the AI Coach experience when that add-on is in scope.

---

## B5. iCloud email integration — hidden for now

**Where:** Settings → Email & E-signature.

**Current state:** Only **Gmail** and **Outlook** are offered today (both complete and in the
review). iCloud is intentionally hidden because Apple does not offer a standard one-click
sign-in and needs an "app-specific password" flow we still want to review.

**What is still needed:** Finish and re-enable the iCloud (Apple Mail) connection flow.

---

## B6. AI deal workspace — parts still on the way

**Where:** The AI deal workspace that opens when you click a single transaction
(`/transactions/<deal>`).

**Current state:** The deal workspace is **complete and in the testing review** (items 17.1–17.8):
the AI assistant, the suggestions and one-click fixes, the safe date moves, document analysis on
upload, the deal tabs, and the Email tab are all ready for your feedback. A few **extras around it
are still being built**, so we are not asking for feedback on these specific pieces yet:

- **Voice input.** A microphone button is shown in the assistant's message box but is switched off
  for now ("coming soon"). Typing works fully today.
- **A built-in document viewer.** Today the assistant points you to the Documents tab to open a file;
  opening the document inside the assistant window itself is still being built.
- **Re-filing an email to the right deal.** The Email tab's Outbox and Inbox are complete; the tool to
  move an email that landed on the wrong deal is not built yet.
- **A full activity feed of the assistant's actions.** The Activity tab already shows date changes,
  status updates, and checklist edits. A complete, single feed of every AI action is still being
  expanded — for now, each applied action points you to the tab where you can see its result.
- **Team-lead oversight, "always approve" rules, and merging documents.** These are planned for a later
  stage. Today every AI action requires your explicit approval, one at a time, which is by design.

**What is still needed:** Finish and switch on the items above as their later phases are completed.

---

## B7. New Transaction wizard — address type-ahead is switched off for now

**Where:** New Transaction wizard → Step 3 (Address & Contacts), the Street Address field.

**Current state:** The Street Address field still suggests addresses you have used before, and AI
parsing fills the address from an uploaded contract. The **live address type-ahead** (Google-powered
"start typing and pick a real address" suggestions) is **temporarily switched off** because the map
service key is not configured in this environment — so we are not asking for feedback on it yet. Every
other part of Step 3 is complete and is in the testing review.

**What is still needed:** Add the address-service key and switch the live type-ahead back on.

---

## B8. Belonging to more than one workspace — waiting on a billing decision

**Where:** A workspace switcher near the top of the sidebar, and the "guest" invite flow (being
invited into another brokerage with an email you already use).

**Current state (updated July 28, 2026):** The feature flag is now **on** in the local and stage
environments, so the workspace switcher appears and guest invitations work. What is still
outstanding is the **billing rule for guest members** — who pays when someone from another
brokerage is working in your workspace. That is a pricing decision, not code.

**What is still needed:** Jake to confirm the guest-member billing rule.

---

## How this list is kept honest

Section A was checked against the live source code on July 28, 2026, after the task-and-email
fixes landed. Section B was first written on June 30, 2026 and re-checked on July 28. As each
item is finished, it will move out of this list and into the main **FRONTEND_CLIENT_TESTING_REVIEW**
with full step-by-step testing instructions.
