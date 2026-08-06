# Agent Email Guideline & Task Attachment Rules — Implementation Plan

**Date:** 2026-08-05
**Author:** Jan Froben
**Sources:** Jake's WhatsApp thread (2026-08-05), Jake's email "Email .md & Attachments for tasks",
`velvet-elves-data/Agent_Email_Instructions.md` (v1.0), `velvet-elves-data/Tasks_Attachments.csv`
**Status:** PLAN ONLY — nothing in this document is implemented yet.
**Verified against:** working tree of `velvet-elves-backend` / `velvet-elves-frontend` as of 2026-08-05.

---

## 0. Executive summary

Jake delivered two artifacts that together define how the communications agent must write and
send email:

1. **`Agent_Email_Instructions.md`** — a 23-section production specification: an assistant identity
   ("Aime"), 7 email categories, 2 delivery modes, 15 hard auto-send gates, a mandatory-review list,
   subject-line patterns, per-category body structures, a missing-information marker format, and a
   5-field JSON output contract.
2. **`Tasks_Attachments.csv`** — 31 rows keyed by task ID saying which documents each task's email
   must **attach** and which it must **omit**.

The WhatsApp exchange already settled the architecture question: **option 3 — structured
underneath, clean email on screen.** This plan builds on that answer and does not reopen it.

The honest headline is this: **the guideline describes a system that is about 40% built.** The
plumbing Jake's spec assumes — deterministic templates, party resolution, attachment resolution,
attachment honesty, a review queue, confidence scoring, a guarded single send path — all exists and
is good. What does not exist is the **governing policy layer**: there is no category vocabulary, no
delivery-mode vocabulary, no per-category auto-send authorization, no mandatory-review interception,
no missing-information markers that actually block a send, no Aime identity, and no data-driven
attachment rules. Attachment rules today are a hard-coded 7-entry Python dict covering 5 document
kinds; Jake's spreadsheet needs ~14 document kinds across 31+ tasks, **with exclusions, for which
there is no mechanism at all.**

There is also a reconciliation problem that has to be solved before any code is written: **Jake's
spreadsheet and the shipped task library do not agree.** Three task IDs in the CSV do not exist in
the database, two rows have names that differ from the library, and **32 tasks in the library are
missing from the CSV entirely** — including task 80 "Confirm Title Order", which is already flagged
`Automated` and already sends attachments in production. Jake explicitly asked for this list back.

**Recommended sequencing:** Phase 0 (reconciliation, no code) goes back to Jake immediately, because
Phases 2 and 8 cannot be finished without his answers. Phases 1, 3, 4, 5 are unblocked and can start
now.

---

## 1. Finalized requirements

Each requirement is traceable to its source. "Spec §" refers to `Agent_Email_Instructions.md`.

### 1.1 Content & structure

| ID | Requirement | Source |
| --- | --- | --- |
| R1 | Every agent-generated transaction email is classified into exactly one of 7 `email_category` values. | Spec §5 |
| R2 | Every email carries exactly one `delivery_mode`: `agent_reviewed_draft` or `aime_auto_send`. | Spec §6 |
| R3 | Subject lines follow the 8 per-category patterns and identify purpose + property. | Spec §12.2 |
| R4 | Subjects use the **street address only**, escalating to the full address only when another property could be confused with it. | Spec §12.1 |
| R5 | Bodies follow the universal structure (greeting → optional opener → message+CTA → completion instructions → signature), overridden by the 7 category-specific structures. | Spec §13, §16 |
| R6 | The friendly opener is suppressed in reminders, scheduling confirmations, status updates, active threads, and problem notices. | Spec §13.2 |
| R7 | Transaction status updates carry **no CTA**. | Spec §16.5 |
| R8 | Completion instructions use the task's stored completion method verbatim; the agent never invents a link, destination, deadline, or workflow. | Spec §13.4 |
| R9 | Multiple related requests to the same recipient/property/owner/method are combined into one bulleted "Items Needed" email; differing owners or methods force separate emails. | Spec §18 |
| R10 | The agent's saved language, preferred phrases, and prohibited phrases are applied; prohibited phrases are never emitted; style never overrides facts, structure, or safety. | Spec §11, §3 |

### 1.2 Identity & signature

| ID | Requirement | Source |
| --- | --- | --- |
| R11 | `agent_reviewed_draft` is written in the **agent's** voice with the agent's saved signature; Aime is never named. | Spec §6.1, §15.1 |
| R12 | `aime_auto_send` is written **as Aime**, using the 5-line Aime signature block (name / "Assistant to {agent}" / brokerage / phone \| email / "RE: topic – address"). | Spec §6.2, §15.2 |
| R13 | Aime never impersonates the agent and never claims the agent personally performed, reviewed, approved, or decided anything unless verified. | Spec §6.2 |
| R14 | A missing required signature field blocks automatic sending. | Spec §15.2 |

### 1.3 Safety & delivery

| ID | Requirement | Source |
| --- | --- | --- |
| R15 | All 15 auto-send gates must pass before any automatic send. No confidence score overrides a failed hard gate. | Spec §7 |
| R16 | The 17 mandatory-review subjects (wire/payment/banking, legal interpretation, contract changes, defaults, cancellations, SSN/credential requests, negotiation positions, **inspection responses**, **repair demands**, every problem notice) are never auto-sent regardless of confidence or category authorization. | Spec §8 |
| R17 | Auto-send requires the user to have enabled it **and** to have authorized the specific category. | Spec §7.1, §7.2 |
| R18 | Confidence is an integer 0–100 measuring factual/addressing/classification/wording/delivery-mode safety — never polish. It is never revealed in the email body. | Spec §9 |
| R19 | Missing or unverified required information produces `**[MISSING: FIELD]**` / `**[CONFLICT: …]**` markers, forces `agent_reviewed_draft`, and **prevents the draft from being sent until resolved**. | Spec §17 |
| R20 | Conflicting verified sources block auto-send and route to review. | Spec §4.3, §7.13 |
| R21 | Recipients are never added without agent review; existing recipients are preserved unless privacy or relevance requires removal; private contact details are never cross-exposed. | Spec §14 |
| R22 | An attachment is mentioned in the body **only when verified as included**. | Spec §4.3 |
| R23 | Timing (when an email fires, follow-up cadence) is owned by the task engine and must not be inferred from this guideline. | Spec §2, §16.2 |

### 1.4 Output contract

| ID | Requirement | Source |
| --- | --- | --- |
| R24 | The model returns exactly five top-level JSON fields: `email_category`, `delivery_mode`, `confidence_score`, `subject`, `body`. No commentary inside that object. | Spec §19.1 |
| R25 | The user preview shows subject + rendered body only — no JSON, no internal values, no confidence reasoning. Category/mode/confidence may be displayed **outside** the preview. | Spec §19.2 |
| R26 | Preview subject/body must byte-match the internal JSON subject/body. | Spec §19.2, §21 |

### 1.5 Attachments (the spreadsheet)

| ID | Requirement | Source |
| --- | --- | --- |
| R27 | Each task has an explicit **attach** list of document kinds. | CSV col. "Documents to Attach" |
| R28 | Each task has an explicit **exclude** list of document kinds that must never ride that email even when present on the deal. | CSV col. "Documents to Exclude" |
| R29 | Welcome emails (10/20/30) carry the **full purchase/sale package**: PA, LBP, SD, Counters, Addendums, Amendments, EM copy if available. | CSV rows 2–4 |
| R30 | Loan Officer Welcome (60) and Order Title (70) carry PA + all Counters + BLC/Tax Sheet (+EM for 60, +SD for 70) and **exclude Addendums & Amendments**. | CSV rows 5–14 |
| R31 | HOA (90/95/100) and Utility (130/135/140) tasks **check the document center first** and only email when the document is absent. | CSV rows 15–20 |
| R32 | Title-delivery tasks (290/300/305/310/320) attach the **title work**. | CSV rows 29–33 |
| R33 | Appraisal Ordered (260) attaches the purchase agreement. | CSV row 26 |
| R34 | Attachment selection is deterministic and performed by the application, never by the model. | Derived from R22 + WhatsApp option 3 |

---

## 2. Answer to the open question in the WhatsApp thread

I asked Jake which five fields the guideline meant. §19.1 answers it, and the answer is consistent
with what I said: **the five fields are the model's output contract, not the system's draft record.**

**What the model returns (spec §19.1) — 5 fields:**
`email_category`, `delivery_mode`, `confidence_score`, `subject`, `body`.

**What a draft actually carries in the product today** (`app/models/communication_log.py`) — 11
operational fields the model must never author:
`recipient_emails`, `cc_emails`, `attachment_ids`, `transaction_id`, `parent_log_id` (threading),
`ai_confidence`, `ai_assumptions`, `ai_source_data`, `approval_status`, `escalation_due_at`,
`thread_key`.

This split is not a discrepancy to resolve — it is the correct design, and it is what makes the
spreadsheet enforceable. **Attachments are conspicuously absent from Jake's five fields, and they
must stay absent.** If the model chose attachments, §4.3 ("mention an attachment only when the
attachment is verified as included") could not be guaranteed. The app resolves attachments from the
task's rule + the deal's real document set, then the body is rewritten if anything fails to attach
(`ai_email_delivery.py:286-312` already does exactly this). The model is told what *will* ship; it
never decides.

**Two type conversions are needed at the boundary:**

| Spec | Product today | Resolution |
| --- | --- | --- |
| `confidence_score` integer 0–100 | `communication_logs.ai_confidence` float 0.0–1.0 | Convert at the model boundary. Store **one** representation (float, as today). Display as an integer percentage. Never persist both. |
| `delivery_mode` on the email | `approval_status` ∈ `pending_review` / `auto_approved` / `approved` | `delivery_mode` is the *intent*; `approval_status` is the *lifecycle state*. Persist both — they answer different questions. |

---

## 3. Current implementation map

This is what exists today. Everything below was read in the working tree, not recalled.

### 3.1 The four paths that produce an agent email

| # | Path | File | Body source | Sends? |
| --- | --- | --- | --- | --- |
| A | AI task executor (`Automated` task rows) | `app/services/ai_task_executor.py:416-587` | Deterministic library template | **Yes — auto-sends, no human stop** |
| B | Task email flow ("Send & complete task") | `app/services/task_email_planner.py:406-573` | Deterministic library template | Yes, on explicit user confirm |
| C | Inbound reply engine + `compose_outbound` | `app/services/ai_email_engine.py:280-683` | LLM (`_draft_factual_from_context_ai`, `_compose_from_intent_ai`) or deterministic fallback | No — drafts only |
| D | Auto-draft sweep | `app/services/task_notification_service.py:768+` | Via `compose_outbound` | No — drafts only |

All four converge on the one guarded send path, `send_ai_draft` (`app/services/ai_email_delivery.py:83-151`).

**Path A is Jake's `aime_auto_send` in all but name** — and it is the one that is currently
**ungated**. Its own docstring says it "deliberately goes beyond the automation posture's 'nothing
sends without a tap' rule". Under spec §7 that is no longer acceptable without gates 1 and 2.

### 3.2 What already satisfies the spec

Genuinely good foundations that should not be rebuilt:

- **Attachment honesty (R22).** `resolve_draft_attachments` + `rewrite_body_for_attachment_fallback`
  (`ai_email_delivery.py:175-312`) neutralize "attached is…" and substitute secure links when a file
  cannot be inlined. This *is* §4.3, already shipped.
- **Deterministic bodies for auto-sent mail.** Path A never lets an LLM free-write an unreviewed
  send (`ai_task_executor.py:22-24`).
- **Recipient resolution from captured parties only.** `task_email_planner.py:241-350`; no recipient
  → the task surfaces instead of sending. That is §7.6 and §14 partially satisfied.
- **Required-document blocking.** `ai_task_executor.py:449-463` refuses to send a title order without
  the purchase agreement. That is the right instinct, applied to one document kind.
- **Idempotency.** `compose_outbound`'s `task_id` / duplicate-draft reuse (`ai_email_engine.py:595-649`).
- **Grounding + source validation.** `_validated_source_data` forces every model-cited value to copy
  a real context value (`ai_email_engine.py:2107`). That is §4.3's spine.
- **Money guardrail.** `KIND_MONEY` is excluded from `AUTO_APPROVABLE_KINDS` (`ai_email_engine.py:108-110`) —
  a subset of §8.
- **Signature.** `_owner_signature` (`ai_email_engine.py:1720-1748`) reads
  `profile_settings_json.email_signature`, falling back to name/company/phone. §15.1 is satisfied.
- **Confidence threshold + tone settings** exist end to end: `TenantAiEmailSettings`
  (`app/api/v1/ai_emails.py:196-205`) ↔ `EmailAutomationSection.tsx`.
- **Clean preview (R25/R26).** `AiEmailReviewPage.tsx` and `TaskEmailFlow.tsx` render subject + body
  as editable text; confidence/assumptions live outside the body. Option 3 is already the shipped shape.

### 3.3 What does not exist at all

| Spec | Status |
| --- | --- |
| §5 `email_category` vocabulary | **Absent.** The nearest thing is `ai_kind` (`factual`, `document_request`, `money`, …) — an *inbound classifier*, different axis, different values. |
| §6 `delivery_mode` vocabulary | **Absent.** |
| §6.2/§15.2 "Aime" identity + signature | **Absent.** `grep -ri aime` across both repos returns zero hits. Auto-sent mail is signed as the agent today. |
| §7 the 15 gates | **~4 of 15 exist**, scattered and only on path C. |
| §7.1/§7.2 per-category auto-send authorization | **Absent.** No per-category toggle anywhere. |
| §8 mandatory-review interception | **Absent** on paths A/B/D; partial on C (money only). |
| §12.2 subject patterns | **Absent.** Template subjects are ad hoc ("Title order: {{property_address}}"). |
| §12.1 full-address escalation | **Absent.** No ambiguity check. |
| §13.2 friendly-opener suppression rules | **Absent.** |
| §13.4 exact completion method | **Absent in data.** `tasks.completion_method` exists in the model (`app/models/task.py:29`) but is **not in the seed migration's column list** — it is NULL for every system template. |
| §17 missing/conflict markers | **Absent.** `ai_assumptions` is advisory and blocks nothing. |
| §11 preferred/prohibited phrases | **Absent.** |
| §19.1 five-field contract | **Absent.** Prompts return `{subject, body, confidence, source_data, assumptions}`. |
| CSV exclusions (R28) | **Absent — no mechanism exists.** |
| CSV preconditions (R31) | **Absent.** |

### 3.4 Three concrete defects the spreadsheet exposes

These are not "not yet built" — these are wrong today.

**D1 — The document matcher over-attaches, and Jake's exclude column has no way to stop it.**

```python
# app/services/ai_task_executor.py:129-136
_DOC_MATCHERS = {
    "purchase_agreement": (("purchase_agreement",), ("purchase agreement",)),
    "counter_offer":      (("counter_offer",),      ("counter",)),
    "tax_sheet":          (("ownership_record", "tax_sheet"), ("blc", "tax")),
    "earnest_money":      (("earnest_money",),      ("earnest",)),
    "sellers_disclosure": (("disclosure", "sellers_disclosure"), ("disclosure",)),
}
```

`_match_documents` (`ai_task_executor.py:1017-1034`) matches if *any* of doc_type, detected type, or
a **bare filename keyword** hits. Consequences on a real deal:

- `"disclosure"` matches **"Lead-Based Paint Disclosure.pdf"** and **"Closing Disclosure.pdf"**.
  Order Title (task 70) therefore attaches the LBP and the CD — neither is on Jake's list for that task.
- `"counter"` matches **"Counter Offer Addendum.pdf"** — an *addendum*, which Jake's row 9/14
  explicitly excludes from tasks 60 and 70.
- `"tax"` matches anything with "tax" in the name.
- A single document can match several kinds and be attached twice.

**D2 — The kind vocabulary is wrong.** `_DOC_MATCHERS` mixes three unrelated taxonomies:

| Vocabulary | Where it is defined | Example values |
| --- | --- | --- |
| Storage doc types | `app/models/enums.py:72-100` (`DocumentType`) | `blc_tax_sheet`, `lead_paint_disclosure`, `title_work`, `hoa_docs`, `utility_info` |
| Packet-parser detected types | `app/services/document_packet_parsing.py:519-525` | `hoa_package`, `title_commitment`, `utility_confirmation`, `emd_receipt` |
| Resolver families | `app/services/contract_resolution.py:95-122` | `ownership_record`, `disclosure`, `title`, `hoa` |

`_DOC_MATCHERS["tax_sheet"]` looks for `ownership_record` (a *family*) and `tax_sheet` (which is not
a value in any of the three) — **the real enum value `blc_tax_sheet` is never matched by doc_type at
all.** A correctly classified BLC/Tax Sheet only attaches by filename luck.

**D3 — Several tasks Jake wants automated are phone tasks in the library, and the spreadsheet
silently converts them to email.** From the seed migration:

- Task **260 "Appraisal Ordered"** — description: *"Call the loan officer and ask if the appraisal
  has been ordered…"*. Jake's CSV says attach the purchase agreement, i.e. send an email.
- Tasks **270, 330, 340** — all "Call the loan officer…".
- Tasks **130/140** — "call the listing agent / seller … **and send a follow up email**" (hybrid).
- Tasks **480/490** — physical Thank You **cards**, not email at all.

Converting a call task into an email task is a workflow decision, not an attachment rule. It needs
Jake's explicit confirmation before it ships.

Separately, task **300 "Deliver Title"**'s own description reads: *"Once title work is received,
click 'send email and complete task' and attach the title work"* — a workflow the product **cannot
currently perform**, because there is no `title_work` matcher and no playbook entry for it.

---

## 4. Conflicts and decisions

### 4.1 DECISION REQUIRED — the "Aime" identity on auto-sent mail

Spec §6.2 and §15.2 require auto-sent email to be written **as Aime** and signed:

```
Aime
Assistant to {{Agent_Name}}
{{Agent_Brokerage}}
{{Agent_Phone}} | {{Agent_Email}}
RE: {{Topic}} – {{Property_Address}}
```

Today, auto-sent task mail is signed **as the agent** (`_apply_tone_rules`,
`ai_email_engine.py:1814-1822`). This changes what a real buyer, seller, lender, and title rep sees
on live production mail.

There is a standing invariant in the codebase from the 2026-07-10 client decision: *recipients are
never told AI wrote the message* (`ai_email_engine.py:31-34`, and the AI-disclaimer stripping in
`ai_email_delivery.py`). **I do not read §15.2 as reversing that invariant.** "Aime — Assistant to
Morgan Lee" names an assistant, not an AI; a recipient learns there is an assistant on the file, the
same as any human TC. The two are compatible, and I recommend implementing §15.2 as written with a
hard guardrail test asserting no outbound body or signature ever contains "AI", "artificial
intelligence", "bot", "automated", or "Velvet Elves" (the one existing exception —
`task_pending_reminder`, `email_template_library.py:190-203` — goes to the account holder's own
inbox and stays as is).

**What Jake must confirm:** that auto-sent mail should stop being signed as the agent. This is
customer-visible on live deals and I will not flip it unilaterally.

### 4.2 DECISION REQUIRED — inspection-response tasks cannot be auto-sent

Spec §8 lists **"Inspection responses"** and **"Repair demands"** as mandatory human review,
*"regardless of confidence score or user category authorization."*

Jake's CSV marks these "(To Be Automated)":

- 235 "Buyer's Inspection Response Due"
- 240 "Inspection Response Reminder"

And the library additionally carries 245 (Inspection Response Reminder), 250/255/257 (Inspection
Negotiated).

A *reminder that a response is due* is arguably not itself a response — but 250/255/257
"Inspection Negotiated" plainly is negotiation. **My reading:** 235/240/245 may auto-send as
`reminder_follow_up` **provided the body contains no response content, no repair language, and no
negotiation position** — enforced by a content check, not by trust. 250/255/257 are permanently
`agent_reviewed_draft`. Jake should confirm.

### 4.3 Auto-send authorization must gate the existing executor

Gates §7.1/§7.2 do not exist. Path A sends today with no user opt-in and no per-category
authorization. Bringing it into spec compliance means **existing behavior changes**: on upgrade, an
executor task whose category is unauthorized stops auto-sending and starts landing in the review
queue.

**Rollout decision:** ship with the seven welcome/order categories pre-authorized for tenants that
already have `Automated` tasks running, so nobody's live deals silently go quiet, and require
explicit opt-in for everything new. This is recorded as a migration data decision in Phase 6.

### 4.4 Naming: "Request Testimonials" vs "Request Referrals"

CSV rows 38–39 call tasks 460/470 "Request Testimonials". The library calls them "Request Referrals"
and the descriptions say *"request social media and online referrals"*. Because the AI executor's
playbook is **keyed by task name** (`ai_task_executor.py:145`, and see the standing note that
renaming a system template breaks its automation), a rename is not cosmetic. Phase 2 removes that
fragility by keying on `legacy_task_id`; until then, do not rename.

---

## 5. Section-by-section gap analysis

| Spec § | Requirement | Today | Gap | Phase |
| --- | --- | --- | --- | --- |
| §3 | Priority order: safety → verified facts → mandatory review → structure → tone → prefs → brevity | Implicit, unenforced | Encode as an ordered pipeline | 3 |
| §4.1 | 18 core inputs incl. brokerage, phone, saved signature, language pref, category authorizations, threshold | ~11 available; brokerage/phone exist on `users`; language pref, phrase lists, per-category auth absent | Add `profile_settings_json.email_style`; add tenant category auth | 4, 6, 9 |
| §4.2 | Content inputs incl. **exact completion method** | `tasks.completion_method` exists but is NULL for all system templates | Populate in the seed | 8 |
| §4.3 | Never invent; conflicts → review; attachments only when verified | Attachment honesty ✅; conflict detection ❌ | Add conflict detector | 3, 7 |
| §5 | 7 categories | Absent | New enum + persisted column | 3, 5 |
| §6 | 2 delivery modes | Absent | New enum + persisted column | 3, 5 |
| §6.1 | Agent voice + agent signature, Aime not named | ✅ (this is today's only behavior) | — | — |
| §6.2 | Aime voice + Aime signature on auto-send | Absent | Identity module | 4 |
| §7 | 15 hard gates | ~4 partial | `gate()` function, single call site | 3, 6 |
| §8 | 17 mandatory-review subjects | 1 of 17 (money, inbound only) | Detector applied to all 4 paths | 3 |
| §9 | Integer 0–100 confidence; never in body | Float 0–1; not in body ✅ | Boundary conversion | 5 |
| §10 | Recipient-specific tone (4 audience classes) | Single tenant tone setting | Audience-aware tone selection | 8 |
| §11 | Language / preferred / prohibited phrases | Absent | `email_style` prefs + application + prohibited-phrase filter | 9 |
| §12.1 | Street address, escalate on ambiguity | Street ✅ by accident; escalation ❌ | Ambiguity check across active deals | 8 |
| §12.2 | 8 subject patterns | Ad hoc | `subject_for(category, …)` | 8 |
| §12.3 | No unsupported urgency; no vague subjects | Unenforced | Validator rule | 3 |
| §12.4 | Preserve thread subject; new thread on material change | Threading ✅ (`_parent_message_id`); subject policy ❌ | Subject policy on reply path | 8 |
| §13.1 | Verified preferred/first name; never guess nickname/title/gender | `_greeting_names` uses first token; falls back to `"there"` | Replace fallback with a §17 marker | 7, 8 |
| §13.2 | Opener suppression matrix | Absent | Category-driven flag | 8 |
| §13.3 | One primary CTA; no system terminology | Unenforced | Validator rule | 3 |
| §13.4 | Exact stored completion method | Data missing | Seed + render | 8 |
| §13.5 | Shortest complete email; bullets for multiple items | Unenforced | Validator (advisory) | 8 |
| §14 | Thread/recipient handling; never add a recipient without review | Recipients from captured parties ✅; "never add" not asserted | Explicit assertion + audit | 3 |
| §15 | Signature rules both modes | §15.1 ✅ / §15.2 ❌ | Identity module | 4 |
| §16.1–16.7 | 7 category structures | 12 ad-hoc templates | Rewrite against structures | 8 |
| §17 | Markers + send block | Absent | Markers + 409 + disabled UI | 7 |
| §18 | Combining requests | Absent | Grouper | 8 |
| §19.1 | 5-field JSON | 5 different fields | New contract | 5 |
| §19.2 | Clean preview; exact match | ✅ | Add regression test | 5 |
| §20 | 9 canonical examples | — | Golden-file fixtures | 10 |
| §21 | Final validation checklist | Absent | `validate()` | 3 |
| §22 | 17 acceptance tests | Absent | Test suite | 10 |

---

## 6. Attachment spreadsheet reconciliation

### 6.1 CSV → task library

Library source of truth: `velvet-elves-backend/supabase/migrations/202603111730_seed_task_templates.sql`
(60 system templates; `automation_level` counts: 5 `Automated`, 35 `ToBeAutomated`, 20 `Manual`)
plus `20260917090000_automated_task_levels.sql` (promotes 8 and 80 to `Automated`).

| CSV ID | CSV name | Library name | Verdict |
| --- | --- | --- | --- |
| 10 | Buyer Welcome | Buyer Welcome | ✅ match |
| 20 | Seller Welcome | Seller Welcome | ✅ |
| 30 | Co-op Agent Welcome | Co-op Agent Welcome | ✅ |
| 60 | Loan Officer Welcome | Loan Officer Welcome | ✅ |
| 70 | Order Title | Order Title | ✅ |
| 90 / 95 / 100 | Request HOA Docs | Request HOA Docs ×3 | ✅ |
| 130 / 135 / 140 | Request Utility Info | Request Utility Info ×3 | ✅ |
| 180 | Confirm Home Warranty Order | Confirm Home Warranty Order | ✅ |
| 200 | Insurance Reminder | Insurance Reminder | ✅ |
| **235** | **Buyer's Inspection Response Due** | **— no such ID —** | ❌ **Does not exist.** Nearest: 230 Inspection Completed, 240/245 Inspection Response Reminder |
| 240 | Inspection Response Reminder | Inspection Response Reminder | ✅ (twin **245** absent from CSV) |
| 260 | Appraisal Ordered | Appraisal Ordered | ✅ (twin **265** absent from CSV) — but see D3 |
| 270 | Appraisal Completed | Appraisal Completed | ✅ — phone task (D3) |
| 280 | Buyer Documentation | Buyer Documentation | ✅ |
| 290 | Title Work Completed | Title Work Completed | ✅ |
| 300 / 305 / 310 | Deliver Title | Deliver Title ×3 | ✅ |
| 320 | Deliver Title to the Loan Officer | Deliver Title to the Loan Officer | ✅ |
| 330 | Clear to Close | Clear to Close | ✅ — phone task (D3) |
| 340 | Closing Disclosure Delivered | Closing Disclosure Delivered | ✅ — phone task (D3) |
| **453** | **Schedule Pick Up of Sign and Lockbox** | **— no such ID —** | ❌ **Does not exist** anywhere in the library |
| **455** | **Change MLS Listing Status to Sold** | **— no such ID —** | ❌ **Does not exist** anywhere in the library |
| **460** | Request Testimonials | **Request Referrals** | ⚠️ ID matches, **name differs** |
| **470** | Request Testimonials | **Request Referrals** | ⚠️ ID matches, **name differs** |
| 480 | Exemptions and Thank You | Exemptions and Thank You | ✅ — physical card, not email |
| 490 | Thank You | Thank You | ✅ — physical card, not email |

### 6.2 Tasks in the library that Jake's CSV does not cover — **32 rows**

This is the list Jake asked for. Highest-priority items first.

**Already `Automated` and shipping attachments today — must be specified:**

| ID | Name | Why it matters |
| --- | --- | --- |
| **80** | **Confirm Title Order** | Promoted to `Automated`; already attaches PA + counters + tax sheet + SD. No CSV row. |
| **8** | **Review Documentation** | `Automated`; attaches unsigned documents to a signature-request draft. No CSV row. |

**Delivery tasks that obviously need attachments but have no row:**

| ID | Name | Implied attachment |
| --- | --- | --- |
| 110 / 115 / 120 | Deliver HOA Docs ×3 | HOA documents. **Each row is two emails**: a thank-you to whoever supplied them, then the docs to the buyer. |
| 150 / 155 / 160 | Deliver Utility Info ×3 | Utility information. Same two-email shape. |

The two-email shape is important: today one task produces one email, so these rows need either a
second template or an explicit decision to drop the thank-you.

**Remaining uncovered tasks:**

| ID | Name | Note |
| --- | --- | --- |
| 5 | Contract Acceptance Date | Milestone anchor — no email |
| 50 | Pending Reminder | Self-reminder to the agent |
| 170 | Order Home Warranty | "Order the home warranty and **send the invoice to the title company**" — needs the invoice |
| 210 / 215 / 220 | Inspection Scheduled ×3 | Phone-first, then a follow-up email |
| 230 | Inspection Completed | Phone task; likely needs the inspection report if it becomes email |
| 245 | Inspection Response Reminder | Twin of 240; `ToBeAutomated` |
| 250 / 255 / 257 | Inspection Negotiated ×3 | **§8 mandatory review** |
| 265 | Appraisal Ordered | Cash-deal twin of 260; **`target` is NULL** in the library |
| 350 | Schedule Closing | "Notify all parties via email of the walkthrough and closing times" |
| 370 / 375 / 380 | Closing Gift ×3 | Physical gift prep — no email |
| 420 | Buyer Closing Information | Closing + walkthrough details |
| 430 | Seller Closing Information | Closing + walkthrough details |
| 440 | **Seller's Agent Closing Information** | Closing details to the co-op agent |
| 450 | **Buyer's Agent Closing Information** | Closing details to the co-op agent |
| 500 / 505 / 510 | Internal Thank You ×3 | "Feedback & rating email to agents" — internal |
| 1000 | Closing Date | Milestone anchor — no email |

Several of these already state their own attachment rule in the library description — task 8 says
"Attach any unsigned documents to the email", task 80 lists the same four documents as task 70, and
task 170 names the invoice. Those can be pre-filled and merely confirmed rather than authored.

### 6.3 Dependency column cross-check

The CSV's "Task Dependency" column agrees with the library's `dep_task_id` on every row I spot-checked
(10→5, 130→1000, 260→5, 270→1000, 290→70/80, 300→290, 460→1000, 480→1000). No action beyond an
automated assertion in Phase 0.

### 6.4 Canonical document kinds implied by the CSV

Jake's shorthand → the canonical kind this plan will define:

| CSV shorthand | Canonical kind | `DocumentType` | Parser detected type |
| --- | --- | --- | --- |
| PA / Purchase Agreement | `purchase_agreement` | `purchase_agreement` | `purchase_agreement` |
| Counters | `counter_offer` | `counter_offer` | `counter_offer` |
| Addendums | `addendum` | `addendum` | `addendum` |
| Amendments | `amendment` | `amendment` | `amendment` |
| LBP | `lead_paint_disclosure` | `lead_paint_disclosure` | `lead_paint_disclosure` |
| SD / Sellers Disclosure | `sellers_disclosure` | `sellers_disclosure` | — |
| BLC or Tax Sheet | `blc_tax_sheet` | `blc_tax_sheet` | — (resolver family `ownership_record`) |
| Copy of EM | `earnest_money` | `earnest_money` | `emd_receipt` |
| Title work | `title_work` | `title_work`, `title_commitment` | `title_commitment` |
| HOA docs | `hoa_docs` | `hoa_docs` | `hoa_package` |
| Utility info | `utility_info` | `utility_info` | `utility_confirmation` |
| Home warranty | `home_warranty` | `home_warranty` | `home_warranty` |
| Inspection report | `inspection_report` | `inspection_report` | `inspection_report` |
| Closing disclosure | `closing_disclosure` | `closing_disclosure` | `closing_disclosure` |

**"Full purchase/sale package"** (rows 2–4) resolves to the ordered set:
`purchase_agreement, counter_offer, addendum, amendment, lead_paint_disclosure, sellers_disclosure, earnest_money`.

---

## 7. Target architecture

Two new modules and one rule table. Everything else is wiring.

```
                      ┌──────────────────────────────────────────┐
                      │  agent_email_policy.py   (the guideline  │
                      │  as code — spec §3,5,6,7,8,9,12,13,15,   │
                      │  17,18,21)                               │
                      │                                          │
                      │  EmailCategory / DeliveryMode enums      │
                      │  requires_mandatory_review(...)          │
                      │  subject_for(category, ...)              │
                      │  signature_block(mode, agent, ...)       │
                      │  gate(candidate) -> GateResult           │
                      │  validate(candidate) -> [Violation]      │
                      └───────────────┬──────────────────────────┘
                                      │  every path calls it, once
      ┌───────────────┬───────────────┼───────────────┬────────────────┐
      │               │               │               │                │
 ai_task_executor  task_email_    ai_email_engine  auto-draft       agent
   (auto-send)      planner       (LLM drafts)      sweep          actions
      │               │               │               │                │
      └───────────────┴───────────────┼───────────────┴────────────────┘
                                      ▼
                          send_ai_draft (unchanged, one send path)

                      ┌──────────────────────────────────────────┐
                      │  document_kinds.py  (one taxonomy)       │
                      │  resolve_kind(document) -> kind | None   │
                      │  select(documents, attach, exclude)      │
                      └──────────────────────────────────────────┘
                                      ▲
                      task_templates.attachment_rule_json  ──┘
                      tasks.attachment_rule_json  (copied at generation)
```

**Design rules:**

1. **One policy module, one call site per path.** The guideline must not be reimplemented four times.
2. **Attachment rules are data, not code.** `_EMAIL_PLAYBOOK`'s `doc_kinds` moves to the task
   template table, keyed by `legacy_task_id` (stable) rather than task name (fragile).
3. **One document taxonomy.** `document_kinds.py` becomes the single resolver; `_DOC_MATCHERS` is deleted.
4. **The model never picks recipients or attachments.** It receives them as verified context and
   returns the five fields only.
5. **Gates are hard.** `gate()` returns `(allowed, failed_gate, reason)`. No caller may pass a
   confidence score that overrides it (spec §7: "No confidence score can override a failed hard gate").

---

## 8. Phased implementation

### Phase 0 — Reconcile the spreadsheet (no code) — **BLOCKING for Phases 2 & 8**

**Deliverables**
1. A reply document to Jake containing: §6.1's mismatch table, §6.2's 32 uncovered tasks, and the
   D3 phone-task question.
2. `Tasks_Attachments_RECONCILED.csv` — Jake's sheet with `legacy_task_id` validated against the
   library, kinds normalized to §6.4's canonical vocabulary, and one row per library task.
3. A CI assertion (`app/tests/test_attachment_rule_coverage.py`) that fails if a system task template
   exists with no attachment rule and no explicit `"no_email"` marker — so the sheet can never drift
   out of sync with the library again.

**Questions for Jake** (also listed in §11):
- Task 235 — new task, or did you mean 230/240/245?
- Tasks 453 and 455 — new tasks to add to the library?
- 460/470 — rename "Request Referrals" → "Request Testimonials", or keep the library name?
- 260/270/330/340 are **phone** tasks in the library. Convert to email, or keep the call and add the
  email as a follow-up?
- Rules for the 32 uncovered tasks, especially 80, 8, 110/115/120, 150/155/160.

**Exit criteria:** reconciled CSV signed off by Jake.

---

### Phase 1 — Canonical document-kind resolver — *unblocked, start now*

**New:** `app/services/document_kinds.py`

```python
@dataclass(frozen=True)
class KindSpec:
    kind: str
    doc_types: tuple[str, ...]        # DocumentType enum values
    detected_types: tuple[str, ...]   # packet-parser vocabulary
    name_keywords: tuple[str, ...]
    name_antikeywords: tuple[str, ...]  # ← fixes D1
    priority: int                      # most specific wins

def resolve_kind(document) -> str | None: ...
def select(documents, *, attach: Sequence[str], exclude: Sequence[str]) -> list: ...
```

**Rules that fix D1/D2:**

- Resolution is **single-valued**: each document resolves to exactly **one** kind, by priority
  (`lead_paint_disclosure` and `closing_disclosure` outrank `sellers_disclosure`;
  `counter_offer_addendum` outranks `counter_offer`). A document can therefore never be attached twice.
- `sellers_disclosure.name_antikeywords = ("lead", "paint", "lbp", "closing")`.
- `counter_offer.name_antikeywords = ("addendum", "amendment")`.
- `blc_tax_sheet.doc_types = ("blc_tax_sheet",)` with resolver family `ownership_record` accepted as
  a secondary signal — **fixes the enum-value bug in D2**.
- `doc_type` (explicit classification) always beats a filename keyword. Keywords are a last resort.
- `exclude` is applied **after** resolution and always wins over `attach`.

**Delete:** `_DOC_MATCHERS` and `_match_documents` from `ai_task_executor.py:129-136, 1017-1034`;
re-point `ai_task_executor.py:448`, `:451` and `task_email_planner.py:452` at `document_kinds.select`.

**Tests:** `app/tests/test_document_kinds.py` — one case per row of §6.4 plus explicit regressions
for "Lead-Based Paint Disclosure.pdf", "Closing Disclosure.pdf", "Counter Offer Addendum.pdf", and a
correctly-typed `blc_tax_sheet` with an unhelpful filename.

**Acceptance:** Order Title (70) on a deal holding PA + counter + LBP + CD + tax sheet + addendum
attaches **exactly** PA + counter + tax sheet + SD, and nothing else.

---

### Phase 2 — Attachment rules as data — *depends on Phase 0*

**Migration** `20260925090000_task_attachment_rules.sql`:

```sql
ALTER TABLE public.task_templates ADD COLUMN attachment_rule_json JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE public.tasks          ADD COLUMN attachment_rule_json JSONB NOT NULL DEFAULT '{}'::jsonb;
```

Rule shape:

```json
{
  "attach":  ["purchase_agreement", "counter_offer", "blc_tax_sheet", "earnest_money"],
  "exclude": ["addendum", "amendment"],
  "required": ["purchase_agreement"],
  "skip_if_present": ["hoa_docs"],
  "email_category": "document_information_request",
  "auto_send_eligible": true
}
```

- `attach` / `exclude` → R27 / R28.
- `required` preserves today's "don't promise a contract you don't have" block
  (`ai_task_executor.py:449-463`).
- `skip_if_present` → **R31**: HOA/Utility tasks check the document center first. When present, the
  task **auto-completes with a note** ("HOA documents are already on file — no request sent") rather
  than emailing. No email, no false chase.
- `email_category` seeds the §5 classification per task.
- `auto_send_eligible: false` hard-blocks §8 tasks (250/255/257) from ever auto-sending.

**Seeded** from `Tasks_Attachments_RECONCILED.csv`, keyed on `legacy_task_id` — **not on name**,
removing the rename fragility called out in §4.4.

**Generation:** `app/services/task_generation_service.py` copies `attachment_rule_json` onto each
task row, exactly as it already copies `target` / `cc_targets`.

**Consumers:** `ai_task_executor._execute_email_task` and `task_email_planner.build_task_email_plan`
read the rule off the **task row**, falling back to `_EMAIL_PLAYBOOK` only for the template_key/roles
they still own.

**Acceptance:** Loan Officer Welcome on a deal with an amendment on file attaches PA + counters +
BLC + EM and **omits** the amendment; a Request HOA Docs task on a deal that already has HOA docs
completes without sending.

---

### Phase 3 — The guideline as code — *unblocked, start now*

**New:** `app/services/agent_email_policy.py`.

```python
class EmailCategory(str, Enum):
    DOCUMENT_INFORMATION_REQUEST = "document_information_request"
    REMINDER_FOLLOW_UP           = "reminder_follow_up"
    SCHEDULING_REQUEST           = "scheduling_request"
    SCHEDULING_CONFIRMATION      = "scheduling_confirmation"
    TRANSACTION_STATUS_UPDATE    = "transaction_status_update"
    INTRODUCTION                 = "introduction"
    PROBLEM_NOTICE_ESCALATION    = "problem_notice_escalation"

class DeliveryMode(str, Enum):
    AGENT_REVIEWED_DRAFT = "agent_reviewed_draft"
    AIME_AUTO_SEND       = "aime_auto_send"
```

- `MANDATORY_REVIEW_TOPICS` — all 17 of §8, each with a matcher (keyword sets + regex for wire/routing
  numbers, SSN patterns, "terminate/cancel/default/breach", repair-demand and negotiation phrasing).
  `requires_mandatory_review(subject, body, category) -> str | None` returns the triggering topic.
- `subject_for(category, *, item=None, event=None, milestone=None, parties=None, issue=None, address)`
  — the eight §12.2 patterns, single source.
- `signature_block(mode, agent, topic, address)` — §15.1 / §15.2.
- `GATES: tuple[Gate, ...]` — all 15 of §7 as named, individually testable predicates.
  `gate(candidate) -> GateResult(allowed, failed_gate, reason)`.
  `PROBLEM_NOTICE_ESCALATION` is hard-failed at gate 4 as §16.7 requires.
- `validate(candidate) -> list[Violation]` — the §21 checklist, split into `blocking` and `advisory`.
  Blocking violations force `agent_reviewed_draft`; advisory ones become assumptions in the review UI.

**Reuse, do not duplicate:** `_FORBIDDEN_PATTERNS` (`ai_email_engine.py:154-159`) folds into
`MANDATORY_REVIEW_TOPICS`; `FORBIDDEN_ACTION_TYPES` in `agent_policy.py:123-134` already forbids
`send_email` / `auto_send_email` as agent actions and stays as is — the two modules are complementary
(action policy vs. email policy) and should cross-reference each other in their docstrings.

**Tests:** one per gate, one per mandatory-review topic, one per subject pattern.

---

### Phase 4 — Identity and signature — *depends on §4.1 decision*

- `assistant_identity` under `tenants.settings_json.ai_email`, default `"Aime"`, with a
  `use_assistant_identity` boolean so the §4.1 decision is reversible without a deploy.
- Extend `_owner_signature` (`ai_email_engine.py:1720-1748`) into
  `resolve_signature(mode, owner) -> str`:
  - `agent_reviewed_draft` → today's behavior, unchanged (§15.1).
  - `aime_auto_send` → the 5-line Aime block (§15.2), built from `users.full_name`,
    `users.company_name`, `users.phone`, `users.email` (all Fernet-decrypted at the repository edge —
    reuse `_safe_decrypt`).
- **Gate 14a:** any missing signature field (name, brokerage, phone, email) → auto-send blocked (R14).
- `_apply_tone_rules` (`ai_email_engine.py:1785-1823`) takes the resolved signature and stops
  appending a sign-off ahead of an Aime block.
- **Guardrail test:** no outbound body or signature may contain `AI`, `artificial intelligence`,
  `bot`, `automated`, or `Velvet Elves`, with `task_pending_reminder` explicitly allowlisted
  (account-holder-only).

---

### Phase 5 — Persist the contract — *unblocked*

**Migration** `20260925091000_email_category_delivery_mode.sql`:

```sql
ALTER TABLE public.communication_logs
  ADD COLUMN email_category TEXT,
  ADD COLUMN delivery_mode  TEXT;
CREATE INDEX IF NOT EXISTS idx_comm_logs_category
  ON public.communication_logs (tenant_id, email_category);
```

- Add the two fields to `CommunicationLog` (`app/models/communication_log.py`),
  `CommunicationLogRepository`, and `CommunicationLogResponse`
  (`app/schemas/communication_log.py:33`).
- Rewrite the two LLM prompts (`_compose_from_intent_ai` `ai_email_engine.py:740-756`;
  `_draft_factual_from_context_ai` `ai_email_engine.py:1332-1352`) to the §19.1 five-field contract.
  `source_data` and `assumptions` move to a **second, separate** response object so §19.1's "exactly
  five top-level fields" holds literally while grounding survives — grounding is non-negotiable and
  §4.3 requires it.
- Boundary conversion: `confidence_score` (0–100 int) ↔ `ai_confidence` (0.0–1.0 float). One helper,
  one place, round-trip tested.
- Frontend: surface category + mode as chips **outside** the preview in `AiEmailReviewPage.tsx` and
  `TaskEmailFlow.tsx` (§19.2 permits exactly this and forbids it inside the body).
- **Regression test for R26:** the persisted `subject`/`body` are byte-identical to what the preview
  renders.

---

### Phase 6 — Auto-send gates and per-category authorization — *depends on 3, 4*

**Settings model.** Extend `TenantAiEmailSettings` (`app/api/v1/ai_emails.py:196-205`):

```python
class TenantAiEmailSettings(BaseModel):
    tone: str = DEFAULT_TONE
    escalation_hours: int = Field(default=36, ge=1, le=168)
    auto_send_threshold: float = Field(default=0.90, ge=0.0, le=1.0)
    auto_send_enabled: bool = False                       # §7.1
    auto_send_categories: list[str] = Field(default_factory=list)  # §7.2
```

**Wiring.** `ai_task_executor._execute_email_task` calls `agent_email_policy.gate()` **before**
`compose_outbound`. On a failed gate the task does not send — it drafts and surfaces with the
existing `_surface_task` mechanism, reusing the established `ai_needs_user` codes plus new
`auto_send_not_authorized` and `mandatory_review_required` (both **retryable**, since authorization
can be granted later — add them to `_RETRYABLE_CODES`, `ai_task_executor.py:201-221`).

**Relationship to automation posture.** `automation_posture_service.py` already models manual /
assisted / autopilot. Category authorization is **narrower** and composes with it:
`may_auto_send = posture != manual AND auto_send_enabled AND category ∈ auto_send_categories AND all 15 gates pass`.
Posture stays the coarse control; §7 is the fine one. They must not be merged.

**Frontend.** Extend `EmailAutomationSection.tsx` with a 7-row category authorization list
(label + toggle + one-line consequence), placed under the existing threshold slider. Copy must be
honest: the current help text *"Nothing sends without a person"* becomes false for authorized
categories and **must be rewritten**.

**Migration data decision (§4.3):** for tenants with existing `Automated` task rows, seed
`auto_send_enabled = true` and `auto_send_categories = ["document_information_request",
"transaction_status_update", "introduction"]` so today's welcome/order emails keep flowing. All other
tenants start closed.

---

### Phase 7 — Missing-information markers and send blocking — *depends on 3*

- `agent_email_policy.MARKER_RE = r"\*\*\[(MISSING|CONFLICT): [^\]]+\]\*\*"`.
- Drafting paths emit markers instead of guessing. The immediate wins:
  `_greeting_names` / `_first_name` currently fall back to `"there"`
  (`task_email_planner.py:186-197`) — under §13.1 an unverified recipient name becomes
  `**[MISSING: VERIFIED RECIPIENT NAME]**` on a review draft.
- **Backend block (R19):** `send_ai_draft` (`ai_email_delivery.py:83`) raises a new
  `DraftHasBlockingMarkers` when the body matches `MARKER_RE`; the `/ai-emails` approve and
  edit-and-send endpoints map it to **409** with the unresolved marker list. This is the single
  chokepoint — every path already funnels through it, so no caller can bypass the rule.
- **Frontend:** `AiEmailReviewPage.tsx` and `TaskEmailFlow.tsx` highlight markers, disable Send, and
  explain what to fill in.
- **Conflict detection (R20):** when two verified sources disagree on a date that the body cites,
  emit `**[CONFLICT: CLOSING DATE DIFFERS BETWEEN SOURCES]**` and block. Sources: the transaction
  record vs. the controlling-document chain already resolved in `contract_resolution.py`.

---

### Phase 8 — Templates and structure — *depends on 0, 3*

- **Subjects.** Re-derive all 12 templates in `email_template_library.py:22-234` through
  `subject_for()`. Example: `task_order_title` "Title order: {{property_address}}" →
  `"Title Order Needed – {{street_address}}"`.
- **New tokens** in `build_substitutions` (`email_template_library.py:278-308`):
  `street_address`, `full_address`, `completion_instructions`, `key_dates`, `next_step`,
  `responsible_party`.
- **§12.1 ambiguity escalation:** `street_address` resolves to the full address when another **active**
  deal in the tenant shares the same street line. One indexed query, cached per compose.
- **§13.4 completion method:** add `completion_method` to the seed migration's column list — it is in
  the `Task` model (`app/models/task.py:29`) but absent from
  `202603111730_seed_task_templates.sql`'s INSERT, so it is NULL everywhere. Populate per task from
  the reconciled CSV, render it as the completion-instructions line, and emit
  `**[MISSING: COMPLETION METHOD]**` when a task that needs one has none.
- **§13.2 openers:** category-driven suppression flag; opener text is only emitted when the actual
  weekday is known.
- **§16.5 no-CTA:** validator rejects an imperative sentence in a `transaction_status_update`.
- **§10 audience tone:** map party role → one of the four §10 classes; select phrasing accordingly.
- **§18 combining:** group same-recipient / same-property / same-method requests due on the same day
  into one "Items Needed – {{street_address}}" email with bullets. Applied in the auto-draft sweep
  and the executor, never across differing owners or methods.
- **Templates to add** for tasks currently unserved: `task_deliver_title`, `task_deliver_hoa_docs`,
  `task_deliver_utility_info`, `task_request_hoa_docs`, `task_request_utility_info`,
  `task_appraisal_ordered`, `task_clear_to_close`, `task_request_referrals`.

---

### Phase 9 — Agent language and style preferences — *depends on 3*

- `users.profile_settings_json.email_style`:
  `{ language, preferred_phrases[], prohibited_phrases[], allow_friendly_opener, warmth }`.
- Applied **after** structure and facts; a prohibited phrase is filtered post-generation and its
  removal is logged as an assumption (§3: style never overrides structure or facts).
- UI: a "Writing style" card on the AI & Automation surface, beside the existing signature field.

---

### Phase 10 — Tests

**Unit**
- `test_document_kinds.py` — §6.4 matrix + D1 regressions.
- `test_agent_email_policy.py` — 15 gates, 17 mandatory-review topics, 8 subject patterns, both signatures.
- `test_attachment_rules.py` — every reconciled CSV row: expected attached set and expected omitted set.
- `test_attachment_rule_coverage.py` — every system template has a rule or `"no_email"` (drift guard).

**Acceptance — spec §22, all 17 rows verbatim**

| # | Scenario | Required result |
| --- | --- | --- |
| 1 | Authorized routine request, verified, above threshold | auto-send permitted |
| 2 | Correct email below threshold | review draft |
| 3 | Category not authorized | review draft |
| 4 | Missing recipient name | review draft **with marker** |
| 5 | Missing opener context | opener omitted, **no placeholder** |
| 6 | Conflicting closing dates | blocked + conflict marker |
| 7 | Confusable property | full address; review if still ambiguous |
| 8 | New recipient needed | review required before adding |
| 9 | Wire instructions | review regardless of confidence |
| 10 | Inspection response language | review regardless of confidence |
| 11 | Problem notice | review regardless of confidence |
| 12 | Several related docs, one person, one method | one email with bullets |
| 13 | Different responsible parties | separate emails |
| 14 | Proposed scheduling event | never called "confirmed" |
| 15 | Status update, no action | no CTA |
| 16 | Introduction with many dates | major dates only |
| 17 | Unknown completion method | review draft with marker |

**Golden files** — spec §20's nine canonical examples become fixtures asserting byte-level output.

**E2E** — a live browser round on `localhost:5173` against a fresh uvicorn on `:8001`, covering:
Buyer Welcome attaches the full package; Loan Officer Welcome omits the amendment; Order Title omits
the LBP; a Request HOA Docs task with docs already on file completes without sending; a marker-bearing
draft cannot be sent from either surface.

---

## 9. Sequencing and dependencies

```
Phase 0 (Jake) ──┬─────────────► Phase 2 ──┐
                 └───────────────────────► Phase 8
Phase 1 ─────────────────────────► Phase 2 ─┴──► Phase 10
Phase 3 ──┬──► Phase 6 ──────────────────────────► Phase 10
          ├──► Phase 7
          └──► Phase 9
Phase 4 (needs §4.1 decision) ──► Phase 6
Phase 5 ─────────────────────────────────────────► Phase 10
```

**Start immediately, no blockers:** Phase 1, Phase 3, Phase 5.
**Blocked on Jake:** Phase 0 (the reconciliation questions), Phase 4 (the Aime decision),
Phase 2 and Phase 8 (downstream of Phase 0).

---

## 10. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| **Phase 6 changes live sending behavior.** Tenants running `Automated` tasks today could silently stop sending. | High | Migration seeds authorization for existing automated tenants (§4.3). Ship with an admin banner naming what changed. |
| **Phase 4 changes what real clients see** on live production mail. | High | Gated on Jake's explicit sign-off; `use_assistant_identity` allows instant reversal without a deploy. |
| **Phase 1 changes attachment sets on live deals.** Fixing the over-attach means emails that used to carry the LBP no longer will — which is correct, but visible. | Medium | Ship Phase 1 with a dry-run report over recent sent drafts showing before/after attachment sets; review before enabling. |
| **The CSV never converges.** 32 tasks lack rules and 3 IDs do not exist. | Medium | The Phase 0 coverage test fails the build on any template without a rule, so gaps are loud, not silent. Tasks without a rule attach **nothing** and never auto-send — the safe default. |
| **Spec §8 vs. Jake's "(To Be Automated)" labels** (§4.2). | Medium | `auto_send_eligible: false` in the rule data; policy hard-fails regardless of the label. |
| **Guideline drifts from code.** | Medium | `agent_email_policy.py` cites its spec section in every docstring; `test_agent_email_policy.py` names the section it enforces. Reviewing the guideline means reviewing the tests. |
| **Prompt regression.** Rewriting two live prompts (Phase 5) can degrade drafting. | Medium | Golden-file fixtures from §20 run against both configured providers before merge. |

---

## 11. Open items for Jake

**Blocking Phase 0 → 2 → 8**

1. **Task 235 "Buyer's Inspection Response Due"** does not exist in the task library. Is this a new
   task, or did you mean 230 (Inspection Completed), 240, or 245 (Inspection Response Reminder)?
2. **Tasks 453 "Schedule Pick Up of Sign and Lockbox"** and **455 "Change MLS Listing Status to Sold"**
   do not exist either. Should I add them to the library? If so I need target, CC, dependency, and
   float days for each.
3. **Tasks 460 / 470** are named **"Request Referrals"** in the library, not "Request Testimonials".
   Rename, or keep the library name? (Renaming currently breaks a task's automation — I am fixing
   that in Phase 2, but I need to know which name is correct.)
4. **32 library tasks have no row in the spreadsheet** (full list in §6.2). The urgent ones are
   **80 Confirm Title Order** and **8 Review Documentation** — both already automated and already
   sending attachments — plus **110/115/120 Deliver HOA Docs** and **150/155/160 Deliver Utility
   Info**, which must attach the documents they deliver.
5. **Four tasks you marked for attachments are phone tasks in the library:** 260 and 270 (Appraisal
   Ordered / Completed), 330 (Clear to Close), 340 (Closing Disclosure Delivered) all say "Call the
   loan officer…". Do you want these converted to email, or should the call stay and the email be a
   follow-up?

**Blocking Phase 4**

6. **§15.2 changes who signs auto-sent mail.** Today those emails are signed as the agent. Under the
   guideline they will be signed "Aime — Assistant to {agent}". This is visible to buyers, sellers,
   lenders, and title reps on live deals. Confirm you want that change.

**Blocking Phase 6**

7. **§8 lists "Inspection responses" and "Repair demands" as always-human-review**, but the
   spreadsheet marks 235/240 "(To Be Automated)". My reading: a *reminder that a response is due* can
   auto-send as long as it contains no response, repair, or negotiation content; tasks 250/255/257
   "Inspection Negotiated" never auto-send. Confirm.

**Non-blocking**

8. §4.2 requires an **exact completion method** per task ("reply to this email", "use this upload
   link", "Reply All"). That field exists in the schema but is empty for every system task. Can you
   add a completion-method column to the reconciled spreadsheet?
9. §11 supports **preferred and prohibited phrases** per agent. Should these be per-agent (each agent
   sets their own) or per-brokerage (set once by the admin)?

---

## 12. What this plan deliberately does not do

- **Does not let the model choose recipients or attachments.** Both stay deterministic (§7 gates 6
  and 11 are only checkable if the app owns them).
- **Does not touch timing.** Spec §2 assigns follow-up cadence to the task engine; the dependency
  engine and deadline rules are untouched.
- **Does not add a send path.** `send_ai_draft` remains the only one, so §17's block and §7's gates
  cannot be circumvented.
- **Does not merge category authorization into automation posture.** They are different-grained
  controls and collapsing them would make §7.2 unexpressible.
- **Does not rewrite the review UI.** Option 3 is already the shipped shape; Phases 5 and 7 add chips
  and marker highlighting to it, nothing more.
