# Transaction Processing Workflow (as implemented)

**Date:** 2026-07-09
**Scope:** The end-to-end transaction processing workflow as it exists in the current `velvet-elves-backend` and `velvet-elves-frontend` source, from document intake through deal creation, task generation, and ongoing workspace processing.
**Method:** Traced directly from source. Every behavior below was read out of the actual code (API routers, services, the wizard component, and its hooks), not from prior design docs. File paths and function names are cited so each claim is verifiable.

---

## 1. Overview

A "transaction" is a single real-estate deal. Processing it has three real stages in the code:

1. **Intake** — the New Transaction "AI Wizard" collects documents, runs a multi-pass AI extraction, and lets the user confirm the deal facts, timeline, and compliance checklist.
2. **Commit** — a create call persists the transaction, its parties, its documents, its compliance checklist, and (deterministically, from the template library) its full task plan.
3. **Ongoing processing** — the Transaction Workspace, driven by a single zero-LLM aggregate endpoint, where tasks are worked, deadlines cascade off contract changes, documents are matched against the checklist, and (optionally) an AI agent proposes next actions.

The guiding invariant across all three: **preview equals commit.** The same deterministic planner produces the wizard's previews and the committed rows, so what the user reviews is exactly what gets saved. The LLM only proposes; deterministic code decides dates and what is created.

```
UPLOAD ─▶ AI PARSE (OCR → extract → double-check → intake intelligence)
            │
            ├─(ship-it tier)─▶ AUTOPILOT ─▶ CONFIRM ─▶ CREATE
            │
            └─(normal)─▶ ADDRESS & CONTACTS ─▶ PURCHASE INFO ─▶ MISSING INFO
                          ─▶ CONFIRM (facts + timeline) ─▶ DOCUMENTS (compliance checklist)
                          ─▶ CREATE
                                 │
                                 ▼
                          TRANSACTION (Active) + tasks + requirements + parties + docs
                                 │
                                 ▼
                          TRANSACTION WORKSPACE
                          (Timeline · Compliance · Documents · Tasks · People · Activity · Email · Agent)
```

---

## 2. Domain model

Defined in `velvet-elves-backend/app/models/`.

### 2.1 Transaction (`models/transaction.py`)

Key fields the workflow reads and writes:

- **Identity / ownership:** `id`, `tenant_id`, `created_by`, `user_id` (the owner).
- **Type:** `use_case` (one of six: `Buy-Fin`, `Buy-Cash`, `Sell-Fin`, `Sell-Cash`, `Both-Fin`, `Both-Cash`), `financing_type`, `representation_type` (Buyer / Seller / Both).
- **Status:** `Active`, `Incomplete`, `Paused`, `Completed`, `Closed`.
- **Property (PII, encrypted at rest):** `address`, `city`, `state`, `zip_code`, `county`.
- **Money:** `purchase_price`, `earnest_money`.
- **Core dates:** `contract_acceptance_date`, `closing_date`, `closing_time`, `possession_date`, `possession_time`.
- **Operational tracking dates** (recorded during the deal, not at intake): `em_delivered_date`, `inspection_response_date`, `appraisal_expected_date`, `cd_delivered_date`, `cleared_to_close_date`.
- **Contingency terms:** `has_inspection` + `inspection_days` / `inspection_response_days`, `has_hoa` + `hoa_doc_days`, `has_home_warranty` + `warranty_ordered_by`, `title_ordered_by`, `insurance_commitment_days`.
- **Cash-deal appraisal election** (`has_appraisal`, tri-state): `True` = buyer elected an appraisal, `False` = waived, `None` = unanswered (no appraisal tasks; the workspace prompts). Not consulted on financed deals.
- **Per-deadline counting basis** (`deadline_day_basis_json`): a map of term-field to `calendar` or `business`, read from the contract, present only for deadlines whose basis the contract states. Absent means calendar.
- **Closing mode / attorney review:** `closing_mode` (`attorney` / `title_escrow` / `shared_approval`), `contract_prepared_by_licensee`, `contracts_delivered_date`, `attorney_review_json` (used for statutory review clocks such as NJ's 3-business-day rule).
- **FSBO:** `is_fsbo`, `fsbo_state` (`listing_prep` / `under_contract`).
- **Misc:** `notes`, `wizard_completed`, `metadata_json`.

### 2.2 Task (`models/task.py`)

A transaction-specific task instance: `name`, `transaction_id`, `automation_level` (`Automated` / `ToBeAutomated` / `AIAssisted` / `Manual`), `status` (`Pending` / `InProgress` / `Completed` / `Blocked` / `Skipped`), `template_id` (null for manual/AI tasks), `due_date`, `float_days`, `dep_rel` (`FS` finish-start or `SS` start-start), `dependencies_json`, `target` / `cc_targets`, `milestone_label`, `completion_method`, `assigned_to` (a user id or `ai_agent`), and provenance (`source` = `template` / `ai` / `manual`, plus `ai_reason` / `ai_confidence`).

### 2.3 Supporting entities

`transaction_party` (buyers, sellers, agents, lender, title, attorney), `document` and `document_requirement` (the compliance checklist rows), `task_template` and its requirement-template counterpart (the master libraries), `transaction_assignment` (staffing), and `audit_log` (history).

---

## 3. Stage 1 — Intake: the AI Wizard

Frontend: `velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx` (~10.5k lines), its types (`wizardTypes.ts`), the contact-fill helper (`wizardContactFill.ts`), and the API hooks (`src/hooks/useWizardApi.ts`).

### 3.1 Step machine and public phases

The internal step machine (`wizardTypes.ts`, `WizardStep`) has these states: `upload`, `parsing`, `address`, `purchase`, `missing`, `confirm`, `timeline`, `checklist`, `review`.

Only these are **navigable** (`WIZARD_STEPS`): `upload`, `address`, `purchase`, `missing`, `confirm`, `checklist`.

- `parsing` is a **transient** auto-advancing progress screen. It is entered only by an explicit `set_step('parsing')` when the user starts extraction, and it auto-advances to `address` (or `confirm` under Autopilot) the moment the parse resolves. It is deliberately kept out of `WIZARD_STEPS` so Back and the stepper can never re-show a finished extraction screen.
- `timeline` folded into Confirm; `review` (the per-task preview) folded into Documents. Both remain valid step values with live renderers but are unreachable by next/prev navigation.

For the top stepper, steps are grouped into **three public phases** (`WIZARD_PHASES`): **Upload**, **Review details** (`address`, `purchase`, `missing`, `confirm`, `timeline`), and **Documents** (`checklist`, `review`). Testers think in phases; back-navigation still walks the internal steps.

### 3.2 Upload step

Gates on the representation choice, then accepts drag/drop or file-input uploads. Each file is uploaded via `POST /api/v1/documents/upload` (`useWizardUploadDocument`) with a null `transaction_id` (the transaction does not exist yet). Per-file status is shown, a multi-page PDF can be split into separate documents (`useDocumentPages` / `useSplitDocument`), and there is a manual-entry escape hatch (skip AI, enter details by hand).

### 3.3 AI parsing pipeline

Triggered by `runParsing` (`NewTransactionWizard.tsx:3653`), which posts every uploaded document id to `POST /api/v1/ai/parse-document-packet` and polls `.../status` for a streamed progress feed plus the final result (`useParseDocumentPacket`, `useWizardApi.ts:157`). The whole packet is parsed as one unit so counteroffers and amendments resolve against the base agreement.

The backend pipeline is `run_packet_parsing_pipeline` in `services/document_packet_parsing.py`. It runs in stages, each reporting progress to the live wizard timeline:

1. **OCR (`ocr` stage).** Every PDF/image is read with Amazon Textract (`services/textract_service.py`), concurrency-limited. The mode is settings-driven: with `TEXTRACT_OCR_ONLY_MODE=false` the pipeline uses document analysis with FORMS + SIGNATURES so Textract's `[X]`/`[ ]` checkbox and key-value markers reach the model (critical for "who orders title", financing type, owner-occupancy, and other checked-box decisions). All page text is concatenated into one delimited packet (`build_packet_ocr_text`), each document tagged with id, filename, mime type, and page count.

2. **Extraction, pass 1 (`extract` stage).** `extract_packet_with_pydantic_ai` runs a pydantic-ai `Agent` against a strict schema (`PacketExtractionPayload`: property, transaction, timeline, parties, detection, sources, confidence, quality_issues, documents). The instructions (`PACKET_EXTRACTION_INSTRUCTIONS`) encode the real-estate rules: later accepted counters/amendments override only the fields they change; blank/N/A/unchecked sections are **negative** answers (do not fabricate contingencies); a tax/assessor/deed record names the seller/owner of record and must never source a buyer; read the CHECKED box, never the first-listed option; search every page for deadline day counts; and a Removal of Contingency notice moves `contract_acceptance_date` to the removal's effective date. The model returns per-field `sources` (dotted path → document id, page, OCR snippet) and per-field `confidence`. A live "what the AI found" event is reported per populated key field (`field_found_pairs`).

3. **Provider selection.** `_build_pydantic_ai_model` picks Anthropic or OpenAI strictly from the tenant/admin-configured provider (`settings.ai_provider`); there is no silent fallback.

4. **Double-check, pass 2 (`verify` stage).** `verify_critical_fields_with_pydantic_ai` re-reads the same packet **independently** with a different (verification) prompt and a narrower schema (`CriticalFieldsVerification`): address, price, closing date, acceptance date, buyer names, seller names, all-parties-signed, document type. `build_double_check` compares pass 1 and pass 2 field-by-field with type-aware equality (date normalization, price tolerance, surname-set match for parties, subset match for addresses). Any disagreement is recorded and **forces the parse into human review** (§3.4 requirement), so a single-pass answer can never silently ship. This is advisory and non-fatal: a verification failure never breaks the primary parse.

5. **Intake Intelligence (`intelligence` stage).** `generate_intake_intelligence_with_pydantic_ai` (`services/intake_intelligence.py`) asks the LLM for only what the standard deterministic plan cannot know: deal-specific `timeline` deadlines/contingencies, `checklist` documents (or waivers of standard docs), coordination `tasks`, and `watchouts`. Crucially, it emits **proposals carrying rules + citations + confidence, never resolved dates.** Then `verify_intake_intelligence` deterministically pins each proposal to real evidence: every citation must locate in the persisted OCR geometry (`services/citation_check.locate_snippet`); a dead citation demotes the item (or drops a watchout entirely); absolute dates must fall in a sane window bracketing acceptance/closing; rules must reference a canonical anchor; a proposal that duplicates a deterministic-floor row merges into it (donating its citation) unless it carries a different value, which becomes a **blocking conflict**. Items come back tagged `verified`, `needs_review`, `conflict`, or `merged`. Also advisory: on failure the wizard runs "floor only" with an honest banner.

The result carries the extraction, the per-field citations, `needs_human_review` + `review_reasons`, the `double_check` block, and the verified `generated` proposals. The frontend applies the extraction to wizard state (`apply_extraction`), builds evidence citations, stores the double-check and signature status, and (for multi-document packets) calls `POST /api/v1/ai/resolve-documents` to flag controlling-vs-superseded conflicts and missing-document reasons as advisory "verify this" flags.

### 3.4 Autopilot routing

After a clean parse, `autopilotEligibleFromResult` checks whether the extraction cleared the tenant's "ship-it" confidence tier on every front and all parties signed. If so, `enable_autopilot` compresses the journey straight to the **Confirm** hub; the required actions shrink to confirming the anchor dates and giving final approval. Ship-it-tier AI proposals are pre-accepted; everything else surfaces for one-click review. Otherwise the wizard advances to Address & Contacts for the normal review path.

### 3.5 Address & Contacts (`address`)

Shows the extracted property address and the party cards (buyers, sellers, listing/buyer agents, loan officer, title company, closing attorney), each with its own citation "find" affordance. The street field is presented as an autocomplete, but Google Places is currently gated off by a hard-coded constant and no key is provisioned, so the dropdown is fed only by the user's recent addresses (empty for a first-run tenant). The four sub-fields (city/state/zip/county) are always manually editable.

### 3.6 Purchase Info (`purchase`)

Every deal-shaping field: price, earnest money, financing type, representation, contract acceptance/closing/possession dates and times, and the contingency terms. Day-count and date fields for contingencies stay in sync (editing "14 days" recomputes the date and vice-versa). Cash deals surface the appraisal election. FSBO can be marked here (only when representing the Buyer). Custom contingencies and a pinned free-text note are supported.

### 3.7 Missing Info (`missing`)

Lists fields `detectMissingFields` found blank. Fixed-choice decisions (who orders title, cash appraisal) render as one-click choice rows that write the answer straight to state. Every other missing field renders a free-text input. (There is an "AI Search" affordance on these rows wired to `POST /api/v1/ai/search-public-source`, but that backend method is a deliberate stub that always returns an empty list, so only manual entry and the one-click choices actually resolve values today.)

### 3.8 Confirm (`confirm`)

The review hub. Renders review tables with per-value "jump to source" (the citation viewer with OCR-geometry highlighting, `WizardEvidenceViewer`), packet-level confidence, the double-check panel (`WizardDoubleCheckPanel`), AI-found deadline proposals with accept/dismiss, the deal-brief watch-outs, the Autopilot hub, and a signature decision: when the AI flagged the document as **not** fully signed, the user may choose "Queue e-signature" (offered only if an e-sign provider is connected). The Timeline review folded into this step, so confirming the anchor dates here previews every derived deadline via the deterministic planner.

### 3.9 Documents / Compliance checklist (`checklist`)

The wizard previews the compliance document checklist via `POST /api/v1/transactions/preview-tasks` (which returns tasks, the timeline, and requirements together) and lets the user match uploaded supporting documents to requirement rows, waive rows, add rows, or import their own checklist (`POST /api/v1/ai/parse-checklist`, `ChecklistImportModal`). Accepted AI checklist proposals ride the same `extra_requirements` channel. Creation happens straight from this step; the full task plan still generates at commit.

### 3.10 Command bar and draft persistence

A natural-language command bar (`WizardCommandBar`) classifies intent through `POST /api/v1/ai/wizard-command` (`parse_wizard_command`) and applies deterministic preview-apply-undo edits.

Drafts persist two ways: a local draft (auto-saved) and a **server-side** draft (`GET/PUT/DELETE /api/v1/wizard-runs/current`) for cross-device resume. A restored draft is coerced back onto a navigable step (`coerceNavigableStep`) so it never lands on a transient/dead step. The user can also explicitly "Save draft," which creates an `Incomplete` transaction shell (parties + linked documents, but **no** tasks) and exits.

---

## 4. Stage 2 — Commit: creating the transaction

The wizard's `submit` (`NewTransactionWizard.tsx:3921`) is the commit orchestrator. It runs a precise, defensively-coded sequence:

1. **Guard + payload.** Requires at least one persisted document, builds the create payload from wizard state.

2. **Create the transaction** — `POST /api/v1/transactions` (`create_transaction`, `transactions.py:172`):
   - **Credit spend gate.** When billing is enabled (DB-backed `platform_settings`), creating a deal costs one credit. The order is: pre-check balance (fast `402 PaymentRequired` on an empty wallet, carrying the fee display), create the row, then an authoritative idempotent debit (`CreditWalletService.spend_for_transaction`). On the rare lost race, the just-created row is compensate-deleted so a failed create never costs a credit. Platform admins are exempt. This is the **only** credit-consumption point in the system.
   - **Ownership + staffing.** Owner defaults to the caller; Admin / Team Lead / TC may delegate via `owner_user_id` (`_resolve_owner_user_id`). The owner is recorded as a `primary_agent` assignment (this drives the card assignee and the Assign Team roster); on delegation the creator also gets a distinct assignment so the deal stays in their queue. Assignment failures are non-fatal.
   - Writes an audit `create` event.
   - Note: **the create endpoint does not generate tasks.** Task generation is a separate, explicit call (step 8), so an `Incomplete` draft can be saved without a plan.

3. **Pinned note** (optional) — a `note` communication-log entry, pinned to the top of history.

4. **Persist parties** — every buyer/seller/agent/lender/title/attorney as a `transaction_party` (`POST /transactions/{id}/parties`). Non-fatal per party.

5. **FSBO invite** — if the deal is FSBO and represents the Buyer and a seller email was given, the seller is captured as a party **and** sent a transaction-scoped invitation (`POST /api/v1/invitations/`, role `ForSaleByOwner`). The deal stays the creator's; accepting the invite creates the `for_sale_by_owner` assignment the FSBO portal reads. Best-effort.

6. **Save service-provider vendors** (optional prompt) — inspector/appraiser/title/etc. parties can be saved to the tenant-wide vendor directory in one click (the "save once, reuse forever" bridge).

7. **Link documents** — every wizard document (parse targets plus checklist supporting uploads) is PATCHed with the new `transaction_id`. Only linked documents may later match a requirement.

8. **Commit the compliance checklist** — the wizard re-runs the server planner (`previewForCommit`) with the confirmed `extra_deadlines`, `extra_requirements` (including accepted AI rows with citations), and `requirement_overrides`, then **bulk-inserts the confirmed requirement rows BEFORE task generation** (`POST /transactions/{id}/document-requirements/bulk`, idempotent on a client `commit_id`). Removed rows commit as **waived** (nothing disappears silently). This returns a `client_key → requirement_id` map so tasks can reference real ids. Failure is non-fatal: the transaction and tasks still land, and the default-checklist hook fills in library defaults.

9. **Conditional e-signature** — only when the AI flagged the document as not fully signed **and** the user chose "Queue e-signature" **and** a provider is connected: buyers/sellers with emails are sent the first linked document for signature (`sendEsign`). Non-fatal.

10. **Generate tasks** — `POST /api/v1/transactions/{id}/tasks/generate` (step 5 of §5). The wizard passes excluded template ids, per-task overrides, and added tasks (custom deadlines as `kind:'deadline'`, accepted AI timeline rows as deadline tasks with evidence, accepted AI task proposals with their rule and resolved related-requirement key), plus the requirement id map. This is the deterministic engine (see §5). Non-fatal but surfaced as an error if it fails post-create.

11. **Persist brief watch-outs** — accepted AI watch-outs are stored with citations (`PUT /transactions/{id}/brief`) so the workspace can show "why does this exist" for the life of the deal.

12. **Finish** — refresh views, clear both drafts, navigate to the new deal. If the create hit a `402`, the in-progress deal is already a server draft and the wizard shows a calm in-flow paywall; paying redirects to Stripe and returns to finish the exact commit.

---

## 5. The deterministic task-generation engine

This is the heart of "processing." It has **no AI creativity** — it is strictly template-driven, and the exact same code produces the wizard's preview and the committed tasks. Entry points: `preview_tasks_for_transaction` (dry-run, no writes) and `generate_tasks_for_transaction` (persist), both in `services/task_generation_service.py`, sharing the pure `plan_tasks_for_transaction`.

The pipeline (`plan_tasks_for_transaction`):

1. **Load templates by use case.** `_list_templates_for_generation` fetches the tenant's task templates for the use case. A `Both-*` deal assembles from the matching Buy + Sell sets, deduplicated by template id.

2. **Evaluate conditions** (`dependency_engine.evaluate_conditions`). Each template carries `conditions_json` (AND-logic predicates like `{"field":"has_hoa","value":true}` or `{"field":"title_responsibility","op":"ne","value":"us"}`). A condition on a field that is **unset** on the transaction excludes the task (never guessed). "Derived" virtual fields are computed first (`build_derived_condition_values`): the contract-literal ordering side ("Buyer"/"Seller") is translated by `title_responsibility` / `warranty_responsibility` into `us` / `counterparty` using side × representation, so a Buy-side deal where the Buyer orders title fires "Order Title" while a Sell-side deal fires "Confirm Title Order." State workflow flags are merged in here too, so statutory attorney tasks fire only in verified states.

3. **Dual-agency filtering** (`filter_both_representation`). For `Both-*` (dual agency) deals, `consolidated` rows replace their `standard` siblings, `suppressed` rows are dropped (e.g. "Co-op Agent Welcome" has no dual-agency equivalent). A final de-dupe by `(family, target)` guarantees one instance per recipient.

4. **State rules** (`state_rules.apply_state_rules`) apply state-specific additions/removals.

5. **Date math** (`dependency_engine.calculate_due_dates`). The two anchors are `contract_acceptance_date` (anchor id 5) and `closing_date` (anchor id 1000), seeded directly from the transaction. Templates with no dependency resolve off an absolute wizard date (e.g. `wizard:closing_date`) or off acceptance + `float_days`; dependent templates resolve iteratively, maturing off the **latest** of their resolved predecessors. `float_days` can be a literal number or a `wizard:<field>` reference (e.g. `wizard:hoa_doc_days`). Two honest-undated invariants matter: if the acceptance/closing anchor is unset, contract-anchored tasks are left **undated** (not fabricated off `today()`), and if a `wizard:<field>` offset points at an unset value the task is left undated rather than collapsed onto its anchor. Each unresolved template is logged and surfaced as a warning.

6. **Counting basis** (`effective_day_basis`). A deadline counts calendar days by default, or **business** days when the contract's per-deadline `deadline_day_basis_json` (or the template default) says so; `add_business_days` skips weekends and US federal holidays (computed in-code, no third-party dependency).

7. **Weekend/holiday roll-forward** (`maybe_roll_forward`). With the client-confirmed default flag `ve_deadline_no_roll_v1` **on**, computed dates are returned **unchanged**, weekends and holidays included ("hitting too early beats hitting late"). Turning the flag off restores the legacy roll-to-next-business-day convention. The given contract anchors themselves are never rolled.

Each planned task carries human-readable derivations for the review UI: `included_because` (e.g. "Property has an HOA"), `due_basis` (e.g. "Closing − 14d"), and `depends_on` predecessor names.

**Persistence** (`generate_tasks_for_transaction`): dates are computed over the **full** plan first, then the Review step's `excluded_template_ids` are dropped (so surviving tasks keep correct deadlines even when a predecessor was excluded). A relative rule always beats a stale absolute date — the server is the single place deadline arithmetic happens. Added tasks are created with `source="ai"` (or `source="manual"` + `milestone_label="Deadline"` for custom deadlines), carrying rationale, evidence citations, and a resolved `related_requirement_id`. The endpoint rejects generation if tasks already exist (409; use the use-case switch for updates) and, after generating, instantiates default requirement rows if the transaction has none (quick-create parity).

### 5.1 Preview and AI supplements

- `POST /transactions/preview-tasks` runs the full planner on a transient (unsaved) transaction and returns tasks + timeline + requirements + a summary that includes `coverage_warnings` (e.g. "no title task was generated because who-orders-title was never answered").
- `POST /transactions/preview-tasks/ai-suggestions` asks the AI for **supplemental** tasks for a draft deal. These are always reviewed and explicitly added by the user, never auto-applied.

---

## 6. Compliance document requirements

Server half: `services/requirement_planner.py`. Pure and deterministic, using the same condition evaluator and the same timeline anchors as tasks (`plan_requirements`):

- Library requirement templates are filtered by use case and by compiled conditions (`has_hoa`, etc.).
- Due dates resolve against the timeline anchors via `resolve_due` (an explicit date wins; an unresolvable anchor yields `None`, never a guess).
- User-added rows and accepted AI rows ride `extra_requirements` and resolve their rule dates with the identical server arithmetic.
- Each row has a `source` (`system` / `condition` / `user` / `user_template` / `ai`) and a human basis label ("14 days after acceptance").

Requirement **status** is `missing` / `uploaded` / `waived`, with an optional `matched_document_id`. `instantiate_default_requirements_if_absent` creates the unmodified library defaults for any transaction that has none, so non-wizard creates (quick-create modal, API) still get a checklist.

---

## 7. Stage 3 — Ongoing processing: the Transaction Workspace

Frontend: `src/pages/transactions/TransactionWorkspacePage.tsx` with tab components under `src/components/workspace/`. Backend data layer: `api/v1/transaction_plan.py`.

### 7.1 The plan aggregate

`GET /transactions/{id}/plan` returns **one deterministic, zero-LLM aggregate** (`_PlanResponse`) that powers the whole workspace in a single request: a header (title, client names, address, status, stage pill, days-to-close, price, use case, representation, appraisal election, an AI-or-rule next step, and honest task/doc counts + weekly sparkline series), the `core_dates`, `term_rows` (contingency deadlines with their editable rule), `deadline_tasks`, `requirements_due`, `tracking_dates`, the deal `brief`, and `coverage` prompts. It is also the regression oracle for the create-boundary invariant: nothing the wizard committed may be missing from this response.

### 7.2 Tabs

The workbench is a single panel of underline tabs:

- **Timeline** (`TimelineTab`) — core dates, term rows, and deadline tasks on one timeline, each row showing its basis and (for AI rows) its citation chip (`AiEvidenceChip`).
- **Compliance** (`ComplianceTab`) — the document requirement checklist: match/unmatch a document, waive/restore, add rows.
- **Documents** (`DocumentsTab`) — upload, view, manage, and drag-drop-intake documents.
- **Tasks** (`TasksTab`) — the task list with status changes.
- **People** (`PeopleTab`) — parties and vendors.
- **Activity** (`ActivityTab`) — the audit/communication history.
- **Email** (`EmailTab`) — AI email drafts/review (agent-enabled deals).
- **Agent** (`AgentPane`) — on wide screens a persistent conversation pane beside the workbench; on narrow screens a tab. The AI agent proposes next actions grounded in the deal.

A cross-tab navigation resolver routes a reference (`requirement` / `task` / `deadline` / `document` / `party` / `email`) to the right tab and flashes the target row.

### 7.3 Task lifecycle

Status changes go through `PUT /api/v1/tasks/{id}/status` (`tasks.py:804`): moving to `Completed` stamps `completed_at`, the change is audit-logged (`task_status_changed`), the AI next-step cache is invalidated, and a `task.completed` / `task.updated` webhook event is emitted in the background. Tasks can also be created, edited, deleted, and queried per transaction; a global **Task Queue** (`GET /api/v1/tasks/queue`, `src/pages/tasks/TaskQueuePage.tsx`) groups a user's tasks across deals with progress/counts/focus.

### 7.4 Coverage banners (resolve-in-place)

For deals with unanswered gating decisions (who orders title, cash appraisal), the plan returns `coverage` prompts that the workspace renders as one-click banners (`CoverageBanner`). Choosing an option PATCHes the transaction column, and the change retargets the gated tasks. Wizard-created deals rarely show these; API-created and pre-existing deals do.

### 7.5 Deadline cascade (contract changes / addenda)

When a core date changes (an addendum moves closing, or the user edits an anchor), the workspace previews and applies a cascade:

- `POST /transactions/{id}/plan/preview` — a dry-run (`compute_plan_cascade`) that returns which deadlines **move** (old → new date, weekend-rolled flag) and which are **not moved** (`pinned` / `completed` / `no_rule` / `no_anchor`), plus a summary sentence.
- `POST /transactions/{id}/plan/apply` — commits the cascade, **idempotent on `commit_id`**, returning the inverse changes for an Undo chip and a `calendar_resync_recommended` flag.

Under the hood this is the same recompute logic exposed at the transaction level: `recompute_task_dates` (`task_generation_service.py`) recomputes template-sourced task dates from the transaction's current dates and returns a diff; with `apply=True` it writes the new dates to non-completed template tasks (completed tasks are history and are always preserved).

### 7.6 Use-case switch and retargeting

Changing the use case (`PUT /transactions/{id}/use-case`) or a gating field runs `retarget_conditional_tasks`. Its contract: completed tasks are always preserved; **only** template-sourced tasks are ever removed, and only when their template no longer applies; manual and AI-added tasks are **never** touched; newly applicable templates are added with planner-computed dates. `changed_fields` scopes the diff to templates whose conditions reference the changed columns (so a who-orders-title answer retargets only the title tasks); a full use-case switch runs the full diff.

### 7.7 Key-date editing and status lifecycle

Operational milestone dates (EM Delivered, Inspection Response, Appraisal Expected, CD Delivered, Cleared to Close, closing/possession date+time) are editable from the Active Transactions drawer via `PUT /transactions/{id}/key-dates`; every change is audited and invalidates the AI guidance cache. The transaction status moves through `Active → Completed → Closed` (or `Paused` / `Incomplete`) via `PUT /transactions/{id}/status`, each transition audited. Closing a deal can fire the post-closing feedback modal.

---

## 8. Cross-cutting behaviors

- **Preview equals commit.** The wizard preview, the workspace plan, the cascade, and the commit all call the *same* deterministic planners (`plan_tasks_for_transaction`, `plan_timeline`, `plan_requirements`). The LLM never computes a date.
- **Evidence for the life of the deal.** AI-proposed timeline rows, requirements, tasks, and watch-outs persist their contract citation (page + snippet + confidence) at the create boundary, so the workspace can always answer "why does this deadline/document exist."
- **Honest degradation.** Every AI pass (double-check, intake intelligence, multi-doc resolver, public-source search, e-sign) is advisory and non-fatal. A provider failure drops the pass to a deterministic floor with a banner; it never strands the transaction.
- **Provider discipline.** The configured AI provider is used strictly, with no automatic fallback (`_provider_model_name` / `_build_pydantic_ai_model`).
- **Auditing.** Create, status changes, key-date edits, task status changes, use-case switches, and task generation all write `audit_log` rows, which surface in the workspace Activity tab and the transaction history endpoint.
- **Billing.** A deal costs one credit at create time (when billing is enabled), enforced with a pre-check `402`, an atomic debit, and compensate-delete on a lost race. This is the single spend point.
- **Export.** The transaction list exports to CSV / Excel / PDF, mirroring the page's status/search filters.

---

## 9. Known limitations in the current build

These are the two places where an intake affordance is present but not fully functional (documented so the description is honest):

1. **"AI Search" on the Missing Info step** posts to `POST /api/v1/ai/search-public-source`, whose backend method (`AIService.search_public_source`) is a deliberate stub — no provider implements `search_public_source`, so it always returns an empty list. Manual entry and the one-click choice rows on that step work fully.
2. **Address autocomplete** on the Address step is gated off by a hard-coded constant, and no Google Places key is provisioned, so the street field falls back to the user's recent addresses (empty for a new tenant). All address sub-fields remain manually editable.

Neither touches the extraction, task-generation, or commit core; both are isolated intake conveniences.

---

*Every claim above was read from current source: `document_packet_parsing.py`, `intake_intelligence.py`, `dependency_engine.py`, `task_generation_service.py`, `requirement_planner.py`, `timeline_planner.py`, `transactions.py`, `transaction_plan.py`, `tasks.py`, `ai.py` (backend); `NewTransactionWizard.tsx`, `wizardTypes.ts`, `useWizardApi.ts`, `TransactionWorkspacePage.tsx`, and the `workspace/` tab components (frontend).*
