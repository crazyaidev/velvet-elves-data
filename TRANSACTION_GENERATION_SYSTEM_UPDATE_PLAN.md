# Transaction Generation System - Q&A-Driven Update Plan

**Status:** IMPLEMENTED 2026-07-03 (uncommitted; 6 new migrations for Jan to
apply — see the Implementation Status appendix at the end of this file for
what shipped, what was deliberately adjusted, and the small remaining items).
**Date:** 2026-07-02 (Revision 2, same day: corrections from a full
workflow/logic review against the source; see the defect register II.3 and
the "review corrections" notes marked [RC] throughout. Revision 3,
2026-07-03: implementation pass complete, status appendix added.)
**Author:** Jan
**Requirements basis:** `requirements.txt` Section 15 (added 2026-07-02 from
`Q&A_Transaction_Generation_System.md`)
**Supersedes / relates to:** extends the shipped task-engine architecture
(`20260605_task_engine_fix.sql`, the wizard preview/commit planner, the
timeline planner); supersedes the roll-forward deadline convention described
in `TRANSACTION_SYSTEM_GUIDE.md` Sections 4-7; answers guide Section 8.

---

## 0. Why this plan is grounded

Previous plans broke down in frontend testing because they were written
against an imagined system rather than the real one. This plan was drafted
only after reviewing, end to end:

**Documentation**
- `Q&A_Transaction_Generation_System.md` (Jake's five answers + his
  Attorney/Title Workflow workbook with per-state sources)
- `requirements.txt` (all 14 prior sections; new Section 15 now records the
  Q&A decisions)
- `TRANSACTION_SYSTEM_GUIDE.md` (the tester-facing description of today's
  behavior, screen by screen)
- `SYSTEM_DESIGN.md` (architecture, schema, API surface, RBAC matrix)
- `FRONTEND_UI_WORKFLOW_LOGIC.md` (Cross-Cutting Workflow A: New Transaction
  Creation; Workflows B/C for lifecycle and tasks)
- `STYLE_GUIDE.md` (v2 comfort scale, forms, chips, dialogs)
- `Real_Estate-Contract-Parsing-Agent-Instructions.txt` (contract-control
  rule set the resolution service implements)
- `milestones.txt`, `REWORKING_TASK_DB.csv`

**Backend source (velvet-elves-backend)**
- `app/services/task_generation_service.py` (plan/commit shared planner,
  use-case switching, date recompute)
- `app/services/dependency_engine.py` (due-date math, conditions evaluator,
  dual-agency filter, business-day helpers, roll-forward)
- `app/services/timeline_planner.py` (wizard timeline rows, added-deadline
  basis resolution)
- `app/services/requirement_planner.py` (compliance checklist planner)
- `app/services/plan_cascade.py` (live-deal anchor-change cascade)
- `app/services/state_rules.py` (current attorney/title state logic)
- `app/services/providers/prompts.py`, `providers/base.py`,
  `providers/parsing.py` (two-pass extraction schema and prompts)
- `app/services/contract_resolution.py` (cross-document controlling values)
- `app/services/document_processing.py` (double-check, confidence routing)
- `app/services/intake_intelligence.py` (AI proposals with citations)
- `app/api/v1/transactions.py` (create, preview-tasks, coverage warnings)
- `app/models/transaction.py`, `app/models/task_template.py`,
  `app/models/confidence_settings.py`, `app/models/enums.py`
- `supabase/migrations/202603111730_seed_task_templates.sql`,
  `20260605_task_engine_fix.sql`, `data/REWORKING_TASK_DB.csv`

**Frontend source (velvet-elves-frontend)**
- `src/components/wizard/NewTransactionWizard.tsx` (all steps, missing-field
  detection wiring, AI-apply mapping, submit payload)
- `src/components/wizard/wizardTypes.ts` (`REQUIRED_PURCHASE_FIELDS`,
  `detectMissingFields`)
- `src/components/wizard/WizardTimelineStep.tsx` (anchor card, deadline rows,
  AI suggestion cards with confidence chips)
- `src/components/wizard/ReviewTasksStep.tsx` (summary banner, undated and
  coverage notices)
- `src/pages/transactions/TransactionWorkspacePage.tsx` (live-deal tabs)

Everything in Part II below cites the actual file so the implementation can
be verified against reality, not memory.

---

## Part I - What Jake decided (requirements summary)

Numbered for traceability; the full text is `requirements.txt` Section 15.

| # | Requirement (short form) | Source |
|---|---|---|
| R1 | Contract silent on who orders title: ask the user at the wizard verification screen; the answer is required before the deal is created | Q1 |
| R2 | No brokerage default for who-orders-title | Q1 |
| R3 | Keep the "no title task" coverage notice as the safety net | Q1 (guide behavior Jake did not object to) |
| R4 | The title answer deterministically yields Order Title or Confirm Title Order, evaluated against representation side | Q1 + master list conditions |
| R5 | No standard/fallback deadline windows, ever | Q2 |
| R6 | Confidence bands: >=90% accept; 70-89% shown as a recommendation the agent approves; <70%/absent left blank to fill at submission | Q2 (+ Jan's confirmed response) |
| R7 | Improve AI recognition of the four windows (inspection, inspection response, HOA docs, insurance commitment), measurably | Q2 |
| R8 | Every cash deal, every state: AI reads an explicit appraisal election from the contract | Q3 |
| R9 | Elected = appraisal tasks; waived = none; silent/unsure = no tasks by default and the agent is prompted | Q3 (Jake confirmed "prompt the agent") |
| R10 | Remove the unconditional cash appraisal follow-up task from the master list | Q3 (Jan's response, acknowledged) |
| R11 | One-click flip of the appraisal answer on the live deal, preserving completed work | Q3 (guide suggestion, consistent with Jake) |
| R12 | Calendar days always by default; business days only when the contract definitively says so (or the agent sets it), read per deadline | Q4 |
| R13 | NO weekend/holiday roll of any deadline; deadlines may land on weekends and holidays | Q4 (Jake's final answer overrides the current convention and Jan's recommendation) |
| R14 | Each deadline displays its counting basis in plain language, with citation when AI-determined | Q4 + existing basis-chip pattern |
| R15 | Product usable in all 50 states: two base workflows + per-state differences | Q5 |
| R16 | No single "attorney state" boolean; per-state workflow flags per Jake's workbook | Q5 workbook |
| R17 | NC/SC/GA/DE: attorney owns legal/title/closing; agent task is "Confirm closing attorney selected and send executed contract", not "Order Title"; no default attorney-review deadline | Q5 workbook |
| R18 | NJ: 3-business-day attorney review from DELIVERY of fully signed contracts, only when a licensee prepared the contract; title-company roles preserved | Q5 workbook |
| R19 | NY: attorney-approval deadline only from contract language, contract's stated period; support both title pathways | Q5 workbook |
| R20 | All other states: standard title/settlement workflow until verified | Q5 workbook |
| R21 | Attorney-specific task library added (15 tasks per workbook), not a blind swap | Q5 workbook |
| R22 | FSBO/attorney-direct: reassign agent coordination tasks to customer/attorney; legal tasks intact; add "confirm who represents whom" | Q5 workbook |
| R23 | RESPA 12 U.S.C. 2608 guardrail on title-provider selection | Q5 workbook |
| R24 | Everything UI-validatable by non-developers, mouse-first, minimal typing; preview = commit; honest blanks | Cross-cutting (client's standing constraint) |

---

## Part II - Current-state audit (what the code actually does)

### II.1 The pipeline today

```
Upload (wizard Step 1)
  -> two-pass extraction  providers/prompts.py + document_processing.py
     (per-field confidence, sources map for <0.90 fields, double-check merge)
  -> cross-document resolution  contract_resolution.py
     (controlling values across PA/counters/amendments, 0.90 threshold)
  -> wizard state  NewTransactionWizard.tsx
     (applyIfBetter per field; needs-attention flags; missing-field detection)
  -> preview  POST /transactions/preview-tasks  api/v1/transactions.py:1665
     (plan_tasks_for_transaction + plan_timeline + plan_requirements;
      coverage warning when no title task; summary counts)
  -> commit  POST /transactions  ->  generate_tasks_for_transaction
     (same planner; exclusions/overrides/added tasks honored)
  -> live deal  plan_cascade.py (anchor moves), switch_use_case_tasks,
     recompute_task_dates
```

This preview-equals-commit shape is sound and is retained. Every change in
this plan is made inside the shared planner/parsers so both paths stay
identical (R24).

### II.2 Per-question findings

**Q1 - who orders title**
- The extraction prompt already reads `title_ordered_by` (buyer|seller|null)
  with detailed clause guidance (`providers/prompts.py:144-153`).
- The wizard Review-details step has a "Who Orders Title" Select with
  Buyer/Seller options (`NewTransactionWizard.tsx:5767-5789`), and AI values
  are mapped into it (`:1895-1913`).
- BUT the field is not required: `REQUIRED_PURCHASE_FIELDS` is only price,
  closing date, acceptance date (`wizardTypes.ts:903`), and
  `detectMissingFields` never flags it (`wizardTypes.ts:1005`). A deal can
  be created with it blank; the only guard is the Step-5 coverage warning
  (`api/v1/transactions.py:1775-1782`).
- DEFECT (D1): the seeded conditions compare against the literal `"us"`
  (`20260605_task_engine_fix.sql:98-100`:
  `[{"field":"title_ordered_by","value":"us"}]`), but the wizard submits
  `"Buyer"`/`"Seller"` unchanged (`NewTransactionWizard.tsx:3368`) and the
  create endpoint stores it raw (`api/v1/transactions.py:264`). With
  `evaluate_conditions`' case-insensitive equality
  (`dependency_engine.py:390-437`), `"Buyer" != "us"` means the "Order
  Title" task can never fire from wizard data, and the `ne` condition makes
  "Confirm Title Order" fire whenever ANY value is set, regardless of side.
  The same mismatch applies to `warranty_ordered_by` (`:104-106`). Unit
  tests pass because they feed `"us"`/`"other_party"` directly
  (`app/tests/test_dependency_engine.py:160-281`); the end-to-end wizard
  path is what's wrong.

**Q2 - deadline windows**
- Correct today: no fallback windows exist anywhere; unset windows leave the
  task undated with a reason (`dependency_engine.resolve_float_days_strict`,
  planner warnings in `task_generation_service.py:197-212`).
- Confidence machinery exists: two-pass merge penalizes disagreements
  (`document_processing.compare_extractions`), `ConfidenceSettings` has
  `auto_proceed_threshold=0.90` / `review_threshold=0.75` / global floor
  (`app/models/confidence_settings.py`), `/admin/confidence` UI exists.
- GAP (G1): the extraction schema has `insurance_days` and `hoa_doc_days`
  but NO explicit day-count fields for the inspection period or the
  inspection-response window (`providers/prompts.py:26-36`); those arrive
  only as a resolved `inspection_deadline` date. `inspection_response_days`
  is not extracted at all, only settable via the wizard command bar
  (`ai_service.py:716`). Jake's "train AI to recognize these fields" points
  exactly here.
- GAP (G2): there is no distinct 70-89% "recommendation to approve" UX for
  scalar fields. Today a below-0.90 field gets a needs-attention highlight,
  but the value is already placed in the input (silent fill), or it is
  blank. The AI-deadline suggestion cards on the Timeline step
  (`WizardTimelineStep.tsx:424`, confidence chip + Add/Skip) already embody
  the wanted pattern; scalar fields need the equivalent.

**Q3 - appraisal on cash deals**
- The parser reads only `appraisal_deadline` (a date). There is no
  appraisal-election field in the schema (`providers/prompts.py`), no
  `has_appraisal` on `Transaction` (`app/models/transaction.py`), no wizard
  question, and no template condition.
- DEFECT (D2): master-list task 265 "Appraisal Ordered" is tagged to
  `Buy Cash, Sell Cash` with NO condition (`data/REWORKING_TASK_DB.csv:69`,
  `task_family='appraisal_ordered'` in `20260605_task_engine_fix.sql:47`),
  so every cash deal gets an appraisal follow-up task, contradicting both
  the guide's description and R8-R10. There is no cash variant of
  "Appraisal Completed" (270 is Fin-only).

**Q4 - calendar vs business days**
- Everything is calendar-counted and then ROLLED FORWARD off weekends and
  US federal holidays: template task dates
  (`task_generation_service.py:188`, `:406-410`, `:541`), every timeline row
  and every requirement due date (`timeline_planner.offset_days:54-58`,
  used by `requirement_planner.py`), the live-deal cascade
  (`plan_cascade.py`), and added-task basis resolution.
- Jake's final ruling (R13) forbids the roll entirely. This is the single
  largest behavioral change in this plan and it touches four services plus
  their tests and the tester guide.
- Per-template `day_basis` ('calendar'|'business') and true business-day
  math (`add_business_days`, negative counts supported) already exist
  (`task_template.py:38`, `dependency_engine.py:366-387`) - but nothing
  reads a basis from the CONTRACT per deadline, and template basis is a
  static library property, not a per-deal fact (R12 needs per-deal).

**Creation paths (verified for gating design)** [RC]
- The full wizard is the ONLY UI path that creates a transaction today.
  `NewTransactionModal.tsx` is a modal HOST for the full
  `NewTransactionWizard` (embedded), not a separate quick-create form; the
  drag-drop `IntakeConfirmationModal.tsx` only attaches documents to
  existing deals or hands the files to the wizard. The quick-create modal
  described in `requirements.txt` 2.4a / Workflow A is NOT implemented.
  Consequence: wizard-side gates cover every UI creation path; the only
  bypass is the raw API. (If 2.4a's quick-create is ever built, it must
  carry the same gates.)

**Q5 - states / attorney workflows**
- DEFECT (D3): `state_rules.py` implements exactly the design Jake's
  workbook forbids: one binary `ATTORNEY_CLOSING_STATES` set of 24 states
  (including FL, PA, VA, ND, SD, MD, ME, MS, VT, WV... none verified by the
  workbook), used as a fallback when `closing_mode` is unset, plus
  name-substring filtering ("attorney" in task name). Unverified states can
  silently flip into an attorney workflow that has no tasks.
- The master list contains ZERO attorney tasks (grep across
  `REWORKING_TASK_DB.csv` and all seed migrations). `closing_mode`
  (attorney|title_escrow|shared_approval) is parsed from the contract and
  stored, and the Attorney RBAC role/dashboard exist, so the selection
  switch is real; the CONTENT and the per-state flags are what is missing.
- Nothing models: NJ licensee-prepared trigger and delivery-of-signed-
  contracts start date; NY contract-detected approval clause; FSBO
  reassignment of agent-targeted tasks (FSBO deals exist via `is_fsbo` /
  `fsbo_state`, but planner `target` strings are fixed).

### II.3 Defect register feeding this plan

| ID | Defect / gap | Fixed in phase |
|----|---|---|
| D1 | `title_ordered_by`/`warranty_ordered_by` semantics mismatch ("us" vs Buyer/Seller): title tasks mis-selected end to end | Phase 1 |
| D2 | Cash appraisal task fires unconditionally (task 265) | Phase 3 |
| D3 | Binary attorney-state list + name-matching filter contradicts workbook; unverified states misclassified | Phase 5 |
| D4 | [RC] `switch_use_case_tasks` matches by task NAME (`task_generation_service.py:522-529`): a non-completed manual or AI-added task whose name is not in the new template set is DELETED on a use-case switch, and re-adds also key on name. User-created work can be silently destroyed by a Fin<->Cash switch (route `transactions.py:1163`). | Phase 3 (the `retarget_conditional_tasks` generalization replaces this machinery) |
| G1 | No explicit extraction of inspection / inspection-response day counts | Phase 2 |
| G2 | No 70-89% recommendation-approval UX for the decision-critical fields | Phase 2 |
| G3 | Roll-forward baked into all deadline math (now contra-requirement) | Phase 4 |
| G4 | No appraisal-election field, transaction flag, or prompt | Phase 3 |
| G5 | No attorney task content, state flags, NJ/NY deadline logic, FSBO reassignment | Phase 5 |

---

## Part III - Target design

### III.1 One shared decision spine (applies to every question)

All five answers share one shape, so the build uses one spine:

```
contract says it clearly (>= accept threshold)  -> use it, show citation
contract suggests it (recommendation band)      -> show AI recommendation,
                                                   agent clicks Approve/Change
contract silent / below band                    -> honest blank + REQUIRED
                                                   mouse-first prompt when the
                                                   value gates task generation
```

Gating values (must be answered before "Approve & Create"): who orders
title, appraisal election (cash deals). Non-gating values (windows, bases)
may remain blank; their tasks stay undated with the existing warnings.

[RC] Gates are WORKFLOW-AWARE. The who-orders-title question is a
title-company-workflow question; in an attorney-controlled closing the
attorney owns title work and forcing a Buyer/Seller answer would be wrong
(and would then fight the coverage check). Rule: the title gate applies
only when the deal's resolved closing workflow expects a party-side title
answer - `closing_mode != 'attorney'` in Phase 1, refined by the state
profile in Phase 5 (III.6). The appraisal gate applies to cash deals in
every workflow.

Confidence bands come from `ConfidenceSettings`: accept =
`auto_proceed_threshold` (default 0.90), recommend-floor = new column
`recommendation_floor` (default 0.70, admin-editable on `/admin/confidence`,
clamped >= global floor). Nothing is hardcoded; Jake's "90%" and Jan's
"70-89" become the defaults of existing machinery.

### III.2 Q1 - Required title answer (R1-R4, D1)

**Semantics fix (D1) - the foundation.** Keep storing the contract-literal
side (`Buyer`/`Seller`) on the transaction; it is what the contract and the
agent both speak. Introduce a derived predicate in the planner:

```
title_responsibility(tx) -> 'us' | 'counterparty' | None
  Buy-side  (use_case Buy-*)  : Buyer orders  -> us;  Seller orders -> counterparty
  Sell-side (use_case Sell-*) : Seller orders -> us;  Buyer orders  -> counterparty
  Dual      (use_case Both-*) : always us (we represent both sides)
  None                        -> None (no title task; coverage warning fires)
```

[RC] The side is derived from `use_case` (Buy-*/Sell-*/Both-*), not from
the freetext `representation_type`, because use_case is the value the
planner already keys everything on and it is normalized by construction.

`evaluate_conditions` (`dependency_engine.py`) learns a small set of
DERIVED FIELDS (computed from the transaction, not stored):
`title_responsibility`, `warranty_responsibility`, and (Phase 3/5)
`has_appraisal`, workflow flags. A migration rewrites the two seeded
conditions to `[{"field":"title_responsibility","value":"us"}]` (and `ne`),
same for warranty. Existing unit tests are extended to cover the
Buyer/Seller x representation matrix, including dual agency.

**Wizard behavior (R1, R2).**
- Add `title_ordered_by` to the required set: `detectMissingFields`
  (`wizardTypes.ts`) flags `purchase.title_ordered_by` when unset, so the
  existing Missing Info step machinery (step gating at
  `NewTransactionWizard.tsx:4255-4256`, `MissingFieldRow`, resolve/dispatch)
  carries it with zero new flow logic. The Review-details Select becomes
  `required` (asterisk + needs-attention treatment it already supports).
- [RC] The requirement is CONDITIONAL on workflow: `detectMissingFields`
  skips it when `purchase.closing_mode === 'attorney'` (the parser already
  reads closing_mode). `shared_approval` KEEPS the question: a title
  company still participates in that mode, so someone's side still orders
  title. Pre-Phase-5 an attorney-closing deal therefore behaves exactly as
  today (no buyer/seller title tasks seeded conditions can produce, honest
  coverage warning on Step 5); Phase 5 gives those deals attorney title
  tasks and teaches the coverage check to accept them (III.6.3).
- The Missing Info row for this field is a mouse-only choice card, not a
  text input: two large option buttons "Buyer orders title" / "Seller
  orders title", each with a one-line consequence caption computed from the
  representation ("Your side -> an 'Order Title' task will be created" /
  "Other side -> a 'Confirm Title Order' task will be created"). No typing,
  one click (R24).
- No brokerage default anywhere (R2): explicitly OUT of scope; no settings
  key, no pre-selection.
- Keep the Step-5 coverage warning untouched as the net (R3); after this
  change it should only ever appear on attorney-closing deals pre-Phase-5
  and on API-created deals that bypassed the wizard.

**Other creation paths.** [RC] There is no quick-create form to extend:
every UI creation path runs the full wizard (see II.2 "Creation paths"),
so the wizard gate is complete for the UI. The workspace coverage banner
with an inline one-click resolver (two buttons; answering generates the
right task via the condition-based add machinery in III.4) exists for the
two real gaps: deals created directly through the API, and deals that
already exist when this ships. If the 2.4a quick-create modal is built
later, it must include the same gate.

### III.3 Q2 - Window recognition + recommendation band (R5-R7, G1, G2)

**No fallback windows (R5).** Already true; the plan adds a regression test
asserting that a silent contract yields blank windows and undated tasks (so
no future change can quietly add defaults).

**Extraction improvements (R7, G1).** Extend the extraction schema
(`providers/prompts.py`, `providers/base.py` FieldExtraction set,
`providers/parsing.py` mapping):
- `timeline.inspection_days` (integer), `timeline.inspection_response_days`
  (integer) - the day COUNTS as written, alongside the existing resolved
  dates; `insurance_days` and `hoa_doc_days` stay.
- Prompt guidance for each window mirroring the successful
  `title_ordered_by` pattern (common clause phrasings, checkbox/blank/n-a
  handling, "return the count the contract states, do not compute").
- The two-pass double-check and the sources map (page + verbatim snippet
  required under 0.90) apply automatically since these are ordinary fields.
- Extend `extraction_benchmark.py` fixtures with labeled contracts covering
  the four windows (stated, silent, n/a, counter-offer-overridden) so
  recognition quality is a measured number before/after prompt work (R7:
  "train AI to recognize these fields better" must be provable).

**Recommendation band UX (R6, G2).** [RC] Scope: the three-way treatment
applies to the DECISION-CRITICAL fields only - the four windows
(`inspection_days`, `inspection_response_days`, `hoa_doc_days`,
`insurance_days`/`insurance_commitment_days`), `title_ordered_by`,
`appraisal_election` (Q3), and per-deadline bases (Q4). That is what the
Q&A actually asks for; applying empty-until-approved to EVERY parsed field
would hollow out the wizard (address, price, parties would arrive blank at
75% confidence) and regress the working flow. All other fields keep
today's behavior: value filled, needs-attention highlight, double-check
panel. Per scoped field:
- confidence >= accept: value fills the input; magnifier citation as today.
- recommend band (0.70-0.89 default): the input stays EMPTY (the
  `applyIfBetter` mapping layer in `NewTransactionWizard.tsx` skips the
  fill for scoped fields in this band); directly under it renders an amber
  recommendation chip-row: sparkle icon, "AI suggests: 10 days - 82% -
  'Buyer shall have 10 days...' (p. 4)", with two ghost buttons
  [Use 10 days] [Enter manually]. One click accepts; the citation opens
  the evidence viewer at the highlighted clause (existing
  `fieldSourceProps` / evidence-viewer plumbing).
- below band / absent: plain blank; flagged by Missing Info only when the
  contingency was opted into (existing `detectMissingFields` conditional
  logic, unchanged).
- The same treatment is reused verbatim for Q1's select and Q3's election
  prompt, so testers learn ONE pattern. When a GATING field sits in the
  recommend band, its Missing Info option-card row carries the same
  recommendation chip, so the AI's read is never lost between steps.

Server side, the per-field band comes from the parse payload the wizard
already receives (`per_field` confidences + sources). [RC] The wizard
currently hardcodes its band cutoffs; add a small read-only
`GET /api/v1/confidence/effective` (current tenant's resolved thresholds
incl. `recommendation_floor`) so the wizard and `/admin/confidence` agree
on one source of truth. `recommendation_floor` relates to the existing
knobs as: recommend band = [recommendation_floor, auto_proceed_threshold);
below recommendation_floor is treated as not-found for the scoped fields.
`review_threshold` keeps its existing document-level review-routing
meaning; the two are validated so floor <= review <= accept.

### III.4 Q3 - Appraisal election on cash deals (R8-R11, D2, G4)

**Parse (R8).** Add to the extraction schema:
- `detection.appraisal_election`: `"elected" | "waived" | null` with prompt
  rules: read the appraisal contingency/addendum checkbox or language on
  EVERY document of a cash deal regardless of state; explicit waiver
  language -> waived; an appraisal contingency opted into, an appraisal
  addendum, or an appraisal deadline filled in -> elected; template text
  merely present -> null. Confidence + citation as any field. (An existing
  `appraisal_deadline` value is corroborating evidence for "elected", and
  the resolver treats an explicit later waiver as controlling, per the
  document-control hierarchy in `contract_resolution.py`.)
- Resolution: add `appraisal_election` to `SCALAR_FIELDS` so counters and
  addenda override the PA read.

**Model.** `transactions.has_appraisal BOOLEAN NULL` (tri-state; NULL =
unanswered). Financed deals: the field is not consulted (lender always
requires appraisal; templates keep their Fin tagging). Cash deals: it
gates the appraisal family.
[RC] Full plumbing is part of the work, or preview and commit diverge:
model field, `TransactionCreateRequest`/update schemas
(`app/schemas/transaction.py`), repo `create`/row mapping
(`transaction_repository.py`), the preview's transient builder
(`_request_to_transient_transaction`, `api/v1/transactions.py:1619`), and
the wizard submit payload (`NewTransactionWizard.tsx` ~:3340). The same
plumbing checklist applies to every new transaction field this plan adds
(Q4's basis map, Q5's NJ/NY fields).

**Master list (R10, D2).** Migration:
- Task 265 (cash "Appraisal Ordered") gains
  `[{"field":"has_appraisal","value":true}]`.
- New global cash variant of "Appraisal Completed": task_family
  `appraisal_completed`, `use_cases` Buy-Cash/Sell-Cash, same condition.
  [RC] Wiring precision: due-date math keys on `legacy_task_id`
  (`calculate_due_dates`), so the new row gets its own unused synthetic
  legacy id (e.g. 271) and `dep_task_ids=[265]` - a dependency on the
  task id, not on the family name.
- `evaluate_conditions`' existing None-excludes rule then gives R9's
  default for free: NULL election -> no appraisal tasks.

**Wizard prompt (R9).** For cash use cases (`*-Cash` derived use case) with
election unresolved (parse null or below accept band):
- Review-details "Deal specifics" section gains a required row "Appraisal
  on this cash deal?" with two option buttons [Yes - buyer is appraising]
  [No appraisal], plus the recommendation chip when the parse landed in the
  recommend band ("AI suggests: No appraisal - 78% - 'Buyer waives...'").
- `detectMissingFields` flags it for cash deals when null, making it
  blocking exactly like Q1 (one shared gating mechanism, R24).
- Preview coverage: `preview_tasks` adds a second coverage rule - cash deal
  with `has_appraisal` NULL -> "No appraisal decision recorded - confirm
  whether this cash deal includes an appraisal." (belt for API-created
  deals; the wizard gate makes it unreachable from the UI).

**Live-deal flip (R11) - and the D4 fix.** On the transaction workspace
(Timeline tab key facts / Overview summary), a read-only "Appraisal:
Yes/No" value with a pencil; editing opens a two-button popover. Saving
PATCHes the transaction and runs a NEW `retarget_conditional_tasks`
service (audit-logged, toast "2 appraisal tasks added"). No page reload;
optimistic per §9.4b.
[RC] `retarget_conditional_tasks` is a corrected generalization of
`switch_use_case_tasks`, NOT a copy of its semantics, because the existing
function has a destructive defect (D4): it deletes any non-completed task
whose NAME is not in the new template set, which wipes manual and AI-added
tasks on a use-case switch. The corrected contract:
- Re-plan with the shared planner, then diff BY `template_id` against
  existing tasks; only tasks with `template_id` set (source="template")
  are ever removed, and only when their template no longer applies.
- Tasks with `source` in {manual, ai} are never touched.
- Completed tasks are always preserved (existing rule, kept).
- For a single-field flip (appraisal), the diff naturally touches only the
  templates whose conditions reference the changed field; the same service
  replaces the body of `switch_use_case_tasks` so the Fin<->Cash switch
  route (`transactions.py:1163`) is fixed by the same change.

### III.5 Q4 - Calendar days, never rolled; per-deadline basis (R12-R14, G3)

**Remove the roll (R13).** Deadline-producing paths stop calling
`roll_forward_to_business_day`:
- `task_generation_service.plan_tasks_for_transaction` (line 188), added
  tasks (:406-410), `switch_use_case_tasks` (:541)
- `timeline_planner.offset_days` (:54-58) - which automatically fixes
  `requirement_planner` and `resolve_added_task_basis`
- `plan_cascade.py` recomputations
The helper itself and `us_federal_holidays` remain (business-day COUNTING
still needs them; and the notification layer may still want "this lands on
a Sunday" awareness for display, see UI below).

**Per-deadline basis (R12).** Two layers, matching where deadlines are born:
1. **Contract-read basis.** Extraction schema gains, for every deadline/
   window field, a companion basis read collected into
   `timeline.deadline_bases`: `{ "<field>": "calendar" | "business" }`,
   emitted ONLY when the contract definitively states the basis for that
   deadline ("within 5 business days", "10 banking days"); otherwise the
   key is omitted. Stored on the transaction as
   `deadline_day_basis_json JSONB DEFAULT '{}'`. Anything absent = calendar
   (R12 default). [RC] Keying rule: the map is keyed by the canonical TERM
   field names (`inspection_days`, `inspection_response_days`,
   `hoa_doc_days`, `insurance_commitment_days`, plus custom-deadline
   client keys). A basis only exists for values the system COUNTS;
   deadlines the parser extracts as absolute dates (closing, possession,
   appraisal_deadline, financing_deadline) have nothing to count and get
   no basis entry. Plumbing per the III.4 checklist (schema, repo,
   transient builder, submit payload).
2. **Computation.** `timeline_planner` and the dependency engine consult
   the per-deal map first, then the template's `day_basis`, then
   'calendar'. [RC] For template tasks the lookup key comes from the
   wizard-field reference already inside the template's offset: a template
   whose `float_days` is `wizard:inspection_response_days` resolves its
   basis from `deadline_day_basis_json["inspection_response_days"]`;
   templates with literal numeric offsets keep their own `day_basis`
   column. `_describe_due_basis` (`task_generation_service.py:140`)
   follows the same resolution order so the displayed chip can never
   disagree with the computed date. Business basis uses the existing
   `add_business_days` (negative counts included: "10 business days before
   closing"). The END date of a business-day count is whatever day the
   count lands on; there is no separate roll step anywhere.

**Agent override (R12 "written in by an agent").** Wherever a rule-based
deadline is editable (Timeline step "Edit days" popover, added-deadline
modal `AddDeadlineModal`/`RuleFields`, workspace date-edit popovers), the
days input gains a two-option toggle `calendar | business` defaulting to
calendar (or the AI-read basis, shown with its citation chip). One extra
click, no typing (R24).

**Display (R14).** Basis strings gain the word "business" when applicable:
timeline rows ("5 business days after Date of Acceptance"), planner
`due_basis` (already handles it: `task_generation_service.py:146-148`
appends "business"), workspace basis chips. Where a deadline lands on a
weekend/holiday, the row shows a neutral gray hint chip "lands on Sat" -
informational only, no date change (this preserves the useful awareness the
roll used to provide, without moving anything).

**Consequences to manage (called out honestly):**
- Existing tests asserting roll behavior (dependency engine, timeline,
  requirement, cascade suites) flip to assert NO roll; a new test pins
  "Saturday stays Saturday".
- Live deals: dates already stored do not silently change. The workspace's
  existing recompute/cascade preview (`recompute_task_dates`,
  `plan_cascade`) shows old -> new when the user next touches an anchor,
  which is the honest way to migrate in-flight deals.
- `TRANSACTION_SYSTEM_GUIDE.md` Sections 4-7 and the Step-3/Step-5 helper
  copy must be rewritten in the same pass (the guide currently PROMISES the
  roll; testers verify against the guide).
- Task queue/calendar views will now show weekend due dates; "Due Today"
  buckets already handle any date, verified in Phase 6 scripts.

### III.6 Q5 - State workflow profiles + attorney content (R15-R23, D3, G5)

**III.6.1 State workflow profiles (R16, R20, D3).** New global table
`state_workflow_profiles` (platform-managed, RLS read-all):

```
state CHAR(2) PK
cluster TEXT            -- 'attorney_controlled' | 'attorney_review_mixed'
                        -- | 'title_escrow' | 'unverified'
requires_attorney_closing_control BOOL
requires_attorney_title_opinion_or_exam BOOL
requires_attorney_supervised_disbursement BOOL
has_default_attorney_review_period BOOL
attorney_review_trigger TEXT    -- 'delivery_of_signed_contract' |
                                -- 'contract_clause' | 'none'
title_company_role_allowed TEXT -- 'support' | 'mixed' | 'standard'
agent_orders_title_default BOOL
fsbo_reassigns_agent_tasks_to_customer BOOL DEFAULT true
verified BOOL
sources_json JSONB              -- workbook citations (NC Bar, SC Bar, GA
                                -- Supreme Court, DE ODC, NJ DOBI, NYSBA)
```

Seed exactly per the workbook: NC/SC/GA/DE attorney_controlled; NJ/NY
attorney_review_mixed (NJ has_default_attorney_review_period=true,
trigger=delivery; NY trigger=contract_clause); IN and the other named
title states title_escrow; EVERYTHING ELSE `unverified` behaving as
title_escrow (R20). `state_rules.py` is rewritten to read the profile;
`ATTORNEY_CLOSING_STATES` / `TITLE_ESCROW_STATES` frozensets and the
name-substring filtering are deleted.

[RC] **Precedence, spelled out** (the workbook separates state
classification from contract detection, and so must we):
- Explicit `closing_mode` from the contract wins over geography for
  SELECTING the base workflow (the parser already reads it).
- The state profile supplies the default mode and the statutory FLAGS.
- A contract-declared attorney closing in an `unverified` state selects
  the GENERIC attorney workflow (attorney conducts closing, agent
  coordinates), but the statutory flag-gated extras (title opinion,
  supervised disbursement, five-part supervision) stay OFF - those are
  verified state law, not contract facts. No state is ever treated as
  attorney-controlled by geography alone unless its profile is verified.

[RC] **How the profile reaches the (sync, pure) planner.**
`plan_tasks_for_transaction`, `evaluate_conditions`, and
`apply_state_rules` are synchronous and must stay pure (preview == commit
depends on it). The profile is therefore loaded ONCE per request in the
async entry points and threaded through as a planning context parameter:
`preview_tasks_for_transaction`, `generate_tasks_for_transaction`,
`switch_use_case_tasks` / `retarget_conditional_tasks`,
`recompute_task_dates` (`task_generation_service.py`), and
`plan_cascade.py` each fetch the profile for `transaction.state` and pass
it down; `evaluate_conditions` gains an optional derived-fields mapping
(title/warranty responsibility computed from the transaction, workflow
flags from the passed profile). No hidden I/O inside the planner.

**III.6.2 Template selection by workflow (R21).** Templates gain
`workflow TEXT DEFAULT 'title_escrow'`
(`'title_escrow' | 'attorney_controlled' | 'attorney_review_mixed' | 'any'`)
plus conditions on the derived workflow-flag fields (III.2's derived-field
evaluator exposes the profile flags, e.g.
`[{"field":"requires_attorney_title_opinion_or_exam","value":true}]` on the
title-opinion tasks). Selection in `apply_state_rules` becomes: keep
`'any'` + the resolved workflow's rows, then conditions prune within the
cluster. No name matching.

**III.6.3 Attorney task library (R17, R21).** Seed the 15 workbook tasks as
global templates (new `Attorney` target value; `task_family` set;
conservative offsets; dependencies rooted at the acceptance/closing anchors
and at each other, mirroring the title-company chain shape):

Engagement: Confirm attorney selected (agent/customer);
Confirm attorney representation & scope (attorney+customer; also FSBO).
Contract: Send executed contract to attorney (agent/customer; REPLACES
"send to title" coordination in attorney_controlled - and in that cluster
`agent_orders_title_default=false` suppresses Order Title/Confirm Title
Order via a derived-field condition, satisfying R17's "agent task is
confirm-and-send, not order title"); Attorney contract review (deadline
only when III.6.4 creates one).
[RC] The Step-5 coverage check (`transactions.py:1775-1782`) is extended
in the same change: title coverage is satisfied by EITHER the
title-company families (order_title/confirm_title_order) OR the attorney
title families; and the Q1 wizard gate does not demand a Buyer/Seller
answer on these deals (III.2). Without this, an NC deal would generate a
correct attorney list and still scream "no title task" while blocking on
a question that has no right answer.
Title: Order or supervise title search/abstract; Preliminary title opinion
/ title certificate (flag-gated: NC, DE); Review title results and
exceptions; Resolve title defects / curative work; Apply for / coordinate
title insurance (NC note: requires attorney opinion first).
Documents: Prepare or review deed; Prepare or review deed of trust /
security documents.
Closing/funds/recording: Conduct or control closing; Authorize or
supervise disbursement (flag-gated); Authorize or supervise recording.
Post-closing: Final title opinion / final title work (flag-gated).

Dual-agency behavior `standard`, cc/targets per workbook owners. The
existing dedupe net (`filter_both_representation`) applies unchanged.

**III.6.4 NJ / NY deadline logic (R18, R19).** New parse fields:
- `detection.contract_prepared_by_licensee` (true|false|null) - NJ forms
  carry the mandated attorney-review clause text; its presence plus
  broker/licensee preparation indicators drive this.
- `timeline.contracts_delivered_date` (date|null) - delivery of fully
  signed contracts when stated.
- `detection.attorney_approval_clause`
  `{present: bool, days: int|null, day_basis: 'calendar'|'business'|null,
    start: 'delivery'|'acceptance'|null}` - NY-style contract-detected
  clause, generic enough for any state whose CONTRACT creates the period.

[RC] These resolved values must be PERSISTED, not just parsed:
`timeline_planner.plan_timeline` is pure over the Transaction, so the
migration adds `contract_prepared_by_licensee BOOLEAN NULL`,
`contracts_delivered_date DATE NULL`, and `attorney_review_json JSONB
NULL` (the clause struct) to `transactions`, with the full III.4 plumbing
checklist (schemas, repo, transient preview builder, wizard payload).
Otherwise the wizard preview would show the NJ/NY rows and the committed
deal would lose them.

Timeline planner rules (all honest-blank):
- NJ + licensee-prepared true: "Attorney Review Deadline" = 3 BUSINESS days
  from `contracts_delivered_date`; when the delivery date is unknown the
  row renders undated with reason "Waiting on the delivery date of the
  fully signed contracts" and a one-click date fill (never counted from
  acceptance, per workbook). Not created for NJ FSBO/no-licensee (R22).
- Any state + `attorney_approval_clause.present`: deadline from the
  clause's own days/basis/start. No clause, no deadline - including NC/SC/
  GA/DE (R17) and NY (R19).
- NY title pathway (R19): no forced owner. The People/parties model
  already holds both `title_company` and `closing_attorney`; the planner
  assigns title tasks to whichever the deal actually has, and when both
  are absent on an attorney_review_mixed deal the wizard's existing
  missing-party flow asks (mouse-first add-party modal).

**III.6.5 FSBO / attorney-direct assignment (R22).** A single owner-
resolution step at the end of planning: when the deal `is_fsbo` (or a
future attorney-direct flag) and the profile's
`fsbo_reassigns_agent_tasks_to_customer` is true, planned tasks whose
owner is the agent-coordination role are re-owned to the customer;
attorney-owned legal tasks are untouched (guarded by workflow flags, not
names). "Confirm attorney representation & scope" is always included for
FSBO/attorney-direct in attorney workflows (the workbook's "confirm who
represents whom").
[RC] Scope honesty about the FSBO surface: FSBO customers have NO
task-execution UI and must not get one here (requirements 1.2g: FSBO
cannot edit back-office tasks). What exists is `fsbo_workspace.py`, which
already derives the customer's read-only milestone timeline and
"next steps" FROM the deal's tasks. So "reassign to customer" means:
(a) the planned task's owner label becomes "Customer" (internal views and
the workbook's audit expectations stay honest), and (b) the existing FSBO
next-steps derivation surfaces those customer-owned items in plain
English, which it already does for tasks generally. No new customer task
UI is built in this plan; if attorney-direct customers later need to
CHECK OFF items, that is the separate intake workstream in Part IX Q3.

**III.6.6 Guardrail (R23).** The title-provider selection surfaces (wizard
party add, workspace People tab) get a neutral helper line on seller-side
deals: "The buyer cannot be required to use a particular title insurance
company (RESPA 12 U.S.C. 2608)." Copy only; no behavioral hard-block, no
legal advice framing (consistent with 8.6 attorney guardrails).

---

## Part IV - Frontend UI/UX specification

Design language: STYLE_GUIDE v2 comfort scale; ve-* tokens only; IBM Plex
Sans / Plex Mono numerals with tabular-nums on all dates; flat headers +
hairline dividers, sentence-case section labels, SegmentedControl for
either/or choices, shadcn Select for lists, Radix dialogs only (no
hand-rolled overlays); lucide icons, never emoji; pages own their scroll
(`flex h-full min-h-0 flex-col overflow-hidden` + inner scroll). Every
surface below is verified by rendering + headless-Chrome screenshot before
being called done.

**IV.1 Wizard Review-details (verification screen).**
- "Deal specifics" field table gains required markers on Who Orders Title
  (non-attorney closings only, per III.2 [RC]) and the new "Appraisal on
  this cash deal?" row (cash only, all workflows).
- The three-state pattern per III.3: filled+citation / empty+amber
  recommendation chip-row with [Use value] ghost button / plain empty.
  The recommendation row is one line, flat, amber-100 border, no gradient.
- Consequence captions under the title and appraisal choices (one line,
  ve-muted): they translate the answer into the task that will exist,
  teaching testers cause -> effect without a manual.

**IV.2 Wizard Missing Info step.** Gating fields render as option-card rows
(two large click targets, 48px min height, keyboard accessible), not text
inputs; when the parse landed in the recommend band the row carries the
same recommendation chip as Review details, so the AI's read follows the
user across steps [RC]. The step's existing continue-gate already blocks
until resolved. The AI public-source search affordance stays for
contact-type fields and is NOT offered for title/appraisal decisions (they
are contract decisions, not lookup facts).

**IV.3 Wizard Timeline step.**
- Deadline rows: basis text extended ("5 business days after Date of
  Acceptance"); a small gray "lands on Sat" hint chip when applicable; the
  existing confidence chip + citation link for AI rows unchanged.
- "Edit days" popover: days stepper + calendar/business SegmentedControl
  (default calendar). Same control inside Add deadline modal (RuleFields).
- NJ attorney-review row when undated: reason line + inline date picker for
  delivery date (one click + date pick).

**IV.4 Tasks & create (Step 5).** Unchanged structurally (summary banner,
undated notice, coverage notices, per-task checkboxes). New: second
coverage rule for the cash-appraisal gap; "why included" strings now cover
the derived conditions ("We order title (your side, per your answer)",
"Buyer elected an appraisal", "Attorney-controlled closing state").

**IV.5 Transaction workspace (live deal).**
- Key facts row: "Appraisal: Yes/No" with pencil -> two-button popover;
  flipping shows the add/remove preview toast; audit-logged.
- Coverage banner variant for deals created without the title answer:
  amber, one line, two inline buttons [Buyer orders] [Seller orders],
  resolves in place (memory rule: fixes resolve in place, never bounce to
  another page).
- Task rows: basis chip may read "3 business days before Closing"; no
  other change.

**IV.6 Coverage banners on the workspace (replaces the earlier
"quick-create" item).** [RC] There is no quick-create form in the
implemented app (II.2 "Creation paths"): `NewTransactionModal` hosts the
full wizard, so the wizard gates cover every UI creation path. The
workspace coverage banners (IV.5) are the net for API-created deals and
for deals that predate this update; both resolve in place with the same
two-button controls. Should the 2.4a quick-create modal ever be built, it
must ship with the same gates (recorded as a constraint, not work in this
plan).

**IV.7 /admin/confidence.** One new slider "Recommendation floor" between
review threshold and accept threshold with live validation (cannot exceed
accept, cannot go below global floor), matching the existing two sliders.

**IV.8 Task Templates page.** Templates gain a read-only "Workflow" chip
(Title company / Attorney / Mixed / Any) in the row + a Select in the
editor; the state-profile matrix itself is platform-managed data, not
tenant UI, in this phase.

---

## Part V - Implementation phases

Ordering rationale: Phase 0+1 fix correctness the other phases depend on
(derived-field evaluator, gating pattern); 2-4 are independent of each
other; 5 is the largest and consumes 1-4's machinery (derived fields,
basis math, recommendation UX); 6 is the tester-facing hardening pass that
the client's principles demand.

### Phase 0 - Foundations (small, unlocks everything)
- Derived-field evaluator in `dependency_engine.evaluate_conditions`:
  an optional derived-values mapping computed OUTSIDE the evaluator and
  passed in (`title_responsibility` / `warranty_responsibility` from
  use_case x stored side; later `has_appraisal` passthrough and Phase 5
  workflow flags from the pre-fetched state profile). The evaluator stays
  sync and pure; the async entry points (preview, generate, retarget,
  recompute, cascade) build the mapping once per request [RC].
- `ConfidenceSettings.recommendation_floor` column + validation
  (floor <= review <= accept) + read-only
  `GET /api/v1/confidence/effective` + admin slider [RC].
- Migration `2026090[6]090000_derived_condition_semantics.sql`: rewrite
  seeded title/warranty conditions to derived fields.
- Tests: use_case x side matrix; dual agency; None handling.

### Phase 1 - Q1 title answer required (R1-R4)
- Frontend: `wizardTypes.ts` required/missing updates, SKIPPED when
  `closing_mode === 'attorney'` [RC]; option-card row on Missing Info;
  required Select on Review details; workspace coverage banner resolver
  (net for API-created and pre-existing deals; there is no quick-create
  surface to change [RC]).
- Backend: coverage warning kept; PATCH path for the banner resolver
  triggers conditional task add (reuses Phase 3's `retarget_conditional_
  tasks` if sequenced after, else a title-scoped equivalent).
- Tests: wizard cannot submit without the answer on a title-company deal;
  attorney-closing deal is NOT blocked by the title question; preview
  shows exactly one title task per answer; banner resolver generates the
  right task.

### Phase 2 - Q2 window recognition + recommendation band (R5-R7)
- Extraction schema + prompts for `inspection_days`,
  `inspection_response_days`, prompt guidance for all four windows;
  parsing.py/base.py plumbing; resolution SCALAR_FIELDS additions.
- Benchmark fixtures + baseline run recorded in the PR description
  (before/after numbers).
- Frontend recommendation chip-row component (shared; used by Q1/Q3 too);
  band logic from per-field confidence + settings.
- Regression test: silent contract -> blank windows, undated tasks, no
  defaults.

### Phase 3 - Q3 cash appraisal election (R8-R11, D4)
- Extraction `detection.appraisal_election` + resolution field.
- Migration: `transactions.has_appraisal` (+ full schema/repo/transient-
  builder/submit plumbing per III.4 [RC]); condition on task 265; new cash
  "Appraisal Completed" template (own synthetic legacy id,
  `dep_task_ids=[265]` [RC]).
- Wizard gating row (cash only) + recommendation chip; preview coverage
  rule.
- `retarget_conditional_tasks` service with the corrected diff-by-
  template_id contract (never touches manual/AI tasks; replaces the body
  of `switch_use_case_tasks`, fixing D4 for the use-case switch route
  too [RC]) + PATCH endpoint + workspace pencil/popover; audit events.
- Tests: elected/waived/silent through the wizard; flip preserves
  completed tasks AND manual/AI tasks; Fin<->Cash switch no longer
  deletes a manual task (D4 regression).

### Phase 4 - Q4 calendar-only, per-deadline basis (R12-R14)
- Remove roll-forward from the four services; keep business-day math.
- Extraction `timeline.deadline_bases`; transaction
  `deadline_day_basis_json` (+ III.4 plumbing checklist [RC]); planner/
  dependency basis resolution order (deal map keyed by term-field name,
  template offsets resolved via their `wizard:<field>` reference ->
  template day_basis -> calendar; `_describe_due_basis` follows the same
  order [RC]).
- Basis toggle in Edit-days popover / Add deadline modal; "lands on Sat"
  hint chip; basis strings.
- Flip/inversion of existing roll tests; new no-roll pins; cascade
  old->new preview verified on a live deal.
- Rewrite `TRANSACTION_SYSTEM_GUIDE.md` Sections 4-7 + Step 3/5 copy.

### Phase 5 - Q5 states + attorney workflows (R15-R23)
- 5a Migration: `state_workflow_profiles` + seed (workbook values +
  sources_json); templates `workflow` column.
- 5b `state_rules.py` rewrite (profile-driven; delete frozensets and name
  matching); profile fetched once per request in the async entry points
  and threaded into the planner/evaluator as context (no I/O inside the
  pure planner [RC]); unverified-state + contract-attorney precedence per
  III.6.1 [RC].
- 5c Attorney task library seed migration (15 templates, families,
  targets, deps, flag conditions; agent coordination task swap in
  attorney_controlled); coverage check extended so attorney title
  families satisfy title coverage, and the Q1 gate stays off for these
  workflows [RC].
- 5d Parse fields: `contract_prepared_by_licensee`,
  `contracts_delivered_date`, `attorney_approval_clause` + the three new
  transaction columns persisting them (with III.4 plumbing [RC]); NJ/NY
  timeline rules in `timeline_planner`; undated-with-reason NJ row +
  inline fill.
- 5e FSBO/attorney-direct owner resolution (owner label + existing FSBO
  next-steps surfacing only; NO new customer task UI, per III.6.5 [RC]);
  "confirm representation" inclusion; RESPA helper copy.
- 5f Task Templates page workflow chip/select.
- Tests: per-cluster generation snapshots (IN title deal unchanged; NC
  deal has attorney chain and NO Order Title for the agent; NJ
  licensee-prepared vs FSBO; NY clause vs no clause; unverified state ==
  title workflow); FSBO reassignment matrix.

### Phase 6 - End-to-end UI validation pass (R24)
- Tester scripts (mouse-first, UI-only), one per decision:
  T1 silent-title contract -> forced choice -> right task.
  T2 borderline inspection window -> approve recommendation -> dated task.
  T3 silent window -> blank -> undated task with reason -> fill on Step 3.
  T4 cash deal, waiver language -> no appraisal tasks; elected -> pair.
  T5 cash silent -> prompt -> No -> flip to Yes on workspace -> tasks
     appear, completed preserved.
  T6 business-day deadline in contract -> basis chip + correct date;
     Saturday deadline stays Saturday.
  T7 NC deal -> attorney list, agent gets confirm-and-send; the wizard
     never asks the Buyer/Seller title question and no coverage warning
     appears.
  T8 NJ licensee-prepared -> 3-business-day review from delivery; NJ FSBO
     -> no default deadline.
  T9 NY with/without approval clause.
  T10 unverified state -> standard list.
  T11 a deal created BEFORE this update (no title answer, cash deal with
     no election) -> workspace coverage banners appear and resolve in
     place with the two-button controls, generating the right tasks.
  T12 dual-agency + cash + attorney state combined smoke.
  T13 Fin -> Cash type switch on a deal carrying a manual task -> the
     manual task survives, completed tasks survive, only template tasks
     change (D4 regression, mouse-only).
- Headless-Chrome screenshots of every changed surface; guide + Help
  Center article updates (including replacing `TRANSACTION_SYSTEM_GUIDE.md`
  Section 8's open questions with the recorded decisions);
  `FRONTEND_UI_WORKFLOW_LOGIC.md` Workflow A addendum.

**Migrations summary (sequenced after 20260905090000):** derived condition
semantics; recommendation_floor; has_appraisal + cash appraisal templates;
deadline_day_basis_json; NJ/NY columns (contract_prepared_by_licensee,
contracts_delivered_date, attorney_review_json); state_workflow_profiles +
seed; templates.workflow; attorney task library seed. All are additive or
data-updates; none rewrite existing task instances (live deals migrate
through user-visible recompute/cascade previews only).

---

## Part VI - Testing & verification strategy

- **Unit (backend):** every phase lists its suites above; the planner
  invariants stay pinned (preview == commit; honest-undated; None-condition
  excludes; family dedupe).
- **Extraction benchmark:** the four windows, appraisal election, basis
  reads, NJ/NY fields get labeled fixtures; recognition numbers reported
  before/after prompt changes (R7 is a measurable requirement).
- **Frontend:** vitest for `detectMissingFields` additions, band logic,
  option-card gating; tsc/lint clean.
- **Rendered-output verification:** per standing rule, no UI item is
  "done" from passing tests alone; each surface is rendered and
  screenshotted, and the click paths in T1-T13 are walked in the real app
  against a fresh backend (dev :8001 convention).
- **Non-developer validation:** T1-T13 are written for real-estate
  professionals: every step is a click or a date-pick, no JSON, no
  payloads, expected on-screen text quoted verbatim.

## Part VII - Rollout & compatibility

- Feature flags: `ve_deadline_no_roll_v1` (Phase 4 behavior swap) and
  `ve_attorney_states_v1` (Phase 5 selection changes) default OFF until
  Jake verifies via T6-T10; Phases 0-3 are corrections/additions shipped
  dark by data (conditions only fire when fields exist) and need no flag.
- No stored dates are mutated by deploy. In-flight deals see new math only
  through the existing user-approved recompute/cascade previews.
- Tenant template libraries: migrations only touch global (tenant_id IS
  NULL) seed rows; tenant-cloned templates are listed by a companion
  report query so any tenant copies of task 265/title tasks can be
  reviewed manually rather than force-updated.

## Part VIII - Explicit non-goals (decided, do not revisit)

- No brokerage default for who-orders-title (Jake, Q1).
- No standard/fallback deadline windows of any kind (Jake, Q2).
- No weekend/holiday roll of deadlines (Jake, Q4 final).
- No single attorney-state boolean; no classifying unverified states as
  attorney states (Jake's workbook, Q5).
- No AI-invented tasks in generation; the master list remains the only
  source of the core list (standing product promise).
- No 50 hand-built state lists; two base workflows + flags + per-state
  forms.

## Part IX - Open questions for Jake (small, non-blocking)

1. **Q4 scope check:** "no rolling" is implemented for ALL generated
   deadlines, including internal follow-up tasks (for example a reminder
   task that lands on a Sunday stays on Sunday in My Task Queue). Confirm
   this uniform reading is wanted rather than contract deadlines only.
   (Plan assumes uniform, per "we shouldn't roll anything".)
2. **NJ delivery date:** when the contract set doesn't state the delivery
   date of the fully signed contracts, the review deadline stays undated
   until someone enters it (T8). Confirm that is preferable to counting
   from the last signature date as a fallback. (Plan assumes undated +
   prompt, per the honest-blank principle.)
3. **Attorney-direct customers:** FSBO reassignment ships in Phase 5; a
   dedicated attorney-direct intake (attorney as the primary workspace
   owner from the start) is modeled by the flags but not given its own
   onboarding flow in this plan. Confirm that can follow as its own
   workstream.

---

## Implementation Status (2026-07-03)

Everything below is IMPLEMENTED, tested, and uncommitted (Jan commits; the
six new migrations are written but not DB-applied).

**Migrations (apply in order, after 20260905090000):**
- `20260906090000_derived_condition_semantics.sql` — D1 fix: title/warranty
  conditions rewritten to the derived responsibility fields.
- `20260906091000_confidence_recommendation_floor.sql` — §15.2 band floor.
- `20260906092000_cash_appraisal_election.sql` — D2 fix:
  `transactions.has_appraisal`, task 265 conditioned, cash "Appraisal
  Completed" (271) seeded.
- `20260906093000_deadline_day_basis.sql` — §15.4 per-deal basis map.
- `20260906094000_template_workflow_column.sql` — D3 fix (part 1):
  `task_templates.workflow` + title-company tags on 70/80/290/300/305/310/
  320/350.
- `20260906095000_attorney_task_library.sql` — the 15 workbook attorney
  tasks (legacy ids 900-970, families, flag conditions).
- `20260906096000_attorney_review_columns.sql` — NJ/NY review inputs on
  transactions.

**Shipped per phase (all with passing tests):**
- Phase 0: derived-condition evaluator (`build_derived_condition_values` +
  `evaluate_conditions(derived=…)`), `recommendation_floor` end to end
  (model/repo/API validation/admin slider), band-order enforcement.
- Phase 1: who-orders-title required in the wizard (skipped for attorney
  closings AND the NC/SC/GA/DE cluster), option-card Missing-Info rows,
  server coverage prompts on the workspace plan + resolve-in-place banners,
  `retarget_conditional_tasks` (scoped diff by template_id; replaces the D4
  name-matching switch — manual/AI tasks are never touched).
- Phase 2: explicit `inspection_days`/`inspection_response_days` extraction
  + four-window prompt guidance, recommendation-band UX (empty field + amber
  "AI suggests" chip with one-click accept, scoped to the decision-critical
  fields only), benchmark `QA_DECISION_FIELDS` floor.
- Phase 3: `appraisal_election` parse read → tri-state `has_appraisal`;
  cash-deal wizard gate; Timeline-tab one-click flip (useConfirm; completed
  and manual work preserved); coverage prompt for API-created deals.
- Phase 4: NO-ROLL shipped as the DEFAULT behind `ve_deadline_no_roll_v1`
  (deliberate adjustment from the plan's flag-off rollout: Jake's Q4 answer
  is categorical and confirmed, so the requirement ships on with
  `VE_DEADLINE_NO_ROLL_V1=false` as the escape hatch); per-deal
  `deadline_day_basis_json` read from the contract, effective-basis
  resolution in the dependency engine + timeline planner, plain-language
  business-day basis strings, "lands on Sat/Sun" hint chips (wizard +
  workspace); all roll-era test assertions flipped to pin the new behavior.
- Phase 5: `state_workflow_profiles.py` (the workbook as code — see the
  deliberate adjustment below), `state_rules.py` rewritten (no binary state
  list, no name matching; selection by the deal's resolved workflow ×
  template `workflow` column; contract closing_mode beats geography;
  statutory extras flag-gated so a contract-attorney deal in an unverified
  state gets the generic chain only), attorney library seeded, NJ
  3-business-days-from-delivery clock (licensee-prepared only; undated with
  the honest reason when the delivery date is unknown), NY contract-clause
  deadline, title coverage satisfied by the attorney title family, RESPA
  §2608 helper note on the People tab's Title group.

**Deliberate adjustments from the plan (with reasons):**
1. State profiles live in CODE (`state_workflow_profiles.py`), not the
   `state_workflow_profiles` DB table: the planner is sync and pure, the
   profile data is static verified law, and a DB table without a platform
   editing surface adds async threading for no capability. The table +
   platform editor remain the follow-up when profile editing is wanted.
2. `ve_deadline_no_roll_v1` defaults ON (see Phase 4 above).
3. The frontend mirrors the NC/SC/GA/DE cluster as a small constant in
   `wizardTypes.ts` (documented to stay in sync) so the wizard gate is
   correct without a new API round-trip.

**Remaining (small, non-blocking):**
- Custom-deadline BASIS toggle in RuleFields/AddDeadlineModal and a term-row
  basis override editor (the contract-read basis and template basis work;
  the agent can already override any resolved DATE — only the per-rule
  calendar/business toggle UI is pending).
- FSBO owner-relabel of agent-coordination tasks (III.6.5(a)); the FSBO
  next-steps surface already derives from tasks, and the attorney
  scope-confirmation task ships in the library.
- Task Templates page `workflow` chip (the API already returns the field).
- Headless-Chrome screenshots of the changed surfaces (AW-style visual pass)
  and the T1-T13 walkthroughs against a live dev backend.

*End of plan.*
