# AI Wizard Redesign: Full-Screen Source-Cited Intake Workspace (Superior Plan, V2)

Prepared: 2026-06-08
Status: Planning only. No frontend or backend source code is changed by this document.
Revision: V2.1 - incorporates a second workflow/logic review pass against the implemented source and the requirements/workflow docs. The findings and corrections are recorded in Section 3A (F1-F11) and folded into the affected body sections.
Supersedes: `AI_WIZARD_REDESIGN_SUPERIOR_LISTEDKIT_PLAN.md` (the OpenAI Codex draft), which is retained as a reference. Where the two disagree, this document is the corrected, source-grounded version.

---

## 0. How this plan is different (and why it is safe to build from)

Every prior plan that broke during frontend testing broke for the same reason: it described features the implemented code could not actually serve, so the end-to-end flow dead-ended somewhere a real-estate tester could not recover from. To avoid repeating that, this plan is built in three disciplined layers:

1. **Verified current state** (Section 2): what the code does today, cited to specific files and lines. I read the real wizard, the real AI/Textract pipeline, the real parsing prompt, the real routing, and the real task planner before drafting.
2. **Corrections to the Codex draft** (Section 3): the prior draft is good, but it asserts several things about the backend that are not true. Building on those assertions would re-create the exact dead-end problem. They are corrected here.
3. **A reuse-first, phased build** (Sections 7 to 14): the headline feature (click an extracted value, jump to the source page, highlight the original) is shippable in Phase 1 with zero new database tables, because the extraction pipeline already returns page numbers and verbatim snippets. Heavier infrastructure (pixel-accurate bounding boxes, a persisted wizard-run model, durable per-stage events) is layered on only after the simple version is proven in the UI.

The guiding product rule is unchanged from the rest of the system: **AI assists, the human decides.** Every important fact must answer three questions on screen: what did the AI find, where exactly did it find it, and what does the human approve, edit, or reject.

---

## 1. Objective and scope

Replace the modal-hosted New Transaction wizard with a dedicated, full-screen, no-navigation **AI Intake Workspace** at `/transactions/new`, and raise it to meet or exceed the ListedKit "AI transaction coordinator reads the contract" experience.

Required outcomes:

- A full-screen page with no app sidebar, no top nav, and no global AI chat overlay.
- Multi-file upload (with PDF splitting and a no-document manual fallback).
- Visible, detailed, stage-by-stage AI processing progress that reflects real backend work, not a fake timer.
- Source-cited review of every important extracted field: a persistent document viewer on the right, and clicking an extracted value jumps the viewer to the cited page and highlights the original text.
- Cross-document conflict transparency (counteroffers and amendments) showing the winning value and the superseded value, each attributed to its source.
- Required human confirmation before the transaction baseline is created and tasks are generated.
- Full validation by non-developer real-estate testers using mouse-first interactions and minimal typing.

Out of scope for this plan: changing the attorney packet/matter intake flow, changing the task engine's internal generation logic (the wizard reuses the existing planner), and any source-code edits (this is a plan only).

### 1.1 Non-negotiable pipeline invariants (this plan preserves them)

The established document parsing pipeline is a fixed foundation. Nothing in this plan changes it; everything is layered on top. The invariants:

1. **Every page is OCR'd by Amazon Textract.** Whether a page is text or image, the rendered page is sent to Textract; the PDF's own embedded text layer is never trusted as the source of truth. This is the existing behavior - the Textract module sends the original PDF/image to Textract rather than the PDF text layer ([textract_service.py:1-8,80-98](velvet-elves-backend/app/services/textract_service.py#L1-L8)). The plan keeps Textract as the sole OCR path for all pages and all supported document types.
2. **The full OCR text is sent to the LLM.** Extraction interprets the complete Textract OCR output (per-page text lines, plus any query/form/table/signature detections), assembled into the packet text the LLM reads ([textract_service.py:476-566](velvet-elves-backend/app/services/textract_service.py#L476-L566); [document_packet_parsing.py:285-331](velvet-elves-backend/app/services/document_packet_parsing.py#L285-L331)). The plan does not chunk, summarize, sample, or otherwise reduce what reaches the LLM. The two-pass check (§7.3) re-reads the **same** full OCR text with a different prompt; it does not re-OCR or trim. (The only existing reduction is the configurable `textract_max_chars` safety cap in `format_textract_result`; the plan does not lower it and treats "send the full OCR text" as the standing contract.)
3. **Unsupported file types are converted INTO the Textract path, never around it.** Any DOC/DOCX/TXT conversion or GIF/WEBP normalization (§3 item 1) exists only to produce a Textract-compatible rendered artifact so those pages also get full OCR. There is no text-extraction shortcut that bypasses Textract.

Consequence for the evidence feature: because Textract already OCRs every page, the per-page OCR text and geometry exist server-side for every document uniformly. The evidence highlight is therefore driven by Textract OCR output, **not** by any client-side PDF text layer, and there is no "native-text vs scanned" split in how highlighting works. The only real gap is that this already-produced OCR output is not yet exposed to the client (a read path to add), not anything about how documents are parsed.

---

## 2. Verified current state (grounded in source)

### 2.1 The wizard that exists today

- `velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx` is a single ~6,600-line component implementing a 7-step flow: `upload`, `parsing`, `address`, `purchase`, `missing`, `confirm`, `review` ([wizardTypes.ts:22-49](velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L22-L49)).
- It is launched as a "full-screen-ish modal" by `NewTransactionModal.tsx`, which hosts the wizard's own split-panel layout and syncs an `?new=1` URL parameter ([NewTransactionModal.tsx:4,44-56,147-148](velvet-elves-frontend/src/components/active-transactions/NewTransactionModal.tsx#L44-L56)).
- It already supports **manual mode** (`set_manual_mode` reducer action), a per-field **AI-filled** marker, per-field **confidence** (`aiConfidences`), a per-field **chronology rank** (`aiSourceRanks`) so newer contract documents win over older ones, and **reviewed-field** tracking ([NewTransactionWizard.tsx:1315-1396](velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L1315-L1396); [wizardTypes.ts:177-212](velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L177-L212)).
- Extraction values arrive as `FieldExtraction` objects `{ value, confidence, source }`, where `source` is a free-form string. The reducer unwraps them in `apply_extraction` ([NewTransactionWizard.tsx:1447-1496](velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L1447-L1496)).
- All wizard state lives in React `useReducer` memory. There is no resumable server-side wizard record.

### 2.2 The AI / OCR pipeline that exists today

- The parse contract for the UI is `ParseDocumentResponse { extracted: dict, confidence, needs_review, transaction_resolution }` ([schemas/ai.py:27-31](velvet-elves-backend/app/schemas/ai.py#L27-L31)).
- The LLM extraction prompt **already requires a `sources` map** keyed by dotted field path, where each value is `"page N: short verbatim snippet of source text"`, and instructs the model to include the page and a short verbatim snippet for any field ([prompts.py:67-81](velvet-elves-backend/app/services/providers/prompts.py#L67-L81)). This is the single most important asset for source-cited review, and it exists right now.
- OCR is Amazon Textract. The raw Textract response carries normalized geometry (`Geometry.BoundingBox` with Top/Left/Width/Height, values 0..1) for LINE and WORD blocks, plus page numbers on QUERY answers and SIGNATURE detections ([textract_service.py:569-584,587-610,676-684](velvet-elves-backend/app/services/textract_service.py#L569-L584)).
- However, `format_textract_result` flattens everything into a text package before the LLM sees it. Page numbers and OCR confidence survive; bounding-box coordinates do not ([textract_service.py:476-566](velvet-elves-backend/app/services/textract_service.py#L476-L566)).
- The `Document` domain model persists `ai_extracted_data`, `ai_confidence`, `metadata_json`, `is_signed`, `signature_status`, `esign_envelope_id`, `acceptance_status`, and version lineage. It has **no column for raw OCR blocks or page geometry** ([document.py:66-84](velvet-elves-backend/app/models/document.py#L66-L84)).
- Parse jobs run via FastAPI `BackgroundTasks`, and their status is **persisted on the document** (`_set_parse_job_state(...)` sets `document_status="processing"`, `_mark_parse_job_failed` writes to Supabase, `_document_parse_job(doc)` reads it back) ([ai.py:647-698](velvet-elves-backend/app/api/v1/ai.py#L647-L698)). So the coarse job state already survives a refresh; what is missing is granular per-stage events.
- Textract supports only `application/pdf`, `image/jpeg`, `image/png`, `image/tiff` ([textract_service.py:49-55](velvet-elves-backend/app/services/textract_service.py#L49-L55)). The wizard's own upload validation matches this set exactly ([NewTransactionWizard.tsx:117-131](velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L117-L131)).

### 2.3 Cross-document resolution that exists today

- `resolve_transaction_documents` already computes, per field, the **controlling value across all parsed documents**, with `has_conflict`, superseded correction ids, the controlling document, acceptance status, and human-readable resolution notes such as "Conflicting values across documents were resolved to this one" ([contract_resolution.py:187-291,614-766](velvet-elves-backend/app/services/contract_resolution.py#L614-L766)). This output is returned to the wizard as `transaction_resolution`.
- The packet endpoints exist: `POST /api/v1/ai/parse-document-packet`, its status poll, and `POST /api/v1/ai/resolve-documents` ([useWizardApi.ts:153-211](velvet-elves-frontend/src/hooks/useWizardApi.ts#L153-L211)).

### 2.4 Task planning that exists today

- `POST /api/v1/transactions/preview-tasks` runs the same server-side planner as commit and returns `PreviewTaskItem[]` with `due_basis`, `depends_on`, `milestone_label`, `automation_level`, and `warnings`, plus a summary ([useWizardApi.ts:422-463](velvet-elves-frontend/src/hooks/useWizardApi.ts#L422-L463)).
- `POST /api/v1/transactions/{id}/tasks/generate` accepts `excluded_template_ids`, `overrides`, `added_tasks`, and `exclusion_reasons` ([useWizardApi.ts:365-391](velvet-elves-frontend/src/hooks/useWizardApi.ts#L365-L391)).
- `POST /api/v1/transactions/preview-tasks/ai-suggestions` returns optional supplemental tasks for explicit user approval ([useWizardApi.ts:410-420](velvet-elves-frontend/src/hooks/useWizardApi.ts#L410-L420)).
- The existing `ReviewTasksStep.tsx` already implements review-before-create with exclusions, overrides, and AI-added tasks. This is reused wholesale.

### 2.5 Routing, roles, and status that exist today

- There is no `/transactions/new` route. `ROUTES.TRANSACTION_DETAIL = (id) => /transactions/${id}` and the dynamic route `/transactions/:transactionId` renders at `App.tsx:498`. The standalone transactions list page was removed in favor of the workspace ([App.tsx:304,498](velvet-elves-frontend/src/App.tsx#L498); [constants.ts:96,105](velvet-elves-frontend/src/utils/constants.ts#L96)).
- `INTERNAL_ROLES = ['Agent','TransactionCoordinator','TeamLead','Admin']`; `INTERNAL_AND_ATTORNEY` adds `'Attorney'` ([App.tsx:124-125](velvet-elves-frontend/src/App.tsx#L124-L125)).
- `RoleRoute` takes `allowedRoles: UserRole[]` ([RoleRoute.tsx:8,19,25](velvet-elves-frontend/src/components/RoleRoute.tsx#L19)).
- `Incomplete` is a real transaction status (yellow) ([constants.ts:24-28](velvet-elves-frontend/src/utils/constants.ts#L24-L28)).

### 2.6 The proven source-rail UI that exists today

`AiEmailReviewPage.tsx` is the design and interaction template to reuse: a confidence taxonomy (`high`/`medium`/`low`/`unknown`), confidence bars and dots, a `HighlightedBody` that wraps AI-flagged assumption phrases in `<mark>`, a `SourceDataPanel`, a `ConfidenceMeter`, and an honest empty state ("No source data was cited for this draft") ([AiEmailReviewPage.tsx:60-83,144-258,423-431](velvet-elves-frontend/src/pages/AiEmailReviewPage.tsx#L60-L83)). The document workspace extends this exact language from "highlight a phrase in an email body" to "highlight a region in a contract page."

### 2.7 Visual tokens that exist today

From `STYLE_GUIDE.md`: champagne `ve-orange (#E26812)` is the single accent reserved for AI-touched fields and primary CTAs ("don't waste it on decoration"); neutrals are `ve-surface (#FFFFFF)` and `ve-surface-2 (#F8F8F6)`; AI surfaces use `ve-ai-bg`/`ve-ai-border`; confidence colors are green >= 80, amber >= 50, rose otherwise; serif (Lora) is for hero titles and prices with `tabular-nums`; required-but-empty and AI-filled fields use a champagne dot plus a soft input wash ([STYLE_GUIDE.md:22-23,41-57,77-93,107-135,408,444-451,739-741](velvet-elves-data/STYLE_GUIDE.md)).

---

## 3. Corrections to the Codex draft (so we do not build on false assumptions)

The Codex draft is largely sound and several of its observations are reused. These specific claims are wrong or misleading and are corrected here, because building on them would reintroduce the broken-workflow problem.

1. **File types.** Codex says the backend upload and AI parsing support GIF, DOC, DOCX, WEBP, TXT in addition to PDF/JPEG/PNG/TIFF, and treats this as a frontend validation gap to "fix" by widening accepted types. In reality Textract supports only PDF/JPEG/PNG/TIFF ([textract_service.py:49-55](velvet-elves-backend/app/services/textract_service.py#L49-L55)), and the wizard validation already matches that set. **Correct policy:** do not advertise a file type the OCR-plus-evidence pipeline cannot serve. If DOC/DOCX/TXT support is wanted, it requires an explicit server-side conversion step (document -> PDF) before Textract, and GIF/WEBP would need normalization to PNG. Treat that conversion as a scoped, optional later phase, not a day-one "widen the allowlist" change.

2. **Evidence is not greenfield.** Codex frames structured citations as something to be added from scratch and leans on a future `ai_field_evidence` table as a prerequisite. In fact the LLM already returns a `sources` map of `field_path -> "page N: snippet"` ([prompts.py:67-81](velvet-elves-backend/app/services/providers/prompts.py#L67-L81)). **Correct sequencing:** ship page-plus-snippet evidence first using existing output, then add bounding-box precision as an enhancement.

3. **Progress is not starting from zero durability.** Codex implies progress is only in-memory React state today. The coarse parse job is already persisted on the document and survives refresh ([ai.py:679-698](velvet-elves-backend/app/api/v1/ai.py#L679-L698)). **Correct framing:** the gap is granularity (one job vs. named sub-stages), not durability of the job itself.

4. **Conflict resolution already exists.** Codex's "explicit document-control resolver" reads as new work. The resolver already computes controlling value, `has_conflict`, superseded values, and notes ([contract_resolution.py:614-766](velvet-elves-backend/app/services/contract_resolution.py#L614-L766)). **Correct framing:** the conflict UI binds to existing `transaction_resolution` output; no new resolution logic is required for v1.

5. **Table sprawl risk.** Codex proposes six new tables up front (`wizard_runs`, `wizard_run_documents`, `wizard_progress_events`, `wizard_extracted_fields`, `ai_field_evidence`, `document_ocr_pages`, plus `wizard_task_reviews`). That is a large surface to land before any tester sees value, and it is the kind of over-build that has historically slipped. **Correct sequencing:** Phase 1 introduces zero new tables; later phases add the minimum needed, in the order the UI actually needs them (Section 9).

These corrections do not reduce ambition. They make the ambition shippable in an order where each phase is independently testable in the UI by a non-developer.

---

## 3A. Workflow and logic review (second source pass)

A second pass over the implemented source and the requirements/workflow docs found flaws in V2 itself. Each is corrected here and reflected in the relevant body sections. These are the workflow/logic errors that would otherwise have re-created the "frontend flow dead-ends" problem.

**F1 - Routing instruction was imprecise (corrected in Section 4).** V2 said to register `/transactions/new` "before `/transactions/:transactionId`." In React Router v6, match ranking already puts a static segment above a dynamic one regardless of order, proven by the existing literal aliases `/transactions/{pending,closed,all,active}` ([App.tsx:482-499](velvet-elves-frontend/src/App.tsx#L482-L499)). The error was framing ordering as the safeguard. The real control is layout-group membership: the route must live in a `ProtectedRoute` group that does not use `AppLayout` (the onboarding / client-workspace standalone pattern at [App.tsx:272-280,336](velvet-elves-frontend/src/App.tsx#L272-L280)). This also confirms alignment with the documented spec, which already calls this surface a "Standalone wizard (minimal shell - logo + step indicator only, no sidebar)" under Cross-Cutting Workflow A ([FRONTEND_UI_WORKFLOW_LOGIC.md:1506-1515](velvet-elves-data/FRONTEND_UI_WORKFLOW_LOGIC.md#L1506-L1515)).

**F2 - Evidence had no document attribution in multi-document mode (corrected in Section 7.1).** The headline "click a value, jump to the source document, highlight it" silently assumed the document was known. The `sources` map is a flat `backend_field_path -> "page N: snippet"` with no document id ([parsing.py:237-367](velvet-elves-backend/app/services/providers/parsing.py#L237-L367)), and the wizard parses multiple files as one packet, so page "N" is ambiguous across documents. UAT 2 (counteroffer) would dead-end here. Fix: use `transaction_resolution.source_document_id` for resolver-covered fields, snippet-search per-document OCR text otherwise, and durably extend the schema to emit a document id per source.

**F3 - Evidence highlighting was wrongly split into "native-text PDF vs scanned" (corrected in Sections 1.1, 7.1, 14).** V2 proposed highlighting native-text PDFs via the PDF text layer and treating scanned documents as a lesser case. That contradicts the established pipeline, in which every page - text or image - is OCR'd by Textract and the PDF text layer is deliberately not trusted (§1.1). The correct, simpler design: highlighting is driven by Textract OCR output uniformly for all documents. Per-page OCR text and geometry already exist server-side; the only gap is exposing them to the client. Phase 1 exposes the per-page OCR text already produced at parse time, so text-match highlight plus page jump work for **every** document; Phase 4 adds geometry for pixel-accurate boxes. Nothing here alters what OCR text is sent to the LLM.

**F4 - Field-path mismatch is a prerequisite, not a nicety (corrected in Section 11).** The `sources` keys are backend namespaces (`property.*`, `transaction.*`, `timeline.*`, `parties.*`, `detection.*`), the UI uses `address.*`/`purchase.*`, and the create payload uses flat keys. The existing `WIZARD_FLAG_TARGETS` does not key on the backend namespaces, so without a deliberate map the click-to-evidence feature cannot locate a row or its citation at all. Elevated from "add" to "blocking prerequisite."

**F5 - Two-pass double-check was treated as optional; §3.4 makes it mandatory (corrected in Section 7.3).** Requirements §3.4 requires Pass 1 (interpret) + Pass 2 (re-read with a different prompt template), agreement on date/party/signature-status/requested-deliverable before proceeding, human routing on disagreement, and halt-and-request-better-copy on blurry/crooked/missing-page scans ([requirements.txt:552-560](velvet-elves-data/requirements.txt#L552-L560)). The implemented parser is single-pass. V2 named the wrong critical-field set and omitted the halt-on-bad-input behavior. Now aligned to §3.4.

**F6 - "No rescan on edit" rule was missing (added to Section 5.2).** Requirements §3.8 mandates "one-time validation (no rescan on edit)" ([requirements.txt:586-594](velvet-elves-data/requirements.txt#L586-L594)). V2's interaction model allowed editing but never forbade re-parsing on edit. Added as an explicit rule.

**F7 - Signature decisions were under-specified vs §3.9 (corrected in Section 13).** §3.9 requires gating the e-sign offer on a connected provider, and on completion replacing the original with the executed copy (original to version history) and distributing to parties ([requirements.txt:596-602](velvet-elves-data/requirements.txt#L596-L602)). Now bound to the real DocuSign endpoints, including the `GET /esign/provider-status` gate ([esign.py:6-12,207,228-340](velvet-elves-backend/app/api/v1/esign.py#L207)).

**F8 - Post-create redirect convention was unspecified (corrected in Section 13).** The codebase redirects to `/transactions?highlight={id}` after create ([FRONTEND_UI_WORKFLOW_LOGIC.md:461](velvet-elves-data/FRONTEND_UI_WORKFLOW_LOGIC.md#L461)). Specified so the tester lands on the new deal.

**F9 - Manual no-document commit is feasible (verified, no change).** `TransactionCreateRequest` requires only `address` and `use_case`; documents are linked separately and `status` is settable ([transaction.py:15-83](velvet-elves-backend/app/schemas/transaction.py#L15-L83)). So manual mode and the Incomplete-shell lifecycle are both supported by the existing create endpoint, which honors `status=payload.status` and enforces owner authorization server-side ([transactions.py:170-256](velvet-elves-backend/app/api/v1/transactions.py#L170-L256)). V2 was correct here; now it is cited rather than asserted.

**F10 - Conflict data needs an explicit resolve call pre-transaction (corrected in Section 7.1).** V2 implied `transaction_resolution` is simply present. The resolver runs over document ids; pre-transaction the workspace must call `POST /ai/resolve-documents` on the uploaded ids to obtain controlling/superseded values and `source_document_id`, rather than assuming it is embedded in the packet parse response.

**F11 - Two competing "controlling value" paths exist (new decision flagged).** The backend resolver computes controlling values, while the frontend wizard independently re-ranks documents by chronology (`aiSourceRanks`, `getContractExtractionRank`). Running both risks divergent answers for counteroffers. Decision required: make the server resolver the single source of truth for controlling values (per §3.6) and have the UI display it, retiring the ad-hoc client ranker over time. Added to Section 17 open decisions.

---

## 4. Product decision: the workspace and its lifecycle

- **Route:** add `ROUTES.TRANSACTION_NEW = '/transactions/new'`. The mechanics that matter (corrected in Section 3A, F1): React Router v6 ranks a static segment (`/transactions/new`) above a dynamic one (`/transactions/:transactionId`) regardless of declaration order, so `new` is never parsed as a transaction id - the existing literal aliases `/transactions/{pending,closed,all,active}` already prove this ([App.tsx:482-499](velvet-elves-frontend/src/App.tsx#L482-L499)). The real requirement is **layout-group membership**: register the route in a `ProtectedRoute` group that does **not** use `AppLayout`, mirroring the existing standalone groups (onboarding and the client workspace at [App.tsx:272-280](velvet-elves-frontend/src/App.tsx#L272-L280)). Do **not** add it as a sibling of `/transactions/pending` inside the `AppLayout` group ([App.tsx:336](velvet-elves-frontend/src/App.tsx#L336)), or it inherits the sidebar.
- **Component:** `WizardWorkspacePage` rendering a full-screen shell with its own minimal header and no app chrome.
- **Access:** `RoleRoute allowedRoles={INTERNAL_ROLES}` using the exact existing values `Agent`, `TransactionCoordinator`, `TeamLead`, `Admin`. Attorneys keep their separate packet/matter intake. Client, FSBO, and Vendor portal roles cannot reach it.
- **Entry points become navigations, not modals:** every existing "New Transaction" / `?new=1` / quick-create "Full Wizard" / dashboard drag-drop entry routes to `/transactions/new`. Drag-drop entry uploads first, then routes with the resulting document ids (via run id once the run model lands, or via query params in Phase 1).
- **The modal becomes a thin redirect** during migration, then is removed once parity is proven. The wizard's internal step logic is preserved and re-hosted in the page; it is not rewritten from scratch in Phase 1.
- **Lifecycle (grounded in the real `Incomplete` status):**
  1. Phase 1: state lives in the page (as today) plus the already-durable per-document parse job. Exiting mid-flow is handled by a branded confirm dialog.
  2. Phase 2 onward: a resumable `wizard_run` is created on entry; once enough data exists (address plus representation) or the user explicitly saves a draft, a transaction shell with `status = Incomplete` is created; on final approval the shell flips to `Active` (or a new `Active` transaction is created if no shell exists). Tasks are generated only after `Active` and after the user approves the task preview.
- **Exit behavior:** explicit "Save and exit" and "Discard draft" using the project's branded confirm dialog. Never `window.confirm`, `window.alert`, or `window.prompt`.

---

## 5. Target user experience

### 5.1 Three-pane workspace

**Left rail (process and navigation):**
- Live AI stage timeline (Section 8), each stage showing status and a one-line human detail.
- Uploaded document list with per-document OCR/parse status and page count.
- Section navigator: Upload or Manual Start, Review Facts, Resolve Conflicts, Missing Info, Signatures, Task Preview, Create.
- Confidence legend and autosave/draft-state indicator (`Unsaved`, `Saved draft`, `Incomplete transaction`, `Ready to create`).

**Center (the human's decisions):** extracted fields grouped by real-estate workflow (Property; Parties and contacts; Price and financing; Key dates; Contingencies including HOA/inspection/warranty/occupancy; Title and closing; Signatures and document control; Ownership and assignment; Missing or public-source). Each field row shows: human label, extracted value, confidence badge, a source chip (document + page), a conflict/missing indicator, and Confirm / Edit / Reject controls.

**Right (the proof):** a persistent PDF/image viewer with document tabs, page thumbnails, OCR text search, and zoom. Clicking a field jumps the viewer to the cited page and highlights the original text or region. Clicking a highlight selects the matching field in the center. When coordinates are unavailable, the viewer jumps to the page and shows a labeled text snippet with an honest "No exact location match" state. This is the email page's `HighlightedBody`/`SourceDataPanel` pattern, promoted to documents.

### 5.2 Mouse-first, minimal-typing interaction model (the convenience mandate)

This is a first-class requirement, not a nicety. Concrete rules:

- **Confirm is one click.** Every field row has a primary Confirm button. The default action for a high-confidence field is to accept it.
- **"Next unresolved"** advances focus to the next field needing attention; supports keyboard Enter to confirm and arrow keys to move. A tester can clear an entire deal with Enter/Enter/Enter.
- **"Confirm all on this page"** and **"Confirm all high-confidence with evidence"** batch actions, each gated so they only act on fields that have evidence (or an accepted non-document source) and no conflict, and each opens a one-screen summary before applying. No silent bulk accept.
- **Editing is structured, not free text, wherever possible:** dates use a date picker, money uses a formatted numeric input, yes/no contingencies use segmented toggles, mortgage type and representation use selects, parties use the existing party editor and Google Places autocomplete that the wizard already has.
- **No rescan on edit (requirements §3.8).** Editing a field updates its value and marks it `user_corrected`; it must never re-run OCR or AI extraction on the document. Re-parsing is triggered only by adding or removing a document, never by correcting a value. The current wizard already behaves this way (edits just set reducer state), so this is a rule to preserve, not introduce ([requirements.txt:586-594](velvet-elves-data/requirements.txt#L586-L594)).
- **Accept-from-evidence:** when the viewer is showing a Textract QUERY answer or a selected snippet, a single "Use this value" button writes it into the field.
- No production control is decorative. Every button maps to a real endpoint, a real state transition, or an explicitly labeled future-phase placeholder that is hidden until wired.

### 5.3 Manual no-document path

The requirements allow "Skip - enter details manually," and the wizard already supports manual mode. In the workspace, manual mode keeps the same three-pane shell; the right viewer shows "No source document for this field" rather than a broken empty panel; manual fields are reviewed and audited but never require document evidence; and commit is not blocked for lack of an upload when manual mode was chosen. The final summary distinguishes `AI from document`, `manual entry`, `public source`, and `user corrected`.

### 5.4 Header and responsiveness

Minimal header: Velvet Elves wordmark, draft title, autosave state, secure-processing note, Save and exit, Discard. No app navigation. Tablet collapses to two panes with a toggleable evidence drawer; mobile keeps the center review primary and opens evidence as a bottom sheet via a "Source" button. Touch targets stay large enough for both mouse and finger.

---

## 6. ListedKit parity-plus matrix (with feasibility verdict)

| Capability | ListedKit benchmark | Velvet Elves target | Verdict vs. current code |
|---|---|---|---|
| Contract upload | Upload contract/packet | Multi-file, drag-drop, PDF split, classify, packet parse | **Exists**; re-host in page |
| Field extraction | Dates, parties, contingencies, deal facts | Same plus signatures, chronology, representation side, HOA/inspection/warranty/occupancy, title/closing mode | **Exists** in extraction + wizard |
| Progress transparency | Show what the AI is doing | Persisted, backend-driven stage events with per-document/per-page detail | **Extend**: durable coarse job exists; add named sub-stages |
| Review extracted data | User reviews before use | Source-cited review for every critical field, right-side viewer, click-to-highlight | **Extend**: `sources` page+snippet exists; add viewer + matcher |
| Counteroffer/addendum | Read counteroffers, update timeline | Show winning + superseded value, each attributed to its source | **Exists** in `transaction_resolution`; add UI |
| Timeline/checklist | Build task checklist | Preview tasks before create with reasons, edits, exclusions; same planner as commit | **Exists** (`preview-tasks` + `ReviewTasksStep`) |
| Human control | Review and adjust | Required confirmation of baseline; all edits audited | **Exists** partially; tighten gating + audit |
| Inbox/email intelligence | AI reads inbox, drafts replies | Reuse AI email source-rail safeguards; later link wizard facts to deal inbox | **Reuse** `AiEmailReviewPage` patterns |
| Differentiation | AI TC simplicity | Source-cited evidence + audit, multi-role owner/FSBO guardrails, two-pass agreement check, conflict transparency, white-label | **Superior** by combining existing assets |

**Where this surpasses ListedKit:** (a) every critical value is provably traceable to a page and region with an audit trail, not just "the AI read it"; (b) cross-document conflicts are shown with both values attributed, not silently merged; (c) a second-pass agreement check on critical fields prevents high overall confidence from hiding a field-level disagreement; (d) the same planner powers both preview and commit, so the checklist the tester approves is exactly what gets created; (e) multi-role ownership/FSBO guardrails and the unified AI source-rail design language extend beyond a single-role TC tool.

---

## 7. The evidence system (the heart of the redesign)

This is the feature the user cares most about. It is designed in two tiers so it ships early and improves over time.

### 7.1 Tier 1 (Phase 1 to 4): page + snippet evidence, no parsing-pipeline change

The extraction already attaches each field's snippet as the `source` string on its `FieldExtraction` (`_fe(..., sources=sources)` -> `source=(sources or {}).get(field_path)`, [parsing.py:39-69,252-367](velvet-elves-backend/app/services/providers/parsing.py#L39-L69)). The value is a flat string like `"page N: snippet"`, keyed by **backend** path. The workspace uses this, with two corrections from the second source pass (Section 3A, F2 and F3):

1. The center field row carries its `field_path`, page number, and snippet, read from each field's `source` string. **The backend keys are `property.*`, `transaction.*`, `timeline.*`, `parties.*`, `detection.*`, not the UI's `address.*`/`purchase.*` keys**, so the canonical field-path map (Section 11, F4) is a hard prerequisite, not a convenience.
2. Clicking the row tells the right viewer to render the cited document at page N.
3. **Document attribution is not free in multi-document mode.** The `sources` snippet contains a page number but no document id (the packet prompt asks only for "page number + snippet"), and the wizard parses via `parse-document-packet`, so page "N" is ambiguous across documents. Resolution order: (a) for fields the resolver covers, use `transaction_resolution.source_document_id` from a `POST /ai/resolve-documents` call on the uploaded document ids (works pre-transaction, Section 3A F10); (b) otherwise locate the document by matching the snippet against per-document OCR text; (c) the durable fix is to extend the extraction schema to emit `document_id` per source, since the packet already labels each document with `id=`/`file_name=`.
4. **Highlighting is driven by Textract OCR, uniformly for every document.** Because every page is OCR'd by Textract and the PDF text layer is not trusted (§1.1), per-page OCR text and geometry exist server-side for all documents - there is no "native-text vs scanned" distinction in how the viewer highlights. The only gap is that this OCR output is not yet returned to the client (the parse response carries `_ocr` metadata, not the OCR text). Exposing it is a read path, not a parsing change, and must return the **full** per-page OCR text, not a reduced copy. Phase 1 exposes the per-page OCR text to support text-match highlight plus page jump for every document; Phase 4 (Tier 2) adds Textract geometry for pixel-accurate boxes. Neither changes what is sent to the LLM.
5. If no location is resolved, the viewer still jumps to page N and shows the snippet in a labeled "cited text" panel with an honest "approximate location" state, mirroring the email page's behavior when an assumption phrase is not found verbatim.

This tier changes nothing in the parsing pipeline. It exposes the Textract OCR text already produced and consumes the document download/page endpoints that already exist, delivering page jump and Textract-OCR text-match highlight for every document, with an explicit page-only fallback only when a citation's source document cannot yet be resolved (F2/F10).

### 7.2 Tier 2 (Phase 4 to 5): pixel-accurate bounding-box highlight

To draw a crisp box over the exact region (not just a text match), persist Textract geometry and match snippet to blocks:

- **Persist OCR geometry.** Textract raw blocks already contain normalized bounding boxes per LINE/WORD ([textract_service.py:569-584](velvet-elves-backend/app/services/textract_service.py#L569-L584)). Store, per document and page: page width/height/rotation, and the LINE/WORD blocks (id, text, page, normalized box). Raw block payloads can be large, so store them in object storage with a DB pointer, or in a dedicated `document_ocr_pages` table if payloads are modest. Decision in Section 9.
- **Snippet -> box matching ladder**, with the match method recorded so reviewers can judge evidence quality:
  1. **Textract QUERY answer**: if the field maps to one of the configured queries (`property_address`, `purchase_price`, `closing_date`, etc. at [textract_service.py:58-73](velvet-elves-backend/app/services/textract_service.py#L58-L73)), the QUERY_RESULT block already has page + geometry. Strongest match.
  2. **Exact line match**: find the LINE block whose text contains the snippet; use its box.
  3. **Fuzzy word-span match**: tokenize the snippet, find the contiguous WORD-block run with the best normalized match, union their boxes.
  4. **Page-only**: jump to the page, no box (Tier 1 behavior).
  5. **Text-only / manual / public-source**: no document box by design; show the appropriate panel.
- **Coordinate reconciliation.** Textract boxes are normalized 0..1 against the page. A PDF.js/react-pdf page viewport and a rendered image both expose page pixel dimensions, so a normalized box maps to an overlay rectangle by simple multiplication. The critical correctness rule: **always overlay against the artifact the user is actually viewing.** If a DOC/DOCX was converted to PDF, the boxes must reference the converted PDF the viewer renders, not an intermediate text stream, or highlights will drift.

### 7.3 Two-pass agreement check on critical fields (required by §3.4, currently missing)

This is not optional polish. Requirements §3.4 "Double-Check Mechanism for AI Parsing" mandates a two-pass system ([requirements.txt:552-560](velvet-elves-data/requirements.txt#L552-L560)), and the implemented packet parser is single-pass (one `extraction` result, no verification pass - [document_packet_parsing.py:478-488](velvet-elves-backend/app/services/document_packet_parsing.py#L478-L488)). So this is a requirement-mandated gap, corrected to match §3.4 exactly:

- **Pass 1:** read the document(s) and produce the interpretation (the existing parser).
- **Pass 2:** re-read using a **different prompt strategy / extraction template**, not just a re-run of the same prompt.
- **Proceed only if both passes agree with high confidence on the key fields named in §3.4: date, party, signature status, and requested deliverable** (the wizard's critical set adds property address and purchase price).
- **On disagreement:** hold the field `pending`, surface the conflict, and request clarification or route to human review. High overall confidence never suppresses a field-level disagreement.
- **On bad input** (blurry, crooked scan, missing pages): halt and request a better copy or route to human review, rather than emitting low-quality values. The pipeline already detects these conditions (`_quality`, `missing_pages_detected`, Textract `PARTIAL_SUCCESS` review reasons at [document_packet_parsing.py:441-454](velvet-elves-backend/app/services/document_packet_parsing.py#L441-L454)); §3.4 requires acting on them, not just logging them.

### 7.4 Honest evidence states

The viewer must never imply precision it does not have. Every field's evidence resolves to exactly one labeled state: `box` (Tier 2 match), `page+snippet` (Tier 1), `page-only`, `text-only` (non-renderable source), `manual`, `public-source`, or `none`. The label is visible. This honesty is what earns professional trust and is itself a differentiator over a black-box "the AI read it."

---

## 8. Progress transparency (grounded in the real job model)

The coarse parse job is already durable on the document. The redesign decomposes the real pipeline boundaries into named, user-facing stages and persists them so they survive refresh and resume.

Stages (each emits a row with status `queued|running|succeeded|warning|failed|skipped`, a human label, and an optional per-document/per-page detail):

1. Uploading files
2. Preparing secure copies
3. Checking file quality (Textract `_quality` already exists in `extracted`)
4. Reading visible text (OCR; detail like "Reading page 4 of Purchase Agreement.pdf")
5. Detecting document types
6. Checking signatures and missing pages (Textract SIGNATURE blocks + `missing_pages_detected` from the prompt)
7. Extracting property and parties
8. Extracting price, financing, deposits
9. Extracting dates and contingency windows
10. Resolving counteroffers and amendments (the existing resolver; detail like "A counteroffer changes the closing date")
11. Comparing conflicting values (surface `has_conflict`)
12. Two-pass agreement check on critical fields
13. Checking confidence and missing fields
14. Mapping source locations (evidence matcher, Tier 2)
15. Preparing the review workspace

Task preview is deliberately **not** part of document processing; it runs only after required baseline fields are confirmed, manually entered, or marked not applicable.

Honesty note: today this is functionally one background job. Phase 3 instruments the boundaries that already exist in code (per-document parse, packet resolve, quality, signatures) as real events; it does not fabricate sub-steps the pipeline does not actually perform. Transport is polling first (the status endpoints already poll); server-sent events can be added later without changing the data model.

---

## 9. Data model (reuse-first, phased)

**Phase 1: zero new tables.** Reuse `documents.ai_extracted_data`, `documents.metadata_json`, the durable parse-job state, `transaction_resolution`, and the `Incomplete` transaction status. Evidence is page+snippet from the existing `sources` map. Wizard state stays in the page as today.

**Phase 2: `wizard_runs` (+ `wizard_run_documents`).** A resumable session: `id`, `tenant_id`, `created_by`, `transaction_id` (nullable until commit), `status`, `current_step`, `mode` (`document_first`/`manual`/`mixed`), `represented_side`, `owner_user_id`, `draft_transaction_id`, timestamps, `metadata_json`. `wizard_run_documents` links documents with `display_order`, `document_role`, `page_count`, `original_mime_type`, `source_preview_status`, `evidence_capability`, and per-stage statuses. This is what makes drafts resumable and lets dashboard/drag-drop entry pass a run id instead of in-memory `File[]`.

**Phase 3: `wizard_progress_events`.** `wizard_run_id`, `sequence_number`, `stage_key`, `status`, `label`, `detail`, optional `document_id`/`field_path`, timestamps, `severity`, `metadata_json`.

**Phase 4 to 5: evidence storage.** `document_ocr_pages` (page geometry + LINE/WORD blocks or an object-storage pointer) and `ai_field_evidence` (`document_id`, `field_path`, `page_number`, `snippet`, `bounding_boxes_json`, `match_method`, confidences). Add a `wizard_extracted_fields` review table only if per-field review state (status, source_kind, reviewed_by/at, controlling doc, conflict group) cannot live cleanly on the run's `metadata_json`. Persist task-review choices (`wizard_task_reviews`: include/exclude/override/add, reason, rationale) so resume does not lose them; these feed the existing `tasks/generate` body, never duplicating created tasks.

The ordering principle: introduce a table only when a shipped, testable UI capability needs it.

---

## 10. API plan (orchestrate around existing endpoints)

Phase 1 uses the endpoints that exist: `documents/upload`, `documents/{id}` PATCH (link), `documents/{id}/pages`, `documents/{id}/split`, `documents/{id}/download`, `ai/parse-document-packet` (+ status), `ai/resolve-documents`, `ai/search-public-source`, `transactions` (create), `transactions/{id}/parties`, `transactions/preview-tasks`, `transactions/preview-tasks/ai-suggestions`, `transactions/{id}/tasks/generate`, plus the e-sign endpoints for signature decisions.

From Phase 2, add a `WizardRunService` and a `/api/v1/wizard-runs` surface that **wraps** (does not fork) the above:

- `POST /wizard-runs` create draft; `GET /wizard-runs/{id}` resume; `PATCH /wizard-runs/{id}` update side/owner/step/mode.
- `POST /wizard-runs/{id}/documents` attach/upload.
- `POST /wizard-runs/{id}/save-draft-transaction` create/update the `Incomplete` shell.
- `POST /wizard-runs/{id}/start-processing` orchestrate OCR/parse/resolve/evidence and emit events.
- `GET /wizard-runs/{id}/events?since_sequence=` progress (poll first; SSE later).
- `GET /wizard-runs/{id}/review-model` sections, fields, conflicts, missing items, evidence summaries, task-preview readiness.
- `PATCH /.../fields/{field_path}`, `POST /.../fields/{field_path}/confirm|reject`, `GET /.../fields/{field_path}/evidence`.
- `POST /wizard-runs/{id}/preview-tasks` (must call the same planner as `transactions/preview-tasks`).
- `POST /wizard-runs/{id}/commit` create/activate transaction, link documents, create parties, apply reviewed task decisions, generate tasks, queue approved e-sign actions, and audit AI plus human decisions atomically.

Evidence/download endpoints must authorize through the run/document relation and the same tenant/transaction rules as document download. Do not expose evidence merely because a caller knows a document id.

---

## 11. Frontend architecture

Components: `WizardWorkspacePage`, `WizardWorkspaceShell`, `WizardProgressRail`, `WizardDocumentList`, `WizardReviewPanel`, `WizardFieldSection`, `WizardFieldRow`, `WizardConflictResolver`, `WizardMissingInfoPanel`, `WizardTaskPreviewPanel` (wrapping the existing `ReviewTasksStep`), `WizardOwnerAssignmentPanel`, `WizardSignatureDecisionPanel`, `WizardEvidenceViewer`, `WizardPdfViewer`, `WizardImageViewer`, `EvidenceHighlightOverlay`, `WizardExitDialog`.

Hooks: `useWizardRun`, `useWizardRunEvents`, `useWizardReviewModel`, `useWizardFieldActions`, `useWizardEvidence`, `useWizardCommit`, `useWizardFieldPathMap`. Keep `useWizardApi` during migration; put run-specific calls in new hooks so the old modal code does not grow.

Reuse: `DocumentSplitDialog`; existing upload validation (kept to Textract-supported types unless conversion lands); `ReviewTasksStep` and the task-preview hooks; `SuggestImprovementButton` (extended with run id, field path, evidence id); the `AiEmailReviewPage` confidence/highlight/source-rail patterns; existing toasts, branded confirm dialog, and design tokens; the wizard's existing owner-assignment and FSBO-owner guard logic; the existing party merge/representation logic.

Add (and treat as a hard prerequisite for the evidence feature, not a convenience): a canonical **field-path map** across three distinct vocabularies that the code actually uses today:
- **Backend extraction / `sources` keys:** `property.address`, `transaction.purchase_price`, `timeline.closing_date`, `parties.buyers.0`, `detection.has_hoa` ([parsing.py:252-367](velvet-elves-backend/app/services/providers/parsing.py#L252-L367)).
- **Wizard UI keys:** `address.street`, `purchase.purchase_price`, `purchase.closing_date`, `parties.buyer`.
- **`TransactionCreateRequest` keys:** `address`, `purchase_price`, `closing_date` ([transaction.py:15-83](velvet-elves-backend/app/schemas/transaction.py#L15-L83)).

The existing `WIZARD_FLAG_TARGETS` ([NewTransactionWizard.tsx:765-1073](velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L765-L1073)) maps flag field names to UI rows but is **not** keyed on the backend `property.*`/`timeline.*`/`detection.*` namespaces, so it cannot by itself route a `sources` citation to a UI row. The map must be built from the backend namespaces outward. Without it, clicking an extracted value cannot find its row or its evidence at all. Also add a source-kind display adapter and a viewer adapter (PDF / image / converted / text-only).

PDF viewer library: PDF.js via react-pdf is the default unless a viewer is already bundled. It renders the page and exposes page viewport dimensions for the highlight overlay. The highlight is positioned from **Textract OCR output** (text match in Phase 1, geometry in Phase 4), not from the PDF's own text layer, consistent with the OCR-everything pipeline (§1.1). For images, `WizardImageViewer` overlays against the rendered image at its natural dimensions.

---

## 12. Visual design direction

Extend the Velvet Elves style; do not imitate ListedKit's look. Full-screen background `ve-surface-2`; compact near-white header with a bottom border; subdued brand-tinted left rail with small status chips; unframed grouped field sections in the center; a fixed right evidence surface with a toolbar and page canvas. Champagne (`ve-orange`) marks AI-touched fields and the primary CTA only, never decoration. AI-filled/required-empty fields use the champagne dot plus soft input wash. Confidence colors follow green/amber/rose. Prices and key numbers use serif with `tabular-nums`. Document highlights are a translucent amber fill with a crisp outline; the active field row gets a subtle left edge plus a pale wash. Lucide icons for toolbar and field actions. No robot mascots, neon AI glows, gradient blobs, or marketing hero copy. Honest empty states everywhere (no demo/sample data on real surfaces).

---

## 13. Commit rules and signature decisions

Commit is blocked until: required property and purchase fields are confirmed, manually entered, or marked not applicable; required parties are sufficient to create the transaction; controlling-value conflicts are resolved; missing referenced documents are acknowledged; the task preview has been generated from confirmed baseline data and approved; signature warnings are resolved, queued for e-sign, or explicitly acknowledged; and in document-first mode the source documents are linked (manual mode does not require an upload).

The commit screen summarizes: facts to be created, documents to be linked, parties to be created, tasks to be generated, public-source fields, manually edited fields, the owner/assignment result, whether commit activates an `Incomplete` shell or creates a new `Active` transaction, any e-sign actions to queue, and remaining warnings.

On success, redirect to the highlighted transaction using the existing convention (`/transactions/active?highlight={id}` / `/transactions?highlight={id}`), which onboarding and the current wizard already use, so the tester lands directly on the new deal rather than a generic list ([FRONTEND_UI_WORKFLOW_LOGIC.md:461](velvet-elves-data/FRONTEND_UI_WORKFLOW_LOGIC.md#L461)).

Signature decisions are specified by requirements §3.9 ([requirements.txt:596-602](velvet-elves-data/requirements.txt#L596-L602)) and are grounded in the existing DocuSign e-sign API ([esign.py:6-12,207,228-340](velvet-elves-backend/app/api/v1/esign.py#L6-L12)). The wizard does not prompt for e-sign at finalization today, so this is a deliberate addition aligned to §3.9:

- During processing, detect signature status and missing signatures (Textract SIGNATURE blocks plus `all_parties_signed` from extraction); show them as source-cited fields.
- **Gate the offer on a real provider check:** call `GET /esign/provider-status` ([esign.py:207](velvet-elves-backend/app/api/v1/esign.py#L207)). Only when a provider (DocuSign) is connected does the commit screen offer "Queue e-signature on finalization." When it is not connected, §3.9 requires informing the user and suggesting they connect (via the existing `ConnectEsignWizardModal`), not silently hiding the option.
- The commit-screen Signature Decisions section appears only when unsigned/needed documents exist, offering Queue e-sign after creation / Handle later / Mark not required with reason.
- Queued actions run after transaction creation and document linking via `POST /documents/{id}/esign` ([esign.py:228-340](velvet-elves-backend/app/api/v1/esign.py#L228-L340)). On envelope completion, §3.9's workflow applies and is already partially wired: replace the original with the executed copy (the original moves to version history) and distribute to identified parties, all audited.

---

## 14. Rollout phases (each independently testable in the UI)

- **Phase 0 - Design lock.** Approve this plan; confirm route name and roles; confirm the `wizard_run` + `Incomplete` shell policy; pick the PDF viewer; decide OCR-geometry storage (JSONB vs object storage); decide the DOC/DOCX conversion policy (in scope or deferred); define the critical-field set that requires evidence before bulk confirm.
- **Phase 1 - Full-screen shell, no parsing-pipeline change.** Add `/transactions/new` in a non-`AppLayout` `ProtectedRoute` group (F1); `ROUTES.TRANSACTION_NEW`; redirect existing CTAs; build the canonical field-path map (F4, prerequisite); re-host the existing wizard logic in the page; expose the full Textract per-page OCR text already produced at parse time; add the right-side viewer with **Tier 1 evidence**: page jump plus Textract-OCR text-match highlight for **every** document (text or scanned alike, since all pages are OCR'd - §1.1). Outcome a tester can see: upload any purchase agreement, click the purchase price, the viewer jumps to the cited page and highlights the cited text. Box-precise highlight arrives in Phase 4. Multi-document attribution uses `resolve-documents` (F10).
- **Phase 2 - Draft lifecycle + manual fallback.** Add `wizard_runs`(+documents) and save/resume; manual no-document mode; `Incomplete` shell creation; persist owner, reviewed fields, task-review choices; final `Active` transition.
- **Phase 3 - Real progress events.** Add `wizard_progress_events`; emit from upload/OCR/parse/resolve/signature boundaries; replace generic client phases; add retry/failure states.
- **Phase 4 - Evidence precision.** Persist OCR page geometry; implement the snippet->box matcher; add `ai_field_evidence`; upgrade the viewer to **Tier 2 bounding-box highlight** with the labeled fallback ladder.
- **Phase 5 - Review UX + conflicts.** Structured per-field confirm/edit/reject; conflict comparison from `transaction_resolution`; missing-info and public-source confirmation in-workspace; owner/assignment review; signature decisions; two-pass agreement check.
- **Phase 6 - Commit, audit, tasks.** Gate commit on confirmed baseline; preview tasks via the shared planner; edit/exclude before create; atomic commit of transaction + parties + documents + tasks + audit; queue approved e-sign; post-create success with links.
- **Phase 7 - Beyond ListedKit.** Deal-inbox linkage to wizard facts; post-commit "today" command center; calendar publication of confirmed deadlines; attorney/FSBO/vendor handoffs from the same baseline; an admin AI-quality dashboard (evidence-match rate, correction rate, confidence drift, provider comparison); a state-rule library combining confirmed dates with team templates.

---

## 15. Non-developer UAT (mouse-only, scripted, no dead ends)

These are written so a real-estate tester can run them with a mouse and confirm on-screen outcomes, with no developer tools. Each step names what the tester should see, and every action maps to a real endpoint/state so the flow never strands them.

**UAT 1 - Clean purchase agreement.** Open New Transaction; pick representation; drag in one purchase-agreement PDF; watch the stage timeline progress with readable details; review Property/Price/Closing/Parties; click Purchase Price and confirm the right viewer jumps to the correct page and highlights the original price; click Confirm on each high-confidence field (or "Confirm all on this page"); review the generated task checklist; click Create; verify the new transaction, its documents, history, and tasks open from the UI.

**UAT 2 - Purchase agreement + counteroffer.** Upload both; watch classification and chronology events; confirm the workspace flags the changed closing date; click Closing Date and confirm both the original value and the counteroffer value are shown, each attributed to its document; pick the controlling value if prompted; confirm generated deadlines use the controlling value.

**UAT 3 - Low-confidence scan.** Upload a blurry/partial scan; confirm the timeline shows quality warnings; confirm low-confidence fields are not auto-accepted; open evidence and confirm the page+snippet (or approximate-location) fallback appears honestly; correct a value with the date/number controls; confirm the summary later labels it "user corrected."

**UAT 4 - Missing info + public search.** Upload documents missing a county/HOA field; trigger public-source search from the Missing Info panel; confirm the UI shows what sources were searched; confirm results are labeled "public source"; accept or reject; confirm the commit summary separates contract data from public-source data.

**UAT 5 - Resume.** Start a run, upload, let processing finish, exit (branded dialog); confirm the run is saved (as a resumable run, or an `Incomplete` transaction once enough data exists); return from the dashboard or `/transactions/new` and resume; confirm uploaded documents, progress, reviewed fields, owner selection, task-review choices, and the current step all persist.

**UAT 6 - Roles.** Agent can create/resume own runs; TC can create/assign within tenant rules; Team Lead can view team runs where permitted; Admin can inspect for support; Attorney is routed to packet intake, not this wizard; Client/FSBO/Vendor cannot reach it; an attempt to open evidence for an unrelated document returns a friendly UI error, not leaked data.

**UAT 7 - Manual, no document.** Open New Transaction; choose Enter details manually; fill property/representation/price/dates/parties with pickers and toggles; confirm the right panel clearly says there is no source document; review the task preview; Create; confirm no upload was required and manual fields are labeled/audited as manual.

**UAT 8 - Signatures.** Upload a packet with a missing signature; confirm the timeline flags signature review; click the signature warning and confirm its source evidence opens; on commit, choose Queue e-sign / Handle later / Mark not required (with reason); confirm the transaction is created and the chosen decision appears in history/audit.

**UAT 9 - Full-screen integrity.** Confirm the wizard has no app sidebar, no top nav, and no global AI chat overlay; confirm Save and exit / Discard use the branded dialog; confirm the layout holds on a tablet width with the evidence drawer toggle.

---

## 16. Automated testing

**Backend:** wizard-run create/resume/status/permissions; `Incomplete` shell create/resume/activate; manual commit without documents; owner-assignment rules (Agent/TC/TeamLead/Admin and FSBO-owned); progress-event ordering and idempotency; parser emits structured citations; evidence matcher maps snippet to Textract boxes; QUERY-answer, exact-line, fuzzy-span, and page-only fallbacks; two-pass disagreement holds the field; conflict resolution for counteroffer/amendment/supersedes-all/broad-reinstatement; commit rejects unconfirmed required fields; wizard preview-tasks reuses the same planner as `transactions/preview-tasks`; commit writes transaction+parties+documents+tasks+audit atomically; signature detection produces a decision and optional e-sign action; evidence endpoints enforce tenant/relation authorization.

**Frontend unit:** `/transactions/new` uses `RoleRoute allowedRoles={INTERNAL_ROLES}` and is not captured by `/transactions/:transactionId`; progress rail renders all event states; field-row confidence/source/conflict/review states; field click selects evidence and calls the viewer jump; edit/confirm/reject call the right APIs; viewer handles PDF/image/page-only/missing/text-only/converted states; manual mode hides broken source controls; owner-assignment and FSBO guard render only for allowed roles; exit dialog uses the branded pattern.

**E2E (Playwright or equivalent):** the nine UATs above, plus evidence-viewer screenshot checks on desktop and tablet.

**Golden contract suite:** at least 10 known packets across states/forms (clean PDF, scanned PDF, counteroffer, amendment, seller disclosure, preapproval, missing pages, missing signatures, blurry scan), each with expected fields, expected controlling values, and expected page/evidence references, run in CI to catch extraction and matcher regressions.

---

## 17. Risks and open decisions

**Decisions to lock in Phase 0:** PDF viewer library; OCR-geometry storage (JSONB vs object storage); DOC/DOCX/TXT conversion (in scope, via a document->PDF step before Textract, or deferred with the allowlist held to PDF/JPEG/PNG/TIFF); exactly when an `Incomplete` shell is created; the critical-field set that must have evidence before bulk confirm; progress transport (poll first, SSE later); old-modal removal vs redirect wrapper; whether commit queues e-sign or only creates an acknowledged follow-up; **(F11) the single source of truth for "controlling value" across counteroffers - server resolver vs the frontend `aiSourceRanks` chronology ranker - which must be reconciled to one path to avoid divergent answers**; **(F2/F10) whether to pull per-source `document_id` into the extraction schema now or rely on `resolve-documents` plus snippet search for multi-document attribution in the interim**; **(F3) how to expose the Textract per-page OCR text to the client in Phase 1 - return it inline with the parse result, or persist it in a lightweight read store - noting it must remain the full OCR text, never a reduced copy, and that highlighting is Textract-driven for all documents (no native/scanned split)**.

**Risks:** Textract normalized coordinates must be reconciled to the rendered artifact the user sees or highlights drift (especially for converted documents); some scans yield no reliable boxes, so the text-only/page-only fallback must be honest, not silently degraded; long OCR/AI work needs the durable run state so users can leave and resume; public-source values must always be labeled and confirmed so they never appear to override contract terms; and the perennial risk - a beautiful UI with controls that do not map to real endpoints. The phased plan mitigates the last one by gating every control behind a shipped, tested capability.

---

## 18. First engineering tickets

1. Add `ROUTES.TRANSACTION_NEW`, register `/transactions/new` outside `AppLayout` and before `/transactions/:transactionId`, gate with `RoleRoute allowedRoles={INTERNAL_ROLES}`, and redirect existing New Transaction / `?new=1` / quick-create CTAs to it.
2. Re-host the existing wizard step logic inside `WizardWorkspacePage` with the three-pane shell; keep behavior equivalent to today.
3. Build `WizardEvidenceViewer` (PDF.js/react-pdf) with signed-download rendering, page jump, and **Tier 1** text/snippet highlight from the existing `sources` map; honest fallback panel when no match.
4. Formalize the canonical field-path map from the knowledge already encoded in `WIZARD_FLAG_TARGETS`.
5. Add `wizard_runs` (+ `wizard_run_documents`) and save/resume APIs; remove the final-submit document hard-block in manual mode.
6. Implement the `Incomplete` shell policy and final `Active` transition; persist owner, FSBO guard, reviewed fields, and task-review choices.
7. Add `wizard_progress_events` and a `WizardRunService` that wraps existing parse/resolve calls and emits real stage events.
8. Persist OCR page text and Textract block geometry for wizard documents; add the snippet->box matcher and `ai_field_evidence`; upgrade the viewer to **Tier 2**.
9. Add the structured per-field review model and the conflict resolver bound to `transaction_resolution`; add the two-pass agreement check on critical fields.
10. Integrate task preview through the existing planner; gate commit on reviewed baseline; add the signature-decision UI and e-sign action handling; make commit atomic and fully audited.
11. Add the nine UATs to the testing guide and automate the clean, counteroffer, manual, and resume paths plus the golden contract suite.

---

## 19. Bottom line

The superior version is not a bigger modal. It is a full-screen, source-cited AI intake workspace where the AI does the tedious reading and the human is never asked to trust a black box. It is shippable in order: page+snippet evidence first (no new tables), then durable drafts, then real progress events, then pixel-accurate highlights, then full conflict-aware review and audited commit. Every phase ends with something a non-developer real-estate tester can validate end-to-end with a mouse, which is exactly what previous plans failed to guarantee.
