# Transaction Processing Evolution Plan - Implementing "Where This Goes Next"

**Status:** IN IMPLEMENTATION. Phases 1 and 3 are built and tested on
`develop` (uncommitted); Phase 2's core is deferred to staging (see the
implementation-status note below); Phases 4-6 pending. See "Implementation
status" immediately below Part 0.
**Date:** 2026-07-03 (Revision 2; implementation started 2026-07-04)
**Author:** Jan
**Requirements basis:** `TRANSACTION_PROCESSING_METHOD.md`, section "Where this
goes next" (the five development directions Jake received), read together with
`requirements.txt` (Sections 4, 6, 8, 9), `SYSTEM_DESIGN.md`,
`FRONTEND_UI_WORKFLOW_LOGIC.md`, and `STYLE_GUIDE.md` (v2).
**Relates to / builds on:** `AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md`
(Pillars A-D; see II.0/RC1 for its true implementation state),
`AI_AGENT_WORKSPACE_SUPERIORITY_PLAN.md` (agent v1, shipped),
`TRANSACTION_GENERATION_SYSTEM_UPDATE_PLAN.md` (implemented on `develop`),
`DOCUMENT_TEMPLATE_LIBRARY_PLAN.md` (Phase 1 shipped, Phases 2-4 pending),
`CLIENT_WORKSPACE_PLAN.md`, `MY_TASK_QUEUE_AND_ANALYTICS_BUILD_PLAN.md`.

---

## 0. Why this plan is grounded

Previous plans broke down in frontend testing when they were written against
an imagined system. Revision 1 of this plan repeated a milder form of the
same mistake: three of its claims came from stale working notes instead of
the current tree, and the review pass (this revision) corrected them against
`velvet-elves-backend` branch `develop` at commit `734cfcc` and the matching
frontend tree. Every "exists today" claim in Part II cites the actual file.
Where a detail still could not be verified, the plan says so explicitly and
front-loads a verification step instead of guessing.

**Backend source verified**
- `app/services/email/` (`base.py` incl. the `EmailAttachment` /
  `InboundEmail` shapes, `gmail_provider.py`, `outlook_provider.py`,
  `icloud_provider.py`, `inbound_dispatch.py`, `outlook_subscriptions.py`,
  `oauth_state.py`)
- `app/services/ai_email_engine.py`, `app/api/v1/ai_emails.py` (including
  the full bodies of `run_escalations` and `run_reminders`)
- `app/services/task_notification_service.py` (`send_daily_summaries`,
  `create_auto_drafts`), `app/services/notification_prefs_service.py`,
  `app/api/v1/notifications.py`
- `app/api/v1/transaction_agent.py`, `app/services/agent_actions.py`,
  `app/services/agent_policy.py`, `app/services/agent_issues.py`
- `app/services/state_workflow_profiles.py`, `app/services/state_rules.py`,
  `supabase/migrations/` (the seven Q&A migrations `20260906*` are present;
  the email migrations `20260429`, `20260507`, `20260812090000` are present)
- `app/services/client_workspace.py` (and its consumers
  `client_invoices.py`, `client_messages.py`, `client_staff.py`,
  `dashboard_role.py`), `app/api/v1/analytics_extras.py`
- `app/api/v1/document_templates.py`, `app/services/pdf_form_fill.py`,
  `app/api/v1/documents.py` (`fill_and_flatten` import at :92,
  `_persist_generated_draft` at :2634), `app/api/v1/esign.py`,
  `app/services/esign_distribution.py`, `app/services/docusign_oauth.py`
- `deploy/` (checked for any scheduler configuration: none exists)
- Git history: `git log develop..origin/feature/auto-emailing-pillar-a`
  (empty - see RC1)

**Frontend source verified**
- `src/pages/transactions/TransactionWorkspacePage.tsx`,
  `src/components/agent/AgentPane.tsx`, `AskAiRowButton.tsx`
- `src/components/workspace/EmailTab.tsx`, `TimelineTab.tsx`,
  `src/pages/AiEmailReviewPage.tsx`,
  `src/components/active-transactions/CommunicationsPanel.tsx`
- `src/components/shared/AddDeadlineModal.tsx`,
  `src/components/wizard/WizardTimelineStep.tsx` (basis-toggle absence
  verified in all three deadline-editing surfaces)
- `src/pages/settings/` (Connections, Notifications, DocumentTemplates,
  Hub), `src/pages/admin/AdminAIGovernancePage.tsx`,
  `src/pages/admin/TaskTemplateListPage.tsx`
- `src/pages/client/` (all nine pages + `_shell.tsx`),
  `src/pages/AnalyticsPage.tsx`

---

## Implementation status (2026-07-04)

Built and tested (backend `develop`, uncommitted; all suites green):

- **Phase 1 - scheduling backbone + daily loops (DONE).**
  - `CRON_SHARED_SECRET` config + `require_cron_secret` (fail-closed) in
    `app/core/auth.py`.
  - `POST /internal/schedules/tick` (`app/api/v1/internal_schedules.py`):
    cross-tenant fan-out to escalations, scheduled digests, and the
    per-tenant auto-draft sweep; per-tenant failures isolated.
  - `run_scheduled_digests` + `send_one_digest` + `normalize_digest_config`
    in `task_notification_service.py`: per-user opt-in digest, fires only at
    the user's local send-hour (tz-aware via `tzdata`, added to
    requirements), idempotent per (user, day) via a `profile_settings_json
    .digest.last_sent_date` marker.
  - User endpoints: `GET/PUT /notifications/digest`,
    `POST /notifications/digest/sample` (force to me),
    `POST /notifications/reminders/run-mine`.
  - Frontend: Settings - Notifications "Morning digest" block
    (`MorningDigestSection`, `useDigestSettings`): On/Off, send-hour,
    timezone, [Send me a sample now], [Run my reminders now].
  - Local runner `scripts/run_schedules.py`; `deploy/SCHEDULER_SETUP.md`.
  - Tests: `app/tests/test_schedule_tick_and_digest.py` (7) + all existing
    notification suites green.

- **Phase 3 - graduated autonomy / always-approve (DONE, one refinement
  deferred).**
  - `agent_policy.AUTO_ELIGIBLE_ACTION_TYPES` + `is_auto_eligible` (7
    eligible; waives/cascades/type-adoption/compliance-attach/forbidden
    hard-excluded).
  - Migration `20260907090000_agent_action_rules.sql` (tenant-scoped, RLS)
    + `AgentActionRuleRepository`.
  - Enforcement in `transaction_agent._maybe_auto_apply`: a just-proposed
    eligible action with an enabled tenant rule applies through the SAME
    `apply_action` path as the Approve button - identical undo/audit;
    stale-preview/validation failures fall back to a normal proposal card;
    result tagged `auto_approved`.
  - Rules API `GET/PUT /agent/rules` (admin/team-lead;
    `app/api/v1/agent_rules.py`), rejects ineligible types (422).
  - Frontend: admin "Automation rules" section on AI & Automation
    (`AgentAutomationRulesSection`, `useAgentRules`) with the never-eligible
    boundary shown; "Ran automatically · your rule" badge on auto-applied
    agent cards.
  - Tests: `app/tests/test_agent_auto_rules.py` (2) + all existing agent
    tests green.
  - DEFERRED refinement: the in-card "[Always approve] / [Turn off]" buttons
    at the moment of manual approval (need role-gated rule fetching inside
    the pane); the admin section is the management surface today and the
    badge gives honest visibility.

Deferred with cause (not built here):

- **Phase 2 - inbox-first.** The G4 needs-filing tray and G3 intake are
  buildable, but the phase's foundation, G2 attachment capture, requires new
  per-provider attachment DOWNLOAD methods: verified that Gmail's inbound
  fetch uses `format=metadata` (`gmail_provider._fetch_messages_by_ids`), so
  inbound `EmailAttachment`s carry no bytes (RC4). That provider code can
  only be exercised against live mailboxes on staging, so Phase 2 is
  sequenced there rather than built blind.
- **Phase 4 - state-aware remainder.** The basis-toggle's whole point is
  that flipping calendar/business changes a COMPUTED deadline date; that is a
  live-behavior change best verified in the running app (the standing
  verify-rendered-output rule). Sequenced into the live pass with the
  T6-T10 walkthrough and flag-on, where it can be seen working.
- **Phase 5, Phase 6** - pending.

Migrations added this pass (apply after `20260906096000`, then
`20260907090000_agent_action_rules.sql`). `tzdata` added to
`requirements.txt`; `CRON_SHARED_SECRET` added to `.env.example`.

---

## Part I - The five directions as requirements

Numbered for traceability. D1-D5 are the five items of "Where this goes
next", in the same priority order Jake received.

| # | Requirement (short form) |
|---|---|
| D1.1 | Watch the connected mailbox and land every deal-related email on the right transaction |
| D1.2 | Capture inbound attachments as deal documents automatically, with classification |
| D1.3 | Offer to START a new deal when an inbound contract arrives (email intake), one click into the wizard |
| D1.4 | Give unmatched or ambiguous emails a visible tray with mouse-only resolution, never a silent misfile |
| D2.1 | Auto-draft a task's email when the task comes due (per-task opt-in, drafts only) |
| D2.2 | A short morning digest of everything due across deals, per-user opt-in |
| D2.3 | A real scheduling backbone so D2.1/D2.2 run without a human trigger |
| D3.1 | Per-action-type "always approve" rules on the transaction agent, tenant-controlled |
| D3.2 | Rules preserve every existing rail: preview, undo, audit trail, forbidden list |
| D4.1 | Finish the state-aware remainder: basis toggle UI, FSBO owner relabel, Task Templates workflow chip, screenshot pass |
| D4.2 | Walk the T6-T10 tester scripts with Jake and turn ON `ve_deadline_no_roll_v1` and `ve_attorney_states_v1` |
| D5.1 | Client progress view completion pass (correct under the new state workflows) plus an agent-side "view as client" preview |
| D5.2 | Closing analytics: outcome metrics across deals on the Analytics page |
| D5.3 | Forms filled from the template library routed one click into e-signature (library Phases 2-3 plus the send handoff) |
| R-UI | Everything validatable by real-estate professionals through the UI alone: mouse-first, minimal typing, honest empty states, preview-before-apply, STYLE_GUIDE v2 + the flat modern professional-tool aesthetic, rendered-screenshot verification before "done" |

---

## Part II - Current-state audit (what the code actually does)

### II.0 Review corrections register (Revision 1 → Revision 2)

| # | Revision 1 said | What the source actually shows | Effect on the plan |
|---|---|---|---|
| RC1 | "Pillars A-D sit on branch `feature/auto-emailing-pillar-a`, ~244 files behind develop, 3 unapplied migrations; landing it is Phase 0" | `git log develop..origin/feature/auto-emailing-pillar-a` is EMPTY: the branch is fully contained in develop (merge-base = branch tip `b83c485`). The 244-file diff was develop being AHEAD. The email migrations are in the tree (`20260429`, `20260507`, `20260812090000`) | Phase 0's "land the branch" work is deleted. What remains from the pillar plan is its UNBUILT layers (see RC2/RC3), plus confirming with Jan's migration log that the email migrations are applied to each environment's database |
| RC2 | "Auto-draft on due date is wiring to build in Phase 1" | `POST /ai-emails/reminders/run` (`ai_emails.py:722`) ALREADY runs `send_daily_summaries` (per-user preference-gated, actionable-items-only) AND `create_auto_drafts` ("due tasks flagged `auto_draft_email` get ONE compose draft per (task, due date)... Drafts only") | D2.1 is implemented behind a manual trigger. Phase 1 shrinks to: the scheduled caller, cross-tenant fan-out, send-hour prefs, the sample-send button, and a digest content audit |
| RC3 | "Matching is address-based only; no unmatched machinery" | `inbound_dispatch.py:109` calls `match_transaction_for_inbound_with_basis` and stores `metadata_json={"match_basis": ...}` (:141); refile stamps `match_basis: "user_filed"` (`ai_emails.py:310`); `CommunicationsPanel.tsx` already renders basis/unmatched state in the log view | The tray (D1.4) must be built ON the existing basis metadata - filter on it, display it, and reuse the refile endpoint - not on a parallel matcher. Pillar D's "needs-filing queue" UI remains unbuilt; the tray IS that queue plus the intake candidates |
| RC4 | "Verify whether attachments even reach the backend" (hedged) | `EmailAttachment` is a normalized shape (`email/base.py:18`: filename, mime_type, `content_b64` "outbound or fetched-inbound", `document_id` link, size) and `InboundEmail.attachments` carries it; `gmail_provider.py` references attachments | The capture hook (D1.2) consumes `InboundEmail.attachments` directly. The open question narrows to: which providers populate `content_b64` on push vs need a fetch step - a Phase 2 verification task, not a design unknown |
| RC5 | "No one-click handoff exists from a filled document to esign" (implied the generated file may not even persist) | `documents.py` imports `fill_and_flatten` (:92) and persists generated drafts as document rows (`_persist_generated_draft`, :2634) | D5.3's handoff is genuinely only a UI follow-on: the generated file is already a deal document that the existing esign send flow can address |
| RC6 | Named the basis-toggle surfaces "the Edit-days popover and Add-deadline modal (`RuleFields`)" under `components/wizard` | The real surfaces are `components/shared/AddDeadlineModal.tsx`, `components/wizard/WizardTimelineStep.tsx`, and `components/workspace/TimelineTab.tsx`; no `RuleFields` component exists in the tree; none of the three contains a basis control (verified) | G7a stands, with corrected file targets |
| RC7 | "Relax `/notifications/daily-summary/trigger` from admin-only to admin-OR-cron" (single-tenant assumption unexamined) | Both `run_reminders` and `trigger_daily_summaries` derive the tenant from `current_user`; a cron caller has NO user and NO tenant. `run_escalations` already models the fix: a `tenant_only: bool` param that fans out across tenants when false | The cron path needs an explicit cross-tenant variant (copy the `run_escalations` pattern), plus per-run idempotency proof for the digest (the auto-draft sweep is already keyed per task+due-date; the digest needs a sent-marker audit in Phase 1) |
| RC8 | Client preview via "`?preview=1` mode on the client endpoints" | Client-facing routers (`client_invoices.py`, `client_messages.py`, `client_staff.py`, `dashboard_role.py`) call `client_workspace.py` projections under CLIENT-role auth; bolting a preview flag onto role-guarded routes confuses every guard | The preview becomes ONE new internal endpoint (agent/TC/lead/admin roles) that calls the same `client_workspace.py` projection functions for a given transaction - same functions, so preview and reality cannot diverge, and no client route changes |

### II.1 Inbox and email (D1, D2)

What exists on `develop` today - more than any tester guide describes:

- **Providers and push.** Gmail, Outlook, and iCloud providers under
  `app/services/email/`; Gmail Pub/Sub push and Outlook subscriptions
  implemented; users connect mail on Settings - Connections.
- **Inbound dispatch with basis.** [RC3] `inbound_dispatch.py` persists
  every inbound email as an immutable `communication_logs` row,
  de-duplicates by `(provider_name, provider_ref_id)`, matches it to an
  open deal via `match_transaction_for_inbound_with_basis`, RECORDS the
  basis in `metadata_json.match_basis`, and fans out registered hooks
  (`register_inbound_hook`).
- **Normalized attachments.** [RC4] `InboundEmail.attachments` is a list of
  `EmailAttachment` (filename, mime type, optional `content_b64`, optional
  `document_id` link) - but no hook consumes it: inbound attachments are
  never persisted as deal documents.
- **AI response engine (M4.2).** `ai_email_engine.py` classifies inbound
  mail and either auto-sends (only confident AND grounded) or files a
  pending-review draft with recorded assumptions and the tone/disclaimer
  pipeline.
- **Proactive logic behind manual triggers.** [RC2/RC7]
  - `POST /ai-emails/reminders/run` = per-user-gated daily summaries PLUS
    the Auto-Email sweep (`create_auto_drafts`, idempotent per
    (task, due date), drafts only). Admin-only, tenant-of-caller only.
  - `POST /ai-emails/escalations/run` = nags for stale drafts, with the
    cross-tenant `tenant_only=false` pattern already in place.
  - `POST /notifications/daily-summary/trigger` = admin-only, tenant-of-
    caller only, "intended to be called by a cron job".
  - **`deploy/` contains no scheduler of any kind** - nothing ever calls
    these. This is the single fact that makes the product feel reactive.
- **Review surfaces.** `AiEmailReviewPage.tsx` (approve / edit-and-send /
  regenerate), the deal Email tab ("Nothing sends without your approval"),
  refile (`POST /ai-emails/inbound/{log_id}/refile`) with sender-
  association learning (`_learn_sender_association`), and a per-deal
  communications log panel that already shows match state
  (`CommunicationsPanel.tsx`).
- **From the pillar plan, still UNBUILT on develop (verified by grep):**
  reminder-RULES cards (plan §11.2/11.3: "3 days before inspection" style
  rules relative to deal dates), the needs-filing queue UI (§12.2), and
  the opt-in Autopilot delayed-send loop (§13 - no `autopilot` reference
  exists in the backend). Autopilot remains gated on Jake and is OUT of
  scope here (Part VIII).

**Confirmed gaps:**
- **G1:** no scheduling backbone; every proactive endpoint waits for an
  admin click, and the two daily endpoints cannot be called tenant-wide
  by a machine at all [RC7].
- **G2:** inbound attachments are not captured as deal documents.
- **G3:** no path from an inbound contract to a NEW deal. Intake entry
  points are in-app upload and the drag-drop `IntakeConfirmationModal`.
- **G4:** unmatched emails have no actionable tray; the basis metadata and
  refile endpoint exist but no surface lists "what needs filing" [RC3].
- ~~G5~~ [RC1] withdrawn: the pillar branch is merged. Its successor is
  the "still unbuilt" list above, of which this plan takes ONLY the
  needs-filing queue (into G4's tray); reminder-rules cards are deferred
  (Part VIII).

### II.2 Agent autonomy (D3)

- `agent_policy.py` is the single source of truth: 13 supported action
  types with `undo_available` / `reason_required` / `risk` /
  `visible_success_location`; a hard-coded `FORBIDDEN_ACTION_TYPES` set;
  v1 doctrine "every write requires explicit human approval".
- The proposal lifecycle is solid: propose (LLM classifies only) - preview -
  approve through canonical handlers - stale-preview 409 - undo - audit
  (`transaction_agent.py`).
- **G6:** no "always approve" exists for agent actions (grep: `auto_approved`
  appears only as an M4.2 email status). The admin home for such rules
  already exists: `AdminAIGovernancePage.tsx` ("AI & Automation").

### II.3 State-aware processing (D4)

The Q&A build is ON `develop` (commit `a52a61a`; migrations
`20260906090000`..`20260906096000`; `state_workflow_profiles.py`;
`state_rules.py` rewritten). Verified remaining work:

- **G7a:** [RC6] no calendar/business basis control exists in ANY of the
  three deadline-editing surfaces: `WizardTimelineStep.tsx` (Edit-days),
  `shared/AddDeadlineModal.tsx`, `workspace/TimelineTab.tsx` (the string
  "business" appears in none of them; the data plumbing exists in
  `NewTransactionWizard.tsx` / `wizardTypes.ts`).
- **G7b:** `TaskTemplateListPage.tsx` has no workflow chip or editor Select.
- **G7c:** FSBO owner-relabel surfacing and the screenshot pass are
  outstanding.
- **G7d:** `ve_deadline_no_roll_v1` and `ve_attorney_states_v1` default OFF
  awaiting the T6-T10 walkthrough with Jake.

### II.4 The outer circle (D5)

- **Client portal:** nine client pages over `client_workspace.py` (canonical
  client-to-transaction link via `transaction_assignments`, true "Your
  agent" card, milestone timeline, client-scoped document summary, two-way
  thread gated by `is_client_visible`). **G8:** no agent-side "what does my
  client see" preview; the milestone/next-steps derivations have not been
  re-checked against attorney-workflow task content.
- **Analytics:** `AnalyticsPage.tsx` + `/analytics/profile-report`,
  `/analytics/dashboard`, `/analytics/overview`. **G9:** closing OUTCOMES
  are not a first-class surface; Phase 5 starts with a payload audit of the
  three endpoints rather than assuming their coverage.
- **Forms and e-signature:** Template library Phase 1 shipped
  (`document_templates.py` CRUD + `/field-options` + `/{id}/pages`;
  `pdf_form_fill.py` TEXT fields + flatten; tenant > built-in > no-template
  precedence). Generated drafts ARE persisted as deal documents
  ([RC5] `documents.py:2634`). E-signature is wired end to end (`esign.py`
  provider status / send / DocuSign webhook / needs-signature;
  `esign_distribution.py` signed-copy distribution). **G10 (narrowed):**
  library Phases 2-3 are unbuilt, and no surface offers [Send for
  signature] on a generated document.

### II.5 Gap register

| ID | Gap | Direction | Fixed in phase |
|----|-----|-----------|----------------|
| G1 | No scheduler; daily endpoints not machine-callable tenant-wide | D2.3 | Phase 1 |
| G2 | Inbound attachments not captured as documents | D1.2 | Phase 2 |
| G3 | No email intake (new deal from inbound contract) | D1.3 | Phase 2 |
| G4 | No needs-filing tray over the existing basis metadata | D1.1/D1.4 | Phase 2 |
| G6 | No per-action always-approve rules | D3 | Phase 3 |
| G7 | State-aware remainder (a-d above) | D4 | Phase 4 |
| G8 | No client-view preview; client derivations unchecked vs new workflows | D5.1 | Phase 5 |
| G9 | No closing-outcomes analytics | D5.2 | Phase 5 |
| G10 | Library P2-P3 + [Send for signature] follow-on missing | D5.3 | Phase 5 |

---

## Part III - Target design

### III.1 D2 first: the scheduling backbone and the two daily loops

Ordering note: D2 is the smallest change with the largest felt effect, and
D1's loops need the same backbone. [RC2] Most of D2's logic already exists;
this section is deliberately mostly plumbing.

**III.1.1 Scheduler (G1).** Keep the existing "logic in services, trigger by
endpoint" shape and add the missing caller:

- New internal cron authentication: dependency `require_cron_secret`
  checking header `X-VE-Cron-Secret` against env `CRON_SHARED_SECRET`.
- [RC7] New machine-callable run endpoints (or params on the existing
  ones), copying the `run_escalations` `tenant_only=false` pattern:
  one platform-level "run all tenants" variant each for the reminder
  sweep and the daily summary. Per-tenant iteration happens server-side
  in one call; each tenant's failures are isolated and logged, never
  aborting the loop.
- Cadence: ONE hourly EventBridge rule calling a single
  `POST /internal/schedules/tick` endpoint that fans out to: escalations
  (hourly), reminder sweep + digest (fired for exactly those users whose
  configured send-hour matches the current hour in their timezone -
  III.1.3). One rule, one secret, all schedule intelligence in code where
  it is testable. Local dev: `scripts/run_schedules.py` loop.
- Every tick writes one audit row per job (started / items produced /
  skipped reason), so "did the digest run today?" is answerable from the
  admin surfaces.
- Idempotency: the auto-draft sweep is already keyed per (task, due date)
  [RC2]. The digest gains an explicit sent-marker per (user, date) -
  Phase 1 first AUDITS whether `send_daily_summaries` already records one
  and adds it only if missing (honest unknown, resolved in-phase).

**III.1.2 Auto-draft on due date (D2.1).** [RC2] Implemented
(`create_auto_drafts`: due tasks flagged `auto_draft_email` produce ONE
pending-review draft per task+due-date into the AI Email Review queue).
Remaining work is exactly two items: the scheduled caller (III.1.1) and a
tester-visible affordance - the Settings block's [Run my reminders now]
button (below) so the loop is validatable without waiting a day. No
auto-send in this direction; auto-send remains the M4.2 confident-and-
grounded path (Autopilot stays gated and out of scope).

**III.1.3 Morning digest (D2.2).** `send_daily_summaries` already builds
per-user, preference-gated, actionable-only summaries [RC2]. Additions:

- Send-hour and timezone per user in the existing notification preferences
  (`notification_prefs_service.normalize` schema + the Settings -
  Notifications page). Default OFF until Jake opts the team in.
- A content audit against the digest spec (ordering: overdue, due today,
  drafts waiting, documents due this week; every line deep-links to the
  exact surface; HTML rendering consistent with `branded_invite_email.py`
  styling per the pillar plan §11.1.3). Only the deltas found are built.
- One-click **[Send me a sample now]** on the Settings page - sends the
  real digest to the signed-in user only, so a non-developer validates the
  entire loop in one click.

### III.2 D1: inbox-first processing

**III.2.1 Attachment capture (G2).** A new inbound hook (via the existing
`register_inbound_hook`) that, for every inbound email attached to a
matched transaction:

- [RC4] consumes `InboundEmail.attachments` directly; step one of the
  phase verifies which providers deliver `content_b64` on push and adds a
  provider fetch (by attachment id) where only metadata arrives - the
  `EmailAttachment` shape already reserves the fields;
- stores each file through the existing document upload path (same
  storage, `source='email'`, provenance = the communication log id, and
  the `EmailAttachment.document_id` back-link filled in);
- runs the existing persisted-parse classification, which automatically
  lights up requirement matching and the agent pane's
  `document_type_mismatch` / `missing_document` detectors;
- never deletes or replaces anything: the file appears in the Documents
  tab flagged "from email" linking back to the source email.

Attachments on UNMATCHED emails wait with the email in the tray - nothing
files silently.

**III.2.2 Email intake - a new deal from an inbound contract (G3).** Flag
`ve_email_intake_v1`.

- Detector (deterministic, in the same hook): an unmatched inbound email
  whose attachment classifies as a purchase agreement produces an **intake
  candidate** (new table `email_intake_candidates`: tenant, log id,
  document id(s), detected address/parties snippet, status
  proposed/dismissed/started/completed, keyed by provider_ref_id +
  document hash so the same contract never proposes twice).
- UI: a tray card "New contract received - 123 Oak St" with
  **[Start intake]** and **[Not a new deal]** (opens the match picker).
  Start intake opens the EXISTING wizard with the attachment(s) preloaded
  exactly as the drag-drop path does - all five steps, all gates, preview
  equals commit, unchanged. No parallel quick-create path (the Q&A plan's
  recorded constraint stands).

**III.2.3 The needs-filing tray (G4).** [RC3] One new internal surface that
IS the pillar plan's §12.2 needs-filing queue, built on the machinery that
already exists (match-basis metadata, refile endpoint, sender-association
learning). Reachable from the AI Email Review page as a second view
(SegmentedControl: **Drafts | Inbox**), keeping nav flat:

- A TABLE (standing list rule: controls row - search left, filter chips
  All / Unmatched / New contracts / Ignored - h-9) of inbound emails
  needing a human: rows where `match_basis` is absent/ambiguous, plus
  intake candidates.
- Each row resolves in place, buttons only: **[Match to deal]** (modal:
  search box + recent-deals list; content-based suggestion pre-selected
  with confidence chip and one-line evidence, reusing tenant
  `ConfidenceSettings` thresholds - below the accept threshold nothing is
  ever automatic), **[Start intake]** (candidates only), **[Ignore]**
  (optional reason; collapses but stays auditable).
- Matching goes through the EXISTING refile endpoint (which already stamps
  `match_basis: "user_filed"` and teaches sender association [RC3]), so
  the tray shrinks over time. Empty state: "Nothing waiting. Matched
  emails file themselves."

### III.3 D3: graduated autonomy

Flag `ve_agent_auto_rules_v1`.

**Model.** New table `agent_action_rules`: tenant_id, action_type, mode
(`always_approve`), enabled, created_by, created_at, disabled_at,
disabled_by. Tenant-scoped in v1 - one team, one rulebook - admin/team-lead
managed.

**Eligibility is policy, not configuration.** `agent_policy.py` gains
`eligible_for_auto: bool` per action type, defaulting FALSE; anything not
explicitly eligible cannot be automated regardless of rules. Eligible
(seven): `create_task`, `create_deadline`, `change_task_status`,
`toggle_task_auto_email`, `compose_email_draft`,
`compose_document_request_draft`, `reclassify_document` (all low risk AND
undoable-or-draft-only). NEVER eligible (hard-coded, like the forbidden
list): `waive_requirement`, `adopt_ai_type_for_requirement`,
`apply_date_cascade` (fresh-preview doctrine), the four compliance
attach/detach types (they move compliance state), and everything in
`FORBIDDEN_ACTION_TYPES`.

**Enforcement.** In the proposal path (`_propose` /
`transaction_agent.create_action`), after the preview is built: if an
enabled rule covers the action type AND policy marks it eligible, apply
immediately through the exact same `apply_action` call the Approve button
uses - same canonical handlers, same undo json, same audit row (summary
suffixed "(auto-approved by tenant rule)"). The conversation message keeps
the `action_applied` kind with a distinct badge. The commit-id idempotency
path (`_propose` returns an existing action for a repeated commit) is
preserved: a replayed proposal never re-applies. Any 409/422 during
auto-apply downgrades the action to a normal proposal card - the stale-
preview doctrine is untouched. Undo stays available on the card.

**UI (mouse-first, in context).**
- On every APPLIED action card of an eligible type: one line - "Approve
  [create task] automatically from now on?" with an **[Always approve]**
  ghost button. The rule is created at the exact moment of demonstrated
  trust.
- Auto-run cards: neutral badge "Ran automatically - your rule" +
  **[Turn off]** inline (disables the rule, audit-logged).
- Management: an "Automation rules" section on the existing AI & Automation
  admin page, in its boxless settings-document style: a plain table (action
  type in sentence case, enabled by, date, on/off switch) followed by
  static plain-language text listing what can never be automated.

### III.4 D4: finish and switch on state-aware processing

No new design - the Q&A plan remains authoritative. Scheduled remainder:

1. **Basis toggle UI (G7a).** [RC6] The `calendar | business`
   SegmentedControl added in all THREE real surfaces:
   `WizardTimelineStep.tsx` (Edit-days popover),
   `components/shared/AddDeadlineModal.tsx`, and the workspace
   `TimelineTab.tsx` date editors - defaulting to calendar or the AI-read
   basis with its citation chip, per the Q&A plan III.5.
2. **Task Templates workflow chip (G7b):** read-only chip (Title company /
   Attorney / Mixed / Any) on `TaskTemplateListPage` rows + a Select in
   the editor.
3. **FSBO relabel surfacing (G7c):** verify owner-relabel output in the
   FSBO next-steps projection and internal task views; screenshot both.
4. **Screenshot pass** across every changed surface.
5. **Flag-ON path (G7d, D4.2):** T6-T10 with Jake on staging; on sign-off
   enable `ve_deadline_no_roll_v1` then `ve_attorney_states_v1` (day-count
   semantics first, selection changes second), each with a one-day soak
   and the tenant-template report query from the Q&A plan's rollout
   section.

### III.5 D5: the outer circle

**III.5.1 Client view completion pass (G8).**
- Re-verify `fsbo_workspace.build_milestone_timeline` and the client
  next-steps derivation against attorney-workflow fixture deals (new task
  families, new owner labels); adjust the plain-English mapping tables
  where a new family renders awkwardly.
- Agent-side preview: [RC8] ONE new internal read-only endpoint
  (`GET /transactions/{id}/client-preview`, agent/TC/lead/admin roles,
  transaction-scoped) that calls the same `client_workspace.py` projection
  functions the client routes use - same functions, so preview and reality
  cannot diverge; client-facing routes and their role guards are untouched.
  UI: a "View as client" action on the workspace People tab (client rows
  only) opening a read-only Radix modal bannered "This is what your client
  sees."
- Client pages keep honest empty states throughout (standing rule).

**III.5.2 Closing analytics (G9).**
- Step 1: audit the three existing `/analytics` payloads; reuse, never
  duplicate.
- New "Closings" section on `AnalyticsPage`: KPI cards with sparklines
  (median days contract-to-close, on-time closing rate, closings this
  month, average open blockers at closing-minus-7), one SVG trend chart,
  one "slippage by task" table - computed from existing rows
  (`transactions` status/dates, `tasks` due/completed,
  `document_priority_events`). React SVG/CSS only, Plex tabular-nums,
  ve-* tokens.
- Every number click-through-explainable: a KPI opens the filtered list
  that produced it.

**III.5.3 Forms into e-signature (G10).**
- Library **Phase 2** (AI mapping assist: field names only, human-
  confirmed) and **Phase 3** (checkbox/radio/dropdown/signature-tag
  widgets; versioning on re-upload) proceed per
  `DOCUMENT_TEMPLATE_LIBRARY_PLAN.md` §9.
- [RC5] The handoff is a UI follow-on only: wherever a generated document
  appears (the chooser's success state; the Documents tab row of a
  `_persist_generated_draft` file), add **[Send for signature]** - routing
  the ALREADY-PERSISTED document into the existing esign send flow with
  recipients pre-selected from deal parties; provider-not-connected shows
  the existing honest provider-status notice. Signed copies then flow
  through `esign_distribution.py` and the agent pane's
  `signature_in_flight` detector unchanged.
- Agent integration (optional, last): a `generate_form` action type
  (policy: low risk, draft-artifact only, never auto-eligible in v1).

---

## Part IV - Frontend UI/UX specification

Design language for every surface below (standing, non-negotiable):
STYLE_GUIDE v2 comfort scale; `ve-*` tokens only; IBM Plex Sans, Plex Mono
tabular-nums for dates and metrics; flat headers with hairline dividers and
sentence-case labels (no gradient strips); shadcn Select and
SegmentedControl for either/or choices; Radix dialogs only; lucide icons,
never emoji; list surfaces are tables with the standardized controls row
and detail in modals, no intro prose; new full pages own their scroll;
destructive or visibility-changing actions use `useConfirm`; downloads
force-save via blob; honest empty states, no demo affordances; fixes
resolve in place. Every surface is rendered and screenshot-verified
(headless Chrome, dev :8001/:5173 convention) before "done".

**IV.1 Email page: Drafts | Inbox.** SegmentedControl on the AI Email
Review page. Inbox view per III.2.3: controls row, table (received, from,
subject, best guess, action cluster). Match picker modal: search + recent
deals, suggestion pre-selected with confidence chip and one-line evidence.
Row resolution animates out; toast names the destination ("Filed to 123 Oak
St - view").

**IV.2 Digest controls.** Settings - Notifications "Morning digest" block:
on/off switch, send-hour Select, timezone read from the profile, and two
buttons: [Send me a sample now] and [Run my reminders now] (the tester
affordance for III.1.2 - both act on the signed-in user only).

**IV.3 Agent rule affordances.** Applied cards: the one-line always-approve
offer (eligible types only). Auto-run cards: neutral badge + [Turn off].
Admin - AI & Automation: "Automation rules" boxless section per III.3. No
new nav entries.

**IV.4 Basis toggle + workflow chip.** [RC6] Days stepper +
`calendar | business` SegmentedControl in `WizardTimelineStep` Edit-days,
`AddDeadlineModal`, and `TimelineTab` date editors (default calendar;
AI-read basis shows its citation chip). Task Templates rows: gray outline
workflow chip; editor: Workflow Select.

**IV.5 "View as client".** People tab, client rows only: eye icon "View as
client". Full-height Radix modal, banner "This is what your client sees -
read-only", body renders the client Home/Milestones/Documents projections
from the [RC8] preview endpoint. No edit affordances inside.

**IV.6 Closings analytics.** A "Closings" section under the existing
Analytics layout: four KPI cards with sparklines, one SVG trend chart, one
slippage table; serif tabular numbers per the calendar-page benchmark;
every figure click-through to its backing list.

**IV.7 Generate-and-send.** The template chooser's success state and the
Documents tab row for a generated file: [Download] (force-save) and
[Send for signature] opening the existing esign send dialog with recipients
pre-checked from deal parties.

---

## Part V - Implementation phases

Ordering rationale: Phase 1 is the smallest visible proactivity win and the
backbone for Phase 2; Phase 3 is independent; Phase 4 is UI remainder plus
a sign-off gate; Phase 5 items are independent; Phase 6 is the tester pass.
[RC1] Revision 1's Phase 0 (landing the pillar branch) is deleted - the
branch is already merged; the only surviving Phase 0 item is an
environment check, folded into Phase 1.

**Phase 1 - The scheduling backbone + the two daily loops (D2, G1)**
- Environment check first [RC1]: confirm with the migration log that
  `20260429`, `20260507`, and `20260812090000` are applied to staging and
  prod databases (Jan applies migrations by hand).
- `require_cron_secret` + env plumbing; the `/internal/schedules/tick`
  fan-out endpoint with cross-tenant iteration per [RC7]; EventBridge
  hourly rule + `scripts/run_schedules.py` for local dev; audit rows per
  job per tick.
- Digest sent-marker audit (add per (user, date) marker only if missing);
  send-hour + timezone prefs; digest content audit vs III.1.3; the two
  Settings buttons (sample digest, run-my-reminders).
- Tests: tick fan-out (multi-tenant fixture, one tenant failing does not
  abort others), double-tick idempotency (zero new drafts, zero duplicate
  digests), hour-matching (a user at UTC-7 with send-hour 8 fires on the
  right tick), cron-auth 401/403 paths.

**Phase 2 - Inbox-first (D1: G2, G3, G4)** - flag `ve_email_intake_v1`
- Verification first [RC4]: which providers deliver `content_b64` on push;
  add per-provider attachment fetch where absent.
- Attachment-capture hook (provenance, `document_id` back-link,
  classification wiring); `email_intake_candidates` table + lifecycle;
  tray backend over the EXISTING `match_basis` metadata and refile
  endpoint [RC3]; content-match suggestions reusing `ConfidenceSettings`.
- Frontend Drafts | Inbox view, match picker, intake cards into the wizard
  with preloaded files (the drag-drop preload path already exists).
- Tests: hook matrix (matched/unmatched/duplicate/PA-detection/no-bytes),
  candidate lifecycle incl. the never-propose-twice key, vitest for the
  tray states; fixture inbound emails through the existing
  `POST /ai-emails/test-inbound` harness so non-developers can populate
  the tray safely on staging.

**Phase 3 - Always-approve rules (D3, G6)** - flag `ve_agent_auto_rules_v1`
- Migration `agent_action_rules`; `eligible_for_auto` in policy (default
  false); enforcement in the proposal path incl. the commit-id replay
  guard [RC-enforcement]; badges + in-card controls; admin section.
- Tests: eligibility matrix over ALL 13 action types (explicit assert that
  the never-eligible set and the forbidden set reject rules), rule on/off
  round trip, auto-run artifacts identical to manual approve (apply json,
  undo json, audit row), 409-during-auto-apply downgrades to proposal.

**Phase 4 - State-aware remainder + switch-on (D4, G7)**
- G7a basis toggle in the three [RC6] surfaces; G7b workflow chip/Select;
  G7c FSBO relabel verification; screenshot pass.
- T6-T10 staging walkthrough with Jake; flags ON in order with soak; the
  `TRANSACTION_SYSTEM_GUIDE.md` Sections 4-7 rewrite lands WITH the
  no-roll flag (the guide currently promises the roll; testers verify
  against the guide).

**Phase 5 - Outer circle (D5: G8, G9, G10)**
- 5a client pass: cluster-fixture verification, mapping fixes, the [RC8]
  preview endpoint + "View as client" modal.
- 5b closings analytics: payload audit, then the section per IV.6.
- 5c forms: library Phases 2-3 per their plan; [Send for signature]
  follow-on [RC5]; optional `generate_form` agent action last.

**Phase 6 - End-to-end validation pass (R-UI)**
- Tester scripts E1-E12 (Part VI) on staging with the test-inbound harness
  and a fixture tenant.
- Headless-Chrome screenshots of every changed surface; Help Center
  articles: connecting email and the Inbox tray, the morning digest,
  automation rules, sending a generated form for signature.

**Migrations summary (sequenced after `20260906096000`):** [RC1 - the
"pillar branch's 3 migrations" item is withdrawn; those files are already
in the tree] `email_intake_candidates`; `agent_action_rules`;
notification-prefs digest fields (send-hour/timezone; only the columns the
Phase 1 audit finds missing); digest sent-marker (only if the audit finds
none); template library Phase 3 versioning columns per its own plan. All
additive; none rewrite existing rows.

---

## Part VI - Testing & verification strategy

- **Unit (backend):** per phase above; the Q&A plan's planner invariants
  stay pinned; new invariants pinned here: inbound hooks never create a
  deal or file a document without a matched transaction or an explicit
  user click; auto-approved actions carry undo json whenever their policy
  promises it; scheduler ticks are idempotent per day per user.
- **Frontend:** vitest for tray table states, rule badges, digest block;
  tsc/lint clean.
- **Rendered-output verification:** every Part IV surface rendered and
  screenshotted before "done".
- **Non-developer test scripts (mouse-first, quoted on-screen text):**
  - E1: connect Gmail on Settings - Connections; fire the fixture inbound
    (staging harness); watch it file to the right deal's Email tab with
    its match-basis badge.
  - E2: fixture inbound from an unknown sender - appears in Inbox tray;
    [Match to deal]; the next email from that sender files itself.
  - E3: fixture inbound carrying a purchase agreement - "New contract"
    card; [Start intake]; the wizard opens with the contract preloaded;
    finish to Approve & Create.
  - E4: inbound with an inspection-report attachment - the file appears in
    Documents flagged "from email" and satisfies the checklist row.
  - E5: enable the digest; [Send me a sample now]; every link in the email
    lands on the right filtered page.
  - E6: toggle Auto-Email on a task due today; [Run my reminders now]; a
    pending draft appears in the Email tab and the review page; approve
    and send it. Run it again: no second draft (idempotency, visible).
  - E7: ask the agent to add a task; Approve; [Always approve]; repeat the
    request - "Ran automatically - your rule"; Undo works; [Turn off]
    stops it.
  - E8: try the same on a waive - no always-approve offer exists (verify
    absence).
  - E9: edit a deadline's days in all three places (wizard timeline,
    Add-deadline modal, workspace timeline) - the calendar/business toggle
    appears in each; pick business; chip and date update together.
  - E10: People tab - [View as client] shows exactly the client portal
    content, read-only.
  - E11: Analytics - Closings: click a KPI; the backing list matches the
    number.
  - E12: generate a filled form; [Send for signature]; the envelope
    appears; the agent pane shows "Awaiting signatures".
- **Metrics recorded before/after (Phase 6):** median time from inbound
  email to filed-on-deal; % of inbound auto-matched; drafts approved
  without edit; time from contract-received to deal-created via email
  intake vs manual upload.

---

## Part VII - Rollout & compatibility

- Flags: `ve_email_intake_v1` (Phase 2), `ve_agent_auto_rules_v1`
  (Phase 3), the two existing Q&A flags switched on in Phase 4. The digest
  and reminder loops ship dark: per-user opt-in means deploy changes
  nothing by itself. Autopilot remains a pillar-plan concern, gated on
  Jake, untouched here.
- No stored data is mutated by deploy; all migrations are additive.
- Tray, digest, and rules are reversible per tenant by flag or preference;
  disabling leaves logged rows intact.

## Part VIII - Explicit non-goals (decided, do not revisit)

- No SMS or voice channels.
- No auto-SEND of email in any new loop; auto-send remains only the M4.2
  confident-and-grounded path and the separately gated Autopilot opt-in
  (which this plan does NOT build).
- Reminder-RULES cards (pillar plan §11.2/11.3, "3 days before inspection"
  rule builder) are deferred - the per-task Auto-Email toggle covers the
  need for now; revisit after the digest ships. [RC1]
- No AI-invented tasks; no client task-execution UI.
- No always-approve on waives, date cascades, type adoption, compliance
  attach/detach, or anything forbidden - hard-coded, not configurable.
- No new top-level navigation; no chart libraries.

## Part IX - Open questions for Jake (non-blocking)

1. **Digest default:** opt-in per user (planned) or on-by-default for the
   pilot team once he has seen a sample?
2. **Auto-draft lead time:** drafts currently generate on the due date;
   morning-of (planned) or evening-before?
3. **Always-approve starter set:** seven types are eligible; which should
   the team start with (my suggestion: create_task and the two draft
   composers)?
4. **Closing analytics KPIs:** which numbers does he report on by hand
   today? The four proposed cards are a starting set.
5. **Client preview wording:** confirm the "This is what your client sees"
   banner copy before the screenshot pass.

---

*End of plan.*
