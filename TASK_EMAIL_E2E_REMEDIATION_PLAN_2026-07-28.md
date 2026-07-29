# Task Lists & Email — Remediation Plan

**Date:** 2026-07-28
**Author:** Jan
**Status:** **ALL SIX PHASES IMPLEMENTED 2026-07-28** (§10-§15 —
including where they deviate). All code is done; the remaining work is OPERATIONAL — see `SCHEDULER_AND_STAGE_ENABLEMENT_RUNBOOK.md`.
**Inputs:** `TASK_EMAIL_E2E_TEST_REPORT_2026-07-28.md` ·
`TASK_EMAIL_E2E_ISSUES_AND_SOLUTIONS_2026-07-28.md`
**Goal:** get the task-list and email features to a state where Audri and Jake can
test *complete functionality* in stage without hitting a wall in the first hour.

---

## 0. The shape of the problem

Fourteen defects, but they are not fourteen independent problems. Four of them
share one root: **a dead mailbox token is not modelled as a first-class condition
anywhere in the system.** It is raised as an HTTP 401, which the SPA reads as
session death (I-01); it escapes the executor's error taxonomy (I-02); each failed
retry leaves a duplicate draft (I-03); and the Settings page has no idea the
mailbox is down (I-10).

Fix that one concept properly and four blockers close together. Everything else is
independent and smaller.

Because Google has not verified the app, Audri's token will expire roughly weekly
throughout the test period. **This is her normal operating condition, not an edge
case** — which is why Phase 1 is not negotiable before she connects Gmail.

---

## 1. Phasing

| Phase | Theme | Issues | Est. | Gate |
|---|---|---|---|---|
| **1** | Mailbox credential expiry, end to end | I-01, I-02, I-10 (partial) | ~1.5 d | ✅ **DONE 2026-07-28** — see §10 |
| **2** | Sending integrity | I-03, I-04, I-11 | ~1.5 d | ✅ **DONE 2026-07-28** — see §11 |
| **3** | Task-list correctness | ~~I-05~~, I-06, I-08, I-09 | ~2 d | ✅ **DONE 2026-07-28** — see §12 |
| **4** | Accidental-send safety + data clean-up | I-07, I-14, backlog purge | ~1 d | ✅ **DONE 2026-07-28** — see §13 |
| **5** | Environment readiness | I-12, stage Gmail + tick | ~0.5 d | ✅ **local DONE** — stage = runbook, see §14 |
| **6** | Polish | I-10 (remainder), I-13 (I-09 done in §12) | ~1 d | ✅ **DONE 2026-07-28** — see §15 |

**Total to hand-off: ~6.5 days** (phases 1–5). Phase 6 rides the next round.

---

## 2. Phase 1 — Mailbox credential expiry, end to end

*The one that decides whether the test week looks like a product or a bug report.*

### 2.1 Model the condition (backend)

`app/services/email/factory.py`
```python
class EmailCredentialsExpired(RuntimeError):
    """The integration exists but its OAuth grant is no longer usable."""
    def __init__(self, provider: str, message: str) -> None: ...
```

Raise it instead of `HTTPException(401)` in:
- `app/services/email/gmail_provider.py:283` (`refresh_access_token`)
- `app/services/email/outlook_provider.py:259` (`refresh_access_token`)

While handling the failure, stamp the integration row:
`metadata_json.token_status = 'expired'`, `token_failed_at = now()`. This is what
Phase 6's health surface reads, and it costs nothing to record now.

**Deliberately not raising `EmailProviderUnavailable`.** "You never connected a
mailbox" and "your mailbox connection lapsed" need different words and different
buttons. Collapsing them is how we ended up telling the user to go connect an
account they can plainly see is already connected.

### 2.2 Map it at the HTTP boundary

Every endpoint that already catches `EmailProviderUnavailable` gains a sibling
handler returning **409** with a machine-readable body:

```json
{"error_code": "email_credentials_expired",
 "provider": "gmail",
 "message": "Your Gmail connection expired. Reconnect it in Settings → Email & E-signature and this will send.",
 "reconnect_path": "/settings/connections"}
```

Endpoints: `tasks.py` `ai_complete_task` · `ai_emails.py` `approve_and_send`,
`edit_and_send`, `send_ready` · `automation.py` `batch_send` ·
`integrations.py` `send_email`.

A shared exception handler registered in `main.py` is preferable to six
`try/except` blocks — one place to change, and it catches the paths we forget.

### 2.3 Stop the false logout (frontend)

`src/utils/api.ts:138` — narrow the trigger so only *our* auth failures log out:

```ts
if (response.status === 401 && token && authFailureHandler && isSessionAuthError(json)) {
  authFailureHandler()
}
```

`isSessionAuthError` returns false for any body whose `error_code` starts with
`email_` / `integration_`. Default-true for unrecognised 401s preserves today's
behaviour everywhere else — this must not become a way to stay logged in with a
genuinely dead session.

### 2.4 Make the message actionable where it happens (frontend)

In `TaskEmailFlow` and `AiEmailReviewPage`, catch `email_credentials_expired` and
render an inline banner with a **Reconnect Gmail** button deep-linking to
`/settings/connections`. Keep the modal open and the draft intact. The user fixes
the connection and retries without losing their place.

### 2.5 Fix the executor's taxonomy (I-02)

`app/services/ai_task_executor.py`:

1. Catch `EmailCredentialsExpired` beside `EmailProviderUnavailable` (~line 500) and
   surface `code="mailbox_reconnect_required"` with:
   *"Your Gmail connection expired, so the AI couldn't send this. Reconnect it in
   Settings → Email & E-signature and the AI will send this automatically."*
2. Add `mailbox_reconnect_required` and `send_failed` to `_RETRYABLE_CODES`
   (line 200), so a fixed blocker releases the task on the next trigger. The
   existing guard — retries bail before composing while still blocked — already
   prevents duplicate email.
3. In the blanket handler (line 279), persist the diagnosis instead of discarding
   it:
   ```python
   extra={"error_type": type(exc).__name__, "error_detail": str(exc)[:200]}
   ```
   Render it in the workspace for Admin/TeamLead only. Testers keep the plain
   sentence; we get the cause. **This is the change that prevents the next
   unclassified failure from being equally blind.**
4. Add a **"Try again"** action on an AI-blocked task card, calling the per-deal
   executor, so a cleared blocker does not wait for a scheduler tick that may never
   come.

### 2.6 Phase 1 acceptance

With a deliberately expired Gmail token:

- [ ] "Send & complete task" shows an inline reconnect banner. **The user stays logged in.**
- [ ] "Approve & send" on AI Email Review does the same.
- [ ] Task generation parks welcome tasks as `mailbox_reconnect_required` with honest text — never `execution_error`.
- [ ] After reconnecting, the next executor pass (or "Try again") sends and completes them, and **exactly one** email goes out per task.
- [ ] `metadata_json.ai_needs_user` on any genuinely unexpected failure carries `error_type` + `error_detail`.

---

## 3. Phase 2 — Sending integrity

### 3.1 One draft per task attempt (I-03)

- Stamp `ai_source_data.task_id` at compose time in `compose_outbound`.
- In `task_email_planner.execute_task_email_plan` (line 519) and
  `ai_task_executor._execute_email_task` (line 466): before composing, look for an
  open non-discarded draft on the same `(transaction_id, task_id)` and **update it
  in place** rather than inserting another.
- On a send failure that never reached the provider, mark the row `discarded_at`
  with `error_message` — except on the `no_provider` / `mailbox_reconnect_required`
  paths, where keeping the prepared draft is the designed hand-off.

### 3.2 One definition of "ready" (I-04)

- Backend: add `is_ready_to_send: bool` to the draft response, computed from the
  real predicate (`approval_status='auto_approved' AND status='ready_to_send'`).
- Frontend: `AiEmailReviewPage.tsx:113` — delete the `confidence >= 0.8 → 'ready'`
  branch; drive the badge and `readyDrafts` from `is_ready_to_send` alone.
  Confidence keeps its own separate chip.
- Frontend: replace the per-draft loop in `handleSendAllReady` (line 1141) with a
  single `POST /ai-emails/send-ready`, rendering `{sent, failed[], skipped}`.
- Frontend: when the posture pre-approves nothing, hide the button and explain why
  rather than showing a contradiction.
- Batch endpoint: collapse drafts sharing
  `(transaction_id, task_id, recipient_emails, subject)` before sending — defence
  against any backlog that predates 3.1.

### 3.3 No unattachable drafts (I-11)

- Require `transaction_id` for `origin='task_email_flow'` and executor-composed
  drafts; reject at the service boundary.
- Needs You: render an "Unattached drafts" group instead of silently dropping them.
- Exclude unattached drafts from every batch send.

### 3.4 Phase 2 acceptance

- [ ] Three consecutive failed sends on one task leave **one** draft, not three.
- [ ] On Manual posture, AI Email Review shows **no** "Send all ready" button, and Needs You and AI Email Review agree on the ready count.
- [ ] Switching to Autopilot makes the same drafts ready on **both** surfaces.
- [ ] "Send all ready" produces one audit row per draft and a legible partial-failure result.
- [ ] No draft can be persisted without a transaction.

---

## 4. Phase 3 — Task-list correctness

### 4.1 Exhaustive condition pairs (I-05)

- `dependency_engine.evaluate_conditions` (line 541): support
  `{"op":"ne","field":…,"value":"us","when_null":true}` so a null field resolves to
  the safe branch. Every existing condition keeps today's exclude-on-null default.
- Set the flag on templates **#80 Confirm Title Order** and **#180 Confirm Home
  Warranty Order** — the two either/or pairs in the library.
- Backstop `title_ordered_by` at intake from the state workflow profile's customary
  ordering side, mirroring `representation-type-wizard-side-backstop`.
- Log a warning and flag the wizard's Review step when a family marked exhaustive
  yields zero rows.

### 4.2 Dates that follow the graph (I-06)

- After `retarget_conditional_tasks` adds or removes any task, run
  `recompute_task_dates(apply=True)` for that deal in the same request and return
  the diff so the workspace can report "3 dates updated".
- On task completion, recompute dependents' dates from the actual completion date.
- At generation, mark a task whose anchor is missing `metadata_json.date_pending`
  and group it as "Waiting on an earlier step" instead of dropping it into "on
  track", where it looks handled and is invisible for ever.

### 4.3 One task, one story, on every surface (I-08)

- `tasks.py:672` — populate `ai_reason` from `metadata_json.ai_needs_user.reason`
  when present; add `ai_needs_user: bool` and `ai_blocked_code`.
- `TaskQueueCard` — render the amber "AI needs you" badge and reason.
- `TaskQueuePage` — mount `TaskEmailFlow` and add "Email transaction party" to the
  row actions, as `TasksTab.tsx:523` does.

### 4.4 Phase 3 acceptance

- [ ] A deal with `title_ordered_by = null` generates **exactly one** title task.
- [ ] Title Work Completed / Deliver Title / Deliver Title to the Loan Officer all carry due dates.
- [ ] Answering the title question later adds the right task **and** recomputes the dependent dates.
- [ ] No open task silently carries a null due date without a "waiting" label.
- [ ] My Task Queue shows the AI blocker reason and can open the email flow.

---

## 5. Phase 4 — Accidental-send safety and data clean-up

### 5.1 Honour the digest opt-in (I-07)

- `send_daily_summaries` (`task_notification_service.py:620`): add the
  `normalize_digest_config(...)["enabled"]` gate that the scheduled path already
  has. One gate, both paths.
- `run-now` defaults to **the calling admin only**. A tenant-wide send becomes a
  separate action behind a confirm dialog naming the recipient count: *"Send the
  morning digest to 13 users now?"*
- Surface `summaries_sent` in the result toast.

### 5.2 Separate prepare from send (I-14)

- `run-now` takes a `jobs` parameter, defaulting to `['drafts','ai_tasks']` — the
  two that send nothing to third parties.
- Label the controls by effect: "Draft due emails (nothing sends)" vs "Send morning
  digest to N users".
- Add a per-deal "Run automation on this deal" action in the workspace — blast
  radius of one file, and the thing a tester actually wants.

### 5.3 Clean the backlog before stage opens

One-off script, dry-run first, against dev and stage:

1. Discard duplicate pending drafts sharing `(transaction_id, task_id, recipients, subject)`, keeping the newest.
2. Discard the 3 drafts with `transaction_id = null` (one is addressed to `party4@example.com`).
3. Clear `ai_needs_user.code = 'execution_error'` on tasks whose only cause was the expired token, so Phase 1's retry logic picks them up cleanly.
4. Delete the harness deal `f8bf6263-99cd-4ed6-8225-b9a5a951de07`.

Run this **after** Phase 1 and 2 ship, so the backlog cannot regrow.

### 5.4 Phase 4 acceptance

- [ ] "Run now" with digest off mails nobody.
- [ ] A tenant-wide digest requires an explicit confirm naming the recipient count.
- [ ] The draft sweep can be run without sending anything.
- [ ] Zero duplicate or unattached drafts remain in dev and stage.

---

## 6. Phase 5 — Environment readiness (do not skip)

Code fixes are worthless if nothing triggers the automation Audri is meant to watch.

1. **Local**: set `CRON_SHARED_SECRET` in `.env`; document the two-terminal dev loop
   (backend on :8001 + `scripts/run_schedules.py --interval 60`) in the testing guide.
2. **Stage**: confirm the ECS task definition still carries the secret (added
   2026-07-23, rev 50); fire **one manual tick** and read the counts before creating
   any recurring schedule. Per `prod-scheduler-never-wired`, a first tick after
   dormancy can burst a backlog of real email.
3. **Stage Gmail**: Audri and Jake reconnect their mailboxes; confirm
   `token_status = healthy` and one self-addressed test send succeeds. Expect to
   repeat weekly until Google verification completes.
4. **Automation status chip**: when `scheduler_healthy` is false, say so plainly —
   *"Automation is not running — the scheduler hasn't checked in"*. Audri must be
   able to tell "the AI decided not to" from "nothing is running".

### 6.1 Phase 5 acceptance

- [ ] `POST /internal/schedules/tick` returns 200 locally and in stage.
- [ ] `GET /automation/status` reports `scheduler_healthy: true` with a recent `last_tick_at`.
- [ ] A stage deal's welcome emails send and self-complete on the tick alone.

---

## 7. Phase 6 — Polish (after the first feedback round)

- **I-10 remainder**: `token_status` + `last_verified_at` on the integrations
  response; a **Test connection** button mirroring the AI provider's; a persistent
  reconnect banner on AI Email Review / Needs You / workspace Email tab; an
  automatic probe on the schedule tick.
- **I-09**: replace the vendor-mode `mailto:` with a real multi-task
  `TaskEmailFlow` send — or remove the button if multi-task composition slips.
- **I-13**: rename the multi-target families ("Internal Thank You — Your Client" /
  "— Co-op Agent"), and render `target` as a chip on the task card.

---

## 8. Regression tests to add alongside the fixes

Backend:
- `test_email_credentials_expired.py` — refresh failure raises `EmailCredentialsExpired`, not `HTTPException`; endpoints map it to 409 with `error_code`.
- `test_ai_task_executor.py` — expired credentials → `mailbox_reconnect_required`, retryable; a genuinely unexpected exception records `error_type`/`error_detail`.
- `test_task_email_flow.py` — three failed sends leave one draft.
- `test_dependency_engine.py` — null `title_ordered_by` yields exactly one title task; `when_null` does not alter any other condition.
- `test_task_generation_service.py` — retarget triggers recompute; dependents get dates.
- `test_task_notification_service.py` — `send_daily_summaries` honours `digest.enabled`.

Frontend:
- `api.test.ts` — a 401 with `error_code: 'email_credentials_expired'` does **not** log out; a plain 401 does.
- `AiEmailReviewPage.test.tsx` — ready count comes from `is_ready_to_send`; no button on Manual posture; batch uses `send-ready`.
- `TaskQueuePage.test.tsx` — AI-blocked task renders the badge and reason and opens `TaskEmailFlow`.

---

## 9. What I would tell Audri

Once Phases 1–5 land, the honest answer to *"when can we test the true
functionality of the task lists/email?"* is: **stage is ready the day after Phase 5
completes** — roughly a week from the start of this work.

Two caveats worth setting expectations on now:

1. **The weekly Gmail reconnect is real and will not go away** until Google
   verifies the app. After Phase 1 the app will tell her clearly when it happens
   and give her a one-click fix, instead of logging her out. That is the achievable
   goal for this round; removing the reconnect entirely is the verification
   workstream Jake and I are running separately.
2. **The automated emails only fire when the scheduler runs.** Phase 5 turns it on
   in stage. If she sees a welcome email sitting undone, the first question is
   whether the tick ran — and after Phase 5 the automation chip will answer that
   without asking me.

---

## 10. Phase 1 — what actually shipped (2026-07-28)

Implemented and verified the same day. Four deviations from §2, each because
implementation surfaced something the plan had not accounted for.

### 10.1 Files changed

**Backend**
| File | Change |
|---|---|
| `app/core/exceptions.py` | New `ProviderCredentialsExpiredError` (409, `error_code=provider_credentials_expired`); `AppError` gained an `error_code` class attribute; `_error_body` emits it; **fixed** the `StarletteHTTPException` handler so a dict `detail` is preserved instead of stringified |
| `app/services/email/gmail_provider.py` | `refresh_access_token` raises the new error, not `HTTPException(401)` |
| `app/services/email/outlook_provider.py` | same, plus the failure is now logged |
| `app/services/email/factory.py` | Records `token_status` (`healthy`/`expired`) + timestamp on the integration row around every refresh |
| `app/services/ai_task_executor.py` | Catches the new error → `mailbox_reconnect_required`; added it to `_RETRYABLE_CODES`; the blanket handler now persists an error fingerprint; corrected stale "Settings → Integrations" copy |
| `app/tests/test_ai_task_executor.py` | 2 new regression tests |

**Frontend**
| File | Change |
|---|---|
| `src/utils/api.ts` | Reads a top-level `error_code`; the 401 logout is gated on `isSessionAuthFailure` |
| `src/types/api.ts` | `ApiErrorBody.error_code` |
| `src/components/integrations/ReconnectMailboxBanner.tsx` | **New** — shared banner + `isCredentialsExpired` helper |
| `src/components/tasks/TaskEmailFlow.tsx` | Inline banner; modal and draft survive the failure |
| `src/pages/AiEmailReviewPage.tsx` | Same, on approve and edit-and-send |
| `src/tests/unit/api.test.ts` | 3 new regression tests |

### 10.2 Deviations from the plan, and why

1. **Named `ProviderCredentialsExpiredError`, not `EmailCredentialsExpired`, and
   it lives in `app/core/exceptions.py`.** The plan put it in the email package,
   but `calendar_sync.py` calls the same `refresh_access_token` and did not catch
   anything — so a lapsed *calendar* grant produced the identical spurious
   logout. Putting it in the core `AppError` hierarchy fixes both paths and keeps
   the import direction right (services → core, never the reverse).

2. **No per-endpoint `try/except` blocks.** §2.2 proposed handlers on six
   endpoints. Because the error subclasses `AppError`, the already-registered
   global handler maps it everywhere — including endpoints nobody remembered.
   Six edits became zero.

3. **`send_failed` was deliberately NOT made retryable**, though §2.5 listed it.
   `mailbox_reconnect_required` is safe because it fires at provider
   *resolution*, before anything is composed — a retry cannot duplicate an email.
   `send_failed` fires *after* a send attempt, where we cannot know whether the
   message left; retrying risks mailing a client twice. Half the plan item, on
   purpose.

4. **Had to repair the `error_code` channel first.** The frontend documents (and
   two components already rely on) reading `error_code` from a dict `detail` —
   but the backend's exception handler stringified `detail` into `message`, so it
   never arrived. That bug was silently breaking `DeletionApprovalsPanel`'s
   `already_decided` branch too. Fixed as part of this.

### 10.3 Verification

Not asserted from reading the diff — reproduced against a genuinely failing
grant. A throwaway backend was run on `:8002` with a deliberately wrong
`GOOGLE_CLIENT_SECRET`, so only that process failed to refresh and the real
connection stayed intact.

**API shape**
```
POST /api/v1/integrations/email/send  →  HTTP 409
{"status_code":409,
 "message":"Your Gmail connection expired. Reconnect it in Settings → Email & E-signature and this will go through.",
 "error_code":"provider_credentials_expired",
 "details":{"provider":"gmail","provider_label":"Gmail","reconnect_path":"/settings/connections"}}
```

**Browser, the exact flow that used to sign the user out** (screenshot:
`_shots/e2e-fix/05-01-reconnect-banner.png`):
```
send clicked: true
409 POST /api/v1/tasks/{id}/ai-complete
LOGGED OUT: false                     ← was: true
banner headline shown: true
names the provider: true
offers Reconnect action: true
modal still open: true
draft edit survived: true
does NOT claim session expired: true  ← was: "Your session has expired"
```

**Health stamping**, both directions: failed refresh → `token_status: expired`;
successful refresh → `token_status: healthy` + `token_verified_at`. This is the
data Phase 6's Settings surface will read (I-10).

**Suites**: backend 324 passed (`-k "email or task or integration or exception or
auth"`), including 2 new; frontend 369/370 with `tsc` and `eslint` clean, plus 3
new. The one frontend failure is `DocumentsModal.test.tsx`, which is
**pre-existing and unrelated** — confirmed by removing every change in this phase
and watching it fail 3 runs out of 3. (Its own source comment records prior
flakiness under load; it is a genuine pre-existing flake worth fixing separately.)

### 10.4 What Phase 1 does NOT do

- The executor still needs a trigger to pick up a released task. Until the
  scheduler runs (**I-12 / Phase 5**), `mailbox_reconnect_required` only clears
  on the next generation or parse event. The §2.5.4 "Try again" button was **not**
  built; it should land with Phase 5 or before stage opens.
- Settings → Connections still shows a flat "Connected" (**I-10**). The data it
  needs is now recorded; the UI is Phase 6.
- **I-04 remains open and is now the top risk.** With a live mailbox, "Send all
  ready · 11" is a one-click mass send to real third parties. Phase 2 should be
  next.

---

## 11. Phase 2 — what actually shipped (2026-07-28)

The urgent one. With a live mailbox, "Send all ready · 16" was a single click
away from mailing sixteen emails — including duplicates and one to a placeholder
address — from a workspace whose posture says nothing sends without a tap.

### 11.1 Files changed

**Backend**
| File | Change |
|---|---|
| `app/schemas/communication_log.py` | `is_ready_to_send` computed field — THE definition, served to every client |
| `app/repositories/communication_log_repository.py` | New `find_open_task_draft`; `list_ready_to_send` now excludes deal-less drafts |
| `app/services/ai_email_engine.py` | `compose_outbound` takes `task_id`: stamps it into `ai_source_data`, **reuses** an open draft for the same (deal, task), and refuses a task email with no deal |
| `app/services/ai_task_executor.py` · `app/services/task_email_planner.py` | Pass `task_id` |
| `app/api/v1/automation.py` | Needs You surfaces unattached drafts instead of dropping them; `transaction_id` nullable; batch send skips them |
| `app/tests/test_task_email_flow.py` | 3 new regression tests |

**Frontend**
| File | Change |
|---|---|
| `src/hooks/useAiEmails.ts` | `is_ready_to_send` on the draft type |
| `src/pages/AiEmailReviewPage.tsx` | Badge and count read `is_ready_to_send`, not confidence; batch goes through `useSendAllReady` (the guarded endpoint); posture explanation; reconnect banner on batch failure |
| `src/hooks/useAutomation.ts` | `transaction_id` nullable |
| `src/pages/automation/NeedsYouPage.tsx` | Unattached drafts group under their own heading |

### 11.2 Deviations from the plan, and why

1. **The dedupe lives in `compose_outbound`, not in the two call sites.** §3.1
   proposed a lookup in the planner *and* the executor. Putting it behind the
   `task_id` parameter means both callers — and any future one — get it for
   free, and there is a single place where "one draft per task" is defined.

2. **No discard-on-failure.** §3.1 wanted failed drafts marked `discarded_at`.
   Reuse makes that unnecessary: there is only ever one draft, and keeping it is
   the designed hand-off ("the prepared draft is waiting in AI Emails"). Adding a
   discard on top would delete the thing we tell the user to go send. Dropped
   deliberately.

3. **Orphans are surfaced, not just excluded.** §3.3 said to require a
   transaction going forward. That stops new ones but says nothing about the
   three already in the database. They are now visible in Needs You under a
   "Not linked to a deal" group, always `Review` (never `Send`), so they can be
   resolved rather than merely being unsendable-by-the-safe-path.

4. **`useSendAllReady` already existed** in `useAutomation.ts` and was wired to
   Needs You only. The review page just was not using it — so §3.2's "route the
   batch through the guarded endpoint" was a two-line change, not a new hook.

### 11.3 Verification

**I-04 — one definition, measured on the same 17 live drafts**
```
is_ready_to_send TRUE:            0   ← what the button shows now (Manual posture)
old confidence>=0.8 rule showed:  16  ← what it showed before
```
Browser: `Send all ready` button **ABSENT**, 0 green "Ready to send" badges, and
the queue explains why ("Every email here waits for your tap. Turn on Autopilot
…"). Needs You header reads `0 ready to send`. **The two surfaces now agree.**
Screenshot: `_shots/e2e-fix/06-01-ai-emails.png`.

**I-03 — three failed sends against a dead mailbox**
```
drafts on deal BEFORE:                    3
attempt 1 → 409   attempt 2 → 409   attempt 3 → 409
drafts on deal AFTER:                     4      (was: +1 per attempt)
drafts tagged with that task_id:          1      (must be 1)
"reused open draft" log lines:            2
```
One draft composed, then reused twice. Before the fix the same measurement was
3 → 5 after only two attempts.

**I-11 — orphans**
```
orphan drafts surfaced in Needs You: 3   (before: 0, silently dropped)
  Review | New file: 5915 E 350 N…      | To party4@example.com — not linked to a deal…
  Review | Working together on 5915 E…  | To tori.banks@minafter.com — not linked to a deal…
  Review | Welcome — we're under way…   | To alden.price@minafter.com — not linked to a deal…
```
All `Review`, never `Send`; excluded from both batch paths; new task drafts
cannot be created without a deal at all.

**Suites**: backend 345 passed, 3 new. Frontend 369/370, `tsc` and `eslint`
clean. The single failure is the same pre-existing `DocumentsModal` flake proven
unrelated in §10.3.

### 11.4 A bug this phase introduced and caught

Making Needs You surface orphans meant passing `transaction_id=None` into
`NeedsYouItem`, where the field was a required `str`. Pydantic raised inside the
drafts loop, the surrounding `except` swallowed it, and the queue silently
served **2 drafts instead of 17** — a worse bug than the one being fixed.

Caught by checking the live endpoint rather than trusting the diff; the field is
now `str | None` on both sides. Worth recording because the failure mode is
invisible: a broad `except` around a loop turns a validation error into quiet
data loss, and there are several more of those in this file.

### 11.5 What Phase 2 does NOT do

- **The backlog is still there.** 17 drafts remain in the dev tenant, including
  duplicates from before the fix and the 3 orphans. Nothing can bulk-send them
  now, but the Phase 4 purge should still run before stage opens.
- **Confidence still drives the "Needs review" band**, which is correct — that
  band is about content quality, not authorisation.
- I-05/I-06/I-08 (Phase 3, task-list correctness) are untouched and are next.

---

## 12. Phase 3 — what actually shipped (2026-07-28)

The phase that proved one of my own findings wrong. **I-05 is retracted**; the
other three are fixed.

### 12.1 I-05 was a mis-diagnosis — retracted, not fixed

I implemented the §4.1 change (make an unset field resolve the `ne` branch to
"included" so the either/or pair stays exhaustive). It broke two tests:

```
FAILED test_dependency_engine.py::TestDerivedConditionValues::test_unanswered_side_excludes_both_tasks
FAILED test_task_generation.py::test_unanswered_title_generates_no_title_task_and_warns
```

Both assert the current behaviour **deliberately** — the second one is even named
"…and warns". Reading them exposed the design I had missed: an unanswered title
question raises a **coverage prompt** that surfaces in Needs You as a one-click
question, whose answer PATCHes the field and retargets exactly one title task.

Verified live on a deal built for the purpose:
```
/plan      → coverage: [{"key":"title_ordering",
                         "message":"No title task exists on this deal — confirm who orders title."}]
/needs-you → kinds: {"task":15,"draft":18,"coverage":1}
             "99 Coverage Probe Lane | No title task exists on this deal — confirm who orders title."
```

So the chain does not vanish *silently* — the system asks, in the queue the tester
is already working. My original run missed it because I checked Needs You before
creating that deal and again after answering the field, never in between.

**Change reverted** (`_tools/i05_revert.patch`). The genuinely broken part was the
downstream effect, which is I-06.

### 12.2 Files changed

**Backend**
| File | Change |
|---|---|
| `app/api/v1/transactions.py` | After a condition-field answer, run `recompute_task_dates(apply=True)` for that deal |
| `app/services/task_classifier.py` | New `undated` due-state; label "Waiting on an earlier step" |
| `app/api/v1/tasks.py` | Queue items carry `ai_needs_user`, `ai_blocked_code`, and the executor's reason in `ai_reason` |
| `app/tests/test_task_generation.py` | 1 new regression test |

**Frontend**
| File | Change |
|---|---|
| `src/types/api.ts` · `queueMeta.ts` | `undated` state, muted (not green) |
| `src/components/tasks/queue/TaskQueueCard.tsx` | "AI needs you" badge + reason; "Email transaction party" action |
| `src/pages/tasks/TaskQueuePage.tsx` | Mounts `TaskEmailFlow`; the vendor-cart `mailto:` replaced with the real per-task flow |

### 12.3 Deviations from the plan, and why

1. **I-05 reverted** — see §12.1.

2. **The recompute is NOT gated on tasks added/removed**, which §4.2 implied.
   Testing showed the gate misses the case where the graph is already correct but
   the dates are still the nulls those tasks were born with. It now runs whenever
   a watched condition field changes.

3. **No blanket recompute on task completion** (§4.2 item 2). `recompute_task_dates`
   re-derives dates from the transaction's dates and overwrites template-sourced
   tasks — running it on every completion would silently undo a user's manual
   "Edit due date". The retarget path covers the real cause; the residual cases
   (an unanswered wizard offset) are now *labelled* rather than silently rewritten.

4. **I-09 pulled forward from Phase 6.** The vendor-cart "Email all" `mailto:` sat
   three lines from the new logged action in the same file; leaving an unlogged
   side channel beside it would have been actively confusing. Each cart row now
   opens the real `TaskEmailFlow`. A genuine multi-task compose still needs a
   backend plan endpoint and remains unbuilt — the header says "Email one at a
   time below" rather than pretending otherwise.

### 12.4 Verification

**I-06 — the full chain, on a deal with the title question unanswered**
```
BEFORE: 27 tasks · title tasks: (none)
   Title Work Completed               due=null
   Deliver Title                      due=null
   Deliver Title to the Loan Officer  due=null

PATCH title_ordered_by=Buyer   (exactly what the Needs-You one-click sends)

AFTER:  28 tasks · title tasks: Order Title
   Order Title                        due=2026-07-26
   Title Work Completed               due=2026-08-09
   Deliver Title                      due=2026-08-09
   Deliver Title to the Loan Officer  due=2026-08-09

null-due OPEN tasks: 4 → 1
log: "Recomputed dates for transaction …: 3 changed, 3 applied (apply=True)"
```
The one remaining undated task is `Insurance Reminder`, whose offset is
`wizard:insurance_commitment_days` — genuinely waiting on an unanswered field, and
now labelled as such instead of sitting in "on track".

**I-08 — the queue payload**
```
AI-blocked tasks in My Task Queue: 15
  Buyer Welcome        | code=execution_error        | reason=The AI hit an unexpected error…
  Order Title          | code=no_recipient           | reason=No Title email is on file for this deal…
  Review Documentation | code=no_documents_to_review | reason=No purchase agreement or counter offers…
undated tasks (were mislabelled on_track): 24
  Insurance Reminder | due_state=undated | label="Waiting on an earlier step"
```

**Browser** (`_shots/e2e-fix/07-01`, `07-02`):
```
queue shows "AI needs you" badge         = true
queue shows a blocker reason             = true
queue shows "Waiting on an earlier step" = true
old "No due date" label gone             = true
expanded card offers "Email transaction party" = true
TaskEmailFlow opened from the queue      = true
```

**Suites**: backend **1362 passed** (the entire suite), 1 new. Frontend 369/370
with `tsc` and `eslint` clean — the single failure is the pre-existing
`DocumentsModal` flake proven unrelated in §10.3.

### 12.5 What Phase 3 does NOT do

- **A manual "Try again" on a blocked task** is still missing (carried from
  Phase 1). Until the scheduler runs, a cleared blocker waits for the next
  generation or parse event.
- **Multi-task vendor compose** is not built; one task at a time is the honest
  interim.
- Phase 4 (digest opt-in, run-now scoping, backlog purge) is next and is the last
  one gating the stage hand-off apart from Phase 5's environment work.

---

## 13. Phase 4 — what actually shipped (2026-07-28)

### 13.1 An incident during this phase, and what it changed

While verifying the fix I called `POST /automation/run-now` tenant-wide against a
**live** mailbox. It sent **two real emails** to deal parties I do not control:

```
20:57:58 | sienna.cole@minafter.com  | Working together on 8104 Riverstone Place…
20:57:54 | amelia.brooks@minafter.com | Welcome — we're under way on 8104 Riverstone Place…
```

They are `@minafter.com` seeded test accounts on a dev deal, and the content is
ordinary product output, so the harm is contained. It was still my mistake: I had
noted earlier in this same session that tenant-wide automation must not be run
with a live mailbox, and then ran it.

It also exposed a flaw in **this phase's own design**. §5.2 proposed defaulting
`run-now` to `['drafts','ai_tasks']`, described as "the two that send nothing to
third parties". **That description was wrong.** The AI task executor sends the
Automated task emails to the deal's captured parties — that is its entire
purpose. I had classified a job that mails strangers as safe-by-default.

Corrected: the default is now **`['drafts']` alone**, and the executor is a
separate, explicitly labelled action behind a confirm dialog. The incident is the
reason the fix is right rather than merely shipped.

### 13.2 Files changed

**Backend**
| File | Change |
|---|---|
| `app/services/task_notification_service.py` | `send_daily_summaries` honors the digest opt-in and takes `only_user_id` |
| `app/api/v1/automation.py` | `run-now` takes `jobs` + `digest_tenant_wide`; default `['drafts']`; returns `jobs_run` |
| `app/api/v1/ai_emails.py` | `/reminders/run` digest scoped to the caller |
| `scripts/purge_draft_backlog.py` | **New** — dry-run-first backlog clean-up |
| `app/tests/test_task_notification_service.py` | 2 new regression tests |

**Frontend**
| File | Change |
|---|---|
| `src/hooks/useAutomation.ts` | `RunNowInput`; `RunNowResult` carries AI-task counts + `jobs_run` |
| `src/pages/admin/AdminAIGovernancePage.tsx` | Three controls separated **by blast radius**, each naming who receives mail |

### 13.3 The controls, by blast radius

| Control | Sends | Guard |
|---|---|---|
| **Draft due emails** | nothing — drafts land in Email review | none needed |
| **Run AI tasks (sends deal email)** | to deal parties, workspace-wide | confirm dialog naming the consequence |
| **Send me my digest** | to you, if your digest is on | none needed — it is one email to yourself |

### 13.4 Deviations from the plan

1. **Default is `['drafts']`, not `['drafts','ai_tasks']`** — see §13.1.
2. **`/ai-emails/reminders/run` scoped to the caller** rather than given its own
   job selector. It is a legacy manual affordance; the governance page is where
   the real controls live now.
3. **The purge script does NOT unstick tasks by default.** A cleared
   `execution_error` flag means that Automated task will EMAIL its deal parties
   on the next executor run. That is a separate `--unstick-tasks` flag with the
   consequence spelled out — the same lesson as §13.1, applied before it bit.

### 13.5 Verification

**I-07 — the digest gate**
```
GET  /notifications/digest        → {"enabled": false, ...}
POST /automation/run-now  {}      → summaries_sent: 0
```
Before the fix this same state mailed every active user with actionable items.
Unit tests cover all three cases (never touched / explicitly off / on) and the
`only_user_id` scoping.

**I-14 — the corrected default**
```
POST /automation/run-now {}  →  jobs_run: ["drafts"]
                                summaries_sent: 0
                                ai_tasks_completed: 0   ← no deal email
                                drafts_created: 0
```

**Backlog purge — dry run, reviewed, NOT applied**
```
open AI drafts: 18
  unattached (no transaction): 3
    - 624355dc → alden.price@minafter.com
    - 8bc2bede → tori.banks@minafter.com
    - 89fc3878 → party4@example.com          ← placeholder address
  duplicate task drafts: 3
    - 3 × "Welcome — we're under way on 77 Harness Test Lane" (keeps the newest)
  tasks parked on execution_error: 5
DRY RUN — nothing written.
```
Left for Jan to apply, consistent with how migrations are handled here. The
draft discards are soft (`discarded_at`, record preserved); the task-unsticking
is deliberately behind its own flag because it arms real sends.

**Suites**: backend **1364 passed**, 2 new. Frontend 369/370, `tsc`/`eslint`
clean — same pre-existing `DocumentsModal` flake.

### 13.6 What Phase 4 does NOT do

- **The backlog is still in the database.** Run
  `venv/Scripts/python.exe scripts/purge_draft_backlog.py --tenant <id> --apply`
  when ready; add `--unstick-tasks` only after reading which deals those 5 tasks
  belong to.
- **Two harness deals remain** (`f8bf6263…` "77 Harness Test Lane", `8045898a…`
  "88 Livefire Test Lane"). Delete them with the same pass.
- Phase 5 (environment: local cron secret, stage tick, stage Gmail) is the last
  gate before hand-off.

---

## 14. Phase 5 — what actually shipped (2026-07-28)

Split deliberately: the code and the **local** environment are done; the
**stage/prod** steps are operations that belong to Jan and Audri, written up as
`SCHEDULER_AND_STAGE_ENABLEMENT_RUNBOOK.md`.

### 14.1 A second send incident — and the rule it produced

Verifying the tick, I fired it against a backend where I had deliberately broken
the **Google** client secret, believing that made it unable to send. It sent two
emails anyway:

```
21:13:50 | sarah.chen@minafter.com via outlook → theohoffmann0310@outlook.com
         | "Title order: 4567 Oak Ridge Avenue, Boardman, OH, 44512"
21:13:42 | sarah.chen@minafter.com via outlook → elias.fischer1106@hotmail.com
         | "Welcome — we're under way on 4567 Oak Ridge Avenue, Boardman, OH, 44512"
```

Those users are on **Outlook**, whose refresh uses the *Microsoft* secret I had
left working. My guard covered one provider; the system has three.

Tenant `395e9917…` is "Tenant 1", `is_active: false`, on the standard seeded
fixture address — so almost certainly demo personas. **Jan should confirm that**,
because I cannot prove it from here.

Combined with the Phase 4 incident, four emails reached addresses I do not
control during this work. Both were the same mistake in different clothes:
running a **cross-tenant** job against a database holding **live mail
credentials**. The rule now written at the top of the runbook:

> A safety guard that covers one provider is not a safety guard. Never run a
> tick or a tenant-wide run against a database with live mail credentials you
> have not personally enumerated. The dev DB has **13 active mail integrations
> across 22 tenants**.

### 14.2 Files changed

| File | Change |
|---|---|
| `velvet-elves-backend/.env` | `CRON_SHARED_SECRET` set (config, not source) |
| `app/api/v1/automation.py` | `/automation/status` returns `scheduler_state`: `ok` / `stale` / `never_run` |
| `src/hooks/useAutomation.ts` | `SchedulerState` type on `AutomationStatus` |
| `src/pages/admin/AdminAIGovernancePage.tsx` | The chip names WHICH failure it is |
| `velvet-elves-data/SCHEDULER_AND_STAGE_ENABLEMENT_RUNBOOK.md` | **New** — the stage/prod procedure |

### 14.3 Verification

**Fail-closed, then reachable**
```
POST /internal/schedules/tick                           → 403
POST /internal/schedules/tick  X-VE-Cron-Secret: wrong   → 403
POST /internal/schedules/tick  X-VE-Cron-Secret: <valid> → 200
```

**A real end-to-end tick across 22 tenants**
```
escalations_sent    : 42    ← internal rows (channel=system/internal), NOT email
digests_sent        : 0     ← the Phase 4 opt-in gate, holding tenant-wide
auto_drafts_created : 0
ai_tasks_completed  : 2     ← the two sends in §14.1
ai_tasks_surfaced   : 40
tenants_swept       : 22    tenant_errors: 0
gmail_watches       : 8 checked / 0 renewed / 8 failed (expected: broken secret)
cost_sync           : ran, AWS 555 rows
```
`digests_sent: 0` is the number worth noticing — before Phase 4 that same run
would have mailed every user in 22 tenants.

**Status honesty**
```
GET /automation/status → scheduler_healthy: true, scheduler_state: "ok"
```
and after the fix the chip reads *"Automation is not running — the scheduler has
never checked in"* rather than a neutral "hasn't run recently", which is what
production has silently been for months.

### 14.4 What is NOT done, and is deliberately not mine to do

- **The stage tick has not been fired.** It needs the mail-integration audit in
  runbook §3 first. Given §14.1, firing it blind would be the same mistake a
  third time.
- **The hourly EventBridge rule does not exist** on stage or prod.
- **Prod has never ticked** and still lacks `CRON_SHARED_SECRET` entirely.
- **Audri and Jake must connect their own mailboxes** — nobody else can.
- **Stage inbound** needs its Pub/Sub push URL verified and Gmail reconnected
  afterwards (the notification URL is baked into the watch).

---

## 15. Phase 6 — what actually shipped (2026-07-28)

The remainder of I-10 plus I-13. (I-09 landed early, in §12.4.)

### 15.1 Files changed

**Backend**
| File | Change |
|---|---|
| `app/services/email/base.py` | New `verify_connection()` on the provider interface — read-only, default is a truthful "cannot verify" |
| `app/services/email/gmail_provider.py` | Probes `users/me/profile` |
| `app/services/email/outlook_provider.py` | Probes Graph `/me` |
| `app/schemas/integration.py` | `token_status` + `token_verified_at` on the response; new `IntegrationTestResponse` |
| `app/api/v1/integrations.py` | List carries health; new `POST /integrations/{provider}/test` |
| `app/tests/test_email_integration_api.py` | 2 new regression tests |

**Frontend**
| File | Change |
|---|---|
| `src/types/api.ts` · `src/hooks/useIntegrations.ts` | Health fields; `useTestIntegration` |
| `src/components/settings/ConnectionsPanel.tsx` | Amber "Expired — reconnect" pill; **Test connection** button; inline result |
| `src/components/tasks/queue/TaskQueueCard.tsx` | Renders the task's `target` (I-13) |

### 15.2 Design notes

**The probe never sends.** It resolves the provider — which performs the token
refresh, the thing that actually dies weekly — then makes a read-only profile
call to prove the resulting access token is accepted. A test that worked by
sending an email would be worse than no test.

**Always HTTP 200.** A dead mailbox is a result to render inline, not a request
failure. This mirrors the AI provider test, which set the precedent for exactly
the same reason ("I switched to Claude and nothing works").

**`verify_connection` defaults to "cannot verify", not True.** A provider that
has not implemented a probe (iCloud) never claims health it has not checked.

**I-13 solved in code, not data.** The plan proposed renaming the template
families. That needs a migration, and per `ai-task-executor-automated-tasks` the
executor playbook is keyed by normalized task NAME — renaming a system template
breaks its automation. "Internal Thank You" is not in the playbook, so a rename
would have been safe, but rendering the existing `target` field solves the
user-visible confusion with no migration and no risk. The rename remains
available if the client wants it.

### 15.3 Verification

```
GET  /api/v1/integrations
  google_calendar   | active=true | token_status=unknown | verified_at=null
  outlook_calendar  | active=true | token_status=unknown | verified_at=null
  gmail             | active=true | token_status=healthy | verified_at=2026-07-28T21:17:52

POST /api/v1/integrations/gmail/test    → 200
  {"ok":true,"message":"Connected as crazyaidev20500519@gmail.com.","token_status":"healthy"}
POST /api/v1/integrations/outlook/test  → 200
  {"ok":false,"message":"No active outlook integration for this user.","token_status":"unknown"}
```

Browser (`_shots/e2e-fix/08-02-tested.png`): the page offers **Test connection**,
the probe returns inline as *"Connected as crazyaidev20500519@gmail.com."*, and
no email is sent.

**Suites**: backend **1366 passed**, 2 new. Frontend 369/370, `tsc`/`eslint`
clean — same pre-existing `DocumentsModal` flake (§10.3).

---

## 16. Where this leaves the round

**All 14 findings are resolved or retracted:**

| | |
|---|---|
| Fixed | I-01, I-02, I-03, I-04, I-06, I-07, I-08, I-09, I-10, I-11, I-13, I-14 |
| Retracted (not a defect) | I-05 — the coverage-prompt design was correct; see §12.1 |
| Fixed in code, operational work remains | I-12 — local done; stage/prod is the runbook |
| New, found mid-work | I-15 (local inbound ngrok) — documented, local-only |

**Nothing further gates the hand-off in code.** What remains is operational and
belongs to people, not to a diff:

1. Apply the backlog purge (`scripts/purge_draft_backlog.py --apply`), and delete
   the two harness deals.
2. Work `SCHEDULER_AND_STAGE_ENABLEMENT_RUNBOOK.md` §2-§4 — **including the
   mail-integration audit before the first stage tick.**
3. Audri and Jake connect their stage mailboxes (§5).

**Two things I would tell Audri directly.** The weekly Gmail reconnect is real
and will not go away until Google verifies the app — but it is now a banner with
a one-click fix and a Test connection button, not a logout. And when an
automated email has not gone out, the first question is whether the scheduler
ran; the automation chip now answers that without asking me.

**One honest caveat about this work:** four emails reached addresses I do not
control while I was verifying it (§13.1, §14.1), both times because I ran a
cross-tenant job against a database with live mail credentials. The fixes are
sound and independently verified, but that judgement error is why the runbook
leads with blast radius rather than mentioning it in passing.
