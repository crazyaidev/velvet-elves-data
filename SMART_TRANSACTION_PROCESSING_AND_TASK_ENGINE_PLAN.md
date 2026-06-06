# Smart Transaction Processing & Task Generation Engine Plan

**Status:** Plan only (no source code changed)
**Author:** Jan Froben (development)
**Date:** 2026-06-05
**Audience:** Jake (product owner) + development
**Scope:** Repair and upgrade the transaction task generation engine, add a wizard task-review UI, and define a roadmap to match and surpass ListedKit (https://www.listedkit.com/).

---

## 0. Executive Summary

Jake's three observations are all correct, and I have traced each one to a specific, verifiable cause in the code and seed data:

1. **"None of the generated tasks include a date."** The dependency engine is built to anchor every task to one of two pseudo-tasks: `Contract Acceptance Date` (legacy id `5`) and `Closing Date` (legacy id `1000`). Those two anchors are seeded with **empty use-case lists**, so the generation query never loads them, so the engine never seeds the two anchor dates, so **every** dependent date fails to resolve and comes back `null`. The engine's own unit tests pass only because they hand the anchor rows directly to the calculator, which production never does.

2. **"Many duplicate tasks have been created."** The de-duplication logic (`filter_both_representation`) is a no-op for single-side transactions, never implements the `single_instance` rule, and inverts the `replace_with` rule. Combined with seed rows whose use-case lists overlap (the "Both" variant of a task also lists every single-side use case), a plain Buy-Fin transaction receives 2x or 3x copies of HOA, utility, title-delivery, closing-gift, inspection, and thank-you tasks.

3. **"I am not confident in the accuracy of the generated tasks."** The conditional logic that should gate tasks (only create HOA tasks when there is an HOA, inspection tasks when there is an inspection, title-order tasks when we order title, financing tasks when financed) is **never enforced**: the conditions were imported as descriptive English text instead of executable predicates, so `evaluate_conditions` silently passes everything.

None of these are deep architectural problems. The engine design is sound and the wizard already collects every field the engine needs. The failures are in **the data that feeds the engine** (anchors, conditions, and representation overlap) plus **three logic bugs in one file**. They are fixable in a focused P0 effort.

On top of the repair, Jake asked for two forward-looking deliverables:

- **A wizard task-review UI**, so the user can examine and adjust every generated task before the transaction is committed.
- **A plan to surpass ListedKit.** ListedKit's entire value proposition is "upload a contract, get a correct, dated, deadline-driven task list, and never miss a date." That is exactly the surface that is broken in Velvet Elves today. Once the engine is repaired, Velvet Elves already has structural advantages ListedKit lacks (a deterministic firm playbook, role-targeted tasks, attorney/state rules, a structured vendor reply loop, multi-tenant white-label, confidence-scored extraction). This document lays out how to close the remaining gaps (business-day deadline math, addendum-driven recalculation, calendar-per-deadline sync, inbox-to-deal matching) and turn the repaired engine into a category-leading capability.

---

## 1. How Task Generation Works Today (as built)

### 1.1 The end-to-end path

1. The New Transaction wizard ([velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx](velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx)) runs six steps: `upload -> parsing -> address -> purchase -> missing -> confirm` (see `WIZARD_STEPS` in [wizardTypes.ts](velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L30)).
2. On "Accept & Create", `submit()` (line ~2760) creates the transaction (`useCreateTransaction`), persists parties, then calls `tasksMut.mutateAsync(tx.id)` (line ~2987), which POSTs to `/api/v1/transactions/{id}/tasks/generate`.
3. That endpoint ([transactions.py:1120](velvet-elves-backend/app/api/v1/transactions.py#L1120)) calls `generate_tasks_for_transaction` ([task_generation_service.py:66](velvet-elves-backend/app/services/task_generation_service.py#L66)).
4. The service: loads templates for the use case, filters by conditions, filters by both-representation behavior, applies state rules, calculates due dates, then writes `Task` rows.
5. The endpoint returns only `{ tasks_generated: <count>, transaction_id }`. The wizard immediately navigates away to the Active Transactions list. **The user never sees the tasks during creation.**

### 1.2 The template library (the firm playbook)

Templates are seeded from [velvet-elves-data/REWORKING_TASK_DB.csv](velvet-elves-data/REWORKING_TASK_DB.csv) into the `task_templates` table via [202603111730_seed_task_templates.sql](velvet-elves-backend/supabase/migrations/202603111730_seed_task_templates.sql). Each template carries: `legacy_task_id`, `use_cases[]`, `target`, `cc_targets[]`, `milestone_label`, `dep_rel` (FS/SS), `dep_task_id`, `float_days`, `automation_level`, `conditions_json`, `both_rep_behavior`, `replace_with_id`, `sort_order`.

Two rows are **anchors**, not real tasks:
- `legacy_task_id = 5` -> `Contract Acceptance Date` (seed line 36), `use_cases = []`.
- `legacy_task_id = 1000` -> `Closing Date` (seed line 131), `use_cases = []`, `float_days = 'wizard:closing_date'`.

Almost every real task depends on one of these two anchors. Tasks near the front of the deal depend on `5` with small positive floats; tasks near closing depend on `1000` (SS) with negative floats (for example `Schedule Closing` is `SS`, dep `1000`, float `-14`, meaning 14 days before closing).

---

## 2. Root-Cause Findings (verified against code, seed, and tests)

### Finding A (Critical): Every task date resolves to null

**Where:** `calculate_due_dates` in [dependency_engine.py:96](velvet-elves-backend/app/services/dependency_engine.py#L96).

**Mechanism:**
- The function builds its lookup and `resolved` map only from the templates passed in (lines 113-119).
- The first pass resolves only templates with `dep_task_id is None` (line 128). In production, virtually no generated task has a null dependency; every chain roots at anchor `5` or `1000`, either directly or through an intermediate task (for example `Request HOA Docs` 90 -> `Deliver HOA Docs` 110 -> anchor 5; `Deliver Utility Info` 150 -> `Request Utility Info` 130 -> anchor 1000).
- The iterative pass resolves a task only if `resolved.get(tmpl.dep_task_id)` is already set (line 149). Since anchors `5` and `1000` are **never in the template set** (they have empty `use_cases`, so `list_by_use_case` in [task_generation_service.py:46](velvet-elves-backend/app/services/task_generation_service.py#L46) never returns them), `resolved[5]` and `resolved[1000]` are never seeded, and because the whole graph roots at those two ids, no chain can ever start resolving.
- Result: nothing resolves, `resolved` stays effectively empty, and back in the service the due date is `None` for every task ([task_generation_service.py:144-148](velvet-elves-backend/app/services/task_generation_service.py#L144)). Conversely, seeding just those two ids unblocks the entire dependency graph in one pass, which is why the Section 3.1 fix is small.

**Why the tests do not catch it:** `test_dependency_engine.py` builds fixtures that pass the anchor row (e.g. `legacy_task_id=5, dep_task_id=None, float_days="0"`) **into** `calculate_due_dates` (for example [test lines 206-210, 222-232](velvet-elves-backend/app/tests/test_dependency_engine.py#L204)). That seeds `resolved[5]` inside the test, so the test passes. Production filters the anchors out by use case before the calculator ever runs. The unit test and production therefore exercise different inputs. This is the single most important bug.

**Consequence:** No due dates means no deadline tracking, no overdue detection, no day-before reminders, no calendar value. This breaks the product's core promise.

### Finding B (Critical): Duplicate tasks for both single-side and "Both" transactions

**Where:** `filter_both_representation` in [dependency_engine.py:225](velvet-elves-backend/app/services/dependency_engine.py#L225).

Three separate defects combine:

1. **No-op for single-side.** Lines 241-243: `if not is_both: return templates`. For Buy-Fin / Sell-Fin / Buy-Cash / Sell-Cash, no de-duplication happens at all.

2. **Dual-agency rows leak into single-side deals.** In this playbook "Both" means **dual agency** (the same brokerage represents buyer and seller), not "buyer and seller as two parties." The dual-agency consolidated rows were seeded with the **full four-use-case list**, so a single-rep deal also loads them. The leak takes two forms, both verified against the seed targets:
   - **True same-target duplicates** (the leaked row has the same `target` as the correct row): `Inspection Scheduled` 210 + 215 (both target Buyer), `Deliver HOA Docs` 110 + 115 (both Buyer), `Deliver Utility Info` 150 + 155 (both Buyer), `Closing Gift` 370 + 375 (both Agent), and `Inspection Negotiated` 250 + 255 (both Agent). For a Buy-Fin deal each of these appears **twice**.
   - **Inapplicable extras** (the leaked dual-agency row has a different target and should not exist on a single-rep deal): `Request HOA Docs` 90 (Co-op Agent) + 95 (Seller), `Request Utility Info` 130 (Co-op Agent) + 135 (Seller), `Deliver Title` 300 (Buyer) + 305 (Buyer & Seller). For `Internal Thank You`, 500 (Agent) and 510 (Co-op Agent) are **both legitimate** on a single-rep deal (thank our agent and the co-op agent); it is only the dual-agency consolidated 505 (target "Both") that leaks in erroneously. So this surface is over-generated by one task, not tripled.
   - Separately, `Inspection Negotiated` 250 carries all four use cases while 255 (Buy) and 257 (Sell) duplicate it per side: this is a plain redundant-row seed error, not a dual-agency pattern, and is cleaned up in the re-seed.

3. **`single_instance` is never implemented and `replace_with` is inverted (Both deals).** For "Both" transactions the function only handles `skip` and `replace_with`, and the `replace_with` branch (lines 254-266) adds the **replacement row's own id** to the skip set, then skips it. Net effect for a Both deal: the side-specific rows are dropped (correct) **and** the intended consolidated row is also dropped (wrong), so whole task families (HOA request/deliver, utility, title delivery, closing gift, internal thank-you) **disappear**; meanwhile families encoded as `single_instance` rather than `replace_with` (for example `Inspection Scheduled` 210/215/220) are not de-duplicated at all and appear **three times**.

**Consequence:** single-side deals over-generate roughly nine task families (a mix of exact duplicates and inapplicable dual-agency tasks); Both deals get a mix of triples and silently-missing families. Either way the user sees a noisy, untrustworthy list, matching Jake's "many duplicate tasks" report. Note that the per-template id de-duplication in `_list_templates_for_generation` ([task_generation_service.py:52-59](velvet-elves-backend/app/services/task_generation_service.py#L52)) already collapses a single template that matches via two use-case lookups, so siblingless tasks are safe; the defect is specifically in the family/representation handling.

### Finding C (Critical): Conditional tasks are never gated

**Where:** `evaluate_conditions` in [dependency_engine.py:181](velvet-elves-backend/app/services/dependency_engine.py#L181) versus the seeded `conditions_json`.

The function expects each condition to be a predicate like `{"field": "has_hoa", "value": true}` and is provably correct (see `TestEvaluateConditions`, [test lines 132-197](velvet-elves-backend/app/tests/test_dependency_engine.py#L132)). But the seed stored the contract's English notes instead, for example:
```json
[{"source": "dev_notes", "text": "If \"no\", this task does not populate."}]
```
Since `cond.get("field")` is `None`, the loop hits `continue` (lines 200-202) for every entry and returns `True`. **All conditions pass unconditionally.**

**Consequence:** HOA tasks are created with no HOA; inspection tasks with no inspection; "Order Title" regardless of who orders title; home-warranty tasks regardless of the wizard answers. The persisted `Transaction` model exposes `has_hoa`, `has_inspection`, `title_ordered_by`, `has_home_warranty`, `warranty_ordered_by`, `hoa_doc_days`, `inspection_days`, `inspection_response_days`, `insurance_commitment_days` ([transaction.py:50-73](velvet-elves-backend/app/models/transaction.py#L50)), but none of them actually influence which tasks appear. **Important nuance verified against the model:** financing is represented by `financing_type` (default `"Financed"`) and by the use case (`Buy-Fin` vs `Buy-Cash`), **not** by a `has_mortgage` field. `has_mortgage` exists only in the wizard, not on the `Transaction` dataclass, so any condition predicate must reference a real `Transaction` attribute or the engine's `getattr(...None)` path will silently exclude the task (lines 204-207). This directly shapes the corrected condition mapping in Section 3.3.

### Finding D (High): Multi-dependency and text floats are silently dropped

The CSV expresses some maturities as multi-dependency or free text:
- `Inspection Completed` (230) depends on "210, 215, 220"; the seed reduced it to a single `dep_task_id = 210`.
- `Title Work Completed` (290) depends on "70, 80"; reduced to `70`.
- `230`'s float is the sentence "Task matures on date entered upon task completion of 210, 215 or 220"; `resolve_float_days` cannot parse it and returns 0.
- `Inspection Negotiated` (250/255/257) have a null float.

The data model (`dep_task_id: int | None`, [task_template.py:30](velvet-elves-backend/app/models/task_template.py#L30)) cannot represent multiple predecessors, and the task instance only stores a single dependency list anyway. Maturities that should follow the latest of several predecessors are therefore wrong or absent.

### Finding E (Medium): State rules are fragile string heuristics

`apply_state_rules` ([state_rules.py:56](velvet-elves-backend/app/services/state_rules.py#L56)) decides attorney-vs-title behavior by substring-matching task **names** ("attorney", "title company", "closing", "schedule"). This is brittle and not represented in the template data. For the client's primary Indiana market the playbook has no attorney rows, so this is low impact today, but it will misfire as soon as attorney-state templates are added.

### Finding F (High, product gap): No task review during creation; generation is fire-and-forget

The generate endpoint returns only a count and the wizard navigates away ([NewTransactionWizard.tsx:2987-3001](velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L2987)). There is no preview, no per-task review, no ability to edit a due date, remove an irrelevant task, or see **why** each task was created before it is committed. If generation throws, the wizard swallows the error and proceeds anyway (the `catch` around `tasksMut`). This is the gap Jake wants closed, and it is also a strong opportunity (see Section 4).

### 2.1 Summary table

| # | Severity | Symptom Jake reported | Root cause | Primary file |
|---|----------|----------------------|-----------|--------------|
| A | Critical | No dates on any task | Anchor pseudo-tasks (5, 1000) filtered out by use case, so the dependency calculator never seeds anchor dates | dependency_engine.py / seed |
| B | Critical | Many duplicate tasks | `filter_both_representation` no-ops for single-side, never implements `single_instance`, inverts `replace_with`; seed use-case lists overlap | dependency_engine.py / seed |
| C | Critical | Tasks not accurate | Conditions seeded as English text, not predicates, so `evaluate_conditions` passes everything | seed / dependency_engine.py |
| D | High | Wrong maturities | Multi-dependency and text floats dropped on import | task_template model / seed |
| E | Medium | Future attorney-state risk | Name-substring heuristics instead of data-driven rules | state_rules.py |
| F | High | Cannot review tasks during creation | No preview endpoint; generation runs post-commit and returns only a count | transactions.py / wizard |

---

## 3. Remediation Plan for the Engine (P0)

Goal: a transaction created from the wizard produces a **correct, dated, de-duplicated, condition-accurate** task list, deterministically, with no AI creativity at generation time (consistent with Milestone 2.2's intent).

### 3.1 Fix dates: seed the anchors inside the calculator

Make `calculate_due_dates` anchor-aware so it does not depend on the anchor rows being present in the template set:

- Before the resolution loop, seed:
  - `resolved[5] = transaction.contract_acceptance_date`
  - `resolved[1000] = transaction.closing_date`
- If `contract_acceptance_date` is missing, fall back to today (already the behavior) but surface a flag so the review UI can warn.
- If `closing_date` is missing, leave closing-anchored tasks undated and flag them rather than silently producing `null`.
- Keep the existing FS/SS and float logic, which is otherwise correct.

Two implementation options:
1. **Minimal (recommended, lowest risk):** seed `resolved[5]` and `resolved[1000]` inside `calculate_due_dates` from the transaction's two anchor dates before the resolution loop. No schema change, no new emitted rows, and the anchors stay out of the generated task list as today.
2. **Data-driven (generalization):** add an `anchor_field` column to `task_templates` (for example `anchor_field = 'contract_acceptance_date'` on row 5, `'closing_date'` on row 1000) plus an `emits_task = false` flag on anchor rows; load the anchor rows explicitly in `_list_templates_for_generation` (they have empty `use_cases`, so they need an explicit "always load anchors" fetch), resolve their dates from the transaction, and **exclude them from the emitted task list**. This generalizes to future anchors (for example a possession date) without code changes, matching the "rule builder without code" goal in Milestone 2.2. The critical detail, missed in my first draft: anchors must be **resolved for date math but never emitted as tasks**, or the user would see "Contract Acceptance Date" and "Closing Date" as actionable tasks.

Either way, add a regression test that runs the **full production path** (load by use case, then calculate), not just the calculator in isolation, so Finding A cannot recur.

### 3.2 Fix duplicates: model representation as a first-class concept

Replace the `skip` / `single_instance` / `replace_with` triad (which is error prone, only partly tested, and whose `replace_with_id` records just one of the two replaced rows) with an explicit, auditable model. The key correction over my first draft: **buyer-vs-seller side is already encoded in `use_cases`** (a `Buy-Fin` deal only loads `Buy-Fin` rows), so the only missing dimension is dual-agency consolidation. Modeling a separate `buyer_side`/`seller_side` scope would duplicate `use_cases` and mis-handle co-op-agent rows. Proposed schema additions to `task_templates`:

- `task_family` (text): a stable key shared by all rows that represent the same logical task, for example `request_hoa_docs`, `internal_thank_you`, `inspection_scheduled`.
- `dual_agency_behavior` (enum): `standard` (default) | `consolidated`. A `consolidated` row replaces every `standard` row in its family **only** when the deal is dual agency.

Generation rule:
- **Non-dual use case** (`Buy-Fin` / `Buy-Cash` / `Sell-Fin` / `Sell-Cash`): drop every `consolidated` row; keep `standard` rows. Side selection is already handled by `use_cases`. This alone fixes the single-side leak in Finding B without even needing the `use_cases` cleanup, because the consolidated rows are now filtered by behavior rather than by their (overlapping) use-case lists.
- **Dual use case** (`Both-Fin` / `Both-Cash`): for any family that has a `consolidated` row, drop that family's `standard` rows and keep the `consolidated` one; families with no `consolidated` row keep their `standard` rows (the id-merge in `_list_templates_for_generation` already prevents a single template from doubling).
- **Safety net:** after selection, de-duplicate by `(task_family, target)` so no family can ever emit twice for the same recipient. This also catches the plain redundant-row case (`Inspection Negotiated` 250/255/257) regardless of seed hygiene.

**Dependency-remap safeguard (logic gap caught on review):** `generate_tasks_for_transaction` resolves dependencies and due dates by `legacy_task_id` against the **filtered** template set ([task_generation_service.py:119-148](velvet-elves-backend/app/services/task_generation_service.py#L119)). If a row is dropped by the family filter, any task depending on its `legacy_task_id` would lose both its dependency link and its computed date. In the current seed the dependency chains stay within one tier (standard rows depend on standard rows, consolidated on consolidated), so the filter keeps chains intact, but this is fragile. The fix routes dependencies through `task_family` so a dependency always resolves to whichever family member survived selection. I will add a test that asserts no surviving task references a dropped `legacy_task_id`.

This collapses every over-generated family to exactly one instance per recipient and is trivially testable (one parametrized test per family per representation). The re-seed also tightens the `use_cases` lists as hygiene, but correctness no longer depends on it.

Interim minimal fix (if the schema work is deferred): correct `filter_both_representation` so it (a) runs for single-side use cases and drops consolidated rows there, (b) for Both deals drops the standard siblings of any family that has a consolidated row and keeps the consolidated row, and (c) abandons the name-based collapsing (two genuinely different tasks can share a name, for example the Agent vs Co-op Agent "Internal Thank You"). I recommend the schema approach because it is self-documenting and removes the brittle name/`replace_with_id` matching entirely.

### 3.3 Fix accuracy: compile conditions into predicates

Re-import the playbook so `conditions_json` holds executable predicates the existing `evaluate_conditions` already understands. The English notes stay in a separate `notes` field for human reference. The mapping below is **finalized on the standard real-estate convention** (gate every task on the contract reality; lender-driven tasks gate on financing because cash deals carry no lender-mandated deadline):

| Task id(s) | Logical task | Condition(s) | Convention rationale |
|---|---|---|---|
| 90, 95, 100, 110, 115, 120 | Request / Deliver HOA Docs | `has_hoa == true` | No HOA, no HOA document obligation |
| 170 | Order Home Warranty | `has_home_warranty == true` AND `warranty_ordered_by == "us"` | We only "order" when we are the ordering party |
| 180 | Confirm Home Warranty Order | `has_home_warranty == true` AND `warranty_ordered_by != "us"` | We "confirm" when the counterparty orders |
| 70 | Order Title | `title_ordered_by == "us"` | We only "order" when we are responsible |
| 80 | Confirm Title Order | `title_ordered_by != "us"` | We "confirm" when the counterparty orders |
| 210, 215, 220, 230, 240, 245, 250, 255, 257 | Inspection family | `has_inspection == true` | No inspection contingency, no inspection workflow |
| 280 | Buyer Documentation | none needed; scoped by `use_cases = [Buy-Fin]` | Underwriting documentation only exists on a financed buy; the use case already enforces this |
| 200 | Insurance Reminder | scope `use_cases` to `[Buy-Fin]` (drop `Buy-Cash`) | The homeowner's-insurance **commitment deadline** is lender-driven; cash deals have no contractual commitment date. Financing is encoded by use case, **not** a `has_mortgage` field |

**Correction caught on review:** my earlier draft gated tasks 200 and 280 on `has_mortgage == true`, but `has_mortgage` is **not** a field on the `Transaction` dataclass (it exists only in the wizard). Because `evaluate_conditions` treats a missing attribute as "condition not met" and returns `False` ([dependency_engine.py:204-207](velvet-elves-backend/app/services/dependency_engine.py#L204)), such a predicate would have **silently dropped** the Insurance Reminder and Buyer Documentation tasks on every deal. The standard, correct signal for financing in this system is the **use case** (`Buy-Fin` vs `Buy-Cash`), so financing is enforced by scoping `use_cases`, not by a predicate. Task 280 is already `Buy-Fin` only; task 200's `use_cases` must be tightened from `[Buy-Fin, Buy-Cash]` to `[Buy-Fin]` in the re-seed.

Decided field-value conventions: `title_ordered_by` and `warranty_ordered_by` use `"us"` for "the side we represent is responsible" and any other value for the counterparty (matching the engine's existing case-insensitive comparison and the values already used in `test_dependency_engine.py`). Every predicate above references a verified attribute of the `Transaction` model (`has_hoa`, `has_home_warranty`, `warranty_ordered_by`, `title_ordered_by`, `has_inspection`), so none can fall into the missing-attribute trap. Tasks with no yes/no gate in the contract notes (welcome emails, utility info, closing information, referrals, thank-you) carry no condition and always apply for their use case. This table is now the seed source of truth; if Jake's firm practice differs on any single row, that row is a one-line `conditions_json` (or `use_cases`) edit, not an engine change.

### 3.4 Multi-dependency and text floats

- Change `dep_task_id` to support a list of predecessors (or add a `dep_task_ids` array), and have the calculator mature a task to the **latest** resolved predecessor (the common real-estate semantic, for example "inspection complete after whichever inspection-scheduled task closed").
- Replace text floats (the "matures on date entered" sentences) with either a real numeric float or a clearly-flagged "matures on completion" marker that the UI renders as "date set when predecessor completes" rather than emitting a wrong date.

### 3.5 State rules

Move attorney-vs-title behavior from name-substring matching to data: tag templates with a `closing_path` applicability (`attorney` | `title_escrow` | `any`) and filter on `transaction.closing_mode`. No behavior change for Indiana today; correctness when attorney-state playbooks are added.

### 3.6 Idempotency and re-generation

Keep the existing 409 guard ([transactions.py:1155](velvet-elves-backend/app/api/v1/transactions.py#L1155)) but route regeneration through a single code path shared with `switch_use_case_tasks` so completed tasks are always preserved and only stale, non-completed, template-sourced tasks are replaced. This also becomes the path used when an addendum changes the dates (Phase C2, Section 6).

### 3.7 Deadline conventions (decided on the standard contract rule)

Two distinct concerns, both resolved on the universal real-estate convention:

1. **Weekend/holiday roll-forward (P0, correctness).** Standard purchase agreements state that when a computed deadline falls on a Saturday, Sunday, or legal holiday, it extends to the **next business day**. I will apply this roll-forward to every resolved due date regardless of how it was counted. This is a correctness requirement, not a parity nice-to-have: a calendar-day computation that lands on a Sunday is simply the wrong legal deadline, so it belongs in Phase A.
2. **Business-day counting (Phase C parity).** The default counting basis is **calendar days**, because that is the legal default in standard forms unless the contract explicitly says "business days." I will add a per-template/per-deadline `day_basis` flag (`calendar` default | `business`) so a deadline the contract specifies in business days (for example "10 business days") counts only business days. The review UI shows both the raw computed date and the rolled/adjusted date with the basis label.

**Holiday calendar (decided):** US federal holidays plus the transaction state's legal holidays (Indiana for the primary market), tenant-configurable for firms operating in other states. A maintained library (for example `python-holidays`) supplies the calendar so the rules stay data-driven rather than hardcoded.

---

## 4. Wizard Task-Review UI (Jake's direct request)

Today generation happens **after** commit and is invisible. I will move it to a **preview-before-commit** model with a dedicated review step.

### 4.0 Three governing principles (added after the UI-grounding review)

These principles override any convenience of backend-only implementation. Every item in this plan is held to them:

1. **Everything is verifiable through the UI by a non-developer.** The testers are real-estate professionals, not engineers. No correctness claim in this plan may depend on reading the database, calling an API, or running a test file. Each engine fix (dates, de-duplication, conditions, roll-forward) must produce a **visible, clickable proof in the frontend** (Section 4.5 maps every fix to its on-screen proof). This is the direct fix for the recurring "end-to-end workflow breaks during frontend testing" problem: the workflow is only "done" when a tester can drive it start to finish with the mouse and see the right result.
2. **Maximum convenience, minimum typing.** The common path is mouse-only: smart defaults pre-selected, one-click accept, bulk actions, inline popovers reused from the existing key-date editor, and `<Select>` dropdowns instead of free-text wherever a value is bounded. The only place typing is unavoidable is naming a brand-new custom task. Removal reasons, target changes, and date changes are all click-driven.
3. **Design harmony, modern, unmistakably a professional real-estate tool.** The review surface is built strictly from the existing design system in [STYLE_GUIDE.md](velvet-elves-data/STYLE_GUIDE.md) and composes the project's shared primitives (`<Button>`, `<Input>`, `<Select>`, `<Dialog>`, `<AlertDialog>`, `StatusBadge`, `Badge`) rather than inventing markup. It mirrors the wizard's existing visual language (navy left-rail stepper, champagne accents, Lora serif titles, IBM Plex Mono kickers, hairline cards) and the in-app task-row anatomy from [TaskList.tsx](velvet-elves-frontend/src/components/tasks/TaskList.tsx). It must feel like the same premium app as the Active Transactions workspace and the `/calendar` page (the in-app style benchmark), not a bolted-on form. Conformance details are in Section 4.6.

**Reuse caution caught during grounding:** the existing [AddTaskModal.tsx](velvet-elves-frontend/src/components/active-transactions/AddTaskModal.tsx) is a useful reference for the "AI suggested approaches" pattern, but it uses native `<select>` elements and hand-rolled class strings, which violate STYLE_GUIDE §9.3 and anti-pattern #15. The review step (and any new task UI) must use the Radix `<Select>` and shared `<Button>`/`<Input>` instead. I note this so we do not propagate the drift by copy-pasting.

### 4.1 New backend endpoint: dry-run preview

`POST /api/v1/transactions/preview-tasks` (no persistence). Accepts the same wizard payload the create call uses (use case, represented side, dates, contingency flags, title/warranty answers). Returns the fully-resolved task list **without** writing anything:

```jsonc
{
  "tasks": [
    {
      "task_family": "order_title",
      "name": "Order Title",
      "milestone_label": "Title Work Ordered",
      "target": "Title",
      "cc_targets": ["Agent", "Co-op Agent"],
      "automation_level": "Automated",
      "due_date": "2026-03-06",
      "due_basis": "Contract Acceptance + 5d",     // human-readable derivation
      "depends_on": ["Contract Acceptance Date"],
      "included_because": "title_ordered_by = us", // which condition/answer drove inclusion
      "warnings": []                                 // e.g. "no closing date set"
    }
  ],
  "summary": { "total": 23, "undated": 0, "by_milestone": {"...": 4} }
}
```

`due_basis` and `included_because` are the key trust features: the user sees not just the date but **why** the task exists and **how** the date was derived.

**Logic detail verified on review:** at the review step the transaction does **not** exist yet (creation happens on "Approve & Create"), so the preview endpoint cannot take a `transaction_id`. It accepts the draft wizard payload, constructs a **transient, unsaved** `Transaction` object using the same request-to-model mapping the create endpoint uses, and runs a **pure planning function** (templates -> condition filter -> dual-agency filter -> state rules -> due dates -> roll-forward) that returns the resolved list without any repository writes. To guarantee the preview matches what gets committed, I will refactor the pure planning step out of `generate_tasks_for_transaction` (which currently interleaves planning with `task_repo.create` calls, [task_generation_service.py:123-174](velvet-elves-backend/app/services/task_generation_service.py#L123)) so both the preview endpoint and the commit path call the identical planner; only the commit path persists.

### 4.2 New wizard step: "Review Tasks"

Insert a `review` step between `confirm` and final creation, so `WIZARD_STEPS` becomes `upload -> parsing -> address -> purchase -> missing -> confirm -> review` and `STEP_LABELS` adds `review: 'Review Tasks'` ([wizardTypes.ts:30](velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L30)). The navy left-rail `WizardStepper` gains one more dot using its existing active/completed/pending styling (STYLE_GUIDE §6.6); no new stepper component.

**Canonical-spec reconciliation:** Workflow A Step 6 in [FRONTEND_UI_WORKFLOW_LOGIC.md](velvet-elves-data/FRONTEND_UI_WORKFLOW_LOGIC.md) currently generates tasks silently on "Accept & Create" with no review. This plan **amends** that flow: "Accept & Create" on the Confirm step advances to the Review step; the transaction is created only from the Review step's "Approve & Create". I will update §4.5 and Cross-Cutting Workflow A in that document as part of the work so the spec and the build stay in lockstep (the root cause of past breakage was the plan drifting from the spec).

**Layout (wizard right panel, `max-w-2xl`, STYLE_GUIDE §4.4):**

- **Summary hero strip** at the top, in the confirm-screen hero-card vocabulary (§6.3): mono kicker `✦ REVIEW YOUR CHECKLIST`, serif headline like `23 tasks · 0 undated · Mar 1 – Apr 15`, and three at-a-glance stat chips (total tasks, tasks needing attention, span to closing) using `tabular-nums`. This gives the non-dev tester an instant, readable verdict.
- **Tasks grouped by milestone** (Offer Accepted, Title Work Ordered, Inspection, Appraisal, Clear to Close, Closing, Post-Close), each group a hairline card (`rounded-xl border border-ve-border`) with a mono-kicker section header and a count chip, tasks sorted by due date within the group. Grouping by milestone (not a flat list) is what makes a 20+ task list scannable to an agent.
- **Task row anatomy mirrors [TaskList.tsx](velvet-elves-frontend/src/components/tasks/TaskList.tsx)** so it already looks like the rest of the app: an include toggle (the same circular control, checked by default), the task name, a `StatusBadge`/automation `Badge` (Automated / To Be Automated / Manual), the due date with an overdue-style relative label ("in 5 days", "14 days before closing"), a target chip (Buyer, Seller, Title, Loan Officer, etc.), and a small "why" line showing the `included_because` reason.

**Convenience-first controls (mouse-driven, minimal typing):**

- **Accept everything in one click.** The page loads with every task included and every AI date pre-filled; the default action is simply "Approve & Create". A tester who trusts the list does nothing but click once.
- **Edit a due date** via the same inline date popover used by the Active Transactions key-date editor (Workflow B step 4) — click the date, pick from the calendar, Save. No manual date typing.
- **Change the target/assignee** via a Radix `<Select>` chip (Myself / AI Agent / team member), not a text field.
- **Include/exclude a task** by toggling its circle; excluded tasks dim in place with a one-click **Undo**, so nothing is destructive and nothing requires confirmation typing.
- **Removal reason** (for the feedback loop) is captured with **one-click chips** ("Not applicable", "Duplicate", "We don't do this"), never a text box. It is optional; skipping it still removes the task.
- **Bulk actions** on each milestone group header: "Include all" / "Exclude all", and a global "Reset to AI defaults". 
- **Add a custom task** via a compact inline form composed from `<Input>` (name — the only typed field), `<Select>` (completion method, reusing the 8 methods already defined in AddTaskModal), and the date popover. Before saving, reuse the existing **similar-task Add / Combine / Disregard** check (Workflow C step 2, `POST /api/v1/ai/suggest-task-approach` already exists) so the tester is guided, not left to type freely.

**Live re-preview (the key testability feature):** a "Back" to the Confirm/Purchase steps lets the tester change a wizard answer (toggle HOA off, switch who orders title, change the closing date) and return to see the checklist **recompute live**. This is how a real-estate tester validates the conditions and date math with the mouse alone, with no developer involvement (see Section 4.5).

**Warnings, using the status triads (§2.3):** any **undated** task is flagged amber at the top with a one-click jump to it; a missing anchor date (no closing date entered) shows a clear amber explanation of which tasks cannot be dated yet; any **duplicate family** (should be zero after the fix) is flagged red as a visible safety net so a tester would immediately see a regression.

**Footer:** a ghost "Back" and a single brand-orange "Approve & Create Transaction" primary (`<Button variant="default">`). Approve persists the transaction and generates the **reviewed** set (including edits, exclusions, and added tasks), not a fresh server-side regeneration; this requires the generate path to accept the reviewed payload (Section 3.6 shared planner makes this clean). The post-create toast keeps the spec's wording: "Transaction '[Client Name]' created with [X] tasks".

### 4.3 Reliability fix

Generation must no longer be best-effort. If preview fails, the user cannot reach the review step; if commit-time generation fails, the wizard must surface the error and offer retry rather than silently navigating away.

### 4.4 Admin alignment

The same preview engine backs the existing admin task-template surfaces so a non-developer admin can verify the playbook through the UI:
- [TaskTemplateListPage.tsx](velvet-elves-frontend/src/pages/admin/TaskTemplateListPage.tsx) (`/admin/task-templates`) lists templates with Use Cases, Dependencies, Float, and Automation columns (FRONTEND_UI_WORKFLOW_LOGIC §10.3).
- [TaskTemplateDetailPage.tsx](velvet-elves-frontend/src/pages/admin/TaskTemplateDetailPage.tsx) (`/admin/task-templates/:id`) already specs a **"This task will be generated for [X] transaction types"** preview and a condition/dependency builder (§10.4). I will wire that preview to the shared planner so editing a condition or float shows the effect on a sample transaction before saving, and so the corrected `dual_agency_behavior`/`conditions_json`/`day_basis` fields are visible and editable in the UI rather than only in the seed file. This makes the re-seed itself testable by an admin: open a template, see its condition and which use cases it fires for.

### 4.5 UI proof for every engine fix (the non-dev tester walkthrough)

This is the section that closes the "frontend testing breaks end-to-end" gap. Each backend fix is paired with an on-screen proof a real-estate professional can verify with the mouse, no API or database access. This doubles as the acceptance script for Phase A + B.

| Engine fix | What the tester does (mouse only) | What they must see (UI proof) |
|---|---|---|
| Dates resolve (Finding A) | Create a Buy-Fin deal with a contract date and closing date; reach the Review step | Every task shows a real due date; the hero strip reads "0 undated"; no task says "no date" |
| Closing-anchored math | On Review, note `Schedule Closing`'s date; go Back, change the closing date by 7 days, return | `Schedule Closing` and other closing-anchored dates shift by 7 days; the relative label still reads "14 days before closing" |
| Weekend/holiday roll-forward (3.7) | Pick a closing date whose minus-14 lands on a Sunday or a holiday | The displayed deadline shows the next business day, never a weekend/holiday date |
| De-duplication (Finding B) | Create a Buy-Fin deal and scan the Inspection and Post-Close groups | Exactly one "Inspection Scheduled", one "Closing Gift", one HOA-request task; no red duplicate banner |
| Conditions: HOA (Finding C) | Go Back to Purchase, toggle "HOA" off, return to Review | All HOA tasks disappear from the list; toggling it on brings them back |
| Conditions: inspection | Toggle "Home inspection" off | The entire inspection family (scheduled, completed, response, negotiated) disappears |
| Conditions: who orders title | Switch "Who orders title" between us / other party | "Order Title" vs "Confirm Title Order" swap accordingly |
| Dual agency | Create a Buyer & Seller (dual agency) deal | The consolidated single tasks appear once; no buyer+seller duplicate pairs |
| Review + edit | Change a task's date and target, exclude one task, add one custom task, Approve & Create | The created transaction's drawer shows exactly the reviewed set: the edited date, the new target, the excluded task absent, the custom task present |
| Reliability (4.3) | (Negative test) trigger a failure | A clear error with a Retry action; the wizard never silently navigates away with a half-made transaction |

I will deliver this as an explicit step-by-step UI test script appended to [WIZARD_TESTING_GUIDE.md](velvet-elves-data/WIZARD_TESTING_GUIDE.md), written for a real-estate professional (click here, expect this), consistent with the existing [FRONTEND_UI_TESTING_GUIDELINES.md](velvet-elves-data/FRONTEND_UI_TESTING_GUIDELINES.md). Per the project's visual-verification practice, I will also render the Review step and capture screenshots before calling it done, rather than building it blind.

### 4.6 Design conformance (harmonized, modern, professional)

The review surface is bound to [STYLE_GUIDE.md](velvet-elves-data/STYLE_GUIDE.md); the specific bindings:

- **Shell & container:** wizard host modal (1040px, `rounded-[16px]`), right panel `max-w-2xl` (§4.4). No new shell.
- **Type voices:** mono kicker (`font-mono text-[9px] tracking-[1.8px] uppercase`) for section/eyebrow labels, Lora serif for the hero headline and milestone titles (one serif title per card, §3.3), IBM Plex Sans for body, `tabular-nums` on all dates/counts.
- **Color:** champagne (`ve-orange*`) only for the primary CTA, AI "why" accents, and the ✦ kicker; status triads (§2.3) for amber undated / red duplicate / green ready; everything else neutral. No raw hex, no Tailwind default palette (§2.4, anti-pattern #9).
- **Components:** shared `<Button>` variants (default primary, ghost back), Radix `<Select>` for target/method (never native `<select>` — §9.3), `<AlertDialog>` for any confirm, the existing date popover for dates. `StatusBadge` and `Badge` for status/automation, matching TaskList.
- **Spacing/borders/shadows:** 4px grid, `p-5` card bodies, hairline `border-ve-border`, `shadow-card`/`shadow-soft` only (§5). Calm motion: `animate-fade-in`, ease-out 200–300ms, no spring (§8).
- **Benchmark:** the milestone grouping, stat chips, and timeline feel should track the `/calendar` page and the Active Transactions drawer (the in-app benchmarks), so the Review step reads as a native part of the professional workspace, not a wizard afterthought. If a timeline visualization is added, it is a hand-built React SVG/CSS port in the brand style, not a charting library.
- **Internal-page rule:** the standalone `/transactions/new` route keeps the breadcrumb header anatomy (§15.2); the wizard-modal variant keeps the wizard chrome. No `max-w` dead-margin failures (anti-pattern #13).

---

## 5. Competitive Analysis: ListedKit vs Velvet Elves

ListedKit positions itself as "the AI transaction coordinator" ("Ava"). Its pitch: connect email, upload a contract, and the AI extracts every date/party/contingency, builds the timeline and task list automatically, tracks every deadline, drafts and sends emails, and syncs deadlines to the calendar. Sources are listed at the end of this section.

### 5.1 ListedKit capabilities (verified from listedkit.com)

| Capability | What ListedKit does |
|---|---|
| Contract reading | Reads any state's purchase agreement, including handwritten and custom brokerage forms, with no setup templates; extracts every date, party, and contingency |
| Timeline building | Auto-builds a live action list of deadlines/parties/contingencies; handles relative deadlines like "7 business days before closing" |
| Addendum handling | Re-reads addenda and updates the timeline automatically |
| Deadline math | Business-day aware (explicitly markets "business days before closing") |
| Inbox monitoring | Matches incoming emails to the right deal by context (parties, property, prior threads) even with no address in the subject |
| Email automation | Drafts and auto-replies from Gmail/Outlook with no AI branding; scheduled reminders before deadlines; bulk-share timelines |
| SMS | Ask questions about a deal and get answers from the file via text |
| Calendar sync | One click adds every deadline to Google/Outlook Calendar and invites all parties |
| Document reading | Reads inspection reports, HOA packages, etc., creates tasks, answers content questions |
| Task learning | Learns custom task lists from user behavior; reassigns tasks between team members |
| Pipeline view | Visual dashboard with stage tracking and bottleneck identification |
| Integrations | Gmail, Outlook, Follow Up Boss (CRM), Calendar |
| Pricing | Usage-based, roughly $9.99 to $14.99 per transaction; first one free; no subscription |

### 5.2 Where Velvet Elves falls short today

1. **Correct dated timelines (the core).** This is ListedKit's headline feature and is currently broken in VE (Finding A). Until fixed, VE loses on its own primary surface. This is why the P0 repair is the top priority.
2. **Accuracy/de-duplication.** ListedKit produces a clean list; VE currently produces duplicates and irrelevant tasks (Findings B, C).
3. **Business-day deadline math.** ListedKit markets "X business days before closing." VE's float math is calendar-day only and ignores weekends and holidays. Real contracts frequently specify business days; calendar-day math produces deadlines that land on weekends/holidays and are legally wrong.
4. **Addendum-driven recalculation.** ListedKit re-reads an addendum and updates the timeline. VE has `switch_use_case_tasks` for use-case changes but no "addendum changed the closing/inspection date -> recompute all dependent dates -> show the diff for approval" loop.
5. **Calendar sync at the deadline level.** Milestone 6.1 scopes generic calendar hooks, but not "one click pushes every task deadline as an event and invites the parties." This is a concrete, high-value parity item.
6. **Inbox-to-deal matching.** VE has communication logging and a structured vendor-reply parser (Milestone 4.3, complete), but not ListedKit-style contextual matching of arbitrary inbound email to the right deal.
7. **Task review/approval in creation.** ListedKit shows the action list immediately; VE hides it (Finding F). Section 4 closes this.

### 5.3 Where Velvet Elves can surpass ListedKit

VE is not a thinner clone; once the engine is repaired it has structural advantages ListedKit does not market:

1. **Deterministic firm playbook + auditable dependency graph.** ListedKit infers tasks per contract with AI. VE encodes the brokerage's exact SOP (the REWORKING DB) as a versioned, admin-editable template library with explicit dependencies, targets, CC lists, milestone labels, and automation levels. The differentiator is **deterministic + auditable + AI-augmented**: same inputs always yield the same vetted task set, every date has a visible derivation (`due_basis`), and AI is used to fill gaps and validate rather than to invent the whole list. For a transaction-coordination firm, reproducibility and auditability beat black-box inference.
2. **Role-targeted tasks and multi-role workspaces.** VE tasks carry a `target` (Buyer, Seller, Co-op Agent, Title, Loan Officer, etc.) and CC list, feeding distinct Agent, Team Lead, Attorney, FSBO, Client, and Vendor workspaces under RBAC and white-label multi-tenancy. ListedKit centers on the agent/TC. VE serves the whole transaction ecosystem.
3. **Structured vendor reply loop.** VE already parses constrained vendor replies ("Scheduled: YYYY-MM-DD") into proposed, human-approved date updates (Milestone 4.3). That is a tighter, more reliable automation than free-form email drafting.
4. **Attorney workflow + state-based closing rules.** VE models attorney vs title/escrow closings, recording/disbursement timing, and legal packet review with explicit AI-vs-human guardrails. ListedKit does not target legal packet coordination.
5. **Confidence-scored, double-checked extraction with field-level human review.** VE's wizard already does two-pass extraction, per-field confidence, and inline discrepancy flags. This is a trust advantage over "the AI just did it."
6. **Closed-loop improvement.** Milestone 5.3 includes a post-closing task feedback loop (useful / unnecessary / missing). Wired to the review-UI "remove reason" data, VE can continuously tune the playbook with real evidence, which a template-free system cannot accumulate the same way.

**Strategic framing for Jake:** ListedKit sells "AI guesses your timeline." VE should sell "Your firm's proven playbook, executed automatically, every date provable, with AI filling the gaps and watching for drift." That is a stronger promise for a professional TC operation, and it is achievable once Findings A to C are fixed.

**Sources:** [listedkit.com](https://www.listedkit.com/), [listedkit.com/features](https://www.listedkit.com/features), [ListedKit AI Review 2026](https://aiandrealtors.com/review-listedkit), [How AI Contract Analysis is Changing Transaction Management](https://listedkit.com/ai-contract-analysis/).

---

## 6. Gap-Closure Roadmap (to match, then surpass)

Phases are sequenced so the product is correct first, reviewable second, then competitively differentiated. Each maps to existing milestones where relevant.

### Phase A — Engine Correctness (P0, blocks everything)
- A1. Anchor-aware due-date calculation (Section 3.1) + full-path regression test.
- A2. Representation-scoped de-duplication (Section 3.2) + per-family tests.
- A3. Condition compilation and re-seed against the finalized mapping (Section 3.3).
- A4. Multi-dependency "latest predecessor" support and text-float cleanup (Section 3.4).
- A5. Weekend/holiday roll-forward on every resolved date (Section 3.7, item 1).
- **Exit criteria:** a Buy-Fin, a Sell-Cash, and a Both-Fin sample each produce zero duplicates, zero undated tasks (given both anchor dates), only condition-appropriate tasks, and no deadline landing on a weekend or holiday. (Detailed acceptance in Section 7.)

### Phase B — Task Review UI (P0/P1, Jake's request)
- B1. Dry-run preview endpoint with `due_basis` and `included_because` (Section 4.1).
- B2. Wizard "Review Tasks" step with grouping, edit/remove/add, warnings, and approve-to-commit (Section 4.2).
- B3. Generation reliability fix (Section 4.3).
- B4. Reuse preview in admin template/rule-builder UI (Section 4.4).

### Phase C — ListedKit Parity
- C1. Business-day deadline counting: the `day_basis` flag (`calendar` default | `business`) per Section 3.7, item 2, using the decided federal + state holiday calendar. Render both the raw and adjusted dates in the review UI. (The weekend/holiday roll-forward itself ships earlier, in A5.)
- C2. Addendum re-parse loop: detect a changed key date from a new document, recompute dependents through the shared regeneration path (Section 3.6), and present a date-diff for approval (preserving completed tasks).
- C3. Calendar-per-deadline sync: extend the calendar hooks already scoped in Milestone 6.1 so one action pushes every task due date to Google/Outlook with party invites. This builds on existing roadmap scope.
- C4. Inbox-to-deal matching: extend the inbound-email processing hooks from Milestone 4.1 to match arbitrary inbound email to a deal by parties/property/thread context, not just the constrained vendor replies already shipped in Milestone 4.3. **Scope note:** full contextual inbox matching is the largest item here and leans toward post-MVP (the milestones list pattern detection and specific CRM integrations as post-MVP); I would stage it as a follow-on rather than fold it into the P0/parity work.

### Phase D — Surpass
- D1. AI gap-fill and validation at preview time: AI proposes tasks the playbook may be missing for this specific contract (clearly labeled, human-approved), and flags playbook tasks that look inapplicable, without ever silently changing the deterministic set.
- D2. Drift detection: surface deals whose dependencies are at risk of breaking a deadline (ties into the dashboard intervention queue already designed in Milestone 5.1).
- D3. Feedback-driven playbook tuning: aggregate review-UI removals and post-closing feedback (Milestone 5.3) into admin-visible suggestions to adjust templates/conditions.
- D4. Document-reading task creation: when an inspection report or HOA packet is uploaded, propose follow-up tasks (parity with ListedKit's document reading, but routed through the same review/approve gate).

---

## 7. Acceptance Criteria & Test Plan

Acceptance is defined **primarily as what a real-estate tester sees in the UI**, because that is how this product is validated and where past efforts broke. Engineering tests exist underneath as a backstop, but no item is "done" until its UI proof passes.

**Primary: UI walkthrough (non-developer, mouse only).** The Section 4.5 table is the acceptance script. It will be delivered as a numbered click-through in `WIZARD_TESTING_GUIDE.md`. Every row must pass by observation alone: dated tasks visible, "0 undated" in the hero, no duplicate banner, conditions toggling task families on/off live, dual-agency consolidation, edits surviving into the created transaction's drawer, and a clean error+retry on failure. The reviewer renders the screen and captures screenshots before sign-off.

**Backstop: engineering guard tests (Phase A).**
- Given a Buy-Fin transaction with `contract_acceptance_date` and `closing_date` set, every generated task has a non-null `due_date`, and closing-anchored tasks fall on the correct number of days before closing (for example `Schedule Closing` = closing - 14).
- No task family appears more than once per recipient for any single-side use case; the corrected families (Section 3.2) each appear once.
- A Both-Fin transaction emits the consolidated variant of each family once and none of the side-specific variants.
- With `has_hoa = false`, no HOA tasks; with `has_inspection = false`, no inspection-family tasks; with `title_ordered_by != "us"`, "Order Title" absent but "Confirm Title Order" present.
- No generated due date falls on a Saturday, Sunday, or recognized holiday; any such date rolls forward to the next business day (Section 3.7).
- The preview endpoint and the commit path call the same shared planner, so the previewed list equals the persisted list (names, targets, dates), with `due_basis` and `included_because` populated.
- A test exercises the **full production path** (load-by-use-case then calculate) and fails if anchors are not seeded (guards Finding A permanently); a test asserts no surviving task references a dropped `legacy_task_id` (guards the dependency-remap, Section 3.2).

**Parity (Phase C), also UI-observable:**
- A contract specifying "X business days" produces a deadline that skips weekends/holidays, and the Review step shows both the raw and adjusted date with the basis label.
- Uploading an addendum that changes the closing date updates all dependent dates and shows a date-diff for approval in the UI, without disturbing completed tasks.

---

## 8. Decisions (resolved on the standard-practice principle)

Per Jake's direction to do everything in the most standard and correct manner, the items that were previously open are now decided as follows. Each is implemented as data/config, so any single one can be adjusted later with a one-line change rather than re-opening the design.

1. **Condition mapping — decided (Section 3.3).** Gate every conditional task on the contract reality; gate lender-driven tasks (insurance commitment, underwriting documentation) on financing because cash deals carry no lender-mandated deadline. `title_ordered_by` / `warranty_ordered_by` use `"us"` for the represented side, any other value for the counterparty. The table in Section 3.3 is the seed source of truth.
2. **Deadline conventions — decided (Section 3.7).** Default counting is calendar days (the legal default unless the contract says otherwise); a per-deadline `day_basis` flag enables business-day counting where the contract specifies it; every resolved date rolls forward to the next business day if it lands on a weekend or holiday. Holiday calendar = US federal + transaction-state holidays (Indiana default), tenant-configurable, sourced from a maintained library.
3. **Re-seed strategy — decided.** A new versioned seed migration corrects anchors, conditions, representation scope, multi-dependency, and use-case overlaps in one place. It replaces only global/system templates (`tenant_id IS NULL`) and preserves all tenant customizations, consistent with the existing seed's `DELETE ... WHERE tenant_id IS NULL` pattern. Forward-only with a documented rollback.
4. **Review step placement — decided.** A dedicated "Review Tasks" wizard step after `confirm`. An explicit review gate before an irreversible commit is the standard wizard pattern and best satisfies Jake's request to examine each task individually; an inline panel would bury a safety-critical step.
5. **AI gap-fill boundary — decided (hard rule).** AI-proposed tasks are always labeled and human-approved, never auto-merged into the deterministic playbook set. This preserves the auditable, reproducible promise that differentiates VE from a black-box system.

### Residual items (confirmation only, not blocking)
- If Jake's firm practice differs on any single condition row in Section 3.3, that is a one-line `conditions_json` edit, not an engine change.
- The default holiday set assumes Indiana as the primary market; firms in other states get their state calendar via the tenant setting.

---

## 9. Note

This document is plan only. No application source code was modified in producing it. The previously-open design questions are now resolved on the standard-practice principle (Section 8); implementation proceeds on this plan, with the residual confirmations handled as data edits rather than design changes.

---

## 10. Plan Review & Correction Log (2026-06-05)

I re-reviewed this plan against the requirements documents (milestones.txt), the seed (`202603111730_seed_task_templates.sql`), and the live backend/frontend source, specifically to find workflow or logic errors in the plan itself. Findings A through F (the diagnosis of the existing system) all held up on re-check. The following errors **in my own plan** were found and corrected:

| # | Error in the prior draft | Why it was wrong | Correction |
|---|--------------------------|------------------|-----------|
| 1 | Conditions for tasks 200 (Insurance Reminder) and 280 (Buyer Documentation) gated on `has_mortgage == true` | `has_mortgage` is not an attribute of the `Transaction` dataclass ([transaction.py](velvet-elves-backend/app/models/transaction.py)); it exists only in the wizard. `evaluate_conditions` returns `False` for a missing attribute, so the predicate would have silently dropped both tasks on every deal. | Section 3.3: gate financing via `use_cases` (`Buy-Fin`), not a predicate; tighten task 200 to `[Buy-Fin]`. Added an explicit warning that all predicates must reference verified `Transaction` fields. |
| 2 | Finding C listed `has_mortgage` among fields "present on the `Transaction` model" | Same as above; factually incorrect about the model. | Finding C: corrected the field list and documented that financing is `financing_type` + use case, not `has_mortgage`. |
| 3 | De-dup design used a `representation_scope` of `buyer_side`/`seller_side`/`single`/`both_only` | Buyer-vs-seller is already encoded in `use_cases`; a side scope duplicates that and mis-handles co-op-agent rows. "Both" actually means dual agency, not "two parties." | Section 3.2: replaced with `task_family` + `dual_agency_behavior` (`standard`/`consolidated`); side selection stays in `use_cases`. |
| 4 | Finding B said `Internal Thank You` is generated "three times" and described the leak as uniform 2x-3x duplication | Verified targets in the seed: 500 (Agent) and 510 (Co-op Agent) are both legitimate on a single-rep deal; only 505 (dual-agency "Both") leaks. The leak is two distinct forms (true same-target dups vs inapplicable dual-agency extras), not uniform tripling. | Finding B: rewritten with per-family target evidence and the two leak categories; noted 250/255/257 as a separate redundant-row error. |
| 5 | Data-driven anchor option (3.1, option 2) included anchor rows in generation without saying they must not be emitted | Including rows 5/1000 in generation without an emit guard would create "Contract Acceptance Date" and "Closing Date" as actionable tasks. | Section 3.1: added `emits_task = false` / resolve-but-do-not-emit; recommended the minimal in-engine seeding as lower risk. |
| 6 | Preview endpoint (4.1) implied it could run generation, but the review step runs before the transaction exists | The engine operates on a `Transaction` object; at review time none exists, and `generate_tasks_for_transaction` interleaves planning with DB writes. | Section 4.1: endpoint builds a transient unsaved `Transaction` from the draft payload and calls a pure planner refactored out of the commit path, so preview and commit share identical logic. |
| 7 | Dependency resolution after family filtering was not addressed | A dependency referencing a `legacy_task_id` that the family filter drops would lose its link and date. | Section 3.2: added a dependency-remap safeguard (resolve dependencies through `task_family`) and a test asserting no surviving task references a dropped id. |
| 8 | Finding A said dependent tasks "all point at 5 or 1000" | Some point at intermediate tasks that themselves chain back to the anchors. | Finding A: reworded to "every chain roots at 5 or 1000 directly or via an intermediate," with examples. |
| 9 | C4 (inbox-to-deal matching) was listed as parity without scope caveat | Full contextual inbox matching leans post-MVP per the milestones. | Section 6: added a scope note staging C4 as a follow-on; clarified C3 builds on Milestone 6.1 hooks. |

No workflow contradictions were found between this plan and `milestones.txt` (the P0 engine work aligns with Milestone 2.2's "no AI creativity at generation," the review UI with the Phase 3 wizard, and C1/C3/C4 with Milestones 6.1/4.1). The plan remains internally consistent after these edits.

### 10.1 Second review pass — UI grounding & testability (2026-06-05)

Triggered by the feedback that prior plans were not grounded in the design system, the canonical workflow spec, or the real frontend source, and that the deliverable must be fully validatable through the UI by real-estate professionals (not developers), with maximum convenience and design harmony. I read `STYLE_GUIDE.md` in full, the `FRONTEND_UI_WORKFLOW_LOGIC.md` New Transaction (§4.5) / Workflow A / Workflow C / admin template (§10.3–10.5) sections, and the actual task components (`TaskList.tsx`, `AddTaskModal.tsx`, the admin template pages). Changes made to the plan:

| # | Gap in the prior draft | Correction |
|---|------------------------|-----------|
| 10 | UI was described abstractly and the plan was backend-weighted; a non-dev tester could not validate the engine fixes | Added Section 4.0 (three governing principles) and Section 4.5 (a per-fix UI-proof table = the non-dev acceptance script); reframed Section 7 so acceptance is UI-observable first, engineering tests as backstop |
| 11 | No grounding in the design system | Added Section 4.6 binding the review surface to `STYLE_GUIDE.md` (type voices, color triads, shared components, spacing, calm motion, the `/calendar` benchmark) |
| 12 | Risked propagating a known style drift | Flagged that `AddTaskModal.tsx` uses native `<select>` and hand-rolled classes (violates §9.3 / anti-pattern #15); the review step must compose Radix `<Select>` and shared `<Button>`/`<Input>` instead |
| 13 | Convenience was under-specified; the draft captured removal reasons via typed input | Section 4.2 rewritten as mouse-first: defaults pre-accepted, one-click approve, inline date popover (reused from key-date editor), `<Select>` for target/method, include/exclude toggles with Undo, one-click removal-reason chips, bulk per-milestone actions; typing limited to naming a custom task |
| 14 | Review step silently contradicted the canonical spec | Section 4.2 now explicitly amends Workflow A Step 6 / §4.5 and commits to updating `FRONTEND_UI_WORKFLOW_LOGIC.md` in lockstep, since spec drift was a root cause of past breakage |
| 15 | "Live recompute on changing a wizard answer" was not called out as the key tester capability | Added the Back-and-recompute behavior so a tester validates conditions and date math by changing answers and watching the list update, mouse only |
| 16 | Admin verification path was vague | Section 4.4 grounded in the real `/admin/task-templates` pages and their existing "generated for [X] transaction types" preview, so the re-seed is admin-verifiable in the UI |

Net effect: the plan now treats the UI as the contract. Every engine fix has a visible, mouse-driven proof; the review experience is convenience-first and built from existing brand components; and the spec document will be updated alongside the build so frontend testing follows a seamless, pre-defined path instead of discovering breakage.
