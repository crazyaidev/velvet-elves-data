# AI Agent-Centric Transaction Workspace Plan

Status: Planning only. This document does not change frontend or backend source code.

Created: 2026-06-12

Workflow/logic review correction: 2026-06-12. This revision corrects the original draft after checking it against the current docs and implemented frontend/backend contracts.

Target surface: `velvet-elves-frontend/src/pages/transactions/TransactionWorkspacePage.tsx` and the supporting transaction, document, task, compliance, email, and AI APIs in `velvet-elves-backend/`.

Primary goal: transform the transaction detail page into a conversation-first AI agent workspace where a real estate professional can resolve transaction issues through a guided conversation, with every change previewed, approved, auditable, undoable where possible, and testable entirely from the frontend UI.

---

## 1. Source Review Completed

This plan is based on a source and documentation pass, not only the ListedKit screenshots.

Project documentation reviewed:

- `velvet-elves-data/requirements.txt`
- `velvet-elves-data/SYSTEM_DESIGN.md`
- `velvet-elves-data/milestones.txt`
- `velvet-elves-data/FRONTEND_UI_WORKFLOW_LOGIC.md`
- `velvet-elves-data/STYLE_GUIDE.md`
- `velvet-elves-data/AI_WIZARD_REDESIGN_SUPERIOR_PLAN_V2.md`
- `velvet-elves-data/AI_WIZARD_LISTEDKIT_PARITY_GAP_CLOSURE_PLAN.md`
- `velvet-elves-data/AI_WIZARD_REDESIGN_SUPERIOR_LISTEDKIT_PLAN.md`
- `velvet-elves-data/AI_WIZARD_TRANSACTION_WORKSPACE_REFINEMENT_PLAN.md`
- `velvet-elves-data/AUTO_EMAILING_FRONTEND_UI_TESTING_GUIDE.md`
- `velvet-elves-data/AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md`
- `velvet-elves-data/REVENUE_GENERATION_SYSTEM_PLAN.md`

Frontend source reviewed:

- `velvet-elves-frontend/src/pages/transactions/TransactionWorkspacePage.tsx`
- `velvet-elves-frontend/src/components/workspace/WorkspaceHeader.tsx`
- `velvet-elves-frontend/src/components/workspace/TimelineTab.tsx`
- `velvet-elves-frontend/src/components/workspace/ComplianceTab.tsx`
- `velvet-elves-frontend/src/components/workspace/DocumentsTab.tsx`
- `velvet-elves-frontend/src/components/workspace/TasksTab.tsx`
- `velvet-elves-frontend/src/components/workspace/PeopleTab.tsx`
- `velvet-elves-frontend/src/components/workspace/ActivityTab.tsx`
- `velvet-elves-frontend/src/components/workspace/AiEvidenceChip.tsx`
- `velvet-elves-frontend/src/components/workspace/CascadeEditor.tsx`
- `velvet-elves-frontend/src/components/documents/AddDocumentModal.tsx`
- `velvet-elves-frontend/src/components/documents/DocVerificationChip.tsx`
- `velvet-elves-frontend/src/components/active-transactions/AIChatPanel.tsx`
- `velvet-elves-frontend/src/contexts/AiChatContext.tsx`
- `velvet-elves-frontend/src/components/active-transactions/ComposeEmailModal.tsx`
- `velvet-elves-frontend/src/pages/AiEmailReviewPage.tsx`
- `velvet-elves-frontend/src/hooks/useTransactionPlan.ts`
- `velvet-elves-frontend/src/hooks/useDocumentRequirements.ts`
- `velvet-elves-frontend/src/hooks/useDocuments.ts`
- `velvet-elves-frontend/src/hooks/useDocVerification.ts`
- `velvet-elves-frontend/src/hooks/useAiEmails.ts`
- `velvet-elves-frontend/src/hooks/usePayments.ts`
- `velvet-elves-frontend/src/tests/integration/TransactionWorkspace.test.tsx`
- `velvet-elves-frontend/src/tests/integration/ComplianceAddDocument.test.tsx`
- `velvet-elves-frontend/src/tests/integration/DocumentsModal.test.tsx`

Backend source reviewed:

- `velvet-elves-backend/app/api/v1/dashboard.py`
- `velvet-elves-backend/app/api/v1/transaction_plan.py`
- `velvet-elves-backend/app/api/v1/transactions.py`
- `velvet-elves-backend/app/api/v1/tasks.py`
- `velvet-elves-backend/app/api/v1/document_requirements.py`
- `velvet-elves-backend/app/api/v1/documents.py`
- `velvet-elves-backend/app/api/v1/ai.py`
- `velvet-elves-backend/app/api/v1/ai_emails.py`
- `velvet-elves-backend/app/api/v1/communication_logs.py`
- `velvet-elves-backend/app/api/v1/transaction_parties.py`
- `velvet-elves-backend/app/services/ai_email_engine.py`
- `velvet-elves-backend/app/services/timeline_planner.py`
- `velvet-elves-backend/app/services/closing_checklist.py`
- `velvet-elves-backend/app/tests/test_transaction_plan.py`
- `velvet-elves-backend/app/tests/test_ai_email_api.py`
- `velvet-elves-backend/app/tests/test_document_requirements.py`
- `velvet-elves-backend/app/tests/test_documents_api.py`
- `velvet-elves-backend/app/tests/test_wizard_command.py`

ListedKit public help center references reviewed:

- Help center root: `https://help.listedkit.com/`
- Working with Ava: `https://help.listedkit.com/en/articles/13657052-working-with-ava`
- How to ask Ava questions about your deals: `https://help.listedkit.com/en/articles/14842078-how-to-ask-ava-questions-about-your-deals`
- Drag Items into Ava Chat for Context: `https://help.listedkit.com/en/articles/15000940-drag-items-into-ava-chat-for-context`
- Using Commands in Ava Chat: `https://help.listedkit.com/en/articles/15361958-using-commands-in-ava-chat`
- Ava Actions: Approving What Ava Proposes: `https://help.listedkit.com/en/articles/14847827-ava-actions-approving-what-ava-proposes`
- Connecting your email and enabling Ava's email inbox: `https://help.listedkit.com/en/articles/14842077-connecting-your-email-and-enabling-ava-s-email-inbox`
- What is Auto Email Drafting: `https://help.listedkit.com/en/articles/13621860-what-is-auto-email-drafting`
- How do I enable Auto Email Drafting on a task: `https://help.listedkit.com/en/articles/13621861-how-do-i-enable-auto-email-drafting-on-a-task`
- Email Rules: Controlling How Ava Writes Emails: `https://help.listedkit.com/en/articles/15000912-email-rules-controlling-how-ava-writes-emails`
- Using Multiple Email Accounts in ListedKit: `https://help.listedkit.com/en/articles/15073138-using-multiple-email-accounts-in-listedkit`
- What is Compliance Scanning: `https://help.listedkit.com/en/articles/13621866-what-is-compliance-scanning`
- How do I run a compliance scan: `https://help.listedkit.com/en/articles/13621867-how-do-i-run-a-compliance-scan`
- Smarter Compliance Scan: Ava Now Reads All Your Documents: `https://help.listedkit.com/en/articles/14847828-smarter-compliance-scan-ava-now-reads-all-your-documents`
- Dismissing Compliance Issues: `https://help.listedkit.com/en/articles/15000936-dismissing-compliance-issues`
- Splitting and Merging Documents with Ava: `https://help.listedkit.com/en/articles/15073123-splitting-merging-documents-with-ava`
- Task Dependencies and Template Import: `https://help.listedkit.com/en/articles/14847829-task-dependencies-and-template-import`
- Conditional Task Templates: Tasks for Specific Scenarios: `https://help.listedkit.com/en/articles/15000933-conditional-task-templates-tasks-for-specific-scenarios`
- What Ava Handles Automatically: `https://help.listedkit.com/en/articles/14426199-what-ava-handles-automatically`

Important note: the ListedKit help center is an Intercom help center with `noindex, nofollow` metadata. The article and collection content was therefore fetched directly from the help center rather than relying on public search snippets.

---

## 2. Workflow And Logic Corrections From Review

The original draft was directionally right, but several workflow details would have caused UI testing failures if implemented literally. This revision makes these corrections explicit:

1. Agent-created missing-document requests must use `/api/v1/ai-emails/compose` so they become `pending_review` AI drafts. The existing `/api/v1/documents/request` endpoint can actually send an email when a provider is connected, so it is allowed only for a separate manual "send/request now" path, not for AI-proposed v1 actions.
2. The plan must not require an Email tab before it exists. Phase 2 now ships a minimal transaction Email panel/tab subset for pending drafts created by agent actions; Phase 4 expands it into the full Outbox/Inbox experience.
3. The Activity tab cannot be the proof surface for every action until `GET /api/v1/transactions/{id}/history` aggregates the new `agent_action` audits plus relevant `document_requirement`, `document`, `transaction_party`, and AI email audit rows. Until that history expansion ships, the canonical proof is the changed tab, the Email/AI Email Review surface, and the agent thread.
4. A document type mismatch must not be resolved by blindly changing the compliance requirement to whatever the AI detected. "Use AI type" is allowed only when the user confirms the checklist row itself was mislabeled. In the ListedKit-style earnest-money scenario, the correct workflow is to preserve/reclassify the uploaded purchase agreement, detach it from the receipt requirement if needed, leave the receipt requirement open, and draft a request for the correct receipt.
5. Split is implemented today via `/api/v1/documents/{document_id}/split`; merge is not. Merge is therefore deferred until a real backend endpoint and frontend flow exist.
6. Agent wrappers must re-check transaction access even when the wrapped endpoint currently checks only tenant access. This matters most for `/api/v1/ai-emails/compose`, draft reads, and communication-log actions.
7. Upload-and-attach compliance workflows remain a two-call flow today: `/documents/upload` followed by `PATCH /transactions/{transaction_id}/document-requirements/{requirement_id}`. The agent plan must either harden `matched_document_id` validation server-side or validate document ownership/transaction scope inside the agent apply handler before calling the existing patch endpoint.
8. Task "add note" is not a first-shippable action unless it maps to an existing communication log, activity note, or task metadata field. It is treated as a deferred action until the canonical note surface is defined.
9. Date changes from uploaded addenda must never write directly from extraction. The AI may extract and cite a proposed date, but the user must confirm it and then see the existing cascade preview before any apply.
10. Always-approve/Autopilot is a later governance feature and does not weaken the v1 rule: every external send, compliance waiver/dismissal, date cascade apply, deletion, and legal/attorney gate remains human-reviewed.

---

## 3. What ListedKit Gets Right

The screenshots and help center establish a clear product model:

1. The transaction page is centered around Ava, not around a static record view.
2. A user can ask plain-English deal questions, and Ava answers from transaction-specific contracts, uploaded documents, and connected deal emails.
3. A user can drag a document, task, or deadline into chat to create an exact reference chip instead of describing the item manually.
4. Ava can propose concrete actions, including task updates, deadline changes, notes, and attention flags.
5. Proposed actions are user-approved. ListedKit also supports "Always approve" rules for action types, editable in Ava preferences.
6. Documents are not just stored; they are scanned for compliance issues and can be split or merged with Ava's help.
7. Email is embedded into transaction work: connected inboxes, auto drafting, templates, signatures, multiple accounts, and rules all feed into the transaction.
8. The right-side workbench in the screenshots keeps structured views close to the conversation: Timeline, Tasks, Details, Compliance, and Email.
9. The UI is mouse-first: status menus, one-click task and compliance updates, attach/upload flows, and draft generation require little typing.

The critical insight is that ListedKit's "AI agent workspace" is not merely a chat widget. It is a transaction operating system where chat is the orchestration layer and the structured tabs are the source-of-truth control panels.

---

## 4. Velvet Elves Foundation Already In Place

Velvet Elves already has many pieces that can surpass ListedKit if they are unified under an agent-centric interaction model.

### 4.1 Existing frontend strengths

The current `TransactionWorkspacePage.tsx` already provides:

- A single deal route at `/transactions/:transactionId`.
- Header identity, status control, AI next-step strip, quick actions, and tab pills.
- Tabs for Timeline, Compliance, Documents, Tasks, People, and Activity.
- Workspace-wide drag-and-drop upload routing to the Documents tab.
- Quick actions for Add Task, Upload Document, Compose, Print, and Ask AI.
- Cascade preview/apply/undo for anchor date changes.
- Deep links such as `?tab=tasks&task=<id>` and `?tab=compliance&requirement=<id>`.

The current workspace components already cover many ListedKit-parity primitives:

- `TimelineTab.tsx` shows live core dates, term rows, deadline tasks, AI evidence chips, and server-resolved date rules.
- `ComplianceTab.tsx` supports missing/uploaded/waived groups, attach document, request by email, waive/un-waive, edit, AI verification mismatch handling, and one-click "Use AI type."
- "Use AI type" must be treated as a powerful correction path: safe when the row was mislabeled, unsafe when a wrong file was attached to a still-required document slot.
- `DocumentsTab.tsx` supports classified upload, drag-drop upload, verification chips, download, and the existing documents manager.
- `TasksTab.tsx` supports grouped tasks, status changes, basis chips, related compliance links, auto-draft toggles, vendor email flow, and rule editing.
- `ComposeEmailModal.tsx` supports deal-scoped mouse-first draft creation to selected parties or all parties.
- `AiEmailReviewPage.tsx` already gives Velvet Elves a strong email review surface with confidence, assumptions, source data, attachment chips, approve, edit/send, discard, and regenerate.

### 4.2 Existing backend strengths

The current backend already provides:

- Deterministic transaction plan aggregate: `GET /api/v1/transactions/{id}/plan`.
- Deterministic cascade dry-run and apply: `POST /api/v1/transactions/{id}/plan/preview` and `/plan/apply`.
- Document requirements CRUD and default checklist creation.
- Document upload, signed download, versioning, OCR geometry, page info, split, email, request-email, draft generation, deletion flag flows, and generated document workflows.
- AI document parse, packet parse, document resolution, public source search, intake classification, AI feedback, wizard command parsing, and checklist parsing.
- On-demand AI email compose, inbound email drafting, settings, templates, test inbound, approval, edit/send, discard, regenerate, and escalation.
- Transaction-scoped communication logs via `/api/v1/communication-logs/transaction/{transaction_id}` and AI email drafts via `/api/v1/ai-emails/drafts?transaction_id=...`.
- External party CRUD through `/api/v1/transactions/{transaction_id}/parties`, used by the People tab and recipient selection.
- Multi-tenant RBAC, Fernet PII encryption, provider-agnostic AI switching, and audit logging.

Important backend constraints the plan must preserve:

- `POST /api/v1/dashboard/ai-chat` is read-only and must stay read-only.
- `/api/v1/documents/request` is not an AI-safe draft endpoint; it records an outbound request and can send through the connected provider. Agent-proposed document requests must use `/api/v1/ai-emails/compose` in v1.
- `GET /api/v1/transactions/{id}/history` currently merges transaction audits, communication logs, and completed task events. It does not automatically include `document_requirement`, `document`, `transaction_party`, or future `agent_action` audit rows unless the history endpoint is expanded.
- `PATCH /api/v1/transactions/{transaction_id}/document-requirements/{requirement_id}` accepts `matched_document_id`; before an agent can use it safely, the agent apply layer or the endpoint itself must validate that the document belongs to the same tenant and transaction.

### 4.3 Existing test coverage to preserve

The existing integration and backend tests protect important end-to-end logic:

- Plan aggregate create-boundary invariant.
- Cascade preview/apply/undo.
- Task basis patching and auto-email toggling.
- Default checklist creation once and idempotent replay.
- Compliance waive/undo and AI evidence chips.
- Classified document add/attach flows with AI verification.
- Unsupported file rejection.
- Request-by-email draft creation that never sends until approved.
- AI email pending review, approval, edit/send, discard, regenerate, source data, attachments, settings, and test inbound.

The new plan must extend this coverage rather than bypass it.

---

## 5. Current Gaps Against ListedKit

The current workspace is strong but still not agent-centric in the ListedKit sense.

1. The AI chat is a floating side panel, not the main transaction workspace.
2. `POST /api/v1/dashboard/ai-chat` is intentionally read-only. Its hard rule says it must never claim to send, schedule, draft, or change anything.
3. Suggested actions are only prompt chips, not typed proposed actions with previews and approvals.
4. Chat does not support structured reference chips for documents, tasks, deadlines, parties, emails, or compliance rows.
5. Dragging a document/task/deadline into chat is not implemented.
6. Compliance scan results do not become persistent agent issue threads with suggested remediations.
7. Email work is split between Compose, AI Email Review, and Activity rather than being a transaction-native Email tab like ListedKit.
8. Conversation history is frontend session state only; it is not a durable transaction work log.
9. The AI cannot yet resolve "any issue arising during the transaction process" because there is no typed action registry, approval lifecycle, or undo-aware agent workflow.
10. The UI still makes users choose which tab to use. The agent should detect the issue and put the right action in front of the user.
11. The safe AI email compose path and the direct document-request send path are currently separate; the agent plan must not confuse them.
12. Activity currently cannot prove every compliance/document/party action because the history endpoint is narrower than the audit log.
13. The system has document split support, but no implemented merge workflow. Merge must not be promised in the first agent release.
14. Compliance mismatch handling can accidentally hide a still-missing requirement if "Use AI type" changes the checklist row without a human confirming the row was mislabeled.

These gaps are fixable because the deterministic backend endpoints already exist for the actions that matter most.

---

## 6. Product Principles For The New Workspace

### 6.1 AI is the front door, deterministic APIs are the hands

The conversation should interpret intent, explain context, and propose actions. The actual writes must route through typed backend endpoints with validation, preview, permissions, audit logs, idempotency, and undo where available.

### 6.2 Mouse-first, minimal typing

The user should usually click:

- A suggested issue.
- A referenced document/task/deadline/party chip.
- Approve, Edit, Dismiss, Upload, Attach, Request, Waive, Apply, Undo.

Typing should be optional and mostly used for a short instruction, email intent, or note.

### 6.3 Every action is visible and reversible where possible

No invisible AI updates. Every proposed action must show:

- What will change.
- Why the AI recommends it.
- The source facts.
- Confidence.
- Whether it can be undone.
- Who approved it.
- What happened after approval.

### 6.4 The frontend is the acceptance surface

Every workflow must be verifiable by a real estate professional from the UI:

- No database inspection.
- No Swagger-only validation.
- No webhook-only validation.
- No hidden admin scripts.
- No "trust that the backend did it."

### 6.5 Legal and compliance boundaries stay explicit

The AI may summarize, compare, flag, draft, prepare, and organize. It may not make legal determinations, approve final attorney releases, decide legal equivalence, or advise on legal strategy.

### 6.6 Velvet Elves should surpass ListedKit

ListedKit's key advantage is agent-centered workflow. Velvet Elves can exceed it by adding:

- Source-cited action previews.
- Cascade diffs before date changes.
- Transaction health and blocker prediction.
- UI-only UAT harnesses.
- Stronger audit and undo.
- Email attachment safety.
- Tenant-level AI governance.
- Compliance issue lifecycle metrics.
- Attorney-safe guardrails.

---

## 7. Target UX: The Agent Workspace

### 7.1 Desktop layout

Replace the current single-column tab-first transaction page with a two-pane agent workspace:

- Left pane: Agent Conversation and Resolution Stream, about 56 to 60 percent width.
- Right pane: Transaction Workbench, about 40 to 44 percent width.
- Header remains full width: breadcrumb, property/deal identity, stage/status, progress, AI next step, and compact quick actions.

Left pane contents:

1. Active issue summary row:
   - "2 blockers"
   - "3 due this week"
   - "1 draft waiting"
   - "4 documents pending"
2. Conversation timeline:
   - AI messages.
   - User messages.
   - Issue cards.
   - Action proposal cards.
   - Approval result cards.
   - Undo result cards.
   - Source/citation chips.
3. Composer:
   - Slash menu.
   - `@` party mentions.
   - `#` document/task/deadline references.
   - Drag-drop reference chips.
   - Voice-to-text button, if supported.
   - Send button.

Right pane contents:

- Timeline
- Tasks
- Details or People
- Compliance
- Documents or Files
- Email
- Activity

The right pane is not secondary. It is the source-of-truth workbench. When the agent proposes an action, the right pane should auto-navigate to the relevant tab and highlight the affected row.

### 7.2 Tablet and mobile layout

Tablet:

- Conversation remains first.
- Workbench collapses to a right drawer or lower split.
- Action cards stay inline in the conversation.

Mobile:

- Header is compact.
- Bottom segmented control: Agent, Timeline, Tasks, Compliance, Email, Files.
- Composer is sticky.
- Approval cards use full-width stacked controls.
- No desktop-only interaction is required; drag/drop must have a tap-based "Add reference" fallback.

### 7.3 Visual style

Follow `STYLE_GUIDE.md` v2:

- Calm, premium, AI-assisted workspace.
- Champagne (`ve-orange`) as the single AI accent.
- Lora serif for section titles.
- No text below 12px.
- Body/input text around 15px with 1.6 line-height.
- Section titles around 20px serif.
- 12px radius cards, 16px modals.
- No decorative clutter, mascots, neon, or oversized empty states.
- AI surfaces use confidence chips, citation chips, pre-confirmed checks, and clear approval cards.

The new workspace should feel more professional than ListedKit's screenshots: denser where real estate experts need scanning, calmer in color, and more explicit about source evidence and next action.

---

## 8. Core Interaction Model

### 8.1 Reference chips

The composer must support typed references:

- Document: `# Earnest Money Deposit Receipt`
- Task: `# Send Executed Contract to All Parties`
- Deadline: `# Inspection Response Deadline`
- Requirement: `# Earnest Money Deposit Receipt`
- Party: `@ Reliable Title Agency`
- Email thread: `@ title company email from Mar 18`

Reference chips can be added by:

- Dragging a row/card into chat.
- Clicking "Ask AI" on a row.
- Typing `#` or `@`.
- Using a plus button in the composer.
- Clicking a suggested chip in an issue card.

Each chip must carry structured identity:

```json
{
  "ref_type": "document",
  "ref_id": "uuid",
  "label": "Earnest Money Deposit Receipt",
  "transaction_id": "uuid",
  "source": "user_drag"
}
```

The chip label is user-facing. The ID and type drive backend context loading.

### 8.2 Agent messages

Messages should be durable, transaction-scoped, and distinguish:

- User text.
- AI answer.
- AI issue detection.
- AI proposed action.
- User approval/dismissal/edit.
- System result.
- Undo result.

Messages should remain visible after refresh and across devices.

### 8.3 Issue cards

Every detected problem becomes an issue card, not just text in chat.

Issue types:

- Missing document.
- Document type mismatch.
- Compliance issue.
- Low-confidence extraction.
- Date conflict.
- Deadline change needed.
- Task blocked.
- Email needs response.
- Incoming email not filed to a deal.
- Party/contact missing email.
- Signature incomplete.
- Closing readiness blocker.
- Attorney review needed.

Issue card fields:

- Title.
- Severity: blocker, warning, watch.
- Status: open, proposed, waiting, resolved, dismissed.
- Source references.
- Impact.
- Recommended next action.
- One-click actions.

### 8.4 Proposed action cards

The agent must never directly write from a free-form response. It creates proposed action cards.

Action card anatomy:

- Action title.
- Plain-English summary.
- Before and after preview.
- Source chips.
- Confidence chip.
- Risk label.
- Buttons: Approve, Edit, Dismiss.
- Optional: Always approve this type.
- Optional: Undo after applied.

Example:

```text
Action: Draft request for correct earnest money receipt
To: Reliable Title Agency
Reason: Uploaded file under Earnest Money Deposit Receipt appears to be a purchase agreement.
Source: test.pdf, page 1, "Real Estate Purchase Agreement"
Will create: one pending review email draft. Nothing sends yet.
Buttons: Review Draft | Edit Instruction | Dismiss
```

### 8.5 Approval policy

Default policy:

- All transaction writes require explicit approval.
- Email compose creates pending-review drafts, not sends.
- Date changes require cascade preview before approval.
- Compliance dismissals require reason or quick reason.
- Deletes remain soft-delete or flag-for-deletion flows.
- Attorney-legal boundaries cannot be auto-approved.

Optional "Always approve" should ship later and be narrower than ListedKit:

- Off by default.
- Tenant-controlled.
- Per action type and recipient class.
- Never for legal, compliance dismissal, final release, or external send without a review-safe path.
- Must show an undo window or audit reason where possible.

---

## 9. Backend Architecture Plan

### 9.1 New service layer

Add a dedicated transaction agent service layer rather than expanding `dashboard.py` chat into a write engine.

Proposed modules:

- `app/services/agent_workspace_context.py`
- `app/services/agent_intent_service.py`
- `app/services/agent_action_registry.py`
- `app/services/agent_action_preview.py`
- `app/services/agent_action_apply.py`
- `app/services/agent_thread_service.py`
- `app/services/agent_policy.py`

Responsibilities:

- Context service loads only authorized transaction data.
- Intent service maps user request plus refs to typed intents.
- Action registry maps typed intents to deterministic preview/apply handlers.
- Policy service determines whether an action requires approval, can be auto-approved, can be undone, or is forbidden.
- Thread service persists conversation, issue cards, and action lifecycle.

### 9.2 New backend endpoints

Add a transaction-scoped agent router:

```text
GET  /api/v1/transactions/{id}/agent-workspace
GET  /api/v1/transactions/{id}/agent/threads
POST /api/v1/transactions/{id}/agent/chat
POST /api/v1/transactions/{id}/agent/actions
POST /api/v1/transactions/{id}/agent/actions/{action_id}/preview
POST /api/v1/transactions/{id}/agent/actions/{action_id}/approve
POST /api/v1/transactions/{id}/agent/actions/{action_id}/dismiss
POST /api/v1/transactions/{id}/agent/actions/{action_id}/undo
GET  /api/v1/transactions/{id}/agent/context-search
PUT  /api/v1/agent/preferences
```

Why not reuse `/dashboard/ai-chat` directly:

- The current chat endpoint is read-only by design.
- It is stateless and stores no durable transaction conversation.
- It returns prompt chips, not typed actions.
- Expanding it would blur the strong current safety boundary.

Keep `/dashboard/ai-chat` for global portfolio Q&A. Build transaction resolution through `/transactions/{id}/agent/*`.

Endpoint design rule: agent endpoints are orchestration wrappers, not duplicate business logic. They must call the same canonical handlers used by the existing workspace where those handlers are safe, and must add missing safety checks before wrapping handlers that are currently broader than the transaction workspace needs.

Required wrapper safeguards:

- Always call `require_transaction_access` for the transaction before loading context, proposing actions, previewing, applying, undoing, or reading transaction-scoped drafts.
- For `/ai-emails/compose`, validate the user can access the referenced transaction before calling the compose engine.
- For document-requirement matching, validate the document exists, is in the same tenant, and is attached to the same transaction before setting `matched_document_id`.
- For communication logs and AI drafts, validate the log belongs to the same tenant and, when a transaction id is present, to the same transaction.
- Return a `visible_success_location` for every apply result so frontend testers know where to confirm the result: Agent thread, Workbench tab, Email tab, Activity, AI Email Review, or Admin Audit.

### 9.3 Minimal data model

Reuse existing tables wherever possible. Add only durable primitives needed for agent-centered workflows.

Proposed table: `agent_threads`

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
tenant_id UUID NOT NULL,
transaction_id UUID NOT NULL,
title TEXT NOT NULL,
issue_type TEXT,
severity TEXT NOT NULL DEFAULT 'watch',
status TEXT NOT NULL DEFAULT 'open',
summary TEXT,
source_refs JSONB DEFAULT '[]'::jsonb,
created_by UUID,
assigned_to UUID,
resolved_at TIMESTAMPTZ,
dismissed_at TIMESTAMPTZ,
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

Recommended constraints/indexes:

- Foreign key to `transactions(id)` where migrations can enforce it safely.
- `CHECK (severity IN ('blocker','urgent','watch','info'))`.
- `CHECK (status IN ('open','waiting_on_user','waiting_on_external','resolved','dismissed'))`.
- Index on `(tenant_id, transaction_id, status, updated_at DESC)`.

Proposed table: `agent_messages`

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
tenant_id UUID NOT NULL,
transaction_id UUID NOT NULL,
thread_id UUID REFERENCES agent_threads(id) ON DELETE CASCADE,
role TEXT NOT NULL,
message_kind TEXT NOT NULL,
body TEXT,
source_refs JSONB DEFAULT '[]'::jsonb,
metadata_json JSONB DEFAULT '{}'::jsonb,
created_by UUID,
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

Recommended constraints/indexes:

- `CHECK (role IN ('user','assistant','system','tool'))`.
- `CHECK (message_kind IN ('chat','issue','action_proposed','action_applied','action_dismissed','action_failed','audit'))`.
- Index on `(tenant_id, transaction_id, thread_id, created_at)`.

Proposed table: `agent_actions`

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
tenant_id UUID NOT NULL,
transaction_id UUID NOT NULL,
thread_id UUID REFERENCES agent_threads(id) ON DELETE SET NULL,
action_type TEXT NOT NULL,
status TEXT NOT NULL DEFAULT 'proposed',
title TEXT NOT NULL,
reason TEXT,
confidence NUMERIC,
source_refs JSONB DEFAULT '[]'::jsonb,
input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
preview_json JSONB DEFAULT '{}'::jsonb,
apply_json JSONB DEFAULT '{}'::jsonb,
undo_json JSONB DEFAULT '{}'::jsonb,
policy_json JSONB DEFAULT '{}'::jsonb,
proposed_by TEXT NOT NULL DEFAULT 'ai',
approved_by UUID,
approved_at TIMESTAMPTZ,
applied_at TIMESTAMPTZ,
dismissed_by UUID,
dismissed_at TIMESTAMPTZ,
audit_log_id UUID,
commit_id TEXT NOT NULL,
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

Recommended constraints/indexes:

- `CHECK (status IN ('proposed','previewed','approved','applying','applied','dismissed','failed','undone','stale','blocked'))`.
- Unique index on `(tenant_id, transaction_id, commit_id)` for idempotency.
- Index on `(tenant_id, transaction_id, status, updated_at DESC)`.

Proposed table or tenant settings extension: `agent_approval_rules`

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
tenant_id UUID NOT NULL,
user_id UUID,
action_type TEXT NOT NULL,
enabled BOOLEAN NOT NULL DEFAULT false,
constraints_json JSONB DEFAULT '{}'::jsonb,
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

Do not add a separate table for every issue category in v1. Store issue-specific source refs and metadata on `agent_threads` and let canonical task/document/requirement/email rows remain canonical.

RLS and PII rule: every new table must include tenant-scoped RLS, and JSON metadata must store source refs and stable labels rather than raw decrypted PII where possible. Full emails, phone numbers, and addresses should be read from canonical encrypted tables at render/context time, not copied into agent metadata unless an existing audit policy already allows that field.

### 9.4 Context packet design

Agent context should be assembled as structured JSON plus a compact LLM-readable summary.

Sources to include:

- `GET /transactions/{id}/plan` equivalent data.
- Tasks from `TaskRepository.list_by_transaction`.
- Requirements from `DocumentRequirementRepository.list_by_transaction`.
- Documents from `DocumentRepository.list_by_transaction`.
- Parties from `TransactionPartyRepository.list_by_transaction`.
- Communication logs from `CommunicationLogRepository`.
- Recent audit logs from `AuditLogRepository`, including transaction-linked agent/document/requirement rows once history aggregation is expanded.
- AI email drafts from `/api/v1/ai-emails/drafts?transaction_id=...` and inbound/outbound communication rows from `/api/v1/communication-logs/transaction/{transaction_id}`.
- Calendar sync state where available.

Each fact sent to the LLM should retain provenance:

```json
{
  "fact": "Earnest Money Deposit Receipt is uploaded but AI detected purchase_agreement",
  "source_refs": [
    {
      "ref_type": "document",
      "ref_id": "uuid",
      "label": "test.pdf",
      "page": 1,
      "snippet": "Real Estate Purchase Agreement"
    },
    {
      "ref_type": "requirement",
      "ref_id": "uuid",
      "label": "Earnest Money Deposit Receipt"
    }
  ]
}
```

### 9.5 Typed action registry

Start with action types backed by existing deterministic endpoints.

Task actions:

- `create_task`
- `update_task`
- `change_task_status`
- `toggle_task_auto_email`
- `skip_task`
- `restore_task`
- `append_task_note` is deferred until the canonical note/comment surface is selected.

Compliance actions:

- `attach_document_to_requirement`
- `waive_requirement`
- `unwaive_requirement`
- `update_requirement_rule`
- `adopt_ai_document_type`
- `detach_requirement_document`

Document actions:

- `run_document_parse`
- `run_compliance_scan`
- `reclassify_document`
- `rename_document`
- `split_document`
- `merge_documents` is deferred; no backend merge endpoint exists today.
- `upload_new_version`
- `generate_document_from_template`

Date and timeline actions:

- `preview_date_cascade`
- `apply_date_cascade`
- `update_term_rule`
- `create_deadline_task`
- `sync_deadline_to_calendar`

Email actions:

- `compose_email_draft`
- `compose_document_request_draft`
- `regenerate_email_draft`
- `discard_email_draft`
- `open_email_review`
- `file_inbound_email_to_transaction`

People/contact actions:

- `add_party`
- `update_party_email`
- `invite_vendor_colleague`
- `assign_transaction_member`

Read-only actions:

- `summarize_transaction`
- `compare_documents`
- `answer_from_sources`
- `closing_readiness_check`

Forbidden or attorney-only actions:

- Legal determination.
- Final legal packet release.
- Same-day disbursement exception approval.
- Compliance issue dismissal without human reason.
- External email auto-send unless tenant policy explicitly allows it and the action is low-risk.

V1 canonical handler map:

| Agent action | Existing handler to wrap | Critical correction |
| --- | --- | --- |
| `compose_email_draft` | `POST /api/v1/ai-emails/compose` | Creates `pending_review`; never sends. Agent wrapper must validate transaction access first. |
| `compose_document_request_draft` | `POST /api/v1/ai-emails/compose` | Do not call `/documents/request` for AI proposals because it can send immediately. |
| `open_email_review` | `GET /api/v1/ai-emails/{log_id}` or route to `/ai-emails/{log_id}` | Verify draft belongs to tenant and transaction before showing in workspace. |
| `regenerate_email_draft` | `POST /api/v1/ai-emails/{log_id}/regenerate` | Allowed only for actionable pending drafts. |
| `discard_email_draft` | `POST /api/v1/ai-emails/{log_id}/discard` | Require visible reason for compliance-sensitive drafts. |
| `file_inbound_email_to_transaction` | `POST /api/v1/ai-emails/inbound/{log_id}/refile` | Validate inbound belongs to tenant; re-draft is best-effort. |
| `attach_document_to_requirement` | `PATCH /api/v1/transactions/{transaction_id}/document-requirements/{requirement_id}` | Validate document transaction/tenant before setting `matched_document_id`. |
| `detach_requirement_document` | same patch endpoint with `unmatch` | Leaves requirement missing unless separately waived. |
| `waive_requirement` / `unwaive_requirement` | same patch endpoint with `status` | Waive requires a reason; no auto-approval. |
| `adopt_ai_document_type` | `PATCH /api/v1/documents/{document_id}` plus optional requirement patch | Only allowed when user confirms the checklist row was mislabeled; never masks a truly missing required document. |
| `change_task_status` | `PUT /api/v1/tasks/{task_id}/status` | Use `Skipped` for reversible remove-from-plan behavior. |
| `toggle_task_auto_email` / `update_task` | `PATCH /api/v1/tasks/{task_id}` | Preserve metadata merge semantics for `auto_draft_email` and `basis`. |
| `create_task` / `create_deadline_task` | `POST /api/v1/tasks` | Deadline tasks must carry planner basis; client does not compute due dates. |
| `preview_date_cascade` | `POST /api/v1/transactions/{transaction_id}/plan/preview` | Required before any date apply. |
| `apply_date_cascade` | `POST /api/v1/transactions/{transaction_id}/plan/apply` | Use existing `commit_id` and `inverse_changes` for undo. |
| `split_document` | `GET /documents/{id}/pages` then `POST /documents/{id}/split` | PDF-only; preview page ranges before apply. |
| `add_party` / `update_party_email` | `/api/v1/transactions/{transaction_id}/parties` | Use People tab vocabulary and audit without copying raw PII into agent JSON. |

### 9.6 Preview and apply contract

Every write action should support a consistent preview response:

```json
{
  "action_id": "uuid",
  "action_type": "apply_date_cascade",
  "title": "Move Closing Date",
  "summary": "Closing Date changes from 2026-05-20 to 2026-05-27.",
  "before": {},
  "after": {},
  "diff_items": [],
  "source_refs": [],
  "confidence": 0.93,
  "requires_approval": true,
  "undo_available": true,
  "risk": "medium",
  "blocked_reason": null,
  "handler_endpoint": "/api/v1/transactions/uuid/plan/apply",
  "visible_success_location": "Timeline tab"
}
```

Apply response:

```json
{
  "action_id": "uuid",
  "status": "applied",
  "result_summary": "Moved 1 deadline and 4 task dates.",
  "affected_refs": [],
  "undo_available": true,
  "audit_log_id": "uuid",
  "visible_success_location": "Timeline tab"
}
```

This allows the frontend to render one action-card component for many action types.

Not every action has a meaningful dry-run today. For actions without an existing preview endpoint, the agent preview must render the exact validated payload that will be sent to the canonical endpoint, the expected visible result, and any non-undoable risk. It must not simulate hidden writes.

### 9.7 Idempotency and race protection

Every proposed action must carry a `commit_id`.

Approval must re-check:

- User still has transaction access.
- Tenant is still active.
- Referenced task/document/requirement still exists.
- The preview is not stale, or the frontend must show "Refresh preview."
- The row version/updated_at matches where relevant.
- For email and communication actions, the draft/log still belongs to the current tenant and transaction.
- For compliance matching, the requirement and document still belong to the same transaction.

If stale:

- Do not apply.
- Return a UI-readable conflict.
- Offer "Refresh proposal."

### 9.8 Audit logging

Every action writes to `audit_logs` and, where communication-related, `communication_logs`.

Activity visibility correction:

- Expand `GET /api/v1/transactions/{id}/history` to include future `agent_action` audit rows and transaction-linked `document_requirement`, `document`, `transaction_party`, and AI email audit rows where they are part of the transaction work log.
- Until that expansion ships, UAT scripts must verify actions through the Agent thread and canonical workbench tab instead of assuming Activity sees everything.

Audit summary examples:

- "Agent approved AI action: compose document request draft for Earnest Money Deposit Receipt."
- "Agent approved AI action: waived requirement Home Warranty, reason: not applicable per contract."
- "Agent applied AI date cascade: Closing Date 2026-05-20 to 2026-05-27; 4 tasks moved."

The agent conversation must link to the audit entry.

---

## 10. Frontend Architecture Plan

### 10.1 Page composition

Refactor transaction workspace into:

```text
TransactionWorkspacePage
  WorkspaceHeader
  AgentWorkspaceShell
    AgentConversationPane
      AgentIssueSummary
      AgentMessageList
      AgentComposer
    WorkbenchPane
      TimelineTab
      ComplianceTab
      DocumentsTab
      TasksTab
      PeopleTab
      ActivityTab
      EmailTab
```

The existing tab components should remain source-of-truth surfaces. The new agent pane orchestrates them.

Migration rule: the current shipped workspace has Timeline, Compliance, Documents, Tasks, People, and Activity. Do not block the agent shell on a full ListedKit-style Email or Details tab. Phase 2 may add a minimal transaction Email panel/tab for pending AI drafts created by agent actions; Phase 4 expands it into the full Outbox/Inbox Email tab. A Details tab is a later consolidation of `DealOverviewCard` and `PeopleTab`, not a first-slice dependency.

### 10.2 New frontend components

Add:

- `components/agent/AgentWorkspaceShell.tsx`
- `components/agent/AgentConversationPane.tsx`
- `components/agent/AgentComposer.tsx`
- `components/agent/AgentReferenceChip.tsx`
- `components/agent/AgentReferencePicker.tsx`
- `components/agent/AgentIssueCard.tsx`
- `components/agent/AgentActionCard.tsx`
- `components/agent/AgentActionPreview.tsx`
- `components/agent/AgentSourceDrawer.tsx`
- `components/agent/AgentApprovalMenu.tsx`
- `components/agent/AgentThreadList.tsx`
- `components/workspace/EmailTab.tsx`

Add hooks:

- `hooks/useAgentWorkspace.ts`
- `hooks/useAgentThreads.ts`
- `hooks/useAgentChat.ts`
- `hooks/useAgentActions.ts`
- `hooks/useAgentContextSearch.ts`

### 10.3 Reuse existing components

Do not rebuild proven surfaces:

- Reuse `CascadeEditor` for date changes.
- Reuse `AiEvidenceChip` for source/citation chips where possible, then extend it for agent refs.
- Reuse `RuleEditor` for date/basis edits.
- Reuse `AddDocumentModal` for uploads.
- Reuse `DocumentsModal` until a native Files tab reaches parity.
- Reuse `ComposeEmailModal` logic, but allow the agent to create compose proposals directly.
- Reuse `AiEmailReviewPage` review cards in an Email tab or embedded review drawer.
- Reuse `DocVerificationChip` for compliance/document mismatch states.

### 10.4 Agent composer details

Required controls:

- Text area with 15px text.
- Plus button for reference picker.
- Slash command menu.
- Voice input button if browser permission is available; otherwise hide or disable with tooltip.
- Send button.
- Drag-over state: "Drop to ask about this item."

Slash commands:

- `/draft email`
- `/request document`
- `/run compliance scan`
- `/summarize`
- `/compare documents`
- `/add task`
- `/move deadline`
- `/closing readiness`
- `/help`

The slash menu must be mouse-selectable. Typing the slash command is optional.

### 10.5 Drag-to-chat behavior

Every row in the right workbench should expose a draggable reference:

- Document row.
- Compliance requirement row.
- Task row.
- Timeline row.
- Email thread row.
- Party row.

On drag start:

- Store `application/x-ve-agent-ref` with structured JSON.
- Also store plain text for accessibility/fallback.

On drop into composer:

- Add a reference chip.
- Do not upload or mutate anything.
- Focus composer.

Tap fallback:

- Each row has an "Ask AI" icon button or row menu option.
- Clicking it adds the chip and opens the Agent pane.

### 10.6 Workbench auto-navigation

When an action card references a source:

- Clicking a document source opens the Documents tab or source drawer.
- Clicking a requirement opens Compliance and flashes the row.
- Clicking a task opens Tasks and flashes the row.
- Clicking a deadline opens Timeline and flashes the row.
- Clicking an email opens Email and flashes the thread.

This keeps the conversation and structured record synchronized.

### 10.7 Email tab

ListedKit screenshots show transaction-native Outbox and Inbox. Add an Email tab to the workbench.

Phase 2 minimal Email subset:

- Show pending AI drafts for this transaction from `GET /api/v1/ai-emails/drafts?transaction_id=...`.
- Open the existing AI Email Review page or an embedded drawer for the selected draft.
- Show draft status, recipients, subject, confidence, source data, and "nothing has sent yet."
- Provide "Open in AI Email Review" even before the embedded drawer is complete.

Phase 4 full Email tab:

Email tab sections:

- Outbox drafts.
- Inbox.
- Needs filing.
- Sent.
- Scheduled.
- Settings mini-panel: draft-from account, signature, auto-draft status.

Minimum v1:

- Show pending AI drafts for this transaction.
- Open embedded review drawer or navigate to `/ai-emails/:id`.
- Compose from this deal.
- Send a UI test inbound email to this deal in non-production/test mode, reusing `useTestInbound`.
- Show empty states that match style guide: concise and action-oriented.

Manual direct-send correction:

- `/api/v1/documents/request` can remain available to a clearly labeled manual "Send request now" flow where the user sees that the message may send immediately.
- Agent-created document requests in v1 must not call that endpoint. They create pending AI drafts through `/api/v1/ai-emails/compose`.

### 10.8 Details tab

ListedKit has Details in the right rail. Velvet Elves currently has People and DealOverviewCard. Create a Details tab or combine People + transaction facts:

- Address.
- Property facts.
- Financing.
- Important dates.
- Parties.
- Contact completeness.
- AI summary PDF generation.

Keep editable fields consistent with existing wizard editors and cascade rules.

---

## 11. Workflow Designs

### 11.1 Compliance document type mismatch

Goal: match the ListedKit screenshot scenario and go further.

Trigger:

- User uploads `test.pdf` under "Earnest Money Deposit Receipt."
- AI verification detects it as a Purchase Agreement.

Conversation result:

- Issue card: "Document Type Mismatch."
- Source chip: `test.pdf`, page/snippet if available.
- Impact: "The required earnest money receipt is still missing."
- Suggested actions:
  - Detach wrong document from this requirement and draft request to title company.
  - Upload correct receipt.
  - Reclassify current document as Purchase Agreement without satisfying the receipt requirement.
  - Keep my classification only with a visible reason.
  - Waive requirement, with reason.

Guardrail:

- Do not let "Use AI type" silently turn the Earnest Money Deposit Receipt requirement into a Purchase Agreement requirement. That hides the real missing receipt. `adopt_ai_document_type` can update the requirement only when the user explicitly confirms the checklist row was mislabeled, not merely because the attached file was wrong.

Preferred action:

- Detach the wrong document from the receipt requirement if it is currently matched.
- Preserve or reclassify the uploaded file as Purchase Agreement in the Documents tab.
- Draft request to Reliable Title Agency if that party exists.
- If no title party email exists, propose "Add email for title company" first.

Approval flow:

1. User clicks "Draft request."
2. Agent shows proposed email with recipient, subject, body, requirement source facts, confidence, and "creates draft only."
3. User clicks "Create Draft."
4. Agent calls `/api/v1/ai-emails/compose`, not `/api/v1/documents/request`.
5. Draft appears in the Phase 2 Email subset and AI Email Review.
6. Conversation card updates to "Draft waiting for review."
7. Receipt requirement remains missing until the correct receipt is uploaded or attached.

Frontend test:

- Upload wrong PDF through Compliance.
- See mismatch chip.
- Click "Ask AI to fix."
- Click "Draft request."
- Verify no email sends.
- Open Email tab and see pending draft.
- Approve/edit from UI.
- Confirm the receipt requirement is still open/missing after draft creation.

### 11.2 Missing document request

Trigger:

- Compliance row is missing and due soon or overdue.

Agent proposal:

- "Request Home Inspection Report from inspector/title/client."

Flow:

1. Agent asks user to choose recipient from known parties if ambiguous.
2. User clicks recipient.
3. Agent creates pending email draft through `/api/v1/ai-emails/compose`.
4. Draft appears in Email tab and review queue.
5. Requirement remains missing until document is uploaded or attached.

Do not use `/api/v1/documents/request` for this agent action in v1 because that endpoint can send through a connected provider. It is reserved for a clearly labeled manual request flow.

Superiority over ListedKit:

- Draft shows exactly what source facts were used.
- If the draft says an attachment is included, the attachment chip must prove it.
- The request is tied to the requirement row and issue thread.

### 11.3 Deadline changed by addendum

Trigger:

- User uploads addendum or asks "The closing moved to May 27. Update everything."

Agent action:

- Parse the referenced document and propose source-cited facts if needed.
- Create `preview_date_cascade` action.
- Use existing `/plan/preview`.

Flow:

1. User drops addendum into chat or references it.
2. Agent extracts the new closing date with source evidence.
3. User confirms the extracted date or edits it.
4. Agent shows cascade preview: deadline moves, task moves, pinned tasks not moved, weekend roll rules.
5. User clicks Apply.
6. Existing `/plan/apply` writes changes.
7. Undo chip appears.

Guardrail:

- Uploading or parsing an addendum must never directly update transaction dates. The first write is always `/plan/apply` after a fresh preview.

Frontend test:

- Ask agent to move Closing Date.
- Verify preview modal/card lists moved and not-moved rows.
- Apply.
- Undo.
- Verify Timeline and Tasks update through UI.

### 11.4 Task issue resolution

Trigger:

- Task is overdue or blocked.

Agent options:

- Mark completed.
- Update due date.
- Draft email related to task.
- Add note only after the canonical note/activity surface is defined; do not create an ad hoc note store.
- Create follow-up task.
- Toggle auto-draft.

Flow:

1. User drags task into chat.
2. Agent summarizes task context and asks what outcome is needed.
3. User clicks suggested action.
4. Agent previews update.
5. User approves.

Frontend test:

- Drag overdue task into composer.
- Click "Draft related email."
- Verify pending draft appears.
- Toggle auto-draft from action card and verify Tasks tab checkbox changes.

### 11.5 Document Q&A and comparison

Trigger:

- User drags one or more documents into chat.

Agent can:

- Summarize document.
- Extract important dates and amounts.
- Compare two documents for inconsistent price/date/parties.
- Run compliance scan.
- Split a PDF if supported.
- Merge documents only after a dedicated backend endpoint and preview UI are implemented.

Action distinction:

- Summarize/compare are read-only.
- Scan creates issue cards.
- Split requires page-range preview and approval.
- Merge is out of scope for v1.

Frontend test:

- Drag inspection report into chat.
- Ask "What are major findings?"
- Drag purchase agreement and counteroffer.
- Ask "Are dates consistent?"
- Verify answer contains source chips and clear "I do not know" if a fact is missing.

### 11.6 Incoming email response

Trigger:

- A connected inbox receives a transaction-related message.

Agent result:

- Email thread appears in Email tab.
- Agent creates issue card if reply is needed.
- If safe, agent creates pending draft.

Flow:

1. User clicks "Send test inbound to this deal" in test mode or receives real inbound.
2. Email appears in Email tab.
3. Agent issue card says "Buyer asked for inspection report."
4. Draft proposal appears.
5. User opens the existing AI Email Review surface or embedded review drawer.
6. User reviews, edits, and sends.

Frontend test:

- Use Email tab test inbound button.
- Verify incoming email appears.
- Verify draft appears with source data and attachment chip when relevant.
- Approve and confirm sent/approved status in Email tab or AI Email Review, and confirm the communication appears in Activity once history aggregation includes the row.

### 11.7 Closing readiness check

Trigger:

- User asks "Are we ready to close?"
- Closing is within a configurable window.

Agent checks:

- Open tasks.
- Overdue tasks.
- Missing documents.
- Unsigned/in-flight documents.
- Pending AI email drafts.
- Unresolved compliance issues.
- Key date conflicts.
- Missing party contact info.
- Attorney-only blockers when applicable.

Output:

- Deterministic readiness score with AI explanation, not a legal opinion.
- Blockers.
- Warnings.
- One-click action list.

Superiority over ListedKit:

- Uses deterministic plan and compliance data.
- Converts each blocker into a typed issue/action.
- Gives a frontend-verifiable path to resolve every item.

---

## 12. Implementation Phases

### Phase 0: Feature flag and audit inventory

Goal: prepare safely without disrupting the current workspace.

Deliverables:

- Tenant/user feature flag: `agent_workspace_v1`.
- Route keeps `/transactions/:transactionId`.
- Ability to toggle between Current Workspace and Agent Workspace for internal test tenants.
- Inventory of all write endpoints and whether each supports preview, idempotency, and undo.
- Explicit inventory of endpoints that can send externally, especially `/api/v1/documents/request`, so they are not wrapped as AI draft actions by mistake.
- Hardening decision for document-requirement matching: either update the existing endpoint to validate `matched_document_id` or enforce that validation inside `agent_action_apply`.
- Action registry skeleton with no writes enabled yet.

Acceptance:

- Existing transaction workspace tests still pass.
- Agent workspace flag off means zero UI change.
- Audit inventory document lists action type, preview endpoint, apply endpoint, undo capability, permissions, and test coverage.

### Phase 1: Agent shell, durable read-only conversation, and references

Goal: make the page conversation-centered without enabling writes.

Deliverables:

- Two-pane Agent Workspace layout.
- Durable `agent_threads` and `agent_messages`.
- Transaction-scoped `POST /transactions/{id}/agent/chat`.
- Read-only answers grounded in transaction context.
- Reference chips for documents, tasks, requirements, deadlines, parties, and emails.
- Drag-to-chat plus tap fallback.
- Source drawer and workbench row flashing.
- UI-only test scripts for reference chips.

Acceptance:

- User can open a deal and see Agent pane first.
- User can drag a document, task, and deadline into chat.
- Agent answers from referenced context.
- Agent refuses unsupported or missing-source questions clearly.
- Refresh keeps the conversation.
- No write action can occur in Phase 1.

### Phase 2: Proposed actions for existing deterministic task, compliance, date, and email flows

Goal: convert common issues into approval cards using existing endpoints.

Deliverables:

- `agent_actions` table.
- Action card component.
- Minimal transaction Email subset showing pending AI drafts created by agent actions.
- Action registry for:
  - `compose_email_draft`
  - `compose_document_request_draft`
  - `waive_requirement`
  - `attach_document_to_requirement`
  - `change_task_status`
  - `toggle_task_auto_email`
  - `create_task`
  - `preview_date_cascade`
  - `apply_date_cascade`
- Preview/apply/dismiss/undo endpoints.
- Audit log integration.
- UI highlight of affected rows after apply.
- History aggregation design for future Activity visibility; canonical tab proof is acceptable until the endpoint is expanded.

Acceptance:

- Every proposed write shows an approval card.
- Date changes always show cascade preview first.
- Email actions create drafts, not sends.
- Agent document requests use `/api/v1/ai-emails/compose`, not `/api/v1/documents/request`.
- Compliance changes update the Compliance tab after approval.
- Task changes update the Tasks tab after approval.
- Pending agent-created drafts are visible from the transaction without leaving the workspace, even if the full Email tab is not complete.
- Dismissed actions remain visible in the thread.
- Undo appears for supported actions.

### Phase 3: Compliance scan and document remediation agent

Goal: meet and exceed ListedKit compliance scanning.

Deliverables:

- Agent "Run compliance scan" command for a selected document or all transaction documents.
- Persistent compliance issue cards.
- Source-cited document type mismatch flow.
- "Use AI type," "Keep my type," "Detach," "Request correct doc," and "Upload replacement" actions from the issue card.
- Document compare flow for price/date/party conflicts.
- Source viewer jump using existing OCR geometry where available.
- Split action proposals backed by existing document page endpoints.
- Merge remains deferred until a backend merge endpoint and frontend preview exist.

Acceptance:

- User can upload a wrong document and resolve the mismatch entirely from the Agent pane.
- User can run scan on all docs and see issue cards.
- User can dismiss an issue with visible reason and audit record.
- User can request the correct document as a pending draft.
- User can jump from issue source chip to document/page evidence.

### Phase 4: Transaction-native Email tab and inbox resolution

Goal: make email part of the transaction workspace, not a separate destination.

Deliverables:

- Workbench Email tab.
- Outbox drafts list for this transaction.
- Inbox threads for this transaction.
- Needs filing queue for ambiguous inbound mail.
- Draft-from account selector.
- Compose from agent action card or Email tab.
- Embedded AI email review drawer.
- Test inbound button for UI-only UAT in non-production/test tenants.

Acceptance:

- User can create a draft from Agent pane and review it in Email tab.
- User can approve/edit/send from the frontend.
- User can generate a test inbound email through UI and see draft generation.
- User can refile a misfiled email to the correct transaction and see the thread move.

### Phase 5: Rules, always-approve, and safe Autopilot

Goal: surpass ListedKit with stronger governance.

Deliverables:

- Agent Preferences screen.
- Per-action always-approve rules.
- Tenant-level allowed action types.
- Confidence thresholds by category.
- Autopilot banner for enabled low-risk flows.
- Review of all legal/compliance-forbidden action types.

Safe initial allowlist:

- Internal reminder drafts.
- Document request draft creation, not sending.
- Internal notes only after the canonical note/comment surface exists.
- Read-only summaries.

Do not allow initial always-approve for:

- External email send.
- Waiving compliance.
- Deleting documents.
- Legal judgment.
- Final attorney release.
- Date cascade apply.

Acceptance:

- User can enable and disable a rule from UI.
- Agent explains why an action was auto-approved.
- Audit log shows rule id and policy.
- User can revoke rule and future actions return to manual approval.

### Phase 6: Superior intelligence layer

Goal: move beyond ListedKit parity into predictive coordination.

Deliverables:

- Closing readiness score.
- Blocker prediction.
- "Next best action" ranked by risk.
- Broker/team lead oversight of unresolved agent issues.
- Agent issue aging metrics.
- Weekly transaction health digest.
- Cross-document contradiction report.
- Source-cited transaction summary PDF.

Acceptance:

- User can click "Closing Readiness" and resolve blockers from issue cards.
- Team Lead can see unresolved agent issues by deal.
- Metrics show time-to-resolution for compliance issues, emails, and missing docs.

---

## 13. UI Testing Plan For Non-Developer Real Estate Testers

The plan must ship with frontend-only scripts. Each script should start from a visible page and end with visible success in the UI.

### 13.1 Required test tenant fixtures

In non-production only, create a "Workspace UAT" setup flow that creates real records through the same public app APIs:

- One under-contract buyer transaction.
- Parties: buyer, seller, co-op agent, title company, lender.
- Documents:
  - Purchase Agreement.
  - Wrongly uploaded earnest money receipt slot containing purchase agreement.
  - Inspection Report.
  - Addendum changing closing date.
- Tasks:
  - One overdue task.
  - One auto-email-eligible task.
  - One pinned task.
- Compliance requirements:
  - One uploaded/verified.
  - One missing.
  - One mismatch.
- Email integration test path:
  - Test inbound button or connected sandbox mailbox.

This setup must be launched from an internal QA page or test-tenant banner, not by scripts testers run manually.

### 13.2 UAT script: document mismatch resolution

1. Open the test transaction.
2. Open Agent pane.
3. Click "Compliance blockers."
4. Open "Document Type Mismatch."
5. Click "Draft request for correct receipt."
6. Confirm recipient is title company.
7. Click "Create Draft."
8. Open Email tab.
9. Confirm draft exists and nothing has sent.
10. Open the draft and confirm source data cites the mismatched document.
11. Return to Compliance and confirm the Earnest Money Deposit Receipt requirement is still missing until the correct receipt is attached.

Pass criteria:

- No developer tools used.
- No API calls inspected.
- User can identify the issue, source, draft, and next step from UI.
- The wrong purchase agreement is not treated as satisfying the receipt requirement.

### 13.3 UAT script: addendum date cascade

1. Drag addendum document into Agent composer.
2. Ask: "Update the closing date from this addendum."
3. Confirm agent extracts new date with source chip.
4. Click "Preview date changes."
5. Confirm moved and pinned tasks are shown.
6. Click Apply.
7. Open Timeline and Tasks tabs.
8. Confirm updated dates are visible.
9. Click Undo from conversation.
10. Confirm dates revert.

Pass criteria:

- Cascade never applies without preview.
- Pinned/not-moved rows are explained.
- Undo is visible and works from UI.

### 13.4 UAT script: missing document request

1. Open Compliance blockers.
2. Select a missing document.
3. Click "Request by email."
4. Pick recipient.
5. Click "Create Draft."
6. Open Email tab.
7. Review the draft.
8. Approve or edit/send.

Pass criteria:

- User never types an email from scratch.
- The draft is grounded in the requirement and deal.
- The requirement remains missing until a document is uploaded.
- The agent-created request appears as `pending_review`; it is not sent by `/documents/request`.

### 13.5 UAT script: incoming email resolution

1. Open Email tab.
2. Click "Send test inbound to this deal" in test mode.
3. Select "Buyer asks for inspection report."
4. Confirm inbound thread appears.
5. Confirm agent proposes a draft.
6. Review source data and attachment chip.
7. Approve/send.
8. Confirm the Email tab or AI Email Review shows the sent/approved state.
9. Confirm Activity shows the email action only after the history aggregation work is included; before then, the communication log or Email tab is the proof surface.

Pass criteria:

- Full workflow is visible in the UI.
- The email does not silently disappear into a global queue.

### 13.6 UAT script: drag references

1. Drag a task into Agent composer.
2. Ask "Draft an email for this."
3. Confirm task reference chip appears.
4. Drag a document into composer.
5. Ask "Summarize this document."
6. Confirm answer has source chip.
7. Drag a deadline into composer.
8. Ask "What needs to happen before this?"

Pass criteria:

- Each item can be referenced without typing its name.
- Tap fallback works if drag is unavailable.

### 13.7 UAT script: closing readiness

1. Click "Closing readiness."
2. Review blockers.
3. Resolve one blocker from the issue card.
4. Confirm score/status updates.
5. Confirm unresolved legal/attorney blockers are routed to human review.

Pass criteria:

- Every blocker has a visible owner and next action.
- No legal advice is given.

---

## 14. Automated Test Plan

### 14.1 Frontend integration tests

Add tests for:

- Agent shell renders with existing plan aggregate.
- Drag document/task/deadline creates reference chips.
- Tap fallback creates reference chips.
- Read-only chat answer appears and persists after remount.
- Proposed action card renders preview, source, confidence, and buttons.
- Email draft action creates pending draft and opens Email tab.
- Agent document-request action uses the AI draft/review path, not the direct document request send path.
- Requirement waive action updates Compliance tab and creates undo card.
- Document mismatch action leaves the original requirement missing unless the correct document is attached or a human waives it.
- Task status action updates Tasks tab.
- Date cascade action reuses preview/apply and updates Timeline.
- Stale preview conflict shows "Refresh preview."
- Legal/forbidden action shows refusal card.
- Mobile layout exposes Agent and workbench tabs without overlap.

### 14.2 Backend tests

Add tests for:

- Agent context denies foreign tenant and unauthorized transaction.
- Agent chat stores durable messages.
- Reference IDs are validated against transaction scope.
- Action proposal creation is idempotent.
- Approval re-checks stale rows.
- Agent email compose wrapper rejects a transaction the user cannot access even if the tenant matches.
- Requirement/document attach rejects a document from a different transaction or tenant.
- Document type adoption cannot update a requirement unless the payload contains an explicit "requirement mislabeled" confirmation.
- Action apply writes audit log.
- Transaction history aggregation includes agent/document/requirement/party audit rows once Activity is used as a proof surface.
- Dismiss stores reason.
- Undo replays inverse changes where supported.
- Email proposal creates pending review draft only.
- Agent missing-document request does not call `/api/v1/documents/request`.
- Date proposal cannot apply without fresh cascade preview.
- Forbidden legal action cannot create applyable action.
- Always-approve policy is ignored for forbidden action types.

### 14.3 End-to-end tests

Use Playwright for:

- Desktop 1440x900 split layout.
- Tablet layout.
- Mobile layout.
- Drag/drop reference chip.
- Document mismatch to email draft.
- Date cascade apply/undo.
- Email tab review.
- Accessibility keyboard path through action card approval.

### 14.4 Visual regression

Capture:

- Empty Agent workspace.
- Issue list with blockers.
- Action card pending.
- Action card applied with Undo.
- Email tab empty and populated.
- Mobile composer with chips.
- Compliance scan issue.

Check:

- No text below 12px.
- No overlap at common viewport widths.
- Buttons meet hit target guidance.
- No nested cards inside cards.
- Champagne accent used only for AI/primary emphasis.

---

## 15. Security, Privacy, And Governance

### 15.1 Authorization

Every endpoint must use existing role and transaction access checks:

- Agent, TransactionCoordinator, TeamLead, Admin for internal transaction workspace.
- Attorney permissions remain attorney-safe and state-specific.
- External users do not get internal agent actions.
- Tenant-level access alone is not enough for agent actions. If the wrapped endpoint does not check transaction assignment/access itself, the agent wrapper must do it before invoking the handler.

### 15.2 Tenant isolation

Every new table must include `tenant_id` and RLS/tenant filtering. Reference chips must be resolved server-side and rejected if not part of the current transaction and tenant.

### 15.3 PII handling

PII remains encrypted at rest. The context service decrypts only the minimum needed for the user's authorized transaction. Audit logs should not store raw PII beyond existing policy; summaries should be human-readable but not overexpose emails/phones.

### 15.4 Prompt safety

System rules:

- Work only from supplied context.
- Cite source refs.
- Do not invent missing facts.
- Return proposed actions as typed JSON only through the action schema.
- Never claim an action was performed unless the apply endpoint confirms it.
- Legal boundaries are non-negotiable.

### 15.5 Action safety

- Apply endpoints must not trust LLM output.
- All user-provided IDs must be server-validated.
- Action payloads must be schema-validated per action type.
- Email sends remain review-gated unless a later explicit policy says otherwise. V1 agent actions create drafts only.
- `/api/v1/documents/request` is treated as a manual direct-send-capable endpoint and is not called by v1 agent document-request proposals.
- Compliance matching validates requirement and document transaction scope before applying `matched_document_id`.
- `adopt_ai_document_type` cannot close a mismatch unless the human confirms whether the document was misclassified or the checklist row was mislabeled.
- Document delete remains soft-delete or flag-for-deletion based on role.

---

## 16. Metrics And Success Criteria

Product metrics:

- Median clicks to resolve a missing document: 4 or fewer after issue card appears.
- Median clicks to create a task-related email draft: 3 or fewer.
- 100 percent of AI write actions show source, confidence, and approval status.
- 100 percent of applied AI actions have audit log entries.
- 100 percent of email drafts created by agent are visible in Email tab.
- 100 percent of agent-created document requests use the pending-review AI email path.
- 0 silent date changes without cascade preview.
- 0 external sends without review in v1.
- 90 percent or more of UAT testers can complete the core scripts without developer help.

Quality metrics:

- No regressions in existing transaction workspace integration tests.
- No UI overlap on desktop/tablet/mobile Playwright screenshots.
- No uncaught API errors in UAT scripts.
- No inaccessible icon-only buttons.
- No low-confidence AI output without visible warning.

Competitive metrics:

- Matches ListedKit: chat-centered transaction workspace, reference chips, action approval, compliance scan, email drafting, task/deadline support.
- Surpasses ListedKit: source-cited action previews, deterministic cascade diffs, undo, attachment safety, richer audit trail, UI-only test harness, closing readiness, and tenant governance.

---

## 17. Risk Register

| Risk | Severity | Mitigation |
| --- | --- | --- |
| AI hallucinated action | High | LLM can only propose typed actions; backend validates against real refs and deterministic handlers. |
| User accidentally approves harmful change | High | Preview, risk label, confirmation, undo where possible, and clear audit. |
| Date cascade surprises user | High | Reuse existing cascade preview/apply/undo. Never direct-write dates from chat. |
| Email sends too early | High | Agent creates drafts only in v1; sending remains AI Email Review approval. |
| Agent accidentally uses direct document request send path | High | `compose_document_request_draft` wraps `/ai-emails/compose`; `/documents/request` is manual-only and covered by tests. |
| Compliance mismatch hides a missing document | High | `adopt_ai_document_type` requires explicit mislabeled-row confirmation; mismatch flow keeps the requirement missing until correct attachment or waiver. |
| Legal advice boundary violated | High | System prompt, forbidden action registry, attorney-only guardrails, backend refusal tests. |
| Table sprawl slows delivery | Medium | Add only threads, messages, actions, and optional approval rules. Reuse canonical tables. |
| Context packet too large | Medium | Load selected refs first; summarize older logs; cap history; source refs point back to full records. |
| Stale proposals overwrite newer changes | Medium | Updated-at checks, commit IDs, stale preview response, "Refresh preview." |
| Activity tab misses applied actions | Medium | Expand transaction history aggregation before using Activity as required proof; otherwise verify in canonical tab/thread. |
| Drag/drop inaccessible on mobile | Medium | Provide tap fallback and reference picker. |
| UI becomes busy | Medium | Issue summary, collapsible threads, right-pane workbench, compact action cards. |
| Testers cannot validate backend effects | High | Every effect must update a visible tab, Email tab, Activity, or Audit/Admin view. |

---

## 18. Definition Of Done

The feature is done when:

1. The transaction workspace opens into an agent-centered layout under a controlled feature flag.
2. Users can ask deal-specific questions in a durable conversation.
3. Users can reference documents, tasks, deadlines, requirements, parties, and emails through chips.
4. Drag-to-chat and tap fallback both work.
5. AI issues appear as persistent issue cards.
6. Common issues can be resolved through proposed action cards.
7. Every v1 write action requires approval and shows preview/source/confidence; later always-approve rules are limited to explicit low-risk allowlists.
8. Date changes always use cascade preview/apply.
9. Email actions create visible pending drafts and never silently send in v1.
10. Compliance mismatch and missing-document workflows can be completed from the Agent pane.
11. Email tab shows transaction-native drafts/inbound/sent or the scoped v1 subset.
12. Completed actions are visibly confirmed in the Agent thread and canonical workbench tab; Activity also confirms them after the history aggregation expansion ships.
13. All core UAT scripts are passable by non-developer real estate testers from the frontend.
14. Existing workspace tests continue to pass.
15. New frontend, backend, Playwright, accessibility, and visual tests cover the agent workflows.

---

## 19. Recommended Build Order

Build in this order:

1. Feature flag and non-invasive shell.
2. Durable read-only agent conversation.
3. Reference chips and workbench highlighting.
4. Proposed action schema and frontend action cards.
5. Email draft action.
6. Compliance missing/mismatch actions.
7. Task actions.
8. Date cascade actions.
9. Email tab.
10. Document scan and comparison issue cards.
11. UI-only UAT harness.
12. Always-approve rules and safe Autopilot.
13. Closing readiness and team oversight.

This order avoids the historical failure mode described in the prompt: building impressive AI UI that breaks when a tester tries to complete the workflow. The first shipping slice should already let a tester resolve one real issue end-to-end from the frontend.

---

## 20. First Shippable Slice

The first meaningful release should be:

"Resolve a document mismatch from the Agent pane."

Scope:

- Agent shell.
- Durable messages.
- Reference chips for compliance requirement and document.
- One issue card: Document Type Mismatch.
- One proposed action: Create missing-document request draft.
- Email tab subset showing pending draft.
- Agent thread and Email tab confirmation; Activity confirmation only if history aggregation is included in the slice.
- UAT script and automated tests.

Why this slice:

- It directly matches the ListedKit screenshot.
- It uses existing document verification, compliance requirements, and AI email compose infrastructure.
- It is fully frontend-verifiable.
- It proves the action-card contract before expanding to broader workflows.

Once this slice works, date cascade, task updates, and inbox workflows can follow the same pattern.
