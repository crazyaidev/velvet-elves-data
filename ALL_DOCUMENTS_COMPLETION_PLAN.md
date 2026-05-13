# All Documents Page Completion Plan

**Status:** Reviewed and revised for implementation  
**Owner:** Jan (sole dev)  
**Last updated:** 2026-05-13  
**Client design reference:** `velvet-elves-data/VE-New-AllDocuments.html`  
**Frontend root:** `velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx`  
**Backend roots:** `velvet-elves-backend/app/api/v1/documents.py`, `app/api/v1/dashboard.py`, `app/api/v1/communication_logs.py`

---

## 0. Review Findings And Corrections

The previous draft had the right direction, but several details would have produced rework or subtle UX bugs. These are the corrections this revision bakes into the plan:

1. **Route mismatch:** product docs call the page `/documents/all`, but the shipped frontend route is `ROUTES.DOCUMENTS = /documents`. Keep `/documents` as the canonical route for compatibility and add `/documents/all` as an alias/redirect.
2. **E-sign endpoint mismatch:** the implemented hooks use `/api/v1/documents/{id}/esign`, `/esign/status`, `/esign/sync`, and `/esign/void`, not `/api/v1/esign/send-for-signature`.
3. **`recently_cleared` naming mismatch:** the backend and frontend currently use `recently_done`. Keep that response field and let the UI label be "Cleared today."
4. **`hero_item` is redundant:** the backend already returns ranked `items[]` and `briefing.hero_id`; the frontend can derive the hero from that. Do not add a duplicate `hero_item` payload unless the ranking contract changes.
5. **`approve` must not write `documents.status = approved`:** `status` is the processing workflow field (`pending`, `processed`, `failed`, `archived`). Add a dedicated document review state instead.
6. **`flag` must not reuse the client deletion flag workflow:** existing `flag-deletion` is for Client/FSBO/Vendor deletion requests. The All Documents flag is an internal follow-up flag and needs a separate table/API.
7. **Requests and nudges are not clear events:** sending a request, nudge, forward, or call should log a "touch" and set next follow-up timing. It should not make the item look completed.
8. **Tab counts currently use two scopes:** the priority queue counts active-transaction docs; `useAllDocuments()` loads all visible docs. The final contract must make one backend source authoritative for badges.
9. **Search already exists globally:** `/api/v1/search` powers Cmd+K and document focus links. Do not build a parallel `/documents/search` endpoint unless page-scoped search becomes a separate product decision.
10. **Modal accessibility is incomplete:** the shared custom modal closes on Escape but does not fully trap focus or restore focus. This needs explicit work before calling the page complete.
11. **The AI note should never block page load:** enrich in the background with cache and rule fallback; do not make the queue wait on an LLM.
12. **MLS is deferred from MVP:** template generation must use existing transaction data and uploaded/parsed documents first. MLS enrichment remains a future enhancement.

---

## 1. Completion Goal

Jake's new design turns All Documents into an AI-led operating surface: the agent should see the most important document blocker, understand why it matters, and act without hunting through tables.

The page is partially shipped. The shell, hero, briefing, tabs, queue rows, modal, upload, preview, email, e-sign, versioning, rename, deletion approval, and silent e-sign sync are present. The unfinished work is making every displayed action durable, auditable, correctly scoped, accessible, and pleasant under failure.

Client/product decisions now locked:

- **Requests, nudges, forwards, and calls stay visible as touched items** until the underlying document requirement is actually resolved. This is the standard workflow pattern for follow-up queues: a touch changes recency and next follow-up timing, not completion state.
- **Global Cmd+K search is sufficient** for this milestone. Do not add a duplicate page-scoped search box.
- **Template generation ships without MLS** for MVP. Generate from transaction metadata, transaction parties, and parsed/uploaded documents.
- **AI never acts without human approval.** It may rank, recommend, draft, summarize, and prefill, but it must not automatically send, waive, approve, void, generate final documents, schedule follow-ups, or mutate workflow state without an explicit user action.

The completion bar is:

- No button is cosmetic.
- Every mutation persists or logs meaningful state.
- The queue, hero, briefing, tab badges, and recently-done strip reconcile after every action.
- The UI remains fast even when AI, email, DocuSign, or storage is slow.
- The implementation aligns with multi-tenant isolation and the existing FastAPI/React Query patterns.
- Every AI-assisted action has a human confirmation/click before it mutates data or contacts anyone.

---

## 2. Page Identity And Access

| Field | Decision |
| --- | --- |
| Canonical route | `/documents` |
| Alias route | `/documents/all` redirects or renders the same page |
| Page title | `All Documents` |
| Allowed product roles | Agent, Elf, Team Lead, Attorney, Admin |
| Actual enum roles | `Agent`, `TransactionCoordinator`, `TeamLead`, `Attorney`, `Admin` |
| External roles | `Client`, `ForSaleByOwner`, `Vendor` redirected away |
| Tenant scope | Repository-level tenant filters now; RLS policies authored for all new tables |

Frontend work:

- Add an alias route for `/documents/all` in `App.tsx`.
- Keep all nav links and global search hrefs pointing to `/documents` unless Jake explicitly wants the longer route.

---

## 3. Backend Response Contract

### 3.1 Priority Queue Endpoint

Keep the BFF endpoint:

`GET /api/v1/dashboard/documents-priority-queue`

Return:

```ts
{
  items: DocumentPriorityItem[],
  briefing: DocumentPriorityBriefing,
  recently_done: DocumentRecentlyDone[],
  tab_counts: DocumentTabCounts,
  generated_at: string
}
```

Required `DocumentPriorityItem` additions:

```ts
{
  id: string,              // display id, e.g. "missing:<tx_id>:lead_paint_disclosure"
  item_key: string,        // stable persistence key, same value for v1
  is_waived: boolean,
  is_flagged: boolean,
  last_touched_at: string | null,
  next_follow_up_at: string | null,
  last_action_label: string | null
}
```

Rules:

- `items[]` remains ranked by backend AI/rules.
- `briefing.hero_id` points to the hero; frontend derives the hero from `items`.
- `tab_counts` must be calculated from the same visible document corpus as the page. If the page shows all accessible tenant docs, the endpoint must count the same set.
- The AI priority tab is capped at 10 promoted items, but Missing can show all missing requirements.
- Waived items are excluded by default but can be included with a future `?include_waived=true` for audit/support.

### 3.2 Recently Done Contract

Keep response field name `recently_done`.

Each item:

```ts
{
  id: string,
  item_key: string,
  document_id: string | null,
  transaction_id: string,
  doc_label: string,
  transaction_address: string | null,
  relative_time: string,
  cleared_at: string,
  via_action: "upload" | "template" | "approve" | "waive" | "signed" | "replace" | "void",
  party_name: string | null
}
```

Only true resolution actions create recently-done rows. Requests, nudges, forwards, and calls are touches, not clears.

---

## 4. Data Model

Create one migration for the document-priority completion work.

### 4.1 Waivers

```sql
CREATE TABLE public.document_priority_waivers (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  transaction_id  UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
  item_key        TEXT NOT NULL,
  waived_by       UUID NOT NULL REFERENCES public.users(id),
  reason          TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at      TIMESTAMPTZ,
  revoked_by      UUID REFERENCES public.users(id),
  UNIQUE (tenant_id, transaction_id, item_key)
);
```

Use soft revoke instead of delete so Undo is auditable.

### 4.2 Internal Follow-Up Flags

Do not reuse `documents.deletion_flagged`.

```sql
CREATE TABLE public.document_followup_flags (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  document_id     UUID REFERENCES public.documents(id) ON DELETE CASCADE,
  transaction_id  UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
  item_key        TEXT,
  flagged_by      UUID NOT NULL REFERENCES public.users(id),
  reason          TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at     TIMESTAMPTZ,
  resolved_by     UUID REFERENCES public.users(id),
  UNIQUE (tenant_id, document_id, item_key)
);
```

### 4.3 Document Review State

Add explicit review columns to `documents`:

```sql
ALTER TABLE public.documents
  ADD COLUMN IF NOT EXISTS review_status TEXT NOT NULL DEFAULT 'unreviewed',
  ADD COLUMN IF NOT EXISTS reviewed_by UUID,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS review_note TEXT;

ALTER TABLE public.documents
  DROP CONSTRAINT IF EXISTS documents_review_status_chk;

ALTER TABLE public.documents
  ADD CONSTRAINT documents_review_status_chk
  CHECK (review_status IN ('unreviewed', 'approved', 'needs_follow_up'));
```

`approve` sets `review_status = 'approved'`. `flag` sets or implies `needs_follow_up`.

### 4.4 Priority Event Ledger

Use one event ledger for queue-affecting actions. It powers "Cleared today," last touch labels, next follow-up logic, and audit-friendly debugging.

```sql
CREATE TABLE public.document_priority_events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  transaction_id  UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
  document_id     UUID REFERENCES public.documents(id) ON DELETE SET NULL,
  item_key        TEXT NOT NULL,
  event_type      TEXT NOT NULL, -- touch | clear | flag | waive | unwaive | approve
  action_key      TEXT NOT NULL, -- request | nudge | call | upload | template | ...
  actor_id        UUID NOT NULL REFERENCES public.users(id),
  party_name      TEXT,
  note            TEXT,
  next_follow_up_at TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Rules:

- `touch`: request, nudge, forward, call.
- `clear`: upload that satisfies missing requirement, template generation, approve, signed webhook/sync, waive, replacement that resolves stale/in-flight item.
- `flag`: internal follow-up flag created.
- `waive` and `unwaive`: waiver state changed.
- All rows include `tenant_id`; add indexes on `(tenant_id, item_key, created_at DESC)` and `(tenant_id, event_type, created_at DESC)`.

### 4.5 RLS And Tenant Safety

For each new table:

- Add `tenant_id`.
- Add repository-level tenant filters immediately.
- Add RLS policies compatible with the multi-tenancy plan's `auth_tenant_id()` / `auth_is_platform_admin()` pattern.
- Add migration tests against local Postgres/Supabase for cross-tenant denial; mock tests alone are not enough for policy validation.

---

## 5. Endpoint Catalogue

Every visible action maps to this catalogue.

| Key | UI Label | Endpoint / Behavior | Persists | Clears Queue? |
| --- | --- | --- | --- | --- |
| `upload` | Upload | Existing `POST /api/v1/documents/upload` | document + audit + priority event if it satisfies an item | Yes when requirement satisfied |
| `request` | Request | Existing `POST /api/v1/documents/request`, add `tone` and `priority_item_key` | communication log + touch event | No |
| `resend` | Resend | Existing e-sign modal -> `POST /api/v1/documents/{id}/esign` | envelope + document sig fields + audit | No unless signed |
| `review` | Review | Existing signed download/preview | optional audit "viewed" | No |
| `approve` | Approve | New `POST /api/v1/documents/{id}/review/approve` | document review state + clear event + audit | Yes |
| `forward` | Forward | Existing `POST /api/v1/documents/{id}/email`, add `tone='forward'` | communication log + touch event | No |
| `void` | Void | Existing `POST /api/v1/documents/{id}/esign/void` | envelope status + document sig fields + audit + event | Usually yes for sent item |
| `replace` | Replace | Existing upload-new-version flow; avoid rename modal for "replace" | new version + audit + event | Yes when stale item resolved |
| `waive` | Mark N/A | New `POST /api/v1/documents/priority-waivers` | waiver + event | Yes |
| `unwaive` | Undo Mark N/A | New `POST /api/v1/documents/priority-waivers/{id}/revoke` or body by item_key | revoked waiver + event | Restores item |
| `template` | Generate | New `POST /api/v1/documents/generate-from-template` | generated draft document + event + audit | Yes after draft created |
| `call` | Call | `tel:` plus existing `POST /api/v1/communication-logs` with `channel='voice_call'` | communication log + touch event | No |
| `nudge` | Nudge | `POST /api/v1/documents/request` or `/email` with `tone='nudge'` | communication log + touch event | No |
| `flag` | Flag | New `POST /api/v1/documents/{id}/follow-up-flag` | follow-up flag + event + audit | No |
| `unflag` | Resolve Flag | New `POST /api/v1/documents/{id}/follow-up-flag/resolve` | resolved flag + audit | No |

Implementation notes:

- Use `item_key` in request bodies; avoid path-only keys for colon-heavy IDs.
- All mutation responses should include enough data for optimistic rollback or a precise refetch.
- Add an idempotency guard for double-clicks. At minimum, disable the active action button while its mutation is pending.
- Use one frontend helper, `invalidateDocumentsWorkspace()`, after every successful mutation:
  - `['dashboard', 'documents-priority-queue']`
  - all `QUERY_KEYS.DOCUMENTS(...)` variants, including all-pages
  - `QUERY_KEYS.DOCUMENT(documentId)` when applicable
  - transaction document lists
  - communication logs when a touch/email/call occurs

---

## 6. Action UX Rules

### 6.0 Human Approval Guardrail

The AI agent may recommend and prepare. The user acts.

The system must not automatically:

- send request, nudge, forward, SMS, or email messages;
- initiate calls or call-bridge workflows;
- waive/mark N/A;
- approve review items;
- void or resend e-sign envelopes;
- generate final documents;
- schedule or reschedule follow-ups;
- change document, transaction, task, party, or communication state.

Allowed without human approval:

- ranking the queue;
- showing "why" explanations;
- enriching non-authoritative AI notes;
- pre-filling message/template forms;
- suggesting next follow-up timing.

Any generated draft must be shown to the user before sending or saving as an official workflow action.

### 6.1 Optimistic Actions

Optimistic:

- `waive`: remove row immediately; Undo toast revokes waiver.
- `flag`: show flag glyph immediately; rollback if API fails.
- `approve`: flip review status immediately; rollback if API fails.

Server-confirmed:

- `upload`, `template`, `request`, `resend`, `forward`, `nudge`, `call`, `void`, `replace`.

### 6.2 Request/Nudge/Call Follow-Up Behavior

After a touch action:

- Keep the row visible if it is still unresolved.
- Add a calm line such as `Requested today` or `Called 12m ago`.
- Set `next_follow_up_at` using defaults:
  - critical: 24 hours
  - high: 48 hours
  - medium/low: 72 hours
- Within the same severity band, items with a fresh touch sort below untouched items until follow-up is due.

This is more convenient than hiding the item and more honest than pretending it is cleared.

### 6.3 Toast Copy

- Start immediately with present-tense feedback: `Sending Request`, `Marking N/A`, `Logging Call`.
- Finish with specific completion: `Request Sent`, `Marked N/A`, `Call Logged`.
- Failures use destructive toasts and preserve the row.
- Avoid "Done!" and vague apology copy.

---

## 7. Frontend Work

### 7.1 Route And URL State

- Add `/documents/all` alias.
- Initialize `activeTab` from `?tab=`.
- Persist tab changes to `?tab=`.
- Add `sort` state from `?sort=`.
- Preserve current global search focus behavior: `/documents?focus=<doc_id>&tx=<tx_id>`.

### 7.2 Sort Dropdown

Replace the static sort chip with the already-imported `DropdownMenu`.

Options:

- `AI impact` (default for AI priority)
- `Close date`
- `Document name`
- `Recently updated`
- `Last touched`

Sorting is client-side over the currently loaded arrays. No new backend call is needed for v1.

### 7.3 Tab Counts

Final contract:

- Backend `tab_counts` is authoritative.
- The backend must count the same document scope the page renders.
- Until that backend fix lands, keep the current client recompute as a temporary defensive fallback, but mark it with a TODO and remove it once the endpoint is corrected.

### 7.4 Action Hooks

Add hooks:

- `useWaivePriorityItem()`
- `useRevokePriorityWaiver()`
- `useApproveDocumentReview()`
- `useFlagDocumentFollowup()`
- `useResolveDocumentFollowupFlag()`
- `useGenerateDocumentFromTemplate()`
- `useLogCommunication()` or extend the existing communication-log hook for one-off call logging.

Update `runItemAction`:

- `approve` calls review approve, not preview.
- `flag` persists follow-up flag, not just toast.
- `waive` persists waiver, not session-only set state.
- `template` generates a draft document, then opens preview of the draft.
- `call` logs a voice-call communication row after launching `tel:`.
- `forward` and `nudge` pass `tone` into the email/request modal.
- `replace` opens version upload, not the rename modal.

### 7.5 Request/Email Tone

Extend request/email payloads with:

```ts
tone: 'request' | 'nudge' | 'forward'
priority_item_key?: string
```

Copy rules:

- Use first-person singular where client-facing copy speaks for the agent: "I" rather than "we."
- `request`: clear, professional ask.
- `nudge`: shorter follow-up with a prior-touch reference when available.
- `forward`: attachment-forwarding language, not a missing-doc request.
- If no provider is connected, keep the existing queued/logged behavior and explain it calmly.

### 7.6 Hero And Briefing

- Use `briefing.hero_id` if present; fallback to `items[0]`.
- Make the "other docs flagged - briefing" link scroll to the briefing card.
- Critical hero address uses the red text token, not a raw hex.
- Briefing footer uses backend `footer_hint`, derived from priority events and average days saved, not hardcoded copy.

### 7.7 Recently Done

- Render `via_action` badge: Signed, Approved, Marked N/A, Generated, Replaced, Voided.
- Click opens preview only when `document_id` exists.
- For waiver-only events, click opens the priority detail/audit view instead of a dead preview.

### 7.8 Accessibility

- Keep queue rows as `div role="button"` or convert to a non-nested accessible row pattern; do not put buttons inside a native `<button>`.
- Every icon-only action keeps `aria-label`.
- Replace custom modals with Radix `Dialog` or add focus trap, initial focus, Escape close, overlay click close, and focus restoration.
- Keyboard path must work: Tab to row, Enter opens modal, Tab to primary action, Enter runs action, Escape closes modal.
- Use `<AlertDialog>` for destructive confirmations; no `window.confirm()`, `window.alert()`, or `window.prompt()`.

---

## 8. Backend Work

### 8.1 Dashboard Priority Queue

Update `dashboard_documents_priority_queue` to:

- Load waivers, flags, review state, and priority events for the visible transaction/document scope.
- Exclude active waivers.
- Include `item_key`, `is_flagged`, `last_touched_at`, `next_follow_up_at`, and `last_action_label`.
- Sort fresh touches below untouched items inside the same severity band until follow-up is due.
- Build `recently_done` from `document_priority_events.event_type = 'clear'`.
- Return tab counts from the same scope as `/api/v1/documents`.
- Do not perform side effects inside the GET handler.

### 8.2 Documents API

Add:

- `POST /api/v1/documents/priority-waivers`
- `POST /api/v1/documents/priority-waivers/revoke`
- `POST /api/v1/documents/{id}/review/approve`
- `POST /api/v1/documents/{id}/follow-up-flag`
- `POST /api/v1/documents/{id}/follow-up-flag/resolve`
- `POST /api/v1/documents/generate-from-template`

Enhance:

- `POST /api/v1/documents/request` accepts `tone` and `priority_item_key`.
- `POST /api/v1/documents/{id}/email` accepts `tone` and `priority_item_key`.
- Existing e-sign send/sync/void handlers create priority events when they change queue state.

### 8.3 Template Generation MVP

Do not depend on MLS for MVP.

Generate from:

- `transactions` metadata
- `transaction_parties`
- uploaded/parsed documents (`ai_extracted_data`)
- approved template assets checked into the backend or stored in a controlled bucket

Constraints:

- Generated docs are marked `review_status='unreviewed'` and `acceptance_status='draft'`.
- UI copy must make it clear the draft needs human review before sending.
- If a template cannot fill required fields, return a structured missing-fields response and keep the row unresolved.

### 8.4 AI Note Enrichment

Add `app/services/document_priority_ai_notes.py`.

Rules:

- Never block the queue response on the LLM.
- Return rule-based notes immediately.
- For critical/high items only, enqueue one background enrichment per request.
- Use tenant-configured AI provider through `AIService`.
- Batch all eligible items into one model call.
- Cache by `tenant_id + item_key + content_hash` for 6 hours.
- Store provider name, model name if available, token estimate/cost if available, and generated timestamp.
- On provider failure, keep rule text and log a warning only.
- Frontend may silently invalidate the priority queue once after a short delay, mirroring the transaction-card AI refresh pattern.

---

## 9. Search Plan

Current global search is the correct short-term surface:

- `GET /api/v1/search?q=...&types=document`
- document hit href: `/documents?focus=<doc_id>&tx=<tx_id>`

Completion tasks:

- Keep the topbar search wired to Cmd+K/global search.
- Improve document search scoring to include transaction address and party names when practical.
- Defer full document-content/vector search to Phase 5+.
- Do not add page-scoped `?q=` search in this milestone.

---

## 10. Edge Cases

| Case | Required Behavior |
| --- | --- |
| User waives the hero item | Hero re-renders from next ranked item; Undo toast can restore it |
| Two users waive same item | Unique constraint makes second call idempotent; return 200 with existing waiver |
| Request sent for missing doc | Row remains visible with `Requested today`; next follow-up date is set |
| Generated template lacks required fields | Show missing-fields modal; no clear event |
| Doc deleted in another tab | Toast "This document was removed elsewhere"; refetch queue/docs |
| Provider not connected for e-sign | Open connect wizard; retry send after success |
| Email provider not connected | Log request as queued; tell user future requests send after connecting email |
| PII decrypt fails | Show safe generic labels; never leak ciphertext |
| No active transactions | Hero/briefing show clear state; All Docs can still show closed/unassigned docs |
| Large document library | All Docs tab relies on paginated `useAllDocuments`; future server-side pagination/search required past 10k safety cap |
| Attorney role | Template generation hidden unless template is attorney-approved/legal-packet safe |
| TransactionCoordinator role | Delete hidden; flag/waive/request allowed within assigned scope |

---

## 11. Test Plan

### Backend

- `test_priority_queue_returns_item_key_and_excludes_active_waivers`
- `test_waive_is_idempotent_and_tenant_scoped`
- `test_unwaive_restores_item_and_logs_event`
- `test_request_logs_touch_but_not_clear_event`
- `test_call_logs_voice_communication_and_touch_event`
- `test_flag_creates_followup_flag_not_deletion_flag`
- `test_resolve_flag_removes_is_flagged`
- `test_approve_sets_review_status_and_clear_event`
- `test_template_generation_creates_draft_or_missing_fields_response`
- `test_recently_done_reads_clear_events_for_signed_approve_waive_template`
- `test_tab_counts_match_documents_endpoint_scope`
- `test_priority_ai_note_cache_hit_skips_provider_call`
- RLS integration tests for new tables against local Postgres/Supabase

### Frontend

- `DocumentsPage honors ?tab and ?sort on first render`
- `DocumentsPage /documents/all alias renders the same page`
- `waive removes row optimistically and Undo restores after revoke`
- `request keeps row visible and shows Requested today`
- `flag persists across refetch with flag glyph`
- `approve flips review state and invalidates queue/docs`
- `sort dropdown reorders without API call`
- `tab badges use backend counts once scope fix lands`
- `PriorityDetailModal renders all alt_actions`
- `PriorityDetailModal renders fallback text when ai_note is null`
- `nudge and forward use distinct subjects/body copy`
- `call action posts voice_call communication log`
- Keyboard-only modal/action path works

### E2E

One Playwright path:

1. Log in as Agent.
2. Open `/documents`.
3. Click hero primary request.
4. Send request.
5. Toast appears.
6. Row remains with a "Requested today" touch state.
7. Mark the same item N/A.
8. Row leaves queue.
9. Briefing count decreases.
10. Cleared Today shows a Marked N/A card.
11. Undo restores row.

---

## 12. Rollout Sequence

### Slice 1 - Persistence And Reconciliation (2-3 days)

- Migration for waivers, follow-up flags, review state, priority events.
- Waive/unwaive, approve, flag/unflag endpoints.
- Priority queue joins persisted state.
- Shared frontend invalidation helper.
- Frontend wiring for waive, approve, flag.
- Backend + focused frontend tests.

### Slice 2 - Communication Touches And URL Controls (2 days)

- Add touch events for request, nudge, forward, call.
- Add `tone` and `priority_item_key` to request/email payloads.
- Log calls through `/communication-logs` as `voice_call`.
- URL-backed `tab` and `sort`.
- Real sort dropdown.
- `/documents/all` alias.

### Slice 3 - Template Generation MVP (2-3 days)

- Generate from existing transaction/party/parsed data.
- Return missing-fields response when draft is incomplete.
- Store generated draft as a document.
- Preview generated draft after success.
- Mark generated docs as draft/unreviewed.

### Slice 4 - AI And Polish (2 days)

- Background AI note enrichment with 6h cache.
- Dynamic briefing footer from priority events.
- Recently Done badges/click behavior.
- Modal focus trap/restoration.
- Final visual pass against `VE-New-AllDocuments.html` and `STYLE_GUIDE.md`.

Each slice ends with tests passing and a short dev deployment check on the All Documents flow.

---

## 13. Jake Defaults

Unless Jake says otherwise:

1. UI label is **Mark N/A**; internal action key remains `waive`.
2. Flagged items stay in place with a glyph and do not jump above higher-severity work.
3. Requests, nudges, forwards, and calls stay in the queue as touched items until the requirement is actually resolved.
4. Template generation uses existing transaction data, parties, key dates, and parsed/uploaded documents; MLS enrichment is deferred.
5. AI note refresh uses 6h TTL and never blocks the page.
6. AI never sends, approves, waives, voids, schedules, or mutates workflow state without explicit human approval.
7. Sort options are AI Impact, Close Date, Document Name, Recently Updated, Last Touched.
8. Search remains global Cmd+K for this milestone; no duplicate page-scoped search box.

---

## 14. Definition Of Done

The page is complete when:

- Every action in Jake's design has a real endpoint or logged side effect.
- Refreshing the page never loses waive/flag/approve/template/call/request state.
- Counts, hero, queue, briefing, and recently-done strip reconcile after mutations.
- No action creates cross-tenant visibility.
- No action silently fails.
- The page works by keyboard.
- No modal uses native browser confirm/alert/prompt.
- Template generation does not promise MLS data before MLS exists.
- No AI-generated draft or recommendation becomes an official action without human approval.
- AI notes enrich the page without adding visible latency.
- `/documents` and `/documents/all` both work.
