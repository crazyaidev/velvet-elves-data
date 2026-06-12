# AI Wizard Redesign Plan: ListedKit-Parity Plus Source-Cited Review

Prepared: 2026-06-08  
Scope: Planning only. No frontend or backend source code is changed by this document.

## 1. Objective

Revamp Velvet Elves' AI new-transaction wizard from a modal-centered flow into a dedicated, full-screen, no-navigation AI workspace that is easier for real estate professionals to validate from the frontend UI alone.

The redesigned wizard must meet or exceed the AI transaction-coordinator experience users observe in ListedKit:

- Upload purchase agreements, counteroffers, amendments, disclosures, and supporting files.
- Show visible, detailed AI processing progress at every stage.
- Extract transaction facts, parties, dates, contingencies, signature status, and document-control logic.
- Let users review every important extracted field against the source document.
- Show the uploaded document on the right side of the screen.
- When a user clicks an extracted value, jump to the matching source page and highlight the original text or document region.
- Require explicit human confirmation before creating the transaction baseline and generating tasks.
- Let non-developer testers validate the entire workflow with mouse-first frontend interactions.

The plan also preserves the project's core rule: AI assists, humans decide.

## 2. Reviewed Project Context

This plan is grounded in the current documentation and source inventory, not just a conceptual comparison.

Documentation reviewed in `velvet-elves-data`:

- `requirements.txt`
- `SYSTEM_DESIGN.md`
- `milestones.txt`
- `FRONTEND_UI_WORKFLOW_LOGIC.md`
- `STYLE_GUIDE.md`
- `ALL_DOCUMENTS_COMPLETION_PLAN.md`
- `ALL_DOCUMENTS_WORKFLOW_COMPLETION_PLAN.md`
- `TRANSACTIONS_PAGE_COMPLETION_PLAN.md`
- `MILESTONE_4_2_AI_EMAIL_WORKFLOW.md`
- `MULTI_TENANCY_IMPLEMENTATION_PLAN.md`
- `MILESTONE_4_3_IMPLEMENTATION_PLAN.md`
- `MILESTONE_4_3_TESTING_GUIDE.md`
- `MILESTONE_5_1_IMPLEMENTATION_PLAN.md`
- `MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md`
- `ROLE_DASHBOARDS_DESIGN_UPDATE_PLAN.md`
- `ATTORNEY_WORKSPACE_PLAN.md`
- `FSBO_WORKSPACE_PLAN.md`
- `CLIENT_WORKSPACE_PLAN.md`
- `MILESTONE_5_2_IMPLEMENTATION_PLAN.md`
- `MILESTONE_5_3_IMPLEMENTATION_PLAN.md`
- `MILESTONE_6_1_IMPLEMENTATION_PLAN.md`
- `MILESTONE_6_2_IMPLEMENTATION_PLAN.md`
- `LISTEDKIT_COMPETITIVE_ANALYSIS_AND_FEATURE_IMPROVEMENT_PLAN.md`
- `AI_SUGGESTIONS_PAGE_COMPLETION_PLAN.md`
- `WIZARD_TESTING_GUIDE.md`
- `VE-Intelligence-AISuggestions.html`
- `completed_designs/ve-intelligence-ai_suggestions.html`

Frontend source reviewed:

- `velvet-elves-frontend/src/App.tsx`
- `velvet-elves-frontend/src/components/RoleRoute.tsx`
- `velvet-elves-frontend/src/components/ProtectedRoute.tsx`
- `velvet-elves-frontend/src/types/enums.ts`
- `velvet-elves-frontend/src/utils/constants.ts`
- `velvet-elves-frontend/src/utils/returnLocation.ts`
- `velvet-elves-frontend/src/pages/AiEmailReviewPage.tsx`
- `velvet-elves-frontend/src/pages/transactions/TransactionListPage.tsx`
- `velvet-elves-frontend/src/components/active-transactions/NewTransactionModal.tsx`
- `velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx`
- `velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx`
- `velvet-elves-frontend/src/components/wizard/wizardTypes.ts`
- `velvet-elves-frontend/src/components/wizard/ReviewTasksStep.tsx`
- `velvet-elves-frontend/src/components/wizard/SuggestImprovementButton.tsx`
- `velvet-elves-frontend/src/components/wizard/DocumentSplitDialog.tsx`
- `velvet-elves-frontend/src/hooks/useWizardApi.ts`
- `velvet-elves-frontend/src/hooks/useDocuments.ts`
- `velvet-elves-frontend/src/tests/integration/WizardFlow.test.tsx`
- `velvet-elves-frontend/src/tests/mocks/handlers.ts`

Backend source reviewed:

- `velvet-elves-backend/app/api/v1/ai.py`
- `velvet-elves-backend/app/api/v1/documents.py`
- `velvet-elves-backend/app/api/v1/transactions.py`
- `velvet-elves-backend/app/api/v1/esign.py`
- `velvet-elves-backend/app/schemas/ai.py`
- `velvet-elves-backend/app/schemas/transaction.py`
- `velvet-elves-backend/app/services/document_packet_parsing.py`
- `velvet-elves-backend/app/services/providers/base.py`
- `velvet-elves-backend/app/services/providers/parsing.py`
- `velvet-elves-backend/app/services/textract_service.py`

Public ListedKit benchmark sources reviewed:

- ListedKit homepage
- ListedKit Ava page
- ListedKit article: "How ListedKit AI Reads Any Real Estate Contract in 60 Seconds"
- ListedKit broker compliance article
- ListedKit TC burnout article
- ListedKit solutions pages

Important limitation: public ListedKit pages describe Ava's capabilities, upload/review/timeline/checklist workflows, and AI transaction-coordinator positioning, but they do not expose the full logged-in implementation. This plan uses the user's observed modal workflow as the product benchmark for the logged-in UI behavior.

## 2.1 Workflow And Logic Corrections From This Review

This section records the main plan flaws found during the follow-up review and the corrections applied in the rest of this document.

- The route snippet in the first draft used lowercase role names and the wrong `RoleRoute` prop. The app uses exact role values from `UserRole` and `RoleRoute allowedRoles={...}`.
- The first draft did not sufficiently handle route ordering. `/transactions/new` must not be captured by `/transactions/:transactionId`.
- The first draft treated the wizard as only pre-transaction until final commit. Project requirements define `Incomplete` as "wizard started but not confirmed"; this plan now includes an explicit `wizard_run` plus optional `Incomplete` transaction-shell strategy.
- The first draft underplayed the no-document manual fallback. Requirements allow "Skip - enter details manually"; the redesigned wizard must not hard-block final creation when the user intentionally chooses manual mode.
- The first draft implied task preview could be built before review was complete. Task preview must run after required baseline fields are confirmed or manually entered.
- The first draft did not call out the current frontend upload-type mismatch. Requirements and backend upload support more file types than the current wizard validation accepts.
- The first draft treated source highlighting as mostly PDF/image based. DOC/DOCX/TXT inputs need conversion or honest text-only evidence fallback.
- The first draft did not explicitly preserve the existing dry-run task planner. New wizard-run endpoints must reuse the same planner service behind `/api/v1/transactions/preview-tasks`, not fork task logic.
- The first draft did not reconcile the signature workflow requirement with the current source, which currently avoids an e-sign prompt at wizard finalization. This plan now makes signature review an explicit decision point.
- The first draft did not call out canonical field-path mapping. Backend extraction paths such as `transaction.purchase_price`, frontend wizard paths such as `purchase.purchase_price`, and transaction payload keys must be mapped deliberately.

## 3. Current Velvet Elves State

### 3.1 Existing strengths to preserve

The current system already has major foundations that should not be discarded:

- React SPA, FastAPI backend, Supabase PostgreSQL/Auth/Storage/Realtime architecture.
- Existing document upload endpoint: `POST /api/v1/documents/upload`.
- Existing signed document download endpoint: `GET /api/v1/documents/{id}/download`.
- Existing PDF page count and split endpoints: `GET /api/v1/documents/{id}/pages`, `POST /api/v1/documents/{id}/split`.
- Existing AI parse endpoints:
  - `POST /api/v1/ai/parse-document/{document_id}`
  - `GET /api/v1/ai/parse-document/{document_id}/status`
  - `POST /api/v1/ai/parse-document-packet`
  - `GET /api/v1/ai/parse-document-packet/{packet_id}/status`
  - `POST /api/v1/ai/resolve-documents`
  - `POST /api/v1/ai/search-public-source`
- Existing packet parsing that handles multiple documents and contract chronology.
- Existing task preview step in `ReviewTasksStep.tsx`, which already supports a strong "review before create" pattern.
- Existing task dry-run endpoint `POST /api/v1/transactions/preview-tasks`, backed by the same server-side planner as final task generation.
- Existing final task generation endpoint `POST /api/v1/transactions/{transaction_id}/tasks/generate`, including exclusions, date/target overrides, removal reasons, and user-approved AI-added tasks.
- Existing owner assignment rules in transaction creation: Agents own their own deals, while Admin, Team Lead, and Transaction Coordinator users can assign a transaction to an allowed owner.
- Existing AI email review page pattern, including source-data review rails, confidence states, and flagged assumption highlighting.
- Existing AI audit logging expectations across the requirements and email workflow docs.
- Existing document metadata fields: `ai_extracted_data`, `ai_confidence`, and `metadata_json`.
- Existing e-signature endpoints that can classify documents, check whether signatures are needed, send documents for signature, track status, and preserve signed versions.

### 3.2 Current gaps blocking ListedKit-plus quality

The current wizard is not yet robust enough for the requested workflow:

- It is launched primarily through `NewTransactionModal`, which wraps `NewTransactionWizard` in a modal-like overlay.
- `NewTransactionWizard` has a standalone layout mode, but the application does not currently expose a true no-navigation wizard route as the primary flow.
- The parsing progress step uses generic phases such as "Reading documents" and "Checking dates"; it does not display a persisted, backend-driven event log for each processing stage.
- AI extraction fields store `value`, `confidence`, and a free-form `source` string, but not structured document/page/bounding-box evidence.
- The frontend tracks `aiConfidences` and source ranks, but it does not maintain a durable field-to-evidence model.
- The right-side source document viewer does not exist in the wizard.
- Clicking an extracted field cannot currently navigate to a source page or highlight source text.
- Backend Textract raw blocks contain page geometry, but this geometry is not normalized into a reusable evidence table or API response.
- The parse job status schema returns coarse job status and optional result/error, not granular stage events.
- The route model places internal pages under `AppLayout`; the requested wizard must be a protected app route but outside the normal navigation shell.
- The current standalone route plan must account for the existing `/transactions/:transactionId` route; `/transactions/new` must be registered outside the AppLayout route group or before the dynamic route.
- The current frontend `RoleRoute` uses `allowedRoles`, not `roles`, and role values are exact strings such as `Agent`, `TransactionCoordinator`, `TeamLead`, and `Admin`.
- The current wizard file validation accepts only PDF, JPEG, PNG, and TIFF, while requirements and the backend upload endpoint support additional formats such as GIF, DOC, DOCX, WEBP, TXT, and other document types.
- The current parse pipeline is Textract-centered for PDF/image files; DOC/DOCX/TXT files need a separate text extraction or conversion path before they can participate in source-cited review.
- The current wizard's submit path requires at least one persisted document, which conflicts with the documented "Skip - enter details manually" fallback.
- The current final payload always creates `status: 'Active'`, while requirements define `Incomplete` for wizard-started but unconfirmed transactions.
- The current wizard keeps progress and review state in component state; it does not persist a resumable backend wizard run.
- The current wizard does not offer the documented e-signature finalization decision for unsigned documents, even though backend e-sign endpoints exist.
- The current AI extraction paths, wizard state paths, and transaction payload keys are not the same vocabulary; a field-path adapter is required before evidence review can be reliable.

## 4. Product Decision

Build a new dedicated route and workspace:

- Route: `/transactions/new`, preferably exposed as `ROUTES.TRANSACTION_NEW`.
- Component: `WizardWorkspacePage`
- Protection: authenticated creation-capable internal roles only, using the existing `ProtectedRoute` plus `RoleRoute allowedRoles={INTERNAL_ROLES}`.
- Creation-capable roles for this wizard: `Agent`, `TransactionCoordinator`, `TeamLead`, and `Admin`.
- Attorney users should continue through attorney packet/matter intake unless the product explicitly expands this new-transaction wizard to attorney-created matters.
- Layout: full-screen, no app sidebar, no top navigation, no global AI chat overlay, no unrelated transaction navigation.
- Persistence: every wizard session is a resumable draft called a `wizard_run`.
- Transaction draft strategy: before enough transaction data exists, keep the run as a `wizard_run` only; once address/use case or explicit "Save draft" requirements are met, create or update a transaction shell with status `Incomplete`; on final approval, update that transaction to `Active` or create an `Active` transaction if no shell exists.
- Exit behavior: explicit "Save and exit" and "Discard draft" actions using the project's branded confirm dialog, never `window.confirm`.

The current modal should become a compatibility entry point:

- Existing "New Transaction" buttons and `?new=1` links should navigate to `/transactions/new`.
- Quick-create "Full Wizard" links should navigate to `/transactions/new`.
- Global drag/drop and dashboard upload entry points should create a `wizard_run` with uploaded document ids and route to `/transactions/new?run=:runId`, not rely only on in-memory `File[]` props.
- The modal can remain temporarily for backward compatibility only if needed, but the primary UX should be the page.

## 5. Target User Experience

### 5.1 Screen layout

Use a three-pane professional workspace:

1. Left rail: process and navigation
   - AI stage timeline with live progress events.
   - Uploaded document list with parse/OCR status.
   - Wizard sections: Upload or Manual Start, Review Facts, Resolve Conflicts, Missing Info, Signature Decisions, Task Preview, Create.
   - Confidence legend.
   - Autosave status.
   - Draft state: `Unsaved run`, `Saved draft`, `Incomplete transaction`, or `Ready to create`.

2. Center workspace: user decisions
   - Extracted fields grouped by real-estate workflow:
     - Property
     - Contract dates
     - Price and financing
     - Parties and contacts
     - Contingencies
     - HOA, inspection, warranty, occupancy
     - Signatures and document control
     - Ownership and assignment
     - Missing or public-source fields
   - Each field row shows:
     - Human label
     - Extracted value
     - Confidence badge
     - Source document/page chip
     - Conflict or missing indicator
     - Confirm, Edit, Reject controls
   - A "Next unresolved" button moves the user through the fields that need attention.
   - Inline editing uses simple inputs, selects, date pickers, and toggles.

3. Right evidence viewer: source proof
   - Persistent PDF/image viewer.
   - Document tabs or compact document selector.
   - Page thumbnails.
   - Search within OCR text.
   - Zoom controls.
   - Highlight overlay for active evidence spans.
   - Clicking a field in the center jumps to the cited page and highlights the source region.
   - Clicking a highlight selects the corresponding field in the center.
   - If exact coordinates are unavailable, jump to the cited page and highlight a text-only snippet panel with a clear "No box match found" state.
   - For DOC/DOCX/TXT or other non-page-native files, show a rendered preview when conversion exists; otherwise show a text evidence panel and clearly label that page-coordinate highlighting is unavailable for that source.

### 5.1a Manual Entry Fallback

The redesigned wizard must support a no-document path because the requirements explicitly allow "Skip - enter details manually."

Manual mode rules:

- The upload screen includes a secondary "Enter details manually" action.
- Manual mode keeps the same full-screen workspace and progress rail, but the right evidence viewer shows "No source document for this field" instead of a blank broken panel.
- Manual fields are still reviewed and audited, but they do not require document evidence.
- The commit rules must not require an uploaded document when the user intentionally chose manual mode.
- The final summary must distinguish `AI from document`, `manual entry`, `public source`, and `user corrected` values.

### 5.2 Header

The full-screen wizard header should be minimal:

- Velvet Elves mark or wordmark.
- Draft title, such as "New transaction from contract packet".
- Autosave state.
- Secure processing state.
- Help button if a real help surface exists.
- Save and exit.
- Discard draft.

No standard app navigation should appear.

### 5.3 Mobile and tablet behavior

The workflow must remain testable on smaller screens:

- Tablet: two columns with collapsible left rail and right evidence viewer.
- Mobile: center review remains primary; evidence viewer opens as a bottom sheet or "Source" tab.
- The same field click must open the source document and highlight the cited area.
- Buttons must remain large enough for mouse and touch.

## 6. ListedKit-Parity Plus Matrix

| Capability | ListedKit public benchmark | Velvet Elves target |
|---|---|---|
| Contract upload | Upload contract/packet and let AI read it | Multi-file upload, drag/drop, split PDFs, classify documents, parse packet |
| Contract extraction | Extract key dates, parties, contingencies, and deal facts | Extract same plus signature status, document chronology, representation side, HOA/inspection/warranty/occupancy, attorney/title mode |
| Counteroffer/addendum handling | Read counteroffers and update timelines | Explicit document-control resolver with visible winning value, superseded value, and source proof |
| Review extracted data | User reviews AI output before use | Source-cited review for every critical field, with right-side document viewer and click-to-highlight evidence |
| Progress transparency | Show what Ava is doing | Persisted backend progress events at each stage, not a fake timer |
| Timeline/checklist | Build transaction timeline and task checklist | Preview generated tasks before create, show reasons and source fields, allow edits/exclusions before commit |
| Inbox/email intelligence | Ava reads inbox and drafts replies | Reuse AI email review safeguards; future phase links wizard facts to deal inbox and AI email source rails |
| Human control | User can review and adjust | Required confirmation for baseline facts; all edits audited |
| Differentiation | AI TC simplicity | Stronger multi-role workflows, attorney/FSBO/client/vendor portals, source-cited evidence, auditability, white-label controls |

## 7. Data Model Plan

The current `documents.ai_extracted_data` JSON is useful but not sufficient for field-level proof. Add normalized wizard and evidence records while keeping existing document storage.

### 7.1 `wizard_runs`

Stores one resumable AI wizard session.

Recommended fields:

- `id`
- `tenant_id`
- `created_by`
- `transaction_id`, nullable until commit
- `status`: `draft`, `uploading`, `processing`, `review_ready`, `needs_input`, `saved_incomplete`, `committing`, `completed`, `failed`, `abandoned`
- `current_step`
- `mode`: `document_first`, `manual`, `mixed`
- `represented_side`: `buyer`, `seller`, `both`, nullable
- `source_document_ids`: array or relation through `wizard_run_documents`
- `draft_transaction_id`, nullable; points to a `transactions` row with status `Incomplete` when a draft shell has been created
- `owner_user_id`, nullable; mirrors the "Who's Transaction Is It?" decision before commit
- `started_at`
- `last_activity_at`
- `completed_at`
- `metadata_json`

### 7.2 `wizard_run_documents`

Connects uploaded documents to a wizard run.

Recommended fields:

- `id`
- `wizard_run_id`
- `document_id`
- `display_order`
- `document_role`: `purchase_agreement`, `counteroffer`, `amendment`, `disclosure`, `preapproval`, `other`, `unknown`
- `represented_side`
- `page_count`
- `original_mime_type`
- `source_preview_status`: `native_pdf`, `image`, `converted_to_pdf`, `text_only`, `unsupported`
- `evidence_capability`: `box_highlight`, `page_and_snippet`, `text_only`, `none`
- `upload_status`
- `ocr_status`
- `parse_status`
- `quality_status`
- `created_at`
- `updated_at`

### 7.3 `wizard_progress_events`

Makes progress visible, resumable, and auditable.

Recommended fields:

- `id`
- `wizard_run_id`
- `sequence_number`
- `stage_key`
- `status`: `queued`, `running`, `succeeded`, `warning`, `failed`, `skipped`
- `label`
- `detail`
- `document_id`, nullable
- `field_path`, nullable
- `started_at`
- `completed_at`
- `severity`: `info`, `success`, `warning`, `error`
- `metadata_json`

### 7.4 `wizard_extracted_fields`

Stores every field the user must review.

Recommended fields:

- `id`
- `wizard_run_id`
- `field_path`, the canonical UI path, for example `purchase.purchase_price`
- `backend_source_path`, for example `transaction.purchase_price`
- `transaction_payload_key`, for example `purchase_price`
- `label`
- `value_json`
- `normalized_value`
- `confidence`
- `source_kind`: `ai_document`, `manual`, `public_search`, `user_corrected`, `system_rule`
- `review_status`: `pending`, `confirmed`, `edited`, `rejected`, `not_applicable`
- `required_for_commit`
- `evidence_required`
- `controlling_document_id`
- `controlling_page_number`
- `conflict_group_id`, nullable
- `evidence_ids`
- `reviewed_by`
- `reviewed_at`
- `metadata_json`

### 7.5 `ai_field_evidence`

Stores structured proof for field values.

Recommended fields:

- `id`
- `wizard_run_id`
- `document_id`
- `field_path`
- `page_number`
- `snippet`
- `textract_block_ids`
- `bounding_boxes_json`
- `source_confidence`
- `ocr_confidence`
- `match_method`: `llm_structured_citation`, `textract_query`, `exact_text`, `fuzzy_text`, `page_only`, `manual`
- `source_text_hash`
- `created_at`

Bounding boxes should use normalized document coordinates:

```json
{
  "page": 2,
  "boxes": [
    { "left": 0.12, "top": 0.42, "width": 0.31, "height": 0.025 }
  ]
}
```

### 7.6 `document_ocr_pages`

Stores page-level OCR text and geometry references.

Recommended fields:

- `id`
- `document_id`
- `page_number`
- `page_width`
- `page_height`
- `rotation`
- `text`
- `textract_blocks_json` or `blocks_storage_path`
- `created_at`

If raw Textract output is too large for PostgreSQL JSONB, store it in object storage and keep only a signed/internal reference in the database.

### 7.7 Field corrections

Reuse or extend existing correction patterns:

- Preserve `transaction_field_corrections` if already used for AI improvement.
- Add `wizard_field_corrections` only if pre-transaction corrections cannot fit cleanly in the existing model.
- Include before value, after value, reason, evidence id, and user id.

### 7.8 `wizard_task_reviews`

The current task review UI lets users exclude tasks, edit target/due date, record removal reasons, and approve AI-added tasks before creation. Persist those choices on the wizard run so refresh/resume does not lose them.

Recommended fields:

- `id`
- `wizard_run_id`
- `template_id`, nullable for AI-added tasks
- `action`: `include`, `exclude`, `override`, `add_ai_task`
- `name`
- `target`
- `due_date`
- `reason`
- `ai_rationale`
- `created_by`
- `created_at`

This table should not duplicate created tasks. It stores the user's pre-commit task-review decisions and feeds the existing task-generation request body at commit.

## 8. Backend Processing Plan

### 8.1 Processing stages shown to users

Progress events should be real backend events. Do not show only simulated client-side phases.

Recommended visible stages:

1. Uploading files
2. Preparing secure copies
3. Checking file quality
4. Reading visible text
5. Mapping pages and source locations
6. Detecting document types
7. Checking signatures and missing pages
8. Extracting property and parties
9. Extracting price, financing, and deposits
10. Extracting dates and contingency windows
11. Resolving counteroffers and amendments
12. Comparing conflicting values
13. Calculating deadline candidates
14. Checking confidence and missing fields
15. Checking task-preview readiness
16. Preparing the review workspace

Each stage should include a user-facing detail, such as:

- "Reading page 4 of Purchase Agreement.pdf"
- "Found a counteroffer that changes the closing date"
- "Purchase price appears in two documents; newest accepted counteroffer is controlling"
- "Inspection window needs confirmation because only a day count was found"

Task preview is not part of initial document processing. It should run only after the required baseline fields are confirmed, manually entered, or marked not applicable.

### 8.2 Wizard orchestration service

Add a backend service, for example `WizardRunService`, responsible for:

- Creating/resuming wizard runs.
- Attaching documents to runs.
- Emitting progress events.
- Calling the existing upload, OCR, packet parsing, resolver, and task preview services.
- Persisting field records and evidence records.
- Enforcing required confirmations before commit.
- Auditing AI decisions and user overrides.

This should wrap existing parsing functions rather than duplicating their logic.

The first production implementation may continue using polling, but processing state must be durable. Do not rely only on in-memory React state or non-durable in-process timers for long OCR/AI work. If a full background queue is not introduced immediately, persist enough job state and progress events to resume after refresh and backend restarts where practical.

### 8.2a Draft Transaction Lifecycle

The project requirements define `Incomplete` as a wizard-started transaction that has not been confirmed. The redesigned backend must support that lifecycle without forcing fake transaction data too early.

Recommended logic:

1. Create `wizard_run` immediately when the user starts from `/transactions/new`, global drag/drop, or quick-create "Full Wizard".
2. Keep `transaction_id` null while the run has no viable address/use-case data.
3. When the user explicitly saves a draft or when enough transaction data exists, create or update a transaction shell with `status=Incomplete`.
4. Link uploaded documents to the `Incomplete` transaction once it exists, while retaining `wizard_run_documents` for resume/evidence.
5. On final approval, update the existing shell to `Active`; if no shell exists, create a new `Active` transaction.
6. Generate tasks only after the transaction is `Active` and the user has approved the task preview.
7. If commit fails after any partial write, show a recoverable state and audit/compensate rather than silently stranding a transaction without tasks.

### 8.2b File-Type Processing

The plan must align frontend validation, backend upload support, and AI parsing support.

- PDF and supported image files should use the existing Textract path.
- DOC/DOCX/TXT files should either be converted to a rendered preview/PDF before evidence review or parsed through a text extraction path with text-only evidence.
- GIF/WEBP and other accepted image types should be normalized to a supported image format if Textract or the viewer cannot process them directly.
- Source highlighting must be honest: box highlights only when rendered-page coordinates exist; otherwise use page/snippet or text-only citation states.
- The frontend should not advertise an accepted file type unless the backend can upload it and the wizard can either parse it or give a clear manual-review fallback.

### 8.3 Evidence extraction

Extend current parsing output from free-form source strings to structured citations.

Implementation path:

1. Extend the existing packet parser's `sources` output instead of replacing it. Current packet parsing already asks for source snippets keyed by dotted paths.
2. Update AI extraction prompts and Pydantic schemas to request structured citations:
   - `document_id`
   - `file_name`
   - `page_number`
   - `quoted_snippet`
   - optional `field_label`
3. Add a field-path adapter that maps backend source paths, wizard UI paths, and transaction payload keys.
4. Use Textract raw blocks to map snippets to one or more bounding boxes.
5. Match in this order:
   - Textract query answer block when available.
   - Exact snippet match within page OCR text.
   - Normalized/fuzzy phrase match.
   - LLM-supplied page with text-only snippet when no coordinates match.
6. Store the match method so reviewers understand evidence quality.
7. Treat missing evidence for critical AI-document fields as a review issue, even if value confidence is high.
8. Do not require document evidence for fields that are intentionally manual, public-source, system-rule, or marked not applicable.

### 8.3a Two-Pass Agreement Checks

Requirements call for a double-check mechanism. The current packet parser produces one resolved extraction result. The redesigned wizard should add an agreement layer for critical fields.

Recommended approach:

- Keep the packet-level parser for multi-document chronology.
- Run a second extraction/check pass for critical fields using a different prompt strategy or validation template.
- Compare value, normalized value, source page/snippet, and confidence for critical fields.
- If passes disagree on address, purchase price, closing date, acceptance date, parties, signature status, or requested deliverable, mark the field `pending` with an explicit conflict/warning.
- Do not let high overall confidence hide field-level disagreement.

### 8.4 Document-control logic

Keep and strengthen the existing packet resolver:

- Accepted counteroffers and amendments override earlier terms only for modified fields.
- Broad reinstatement carries forward unmodified earlier terms.
- Supersedes-all-prior language dismisses earlier terms only when explicit.
- Missing referenced documents create a visible warning.
- Signature gaps create visible warnings.
- The review UI must show both the winning value and superseded/conflicting values.

### 8.5 Public-source search

Use public-source search only for fields that cannot be confirmed from uploaded documents.

Rules:

- Label public-source values clearly.
- Show searched sources and source labels.
- Require user confirmation.
- Do not silently replace contract data with public-source data.
- Log what was searched, what was found, and who accepted it.

## 9. API Plan

Add a wizard-run API surface under `/api/v1/wizard-runs`.

Recommended endpoints:

- `POST /api/v1/wizard-runs`
  - Create a draft wizard run.
- `GET /api/v1/wizard-runs/{run_id}`
  - Resume a run, including status and current step.
- `PATCH /api/v1/wizard-runs/{run_id}`
  - Update represented side, owner, current step, mode, or draft metadata.
- `POST /api/v1/wizard-runs/{run_id}/documents`
  - Attach uploaded documents to the run, or upload through the run.
- `POST /api/v1/wizard-runs/{run_id}/save-draft-transaction`
  - Create or update an `Incomplete` transaction shell when enough data exists or the user explicitly saves a draft.
- `POST /api/v1/wizard-runs/{run_id}/start-processing`
  - Start OCR, parse, resolver, evidence mapping, and review model creation.
- `GET /api/v1/wizard-runs/{run_id}/events`
  - Return progress events, with optional `since_sequence`. Polling is acceptable for v1; SSE can be added later.
- `GET /api/v1/wizard-runs/{run_id}/review-model`
  - Return sections, fields, conflicts, missing items, evidence summaries, and task preview status.
- `PATCH /api/v1/wizard-runs/{run_id}/fields/{field_path}`
  - Edit a field value.
- `POST /api/v1/wizard-runs/{run_id}/fields/{field_path}/confirm`
  - Confirm a field value.
- `POST /api/v1/wizard-runs/{run_id}/fields/{field_path}/reject`
  - Reject a field value and optionally mark it manual/not applicable.
- `GET /api/v1/wizard-runs/{run_id}/fields/{field_path}/evidence`
  - Return source locations for the active field.
- `POST /api/v1/wizard-runs/{run_id}/public-source-search`
  - Search for missing info with source labeling.
- `POST /api/v1/wizard-runs/{run_id}/preview-tasks`
  - Preview generated task plan from confirmed baseline fields. This endpoint must call the same server-side planner used by `POST /api/v1/transactions/preview-tasks`.
- `PATCH /api/v1/wizard-runs/{run_id}/preview-tasks/{task_key}`
  - Persist a pre-commit include/exclude/override/add decision on `wizard_task_reviews`; it does not edit created tasks because no tasks exist yet.
- `POST /api/v1/wizard-runs/{run_id}/commit`
  - Create or activate the transaction, link documents, lock confirmed baseline, create parties, apply reviewed task decisions, generate tasks, process any user-approved signature actions, and audit everything.

Document viewer support:

- Reuse `GET /api/v1/documents/{document_id}/download` for signed source URLs.
- Add `GET /api/v1/documents/{document_id}/ocr-pages/{page_number}` if OCR text/boxes should be lazy-loaded.
- Add `GET /api/v1/documents/{document_id}/evidence?wizard_run_id=...&field_path=...` if evidence is not returned inside the review model.
- Evidence endpoints must authorize through the wizard run/document relation and the same tenant/transaction access rules used by document download. Do not expose source evidence for a document merely because a user knows its id.

Compatibility endpoints to keep:

- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/{id}/download`
- `GET /api/v1/documents/{id}/pages`
- `POST /api/v1/documents/{id}/split`
- `POST /api/v1/ai/parse-document-packet`
- `GET /api/v1/ai/parse-document-packet/{packet_id}/status`
- `POST /api/v1/ai/resolve-documents`
- `POST /api/v1/transactions/preview-tasks`
- `POST /api/v1/transactions/{transaction_id}/tasks/generate`

The new wizard-run API should orchestrate and persist around these capabilities first, then retire direct frontend calls only when parity is proven.

## 10. Frontend Implementation Plan

### 10.1 Routing

Add a protected route outside `AppLayout`. It should sit in the protected route group before the AppLayout route group, or otherwise be registered before `/transactions/:transactionId` so the string `new` is never treated as a transaction id.

```tsx
<Route
  path={ROUTES.TRANSACTION_NEW}
  element={
    <RoleRoute allowedRoles={INTERNAL_ROLES}>
      <WizardWorkspacePage />
    </RoleRoute>
  }
/>
```

Implementation notes:

- Add `TRANSACTION_NEW: '/transactions/new'` to `ROUTES`.
- Use the existing `INTERNAL_ROLES` values: `Agent`, `TransactionCoordinator`, `TeamLead`, `Admin`.
- Keep the route inside an existing `<Route element={<ProtectedRoute />}>` group, but outside the `AppLayout` element group.
- Clients, FSBO users, vendors, public viewers, and Attorneys should not access this internal transaction-creation wizard unless product requirements change.
- `returnLocation.ts` already allows `/transactions/*` for internal roles, but add route tests so a saved `/transactions/new` return URL is restored for internal users and rejected for portal users.

### 10.2 Component structure

Recommended components:

- `WizardWorkspacePage`
- `WizardWorkspaceShell`
- `WizardProgressRail`
- `WizardDocumentList`
- `WizardReviewPanel`
- `WizardFieldSection`
- `WizardFieldRow`
- `WizardConflictResolver`
- `WizardMissingInfoPanel`
- `WizardTaskPreviewPanel`
- `WizardOwnerAssignmentPanel`
- `WizardSignatureDecisionPanel`
- `WizardEvidenceViewer`
- `WizardPdfViewer`
- `WizardImageViewer`
- `EvidenceHighlightOverlay`
- `WizardExitDialog`

Recommended hooks:

- `useWizardRun`
- `useWizardRunEvents`
- `useWizardReviewModel`
- `useWizardFieldActions`
- `useWizardEvidence`
- `useWizardCommit`
- `useWizardFieldPathMap`

Continue using `useWizardApi` during migration where practical, but move new run-specific calls into a dedicated hook so the old modal code does not become more complex.

### 10.3 Reuse existing frontend work

Reuse:

- `DocumentSplitDialog` for PDF splitting.
- Existing upload validation patterns, but update accepted formats to match backend support and documented requirements.
- `ReviewTasksStep` logic and task preview patterns.
- `SuggestImprovementButton`, extended to include wizard run id, field path, evidence id, and document/page context.
- AI email review source-rail concepts from `AiEmailReviewPage.tsx`.
- Confidence badge patterns from `STYLE_GUIDE.md`.
- Existing toasts, branded confirm dialog, and design tokens.
- Existing owner-assignment behavior from `NewTransactionWizard`: Agents own their own transactions, while Admin, Team Lead, and Transaction Coordinator users can pick an allowed owner.
- Existing FSBO guard: an FSBO deal must be assigned to a `ForSaleByOwner` account so it appears in the seller portal.
- Existing task review behavior: excluded template ids, overrides, exclusion reasons, and AI-added tasks must persist on the wizard run and flow into final generation.

Add:

- A canonical field-path map that translates backend extraction paths, UI paths, evidence paths, and `TransactionCreateRequest` keys.
- A source-kind display adapter so users can tell AI-document data, manual data, public-source data, and user-corrected data apart.
- A viewer adapter for PDF, image, converted document, and text-only evidence sources.

Avoid:

- Nested card-heavy UI.
- Marketing-style hero sections.
- Dead-end controls that do not map to real backend data.
- `window.alert`, `window.confirm`, or `window.prompt`.
- Fake data in production paths.

### 10.4 Review interaction model

Every extracted field should support:

- Click row: select field and jump right viewer to evidence.
- Confirm: marks field reviewed.
- Edit: inline edit with immediate source kind changing to user-corrected while retaining the original AI value in history.
- Reject: marks AI value unusable and asks for manual replacement or not applicable.
- Show conflict: opens comparison of competing values and sources.
- Show history: displays AI value, user edits, and audit trail if available.
- Source fallback: if the field is manual, public-source, or text-only, the evidence action opens the relevant manual/public/source panel instead of pretending a document highlight exists.

Mouse-first controls:

- "Next unresolved"
- "Confirm visible high-confidence fields" only when each field has evidence or an accepted non-document source, no conflict, and the action opens a summary confirmation first.
- "Show source"
- "Edit"
- "Use this value"
- "Search public sources"
- "Mark not applicable"

### 10.5 Commit rules

The user cannot create the transaction until:

- Required property fields are confirmed, manually entered, or accepted from public search where allowed.
- Required purchase fields are confirmed, manually entered, or marked not applicable.
- Required parties are confirmed enough to create the transaction.
- Conflicting controlling values are resolved.
- Missing referenced documents are acknowledged.
- Task preview is generated after confirmed baseline data is available.
- The user approves the final task plan.
- Signature warnings are either resolved, assigned to an e-sign action, or explicitly acknowledged.
- In document-first mode, required uploaded source documents are linked to the run. In manual mode, uploaded documents are not required.

The commit step must show:

- Transaction facts to be created.
- Documents to be linked.
- Parties to be created.
- Tasks to be generated.
- Fields sourced from public search.
- Fields edited manually.
- The transaction owner and assignment result.
- Whether the commit is activating an existing `Incomplete` transaction or creating a new `Active` transaction.
- Any e-signature actions that will be queued after creation.
- Remaining warnings.

### 10.6 Signature Review And E-Sign Decisions

Requirements say unsigned documents should be reviewed and, when an e-sign provider is connected, the user should be offered an electronic-signature action at finalization. Current wizard source intentionally avoids this prompt during create, so this is a required product alignment decision.

Recommended behavior:

- During document processing, detect signature status and missing signatures.
- In the review workspace, show signature warnings as source-cited fields with document/page evidence where available.
- On the final commit screen, show a "Signature decisions" section only when unsigned/signature-needed documents exist.
- Let the user choose one of:
  - Queue e-sign after transaction creation.
  - Create transaction and handle signature later.
  - Mark signature not required with reason.
- If no e-sign provider is connected, show a non-blocking explanation and an "handle later" path.
- Any queued e-sign action should occur after transaction creation and document linking, using the existing e-sign endpoints and audit trail.

## 11. Visual Design Direction

The redesign should extend the existing Velvet Elves style rather than imitate ListedKit visually.

Design principles:

- Calm, premium, AI-aware, and professional.
- Dense enough for real work, not a landing page.
- Champagne or warm accent for AI activity.
- Neutral surfaces for review work.
- Confidence colors should follow the style guide: green, amber, and rose/red.
- Source highlights in the document should be visible but restrained.
- Use lucide icons for toolbar buttons and field actions.
- No robot mascots, neon AI effects, decorative gradient blobs, or oversized hero copy.

Suggested visual hierarchy:

- Full-screen background: `ve-surface-1`.
- Header: compact, white or near-white, bottom border.
- Left progress rail: subdued brand tone with small status chips.
- Center field review: unframed page section with grouped rows.
- Right source viewer: fixed evidence surface with toolbar and page canvas.
- Field row active state: subtle left edge plus pale highlight.
- Document highlight: translucent amber fill with a crisp outline.

## 12. Frontend-Only Validation Workflows

Real estate professional testers must be able to validate these from the UI with no developer tools.

### Workflow 1: Clean purchase agreement

1. Open `/transactions/new`.
2. Upload one purchase agreement PDF.
3. Watch detailed progress events.
4. Review property, price, closing date, parties, and contingencies.
5. Click purchase price.
6. Confirm the right viewer jumps to the correct page and highlights the original price.
7. Confirm all required fields.
8. Review generated tasks.
9. Create the transaction.
10. Verify transaction, documents, history, and tasks from the UI.

### Workflow 2: Purchase agreement plus counteroffer

1. Upload the original purchase agreement and counteroffer.
2. Watch document classification and chronology events.
3. Confirm the wizard flags changed fields.
4. Click closing date.
5. Confirm the viewer can show the original value and the counteroffer value.
6. Choose the controlling value if needed.
7. Verify generated deadlines use the confirmed controlling value.

### Workflow 3: Low-confidence extraction

1. Upload a blurry or partially scanned contract.
2. Confirm progress shows quality warnings.
3. Confirm low-confidence fields are not silently accepted.
4. Open source evidence and verify page/snippet fallback.
5. Correct the value manually.
6. Confirm audit copy shows user-corrected value.

### Workflow 4: Missing information and public search

1. Upload documents missing an HOA or county field.
2. Trigger public-source search from the missing info panel.
3. Confirm the UI shows what sources were searched.
4. Confirm public-source values are labeled as public-source data.
5. Accept or reject the result.
6. Confirm the commit summary distinguishes contract data from public-source data.

### Workflow 5: Resume an incomplete run

1. Start a wizard run.
2. Upload documents and let processing finish.
3. Exit before commit.
4. Confirm the run is saved either as a resumable wizard run or an `Incomplete` transaction when enough transaction data exists.
5. Return from dashboard, Pending transactions, or `/transactions/new`.
6. Resume the draft.
7. Confirm uploaded documents, progress events, reviewed fields, owner selection, task-review choices, and current step persist.

### Workflow 6: Role and permission checks

1. Agent can create and resume own runs.
2. Transaction Coordinator can create and assign within allowed tenant rules.
3. Team Lead can view team runs when permitted.
4. Admin can inspect runs for support/audit.
5. Attorney does not enter this new-transaction wizard unless product scope changes; attorney packet intake remains separate.
6. Client, FSBO, vendor, and public roles cannot access the internal wizard.
7. Attempts to access unauthorized document evidence return a friendly UI error, not leaked data.

### Workflow 7: Manual no-document creation

1. Open `/transactions/new`.
2. Choose "Enter details manually" instead of uploading a document.
3. Enter property, representation, price, dates, parties, and missing required details.
4. Confirm the right evidence panel clearly says there is no source document for manual fields.
5. Review task preview.
6. Create the transaction.
7. Verify no document upload was required and manual fields are labeled/audited as manual.

### Workflow 8: Non-PDF source fallback

1. Upload a DOCX or supported non-PDF document.
2. Confirm the wizard either converts it to a rendered preview or shows text-only evidence.
3. Click an extracted field.
4. Confirm the UI does not promise a box highlight if the source has no page coordinates.
5. Confirm the field can still be reviewed, edited, and committed.

### Workflow 9: Signature decision

1. Upload a packet with a missing signature.
2. Confirm the processing log flags signature review.
3. Click the signature warning and verify source evidence opens.
4. On final commit, choose whether to queue e-sign, handle later, or mark not required with a reason.
5. Confirm the transaction is created and the chosen signature decision appears in audit/history.

## 13. Automated Testing Plan

Backend tests:

- `wizard_runs` creation, resume, status transitions, and permissions.
- `Incomplete` transaction shell creation, resume, and final transition to `Active`.
- Manual mode commit without uploaded documents.
- Owner assignment rules for Agent, Transaction Coordinator, Team Lead, Admin, and FSBO-owned deals.
- Progress event ordering and idempotency.
- Packet parser emits structured citations.
- Evidence matcher maps snippets to Textract boxes.
- Page-only fallback when no box match is possible.
- DOC/DOCX/TXT text-only or converted-preview evidence fallback.
- Conflict resolver for counteroffers, amendments, supersedes-all-prior, and broad reinstatement.
- Commit rejects unconfirmed required fields.
- Task preview endpoint reuses the existing planner rather than diverging from `/api/v1/transactions/preview-tasks`.
- Commit creates transaction, parties, linked documents, tasks, and audit records atomically.
- Signature-needed detection produces a review decision and optional e-sign action.

Frontend unit tests:

- `/transactions/new` route uses `RoleRoute allowedRoles={INTERNAL_ROLES}` and is not captured by `/transactions/:transactionId`.
- Progress rail renders queued/running/succeeded/warning/failed events.
- Field row confidence, source, conflict, and review states.
- Field click selects evidence and calls viewer jump.
- Edit/confirm/reject controls call correct APIs.
- Source viewer handles PDF, image, page-only evidence, and missing evidence.
- Source viewer handles converted-document and text-only evidence states.
- Manual mode labels fields correctly and does not show broken source controls.
- Owner assignment and FSBO owner guard render only for allowed roles.
- Exit dialog uses the app confirm pattern.

Playwright or equivalent E2E tests:

- Clean upload to commit.
- Multi-document counteroffer resolution.
- Low-confidence manual correction.
- Public-source missing info acceptance.
- Refresh/resume.
- Save as `Incomplete`, resume from Pending, then activate.
- Manual no-document create.
- Non-PDF/text-only source fallback.
- Signature decision path.
- No-nav full-screen layout.
- Evidence viewer screenshot checks on desktop and mobile.

Golden contract suite:

- At least 10 known transaction packets across states/forms.
- Include clean PDF, scanned PDF, counteroffer, amendment, seller disclosure, preapproval, missing pages, missing signatures, and blurry scan.
- Expected extracted fields, expected controlling values, and expected page/evidence references.

## 14. Rollout Phases

### Phase 0: Design lock and inventory

- Approve this plan.
- Confirm route name and role list.
- Confirm the `wizard_run` plus `Incomplete` transaction-shell policy.
- Select PDF viewer library.
- Select DOC/DOCX conversion or text-only fallback policy.
- Confirm whether raw Textract blocks are stored in PostgreSQL JSONB or object storage.
- Define critical fields that require evidence before high-confidence bulk confirmation.

### Phase 1: Full-screen wizard shell

- Add `/transactions/new` outside `AppLayout`.
- Add `ROUTES.TRANSACTION_NEW`.
- Register the route before any `/transactions/:transactionId` match.
- Redirect current new-transaction CTAs to the page.
- Reuse current upload, parsing, field review, and task preview logic.
- Keep `RoleRoute allowedRoles={INTERNAL_ROLES}` with exact implemented role strings.
- Keep behavior equivalent to the old wizard while changing the workspace model.

### Phase 2: Draft lifecycle and manual fallback

- Add `wizard_runs`.
- Add save/resume APIs.
- Add manual no-document mode.
- Add `Incomplete` transaction shell creation once enough data exists.
- Persist owner selection, reviewed fields, and task-review choices.
- Ensure final confirmation updates `Incomplete` to `Active`.

### Phase 3: Real progress events

- Add `wizard_progress_events`.
- Emit backend events from upload, OCR, parse, resolver, and later task-preview stages where applicable.
- Replace generic client-only parsing phases with event-driven progress.
- Add retry and failure states.

### Phase 4: Evidence model and viewer

- Add OCR page and evidence storage.
- Extend parser citations.
- Add canonical field-path mapping.
- Implement evidence matching.
- Build right-side PDF/image viewer with page jump and highlight overlay.
- Add converted-document or text-only evidence fallback for non-PDF sources.
- Add field click to source navigation.

### Phase 5: Review UX and conflict handling

- Add structured field review model.
- Add confirm/edit/reject per field.
- Add conflict comparison for counteroffers and amendments.
- Add missing info and public-source confirmation inside the new workspace.
- Add owner/assignment review.
- Add signature decision review.

### Phase 6: Commit, audit, and task plan

- Require confirmed baseline fields before commit.
- Generate task preview from confirmed values.
- Let users edit/exclude preview tasks before create.
- Commit transaction, parties, documents, tasks, and audit records atomically.
- Queue any approved e-signature actions after transaction/document linkage.
- Show post-create success with links to the created transaction and audit/history.

### Phase 7: Superior capabilities beyond ListedKit

- Deal inbox integration: link emails to wizard facts and transaction context.
- Today command center: after commit, show urgent deal work generated from the wizard baseline.
- Calendar sync: publish confirmed deadlines and reminders.
- Attorney/FSBO/vendor handoffs: create role-specific follow-up flows from the same confirmed baseline.
- Admin AI quality dashboard: evidence match rate, correction rate, field-level confidence drift, and provider comparison.
- State rule library: combine confirmed contract dates with configurable state/team templates.

## 15. Acceptance Criteria

The implementation is complete only when all of the following are true:

- The primary AI wizard opens as a full-screen no-navigation page.
- `/transactions/new` is registered safely and cannot be mistaken for `/transactions/:transactionId`.
- Only `Agent`, `TransactionCoordinator`, `TeamLead`, and `Admin` roles can access the internal new-transaction wizard unless requirements are explicitly changed.
- Users can upload multiple documents and split multi-page PDFs from the UI.
- Users can choose manual mode and create a transaction without uploading a document.
- Accepted upload formats match the backend and documented file-type policy, with clear parse/preview fallback for formats that cannot produce box highlights.
- Wizard runs persist through refresh and can become `Incomplete` transaction shells when saved as drafts.
- Final approval activates an existing `Incomplete` transaction or creates a new `Active` transaction.
- Progress is backend-driven and persists through refresh.
- Every critical AI-extracted field shows confidence and source.
- Clicking a field opens the source document on the correct page.
- When evidence coordinates exist, the original source region is highlighted.
- When only page/snippet or text-only evidence exists, the UI clearly shows that fallback.
- Conflicts across documents are visible and resolvable from the UI.
- Missing info can be searched, labeled, accepted, or rejected from the UI.
- Users can confirm, edit, or reject fields without developer tools.
- Transaction creation is blocked until required fields and conflicts are resolved.
- Task preview is generated from confirmed baseline data and reviewed before tasks are created.
- Task preview and final task generation use the same server-side planner.
- Owner assignment, FSBO owner guardrails, and permission checks are validated from the UI.
- Signature-needed warnings are source-cited and result in an explicit queue/handle-later/not-required decision.
- Commit creates the transaction, links documents, creates parties/tasks, and audits AI plus human decisions.
- Non-developer testers can complete the documented workflows without backend access.
- No production UI button is decorative or dead-ended.

## 16. Risks and Decisions Needed

Open decisions:

- PDF viewer library: `react-pdf`/PDF.js is the likely default unless the project already has a preferred viewer.
- DOC/DOCX/TXT policy: convert to rendered preview/PDF for page evidence, or support text-only evidence for v1.
- Draft policy: exactly when to create an `Incomplete` transaction shell versus keeping only a `wizard_run`.
- OCR geometry storage: JSONB for smaller payloads versus object storage for full Textract block payloads.
- Progress transport and worker durability: polling first for simplicity; SSE or realtime channel later if needed; durable queue versus persisted in-process job metadata must be decided.
- Critical evidence policy: decide which fields require structured evidence before high-confidence bulk confirmation.
- Old modal deprecation: decide whether to remove it immediately or leave it as a redirecting compatibility wrapper.
- Signature finalization: whether to queue e-sign actions during the wizard commit or only create an acknowledged follow-up task.

Risks:

- Textract geometry and rendered PDF coordinates must be normalized carefully or highlights will drift.
- Converted DOC/DOCX previews can change pagination; evidence coordinates must reference the rendered artifact the user sees, not an invisible intermediate text stream.
- Some scanned documents will not yield reliable bounding boxes; the UI must handle text-only evidence honestly.
- Long-running OCR/AI work needs robust background job handling so users can leave and resume.
- Public-source search can create trust issues if it appears to override contract terms; labeling and confirmation are mandatory.
- A beautiful UI without real endpoint coverage would repeat prior planning failures. Every planned control must map to a real endpoint, state transition, or explicitly gated future phase.

## 17. Recommended First Engineering Tickets

1. Add `ROUTES.TRANSACTION_NEW`, register `/transactions/new` outside `AppLayout`, and redirect current new-transaction CTAs to it.
2. Correct route tests and role gating with `RoleRoute allowedRoles={INTERNAL_ROLES}` using `Agent`, `TransactionCoordinator`, `TeamLead`, and `Admin`.
3. Add `wizard_runs`, `wizard_run_documents`, and basic save/resume APIs.
4. Add manual no-document mode and remove the final-submit document hard-block when manual mode is selected.
5. Implement the `Incomplete` transaction-shell policy and final transition to `Active`.
6. Persist owner selection, FSBO owner validation, reviewed fields, and task-review choices.
7. Add `wizard_progress_events` and wrap existing packet parsing in a wizard-run orchestration service that emits real events.
8. Add canonical field-path mapping across backend extraction paths, UI paths, evidence paths, and transaction payload keys.
9. Add structured citation schema to AI extraction output while preserving backward compatibility with existing `source` strings.
10. Persist OCR page text and Textract block geometry for uploaded wizard documents.
11. Add DOC/DOCX/TXT conversion or text-only evidence fallback.
12. Add evidence matcher and `ai_field_evidence` API.
13. Build `WizardEvidenceViewer` with signed document URLs, page jump, highlight overlay, and text-only fallback.
14. Replace current field review with source-cited `WizardReviewPanel`.
15. Integrate task preview through the existing planner and gate commit on reviewed baseline fields.
16. Add signature decision UI and backend audit/e-sign action handling.
17. Add the frontend-only validation workflows to the testing guide and automate the clean path, counteroffer path, manual path, and resume path.

## 18. Bottom Line

The superior version is not just a larger modal. It is a source-cited AI transaction intake workspace.

The user should feel the AI doing the tedious reading, but never feel forced to trust a black box. Every important fact should answer three questions instantly:

- What did the AI find?
- Where exactly did it find it?
- What does the human want to approve, edit, or reject?

That is the workflow that can surpass ListedKit while staying aligned with Velvet Elves' architecture, audit requirements, multi-role ambitions, and professional real-estate UI style.
