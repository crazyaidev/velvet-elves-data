# Velvet Elves — Frontend Client Testing Review

## Features Currently Complete — Client Feedback Requested

**Last Updated:** April 15, 2026  
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
- **Team Lead or Admin** — needed to see the Delete button on transactions, the admin-only Task Templates pages, and the Deletion Queue on the Documents page.
- **Attorney** — loads the attorney-specific workspace at /transactions.
- **FSBO Customer** — verifies the FSBO sidebar layout.
- **Admin with a known user ID** — needed only for the direct user-detail link at /admin/users/<userId>.

### Suggested order of testing

1. Public pages and sign-in / sign-up
2. Onboarding and the first-time tutorial
3. Standard Agent or Elf workflow (dashboard, new transaction, transactions list, documents)
4. Team Lead or Admin extras (delete permission, task templates, deletion queue)
5. Attorney workspace
6. FSBO-customer sidebar
7. Direct links and error pages

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

- Check that every field is visible.
  - Full name, Email, Password, Confirm Password, Phone (optional), Role, and the Terms / Privacy checkbox.
  - A Google sign-up button at the top of the form.
- Try invalid inputs and make sure the page stops you.
  - An invalid email address (for example 'abc' with no @).
  - A weak password — confirm the password-strength hints appear.
  - Mismatched Password and Confirm Password.
  - Leaving the Terms / Privacy box unchecked.
- Submit a valid registration using a real email you can check.

**Expected Result**

- Each invalid case shows a clear inline message next to the field.
- After a successful submission, one of two things should happen.
  - You are signed in automatically and taken to the /onboarding page.
  - Or you are taken to /login with a message asking you to confirm your email.

**Future Improvement Suggestions**

- Check email availability while typing (instead of only after submit).
- Add an eye icon that shows / hides the password while typing.
- Show a short sentence under each Role to explain what that role can do.

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

- Open the invite URL.
  - Confirm the page shows the invited email and the invited role.
  - Confirm the form fields for Full Name, Password, and optional Phone.
- Submit the form with valid values.
- Separately, open an invite URL with an invalid token.

**Expected Result**

- A valid invite signs the new user in and takes them to /onboarding.
- An invalid token shows an 'Invalid Invitation' screen with a link back to login.

**Future Improvement Suggestions**

- Show a countdown for how long the invite is still valid.
- Let the person who sent the invite resend or cancel it from the admin area when that page is built.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

## Section 2 — First-Time User Experience

### 12. Onboarding wizard

**Route / Location**

/onboarding

**How To Test**

- Step 1 — Welcome.
  - Read the welcome copy and check the progress indicator.
  - Click Next.
- Step 2 — Role & Company.
  - Change the Role dropdown.
  - Enter a company name.
  - Upload a company logo and confirm the preview appears.
  - Also test the Skip button on this step.
- Step 3 — Integrations.
  - Confirm the Gmail Connect button is shown.
  - Click Connect (if Gmail is configured, confirm the connected state).
  - Also test the Skip button.
- Step 4 — First Transaction.
  - Drag and drop a test PDF or use Browse Files.
  - Confirm the uploaded file name appears.
  - Also test the Skip button.
- Step 5 — All Set.
  - Verify the final success screen.
  - Click Go to Dashboard.

**Expected Result**

- Each step shows the correct fields and text.
- Skip behaves as expected on every step.
- Clicking Go to Dashboard at the end takes you to /dashboard.

**Future Improvement Suggestions**

- Add a 'Save and finish later' option so users can leave and return.
- Show a named progress bar at the top (Welcome → Role → Integrations → Transaction → Done).
- Preview the uploaded logo at the exact size it will appear in the app's sidebar.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 13. First-time tutorial overlay

**Route / Location**

/dashboard (first visit)

**How To Test**

- On the first dashboard visit, an overlay should appear automatically.
  - Click Next through all steps.
  - Click Back to verify you can go back.
  - Click Skip to verify it closes the overlay.
- On the last step, click Get Started.
- To test again: clear the browser storage key 'velvet_elves_tutorial_completed' and reload.

**Expected Result**

- The overlay closes after Skip or Get Started.
- The overlay does not reappear automatically on the next visit.

**Future Improvement Suggestions**

- Create role-specific tutorials (different tips for Agents, Team Leads, and Attorneys).
- Add a 'Replay tutorial' button inside the user menu so clients can rewatch it any time.

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
- Any dates that are overdue are visually marked (for example in red).

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

### 27. All Documents page — overview, access, and deep-link entry

**Route / Location**

/documents

**How To Test**

- Open /documents and check the header.
  - The page title reads 'All Documents' (with a small 'Workflow > All Documents' breadcrumb on wide screens).
  - Next to the title, an orange count pill shows '{N} files'. When there is at least one missing required document it extends to '{N} files / {N} missing'.
  - While the document list is fetching, the count pill is replaced by a smaller pill that reads 'Loading' with a spinner.
- Check the top-right header buttons.
  - 'Upload Document' (or just 'Upload' on a narrow screen) is always visible.
  - 'Send for Signature' is visible. The text label collapses to a pen icon on narrow screens.
  - 'Deletion Queue' is visible only when you are signed in as an internal role (Agent, Transaction Coordinator, Team Lead, Attorney, or Admin). The text label collapses to a flag icon on narrow screens.
- Check the underline-style filter tabs directly below the title row.
  - Tabs: All, Signed, Pending Review, Sent for Sig., Missing — each shows a count badge.
  - The active tab is highlighted with an orange underline and orange text.
  - The 'Missing' badge turns red when the count is greater than zero.
- Try opening /documents as a non-internal role (for example as a For-Sale-By-Owner Customer if that account is available).
  - You should be redirected to /dashboard instead of seeing the page.
  - Note: as a result, the 'Flag for Deletion' path no longer applies on this page — non-internal flagging now happens only inside a transaction's documents tab.
- Confirm the page loads every document, not just the most recent 100.
  - If your tenant has more than 100 documents, scroll down or use the search box to find an older one — it should still appear (the page paginates through every page on load).
- Test the Cmd/Ctrl+K global search deep-link entry.
  - Press Cmd+K (Mac) or Ctrl+K (Windows) anywhere in the app to open the global search palette.
  - Search for a document by name and press Enter on the matching result.
  - /documents opens with the matching transaction's drawer expanded, the matching row scrolled into view, and a brief amber flash animation on that row.
  - Confirm the 'focus' and 'tx' query parameters are stripped from the URL afterwards (so a refresh does not re-flash forever).
  - If the document was deleted or filtered out, a toast appears: 'Document not found in the current view'.
- Force the empty state.
  - Apply filters that return no results — confirm 'No documents match this filter' with a 'Clear filters' button.
- Force the error state.
  - Briefly turn off your internet and reload — the page should show 'Failed to load documents' with a 'Retry' button.

**Expected Result**

- The title, count pill, filter tabs, and header buttons all render correctly for the signed-in role and screen size.
- Client / non-internal users cannot reach this page.
- Cmd+K deep-links open the right transaction, scroll to the matching row, flash it, and then clean the URL.
- Empty and error states are clear and give a way forward.

**Future Improvement Suggestions**

- Show a small tooltip on the count pill that explains what 'missing' means in plain language.
- On the redirect for non-internal users, briefly explain why they cannot see this page.
- Add a 'Report an issue' link on the error state so clients can flag problems directly.
- Persist the last opened transaction drawer between visits, so users do not lose their place when navigating away and back.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.1. All Documents — unified command bar (search, side filters, view toggle)

**Route / Location**

/documents (Unified Command Bar — second tier, directly below the AI Briefing)

**How To Test**

- Locate the Unified Command Bar. It is a single white card with two tiers — the bottom tier holds the controls described here (Tier 1 is covered in 27.2).
  - Scroll the document list down. The Unified Command Bar should stick to the top of the scroll area with a soft frosted-glass backdrop so the search and filters stay reachable while you scan a long list.
- Use the search box on the left of Tier 2.
  - The placeholder reads 'Search documents, addresses, types...'.
  - Type a partial document name, a transaction address, or a document type and confirm the list narrows as you type.
  - Confirm the search field gains an orange focus ring when selected.
  - Click the small 'x' inside the search box to clear it.
- Use the side filter pills.
  - Options: All, Buyer Side, Listing Side.
  - Each pill shows a transaction count.
  - The active pill has an orange background and bold amber text.
  - On narrow screens the pills scroll horizontally rather than wrapping.
- Use the view toggle at the far right of the command bar.
  - Hover each toggle to see a tooltip: 'View grouped by transaction' or 'View grouped by status'.
  - On wide screens each toggle shows its icon plus the text 'By Transaction' / 'By Status'.
  - On narrow screens only the icons are visible (the text is hidden for accessibility but still read by screen readers).
  - The active toggle has an amber background and the inactive toggle is plain white.
- Confirm the filter tabs in the page header still work together with these controls.
  - Header tabs: All, Signed, Pending Review, Sent for Sig., Missing.
  - The header filter tabs and the Tier 1 status chips (see 27.2) always stay in sync — switching one updates the other.
- Combine multiple controls at once.
  - For example: search 'inspection' + Buyer Side + Signed tab + By Status view. Confirm the list still makes sense.

**Expected Result**

- Search updates the list in real time and the focus ring confirms the input is active.
- Side filter pills, view toggle, header filter tabs, and Tier 1 status chips each change what is shown.
- All controls can be used together without the list breaking.

**Future Improvement Suggestions**

- Remember the last-used view (By Transaction vs. By Status) per user.
- Let the user save filter presets such as 'My overdue reviews'.
- Add an 'Export this filtered list' button so the user can share the current view as CSV.
- Add text labels under the view-toggle icons on narrow screens so new users know what the icons mean without hovering.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.2. All Documents — AI Briefing, status quick-filters, and completion progress

**Route / Location**

/documents (AI Briefing strip + Tier 1 of the Unified Command Bar, at the top of the content area)

**How To Test**

- Look at the AI Briefing strip at the top of the list (redesigned on April 20, 2026).
  - A small 'AI BRIEFING' tag with an orange sparkle icon is visible on the left.
  - On wide screens, a muted 'Updated {date}' (or 'No recent document activity') timestamp sits at the far right of the badge row; on narrow screens that same timestamp appears below the summary paragraph instead.
  - A bold one-line headline and a slightly lighter one-sentence summary are shown below the badge row.
  - A blue primary action button sits on the right on wide screens and centres below the text on narrow screens. Its label changes based on what is most urgent — for example 'Focus missing docs', 'Review signature queue', 'Review pending docs', or 'Review signed docs'.
  - While the briefing is loading, the strip shows the AI Briefing badge with a spinner plus two skeleton lines (no layout jump when it resolves).
- Click the primary action button.
  - The view resets to 'By Transaction' and the matching filter tab / status chip activates.
- Directly below the briefing, find the Unified Command Bar. Focus on Tier 1 (the top row of the bar).
  - Tier 1 contains four status quick-filter chips followed by the completion progress bar.
  - Chips, in order: 'Signed' (green number), 'Pending' (blue number), 'Sent' (amber number), 'Missing' (red number) — each with a large count and a small label.
  - On narrow screens the four chips sit in a 2x2 or 4-column grid; on wide screens they sit in a single row.
- Click one of the status chips.
  - The chip gains a coloured border and tinted background matching its number colour (green, blue, amber, or red).
  - The list below filters to only that status, and the header filter tab with the matching name also becomes active — the two controls stay in sync.
  - Hovering a chip shows a tooltip such as 'Filter by missing' when inactive, or 'Showing missing — click to clear' when active.
- Click the already-active chip a second time.
  - The chip returns to its transparent state and the filter resets to 'All'.
- Look at the completion progress bar on the right side of Tier 1.
  - The label 'Completion' appears to the left of the bar on screens at least 640 px wide (hidden on small phones to save space).
  - A thin green-gradient bar shows the percentage of tracked documents that are fully signed.
  - The numeric percentage is shown in bold green on the right of the bar.
  - On wide screens a thin vertical divider separates the chip group from the completion bar.

**Expected Result**

- The AI briefing headline and summary reflect the most urgent state of your document portfolio right now, and the timestamp tells you how fresh the underlying data is.
- Clicking the primary action button switches to the matching filter tab and 'By Transaction' view.
- Each status quick-filter chip filters the list and stays in sync with the header filter tabs; clicking an active chip clears the filter.
- The percentage on the progress bar matches the ratio of signed documents to the total of signed + pending + sent (missing rows are excluded from the denominator).

**Future Improvement Suggestions**

- Show a small trend indicator next to the completion percentage (up / down vs. last week).
- Make the whole briefing sentence clickable, not just the action button.
- Add a 'Email this briefing to my manager' one-click action.
- Let the user pin a favourite status chip so it is always pre-filtered on page load.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.3. All Documents — Transaction View (documents grouped by transaction)

**Route / Location**

/documents with 'By Transaction' selected

**How To Test**

- Switch the view toggle to 'By Transaction'.
- Inspect each transaction card header when it is collapsed.
  - Property address on the left.
  - A side badge: 'BUYER SIDE' (blue), 'LISTING SIDE' (amber), or 'BOTH SIDES' (purple).
  - Closing date shown as 'Close: {date}'.
  - Status pills: red '{N} missing doc(s)' if any are missing, or amber 'Sig. Pending' when signatures are outstanding.
  - A mini progress bar on the right showing {signed}/{total}, green when all signed, amber when at or above 50%, red below 50%.
- Click a transaction card to expand it.
  - The drawer contains up to four sections (only shown when they have items): 'SIGNED / EXECUTED' (green), 'NEEDS ATTENTION' (amber), 'SENT FOR SIGNATURE' (amber), and 'MISSING / REQUIRED' (red).
  - Each section shows its own count badge.
- At the bottom of the expanded drawer, check the extra controls.
  - A '+ Add another document to this transaction' button opens the Upload Document modal with this transaction already selected.
  - A footer row shows close date, full address, side, and an 'Open Transaction' button that navigates to the transaction detail page.
- Scroll to the bottom of the whole list.
  - If any document has not been assigned to a transaction, an 'UNASSIGNED DOCUMENTS' group appears with those rows.

**Expected Result**

- The header summarises each transaction's document state at a glance.
- Only sections that contain items appear in the expanded drawer.
- 'Add another document' pre-fills the correct transaction.
- 'Open Transaction' navigates to the transaction detail page for that deal.

**Future Improvement Suggestions**

- Add 'Expand all' and 'Collapse all' buttons at the top of the list.
- Show the assigned agent and elf on the card header for team lead visibility.
- Add a 'Resend client-facing packet' shortcut inside the card footer.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.4. All Documents — Status View (grouped by signature status)

**Route / Location**

/documents with 'By Status' selected

**How To Test**

- Switch the view toggle to 'By Status'.
- Confirm the four status groups appear in this order, each with a coloured icon.
  - Signed / Executed (green check).
  - Sent for Signature (amber diamond).
  - Pending Review (blue dot).
  - Missing / Required (red exclamation).
- Each group header shows the status title plus '{N} items across {M} transactions'.
- Click a group to expand and confirm each document row shows the transaction address it belongs to.

**Expected Result**

- All four groups render in the correct order.
- Groups align with whatever search, side filter, and filter tab are currently active.

**Future Improvement Suggestions**

- Add a 'Group by document type' option alongside 'Group by status'.
- Let the user drag-reorder groups for personal preference.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.5. All Documents — missing required documents and 'Upload Now'

**Route / Location**

/documents (MISSING / REQUIRED rows in both views)

**How To Test**

- The app automatically flags certain required documents based on the transaction. Examples you can test:
  - 'Appraisal Report' — appears for a buyer-side deal that is financed.
  - 'Counter Offer Addendum' — appears for a listing-side deal that has a counter offer on file.
  - 'Wire Instructions' — appears for a listing-side deal with a title/escrow closing mode.
- Confirm the visual style of a missing row.
  - Dashed pink/red border.
  - Light red background.
  - A 'MISSING' status badge.
- Click the 'Upload Now' button on a missing row.
  - The Upload Document modal opens with the transaction, suggested document type, and document label pre-filled.
  - A 'SUGGESTED DOCUMENT' banner appears at the top of the modal with the label.

**Expected Result**

- Missing documents appear according to the rules above.
- 'Upload Now' pre-fills the transaction, document type, and label correctly so the user can upload without retyping.

**Future Improvement Suggestions**

- Let admins customise the missing-document rules per tenant.
- Show a short reason next to each missing row ('Required because financing is conventional', etc.) so users understand why.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.6. All Documents — Upload Document modal

**Route / Location**

Opens from 'Upload Document' header button, 'Upload Now' on missing rows, or '+ Add another document…' inside a transaction card

**How To Test**

- Open the Upload Document modal from the header button.
- Check the 'ASSIGN TO TRANSACTION' dropdown.
  - It lists all active transactions by full address.
  - Leaving it blank is allowed (the document becomes an unassigned upload).
- Check the 'DOCUMENT TYPE' selector.
  - Shows toggle chips for each type: Purchase Agreement, Inspection Report, Appraisal, Amendment, and others.
  - At most one type can be selected at a time.
- Check the 'FILE' drop zone.
  - The hint underneath the drop zone reads 'PDF, DOC, DOCX, JPG, PNG, WEBP, GIF, TXT · Max 20 MB'.
  - Drag and drop a file, or click 'Click to browse' to pick a file.
  - Allowed types: .pdf, .doc, .docx, .jpg, .jpeg, .png, .webp, .gif, .txt.
  - Max size: 20 MB. Try a file larger than 20 MB and confirm the modal surfaces a clear backend error.
  - Note: spreadsheet types (.csv, .xlsx, .xls) are no longer accepted by the upload endpoint.
- Confirm a spinner appears in the drop zone while the file uploads, and that the primary button text changes to 'Uploading...'.
- Click Cancel to close without uploading, and Upload Document to save.

**Expected Result**

- The new file appears in both Transaction View and Status View.
- The upload is tagged with the chosen transaction and document type.
- Files over 20 MB or of unsupported types are rejected with a clear message.

**Future Improvement Suggestions**

- Suggest the document type automatically using AI on upload.
- Allow multi-file drag-and-drop in a single action.
- Add an 'Upload later' queue for users who are offline.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.7. All Documents — Preview and Download

**Route / Location**

/documents (row actions on each document)

**How To Test**

- Click the eye (Preview) icon on a document row.
  - The Preview modal shows the file name in the header.
  - For PDFs and images, the file renders inline.
  - For other file types, the modal says 'Preview not available — download to view.'
- In the Preview modal header, click the green 'Download' button.
- On any document row, click the standalone Download icon without opening preview first.
- Inside the Preview footer, click the orange 'Send for Signature' button.
  - The Send for Signature modal opens with this document already selected.

**Expected Result**

- PDFs and images preview inline. Unsupported types prompt the user to download.
- Download always opens or saves the file.
- Send for Signature from the preview hands off cleanly to the signature flow.

**Future Improvement Suggestions**

- Add inline annotations on the preview (highlight, comment) for collaborative review.
- Remember the last zoom level between previews.
- Allow side-by-side comparison of two versions in the preview window.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.8. All Documents — Send for Signature (live DocuSign integration)

**Route / Location**

'Send for Signature' header button, row action (pen icon), or Preview footer

**How To Test**

- Open the Send for Signature modal from each of the three entry points at least once.
  - Header button: opens with no document pre-selected.
  - Row pen icon: opens with both transaction and document pre-selected.
  - Preview footer 'Send for Signature' button: opens with the previewed document already selected and the preview modal closed in the background.
- If you opened the modal from the header (no document pre-selected), confirm the extra picker fields appear.
  - A 'TRANSACTION' dropdown listing every active transaction by full address.
  - A 'DOCUMENT' dropdown that filters its options by the chosen transaction (or shows everything when no transaction is selected).
  - Switching the transaction after picking a document that belongs to a different file clears the document selection.
- Confirm the DocuSign connection check at the top of the modal body.
  - If your DocuSign account is not yet connected, a red alert banner appears: 'No e-signature provider connected'.
  - The banner has a 'Connect DocuSign' button that opens the inline DocuSign Connect wizard (covered in 27.14).
  - Once connected, the red banner is replaced with a green confirmation: 'Connected to {provider}' with a one-line note that envelopes are sent from your account and that signed copies replace the original automatically.
- Configure the signers using the new manual recipient list.
  - Suggested-party chips appear above the list when the chosen transaction has parties on file (buyer, co-buyer, listing agent, etc.). Each chip shows '+ {name} ({party_role})'.
  - Click a suggested chip to add that party as a signer with their name and email pre-filled. Clicking the same chip a second time is a no-op (duplicate emails are ignored).
  - Click '+ Add signer' on the right of the SIGNERS label to add a blank row and type a name and email manually.
  - Each signer row shows '#1', '#2', '#3' on the left so the routing order is obvious; rows can be removed with the small red X on the right.
  - Confirm the empty-state message reads 'Add signers from the transaction's parties, or use "Add signer" to enter one manually.' when no signers have been added.
- Edit the 'SUBJECT' field at the bottom.
  - Pre-filled with 'Please sign the attached document' (250-character limit).
  - Whatever you type here becomes the email subject DocuSign sends to the recipients.
- Optionally write a note in 'MESSAGE TO SIGNERS'.
- Confirm Send button validation.
  - The Send button stays disabled until: a document and transaction are selected, every signer row has both a non-empty name and a syntactically valid email, AND DocuSign is connected.
  - Try saving with a malformed email — confirm an inline red error appears: 'Each signer needs a name and a valid email address.'
  - While sending, the button label changes to 'Sending...'.
- Click Send for Signature.

**Expected Result**

- A success toast reads 'Sent for signature' with the document name and transaction address.
- The matching document row in the list flips to the 'Sent for Sig.' status badge and gains an 'Awaiting: {names}' line under the metadata.
- If the Send call fails, a red 'Send for signature failed' toast appears AND the error is shown inline at the bottom of the modal so the user does not have to re-open it.
- The DocuSign envelope is created in your linked account; signers receive the email immediately.

**Future Improvement Suggestions**

- Let the sender pick a signing order explicitly (sequential vs. parallel) — currently the order is the order the signers were added.
- Add support for additional providers (DotLoop, Authentisign, Adobe Sign) alongside DocuSign.
- Show live signature status updates inside the modal as each signer completes their part, instead of waiting for the row to refresh.
- Persist subject/message templates per user so common envelopes (e.g. 'Inspection addendum sign request') can be re-used in one click.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.9. All Documents — Email Document modal

**Route / Location**

Three-dot menu on any document row (internal roles only)

**How To Test**

- Sign in as an internal role (Agent, Transaction Coordinator, Team Lead, Attorney, or Admin).
- Open the three-dot menu on a document and click 'Email Document'.
- Check the modal fields.
  - Attached document name is shown at the top (readonly, light orange background).
  - 'TO' field: accepts addresses separated by commas, semicolons, or spaces.
  - 'CC' field: optional, same format.
  - 'SUBJECT' field: pre-filled with 'Document: {filename}'.
  - 'MESSAGE' field: pre-filled with a ready-to-use template.
- Try to send with no recipient and confirm an inline error appears.
- Add one or more valid recipients and click 'Send Email'.

**Expected Result**

- A success toast reads 'Email queued' with the recipient count.
- The email is queued on the backend and will be logged in the communication history.

**Future Improvement Suggestions**

- Offer saved templates such as 'Client intro', 'Lender hand-off', 'Title company request'.
- Offer a 'Schedule for later' option.
- Flag invalid email addresses live as the user types.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.10. All Documents — Rename / Reclassify modal

**Route / Location**

Three-dot menu on any document row (internal roles only)

**How To Test**

- Sign in as an internal role.
- Open the three-dot menu and click 'Rename / Reclassify'.
- Check the modal fields.
  - 'FILE NAME' (required) is pre-filled with the current file name.
  - 'DISPLAY LABEL (optional)' — example placeholder: 'Executed PA — Smith'.
  - 'DOCUMENT TYPE' dropdown shows the current type selected, with all other types available.
- Try to save with an empty file name and confirm it is blocked.
- Change one or more fields and click Save.

**Expected Result**

- The document row updates its name, label, and type immediately after save.

**Future Improvement Suggestions**

- Use AI to suggest the correct document type based on the file content.
- Preview how the new name will appear in email subjects and the client portal before saving.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.11. All Documents — Version History (and Upload New Version)

**Route / Location**

Three-dot menu on any document row

**How To Test**

- Open the three-dot menu and click 'Version History'.
- Check the modal content.
  - Loading skeletons appear while versions load.
  - Each version is listed with a label such as 'v1', 'v2', etc., the file name, size, upload date, and a 'Download' button.
  - The newest version has a green 'Current' badge; older versions have a grey 'Legacy' badge.
  - Empty state if no versions yet: 'No versions yet'.
- Click 'Upload New Version' and pick a replacement file.
  - A success toast appears: 'New version uploaded — v{N+1} is now current.'
- Reopen the modal and confirm the new version is marked Current.
- Click Download on any historical version to confirm it still downloads.

**Expected Result**

- All versions are listed in chronological order.
- Uploading a new version moves the previous Current version to Legacy.
- Downloads work for any version in the list.

**Future Improvement Suggestions**

- Show a side-by-side diff between two versions.
- Allow rolling back to a prior version and marking it current again.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.12. All Documents — Archive (internal-only on this page)

**Route / Location**

Three-dot menu on any document row (/documents)

**How To Test**

- Sign in as an internal role (Agent, Transaction Coordinator, Team Lead, Attorney, or Admin).
  - Open the three-dot menu and click 'Archive Document' at the bottom (red text).
  - Confirm the dialog: 'Archive this document? The document will be archived (soft-deleted) and can be restored by an authorized user.'
  - Click Archive and confirm the document disappears from the list and a 'Document archived' toast appears.
- Confirm the non-internal flagging path is no longer reachable from /documents.
  - Non-internal users (For-Sale-By-Owner Customers, etc.) are redirected to /dashboard before they can reach the page, so the 'Flag for Deletion' modal does not open here.
  - If the client wants to flag a document, they must do it from the documents tab inside an individual transaction (covered in section 23 / Documents window on a transaction card).

**Expected Result**

- Internal users can archive directly, with a confirmation dialog to prevent accidents and a toast on success.
- Non-internal users never see the dropdown action on /documents because the page redirects them away.

**Future Improvement Suggestions**

- Add a 'Restore archived document' area for admins so they can undo accidental archives.
- Add an undo toast immediately after archiving so an accidental click can be reverted in one tap.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.13. All Documents — Deletion Approval Queue

**Route / Location**

'Deletion Queue' header button on /documents (internal roles only)

**How To Test**

- Sign in as an internal role and click 'Deletion Queue' in the page header.
- Check each queued request card.
  - Document name (bold) and flagged date.
  - Document type badge, if set.
  - The reason the requester gave, in a light grey box.
  - A 'DECISION NOTES (optional)' textarea for the reviewer.
  - Two buttons: 'Reject' and 'Approve & Archive'.
- Check the empty state.
  - When there are no requests, the panel reads 'No pending deletion requests.'
- Approve one request and confirm the toast: 'Deletion approved — Document archived.'
- Reject another request and confirm the toast: 'Deletion rejected — Document remains active.'

**Expected Result**

- All flagged requests from non-internal users appear in order.
- Approve archives (soft-deletes) the document. Reject leaves it active.
- Both decisions are recorded for audit purposes.

**Future Improvement Suggestions**

- Notify the original requester automatically when their request is approved or rejected.
- Allow bulk approve / bulk reject for high-volume cleanup.
- Show the reviewer who flagged the document (requester name) alongside the reason.

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.14. All Documents — Connect DocuSign wizard (inline OAuth)

**Route / Location**

'Connect DocuSign' button inside the Send for Signature modal (only when no provider is connected yet)

**How To Test**

- Make sure your DocuSign account is NOT connected, then open the Send for Signature modal (header button is fine).
  - The red 'No e-signature provider connected' banner appears.
  - Click the 'Connect DocuSign' button on the banner — a new modal opens on top.
- Inspect the wizard's intro step.
  - Header reads 'Connect DocuSign' on a soft amber gradient with a pen icon.
  - Subheading: 'Link your DocuSign account so you can send documents for signature.'
  - Body has three explainer rows: 'Tokens are encrypted at rest', 'Envelopes are sent from your DocuSign account', 'You can disconnect anytime'.
  - A three-dot step indicator near the top shows you are on step 1 of 3.
  - Footer buttons: Cancel and 'Continue to DocuSign' (with an external-link icon).
- Click 'Continue to DocuSign'.
  - The wizard advances to the authorize step. A spinner and the message 'Complete the sign-in in the DocuSign window' appear.
  - A new browser popup opens pointing at DocuSign's OAuth screen.
  - Helper text below the spinner: 'Popup blocked? Enable popups for this site and click Retry.'
- Complete the DocuSign login in the popup.
  - DocuSign closes the popup automatically and the wizard advances to the 'Done' step.
  - A green check icon, the headline 'DocuSign connected', and a one-line summary 'Connected to {account_name} as {email}' (or just the email if the account name is not available) are shown.
  - The footer button changes to 'Back to Send for Signature' (green).
- Click 'Back to Send for Signature'.
  - The wizard closes. The Send for Signature modal underneath now shows the green 'Connected to {provider}' confirmation, and the Send button enables once you add a valid signer.
  - A page-level toast 'DocuSign connected — You can now send documents for signature.' confirms success.
- Test the failure path.
  - Cancel the DocuSign popup before it finishes.
  - The wizard stays on the authorize step, the spinner is replaced by the message 'Waiting for a response from DocuSign…' and 'If the window closed without finishing, click Retry below.'
  - If the OAuth handshake itself fails, a red 'Connection failed' banner shows the underlying error and the Retry button stays enabled.

**Expected Result**

- Connecting to DocuSign happens entirely inside Velvet Elves — the user never has to leave the documents page.
- On success, a toast confirms the connection and the Send for Signature flow becomes usable without a page refresh.
- If the user cancels or hits an OAuth error, they can retry without re-opening the wizard from scratch.
- Tokens are stored encrypted at rest on the user's profile (not visible in app logs).

**Future Improvement Suggestions**

- Detect popup-blocked browsers up-front and offer a fallback redirect flow instead of a popup.
- After a successful connection, auto-send a tiny test envelope to the signed-in user's own email so they can verify the link works.
- Surface the connected DocuSign account name in the profile menu (so users can tell at a glance which account is linked).

**Feedback**

_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._

> _Status:_ 
> 
> _Comments:_ 
> 
> _Improvement priority:_ 

---

### 27.15. All Documents — Manage in-flight envelopes (Refresh, Void, Declined / Voided states)

**Route / Location**

Document rows whose signature status is sent / pending / declined / voided

**How To Test**

- Send a document for signature (see 27.8) but do not let the recipients sign yet.
  - Confirm the row's status badge changes to 'Sent for Sig.' and a new 'Awaiting: {name1}, {name2} +{N} more' line appears under the metadata.
  - Hover the awaiting line — a tooltip lists every recipient with their role (e.g. 'Jane Smith (signer)').
  - On wide screens the pen icon in the row's action strip is replaced with a circular Refresh icon (with the tooltip 'Refresh signature status'). On narrow screens the same action lives inside the three-dot menu as 'Refresh Signature Status'.
- Open the page (or refresh it) and confirm the auto-sync behaviour.
  - On every page load, the page silently calls DocuSign in the background for every in-flight envelope. This heals docs whose webhook was missed.
  - Auto-sync runs at most once per document per page mount; failures are silent (the manual Refresh button stays available as the user's escape hatch).
- Click the Refresh icon on an in-flight envelope.
  - While the call is in flight, the icon spins and is disabled.
  - On success a toast appears: 'Signature status refreshed — {Document name} - {Signature complete | Envelope voided | Envelope declined | Status: {raw status}}'.
  - If the envelope finished, the row immediately flips to 'Signed' (green) without a manual refresh.
- Open the three-dot menu on an in-flight envelope and click 'Void Envelope'.
  - A toast appears: 'Envelope voided — {Document name} - recipients will no longer be able to sign.'
  - The row gains a soft pink background, a red '! Voided' pill next to the status badge, and an inline message: 'Previous envelope voided. Send a new one when ready.'
  - The pen icon is restored on the row (replacing the Refresh icon) and its tooltip becomes 'Resend for Signature (previous voided)'. The dropdown's send option label also updates to 'Resend for Signature'.
- Simulate a declined envelope (the recipient clicks Decline in DocuSign).
  - After the next sync, the row turns the same soft-pink background and shows a '! Declined' pill plus the inline message: 'A signer declined the previous envelope. Resend to try again.'
  - Just like the voided case, the action becomes 'Resend for Signature' so the user can immediately recover.
- Click 'Resend for Signature' from a declined or voided row.
  - The Send for Signature modal opens with the same document already selected so the user can adjust signers / message and re-send.

**Expected Result**

- Awaiting recipients are visible at a glance without having to open DocuSign in another tab.
- Refresh and Void are reachable from both the row's action strip (wide screens) and the three-dot menu (mobile).
- Declined and voided envelopes are surfaced clearly with red styling, a descriptive inline message, and a one-click 'Resend' path so a stuck file never feels permanent.
- Auto-sync on page load means most stuck envelopes heal themselves before the user notices.

**Future Improvement Suggestions**

- Add a 'Why did this fail?' link to the declined/voided message that opens the DocuSign envelope page in a new tab.
- When voiding an envelope, prompt the user for a short reason and pass it to DocuSign so signers see context.
- Surface awaiting recipients on the transaction card header (not just on the document row) so a team lead can see which deal is stuck on whom from the list view.
- Add a manual 'Force-sync all' button that runs the sync logic across every in-flight envelope without a page reload.

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

### 29. Settings — Integrations tab

**Route / Location**

/settings (Integrations tab)

**How To Test**

- Open /settings and go to the Integrations tab.
- Click Refresh to reload integrations.
- For Gmail, try Connect and then Disconnect.

**Expected Result**

- The Gmail row updates its connected state after each action.

**Future Improvement Suggestions**

- Add Microsoft / Outlook and Apple iCloud integrations next to Gmail.
- Show a 'Last synced' timestamp and a sync-now button per integration.

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

### 32. Admin user detail (direct link)

**Route / Location**

/admin/users/<userId>

**How To Test**

- As an Admin, open a known user ID URL.
- Open an invalid user ID to check the error state.

**Expected Result**

- A valid ID renders the user's profile card.
- An invalid ID shows a clean error state.

**Future Improvement Suggestions**

- Finish the Team Members list page so this page is reachable without typing URLs.
- Add an audit trail showing the user's recent actions.

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
