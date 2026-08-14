# Comprehensive Smart Automation System — Implementation Plan

**Date:** 2026-08-14  
**Author:** drafted from live `velvet-elves-backend` / `velvet-elves-frontend` source and the documents in `velvet-elves-data`  
**Status:** Plan only. This file does not change product code.  
**Supersedes as the forward plan:** `AUTOMATE_EVERYTHING_IMPLEMENTATION_PLAN.md` Phases 1–6 (those phases are largely **shipped**; this document does not rebuild them).  
**Does not cancel:** `AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md` §13 / Phase 7 (gated delayed auto-send), `Agent_Email_Instructions.md` (content law), `SCHEDULER_AND_STAGE_ENABLEMENT_RUNBOOK.md` (tick blast-radius rules), `EMAIL_GUIDELINE_QUESTIONS_FOR_JAKE.md` (open Jake decisions).

---

## 0. How to read this document

Velvet Elves already has an automation **stack**: posture, Needs You, a named playbook executor that can send, an inbound drafter that must not send, an hourly EventBridge tick, and a guarded delivery path. What it does **not** yet have is one **system** — a single doctrine for when mail leaves, a closed loop when the AI fails, and intelligence that asks “what is true of this file?” instead of “which due task still has a flag?”

This plan is written against **the code as of 2026-08-14**, not against the July plans’ “current state” sections (several of those are now historical). Every “today” claim below was checked against the live trees or against the live stage/prod APIs the same morning.

| If you want… | Go to |
| --- | --- |
| The one-paragraph product thesis | §1 |
| Rules this plan is forbidden to break | §2 |
| What is already live (do not rebuild) | §3 |
| Why the current stack is not yet “smart” | §4 |
| Target architecture | §5–§6 |
| Build sequence | §7 |
| Jake decisions that still gate work | §15 |
| What we will not do | §16 |

---

## 1. Thesis

**Smart automation** for this product is not “the AI sends more email.” It is:

1. **One send doctrine**, written on every posture card and enforced in one delivery path.  
2. **A deal runtime** that prepares routine work overnight, sends only the named library letters that policy allows, and collapses everything else into Needs You.  
3. **A closed recovery loop**: when the AI stops, the product says why, the cause is fixable, and the next tick or a Give-back actually retries.  
4. **Content that cannot cost a house**: money/wire mail is never drafted, never Ready, never sent by a machine; every other body is either a locked template or a grounded draft a human still sends.  
5. **Provable operations**: the hourly tick is visible, timeout-safe, tenant-scoped where it must be, and loud when it fails.

ListedKit’s public bar remains “you review and send.” Velvet Elves already beats that on citations, audit, and a **narrow** unattended send (the Automated playbook). The way to become comprehensively smart is to make that exception **tiny, named, and honest**, and to make everything around it **recoverable and inspectable** — not to widen unattended send until Phase 7 is explicitly approved.

The conference positioning in `FIRST_CONFERENCE_LISTEDKIT_ADVANTAGE_STRATEGY.md` is the right product shape: **Morning Queue** (overnight preparation, review-gated) as the claim; not “the AI works the file unsupervised.”

---

## 2. Binding requirements (the floor)

These are not preferences. A phase that violates them is a defect against this plan.

From `requirements.txt` / `SYSTEM_DESIGN.md` / `agent_policy.py` / the workflow guide:

| # | Rule | Code / doc anchor |
| --- | --- | --- |
| B1 | The AI may **suggest** deadline changes; it must **never auto-change** dates. Cascades always go through a fresh preview. | requirements §4.4; `apply_date_cascade` is not auto-eligible |
| B2 | Waives, legal determinations, packet release, disbursement exceptions stay human. | requirements §8.6; `FORBIDDEN_ACTION_TYPES` |
| B3 | Agent actions must never include `send_email` / `auto_send_email`. Unattended send, if it exists, lives **only** in the email engine’s guarded path (`send_ai_draft`), not in the agent registry. | `agent_policy.py`; `ai_email_delivery.py` |
| B4 | Auto-eligible agent types are the low-risk, undoable-or-draft-only set. No tenant toggle may enlarge that set. | `AUTO_ELIGIBLE_ACTION_TYPES` |
| B5 | Recipients of deal mail come from **captured parties** (or the account holder for self-reminders). The platform mailer is not used for deal correspondence. | `ai_task_executor.py`; `ai_email_delivery.py` |
| B6 | The recipient is never told AI wrote the mail. Legacy disclaimers are stripped on send. | `strip_ai_disclaimer`; `Agent_Email_Instructions.md` |
| B7 | Digest is a **per-user opt-in**, not a posture lever. | AUTOMATE_EVERYTHING R4 |
| B8 | A tick is **cross-tenant**. It must not be “tested” against live mailboxes that have not been accounted for. | `SCHEDULER_AND_STAGE_ENABLEMENT_RUNBOOK.md` |
| B9 | Attachment prose must match what actually ships. | `ai_email_delivery.py` (“attachment honesty”) |
| B10 | Preview equals commit for the **plan engine**. The LLM never computes a deadline. | `task_generation_service.py`, `timeline_planner.py` |

**The one documented exception to “no send without a tap”** is the AI task executor (`ai_task_executor.py`, client feedback 2026-07-13): on Assisted/Autopilot, a **named** library task (welcomes, title order/confirm, pending MLS reminder) may send a **deterministic template** through `send_ai_draft` and complete the task. That exception is real in production as of this date. This plan does not pretend it does not exist. It **names it, cages it, and refuses to grow it** until Jake approves Phase 7.

---

## 3. Current-state inventory (2026-08-14)

### 3.1 Mechanisms that exist and must be reused

Nine engines, now unified at the UI by posture + Needs You. Do not replace them; compose them.

| # | Mechanism | Where | What it does today | Sends to a deal party? |
| --- | --- | --- | --- | --- |
| 1 | Wizard Autopilot | `NewTransactionWizard.tsx` | Fast-path intake when confidence clears | No |
| 2 | Deterministic plan | `task_generation_service.py`, `timeline_planner.py`, `requirement_planner.py` | Tasks, dates, checklist from contract anchors | No |
| 3 | Agent workspace | `transaction_agent.py`, `AgentPane.tsx` | Typed proposals; `_maybe_auto_apply` honors deal posture | Drafts only |
| 4 | Graduated autonomy | `agent_rules.py` | Tenant “always approve” for the seven eligible types | No |
| 5 | Posture | `automation_posture_service.py`, `WorkspaceHeader.tsx`, `AdminAIGovernancePage.tsx` | Manual / Assisted / Autopilot; Manual is a send kill-switch for the playbook; inherit exists in the header | Gates #6 and #8 |
| 6 | AI task executor | `ai_task_executor.py` | Named Automated rows: template send + Review Documentation (no send; may draft a signature chase) | **Yes**, Assisted/Autopilot |
| 7 | Auto-draft sweep | `create_auto_drafts` | One LLM/template draft per `(task, due_date)` for `auto_draft_email`; skips Automated rows; Autopilot marks Ready | No (Send tap) |
| 8 | Inbound engine | `inbound_triage.py`, `inbound_dispatch.py`, `ai_email_engine.py` | Relevance funnel, then classify/draft; `KIND_MONEY` is not drafted; Ready is a label | No (Send tap) |
| 9 | Hourly tick | `internal_schedules.py` + EventBridge | Escalations, digests, auto-drafts, executor, Gmail watch renewal, cost sync | **Yes**, via #6 |
| 10 | Needs You | `GET /automation/needs-you`, `NeedsYouPage.tsx` | Residual queue: ready drafts, proposals, drafts, coverage, blocked AI tasks; batch approve/send; Give-back; scheduler banner | Send is still `_send_draft` |
| 11 | Status + Run now | `GET /automation/status`, `POST /automation/run-now`, preview | Chip + jobs split by blast radius (`drafts` vs `ai_tasks` vs `digests`) | Only if `ai_tasks` is chosen |
| 12 | Guarded send | `ai_email_delivery.send_ai_draft` | One path: attachments honest, disclaimer stripped, user’s mailbox | Yes, when called |
| 13 | Activity lens | `GET /automation/activity`, deal Automation filter | What ran without a click | No |

Code default posture is **Manual** (`DEFAULT_TENANT_POSTURE`). Individual tenants can (and do) override: the stage admin workspace was **Autopilot** on 2026-08-14; production was **Assisted**.

### 3.2 Playbook that may send unattended

Locked set in `_EMAIL_PLAYBOOK` (`ai_task_executor.py`). Unknown Automated names are **surfaced**, never guessed.

| Task (normalized name) | Recipient role | Body |
| --- | --- | --- |
| Buyer / seller / co-op agent welcome | That party | Library template + address + closing date |
| Loan officer welcome | Lender | Template + document list; requires purchase agreement |
| Order title / confirm title order | Title company or title rep | Template + contract packet; requires purchase agreement |
| Pending reminder | Account holder only | MLS pending nudge (allowed to name the platform) |
| Review documentation | — | Completes or surfaces; signature chase is a **draft** |

Safety already in the executor: Active deals only; captured emails only; connected mailbox required; overdue **> 30 days** surfaces instead of sending; Manual → `posture_manual`.

Triggers already wired: task generation (`transactions.py`), document parse (`ai.py`), hourly tick, `POST /automation/run-now` with `jobs: ["ai_tasks"]`.

### 3.3 Scheduler — now on (ops fact, this morning)

This is the largest change since `AUTOMATE_EVERYTHING` Phase 4 and `todo_list.md` A1.

| Environment | Hourly caller | Status at 2026-08-14 ~06:14 UTC |
| --- | --- | --- |
| Staging | EventBridge rule `velvet-elves-stage-hourly-tick` (existed since 2026-08-13) | `scheduler_healthy: true` |
| Production | EventBridge rule `velvet-elves-prod-hourly-tick` (**created 2026-08-14**) | `scheduler_healthy: true` after one manual tick |

First production tick after enablement: **88 tenants swept, `ai_tasks_completed: 0`, 2 tasks surfaced, 93 internal escalation rows, 0 digests, 0 auto-drafts.** Cost Explorer sync failed (`ce:GetCostAndUsage` denied on the prod ECS task role). One Gmail watch renewal failed. EventBridge targets were set to **MaximumRetryAttempts = 0** because the ALB idle timeout (~60s) is shorter than a real tick (minutes); retries would double-fire.

`GET /automation/preview` exists in current backend source and on **stage**; it returned **404 on production** the same morning (prod deploy behind main).

### 3.4 What Phases 1–6 already delivered (do not rebuild)

From `AUTOMATE_EVERYTHING_IMPLEMENTATION_PLAN.md`, checked against source:

| Old phase | Verdict |
| --- | --- |
| 1 Posture | Shipped (including inherit in `WorkspaceHeader`) |
| 2 Needs You | Shipped (kinds now include blocked AI `task`) |
| 3 Activity feed | Shipped; still under-credits executor completions (finding A-07 / A-10) |
| 4 Status + Run now | Shipped; Run now is **tenant-scoped** and does **not** flip `scheduler_healthy` (correct) |
| 5 Auto-draft defaults + Send all ready | Shipped |
| 6 Deal card “handled / needs you” | Partially shipped; **two definitions of needs-you still disagree** (A-08) |
| 7 Delayed auto-send | **Not built**, still gated |

Give-back (`GiveBackToAiButton`, `can_release_to_ai`) shipped after finding A-02. Retryable codes include mailbox/docs/recipient. Terminal / no-release: `send_failed`, `posture_manual`, `draft_skipped_no_recipient`. `execution_error` retries 3 times then waits for Give-back. `stale_overdue` stays parked until a due-date edit or Give-back (`apply_user_edit_to_ai_block`).

---

## 4. Why this is not yet a comprehensive smart system

The stack is **risk-aware**, not **closed-loop**. These are the gaps a “smart” system has to close. They are ordered by how much they can still hurt a real client now that the hourly tick is live.

### 4.1 Doctrine split (product integrity)

The workflow guide and AUTOMATE_EVERYTHING Rev 2 say: **no email leaves without a tap.** The executor **does** send. Assisted captions still say welcomes and title orders “send on their own.” Needs You, when the scheduler is healthy, can still read as if “everything routine already ran.” Testers and agents cannot form one picture.

Until copy, settings, and code tell the **same** story, every new automation feature will be judged as either “broken” or “too aggressive.”

### 4.2 Open-loop failure

A tick that surfaces 40 tasks and completes 2 (`AI_AUTOMATION_TASK_SYNC_FINDINGS_2026-08-04.md`) is not intelligence; it is a sorter. Give-back exists, but:

- Fixing a contact or uploading a document does not always **re-arm** without another trigger.
- `stale_overdue` copy historically told the user to change the due date; that path must actually clear the flag (A-03).
- `execution_error` still names no cause.
- Needs You count ≠ deal header `needs_you` (A-08).
- AI-completed work can be invisible on progress / handled-today (A-10).

A smart system retries when the **cited cause** is gone, and it credits work the user can see.

### 4.3 Content risk on the paths that still use a model

Unattended playbook bodies are templates (low invention risk, **high mis-address / mis-attach risk**). LLM paths are the inverse:

- Due-task auto-drafts: `compose_outbound` from task description + deal context.  
- Inbound replies: `_draft_reply` after a **regex** classifier.  
- `KIND_MONEY` is skipped only if the regex hits (`wire instructions`, `routing number`, `earnest money`, …). “Please send banking details” can classify as `document_request`, which **is auto-approvable**.  
- `Agent_Email_Instructions.md` (mandatory-review categories, Aime vs agent signature, inspection-always-review vs sheet-says-automate) is **not** the runtime policy. Jake’s answers in `EMAIL_GUIDELINE_QUESTIONS_FOR_JAKE.md` are still open.

### 4.4 Inbound is a funnel, not yet a file clerk

`inbound_triage.py` already separates “is this our business?” from “should we draft?” That was the right fix after the July corpus (junk drafted, real mail dropped). Remaining product work: **why this deal**, **refile**, **filtered-mail inbox**, and never letting a newsletter footer look like a property. ListedKit’s loudest email claim is still “every email is already in the right file.”

### 4.5 ToBeAutomated is a promise, not work

`GET /automation/status` reports `to_be_automated_templates` / `to_be_automated_open_tasks` (35 templates / 82 open tasks on stage the same morning). Those rows are **playbook labels**. Promoting them to Automated without attachment rules, recipient checks, and a send/review policy would multiply unattended mail across every active file the next tick.

### 4.6 Operations are live but thin

- EventBridge HTTP timeout vs long tick (mitigated by retry=0; the tick can still **look** failed in CloudWatch while succeeding).  
- No in-product **mailbox census** before a tick (the runbook’s SQL audit is still manual).  
- Prod preview 404.  
- Cost sync AccessDenied on prod.  
- No page when `ai_tasks_completed` is unexpectedly large.  
- Local, stage, and prod are **different identity stores**; the local Needs You banner and prod health are not the same database.

### 4.7 What is already good (do not regress)

Recorded so later phases do not “simplify” them away:

- Forbidden agent actions and auto-eligible set.  
- Manual posture as a real executor kill-switch.  
- Named playbook only; unknown Automated names surface.  
- Captured recipients only; no mailbox → surface.  
- 30-day stale cap.  
- Money kind not drafted (when classified).  
- Run now split by blast radius after I-14 (default `drafts` only).  
- Attachment honesty on `send_ai_draft`.  
- Scheduler banner on Needs You when `scheduler_healthy` is false.  
- Give-back + retryable taxonomy.

---

## 5. Target: one control loop

```
                    ┌─────────────────────────────────────────┐
                    │  Deal runtime (per Active deal)         │
                    │  facts: plan, parties, mailbox, posture │
                    └─────────────────────────────────────────┘
                                      │
           hourly tick / create / parse / Run now / inbound
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
   Policy gate                  Act or prepare                 Stop
   posture, kind,               playbook send OR               Needs You
   money, mailbox,              draft (LLM/template)           Give-back
   overdue, evidence            OR agent auto-apply            coverage
          │                           │                           │
          └────────────┬──────────────┴────────────┬──────────────┘
                       ▼                           ▼
              Guarded send path              Automation lens
              send_ai_draft only             + status chip
                       │
                       ▼
              Audit + (undo or discard)
```

**Smart** means the policy gate is evaluated **before** compose, with **evidence** that the milestone is not already done (e.g. do not Order Title if a title confirmation email is already on the file), and the stop path is **reversible** when the user fixes the cited cause.

**Comprehensive** means every automation the product already has — agent, playbook, sweep, inbound, digest, vendor proposals, suggestions — reports into the **same** Needs You + activity + status surfaces, with one count.

---

## 6. Send doctrine (the cage)

This is the canonical statement every UI surface must use after S1. It replaces both “nothing ever sends” and silent playbook sends.

### 6.1 Three classes of outbound

| Class | Examples | Machine may send? | Human? |
| --- | --- | --- | --- |
| **A. Library send** | Named `_EMAIL_PLAYBOOK` emails on Assisted/Autopilot | Yes, via `send_ai_draft`, Active deal, captured party, healthy mailbox, not >30 days overdue | Manual blocks; Give-back / Handle if surfaced |
| **B. Prepared send** | Auto-drafts, inbound replies, signature chase, vendor replies, agent compose | **Never** | Review / Ready / Send all ready |
| **C. Gated delayed send** | Phase 7: factual / document-delivery only | Only after Jake opt-in, visible countdown, Hold | Hold returns to B |

Class A is **closed**. New unattended letters require: a template in `email_template_library.py`, a playbook row, attachment sheet, recipient role, tests, and an explicit product decision — not a `ToBeAutomated` flip.

### 6.2 Topics that are never Class A and never Ready (Class B may draft only if we later decide; default is **no draft**)

From `Agent_Email_Instructions.md` and `ai_email_engine.py`:

- Wire instructions, routing/account numbers, payoff, earnest-money **direction to remit**  
- Legal advice, “you should sue,” guaranteed outcomes  
- Commission disputes, release of earnest money as a legal act  
- Anything the money classifier hits (expand beyond regex in S4)

Inbound `KIND_MONEY` stays **no draft**. Ready-marking allow-list stays `{factual, document_request}` until a second review; money must never be added.

### 6.3 Posture mapping (target, after S1 copy freeze)

| Posture | Agent auto-apply | Class A library send | Class B drafts | Ready label |
| --- | --- | --- | --- | --- |
| Manual | No | No (`posture_manual`) | Only if asked | Tenant threshold only |
| Assisted | Yes (eligible types) | Yes | Due-task sweep | No (pending review) |
| Autopilot | Yes | Yes | Due-task sweep | Yes (still a Send tap) |

Wizard Autopilot remains **intake only**. Do not rename it in this plan (open naming question stays with Jake).

---

## 7. Phased build

Phases are independently shippable. S0–S2 should land **before** promoting any `ToBeAutomated` template and **before** Phase 7. Conference-facing work is S0 + S1 + S3a (Morning Queue as **prepare, don’t send**).

Each phase lists: goal, backend, frontend, acceptance, and the finding/doc it closes.

---

### S0 — Stabilize the live tick (operations, days not weeks)

**Goal:** The hourly job we just enabled cannot quietly email 88 production tenants, cannot double-fire, and cannot fail silently.

**Backend / infra**

1. **Async tick or long-timeout path.** EventBridge API destinations will keep timing out at ~5–60s while `schedule_tick` runs minutes. Preferred: tick enqueues a worker (SQS / ECS task) and returns 202 immediately with a run id; worker writes `KEY_AUTOMATION_LAST_TICK` at **end**. Alternative: a tiny Lambda that POSTs and ignores HTTP timeout, with idempotency already in the jobs. Keep **MaximumRetryAttempts = 0** until 202 exists.  
2. **Idempotency keys visible in the tick response** (already true for digests per user-day and drafts per task+due). Add an **executor send idempotency** check: never send a second library email for the same `(task_id, playbook_key)` if a `communication_logs` row already exists as sent.  
3. **Deploy `GET /automation/preview` to production** so Run AI tasks is never blind.  
4. **Grant or disable cost sync.** Either attach `ce:GetCostAndUsage` to `velvet-elves-prod-backend-task-role` or skip cost sync in prod until granted (failed sync must not look like a tick failure).  
5. **Operator page:** if `ai_tasks_completed` > tenant-configured ceiling (default 0 for a brand-new production tenant’s first 24h is too strict; default **alert at ≥ 1** for 48 hours after first enable, then a higher ceiling). CloudWatch on `schedule tick:` log line.  
6. **Mailbox census endpoint** (admin/platform): count of active Gmail/Outlook/iCloud per tenant, last token health — the runbook SQL as an API so nobody fires a tick blind again.

**Frontend**

- AI & Automation: show **last tick counts** (tenants swept, emails sent, surfaced, errors), not only “active / stale.”  
- If `ai_tasks_completed > 0` on the last tick, an amber line: “The hourly run sent N Automated emails.” Honesty, not panic.

**Acceptance**

- A prod tick that times out at the ALB is **not** retried.  
- Preview 200 on prod.  
- Status chip remains `ok` with `last_tick_at` within 2 hours **and** matches CloudWatch TriggeredRules.  
- No second welcome for a task that already sent.

**Closes:** runbook timeout double-fire; prod-behind-main preview; silent cost-sync failure; A1 “timer off” as an ops story (timer is on; now it must be **safe**).

---

### S1 — One doctrine, one count, one caption

**Goal:** Every screen tells the same story as §6. Metrics that say “needs you” agree.

**Backend**

1. **Single `needs_you` composer** used by `GET /automation/needs-you`, `GET /transactions/{id}/plan` automation summary, and the workspace header. Same filters, same kinds (action, draft, ready_draft, coverage, task). Finding A-08.  
2. **Credit Class A completions** on `handled_today` and the Automation lens (executor `trigger` + log id). Finding A-07 / A-10. Progress % may still exclude Automated rows from the human bar (deliberate); the **automation** line must not read “0 handled.”  
3. Confirm inherit (`PUT .../automation` with `inherit` / clearing deal override) matches `WorkspaceHeader` (A-09). If the API still cannot clear the pin, that is a one-line API fix in this phase.

**Frontend**

1. Rewrite posture captions and the AI can/cannot panel:  
   - “On Assisted and Autopilot, Velvet Elves may send the library welcome and title-order letters by itself. Every other email is drafted for you to send.”  
   - Remove any line that says no email ever leaves without a tap **unless** it is explicitly scoped to Class B.  
2. Needs You briefing when healthy: do not say “everything routine already ran” if Class A did not run or items are blocked. Prefer the existing stale copy when `scheduler_healthy` is false (already shipped).  
3. Settings chip: last tick **and** last tenant Run now, labelled as two clocks (already in `AdminAIGovernancePage`; keep).

**Acceptance**

- A tester on Autopilot can explain, in one sentence, what sends alone vs what waits.  
- Sum of deal `needs_you` equals the Needs You badge for that user’s scope.  
- Completing a welcome via the executor increments handled-today / Automation lens.

**Closes:** D2 / R5 copy debt; A-06, A-08, A-09, A-10.

---

### S2 — Closed-loop executor (the intelligence of recovery)

**Goal:** “The AI stopped because X” is always followed by “when X is gone, it tries again.”

**Backend**

1. **Cause watchers** (no extra LLM):  
   - `no_recipient` / `draft_skipped_no_recipient` → party email added.  
   - `missing_document` / `no_documents_to_review` → matching document uploaded or parse finished.  
   - `mailbox_reconnect_required` / `no_provider` → integration `token_status=healthy`.  
   - `unsigned_documents` → signature verdict changes.  
   On those events, pop `ai_needs_user` if the code matches, then enqueue a **per-deal** executor run (not a platform tick).  
2. Honor A-03: `apply_user_edit_to_ai_block` on due-date change must re-arm `stale_overdue` (verify with a regression test; if already true, add the Chrome assertion).  
3. **`execution_error`**: store `cause` class (provider, compose, unexpected) in the flag; surface that sentence; after 3 attempts, Needs You Handle + Give-back remain.  
4. **Tick scoreboard:** persist per-tenant `{completed, surfaced, waiting, errors}` on the last tick blob (not only platform totals). Admin activity panel lists tenants with `surfaced > 0` and `completed = 0`.  
5. Executor **evidence skip**: if a sent library email or a completed sibling task already satisfies the milestone (e.g. title order sent), mark complete with note “already satisfied” — do not send a duplicate. Complements S0 idempotency.

**Frontend**

- Blocked-task card: the recovery instruction must match a **control that exists** (Add contact, Upload, Reconnect, Change due date, Give-back). No dead advice (A-03 class).  
- Optional “Try now” that calls a **per-deal** run (not platform tick) for Admins — fills the gap `todo_list.md` A2.

**Acceptance**

- Add a missing buyer email on a `no_recipient` welcome → the next per-deal run sends or surfaces a new honest reason, without Give-back.  
- Chrome: due-date edit on `stale_overdue` re-arms.  
- A tick with 0 completes and N surfaces is visible on AI & Automation without opening CloudWatch.

**Closes:** A-02 remainder, A-03, A-04, A-11 operator silence; todo A2.

---

### S3 — Deal runtime and Morning Queue

**Goal:** Automation asks “what is this file waiting on?” Overnight it **prepares**; it does not widen Class A.

**S3a — Morning Queue (conference-safe)**

Product promise from `FIRST_CONFERENCE_LISTEDKIT_ADVANTAGE_STRATEGY.md`: overnight preparation, review-gated.

- Nightly (or last tick before the user’s digest hour): for Assisted/Autopilot deals, run auto-draft sweep + executor **preview** (no Class A send if a tenant flag `morning_queue_send=false`, default **true only where Class A is already allowed** — do not change Class A here).  
- Output: Needs You is full at 8am local; digest (opt-in) lists “N ready, M blocked.”  
- **Default for new production tenants:** `morning_queue_send` follows posture Class A (already). A **new** flag is only needed if Jake wants Autopilot drafts without Class A sends for a soak period.

**S3b — Satisfaction engine (the smart core)**

A small, deterministic module `deal_runtime.py` (name flexible) evaluated per deal:

Inputs: plan tasks, communication_logs (sent/draft), documents, parties, mailbox health, posture, `ai_needs_user`.

Outputs: ordered work items `{send_playbook, draft_task, surface, noop_satisfied}`.

Rules examples (each is a unit test, not a prompt):

- If Order Title is open but a sent `task_order_title` log exists → `noop_satisfied`.  
- If welcome is due but party email empty → `surface no_recipient` (already).  
- If inspection response is due and inbound already contains the response → draft is FYI / no duplicate request (needs inbound category; S4/S5).  
- If deal is not Active → no Class A, no sweep.

The hourly tick **calls this per deal** instead of independently blasting executor + sweep with no shared picture. Implementation can start by wrapping the two existing functions with a satisfaction pre-check; it does not require a new database.

**Frontend**

- Deal header one-liner uses the S1 composer: `Autopilot · 6 handled · 1 needs you` with matching queue.  
- Morning Queue empty state: “Overnight prep ran. Nothing needs you.” only when the last tick is healthy **and** needs_you is 0.

**Acceptance**

- Creating a deal still sends Class A welcomes when policy allows (do not break the 2026-07-13 client decision).  
- A second tick the same day does not send a second welcome.  
- Tester can set Autopilot, sleep on it (or Run now), and clear Needs You with clicks only — the AUTOMATE_EVERYTHING §5 script, with honest Class A copy.

**Closes:** D3 leftover (runtime still felt like two crons); conference Morning Queue; duplicate-send class of risk.

---

### S4 — Content policy (Aime’s instructions as code)

**Goal:** Runtime drafting obeys `Agent_Email_Instructions.md` where the product has already decided, and **stops** where Jake has not.

**Backend**

1. **Category enum** aligned to the guideline (request, reminder, schedule, status, intro, problem) **and** the engine kinds (factual, document_*, money, vendor_reply). Mapping table in one file; classifiers write both.  
2. **Money / funds classifier v2:** regex (keep, first) **plus** a bounded model vote only when regex misses and the message contains bank/payment/closing-funds language. If either says money → `KIND_MONEY`, no draft, Needs You “Handle.” Never Ready.  
3. **Mandatory human review list** from the guideline (inspection responses if Jake picks “always review”, legal, money, identity change). Those kinds cannot be `auto_approved`.  
4. **Grounding:** keep `_validated_source_data` (verbatim copy of deal facts). Extend to auto-drafts: if the task description asks for a date/amount, the draft must cite a context key or the draft is low-confidence pending_review.  
5. **Attachments:** continue `send_ai_draft` honesty; add a compose-time check that a sentence matching `attached is` requires `attachment_ids`. Regression: the June document-request break cannot return.  
6. **Signature:** do not implement “signed Aime” until Jake answers Q6. Default remains the **agent’s** signature (`_owner_signature`). Document the branch.

**Frontend**

- Draft rail: show **policy tags** (`library-send` / `needs-review` / `money-held`) so Ready is never mysterious.  
- Settings: “Mark drafts ready” slider already exists; add a read-only list of kinds that are **never** eligible.

**Acceptance**

- A fixture inbound “please send the wire instructions” → no draft, visible in Needs You or Email as money-held.  
- A fixture inbound “please send banking details for closing” → same (v2).  
- A document-request draft cannot send with “Attached is X” and zero files.

**Depends on:** Jake Q6, Q7, Q8 from `EMAIL_GUIDELINE_QUESTIONS_FOR_JAKE.md` for inspection/automation and reply-how-to columns. **S4 money v2 does not wait on Jake.**

**Closes:** wire-adjacent misclassification; guideline/product drift; June attachment incident class.

---

### S5 — Inbound as file clerk

**Goal:** Every kept message is on the right deal or honestly unmatched; junk does not become work.

Reuse `inbound_triage.py` (who-sent-it beats what-it-says). Add product, not a second funnel:

**Backend**

1. Persist `match_evidence` on the inbound row (already on the verdict) and expose it on GET draft/parent.  
2. `POST /ai-emails/{id}/refile` `{ transaction_id | null }` — moves inbound + child draft; re-runs draft only if still in DRAFTING_KINDS and not money.  
3. Filtered-mail list (`inbound_filtered`) in the Email UI with **Undo filter** (one tap, as the triage docstring promised).  
4. Unmatched but relevant: Needs You kind `unmatched` or keep on Email with “Match to a deal” — do not silently drop (July failure mode).

**Frontend**

- “Why this deal” one line on the inbound pane.  
- Refile picker (existing deal search).  
- Filtered tab: envelope only, no body (privacy already in triage).

**Acceptance**

- Newsletter with a street in the footer does not draft (triage + tests).  
- A real title-commitment statement is kept even if it is not a question.  
- Wrong-deal mail is refiled in one click; the old draft is discarded or moved.

**Closes:** ListedKit “in the right file”; EMAIL_INTELLIGENCE July corpus class of bugs.

---

### S6 — Promote ToBeAutomated (never a bulk flip)

**Goal:** The honesty report (`to_be_automated_*`) becomes a **promotion pipeline**, not a silent upgrade.

**Rules**

1. Default: ToBeAutomated stays **human / Class B draft** if `auto_draft_email` is on.  
2. Promotion to Class A requires:  
   - stable template id (not display name) in `_EMAIL_PLAYBOOK`;  
   - `email_template_library` body;  
   - attachment kinds from the Jake sheet **once IDs match** (Q1–Q5, Appendix A);  
   - recipient role resolvable;  
   - tests: send, skip-if-satisfied, skip-if-manual, skip-if-no-mailbox;  
   - feature flag per template, off by default, per environment.  
3. Cap: **one template per production week** after stage soak, with `ai_tasks_completed` watched (S0).

**Frontend**

- AI & Automation honesty panel: list ToBeAutomated template names and “not sent by AI.”  
- Platform/admin: promotion checklist UI (optional; a markdown runbook is enough for v1).

**Acceptance**

- Flipping a task template to Automated **without** a playbook key still surfaces `unknown playbook` (already).  
- No environment promotes 35 templates in one deploy.

**Blocked on:** Jake Q1–Q5, Q7 (inspection).

---

### S7 — Gated delayed auto-send (old Phase 7)

**Goal:** The only **new** unattended send. Off by default. Does not touch `FORBIDDEN_ACTION_TYPES`.

Unchanged from `AUTOMATE_EVERYTHING` Phase 7 / `AUTO_EMAILING` §13:

- Tenant opt-in; kinds ⊆ `{factual, document_delivery}` **minus** money-adjacent.  
- Visible countdown (default 5 minutes); **Hold** returns to pending_review.  
- Audit: decision drivers, confidence, “auto-sent after hold window.”  
- Never Class A expansion; never inspection-response if Jake chose always-review.

**Acceptance:** the mouse-only test in AUTOMATE_EVERYTHING §4 Phase 7. If Jake never approves, S0–S6 still stand.

---

### S8 — Platform-grade tenancy

**Goal:** A tick that is safe on 88 tenants.

**Backend**

1. **Per-tenant tick switch** `automation.scheduler_enabled` (default true for existing; **false for brand-new signups** until an admin enables Assisted **and** a mailbox is healthy).  
2. Skip tenants with `legal_hold`, deactivated, or zero healthy mail integrations (still write “skipped” in counts).  
3. Platform admin: table of tenants × last tick outcome × mailbox health × posture default.  
4. Dry-run week: `scheduler_enabled` on but Class A send suppressed (`library_send_enabled=false`) — drafts + surfaces only.

**Frontend**

- Platform › (existing Signups / tenants) or AI & Automation at platform role: the table in (3).  
- Workspace settings: “Hourly automation is on for this workspace” with the S1 doctrine sentence.

**Acceptance**

- A new self-serve tenant on Manual receives **zero** Class A mail until they opt in and connect a mailbox.  
- Legal-hold tenant is skipped and counted.

---

## 8. Frontend map (no new aesthetic)

Reuse `AdminAIGovernancePage`, `NeedsYouPage`, `WorkspaceHeader` posture, `AiEmailReviewPage`, Activity Automation lens, `GiveBackToAiButton`. Add only:

| Surface | Change |
| --- | --- |
| Posture cards / can-cannot | S1 copy |
| Status chip | S0 counts + “N Automated emails sent” |
| Needs You briefing | S1 honesty; S2 recovery verbs |
| Deal header | S1 one composer |
| Email inbound pane | S5 why/refile/filtered |
| Draft policy tags | S4 |
| Platform tenant table | S8 |

Style: existing Settings / Needs You / Calendar density. No new visual language.

---

## 9. Suggested implementation order vs calendar

Assuming the September 12 lock / September 22 conference in `FIRST_CONFERENCE_LISTEDKIT_ADVANTAGE_STRATEGY.md`:

| Window | Phases | Why |
| --- | --- | --- |
| Immediate (this week) | S0, S1 | Tick is already live; honesty and no double-send matter **now** |
| Before conference | S2, S3a | Recovery + Morning Queue story |
| After conference | S3b, S4, S5 | Smarter runtime and inbound clerk |
| Only with Jake answers | S6, signature/Aime | Do not guess template IDs |
| Only with explicit yes | S7 | Delayed auto-send |
| Parallel when platform time | S8 | Multi-tenant safety net |

If conference claims must not include overnight send, keep Class A as “on create + hourly for the **named six letters**” and sell **Needs You in the morning**, not “Ava works the file.”

---

## 10. Test program (non-developer, mouse-first)

Extend AUTOMATE_EVERYTHING §5; add these **must-pass** cases. Chrome against stage first, then one production tenant whose parties are mailboxes we control.

| ID | Steps | Pass |
| --- | --- | --- |
| T1 | Manual deal, create with welcomes due | No Class A send; tasks show posture_manual or wait |
| T2 | Assisted deal, create, mailbox connected, parties = our inboxes | Exactly the expected welcomes, once |
| T3 | Run now drafts only | Drafts in Email review; **zero** provider sends |
| T4 | Run now AI tasks after preview shows 0 would_send | Completes/surfaces; 0 sends |
| T5 | Preview would_send ≥ 1 | Confirm copy names recipients; abort is possible |
| T6 | Disconnect mailbox, tick | Surface mailbox_reconnect; no send |
| T7 | Add missing email on no_recipient (after S2) | Next per-deal run retries |
| T8 | Inbound wire-instructions fixture | No draft |
| T9 | Inbound “title commitment is ready” | Kept; draft or FYI, not dropped |
| T10 | Send all ready | Confirm lists recipients; `_send_draft` only |
| T11 | Needs You badge vs deal chips | Equal (after S1) |
| T12 | Change due date on stale_overdue | Re-arms |
| T13 | Give-back on execution_error | Executor may run again |
| T14 | Second tick same day | No second welcome |
| T15 | Scheduler kill (disable rule) | Amber banner < 2h+ε |

API tests already in `test_ai_task_executor.py`, `test_automation_posture.py`, `test_auto_draft_sweep.py`, `test_schedule_tick_and_digest.py` stay the regression floor; each S-phase adds tests named in that phase.

---

## 11. Metrics

| Metric | Good | Alarm |
| --- | --- | --- |
| `scheduler_state` | `ok` | `stale` / `never_run` |
| `ai_tasks_completed` per tick | 0–small, explained by preview | Spike vs 24h baseline |
| `ai_tasks_surfaced / completed` | falling over a week | >10 with 0 completed (A-11 class) |
| Duplicate Class A sends per `(task_id)` | 0 | ≥ 1 |
| Inbound money drafted | 0 | ≥ 1 |
| Needs You vs header delta | 0 | A-08 |
| EventBridge FailedInvocations with retry=0 | expected timeouts only | retries > 0 |
| New tenant Class A sends before opt-in (S8) | 0 | ≥ 1 |

---

## 12. Risks this plan accepts vs refuses

**Accepts**

- Class A library send on Assisted/Autopilot (already live; caging, not removal, unless Jake reverses 2026-07-13).  
- LLM drafts that can be wrong — contained by Send tap + grounding + money hold.  
- EventBridge not seeing HTTP 200 for a long tick until S0 async.

**Refuses**

- Bulk ToBeAutomated → Automated.  
- Agent `send_email`.  
- Auto date changes, auto waives, auto legal.  
- Ready-marking money or inspection-response (if Jake says always review).  
- Using local `CRON_SHARED_SECRET` against prod.  
- Firing a tick to “make the chip green” as a substitute for EventBridge (chip is green now; keep it that way with the rule, not with ad-hoc curls).

---

## 13. Open decisions (Jake)

Carried forward; this plan does not invent answers.

| # | Source | Question | If unanswered, this plan does |
| --- | --- | --- | --- |
| J1–J5 | Email guideline Q1–Q5 | Task ID / attachment sheet alignment | No S6 promotions |
| J6 | Q6 | Sign auto-sent mail as Aime vs agent | Keep agent signature |
| J7 | Q7 | Inspection: automate reminders vs always review | Inspection stays Class B / human |
| J8 | Q8 | Per-task “how to reply” copy | Drafts keep task description as intent |
| J9 | Q9 | Style per agent vs brokerage | Keep per-user signature/tone |
| J10 | AUTOMATE_EVERYTHING §6 | Naming: Autopilot ×3 | No rename |
| J11 | AUTO_EMAILING X1 | Phase 7 delayed auto-send | S7 stays unbuilt |
| J12 | New | Soak: new prod tenants Class A off until mailbox + Assisted (S8) | Recommend **yes** |

---

## 14. Non-goals

- SMS, native Follow Up Boss, AI Coach (`FIRST_CONFERENCE_LISTEDKIT_ADVANTAGE_STRATEGY.md` §4.3).  
- Replacing Gmail/Outlook with a platform-owned sending domain for deal mail.  
- A second agent framework or a generic “LLM plans the deal.” The plan engine stays deterministic.  
- Rebuilding Needs You, posture, or the tick endpoint.  
- Claiming wire-fraud protection beyond S4’s classifier.

---

## 15. Traceability

| Phase | Reuses | Modifies | Adds |
| --- | --- | --- | --- |
| S0 | EventBridge rules, `schedule_tick`, `KEY_AUTOMATION_LAST_TICK` | Tick completion vs HTTP; retry policy already 0 | Async/202 worker or equivalent; preview on prod; census; alerts; send idempotency |
| S1 | Needs You, plan automation, posture UI | Copy; one `needs_you` composer; handled_today | — |
| S2 | Give-back, `ai_needs_user`, executor | Cause watchers; per-deal run; error causes | Try-now per deal |
| S3 | Executor + `create_auto_drafts` | Satisfaction pre-check; Morning Queue packaging | `deal_runtime` wrapper |
| S4 | `ai_email_engine`, templates, `send_ai_draft` | Money v2; grounding on auto-drafts | Policy tags |
| S5 | `inbound_triage` | Evidence, refile, unmatched | Filtered UI |
| S6 | `_EMAIL_PLAYBOOK`, honesty counts | Promotion flags | Per-template flags |
| S7 | Review queue, `_send_draft` | Delayed send/hold in email engine only | Opt-in + countdown |
| S8 | Tick tenant loop | Skip rules | Per-tenant switches; platform table |

No phase modifies `FORBIDDEN_ACTION_TYPES` or lets the LLM compute dates.

---

## 16. Sources (re-read when implementing)

**Product / requirements:** `velvet-elves-data/requirements.txt` (if present in data; else backend-adjacent), `SYSTEM_DESIGN.md`, `TRANSACTION_PROCESSING_AND_AUTOMATION_GUIDE.md`, `TRANSACTION_PROCESSING_EVOLUTION_PLAN.md`, `TRANSACTION_PROCESSING_LOGIC_AND_WORKFLOW_GUIDE.md`.

**Prior plans:** `AUTOMATE_EVERYTHING_IMPLEMENTATION_PLAN.md`, `AUTO_EMAILING_SYSTEM_SUPERIORITY_PLAN.md`, `EMAIL_INTELLIGENCE_TEST_FINDINGS_AND_PLAN_2026-07-30.md`, `AGENT_EMAIL_GUIDELINE_AND_TASK_ATTACHMENTS_IMPLEMENTATION_PLAN.md`, `SCHEDULER_AND_STAGE_ENABLEMENT_RUNBOOK.md`.

**Findings:** `AI_AUTOMATION_TASK_SYNC_FINDINGS_2026-08-04.md`, `TASK_EMAIL_E2E_ISSUES_AND_SOLUTIONS_2026-07-28.md`, `NEEDS_YOU_CHROME_QA_2026-08-13.md`, `todo_list.md` §A.

**Content law:** `Agent_Email_Instructions.md`, `EMAIL_GUIDELINE_QUESTIONS_FOR_JAKE.md`.

**Release:** `FIRST_CONFERENCE_LISTEDKIT_ADVANTAGE_STRATEGY.md`.

**Code (canonical):**  
Backend: `app/services/ai_task_executor.py`, `ai_email_engine.py`, `ai_email_delivery.py`, `automation_posture_service.py`, `agent_policy.py`, `task_notification_service.py`, `task_classifier.py`, `email/inbound_triage.py`, `email/inbound_dispatch.py`, `api/v1/automation.py`, `api/v1/internal_schedules.py`, `email_template_library.py`.  
Frontend: `NeedsYouPage.tsx`, `AdminAIGovernancePage.tsx`, `WorkspaceHeader.tsx`, `GiveBackToAiButton.tsx`, `useAutomation.ts`, `AiEmailReviewPage.tsx`.

---

*This plan’s job is to make the automation we already shipped **honest, recoverable, and safe to run hourly** — then to add intelligence (satisfaction, inbound clerk, content policy) without growing unattended send. That is the comprehensive smart system this codebase can actually become.*
