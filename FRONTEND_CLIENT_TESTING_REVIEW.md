# Velvet Elves — Frontend Client Testing Review

## Features Currently Complete — Client Feedback Requested

**Last Updated:** May 13, 2026  
**Test Environment:** http://dev.velvetelves.com/  
**Recommended Browsers:** Chrome or Edge (please allow pop-ups and downloads)  
**Reviewer:** Client — please fill in the Feedback block under each feature

---

## How To Use This Document

### What is in this document

- This document lists every frontend feature that is currently complete and needs your review.
- Each feature includes the page address, the exact steps to test, the expected result, our ideas for future improvements, and a blank Feedback area for your notes.
- Features that are still being built (for example placeholder 'Coming Soon' pages) are intentionally left out of this review.

### How to fill in the Feedback area

- **Status** — write Pass, Fail, or Needs Work after you try the feature.
- **Comments** — anything you noticed: confusing text, slow actions, wrong results, missing fields, visual issues.
- **Improvement priority** — for the ideas listed under 'Future Improvement Suggestions', please mark each as High, Medium, Low, or Skip.

### Accounts you will need

- **Agent or Elf** — covers the main day-to-day workflow.
- **Team Lead or Admin** — needed to see the Delete button on transactions, the admin-only Task Templates pages, the Deletion Queue on the Documents page, and the full Team Members admin page.
- **Workspace Owner** — the very first person who registered the brokerage. Required for the Transfer ownership flow and the Settings → Danger Zone (schedule deletion).
- **Invited member** — sign up by clicking an invite-email link (instead of /register). Required for the invite-accept flow and the invitee branch of the onboarding wizard.
- **Attorney** — loads the attorney-specific workspace at /transactions.
- **FSBO Customer** — verifies the FSBO sidebar layout.
- **Platform admin** (internal Velvet Elves staff only) — required for the /platform/tenants pages.

### Suggested order of testing

1. Public pages and sign-in / sign-up (including the new Organization field on /register)
2. Invite-accept flow (open an invite link as a brand-new user)
3. Onboarding wizard (test both founder and invitee branches) and the product tour overlay
4. Standard Agent or Elf workflow (dashboard, new transaction, transactions list, documents)
5. Settings and Email Integrations (needed before AI Email Review can send)
6. AI Email Review queue at /ai-emails
7. Team Lead or Admin extras — Team Overview, Team Members admin, invite teammate, ownership transfer, deactivate, Company Details, Danger Zone, plus task templates and deletion queue
8. Attorney workspace
9. FSBO-customer sidebar
10. Platform admin pages (internal Velvet Elves staff only)
11. Direct links and error pages

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
- Gmail / Outlook / DocuSign connections persist into Settings → Integrations after onboarding.
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
- If you already finished the tour, open Settings → Help & Tour → Start tour to replay it.
- Step through the whole tour using Next / Back / Skip. Internal roles (Agent, Transaction Coordinator, Team Lead, Admin) see a 9-step tour covering sidebar KPIs, Active Transactions, My Task Queue, All Documents, AI Briefing, search, notifications, and the New Transaction button.
- Sign in as an Attorney and replay the tour — it should be a 5-step tour focused on the matter queue, documents, and AI briefing.
- Sign in as a Client, FSBO Customer, or Vendor and replay the tour — it should be a 5-step tour focused on My Properties, Documents, and Ask Velvet Elves AI.
- Use the keyboard: → or Enter to advance, ← to go back, Esc to skip. Confirm Cmd+K / Ctrl+K still opens global search mid-tour.
- Skip the tour mid-way and confirm it does not mark complete (Settings → Help & Tour → Start tour starts it again from the beginning).
- Finish the tour on the final step and confirm it does not auto-start the next time you log in.

**Expected Result**

- The tour highlights the right element for each step and the tooltip stays on screen.
- Internal roles see a 9-step tour; Attorney and external roles see 5-step role-appropriate tours.
- Skipping does not lock the tour; only Finish marks it complete.
- Settings → Help & Tour always replays the tour for the role you are signed in as.

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

### 14. Dashboard home

**Route / Location**

/dashboard

**How To Test**

- Open the dashboard and check each card.
  - A personalized greeting is visible.
  - 'My week' pills show tasks, overdue, completed, and active counts.
  - 'My Tasks' card has Upcoming and Overdue tabs.
  - 'My Deadlines' card has Upcoming and Overdue tabs.
  - 'Upcoming Closings' shows cards or a clean empty state.
- Click the New Transaction button.

**Expected Result**

- Every card shows real data or a clean empty state — nothing blank or broken.
- The New Transaction button opens the transaction wizard.

**Future Improvement Suggestions**

- Let the user reorder or hide cards to personalize their landing page.
- Add an 'AI summary of my day' card at the top.
- Show a small comparison like 'this week vs last week' on the My Week pills.

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
  - Navigation items change depending on the signed-in role.
  - KPI tiles in the sidebar show numbers such as overdue tasks, closings this week, etc.
- Check the top bar.
  - Click 'Today's AI Briefing' — a side panel should open.
  - Click any status chip (Critical / Needs Attention / On Track) — it should filter the transactions list.
  - Open the avatar menu — confirm My Profile, Settings, and Log Out.
  - On a narrow browser window, click the mobile menu icon.
- Please note the current state of two items:
  - The search field in the top bar is visual only right now and does not run a real search.
  - The bell icon in the top bar is visual only right now and does not open notifications.

**Expected Result**

- Sidebar navigation and KPIs adjust correctly to the user's role.
- The AI Briefing panel opens and closes cleanly.
- Status chips take you to the correct filtered transaction view.
- The user menu and mobile menu both behave correctly.

**Future Improvement Suggestions**

- Turn the top-bar search into a live global search across deals, tasks, and documents.
- Wire the bell icon to real notifications with unread counts.
- Add a sidebar collapse toggle for users on smaller laptops.

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

Opens from an expanded transaction card

**How To Test**

- Open the Documents window.
  - Confirm the list of existing documents appears.
  - Expand Details on a document and read the metadata.
- Click Download on a document.
- Click Add Document and upload a new file.

**Expected Result**

- The download link opens the document.
- The uploaded file appears in the list, with version and last-updated info.

**Future Improvement Suggestions**

- Let the user rename a document without leaving the page.
- Suggest the document type automatically when uploading (Contract, Addendum, etc.).
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
- Click Upload on a missing-document row. Confirm the Upload Document modal opens with the transaction and document type already filled in.
- Click Generate (Template) on a missing item that supports template generation. Confirm a draft document is created and the preview opens.
- Click Approve on a Pending Review row. Confirm the row leaves the queue and appears in the Cleared Today strip.
- Click Mark N/A on any row. Confirm a confirmation appears, the row disappears, and an Undo toast restores it if clicked.
- Click Flag on any row. Confirm a flag icon appears next to the item and is still there after refresh.
- Click Call on a row with a phone number — confirm your phone app opens and the activity is logged on the transaction.
- Click Forward on a signed document. Confirm a forward-style email modal opens with the document attached.

**Expected Result**

- Every action button does something real (sends an email, opens the right modal, or updates the queue).
- Request, Nudge, Call, and Forward keep the row visible with a 'last touched' note until the requirement is actually resolved.
- Mark N/A, Approve, Upload, and Generate clear the row and add it to the Cleared Today strip at the bottom of the page.

**Future Improvement Suggestions**

- Show 'Next follow-up due in N hours' on touched rows so the user knows when to nudge again.
- Bulk-select rows for batch Request or Mark N/A.

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

/documents (strip at the bottom of the AI Priority list)

**How To Test**

- Mark a few items resolved (Approve, Mark N/A, Upload, sign, or generate) and confirm each one appears in the Cleared Today strip.
- Click a card in the strip that points to a real document and confirm the preview opens.
- Click a card for a Mark N/A item and confirm the priority detail / audit view opens (not a dead preview).

**Expected Result**

- Only items that were truly resolved today show up in the strip. Requests, nudges, calls, and forwards do not appear here.
- Each card opens the most useful detail for that item.

**Future Improvement Suggestions**

- Add a one-click Undo on each card for accidental clears.
- Let the user filter the strip by who cleared the item (self vs. teammate).

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

Eye icon on any document row

**How To Test**

- Click the Preview (eye) icon on a PDF or image — the document should render inline.
- Click Preview on a non-previewable file (for example a .docx) — the modal should offer a Download button instead.
- Click the Download icon directly on the row, without opening Preview first.
- From inside the Preview modal, click Send for Signature.

**Expected Result**

- PDFs and images preview in the modal; everything else prompts a download.
- Download always saves the file.
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

### 27.9. All Documents — Email Document, Rename, Version History

**Route / Location**

Three-dot menu on any document row (internal roles only)

**How To Test**

- Open the three-dot menu and click Email Document. Add at least one recipient and click Send Email. Confirm a toast reports the email is queued.
- Click Rename / Reclassify. Try to save with an empty file name and confirm it is blocked. Change the file name, label, or type and click Save.
- Click Version History. Confirm every version is listed with v1, v2, … and that downloading any historical version still works. Upload a replacement and confirm the latest version is marked Current.

**Expected Result**

- Email Document queues the email and records it in the transaction's communication history.
- Rename / Reclassify updates the document immediately after save.
- Uploading a new version moves the previous one to Legacy.

**Future Improvement Suggestions**

- Offer saved email templates ('Client intro', 'Title hand-off', etc.).
- Allow rolling a Legacy version back to Current.
- Use AI to suggest the right document type during Rename / Reclassify.

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
- Confirm a confirmation dialog appears explaining the document will be soft-deleted but can be restored.
- Click Archive and confirm the document disappears from the list and a toast confirms.

**Expected Result**

- Archiving requires a confirmation step.
- After archive, the document leaves the list and is no longer counted in the tabs.

**Future Improvement Suggestions**

- Add a 'Restore archived' area for admins to undo accidental archives.
- Show an Undo toast right after archive so a single click can reverse it.

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

- Sign in as Team Lead, Admin, or any other internal role and click Deletion Queue in the page header.
- Review each pending request — confirm you can see the document name, the reason given by the requester, and an optional decision-notes field.
- Approve one request and confirm a toast reports the document is archived.
- Reject another request and confirm the toast reports the document stays active.

**Expected Result**

- Every flagged request from a client / FSBO / vendor appears here for an internal reviewer.
- Approve archives the document. Reject leaves it in place.
- Both decisions are recorded for audit.

**Future Improvement Suggestions**

- Email the original requester automatically when a decision is made.
- Add bulk approve / bulk reject for high-volume cleanup.

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

### 28. My Profile page

**Route / Location**

/profile

**How To Test**

- Open /profile from the user menu.
  - Confirm the summary card (initials, role, status, email, created date).
- Edit your name or phone number, then click Save Changes.

**Expected Result**

- A success toast appears and the profile card reflects the update.

**Future Improvement Suggestions**

- Allow avatar photo upload.
- Add a change-password form on this page.
- Add a notification-preferences section (email, in-app, daily digest).

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29. Settings page — overview and layout

**Route / Location**

/settings

**How To Test**

- Open /settings and confirm it is a single scrolling page divided into seven sections: Company, Email Integrations, E-Signature, Branding, AI Configuration, Task Templates, Help & Tour.
- Confirm four Snapshot tiles at the top (Inbox, E-Sign, Credits, Templates) and a 'Sections' nav on the side.
- Click each Snapshot tile in turn — the page should jump to the matching section.
- Click each item in the Sections nav and confirm the page jumps to that section.
- Scroll slowly and confirm the Sections nav highlight follows the active section.
- Confirm the Inbox tile's 'connected/total' number matches what the Email Integrations section shows below.
- Each individual section is tested in 29.1–29.6.

**Expected Result**

- Snapshot tiles and the Sections nav both jump to the right section.
- Every signed-in role can open /settings (individual sections have their own gating).

**Future Improvement Suggestions**

- Role-gate Branding, Task Templates, and AI Configuration so non-admin users cannot see them.
- Persist the last-visited section so that returning to /settings scrolls to where the user left off.
- Add a 'What's new in Settings' callout when major sections change between releases.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.1. Settings — Email Integrations (Gmail and Outlook)

**Route / Location**

/settings (Email Integrations section)

**How To Test**

- Open Settings and scroll to Email Integrations. Confirm a Gmail row and an Outlook row are visible (iCloud is intentionally not shown yet).
- Click Connect on the Gmail row. Complete sign-in in the Google popup that opens. After approval the row should switch to Connected with your email and the date.
- Repeat on the Outlook row using a Microsoft 365 account.
- Cancel the popup mid-way and confirm the row stays in the 'Connect' state without an error.
- Click Disconnect on a connected row. Confirm a warning appears explaining inbound sync and AI email automation will stop.
- Cancel the warning — the row should remain connected. Confirm it — the row should return to Connect.
- Click Refresh on the section to re-fetch the integration list.

**Expected Result**

- Both providers connect through their official sign-in popup — no password is typed into Velvet Elves.
- Disconnect always asks for confirmation first.
- At least one provider must be connected for AI Email Review (29.7+) to send replies.

**Future Improvement Suggestions**

- Show a 'Last synced' timestamp and a manual 'Sync now' button per provider.
- Re-enable the iCloud row once the Apple app-specific-password flow is reviewed.
- Show a small indicator on the row when the linked mailbox has unread AI drafts waiting in /ai-emails.
- Detect popup-blocked browsers and offer a redirect-based fallback path.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.2. Settings — E-Signature (DocuSign)

**Route / Location**

/settings (E-Signature section)

**How To Test**

- Open Settings → E-Signature.
- If DocuSign is not yet connected, click Connect. Complete the 3-step wizard (Intro → DocuSign popup → Done).
- After connecting, confirm the section shows your DocuSign account email and the date you connected.
- Click Disconnect, read the warning that future Send-for-Signature attempts will fail, and confirm.

**Expected Result**

- Connect and Disconnect both work without leaving the Settings page.
- Once connected, the same account is also shown inside the Send for Signature modal on /documents.

**Future Improvement Suggestions**

- Add support for additional providers (DotLoop, Authentisign, Adobe Sign) alongside DocuSign in this section.
- Show the monthly envelope count remaining so users do not hit their DocuSign quota by surprise.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.3. Settings — Branding (placeholder — not wired yet)

**Route / Location**

/settings (Branding section)

**How To Test**

- Open Settings → Branding. Confirm a logo upload, a primary colour field, and a display name field are visible.
- Try changing each field and click Save branding.
- Refresh the page — the fields should reset to the defaults.

**Expected Result**

- The Branding section is currently a placeholder; nothing persists after refresh.
- Please flag clearly if any client expects this section to be live so we can prioritise wiring it up.

**Future Improvement Suggestions**

- Wire all three Branding fields to the tenant settings backend.
- Show a live preview of the sidebar and a sample email so the user can see the changes before saving.
- Add a tenant-wide 'Reset to Velvet Elves defaults' button.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.4. Settings — AI Configuration (placeholder toggles)

**Route / Location**

/settings (AI Configuration section)

**How To Test**

- Open Settings → AI Configuration.
- Confirm an 'AI Credits' line and three toggles: Auto-parse uploaded documents, Task recommendations, and Smart email drafts.
- Flip each toggle and refresh — the toggle should reset (settings do not persist yet).
- Click Upgrade plan and confirm nothing happens (placeholder button).

**Expected Result**

- Toggles flip on screen but do not persist on refresh.
- The AI Credits numbers shown today are placeholders and do not reflect real usage — please flag if a stakeholder expects them to.

**Future Improvement Suggestions**

- Wire each toggle to the tenant AI settings (tone, disclaimer, escalation hours, auto-send threshold) so admins can actually configure AI behaviour.
- Replace the placeholder credit count with a real meter pulled from the AI usage backend.
- Add a 'Smart email drafts' explainer link that opens a preview of the AI Email Review queue.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.5. Settings — Task Templates (placeholder list)

**Route / Location**

/settings (Task Templates section)

**How To Test**

- Open Settings → Task Templates. Confirm a placeholder list of five templates: Buyer Standard, Seller Standard, Dual Agency, Lease, and Commercial.
- Click Edit on any row — nothing should happen (placeholder).
- Click Import in the section header — nothing should happen (placeholder).

**Expected Result**

- Neither Edit nor Import is wired on this section.
- Real template management lives at /admin/task-templates (features 30 and 31).

**Future Improvement Suggestions**

- Replace this placeholder with a live mini-list pulled from the Task Templates backend.
- Or remove this section from Settings and link directly to /admin/task-templates instead.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 29.6. Settings — Help & Tour (replay the product tour)

**Route / Location**

/settings (Help & Tour section)

**How To Test**

- Open Settings → Help & Tour and click Start tour.
- Confirm the product tour starts immediately for whatever role you are signed in as.
- Try it for each role (Agent, Transaction Coordinator, Team Lead, Admin, Attorney, Client, FSBO Customer, Vendor) — the tour content should match the role (see feature 13 for what is expected).

**Expected Result**

- Start tour always launches the product tour for the signed-in role, even if you have already finished it.
- This is the only fully-wired control among AI Configuration, Branding, Templates, and Help — please test it for every role.

**Future Improvement Suggestions**

- Add a 'What's new in this release' card next to Replay tour so users can re-run a tour focused on recent changes only.
- Add a per-feature mini-tour launcher (e.g. 'Replay Documents tour only').
- Show a small completion timestamp ('Last completed Apr 28, 2026') so users know whether they've already seen the latest version.

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
- Disconnect your email provider in Settings, then click Approve & Send on a draft. Confirm a clear error explains that no email provider is connected.
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

### 32.7. Settings — Company Details (organization name)

**Route / Location**

/settings (Company section, at the top of the page)

**How To Test**

- As an Admin, open /settings and confirm the Organization Name field is editable with a Save button.
- Sign in as any non-Admin (Team Lead, Agent, Transaction Coordinator, Attorney, Client, FSBO Customer, Vendor) and confirm the field is read-only with a note that only an Admin can change it.
- As an Admin, type a new name and click Save. Confirm the change is persisted.
- Sign in as another member of the same workspace and confirm they see the new name without needing to refresh again.
- As an Admin, leave the field empty and click Save — confirm the page shows a clear error rather than saving an empty name.

**Expected Result**

- Admins can change the organization name; everyone else sees a read-only field with a clear explanation.
- The new name shows up for every member of the brokerage on the next page load.
- Errors appear inline; the page never breaks silently.

**Future Improvement Suggestions**

- Show a small preview of how the organization name will appear in the sidebar, the invitation email, and outbound transaction emails before saving.
- Add a 'Tenant slug' field so admins can claim a unique subdomain (for example acme.velvetelves.com).
- Show the workspace owner's name and email on this card so members know who to ask for changes.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 32.8. Settings — Danger Zone (schedule / cancel deletion)

**Route / Location**

/settings (Danger Zone section at the bottom — workspace owner only)

**How To Test**

- Sign in as the workspace owner and scroll to the bottom of /settings. Confirm a Danger Zone section is visible.
- Sign in as any other role on the same workspace and confirm the section is not visible at all.
- As the owner, click Delete organization. Confirm the page asks you to type the workspace name exactly before Schedule deletion becomes available.
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
- Add a Schedule deletion action on the row alongside Suspend (currently only available inside the tenant's own Settings → Danger Zone).
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

## Section 5 — Role-Specific Workspaces

### 33. Attorney workspace

**Route / Location**

/transactions (as Attorney)

**How To Test**

- Sign in as an Attorney and open /transactions.
  - The page should automatically switch to the attorney layout.
- Check the header.
  - The attorney-specific title and KPI row are visible.
- Use the filter tabs.
  - All, Needs Review, Missing Docs, Ready To Release, Clean Files.
- Confirm the matter cards render.
- Click the floating Ask AI button.
- Please note the current state of three header buttons:
  - Open review queue — visual only right now.
  - State rules — visual only right now.
  - Upload legal packet — visual only right now.

**Expected Result**

- The attorney layout loads with the correct tabs and matter cards.
- The Ask AI panel opens correctly.

**Future Improvement Suggestions**

- Wire the three header buttons (Open review queue, State rules, Upload legal packet).
- Add a quick-reference modal for state recording rules.
- Add a 'Sign off all in this packet' bulk action.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 34. FSBO customer sidebar

**Route / Location**

Sidebar (as FSBO Customer)

**How To Test**

- Sign in as an FSBO Customer.
  - Confirm the sidebar shows: My Properties, Documents, Milestones & Messages, Ask Velvet Elves AI, Notifications, Sharing.
- Confirm Dashboard, Transactions, and Documents pages still load cleanly.
- Please note which sidebar items are intentional placeholders today:
  - Milestones & Messages, Notifications, and Sharing are 'Coming Soon' pages for now.

**Expected Result**

- FSBO sidebar items render correctly.
- Dashboard, Transactions, and Documents are reachable and working.

**Future Improvement Suggestions**

- Replace the placeholder pages with the FSBO milestone viewer and sharing-link manager planned for Phase 5.
- Simplify the home screen for FSBO customers who are less technical.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

## Section 6 — Direct Links and Error Pages

### 35. Unauthorized page

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

### 36. Not Found (404) page

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
