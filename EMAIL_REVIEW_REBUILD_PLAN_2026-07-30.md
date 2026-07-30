# Intelligence › Email review — remediation and rebuild plan

**Date:** 2026-07-30
**Inputs:** `EMAIL_REVIEW_ISSUES_2026-07-30.md` (E-01…E-20),
`EMAIL_REVIEW_E2E_TEST_REPORT_2026-07-30.md`
**Status: IMPLEMENTED 2026-07-30.** All seven phases are built and verified.
See `EMAIL_REVIEW_IMPLEMENTATION_REPORT_2026-07-30.md` for what shipped, what
was verified how, and the two items that still need a person.

---

## 0. The decision this plan rests on

The current page is a **queue of AI drafts**. The user needs an **inbox filtered
to transaction mail**. Those two things have different units of display, so no
amount of threshold tuning closes the gap: a message the engine declines to
answer has no row to appear in, and a message it wrongly answers looks exactly
like real work.

So the plan changes the unit. **The row becomes the message; the draft becomes
an attribute of the message.** Everything relevant is visible whether or not
the AI had something to say about it, and everything filtered out is visible on
demand so the filter can be audited and corrected.

Three principles carried through every phase:

1. **Precision before recall, then earn recall back.** Better to show a
   coordinator six real emails than sixty maybes. Recall is recovered through
   the "Filtered out" tab and the feedback loop, not by loosening the gate.
2. **Every filter decision is inspectable and reversible by the user.** No
   silent drops. A skipped message is one tap from being restored, and the tap
   teaches the system.
3. **Relevance and reply-worthiness are separate questions.** "This matters to
   your deal" and "the AI has a reply for you" are decided independently and
   displayed independently.

---

## 1. Phase map

| Phase | Title | Closes | Effort | Depends on |
| --- | --- | --- | --- | --- |
| 0 | Restore a testable inbound path | — | 0.5 d + owner action | — |
| 1 | Triage funnel before persistence | E-01, E-02, E-03, E-04 | 3 d | 0 |
| 2 | Intent model that admits statements | E-05, E-16 | 2 d | 1 |
| 3 | Deal matching on human phrasing | E-06, E-07, E-20 | 2.5 d | — |
| 4 | The correction loop | E-08, E-10 | 2 d | 1, 3 |
| 5 | Rebuild the surface | E-09, E-11, E-13, E-15, E-19 | 6 d | 1–4 |
| 6 | Queue hygiene | E-12, E-14, E-17, E-18 | 2 d | 5 |
| 7 | Regression corpus + telemetry | proves all of it | 1.5 d | 1–3 |

**~19.5 developer-days.** Phases 1–4 are the user's actual complaint and are
worth shipping before the rebuild lands; Phase 5 is what makes the page good.

---

## Phase 0 — Restore a testable inbound path

Gmail push is dead locally: `EMAIL_WEBHOOK_PUBLIC_BASE_URL` and
`PUBSUB_PUSH_AUDIENCE` in `velvet-elves-backend/.env` point at a retired ngrok
tunnel. Every finding in this plan was produced by calling
`dispatch_inbound_email` directly, which is faithful but cannot exercise the
Gmail-side label filtering that Phase 1 introduces.

1. Stand up a stable tunnel (a reserved ngrok domain, or Cloudflare Tunnel —
   ngrok's rotating URL is why this breaks repeatedly).
2. Update both env values and restart the backend (`.env` is read by absolute
   path at startup; `--reload` does not re-read it — see
   `backend-env-loaded-by-absolute-path-restart-to-apply`).
3. **Reconnect Gmail.** The notification URL is baked into the watch, so an env
   change alone does nothing.

**Owner action, not developer action:** step 3 needs the mailbox owner. Google
verification also still gates the 7-day watch expiry
(`gmail-watch-no-renewal-inbound-dead`).

---

## Phase 2 is where the user's complaint is fixed — read Phases 1–4 as one unit

### Phase 1 — A triage funnel that runs *before* persistence

Replace the single `_is_transaction_related` call with an explicit, ordered
funnel in a new `app/services/email/inbound_triage.py`. Each stage returns a
verdict *and a reason string* that is persisted and shown to the user.

```
Stage 0  provider narrowing      → never fetched
Stage 1  hard drop               → stub row only, no body
Stage 2  known-party accept      → full store, linked
Stage 3  content relevance       → full store or stub
Stage 4  persistence policy      → write
```

**Stage 0 — narrow at Gmail.** `gmail_watch_label_ids` is `INBOX`
(`app/core/config.py:271`). Gmail's watch API supports
`labelFilterBehavior: EXCLUDE`, already plumbed through
`register_watch` (`gmail_provider.py:732-739`). Register with
`EXCLUDE` on `CATEGORY_PROMOTIONS`, `CATEGORY_SOCIAL`, `CATEGORY_FORUMS`,
`SPAM`, `TRASH`. This removes the bulk of the firehose at zero cost and
without us ever holding the data. Offer a per-user override for the
coordinators who file transaction mail into a dedicated label.
*Closes the ingestion half of E-01.*

**Stage 1 — hard drops.** Extend `_is_auto_generated`
(`ai_email_engine.py:156-179`) into a proper bulk detector:

| Signal | Action |
| --- | --- |
| `List-Unsubscribe` / `List-Unsubscribe-Post` present | drop |
| `List-Id` present | drop |
| `Precedence: bulk\|junk\|list` | drop (existing) |
| `Auto-Submitted` ≠ `no` | drop (existing) |
| `X-Auto-Response-Suppress`, `Feedback-ID` | drop |
| no-reply-shaped sender local part | drop (existing) |
| `text/calendar` part with no prose | drop |

Hard drops are *not* silent: they write a stub row (see Stage 4) and appear in
the **Filtered out** tab. *Closes E-03.*

**Stage 2 — known-party accept.** The single highest-precision signal in the
system is not being used for relevance at all: does the sender (or anyone on
cc) match a `transaction_parties.email`, a `contacts.email`, or a
`vendors.email` in this tenant? `_candidate_transaction_ids_for_party_emails`
(`inbound_dispatch.py:656-712`) already computes this — for *matching*. Promote
it to a relevance verdict: **a known party is always relevant, whatever the
content**, and it arrives pre-linked to the deal. A one-word "ok" from the
buyer must never be filtered.

**Stage 3 — content relevance, rebuilt.** For the remainder:

- **Delete the footer-address rule.** `_ADDRESS_SIGNAL_RE`
  (`ai_email_engine.py:184-189`) may only fire on an address found *outside* a
  detected signature/footer block, and only when it also matches a deal in the
  tenant (Phase 3). A street address that matches no deal is not a signal.
  *Closes E-02.*
- **Split the term list into tiers.** `_TRANSACTION_SIGNAL_TERMS`
  (`ai_email_engine.py:133-145`) becomes: **strong** multi-word phrases
  ("closing disclosure", "earnest money", "title commitment", "settlement
  statement", "final walkthrough") that stand alone; **weak** single words
  ("title", "listing", "loan", "commission", "buyer", "seller") that only
  count in combination and never alone. *Closes E-04.*
- **The AI check becomes the arbiter, not the fallback.** Today the
  deterministic path short-circuits it. Invert: deterministic signals decide
  only the confident ends; the ambiguous middle always asks the model. Cache
  the verdict per `(tenant, sender domain)` for 30 days so cost stays flat and
  a newsletter is judged once, not weekly.
- **Fail closed.** Provider down + no strong signal → not relevant, stub row,
  visible in **Filtered out**. Today it also returns `False`
  (`ai_email_engine.py:890`) but invisibly.

**Stage 4 — persistence policy.** `dispatch_inbound_email`
(`inbound_dispatch.py:134-157`) currently stores everything. Change to:

| Verdict | Stored |
| --- | --- |
| relevant | full row as today |
| not relevant | **stub**: `provider_ref_id`, sender, subject, received-at, triage reason, retention 30 d. **No body, no body_html.** |

De-duplication keeps working (it keys on `provider_ref_id` and a fingerprint),
"Filtered out" has something to render, and the tenant stops accumulating the
user's personal correspondence. *Closes the storage half of E-01.*

Add to the schema: `triage_verdict`, `triage_reason`, `triage_score`,
`triage_source` (`rule` / `ai` / `party` / `user`) on `communication_logs`.
Everything downstream — the UI, the corpus harness, the telemetry — reads these.

---

### Phase 2 — An intent model that admits statements

`_classify` (`ai_email_engine.py:802-867`) recognises question shapes and
returns `KIND_OTHER` for everything else, and `handle_inbound` bails on
`KIND_OTHER` at line 288. That is why "The title commitment is ready" vanished.

**Separate the two questions.** Relevance (Phase 1) decides whether the message
appears. Intent decides what we *do* with it:

| Intent | Appears | Draft? |
| --- | --- | --- |
| `question` | yes | reply draft |
| `document_request` | yes | reply draft + attachment |
| `document_delivery` ("report attached") | yes | acknowledge + file the doc |
| `schedule_change` ("closing moved to the 14th") | yes | acknowledge + propose task/date change |
| `status_update` ("appraisal came in at $312k") | yes | no reply needed — mark as read-and-file |
| `money` (wire instructions, EMD, payoff) | yes, **pinned** | never auto-draft; always flagged |
| `vendor_reply` | yes | existing proposal flow |
| `fyi` | yes, low priority | no draft |

Two rules that matter:

- **`KIND_OTHER` stops being a drop.** A relevant message with no recognised
  intent is `fyi` — it appears with no draft, which is an honest outcome.
  *Closes E-05.*
- **Money-shaped mail never gets an auto-draft** and carries a standing
  wire-fraud warning in the reading pane. This is the one category where a
  confident AI reply is a liability.

Regenerate (E-16) becomes intent-aware: on a message the user has marked
irrelevant it offers "not relevant — filter this sender" instead of rebuilding
the same draft.

---

### Phase 3 — Deal matching that survives human phrasing

`_transaction_text_match_score` (`inbound_dispatch.py:821-861`) with its
`>= 8` threshold (`:774`) cannot match "8104 Riverstone Place" because
`transactions.address` stores the composed `"street, city, ST, zip"`, so the
`+10` exact-substring rule needs the sender to paste all four parts.

1. **Match on components, not the composed string.** Parse the transaction
   address once into `{street_number, street_name, unit, city, state, zip}` and
   score against those. Anchor on **street number + street name** — that pair
   alone is a strong match; city/state/zip become confirmations, not
   requirements. *Closes E-06.*
2. **Drop the bare state point** (`inbound_dispatch.py:840`). "IN" and "OH" are
   English words. *Closes E-07.*
3. **Use the thread key.** `thread_key` is already stamped on every inbound
   (`inbound_dispatch.py:118-124`). If any earlier message on the same thread is
   linked to a deal, this one inherits it. This is exact, free, and currently
   unused for matching.
4. **Add a subject-line pass** for `Re:` chains that quote the address only in
   the subject.
5. **Ambiguity asks rather than guesses.** Two candidates within one point →
   `unmatched` with `candidates: [...]` recorded, and the UI shows a two-option
   "Which deal?" chip. Better a one-tap question than a wrong file.
6. Backfill: legacy `transaction_id = NULL` composed task drafts (E-20) get a
   one-off reconciliation from `ai_source_data.task_id`, and unfixable ones are
   discarded rather than left sendable.

---

### Phase 4 — The correction loop

Two actions, both one tap, both teaching.

**"Not mail I need"** — new endpoint `POST /ai-emails/inbound/{id}/not-relevant`:

- discards any draft,
- moves the message to **Filtered out**,
- writes an `inbound_suppression_rules` row scoped to the tenant, keyed by
  sender address, sender domain, or `List-Id` (the user picks the scope in the
  confirm: *this sender* / *everyone at this domain* / *this mailing list*),
- is **undoable** for 30 days, and every rule is listed and editable in
  Settings → AI & Automation.

Stage 1 of the funnel consults these rules first. *Closes E-08.*

**"File to deal"** — surfaces the existing
`POST /ai-emails/inbound/{log_id}/refile` (`ai_emails.py:272-353`), which
already re-points the log, writes `inbound_sender_deal_links` so the sender
auto-files next time, and re-drafts against the right deal. It needs a deal
picker in the row and in the reading pane, nothing more. *Closes E-10 — and
note the tooltip at `AiEmailReviewPage.tsx:836` already promises this action.*

Both write an audit entry via `log_ai_email_action`, so the filter's behaviour
is explainable after the fact.

---

## Phase 5 — Rebuild the surface

**Name:** `Intelligence › Inbox`, nav label `Inbox`. One name everywhere.
*Closes E-17.* Route `/inbox`, with `/ai-emails` redirecting.

### 5.1 Structure

Three regions on desktop, push-navigation on mobile:

```
┌──────────────┬────────────────────────┬──────────────────────────────┐
│ Views + deals│ Message list           │ Conversation                 │
│              │                        │                              │
│ Needs you  6 │ ● Sarah Chen      2h   │  [thread, oldest → newest]   │
│ Waiting     3│   Oak Ridge · Question │                              │
│ All        24│   "when do we close?"  │  Facts the AI used           │
│ Filtered   87│ ─────────────────────  │  Check these before sending  │
│              │ ○ Title Co        4h   │                              │
│ ── Deals ──  │   Riverstone · Doc     │  [ Approve & send ] [ Edit ] │
│ Oak Ridge  3 │   "commitment ready"   │  [ Reply myself ] [ File to ]│
│ Riverstone 2 │ ─────────────────────  │  [ Not mail I need ]  [ Done]│
│ Unlinked   1 │ ⚑ Escrow          6h   │                              │
└──────────────┴────────────────────────┴──────────────────────────────┘
```

**Views** (segmented, not tabs-that-show-the-same-rows — the 2026-07-10 mistake):

- **Needs you** *(default)* — relevant mail that is unread, unanswered, or has
  a draft waiting. This is the "only what I actually need" the user asked for.
- **Waiting** — we replied, awaiting their response. Ages visibly.
- **All** — every relevant message, threaded.
- **Filtered out** — everything triage rejected, with its reason and a
  one-tap **"Actually, I need this"**. This is what makes an aggressive filter
  safe to ship, and it is the answer to E-09: nothing is invisible, it is
  merely out of the way.

**Deal rail** — counts per deal, plus **Unlinked** pinned at top with the
"Which deal?" resolution flow from Phase 3. *Closes E-19.*

### 5.2 The row

`● Sarah Chen · 2h` / `Oak Ridge Ave · Question` / snippet / state chip.

State chip is honest about what the AI did:
`Reply ready` · `Needs your reply` · `No reply needed` · `Waiting on them` ·
`Not linked`.

### 5.3 Ordering — replace escalation-first

Priority 0 for `escalated` (`AiEmailReviewPage.tsx:100-108`, sort at
`:1142-1149`) means the nine stalest drafts outrank new client mail. Replace
with a real urgency model, highest first:

1. money / wire-instruction mail
2. a deadline or closing-date change
3. explicitly asked a question, unanswered > 24 h
4. unlinked but relevant (needs a human decision)
5. draft ready to send
6. everything else, newest first

Staleness stops being a rank and becomes a **badge on the row** ("waiting 9
days"), which is what the user actually needs to see. *Closes E-11.*

### 5.4 The conversation pane

- **Full thread**, oldest → newest, not just parent + draft. `thread_key`
  already groups it and `_thread_history` already loads it for the model — the
  reader deserves the same view.
- Keep verbatim: the sandboxed HTML frame, the assumptions panel, the "Facts
  the AI used" rail, the `body_preview_only` honesty notice. These are the best
  parts of the current page.
- **Editable recipients.** To / Cc / Bcc become real inputs; attachments can be
  picked from the deal's documents. The backend already accepts `cc` in
  `EditAndSendRequest` — the UI has simply never sent it. *Closes E-13.*
- Action bar: `Approve & send` · `Edit` · `Reply myself` · `File to deal` ·
  `Not mail I need` · `Mark done`.

### 5.5 Bulk actions

Explicit checkbox selection with a live count, and a confirm that names the
recipients. Never a context-free "Send all ready" — that was E2E finding I-04
and the shape of it should not return. Bulk **file to deal**, bulk **not
relevant**, and bulk **mark done** are the high-value ones; bulk send stays
deliberately awkward.

### 5.6 Mobile

`grid-cols-1 lg:grid-cols-[340px_1fr]` in an `h-full` shell
(`AiEmailReviewPage.tsx:1299`) clips both panes at 390 px. Replace with
push navigation: list fills the viewport, tapping a row slides in the
conversation with a back control, action bar pinned to the bottom. Views become
a select; the deal rail becomes a sheet. *Closes E-15.*

### 5.7 Keyboard and accessibility

`j`/`k` move, `Enter` open, `e` mark done, `r` reply, `f` file to deal,
`!` not relevant, `/` search, `?` shortcut sheet. Rows are already focusable
buttons; add roving tabindex, `aria-live` on the count, and visible focus rings
throughout.

---

## Phase 6 — Queue hygiene

- **E-12 duplicates.** Extend the `find_open_task_draft` idempotency
  (`ai_email_engine.py:576-612`) to every compose path via a natural key —
  `(tenant, transaction, recipient, template/intent, day)` — not just the ones
  passing `task_id`. Add a DB partial unique index so it holds under
  concurrency, and reconcile the existing ×4 / ×2 / ×2 groups.
- **E-14 pagination.** `list_pending_ai_drafts`
  (`communication_log_repository.py:272-294`) takes `limit`/`cursor`; the list
  virtualises and pages at 50. Counts come from a `count` query, not
  `items.length`.
- **E-18 staleness.** A draft older than 7 days, or one quoting a date now in
  the past, shows a "facts may have changed — regenerate before sending"
  banner, is excluded from bulk send, and auto-expires at 30 days with a
  notification. The current top row — asking for a document named `"test"` by
  a date five weeks gone — is exactly what this prevents.
- **E-17 naming** — applied in Phase 5.

---

## Phase 7 — Prove it, and keep it proved

The corpus written for this test becomes a checked-in regression fixture:
`app/tests/fixtures/inbound_corpus.jsonl`, ~120 labelled messages (real
transaction mail, newsletters, receipts, social, personal, adversarial edges,
plus every message from this run).

`app/tests/test_inbound_triage.py` asserts against it:

| Metric | Target | Today |
| --- | --- | --- |
| Precision on "shown to the user" | ≥ 0.95 | 0.20 on the junk subset (4 of 5 junk drafted) |
| Recall on genuine transaction mail | ≥ 0.98 | 0.67 (2 of 3 statement-shaped mails dropped) |
| Known-party mail shown | 1.00 | not evaluated as a rule today |
| Money-shaped mail auto-drafted | 0.00 | not modelled |

CI fails the build on regression. Ship telemetry for the same numbers per
tenant (`triage_verdict` + `triage_source` make this a group-by), so the filter
can be tuned on evidence rather than on the next complaint.

---

## 8. Sequencing

**Ship in three releases.**

- **R1 — "stop the noise" (Phases 0–2, ~5.5 d).** Provider-level exclusion,
  the bulk-header drops, the known-party accept, the footer-address fix, and
  statements stop vanishing. On this run's corpus that alone takes the junk
  drafts from 4-of-5 to 0-of-5 and recovers both dropped transaction emails.
  This is the release the user is waiting for.
- **R2 — "make it correctable" (Phases 3–4, ~4.5 d).** Matching on human
  phrasing, "File to deal", "Not mail I need". The system starts improving with
  use instead of repeating itself.
- **R3 — "make it good" (Phases 5–7, ~9.5 d).** The rebuilt surface, hygiene,
  regression corpus.

**Do not defer Phase 1 Stage 4 (the stub-row policy) past R1.** Every day the
current code runs against a live personal mailbox, it copies more of that
mailbox into the tenant database.

---

## 9. Decisions needed before R1

| # | Question | Who | Default if unanswered |
| --- | --- | --- | --- |
| 1 | Exclude Gmail's Promotions / Social / Forums categories at the watch? Or require a dedicated label the user files into? | Jake / Audri | Exclude the three categories; keep whole-INBOX as an opt-in |
| 2 | Retention for filtered-out stubs — 30 days? | Jake | 30 days, then purge |
| 3 | Is a body-less stub acceptable for filtered mail, or should nothing at all be written? | Jake | Stub (needed for de-dup and for the Filtered out tab) |
| 4 | Suppression default scope — sender, or whole domain? | Audri | Sender, with domain offered in the confirm |
| 5 | Should `Intelligence › Inbox` replace `/ai-emails` outright, or ship beside it behind a flag? | Jake | Flag `ve_inbox_v1`, default on in dev |

Phase 0 step 3 (reconnecting Gmail after the tunnel change) and any Google
verification work are owner actions, not developer actions.

---

## 10. What not to break

The current page does several things well and the rebuild must carry them
forward unchanged:

- Nothing sends without a human tap. `handle_inbound` never calls the provider.
- No AI disclosure ever reaches a recipient
  (`ai-emails-review-redesign-no-ai-disclosure`).
- The assumptions panel and the grounded "Facts the AI used" rail.
- Sandboxed HTML rendering with scripts blocked.
- The `body_preview_only` honesty notice.
- The reconnect-mailbox banner path from the 2026-07-28 remediation.
- Zero console errors, zero failed requests, zero horizontal overflow — the
  current page hits all three, and so must the replacement.
