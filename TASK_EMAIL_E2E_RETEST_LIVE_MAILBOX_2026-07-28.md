# Task Lists & Email — Re-test with a LIVE mailbox (addendum)

**Date:** 2026-07-28, same day, after Jan reconnected Gmail
**Parent documents:** `TASK_EMAIL_E2E_TEST_REPORT_2026-07-28.md` ·
`TASK_EMAIL_E2E_ISSUES_AND_SOLUTIONS_2026-07-28.md` ·
`TASK_EMAIL_E2E_REMEDIATION_PLAN_2026-07-28.md`

The first run was conducted against a **dead** Gmail token, so the entire send
happy path was unverifiable. This addendum records what changed once the mailbox
was reconnected. **No source code was changed.**

---

## 1. Headline: the happy path is genuinely good

With a live mailbox, the automation does exactly what it promises. On a fresh
Buy-Fin deal, seconds after task generation and with no human involvement:

```
Review Documentation  | Pending   | NEEDS:no_documents_to_review
Buyer Welcome         | Completed | assigned=ai_agent | SENT:crazyaidev20500519@gmail.com
Co-op Agent Welcome   | Completed | assigned=ai_agent | SENT:crazyaidev20500519@gmail.com
Loan Officer Welcome  | Pending   | NEEDS:missing_document
Order Title           | Pending   | NEEDS:missing_document
```

and in `communication_logs`:

```
sent | approved | to=crazyaidev20500519@gmail.com | ref=19fa992d40e8b0c9 | Working together on 88 Livefire Test Lane
sent | approved | to=crazyaidev20500519@gmail.com | ref=19fa992c66ffddd2 | Welcome — we're under way on 88 Livefire Test Lane
```

Two emails, two real Gmail message ids, two tasks closed by the AI, **zero
duplicates**. This is the feature Audri is being asked to evaluate, and it works.

The `TaskEmailFlow` path is equally clean. Driving the real UI — workspace → Tasks
→ *Inspection Scheduled* → **Email transaction party** → **Send & complete task**:

```
LOGGED OUT: false          ← the I-01 symptom is gone with a healthy token
Inspection Scheduled -> status=Completed | assigned=ai_agent
ai_execution: {"note":"Sent to crazyaidev20500519@gmail.com — confirmed by you",
               "trigger":"user_confirmed", "log_id":"f9f0e634-…"}
logs on deal now: 3   (no duplicate rows)
```

---

## 2. What this proves about the original findings

| Issue | Status after re-test |
|---|---|
| **I-01** logout on expired token | **Confirmed diagnosis, still unfixed.** The symptom disappears with a healthy token because the 401 is never raised. Nothing about the code changed — it returns the moment the grant lapses again, which is weekly until Google verifies the app. |
| **I-02** `execution_error` park | **Root cause confirmed exactly.** The identical two tasks that failed on the dead-token deal (`Buyer Welcome`, `Co-op Agent Welcome`) sailed through on the live-token deal. The expired grant was the sole cause. |
| **I-03** duplicate drafts | **Confirmed as failure-path-only.** Successful sends produce exactly one log and leave no pending draft. The duplication is entirely a consequence of failed attempts not cleaning up. |
| **I-04** "Send all ready" divergence | **Unchanged — and now dangerous.** See §4. |
| **I-05** missing title chain | **Unchanged.** Setting `title_ordered_by` at creation produced `Order Title` correctly, which re-confirms the null field is the sole cause. |
| **I-06 … I-14** | Unchanged; none depended on mailbox health. |

**Nothing in the parent documents needs revising.** The remediation plan stands as
written — the re-test narrows I-01/I-02 to precisely the diagnosis given, and
raises the urgency of I-04.

---

## 3. New finding — I-15: inbound email is dead locally (stale ngrok tunnel)

**Severity: Medium (local environment only); Blocker for testing the inbound half**

### Symptom

Replies to any email the system sends will never appear in AI Email Review on this
machine. Outbound works; the return leg does not.

### Root cause

The Gmail OAuth callback *does* register a `users.watch`
(`app/api/v1/integrations.py:495`, gated on `GMAIL_PUBSUB_TOPIC_NAME`, which is
set), so the reconnect armed inbound correctly. But the Pub/Sub push destination
in `.env` is a tunnel from an earlier session:

```
EMAIL_WEBHOOK_PUBLIC_BASE_URL=https://69df-45-61-150-174.ngrok-free.app
PUBSUB_PUSH_AUDIENCE=https://69df-45-61-150-174.ngrok-free.app/api/v1/integrations/email/webhook/gmail
```

That host is no longer ours:

```
via ngrok  → ngrok's own HTML error page
local :8000 same path → {"status_code":400,"message":"Missing validationToken."}
```

Google is delivering notifications to a dead endpoint and nothing reaches the app.

### Solution

Local only — stage and prod use real hostnames. To test inbound locally:

1. Start a fresh tunnel: `ngrok http 8000`.
2. Update `EMAIL_WEBHOOK_PUBLIC_BASE_URL` and `PUBSUB_PUSH_AUDIENCE` in `.env`,
   then restart the backend (per `backend-env-loaded-by-absolute-path-restart-to-apply`,
   `--reload` does **not** re-read `.env`).
3. Point the Pub/Sub push subscription at the new URL.
4. **Reconnect Gmail again** — the notification URL is baked into the watch at
   registration time, so an existing watch keeps pointing at the dead tunnel.

Worth folding step 4 into the testing guide: reconnecting is not optional after a
tunnel change, and it is not obvious.

---

## 4. Live-fire warning — "Send all ready" is now armed

This needs saying before anyone opens the app.

Now that the mailbox is healthy, the **"Send all ready · 11"** button on AI Email
Review will actually deliver. Its contents are not safe:

```
pending drafts: 14  |  would fire on "Send all ready": 11
third-party recipients inside that batch:
   alden.price@minafter.com
   tori.banks@minafter.com
   drew.linden@minafter.com
   party4@example.com        ← placeholder address, no deal attached
```

Per **I-04**, that button is driven by `ai_confidence >= 0.8` on the client, not by
the backend's ready contract — the tenant is on **Manual** posture and the backend
considers **zero** drafts ready. Per **I-11**, three of those drafts have no
`transaction_id` at all.

So a single click sends eleven emails, including duplicated welcome messages and
one to a placeholder address, from a workspace whose posture says nothing should
send without an individual tap.

**Until I-04 lands, do not press it, and do not put it in front of Audri.** The
Phase 4 backlog purge in the remediation plan should run before stage opens; I have
left the drafts in place rather than deleting them unilaterally.

---

## 5. Second-order observation: `Order Title` needs documents

Not a defect, but a testing prerequisite worth knowing.

On the live-fire deal, `Order Title` and `Loan Officer Welcome` both parked with
`missing_document` rather than sending. That is the executor working as designed —
`_execute_email_task` refuses to send an email that promises an attachment it does
not have, because "an email that says 'here's the contract' without the contract
does damage". Both are retryable, so they fire on their own once the documents land.

The consequence for the test plan: **a deal created without uploaded documents will
never demonstrate the title-order email.** Audri should test with a wizard-created
deal that has its contract package attached, not a quick-created one, or she will
report the title automation as broken when it is deliberately waiting.

---

## 6. Test data created in this run

| Object | Id |
|---|---|
| Live-fire transaction | `8045898a-4e17-4af7-aa74-ffa76fbab96f` — "88 Livefire Test Lane", Buy-Fin, `title_ordered_by=Buyer` |
| Parties | 5, **every address = `crazyaidev20500519@gmail.com`** (the connected mailbox) |
| Emails actually delivered | **4**, all self-addressed: 1 health probe, 2 automated welcomes, 1 task email |

Every send in this exercise went to the connected mailbox itself. No email reached
a third party. The pre-existing drafts addressed to other people were deliberately
left untouched.

Both harness deals (`f8bf6263…` "77 Harness Test Lane" and `8045898a…` "88 Livefire
Test Lane") are still in the dev tenant — the first as a live reproduction of the
dead-token failure mode, the second as a working reference. Delete both with the
Phase 4 clean-up.

---

## 7. Revised recommendation

The re-test does not change the plan, but it sharpens the argument for it.

The features **work**. What does not work is the system's behaviour when the
mailbox lapses — and for Audri that is not an exception path, it is a weekly event.
Phase 1 remains the gate: with it, a lapsed token becomes a banner and a Reconnect
button; without it, it becomes a logout, an opaque "unexpected error" on every
automated task, and a pile of duplicate drafts.

One item moves up in priority: **I-04 should now be treated as urgent rather than
merely high**, because a live mailbox turns a labelling inconsistency into a
one-click mass send to real addresses.
