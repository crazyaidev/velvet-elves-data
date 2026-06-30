# Velvet Elves — Still Being Built (Not Yet Ready for Client Feedback)

**Last Updated:** June 30, 2026

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

## 2. In-app password change — not built yet

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

## 3. Credit wallet & billing — switched off for now

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

## 4. AI Coach / "AI Coach Pro" advanced analytics — intentionally switched off

**Where:** The sidebar "AI Coach" entry (Team dashboards) and the "AI Coach Pro — Advanced
Analytics" block on the Analytics page.

**Current state:** These coaching surfaces are deliberately turned **off** for now. AI Coach
is planned as a future paid add-on, so it is not part of this release and not ready for
feedback.

**What is still needed:** Build and enable the AI Coach experience when that add-on is in scope.

---

## 5. iCloud email integration — hidden for now

**Where:** Settings → Email & E-signature.

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

## 8. Belonging to more than one workspace — switched off for now

**Where:** A workspace switcher near the top of the sidebar, and the "guest" invite flow (being
invited into another brokerage with an email you already use).

**Current state:** The ability for one person to belong to several workspaces and switch between
them is built but **switched off behind a feature flag**. With the flag off, each person belongs to
a single workspace exactly as today and no switcher appears.

**What is still needed:** Finish the host-billing rules for guest members, then switch the flag on.

---

## How this list is kept honest

Everything above was checked against the live frontend source code on June 30, 2026. As each
item is finished, it will move out of this list and into the main **FRONTEND_CLIENT_TESTING_REVIEW**
with full step-by-step testing instructions.
