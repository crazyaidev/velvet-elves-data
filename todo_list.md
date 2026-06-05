# Velvet Elves — Still Being Built (Not Yet Ready for Client Feedback)

**Last Updated:** June 4, 2026

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

## How this list is kept honest

Everything above was checked against the live frontend source code on June 4, 2026. As each
item is finished, it will move out of this list and into the main **FRONTEND_CLIENT_TESTING_REVIEW**
with full step-by-step testing instructions.
