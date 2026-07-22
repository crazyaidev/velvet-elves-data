# Transaction Processing Alignment with the Four-Stage AI Wizard - Plan

**Status:** **IMPLEMENTED 2026-07-22** (uncommitted; Jan commits). All 7 phases built and green: backend 95 tests (79 existing suites + 16 new in `test_intake_handoff_alignment.py`) with `ruff check app/` clean; frontend `tsc` clean and the **full vitest suite 340/340 across 49 files**. See "Implementation status" below Part 0 for what shipped, the design deviation the source forced, the wrong turn the tests caught, and what remains.
**Prepared by:** Jan
**Date:** 2026-07-22 (rev 3. Rev 2 was a full workflow/logic review of rev 1 against the documentation set and the current source - Appendix B lists every correction it produced. Rev 3 applies the client's D3 answer: the checklist-import feature is **retired**, and corrects one rev-2 imprecision found while scoping the retirement, Appendix B #12.)
**Purpose:** The AI Wizard (transaction creation) was reorganized into Audri's four stages - Upload / Contract Details / Contacts & Fees / Verification - with the checklist step retired, per-side fees added, and client-scoped signature/missing-document actions added. Transaction processing (the workspace, the task engine, the automation system, the cross-deal queues) was designed against the old wizard. This plan audits every seam between creation and processing against the current source, names the inconsistencies precisely, and lays out the changes that make the two stages one coherent workflow.
**Grounding rule for this plan:** the documents in `velvet-elves-data/` are treated as **reference, not truth** - several of them still describe the pre-reorganization wizard. Every "exists today" claim below was verified in the current frontend/backend source and carries its file citation. Where a document contradicts the source, the source wins and the document is queued for correction in Phase 7.

**Documents read (reference):** `WIZARD_REORGANIZATION_FOUR_STEP_PLAN.md`, `WIZARD_REORG_JAKE_IMPLEMENTATION_PLAN.md`, `TRANSACTION_PROCESSING_METHOD.md`, `TRANSACTION_PROCESSING_LOGIC_AND_WORKFLOW_GUIDE.md`, `TRANSACTION_PROCESSING_EVOLUTION_PLAN.md`, `SMART_TRANSACTION_PROCESSING_AND_TASK_ENGINE_PLAN.md`, `FRONTEND_UI_WORKFLOW_LOGIC.md` (§4.5/§4.6/§13.A), `STYLE_GUIDE.md`, `SYSTEM_DESIGN.md`, `requirements.txt` (§15), `WIZARD_TESTING_GUIDE.md`.
**Source verified:** `velvet-elves-frontend/src/components/wizard/` (wizardTypes.ts, NewTransactionWizard.tsx, WizardSignaturePanel.tsx, WizardMissingDocsPanel.tsx), `src/components/workspace/` (ComplianceTab, TasksTab, DealBriefBand, WorkspaceHeader, TimelineTab), `src/pages/transactions/TransactionListPage.tsx`; `velvet-elves-backend/app/api/v1/transactions.py`, `app/api/v1/transaction_plan.py`, `app/api/v1/ai.py`, `app/services/task_generation_service.py`, `app/services/ai_task_executor.py`, `app/services/task_email_planner.py`, `app/services/task_notification_service.py`, `app/services/automation_posture_service.py`, `app/services/agent_issues.py`, `app/schemas/transaction.py`, `app/models/transaction.py`, `app/repositories/transaction_repository.py`.

---

## Part 0 - Principles this plan is held to

These are the standing rules from the client and from past failures, restated here because every design choice below is tested against them:

1. **Everything is verifiable through the UI by a non-developer.** The testers are real-estate professionals. Every acceptance criterion in Part 5 is a mouse-driven click script with an on-screen expected result; no claim depends on reading the database or calling an API.
2. **Maximum convenience, minimum typing.** One-click actions, pre-addressed emails, pre-filled values, honest defaults. Where this plan adds UI, the common path is mouse-only.
3. **Design harmony, modern, unmistakably a professional tool.** The wizard keeps its approved expressive style; workspace surfaces keep the flat modern professional-tool aesthetic (hairline dividers, sentence case, `ve-*` tokens, shadcn Select / SegmentedControl, Radix dialogs, lucide icons, tables + modals for lists, honest empty states). Every UI phase ends with a rendered-screenshot check.
4. **Preview equals commit; evidence for every AI claim; honest degradation; everything audited.** The four system rules from the processing guide remain non-negotiable.
5. **Each phase leaves a fully working end-to-end product** (wizard through workspace), so testing never hits a broken interim build.

---

## Implementation status (2026-07-22)

All seven phases are built. Suites: backend `test_intake_handoff_alignment.py` (16 new) + `test_ai_task_executor` / `test_task_generation` / `test_transactions_api` / `test_transactions_advanced` / `test_transaction_fees` / `test_transaction_plan` (79) all green, ruff clean; frontend `tsc -p tsconfig.app.json` clean, `WizardFlow` 68/68.

| Phase | Shipped |
|---|---|
| 1 | `TransactionIntakePayload` + `intake_json` on `TransactionCreateRequest` (create only); merged into `metadata_json.intake` in the create endpoint; `metadata_json` threaded through `TransactionRepository.create()`; FE `TransactionIntakePayload` type; the wizard's `submit()` sends the record (never the shared draft payload, so save-draft is untouched) |
| 2 | Both request tasks now carry `target: 'Co-op Agent'`, `basis` acceptance+2d **and** an explicit fallback `due_date`, plus `intake_request`; `_AddedTask.intake_request` added; the generation service writes it to `metadata_json` and now distinguishes `auto_draft_email: False` (suppressed) from absent (posture default) |
| 3 | `_signature_deference()` + `_open_intake_request_exists()` in `ai_task_executor.py`; the §3.3 table honored in `_execute_documentation_review`; envelope-in-flight documents split out of the chase set entirely; deference codes `signing_deferred` / `covered_by_request_task` / `awaiting_esign` added to `_RETRYABLE_CODES` so the chase re-arms cleanly |
| 4 | `FeeEditDialog.tsx` (per-side amounts + `$`/`%`, "Remove fee") + `DealFeesSection.tsx` on the **People tab**, with the pencil affordance and the "+ Add fees" empty state, gated on the PATCH role set (D5 default). See the deviation note below for why it is not on the deal brief |
| 5 | Create now lands on `/transactions/:id?created=1` (save-draft and the onboarding `onCreated` path untouched); `CreationReceiptStrip.tsx` renders the one-time receipt with per-segment tab links and dismiss |
| 6 | Checklist import retired per D3: deleted `ChecklistImportModal.tsx`, `useParseChecklist`, the `ChecklistImportItem` type, the MSW handler, the `WizardChecklistStep` wiring and its now-orphaned `onAddTasks` prop, the `/ai/parse-checklist` endpoint + models, `checklist_import.py`, and `test_checklist_import.py` |
| 7 | Docs rewritten (below) + the regression run |

**Deviation the source forced (one), and the design decision that shaped it.** The plan's S5 said fees were "displayed read-only on the deal brief (`DealBriefBand.tsx`, mounted by `WorkspaceHeader.tsx:361`)". That mount is inside `DealOverviewCard`, and **`DealOverviewCard` has no live usage anywhere** - so fees entered in the wizard were rendered **nowhere** on the workspace, and a fee-edit affordance inside `DealBriefBand` would have been dead UI. S5 understated the problem: fees were not merely uneditable, they were invisible.

My first fix was to render `DealBriefBand` at the top of the Timeline tab. **That was wrong, and the test suite caught it.** Two `TransactionWorkspace` tests assert the opposite in as many words - *"legacy deals render cleanly with no overview band on the page"* and *"Per Jan's 2026-06-13 review the deal brief / overview band was removed from the page entirely - neither the summary nor watch-outs appear"*. The band's absence is a deliberate, pinned design decision, not an accident of a refactor. Reverted.

Shipped instead: a **`DealFeesSection` on the People tab** - the fees alone, no brief summary, no watch-outs, no KPI band. People is where the deal's commercial relationships already live (who is on the deal, and now who pays what), and it already carries the identical role gate. This satisfies invariant 5 without reopening a decision the client already made. The workspace's no-overview-band rule stands untouched.

**Test churn (expected, from D1).** Eleven `WizardFlow` create-path assertions moved from `findByText('Transactions list')` to `findByText('Deal workspace')`, and the harness gained a `/transactions/:transactionId` route stub. The save-draft assertion deliberately still expects the list.

**Not built (deliberately deferred).** The receipt strip's rendered-screenshot sign-off for Jake/Audri (standing screenshot gate on UI phases) and the Part 5 matrix walked on the live stack — both need the running app and are the natural next session. Everything else in Parts 3-4 is implemented.

---

## Part 1 - What creation actually produces now (verified)

The wizard's navigable machine is `WIZARD_STEPS = ['upload', 'purchase', 'address', 'missing', 'confirm']` with `missing` a hidden auto-skip, presented as four public phases: Upload / Contract Details / Contacts & Fees / Verification (`wizardTypes.ts:65-108`). Create is the full-width **"Upload Transaction"** button on Verification with a confirmation disclaimer above it; the retired `timeline` / `checklist` / `review` ids remain only for stale-draft coercion.

What clicking "Upload Transaction" emits, in order (the `submit()` chain in `NewTransactionWizard.tsx`):

| # | Output | Where it lands in processing |
|---|--------|------------------------------|
| 1 | The transaction row, now including per-side **`fees_json`** (`transactions.py:306`; schema `schemas/transaction.py:137`) | Deal brief band on the workspace header (`DealBriefBand.tsx:30,131-137` via `transaction_plan.py:817`); nothing else reads fees |
| 2 | Parties (with vendor auto-bridge) | People tab, vendor directory |
| 3 | Linked documents + the confirmed compliance rows with auto-matched uploads (bulk insert before task generation) | Compliance tab, Documents tab |
| 4 | E-signature queue, only when the **client's** side is unsigned and the user chose "Queue e-signature" (`NewTransactionWizard.tsx:4409`) | E-sign surfaces, `signature_in_flight` agent detector (`agent_issues.py:265`) |
| 5 | The full deterministic task plan, plus wizard-approved AI rows (`added_tasks`, created `source="ai"`, `task_generation_service.py:432-521`) | Tasks tab, Timeline tab (with evidence chips), My Task Queue |
| 6 | **New since the reorg:** up to two client-scoped request tasks - "Request signed copy from the other agent" (when the counterparty is unsigned and the user picked that action) and "Request missing documents from the other agent" (`NewTransactionWizard.tsx:4498-4519`) | Tasks tab / My Task Queue - **with the defects in Part 2** |
| 7 | Watch-outs persisted with citations | Deal brief / workspace |
| 8 | An immediate background run of the AI task executor over the library's Automated rows (`transactions.py:1462-1469`) | Welcome emails sent and completed, Review Documentation runs, "AI needs you" surfacing |
| 9 | Navigation to the **transactions list** with the new deal's card expanded (`?highlight=`, create completion `NewTransactionWizard.tsx:4575`; alias handling `TransactionListPage.tsx:446-448`). The separate save-draft exit (`:4658`, Incomplete shell, no tasks generated) also lands on the list, correctly. When the wizard is embedded, completion is delegated to `onCreated` - passed only by the onboarding first-transaction flow (`OnboardingWizard.tsx:776`) | The user does NOT land in the workspace |

What the reorganization **removed** from creation (processing must absorb each):

- The pre-create checklist editing step (attach/add/waive/import before the deal exists). The workspace Compliance tab is now the only checklist editing surface.
- The standalone timeline and task-review steps (folded earlier; unchanged here).
- The platform `hello@` party-introduction emails at creation (retired 2026-07-16; the agent-mailbox Automated Welcome tasks own transaction welcomes).

## Part 1.5 - What already lines up (verified consistent; pin, don't change)

- **Decision gates:** `title_ordered_by` (requirements.txt:1245, §15.1) and the cash-deal appraisal election (§15.3) hard-block create in the wizard; the workspace decision banner remains for post-create answer changes and quick-create deals. Both sides agree.
- **Compliance tab parity:** add requirement, waive/un-waive with undo, attach with auto-match, request-by-email, generate defaults, verify document type, adopt AI type - all present (`ComplianceTab.tsx:137-155, 533-562`). The retired wizard checklist step's editing role is genuinely covered; its one leftover, checklist import, is resolved by decision D3 (feature retired - S6/§3.6).
- **Executor discipline:** the AI task executor touches only `automation_level='Automated'` playbook rows (`ai_task_executor.py:258-260`); the wizard's Manual request tasks can never be auto-run.
- **Quick-create parity:** non-wizard creates get library-default compliance rows at task generation (`transactions.py:1443-1455`); absent fees render nothing (honest absence) wherever fees are shown.
- **Evidence continuity:** accepted AI timeline/checklist/task rows carry their citations into task `metadata_json` at commit (`transactions.py:1287-1295`; `task_generation_service.py:491-496`) and render as evidence chips in the workspace.
- **Stale drafts:** retired step ids coerce at draft-apply; resume works from any historical step.
- **Autopilot fast path:** still lands on Verification, still the last step; the posture system is untouched by the reorg.

---

## Part 2 - Seam-by-seam audit: the inconsistencies

Each seam states what creation now promises, what processing actually does (source-verified), and the verdict.

### S1 (Critical) - The "other agent" request tasks are addressed to the wrong person

The wizard creates the two request tasks with **no `target`** (`NewTransactionWizard.tsx:4507-4518` passes only name/kind/description, though `_AddedTask.target` exists, `transactions.py:1316`). In the workspace, "Complete this task" resolves its recipient through `_selected_group_for_task` (`task_email_planner.py:279-291`): no playbook entry, no target → **defaults to the account holder** (a self-reminder). So a task literally named "Request signed copy from the other agent" opens a pre-addressed email **to yourself**. This contradicts the task's own name, the wizard's promise, and the "task emails go to the matrix target" rule. The `Co-op Agent` group exists in both the planner (`task_email_planner.py:78`) and the auto-draft role map (`task_notification_service.py:738-745`), so the fix is data, not machinery.

### S2 (High) - The request tasks are undated, so the most urgent tasks sort last

`task_generation_service.py:441-450`: an added task without `due_date`/`basis` persists undated. The Tasks tab sorts undated rows with a `'9999-12-31'` sentinel (`TasksTab.tsx:132-133`), i.e. to the **bottom of Upcoming**, and an undated task never triggers the due-date loops (reminder sweep, auto-draft, digest). A chase for a missing signature is the most time-critical item on a fresh deal, and it is the single easiest task to miss.

### S3 (High) - Two parallel chase channels ask the other agent for the same thing

On an unsigned packet, creation now fires **both**:
- the wizard's Manual "Request signed copy from the other agent" task (item 6 above), and
- the executor's **Review Documentation** Automated task, which independently inspects the extraction evidence, surfaces "unsigned_documents", and **drafts its own signature-request email to the co-op agent** immediately at generation (`ai_task_executor.py:490-574`, draft at `:547,614-657`).

The user gets a manual task and an AI draft for the same ask, created seconds apart, with no reference to each other. Two facts make this worse than it first looks:

- **The executor deliberately bypasses the automation posture** (`ai_task_executor.py:12-13`: it "goes beyond the automation posture's 'nothing sends without a tap' rule"). Setting the deal to Manual does NOT stop the chase draft; only a design change can.
- Once S1/S2 give the task a `Co-op Agent` target and a due date, posture defaulting (`automation_posture_service.py:153-168` - and note `task_generation_service.py:504-507` applies the posture default whenever the explicit flag is not True, so passing `false` today does not suppress it) would enroll the task in the auto-draft sweep on Assisted/Autopilot: potentially **three** chase artifacts. (The sweep itself is well-behaved: it skips undated tasks, `task_notification_service.py:811-813`, and Automated tasks, `:807-808`, and resolves posture per deal.)

One ask must have one owner.

### S4 (High) - The wizard's signature decision is never persisted, so processing overrules the user

`signatureChoice` (`'queue' | 'later' | 'not_required' | 'request_other_agent'`, `wizardTypes.ts:1068`) drives only in-wizard behavior (`NewTransactionWizard.tsx:1944,4409,4503`); nothing writes it to the deal. Consequence: a user who clicks **"Mark not required"** on Verification still gets Review Documentation surfacing "missing signatures" plus a chase draft on the very first executor run - the system contradicts a decision the user made one minute earlier on the Verification screen. Same for "I'll handle signing later" (the user asked not to be chased yet).

The **"Queue e-signature"** choice is contradicted too, through a different mechanism: `_signature_verdict` counts an in-flight envelope as unsigned (`ai_task_executor.py:595-596` returns `False, ["awaiting e-signature"]` for `signature_status` sent/delivered), so while the client's envelope is out for signing, Review Documentation drafts a chase email **to the co-op agent** about a document that is simply awaiting the client's e-signature - the wrong recipient for a non-problem. (The verdict's in-flight branch is correct for *completing* the task - the doc is genuinely not yet signed; the defect is that the chase draft doesn't distinguish "the other side never signed" from "our envelope is pending.")

The transaction model already has `metadata_json` (`models/transaction.py:109`), but the repository's **create** kwarg whitelist does not thread it (only `_row_to_transaction:420` reads it), so persisting the decision needs the same touchpoint threading `fees_json` got on the create side. (`update()` is a generic field mapper, `transaction_repository.py:166-187` - not a whitelist - but this plan deliberately does not extend the update path for intake; see §3.1.)

### S5 (Medium) - Fees can be entered at creation but never edited afterwards

`fees_json` is accepted on create (`transactions.py:306`; schema `schemas/transaction.py:137`) **and on the generic PATCH** (`transactions.py:827-906`: `model_dump(exclude_unset=True)` → `repo.update(tx, **fields)`, whose field mapper passes `fees_json` through, `transaction_repository.py:166-187`). The only component that renders it is `DealBriefBand.tsx`, mounted by `DealOverviewCard` (`WorkspaceHeader.tsx:361`) - **and `DealOverviewCard` is never rendered** (the deal brief / overview band was deliberately removed from the workspace page in Jan's 2026-06-13 review, a decision pinned by two `TransactionWorkspace` tests). So a fee entered in the wizard is not merely uneditable afterwards: it is displayed **nowhere** on the workspace. Commission terms change mid-deal (amendments, negotiated credits); today that means the data is simply frozen at intake. The four-step plan's Phase 6 promised inline edit; it was never built.

Three server-side facts the edit UI must design around (all verified):

- **`repo.update()` silently skips `None` values** (`transaction_repository.py:176-177`), so `"fees_json": null` cannot clear fees. Clearing must send a non-null empty payload (`{"professional": null, "transaction": null}`), which overwrites the JSONB; the display already renders nothing for it.
- **The PATCH role gate excludes the Transaction Coordinator** (`transactions.py:832`: agent / team lead / admin), even though key-dates (`:1050`) and task generation include TC. Fee editing inherits whichever gate we choose - Decision D5.
- The PATCH already writes an audit row ("Updated fields: fees_json") and `record_corrections_from_patch` ignores fees (deliberately absent from the corrections resolution map), so no spurious correction rows - the audit story needs no new plumbing.

### S6 (Medium) - The checklist-import feature died silently with the checklist step. **DECIDED (D3, 2026-07-22): retire it**

`POST /ai/parse-checklist` (`ai.py:2065-2106`) and `app/services/checklist_import.py` still exist and are tested. Their only frontend consumer chain - `useParseChecklist` (`useWizardApi.ts:600-620`) → `ChecklistImportModal.tsx` → `WizardChecklistStep.tsx` (:44, :57, :246, :530) - hangs entirely off the retired checklist step, which is kept in the tree only as an unreachable stale-draft guard. So the feature is live code with no reachable UI, while "import your own checklist" is still advertised in the processing guide. Dead-but-compiled feature code is drift in both directions: it cannot be tested through the UI, and the docs promise something the product no longer offers.

The client's answer to D3 is to **retire the feature**, not restore it. §3.6 specifies the removal inventory; the docs stop mentioning imports in the same phase the code goes.

### S7 (Medium) - The creation→processing handoff drops the user on the list, and nothing proves what was created

After "Upload Transaction" the user lands on `/transactions?highlight=<id>` (the list, card expanded), not the deal. The Verification disclaimer explicitly promises "tasks, timeline, checklist, communications" will be built; the only way a tester can verify that promise today is to click into the deal and open four tabs one by one. There is no single on-screen proof that creation produced what Verification said it would - exactly the class of gap that has broken frontend testing before.

### S8 (Medium) - The processing documentation and guides describe the retired wizard

Treating docs as reference does not mean leaving them wrong; testers follow them. Verified stale claims: `TRANSACTION_PROCESSING_METHOD.md` ("five short screens", Timeline/Checklist/Tasks-and-create steps, "Approve & Create"); `TRANSACTION_PROCESSING_LOGIC_AND_WORKFLOW_GUIDE.md` Part 2 (three-phase stepper, checklist step, §2.5) and Part 3 item 3 (intro emails from `hello@` - retired 2026-07-16); `TRANSACTION_SYSTEM_GUIDE.md` (verified: "Step 3 of 5 · Timeline" rail, "Confirm Timeline"/"Confirm Checklist"/"Approve & Create" button ladder at its lines 105-185, and it claims create "opens the deal's transaction page" - which the source contradicts today and D1 would make true); the Help Center creation articles (verified: the content migration `20260905090000_help_center_content_source_accurate.sql` describes a wizard that "walks through nine steps, grouped into phases" and contains zero mentions of Verification or "Upload Transaction"). `FRONTEND_UI_WORKFLOW_LOGIC.md` §13.A and `WIZARD_TESTING_GUIDE.md` are already current; the processing-side guides are not.

### S9 (Low) - Referenced-missing-document context lives only in one task's description

`state.aiMissingDocuments` (referenced-but-not-uploaded documents from the contract resolution) reaches processing only as prose inside the single "Request missing documents from the other agent" task description (`NewTransactionWizard.tsx:4513-4518`). The workspace missing-documents surfaces are requirement-based (`MissingDocumentsPanel.tsx:93`) and do not know about packet-referenced gaps. Acceptable as a v1 record; S4's intake persistence gives this a durable home, and the request task remains the actionable surface.

---

## Part 3 - Target design

### 3.1 One intake handoff record (fixes S4, S9; enables S3)

At create, the wizard sends a compact, validated **intake review record** that processing can honor:

```jsonc
// TransactionCreateRequest.intake_json (new, optional)
{
  "signature_choice": "request_other_agent",   // 'queue' | 'later' | 'not_required' | 'request_other_agent' | null
  "missing_signature_roles": ["seller"],        // from state.aiMissingSignatures
  "missing_documents": ["Counter Offer #2"],    // from state.aiMissingDocuments
  "missing_docs_requested": true                 // state.missingDocsRequested
}
```

Server-side it is merged into `transactions.metadata_json.intake` (column exists; **no migration**). Threading, mirroring the fees precedent exactly (the repository is a kwarg whitelist, not a pass-through): pydantic model in `schemas/transaction.py` → create endpoint merge → `TransactionRepository.create()` signature + `_optional` dict (`update()` deliberately NOT extended; the intake record is a point-in-time fact, corrected only through the workspace actions it drives) → `_row_to_transaction` already maps it → FE `types/api.ts`. Deals created before this change, and quick-create deals, simply have no `intake` key; every consumer below treats "absent" as "behave exactly as today," so nothing changes retroactively.

### 3.2 Request tasks become real, correctly-addressed, dated tasks (fixes S1, S2)

In the wizard's `submit()`, both request tasks gain:

- `target: 'Co-op Agent'` - "Complete this task" then pre-addresses the other agent with CC per matrix, and the auto-draft role map already resolves it (`buyers_agent` / `listing_agent`).
- `basis: { anchor: 'contract_acceptance_date', direction: 'after', days: 2 }` - resolved server-side by the same arithmetic as every other deadline (`resolve_added_task_basis`, `timeline_planner.py:433-457`), rolled off weekends. **Plus an explicit fallback `due_date` of today+2:** the resolver returns `None` when the anchor is missing or undated (`:451-456`), and the generation code keeps the explicit date exactly when the basis fails to resolve (`task_generation_service.py:441-463`, basis wins when resolvable) - so the task can never land undated, even on a deal whose acceptance date is somehow absent. A chase is due promptly; two days is the professional norm and the value is a constant, changeable in one line.
- `metadata.intake_request: 'signed_copy' | 'missing_documents'` (via a new optional `_AddedTask.intake_request` passed into `metadata_json`) so processing can recognize these rows structurally, never by name-matching.

Backend honor-explicit-false fix: `task_generation_service.py:504-507` currently applies the posture auto-draft default whenever the explicit flag is not True. Change to distinguish `False` (explicitly suppressed) from `None`/absent (posture default applies). The request tasks pass nothing and so **follow the deal's posture** like any other co-op-agent task: Manual posture → the user drives it via the pre-addressed Complete-this-task dialog; Assisted/Autopilot → the sweep drafts the chase when due, exactly one draft per (task, due date). The explicit-false capability exists for any future caller that must opt out.

### 3.3 One ask, one owner: Review Documentation defers to the user's decision (fixes S3, S4)

`_execute_documentation_review` gains one lookup before drafting: the deal's `metadata_json.intake` plus the presence of an open `intake_request='signed_copy'` task.

| Intake state | Review Documentation behavior (new) |
|---|---|
| No `intake` record (old deals, quick-create) | Unchanged: surface + draft the chase (today's behavior) |
| `signature_choice: 'not_required'` | **Complete with a note**: "You marked signatures not required at intake." No surfacing, no draft. Fully audited |
| `signature_choice: 'later'` | Surface (amber, "you chose to handle signing later - the AI found these still unsigned") but **no draft**. The user asked not to be chased yet; the finding stays visible, not silent |
| `signature_choice: 'request_other_agent'` and the request task is open | Surface with the reason **pointing at the task** ("your 'Request signed copy from the other agent' task covers this - it is due {date}") and **no second draft**. The task owns the chase |
| `signature_choice: 'queue'` | Surface as awaiting signature; **no chase draft** - the envelope is the channel and the `signature_in_flight` detector reports progress |
| A document's only "missing" evidence is an in-flight envelope (`_signature_verdict` returns `["awaiting e-signature"]`, `ai_task_executor.py:595-596`) - regardless of intake record, old deals included | **Never draft a chase to the co-op agent for it.** A pending envelope is our own channel in flight, not the other side's failure; chasing the co-op agent about it is the wrong recipient for a non-problem (see S4). Extraction-evidenced missing signatures on OTHER documents still chase normally |
| Request task completed but documents still unsigned on a later parse | Normal chase resumes (the deferral is tied to an OPEN request task, so a stalled chase is never silently dropped) |

The invariant this encodes: **a decision the user made on Verification is never contradicted by the first automation cycle.** Two implementation rules keep the mechanics honest:

- **Deference surfacing uses distinct codes** (e.g. `signing_deferred`, `covered_by_request_task`, `awaiting_esign`), never `unsigned_documents` - the existing re-draft guard keys on `code == "unsigned_documents"` plus a findings hash (`ai_task_executor.py:541-546`), so a deference state must not be mistakable for an already-drafted chase, and when a deferral ends the normal chase path re-arms cleanly.
- Re-surfacing is safe by construction: `_surface_task` is a metadata overwrite (`:713-730`), so an hourly cycle repeating the same deference does not spam anything; each branch still short-circuits ("surfaced") when the state is unchanged.

### 3.4 Fees become live deal facts (fixes S5)

- **Where fees live:** a compact **Deal fees** section at the top of the **People tab** - the fees alone, never the brief summary or watch-outs, so the workspace's no-overview-band rule is untouched. People already holds the deal's commercial relationships (who is on the deal, and who pays what) and already carries the same role gate.
- **Edit in place:** the fee row gains a pencil affordance opening a compact Radix dialog that reuses the wizard's fee-card anatomy verbatim: "Who pays?" SegmentedControl (Buyer / Seller / Both), one amount `Input` + `$ | %` SegmentedControl per paying side (two labeled rows for Both). Same component family, zero new primitives, one number typed at most per side.
- **Honest empty state:** when no fees exist and the viewer can edit, the band shows a ghost "+ Add fees"; viewers without edit rights see nothing (no fake rows).
- **Removing fees works too:** the dialog offers "Remove fee" per card. Because `repo.update()` skips `None` kwargs (S5), removal sends the non-null empty payload `{"professional": null, "transaction": null}` (or nulls one side), never `"fees_json": null` - which the server would silently drop. The FE integration test pins this exact payload shape.
- **Plumbing:** the existing `PATCH /transactions/{id}` (`transactions.py:827-906`) already threads `fees_json` and already writes the audit row - this phase is UI only. Display keeps tolerating old-shape rows (renders nothing rather than crashing).
- **Roles:** the affordance renders exactly for the roles the PATCH accepts - today agent / team lead / admin (`transactions.py:832`). Whether the Transaction Coordinator joins them is Decision D5; the UI reads the same gate either way, so the decision is a one-line backend change, not a UI fork.
- Fees remain **capture-only** beyond display (Jake's decision): no invoicing/payout computation in this plan.

### 3.5 The handoff lands where the work is, with proof (fixes S7)

- After "Upload Transaction," navigate to **the new deal's workspace** (`/transactions/:id`), not the list. Scope, precisely: only the create-completion site changes (`NewTransactionWizard.tsx:4575`). The save-draft exit (`:4658`) keeps landing on the list - an Incomplete shell has no tasks and no receipt to show. The embedded/onboarding path (`onCreated`, passed only by `OnboardingWizard.tsx:776`) keeps its own completion flow untouched. (Decision D1; the list keeps `?highlight`/`?expand` support for every other inbound path.)
- The workspace shows a **one-time creation receipt strip** under the header on first visit after create (dismissed on click, never shown again; driven by a `?created=1` param the wizard appends, not by new storage): one flat line in the workspace's professional-tool voice, e.g.
  `Created just now · 23 tasks (5 handled by AI) · 12 checklist items, 3 documents attached · Fees captured · E-signature queued · 1 request to the other agent`
  Every segment is a link to its tab (Tasks / Compliance / Documents / the fee row / the request task). Segments render **only when true** (no fees entered → no fees segment). Numbers come from the rows actually created, so the strip is the mouse-verifiable proof that "what Verification promised is what processing received" - the direct answer to the end-to-end testability principle.
- Visual: flat band, hairline border, `ve-*` tokens, sentence case, lucide `check-circle-2`, no gradients - workspace aesthetic, not wizard-expressive.

### 3.6 Checklist-import retirement (fixes S6; D3 decided: retire)

The feature is removed cleanly, code and docs together, so nothing dead stays compiled and nothing advertised stays unbuildable. Removal inventory (verified complete by repo-wide search):

| Layer | Removed |
|---|---|
| Frontend | `ChecklistImportModal.tsx`; the modal wiring inside the unreachable `WizardChecklistStep.tsx` (:44, :57, :246, :530 - the component itself **stays** as the stale-draft guard); `useParseChecklist` + `ChecklistImportItem` (`useWizardApi.ts:600-620`); the MSW handler (`tests/mocks/handlers.ts:856`) |
| Backend | The `/ai/parse-checklist` endpoint + its response models (`ai.py:2065-2106`); `app/services/checklist_import.py`; `app/tests/test_checklist_import.py` |
| Docs (folded into Phase 7) | `TRANSACTION_PROCESSING_LOGIC_AND_WORKFLOW_GUIDE.md:84` ("import your own checklist"); `TRANSACTION_SYSTEM_GUIDE.md:142` ("Use your own checklist"); `TRANSACTION_PROCESSING_WORKFLOW_IMPLEMENTED.md:131`; `WIZARD_TESTING_GUIDE.md` §11.3; `FRONTEND_CLIENT_TESTING_REVIEW.md:757`; any Help Center article mention found in the Phase 7 sweep |

What users keep, unchanged: the Compliance tab's add-requirement, generate-defaults, attach, waive, and request-by-email actions - a checklist can still be built by hand row-by-row or from the library defaults; only the parse-a-pasted-or-uploaded-file path goes away. No data migration is involved (the parser never persisted anything; files were parsed in-memory by design).

### 3.7 Documentation truth pass (fixes S8)

Rewrite the stale creation narratives against the shipped reality: `TRANSACTION_PROCESSING_METHOD.md` Step 1 (four stages, "Upload Transaction," checklist committed silently with auto-match, welcome mail via the agent's Automated tasks); `TRANSACTION_PROCESSING_LOGIC_AND_WORKFLOW_GUIDE.md` Part 2 (full rewrite to the four stages incl. fees and the client-scoped actions), Part 3 (creation sequence: fees persisted, intake record, request tasks, no `hello@` party intros), Part 6 (Review Documentation's new deference table); `TRANSACTION_SYSTEM_GUIDE.md` wizard sections; the Help Center creation/wizard articles; add the Part 5 matrix below to `TRANSACTION_WORKSPACE_TESTING_GUIDE.md`; and strip every checklist-import mention per the §3.6 docs inventory. Docs ship in the same phase as the behavior they describe, never ahead of it.

---

## Part 4 - Implementation phases

Sequencing rule: backend truth first, then task correctness, then the deduplication that depends on both, then the UI surfaces, then docs. Every phase leaves the full wizard→workspace flow working.

**Phase 1 - Intake handoff record (backend + wizard payload).**
`intake_json` schema model with strict literals; create-endpoint merge into `metadata_json.intake`; repository threading (create signature + `_optional`; response echo); FE `types/api.ts`; wizard `submit()` sends it. Tests: backend create round-trip (all four choices + absent), whitelist regression (update does not accept it), WizardFlow payload assertion.
*Acceptance (mouse):* create a deal choosing "Mark not required"; the deal creates exactly as before (no visible change yet - this phase is substrate).

**Phase 2 - Request tasks addressed, dated, and tagged.**
Wizard passes `target`, `basis` + fallback `due_date`, `intake_request` on both request tasks; `_AddedTask` gains `intake_request`; generation service writes it to `metadata_json` and honors explicit `auto_draft_email: false` (None keeps posture default). Tests: generation-service unit (target/basis/fallback-date/metadata/false-vs-absent), WizardFlow assertion on the generate payload, planner test (request task resolves to Co-op Agent group via the target fallback, since these names are not in `_EMAIL_PLAYBOOK`).
*Acceptance (mouse):* create an unsigned-packet deal choosing "Request the signed copy"; on the Tasks tab the request task shows **due two days after acceptance** near the top of Upcoming; "Complete this task" opens **pre-addressed to the co-op agent** with the description as the body seed; the auto-draft sweep produces nothing for it on Manual posture. **Known interim state, unchanged from today:** the executor's Review Documentation chase draft still appears alongside the task until Phase 3 lands (the executor bypasses posture by design, `ai_task_executor.py:12-13`) - Phase 2 does not worsen it, Phase 3 removes it.

**Phase 3 - Single chase channel in Review Documentation.**
The deference table (§3.3) in `_execute_documentation_review`; open-request-task lookup by `metadata_json.intake_request`; the envelope-in-flight no-chase rule; distinct surface codes (never `unsigned_documents` for a deference state); notes/reasons worded as specified; the existing re-draft guard untouched. Tests: executor matrix over all seven rows of the table, including old-deal/no-intake fallback, envelope-in-flight, and the reopened-chase row.
*Acceptance (mouse):* same deal as Phase 2 - the Tasks tab shows Review Documentation surfaced with "your request task covers this" and **AI Emails contains zero chase drafts**; a fresh deal with "Mark not required" shows Review Documentation **completed** with the note; a deal with a queued envelope shows "awaiting e-signature" and **no chase draft to the co-op agent**; a quick-create deal with genuinely unsigned paperwork still gets today's chase draft.

**Phase 4 - Fees editable on the workspace.**
Fee edit dialog + the People-tab Deal fees section with its "+ Add fees" empty state; remove-fee sends the non-null empty payload (§3.4); old-shape tolerance kept; D5 role decision applied (one-line backend change if TC joins). Tests: FE unit (dialog per-side entry, Both = two rows), integration (edit → the section updates → reload persists; **remove → the section empties → reload stays empty**, pinning the payload shape against the `None`-skip), audit-row backend assertion. Screenshot check.
*Acceptance (mouse):* on a deal created with no fees, open the People tab, click "+ Add fees," click Seller, type 3, click %, Save - the row reads "Professional fee · 3% · seller"; reload persists; "Remove fee" empties it and survives reload; Activity shows the fees update; a signed-in role outside the PATCH gate sees the fee row with no pencil and no "+ Add fees".

**Phase 5 - Workspace landing + creation receipt.**
Navigation change (D1), `?created=1` receipt strip with real created-row counts, per-segment links, dismiss behavior. Tests: WizardFlow navigation assertion, receipt unit tests (segment truth table incl. absent-fees and no-request-task cases), screenshot at desktop and mobile widths.
*Acceptance (mouse):* "Upload Transaction" lands directly on the new deal's workspace; the receipt line's numbers match the Tasks/Compliance tabs behind it; clicking "12 checklist items" opens Compliance; the strip is gone on the next visit; opening a deal from the transactions list never shows it.

**Phase 6 - Checklist-import retirement (D3: decided).**
Remove the §3.6 inventory: frontend modal/hook/handler and the `WizardChecklistStep` wiring (component kept as the stale-draft guard), backend endpoint + service + their test file. Tests: `tsc` clean and both suites green after the deletions; a backend test-client call to `/ai/parse-checklist` returns 404 (asserted once in an existing ai-router test, then that assertion is the only trace left).
*Acceptance (mouse):* nowhere in the running app - wizard included, via a stale pre-reorg draft resumed onto the guard step - does any "Use your own checklist" / import affordance render; the Compliance tab's add / generate-defaults / attach / waive / request actions all still work.

**Phase 7 - Documentation truth pass + full regression.**
All §3.7 rewrites; append the Part 5 matrix to the workspace testing guide; run the whole matrix on the local stack; rendered screenshots of every changed surface (receipt strip, fee dialog, import modal, Review Documentation notes) for Jake/Audri sign-off.

---

## Part 5 - End-to-end verification matrix (mouse-only, written for the testers)

| # | Scenario | Expected on screen |
|---|----------|--------------------|
| 1 | Happy path: upload the 10-doc packet → four stages → Upload Transaction | Lands on the deal workspace; receipt strip counts match the Tasks and Compliance tabs; fees from Contacts & Fees show on the People tab |
| 2 | Unsigned counterparty + "Request the signed copy from the other agent" | Request task due acceptance+2 near the top of Upcoming; Complete-this-task pre-addressed to the co-op agent; Review Documentation surfaced pointing at that task; zero AI chase drafts |
| 3 | Same deal on Assisted posture | Exactly one chase draft appears in AI Email Review when the task comes due; running the cycle again adds none |
| 4 | "Mark not required" on Verification | Review Documentation completes itself with the "you marked signatures not required" note; no chase draft ever; Activity shows the completion |
| 5 | "I'll handle signing later" | Review Documentation surfaced amber, wording says the user chose later; no draft |
| 6 | Client-side unsigned + "Queue e-signature" | Envelope sent; agent pane shows "Awaiting signatures"; Review Documentation surfaces "awaiting e-signature"; no chase task and **no chase draft to the co-op agent** (new behavior - today a chase drafts against the pending envelope) |
| 7 | Referenced Counter #2 deliberately removed + "Request from the other agent" | Request task lists Counter #2 in its body; completing it sends to the co-op agent |
| 8 | Quick-create deal (no wizard) | Default checklist appears; Review Documentation behaves exactly as before this plan; no fees row, no receipt strip |
| 9 | Deal created with no fees | The People tab shows "+ Add fees" for the agent, nothing for a role outside the edit gate (D5); adding 3% / Seller persists across reload; removing it empties the band across reload; Activity logs it |
| 10 | Fee entered in the wizard, edited on the workspace | The People-tab row updates in place; reload persists; old deals with pre-reshape fee rows render without errors |
| 11 | Checklist-import retirement check: look for an import affordance on Compliance and on a resumed stale pre-reorg draft; then build a checklist by hand | No import control exists anywhere; the guides no longer mention it; adding rows manually and generating library defaults still work |
| 12 | Draft resume from a stale pre-reorg draft (retired step ids) | Reopens on the mapped step; create still lands on the workspace with the receipt |
| 13 | Decision gates regression | A packet with unanswered "who orders title" cannot reach Upload Transaction; answering via the one-click card enables it; the created deal has the right title task (no workspace banner) |
| 14 | Old deal created before this plan | Opens with no receipt strip, no behavior change from the intake record it doesn't have |
| 15 | Paywall (402) and Autopilot fast-path creates | Both complete to the workspace landing + receipt; every gate above still holds |

---

## Part 6 - Decisions (defaults chosen so work is never blocked)

| # | Question (owner: Jake/Audri) | Default if unanswered |
|---|------------------------------|----------------------|
| D1 | Land on the deal workspace after "Upload Transaction" (instead of the list with the card expanded)? | Yes - workspace + receipt strip; the list keeps highlight support for other paths |
| D2 | Chase-ownership rule: the request task owns the ask and Review Documentation defers (no second draft)? | Yes, per the §3.3 table; the deferral only holds while the request task is open |
| D3 | ~~Checklist import: restore on the Compliance tab, or retire the feature?~~ **DECIDED 2026-07-22: retire the feature.** | Applied in §3.6 / Phase 6: full code + docs removal, manual and library-default checklist building unchanged |
| D4 | Request-task due rule: acceptance + 2 days? | 2 days, one constant, changed in one line if Jake prefers a different norm |
| D5 | May the Transaction Coordinator edit fees? The generic PATCH gate excludes TC today (`transactions.py:832`), while key-dates and task generation include TC | Keep the current gate (agent / team lead / admin) - no silent permission widening; adding TC is a one-line change on Jake's word |

## Part 7 - Out of scope (decided elsewhere or deliberately untouched)

- Commission payout / invoicing / analytics computed from `fees_json` (capture-only per Jake; the data now stays correct enough to build on later).
- The wizard's parsing, extraction, backstops, confidence system, and step machine (just shipped and validated). This plan changes only what `submit()` sends, plus one subtraction: trimming the dead import wiring out of the unreachable `WizardChecklistStep` guard (Phase 6) - no reachable wizard behavior changes.
- Autopilot naming (Proposal 7), inbox intake, SMS, calendar invites, and the other evolution-plan directions - separate tracks.
- The quick-create modal beyond verifying its parity rows here.
- Any migration: both new persistence homes (`metadata_json`, task `metadata_json`) already exist as columns.

## Appendix A - Consistency invariants to pin (regression list)

1. A decision made on Verification (signature choice, fee entry, request actions) is never contradicted or silently re-asked by the workspace or the first automation cycle.
2. A task whose name says "the other agent" pre-addresses the co-op agent; a task with no matrix target still defaults to the account holder.
3. One ask, one owner: for any unsigned-documents finding there is at most one open chase artifact (task, draft, or envelope) at a time.
4. Wizard-created request tasks are Manual, dated, and executor-proof; the executor runs only Automated playbook rows.
5. Every fee shown anywhere is editable somewhere (by an editing role), and every fee edit is audited.
6. Deals without an intake record (old, quick-create) behave byte-for-byte as before this plan - with the single deliberate exception of the envelope-in-flight no-chase rule (§3.3), which corrects a wrong-recipient draft for every deal.
7. The receipt strip never shows a number that the tab behind it does not corroborate.
8. An in-flight e-sign envelope is never "chased" to the co-op agent; the envelope is the channel, and its progress is reported, not escalated.
9. Retiring a UI surface retires its exclusive endpoints, hooks, and doc mentions in the same change - no live endpoint without a reachable UI, no advertised feature without live code (the S6 lesson).

---

## Appendix B - Rev-2 review correction log (workflow/logic flaws found in rev 1)

I re-reviewed rev 1 of this plan against the documentation set and the current source, specifically hunting for workflow and logic errors in the plan itself. The seam audit (S1-S9) held up; the following errors in the plan were found and corrected:

| # | Rev-1 error | Why it was wrong (source evidence) | Correction |
|---|-------------|-----------------------------------|-----------|
| 1 | Phase 2 acceptance claimed "on Manual posture no draft appears anywhere" | The AI task executor deliberately bypasses the automation posture (`ai_task_executor.py:12-13`); Review Documentation drafts its chase on Manual deals too, and does so until Phase 3 lands | Phase 2 acceptance rewritten: the auto-draft sweep produces nothing on Manual, but the executor's chase draft remains as a documented interim state; S3 now names the posture-bypass explicitly |
| 2 | The §3.3 'queue' row said "Unchanged: the e-sign envelope is the channel," and matrix row 6 claimed today's behavior already produces no chase draft | `_signature_verdict` counts an in-flight envelope as unsigned (`ai_task_executor.py:595-596`, `["awaiting e-signature"]`), so today a queued envelope triggers a chase draft **to the co-op agent** about the client's own pending signature | New deference rule: envelope-in-flight documents are surfaced, never chased (applies to all deals, old included); 'queue' row rewritten; matrix row 6 marked as new behavior; S4 documents the defect; new invariant 8 |
| 3 | Fee update cited `transactions.py:1751` as the update endpoint and claimed edit roles were "the same as every other transaction edit (agent / TC / team lead / admin)" | `:1751` is `_request_to_transient_transaction` (the preview-tasks builder). The real PATCH is `:827-906`, and its role gate **excludes** the Transaction Coordinator (`:832`), unlike key-dates (`:1050`) | S5/§3.4 corrected with the real endpoint and mechanics; TC access became Decision D5 (default: keep the current gate, no silent permission widening) |
| 4 | The fee dialog assumed clearing fees was plain PATCH plumbing | `repo.update()` silently skips `None` kwargs (`transaction_repository.py:176-177`), so `"fees_json": null` can never clear; only a non-null empty payload overwrites the JSONB | §3.4 "Remove fee" specifies the exact payload shape; Phase 4 adds an integration test pinning it; matrix row 9 extended with the remove case |
| 5 | S4 described the repository as a "kwarg whitelist" for both create and update | Only `create()` is a whitelist; `update()` is a generic field mapper (`transaction_repository.py:166-187`) that already passes `fees_json` (and would pass `metadata_json`) through | S4/S5 corrected; the intake record still deliberately stays create-only, now for the stated design reason rather than a mechanical one |
| 6 | The navigation change cited both `NewTransactionWizard.tsx:4575` and `:4658` as create-completion sites | `:4658` is the save-draft exit (Incomplete shell, no tasks generated) - it must keep landing on the list; the embedded path delegates to `onCreated`, passed only by `OnboardingWizard.tsx:776` | Part 1 row 9 and §3.5 scope the change to the create site only, with save-draft and onboarding explicitly untouched |
| 7 | §3.2's basis rule left the request tasks undated whenever the acceptance anchor was missing | `resolve_added_task_basis` returns `None` on a missing/undated anchor (`timeline_planner.py:451-456`); the generation code falls back to an explicit `due_date` only when one was passed (`task_generation_service.py:441-463`) | The tasks now pass **both** the basis and a fallback `due_date` (today+2), so they can never land undated |
| 8 | The deference design did not say which surface codes it uses | The executor's re-draft guard keys on `code == "unsigned_documents"` + findings hash (`ai_task_executor.py:541-546`); reusing that code for a deference state would corrupt the resume logic | §3.3 mandates distinct codes (`signing_deferred`, `covered_by_request_task`, `awaiting_esign`) and documents why re-surfacing is idempotent-safe (`_surface_task:713-730`) |
| 9 | S8's staleness list included `TRANSACTION_SYSTEM_GUIDE.md` and the Help Center articles on inference, not evidence | Verified: the guide's "Step 3 of 5 · Timeline" rail and "Confirm Timeline / Confirm Checklist / Approve & Create" ladder (its lines 105-185, incl. a claim that create opens the transaction page - false today, true under D1); the Help Center content migration (`20260905090000`) describes a "nine steps" wizard with zero mentions of Verification / "Upload Transaction" | S8/§3.7 now carry the verified specifics |
| 10 | Phase 4 / matrix row 9 tested the empty state against "a colleague with a client role" | Client-role users never open the internal workspace at all (they have the client portal), so the check tested nothing | Acceptance rewritten against "a signed-in role outside the PATCH gate" |
| 11 | S2's "never triggers the due-date loops" and §3.2's Co-op Agent routing were asserted without citations | Now verified: the sweep skips undated tasks (`task_notification_service.py:811-813`) and Automated tasks (`:807-808`), resolves posture per deal, and `Co-op Agent` maps in both `TARGET_TO_GROUP` (`task_email_planner.py:118`) and `_AUTO_DRAFT_TARGET_ROLES` (`task_notification_service.py:742`); playbook-name lookup cannot shadow the request tasks (their names are not in `_EMAIL_PLAYBOOK`) | Citations added; Phase 2's planner test names the exact resolution path |
| 12 | (rev 3) S6 claimed "a repo-wide search finds no frontend caller" for `/ai/parse-checklist` | The caller chain exists - `useParseChecklist` (`useWizardApi.ts:600-620`) → `ChecklistImportModal.tsx` → `WizardChecklistStep.tsx` - but hangs entirely off the unreachable stale-draft guard step; the rev-2 search patterns were too narrow (`parse-checklist` was not among them). Functionally orphaned, not literally uncalled | S6 corrected; §3.6's retirement inventory enumerates the full chain (found by searching the endpoint path itself), so the deletion cannot leave dangling references |

*End of plan.*
