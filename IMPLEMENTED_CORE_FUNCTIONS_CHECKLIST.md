# Implemented core functions — testing checklist

**Date:** 2 Sep 2026  
**Where:** `https://app.stage.velvetelves.com`  
**What this is:** a list of product functions that are in the running app, for one-by-one testing. It is not a CASA evidence pass and it is not a rewrite of the older July core-features guide.

Against each line write **Pass**, **Fail**, **Needs work**, or **Skip**, plus a short note if something is off.

Sign in the usual way so you can reach the screens. Do **not** re-test login lockout, MFA, cookies, TLS, injection, or tenant IDOR. Those belong to the CASA pack and must stay untouched.

---

## Out of this list (do not test here)

**CASA AL1 (48 TAC rows).** Auth hardening, session and cookie flags, password storage, invite/reset token crypto, platform-admin MFA, OAuth PKCE/state as a security check, CSRF, IDOR, XSS, SQLi, SSRF, LFI, malicious uploads, TLS, secrets, debug off, logout storage wipe.

**Not shipped, or parked.** Native mobile. Generic IMAP/SMTP. Named CRM (Follow Up Boss). AI Coach (locked teaser). Commission / Stripe Connect payouts. Active Listings nav. Client-facing Aime chat. Next-day follow-up nags. Cloud-on-title summary. Year-end exemption blast. Sharing as a standalone page.

**Safety while you work the list.** Do not Send, Send all ready, confirm Run AI tasks, Disconnect a mailbox, or Change status on a live file. Prefer plus-addresses you own. Do not staff `elf@cbstiles.com` on QA files.

---

## How to use this

Work top to bottom. One function per line. The Aime numbered features (1–32) sit under **Aime and automation** as the functions they cover, not as a second document.

Older companions, if you need steps later: `CORE_FEATURES_TESTING_GUIDE.md`, `WIZARD_TESTING_GUIDE.md`, `TRANSACTION_WORKSPACE_TESTING_GUIDE.md`, `AIME_AI_AUTOMATION_TESTING_GUIDELINES_2026-08-18.md`.

---

## 1. Getting in (product only)

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 1.1 | Register a new workspace (name, role, org, email) | `/register` | | |
| 1.2 | Accept an invite and set a password | `/invite/:token` | | |
| 1.3 | Sign in with email and password | `/login` | | |
| 1.4 | Sign in with Google | `/login` | | |
| 1.5 | Finish onboarding (profile, company, skip connections) | `/onboarding` | | |
| 1.6 | Role landing after sign-in (Agent / Team Lead / Admin / Attorney / Client / FSBO / Vendor) | `/dashboard` | | |
| 1.7 | Log out from the avatar menu | Avatar → Log out | | |

---

## 2. Shell, search, and briefing

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 2.1 | Sidebar groups and live counts | App shell | | |
| 2.2 | KPI tiles (overdue, closing this week, active deals, pipeline) | Sidebar | | |
| 2.3 | Today's AI Briefing filters the deal list | Topbar chip | | |
| 2.4 | Command search finds a deal, task, contact, and document | ⌘K / Ctrl+K | | |
| 2.5 | Notification bell, mark read, View all | Topbar bell | | |
| 2.6 | Ask AI on the dashboard (overdue, closing this week, focus) | Ask AI | | |
| 2.7 | Agent / TC dashboard | `/dashboard/agent` | | |
| 2.8 | Team Lead dashboard | `/dashboard/team` | | |
| 2.9 | Admin dashboard (including Terminated tile) | `/dashboard/admin` | | |

---

## 3. New Transaction wizard

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 3.1 | Open the full-screen wizard | `/transactions/new` | | |
| 3.2 | Fast intake from an uploaded contract | Confirm Details | | |
| 3.3 | Skip upload and enter the file by hand | Wizard | | |
| 3.4 | Representation: Buyer, Seller, Both | Who are you representing | | |
| 3.5 | Financing: mortgage vs cash | Contract details | | |
| 3.6 | Cash appraisal question (only on cash) | Contract details | | |
| 3.7 | Title ordered by us vs the other side | Who orders title | | |
| 3.8 | Closing mode: title/escrow vs attorney | Contract details | | |
| 3.9 | Inspection, HOA, home warranty, occupancy | Contract details | | |
| 3.10 | Preview the generated task list before create | Review tasks | | |
| 3.11 | Create the file and land in the workspace | Review → create | | |
| 3.12 | Draft / discard / resume an unfinished wizard | `/transactions/new` | | |

---

## 4. Deal list (Active Transactions)

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 4.1 | Active / Drafts & Paused / Closed / All | Sidebar Deals | | |
| 4.2 | Filter tabs (All, Overdue, Due Today, Needs Attention, Closing Soon, In Inspection, On Track, Unhealthy) | `/transactions` | | |
| 4.3 | Sort by urgency, close date, client name, price | Deal list | | |
| 4.4 | Team-member filter (Team Lead / Admin) | Deal list | | |
| 4.5 | Expand a card: tasks, key dates, contacts | Deal card | | |
| 4.6 | Complete a task from the card | Deal card | | |
| 4.7 | Edit a key date from the card | Deal card | | |
| 4.8 | Open workspace, docs, print checklist, history, comms, client access, Q&A, invoice | Card actions | | |
| 4.9 | Export CSV / Excel / print report | Deal list header | | |
| 4.10 | Stage pill (Critical / Needs Attention / On Track / Unhealthy) | Card header | | |
| 4.11 | Pause, complete, close, or terminate a **QA** file | Card / workspace | | |
| 4.12 | Delete a **QA** file (confirm names the property) | Card | | |

---

## 5. Deal workspace

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 5.1 | Overview (parties, dates, money, posture chip) | `/transactions/:id` | | |
| 5.2 | Timeline | `?tab=timeline` | | |
| 5.3 | Compliance / document requirements | `?tab=compliance` | | |
| 5.4 | Tasks (work queue, Add Task, Show completed) | `?tab=tasks` | | |
| 5.5 | Documents on the file | `?tab=documents` | | |
| 5.6 | Contacts / parties on the file | `?tab=contacts` | | |
| 5.7 | Billing / invoices on the file | `?tab=billing` | | |
| 5.8 | Activity / history | `?tab=activity` | | |
| 5.9 | Email on the file (Inbox / drafts / sent) | `?tab=email` | | |
| 5.10 | Pin Manual / Assisted / Autopilot on the deal | Posture chip | | |
| 5.11 | Ask AI in the workspace (deal context) | Workspace | | |
| 5.12 | Print / closing checklist | Workspace | | |

---

## 6. Tasks

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 6.1 | Library generates the right rows for Buy-Fin / Buy-Cash / Sell-Fin / Sell-Cash / Both-Fin / Both-Cash | New file | | |
| 6.2 | Dual (Both): buyer and seller targets both populate; co-op-target rows do not | Both file | | |
| 6.3 | Dual: two Deliver Title rows (buyer + seller); buyer Deliver Utility Info; no co-op utility | Both file | | |
| 6.4 | Order Title vs Confirm Title Order from who orders title | New file | | |
| 6.5 | Cash Appraisal Ordered / Completed (buyer on Buy-Cash, co-op on Sell-Cash) | Cash file | | |
| 6.6 | Listing Deliver Utility Info is one letter to the co-op | Sell file | | |
| 6.7 | Order Home Warranty is an internal reminder, not a vendor letter | Tasks | | |
| 6.8 | Closing Gift is one row | Tasks | | |
| 6.9 | No seller Inspection Completed on a new listing | Sell file | | |
| 6.10 | Add a manual task; similarity check (Add / Combine / Disregard) | Add Task | | |
| 6.11 | Edit due date (basis or calendar date) | Task row | | |
| 6.12 | Change status (Pending / In progress / Completed / Skipped) on a **QA** task | Status pill | | |
| 6.13 | Email transaction party / Complete this task plan | Task kebab | | |
| 6.14 | Block Send when the purchase agreement is missing (Order Title, LO Welcome) | No-contract file | | |
| 6.15 | Named emails stay on the open list on Manual and Assisted | Tasks tab | | |
| 6.16 | My Task Queue groups (Critical / Attention / On track / Playbook) | `/tasks/queue` | | |
| 6.17 | Complete or email a task from the queue | `/tasks/queue` | | |

---

## 7. Documents and compliance

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 7.1 | Upload to a deal and classify type | Documents tab / All Documents | | |
| 7.2 | AI / Textract extract fills dates, price, parties | After upload | | |
| 7.3 | Preview and download | Document row | | |
| 7.4 | Rename, reclassify, reassign, version history | Document row | | |
| 7.5 | Archive and restore | Documents | | |
| 7.6 | Missing / AI priority / Cleared Today | `/documents` | | |
| 7.7 | Send for signature (DocuSign); resend / void | Documents | | |
| 7.8 | Email a document from the file | Documents | | |
| 7.9 | Generate a fillable PDF from a document template | Deal + Settings templates | | |
| 7.10 | Deletion queue approve / reject (Team Lead) | All Documents | | |

---

## 8. People: contacts, clients, vendors

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 8.1 | Directory search and type filters | `/contacts` | | |
| 8.2 | Contact detail and deals they sit on | `/contacts/:id` | | |
| 8.3 | Add / edit a party on the file (buyer, seller, co-op, lender, title) | Contacts tab | | |
| 8.4 | Expand a contact card (compose, copy, open profile) | Contacts tab | | |
| 8.5 | Clients hub (portal access, to-answer / to-review) | `/clients` | | |
| 8.6 | Grant or revoke client portal access | Deal card / Clients | | |
| 8.7 | Vendor Directory search and category | `/vendors` | | |
| 8.8 | Vendor card (contacts, deals, details) | Vendor Directory | | |
| 8.9 | Vendor proposals (pending / decided) | `/vendor-proposals` | | |
| 8.10 | Colleague invite public link | `/v/:token` | | |

---

## 9. Aime and automation

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 9.1 | Connect Gmail or Outlook; Test connection (sends nothing) | `/settings/connections` | | |
| 9.2 | Connect DocuSign | `/settings/connections` | | |
| 9.3 | Workspace How it runs: Manual / Assisted / Autopilot | Settings → AI & Automation | | |
| 9.4 | Overnight switches (hourly, named emails, Aime signature, inspection reminder) | How it runs | | |
| 9.5 | Preview next run (Got it; sends nothing) | AI & Automation | | |
| 9.6 | Draft due emails (writes drafts only) | AI & Automation | | |
| 9.7 | Needs You queue, filters, deal grouping | `/needs-you` | | |
| 9.8 | Recovery on the first screen (Add contact, Upload document, Change due date) | Needs You | | |
| 9.9 | Give this back to the AI / Try now (this deal only) | Needs You | | |
| 9.10 | Prepared drafts and Send all ready (ready count; do not confirm on live files) | Needs You / Email | | |
| 9.11 | Manual: named letters do not send | Manual deal | | |
| 9.12 | Assisted: named letter waits for a tap | Assisted deal | | |
| 9.13 | Autopilot: named letter may send once (Preview first; plus-addresses only) | Autopilot **QA** file | | |
| 9.14 | No guessed To when the party has no email | File with blank buyer | | |
| 9.15 | Inspection response reminder prints the file date (not TBD) | Tasks | | |
| 9.16 | Confirm Title Order courtesy names the co-op | Title-other file | | |
| 9.17 | Closing-information letters do not attach the Closing Disclosure | Tasks | | |
| 9.18 | Inbound mail lands on the right deal and kind (money, date, document) | Email → Inbox | | |
| 9.19 | Dates do not move themselves from an email | Deal dates | | |
| 9.20 | Digest / Fine-tune / paused files | AI & Automation | | |
| 9.21 | Copy never says the letter was written by AI | Any plan | | |
| 9.22 | Completed vs Terminated copy | Admin dashboard / status | | |

---

## 10. Email review

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 10.1 | Outbox lists prepared mail with counts | `/ai-emails` | | |
| 10.2 | Open a draft (To, Cc, subject, body, attachments) | Email | | |
| 10.3 | Edit To / Cc on the draft | Email | | |
| 10.4 | Approve & send / Send edited (plus-addresses only) | Email | | |
| 10.5 | Regenerate a reply | Email | | |
| 10.6 | Discard a draft | Email | | |
| 10.7 | Inbox tab, deal filter, search | `/ai-emails` | | |
| 10.8 | “Not mail I need” / delete | Email | | |
| 10.9 | Email templates create and use | `/email-templates` or Settings | | |

---

## 11. Calendar

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 11.1 | Month view of key dates | `/calendar` | | |
| 11.2 | Agenda view | `/calendar` | | |
| 11.3 | Closings only | `/calendar` | | |
| 11.4 | Month nav and Today | `/calendar` | | |
| 11.5 | Connect Google or Outlook calendar; Add my closings | `/calendar` | | |

---

## 12. Invoices and billing

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 12.1 | Create an invoice from a deal | Card / Billing tab | | |
| 12.2 | Invoices & Payments list and search | `/payments` | | |
| 12.3 | Invoice detail | `/payments/invoices/:id` | | |
| 12.4 | Public pay link | `/pay/invoices/:id` | | |
| 12.5 | Workspace billing: per-deal fee | `/organization` | | |
| 12.6 | Creating a deal charges once | Admin | | |
| 12.7 | Delete inside the refund window refunds | Admin, **QA** file | | |
| 12.8 | Pay ahead / prepaid deal credits | `/organization` | | |
| 12.9 | Payment Access (who can invoice / refund) | Settings | | |

Commission payouts are parked. Do not look for Stripe Connect payouts.

---

## 13. Settings, branding, and playbooks

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 13.1 | Settings hub search finds a card | `/settings` | | |
| 13.2 | Profile (photo, name, phone, signature) | `/settings/account` | | |
| 13.3 | Notification preferences and morning digest opt-in | `/settings/notifications` | | |
| 13.4 | My Playbook (checklists, notes, vendors, resources) | `/settings/my-playbook` | | |
| 13.5 | Document templates (fillable PDFs) | `/settings/document-templates` | | |
| 13.6 | Help & Tour replay | `/settings/help` | | |
| 13.7 | Company name, plan, seats | `/organization` | | |
| 13.8 | Branding (logo and colour on app and outbound mail) | `/organization` | | |
| 13.9 | Vendor email templates | `/admin/vendor-templates` | | |
| 13.10 | Team Playbook (Team Lead) | Team Settings | | |
| 13.11 | Integrations & webhooks | `/admin/integrations` | | |
| 13.12 | Task library (use-case list, targets, Dual flags) | `/admin/task-templates` | | |
| 13.13 | Import task templates | `/admin/task-templates/import` | | |

---

## 14. Team and oversight

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 14.1 | Team Overview (people and production) | `/team` | | |
| 14.2 | Create a team, members, invite | `/admin/teams` | | |
| 14.3 | Users & invites | `/admin/users` | | |
| 14.4 | Change a member’s role | Users | | |
| 14.5 | Deactivate a member | Users | | |
| 14.6 | Transfer workspace ownership | `/organization` | | |
| 14.7 | Communication Audit and CSV | `/admin/communications` | | |
| 14.8 | Audit Log (readable rows) | `/admin/audit-logs` | | |
| 14.9 | Advertising admin (storefront copy) | `/admin/advertising` | | |

---

## 15. Intelligence

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 15.1 | Analytics (GCI, volume, goals, export PDF) | `/reports` | | |
| 15.2 | AI Suggestions: why, act, dismiss | `/ai-suggestions` | | |

---

## 16. Attorney workspace

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 16.1 | Caseload rail (Needs a call / Ready / All) | `/dashboard/attorney` | | |
| 16.2 | Matter workspace | `/transactions/:id` | | |
| 16.3 | Upload legal packet | Attorney CTA | | |
| 16.4 | Recording calendar | `/attorney/recording-calendar` | | |
| 16.5 | Releases | `/attorney/releases` | | |
| 16.6 | State rules | `/attorney/state-rules` | | |
| 16.7 | Ask AI stays inside counsel guardrails (no final legal position) | Matter | | |

---

## 17. Client portal

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 17.1 | Home | `/client/home` | | |
| 17.2 | Next Steps | `/client/next-steps` | | |
| 17.3 | Timeline | `/client/milestones` | | |
| 17.4 | Documents (view / download) | `/client/documents` | | |
| 17.5 | Updates | `/client/updates` | | |
| 17.6 | Client invoices | `/client/invoices` | | |
| 17.7 | Profile / Help Center from the account chip | Client shell | | |

---

## 18. FSBO workspace

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 18.1 | Home | `/fsbo` | | |
| 18.2 | My Properties | `/fsbo/properties` | | |
| 18.3 | Property detail | `/fsbo/properties/:id` | | |
| 18.4 | Documents | `/fsbo/documents` | | |
| 18.5 | Milestones | `/fsbo/milestones` | | |
| 18.6 | Invoices (if any are open) | `/fsbo/invoices` | | |
| 18.7 | Share milestones modal | Footer CTA | | |
| 18.8 | FSBO settings | `/fsbo/settings` | | |

---

## 19. Vendor portal

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 19.1 | Overview by scope (loan / title / your files) | `/portal/vendor` | | |
| 19.2 | File detail | `/portal/vendor/files/:id` | | |
| 19.3 | Documents | `/portal/vendor/documents` | | |
| 19.4 | Tasks | `/portal/vendor/tasks` | | |
| 19.5 | Settings | `/portal/vendor/settings` | | |
| 19.6 | Upload a document from the portal | Vendor CTA | | |

---

## 20. Public and Help

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 20.1 | Public milestone viewer | `/milestones/:token` | | |
| 20.2 | Advertise storefront | `/advertise` | | |
| 20.3 | Help Center articles (published) | help.velvetelves.com | | |
| 20.4 | Terms and Privacy | `/terms` `/privacy` | | |

---

## 21. Velvet Elves operator (optional)

Skip unless you are testing the vendor console. Do **not** exercise platform MFA, suspend, or cross-tenant IDOR (CASA).

| # | Function | Where | Result | Notes |
|---|---|---|---|---|
| 21.1 | Tenants list (read) | `/platform/tenants` | | |
| 21.2 | Users list (read) | `/platform/users` | | |
| 21.3 | Registration alerts | `/platform/users/alerts` | | |
| 21.4 | Waitlist | `/platform/waitlist` | | |
| 21.5 | AI usage | `/platform/ai-usage` | | |
| 21.6 | Costs & pricing | `/platform/costs` | | |
| 21.7 | Help Center authoring | `/platform/help` | | |

---

## Rollup

| Area | Pass | Fail | Needs work | Skip |
|---|---|---|---|---|
| 1 Getting in | | | | |
| 2 Shell | | | | |
| 3 Wizard | | | | |
| 4 Deal list | | | | |
| 5 Workspace | | | | |
| 6 Tasks | | | | |
| 7 Documents | | | | |
| 8 People | | | | |
| 9 Aime | | | | |
| 10 Email | | | | |
| 11 Calendar | | | | |
| 12 Invoices | | | | |
| 13 Settings | | | | |
| 14 Team | | | | |
| 15 Intelligence | | | | |
| 16 Attorney | | | | |
| 17 Client | | | | |
| 18 FSBO | | | | |
| 19 Vendor | | | | |
| 20 Public / Help | | | | |
| 21 Operator (optional) | | | | |

**What to test next (after this pass):**

>
>
