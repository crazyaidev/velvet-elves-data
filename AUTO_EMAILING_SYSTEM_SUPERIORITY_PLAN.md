# Auto-Emailing System Superiority Plan

**Created:** 2026-06-08
**Author:** Jan (sole developer)
**Status:** Plan only. No source code is changed by this document.
**Goal:** Review the auto-emailing feature as actually implemented, compare it head-to-head with ListedKit's email automation, and define a robust plan for an auto-emailing system that is a strict superset of ListedKit's, validatable end-to-end through the frontend UI by non-developer real-estate testers.

This plan is written to fix the failure mode of earlier drafts: it is grounded in the real requirements, the real system design, and the **current frontend and backend source**, not in the milestone narrative alone. Every claim about current behavior below is tied to a concrete file so the plan does not drift from the code.

---

## 0. How to read this document

> **Post-write source re-verification (2026-06-08).** This plan was re-checked against the live source after it was written. The central claims hold: `communication_logs.attachment_ids` exists (`20260305_phase1_schema.sql`) and `CommunicationLogRepository.create` accepts it, yet `_send_draft` (`ai_emails.py`) builds `OutboundEmail` with no attachments while the document-request drafter promises one (the §4.1 break is real); the threading columns (`message_id_header`, `in_reply_to_header`, `thread_key`) exist and the vendor send path (`vendor_communications.py`) stamps them while the AI reply send sets `in_reply_to=None` (the §4.7 gap is real); `VendorTemplateService` and `vendor_communications.py` exist (the reuse in Pillars B/C is valid); `useAiEmailSettings`/`useUpdateAiEmailSettings` are defined but imported nowhere (the §4.5 gap is real); and `send_daily_summaries` inserts `pending_review` rows with no provider send and no scheduler (the §4.3 gap is real). Two wording overstatements found in the first draft were corrected in place and are marked `[Corrected 2026-06-08]`: the scheduled-send primitive does **not** already exist (§2.6), and the greeting claim needed path-level precision (§4.4).

- Section 1 to 4 establish the truth: what is built, what is broken, and exactly where in the code.
- Section 5 is the ListedKit comparison, scoped to auto-emailing only (not the whole platform; the platform-level comparison already exists in `LISTEDKIT_COMPETITIVE_ANALYSIS_AND_FEATURE_IMPROVEMENT_PLAN.md`).
- Section 6 onward is the build plan: product thesis, UI principles, the four pillars, backend, frontend, mouse-first walkthroughs, non-developer test scripts, governance, metrics, rollout, risks, and open questions.

Sources consulted for this plan:

- Requirements: `requirements.txt` (4.8 Notifications & Reminders, 5.3 Document Emailing, 6.1 to 6.8 Communication Engine, 7.1 Email APIs, 8 AI & Automation).
- Architecture: `SYSTEM_DESIGN.md`, `milestones.txt`.
- Prior plans: `MILESTONE_4_2_AI_EMAIL_WORKFLOW.md`, `MILESTONE_4_3_IMPLEMENTATION_PLAN.md`, `MILESTONE_4_1_EMAIL_INTEGRATION_CONFIGURATION_GUIDE.md`, `LISTEDKIT_COMPETITIVE_ANALYSIS_AND_FEATURE_IMPROVEMENT_PLAN.md`, `STYLE_GUIDE.md`, `FRONTEND_UI_WORKFLOW_LOGIC.md`.
- Backend source: `app/services/ai_email_engine.py`, `app/api/v1/ai_emails.py`, `app/services/email/inbound_dispatch.py`, `app/services/email/base.py`, `app/services/email/{gmail,outlook,icloud}_provider.py`, `app/services/email/factory.py`, `app/services/task_notification_service.py`, `app/services/email_service.py`, `app/services/vendor_proposal_service.py`.
- Frontend source: `src/pages/AiEmailReviewPage.tsx`, `src/hooks/useAiEmails.ts`, `src/pages/admin/AdminAIGovernancePage.tsx`, `src/utils/constants.ts`.
- ListedKit public pages (June 2026): the feature pages cited inline in Section 5.

---

## 1. Executive Summary

The auto-emailing feature that exists today (Milestone 4.2, extended by 4.3 for vendors) is a **well-built but one-directional** system. It does exactly one job: when an email comes in, it classifies the message, drafts a grounded reply, attaches a confidence score and a list of assumptions, and routes the draft to a human review queue (`/ai-emails`) where the file owner approves, edits, regenerates, or discards it. The send always goes out through the user's own connected Gmail, Outlook, or iCloud account. The architecture is clean, the safeguards are real, and the audit trail is complete.

It is not yet the full feature the requirements describe, and it is behind ListedKit on the parts of email automation that real-estate users feel most:

1. **It only reacts to inbound mail.** It cannot draft an email on demand ("send the buyer the timeline"), and it cannot send a scheduled deadline reminder. Those are two of ListedKit's three headline email workflows, and both are explicitly out of scope in 4.2 (`MILESTONE_4_2_AI_EMAIL_WORKFLOW.md` Section 15).
2. **A real end-to-end break exists in the document-request path.** The drafter writes "Attached is the {document}" with 0.93 confidence, but the send path never attaches anything. A tester who approves that draft sends a client an email that says "Attached is the inspection report" with no attachment. This is precisely the kind of silent workflow break that has burned past testing.
3. **The reminder and daily-summary engine is built but not wired.** `task_notification_service.py` computes day-before, due-today, overdue, upcoming, and daily-digest payloads, but nothing schedules it, nothing actually sends it (rows are inserted with status `pending_review` and never delivered), and no UI surfaces or configures it. Requirements 4.8 and 6.6 are therefore unmet in the live flow.
4. **There is no UI to configure the automation.** The tenant settings API (`PUT /ai-emails/settings`) exists, and the hooks `useAiEmailSettings` / `useUpdateAiEmailSettings` exist in `useAiEmails.ts`, but **no page imports them**. Admins and team leads cannot set tone, disclaimer, escalation hours, or the auto-send threshold from the UI. That alone violates the "everything must be UI-validatable" rule.
5. **Matching is strong but invisible.** The inbound matcher in `inbound_dispatch.py` is genuinely good (subject tag, encrypted party-email match, address scoring, disambiguation), but a user can never see why an email landed on a deal, cannot re-file a mismatched email, and cannot rescue an unmatched one. ListedKit's single loudest promise is "every email is already in the right file."

The strategic insight that reshapes the whole plan: **ListedKit also requires a human to review and send.** Its own feature page says, verbatim, "You review and send. Nothing leaves without you." So Velvet Elves' human-in-the-loop posture is **parity, not a weakness**, and Velvet Elves is already ahead on source-citation, assumptions surfacing, and audit. The way to surpass ListedKit on auto-emailing is therefore not to take the risky step of sending without a human. It is to:

- **Match** ListedKit's three workflows (inbound auto-reply, on-demand compose, scheduled reminders) plus templates and bulk-to-parties.
- **Fix** the reliability breaks (attachments, identity/signature, threading) so approving a draft never produces a wrong email.
- **Beat** ListedKit on the experience: a visible "Inbox by Deal" with correction, a mouse-first compose and review surface a non-developer can run end to end, honest source-cited drafts, and a clean configuration surface.
- **Optionally** offer an explicit, opt-in autopilot for the narrow, fully-grounded cases, with an undo window and complete audit, which is the one place we can safely go further than ListedKit's "nothing leaves without you."

That sequence makes Velvet Elves a strict superset of ListedKit's email automation.

---

## 2. Current Implemented State (grounded in source)

This section is the canonical description of what runs today. It is deliberately precise so the build plan in later sections is additive and does not rebuild working pieces.

### 2.1 The inbound-to-draft pipeline

```
Inbound email (Gmail / Outlook / iCloud)
   -> provider webhook (re-fetch message)
   -> dispatch_inbound_email()                         [inbound_dispatch.py]
        - resolve tenant from the user's integration
        - 3-layer dedupe: provider_ref_id unique index,
          15-minute fingerprint, DB unique-violation catch
        - match_transaction_for_inbound()
        - persist ONE immutable communication_logs row (direction=inbound)
        - fan out registered hooks
   -> ai_email_inbound_hook()                          [ai_email_engine.py]
   -> AIEmailEngine.handle_inbound()
        1. _classify()  (rule-based regex, no LLM)
        2. load transaction + non-deleted documents + parties + tasks
        3. _draft_reply() per kind (+ optional LLM refine)
        4. _apply_tone_rules() (redact, sign-off, disclaimer)
        5. CC the file owner
        6. persist outbound draft row:
             approval_status = auto_approved | pending_review
             status          = ready_to_send | pending_review
             escalation_due_at = now + escalation_hours
        7. if vendor_reply: create a vendor_proposals row (M4.3)
```

Key facts from the code:

- **Classification is rule-based** (`_classify`, `ai_email_engine.py`): five buckets, `factual`, `document_request`, `vendor_reply`, `uncertain`, `other`. `other` returns early with no draft.
- **Factual answers are source-validated.** `_draft_factual_from_context_ai` asks the provider to return JSON whose `source_data` must copy exact keys and exact raw values from the loaded transaction context; `_validated_source_data` rejects any value the model did not copy verbatim, and the draft falls back to a deterministic match (`_best_context_source_match`) otherwise. This is a genuine anti-hallucination control and is ahead of a generic "draft from contract" prompt.
- **Auto-approve is gated** (`handle_inbound`): `confidence >= auto_send_threshold AND kind in (factual, document_request) AND no assumptions`. Even then it only sets `approval_status="auto_approved"` / `status="ready_to_send"`. **It never actually sends.** A human still clicks Approve. The label means "safe to one-click," not "sent."
- **Tone safeguards** (`_apply_tone_rules`): redacts forbidden phrases (legal advice, "you should sue", "guaranteed", "I/we advise you to") and appends a sign-off plus the tenant disclaimer. The default sign-off is "Best regards," and the default signature line is literally "Velvet Elves" (see Section 4.4 for why that is a problem).
- **Owner CC** (`_owner_email`): the file owner is always CC'd, decrypting the Fernet-encrypted `users.email` first.

### 2.2 The human review and send surface

- API: `app/api/v1/ai_emails.py` exposes `GET /ai-emails/drafts`, `GET /{id}`, `GET /{id}/parent`, `POST /{id}/approve`, `POST /{id}/edit-and-send`, `POST /{id}/regenerate`, `POST /{id}/discard`, `POST /escalations/run` (admin), and `GET`/`PUT /ai-emails/settings`.
- Send path (`_send_draft`): resolves the user's provider via `get_email_provider_for_user`, builds an `OutboundEmail`, calls `provider.send()`, writes back `status`, `approval_status="approved"`, `approved_by/at`, `provider_name`, `provider_ref_id`, and audit-logs the action. A 409 is returned when no provider is connected.
- Frontend: `src/pages/AiEmailReviewPage.tsx` is a polished two-pane review console: filter tabs (All, Needs Review, Ready to Send, Low Confidence, Escalated), a draft list with confidence dots and kind pills, and a detail pane with a champagne hero header, the draft body with **highlighted assumptions** (`HighlightedBody`), a "Confidence" meter, an "AI Verified From" source-data rail (`SourceDataPanel`), the original inbound (`ParentInbound`), the linked vendor proposal (`LinkedVendorProposalPanel`), and the action footer (Approve & Send, Edit, Send Edit, Regenerate, Discard). It polls every 60 seconds (`useAiEmailDrafts`).

This surface already conforms to `STYLE_GUIDE.md` (champagne accents, IBM Plex Mono kickers, Lora serif titles, status triads, breadcrumb header). It is the right foundation to extend.

### 2.3 Inbound-to-deal matching

`match_transaction_for_inbound` (`inbound_dispatch.py`) is the quiet strength of the system. In order: a `[VE-TX-<id>]` subject tag, then party-email match against `transaction_parties.email` and linked `contacts.email` (decrypted in process because Fernet is non-deterministic), then address text scoring (street number plus distinctive token, zip, city, state), with explicit ambiguity handling that returns `None` rather than guess. Open transactions are preferred over closed.

### 2.4 Vendor extension (Milestone 4.3)

`vendor_reply` drafts get a `vendor_proposals` row that links the reply to a candidate task and a parsed `Scheduled: YYYY-MM-DD` date. The reviewer accepts the proposal from inside the AI Email Review page (`LinkedVendorProposalPanel`), which updates the task due date. Vendor request templates exist (`vendor_email_templates`) but are vendor-scoped only.

### 2.5 The reminder / digest engine (built, not wired)

`task_notification_service.py` builds `day_before`, `due_today`, `past_due`, `upcoming` task notifications and a `DailySummary` with per-transaction roll-ups and compiled phrasing ("You have 3 transaction(s) with deadlines due today"). `send_daily_summaries` respects a per-user `notification_prefs.daily_summary` flag. But it inserts rows with `status="pending_review"` and **never calls a provider**, nothing schedules it, and no UI shows or configures it. It is a strong skeleton waiting to be connected.

### 2.6 Providers and outbound primitives

`OutboundEmail` (`email/base.py`) already supports `attachments: list[EmailAttachment]`, `cc`, `bcc`, `in_reply_to`, and AI metadata, and `communication_logs` already carries `attachment_ids`, `message_id_header`, `in_reply_to_header`, and `thread_key`. The provider abstraction (`EmailProvider.send`) is in place for Gmail, Outlook, and iCloud. So the data shapes needed for **attachments and threading** already exist; closing those two gaps is wiring, not new primitives. **[Corrected 2026-06-08: scheduled send is the exception. `OutboundEmail` has no send-at field and there is no scheduled-email table, so Pillar C requires the new `scheduled_emails` table described in Section 15; it is not just wiring.]**

---

## 3. Requirements Coverage Map

Mapping the live code to the requirements shows the precise holes.

| Requirement | What it asks for | Status today | Gap to close |
| --- | --- | --- | --- |
| 6.2 Email Integration | Gmail/Outlook/iCloud connect, outbound + inbound | Implemented (providers, webhooks, dispatch) | None |
| 6.3 AI Email Responsibilities | Auto-respond to doc requests and factual questions, CC owner | Implemented for inbound | Document **attachment** never sent; on-demand initiation missing |
| 6.4 AI Draft Safeguards | Draft not sent, side-by-side review, assumptions bold, human final say | Implemented well | None for inbound; extend to new flows |
| 6.5 Tone & Guidelines | Configurable style, no legal advice, disclaimer | Implemented in engine | **No UI** to configure; signature/identity wrong (Section 4.4) |
| 6.6 In-App Notifications | Bell, AI-send notifications, escalations, daily summary, per-channel prefs | Partial (bell + escalation exist) | Daily summary not delivered; per-channel toggle UI missing |
| 4.8 Notifications & Reminders | Email reminders for due/critical tasks, configurable intervals, compiled summaries, daily digest | **Built but not wired** | Schedule + deliver + UI controls |
| 5.3 Document Emailing | Choose recipients/subject/body/attachments, templated, resend one-click | Not as an AI compose flow | On-demand compose + templates + attachments |
| 6.8 Vendor Communication | Constrained-format vendor requests, parse, propose date | Implemented (4.3) | Reuse template engine for non-vendor outbound |
| 6.1 Unified Communication Log | One immutable log, search/filter, resend | Implemented | Add "Inbox by Deal" view + re-file/correction |
| 6.7 / 7.8 SMS & Voice hooks | Provider-agnostic data model, future SMS | Hooks only | Out of scope here; keep model ready |
| 8.2 Natural-language task | "send reminder 3 days before inspection" | Task side partial | Tie reminder rules to email reminders (Pillar C) |

---

## 4. Confirmed Gaps and Workflow Breaks

These are the concrete defects and missing pieces, each tied to source. The build plan in Section 8 onward is organized to close every one.

### 4.1 The document-request attachment break (critical)

`_draft_document_request` (`ai_email_engine.py`) produces, on a match, the body "Attached is the {name} for {address}." with confidence 0.93 and zero assumptions, which makes it **auto-approve eligible**. But `_send_draft` (`ai_emails.py`) constructs `OutboundEmail(... )` with **no `attachments`**. `attachment_ids` exists on the communication-log model and `EmailAttachment` exists on `OutboundEmail`, but neither is populated. Result: the recipient is told a document is attached, and it is not. This is the single most damaging end-to-end break in the feature and must be fixed before any expansion.

### 4.2 No on-demand / proactive email

The engine has a single public entry point, `handle_inbound`. There is no path to compose an email that is not a reply to an inbound message. ListedKit explicitly supports "draft any email about any aspect of your transaction on the fly." This is missing entirely and is called out as deferred in `MILESTONE_4_2_AI_EMAIL_WORKFLOW.md` Section 15 ("AI-driven outbound initiation").

### 4.3 Reminders and daily digest are not delivered

`send_daily_summaries` inserts `communication_logs` rows with `status="pending_review"` and never sends. There is no scheduler, no per-interval reminder send, and no UI. Requirement 4.8 is effectively unimplemented at the delivery layer despite the computation layer being done.

### 4.4 Outbound identity and personalization feel like a bot, not the agent

- Every draft is signed "Best regards," then "Velvet Elves," and carries an AI disclaimer (`_apply_tone_rules`). ListedKit's page stresses the opposite: emails send "directly from your Gmail or Outlook account" with "No third-party branding; maintains user's professional identity." A real-estate professional wants the email to look like it came from them, signed with their name and signature block.
- The greeting uses `_first_name(email)`, which derives a name from the email handle (`john.smith@` becomes "John", but `info@` becomes "Info" and `buyer_2024@` becomes "Buyer 2024"). **[Corrected 2026-06-08: precise scope — `_first_name` is used by the document-request drafter and the deterministic factual fallback (`_draft_factual_from_context`), plus the vendor/uncertain bodies. The primary factual path (`_draft_factual_from_context_ai`) generates its own greeting via the LLM, so it is not `_first_name`-derived, but it is still not given the matched party's real name to use.]** The engine already loads parties and contacts; every path should greet using the actual party name rather than the email handle.

### 4.5 No configuration UI

`useAiEmailSettings` / `useUpdateAiEmailSettings` are defined in `useAiEmails.ts` but imported nowhere. `AdminAIGovernancePage.tsx` does not touch them. Tone, disclaimer, escalation hours, and auto-send threshold are unreachable from the UI. This breaks the non-developer-validatable rule outright.

### 4.6 Matching is invisible and uncorrectable

There is no surface that shows the inbound stream grouped by deal, no indication of why an email matched, no "this is the wrong deal, move it" action, and no queue for unmatched mail. The matcher returns `None` on ambiguity (correct), but the resulting "please confirm which property" draft is the only signal a user gets, and they cannot fix the underlying match.

### 4.7 Threading and reply continuity

`_send_draft` sets `in_reply_to=None`. AI replies therefore may not thread under the original message in the recipient's client, which looks unprofessional. M4.3 stamps threading headers for vendor sends only.

### 4.8 No templates beyond vendor, no bulk, no scheduled send, no triage actions

ListedKit offers saved templates with smart placeholders, bulk email to all parties, and "schedule it to send Thursday 9am." Velvet Elves has none of these for general client/party email, and the review queue has no bulk actions.

---

## 5. ListedKit Auto-Emailing: Capabilities and Comparison

Scope: email automation only. Sources (June 2026): the ListedKit email-automation feature page (`listedkit.com/features/email-automation`), the features index (`listedkit.com/features`), the Ava page (`listedkit.com/ava`), the agents solution page (`listedkit.com/solutions/real-estate-agents`), and the TC email-templates resource (`listedkit.com/resources/ai-email-templates-real-estate-tcs`).

### 5.1 What ListedKit's email automation actually does

1. **Auto-reply drafting.** "Ava reads your incoming emails and drafts a reply using deal context." Drafts pull parties, dates, address, and terms from the contract and from prior threads.
2. **On-demand drafting from a prompt.** Compose any email by describing it: "congrats buyer is in escrow, send timeline." Ava drafts it with full transaction context.
3. **Scheduled reminders.** Draft a reminder for a deadline and schedule the send (example given: draft Friday's closing reminder, send it Thursday 9am). Customizable intervals such as 48 hours pre-inspection or 3 days before a contingency expires.
4. **Templates with smart placeholders.** Save your best messages; placeholders auto-fill client names, dates, and deal details.
5. **Bulk send to all parties** of a transaction at once.
6. **Sends from the user's own Gmail/Outlook**, with no AI branding, preserving the agent's professional identity.
7. **Human review is mandatory.** "You review and send. Nothing leaves without you." There is no fully automatic send.

### 5.2 Side-by-side (auto-emailing only)

| Capability | ListedKit | Velvet Elves today | After this plan |
| --- | --- | --- | --- |
| Inbound auto-reply drafting | Yes | Yes, with source-validated facts and assumptions | Yes, plus fixed attachments, real signature, threading |
| Anti-hallucination grounding | "uses contract details" | Stronger: exact-value source validation, assumptions list | Same strength, extended to all flows |
| On-demand compose from a prompt | Yes | No | Yes (Pillar B) |
| Templates with placeholders | Yes | Vendor templates only | Yes, tenant + personal template library (Pillar B) |
| Bulk email to all parties | Yes | No | Yes (Pillar B) |
| Scheduled deadline reminders | Yes | Engine built, not delivered | Yes, fully wired with UI controls (Pillar C) |
| Daily digest | Not emphasized | Built, not delivered | Yes (Pillar C) |
| Send from user's own mailbox | Yes | Yes | Yes |
| No-bot identity / agent signature | Yes (no branding) | Signs "Velvet Elves" + disclaimer | Agent signature, configurable subtle disclaimer (Pillar A) |
| Human review required | Yes | Yes | Yes, plus optional opt-in autopilot with undo (Pillar A) |
| Inbox-by-deal + correction | Implied ("right file") | Matching strong but invisible | Yes, visible and correctable (Pillar D) |
| Source citation shown to user | Verify next to source | Yes (source-data rail) | Yes, extended to citations per fact |
| Audit trail of every send | Not emphasized | Complete audit log | Complete, surfaced in UI |
| Non-developer testability | Product is the test | Partial, no settings UI, no compose | Full UI test path (Section 12) |

### 5.3 Reading of the comparison

Velvet Elves is even or ahead on grounding, safeguards, and audit, and is **behind on three things users feel daily**: on-demand compose, scheduled reminders, and the visible "every email in the right file" experience. It also has two reliability defects (attachments, identity) that make the existing flow feel untrustworthy. Closing those gaps, while keeping the compliance edge, yields superiority rather than parity.

---

## 6. Product Thesis: How Velvet Elves Surpasses ListedKit

> Velvet Elves does not just reply to email. It runs the file's correspondence: it answers inbound questions with cited facts, it drafts any email you ask for from deal context, it remembers every deadline and offers the reminder before you think of it, and it keeps every message in the right deal where you can see and correct it. You stay in control, you send from your own mailbox under your own name, and every action is logged.

Positioning line for the product surface:

> AI drafts. You approve. Every message lands in the right deal, on time, in your voice.

Three rules keep the thesis honest and keep the testers' workflow from breaking:

1. **Never promise what we do not send.** If a draft says "attached," the attachment is on the send. If a draft cites a date, the date is the real one on file.
2. **Default to the agent's identity.** Drafts read as the agent, signed with the agent's signature. The AI disclaimer is minimal and configurable, present only when policy requires it.
3. **Make every step a visible, mouse-first action.** A real-estate tester can connect a mailbox, watch an inbound email become a cited draft, approve it, compose a new email from a template, schedule a reminder, and correct a mis-filed email, all without typing more than a sentence and without leaving the app.

---

## 7. Frontend UI Principles (non-negotiable)

These principles are the contract with the testers. They derive from `STYLE_GUIDE.md`, the "UI testable by non-dev testers" rule, the "no demo data without real data" rule, and the "calendar page design reference" benchmark.

1. **Mouse-first, minimal typing.** Every common action is a click or a select: pick a recipient from the deal's known parties, pick a template from a list, pick a "send time" from preset chips (Now, Tomorrow 9am, 1 day before, 3 days before). Free typing is optional polish, never the only path.
2. **One screen per job, no dead ends.** Inbound review, compose, reminders, and inbox-by-deal each have a clear home, and every button leads to a real action with a real result a tester can see (a sent email in the log, a scheduled reminder on the calendar, a corrected deal match).
3. **Honest empty states, real data only.** No mock drafts, no sample reminders on real surfaces. Empty states explain what will appear and why (per `STYLE_GUIDE.md` Section 11). A built-in, clearly-labeled "Send a test email to this deal" affordance is the only way to populate the surfaces for testing, and it sends real mail to the tester's own address.
4. **Modern, professional, on-brand.** Reuse the existing AI Email Review visual system and the `/calendar` design language (header, cards, pills, stats) so the new surfaces feel native. Champagne accent only on AI-touched moments. Lora serif titles, IBM Plex Mono kickers, status triads, 1px hairlines, the breadcrumb header on every internal page.
5. **Confidence and source are always visible.** Every AI-produced draft shows its confidence, its cited facts, and any assumptions, exactly as the review page does today. Nothing is sent blind.
6. **Explain the automation in plain English.** Settings and autopilot controls describe behavior in a sentence the tester understands ("When a question is fully answered by the file, mark it ready to send in one click. We never send without you unless you turn on Autopilot below.").

---

## 8. The Build Plan: Four Pillars

The work is organized into four pillars plus two cross-cutting tracks. Each pillar is independently shippable and independently testable through the UI, which keeps the testers unblocked and the rollout safe.

- **Pillar A:** Make the existing inbound auto-reply trustworthy (fix attachments, identity/signature, personalization, threading, and ship the settings UI). This is the reliability foundation; nothing else ships first.
- **Pillar B:** On-demand AI compose, template library with placeholders, and bulk-to-parties.
- **Pillar C:** Scheduled deadline reminders and daily digest, wired end-to-end with UI controls.
- **Pillar D:** Inbox by Deal with matching transparency and a correction loop.
- **Cross-cutting 1:** Opt-in Autopilot with an undo window and full audit (the one place we exceed "nothing leaves without you").
- **Cross-cutting 2:** Compliance and audit surfacing, plus the non-developer test harness.

Dependencies: A is first. B and C can proceed in parallel after A. D can proceed in parallel with B and C. Autopilot depends on A and on the audit surfacing.

---

## 9. Pillar A: Make Inbound Auto-Reply Trustworthy

### 9.1 Fix the attachment flow (closes 4.1)

Backend:

- In the document-request drafter, persist the matched document id onto the draft. The communication-log row already has `attachment_ids`; populate it with the matched document's id when a document is found.
- In the send path (`_send_draft`), when the draft has `attachment_ids`, load each document, fetch its bytes from storage, and append an `EmailAttachment` (filename, mime type, base64, document id) to the `OutboundEmail`. Respect provider attachment size limits; if a file exceeds the provider limit, fall back to a secure, expiring document link (requirement 5.3 allows secure links as fallback) and adjust the body copy to say "Here is a secure link to the {document}" rather than "Attached."
- Guard rule: a `document_request` draft may only stay auto-approve eligible if the attachment (or fallback link) is actually resolvable at draft time. If the document cannot be resolved, downgrade confidence and add an assumption, exactly as the no-match path already does.

Frontend (review page):

- Show an **Attachments** chip row in the draft detail (filename, size, a paperclip icon) so the reviewer sees what will actually be sent. If a fallback link is used, label it "Secure link (file too large to attach)."
- Block the Approve & Send button with an inline explanation if the draft references an attachment that failed to resolve, offering "Attach a different document" (opens the deal's document picker) or "Remove the attachment line."

This single fix converts the most dangerous draft type into a reliable one.

### 9.2 Real agent identity and signature (closes 4.4)

- Add a per-user **email signature** (rich text or plain) stored on the user profile, editable in profile settings. Default it from the user's name, title, brokerage, and phone. The engine appends the agent's signature instead of the literal "Velvet Elves" block.
- Make the AI disclaimer **tenant-configurable and minimal**, default to a single quiet line, and allow tenants in non-attorney contexts to disable it for human-approved sends (the disclaimer requirement in 6.3/6.5 is strongest for autonomously AI-sent mail; a human-approved Edit & Send is the human's email). Keep the disclaimer mandatory whenever Autopilot sends without a human (Cross-cutting 1).
- The sign-off ("Best regards" / "Cheers" / "Best") stays driven by the tenant tone setting, but sits above the agent signature, not the brand name.

### 9.3 Greet by the real party name (closes 4.4)

- The engine already loads parties and contacts. Replace the email-handle greeting with the matched party's first name when the sender maps to a known party or contact; fall back to the handle only when no party match exists, and never render an obviously wrong name (suppress the greeting name for role addresses like `info@`, `office@`, `team@`).

### 9.4 Thread the reply (closes 4.7)

- Stamp the inbound provider message id on the inbound log, and set `OutboundEmail.in_reply_to` from it on the reply send so the message threads in the recipient's client. Reuse the threading-header approach M4.3 already introduced for vendor sends.

### 9.5 Ship the AI-email settings UI (closes 4.5)

- Add an **Email Automation** settings surface for Admin and Team Lead. Per `STYLE_GUIDE.md` Section 16.8, AI configuration the admin reaches from the dashboard belongs on the AI Governance surface, so add an "Email Automation" section to `AdminAIGovernancePage.tsx` (or a sibling tab in that admin group with the shared breadcrumb header), wired to the existing `useAiEmailSettings` / `useUpdateAiEmailSettings` hooks.
- Controls, all mouse-first:
  - **Tone:** segmented control (Professional, Friendly, Concise).
  - **Disclaimer:** a textarea with a "Use recommended" reset and a live preview, plus a toggle "Include disclaimer on human-approved sends."
  - **Escalation reminder:** a slider or stepped select for 24 to 48 hours.
  - **Auto-send readiness threshold:** a slider from 0.80 to 1.00 with plain-English labels ("Only mark a draft ready when the AI is very sure"). Show, live, how many of the current drafts would be marked ready at the chosen threshold so the setting is concrete.
- Every change writes through the existing audited `PUT /ai-emails/settings`.

### 9.6 Review-queue ergonomics

- Add **bulk triage** to `AiEmailReviewPage.tsx`: select all in the "Ready to Send" tab, "Approve & Send selected" with a confirm dialog summarizing recipients. This is a high-value, low-risk speed win that matches a TC's "clear the queue" mental model.
- Add a per-fact citation hover in the source rail so each cited value links to where it came from (transaction field, document, party).

### 9.7 Pillar A acceptance (UI-validatable)

A non-developer can: connect a mailbox, send a test "where is the inspection report?" to the deal, watch a cited draft appear with a visible attachment chip, approve it, and confirm in the recipient inbox that the attachment really arrived, the email is signed with the agent's name, and it threads under the original. They can also open Email Automation settings and change the tone and disclaimer and see the change reflected in the next draft.

---

## 10. Pillar B: On-Demand AI Compose, Templates, and Bulk

### 10.1 New engine entry point

Add a second public engine path alongside `handle_inbound`, for example `compose_outbound`, that takes a transaction, a recipient set, an intent (free text such as "send the buyer the closing timeline" or a chosen template), and the same tenant settings, and produces an `AiEmailDraft` using the same grounding, tone, and safeguard pipeline. It reuses `_build_transaction_context`, `_apply_tone_rules`, the agent signature, and the source-validation discipline. Crucially, it shares the **same review-and-send path** as inbound drafts, so there is one audited send, one log shape, one undo behavior.

### 10.2 Template library with placeholders

- Generalize the existing `vendor_email_templates` concept into a tenant **email template library** plus a personal "my templates" set. Templates carry a subject and body with placeholders that auto-fill from deal context: `{{property_address}}`, `{{closing_date}}`, `{{buyer_name}}`, `{{seller_name}}`, `{{inspection_date}}`, `{{agent_signature}}`, and so on, matching the placeholder approach already proven in `VendorTemplateService`.
- Seed a starter set of system templates per tenant (closing timeline to client, congratulations under contract, inspection scheduled, document request to a party, post-closing follow-up), so the surface is useful on day one without the tenant authoring anything. These are templates (structure), not demo data (fake records), so they comply with the "no demo data" rule.
- Admin/Team Lead manage tenant templates from the same admin group as vendor templates (extend `VendorTemplatesPage.tsx` patterns).

### 10.3 Compose UI (mouse-first)

A **Compose** action available from the deal workspace, the deal's communication panel, and the AI Email Review page. The composer is a guided card, not a blank editor:

1. **Recipients:** chips prefilled from the deal's known parties (Buyer, Seller, Co-agent, Lender, Title, Attorney, Vendors). The user clicks to include; "All parties" is one click (bulk send). Free-typing an address is allowed but secondary.
2. **What do you want to say:** either pick a **template** from a list (each shows a one-line preview) or type a short intent ("send the buyer the timeline"). This is the only place typing may occur, and a template removes even that.
3. **Generate:** the AI fills subject and body from deal context, shows the same confidence, cited facts, and assumptions as the review page, in the same visual system.
4. **Send options:** Send now, or **Schedule** (preset chips: Tomorrow 9am, specific date/time, or relative to a deal date like "1 day before closing"). Scheduling routes to Pillar C's scheduled-send mechanism.
5. **Review and send:** identical Approve / Edit / Discard controls, identical audit.

Bulk-to-parties produces one draft per recipient group with per-recipient personalization (correct names), shown as a compact list the user approves together or one by one.

### 10.4 Pillar B acceptance (UI-validatable)

A tester opens a deal, clicks Compose, clicks "Buyer," picks the "Closing timeline" template, clicks Generate, sees a draft with the real closing date cited, clicks Send, and finds the email in their sent mail and in the deal's communication log. They repeat with "All parties" and confirm each party got a correctly-named copy.

---

## 11. Pillar C: Scheduled Reminders and Daily Digest

### 11.1 Wire the existing engine to delivery

`task_notification_service.py` already computes everything. The plan adds the missing three layers:

1. **A scheduler.** Add a single internal scheduled job (the same cadence model as the existing escalation runner, which is already admin/cron-triggered) that, per tenant, runs the reminder pass daily at a tenant-configured local hour and the digest pass once daily. Reuse the escalation runner's tenant-scoping and idempotency pattern so re-runs do not double-send.
2. **Real delivery as drafts or sends.** Reminder and digest emails flow through the **same review-and-send path** as every other AI email. Default behavior: a reminder is created as a draft addressed to the responsible internal owner (and, where appropriate, the client) and surfaced in the review queue and the bell, exactly like an inbound draft. Tenants who enable Autopilot for reminders (Cross-cutting 1) may have low-risk internal reminders auto-send.
3. **HTML rendering.** Render the digest with a branded, on-style HTML template (not the current plain text), matching the email template system in `branded_invite_email.py`.

### 11.2 Reminder rules tied to deal dates

- Reminders are configured as rules relative to key deal dates: "3 days before inspection," "1 day before closing," "day of possession." These map directly onto the task/key-date engine and satisfy requirement 8.2's example ("send inspection contingency reminder three days before inspection").
- Recipients per rule are chosen by role (internal owner, buyer, seller, vendor) via the same recipient chips as Compose.

### 11.3 Reminder and digest UI

- A **Reminders** surface per deal and a tenant-level default set. Each rule is a card: trigger (relative to which date), how far before (preset chips), recipients (chips), template (list), and on/off toggle. No typing required to set up a standard reminder.
- A **per-user notification preferences** screen (requirement 6.6) with per-channel toggles (email, in-app, push) for each category (reminders, AI sends, escalations, daily summary), wired to the `notification_prefs` already read by `send_daily_summaries`.
- The daily digest shows in-app as well as by email, and links each line to the deal and the task.
- A scheduled email appears on the deal timeline and (optionally) on `/calendar` as a "reminder will send" marker, so a tester can see the future send before it happens and cancel it with one click.

### 11.4 Pillar C acceptance (UI-validatable)

A tester sets "1 day before closing, email the buyer the closing reminder," sees the scheduled send appear on the deal timeline and calendar, uses "Send now (test)" to fire it immediately, and confirms the buyer copy arrived. They toggle off "daily summary" in their preferences and confirm they stop receiving it.

---

## 12. Pillar D: Inbox by Deal and Matching Correction

### 12.1 Inbox by Deal surface

- Add an **Emails** tab to the deal workspace and a global **Inbox by Deal** view that groups the communication log by transaction, with inbound, outbound, AI draft, system, and reminder filters (the unified log API already supports filtering; this is primarily UI).
- Each thread shows the match basis as a small, honest badge: "Matched by party email," "Matched by address," "Matched by subject tag," or "Unmatched."

### 12.2 Correction loop

- **Move to another deal:** a one-click action on any logged email that re-files it onto the correct transaction and re-runs the inbound hook so the AI re-drafts against the right context. Audit-logged.
- **Needs filing queue:** a list of unmatched and low-confidence inbound emails (the matcher already returns `None` on ambiguity; surface those) where the user picks the right deal from a suggested shortlist. Picking a deal teaches the system for that sender going forward (store the corrected sender-to-deal association so future mail from that address matches automatically).
- This directly answers ListedKit's "every email in the right file" promise, and goes further by making the basis visible and the correction one click.

### 12.3 Pillar D acceptance (UI-validatable)

A tester sends an email from an address not yet on any deal, finds it in "Needs filing," assigns it to the right deal in two clicks, watches the AI draft a reply against that deal, and confirms the next email from that same address auto-files to the same deal.

---

## 13. Cross-Cutting 1: Opt-In Autopilot (the one step beyond ListedKit)

ListedKit's ceiling is "nothing leaves without you." Velvet Elves can responsibly offer one carefully bounded step further, because its grounding and audit are strong enough to support it.

- **Off by default.** Autopilot is a tenant setting, disabled until an admin explicitly enables it, with copy that explains exactly what will happen.
- **Narrow eligibility.** Only `factual` and `document_request` drafts, only when confidence is at or above the (high) threshold, only with zero assumptions, only when the attachment (if any) is resolved, and only for recipient types the tenant allows (for example, "internal reminders" and "document delivery to known parties," but never an attorney-context legal question).
- **Undo window.** An auto-send is queued with a visible delay (default 5 minutes, tenant-configurable) during which it appears in the review queue with a prominent "Will auto-send in 4:32, hold it" button. Holding it converts it back to a normal pending draft.
- **Always disclosed and audited.** Autopilot sends always carry the disclaimer, are clearly marked in the log as auto-sent, and write the full audit entry (decision, drivers, confidence) per requirement 8.5.

This gives the speed-seeking solo agent a true "set it and forget it" mode that ListedKit does not offer, without compromising the compliance posture that attorney and brokerage tenants need (they simply leave it off).

---

## 14. Cross-Cutting 2: Compliance Surfacing and the Test Harness

### 14.1 Surface the audit advantage

- Add an **email audit view** (reuse the audit log pattern) filtered to email actions: every draft, approve, edit, discard, regenerate, escalation, reminder, and auto-send, with who/what/when and the AI drivers. This packages the compliance story that ListedKit does not emphasize.

### 14.2 The non-developer test harness (so testers never hit a dead end)

This is the explicit mechanism that makes "every aspect validatable through the UI" true:

- **"Send a test email to this deal"** button on the deal's Emails tab: it sends a real, prewritten inbound-style message (closing question, document request, or vendor schedule reply, chosen from a small menu) from the tester's own connected mailbox to the deal, so the whole inbound pipeline runs on real mail without any developer tooling or webhook poking.
- **"Send now (test)"** on any scheduled reminder, to fire it immediately.
- **A status strip** on each surface that shows, in plain English, the live state ("Mailbox connected as jane@brokerage.com," "Last inbound processed 2m ago," "1 reminder scheduled for tomorrow 9am"), so a tester always knows the system is working and what to expect next.

These are clearly labeled test affordances, send real mail to the tester, and create no fake records on production surfaces, so they comply with the "no demo data" rule.

---

## 15. Backend Implementation Summary

All changes are additive and reuse existing primitives. No working inbound behavior is rebuilt.

- **Engine:** add `compose_outbound`; refactor the shared draft-to-log persistence so both `handle_inbound` and `compose_outbound` use it; populate `attachment_ids` on document-request drafts; greet by party name; stamp threading ids.
- **Send path:** in `_send_draft`, resolve `attachment_ids` to real `EmailAttachment` payloads (with secure-link fallback) and set `in_reply_to`. This one function is where the attachment and threading fixes live.
- **Templates:** generalize `vendor_email_template` into a tenant + personal template model and repository, with a placeholder renderer shared with `VendorTemplateService`.
- **Scheduling:** a `scheduled_emails` concept (send-at timestamp, draft payload, status) plus a runner modeled on the escalation runner; the reminder/digest engine writes through it.
- **Reminders:** reminder-rule storage keyed to deal dates and roles; the daily pass in `task_notification_service.py` delivers through the standard send path and an HTML template.
- **Matching correction:** persist corrected sender-to-deal associations and consult them first in `match_transaction_for_inbound`; an endpoint to re-file a logged email and re-run the hook.
- **Settings:** extend the existing `ai_email` settings (signature defaults, disclaimer-on-human-send toggle, autopilot config, reminder send hour) behind the existing audited `PUT /ai-emails/settings`.
- **Autopilot:** a guarded, delayed auto-send path with the undo window and mandatory disclaimer/audit.
- **Tests:** extend `test_ai_email_api.py` and add service tests for attachments-on-send, compose, scheduled send, reminder delivery, matching correction, and autopilot eligibility and undo. Keep the bar at the existing suite's coverage level.

Data-model note: `OutboundEmail`, `EmailAttachment`, `communication_logs.attachment_ids`, `in_reply_to`, `metadata_json`, and threading columns already exist (4.2/4.3), so most of this is wiring, not new schema, except the template, scheduled-email, reminder-rule, and sender-association tables.

---

## 16. Frontend Implementation Summary

- **Reuse** the AI Email Review visual system (`AiEmailReviewPage.tsx`) as the shared draft viewer for inbound, compose, reminders, and autopilot-hold drafts. One viewer, many sources.
- **New surfaces:** Compose modal/card; Template library (admin + personal); Reminders (per-deal + tenant defaults); Notification preferences; Inbox by Deal (deal tab + global); Needs-filing queue; Email Automation settings (in AI Governance group); email audit view.
- **New hooks:** wire the already-defined `useAiEmailSettings` / `useUpdateAiEmailSettings`; add `useCompose`, `useEmailTemplates`, `useReminders`, `useScheduledEmails`, `useInboxByDeal`, `useRefileEmail`, `useNotificationPrefs`.
- **Design conformance:** breadcrumb header on every internal page; `/calendar` design language for the reminders and inbox surfaces; champagne only on AI moments; honest empty states; no `max-w` on internal pages; mouse-first controls (chips, segmented controls, preset time chips, recipient chips); 44px touch targets; one explicit action button per item (no whole-card click targets).

---

## 17. Mouse-First Workflow Walkthroughs

These are the canonical flows the UI must make effortless. Each is a sequence of clicks and at most one short sentence of typing.

1. **Answer an inbound question:** Bell shows "1 draft" -> open AI Email Review -> read the cited closing date in the source rail -> Approve & Send. (0 typing.)
2. **Send a document a client asked for:** open the draft -> see the attachment chip -> Approve & Send. The file is really attached. (0 typing.)
3. **Compose a client update:** open deal -> Compose -> click "Buyer" -> pick "Closing timeline" template -> Generate -> Send. (0 typing.)
4. **Schedule a reminder:** deal -> Reminders -> "1 day before closing" chip -> recipients "Buyer" -> template -> Save. See it on the calendar. (0 typing.)
5. **Fix a mis-filed email:** Inbox by Deal -> open the email -> "Move to another deal" -> pick the deal. Next email from that sender auto-files. (0 typing.)
6. **Bulk clear the queue:** AI Email Review -> Ready to Send tab -> Select all -> Approve & Send selected -> confirm. (0 typing.)

---

## 18. Non-Developer Test Scripts (acceptance, click-by-click)

These scripts are written for real-estate testers. Each is fully UI-driven and ends in an observable result.

**Script 1: Inbound auto-reply with attachment.**
1. Settings -> connect Gmail.
2. Open a deal that has an inspection report uploaded.
3. Deal -> Emails tab -> "Send a test email to this deal" -> choose "Ask for the inspection report."
4. Wait for the bell to show a new draft (under a minute).
5. Open AI Email Review. Confirm: kind is Document request, an attachment chip shows the inspection report, the greeting uses the buyer's name, the source rail cites the document.
6. Click Approve & Send.
7. Check your own inbox (you are CC'd). Confirm the attachment is really there and the email is signed with your name, not "Velvet Elves."

**Script 2: On-demand compose to all parties.**
1. Open a deal with at least a buyer and a seller.
2. Compose -> "All parties" -> "Closing timeline" template -> Generate.
3. Confirm each recipient's draft greets the correct person and cites the correct closing date.
4. Send. Confirm each party received a correctly-named copy and the deal log shows the sends.

**Script 3: Scheduled reminder.**
1. Deal -> Reminders -> "1 day before closing" -> recipients "Buyer" -> "Closing reminder" template -> Save.
2. Confirm the scheduled send appears on the deal timeline and on `/calendar`.
3. Click "Send now (test)." Confirm the buyer copy arrives and the calendar marker clears.

**Script 4: Settings change is visible.**
1. AI Governance -> Email Automation -> set Tone to Friendly, edit the disclaimer.
2. Run Script 1 again. Confirm the new tone and disclaimer appear in the new draft.

**Script 5: Matching correction.**
1. From a personal address not on any deal, email the connected mailbox.
2. Inbox by Deal -> Needs filing -> assign the email to the right deal.
3. Confirm an AI draft now exists against that deal.
4. Email again from the same address. Confirm it auto-files to the same deal.

**Script 6: Autopilot with undo (optional, if enabled).**
1. Admin enables Autopilot for document delivery only.
2. Run Script 1. Confirm the draft shows "Will auto-send in 5:00."
3. Click "Hold it." Confirm it converts to a normal pending draft.
4. Run Script 1 again, let the timer run out, confirm it sends and is marked "Auto-sent" in the log with a full audit entry.

A pillar is "done" only when its scripts pass for a non-developer with no developer assistance and no console or API usage.

---

## 19. Metrics and Success Criteria

Inbound quality:
- Draft factual accuracy (cited value matches the file) at or above 99 percent (the source-validation control should make wrong facts near-impossible).
- Document-request drafts that promise an attachment and actually attach it: 100 percent (the 4.1 fix).
- Reply threading success in the recipient client: at or above 95 percent.

Coverage and speed:
- On-demand compose available from deal, deal-comms panel, and review page.
- Scheduled reminders delivered within the configured window: at or above 99 percent, zero double-sends.
- Median clicks to send a templated client email: 4 or fewer, zero required typing.

Matching:
- Inbound auto-match accuracy on a tenant test set at or above 90 percent.
- 100 percent of unmatched or ambiguous emails appear in Needs filing.
- Corrected sender associations auto-match subsequent mail: 100 percent.

Trust and testability:
- Every email action present in the audit view.
- All six test scripts pass for a non-developer.
- Email Automation settings fully editable from the UI.

---

## 20. Phased Rollout

The order protects testers: reliability first, then breadth, then the experience layer, then the optional autopilot.

| Phase | Scope | Exit criteria |
| --- | --- | --- |
| A1 | Attachment fix + attachment chip + send-blocking guard | Script 1 passes; no draft promises an unattached file |
| A2 | Agent signature + party-name greeting + threading | Drafts read as the agent and thread correctly |
| A3 | Email Automation settings UI + bulk triage | Script 4 passes; settings editable; bulk approve works |
| B1 | Compose engine path + compose UI | Script 2 (single recipient) passes |
| B2 | Template library + placeholders + bulk-to-parties | Script 2 (all parties) passes |
| C1 | Scheduler + reminder delivery through send path + HTML digest | Script 3 passes; digest delivered |
| C2 | Reminder rules UI + notification preferences | Reminders and prefs fully UI-driven |
| D1 | Inbox by Deal + match-basis badges | Threads grouped, basis visible |
| D2 | Correction loop + Needs filing + learned associations | Script 5 passes |
| X1 | Autopilot with undo window + audit | Script 6 passes; off by default |
| X2 | Email audit view + test-harness polish | All scripts pass for a non-developer |

Each phase ships behind a feature flag, on dev first, with its test scripts as the gate, mirroring the 4.3 rollout discipline.

---

## 21. Risk Register

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Attachment bytes too large for provider | Medium | Secure-link fallback with adjusted copy (req 5.3); never silently drop |
| On-demand compose hallucinates a fact | Low | Reuse exact-value source validation; show confidence + assumptions; human approves |
| Scheduled runner double-sends | Medium | Idempotency stamp like the escalation runner; one scheduled-email row per send |
| Autopilot sends something wrong | Low (off by default) | Narrow eligibility, undo window, mandatory disclaimer, full audit, attorney contexts excluded |
| Matching correction mis-learns a shared address | Medium | Associations are per sender + per tenant, reversible, and never override an explicit subject tag or party-email match |
| Disclaimer policy conflicts with compliance | Low | Disclaimer mandatory on autopilot sends; configurable only for human-approved sends; tenant-level control |
| Testers blocked by needing developer tooling | Medium | The Section 14.2 test harness removes all developer-only steps |
| Identity change surprises existing tenants | Low | Default new signature from existing profile data; preview before first send |

---

## 22. Definition of Done

- The document-request attachment break is fixed; no draft can promise an attachment it will not send.
- Drafts are signed with the agent's signature and greet the correct party; replies thread.
- Email Automation settings are fully editable in the UI and audited.
- On-demand compose, template library, and bulk-to-parties work from the deal workspace.
- Scheduled reminders and the daily digest are delivered end-to-end with UI controls and per-user preferences.
- Inbox by Deal shows the match basis, supports one-click re-filing, surfaces unmatched mail, and learns corrections.
- Autopilot exists, is off by default, narrow, reversible within the undo window, disclosed, and audited.
- An email audit view surfaces every action.
- All six non-developer test scripts pass without developer assistance.
- `FRONTEND_UI_WORKFLOW_LOGIC.md`, `SYSTEM_DESIGN.md`, and `milestones.txt` are updated to reflect the shipped behavior.

---

## 23. Open Questions for Jake

1. **Autopilot:** do we offer the opt-in, undo-windowed auto-send at all, and if so for which recipient types (internal reminders only, or also document delivery to known parties)? My recommendation: ship it off by default, internal reminders and document delivery only, never attorney-context legal answers.
2. **Disclaimer on human-approved sends:** keep it always on, or let non-attorney tenants disable it for human-approved (not autopilot) sends so the email reads fully as the agent? My recommendation: configurable, default on, mandatory whenever autopilot sends.
3. **Default reminder rule set:** which standard reminders ship enabled per tenant (for example, 3 days before inspection, 1 day before closing, day of possession)? My recommendation: those three, all editable.
4. **Compose entry points:** deal workspace and review page are obvious; do we also want a top-level "New email" action, or keep compose deal-scoped to preserve context grounding? My recommendation: keep it deal-scoped so every email is always grounded in a file.

---

**End of Auto-Emailing System Superiority Plan.**
