# "Automate Everything" - Implementation Plan

**Date:** 2026-07-09. **Rev 2:** 2026-07-10.
**Author:** Jan
**Status:** Plan only. No source changed. Every current-state claim was verified against the live backend and frontend code and the project documents (requirements.txt, SYSTEM_DESIGN.md, AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md, TRANSACTION_PROCESSING_EVOLUTION_PLAN.md) and is cited by file.

### Rev 2 changelog (what the review of Rev 1 found and corrected)

- **R1 (major):** Rev 1 claimed the inbound AI email engine "already sends with no human" above the confidence threshold. **False.** `handle_inbound` only marks a confident draft `approval_status="auto_approved"` / `status="ready_to_send"`; the only two code paths that ever deliver an email are the human endpoints `approve_and_send` and `edit_and_send` (`ai_emails.py:795/830`, both via `_send_draft:1027`). Nothing in the codebase consumes `ready_to_send` autonomously. `AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md` line 88 states the same: "It never actually sends... The label means 'safe to one-click,' not 'sent.'" Sections 0, 1, 2, 5 and the posture table are corrected accordingly, and true auto-send is re-scoped as the separately gated Phase 7.
- **R2 (major):** Rev 1's ceiling table said deadline cascades can run hands-off "through a fresh preview." **Wrong twice over:** `apply_date_cascade` is not in `AUTO_ELIGIBLE_ACTION_TYPES` (`agent_policy.py`), and requirements §4.4 says the AI may "suggest deadline adjustments (**never auto-change**)". Cascades are one-tap human actions, always. The table, Phase 3's example, and §5 are corrected.
- **R3 (major):** Rev 1's per-deal posture control could not actually work as described: agent auto-apply checks a **tenant-level** rules table only (`_maybe_auto_apply` → `rules.is_enabled(tenant_id, action_type)`, `transaction_agent.py:344`). A deal set to Manual would still auto-apply if the tenant rule was on, making the per-deal control a non-functional affordance (exactly the F1/F2 failure class from the wizard audit). Phase 1 now names the required change: a per-deal posture gate inside `_maybe_auto_apply`.
- **R4:** Rev 1 bundled the morning digest into the posture presets. The digest is a deliberately **per-user** opt-in stored in `users.profile_settings_json.digest` ("the scheduled loop touches a user only after they opt in on Settings → Notifications", `task_notification_service.py:35-44`). A tenant/deal posture must not silently flip personal notification settings. Digest removed from the posture bundle.
- **R5:** Rev 1's D2 ("the product contradicts itself on auto-send") had the direction backwards. The UI copy "Nothing sends without a person" is **accurate**. The misleading artifacts are the engine's own docstring ("an auto-sent reply..."), the settings key name `auto_send_threshold`, and the admin page's "AI cannot: Send anything **below** the review threshold without a human" (which implies above-threshold autonomous sends exist). D2 rewritten; the fix is aligning code comments and copy to the real behavior.
- **R6:** Rev 1's "auto-mark drafts Ready" (Phase 5) ignored that `compose_outbound` always persists `pending_review` by design. The mechanics are now specified (reusing the existing `auto_approved` / `ready_to_send` values so dashboard counts like `_AI_APPROVED` stay correct).
- **R7:** "Future tasks inherit the auto-draft flag" had no named hook. Phase 1/5 now name the task-creation paths that must read the deal posture.
- **R8:** Batch "Approve all safe" is now precisely defined (only the seven auto-eligible types; excludes reason-required, fresh-preview, and warning-carrying items), and the cross-deal "Needs you" queue's permission scoping is specified. Also: "Autopilot" now names three different things in this codebase; §6 carries the naming decision as an open question for Jake.

---

## 0. What "automate everything" must and must not mean

The phrase is a product direction, not a literal instruction, and both the codebase and the requirements draw hard lines the plan must respect. Getting this right up front is what makes the plan robust instead of a naive "auto-send all emails" that would break the first legal review.

**The platform enforces boundaries in code, not policy** (`app/services/agent_policy.py`). These are fixed and no tenant setting or automation rule can cross them:

- `send_email` and `auto_send_email` are in `FORBIDDEN_ACTION_TYPES`. A proactive external send to a party is **never** an autonomous agent action. So are `legal_determination`, `release_packet`, `approve_disbursement_exception`, `delete_document`.
- Only seven low-risk, undoable-or-draft-only action types are ever auto-eligible (`AUTO_ELIGIBLE_ACTION_TYPES`): create task, create deadline, change task status, toggle task auto-email, compose email draft, compose document-request draft, reclassify document.
- Waives (reason + high risk), document-type adoption (needs a mislabel confirmation), the compliance attach/detach family, and date cascades are deliberately **not** auto-eligible. Requirements §4.4 backs the last one at the product level: the AI may "suggest deadline adjustments (never auto-change)".

**And, verified (R1): nothing in the current system ever sends an external email without a human.** The inbound engine's `auto_approved` / `ready_to_send` marking means "safe to one-click," not "sent." Every delivery goes through `approve_and_send` or `edit_and_send`. True autonomous sending exists only as a designed-but-unbuilt, opt-in feature with a visible delay and a hold/undo window (`AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md` §13 / Cross-cutting X1), and that feature is gated on a client decision.

So the honest ceiling of "automate everything" is:

| Work | Can run fully hands-off? | Why |
|------|--------------------------|-----|
| Create/advance tasks, add deadlines, relabel documents | **Yes** (auto-eligible, undoable, tenant opt-in already shipped) | Low risk, reversible |
| Cascade deadlines off a contract-date change | **No - one tap**, always through a fresh preview | Not auto-eligible; requirements §4.4 "never auto-change" |
| Draft routine outbound emails and queue them | **Yes** (draft only) | No external send without a person |
| Mark a grounded, confident draft ready for one-click send | **Yes** (already shipped for inbound) | A label, not a send |
| Send any email - proactive or reply | **No - one tap today.** Optional delayed auto-send with a hold window is a gated future opt-in (Phase 7) | Legal boundary; `send_email` forbidden as an agent action |
| Waive a checklist item, adopt an AI doc type, release a packet, any legal call | **No** | Human judgment required by design (requirements §8.6 family) |

**Therefore "automate everything" is delivered as:** *set the posture once, everything routine happens on its own inside the boundary above, and the small legally-required residual becomes a single one-tap "Needs you" queue that a person clears from anywhere, including a phone.* Hands-off in daily use, and it never asks the platform to do something it forbids itself from doing.

---

## 1. Current-state audit (verified from source)

Nine automation mechanisms already exist. They work, but they are fragmented across three mental models and three control surfaces, and the code's own documentation misstates the one question users care about most (does email ever send by itself). The plan's core job is unification, not new engines.

### 1.1 What exists

1. **Confidence gate system** (`confidence_settings`: `auto_proceed_threshold`, `review_threshold`, `recommendation_floor`, `global_min_floor`). Drives wizard extraction tiers and intake-Autopilot eligibility. Tuned at Settings → AI & Automation (`src/pages/admin/AdminAIGovernancePage.tsx`) with ordered sliders.
2. **Wizard intake Autopilot** (`autopilotEligibleFromResult`, `NewTransactionWizard.tsx`): a parse that clears the ship-it tier with all parties signed compresses intake to Confirm then Create.
3. **Deterministic plan engine** (`task_generation_service.py`, `timeline_planner.py`, `requirement_planner.py`): preview equals commit; the LLM never computes a date.
4. **Agent workspace** (`app/api/v1/transaction_agent.py`, `src/components/agent/AgentPane.tsx`): the AI proposes typed actions, each with a policy (undo / reason / risk / where it shows). Human approves, dismisses, or undoes. Chat + scan.
5. **Graduated autonomy** (`app/api/v1/agent_rules.py`, `_maybe_auto_apply`): admins turn "always approve" on for the seven eligible types; those then apply through the same path, tagged "ran automatically," undoable-or-draft-only. Managed in `AgentAutomationRulesSection.tsx`. **Tenant-level only; there is no per-deal scope today (R3).**
6. **Outbound auto-draft sweep** (`create_auto_drafts`, `task_notification_service.py`): per-task opt-in (`metadata_json.auto_draft_email`), drafts one email per (task, due date) into the AI Email Review queue when due or overdue, never sends, idempotent. Enabled today only by a per-task checkbox in the workspace Tasks tab or an agent toggle. The sweep resolves the recipient from the deal's parties at run time and silently skips a task whose target has no captured email.
7. **Inbound AI email engine** (`ai_email_engine.py`): classifies inbound, drafts a reply, CCs the internal owner, escalates unactioned drafts. Above `auto_send_threshold` (default 0.90), for factual/document-request kinds with no assumptions and a matched transaction, it marks the draft `auto_approved` / `ready_to_send` - **a one-click label; it never sends (R1)**. Configured in `EmailAutomationSection.tsx`. On-demand `compose_outbound` drafts are always `pending_review` (R6).
8. **Daily digest + reminders** (`run_scheduled_digests`, `send_daily_summaries`): **per-user** opt-in (R4), timezone-aware, day-before / due-today / overdue.
9. **Scheduler** (`app/api/v1/internal_schedules.py`, `POST /internal/schedules/tick`): hourly, secret-guarded, fans out to escalations, digests, auto-drafts, cost sync. Called by EventBridge in prod and `scripts/run_schedules.py` in dev. Also runnable per-tenant by an admin via `POST /ai-emails/reminders/run`.

### 1.2 Deficiencies this plan fixes

- **D1 - Three mental models, no single posture.** Agent rules, the per-task auto-draft opt-in, and the inbound ready-marking threshold are configured in three different places with three different vocabularies. A real-estate user cannot form one picture of "what will happen automatically on my deals." There is no per-deal automation posture at all, and the underlying agent rules cannot express one (R3).
- **D2 - The code misdescribes its own email behavior (R5).** Actual behavior: no email ever sends without a human. But the engine docstring says "an auto-sent reply (only when the AI is confident...)", an inline comment says "(or auto-send when confident enough)", the tenant setting is named `auto_send_threshold`, and the admin page's boundary panel says the AI cannot send "below the review threshold" without a human, implying it can above. The UI copy that is accurate ("Nothing sends without a person") is contradicted by those artifacts. Fix: one canonical statement ("AI never sends; above your threshold a draft is marked ready for one click"), applied to the docstring, comments, key naming (display label only; the API key stays for compatibility), and the boundary panel.
- **D3 - Automation is invisible and unprovable in the UI.** The timeline-driven sweep depends on an external scheduler that a tester cannot see, run, or confirm. There is no in-app "it ran / it will run" signal and no single feed of "what the AI did for me."
- **D4 - The opt-in is buried and per-task.** Turning routine-email automation on means checking a box on individual tasks. There is no deal-level or tenant-level default, so "automate everything" is many manual clicks.
- **D5 - The residual is scattered.** Things that legitimately need a person (a waive reason, a send, a low-confidence field, an unanswered gating decision) surface in different tabs and different deals. There is no one place a user clears them, and no batch action.
- **D6 - Not testable by non-developers end to end.** Because of D3 and D5, a real-estate tester cannot validate the automation story with the mouse alone; they would have to trigger infra and read logs.

---

## 2. The unifying model: Automation Posture

One concept resolves D1, D4, and most of D5: a single **Automation Posture** chosen per deal (with a tenant default), presented as three one-click preset cards. The posture does **not** introduce a new engine. It is a write-through preset over the existing primitives (the tenant agent-rules table plus a new per-deal gate, and `auto_draft_email` defaults), so there is exactly one control the user thinks about and the plumbing underneath is what already ships.

| Posture | Tasks / deadlines / relabels | Routine outbound emails | Inbound replies | Residual that waits for you |
|---------|------------------------------|-------------------------|-----------------|------------------------------|
| **Manual** | AI proposes; nothing applies without a click | AI drafts only when asked | Drafted; marked ready above the tenant threshold; you send | Everything |
| **Assisted** (default) | Auto-apply (undoable) | Auto-draft to the review queue when due | Same | Sends, waives, cascades, legal, low-confidence |
| **Autopilot** (hands-off) | Auto-apply (undoable) | Auto-draft **and** auto-mark ready; "Send all ready" is one tap | Same | Only sends you haven't tapped, waives, cascades, legal, low-confidence |

Corrections baked into this table (R1, R2, R4): the inbound column is identical across postures because ready-marking is a tenant-level threshold and **no posture sends autonomously**; deadline cascades appear in the residual column for every posture because they are never auto-applied; the digest is absent because it is a personal setting, not a posture lever.

Two honest truths shown on the posture cards themselves (fixing D2): (a) no posture ever sends an email without one tap; (b) if the tenant later enables the gated Full-Send option (Phase 7), auto-sends happen only with a visible countdown and a hold button, and the card says so. This is the single, consistent statement of what auto-sends, and it replaces every misleading line in the current copy.

Posture maps to primitives like this:

- **Manual:** the deal's posture gate blocks agent auto-apply on this deal regardless of tenant rules (new, R3); `auto_draft_email` defaults off for the deal's tasks.
- **Assisted:** auto-apply allowed for the seven eligible types where the tenant rule is on (tenant default posture turns all seven on); `auto_draft_email` defaults on for tasks whose target maps to a party role (the sweep already skips safely when no email is captured).
- **Autopilot:** everything in Assisted, plus the sweep marks the resulting drafts `auto_approved` / `ready_to_send` for the batch send surface (R6).

---

## 3. Guiding UX principles (apply to every surface below)

1. **One posture, one click.** The primary control is three preset cards, not a matrix of toggles. Advanced per-type overrides live behind a "Customize" disclosure for power users, defaulted closed.
2. **Mouse-first, minimal typing.** Every routine action is a click: preset cards, toggles, sliders, "Approve," "Send all ready," "Undo." Typing is only ever optional (editing a draft's prose, a waive reason) and always has a "Use recommended" escape.
3. **Nothing hidden.** Anything the AI does on its own is written to a legible, per-deal Automation activity feed and a tenant-wide feed, each row carrying its evidence and an Undo where the action supports it.
4. **Provable without infra.** Every automated behavior can be triggered on demand from a button in the UI and shows a "last run / next run" status, so a tester never waits on or inspects a cron.
5. **On-brand, modern, professional.** Reuse the resolved boxless Settings voice (serif section titles, label-left / control-right rows, `SegmentedControl`, `ThresholdSlider`, one hairline-topped orange Save) and the flat modern tool aesthetic of the Calendar page benchmark. Sentence-case, lucide icons, no gradient strips. See §6.
6. **Honest boundaries on screen.** The "AI can / AI cannot" panel becomes the canonical, reused explanation of the ceiling, shown wherever posture is set - with its copy corrected per D2.
7. **No non-functional affordances.** Every control shown must be fully wired the day it ships (the lesson of the wizard audit's F1/F2). The per-deal posture control ships only together with the per-deal gate it depends on (R3).

---

## 4. Phased plan

Each phase lists backend work, frontend surfaces, and the click-only test path a real-estate tester follows. Phases 1-6 are independently shippable and none of them depends on the client decision that gates Phase 7. Unlike Rev 1, the phases are honest about the two small behavior changes required in existing functions (the auto-apply posture gate and the sweep's ready-marking); everything else is config, thin endpoints, and UI.

### Phase 1 - Automation Posture (the one control)

**Goal:** Replace the three scattered controls with a single posture, per deal and tenant-default, that writes through to the existing primitives - and actually works per deal (R3).

**Backend**
- Add `automation_posture` (`manual` | `assisted` | `autopilot`) per transaction, defaulting from a tenant default in `tenants.settings_json.automation` (same storage pattern as `ai_provider`). Storage decision (column vs `metadata_json` key) is called out as an open item for the migration.
- **Modify `_maybe_auto_apply` (`transaction_agent.py`)** to read the deal's effective posture before applying: posture `manual` skips auto-apply even when the tenant rule is enabled, leaving the proposal card. This is the one agent-path change and it is what makes the per-deal control real. The tenant-level rules table and `is_auto_eligible` boundary are untouched.
- A resolver `automation_posture_service.apply_posture(...)`: at tenant level, upserts the seven `agent_action_rules`; at deal level, sets `auto_draft_email` defaults on existing eligible tasks (target maps to a party role). It calls only existing repositories plus the `is_auto_eligible` gate, so it can never enable a forbidden action.
- **Name the future-task hook (R7):** the task-creation paths - template generation (`generate_tasks_for_transaction`), retargeting, the agent's `create_task`, and manual task create - default `auto_draft_email` from the deal's posture at creation time.
- Endpoints: `GET/PUT /transactions/{id}/automation` (per-deal), and extend the AI & Automation admin settings to carry the tenant default. Reuse `PUT /agent/rules/{action_type}` under the hood.

**Frontend**
- **Per deal:** a compact posture control in the workspace header (`WorkspaceHeader.tsx`) as a three-segment control with a one-line "what this means" caption and a "Customize" link. One click.
- **Tenant default:** a new "Automation posture" `SettingsCard` at the top of `AdminAIGovernancePage.tsx` - three preset cards (icon, title, one-sentence promise, the honest send note), single orange Save. The existing `EmailAutomationSection`, `AgentAutomationRulesSection`, and confidence sliders move below it under a "Fine-tune" disclosure.
- **Copy corrections (D2/R5), same PR:** engine docstring and comment, the boundary panel line (to "Send any email without a person - never"), and the threshold's display label (to "Mark drafts ready to send at", which `EmailAutomationSection` already uses; the API key `auto_send_threshold` stays for compatibility).

**Test path (mouse only)**
1. Admin → Settings → AI & Automation → click the **Autopilot** preset card → Save. Toast confirms.
2. Open any deal → header shows **Autopilot** selected with its caption.
3. Click **Manual** on the deal → header updates and a "custom" dot appears. Ask the agent to advance a task → it appears as a proposal card and does **not** auto-apply, proving the per-deal gate.

**Acceptance:** posture is set in one click at both levels; a Manual deal never auto-applies even with tenant rules on; forbidden actions never appear as options; all misleading auto-send copy is gone.

### Phase 2 - The unified "Needs you" queue (the residual)

**Goal:** Collapse every item that legitimately needs a person into one cross-deal, batch-clearable list (fixes D5).

**Backend**
- One aggregate endpoint `GET /automation/needs-you` returning, across the caller's visible deals: pending agent-action proposals, outbound drafts pending review, drafts marked ready (one-tap send), and unanswered coverage prompts (gating decisions). Each item carries a type, deal label, one-line summary, evidence/citation where present, and its single action verb ("Approve," "Send," "Choose"). Composes existing data (`agent_actions`, `communication_logs`, the plan's `coverage`); no new stores.
- **Permission scoping (R8):** the aggregate applies the same visibility rules as the transactions list - Admin sees the tenant, Team Lead the team, everyone else deals they own or are assigned to - by reusing the existing scoping helpers, so the queue can never leak a deal the caller cannot open.
- Batch endpoints that fan out to the existing per-item guarded endpoints: `POST /automation/needs-you/approve` and `POST /automation/needs-you/send`. **"Safe" for batch approve is defined in code (R8):** only the seven auto-eligible action types, never `reason_required` items, never `requires_fresh_preview` items (cascades), never items whose preview carries warnings. Everything excluded stays an individual card. A per-item failure (e.g. a stale preview 409) is reported per row, not swallowed.

**Frontend**
- A **"Needs you"** page and a header badge with the count. Rows are cards with a left evidence chip and a right primary button; a top "Approve all safe" and "Send all ready" batch bar. A row expands inline to edit a draft or type a waive reason; the reason field is pre-filled with the AI proposal's own `reason` when one exists, so "Use recommended" is a click, and batch approve never requires typing.
- Renders as a right-rail on wide screens and a tab on narrow, matching the workspace pattern, so it is reachable on a phone.

**Test path**
1. Header shows **Needs you (3)**. Click it.
2. See three cards: a ready outbound email, a waive that needs a reason, a "who orders title?" choice.
3. Click **Send all ready** (the email goes; toast). Click the title choice's **Buyer** chip (resolves; card disappears). Expand the waive, click **Use recommended reason**, **Approve**.
4. Queue is empty with a calm empty state. No free typing was required.

**Acceptance:** every human-required item across the caller's visible deals appears in one place; a full clear is achievable with clicks only; each send/approve still passes through its existing guarded endpoint and audit; nothing reason-required or preview-stale is ever batch-approved.

### Phase 3 - Automation activity feed (trust and undo)

**Goal:** Show, in plain language, everything the AI did on its own, with one-tap Undo where supported (fixes D3's transparency half).

**Backend**
- `GET /transactions/{id}/automation/activity` composing the audit log's auto-approved `agent_action_applied` rows and the auto-draft sweep's output, each with its result summary and, when the action policy allows, an undo handle (reuse `POST .../agent/actions/{action_id}/undo`). Human-approved actions (including every cascade) appear in the normal Activity history, not in this lens - the lens is strictly "ran without a click" (R2).
- A tenant-wide `GET /automation/activity` for the admin AI dashboard (recent auto-runs across deals, counts by type).

**Frontend**
- In the workspace, an **"Automation" lens** on the existing `ActivityTab.tsx` (a filter chip, not a new tab): only what ran automatically, each row with an "Undo" button when available and its evidence chip.
- On the admin AI dashboard, a compact **"What ran automatically"** panel (last 24h: tasks advanced, deadlines added, emails drafted, documents relabeled) linking into the per-deal feeds.

**Test path**
1. Deal → Activity → click **Automation** chip → see "Advanced 'Order title' to In progress," "Drafted email to Loan Officer," "Added deadline 'Septic evaluation'."
2. Click **Undo** on the added deadline → toast, the deadline is marked Skipped, row shows "Undone."
3. Admin dashboard shows the tenant-wide counts updating.

**Acceptance:** every autonomous action is visible with human-readable text and evidence; undoable ones revert in one click; nothing the AI did on its own is hidden; nothing human-approved is misattributed to automation.

### Phase 4 - Make the scheduler provable and reliable (fixes D3's infra half)

**Goal:** No automation behavior should depend on invisible infra that a tester cannot see or trigger.

**Backend**
- Record each `POST /internal/schedules/tick` outcome (ran_at, per-job counts) to a small `automation_runs` log so "last run" is queryable.
- Admin-only `POST /automation/run-now`: runs the tenant-scoped jobs synchronously (wrapping the existing `POST /ai-emails/reminders/run` behavior: digest-eligible summaries plus the auto-draft sweep) and returns the counts, so a tester never needs the cron.
- `GET /automation/status`: last-run time, next expected run, and whether the external scheduler has ticked within the expected window.

**Frontend**
- On the AI & Automation page and the "Needs you" header, a **status chip**: "Automation active. Last run 12 min ago." Stale turns amber: "Automation hasn't run recently" with a **Run now** button (admin).
- A **Run now** button (admin) on the AI dashboard that calls `run-now` and toasts the counts ("Drafted 3 emails, advanced 2 tasks").

**Test path**
1. Admin → AI & Automation → status chip reads "Last run: never" on a fresh env.
2. Click **Run now** → toast with counts; chip updates to "Last run: just now."
3. Re-open "Needs you" → the freshly drafted items are there.

**Acceptance:** a tester can drive and confirm all timeline-based automation with buttons, with zero infra access; the status chip makes an unwired scheduler obvious instead of silent.

### Phase 5 - Deal-level routine-email automation (fixes D4)

**Goal:** Make "draft the routine emails" a posture default instead of a per-task chore, and add the one-tap batch send.

**Backend**
- Posture Assisted/Autopilot: `apply_posture` sets `auto_draft_email` on existing tasks whose `target` maps to a party role, and the Phase 1 creation hooks default it on new tasks (R7). No new sweep; `create_auto_drafts` already resolves the recipient at run time and skips targets with no captured email, so over-flagging is harmless by design.
- **Ready-marking mechanics (R6):** for deals whose posture is Autopilot, the sweep sets the created draft's `approval_status="auto_approved"` and `status="ready_to_send"` - the exact values the inbound path already uses - so `_load_actionable_draft`, the escalation sweep, and the dashboard's `_AI_APPROVED` counting all work unchanged. (`compose_outbound` itself stays `pending_review`-always; the flip happens in the sweep, keyed on posture.)
- `POST /ai-emails/send-ready` (batch): sends all ready drafts for a deal or the tenant by iterating the existing guarded `_send_draft` path per draft, with per-draft success/failure in the response.

**Frontend**
- The per-task checkbox stays for fine control, but its default now follows posture.
- Email tab and the "Needs you" queue get **"Send all ready"** (one click) with a confirm count.

**Test path**
1. Set deal to **Autopilot**. Click **Run now**.
2. Email tab shows drafts marked **Ready**, each addressed to the right party.
3. Click **Send all ready** → confirm "Send 4 emails?" → Send → toasts; drafts move to Sent; Automation activity logs the drafting; the sends are in the normal activity history (human-tapped).

**Acceptance:** enabling routine-email automation for a whole deal is one posture click; sending the batch is one click; no email leaves without that click.

### Phase 6 - Autopilot end-to-end and the deal card (ties to the transactions-page redesign)

**Goal:** Close the loop so a deal genuinely runs itself day to day, and surface its state exactly as Audri wants the transactions page to read ("where it is and what's coming up next").

**Backend**
- Reuse the plan aggregate (`GET /transactions/{id}/plan`), which already returns `ai_next_step`, `stage_pill`, `days_to_close`, and honest counts. Add one derived field: `automation_summary` ("6 handled today, 1 needs you") composed from the activity feed and the needs-you count. Zero new LLM.

**Frontend**
- The transactions list card and the workspace header show a single line: **stage · next up · "Autopilot: 6 handled, 1 needs you."** Clicking the "needs you" part deep-links into the queue filtered to that deal.
- A deal in Autopilot with an empty "Needs you" shows a calm "Running on Autopilot. Nothing needs you right now."

**Test path**
1. Transactions list → a card reads "Under contract · Inspection due in 3 days · Autopilot: 5 handled, 0 needs you."
2. Open it → header echoes the same; Automation activity shows the five handled items.
3. No action required, which is the point; the tester confirms the deal advanced itself.

**Acceptance:** a real-estate tester can create a deal, set Autopilot, run the automation, and watch tasks advance, emails draft and batch-send on one tap, and the residual collapse to the queue - all validated through the UI, with the deal card telling them at a glance that it is handled.

### Phase 7 (gated, optional) - Full-send Autopilot with a hold window

**Goal:** The only true autonomous sending in the product, implemented exactly as `AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md` §13 / X1 already designed it, and shipped only if the client approves it (that plan records the decision as pending).

**Scope (unchanged from that design; restated so this plan is self-contained):**
- Off by default; an explicit tenant opt-in with plain copy about exactly what will happen, and scoped to the narrow grounded kinds (factual replies, document delivery).
- An auto-send is **queued with a visible countdown** (default 5 minutes) during which it sits in the review queue with a prominent "Will auto-send in 4:32 - hold it" button; holding converts it back to a pending draft.
- Always carries the disclaimer, is clearly marked auto-sent in the log, and writes the full audit entry (decision drivers, confidence).
- Implementation note: this is the one place the `FORBIDDEN_ACTION_TYPES` boundary is deliberately **not** touched - the send does not become an agent action; it is a scheduled delivery inside the email engine's own guarded path, which keeps the agent doctrine intact.

**Test path:** enable for document delivery only → run an inbound test (`/ai-emails/test-inbound`) → the draft shows the countdown → let one send (log shows auto-sent + disclaimer) → hold another (it reverts to pending). Mouse only.

**Acceptance:** nothing in Phases 1-6 changes if this phase never ships; with it on, every auto-send was visibly holdable, disclaimed, and audited.

---

## 5. End-to-end tester validation script (single pass, mouse only)

1. **Set the default.** Settings → AI & Automation → click **Autopilot** preset → Save.
2. **Create a deal.** New Transaction → drag in a signed purchase agreement → the wizard parses and (clean, signed) fast-paths to Confirm → **Confirm dates** → **Create**. (Typing only if a field was blank.)
3. **Watch it self-staff.** Open the deal → Automation activity shows tasks created and flagged for auto-email.
4. **Run the timeline jobs.** Click **Run now** (or wait for the tick) → toast: "Drafted 3 emails, advanced 2 tasks."
5. **Clear the residual.** Header **Needs you (k)** → **Approve all safe**, **Send all ready**, resolve any one-click choice → queue empties.
6. **Trust it.** Activity → **Automation** lens → read the plain-language list; **Undo** one row to confirm reversibility.
7. **Prove the boundary.** Set the deal to **Manual**, ask the agent to advance a task → it waits as a proposal card. Nothing auto-applied.
8. **Confirm the glanceable state.** Transactions list → the card reads "stage · next up · Autopilot: handled/needs-you."

If any step requires reading a log, calling an API, or typing more than an optional edit, it is a defect against this plan.

---

## 6. UI and interaction design

The plan adds surfaces, not a new look. Everything reuses the resolved design language so it lands on-brand and reads as a professional tool.

- **Voice and layout.** Boxless, centered Settings document for configuration (`SettingsPageShell`, `SettingsCard`, `SettingsField`), label-left / control-right rows, serif section titles, one hairline-topped orange Save per card - matching `AdminAIGovernancePage.tsx` and `EmailAutomationSection.tsx` exactly.
- **Preset cards.** Three equal cards (Manual / Assisted / Autopilot): a lucide icon (semantically matched, per the no-emoji rule), sentence-case title, a one-line promise, and the honest send note. Selected state uses the ve-orange border treatment already used for active tabs. Selection is a click; no modal.
- **Controls.** `SegmentedControl` for the per-deal posture; `ThresholdSlider` for any advanced threshold; `ToggleRow` for per-type overrides under "Fine-tune." No free-text on primary paths.
- **Needs-you and activity.** Flat cards with a left evidence chip (`AiEvidenceChip`, already built) and a right primary button; hairline dividers; Calendar-page density as the benchmark. Batch bars are one sticky row with two buttons.
- **Status chip.** A small pill next to the page title: green "Automation active," amber "hasn't run recently," each with the last-run time; amber exposes **Run now**.
- **Honesty panel.** The "AI can / AI cannot" panel, with corrected copy, wherever posture is chosen.
- **Naming (open question for Jake).** "Autopilot" would now name three things: the wizard's intake fast-path, this posture level, and Phase 7's full-send option. Proposal: keep **Autopilot** as the posture (the umbrella the user thinks in), rename the Phase 7 toggle "Full-send Autopilot," and leave the wizard's internal name alone since its user-facing banner already reads as part of the same promise. If Jake prefers zero overlap, the posture level falls back to "Hands-off." Decision needed before copy freeze.
- **Theme and responsiveness.** New surfaces inherit the app shell's scroll ownership (`flex h-full min-h-0` pattern); the needs-you queue is a right-rail on xl and a tab on narrow, usable on a phone during a showing.

---

## 7. Risks, boundaries, and non-goals

- **Non-goal: autonomous sending in Phases 1-6.** No email leaves without a tap. Phase 7 is the only exception, it is opt-in, delayed, holdable, disclaimed, audited, and gated on the client's pending decision recorded in the auto-emailing plan.
- **Non-goal: automating judgment.** Waives, document-type adoption, packet release, disbursement, legal determinations, and **deadline changes** (requirements §4.4) stay human. Autopilot routes these to "Needs you," never around them.
- **Risk: a per-deal control that lies (R3).** The workspace posture control ships in the same release as the `_maybe_auto_apply` gate, never before. A visible control without its backend is the exact defect class the wizard audit exists to catch.
- **Risk: the scheduler is off in an environment.** Mitigated by Phase 4's status chip and Run-now button.
- **Risk: posture write-through drift.** The "Fine-tune" panel shows the resolved state, and a deal differing from the tenant default shows the "custom" dot, so hand-toggled rules are never invisible.
- **Risk: over-automation surprising a user.** Every autonomous action is undoable-or-draft-only by the eligibility rule, logged to the Automation lens, and reversible in one click.
- **Boundary deliberately not crossed:** the digest stays a per-user setting (R4); posture never flips another person's notifications.
- **Dependency: parties need emails.** The sweep already skips targets without a captured email; the posture card's caption notes "add party emails to let AI draft their updates," and the People tab surfaces the gaps.

---

## 8. Traceability - what each phase reuses, modifies, adds

| Phase | Reuses (no change) | Modifies (named, minimal) | Adds (config / thin endpoint / UI) |
|-------|--------------------|---------------------------|-------------------------------------|
| 1 | `agent_rules` table + API, `is_auto_eligible`, `auto_draft_email` | `_maybe_auto_apply` (per-deal posture gate); task-creation paths default the flag; email copy/docstrings (D2) | `automation_posture` + tenant default; `apply_posture`; posture control + preset cards |
| 2 | `agent_actions` approve/undo, `communication_logs`, plan `coverage`, list-visibility scoping | - | `GET /automation/needs-you`; batch approve/send fan-out; Needs-you page + badge |
| 3 | audit log, agent undo, `AiEvidenceChip`, `ActivityTab` | - | activity compose endpoints; Automation lens + tenant panel |
| 4 | `internal/schedules/tick`, `ai-emails/reminders/run` | tick also records its outcome | `automation_runs` log; `run-now`, `status`; status chip + Run-now button |
| 5 | `create_auto_drafts` recipient logic, `_send_draft` guarded path, `TasksTab` eligibility | sweep sets `auto_approved`/`ready_to_send` on Autopilot deals | `send-ready` batch; "Send all ready" |
| 6 | `GET /transactions/{id}/plan` | - | `automation_summary` field; deal-card + header one-liner |
| 7 (gated) | email engine, review queue, disclaimer, audit | engine gains the delayed-send/hold path (per AUTO_EMAILING §13) | tenant opt-in, countdown UI, hold button |

No phase modifies the deterministic plan engine, the confidence math, or the forbidden/eligible sets. The safety doctrine in `agent_policy.py` is a fixed floor; Phase 7's send lives inside the email engine's guarded path precisely so that floor never moves.

---

*Rev 2 grounded in: `agent_policy.py`, `agent_rules.py`, `transaction_agent.py` (`_maybe_auto_apply`, `_propose`), `agent_actions.py`, `ai_email_engine.py` (`handle_inbound`, `compose_outbound`), `ai_emails.py` (`approve_and_send`, `edit_and_send`, `_send_draft`, `reminders/run`), `task_notification_service.py` (`create_auto_drafts`, digest config), `internal_schedules.py`, `ai_settings.py`, `transaction_plan.py`, `task_generation_service.py` (backend); `AdminAIGovernancePage.tsx`, `EmailAutomationSection.tsx`, `AgentAutomationRulesSection.tsx`, `AgentPane.tsx`, `TasksTab.tsx`, `ActivityTab.tsx`, `WorkspaceHeader.tsx` (frontend); requirements.txt §4.2-4.5, §6.8, §8; AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md (lines 88, §13, X1); TRANSACTION_PROCESSING_EVOLUTION_PLAN.md Phase 3/D3.*
