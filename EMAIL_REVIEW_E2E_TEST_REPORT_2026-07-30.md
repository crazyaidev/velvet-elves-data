# Intelligence › Email review — E2E test report

**Date:** 2026-07-30
**Surface under test:** `/ai-emails` (nav label "AI Email Review", page title
"Intelligence › Email review") plus the whole inbound path that feeds it.
**Tester account:** `shyna.elene@minafter.com` — Admin, platform admin,
tenant `526cf077-59da-496a-aa38-8f8d761c29da`.
**Outcome:** the reported problem reproduces exactly, and it is not a
tuning issue. See `EMAIL_REVIEW_ISSUES_2026-07-30.md` for the 20 defects and
`EMAIL_REVIEW_REBUILD_PLAN_2026-07-30.md` for the fix + rebuild.

> **No source code was changed.** Everything below was produced by running the
> shipped code as-is against the local dev stack.

---

## 1. Environment

| Piece | Value |
| --- | --- |
| Backend | fresh `uvicorn app.main:app` on `127.0.0.1:8001` (the long-lived `:8000` instance serves stale code) |
| Frontend | `vite` on `localhost:3000` with `VITE_API_BASE_URL=http://localhost:8001` (`:3000` is in `CORS_ORIGINS`) |
| Browser | system Chrome via puppeteer-core, real login through the UI form |
| AI provider | `AI_PROVIDER=openai`, `OPENAI_MODEL=gpt-5.4` (live calls, not stubbed) |
| Mailbox | Gmail `crazyaidev20500519@gmail.com`, integration active, `token_status=healthy` |
| Transactions in tenant | 6, all `Active` |

Gmail push into this environment is dead (`EMAIL_WEBHOOK_PUBLIC_BASE_URL` and
`PUBSUB_PUSH_AUDIENCE` point at a retired ngrok tunnel), so inbound mail was
injected by calling `dispatch_inbound_email` directly — the exact function the
Gmail webhook calls, with the real `ai_email_inbound_hook` registered. Every
message therefore ran the real matcher, the real relevance gate, the real
classifier, the real OpenAI calls and the real draft writer.

## 2. What was run

| # | Harness | What it does |
| --- | --- | --- |
| 1 | `_tools/e2e/er_gate_probe.py` | Runs the shipped predicates (`_is_auto_generated`, `_classify`, `_has_real_estate_signal`) over a 38-message corpus of realistic mailbox traffic. No DB, no AI. |
| 2 | `_tools/e2e/er_live_dispatch.py` | Pushes 10 messages through the full live pipeline and reports what each produced. |
| 3 | `_tools/e2e/er_ui_01_survey.mjs` | Real browser: queue contents, every row, search, keyboard, mobile viewport. |
| 4 | `_tools/e2e/er_ui_02_actions.mjs` | Real browser: reading pane, deep links, edit mode, available controls. |
| 5 | `_tools/e2e/er_ui_03_lifecycle.mjs` | Real browser: discard (cancel + confirm), regenerate, duplicates, escalation, reachability of undrafted mail. |

Screenshots: `c:\Projects\_shots\emailreview\er-01 … er-15`.

## 3. Result 1 — the relevance gate, on a realistic corpus

38 messages: 10 genuine transaction mails, 20 ordinary mailbox items
(newsletters, receipts, social, personal), 8 adversarial edges. Every
non-transaction message carried the CAN-SPAM postal address that US commercial
email is legally required to include.

| Signal | Result |
| --- | --- |
| Messages where the **deterministic** signal fired (so the AI relevance check never ran) | **25 of 38** |
| Unrelated messages whose only "real-estate signal" was the footer street address | **18 of 20** |
| Unrelated messages that would produce a draft with no AI check at all | 3 (LinkedIn, a CRM sales pitch, a recruiter) |
| Genuine transaction mail dropped by the classifier before any gate | 1 (a title company's "commitment is ready") |

Bulk-mail headers:

| Header | Recognised as automated? |
| --- | --- |
| `Precedence: bulk` | yes |
| `Auto-Submitted: auto-generated` | yes |
| `List-Unsubscribe` | **no** |
| `List-Id` | **no** |

`List-Unsubscribe` is the header Gmail itself uses to render its Unsubscribe
button; it is present on essentially every real newsletter. `Precedence: bulk`
is largely legacy.

## 4. Result 2 — the same 10 messages through the live pipeline

| # | Message | Deal matched | Draft created | Verdict |
| --- | --- | --- | --- | --- |
| L01 | "when is closing for 4567 Oak Ridge Avenue, Boardman OH 44512?" | `4585ea3b` (address) | yes — factual 0.65 | correct |
| L02 | "The title commitment for 8104 Riverstone Place is ready for review." | **none** | **none** | **real mail, silently dropped** |
| L03 | "The appraisal for 5915 E 350 N, Franklin IN came in at $312,000." | **none** | **none** | **real mail, silently dropped** |
| L04 | "we can come out to 77 Harness Test Lane. Scheduled: 2026-08-15" | **none** | yes — vendor_reply 0.45 | drafted but not filed |
| L05 | CRM vendor: "helps realtors close more deals. Book a demo?" | none | **yes — uncertain 0.45** | **junk in the queue** |
| L06 | Recruiter: "We are hiring agents. Great commission split." | none | **yes — uncertain 0.45** | **junk in the queue** |
| L07 | LinkedIn: "You appeared in 9 searches" | none | **yes — factual 0.45** | **junk in the queue** |
| L08 | Mum: "Dinner Sunday?" | none | none | correct |
| L09 | Client: "hey / any update?" | none | yes — factual 0.45 | correct to draft |
| L10 | Zillow: "New homes matching your search" | none | **yes — uncertain 0.45** | **junk in the queue** |

**4 of the 5 junk messages produced a draft. 2 of the 3 statement-shaped
transaction emails produced nothing at all.** The one junk message that was
correctly ignored (L08) is the only one with no street address anywhere in it.

The address-matching behaviour is the clean split between L01 and L02/L03:
L01 quoted the address in the full `street, city ST zip` form the platform
itself writes, and matched. L02 and L03 wrote the address the way a person
writes it, and did not.

## 5. Result 3 — what the browser shows

`/ai-emails`, logged in as the tester, after the injection: **25 drafts**.

Top of the queue (in the order the page renders them):

```
 [0] Escalated   Cool Communication            Document request for 4567 Oak Ridge Avenue      5d
 [1] Escalated   Drew Linden                   New file: 5915 E 350 N … contract documents     8d
 [2] Escalated   Tori Banks                    Working together on 5915 E 350 N                8d
 [3] Escalated   Tori Banks                    Welcome — we're under way on 5915 E 350 N       8d
 [4] Escalated   party4@example.com            New file: 5915 E 350 N … contract documents     9d
 [5] Escalated   Tori Banks                    Working together on 5915 E 350 N                9d
 [6] Escalated   Alden Price                   Welcome — we're under way on 5915 E 350 N       9d
 [7] Escalated   Test Client                   Re: Quick question about closing               20d
 [8] Escalated   Cool Communication            Request for Earnest Money Deposit Receipt      20d
 [9] Needs review deals@zillow.com             Re: New homes matching your search              2h
[10] Needs review Buyer Jane                   Re: hey                                         2h
[11] Needs review linkedin@linkedin.com        Re: You appeared in 9 searches                  2h
[12] Needs review recruiter@bigbrokerage.com   Re: Join our team                               2h
[13] Needs review sales@crmvendor.com          Re: Grow your real estate business              2h
[14] Needs review scheduler@homeinspect.com    Re: Inspection scheduling                       2h
[15] Needs review Buyer Jane                   Re: Quick question about closing                2h
[16-24] To review  crazyaidev20500519@gmail.com  task emails, 2d old, incl. 4 identical rows
```

Read that as a working queue: the nine most prominent rows are between 5 and 20
days old, and the genuine new client email (row 10, "any update?") sits below
a Zillow listing alert.

Reading pane for row 11 (LinkedIn) — this is a real draft the product is
offering to send:

> To linkedin@linkedin.com
> "Thanks for the note. I want to make sure I answer for the right file. Could
> you confirm the property address or transaction you mean? Once I have that,
> I'll follow up with the details."

Other measured facts:

| Check | Result |
| --- | --- |
| Controls in the reading pane | `Approve & send`, `Edit`, `Regenerate`, `Discard` — nothing else |
| Any re-file / link-to-deal control | **none**, although the tooltip tells the user to re-file and `POST /ai-emails/inbound/{id}/refile` exists |
| Recipients / Cc editable in edit mode | **no** (read-only line); no attachment control |
| Duplicate rows (same recipient + subject) | 3 groups — ×4, ×2, ×2 |
| Escalated rows | 9 of 25, ages 5–20 d; the 2-day-old drafts are *not* escalated |
| Filters (deal / kind / status / date) | none |
| Pagination | none, client or server |
| Search `Riverstone` (a deal with real inbound mail on file) | **0 rows** |
| Discard → confirm dialog | correct copy, cancel works, confirm removes the row (25 → 24) |
| Regenerate on the LinkedIn junk draft | pane unchanged, draft still in the queue |
| Mobile 390 px | no horizontal overflow, but list and reading pane stack inside a fixed-height shell — both clipped, no way to move between them |
| Failed API calls / console errors / page errors | **0 / 0 / 0** across all three browser runs |

The last row matters: nothing here is a crash or a broken request. The page
does exactly what it was built to do. What it was built to do is the problem.

## 6. Result 4 — the mail you cannot see

`dispatch_inbound_email` writes every inbound message to `communication_logs`
before any relevance decision, and the engine's decision to skip is silent.
After the run, these rows exist in the tenant database and appear on **no**
screen in the product:

- `"Title commitment ready"` — appraisals/title vendor, body names 8104
  Riverstone Place, `transaction_id = NULL`
- `"Appraisal complete"` — `appraisals@valuationpartners.com`, body names
  5915 E 350 N and a $312,000 valuation, `transaction_id = NULL`

`/ai-emails` lists drafts, so a message that produced no draft cannot be
listed, cannot be searched, and cannot be re-filed. Searching the page for
"Riverstone" returns zero rows while the email sits in the database.

The same write path means the tenant's database accumulates a full copy — body
text and HTML — of every message that reaches the connected personal inbox,
including the ones the product then decides are irrelevant.

## 7. What is genuinely good

Worth keeping through any rebuild:

- The human gate is real. Nothing sends without a tap; `handle_inbound` never
  calls the provider.
- The assumptions panel ("Check these before sending") and the "Facts the AI
  used" rail are excellent — they make a draft auditable at a glance.
- Original-message rendering (sandboxed HTML iframe, no scripts, preserved
  plain-text line breaks) is solid.
- Discard confirm copy is precise: "The original message stays in your
  communication log."
- Zero console errors, zero failed requests, clean keyboard focus on rows, no
  horizontal overflow on mobile.
- The reconnect-mailbox banner path from the 2026-07-28 remediation is wired in
  and did not regress.

## 8. Test data left behind

Injected inbound rows carry `provider_ref_id` `ERPROBE-L01 … ERPROBE-L10`; the
drafts they produced are their children in `communication_logs`. One (`L10`,
Zillow) was discarded during the lifecycle test. Remove with a delete on
`provider_ref_id LIKE 'ERPROBE-%'` plus their `parent_log_id` children when the
environment is next reset.
