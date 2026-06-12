# AI Wizard Superiority Completion Plan

Date: 2026-06-11 (revised same day after a full source-verification review pass)
Author: Jan Froben
Status: PLAN ONLY. No source code has been changed for this document.
Supersedes nothing; builds directly on top of the merged work from
`AI_WIZARD_LISTEDKIT_PARITY_GAP_CLOSURE_PLAN.md` (frontend PR #95, backend PR #118,
both merged to `develop`).

---

## 0. Executive Summary

The previous parity plan has been fully implemented and merged. The wizard today is a
7-step, full-screen, evidence-cited intake workspace with a live extraction feed, a
two-pass double-check gate, row-level source verification against the actual PDF, task
preview that runs the real planner, draft resume on the server, and e-sign queueing.
On extraction transparency and source verifiability we are already ahead of ListedKit.

A fresh review of all 25 ListedKit screenshots (`ai_wizard/Screenshot_27.png` through
`Screenshot_51.png`) against the current `develop` source shows that ListedKit still
wins on exactly **four workflow capabilities**, all in the second half of their flow:

1. **A dedicated Timeline Review step.** ListedKit shows every deadline with its
   calculation basis ("5 days after Date of Acceptance"), lets the user confirm the
   anchor date first, and lets them add, edit, or remove deadlines as relative rules.
   We show key dates as plain editable fields; we never show or edit the rule.
2. **A Compliance Checklist step.** ListedKit generates the list of documents the file
   needs (EMD receipt, loan application, inspection report, insurance binder, deed,
   and so on), each with a description and a relative due date, supports add/edit/
   remove, and accepts the user's own checklist by PDF/TXT/CSV upload or paste.
   We have no required-documents concept (verified in §0.1, correction C8).
3. **Relative due-date editing on tasks.** ListedKit's Edit Task modal expresses due
   dates as "N days before/after [Deadline | Task | Document]" and links a task to a
   related compliance item. Our Review step only supports absolute date overrides.
4. **Auto-Email per task.** ListedKit marks tasks with an Auto-Email badge and an
   "Auto-draft email" toggle. When we built the parity plan this was ungrounded; the
   Auto-Emailing system (compose, templates, review queue, notification runners) has
   since been merged to `develop`, so this is now buildable honestly.

This plan designs those four capabilities natively for Velvet Elves, plus the
supporting UX (5-phase public stepper, persistent timeline rail, search/filter in the
checklist and task steps), the data model and API changes, the exact UI specification
per `STYLE_GUIDE.md`, and a tester-facing validation script for every new behavior.
Every feature is grounded in a system that already exists in the repos; nothing
requires invented data, and every deliverable can be validated end to end by a
non-developer using only the mouse and a test PDF.

What makes the result strictly superior to ListedKit rather than equal to it:

- ListedKit's checklist is a static list that dies after intake. Ours becomes living
  state: requirement rows drive the Documents tab "Missing" section, the client
  portal document status cues that already exist, AI missing-document suggestions,
  and (behind the existing review queue) AI chase emails.
- ListedKit's timeline shows the rule. Ours shows the rule, the source page in the
  actual contract, and recomputes every dependent task date through the same
  deterministic planner that the commit path uses, with business-day and holiday
  awareness that already exists in `dependency_engine.py`.
- Every AI-extracted value in our flow is click-verifiable against the document with
  OCR-region highlighting. ListedKit only cites page references.
- Cross-device draft resume (`wizard_runs`) and signature detection with e-sign
  queueing have no visible ListedKit equivalent.

---

## 0.1 Source-Verification Corrections (2026-06-11 review pass)

After drafting, I re-verified every workflow and logic assumption against the live
`develop` source of both repos and the documentation set. The following corrections
are already incorporated into the body of this plan. They are listed here so a
reviewer can see what changed and why, in the same spirit as §2B of the parity plan.

- **C1, commit ordering inversion (was a real bug in the draft plan).** The draft
  created document requirements *after* task generation, while also letting tasks
  link to requirements via `related_requirement_id`. Requirement ids do not exist
  until the bulk insert returns, so the links could never be written. The verified
  commit sequence in `NewTransactionWizard.tsx` (create transaction → pinned note →
  parties → vendor-save prompt → link documents → optional e-sign → generate tasks)
  now gains the requirements bulk call **after document linking and before task
  generation** (§8.4), so resolved requirement ids are available to the generate
  payload, and `matched_document_id` can use the just-linked document ids.
- **C2, idempotency key.** The draft keyed bulk-insert idempotency on "the wizard run
  id". A `wizard_runs` row is not guaranteed to exist (the server draft is optional
  and is deleted on create). Corrected to a client-generated commit UUID stored in
  wizard state and carried inside the draft payload (§8.4).
- **C3, Auto-Email eligibility was built on a field that does not exist.** The draft
  gated the toggle on `completion_method`, but `TaskTemplate`
  (`app/models/task_template.py`) has **no completion_method field**, and the preview
  response does not carry one. Eligibility is now: the task's `target` (Buyer,
  Seller, Co-op Agent, Loan Officer, Title, ...) resolves to a confirmed party or
  vendor with an email address in the wizard state (§6.2). Deterministic, visible,
  and testable. `completion_method` exists only on Task instances and stays relevant
  for manually added tasks.
- **C4, wrong runtime hook for auto-drafts.** The draft hooked auto-draft creation
  into "the reminders runner" in `ai_emails.py`. Verified: `POST
  /ai-emails/reminders/run` calls `task_notification_service.send_daily_summaries`,
  which emails *internal users* their due-task summaries; it is not an outbound
  compose path. Corrected: a sibling sweep in `task_notification_service` invoked by
  the same daily cron/admin trigger, which calls the existing compose service
  (`ComposeRequest`: `transaction_id`, `recipient_emails`, `intent`) to file drafts
  into the existing review queue (§8.7).
- **C5, timeline rows included dates that cannot exist at intake.** The draft listed
  the five operational milestone dates (EM Delivered, Appraisal Expected, CD
  Delivered, Cleared to Close, Inspection Response) as timeline rows. Those are
  tracking dates recorded *during* the transaction; at intake they are unknowable,
  and rendering undated rows would violate the honest-empty-state rule. Corrected
  (§4.3): the timeline shows the anchor, closing, possession, and contract-derived
  deadlines that actually have values; operational tracking dates stay in the Active
  Transactions drawer where they belong. The one 1:1 mapping kept is the inspection
  response deadline onto `inspection_response_date` (it exists on
  `TransactionCreateRequest`, verified).
- **C6, relative-rule storage gap for system deadlines.** The draft offered "relative
  to any anchor" editing on every timeline row, but the `Transaction` model has no
  metadata column to store an arbitrary rule for a derived deadline; derived
  deadlines are stored as day-count term fields (`inspection_days`,
  `inspection_response_days`, `hoa_doc_days`, `insurance_days`, all verified on
  `TransactionCreateRequest`). Corrected (§4.3): derived rows edit via a day-count
  stepper against their natural anchor (which writes the underlying term field) or
  an absolute date; the full anchor-choice editor applies where a rule can actually
  be persisted: custom deadlines, checklist requirements, and tasks.
- **C7, custom-deadline date drift.** The draft let the browser compute custom
  deadline dates, which would drift from the server's business-day and holiday
  arithmetic. Corrected (§4.5, §8.3): `_AddedTask` gains optional basis fields and
  the server resolves dates at preview and at commit, so there is exactly one
  arithmetic, in `dependency_engine.py`.
- **C8, existing services reconciled.** The backend already contains
  `closing_checklist.py` (`build_closing_checklist`, the printable buyer/seller
  closing sheets of requirements §4.10) and `document_template_registry.py` (the
  registry of document types that can be *generated* from templates, with required
  fields). Neither is a per-transaction required-documents checklist, so the claim
  "no required-documents concept exists" stands, but §5.2 now names both, defines
  the compliance checklist as a third distinct concept, and reuses the registry's
  `doc_type` vocabulary for requirement-to-document matching so the three systems
  stay interoperable rather than parallel.
- **C9, document auto-match overclaim.** The draft promised "the purchase agreement
  always will" auto-match. The resolver output is an opaque advisory
  (`transaction_resolution: dict`, see parity plan Gap F: attribution unverified).
  Corrected (§5.3): conservative deterministic matching only (single uploaded
  document matches the primary-contract requirement; anything else stays unmatched
  with a one-click "Mark as uploaded" document picker).
- **C10, missing-docs detector described imprecisely.** Verified:
  `_det_missing_required_docs` (suggestion_engine.py:267) currently keys off open
  *task names* by keyword within a closing window. §5.6 now specifies a
  requirements-based branch plus the existing keyword fallback for transactions
  created before this feature (which will have no requirement rows).
- **C11, generate-request schema extensions made explicit.** Verified current shapes:
  `_TaskOverride { template_id, due_date, target }` and `_AddedTask { name,
  description, target, due_date, automation_level, ai_rationale }`
  (transactions.py:1121). §8.3 now spells out the exact field additions, and the
  preview response addition of `description` (which `TaskTemplate` has but
  `PreviewTaskItem` currently lacks).
- **C12, quick-create consistency.** Workflow A's quick-create modal creates the same
  transaction object outside the wizard. If only wizard files got checklists,
  testers would read quick-created files as broken. §5.7 routes both paths through
  one server-side instantiation service (Decision D7).
- **C13, draft-resume wording.** "v1 drafts resume into confirm safely" was wrong.
  Corrected (§9.2): v1 drafts restore to their saved step unchanged; the new steps
  initialize fresh from preview data on first entry. Also flagged the verified
  `returnToConfirmAfterEdit` hop-back shortcut (NewTransactionWizard.tsx:6121) as a
  regression risk to test: it must keep returning to `confirm` only for edit-jumps,
  never hijacking timeline/checklist forward navigation.
- **C14, role gating stated explicitly.** The generate endpoint allows Agent, TC,
  Team Lead, Admin (verified `require_role` list). All new requirement endpoints use
  the same set (§8.4).
- **C15, checklist-import file handling.** The checklist file is parsed via direct
  multipart upload to the new endpoint and is **not** persisted as a transaction
  Document (so the wizard never links it to the created transaction) (§8.5).
- **C16, `ai_condition` source value renamed to `condition`** to avoid implying an
  LLM was involved in deterministic predicate gating (§8.1).
- **C17, single source of truth for the anchor.** The timeline anchor card edits the
  same `purchase.contract_acceptance_date` state the purchase step owns, not a copy
  (§4.2).

---

## 1. Inputs Reviewed

### 1.1 Project documentation (read in full or in the cited sections)

| Document | What it governs here |
|---|---|
| `requirements.txt` §3 (Wizard), §4 (Task Engine), §5.2/5.4 (document status, e-sign), §6.3/6.4 (AI email rules and safeguards), §1.5/§4.10 (profile checklist templates), §8.1a (provider switching), §9.1 (UI rules) | Functional scope and guardrails |
| `SYSTEM_DESIGN.md` (task template schema with `wizard:` references, `conditions_json`, endpoints, §1041 `POST /transactions/{id}/tasks/generate`) | Engine and schema conventions |
| `FRONTEND_UI_WORKFLOW_LOGIC.md` §4.5 (`/transactions/new`), Cross-Cutting Workflow A (full wizard), C (task management), D (document lifecycle), E (AI email flow) | Canonical workflow logic |
| `STYLE_GUIDE.md` (all sections; §2 tokens, §3 typography, §6 components, §10 AI-adjacent UI, §13 anti-patterns) | Visual specification |
| `milestones.txt` | Delivery framing |
| `AI_WIZARD_LISTEDKIT_PARITY_GAP_CLOSURE_PLAN.md` | What is already built; its Phase 8 list |
| `AI_WIZARD_REDESIGN_SUPERIOR_PLAN_V2.md`, `AI_WIZARD_REDESIGN_SUPERIOR_LISTEDKIT_PLAN.md`, `LISTEDKIT_COMPETITIVE_ANALYSIS_AND_FEATURE_IMPROVEMENT_PLAN.md` | Historical decisions; not re-litigated |
| `SMART_TRANSACTION_PROCESSING_AND_TASK_ENGINE_PLAN.md` | Task engine root causes and the implemented Phase A/B fixes |
| `WIZARD_TESTING_GUIDE.md` | The tester-facing validation format this plan extends |
| `AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md` | The merged email system the Auto-Email toggle hooks into |

### 1.2 ListedKit screenshots (all 25 reviewed)

| Screens | Content |
|---|---|
| 27 to 29 | Step 1: welcome panel, multi-file upload (25 MB/file, max 10), file list with preview/remove, "Which side do you represent?" (Listing / Both / Buyer), Start Intake |
| 30 | Waiting state with "did you know" educational card and bottom progress bar |
| 31 to 33 | Live extraction log (specific, field-level lines) beside a PDF viewer with tabs, zoom, page thumbnails |
| 34 to 38 | "Review Transaction Details": Property Details and Parties and Financing Summary and Terms as Name/Value tables, per-row edit + source controls, source strips citing section and page, "Your timeline is ready" interstitial |
| 39 | Anchor gate: "Does this Date of Acceptance look right?" with the date, its source basis, and a single Looks Good button |
| 40 to 43 | "Review Your Timeline": deadline rows with final date plus basis ("5 days after Date of Acceptance"), per-row edit/delete/source, Add Deadline, summary + source page reveal, Confirm Timeline |
| 44 to 48 | "Confirm Your Compliance Checklist": generation state, document cards with description and due date, Edit Document modal (relative date: Days, Before/After, Relative to Deadline/Task/Document, Related item), Add Document modal, "Use Your Own Compliance Checklist" (Upload PDF/TXT/CSV or Paste Text), uploaded contract auto-checked, persistent Transaction Timeline rail |
| 49 to 51 | "Review Your Task List": task cards with descriptions, relative due rules, Auto-Email badge, Edit Task modal (Auto-draft email toggle, relative date, Notes, Related Compliance Item), Add Task, Open Transaction File |

### 1.3 Source code verified on `develop` (both repos clean, parity work merged)

Frontend (`velvet-elves-frontend`):

- `src/components/wizard/NewTransactionWizard.tsx` (7,900 lines): 7 internal steps
  (`upload`, `parsing`, `address`, `purchase`, `missing`, `confirm`, `review`),
  representation radio gating upload, manual fallback, live extraction feed,
  FieldTable rows with per-row source strips, ReviewTable confirm step, top stepper.
  Verified commit sequence (lines 3132 to 3299): create → pinned note → parties →
  vendor-save prompt → link documents → optional e-sign queue → generate tasks
  (with `excluded_template_ids`, `overrides`, `added_tasks`, `exclusion_reasons`) →
  refresh, clear local + server drafts, navigate. Verified navigation specials:
  `returnToConfirmAfterEdit` hop-back (line 6121), visited-steps stepper jumping
  (line 6137).
- `src/components/wizard/ReviewTasksStep.tsx` (635): dry-run task preview grouped by
  milestone, include/exclude with undo, absolute due-date overrides, removal reasons,
  custom checklist paste (one task per line), AI supplemental-task suggestions.
- `src/components/wizard/WizardEvidenceViewer.tsx` (647), `WizardPdfDocument.tsx`
  (281): multi-document tabs, page thumbnail rail, OCR geometry highlight, text
  search with digits-only phone matching, cross-document locate.
- `WizardDoubleCheckPanel.tsx`, `WizardMissingDocsPanel.tsx`, `WizardSignaturePanel.tsx`,
  `SuggestImprovementButton.tsx`, `DocumentSplitDialog.tsx`, `WizardStepper.tsx`,
  `wizardTypes.ts` (758).
- `src/hooks/useWizardApi.ts` (517): upload, packet parse + status polling, resolve,
  split, public search, intake classify, feedback, create transaction/party,
  generate tasks, preview tasks, AI suggestions preview, server draft
  (GET/PUT/DELETE `/wizard-runs/current`).
- `PreviewTaskItem` carries `due_basis`, `depends_on`, `milestone_label`,
  `included_because`, `warnings`; it does **not** carry `description` or any
  completion method (useWizardApi.ts:429).

Backend (`velvet-elves-backend`):

- `app/api/v1/ai.py` (1,733): packet parse with persisted stage progress events,
  double-check verifier, resolver (`ResolveDocumentsResponse.transaction_resolution`
  is an opaque advisory dict), `search-public-source`, `intake/classify`, feedback.
- `app/api/v1/transactions.py`: `POST /transactions/preview-tasks` takes a full
  `TransactionCreateRequest` and builds a transient Transaction
  (`_request_to_transient_transaction`), `POST /transactions/preview-tasks/
  ai-suggestions`, `POST /transactions/{id}/recompute-dates?apply=`,
  `POST /transactions/{id}/tasks/generate` with `_TaskGenerateRequest
  { excluded_template_ids, exclusion_reasons, overrides: _TaskOverride[],
  added_tasks: _AddedTask[] }`; role gate Agent/TC/TeamLead/Admin.
- `app/schemas/transaction.py`: `TransactionCreateRequest` carries the core dates,
  the milestone dates (including `inspection_response_date`), and the wizard term
  fields (`inspection_days`, `inspection_response_days`, `has_hoa`, `hoa_doc_days`,
  `has_home_warranty`, `title_ordered_by`, insurance fields).
- `app/services/task_generation_service.py` + `dependency_engine.py`: shared pure
  planner (preview == commit), anchor seeding (legacy ids 5 and 1000), business-day
  basis, holiday roll-forward, dual-agency de-duplication, compiled conditions.
- `app/models/task_template.py`: has `description`, `target`, `cc_targets`,
  `milestone_label`, `float_days`, `day_basis`, `dep_task_ids`, `conditions_json`,
  `task_family`, `dual_agency_behavior`. **No completion_method.**
- `app/api/v1/ai_emails.py`: drafts queue, `POST /compose` (`ComposeRequest
  { transaction_id, recipient_emails, intent, subject, body, template_id }`),
  templates CRUD, tenant settings, approve/edit/send/regenerate/discard,
  escalations runner, and `POST /reminders/run` which calls
  `task_notification_service.send_daily_summaries` (user-facing due-task summary
  emails, requirement 4.8).
- `app/services/suggestion_engine.py`: deterministic detectors including
  `_det_missing_required_docs` (line 267), currently keyword-matching open task
  names within a closing window.
- `app/services/closing_checklist.py` (`build_closing_checklist`): the printable
  closing sheets feature (requirements §4.10). Distinct concept; see §5.2.
- `app/services/document_template_registry.py`: registry of document types that can
  be generated from templates (`doc_type`, `doc_label`, required fields, fix
  routes). Distinct concept; see §5.2.
- `app/api/v1/wizard_runs.py` + migration `20260815090000_wizard_runs.sql`.
- `app/models/task.py`: `metadata_json`, `milestone_label`, `completion_method`,
  `target`, `cc_targets`, `float_days`, `dependencies_json`.
- `app/models/transaction.py`: core dates, five milestone dates, wizard term fields.
  **No metadata/JSON column** for arbitrary per-transaction rules.
- `app/models/document.py`: per-document `status`, `doc_type`, `is_signed`,
  `signature_status`, review states. **No required-documents concept**, which
  confirms the compliance checklist needs a new model.

### 1.4 Working constraints honored by this plan

- Testers are real-estate professionals, not developers. Every deliverable must be
  validatable entirely through the UI with mouse-first interactions and minimal
  typing. Every new control in this plan is a button, stepper, dropdown, toggle, or
  date picker; free text is only ever optional.
- No demo or sample data on real surfaces. New steps must render honest empty states.
- Layout may follow the ListedKit comps; styling always comes from `STYLE_GUIDE.md`
  (champagne accents, Lora serif protagonists, mono kickers, `ve-*` tokens only).
- AI may prepare; the human decides. Nothing external or AI-generated is accepted
  without explicit confirmation (requirements §3.7, §6.4).
- Suggestion existence stays deterministic so testers can predict exactly which cards
  appear. The LLM extracts and drafts; it does not invent checklist or task rows at
  generation time.

---

## 2. Where the Wizard Stands Today

Verified capabilities (do not rebuild, do not regress):

| Area | Status on `develop` |
|---|---|
| Full-screen workspace, branded top bar, centered step dots, per-step CTAs ("Start Intake", "Confirm Details", "Approve & Create Transaction") | Done |
| Representation choice before parsing | Done (Buyer / Seller / Buyer & Seller) |
| Multi-file upload, 20 MB cap, auto-compression note, page-range splitting | Done |
| Live field-level extraction feed with persisted progress events | Done, richer than ListedKit's log |
| Two-pass double-check with a blocking acknowledge gate on disagreement | Done, ListedKit shows nothing comparable |
| Row-level source verification: every AI value has a find control, inline source strip, OCR-region highlight, text-locate fallback, cross-document search | Done, stronger than ListedKit's page citations |
| Review Transaction Details tables (Property, Parties, Key Dates, Financing, Terms) | Done |
| Missing info step with labeled AI public search and mandatory confirmation | Done |
| Signature review and e-sign queue when AI detects missing signatures | Done |
| Task preview that dry-runs the real planner, include/exclude, absolute date overrides, AI supplemental suggestions (explicit add only) | Done |
| Custom checklist paste (one task per line) | Done (upgraded by §5.5) |
| Draft resume: localStorage plus server `wizard_runs` | Done |
| Engine correctness: anchored dates, de-duplication, compiled conditions, business days, holiday roll-forward, preview == commit | Done (SMART plan Phases A/B) |

Deployment note for Jan: confirm migrations `20260814090000_document_ocr_geometry.sql`
and `20260815090000_wizard_runs.sql` are applied in the target environment before
testing resume and source highlighting there.

---

## 3. Gap Analysis Against the Screenshots

| # | ListedKit capability (screens) | Velvet Elves today | Verdict |
|---|---|---|---|
| G1 | Anchor confirmation gate, "Does this Date of Acceptance look right?" (39) | Acceptance date is one editable field among many in `purchase` | **Build** (§4.2) |
| G2 | Timeline step: per-deadline final date + relative basis, edit rule, delete, add, source (40 to 43) | Key dates editable as absolute values only; basis never shown outside task preview `due_basis` | **Build** (§4) |
| G3 | Compliance checklist step: generated document requirements with descriptions, relative due dates, add/edit/remove, search (44 to 47) | No required-documents concept | **Build** (§5) |
| G4 | Use Your Own Compliance Checklist: upload PDF/TXT/CSV or paste (48) | Paste-only, creates tasks rather than document requirements | **Upgrade** (§5.5) |
| G5 | Task relative due-date editor: Days, Before/After, Relative to Deadline/Task/Document (51) | Absolute date override only | **Build** (§6.1) |
| G6 | Auto-Email badge + Auto-draft email toggle on tasks (49 to 51) | Not present; the email engine it needs is now merged | **Build** (§6.2) |
| G7 | Related Compliance Item link on a task (51) | Not present | **Build** (§6.1) |
| G8 | Persistent Transaction Timeline rail on checklist/tasks steps (44 to 50) | Right pane is the PDF viewer, hidden on the review step | **Build** (§4.4) |
| G9 | Search box over checklist documents and tasks (44, 49) | Not present | **Build** (§5.3, §6.3) |
| G10 | "Step X of 5" public phase model | 7 dots matching internal steps | **Build** (§7.1) |
| G11 | "Did you know" cards while waiting (30) | Live extraction feed instead | **Optional**; our feed is more informative. Offer as idle-filler copy only if Jake wants it |
| G12 | Credits counter (all screens) | Not applicable to our business model | **Skip**, deliberate |

Everything else in the screenshots is already met or exceeded.

---

## 4. New Step: Review Your Timeline

### 4.1 Placement and purpose

A new internal step `timeline` between `confirm` and the checklist step. It receives
the confirmed facts and turns them into the deal calendar the user actually signs off
on. It answers three questions a coordinator asks on every file: what is the anchor,
what are the deadlines, and what happens if one moves.

Internal step order becomes:

```
upload → parsing → address → purchase → missing → confirm → timeline → checklist → review
```

### 4.2 Anchor gate (top of the step)

A single card, ListedKit screen 39's layout, our styling:

- Mono kicker `✦ TIMELINE ANCHOR`, serif title "Does this Date of Acceptance look
  right?", the date rendered large in tabular nums, beneath it the source line reusing
  the existing `ReviewSourceStrip` (snippet, page, View in Document wired to the
  evidence viewer; this data already exists on the acceptance-date citation).
- Two actions: primary "Looks good" and secondary "Edit date" (inline date picker,
  no navigation). Editing writes the **same**
  `purchase.contract_acceptance_date` state the purchase step owns (single source of
  truth, correction C17); the purchase step and the confirm table reflect the change
  because they read the same field.
- Confirming enables the deadline list below (rendered dimmed and non-interactive
  until then, with the hint "Confirm the anchor first; every deadline below is
  calculated from it"). The step's primary CTA stays disabled until the anchor is
  confirmed.
- If extraction produced no acceptance date (or the user is in manual mode), the
  card renders the honest empty state: "I couldn't find a Date of Acceptance in the
  documents" plus the date picker. No fabricated default.

### 4.3 Deadline list

One row per timeline entry. The list is produced by the same pure planner the task
preview uses (§8.2) so what the user confirms here is exactly what generation will
use. **Only rows that have a value render** (correction C5); there are no undated
placeholder rows. Initial population:

- Core dates from the wizard state: Date of Acceptance, Closing Date, Possession
  Date.
- Contract-derived deadlines computed from term fields the parser already extracts
  and `TransactionCreateRequest` already carries: inspection deadline
  (acceptance + `inspection_days`), inspection response deadline
  (+ `inspection_response_days`, maps onto `inspection_response_date` at create),
  HOA document delivery (+ `hoa_doc_days`, only when `has_hoa`), insurance deadline
  (+ insurance days), and financing application/approval deadlines when the contract
  states them as extracted dates.
- Operational tracking dates (EM Delivered, Appraisal Expected, CD Delivered,
  Cleared to Close) are deliberately **not** wizard timeline rows; they are recorded
  during the transaction in the Active Transactions drawer (requirements §2.1). The
  step explains this in one muted line so testers do not search for them here.

Row anatomy (FieldTable-family styling, §9):

```
[calendar icon]  Home Inspection Deadline            Fri, Mar 20 2026
                 5 days after Date of Acceptance     [edit] [remove] [find]
```

- Name, final date (tabular nums), and a **basis chip** in muted text. Basis kinds:
  `From contract text` (with page source), `N days after Date of Acceptance` (term
  arithmetic), `You set this date`. The chip is honest about provenance; a
  system-computed date never claims to be quoted text.
- `[find]` reuses the existing source magnifier + `ReviewSourceStrip` + evidence
  viewer jump for extracted dates. Computed dates show the rule instead of a snippet.
- `[edit]` opens a popover whose modes depend on what can actually be persisted
  (correction C6):
  - **Derived rows** (term-based): a Days stepper against the row's natural anchor
    ("[7] days after Date of Acceptance"; writes the underlying term field, e.g.
    `inspection_days`), or an absolute date picker (writes the mapped date field).
  - **Core date rows** (closing, possession): absolute date picker.
  - **Custom rows**: the full `RelativeDateRuleEditor` (Days stepper, Before/After,
    anchor dropdown over the other timeline entries) or an absolute date.
- `[remove]` applies to custom rows and optional derived rows (HOA, insurance),
  soft-removes with an inline Undo chip. Core dates cannot be removed, only edited;
  their remove control does not render.
- "+ Add deadline" opens the custom-row editor plus a Name field (the one place
  typing is required, because a custom deadline needs a name) and an optional
  description.

### 4.4 Cascade preview and the timeline rail

When the user edits the anchor or any term that other dates depend on:

- The step re-runs the dry-run preview (§8.2) and updates dependent rows in place,
  marking changed rows with a small amber `updated` chip for one render cycle.
- A summary line appears above the list: "3 deadlines and 12 task dates moved", with
  "Review changes" expanding a compact diff (old date struck through, new date).
  The diff is computed by comparing the previous and new preview responses
  client-side; the dates themselves always come from the server planner.

The confirmed timeline then persists as a compact right-rail card ("Transaction
Timeline", ListedKit screens 44 to 50) on the checklist and task steps, where the PDF
viewer is not shown. Read-only there; each entry deep-links back to the timeline step.

### 4.5 What confirm writes

Nothing is created at this step. The confirmed timeline travels in wizard state:

- Core dates and the inspection response deadline map onto the existing
  `TransactionCreateRequest` fields (`contract_acceptance_date`, `closing_date`,
  `possession_date`, `inspection_response_date`).
- Edited day-count rules map onto their existing term fields (`inspection_days`,
  `inspection_response_days`, `hoa_doc_days`, insurance fields). Because the preview
  endpoint consumes the same `TransactionCreateRequest`, preview == commit holds with
  no new transport for these edits.
- Custom deadlines are sent at commit through the existing `added_tasks` channel,
  extended with basis fields (§8.3), with `kind: "deadline"` and `milestone_label:
  "Deadline"`. The **server** resolves their dates from the basis at both preview
  and commit (correction C7), so business-day and holiday arithmetic lives in
  exactly one place. They then appear in My Task Queue, the Closing Calendar, and
  calendar push with zero new infrastructure (Decision D3 records the alternative).

---

## 5. New Step: Confirm Your Compliance Checklist

### 5.1 Placement and purpose

New internal step `checklist` between `timeline` and `review`. It shows the documents
this file must contain before closing, each with a due date derived from the confirmed
timeline. This is ListedKit screens 44 to 48, rebuilt on a real data model so the
checklist keeps working after the wizard closes.

### 5.2 Data model (new, backend) and how it relates to the two existing "checklist" systems

Three document-related systems will now exist, and they are deliberately distinct
(correction C8):

1. **Printable closing checklists** (`closing_checklist.py`, requirements §4.10):
   buyer/seller closing sheets generated from profile templates. Untouched.
2. **Document template registry** (`document_template_registry.py`): which document
   types the system can *generate* from templates, with required fields. Untouched,
   but its `doc_type` vocabulary becomes the shared matching key below.
3. **Compliance document requirements** (new): which documents this transaction must
   *contain*, with status tracking. This section.

Two new tables (full DDL in §8.1):

- `document_requirement_templates`: the system library. Per row: name, description,
  `doc_type` (aligned with the registry vocabulary and `documents.doc_type` where a
  match exists, so matching and future "generate this document" cross-links are
  possible), use cases (Buy-Fin, Buy-Cash, Sell-Fin, Sell-Cash), conditions over
  wizard fields (`has_hoa`, financing, `has_home_warranty`) in the same compiled
  predicate grammar task templates use, due-basis rule (days, direction, anchor
  key), sort order, `tenant_id NULL` for system rows so tenants can add their own
  later (same convention as task templates).
- `transaction_document_requirements`: the per-file instances. Per row: name,
  description, `doc_type`, due date plus stored basis, status (`missing`,
  `uploaded`, `waived`), `matched_document_id`, source (`system`, `condition`,
  `user`, `user_template`), template id when applicable.

The initial system library (about 18 rows) I will draft from the four use cases in
`SYSTEM_DESIGN.md`, the closing checklist material in requirements §1.5/§4.10, and
the document names visible in the ListedKit screens (purchase agreement, EMD receipt,
loan application evidence, inspection report, inspection response, appraisal report,
insurance binder, title commitment, CD, deed, final utility confirmation, HOA package
when `has_hoa`, home warranty when ordered). The library content ships in the seed
migration and goes to Jake for sign-off as a readable table before implementation
(Decision D1).

### 5.3 Step UI

- Header: serif "Confirm your compliance checklist", count pill, a search input that
  filters rows as you type (optional typing, never required), and "+ Add document".
- Generation is instant and deterministic (template filter + compiled conditions +
  timeline arithmetic, no LLM call), so unlike ListedKit there is no spinner
  theater; the list simply renders. A short AI-accent banner explains: "Built from
  your use case, contract terms, and timeline. Adjust anything."
- Requirement card per row: document icon, name, one-line description, due chip
  ("Sun 03/15/2026 · day of acceptance"), Edit and Remove buttons.
- **Document matching is conservative and deterministic** (correction C9): when
  exactly one document was uploaded in this wizard session, it matches the
  primary-contract requirement and renders checked with a green `Uploaded` chip and
  the real file name. With multiple uploads, no automatic match is made; each
  requirement row instead offers a one-click "Mark as uploaded" control that opens a
  picker listing this session's uploaded documents (mouse-only). Resolver output is
  advisory and is **not** used to auto-link (parity plan Gap F stands).
- Edit Document modal mirrors the deadline editor: Name, Description, due date as
  Specific date or Relative rule via the shared `RelativeDateRuleEditor` (Days
  stepper, Before/After, Relative to dropdown spanning Timeline deadlines and, in a
  second group, other checklist documents). Requirements have their own basis
  columns, so the full editor is persistable here (unlike derived timeline rows,
  §4.3).
- Remove uses the same soft-remove + Undo pattern. Removing never deletes a
  template; it excludes the instance (recorded as `waived` if it was already
  persisted, or simply not created during the wizard).

### 5.4 What confirm writes

At "Approve & Create Transaction" (final step), the wizard inserts the confirmed
requirement rows via the new bulk endpoint **after document linking and before task
generation** (correction C1; full sequence in §8.4), so requirement ids exist when
the task generate payload references them and `matched_document_id` can point at the
just-linked documents.

### 5.5 Use your own checklist (upgrade of the existing paste flow)

The existing paste flow in `ReviewTasksStep` becomes a first-class modal on this step,
matching ListedKit screen 48 but with confirmation discipline:

- Two tabs: Upload Document (PDF, TXT, CSV; drag/drop or browse) and Paste Text.
- Upload sends the file directly (multipart) to the new `POST
  /api/v1/ai/parse-checklist` (§8.5); the file is parsed and discarded, **not**
  persisted as a transaction Document (correction C15). Paste is parsed line-wise
  client-side exactly as today.
- Results render as a review list with checkboxes (all checked by default), each row
  editable inline before accepting. Source label: "From your checklist". Nothing is
  added without the explicit "Add N documents" confirmation, honoring the §3.7 rule
  that imported data is never auto-accepted.
- The same modal stays reachable from the task step for task-style lines, preserving
  the current behavior (one task per line) under an explicit "Add as tasks instead"
  secondary action.

### 5.6 Life after the wizard (the superiority part)

- Transaction Documents tab gains a "Missing documents" group rendering open
  requirements with their due chips; uploading there offers "Mark as [requirement]"
  using the existing `intake/classify` response extended with a proposed
  `requirement_id` (§8.6). The proposal is computed by deterministic
  `doc_type`/name matching against the open requirement list, not by asking the LLM
  to pick ids. User confirms the match; nothing auto-links.
- Client and FSBO document views already render Missing / Uploaded / Verified
  states; requirements give "Missing" real backing data instead of nothing.
- `_det_missing_required_docs` in `suggestion_engine.py` gains a requirements-based
  branch: open `missing` requirements due within the closing window produce the
  card, with the existing task-keyword logic retained as fallback for transactions
  created before this feature, which have no requirement rows (correction C10).
  Detector existence stays deterministic.
- Overdue `missing` requirements surface an "Email a request" action that calls the
  existing `POST /ai-emails/compose` (`transaction_id`, `recipient_emails`,
  `intent`) so the draft lands in the existing review queue. Draft only; the §6.4
  safeguards and CC rules apply unchanged.

### 5.7 Quick-create consistency (correction C12)

The quick-create modal (Workflow A) creates the same transaction object without the
wizard. So testers never see two classes of files, requirement instantiation lives in
one server-side service function: the wizard path passes its confirmed rows; the
quick-create path (and any other non-wizard create that generates tasks) instantiates
the unmodified system defaults for the use case. Both paths produce rows in
`transaction_document_requirements`; only the wizard path has had human review at
create time, which is fine because every row remains editable on the Documents tab.
(Decision D7.)

---

## 6. Review Your Task List: Upgrades

The existing `ReviewTasksStep` keeps its structure (milestone grouping, real planner
preview, include/exclude with undo, warnings, explicit-add AI suggestions). Three
additions:

### 6.1 Relative due-date editing and related compliance item

- The per-task edit popover (today: absolute date input) becomes the shared
  `RelativeDateRuleEditor`: Specific date, or Days stepper + Before/After + Relative
  to (Timeline deadline, another task, or a checklist document). The planner already
  expresses every template task this way internally (`float_days`, `dep_task_ids`,
  `day_basis`); this UI finally exposes it instead of flattening to a date.
- `_TaskOverride` gains an optional `basis` object next to the existing `due_date`
  override (§8.3). Preview echoes the resulting `due_basis` string so the row
  immediately shows "3 days after Inspection Response Deadline".
- A "Related compliance item" dropdown (optional) selects one of the checklist rows
  from the previous step. Because requirement ids do not exist until commit, the
  selection is stored against the requirement's **client correlation key** and
  resolved to the real id during the commit sequence (§8.4). Rendered as a small
  neutral chip on the task row here, in My Task Queue, and on the transaction Tasks
  tab. Completing a task linked to a requirement whose status is still `missing`
  nudges: "Did this produce the [Inspection Report]? Mark it uploaded" (one click,
  dismissible).

### 6.2 Auto-Email toggle

Grounding: the merged Auto-Emailing system (queue at `/ai-emails`, compose endpoint,
templates, tenant thresholds, runners in `app/api/v1/ai_emails.py`).

- Eligibility, deterministic and visible (correction C3): the toggle renders only
  when the task's `target` (Buyer, Seller, Co-op Agent, Loan Officer, Title, ...)
  resolves to a confirmed party or vendor contact **with an email address** in this
  wizard's state. `completion_method` is not used for template tasks because task
  templates do not carry one. Ineligible tasks show nothing (no disabled mystery
  toggles).
- The toggle row states exactly what will happen: "When this task comes due, I draft
  the email to [name, address] for your review. Nothing sends without approval."
  Default **off** (Decision D2). Persisted into `task.metadata_json.auto_draft_email`
  via the generate payload (§8.3).
- Runtime (correction C4): a new sweep function in `task_notification_service`,
  invoked from the same daily trigger that already calls `send_daily_summaries`
  (admin endpoint `POST /ai-emails/reminders/run` plus its cron), finds due tasks
  with the flag and files a draft through the existing compose service with task and
  transaction context, CCing the responsible owner per requirements §6.3.
  Idempotency: the sweep records `(due_date)` markers in
  `task.metadata_json.auto_draft_log` and never creates a second draft for the same
  task and due date. Approval, edit, regenerate, discard, audit logging, and the AI
  disclaimer all come from the already-merged system; this feature adds a trigger,
  not a new email path. Tasks with a pending auto-draft show the amber "Draft ready"
  chip linking to `/ai-emails`.
- Rows with the flag get the `Auto-Email` badge (blue triad chip) exactly where
  ListedKit puts theirs.

### 6.3 Search and density

- A search input filters tasks by name/target as you type, next to the existing
  milestone grouping. Optional typing, mirrors §5.3.
- Task rows gain a one-line description under the name (template `description`
  exists on `TaskTemplate` but is not in the preview response today; §8.3 adds it),
  truncated with expand-on-click.

---

## 7. Workspace and Navigation Polish

### 7.1 Public 5-phase stepper over 9 internal steps

Testers think in phases, not in our internal state machine. `WizardTopStepper` maps:

| Public phase | Internal steps |
|---|---|
| 1 Upload | `upload`, `parsing` |
| 2 Review details | `address`, `purchase`, `missing`, `confirm` |
| 3 Timeline | `timeline` |
| 4 Compliance | `checklist` |
| 5 Tasks & create | `review` |

"Step 2 of 5" plus five dots; the active dot fills proportionally as internal steps
advance (parsing shows phase 1 still active, like ListedKit's screen 30/31). In
manual mode phase 1 is `upload` only; the mapping is a static table in
`wizardTypes.ts` keyed off `WIZARD_STEPS`, which remains the single source of truth
for ordering. Back navigation continues to step through internal steps, and the
visited-steps jump list in the stepper keeps working because it already derives from
`WIZARD_STEPS` (NewTransactionWizard.tsx:6137).

### 7.2 Per-step CTAs and navigation specials

- Existing labels stay. New ones: timeline = "Confirm Timeline" (disabled until the
  anchor gate is confirmed, §4.2), checklist = "Confirm Checklist", and the final
  step keeps "Approve & Create Transaction".
- `onPrimary` (NewTransactionWizard.tsx:6094) gains a `timeline` branch for the
  anchor-gate guard; other new steps use the generic `next_step` path.
- The `returnToConfirmAfterEdit` shortcut (line 6121) must keep its current meaning:
  it fires only when the user jumped backward from `confirm` via an Edit control,
  and it returns them to `confirm`. It must **not** trigger on normal forward
  navigation out of `timeline` or `checklist` (correction C13). A regression test
  covers this (§11.2).
- The post-create success state adds an "Open Transaction File" primary button
  (navigates to `/transactions/:id`) alongside the existing redirect behavior,
  matching ListedKit's closing beat and requirement §2.4's deep-linking.

### 7.3 Right pane policy

- PDF evidence viewer: `parsing` through `timeline` (timeline rows cite contract
  pages, so the viewer earns its place there).
- Transaction Timeline rail: `checklist` and `review`.
- The existing large-screen gating and 50/50 split logic stays.

---

## 8. Backend and API Plan

All endpoints follow existing router/repository/service conventions, tenant scoping,
and audit logging. Provider-touching paths log the active provider (req §8.1a).

### 8.1 Migration: document requirements

`supabase/migrations/<ts>_document_requirements.sql`:

```sql
CREATE TABLE document_requirement_templates (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       uuid NULL REFERENCES tenants(id),      -- NULL = system row
  name            text NOT NULL,
  description     text,
  doc_type        text,                                  -- aligned with documents.doc_type
                                                         -- / document_template_registry
  use_cases       text[] NOT NULL,                       -- e.g. {buy_fin,buy_cash}
  conditions_json jsonb NOT NULL DEFAULT '[]'::jsonb,    -- compiled predicates, same
                                                         -- grammar as task templates
  due_days        int,
  due_direction   text CHECK (due_direction IN ('before','after')),
  due_anchor      text,                                  -- canonical anchor key, e.g.
                                                         -- 'contract_acceptance_date'
  sort_order      int NOT NULL DEFAULT 0,
  is_active       boolean NOT NULL DEFAULT true,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE transaction_document_requirements (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id            uuid NOT NULL REFERENCES tenants(id),
  transaction_id       uuid NOT NULL REFERENCES transactions(id),
  template_id          uuid NULL REFERENCES document_requirement_templates(id),
  name                 text NOT NULL,
  description          text,
  doc_type             text,
  due_date             date,
  due_days             int,
  due_direction        text,
  due_anchor           text,
  status               text NOT NULL DEFAULT 'missing'
                       CHECK (status IN ('missing','uploaded','waived')),
  matched_document_id  uuid NULL REFERENCES documents(id),
  source               text NOT NULL DEFAULT 'system'
                       CHECK (source IN ('system','condition','user','user_template')),
  sort_order           int NOT NULL DEFAULT 0,
  created_by           uuid,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON transaction_document_requirements (transaction_id);
CREATE INDEX ON transaction_document_requirements (tenant_id, status);
```

A second seed migration inserts the system template library (tenant_id NULL only,
re-runnable with the same replace-only-system-rows convention as the task re-seed).

### 8.2 Preview extension: timeline and requirements blocks

Extend the existing dry-run rather than adding parallel endpoints, so preview ==
commit stays one invariant. `POST /api/v1/transactions/preview-tasks` already takes a
full `TransactionCreateRequest` and builds a transient Transaction (verified), which
means **timeline edits that map to existing fields need no new transport**: the
wizard simply rebuilds the request with the edited dates and term day-counts and
re-previews. The request gains exactly one optional field:

```json
{ ...TransactionCreateRequest,
  "extra_deadlines": [
    { "client_key": "d-1", "name": "Septic inspection",
      "days": 10, "direction": "after", "anchor": "contract_acceptance_date" }
  ]
}
```

The response gains two blocks, both produced inside the shared pure planner in
`task_generation_service.py` (deterministic, no LLM):

```json
{
  "tasks": [ ...unchanged, plus "description" per item... ],
  "timeline": [
    { "key": "inspection_deadline", "label": "Home Inspection Deadline",
      "date": "2026-03-20", "basis_kind": "term",
      "basis": "5 days after Date of Acceptance",
      "anchor": "contract_acceptance_date", "days": 5, "direction": "after",
      "source": "computed", "editable": "days|date" },
    { "key": "custom:d-1", "label": "Septic inspection", "date": "2026-03-25",
      "basis_kind": "rule", "basis": "10 days after Date of Acceptance",
      "source": "user", "editable": "rule|date" }
  ],
  "requirements": [
    { "client_key": "r-emd", "template_id": "...",
      "name": "Earnest Money Deposit Receipt", "doc_type": "emd_receipt",
      "description": "...", "due_date": "2026-03-15",
      "basis": "day of acceptance", "source": "system" }
  ],
  "summary": { ... }
}
```

`editable` tells the frontend which edit modes the row supports (§4.3), so the UI
cannot offer a rule it has nowhere to store.

### 8.3 Generation payload extensions (exact shapes, correction C11)

`_TaskOverride` (today `{ template_id, due_date, target }`) gains:

```
basis: { days: int, direction: 'before'|'after',
         anchor_kind: 'timeline'|'task'|'requirement', anchor_key: str } | None
auto_draft_email: bool | None
related_requirement_key: str | None   # client correlation key, resolved server-side
```

`_AddedTask` (today `{ name, description, target, due_date, automation_level,
ai_rationale }`) gains:

```
kind: 'task'|'deadline' = 'task'
basis: { days, direction, anchor_kind, anchor_key } | None
auto_draft_email: bool | None
related_requirement_key: str | None
```

`_TaskGenerateRequest` gains `requirement_id_map: dict[str, str]` (client key →
created requirement id), supplied by the wizard from the bulk-insert response so the
service can resolve `related_requirement_key` into
`task.metadata_json.related_requirement_id`. When the map lacks a key (bulk failed,
§8.4), the service stores the unresolved key as
`metadata_json.related_requirement_key` so a later repair can re-link; nothing is
silently dropped.

The planner resolves every `basis` to a date at plan time (business-day and holiday
rules included). The preview response item gains `description` (from
`TaskTemplate.description`) so §6.3 needs no extra call.

### 8.4 Requirements CRUD and the corrected commit sequence

Endpoints (role gate identical to task generate: Agent, TC, Team Lead, Admin):

- `POST /api/v1/transactions/{id}/document-requirements/bulk`: array of confirmed
  rows, each with its `client_key`; response maps `client_key` → created id.
  Idempotency: the request carries a client-generated `commit_id` UUID (held in
  wizard state and included in the persisted draft payload, correction C2); the
  server stores it in an idempotency column and returns the existing rows on replay
  instead of double-inserting.
- `GET /api/v1/transactions/{id}/document-requirements`
- `PATCH /api/v1/transactions/{id}/document-requirements/{req_id}` (edit, waive,
  match a document, unmatch).
- All writes audit-log with before/after state per requirements §10.3.

Corrected wizard commit sequence (extends the verified sequence at
NewTransactionWizard.tsx:3132):

1. Create transaction (unchanged).
2. Pinned note, parties, vendor-save prompt (unchanged).
3. Link wizard documents (unchanged).
4. **Bulk-create requirements** with `commit_id`, including `matched_document_id`
   for rows the user matched in §5.3 (ids now exist from step 3). Returns the
   `client_key → id` map.
5. Optional e-sign queue (unchanged).
6. Generate tasks, passing `requirement_id_map` from step 4 plus the extended
   overrides and added tasks.
7. Refresh, clear drafts, navigate (unchanged).

Failure handling: if step 4 fails, the flow continues (transaction and tasks must
not be stranded), tasks persist their `related_requirement_key` unresolved, and the
success screen shows a retry banner ("Checklist could not be saved, retry"). Retry
re-posts the same bulk payload with the same `commit_id` (safe) and then calls a
small `POST .../document-requirements/relink` that resolves any tasks still holding
`related_requirement_key`.

### 8.5 Checklist file parsing

`POST /api/v1/ai/parse-checklist`: accepts a direct multipart upload (PDF/TXT/CSV)
or a raw text body; returns `{ items: [{name, description, due_hint}] }`. The file
is parsed and discarded; it is **not** persisted as a Document and never attaches to
the transaction (correction C15). CSV/TXT parse deterministically (header detection,
line split). PDF goes through the existing OCR + provider path with a constrained
extraction prompt. Response rows are proposals only; the audit log records the
provider used. Rate-limited like other AI routes.

### 8.6 Intake classify extension

`POST /api/v1/ai/intake/classify` response gains optional
`proposed_requirement_id` + `proposed_requirement_name`, computed by deterministic
`doc_type`/name matching against the target transaction's open requirements (the
LLM is not asked to pick ids). The Documents tab upload flow surfaces it as a
confirm chip.

### 8.7 Auto-draft sweep (correction C4)

New `create_auto_drafts(supabase, tenant_id)` in
`app/services/task_notification_service.py`, called by the same daily trigger that
calls `send_daily_summaries` (admin endpoint `POST /ai-emails/reminders/run` and its
cron). For each due, non-completed task with `metadata_json.auto_draft_email` and a
resolvable recipient, and no `auto_draft_log` marker for the current due date: call
the compose service (`transaction_id`, `recipient_emails`, intent built from the
task name/description), file the draft in the review queue, write the marker, audit
log. The runner's response gains a `drafts_created` count so the admin endpoint
remains a complete manual test surface.

---

## 9. Frontend Component Plan

### 9.1 New components

| Component | Purpose |
|---|---|
| `WizardTimelineStep` (in `NewTransactionWizard.tsx` or extracted) | §4: anchor gate + deadline list + cascade summary |
| `RelativeDateRuleEditor` | Shared popover/modal body: Specific date vs Days stepper + Before/After + Anchor dropdown, honoring the row's `editable` modes | 
| `WizardChecklistStep` | §5: requirement cards, search, match picker, add/edit modals |
| `ChecklistImportModal` | §5.5: Upload Document / Paste Text tabs, proposal review list, add-as-documents or add-as-tasks |
| `TransactionTimelineRail` | §4.4: compact read-only timeline card for the right pane |
| `AutoEmailToggleRow` | §6.2: eligibility-aware toggle with recipient preview |

### 9.2 Modified

- `wizardTypes.ts`: add `timeline`, `checklist` to `WizardStep`/`WIZARD_STEPS`/
  `STEP_LABELS`; timeline and requirement state slices + reducer actions; the
  public-phase mapping table; a `commit_id` field in wizard state; draft schema
  version bump to v2 carrying the new slices in both localStorage and `wizard_runs`
  payloads. v1 drafts restore to their saved step unchanged; the new steps
  initialize fresh from preview data on first entry (correction C13).
- `WizardStepper.tsx`: 5-phase public model (§7.1).
- `NewTransactionWizard.tsx`: step renderers, `onPrimary` timeline branch, right-pane
  policy, the corrected commit sequence (§8.4) with retry banner, and the
  `returnToConfirmAfterEdit` guard left untouched but covered by a regression test.
- `ReviewTasksStep.tsx`: rule editor swap, related-compliance dropdown (client keys),
  Auto-Email badge/toggle, search, descriptions from the extended preview.
- `useWizardApi.ts`: extended preview types (`timeline`, `requirements`,
  `extra_deadlines`, `description`), requirements bulk/CRUD hooks,
  `useParseChecklist`.
- Transaction Documents tab (`/transactions/:id`): Missing documents group (§5.6).

### 9.3 Visual specification (style guide application)

- Layout from the ListedKit comps; styling exclusively from `STYLE_GUIDE.md`:
  `ve-*` tokens, hairline borders, radii per component scale, soft shadows.
- Type: serif step titles at 22 px, section serif 16 px semibold, body 13 px, mono
  kickers 9 px/1.8 px tracking, all dates and money `tabular-nums`. Wizard body type
  stays at the app's 13 to 14 px scale (the Round 6 lesson: do not oversize).
  **[SUPERSEDED by Part II §19 / Decision D13: Jan's 2026-06-11 direction replaces
  the Round 6 downscale with the v2 comfort scale, pending Jake's side-by-side
  approval. Until D13 is decided, the built Part I wizard remains on this scale.]**
- Basis chips: muted text, never color-only meaning. Status chips use the paired
  triads (`ve-green-bg/border/text` for Uploaded, `ve-amber-*` for moved dates,
  `ve-blue-*` for Auto-Email, `ve-neutral-*` for waived).
- AI-derived surfaces use the champagne accent system (`ve-ai-bg`/`ve-ai-border`),
  not robots or glows; the checklist banner follows §10 of the style guide.
- Interactive targets at 48 px minimum; every icon button gets an aria-label;
  steppers and dropdowns are keyboard-operable; popovers trap focus. Find-button
  aria-labels keep the established "Show document source (page N)" pattern to avoid
  test-query collisions.
- Empty states are honest and specific per §11 of the style guide ("No deadlines
  could be derived yet. Add one or go back to review dates."). No sample rows, ever.

---

## 10. Superiority Scorecard (after this plan)

| Capability | ListedKit | Velvet Elves |
|---|---|---|
| Live extraction log | Field-level lines | Field-level lines, persisted events, click-to-source |
| Source verification | Page citation + viewer | OCR-region highlight, snippet strip, cross-document text locate, per-party-detail finds |
| Extraction QA | None visible | Two-pass double-check with blocking acknowledge gate |
| Anchor gate | Yes | Yes, with in-document source proof |
| Timeline with relative rules | Yes | Yes, plus business-day/holiday-aware cascade recompute and a visible diff |
| Compliance checklist | Static intake list | Persistent requirement rows driving Documents tab, client portal statuses, deterministic AI suggestions, and draft chase emails |
| Own checklist import | PDF/TXT/CSV/paste | Same formats, plus row-level review before accept and a tasks-or-documents choice |
| Task preview | Opaque generated list | Real planner dry-run, preview == commit, include/exclude, basis editing, warnings |
| Auto-Email | Toggle, behavior opaque | Toggle with named recipient, drafts into a human review queue with audit trail, never silent sends |
| Signatures | Not visible | Detection + e-sign queue on create |
| Drafts | Not visible | Browser resume + cross-device server resume |
| Manual fallback | Not visible | Full manual path behind the same review gates |

---

## 11. Testing and Validation Plan

### 11.1 Tester-facing UI validation (primary)

I will extend `WIZARD_TESTING_GUIDE.md` with new sections in the established
"How to test / Expected result" format, mouse-only, using one multi-page test
contract PDF. New sections:

- **Timeline step**: anchor card appears with the extracted date and a working View
  in Document; Looks Good enables the list and the CTA; editing the anchor moves
  dependent rows and shows the "N dates moved" summary; the edited anchor also shows
  changed on the purchase step and confirm table (single source of truth); derived
  rows offer Days stepper + date only; Add deadline with a relative rule shows the
  correct server-computed date; removed deadline shows Undo; core dates show no
  remove control; no undated rows render anywhere; Confirm Timeline advances.
- **Compliance checklist**: list renders for the chosen use case; with a single
  uploaded contract the primary-contract row is checked Uploaded with the real file
  name; with two uploads nothing is auto-checked and "Mark as uploaded" opens the
  picker; Edit changes a due rule via dropdowns/steppers only; Add Document works;
  search filters; Remove + Undo works; the import modal accepts a small CSV and a
  pasted list, shows the review list, and only adds after the confirm click.
- **Task step upgrades**: a task edit shows the relative rule prefilled; switching
  anchor updates the shown date from the server preview; the related compliance
  dropdown lists exactly the checklist rows; the Auto-Email toggle appears only on a
  task whose target has a known recipient and names that recipient; the badge
  renders.
- **Create and continuity**: Approve & Create succeeds; Open Transaction File lands
  on the transaction; Documents tab shows the Missing group with the same rows
  confirmed in the wizard; a simulated checklist-save failure shows the retry
  banner, and retry completes without duplicate rows; uploading a matching file
  later offers the confirm chip; after a flagged task comes due and the admin
  reminders run is triggered, exactly one draft appears in `/ai-emails`, CC'd
  correctly, and nothing was sent.
- **Quick-create parity**: a file created from the quick-create modal also shows the
  default Missing documents group on its Documents tab.
- **Resume**: refresh mid-timeline and mid-checklist restores both (draft v2); an
  old v1 draft resumes at its saved step with the new steps starting fresh.
- **Edit hop-back**: from confirm, jump back via an Edit control, press Continue,
  land on confirm (not timeline); then walk forward normally through timeline and
  checklist.
- **Empty states**: a no-date document produces the honest anchor empty state;
  manual mode reaches both new steps with picker-driven entry only.

Each section gets explicit pass criteria so a real-estate tester can mark pass/fail
without reading code.

### 11.2 Automated tests

- Frontend (vitest, msw): WizardFlow integration extensions for both new steps and
  the upgraded editors; unit tests for `RelativeDateRuleEditor` mode gating off
  `editable`, stepper phase mapping, draft v2 + v1 migration, checklist import
  review list, `returnToConfirmAfterEdit` regression (correction C13), commit
  sequence ordering (requirements bulk observed before generate in the mock server
  call log), retry-banner flow.
- Backend (pytest): planner timeline block correctness (anchor edit cascade,
  term-field mapping, business-day basis, `editable` flags), requirements preview ==
  commit parity, conditions gating (`has_hoa` requirement appears only when true),
  bulk idempotency on `commit_id` replay, `requirement_id_map` resolution plus the
  unresolved-key + relink path, parse-checklist CSV/TXT determinism (PDF path mocked
  at the provider boundary), auto-draft sweep idempotency and recipient resolution,
  classify requirement proposal matching, quick-create default instantiation.
- No live LLM calls and no real `SUPABASE_DB_URL` in tests, per the standing rule.

### 11.3 Visual verification

Per the established method: run the frontend on :5173 against a fresh backend on
:8001, drive each step with the test PDF, capture Chrome-headless screenshots of all
nine internal steps, and compare side by side against `Screenshot_27..51` for layout
and against `STYLE_GUIDE.md` for styling before declaring any step done. No UI is
built blind; Jake reviews each round in his environment as before.

---

## 12. Implementation Phases

Ordered so each phase is independently shippable and UI-testable.

**Phase 1: Timeline step.**
Planner timeline block + `extra_deadlines` + `editable` flags; anchor gate wired to
the shared acceptance-date state; deadline list with mode-gated editing, add/remove,
cascade summary; right-pane policy; stepper 5-phase model; `onPrimary` timeline
branch.
Acceptance: timeline tester section passes; preview == commit holds for edited
terms and custom deadlines; the hop-back regression test passes; all existing wizard
tests stay green.

**Phase 2: Compliance checklist.**
Migrations + seed library (after Jake signs off the library content, D1);
requirements block in preview; checklist step UI with conservative matching;
corrected commit sequence with `commit_id` idempotency and retry/relink;
timeline rail; quick-create default instantiation through the shared service (D7).
Acceptance: checklist and quick-create tester sections pass; a created transaction
returns identical requirement rows via GET; replaying the bulk call creates no
duplicates; no demo rows anywhere.

**Phase 3: Post-wizard checklist surfaces.**
Documents tab Missing group; classify match proposal; `_det_missing_required_docs`
requirements branch with keyword fallback; chase-email draft action.
Acceptance: continuity tester section passes end to end through the UI; a
pre-feature transaction (no requirement rows) still produces the legacy detector
behavior.

**Phase 4: Task editor upgrades.**
`RelativeDateRuleEditor` in ReviewTasksStep; `_TaskOverride`/`_AddedTask` extensions;
`description` in preview; related compliance item via client keys; search.
Acceptance: task tester section passes; an overridden basis survives create and
shows correctly on the Tasks tab; an unresolved requirement link is repaired by the
relink call.

**Phase 5: Auto-Email.**
Toggle + target-based eligibility + badge; `create_auto_drafts` sweep with
idempotent markers; "Draft ready" chip; `drafts_created` in the runner response.
Acceptance: due task with the flag produces exactly one draft in `/ai-emails` per
due date, CC'd correctly, and nothing sends without approval; a second runner
invocation creates nothing new.

**Phase 6: Checklist import upgrade + polish.**
`parse-checklist` endpoint (multipart, file not persisted); `ChecklistImportModal`;
Open Transaction File button; optional idle "did you know" copy if Jake approves it;
final visual pass and testing-guide updates.
Acceptance: import tester section passes; full visual comparison archived.

**Phase 7: Extraction accuracy benchmark and tuning loop (see §14.1).**
Curated contract corpus with golden extractions; scoring harness over the existing
packet parser; per-field accuracy report across both AI providers; prompt/extraction
iteration against the scores; double-check disagreement analytics.
Acceptance: a reproducible accuracy report exists per provider and per field; the
top tester-visible fields (address, parties, price, acceptance date, closing date,
deadlines) meet the agreed floor (D9) on the corpus; re-running the harness after
any prompt change shows no regression.

**Phase 8: Latency measurement and reduction (see §14.2).**
Stage-timing report from the persisted progress events; parallelize per-document
OCR/extraction where currently sequential; poll cadence tuning; perceived-speed
polish on the live feed.
Acceptance: a before/after timing report per stage exists; the agreed end-to-end
budget (D10) is met for the standard single-contract case on the test environment;
the live feed never sits silent longer than the agreed threshold while work is
running.

Dependencies: Phase 2 needs Phase 1's timeline anchors. Phase 4's related-item
dropdown needs Phase 2's requirement rows but its rule editor does not; if
sequencing pressure arises, the rule editor can land with Phase 1's shared
component. Phases 3, 5, 6 are independent of each other once 1 and 2 land. Phases 7
and 8 are independent of all feature phases and can start immediately in parallel;
their measurement baselines should ideally be captured **before** the feature phases
change anything. I will work the phases in order without pausing for direction, and
Jan commits all work himself.

---

## 13. Decisions Needed From Jake

| # | Decision | My recommendation |
|---|---|---|
| D1 | Content of the system requirement library (about 18 documents across the 4 use cases) | I draft it from the task DB, requirements §1.5/§4.10, and the ListedKit document names; Jake approves the table before the seed migration is written |
| D2 | Auto-Email toggle default | Off. The tester sees it work by turning it on deliberately; no surprise drafts |
| D3 | Custom deadline storage | Manual tasks with `metadata_json.kind="deadline"` via the extended `added_tasks` channel (zero new infrastructure, server-resolved dates, visible in queue/calendar today). Alternative is a dedicated deadlines table; defer unless reporting needs it |
| D4 | Public stepper regrouping to 5 phases | Yes; testers count phases, and it matches the comp |
| D5 | Timeline writes onto the create payload | Yes, scoped to what maps 1:1: core dates, `inspection_response_date`, and the term day-count fields. Operational milestone dates (EM Delivered, CD Delivered, etc.) stay out of the wizard |
| D6 | Idle "did you know" cards during parsing | Skip; the live feed is better. Build only if Jake wants the marketing touch |
| D7 | Quick-create files also get default requirement rows (unreviewed, editable later) | Yes; otherwise testers will read quick-created files as missing the checklist feature |
| D8 | Source of the benchmark contract corpus (§14.1) | Jake and his testers supply 10 to 20 representative purchase agreements and counter/amendment packets (their own states' forms, redacted as needed); I add the synthetic edge cases (scans, rotation, missing pages) |
| D9 | Per-field accuracy floor for the tester-visible fields | Proposed: the wizard is not declared superior until address/parties/price/dates score at least 95 percent field-accuracy on the corpus; Jake confirms or adjusts the bar |
| D10 | End-to-end parse latency budget for a standard single contract | Measure first (Phase 8 baseline), then Jake picks the budget from the report; I will not promise a number before measuring |

---

## 14. Beyond the Feature Set: Accuracy and Speed (the superiority insurance)

The feature phases (1 to 6) make the wizard a strict superset of ListedKit's visible
workflow. But "superior" is judged by a tester feeding in a real contract, and two
dimensions decide that experience which no feature list captures: whether the
extraction is *right*, and whether the flow feels *fast*. ListedKit's real moat is
production maturity on exactly these two dimensions ("I can read contracts from all
50 states" is an accuracy claim, not a feature). A feature-superset wizard that
misreads a price or takes twice as long would still lose the comparison. These two
workstreams turn both dimensions from hope into measurement. They are
engineering-internal instrumentation; the tester-visible deliverable remains the UI,
so the UI-testable principle is unaffected.

### 14.1 Extraction accuracy benchmark (Phase 7)

- **Corpus.** 10 to 20 representative purchase agreement packets sourced from Jake
  and his testers (their states' real forms, redacted), plus synthetic edge cases I
  generate: skewed scans, low-DPI photos, rotated pages, missing pages, multi-doc
  packets with counters and amendments (D8). Stored outside the repos if the
  documents are sensitive; the harness reads a local path.
- **Golden answers.** One YAML/JSON file per packet with the expected value for
  every canonical field the wizard displays (address, parties with roles and
  contact details, price, earnest money, financing type, acceptance date, closing
  date, possession, term day-counts, signature status).
- **Harness.** A backend script (pytest-marked `benchmark`, excluded from the
  default suite so CI stays LLM-free) that runs the existing packet-parse service
  against the corpus and scores per-field exact/normalized accuracy, plus
  double-check disagreement frequency. Output: a per-field, per-provider table.
- **Dual-provider comparison.** Requirements §8.1a demands switchable providers; the
  harness runs both OpenAI and Claude and reports them side by side, giving Jake an
  evidence-based default rather than a guess.
- **Tuning loop.** Prompt and extraction-template iteration is done **against the
  scoreboard**, never by feel; any change must not regress the report. The existing
  `SuggestImprovementButton`/`POST /ai/feedback` field-level feedback becomes input
  for which fields to tune next.
- **Definition of done.** The tester-visible core fields meet the D9 floor on the
  corpus. The report is committed (numbers, not the documents) so future changes
  have a baseline.

### 14.2 Latency budget (Phase 8)

- **Measure first.** The packet pipeline already persists timestamped progress
  events (`ParseProgressEvent.at`); a small report script turns them into per-stage
  timings (upload, OCR, pass 1, pass 2 double-check, resolver) across the corpus.
  Baseline is captured before the feature phases change anything.
- **Reduce.** The two known candidates, pending what the baseline shows:
  per-document OCR/extraction parallelism where the pipeline is currently
  sequential, and double-check scope (it must stay for the critical fields per
  requirements §3.4, but its pass-2 prompt can be limited to the fields that
  actually gate the workflow).
- **Perceived speed.** The live feed must never sit silent while work runs; if a
  stage is long, the feed says what is happening (we already have stage events;
  this is cadence tuning, not invention).
- **Definition of done.** The D10 budget, chosen by Jake from the baseline report,
  is met for the standard single-contract case, and no stage regresses silently
  (the timing report runs in the benchmark suite).

---

## 15. Guardrails (restating the non-negotiables)

- Plan only today; no source changes until execution is approved.
- No demo/sample data on real surfaces; honest empty states everywhere.
- AI never auto-accepts external or imported data, never sends email without human
  approval, and never invents checklist or task rows at generation time; existence
  stays deterministic so testers can predict every card.
- Date arithmetic lives in exactly one place, the server planner; the browser never
  computes a deadline it will later persist.
- Layout from the comps, styling from the style guide; `ve-*` tokens only.
- Every deliverable validatable through the UI by a non-developer with a mouse, a
  test PDF, and the updated testing guide.

---
---

# PART II — Active Intelligence and the Modern UI Revision

Date: 2026-06-11 (same-day revision after Jan's review of the Part I build)
Status: PLAN. Part I is implemented and uncommitted; Part II is the next build.

## 16. The Feedback, Taken Straight

Jan's review of the Part I build:

1. The LLM is used only for document parsing. Timeline, checklist, and tasks
   are assembled by deterministic rules, so the wizard EXTRACTS but never
   GENERATES. ListedKit generates its timeline with an LLM; ours only carries
   dates out of the documents. That makes the system passive, an "AI wizard"
   in name only.
2. A true AI wizard should use the LLM actively at every stage and automate
   far enough that manual editing is normally unnecessary.
3. The UI is outdated, and in places the type is too small and strains the
   eyes. STYLE_GUIDE.md itself is flawed and needs to be improved toward a
   modern style that always puts user convenience first.

Both criticisms are accepted and drive this revision.

### 16.1 Why Part I came out deterministic (and what changes now)

The passivity was not an accident; it followed two written constraints:
`requirements.txt` §4.3 ("Upon wizard confirmation: tasks generated strictly
from confirmed use case, confirmed dates, and dependency logic. No AI
creativity at this stage") and the standing predictability decision from the
task-engine work ("a tester can predict exactly which cards appear"). Part I
treated those as a ceiling. The correction in Part II: they are a FLOOR, not
a ceiling. The deterministic skeleton stays, because it is what guarantees a
usable result when a model has a bad day and what keeps E2E flows from
breaking, but a full LLM proposal layer now runs ON TOP of it at every stage,
and the floor is only what the user sees if the intelligence fails.

Two requirement lines need Jake's sign-off to amend (Decision D15):
§4.3's "no AI creativity" wording (AI creativity moves INTO the wizard review,
where a human confirms it; post-confirmation generation stays deterministic),
and the per-step explicit confirmations in §3.5/§3.6 (consolidated into one
final confirmation when confidence is high, see Autopilot, §18.4).

### 16.2 The architecture in one sentence

**The AI proposes everything, the engine verifies everything, the human
confirms once.**

Per stage, three layers:

1. **Deterministic floor** (built in Part I): template library + date
   arithmetic + extraction. Never removed. If the LLM call fails, the wizard
   degrades to exactly what exists today.
2. **LLM proposal layer** (new): one structured "Intake Intelligence" pass
   over the full OCR text that GENERATES the deal's timeline, compliance
   checklist, supplemental tasks, and a plain-English deal brief, every item
   carrying a citation (page + snippet) and a confidence score.
3. **Confidence-gated presentation** (new): items at the "ship it" tier
   (requirements §4.7, default at or above 0.90) arrive pre-confirmed and
   collapsed; items below it surface for one-click review. Manual editing
   remains available but becomes the exception path, not the workflow.

This is also the honest answer to "how do we beat ListedKit's LLM timeline":
they generate; we generate AND verify AND cite. Every AI-generated row in our
wizard can be clicked through to the contract page it came from, and every
date the AI proposes is recomputed by the same arithmetic engine that runs
commit, so a hallucinated date cannot survive into the transaction.

---

## 17. The Intake Intelligence Pass (backend)

One additional LLM call per intake (not per stage), running right after the
existing two-pass extraction inside the packet pipeline, via the existing
provider abstraction (`AIService`, requirements §8.1a, provider recorded in
the audit log per §8.5).

**Where the output lives and when dates materialize (correction P1).** The
pass produces PROPOSALS, not dates. Each proposal carries its rule, citation,
and confidence; the parse result persists them on `ParseDocumentResponse`
exactly like `double_check` does, and the wizard holds the user's
accept/reject decisions in its draft state (keyed by a stable proposal hash,
so refresh or a re-parse never re-bills or loses decisions). Final dates are
NEVER resolved at parse time: the user can still edit the anchor and the
contract terms on later steps, and a parse-time date would silently go stale.
Accepted proposals ride the SAME preview channels Part I built, extended with
`source: 'ai'` and citation fields: timeline proposals as `extra_deadlines`,
checklist proposals as `extra_requirements`, task proposals as added tasks.
The preview planner resolves their rules on every edit, so the Part I anchor
cascade (§4.4) applies to AI rows identically, and preview == commit holds.
This requires a small Part II migration extending the
`transaction_document_requirements.source` CHECK (and the matching schema
patterns and planner values) with `'ai'` (correction P2), plus optional
`source_page`/`snippet`/`confidence` fields on the timeline-entry and
preview-requirement shapes.

### 17.1 Contract

`AIService.generate_intake_intelligence(ocr_text, extracted_facts, use_case)`
returns one structured JSON object:

```json
{
  "timeline": [
    { "label": "Septic evaluation contingency", "kind": "contingency",
      "rule": { "days": 14, "direction": "after", "anchor": "contract_acceptance_date" },
      "date": null, "source_page": 4,
      "snippet": "Buyer shall have 14 days from acceptance to complete a septic evaluation",
      "confidence": 0.93 }
  ],
  "checklist": [
    { "name": "Septic Evaluation Report", "description": "...",
      "due": { "days": 14, "direction": "after", "anchor": "contract_acceptance_date" },
      "source_page": 4, "snippet": "...", "confidence": 0.91 },
    { "waive": "HOA Documents Package", "reason": "No HOA per section 7",
      "source_page": 7, "snippet": "...", "confidence": 0.95 }
  ],
  "tasks": [
    { "name": "Schedule septic evaluation", "target": "Buyer",
      "due": { "days": 3, "direction": "after", "anchor": "contract_acceptance_date" },
      "related_checklist": "Septic Evaluation Report",
      "auto_email_recommended": true, "rationale": "...", "confidence": 0.88 }
  ],
  "watchouts": [
    { "text": "The inspection window is only 5 days", "source_page": 3,
      "snippet": "...", "confidence": 0.92 }
  ]
}
```

The deal brief's summary sentence is deliberately NOT in this contract
(correction P4): prose with embedded numbers is where hallucination hides, so
the summary is CODE-assembled from the verified extracted fields (template
slots), and the LLM contributes only the `watchouts`, each of which must
carry a citation that locates or it is dropped.

### 17.2 The verifier (what makes generation safe)

Every proposal passes a deterministic validator before it reaches the UI:

- **Rules over dates.** A proposal with a `rule` is validated structurally at
  parse time and resolved by `timeline_planner` at preview time (the commit
  arithmetic, weekends and holidays included; see P1). An absolute `date`
  must parse and fall inside the sane window: acceptance minus 30 days to
  closing plus 90 days, or acceptance plus or minus 365 days when no closing
  date exists yet (correction P10). Otherwise the row is demoted to
  needs-review with the reason shown.
- **Citations must land.** `source_page` must exist in the document and the
  snippet must locate in the persisted OCR geometry. The Part I locate logic
  lives in frontend TypeScript (`ocrHighlight.ts`), so the verifier gets a
  small Python equivalent (`app/services/citation_check.py`) running the same
  containment and token-overlap scoring against the stored
  `document_ocr_geometry` LINE rows (correction P9). A proposal whose
  citation cannot be found is demoted, never silently shown as fact.
- **De-duplication against the floor.** Proposals that duplicate a
  deterministic row (fuzzy label + same rule or date) merge into it, which
  also means floor rows GAIN the AI's citation; conflicts (same label,
  different date) surface exactly like Part I double-check disagreements,
  blocking until acknowledged.
- **Name links resolve deterministically.** A task's `related_checklist`
  matches checklist rows by normalized name; when nothing matches, the LINK
  is dropped and the task is kept (correction P10).
- **Waive proposals never auto-apply.** An LLM "this library document does
  not apply, here is the clause" becomes a pre-checked waive suggestion with
  the citation; the row is struck only after the user confirms.

The pass is cached per packet (re-entering a step never re-bills), its
latency is a stage in the Phase 8 report, and the whole pass is skipped
gracefully when the provider errors (floor-only mode, with an honest banner:
"AI generation is unavailable; showing the standard plan").

### 17.3 Cost and tests

One call, bounded output (JSON schema with max items), prompt grounded in
already-OCR'd text (no second OCR). Input is capped to the controlling
contract plus counters/amendments (the resolver's chronology), truncated with
an honest marker when a packet exceeds the cap (correction P10). Tests mock
at the provider boundary with fixture responses including: a valid proposal,
a hallucinated date outside the window, a citation that does not locate, and
a duplicate of a floor row, asserting demote/merge/flag behavior. The Phase 7
benchmark corpus gains golden timeline/checklist items so generation quality
is scored the same way extraction is (the D9 floor applies).

---

## 18. Active Intelligence in the UI

### 18.1 Generated timeline (the ListedKit answer)

The timeline step's list becomes the union of the floor rows and the
verified LLM rows. Each AI row shows its citation chip ("found on p.4: 'Buyer
shall have 14 days…'", click to jump the viewer) and arrives pre-confirmed at
the ship-it tier with a subtle champagne check; below the tier it carries an
amber "verify" chip with one-click confirm. The step header states the work
the AI did: "I read the contract and built this timeline: 9 deadlines, 3 from
contingency language." Custom contingencies the fixed schema never captured
(septic, well, survey, sale-of-home, title objection windows) now appear
without the user typing anything, which is precisely what was missing.

### 18.2 Generated checklist

Same pattern on the checklist step: AI-proposed documents merge with the
library (cited, confidence-gated), and AI waive suggestions appear as
pre-checked strikethrough proposals with the clause citation. The banner
changes from "built from your use case" to "I read the contract: 14 documents
this file needs, 2 specific to this deal, 1 standard item that does not
apply."

### 18.3 Generated tasks

LLM contingency tasks land directly IN the task list at the ship-it tier
(labeled "AI", excludable in one click, related checklist item pre-linked),
instead of the Part I opt-in suggestion cards. Below the tier they stay as
suggestions. Where the AI recommends Auto-Email and a recipient resolves, the
recommendation renders as a champagne "AI recommends Auto-Email" chip with a
one-click enable; the toggle itself never arrives ON, because D2 (default
off, no surprise drafts) stands unless Jake flips it (correction P5). The
§4.3 guarantee holds because commit still only creates what is on the
reviewed list when the user approves.

### 18.4 Autopilot intake (manual editing becomes the exception)

When extraction is double-check-clean and every core field and AI proposal
sits at the ship-it tier, the wizard stops walking the user through seven
review screens. It advances itself, compresses the journey into the Confirm
hub plus the final approval, and presents: the deal brief, the generated
timeline, the generated checklist, the task plan, all pre-confirmed and
collapsed, with the only required actions being "Looks good" on the anchor
(kept separate because it is the root every computed date hangs from) and
"Approve & Create Transaction".

**The party-completeness gate is the known obstacle (correction P3).** The
address step today hard-requires every party to carry a name, email, AND
phone (Audri's rule), and real contracts rarely contain emails or phones, so
on most documents the autopilot will interrupt there. Three things follow:
(1) the metric below is scoped to contracts whose principal parties include
contact details; (2) the party gate is named as an EXPECTED autopilot
interrupt, and when it fires the wizard immediately offers the existing
§3.7 AI public contact search as the proposed fill, so the interrupt is
"confirm the AI's find", not "go type a phone number"; (3) whether the
gate itself relaxes under Autopilot is Jake's call, folded into D15.

Target metric, measured in a WizardFlow integration test (no separate E2E
infrastructure exists): **a clean contract whose parties carry contact
details goes from upload to created transaction in 3 clicks** (Start Intake,
Looks good, Approve), with zero typing. Anything below the confidence tier
interrupts the autopilot exactly where attention is needed, and only there.
Per-step confirmations collapse into the single final approval; this is the
§3.5/§3.6 amendment that needs Jake's sign-off (D15).

### 18.5 The wizard command bar (natural language editing)

Grounded in requirements §8.2 (natural-language task creation) and Workflow F:
a persistent command input at the bottom of the wizard's left pane:

- "add a septic inspection deadline 14 days after acceptance"
- "make the EMD receipt due Friday"
- "turn on auto-email for every buyer task"
- "waive the home warranty item"

The LLM parses the utterance into a typed command (a closed schema of intents
mapping 1:1 onto the existing reducer actions and rule editors); the wizard
shows a preview chip ("Add deadline 'Septic inspection', 14 days after Date
of Acceptance → Mar 16") that applies on click and undoes in one click.
Unparseable input gets an honest "I couldn't map that; try …". Execution is
deterministic; only the intent parsing is LLM. This single control removes
most remaining reasons to touch a form.

### 18.6 The deal brief

A serif, three-sentence plain-English summary of the deal at the top of the
Confirm hub and the timeline step, plus up to three "watchouts" (tight
windows, missing signatures, unusual terms). Consistent with the §17.1
contract (correction P4): the summary is code-assembled from the verified
extracted fields, and only the watchouts are LLM-written, each citing a
source that locates or it is dropped. Display-only, high perceived
intelligence, near-zero risk.

---

## 19. The Modern UI Revision and STYLE_GUIDE v2

### 19.1 What is wrong, concretely

An audit of the built wizard against Jan's critique:

| Offender | Today | Problem |
|---|---|---|
| Mono kickers | 9px, 1.8px tracking | Below comfortable legibility; reads as decoration |
| Chips/badges | 9.5 to 10.5px | Squinting territory, yet used for MEANING (confidence, status) |
| Body / inputs | 13 to 14px | At the low edge for long review sessions |
| Basis/citation lines | 12px muted #7A7A7A | Small AND low-contrast: the eye-strain combination |
| Section headers | 15 to 17px | Hierarchy too flat against 13px body |
| Cards | 6px radius, hairlines everywhere | Reads dated next to current product design |

The Round 6 history is acknowledged: Jake scaled the wizard DOWN to the app's
13 to 14px body in June. Jan's direction now supersedes that, and because it
changes the whole app's feel it ships as a STYLE_GUIDE revision with a
side-by-side screenshot approval round for Jake (D13), wizard first, app-wide
after approval. This plan does not quietly re-litigate Round 6; it puts the
conflict on the table with a concrete proposal.

### 19.2 STYLE_GUIDE v2: the comfort scale

Revisions to the guide itself (a full edited STYLE_GUIDE.md is the
deliverable; this is the spec):

- **Type scale (the eye-strain fix).** Body 13.5 → **15px** (line-height
  1.6); secondary 12.5 → 13.5px; field labels 11.5 → **12.5px**; mono kickers
  9 → **12px** (uppercase mono reads comfortably at 12; tracking 1.5px);
  chips minimum **12px**; hero serif 22-26 → **28px**; section serif 16-18 →
  **20px**; money/dates in tables 13.5 → 15px tabular. New hard rule:
  **no text below 12px anywhere, no exceptions** (the kicker size above was
  corrected from an earlier 10.5px draft precisely because it violated this
  rule, correction P6), and no meaning carried by the smallest size, ever.
- **Contrast.** Muted ink #7A7A7A is reserved for 14px and larger; below
  that, muted becomes #5C5F62. All text passes WCAG AA at its actual size,
  audited.
- **Space.** Card padding 16/20 → 20/24; section rhythm 24 → 32; list rows
  minimum height 52px; the 48px interactive minimum (req §9.1) enforced, not
  aspirational.
- **Shape and depth.** Cards 6 → **12px radius** (modals 16), one soft
  elevated shadow token replacing per-component ad-hoc shadows, hairlines
  kept but fewer (whitespace separates; borders only where grouping needs
  them).
- **Motion.** A short standard: 150ms ease-out for state, 250ms for
  enter/exit, skeletons for every async surface, a single shimmer for AI
  work in progress. No bounce, no parade.
- **AI surfaces (§10 rewrite).** The champagne system gains: the confidence
  ring (one glyph for ship-it/review/low), the citation chip (page + first
  words, always clickable), the pre-confirmed check, and the autopilot
  banner. These are the brand: the AI shows its work.
- **New §16 Comfort and Convenience.** The codified principle Jan asked for:
  every flow must be completable mouse-only; typing is only ever for naming
  things; defaults always proposed; destructive actions always undoable
  inline; nothing meaningful below 12px; the user confirms once, not per
  screen.

### 19.3 Wizard visual modernization (applying v2)

- Step surfaces rebuilt on the v2 scale and shape tokens; the top bar gains a
  slim progress shimmer while the intelligence pass runs.
- The timeline step gains a horizontal mini-timeline visualization (dots on a
  dateline from acceptance to possession, today marker, hover highlights the
  row), which ListedKit does not have.
- Checklist cards get a status ring (missing/uploaded/waived) instead of
  text-only chips; the live extraction feed gets per-find icons and a typing
  indicator.
- The Confirm hub becomes the deal-brief hero plus collapsed green sections
  (Autopilot) rather than a long table wall.
- **Rollout mechanics (correction P8).** "Wizard first" cannot mean editing
  the existing `ve-*` token VALUES, because those are global: changing the
  body size, radii, or shadows in `tailwind.config.js` restyles the whole app
  instantly. The v2 scale therefore ships as NEW parallel tokens and classes
  consumed by the wizard components first; the global remap of the old tokens
  happens only after Jake approves D13.
- Verification per the standing method: render on :5173 against a fresh
  backend, Chrome-headless screenshots of all steps, side-by-side against the
  ListedKit comps AND against current production, delivered to Jake with the
  D13 decision. No UI ships blind.

---

## 20. Revised Phases (continuing from Part I)

**Phase 9: Intake Intelligence pass.** `generate_intake_intelligence` on
`AIService` (both providers), the verifier (`citation_check.py`, window
check, dedupe/conflict, name-link resolution), packet-pipeline integration +
persistence on `ParseDocumentResponse` + floor-only fallback, the `'ai'`
source migration (CHECK constraint + schema patterns + planner values, P2),
provider audit logging, mocked fixture tests (valid, hallucinated-date,
dead-citation, duplicate).
Acceptance: with the provider mocked, the parse status response carries
statically verified PROPOSALS (rules + citations + confidence, no resolved
dates, P1); a dead citation never renders as fact; provider failure yields
the Part I floor with the honest banner.

**Phase 10: Generated timeline + checklist + tasks in the UI.** Proposals
ride the existing preview channels with `source: 'ai'` so dates resolve at
preview and the anchor cascade applies to AI rows (P1); merge layers on all
three steps, citation chips, confidence states, pre-confirmed ship-it tier,
waive proposals, conflict gates, draft-v2 persistence of accept/reject
decisions.
Acceptance: a fixture contract with a septic clause shows the septic deadline,
document, and task with citations, none of them typed by the user; the
testing guide gains §15 with the mouse-only script.

**Phase 11: Autopilot intake.** Confidence-gated auto-advance, the condensed
Confirm hub, interrupt-only-below-tier behavior, the 3-click E2E test.
Acceptance: clean fixture = 3 clicks, zero typing; a low-confidence field
interrupts exactly once, at the right step.

**Phase 12: Command bar + deal brief.** Typed-intent schema, preview-then-
apply, undo, honest failure copy; the brief + watchouts with citations.
Acceptance: the four example utterances in §18.5 each produce the previewed
mutation; an unmappable utterance produces no mutation.

**Phase 13: STYLE_GUIDE v2 + wizard modernization.** The revised
STYLE_GUIDE.md text, token changes, wizard application, mini-timeline,
screenshot approval round with Jake (D13) before app-wide rollout.
Acceptance: no text below 12px in the wizard; the AA contrast audit passes;
Jake approves the side-by-sides.

**Phase 14: Intelligence quality and cost.** The benchmark corpus gains
golden generated-timeline/checklist items (Phase 7 harness extended); the
latency report gains the intelligence-pass stage; a per-intake token/cost
line lands in the report (D14 budget).

Order: 9 → 10 → 11 → 12; 13 can run in parallel from the start; 14 runs
against everything.

---

## 21. New Decisions for Jake

| # | Decision | Recommendation |
|---|---|---|
| D11 | Intake Intelligence pass on by default | Yes; floor-only mode remains the automatic fallback |
| D12 | Autopilot threshold source | Reuse the §4.7 confidence tiers (admin floor, team-configurable) rather than inventing a wizard-specific knob |
| D13 | STYLE_GUIDE v2 comfort scale (supersedes the Round 6 downscale) | Approve from side-by-side screenshots; wizard first, app-wide after |
| D14 | Per-intake AI cost budget | Set from the first Phase 14 report; one bounded call per intake by design |
| D15 | Requirements amendments: §4.3 wording, §3.5/§3.6 consolidated single confirmation under Autopilot | Approve; the human-confirms guarantee is kept, relocated to one decisive approval |
| D16 | Command-bar scope at launch | The closed intent schema in §18.5; free-form agentic editing later |

## 22. What Part II Deliberately Keeps

- The deterministic floor and preview == commit. Generation proposes; it
  never becomes the arithmetic.
- Citations on everything AI-made; the click-to-source viewer is the trust
  story ListedKit cannot match.
- Draft-only email, the §6.4 safeguards, audit logs with provider names.
- UI-testability: every new behavior has a mouse-only script, and the
  fixture-driven intelligence pass keeps E2E predictable (the LLM is mocked
  in tests; live quality is measured by the Phase 7/14 benchmark instead).

---

## 23. Part II Review Corrections (2026-06-11 workflow/logic pass)

A source-verification review of Part II against the BUILT Part I code, in
the same spirit as §0.1. All corrections are already folded into the text
above; this log records what was wrong and why, so a reviewer can audit the
reasoning.

- **P1, the stale-date flaw (serious).** §17 originally resolved AI rule
  proposals at parse time. The user can edit the anchor date and the
  contract terms on later steps; a parse-time date silently goes stale, and
  Part I routes every date through the preview pipeline for exactly this
  reason. Corrected: the pass emits rules + citations + confidence only;
  accepted proposals ride the existing `extra_deadlines` /
  `extra_requirements` / added-task channels (extended with `source: 'ai'`
  and citation fields), dates materialize at preview, the anchor cascade
  applies to AI rows, preview == commit holds. Phase 9/10 acceptance
  reworded to match.
- **P2, `'ai'` is not a legal source (would fail at commit).** Verified: the
  Part I migration constrains `transaction_document_requirements.source` to
  `('system','condition','user','user_template')`, and the bulk schema and
  planner mirror it. AI-generated checklist rows would violate the CHECK on
  insert. Corrected: Phase 9 includes a small amending migration plus the
  schema-pattern and planner updates.
- **P3, the 3-click metric collided with the party-completeness gate.** The
  address step hard-requires name + email + phone for every party (Audri's
  rule, verified in `canAdvance`), and real contracts rarely contain emails
  or phones, so Autopilot would interrupt there on most documents. Corrected
  (§18.4): the metric is scoped to contracts whose parties carry contact
  details; the party gate is named an expected interrupt that immediately
  offers the existing §3.7 AI public contact search as the proposed fill;
  whether the gate relaxes under Autopilot is folded into D15 for Jake.
- **P4, internal contradiction on the deal brief.** §17.1 had the LLM
  writing the summary prose (embedded numbers are where hallucination
  hides) while §18.6 claimed facts came from verified extraction. Corrected:
  the summary is code-assembled from verified fields; the LLM writes only
  the watchouts, each requiring a locating citation or it is dropped.
- **P5, auto-email recommendation conflicted with D2.** §18.3's "auto-email
  pre-recommended" read as the toggle arriving ON, contradicting D2 (default
  off, no surprise drafts). Corrected: the recommendation is a champagne
  chip with one-click enable; the toggle never arrives ON unless Jake flips
  D2.
- **P6, type-scale self-contradiction.** §19.2 set mono kickers to 10.5px
  while declaring "no text below 12px anywhere". Corrected: kickers go to
  12px; the 12px floor stands with no exceptions.
- **P7, Part I §9.3 disagreed with Part II §19.** Part I's visual spec still
  mandated the 13 to 14px Round-6 scale as a standing rule. Corrected with
  an explicit SUPERSEDED marker pointing at §19/D13, including the interim
  state (the built wizard stays on the old scale until D13 is decided).
- **P8, "wizard-first" rollout was mechanically impossible as written.**
  `ve-*` token values are global; editing them restyles the whole app at
  once. Corrected (§19.3): v2 ships as new parallel tokens/classes consumed
  by the wizard first; the global remap happens only after D13 approval.
- **P9, the verifier cited machinery that does not exist server-side.** The
  Part I locate logic is frontend TypeScript. Corrected: a small Python
  equivalent (`citation_check.py`) runs the same containment and
  token-overlap scoring against the persisted `document_ocr_geometry` rows.
- **P10, smaller specification fixes.** Window check gains a fallback when
  no closing date exists (acceptance plus or minus 365 days);
  `related_checklist` matches by normalized name and drops only the link,
  never the task; command-bar relative phrases ("Friday") resolve to dates
  in code from structured intent fields, never by the LLM; proposals and
  accept/reject decisions persist in the draft payload keyed by a stable
  proposal hash (no re-billing, no lost decisions on refresh or re-parse);
  the intelligence pass input is capped to the controlling contract plus
  amendments with an honest truncation marker; "six review screens" was
  seven; the 3-click metric is measured by a WizardFlow integration test
  because no separate E2E infrastructure exists.

**Verified as sound (not errors):** `GET /api/v1/confidence/` is readable by
any authenticated user, so the wizard can read the §4.7 tiers and D12 stands
as designed; persisting the generated blocks on `ParseDocumentResponse`
follows the existing `double_check` precedent; all four §18.5 command-bar
examples map onto reducer actions and editors that exist in the Part I
build; Part II's section and phase numbering continues Part I without
collision.
