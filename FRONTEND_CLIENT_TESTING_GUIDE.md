# Real Estate Expert Frontend Testing Guide

Last updated: April 13, 2026

## Purpose

This guide explains how the Real Estate Expert team can test the currently implemented frontend features in the Velvet Elves application directly in the browser.

This document is based on the current `velvet-elves-frontend` implementation as of April 13, 2026. It focuses on:

- Fully testable frontend workflows
- Role-specific screens and permissions
- Screens that are present but intentionally still "Coming Soon" or UI-only

It does **not** describe planned features that are only present in design files or roadmap documents.

## Test Setup

Before testing, make sure the following are ready:

| Item | What you need |
| --- | --- |
| Frontend | Live Real Estate Expert testing URL: `http://dev.velvetelves.com/` |
| Backend | No direct backend URL is needed for Real Estate Expert testing. The frontend should already be connected to the correct environment. |
| Browser | Chrome or Edge recommended. Allow pop-ups and downloads for print/export flows. |
| Email access | Needed for register/confirm-email/forgot-password/invite flows if those flows are being tested end-to-end. |
| Test accounts | Ideally one account for each role you want to verify. |

All steps in this guide assume testing is being performed on the Real Estate Expert dev site at `http://dev.velvetelves.com/`, not on a localhost frontend.

### Recommended roles to have available

For full coverage, try to test with these user types:

| Role | Why it matters |
| --- | --- |
| Agent or Elf | Covers the main day-to-day workflow. |
| TeamLead or Admin | Needed for delete permissions, team filters, and admin task-template screens. |
| Attorney | Loads the attorney-specific transaction workspace. |
| FSBO_Customer | Lets you verify the FSBO-specific navigation and placeholder pages. |
| Admin with a known user ID | Needed only if you want to test the direct user-detail route. |

If the Real Estate Expert environment does not allow self-registering privileged roles, ask the product team to provision those accounts first.

### Browser reset tips

Use these when switching roles or retesting first-time flows:

1. Sign out before switching accounts.
2. Use separate browser profiles or incognito windows for different roles.
3. Clear local storage if you need a clean session.
4. Clear `velvet_elves_tutorial_completed` if you want to see the first-time tutorial again.
5. Clear `velvet_elves_token` if you want to fully reset auth locally.

### Minimum data set to create

If the environment starts mostly empty, create this minimum data set first:

1. One new transaction
2. At least one task inside that transaction
3. At least one uploaded document
4. At least one contact on the transaction

That is enough to exercise most of the implemented screens.

## Coverage Summary

### Fully testable now

- Registration and login
- Forgot password and reset password
- Email confirmation
- Onboarding wizard
- First-time tutorial overlay
- Dashboard
- New Transaction wizard
- Active Transactions page
- Transaction card actions
- Transaction detail page
- Documents page
- Profile page
- Gmail integration connect/disconnect screen
- Admin/TeamLead task template screens
- Attorney transaction workspace

### Testable with direct links or tokenized links

- Email-confirmation route
- Password-reset route
- Invite-accept route
- Task detail route
- Admin user detail route
- Unauthorized page
- 404 page

### Present in the frontend, but not fully implemented yet

- My Task Queue page
- Closing Calendar page
- AI Suggestions page
- Analytics page
- Client Communication / Contacts page
- Notifications page
- Sharing page
- Team Overview page
- Team Members list page
- Several "Settings" tabs outside of Integrations
- Some top-bar and attorney-header buttons
- AI chat panel is a frontend demo surface, not a live AI conversation endpoint

## Suggested Test Order

Run testing in this order to avoid backtracking:

1. Public pages and auth flows
2. Onboarding and first-time tutorial
3. Standard Agent or Elf workflow
4. TeamLead or Admin extras
5. Attorney workspace
6. FSBO-specific navigation
7. Direct-link-only routes and error states

---

## 1. Public and Auth Flows

Use a logged-out browser window for this section.

### 1.1 Terms of Service and Privacy Policy

Test both routes:

- `/terms`
- `/privacy`

What to verify:

1. Each page loads without requiring login.
2. The correct page title is shown.
3. The long-form legal content renders correctly.
4. These pages still open correctly whether you are logged in or logged out.

### 1.2 Protected-route redirect to login

1. While logged out, go directly to `/dashboard`.
2. Confirm the app redirects you to `/login`.

Expected result:

- Protected pages should not be visible without authentication.
- The app should send you to the login screen first.

### 1.3 Register page

Open `/register`.

What to verify on the screen:

1. Google sign-up button is visible.
2. These fields are visible:
   - Full name
   - Email address
   - Password
   - Confirm password
   - Phone (optional)
   - Role dropdown
   - Terms/Privacy checkbox
3. Password strength indicator appears and updates while typing.
4. Terms of Service and Privacy Policy links open.

Validation checks to perform:

1. Enter an invalid email and confirm validation appears.
2. Enter a weak password and confirm password rules are shown.
3. Enter mismatched passwords and confirm the mismatch message appears.
4. Leave the Terms checkbox unchecked and confirm submission is blocked.

Successful submission test:

1. Submit a valid registration.
2. Use different roles if you want to verify role-based navigation later.

Expected result:

- Depending on backend response, the user will either:
  - be logged in immediately and sent to `/onboarding`, or
  - be redirected to `/login` after a success message telling them to confirm their email.

### 1.4 Login page

Open `/login`.

What to verify on the screen:

1. Google login button is visible.
2. Email and password fields are visible.
3. "Forgot password?" link is visible.
4. Link to `/register` is visible.

Validation and success checks:

1. Try invalid email format and confirm validation appears.
2. Try wrong credentials and confirm an error banner appears.
3. Sign in with a valid account.

Expected result:

- If `onboarding_completed` is `false`, the user should go to `/onboarding`.
- If `onboarding_completed` is `true`, the user should go to `/dashboard`.
- Refresh the browser after login and confirm the user stays signed in.

### 1.5 Logout

After logging in:

1. Open the avatar/user menu in the top bar or sidebar.
2. Click `Log Out`.

Expected result:

- You return to `/login`.
- Protected pages should no longer be accessible without signing in again.

### 1.6 Forgot password

Open `/forgot-password`.

Test steps:

1. Verify the email field and `Send Reset Link` button are visible.
2. Try an invalid email and confirm validation appears.
3. Submit a valid email address.

Expected result:

- The page switches to a success state saying the reset email was sent.
- The success state includes:
  - the submitted email address
  - "Try a different email"
  - link back to sign in

### 1.7 Reset password

This flow needs a valid recovery link or tokenized reset URL.

Use either:

- the real reset link received by email, or
- `/reset-password` with valid recovery query/hash parameters

Important behavior:

- If a valid recovery link lands on `/`, `/login`, `/register`, or `/forgot-password`, the frontend should automatically redirect to `/reset-password`.

What to test:

1. Open a valid reset link.
2. Verify the reset form loads.
3. Enter a weak password and confirm validation appears.
4. Enter a valid new password and matching confirmation.
5. Submit the form.

Expected result:

- Success state appears.
- The app then redirects to `/login`.

Invalid-link test:

1. Open `/reset-password` without a token, or with an expired/invalid token.

Expected result:

- You should see the "Invalid or expired link" state with a way to request a new link.

### 1.8 Email confirmation

This flow needs a valid email-confirmation link.

Use either:

- the real confirmation link from email, or
- a URL containing valid confirmation parameters

Important behavior:

- If a valid confirmation link lands on a non-confirmation entry page, the frontend should automatically redirect to `/auth/confirm`.

What to test:

1. Open a valid email-confirmation link.
2. Verify the spinner/loading state.
3. Wait for the redirect.

Expected result:

- The user should be signed in automatically.
- The app should route to:
  - `/onboarding` for a not-yet-onboarded user, or
  - `/dashboard` for an already-onboarded user.

Invalid-link test:

1. Open a malformed confirmation URL.

Expected result:

- An error state appears telling you the link is missing or unsupported.

### 1.9 Google OAuth sign-in / sign-up

The frontend currently exposes Google buttons on Login and Register.

How to test:

1. Click the Google button on `/login`.
2. Repeat on `/register`.

Expected result if OAuth is configured:

- The browser redirects to Google.
- After approval, the app returns through `/oauth/callback`.
- The user is logged in and then sent to `/onboarding` or `/dashboard`.

Expected result if OAuth is not configured in the environment:

- The flow should fail gracefully with an error banner.

### 1.10 Invite acceptance

This flow needs a valid invitation token.

Frontend route currently implemented:

- `/invite/<token>`

What to test:

1. Open the valid invite URL.
2. Confirm the page shows:
   - invitation email
   - invited role
   - form fields for full name, password, and optional phone
3. Submit the form with valid values.

Expected result:

- The invited user is signed in.
- The user is sent to `/onboarding`.

Invalid-invite test:

1. Open an invalid token.

Expected result:

- "Invalid Invitation" screen appears with a link back to login.

> Note: there is a route-format mismatch worth watching during Real Estate Expert testing. The frontend route is `/invite/<token>`. If an environment still sends invite emails that land on `/invite/accept?token=...`, use the actual token value to open `/invite/<token>` directly.

---

## 2. First-Login Flows

### 2.1 Onboarding wizard

The onboarding wizard is shown for newly created or newly invited users, and it is also available at `/onboarding` for an authenticated user who has not completed onboarding.

The onboarding flow has 5 steps:

1. Welcome
2. Role & Company
3. Integrations
4. First Transaction
5. All Set

#### Step-by-step test

1. Welcome
   - Verify the welcome copy and progress indicator.
   - Click `Next`.

2. Role & Company
   - Change the role dropdown.
   - Enter a company name.
   - Upload a logo and confirm the image preview appears.
   - Test the `Skip` option as well.

3. Integrations
   - Verify Gmail connect button is shown.
   - Click `Connect`.
   - If the backend integration endpoint is configured, confirm the connected state.
   - If not configured, confirm an error is shown gracefully.
   - Test the `Skip` option too.

4. First Transaction
   - Drag and drop a supported file or use `Browse Files`.
   - Confirm the uploaded file name appears.
   - Test the `Skip` option too.

5. All Set
   - Verify final success screen.
   - Click `Go to Dashboard`.

Expected result:

- Onboarding completion should redirect the user to `/dashboard`.

### 2.2 First-time tutorial overlay

After landing on the authenticated app for the first time, a tutorial overlay may appear.

What to test:

1. Verify the tutorial appears on first dashboard visit.
2. Click `Next` through all tutorial steps.
3. Test `Back`.
4. Test `Skip`.
5. On the last step, click `Get Started`.

Expected result:

- The overlay closes and does not automatically reappear.

To retest it:

1. Clear local storage key `velvet_elves_tutorial_completed`.
2. Reload the app.

---

## 3. Core Authenticated App (Agent or Elf Baseline)

Use an Agent or Elf account for this section unless a different role is called out.

### 3.1 Dashboard and global app shell

Open `/dashboard`.

What to verify on the dashboard:

1. Greeting text appears.
2. "My week" pills appear:
   - tasks
   - overdue
   - completed
   - active
3. `My Tasks` card appears with `Upcoming` and `Overdue` tabs.
4. `My Deadlines` card appears with `Upcoming` and `Overdue` tabs.
5. `Upcoming Closings` area appears with cards or an empty state.
6. `New Transaction` button opens the transaction wizard.

What to verify in the global layout:

1. Sidebar navigation appears and changes based on role.
2. Sidebar KPI tiles appear.
3. `Today's AI Briefing` button in the top bar opens the AI side panel.
4. Top-bar status chips such as `Critical`, `Needs Attention`, and `On Track` route into filtered transaction views when present.
5. User menu opens and gives access to:
   - My Profile
   - Settings
   - Log Out
6. Mobile menu button opens the sidebar on smaller screens.

Current UI-only items in the shell:

- The top-bar search area is presentational only.
- The notification bell in the top bar is presentational only.

### 3.2 New Transaction wizard

The main new-transaction flow opens from:

- top-bar `+ New Transaction`
- sidebar `+ New Transaction`
- dashboard `New Transaction`

This wizard is one of the most complete frontend workflows and should be tested carefully.

#### Wizard step coverage

| Step | What to test | Expected result |
| --- | --- | --- |
| Documents | Upload one PDF, upload multiple files, remove a file, verify document count, click `Split` on a PDF, test `Skip upload - enter details manually` | Uploaded files appear immediately; PDF opens split dialog; manual mode jumps forward without upload |
| AI Parsing | Continue after upload | Parsing screen appears and extraction runs; if parsing cannot complete, the flow still supports manual continuation |
| Address | Fill Street, City, State, ZIP; leave confirmation unchecked first, then check it | `Continue` should remain blocked until `I confirm this address is correct` is checked |
| Purchase Info | Fill price, closing date, inspection days, financing type, title ordered by, notes; toggle `Home warranty`; toggle `HOA`; click `Add party` | Conditional fields appear for warranty and HOA; party rows can be added; form data is retained |
| Missing Info | Leave a required field empty so this step appears; resolve it manually and with `AI Search` | Missing fields show as rows; saving a value marks them resolved |
| Confirm | Review summary sections, use `Edit` buttons, click `Accept & Create Transaction` / `Create Transaction` | Transaction is created and you are returned to the transaction workspace/listing flow |

Additional wizard checks:

1. Close the wizard after entering some data.
2. Confirm the discard-warning prompt appears.
3. Reopen the wizard and verify the initial state is clean.

### 3.3 Active Transactions page

Open `/transactions`.

What to verify:

1. The page header shows the correct title and total deal count.
2. Export buttons are visible:
   - `Export CSV`
   - `Export Excel`
   - `Print Report`
3. Filter tabs are visible:
   - All
   - Overdue
   - Due Today
   - Closing Soon
   - In Inspection
   - On Track
   - Unhealthy
4. Sort control is visible.
5. Cards load from the backend.
6. Floating `Ask AI` button opens the AI panel.

State-filter checks:

1. Use the sidebar to open:
   - Active Transactions
   - Pending
   - Closed
   - All Transactions
2. Confirm the title and list update correctly for each.

Export checks:

1. Click `Export CSV` and confirm a file download starts.
2. Click `Export Excel` and confirm a file download starts.
3. Click `Print Report` and confirm a new printable report window opens.

Expected filenames from the frontend helpers:

- `transactions.csv`
- `transactions.xls`

### 3.4 Expanded transaction card actions

On `/transactions`, expand at least one transaction card and test all available actions.

#### Tasks section

1. Expand the card.
2. Toggle a task complete/incomplete using the checkbox.
3. Open the task status dropdown and change the status.
4. Click `+ Add` or `+ Add Task`.

Expected result:

- The task state should update visually right away.
- Add Task opens the Add Task modal.

#### Key Dates section

1. Click any key date row.
2. Change the date in the popover.
3. Save it.

Expected result:

- The updated date should display immediately in the card.

#### Contacts section

1. Expand a contact row.
2. Test phone and email actions if values exist.
3. Use the plus button to add a new contact.
4. If a group is empty, click its empty-state add area.

Expected result:

- Contact modal opens with the role preselected from the clicked group.

#### Documents and history

1. Click the `Docs` badge or `View/Add Docs`.
2. Click the `History` badge or `History`.

Expected result:

- Documents modal opens for the correct transaction.
- History side panel opens for the correct transaction.

#### Print and AI actions

1. Click `Print`.
2. Click the next-step CTA or any AI suggestion chip.

Expected result:

- `Print` opens a printable closing-checklist window.
- AI actions open the AI side panel.

### 3.5 Add Task modal

Open the Add Task modal from an expanded transaction card.

What to test:

1. Confirm task name is required.
2. Set a completion method.
3. Set a due date.
4. Change assignee between `Myself` and `AI Agent`.
5. Click `Get AI Suggestions on How to Complete`.
6. Apply one of the AI-suggested approaches.
7. Submit the task.

Expected result:

- The task is created and the modal closes.
- Applying an AI suggestion should populate the completion method when a suggested method is returned.

### 3.6 Add Contact modal

Open the Add Contact modal from an expanded transaction card.

What to test:

1. Confirm the role label matches the contact group you clicked from.
2. For lender/title groups, verify the `Company Name` field appears.
3. Enter first name, last name, phone, email, and optional company.
4. Submit the form.

Expected result:

- The contact is created and the modal closes.

### 3.7 Documents modal from a transaction card

Open the transaction documents modal from an expanded card.

What to test:

1. Existing documents list appears.
2. `Details` expands per document.
3. Download button opens the document download URL.
4. `Add Document` uploads a new file.

Expected result:

- Uploaded file appears in the transaction document list.
- Document details show metadata such as version and update date.

### 3.8 History panel

Open the transaction history panel from an expanded card.

What to test:

1. The panel slides in from the right.
2. Search box filters history.
3. Events are grouped under headings.

Expected result:

- Matching history items remain visible while nonmatching items are filtered out.

### 3.9 AI chat panel

This panel can be opened from:

- top-bar `Today's AI Briefing`
- floating `Ask AI` button on transactions pages
- AI buttons/chips inside transaction cards

What to test:

1. Verify the panel opens and closes.
2. Click several quick chips.
3. Type your own prompt and click `Send`.

Expected result:

- Messages appear in the panel.

Current limitation:

- This is currently a frontend demo chat surface. It stores/display messages in the UI but is not yet a live AI conversation endpoint.

### 3.10 Transaction detail page

Open a transaction detail page by clicking a transaction from the dashboard or by going directly to `/transactions/<transactionId>`.

What to verify in the header:

1. Property address appears.
2. Created timestamp appears.
3. Current transaction status badge appears.
4. Status dropdown allows changing the transaction status.

Delete permission check:

1. Log in as TeamLead or Admin.
2. Confirm the `Delete` button is visible.
3. Confirm the delete confirmation dialog appears.

Expected result:

- Successful delete should return the user to `/transactions`.

#### Transaction-detail tabs

| Tab | What to test | Current expectation |
| --- | --- | --- |
| Overview | Summary card, key dates, status, use case, price | Fully renders; AI Suggestions block is still a placeholder section |
| Tasks | Add task, change task status, toggle complete, open task-info dialog | Fully interactive |
| Documents | Upload and list transaction documents | Fully interactive |
| Parties | Open tab | Currently empty placeholder state |
| Communications | Open tab | Currently empty placeholder state |

### 3.11 Task detail page

This route exists at `/tasks/<taskId>`, but it is not currently exposed from the main navigation.

Use it only if you already know a valid task ID.

What to test:

1. Open a valid task detail URL.
2. Confirm task name, status, due date, description, automation level, and metadata render.
3. Click `Edit Task`.
4. Change fields and save.
5. Test `Cancel`.

Expected result:

- Changes save successfully and edit mode closes.

Not-found check:

1. Open `/tasks/non-existent`.

Expected result:

- `Task not found` message appears.

### 3.12 Documents page

Open `/documents`.

What to test:

1. Page header and upload button render.
2. Search box filters the document list.
3. Grid/list view toggle works.
4. Upload dialog accepts supported file types.
5. Clicking a document opens the detail dialog.

Expected result:

- Search filters by filename.
- Upload adds a new document.
- Detail dialog shows metadata such as size, upload date, transaction ID, and storage path.

### 3.13 My Profile page

Open the user menu and go to `/profile`.

What to test:

1. Profile summary card renders with initials, role, status, email, and created date.
2. Edit form is prefilled with current name and phone.
3. Update the name or phone.
4. Click `Save changes`.

Expected result:

- Success toast appears and the profile card reflects updated data.

### 3.14 Settings page

Open `/settings`.

#### Integrations tab

This is the main settings area that is currently wired to backend actions.

What to test:

1. Refresh button loads current integrations.
2. Gmail row shows connected vs not connected state.
3. `Connect` and `Disconnect` work.

Expected result:

- Gmail state updates after connect/disconnect.

#### Other settings tabs

These tabs are present in the UI but not fully wired as persistent settings yet:

| Tab | Current behavior |
| --- | --- |
| Company | Form fields render and `Save Changes` button is present, but there is no save handler wired yet |
| Branding | Branding inputs and `Save Branding` button are present, but not wired for persistence |
| AI Config | Read-only status/credit display only |
| Task Templates | Static preview list inside Settings; use the real admin task-template screens for actual create/edit testing |

---

## 4. Role-Specific Flows

### 4.1 TeamLead and Admin

Use a TeamLead or Admin account for this section.

#### Extra permissions already visible in the standard workflow

What to test:

1. On `/transactions`, confirm the team-member filter appears.
2. On transaction detail, confirm `Delete` is visible.
3. On task lists, confirm task delete controls are visible.

#### Task Templates list page

Open `/admin/task-templates`.

What to test:

1. Search box filters templates.
2. Templates are grouped by category.
3. `New Template` opens the create dialog.
4. Create a new template with:
   - name
   - description
   - automation level
   - category
5. Open an existing template.

Expected result:

- New template appears in the list after creation.

#### Task Template detail page

Open `/admin/task-templates/<templateId>`.

What to test:

1. Read-only detail view renders.
2. Click `Edit Template`.
3. Update:
   - name
   - description
   - target
   - milestone label
   - dependency relationship
   - float days
   - automation level
   - category
   - sort order
   - active/inactive toggle
4. Use the dependency rule builder section.
5. Save.

Expected result:

- Changes persist and the page returns to non-edit mode.

#### Team pages currently available to TeamLead/Admin

Open these routes:

- `/team`
- `/admin/users`

Expected result:

- Both routes should load, but they currently show `Coming Soon` pages rather than management tables.

#### Admin-only user detail route

This route is implemented but is not currently reachable from the Team Members list page because that list page is still a placeholder.

Open:

- `/admin/users/<userId>`

Requirements:

- Admin role
- A real known user ID

What to test:

1. Confirm the user detail/profile card renders.
2. Confirm invalid or inaccessible IDs show the error state.

### 4.2 Attorney

Use an Attorney account and open `/transactions`.

Important behavior:

- Attorneys do **not** get the normal Active Transactions page at `/transactions`.
- The route switches to the attorney-specific workspace automatically.

What to test in the attorney workspace:

1. Attorney-specific page title and KPI row render.
2. Filter tabs work:
   - All
   - Needs Review
   - Missing Docs
   - Ready To Release
   - Clean Files
3. Matter cards render.
4. Floating `Ask AI` button opens the AI panel.
5. Attorney-specific sidebar appears.

Current attorney UI-only items:

- `Open review queue`
- `State rules`
- `Upload legal packet`

Those buttons are currently presentational only.

### 4.3 FSBO_Customer

Use an FSBO_Customer account if one is available.

What to verify:

1. FSBO-specific sidebar labels appear:
   - My Properties
   - Documents
   - Milestones & Messages
   - Ask Velvet Elves AI
   - Notifications
   - Sharing
2. Dashboard still loads.
3. Transactions still load.
4. Documents page still loads.

Expected placeholder behavior for FSBO-specific routes:

- `Milestones & Messages` points to the current Task Queue placeholder
- `Notifications` is a Coming Soon page
- `Sharing` is a Coming Soon page

---

## 5. Direct-Route and Error-State Checks

### 5.1 Unauthorized access

Use a lower-privilege account such as Agent.

Test these routes directly:

- `/team`
- `/admin/task-templates`
- `/admin/users/some-id`

Expected result:

- The app should redirect to `/unauthorized`.
- The Unauthorized page should show a 403-style access-denied screen.

### 5.2 Not Found page

Open any made-up route such as:

- `/this-page-does-not-exist`

Expected result:

- The 404 page appears with a `Back to Dashboard` button.

### 5.3 Direct-link-only screens worth checking

These implemented routes are not yet easy to reach from normal navigation, but they can still be validated directly:

- `/tasks/<taskId>`
- `/admin/users/<userId>`
- `/reset-password?...`
- `/auth/confirm?...`
- `/invite/<token>`

---

## 6. Screens That Are Present But Not Fully Implemented Yet

For the pages below, the correct current behavior is simply that the page opens and shows its placeholder state. Real Estate Expert reviewers should **not** expect full CRUD behavior there yet.

### 6.1 Full-page Coming Soon routes

| Route | Current title |
| --- | --- |
| `/tasks/queue` | My Task Queue |
| `/calendar` | Closing Calendar |
| `/ai-suggestions` | AI Suggestions |
| `/reports` | Analytics |
| `/contacts` | Client Communication |
| `/notifications` | Notifications |
| `/sharing` | Sharing |
| `/team` | Team Overview |
| `/admin/users` | Team Members |

Expected result for each:

1. The page title and description render.
2. `Back to Dashboard` works.

### 6.2 Partial areas inside otherwise real pages

| Location | Current state |
| --- | --- |
| Transaction Detail > Overview > AI Suggestions | Placeholder only |
| Transaction Detail > Parties tab | Empty placeholder only |
| Transaction Detail > Communications tab | Empty placeholder only |
| Settings > Company | UI present, save not wired |
| Settings > Branding | UI present, save not wired |
| Settings > AI Config | Read-only display |
| Settings > Task Templates | Static preview, not the real admin management page |
| Top bar search field | Presentational only |
| Top bar notification bell | Presentational only |
| AI chat panel | Demo/local UI, not a live AI backend |
| Attorney header action buttons | Presentational only |

---

## 7. Known Notes and Caveats for Real Estate Expert Testing

1. The most complete end-to-end browser flows today are:
   - login
   - onboarding
   - dashboard
   - new transaction wizard
   - active transactions
   - transaction detail
   - documents
   - profile
   - admin task templates

2. The current app has both real workflows and intentional placeholders. When Real Estate Expert reviewers see a dedicated `Coming Soon` page, that is the expected current result rather than a broken route.

3. Several useful pages exist only behind direct links for now:
   - task detail
   - admin user detail
   - invite acceptance
   - reset password
   - email confirmation

4. Allow browser pop-ups and downloads before testing:
   - Print Report
   - transaction checklist print
   - CSV/Excel export

5. The main "Task Queue" page is still a placeholder, so most actual task testing should happen from:
   - expanded transaction cards
   - transaction detail > Tasks
   - direct `/tasks/<taskId>` route if you have a task ID

6. The real task-template management flow is the admin page at `/admin/task-templates`, not the static preview inside Settings.

7. Google OAuth and Gmail integration behavior are environment-dependent. If those services are not configured in the Real Estate Expert environment, graceful error states are acceptable and should be recorded as environment limitations rather than frontend navigation defects.

8. If the invite email URL format does not open the implemented invite page automatically, use `/invite/<token>` directly. The token itself is still what the frontend expects.
