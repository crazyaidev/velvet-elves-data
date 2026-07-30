# Intelligence › Email review — issue register

**Date:** 2026-07-30
**Source:** live E2E run documented in `EMAIL_REVIEW_E2E_TEST_REPORT_2026-07-30.md`
**Status:** findings only — no source code was changed.

20 issues, grouped by the question each one answers. Severity is about the
product the user described wanting ("show me only the emails I actually need"),
not about crash risk — there were no crashes.

| Sev | Count | IDs |
| --- | --- | --- |
| Blocker | 5 | E-01, E-02, E-05, E-09, E-10 |
| High | 6 | E-03, E-04, E-06, E-08, E-11, E-13 |
| Medium | 7 | E-07, E-12, E-14, E-15, E-16, E-18, E-20 |
| Low | 2 | E-17, E-19 |

---

## A. Why unrelated mail reaches the queue

### E-01 — Blocker — The whole personal inbox is ingested and permanently stored

`gmail_watch_label_ids` defaults to `INBOX` (`app/core/config.py:271`), and
Gmail's `INBOX` label covers every category — Promotions, Social, Updates,
Forums. `dispatch_inbound_email` then writes the message to
`communication_logs` *before* any relevance decision
(`app/services/email/inbound_dispatch.py:134-157`), so the row is created and
kept whatever the engine later decides.

**Impact.** Two separate problems from one cause. The queue draws from a
firehose, and the tenant database accumulates a full copy — subject, body text,
body HTML, sender — of the user's personal correspondence, including messages
the product itself classifies as irrelevant. That is the data-protection
version of the same complaint.

**Evidence.** After the injection run, `"Dinner Sunday?"` and every newsletter
are rows in `communication_logs` with `direction=inbound`, subject and body
intact, and no draft.

**Fix direction.** Ingestion needs its own gate, before persistence: decide
*relevant / not relevant* first, persist only what passes, and keep a
minimal, body-less audit stub for the rest so de-duplication still works.

---

### E-02 — Blocker — A CAN-SPAM footer address counts as a real-estate signal, and it skips the AI check

`_is_transaction_related` (`app/services/ai_email_engine.py:871-890`) runs the
deterministic signal test **first** and returns `True` immediately when it
fires — the AI relevance call on line 887 is only reached when the
deterministic test says *no*. `_has_real_estate_signal` returns `True` when
`_ADDRESS_SIGNAL_RE` (`ai_email_engine.py:184-189`) finds anything shaped like
`123 Some Street`.

Every US commercial email is legally required to carry a physical postal
address. So the single most reliable marker of *bulk marketing* is being read
as a marker of *a specific property*, and it disables the one check that could
have caught the mistake.

**Impact.** The AI relevance gate — the thing that is supposed to keep the
queue clean — is bypassed for the majority of exactly the mail it exists to
reject.

**Evidence.** Corpus run: the deterministic path fired on 25 of 38 messages;
18 of 20 unrelated messages matched only on their footer address. Live run:
LinkedIn, Zillow, a recruiter and a CRM sales pitch all produced drafts.

---

### E-03 — High — Bulk-mail headers are not recognised

`_is_auto_generated` (`ai_email_engine.py:156-179`) checks the sender
local-part, `Auto-Submitted` and `Precedence`. It does not look at
`List-Unsubscribe` or `List-Id`.

**Impact.** `List-Unsubscribe` is what Gmail reads to draw its own Unsubscribe
button; it is on essentially every real newsletter. `Precedence: bulk` is
largely legacy. The check therefore misses most modern bulk mail.

**Evidence.** Header probe: `Precedence: bulk` → detected; `Auto-Submitted` →
detected; `List-Unsubscribe` → **not** detected; `List-Id` → **not** detected.

---

### E-04 — High — The signal term list is too generic to be a signal

`_TRANSACTION_SIGNAL_TERMS` (`ai_email_engine.py:133-145`) mixes genuinely
high-precision phrases ("closing disclosure", "earnest money", "title
commitment") with bare words that occur constantly in ordinary business mail:
`title`, `listing`, `survey`, `loan`, `commission`, `buyer`, `seller`,
`disclosure`, `real estate`, `brokerage`, `mls`.

**Impact.** A recruiter writing "great commission split" and a CRM vendor
writing "helps realtors close more deals" both read as transaction mail.
Because of E-02 this verdict is final — no AI check follows.

**Evidence.** `E04` (recruiter) matched on `commission`; `N12` (CRM) matched on
`real estate`; `E01` (title marketing) matched on `title`.

---

### E-05 — Blocker — Transaction mail that is not a question is dropped entirely

`_classify` (`ai_email_engine.py:802-867`) recognises vendor schedule replies,
document *requests*, and question shapes. Anything else returns `KIND_OTHER`
and `handle_inbound` returns `None` at line 288 before the relevance gate is
even consulted.

Most consequential mail on a transaction is a **statement**:

- "The title commitment for 8104 Riverstone Place is ready for review."
- "The appraisal came in at $312,000. Report attached."
- "Closing has been moved to the 14th."
- "Wire instructions attached."

**Impact.** These produce no draft, no notification, and — because of E-09 —
no visible row anywhere. The most important email of the week is the one most
likely to be silently discarded. This is the mirror image of the user's
complaint and, for a coordinator, the more dangerous half.

**Evidence.** Live run L02 and L03: both real, both addressed to a real deal in
the tenant, both produced nothing.

---

### E-06 — High — The deal matcher cannot match how people write addresses

`_match_transaction_by_message_address` requires `score >= 8`
(`inbound_dispatch.py:774`). In `_transaction_text_match_score`
(`inbound_dispatch.py:821-861`) the only large component is `+10` for the
transaction's whole `address` value appearing as a substring of the message.

But `transactions.address` stores the fully composed form — `"8104 Riverstone
Place, Hilliard, OH, 43026"` — so that `+10` only fires when the sender pasted
street, city, state *and* zip. Natural phrasing falls back to the small
components (`city +2`, `state +1`, street-number-plus-distinctive-token `+4`),
which lands just under the threshold.

**Impact.** Real mail about a real deal arrives unlinked, so it is drafted (if
at all) with no deal context, marked "Not linked to a deal", and — per E-10 —
cannot be corrected.

**Evidence.** L01 quoted the full composed form → matched, `basis=address`.
L02 and L03 wrote the same addresses the way a person writes them → both
`basis=unmatched`. L04 named "77 Harness Test Lane" and still came back
unmatched.

**Related invariant.** `address-compose-dedupe-invariant` already records that
`address` double-stores city/state/zip. This is a second consumer that the
composed column silently breaks.

---

### E-07 — Medium — Two-letter state codes are ordinary English words

`_transaction_text_match_score` adds `+1` when the state token appears
(`inbound_dispatch.py:840`). The tenant's deals are in `OH` and `IN`. "in" is
one of the most common words in English, and `_ADDRESS_STOP_WORDS`
(`inbound_dispatch.py:864-868`) lists `"oh"` and `"in"` as stop words for the
*token* pass while the *state* pass still scores them.

**Impact.** Noise in a score that is already tuned to one point of precision
(E-06). Wrong deals gain score from prose.

---

### E-08 — High — Nothing the user does teaches the filter

`POST /ai-emails/{id}/discard` takes `{reason}` and writes it to
`error_message` (`app/api/v1/ai_emails.py:1076-1107`). There is no sender rule,
no mute, no "never draft from this address", no per-tenant allow/deny list, no
signal fed back into the gate.

**Impact.** The user discards the Zillow draft today and gets an identical one
tomorrow. Manual cleanup is unbounded, which is precisely why the user
concluded it is easier to read Gmail directly.

**Evidence.** No learning call fires on discard; the only learning table in the
system, `inbound_sender_deal_links`, is written exclusively by re-file
(`ai_emails.py:443-489`), which the UI cannot reach (E-10).

---

## B. What the page is, versus what it needs to be

### E-09 — Blocker — This is a draft queue, not an email review surface

`GET /ai-emails/drafts` returns rows where `is_ai_generated = true`
(`communication_log_repository.py:272-294`), and the page renders exactly that
list. An inbound message that produced no draft has no representation on the
screen at all.

**Impact.** The user's stated goal — "display only the emails that are exactly
necessary" — cannot be met by this surface even in principle, because the
surface's unit is the AI's *output*, not the *mail*. Every engine miss (E-05)
becomes invisible rather than merely unhelpful.

**Evidence.** `"Appraisal complete"` and `"Title commitment ready"` are rows in
`communication_logs` right now. Searching the page for "Riverstone" returns 0.

---

### E-10 — Blocker — The re-file correction loop is unreachable

`POST /ai-emails/inbound/{log_id}/refile` exists, re-points the log, teaches
`inbound_sender_deal_links` so the sender auto-files next time, and re-runs the
draft against the right deal. The reading pane offers exactly four controls:
`Approve & send`, `Edit`, `Regenerate`, `Discard`.

Worse, the "Not linked to a deal" tooltip
(`AiEmailReviewPage.tsx:836`) instructs the user to "re-file it onto the right
deal" — an action the UI does not provide.

**Impact.** The one mechanism that would make the matcher improve with use is
dead. Given E-06 puts real mail in the unlinked state routinely, this is the
difference between a system that gets better every week and one that does not.

**Evidence.** Enumerated every `button`/`a`/`select` in the reading pane:
`["Approve & send","Edit","Regenerate","Discard"]`.

---

### E-11 — High — "Escalated" sorts to the top and means "old", not "important"

`reviewStatus` gives `escalated` priority 0 (`AiEmailReviewPage.tsx:100-108`)
and the list sorts on that first (`AiEmailReviewPage.tsx:1142-1149`). A draft
becomes escalated when `escalation_due_at` (created + 36 h by default) has
passed *and the escalation job happened to run*.

**Impact.** The nine most prominent rows are the nine stalest, and a brand-new
client email ranks below a Zillow alert. Because escalation depends on when the
job last ran, the badge is not even a consistent measure of age.

**Evidence.** 9 escalated rows aged 5–20 days sit above the 2-hour-old genuine
client mail; the 2-day-old drafts are *not* escalated despite being well past
36 hours — the scheduler had not run for them. (See `prod-scheduler-never-wired`.)

---

### E-12 — Medium — Duplicate drafts reach the queue

Three duplicate groups were rendered simultaneously: ×4 `"Welcome — we're under
way on 77 Harness Test Lane"` to the same recipient, ×2 `"Appraisal Ordered —
88 Livefire Test Lane"`, ×2 `"Working together on 5915 E 350 N"`.

`compose_outbound` de-duplicates per `(transaction, task)` via
`find_open_task_draft` (`ai_email_engine.py:576-612`), which is why the
2026-07-28 finding I-03 was closed — but it only applies when `task_id` is
passed, so other compose paths still stack.

**Impact.** Four identical drafts to one person is four chances to send the
same email twice.

---

### E-13 — High — You cannot fix a wrong recipient

Edit mode exposes subject and body only; the To/Cc line stays read-only text
(`AiEmailReviewPage.tsx:896`, `912`). There is no attachment control. The
backend's `EditAndSendRequest` accepts a `cc` array that the UI never sends.

**Impact.** A draft addressed to `party4@example.com` — a placeholder that is
sitting in the live queue right now — can only be discarded, taking the drafted
content with it. The same applies to any mail the AI addressed to the wrong
party.

---

### E-14 — Medium — No pagination, no server limit

`list_pending_ai_drafts` applies no range or limit, and the page renders every
row into one `<ul>`. With a personal mailbox feeding it (E-01/E-02), the list
grows without bound, and past PostgREST's default max-rows the response
truncates silently.

---

### E-15 — Medium — Mobile stacks both panes inside a fixed-height shell

`grid-cols-1 lg:grid-cols-[340px_1fr]` (`AiEmailReviewPage.tsx:1299`) inside an
`h-full` shell. At 390 px the queue and the reading pane share one viewport:
about 2.5 list rows are visible above a clipped reading pane, with no way to
switch between them.

**Impact.** The audience is mouse-and-phone real-estate professionals
(`ui-testable-by-non-dev-testers`). The surface is effectively desktop-only.
No horizontal overflow, so this is a layout-model issue, not a CSS bug.

**Evidence.** `er-05-mobile.png`.

---

### E-16 — Medium — Regenerate on irrelevant mail regenerates the same irrelevant draft

Regenerate re-runs `handle_inbound` on the same parent. For a LinkedIn
notification the inputs are identical, so the output is identical.

**Evidence.** Clicked Regenerate on the LinkedIn draft: reading pane unchanged,
row still in the queue.

---

### E-18 — Medium — Stale drafts sit indefinitely, quoting stale facts

The queue's top row asks a client to return a document named `"test"` by
**June 22, 2026** — five weeks in the past as of this run. Drafts have an
`escalation_due_at` but no expiry, no staleness warning, and no re-validation
of the facts they quote.

**Impact.** One mis-tap sends a client a request with a placeholder file name
and a lapsed deadline.

---

### E-20 — Medium — Orphan task drafts show "Not linked to a deal" with no remedy

Two composed task emails about `5915 E 350 N` carry `transaction_id = NULL`
and render the unlinked warning. `compose_outbound` now refuses `task_id`
without `transaction_id` (`ai_email_engine.py:488-492`), so these are legacy
rows — but they remain sendable, invisible to Needs You, and unfixable from
this page.

---

## C. Smaller things

### E-17 — Low — The page has two names
Nav says **"AI Email Review"**; the page header and breadcrumb say
**"Intelligence › Email review"**. Pick one.

### E-19 — Low — No filters at all
No filter by deal, by kind, by status, by date, by linked/unlinked. Search is a
client-side substring match over subject, body, recipients and sender of the
loaded drafts, and nothing else.

---

## D. The one-line summary

The page is well built and does what it was designed to do. It was designed as
a **review queue for AI drafts**, and the user needs a **filtered inbox for
transaction mail**. Those differ in their unit of display, so the gap cannot be
closed by tuning thresholds:

- mail the engine skips is invisible rather than filtered out (E-05 + E-09),
- mail the engine wrongly accepts is indistinguishable from real work (E-02),
- and neither outcome can be corrected by the person looking at it (E-08, E-10, E-13).

`EMAIL_REVIEW_REBUILD_PLAN_2026-07-30.md` addresses all 20.
