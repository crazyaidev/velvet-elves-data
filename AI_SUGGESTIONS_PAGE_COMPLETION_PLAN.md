# AI Suggestions Page — Definitive Completion Plan

> **Status:** Plan only (no source changed). Authored 2026-06-03.
> **Design reference:** `VE-Intelligence-AISuggestions.html` (Jake's base design).
> **Canonical specs cross-referenced:** `requirements.txt` §2.6, §4.4–§4.9, §6, §8, §9.3.1, §10.6, §12.10; `SYSTEM_DESIGN.md` §AI Suggestions; `FRONTEND_UI_WORKFLOW_LOGIC.md` §6.1; `STYLE_GUIDE.md` (whole).
> **Current code reviewed:** backend `app/api/v1/ai_suggestions.py`, `app/services/ai_service.py`, `app/schemas/ai.py`, migration `20260802090000_milestone_5_3_personalization.sql`, `app/api/v1/router.py`, `communication_logs.py`, `ai_emails.py`, `calendar.py`; frontend `src/pages/AISuggestionsPage.tsx`, `src/App.tsx`.

---

## 0. Why the previous plans failed (root-cause, so we do not repeat it)

Every prior attempt broke during real-estate-tester walkthroughs for the same five reasons. This plan is structured to eliminate each one.

1. **The design was treated as the source of *data*, not just the source of *functionality*.** Jake's HTML is full of hand-written mock content (628 Prince Dr, "3 comps reduced this week", "0 social activity detected"). Prior plans wired the UI to render those *shapes* but had no real engine producing them, so the moment a tester opened the page on a live tenant the cards were either empty, fabricated, or broke on accept. **This violates the standing rule "no demo/sample data on real surfaces — show honest empty states" (memory: `no-demo-data-without-real-data`).**
2. **Actions were not mapped to real endpoints.** "Send Email", "Send Text", "Add to Calendar", "Add to Template", "Copy to Clipboard" were rendered as buttons with no verified backend path. On accept, the workflow dead-ended. A tester clicking "Send Email" must actually move the deal forward and leave a record in the communication log — or the button must not exist.
3. **The design's data sources were not reconciled with what the platform actually stores.** Several cards depend on data Velvet Elves does **not** have: MLS days-on-market/comps, listing-description word counts, social-media activity, Google-review sentiment, cross-agent conversion benchmarks. Building UI for those without the data is the single biggest cause of "the workflow breaks instead of flowing."
4. **Coaching / AI Coach was scoped as MVP.** Requirements are explicit: **AI Coach is a future paid add-on, NOT MVP** (`requirements.txt` §12.10; §2.6 Team-Leader "e"). The design foregrounds it (purple PRO cards, $49 upsell banner, floating widget). Prior plans either over-built it or deleted it; the correct answer is **feature-flagged placeholder, off by default.**
5. **Confidence, snooze, categories, and roles were ignored at the data layer.** The current `ai_suggestions` table only allows five *task* suggestion types and has no concept of category, priority, draft content, channel, or snooze. The design needs all of them. Prior plans bolted UI on top of a schema that could not carry the state, so filters/snooze/accept silently lost data.

**The governing principle of this plan:** *every pixel in Jake's design is honored as a capability, but every capability is wired to a deterministic detector over real tenant data and a real action endpoint — or it is explicitly gated behind an integration flag with an honest empty state.* A real-estate tester must be able to click through every surface and have the deal actually advance.

---

## 1. What "implement every feature" means here

Jake's instruction: *"I do not mean to simply copy the design exactly; I mean the specific functions of the page."* So we enumerate the **functions** in the design and commit to each one. The visual treatment follows the project `STYLE_GUIDE.md` (the design's own chrome — IBM Plex, champagne accents, navy sidebar — already matches the brand, so fidelity and style-compliance coincide here).

### 1.1 Complete function inventory extracted from the design

| # | Function in design | Design element |
|---|--------------------|----------------|
| F1 | **AI activity summary** (today's counts: new, critical, acted-on, snoozed) | Sidebar "AI activity today" mini-stat grid |
| F2 | **Intelligence briefing** (top-of-page narrative summary of the day's most urgent items + "Draft action plan") | `.ai-briefing` hero |
| F3 | **Category filtering** (All, Risk, Task, Communications, Market & Pricing, Listing & Marketing, Relationship, Coaching) with live counts | `.filter-bar` tabs |
| F4 | **Show / hide dismissed** | `.dismissed-toggle` |
| F5 | **Act on all high-confidence** (bulk-apply ≥ threshold) | topbar `acceptAll()` |
| F6 | **Category section groups** with label + count + divider | `.sg-wrap` / `.sg-header` |
| F7 | **Collapsed suggestion row**: category icon, title, priority pill, transaction context, age/timing, confidence bar+label, expand chevron | `.sug-collapsed` |
| F8 | **Priority severity rail** (critical/high/medium/low/pro left border) | `.pri-*` |
| F9 | **Expand panel — reasoning**: "Why AI flagged this" + "✦ AI recommendation" two-column | `.exp-zone-reason` |
| F10 | **Editable AI draft** (email / text / social caption / MLS copy / seller-talk framework) with read-only ⇄ edit toggle | `.exp-draft-wrap` |
| F11 | **Task checklist suggestions** with checkbox + "Add to template" | `.exp-zone-tasks` |
| F12 | **Context-specific primary action** (Send Email, Send Text, Add Tasks + Send Email, Add to Template, Schedule Text for <date>, Copy to Clipboard, Add Seller Call Task, Add gift task) | `.btn-accept` (label varies) |
| F13 | **Confidence-gated accept** (< threshold → "Confirm: …" two-step) | `handleAccept()` needs-confirm |
| F14 | **Snooze** with quick-pick durations (2h / Tomorrow / 1 week / 2 weeks) | `.btn-snooze` / `.snooze-picker` |
| F15 | **Dismiss** (with restore-via-show-dismissed) | `.btn-dismiss` |
| F16 | **Confidence meter** per card (high/med/low color) | `.confidence-*` |
| F17 | **Q&A advisor flow** (closing-gift: 3 questions → 3 tailored suggestions → add task) | `.qa-flow` |
| F18 | **PRO-gated coaching cards** (blurred body + upgrade gate) | `.pro-gate` |
| F19 | **AI Coach upsell banner** ($/mo, checklist, trial CTA) | `.coach-upsell` |
| F20 | **Floating AI Coach widget** | `.floating-ai` |
| F21 | **Toast confirmations** for every action | `.toast` |
| F22 | **Empty state** | `.empty-state` |

### 1.2 The seven content categories (and their honest data backing)

This is the crux. For each category in the design, we state the **real internal data source** that can deterministically produce it, and whether it is **MVP**, **flag-gated** (UI built, behind an integration/feature flag, honest empty state when data absent), or **deferred** (architecture hook only).

| Category | Design cards | Real data the platform already has | Verdict |
|----------|--------------|-------------------------------------|---------|
| 🔴 **Risk Alerts** | R1 financing-contingency expiring; R2 stale client comms; R3 missing required docs | milestone/key dates, `documents` + task-template "required" set, `communication_logs` recency, `tasks` deadlines | **MVP — fully buildable from internal data** |
| ✅ **Task Intelligence** | T1 pattern→template; T2 closing-gift; T3 predicted missed task | `tasks` (cross-file history for T1), `transactions.closing_date`, task state + calendar/comm absence | **MVP** (T1 = Phase 2; T2 trigger MVP, Q&A advisor flag-gated; T3 MVP) |
| 💬 **Communications** | C1 referral (6-mo post-close); C2 anniversary (1-yr post-close) | closed `transactions` with `completed_at`/`closing_date`, party contacts | **MVP** |
| 🤝 **Relationship** | REL1 review request; REL2 social post | listing go-live timing + comm recency (REL1 trigger); REL2 needs social-activity tracking | REL1 **MVP** (drop unverifiable "sentiment is positive" claim → derive from comm recency only); REL2 **flag-gated** (no social data) |
| 📊 **Market & Pricing** | M1 price-reduction nudge | listing live-date/DOM internal; **comps "3 reduced this week"** needs MLS feed (absent) | **flag-gated** — build the DOM-only trigger; the comp claim is suppressed until an MLS integration exists |
| 📣 **Listing & Marketing** | MK1 MLS-description optimization | **description word count + MLS benchmark** needs MLS listing data (absent) | **flag-gated** — UI + AI rewrite exist, but the trigger only fires when a listing description is actually stored on the deal |
| ✦ **Coaching** | CO1 negotiation; CO2 conversion benchmarking | cross-agent benchmarks, opposing-agent pattern history (absent + non-MVP) | **flag-gated placeholder** (AI Coach is non-MVP per §12.10) |

**Consequence for testing:** on a fresh real tenant, the page will reliably show **Risk, Task, Communications, and Relationship** suggestions (these derive from data testers create in the normal course of using the app). Market/Marketing/Coaching surfaces render only when their data/flags are present, and otherwise contribute honest empty states — never fabricated cards. This is exactly what stops the end-to-end flow from "breaking."

---

## 2. Reconciling design ⇄ requirements ⇄ current code

### 2.1 Canonical requirements that constrain this page

- **§10.6 Intelligence UI:** `/ai-suggestions` = pending suggestion cards (type icon, confidence ring, title, description, source, transaction link); actions Accept / **Edit & Accept** / Dismiss (optional reason); scope radio **Apply to this transaction / Apply to all future**; filter by type/confidence/transaction; **bulk action for high-confidence**.
- **§9.3.1 AI Daily Briefing:** persistent briefing surface with **Critical / Needs Attention / On Track** counters, actionable as a filter shortcut. ⇒ Maps directly to design F1 (sidebar mini-stats) + F2 (briefing hero).
- **§4.7 Confidence threshold system:** two-tier, **"Ship it" ≥ 90%** auto-proceed, **"see it first" ≤ 75%** human review; **admin sets global floor; team leads set higher**. ⇒ The design's hardcoded "< 90% → confirm" (F13) must read the **configured** thresholds, not a literal 90.
- **§4.4–§4.6 Dynamic Task Intelligence:** all additions/removals are **recommendations not forced**; transparency (reason, source, suggested deadline); removed tasks "sleep"; **scope rules** (agent→own txn, team-lead→template/all-future); post-closing **feedback loop**. ⇒ Already partly implemented in `ai_suggestions.py`; we extend, not replace.
- **§6.3/§6.4 AI email safeguards:** AI-drafted comms that contain assumptions are **drafted not sent**, routed for **Approve / Edit & Send**, with **CC to the responsible internal owner** and an **AI disclaimer**. ⇒ The design's "Send Email" must flow through the existing AI-email/communication-log pipeline, not a raw send.
- **§6.7/§4.8 SMS:** SMS is a **provider-agnostic hook**, only active **when the channel is enabled for the tenant/user**. ⇒ "Send Text" (F12) is gated on SMS being enabled; otherwise it degrades to "Copy message" + log, honestly.
- **§12.10 / §2.6e AI Coach:** **future paid add-on, NOT MVP** — "MVP may preserve architecture hooks or feature-flagged placeholders, but should not scope active implementation." ⇒ F18/F19/F20 are flagged placeholders.
- **Roles (§1.2, SYSTEM_DESIGN permission matrix, *verified against `App.tsx`*):** the route uses `RoleRoute allowedRoles={INTERNAL_AND_ATTORNEY}` where `INTERNAL_AND_ATTORNEY = ['Agent','TransactionCoordinator','TeamLead','Admin','Attorney']`. So the page is visible to **Agent, Elf (TransactionCoordinator), Team Lead, Admin, Attorney** (All/Team/Own-txn/Assigned/All/Attorney-relevant respectively — Admin = "All" per the permission matrix). **No Client/FSBO/Vendor access.** Attorney sees legal-relevant only, with **AI guardrails** (no legal-judgment suggestions — §8.6).
  > *Doc discrepancy:* `FRONTEND_UI_WORKFLOW_LOGIC.md` §6.1 lists allowed roles as "Agent, Elf, Team Lead, Attorney" (omits Admin), but the **actual route and the SYSTEM_DESIGN permission matrix both include Admin**. Code + matrix are authoritative → **Admin is included.**

> **Discrepancy to flag for Jake:** the design's upsell banner says **$49/agent/month**; requirements §12.10 say **$79/agent/month**. The number must be config-driven and confirmed before any pricing is shown. (Open question Q1.)

### 2.2 Current backend (what exists today)

`app/api/v1/ai_suggestions.py` (router prefix `/ai`):
- `GET /ai/suggestions` (filter by `status`, `transaction_id`, `min_confidence`; ordered by confidence/created).
- `GET /ai/suggestions/stats` (pending/accepted/dismissed/expired counts).
- `POST /ai/suggestions/{id}/accept` (scope transaction|all_future; **only `create_task` is actually applied** — other types just flip status).
- `POST /ai/suggestions/{id}/dismiss` (reason).
- `POST /ai/suggestions/generate?transaction_id=` (calls `AIService.recommend_task_changes`, which is **deliberately stubbed to return `[]`** as a guardrail — so generation currently produces nothing).
- Plus NL-task parse and post-closing feedback (reuse as-is).

`ai_suggestions` table (migration `20260802090000`): `type` CHECK is limited to `create_task|update_task|remove_task|restore_task|update_deadline`; columns: tenant_id, transaction_id, created_by_actor, title, description, source, reason, suggested_action_json, confidence, status (`pending|accepted|dismissed|superseded|expired`), accepted/dismissed metadata, accepted_scope, dedup_hash, expires_at. **No category, priority, channel/action_kind, draft content, or snooze fields. No `snoozed` status.**

Other services we will reuse — **and the verified gaps that prior plans missed:**
- **Communication / AI email pipeline:** `communication_logs.py` exposes `POST /communication-logs` (append-only log create; Agent/Elf/TL/Admin) and `GET` (search/filter). `ai_emails.py` exposes `approve`, `edit-and-send`, `regenerate`, `discard`, `GET /drafts`, settings, `escalations/run`. **GAP (verified):** *every* `ai_emails` action operates on a draft that **already exists** — drafts are minted only by the **inbound** AI auto-reply flow. **There is no endpoint that composes a fresh *outbound* AI draft for review, and `_send_draft` only sends an existing draft.** ⇒ "Send Email" from a suggestion is **new backend work** (a compose-draft endpoint), not a free reuse. See §5.2.
- **Calendar:** `calendar.py` `/calendar/push` pushes **transaction *closings*** into connected Google/Outlook calendars (idempotent). It does **not** push tasks and does **not** create arbitrary events. **Correction:** "Add to Calendar" (the design's walkthrough card) therefore **cannot** create a real Google/Outlook event for MVP — it degrades to creating a **dated task** that drives in-app reminders. Do not claim a calendar event is created.
- **Tasks / task templates:** `tasks.py` (task create — Agent/Elf/TL/Admin) and `task_templates.py`. **GAP (verified):** `POST`/`PUT /task-templates` are gated `require_role(ADMIN, TEAM_LEAD)` and the create path scopes to `team_id` (TeamLead) or tenant-wide (Admin) — **there is no per-agent personal task template, and an Agent/Elf cannot write any template.** ⇒ "Add to Template" (F11/F12, T1) is a **TeamLead/Admin-only** action in MVP; agent-personal templates (req §1.2a) are an un-built backend feature, not something to assume. (Note: `task_templates` = the *task library*; the `profile_settings_json.user_checklist_templates` field is the *closing/print checklist* — a different feature. Do not conflate them.)
- **Confidence config:** `confidence.py` `GET /confidence/` returns `{ global_min_floor (default 0.75), auto_proceed_threshold (default 0.90 = "Ship it"), review_threshold (default 0.75) }`, resolved **team → tenant → global**. These are the real field names to use for F13/F5.
- **Notifications:** `notifications.py` exposes `pending`, `last-seen`, `mark-seen`, `preferences`, and an admin cron POST. **GAP (verified):** notifications are **system-generated**; there is **no compose-and-schedule endpoint** for an arbitrary user message at a future date. ⇒ "Schedule Text for <date>" degrades to a **dated task/reminder** for MVP; a true scheduled auto-send is future work.

### 2.3 Current frontend (what exists today)

`src/pages/AISuggestionsPage.tsx` — a minimal flat inbox: header + stat tiles, status tabs (pending/accepted/dismissed), a min-confidence slider, and `AiSuggestionCard` with Apply / +all-future / Dismiss. **Gaps vs design:** no categories, no briefing, no expand panel, no draft editing, no snooze, no Q&A, no coach placeholder, no severity rails, no context-specific actions. **Anti-pattern present:** uses `window.confirm()` for bulk accept (forbidden by `STYLE_GUIDE.md` §13.3 / §6.5). Routed in `App.tsx` at `/ai-suggestions` under `RoleRoute allowedRoles={INTERNAL_AND_ATTORNEY}` inside `AppLayout` (correct shell).

> **Shell decision (matches memory `ve-design-comp-fidelity`):** This is an *internal app page*, so it lives inside the existing `AppLayout` (real sidebar, real topbar) — we do **not** reproduce the design's standalone sidebar/topbar chrome. The design's sidebar mini-stats (F1) and topbar action (F5) are mapped onto the real shell's existing sidebar/topbar slots. (The pixel-replica-with-own-chrome rule from that memory applies to *client-portal redesigns*, not to internal pages that already have a shell.)

---

## 3. Architecture decisions (the spine of the rebuild)

### D1 — One generic suggestion model, many detectors
Keep a **single** `ai_suggestions` table and a **single** inbox API, but make the row rich enough to carry any category/action. A library of **deterministic detector functions** (one per suggestion type) reads real tenant data and emits rows. No LLM is required to *decide* a suggestion exists; the LLM is only used to *draft prose* (email/text/caption) where a draft is needed, behind the existing safeguard pipeline. This keeps generation explainable, testable, and reproducible — a tester can set up a known deal state and predict exactly which cards appear.

### D2 — Extend the schema, do not fork it
Add nullable columns + widen the CHECK constraints via a new migration (§4). Existing task-type rows keep working. New columns: `category`, `priority`, `action_kind`, `draft_channel`, `draft_subject`, `draft_body`, `draft_editable`, `context_label`, `timing_label`, `snoozed_until`, plus `'snoozed'` status and a wider `type`/`action_kind` vocabulary.

### D3 — Accept = execute a real action, transactionally and auditable
`accept` dispatches on `action_kind` to a real executor, writes the audit log, and only then flips the row to `accepted`. If the executor fails, the row stays `pending` and the UI restores the card (optimistic-with-rollback per §9.4b). **Copy-to-clipboard is a pure front-end action** (no accept needed) and is offered for MLS/social drafts where the destination is an external surface. **Executors that require *new* backend work (not free reuse), per the §2.2 gap audit:** (a) `send_email` needs a **compose-draft endpoint** (no outbound-draft minting exists today); (b) `add_to_template` is **TeamLead/Admin-only** (no agent-personal template exists); (c) `schedule_message` and "add to calendar" have **no scheduled-send / arbitrary-event API**, so they degrade to **dated tasks** for MVP. The plan treats these as explicit build items, not assumptions.

### D4 — Confidence is configuration, not a constant
Read `{ global_min_floor, auto_proceed_threshold, review_threshold }` from `GET /confidence/` (resolved **team → tenant → global**; defaults 0.75 / 0.90 / 0.75). A suggestion ≥ `auto_proceed_threshold` ("Ship it") is "high-confidence" (eligible for F5 bulk and single-click accept); below it, accept requires the F13 confirm step. Risk-category cards are always shown regardless of confidence (per §6.1 "Risk alerts shown with red indicator regardless of confidence").

### D5 — Honest empty states everywhere (no fabrication)
If a detector has no real data to act on, it emits nothing; the category renders an empty state or is hidden. Flag-gated categories (Market/Marketing/Coaching) show a one-line explanatory state when their integration/flag is off (style guide §11). **Never** ship the design's literal sample cards as seeded content.

### D6 — Coaching/AI Coach is a dormant, flagged surface
The coaching section, PRO gate, upsell banner, and floating widget are built to the design but rendered only when `feature_flags.ai_coach_enabled` is true (default false). With the flag off, none of it appears — the page is a clean MVP intelligence inbox. With it on (future), the placeholders show the upgrade path. No coaching *logic* (opposing-agent pattern analysis, cross-agent benchmarking) is implemented for MVP.

---

## 4. Data model changes (migration)

New migration `migrations/20260605090000_ai_suggestions_intelligence.sql` (additive, reversible):

```sql
ALTER TABLE public.ai_suggestions
  ADD COLUMN IF NOT EXISTS category       TEXT,      -- risk|task|comms|relationship|market|marketing|coaching
  ADD COLUMN IF NOT EXISTS priority       TEXT,      -- critical|high|medium|low|pro
  ADD COLUMN IF NOT EXISTS action_kind    TEXT,      -- send_email|send_text|schedule_message|add_task|
                                                     --   add_to_template|copy_text|add_seller_call_task|none
  ADD COLUMN IF NOT EXISTS draft_channel  TEXT,      -- email|sms|social|mls|talk_track|null
  ADD COLUMN IF NOT EXISTS draft_subject  TEXT,
  ADD COLUMN IF NOT EXISTS draft_body     TEXT,
  ADD COLUMN IF NOT EXISTS draft_editable BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS context_label  TEXT,      -- "628 Prince Dr, Greenwood" — shown in collapsed row
  ADD COLUMN IF NOT EXISTS timing_label   TEXT,      -- "Flagged 2h ago" / "28 days to close"
  ADD COLUMN IF NOT EXISTS snoozed_until  TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS recipient_party_id UUID,  -- which transaction party the draft targets
  ADD COLUMN IF NOT EXISTS detector_key   TEXT;      -- stable detector id, e.g. 'risk.financing_contingency'

-- widen status to include 'snoozed'
ALTER TABLE public.ai_suggestions DROP CONSTRAINT IF EXISTS ai_suggestions_status_check;
ALTER TABLE public.ai_suggestions ADD CONSTRAINT ai_suggestions_status_check
  CHECK (status IN ('pending','accepted','dismissed','snoozed','superseded','expired'));

-- widen type to cover non-task suggestions (keep old values valid)
ALTER TABLE public.ai_suggestions DROP CONSTRAINT IF EXISTS ai_suggestions_type_check;
ALTER TABLE public.ai_suggestions ADD CONSTRAINT ai_suggestions_type_check
  CHECK (type IN (
    'create_task','update_task','remove_task','restore_task','update_deadline',
    'risk_alert','comms_nudge','relationship_nudge','market_nudge',
    'marketing_nudge','coaching_tip'
  ));

CREATE INDEX IF NOT EXISTS idx_ai_suggestions_category
  ON public.ai_suggestions(tenant_id, status, category, confidence DESC);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_snooze
  ON public.ai_suggestions(snoozed_until) WHERE status = 'snoozed';
```

- **Dedup** continues via `dedup_hash`; detectors compute the hash from `detector_key + transaction_id + salient facts` so the same condition does not re-flood (existing pattern in `_dedup_hash`). Re-running a detector on an unchanged state is a no-op.
- **RLS** unchanged (tenant isolation already enforced).
- **Snooze** uses `status='snoozed'` + `snoozed_until`; a scheduled job (or lazy on-read sweep) flips it back to `pending` when `snoozed_until <= now()`.
- **No new columns are required for coaching** — coaching rows use `category='coaching'`, `priority='pro'`, and render through the flag gate.

---

## 5. Backend implementation plan

### 5.1 Suggestion-generation engine (`app/services/suggestion_engine.py`, new)

A registry of **detectors**, each: `key`, `category`, `applies(ctx) -> bool`, `build(ctx) -> SuggestionDraft`. A tenant- or transaction-scoped run loads the needed context once (transaction, key dates, tasks, documents, required-doc template set, communication-log recency, closed-deal history) and emits rows via upsert-by-dedup.

**MVP detectors (deterministic, internal data only):**

| detector_key | category / priority | Fires when (all from real data) | confidence basis | draft / action |
|---|---|---|---|---|
| `risk.financing_contingency` | risk / critical | financing-type deal **and** a financing/appraisal key-date within N days **and** no lender-commitment document present | rises as deadline nears & doc absent | email draft to client/lender → `send_email` (+ optionally `add_task`) |
| `risk.stale_client_comms` | risk / high | last `communication_logs` entry with the client > threshold days **and** deal still active with future close | gap length vs configured cadence | text/email draft → `send_text`/`send_email` |
| `risk.missing_required_docs` | risk / high | **Corrected basis:** internal deals do **not** model "required documents" (only FSBO does, via `fsbo_workspace.required_doc_types_for`). So fire on **incomplete documentation/compliance *tasks*** from the task library (e.g. "Order Title", "Deliver HOA Docs", "Closing Disclosure Delivered") that are still open **and** have no matching uploaded `documents` row, with close within window | count & proximity to close | `add_task` (per gap) + request email (needs compose-draft, §5.2) |
| `task.predicted_missed` | task / high | a task due within N days with status not started **and** no comm/calendar evidence of progress | days-to-due | text draft + `add_task`/update |
| `task.closing_gift` | task / low | active deal with `closing_date` within the gift window (e.g. 14–30 days) and no existing "Closing Gift" task done | fixed/high | `add_task` ("Closing Gift"); Q&A advisor = flag-gated enrichment |
| `comms.referral_request` | comms / low | a **closed** deal whose `completed_at` ≈ 6 months ago, client contact on file | fixed | email draft → `send_email` |
| `comms.anniversary` | comms / low | a **closed** deal whose `completed_at` ≈ 12 months ago | fixed | text draft + `schedule_message` → **MVP: dated task** "Send anniversary text on <date>" (no scheduled-send infra, §2.2) |
| `relationship.review_request` | relationship / low | active listing live ≥ N days, recent positive-cadence client comms exist | timing-based (NO sentiment claim) | text draft → `send_text` |

**Flag-gated detectors (UI built; emit only when their data/flag is present):**

| detector_key | gate | Notes |
|---|---|---|
| `market.price_reduction` | `flags.mls_integration` | DOM from internal listing-live date can fire a softened nudge; the "comps reduced" claim is included **only** when comp data exists. Without the flag: no card. |
| `marketing.mls_description` | a listing **description** is actually stored on the deal | Fires on word-count of the stored description; benchmark copy shown generically (no fabricated "23% more saves" unless a benchmark source exists). |
| `relationship.social_post` | `flags.social_tracking` | "no social activity detected" requires social data; otherwise offer a generic "Draft a just-listed post" with copy-to-clipboard only. |
| `task.pattern_template` (T1) | Phase 2 | Requires cross-transaction task-history analysis (manually-added task on ≥ X of last Y files). Deterministic but heavier; deferred to Phase 2. |
| `coaching.*` (CO1/CO2) | `flags.ai_coach_enabled` (default off) | Placeholder only; no analysis logic in MVP. |

### 5.2 API surface (extend `app/api/v1/ai_suggestions.py`)

- **`GET /ai/suggestions`** — extend response with the new fields; add `category` filter and a `group=category` option returning rows grouped into the design's section order. Continue to default `status=pending`. Respect role scoping (Agent own, Elf assigned, TL team, Attorney legal-relevant only).
- **`GET /ai/suggestions/briefing`** *(new)* — returns the F2 narrative + F1 counters: `{ counts: {new, critical, acted_on_today, snoozed}, headline, narrative, critical_items[], refreshed_at }`. Counters reuse `stats` plus today's accepted/snoozed. The narrative is assembled from the top-priority pending rows (template string, not free LLM, to stay deterministic and §9.3.1-compliant — Critical/Needs-Attention/On-Track framing).
- **`POST /ai/suggestions/{id}/accept`** — dispatch on `action_kind`:
  - `add_task` / `add_seller_call_task` → existing task insert (already present in `accept`), with reason/source/confidence carried (§4.5 transparency). **MVP "Add to Calendar" reuses this** (dated task) — `/calendar/push` is closings-only and cannot create the event (§2.2).
  - `add_to_template` → **TeamLead/Admin only** (`POST /task-templates` is `require_role(ADMIN, TEAM_LEAD)`; create scopes to team_id/tenant). For **Agent/Elf the action is hidden/disabled** with a "Ask your team lead to add this to the template" affordance, because **no agent-personal task template exists** (req §1.2a is unbuilt — **flagged gap Q7**). Honors scope rules (§4.4); TL change shows the affected-transactions preview.
  - `send_email` → **NEW backend work required (no outbound-draft endpoint exists — §2.2).** Add `POST /ai-emails/compose` (or fold into `accept`) that creates a **pending `communication_logs` draft** (`is_ai_generated=true`, `ai_assumptions`, `approval_status='pending'`) from `{transaction_id, recipient_party_id→emails, subject, edited draft_body}`, **CC the responsible internal owner**, append the **AI disclaimer** (§6.3/§6.4), then return the draft id so the UI routes to the existing **Approve / Edit-&-Send** path. The inline editable draft on the card is itself the human review; a ≥`auto_proceed_threshold` unedited draft may go straight to Approve-&-Send.
  - `send_text` → log an SMS-channel `communication_logs` entry (`POST /communication-logs`, channel=`sms`). **Actual SMS transmission is a non-MVP provider hook (§6.7)** — so for MVP this **records/copies** rather than truly delivering; when SMS is not enabled, return 409 and the UI falls back to copy.
  - `schedule_message` → **no scheduled-send infra (§2.2)** → MVP creates a **dated task** ("Send anniversary text on <date>"); true scheduled auto-send is Phase 3.
  - `copy_text` → not an accept path; front-end only.
  - On success: audit log (`ai_suggestion_accept` with action_kind + scope), flip to `accepted`. On failure: leave `pending`, return error.
- **`POST /ai/suggestions/{id}/dismiss`** — unchanged (records reason for the learning loop, §4.6).
- **`POST /ai/suggestions/{id}/snooze`** *(new)* — body `{ duration: '2h'|'tomorrow'|'1week'|'2weeks'|iso }`; set `status='snoozed'`, compute `snoozed_until`; audit. A sweep re-activates due rows.
- **`POST /ai/suggestions/act-all-high-confidence`** *(new)* — server-side bulk accept of all pending rows at/above the team "Ship it" threshold whose `action_kind` is safe to auto-apply (e.g. `add_task`, `schedule_message`); **email/text actions are excluded from auto-send** and instead are queued as drafts for review (safeguard §6.4). Returns a per-row result list for the toast.
- **`POST /ai/suggestions/generate`** — repoint from the stubbed `recommend_task_changes` to the new `suggestion_engine.run(transaction_id|tenant)`; keep dedup. (Background generation on state-change is a Phase 3 hook; for MVP it runs on this explicit call and on a periodic sweep.)
- **`PATCH /ai/suggestions/{id}/draft`** *(new, optional)* — persist an edited `draft_body` so the edit survives reload before accept (the design edits in place; persisting is nicer but optional — front-end may also just pass the edited body into `accept`).

### 5.3 Attorney guardrails (§8.6)
For `role=Attorney`, the engine emits only legal-relevant categories (risk/task tied to attorney-owned matters) and **never** coaching, marketing, market-pricing, or relationship nudges. No suggestion may assert legal equivalence/position. Accept actions that would send legal communications route through the attorney approval path, not auto-send.

### 5.4 Confidence wiring
Add a small helper to read `{ global_min_floor, auto_proceed_threshold, review_threshold }` from `GET /confidence/` (resolved team→tenant→global). The accept endpoint enforces: if `confidence < auto_proceed_threshold` and the request is not flagged `confirmed=true`, return `200` with `{requires_confirmation: true}` instead of executing (mirrors design F13). The front-end then re-posts with `confirmed=true`.

---

## 6. Frontend implementation plan

### 6.1 Page composition (inside `AppLayout`, per `STYLE_GUIDE.md` §15/§16)

Rebuild `src/pages/AISuggestionsPage.tsx` as a composition of focused components under `src/components/ai-suggestions/`:

- `AISuggestionsPage` — data orchestration (load grouped suggestions + briefing + confidence config), URL-encoded filter/category state (§2.4 deep-linking), optimistic mutations with rollback.
- `IntelligenceBriefing` (F2) — the navy hero. Mono kicker "Intelligence summary — today", serif headline, narrative, "Draft action plan" (opens AI chat / drafts a plan), "Refreshed N min ago". Uses `from-ve-sidebar` gradient, white text — matches the design and §16.3 "one brand-toned hero."
- `AiActivityStats` (F1) — the four counters. On internal pages the real sidebar already owns KPI tiles, so these render as a compact stat strip beneath the briefing (style-guide KPI card vocabulary, §16.4) and double as the §9.3.1 Critical/Needs-Attention/On-Track counters; each is a **clickable filter** (New→all pending, Critical→risk, Acted-on→accepted, Snoozed→snoozed).
- `CategoryFilterBar` (F3/F4) — rounded filter chips with live counts + "Show dismissed" toggle. Chips use the `ve-orange-soft/active` treatment already in the current page; **counts come from the grouped API**, not client guesses.
- `SuggestionSection` (F6) — per-category group with mono label (category-colored), count pill, hairline divider.
- `SuggestionCard` (F7–F16) — collapsed row (category icon tile, title, priority pill, `context_label`, `timing_label`, confidence bar+label, chevron) with a `pri-*` left rail (`ve-red/amber/blue/green/purple`); expands to:
  - `SuggestionReasoning` (F9) — "Why AI flagged this" (`reason`) + "✦ AI recommendation" (champagne/purple AI box) two-column.
  - `SuggestionDraftEditor` (F10) — read-only ⇄ textarea toggle bound to `draft_body`; champagne focus ring per §6.2.
  - `SuggestionTaskChecklist` (F11) — when `suggested_action` carries tasks: checkbox rows + "Add to template" (teal) action.
  - `SuggestionActionRow` (F12–F15) — primary action button whose **label + handler derive from `action_kind`** (Send Email / Send Text / Add Tasks + Send Email / Add to Template / Schedule Text for <date> / Copy to Clipboard / Add Seller Call Task / Add gift task), plus Snooze (with `SnoozePicker`) and Dismiss; right-aligned confidence meta.
- `SnoozePicker` (F14) — inline duration chips → `POST /snooze`.
- `ClosingGiftAdvisor` (F17) — the Q&A flow, **flag-gated** (`flags.ai_coach_enabled` or a dedicated `flags.gift_advisor`); when off, the closing-gift card still offers the plain "Add gift task to queue" action (its MVP trigger works without the advisor).
- `CoachingPlaceholder` + `AiCoachUpsell` + `FloatingAiCoach` (F18–F20) — rendered only when `flags.ai_coach_enabled`. Price string from config (Q1).
- `useSuggestionConfirm` — replaces the design's needs-confirm inline mutation; on a `requires_confirmation` response, the primary button switches to "Confirm: <label>" (champagne) for one click (F13). **No `window.confirm`.**
- Toaster (F21) — reuse `react-hot-toast` already in the page (style-guide compliant); the existing `window.confirm` in bulk-accept is **removed** and replaced by an `AlertDialog` preview ("Apply N suggestions ≥ X%?") per §6.5/§13.3.
- `EmptyState` (F22) — per-category and whole-page honest empty states (§11).

### 6.2 Action → endpoint map (so nothing dead-ends)

| Design action label | `action_kind` | Front-end behavior | Backend | Reuse vs new |
|---|---|---|---|---|
| Send Email | `send_email` | optimistic remove → route to AI-email Approve/Edit&Send review; toast on send | `accept` → **NEW** compose-draft (pending `communication_logs`, +CC owner, +disclaimer) → existing approve/edit-&-send | **new** (compose endpoint) |
| Send Text | `send_text` | if SMS enabled: record + toast; else fall back to Copy + toast "SMS not enabled — copied" | `accept` → log `communication_logs` channel=sms; **no real delivery in MVP** (§6.7); 409 → FE copy fallback | partial (log reuse; delivery deferred) |
| Add Tasks + Send Email | `add_task`+`send_email` | create tasks, then queue email draft for review | `accept` composite (task insert + compose-draft) | task reuse + **new** compose |
| Add to Template | `add_to_template` | **TL/Admin:** toast "Added to template". **Agent/Elf:** action disabled with "Ask your team lead" note | `accept` → `POST /task-templates` (Admin/TeamLead only) | reuse, **role-gated**; agent-personal = gap (Q7) |
| Schedule Text for <date> | `schedule_message` | toast "Reminder task added for <date>" | `accept` → **dated task** (no scheduled-send infra) | reuse (task); true schedule = Phase 3 |
| Add Seller Call Task / Add gift task | `add_task` | toast "Task added" | existing task insert | reuse |
| Copy to Clipboard / Copy Caption | `copy_text` | `navigator.clipboard.writeText(draft_body)` + toast | none (FE only) | reuse |
| Add to Calendar (walkthrough) | `add_task` (dated) | create dated task (drives in-app reminders); **does NOT create a Google/Outlook event** | task insert (`/calendar/push` is closings-only) | reuse; external event = future |

### 6.3 Style-guide compliance checklist (enforced in review)
- Tokens only (`ve-*`), no raw hex, no default Tailwind palette (§2.4).
- Serif for hero/section titles, mono kickers ≤ 11px, sans body; one serif title per card (§3).
- Cards `rounded-xl`/`rounded-2xl`, hairline borders, named shadows; severity via 4px left rail + paired status triads (§5, §16.5).
- Buttons via shared `<Button>` variants; primary action is **filled orange**, never an outline, on action items (§16.5).
- Selects (if any filter becomes a select) use Radix `<Select>`, never native (§9.3).
- No `window.confirm/alert/prompt`; use `AlertDialog`/inline confirm (§13.3).
- Accessibility: icon-only buttons get `aria-label`; Esc closes pickers; keyboard order follows visual order; ≥ 32px hit targets (§12).
- Empty/loading states: skeleton cards on load; honest dashed empty states with one-line copy (§9.4b/§11).

---

## 7. Feature-by-feature acceptance behavior (the contract)

For each design function, the exact behavior, data source, and the "done" condition a tester can observe.

- **F1 AI activity counters** — real counts from `/briefing`. Done: opening the page on a deal with a stale-comms condition shows "Critical/New" > 0; clicking a counter filters the list.
- **F2 Briefing** — narrative built from the top pending rows. Done: with at least one critical risk present, the hero names it; with none, it reads an honest "You're on track today" state (not fabricated).
- **F3 Category tabs + counts** — counts from grouped API. Done: switching tabs shows only that category; "All" shows every section in design order.
- **F4 Show dismissed** — toggles `status=dismissed` rows back in, dimmed, restorable. Done: dismissed card reappears and can be restored.
- **F5 Act on all high-confidence** — `AlertDialog` preview → bulk endpoint; **never auto-sends emails/texts** (those become review drafts). Done: tasks/scheduled items apply; comms appear in the AI-email review queue; toast summarizes.
- **F6–F8 Sections/rows/rails** — render from row fields; severity rail color = `priority`.
- **F9 Reasoning** — `reason` + recommendation copy from the row; never blank.
- **F10 Draft editor** — edit persists into the accept payload (and optionally via `PATCH /draft`). Done: edited body is what actually sends/copies.
- **F11 Add-to-template** — **TeamLead/Admin only** (`POST /task-templates` is role-gated; no agent-personal template exists — Q7). Done (TL/Admin): task added to the team/tenant template with affected-transactions preview before confirm (§4.4); future new deals include it. Done (Agent/Elf): the action is **disabled** with an "Ask your team lead to add this" affordance — it does **not** silently fail.
- **F12 Context actions** — per the §6.2 map. Done: each label performs its mapped real action and the deal state changes (task created / draft queued / message scheduled / clipboard filled).
- **F13 Confidence gate** — below team "Ship it" threshold → one-click "Confirm:" step. Done: a 72% card requires confirm; a 95% card applies in one click.
- **F14 Snooze** — durations set `snoozed_until`; card leaves the list; returns when due. Done: snoozed card disappears and reappears after the interval (verifiable with a short test duration).
- **F15 Dismiss** — records reason; removable/restorable. Done: dismissed and restorable via F4.
- **F16 Confidence meter** — high/med/low color from thresholds.
- **F17 Q&A gift advisor** — flag-gated; when off, plain "Add gift task" still works. Done (flag on): 3 answers → tailored options → add task; (flag off): card still actionable.
- **F18–F20 Coaching/upsell/widget** — only with `ai_coach_enabled`. Done (flag off): entirely absent; (flag on): placeholders show upgrade path; price from config.
- **F21 Toasts** — every action confirms via `react-hot-toast`.
- **F22 Empty states** — per category + whole page; honest, no fabricated cards.

---

## 8. Testability plan (for real-estate testers, validated entirely through the UI)

This is the section that directly answers "testers are real-estate professionals, not developers — the whole thing must be validatable through the UI, and the end-to-end flow must not break."

### 8.1 Deterministic test fixtures (set up via the normal app UI, not SQL)
Provide a short **"AI Suggestions test script"** (a one-page checklist the tester follows in the running app) that *creates the real conditions* each MVP detector needs, using only normal app actions:

1. **Risk: financing contingency** — create a Buyer–Financing transaction with a financing/appraisal date ~3 days out; upload **no** lender commitment. → expect `risk.financing_contingency` (critical).
2. **Risk: stale comms** — on an active deal, ensure no client communication for > the cadence threshold. → expect `risk.stale_client_comms` (high).
3. **Risk: missing docs** — on a deal with an **open documentation/compliance task** (e.g. "Order Title", "Deliver HOA Docs") and **no matching uploaded document**, with close within window. → expect `risk.missing_required_docs` (high). *(Basis is incomplete tasks, not a "required-docs template" — internal deals don't model required docs; §5.1.)*
4. **Task: predicted missed** — add a task due in a few days, leave it not-started. → expect `task.predicted_missed`.
5. **Task: closing gift** — set a deal's `closing_date` ~21 days out. → expect `task.closing_gift` (low).
6. **Comms: referral / anniversary** — mark a deal closed with `completed_at` ~6 or ~12 months ago. → expect `comms.referral_request` / `comms.anniversary`.
7. **Relationship: review request** — active listing live ≥ N days with recent client comms. → expect `relationship.review_request`.

Each step lists the **exact expected card** (title, category, priority, confidence band) so the tester confirms by sight. Because detectors are deterministic, the same setup always yields the same cards — eliminating the "it worked yesterday, broke today" class of failure.

### 8.2 End-to-end action validation (click-through, no dev tools)
For each produced card the tester verifies the action **actually advances the deal**:
- **Send Email** → a **pending draft** appears in the deal's AI-email review (AI disclaimer + CC to the owner); **Approve & Send** moves it to the immutable communication log. *(Requires the new compose-draft endpoint — §5.2.)*
- **Add Task / Add Seller Call Task / Add gift task / Add to Calendar** → the task appears in My Task Queue and on the transaction's Tasks tab with the AI reason/confidence shown. *(Add-to-Calendar creates a dated task, not a Google/Outlook event.)*
- **Add to Template** *(as a TeamLead/Admin tester)* → a new deal of that type includes the task; an Agent/Elf tester sees the action disabled.
- **Schedule Text** → a **dated reminder task** appears for the target date *(true scheduled auto-send is Phase 3)*.
- **Send Text** → an SMS-channel entry is recorded in the communication log (or, if SMS disabled, the text is copied) — **no real SMS is transmitted in MVP**.
- **Copy to Clipboard** → pasting elsewhere yields the (possibly edited) draft text.
- **Snooze** → card leaves and returns after the interval; **Dismiss** → card leaves and is restorable via "Show dismissed".
- **Confidence gate** → a sub-threshold card (below `auto_proceed_threshold`) requires the "Confirm:" second click.

### 8.3 Honesty checks (the anti-fabrication gate)
- On a brand-new tenant with no deals: the page shows the whole-page empty state, **zero fabricated cards**, and the briefing reads an honest "nothing critical" state.
- Market/Marketing/Coaching categories are **absent** unless their flag/data is present (no sample cards).
- No card asserts data the platform cannot know (no MLS comps, no social activity, no review sentiment) unless that data is actually present.

### 8.4 Automated coverage (engineering, supports the manual pass)
- Unit tests per detector: given a constructed deal state → asserts the emitted row (or none). Dedup test: re-run → no duplicate.
- Accept-executor tests per `action_kind`: task created / template written / email draft queued (+CC +disclaimer) / schedule created / SMS-disabled 409 fallback.
- Confidence-gate test: sub-threshold accept returns `requires_confirmation`; `confirmed=true` executes.
- Role-scoping tests: Agent/Elf/TL/Admin/Attorney visibility (Admin = all; Attorney = legal-relevant only); Client/FSBO/Vendor 403; "Add to Template" allowed only for TL/Admin.
- Snooze sweep test: due rows return to pending.
- Front-end: render tests for each card/category/empty state; a Chrome-headless screenshot pass compared against the design for layout fidelity (per memory `ui-visual-verification-method`).

---

## 9. Phased delivery roadmap

**Phase 0 — Foundations (schema + config + scoping)**
- Migration §4. Confidence-config helper. Role-scoping + Attorney guardrails in the list endpoint. Briefing endpoint skeleton. *Exit:* API returns rich rows; roles enforced.

**Phase 1 — MVP detectors + accept executors**
- Implement the 8 MVP detectors (§5.1). Build the **new `POST /ai-emails/compose`** outbound-draft endpoint (no compose path exists today — §2.2). Implement accept dispatch for `add_task`, `add_to_template` (TL/Admin-gated), `send_email` (via the new compose-draft → existing approve/edit-&-send), `schedule_message` (dated task), `copy_text`, snooze, dismiss, act-all (safe kinds only). *Exit:* §8.1 fixtures produce the expected cards; §8.2 actions advance deals. | Add inline task name/due-date edit for task-type "Edit & Accept" (§10.6).

**Phase 2 — Full front-end rebuild to the design**
- Build all components §6.1, the §6.2 action map, confidence gate (no `window.confirm`), snooze UI, briefing + counters, category tabs, empty states, style-guide pass + screenshot compare. *Exit:* design functions F1–F16, F21, F22 demonstrably working on real data.

**Phase 3 — Flag-gated surfaces + learning loop + background generation**
- Build (gated, default off) coaching section/upsell/floating widget (F18–F20), gift Q&A advisor (F17), market/marketing/social detectors behind their flags. Wire the dismiss/feedback learning signal. Add background generation on transaction state-change + the snooze re-activation sweep (currently explicit/periodic). T1 pattern→template detector. *Exit:* placeholders appear only with flags; nothing fabricated when off.

**Phase 4 — Hardening**
- Full automated suite §8.4, performance (grouped query + indexes), accessibility audit, and a guided real-estate-tester walkthrough of §8. *Exit:* tester signs off end-to-end with no broken flow.

---

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Fabricated/mock cards reappear (the #1 historical failure) | Detectors emit only from real data; honest empty states; CI test asserts a fresh tenant yields zero cards; design sample content is never seeded. |
| Action buttons dead-end | Every `action_kind` has a verified executor and a §8.2 click-through test; copy-only actions are explicitly front-end. |
| "Send Email/Text" bypasses safeguards | Email routes through a **new compose-draft endpoint** → existing approve/edit-&-send (CC owner, disclaimer); SMS only **records** (no MVP delivery) with copy fallback (§6.3/§6.4/§6.7). |
| **"Send Email" assumed free but no outbound-draft endpoint exists** (verified) | Treat as explicit build item: `POST /ai-emails/compose` mints a pending draft; do not assume reuse. Phase 1 scope. |
| **"Add to Template" fails for agents** (verified `require_role(ADMIN, TEAM_LEAD)`) | Role-gate the action; disable with guidance for Agent/Elf; surface agent-personal-template as an un-built feature (Q7), not a silent dead-end. |
| **"Schedule Text" / "Add to Calendar" have no backing API** (verified) | Degrade both to **dated tasks** for MVP; document true scheduled-send / external calendar events as future work — never render a button that does nothing. |
| Coaching scoped as MVP again | Hard feature flag default-off; no coaching analysis logic built; price from config; documented as §12.10 non-MVP. |
| Confidence behavior diverges from config | Single confidence-config helper; gate + bulk both read team thresholds; risk cards always shown (§6.1). |
| Schema can't carry new state | Additive migration adds category/priority/action/draft/snooze before any UI work (Phase 0 first). |
| Snooze never re-surfaces | Status+`snoozed_until` + sweep, with a unit test; short test-duration for manual verification. |
| Design data the platform lacks (MLS/social/sentiment/benchmarks) | Flag-gated detectors; unverifiable claims suppressed; cards only when data present. |
| Attorney sees non-legal/legal-judgment suggestions | Engine filters categories for Attorney; no legal-equivalence assertions; releases stay human-owned (§8.6). |

---

## 11. Open questions for Jake (resolve before/within Phase 0)

1. **AI Coach price** — design shows **$49/agent/mo**, requirements §12.10 say **$79**. Which is canonical? (Until answered, the upsell stays flag-off and the number is config-driven.)
2. **Snooze re-surfacing** — confirm the durations (2h / Tomorrow / 1 week / 2 weeks) and whether a snoozed item should also drop a notification when it returns.
3. **"Send Text"** — is SMS expected to be live for any pilot tenant, or should "Send Text" always degrade to "Copy message" for MVP? (§6.7 hook vs active channel.)
4. **Closing-gift Q&A advisor** — is the 3-question advisor desired for MVP (behind a flag) or deferred entirely? The plain "Add gift task" works regardless.
5. **Cadence/window thresholds** — confirm the day-count thresholds for stale-comms, financing-contingency proximity, missing-docs window, gift window, referral/anniversary anchors (defaults proposed; easily configurable).
6. **Briefing "Draft action plan"** — should it open the existing AI chat with a pre-seeded prompt, or generate a static prioritized checklist? (Default: open AI chat seeded with the day's critical items.)
7. **Agent-personal task templates** — req §1.2a says agents "own personal task templates (unless on a team)", but the backend restricts `task-templates` writes to **Admin/TeamLead** and has no per-agent template. Should we (a) build agent-personal templates, or (b) ship MVP with "Add to Template" as **TeamLead/Admin-only** and hide it for agents? *(Plan assumes (b) until told otherwise.)*
8. **Outbound AI-email compose** — confirm the approach for "Send Email": new `POST /ai-emails/compose` that mints a pending draft for the existing review pipeline (recommended), vs. direct provider-send + log. *(Plan assumes the compose-draft approach to preserve §6.4 safeguards.)*

---

## 12. Summary

The page becomes a **deterministic, real-data intelligence inbox** that looks and behaves exactly like Jake's design, but where **every card is produced by an explainable detector over data the tenant actually has, and every action moves the real deal forward through a real (existing or explicitly-scoped-new), safeguarded endpoint.** MVP delivers Risk, Task, Communications, and Relationship intelligence end-to-end; Market, Marketing, and Coaching ship as flag-gated surfaces that stay invisible (with honest empty states) until their data or the AI-Coach add-on exists. Confidence, snooze, categories, roles, and the AI-email safeguards are all wired at the data layer first, so the front-end rebuild can be a faithful, unbreakable realization of the design — and a real-estate tester can validate every function by clicking, with nothing fabricated and nothing dead-ending.

---

## 13. Review corrections log (post-draft verification against source)

After the first draft, every capability claim was re-checked against the actual backend/frontend source. Nine logic/workflow errors were found and corrected in place; this log records each with its evidence so the reasoning is traceable.

| # | Original claim (wrong/over-stated) | Verified reality (evidence) | Correction applied |
|---|---|---|---|
| 1 | Allowed roles = "Agent, Elf, Team Lead, Attorney" (omitted Admin) | `App.tsx:123–124,567`: route uses `INTERNAL_AND_ATTORNEY = ['Agent','TransactionCoordinator','TeamLead','Admin','Attorney']`; SYSTEM_DESIGN matrix gives Admin = "All". (`FRONTEND_UI_WORKFLOW_LOGIC §6.1` omits Admin — doc bug.) | §2.1 now includes **Admin**; doc discrepancy noted. |
| 2 | "Add to Template" works for agents (personal template) | `task_templates.py:86–123,203–225`: `POST`/`PUT` are `require_role(ADMIN, TEAM_LEAD)`; create scopes to `team_id`/tenant — **no agent-personal template, agents can't write**. | §2.2/§5.2/§6.2/§7-F11/§8 now gate to **TL/Admin**; agent action disabled; agent-personal flagged as gap **Q7**. |
| 3 | "Send Email" reuses the existing AI-email pipeline | `ai_emails.py` (approve/edit-&-send/regenerate/discard) + `_send_draft` all operate on **pre-existing** drafts minted by the **inbound** auto-reply flow; **no compose-outbound-draft endpoint** (POST 441 = discard, not compose). | §2.2/§3-D3/§5.2/§6.2/§10/Q8: "Send Email" is **new backend work** (`POST /ai-emails/compose`), not reuse. |
| 4 | "Add to Calendar" → dated task "flows into calendar push" | `calendar.py:370–414`: `/calendar/push` pushes **transaction closings only**, not tasks; no arbitrary-event API. | §2.2/§6.2: "Add to Calendar" creates a **dated task** (in-app reminder); **no** Google/Outlook event in MVP. |
| 5 | "Schedule Text" → scheduled notification/communication | `notifications.py`: only `pending`/`mark-seen`/`preferences`/admin-cron; **no compose-and-schedule endpoint** for a future user message. | §2.2/§5.2/§6.2: degrades to a **dated reminder task**; true scheduled send = Phase 3. |
| 6 | Confidence fields = `{global_floor, team_ship_it, team_review}` | `confidence.py:29–62`: actual fields `global_min_floor` (0.75), `auto_proceed_threshold` (0.90), `review_threshold` (0.75); resolved team→tenant→global. | §3-D4/§5.4/§7-F13/§8.2 use the **real field names**. |
| 7 | `risk.missing_required_docs` keys off a "required-docs template" | Required-docs modeled **only for FSBO** (`fsbo_workspace.required_doc_types_for`); internal deals have no required-doc matrix. | §5.1/§8.1: detector keys off **incomplete documentation/compliance tasks** + missing matching document. |
| 8 | "Send Text" sends an SMS when enabled | `communication_logs.py:47` supports logging an SMS-channel entry, but **SMS delivery is a non-MVP provider hook** (§6.7); no provider wired. | §5.2/§6.2/§8.2: MVP **records/copies**, does not transmit; honest 409→copy fallback. |
| 9 | §10.6 "Edit & Accept" fully covered by inline draft edit | Inline draft (F10) covers *draft-bearing* cards, but **task-type** suggestions (T1/T3) have no field editor in the design. | Add (to §6.1 `SuggestionActionRow`/task-checklist) an inline **edit of task name/due-date** before accept so §10.6 "Edit & Accept" holds for task suggestions too. |

**Net effect on scope:** Phase 1 now explicitly includes one new backend endpoint (`/ai-emails/compose`) and a role-gate on template writes; three design actions (Add-to-Calendar, Schedule-Text, Send-Text) are honestly down-scoped to dated-task / record-only for MVP rather than implied as fully wired. None of these changes alter the page's look or the function inventory (F1–F22) — they make the *action layer* truthful, which is precisely what was breaking end-to-end testing before. Two new open questions (Q7 agent-personal templates, Q8 compose approach) are raised for Jake.
