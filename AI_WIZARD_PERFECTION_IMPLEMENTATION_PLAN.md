# AI Wizard — Transaction & Task Generation — Perfection Implementation Plan

**Author:** Jan
**Date:** 2026-06-23
**Basis:** [AI_WIZARD_TRANSACTION_TASK_GENERATION_REVIEW.md](AI_WIZARD_TRANSACTION_TASK_GENERATION_REVIEW.md)
(findings C1-C3, H1-H3, M1-M3, L1, and client-test defects T1-T4).
**Goal:** Turn the create-to-tasks path into a system a transaction coordinator
can trust without second-guessing, and that a new brokerage can onboard its own
task list into without losing fidelity. This plan is implementation-ready: every
item names the file, the function, the exact change, the tests, and a
"definition of done" that asserts on rendered output, not just the mechanism.

---

## 0A. Self-review corrections (validated against `velvet-elves-data` docs + code)

I reviewed this plan against the project's own specs and the implementation and
found six places where the original draft was wrong or risky. They are corrected
in the items below; summarized here with evidence so the change is auditable.

1. **T1 (Item 1.4) was based on a false premise — now reframed.** I claimed the
   per-field source document "already exists, just surface it." It does not
   reliably exist: the wizard builds citations from the *packet parse* result
   (`buildEvidenceCitations(result.extracted)` at
   [NewTransactionWizard.tsx:3199](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L3199)),
   whose field sources are `page N: snippet` with **no document id**, and the
   code explicitly documents that resolver source attribution is **not
   evidence-verified** and is deliberately **not used to drive jumps** because
   the packet pipeline can stamp one extraction onto every document
   ([wizardTypes.ts:497-502](../velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L497),
   "Gap F / §15.6"). T1 is therefore a larger backend attribution item, not a
   frontend wiring fix, and the OCR text-locate fallback must be **kept**.
2. **T3 (Item 1.6) must preserve a hard requirement.** The contract-parsing spec
   §404 mandates the missing-document flag
   ([Real_Estate-Contract-Parsing-Agent-Instructions.txt:404](Real_Estate-Contract-Parsing-Agent-Instructions.txt)).
   The fix reduces false positives only; it does not disable the feature.
3. **T4 (Item 1.7) was too loose and mis-scoped.** Raw substring matching can
   mask real conflicts; and the double-check itself is required (spec §3.4 /
   §747 `_disagreements`, third pass §578). The fix is scoped to a dedicated
   `property_address` branch using **token-subset**, leaving `document_type`
   (default branch) and `buyers`/`sellers` (already surname-set) untouched.
4. **C2 (Item 1.1) over-stated wizard exposure.** The wizard's Timeline step
   already gates on a confirmed acceptance date and "never makes up a date"
   (testing guide 16.1), so the real exposure is quick-create / API / preview-
   before-confirm. The engine fix still stands; the repro is corrected.
5. **C1 (Item 1.3) hard gate softened.** Who-orders-title can be genuinely
   absent from a contract, so a hard block fights "honest empty states." The
   coverage-warning safety net + a sensible prefill lead; the hard-required gate
   is the optional, Jake-gated choice.
6. **C3 (Item 1.2) call-site scope made explicit.** The strict resolver is used
   only at the two engine call sites; the lenient `resolve_float_days` is left
   intact for display and to keep its existing test green.

---

## 0. What "perfect" means here (measurable invariants)

These are the acceptance gates. The system is "perfect" for this scope when all
seven hold and have tests proving them.

- **INV1 — No fabricated dates.** A task is either dated from a real input or
  explicitly **undated with a visible reason**. Nothing is ever dated off
  `today()` or a silently-zeroed offset.
- **INV2 — No silent coverage gaps.** Every mandatory workflow that applies to a
  deal (title ordering; inspection-response when `has_inspection`) is either
  generated or surfaced as a named coverage warning on the Review step.
- **INV3 — Preview == Create stays exact.** The dry-run and the commit keep
  producing identical task sets and dates. Every change is applied in the shared
  planner, never in one path only.
- **INV4 — Every citation is clickable to the right page.** Any AI-extracted
  value that shows a "View in Document" lands on the **correct document and
  page**, including in multi-file packets.
- **INV5 — No false alarms.** "Missing document" and "verify this value" only
  fire on a genuine gap or a real semantic conflict, never on a date-format or
  granularity difference, and never against a document that is uploaded.
- **INV6 — Authoring parity.** A tenant can create or import a template that uses
  conditions, `task_family`, `dual_agency_behavior`, predecessors, and
  `day_basis`, and get the same engine behavior as the seed library.
- **INV7 — Green + guarded.** The full backend and frontend suites stay green,
  and each fix ships with a regression test that fails before and passes after.

---

## 1. Guardrails to preserve (do not regress)

1. **Shared planner.** All date/condition logic stays in
   `plan_tasks_for_transaction`; preview and commit both call it. Never patch a
   date in the API layer only.
2. **Deterministic generation.** No LLM decides the task list. AI stays
   extract-and-suggest only.
3. **Honest empty/■undated states.** Prefer an explicit "not set" + reason over a
   plausible guess (this is the whole point of the plan).
4. **AI provider is the one the admin selected.** No provider auto-switching in
   any new code.
5. **Tenant isolation / RLS** unchanged; system templates stay `tenant_id IS
   NULL`, tenant templates stay scoped.

---

## 2. Phases at a glance

| Phase | Theme | Items | Migrations | Needs Jake | Ship before legacy rollout? |
|---|---|---|---|---|---|
| 1 | Trust & correctness | C1, C2, C3, T1, T2, T3, T4 | **none** | only the title-default value | **Yes** |
| 2 | Authoring parity | H1 | none (columns exist) | no | **Yes** |
| 3 | Secondary-flow correctness | H3, M1 | none | no | nice-to-have |
| 4 | State & business-day fidelity | H2, M2, M3 | 1 (state) | **yes** | no |
| 5 | Polish & discoverability | L1, exclusion transparency | none | no | no |

Phase 1 deliberately has **zero migrations**: it is all engine/UI logic, so it
is low-risk and fast to ship. Phases 1 and 2 are the pre-rollout bar for Audri's
legacy-list work.

---

## PHASE 1 — Stop the silent wrong output and the trust-breakers

### Item 1.1 — C2: never date from `today()`

- **Files:** [dependency_engine.py:176](../velvet-elves-backend/app/services/dependency_engine.py#L176),
  [task_generation_service.py:181-232](../velvet-elves-backend/app/services/task_generation_service.py#L181)
- **Change:**
  1. In `calculate_due_dates`, replace
     `anchor_date = transaction.contract_acceptance_date or date.today()` with
     `anchor_date = transaction.contract_acceptance_date` (may be `None`). In the
     first pass, when `abs_anchor is None` **and** `anchor_date is None`, leave
     the task unresolved (do not write into `resolved`).
  2. In `plan_tasks_for_transaction`, generalize the warning block so **any**
     legacy task left with `due is None` gets a reason: if it depends on / anchors
     to contract acceptance and `contract_acceptance_date is None` →
     "No contract acceptance date set; this deadline can't be scheduled yet."; if
     it needs closing and `closing_date is None` → the existing closing message;
     else the generic "depends on a value that isn't set yet."
- **Migration:** none.
- **Tests (backend):** add to `test_dependency_engine.py` /
  `test_task_generation.py`: a transaction with `contract_acceptance_date=None`
  yields **no dated** contract-anchored tasks and a warning on each; previews run
  on two different "today"s are identical.
- **Exposure (corrected):** the wizard's Timeline step already gates on a
  confirmed acceptance date and "never makes up a date" (testing guide 16.1), so
  by the Review step it is set. The real exposure is **quick-create**, the
  **API**, and any preview taken before confirmation. This fix makes the engine
  honor the promise the UI already makes.
- **DoD:** call `POST /preview-tasks` (or quick-create) with
  `contract_acceptance_date` omitted; contract-anchored rows come back undated
  with the reason and are counted in `undated`. Re-running on a different day
  gives identical output. (Clearing it inside the wizard may be unreachable due
  to the Timeline gate — use the API path.) Screenshot the response / Review step.

### Item 1.2 — C3: an unset offset must not collapse to the anchor

- **Files:** [dependency_engine.py:48-85](../velvet-elves-backend/app/services/dependency_engine.py#L48)
  (`resolve_float_days`), `calculate_due_dates`,
  `plan_tasks_for_transaction`.
- **Change:**
  1. Add `resolve_float_days_strict(...) -> float | None` that returns `None`
     (not `0.0`) when a `wizard:<field>` reference points at an unset value, so
     "literal 0" and "unset wizard field" are distinguishable.
  2. In `calculate_due_dates`, when the strict resolver returns `None` for a
     `wizard:` offset, leave the task **unresolved** (undated) rather than using
     0. Keep the literal-`0` path (same-day tasks) working.
  3. In `plan_tasks_for_transaction`, warn on those rows:
     "This deadline needs the <inspection response window / HOA document window /
     insurance window>, which isn't set yet."
  4. **Call-site scope:** use the strict resolver only at the two engine sites
     ([dependency_engine.py:190](../velvet-elves-backend/app/services/dependency_engine.py#L190)
     and [:216](../velvet-elves-backend/app/services/dependency_engine.py#L216));
     leave `resolve_float_days` unchanged for the display derivation at
     [task_generation_service.py:145](../velvet-elves-backend/app/services/task_generation_service.py#L145)
     so its existing test
     ([test_dependency_engine.py:96](../velvet-elves-backend/app/tests/test_dependency_engine.py#L96))
     stays green.
- **Exposure note:** `inspection_response_days` is **not** in the wizard's
  contingency field set
  ([NewTransactionWizard.tsx:1169-1181](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L1169)),
  so the Inspection Response Reminder collapse is a real **wizard-path** misfire,
  not only an API one.
- **Migration:** none. (Tenant-default windows are a separate optional follow-up,
  Item 1.2a, not required for INV1.)
- **Tests:** financed buy with `has_inspection=True` but
  `inspection_response_days=None` → Inspection Response Reminder is undated +
  warned, not dated to the acceptance day. Same for HOA delivery and insurance.
- **DoD:** Preview a default financed-buyer deal without the response window; the
  Inspection Response Reminder shows undated + reason. Screenshot.

#### Item 1.2a (optional, follow-up) — tenant default windows

If Jake wants standard windows pre-filled, add a small `tenant_settings`-backed
map (`inspection_days`, `inspection_response_days`, `hoa_doc_days`,
`insurance_commitment_days`) applied **in the wizard as a prefill the user sees
and can change**, never as a hidden server default. This keeps INV1 honest (the
value is visible, not silent). Defer until the window numbers are confirmed.

### Item 1.3 — C1: no deal without a title task

- **Files:** [schemas/transaction.py:58](../velvet-elves-backend/app/schemas/transaction.py#L58),
  [NewTransactionWizard.tsx:1169-1181](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L1169),
  `plan_tasks_for_transaction`, `preview_tasks` summary
  ([transactions.py:1761-1815](../velvet-elves-backend/app/api/v1/transactions.py#L1761)).
- **Change (corrected — lead with the safety net, not a hard block):**
  1. **Backend safety net (primary):** add a `coverage_warnings` list to the
     preview summary. If no task in family `order_title` / `confirm_title_order`
     survived, add "No title task was generated — confirm who orders title."
     Render it on the Review step near the undated banner. This also requires
     adding `coverage_warnings` to the frontend `PreviewTasksResponse.summary`
     type ([useWizardApi.ts](../velvet-elves-frontend/src/hooks/useWizardApi.ts))
     and rendering it in `ReviewTasksStep`.
  2. **Prefill (not a hard block):** default the `title_ordered_by` select to the
     tenant's common value so the order-vs-confirm decision is normally made.
     Because the answer can be genuinely absent from a contract, do **not** hard-
     block creation by default (that would fight "honest empty states"); the
     coverage warning covers the unset case.
  3. **Optional hard gate (Jake's call):** if Jake wants it required, gate
     "Approve & Create" on a non-null `title_ordered_by`. Listed as an Open
     Decision, not assumed.
- **Migration:** none.
- **Tests:** transaction with `title_ordered_by=None` → preview returns a
  `coverage_warnings` entry for title; with `"us"` → Order Title present; with
  `"them"` → Confirm Title present.
- **DoD:** force the unset case via API → preview shows the coverage warning, and
  the Review step renders it. Screenshot.

### Item 1.4 — T1: "View in Document" must work in multi-file packets (highest value)

- **Files:**
  [NewTransactionWizard.tsx:4015-4058](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L4015)
  (`citedFields`, `selectEvidence`, `singleDocId`),
  [wizardTypes.ts:268-286](../velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L268)
  (`WizardCitation`, `CitedField`),
  [WizardEvidenceViewer.tsx:271-301](../velvet-elves-frontend/src/components/wizard/WizardEvidenceViewer.tsx#L271),
  and the parse-response → `aiCitations` mapping (the
  `set_ai_citations` dispatch at
  [:1647](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L1647)).
- **Root cause recap (corrected):** the wizard builds citations from the
  **packet parse** result (`buildEvidenceCitations(result.extracted)` at
  [NewTransactionWizard.tsx:3199](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L3199)),
  whose field `source` is `page N: snippet` with **no document id**
  ([wizardTypes.ts:465-481](../velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L465)).
  Per-field document attribution is a **known, unsolved gap**: the resolver's
  `source_document_id` is explicitly **not evidence-verified** and deliberately
  not used to drive jumps, because the packet pipeline can stamp one extraction
  onto every document
  ([wizardTypes.ts:497-502](../velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L497),
  "Gap F / §15.6"). So "just surface the existing document id" is **not safe** —
  it could point at the wrong file.
- **Correct fix (two tracks):**
  - **Track A — interim mitigation (small, ship first):** make the existing
    cross-document locate succeed for formatted values. The verbatim `snippet`
    is the reliable key (the AI quotes it from the page), so prefer
    snippet-first matching over the formatted `value` (a date like "06/21/2026"
    rarely OCR-matches), and when the snippet matches OCR text in exactly **one**
    document, jump to that document + the cited page. This clears the tester's
    "won't show the page" without claiming attribution we don't have. Touches the
    locate effect at
    [WizardEvidenceViewer.tsx:309-353](../velvet-elves-frontend/src/components/wizard/WizardEvidenceViewer.tsx#L309).
  - **Track B — real fix (larger, the actual "Gap F"):** make the packet
    extraction produce **true per-field `(document_id, page)`** attribution,
    verified against that document's OCR geometry, then thread a trustworthy
    `documentId` into `WizardCitation` / `CitedField` and `selectEvidence`. Only
    then can the viewer switch documents deterministically. This is backend
    extraction work, scoped as its own item.
  - **Do not** remove the OCR text-locate fallback (the prior draft's step 5):
    it is intentional precisely because attribution is unverified.
- **Migration:** none.
- **Tests:** Track A — a multi-doc OCR fixture where a date value differs in
  format from the page text; assert the snippet-first locate lands on the right
  document + page. Track B — extraction unit asserting each critical field
  carries the document_id it was read from.
- **DoD (walk the click path):** upload a 2+ file packet, open Review, click
  "View in Document" on the acceptance date and on "Who orders title" — Track A
  must land on the correct page via snippet locate; Track B makes the document
  switch deterministic. Screenshot the jump. This is the tester's top complaint.

### Item 1.5 — T2: stop saying "couldn't find" next to a found value

- **Files:** the field-source rendering
  ([NewTransactionWizard.tsx:4090-4101](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L4090),
  `fieldSourceProps`) and the missing-info / verify copy; threshold at
  [contract_resolution.py:28](../velvet-elves-backend/app/services/contract_resolution.py#L28)
  and [:107-116](../velvet-elves-backend/app/services/contract_resolution.py#L107).
- **Change:** branch the copy on **citation presence**, not on `needs_review`
  alone. If `citedByKey[key]` exists, the field reads "Found on page N — please
  confirm" (verify state), never "couldn't find." Reserve "couldn't find / please
  enter" for fields with no candidate at all.
- **Migration:** none.
- **Tests:** a field with confidence 0.87 + citation renders the confirm copy,
  not the not-found copy.
- **DoD:** the "Who orders title" case shows "Found on page 1 — confirm" with a
  working View-in-Document (after 1.4), not a contradiction. Screenshot.

### Item 1.6 — T3: kill the false "referenced documents not uploaded"

- **File:** [contract_resolution.py:919-991](../velvet-elves-backend/app/services/contract_resolution.py#L919)
  (`_detect_missing_referenced_documents`, `_missing_reference_reason`).
- **Requirement to preserve:** spec §404 mandates this flag ("If a document
  references another document that is not included in the upload, the agent must
  create a missing-document flag" —
  [Real_Estate-Contract-Parsing-Agent-Instructions.txt:404](Real_Estate-Contract-Parsing-Agent-Instructions.txt)).
  The fix only removes **false** positives; the flag stays for genuinely-absent
  references.
- **Change:** before emitting a flag,
  1. **Family-presence guard:** if any inventory document is of `ref_family`,
     do **not** flag on a date-only mismatch; only flag when a specific
     `sequence` is provably missing (e.g. a counter #2 with no #1).
  2. **No self-reference:** skip when the referrer's own family equals
     `ref_family` and it is the only member of that family (the tester's case:
     "purchase_agreement references purchase_agreement").
  3. **Match by the right date, or by presence — not the controlling date.** The
     cited "dated" value is the referenced document's *own* date (offer date),
     not the controlling `document_effective_at` (acceptance date), so stop using
     effective-date prefix equality as the sole presence test; fall back to
     family presence when no specific sequence gap exists.
- **Migration:** none.
- **Tests:** PA whose body cites "purchase_agreement dated 2026-06-20" while its
  effective date is 2026-06-21 → **no** flag; a counter #2 with no #1 → flag
  stays.
- **DoD:** re-run the tester's packet; the "5 referenced documents not uploaded"
  panel is empty (or shows only a true gap). Screenshot.

### Item 1.7 — T4: double-check must not flag formatting differences

- **File:** [document_packet_parsing.py:499-549](../velvet-elves-backend/app/services/document_packet_parsing.py#L499)
  (`_norm_text`, `_values_agree`).
- **Change (corrected scope):** add a **dedicated `property_address` branch** to
  `_values_agree` using **token-subset**: tokenize both normalized addresses and
  agree when every token of the shorter set appears in the longer (so "603
  yandes st" agrees with "603 yandes st franklin in 46131"). Do **not** change
  the default `_norm_text` branch (it also serves `document_type`, where subset
  matching would be wrong), and do **not** touch `buyers`/`sellers` (already
  surname-set), `purchase_price` (numeric tolerance), or the date branch. The
  double-check stays required (spec §3.4 / third pass §578); this only stops
  granularity differences from counting as conflicts.
- **Migration:** none.
- **Tests:** extend `test_document_packet_parsing.py`: short vs full address →
  `agree=True`; a different street number ("603 …" vs "605 …") → `agree=False`;
  confirm `document_type` "counter" vs "counter offer" behavior is unchanged.
- **DoD:** re-run the packet; the double-check no longer asks to verify the
  address that was already correct. Screenshot the agreed state.

**Phase 1 exit criteria:** INV1, INV2, INV3, INV5 hold with tests; INV4 is met
for the common case via Item 1.4 **Track A** (snippet locate), with full
determinism deferred to **Track B**; backend and frontend suites green; the
tester's four reported symptoms reproduced-then-fixed with screenshots.

---

## PHASE 2 — Authoring parity so a brokerage's own list onboards cleanly (H1)

This is the work that de-risks Audri's legacy-list implementation. No migration:
the columns already exist from `20260605_task_engine_fix.sql`.

### Item 2.1 — Create-template parity with update

- **Files:** [schemas/task_template.py:11-27](../velvet-elves-backend/app/schemas/task_template.py#L11)
  (`TaskTemplateCreateRequest`),
  [task_template_repository.py:121-185](../velvet-elves-backend/app/repositories/task_template_repository.py#L121)
  (`create`),
  [task_templates.py:88-139](../velvet-elves-backend/app/api/v1/task_templates.py#L88).
- **Change:** add `task_family`, `dual_agency_behavior`, `dep_task_ids`,
  `day_basis`, and `conditions_json` to the create schema and to `repo.create`
  (mirror what `update` + the generic `repo.update` already pass through). The
  create endpoint forwards them.
- **Tests:** create a template with `dual_agency_behavior="consolidated"` and a
  `dep_task_ids` list → round-trips and participates in
  `filter_both_representation` / `calculate_due_dates`.
- **DoD:** create a tenant template via API with a condition + family + dual-
  agency role; generate a deal that exercises it; confirm consolidation/date
  behavior matches the seed library.

### Item 2.2 — Structured CSV importer + library linter

- **File:** [task_templates.py:323-455](../velvet-elves-backend/app/api/v1/task_templates.py#L323)
  (`import_templates_csv`).
- **Change:**
  1. Read **explicit columns** when present (`Condition`, `Task Family`,
     `Dual Agency`, `Day Basis`, `Predecessors`, `Automation`), and only fall
     back to the English-note inference as a *suggestion* the admin confirms.
  2. Stop hardcoding `automation_level="Manual"`; honor the column.
  3. Parse `title_ordered_by` / `warranty_ordered_by` conditions, not just
     inspection/HOA/warranty booleans.
  4. Add a **linter pass** returning warnings: orphan `dep_task_id`
     (no matching `legacy_task_id`), a family with two `consolidated` rows,
     conditions referencing unknown fields, unparseable `float_days`.
- **Tests:** import a `REWORKING_TASK_DB.csv`-shaped file with explicit columns →
  families/dual-agency/predecessors persist; a file with an orphan dependency →
  linter warning, row still imported or skipped per policy.
- **DoD:** import the brokerage's own list; generate the 6 use cases; the result
  matches the seed library's fidelity (consolidation, multi-predecessor, dates).
  This is the literal "bring your task list" promise.

**Phase 2 exit criteria:** INV6 holds; an imported/authored tenant library
produces the same engine behavior as the seed on the §7 use-case fixture matrix.

---

## PHASE 3 — Secondary-flow correctness

### Item 3.1 — H3: switch use case by `template_id`, then re-date survivors

- **File:** [task_generation_service.py:468-558](../velvet-elves-backend/app/services/task_generation_service.py#L468).
- **Change:** match preserve/remove on `template_id`, not `task.name`. After the
  switch, run the `recompute_task_dates` logic over surviving, non-completed
  template tasks so the whole list is internally consistent.
- **Tests:** Buy-Fin → Both-Fin keeps completed tasks, swaps the right rows, and
  re-dates survivors; no duplicate/again-named mis-preserve.

### Item 3.2 — M1: recompute user-added relative deadlines

- **File:** [task_generation_service.py:561-629](../velvet-elves-backend/app/services/task_generation_service.py#L561)
  (`recompute_task_dates`).
- **Change:** also recompute any task whose `metadata_json.basis` is set, using
  `resolve_added_task_basis` against the new dates (not just `template_id` rows).
- **Tests:** a user "10 days before closing" deadline moves when closing moves.

**Phase 3 exit criteria:** addenda and use-case changes leave a fully consistent,
correctly-dated list (extends INV1/INV3 to the edit flows).

---

## PHASE 4 — State & business-day fidelity (needs Jake)

### Item 4.1 — H2: make state rules real (or scope them honestly)

- **File:** [state_rules.py](../velvet-elves-backend/app/services/state_rules.py).
- **Change:** drive state behavior off **structured data**, not name substrings:
  add a `closing_entity` (`title` | `attorney`) and `required_states` /
  `excluded_states` capability on templates, and seed a small attorney-state task
  set (attorney review period, attorney-ordered title, attorney closing). Replace
  the `"attorney" in name` matching with the structured fields.
- **Migration:** **1 new migration** `20260830090000_state_rules.sql` (next free
  timestamp after `20260829090000`): add the columns + seed attorney tasks.
- **Interim if deferred:** document the limitation in the wizard and the review
  so we are not advertising state-awareness we do not deliver.
- **Needs Jake:** which states/workflows to model first.

### Item 4.2 — M2/M3: business-day windows and cash-appraisal policy

- **M2:** audit which legacy windows are written in *business* days and set
  `day_basis='business'` on those rows (data fix, same migration as 4.1 or its
  own).
- **M3:** decide whether cash deals get both Appraisal Ordered + Completed or
  neither, and align seed rows 265/270.
- **Needs Jake:** both are policy calls about how his contracts read.

---

## PHASE 5 — Polish & discoverability

### Item 5.1 — L1: idempotent `generate` + regenerate affordance

- **File:** [transactions.py:1280-1366](../velvet-elves-backend/app/api/v1/transactions.py#L1280).
- **Change:** accept an optional `commit_id` (like the bulk-requirements
  endpoint) so a retried commit after a partial failure is safe; offer an
  explicit "regenerate" path instead of a hard 409.

### Item 5.2 — Exclusion transparency

- When a whole family is excluded because a question was unanswered (title, HOA,
  warranty), show a small "X tasks were not added because these are unanswered:
  …" note on the Review step. Reinforces INV2 and prevents C1-style surprises.

---

## 6. Verification protocol (how we prove each item, per project norms)

For every item, "done" means **rendered output verified**, not just a passing
unit test (this has bitten the team before):

1. **Backend:** `pytest` green (keep the current count; add the new regression
   tests). For engine items, assert on the actual planned dates/warnings, not
   just status codes.
2. **Frontend:** `tsc` + `eslint` clean; `vitest` for the citation/double-check
   units.
3. **Render + screenshot** the affected surface (Review Timeline, Review Tasks,
   the evidence viewer) and **walk the click path** (e.g. actually click "View in
   Document" and confirm the page jump) before marking done.
4. **Tester-facing repro** for each fix, written so a non-developer tester can
   confirm it (mouse-first, minimal typing), to fold back into the testing guide.

---

## 7. The two cross-cutting test assets to build once

- **Use-case fixture matrix:** the 6 use cases × {HOA on/off, inspection on/off,
  title us/them, warranty us/them/none, attorney/title closing}, asserting the
  exact expected task set and that **no** task is silently mis-dated. This is the
  single best guard for INV1/INV2/INV6 and for the legacy-list rollout.
- **Missing-input suite:** omit contract date, closing date, each offset, and
  `title_ordered_by`; assert a visible warning every time and zero fabricated
  dates.

---

## 8. Recommended defaults to build now (then confirm with Jake)

Approach: build the honest, defensible default for each item, then show Jake
"the system works like this — confirm or rework." The unifying principle that
makes this safe to build before his answer: **prefer the value the contract
states (AI-extracted); when the contract is silent, warn rather than guess; and
keep Indiana / calendar-days / title-company as the working baseline** (Indiana
is the client's primary market and is already modeled —
[state_rules.py:38-45](../velvet-elves-backend/app/services/state_rules.py#L38)).

1. **Title default (Item 1.3).** Build: **prefer the AI-extracted
   `title_ordered_by`** (the contract usually states it — the tester's packet
   extracted "Buyer"); when absent, **leave it blank and show the coverage
   warning** rather than guessing a side. Do **not** hard-code a side default —
   guessing wrong makes the TC either order title the other side is ordering, or
   only "confirm" a title nobody ordered; both are real errors. Optional
   per-tenant default for the silent case, off until set.
   *Ask Jake:* "When the contract is silent on who orders title, do you want a
   brokerage default (which side), or keep the warning?"
2. **Default windows (Item 1.2a).** Build: **prefer the AI-extracted window**;
   when absent the field stays empty + the C3 warning fires (no silent zero).
   Ship 1.2a prefills as **visible, editable suggestions only**, starting values
   inspection 10 / response 5 / HOA docs 10 / insurance 10 (calendar days).
   *Ask Jake:* confirm the numbers for his market.
3. **Cash appraisal (M3).** Build: **cash deals get no appraisal tasks by
   default** (drop the cash scope on row 265; appraisal stays financed-only and
   consistent with 270). If some cash buyers appraise, add a one-click "appraisal
   on this deal" toggle instead of always generating it.
   *Ask Jake:* "Do your cash deals usually involve an appraisal?"
4. **Business-day rows (M2).** Build: **change nothing in the data yet** — keep
   every row on calendar days so no deadline math shifts silently. The engine
   already supports business days; flip rows only once the contract language is
   confirmed. *Ask Jake:* "Which deadlines does your contract write in *business*
   days?" (likely: inspection response, financing / clear-to-close).
5. **State priorities (H2).** Build: the **structured `closing_entity` / state
   scaffolding** + keep Indiana (title-company) as the correct baseline; **do not
   seed attorney-state tasks yet**, and scope the wizard copy honestly
   ("optimized for title-company states"). *Ask Jake:* "Which states are your
   next brokerages in — any attorney-closing states to model first?"

This turns five blockers into five confirmations. Items 1.1, 1.2 (warn path),
1.4-1.7, and 2.x still need none of them.

---

## 9. Sequencing relative to Audri's legacy-list rollout

- **Before rollout:** Phase 1 (trust + correctness; the tester's four defects)
  and Phase 2 (authoring parity). Without Phase 2, a brokerage's imported list is
  a degraded engine; without Phase 1, the wizard hands TCs confident-but-wrong
  output. Both must land first.
- **During/after rollout:** Phase 3 (edit-flow correctness), then Phase 4 (state)
  once Jake prioritizes states, then Phase 5 polish.

**Recommended first commit (corrected):** Item 1.6 (false missing-docs) + Item
1.7 (double-check) + Item 1.4 **Track A** (snippet-first locate) — all pure
correctness with no attribution dependency and no Jake input, and they clear the
tester's filed complaints. Then 1.1-1.3 (the engine Critical three). Item 1.4
**Track B** (true per-field document attribution, the real "Gap F") is a larger
backend item scheduled after, since it is the only way to make document switching
deterministic. Then Phase 2.
