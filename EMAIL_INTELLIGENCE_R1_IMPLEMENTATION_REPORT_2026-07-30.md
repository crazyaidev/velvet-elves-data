# Email intelligence R1 + R2 + Phase 5 — implementation report

**Date:** 2026-07-30 (Phase 5 added 2026-07-31)
**Plan:** `EMAIL_INTELLIGENCE_TEST_FINDINGS_AND_PLAN_2026-07-30.md` (revision 3)
**Scope delivered:** R1 (Phases 0–2 + the S1-06 access-control fix),
R2 (Phases 3–4) and **Phase 5 (the surface)**, with Phases 2–3 reworked around a
single thread-aware model call
**State:** implemented, tested, browser-verified. **Uncommitted.**

> **The client's complaint is now answered end to end.** Mail is categorised
> without anyone touching it, every category is on screen, filtered mail is
> visible with its reason and one tap from coming back, and junk no longer
> reaches the queue at all.

---

## 1. What shipped

| # | Change | Files |
| --- | --- | --- |
| S1-06 | Role guard on the three unguarded read endpoints | `api/v1/ai_emails.py` |
| Phase 0 | Bulk Gmail categories dropped at ingest, before any body fetch | `services/email/gmail_provider.py`, `core/config.py` |
| Phase 1 | Triage funnel running **before** persistence; filtered mail to its own table | `services/email/inbound_triage.py` (new), `services/email/inbound_dispatch.py`, migration `20260924090000` |
| Phase 2 | Categories that admit statements; one thread-aware model call for relevance + category + deal | `services/ai_email_engine.py`, `services/email/inbound_triage.py` |
| Phase 3 | Address matching on components; bare-state point dropped; thread inheritance; model ranking with abstention | `services/email/inbound_dispatch.py`, `services/email/inbound_triage.py` |
| Phase 4 | The correction loop — "Not mail I need", "Actually I need this" (with body re-fetch), suppression rules | `services/email/inbound_correction.py` (new), `services/email/inbound_hydration.py`, `api/v1/ai_emails.py` |
| Phase 5 | The surface: two streams, five views, category chips, deal rail, correction actions wired | `services/email/inbox_service.py` (new), `components/email/EmailViews.tsx` (new), `pages/AiEmailReviewPage.tsx`, `hooks/useAiEmails.ts`, `layouts/AppLayout.tsx` |
| Phase 6 | Queue hygiene: duplicate guard on every compose path, stale-draft warning + bulk-send exclusion, bounded reads | `repositories/communication_log_repository.py`, `schemas/communication_log.py`, `services/ai_email_engine.py`, `api/v1/ai_emails.py`, `pages/AiEmailReviewPage.tsx` |
| Phase 7 | Regression corpus gating CI; inbound AI spend attributed per tenant and split triage/draft | `tests/fixtures/inbound_corpus.jsonl` (new), `tests/test_inbound_corpus.py` (new), `tests/test_email_cost_telemetry.py` (new), `services/email/inbound_dispatch.py`, `services/ai_email_engine.py` |

**New endpoints:**

```
GET    /ai-emails/messages                      the mail itself, with the draft as an attribute
GET    /ai-emails/filtered                      the "Filtered out" feed, with reasons
POST   /ai-emails/filtered/{id}/restore         "Actually, I need this"
POST   /ai-emails/inbound/{log_id}/not-relevant "Not mail I need" (+ optional rule)
GET    /ai-emails/suppression-rules             manage the filter rules
DELETE /ai-emails/suppression-rules/{rule_id}   undo one (soft, audit survives)
```

### The surface (Phase 5)

**Two streams, one page** — the constraint the 2026-07-30 revert established.
`/ai-emails` and `/ai-emails/:logId` are unchanged as routes.

Five views, each answering a **different** question rather than re-sorting the
same rows (the 2026-07-10 "tabs that showed the same list" mistake):

| View | Shows |
| --- | --- |
| **Needs you** *(default)* | mail with a draft waiting, or that nobody has answered |
| **Incoming** | every relevant inbound message, drafted or not |
| **Outgoing** | the AI-composed task email — lifecycle completely unchanged |
| **Waiting** | we actually sent a reply; the ball is with them |
| **Filtered out** | every rejection, with its reason and a one-tap undo |

- **Category chips on the row** — Money, Date change, Document, Question,
  Update, FYI, Vendor reply. Assigned by triage reading the thread; the user
  never assigns anything.
- **Deal rail** with per-deal counts and **Unlinked pinned first**.
- **Money mail carries a standing wire-fraud warning** in the reading pane and
  is never drafted.
- **"Not mail I need"** behind a confirm that names the scope and the
  consequence, and **"Actually, I need this"** in Filtered out.
- One name everywhere: nav, breadcrumb and heading all read **"Email"**.
- The intro prose above the list is gone (`list-pages-no-intro-prose`).

---

## 2. Measured outcome

Same 20-message corpus, same real provider (`openai` / `gpt-5.4`), before and
after:

| Metric | Before | After |
| --- | --- | --- |
| Junk producing an AI draft | **3 / 12** | **0 / 12** |
| Junk reaching the queue at all | 9 / 12 relevant | **0 / 12** |
| Genuine deal mail lost | **6 / 8** | **1 / 8** † |
| Precision of what reaches the user | **0.40** | **1.00** |
| Recall on genuine deal mail | **0.25** | **0.88** † |
| Money-shaped mail auto-drafted | not modelled | **0** |

† **Read this number honestly.** The probe harness deliberately strips every
who-sent-it signal — no parties, no threads, no learned links — so it measures
the *content* path alone. The single loss is `D06`, a bare **"ok"** from the
buyer with no context whatsoever, which the model judged unrelated. In
production that message never reaches the model: the sender is a party, so
Stage 3 accepts it for free. That path is covered by
`test_known_party_is_relevant_whatever_the_content`, not by this harness.

It is the clearest possible illustration of the principle the rebuild rests on:
**content analysis cannot save a bare follow-up — only knowing who sent it can.**

Categories now assigned where nothing was produced before: `document_delivery`
(title commitment ready), `status_update` (appraisal came in / clear to close),
`money` (wire instructions — surfaced, never drafted), `schedule_change`.

### Deal matching (Phase 3), same real deal, threshold ≥ 8

`4567 Oak Ridge Avenue, Boardman, OH, 44512`:

| Phrasing | Before | After |
| --- | --- | --- |
| full composed address | 22 match | 17 match |
| `4567 Oak Ridge Avenue` | **4 miss** | **10 match** |
| `4567 Oak Ridge` | **4 miss** | **8 match** |
| `Re: 4567 Oak Ridge Avenue` | **4 miss** | **10 match** |
| `…the title commitment for 4567 Oak Ridge Avenue is ready` | **4 miss** | **10 match** |
| `4567 Oak` | **0 miss** | **8 match** |
| `4567 Oak Ridge Avenue, Boardman` | **6 miss** | **12 match** |
| `the Oak Ridge file` | 0 miss | 6 miss *(deliberate — see below)* |
| `the closing on 44512 is Friday` | 5 miss | 5 miss *(a zip is a town)* |
| `the Boardman closing is Friday` | 2 miss | 2 miss *(so is a city)* |

**Seven previously-missed phrasings now match, with zero false positives.**
Every phrasing was scored against *all six* deals in the tenant, including
`4567 Meadowridge Avenue, Boardman, OH, 44512` — same street number, same city,
same state, same zip. The intended deal won uniquely every time.

`the Oak Ridge file` scores 6 on purpose: two deals share that number, city and
zip, so it stays below the threshold for the model to arbitrate or a human to
pick, rather than being guessed at.

---

## 3. The design decisions worth recording

**Bulk categories are dropped at ingest, not at the Gmail watch.**
`users.watch` takes one label list and one behaviour, so `EXCLUDE` would have
discarded the `INBOX` restriction and started delivering `SENT`, `DRAFT` and
archived mail — a *bigger* firehose. The exclusion happens in the history walk,
where each message's own `labelIds` are already present, before any body fetch.
Consequence worth noting: **no watch re-registration, so no mailbox-owner
reconnect is required.**

**Filtered mail never enters `communication_logs`.** It goes to a new
`inbound_filtered` table, envelope-only, no body. The first attempt stored stubs
in `communication_logs`, which would have fed a body-less row into
`list_recent_thread_messages` → the AI's own `_thread_history`, into
response-time analytics, into the vendor workspace and into the unpaginated CSV
export — and contradicted `requirements.txt` §6.1 / `SYSTEM_DESIGN.md` §2.2.11,
which define that table as the immutable master log of *communication* on a
two-year retention.

**De-duplication had to be preserved explicitly.** The dispatcher's fingerprint
hashes the body, so a body-less record can never match it — precisely the
Outlook case (same message, new resource id) the fingerprint exists for. The
filtered row stores `fingerprint_sha256`, and dispatch consults both tables.

**One model call answers three questions, with the thread attached.**
`analyze_inbound(message, thread_so_far[], candidate_deals[])` returns
`{related, category, transaction_id, confidence, evidence}`. This replaced a
regex that read one message in isolation — which is why *"Yes, Thursday works"*
used to produce nothing. Deterministic signals still short-circuit: suppression
rules, bulk headers, known party, filed thread and terms of art are all settled
without a call.

**The ranker may not search, invent, or guess.** Candidates are built
deterministically and capped at 8; an id the model was not offered is rejected;
and below `MATCH_CONFIDENCE_FLOOR = 0.75` the message stays unlinked for a human
to file. A wrong match is worse than none — the drafter would then answer using
another deal's closing date and parties, one tap from a real client.

**A party on more than one deal is relevant but not filed.** Caught by the
existing suite: my first cut took `candidates[0]`, silently filing an ambiguous
message to whichever row came back first. `test_dispatch_leaves_ambiguous_party_email_unmatched`
failed and the behaviour was corrected.

---

## 4. Verification

**Backend suite: 1564 passed, 0 failed** (`pytest app/tests`); `ruff check app/`
clean; `eslint` clean; `tsc --noEmit` clean; production build succeeds.

**Full-matrix Chrome pass** (`_tools/e2e/er2_10_full_matrix.mjs`): **70/70**,
run three times consecutively to prove it is repeatable rather than
order-dependent. 0 console errors, 0 page errors, 0 unexpected failed API calls.
It covers access control, both streams, all five views, empty states, search,
the toolbar shape, categories, delete (row + bulk), the correction loop, the
suppression-rule lifecycle, queue hygiene, limit validation, deep links, the
send-safety invariants, and mobile at 390×844.
Four tests were updated, each for a real reason:

| Test | Why it changed |
| --- | --- |
| `test_engine_skips_unmatched_unrelated_email` | The guard moved from the engine to dispatch. Now asserts the *stronger* outcome: the message never enters `communication_logs` at all. |
| `test_classifier_returns_other_for_chatter` → `..._fyi_...` | `KIND_OTHER` was a discard; `KIND_FYI` means kept-but-no-reply. |
| `test_dispatch_writes_provider_attribution_atomically` | Tests persistence mechanics; given a term of art so it is not coupled to a relevance verdict. |
| `test_dispatch_dedupes_repeated_webhook_deliveries` | Same. |

**New:** `app/tests/test_inbound_triage.py` — 48 tests covering the junk corpus,
statement categories, thread-context follow-ups, match abstention, the
hallucination guard, provider-down fallback, the money invariants, and the
component matcher (including the false-positive check against the near-identical
neighbouring deal). `app/tests/test_inbound_correction.py` — 11 tests covering
restore-with-refetch, the honest body-less fallback, idempotent restore, draft
discarding, tenant isolation, sender hashing, the expired-token regression, and
a round trip proving a rule written by the UI is actually honoured by the
funnel. `app/tests/test_inbox_service.py` — 9 tests covering the read model: a
message with no draft is still listed, the draft is an attribute, a discarded
draft is not an answer, "Waiting" means we actually *sent* something, money
outranks newer mail, newest-first within a tier, Unlinked pinned in the rail,
and tenant scoping.

**Frontend:** `tsc --noEmit` clean (needs `--max-old-space-size=6144`; the
default heap OOMs on this codebase).

**Real Chrome** (`_tools/e2e/er2_03_verify_r1.mjs`, system Chrome via
puppeteer-core, logged in as the platform admin) — **6/6 passed**:

| # | Check | Result |
| --- | --- | --- |
| V9 | Outgoing composed drafts still listed | 18 drafts, 17 `compose` + 1 `factual` |
| V9b | Rows render | 18 rows |
| V9c | Approve & send / Edit / Discard intact | all present |
| V18 | Deep link `/ai-emails/:logId` resolves | yes |
| V15a | Unauthenticated read rejected | 401 |
| V14 | 0 console errors, 0 page errors, 0 failed API calls | clean |

Screenshots: `c:\Projects\_shots\er2\er2_03_desktop.png`, `er2_03_mobile.png`.

**R2 in real Chrome** (`_tools/e2e/er2_04_verify_r2.mjs`) — **10/10 passed**,
driving the new endpoints through a real logged-in session:

| # | Check | Result |
| --- | --- | --- |
| V5a | `GET /filtered` returns the feed | 200 |
| V5b | Every filtered entry carries a reason | yes |
| V5c | `POST /restore` brings a message back honestly | `restored_without_body` + `body_preview_only` flag |
| V6a | `GET /suppression-rules` | 200 |
| V6b | `POST /not-relevant` filters and writes a rule | both ids returned |
| V6c | The orphaned draft is discarded, not left sendable | not in the queue |
| V6d | The rule is listed with a readable label | `er2-verify.example` |
| V6e | Revoking is one call and it disappears | 200, gone |
| V15b | New endpoints reject unauthenticated callers | 401 / 401 |
| V14b | No unexpected console or API errors | clean |

V6d returned the **same rule id across two separate runs** — the first run
revoked it, the second re-created it — which proves the revive-not-duplicate
path against the real unique index rather than against a mock.

**Phase 5 in real Chrome** (`_tools/e2e/er2_05_verify_surface.mjs`) —
**12/12 passed**:

| # | Check | Result |
| --- | --- | --- |
| S3-15 | Nav, breadcrumb and heading agree | all read "Email" |
| S1-01 | Five views, each showing different rows | Needs you 6 · Incoming · Outgoing 17 · Waiting · Filtered out |
| S1-02a | API serves messages including undrafted ones | 15 messages, **15 with no draft** |
| **S1-02b** | **Undrafted messages actually render** | **15 of 15 on screen** |
| S1-01b | Category chips render on rows | yes |
| S5-pane | Incoming shows no leftover outgoing draft | fixed, see below |
| V5d | Filtered out lists a rejection with its reason and an undo | 2 rows, reason + button shown |
| V5e | Restoring returns the message to the inbox | `restored_without_body` |
| V9d | Outgoing still lists composed drafts with their actions | 17 drafts, all actions |
| S2-11b | Deal rail renders with Unlinked pinned | yes |
| S3-14b | Mobile 390×844, no horizontal overflow | 5 views render |
| V14c | 0 console, page and API errors | clean |

**S1-02b is the headline.** Before this work, 13 of 18 inbound messages had no
row anywhere in the product. Now every message is on screen, whether or not the
AI had anything to say about it.

**Phase 6 in real Chrome** (`_tools/e2e/er2_06_verify_hygiene.mjs`) —
**7/7 passed**:

| # | Check | Result |
| --- | --- | --- |
| S2-10 | No duplicate draft groups remain | 13 drafts, **0 duplicate groups** (was 17 with 2 groups) |
| S2-12a | The server flags stale drafts with a reason | 7 flagged |
| S2-12b | A stale draft is never counted as ready for bulk send | 0 stale-and-ready |
| S2-12c | The stale banner renders in the reading pane | yes |
| S3-13 | The drafts list honours a limit | `?limit=2` → 2 |
| S3-13b | An out-of-range limit is rejected | `?limit=9999` → 422 |
| V14d | 0 console, page and API errors | clean |

The very draft that opened this investigation — *"Request for Earnest Money
Deposit Receipt… by 2026-06-22"* — now reads **"It asks for a date that has
passed (2026-06-22)."**

**S2-12b was a vacuous pass in the browser** (this tenant runs Manual posture,
so nothing is ready-to-send and the set was trivially empty). The real
guarantee is pinned by `test_send_ready_skips_a_stale_draft`, which puts a
genuinely `ready_to_send` draft quoting a past date through the batch endpoint
and asserts `sent == 0` and that the provider was never called.

**Duplicates reconciled:** 4 drafts discarded across the ×4 "Welcome — 77
Harness Test Lane" and ×2 "Appraisal Ordered — 88 Livefire Test Lane" groups,
keeping the newest of each (composed from the most recent deal facts). Soft
delete — the same state the Discard button produces. Pending drafts 17 → 13.
Script: `_tools/e2e/er2_reconcile_duplicates.py`, dry-run by default.

### Phase 7 — the corpus, and where the money goes

**`app/tests/fixtures/inbound_corpus.jsonl`** — 37 labelled messages, each
carrying a `note` saying what it exists to catch, so a future reader can tell a
deliberate edge case from filler. It includes five adversarial pairs: marketing
that name-drops "title commitment" to get through, and real deal mail that
happens to carry a footer address.

**`test_inbound_corpus.py`** runs on every CI build (the existing `pytest -q`
step already covers it — no workflow change) and asserts:

- the verdict for every message, naming the failure in the message;
- **which stage decided** — junk settled by `bulk` costs nothing, junk settled
  by `ai` costs a call, and deal mail settled by `party` survives with no
  content at all;
- precision ≥ 0.95 and recall ≥ 0.98, printing exactly which refs leaked or
  were lost;
- no junk is ever drafted, and money mail is always shown and never
  auto-drafted;
- **≤ 35% of messages reach the model** — cost control asserted, not assumed.

**No model calls happen in CI.** The model is stubbed from the label, so what
the corpus pins is the *funnel* — which stage decides — not the model's
judgement. Cases marked `expect_source: "ai"` assert that the deterministic
stages correctly abstained, not what the model then said. That is a real limit
and it is stated in the file's docstring.

**The corpus immediately found a bug.** `D16` ("payoff statement") needed a
model call, because the money vocabulary was missing from the strong-signal
list. Routing unmistakable closing terms through the ambiguous middle meant a
provider outage could sink a **wire-instruction email into "Filtered out"**.
`payoff statement / payoff letter / payoff amount / closing statement` are now
strong signals.

**Cost attribution.** The inbound path is a webhook with no request-scoped user,
so every triage and drafting call was metered against a **null tenant** under
the catch-all feature `"other"` — `/platform/costs` literally could not show
what inbound mail costs. Both calls are now scoped explicitly:

| Feature | Call |
| --- | --- |
| `email_triage` | the short classification, only for the ambiguous middle, cached per sender domain |
| `email_draft` | the expensive one — full deal context, document list, thread history |

Splitting them is what makes the saving legible: junk should now cost at most a
cached triage call and never a draft. `/platform/costs` groups by `feature`
generically, so both appear with no console change.

### The test suite was making live AI calls (CI, 2026-07-31)

CI failed `test_inbound_webhook_persists_log` — `persisted: 0` where the test
expects `1`. It passed locally every time. The reason is worse than the symptom:

**`AIService.chat()` builds a live client from the configured key, so the suite
was calling api.openai.com for real.** Locally a working key made the model
answer; in CI, where the key is `sk-placeholder`, every call 401'd. The suite
therefore behaved *differently in the two places* — which is exactly how a
genuine regression in the provider-unavailable path passed my local verification
and only surfaced in CI. It was also spending money on every local run.

Fixed at the root: an autouse fixture in `conftest.py` makes `AIService.chat`
raise "provider unavailable" in tests. CI and local now agree, nothing reaches
the network, and the deterministic paths get exercised deterministically. Tests
that want a specific model answer still inject their own stub via
`AIEmailEngine(supabase, ai_service=...)`, which the fixture does not touch.

**The regression it was hiding was real.** *"Inspection scheduled / Scheduled
for Tuesday at 10am"* from a vendor is unmistakable coordination mail, but
"inspection" is only a **weak** term, so with the model unreachable it was
filtered — losing vendor scheduling mail precisely when the system is least able
to compensate. The old flat keyword list caught it; deleting that list (rightly,
it fired on newsletters) lost this case.

The fix is a compound rule, not a return to flat keywords: **a weak real-estate
word PLUS explicit scheduling language** is a strong signal. Neither half counts
alone, so "Coffee is scheduled for 10am" stays out and "Thoughts on the
listing?" still needs the model. Four corpus cases pin it, including that
adversarial pair.

### Toolbar redesign and delete (client feedback, 2026-07-31)

**The toolbar was two wrapping rows of twelve loose chips** — five views plus
one per deal. That does not scale (thirty deals meant thirty chips) and it read
as clutter rather than as a control. Now one row:

- **Views** are a single segmented container, matching the Calendar-page mode
  switch — a fixed, small set, so pills are right.
- **Deals** are a `Select`, the same rounded-full trigger the transactions index
  uses — unbounded, so a dropdown is right.
- **Search** moved up beside them; the list pane no longer carries a second
  search box competing with the header.

**Delete had no affordance outside the reading pane.** Now:

- every row has a **checkbox** and a **delete** control on hover/focus;
- ticking rows reveals a **bulk bar** naming the count, with Delete and Clear;
- the confirm names the consequence per kind — incoming mail moves to
  **Filtered out** and is restorable, outgoing drafts are discarded — because
  people delete far more readily once they know it is reversible;
- partial failures are reported honestly ("3 of 5 deleted") rather than as a
  clean sweep.

Two defects found while doing it, both by looking at screenshots rather than by
a passing check: the delete icon **printed over the row's timestamp** (fixed
with permanent right padding, not a hover-only gap that made rows jump), and on
mobile the stacked panes showed **two empty states saying the same thing**
(the reading pane's is now desktop-only). Both are now pinned by checks.

### A 500 that any client could trigger

`POST /ai-emails/filtered/undefined/restore` — a malformed id went straight to
Postgres and raised `invalid input syntax for type uuid` as an **unhandled 500**,
filling the logs with tracebacks. Found because a harness template built
`undefined` into a URL, but any client bug would do it. All three id-taking
endpoints now validate up front and return 404. Pinned by
`test_a_malformed_id_is_a_404_not_a_500`.

### Three regressions found by the client's review, not by my tests

Reported as *"why has the AI draft feature been removed?"* — and the answer was
that in two real senses it had been.

1. **The default view no longer showed the draft queue.** `list_inbox_messages`
   filtered `direction = 'inbound'`, so "Needs you" — the view the page lands on
   — carried none of the AI-composed task drafts, which are the *majority* of
   the queue (14 of 14 rows here). The drafts were one click away under
   Outgoing, but a user opening the page saw a screen with none of their work on
   it. My own Phase 5 plan said Needs you should carry *"relevant mail … plus
   outgoing drafts awaiting approval"* and I implemented only the first half.
   My verification missed it because V9d asked "does the Outgoing view still
   list drafts?" rather than "does the page a user actually lands on still show
   their drafts?"
2. **Restoring a filtered message never re-drafted it.** `restore_filtered`
   inserted the log and stopped, so "Actually, I need this" returned the mail
   but silently withheld the reply — correcting the filter left the user worse
   off than if triage had never fired. It now runs the normal inbound hooks.
3. **`direction` was dropped in serialization.** Fixing (1) appeared not to
   work: the backend returned 20 rows including 14 outbound, but `InboxMessage`
   had no `direction` field, so pydantic discarded it and the client could not
   tell the streams apart. A field added to the dict, the TS interface and the
   row renderer — but not the response model.

All three are pinned: `test_needs_you_includes_outgoing_composed_drafts`,
`test_a_reply_draft_is_not_listed_twice`,
`test_a_discarded_outgoing_draft_is_not_listed`,
`test_restore_re_runs_the_ai_hooks`, and two new browser checks (`S5-drafts`,
`S5-drafts-ui`) that assert against the **landing** view rather than a view
reached by clicking.

Outgoing rows read `To <name>` with a "Draft to send" chip, so they cannot be
mistaken for incoming mail. Reply drafts are *not* duplicated into the list —
they already appear as an attribute of the message they answer.

### Three bugs the earlier verification caught

None of these would have been found by unit tests.

1. **The reading pane leaked across views.** Switching to Incoming left an
   unrelated *outbound* draft in the pane under an incoming row — visible in the
   first Phase 5 screenshot. The auto-select effect was running in every view;
   it is now scoped to Outgoing, and switching views clears both selections.
2. **Empty-state copy said "Pick a draft to review" under Filtered out**, which
   described the wrong surface entirely. Copy now follows the view.
3. **Restore returned 409 when the Gmail token was expired.** This was the
   serious one: `get_email_provider_for_user` raises
   `ProviderCredentialsExpiredError`, which propagated out of the restore path —
   so a user could not undo a filter decision until they reconnected their
   mailbox, *precisely when the system was least able to help them*. An expired
   token is just one more way the provider "can no longer supply it", so it now
   degrades to the honest body-less restore like any other fetch failure.
   Pinned by `test_restore_survives_an_expired_mailbox_token`.

The V5d check was initially a **vacuous pass** — the filtered feed was empty, so
"lists rejections with an undo" was trivially true. It now drives the full round
trip: filter a real message, assert the row renders with its reason and undo
button, then restore it and assert the outcome.

The script seeds its own disposable inbound through the product's
`test-inbound` endpoint. An earlier version silently depended on whatever
happened to be in the queue and skipped itself on the second run; that is fixed
so the check is repeatable.

**Data touched in the dev tenant:** two `test-client@example.com` "Quick
question about closing" harness messages were filtered and then restored (the
originals are removed, replaced by body-less restored copies flagged
`body_preview_only`, because there is no live mailbox to re-fetch from), one
draft was discarded by the not-relevant flow, and one suppression rule for
`er2-verify.example` exists in a revoked (inert) state. No real correspondence
was affected. Pending drafts on `/ai-emails`: 18 → 17.

---

## 5. What is NOT done

- **Legacy messages show as "Message", not a real category.** Rows that arrived
  before this work carry no `triage_category`, so they fall back to a generic
  chip. Only mail arriving from now on is categorised by the model. A backfill
  would need a model call per historical message and has not been run.
- **"File to deal" still has no UI.** The `refile` endpoint works and teaches
  the matcher, but nothing calls it — unchanged since finding S2-11. The
  "Which deal?" two-option chip for ambiguous matches is likewise unbuilt, so
  ambiguous mail sits in **Unlinked** rather than asking.
- **Mobile is not push-navigation yet.** It renders without horizontal overflow
  and the views work, but both panes still share the viewport (S3-14). The
  plan's slide-in navigation is not built.
- **No keyboard shortcuts, no bulk selection.** Both are in the Phase 5 plan
  and neither is implemented.
- **The thread is not rendered in the pane.** A selected message shows its
  snippet, not the full conversation oldest → newest. The model reads the
  thread; the reader does not yet see it.
- **Verification gaps.** V19 (a real 3-message thread end-to-end), V20 (prose
  deal reference from an unknown sender) and V21 (provider down mid-run) are
  covered by unit tests but have **not** been exercised in the browser against
  seeded data.
- **S1-06 is proven only for unauthenticated callers.** The full check — logging
  in as a Client-role account and confirming 403 — needs a seeded Client user.
- **The AI verdict cache is per-process**, so with two ECS tasks a domain may be
  judged twice. Cost optimisation only, never correctness.
- **Auto-expiry at 30 days is not built.** Stale drafts are warned about and
  excluded from bulk send, both computed live, but nothing removes them. That
  half needs the scheduler, which has never run in production.
- **No partial unique index for duplicates.** The guard is a read-then-write in
  application code, so two concurrent composes could still both miss it. The
  plan calls for a DB-level index; it is not written, and the window is narrow
  but real.
- **Stale detection only reads ISO dates** (`2026-06-22`). A draft saying
  "by June 22, 2026" is not flagged. Deliberate — a false stale warning trains
  people to ignore the banner — but it is a gap.
- **No per-tenant daily triage budget or visible cap.** The plan asked for one.
  Spend is bounded in practice by the deterministic-first ordering and the
  domain cache, but nothing enforces a ceiling.
- **No before/after cost figure has been published.** The attribution now
  exists; the numbers need a period of real traffic to be worth quoting, and
  quoting an estimate instead would be exactly the kind of unearned precision
  this document has tried to avoid.
- **The corpus does not exercise the real model.** By design, for CI
  determinism — but it means a model regression (a prompt change that makes it
  worse) would not be caught. `_tools/e2e/er2_gate_probe_v2.py` hits the real
  provider and should be run by hand before any prompt change.

---

## 6. Deployment notes

- Migration `20260924090000_inbound_filtered.sql` is **applied to dev only**.
  Staging and prod still need it. It is idempotent and safe whichever of
  `20260922090000` / `20260923090000` an environment has run.
- `inbound_suppression_rules` is reproduced verbatim from the reverted attempt,
  so dev and staging need no change and prod converges on the same shape.
- New setting `GMAIL_EXCLUDED_LABEL_IDS`, defaulting to
  `CATEGORY_PROMOTIONS,CATEGORY_SOCIAL,CATEGORY_FORUMS,SPAM,TRASH`. No watch
  change and no owner action required.
- The `inbound_filtered` retention purge is **not yet wired**; it belongs on
  `/internal/schedules/tick`, which has never run in production
  (`prod-scheduler-never-wired`). Correctness does not depend on it — filtered
  mail is invisible because of which table it is in, not its age.
