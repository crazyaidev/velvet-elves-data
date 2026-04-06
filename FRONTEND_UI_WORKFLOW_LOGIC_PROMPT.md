# Velvet Elves — Frontend UI Workflow Logic Design Prompt

**Purpose:** Generate a complete, page-by-page frontend UI workflow logic specification that governs user interactions, state transitions, navigation flows, data dependencies, conditional rendering, error states, and AI integration touchpoints across every page and overlay in the Velvet Elves platform.

**Output format:** A single structured document covering every route in the application. Each page section must include: entry conditions, data requirements, user actions and their resulting state changes, conditional UI logic, navigation flows (where the user came from, where they can go), error/empty/loading states, AI interaction points, role-based visibility rules, and edge cases.

---

## System Context

Velvet Elves is an AI-first real estate transaction management platform. The tech stack is React (Vite + TypeScript) frontend with FastAPI backend, Supabase (PostgreSQL + Auth + Storage), and switchable OpenAI/Claude AI providers. The platform uses a multi-tenant architecture with Row-Level Security.

### Roles (8 total)
1. **Agent** — Creates/manages transactions, confirms wizard data, assigns tasks, approves AI communications, owns personal task templates (unless on a team)
2. **Elf (Transaction Coordinator)** — Manages assigned transactions, assigns/completes tasks, approves AI emails; CANNOT change master task templates or override agent decisions
3. **Team Lead** — Controls team-wide task templates, oversees all team transactions, can act as agent; all activities logged
4. **Attorney** — Uploads legal packets, reviews title objections/settlement deltas/release timing, approves or holds attorney-owned sends/releases; CANNOT delegate legal judgment to AI
5. **Administrator** — Manages users, sets system-wide defaults, configures AI behavior limits, accesses all data
6. **Client (Buyer/Seller)** — Views documents/milestones, asks questions, uploads documents (cannot delete); CANNOT edit tasks, delete documents, or see internal notes
7. **FSBO Customer (Self-Guided Seller)** — Customer-facing property-centric workspace; uploads/views/downloads documents, reviews milestones, gets plain-English AI guidance; CANNOT see internal workflow logic
8. **Vendor** — Uploads documents (if invited), receives documents, answers timeline adjustment requests; CANNOT view full document center or see tasks/timelines

### Transaction Types (6)
1. Buyer - Financing (Buy-Fin)
2. Buyer - Cash (Buy-Cash)
3. Seller - Financing (Sell-Fin)
4. Seller - Cash (Sell-Cash)
5. Buyer & Seller - Financing (Both-Fin)
6. Buyer & Seller - Cash (Both-Cash)

### Transaction Statuses
Active, Incomplete, Paused, Completed, Closed

### Task Statuses
Pending, InProgress, Completed, Blocked, Skipped

### Design System Constants
- Shell: dark sidebar + slim topbar + page header + scrollable content area
- FSBO/Client: simplified but brand-consistent shell variant
- Colors: Deep Institutional Navy (#1B2B3C), Refined Amber Orange (#EE7623), Soft Cool Grey (#F5F7FA), Subtle Champagne Glow (#FFEEC2), Max-Contrast Slate Grey (#333333)
- Functional states: Critical red (#c8322f), Warning amber (#c07a0a), Healthy green (#1a7a52), Info blue (#2c4c7f), Neutral gray (#7a7a7a)
- Typography: IBM Plex Sans (UI), IBM Plex Mono (numbers/dates/countdowns), Limited Lora serif (approved display headings only)
- Components: shadcn/ui + Tailwind + custom workspace components
- Interaction: 6px corner radius, minimum 48x48px interactive targets
- Numeric: tabular-nums lining-nums on all money, dates, phones, addresses, file IDs, percentages, deadlines

### Navigation Architecture (Sidebar Groups)
Internal roles share a grouped sidebar:
- **Dashboard** — role-specific landing page
- **Deals** — Active Transactions, Pending, Closed, All Transactions
- **Workflow** — My Task Queue, All Documents, Closing Calendar
- **Intelligence** — AI Suggestions, Analytics, Settings
- **Team** (Team Lead only) — Agents, Task Templates
- Footer: pinned "+ New Transaction" CTA, user profile card

FSBO sidebar: Dashboard, My Properties, Documents, Milestones & Messages, Ask Velvet Elves AI, Notifications, Sharing

### AI Briefing System
- Persistent topbar chip: "Today's AI Briefing" with Critical / Needs Attention / On Track counts
- Available across all internal dashboards and Active Transactions workspace
- Acts as a filter/sort shortcut into the current workspace

### Key Milestone Dates (per transaction, editable inline)
EM Delivered, Inspection Response, Appraisal Expected, CD Delivered, Cleared to Close, Closing Date (with time-of-day), Possession (with time-of-day)

### Milestone Bar Steps
Contract → EM → Inspection → Appraisal → CD Delivered → CTC → Close

### Stage Pill Computation
- "Critical" — overdue tasks or approaching deadline with blockers
- "Needs Attention" — warning-level issues (stale communication, upcoming deadlines)
- "On Track" — no overdue tasks, deadlines on schedule
- "Unhealthy" — multiple risk factors combined
- "In Inspection" — inspection response has not yet been sent

---

## Completed HTML Design References

The following approved HTML designs exist and must be treated as the canonical visual and structural reference for their respective pages:

1. `completed_designs/ve-active_transactions.html` — Shared Active Transactions workspace
2. `completed_designs/ve-homepage_dashboard-solo_agent.html` — Solo Agent dashboard landing
3. `completed_designs/ve-homepage_dashboard-team_leader.html` — Team Leader dashboard landing
4. `completed_designs/ve-fsbo_dashboard.html` — FSBO Customer workspace
5. `completed_designs/ve-attorney_dashboard.html` — Attorney dashboard landing
6. `completed_designs/ve-workflow-closing_calendar.html` — Closing Calendar workspace
7. `completed_designs/ve-workflow-my_task_queue.html` — My Task Queue workspace
8. `completed_designs/ve-intelligence-analytics.html` — Analytics workspace
9. `completed_designs/ve-intelligence-ai_suggestions.html` — AI Suggestions workspace
10. `completed_designs/ve-workflow-all_documents.html` — All Documents workspace

---

## Route Map

Design the complete workflow logic for every route below. Each page must be covered.

### Auth Pages (Public)
- `/login`
- `/register`
- `/forgot-password`
- `/reset-password`
- `/auth/callback` (OAuth)
- `/invite/:token`

### Onboarding (Protected, Standalone)
- `/onboarding`

### Dashboard Landing Pages (Role-Specific)
- `/dashboard` (auto-routes by role)
- `/dashboard/agent` (Solo Agent)
- `/dashboard/team` (Team Leader)
- `/dashboard/attorney` (Attorney)
- `/dashboard/admin` (Administrator)

### Deals Section
- `/transactions/active` (Shared Active Transactions workspace — used by Agent, Elf, Team Lead, Attorney)
- `/transactions/pending`
- `/transactions/closed`
- `/transactions/all`
- `/transactions/new` (New Transaction — wizard entry)
- `/transactions/:id` (Transaction Detail — tabbed: Overview, Tasks, Documents, Parties, Communications)

### Workflow Section
- `/tasks/queue` (My Task Queue)
- `/tasks/:id` (Task Detail)
- `/closing-calendar` (Closing Calendar)
- `/documents/all` (All Documents with AI search)

### Intelligence Section
- `/ai-suggestions` (AI Suggestions)
- `/analytics` (Analytics)
- `/settings` (System/User Settings)

### Attorney Workspace
- `/attorney/queue` (Attorney matter queue)
- `/attorney/releases` (Release-ready packets)
- `/attorney/state-rules` (State rules modal/view)
- `/attorney/recording-calendar`

### FSBO Customer Workspace
- `/fsbo` (FSBO overview)
- `/fsbo/properties` (Property portfolio)
- `/fsbo/properties/:id` (Property detail)
- `/fsbo/documents` (Document submission)
- `/fsbo/milestones` (Milestones & Messages)
- `/fsbo/share` (Milestone sharing management)
- `/fsbo/ask-ai` (Plain-English AI guidance)

### Client Portal
- `/client/transactions` (My Transactions)
- `/client/documents` (Documents)
- `/client/milestones` (Milestones)
- `/client/agent` (Agent Info / Bio)

### Admin Section
- `/admin/users` and `/admin/users/:userId`
- `/admin/task-templates`, `/admin/task-templates/:id`, `/admin/task-templates/import`
- `/admin/confidence` (AI Confidence Settings)
- `/admin/audit-logs` (Audit Logs)
- `/admin/tenant` (Tenant/Brokerage Settings)

### Profile
- `/profile` (Personal Info, Notification Preferences, Checklist Templates, Integrations)

### Shared / Public
- `/milestones/:shareToken` (Public read-only milestone viewer)

---

## Required Output Per Page

For EACH route listed above, produce the following structured workflow specification:

### 1. Page Identity & Access
- **Route:** the URL pattern
- **Page title** and description
- **Allowed roles:** which roles can access this page
- **Redirect rule:** what happens if an unauthorized role navigates here
- **Auth requirement:** public, protected, or protected + specific role check

### 2. Entry Conditions & Data Loading
- **Prerequisite state:** what must be true before the page renders (e.g., user authenticated, onboarding complete, transaction exists)
- **API endpoints consumed on mount:** list every API call the page makes when it loads, with query parameters and cache keys
- **Loading state UI:** what the user sees while data is loading (skeleton cards, spinners, placeholder text)
- **Empty state UI:** what the user sees when there is no data (e.g., no transactions, no tasks) — include the CTA or guidance shown
- **Error state UI:** what happens on API failure — retry logic, fallback display, toast notifications

### 3. Layout & Component Hierarchy
- **Shell variant:** full internal shell (sidebar + topbar) or simplified customer-facing shell
- **Sidebar state:** which nav item is active, which KPI tiles are shown, which deal counts are displayed
- **Topbar state:** which CTAs are visible, AI briefing chip state, search scope
- **Page header:** title, subtitle, count pills, action buttons (e.g., Export CSV, Print Report), tab bar if applicable
- **Primary content area:** component hierarchy in order of render (cards, grids, lists, empty states)
- **Overlay/modal inventory:** every modal, drawer, popover, or floating panel available from this page

### 4. User Actions & State Transitions
For every interactive element on the page, define:
- **Trigger:** what the user clicks/taps/types/drags
- **Immediate UI response:** optimistic update, loading indicator, disabled state
- **API call:** endpoint, method, payload
- **Success behavior:** UI update, toast notification, navigation, data refetch
- **Failure behavior:** error toast, field validation highlight, rollback of optimistic update
- **Side effects:** audit log entry, notification to other users, task generation, AI action triggered

### 5. Conditional Rendering Logic
- **Role-based visibility:** which UI elements appear or hide based on the current user's role (e.g., Team Lead sees assignee filter; Attorney sees sign-off checkboxes; Client doesn't see internal notes)
- **State-based visibility:** which elements appear based on transaction status, task status, or data presence (e.g., "In Inspection" tab count only shows when transactions have unsent inspection responses; empty contact slots show "Add [role]" links)
- **Feature flags / capability checks:** elements gated behind tenant settings, connected integrations, or paid features (e.g., AI Coach placeholder for future paid feature)
- **Responsive behavior:** how the layout adapts across desktop, tablet, and mobile breakpoints; which elements collapse, stack, or hide

### 6. Navigation Flows
- **Inbound routes:** how users arrive at this page (sidebar link, dashboard deep-link, redirect, URL direct entry, AI suggestion link)
- **Outbound routes:** every link, button, or action that navigates away from this page and the destination
- **Deep-link support:** which filter states, tab selections, or scroll positions can be encoded in the URL for sharing or AI-driven navigation
- **Back navigation:** breadcrumb behavior, browser back button handling, return-to-previous-context logic

### 7. AI Integration Points
- **AI data on page:** where AI-generated content appears (briefing counts, next-step banners, suggestions, draft emails, extracted data)
- **AI actions available:** what AI can do from this page (draft email, suggest task, parse document, answer question, run search)
- **AI confidence display:** where and how confidence scores or AI-sourced labels appear
- **AI guardrails:** what AI CANNOT do from this page (per role restrictions, especially Attorney role — AI must NOT determine legal equivalence, final packet release, or same-day disbursement exceptions)
- **AI chat panel:** whether the floating AI chat panel is available and what context it receives

### 8. Real-Time & Notification Behavior
- **Live updates:** which data refreshes in real-time via Supabase Realtime or polling (e.g., task completion by another user, new document upload, AI briefing update)
- **Notification triggers:** what actions on this page generate notifications for other users
- **Toast/alert patterns:** which actions show success/warning/error toasts

### 9. Cross-Page Relationships
- **Shared state:** what global state (filters, search terms, selected transaction, workspace view toggle) persists when navigating between pages
- **Dashboard deep-linking:** which dashboard cards/filters link to filtered views of this page
- **Data dependencies:** which pages must be visited first or which data must exist before this page becomes useful

### 10. Edge Cases & Special Behaviors
- **First-time user:** overlay tutorial, profile completion prompt on first transaction upload
- **Transaction type switching:** what happens in the UI when a transaction type changes mid-process (e.g., Financing to Cash — targeted task updates, not full regeneration; completed tasks preserved)
- **Concurrent editing:** what happens if two users edit the same transaction/task simultaneously
- **Offline/slow network:** graceful degradation, queued actions, retry behavior
- **Large data sets:** pagination strategy, virtual scrolling, load-more patterns
- **Document drag-and-drop:** global drop zone behavior when documents are dragged anywhere in the authenticated workspace — AI identifies the document, suggests a name, confirms the transaction, checks for e-signature needs

---

## Cross-Cutting Workflows to Design End-to-End

Beyond individual page workflows, the following multi-page user journeys must be designed as continuous flows with clear hand-offs between pages:

### A. New Transaction Creation Flow
1. Entry: "+ New Transaction" CTA (topbar or sidebar) OR document drag-and-drop anywhere in workspace
2. Quick-create modal (AI Import with paste, or manual field entry)
3. AI parsing and extraction (if documents provided)
4. Wizard steps: Document upload → AI parsing progress → Address confirmation → Purchase information validation → Missing information handling → Confirmation page
5. Transaction creation → task generation → redirect to Active Transactions or Transaction Detail
6. Post-creation: first-transaction profile completion prompt if applicable

### B. Transaction Lifecycle Management Flow
1. Active Transactions workspace: viewing, filtering, sorting
2. Transaction card expansion: tasks, key dates, contacts
3. Inline task completion and key date editing
4. AI suggestions and next-step actions
5. Document upload/view/email/e-sign from transaction context
6. Transaction type switching (mid-process use case change)
7. Transaction status transitions: Active → Completed → Closed
8. Post-closing: feedback prompt (useful/unnecessary/missing tasks)

### C. Task Management Flow
1. Task auto-generation from wizard confirmation
2. Manual task creation (Add Task modal) with AI similar-task check (Add / Combine / Disregard)
3. Task assignment (self, AI Agent, team member)
4. Task completion methods (phone call, email, e-sign, in person, upload, portal, AI agent, other)
5. AI task intelligence: recommendations for adding/removing tasks with transparency (reason, source, suggested deadline)
6. Task approval flow for team leads (bulk approve with preview of affected transactions)
7. Dynamic task updates when transaction type switches
8. Notification chain: day-before → due-today → past-due reminders

### D. Document Lifecycle Flow
1. Upload: drag-and-drop anywhere, or from document center, or from wizard
2. AI identifies document type, suggests name, confirms transaction, checks signature status
3. Storage with versioning (vendor re-uploads create new versions; old marked as legacy)
4. Document emailing with recipient selection, templated body, attachments
5. E-signature workflow: send → track → receive signed → replace original (old to version history) → distribute
6. Client/FSBO: view document statuses (Missing, In Progress, Uploaded, Verified, Complete), flag for deletion
7. Vendor: upload only, see own uploads, cannot see full document center
8. Cross-transaction AI search (All Documents workspace)

### E. Communication & AI Email Flow
1. Inbound email triggers AI processing
2. AI determines: factual question, document request, or uncertain
3. Factual / document exists → AI auto-responds (CC responsible internal owner)
4. Document missing or uncertain → AI drafts but DOES NOT send; routes to human with "Approve / Edit & Send"
5. Side-by-side review UI: draft with bolded assumptions vs. source data with tooltips
6. Vendor communication: constrained response format → AI parses reply → proposes date update → validates against timeline constraints
7. Communication log: immutable, searchable, filterable by date/party/keyword

### F. AI Chatbot Interaction Flow
1. Floating AI chat panel available throughout the workspace
2. On dashboard login: AI offers "most important things today" briefing (overdue tasks, due-today, timeline reminders)
3. Contextual: when a transaction is selected/expanded, chat receives that transaction context
4. Quick-action prompts: "Show overdue tasks", "Draft inspection response", "Summarize [client] deal"
5. AI can act as filter/sort layer — user asks in natural language, AI filters the workspace
6. All everything is leisure → AI offers leisure time suggestions or prospecting tips

### G. Attorney Workflow
1. Upload legal packets (title commitments, settlement statements, affidavits, signed amendments, recording packets)
2. AI extracts deadlines, compares versions, indexes exhibits, flags missing formal documents
3. Attorney queue: filter by All, Needs Review, Missing Docs, Ready To Release, Clean Files
4. Matter cards: review queue with sign-off checkboxes, key dates with status colors, AI-prepared next step
5. Explicit AI-vs-human boundary: AI prepares, human decides (legal equivalence, packet release, same-day disbursement remain human-owned)
6. State rules surface: closing mode, recording timelines, disbursement timing, same-day release checks
7. Release approval → writes to communication history and audit logs

### H. FSBO Customer Journey
1. Entry: FSBO-specific workspace with simplified shell
2. Property-centric view: listing-prep state → under-contract state
3. Document submission with status tracking (Missing → In Progress → Uploaded → Verified → Complete)
4. Milestone viewing with plain-English AI guidance (next step, why it matters, deadline explanations)
5. Milestone sharing: generate expirable read-only links; viewer-open notifications
6. Shared viewer experience: timeline + key dates only — no task editing, document deletion, or internal notes
7. Support/guide contact area with boundary notice (VE coordinates workflow, does not act as agent or provide legal advice)

### I. Team Lead Workflow
1. Dashboard with team-aggregated KPIs and intervention queue
2. Toggle between personal view (own deals) and team view (all team deals)
3. Agent board with drill-down into individual agent's portfolio
4. Team task template management: override templates for team, configure dependencies
5. Bulk approval of AI task recommendations with preview of affected transactions
6. Drift/discipline monitoring: closings in 7 days with unresolved deps, no client touch 72+ hrs, missing signatures, agent coaching

### J. Notification & Reminder System (Cross-Cutting)
1. In-app notifications (bell icon) for: task assignments, task due dates, document actions, AI email sends, communication received
2. Push notifications support
3. Email reminders: day-before, due-today, past-due (compiled summaries: "You have 3 transactions with deadlines due tomorrow")
4. Daily summary email: only when tasks are due, not when everything is clear
5. Configurable notification preferences per user (on/off toggles)
6. Escalation reminders: configurable 24-48 hour follow-up if no action taken
7. SMS hooks: architecture-ready for future SMS integration

### K. Admin Configuration Flow
1. User management: create, invite, activate/deactivate, role assignment
2. Task template management: edit definitions, dependencies, float, automation flags, use-case applicability
3. AI confidence threshold configuration: global minimum floor, per-team overrides
4. Tenant/brokerage settings: branding (logo, colors, domain), AI provider selection (OpenAI/Claude)
5. Audit log review: searchable, filterable, exportable

### L. Profile & Settings Flow
1. Personal info management (name, email, phone, bio, avatar)
2. Notification preferences (per-channel on/off toggles)
3. Buyer and Seller closing checklist template configuration
4. Tagged note management for checklist printing
5. Seller escrow overage reminder defaults
6. Preferred vendor list management
7. Email/calendar integration connections (Gmail, Outlook, iCloud)
8. E-signature provider connection (DocuSign, HelloSign)
9. First-time user overlay tutorial (skippable, re-viewable)
10. Post-first-transaction profile completion prompt if required fields or checklist templates are missing

---

## Global Interaction Patterns to Apply Everywhere

These patterns must be consistently applied across all pages:

1. **Global drag-and-drop document intake:** Dropping a document anywhere in the authenticated workspace triggers the AI intake flow (identify → name → assign to transaction → check signature needs)
2. **Global search:** Always available in topbar; searches across client names, vendor names, companies, dates, addresses, and all transaction fields
3. **AI briefing chip:** Persistent in topbar across all internal pages; acts as filter shortcut
4. **"+ New Transaction" CTA:** Available from both topbar and sidebar on all internal pages; opens quick-create modal
5. **Print closing checklist:** Available from any transaction context; pulls Buyer or Seller template from user/team profile settings; includes tagged notes and seller escrow overage reminders
6. **Audit logging:** Every user action that modifies data is logged with: user, role, timestamp, action type, before/after state, human-readable summary
7. **Sidebar deal-state filters:** Clicking Active Transactions, Pending, Closed, or All Transactions in the sidebar navigates to the corresponding filtered transaction workspace
8. **AI confidence indicators:** Where AI-generated content appears, show confidence level; content below review threshold is flagged for human review
9. **White-label theming:** All pages render with tenant-specific branding (logo, colors, domain) via CSS variables

---

## Constraints & Rules

1. **AI assists, humans decide.** All AI actions are recommendations. No auto-changes to dates, tasks, or communications without human confirmation (except for auto-send when confidence >= 90% threshold)
2. **Transparency beats automation speed.** Every AI recommendation must show reason, source, and confidence
3. **Nothing disappears silently.** Removed tasks "sleep" (can be restored). Deleted documents are soft-deleted. Communication logs are immutable
4. **Do not hardcode logic.** Task templates, dependencies, confidence thresholds, reminder intervals, and AI behavior must be configurable
5. **Everything is logged.** Every action writes to audit_logs with before/after state
6. **Compliance tasks cannot be fully removed** from all transactions
7. **Attorney AI guardrails are absolute.** AI must NOT determine legal equivalence, legal position, final packet release approval, or same-day disbursement exceptions — these are always human-owned
8. **FSBO boundary:** VE coordinates workflow but does not act as the customer's agent or provide legal advice
9. **Dashboard deep-linking:** Dashboard cards, fast filters, and AI prompts must open filtered views in Active Transactions or the relevant workspace — no dead-end pages
10. **MVP Active Transactions is shared:** All internal roles use the same Active Transactions workspace with role-specific adaptations (not separate pages per role)

---

## Deliverable

Produce a comprehensive document that covers every route, every overlay, every modal, and every cross-cutting flow listed above with the 10-section structure defined in "Required Output Per Page." The result must be detailed enough that a frontend developer can implement the complete UI workflow logic without ambiguity, and a QA engineer can derive test cases directly from it.
