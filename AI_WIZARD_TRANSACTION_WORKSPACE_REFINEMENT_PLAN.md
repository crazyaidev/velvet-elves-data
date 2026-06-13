# AI Wizard + Transaction Workspace Refinement Plan

**Compliance "Add document" with real upload, modal-first add flows, selector modernization, and wizard/workspace consistency.**

- Date: 2026-06-12
- Status: **IMPLEMENTED 2026-06-12** (Phases A-E + F docs, uncommitted - Jan commits). Suites at sign-off: frontend **244 passed** (31 files; 236 before + 8 new), backend **880 passed**, tsc/eslint/ruff clean. Review pass (§0.2) corrected ten issues (R1-R10); revision 2 (§0.3) added the ListedKit-parity **AI upload-verification loop** (G1-G5), reversing the original J2. **Implementation deviations (§0.4)**: one 3-line backend addition (doc_type on the requirement PATCH - needed by "Use AI type"; no migration), B2's `useAttachRequirementDocument` folded into the modal's resumable logic, and F4 screenshots deferred to Jake's environment review per the established wizard-round precedent.
- Scope: the New Transaction AI Wizard (`/transactions/new`) and the Transaction Workspace (`/transactions/:id`), plus the shared components both surfaces mount
- Author: Jan (drafted for Jake's review)

---

## 0. The feedback this plan answers

1. **"Add document" in the Compliance Checklist is superfluous as built.** It only records a name; there is no way to actually upload the document. It must become fully functional with real upload capability.
2. **The card-expansion UI for "Add document" is inconvenient.** It should be a modal.
3. **The selector UI is outdated and the dropdown arrow placement is wrong.** It must be modernized.
4. **General mandate:** every feature on these two surfaces must be practical and fully functional; resolve the inconsistencies between the AI Wizard and the Transaction page so the two form one seamless system; the result must be validatable entirely through the UI by real-estate professionals using a mouse and minimal typing.
5. **(Revision 2) AI must guide the user throughout, ListedKit-style.** At ListedKit, AI analyzes every uploaded document; if an incorrect document is uploaded, the system notifies the user to help them avoid errors. This plan must incorporate that guidance loop. (This also matches our own requirements §3.2: "After drop/upload, AI verifies what the document is, proposes a name…" - the requirement existed all along; only the documents manager honors it today.)

## 0.1 Grounding - what was reviewed before drafting

Project documents (velvet-elves-data):

| Document | What it contributed |
| --- | --- |
| `requirements.txt` §3 (Wizard), §3.2 (upload formats, 20 MB cap, global drag-drop), §6.4 (human approval of outbound email) | The functional contract the flows must honor |
| `SYSTEM_DESIGN.md` | Endpoint and entity vocabulary |
| `FRONTEND_UI_WORKFLOW_LOGIC.md` §4.5, §4.6, Workflow A | The canonical UI workflow spec (now drifted; amended in Phase F) |
| `STYLE_GUIDE.md` v2 Comfort Scale, §6.5 (Dialogs), §9.3 (Selects), §11 anti-patterns 13/15 | The binding design rules; **§9.3 already forbids native `<select>`** |
| `AI_WIZARD_LISTEDKIT_PARITY_GAP_CLOSURE_PLAN.md`, `TRANSACTION_PAGE_REDESIGN_SUPERIORITY_PLAN.md` | What the current implementation intended; section references (§5.5, W3, W6, T5) |
| `WIZARD_TESTING_GUIDE.md`, `TRANSACTION_WORKSPACE_TESTING_GUIDE.md` | The tester-facing scripts that must stay truthful |

Source code (all paths verified against the working tree on 2026-06-12):

- Frontend: `src/components/workspace/*` (all seven workspace components), `src/pages/transactions/TransactionWorkspacePage.tsx`, `src/components/wizard/WizardChecklistStep.tsx`, `WizardTimelineStep.tsx` (owner of `RuleEditor`), `ReviewTasksStep.tsx`, `WizardCommandBar.tsx`, `NewTransactionWizard.tsx` (commit path), `src/components/active-transactions/AddTaskModal.tsx`, `MissingDocumentsPanel.tsx`, `src/components/client/ClientUploadModal.tsx`, `src/components/ui/select.tsx`, `dialog.tsx`, hooks `useDocumentRequirements.ts`, `useDocuments.ts`, `useWizardApi.ts`, `useTransactionPlan.ts`, `src/types/enums.ts`
- Backend: `app/api/v1/document_requirements.py` (list / bulk / defaults / relink / patch), `app/api/v1/transaction_plan.py`, `app/api/v1/documents.py` (upload route, MIME allowlist), `app/api/v1/ai.py` (`/intake/classify`, parse endpoints), `app/api/v1/transactions.py` (history endpoint)

## 0.2 Review pass (2026-06-12) - corrections R1-R10

A second pass re-verified every workflow and logic claim against the source. Ten issues were found and **the plan body below is already corrected for all of them**; this section records what changed and why, so the reasoning is auditable.

- **R1 (logic, high) - the e-sign queue would have grabbed the wrong document.** The commit's e-sign block takes `linkedDocIds[0]` as the signing target (`NewTransactionWizard.tsx:3646`), and `linkedDocIds` is built from `state.documents` (parse targets, `:3479-3481`). The original C3 said modal-uploaded supporting files "join `linkedDocIds`", which could have made a supporting upload the e-sign target. Corrected: supporting documents live in their own `state.supportingDocuments` list; the commit links the **union** but the e-sign block and every parse/viewer flow keep reading the untouched parse-target list. The `matchedValid` guard checks the union.
- **R2 (logic, high) - the plan was inventing a second matching channel.** C1 originally added `uploaded_document_id` to `WizardUserRequirement`, duplicating the existing `requirementMatches` map that the commit already consumes (`manualMatches[r.client_key]`, `:3584`). Corrected: an upload-on-add records its document id in the **existing** `requirementMatches` map keyed by the new row's `client_key`; `state.supportingDocuments` (id + file name) exists only for display names, linking, and draft persistence. One matching channel, as before.
- **R3 (logic, high) - Script 1 told testers to verify something that cannot appear.** The Activity feed merges only audits with `entity_type="transaction"` (`transactions.py:1866`), while requirement actions audit as `entity_type="document_requirement"` (`document_requirements.py:_audit`) and uploads as `"document"`. Compliance events therefore never reach the Activity tab today. Corrected: Script 1 verifies through the Compliance and Documents tabs; surfacing requirement/document audits in `/history` is now optional backend item O2.
- **R4 (test claim, medium) - "Radix Select has working test patterns in the repo" was false.** The entire suite contains zero tests that *change* a Radix Select value (one read-only assertion exists, `WizardFlow.test.tsx:894`), `setup.ts` has none of the jsdom shims Radix needs, and the two `user.selectOptions` calls (`WizardFlow.test.tsx:2469, 2532`) drive exactly the native selects Phase A replaces. Corrected: new Phase A item A5 adds the jsdom enablement (`hasPointerCapture`/`releasePointerCapture`/`scrollIntoView` stubs) plus a tiny `selectVeOption(trigger, optionName)` test helper, and migrates the two `selectOptions` call sites.
- **R5 (fact, medium) - parsing is never a server-side side effect of upload.** `POST /documents/upload` (`documents.py:400-489`) stores, optionally classifies, audits - nothing else. Parsing is always a frontend-initiated `POST /ai/parse-document/:id`: the documents **manager** does it after its own uploads (`DocumentsModal.tsx:452`), but the Documents tab's inline upload does **not**, so its current toast "Parsing runs automatically" is false for that path. This confirms the verification loop needs zero backend work (the parse endpoint is the analyzer), and E4 makes the toast true by actually running it. (Note: revision 2 / §0.3 later reversed the original J2 "skip parse" recommendation; R5's factual finding stands unchanged.)
- **R6 (fact, low) - the accepted-format list was incomplete.** Backend `ALLOWED_MIME_TYPES` (`documents.py:98-107`) is PDF, DOC/DOCX, JPEG, PNG, WEBP, GIF, TXT, 20 MB cap, auto-compression over 10 MB. The modal copy and client-side validation now mirror that exact list.
- **R7 (gap, low-medium) - Save draft would have stranded supporting uploads.** The save-draft path links only `state.documents` (`NewTransactionWizard.tsx:3828-3836`). C4 now links `supportingDocuments` on Save draft too and persists them in the local/server draft JSON so resume keeps the attachment chips.
- **R8 (hardening note, low) - the server does not validate `matched_document_id`.** Neither bulk nor PATCH checks that the document exists or belongs to the transaction/tenant (verified in `document_requirements.py`); the wizard's client-side `matchedValid` guard exists precisely because of this. The new flows only pass server-issued in-session ids, so nothing breaks, but this is recorded as optional hardening O3.
- **R9 (UX detail, low) - the attach picker must not inherit the 12-row cap.** Today's inline match picker shows `documents.slice(0, 12)` (`ComplianceTab.tsx:333`). The Attach modal lists all documents with scroll plus a filter box, and rows whose `doc_type` is null default the upload pane's type to "Other".
- **R10 (E1 detail, low) - dialog-over-modal stacking.** `MissingDocumentsPanel` renders inside `DocumentsModal`, so `AddDocumentModal` must support the STYLE_GUIDE §6.5 over-modal z-index pattern (the `NewTransactionModal` / `DocumentSplitDialog` precedent).

Verified-sound during the same pass (no change needed): bulk schema accepts `doc_type` / `matched_document_id` / `source='user'` (`app/schemas/document_requirement.py:37-66`); `doc_type` is unconstrained TEXT in the DB (the migration CHECKs only direction/status/source); linking runs before the requirements bulk in the commit sequence (`:3479-3490` precedes `:3492+`); PATCH derives `status` from match/unmatch via `setdefault` (`document_requirements.py:362-367`); `brandedInputClass` exists in `NewTransactionWizard.tsx:4216` (A1 must export it or duplicate the class string once).

## 0.3 Revision 2 (2026-06-12) - the AI upload-verification loop (G1-G5)

New feedback after the review pass: ListedKit analyzes **every** uploaded document and notifies the user when the wrong document was uploaded - AI guides throughout. This revision incorporates that loop, and it **reverses the original decision J2** (which recommended skipping the parse on compliance uploads). Grounding facts, all source-verified:

- **G1 - the analyzer already exists and is frontend-initiated.** The background parse (`POST /ai/parse-document/:id?background=true`, polled via `useParseDocument`) extracts `document_type_detected` and persists everything to the document's `ai_extracted_data`. The documents manager already runs it after its own uploads (`DocumentsModal.tsx:452`) and already builds a type-match proposal from `document_type_detected` (the §8.6 confirm chip). Nothing new is invented; the loop is extended to the new flows.
- **G2 - `/ai/intake/classify` is NOT an analyzer.** Verified (`ai.py:1645-1694`): it only reads the document's **stored** `ai_extracted_data` from a prior parse (a fresh, never-parsed upload returns nothing useful, and its `suggested_doc_type` falls back to `doc.doc_type` - the value the user just set, which would be circular). So verification must run the parse, not classify; classify remains useful as a cheap read of an already-parsed document.
- **G3 - the verdict chip can survive reloads with zero new persistence.** `UploadedDocument.ai_extracted_data` is already on the documents list the Compliance tab fetches (`types/api.ts:678`), so a row's verification state is re-derivable forever: `matchedDoc.ai_extracted_data.document_type_detected` vs the row's expected type.
- **G4 - verification is advisory, never a gate.** Consistent with the system's architecture (AI proposes, the engine verifies, the human confirms - and conservative matching per correction C9): a mismatch never auto-rejects, never auto-detaches, never blocks Save. It notifies and offers one-click corrections.
- **G5 - already-parsed documents are not re-parsed.** Attach-by-pick of a document that has `ai_extracted_data` derives the verdict instantly with no new AI call; only fresh uploads trigger a parse. One parse per uploaded file is the same price the manager flow pays today.

Where it landed in the body: feedback item 5 (§0), finding F13 (§1.2), a new row in the inconsistency map (§1.3), design section §2.6, phase items B5 and C5, a reversed E4 parse rule, the rewritten J2, Script 1 step 6 and the new Script 5 (§5), a latency/cost risk (§7), and definition-of-done item 7 (§8).

## 0.4 Implementation notes (2026-06-12)

Phases A-E plus the Phase F document amendments are implemented (uncommitted). What shipped exactly as planned: VeSelect + SegmentedControl + the RuleEditor rebuild with unchanged aria contract (A); AddDocumentModal with add/attach modes, the extended hooks, the rebuilt ComplianceTab, `useDocVerification` + `DocVerificationChip` (B); `supportingDocuments` + `requirementMatches` wiring with `linkedDocIds` kept parse-targets-only and Save-draft linking (C); AddDeadlineModal on both timeline surfaces and AddTaskModal on the shared Dialog (D); MissingDocumentsPanel on the shared Attach modal, the verb sweep, AiEvidenceChip in the wizard checklist, and the classified-upload dialog + verification chips on the Documents tab with the quick action repointed (E).

Deviations, all justified:
1. **One small backend addition** (vs "no backend changes required"): `doc_type` accepted on `PATCH /document-requirements/:id` (schema + 3 lines in the router + test). The §2.6 "Use AI type" action must update the row's expected type, and the original endpoint had no channel for it. No migration - the column exists.
2. **B2's `useAttachRequirementDocument` was not created as a hook** - the resumable upload-then-write logic lives inside AddDocumentModal (it owns the retry state), and surfaces inject plain upload/save functions. Same behavior, less API surface.
3. **AddDocumentModal grew a third mode** (`upload`) for E4's classified-upload dialog instead of a separate component - one dropzone/validation/resume implementation everywhere.
4. **RuleEditor/DaysStepper moved to `shared/RuleFields.tsx`** (move-only; WizardTimelineStep re-exports) to break the import cycle the AddDeadlineModal would have created.
5. **F4 headless screenshots deferred to Jake's environment review**, consistent with the established wizard-round precedent (he reviews in his running env; the flows are covered by 14 new/updated integration tests).

New/updated tests: `RuleEditor.test.tsx` (no-native-select regression + Radix value change), `ComplianceAddDocument.test.tsx` (6 tests: upload-add with mismatch + Use AI type, no-file add, zero-doc attach via upload, attach-by-pick with no re-parse, resumable retry without re-upload, format validation), WizardFlow gains the supporting-upload commit/link/verification test and the migrated modal-add test, DocumentsModal's panel test drives the shared Attach modal, plus the A5 jsdom shims and `selectVeOption` helper.

---

## 1. Review findings

### 1.1 What already works end to end (verified - do not churn)

These were checked specifically because the mandate is "every feature practical and fully functional." They are functional and should not be rebuilt, only kept consistent:

- **Workspace shell and tabs** (`TransactionWorkspacePage.tsx`): plan aggregate header, status change with confirm + post-closing feedback, deep links (`?tab/?task/?requirement`), workspace-wide file drop routing to the Documents tab.
- **Cascade editing** (`CascadeEditor`, `CoreDatePickerInline`, `TermDaysEditor`): core-date and term edits preview server-side, apply with undo, audit entries land in Activity.
- **Command bar** (`WizardCommandBar` on the Timeline tab and in the wizard): LLM classifies into a closed intent schema, execution is deterministic with preview-then-apply and undo; backend `POST /ai/wizard-command` exists.
- **Quick actions** (`WorkspaceQuickActions`): Add Task, Upload Document, Sync Deadlines, Compose, Print, Ask AI - all wired to real mutations/modals.
- **Compliance row actions** other than Add: Waive + undo chip, un-waive, unmatch, edit with server-side rule re-resolution, Request by email (drafts into AI Email Review, nothing auto-sends, honoring requirements §6.4).
- **Evidence**: `AiEvidenceChip` with citation, confidence, page; persisted at the create boundary.
- **The stat band sparklines** render only real weekly series (no fabricated data).

So the system is not riddled with dead UI; the genuinely non-functional area is concentrated exactly where the feedback points: **the Add document flow and the form controls inside the shared rule editor**.

### 1.2 Defects and gaps

Each finding lists evidence, severity, and verdict (Complete = make functional; Restyle = visual/control fix; Unify = merge duplicated surfaces; Amend = documentation).

**F1 - "Add document" creates a name, not a document.** `ComplianceTab.tsx:481-519`: the header button toggles `adding` and renders the wizard's `RuleEditor` inline (name, description, due rule only). `useDocumentRequirements.ts:103-135` (`useAddRequirement`) sends neither a file, a `doc_type`, nor a `matched_document_id`, although the backend bulk endpoint accepts all of them (`document_requirements.py:177-188`). The user must then visit the Documents tab, upload, return, and click "Mark uploaded" - three surfaces for one job. *Severity: high. Verdict: Complete (Phase B).*

**F2 - The wizard checklist "Add document" has the same hole.** `WizardChecklistStep.tsx:491-514`: identical inline `RuleEditor`, no way to attach or upload a file even though the wizard already holds uploaded documents and `useWizardUploadDocument` (`useWizardApi.ts:37-53`) can upload unattached files at any time. *Severity: high. Verdict: Complete (Phase C).*

**F3 - Native `<select>` elements violate the project's own style guide.** `STYLE_GUIDE.md` §9.3: "**Never use a native `<select>`**" and §11 anti-pattern 15 repeats it. The shared Radix `<Select>` (`src/components/ui/select.tsx`, proper chevron inside the trigger) is already used in 20+ files - including `NewTransactionWizard.tsx` and even `ReviewTasksStep.tsx` itself - yet raw `<select>`s remain at:
- `WizardTimelineStep.tsx:327-347` (`RuleEditor`: direction + anchor) - this is the control rendered inside ComplianceTab, WizardChecklistStep, TimelineTab, and TasksTab, i.e. precisely the "outdated selector with the misplaced arrow" in the feedback (the OS default arrow sits at the far edge of an unstyled control and ignores the brand input styling)
- `ReviewTasksStep.tsx:140-157` (rule editor) and `:619-627` (related-document picker)
- `AddTaskModal.tsx:238-246` (completion method) and `:277-285` (assign to) - mounted from the workspace header quick action
*Severity: high (visual quality + guide violation). Verdict: Restyle (Phase A).*

**F4 - Add flows expand cards instead of opening modals.** The `adding && <RuleEditor/>` pattern appears in four places: `ComplianceTab.tsx:481`, `WizardChecklistStep.tsx:491`, `WizardTimelineStep.tsx:899-918` (Add deadline), `TimelineTab.tsx:641-668` (Add deadline). The expansion pushes the list down, scrolls the trigger out of view, and gives no focus trap or Escape handling. The style guide already defines the form-dialog pattern (§6.5, `max-w-lg`, 16 px radius). *Severity: high (explicit feedback). Verdict: Restyle to modal for ADD flows; keep inline editors for in-place row EDITS (Phases B-D).*

**F5 - "Mark uploaded" dead-ends when no document exists.** `ComplianceTab.tsx:325-352`: the match picker says "upload one from the Documents tab first." The one action the user actually wants at that moment (upload the file right here) is missing. *Severity: medium-high. Verdict: Complete - the attach flow gains an upload path (Phase B).*

**F6 - The same compliance actions live in two diverging UIs.** `ComplianceTab.tsx` (workspace tab) and `MissingDocumentsPanel.tsx` (inside `DocumentsModal`) both implement mark-uploaded, waive/un-waive, and chase-email with different markup and verbs. *Severity: medium. Verdict: Unify on shared pieces (Phase E).*

**F7 - Two different Add Task implementations.** `active-transactions/AddTaskModal.tsx` hand-rolls its overlay (`fixed inset-0 ... z-[600]`, line 150) with native selects, while `tasks/queue/AddTaskDialog.tsx` already does the same job on the shared `<Dialog>` + `<Select>`. The workspace mounts the outdated one. *Severity: medium. Verdict: Restyle AddTaskModal onto the shared primitives (Phase D); full consolidation listed as follow-up.*

**F8 - The workflow spec has drifted from the shipped workspace.** `FRONTEND_UI_WORKFLOW_LOGIC.md` §4.6 still specifies tabs "Overview | Tasks | Documents | Parties | Communications", while the live page ships "Timeline | Compliance | Documents | Tasks | People | Activity" (`TransactionWorkspacePage.tsx:63-70`); §4.5 still describes a 6-step wizard vs the current 5-phase stepper. Past testing breakdowns came exactly from this kind of drift. *Severity: medium (process). Verdict: Amend in lockstep (Phase F).*

**F9 - Legacy form controls beyond selects.** Native radio buttons for the rule/date mode toggle (`WizardTimelineStep.tsx:314-323` and `:189-208`) and a native checkbox for "Show document due dates" (`TimelineTab.tsx:404-411`). The in-app benchmark (Calendar page) expresses mode switches as segmented rounded-full pills with the active pill `bg-ve-orange text-white`. *Severity: low-medium. Verdict: Restyle (Phase A).*

**F10 - Verb and naming drift between the two surfaces.** Wizard: "Mark as uploaded", "Remove" (library rows commit as `waived`, `NewTransactionWizard.tsx:3606`); Workspace: "Mark uploaded", "Waive", "Unmatch". One mental model should hold: a checklist row may have a document **attached**; a row that does not apply is **waived**. *Severity: low. Verdict: Unify copy (Phase E).*

**F11 - Evidence chip markup duplicated.** `WizardChecklistStep.tsx:358-362` re-implements the AI chip inline while the workspace uses the shared `AiEvidenceChip`. *Severity: low. Verdict: Unify (Phase E).*

**F12 - Workspace uploads carry no type or label, and the upload toast lies.** `DocumentsTab.tsx:66-80` uploads file-only; its toast says "Parsing runs automatically", but parsing is never a server-side effect of upload (`documents.py:400-489`) - only the documents manager triggers a parse after its own uploads (`DocumentsModal.tsx:452`), so for this inline path the toast describes something that never happens (exactly the "UI claims without functionality" class the feedback targets). Meanwhile `ClientUploadModal.tsx` already demonstrates the proper pattern (Dialog + dropzone + type Select + optional label + `useUploadDocument`). The Upload quick action currently just opens the manager modal. *Severity: medium. Verdict: Complete - route the explicit Upload buttons through the new upload modal, fix the toast copy to state what actually happened (Phase E4).*

**F13 (revision 2) - AI verifies uploads only inside the documents manager.** Requirements §3.2 says "After drop/upload, AI verifies what the document is, proposes a name…", and the manager honors it: parse after upload (`DocumentsModal.tsx:452`), then a user-confirmed type-match proposal from `document_type_detected`. But every other upload path is unguided - the Documents tab inline upload/drop, and (without this revision) the new Add/Attach Document modals would have joined them. ListedKit analyzes every upload and warns on a wrong document; we have all the machinery (G1-G3) and use it on one surface. *Severity: medium-high (parity + own-requirements gap). Verdict: Complete - the §2.6 verification loop runs on every upload path (Phases B5, C5, E4).*

### 1.3 The wizard / workspace inconsistency map

| Concern | AI Wizard today | Workspace today | Target (one system) |
| --- | --- | --- | --- |
| Add checklist document | Inline RuleEditor, no file | Inline RuleEditor, no file | One shared **Add Document modal** with upload, used by both |
| Attach a file to a row | "Mark as uploaded" picker (existing wizard docs only) | "Mark uploaded" picker (existing deal docs only, dead-end when none) | One shared **Attach Document modal**: pick existing OR upload new |
| Add deadline | Inline RuleEditor | Inline RuleEditor | One shared **Add Deadline modal** |
| Rule editing controls | Native selects + radios | Same (same component) | Shared `RuleFields` on Radix `<Select>` + segmented pills |
| Add task | n/a (review step) | Custom-overlay AddTaskModal, native selects | AddTaskModal rebuilt on `<Dialog>` + `<Select>` |
| Verbs | Mark as uploaded / Remove | Mark uploaded / Waive / Unmatch | Attach document / Waive / Detach |
| AI evidence chip | Inline span markup | `AiEvidenceChip` | `AiEvidenceChip` everywhere |
| AI checks the uploaded file | Only intake docs (packet parse) | Only inside the documents manager | Every upload, every path: §2.6 verification chip |

---

## 2. Target design

### 2.1 The Add Document modal (the centerpiece)

One component, two entry modes, shared between wizard and workspace. Model: `ClientUploadModal.tsx` (Dialog + dropzone + Select), extended with the due-rule block.

**Mode 1 - "Add document" (from the checklist header).** Creates a checklist requirement, optionally satisfying it immediately with a file.

```
+----------------------------------------------------------+
| ✦ COMPLIANCE                                        [X]  |
| Add a document to the checklist          (serif, 20px)   |
| Track a document this deal must produce. Attach the      |
| file now if you already have it.                         |
|                                                          |
| [ Drag the file here, or click to browse ]               |
|   PDF, DOC/DOCX, JPEG, PNG, WEBP, GIF, TXT · up to 20 MB |
|   (file is optional)                                     |
|   -> after pick: [file chip: name · size · remove]       |
|                                                          |
| Document name *        [ Septic inspection report      ] |
|   (auto-filled from the file name, Title Case, editable) |
| Document type          [ Inspection Report          v ]  |
|   (Radix Select, DOCUMENT_TYPE_LABELS, default "Other")  |
|                                                          |
| Due                    ( None | Relative rule | Date )   |
|   Relative: [-] [3] [+] days  [after v] [Closing Date v] |
|   Date:     [ date input ]                               |
|                                                          |
| + Add a description (collapsed by default)               |
|                                                          |
|              [ Cancel ]  [ Add to checklist ]            |
+----------------------------------------------------------+
```

Behavior:
- **With a file** (the primary path the feedback demands): upload first, then create the requirement already matched. Workspace: `useUploadDocument({file, transactionId, docType, docLabel: name})` then the bulk endpoint with `matched_document_id` + `doc_type` set - the row is born in the **Uploaded** group with the green "Matched: <file>" line. Backend needs nothing new: `document_requirements.py:186-188` already derives `status='uploaded'` from `matched_document_id`.
- **Without a file**: requirement only (status `missing`), exactly today's behavior but now an explicit, secondary choice. The success toast offers the logical next step: "Request it by email" (opens the existing party picker). This path stays because real checklists track obligations the agent does not yet hold (decision J1).
- Primary button label switches with state: "Upload & add to checklist" / "Add to checklist".
- Validation mirrors the backend exactly (R6): `ALLOWED_MIME_TYPES` = PDF, DOC/DOCX, JPEG, PNG, WEBP, GIF, TXT (`documents.py:98-107`), 20 MB cap (the server auto-compresses over 10 MB); inline `text-ve-red-text` error, never a toast-only failure.
- Failure handling is honest and resumable: if upload succeeds but the requirement call fails, the modal stays open with the file chip marked "Uploaded ✓" and retries only the requirement creation (the document is already safely visible in the Documents tab either way).
- Every uploaded file immediately enters the §2.6 AI verification loop (background, non-blocking): the new row carries the `checking` chip, then `confirmed` or the mismatch warning with one-click corrections.

**Mode 2 - "Attach document" (from a missing row; replaces the dead-end match picker).**

```
| ✦ COMPLIANCE                                             |
| Attach the Septic Inspection Report                      |
|                                                          |
| ( Pick an uploaded file | Upload a new file )  <- pills  |
|  - Pick: radio list of ALL the deal's unmatched          |
|    documents (label · type · date), scrollable with a    |
|    filter box - no 12-row cap like today's picker (R9)   |
|  - Upload: the same dropzone; type pre-set from the      |
|    row's doc_type ("Other" when the row has none, R9);   |
|    name pre-filled from the row name                     |
|                                                          |
|              [ Cancel ]  [ Attach ]                      |
+----------------------------------------------------------+
```

- Pick path: `PATCH /document-requirements/:id { matched_document_id }` (status flips to `uploaded` server-side). An already-parsed pick gets its §2.6 verdict instantly (no new AI call, G5); an unparsed pick enters the loop.
- Upload path: upload with the row's `doc_type`/name, then the same PATCH, then the §2.6 verification loop - this is the "you attached the wrong file" guard the feedback asks for.
- The F5 dead-end disappears: zero documents on the deal simply means the picker opens on the Upload pane.

**Wizard flavor of both modes (Phase C).** Same component, different adapters: files upload **unattached** via `useWizardUploadDocument` (no transaction exists yet). Two pieces of state, with strictly separated jobs (R1/R2):
- Matching always lands in the **existing** `requirementMatches` map (`client_key -> document id`) - the single channel the commit already consumes at `NewTransactionWizard.tsx:3584`. No second matching field is introduced.
- A new `state.supportingDocuments: Array<{ id, fileName }>` records what was uploaded, purely for display names in the checklist rows, for linking at commit/save-draft, and for draft persistence. It is deliberately **not** part of `state.documents`, so the parse pipeline, the evidence viewer, the `_wizard_document_ids` metadata, and the e-sign target selection never see supporting files.

Everything becomes real at commit (see 3.C3).

### 2.2 `RuleFields` v2 - the shared rule editor internals

`RuleEditor` (exported from `WizardTimelineStep.tsx`, consumed by ComplianceTab, WizardChecklistStep, TimelineTab, TasksTab) keeps its name, props, and aria-labels (test stability), but its internals change:

- Direction and anchor become the shared Radix `<Select>` with the branded trigger (`STYLE_GUIDE.md` §9.3: trigger styling = `brandedInputClass`; chevron is part of the trigger component, which resolves the "down arrow in the wrong place" complaint structurally rather than cosmetically).
- The "Relative rule / Specific date" radios become a **segmented pill control** (new tiny shared component, rounded-full container, active pill `bg-ve-orange text-white`, the Calendar-page voice). Same for `TermRowEditor`'s "Days after / Specific date".
- The `DaysStepper` stays as-is: it is already the mouse-first ideal.
- Type sizes audit to the v2 Comfort Scale (labels 12.5 px, inputs 15 px, nothing under 12 px).
- The same component is rendered in two containers: inside the new modals for ADD, and inline (as today) for row EDIT. In-place editing of an existing row is a legitimate inline pattern (the row provides context); only creation moves to modals.

### 2.3 One mental model for compliance rows

A requirement row has exactly three states and the verbs say so on both surfaces:

| State | Row affordances (both surfaces) |
| --- | --- |
| `missing` | **Attach document** (modal, pick-or-upload) · **Request by email** · **Waive** · Edit |
| `uploaded` | green "Matched: <file>" · **Detach** (today's "Unmatch") |
| `waived` | **Un-waive** |

"Mark uploaded / Mark as uploaded" disappears as a verb: it described the implementation (set a status) rather than the action (attach the document).

### 2.4 Modal vs inline - the decision rule (recorded for future work)

- **Create something new** -> modal (`<Dialog>`, form variant, `max-w-lg`, 16 px radius): Add document, Attach document, Add deadline, Add task.
- **Edit a thing in place** -> inline expansion under the row (rule editor, term stepper) - context is the row itself.
- **Pick-one-from-few with no fields** -> popover/dropdown (status menus, date popovers).

This rule goes into the STYLE_GUIDE (Phase F) so the next surface doesn't reinvent the choice.

### 2.5 Visual spec (harmonizing, not inventing)

- Dialog: `rounded-2xl` 16 px, `shadow-premium`, header = mono kicker (`✦ COMPLIANCE`, 12 px / 1.5 px tracking) over serif 20 px title over 13.5 px muted description; body padding 24/24/20 (`STYLE_GUIDE.md` §5, §6.5); footer right-aligned Cancel (ghost) + primary (`bg-ve-orange hover:bg-ve-orange-dark`).
- Dropzone: dashed `border-ve-orange-border` on `bg-ve-orange-soft/15`, drag-over deepens to `bg-ve-orange-soft/40` (the page-level drop overlay voice from `TransactionWorkspacePage.tsx:278-284`); icon `UploadCloud`; the file chip uses the document-row anatomy from DocumentsTab.
- Selects: shared trigger class identical to `brandedInputClass`; menu items 15 px; no bespoke arrows.
- All sizes obey the v2 Comfort Scale hard floor (>= 12 px); accessibility per §12 (Dialog Title + Description, Escape closes, focus trap is free with Radix).

### 2.6 AI verification of every upload (revision 2 - the ListedKit guidance loop)

Every file that enters the system through the flows in this plan gets analyzed, and the user is told when something looks wrong. One shared piece: a **verification chip** that lives on the compliance row (or the document row, for plain uploads), driven by the existing background parse.

**Lifecycle** (all states use the champagne AI accent per STYLE_GUIDE §10; one shimmer for in-progress per Comfort Scale v2.4):

| State | Chip | When |
| --- | --- | --- |
| `checking` | `✦ AI is checking this document…` (shimmer) | Upload completed; background parse polling (`useParseDocument`, the manager's exact mechanism) |
| `confirmed` | quiet green `✓ AI confirmed · Inspection Report` (+ confidence when present) | `document_type_detected` matches the expected type |
| `mismatch` | amber `AI read this as Purchase Agreement - expected Inspection Report` + actions | Detected and expected types both present and different |
| `info` | `✦ AI read this as Pre-Approval` + "Use this type" | A type was detected but nothing was expected (row/modal had no type) - guidance, not a warning |
| `unverified` | muted `AI couldn't read this file` | Parse failed or no text layer - honest, no action required |

**Mismatch actions, by context:**
- Mode 1 (add-with-upload): **Use AI type** (PATCHes the document's `doc_type` and the requirement's `doc_type` to the detected value) · **Keep my type** (dismisses; the user is the authority) · **Remove file** (detaches; the requirement stays, back to `missing`).
- Mode 2 (attach) and manager/Documents-tab uploads: **Keep anyway** · **Detach & re-attach** (reopens the Attach modal).

**Rules (G4/G5):**
- Advisory only - a mismatch never blocks Save, never auto-detaches, never auto-rejects. The modal closes as soon as the upload and the requirement write succeed; the chip continues on the row.
- Comparison is the deterministic, normalized `docTypeMatches(detected, expected)` (extracted as a shared helper from the manager's existing §8.6 proposal logic) - no LLM in the comparison, only in the extraction.
- No re-parsing: a picked document that already has `ai_extracted_data` gets its verdict computed instantly; only fresh uploads trigger a parse (G5).
- Reload-safe with zero new persistence: the chip re-derives from `UploadedDocument.ai_extracted_data.document_type_detected` vs the requirement's `doc_type`, both already on the data the tabs fetch (G3).
- Wizard isolation: a supporting document's parse result feeds ONLY its verification chip - it is never merged into the wizard's extraction state, proposals, or evidence viewer (it is not an intake document; R1's separation holds).
- Scope boundary: the manager's richer post-parse flow (transaction field-update suggestions) stays exclusive to the manager; the verification loop checks document identity only.

---

## 3. Implementation phases

Ordered so every phase ships a UI-verifiable improvement and the suites stay green between phases. No backend migrations anywhere in this plan.

### Phase A - Form-control modernization (the selector fix)

| # | Change | Files |
| --- | --- | --- |
| A1 | Export a `brandedSelectTriggerClass` (or a thin `VeSelect` wrapper) so every Select trigger matches `brandedInputClass` exactly once | `src/components/ui/select.tsx` or a small `src/components/shared/VeSelect.tsx` |
| A2 | New `SegmentedControl` (rounded-full pills, `role="radiogroup"`, active = `bg-ve-orange text-white`) | new `src/components/ui/segmented-control.tsx` |
| A3 | Rebuild `RuleEditor` + `TermRowEditor` internals: Radix Selects, segmented mode toggle, Comfort-Scale sizes. Keep exported names, props, ids, and aria-labels (`"Before or after"`, `"Relative to"`, `dl-name-*`) | `WizardTimelineStep.tsx` |
| A4 | Replace the native selects in `ReviewTasksStep.tsx` (rule editor + related-document picker) and the checkbox in `TimelineTab.tsx:404-411` (becomes a pill toggle) | `ReviewTasksStep.tsx`, `TimelineTab.tsx` |
| A5 | Test enablement for Radix Select value changes (R4 - **no precedent exists in the suite today**): add the standard jsdom shims to `setup.ts` (`Element.prototype.hasPointerCapture` / `releasePointerCapture` / `scrollIntoView` no-ops), add a `selectVeOption(user, triggerLabel, optionName)` helper (click trigger, click `role="option"`), and migrate the only two `user.selectOptions` call sites (`WizardFlow.test.tsx:2469` and `:2532`) to it | `src/tests/setup.ts`, `src/tests/test-utils.tsx`, `WizardFlow.test.tsx` |

Tests: queries are unaffected (aria-labels stay identical; Radix puts `aria-label` on the trigger, so `getByLabelText` / `getByRole('combobox', { name })` keep working - the suite already asserts on one Radix trigger this way at `WizardFlow.test.tsx:894`). What changes is only the **value-change interaction**, covered by A5. Add one regression test asserting `RuleEditor` renders no native `select` element.

Proof for testers: every dropdown in the wizard timeline/checklist steps and the workspace Compliance/Timeline tabs now looks like every other dropdown in the app (chevron inside the bordered control, branded focus ring).

### Phase B - The Add/Attach Document modal in the workspace

| # | Change | Files |
| --- | --- | --- |
| B1 | New `AddDocumentModal` implementing §2.1 (both modes). Wizard/workspace differences injected via props (`onUpload`, `documents`, `defaultDocType`), so the component owns layout and validation only | new `src/components/documents/AddDocumentModal.tsx` |
| B2 | Extend `useAddRequirement` to send `doc_type` and `matched_document_id` (backend bulk already accepts both); add a `useAttachRequirementDocument` convenience that wraps upload + PATCH with the resumable-failure behavior from §2.1 | `useDocumentRequirements.ts` |
| B3 | ComplianceTab integration: header "Add document" opens the modal (mode 1); row "Mark uploaded" becomes "Attach document" opening mode 2; the inline match panel (`:325-352`) and inline add (`:481-519`) are deleted; "Unmatch" relabels "Detach" | `ComplianceTab.tsx` |
| B4 | The workspace-wide drop target keeps routing to Documents (unchanged); when the AddDocumentModal is open, a drop lands in the modal's dropzone | `TransactionWorkspacePage.tsx`, `AddDocumentModal.tsx` |
| B5 | The §2.6 verification loop (F13): new `useVerifyUploadedDocument` hook (wraps `useParseDocument` background polling; skips documents that already have `ai_extracted_data`, G5), shared `docTypeMatches(detected, expected)` helper extracted from the manager's §8.6 proposal logic, and a `DocVerificationChip` component rendering the five §2.6 states with the per-context mismatch actions. ComplianceTab rows derive their persistent verdict from `matchedDoc.ai_extracted_data` (G3) | new `src/hooks/useDocVerification.ts`, new `src/components/documents/DocVerificationChip.tsx`, `ComplianceTab.tsx` |

Tests: integration tests for both modes (upload-then-add lands in Uploaded group; add-without-file lands in Open; attach-by-pick; attach-by-upload; the 20 MB / format validation; the upload-ok-requirement-fail retry). Verification tests: mismatch chip appears when the stubbed parse returns a different `document_type_detected`; "Use AI type" patches both the document and the requirement; "Detach & re-attach" reverts the row to missing; already-parsed pick renders a verdict with no parse request (assert via msw call count); parse failure renders `unverified` and nothing blocks.

Proof for testers (mouse-only): Compliance tab -> Add document -> drop a PDF -> name auto-fills -> pick type -> "Upload & add to checklist" -> the row appears under Uploaded with the file name, and the file is visible in the Documents tab. Total typing: zero (or one name edit).

### Phase C - Wizard checklist parity (same modal before the transaction exists)

| # | Change | Files |
| --- | --- | --- |
| C1 | New wizard state `supportingDocuments: Array<{ id, fileName }>` (R2 - **not** a field on `WizardUserRequirement`, and **not** part of `state.documents`, so the intake parse pipeline, evidence viewer, and e-sign flows never see these files, R1). The checklist step's "Add document" opens `AddDocumentModal` (wizard adapter: `useWizardUploadDocument`, file uploads unattached). An upload-on-add records `requirementMatches[newRow.client_key] = doc.id` - the existing single matching channel | `wizardTypes.ts`, `WizardChecklistStep.tsx`, `NewTransactionWizard.tsx` (state) |
| C2 | Row-level "Mark as uploaded" becomes "Attach document" (mode 2): pick from the wizard's persisted documents **or** upload a new unattached file (which also joins `supportingDocuments`); either way the selection lands in the existing `requirementMatches` map; the row's display name resolves from `state.documents` first, then `supportingDocuments` | `WizardChecklistStep.tsx` |
| C3 | Commit wiring in `NewTransactionWizard.tsx`: link the **union** of parse-target ids and `supportingDocuments` ids (the existing `linkDocMut` loop, which already runs before the requirements bulk, `:3479-3490`); the `matchedValid` guard (`:3591-3593`) checks that union. **The `linkedDocIds` array itself stays parse-targets-only** so the e-sign block (`:3646`, takes `linkedDocIds[0]`) and `_wizard_document_ids` metadata are untouched (R1). User-row bulk items carry `matched_document_id` and `doc_type` | `NewTransactionWizard.tsx` |
| C4 | Draft persistence: `supportingDocuments` rides the localStorage/server draft JSON so refresh-resume keeps the attachment chips (the files are already persisted server-side); **Save draft also links supporting documents** to the Incomplete shell - today's save path links only `state.documents` (`:3828-3836`, R7) | `NewTransactionWizard.tsx` |
| C5 | The §2.6 verification loop in the wizard (F13/G-series): every supporting upload runs the same `useVerifyUploadedDocument` + `DocVerificationChip` on its checklist row. **Isolation rule:** the parse result feeds ONLY the chip - it is never merged into the wizard's extraction state, proposals, double-check, or evidence viewer (a supporting document is not an intake document). Mismatch actions are the mode-appropriate set from §2.6 | `WizardChecklistStep.tsx` |

Tests: WizardFlow additions - add-with-upload shows the "Uploaded · <name>" chip on the new row; commit produces a bulk payload whose user row carries the matched id; the commit's link calls include the supporting document while the e-sign payload (when queued) still targets the parse document (R1 regression test); resume keeps the chip; Save draft links the supporting document (R7); a supporting upload whose stubbed parse detects a different type shows the mismatch chip while the wizard's extracted fields remain untouched (C5 isolation regression).

Proof for testers: in the wizard's Compliance step, click Add document, attach the HOA paperwork you already have, finish the wizard - the workspace Compliance tab shows that row already green under Uploaded. One continuous system, no re-doing work after creation.

### Phase D - Modal parity for deadlines and tasks

| # | Change | Files |
| --- | --- | --- |
| D1 | New `AddDeadlineModal` (thin Dialog wrapper around `RuleFields` with name field); replaces the inline add at `WizardTimelineStep.tsx:899-918` and `TimelineTab.tsx:641-668`. Save behavior unchanged (wizard: `onAddDeadline`; workspace: `useCreateDeadlineTask`, server-resolved) | new `src/components/shared/AddDeadlineModal.tsx`, both timeline files |
| D2 | `AddTaskModal` rebuilt on the shared `<Dialog>` (replacing the hand-rolled `z-[600]` overlay) with shared Selects for completion method and assignee; the AI-approach suggestions block is kept as-is (it is functional) | `AddTaskModal.tsx` |
| D3 | Row EDIT flows stay inline everywhere (already fixed visually by Phase A) | n/a |

Tests: existing AddTaskModal tests migrate to Dialog queries; deadline-modal happy paths on both surfaces.

### Phase E - One compliance system, one vocabulary

| # | Change | Files |
| --- | --- | --- |
| E1 | `MissingDocumentsPanel` (DocumentsModal) adopts `AddDocumentModal` mode 2 for its mark-uploaded picker and the unified verbs, deleting its bespoke picker markup. Because the panel renders **inside** `DocumentsModal`, `AddDocumentModal` must support the STYLE_GUIDE §6.5 dialog-over-modal z-index pattern (the `NewTransactionModal` / `DocumentSplitDialog` precedent, R10) | `MissingDocumentsPanel.tsx`, `AddDocumentModal.tsx` |
| E2 | Verb sweep per §2.3 across both surfaces + the wizard ("Attach document", "Detach", "Waive"); wizard library rows keep "Remove" pre-create but the tooltip states "Removed library items are recorded as waived" (matches the actual commit behavior at `NewTransactionWizard.tsx:3606`) | `ComplianceTab.tsx`, `WizardChecklistStep.tsx`, `MissingDocumentsPanel.tsx` |
| E3 | `WizardChecklistStep` swaps its inline AI-chip markup for the shared `AiEvidenceChip` | `WizardChecklistStep.tsx`, `AiEvidenceChip.tsx` (export location maybe moves to shared) |
| E4 | The Documents tab "Upload" button and the header "Upload Document" quick action open a slim upload dialog (file + type + label, same dropzone) instead of a bare file input; drag-drop anywhere stays instant-upload (requirements §3.2 "global drag-and-drop"). **One parse rule everywhere (revision 2, reverses the original draft):** every upload on every path enters the §2.6 verification loop - the new dialogs, the inline Documents-tab upload, and page drops included. This finally makes the existing toast "Parsing runs automatically" TRUE (R5 found it false for the inline path); document rows in the Documents tab show the same `DocVerificationChip`, with mismatch compared against the type the user picked (or `info` guidance when none was picked). The manager keeps its richer parse-confirm flow on top | `DocumentsTab.tsx`, `TransactionWorkspacePage.tsx` |

### Phase F - Spec, guides, verification (the anti-drift phase)

| # | Change | Files |
| --- | --- | --- |
| F1 | Amend `FRONTEND_UI_WORKFLOW_LOGIC.md`: §4.6 rewritten to the shipped tab set (Timeline, Compliance, Documents, Tasks, People, Activity) including the Compliance tab's full action inventory and the new modal inventory; §4.5 updated to the 5-phase stepper with the checklist step's upload capability; Workflow A cross-references updated | `FRONTEND_UI_WORKFLOW_LOGIC.md` |
| F2 | `STYLE_GUIDE.md`: add the §2.4 modal-vs-inline decision rule and cite `AddDocumentModal` as the canonical upload-dialog reference | `STYLE_GUIDE.md` |
| F3 | Testing guides: new mouse-only sections - WIZARD guide gains "Add a checklist document with a file mid-wizard"; WORKSPACE guide gains "Upload a compliance document in one motion", "Attach an existing file to a requirement", and "The AI catches a wrong document" (Script 5); stale "Mark uploaded" wording replaced everywhere | `WIZARD_TESTING_GUIDE.md`, `TRANSACTION_WORKSPACE_TESTING_GUIDE.md` |
| F4 | Visual verification before sign-off: render + headless Chrome screenshots of (1) the Add Document modal both modes, (2) the restyled RuleFields inline edit, (3) the wizard checklist step with an attached row - compared against the Calendar-page benchmark voice; full frontend (236+) and backend (880) suites green; tsc/eslint/ruff clean | screenshots under `C:\Projects\_shots\` |

---

## 4. Backend assessment

**No backend changes are required for any phase.** Verified against source:

- Upload: `POST /api/v1/documents/upload` takes multipart `file` + optional `transaction_id`, `doc_type`, `doc_label` (used by `useUploadDocument` and `useWizardUploadDocument` today).
- Create-with-match: `POST /transactions/:id/document-requirements/bulk` items accept `doc_type`, `matched_document_id`, rule fields; status derives to `uploaded` when matched (`document_requirements.py:184-188`); due rules resolve server-side; idempotent per `commit_id`.
- Attach/detach: `PATCH /document-requirements/:id` handles `matched_document_id` and `unmatch` with correct status transitions (`:362-367`); audit entries are written.
- Wizard linking: `PATCH /documents/:id { transaction_id }` already links unattached uploads at commit.

Optional backend items (explicitly **not** required by any phase, recorded to prevent re-derivation):

- **O1 - composite `POST /document-requirements/:id/upload`** doing upload+match server-side would remove the two-call window. The client-side resumable handling in §2.1 makes the window harmless (worst case: an uploaded, unmatched document that is fully visible in the Documents tab). Recommend skipping.
- **O2 - surface compliance events in the Activity feed.** `GET /transactions/:id/history` merges only audits with `entity_type="transaction"` (`transactions.py:1866`); requirement actions audit as `entity_type="document_requirement"` and uploads as `"document"`, so neither appears in the Activity tab today (R3). If Jake wants the Activity tab to answer "who added/waived/attached what", the history endpoint needs to merge those two entity types (requirement audits are findable: bulk/defaults audit with `entity_id = transaction_id`, patch audits need a lookup through the transaction's requirement ids). Small, isolated, worth doing; until then the testing scripts verify through the Compliance/Documents tabs instead.
- **O3 - validate `matched_document_id` server-side.** Neither bulk nor PATCH verifies the document exists or belongs to the transaction/tenant (R8); the wizard's client-side `matchedValid` guard exists because of this. The new flows pass only server-issued in-session ids, so this is hardening, not a blocker.

## 5. Mouse-only validation scripts (tester-facing summary)

Script 1 - "I just received the septic report" (workspace, the headline fix):
1. Open any active deal -> Compliance tab.
2. Click **Add document**.
3. Drag the PDF into the modal (or click to browse).
4. Confirm the auto-filled name; pick "Inspection Report" from the type dropdown.
5. Click **Upload & add to checklist**.
6. Verify: row appears under **Uploaded** with "Matched: <file>", the "✦ AI is checking this document…" chip appears and settles into "✓ AI confirmed · Inspection Report", the open/uploaded counts in the card header update, and the Documents tab lists the file. Typing required: none. (The Activity tab does NOT log compliance events today - see optional item O2; do not send testers there for this, R3.)

Script 2 - "The lender still owes me the appraisal":
1. Compliance tab -> Add document -> type the name "Appraisal" (the one unavoidable typing), set Due = Relative rule, 10 days after Date of Acceptance, no file.
2. Save; the row appears under Open with the due chip.
3. Click **Request by email** on the row, pick the loan officer; verify the draft lands in AI Email Review (nothing sends).
4. Later: click **Attach document** on the row -> Upload a new file pane -> drop the file -> Attach. Row turns green.

Script 3 - "Wizard intake with paperwork in hand":
1. Run the wizard to the Compliance step.
2. Add document -> attach the HOA file in the modal -> finish the wizard.
3. Open the created deal's Compliance tab: the HOA row is already Uploaded and the file is on the deal.

Script 4 - regression sweep: every dropdown across the wizard steps and workspace tabs shows the branded control with the chevron inside the field; Escape closes every new modal; all previous compliance actions (waive/undo, edit rule, cascade) behave exactly as in the existing testing guides.

Script 5 - "I attached the wrong file" (revision 2, the ListedKit guard):
1. Compliance tab -> on the "Septic Inspection Report" row click **Attach document** -> Upload a new file pane -> drop a purchase agreement PDF on purpose -> Attach.
2. The row turns green immediately (the attach is never blocked), with the "✦ AI is checking this document…" chip.
3. Within a minute the amber warning appears: "AI read this as Purchase Agreement - expected Inspection Report".
4. Click **Detach & re-attach**; the row returns to Open and the Attach modal reopens; drop the correct file; the chip settles into "✓ AI confirmed".
5. Also verify the keep path: repeat with a correctly-typed file the AI cannot read (a photo of a blank page) - the chip says "AI couldn't read this file" and nothing nags further. Typing required: none.

## 6. Decisions needed (Jake)

- **J1** - Keep the no-file "checklist-only" add as a secondary path in the modal (recommended: yes; tracking obligations you do not yet hold is the normal TC workflow).
- **J2 (rewritten in revision 2 - the original "skip parse" recommendation is REVERSED)** - Every upload on every path runs the §2.6 AI verification loop (background parse, type check, advisory chip), ListedKit-style. The parse result is used for document-identity verification and stored extraction only; compliance uploads do NOT auto-apply transaction field updates (that richer flow stays exclusive to the documents manager). Cost: one parse per fresh upload, the same price the manager flow already pays; already-parsed documents are never re-parsed (G5). Still zero backend work (R5/G1). Recommended: yes.
- **J3** - Optional polish: dropping a file directly onto a missing requirement row attaches it (recommended: defer; the modal covers the need).
- **J4** - Follow-up consolidation of `AddTaskModal` and the queue's `AddTaskDialog` into one component (recommended: separate follow-up after this plan).
- **J5** - The remaining native selects on out-of-scope pages (DocumentsPage, AnalyticsPage, TransactionListPage, AdminUsersListPage, VendorListPage, VendorTemplatesPage, TaskTemplateListPage, CommunicationsFilters, EmailVendorFlow, IntakeConfirmationModal, UploadLegalPacketModal, PortalSections, M53Editors) - schedule as a one-pass style sweep after Phase A proves the pattern (recommended).

## 7. Risks and mitigations

- **Test churn in WizardFlow (67 tests).** Mitigated by keeping `RuleEditor`'s exported API and aria-labels byte-identical; only its internals change. Queries survive unchanged, but **value-change interactions need new plumbing** - the suite has no Radix Select value-change precedent and `setup.ts` lacks the jsdom shims, so Phase A5 adds the shims, a `selectVeOption` helper, and migrates the two `selectOptions` call sites (R4).
- **Two-call upload+create window (no backend transaction).** Mitigated by the resumable modal state (§2.1); the orphan case is an honestly visible uploaded document, never silent data loss.
- **Wizard commit ordering and e-sign targeting.** The `matchedValid` guard drops matches for unlinked documents; C3 sequences link-before-bulk over the union of parse targets and supporting documents while keeping `linkedDocIds` parse-targets-only so the e-sign block's `linkedDocIds[0]` (`:3646`) can never pick a supporting file (R1). Both behaviors get dedicated tests.
- **Verification latency and cost (revision 2).** A parse can take tens of seconds and costs one LLM call per fresh upload. Mitigations: it is fully background and advisory (the user's flow never waits, G4), already-parsed documents are never re-parsed (G5), and the `unverified` state is an honest terminal state - a failed parse never retries in a loop and never blocks. If volume becomes a concern, a cheaper classification-only prompt can later replace the full parse behind the same `useVerifyUploadedDocument` interface without UI changes.
- **Stale verdicts after type edits.** The chip re-derives from current data (G3), so editing a requirement's type recomputes the verdict client-side; no cached state to invalidate.
- **Scope creep.** Phases E4/J3/J5 are the pressure valves: each is separable without weakening the headline fixes (F1-F5). The verification loop (B5/C5) is deliberately one shared hook + one chip component so it cannot fork per surface.

## 8. Definition of done

1. No native `<select>`, radio-as-mode-toggle, or hand-rolled overlay remains anywhere the wizard or workspace renders.
2. "Add document" on both surfaces produces a real, uploaded, matched document in one modal flow; the no-file path is an explicit secondary choice.
3. No compliance action dead-ends ("upload somewhere else first" no longer exists).
4. One verb set across wizard, workspace, and documents manager.
5. `FRONTEND_UI_WORKFLOW_LOGIC.md`, both testing guides, and the STYLE_GUIDE reflect the shipped reality.
6. Full suites green (frontend 236+ and new tests, backend 880), tsc/eslint/ruff clean, screenshots reviewed against the Calendar benchmark.
7. Every upload path (Add Document modal, Attach modal, wizard supporting uploads, Documents tab button, page drop) runs the AI verification loop and shows the §2.6 chip; uploading a deliberately wrong document produces the mismatch warning with working one-click corrections (Script 5 passes end to end).
