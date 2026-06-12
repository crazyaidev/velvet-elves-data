# AI Wizard ListedKit-Parity Gap Closure Plan

Prepared: 2026-06-09
Status: Planning only. No frontend or backend source code is changed by this document.
Revision: workflow/logic review pass completed against project docs and implemented source on 2026-06-09. A second source-verification pass (also 2026-06-09) checked the load-bearing claims line by line against the post-implementation source and recorded its corrections and confirmations in Section 2B; the affected body sections (2A.7, 7.1, 8, 9) were updated to match.
Purpose: close the three highest-priority AI Wizard gaps after the current V2 implementation pass: the workspace layout, the live extraction feedback, and source-cited PDF navigation for every AI-extracted value.

---

## 0. Executive Decision

The current AI Wizard has moved in the right direction, but it is not yet a professional source-cited intake workspace. The code now has a standalone route, a right-side document viewer, packet-parse polling, and OCR geometry support. Those are strong foundations. The remaining problem is that they are not yet bound into the workflow a real-estate user needs:

1. The standalone page does not have the required branded top bar with `velvet-elves-frontend/public/logo-removebg-preview.png`, project title, and always-visible workspace context.
2. Extraction feedback is still too generic. ListedKit shows field-level discoveries in the left workspace while the PDF is visible on the right. Velvet Elves currently shows a short stage list during the parsing step, not a persistent field-discovery log.
3. Source citation is incomplete. The current viewer can jump from a small set of citation chips, but every AI-extracted value must carry evidence, and clicking the value itself must select the correct document, page, and highlight or snippet.

The implementation should therefore be a gap-closure pass, not a full rewrite. Reuse the existing route, wizard state, packet parser, OCR geometry table, PDF viewer, and task preview step. Replace the weak binding layer around them.

---

## 1. Reviewed Inputs

### Project documentation reviewed

- `velvet-elves-data/requirements.txt`
- `velvet-elves-data/SYSTEM_DESIGN.md`
- `velvet-elves-data/milestones.txt`
- `velvet-elves-data/FRONTEND_UI_WORKFLOW_LOGIC.md`
- `velvet-elves-data/STYLE_GUIDE.md`
- `velvet-elves-data/AI_WIZARD_REDESIGN_SUPERIOR_PLAN_V2.md`
- `velvet-elves-data/AI_WIZARD_REDESIGN_SUPERIOR_LISTEDKIT_PLAN.md`

### ListedKit screenshots reviewed

Reviewed every screenshot in `velvet-elves-data/listedkit/ai_wizard`:

- `Screenshot_27.png` through `Screenshot_30.png`: upload, represented-side selection, start intake, document preparation.
- `Screenshot_31.png` through `Screenshot_33.png`: live extraction log on the left with PDF viewer on the right.
- `Screenshot_34.png` through `Screenshot_38.png`: transaction-detail review, source strips, row-level source actions, party cards, financing and contingency review.
- `Screenshot_39.png` through `Screenshot_43.png`: one-at-a-time date confirmation and full timeline review with source lookup.
- `Screenshot_44.png` through `Screenshot_48.png`: compliance checklist generation, checklist review, edit/add document dialogs, custom checklist import.
- `Screenshot_49.png` through `Screenshot_51.png`: final task-list review, task edit dialog, auto-email option, open transaction action.

### Current frontend source reviewed

- `velvet-elves-frontend/src/App.tsx`
- `velvet-elves-frontend/src/utils/constants.ts`
- `velvet-elves-frontend/src/pages/transactions/WizardWorkspacePage.tsx`
- `velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx`
- `velvet-elves-frontend/src/components/wizard/wizardTypes.ts`
- `velvet-elves-frontend/src/components/wizard/WizardEvidenceViewer.tsx`
- `velvet-elves-frontend/src/components/wizard/WizardPdfDocument.tsx`
- `velvet-elves-frontend/src/components/wizard/ReviewTasksStep.tsx`
- `velvet-elves-frontend/src/hooks/useWizardApi.ts`
- `velvet-elves-frontend/src/hooks/useDocuments.ts`
- `velvet-elves-frontend/src/utils/ocrHighlight.ts`
- `velvet-elves-frontend/src/tests/integration/WizardFlow.test.tsx`
- `velvet-elves-frontend/src/tests/mocks/handlers.ts`
- `velvet-elves-frontend/src/components/RoleRoute.tsx`

### Current backend source reviewed

- `velvet-elves-backend/app/api/v1/ai.py`
- `velvet-elves-backend/app/api/v1/documents.py`
- `velvet-elves-backend/app/api/v1/transactions.py`
- `velvet-elves-backend/app/api/v1/esign.py`
- `velvet-elves-backend/app/schemas/ai.py`
- `velvet-elves-backend/app/schemas/transaction.py`
- `velvet-elves-backend/app/services/document_packet_parsing.py`
- `velvet-elves-backend/app/services/providers/parsing.py`
- `velvet-elves-backend/app/services/providers/prompts.py`
- `velvet-elves-backend/app/services/textract_service.py`
- `velvet-elves-backend/app/services/contract_resolution.py`
- `velvet-elves-backend/app/repositories/document_ocr_geometry_repository.py`
- `velvet-elves-backend/supabase/migrations/20260814090000_document_ocr_geometry.sql`

---

## 2. Requirements That Must Govern The Build

These are not optional UX preferences. They are already required by the project docs.

- The wizard is document-first, but it must support a manual no-document fallback.
- AI extraction must be user-confirmed before transaction creation and task generation.
- AI parsing must use a two-pass or double-check mechanism for critical fields: date, party, signature status, and requested deliverable.
- Every AI recommendation or AI-filled fact must show reason, source, and confidence.
- Editing a field is a one-time validation action. It must not trigger a rescan.
- Task preview and final task generation must use the same server-side planner.
- The documented public wizard flow is six phases; the existing task-review screen is allowed as a pre-create confirmation substate, but it must not create a second contradictory workflow model.
- Save-as-draft must use the documented `Incomplete` lifecycle rather than leaving the user with only volatile in-browser state once draft persistence is implemented.
- The upload UX may advertise only file types that the OCR-plus-evidence path can actually support. Wider DOC/DOCX/GIF/WEBP support requires conversion or normalization into the Textract path first.
- Creation-capable roles must match implemented role names: `Agent`, `TransactionCoordinator`/Elf, `TeamLead`, and `Admin`, unless product explicitly removes Admin creation access.
- The UI must be fully testable by real-estate professionals from the frontend, with mouse-first actions and minimal typing.
- The visual language must follow Velvet Elves: calm, premium, professional, light-mode, restrained champagne AI accents, no imitation of ListedKit's green theme. Do not decorate rows as "AI vs manual" once data is in a card; source identity belongs in source controls and audit details, not as noisy visual badges.

---

## 2A. Workflow And Logic Corrections From This Review

This review found several plan flaws that would have caused frontend validation dead ends if implemented as originally written.

1. **Realtime extraction wording was too strong.** The current packet parser emits real persisted stage progress, but the structured LLM call is not field-streaming. The corrected workflow must show OCR/stage progress live, then append field-discovery events immediately when the extraction object returns. It must not fake per-field streaming with artificial delays.
2. **The resolver cannot be blindly trusted after packet parsing until per-document candidates are fixed.** `parse-document-packet` currently extracts one transaction-level result and persists that same top-level extracted result on every document, with per-document inventory added underneath. If `resolve-documents` then collects field candidates from each document, it may see duplicated transaction-level values and attribute the winning value to the wrong document. The corrected plan requires either structured field evidence with document id from packet parsing or true per-document field candidates before the resolver becomes the authority for packet-created fields.
3. **Manual mode was contradicted by current advancement rules.** The UI exposes `Skip upload - enter details manually`, but `missing`, `confirm`, and final submit are currently blocked by `hasRequiredDocument`. The corrected workflow explicitly allows no-document manual creation, with every field marked as manual source kind and no broken document panel.
4. **The double-check requirement was named but not planned.** Requirements mandate a two-pass/double-check gate for date, party, signature status, and requested deliverable. The corrected implementation phases include this as a gating backend/API requirement before AI values can be auto-confirmed.
5. **Six documented phases vs seven internal states needed reconciliation.** The code has `upload`, `parsing`, `address`, `purchase`, `missing`, `confirm`, and `review`. The plan now treats task review as a confirmation substate before create, not a separate public workflow that conflicts with the documented six-step wizard.
6. **Source visualization risked violating the style guide.** Source controls are required, but rows should not be visually split into loud "AI" and "manual" styles. The corrected UI uses source chips, inline source strips, confidence, and audit labels without turning origin into decorative noise.
7. **Post-create routing was too vague.** The current implementation navigates to `/transactions?highlight={id}` ([NewTransactionWizard.tsx:3099](velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L3099)). Both `/transactions` and `/transactions/active` render the same `TransactionListRouter` and honor `?highlight=`, and `/transactions/active?highlight=` is the convention used everywhere else in the app, so this is a one-line consistency choice, not a route-architecture change (see §2B.4). Either is safe; prefer `/transactions/active?highlight={id}` for consistency.
8. **File-type parity cannot be solved by widening frontend validation alone.** Requirements mention DOC/DOCX/GIF and other image types, while the source-cited pipeline is presently PDF/JPEG/PNG/TIFF. The corrected plan requires conversion/normalization before advertising those formats for source-highlighted extraction.

---

## 2B. Additional Corrections From The Source-Verification Pass (2026-06-09)

This pass re-read the implemented source named in Section 1 and checked the plan's load-bearing claims line by line. Most of the plan is accurate and well-grounded; the following are the confirmations and the three corrections.

### 2B.1 Confirmed accurate (do not "fix" these)

- **Resolver duplication is real.** `parse-document-packet` does `doc_extracted = dict(packet_result.extracted_data)` for every uploaded document and only attaches per-document *inventory* underneath (`_packet_document_finding`, `document_type_detected`, `all_parties_signed`, `missing_signatures`) ([ai.py:987-1014](velvet-elves-backend/app/api/v1/ai.py#L987-L1014)). The transaction-level fields (address, price, dates, parties) are identical on every document row, exactly as Gap F and §15.6 state. The resolver-safety requirement stands.
- **Manual-mode dead-end is real.** `hasRequiredDocument = state.documents.some(isPersistedWizardDocument)` gates the `missing` step, the `confirm` step, and every final submit button ([NewTransactionWizard.tsx:3116-3119,3240-3242,5730-5948](velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L3116-L3119)). Gap G is correct: manual mode cannot currently reach create.
- **Evidence coverage gaps are real.** `buildEvidenceCitations` cites only address, purchase_price, closing_date, contract_acceptance_date, earnest_money, possession_date, first buyer, first seller ([wizardTypes.ts:198-234](velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L198-L234)); the rendered `evidenceFacts` chips are an even narrower six ([NewTransactionWizard.tsx:3123-3162](velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L3123-L3162)); and `EvidenceFact` carries no `document_id` ([WizardEvidenceViewer.tsx:39-45](velvet-elves-frontend/src/components/wizard/WizardEvidenceViewer.tsx#L39-L45)). Gaps C, D, E are correct.
- **`useResolveDocuments` is defined but never called by the wizard** ([useWizardApi.ts:206](velvet-elves-frontend/src/hooks/useWizardApi.ts#L206); no import in `NewTransactionWizard.tsx`). Gap F is correct.
- **Progress keys are `prepare`, `ocr`, `extract`, `resolve`, `finalize`** ([ai.py:935,968](velvet-elves-backend/app/api/v1/ai.py#L935); [document_packet_parsing.py:434-461](velvet-elves-backend/app/services/document_packet_parsing.py#L434-L461)). §4.1/§6.2 are correct.

### 2B.2 Correction 1: Several "evidence-gap" fields are NOT EXTRACTED at all (prevents a tester dead-end)

The plan repeatedly lists `county`, `parcel number / tax ID`, `down payment`, `loan amount`, and `tenant occupied` as fields that merely lack a source control (Gap C, §6.1, §6.2 step 5, §7.1 registry, Phase 2 acceptance). They are not in the extraction schema at all: `ExtractionResult` has no county, no parcel/tax-ID, no down_payment, no loan_amount, and only `is_owner_occupied` (there is no tenant-occupied field) ([base.py:38-131](velvet-elves-backend/app/services/providers/base.py#L38-L131)), and `parsing.py` never populates them ([parsing.py:250-371](velvet-elves-backend/app/services/providers/parsing.py#L250-L371)).

This matters because the two cases need different work and carry different risk:

- **Category A (extracted today, just not surfaced).** Every field `parsing.py` already attaches a `source` to is pure frontend evidence-surfacing work with no backend change: address, city, state, zip, representation_type, purchase_price, financing_type, earnest_money, title_ordered_by, closing_mode, contract_acceptance_date, closing_date, possession_date, inspection_deadline, financing_deadline, appraisal_deadline, insurance_days, hoa_doc_days, other_contingencies, buyers, sellers, listing_agent, buyers_agent, loan_officer, title_company, closing_attorney, is_owner_occupied, has_hoa, has_inspection, has_home_warranty, home_warranty, professional_fees, all_parties_signed, document_acceptance_status. Phase 2 can deliver these immediately.
- **Category B (not extracted; needs backend work first).** county, parcel/tax ID, down payment, loan amount, tenant-occupied. A click-to-source control is impossible until the prompt, `ExtractionResult`, and `parsing.py` are extended to extract and cite them. Promising a tester "click the parcel number to see its source" before that lands is exactly the dead-end this plan exists to prevent.

**Correction:** the field registry (§7.1) and Phase 2 acceptance (§9) must tag each field Category A (surface-only) or Category B (extract-first), and Category B fields move behind a backend extraction-schema task. Down payment and loan amount should join the §3.4 finance set only after they are extractable.

### 2B.3 Correction 2: §8 sub-numbering contradicts the six-phase model it is trying to protect

Section 8 lists six documented phases (Upload, Parsing, Address & Contact, Purchase, Missing, Confirm & Create) and then numbers its sub-sections "Step 1…Step 6", but §8.3 ("Step 3: Review extracted facts") and §8.4 ("Step 4: Review timeline") do not match documented phase 3 (Address & Contact) or phase 4 (Purchase), and §8.6 ("Step 6: Signature decisions") is not phase 6 (Confirm & Create). The implemented step machine is `upload`, `parsing`, `address`, `purchase`, `missing`, `confirm`, `review`, which already maps cleanly to the six phases (`address`→3, `purchase`→4). This is the exact "two competing workflow definitions" failure Gap J/§2A.5 warn against, reproduced inside §8. Corrected in §8 below: the §8.x sub-sections are relabeled as **workspace surfaces inside the existing phases/steps**, not a second step numbering.

### 2B.4 Correction 3: Post-create route is a consistency choice, not an architecture change

§2A.7 and §8.7 treat `/transactions/active?highlight={id}` as a deliberate route-architecture change versus the current `/transactions?highlight={id}`. In fact both paths render the same `TransactionListRouter` and both honor `?highlight=` ([App.tsx:489,496](velvet-elves-frontend/src/App.tsx#L489)), and `/transactions/active?highlight=` is the dominant convention (dashboards, tasks, payments, analytics). Either is safe; this is a one-line consistency choice. Softened in §2A.7 and §8.7.

---

## 3. ListedKit Benchmark Findings

The screenshots show a consistent product pattern.

### 3.1 Upload and intake start

ListedKit starts with a simple upload card, file list, large represented-side buttons, and a single `Start Intake` action. The top bar remains fixed with the brand, step indicator, credits, and exit action.

Required Velvet Elves equivalent:

- Top bar is always visible.
- Upload area is simple and not buried in a modal card.
- Represented side is selected before parsing so party extraction can scope correctly.
- Uploaded file list supports preview and remove.
- Start extraction is an explicit user action.

### 3.2 Live extraction

During extraction, ListedKit immediately shifts into a split workspace:

- Left side: a live log of specific discoveries.
- Right side: the PDF viewer with document tab, zoom controls, page thumbnails, and current page.
- Log examples include address, city/state/zip, county, parcel number, inclusions, exclusions, seller names, buyer names, marital status, purchase price, earnest money, financing type, closing date, possession, title, home warranty, inspection, disclosures, default, and execution date.

Required Velvet Elves equivalent:

- The left workspace must show more than `Reading documents`, `Extracting transaction details`, `Resolving across documents`.
- It must show field-level findings as they become available or immediately after the extraction result is finalized.
- It must remain visible as the user transitions into review.
- Clicking an extraction event that has evidence should jump the right viewer to the source.

### 3.3 Transaction detail review

ListedKit displays extracted data in editable tables/cards. Each row has edit and source/search controls. Clicking source reveals an inline strip with source section, page, summary, and `View in Document`.

Required Velvet Elves equivalent:

- Source must be attached to the field row, not only to a global chip bar.
- The source action must be adjacent to the value.
- Inline source details must show document, page, snippet/summary, confidence, and match quality.
- Edit, reject, and confirm controls must preserve the original AI source for audit.

### 3.4 Timeline review

ListedKit separates timeline review from generic fact review. Deadline rows show final date plus calculation basis, such as `5 days after Date of Acceptance`, and each row can be edited, deleted, or source-checked.

Required Velvet Elves equivalent:

- Key dates must be a first-class review section.
- Each date must show both final date and basis.
- Derived dates must show whether they came from contract text, system calculation, or user edit.
- Clicking a timeline source must jump to the actual source page, which may be a later signature page.

### 3.5 Checklist and task review

ListedKit generates a compliance checklist after timeline confirmation, then a final task list. The user can search, add, edit, remove, and confirm before opening the transaction file.

Required Velvet Elves equivalent:

- Reuse `ReviewTasksStep` because it already dry-runs the real planner and exposes due basis.
- Add clearer task basis/source display so users understand why each task exists.
- Add missing-document or compliance-checklist review as a future parity-plus layer, but do not block the three priority fixes on it.

---

## 4. Current Implementation Audit

### 4.1 Foundations to preserve

- `ROUTES.TRANSACTION_NEW = '/transactions/new'` exists.
- `App.tsx` mounts `/transactions/new` inside `ProtectedRoute` and outside `AppLayout`, using `RoleRoute allowedRoles={INTERNAL_ROLES}`.
- `WizardWorkspacePage.tsx` consumes pending files and hosts `NewTransactionWizard`.
- `NewTransactionWizard` has a standalone layout and can mount `WizardEvidenceViewer` on large screens.
- `useParseDocumentPacket` polls `POST /api/v1/ai/parse-document-packet` and `GET /api/v1/ai/parse-document-packet/{packet_id}/status`.
- Backend packet parsing appends persisted `progress` events to document metadata.
- Backend packet parsing persists Textract LINE geometry through `DocumentOcrGeometryRepository`.
- `GET /api/v1/documents/{document_id}/ocr-geometry` returns geometry to the frontend.
- `WizardEvidenceViewer` fetches signed document URLs, supports document tabs, page navigation, citation chips, and OCR geometry.
- `WizardPdfDocument` renders PDFs with `react-pdf` and draws normalized highlight boxes.
- `matchSnippetToHighlights` provides an honest fallback when the snippet cannot be matched confidently.
- `ReviewTasksStep` already previews generated tasks with due basis and lets users exclude, override, and approve AI-added tasks.

### 4.2 Gaps blocking the requested experience

#### Gap A: Layout is still not the requested workspace

Current standalone layout is a left scroll area plus right viewer, but it lacks:

- Fixed top bar with Velvet Elves logo image.
- Dynamic project title.
- Global step/status context in the top bar.
- Left workspace structured as a persistent extraction/review surface.
- A layout where extraction and review both preserve the same left/right mental model.

#### Gap B: Extraction progress is not detailed enough

The frontend has `parseProgress`, and backend has `prepare`, `ocr`, `extract`, `resolve`, and `finalize` events. This is real backend progress, but it is too coarse compared with ListedKit's field-by-field log.

Missing:

- Field-discovery events such as `Identified sellers`, `Found purchase price`, `Confirmed closing date`.
- Page/document attribution on extraction events.
- A persistent activity panel after the parsing step.
- User-visible warnings for partial OCR, low confidence, missing pages, unclear signatures, or conflicts.

#### Gap C: Evidence is limited and not attached to every field

`buildEvidenceCitations` currently extracts citations only for:

- `address`
- `purchase_price`
- `closing_date`
- `contract_acceptance_date`
- `earnest_money`
- `possession_date`
- first buyer
- first seller

That is far below the requirement. It misses many fields visible in ListedKit and in Velvet Elves requirements: city, state, ZIP, county, parcel number, HOA, tenant occupied, financing type, down payment, loan amount, appraisal, inspection, title, closing agent, home warranty, professional fees, signatures, acceptance status, parties beyond the first buyer/seller, and custom contingencies.

#### Gap D: Evidence lacks document identity

`EvidenceFact` has `id`, `label`, `value`, `page`, and `snippet`, but no `document_id`. In a single PDF, this can appear to work. In a packet with a purchase agreement, counteroffer, amendment, and disclosure, page 2 is ambiguous. The viewer cannot reliably select the right document.

#### Gap E: Evidence is global instead of row-level

The current viewer exposes `Jump to` chips. ListedKit makes the source action part of each extracted row/card. A real-estate user should not have to hunt through a chip bar to verify a field.

#### Gap F: Server document resolver is available but not safely bound to packet evidence

`useResolveDocuments` exists, but `NewTransactionWizard` does not call it. That means the wizard can still rely on frontend chronology ranking while the backend has a stronger authoritative resolver in `contract_resolution.py`.

However, there is a deeper logic risk: the packet parser currently returns one transaction-level extraction and persists that same top-level extracted data onto each uploaded document. If the resolver collects candidates from those duplicated document records without true per-document field candidates, it can pick a controlling document id that reflects document ordering rather than the document that actually supplied the field source.

Corrected decision:

- The server resolver must become the single source of truth for controlling values across counteroffers and amendments.
- Before relying on it for packet-created fields, the backend must either store per-document field candidates or return structured packet evidence with `document_id` for each field.
- Until then, the frontend may use `resolve-documents` to show inventory, conflicts, and review warnings, but field-level source jumps must prefer structured packet evidence or snippet-to-OCR matching over a duplicated resolver candidate.

#### Gap G: Manual fallback is still at risk

The UI supports manual mode, but current advancement rules still require `hasRequiredDocument` for later steps. Requirements explicitly allow `Skip - enter details manually`; manual mode must not be blocked at final create solely because no document exists.

#### Gap H: Tests prove the prototype, not the final workflow

Current tests cover citation chips and OCR highlight rendering. They do not yet prove:

- every displayed AI field has evidence or an explicit non-document source label;
- clicking the actual field row changes the right viewer;
- multi-document packets select the correct document before jumping to a page;
- source strips render inline beside the selected row;
- manual mode can complete transaction creation without a required document;
- extraction progress contains field-level user-visible events.

#### Gap I: Double-check parsing is not implemented as a workflow gate

The requirements mandate a two-pass or double-check mechanism for date, party, signature status, and requested deliverable. The current packet parser runs a single structured extraction pass. A plan that only improves layout and evidence would still allow a single-pass AI result to advance into review without the required agreement check.

#### Gap J: Public step model and internal state model are inconsistent

Project docs describe a six-step full wizard ending in confirmation. Current code has seven internal states because `ReviewTasksStep` previews tasks before final create. The corrected workflow must present this as six user-facing phases plus a task-preview substate inside final confirmation, so testers are not validating against two competing workflow definitions.

#### Gap K: Draft and `Incomplete` lifecycle are underspecified

Requirements define `Incomplete` as the status for a wizard started but not confirmed. Current wizard state is mostly in React memory and parse-job metadata. The plan must distinguish Phase 1 volatile state from later draft persistence and specify when an `Incomplete` transaction shell is created and when it flips to `Active`.

#### Gap L: Source UI could violate the style guide if origin becomes decoration

The style guide warns against visually differentiating AI-extracted vs manual data once it is in a card. Source transparency is required, but it should be implemented with source actions, confidence, inline source strips, and audit metadata. Avoid loud row treatments that make manual vs AI origin the dominant visual language.

---

## 5. Target Workspace Design

### 5.1 Screen structure

Use a two-pane workspace under a fixed top bar.

#### Top bar

Content:

- Left: brand image from `/logo-removebg-preview.png`, with alt text `Velvet Elves`.
- Center-left: project title.
  - Before extraction: `New transaction`.
  - After address is known: property address.
  - If client is known: append buyer/seller name in smaller text.
- Center: compact step indicator.
- Right: extraction status chip, save/exit action, discard action.

Behavior:

- Always visible.
- No app sidebar.
- No global top nav.
- No floating AI chat overlay.
- Does not visually copy ListedKit; use Velvet Elves typography and color tokens.

#### Left workspace

The left workspace is the user's working surface. It is not a modal card.

States:

- Upload and represented-side selection.
- Live extraction activity.
- Review facts.
- Review timeline.
- Missing information.
- Signature decisions.
- Task preview and final create.

The left workspace should have its own sticky footer:

- Back.
- Next unresolved or confirm current section.
- Primary CTA for the current phase.

#### Right document viewer

The right side is the proof surface.

Required controls:

- Document tabs or compact document selector.
- PDF/image preview.
- Page thumbnails for PDF.
- Page navigation.
- Zoom controls.
- Search within OCR text if available.
- Active citation banner.
- Highlight overlay when geometry matches.
- Page/snippet fallback when a precise box is unavailable.

Click behavior:

- Selecting a field or source action in the left workspace updates the active document.
- The viewer changes to the evidence page.
- The viewer centers the matched highlight when possible.
- If the viewer is single-page mode, page jump plus highlight is acceptable.
- If no exact geometry exists, the viewer still selects the page and shows the snippet/summary.

### 5.2 Responsive behavior

Desktop:

- Top bar fixed.
- Left workspace and right viewer split horizontally.
- A draggable width splitter is optional but useful.

Tablet:

- Two panes remain if there is enough width.
- Otherwise use `Workspace` and `Source` segmented tabs.

Mobile:

- Workspace is primary.
- Source opens as a bottom sheet or full-screen source tab.
- The same field click must open the source view and select the right document/page.

---

## 6. Detailed Extraction Feedback Plan

### 6.1 Event taxonomy

Expand `ParseProgressEvent` from a generic stage list into user-visible operational events.

Proposed event shape:

```ts
type WizardExtractionEvent = {
  sequence: number
  kind:
    | 'stage_started'
    | 'stage_completed'
    | 'document_started'
    | 'page_read'
    | 'field_found'
    | 'field_conflict'
    | 'quality_warning'
    | 'evidence_matched'
    | 'stage_failed'
  stage:
    | 'prepare'
    | 'ocr'
    | 'classify_documents'
    | 'property'
    | 'parties'
    | 'price_financing'
    | 'timeline'
    | 'contingencies'
    | 'signatures'
    | 'resolve'
    | 'evidence'
    | 'finalize'
  label: string
  detail?: string
  field_id?: string
  field_path?: string
  value_preview?: string
  document_id?: string
  document_name?: string
  page?: number
  confidence?: number
  severity?: 'info' | 'success' | 'warning' | 'error'
  at: string
}
```

### 6.2 Immediate backend implementation

Use the existing packet parse job metadata first. Do not introduce a new table just to close the UI gap.

Backend changes to plan:

1. Keep existing `prepare`, `ocr`, `extract`, `resolve`, and `finalize` events. Extend the current `ParseProgressEvent` shape backward-compatibly rather than replacing `sequence`, `key`, `label`, `detail`, and `at` in one breaking change.
2. Add document-level OCR events:
   - `Reading test.pdf`
   - `Read 6 pages from test.pdf`
   - `Textract warnings found for test.pdf`
3. Do not claim page-by-page live OCR progress unless `process_document_with_textract` is changed to report page callbacks. Today Textract returns the page count after the OCR job completes, so per-document page-count events are truthful while per-page streaming events would be misleading.
4. Run the mandatory double-check pass for critical fields before the parser reports the extraction as reviewable:
   - date fields;
   - buyer/seller and represented-party roles;
   - signature and acceptance status;
   - requested deliverable/document purpose.
5. After the LLM extraction and double-check result are available, flatten the extracted fields through a canonical field registry and append `field_found` events in real-estate order:
   - property address
   - city/state/ZIP/county
   - parcel number
   - sellers
   - buyers
   - purchase price
   - earnest money
   - financing type and deadlines
   - closing/title/possession
   - contingencies
   - signatures
6. Append `field_conflict` events only from a resolver output that has reliable per-document candidates or from structured packet evidence that identifies competing source documents. Do not create conflict events from duplicated transaction-level packet data alone.
7. Append `quality_warning` events from OCR warnings, low confidence, double-check disagreement, missing source, page-only match, or failed geometry match.

This is honest progress. It does not fake a timer. Field events will normally appear as a batch immediately after extraction and double-check complete because the current structured LLM call does not stream individual fields. That is acceptable for the first parity pass as long as the UI labels them as findings discovered during the completed extraction rather than pretending the model streamed them token by token.

### 6.3 Later realtime implementation

Once the workspace is stable, add a durable event stream:

- `GET /api/v1/ai/parse-document-packet/{packet_id}/events?since_sequence=N`
- or Server-Sent Events at `/api/v1/ai/parse-document-packet/{packet_id}/events/stream`

Polling is acceptable for v1 because the current hook already polls. SSE is an enhancement, not a blocker.

### 6.4 Left-workspace UI

During extraction, the left workspace should show:

- Document list with per-document status.
- Live event log with checkmarks, spinner for current stage, and warning badges.
- A compact `Found so far` area. In the first implementation this can populate immediately after extraction completes; it should update during extraction only if the backend actually emits field events before the final parse result.
- A `Pause auto-scroll` control once the user scrolls upward.
- A `Review extracted details` CTA only after extraction reaches a terminal state.

After extraction, the event log should remain available as a collapsible `What AI found` section. This lets a tester explain what happened without leaving the wizard.

---

## 7. Source Evidence Plan

### 7.1 Canonical field registry

Create one field registry shared by evidence, review rendering, missing-info checks, and task preview.

Each field definition should include:

```ts
type WizardFieldDefinition = {
  field_id: string
  label: string
  group:
    | 'property'
    | 'parties'
    | 'price_financing'
    | 'timeline'
    | 'contingencies'
    | 'title_closing'
    | 'signatures'
    | 'documents'
  backend_paths: string[]
  extracted_keys: string[]
  ui_path: string
  input_kind: 'text' | 'money' | 'date' | 'number' | 'boolean' | 'select' | 'party' | 'long_text'
  required_for_create: boolean
  source_policy: 'document_required' | 'document_optional' | 'manual_ok' | 'system_rule' | 'public_source'
  critical_double_check?: boolean
}
```

Each registry entry must be tagged **Category A** (extracted today, surface-only frontend work) or **Category B** (not yet extracted, requires a prompt/`ExtractionResult`/`parsing.py` change first; see §2B.2). county, parcel/tax ID, down payment, loan amount, and tenant-occupied are Category B. The first registry must cover at least:

- Street address, city, state, ZIP, county, parcel/tax ID.
- HOA, tenant occupied, owner occupied.
- Buyer(s), seller(s), listing agent, buyer agent, loan officer, title company, closing attorney.
- Purchase price, earnest money, down payment, loan amount, financing type.
- Contract acceptance date, closing date, possession date, title transfer date.
- Inspection deadline, financing deadline, appraisal deadline, insurance days, HOA document days.
- Home warranty, professional fees, closing mode.
- Document type, acceptance status, all parties signed, missing signatures.
- Custom contingencies and other extracted terms.

The registry is also the authoritative map between backend namespaces (`property.address`, `transaction.purchase_price`, `timeline.closing_date`, `parties.buyers[0].name`, `detection.all_parties_signed`) and UI state paths (`address.street`, `purchase.purchase_price`, `purchase.closing_date`, `parties.*`). Without this map, row-level evidence cannot reliably select the correct left-workspace row or source record.

### 7.2 Structured evidence shape

Every AI-filled field should resolve to a structured evidence object.

```ts
type FieldEvidence = {
  evidence_id: string
  field_id: string
  backend_path: string
  source_kind: 'ai_document' | 'manual' | 'public_search' | 'user_corrected' | 'system_rule' | 'not_applicable'
  document_id?: string
  document_name?: string
  page?: number
  section_label?: string
  snippet?: string
  summary?: string
  confidence?: number
  match_method?: 'query_answer' | 'exact_line' | 'fuzzy_line' | 'page_only' | 'text_only' | 'manual'
  highlight_rects?: Array<{
    page: number
    left: number
    top: number
    width: number
    height: number
  }>
  original_value?: unknown
}
```

### 7.3 Immediate evidence implementation

Do not wait for a new evidence table.

Use this order:

1. Keep the existing free-form `source` string for backward compatibility.
2. Parse source strings for document id, file name, page number, and snippet. The packet prompt already labels each document with id and file name; the evidence parser should use any document identity the model included before falling back to heuristics.
3. Parse `page N: snippet` as today for older responses.
4. If there is exactly one uploaded document, attach that document id to each citation.
5. If there are multiple uploaded documents, do not rely on resolver output alone unless the resolved field has a trustworthy `source_document_id` that came from a true per-document candidate. The current packet persistence can duplicate one transaction-level result onto every document, so resolver attribution must be treated as advisory until that is fixed.
6. Match snippet text against each document's OCR line geometry from `GET /api/v1/documents/{document_id}/ocr-geometry` and choose the best document/page match. If the same snippet appears in several documents, mark the evidence as ambiguous and require review instead of guessing.
7. For resolver-covered fields, use resolver histories to show controlling vs superseded values only when each candidate has distinct source document metadata.
8. If no document can be identified, show `Source not resolved` and require user confirmation before final create.

### 7.4 Backend evidence implementation

After the immediate pass, make evidence structured at the source:

1. Keep enforcing packet input labels for `document_id`, `file_name`, document index, and page count.
2. Change the extraction result to return sources as structured objects, not only strings.
3. Preserve the structured `sources` map through `packet_payload_to_extraction_result` instead of flattening away document identity.
4. Add post-processing that validates or repairs the LLM-provided `document_id` by searching OCR lines for the cited snippet.
5. Persist or return true per-document field candidates before making `resolve-documents` the field authority for newly parsed packets. The resolver already has `source_document_id`, but its output is only as good as the per-document candidates it receives.
6. Run the evidence matcher server-side where practical and return `match_method` plus optional highlight rectangles.
7. Include `transaction_resolution` in the packet parse result only after the evidence/candidate problem is solved, or call `resolve-documents` immediately after packet parse and clearly label its result as inventory/conflict advisory where evidence is incomplete.

The frontend should not be the long-term authority for deciding which counteroffer controls the final value. The backend resolver must be the authority, but only after the packet pipeline gives it field candidates that truly belong to individual source documents.

### 7.5 Frontend evidence UI

Replace global-only citation chips with row-attached evidence controls.

Each AI-filled row/card must show:

- Value.
- Confidence badge.
- Source chip: `Document name - p.N`. This is an action/audit control, not a decorative "AI vs manual" badge.
- Source icon button.
- Inline source strip when selected:
  - `Source: Section 3.4 Type of Financing`
  - `Page: 2`
  - `Summary: ...`
  - `Match: Exact line` or `Page only`
  - `View in document`

Clicking any of these should call one shared action:

```ts
selectEvidence(evidence: FieldEvidence)
```

That action must:

1. Set the active field in the left workspace.
2. Set the active document in the right viewer.
3. Set the active page.
4. Set the highlight rectangles or snippet fallback.
5. Scroll/center the viewer to the highlighted region when possible.

### 7.6 Source requirements by source kind

- `ai_document`: document/page/snippet required. Highlight expected when geometry exists.
- `manual`: no document required. Show `Manual entry` and audit the user edit.
- `public_search`: show searched source label and require explicit acceptance.
- `user_corrected`: show corrected value plus original AI value/source.
- `system_rule`: show rule basis, such as `5 days after Date of Acceptance`.
- `not_applicable`: show who marked it not applicable and why.

### 7.7 Acceptance rule

The user should not be able to approve an AI-document-sourced field as final if it has no source evidence, unless they explicitly convert it to `user_corrected` or `manual`.

This is the strongest way to ensure "whenever the AI displays data extracted from a document, the source of that data is clearly identifiable."

---

## 8. Workflow Design

The public workflow should read as the documented six-phase wizard:

1. Document Upload or Manual Start.
2. AI Parsing Progress.
3. Address and Contact Confirmation.
4. Purchase Information Validation.
5. Missing Information Handling.
6. Confirmation and Create.

The existing `review` state for `ReviewTasksStep` remains, but it is a confirmation substate before create, not a separate public requirement that contradicts the docs. In the top bar, show it as `Confirm - Task Preview` or `Final Review`, not as an unexpected seventh core step.

Mapping to the implemented step machine (so this section does not become the "competing workflow definition" Gap J/§2A.5 warn about): the code's internal states map onto the six phases as `upload`→1, `parsing`→2, `address`→3, `purchase`→4, `missing`→5, and `confirm`+`review`→6. The sub-sections below are therefore **workspace surfaces inside those phases**, not a second numbering. In particular, "extracted facts" (§8.3) and "timeline" (§8.4) are not new steps 3 and 4; they are review presentation layered onto the existing `address` and `purchase` steps, "signature decisions" (§8.6) is part of the phase 6 confirmation surface.

### 8.1 Step 1: Upload or manual start

Left workspace:

- Drop zone.
- Uploaded files list.
- Represented-side segmented control:
  - Buyer
  - Seller
  - Buyer and Seller
- `Run AI extraction` primary action.
- `Enter manually` secondary action.

Right viewer:

- Empty state before upload.
- Uploaded document preview after upload.

### 8.2 Step 2: Extraction

Left workspace:

- Live extraction activity log.
- Document statuses.
- Warnings and errors.
- Double-check status for critical fields: dates, parties, signatures, and requested deliverable.
- `Continue manually` fallback if extraction fails.

Right viewer:

- Active uploaded document.
- Thumbnails and zoom.
- If the active log event has evidence, jump to that page.

Advance rule:

- If OCR fails, no readable text is returned, pages are missing, or the double-check pass disagrees on a critical field, do not silently advance as a clean AI parse. Route the user into review with warnings, request a clearer copy, or offer manual continuation.

### 8.3 Review surface: extracted facts (inside phases 3-4, code steps `address` + `purchase`)

This is a presentation surface, not a new step. The implemented wizard already splits fact review across the `address` step (phase 3: property + parties/contacts) and the `purchase` step (phase 4: price + financing + contingencies + title/closing), each with its own `canAdvance` gate. The grouped review below enhances those two steps; it must not replace them with a single "facts" step (that would re-create the competing-workflow problem from Gap J).

Left workspace groups (rendered within the `address` and `purchase` steps):

- Property details.
- Parties.
- Price and financing.
- Contingencies and terms.
- Title and closing.
- Signatures.

Each field row:

- Confirm.
- Edit.
- Reject/not applicable when allowed.
- Source action.

Mouse-first actions:

- `Next unresolved`.
- `Confirm visible high-confidence fields` only when each field has evidence and no conflict.
- `Show only needs review`.

### 8.4 Review surface: timeline (dates from the `purchase`/`missing` steps, phases 4-5)

Use the ListedKit pattern, but in Velvet Elves style.

Each timeline row shows:

- Deadline name.
- Final date.
- Basis, such as `5 days after Date of Acceptance`.
- Source kind:
  - document evidence
  - system calculation
  - user corrected
- Edit and source actions.

Important: clicking `Date of Acceptance` may jump to a signature page, not necessarily the first contract page.

### 8.5 Step 5: Missing information

Missing fields should be grouped by urgency:

- Required to create.
- Required for task generation accuracy.
- Optional enrichment.

For each field:

- Manual input.
- Public-source search only when contract data is unavailable.
- Public-source result must show source label and require user acceptance.

### 8.6 Review surface: signature decisions (part of phase 6 Confirmation, not a separate step)

Show signature status as a source-cited review section:

- All parties signed.
- Missing signatures.
- Document acceptance status.
- E-sign provider connected or not, using `GET /esign/provider-status`.

Actions:

- Queue e-sign after create through `POST /documents/{id}/esign` when a provider is connected and the user chooses to send.
- Mark handled outside Velvet Elves.
- Mark signature not required, with reason.

This should not block the first source-navigation pass, but it must be in the plan because requirements 3.9 already require it. The e-sign completion path already replaces the original with the executed version and distributes/records communication, so the wizard should queue into that existing flow rather than inventing a separate signature lifecycle.

### 8.7 Final confirmation substate: Task preview and create

Treat this as the task-preview substate of final confirmation, not a seventh public wizard requirement. Reuse `ReviewTasksStep`.

Enhance the presentation to show:

- Task name.
- Due date.
- Due basis.
- Included because.
- Automation level.
- Related source field or timeline item.
- Edit target/date.
- Remove with reason.
- Approve AI-added task.

The final CTA should be `Approve and create transaction`.

After creation:

- Link uploaded documents.
- Generate tasks from reviewed set.
- Navigate to `/transactions/active?highlight={id}` (the app-wide convention) or `/transactions?highlight={id}` (the wizard's current target). Both render the same `TransactionListRouter` and honor `?highlight=`, so this is a consistency choice, not a route-architecture change (see §2B.4).

---

## 9. Implementation Phases

### Phase 1: Workspace shell and top bar

Goal: satisfy the layout requirement immediately.

Tasks:

- Update standalone `/transactions/new` shell to include fixed top bar.
- Use `/logo-removebg-preview.png` for the brand image.
- Add dynamic project title.
- Convert the standalone wizard layout into a two-pane workspace under the top bar.
- Keep right viewer mounted whenever viewport supports it.
- Remove unnecessary centered card framing from the left workspace.
- Add responsive source drawer/tab behavior for smaller screens.

Acceptance:

- The first viewport has top bar, left workspace, and right document viewer.
- No app sidebar or app top nav is present.
- Logo image is visible.
- The user can upload a file and preview it on the right before extraction.

### Phase 2: Row-level evidence binding

Goal: every visible AI field has a source control or explicit non-document label.

Tasks:

- Add canonical field registry.
- Expand evidence extraction beyond the current small citation list.
- Add `document_id` to evidence objects.
- Replace or supplement viewer `Jump to` chips with row-attached source controls.
- Implement `selectEvidence`.
- Add inline source strip to field rows and party cards.
- Preserve original evidence after user edits.

Acceptance:

- Clicking Category A fields (address, city, state, zip, buyer, seller, price, financing type, earnest money, acceptance date, closing date, possession, inspection/financing/appraisal deadlines, title company, closing attorney, owner-occupied, HOA, home warranty, professional fees, signatures) updates the right viewer. These need no backend change (see §2B.2).
- County, parcel/tax ID, down payment, loan amount, and tenant-occupied are NOT acceptance items for this phase. They are Category B (not yet extracted) and only become clickable after the extraction schema is extended.
- Single-document flow always selects the correct page.
- Missing source fields are clearly labeled and cannot be silently accepted as AI-document evidence.

### Phase 3: Multi-document source correctness and resolver authority

Goal: make packet/counteroffer review reliable.

Tasks:

- Call `useResolveDocuments` after packet parse when multiple documents are present.
- Fix or bypass the duplicated packet-data problem before treating resolver field attribution as authoritative:
  - either persist per-document field candidates;
  - or return structured packet evidence with `document_id` per field;
  - or restrict resolver use to inventory/conflict warnings until evidence is trustworthy.
- Prefer `transaction_resolution.resolved_fields[field].source_document_id` for controlling values only when that source document came from a real candidate, not a duplicated transaction-level packet copy.
- Retire frontend-only chronology as the long-term authority for controlling values after backend evidence/candidates are reliable.
- Add conflict UI showing winning value, superseded value, source document/page, and reason.
- Add document id repair by snippet-to-OCR match for fields not covered by the resolver.

Acceptance:

- Purchase agreement plus counteroffer packet shows the counteroffer value when it controls.
- Clicking the controlling value opens the counteroffer document, not the original purchase agreement.
- Superseded values remain visible with their own source.
- A regression test proves that a packet-level field copied onto every document does not cause the resolver to attribute the source to the wrong document.

### Phase 4: Double-check and quality gates

Goal: satisfy the mandatory two-pass parsing requirement before AI values can be treated as reviewable.

Tasks:

- Add a second extraction/check pass for critical fields using a different prompt strategy or extraction template.
- Compare pass results for date, party, signature status, and requested deliverable.
- Return a `double_check` object with agreement status, compared fields, differences, and recommended user action.
- Route disagreements to the review UI with warnings; do not mark them as clean high-confidence values.
- Halt or request a clearer copy when OCR indicates unreadable pages, missing pages, or other hard quality failures.

Acceptance:

- A clean document can proceed to field review with double-check agreement recorded.
- A disagreement on closing date, represented party, signature status, or deliverable appears as a blocking review item.
- The frontend can validate the entire disagreement path through the UI without opening backend logs.

### Phase 5: Detailed extraction activity log

Goal: match ListedKit's perceived transparency while staying truthful to the backend.

Tasks:

- Expand backend progress events with field-discovery and warning events.
- Surface the event log in the left workspace during extraction.
- Keep event history after extraction.
- Let event clicks select evidence.
- Add warning states for OCR partial success, low confidence, conflicting documents, missing source, no geometry match.

Acceptance:

- During extraction, the left workspace shows specific discoveries and warnings.
- Users can see what document and field the AI is working on.
- The log remains available after parsing.

### Phase 6: Review workflow polish

Goal: make the review flow usable by real-estate professionals without developer knowledge.

Tasks:

- Add `Next unresolved`.
- Add `Confirm visible high-confidence fields` with summary confirmation.
- Add grouped filters: All, Needs review, Missing source, Conflicts, Manual.
- Add timeline review screen with basis and source.
- Add sticky footer actions for each review state.
- Ensure no rescan occurs after edits.

Acceptance:

- A tester can complete a normal purchase agreement using mouse actions and minimal typing.
- The tester can explain every AI-populated value by opening its source.
- The task preview is reached only after required facts are reviewed.

### Phase 7: Manual fallback and draft resilience

Goal: remove dead ends.

Tasks:

- Allow manual mode to complete without a required document.
- Label all manual fields as manual source kind.
- Add save/exit draft behavior.
- When draft persistence is implemented, create or update a transaction shell with `status = Incomplete` only when the user explicitly saves or enough required shell data exists. Flip it to `Active` only after final approval and task preview confirmation.
- Later: add `wizard_runs` if resumability must survive browser refresh and device changes without creating an incomplete transaction shell early.

Acceptance:

- User can choose manual mode, enter required fields, preview tasks, and create a transaction without uploading a document.
- The right viewer shows an honest no-source state instead of a broken panel.
- Saving and exiting a draft does not generate tasks or mark the transaction Active.

### Phase 8: Superior-to-ListedKit enhancements

Goal: exceed parity after the three priority fixes are stable.

Candidate enhancements:

- Custom compliance checklist import by upload or paste.
- Auto-draft email toggles tied to AI Email Review.
- Document requirement checklist separate from task checklist.
- OCR text search in the right viewer.
- User feedback loop per field for AI improvement.
- Persistent wizard-run audit history.

---

## 10. Backend/API Plan

### 10.1 Extend parse response safely

Keep current response fields:

```json
{
  "extracted": {},
  "confidence": 0.92,
  "needs_review": false,
  "transaction_resolution": null
}
```

Add optional fields:

```json
{
  "evidence": {},
  "field_events": [],
  "quality_warnings": [],
  "double_check": {
    "status": "agreed",
    "critical_fields": []
  }
}
```

This preserves existing frontend compatibility.

`transaction_resolution` should remain optional until packet evidence is corrected. If included for a packet parse, it must clearly distinguish resolver outputs based on true per-document candidates from advisory inventory/conflict output based on duplicated transaction-level packet data.

### 10.2 Evidence endpoint strategy

Immediate:

- Use parse result plus `GET /api/v1/documents/{id}/ocr-geometry`.
- Build evidence from structured packet sources when available, then source strings, then OCR snippet matching.

Later:

- `GET /api/v1/ai/parse-document-packet/{packet_id}/evidence`
- or `GET /api/v1/wizard-runs/{run_id}/evidence`

### 10.2A Resolver contract correction

Before the frontend treats the resolver as authoritative for packet-created field attribution, the backend must stop feeding it duplicated transaction-level candidates. Acceptable fixes:

- Store per-document extracted field candidates from the packet parse, each with `field_path`, `value`, `confidence`, `source`, `document_id`, and page/snippet.
- Or return packet-level `evidence[field_path]` with controlling and superseded candidates, each carrying its source document id.
- Or change `resolve-documents` to ignore duplicated packet-level fields unless the field source string or structured evidence points back to that same document.

The UI can still call `resolve-documents` immediately for document inventory, acceptance status, missing-document flags, and review reasons. It must not use resolver `source_document_id` for a source jump unless the backend marks that candidate as evidence-verified.

### 10.3 Persistence strategy

Use existing persistence first:

- document metadata parse job for progress;
- `documents.ai_extracted_data` for extracted values;
- `document_ocr_geometry` for geometry.

Add a `wizard_runs` model only after the layout/evidence/progress UX is proven, or when draft/resume requirements exceed what document metadata and `Incomplete` transaction shells can safely support.

Draft lifecycle:

- Phase 1: no new persistence; warn before exit if state is dirty.
- Draft phase: explicit save creates or updates an `Incomplete` transaction shell when required shell fields exist.
- Final approval: create or update the transaction as `Active`, link documents, persist reviewed values, then generate tasks from the reviewed set.
- Manual no-document flow may create an `Active` transaction without linked documents after required fields are entered and task preview is approved.

If added later, minimum fields:

- `id`
- `tenant_id`
- `created_by`
- `status`
- `current_step`
- `document_ids`
- `draft_payload_json`
- `review_state_json`
- `progress_events_json` or separate events table
- `created_transaction_id`
- `created_at`
- `updated_at`

### 10.4 Security and authorization

- Evidence endpoints must authorize through the same document access path as download.
- Do not expose OCR geometry just because a user knows a document id.
- Keep service-role-only RLS for `document_ocr_geometry`; enforce tenant/document access in the API layer.

---

## 11. Frontend Component Plan

### 11.1 New or refactored components

- `WizardWorkspaceShell`
  - top bar
  - left/right pane layout
  - responsive source drawer
- `WizardTopBar`
  - logo image
  - title
  - step indicator
  - status and exit controls
- `WizardExtractionLog`
  - live events
  - warnings
  - field found entries
- `WizardDoubleCheckPanel`
  - critical-field agreement status
  - disagreement rows
  - clearer-copy/manual fallback actions
- `WizardReviewWorkspace`
  - grouped field registry renderer
- `WizardFieldRow`
  - value, confidence, confirm/edit/reject/source
- `WizardSourceStrip`
  - inline evidence summary
- `WizardTimelineReview`
  - date cards with basis/source
- `WizardEvidenceController`
  - shared selected evidence state used by left rows and right viewer
  - refuses ambiguous multi-document source jumps until the user chooses or the backend verifies the source

### 11.2 Existing components to keep

- `WizardEvidenceViewer`, but extend `EvidenceFact` to include `document_id` and selected evidence state.
- `WizardPdfDocument`, but add scroll-to-highlight behavior when possible.
- `ReviewTasksStep`, but enhance labels/source basis.
- `DocumentSplitDialog`.
- `SuggestImprovementButton`.

---

## 12. UX Copy and Visual Direction

Do not copy ListedKit's green product identity. Use Velvet Elves tokens.

Top bar:

- White surface, hairline border.
- Logo image at left.
- Serif or strong sans title depending on available vertical space.
- Champagne accent only for AI status and primary action.

Left workspace:

- Quiet gray page background.
- White field rows or slim sections.
- No nested decorative cards.
- Compact controls with icons and tooltips.
- Source action uses a search/file-text icon, not a text-heavy button.
- Source identity is available through the source chip/strip, but field rows should not be color-coded primarily as AI vs manual.

Right viewer:

- Neutral document surface.
- Active source highlight in champagne.
- Page thumbnails with subtle active border.
- Active citation banner uses amber only for warnings; normal source state should not look like an error.

---

## 13. Testing Plan

### 13.1 Manual UI validation workflows

These workflows must be executable by a real-estate tester through the frontend only.

1. Clean single purchase agreement
   - Upload PDF.
   - Choose represented side.
   - Watch extraction log.
   - Confirm double-check agreement is visible or recorded.
   - Review property, party, price, timeline, contingency, signature fields.
   - Click source for at least ten fields.
   - Confirm tasks and create transaction.

2. Multi-document counteroffer packet
   - Upload purchase agreement and counteroffer/amendment.
   - Confirm server resolver chooses controlling values.
   - Confirm the source document is not inferred from duplicated packet-level data.
   - Click controlling and superseded values.
   - Verify the right viewer opens the correct document for each.

3. Scanned/low-quality document
   - Upload a document that produces OCR warning or low confidence.
   - Confirm warnings appear in extraction log and field rows.
   - Verify manual correction preserves original source.

4. Missing information
   - Parse a document missing title company representative or phone.
   - Use public-source search.
   - Confirm source labels are visible and acceptance is explicit.

5. Manual no-document flow
   - Choose manual entry.
   - Complete required fields.
   - Confirm right viewer shows no-source manual state.
   - Preview tasks and create transaction.
   - Verify no upload-required banner blocks Missing, Confirm, or final Create.

6. Timeline source jump
   - Click Date of Acceptance.
   - Verify viewer jumps to the signature page if that is where the evidence lives.
   - Click financing deadline and verify the basis source.

7. Mobile/tablet
   - Source action opens source drawer/tab.
   - Same document/page evidence is selected.

### 13.2 Automated frontend tests

Add or extend tests for:

- Top bar renders logo and title on `/transactions/new`.
- Extraction log renders backend progress and field events.
- Double-check disagreement renders as a review blocker.
- Every registry-backed AI field renders a source control when evidence exists.
- Row click calls evidence selection and updates the viewer.
- Multi-document evidence switches the active document.
- Resolver source jumps are disabled or marked ambiguous when evidence is not verified.
- Missing evidence renders explicit fallback state.
- Manual mode can proceed without a document.
- Edited fields become `user_corrected` while preserving original AI evidence.
- Task review is presented as a final confirmation substate, not a contradictory seventh public workflow phase.

### 13.3 Backend tests

Add or extend tests for:

- Packet parse status returns progress events in sequence.
- Field events are generated from extraction results.
- Double-check result is returned for critical fields and disagreement changes `needs_review`.
- Evidence post-processing attaches document id for single-doc packet.
- Multi-doc evidence uses resolver source document where available.
- Resolver does not attribute packet-level duplicated fields to the wrong document.
- OCR geometry endpoint enforces document access.
- Resolver output includes enough source metadata for frontend review.

### 13.4 Visual checks

Use Playwright screenshots for:

- Desktop upload state.
- Desktop extraction state with live log and PDF viewer.
- Desktop review state with inline source strip.
- Mobile source drawer.

Canvas/PDF checks should verify that a highlight box is visible when OCR geometry is returned.

---

## 14. Acceptance Criteria

The implementation is ready only when all of these are true:

- `/transactions/new` shows a fixed top bar with the Velvet Elves logo image and project title.
- The first viewport contains the left workspace and right document viewer on desktop.
- During extraction, the left workspace shows detailed user-visible progress, including field discoveries and warnings.
- Critical fields have a double-check result; disagreements or hard OCR quality failures are routed to review/manual/clearer-copy recovery, not silently accepted.
- The right viewer remains visible during extraction and review.
- Every AI-extracted field has a source chip or an explicit non-document source label.
- Clicking an extracted field or its source action selects the correct document and page.
- When OCR geometry exists, the original source region is highlighted.
- When geometry does not match, the UI shows a page/snippet fallback without pretending there is a precise box.
- Multi-document packet evidence opens the correct source document.
- Server document resolution controls counteroffer/amendment values only after field candidates or structured evidence prove the source document. Until then, ambiguous source jumps are blocked or explicitly marked for review.
- Manual mode can create a transaction without a required upload.
- Draft save uses `Incomplete` status when a transaction shell is created, and no tasks are generated until final approval.
- Task preview uses the existing planner and the final generated tasks match the reviewed set.
- The workflow can be validated from the frontend by a non-developer tester.

---

## 15. Risks and Decisions

### 15.1 Field-level "real-time" limits

The current structured extraction call returns a complete object after the model finishes. True token-level field streaming may require a different provider call shape. The first implementation should be truthful: show real OCR/stage progress live, then append field-discovery events as soon as extraction returns. Do not fake delays to mimic ListedKit.

### 15.2 File type scope

The reliable source-cited path is currently PDF/JPEG/PNG/TIFF through Textract. Do not advertise DOC/DOCX/TXT/GIF/WEBP for source-highlighted extraction until the backend converts or normalizes them into the same OCR/evidence path.

### 15.3 Geometry match precision

Line-level matching is useful but not perfect. The UI must show `match_method` so users know whether the highlight is exact, fuzzy, page-only, or text-only.

### 15.4 Page rotation and scaling

Highlight rectangles are normalized. Test rotated/scanned PDFs before promising pixel-perfect highlighting.

### 15.5 Table sprawl

Do not add a large wizard persistence schema before the immediate layout/evidence/progress gaps are closed. Use existing document metadata and `document_ocr_geometry` first.

### 15.6 Resolver attribution risk

The packet parser currently persists one resolved transaction-level extraction onto each source document. If the resolver consumes that duplicated data as if each document independently said the same thing, source attribution can be wrong. The implementation must add per-document field candidates, structured field evidence, or an evidence-verified resolver flag before using resolver `source_document_id` for automatic source jumps.

### 15.7 Double-check cost and latency

The required second pass adds model cost and time. The UI should show it as part of the extraction process, but the backend should keep the comparison scoped to critical fields so the feature improves trust without making every parse feel stalled.

### 15.8 Draft shell timing

Creating an `Incomplete` transaction too early can clutter the active workspace; creating it too late can lose work on refresh. Phase 1 should keep dirty-state exit protection only. Draft persistence should create an `Incomplete` shell on explicit save or once required shell fields exist, and it must not generate tasks until final approval.

---

## 16. Build Checklist

1. Add `WizardWorkspaceShell` with top bar and two-pane layout.
2. Use `/logo-removebg-preview.png` in the top bar.
3. Move standalone wizard content into the left workspace rather than a centered card.
4. Keep `WizardEvidenceViewer` mounted on desktop.
5. Add field registry.
6. Build structured evidence objects from current extracted fields.
7. Add `document_id` to evidence.
8. Add row-level source controls and inline source strips.
9. Add shared `selectEvidence` controller.
10. Make `WizardEvidenceViewer` switch active document from selected evidence.
11. Expand evidence coverage to all extracted fields.
12. Parse or produce document identity for every evidence object.
13. Call server document resolver after packet parse, but treat field attribution as advisory until per-document candidates or structured evidence are verified.
14. Fix packet/resolver candidate duplication so resolver source documents are trustworthy.
15. Render conflict comparison from resolver output.
16. Add backend double-check pass for critical fields.
17. Surface double-check results and disagreements in the workspace.
18. Expand backend progress events with truthful field-discovery and warning events.
19. Render extraction log in left workspace.
20. Add timeline review with source and basis.
21. Fix manual mode final-create blocking.
22. Preserve original AI evidence after edits.
23. Add `Incomplete` draft behavior only when explicit save/resume support is implemented.
24. Expand frontend tests around row-click evidence, multi-document selection, double-check disagreements, and manual no-document create.
25. Add backend tests for progress events, evidence document id, resolver candidate attribution, double-check results, and geometry access.

---

## 17. Final Recommendation

Build in this order:

1. Layout and top bar.
2. Row-level source evidence for all fields.
3. Multi-document evidence correction and resolver candidate safety.
4. Double-check and quality gates.
5. Detailed extraction log.
6. Timeline and task review polish.
7. Manual fallback and draft resilience.

This order directly addresses the user's three priorities while protecting the existing working pieces. It also avoids the previous planning failure mode: every planned control maps to a current endpoint, a small endpoint extension, or a clearly phased future capability.
