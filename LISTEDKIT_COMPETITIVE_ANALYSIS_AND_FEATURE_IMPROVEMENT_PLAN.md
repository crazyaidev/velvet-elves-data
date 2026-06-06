# ListedKit Competitive Analysis And Feature Improvement Plan

**Created:** 2026-06-05  
**Project goal:** Build a platform superior to ListedKit.  
**Scope reviewed:** Public ListedKit positioning as of 2026-06-05, the documented Velvet Elves product requirements and milestone plans in `velvet-elves-data`, and the current frontend/backend source in `velvet-elves-frontend` and `velvet-elves-backend`.

---

## 1. Executive Summary

ListedKit's public product is extremely focused: an AI transaction coordinator, Ava, that reads contracts, monitors inboxes, builds timelines, drafts/replies to emails, syncs calendars, supports SMS questions, and surfaces what is urgent across a transaction pipeline. Its advantage is not only feature breadth; it is the simplicity of the promise: "connect email, upload contract, Ava handles the rest." The website claims any-state contract reading, handwritten support, no setup/templates, deal-aware inbox matching, state-aware timeline building, Gmail/Outlook/Follow Up Boss/calendar integrations, SMS access, unlimited team members, and pay-per-use pricing.

Velvet Elves is already architecturally broader than ListedKit. The source code shows a multi-role, multi-tenant platform with transactions, tasks, task templates, document management, AI parsing, contract resolution, AI email review, vendor communications, client and FSBO portals, attorney workspaces, payments, advertising hooks, calendar push, CRM/webhook infrastructure, tenant branding, and platform administration. This is more than an AI TC; it is closer to a real estate closing operating system.

The strategic challenge is that ListedKit owns the most important wedge more clearly: AI-assisted intake + inbox monitoring + dated timeline/task generation. Velvet Elves can beat it, but only if the core transaction automation becomes demonstrably reliable, fast, and easy enough to show in one live demo. The June 5 task-engine fix has moved Velvet Elves much closer: the code now includes task preview, anchor-date seeding, executable conditions, dual-agency task families, multi-predecessor dates, business-day roll-forward, and a wizard Review Tasks step. The next phase should harden that into an editable, source-cited, benchmarked transaction-intake experience.

**Recommended product position:**  
Velvet Elves should not position itself as "another AI transaction coordinator." It should position as **the AI-assisted real estate closing operating system for brokerages, coordinators, attorneys, teams, clients, FSBO sellers, and vendors**. That keeps ListedKit's strongest promise, then expands beyond it into role-specific workspaces, external portals, payments, vendor workflows, white-label tenancy, and compliance-grade auditability.

---

## 2. Evidence Base

### 2.1 Public ListedKit Sources Consulted

The public competitive assessment is based on these current ListedKit / ListedKit-adjacent sources:

| Source | URL | Notable evidence |
| --- | --- | --- |
| ListedKit home page | https://www.listedkit.com/ | Ava reads inboxes and contracts, extracts dates/parties/contingencies, tracks urgent work, supports skills such as email, compliance, todos, calendar sync, SMS, and inbox-by-deal. |
| ListedKit features page | https://www.listedkit.com/features | Detailed feature list: inbox reading, any-state contract reading, state-aware timeline building, email automation, SMS texting, calendar sync, team collaboration, smart document reading, pipeline deal flow, integrations with Gmail, Outlook, Follow Up Boss, and calendar. |
| ListedKit pricing page | https://www.listedkit.com/pricing | $14.99 per transaction/contract setup, first free, no monthly fee, credits never expire, unlimited team members. |
| ListedKit state guides | https://www.listedkit.com/state | Public 50-state transaction-guide content with state-specific requirements. |
| ListedKit team solution | https://www.listedkit.com/solutions/teams | Team hierarchy and role access: Super Admin, Admin, User, task delegation, access controls. |
| ListedKit TC solution | https://www.listedkit.com/solutions/transaction-coordinators | Claims around 40 active deals, every email in the right file, timeline/checklist in under 2 minutes, and scaling TC capacity. |
| ListedKit broker solution | https://www.listedkit.com/solutions/real-estate-broker-software | Broker/compliance positioning: missing signatures, date inconsistencies, incomplete fields caught at intake. |
| ListedKit attorney solution | https://www.listedkit.com/solutions/real-estate-attorney-software | Attorney review workflows, version control, document comparison, legal timeline management, attorney-state support. |
| Inman tech review | https://www.inman.com/2025/08/15/all-new-listedkit-is-giving-ai-the-wheel-in-transaction-management-tech-review/ | Third-party validation that ListedKit devises/publishes timelines from documents and supports chat about documents/deal points in a single UI. |

### 2.2 Velvet Elves Local Sources Consulted

Primary documents:

- `requirements.txt`
- `SYSTEM_DESIGN.md`
- `milestones.txt`
- `FRONTEND_UI_WORKFLOW_LOGIC.md`
- `STYLE_GUIDE.md`
- `SMART_TRANSACTION_PROCESSING_AND_TASK_ENGINE_PLAN.md`
- `TRANSACTIONS_PAGE_COMPLETION_PLAN.md`
- `MILESTONE_4_2_AI_EMAIL_WORKFLOW.md`
- `MILESTONE_4_3_IMPLEMENTATION_PLAN.md`
- `MULTI_TENANCY_IMPLEMENTATION_PLAN.md`
- `MILESTONE_5_1_IMPLEMENTATION_PLAN.md`
- `MILESTONE_5_2_IMPLEMENTATION_PLAN.md`
- `MILESTONE_5_3_IMPLEMENTATION_PLAN.md`
- `MILESTONE_6_1_IMPLEMENTATION_PLAN.md`
- `MILESTONE_6_2_IMPLEMENTATION_PLAN.md`
- `ATTORNEY_WORKSPACE_PLAN.md`
- `FSBO_WORKSPACE_PLAN.md`
- `CLIENT_WORKSPACE_PLAN.md`
- `ROLE_DASHBOARDS_DESIGN_UPDATE_PLAN.md`
- `ALL_DOCUMENTS_COMPLETION_PLAN.md`
- `ALL_DOCUMENTS_WORKFLOW_COMPLETION_PLAN.md`

Source-code areas reviewed:

- Backend router registration: `velvet-elves-backend/app/api/v1/router.py`
- Backend README and current API/service files under `velvet-elves-backend/app`
- Frontend routes: `velvet-elves-frontend/src/App.tsx`
- Frontend route constants: `velvet-elves-frontend/src/utils/constants.ts`
- New transaction wizard and task review: `src/components/wizard/*`, `src/hooks/useWizardApi.ts`
- Current API/service surfaces for AI, tasks, documents, email, calendar, payments, advertising, tenant management, client/FSBO/attorney/vendor workspaces.

---

## 3. ListedKit Strengths

### 3.1 Clear Core Promise

ListedKit's strongest product advantage is clarity. Ava is presented as an AI transaction assistant that reads inboxes and contracts, knows every active deal, and tells the user what is urgent. The positioning is concrete and easy to demo:

1. Connect email.
2. Upload a contract.
3. Ava reads it.
4. Ava builds the timeline/checklist.
5. Ava files related emails into the right deal.
6. Ava drafts/replies/syncs reminders.

This "single loop" is more immediately legible than a broad platform with many surfaces.

### 3.2 Contract Intelligence Is The Wedge

ListedKit claims it reads purchase agreements from any state, including handwritten contracts, and extracts every date, party, and contingency automatically with no templates or pre-setup. It also claims timeline/checklist generation in under 2 minutes and contract timeline building in 60 seconds in public-facing messaging.

Why this matters: in transaction coordination, a user will forgive many missing secondary modules if the first upload reliably creates the correct dates and tasks.

### 3.3 Inbox-To-Deal Matching

ListedKit prominently claims Ava can read incoming email and match each email to the right deal even when the property address is not in the subject line. This is a major workflow win because TC work is inbox-driven, not only document-driven.

### 3.4 "What Is Urgent Today" Across The Pipeline

ListedKit does not just say it stores tasks; it says Ava knows all open deals and surfaces what needs attention today. That makes the product feel like a decision engine, not a database.

### 3.5 Integrated Action Channels

ListedKit publicly lists:

- Gmail and Outlook
- Follow Up Boss
- Calendar
- Email drafting/replies
- Scheduled reminders
- SMS texting to ask Ava questions
- Calendar sync to Google Calendar or Outlook

This creates a high-convenience perception: Ava works where coordinators already work.

### 3.6 Team And Role Collaboration

ListedKit exposes team collaboration and role concepts publicly. Its team solution describes Super Admin, Admin, and User access, plus task delegation and reports. Pricing also advertises unlimited team members on a shared credit pool.

### 3.7 Public Proof And Market Confidence

ListedKit has stronger public proof than Velvet Elves currently appears to have:

- Customer testimonials.
- Logos on public pages.
- Public 50-state guides.
- Pricing page.
- "First transaction free" call to action.
- Inman coverage and Innovators Award finalist language.
- A simple one-minute demo hook.

This matters because the market buys trust before it buys completeness.

---

## 4. ListedKit Weaknesses And Openings

These are not accusations about hidden product capability. They are openings based on the public feature surface.

### 4.1 Narrower Public Platform Scope

ListedKit is publicly strongest as an AI TC assistant. Its public pages do not emphasize a full brokerage operating system with:

- FSBO customer workspaces.
- Represented-client concierge workspaces.
- Vendor document portals.
- Public milestone sharing.
- Payment collection/invoicing.
- Advertising marketplace hooks.
- Tenant white-label branding and platform fleet operations.
- Deep platform-admin lifecycle management.

Velvet Elves already has many of these systems in source.

### 4.2 Less Publicly Visible Deterministic Playbook Control

ListedKit's "no templates, no setup" message is a strength for speed, but it can also be a weakness for brokerages that want a firm-approved deterministic playbook, auditable task rules, controlled task templates, per-team preferences, and admin governance.

Velvet Elves has a stronger architecture for:

- Master task templates.
- Tenant/team/user settings.
- Task dependency logic.
- Admin and team configuration.
- Confidence settings.
- Audit logs.

### 4.3 Less Publicly Visible External-Participant Portals

ListedKit's public messaging centers on teams, TCs, brokers, agents, and attorneys. Velvet Elves can differentiate by making every external participant's experience first-class:

- Client sees next steps, milestones, documents, invoices, and agent info.
- FSBO seller gets plain-English guidance, property prep, milestones, share links.
- Vendor sees only assigned document/request surfaces.
- Public milestone viewers can open read-only links.

### 4.4 Compliance And Human-Control Story Is An Opening

ListedKit does state that users can verify extracted fields next to source text. Velvet Elves should go further: every AI extraction, recommendation, task change, email draft, payment-triggered workflow, and attorney approval should have a durable human-in-control audit trail and source evidence.

### 4.5 Pricing Attack Surface

ListedKit's $14.99-per-credit, first-free, no-subscription model is attractive. Velvet Elves will need a pricing model that does not make the platform feel expensive before its breadth is understood. A pure SaaS seat price could lose to ListedKit for solo TCs unless the value difference is obvious.

---

## 5. Velvet Elves Current Strengths

### 5.1 Broader Role Model

The project has explicit roles for:

- Agent
- Transaction Coordinator
- Team Lead
- Attorney
- Admin
- Client
- ForSaleByOwner
- Vendor

ListedKit publicly addresses multiple professional roles, but Velvet Elves has a wider operational role boundary in both requirements and implemented route gating.

### 5.2 Multi-Tenant And White-Label Architecture

The backend includes tenant APIs, platform tenant administration, branding endpoints, public branding, logo storage, tenant lifecycle controls, legal hold/archive work, plan/seat metadata, and isolation tests. The 6.1 plan records white-label/multi-tenant implementation as delivered, and the router/source includes tenant, platform, branding, calendar, CRM/webhook, and public-branding routers.

Competitive value:

- Brokerages can make the platform feel like their own.
- Platform operators can manage multiple tenant workspaces.
- White-label client/FSBO/payment surfaces can become a differentiator against a single-brand AI assistant.

### 5.3 More Complete Closing Workflow Surface

Current source includes implemented or routed surfaces for:

- Transactions and transaction detail routing.
- Active Transactions workspace.
- Task Queue.
- All Documents.
- AI Suggestions.
- AI Email Review.
- Analytics/reports.
- Calendar.
- Contacts.
- Vendors and vendor proposals.
- Client hub and client workspace.
- FSBO workspace.
- Attorney dashboard, releases, state rules, recording calendar, matter workspace.
- Payments, invoices, public invoice pay links, payouts, payment-access controls.
- Advertising admin/platform/public storefront.
- Platform tenant console.

This is broader than ListedKit's public assistant-focused story.

### 5.4 Smart Task Engine Foundation

The June 5 task-engine work materially improves competitiveness:

- `POST /api/v1/transactions/preview-tasks` exists.
- Wizard has a `Review Tasks` step.
- Preview and commit share the same backend planning path.
- Dependency engine seeds contract acceptance and closing anchors directly.
- Conditions are executable JSON predicates.
- Dual-agency consolidation is modeled with task families.
- Multiple predecessors are supported via `dep_task_ids`.
- Due dates roll forward from weekends/federal holidays.
- Tests cover production-path anchor behavior, conditions, dual-agency filtering, and task preview.

This gives Velvet Elves a deterministic alternative to ListedKit's AI-only setup: "the firm playbook is precise, reviewable, and auditable."

### 5.5 AI And Document Processing Architecture

The backend includes:

- AI provider abstraction.
- Document parsing endpoints.
- Packet parsing.
- Document resolution across uploaded document sets.
- Textract support for PDF/image extraction with forms, tables, queries, signatures, and layout.
- AI feedback.
- AI task recommendations and AI suggestions.
- AI next-step refresh.
- AI email engine.

This can become stronger than ListedKit if field extraction is source-cited, benchmarked, and connected cleanly to task/timeline updates.

### 5.6 Human-In-The-Loop Communication

The AI email workflow is intentionally human-controlled:

- Inbound email is logged.
- Classification is rule-based for common patterns.
- Drafts are generated with confidence and assumptions.
- Sends require explicit user approval.
- Tone/disclaimer settings exist.
- Actions are logged.

This is especially important for attorney and broker compliance.

### 5.7 Vendor Lifecycle Advantage

Milestone 4.3 and current source cover:

- Vendor templates.
- Vendor communications.
- Vendor proposals.
- Vendor background refresh.
- Add-colleague public flow.
- Transaction vendor assignments.
- Vendor document portal.
- Communication log exports.

ListedKit's public pages do not emphasize a comparable vendor lifecycle.

### 5.8 Client And FSBO Portal Advantage

Velvet Elves can serve both represented clients and FSBO sellers with branded, constrained, customer-safe portals. This creates a defensible moat: the product is not only a back-office assistant; it can become the place where all participants know what is next.

### 5.9 Payments And Monetization

The source includes:

- Stripe client/service.
- Invoices.
- Payments.
- Refunds.
- Commission payouts.
- Public invoice pay links.
- Client/FSBO invoice views.
- Payment event dispatcher.
- Payment access policy.
- Advertising packages/orders/placements/creative upload/click tracking.

ListedKit publicly sells coordination automation, not a transaction monetization infrastructure. Velvet Elves can support both workflow and revenue operations.

---

## 6. Velvet Elves Current Weaknesses

### 6.1 Core Demo Is Less Clear Than ListedKit's

ListedKit can say: "Upload contract, connect inbox, Ava runs the file." Velvet Elves currently has many strong modules, but the first-run demo must become equally simple:

1. Upload a contract.
2. Extract facts with field-level evidence.
3. Review generated dated tasks.
4. Create the transaction.
5. See inbox/doc/calendar/task updates in one deal workspace.
6. Ask the assistant "what is urgent today?"

If this loop is not crisp, the platform's breadth will feel like complexity.

### 6.2 Inbox-To-Deal Matching Is Not Yet The Center Of The Product

The backend has email integrations, inbound dispatching, AI emails, communication logs, and matching infrastructure. But ListedKit's public differentiator is that every incoming email is already in the right file even without an address in the subject. Velvet Elves needs a visible Inbox by Deal experience and a confidence-scored matching pipeline that users can correct.

### 6.3 Contract Intelligence Needs Benchmark Proof

Velvet Elves has strong document/AI infrastructure, but the product should publish and internally track hard metrics:

- Parse latency.
- Field extraction accuracy.
- Date/deadline accuracy.
- Handwritten scan success.
- Addendum/counteroffer update accuracy.
- Source-citation coverage.
- Human correction rate.

ListedKit is claiming 60-second/2-minute outcomes publicly. Velvet Elves needs its own measured claim.

### 6.4 Task Review Is Still Mostly View-Only

The current wizard Review Tasks step shows exactly what will be created, which is a major improvement. To beat ListedKit, coordinators should be able to edit before commit:

- Remove a task.
- Change due date.
- Change assignee/target.
- Add a custom task.
- Save edits as a team/tenant playbook improvement.
- Explain why a task was removed, for audit and training.

### 6.5 Documentation Drift Creates Execution Risk

Some docs are older than the source, and some plan bodies contradict later status notes. For example, 6.2's status note says implemented while older sections still describe greenfield or standalone-site decisions. This is manageable, but it creates product risk: engineers and testers can chase stale gaps or miss implemented behavior.

### 6.6 Some Broad Modules Need Product Polish

The platform is broad. The risk is "many capable surfaces, not enough magical workflows." The biggest polish needs are:

- Make every dashboard button lead to a real action.
- Consolidate duplicate shell/navigation patterns.
- Keep task/document/contact modals contextual with client and property address.
- Avoid exposing internal milestone/version language to users.
- Ensure role-specific workspaces are tools, not decorated dashboards.

### 6.7 SMS/Voice And Named CRM Integrations Are Still Mostly Hooks

Velvet Elves has provider-agnostic hooks and CRM/webhook infrastructure, but ListedKit publicly claims SMS texting and Follow Up Boss. To win head-to-head, Velvet Elves needs at least one named CRM and one real SMS/call provider integration, or a stronger open-integration story that is easy for non-engineers to configure.

### 6.8 Security And Compliance Story Needs Packaging

The codebase has meaningful security controls: tenant scoping, audit logs, invitation hardening, encryption helpers, SSRF guards, public token patterns, platform admin separation, payment webhooks, and retention planning. But a buyer will want a packaged trust story:

- SOC 2 roadmap or controls matrix.
- AI data-handling statement.
- Field-level source evidence.
- Tenant isolation statement.
- Export/audit retention policy.
- DPA/security page.

### 6.9 Pricing And Packaging Are Undefined

ListedKit's pricing is easy to understand. Velvet Elves needs pricing that fits three buyer profiles:

- Solo agent / small team that compares directly to ListedKit.
- TC/admin team that needs high-volume automation.
- Brokerage/platform buyer that values portals, white-label, payments, and compliance.

Without this, the platform may look powerful but hard to buy.

---

## 7. Feature-By-Feature Scorecard

Legend:

- **ListedKit lead**: ListedKit's public product is stronger or more clearly proven.
- **Velvet Elves lead**: Velvet Elves has broader/deeper implemented architecture.
- **Tie / unclear**: Both appear capable or current proof is insufficient.

| Category | ListedKit public strength | Velvet Elves current state | Current winner | Improve Velvet Elves by |
| --- | --- | --- | --- | --- |
| AI contract intake | Any-state, handwritten, no templates, 60s/2min public claims | AI parsing, Textract, packet parsing, resolution, wizard extraction | ListedKit lead | Publish measured parsing benchmarks, add field-source review, handwritten golden set |
| Task/timeline generation | Timeline/checklist from contract, no setup | Deterministic task engine with preview, conditions, business-day roll-forward | Tie if validated | Editable pre-commit review, addendum recalculation, state-specific day-basis |
| Inbox monitoring | Prominent deal-aware inbox matching even without address subject | Email integration/inbound/AI drafts exist, but inbox-by-deal not central | ListedKit lead | Build "Inbox by Deal" surface, matching confidence, correction loop |
| Daily urgency | Ava surfaces urgent work across all deals | Dashboards, task queue, AI briefing, health score, suggestions | Tie / VE potential | One "Today" command center that merges inbox, tasks, docs, calendar |
| Email automation | Drafts/replies from Gmail/Outlook, scheduled reminders | AI email review with human approval, provider abstraction, logs | Tie | Scheduled deadline reminders from deal context; source-cited email drafts |
| SMS | Publicly claims SMS texting to ask Ava | Hooks/future support, no obvious live provider | ListedKit lead | Twilio/phone provider MVP: ask status, log reply, notify owner |
| Calendar | Google/Outlook sync, one-step deadline events | Calendar routes, Google/Outlook connect, push closings | ListedKit slight lead | Push all key deadlines, invite parties, handle updates/deletes, optional inbound conflict handling |
| State rules | 50 public state guides, state-aware timelines | State rules service, attorney-state workflows, state rules page | ListedKit lead publicly | Build state rule library/admin, 50-state public/internal guide, state-specific deadline rules |
| Attorney workflow | Attorney page: review periods, doc versioning, risk management | Dedicated attorney dashboard/releases/state rules/matter workspace | Velvet Elves lead potential | Finish legal packet intake, version comparison, risk checklist, release workflow |
| Client portal | Not emphasized publicly | Dedicated client concierge/workspace, docs, milestones, invoices | Velvet Elves lead | Polish branded client experience and visible "ask a question" loop |
| FSBO | Not emphasized publicly | FSBO property workspace, docs, milestones, sharing, guidance | Velvet Elves lead | Make FSBO listing-prep and under-contract flows first-class |
| Vendor workflow | Not central publicly | Vendor portal, proposals, contacts, background refresh, comm logs | Velvet Elves lead | Inline vendor task CTA, structured request marketplace, SLA tracking |
| Payments | Not central publicly | Stripe, invoices, public pay links, payouts, access policy | Velvet Elves lead | Tie payments to milestones, client portal, receipts, accounting webhook |
| Advertising/marketplace | Not central publicly | Public ad storefront, admin/platform ad management, ad slots | Velvet Elves lead | Decide if ads support or distract from premium workspace; keep tenant opt-in |
| White-label/multi-tenant | Team accounts/public roles | Tenant branding, platform console, public branding, isolation | Velvet Elves lead | Activate/harden RLS path, custom domain ops, security docs |
| Public proof | Testimonials, logos, pricing, Inman coverage, guides | Internal docs/source, no public proof in this repo | ListedKit lead | Website, demo videos, trust center, pricing, launch case studies |

---

## 8. Strategic Product Thesis

### 8.1 Do Not Chase ListedKit Feature-For-Feature Only

Velvet Elves should match the AI TC wedge, but it should not stop there. The winning strategy is:

1. **Match ListedKit's magic loop**: contract + inbox + timeline + urgent work.
2. **Beat ListedKit on control**: deterministic templates, audit, admin governance, source evidence.
3. **Beat ListedKit on participants**: client, FSBO, vendor, attorney, payment, and milestone portals.
4. **Beat ListedKit on brokerage scale**: multi-tenancy, white-label, platform admin, team configuration.
5. **Beat ListedKit on monetization and operations**: payments, ad hooks, CRM/webhooks, analytics.

### 8.2 Product Promise To Aim For

Recommended public promise:

> Upload a contract. Connect your inbox. Velvet Elves builds the file, dates the playbook, watches every message, and gives every party the right next step.

Sub-promise:

> Ava coordinates the file. Velvet Elves runs the closing.

Avoid over-indexing on "AI does everything." For attorneys, brokers, and compliance-minded teams, the more trustworthy promise is:

> AI prepares. Humans approve. The system remembers.

---

## 9. Concrete Improvement Plan

### Phase 0: Align The Competitive Story (2-3 days)

**Goal:** Everyone on the project can explain how Velvet Elves beats ListedKit in one minute.

Deliverables:

1. Create a single internal product narrative:
   - "AI TC parity plus closing operating system."
   - "Contract + inbox + timeline + participant portals."
2. Define the flagship demo flow:
   - Upload purchase agreement.
   - AI extracts fields with source evidence.
   - Review dated task plan.
   - Create transaction.
   - Inbox messages appear in the deal file.
   - Daily command center shows urgent work.
   - Client/FSBO/vendor sees a constrained portal view.
3. Create a competitor parity checklist with acceptance tests:
   - Contract read.
   - Inbox match.
   - Timeline build.
   - Email draft.
   - Calendar sync.
   - SMS/status query.
   - Team permissions.
   - Source/audit evidence.

Success criteria:

- A non-engineer can watch the demo and understand why the platform is more complete than ListedKit.

### Phase 1: Harden The Contract-To-Tasks Core (1-2 weeks)

**Goal:** Velvet Elves can confidently claim reliable contract-driven timeline generation.

Already present:

- Task preview endpoint.
- Wizard Review Tasks step.
- Fixed anchor dates, conditions, dual-agency task families, multi-predecessor dates, business-day roll-forward.

Build next:

1. **Editable task preview before commit**
   - Remove task.
   - Change due date.
   - Change target/assignee.
   - Add custom task.
   - Save customizations into transaction metadata/audit.
   - Optional: "Make this my default" to feed team/user templates.

2. **Source-cited extraction review**
   - Every extracted date/party/contingency shows source document, page, text snippet/field confidence.
   - If the source is uncertain, require human confirmation.
   - Store review/correction history.

3. **Golden contract test suite**
   - 10 Indiana contracts.
   - 10 mixed-state contracts.
   - 5 handwritten/scanned contracts.
   - 5 addenda/counteroffer packets.
   - Expected fields and deadline outputs.

4. **Benchmark dashboard**
   - Parse time.
   - Field accuracy.
   - Task count.
   - Undated tasks.
   - Human correction rate.
   - Date roll-forward count.

5. **Addendum recalculation**
   - Upload addendum to existing deal.
   - Detect changed closing date, inspection terms, possession, parties, contingencies.
   - Show "changes to timeline" before applying.
   - Preserve completed tasks.

Success criteria:

- 95%+ of golden-set required dates extracted or explicitly marked for review.
- 0 duplicate task families in generated task preview.
- 0 undated tasks when contract acceptance and closing date are known.
- Every generated task has an explainable basis.

### Phase 2: Build Inbox Intelligence To Match ListedKit (2-4 weeks)

**Goal:** Every email is in the right file, and the user starts from what needs attention.

Build:

1. **Inbox by Deal**
   - New deal tab/panel: Emails.
   - Thread list grouped by transaction.
   - Inbound/outbound/system/AI draft filters.
   - Subjectless/weak-subject email matching.
   - "Move to another deal" correction action.

2. **Matching confidence engine**
   - Signals: participants, email domain, property/address fragments, prior threads, attachments, closing/title/lender phrases.
   - Store match reason and confidence.
   - Low confidence goes to "Needs filing" queue.
   - User corrections train future matching for repeat contacts.

3. **Daily triage queue**
   - "Needs response."
   - "Deadline mentioned."
   - "Document received."
   - "Vendor proposed date."
   - "Unmatched email."
   - "Client asked question."

4. **Email draft with evidence**
   - Draft body shows cited fields: closing date, status, documents, tasks.
   - User can approve/edit/send.
   - AI never sends without explicit approval unless a future tenant policy allows it.

5. **Scheduled deadline reminders**
   - Build from task/key-date engine.
   - Send from connected Gmail/Outlook.
   - Human-configurable templates.

Success criteria:

- 90%+ correct auto-match on test inbox set.
- All unmatched/low-confidence emails appear in a filing queue.
- Every draft can show which deal facts it used.

### Phase 3: Make The "Today" Command Center Unmissable (1-2 weeks)

**Goal:** Beat ListedKit's "Ava tells you what is urgent" with a stronger multi-source command surface.

Build:

1. **Unified Today view**
   - Due/overdue tasks.
   - Emails needing response.
   - Missing documents.
   - Calendar deadlines.
   - Vendor proposals.
   - Client/FSBO questions.
   - Payments/invoices requiring action.
   - Attorney holds/releases.

2. **Priority reasoning**
   - Each item states why it is urgent.
   - Example: "Inspection response due tomorrow; seller agent emailed at 9:12am asking for repair response."

3. **One-click next actions**
   - Draft email.
   - Update date.
   - Request document.
   - Assign task.
   - Open deal.
   - Mark reviewed.

4. **Role-specific filters**
   - Agent: revenue and client commitments.
   - TC: deadline and document workload.
   - Team Lead: team drift and bottlenecks.
   - Attorney: review/release risk.
   - Admin: compliance/AI/payment/system issues.

Success criteria:

- A user can start their day from one screen without opening each transaction manually.

### Phase 4: Calendar And SMS Parity (2-3 weeks)

**Goal:** Close ListedKit's public action-channel lead.

Calendar:

1. Push every critical deadline, not only closing.
2. Add Google and Outlook event metadata linking back to transaction/task.
3. Update/delete existing events without duplicates.
4. Invite internal responsible parties; optionally invite external parties by role.
5. Render calendar sync status per transaction.

SMS/phone:

1. Add Twilio or equivalent provider abstraction.
2. MVP SMS commands:
   - "What is due today?"
   - "Status for 123 Oak?"
   - "What is missing on Smith?"
   - "Draft reminder to title."
3. Log every SMS in communication logs.
4. Route ambiguous SMS to AI chat or the app.

Success criteria:

- A coordinator can sync all deal deadlines to calendar and ask the system via SMS what is urgent.

### Phase 5: State Rules And Attorney Superiority (3-5 weeks)

**Goal:** Turn state/attorney handling into a durable moat.

Build:

1. **50-state transaction rule library**
   - Public guide pages optional, internal rule data required.
   - Closing path: attorney/title/escrow/shared.
   - Business-day/calendar-day basis.
   - Attorney review periods.
   - Earnest money norms.
   - Disclosure requirements.
   - Transfer tax/recording notes.

2. **State-aware task generation**
   - Task templates can depend on state, county, closing mode, and representation.
   - Rules are data-driven, not string matching on task names.

3. **Attorney packet intake**
   - Upload legal packet.
   - Index documents.
   - Compare versions.
   - Extract settlement deltas.
   - Generate attorney review checklist.
   - Human approval/hold/release workflow.

4. **Version comparison**
   - "What changed between v2 and v3?"
   - Field-level diff for contract/addendum/settlement statement.
   - Source-cited differences.

Success criteria:

- Velvet Elves is credibly better than ListedKit for attorney-closing states and compliance-sensitive brokerages.

### Phase 6: Make Participant Portals The Differentiator (2-4 weeks)

**Goal:** Show something ListedKit does not publicly lead with: every external participant gets a useful, constrained workspace.

Client:

- Home/next steps/timeline/documents/agent/invoices.
- Ask-a-question thread.
- Plain-English status.
- Upload only what they are allowed to upload.
- No internal task/audit leakage.

FSBO:

- Property prep checklist.
- Listing-prep and under-contract states.
- Document board.
- Milestone sharing.
- Plain-English AI guidance with legal/agency boundary copy.

Vendor:

- Document upload.
- Request/proposal response.
- Add colleague.
- Vendor request history.
- No full transaction visibility.

Attorney:

- Matter workspace.
- Release queue.
- State rules.
- Recording calendar.

Success criteria:

- A brokerage can replace several disconnected portals/tools with one branded workspace.

### Phase 7: Integrations That Matter (4-8 weeks)

**Goal:** ListedKit claims named integrations; Velvet Elves needs either named connectors or a very strong open-integration story.

Build in this order:

1. Follow Up Boss contact/deal sync.
2. QuickBooks/Xero accounting webhook or connector.
3. Title/MLO document/status webhook profiles.
4. RESO/MLS listing data import if access is available.
5. Zapier/Make connector only after the core webhooks are stable.

Keep:

- Generic signed webhooks.
- Per-tenant API keys.
- Delivery logs and test events.
- Inbound sync testing in the UI.

Success criteria:

- At least one named CRM and one accounting/status integration can be demoed without engineering assistance.

### Phase 8: Trust, Security, And Public Proof (parallel, 2-6 weeks)

**Goal:** Match ListedKit's market trust and exceed its compliance posture.

Build:

1. Public website page:
   - Product promise.
   - One-minute demo.
   - Pricing.
   - Security summary.
   - Role/persona pages.
   - Compare with ListedKit.

2. Trust center:
   - AI data policy.
   - Tenant isolation.
   - Encryption.
   - Audit logs.
   - Payment handling.
   - Retention/deletion.
   - Subprocessors.

3. Security hardening:
   - Decide and schedule RLS activation or formally document app-layer isolation.
   - Pen-test plan.
   - SOC 2 readiness checklist.
   - Backup/restore runbook.

4. Customer proof:
   - Pilot case studies.
   - Time saved per transaction.
   - Parse accuracy metrics.
   - Deal volume handled.
   - Coordinator testimonials.

Success criteria:

- A buyer can evaluate Velvet Elves without a private explanation from the development team.

---

## 10. Pricing And Packaging Recommendation

ListedKit's public model is simple: first transaction free, $14.99 per transaction/contract setup, no monthly fees, credits never expire, unlimited team members.

Velvet Elves should avoid making the entry point heavier than ListedKit. Recommended packaging:

### Package A: Transaction AI

For solo agents and TCs comparing directly to ListedKit.

- First transaction free.
- Usage-based intake credits.
- Contract extraction.
- Task/timeline generation.
- Inbox-by-deal.
- Calendar sync.
- AI email drafts.

Goal: neutralize ListedKit on price simplicity.

### Package B: Team Operating System

For small teams and TC companies.

- Monthly base or annual subscription.
- Unlimited users or generous included seats.
- Team templates.
- Team dashboard.
- Vendor workflows.
- Client portal.
- Payment/invoice module.
- Analytics.

Goal: sell operational control, not just AI.

### Package C: Brokerage / White Label

For brokerages and platform buyers.

- White-label tenant.
- Platform admin.
- Custom branding/domain.
- Webhooks/API keys.
- Advanced audit/export.
- Role dashboards.
- Security/retention controls.

Goal: win where ListedKit's pay-per-intake positioning may feel too lightweight.

### Add-ons

- Attorney state/risk module.
- SMS/voice.
- AI Coach.
- Advertising/marketplace.
- Named integrations.
- Premium support/concierge.

---

## 11. Product Quality Metrics

To credibly beat ListedKit, measure the work the way users feel it.

### Contract Intake Metrics

- Time from upload to editable transaction draft.
- Required-field extraction accuracy.
- Deadline/date accuracy.
- Source-citation coverage.
- Human correction rate.
- Handwritten/scan success rate.
- Addendum update accuracy.

### Inbox Metrics

- Email match accuracy.
- Unmatched email rate.
- False positive match rate.
- Time from inbound email to deal file.
- Draft approval rate.
- Draft edit distance.

### Workflow Metrics

- Tasks created per transaction.
- Duplicate task family rate.
- Undated task rate.
- Overdue task rate.
- Time-to-first-next-action after login.
- Calendar sync success/failure rate.

### Portal Metrics

- Client/FSBO login rate.
- Documents uploaded by external participants.
- Questions asked/resolved.
- Milestones shared/viewed.
- Invoice pay-link conversion.

### Trust Metrics

- AI actions requiring human review.
- AI recommendations accepted/dismissed.
- Audit-log completeness.
- Tenant-isolation test coverage.
- Security/control checklist completion.

---

## 12. Highest-Risk Gaps

### Risk 1: Breadth Without A Magical Core

If the product has many pages but does not obviously solve "contract and inbox chaos," ListedKit will feel better even with fewer modules.

Mitigation:

- Make the flagship flow contract + inbox + tasks + today queue.

### Risk 2: AI Trust

Real estate users will not trust AI if they cannot verify where a date or statement came from.

Mitigation:

- Source-cited extraction and source-cited email drafting everywhere.

### Risk 3: Documentation Drift

Planning docs and source status are out of sync in places.

Mitigation:

- Maintain a single `CURRENT_PRODUCT_STATE.md` or generated feature inventory.
- Mark docs as "implemented", "planned", "superseded", or "needs verification".

### Risk 4: Pricing Confusion

If Velvet Elves launches with a complex enterprise pricing story only, ListedKit wins the solo/TC wedge.

Mitigation:

- Offer a direct pay-per-intake or first-free entry package.

### Risk 5: Compliance/Security Claims Not Packaged

The code may be secure enough for pilot use, but buyers need a readable trust story.

Mitigation:

- Build a trust center and security checklist before public launch.

---

## 13. Immediate Next 10 Tickets

1. **Editable task preview:** allow remove/date/assignee/custom edits before transaction commit.
2. **Field-source viewer:** show source document/page/snippet for each extracted field in the wizard.
3. **Golden contract suite:** create fixture set and expected extraction/deadline outputs.
4. **Inbox by Deal MVP:** render matched inbound/outbound threads on transaction detail/drawer.
5. **Unmatched inbox queue:** low-confidence email filing review.
6. **Today command center:** unified urgent queue from tasks, emails, docs, vendor proposals, payments, and calendar.
7. **Full deadline calendar sync:** push all key dates/tasks, not only closing.
8. **State rule data model:** replace state/attorney string heuristics with state/closing-mode rule data.
9. **Public product/pricing draft:** create first comparison/pricing/product narrative doc.
10. **Current-state inventory doc:** reconcile docs vs implemented source to prevent stale-plan confusion.

---

## 14. Bottom Line

ListedKit is ahead in public clarity, proof, and the AI-TC wedge: contract reading, inbox matching, timeline generation, and urgent-work surfacing. Velvet Elves is ahead in architectural ambition and platform breadth: role-specific workspaces, external portals, payments, vendor lifecycle, white-label tenancy, advertising hooks, auditability, and admin control.

The winning path is not to out-breadth ListedKit first. The winning path is to make Velvet Elves' first five minutes feel at least as magical as ListedKit's:

1. Upload contract.
2. Verify extracted facts.
3. Review/edit dated task plan.
4. Connect inbox.
5. See every urgent item across the pipeline.

Then show the parts ListedKit does not publicly lead with:

1. Client, FSBO, attorney, and vendor portals.
2. Payments and invoicing.
3. White-label brokerage platform.
4. Compliance-grade audit/source evidence.
5. Vendor and external-party coordination.

If Velvet Elves executes that sequence, it can become meaningfully superior to ListedKit rather than merely similar.

