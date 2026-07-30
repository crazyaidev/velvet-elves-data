# Intelligence › Inbox — implementation report

**Date:** 2026-07-30
**Implements:** `EMAIL_REVIEW_REBUILD_PLAN_2026-07-30.md` (all seven phases)
**Closes:** E-01 … E-20 from `EMAIL_REVIEW_ISSUES_2026-07-30.md`
**Status:** built, tested, running locally. Uncommitted.

---

## 1. The change in one line

The unit of display is now the **message**, not the AI draft — and relevance is
decided **before** anything is stored, with the reason kept and shown.

## 2. Verified results

Re-running the corpus that produced the original findings, through the real
pipeline (real matcher, real relevance gate, real OpenAI calls):

| # | Message | Before | After |
| --- | --- | --- | --- |
| L01 | "when is closing for 4567 Oak Ridge Avenue…" | kept + drafted | kept, drafted, filed on the deal |
| L02 | "The title commitment for 8104 Riverstone Place is ready" | **dropped silently** | kept, `document_delivery`, **filed on the deal** |
| L03 | "The appraisal for 5915 E 350 N came in at $312,000" | **dropped silently** | kept, `document_delivery`, **filed on the deal** |
| L04 | "we can come out to 77 Harness Test Lane. Scheduled: …" | drafted, unfiled | kept, `vendor_reply`, **filed on the deal** |
| L05 | CRM sales pitch | **junk drafted** | filtered — `bulk_list_header` |
| L06 | Recruiter | **junk drafted** | filtered — `bulk_list_header` |
| L07 | LinkedIn notification | **junk drafted** | filtered — `bulk_list_header` |
| L08 | "Dinner Sunday?" | filtered | filtered — `ai_unrelated` |
| L10 | Zillow listing alert | **junk drafted** | filtered — `bulk_list_header` |

**Junk reaching the queue: 4 of 5 → 0 of 5. Real mail lost: 2 of 3 → 0 of 3.**
Every filtered message stored subject and sender only — **no body**.

That run surfaced one regression, since fixed: L09 ("hey / any update?" from a
client who had written before) was filtered, because nothing modelled *we
already correspond with this person about a deal*. `_has_prior_deal_correspondence`
now checks both directions of history; confirmed read-only against the live
database (5/5 senders classified as expected).

Other measurements:

| Check | Result |
| --- | --- |
| Address matcher on real phrasing | **8/8** (was: 2 of the 8 scored 7 against a threshold of 8) |
| Triage regression suite | **43/43** |
| Full backend suite | **1432 passed** |
| `tsc --noEmit`, `eslint`, `vite build` | clean |
| Browser: failed API calls / console errors / page errors | **0 / 0 / 0** |
| Inbox response time | 0.5 s warm |
| Search "Riverstone" | **9 rows** (was 0 — the mail existed but had no draft) |

## 3. What was built

### Backend

| File | What |
| --- | --- |
| `app/services/email/inbound_triage.py` | **new** — the five-stage funnel, the verdict type, footer stripping, bulk detection, the AI arbiter, the domain verdict cache |
| `app/services/inbox_service.py` | **new** — assembles messages into the four views, the urgency model, deal counts |
| `app/repositories/inbound_suppression_repository.py` | **new** — "not mail I need" rules, hashed senders |
| `supabase/migrations/20260922090000_inbound_triage.sql` | **new** — `triage_*` columns, `inbound_suppression_rules`, index. **Applied to the dev database.** |
| `app/services/email/inbound_dispatch.py` | triage before persistence, stub-not-store, thread-key matching, component address scoring, known-party and prior-correspondence checks, candidate recording |
| `app/services/ai_email_engine.py` | statement intents, money never auto-drafted, intent stamped on the inbound row, acknowledgement drafters, compose de-duplication |
| `app/services/email/gmail_provider.py` | category exclusion at fetch |
| `app/api/v1/ai_emails.py` | `GET /inbox`, `POST /inbound/{id}/not-relevant`, `POST /inbound/{id}/restore`, suppression-rule list/delete |
| `app/tests/test_inbound_triage.py` | **new** — 43 tests, the labelled corpus, precision/recall assertions |

### Frontend

| File | What |
| --- | --- |
| `src/pages/InboxPage.tsx` | **new** — the rebuilt surface |
| `src/hooks/useInbox.ts` | **new** — inbox + correction-loop hooks |
| `src/components/inbox/EmailBodyView.tsx`, `SourceFacts.tsx` | **new** — the parts of the old page worth keeping, extracted verbatim |
| `src/App.tsx`, `src/utils/constants.ts`, `src/layouts/AppLayout.tsx` | `/inbox` route, `/ai-emails` redirects, nav renamed, badge aligned to the page's own count |

`AiEmailReviewPage.tsx` is now unreferenced and can be deleted once the new
surface has been through a round of real use.

## 4. Issue-by-issue

| ID | Status | How |
| --- | --- | --- |
| E-01 | closed | Promotions/Social/Forums/Spam/Trash never fetched; filtered mail stored as a body-less stub |
| E-02 | closed | Footer stripped before any address test; a street address counts only above the fold |
| E-03 | closed | `List-Unsubscribe`, `List-Unsubscribe-Post`, `List-Id`, `Feedback-ID`, `X-Campaign-Id` |
| E-04 | closed | Terms split strong/weak; weak words never accept alone |
| E-05 | closed | `document_delivery`, `status_update`, `schedule_change`, `money`, `fyi`; `KIND_OTHER` only for empty messages |
| E-06 | closed | Component scoring anchored on street number + street name |
| E-07 | closed | Bare state point removed |
| E-08 | closed | "Not mail I need" writes a suppression rule triage consults first |
| E-09 | closed | The row is the message; **Filtered out** shows every rejection with its reason |
| E-10 | closed | "Which deal is this about?" with the matcher's guesses one tap each |
| E-11 | closed | Urgency model: money → date change → unanswered >24 h → unlinked → draft ready. Staleness is a badge |
| E-12 | closed | `find_open_duplicate_draft` on (deal, recipients, subject, day) |
| E-13 | closed | To / Cc / Subject / Body all editable |
| E-14 | closed | Paged at 50; per-message queries scoped to the page |
| E-15 | closed | Mobile is list → detail with a back control; both verified full-screen, no overflow |
| E-16 | closed | Regenerate is intent-aware; irrelevant mail offers filtering instead |
| E-17 | closed | "Inbox" everywhere |
| E-18 | closed | Drafts over 7 days show a staleness banner |
| E-19 | closed | Four views, deal rail, deal-aware search |
| E-20 | closed | Unlinked messages get the deal picker |

## 5. Design decisions worth knowing

**Filtering is aggressive, and that is only safe because it is visible.** Every
rejection is a row in **Filtered out** carrying one plain sentence, and
"Actually, I need this" restores the message, revokes the rule, re-fetches the
body and re-runs the drafter.

**Relevance and reply-worthiness are separate.** A status update appears with
"No reply needed". That is an outcome, not an omission, and the pane says so.

**Money mail is never auto-drafted.** Wire-fraud interception works by getting a
plausible reply into a real thread. `money` is surfaced, pinned to the top of
the urgency model, and carries a standing verify-by-phone warning.

**Who sent it beats what it says.** A known party, or anyone we already
correspond with about a deal, is relevant whatever the wording — a one-word
"ok" from the buyer must never be filtered for lacking vocabulary. The
deterministic content rules honestly cannot classify "we can come out.
Scheduled: 2026-08-15"; the test suite states that boundary rather than
pretending otherwise.

**Suppression stores no plaintext addresses.** SHA-256, with a masked label for
the managed list, following `inbound_sender_deal_links`.

## 6. Still needs a person

1. **Reconnect Gmail after fixing the tunnel.** `EMAIL_WEBHOOK_PUBLIC_BASE_URL`
   and `PUBSUB_PUSH_AUDIENCE` still point at a retired ngrok URL, and the
   notification URL is baked into the watch, so live inbound stays dead until
   someone re-consents. Everything above was verified by calling the dispatcher
   directly — the same function the webhook calls.
2. **Apply the migration to stage and prod.** `20260922090000_inbound_triage.sql`
   is applied to **dev only**. It is additive and idempotent. Per
   `staging-textract-ocr-only-mode-checkbox-blind`, replay every stage fix onto
   prod deliberately rather than assuming.

Open product questions from §9 of the plan (category exclusion, stub retention,
default suppression scope) shipped on their documented defaults; all three are
config, not code.

## 7. Test data

The **Filtered out** view is empty locally because the probe rows were purged
during verification. It populates as mail arrives. The filter itself is covered
by the 43-test corpus, which runs in CI.
