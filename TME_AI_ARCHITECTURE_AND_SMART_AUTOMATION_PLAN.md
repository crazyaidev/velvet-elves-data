# Transaction Management Engine — AI Architecture & Smart Automation Plan

**Date:** 2026-08-15  
**Status:** Plan only. This file does not change product code.  
**Audience:** Engineering (Jan) + product alignment with Jake and Audri  
**Primary sources (in this order):**  
1. Live `velvet-elves-backend` and `velvet-elves-frontend` source (this morning)  
2. Jake — `VE_Transaction_Management_Engine_AI_Agent_Architecture.md`  
3. Audri — `SMART_AI_AUTOMATION_A.md` and `EMAIL_GUIDELINE_TASK_ATTACHMENTS_A.md`  
4. Origin questions — `SMART_AI_AUTOMATION_SYSTEM_FOR_JAKE.md` and `EMAIL_GUIDELINE_QUESTIONS_FOR_JAKE.md`  

**Companion plans this document does not replace:**  
- `SMART_AUTOMATION_SYSTEM_PLAN_2026-08-14.md` — send doctrine, Needs You, hourly tick, Class A cage  
- `AGENT_EMAIL_GUIDELINE_AND_TASK_ATTACHMENTS_IMPLEMENTATION_PLAN.md` — email guideline as code  
- `SMART_AUTOMATION_CHROME_TESTING_PLAN_2026-08-14.md` — Chrome proof  

**Outdated reference only (do not treat as current state):** `SYSTEM_DESIGN.md`, `milestones.txt`, `FRONTEND_UI_WORKFLOW_LOGIC.md` (March–April 2026). Use them for vocabulary, not for “what ships today.”

---

## 0. How to read this document

Jake sent a product-level architecture he spent ~1.5 weeks and 400 questions building for the Listing Success Engine, then stripped the listing work so it could apply to the **Transaction Management Engine we are building now**. Audri answered the open automation and email-guideline questions.

This plan does three jobs:

1. **Record Audri’s answers as binding product decisions** (Section 2).  
2. **Map Jake’s architecture onto the code that actually exists** (Sections 3–6).  
3. **Give a concrete build sequence** that improves the smart automation already on staging without rebuilding it as seven LLM agents (Sections 7–12).

Jake’s own interpretation rule is the constraint:

> Produce the smallest technical architecture capable of reliably honoring these product rules. Do not simplify by converting inference into fact, letting learned behavior expand authority, treating silence as consent, or exposing internal reasoning trees.

We will **not** stand up a Conductor microservice, a specialist LLM per domain, or a vector memory of private chats. We will **wrap and extend** the engines that already run.

---

## 1. Thesis

**Transaction management strategy for Velvet Elves**

Velvet Elves is the Transaction Management Engine (TME). It starts when an offer is accepted / a contract is executed and the file is in the product. Aime is the one assistant. The agent (and an authorized TC) remains the professional authority. Aime keeps contractual, administrative, communication, document, and follow-through obligations **visible and moving**.

**What “smart” means after Jake’s architecture, not only after the email plan**

The 2026-08-14 smart-automation plan defined smart as: overnight prep, a named library-letter exception, Needs You as the leftover pile, and a closed recovery loop. That remains the **execution layer**. Jake’s document adds the **intelligence layer** the execution layer is missing:

- A typed, provenance-aware picture of the file (not just open tasks).  
- A response ladder (not every issue becomes a recommendation or an email).  
- Explicit authority and risk gates (not posture alone).  
- Contract facts that stay literal, human-verified before they become obligations, and superseded rather than overwritten.  
- Client-facing Aime that reassures and routes, and never negotiates or interprets law.  
- Learning that may change *how* Aime works, never *what* she is allowed to do.

**One sentence for conference (unchanged, still honest)**

> On Assisted and Autopilot, Velvet Elves may send the named library letters by itself. Every other email is drafted for you to send. Aime prepares the file overnight; Needs You is what still needs a person.

Jake’s architecture is the **north star for the TME phase**. It is not a license to widen unattended send, add legal interpretation, or pull Listing Success Engine work into this phase.

---

## 2. Binding decisions from Audri (2026-08-15)

These answers close the questions in `SMART_AI_AUTOMATION_SYSTEM_FOR_JAKE.md` §6 and `EMAIL_GUIDELINE_QUESTIONS_FOR_JAKE.md`. Where the Google Doc markup is still coming, that item stays blocked.

### 2.1 Decided — implement

| ID | Decision | Effect on product |
| --- | --- | --- |
| **A** | Sign automatic emails as **Aime** (Assistant to {Agent}, brokerage, phone \| email). | Library sends use `DeliveryMode.AIME_AUTO_SEND` and `signature_block()` in `agent_email_policy.py`. Add a **brokerage-wide off switch** that reverts to the agent signature. Reviewed drafts stay in the agent’s voice. Recipients are never told the mail is AI. |
| **B** | **Automate inspection reminders only.** Inspection Negotiated stays human. | Promote tasks **240** and **245** (Inspection Response Reminder) to Class A library send: deadline-only copy, no repair/response/negotiation language (hard block). Tasks **250 / 255 / 257** stay review-gated. Until the playbook row exists, they remain ToBeAutomated drafts. |
| **D** | **Defer** delayed auto-send (countdown + Hold). | Do not build `SMART_AUTOMATION` S7 / old Phase 7. |
| **E** | New workspaces start **Manual**. Autopilot is opt-in. **Add the choice on account creation**, and tell the user they can change it anytime in Settings. | Code default is already Manual (`DEFAULT_TENANT_POSTURE`). Missing: Register / Onboarding UI. Library send stays off on a brand-new production workspace until Assisted/Autopilot is chosen **and** a mailbox is healthy (already `new_tenant_automation_block()`). |
| **F** | Task **235 is new**: seller-side counterpart of task **230** (Inspection Completed). Use cases: **Sell-Fin and Sell-Cash**. | Add template `legacy_task_id=235`. Do not remap 230/240/245. |
| **G** | Add **453** (pick up sign and lockbox) and **455** (MLS to Sold). Agent self-reminders, seller-side, day of closing, no attachments. | New templates. Not Class A. Appear as ordinary tasks / Class B drafts if they ever email. |
| **H** | Rename 460 / 470 to **Request Testimonials**. Write a review request, not a referral request. | Rename by `legacy_task_id`, not display name. Automation must key off ID (already a known footgun). |
| **J** | Keep the **call**, add the **email as a follow-up**. Preference: **email goes out first**, then the user calls. | Tasks 260, 270, 330, 340: hybrid like 130/140, but **email-then-call**, not call-then-email. Do not drop the call. |
| **K** | Engineering chooses sensible **“how to reply”** defaults; Audri will correct. | Fill `completion_method` / reply-instruction per task. Never invent a portal link. |
| **L** | Writing style is **per user** (Agent, TC, TL, Admin — whoever is sending), not per brokerage. | Preference store on `users`, not `tenants`. Jake’s “personal agent learning may follow the agent between organizations” is the same idea. |
| **N** | **Count Automated completions in progress %.** Marketing claim: the bar moves while the user is away. | Today `task_progress.py` **excludes** AI-hidden tasks. Change: completed Automated rows count in numerator **and** denominator. Open Automated rows that are *not* `ai_needs_user` still do **not** turn the deal Critical/Unhealthy (`_user_visible_tasks` in `dashboard.py` stays). |

### 2.2 Decided in Appendix A (email guideline answers)

| Item | Decision |
| --- | --- |
| HOA 110/115/120 and Utility 150/155/160 | **Send both emails**: thank-you to the listing/co-op side **and** deliver the documents to the represented party. Today one task = one email. Split into two sends from one task, or add sibling tasks — product choice in Wave 1. |
| Task **265** (Appraisal Ordered, cash) | Recipient is the **represented client** (buyer and/or seller). Not the loan officer. |
| Tasks **480 / 490** | **Send an email as well** — remind the buyer(s) to file tax exemptions. Recipients: buyer(s) + agent + TC. |
| Co-contacts | Whenever a role is addressed (buyer, seller, co-op agent), **every person with that role** is on the email. One buyer does not speak for two. This is also Jake §4.4. |

### 2.3 Still open — do not guess

| ID | Status | What is blocked |
| --- | --- | --- |
| **C** | Audri wants **additional automatic letters now**; list = “to be provided.” | No seventh (or eighth) Class A letter until the written list arrives. Inspection reminders (B) are the only approved expansion. |
| **I** | Audri will mark up Appendix A in the Google Doc. | Attachment/exclude rules for the 32 tasks without a sheet row. Safe default remains: no rule → attach nothing, except where the task’s own instructions already name files (80, 8, HOA, utilities). |
| **M** | Discuss Autopilot naming on a call. Audri: “Should we use Aime?” | Do not rename Wizard Autopilot / Deal Autopilot / (future) delayed send in this plan. Recommendation for the call is in §6.3. |
| 420 / 430 Closing Disclosure attach? | Unanswered. | Do not attach CD until answered. Lender typically sends it; attaching the wrong CD is worse than none. |
| Additional Class A list | Not received. | Promotion pipeline (S6) stays closed except 240/245. |

### 2.4 How Audri’s answers sit on Jake’s architecture

They are compatible if we keep one distinction Jake insists on:

- **Explicit grant** (a named letter, a posture, a signature mode) may expand what Aime *does*.  
- **Learned preference** (style, cadence, no-edit client updates) may only change *how* she does authorized work.

Signing as Aime, counting AI work on the progress bar, email-then-call, and per-user voice are grants or presentation. They do not let Aime waive contingencies, move dates, or negotiate inspection.

---

## 3. Jake’s architecture — what we are adopting

Jake’s document is a **product-level developer handoff**, provider-agnostic, TME-only. Listing, buyer search, showings, and pre-offer work are out of scope. Failed-transaction handoff *back* to a Listing Success Engine is specified but **deferred** until that engine exists.

### 3.1 Operating principles we will treat as law

| # | Principle | Product consequence |
| --- | --- | --- |
| 1 | One continuous assistant: **Aime** | Users never meet “contract bot,” “deadline bot,” or “email AI.” Internal specialists stay hidden. |
| 2 | AI is an advisor, never the authority | Agent (and authorized TC) decide. Clients keep their own decisions. Aime does not make legal, fiduciary, negotiation, or client decisions. |
| 3 | If Aime can do it, she should | Routine administrative work, when authorized, is performed — not dumped as a task list. This is the doctrine behind library letters and auto-apply. |
| 4 | No material assumptions as facts | Hypotheses are questions. They are not written onto the file until confirmed. |
| 5 | Provenance matters | Every material fact has source, time, observed vs reported vs inferred, and whether a newer source supersedes it. |
| 6 | Authority must be explicit | Repeated behavior is not permission. Past approval is not permanent. Learned preferences cannot enlarge the action set. |

### 3.2 The stack Jake specified

```text
Aime (single user-facing assistant)
  → Conductor (context, risk, authority, routing, approval, execution gating)
      → Transaction Intelligence (descriptive / diagnostic state)
      → Contract & Document Intelligence (literal extraction only)
      → Advisory Intelligence (what deserves attention)
      → Client Interaction Intelligence (buyer/seller-facing behavior)
  → Memory & Provenance | Learning & Pattern | Product Intelligence
```

Specialists **reason**. They do not execute. The Conductor gates execution. Memory types truth. Learning improves future intelligence. The agent and client retain decision authority.

### 3.3 Lifecycle Jake wants (conceptual, overlapping, not linear)

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

Closing does **not** end the TME. Complete is when managed post-closing obligations are resolved or intentionally closed.

### 3.4 Autonomy Jake wants (deadline / obligation activation)

| Jake mode | Contract-derived deadlines |
| --- | --- |
| **Manual** | Extract and propose. Human verifies before the obligation is authoritative. |
| **Assisted** | Prepare automatically. Authoritative deadlines still need verification unless a narrower grant exists. |
| **Trusted** | May auto-activate **high-confidence, explicit, non-conflicting** contract obligations when the user has granted it. Ambiguity always returns to a human. |

This is **not the same axis** as deal posture (who may send mail). See §6.2.

### 3.5 Contextual risk (four categories)

1. **Routine / Operational** — organize, remind, collect, status. Eligible to Perform.  
2. **Relationship / Service** — client anxiety, missed commitments. Inform / Recommend, careful client wording.  
3. **Professional Judgment** — extensions, waives, inspection strategy, financing strategy. Request decision. Never Perform.  
4. **Authority / Transaction** — client approval, multi-party consensus, execution, privacy, compliance. Request decision, Refuse, or Escalate.

Risk is contextual, not the action name.

### 3.6 Intelligence response ladder

A detected condition may result in: no action → internal watch → early awareness → **perform** → inform → clarify → recommend → request decision → strong challenge → refuse → escalate.

Not every issue is a recommendation. Not every recommendation is an email. A known obligation may outrank an AI suggestion. Aime may not silently choose which explicit commitment to break.

### 3.7 Hard boundaries we will not cross in TME

- Literal contract language only. No “legally, this means you can terminate.”  
- Negotiation intelligence is a **future paid add-on**. Core TME may detect that judgment is needed and route to the agent.  
- Multiple decision-makers stay individual. One buyer does not speak for all.  
- Silence is not consent. No-edit client updates may *suggest* automation; they do not grant it.  
- Vendor performance claims need a verifiable sample, attributed to the person when evidence supports it.  
- Private conversation content does not become platform learning. Structured signals (deadline met/missed, recommendation accepted/rejected) may.  
- Clients are never the recipient of internal brokerage-risk escalation.  
- Aime may refuse prohibited execution. She may not refuse because she disagrees with the agent’s professional judgment.

---

## 4. What the product actually is today (code, 2026-08-15)

Nine (now more) engines, unified at the UI by posture + Needs You. This is the execution layer. It is **not** Jake’s intelligence stack yet.

### 4.1 Engines that exist and must be reused

| Engine | Where | What it does | Sends to a party? |
| --- | --- | --- | --- |
| Wizard Autopilot | `NewTransactionWizard.tsx` | Fast intake when parse confidence is high | No |
| Deterministic plan | `task_generation_service.py`, `timeline_planner.py`, `requirement_planner.py` | Tasks, dates, checklist from confirmed anchors | No |
| Packet parse | `document_packet_parsing.py`, `intake_intelligence.py` | OCR + extraction; per-field source strings | No |
| Agent workspace | `transaction_agent.py`, `AgentPane.tsx` | Chat + typed proposals; auto-apply on Assisted/Autopilot | Drafts only |
| Graduated autonomy | `agent_policy.py`, `agent_rules.py` | Hard-coded `AUTO_ELIGIBLE` / `FORBIDDEN` | No |
| Posture | `automation_posture_service.py` | Manual / Assisted / Autopilot; deal override or inherit | Gates library send |
| AI task executor | `ai_task_executor.py` | Named `_EMAIL_PLAYBOOK` + Review Documentation | **Yes**, Assisted/Autopilot |
| Deal runtime | `deal_runtime.py` | Skip send if the letter already left, or title already ordered | Prevents duplicate |
| Auto-draft sweep | `create_auto_drafts` | One draft per (task, due_date); Autopilot marks Ready | No (Send tap) |
| Inbound | `inbound_triage.py`, `inbound_dispatch.py`, `ai_email_engine.py` | File + classify + draft; money not drafted | No |
| Email policy | `agent_email_policy.py` | Categories, delivery modes, mandatory-review topics, Aime signature **helper** (not yet used on live sends) | Gates |
| Guarded send | `ai_email_delivery.send_ai_draft` | Attachment honesty, `strip_ai_disclaimer`, user’s mailbox | Yes when called |
| Hourly tick | `internal_schedules.py` + EventBridge | Escalations, digests, drafts, executor, Gmail watches | Yes via executor |
| Needs You | `needs_you_composer.py`, `NeedsYouPage.tsx` | Residual queue | Send is still a tap |
| Issue detectors | `agent_issues.py` | Deterministic blockers/warnings/watch — no LLM | No |
| Suggestions | `suggestion_engine.py` | Deterministic cards (risk/task/comms/relationship) | No |
| Mailbox census | `mailbox_census.py` | Healthy Gmail/Outlook/iCloud per tenant | No |

### 4.2 Class A library letters (closed set in `_EMAIL_PLAYBOOK`)

Buyer welcome, Seller welcome, Co-op agent welcome, Loan officer welcome, Order Title, Confirm Title Order, Pending reminder (to the account holder). Review Documentation completes or drafts a signature chase — that chase does not send.

Guards already in code: Active deals only; captured Contacts emails only; connected mailbox; Manual kills send; >30 days overdue surfaces; duplicate send skipped; Confirm Title Order skipped if Order Title is done; no AI disclosure on the wire; attachment prose must match files.

### 4.3 What the UI currently calls the assistant

| Surface | Identity today | Jake requirement |
| --- | --- | --- |
| Deal `AgentPane` | **“Velvet Elves AI”** / “Your deal assistant” | Aime |
| Active Transactions `AIChatPanel` | Generic AI chat | Aime |
| Attorney chat | Separate attorney assistant | Aime (same person, different authority) |
| Client portal `ClientAskThread` | **Human team thread** — “Your agent will see it” | Client-facing Aime with hard boundaries |
| Automatic emails | Signed **as the agent** (`_owner_signature`) | Sign as Aime (Audri A) |
| Settings copy | “library welcome and title-order letters” | Keep; add Aime name where the assistant is the actor |

Internal specialist names must never appear in these surfaces.

### 4.4 Transaction state today vs Jake’s lifecycle

**Status enum** (`TransactionStatus`): Active, Incomplete, Paused, Completed, Closed. There is **no Terminated / Failed**.

**Stage pill** (`compute_stage_pill`): a **health** label — Pending, Critical, Unhealthy, Needs Attention, In Inspection, On Track. It is not a lifecycle stage. “In Inspection” is the only stage-like pill, and it is a health override.

**Milestone bar**: Contract, EM Delivered, Inspection Response, Appraisal Expected, CD Delivered, Cleared to Close, Closing, Possession. This is the closest lifecycle the product has, and it is date-based, not overlapping-stage-based.

**Progress** (`task_progress.py`): AI-hidden Automated tasks are excluded so the human bar stays “honest.” Audri N reverses the *completed* side of that choice.

### 4.5 Parties today vs Jake’s party model

`SUPPORTED_PARTY_ROLES`: buyer, seller, listing_agent, buyers_agent, loan_officer, title_rep, title_company, closing_attorney, settlement_attorney, inspector, appraiser, home_warranty, other.

Missing as first-class roles: processor, underwriter, escrow, HOA / management, broker / manager, TC-as-party, home-warranty *contact vs company*, decision-maker flag, “required for this action” authority.

Co-op agent is a **pseudo-role** resolved side-aware in the executor, not a stored `party_role`. Multiple people with the same role exist as multiple `transaction_parties` rows; Audri’s “include all co-contacts” is not consistently enforced on send.

There is **no** per-person approval ledger (who signed, who agreed, whether unanimity is required).

### 4.6 Contract intelligence today

Packet parse extracts parties, price, earnest money, dates, contingencies, etc., with per-field source/confidence. The wizard is the human verification gate **at intake**. After that:

- Amendments / addenda / extensions are documents, not a **controlling-state** overlay.  
- Extracted values can be edited on the file; there is no typed fact (`verified` vs `inferred` vs `hypothesis`).  
- The LLM is forbidden from computing deadlines (`timeline_planner` is deterministic). That already matches Jake’s “the model does not invent dates.”  
- Literal-vs-legal boundary is **prompted** in chat, not enforced as a specialist output type.

### 4.7 Authority and risk today

`agent_policy.py` uses **low / medium / high** on action types, plus a hard `FORBIDDEN` set (legal determination, packet release, disbursement exception, send_email, auto_send_email, delete_document, merge, schedule_send). Auto-eligible types are code, not tenant config.

This is a **capability** gate. Jake’s model is a **contextual** gate (same “send a reminder” is Routine in one file and Relationship-risk in another). We need both: capability remains the floor; context becomes the Conductor.

### 4.8 Client-facing intelligence today

Represented clients get a concierge workspace (overview, milestones, documents, ask-the-team). They do **not** talk to Aime. FSBO gets plain-English next-step copy with a “we are not your agent / not legal advice” boundary. That boundary stays.

### 4.9 Learning today

Almost none of Jake’s layered learning exists. We have: audit logs, AI usage events, suggestion dismissals, some analytics. We do **not** have typed learning signals, vendor-person performance, recommendation accepted/rejected as a first-class event, or product-intelligence (where Aime creates noise).

---

## 5. Gap analysis — Jake vs code vs Audri

### 5.1 Already aligned (do not rebuild)

| Jake rule | Evidence in code |
| --- | --- |
| Dates never auto-change | `apply_date_cascade` requires a fresh preview; not auto-eligible |
| Waives / legal / packet release stay human | `FORBIDDEN_ACTION_TYPES`; attorney packet release is a human endpoint |
| Unattended send is a named exception, not an agent action | Executor → `send_ai_draft`; agent cannot `send_email` |
| Recipients from captured parties | Executor + delivery path |
| No AI disclosure to recipients | `strip_ai_disclaimer` |
| Manual is a real kill-switch | `playbook_sends_allowed` |
| Ambiguous / unknown Automated names surface, never guessed | Unknown playbook → `ai_needs_user` |
| Agent and TC share the deal workspace | `_WORKSPACE_ROLES` includes Agent, TC, Team Lead, Admin |
| Hypotheses in inbound (“file looks ahead”) are not recorded as facts | Inbound drafts; money held; statements kept without inventing history |
| Provider-agnostic | `ai_settings` / provider factory |

### 5.2 Missing — intelligence (Jake), not more mail

| Jake capability | Today | Plan wave |
| --- | --- | --- |
| One Aime identity | Split names, agent-signed auto mail | **W0** |
| Conductor (risk + authority + ladder + execution gate) | Independent engines, posture only | **W2** |
| Typed Memory & Provenance | Parse sources at intake; no fact table | **W2** |
| Lifecycle stages (overlapping) | Health pills + milestone dates | **W2** |
| Terminated / Failed status | Not in enum | **W2** |
| Contract supersession (amendment controls) | Documents exist; controlling state does not | **W3** |
| Human verify of *post-intake* contract-derived obligations | Wizard confirms once | **W3** |
| Response ladder as code | Needs You kinds + suggestion priority | **W2** |
| Portfolio next-best-action with evidence/confidence/what-changed | Suggestions + urgency sort | **W3** |
| Strong challenge only with new evidence | Not built | **W3** |
| Client-facing Aime | Human Ask thread | **W4** |
| Multi-party decision ledger | Parties have no authority flags | **W3** |
| Communication-gap → clarify, not invented history | Partial (inbound) | **W3** |
| Vendor/person performance with sample floor | Not built | **W5** (post-conference) |
| Governed cross-transaction learning | Not built | **W5** |
| Product intelligence (Aime noise, ignored workflows) | Analytics only | **W5** |
| Earned client-update automation | Not built | **W4** |
| LSE ↔ TME handoff | LSE does not exist | **Deferred** |
| Negotiation add-on | Out of TME core | **Deferred / paid** |

### 5.3 Missing — execution (Audri), on the current stack

These do not wait for the Conductor.

| Item | Code today | Work |
| --- | --- | --- |
| Aime signature on Class A | Helper exists; send path uses `_owner_signature` | Wire `signature_block(AIME_AUTO_SEND)` in executor + delivery; tenant off switch |
| Inspection reminder Class A | 240/245 are `ToBeAutomated` | Playbook rows, locked template, repair-language block |
| Task 235 | No `legacy_task_id=235` | Seed template, Sell-Fin / Sell-Cash, sibling of 230 |
| Tasks 453, 455 | Do not exist | Seed, seller-side, closing-day, agent target |
| 460/470 rename | “Request Referrals” | Rename + copy |
| 260/270/330/340 hybrid | Phone-only | Email follow-up first, call remains on the task |
| Dual HOA/utility emails | One email per task | Two sends |
| Task 265 recipient | Unset | Represented client |
| 480/490 tax-exemption email | Card reminder | Email to buyers + agent + TC |
| All co-contacts on send | First matching party often wins | Recipient expansion by role |
| Progress includes AI completions | `is_ai_hidden` drops them | Count completed Automated; keep overdue filter |
| Posture on account creation | Register has no posture; onboarding has no automation step | Add to Register (founders) + Onboarding (admins) |
| Reply-how-to defaults | Empty | Fill per K |
| Per-user style | Not stored | User settings |

### 5.4 Tensions to resolve on the Jake call (do not code around them)

1. **Naming.** Product: Manual / Assisted / Autopilot (deal) + Wizard Autopilot (intake). Jake: Manual / Assisted / **Trusted**. Audri asked whether the third level should be branded Aime. Recommendation in §6.3.  
2. **Class A growth.** Audri wants more automatic letters now; Jake’s earned-automation and Jan’s closed list both say grow one named letter at a time with a written yes. Inspection reminders are the one yes we have.  
3. **Progress bar.** Audri wants AI work visible (marketing). Jake wants the agent to see that Aime is working, without pretending human obligations are done. The split in §2.1 N is the resolution: **progress counts AI completions; health pills do not treat unblocked AI work as the user’s overdue.**  
4. **Client Aime.** Jake wants buyers/sellers talking to Aime now. The client portal is a human thread. Shipping client Aime before Conductor + Client Interaction policy would violate Jake §4.3 (legal advice, manufactured consensus). Sequence: policy first, then a bounded client Aime (status, next steps, route professional questions).

---

## 6. Target architecture — smallest system that honors Jake

### 6.1 Layers mapped onto existing modules

```text
┌─────────────────────────────────────────────────────────────┐
│  AIME  (one identity across AgentPane, dashboard chat,      │
│         attorney chat, outbound Class A, later client)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  CONDUCTOR  app/services/aime_conductor.py  (new, thin)     │
│  Assemble context → type facts → score risk → pick ladder   │
│  → call one existing engine or stop                         │
└──────────────────────────────┬──────────────────────────────┘
          ┌────────────┬───────┴────────┬────────────┐
          ▼            ▼                ▼            ▼
   Transaction     Contract &      Advisory     Client
   Intelligence    Document        Intelligence Interaction
   agent_issues    packet_parse    suggestion_  (new policy
   deal_runtime    + fact store    engine +     module;
   plan + stages   + supersession  agent_issues  portal later)
          └────────────┴───────┬────────┴────────────┘
                               ▼
              Memory & Provenance (transaction_facts)
              Learning signals (structured, opt-in)
              Product intelligence (admin, not client-facing)
                               ▼
              EXECUTION (unchanged cage)
              playbook send | draft | Needs You | refuse
```

**Rules for this mapping**

- A specialist returns a **finding** `{fact_or_issue, evidence, provenance, confidence, missing, contradictions, hypothesis?}`. It never sends mail or completes a task.  
- The Conductor is **deterministic Python** plus optional LLM *wording*. It does not “vote.” Unresolved disagreement lowers confidence or becomes Clarify.  
- Execution still goes through `send_ai_draft`, `agent_actions.py`, and Needs You. The Conductor may not grow `AUTO_ELIGIBLE` or `_EMAIL_PLAYBOOK`.  
- Internal names (Conductor, Transaction Intelligence, …) never appear in UI copy.

### 6.2 Two independent axes (do not collapse them)

| Axis | Values | Owns |
| --- | --- | --- |
| **Deal posture** (exists) | Manual / Assisted / Autopilot | Whether routine *actions* auto-apply, whether Class A *mail* may send, whether drafts arrive Ready |
| **Obligation autonomy** (Jake, new) | Manual / Assisted / Trusted | Whether a contract-derived deadline becomes an **authoritative task** without a human tick |

Today the wizard is the one-time Trusted-or-not gate: the human confirms extracted dates, then the plan engine materializes tasks. After intake, amendments currently **do not** re-open that gate. Wave 3 adds: new controlling document → proposed obligation → posture/autonomy decides if it auto-activates.

Until obligation autonomy is a separate setting, **map it to deal posture**:

| Deal posture | Obligation autonomy (interim) |
| --- | --- |
| Manual | Manual — propose only |
| Assisted | Assisted — prepare, human confirms new contract-derived dates |
| Autopilot | Trusted **only** when language is explicit, complete, non-conflicting, no amendment ambiguity |

Ambiguity always increases human involvement, regardless of posture (Jake §8.2 Hard Boundary).

### 6.3 Naming recommendation for the Jake/Audri call (Question M)

Do not rename in code until the call. Proposed product language:

| Today | Proposed (if they want Aime in the name) | Jake equivalent |
| --- | --- | --- |
| Manual | **Aime off** (you click) | Manual |
| Assisted | **Aime assists** | Assisted |
| Autopilot (deal) | **Aime trusted** | Trusted |
| Wizard Autopilot | **Fast intake** (not a send setting) | n/a |

If they prefer to keep Autopilot, keep it — but **never** use it for a third meaning (delayed auto-send is deferred anyway).

### 6.4 Fact types (Memory & Provenance — new table)

Material intelligence is typed. An inference never silently becomes a transaction column.

| Type | May drive Class A / dates? | Example |
| --- | --- | --- |
| `verified_fact` | Yes | Closing date confirmed in wizard |
| `reported_fact` | No, until verified | Lender emailed “appraisal Tuesday” |
| `decision` | Context | Agent chose not to request an extension |
| `commitment` | Yes, as obligation | Agent told buyer “I’ll send the HOA packet today” |
| `inference` | No | “Buyer concern may be increasing” |
| `hypothesis` | No — ask | “Did the lender waive appraisal?” |
| `preference` | Shapes wording only | Short client updates |
| `pattern` | Recommend only after sample floor | “This LO is slower to CTC” |
| `recommendation` | Needs You / Advisory | “Follow up with title” |
| `authority` | Gates execution | “Both buyers must sign” |
| `obligation` | Task engine | Inspection response due date |

Storage sketch (implementation in W2, not a migration in this file): `transaction_facts` with `type`, `key`, `value`, `source`, `source_at`, `superseded_by`, `confidence`, `privacy_scope`. Existing transaction columns remain the **verified** projection the rest of the app already reads.

### 6.5 Response ladder as code (Conductor output)

Reuse Needs You rather than a new queue. Map ladder rungs to existing surfaces:

| Ladder | Product |
| --- | --- |
| No action / Watch | Activity log only; optional `watch` fact |
| Early awareness | AgentPane suggestion, low priority |
| Perform | Executor / auto-apply (Routine + authorized) |
| Inform | Automation activity + optional digest |
| Clarify | Needs You + Aime question in AgentPane |
| Recommend | Suggestion / proposed `agent_action` |
| Request decision | Proposed action, not auto-eligible |
| Strong challenge | Same, with “what changed” evidence block |
| Refuse | Chat refusal + audit; no action row that looks approvable |
| Escalate | Team Lead / Admin notification; **never** the client |

### 6.6 Risk × posture → allowed rungs

| Risk \ Posture | Manual | Assisted | Autopilot / Trusted |
| --- | --- | --- | --- |
| Routine | Recommend / Inform | Perform (library + auto-apply) | Perform |
| Relationship | Inform | Recommend; Aime drafts, human sends | Same; no silent client send |
| Professional judgment | Request decision | Request decision | Request decision (never Perform) |
| Authority / Transaction | Request / Refuse | Request / Refuse / Escalate | Same |

This is how Jake’s “If Aime can do it, she should” and “never collapse professional judgment into automation” coexist with Audri’s library letters.

---

## 7. Transaction management strategy (TME)

This is the operational strategy for the current phase — not Listing Success, not a rewrite of the task engine.

### 7.1 When TME starts and ends

**Starts:** offer accepted / contract executed, file created in Velvet Elves (wizard intake or later LSE handoff). Buyer-side pre-pending is out of scope.

**Does not end at closing.** Post-closing tasks (possession, sign/lockbox, MLS Sold, tax exemptions, testimonials, thank-yous) stay on the file. **Complete** is a new terminal state meaning “no managed obligation left,” distinct from **Closed** (closing event occurred). **Terminated / Failed** is a new status for dead deals; if/when LSE exists, context hands off. Until then, Aime offers nothing that looks like listing marketing.

### 7.2 Representation and dual agency

Keep the six use cases (`Buy-Fin`, `Buy-Cash`, `Sell-Fin`, `Sell-Cash`, `Both-Fin`, `Both-Cash`). Dual agency (`Both-*`) is a first-class Transaction Intelligence flag: two represented sides, two decision groups, no “the client said yes” without saying which client.

### 7.3 Who Aime works for on a file

| User | Aime may | Aime may not |
| --- | --- | --- |
| Transaction agent | Full TME intelligence, Perform within posture | Legal interpretation, negotiation, client decisions |
| TC (assigned) | Same operational access as the agent on that file | Authority the brokerage did not grant |
| Team Lead / Admin | Oversight, posture, escalation | Quietly override agent professional calls without an audit trail |
| Buyer / seller (later) | Status, next steps, reminders, capture questions | Legal advice, negotiation, speaking for co-clients, seeing internal escalation |
| Attorney | Matter workspace; packet holds | Delegating legal judgment to Aime |
| Vendor | Their uploads and assigned requests | The full file |

### 7.4 How work moves on a file (the TME loop)

This is Jake §33, implemented with current triggers:

1. Event enters: wizard confirm, document upload/parse, inbound email, task due, hourly tick, user chat, party edit, mailbox reconnect.  
2. Conductor identifies transaction, user, posture, authority, risk, relevant facts.  
3. Only needed specialists run (today: `agent_issues` + `deal_runtime` + parse; later: fact store + advisory).  
4. Ladder classification.  
5. Authority / approval check (posture + `agent_policy` + email policy gates).  
6. Aime performs, drafts, asks, or stops in Needs You.  
7. Memory records the typed result.  
8. Eligible structured learning signals fire (W5).

Overnight: the hourly tick is this loop over Active deals. Morning Queue remains: library letters that policy allows may have gone; everything else is Needs You.

### 7.5 Contract-derived obligations

**Default (already true at intake):** parse → wizard confirm → plan engine. The human does not re-type dates; they verify.

**After intake (new):** a later executed amendment is a *candidate* change. Aime prepares the diff (“inspection response moves from X to Y because Addendum 2 says …”). Manual/Assisted: Needs You confirm. Autopilot/Trusted: auto-activate only if literal, complete, no conflict. Otherwise confirm.

**Never:** the model computes a deadline; Aime treats a hypothesis as the new date; Aime waives a contingency because a party “seems fine with it.”

### 7.6 Communication strategy (ties to email guideline)

Three outbound classes remain (`SMART_AUTOMATION` §6):

- **A. Library send** — named templates, Aime-signed after Audri A, Assisted/Autopilot.  
- **B. Prepared drafts** — everything else, including inbound replies and inspection negotiated.  
- **C. Delayed auto-send** — not built (Audri D).

Inbound: file to the deal, keep statements, hold money, draft factual answers, never Ready-mark inspection negotiation.

Client updates: Aime drafts, agent/TC sends (Jake §16). Earned automation is W4 and requires an explicit grant.

### 7.7 Portfolio strategy

Needs You is the cross-file leftover pile (already). Advisory Intelligence ranks the agent’s book by deadline proximity, contractual consequence, client-service risk, and missing information — **one clear next action**, not a second inbox. A known obligation outranks a suggestion. Implement as an ordering of existing Needs You + suggestion rows, not a new product surface, until conference is past.

---

## 8. Build sequence

Phases are independently shippable. **W0–W1 are conference path** (lock ~2026-09-12, conference ~2026-09-22). W2+ may start in parallel as modules but must not destabilize Class A send.

Reuse Chrome cases from `SMART_AUTOMATION_CHROME_TESTING_PLAN_2026-08-14.md`. New cases are listed per wave.

---

### W0 — Aime identity, Audri grants, progress honesty  
**Goal:** The assistant has one name. Automatic letters match the guideline. The progress bar shows that Aime worked. New accounts choose posture. No new unattended letter except inspection *reminders*.

**Backend**

1. **Aime signature on Class A.** Executor and `send_ai_draft` use `signature_block(DeliveryMode.AIME_AUTO_SEND, agent, topic, address)` when the send is a library letter. Reviewed drafts stay `AGENT_REVIEWED_DRAFT`. Persist `delivery_mode` on the log (column already exists in tests).  
2. **Off switch.** `tenants.settings_json.automation.aime_signature_enabled` default **true** once shipped (Audri chose Aime). False restores `_owner_signature`.  
3. **Disclosure cage.** Block outbound bodies containing `AI`, `artificial intelligence`, `bot`, `automated`, `Velvet Elves` as identity claims (pending-reminder to the *agent* may still name the product — that letter is not client-facing).  
4. **Progress.** `compute_task_progress`: include completed Automated tasks in total/completed. Keep `user_visible_tasks` for overdue/Critical so an unsent welcome does not paint the deal red. Header copy: “12 of 40 complete” may now include Aime’s 7.  
5. **Recipient expansion.** Library send and task emails include **all** parties for the target role (Audri co-contacts + Jake §4.4).  
6. **Register / onboarding posture.** Founder register and Admin onboarding: Manual (default) / Assisted / Autopilot. Copy: change anytime in Settings → AI & Automation. Selecting Assisted/Autopilot does **not** turn library send on until a mailbox is healthy (existing S8 cage).

**Frontend**

1. Rename AgentPane header from “Velvet Elves AI” to **Aime** / “Assistant to this file.” Same for dashboard chat chrome. Do not expose specialist names.  
2. AI & Automation: Aime signature toggle; posture-on-signup copy; Always-true line still names library letters.  
3. Progress chip / Overview: when Automated completions are in the bar, a short “Aime completed N today” using existing `handled_today` — do not invent a second percentage.  
4. RegisterPage + OnboardingWizard: posture cards matching `AutomationPostureSection` (same three, same captions).

**Tasks / templates**

5. Seed **235** Inspection Completed (seller), Sell-Fin / Sell-Cash, parallel copy to 230, target Seller / Agent / TC.  
6. Seed **453**, **455** as specified.  
7. Rename 460/470 → Request Testimonials; rewrite instructions to a review ask.  
8. Tasks 260, 270, 330, 340: keep phone method; add `auto_draft_email` follow-up (email first).  
9. Task 265: recipient = represented client.  
10. 480/490: outbound email to buyers + agent + TC (tax exemptions). Not Class A.

**Inspection reminders (Audri B) — the only Class A expansion**

11. Add playbook keys for 240 and 245. Locked template: “The inspection response deadline is {date}.” **Send abort** if body matches repair/response/negotiation `MandatoryReviewTopic`. Feature flag per template, on for staging, off for production until a 48h soak.

**Acceptance**

- A library welcome on Autopilot is signed Aime / Assistant to {Agent} / brokerage / phone | email.  
- Toggle off → same letter signed as the agent.  
- Completing a welcome via executor moves the workspace progress percent.  
- A deal with only an unblocked overdue welcome is **not** Critical.  
- New register flow offers Manual/Assisted/Autopilot; skipping leaves Manual.  
- 240/245 may send on Assisted when the deadline copy is clean; a body containing “repair demand” cannot.  
- Chrome: W0 cases in the existing testing plan plus Aime signature and progress.

**Does not include:** extra Class A letters from Question C; Appendix A markup; delayed send; client Aime; Conductor module.

---

### W1 — Email guideline completion (still execution layer)

**Goal:** Attachment rules, dual HOA/utility sends, reply-how-to defaults, per-user style. Unblocks later promotions.

**Depends on:** Appendix A markup (Question I) for the 32-row list. Until it arrives, implement only rows whose **task text already names attachments** (8, 80, 110–120, 150–160, 170) and Audri’s explicit Appendix answers (both emails; 265; 480/490).

**Backend**

1. Dual-send for HOA/utility: thank-you + delivery, same task completion when both exist or both are blocked for the same honest reason.  
2. Reply-instruction defaults (K) stored on templates; compose uses them verbatim.  
3. `users.settings_json.writing_style` (preferred phrases, prohibited phrases). Applied at compose; never overrides facts or safety.  
4. Continue document-kind attach/exclude (already rebuilt vs filename keywords). Apply sheet rules as markup arrives.

**Acceptance**

- HOA delivery to a buyer-side file produces two emails or two blocked Needs You rows with distinct reasons.  
- A prohibited phrase in user style never appears in a draft.  
- Send remains blocked on `**[MISSING: …]**` / `**[CONFLICT: …]**`.

---

### W2 — Conductor + Memory + lifecycle (intelligence foundation)

**Goal:** One routing function and a typed fact store. No new mail. Specialists remain hidden.

**Backend**

1. `app/services/aime_conductor.py`  
   - Input: event type + transaction id + actor.  
   - Loads plan, parties, facts, posture, mailbox, open Needs You.  
   - Outputs a ladder decision + which existing function to call (`run_automated_tasks_for_deal`, `create_auto_drafts` for one deal, `detect_issues`, propose action, or noop).  
   - Hourly tick **per deal** goes through this instead of blasting executor + sweep with no shared picture (this is also `SMART_AUTOMATION` S3b, now with a Jake-shaped name).  
2. `transaction_facts` table + repository. Backfill verified facts from current transaction columns (closing date, EM, inspection dates, parties). Parse results write `reported_fact` until wizard/user confirms → `verified_fact`.  
3. Lifecycle **overlay** `tme_stages: string[]` on the transaction (overlapping). Derived deterministically from dates + task families + facts. Status enum adds `Terminated`. Closed ≠ Complete.  
4. Stage pill stays health. Workspace header may show **one** lifecycle label (“Inspection · Financing”) beside health — not a second pill color system.  
5. Refusal path in AgentPane: capability + authority messages, never “I disagree with your judgment.”  
6. Diagnostic payload for Admin/support only (auditable): specialist findings, not chain-of-thought.

**Frontend**

- Aime never says “Conductor” or “Transaction Intelligence.”  
- Optional lifecycle line on the workspace header.  
- Terminated as a status in deal filters.

**Acceptance**

- A second tick does not send a second welcome (already `deal_runtime`; Conductor must keep that).  
- A reported inbound fact (“appraisal Tuesday”) does not change `appraisal_date` until confirmed. Aime may ask.  
- Terminated deals: no Class A, no sweep.  
- AgentPane refusal of “tell them they can terminate” cites the legal boundary, offers to draft a *question for the agent*, does not send.

**Closes Jake §6, §7, §14, §28 (partial), §33, §35 items 1–4, 8, 24.**

---

### W3 — Specialists that change file quality

**Goal:** Contract supersession, obligation verification, advisory quality, multi-party authority.

**Contract & Document Intelligence**

1. Controlling-document pointer: latest executed amendment/addendum/extension vs original. Historical state preserved.  
2. Candidate obligation diffs → Needs You “Verify deadline” (Assisted) or auto-activate under Trusted rules (W2 mapping).  
3. Literal extraction only; interpretation requests route to Request decision.  
4. Conflicts (`**[CONFLICT: …]**`) already block send; they must also block Trusted activation.

**Transaction Intelligence**

5. Canonical stage + contingency/EM/inspection/financing/appraisal/title/possession flags as facts, not only tasks.  
6. Issue detectors in `agent_issues.py` emit ladder hints (watch vs clarify vs recommend) instead of a flat warning list.

**Advisory**

7. Recommendation object: `{recommendation, why, confidence, evidence, what_changed}`.  
8. Strong challenge only when a **new verified fact** contradicts a recorded `decision`. Reaffirmation raises the threshold. Time passing is not new evidence.  
9. Portfolio sort: Needs You + suggestions ranked by Jake §15 factors. One “do this next” on Active Transactions.

**Authority**

10. Party flags: `is_decision_maker`, `must_sign`. Actions that imply consent check the set. Aime will not send “the buyers agreed” unless all required parties are on the evidence.

**Acceptance**

- Uploading “Addendum 2” that moves closing does not silently rewrite `closing_date`.  
- Dual-buyer file: welcome goes to both emails; Aime will not treat one reply as both.  
- Chrome: verify-deadline Needs You on Assisted after an amendment parse.

**Closes Jake §5.3–5.5, §8, §12, §15, §23, §35 items 5–7, 12, 15.**

---

### W4 — Client Interaction Intelligence (bounded client Aime)

**Goal:** Buyers and sellers can ask Aime for status and next steps without getting legal advice or internal risk workflow.

**Only after W2.** Client Aime is a **policy filter** over Transaction Intelligence, not the AgentPane with a different CSS theme.

**Allows:** known status, known next steps in plain language, known milestones, process glossary, capture a question for the agent, reminders the agent already authorized.

**Refuses:** legal interpretation, negotiation, “your co-buyer said yes,” manufacturing consensus, internal Needs You, brokerage escalation, wire/banking.

**Client updates:** Aime drafts; agent/TC approves. After N no-edit sends, Aime *asks* to automate that template. Silence ≠ yes.

**Acceptance**

- Client asks “can I back out?” → Aime routes to the agent, does not interpret the contingency.  
- Client Ask thread can be Aime or the team; labels are honest.  
- No internal issue titles leak (`document_type_mismatch`, playbook codes).

**Closes Jake §5.6, §16, §17, §32, §35 items 11, 17, 26.**

---

### W5 — Learning, vendors, product intelligence (post-conference)

**Goal:** Structured signals only. No private chat promotion.

**Signals (examples):** deadline met/missed, recommendation accepted/rejected, agent correction, vendor response time, CTC timing, document error, follow-up required, party responsiveness, closing outcome.

**Rules:** explicit correction > explicit response > repeated behavior > single observation > inferred motive. Correlation ≠ causation. Stale learning weakens. Agent preferences travel with the user; client data, transaction history, and autonomy grants do **not** follow a brokerage move.

**Vendor intelligence:** person-level when the identity is known; company-level otherwise. No performance claim below a documented sample floor (number TBD with Jake; until then, Aime may not say “this lender is slow”). Explain evidence, never labels (“bad lender”).

**Product intelligence:** admin-only — where files stall, where Aime is overridden, unused workflows, noisy recommendations. Not used in client-facing reasoning.

**Closes Jake §6.2–6.3, §18–21, §35 items 19–22.**

---

### Deferred — not this phase

| Item | Why |
| --- | --- |
| Listing Success Engine behavior | Jake §2.2 / §35.30 |
| LSE ↔ TME handoff | No LSE product |
| Negotiation add-on | Jake §10; paid; inspection strategy stays human |
| Delayed auto-send (S7) | Audri D |
| Bulk ToBeAutomated → Class A | Audri C list not provided; Jake earned-automation |
| Vector memory of conversations | Violates privacy + “inference ≠ fact” |
| Per-specialist unrestricted memory | Jake §37 |
| Exact confidence / vendor-sample / escalation formulas | Jake §36 deferred on purpose |
| Client as escalation target | Forbidden |

---

## 9. Class A promotion pipeline (after the written list)

Audri C wants more automatic letters. Until the list arrives, the pipeline is:

1. Letter is named (task `legacy_task_id`, not display name).  
2. Risk is Routine / Operational (Conductor). Inspection *response* and *repair* fail this test; *reminder* passes (B).  
3. Locked template in `email_template_library.py`.  
4. Attachment + exclude rule from the sheet (Question I).  
5. Recipients = all parties in role(s).  
6. Tests: send, skip-if-satisfied, skip-if-manual, skip-if-no-mailbox, skip-if-repair-language.  
7. Feature flag off by default; staging soak; **one production promotion per week**.

Unknown Automated names still surface. Flipping a template to `Automated` without a playbook key must not send.

---

## 10. Open questions for the kickoff call

Jake asked for a call before the team goes too far down one path. These are the decisions that still change architecture, not copy.

1. **Naming (M):** Autopilot vs Trusted vs Aime-branded levels. Wizard Autopilot stays intake-only.  
2. **Class A list (C):** which letters after inspection reminders, in order.  
3. **Appendix A (I):** attachment markup, and 420/430 CD attach.  
4. **Client Aime timing:** conference claim is agent-side Morning Queue. Client Aime is W4 unless they want a read-only status bot sooner.  
5. **Terminated vs Closed vs Complete:** confirm the three-way split before we migrate status.  
6. **Obligation autonomy:** separate control vs mapped to deal posture (§6.2).  
7. **Vendor sample floor:** a number or “do not claim until we set one.”  
8. **TC authority:** product already gives TCs the agent workspace; any brokerage-level restriction beyond assignment?  
9. **Negotiation add-on:** confirm it stays out of TME and out of conference.

Ask Jake to send the demo video Audri mentioned; it will catch posture/copy mismatches faster than the call.

---

## 11. What we will not do

- Rebuild the product as multi-agent LLM specialists.  
- Let Aime send mail as an `agent_action`.  
- Auto-change dates, waive, release packets, or draft wire/funds mail.  
- Treat wizard Autopilot as deal Autopilot.  
- Treat ToBeAutomated as live send.  
- Treat user silence or no-edit behavior as a new grant.  
- Let one co-buyer authorize for all.  
- Put legal interpretation in Contract Intelligence.  
- Show Conductor / specialist names, reasoning trees, or internal routing in Aime chat.  
- Start new production workspaces on Autopilot with library send on.  
- Fire `POST /internal/schedules/tick` from local Chrome against live third-party addresses (`SMART_AUTOMATION_CHROME_TESTING_PLAN` blast-radius table still applies).

---

## 12. Jake §35 acceptance principles → how we will prove them

| # | Principle | Proof |
| --- | --- | --- |
| 1 | One Aime | UI chrome + email signature tests (W0) |
| 2 | Hidden specialists | No specialist strings in AgentPane fixtures |
| 3 | Provenance-aware truth | `transaction_facts` types (W2) |
| 4 | Inference ≠ fact | Inbound “appraisal Tuesday” does not write `appraisal_date` |
| 5–7 | Human-verified deadlines; ambiguity ↑ human | Wizard + amendment verify-deadline (W3) |
| 8 | Literal contract only | Chat refusal fixture |
| 9 | Perform routine when authorized | Existing executor tests + inspection reminder |
| 10 | Agent and TC | Existing `_WORKSPACE_ROLES` |
| 11 | Client Aime boundaries | W4 fixtures |
| 12 | Individual decision-makers | All-role recipient expansion (W0) + flags (W3) |
| 13 | Proactive friction | `agent_issues` + Needs You (exists); ladder (W2) |
| 14 | Gaps are hypotheses | Conductor Clarify (W2) |
| 15 | Portfolio priority | W3 sort |
| 16 | Third-party follow-up when authorized | Class B drafts now; Perform later if listed in C |
| 17 | Client updates earned | W4 |
| 18 | Negotiation add-on separate | No inspection-negotiated auto-send (B) |
| 19–20 | Vendor sample + person attribution | W5; silent until floor exists |
| 21–22 | Governed learning; private chats stay private | W5 |
| 23 | Strong challenge only with evidence | W3 |
| 24 | Refuse prohibited, not disagreement | W2 |
| 25–26 | Exception-based brokerage visibility; no client escalation | W2/W4 |
| 27 | Post-closing continues | 453/455/480/490 (W0); Complete ≠ Closed (W2) |
| 28 | Failed → LSE | Deferred |
| 29 | Provider-agnostic | Already |
| 30 | No pre-pending in TME | Already (wizard is accepted-contract intake) |

---

## 13. Suggested engineering order (practical)

Week-by-week is less useful than **dependency order**. Conference lock is ~four weeks from this date (2026-08-15 → 2026-09-12).

| Order | Work | Why this order |
| --- | --- | --- |
| 1 | W0 signature, identity, progress, co-contacts, posture-on-signup | Visible, decided, no new risk model |
| 2 | W0 task seeds 235 / 453 / 455 / testimonials / hybrids / 265 / 480 | Audri F–J, H; no Class A |
| 3 | W0 inspection reminder playbook behind flag | Only approved Class A growth |
| 4 | W1 dual HOA/utility + reply defaults + per-user style | Unblocks later letters |
| 5 | Soak staging; production after A–E (already answered) | Conference claim |
| 6 | W2 Conductor + facts + Terminated/Complete | Makes W3 safe |
| 7 | W3 contract supersession + advisory object + party authority | File quality |
| 8 | W4 client Aime | After policy exists |
| 9 | W5 learning / vendors | After signals exist |
| — | Appendix A + list C | Insert promotions at step 5+ one per week |
| — | Naming M | Rename copy only, after the call |

`SMART_AUTOMATION` S0–S3 operations work (tick timeout, preview on prod, closed-loop retry) **continues in parallel** and is not superseded. This document adds the TME intelligence strategy on top of that cage.

---

## 14. File-level implementation map (W0 first)

| Area | Backend | Frontend |
| --- | --- | --- |
| Aime signature | `agent_email_policy.py`, `ai_task_executor.py`, `ai_email_delivery.py`, `automation_posture_service.py` | `AdminAIGovernancePage.tsx`, `AutomationOvernightSection.tsx` |
| Identity | Chat system prompts in `transaction_agent.py`, `dashboard.py` | `AgentPane.tsx`, `AIChatPanel.tsx` |
| Progress | `task_progress.py` (completed Automated in); `dashboard.py` overdue filter unchanged | Workspace header / Overview (already consume `compute_task_progress`) |
| Recipients | `ai_task_executor.py` party resolution; `task_email_planner.py` | — |
| Posture at signup | Register/onboarding APIs + `merge_new_tenant_settings` | `RegisterPage.tsx`, `OnboardingWizard.tsx` |
| New tasks | `task_templates` seed migration (`legacy_task_id` 235, 453, 455); 460/470 rename | Task template admin (no UI design change) |
| Inspection reminders | `_EMAIL_PLAYBOOK` + templates + mandatory-review abort | Policy tag already understands library-send |
| Conductor (W2) | **new** `aime_conductor.py`; `internal_schedules.py` calls it per deal | No new page |
| Facts (W2) | **new** table + repo; parse/wizard write types | Optional provenance on key dates later |

---

## 15. Summary

Jake’s architecture is the TME product constitution: one Aime, hidden specialists, typed truth, explicit authority, a response ladder, and a hard line against legal/negotiation automation. The product we have is a strong **execution** system (posture, library letters, Needs You, guarded send) with fragments of intelligence (`agent_issues`, packet parse, suggestions) that are not yet a Conductor.

Audri’s answers tell us to **put Aime on the letters**, **show that she worked**, **let new users pick posture**, **add the missing seller/post-close tasks**, and **automate inspection reminders only** — not to open the library list and not to build delayed auto-send.

The strategy is: **keep the cage, name the assistant, then put a thin Conductor and a fact store in front of the engines we already trust.** That is the smallest architecture that honors Jake without throwing away the automation already running on staging.
