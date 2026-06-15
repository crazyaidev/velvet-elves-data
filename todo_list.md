# Velvet Elves — Still Being Built (Not Yet Ready for Client Feedback)

**Last Updated:** June 15, 2026

This is the companion list to **FRONTEND_CLIENT_TESTING_REVIEW**. The testing review
only covers features that are **fully complete** and ready for your feedback. The items
below are still being built or are intentionally switched off for now, so we are **not**
asking for feedback on them yet. We are listing them here so you can see what is on the
way and so nobody spends time testing a screen that is not finished.

If any item below is more urgent for you than its current position suggests, tell us and
we will re-prioritise it.

---

## 1. Sharing page (internal staff) — placeholder

**Where:** `/sharing` (the internal "Sharing" surface for Agents / Team Leads / Admins)

**Current state:** This page is still a "Coming Soon" placeholder. It does not yet let
staff create or manage share links from a dedicated page.

**Note:** Sharing milestone links with sellers already works today **for FSBO customers**
through the "Share milestones" button in their own workspace — that flow is complete and
is covered in the testing review. Only the separate internal staff Sharing page is unfinished.

**What is still needed:** A real share-link manager (create a link, see live links, revoke
a link) for internal staff.

---

## 2. Organization page → AI configuration — placeholder

**Where:** Organization page → **AI configuration** section (`/organization`)

**Current state:** The section shows three switches (Auto-parse uploaded documents, Task
recommendations, Smart email drafts) and an AI-usage area, but:

- The switches are display-only right now — flipping them does not change anything and the
  setting does not save.
- The AI-usage area honestly says metering "will appear here once billing is connected" —
  there is no real credit balance or usage meter yet.

**What is still needed:** Wire the switches to real per-workspace AI settings, and connect a
real AI-usage / credits meter once billing is in place.

> The other Organization sections — **Company, Branding, Email, and E-signature** — are
> complete and **are** in the testing review. Only AI configuration is a placeholder.

---

## 3. Account Security (change email / change password) — not built yet

**Where:** Avatar menu → Account → Profile

**Current state:** You can edit your name, photo, phone, and bio today (this is complete and
covered in the review). Your email address is shown read-only, with a note that email and
password changes are "coming soon."

**What is still needed:** An Account Security area to change your email address and password
from inside the app.

---

## 4. AI Coach / "AI Coach Pro" advanced analytics — intentionally switched off

**Where:** The sidebar "AI Coach" entry (Team dashboards) and the "AI Coach Pro — Advanced
Analytics" block on the Analytics page.

**Current state:** These coaching surfaces are deliberately turned **off** for now. AI Coach
is planned as a future paid add-on, so it is not part of this release and not ready for
feedback.

**What is still needed:** Build and enable the AI Coach experience when that add-on is in scope.

---

## 5. iCloud email integration — hidden for now

**Where:** Organization page → Email section.

**Current state:** Only **Gmail** and **Outlook** are offered today (both complete and in the
review). iCloud is intentionally hidden because Apple does not offer a standard one-click
sign-in and needs an "app-specific password" flow we still want to review.

**What is still needed:** Finish and re-enable the iCloud (Apple Mail) connection flow.

---

## 6. AI deal workspace — parts still on the way

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

## 7. New Transaction wizard — address type-ahead is switched off for now

**Where:** New Transaction wizard → Step 3 (Address & Contacts), the Street Address field.

**Current state:** The Street Address field still suggests addresses you have used before, and AI
parsing fills the address from an uploaded contract. The **live address type-ahead** (Google-powered
"start typing and pick a real address" suggestions) is **temporarily switched off** because the map
service key is not configured in this environment — so we are not asking for feedback on it yet. Every
other part of Step 3 is complete and is in the testing review.

**What is still needed:** Add the address-service key and switch the live type-ahead back on.

---

## How this list is kept honest

Everything above was checked against the live frontend source code on June 15, 2026. As each
item is finished, it will move out of this list and into the main **FRONTEND_CLIENT_TESTING_REVIEW**
with full step-by-step testing instructions.
