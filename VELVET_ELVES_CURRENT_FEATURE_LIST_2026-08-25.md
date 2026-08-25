# Velvet Elves — Current Feature List

| | |
|---|---|
| **Prepared for** | Jake |
| **Prepared by** | Jan |
| **Date** | 25 August 2026 |
| **Purpose** | Enumerated inventory of features that exist in the shipping product today, for marketing videos and clips |
| **Rule** | Advertise only Part A. Do not film, name, or imply anything in Part B. |
| **Grounded in** | Live `velvet-elves-frontend` and `velvet-elves-backend` source as of this date — not the original requirements, not Help Center copy, not the marketing site |

---

## How to use this list

This is the list of what Velvet Elves actually does this week. Every item in **Part A** has a working screen and a working API. Film those. Name those.

**Part B** is the honesty list: placeholders, locked teasers, parked flags, and capabilities that exist only in the spec. If a clip would make a viewer think one of those is live, cut it.

Product names to say on camera (these are the labels in the app):

- **Aime** — the in-app assistant (not “the AI,” not “Elf”)
- **Needs You** — the residual queue
- **My Task Queue**, **All Documents**, **Email**, **Closing Calendar**
- **Transaction Coordinator** — the role (not “Elf”)
- **For Sale By Owner** — the FSBO role
- Create a deal with **Upload Transaction**, not “Accept & Create”

Hosts to film: `https://app.velvetelves.com` (app), `https://help.velvetelves.com` (Help Center), `https://velvetelves.com` (marketing site).

---

## What Velvet Elves is

Velvet Elves is AI-first real estate transaction management. You upload a signed contract packet. Aime reads it, you confirm what it found, and the platform builds the deal: task plan, timeline, compliance checklist, documents, contacts, and email. Humans approve what leaves the building.

Eight roles share one transaction record and see different shells: Agent, Transaction Coordinator, Team Lead, Attorney, Admin, Client, For Sale By Owner, and Vendor. Platform admin is a flag on a user, not a ninth role.

---

## Part A — Features that exist today

Advertise these. They are implemented in the frontend and backend.

### 1. Accounts, login, and onboarding

1. Email-and-password registration and sign-in.
2. Continue with Google (OAuth) on both login and register.
3. Forgot-password email and reset-password flow.
4. Email confirmation after signup.
5. Invite-token accept (`/invite/:token`) so invited people join without a public signup.
6. Public self-signup roles: **Agent**, **Team Leader**, **Transaction Coordinator**, **Admin**.
7. Invite-only roles: **Attorney**, **Client**, **For Sale By Owner**, **Vendor**.
8. Password policy on signup (length, upper, lower, digit, symbol) with a strength meter.
9. Terms of Service and Privacy Policy pages, required on signup.
10. Role-aware onboarding wizard after first login (skippable email and e-signature steps; connections can be finished later in Settings).
11. Tenant-owner onboarding includes an **Aime** step: Manual, Assisted, or Autopilot as the workspace default.
12. Tenant branding on the auth screens (logo and colors resolved from the domain).

### 2. Role-based workspaces

13. Eight stored roles with distinct shells and landings — Agent, Transaction Coordinator, Team Lead, Attorney, Admin, Client, For Sale By Owner, Vendor.
14. Internal shell (Agent / TC / Team Lead / Admin): dark sidebar, KPI tiles, today’s AI briefing (Critical / Needs Attention / On Track), ⌘K search, notification bell, **+ New Transaction**.
15. Attorney shell: caseload rail and a matter workspace (not the internal KPI mosaic).
16. Client shell: concierge portal (Home, Next Steps, Timeline, Documents, Updates).
17. FSBO shell: property-centric workspace (Home, My Properties, Documents, Payments when invoices exist, share-milestones CTA).
18. Vendor shell: scoped files / documents / tasks (Loan Files, Title Files, or Your Files by vendor type).
19. Portal users cannot reach internal routes by typing a URL.

### 3. Role dashboards

20. Solo Agent / Transaction Coordinator dashboard — health, action queue, production snapshot, priority deal cards.
21. Team Leader dashboard — intervention queue, agent board with drill-down, team financials and pipeline health.
22. Admin dashboard — organization snapshot, overnight automation health, users and invites shortcuts.
23. Attorney landing — opens the first matter or an empty state; counsel filters **Needs a call / Ready / All**.

### 4. New Transaction wizard (AI contract intake)

24. Full-screen **+ New Transaction** wizard at `/transactions/new`.
25. Four public phases: **Upload → Contract Details → Contacts & Fees → Verification**.
26. Multi-file upload (PDF, photos, Word). Combined scans can be split into separate documents by page range.
27. AI parse of the packet (Amazon Textract for OCR where needed, then two-pass extraction).
28. Extracted parties, property, price, fees, financing, and contractual dates, each with a **citation** (page and passage) so the user can verify in the document.
29. Missing fields are listed for **manual** fill-in or one-click choice rows (who orders title, cash appraisal, and similar).
30. Wizard **autosaves** as a draft; a half-finished intake is waiting where it was left (Drafts & Paused).
31. **Upload Transaction** creates the deal and generates the task plan, timeline, and compliance checklist from templates plus the dates just confirmed.
32. Six deal types: Buy-Fin, Buy-Cash, Sell-Fin, Sell-Cash, Both-Fin, Both-Cash.
33. Closing modes: attorney closing, title/escrow, shared approval.
34. Prepaid-deal paywall in the wizard when billing is on and the workspace has no remaining deals.

### 5. Pipeline — Active Transactions

35. Deal list at `/transactions` with sidebar views: Active, Drafts & Paused, Closed, All.
36. Health tabs on Active: All, Overdue, Due Today, Closing Soon, Needs Attention, In Inspection, On Track.
37. All-Transactions status tabs: Active, Incomplete, Paused, Completed, Closed, Terminated.
38. Sort by urgency, close date, client name, or price; search; Team Lead can filter by team member.
39. Collapsible deal cards: status, why-badges, AI next-step, milestone bar, key dates, grouped contacts.
40. Inline complete-a-task and edit-a-key-date from the expanded card.
41. Card actions: open workspace, documents, print closing checklist, history, communications, client access, client Q&A, invoice.
42. Export CSV, Export Excel, and Print Report from the list.
43. Sidebar KPI tiles: overdue tasks, closing this week, active deals, pipeline value.
44. Today’s AI Briefing chip filters the list to Critical / Needs Attention / On Track.

### 6. Transaction workspace and Aime

45. One page per deal at `/transactions/:id` with tabs: **Overview, Timeline, Compliance, Tasks, Documents, Contacts, Billing, Activity**, plus **Agent** and **Email** when the deal agent is on.
46. Header: property, stage, address, task progress, status change (Closed asks for post-closing feedback).
47. **Aime** (Ask Aime / Agent pane): plain-English Q&A about the deal, evidence citations, proposed actions that wait for approval.
48. Aime command helpers: `/` commands, `@` people, `#` items; drag a row into chat or **Ask AI** on a row.
49. Timeline: key dates with a **cascade preview** before a date change is committed (dependent deadlines shown, then applied).
50. Compliance: living required-document checklist — attach existing, upload new, mark not applicable; mismatch notice when an upload does not match the row.
51. Tasks: generated checklist with dependencies, statuses (Pending, In Progress, Completed, Blocked, Skipped), assignment, and “waiting on an earlier step.”
52. Documents on the deal: upload, preview, classify, version history, send for signature, generate from a fillable template.
53. Contacts on the deal: parties, vendors, teammates, client-access invites.
54. Billing on the deal: invoices tied to that transaction.
55. Activity: searchable history (audit + communications + task events) and an Automation lens with undo where the engine supports it.
56. **Print closing checklist** from the workspace (buyer/seller sheets fed by My Playbook / Team Playbook).
57. Pause, complete, close, or terminate a transaction; type switch updates tasks without wiping completed work.

### 7. Needs You, tasks, and deadlines

58. **Needs You** (`/needs-you`) — residual queue grouped by deal: Ready to send, AI proposal, Draft to review, Decision.
59. Batch **Send all ready** (confirm dialog names the recipient count) and batch approve; per-item approve / edit / discard still available.
60. **My Task Queue** (`/tasks/queue`) — cross-deal prioritized list; filters for overdue / due today / upcoming; type tabs (Documents, Communication, Milestones, and others); vendor-cart grouping; add-task; CSV export.
61. Task templates (Team Lead / Admin / owner) applied to new deals from the library.
62. Due-date reminders and assignment alerts (in-app and email, per notification preferences).
63. Overnight scheduler health visible in Settings → AI & Automation (automation is not a silent black box).
64. Completion methods on tasks include Phone Call, Email, DocuSign/E-Signature, In Person, Upload Document, Online Portal, AI Agent, Other.

### 8. Documents and e-signature

65. **All Documents** (`/documents`) is an AI-prioritized action queue, not a filing cabinet.
66. Tabs: AI priority, All docs, Missing, Pending review, Sent for sig, Signed.
67. Severity tiers with a suggested next action per row and a cleared-today ledger.
68. Preview, rename, reclassify; version history kept.
69. **DocuSign** send-for-signature from the Documents center and the deal; envelope status tracked in-app (Sent for sig / Signed).
70. **Document Templates**: upload fillable PDFs, map fields once, generate a flattened copy from deal data.
71. Required-document checklist per deal (missing / uploaded / waived).
72. Deletion is a reviewed action (flag for deletion / deletion-approvals panel), not a silent delete.
73. Request a missing file from a vendor; it arrives through the vendor portal.
74. Clients and FSBO sellers can upload and flag for deletion review; they cannot delete directly.

### 9. Email

75. Connect **Gmail** or **Outlook** from Settings → Email & E-signature (OAuth; Test connection; expired grant says reconnect without signing the user out of Velvet Elves).
76. Incoming mail is matched to the deal when the engine can identify it.
77. Intelligence → **Email** (`/ai-emails`): **Inbox, Outbox, Sent, Filtered**.
78. Aime drafts replies with a confidence score and sources. Nothing sends until a person acts.
79. Approve & send, edit first then send, regenerate, or discard.
80. **Send all ready** for pre-approved drafts, behind a confirm.
81. Filtered mail is envelope-only (no body) with Undo filter.
82. **Email Templates**: Starter (system), Shared (tenant), and Personal, with deal placeholders at send time.
83. Per-user **writing style** applied to drafts.
84. Every outbound message is logged to the deal and the Communication Audit.
85. Optional **Autopilot** (Admin sets Manual / Assisted / Autopilot in Settings → AI & Automation): named **welcome, title-order, and inspection-reminder** letters may send when confidence is high. Everything else waits in Email or Needs You. Wire and legal mail never auto-send. Deadlines never move themselves. Packet release stays human.

### 10. Closing Calendar

86. Closing Calendar (`/calendar`) with month and agenda views of inspection, appraisal, financing, and closing dates across deals.
87. Dates flow from intake / the deal — not a separate manual calendar to keep in sync.
88. Events deep-link to the transaction.
89. Push closings to **Google Calendar** or **Outlook Calendar** (connect, then Add my closings).

### 11. Contacts, clients, and vendors

90. **Contacts** directory — tenant-wide buyers, sellers, lenders, title, co-agents, inspectors, and others; search, filter, CSV export, add/edit/delete (by role).
91. **Clients** hub — cross-deal index of represented clients, with unanswered questions and uploads awaiting review.
92. **Vendor Directory** — searchable bench, categories, contact details, deals touched.
93. Assign vendors to a transaction so scheduling, documents, and email happen in context.
94. **Vendor Templates** — standard outreach the AI can send (order title, schedule inspection, and similar).
95. **Vendor Proposals** — inbound date/change proposals: accept, ask for clarification, or decline.
96. Public **Add a colleague** page (`/v/:token`) so a vendor contact can add a processor or partner without seeing the deal.
97. Optional AI auto-close of vendor task close-outs (Admin toggle, default off, confidence floor).

### 12. Invoices, payments, and workspace billing

98. **Invoices & Payments** (`/payments`): create, send, track Open / Paid / Draft / Void; payment history.
99. Secure **Stripe pay links** — client pays without a Velvet Elves login (`/pay/invoices/:id`).
100. Partial or full **refunds** on the record.
101. **Payment Access** — Admin/owner chooses which roles may invoice, refund, or (if ever unparked) pay out.
102. Client and FSBO invoice lists inside their portals when invoices exist.
103. Tenant **Billing** (when the credit-billing flag is on): per-deal fee, free first deal(s) as configured, prepaid-deal bundles, payment history.

### 13. Intelligence and analytics

104. **AI Suggestions** (`/ai-suggestions`) — next-best actions detected from real deal data, each with a reason, recommendation, and editable draft; accept or dismiss.
105. **Analytics** (`/reports`) — GCI, volume, pipeline, on-time close, days-to-close, task throughput, type mix, AI-suggestion acceptance, drift, over the actual closings; CSV export; personal vs team scope.
106. Aime as a floating assistant on internal screens (and Ask AI on attorney / FSBO surfaces).
107. Global search (⌘K / Ctrl+K) across transactions, tasks, contacts, and documents for internal and attorney roles.

### 14. Client portal (buyer / seller on an agent-led deal)

108. Concierge Home: next action, upcoming dates, documents needing attention, recent updates, agent card.
109. **Next Steps**, **Timeline** (milestones + key dates), **Documents** (view, download, upload; no delete), **Updates** (two-way Ask your team / Ask Velvet thread).
110. Add a date to Google Calendar or download an `.ics`.
111. Notification preferences (turn channels on/off).
112. Clients never see internal notes, task internals, or the staff workspace.

### 15. For Sale By Owner workspace

113. FSBO Home with properties, critical next steps derived from real missing docs/dates/tasks, days to close, live share-link count.
114. My Properties, property detail, Documents board (Missing / In progress / Uploaded / Verified / Complete).
115. Messages with assigned Velvet Elves support/guide contacts (portal-visible only).
116. **Share milestones** — create, expire, and revoke read-only public links.
117. Public milestone viewer (`/milestones/:shareToken`) — no login; opening it can notify the link creator.
118. FSBO invoices/pay when open invoices exist.
119. Plain-English Ask AI on the FSBO shell. FSBO users cannot edit back-office tasks, approvals, or delete documents directly.

### 16. Vendor portal

120. Vendor home: shared files, open documents, needs-attention cards (Loan / Title / File depending on vendor type).
121. Documents: view what was shared, upload requested files, request a document not yet shared.
122. Tasks: vendor-facing task list and close-out / timeline-adjustment replies.
123. No access to the full staff document center, internal notes, or the whole pipeline.

### 17. Attorney workspace

124. Matter workspace per assigned deal: command strip, checklist / timeline / activity, AI legal brief, people.
125. Upload legal packets (title commitments, settlement statements, affidavits, signed amendments, recording packets, and related types).
126. Human **approve** or **hold** on review items; every decision writes to communication history and the audit log.
127. **Releases** queue — release-ready vs released; send packet is always human-initiated (no AI auto-release).
128. **State rules** reference by state (closing mode, recording/disbursement notes as a reference surface).
129. Counsel Ask AI on the matter. Legal judgment, legal-equivalence decisions, and final packet release stay with the attorney.

### 18. Teams, settings, and playbooks

130. Settings hub (avatar menu): personal cards + workspace cards + platform cards, role-gated so a card never leads to Unauthorized.
131. **Profile** — photo, name, email, phone, bio, email signature.
132. **Notifications** — which reminders and assignment alerts you receive.
133. **Email & E-signature** — Gmail / Outlook + DocuSign (not shown to Attorney on this card; counsel uses the matter tools).
134. **My Playbook** — personal closing checklists, tagged notes, preferred vendors, resources (feeds Print closing checklist).
135. **Team Playbook** — shared checklists, notes, vendors, resources that members inherit.
136. **Help & Tour** — replay the guided product tour; link to the Help Center.
137. **Company** — brokerage name, plan, seats.
138. **Branding** — logo, brand color, display name (white-label across the app and auth).
139. **Users & Invites** — invite members, assign roles, manage access.
140. **Teams** and **Team Overview** — people and production across the team (Team Lead / Admin).
141. **Integrations & Webhooks** — outbound signed webhooks to a CRM/MLO/title URL, delivery log, test event; inbound **API keys** so an external system can push contacts.
142. **AI & Automation** — posture (Manual / Assisted / Autopilot), AI model, email-reply policy, always-approve rules for eligible low-risk actions, confidence gates, overnight health.
143. **Advertising** (tenant) — workspace ads on/off, house ads, performance.
144. Delete Organization (owner or platform admin).

### 19. Trust and oversight

145. Role-based access on every surface (see §2).
146. **Communication Audit** — searchable cross-deal message log; CSV export-request workflow and retention purge (Admin).
147. **Audit Log** — timestamped actions with before/after; CSV export (Admin).
148. In-app **notifications** (bell + `/notifications`) for overdue / today / upcoming work; mark read.
149. Immutable communication log on each deal (who, what, when, direction).

### 20. Help Center, tour, and public sites

150. In-app guided **tour** (role-aware; skippable; replay from Settings → Help & Tour).
151. Public **Help Center** at help.velvetelves.com — collections, articles, search, article feedback, and an Ask widget grounded in published articles.
152. In-app Help Center authoring for platform admins (collections, articles, preview, feedback, settings).
153. Marketing website (velvetelves.com) — product, features, how it works, role pages, FAQ, demo CTA, create-account, waitlist/lead capture into this same backend.
154. Public **Advertise** storefront (`/advertise`) for sponsored placements (packages, checkout, complete) — a live VE surface, not a typical agent-demo clip.

### 21. Platform operations (Velvet Elves staff — not customer-demo clips)

These exist in production for Velvet Elves operators (`is_platform_admin`). Do not present them as brokerage features unless the video is about running Velvet Elves itself.

155. Tenants, cross-tenant users, registration alerts, waitlist, AI usage, costs & pricing, platform billing, platform advertising, Help Center CMS.

---

## Part B — Do not advertise

Do not film these as available. Do not say “coming soon” on camera unless Jake explicitly wants a labeled teaser. Default: omit.

| # | Item | Why it is not fair to advertise |
|---|---|---|
| B1 | **SMS** | Channel badge and marketing card are labeled coming soon. No Twilio send path in the product. |
| B2 | **Voice / call transcription / Aime microphone** | Voice input button is disabled (“coming soon”). No live call/voicemail product. |
| B3 | **AI Coach** | Team Lead sidebar item is a **locked teaser**. `AI_COACH_ENABLED = false`. No coaching workflow, no $79 add-on billing. |
| B4 | **Native / mobile app** | Web app only. Responsive desktop-first; not a store app. |
| B5 | **Two-factor authentication** | In the original requirements. **Not in the source.** Email/password + Google only. |
| B6 | **Microsoft sign-in** on login/register | Only **Continue with Google** is on those screens. Outlook is for **mailbox** connect, not account login. |
| B7 | **iCloud Mail** as an inbox the user can connect in Settings | Backend connector exists; Settings → Email & E-signature shows **Gmail and Outlook only**. Do not say “connect iCloud.” |
| B8 | **Generic IMAP/SMTP** | Explicitly out of MVP. |
| B9 | **Follow Up Boss** (or any named CRM) | **Generic webhooks** and inbound API keys only. No FUB (or other named) integration. |
| B10 | **Commission payouts / Stripe Connect payouts** | UI and API exist behind `ve_commission_payouts_v1`, which is **off by default**. Routes 404 while parked. Do not show `/payments/payouts`. |
| B11 | **Internal Sharing page** (`/sharing`) | Placeholder “Coming soon.” **Do** advertise FSBO share-milestone links and the public milestone viewer — those work. |
| B12 | **AI public-source search** that fills missing contract fields | The button/API exist; the service returns an **empty list** unless a provider implements search (none does). Manual entry works. Do not say “it looks the missing info up on the web.” |
| B13 | **AI inventing the task checklist** | Task generation is from the **template library + confirmed dates**. `recommend_task_changes` is hard-wired to return no suggestions. |
| B14 | **MLS / Active Listings** | MLS feed deferred. No Active Listings nav item. |
| B15 | **Attorney Recording Calendar as live jurisdiction data** | The page exists; it shows an honesty notice that recording-window data is **not wired per jurisdiction**. Do not claim a live recording calendar. |
| B16 | **Autopilot as “it sends all the emails”** | Autopilot is real, but **only** the named welcome, title-order, and inspection-reminder letters, and only above the confidence floor. Do not imply blanket auto-send. |
| B17 | **Aime changing the file without approval** | Default story: Aime proposes, the person approves. Always-approve rules exist for a **short list of low-risk actions** the Admin opted in. Wire mail, legal calls, waives, and packet release never auto-run. |
| B18 | **User dark mode** | Theme is **tenant branding** (logo/color), not a personal dark/light toggle. |
| B19 | **Orphan-accounts marketing dashboard, custom milestone videos, concierge upsell, FSBO self-listing** | Post-MVP roadmap only. |
| B20 | **Supabase Row Level Security as the customer security story** | App-layer RBAC is what ships. RLS activation is still listed as not in delivery. |

---

## Suggested clip map (Part A only)

Use this as a shot list. One claim per clip; the screen must match the words.

| Clip | Say this | Show this |
|---|---|---|
| 1 | Drop in the contract. Confirm what it read. | `/transactions/new` — four phases, then **Upload Transaction** |
| 2 | One page per deal, with Aime beside it. | `/transactions/:id` — Overview + Aime answering with a citation |
| 3 | Change a date; see what else moves before you commit. | Workspace **Timeline** cascade preview |
| 4 | The queue that needs a human. | `/needs-you` — Send all ready / approve a draft |
| 5 | Everything due, across every file. | `/tasks/queue` |
| 6 | Documents ranked by what blocks closing. | `/documents` — AI priority |
| 7 | Send for signature without leaving the deal. | DocuSign send + Sent for sig tab |
| 8 | Mail is matched and drafted; you approve. | `/ai-emails` — Inbox → Approve & send → Sent |
| 9 | Closing dates on the calendar you already use. | `/calendar` + Google or Outlook connect |
| 10 | Clients see progress, not your notes. | `/client/home` (or Next Steps / Documents) |
| 11 | FSBO sellers share a live milestone link. | FSBO Share milestones → `/milestones/:token` |
| 12 | Vendors upload into their own portal. | `/portal/vendor` |
| 13 | Attorneys release packets; AI never does. | `/attorney/releases` + human Send |
| 14 | Invoices clients pay on a link. | `/payments` + public `/pay/invoices/:id` |
| 15 | The whole trail is searchable. | Communication Audit or deal Activity |

---

## Source notes (for Jan, not for camera)

Verified against, among others:

- Frontend routes: `velvet-elves-frontend/src/App.tsx`, `layouts/dashboardShellConfig.ts`, `pages/settings/settingsCards.ts`
- Wizard phases: `components/wizard/wizardTypes.ts` (`WIZARD_PHASES`)
- Workspace tabs: `pages/transactions/TransactionWorkspacePage.tsx`
- Email UI: `pages/AiEmailReviewPage.tsx`, `components/settings/ConnectionsPanel.tsx` (Gmail + Outlook + DocuSign only)
- Autopilot bounds: `pages/admin/AdminAIGovernancePage.tsx` copy + `app/services/automation_posture_service.py`
- Parked payouts: `app/tests/test_payout_parking.py`, `ve_commission_payouts_v1` default off
- Empty public-source search: `app/services/ai_service.py` (`search_public_source`)
- Empty task-invention path: `recommend_task_changes` returns `suggestions=[]`
- AI Coach off: `pages/AISuggestionsPage.tsx` (`AI_COACH_ENABLED = false`)
- Sharing placeholder: `pages/SharingPage.tsx` (`ComingSoonPage`)
- FSBO share is live: `components/fsbo/FsboShareManagementModal.tsx` + `pages/public/MilestoneViewerPage.tsx`
- Backend surface: `app/api/v1/router.py`

If a later deploy adds SMS, 2FA, iCloud in Settings, named CRM, or unparks payouts, this file must be revised before those claims go on camera.
