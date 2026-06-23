# AI Wizard — Transaction Creation & Task-List Generation — Critical Review

**Reviewer:** Engineering (Jan)
**Date:** 2026-06-23
**Scope:** End to end, from "Start New Transaction" through the deterministic
task-list generation, including the master task-template library and its
authoring/onboarding surfaces.
**Verdict:** Not perfect. The core engine is well architected and, in the happy
path, genuinely good. But there are several **silent-failure correctness bugs**
that produce plausible-looking but wrong task lists, and one **critical
onboarding gap**: a tenant cannot faithfully express their own legacy task list
through the authoring surfaces. That last point matters now, because Audri's
team is about to implement exactly that.

---

## 0. How I reviewed this

I read the shipped code end to end, not the plans:

- Engine: [task_generation_service.py](../velvet-elves-backend/app/services/task_generation_service.py),
  [dependency_engine.py](../velvet-elves-backend/app/services/dependency_engine.py),
  [state_rules.py](../velvet-elves-backend/app/services/state_rules.py),
  [timeline_planner.py](../velvet-elves-backend/app/services/timeline_planner.py)
- Data: [202603111730_seed_task_templates.sql](../velvet-elves-backend/supabase/migrations/202603111730_seed_task_templates.sql),
  [20260605_task_engine_fix.sql](../velvet-elves-backend/supabase/migrations/20260605_task_engine_fix.sql),
  [REWORKING_TASK_DB.csv](REWORKING_TASK_DB.csv)
- API + schema: [transactions.py](../velvet-elves-backend/app/api/v1/transactions.py),
  [task_templates.py](../velvet-elves-backend/app/api/v1/task_templates.py),
  [schemas/transaction.py](../velvet-elves-backend/app/schemas/transaction.py),
  [schemas/task_template.py](../velvet-elves-backend/app/schemas/task_template.py),
  [task_template_repository.py](../velvet-elves-backend/app/repositories/task_template_repository.py)
- Frontend: [NewTransactionWizard.tsx](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx),
  [ReviewTasksStep.tsx](../velvet-elves-frontend/src/components/wizard/ReviewTasksStep.tsx),
  [useWizardApi.ts](../velvet-elves-frontend/src/hooks/useWizardApi.ts)

---

## 1. Executive summary

### What is genuinely strong (keep, do not regress)

1. **Preview == Create.** Both the dry-run and the commit call the same
   `plan_tasks_for_transaction`, so what the user reviews is what gets saved.
   This is the right architecture.
2. **Transparency.** Each planned task carries `included_because`, `due_basis`,
   `depends_on`, and `warnings`, and the Review UI renders them
   ([ReviewTasksStep.tsx:670](../velvet-elves-frontend/src/components/wizard/ReviewTasksStep.tsx#L670)).
3. **Dual-agency consolidation is correct.** The `standard` / `consolidated` /
   `suppressed` model with `(task_family, target)` de-dup
   ([dependency_engine.py:416](../velvet-elves-backend/app/services/dependency_engine.py#L416))
   resolves the "Both" cases (one combined Internal Thank You, no Co-op Agent
   Welcome, referrals from both clients) exactly as the legacy notes intend. I
   traced every family; this part holds up.
4. **Business-day roll-forward** off weekends and US federal holidays
   ([dependency_engine.py:294](../velvet-elves-backend/app/services/dependency_engine.py#L294))
   matches contract convention.
5. **Deterministic generation.** No LLM decides the list. Good for trust and
   for testers.

### The headline problems

| # | Severity | Problem | One-line impact |
|---|---|---|---|
| C1 | Critical | `title_ordered_by` defaults to `None`; both title tasks are then condition-excluded | A deal can be created with **no title task at all** |
| C2 | Critical | Missing `contract_acceptance_date` silently dates tasks from **today**, with no warning | Confident, wrong deadlines on the most-used anchor |
| C3 | Critical | Missing day-offset fields (`hoa_doc_days`, `inspection_response_days`, `insurance_commitment_days`) silently collapse to the anchor date | Critical deadlines (inspection response) land on the wrong day, silently |
| H1 | High | Tenants cannot author the full model: create-template API and CSV import cannot set `task_family` / `dual_agency_behavior` / `dep_task_ids` / `day_basis` | A brokerage's own legacy list onboards as a **degraded** engine (no consolidation, no multi-predecessor) |
| H2 | High | `apply_state_rules` is name-substring matching against a library that has **no** attorney/state tasks | "State-aware" is effectively inert; attorney states are not actually handled |
| H3 | High | `switch_use_case_tasks` matches existing tasks by **name**, and does not re-date survivors | Use-case change mid-deal mis-preserves/mis-removes and leaves stale dates |
| M1 | Medium | Manual / AI-added deadlines do not recompute when closing/contract dates change | An addendum moves closing; user-added deadlines do not follow |
| M2 | Medium | `day_basis='business'` is supported by code but used by **no** seed row | Contracts written in "business days" are modeled as calendar days |
| M3 | Medium | Cash-deal appraisal inconsistency in the seed (265 exists, 270 financed-only) | Cash deals get "Appraisal Ordered" but never "Appraisal Completed" |
| L1 | Low | `generate` 409s if any task exists; no partial-failure recovery | A half-failed commit cannot be re-run cleanly |

Details and fixes below.

---

## 2. Critical findings (silent wrong output on real deals)

These are the dangerous class: the system does not error, it produces a
confident task list that is quietly wrong. That is the exact failure mode the
team has been bitten by before (verify rendered output, not the mechanism).

### C1. A deal can be created with no title task

- **Where:** schema default `title_ordered_by: str | None = None`
  ([schemas/transaction.py:58](../velvet-elves-backend/app/schemas/transaction.py#L58));
  seed conditions set Order Title (70) to require `title_ordered_by == "us"` and
  Confirm Title (80) to require `title_ordered_by != "us"`
  ([20260605_task_engine_fix.sql:98-101](../velvet-elves-backend/supabase/migrations/20260605_task_engine_fix.sql#L98));
  condition evaluation returns **False** when the field is unset
  ([dependency_engine.py:366-370](../velvet-elves-backend/app/services/dependency_engine.py#L366)).
- **Effect:** If the wizard does not send `title_ordered_by` (it is an optional
  select, not a gated/required field — it sits in the contingencies group at
  [NewTransactionWizard.tsx:1177](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L1177)
  with no submit gate), then **neither** Order Title **nor** Confirm Title
  populates. Title work is mandatory on essentially every resale transaction.
  The deal silently launches with no title-ordering task and no warning.
- **Why it matters to an agent/TC:** Title is the spine of the closing. A task
  list missing it is worse than no list, because the TC trusts it.
- **Fix (pick one, I recommend the first two together):**
  1. Make `title_ordered_by` a **required** wizard answer before
     "Approve & Create" (it is a single click; default the select to the most
     common value for the tenant, e.g. "us").
  2. Add a **plan-level safety check**: if zero tasks in the `order_title`
     family survive, emit a Review-step warning ("No title task was generated.
     Confirm who orders title.") rather than failing silent.
  3. Optionally give `title_ordered_by` a sensible non-null default at the
     model layer so the order-vs-confirm decision is always made.

### C2. Missing contract-acceptance date silently dates tasks from today

- **Where:** `anchor_date = transaction.contract_acceptance_date or date.today()`
  ([dependency_engine.py:176](../velvet-elves-backend/app/services/dependency_engine.py#L176)).
  The warning path only fires for dependency-based tasks whose date is `None`
  ([task_generation_service.py:197-202](../velvet-elves-backend/app/services/task_generation_service.py#L197)),
  so a no-dependency task anchored to contract acceptance gets `today + float`,
  which is **not None**, so **no warning is shown** and it is **not counted as
  undated**.
- **Asymmetry that proves the bug:** a missing **closing** date does the right
  thing (the task stays undated and the Review step shows "No closing date set"
  via the `undated` count at
  [ReviewTasksStep.tsx:399](../velvet-elves-frontend/src/components/wizard/ReviewTasksStep.tsx#L399)).
  A missing **contract acceptance** date does the wrong thing (fabricates dates
  off today). The two anchors are handled inconsistently.
- **Effect:** The whole contract-anchored half of the list (Review
  Documentation, Welcomes, Order Title, Inspection Scheduled, etc.) gets dated
  relative to the day the wizard was run. Run the same preview tomorrow and the
  dates shift. Testers will see non-deterministic previews.
- **Fix:** Treat a missing contract-acceptance date the same as a missing
  closing date: leave contract-anchored tasks **undated** and attach the warning
  "No contract acceptance date set; this deadline can't be scheduled yet."
  Remove the `or date.today()` fallback. Surface it in the `undated` summary.

### C3. Missing day-offset fields silently collapse a deadline onto its anchor

- **Where:** `resolve_float_days` returns `0.0` (with only a `logger.warning`)
  when a `wizard:<field>` reference points at an unset value
  ([dependency_engine.py:70-76](../velvet-elves-backend/app/services/dependency_engine.py#L70)).
- **Effect on specific, high-stakes deadlines:**
  - **Inspection Response Reminder** (240/245) uses
    `float = wizard:inspection_response_days`. If the wizard did not capture
    `inspection_response_days`, the reminder lands on the **contract-acceptance
    day** instead of "N days after acceptance." Missing the inspection response
    deadline can terminate a deal.
  - **Insurance Reminder** (200) uses `wizard:insurance_commitment_days`; same
    collapse.
  - **Deliver HOA Docs** (110/115) uses `wizard:hoa_doc_days`; same collapse.
  - Note `has_inspection` defaults **True** ([transaction.py:51](../velvet-elves-backend/app/models/transaction.py#L51))
    while `inspection_days` / `inspection_response_days` default `None`, so the
    default financed-buyer deal generates inspection tasks but mis-dates the
    response reminder. This is the most likely real-world misfire.
- **Effect on the user:** No warning. The task shows a confident (wrong) date,
  and it is counted as "dated," so it does not even show up in the `undated`
  tally.
- **Fix:**
  1. When a `wizard:` offset resolves to `None`, mark the task with a warning
     ("Deadline depends on a value that isn't set yet") instead of silently
     using 0, mirroring the dependency-None path.
  2. Give these offset fields tenant-configurable **defaults** (most contracts
     use standard windows, e.g. 10-day inspection, 5-day response). A default is
     better than a silent zero.
  3. In the wizard, when `has_inspection` is true, require `inspection_days` and
     `inspection_response_days` (or prefill from contract parsing).

---

## 3. High-severity findings (workflow & onboarding)

### H1. Tenants cannot author their own legacy task list faithfully

This is the most important strategic finding, because it is exactly what
Audri's team is about to do.

- **Create path is missing fields.** `TaskTemplateCreateRequest`
  ([schemas/task_template.py:11-27](../velvet-elves-backend/app/schemas/task_template.py#L11))
  and `TaskTemplateRepository.create`
  ([task_template_repository.py:121-185](../velvet-elves-backend/app/repositories/task_template_repository.py#L121))
  do **not** accept `task_family`, `dual_agency_behavior`, `dep_task_ids`, or
  `day_basis`. Yet the **update** schema does
  ([schemas/task_template.py:44-47](../velvet-elves-backend/app/schemas/task_template.py#L44)).
  So a tenant-created template is born unable to participate in dual-agency
  consolidation or multi-predecessor maturity, and only a second PUT can fix it.
- **CSV import is lossy and brittle.** The importer
  ([task_templates.py:392-438](../velvet-elves-backend/app/api/v1/task_templates.py#L392))
  guesses `both_rep_behavior` and conditions from **English notes** via
  substring matching, never sets `task_family` / `dual_agency_behavior` /
  `dep_task_ids` / `day_basis`, does not parse the `title_ordered_by` /
  `warranty_ordered_by` conditions at all, and **hardcodes
  `automation_level="Manual"`** regardless of the CSV. In other words, importing
  the brokerage's own `REWORKING_TASK_DB.csv`-style file produces a **degraded**
  engine: no consolidation, no multi-predecessor, fragile conditions.
- **Why it matters:** The system's whole value proposition for a new brokerage
  is "bring your task list." Today, the seed library (`tenant_id IS NULL`) is
  the only first-class citizen, because it was hand-finished by a migration
  (`20260605_task_engine_fix.sql`) that the authoring UI cannot reproduce.
- **Fix:**
  1. Add `task_family`, `dual_agency_behavior`, `dep_task_ids`, `day_basis`,
     `conditions_json` to the **create** schema and `repo.create`, reaching
     parity with update. (Small, mechanical, high value.)
  2. Replace the note-scraping CSV importer with a **structured importer** that
     reads explicit columns (condition, family, dual-agency role, day basis,
     predecessors), or a guided mapping UI. Treat the English-note inference as
     a fallback suggestion the admin confirms, not the source of truth.
  3. Add a **template-library linter**: warn on orphan dependencies (a
     `dep_task_id` with no matching `legacy_task_id`), families with two
     `consolidated` rows, conditions referencing unknown fields, and
     unparseable `float_days`.

### H2. State rules are effectively inert

- **Where:** `apply_state_rules` decides attorney-vs-title by **substring on the
  task name** (`"attorney" in name_lower`, `"title company" in name_lower`)
  ([state_rules.py:92-112](../velvet-elves-backend/app/services/state_rules.py#L92)).
- **Reality:** The seed library has **no** task whose name contains "attorney"
  or "title company," so the rule only ever *removes* nothing and *adds*
  nothing. Attorney-closing states (NY, GA, SC, etc., listed in
  [state_rules.py:24](../velvet-elves-backend/app/services/state_rules.py#L24))
  get the same Indiana title-company workflow. The layer advertises
  state-awareness that is not actually delivered.
- **Why it matters:** The product is multi-tenant and multi-state. The first
  attorney-state brokerage will find no attorney review task, no attorney-ordered
  title task, and incorrect closing tasks.
- **Fix:** Drive state behavior off **structured data**, not names: a
  `closing_entity` / `required_in_states` tag on templates, plus a small set of
  attorney-state tasks in the library. Either build the attorney workflow into
  the seed or stop presenting state rules as functional until it exists. At
  minimum, document the current limitation.

### H3. Use-case switch is fragile and leaves stale dates

- **Where:** `switch_use_case_tasks`
  ([task_generation_service.py:468-558](../velvet-elves-backend/app/services/task_generation_service.py#L468))
  decides what to preserve/remove by **task name** membership
  (`task.name not in new_template_names`, line 516). Many tasks share a name
  across use cases ("Request HOA Docs," "Inspection Scheduled," "Deliver Title,"
  "Internal Thank You"), so name matching mis-preserves or mis-removes. It also
  only computes dates for **newly added** tasks; **surviving** tasks keep their
  old dates even though the use case (and possibly the relevant offsets) changed.
- **Fix:** Match on `template_id` (stable), not name. After a switch, run the
  same date recompute used by `recompute_task_dates` over the survivors so the
  whole list is internally consistent.

---

## 4. Medium-severity findings

### M1. User-added deadlines do not recompute on date changes

`recompute_task_dates` only touches rows that have a `template_id`
([task_generation_service.py:600-601](../velvet-elves-backend/app/services/task_generation_service.py#L600)).
Manual deadlines and AI-added tasks (created with `source="manual"`/`"ai"` and a
relative `basis` in `metadata_json`) are skipped. So when an addendum moves the
closing date, a user-added "10 days before closing" deadline does **not** move.
**Fix:** When recomputing, also resolve any task whose `metadata_json.basis` is
present, using `resolve_added_task_basis` against the new dates.

### M2. Business-day deadlines are not modeled in the data

The engine supports `day_basis='business'`
([dependency_engine.py:121-126](../velvet-elves-backend/app/services/dependency_engine.py#L121)),
but `20260605_task_engine_fix.sql` sets **every** seed row to `'calendar'`. Many
purchase agreements express inspection/response windows in *business* days.
Today those are computed as calendar days and then merely rolled forward, which
is not the same number of days. **Fix:** Audit the legacy windows with Jake and
set `day_basis='business'` on the rows whose contract language is business-day
based.

### M3. Cash-deal appraisal inconsistency in the seed

"Appraisal Ordered" (265) is scoped to `Buy-Cash, Sell-Cash`, but "Appraisal
Completed" (270) is `Buy-Fin, Sell-Fin` only
([seed:102-103](../velvet-elves-backend/supabase/migrations/202603111730_seed_task_templates.sql#L102)).
A cash deal therefore gets a task to order/confirm an appraisal but never one to
confirm completion. Either cash deals should have both or neither. **Fix:**
confirm the intended cash-appraisal policy with Jake and align the two rows.

---

## 5. Low-severity / polish

- **L1. No partial-failure recovery for `generate`.** Any existing task makes
  `generate` return 409
  ([transactions.py:1316-1320](../velvet-elves-backend/app/api/v1/transactions.py#L1316)).
  The wizard commit sequence is create -> bulk requirements -> generate; if
  generate half-fails, the user cannot cleanly re-run. Consider an idempotency
  key on generate (like the bulk-requirements `commit_id`) plus a "regenerate"
  affordance.
- **Preview determinism for testers.** Because of C2, previews drift day to day
  when the contract date is absent. Fixing C2 also fixes this.
- **`evaluate_conditions` "unset -> exclude" is a good rule, but undiscoverable.**
  When a whole family is excluded purely because a field was unset (title, HOA,
  warranty), the Review step shows nothing at all for it. A small "X tasks were
  excluded because these questions are unanswered: ..." affordance would make
  the silent exclusions visible (and prevent C1 in practice).

---

## 6. Practical-utility assessment for real estate professionals

**Where it already helps a TC/agent:**
- One pass from contract upload to a dated, role-assigned, deduplicated task
  list is a real time saver, and the "why is this here / why this date"
  transparency builds the trust a TC needs to rely on it.
- Dual agency, the historically error-prone case, is handled correctly.

**Where it will hurt them today:**
- The three Critical findings all share one failure mode: a confident but wrong
  list with no signal that anything is off. A TC who trusts the output (the
  whole point) is exposed on title (C1) and on the inspection-response and other
  date-driven deadlines (C2/C3). For this audience, a silently wrong deadline is
  the worst possible defect.
- A brokerage onboarding its own task list (H1) will not get the engine the seed
  library gets, so the product will feel "dumber" for exactly the customers we
  are trying to win, and will quietly diverge from how that brokerage actually
  works.

**Net:** The foundation is strong and the design instincts are right. It is not
"perfect," and the gap to perfect is concentrated in input validation,
authoring parity, and honest handling of missing data, not in the core
algorithm.

---

## 7. Recommended remediation plan (in priority order)

**Phase 1 — Stop the silent wrong output (the Critical three).**
1. C2: remove the `today()` fallback; warn + leave undated when contract
   acceptance is missing (symmetry with closing).
2. C3: warn + leave undated when a `wizard:` offset is unset; add
   tenant-default windows; require inspection days when `has_inspection`.
3. C1: require `title_ordered_by`; add a "no title task generated" safety
   warning.
   *Each is small, local, and independently shippable. Add a regression test per
   item asserting the warning fires and the date is not fabricated.*

**Phase 2 — Authoring parity for onboarding (H1).**
4. Bring create-template to parity with update (family, dual-agency, dep_task_ids,
   day_basis, conditions).
5. Replace/augment the CSV importer with a structured import + a library linter.
   *This is the work that de-risks Audri's legacy-list implementation.*

**Phase 3 — Correctness of the secondary flows.**
6. H3: switch use case by `template_id` and re-date survivors.
7. M1: recompute user-added relative deadlines on date changes.

**Phase 4 — State and business-day fidelity.**
8. H2: structured state rules + attorney-state tasks (or document the limit).
9. M2/M3: audit business-day windows and the cash-appraisal policy with Jake.

**Cross-cutting test additions:**
- A fixture matrix over the 6 use cases x {HOA on/off, inspection on/off,
  title us/them, warranty us/them/none, attorney/title closing} asserting the
  expected task set and that **no** task is silently mis-dated.
- A "missing-input" suite: omit contract date, closing date, each offset, and
  `title_ordered_by`, and assert a warning is produced every time.

---

## 8. Bottom line

The engine is a solid, well-reasoned piece of work, and the dual-agency core in
particular is correct. It is **not** complete. The path to "the most perfect and
excellent" version runs through three things, in order: (1) make missing or
unanswered inputs **loud** instead of silent, (2) give tenants authoring parity
so their real task lists onboard without losing fidelity, and (3) make the
state/business-day claims real or scope them honestly. Phase 1 is small and
should be done before the legacy-list rollout, because it is the difference
between a tool a TC can trust and one that occasionally hands them a confident,
wrong deadline.

---

## 9. Addendum — Confirmed defects from client UI testing (2026-06-22/23)

The tester ran the New Transaction wizard against a real Indiana packet and
reported four problems. I reproduced each in code. Importantly, these live in
the **parsing-and-review front half** of the wizard (how extracted values and
documents are presented), which is *distinct from* the task-generation engine my
sections 1-8 cover. Together they are the full picture: the engine has
silent-**wrong-output** bugs; the review layer has **false-negative / false-
positive** bugs that erode trust before the user even reaches task generation.

| # | Severity | Tester words | Root cause (verified) |
|---|---|---|---|
| T1 | High | "When clicking 'View in doc' it does nothing" / "says it found it but won't show the page" | Citation viewer cannot resolve which document a value came from once more than one file is uploaded |
| T2 | Medium | "It says it couldn't find it, but gives info on where it is" | A found-with-citation value is still labeled "needs review / couldn't find" because of a high visual-field confidence threshold |
| T3 | High | "Why does this appear? They are uploaded" (5 referenced documents not uploaded) | Missing-reference detector matches on exact date/sequence with no "family already present" guard and no self-reference exclusion |
| T4 | Medium | "Again, it's asking me for info I've already provided" | The two-pass double-check flags values that differ only in formatting (short vs full address) as disagreements |

### T1. "View in Document" does nothing once a packet is uploaded

- **Root cause:** `selectEvidence` hardcodes the target as `documentId:
  singleDocId`
  ([NewTransactionWizard.tsx:4045-4058](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L4045)),
  and `singleDocId` is **null whenever more than one document is uploaded**
  ([:4038-4041](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L4038)).
  The `CitedField` type carries no per-document id at all
  ([wizardTypes.ts:278-286](../velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L278)).
  So with a packet (purchase agreement + counters + disclosures, the normal
  case), the evidence viewer treats every citation as "ambiguous document" and
  abandons the precise page jump for a fuzzy OCR **text-locate**
  ([WizardEvidenceViewer.tsx:271-353](../velvet-elves-frontend/src/components/wizard/WizardEvidenceViewer.tsx#L271)).
  That locate fails for formatted values (a date like "06/21/2026" rarely
  OCR-matches verbatim), so the page never shows. Earnest money worked because
  "$1,500" / "1500" happens to text-match.
- **The code already admits this:** the comment at
  [:4034-4037](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L4034)
  calls true per-document attribution "a later phase." The tester just hit that
  gap. And the backend already has the data: resolution carries
  `source_document_id` per field
  ([contract_resolution.py:701](../velvet-elves-backend/app/services/contract_resolution.py#L701)),
  and the parse pipeline already passes `citation.document_id` in places
  ([NewTransactionWizard.tsx:3756](../velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx#L3756)).
- **Fix:** thread `documentId` through the citation end to end: add it to
  `CitedField`, populate it from the per-field `source_document_id`, and have
  `selectEvidence` pass `f.documentId` instead of `singleDocId`. Then the
  viewer's existing `knownDoc` branch
  ([WizardEvidenceViewer.tsx:273-277](../velvet-elves-frontend/src/components/wizard/WizardEvidenceViewer.tsx#L273))
  jumps straight to the right document and page. This is the single highest-value
  fix in this addendum: "View in Document" is the feature that makes the AI
  trustworthy, and it is broken in the most common (multi-file) case.

### T2. "Couldn't find it, but shows where it is"

- **Root cause:** `title_ordered_by` (and the other layout-dependent fields) sit
  in `LOWER_CONFIDENCE_FOR_VISUAL_FIELDS`
  ([contract_resolution.py:107-116](../velvet-elves-backend/app/services/contract_resolution.py#L107))
  and the auto-accept threshold is **0.90**
  ([contract_resolution.py:28](../velvet-elves-backend/app/services/contract_resolution.py#L28)).
  In the screenshot the value was found at 87% **with** a page+snippet citation,
  but because 0.87 < 0.90 it is marked `needs_review`, so the UI says "couldn't
  find / verify this" while simultaneously rendering the exact source. The copy
  conflates "no value found" with "found but below the auto-accept bar."
- **Fix:** branch the messaging on *whether a citation exists*, not on
  `needs_review` alone. With a citation: "Found on page N — please confirm."
  Without any candidate: "Couldn't find this; please enter it." Never show
  "couldn't find" next to a populated value and a source link.

### T3. False "5 referenced documents not uploaded"

- **Root cause:** `_detect_missing_referenced_documents`
  ([contract_resolution.py:919-991](../velvet-elves-backend/app/services/contract_resolution.py#L919))
  flags a referenced document unless it finds an exact `(family, sequence)` or an
  exact `document_effective_at` **date-prefix** match
  ([:947-957](../velvet-elves-backend/app/services/contract_resolution.py#L947)).
  Two gaps make it cry wolf:
  1. **No self / family-presence guard.** The uploaded purchase agreement's
     effective date (acceptance, 2026-06-21, or null) does not equal the date it
     and the other documents *cite* ("dated 2026-06-20", the offer date), so the
     PA that is sitting in the viewer is flagged as missing, and
     "purchase_agreement references purchase_agreement" flags the file against
     itself.
  2. **Date semantics are noisy** (offer date vs acceptance date vs effective
     date), so date-prefix equality is the wrong test.
- **Why it matters:** This is exactly the tester's confusion ("they are uploaded,
  they're on the right"). False missing-doc alarms train users to ignore the
  panel, which defeats its purpose when a document really is missing.
- **Fix:** before flagging, (a) skip a reference whose family matches a document
  already in the inventory unless a *specific* sequence number is provably
  missing; (b) never flag a document against its own family when it is the only
  member; (c) treat date as corroborating evidence, not the primary key. Flag
  only genuine gaps (a counter #2 with no counter #1, a referenced family with
  zero uploads of that family).

### T4. "Asking for info I've already provided"

- **Primary root cause (the double-check panel):** the two-pass agreement check
  marks any field where the two reads are not byte-identical
  ([WizardDoubleCheckPanel.tsx:40-94](../velvet-elves-frontend/src/components/wizard/WizardDoubleCheckPanel.tsx#L40)).
  In the screenshot the two reads were "603 Yandes St" and "603 Yandes St,
  Franklin, IN 46131" — the **same** address at different granularity — yet it
  asked the user to verify. The comparison is naive string inequality, so
  formatting/granularity differences become fake disagreements.
- **Fix:** normalize before comparing — trim and case-fold; compare dates by
  parsed value and numbers by numeric value; for addresses/names treat one value
  being a superset of the other as agreement. Only surface a *semantic* conflict.
- **Secondary (lower priority):** the Compliance step re-presents the
  already-confirmed property address as a fresh prompt. Show confirmed values as
  read-only context ("from your contract") instead of re-asking.

### Where these fit in the plan

T1 and T3 are the trust-breakers the tester actually felt and should join
**Phase 1** alongside the Critical engine fixes. T2 and T4 are copy/normalization
fixes that are cheap and can ride along. None of them require Jake's input; they
are correctness and wording, not policy. I can turn this addendum plus Phase 1
of section 7 into a single implementation plan on request.
