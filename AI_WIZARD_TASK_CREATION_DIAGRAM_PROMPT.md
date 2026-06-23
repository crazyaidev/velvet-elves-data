Create a single workflow diagram titled "AI Wizard — How a Transaction's Task
List Is Created (Velvet Elves)". Use a swim-lane / labeled-group layout, top to
bottom. Style: flowchart with clear directional arrows. Color palette: warm
neutrals; use ONE accent color for AI-assist nodes; do NOT use red except on
the "excluded / removed" path. Keep node labels short; put the file or endpoint
in a small subtitle when useful.

CAPTION ABOVE THE DIAGRAM (one line):
"The wizard collects the deal's facts; a deterministic engine then turns the
legacy task-template library into a dated, role-targeted task list. The AI
parses the contract and may suggest extra tasks, but it never invents the core
list — every task is template-driven and auditable."

CREATE FIVE SWIM LANES, top to bottom:
  1. "Agent / TC / Team Lead (signed-in user)"
  2. "Frontend — New Transaction Wizard (React)"
  3. "Backend — Deterministic Task Engine"
  4. "Reference Data — Legacy Task Template Library + Transaction Inputs"
  5. "Postgres (Supabase): tasks"

──────── LANE 1: Agent / TC / Team Lead ────────
  A1 [Start New Transaction]
  A2 [Upload contract / documents]
  A3 [Review AI-extracted details; fill any missing answers]
  A4 [Set / confirm key dates on the Timeline step]
  A5 [Confirm the compliance checklist]
  A6 [Review the proposed task list (Review step)]
  A7 {Decision per row: keep / uncheck / edit date or target}
  A8 [(Optional) Click "Suggest more tasks" — review AI suggestions]
  A9 [Click "Approve & Create"]

──────── LANE 2: Frontend — New Transaction Wizard ────────
  Caption for this lane: "9 internal steps, 5 public phases
  (wizardTypes.ts: WIZARD_STEPS / WIZARD_PHASES)"
  F1 [Phase 1 — Upload: steps 'upload' → 'parsing']
  F2 [Phase 2 — Review details: 'address' → 'purchase' → 'missing'
      → 'confirm'  (collects use_case, state/closing_mode, condition flags)]
  F3 [Phase 3 — Timeline: 'timeline'
      (collects contract_acceptance_date, closing_date, offset day-fields,
       custom deadlines)]
  F4 [Phase 4 — Compliance: 'checklist' (document requirements)]
  F5 [Phase 5 — Tasks & create: 'review']
  F6 [POST /api/v1/transactions/preview-tasks
      useWizardApi.usePreviewTasks  — DRY RUN, nothing saved]
  F7 [(Optional) POST /api/v1/transactions/preview-tasks/ai-suggestions
      usePreviewAiSuggestions — suggestions only, never auto-applied]
  F8 [POST /api/v1/transactions/{id}/tasks/generate
      useGenerateTasks — sends excluded_template_ids + overrides
      + added_tasks]

──────── LANE 3: Backend — Deterministic Task Engine ────────
  Caption for this lane: "plan_tasks_for_transaction() — the SAME pipeline
  runs for both preview and commit (preview == create)"
  B0 [parsing: AI extracts contract data — the ONLY AI on this path so far
      (badge: AI-assist)]
  B1 [STAGE 1 — Load templates for use_case
      _list_templates_for_generation
      Both-Fin = Buy-Fin + Sell-Fin ; Both-Cash = Buy-Cash + Sell-Cash
      sort by (sort_order, legacy_task_id, name)]
  B2 [STAGE 2 — evaluate_conditions
      keep templates whose conditions_json ALL match the deal (AND);
      a flag that is unset → task EXCLUDED (never guess)]
  B3 [STAGE 3 — filter_both_representation (dual agency only)
      standard | consolidated (replaces siblings) | suppressed (single-side
      only); then dedupe by (task_family, target)]
  B4 [STAGE 4 — apply_state_rules
      attorney vs title/escrow closing; closing_mode primary,
      geographic state fallback]
  B5 [STAGE 5 — calculate_due_dates
      seed anchors Contract Acceptance(5) + Closing(1000) from the deal;
      resolve no-dependency tasks off contract acceptance + Float (or an
      absolute wizard date); iteratively resolve dependents (FS/SS),
      maturing off the LATEST predecessor]
  B6 [STAGE 6 — roll_forward_to_business_day
      weekend / US federal holiday → next business day;
      day_basis='business' counts business days for the offset]
  B7 [Build PlannedTask list: name, target(role), cc_targets,
      milestone_label, automation_level, due_date, due_basis ("Closing −14d"),
      included_because ("why"), depends_on, warnings]
  B8 [COMMIT — generate_tasks_for_transaction
      1) drop rows in excluded_template_ids (Review unchecks)
      2) apply overrides (due_date / target / relative basis rule —
         a relative rule BEATS an absolute date)
      3) persist template tasks: source='template', status=PENDING
      4) map legacy dep ids → new task UUIDs (deps on excluded rows dropped)
      5) append approved AI tasks (source='ai') + custom deadlines
         (kind='deadline', source='manual', milestone_label='Deadline')]

──────── LANE 4: Reference Data ────────
  R1 [(cylinder) Legacy Task Template Library
      task_templates  ←  REWORKING_TASK_DB.csv (~97 rows)
      columns: Task Name, Task ID, Use Case, Target, CC, Milestone,
      Deprel(FS/SS), Task Dependent, Float, conditions]
  R2 [(note) Use-case matrix (6):
      Buy-Fin · Buy-Cash · Sell-Fin · Sell-Cash ·
      Both-Fin (dual agency) · Both-Cash (dual agency)]
  R3 [(note) Targets / roles:
      Agent · Co-op Agent · Buyer · Seller · Loan Officer · Title · Attorney]
  R4 [(note) Condition flags collected by the wizard:
      has_hoa · has_inspection · title_ordered_by · has_home_warranty ·
      warranty_ordered_by]
  R5 [(note) Date inputs: contract_acceptance_date · closing_date ·
      hoa_doc_days · inspection_days · inspection_response_days ·
      insurance_commitment_days · possession_date]

──────── LANE 5: Postgres ────────
  D1 [(cylinder) tasks rows — name, due_date, target, cc_targets,
      automation_level, dependencies, milestone_label, source, status,
      metadata_json]

DRAW THESE EDGES (group by phase; label each with its trigger or return shape):

PHASE A — COLLECT (wizard):
  A1 → A2 → F1 → B0
  B0 → A3 → F2
  A4 → F3
  A5 → F4
  R1 -.feeds.-> B1
  R2 -.feeds.-> B1
  R4 -.feeds.-> B2
  R3 -.feeds.-> B3
  R5 -.feeds.-> B5

PHASE B — PLAN (dry run, on reaching the Review step):
  F5 → F6 → B1 → B2 → B3 → B4 → B5 → B6 → B7
  B7 -- "tasks + timeline + summary (nothing saved)" --> A6

PHASE C — REVIEW (human in the loop):
  A6 → A7
  A7 -- keep --> A9
  A7 -- uncheck --> [Note: row added to excluded_template_ids] --> A9
  A7 -- edit date/target/rule --> [Note: row added to overrides] --> A9
  A8 -. optional .-> F7 -. "suggestions (always reviewed)" .-> A6

PHASE D — COMMIT (create):
  A9 → F8 → B8
  B8 -- "same plan_tasks_for_transaction re-run, then persist" --> D1
  B8 -.audit/log.-> D1

ANNOTATIONS / CALLOUTS TO ADD ON THE DIAGRAM:
  * Across B1..B7 add a banner: "Deterministic — strictly template-driven,
    NO AI decides the task list"
  * Between F6 and F8 add a callout: "Preview == Create — the SAME planner
    runs in both, so the review is exactly what gets saved"
  * On B0 and F7 add a badge: "AI-assist only (extract + suggest); never
    auto-applied"
  * On B2 add a callout: "Unset answer → task excluded (never guess)"
  * On B3 add a callout: "'Both' = DUAL AGENCY, not a union — consolidates
    duplicate role copies"
  * On B5 add a callout: "Every deadline roots at Contract Acceptance(5) or
    Closing(1000)"
  * On B6 add a callout: "Weekend / US holiday → next business day"
  * On B8 add a callout: "tasks.source distinguishes template vs ai vs manual"

LEGEND TO INCLUDE:
  * Solid arrow  = synchronous call / step transition
  * Dashed arrow = data feed or side effect (DB read/write, audit)
  * Diamond      = user or system decision
  * Rounded box  = UI screen / user action
  * Rectangle    = backend stage or API endpoint
  * Cylinder     = database table / data source
  * Accent color = AI-assist node

DO NOT include nodes for: the transaction Workspace/agent pane, e-signature,
vendor communications, or billing/credits — those are downstream of task
creation and out of scope for this diagram. Keep the focus on
collect → plan → review → commit.

OUTPUT:
  1. The diagram itself (one page).
  2. Below it, a 6–8 line plain-English caption that states the role of the
     system ("deterministic, human-gated task generator fed by the wizard")
     and the two invariants: (a) the AI never decides the task list — it is
     strictly template-driven; and (b) preview equals create.
