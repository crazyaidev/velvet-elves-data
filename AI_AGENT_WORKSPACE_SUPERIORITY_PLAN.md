# AI Agent-Centric Transaction Workspace: Superiority Plan

Status: PLAN ONLY. No source code is changed by this document.
Created: 2026-06-12
Author basis: full review of project documentation, the implemented frontend and backend source, the 16 ListedKit screenshots in `velvet-elves-data/ai_agent_transaction/`, and the public ListedKit help/feature documentation.
Reference plan: `AI_AGENT_TRANSACTION_WORKSPACE_SUPERIOR_LISTEDKIT_PLAN.md` (created with OpenAI Codex). Section 3 of this document records which of its claims I verified as true, which I corrected, and where this plan deliberately diverges.

Goal: transform `/transactions/:transactionId` into a conversation-first AI agent workspace in which a real estate professional can resolve any issue that arises during a transaction by talking to the agent, while every write stays previewed, human-approved, evidence-cited, audit-logged, undoable where the backend supports it, and verifiable entirely through the frontend UI by a non-developer tester using only a mouse.

---

## 0. Table of Contents

0.1. Review pass corrections (2026-06-12, R1 to R12)
1. Grounding review: what was actually read and verified
2. The ListedKit model, decoded from the screenshots and help center
3. Verification of the Codex reference plan
4. What Velvet Elves already has (verified inventory)
5. Gap analysis: what is missing for an agent-centric workspace
6. Product principles
7. Target UX specification
8. The interaction model: references, issues, actions, approvals
9. Backend architecture
10. The typed action registry (verified handler map)
11. End-to-end workflow designs with UI test scripts
12. Superiority ledger: Velvet Elves vs ListedKit
13. Implementation phases
14. Database migrations inventory
15. Testing plan (automated + non-developer UAT)
16. Decisions pending Jake (AW1 to AW10)
17. What must not regress
18. Risks
19. Definition of done

---

## 0.1 Review Pass Corrections (2026-06-12)

A workflow-and-logic review of the first draft, checked line by line against the documentation and the implemented source, found and fixed the following. The body below already incorporates every correction; this list exists so reviewers can see what changed and why.

- R1 (workflow logic, critical): the document-mismatch scenario misstated requirement status. Matching a document to a requirement sets its status to `uploaded` (verified in `document_requirements.py`: matching sets `uploaded`, unmatching sets `missing`). So when the wrong file is attached, the receipt requirement is NOT "missing"; it sits in the Uploaded group wearing a mismatch chip, which is worse because it looks satisfied. Section 11.1 and UAT script 15.2.1 are rewritten: the primary remediation bundles "detach the wrong file" with the request draft, and the test asserts the row returns to Missing only after detach, never from the draft.
- R2 (consistency with shipped behavior): the existing ComplianceTab "Use AI type" control is one click and rewrites BOTH the requirement's expected `doc_type` AND the matched document's classification (verified: `adoptAiType` in `ComplianceTab.tsx:284`). The draft's server-side "mislabeled row" confirmation gate would have contradicted shipped UX without saying so. Corrected: the gate lives in the agent action layer (new explicit action `adopt_ai_type_for_requirement`), and aligning the ComplianceTab one-click control with the same single-question confirm is now an explicit Phase 2 deliverable, flagged as a deliberate change to a shipped control (the endpoint contract does not change).
- R3 (phase inconsistency): the 11.1 first-slice scenario offered "reclassify the document" and "adopt the AI type", but those actions were scheduled in Phase 3. `reclassify_document` and `adopt_ai_type_for_requirement` move into Phase 2 so the first shippable slice is self-consistent.
- R4 (missing backend prerequisite): the header task-progress indicator cannot be computed from the plan aggregate today. `_HeaderCounts` carries only `open_tasks`, `overdue_tasks`, `missing_docs`, `overdue_docs` (verified `transaction_plan.py:112`). The plan now names the small additive extension (`tasks_completed`, `tasks_total`, computed in the same pass that already counts active tasks).
- R5 (wrong assumption): the workspace has NO document viewer. `WizardPdfDocument` / `WizardEvidenceViewer` exist only under `src/components/wizard/`; the workspace `AiEvidenceChip` expands to snippet text plus an optional "view in document" callback. Corrected: a new `SourceViewerDrawer` component (reusing the wizard viewer, the OCR-geometry endpoint, and the `ocrHighlight` locate utilities) is an explicit Phase 3 deliverable; Phase 1 citation chips show page + snippet and open the Documents tab, which is the chip's existing honest behavior.
- R6 (mechanism precision): `/ai-emails/test-inbound` is role-gated (Agent, TransactionCoordinator, TeamLead, Admin), not environment-gated, with three fixed scenarios (`closing_question`, `document_request`, `vendor_reply`); it creates an inbound log + AI draft tagged `metadata_json.test = true` and sends nothing (verified `ai_emails.py:354`). A `TestInboundButton` already exists in `CommunicationsPanel.tsx`. The Email tab reuses it; hiding it on production tenants is a frontend visibility choice, not an endpoint property. Script wording now matches the real scenarios.
- R7 (evidence precision): `compose_outbound` produces `source_data` and `assumptions` only on the intent-composed AI path; a chosen template or provided body is used verbatim with 0.9 confidence and empty source data (verified `ai_email_engine.py:295+`). Sections 11.1/11.2 now say: the proposal card cites the requirement (agent side); the draft review shows the engine's grounded source data when composed from intent, and an honestly empty rail when a deterministic template was used.
- R8 (undo correctness): `add_party` undo is deleting the created party (`DELETE /transactions/{id}/parties/{party_id}` exists, verified); "edit back" was wrong. `update_party` undo restores prior values.
- R9 (scope omission): attorneys reach `/transactions/:id` as the Matter Workspace. The agent workspace targets the internal ops workspace only in v1; attorney agent integration is explicitly future work under the requirements 8.6 guardrails. Stated in section 6.
- R10 (stale numbers): the current green state is backend 880 / frontend 244 (after the wizard/workspace refinement pass; the 7 `TransactionWorkspace.test.tsx` integration tests are included). The draft said frontend 236.
- R11 (mechanism precision): there is no dedicated document-verify endpoint. Upload verification is the existing background parse (`useParseDocument` → `/ai/parse`) plus a deterministic doc-type comparison against persisted `ai_extracted_data.document_type_detected` (`useDocVerification.ts`), and already-parsed documents are never re-parsed. The `run_compliance_scan` registry row now says exactly that.
- R12 (mechanism named): the per-user pane preference persists through the existing profile-settings mechanisms (`PUT /users/me`; the `/users/me/dashboard-layout` preference endpoint is the precedent pattern), not a new system.

---

## 1. Grounding Review: What Was Actually Read and Verified

This plan was written after reading the documents and source below directly, not from memory or from the Codex plan's summaries.

Project documentation:

- `velvet-elves-data/requirements.txt` (full read: RBAC, transaction model, task engine, communication engine, AI rules in section 6.3 to 6.5 and 8.x, UI requirements in 9.x)
- `velvet-elves-data/SYSTEM_DESIGN.md` (full read: schema, API architecture, permission matrix, frontend state architecture, ListedKit feature alignment appendix)
- `velvet-elves-data/FRONTEND_UI_WORKFLOW_LOGIC.md` (section 4.6 Transaction Detail, section 6.4 AI Email Review, cross-cutting workflows A to L, especially E Communication and F AI Chatbot)
- `velvet-elves-data/STYLE_GUIDE.md` (full read, including the v2 Comfort Scale which supersedes v1 sizes)
- `velvet-elves-data/milestones.txt` (milestone structure; this work extends Milestones 3.x/4.x/5.x surfaces)
- `velvet-elves-data/TRANSACTION_PAGE_REDESIGN_SUPERIORITY_PLAN.md` and `TRANSACTION_WORKSPACE_TESTING_GUIDE.md` (the shipped workspace this plan builds on)
- `velvet-elves-data/AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md` and `AUTO_EMAILING_FRONTEND_UI_TESTING_GUIDE.md`
- `velvet-elves-data/AI_WIZARD_REDESIGN_SUPERIOR_PLAN_V2.md`, `AI_WIZARD_LISTEDKIT_PARITY_GAP_CLOSURE_PLAN.md`, `AI_WIZARD_REDESIGN_SUPERIOR_LISTEDKIT_PLAN.md` (the "AI proposes, the engine verifies, the human confirms once" architecture this plan generalizes)
- `velvet-elves-data/AI_AGENT_TRANSACTION_WORKSPACE_SUPERIOR_LISTEDKIT_PLAN.md` (the Codex reference plan, reviewed critically in section 3)

ListedKit references:

- All 16 screenshots in `velvet-elves-data/ai_agent_transaction/` (Screenshot_2 through Screenshot_17), mapped feature by feature in section 2
- ListedKit help center content (`listedkit.com/help`, Ava getting-started guide: capability levels, integrations, template configuration, best practices) and the Ava product pages (`listedkit.com/transactional-workflow-ai-assistant/`, `listedkit.com/ava/`). Note: `help.listedkit.com` blocks direct fetching (HTTP 403), so the help content was obtained through the mirrored help page at `listedkit.com/help` plus search-indexed article content. The Codex plan lists individual Intercom article URLs; I could not re-fetch those URLs to confirm their contents, so any claim sourced only from them is treated as unverified (see section 3.3).

Frontend source verified directly (not exhaustive, the load-bearing files):

- `src/pages/transactions/TransactionWorkspacePage.tsx` (current shell: 6 tab pills, sticky header, deep links `?tab` / `?task` / `?requirement`, workspace-wide drop, status control, quick actions)
- `src/components/workspace/`: `WorkspaceHeader.tsx` (DealOverviewCard, quick-action pills incl. `SyncDeadlinesButton`), `TimelineTab.tsx` (command bar with closed-intent executors, cascade routing), `ComplianceTab.tsx`, `DocumentsTab.tsx`, `TasksTab.tsx`, `PeopleTab.tsx`, `ActivityTab.tsx`, `CascadeEditor.tsx`, `AiEvidenceChip.tsx`, `TimelineMiniMap.tsx`, `DealBriefBand.tsx`
- `src/contexts/AiChatContext.tsx` and `src/components/active-transactions/AIChatPanel.tsx` (floating panel, in-memory conversation, `suggested_actions` prompt chips; no persistence)
- `src/components/wizard/WizardCommandBar.tsx` (closed-intent NL bar: classify via `/api/v1/ai/wizard-command`, deterministic preview, Apply, one-click Undo)
- `src/components/active-transactions/ComposeEmailModal.tsx`, `AddTaskModal.tsx`, `src/components/documents/AddDocumentModal.tsx`, `src/pages/AiEmailReviewPage.tsx`
- `src/hooks/useTransactionPlan.ts`, `useAiEmails.ts` (incl. `useTestInbound` at line 275), `useDocumentRequirements.ts`, `useDocuments.ts`

Backend source verified directly:

- `app/api/v1/dashboard.py` line 3730: `POST /dashboard/ai-chat` (stateless, read-only by design, frontend owns history, loads transaction context on demand, audit-logs `ai_chat`)
- `app/api/v1/transaction_plan.py`: `GET .../plan` (448), `POST .../plan/preview` (771), `POST .../plan/apply` (792, commit replay with `inverse_changes` undo), `PUT .../brief` (882)
- `app/api/v1/ai_emails.py`: `GET /drafts?transaction_id=` (205), `POST /compose` (225, role-gated, produces `pending_review`, never sends; takes `transaction_id`, `recipient_emails`, `intent`, `subject`, `body`, `template_id`), `POST /inbound/{log_id}/refile` (274), `POST /test-inbound` (354), templates CRUD (493+), settings (614+), `/{log_id}` (756), `/{log_id}/approve` (791), `/{log_id}/edit-and-send` (826), `/{log_id}/regenerate` (875), `/{log_id}/discard` (971). Verified: `_load_actionable_draft` checks tenant access only, not transaction access
- `app/api/v1/documents.py`: upload (399), list/transaction (547), download (580), ocr-geometry (611), PATCH metadata (654), versions (898), pages (935), split (960), email (1148), `POST /request` (1263, can send immediately through a connected provider), flag-deletion flows (1438+)
- `app/api/v1/document_requirements.py`: list (120), bulk (132), defaults (228), relink (263), PATCH `/{requirement_id}` (312; status vocabulary is `missing` / `uploaded` / `waived`; match/unmatch sets status)
- `app/api/v1/transactions.py`: `GET /{transaction_id}/history` (1837, merges transaction audits + communication logs + completed-task events)
- `app/api/v1/transaction_parties.py`: POST/GET/PUT/DELETE parties
- `app/api/v1/tasks.py`, `app/api/v1/communication_logs.py` (incl. `GET /transaction/{transaction_id}`)
- `app/api/v1/ai.py`: parse (430), resolve-documents (1236), recommend-tasks (1317), suggest-task-approach (1355), search-public-source (1569), intake/classify (1645), feedback (1715), wizard-command (1761, closed intent schema, returns `{"intent":"unknown"}` rather than guessing), parse-checklist (1802)
- `app/services/`: `plan_cascade.py`, `intake_intelligence.py`, `citation_check.py`, `ai_email_engine.py`, `calendar_sync.py`, `document_splitting.py`, `health_score_service.py`, `closing_checklist.py`, `state_rules.py`, `dependency_engine.py`, `timeline_planner.py`

Test suites that protect current behavior: backend 880 passing, frontend 244 passing (per the current uncommitted working tree after the wizard/workspace refinement pass), including the 7 tests in `src/tests/integration/TransactionWorkspace.test.tsx` and the 8 in `app/tests/test_transaction_plan.py`.

---

## 2. The ListedKit Model, Decoded

### 2.1 Screenshot-by-screenshot inventory

| Screenshot | What it shows | Details that matter |
| --- | --- | --- |
| 2 | The whole workspace | Roughly 50/50 split. LEFT: Ava chat. User uploaded a file into chat under a requirement chip ("EARNEST MONEY DEPOSIT RECEIPT") and typed "Run compliance scan on this document". Ava shows a collapsible "2 steps completed" agent-steps disclosure, a "Compliance Scan Complete" result card listing one issue ("Document Type Mismatch") with "Click to open", file chips ("TEST.PDF (0.13 MB)", "TEST.PDF, NOT_COMPLIANT"), then a conversational explanation: the uploaded file is actually a copy of the Purchase Agreement, the official receipt from Reliable Title Agency for the $5,000.00 deposit is needed, and an offer to draft the request email. Composer placeholder: "Ask a question, use / for commands, @ for mentions, # for references", plus attach (+), mic, send. Banner: "Connect your integrations to Ava" with provider icons. Disclaimer: "Ava can make mistakes. Verify important information." RIGHT: tab strip Timeline / Tasks / Details / Compliance / Email. HEADER: back chevron, editable address title, "4% Of Tasks Completed" progress bar, "Under Contract" status dropdown, kebab menu. |
| 3 | Timeline tab | "Deadlines" list + "+ New". Rows: name, weekday-spelled date, circle check, calendar icon (sync), edit, delete. |
| 4 | Connect Calendar modal | One-button "Connect Integration" (Google/Outlook). |
| 5, 6 | Edit/Add Deadline modals | Name, Date, "Relative date" toggle, Reminders list with "+ Add Reminder", Save/Cancel. |
| 7 | Tasks tab | Search, sort, "+ New". Rows: drag handle, circle check, name, blue envelope icon when auto-draft email is on, due date. |
| 8 | Task edit modal | Name, Due Date, Auto-draft email toggle, "Email Template (optional)" with helper "Ava will use this template when drafting the email. Leave empty for AI-powered template selection.", Relative date (Days, Direction Before/After, Relative to: Deadline / Task / Document, Related item select), "Tell Ava What To Do" instruction textarea, Notes, Related Compliance Item. |
| 9 | Add Task modal | Same fields plus Reminders. |
| 10, 11 | Details tab | Chips (BUYING, RESIDENTIAL), "Generate Summary" (PDF) button. Sections: Address card, Property cards (County, HOA, Parcel No, Tenant Occupied), Financing cards (Daily Possession Rent, Down Payment, Earnest Money), party card with role badge (ESCROW COMPANY), Terms section with contingency cards (Code Inspection, Damage, Financing, Home Warranty, Inspection, Title), each with per-card edit/delete. |
| 12 | Compliance tab | Checklist rows: drag handle, name, "Due:" date, linked-deadline chip (e.g. "DATE OF ACCEPTANCE"), status pill dropdown, shield scan icon (gray = not scanned, green = scanned), upload icon. |
| 13, 14 | Update Compliance Checklist modal | Name, Due Date (read-only when relative), Relative date (Days / Direction / Relative to Deadline-Task-Document / Related item), Description, Upload File dropzone, attached file row with "1 VERSION" chip + history/view/unlink/upload icons, "View Detailed Compliance Report (1 Issue)" button, Delete, status pill, Save. |
| 15 | Compliance status menu | Pending / Uploaded / Has Issues / Fully Executed. |
| 16, 17 | Email tab | Outbox / Inbox toggle, search. Outbox: "Draft from" account selector ("You can still change the account when composing or ask Ava to use a specific account"). Inbox empty state: "No incoming emails for this transaction yet. Emails received and matched to this transaction will appear here." |

### 2.2 The capability model from the help center

- Three capability levels: (1) housekeeping and Q&A (update dates, retrieve facts), (2) email and calendar (sync timelines with party invitations, draft emails with populated names/amounts/dates, send transaction summary PDFs), (3) compliance and document intelligence (shield-icon scans for missing signatures, date mismatches, required disclosures, data inconsistencies; multi-document analysis; relative-deadline calculation).
- A "3-transaction training model": Ava learns templates and workflow over the first three intakes; "Ava Rules" let users state plain-English preferences for how emails get written.
- Templates carry "when to use" triggers; compliance checklists import from CSV, screenshot, or paste; task templates carry "Email Task" tags for auto-drafting.
- 30+ chat commands; inbox monitoring that files inbound mail to the right deal; drafts replies from contract data.
- Layout per their own docs: center chat, right panel of structured tabs. The chat is the orchestration layer; the tabs remain the source-of-truth control panels.

### 2.3 What to take and what to beat

Per the established design-replication rule (layout from the comp, styling from our own in-app benchmark): the LAYOUT to take is the split agent-first workspace with the structured workbench beside it, the composer affordances (/, @, #, attach, drop), the issue-to-action conversation pattern, the per-tab modal anatomy (relative dates, related items, reminders), and the transaction-native Email tab. The STYLING stays ours: breadcrumb header, champagne/serif/mono voices, the v2 comfort scale, calm color discipline.

What ListedKit visibly does NOT do (our openings): no dependency cascade preview before a date change (their Edit Deadline modal edits a single date), no visible undo anywhere, no per-fact source citations in chat answers, no visible audit trail, single AI provider, no tenant governance over what the AI may do, no UI test harness, and their compliance status is manual-first (a dropdown) rather than evidence-first.

---

## 3. Verification of the Codex Reference Plan

Jan's instruction: use the Codex plan for reference, do not accept it as absolute truth. I checked its load-bearing claims against the source.

### 3.1 Claims verified TRUE (kept in this plan)

1. `POST /api/v1/dashboard/ai-chat` is stateless and read-only by design; the frontend owns conversation history (dashboard.py:3730 docstring confirms). Building writes into it would be wrong; a transaction-scoped agent router is the right move.
2. `POST /api/v1/ai-emails/compose` produces a `pending_review` draft and never sends (ai_emails.py:225). Correct safe path for agent-proposed emails.
3. `POST /api/v1/documents/request` CAN send immediately through a connected provider (documents.py:1263). It must never be wrapped as an AI-proposed action; reserve it for an explicitly labeled manual "send now" flow.
4. `_load_actionable_draft` checks tenant access only (verified in ai_emails.py). Agent wrappers must add transaction-level access checks for compose, draft reads, and draft actions.
5. `GET /transactions/{id}/history` merges transaction audits, communication logs, and completed-task events only; compliance/document/party audit rows do not surface there yet (also confirmed by the note inside `ActivityTab` and item O2 in the workspace refinement plan). Activity cannot be the universal proof surface until expanded.
6. Document split exists (`POST /documents/{id}/split`, documents.py:960) and merge does not. Merge stays out of v1.
7. `PATCH .../document-requirements/{requirement_id}` accepts `matched_document_id` and the agent layer must validate the document's tenant/transaction scope before matching (document_requirements.py:312+).
8. The mismatch guardrail: "Use AI type" must not silently convert a still-required checklist row into whatever the AI detected. Correct and adopted (section 11.1).
9. Cascade preview before any date apply, reusing `/plan/preview` and `/plan/apply` with `inverse_changes` undo. Correct and adopted.
10. The phase logic of "shell and durable read-only conversation first, writes second" is sound and adopted with modifications (section 13).

### 3.2 Claims corrected or tightened

1. The Codex plan proposes the agent pane at 56 to 60 percent width as a blanket replacement. Correction: Jake explicitly rejected a persistent AI side rail on this very page during the workspace redesign (it was removed as "whitespace and complexity"), and he iterated five rounds to reach the current full-width single-column shell. The split layout is exactly what Jan is asking for now, but it must ship (a) behind a feature flag, (b) with a one-click collapse that returns the workbench to the current full-width layout, with the choice remembered per user, and (c) through the established screenshot-approval loop before rollout. This is decision AW1, the first gate of the whole project.
2. The Codex plan says conversation history "is frontend session state only". Slightly imprecise: it is in-memory React state in `AIChatPanel.tsx` (no sessionStorage either). The fix (durable server threads) is the same.
3. The Codex plan's role list for authorization ("Agent, TransactionCoordinator, TeamLead, Admin") matches the code's `UserRole` usage in `ai_emails.py` (AGENT, TRANSACTION_COORDINATOR, TEAM_LEAD, ADMIN, ATTORNEY). Adopted with the note that requirements.txt calls the coordinator role "Elf"; the enum name in code is what matters.
4. The Codex plan defers `append_task_note` because "no canonical note surface exists". Tightened: `tasks.notes` exists as a column (SYSTEM_DESIGN 2.2.9) and `PATCH /tasks/{id}` can write it, but the workspace UI does not render task notes today, so the action stays deferred until the Tasks tab shows notes; otherwise the action would be invisible to testers, violating the UI-verifiability principle.
5. The Codex plan's Email tab Phase 4 includes "Scheduled" as a section. There is no scheduled-send capability in the backend; including it would promise a feature with no handler. Dropped from scope (listed under non-goals).
6. The Codex plan's metric "median clicks to resolve a missing document: 4 or fewer" is kept, but its UAT scripts assumed an Email tab exists before Phase 2 in some steps. This plan sequences the minimal Email panel into the same phase as the first email-producing action so every script is passable at the moment it ships.
7. The Codex plan treats voice input as a required composer control. Correction: nothing in the project supports dictation today and browser support (Web Speech API) is uneven. Voice becomes decision AW6, default off, never load-bearing for any workflow (mouse-first remains the rule).

### 3.3 Claims I could not verify (treated as unverified, not relied on)

- The 23 individual `help.listedkit.com` Intercom article URLs and their specific contents (the host returns 403 to fetchers; the Codex plan says it fetched them directly). Where this plan relies on ListedKit behavior, it relies on the screenshots and the fetchable marketing/help pages instead. Notably: ListedKit's "Always approve" rules and drag-into-chat are asserted by the Codex plan from those articles; the composer placeholder in Screenshot_2 confirms `/`, `@`, `#` exist, and "Always approve" is consistent with their "What Ava Handles Automatically" positioning, so both are treated as probably true but our design does not depend on copying them precisely.

---

## 4. What Velvet Elves Already Has (Verified Inventory)

The decisive fact of this project: almost every "hand" the agent needs already exists as a deterministic, tested endpoint. The work is orchestration, conversation durability, and UI, not new business logic.

### 4.1 Frontend

| Asset | Where | Relevance |
| --- | --- | --- |
| One-URL deal workspace, 6 tabs, sticky header, deep links | `TransactionWorkspacePage.tsx` | The workbench pane already exists, tested, styled to the approved benchmark |
| Closed-intent NL command bar with preview/apply/undo | `WizardCommandBar.tsx` + TimelineTab executors | The exact "classify only, execute deterministically" pattern the agent generalizes |
| Cascade preview/apply/undo UI | `CascadeEditor.tsx` | Reused as-is for every date action the agent proposes |
| AI evidence chips (citation snippet, confidence, page reference; the in-page locate viewer itself exists only in the wizard, R5) | `AiEvidenceChip.tsx`, `DocVerificationChip` | The citation vocabulary for agent messages |
| Classified upload with AI verification on every path | `AddDocumentModal.tsx`, DocumentsTab, page-wide drop | Chat-attach can route through this and inherit verification |
| Deal-scoped compose modal, mouse-first recipients | `ComposeEmailModal.tsx` | The agent's email proposals reuse its vocabulary |
| Full AI email review surface (assumptions bolded, source rail, attachments, approve / edit+send / regenerate / discard) | `AiEmailReviewPage.tsx` | Already stronger than anything visible in ListedKit's screenshots |
| Floating AI chat with transaction context + suggestion chips | `AIChatPanel.tsx`, `AiChatContext.tsx` | The conversational seed; gets superseded on this page by the agent pane |
| Calendar deadline sync button | `SyncDeadlinesButton` in `WorkspaceHeader.tsx` | ListedKit's Connect Calendar parity already exists |
| Post-closing feedback, print checklist, status lifecycle | workspace page | Untouched |

### 4.2 Backend

| Asset | Endpoint/service | Relevance |
| --- | --- | --- |
| Deterministic plan aggregate (header, dates, deadlines, requirements due, brief) | `GET /transactions/{id}/plan` | The agent's context backbone and the workbench's single paint call |
| Cascade dry-run + apply + inverse-changes undo + audit | `/plan/preview`, `/plan/apply` | The only legal way the agent changes dates |
| Requirements checklist CRUD, defaults, waive/unwaive, match/unmatch | `/document-requirements/*` | Compliance actions |
| Documents: upload, classify-verify, OCR geometry, pages, split, versions, email, flag-deletion | `/documents/*` | Document actions, evidence locating |
| AI emails: compose (pending_review), drafts by transaction, refile inbound, approve/edit-send/regenerate/discard, templates, settings, test-inbound | `/ai-emails/*` | Email actions and the UI-only test harness |
| Communication logs by transaction | `/communication-logs/transaction/{id}` | Email tab inbox/outbox data |
| Parties CRUD | `/transactions/{id}/parties` | People actions, @ mentions |
| Tasks CRUD with basis/auto_draft_email semantics, status changes | `/tasks/*` | Task actions |
| Read-only contextual chat with deterministic closing-date answers | `POST /dashboard/ai-chat` | Stays for the global panel; its context loader and the fixed-format closing-date rule carry over |
| Closed-intent command parser | `POST /ai/wizard-command` | Extended, not replaced, for agent intent classification |
| Citation verification (Python port of the frontend locate scoring) | `citation_check.py` | Every agent claim about a document must locate or demote |
| Intake intelligence verifier (AI proposes, engine verifies, dedupe, date windows, waives never auto-apply) | `intake_intelligence.py` | The verification philosophy the agent inherits |
| Multi-provider AI with admin switching and per-action provider audit | `ai_service.py`, tenant settings | A structural advantage ListedKit does not have |
| Health score, state rules, closing checklist, esign detection | services | Closing-readiness inputs |
| Audit logging with before/after and human-readable summaries | `audit_service.py` | Every agent apply writes here |

### 4.3 Governance and safety already in place

- Confidence threshold system with admin floor and team overrides (`/admin/confidence`, `confidence_settings` table).
- AI Governance page with Email Automation settings; tenant `ai_email` settings incl. auto-send threshold.
- Attorney guardrails (requirements 8.6): AI prepares, human decides; release/judgment endpoints are human-only.
- Fernet PII encryption, tenant RLS, immutable communication logs.

---

## 5. Gap Analysis: What Is Missing

1. Conversation is not durable. The floating panel's history dies on close/refresh. ListedKit's workspace treats the conversation as the work record.
2. Chat is read-only by design. There is no path from "the AI said it" to "the system did it" other than the user walking to a tab and doing it manually.
3. No typed action lifecycle. `suggested_actions` are prompt strings, not proposals with preview, approval, apply, result, and undo.
4. No structured references. The user cannot point at a document, task, deadline, requirement, party, or email inside the conversation; they can only describe them in words.
5. No issue objects. Compliance mismatches, overdue tasks, missing documents, and unanswered inbound emails are visible in their tabs, but nothing aggregates them into an actionable "what needs me now" stream with state (open / waiting / resolved).
6. No transaction-native Email tab. Outbound drafts live on `/ai-emails`, inbound logs live in Activity's communications panel; ListedKit puts both inside the deal.
7. No agent entry points on rows. No "Ask AI about this" affordance on a task, requirement, document, deadline, or party row; no drag-to-chat.
8. Chat-attached uploads do not exist (the page drop zone uploads to Documents, which is good, but the conversation does not know about it).
9. Activity tab cannot prove compliance/document/party/agent events yet (history endpoint is narrower than the audit log).
10. The header has no tasks-completed progress indicator (ListedKit shows "4% Of Tasks Completed"). The plan aggregate counts open and overdue tasks but not completed/total (`_HeaderCounts` has `open_tasks`, `overdue_tasks`, `missing_docs`, `overdue_docs` only), so this needs a small additive aggregate extension, not just UI.

---

## 6. Product Principles

1. The agent is the front door; deterministic APIs are the hands. The LLM interprets, explains, and proposes. Only typed, schema-validated, server-verified actions write anything, through the same endpoints the tabs use.
2. AI proposes, the engine verifies, the human confirms once. Generalizes the wizard's Part II architecture: every AI factual claim carries a citation that `citation_check` can locate, or it is demoted to "unverified" wording; every proposal is previewed from real data, never from LLM output.
3. Mouse-first, minimal typing. Every workflow in section 11 is completable with clicks alone; typing is only ever for naming things or optional free-text instructions. A proposed default always exists.
4. Everything is visible, nothing is silent. Every applied action lands in: the conversation (result card), the owning tab (row updates and flashes), the audit log, and (after the history expansion) Activity. Every apply response names its `visible_success_location` so testers know exactly where to look.
5. Undo where the backend can honestly undo. Date cascades (inverse changes), waives (un-waive), task removal (Skipped + restore), matches (unmatch). Where undo is impossible (a sent email), the action says so before approval.
6. The frontend is the acceptance surface. Real estate professionals must be able to validate every behavior from the UI: no DB inspection, no Swagger, no log tailing. Honest empty states; no demo data on real surfaces; the UAT fixture harness is explicit opt-in and creates real records through real APIs.
7. Legal boundaries are non-negotiable. The agent may summarize, compare, flag, draft, prepare, organize. It may not make legal determinations, release packets, decide legal equivalence, waive compliance without a human reason, or send anything externally without review in v1.
8. Layout from the comp, styling from the house. The split workspace layout comes from the ListedKit screenshots; every token, voice, and component comes from STYLE_GUIDE v2 and the existing workspace benchmark. The breadcrumb header stays.
9. Honest AI voice. Deterministic answers for deterministic questions (the closing-date fixed format stays code-rendered, never LLM-paraphrased). "I could not find that in this transaction's documents" is a first-class answer. The ListedKit-style disclaimer appears under the composer.

Scope boundary for roles: the agent workspace targets the internal ops workspace (Agent, TransactionCoordinator, TeamLead, Admin). Attorneys reach `/transactions/:id` as the Matter Workspace and keep it unchanged; an attorney-facing agent is future work and must inherit the requirements 8.6 guardrails (AI prepares, the attorney decides) from day one. Client, FSBO, and Vendor roles never see the agent workspace (they cannot reach this route today; that stays true).

Non-goals for this project: scheduled sends, document merge, SMS/voice channels, auto-send expansion beyond the existing tenant threshold system, attorney auto-release, mobile app. Architecture must not block them; scope must not include them.

---

## 7. Target UX Specification

### 7.1 Desktop layout (>= 1280px)

```
+----------------------------------------------------------------------------------+
| Sticky header (UNCHANGED anatomy, full width)                                     |
|  Deals > Transactions > 4567 Oak Ridge Avenue          [breadcrumb, Briefcase]    |
|  Serif identity row + stage pill + inline address      [+ NEW: task progress bar] |
|  Champagne AI next-step strip                                                     |
|  Tab pills (workbench tabs) ........ quick-action pills [+ NEW: Agent pane toggle]|
+------------------------------------+---------------------------------------------+
| AGENT PANE (~55%)                   | WORKBENCH PANE (~45%)                        |
|                                     |                                              |
|  Needs-you strip:                   |  DealOverviewCard (stat band, tracking       |
|   [2 blockers] [1 draft waiting]    |   chips, brief) collapses to a summary row   |
|   [3 due this week] [readiness]     |   in split mode                              |
|                                     |                                              |
|  Conversation stream:               |  Active tab card (Timeline | Compliance |    |
|   - user + agent messages           |   Documents | Tasks | People | Activity |    |
|   - issue cards                     |   Email)                                     |
|   - action proposal cards           |                                              |
|   - applied/result cards w/ Undo    |  Rows referenced by the conversation flash   |
|   - evidence chips (page+snippet)   |   champagne; "Ask AI" affordance per row     |
|                                     |                                              |
|  Composer:                          |                                              |
|   [+] [text area..............]     |                                              |
|   / commands  @ parties  # items    |                                              |
|   [attach] [mic?] ......... [Send]  |                                              |
|   "The AI can make mistakes.        |                                              |
|    Verify important information."   |                                              |
+------------------------------------+----------------------------------------------+
```

Layout rules:

- The page keeps owning its scroll (AppLayout's main is overflow-hidden). In split mode each pane owns an independent `flex-1 min-h-0 overflow-y-auto` scroll region; the header stays sticky above both.
- The Agent pane toggle (a pill in the header controls row) collapses the agent pane entirely and restores the current shipped full-width single-column workspace, byte-for-byte. The choice persists per user in `profile_settings_json` through the existing profile-settings mechanisms (`PUT /users/me`; the `/users/me/dashboard-layout` preference endpoint is the precedent for a dedicated preference route if one is wanted). This is the safety valve for the AW1 layout decision and for users who want the classic view.
- Width split defaults 55/45 with a draggable divider snapping to 50/50, 55/45, 60/40 (persisted). Minimum workbench width 480px.
- The tab pills move with the workbench (they label the right pane in split mode). Quick-action pills stay in the header.
- New header element: a slim task-progress indicator next to the stage pill ("12 of 38 tasks complete", mono tabular numerals, thin champagne bar). Backend prerequisite: extend `_HeaderCounts` in the plan aggregate with `tasks_completed` and `tasks_total` (additive, computed in the same pass that already derives `open_tasks`; no new query). Matches ListedKit's "% Of Tasks Completed" with honest absolute numbers.

### 7.2 Narrow screens (< 1280px)

- The split collapses to the current single-column workspace plus an "Agent" tab pill as the FIRST pill. The agent pane becomes tab content; the composer is sticky at the bottom of it.
- All action cards stack full width. Drag-to-chat is replaced by the per-row "Ask AI" button (which is always present at every width; drag is an enhancement, never the only path).

### 7.3 Styling (normative, from STYLE_GUIDE v2)

- Conversation body and composer input: 15px / 1.6. Message meta and chips: >= 12px. Section/serif titles 20px. No text below 12px anywhere.
- The agent's messages render on `ve-surface` with no avatar mascots; the user's on `ve-surface-2`. The single AI accent is champagne. Issue severity uses the status triads (red blocker / amber warning / neutral watch), always bg+border+text.
- Issue cards and action cards are the one card vocabulary (12px radius, hairline border, shadow-soft), with the 4px severity rail pattern from the dashboard action-queue spec for issue cards.
- Evidence chips reuse the `AiEvidenceChip` anatomy: `AI · 93%` confidence chip expanding to the snippet and "Page N, view in document". Until Phase 3 that link opens the Documents tab on the cited file (the chip's existing honest behavior); from Phase 3 it opens the new `SourceViewerDrawer` (the wizard's `WizardPdfDocument` viewer + OCR geometry + the `ocrHighlight` locate utilities, mounted in a workspace drawer) at the cited page with the snippet highlighted. The workspace has no document viewer today; this drawer is a real new component, not a reuse claim.
- Buttons: one filled brand-orange primary per action card (Approve / Create Draft / Apply); ghost secondary (Edit, Dismiss); destructive uses the charcoal discard pattern. Approve is never the default focused control; nothing applies on Enter alone.
- Empty agent pane state (new deal): one sentence plus three starter chips ("What needs my attention?", "Are we ready to close?", "Draft a welcome email"), per the explanatory-not-apologetic rule. No illustrations.
- The composer disclaimer line: 12px `ve-text-muted`, "The AI can make mistakes. Verify important information." (ListedKit parity, honest voice.)

### 7.4 The composer

- `+` button opens the reference picker (popover with tabs: Documents, Tasks, Deadlines, Requirements, People, Emails; search within; click to insert a chip). 100 percent mouse-driven.
- `/` opens the command menu (mouse-selectable; typing filters): `/draft-email`, `/request-document`, `/scan` (compliance scan), `/summarize`, `/compare`, `/add-task`, `/add-deadline`, `/move-date`, `/readiness`, `/help`. Each command inserts a guided card, not raw text (e.g. `/draft-email` opens recipient chips + intent field, mirroring ComposeEmailModal's vocabulary).
- `@` filters this transaction's parties (from `/transactions/{id}/parties`); `#` filters documents, tasks, deadlines, requirements (from the plan aggregate + documents list). Both insert typed chips.
- Attach: clicking the paperclip or dropping a file onto the composer routes through the existing classified-upload dialog (AddDocumentModal anatomy: file + name + type), uploads via `/documents/upload`, inherits the AI verification chip, then inserts a document reference chip into the conversation with a system note "Uploaded {name} ({type})". The existing page-wide drop zone keeps its current instant-upload behavior; only a drop specifically on the composer goes through chat.
- Mic: hidden by default (decision AW6).
- Send: paper-plane button; Enter sends, Shift+Enter newlines.

### 7.5 Workbench choreography

- Every row in every tab gets a small ghost "Ask AI" sparkle button (44px hit area) that inserts that row's reference chip into the composer and focuses it. Rows are also draggable (`application/x-ve-agent-ref` + text/plain fallback); dropping on the composer inserts the chip and mutates nothing.
- When the conversation references an entity (chip click, proposal preview, applied result), the workbench switches to the owning tab via the existing deep-link params and flashes the row (the `?task=` / `?requirement=` flash mechanics already exist; extend with `?document=`, `?deadline=`, `?email=`).
- After an apply, the owning tab's queries invalidate (same React Query keys the tabs already use), so the proof is the live tab, not a claim in chat.

### 7.6 Email tab (new workbench tab)

Phase E1 subset (ships with the first email-producing action):

- "Outbox" list: pending AI drafts for this transaction (`GET /ai-emails/drafts?transaction_id=`) + sent outbound logs (`GET /communication-logs/transaction/{id}` filtered to email/outbound). Status pills: Pending review / Sent / Discarded. Row click opens the draft review (embedded drawer reusing the AiEmailReviewPage card anatomy; "Open full review" links to `/ai-emails/:id`).
- Banner when drafts exist: "N drafts waiting. Nothing sends without your approval."

Phase E2 full tab:

- Outbox / Inbox pill toggle (ListedKit parity), search within each.
- Inbox: inbound communication logs for this transaction, each with the existing match-basis badge (how the system filed it here) and a "Move to another deal" action wrapping `/ai-emails/inbound/{log_id}/refile`.
- "Needs filing" entry point: deferred until an unmatched-inbound list endpoint exists (known gap from the auto-emailing plan); the tab links to the global review queue meanwhile. Honest scoping, no dead UI.
- Test mode: a "Send test inbound to this deal" control reuses the existing `TestInboundButton` / `useTestInbound` (the endpoint is role-gated to internal roles, offers the three fixed scenarios `closing_question` / `document_request` / `vendor_reply`, creates an inbound log plus AI draft tagged `metadata_json.test = true`, and sends nothing external). Hiding the button on production tenants is a frontend visibility choice (same flag family as the UAT fixtures), not an endpoint property.
- "Draft from" account display: shows the user's connected provider account (from integrations); a per-transaction account SELECTOR is decision AW8 (only meaningful for users with multiple connected accounts).

### 7.7 Details consolidation (later phase, decision AW7)

ListedKit's Details tab (screenshots 10, 11) maps to our DealOverviewCard + PeopleTab + term rows. Proposal: a Details tab consolidating property facts, financing, terms (term rows already in the plan aggregate), parties, and a "Generate summary" action (print/PDF via the existing checklist/print utilities, extended with the deal brief). Not a v1 dependency; the existing tabs already expose the data.

---

## 8. The Interaction Model

### 8.1 Reference chips

```json
{
  "ref_type": "document | task | deadline | requirement | party | email",
  "ref_id": "uuid",
  "label": "Earnest Money Deposit Receipt",
  "transaction_id": "uuid",
  "source": "user_pick | user_drag | row_ask_ai | ai_detected"
}
```

Labels are display-only; the server re-resolves every `ref_id` against the transaction and tenant and rejects foreign references. Chips never carry decrypted PII payloads (emails/phones resolve server-side at render time).

### 8.2 Message kinds

`chat` (user/agent text), `issue` (detected problem card), `action_proposed`, `action_applied`, `action_dismissed`, `action_failed`, `system` (e.g. "Uploaded test.pdf"). All durable, transaction-scoped, restored on refresh and across devices.

### 8.3 Issue cards

Fields: title, issue_type, severity (`blocker` / `warning` / `watch`), status (`open` / `proposed` / `waiting_on_user` / `waiting_on_external` / `resolved` / `dismissed`), source_refs, impact sentence, recommended action buttons.

v1 issue detectors are DETERMINISTIC (no LLM in detection; the LLM only words the explanation):

| Detector | Source of truth |
| --- | --- |
| Document type mismatch | document AI verification result vs requirement (the existing DocVerificationChip data) |
| Missing required document due/overdue | requirements list + due rules from the plan aggregate |
| Overdue / blocked tasks | tasks list |
| Draft waiting for review | pending AI drafts for the transaction |
| Inbound email needing a response | inbound log newer than the last outbound in its thread |
| Party missing email (blocks sends and auto-draft eligibility) | parties list |
| Unsigned document in flight | documents signature_status |
| Date conflict / anchor gap | plan aggregate (e.g. closing before inspection response) |
| Closing readiness (window-based) | composite of the above + health score inputs |

### 8.4 Action proposal cards

Anatomy: title, plain-English summary, BEFORE and AFTER preview (from real data), source/evidence chips, confidence chip, risk label, undo availability statement, buttons: Approve (filled), Edit (ghost, opens the same editor the tab uses), Dismiss (ghost, optional reason). After apply: result card with `visible_success_location`, affected refs (clickable), Undo chip where supported, and a link to the audit entry.

### 8.5 Approval policy (v1, non-negotiable)

- Every write requires explicit human approval. No always-approve in v1 (that is Phase 5, decision AW5, and even then never for sends, waives, deletions, date applies, or anything attorney-gated).
- Email actions create `pending_review` drafts only; sending stays in the review surfaces.
- Date changes require a fresh cascade preview; stale previews block with "Refresh preview".
- Waives and dismissals require a reason (quick-pick chips + optional text).
- Deletions remain flag-for-deletion / soft-delete flows.
- The agent never claims success the apply endpoint did not confirm.

---

## 9. Backend Architecture

### 9.1 New router and services

New transaction-scoped router `app/api/v1/transaction_agent.py` (registered in `router.py`), nested under the transaction prefix like `transaction_plan.py`:

```
GET  /api/v1/transactions/{id}/agent              # bootstrap: threads, open issues, needs-you counts
GET  /api/v1/transactions/{id}/agent/messages     # paged conversation (per thread or merged stream)
POST /api/v1/transactions/{id}/agent/chat         # user turn: text + reference chips -> agent reply, maybe issues/proposals
POST /api/v1/transactions/{id}/agent/scan         # run deterministic detectors (and document scan when a doc ref is given)
POST /api/v1/transactions/{id}/agent/actions/{action_id}/preview
POST /api/v1/transactions/{id}/agent/actions/{action_id}/approve
POST /api/v1/transactions/{id}/agent/actions/{action_id}/dismiss
POST /api/v1/transactions/{id}/agent/actions/{action_id}/undo
GET  /api/v1/transactions/{id}/agent/refs?q=      # server-side reference search for the picker (# and @)
```

New services, mirroring the layering of `plan_cascade.py` and `intake_intelligence.py`:

- `agent_context.py`: assembles the context packet (section 9.3) with provenance; reuses the dashboard chat's transaction context loader and the deterministic date-facts (the fixed closing-date format rule carries over verbatim).
- `agent_intents.py`: extends the wizard-command pattern; the LLM classifies one utterance plus chips into a CLOSED intent schema (section 10 action types + `question` + `unknown`), temperature 0, never executes. Unknown returns an honest "I can't do that yet" with the supported-commands list.
- `agent_actions.py`: the registry: per action type, a `validate -> preview -> apply -> undo` quad that calls the SAME service/repository code paths the canonical endpoints use (refactor those handlers into shared service functions where they currently live inline in routers, without changing the public endpoints or their tests).
- `agent_issues.py`: the deterministic detectors.
- `agent_policy.py`: per-action-type policy (requires_approval, undo_available, forbidden roles, reason_required), with the forbidden list (legal determinations, releases, external sends) hard-coded, not configurable.
- `agent_threads.py`: persistence for threads/messages/actions.

`POST /dashboard/ai-chat` is untouched and remains the global floating panel's endpoint. On the workspace route, the frontend's `AiChatContext.open()` focuses the agent pane instead of the floating panel (other pages keep the panel).

### 9.2 Wrapper safeguards (all verified necessary)

- Every agent endpoint resolves the transaction through the same access checks the workspace plan endpoints use, BEFORE loading context or touching actions.
- `compose_email_draft` wrappers validate transaction access before calling the compose engine (the compose endpoint itself only role-gates; verified).
- Draft reads/actions surfaced in the workspace re-check that the log's `transaction_id` matches (the underlying `_load_actionable_draft` is tenant-scoped only; verified).
- `attach_document_to_requirement` validates the document exists, same tenant, same transaction, before patching `matched_document_id` (the PATCH endpoint does not enforce this today; verified).
- Every apply re-checks existence and freshness (updated_at / preview hash); stale returns HTTP 409 with a UI-readable "Refresh preview" payload, applies nothing.
- Idempotency: every action carries a client `commit_id`; replays return the original result (same pattern as the requirements bulk endpoint).

### 9.3 Context packet

Structured JSON + compact markdown summary for the LLM, every fact with provenance:

- Plan aggregate (dates, term rows, deadlines, requirements due, brief, counts).
- Tasks, requirements, documents (with verification results), parties (names/roles; emails only as "present/absent" flags unless a send is being drafted), pending drafts, recent communications (capped), recent audit summaries (capped).
- The user's open issues and recent agent actions (so the agent does not re-propose what was dismissed).

Caps: newest-first windows per source (configurable, default 25 rows each); older history is summarized; source refs always point back to canonical rows. Facts about document CONTENT enter the packet only with page+snippet citations that `citation_check.verify` can locate; claims that fail to locate are dropped or demoted exactly as the intake intelligence verifier does.

### 9.4 Audit and Activity expansion

- Every apply writes `audit_logs` (action `agent_action_applied`, entity `agent_action`, before/after, human-readable summary naming the wrapped operation) IN ADDITION to whatever the wrapped endpoint already logs. Dismissals log with reasons.
- Expand `GET /transactions/{id}/history` to merge transaction-linked `document_requirement`, `document`, `transaction_party`, `ai_email`, and `agent_action` audit rows (this also closes the pre-existing O2 item the Activity tab notes). Until this ships, every UAT script's proof surface is the owning tab + the agent thread, never Activity.

### 9.5 LLM usage summary (provider-agnostic, per requirements 8.1a)

| Use | Mode | Guardrail |
| --- | --- | --- |
| Intent classification | Closed schema, temperature 0 | Unknown intent mutates nothing |
| Grounded Q&A | Context packet only | Citations verified by citation_check; deterministic answers (closing date) rendered by code |
| Issue explanation wording | Facts from detectors only | The card's facts never come from the LLM |
| Email drafting | Existing ai_email_engine | pending_review only, assumptions bolded, source rail |
| Document scan narrative | Existing parse/verification outputs | Result card lists deterministic findings; LLM words the summary |

All calls route through `AIService` so OpenAI/Claude switching and per-action provider audit keep working.

---

## 10. The Typed Action Registry (Verified Handler Map)

Every action wraps a VERIFIED existing endpoint or service. No new business logic in v1 except the thin validation described above.

| Action type | Wraps (verified) | Preview source | Undo | Notes |
| --- | --- | --- | --- | --- |
| `compose_email_draft` | `POST /ai-emails/compose` | Rendered draft intent (recipients, subject, intent, template) | n/a (draft is discardable) | Creates pending_review; never sends |
| `compose_document_request_draft` | `POST /ai-emails/compose` | Same + requirement context | n/a | NEVER `/documents/request` (can send immediately) |
| `regenerate_email_draft` / `discard_email_draft` | `/ai-emails/{id}/regenerate`, `/discard` | Draft state | n/a | Transaction match re-checked |
| `file_inbound_email` | `POST /ai-emails/inbound/{id}/refile` | Target deal summary | refile back | Phase E2 |
| `attach_document_to_requirement` | `PATCH .../document-requirements/{id}` (`matched_document_id`) | Requirement + document cards | `detach` | Cross-transaction match rejected server-side |
| `detach_requirement_document` | same PATCH (unmatch) | Current match | re-match | Leaves requirement missing, honestly |
| `waive_requirement` / `unwaive_requirement` | same PATCH (status) | Requirement card | yes (inverse) | Reason required; never auto-approved |
| `update_requirement_rule` | same PATCH (due rule fields) | Server-resolved new due date | restore prior rule | Same editor the Compliance tab uses |
| `reclassify_document` / `rename_document` | `PATCH /documents/{id}` | Before/after metadata | restore prior | Reclassify changes the DOCUMENT only; it never touches a requirement |
| `adopt_ai_type_for_requirement` | `PATCH .../document-requirements/{id}` (`doc_type`) + `PATCH /documents/{id}` | Before/after on both rows | restore prior types | The "this checklist row is mislabeled" path. Requires the explicit mislabeled-row confirmation in the payload (the agent layer enforces it); mirrors what `ComplianceTab.adoptAiType` does today, which is one-click with no confirm: aligning that shipped control with the same single-question confirm is a Phase 2 deliverable (endpoint contract unchanged) |
| `split_document` | `GET /documents/{id}/pages` + `POST /documents/{id}/split` | Page ranges + resulting names | no (stated) | PDF only |
| `create_task` / `create_deadline` | `POST /tasks` (kind/basis server-resolved) | Resolved due date + basis chip | Skip task | Deadline = the existing deadline-task path |
| `update_task` / `toggle_task_auto_email` | `PATCH /tasks/{id}` | Before/after fields | restore prior | Auto-email eligibility = target resolves to a party email (existing rule) |
| `change_task_status` | `PUT /tasks/{id}/status` | Status transition | inverse status | Remove-from-plan = Skipped + Undo, per the workspace pattern |
| `preview_date_cascade` | `POST .../plan/preview` | The cascade diff itself | n/a | Mandatory before any apply |
| `apply_date_cascade` | `POST .../plan/apply` | Fresh preview hash | yes (`inverse_changes`) | The ONLY way the agent changes any date |
| `add_party` / `update_party` | `/transactions/{id}/parties` (POST / PUT) | Party card | add: DELETE the created party; update: restore prior values | No raw PII into agent JSON |
| `run_compliance_scan` | existing background parse (`/ai/parse`) for not-yet-parsed documents + deterministic doc-type comparison against persisted `ai_extracted_data.document_type_detected` + the section 8.3 detectors | n/a (read) | n/a | There is no dedicated verify endpoint; already-parsed documents are never re-parsed (the shipped G5 rule). Produces issue cards |
| `summarize` / `compare_documents` / `answer` | context packet + AI service | n/a (read) | n/a | Citations mandatory |
| `closing_readiness` | detectors + plan + health inputs | n/a (read) | n/a | Deterministic score, AI-worded explanation |

Deferred (no honest handler today, listed so nobody promises them): `merge_documents`, `append_task_note` (until task notes render in the Tasks tab), `schedule_send`, needs-filing queue (until the unmatched-inbound list endpoint exists), SMS/voice anything.

Forbidden permanently (policy layer, tested): legal determinations, packet release, same-day disbursement exceptions, compliance waive/dismiss without human reason, external send without review.

---

## 11. End-to-End Workflow Designs (Each With a Mouse-Only UI Test)

### 11.1 Document type mismatch (the ListedKit Screenshot_2 scenario, done better)

Trigger: a file attached to the "Earnest Money Deposit Receipt" requirement; AI verification reads it as a Purchase Agreement (this detection already exists and renders as a chip in the Compliance tab).

State precision (R1): attaching a file sets the requirement's status to `uploaded`. So the dangerous condition is not "missing", it is "looks satisfied but is not": the row sits in the Uploaded group wearing a mismatch chip. The issue card must say exactly that.

Agent behavior:

1. Issue card "Document type mismatch" (severity: blocker if the requirement is due/overdue, else warning), citing the file with page+snippet evidence. Impact line: "This requirement currently reads as satisfied, but the attached file is a Purchase Agreement, not the earnest money receipt."
2. Primary remediation (one proposal, two bundled steps, both previewed): detach the wrong file from the receipt requirement (`detach_requirement_document`, returning the row honestly to Missing) and draft a request to the title company for the correct receipt (`compose_document_request_draft`; recipient pre-picked from parties, with "Add email for the title company" proposed first if the party has no email). The user can also take either step alone.
3. Secondary actions: (a) Upload the correct receipt now (opens the existing attach modal on the requirement; the wrong file is detached as part of re-attaching), (b) keep the file but file it correctly: `reclassify_document` to Purchase Agreement, which never touches the requirement, (c) waive the requirement (reason required), (d) "the checklist row itself is mislabeled": `adopt_ai_type_for_requirement`, gated on the explicit confirmation.
4. Guardrail (hard, agent-layer): `adopt_ai_type_for_requirement` is rejected unless the payload carries the explicit mislabeled-row confirmation. A wrong attachment can never silently satisfy or rewrite a still-required document slot. Companion deliverable: the existing one-click "Use AI type" in the Compliance tab (which today rewrites both the requirement's expected type and the document's classification with no confirm, `ComplianceTab.adoptAiType`) gains the same single-question confirm dialog so the two paths agree. This is a deliberate change to a shipped control; the PATCH endpoint contract does not change.

UI test (mouse only): attach the wrong PDF from Compliance > the row lands in Uploaded with the mismatch chip > click the row's "Ask AI" > issue card appears in the agent pane stating the looks-satisfied danger > approve the bundled detach + draft proposal > Compliance shows the receipt requirement back in Missing > open the Email tab and see the pending draft, status "Pending review" (when the draft was composed from intent, the engine's grounded source data shows in the review rail; the proposal card itself always cites the requirement and the mismatched file) > nothing was sent (no sent row in Outbox).

### 11.2 Missing document chase

Trigger: requirement missing and due within N days (or overdue). Agent proposes `compose_document_request_draft` with the recipient picked by role from parties (clickable choice when ambiguous). Approval creates the pending draft; the requirement stays missing until a real upload/attach. The proposal card cites the requirement and its due rule; the draft itself carries the engine's grounded source data when composed from intent (a deterministic template body shows an honestly empty source rail, R7).

UI test: open agent pane > "needs-you" strip shows the missing-doc count > click it > click the issue > click recipient chip > Create draft > verify in Email tab > approve or edit/send from the review drawer > Compliance row flips to uploaded only after the actual document is attached, never from the email.

### 11.3 Date moved by addendum

Trigger: user drops an addendum into the composer, or types "closing moved to May 27", or clicks the deadline row's Ask AI.

Flow: (1) if a document was referenced, the agent extracts the new date WITH a citation chip the user can click to see the page; the user confirms or edits the date (one click on a date chip, or the date input); (2) the agent runs `preview_date_cascade` and renders the existing CascadeEditor diff (moved rows, not-moved rows with honest reasons: pinned/completed/no_rule/no_anchor); (3) Apply; (4) result card with Undo chip and a calendar re-sync recommendation chip when integrations exist (existing behavior). Parsing an addendum NEVER writes a date; the only write is `/plan/apply` after a fresh preview.

UI test: drop addendum on composer > classified-upload dialog > uploaded chip appears in chat > ask "update the closing date from this addendum" > click the citation chip and see the page > click "Preview changes" > see moved/not-moved > Apply > Timeline tab shows new dates > click Undo > dates revert > Activity/audit records both.

### 11.4 Overdue task rescue

Trigger: task overdue. Issue card offers: mark complete, move the due date (through the basis/rule editor or cascade when the task is anchor-derived), draft the related email (auto-draft-eligible targets), skip with undo, create a follow-up task. Each is a one-click proposal; the Tasks tab row flashes after apply.

UI test: click the overdue chip in the needs-you strip > pick a task > click "Draft the email" > approve > pending draft visible in Email tab > toggle auto-draft from the same card > Tasks tab shows the toggle changed.

### 11.5 Document Q&A, comparison, and scan

Read-only: drop one or more documents into the composer (or # reference them), ask anything. Answers carry per-fact citation chips, server-verified against OCR geometry by `citation_check` (a fact that cannot be located is answered as "I could not verify this in the documents"); clicking a chip opens the new `SourceViewerDrawer` at the cited page with the snippet highlighted (R5: this drawer is a new workspace component reusing the wizard's viewer and the `ocrHighlight` locate utilities; it ships in this phase). `/compare` renders a deterministic field-by-field comparison (price, dates, parties) using the existing parse outputs, with both citations per row. `/scan` runs the parse for not-yet-parsed documents plus the deterministic type comparison and the section 8.3 detectors, and emits issue cards, ListedKit's shield scan as a conversation citizen.

UI test: # reference the purchase agreement and the counteroffer > "/compare" > table with citation chips both sides > click a chip > the SourceViewerDrawer opens at the cited page > ask a question whose answer is not in the documents > agent says it cannot find it (no fabrication).

### 11.6 Inbound email resolution

Trigger (test mode): "Send test inbound to this deal" in the Email tab (the existing `TestInboundButton` wrapping `/ai-emails/test-inbound`, scenario picker offering the three real scenarios: closing question, document request for the inspection report, vendor scheduling reply). The inbound appears in the Inbox with its match-basis badge (`test` for synthesized mail); the engine's draft (existing behavior) surfaces as a "draft waiting" issue; the user reviews/edits/sends from the embedded review drawer. Misfiled mail: "Move to another deal" wraps refile.

UI test: entirely UI-driven via the test-inbound button (pick the "document request" scenario); proof surfaces are the Inbox row, the draft drawer, and the sent status after approval.

### 11.7 Closing readiness

`/readiness` or the readiness chip: deterministic checklist (open/overdue tasks, missing/mismatched documents, unsigned documents, pending drafts, party gaps, date conflicts, attorney gates flagged as human-owned) each rendered as a clickable issue with its one-click next action; a score with honest inputs; explicitly NOT a legal opinion (stated on the card).

UI test: click Readiness > resolve one blocker through its card > readiness recomputes > attorney-gated items show "needs attorney review" and offer no AI action.

### 11.8 Generalized "tell the agent what to change"

Everything the Timeline command bar does today (add_deadline, set_core_date, set_term_days, waive_requirement, toggle_auto_email) becomes agent intents with the same closed-schema classification and the same preview-then-apply-then-undo, so the agent pane is a strict superset of the command bar. The command bar stays in the Timeline tab (it is shipped and tested); both routes converge on the same executors.

---

## 12. Superiority Ledger: Velvet Elves vs ListedKit

Parity (must match):

| ListedKit | Velvet Elves answer |
| --- | --- |
| Chat-centered transaction page, tabs beside it | Split agent workspace, existing tabs as the workbench |
| `/` commands, `@` mentions, `#` references, attach, drop | Composer spec 7.4, all mouse-first |
| Compliance scan from chat with issue cards | `/scan` + deterministic detectors + verification chips |
| Auto-draft email per task, optional template, AI template selection | Already shipped (auto_draft_email + email_templates + compose template_id) |
| Relative dates on deadlines/tasks/requirements with related items | Already shipped (server-resolved rules, basis chips) |
| Status pills, mouse-first row actions | Already shipped |
| Calendar connect/sync | Already shipped (SyncDeadlinesButton + integrations) |
| Transaction-native Email tab (Outbox/Inbox) | Phases E1/E2 |
| Tasks-completed progress in header | New slim progress indicator (plan aggregate gains `tasks_completed`/`tasks_total`, R4) |
| "Ava can make mistakes" honesty line | Composer disclaimer |

Surpass (ListedKit shows nothing comparable):

1. Evidence or it didn't happen: per-fact citation chips in chat, server-verified by citation_check, with locate-in-document jumps once the `SourceViewerDrawer` ships (Phase 3). ListedKit cites sources at intake; our agent cites in every answer.
2. Cascade preview with honest not-moved reasons before any date change, plus one-click Undo from inverse changes. Their Edit Deadline modal edits one date blind.
3. Undo as a system property (dates, waives, skips, matches), stated per action before approval.
4. A durable, transaction-scoped conversation that doubles as a work log, with every applied action linked to an audit entry (who, what, before/after, which AI provider).
5. Draft safety that is already stronger: assumptions bolded, source-data rail, attachment chips that prove attachments, escalation reminders, tenant auto-send thresholds with an admin floor.
6. Tenant governance: per-action policy, confidence thresholds, AI Governance surface, multi-provider switching with per-action provider audit.
7. Attorney-safe boundaries as enforced policy, not prose.
8. A UI-only UAT harness (test inbound, fixture setup) so non-developer testers can validate everything; honest empty states, no demo data on real surfaces.
9. Deterministic answers for deterministic questions (the fixed closing-date format), instead of LLM paraphrase roulette.
10. Closing readiness composed from real plan/compliance/task data with one-click remediation per blocker.

---

## 13. Implementation Phases

Each phase is independently shippable, behind the `agent_workspace_v1` feature flag (tenant + user), and ends with green suites plus headless screenshots for Jake.

### Phase 0: Flag, skeleton, and safety inventory (small)

- Feature flag plumbing; flag off = zero UI change (assert by snapshot test).
- Agent pane toggle + persisted preference; split shell renders with the EXISTING tabs unchanged in the right pane; agent pane shows the read-only floating-panel chat content temporarily.
- Backend: router skeleton (bootstrap + refs search only), `agent_policy.py` with the forbidden list, the wrapper-safeguard helpers (transaction access, document-scope validation) written and unit-tested against the known gaps (compose transaction check, draft transaction match, matched_document_id scope).
- Screenshot round with Jake on the split layout (AW1 gate).

Acceptance: existing 244 frontend / 880 backend tests untouched and green; flag off renders the current page identically; layout screenshots approved.

### Phase 1: Durable conversation, references, choreography (read-only)

- Migrations: `agent_threads`, `agent_messages` (section 14).
- `POST .../agent/chat` (read-only answers, context packet, citations verified, deterministic closing-date answer preserved), `GET .../agent`, `GET .../agent/messages`, `GET .../agent/refs`.
- Composer with `+` picker, `/` menu (read-only commands enabled: summarize, compare, readiness-lite, help), `@` and `#` pickers, attach-through-classified-upload, drop-on-composer.
- Per-row "Ask AI" buttons + drag refs in all six tabs; workbench flash for `?document=`/`?deadline=`/`?email=` added to the existing deep-link mechanics.
- Needs-you strip fed by the deterministic detectors (read-only: clicking scrolls to the issue card; no writes yet).

Acceptance: refresh keeps the conversation; every ref type insertable by mouse; answers cite or honestly decline; zero write paths exist (verified by tests that the router exposes no apply).

### Phase 2: The action lifecycle + first writes + Email subset (the heart)

- Migration: `agent_actions`.
- Preview/approve/dismiss/undo endpoints; idempotent commit_ids; stale-preview 409s.
- Action types: `compose_email_draft`, `compose_document_request_draft`, `attach_document_to_requirement`, `detach_requirement_document`, `waive_requirement`/`unwaive_requirement`, `reclassify_document`, `adopt_ai_type_for_requirement` (with the mislabeled-row confirmation gate), `change_task_status`, `toggle_task_auto_email`, `create_task`, `preview_date_cascade`, `apply_date_cascade` (R3: the first-slice mismatch scenario needs reclassify/adopt/detach, so they live here, not in Phase 3).
- Action proposal/result cards; CascadeEditor embedded for date actions; Undo chips.
- Email tab E1 subset (Outbox: pending drafts + sent, embedded review drawer).
- ComplianceTab "Use AI type" alignment: the shipped one-click control gains the same single-question mislabeled-row confirm the agent action enforces (R2; deliberate change to a shipped control, endpoint contract unchanged, screenshot included in the phase review).
- Audit rows for every apply/dismiss.

Acceptance: the 11.1, 11.2, 11.3, 11.4 UI tests pass end-to-end; every write shows preview first; email actions provably create drafts only; the mismatch guardrail is enforced in the agent layer (test: adoption without the mislabeled confirmation is rejected with a UI-readable error) and the Compliance tab control asks the same confirmation.

### Phase 3: Scan, Q&A, compare, split; issue lifecycle complete

- `/scan` on one or all documents; persistent issue cards with resolve/dismiss(reason) lifecycle; `run_compliance_scan`, `rename_document`, `split_document` (page-range preview), `summarize`, `compare_documents`.
- New `SourceViewerDrawer` component (R5: the wizard's `WizardPdfDocument` + OCR geometry + `ocrHighlight` locate utilities mounted in a workspace drawer); from this phase, citation chips open it at the cited page; before it, chips show page + snippet and open the Documents tab.

Acceptance: 11.5 UI test passes; dismissals carry reasons and audit rows; split previews page ranges before apply; clicking any citation chip lands on the cited page with the snippet highlighted.

### Phase 4: Email tab E2 + inbound flows + history expansion

- Inbox with match-basis badges, refile action, the existing `TestInboundButton` (visibility gated to non-production tenants on the frontend, R6), Outbox/Inbox toggle + search; unmatched-inbound list endpoint for the needs-filing entry (the known auto-emailing deferral, built honestly here).
- `GET /transactions/{id}/history` expansion (agent/document/requirement/party/ai_email audit rows) so Activity becomes a complete proof surface; ActivityTab note removed.

Acceptance: 11.6 UI test passes; Activity now shows agent and compliance/document events; refile moves a thread between deals visibly.

### Phase 5: Readiness, oversight, and governance (superiority layer)

- `closing_readiness` full version; needs-you strip becomes fully actionable; team-lead view of unresolved agent issues across deals (Intelligence section entry); issue aging metrics.
- Agent preferences (per-user starter chips, pane defaults). "Always approve" rules ONLY if Jake green-lights AW5, with the hard forbidden list and per-rule audit.

Acceptance: 11.7 UI test passes; team lead can see open agent issues per deal; any always-approve rule is visible, revocable, audited, and excluded from forbidden types (tested).

First shippable slice (inside Phase 2): "Resolve a document mismatch from the agent pane" (issue card + the bundled detach-and-draft proposal + Email subset + UAT script 15.2 item 1). It matches the ListedKit hero screenshot, uses only verified infrastructure, and proves the action-card contract before anything else is built.

---

## 14. Database Migrations Inventory (for Jan to apply)

Three new migrations, additive only, RLS-enabled, tenant-scoped (same conventions as `20260819*`):

1. `agent_threads`: id, tenant_id, transaction_id, title, issue_type, severity CHECK (`blocker`,`warning`,`watch`), status CHECK (`open`,`proposed`,`waiting_on_user`,`waiting_on_external`,`resolved`,`dismissed`), summary, source_refs JSONB, created_by, resolved_at, dismissed_at, dismiss_reason, timestamps. Index (tenant_id, transaction_id, status, updated_at DESC).
2. `agent_messages`: id, tenant_id, transaction_id, thread_id FK CASCADE, role CHECK (`user`,`assistant`,`system`), message_kind CHECK (`chat`,`issue`,`action_proposed`,`action_applied`,`action_dismissed`,`action_failed`,`system`), body, source_refs JSONB, metadata_json, created_by, created_at. Index (tenant_id, transaction_id, created_at).
3. `agent_actions`: id, tenant_id, transaction_id, thread_id FK SET NULL, action_type, status CHECK (`proposed`,`previewed`,`approved`,`applying`,`applied`,`dismissed`,`failed`,`undone`,`stale`,`blocked`), title, reason, confidence, source_refs JSONB, input_json, preview_json, apply_json, undo_json, policy_json, proposed_by, approved_by/at, applied_at, dismissed_by/at, dismiss_reason, audit_log_id, commit_id, timestamps. UNIQUE (tenant_id, transaction_id, commit_id); index (tenant_id, transaction_id, status, updated_at DESC).

Optional Phase 5 migration: `agent_approval_rules` (only if AW5 approves). No other schema changes: issues live on threads; canonical rows stay canonical; no PII copies into agent JSON (labels + ids only).

---

## 15. Testing Plan

### 15.1 Automated

Frontend (vitest + msw, extending `TransactionWorkspace.test.tsx` patterns: requery-inside-waitFor, default handlers for every endpoint the page touches):

- Flag off renders the current workspace unchanged (snapshot-level assertion).
- Split shell: pane toggle collapses/restores; preference persists.
- Composer: + picker inserts each ref type; / menu mouse-selection; @ and # filtering; attach routes through the classified-upload dialog and posts a system message; drop on composer vs page drop behave differently.
- Read-only chat: answer renders citation chips; unknown intent renders the honest refusal; conversation survives remount.
- Action cards: proposal renders preview/source/confidence/risk; Approve applies and flashes the owning tab row; Dismiss requires reason where policy says so; stale preview renders "Refresh preview"; Undo reverts and updates the tab.
- Email subset: pending draft renders; review drawer approve/edit-send/discard; nothing renders as "sent" without the approve mutation.
- Mismatch guardrail: the "row mislabeled" confirmation gate.
- Narrow layout: Agent tab pill first, sticky composer, no overlap.

Backend (pytest, extending `test_transaction_plan.py` / `test_ai_email_api.py` fixtures; remember the mock-supabase JSONB and dependency-engine seeding gotchas already documented):

- Access: foreign tenant 404s; tenant-matching but unassigned transaction rejected on every agent route; ref ids from another transaction rejected.
- Compose wrapper transaction check; draft action transaction match; matched_document_id cross-transaction rejection.
- Idempotent action creation (commit_id replay); stale preview 409; approve-after-entity-deleted 409.
- Apply writes audit (agent_action) + the wrapped endpoint's own audit; dismiss stores reason; undo replays inverse changes (cascade) and inverse statuses (waive, skip).
- Policy: forbidden action types cannot be created as applyable; always-approve (if built) ignored for forbidden types; email actions never call a send path; `/documents/request` never reachable from the registry (explicit test).
- Citation gating: an uncited document claim is demoted; located citations pass.
- Mismatch guardrail: `adopt_ai_type_for_requirement` without the mislabeled-row confirmation is rejected and writes nothing to either row.
- Plan aggregate extension: `_HeaderCounts.tasks_completed` / `tasks_total` are returned and consistent with the task list (extends the existing 8 plan tests).
- History expansion: agent/requirement/document/party/ai_email audit rows appear in `/history` (Phase 4).

Visual verification (the established method): render with the dev stack, Chrome-headless screenshots of: empty agent pane, issue stream with blockers, proposal card, applied card with Undo, cascade preview in-conversation, Email tab empty/populated, narrow layout, against the v2 comfort checklist (nothing under 12px, one card vocabulary, champagne only where it matters).

### 15.2 Non-developer UAT scripts (mouse-only; published as `AI_AGENT_WORKSPACE_TESTING_GUIDE.md` when implementation ships, same format as the existing workspace and auto-emailing guides)

Fixture setup: an explicit, internal-only "Set up the UAT deal" action (visible only on non-production tenants behind the flag) that creates real records through the public APIs: one buyer-financed deal, five parties (title company with email; lender WITHOUT email to exercise the party-gap issue), the standard checklist, a purchase agreement upload, a deliberately wrong file ATTACHED to the receipt requirement (so the row reads Uploaded with a mismatch chip, the looks-satisfied danger from 11.1), an addendum with a new closing date, one overdue task, one auto-email-eligible task. No mock data on real surfaces; everything is a real row a tester could have created by hand.

1. Mismatch to draft (the hero script): per 11.1. Pass = the issue card names the looks-satisfied danger; the bundled detach + draft proposal returns the requirement to Missing AND creates the pending draft; NOTHING sent; all proven on screen. (R1: the wrong attachment shows the row as Uploaded-with-mismatch before remediation, never as missing.)
2. Missing document chase: per 11.2.
3. Addendum cascade with undo: per 11.3. Pass = preview always precedes apply; not-moved rows are explained; undo restores.
4. Overdue task rescue: per 11.4.
5. Ask-the-documents: per 11.5, including the "answer not in documents" honesty check.
6. Inbound email round-trip: per 11.6 using the test-inbound button's "document request" scenario.
7. Closing readiness: per 11.7, including the attorney-gate check.
8. Reference fluency: insert all six ref types using only the mouse (+ picker, Ask AI buttons, drag); ask one question per ref.
9. Safety net: try to approve a stale proposal (a second browser tab changes the task first); confirm the UI asks to refresh instead of applying.
10. The off switch: collapse the agent pane; confirm the classic workspace is fully intact; reopen and confirm the conversation is still there.

Every script starts on a visible page, ends with visible proof, and names its proof surface (tab, Email tab, agent thread, audit page). Target: 90 percent of testers complete scripts 1 to 7 unaided.

---

## 16. Decisions Pending Jake

| # | Decision | Context and recommendation |
| --- | --- | --- |
| AW1 | Split-pane layout approval | **RESOLVED 2026-06-13 — Jan directed that the agent-centric workspace BE the transaction detail page, on by default, no opt-in.** `agentWorkspaceEnabled()` now returns true by default; the `ve_agent_workspace_v1='off'` value remains only as a reviewer escape hatch while the feature is uncommitted, and the in-page "Agent pane" collapse toggle stays. Jake's screenshot sign-off is still owed before this is committed/shipped to his testers (the prior AI-rail rejection on this page is the reason the escape hatch is kept), but local/default access no longer requires a script. |
| AW2 | Agent identity | ListedKit named theirs Ava. Options: keep "Velvet Elves AI" (consistent with the floating panel), or a persona name. Recommendation: keep "Velvet Elves AI" with the ✦ kicker; personas invite mascot styling the brand forbids. |
| AW3 | Default pane state | Agent pane open by default for everyone, or opt-in per user after first visit? Recommendation: open by default behind the flag tenant, remembered per user thereafter. |
| AW4 | Issue sensitivity | Which detector thresholds count as "blocker" vs "warning" (e.g. missing doc due in 3 vs 7 days). Recommendation: ship the table in 8.3 with conservative defaults, tune from UAT. |
| AW5 | Always-approve rules (Phase 5) | Off entirely in v1. Recommendation: revisit only after a month of UAT data; never for sends/waives/deletes/date applies regardless. |
| AW6 | Voice input | Browser dictation is uneven and nothing depends on it. Recommendation: skip in v1; revisit with the future SMS/voice milestone. |
| AW7 | Details tab consolidation | Fold DealOverviewCard + People + terms into a ListedKit-style Details tab, or keep the current six tabs + Email. Recommendation: keep current tabs for v1; Details is cosmetic consolidation, not capability. |
| AW8 | Per-transaction "Draft from" account selector | Only matters for multi-account users. Recommendation: display-only in E2; selector when multi-account demand is real. |
| AW9 | Thread retention | Agent conversations are work records; align retention with the communication-log policy (2 years from last login)? Recommendation: yes, same purge job family. |
| AW10 | Header progress indicator copy | "12 of 38 tasks complete" (absolute, recommended) vs ListedKit's bare percentage. |

---

## 17. What Must Not Regress

- The current workspace with the flag off, byte-for-byte, including all 7 `TransactionWorkspace.test.tsx` integration tests and the cascade/compliance/task flows.
- The read-only contract of `POST /dashboard/ai-chat` and the floating panel on every other page.
- The AI Email Review queue at `/ai-emails` (the Email tab embeds it, never replaces it).
- The Timeline command bar, the wizard (all 15 testing-guide sections), the deterministic closing-date answer format, auto-draft eligibility rules, the mismatch verification chips, SyncDeadlines, print checklist, post-closing feedback.
- The 880 backend and 244 frontend green suites; no existing public endpoint changes its contract (handlers may be refactored into shared services, signatures and behavior identical, proven by the existing tests). One scoped exception, called out in Phase 2: the Compliance tab's "Use AI type" control gains a confirmation dialog (R2); its test updates with it, deliberately.

---

## 18. Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Jake rejects the split layout again | High | AW1 screenshot gate in Phase 0; collapse toggle keeps the approved classic layout one click away; flag keeps it off everywhere else |
| LLM proposes a hallucinated action | High | Closed intent schema; server re-validates every ref; only registry actions exist; unknown intent mutates nothing |
| A wrong attachment hides a missing required document | High | The mismatch issue card names the looks-satisfied state; the primary remediation detaches the wrong file (row returns to Missing); type adoption is gated on the mislabeled-row confirmation in both the agent layer and the aligned Compliance tab control |
| An email sends without review | High | Registry can only reach `/ai-emails/compose`; `/documents/request` is untouchable from the agent (tested); send stays in the review surfaces |
| Stale proposal overwrites newer state | Medium | commit_ids, updated_at checks, 409 + "Refresh preview" |
| Context packet bloat (cost/latency) | Medium | Capped windows, summaries, refs-first loading; provider switchable; latency measured per the existing parse-latency harness pattern |
| Conversation UI becomes noisy | Medium | Issue cards collapse when resolved; needs-you strip is the index; one card vocabulary; calm-brand review each phase |
| Activity proof gap confuses testers before Phase 4 | Medium | Every script names its proof surface; result cards always name `visible_success_location` |
| Scope creep into deferred features | Medium | Section 10's deferred/forbidden lists are explicit; non-goals stated in section 6 |
| Test-suite flakiness from the new pane | Medium | Follow the documented gotchas: default msw handlers for every endpoint the page mounts, requery-inside-waitFor, no elements held across awaits |

---

## 19. Definition of Done

1. With the flag on, `/transactions/:id` opens as the split agent workspace; with it off (or collapsed), the current approved workspace renders unchanged.
2. The conversation is durable, transaction-scoped, and survives refresh and device changes.
3. All six reference types insert by mouse (picker, Ask AI button, drag), and the workbench auto-navigates and flashes for every reference.
4. The deterministic detectors surface issues as cards with severity, evidence, and one-click actions; the needs-you strip counts are live.
5. Every write the agent performs went through a typed proposal with preview, evidence, confidence, explicit human approval, audit logging, and undo where the backend supports it; date changes always show the cascade diff first; email actions only ever create pending-review drafts in v1.
6. The Email tab shows this deal's drafts and (E2) inbound mail with match basis, refile, and the UI test-inbound harness.
7. The mismatch, missing-document, addendum-cascade, task-rescue, document-Q&A, inbound-email, and readiness workflows each pass their mouse-only UAT script, executed by a non-developer, with proof entirely on screen.
8. Activity shows agent, compliance, document, party, and email events after the history expansion.
9. All existing tests stay green; new frontend, backend, and screenshot coverage exists per section 15; STYLE_GUIDE v2 holds on every new surface (nothing under 12px, one card vocabulary, champagne discipline).
10. The superiority ledger's parity rows all demonstrably work, and at least the evidence-citation, cascade-preview, undo, governance, and UAT-harness surpass rows are live, so the workspace does not merely imitate ListedKit's agent but is verifiably safer, more transparent, and easier for a real estate professional to trust.
