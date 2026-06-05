# Velvet Elves — Frontend Client Testing Review

## Features Currently Complete — Client Feedback Requested

**Last Updated:** June 4, 2026  
**Test Environment:** http://dev.velvetelves.com/  
**Recommended Browsers:** Chrome or Edge (please allow pop-ups and downloads)  
**Reviewer:** Client — please fill in the Feedback block under each feature

---

## How To Use This Document

### What is in this document

- This document lists every frontend feature that is currently complete and needs your review.
- Each feature includes the page address, the exact steps to test, the expected result, our ideas for future improvements, and a blank Feedback area for your notes.
- Features that are still being built (for example placeholder 'Coming Soon' pages) are intentionally left out of this review. They are listed separately in the companion `todo_list.md` so you know what is still on the way.

### How to fill in the Feedback area

- **Status** — write Pass, Fail, or Needs Work after you try the feature.
- **Comments** — anything you noticed: confusing text, slow actions, wrong results, missing fields, visual issues.
- **Improvement priority** — for the ideas listed under 'Future Improvement Suggestions', please mark each as High, Medium, Low, or Skip.

### Accounts you will need

- **Agent or Elf** — covers the main day-to-day workflow.
- **Team Lead or Admin** — needed to see the Delete button on transactions, the admin-only Task Templates pages, the Deletion Queue on the Documents page, and the full Team Members admin page.
- **Workspace Owner** — the very first person who registered the brokerage. Required for the Transfer ownership flow and the Organization page → Delete organization (schedule deletion).
- **Invited member** — sign up by clicking an invite-email link (instead of /register). Required for the invite-accept flow and the invitee branch of the onboarding wizard.
- **Attorney** — loads the attorney workspace (Matters, Releases Queue, State Rules, Recording Calendar).
- **Client** — a buyer or seller invited to a transaction; loads the 'closing concierge' client workspace at /client/home.
- **FSBO Customer** — loads the for-sale-by-owner seller workspace at /fsbo.
- **Vendor** — loads the vendor document portal at /portal/vendor.
- **Platform admin** (internal Velvet Elves staff only) — required for the /platform/tenants and /platform/advertising pages.

### Suggested order of testing

1. Public pages and sign-in / sign-up (including the new Organization field on /register)
2. Invite-accept flow (open an invite link as a brand-new user)
3. Onboarding wizard (test both founder and invitee branches) and the product tour overlay
4. Standard Agent or Elf workflow (dashboard, new transaction, transactions list, My Task Queue, Closing Calendar, Clients, Contacts, All Documents)
5. The Organization page (Company, Branding, Email & E-signature integrations — needed before AI Email Review can send) and your Account window
6. Intelligence — AI Email Review at /ai-emails, AI Suggestions, Analytics, and Vendors
7. Payments — invoices and commission payouts
8. Team Lead or Admin extras — Team Overview, Teams, Team Members admin, invite / ownership / deactivate, Team Settings, plus the Admin pages (Integrations, AI Governance, Payment Access, Advertising, Audit Log)
9. Attorney workspace (Matters, Matter detail, Releases Queue, State Rules, Recording Calendar)
10. Client, FSBO, and Vendor portals
11. Public links (milestone viewer, invoice payment, advertise storefront) — no sign-in
12. Platform admin pages (internal Velvet Elves staff only)
13. Direct links and error pages

---

## Section 1 — Public & Sign-In Pages

### 1. Terms of Service page

**Route / Location**

/terms

**How To Test**

- Open the page in two different ways.
  - Open /terms while you are signed out.
  - Open /terms again while signed in as any role.
- Scroll the page from top to bottom and read the legal text.
  - Check headings and paragraphs render without missing text.
  - Confirm any links inside the document open correctly.

**Expected Result**

- The page loads without asking you to sign in.
- The page title at the top clearly says Terms of Service.
- The full legal content appears in a clean, readable layout.

**Future Improvement Suggestions**

- Show a 'Last updated' date at the top so readers know which version they are looking at.
- Add a clickable Table of Contents so long sections are easy to jump to.
- Offer a 'Save as PDF' button for clients who want to keep a copy.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 2. Privacy Policy page

**Route / Location**

/privacy

**How To Test**

- Open /privacy while signed out, then open it again while signed in.
- Scroll the whole page and read through the policy sections.
  - Make sure nothing is cut off on the right side on a wide screen.
  - Confirm any in-page links work.

**Expected Result**

- The page loads without any sign-in prompt.
- The page title clearly says Privacy Policy.
- The content reads cleanly in both signed-out and signed-in states.

**Future Improvement Suggestions**

- Add jump links to common sections such as data storage and user rights.
- Provide a print-friendly layout so clients can save a paper copy.
- Summarize key points at the top in plain language.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 3. Protected page redirect

**Route / Location**

/dashboard (while signed out)

**How To Test**

- Sign out, then paste /dashboard directly into the browser address bar and press Enter.

**Expected Result**

- The app should send you straight to /login instead of showing the dashboard.
- No protected content (such as transactions) should appear on screen.

**Future Improvement Suggestions**

- Remember the page you originally tried to open, and take you there after you sign in.
- Show a short explanation on the login screen that says 'Please sign in to continue'.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 4. Register (sign-up) page

**Route / Location**

/register

**How To Test**

- Open /register and confirm the fields: Full name, Organization (optional), Email, Password, Confirm Password, Phone (optional), and a Terms / Privacy checkbox. A Google sign-up button is also available.
- Note: there is no Role dropdown. The first person to register for an organization is automatically the Admin and Owner of a brand-new workspace. To join an existing brokerage you must use an invite link — typing the brokerage name in Organization does not join you to it.
- Type an email already in use and confirm the page blocks Create Account and offers a 'Sign in instead' link.
- Type a weak password (under 8 characters, no number, no symbol, etc.) and confirm the page shows which rules still need to be met.
- Type mismatching passwords and confirm Create Account is blocked until they match.
- Leave the Terms / Privacy box unchecked and confirm Create Account is blocked.
- Submit a valid registration using an email you can check.

**Expected Result**

- Each invalid case shows a clear message next to the field, and Create Account stays disabled.
- After a successful submission you are either signed in and taken to /onboarding, or taken to /login with a 'please confirm your email' message.

**Future Improvement Suggestions**

- Add an eye icon that shows / hides the password while typing.
- Show a one-line preview of how the Organization name will appear on outbound emails before you submit.
- Add Microsoft / Outlook and Apple sign-up buttons next to Google.
- Auto-suggest an Organization name from the email domain (for example 'acme-realty.com' suggests 'Acme Realty').

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 5. Login (sign-in) page

**Route / Location**

/login

**How To Test**

- Check the page content.
  - A Google sign-in button is visible at the top.
  - Email and password fields are visible.
  - A 'Forgot password?' link is visible.
  - A link to the Register page is visible.
- Try bad inputs.
  - Invalid email format — an error should appear.
  - Wrong password — a clear error banner should appear.
- Sign in with a valid account, then refresh the browser tab.

**Expected Result**

- Users who have not finished onboarding go to /onboarding.
- Users who have finished onboarding go to /dashboard.
- After a page refresh, you are still signed in.

**Future Improvement Suggestions**

- Add a 'Remember me' checkbox for longer sessions.
- Show a clear lockout message after several failed attempts.
- Add optional two-step verification for extra safety.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 6. Log out

**Route / Location**

User menu (top-right avatar)

**How To Test**

- Sign in, then open the avatar menu in the top-right corner.
- Click Log Out.
- After signing out, try to re-open /dashboard directly in the browser.

**Expected Result**

- You are returned to the /login page right away.
- Protected pages cannot be opened again until you sign back in.

**Future Improvement Suggestions**

- Add a 'Sign out of all devices' option for extra safety if a laptop is shared or lost.
- Briefly confirm the sign-out with a small message ('You have been signed out').

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 7. Forgot password

**Route / Location**

/forgot-password

**How To Test**

- Verify the screen.
  - An email field and a 'Send Reset Link' button should be visible.
- Try an invalid email format first, then submit a valid email.

**Expected Result**

- Invalid formats are blocked by a clear message.
- A valid submission switches the page into a success state.
  - It shows the email address you entered.
  - It offers a 'Try a different email' link.
  - It offers a link back to sign in.

**Future Improvement Suggestions**

- Show the same success message for known and unknown emails so that no one can fish for registered emails.
- Add a 'Resend email' button that is enabled after 60 seconds.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 8. Reset password

**Route / Location**

/reset-password (opened from the reset email)

**How To Test**

- Open a real reset link from your email inbox.
- Try a weak password and confirm the page blocks it.
- Enter a strong password and a matching confirmation, then submit.
- Also test opening /reset-password directly with no token, or an expired token.

**Expected Result**

- The reset form loads correctly when the link is valid.
- A successful reset shows a success screen and then takes you to /login.
- An invalid or expired link shows a clear 'Invalid or expired link' screen with a way to request a new one.

**Future Improvement Suggestions**

- Show a password strength meter while typing.
- Warn the user that all other signed-in sessions will be logged out after reset.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 9. Email confirmation

**Route / Location**

/auth/confirm (opened from the confirmation email)

**How To Test**

- Open a valid confirmation link from your email inbox.
- Watch the spinner and wait for the redirect.
- Also open a broken / malformed confirmation URL.

**Expected Result**

- A valid link signs you in and takes you to /onboarding (new user) or /dashboard (returning user).
- A malformed link shows a clear error screen.

**Future Improvement Suggestions**

- Show the confirmed email address on the success screen so the user can double-check the right account was confirmed.
- Offer a 'Resend confirmation email' button on the error screen.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 10. Google sign-in and sign-up

**Route / Location**

/login and /register

**How To Test**

- Click the Google button on the Login page.
- Do the same on the Register page.
- Approve Google's consent screen.

**Expected Result**

- The browser goes to Google, then comes back through the app's callback page.
- You are signed in and taken to /onboarding (new user) or /dashboard (returning user).
- If Google sign-in is not configured in this environment, an error message should appear cleanly rather than breaking the page.

**Future Improvement Suggestions**

- Add Microsoft / Outlook and Apple sign-in buttons next to Google.
- Show the connected Google account email on the first screen after sign-in.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 11. Invite acceptance

**Route / Location**

/invite/<token> (opened from the invite email)

**How To Test**

- Open the invite link from your email. Both '/invite/<token>' and '/invite/accept?token=<token>' should work.
- Confirm the page shows a 'You're invited!' headline, the role you are joining as (Agent, Transaction Coordinator, Team Lead, Attorney, Client, FSBO Customer, or Vendor), and the invited email.
- Fill in Full name (required), Create password (required, at least 8 characters with at least one number), and Phone (optional).
- Try an empty name or a weak password and confirm the page blocks Submit.
- Click 'Join Velvet Elves' to submit.
- Separately, paste a fake token in the browser (e.g. /invite/some-fake-token) and confirm an 'Invalid Invitation' screen appears with a 'Go to login' link.

**Expected Result**

- A valid invite signs the new user in and takes them to /onboarding.
- On /onboarding, the wizard skips the Company / brokerage step and shows a read-only 'Joining: {brokerage name}' line instead.
- An invalid or expired token shows the 'Invalid Invitation' screen with a way back to login.

**Future Improvement Suggestions**

- Show a countdown for how long the invite is still valid (e.g. 'Expires in 6 hours').
- Add a password-strength meter that matches the one on the /register page so invitees see the same five rules.
- Show the inviter's name (for example 'Sam Closer invited you to Acme Realty') so the recipient knows it is legitimate.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

## Section 2 — First-Time User Experience

### 12. Onboarding wizard (role-aware flow)

**Route / Location**

/onboarding

**How To Test**

- Sign up for a fresh account or accept an invite. The wizard should open automatically. An account that already finished onboarding is forwarded straight to /dashboard.
- Founder vs. invitee: if you self-registered on /register, Step 2 includes a Company / brokerage field and a Brand logo upload. If you joined via an invite, Step 2 hides those fields and shows a read-only 'Joining: {brokerage name}' line instead.
- Step 1 — Welcome: confirm the page greets you by first name and shows a short intro for your role. Internal roles see four value cards; external roles (Client, FSBO, Vendor) see two. Click 'Let's go' to advance.
- Step 2 — Your Profile: confirm Full name and Phone (auto-formats as you type) are pre-filled, and a Role dropdown lets you pick your role. Founders also see Company / brokerage and Brand logo (PNG, JPEG, WEBP, SVG, GIF; max 2 MB — upload a wrong type or oversize file and confirm a clear error). Switch the Role dropdown to an external role and confirm the email and e-sign steps disappear from the step list.
- Step 3 — Email Inbox (internal roles only): connect Gmail or Outlook by clicking Connect. Confirm a real OAuth popup opens; on success the row flips to Connected. You can also click 'Skip for now' to move on.
- Step 4 — E-signature (Agent / TC / Team Lead / Attorney only): connect DocuSign through its OAuth popup, or skip.
- Final step — All set: confirm you can click 'Create your first transaction' to open the New Transaction wizard, or 'Go to dashboard' to finish. After finishing, refresh — you should land on /dashboard, not back on /onboarding.
- Refresh mid-wizard and confirm your previously-saved fields (name, phone, role, company, logo) are remembered even though the wizard restarts at Step 1.

**Expected Result**

- Each step shows only the fields that match your role.
- Internal roles see 4–5 steps; external roles see 3.
- Gmail / Outlook / DocuSign connections persist into the Organization page (Email and E-signature sections) after onboarding.
- Logo files outside the allowed types or larger than 2 MB are rejected with a clear message.
- Either final-step button marks onboarding complete on the server and triggers the product tour the next time the dashboard loads.

**Future Improvement Suggestions**

- Add a 'Save and finish later' option that remembers the current step (today only the field values are remembered).
- Detect popup-blocked browsers up front and offer a fallback redirect-based OAuth path.
- Preview the uploaded logo at the exact size it will appear in the app's sidebar.
- Let a user preview which steps an external role will see before they switch the role dropdown.
- Add an invitee-only 'Welcome from {inviter name}' line so the invitee knows who brought them in.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 13. Product Tour overlay (role-aware walkthrough)

**Route / Location**

/dashboard (and any other signed-in page once the tour is started)

**How To Test**

- Finish onboarding with a fresh test account, then land on the dashboard. The product tour should start automatically.
- If you already finished the tour, open the avatar menu → Account → Help & tour → Start tour to replay it.
- Step through the whole tour using Next / Back / Skip. Internal roles (Agent, Transaction Coordinator, Team Lead, Admin) see a 9-step tour covering sidebar KPIs, Active Transactions, My Task Queue, All Documents, AI Briefing, search, notifications, and the New Transaction button.
- Sign in as an Attorney and replay the tour — it should be a 5-step tour focused on the matter queue, documents, and AI briefing.
- Sign in as a Client, FSBO Customer, or Vendor and replay the tour — it should be a 5-step tour focused on My Properties, Documents, and Ask Velvet Elves AI.
- Use the keyboard: → or Enter to advance, ← to go back, Esc to skip. Confirm Cmd+K / Ctrl+K still opens global search mid-tour.
- Skip the tour mid-way and confirm it does not mark complete (Account → Help & tour → Start tour starts it again from the beginning).
- Finish the tour on the final step and confirm it does not auto-start the next time you log in.

**Expected Result**

- The tour highlights the right element for each step and the tooltip stays on screen.
- Internal roles see a 9-step tour; Attorney and external roles see 5-step role-appropriate tours.
- Skipping does not lock the tour; only Finish marks it complete.
- Account → Help & tour always replays the tour for the role you are signed in as.

**Future Improvement Suggestions**

- Add per-feature mini-tours (e.g. 'tour just the Documents page') reachable from inline 'New here?' badges.
- Show a one-line tip about what to try after Finish (for example 'Try uploading your first contract').
- Add an option to slow down the spotlight animation for users with motion sensitivity.
- Track tour completion analytics (where users skip) so we can prioritise improvements.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

## Section 3 — Daily Agent / Elf Workflow

### 14. Dashboard home (role-aware)

**Route / Location**

/dashboard

**How To Test**

- Open /dashboard. You are automatically sent to the dashboard built for your role — a solo Agent / Transaction Coordinator, a Team Lead, an Admin, and an Attorney each see a different layout.
- On the Agent / Team Lead dashboard, check the main areas.
  - A row of KPI tiles at the top (for example Pending commission, Pipeline volume, Closings this year, Active deals).
  - An 'Action queue' card listing the most urgent things to do.
  - A 'Priority transactions' area showing your most important deals as cards.
  - A 'Portfolio health' and a 'Portfolio intelligence' (AI) card.
  - A payments snapshot card.
- Confirm every card either shows real numbers or a clean 'all clear' / empty message — nothing should be blank or broken.
- Click the '+ New Transaction' button (top bar and sidebar).
- Sign in as a Team Lead and confirm the dashboard shows team-wide numbers; sign in as an Admin and confirm the Admin console layout.

**Expected Result**

- Each role lands on its own dashboard automatically — you never see another role's layout.
- Every card shows real data or a clean empty state.
- The New Transaction button opens the transaction wizard.

**Future Improvement Suggestions**

- Let the user reorder or hide cards to personalize their landing page.
- Add a single 'AI summary of my day' headline card at the top.
- Show a small 'this week vs last week' comparison on the KPI tiles.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 15. Sidebar and top bar

**Route / Location**

Every signed-in page

**How To Test**

- Check the sidebar.
  - Navigation items change depending on the signed-in role (for example an Agent sees Deals, Workflow, Payments, Vendors, and Intelligence groups; an Admin also sees Team and Admin groups).
  - KPI tiles in the sidebar show numbers such as overdue tasks, closings this week, active deals, and pipeline value.
- Check the top bar.
  - Click 'Today's AI Briefing' — a side panel should open (internal roles only).
  - Click any status chip (Critical / Needs Attention / On Track) — it should filter the transactions list.
  - Click the search box (or press Ctrl+K / Cmd+K) — a search panel should open and find deals, tasks, documents, and people as you type. Press Enter on a result to jump to it.
  - Click the bell icon — a notifications panel should open. If you have overdue or upcoming task reminders, a small number badge shows the unread count.
  - Open the avatar menu — confirm Account, Organization (internal roles only), and Log Out.
  - On a narrow browser window, click the mobile menu icon.

**Expected Result**

- Sidebar navigation and KPIs adjust correctly to the user's role.
- The AI Briefing panel opens and closes cleanly.
- Status chips take you to the correct filtered transaction view.
- Search returns real results and the bell opens a real notifications list with an accurate unread count.
- The avatar menu opens the Account window (Account), the Organization page (Organization), or signs you out (Log Out). The mobile menu behaves correctly.

**Future Improvement Suggestions**

- Add a sidebar collapse toggle for users on smaller laptops.
- Let the user mark all notifications as read in one click from the panel.
- Add recent-searches and saved-search shortcuts to the search panel.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 16. New Transaction wizard

**Route / Location**

Opens from the top bar, the sidebar, and the dashboard 'New Transaction' button

**How To Test**

- Start the wizard.
- Step 1 — Documents.
  - Upload one PDF, then upload several files at once.
  - Remove a file and confirm the count updates.
  - Click Split on a PDF to try the page-range selector.
  - Also try 'Skip upload — enter details manually'.
- Step 2 — AI Parsing.
  - If you uploaded a document, let AI parsing run.
  - If it cannot finish, check that you can still continue manually.
- Step 3 — Address.
  - Fill in Street, City, State, and ZIP.
  - Leave the 'I confirm this address is correct' box unchecked — Continue should stay disabled.
  - Check the box and confirm Continue becomes active.
- Step 4 — Purchase Info.
  - Enter purchase price, closing date, inspection days, financing, title ordered by, and notes.
  - Toggle Home Warranty and HOA — extra fields should appear.
  - Click Add Party and add a party.
- Step 5 — Missing Info (appears only if something is missing).
  - Leave one required field empty to trigger this step on purpose.
  - Fill it in manually, then try AI Search.
- Step 6 — Confirm.
  - Review every section.
  - Click an Edit button to jump back.
  - Finally click Accept & Create Transaction.
- Close the wizard mid-way and confirm the discard warning appears.

**Expected Result**

- Each step shows only the fields described above.
- Continue is blocked until required information is present.
- At the end, the transaction is created and the list page shows it.

**Future Improvement Suggestions**

- Add a 'Save draft and continue later' button.
- Show the uploaded document side-by-side with the AI-parsed fields.
- Show a confidence badge next to each AI-filled field (High / Medium / Low).

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 17. Active Transactions page

**Route / Location**

/transactions

**How To Test**

- Check the page header.
  - The correct title and the total deal count are shown.
  - Export CSV, Export Excel, and Print Report buttons are visible.
- Use the filter tabs.
  - All, Overdue, Due Today, Closing Soon, In Inspection, On Track, Unhealthy.
  - The list updates as you switch tabs.
- Use the sort control.
- From the sidebar, switch between Active Transactions, Pending, Closed, and All Transactions.
- Click Export CSV and Export Excel — confirm the files download.
- Click Print Report — confirm a printable window opens.
- Click the floating Ask AI button.

**Expected Result**

- Filter tabs and sidebar filters update the title and the list correctly.
- The exports download files named 'transactions.csv' and 'transactions.xls'.
- Ask AI opens the AI side panel.

**Future Improvement Suggestions**

- Let the user save custom filter views such as 'My hot deals this week'.
- Add multi-select and bulk actions on cards (bulk reassign, bulk status change).
- Let the user pick which columns to include in the CSV / Excel export.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 18. Transaction card — Tasks area

**Route / Location**

Expanded card on /transactions

**How To Test**

- Expand a card.
- In the Tasks area, click the checkbox on a task to mark it complete, then click again to mark it incomplete.
- Open the task status dropdown and change the status.
- Click '+ Add' or '+ Add Task'.

**Expected Result**

- The task state updates on screen right away.
- The Add Task button opens the Add Task window.

**Future Improvement Suggestions**

- Let the user rename a task inline without opening a modal.
- Allow drag-and-drop reordering of tasks.
- Add a 'Snooze until' option for tasks the user wants to hide temporarily.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 19. Transaction card — Key Dates area

**Route / Location**

Expanded card on /transactions

**How To Test**

- Click any key date row.
- Change the date in the popover and click Save.

**Expected Result**

- The new date shows up on the card right away.
- Overdue dates are visually flagged.

**Future Improvement Suggestions**

- When a key date changes, preview which downstream tasks will move.
- Offer a one-click 'Notify client of new date' option.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 20. Transaction card — Contacts area

**Route / Location**

Expanded card on /transactions

**How To Test**

- Expand a contact row and try the phone and email actions if those fields are filled in.
- Click the plus button to add a new contact.
- On an empty contact group, click the empty-state add area.

**Expected Result**

- The contact creation window opens with the role already chosen, matching the group you clicked.

**Future Improvement Suggestions**

- Show 'Last contacted' date next to each person.
- Add a 'Log a call' one-click shortcut that records when you called them.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 21. Add Task window

**Route / Location**

Opens from an expanded transaction card

**How To Test**

- Open the Add Task window.
  - Leave the task name empty and try to save — it should block you.
  - Enter a name, pick a Completion Method, pick a Due Date, and pick an Assignee (Myself or AI Agent).
- Click 'Get AI Suggestions on How to Complete'.
- Apply one of the AI suggestions, then submit the task.

**Expected Result**

- The task is created and the window closes.
- Applying an AI suggestion fills in the Completion Method when the suggestion provides one.

**Future Improvement Suggestions**

- Add a dropdown of common task templates for one-click creation.
- Add a 'Recurring task' option (weekly, monthly).
- Allow attaching a document while creating the task.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 22. Add Contact window

**Route / Location**

Opens from an expanded transaction card

**How To Test**

- Open the Add Contact window from different groups (Buyer, Lender, Title, etc.).
  - Confirm the role label matches the group you opened it from.
  - Confirm Company Name appears for Lender and Title groups.
- Enter First Name, Last Name, Phone, Email, and optional Company.
- Submit the form.

**Expected Result**

- The new contact is added and the window closes.

**Future Improvement Suggestions**

- Offer 'Pick from existing contacts' so vendors used on other deals can be reused without retyping.
- Auto-format phone numbers while typing.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 23. Documents window on a transaction card

**Route / Location**

Opens from the 'View / Add Documents' button on an expanded transaction card

**How To Test**

- Expand a transaction card on /transactions/active and click View / Add Documents.
- Confirm the documents panel opens and lists every document on that transaction.
- Confirm each row shows the document name, a status badge (Signed / Awaiting / Flagged / Uploaded), the version, the upload date, and the size.
- Click Download on a row. Confirm the file opens in a new browser tab without being blocked by your pop-up blocker, even if the panel has been open for a while.
- Click the document name. Confirm it also opens the download in a new tab.
- Click Add Document and upload a new file. Confirm the new file appears in the list with its version and upload date.
- Click the Email icon on a row (internal users only). Confirm the Email Document window opens above the panel and is clickable.
- Click the Version history icon. Confirm the Version history panel opens above the panel and lists every version.
- Open the three-dot menu on any row. As an internal user you should see Rename / Classify, Upload new version, and Archive. As a Client / FSBO / Vendor you should see Flag for deletion (or Flagged if you already flagged it).
- Click Archive (internal) and confirm a confirmation window opens. Click Confirm and confirm the document leaves the list.
- Click Flag for deletion (Client / FSBO / Vendor) and submit a reason. Confirm the row updates to show Flagged.
- Press the Escape key — the panel should close.

**Expected Result**

- Every action (Download, Email, Version history, Rename, Archive, Flag) opens its window or finishes its action visibly above the panel — no clicks land on something hidden behind the backdrop.
- Download is not blocked by the browser's pop-up blocker.
- Internal users can rename, classify, archive, and email a document from this panel. External users can flag a document for deletion.
- Escape closes the panel.

**Future Improvement Suggestions**

- Add a Preview window so PDFs render inline instead of opening in a new tab.
- Add Send for Signature, Refresh status, and Void envelope buttons here so internal users can finish the signature flow without leaving the transaction card.
- Add a status filter (All / Uploaded / Awaiting / Signed / Flagged) and a sort menu to make long document lists easier to scan.
- Add an internal Mark for follow-up flag so the agent can mark a document they need to come back to.
- Offer a 'Download all as zip' button for the full packet.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 24. Transaction history panel

**Route / Location**

Opens from an expanded transaction card

**How To Test**

- Open the History panel from a card.
  - Check that it slides in from the right.
- Type in the search box and confirm the list filters.
- Confirm events are grouped by date (Today, Yesterday, etc.).

**Expected Result**

- Matching events stay visible and the rest are filtered out.

**Future Improvement Suggestions**

- Add filter chips by event type (emails, tasks, documents, AI flags).
- Add an 'Export this timeline as PDF' button for client hand-offs.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 25. Print and AI actions on a transaction card

**Route / Location**

Expanded card on /transactions

**How To Test**

- Click Print on a card.
- Click the next-step suggestion or any AI chip on a card.

**Expected Result**

- Print opens a printable closing-checklist window.
- AI chips open the AI side panel.

**Future Improvement Suggestions**

- Let the user pick a print template (full checklist, one-pager, client summary).
- Let the user decide which sections to include in the printout.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 26. Velvet Elves AI chat panel

**Route / Location**

Top bar 'Today's AI Briefing', floating Ask AI button, and AI chips on cards

**How To Test**

- Open and close the panel from each of the three entry points.
- Click several of the suggested-action chips at the bottom.
- Type your own message such as 'Summarize the Smith deal' and click Send.
- Try a deal-specific question with a transaction card expanded so the AI picks up that transaction as context.
- Try the message actions on a returned reply — Copy, Edit, Delete, and Regenerate.

**Expected Result**

- Each Send produces a real AI reply (the panel is connected to a live AI service).
- Suggested chips fill the input with a useful starting prompt.
- Copy, Edit, Delete, and Regenerate all work on existing messages.

**Future Improvement Suggestions**

- Save past conversations so users can come back later.
- Let users 'pin' a transaction so the AI always uses it as context.
- Stream answers word-by-word instead of waiting for the full response.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 26.1. My Task Queue

**Route / Location**

/tasks/queue (sidebar → Workflow → My Task Queue)

**How To Test**

- Open My Task Queue from the sidebar. Confirm a 'Today's AI briefing' strip at the top and a 'Today's progress' summary.
- Use the type tabs (All / Documents / Communication / Milestones / Admin) and the Sort menu (Priority / Due date / Transaction / Task type). Confirm the list updates.
- Type in the search box ('Search tasks, deals, contacts…') and confirm the list filters.
- Tick a task's checkbox to complete it and confirm it moves to 'Completed today'; untick to bring it back.
- Click Add task, fill in the task, and confirm it appears in the list.
- Click the floating Ask AI button and confirm the AI panel opens.

**Expected Result**

- The queue gathers your tasks across every deal in one place.
- Tabs, sort, and search all narrow or reorder the list correctly.
- Completing, adding, and AI assist all work.

**Future Improvement Suggestions**

- Add a 'snooze until' option to hide a task for a day.
- Allow drag-to-reorder within a priority group.
- Add bulk-complete for several tasks at once.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 26.2. Closing Calendar

**Route / Location**

/calendar (sidebar → Workflow → Closing Calendar)

**How To Test**

- Open Closing Calendar. Confirm a month view of your transaction key dates and closings, with a way to switch to an agenda (list) view.
- Move between months and confirm events land on the right dates.
- Click an event and confirm it takes you to the matching transaction with that card opened.
- Use the 'Connect calendar' / sync controls to connect Google or Outlook (a sign-in popup opens), then use Sync to push your closings. Disconnect and confirm it stops syncing.

**Expected Result**

- The calendar is built from your real transaction dates — nothing made up.
- Events deep-link into the right transaction.
- Google / Outlook calendar connect, sync, and disconnect all work.

**Future Improvement Suggestions**

- Add a week view alongside month and agenda.
- Color-code events by deal health.
- Add an .ics download for a single closing.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 26.3. Clients hub

**Route / Location**

/clients (sidebar → Deals → Clients)

**How To Test**

- Open Clients from the sidebar. Confirm one row per represented client showing their deals and two 'needs me' signals: an unanswered client question and uploads awaiting review.
- Click a client's action (for example the unanswered-question signal) and confirm it takes you to the right transaction with the client Q&A drawer or client-access modal open.
- Use the phone / email shortcuts on a client row.

**Expected Result**

- Every represented client is listed once with their deals and what needs your attention.
- Actions deep-link to the matching transaction and open the right drawer.

**Future Improvement Suggestions**

- Add a search box and a filter for 'only clients who need me'.
- Show the last time you contacted each client.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 26.4. Contacts directory

**Route / Location**

/contacts (sidebar / global search)

**How To Test**

- Open Contacts. Confirm a searchable list of people (co-agents, loan officers, title reps, and other contacts) with their type, email, and phone.
- Type in the search box and confirm the list filters by name, email, or company.
- Use the type filter to narrow to one kind of contact.
- Confirm preferred contacts are marked (star) and vendor contacts are indicated.

**Expected Result**

- Contacts are searchable and filterable by type.
- Email and phone shortcuts work; preferred and vendor contacts are clearly marked.

**Future Improvement Suggestions**

- Add an 'add contact' button directly on this page.
- Show which transactions each contact is attached to.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 26.5. Notifications center

**Route / Location**

/notifications (and the top-bar bell)

**How To Test**

- Open the bell in the top bar, then open the full Notifications page.
- Confirm filter tabs (All / Overdue / Today / Tomorrow / Upcoming) and that each notification shows its urgency.
- Click a notification and confirm it takes you to the related task or transaction.
- Confirm reading notifications updates the unread count on the bell.

**Expected Result**

- Notifications are real task reminders grouped by urgency.
- Opening one navigates to the right place and the unread count stays accurate.

**Future Improvement Suggestions**

- Add a 'mark all as read' button.
- Add notification types beyond task reminders (new client message, signature completed).

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 26.6. AI Suggestions (intelligence inbox)

**Route / Location**

/ai-suggestions (sidebar → Intelligence → AI Suggestions)

**How To Test**

- Open AI Suggestions. Confirm a briefing hero, activity stats, and a row of category filter pills.
- Expand a suggestion card and confirm it shows the reason, the AI recommendation, an editable draft where relevant, and an action row.
- Apply an action on a card (for example send a draft, add a task, or dismiss) and confirm it does something real and the card updates.
- Use the category pills to filter the suggestions.

**Expected Result**

- Every suggestion is based on real data about your deals — no generic tips.
- Each action runs a real, role-appropriate operation.

**Future Improvement Suggestions**

- Add a 'snooze this suggestion' option.
- Let the user thumbs-down a suggestion to tune what appears.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 26.7. Analytics (Reports)

**Route / Location**

/reports (sidebar → Intelligence → Analytics)

**How To Test**

- Open Analytics. Confirm a row of KPI tiles (for example commission, transaction volume, on-time close rate) followed by charts (GCI by month, transaction volume, active pipeline, days-to-close, task completion, and so on).
- Confirm every chart shows your real numbers or a clean 'not enough data yet' message.
- Open the goals editor, set a goal, save it, and confirm the relevant tile reflects progress toward it.
- Click Export / Download and confirm a file downloads.

**Expected Result**

- All tiles and charts are driven by your real transactions.
- Goals save and show progress; export downloads a file.

**Future Improvement Suggestions**

- Let the user pick the date range / compare two periods.
- Add a team-vs-me toggle for Team Leads.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 26.8. Invoices & Payments

**Route / Location**

/payments (sidebar → Payments → Invoices & Payments)

**How To Test**

- Open Invoices & Payments. Confirm tabs: All Invoices, Open, Paid, Drafts, Void, and Payments.
- Switch tabs and confirm the list narrows; use the search box to find an invoice.
- Click New invoice, fill it in (transaction, amount, line items), and save a draft, then open it.
- Open an invoice to view its detail window; if you have permission, send it and confirm the client receives a pay link.
- Open the Payments tab and confirm recorded payments are listed.
- Sign in as a role without invoice permission and confirm the create / refund actions are not offered (read-only history is still visible).

**Expected Result**

- Invoices and payments are real and filterable by status.
- Creating, sending, and viewing invoices works; permission gating hides actions a role cannot perform.

**Future Improvement Suggestions**

- Add recurring invoices.
- Add a one-click reminder for overdue invoices.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 26.9. Commission Payouts

**Route / Location**

/payments/payouts (sidebar → Payments → Commission Payouts)

**How To Test**

- Open Commission Payouts (shown when your role / plan allows payouts).
- Confirm a list of payouts with amount and status; use the search box to find one.
- Click New payout, pick a transaction with the typeahead, enter the amount, and create it.
- Open a payout to view its detail window.

**Expected Result**

- Payouts are listed with accurate amounts and statuses.
- Creating and viewing a payout works; the action is gated by payment permission.

**Future Improvement Suggestions**

- Add a split-commission helper for co-brokered deals.
- Export payouts to CSV for accounting.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27. All Documents page — open and access

**Route / Location**

/documents (also reachable as /documents/all)

**How To Test**

- Open /documents while signed in as Agent, Transaction Coordinator, Team Lead, Attorney, or Admin.
- Try opening /documents while signed in as a Client, For-Sale-By-Owner Customer, or Vendor.
- From any page, press Cmd+K (Mac) or Ctrl+K (Windows), search for a document by name, and press Enter on the result.

**Expected Result**

- Internal roles see the full All Documents page.
- Non-internal roles are sent back to their dashboard instead.
- The Cmd+K result opens /documents with the right document highlighted and scrolled into view.

**Future Improvement Suggestions**

- Show non-internal users a one-line note explaining where they can find documents inside their assigned transactions.
- Remember the last filter and sort the user picked between visits.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.1. All Documents — AI Priority queue and Today's Priority card

**Route / Location**

/documents (default AI Priority tab)

**How To Test**

- Open /documents and stay on the AI Priority tab.
- Read the Today's Priority card at the top — it should name the most urgent item with a short reason and one or two recommended actions.
- Read the AI Briefing strip just below it — a one-sentence summary plus a button that jumps to whichever tab is most relevant right now.
- Scroll down the priority list. Each row names the document or missing item, the transaction it belongs to, and the action buttons available.

**Expected Result**

- The hero and list highlight whatever is most likely to delay a deal.
- Clicking the AI Briefing button switches to the matching tab (for example Missing or Sent for Signature).

**Future Improvement Suggestions**

- Show a short reason next to each priority row ('Closing in 3 days', 'Awaiting buyer signature for 5 days').
- Allow snoozing an item for a day so it drops out of the list without being marked complete.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.2. All Documents — filter tabs and sort

**Route / Location**

/documents (tabs under the page title)

**How To Test**

- Click each filter tab in turn: AI Priority, All Docs, Missing, Pending Review, Sent for Signature, Signed.
- Confirm the list narrows to match the chosen tab.
- Open the Sort menu and pick each option in turn: AI Impact, Close Date, Document Name, Recently Updated, Last Touched.
- Refresh the page after changing tab or sort.

**Expected Result**

- Every tab shows only the documents that match its name.
- Sort instantly reorders the visible list.
- Tab and sort choices stay in place after a refresh (they are saved in the URL).

**Future Improvement Suggestions**

- Let the user save a favourite tab + sort combination as a one-click shortcut.
- Add a 'Group by document type' option alongside the existing sort options.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.3. All Documents — actions on a priority row

**Route / Location**

/documents (any row in the AI Priority list)

**How To Test**

- Click Request on a missing-document row. Confirm the email modal opens with the right recipient and template, and that the row stays in the queue with a 'Requested today' note after Send.
- Click Nudge on a row that already had a request. Confirm a shorter follow-up email is drafted and the row updates with a 'Nudged' note.
- Click Upload on a missing-document row. Confirm the Upload Document modal opens with the transaction and document type already filled in, and that uploading clears the row.
- Find a missing item that does not have a template ready (for example Appraisal Report). Confirm the Generate button is NOT shown — only Upload / Request / Call appear.
- Find a missing item that does have a template ready (for example Lead-Based Paint Disclosure). Click Generate.
- If the transaction has all the information the template needs, confirm a draft document is created and the preview opens.
- If the transaction is missing information (for example the seller name), confirm an 'Almost ready' window appears listing each missing piece in plain English and a Fix button next to each one.
- Click Fix on one of the missing pieces. Confirm you are taken straight to the transaction page with the right field highlighted. Fill it in.
- Come back to /documents. Confirm the Generate action retries on its own and either opens the draft or shows the next missing piece. You should not have to click Generate a second time.
- Trigger Generate on a requirement that has no template at all (rare). Confirm the window now offers real next-step buttons — Upload draft manually or Request from counter-party — instead of a dead 'Got it' button.
- Click Approve on a Pending Review row. Confirm the row leaves the queue and appears in the Cleared Today strip.
- Click Mark N/A on any row. Confirm a confirmation appears, the row disappears, and an Undo option is available on the Cleared Today card.
- Click Flag on any row. Confirm a flag icon appears next to the item and is still there after refresh.
- Click Call on a row with a phone number — confirm your phone app opens and the activity is logged on the transaction.
- Click Forward on a signed document. Confirm a forward-style email modal opens with the document attached.

**Expected Result**

- Every action button does something real (sends an email, opens the right modal, or updates the queue).
- Request, Nudge, Call, and Forward keep the row visible with a 'last touched' note until the requirement is actually resolved.
- Mark N/A, Approve, Upload, and Generate clear the row and add it to the Cleared Today strip at the bottom of the page.
- Generate is only offered when the system actually has a template for that requirement.
- The missing-fields window never shows raw machine names — every line is plain English with a Fix button.

**Future Improvement Suggestions**

- Show 'Next follow-up due in N hours' on touched rows so the user knows when to nudge again.
- Add a 'Skip this field' option on the missing-fields window for rare cases where a value is genuinely unavailable.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.4. All Documents — Cleared Today strip

**Route / Location**

/documents (strip at the bottom of the page)

**How To Test**

- Read the Cleared Today header. There should be a one-line description telling you what the strip is — items resolved in the last 24 hours.
- Click the information icon next to the header. A short pop-up should explain what each kind of card means (Signed, Approved, Marked N/A, Generated, Replaced, Voided, Uploaded, Reassigned).
- Confirm the strip is visible on every tab (AI Priority, Missing, All Docs, Pending Review, Sent for Signature, Signed) — not only on AI Priority.
- Resolve a few items different ways (Approve a review, Mark something N/A, Upload a missing document, sign an envelope, generate a draft). Confirm each one shows up as a card on the strip with the matching label.
- Send a Request or Nudge from a row. Confirm those touches do NOT show up here — only true resolutions appear on the strip.
- On any card, click View Details. Confirm a small read-only window opens with the document name, the transaction, the badge, who cleared it, and when. (No more single whole-card click — every card has clear buttons.)
- On a card that points to a real document, click Open. Confirm the document preview opens.
- On a Mark N/A card (which does not have a document attached), click Open. Confirm the transaction's Documents view opens — not a dead window.
- On an Approved card, click Undo. Confirm the document goes back to Pending Review.
- On a Mark N/A card, click Undo. Confirm the row returns to the Missing list.
- On a Generated card, click Undo and confirm the draft is removed and the Missing row comes back.
- On a Signed card, confirm Undo is not offered, and a short explanation tells you to void the envelope from the document row instead.
- Use the filter buttons at the top of the strip: All, Me, Team. Confirm Me shows only items you cleared, Team shows your teammates' clears, and All shows both.
- Click 'View all cleared (last 7 days)'. Confirm a panel slides out listing every clear from the past week with the same filter buttons. Scroll down — more rows should load as you reach the bottom.
- If you are signed in as a solo agent with no teammates, confirm the Team filter button is not shown.

**Expected Result**

- The strip explains itself — a new user can tell what it is and what each card means without help.
- Cards never use a single 'click the whole card' target. Every card has a View Details button, an Open button, and an Undo where it makes sense.
- Only true resolutions appear on the strip — requests, nudges, calls, and forwards do not.
- Undo works for Approve, Mark N/A, Generated, and Uploaded clears. Signed, Replaced, and Voided clears explain why they cannot be undone here.
- Switching to Me filters the strip to your own clears; Team shows your teammates'.
- The 7-day panel shows the same items beyond the last 24 hours, with the same filter buttons.

**Future Improvement Suggestions**

- Show a small badge on the Cleared Today header when new items land while you're on a different tab.
- Group the 7-day panel by day so it reads like a timeline.
- Let the user export the 7-day list to CSV for end-of-week reporting.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.5. All Documents — Upload Document modal

**Route / Location**

Opens from the 'Upload Document' header button or from 'Upload' on a missing-document row

**How To Test**

- Open the Upload modal from the page header button.
- Open it again from the Upload action on a missing-document row and confirm the transaction and document type are already filled in.
- Drag a PDF onto the drop zone, or browse and pick a file.
- Try a file over 20 MB or an unsupported file type (.zip, .xlsx) and confirm the modal shows a clear error.
- Click Upload Document to save.

**Expected Result**

- Allowed file types: PDF, DOC, DOCX, JPG, PNG, WEBP, GIF, TXT, up to 20 MB.
- After upload, the new file appears in the document list and resolves the matching missing item if any.

**Future Improvement Suggestions**

- Auto-suggest the document type by reading the file contents on upload.
- Let the user drag and drop several files at once.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.6. All Documents — Preview and Download

**Route / Location**

Preview (eye) and Download icons on any document row

**How To Test**

- Click the Preview (eye) icon on a PDF or image — the document should open inside the window.
- Click Preview on a non-previewable file (for example a .docx) — the window should offer a Download button instead.
- Click the Download icon on a row. The document should open in a new browser tab.
- Confirm Download is not blocked by your browser's pop-up blocker, even after the page has been open for a while.
- From inside the Preview window, click Send for Signature.

**Expected Result**

- Preview opens the document inside the page so you can read it without leaving.
- Download opens the document in a new tab and is never blocked by the pop-up blocker.
- Send for Signature from Preview opens the signature modal with the document already selected.

**Future Improvement Suggestions**

- Allow side-by-side comparison of two versions in the preview window.
- Remember the last zoom level between previews.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.7. All Documents — Send for Signature (DocuSign)

**Route / Location**

'Send for Signature' header button, the row's signature icon, or the Preview footer

**How To Test**

- Open the Send for Signature modal from each of the three entry points (header button, row icon, preview footer).
- If your DocuSign account is not yet connected, click the Connect DocuSign button on the banner and complete the popup sign-in.
- Add signers using the suggested-party chips (buyer, listing agent, etc.) and / or the 'Add signer' button. Confirm you cannot send until each row has a name and a valid email.
- Edit the subject and message that will go to the signers.
- Click Send for Signature.

**Expected Result**

- After Send, a toast confirms the envelope was sent and the row updates to 'Sent for Sig.' with an 'Awaiting: {names}' note.
- Recipients receive a DocuSign email immediately.
- If sending fails, the error appears both as a toast and inside the modal so the user does not need to reopen it.

**Future Improvement Suggestions**

- Let the sender choose sequential vs. parallel signing order.
- Show live signature progress inside the modal so the user does not have to refresh the row.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.8. All Documents — manage envelopes already sent for signature (Refresh, Void, Resend)

**Route / Location**

Rows whose status is Sent for Sig., Declined, or Voided

**How To Test**

- Send a document for signature but do not let recipients sign yet. Confirm the row shows the 'Awaiting: …' line listing the recipients.
- Click Refresh on the row and confirm a toast reports the current signature status.
- Open the row's three-dot menu and click Void Envelope. Confirm a toast appears and the row switches to a 'Voided' state with a Resend option.
- Simulate a declined signer in DocuSign (Decline) and refresh — the row should switch to 'Declined' and offer Resend.
- Click Resend for Signature from a voided or declined row and confirm the Send for Signature modal reopens with the same document.

**Expected Result**

- The agent can see who has not signed yet without opening DocuSign.
- Refresh updates the row from DocuSign on demand.
- Voided and declined envelopes always offer a one-click Resend so a stuck file is never a dead end.

**Future Improvement Suggestions**

- When voiding, prompt the user for a short reason that gets passed to DocuSign.
- Add a single 'Force-sync all' button that refreshes every in-flight envelope at once.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.9. All Documents — Email Document, Edit Document (Rename / Reclassify / Reassign), Version History

**Route / Location**

Three-dot menu on any document row (internal roles only). Edit Document is also reachable from the AI Priority queue rows and the priority detail window.

**How To Test**

- Open the three-dot menu and click Email Document. Add at least one recipient and click Send Email. Confirm a toast reports the email is queued.
- Click Edit Document. The window should show two groups of fields: Identity (file name, label, document type) and Assignment (the transaction this document belongs to).
- Try to save with an empty file name and confirm it is blocked.
- Change the file name, label, or type and click Save. Confirm the row updates immediately.
- Open Edit Document again. Use the Transaction picker to move the document to a different transaction you have access to. A short note should warn you that moving the document reattaches its history and version chain.
- Save. Confirm the document leaves the original transaction's list and now appears under the new transaction.
- If the document was satisfying a missing requirement on the new transaction, confirm a 'Reassigned' card appears in Cleared Today.
- Try to reassign a document that has an envelope already sent for signature, or one that is already signed. Confirm the save is blocked with a clear message asking you to void the envelope first.
- Open Edit Document from a row in the AI Priority list (not just from the Three-dot menu on a document row). Confirm it works the same way.
- Click Version History. Confirm every version is listed with v1, v2, … and that downloading any historical version still works. Upload a replacement and confirm the latest version is marked Current.

**Expected Result**

- Email Document queues the email and records it in the transaction's communication history.
- Edit Document handles renaming, reclassifying, and reassigning a document in one window. The label is the same everywhere — there is no separate 'Rename' or 'Reassign' button.
- Reassigning the document moves it between transactions and shows up in the audit trail of both transactions.
- An envelope-in-flight or signed document cannot be reassigned, and the system tells you exactly why.
- Uploading a new version moves the previous one to Legacy.

**Future Improvement Suggestions**

- Offer saved email templates ('Client intro', 'Title hand-off', etc.).
- Allow rolling a Legacy version back to Current.
- Use AI to suggest the right document type during Edit Document.
- Add a 'Move all related documents' option when reassigning a document — copy / addendum / disclosure as a group.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.10. All Documents — Archive a document

**Route / Location**

Three-dot menu on any document row (internal roles only)

**How To Test**

- Open the three-dot menu on a document and click Archive Document.
- Confirm a confirmation dialog appears explaining the document will be archived and can be restored by an authorized user.
- Click Archive and confirm the document leaves the list.
- Open the Restore Archived panel (test 27.13) and confirm the document appears there, ready to bring back.

**Expected Result**

- Archiving requires a confirmation step.
- After archive, the document leaves the list and is no longer counted in the tabs.
- The Restore Archived panel always shows recently archived documents, so an accidental archive can be undone from there.

**Future Improvement Suggestions**

- Add a one-click Undo button on the toast right after archive so the user does not have to open the Restore Archived panel for a fresh mistake.
- Allow batch archive of several documents at once.
- Auto-clean documents that have been archived for over 90 days, with an admin warning two weeks before.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.11. All Documents — Deletion Approval Queue

**Route / Location**

'Deletion Queue' header button on /documents (internal roles only)

**How To Test**

- Sign in as Team Lead, Admin, or any other internal role.
- If no clients have flagged anything yet, confirm the Deletion Queue button is not shown at all (the header stays clean).
- When at least one document has been flagged for deletion (use 27.15 to flag one as a client / FSBO customer), confirm the Deletion Queue button now appears in the page header with a small number badge showing how many requests are waiting.
- Confirm you also see flagged documents inside the AI Priority list as 'Review deletion request' items, with higher importance if the document has already been signed.
- Click Deletion Queue. Review each pending request — confirm you can see the document name, the reason given by the requester, and a decision-notes field.
- Click Approve on one request. Confirm a clear confirmation window opens before anything is archived. If the document was signed, confirm the warning says so explicitly. Click Archive document to confirm.
- Click Reject on another request without typing a reason. Confirm you are blocked with a clear 'please enter a reason' message — Reject requires a reason so the requester knows why their request was turned down.
- Add a reason and click Reject. Confirm the document stays in place and the request is closed.
- Sign in as the original requester (the client / FSBO / vendor who flagged the document). Confirm they receive an in-app notification AND an email telling them the decision and the reviewer's reason.
- Try to approve deletion of a document that has an envelope already sent for signature. Confirm the system blocks it with a message telling you to void the envelope first.

**Expected Result**

- Every flagged request from a client / FSBO / vendor appears here for an internal reviewer, and also as a priority item in the AI Priority list so it cannot be missed.
- The button only shows up when there is work to do — the badge tells you how many requests are waiting.
- Approve always requires an explicit confirmation step. Reject always requires a reason.
- Both decisions are recorded for audit, and the requester always hears back by notification and email.

**Future Improvement Suggestions**

- Add bulk approve / bulk reject for high-volume cleanup.
- Show the requester their previous flag history if they have flagged several documents in a short period.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.12. All Documents — Connect DocuSign wizard

**Route / Location**

'Connect DocuSign' button inside Send for Signature (when no provider is connected yet)

**How To Test**

- Make sure DocuSign is not yet connected. Open the Send for Signature modal and click Connect DocuSign on the banner.
- In the wizard, click Continue to DocuSign and complete sign-in in the popup that opens.
- After the popup closes, click Back to Send for Signature.
- Try the failure path: cancel the DocuSign popup before signing in. Confirm the wizard offers a Retry button.

**Expected Result**

- The whole connection flow happens inside Velvet Elves; the user never leaves /documents.
- On success, a toast confirms the connection and the Send for Signature modal becomes usable.
- If the popup is cancelled, the wizard offers a retry without restarting from scratch.

**Future Improvement Suggestions**

- Send a tiny test envelope to the signed-in user's own email after a successful connection so they can verify the link works.
- Detect popup-blocked browsers up front and offer a redirect flow instead.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.13. All Documents — Restore Archived

**Route / Location**

'Restore archived' button in the page header on /documents (internal roles only)

**How To Test**

- Archive one or two documents from the three-dot menu on a row (see test 27.10).
- Click the Restore archived button in the page header (it sits next to Send for Sig and Upload).
- Confirm a panel opens listing recently archived documents.
- Confirm each row shows the document name and the date it was archived.
- Click Restore on a row. Confirm the document comes back to the active list and the row leaves the Restore Archived panel.

**Expected Result**

- Recently archived documents can be restored from this panel without contacting an admin.
- Restoring a document brings it back exactly where it was — same transaction, same version history.

**Future Improvement Suggestions**

- Show who archived the document and the reason, so the reviewer can decide whether to restore.
- Allow searching the panel by document name or transaction address for tenants with a lot of archived documents.
- Add a 'Restored by' note to the document's history so the audit trail is complete.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.14. All Documents — Bulk actions on the Missing tab

**Route / Location**

/documents (Missing tab)

**How To Test**

- Open the Missing tab. Each row should have a small checkbox at the left edge.
- Tick the checkboxes on two or three rows. A bulk-action bar should appear above the list showing 'N items selected'.
- From the bulk-action bar click Mark N/A. Confirm all selected rows clear at once.
- Select two or three more rows and click Request. Confirm a request email window opens for the first selected row (the system asks one recipient at a time — sending one email to several different recipients at once is not yet supported).
- Select rows and click Upload / Assign. Confirm the Upload window opens with the first selected row's transaction and document type already filled in.
- Click Clear on the bulk-action bar. Confirm the bar disappears and no rows stay selected.
- Confirm the bulk-action bar is only shown when at least one row is selected — no checked rows, no bar.

**Expected Result**

- Multi-select is only offered on the Missing tab — other tabs do not show row checkboxes.
- Mark N/A runs on every selected row at once.
- Request and Upload / Assign use the first selected row to pre-fill their modal — they do not yet send to several recipients at once.
- There is no bulk Reassign on the Missing tab — there's no existing document to move yet.

**Future Improvement Suggestions**

- Allow Request to send to several different recipients in one pass.
- Add a Select-all checkbox at the top of the list.
- Add a 'Select rows by transaction' shortcut so the user can clear an entire deal in two clicks.
- Add bulk Reassign on the All Docs and Pending Review tabs once that surface is ready.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.15. Client / FSBO Documents portal — view and flag a document for deletion

**Route / Location**

/client/documents (Client) or /fsbo/documents (FSBO Customer)

**How To Test**

- Sign in as a Client (a buyer or seller invited to a transaction) and open Documents from the sidebar. Confirm a real list of documents shared with you appears (not a stub or count-only summary).
- Sign in as an FSBO Customer and open Documents from the sidebar. Confirm the same kind of real list appears.
- Confirm each row shows the document name, the upload date, and the document type. If a document is already flagged, a small 'Flagged' badge appears next to its name.
- On a row that is not yet flagged, click the Flag for deletion button on the right edge of the row. Fill in the reason field and submit.
- Confirm the row now shows a 'Flagged' badge and the Flag for deletion button is no longer offered for that row.
- Sign in as the Agent or Team Lead for that transaction. Confirm the document now appears on the Deletion Queue (test 27.11) and as a 'Review deletion request' item in the AI Priority list.
- After the agent approves or rejects, sign back in as the original requester. Confirm a notification appears in the bell and an email is in your inbox with the decision and any reviewer note.

**Expected Result**

- Client and FSBO users see a real document list, not a placeholder.
- Anyone outside the agent team can flag a document for deletion, and the agent always hears about it through the queue.
- Once flagged, the row shows a Flagged badge so the requester does not flag the same document twice.
- The requester always hears back about the decision — through both the in-app bell and email.

**Future Improvement Suggestions**

- Add an inline preview of each document so the requester can re-read it before flagging.
- Show which transaction each document belongs to (currently only the date and type are shown).
- Allow the requester to attach a short note when their reason needs more than one line.
- Show the same list to Vendors on the vendor portal once that surface is ready.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 28. Account window — Profile (your identity)

**Route / Location**

Avatar menu (top-right) → Account → Profile. The old /profile and /settings links still open it.

**How To Test**

- Open the avatar menu in the top-right corner and click Account. A large Account window opens with a section list down the left side.
- On the Profile section, confirm your photo, Full name, Email (read-only), Phone, and a short Bio.
- Upload a photo: drag an image onto the photo box or click Upload photo (PNG or JPG, up to 5 MB). Confirm the preview updates, then remove it and confirm it clears.
- Edit your name, phone, or bio. Confirm 'Save changes' only becomes active once you change something.
- Click Save changes and confirm a success toast.
- Close the window with the X or the Escape key, reopen it, and confirm your edits stuck.

**Expected Result**

- The Account window opens over whatever page you are on — you do not navigate away.
- Email is read-only (a note explains email changes are coming soon); everything else saves.
- Your photo and name update across the app after saving.

**Future Improvement Suggestions**

- Add a change-password / account-security area for email and password changes.
- Store the photo in cloud storage so very large images are supported.
- Show which workspaces you belong to on the Profile section.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29. Account window — personal preferences

**Route / Location**

Avatar menu (top-right) → Account (sections other than Profile)

**How To Test**

- Open the avatar menu → Account. Besides Profile, internal users (Agent, Transaction Coordinator, Team Lead, Admin) see these sections down the left side: Notifications, My Checklist Templates, My Tagged Notes, My Preferred Vendors, My Internal Resources, and Help & tour.
- Open Notifications.
  - Confirm a grid of notification categories with Email / Push / In-app switches. Flip a few and click Save — confirm a success toast, then reopen and confirm they stuck.
- Open My Checklist Templates, My Tagged Notes, My Preferred Vendors, and My Internal Resources in turn.
  - Each is your own personal list — add, edit, and remove an entry, then save. These are the 'My …' personal copies; the team-wide versions live under Team → Team Settings (feature 32.14).
- Open Help & tour and click Start tour.
  - Confirm the product tour starts for whatever role you are signed in as (see feature 13).
- Sign in as a Client or Vendor and confirm the Account window shows Profile only. Sign in as an FSBO Customer and confirm it shows Profile plus a Preferences section.

**Expected Result**

- Every section saves its own changes with a clear success toast and the changes persist after reopening.
- Internal roles see all personal sections; Client and Vendor see Profile only; FSBO sees Profile plus Preferences.
- Help & tour replays the role-appropriate product tour at any time.

**Future Improvement Suggestions**

- Add a one-click 'copy my checklist template to the team' shortcut.
- Add a daily-digest email option in Notifications.
- Add a per-feature mini-tour launcher in Help & tour.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.1. Organization page — Company details

**Route / Location**

/organization (Company section). Open it from the avatar menu → Organization (internal roles).

**How To Test**

- Open the avatar menu → Organization. Confirm a page with a section rail on the left: Company, Branding, Email, E-signature, AI configuration (and, for the workspace owner only, Delete organization).
- On the Company section, as an Admin, confirm the Organization name field is editable with a Save changes button.
- Sign in as any non-Admin (Team Lead, Agent, Transaction Coordinator) and confirm the field is read-only with a note that only an Admin can change it.
- As an Admin, type a new name and click Save changes — confirm a success toast.
- Sign in as another member of the same workspace and confirm they see the new name.

**Expected Result**

- Admins can rename the workspace; everyone else sees a read-only field with a clear explanation.
- The new name shows up for every member of the brokerage.
- The Organization page replaces the old Settings page — personal preferences now live in the Account window (feature 29).

**Future Improvement Suggestions**

- Show a preview of how the name appears in the sidebar, invitation email, and outbound transaction emails.
- Add a 'workspace web address' (subdomain) field.
- Show the workspace owner's name and email on this section.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.2. Organization page — Email integrations (Gmail and Outlook)

**Route / Location**

/organization (Email section)

**How To Test**

- Open Organization → Email. Confirm a Gmail row and an Outlook row (iCloud is intentionally hidden for now).
- Click Connect on the Gmail row and complete sign-in in the Google popup. After approval the row should switch to Connected with your email and the date.
- Repeat on the Outlook row using a Microsoft 365 account.
- Cancel the popup mid-way and confirm the row stays on 'Connect' without an error.
- Click Disconnect on a connected row, read the warning that inbound sync and AI email automation will stop, then cancel (row stays connected) and try again to confirm (row returns to Connect).
- Click Refresh to re-fetch the list.

**Expected Result**

- Both providers connect through their official sign-in popup — no password is typed into Velvet Elves.
- Disconnect always asks for confirmation first.
- At least one provider must be connected for AI Email Review (features 29.7+) to send replies.

**Future Improvement Suggestions**

- Show a 'Last synced' time and a manual 'Sync now' button per provider.
- Re-enable the iCloud row once the Apple app-specific-password flow is reviewed.
- Show an indicator when the linked mailbox has unread AI drafts waiting.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.3. Organization page — E-signature (DocuSign)

**Route / Location**

/organization (E-signature section)

**How To Test**

- Open Organization → E-signature.
- If DocuSign is not yet connected, click Connect and complete the wizard (Intro → DocuSign popup → Done).
- After connecting, confirm the section shows your DocuSign account email and the date you connected.
- Click Disconnect, read the warning that future Send-for-Signature attempts will fail, and confirm.

**Expected Result**

- Connect and Disconnect both work without leaving the Organization page.
- Once connected, the same account is also used inside the Send for Signature modal on the Documents page.

**Future Improvement Suggestions**

- Add support for other providers (DotLoop, Adobe Sign) alongside DocuSign.
- Show the monthly envelope count remaining so users do not hit their DocuSign quota by surprise.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.4. Organization page — Branding (white-label)

**Route / Location**

/organization (Branding section — Admin only)

**How To Test**

- Open Organization → Branding as an Admin. Confirm a logo upload, a brand-color field, and a display-name field.
- Upload a logo (PNG, JPEG, WEBP, SVG, or GIF, up to 2 MB). Try a wrong file type or an oversized file and confirm a clear error.
- Pick a brand color and a display name, watch the live preview update, then click Save branding.
- Refresh the page and confirm your logo, color, and display name are still there.
- Confirm the saved logo and color now show in the sidebar and on the sign-in page; check that they also appear on outbound/printed documents.
- Sign in as a non-Admin and confirm Branding is read-only or hidden.

**Expected Result**

- Branding now fully saves — logo, brand color, and display name persist and apply across the app immediately (this was a placeholder before and is now live).
- Invalid logo files are rejected with a clear message.
- Only Admins can change branding.

**Future Improvement Suggestions**

- Add a 'Reset to Velvet Elves defaults' button.
- Show a sample invitation email and a sample printed document in the preview.
- Let an Admin preview dark-mode branding before saving.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.7. AI Email Review — overview, list, and filter tabs

**Route / Location**

/ai-emails

**How To Test**

- Open Intelligence → AI Email Review from the sidebar (Agent, Transaction Coordinator, Team Lead, and Admin only; Attorney and external roles do not see this entry).
- Confirm the filter tabs: All, Needs Review, Ready to Send, Low Confidence, Escalated — each with a count.
- Click each tab in turn and confirm the list narrows to that subset.
- Click Refresh and confirm the list reloads.
- Leave the page open for at least 60 seconds. The list should silently re-fetch every minute, and any new draft should appear without a manual refresh.
- Open the top-bar bell on another page and confirm the unread count matches the All tab here.
- Force an empty state by switching to a tab with no matches and confirm a clear empty message appears.

**Expected Result**

- The list only contains drafts your role is allowed to act on.
- Auto-refresh runs every 60 seconds; the list also refreshes immediately after Approve / Edit / Discard / Regenerate.
- Empty and error states show a clear next step.

**Future Improvement Suggestions**

- Add an inline search box and sort control inside the list.
- Add per-row checkboxes plus bulk Approve / Discard so a reviewer can clear a backlog quickly.
- Wire the deep-link /ai-emails/:logId so notifications open the exact draft in question.
- Stream live updates so the list does not have to poll every minute.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.8. AI Email Review — what each draft row shows

**Route / Location**

/ai-emails (list of drafts)

**How To Test**

- Look at any draft row. Confirm it shows: the subject, the recipient(s), the kind of email (Factual question / Document request / Vendor reply / Uncertain / Other), a confidence percent, an Escalated marker if the draft is past its deadline, and a 'how long ago' timestamp.
- Click a row and confirm the detail pane on the right loads the full draft (see 29.9).
- Note: there is no per-row search, sort, or bulk action yet — the only filtering surface is the tab row at the top. Please flag if this is missing for the way you want to work.

**Expected Result**

- Every row tells you at a glance how confident the AI is, who the email is to, and whether it is overdue.
- Selection survives the 60-second auto-refresh as long as the draft is still in the same filter.

**Future Improvement Suggestions**

- Show the transaction address on each row so a reviewer can scan deals without opening each draft.
- Show an attachment indicator (planned alongside attachment support).
- Offer a compact / comfortable density toggle for high-volume reviewers.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.9. AI Email Review — what the draft detail shows

**Route / Location**

/ai-emails (open any draft)

**How To Test**

- Open any draft and confirm the top of the detail shows the email kind, the confidence percent, and an Escalated marker if applicable. The subject and the To / Cc lines are also visible (by default the file owner is automatically CC'd).
- Read the AI-drafted reply. Any phrases the AI is unsure about should be highlighted in the body, and if it made any explicit assumptions, those are listed below the body as 'Flagged assumptions'.
- On the right side, confirm an 'AI Verified From' card lists every piece of source data the AI used (address, closing date, status, document names, etc.). If the list is empty, a warning explains that no source data was cited and that the agent should verify each fact manually.
- Below it, confirm an 'Original Inbound' card shows the email that triggered this draft (sender, time, subject, body). If the original can't be loaded, the card says so cleanly.

**Expected Result**

- The confidence percent, kind, and escalation status match whatever was shown on the list row.
- Highlighted phrases in the body match the explicit 'Flagged assumptions' list.
- AI Verified From only shows facts the AI actually used — it does not guess.
- Original Inbound shows the email that triggered this reply, not the entire thread (full-thread view is a future improvement).

**Future Improvement Suggestions**

- Show the entire thread, not just the immediate inbound, so a reviewer can see prior context.
- Make each AI Verified From row clickable so it deep-links to the source field on the transaction record.
- Add an inline 'Flag this fact as wrong' button that pushes a correction back into the AI's training data.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.10. AI Email Review — Approve & Send, Edit & Send, Regenerate, Discard

**Route / Location**

/ai-emails (action buttons on the open draft)

**How To Test**

- Open a draft and click Approve & Send. Confirm the email is sent and a toast confirms.
- Open another draft and click Edit. The subject and body should become editable. Make a change and click Send Edit — confirm the edited version is sent.
- Click Regenerate on a draft. Confirm the AI redraws a fresh reply from the original inbound email.
- Click Discard. Confirm a warning explains the draft will be removed but the original inbound message stays in the communication log. Confirm Discard removes the draft.
- Disconnect your email provider on the Organization page (Email section), then click Approve & Send on a draft. Confirm a clear error explains that no email provider is connected.
- Confirm the actions that are NOT here yet: no Reassign, no 'Mark Reviewed', no attachment uploader, no scheduled-send.

**Expected Result**

- Approve, Edit, Regenerate, and Discard all complete with a toast and the list refreshes.
- Editing a draft also clears its flagged assumptions, since the human reviewer rewrote the content.
- Discard preserves the original inbound message in the communication log — only the draft disappears.
- If your role is not allowed to act, an error toast explains it on click rather than the button being hidden.

**Future Improvement Suggestions**

- Add a Reassign button so a Team Lead can hand a draft to a colleague without opening it.
- Add a Mark Reviewed (no-send) status for drafts the human read but does not want to send.
- Add support for attachments when replying so contracts and addenda can ride out with the AI reply.
- Add a per-tenant 'Auto-send when confidence is over X%' threshold (backend already supports it; no UI yet).

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.11. Vendor directory

**Route / Location**

/vendors

**How To Test**

- Open the sidebar and click Vendors, or go to /vendors directly.
- Confirm a card for every vendor company shows the name, category, contact email, and phone.
- Use the search box to find a vendor by company name, category, or email.
- Use the category dropdown and the 'Preferred only' toggle to narrow the list.
- Click New vendor and add a vendor company. Confirm it appears in the directory.
- Click a vendor card to open the vendor detail page.

**Expected Result**

- Every vendor stored for your brokerage shows up in the directory and stays reachable from any transaction.
- Search, category, and preferred filters all narrow the visible list in real time.
- New vendors created here can be assigned to transactions afterwards.

**Future Improvement Suggestions**

- Show the number of open transactions each vendor is currently assigned to.
- Allow tagging vendors with custom labels (for example 'fast turnaround', 'cash only').

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.12. Vendor detail page (contacts, portfolio, background refresh)

**Route / Location**

/vendors/{vendorId}

**How To Test**

- Open a vendor from the directory.
- Confirm the page shows the company name, category, address, phone, email, and preferred status.
- Under Contacts, confirm each person on file shows a name, email, and phone, with the primary contact clearly labelled.
- Click the Email button on a contact and confirm the Send Vendor Request modal opens with that contact pre-filled.
- Hover the Call button — until SMS / voice integration is enabled it should show a 'Coming soon' note.
- Under Portfolio, confirm a list of transactions where this vendor is on the team.
- Click Refresh info — the Background refresh drawer opens (see entry 29.16).
- Click Add colleague (public link) — confirm a one-time link is created and copied to the clipboard.

**Expected Result**

- The page summarises everything you need to know about the vendor in one screen.
- Email opens the request flow with the right contact selected.
- Add colleague creates a public link that the vendor can use to add a teammate without logging in.
- Refresh info opens the suggestions drawer; nothing applies without an explicit click.

**Future Improvement Suggestions**

- Show the latest vendor reply per transaction directly on the portfolio list.
- Allow the agent to set vendor-specific reply expectations (for example 'always reply within 24h').

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.13. Send Vendor Request (template-based email)

**Route / Location**

Email button on a vendor contact card, or from a task that has a vendor assignment

**How To Test**

- Open a vendor detail page and click Email on one of the contacts.
- Pick a template from the list (for example 'Inspection — Schedule Visit'). Confirm the right pane previews the subject and body with the transaction address, task name, and primary contact name filled in.
- Confirm the body ends with the reply footer 'Reply with: Scheduled: YYYY-MM-DD' (or the equivalent footer for the chosen template).
- Edit the subject or body inline if you want.
- Click Send request.
- Open the Communications panel for the same transaction and confirm a new outbound row appears with the right vendor and timestamp.
- Check the vendor's inbox in another window — the email should be there.

**Expected Result**

- The request is sent through the agent's connected Gmail or Outlook (not from a Velvet Elves address).
- Both the email and a record of it appear in the transaction's communication log.
- If no email provider is connected, the modal explains how to fix it and does not silently fail.

**Future Improvement Suggestions**

- Allow attaching the most recent contract or inspection report directly from the modal.
- Schedule the send for later (overnight or a specific weekday).

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.14. Vendor proposals queue

**Route / Location**

/vendor-proposals (sidebar → Intelligence → Vendor Proposals)

**How To Test**

- Open /vendor-proposals from the sidebar.
- Confirm three tabs: 'Awaiting decision', 'Awaiting vendor', and 'All open'.
- Each proposal card should show the task name, the vendor company, the original task date, and the date the vendor is proposing.
- Click Accept & update task on a pending proposal — confirm a toast reports the task date was updated, and check the matching transaction's task tab to verify the new date.
- Click Ask vendor to clarify on a vague proposal (one with no clear date) — confirm the proposal moves to the 'Awaiting vendor' tab.
- Click Reject on another proposal — confirm a toast reports the task date is unchanged.

**Expected Result**

- Every vendor reply that proposes a new date lands here for the agent to approve.
- Accept is the only action that changes a task's due date — nothing happens automatically.
- Decisions are recorded in the audit log for compliance.

**Future Improvement Suggestions**

- Show the original vendor email inline so the agent does not have to bounce between this page and /ai-emails.
- Suggest an alternative date when Reject is clicked, so the agent can immediately reply with one.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.15. Add a vendor colleague (public link)

**Route / Location**

'Add colleague (public link)' button on a vendor contact card; the public page is /v/{token}

**How To Test**

- On a vendor detail page, click Add colleague (public link). Confirm a one-time link is copied to your clipboard.
- Open the link in a private / incognito browser window. The page should show only your brokerage name and the vendor company name (no transaction details).
- Submit the form with first name, last name, email, optional phone, and optional title.
- Confirm the success screen reads 'You're on the thread.'
- Back in the authenticated app, reload the vendor detail page and confirm the new contact appears in the Contacts list (not marked primary).
- Try opening the same link again — the page should report the link is no longer valid (single-use).

**Expected Result**

- Vendors can attach a colleague without creating an account.
- The public page never leaks any transaction information.
- Each link can be used exactly once and expires after the default window (7 days).

**Future Improvement Suggestions**

- Allow the vendor to set their own preferred contact channel (email or SMS) right on the public form.
- Let the agent customise the welcome message that appears on the public page.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.16. Vendor background refresh (suggested updates)

**Route / Location**

'Refresh info' button on a vendor detail page

**How To Test**

- Open a vendor detail page that already has one or more contacts and click Refresh info.
- In the drawer, click Run refresh. Confirm suggestions appear as 'Current value' vs. 'Suggested value' cards with a confidence score and source label.
- Tick one or two suggestions and click Apply selected.
- Confirm a toast reports the vendor record was updated, and the At-a-glance section on the vendor detail page reflects the new values.
- Reopen the drawer and confirm the suggestions you accepted are gone but the others remain.

**Expected Result**

- Suggestions are based on existing tenant data (other transactions, other contacts) — no public web search.
- Nothing changes on the vendor record without an explicit click.
- Every accepted change is recorded in the audit log per field.

**Future Improvement Suggestions**

- Pull from approved public sources (state licensing boards, business directories) once that is reviewed.
- Run the refresh on a schedule for preferred vendors so suggestions are always fresh.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

## Section 4 — Admin / Team Lead Extras

### 30. Task Templates list

**Route / Location**

/admin/task-templates

**How To Test**

- Type in the search box to filter templates.
- Confirm templates are grouped by category.
- Click New Template and create a template.
  - Fill in Name, Description, Automation Level, and Category.
  - Submit.
- Click an existing template to open it.

**Expected Result**

- The newly created template appears in the list right away.

**Future Improvement Suggestions**

- Allow CSV import and export of templates.
- Add a 'Duplicate this template' shortcut.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 31. Task Template detail

**Route / Location**

/admin/task-templates/<templateId>

**How To Test**

- Open a template.
  - Check the read-only detail view.
- Click Edit Template and update several fields.
  - Name, description, target, milestone label, dependency, float days, automation level, category, sort order, active toggle.
- Try the dependency rule builder section.
- Click Save.

**Expected Result**

- All changes persist and the page returns to read-only mode.

**Future Improvement Suggestions**

- Add a visual dependency graph so admins can see how tasks connect.
- Show a 'where used' indicator listing which transaction types use this template.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32. Admin user detail

**Route / Location**

/admin/users/<userId> (reachable from /admin/users and /team)

**How To Test**

- From /admin/users, click a member's name or 'View profile'. The detail page should open.
- From /team, click any member tile in 'Recently added members' and confirm it opens the same page.
- Confirm the page shows the member's name, email, phone, joined date, last sign-in, role, and active/inactive status. The workspace owner is clearly marked.
- Paste /admin/users/some-fake-id directly in the browser. Confirm a 'Failed to load user' error card appears (not a white screen).

**Expected Result**

- A valid user id renders the profile without errors.
- An invalid or deleted user id shows a clean error state with a way to navigate back.

**Future Improvement Suggestions**

- Add an audit trail showing the user's recent actions (logins, role changes, transactions worked).
- Add an inline Edit form so an Admin can update name, phone, or role from this page.
- Show recent transactions assigned to this user so a Team Lead has full context.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.1. Team Overview page

**Route / Location**

/team (Team Lead and Admin only)

**How To Test**

- Sign in as Team Lead or Admin and open Team from the sidebar.
- Try the same as Agent, Transaction Coordinator, Attorney, Client, FSBO, or Vendor — the page should redirect to Unauthorized.
- Confirm the four overview numbers at the top: Active Members, Pending Invites, Seats Used (if your plan has a seat limit), and Recently Active.
- Confirm the 'Recently added members' list shows up to 12 members with their role; the workspace owner is clearly marked.
- Click any member to open their detail page (feature 32).
- Confirm the Role Coverage area shows how many people you have in each role (Admin, Team Lead, Transaction Coordinator, Agent, Attorney).
- Confirm the side panels show Pending Invites (with time left), Last Seen (recent sign-ins), and Seat Usage (if your plan has a seat limit).
- Click the Team Members and Task Templates quick-link cards at the bottom and confirm they open the matching admin pages.
- Click Manage team in the header and confirm it opens /admin/users (feature 32.2).

**Expected Result**

- Only Team Lead and Admin can reach the page.
- Every panel reflects real data for your workspace.
- Quick links navigate to the right admin page.

**Future Improvement Suggestions**

- Let the user filter Team Members by clicking a role on the Role Coverage row.
- Show a 7-day activity sparkline on the top numbers.
- Allow pinning a favourite member for quick contact from the side rail.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.2. Team Members admin — Active members tab

**Route / Location**

/admin/users (Team Lead and Admin only)

**How To Test**

- Open /admin/users from the Team Overview page (Manage team) or directly.
- Sign in as Agent or another lower role and confirm the URL redirects to Unauthorized.
- Confirm two tabs: 'Active members' and 'Pending invitations'.
- On the Active members tab, type in the search box and confirm the list filters by name and email as you type.
- Open the role dropdown, pick a role, and confirm only members with that role remain. Combine search and role filter and confirm both apply.
- Expand a member card. Confirm Email, Phone, Joined date, and Last sign-in are shown, with a 'View full profile' button.
- If you are the workspace owner, confirm a Transfer ownership button appears in the expanded card (see 32.5).
- If you are Admin, confirm a Deactivate button appears in the expanded card for every member except yourself and the owner (see 32.6).
- Apply a search term with no matches and confirm a clear 'no members match' message appears.

**Expected Result**

- Search and role filter narrow the list in real time.
- Transfer ownership and Deactivate buttons only appear for users who have permission to use them, and never on your own card.

**Future Improvement Suggestions**

- Show a 'last active' time directly on the collapsed card.
- Add bulk selection so an Admin can deactivate or change role for multiple members at once.
- Add an inline 'Resend welcome email' action for members who never signed in.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.3. Team Members admin — Pending invitations tab

**Route / Location**

/admin/users → 'Pending invitations' tab

**How To Test**

- Switch to the Pending invitations tab on /admin/users.
- If there are pending invites, confirm each row shows the invited email, the invited role, and how much time is left before the invite expires.
- Click Copy link on a row and confirm the invite URL is copied to your clipboard.
- In the row's three-dot menu, try Resend email, Extend by 72h, and Revoke invitation. Each should show a confirming toast and update the row.
- If there are no pending invites, confirm a clear empty state pointing at the Invite teammate button.
- Block your browser clipboard and click Copy link — confirm a clear error appears rather than a silent failure.

**Expected Result**

- All four row actions (Copy link, Resend, Extend, Revoke) work on pending invitations.
- Accepted invitations do not appear on this tab.
- Revoking an invitation removes the row and prevents the invitee from accepting.

**Future Improvement Suggestions**

- Add a Bulk revoke expired button so cleanup is one click instead of many.
- Show who originally sent each invitation so a Team Lead can see which Admin invited a particular email.
- Show a preview of the full invite URL before copying.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.4. Invite teammate modal

**Route / Location**

/admin/users → 'Invite teammate' button

**How To Test**

- Click Invite teammate on /admin/users.
- Confirm two required fields: Email address and Role. A short hint under the dropdown explains what each role can do.
- Sign in as different inviter roles (Agent, Team Lead, Admin) and confirm the dropdown only offers roles you are allowed to grant — for example only Admins can invite new Admins.
- Try to send with an empty email and confirm it is blocked.
- Try to invite an email that already belongs to a member and confirm an inline error explains the email is already in use.
- If your plan has a seat cap, try inviting beyond the cap and confirm a seat-limit error appears.
- Send a valid invitation and confirm a success toast appears, the modal closes, and the new row appears on the Pending invitations tab.

**Expected Result**

- Roles you cannot grant are not offered in the dropdown.
- Every failure mode shows a clear inline error rather than breaking the modal.
- A successful invite appears in the Pending invitations list immediately.

**Future Improvement Suggestions**

- Allow inviting multiple emails at once (comma-separated) so an admin can bulk-onboard a team.
- Show a 'view what the invitee will see' preview link before sending.
- Let the admin attach a team or a transaction at invite time (planned for Phase 5).

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.5. Transfer workspace ownership

**Route / Location**

/admin/users → member three-dot menu (workspace owner only)

**How To Test**

- Sign in as the workspace owner and confirm you are clearly marked as the owner on /admin/users.
- Open the three-dot menu (or expand the card) on a different member and confirm a Transfer ownership option is offered. It should not appear on your own row or on a member who is already the owner.
- Click Transfer ownership. Confirm the warning dialog explains: the target will be promoted to Admin if they are not already one; you will stay as Admin but lose owner-only abilities (schedule deletion, transfer ownership); and the action is logged.
- Confirm the transfer. After success, the owner mark moves from your row to the new owner's row.
- Refresh the page and confirm the new ownership state persists.
- Sign in as a regular Admin (not the owner) and confirm Transfer ownership is hidden from every member's menu.

**Expected Result**

- Only the current owner sees the Transfer ownership control.
- The confirmation dialog clearly describes the side effects before you commit.
- After transfer, the previous owner can no longer schedule deletion or transfer ownership — those controls disappear from Settings.

**Future Improvement Suggestions**

- Send an automatic email to the new owner immediately so they know responsibility has moved.
- Add an undo window (for example 30 minutes) on a recently-transferred ownership.
- Show the full audit trail of past ownership transfers on the Team Overview page.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.6. Deactivate a member

**Route / Location**

/admin/users → member three-dot menu (Admin only)

**How To Test**

- Sign in as an Admin who is not the target. Open another member's three-dot menu (or expand their card) and confirm a Deactivate option is offered.
- Confirm Deactivate is hidden on the workspace owner's row and on your own row.
- Click Deactivate. A confirmation dialog should explain the member will no longer be able to sign in and can be re-activated later.
- Cancel and confirm the member is still listed. Try again and confirm — the member disappears from Active members.
- Switch to Pending invitations and confirm any invitations the deactivated user created are still listed there.

**Expected Result**

- Deactivation requires confirmation and updates the list immediately.
- The owner cannot be deactivated — the option is hidden on their row.
- You cannot deactivate yourself — the option is hidden on your own row.

**Future Improvement Suggestions**

- Add a paired Re-activate control that surfaces deactivated members in a separate sub-list.
- Capture a deactivation reason at confirmation time so the audit log records why.
- Auto-revoke any active browser sessions for the deactivated member.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.7. Organization page — Delete organization (Danger Zone)

**Route / Location**

/organization (Delete organization section — workspace owner only)

**How To Test**

- Sign in as the workspace owner, open the avatar menu → Organization, and confirm a 'Delete organization' entry appears at the bottom of the section rail.
- Sign in as any other role on the same workspace and confirm the Delete organization entry is not shown at all.
- As the owner, open Delete organization. Confirm the page asks you to type the workspace name exactly before Schedule deletion becomes available.
- Schedule deletion and confirm a clear message reports the exact date and time it will run, plus a note that audit logs and a full snapshot are archived under the 2-year retention policy.
- Click Cancel deletion and confirm the workspace returns to normal.
- If your workspace is on legal hold, confirm the Delete button is disabled with a clear explanation pointing the owner at platform support.

**Expected Result**

- Only the workspace owner can see and use the Danger Zone.
- Scheduling deletion requires typing the workspace name exactly, and the action can be reversed during the grace period.
- Members can still sign in while deletion is scheduled, so the owner can cancel it.
- Legal hold blocks the action with a clear plain-language reason.

**Future Improvement Suggestions**

- Show a top-of-page banner with the deletion date and days remaining while deletion is scheduled.
- Send a daily reminder email to the owner while deletion is scheduled.
- Let the owner customise the grace-period length (default is 30 days).
- Add a 'Download a full export before I leave' button next to the schedule-deletion CTA.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.9. Platform Admin — Tenants list (internal Velvet Elves staff only)

**Route / Location**

/platform/tenants (platform admins only)

**How To Test**

- Sign in as a platform admin and open /platform/tenants.
- Sign in as any non-platform user and try /platform/tenants directly — confirm you get a 404 (not a 403), so the route's existence is not leaked.
- Use the filter dropdown (All / Active / Suspended / On legal hold) and confirm the table narrows correctly.
- Each tenant row should show the tenant name, slug, current status, plan, and an Actions menu.
- Click Details on a row and confirm the tenant detail page opens (feature 32.10).
- Click Suspend on an active tenant. Confirm a warning explains members will not be able to sign in and that you can reactivate later. Confirm and check the row updates.
- Confirm the Suspend button is disabled for a tenant on legal hold.
- Click Reactivate on a suspended tenant and confirm it returns to Active.

**Expected Result**

- Non-platform users get a 404 — the route's existence is not leaked.
- Filters narrow the list correctly.
- Suspend / Reactivate updates the row immediately and is recorded in the platform audit log.

**Future Improvement Suggestions**

- Add a search box that matches name / slug / owner email.
- Add a Schedule deletion action on the row alongside Suspend (currently only available inside the tenant's own Organization page → Delete organization).
- Show owner email and member count as extra columns.
- Add a 'Force re-verify domain' action for tenants on a custom domain.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.10. Platform Admin — Tenant detail (internal Velvet Elves staff only)

**Route / Location**

/platform/tenants/<tenantId> (platform admins only)

**How To Test**

- Open a tenant detail by clicking Details on /platform/tenants or by pasting the URL.
- Confirm the page shows the tenant name, slug, created date, status (Active, Suspended, Legal hold, or Deletion scheduled), and an All tenants back link.
- Confirm the Identity panel lists ID, slug, custom domain (if any), domain verification status and timestamp, owner user id, and the invite base URL.
- Confirm the Plan & lifecycle panel lists plan name, seat limit, staff seats used, trial-ends date (if any), scheduled-deletion timestamp (if any), and the legal-hold reason (if any).
- Sign in as any non-platform user and try the URL directly — confirm you get a 404.
- Open the URL with an invalid tenant id and confirm the page shows a clear 'Tenant not found' message with a back link.

**Expected Result**

- All read-only data renders without errors.
- Non-platform users cannot reach this page even with a direct URL.
- An invalid or deleted tenant id shows a clean fallback, not a broken page.

**Future Improvement Suggestions**

- Add inline edit for tenant name and plan from this detail page.
- Show the tenant's recent audit-log events (last 50) directly on this page.
- Add a Reset domain verification control for tenants stuck on unverified.
- Add a Set / clear legal hold control on this page (currently the field is read-only).

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.11. Vendor email templates (Admin / Team Lead)

**Route / Location**

/admin/vendor-templates

**How To Test**

- Sign in as Admin or Team Lead and open Team → Vendor Templates.
- Confirm five system templates ship with every tenant: Inspection — Schedule Visit, Inspection — Reschedule, Appraisal — Schedule Visit, Title — Document Request, Generic Vendor — Scheduling.
- Open any system template. Confirm its body includes the required reply footer 'Reply with: Scheduled: YYYY-MM-DD'. Tune the subject or body and click Save.
- Click New template, fill in the name, category, subject, and body, then save. Confirm the new template appears with a 'Custom' label.
- Sign out and back in as an Agent, then open the Send Vendor Request modal from a vendor's contact card — confirm the new custom template appears in the template picker.
- Deactivate a custom template and confirm it no longer appears for agents.

**Expected Result**

- Every tenant has the five system templates available out of the box.
- Admins and Team Leads can add, edit, and deactivate custom templates; agents can use them but cannot edit them.
- System template names and categories are locked, but their subject and body can still be tuned.

**Future Improvement Suggestions**

- Show a live preview of the rendered email with a sample transaction filled in.
- Allow importing and exporting templates as a single file.
- Track how often each template is used so the team can retire low-value ones.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.12. Communication audit page

**Route / Location**

/admin/communications (the legacy /communications URL still redirects here)

**How To Test**

- Sign in as Team Lead or Admin and open Team → Communication audit.
- Confirm two tabs: 'Audit log' (visible to Team Lead and Admin) and 'Export requests' (visible to Admin only).
- On the Audit log tab, use the filter row: search, channel, direction, date range, AI-only, vendor-only, and party email.
- Filter to a single transaction and click Download CSV — a single-transaction CSV downloads.
- Open Export requests (Admin only) and submit a multi-transaction export request. Confirm it appears in the list and can be downloaded once it finishes.
- Try to open /admin/communications as a regular Agent — the page should redirect to Unauthorized.

**Expected Result**

- Team Lead and Admin can audit every communication across every transaction.
- Single-transaction CSV downloads work in the foreground; multi-transaction exports go through the request queue.
- Agents and lower roles cannot reach the page.

**Future Improvement Suggestions**

- Add a saved-search feature so admins can revisit the same filter quickly.
- Email the requester automatically when a multi-transaction export is ready.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.13. Teams

**Route / Location**

/admin/teams (Admin only; sidebar → Team → Teams)

**How To Test**

- Sign in as an Admin and open Teams from the sidebar.
- Confirm a list of the teams in your workspace, each showing its lead and member count.
- Click New team, fill in the setup dialog (name and lead), and save — confirm the new team appears.
- Edit a team and change its name or lead, then save.
- Delete a team and confirm a confirmation step appears before it is removed.

**Expected Result**

- Admins can create, rename, and delete teams.
- Every change requires the expected confirmation and updates the list immediately.

**Future Improvement Suggestions**

- Show each team's active-deal count and pipeline value.
- Allow moving several members between teams at once.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.14. Team Settings (team-wide playbook)

**Route / Location**

/admin/team-settings (Team Lead and Admin; sidebar → Team → Team Settings)

**How To Test**

- Open Team Settings from the sidebar. Confirm a section rail like the Organization page, with: Checklist Templates, Tagged Notes, Preferred Vendors, and Internal Resources.
- As an Admin, use the team picker at the top to choose which team you are editing. (A Team Lead is automatically locked to their own team.)
- In each section, add or edit an entry and save. Confirm it persists.
- Confirm these are the team-wide versions; the personal 'My …' copies live in your Account window (feature 29).

**Expected Result**

- One place to edit a team's whole playbook (checklists, notes, vendors, resources).
- Admins choose a team; Team Leads are scoped to their own team automatically.
- Saved changes apply to everyone on that team.

**Future Improvement Suggestions**

- Add a 'copy from another team' shortcut to clone a playbook.
- Show which agents are using each checklist template.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.15. Admin — Integrations (CRM / webhooks)

**Route / Location**

/admin/integrations (Admin only; sidebar → Admin → Integrations)

**How To Test**

- Sign in as an Admin and open Integrations.
- Click to register a new webhook endpoint, pick the events it should receive, and save.
- Copy the signing secret with the copy button.
- Fire a test event and confirm a delivery attempt is recorded with its result.
- Review the delivery history for an endpoint.

**Expected Result**

- An Admin can set up a CRM / integration webhook end-to-end without an engineer.
- Test events and delivery history both work.

**Future Improvement Suggestions**

- Add ready-made templates for popular CRMs.
- Add automatic retry with backoff for failed deliveries.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.16. Admin — AI Governance

**Route / Location**

/admin/confidence (Admin only; sidebar → Admin → AI Governance)

**How To Test**

- Sign in as an Admin and open AI Governance.
- Confirm plain-English 'what AI can do' and 'what AI cannot do' lists.
- Adjust the confidence thresholds (for example the review threshold and the auto-send threshold) and save.
- Confirm the change affects how AI Email Review classifies and auto-sends drafts (feature 29.7+).

**Expected Result**

- Admins control the AI confidence thresholds for the whole workspace.
- AI never sends below the review threshold without a human; the page states this clearly.

**Future Improvement Suggestions**

- Show a recent history of auto-sent vs held drafts at each threshold.
- Allow per-team thresholds, not just per-workspace.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.17. Admin — Payment Access

**Route / Location**

/admin/payment-access (Admin only; sidebar → Admin → Payment Access)

**How To Test**

- Sign in as an Admin and open Payment Access.
- Confirm a grid of roles (Agent, Elf / Transaction Coordinator, Team Lead) against capabilities (create invoice, refund, trigger payout).
- Turn a capability on or off for a role and save.
- Sign in as that role and confirm the matching action appears or disappears on the Payments pages (features 26.8–26.9).

**Expected Result**

- Admins decide which roles can create invoices, issue refunds, and trigger payouts.
- Changes take effect on the Payments pages for that role.

**Future Improvement Suggestions**

- Allow per-person overrides, not only per-role.
- Show an audit trail of who changed which capability.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.18. Admin — Advertising

**Route / Location**

/admin/advertising (Admin only; sidebar → Admin → Advertising)

**How To Test**

- Sign in as an Admin and open Advertising. Confirm three cards: Workspace ads (a single on/off toggle, OFF by default), Your house ads, and Performance.
- Turn Workspace ads on and confirm sponsored placements may then appear in the workspace; turn it off and confirm they stop.
- Create a house ad: add the details, upload an image, and approve it. Confirm each ad shows a plain-English 'why it is / isn't showing' chip.
- Pause a house ad and confirm it stops showing.
- Check the Performance card for impressions, clicks, and click-through rate.

**Expected Result**

- Ads are OFF until an Admin explicitly turns them on.
- House ads can be created, approved, and paused, each with a clear status reason.
- Performance numbers reflect this workspace's ads.

**Future Improvement Suggestions**

- Add scheduling (start / end dates) for a house ad.
- Add simple A/B testing for two creatives.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.19. Admin — Audit Log

**Route / Location**

/admin/audit-logs (Admin only; sidebar → Admin → Audit Log)

**How To Test**

- Sign in as an Admin and open Audit Log.
- Confirm a list of recorded actions across the workspace (documents, transactions, tasks, users, invitations, vendors, AI emails, and so on).
- Filter by entity type and confirm the list narrows.
- Expand an entry and confirm it shows who did what and when.
- Scroll to load more entries.

**Expected Result**

- Every meaningful action is recorded and filterable.
- Each entry clearly shows the actor, the action, and the time.

**Future Improvement Suggestions**

- Add a date-range filter and free-text search.
- Add CSV export for a filtered view.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.20. Platform Admin — Advertising (internal Velvet Elves staff only)

**Route / Location**

/platform/advertising (platform admins only)

**How To Test**

- Sign in as a platform admin and open Platform → Advertising.
- Sign in as any non-platform user and try /platform/advertising directly — confirm you get a 404 (the route's existence is not leaked).
- Review and manage the platform-wide / partner ad inventory shown here.

**Expected Result**

- Only platform admins can reach the page; everyone else gets a 404.
- Platform-level ad management renders without errors.

**Future Improvement Suggestions**

- Add per-tenant targeting controls for partner ads.
- Show platform-wide ad performance roll-ups.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

## Section 5 — Attorney Workspace

### 33. Attorney workspace — Matters list

**Route / Location**

/transactions (as Attorney); the sidebar entry is 'Matters'

**How To Test**

- Sign in as an Attorney and open Matters from the sidebar (or /transactions). The page should automatically load the attorney layout, not the agent transactions list.
- Confirm the attorney KPI row at the top (for example Hard Stops, Release Ready, Active Matters, Needs Review).
- Use the filter tabs: All, Needs Review, Missing Docs, Ready To Release, Clean Files. Confirm the matter cards narrow as you switch.
- On a matter card, click Review to open that matter's full workspace (feature 33.1).
- Click the floating Ask AI button and confirm the AI panel opens.
- Click the '+ Upload Legal Packet' button (sidebar footer / top bar) and confirm the legal-packet upload flow opens.

**Expected Result**

- The attorney layout loads with the correct KPI row, tabs, and matter cards.
- Review opens the matter workspace; Upload Legal Packet opens the intake flow; Ask AI opens the AI panel.
- Releases, State Rules, and Recording Calendar are now their own sidebar pages (features 33.2–33.4) — they are no longer header buttons.

**Future Improvement Suggestions**

- Add a 'Sign off all in this packet' bulk action from the card.
- Let the attorney save a custom matter filter (for example 'closing this week, needs review').
- Show the responsible agent on each matter card.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 33.1. Attorney matter workspace (one matter in depth)

**Route / Location**

/transactions/<id> (as Attorney) — opens from Review on a matter card

**How To Test**

- Open a matter from the Matters list. Confirm a full-screen workspace with a header (property address, status, and a matter switcher to jump between matters) rather than a simple scrolling page.
- Use the left section rail to move between Overview, Review, Brief, Timeline, People, Activity, and Releases. Confirm each section loads its own content.
- On the Review section, work through the document review items. On the Releases section, confirm you can start a packet release.
- Use the matter switcher in the header to jump to a different matter without going back to the list.

**Expected Result**

- The matter opens as a focused workspace; each rail section shows real data for that matter.
- The matter switcher moves you between matters in place.

**Future Improvement Suggestions**

- Add keyboard shortcuts to move between rail sections.
- Add a one-click 'export this matter file as PDF' for the closing binder.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 33.2. Attorney Releases Queue

**Route / Location**

/attorney/releases (sidebar → Releases Queue)

**How To Test**

- Open Releases Queue from the sidebar. Confirm a list of matters that are ready to release and a history of recently released packets.
- On a ready matter, click the release action and confirm the Send Packet window opens with the recipients and documents pre-filled.
- Send a packet and confirm it moves into the released history with the date and recipients.

**Expected Result**

- Only matters that are actually ready to release appear in the ready list.
- Sending a packet records who it went to and when.

**Future Improvement Suggestions**

- Add a one-click 'release all ready matters' for a quiet end-of-day sweep.
- Let the attorney attach a short cover note to the released packet.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 33.3. Attorney State Rules

**Route / Location**

/attorney/state-rules (sidebar → State Rules)

**How To Test**

- Open State Rules from the sidebar.
- Confirm a clean reference document listing, per state, the closing type (attorney / title / escrow), the recording window, and whether same-day disbursement is allowed.
- Scroll through and confirm it reads as a reference page, not a dashboard.

**Expected Result**

- The page is a read-only reference of state recording / closing rules.
- Every state your matters touch is listed.

**Future Improvement Suggestions**

- Add a search box to jump to a state quickly.
- Link each state to the matters currently in that state.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 33.4. Attorney Recording Calendar

**Route / Location**

/attorney/recording-calendar (sidebar → Recording Calendar)

**How To Test**

- Open Recording Calendar from the sidebar.
- Confirm a month grid with recording deadlines / closings marked on their dates.
- Move between months with the arrows.
- Click Print and confirm a printable calendar opens.

**Expected Result**

- The calendar shows the matters' recording deadlines on the right dates.
- Month navigation and Print both work.

**Future Improvement Suggestions**

- Let the attorney click a day to see every matter due that day.
- Add an agenda (list) view alongside the month grid.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

## Section 6 — Client, FSBO & Vendor Portals

### 34. Client workspace — Home (closing concierge)

**Route / Location**

/client/home (Client sign-in lands here)

**How To Test**

- Sign in as a Client (a buyer or seller invited to a transaction). You should land on a warm 'closing concierge' Home with its own navy sidebar — not the staff app layout.
- Confirm the Home shows where your deal stands, what is coming next, your key dates, and a short list of documents and your agent.
- Use the 'Ask Velvet' / 'Ask your agent' box to send a message, and confirm it posts to a real two-way thread.
- Confirm the left sidebar shows: Home, Next Steps, Timeline, Documents, Updates. (Your Payments and Agent Info pages are reachable from links on the Home cards.)
- Open Next Steps (your action items and key dates) and Updates (recent updates plus the message thread with your agent) and confirm each loads with real content.
- If you are a brand-new client with no transaction yet, confirm a friendly empty Home appears instead of fake sample data.

**Expected Result**

- Clients get their own concierge workspace, not the internal staff layout.
- Every number and date is real; an empty account shows an honest empty state.
- The Ask box reaches the agent and shows replies.

**Future Improvement Suggestions**

- Add a single 'what should I do next' banner at the very top.
- Let the client switch between several of their transactions from the Home header.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 34.1. Client workspace — Timeline

**Route / Location**

/client/milestones (sidebar → Timeline)

**How To Test**

- Open Timeline from the client sidebar. Confirm one card per transaction summarising where the deal stands and the closing date.
- Tap a transaction card and confirm it opens that deal's full step-by-step timeline.

**Expected Result**

- Clients with more than one deal see a calm card per deal; each opens its own detailed timeline.
- Every step and date is driven by the real transaction, not a template.

**Future Improvement Suggestions**

- Add an estimated date next to upcoming steps.
- Let the client turn on email alerts when a step completes.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 34.2. Client workspace — Documents

**Route / Location**

/client/documents (sidebar → Documents)

**How To Test**

- Open Documents from the client sidebar. Confirm it leads with anything waiting on you, then a real status summary, then your document list.
- Click the upload action, pick the transaction and document type, and upload a file. Confirm it appears in the list.
- On a document, use Flag for deletion, give a reason, and confirm a 'Flagged' badge appears (this routes to the agent's Deletion Queue — feature 27.11).

**Expected Result**

- The client sees a real document list and status summary, never a hardcoded zero board.
- Upload and flag-for-deletion both work and the agent is notified of flags.

**Future Improvement Suggestions**

- Add an inline preview so the client can re-read a document before flagging.
- Show which transaction each document belongs to when the client has several deals.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 34.3. Client / FSBO workspace — Payments (invoices)

**Route / Location**

/client/invoices (Client and FSBO sidebar → Payments)

**How To Test**

- Sign in as a Client or FSBO Customer and open Payments from the sidebar.
- Confirm a list of invoices on your transactions with their amount, status, and due date.
- Open an invoice and confirm you can pay it securely (Stripe). After paying in test mode, confirm the status updates to Paid.

**Expected Result**

- Clients and FSBO customers see only their own invoices.
- Paying an invoice updates its status and records the payment.

**Future Improvement Suggestions**

- Email a receipt automatically after payment.
- Let the payer save a card for future invoices.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 34.4. Client workspace — Agent Info (your team)

**Route / Location**

/client/agent (sidebar → Agent Info)

**How To Test**

- Open Agent Info from the client sidebar.
- Confirm your agent's details and the deal's key contacts (loan officer, title, etc.) with one-tap call and email.
- Confirm the agent's short bio appears (this is the bio the agent set in their Account → Profile).

**Expected Result**

- The page shows the real agent and key contacts for the deal, read-only.
- Call and email shortcuts work on a phone.

**Future Improvement Suggestions**

- Add the agent's photo and office hours.
- Add a one-tap 'message my agent' that opens the Ask thread.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 35. FSBO workspace — Overview & sidebar

**Route / Location**

/fsbo (FSBO Customer sign-in lands here)

**How To Test**

- Sign in as an FSBO Customer. Confirm you land on an Overview dashboard with KPI tiles (for example My Properties, Missing Docs, Share Links Live, Days To Close) and a floating Ask AI button.
- Confirm the sidebar shows: Dashboard, My Properties, Documents, Payments, Messages.
- Confirm the sidebar footer has a 'Share milestones' button.
- Click through each sidebar item and confirm every page loads (none should be a 'Coming Soon' placeholder).

**Expected Result**

- The FSBO Overview shows real numbers or clean empty states.
- Every FSBO sidebar destination is a working page.
- Share milestones opens the share-link manager.

**Future Improvement Suggestions**

- Simplify the home screen further for less technical sellers.
- Add a guided 'first week as a FSBO seller' checklist.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 35.1. FSBO workspace — My Properties (and property detail)

**Route / Location**

/fsbo/properties (sidebar → My Properties)

**How To Test**

- Open My Properties. Confirm one card per home with its status, closing date, outstanding-document count, and unread-message count.
- Open a property card and confirm its workspace opens (milestones, documents, and messages for that one home).
- From a property, use the 'Manage' / share action and confirm the share-link manager opens.

**Expected Result**

- Every property the seller owns appears as a scannable card.
- Opening a property shows that home's full workspace.

**Future Improvement Suggestions**

- Add a filter strip (active / closing soon / closed) above the property cards.
- Show the next action needed on each property card.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 35.2. FSBO workspace — Documents

**Route / Location**

/fsbo/documents (sidebar → Documents)

**How To Test**

- Open Documents. Confirm a count badge and a filter-tab strip (All / Missing / In progress / Uploaded / Verified / Complete) over one combined list across all your properties.
- Each row should show the document, its status, and a tag for which property it belongs to.
- On a missing requirement, click Upload — confirm the upload window opens with that property pre-selected.
- On a document, use Flag for deletion and confirm a reason is required and the row updates.

**Expected Result**

- All documents across every property show in one place, filterable by status.
- Upload and flag-for-deletion both work.

**Future Improvement Suggestions**

- Add a 'download everything for this property' button.
- Auto-detect the document type from the uploaded file.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 35.3. FSBO workspace — Messages

**Route / Location**

/fsbo/milestones (sidebar → Messages)

**How To Test**

- Open Messages. Confirm a single inbox of everything your coordinator has sent you, across all properties.
- Confirm each message is tagged with the property it belongs to.
- Use the filter-tab strip to narrow the list.

**Expected Result**

- One unified message inbox across every property.
- Each message clearly shows which property it relates to.

**Future Improvement Suggestions**

- Let the seller reply to a coordinator message directly from this inbox.
- Add unread / read filters.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 36. Vendor portal — Document requests and uploads

**Route / Location**

/portal/vendor (Vendor sign-in lands here)

**How To Test**

- Sign in as a Vendor. Confirm a focused portal showing the documents requested from you and an upload area — not the staff app.
- Upload a requested document and confirm it is accepted and shows in your uploads.
- Switch to the My Uploads view (sidebar) and confirm your previously uploaded files are listed.
- Confirm the portal only ever shows your own requests and uploads — no transaction details you should not see.

**Expected Result**

- Vendors see only their own document requests and uploads.
- Upload works and the file reaches the right transaction for the agent.

**Future Improvement Suggestions**

- Let a vendor reply to a request with a short note alongside the file.
- Show the due date for each requested document.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

## Section 7 — Public Links (No Sign-In)

### 37. Public milestone viewer

**Route / Location**

/milestones/<share token> (opened from a share link an agent or seller sent)

**How To Test**

- Open a milestone share link in a browser where you are signed out (or a private window).
- Confirm a clean, read-only progress page showing the property address and the milestone steps with their status — branded with the sharing brokerage's name and color.
- Confirm there is no sign-in prompt and no private contact or financial detail.
- Open a made-up / expired token and confirm a clear 'link not available' message rather than a broken page.

**Expected Result**

- Anyone with the link sees the milestone progress without signing in.
- The page is read-only and never leaks private details.
- An invalid or expired link shows a clean message.

**Future Improvement Suggestions**

- Show an estimated closing date on the viewer.
- Let the viewer subscribe to email updates when a step completes.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 38. Public invoice payment link

**Route / Location**

/pay/invoices/<invoice id> (opened from an invoice email)

**How To Test**

- Open a public invoice pay link while signed out.
- Confirm the page shows the amount, who it is for, the property, and the due date, with a secure 'Pay' button (Stripe).
- Pay in test mode and confirm you are taken to a 'payment complete' confirmation page.
- Open the link again after paying and confirm it shows the invoice is already paid rather than charging twice.

**Expected Result**

- A payer with no account can pay an invoice securely from the link.
- After payment a clear confirmation page appears and the invoice is marked paid.

**Future Improvement Suggestions**

- Offer a downloadable PDF receipt on the confirmation page.
- Support partial / installment payments.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 39. Advertise storefront

**Route / Location**

/advertise (public marketing + checkout)

**How To Test**

- Open /advertise while signed out. Confirm a marketing landing page explaining advertising on Velvet Elves with a clear call to action.
- Start the checkout flow and confirm it walks you through choosing a placement and paying.
- Complete a test checkout and confirm a completion / confirmation page appears.

**Expected Result**

- The storefront is reachable with no sign-in and explains the offer clearly.
- Checkout and completion both work end to end in test mode.

**Future Improvement Suggestions**

- Show live example placements so advertisers see what they are buying.
- Add package tiers (week / month / quarter) with clear pricing.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

## Section 8 — Direct Links and Error Pages

### 40. Unauthorized page

**Route / Location**

/unauthorized (or any blocked page)

**How To Test**

- Sign in as a basic Agent and open one of these URLs directly:
  - /team
  - /admin/task-templates
  - /admin/users/some-id

**Expected Result**

- The app redirects you to /unauthorized.
- A clear 'Access denied' screen appears.

**Future Improvement Suggestions**

- Add a 'Request access from your admin' button that emails the tenant admin.
- Explain in plain language which role is needed to open the page.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 41. Not Found (404) page

**Route / Location**

Any unknown URL, for example /this-does-not-exist

**How To Test**

- Type an invalid URL in the browser address bar and press Enter.

**Expected Result**

- A 404 page appears with a Back to Dashboard button.

**Future Improvement Suggestions**

- Add a small search bar on the 404 page that suggests the likely intended page based on the URL.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

## Overall Feedback

### Biggest usability wins you noticed

> 
> 
> 

### Biggest friction points you noticed

> 
> 
> 

### Features you would like prioritized next

> 
> 
> 

### Additional requests or general notes

> 
> 
> 
