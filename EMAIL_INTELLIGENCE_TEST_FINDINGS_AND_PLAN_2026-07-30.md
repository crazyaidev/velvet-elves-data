# Intelligence › Email review — live test findings and rebuild plan

**Date:** 2026-07-30 · **Revision 3** (Phases 2–3 reworked around a single
thread-aware model call — see the revision notes in each phase; earlier design
review in §10)
**Author:** Jan Froben
**Tested against:** `velvet-elves-backend` @ `ff6d084`, `velvet-elves-frontend` @ `ef8e32c`
(the tree *after* the 2026-07-30 Inbox revert)
**Method:** real Chrome, real login, real API, real AI provider — no mocks
**Status:** findings measured; plan proposed; **no source code changed**

> Supersedes `EMAIL_REVIEW_REBUILD_PLAN_2026-07-30.md` and
> `EMAIL_REVIEW_E2E_TEST_REPORT_2026-07-30.md`, which are withdrawn.
>
> **Revision 2** reviews revision 1's workflow and logic against
> `requirements.txt` §6, `SYSTEM_DESIGN.md` §2.2.11, `FRONTEND_UI_WORKFLOW_LOGIC.md`
> §6.4 and the live backend/frontend source. Ten design errors were found and
> corrected; §10 lists each one. Two of them would have shipped real bugs
> (poisoned AI thread history, broken de-duplication), one was factually wrong
> about the Gmail API, and one violated a written requirement.

---

## 0. The one-paragraph answer

The page is not miscategorising email — **it has no categorisation at all**, and
the thing it lists is not email. It lists *AI drafts*. A message the engine
declines to answer has no row to appear in, so it is invisible rather than
filtered; a message the engine wrongly answers looks exactly like real work. In
a 20-message live corpus, **3 of 12 junk emails produced an AI draft and 6 of 8
genuine transaction emails produced nothing at all**. Both failures come from
the same design error: one boolean ("can I write a reply to this?") is being
asked to answer four different questions. The fix is to separate those questions,
let the model decide the one it is actually good at, and make every automatic
decision visible and reversible in one tap.

---

## 1. How this was tested

| | |
| --- | --- |
| Backend | fresh `uvicorn` on `:8002` from the working tree at `ff6d084` |
| Frontend | fresh `vite` on `:5191`, `VITE_API_BASE_URL=http://localhost:8002` |
| Browser | system Chrome via `puppeteer-core`, 1600×1000 and 390×844 |
| Account | `shyna.elene@minafter.com` (Admin), tenant `526cf077…c29da` |
| AI | the tenant's real provider — `openai` / `gpt-5.4` |

The two backends already running on this box were both stale (`:8000` predates
`cb59302`; `:8001` still served the reverted-away Inbox routes), which is why a
clean one was started. Harness, all read-only unless noted:

| Script | What it does |
| --- | --- |
| `_tools/e2e/er2_01_survey.mjs` | logs in through the UI, captures the page, dumps `GET /ai-emails/drafts` |
| `_tools/e2e/er2_02_actions.mjs` | filters, search, unlinked drafts, edit mode, mobile |
| `_tools/e2e/er2_gate_probe.py` | 20 labelled messages through the engine's real predicates + real AI relevance call |
| `_tools/e2e/er2_match_probe.py` | real deal matcher scored against human phrasings of a real deal address |
| `_tools/e2e/er2_db_state.py` | what is actually in `communication_logs` |

Screenshots and JSON: `c:\Projects\_shots\er2\`.

**Evidence grading.** Findings are marked **[browser]** (observed in Chrome),
**[measured]** (executed against the real predicates/matcher/DB), or
**[code-read]** (derived from source, not executed). Every **[code-read]**
finding carries a verification step in Phase 8.

**Not covered:** Gmail push could not be exercised end-to-end. Local
`EMAIL_WEBHOOK_PUBLIC_BASE_URL` and `PUBSUB_PUSH_AUDIENCE` (`.env:90,103`) point
at a retired ngrok tunnel, and a live injection through `dispatch_inbound_email`
was abandoned after the account lookup failed (`users.email` is Fernet-encrypted
at rest).

---

## 2. What the page actually is today  **[browser]**

Three names for one surface: nav **"AI Email Review"**, breadcrumb
**"Intelligence › Email review"**, heading **"Email review"**.

`GET /api/v1/ai-emails/drafts` returned **18 rows**. Of those:

- **17 are outbound composed emails** (`ai_kind = "compose"`, no `parent_log_id`) —
  welcome letters, "new file" notices, appraisal and inspection updates generated
  by the task executor.
- **1 is a reply to an inbound message** (`ai_kind = "factual"`).

So the surface a user opens expecting an inbox is, in practice, **an outbox of
AI-composed task email**. This is exactly what the 2026-07-30 revert was about —
the backend revert message says so outright:

> *"The message-based Inbox replaced a surface that also carried outbound
> composed drafts, so it is being withdrawn."*

**Any redesign must carry both streams.** A pure inbox deletes a working
surface; that mistake has already been made once and reverted.

---

## 3. Findings

Severity: **S1** breaks the product's promise · **S2** material daily damage ·
**S3** friction.

### S1-01 — There is no categorisation UI whatsoever  **[browser]**

Measured on the live page: `selects: []`, `tabs: []`, `checkboxes: 0`, and one
`<input>` — the search box. No category, no folder, no deal filter, no
relevance filter, at either viewport.

The user's report ("emails are not being categorized; transaction-related emails
and general emails are mixed together") is not a tuning problem. There is
nothing to tune. One flat list, sorted one way, is the entire surface.

> Note: `FRONTEND_UI_WORKFLOW_LOGIC.md` §6.4 still documents five filter tabs
> (All / Needs Review / Ready to Send / Low Confidence / Escalated). Those were
> removed by the 2026-07-10 redesign. **The spec is stale against the build** —
> §6.4 is a deliverable of Phase 5.

### S1-02 — The unit of the list is the AI's output, not the mail  **[measured]**

`list_pending_ai_drafts` (`communication_log_repository.py:272-294`) selects
`is_ai_generated = true`. An inbound message that produced no draft has no row
anywhere in the product.

In this tenant: **18 inbound messages, 13 of which produced no draft** — 72%
invisible. One of them arrived today (2026-07-30 14:25) from
`buyer.jane@gmail.com`, subject *"Quick question about closing"*, which
**matched a deal** (`match_basis = address`) — and still produced nothing, so it
appears nowhere.

This is why the page cannot be fixed by adjusting a threshold. There is no row
to hide or show.

### S1-03 — 6 of 8 genuine transaction emails are dropped before relevance is considered  **[measured]**

`_classify` (`ai_email_engine.py:802-867`) recognises question shapes and returns
`KIND_OTHER` for everything else. `handle_inbound` bails on `KIND_OTHER` at
`:287-292` — before the relevance gate runs at all.

| Ref | Message | Outcome |
| --- | --- | --- |
| D01 | "the title commitment for 4567 Oak Ridge Avenue is ready" | **lost** — `KIND_OTHER` |
| D02 | "The appraisal came in at $312,000" | **lost** — `KIND_OTHER` |
| D04 | "Attached are the wire instructions for the settlement" | **lost** — `KIND_OTHER` |
| D05 | "My sellers accepted. Sending the signed addendum" | **lost** — `KIND_OTHER` |
| D06 | "ok" (from the buyer) | **lost** — `KIND_OTHER` |
| D07 | "Closing docs went out to title. We are clear to close." | **lost** — `KIND_OTHER` |
| D03 | "when do we actually close?" | drafted |
| D08 | "We can be there Thursday at 9am for the inspection." | drafted |

Every real-estate transaction runs on *statements*, not questions. A coordinator
losing "we are clear to close" and "here are the wire instructions" is losing the
job. **Wire instructions vanishing silently is also a fraud-surface problem** —
it is the single message class a coordinator must always see.

This also contradicts `requirements.txt` §6.3, which says an unclear request
must **"notify responsible internal owner(s) with draft email"** — the specified
behaviour on uncertainty is *notify*, never *drop*.

### S1-04 — Junk is drafted, and the CAN-SPAM footer is why  **[measured]**

3 of 12 junk emails produced an AI draft: a CRM sales pitch, a recruiter email,
and a **utility bill**.

The mechanism is worse than the count. `_has_real_estate_signal`
(`ai_email_engine.py:892-901`) fired on **9 of 12** junk messages:

| Junk message | What made it look like a deal |
| --- | --- |
| LinkedIn notification | footer address `1355 Market Street` |
| Recruiter | footer address `1355 Market Street` |
| Home Depot promotion | footer address `1355 Market Street` |
| Bank statement alert | footer address `1355 Market Street` |
| CRM sales pitch | footer address + the word "title" |
| Inman newsletter | footer address + "mortgage", "listing", "commission" |
| Zillow listing alert | a property address belonging to no deal |
| Amazon shipping notice | the delivery address |
| Utility bill | the service address |

**Six of the nine matched on the postal address in the CAN-SPAM footer** — the
address every commercial email in the United States is legally *required* to
carry — and the other three matched an address in the body belonging to no deal.
`_ADDRESS_SIGNAL_RE` (`:184-189`) cannot distinguish a footer from a subject
property, and never checks the address against any deal in the tenant. Only 2 of
9 contained a genuine real-estate term.

### S1-05 — The AI arbiter is bypassed for the traffic it exists to judge  **[measured]**

`_is_transaction_related` (`:871-890`) returns `True` on the deterministic fast
path *before* calling the model. Since that fast path fires on newsletters, the
check that exists to reject newsletters never runs on newsletters.

Across the 20-message corpus **the model was consulted twice** — and was
**right both times** (it rejected a personal note about Sunday dinner and
accepted a vague "quick q" about closing the regex had missed). The most
accurate component in the pipeline is reached by 10% of traffic, and only the
10% that needs it least.

This is the direct answer to the AI-cost complaint. The cheap, accurate call is
skipped and the **expensive** one — full draft generation with deal context,
document list and thread history — is what runs on the junk.

### S1-06 — Any tenant user, including Clients and Vendors, can read every AI draft  **[code-read]**

`GET /ai-emails/drafts` (`ai_emails.py:200-203`), `GET /ai-emails/{log_id}`
(`:853-856`) and `GET /ai-emails/{log_id}/parent` (`:868-871`) are guarded by
bare `get_current_user` — **no `require_role`**. The repository call scopes by
`tenant_id` only (`list_pending_ai_drafts(current_user.tenant_id)`); there is no
role or ownership filter. Sibling endpoints (`/compose`, `/refile`,
`/test-inbound`, `/send-ready`) *do* use `require_role`.

`UserRole` (`app/models/enums.py:9-17`) includes `Client`, `ForSaleByOwner`,
`Vendor` and `Attorney`, and those users live in the tenant. So an external-role
account can list every AI draft in the tenant and read the original inbound body
behind each one.

`FRONTEND_UI_WORKFLOW_LOGIC.md` §6.4 asserts the opposite — *"the list is
server-scoped to drafts the caller's tenant + role can act on"* — and the
sidebar simply hides the entry. **The documented control is not implemented.**
Not exercised in the browser; Phase 8 V15 verifies it.

### S2-07 — Deal matching cannot survive human phrasing  **[measured]**

Scored against the real deal `4567 Oak Ridge Avenue, Boardman, OH, 44512`
(threshold `>= 8`, `inbound_dispatch.py:774`):

| Phrasing | Score | |
| --- | --- | --- |
| `4567 Oak Ridge Avenue, Boardman, OH, 44512` | 22 | match |
| `Hi, the commitment for 4567 Oak Ridge Avenue, Boardman, OH, 44512 is ready.` | 22 | match |
| `4567 Oak Ridge Avenue 44512` | 9 | match |
| `4567 Oak Ridge Avenue, Boardman, OH` | 7 | **miss** |
| `4567 Oak Ridge Avenue, Boardman` | 6 | **miss** |
| `Re: 4567 Oak Ridge Avenue` | 4 | **miss** |
| `Hi Shyna, the title commitment for 4567 Oak Ridge Avenue is ready` | 4 | **miss** |
| `4567 Oak Ridge Avenue` | 4 | **miss** |
| `the Oak Ridge file` | 0 | **miss** |

The only large component (`+10`) requires the **entire composed** value of
`transactions.address` as a substring (`:829-830`), and that column stores
`"street, city, ST, zip"`. A match needs the sender to type all four parts.
Nobody writes email that way.

Two further defects in the same function:

- **Bare state scores `+1`** (`:840-841`). "IN" and "OH" are English words.
- Two deals in this tenant are `4567 Oak Ridge Avenue, Boardman, OH, 44512` and
  `4567 Meadowridge Avenue, Boardman, OH, 44512` — same street number, same
  city/state/zip. Ties resolve to `None` (`:781-782`), so the message is silently
  unlinked rather than asking which one.

### S2-08 — The tenant database accumulates the user's personal mailbox  **[measured]**

`dispatch_inbound_email` writes `body` and `body_html` (`:144-145`) **before**
any relevance test — the test happens later, in a hook. All 18 inbound rows in
this tenant carry full bodies, including the ones the product then decided were
irrelevant.

Upstream, `GMAIL_WATCH_LABEL_IDS=INBOX` with
`GMAIL_WATCH_LABEL_FILTER_BEHAVIOR=INCLUDE` (`.env:97-98`, `config.py:271-272`)
subscribes to the whole inbox — Promotions, Social and Forums included.

Connect a real personal Gmail to this and the product copies it into the tenant
database. `requirements.txt` §6.1 sets retention at **two years from last user
login**, so it stays there.

### S2-09 — Ordering is staleness dressed up as urgency  **[browser]**

`reviewStatus` assigns `escalated` priority `0`
(`AiEmailReviewPage.tsx:100-108`); the sort runs at `:1142-1150`. "Escalated"
only means an escalation email was sent — i.e. **it is old**.

Observed in dev: the top nine rows are all "Escalated" and 5–9 days old; the
2-day-old rows sort below them.

> **Environment caveat.** `escalation_sent_at` is written by the escalations job
> behind `/internal/schedules/tick`, which **has never run in production**
> (`prod-scheduler-never-wired`). In prod no row is escalated, so every row ties
> at one priority and falls back to newest-first. The defect is real in both
> environments but presents differently; the fix must be validated against both.

### S2-10 — Duplicate drafts  **[measured]**

| Count | Subject |
| --- | --- |
| ×4 | Welcome — we're under way on 77 Harness Test Lane |
| ×2 | Appraisal Ordered — 88 Livefire Test Lane |
| ×2 | Re: Quick question about closing |

The one-draft-per-task guard (`find_open_task_draft`) is gated on
`if task_id and transaction_id` (`ai_email_engine.py:576`). Every compose path
without both stacks a new row each time it runs.

### S2-11 — Dead-end affordances  **[browser]**

- **"Not linked to a deal" with no way to link it.** Three drafts have
  `transaction_id = null`. The reading pane shows the chip; measured
  `hasFileToDealControl: false`. `POST /ai-emails/inbound/{log_id}/refile`
  (`ai_emails.py:272-353`) exists, already writes `inbound_sender_deal_links` so
  the sender auto-files next time, and **has no UI control anywhere**.
  One of these drafts names its own address in the body — *"your purchase of
  5915 E 350 N, Franklin, IN, 46131"* — and is still unlinked.
- **Recipients are not editable.** Edit mode exposes subject and body only
  (measured `recipientEditable: false`). One draft is addressed to
  `party4@example.com`, a placeholder; the only action available is Discard.

### S2-12 — Stale drafts stay one tap from sending  **[browser]**

The top row asks a client to return a document named `"test"` **by June 22,
2026** — five weeks in the past — under a live "Approve & send" button. Another
(created 2026-07-10, 20 days old) requests an earnest-money receipt by a date
that has also passed. Nothing expires, nothing warns.

### S3-13 — No pagination or server-side limit  **[code-read]**

`list_pending_ai_drafts` takes no `limit` and no cursor. The client fetches every
pending draft in the tenant and filters in memory. Fine at 18; not at 2,000.

### S3-14 — Mobile shows three rows  **[browser]**

At 390×844 the list pane renders about three rows before the reading pane begins,
with the third sliced mid-content. Both panes share one viewport in an `h-full`
shell. No horizontal overflow.

### S3-15 — Three names for one page, and intro prose above the list  **[browser]**

Nav "AI Email Review", breadcrumb "Intelligence › Email review", heading
"Email review". The list pane also opens with two lines of explanatory prose
("Every email here waits for your tap. Turn on Autopilot…"), which
`list-pages-no-intro-prose-lead-with-controls` rules out.

### Health  **[browser]**

**0 console errors, 0 page errors, 0 failed API calls**, at both viewports.
Nothing is broken. The design is wrong.

---

## 4. Root cause, in one line

**Four different questions are being answered by one boolean.**

| Question | Who answers it today | What goes wrong |
| --- | --- | --- |
| Is this about our business? | a regex that fires on CAN-SPAM footers | newsletters pass |
| Which deal is it? | substring match on a composed address | human phrasing misses |
| What kind of message is it? | a question-shape classifier | statements are deleted |
| Should we reply? | the same classifier | relevance and reply-worthiness are fused |

Because they are fused, every fix to one breaks another — which is why threshold
tuning has never worked here.

---

## 5. The solution

Eight principles. Everything in §6 follows from them.

1. **Categorise every message; never gate on "can I reply?"** Relevance,
   deal-linking, category and action are decided independently and displayed
   independently.
2. **Who sent it beats what it says.** A sender matching a
   `transaction_parties`, `contacts` or `vendors` email is relevant whatever the
   content, and arrives pre-linked. The lookup already exists
   (`_candidate_transaction_ids_for_party_emails`, `inbound_dispatch.py:656-712`)
   and is used only for matching. A one-word "ok" from the buyer must never be
   filtered.
3. **Deterministic rules decide only the confident ends; the model decides the
   middle — once per sender, cached.** This raises accuracy *and* cuts cost,
   because the expensive call today is the drafting call that junk reaches.
4. **Triage before persistence — and filtered mail never enters
   `communication_logs`.** `requirements.txt` §6.1 and `SYSTEM_DESIGN.md`
   §2.2.11 define that table as the *immutable master record of communication*,
   on a two-year retention. A filtered newsletter is not communication with a
   party. It goes in its own table, on its own retention, invisible to every
   existing consumer. (Revision 1 got this wrong — see §10 E2.)
5. **Every automatic decision is visible and reversible in one tap, and the tap
   teaches.** The user never categorises, but can always correct, and correcting
   is what tunes the system.
6. **Both streams stay.** Inbound mail *and* outbound composed drafts live on
   this page. This is the constraint the reverted attempt broke.
7. **Money mail is never auto-drafted and never one-click.** Wire instructions,
   EMD, payoff figures: always shown, always pinned, always carrying a
   wire-fraud warning, never answered automatically and never
   `approval_status = auto_approved`.
8. **Safeguards written into `requirements.txt` §6 survive the rebuild.** The
   responsible internal owner is always CC'd (§6.3); assumptions are always
   shown (§6.4); humans always have final say (§6.4).

### What the user gets that they do not have now

- Mail sorted into categories **without touching anything**.
- Every message linked to its deal, or asking a one-tap question when ambiguous.
- A one-line AI summary per message, so triage does not require opening it.
- A suggested **action**, not only a reply — file this document, move this date,
  create this task, acknowledge and close.
- Urgency that means urgency: money, deadline changes and unanswered client
  questions first.
- A notification only when mail actually matters (`requirements.txt` §6.6).

---

## 6. Implementation plan

| Phase | Title | Closes | Est. |
| --- | --- | --- | --- |
| 0 | Drop bulk categories at ingest | S2-08 (ingest) | 0.5 d |
| 1 | Triage funnel before persistence | S1-02, S1-04, S1-05, S2-08 | 3.5 d |
| 2 | A category model that admits statements | S1-03 | 2 d |
| 3 | Deal matching on components | S2-07 | 2 d |
| 4 | The correction loop | S2-11 | 2.5 d |
| 5 | The surface: two streams, real categories | S1-01, S2-09, S3-14, S3-15 | 5 d |
| 6 | Queue hygiene + access control | S1-06, S2-10, S2-12, S3-13 | 2.5 d |
| 7 | Regression corpus + cost telemetry | proves it | 1.5 d |
| 8 | **Real-Chrome verification and defect burn-down** | mandatory | 2 d |

**≈ 21.5 developer-days.** Ship in three releases — see §8.

**Prerequisite, not a phase:** wire the production scheduler
(`/internal/schedules/tick` + `CRON_SHARED_SECRET` + EventBridge). It has never
run in prod (`prod-scheduler-never-wired`), and Phases 1 and 6 add retention and
expiry jobs to it. Nothing in this plan may depend on it for *correctness* —
only for *tidiness* — but the retention promise in §9 Q2 is not kept until it
runs.

---

### Phase 0 — Drop bulk categories at ingest (0.5 d)

**Do not change the Gmail watch.** `create_inbox_watch`
(`gmail_provider.py:728-739`) accepts **one** `labelIds` list and **one**
`labelFilterBehavior`. Switching to `EXCLUDE` does not mean "INBOX but not
Promotions" — it means "everything except these labels", which would start
delivering `SENT`, `DRAFT` and archived mail and make the firehose *larger*. It
would also require the mailbox owner to reconnect, since the notification URL is
baked into the watch. (Revision 1 had this backwards — §10 E1.)

Filter one step later instead, where it is both correct and free. The Gmail
history walk already receives each message's own `labelIds` and already applies
an **include** set through `_message_matches_labels`
(`gmail_provider.py:929-933`), called from `_history_inbox_message_ids`
(`:903-925`). Add a symmetric
**exclude** set there:

- new setting `GMAIL_EXCLUDED_LABEL_IDS`, default
  `CATEGORY_PROMOTIONS,CATEGORY_SOCIAL,CATEGORY_FORUMS,SPAM,TRASH`
- a message carrying any excluded label is dropped from `message_ids` **before
  the per-message body fetch**

Result: no watch re-registration, no owner action, no body ever fetched, nothing
stored, no AI cost — and INBOX scoping is preserved.

Outlook has no label categories; its equivalent (`inferenceClassification =
other`) is advisory only and is handled as a *weak* signal in Phase 1 Stage 2,
never as a drop.

Offer a per-account override for coordinators who file transaction mail into a
dedicated Gmail label — that path is strictly better and should be recommended
in the connect flow.

---

### Phase 1 — A triage funnel that runs before persistence (3.5 d)

New `app/services/email/inbound_triage.py`, called from `dispatch_inbound_email`
**after** the two de-duplication checks and **before** `repo.create`. Each stage
returns a verdict **and a plain-language reason** that is persisted and shown.

```
Stage 0  ingest label exclusion  → never fetched                    (Phase 0)
Stage 1  suppression rules       → filtered, "you filtered this sender"
Stage 2  bulk / automated        → filtered, "bulk mail"
Stage 3  known party / prior thread → ACCEPT, pre-linked
Stage 4  content relevance       → model verdict, cached
Stage 5  persistence             → communication_logs, or inbound_filtered
```

**Stage 2 — real bulk detection.** `_is_auto_generated`
(`ai_email_engine.py:164-179`) checks only `Precedence` and `Auto-Submitted`,
which modern ESPs rarely set. Add `List-Unsubscribe`, `List-Unsubscribe-Post`,
`List-Id`, `X-Auto-Response-Suppress`, `Feedback-ID`, and a `text/calendar` part
with no prose. In the corpus, `List-Id`/`List-Unsubscribe` alone identifies every
newsletter, promotion and notification without reading a word of content.

**Stage 3 — known-party accept.** Promote
`_candidate_transaction_ids_for_party_emails` from a matcher to a relevance
verdict. Sender or any Cc matching a party, contact or vendor in this tenant →
relevant whatever the content, pre-linked to the deal. Extend with "we have
corresponded before": a `thread_key` already linked to a deal, or an
`inbound_sender_deal_links` row, is equally decisive.

**Stage 4 — content relevance, rebuilt.**

- **Delete the footer-address rule.** `_ADDRESS_SIGNAL_RE` may fire only on an
  address found *outside* a detected signature/footer block **and** matching a
  real deal in the tenant (Phase 3). An address matching no deal is not a signal.
- **Tier the term list.** `_TRANSACTION_SIGNAL_TERMS` (`:133-145`) splits into
  **strong** multi-word phrases that stand alone ("closing disclosure", "earnest
  money", "title commitment", "settlement statement", "final walkthrough") and
  **weak** single words ("title", "listing", "loan", "commission", "buyer",
  "seller") that never suffice alone.
- **Invert the AI check.** Deterministic signals decide only the confident ends;
  everything ambiguous asks the model. Cache the verdict per
  `(tenant, sender_domain)` for 30 days.
- **Fail closed, visibly.** Provider down and no strong signal → filtered, with
  the reason "couldn't check — AI unavailable". Today it silently returns `False`
  (`:890`).

**Stage 5 — persistence.**

| Verdict | Where it goes |
| --- | --- |
| relevant | `communication_logs`, full row, exactly as today |
| filtered | **new table `inbound_filtered`** — `tenant_id`, `provider_name`, `provider_ref_id`, `sender_email`, `subject`, `received_at`, `verdict`, `reason`, `source`, `score`, `body_sha256`, `thread_key`, `created_at`. **No body, no body_html.** Own retention (default 30 days). |

**Why a separate table, not a stub row in `communication_logs`** (this is the
single most important correction in revision 2 — §10 E2). A body-less row in
`communication_logs` would have leaked into four live consumers and contradicted
two specs:

| Consumer | What a stub would have done |
| --- | --- |
| `list_recent_thread_messages` (`communication_log_repository.py:202-251`), read by the engine's `_thread_history` (`ai_email_engine.py:1443-1470`) | **Fed an empty-bodied message into the AI's conversation memory** — it filters by status for *outbound* only, so any inbound stub sharing a `thread_key` is included verbatim |
| `analytics_extras.py:495-505` | counted every filtered newsletter as an inbound awaiting reply, poisoning median response time |
| `dashboard_role.py:791-806` | listed filtered mail as "recent threads" in the vendor workspace |
| `list_for_export` (`:254-270`) | exported the user's filtered personal mail into a customer CSV — no pagination, no filter |
| `requirements.txt` §6.1 / `SYSTEM_DESIGN.md` §2.2.11 | that table is the *immutable master log of communication* on a **two-year** retention; a filtered newsletter is neither |

A separate table changes **zero** existing consumers, makes retention a
single-table purge, and keeps the master log honest.

**De-duplication must be preserved explicitly** (§10 E3).
`_find_recent_duplicate_inbound` (`:383-441`) hashes the **body**, so a row with
no body can never match — and that fingerprint exists precisely for the Outlook
case where the same message arrives under different resource IDs. Therefore:

- store `body_sha256` on the `inbound_filtered` row,
- have `_find_recent_duplicate_inbound` also consult `inbound_filtered`, comparing
  against the stored hash rather than recomputing from an absent body,
- keep the `(provider_name, provider_ref_id)` uniqueness check spanning both
  tables.

**Retention.** A purge job on `/internal/schedules/tick`. Correctness never
depends on it: filtered rows are invisible to every surface because of *which
table they are in*, not because of their age.

**Schema note.** `triage_verdict`, `triage_reason`, `triage_score`,
`triage_source` currently exist on `communication_logs` in dev — migration
`20260922090000` was applied and its reversal `20260923090000` shipped with the
revert. Under this design they belong on `inbound_filtered`, with only
`triage_source` retained on `communication_logs` to record *why* a relevant
message was accepted. Verify each environment's actual column state before
writing the migration; do not assume.

---

### Phase 2 — Categories, read in thread context (2.5 d)

**Revised 2026-07-30 after review.** The first cut of this phase categorised on
regex over the *current message only*. That is enough for an opening enquiry and
useless for the second and third message of a thread: *"Yes, Thursday works"*
carries no address, no term of art and no question mark, so it fell to `fyi` and
produced nothing. The drafter already receives thread history — so the regex gate
deciding *whether to draft* was strictly dumber than the component it gated.

So relevance, category and deal matching are answered by **one model call that
receives the last turns of the thread**, and the regex classifier becomes the
fallback for when the provider is unavailable.

```
analyze_inbound(message, thread_so_far[], candidate_deals[])
  → {related, category, transaction_id|null, confidence, evidence}
```

Deterministic signals still run first and still short-circuit — the model is
never asked what a cheap exact signal already knows:

| Situation | Model call? |
| --- | --- |
| suppression rule / bulk headers | no |
| known party, filed thread, `[VE-TX-…]` tag | **relevance:** no · **category:** yes |
| term of art in the body | **relevance:** no · **category + deal:** yes |
| nobody we recognise, nothing we know | yes — all three answers |

Known-party mail still costs a categorisation call, deliberately: that is
precisely the traffic most likely to be a context-dependent follow-up. It is a
small call, and it replaces the *drafting* call that junk used to reach.

`KIND_OTHER` stops being a drop. Relevance decides whether a message appears;
**category** decides what we offer to do about it.

| Category | Appears | AI action | `auto_approved` eligible |
| --- | --- | --- | --- |
| `question` (today's `factual`) | yes | reply draft | yes |
| `document_request` | yes | reply draft + attach from the deal | yes |
| `document_delivery` — "report attached" | yes | acknowledge + file the document | no |
| `schedule_change` — "closing moved to the 14th" | yes | acknowledge + propose the date change | no |
| `status_update` — "appraisal came in at $312k" | yes | **no reply needed** — summarise and file | no |
| `money` — wire, EMD, payoff | yes, **pinned** | **never auto-draft**, standing fraud warning | **never** |
| `vendor_reply` | yes | existing proposal flow | no |
| `fyi` | yes, low priority | no draft | no |

Implementation notes the code demands:

- **No DB migration is needed for the new values.** There is no CHECK constraint
  on `communication_logs.ai_kind` anywhere in `supabase/migrations/`.
- **The `auto_approved` gate must be rewritten as an allow-list.** It is
  currently `kind in (KIND_FACTUAL, KIND_DOCUMENT_REQUEST)`
  (`ai_email_engine.py:378-386`). New categories default to *not* eligible, which
  is correct — but state the allow-list explicitly so `money` can never be added
  by a later edit.
- **`KIND_LABEL` in `AiEmailReviewPage.tsx:67-74` needs an entry per category**,
  or new categories render as a bare "Reply".
- A relevant message with no recognised category is `fyi` — it appears with no
  draft, which is an honest outcome and costs nothing.
- Categories are assigned by the same cached model call that settles relevance,
  so the category is free.

This alone recovers all six messages lost in S1-03 and puts wire instructions on
screen with a warning instead of deleting them.

---

### Phase 3 — Deal matching that survives human phrasing (2 d)

**Revised 2026-07-30 after review: retrieve deterministically, then let the model
rank — and let it abstain.**

The exact signals stay primary and are never routed through a model, because a
model cannot improve on them and can only add cost, latency and a dependency:
`thread_key`, the `[VE-TX-…]` tag on our own outbound, a learned
`inbound_sender_deal_links` row, and a sender who is a party on exactly **one**
open deal. For a coordinator with six live files these settle most mail.

The model handles only the residue those miss — an unknown sender referring to a
property in prose (*"the Oak Ridge file"*, *"the Boardman closing"*) — under
three rules:

- **It ranks a shortlist, it does not search.** Candidates are built
  deterministically (party deals first, then open deals, capped at 8), so the
  prompt stays bounded as a tenant grows.
- **An id it was not offered is rejected outright** — a hallucination guard, not
  a nicety.
- **It must be able to abstain, and confidence gates filing.** Below
  `MATCH_CONFIDENCE_FLOOR` (0.75) the message stays unlinked and the UI asks
  "which deal?". A wrong match is worse than none: the message lands on the
  wrong file and the drafter then answers using *that* deal's closing date and
  parties, one tap from a real client.

Every human answer to that question writes `inbound_sender_deal_links`, so the
same correspondent is never sent to the model twice — **the AI cost is one-time
per sender, not per message.** The `evidence` string ("street name + buyer's
name") is displayed, so a wrong match is correctable rather than mysterious.

The scorer still gets fixed, as the no-provider fallback and the cheap path:

1. **Match on components, not the composed string.** Parse each deal address once
   into `{street_number, street_name, unit, city, state, zip}` and score against
   those. **Street number + street name is a strong match on its own**; city,
   state and zip become confirmations, not requirements.
2. **Drop the bare-state point** (`:840-841`).
3. **Use `thread_key`.** Already stamped on every inbound (`:118-124`) and never
   used for matching. If any earlier message on the thread is linked to a deal,
   this one inherits it — exact, free, and it is the same signal Stage 3 uses for
   relevance.
4. **Add a subject-line pass** for `Re:` chains that name the address only in the
   subject.
5. **Ambiguity asks instead of guessing.** Two candidates within one point →
   record both and show a two-option "Which deal?" chip. This fixes the Oak Ridge
   / Meadowridge tie, which today resolves to `None`.
6. **Backfill** the three composed drafts with `transaction_id = null` from
   `ai_source_data.task_id`; discard any that cannot be resolved rather than
   leaving them sendable.

---

### Phase 4 — The correction loop (2.5 d)

Two actions. Both one tap. Both teach.

**"Not mail I need"** — `POST /ai-emails/inbound/{id}/not-relevant`: discards any
draft, **moves the row from `communication_logs` to `inbound_filtered`**, and
writes an `inbound_suppression_rules` row scoped to the tenant and keyed by
sender address, sender domain, or `List-Id` — the user picks the scope in the
confirm (*this sender* / *everyone at this domain* / *this mailing list*).
Undoable for 30 days; every rule listed and editable in Settings → AI &
Automation. Stage 1 consults these first.

**"Actually, I need this"** — the reverse, and it needs a body that was never
stored (§10 E4). Restore therefore:

1. re-fetches the message from the provider by `provider_ref_id`, reusing the
   machinery `inbound_hydration.py` already has (`_HYDRATABLE_PROVIDERS =
   {gmail, outlook}`, tenant-mailbox fallback, `_MAX_INTEGRATION_ATTEMPTS`),
2. inserts it into `communication_logs` and runs the normal inbound hooks,
3. and when the provider can no longer supply it (disconnected, deleted, iCloud),
   inserts what we do have and sets the established `metadata_json.body_preview_only`
   flag so the UI says so honestly rather than showing a blank message,
4. and records `triage_source = 'user'` so the corpus and telemetry can learn
   from it.

**"File to deal"** — surface the existing
`POST /ai-emails/inbound/{log_id}/refile` (`ai_emails.py:272-353`). It already
re-points the log, writes `inbound_sender_deal_links` so that sender auto-files
next time, and re-drafts against the right deal. It needs a deal picker in the
row and in the reading pane, and nothing else.

All three write `log_ai_email_action`, so the filter's behaviour is explainable
after the fact — and `requirements.txt` §6.1's *"users can report errors for AI
training"* is finally implemented.

---

### Phase 5 — The surface (5 d)

**One page, two streams.** Route `/ai-emails` stays, and `/ai-emails/:logId`
must keep resolving — escalation emails and the Needs-You queue deep-link into it
(`FRONTEND_UI_WORKFLOW_LOGIC.md` §6.4), including for a message that now lives in
a different view. Name it once — nav, breadcrumb and heading all read **"Email"**
under Intelligence (S3-15), and the intro prose above the list goes.

```
┌──────────────┬────────────────────────┬──────────────────────────────┐
│ Needs you  6 │ ● Sarah Chen      2h   │  [thread, oldest → newest]   │
│ Incoming  12 │   Oak Ridge · Document │                              │
│ Outgoing   9 │   "commitment ready"   │  AI summary                  │
│ Waiting    3 │ ─────────────────────  │  Facts the AI used           │
│ Filtered  87 │ ⚑ Escrow          6h   │  Check these before sending  │
│              │   Oak Ridge · MONEY    │                              │
│ ── Deals ──  │   "wire instructions"  │  [Approve & send] [Edit]     │
│ Oak Ridge  3 │ ─────────────────────  │  [File to deal] [Not for me] │
│ Riverstone 2 │ ○ Task exec       1d   │  [Mark done]                 │
│ Unlinked   1 │   Harness · Outgoing   │                              │
└──────────────┴────────────────────────┴──────────────────────────────┘
```

**Views** — segmented pills per `STYLE_GUIDE.md` §"Filters are chips / segmented
pills", and each shows genuinely different rows (the 2026-07-10 "tabs that show
the same list" mistake must not return):

- **Needs you** *(default)* — relevant mail unanswered or with a draft waiting,
  plus outgoing drafts awaiting approval.
- **Incoming** — every relevant inbound message, threaded, drafted or not.
- **Outgoing** — the AI-composed task email that is 17/18 of today's queue, with
  its approve / edit / discard / send-all-ready lifecycle **unchanged**.
- **Waiting** — we replied, awaiting their response. Ages visibly.
- **Filtered out** — reads `inbound_filtered`, each row with its reason and a
  one-tap **"Actually, I need this"**. This is what makes an aggressive filter
  safe to ship.

**Endpoints.** `GET /ai-emails/drafts` keeps its exact contract for the Outgoing
view and the bell badge. Two additions: `GET /ai-emails/messages` (relevant
inbound, cursor-paged, view + deal filters) and `GET /ai-emails/filtered`
(cursor-paged over `inbound_filtered`). All three take the same role guard as
Phase 6.

**Deal rail** — per-deal counts, **Unlinked** pinned at the top carrying the
"Which deal?" flow from Phase 3.

**The row** — `● Sarah Chen · 2h` / `Oak Ridge Ave · Document` / one-line AI
summary / state chip. The category is on the row; the user never assigns it.

**Ordering — replace escalation-first** (S2-09), highest first:

1. money / wire-instruction mail
2. a deadline or closing-date change
3. a client question unanswered > 24 h
4. relevant but unlinked (needs a human decision)
5. a draft ready to send
6. everything else, newest first

Staleness becomes a **badge** ("waiting 9 days"), not a rank. Because prod has
never escalated anything, validate the new ordering against both an escalated
(dev) and an un-escalated (prod-shaped) data set.

**Conversation pane** — keep verbatim what is already good: the sandboxed HTML
frame, the assumptions panel (`requirements.txt` §6.4), the "Facts the AI used"
rail, the `body_preview_only` notice, "Nothing sends until you approve it". Add
the full thread oldest → newest (`thread_key` already groups it) and the AI
summary.

**Editable recipients, with one hard rule.** To / Cc / Bcc become real inputs and
attachments are pickable from the deal's documents — **but the responsible
internal owner's Cc chip is not removable.** `requirements.txt` §6.3 requires the
owner to be CC'd on every AI response, and the engine adds them deliberately
(`ai_email_engine.py:367-372`, *"CC the responsible internal owner so they're
never blind to a send"*). Revision 1's free-form Cc editing would have let a user
delete that safeguard (§10 E5). Everyone else can be added or removed freely.

**Notifications** (`requirements.txt` §6.6). Triage decides what notifies:
relevant inbound raises a "communication received" notification; filtered mail
never does. Keep the bell counting rule from
`notification-badge-mark-all-read-fix` — never count drafts unconditionally.

**Bulk actions** — explicit checkbox selection with a live count and a confirm
that names the recipients. Bulk *file to deal*, *not relevant* and *mark done*
are the valuable ones; bulk send stays deliberately awkward.

**Mobile** (S3-14) — push navigation: the list fills the viewport, tapping a row
slides in the conversation with a back control and a pinned action bar, per
`app-pages-own-their-scroll` (`h-full min-h-0` shell, inner `overflow-y-auto`).
Views become a select; the deal rail becomes a sheet.

**Keyboard** — `j`/`k` move, `Enter` open, `e` done, `r` reply, `f` file to deal,
`!` not relevant, `/` search, `?` shortcuts. Roving tabindex, `aria-live` on the
counts, visible focus rings.

**Deliverable:** rewrite `FRONTEND_UI_WORKFLOW_LOGIC.md` §6.4 to match. It is
already stale (S1-01) and this phase would strand it further.

---

### Phase 6 — Queue hygiene and access control (2.5 d)

- **Access control (S1-06).** Put `require_role(AGENT, TRANSACTION_COORDINATOR,
  TEAM_LEAD, ADMIN)` on `GET /drafts`, `GET /{log_id}` and
  `GET /{log_id}/parent`, matching the sibling endpoints, and scope the query to
  files the caller can act on so §6.4's documented behaviour becomes true. Apply
  the same guard to the two new endpoints in Phase 5. **Ship this in R1** — it is
  a one-line-per-endpoint change and it is the only finding here with a
  confidentiality consequence.
- **Duplicates (S2-10).** Extend the `find_open_task_draft` guard to every
  compose path via a natural key — `(tenant, transaction, recipient,
  template/category, day)` — not only the paths passing `task_id`. Add a partial
  unique index so it holds under concurrency, and reconcile the existing
  ×4/×2/×2 groups.
- **Staleness (S2-12).** A draft older than 7 days, or one quoting a date now
  past, shows a "facts may have changed — regenerate before sending" banner and
  is excluded from bulk send. Auto-expiry at 30 days rides the scheduler tick and
  is therefore *tidiness*; the banner and the bulk-send exclusion are computed at
  read time and hold with or without the cron.
- **Pagination (S3-13).** `limit` + cursor on `list_pending_ai_drafts`; the list
  virtualises and pages at 50; counts come from a `count` query.

---

### Phase 7 — Regression corpus and cost telemetry (1.5 d)

The corpus from this test becomes a checked-in fixture —
`app/tests/fixtures/inbound_corpus.jsonl`, ~120 labelled messages: real
transaction mail, newsletters, receipts, social, personal, adversarial edges, and
every message from this run. `app/tests/test_inbound_triage.py` asserts against
it, and CI fails on regression.

| Metric | Target | **Measured today** |
| --- | --- | --- |
| Precision of what reaches the user | ≥ 0.95 | **0.40** (2 of 5 drafted were real) |
| Recall on genuine transaction mail | ≥ 0.98 | **0.25** (2 of 8) |
| Known-party mail shown | 1.00 | not a rule today |
| Money-shaped mail auto-drafted | 0.00 | not modelled |
| Junk reaching the queue | 0 of 12 | **3 of 12** |
| Filtered mail in `communication_logs` | 0 | n/a — everything is stored |

**Cost telemetry.** Record provider, model, token counts and verdict source per
triage decision, grouped by `triage_source`, and surface it on `/platform/costs`.
The design intent is that a junk message costs **one cached classification and no
drafting call**, versus today's uncached relevance call plus a full context-laden
drafting call. Publish the real before/after per tenant rather than asserting a
number, and add a per-tenant daily triage budget with a visible cap.

---

### Phase 8 — Real-Chrome verification (mandatory, 2 d)

**This phase is not optional and the work is not done without it.** No phase may
be reported complete on unit tests alone.

Run against a fresh backend and a fresh vite pointed at it, in **system Chrome**,
at **1600×1000 and 390×844**, capturing console errors, page errors and failed
API calls throughout.

| # | Check | Passes when |
| --- | --- | --- |
| V1 | Seed the tenant with the labelled corpus through the real inbound path | every message lands in exactly one view |
| V2 | Junk (LinkedIn, Zillow, recruiter, utility bill, Home Depot, bank alert) | **0 drafts**; all in Filtered out with a readable reason |
| V3 | Statement mail (title commitment, appraisal, clear-to-close, "ok") | all visible in Incoming, correctly categorised |
| V4 | Wire-instruction mail | visible, pinned, fraud warning shown, **no draft**, not `auto_approved` |
| V5 | "Actually, I need this" | restores it **with its body re-fetched**, or shows the honest preview-only notice; sender not filtered again |
| V6 | "Not mail I need" | filters it, writes the rule, rule undoable from Settings |
| V7 | "File to deal" on an unlinked message | links it, re-drafts, next mail from that sender auto-files |
| V8 | Deal rail counts | match the DB, and "Unlinked" resolves in one tap |
| V9 | Outgoing view | still lists composed task drafts; approve / edit / discard / send-all-ready all work |
| V10 | Ordering | money first, stale drafts badged not ranked — verified on **both** an escalated and an un-escalated data set |
| V11 | Edit mode | To / Cc editable **and the owner Cc chip cannot be removed**; changes persist on send |
| V12 | Duplicates | corpus replay produces exactly one draft per task |
| V13 | Mobile 390×844 | full-height list, push navigation, no clipped pane |
| V14 | Health | 0 console errors, 0 page errors, 0 failed API calls |
| V15 | **Log in as a Client-role user** (S1-06) | `/ai-emails` and its API return 403, not other people's drafts |
| V16 | **`communication_logs` contains no filtered mail** (S1-04, Phase 1) | direct DB query returns 0 rows; export CSV contains none |
| V17 | **AI thread history is clean** | a filtered message sharing a `thread_key` never appears in `_thread_history` output |
| V18 | Deep link `/ai-emails/:logId` | resolves for inbound, outbound and restored messages |
| V19 | **A 3-message thread** — enquiry, our reply, then a bare "Yes, Thursday works" | the third message is kept, filed to the same deal, and categorised from the thread rather than falling to `fyi` |
| V20 | **Prose deal reference** from an unknown sender ("any update on the Oak Ridge file?") | filed to the right deal with visible evidence, or left unlinked with a "which deal?" chip — never filed to the wrong one |
| V21 | **Provider unavailable** mid-run | messages still land (deterministic fallback), nothing is lost, and "Filtered out" says why where it applies |

**Every defect found in V1–V18 is fixed and the whole table is re-run from the
top until it passes clean.** The verification run is written up with screenshots
in `velvet-elves-data/` and the harness scripts are checked in beside the
existing `_tools/e2e/er2_*` set.

---

## 7. What must not break

- Nothing sends without a human tap. `handle_inbound` never calls the provider,
  and `auto_approved` is a label the UI renders as one-click — never an auto-send
  (`requirements.txt` §6.4, *"humans always have final say"*).
- **The responsible internal owner is CC'd on every AI response**
  (`requirements.txt` §6.3).
- No AI disclosure ever reaches a recipient
  (`ai-emails-review-redesign-no-ai-disclosure`).
  **Documented deviation:** `requirements.txt` §6.3/§6.5 still mandate an AI
  disclaimer on AI-sent mail. That was deliberately reversed; the send path and
  `_legacy_tenant_disclaimers` (`ai_emails.py:1158`) actively strip legacy
  disclaimers. The current behaviour is correct and the requirement is stale —
  recorded here so nobody "fixes" it back.
- The assumptions panel and the grounded "Facts the AI used" rail
  (`requirements.txt` §6.4).
- Sandboxed HTML rendering with scripts blocked.
- The `body_preview_only` honesty notice.
- The reconnect-mailbox banner path.
- **The outbound composed-draft lifecycle** — the reason the last attempt was
  reverted.
- `communication_logs` stays the immutable master record of *communication*
  (`SYSTEM_DESIGN.md` §2.2.11, `requirements.txt` §6.1). Triage writes nothing
  into it that is not a real message.

---

## 8. Sequencing

- **R1 — "stop the noise" (Phases 0–2 + the S1-06 access-control fix, ≈ 6.5 d).**
  Ingest-level category exclusion, real bulk detection, known-party accept, the
  footer-address rule deleted, statements no longer dropped, filtered mail
  diverted out of `communication_logs`, and the read endpoints role-guarded. On
  this corpus that takes junk drafts from 3-of-12 to 0 and recovers all six lost
  transaction emails. **This is the release the client is waiting for.**
- **R2 — "make it correctable" (Phases 3–4, ≈ 4.5 d).** Component matching, "File
  to deal", "Not mail I need", restore-with-refetch.
- **R3 — "make it good" (Phases 5–8, ≈ 10.5 d).** The categorised two-stream
  surface, hygiene, the regression corpus, and the mandated Chrome verification.

**Do not defer Phase 1 Stage 5 past R1.** Every day the current code runs against
a live personal mailbox, it copies more of that mailbox into a table on a
two-year retention.

---

## 9. Decisions needed before R1

| # | Question | Who | Default if unanswered |
| --- | --- | --- | --- |
| 1 | Drop Gmail's Promotions / Social / Forums at ingest, or require a dedicated label? | Jake / Audri | Drop the three categories; dedicated label offered as the better option |
| 2 | Retention for `inbound_filtered` rows | Jake | 30 days, then purge |
| 3 | Keep a body-less filtered record at all, or write nothing? | Jake | Keep it — needed for de-dup, for "Filtered out", and for the correction loop |
| 4 | Default suppression scope | Audri | Sender, with domain offered in the confirm |
| 5 | Ship the new surface behind a flag beside the old one, or replace outright? | Jake | Flag `ve_email_v2`, default on in dev |
| 6 | Should Attorney-role users see the email surface? | Jake | No — matches the current sidebar, and S1-06 makes it real |

**Owner/infra actions, not developer actions:** wiring the production scheduler
(`CRON_SHARED_SECRET` + EventBridge), and any Google verification work on the
Gmail watch. Phase 0 as revised needs **no** mailbox reconnection.

---

## 10. Review log — errors found in revision 1 and how they were corrected

| # | Error in revision 1 | Correction |
| --- | --- | --- |
| **E1** | Phase 0 said to re-register the Gmail watch with `labelFilterBehavior: EXCLUDE`. `create_inbox_watch` takes one label list and one behavior, so EXCLUDE **removes the INBOX restriction** — the watch would start firing on `SENT`, `DRAFT` and archived mail, *enlarging* the firehose. It also forced an owner reconnect. | Leave the watch on `INCLUDE ["INBOX"]`. Exclude categories in the history walk, where `labelIds` are already available and `_message_matches_labels` already exists — before any body fetch. No owner action needed. |
| **E2** | Filtered mail was to be stored as a body-less stub **in `communication_logs`**. That table feeds `_thread_history` (the AI's own conversation memory), response-time analytics, the vendor workspace, and the customer CSV export — and `requirements.txt` §6.1 / `SYSTEM_DESIGN.md` §2.2.11 define it as the immutable master log of *communication* on a two-year retention. | Filtered mail goes in a new `inbound_filtered` table. Zero existing consumers change; retention is a one-table purge; the master log stays honest. |
| **E3** | Claimed "de-duplication keeps working (it keys on `provider_ref_id` and a fingerprint)". The fingerprint hashes the **body**, so a body-less record can never match — breaking exactly the Outlook duplicate case the fingerprint exists for. | Store `body_sha256` on the filtered row; have `_find_recent_duplicate_inbound` consult both tables and compare against the stored hash. |
| **E4** | "Actually, I need this" restored a message whose body was never stored — the user would get a blank message. | Restore re-fetches from the provider by `provider_ref_id` using `inbound_hydration.py`'s existing machinery, and falls back to the established `body_preview_only` honesty notice when the provider cannot supply it. |
| **E5** | Made To / Cc / Bcc freely editable, which lets a user delete the responsible internal owner from the Cc — violating `requirements.txt` §6.3 and the safeguard the engine adds deliberately. | The owner's Cc chip is non-removable; everyone else is freely editable. Verified by V11. |
| **E6** | 30-day purge and 30-day draft expiry were assigned to a scheduler that **has never run in production**, making a retention promise the product would not keep. | Scheduler wiring is called out as an explicit R1 prerequisite; the purge rides the existing tick; and no correctness claim depends on it — filtered mail is invisible because of *which table it is in*, not its age. |
| **E7** | S2-09 (escalation-first ordering) was stated as universal. `escalation_sent_at` is written by a job that has never run in prod, so prod ties at one priority instead. | Environment caveat added to the finding; V10 validates the fix on both escalated and un-escalated data. |
| **E8** | New categories were introduced without saying what they do to `auto_approved` eligibility, to the frontend `KIND_LABEL` map, or to DB constraints. | Eligibility is now an explicit allow-list column in the Phase 2 table with `money` marked **never**; `KIND_LABEL` is called out; confirmed there is no CHECK constraint on `ai_kind`, so no migration is needed. |
| **E9** | The redesign never mentioned `/ai-emails/:logId`, which escalation emails and the Needs-You queue deep-link into. | Deep-link preservation is stated in Phase 5 and verified by V18. |
| **E10** | Missed entirely: `GET /drafts`, `GET /{log_id}` and `GET /{log_id}/parent` have **no role guard**, so any tenant user — including Client, Vendor and FSBO roles — can read every AI draft and every original inbound body. §6.4 documents a role scope that does not exist in code. | Added as finding **S1-06**, fixed in Phase 6, pulled forward into R1, and verified by V15. |

Two further alignments made while reviewing: notifications
(`requirements.txt` §6.6) are now triage-gated rather than unmentioned, and the
stale `FRONTEND_UI_WORKFLOW_LOGIC.md` §6.4 spec is an explicit Phase 5
deliverable rather than being left to drift.
