# Jake TME AI architecture — implementation plan

**Source of truth:** `VE_Transaction_Management_Engine_AI_Agent_Architecture.md` (Jake, Phase 1 product architecture)  
**Current-state review:** `JAKE_AI_AGENT_ARCHITECTURE_STAGING_REVIEW.md` (2 Sep 2026)  
**Engineering wrap (15 Aug 2026):** `TME_AI_ARCHITECTURE_AND_SMART_AUTOMATION_PLAN.md` — use for the “wrap existing engines” thesis. Where it fights live code or later Audri answers, live code and `AUDRI_UPDATED_TASK_LIST_ANSWERS.md` (24 Aug) win. In particular: Assisted does **not** unattended-send; do **not** seed task 235 (Audri Q13 dropped it).  
**Staging:** `https://app.stage.velvetelves.com` / `https://api.stage.velvetelves.com`  
**Date:** 2 Sep 2026  
**Status:** Plan only. This file does not change product code.

This plan is how I close the gap between the **execution product** already on staging and Jake’s **intelligence architecture**. The bar is Jake §35 (the 30 acceptance principles), interpreted with Jake §37 (smallest technical architecture that honors the product rules).

**Revision, 2 Sep 2026 evening.** The first wrap is built and I tested it in a real browser. The two-grant law held: Autopilot is email, Trusted is dates, and neither implies the other. But I shipped the Contract dates control as three cards (Manual / Assisted / Trusted), and that was an error in this plan, not in Jake's rules. Manual and Assisted behave identically at the only moment that matters (a person clicks before a later date goes live), and those two words already mean something else one card up on the email control. Users read three choices as three behaviors and got confused. §5.2 and Phase 4 are corrected below to a two-state control: **You confirm** (default) and **Trusted**. The rule this adds for every later phase: a user-facing choice exists only when the behavior actually differs. Mirroring the spec's internal vocabulary on screen is not a goal; fewer, clearer controls are.

---

## 0. Verdict this plan starts from

Staging already runs a live TME: one staff assistant named Aime, Manual / Assisted / Autopilot, named library letters, Needs You, Fast intake extract, Dual files, send gates, and no legal advice in prompts.

Staging does **not** yet run Jake’s intelligence stack: typed Memory & Provenance, a Conductor that classifies every event onto the 11-step ladder, Trusted Mode for contract-derived deadlines, earned client-update grants, client-facing Aime, multi-party consensus, vendor performance with a sample floor, brokerage exception escalation, or LSE handoff.

The 15 Aug engineering decision still stands: wrap the engines that exist. Do not stand up a Conductor microservice, a specialist LLM per domain, or a vector memory of private chats.

**One sentence:** keep the cage, type the file’s truth, put a thin Conductor in front of the engines we already trust, then add client Aime and governed learning without expanding authority by silence.

---

## 1. How to read this document

Jake §36 explicitly does not define model, database, event bus, MVP, or UI. This plan **does** choose those things because it is an implementation plan, not a product constitution.

If a later choice fights Jake’s product rule, keep the product rule (Jake §37). Do not simplify by:

- converting inference into fact
- letting learned behavior expand authority
- treating silence as consent
- treating one client as speaking for all
- exposing internal reasoning trees
- collapsing professional judgment into automation
- auto-providing paid negotiation intelligence
- pulling pre-pending listing or buyer-search work into TME

Companion files this plan does not replace:

| File | Job |
|---|---|
| `VE_Transaction_Management_Engine_AI_Agent_Architecture.md` | Product constitution |
| `JAKE_AI_AGENT_ARCHITECTURE_STAGING_REVIEW.md` | What staging honors vs misses (2 Sep 2026) |
| `TME_AI_ARCHITECTURE_AND_SMART_AUTOMATION_PLAN.md` | Wrap-engines thesis. Stale on Assisted send and task 235. |
| `AIME_AI_AUTOMATION_TESTING_GUIDELINES_2026-08-18.md` | Testing documentation I write for Audri each round. Describes what shipped so she can test it. **Not a requirements source** |
| `AUDRI_UPDATED_TASK_LIST_ANSWERS.md` | Dual / utility / title (Q1). Also Q3 extra Autopilot letters and Q13 drop 235. |
| `IMPLEMENTED_CORE_FUNCTIONS_CHECKLIST.md` | Shipped-function test list (execution layer) |

One relationship this plan must never invert: the testing guidelines are **point-in-time documentation of shipped features**. I write them so Audri can test a round. They are not requirements, and nothing in this plan may be justified or gated by them. Requirements come from Jake's architecture document and the answered Jake/Audri questions. Example: the guidelines mark a client-facing Aime chat as a fail this round only because that chat is not in the product yet. That line does not forbid Phase 7. When a phase changes what a tester should see, I update the guidelines to match the product. The guidelines follow the product, never the other way around.

---

## 2. Product rules that stay law

These are not optional polish. Every phase must preserve them.

1. **One Aime.** Users never meet Conductor, Transaction Intelligence, or any other internal name.
2. **Advisor, never the authority.** Agent (and assigned TC) decide. Clients keep their own decisions.
3. **If Aime can do it, she should** — only when information, authority, risk, and contradiction checks pass.
4. **No material assumption as fact.** Hypotheses are questions. They are not written onto verified columns.
5. **Provenance on every material fact.** What, where, when, observed vs reported vs inferred vs confirmed, superseded vs conflicting.
6. **Authority is explicit.** Repeated no-edit, silence, and “the last five were fine” never grant send or deadline activation.
7. **Literal contract language only.** Quote the date. Do not say what a clause legally means.
8. **Ambiguity increases human involvement** regardless of Autopilot or Trusted Mode.
9. **Negotiation intelligence is a paid add-on.** Core TME detects that judgment is needed and routes. It does not negotiate.
10. **Clients never receive internal brokerage-risk escalation.**
11. **Pre-pending stays out.** TME starts at accepted / executed contract.
12. **Chat cannot send mail.** Library send stays on the executor + `send_ai_draft` path.

---

## 3. What already honors Jake (do not rebuild)

Reuse these. Phase work wraps them; it does not replace them.

| Capability | Where it lives | Jake it already covers |
|---|---|---|
| Staff Aime chat | `transaction_agent.py`, `dashboard.py` `/ai-chat`, AgentPane, FAB | §5.1 staff, §35.1–2 |
| Chat cannot send | `agent_policy.py` forbids `send_email` | §3.2, §25 |
| Deal posture | `automation_posture_service.py` Manual / Assisted / Autopilot. `playbook_sends_allowed` is **Autopilot only**. | §22 send axis only |
| Named library letters | `ai_task_executor.py`, `_EMAIL_PLAYBOOK` | §3.3, §35.9 (narrow) |
| Hard email gates | `agent_email_policy.py` | §9.4, §24, §25 |
| Needs You leftover pile | `needs_you_composer.py`, Needs You UI | §14 Inform / leftover |
| Overnight tick | `internal_schedules.py` | §33 event loop (partial) |
| Fast intake extract | Textract + LLM parse, wizard Confirm Details | §5.4 extract, §8.1 at create |
| Later document control | `contract_resolution.py`, `amendment_date_gate.py` | §5.4 supersession (partial) |
| Dual agency rows | `filter_both_representation`, Audri Q1 | §2 Dual, §5.3 dual state (partial) |
| Issue detectors | `agent_issues.py` (deterministic) | §13 (partial) |
| Suggestions | `suggestion_engine.py` | §5.5 (partial) |
| Briefing + Task Queue | dashboard briefing, My Task Queue | §15 (partial) |
| Agent + TC same file | workspace roles | §4.2, §35.10 |
| Terminated status | `TransactionStatus.TERMINATED` | §7 stage 13 and §30 (status exists; LSE handoff does not) |
| Post-close task rows | 453/455, testimonials, gifts, tax exemptions | §29 tasks exist |
| Inbound email triage | money / dates / documents | §11 email only |
| Provider-agnostic AI | settings / factory | §35.29 |
| No listing/search TME | wizard is accepted-contract intake | §2.2, §35.30 |

**Do not** rewrite Dual as a specialist. Keep Audri Q1: Dual populates buyer-target and seller-target rows; vendor targets once; co-op-target rows stay off; Both-only extras **95, 115, 135, 155, 215, 305, 375, 505** stay off; also stop sell-only extra **380** (Audri ID map: one Closing Gift = live 370). 300 and 310 Deliver Title = `standard`; 150 buyer utility = `standard`; 160 co-op utility = `suppressed`.

Durable Dual restore still needs `supabase/migrations/20261007090000_restore_audri_dual_q1.sql` applied through the usual deploy path. Staging was corrected by template API PUT on 2 Sep. That is not enough for the next environment.

---

## 4. Target architecture (smallest wrap)

Jake’s diagram stays the north star. The implementation is one Python conductor plus typed facts plus specialist **functions** that return findings and never execute.

```text
Aime (staff chat, later client chat, Aime-signed library letters)
  → Conductor  app/services/aime_conductor.py
       assemble context, score risk, check authority, pick ladder, gate execution
  → Specialist functions (hidden):
       Transaction Intelligence   agent_issues + deal_runtime + stage overlay + parties
       Contract & Document        packet parse + contract_resolution + fact store
       Advisory                   suggestion_engine + ranked next action + strong challenge
       Client Interaction         new policy module; portal Aime after Phase 7
  → Memory & Provenance           transaction_facts (source of typed truth)
  → Learning signals              structured events only (Phase 10)
  → Product Intelligence          admin-only (Phase 10)
  → Execution cage (unchanged)    playbook send | draft | Needs You | refuse | escalate
```

**Rules for this mapping**

- A specialist returns `{finding, evidence, provenance, confidence, missing, contradictions, hypothesis?}`. It never sends mail or completes a task.
- The Conductor is deterministic Python. An LLM may word a question or a talking-points pack. It does not vote.
- Execution still goes through `send_ai_draft`, `agent_actions.py`, and Needs You. The Conductor may not grow `_EMAIL_PLAYBOOK` or `AUTO_ELIGIBLE`.
- Internal names never appear in UI copy, emails, or client portal.

---

## 5. Two independent axes (do not collapse them)

Today Autopilot is send authority. Jake’s **Trusted Mode** is deadline-activation authority. They are different grants.

| Axis | Values | Owns |
|---|---|---|
| **Deal posture** (exists) | Manual / Assisted / Autopilot | Whether routine *actions* auto-apply, whether named *mail* may send **unattended** (Autopilot only), whether drafts arrive Ready |
| **Contract dates** (shipped 2 Sep, corrected same day) | **You confirm / Trusted** on screen (stored as `obligation_autonomy`) | Whether a contract-derived deadline becomes an **authoritative task** without a human tick |

### 5.1 Deal posture (keep)

- **Manual:** Aime extracts, drafts, and asks. No library send.
- **Assisted:** Aime prepares. Human taps Send / Apply.
- **Autopilot:** Named library letters may send when gates pass. Chat still cannot send.

New tenants stay **Manual** in code (`DEFAULT_TENANT_POSTURE`). The QA tenant on staging is Autopilot by choice; that is not the product default.

### 5.2 Contract dates (corrected to two states)

Jake §8 names Manual, Assisted, and Trusted for deadline verification. In this product, Manual and Assisted are the same at the only moment that matters: a person clicks before a later date becomes official. Jake's Assisted differs only in how much Aime prepares automatically, and Aime prepares either way here. Three cards where two behave the same confused testers on 2 Sep, and Manual / Assisted already mean something else on the email card beside it.

**The product shows two states:**

- **You confirm** (default). Aime prepares the change: old date, new date, source document. A person clicks before the date is official. This covers Jake's Manual and Assisted.
- **Trusted.** An explicit grant. Clear, complete, non-conflicting contract dates may go live on their own. Unclear, incomplete, conflicting, or superseding context always returns to a person. Trusted never sends mail.

Jake's Assisted row returns as a third state only if Jake writes the narrower automated-verification grant from §8.2. Do not build it ahead of that call.

**Implementation notes**

- Storage and API keep `obligation_autonomy` with `manual | assisted | trusted` so nothing breaks. Only `trusted` activates; a stored `assisted` already behaves exactly like `manual` (`can_auto_activate_deadlines`). The UI writes `manual` or `trusted` and renders any legacy `assisted` as You confirm. No migration.
- User-facing words are **Contract dates**, **You confirm**, **Trusted**. Never "obligation autonomy."
- One card in Settings with one Save. On the deal, a small **Trusted dates** group inside the existing automation menu: on for this deal, off for this deal, follow the workspace. Not a second Manual / Assisted / Trusted block.
- Every surface that shows this setting repeats the always-true line: unclear or conflicting contract dates never go live on their own.

The split itself shipped and stays law: Autopilot is email, Trusted is dates, and the old interim mapping (Autopilot treated as weak Trusted in `amendment_date_gate` and the Conductor) is gone. Do not reintroduce it. Existing Autopilot workspaces that relied on auto-applied amendment dates wait unless they turn Trusted on. Jake confirms that cutover in Question 1 of `AIME_INTELLIGENCE_WORKFLOWS_FOR_JAKE_AND_AUDRI.md`. The two-state dates control (You confirm / Trusted) is my call, not a Jake question.

Silence, no-edit drafts, and “the wizard already confirmed intake” do not turn on Trusted for later documents.

---

## 6. Memory & Provenance model

Existing transaction columns remain the **verified projection** the rest of the app already reads (`closing_date`, parties, contingencies, and so on). Typed rows sit beside them. An inference never writes a verified column.

### 6.1 Types (Jake §6.1)

| Type | May drive dates / Class A / obligations? | Example |
|---|---|---|
| `verified_fact` | Yes | Closing date confirmed in wizard or Confirm amendment |
| `reported_fact` | No, until verified | Lender emailed “appraisal Tuesday” |
| `decision` | Context only | Agent chose not to request an extension |
| `commitment` | No, until confirmed as an `obligation` | Agent told buyer “I’ll send the HOA packet today.” Record the commitment. Do not move dates or send Class A from it. |
| `inference` | No | “Buyer concern may be increasing” |
| `hypothesis` | No — ask | “Did the lender waive appraisal?” |
| `preference` | Wording / cadence only | Short client updates |
| `pattern` | Recommend only after sample floor | “This LO is slower to CTC” |
| `recommendation` | Needs You / Advisory | “Follow up with title” |
| `authority` | Gates execution | “Both buyers must sign” |
| `obligation` | Task engine, after verify or Trusted | Inspection response due date |

### 6.2 Table sketch (`transaction_facts`)

Not a Jake-deferred mystery. Implementation columns:

- `id`, `tenant_id`, `transaction_id`
- `fact_type` (enum above)
- `key` (stable: `closing_date`, `appraisal_scheduled_on`, `buyer_decision:extension`)
- `value_json`
- `source_kind` (`document`, `email`, `user_confirm`, `chat`, `system`, `party_report`)
- `source_id` (document id, communication log id, user id)
- `source_at`
- `confidence` (0–1, stored, not shown as a fake precision)
- `privacy_scope` (`transaction`, `agent`, `brokerage`, `platform_signal`)
- `superseded_by`, `conflicts_with`
- `learning_eligible` (boolean; private chat content stays false)

Parse / inbound write `reported_fact` or `hypothesis`. Fast intake may **fill the wizard form** with those values (prepare, not authoritative). Wizard Confirm Details, amendment confirm, and explicit agent edits promote matching keys to `verified_fact` and then write the projection column. If a newer source conflicts, do not overwrite. Open Clarify / Verify deadline.

Do not treat a backfill of today’s transaction columns as proof a human verified them. Backfill as `verified_fact` only for fields the wizard or an explicit edit already committed. Parse-only or API-filled fields that never passed Confirm Details backfill as `reported_fact`.

### 6.3 Privacy

Private conversation content never becomes platform learning. Eligible structured signals (deadline met/missed, recommendation accepted/rejected) may, in Phase 10, with `privacy_scope` enforced.

---

## 7. Risk × ladder (Conductor output)

### 7.1 Four contextual risk buckets (Jake §9)

Risk is contextual, not the action name. The same “send a reminder” can be Routine on one file and Relationship-risk on another.

1. **Routine / Operational** — organize, remind, collect, status. Eligible to Perform when authorized.
2. **Relationship / Service** — client anxiety, missed commitments. Inform / Recommend. Careful client wording. No silent **client-update** send. Named Autopilot Class A letters to clients (welcome, etc.) stay a separate explicit grant.
3. **Professional Judgment** — extensions, waives, inspection strategy, financing strategy. Request decision. Never Perform.
4. **Authority / Transaction** — client approval, multi-party consensus, execution, privacy, compliance. Request decision, Refuse, or Escalate.

### 7.2 Eleven rungs (Jake §14) mapped onto existing surfaces

Do not build a second inbox. Reuse Needs You, briefing, suggestions, chat, and the executor.

| Ladder | Product surface |
|---|---|
| No action | Activity log only |
| Internal watch | `watch` fact + optional briefing footnote |
| Early awareness | Low-priority AgentPane / briefing line |
| Perform | Executor / auto-apply (Routine + authorized). Named library send is Autopilot-only today. |
| Inform | Automation activity + digest. Not the same as Escalate. |
| Clarify | Needs You + Aime question (hypothesis, not a date write) |
| Recommend | Suggestion / proposed `agent_action` with why / evidence / what changed |
| Request decision | Proposed action, never auto-eligible |
| Strong challenge | Same, plus “what changed” evidence; only on a new verified fact vs a recorded `decision` |
| Refuse | Chat / API refusal + audit; no approvable action row |
| Escalate | Exception object (agent always informed). Brokerage-visible only when the threshold is met or the agent asks. **Never** collapse this into ordinary Needs You. **Never the client.** |

### 7.3 Allowed rungs by risk and posture

| Risk \ Posture | Manual | Assisted | Autopilot |
|---|---|---|---|
| Routine | Recommend / Inform | Draft named letters and auto-apply **file** work when granted. Human taps Send. | Perform named library letters when gates pass. Chat still cannot send. |
| Relationship | Inform | Recommend; Aime drafts, human sends | Named Class A client letters already on the playbook (welcome, etc.) may still Perform. **Earned client-update** send waits for the Phase 7 grant. No other silent client mail. |
| Professional judgment | Request decision | Request decision | Request decision (never Perform) |
| Authority / Transaction | Request / Refuse | Request / Refuse / Escalate | Same |

Trusted Mode (obligation axis) only changes whether a **high-confidence contract obligation** becomes authoritative. It does not move Professional Judgment into Perform.

Known obligations outrank AI suggestions. Aime may reorder work if all commitments remain achievable. She may not silently choose which explicit commitment to break (Jake §15).

---

## 8. Intelligence cycle (Jake §33)

Every meaningful event uses the same ten steps. Overnight tick is this loop over **Active** deals, including files that have reached the Closing or Post-Closing **stage** but are still Active. Completed, Closed, and Terminated stay out of the executor (`ai_task_executor` already no-ops unless `status == Active`). Do not move post-close work onto Closed files.

**Events in:** wizard confirm, document upload/parse, inbound email (later SMS/call summary), task due, hourly tick, user chat, party edit, mailbox reconnect, amendment detect, client portal question.

1. Aime receives the event.
2. Conductor identifies transaction, user, posture, obligation autonomy, authority, risk, relevant facts.
3. Only needed specialist functions run.
4. Specialists return typed findings.
5. Advisory synthesizes when advice is needed.
6. Conductor classifies the ladder rung.
7. Authority and approval are validated (posture + `agent_policy` + email policy + party consensus).
8. Aime performs, drafts, asks, refuses, or escalates.
9. Memory records the typed result.
10. Eligible structured learning signals fire (Phase 10).

A second tick must not send a second welcome (`deal_runtime` stays). Terminated deals: no Class A, no sweep, no client Aime perform.

---

## 9. Lifecycle overlay (Jake §7)

Keep today’s **health pill** (Critical / On Track / In Inspection / …). Add overlapping **TME stages** as a separate overlay. Do not reuse pill colors for stages.

Conceptual stages (may overlap):

1. Accepted / Intake  
2. Earnest Money  
3. Inspection / Due Diligence  
4. Financing  
5. Appraisal  
6. Title / Closing Preparation  
7. Contingency Resolution  
8. Clear to Close / Final Preparation  
9. Closing  
10. Possession  
11. Post-Closing Follow-Through  
12. Complete  
13. Terminated / Failed  

**Status vs stage (do not invert today’s vocabulary)**

Jake §7 Closing and Complete are **stages**. Product **status** today is a different axis. Live workflow and copy treat Completed and Closed as terminal history (`Active → Completed → Closed`). The executor, task nags, and often the workspace already freeze Completed / Closed / Terminated. Swapping those names so Closed means “closing happened, keep working” and Completed means “TME done” would reverse the live sequence and reopen archived files.

| Axis | Keep this meaning |
|---|---|
| Stage 9 Closing | Closing date reached or closing package in motion. File can still be **Active**. |
| Stage 11 Post-Closing Follow-Through | Open post-close tasks (453, 455, testimonials, etc.) on an **Active** file. |
| Stage 12 Complete | Derived: no managed obligation left. Aime may **suggest** the agent mark Completed/Closed. |
| Status Active | TME is still running, including after the closing event. |
| Status Completed / Closed | Terminal history. Executor skips. Nags skip. Do not bulk-reopen. |
| Status Terminated | Failed / dead file. No Class A. Ready for LSE handoff payload when LSE exists. |
| Status Incomplete / Paused | Health “Pending”; stages may still exist. |

Jake §29 is honored by **not** auto-moving Active → Completed/Closed on closing date, and by keeping post-close tasks on Active files. Do not auto-Complete because the closing date passed. Do not run the hourly send loop on Closed files.

Workspace header may show one lifecycle line (“Inspection · Financing”) beside the health pill.

---

## 10. Build sequence

Phases land on staging one at a time. They are **not** independently startable: Phase 2 needs Phase 1 facts, Phase 4 needs the Phase 2 Conductor (the interim Autopilot≈Trusted mapping bridged them until the Phase 4 split removed it), Phase 7 needs Phase 2. Parallel *module* work is fine if it does not destabilize named-letter send, Dual Q1, or chat-cannot-send.

Safety while building on staging: do not Send, confirm Run AI tasks, Send all ready, Disconnect, or Change status on live files. Do not staff `elf@cbstiles.com` on QA files.

---

### Phase 0 — Protect the execution layer

**Goal:** Intelligence work starts on a honest Dual library and a documented cage.

**Work**

1. Apply `20261007090000_restore_audri_dual_q1.sql` through the usual backend deploy so Dual flags are durable (305 off, 300/310/150 `standard`, 160 `suppressed`). Do not rewrite live task rows.
2. Keep `filter_both_representation` tests green (`TestFilterBothRepresentation`).
3. Confirm staff surfaces still say Aime, never specialist names.
4. Record the two-axis split in Settings copy as “coming,” without shipping Trusted yet.
5. Leave Audri Class A expansion closed **in this intelligence plan**. Audri 24 Aug Q3 already names more Autopilot letters (request tasks, CTC, closing-info, testimonials). That is execution-layer work in the task-list answers, not Conductor/facts work. Do not seed task 235 (Q13).

**Acceptance**

- Both-Fin `preview-tasks`: two Deliver Title (Buyer + Seller), buyer Deliver Utility Info, no 305, no co-op welcome.
- Buy-Fin / Sell-Fin / Buy-Cash do not leak 305.
- Chat still cannot send.
- Manual still kills library send.

**Jake closed:** none new. This keeps §2 Dual and §35.9 from regressing.

---

### Phase 1 — Memory & Provenance

**Goal:** Material intelligence is typed. Inference cannot silently become a transaction column.

**Backend**

1. Migration: `transaction_facts` as in §6.2, RLS tenant-scoped, indexes on `(transaction_id, key)` and `(transaction_id, fact_type)`.
2. Repository: `app/repositories/transaction_fact_repository.py` with `record`, `supersede`, `conflict`, `verified_projection`.
3. Backfill facts from current transaction columns. `verified_fact` only when the wizard or an explicit edit committed the field. Everything else is `reported_fact`.
4. Packet parse and inbound extract write `reported_fact` (or `hypothesis` when the message is “it looks like”). They do **not** write projection columns. Fast intake still **fills Confirm Details** so the human is not re-typing.
5. Wizard Confirm Details and explicit field edits promote matching keys to `verified_fact` and then update the projection.
6. `amendment_date_gate` records proposed obligations as `obligation` + `reported_fact` until confirm. Confirm promotes. (Sequencing note, now history: through Phase 3, Autopilot could still auto-apply explicit complete non-conflicting dates. The Phase 4 split removed that shortcut on 2 Sep.)
7. Feature 24 stays: dates-from-email do not auto-move verified dates.

**Frontend**

1. On key dates in the workspace (closing, inspection response, EM), show a quiet provenance line: Confirmed / Reported / Conflict. Do not show specialist names or confidence theater.
2. Confirm / Reject on a reported date is a first-class control (reuse amendment confirm UX where possible).
3. Aime chat, when asked “when is closing?”, answers from verified facts; if only reported, she asks rather than stating.

**Tests**

- Inbound “appraisal Tuesday” creates `reported_fact`, leaves `appraisal_date` null, Aime asks (Clarify copy is enough before the Conductor exists).
- Wizard confirm writes `verified_fact` and projection together. Fast intake still shows extracted dates on Confirm Details before that write.
- Conflicting amendment does not overwrite; opens Verify deadline.
- Explicit Autopilot amendment still auto-applies until Phase 4 (sequencing history, like item 6; the Phase 4 split has since removed it).

**Jake closed:** §3.4–3.5, §6.1, §35.3–4 (foundation).

---

### Phase 2 — Conductor, risk model, response ladder

**Goal:** Every event gets a ladder classification. Not every issue is a recommendation or an email.

**Backend**

1. `app/services/aime_conductor.py`:
   - Input: `event_type`, `transaction_id`, `actor_id` (nullable for tick).
   - Load: plan, parties, facts, posture, mailbox, open Needs You, recent decisions, and the contract-dates setting. (The interim Autopilot-as-weak-Trusted mapping lived here until the Phase 4 split removed it on 2 Sep. Do not reintroduce it.)
   - Output: `{risk, ladder, specialist_findings, action}` where `action` is call an existing function, open Needs You, open an exception (Escalate), chat reply, or noop.
   - Advisory in this phase is a stub: reuse `suggestion_engine` / `agent_issues`. The Phase 5 object is not required for the tick to route.
2. Risk classifier: deterministic rules first (overdue, missing doc, legal/wire topic, inspection negotiated, multi-party unsigned). LLM wording only after the bucket is set.
3. Map existing Needs You block codes and `agent_issues` severities onto ladder rungs (`watch` / `warning` / `blocker` → Watch / Recommend / Request or Clarify).
4. Hourly tick **per deal** goes through the Conductor instead of independently blasting executor + draft sweep with no shared picture. `deal_runtime` skip-if-already-sent stays.
5. Refusal path: capability + authority + legal-boundary messages. Never “I disagree with your professional judgment.”
6. Admin/support diagnostic payload (auditable): structured findings, not chain-of-thought. Privileged access is logged (Jake §28).

**Frontend**

1. Needs You groups can stay. Optionally tag the human-visible reason with Inform / Clarify / Decide, never with Conductor.
2. AgentPane uses the same refusal copy.
3. No new page named Intelligence.

**Tests**

- Second tick does not send a second welcome.
- “Tell them they can terminate” refuses, offers to draft a question for the agent, does not send.
- Weak stale-comms signal is Watch or Early awareness, not a recommendation email.
- Inspection Negotiated stays Request decision on Autopilot.

**Jake closed:** §5.2, §9, §14, §25, §28, §33, §34, §35.2, §35.24.

---

### Phase 3 — Transaction Intelligence (lifecycle, parties, friction)

**Goal:** The file has a diagnostic picture, not only a task list and a health pill.

**Lifecycle**

1. Derive `tme_stages: string[]` from dates + task families + verified facts. Overlap allowed. Closing and Complete are stages, not a status rename.
2. Header line next to health pill.
3. Keep post-close tasks on **Active** files. Do not auto-set Completed or Closed when the closing date passes. Aime may suggest archive when managed obligations are done.
4. Completed / Closed stay terminal. Executor, nags, and coverage prompts stay skipped (`ai_task_executor` already requires Active). Do not reopen existing Closed files to finish 453.
5. Terminated: no Class A, no sweep, no Perform. Preserve history.

**Parties (Jake §12, §4.4, §35.12)**

1. Expand `SUPPORTED_PARTY_ROLES` with first-class: `processor`, `underwriter`, `escrow`, `hoa`, `broker_manager`, `transaction_coordinator` (as party, not only user role). Keep aliases (`lender` → loan officer family).
2. **Send-matrix follow-through:** processors today ride the loan-officer family on To/CC (`task_email_planner.py`). Splitting `processor` out without updating that family will drop them from LO letters. Ship role + matrix in the same change. Assigned TC users must not get a duplicate TC party email unless a party row exists on purpose.
3. Party flags: `is_decision_maker`, `must_sign`, `authority_for` (JSON list of action keys).
4. Multiple people with the same role already exist as rows. Enforce on **consent language** and **client updates**: Aime will not say “the buyers agreed” unless every required decision-maker is on the evidence.
5. Recipient expansion by role (all co-contacts) stays on send. That is necessary but not sufficient for consensus. Dual-buyer welcome already doing this is not a Phase 3 invention.

**Issue detection (Jake §13)**

Extend `agent_issues.py` (still deterministic, no LLM in detection) with ladder hints for:

- approaching / missed deadline
- missing document / signature
- conflicting document
- unresolved contingency
- missing EM confirmation
- inspection / financing / appraisal / title delay
- missing client decision
- multiple decision-maker conflict
- third-party non-response
- communication gap (hypothesis, not invented history)
- stage inconsistency
- closing readiness
- post-closing obligation at risk

Each detector emits `{condition, evidence, risk_hint, ladder_hint}`. Conductor routes.

**Frontend**

- Contacts: decision-maker and must-sign checkboxes.
- Do not invent a 13-step wizard. Stages are derived.

**Tests**

- One buyer’s reply is not both buyers’ approval (consent language + `is_decision_maker`).
- Closing date passing does not flip status to Completed/Closed; post-close tasks remain on Active; executor still runs.
- A Closed fixture still makes the executor no-op (regression).
- Terminated: executor no-ops.

**Jake closed:** §5.3, §7, §12, §13, §29 (partial), §35.10, §35.12–13, §35.27.

---

### Phase 4 — Contract & Document Intelligence + Trusted Mode

**Goal:** Extract stays literal. Authoritative deadlines stay human-verified by default. Higher autonomy is an explicit grant that stays simple on screen.

**Status 2 Sep 2026:** the split shipped in the first wrap. Autopilot no longer auto-applies later dates; only Trusted does, and fuzzy still waits. Packet parse, wizard confirm, `contract_resolution`, and `amendment_date_gate` reading the real setting are all in place. What shipped wrong first was the UI: three date cards (Manual / Assisted / Trusted) plus a second three-option block in the deal menu. Local testing found that confusing, so the same evening I rebuilt it to the two-state control from §5.2 and click-verified it in the browser: one card with You confirm / Trusted, a Trusted dates on / off / follow group in the deal menu, and legacy `assisted` rendering as You confirm.

**Work**

1. **Contract dates setting** on the tenant, default **You confirm**, optional per-deal pin, independent of posture. Two states on screen: **You confirm** and **Trusted**. Copy is about when a date from the contract becomes official. Never “send mail,” never “obligation autonomy.”
2. Storage keeps `obligation_autonomy` (`manual | assisted | trusted`). Only `trusted` activates. The UI writes `manual` or `trusted`; a legacy `assisted` renders and behaves as You confirm. No migration.
3. Candidate obligation diffs for any controlling later document (not only closing/possession). Needs You “Verify deadline” whenever dates are You confirm, and on Trusted when any hard-boundary flag is set.
4. Trusted auto-activate **only if** all are true: language explicit, data complete, no conflicting document, no amendment ambiguity, authority valid, grant present. Else human.
5. **Cutover** (shipped): Autopilot stopped implying Trusted. Do not silently preserve the old auto-apply. Jake confirms existing Autopilot offices in the questions doc (Question 1). The on-screen dates control is two states, You confirm and Trusted; that is not a Jake question.
6. Interpretation requests (“what does this clause mean legally?”) → Request decision / Refuse legal advice. Quote literal text if present.
7. Conflicts already block send (`**[CONFLICT: …]**`). They must also block Trusted activation.
8. Human does not re-type extracted dates. Aime prepares the obligation; the human ticks.

**Frontend**

- Settings → AI & Automation: one **Contract dates** card beside Automation posture. Two choice tiles (You confirm / Trusted), the always-true line (“Unclear or conflicting contract dates never go live on their own”), one **Save dates** button. Not three cards.
- Deal header: a small **Trusted dates** group inside the existing automation menu: on for this deal, off for this deal, follow the workspace. Not a second Manual / Assisted / Trusted block.
- Verify deadline Needs You: old value, new value, source document, Confirm / Keep current / Edit.

**Tests**

- Addendum that moves closing does not silently rewrite `closing_date` on You confirm.
- Same addendum on Trusted with explicit complete language auto-activates and writes `verified_fact` + provenance.
- Fuzzy addendum on Trusted still waits.
- A stored legacy `assisted` value behaves exactly like You confirm and renders as You confirm.
- Autopilot + dates You confirm: library letters may send; new amendment dates wait.

**Jake closed:** §5.4, §8, §24, §35.5–8.

---

### Phase 5 — Advisory Intelligence

**Goal:** One clear next action for the book. Recommendations carry why, confidence, evidence, and what changed. Strong challenge is rare and evidence-based.

**Work**

1. Recommendation object: `{recommendation, why, confidence, evidence[], what_changed, ladder}`. Store as `recommendation` facts. Do not auto-execute.
2. Portfolio ranker over Needs You + suggestions using Jake §15 factors: deadline proximity, contractual consequence, client-service consequence, authority risk, transaction risk, explicit commitments, closing impact, third-party dependency, missing information, strength of evidence, prior agent decisions, time sensitivity, chance to prevent delay.
3. **Known obligation outranks a suggestion.** Sort must prove this in tests.
4. Strong challenge: only when a **new verified fact** contradicts a recorded `decision`. If the agent reaffirms, raise the threshold. Time passing is not new evidence.
5. Optional talking-points pack for Relationship-risk (staff only): acknowledge concern, known facts, known next steps, uncertainty, what the agent will do. Do not invent reassurance (Jake §17).
6. Recommendation competition: if two specialists disagree, lower confidence or Clarify. Do not pick silently.

**Frontend**

- Active Transactions / briefing: one “Do this next” line with why.
- Suggestion cards show evidence and what changed.
- Strong challenge uses a distinct card, not a louder suggestion.

**Tests**

- Overdue EM confirmation outranks a stale “ask for a testimonial” suggestion.
- Strong challenge does not fire on “it’s been two weeks.”
- Strong challenge does fire when a verified CTC date moves after the agent recorded “we’re fine to close Friday.”

**Jake closed:** §5.5, §15, §17 (talking points), §23, §35.15, §35.23.

---

### Phase 6 — Communication monitoring (beyond email)

**Goal:** Architecture supports channels even when an integration is missing. Absence is not proof. Gaps become hypotheses.

Email is live. SMS, calls, voice notes, and platform messages are not.

**Work**

1. Channel adapter interface: `{channel, occurred_at, parties, transcript_or_body, source_id}`. Email implements it first. SMS / call-summary / voice-note adapters can be empty without blocking the Conductor.
2. Communication extraction writes `reported_fact` when the statement is explicit (“appraisal is Tuesday”). Never `verified_fact`.
3. Missing-channel detection: if documents or a party message imply progress Aime cannot see, Conductor Clarifies with Jake’s example pattern: “It looks like we may be further ahead than I expected. Did the appraisal come back, or did the lender waive that step?” Record a `hypothesis`. Confirm before either explanation becomes fact.
4. Absence-is-not-proof: no detector may conclude “the call did not happen” because Aime has no call log.
5. Manual agent updates are a first-class channel (already partly true via workspace edits).

**Frontend**

- Clarify cards offer **one** of the competing explanations, or “neither / something else.” Do not use a single Confirm that could promote both hypotheses.
- Do not show “no SMS connected” as a client failure.

**Integrations:** ship email-complete in this phase. SMS/call can land as “supported conceptually, not connected” until a provider is chosen (Jake §36). Do not fake call transcripts.

**Jake closed:** §11, §35.14.

---

### Phase 7 — Client Interaction Intelligence (bounded client Aime)

**Goal:** Buyers and sellers can ask Aime for status, next steps, and reassurance without legal advice, negotiation, manufactured consensus, or internal risk workflow.

**Gating:** Phase 2 Conductor + the client policy module must exist, and Jake makes the timing call (Question 2 in `AIME_INTELLIGENCE_WORKFLOWS_FOR_JAKE_AND_AUDRI.md`). The testing guidelines are not a gate: their current client-chat fail line only records that the chat is not in the product yet. When this phase ships, I update the guidelines so Audri tests the bounded chat as an expected pass.

**Allows (Jake §4.3, §5.6)**

- Transaction status from verified facts
- Known next steps in plain language
- Administrative information
- Known milestones
- General process questions (glossary)
- Capture a question for the agent
- Capture missing context
- Reassurance that does not invent facts
- Reminders the agent already authorized
- Route professional or contractual questions to the agent

**Refuses**

- Legal advice or interpretation beyond literal content
- Negotiation
- “Your co-buyer said yes”
- Manufacturing consensus
- Internal Needs You, block codes, brokerage escalation
- Wire / banking
- Representing that a client agreed unless authority is confirmed

Cautious inferences (frustration, urgency, reduced engagement) stay `inference` facts on the **staff** file. They are not shown to the client as diagnoses. Never label personality or motive.

**Client updates (Jake §16, §32)**

1. **Initial:** Aime drafts. Agent/TC reviews, edits, approves, sends.
2. **Learning:** observe whether edits are made, what changed, which updates are consistently approved.
3. **Suggestion:** after a documented streak of no-edit or low-edit sends, Aime **asks** to automate that template. Silence ≠ yes.
4. **Explicit grant:** agent turns on automation for that context (template + audience + risk Routine). Grant is stored as `authority`, not inferred.
5. **Execution:** send only if posture is Assisted or Autopilot (Manual remains the kill-switch), information is complete, no contradiction, grant still valid, no higher-risk condition. Material new information before send invalidates stale approval. The grant never bypasses Manual and never bypasses `agent_email_policy` hard gates.

Named Class A letters (buyer/seller welcome, etc.) are not this product. They stay on the executor playbook.

**Frontend**

- Represented client portal: Aime thread **in addition to** “Messages with your team,” with honest labels.
- Client never sees Needs You titles or playbook codes.
- Staff sees captured client questions in Needs You / Clarify.

**Tests**

- “Can I back out?” → routes to the agent, does not interpret the contingency.
- Two buyers: Aime will not treat one portal user as both.
- Internal issue titles do not leak.
- No-edit streak suggests automation; leaving the prompt unanswered does not enable send.
- Manual + a client-update grant still does not send.

**Jake closed:** §4.3, §5.6, §16, §17, §32, §35.11, §35.17, §35.26.

---

### Phase 8 — Escalation and brokerage visibility

**Goal:** Escalation is exception-based. Ordinary Aime–agent advisory stays private. Clients are never internal-escalation recipients.

**Work**

1. Escalation recipients: agent, assigned TC, then managing broker / brokerage admin when threshold is met.
2. Jake §36 deferred exact thresholds. Interim product defaults (confirm with Jake before production):
   - Routine unresolved > 7 days → stay with agent, Watch on TL dashboard
   - Authority / compliance / misrepresentation risk → immediate brokerage-visible exception
   - Professional judgment stays with the agent unless they request help or a hard compliance rule fires
3. Ordinary chat remains private by default.
4. Auto-downgrade **routine** issues when reliable evidence confirms resolution. Professional Judgment, Authority/Transaction, compliance, and major brokerage-risk require an authoritative human resolution.
5. Resolution does not erase history (audit, facts, learning eligibility).
6. Client-facing messages never include the internal escalation trail.

**Frontend**

- Team Lead / Admin: Exceptions list, not a dump of every Aime thread.
- Agent can “ask my broker” explicitly (creates an exception on purpose).

**Jake closed:** §26, §27, §35.25–26.

---

### Phase 9 — Preferences (how, not what)

**Goal:** Aime learns how the agent likes work done. Preferences never expand what she may do.

**Work**

1. `users.settings_json` writing style, update length, cadence, call-vs-email preference, how recommendations are presented.
2. Scope starts narrow and widens only with evidence: interaction → client → transaction → workflow → agent-wide (Jake §22).
3. Explicit instruction always overrides learned preference.
4. Preferences may follow the agent between VE organizations.
5. These do **not** follow a brokerage move: client information, transaction history, brokerage-private information, organization-specific strategies, prior autonomy grants (Trusted, client-update send, Autopilot).

**Tests**

- Prohibited phrase in user style never appears in a draft.
- Style cannot bypass `**[MISSING: …]**` / legal gates.
- Moving an agent to a new tenant copies style, not Autopilot, not Trusted, not client data.

**Jake closed:** §3.6, §22, §35.6 (grants stay explicit).

---

### Phase 10 — Learning, vendors, product intelligence

**Goal:** Structured signals only. No private-chat promotion. No vendor claim without a sample floor.

Jake §36 deferred exact sample-size and confidence formulas. Until Jake sets a number, **Aime may not make performance claims in the product.** She may still count internally. Do not ship the “across a sufficient number of recent transactions…” sentence until the floor exists; that sentence **is** a claim.

**Signals (examples)**

- Deadline met / missed
- Recommendation accepted / rejected
- Agent correction
- Vendor response time
- Financing / title / inspection / closing delay
- Document error
- Required follow-up
- Party responsiveness
- Objective transaction outcome

**Evidence strength (Jake §21)**

1. Explicit correction / instruction  
2. Explicit response  
3. Repeated consistent behavior  
4. Single observed behavior  
5. AI inference about motive (weakest; may not become confirmed intent)

Correlation is not causation. Stale learning weakens. Learn from failures, not only successes.

**Vendor intelligence (Jake §18–19, §35.19–20)**

- Attribute to the **person** when identity is known; company / office / market otherwise.
- No “this lender is bad.”
- Explain evidence **only after** the floor exists. Example once allowed: “Across a sufficient number of recent transactions, this loan officer has taken longer than the comparison group to reach clear-to-close.”
- Follow-up: identify delay, recommend, Perform only if already authorized and Routine; else Request decision.

**Cross-transaction patterns (Jake §20–21)**

- Low-risk patterns may auto-promote after validation.
- Patterns that materially influence professional judgment need authorized human governance before promotion.
- Promoted patterns can be weakened, demoted, suspended, or retired.

**Product Intelligence (Jake §6.3)**

Admin-only: where files stall, where agents correct Aime, ignored workflows, useful vs dismissed recommendations, unused features, where Aime creates noise. Never used in client-facing reasoning.

**Private chats:** `privacy_scope` + `learning_eligible=false` on conversation content. Structured signals only.

**Jake closed:** §6.2–6.3, §18–21, §35.16, §35.19–22.

---

### Phase 11 — LSE boundary (TME side only)

**Goal:** Honor failed-file and listing-origin handoff **contracts** without building the Listing Success Engine.

LSE does not exist in the product. Jake §30–31 and §35.28 still require TME to be ready.

**If the file originated in LSE (future)**

Aime stays the same assistant. TME accepts an inherit payload: seller identity, decision-maker authority, communication preferences, concerns, agent instructions, listing history, material decisions, commitments, communication history, relationship context, provenance, accepted-contract context, unresolved issues. No duplicate data entry.

**If the file did not originate in LSE**

On Terminated, Aime may **offer** LSE as a paid capability. TME must not silently start listing marketing, showings, or pricing.

**Work now**

1. Define `TmeLseHandoff` JSON (versioned) produced on Terminated and accepted on intake `source=lse`.
2. UI on Terminated: “Offer Listing Success” is disabled/teaser until LSE exists, with honest copy. No silent listing workflows.
3. Intake already starts at executed contract. Keep it that way.

**Do not build:** listing marketing, showings, buyer search, pre-offer negotiation (Jake §2.2, §35.30).

**Jake closed:** §30–31, §35.28 as a TME-side contract; LSE product remains out of TME.

---

## 11. Explicitly not in this plan

| Item | Why |
|---|---|
| Seven LLM specialists / Conductor microservice | Jake §37 smallest architecture; 15 Aug wrap |
| Vector memory of private chats | Privacy + inference ≠ fact |
| Negotiation add-on (inspection strategy, repair credits, waive/terminate advice) | Jake §10; paid; core TME routes to the agent |
| Delayed auto-send countdown | Audri D |
| Bulk ToBeAutomated → Class A | Audri C / this plan’s intelligence scope. 24 Aug Q3 is a **parallel execution** track, not blocked by Conductor work |
| Task 235 seller inspection | Audri Q13 dropped it; 15 Aug plan is stale |
| Client as escalation target | Forbidden |
| Pre-pending buyer/seller work | Jake §2.2 |
| Exact confidence / vendor-sample / escalation formulas as if Jake defined them | Jake §36; use interim defaults, confirm with Jake |
| CASA AL1 / auth hardening | Outside this architecture |
| Commission payouts, AI Coach teaser, native mobile | Parked product, not Jake TME intelligence |
| Rewriting Dual away from Audri Q1 | Binding task law |

---

## 12. File-level map

| Area | Backend | Frontend |
|---|---|---|
| Dual durable restore | `20261007090000_restore_audri_dual_q1.sql`, `dependency_engine.py` | — |
| Facts | new table + `transaction_fact_repository.py`; parse/wizard/inbound writers | provenance on key dates |
| Conductor | **new** `aime_conductor.py`; `internal_schedules.py` per deal | Needs You labels only |
| Risk / ladder | Conductor + `agent_issues.py` hints | Inform / Clarify / Decide copy |
| Lifecycle | `tme_stages` overlay on Active files; status Completed/Closed stay terminal | header line |
| Parties | `party_roles.py` + flags on `transaction_parties` | Contacts checkboxes |
| Trusted Mode | `automation_posture_service.py` sibling setting; `amendment_date_gate.py` reads it | One Contract dates card (You confirm / Trusted); Trusted dates on / off / follow group in the deal menu |
| Advisory | `suggestion_engine.py` recommendation object + ranker | “Do this next”; challenge card |
| Channels | adapter over inbound email; stubs for SMS/call | Clarify hypothesis card |
| Client Aime | new policy module; portal chat endpoint; still no `send_email` from chat | portal Aime + team thread |
| Client updates | draft → streak → suggest → `authority` grant → send | review UI; grant toggle |
| Escalation | exception rows; TL/Admin API | Exceptions list |
| Preferences | `users.settings_json`; travel-on-move copy rules | writing style settings |
| Learning | signal table; vendor stats; no claims until floor | admin Product Intelligence |
| LSE | handoff JSON + Terminated teaser | disabled Offer LSE |

Execution cage files that this plan must not bypass: `ai_task_executor.py`, `ai_email_delivery.py`, `agent_email_policy.py`, `agent_policy.py`, `deal_runtime.py`, `needs_you_composer.py`.

---

## 13. Jake §35 → phase that proves it

| # | Principle | Phase | Proof |
|---:|---|---|---|
| 1 | One continuous Aime | 0, 7 | Staff already; client Aime uses the same name |
| 2 | Specialists stay hidden | 2 | No specialist strings in UI fixtures |
| 3 | Provenance-aware truth | 1 | `transaction_facts` types |
| 4 | Inference ≠ fact | 1, 6 | Inbound date does not write projection |
| 5 | Deadlines human-verified by default | 4 | Verify deadline on You confirm |
| 6 | Higher deadline autonomy is explicit | 4 | Trusted toggle; Autopilot ≠ Trusted |
| 7 | Ambiguity increases human involvement | 4 | Fuzzy addendum waits on Trusted |
| 8 | Literal language, no legal interpretation | 2, 4, 7 | Chat / client refusal fixtures |
| 9 | Perform routine when authorized | 2 | Executor still the only Perform mail path |
| 10 | Agent and TC share the file | already | Keep |
| 11 | Clients interact with Aime under client rules | 7 | Portal fixtures |
| 12 | Multiple decision-makers stay individual | 3, 7 | Flags + consent language tests |
| 13 | Proactive deadlines and friction | 3 | Expanded `agent_issues` |
| 14 | Gaps are hypotheses, not invented history | 6 | Clarify copy; absence ≠ proof |
| 15 | Prioritize the pending book | 5 | Ranker; obligation outranks suggestion |
| 16 | Third-party follow-up when authorized | 5, 10 | Recommend / Perform only if granted |
| 17 | Client updates earned + explicit | 7 | Streak suggests; silence does not grant |
| 18 | Negotiation add-on separate | out | No inspection-negotiated auto-send |
| 19 | Vendor sample before claims | 10 | No claim until Jake sets floor |
| 20 | Attribute vendor performance to the person | 10 | Person key when known |
| 21 | Cross-transaction learning via governed signals | 10 | Promotion / demotion |
| 22 | Private chat ≠ platform content | 1, 10 | `learning_eligible` |
| 23 | Strong challenge only with new evidence | 5 | Fixture vs time-passing |
| 24 | Refuse prohibited execution, not disagreement | 2 | Refusal copy |
| 25 | Brokerage visibility is exception-based | 8 | Exceptions list |
| 26 | Client never sees internal risk workflow | 7, 8 | Portal leak tests |
| 27 | Closing does not end post-closing work | 3 | Closing stage on Active; executor still Active-only; no auto-archive |
| 28 | Failed files can return to LSE | 11 | Handoff JSON; no silent LSE |
| 29 | Provider/model/DB out of Jake spec | already | Keep factory |
| 30 | Pre-pending stays out | already | Keep wizard boundary |

**Definition of done for “staging reflects Jake”:** every row above is Honored or Honored-by-absence (18, and 28 as a TME-side contract). Partial is not done.

---

## 14. Testing strategy

Automated tests first, then staging Chrome with the same send-safety practice used in the Aime testing rounds.

| Phase | Must-have automated coverage | Staging check (no Send unless the case is a named letter on a plus-address I own) |
|---|---|---|
| 0 | Dual preview-tasks | Both-Fin / Buy-Fin library |
| 1 | reported vs verified writes | inbound date does not move closing |
| 2 | tick idempotency; legal refusal | Needs You shows Clarify vs Decide |
| 3 | Active through post-close; Closed still skips executor; consent flags | header lifecycle line |
| 4 | Trusted vs Autopilot split; fuzzy wait; legacy `assisted` behaves as You confirm | Verify deadline after addendum |
| 5 | obligation outranks suggestion; strong challenge | “Do this next” |
| 6 | hypothesis not written as fact | Clarify copy |
| 7 | client “can I back out?”; no-edit ≠ grant | portal Aime + team thread |
| 8 | client cannot see exception payload | TL Exceptions |
| 9 | style cannot bypass gates | — |
| 10 | no vendor claim below floor | admin-only Product Intelligence |
| 11 | Terminated emits handoff JSON | Offer LSE stays inert |

Do not re-test CASA AL1. The Aime testing guidelines are round documentation, not acceptance criteria for this plan: their current client-Aime fail line neither blocks Phase 7 nor records a Jake decision about it. I update the guidelines when a phase ships.

---

## 15. Open questions that still change architecture

Do not guess these in code. Default in brackets is the interim I will implement if the call does not land first.

1. **Naming.** Keep Manual / Assisted / Autopilot for **send**. Add Trusted for **deadlines**, or brand all three with Aime. [Keep Autopilot for send; add Trusted as a separate setting.]
2. **Obligation autonomy vs posture.** Separate controls or mapped. [Separate. Autopilot ≠ Trusted. On screen the dates control is two states, You confirm and Trusted. Assisted returns only if Jake writes the §8.2 narrower grant.]
3. **Client Aime timing.** When do buyers and sellers get the bounded chat. Jake's call (workflows doc Question 2). [Phase 7 in order, after the client policy module exists. The testing guidelines follow the product and get updated when it ships; they are not part of this question.]
4. **Vendor sample floor.** A number or “do not claim.” [Do not claim until Jake sets a number. Store counts anyway.]
5. **Escalation threshold.** [Interim in Phase 8; confirm before production brokerage-visible exceptions.]
6. **Closing vs Complete vs Closed.** Jake Complete is a **stage**. Do not rename status Closed to mean “closing happened, keep working.” [Keep Completed/Closed as terminal history. Stay Active through post-close. Suggest archive when obligations are done. Do not bulk-reopen Closed files.]
7. **TC authority beyond assignment.** Product already gives TCs the agent workspace. Any brokerage restriction? [Assignment remains the grant.]
8. **SMS / voice provider.** [Adapters exist; no fake transcripts.]
9. **Class A list (Audri C / Q3).** [This intelligence plan does not add letters. Q3 remains a parallel execution track.]
10. **Negotiation add-on.** [Stays out. Detect judgment needed, route, optionally teaser the add-on later.]

---

## 16. Suggested engineering order

Dependency order, not a calendar. Each phase should land on staging and stay there before the next one changes send or client behavior.

1. Phase 0 Dual durable restore  
2. Phase 1 facts (everything else writes the wrong type if this is late)  
3. Phase 2 Conductor + ladder (makes later specialists safe)  
4. Phase 3 lifecycle + parties + issues  
5. Phase 4 Trusted Mode + obligation diffs  
6. Phase 5 advisory ranker + strong challenge  
7. Phase 6 communication hypotheses  
8. Phase 7 client Aime + earned updates (after Jake's timing call; I update the testing guidelines when it ships)  
9. Phase 8 brokerage exceptions  
10. Phase 9 preferences travel rules  
11. Phase 10 learning / vendors (claims off until floor exists)  
12. Phase 11 LSE handoff contract  

Hourly-tick reliability, mailbox health, and Needs You recovery stay in parallel and are not superseded.

---

## 17. What “fully implemented” means

Jake’s architecture is fully reflected on staging when:

- Aime is the only assistant for **staff and represented clients**, with specialists hidden.
- Every material fact is typed; a reported inbound date cannot become the file’s closing date without a human or a Trusted grant that still fails closed on ambiguity.
- Every event is ladder-classified; leftover work is Needs You; routine authorized admin is performed; professional judgment is requested, never performed.
- Deal posture and Trusted Mode are two grants. Silence grants neither.
- Dual still matches Audri Q1.
- Multiple decision-makers stay individual.
- Client updates can earn an explicit send grant and lose it when facts change.
- Vendor performance is silent until a sample floor exists, then attributed to the person when known.
- Private chats are not platform training data.
- Closed files still do **not** run the executor; post-close work stays on **Active** until the agent archives. Terminated can emit an LSE payload without silently becoming a listing engine.
- Negotiation and pre-pending remain out.

That is the product Jake specified. The smallest system that does it is still a wrap around the execution cage already on staging, not a new fleet of named AI services.
