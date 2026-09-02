# Jake TME AI architecture vs staging

**Source:** `VE_Transaction_Management_Engine_AI_Agent_Architecture.md` (Jake, Phase 1 product architecture)  
**Checked:** 2 Sep 2026  
**Staging:** `https://app.stage.velvetelves.com` / `https://api.stage.velvetelves.com`  
**Account used:** `crazyaidev20500519@gmail.com` (Admin). I did not Send, confirm Run AI tasks, Disconnect, or Change status.

This review asks whether the **running staging product** adequately reflects Jake’s architecture. Jake’s own rule (§37) is to honor the **product behaviors**, not to stand up named microservices. §36 also defers MVP scope, UI, and code structure. The score below uses **§35 Core Acceptance Principles** as the bar.

---

## Verdict

Staging **does not yet adequately reflect the full architecture**. It **does** reflect the TME as a live transaction engine with one assistant named Aime, explicit send authority, and a leftover pile (Needs You). It **does not** yet implement Jake’s intelligence stack as a Conductor plus four specialist domains plus typed Memory & Provenance.

What is on staging today is the **execution layer** (posture, named library letters, overnight tick, drafts, Needs You, Ask AI for staff) plus **file intelligence** (contract extract, document resolver, stage pills, task library). What is missing is the **intelligence layer** Jake specified: typed facts vs hypotheses, the 11-step response ladder, earned client-update automation, client-facing Aime, vendor performance with sample-size rules, brokerage exception escalation, LSE handoff, and a Trusted-mode grant for contract-derived deadlines.

Engineering already chose this shape on 15 Aug 2026 in `TME_AI_ARCHITECTURE_AND_SMART_AUTOMATION_PLAN.md`: wrap the engines that exist; do not build seven LLM specialists. Staging matches that engineering plan more closely than it matches Jake’s module diagram. The product rules that the execution layer can honor (one Aime, no legal advice, no silent send except authorized letters, agent stays the authority) are largely in place. The product rules that need a provenance-aware file picture and a response ladder are only partly there.

**One-line summary for conference:** Staging can run a contract file with Aime as the assistant. It cannot yet keep Jake’s full sentry picture (typed truth, laddered response, client Aime, governed learning).

---

## How staging was checked

| Check | Result on 2 Sep 2026 |
|---|---|
| API health | 200 |
| Workspace default posture | **autopilot** on this QA tenant (product default for a **new** tenant is still Manual in code) |
| Hourly automation | `scheduler_enabled: true` |
| Named-email send | `library_send_enabled: true` |
| Needs You | 70 waiting items, recovery verbs on the first screen |
| Today's AI Briefing | live (`critical_count`, `needs_attention_count`, `on_track_count`, `suggested_focus`) |
| Sidebar KPIs | overdue, closing this week, active deals, pipeline |
| My Task Queue | live groups + suggested focus |
| Ask AI (staff) | workspace pane + floating button; system prompt is **Aime**, not a lawyer |
| Ask AI (client portal) | **not present** |
| Dual library after restore | Both-Fin preview: Deliver Title to Buyer **and** Seller; buyer utility; no co-op welcome |
| Listing Success Engine | **not in the product** |

---

## Architecture map (Jake §5–§6 vs what actually runs)

Jake’s diagram is Aime → Conductor → Transaction / Contract / Advisory / Client specialists → Memory, Learning, Product Intelligence.

Staging maps those **ideas** onto existing modules. There is no Conductor service and no specialist LLM per domain.

| Jake layer | Staging equivalent | Fit |
|---|---|---|
| **Aime** (§5.1) | Ask AI (`POST /transactions/{id}/agent/chat`, `POST /dashboard/ai-chat`), Aime signature on auto-send, FAB on staff shells | Strong for **staff**. Missing for buyers/sellers. |
| **Conductor** (§5.2) | Spread across `automation_posture_service`, `ai_task_executor`, `agent_email_policy.gate`, `agent_policy` (forbids `send_email` from chat), Needs You routing | Partial. Authority and send gates exist. Contextual risk categories and an 11-step ladder do not. |
| **Transaction Intelligence** (§5.3) | Transaction row + tasks + `compute_stage_pill` + workspace plan + Dual filter | Partial. Stage is a **health pill** (Critical / On Track / In Inspection), not Jake’s 13 lifecycle stages. Dual agency is a use-case + library flags, not a specialist diagnosis. |
| **Contract & Document Intelligence** (§5.4) | Wizard Fast intake, Textract + LLM extract, `document_packet_parsing`, `contract_resolution` (amendments can supersede), `amendment_date_gate` | Strong extract. Literal-language boundary is in chat/email prompts. Human verification of extracted deadlines is the wizard Confirm Details screen, not a typed “proposed obligation.” |
| **Advisory Intelligence** (§5.5) | AI Suggestions (`GET /api/v1/ai/suggestions`), briefing `suggested_focus`, Task Queue focus, Needs You | Partial. Detectors are deterministic (financing window, stale comms, missing docs, predicted miss, closing gift). No strong-challenge, no recommendation competition, no talking-points pack. |
| **Client Interaction Intelligence** (§5.6) | Client portal (Home, Next Steps, Timeline, Documents, Updates) with **no Aime chat**. FSBO has a comment about FloatingAskAi; represented clients do not. | Weak vs Jake. Aligned with current Audri testing rule: a client-facing Aime chat is treated as a fail. |
| **Memory & Provenance** (§6.1) | Documents + extract fields + audit log + communication logs. Extract has source strings. No typed fact model (verified / reported / inference / hypothesis / obligation). | Weak. Inference can sit in extracted fields until a person edits them. |
| **Learning & Pattern** (§6.2) | Analytics extras (avg response time), suggestion feedback endpoint, post-close suggestion detectors | Weak. No governed promotion of patterns. No vendor sample-size claims. |
| **Product Intelligence** (§6.3) | Platform AI usage / costs consoles | Out of TME file-running. Not Jake’s product-learning loop. |

---

## Scope (§2)

| Jake requirement | Staging |
|---|---|
| TME starts at accepted / executed contract | Yes. Wizard + Fast intake. No Listing Success Engine upstream. |
| Buyer, seller, Dual | Yes. Six use cases. Dual restored 2 Sep to Audri Q1 (300+310, 150 on Dual, 160 off). |
| With or without a human TC | Yes. Agent and TC share the staff shell when assigned. |
| Client-facing Aime | **No chat.** Portal is status, docs, next steps. |
| Agent- and TC-facing Aime | Yes. |
| Contract / deadline / document intelligence | Partial (extract + tasks + compliance). |
| Communication monitoring | Email inbox + triage (money, dates, documents). No SMS, call summaries, or voice notes. |
| Portfolio prioritization | Briefing + queue focus + Needs You. Not a ranked “one next action” with Jake’s full factor set. |
| Post-closing obligations | Task library includes post-close rows (Closing Gift, lockbox/MLS Sold 453/455, testimonials). Closing a file is a **status**, not “all post-close work is done.” |
| Failed-transaction handoff to LSE | Terminated status exists. **No LSE.** Offer-LSE-as-paid-add-on is not in the product. |
| Pre-pending listing/buyer work out of scope | Honored. No property search, showings, or listing marketing in TME. |

---

## Principles Jake cares about most

### One assistant, hidden specialists (§3.1, §35.1–2)

Staff always see **Aime**. Chat prompts say coordinator, not lawyer. Internal names (executor, classifier, Dual filter, triage) do not appear in the UI. **Honored** on staff surfaces.

### Advisor, never the authority (§3.2, §35.10)

Ask AI proposes cards for approval. `agent_policy` forbids `send_email` from the agent. Library send is gated by posture + `agent_email_policy` hard gates. Agent/TC remain the professional. **Honored** for send and chat writes.

### If Aime can do it, she should (§3.3, §35.9)

On Autopilot, authorized named letters may send. Assisted drafts for a tap. Manual does not send those letters. Overnight can prep. That is the current “do the admin work” line, **narrower** than Jake’s “perform whenever reliable.” Inspection Negotiated and most library letters still wait for a person (Audri). **Partial.**

### No inference as fact; provenance (§3.4–3.5, §35.3–4, §14)

Inbound mail can be labeled (money, date, document). Fast intake fills wizard fields from a packet. `contract_resolution` keeps source document ids when an amendment wins. There is **no** first-class hypothesis object, and no UI that says “reported vs confirmed.” Missing-channel copy (“it looks like we may be further ahead”) is not a product feature. **Partial / weak.**

### Authority must be explicit (§3.6, §8.2, §32, §35.6, §35.17)

Posture is an explicit grant (workspace default + per-deal pin). New tenants default Manual in code. Repeated no-edit on drafts does **not** promote send rights. Client-update earned automation (draft → learn → suggest → explicit grant → send) is **not built**. Jake’s **Trusted Mode** for auto-activating contract deadlines is **not** a separate setting; Autopilot is send authority, not deadline-activation authority. `amendment_date_gate` is the closest piece: Manual/Assisted wait; Autopilot applies only when the later document is explicit and complete. **Partial.**

### Contract boundary (§5.4, §24, §35.7–8)

Chat and email policy strip / block legal-advice wording. Inspection reminder is deadline-only. Aime may quote a date from the file. She is not supposed to say what a clause “legally means.” **Honored** in prompts and send gates. Human verification of *new* extracted deadlines is the wizard review, not a standing obligation queue.

### Risk model (§9)

Jake’s four buckets (routine, relationship, professional judgment, authority) are **not** named in the product. Risk is approximated by overdue counts, Needs You block codes, email mandatory-review topics, and suggestion categories. **Not honored as a model.** Behavior often still lands in the right bucket (inspection strategy stays human; wire/legal topics cannot auto-send).

### Response ladder (§14, §33, §35)

Jake: No action / Watch / Early awareness / Perform / Inform / Clarify / Recommend / Request decision / Strong challenge / Refuse / Escalate.

Staging collapses this to:

- **Perform** — Autopilot named letters, some overnight prep  
- **Inform / leftover** — Needs You, briefing, queue  
- **Recommend** — AI Suggestions  
- **Refuse** — hard email gates, chat will not send  
- **Escalate** — stale email escalation hours to the **agent’s** review pile, not a managing broker workflow  

Watch, strong challenge, and brokerage-visible exception escalation are **missing**. **Partial.**

---

## §35 scorecard (the acceptance list)

| # | Principle | Staging | Notes |
|---:|---|---|---|
| 1 | One continuous Aime | **Honored** (staff) | Same name in chat, FAB, auto-send signature. |
| 2 | Specialists stay hidden | **Honored** | No Conductor/specialist labels in UI. |
| 3 | Central, provenance-aware truth | **Partial** | One transaction record. Extract has sources. No typed memory. |
| 4 | Inference never silently becomes fact | **Partial** | Wizard lets you edit extract. No hypothesis type. Dates-from-email do not auto-move (Feature 24). |
| 5 | Contract deadlines human-verified by default | **Partial** | Confirm Details is the verify step at create. Later extracts are weaker. |
| 6 | Higher deadline autonomy needs explicit grant | **Partial** | Autopilot ≠ Trusted Mode. Amendment gate is the only later-document grant. |
| 7 | Ambiguity increases human involvement | **Partial** | Fuzzy amendment always waits. Conflicting docs need a person, but there is no dedicated “verify this conflict” specialist. |
| 8 | Literal contract language, no legal interpretation | **Honored** | Chat + email policy. |
| 9 | Perform routine admin when authorized | **Partial** | Named Autopilot letters + drafts. Not general admin. |
| 10 | Agent and authorized TC share the file | **Honored** | Same workspace when assigned. |
| 11 | Clients interact with Aime under client rules | **Not honored** | Portal has no Aime. Current Audri test rule also forbids a client Aime chat this round. |
| 12 | Multiple decision-makers stay individual | **Partial** | Multiple buyer/seller party rows exist. No unanimity / “who approved” model. |
| 13 | Proactive deadlines and friction | **Partial** | Tasks, briefing, Needs You, suggestions. Not a full friction diagnosis. |
| 14 | Communication gaps are hypotheses, not invented history | **Partial** | Absence of a call is not treated as “it did not happen.” Missing-channel clarification copy is not built. |
| 15 | Prioritize the whole pending book | **Partial** | Briefing + queue + Needs You. Not Jake’s full ranking. |
| 16 | Follow up with third parties when authorized | **Partial** | Task emails to title/lender/co-op. No vendor-delay specialist. |
| 17 | Client updates start with review; automation is earned + explicit | **Not honored** | No client-update product with that progression. |
| 18 | Negotiation intelligence is a paid add-on | **Honored by absence** | Not in the stack. Inspection Negotiated stays human. No silent paid add-on. |
| 19 | Vendor intelligence needs a real sample | **Not honored** | No vendor performance claims product. Analytics has response-time numbers, not Jake’s evidence standard. |
| 20 | Attribute vendor performance to the person | **Not honored** | Parties are named. No performance layer. |
| 21 | Cross-transaction learning via governed signals | **Not honored** | Suggestions/analytics are per tenant, not promoted patterns. |
| 22 | Private chat does not become platform content | **Honored as designed** | Workspace chat is tenant-scoped. No platform training pipeline from chats. |
| 23 | Challenge judgment only with strong new evidence | **Not honored** | No strong-challenge feature. |
| 24 | Refuse prohibited execution; do not refuse mere disagreement | **Honored** | Gates refuse send. Chat does not argue policy with the agent. |
| 25 | Brokerage visibility is exception-based | **Partial** | Team Lead / Admin see team queues. No “exception threshold” that suddenly opens a private Aime thread to the broker. |
| 26 | Client-facing escalation never shows internal risk workflow | **Honored by absence** | Clients do not see Needs You or internal block codes. |
| 27 | Closing does not end post-closing work | **Partial** | Post-close tasks exist. Status Complete/Closed is independent of those rows. |
| 28 | Failed files can return to LSE | **Not honored** | Terminated exists. LSE does not. |
| 29 | Provider/model/DB out of this spec | **Honored** | OpenAI/Claude/Textract/Supabase are implementation choices. |
| 30 | Pre-pending work stays out | **Honored** | No listing/search TME. |

**Count:** 8 honored · 12 partial · 8 not honored · 2 honored-by-absence (18, 26).

That is **not** “adequately reflects” if the bar is Jake’s full sentry. It **is** a coherent first TME slice if the bar is §37’s smallest architecture that does not break the hard rules (authority, no legal advice, no silence-as-consent, no LSE bleed-in).

---

## Live product behaviors that *do* match Jake

1. **Aime is the only staff assistant.** Workspace Ask AI, dashboard chat, and auto-send signature use that name. Specialists are code, not personas.
2. **Send authority is explicit.** Manual / Assisted / Autopilot. Library send and hourly jobs are workspace switches. Chat cannot send mail.
3. **Hard stop on legal / high-risk mail.** `agent_email_policy` mandatory review and gates. Inspection reminder is deadline-only.
4. **Dual is a TME concern, not a listing concern.** Buyer and seller rows both populate. Co-op-target rows do not. Vendor targets once.
5. **Extract, don’t invent.** Fast intake and packet parsing fill the file from documents. Chat is told to work only from context.
6. **Later documents can control.** `contract_resolution` + `amendment_date_gate` keep history and do not silently overwrite on Manual/Assisted.
7. **Leftover work has a place.** Needs You is the human residual. Recovery (Add contact, Upload document) is on the first screen.
8. **Portfolio surfaces exist.** Briefing, KPIs, Task Queue, deal-list pills.
9. **Terminated is a first-class status.** It is not an LSE handoff, but it is not hidden as “closed.”
10. **Pre-pending is out.** Staging TME does not run listings or buyer search.

---

## Gaps that matter if we want staging to *reflect* the architecture

These are the holes I would treat as “not yet Jake,” not as CASA or polish.

### Intelligence (the missing middle)

- No Conductor that classifies every event onto the 11-step ladder.
- No typed Memory (verified fact / hypothesis / obligation / authority).
- Stage pills are **health**, not Jake’s Accepted → EM → Inspection → Financing → … → Complete lifecycle (overlapping stages allowed).
- Advisory is a small detector set, not next-best-action with evidence, confidence, and “what changed.”
- No strong challenge when new evidence reopens a settled call.

### Authority Jake named that Autopilot does not cover

- **Trusted Mode** for high-confidence contract deadlines.
- **Earned client-update automation** (observe edits → suggest → explicit grant → send, invalid if facts change).
- Silence still does not grant send (good), but there is also no suggestion to *ask* for that grant.

### Client Aime (§4.3, §5.6, §35.11)

Jake: buyers/sellers may ask Aime for status, next steps, reassurance, and routing. Aime must not give legal advice or negotiate.

Staging: represented client portal has **no assistant**. That is a product choice in the current Aime testing guidelines (client Aime chat = fail this round). It is still a **gap vs Jake**. Building it later must keep the refusal boundary or it will violate §24/§25.

### Parties and consensus (§4.4, §12, §35.12)

Multiple buyers/sellers can be contacts. There is no model of required decision-makers, unanimity, or “this person approved.” Aime cannot yet refuse “manufacture consensus.”

### Communication channels (§11)

Email is live. SMS, calls, voice notes, and “progress happened off-channel, please confirm” are not. Absence-is-not-proof is mostly true by not inferring from silence, not by asking Jake’s clarification question.

### Learning, vendors, LSE (§19–§21, §30–§31, §35.19–21, §35.28)

No vendor performance with sample size and person-level attribution. No governed cross-file pattern promotion. No Listing Success Engine, so no seamless failed-file handoff and no inherit-from-listing intake.

### Escalation (§26–§27, §35.25)

Needs You and Email “escalated” mean **the agent must look**. Jake’s managing-broker / brokerage-admin exception path is not a product object. History is kept (audit, comms, tasks); automatic downgrade of professional-judgment issues is not.

---

## What I would not score as a miss

Jake §36 explicitly does not define model, database, event bus, exact UI, or MVP. Missing a Conductor **service** is not a fail of §36.

Negotiation add-on missing is correct for this phase.

CASA auth/session/TLS work is outside this architecture file.

Commission payouts and AI Coach teasers are parked product, not Jake TME intelligence.

---

## Adequacy by Jake chapter

| Chapter | Adequacy on staging |
|---|---|
| 1 Purpose (sentry, reduce anxiety) | Partial. Tasks and Needs You keep work visible. Client reassurance Aime is absent. |
| 2 Scope | In-scope TME yes. LSE and client Aime no. |
| 3 VE-wide principles | Strong on authority and one assistant. Weak on provenance and “do all reliable admin.” |
| 4 Users | Agent/TC yes. Client Aime no. Multi-party consensus no. |
| 5 Operating architecture | Execution yes. Specialist diagram no. |
| 6 Shared layers | Logs and extract sources only. |
| 7 Lifecycle | Status + health pills, not 13 stages. |
| 8 Contract deadlines | Extract + wizard confirm + amendment gate. No Trusted Mode. |
| 9 Risk model | Implicit in gates, not a model. |
| 10 Negotiation add-on | Correctly absent. |
| 11 Communication monitoring | Email only. |
| 12 Parties | Contact roles exist. Processor/underwriter/HOA/insurance as first-class parties are thin or missing. |
| 13 Issue detection | Tasks overdue, Needs You codes, a few suggestion detectors. |
| 14 Response ladder | Collapsed to perform / leftover / recommend / refuse. |
| 15 Portfolio | Briefing + queue. |
| 16–17 Client updates and relationship | Not built. Stale-comms suggestion is the closest. |
| 18–20 Vendor and learning | Not built to Jake’s standard. |
| 21–23 Learning rules, preferences, strong challenge | Posture + playbook flags. No challenge. |
| 24–25 Interpretation and refusal | Honored in prompts and send gates. |
| 26–28 Escalation and diagnostics | Agent leftover pile. No broker exception workflow. Chat does not dump chain-of-thought (good). |
| 29 Post-closing | Tasks exist; Complete ≠ all obligations done. |
| 30–31 LSE | Not in product. |
| 32 Client update progression | Not built. |
| 33 Intelligence cycle | Event → tick/executor/Needs You. Not the 10-step cycle. |
| 34 Specialist handoff | N/A (no specialists). |
| 35 Acceptance | See scorecard. |
| 36 Deferred tech | Correctly not claimed. |

---

## Bottom line

Staging **adequately reflects the TME execution product** that Audri and the 15 Aug engineering plan described: Aime as the staff assistant, Manual / Assisted / Autopilot, named letters, Needs You, contract extract, Dual files, and no legal advice.

Staging **does not adequately reflect Jake’s AI Agent & Intelligence Architecture** as a finished intelligence system. The diagram in §38 is still a north star. The running system is a smaller conductor-less wrap around tasks, documents, email, and posture.

If the next pass is meant to close the gap with Jake, the highest-leverage slices are: (1) typed file facts vs hypotheses, (2) a real response ladder on top of Needs You, (3) Trusted-mode / earned grants that stay explicit, and (4) client Aime with the same refusal boundary. LSE and vendor-performance learning stay later; they are not required to keep TME honest on a pending file.
