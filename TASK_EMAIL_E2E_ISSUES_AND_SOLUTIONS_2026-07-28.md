# Task Lists & Email — Issues Found and Their Solutions

**Date:** 2026-07-28
**Source:** local end-to-end run documented in `TASK_EMAIL_E2E_TEST_REPORT_2026-07-28.md`
**Fix sequencing:** `TASK_EMAIL_E2E_REMEDIATION_PLAN_2026-07-28.md`

Every issue below was reproduced against the running system, not inferred from
reading code. Where an issue was confirmed from source plus live state rather than
by executing it, that is stated explicitly.

**Severity key** — **Blocker**: Audri cannot usefully test the feature.
**High**: she will hit it and reasonably report it as broken. **Medium**: visible
wrongness or a real risk. **Low**: cosmetic or confusing.

| Id | Severity | Issue |
|---|---|---|
| I-01 | Blocker | An expired mailbox token logs the user out of the app |
| I-02 | Blocker | Executor turns any unclassified failure into a permanent, unexplained park |
| I-03 | High | Every failed send leaves another duplicate draft behind |
| I-04 | High | "Send all ready" means something different on every surface, and bypasses the posture |
| I-05 | ~~High~~ | ~~Title chain disappears when `title_ordered_by` is unset~~ — **RETRACTED**, the system raises a coverage prompt |
| I-06 | Medium | Retarget adds the task but never recomputes dependent due dates |
| I-07 | High | Admin "Run now" / "Send reminders" mail the digest to users who switched it off |
| I-08 | High | My Task Queue can neither explain nor act on AI-blocked tasks |
| I-09 | Medium | Task queue "Email all" is a raw `mailto:` — unlogged, unsent, un-Velvet-Elves |
| I-10 | Medium | Settings → Connections reports "Connected" for a dead mailbox |
| I-11 | Medium | Orphan drafts with no transaction are invisible to Needs You but sendable in bulk |
| I-12 | Medium | No scheduler credential anywhere but `.env.example` — nothing proactive can run |
| I-13 | Low | Two "Internal Thank You" rows that look identical to the user |
| I-14 | Medium | The auto-draft sweep cannot be run without also blasting digests |

---

## I-01 — An expired mailbox token logs the user out of the app

**Severity: Blocker**

### Symptom

Any action that sends mail through the connected mailbox, when that mailbox's
OAuth token has expired, throws the user out to `/login` with:

> Your session has expired for your security. Please sign in again to continue.

The true cause appears only as a transient toast *on the login page* — "Gmail
credentials expired — please reconnect." — where the user can no longer act on it.
Their Velvet Elves session was in fact perfectly valid.

### Reproduction (browser, twice, two different surfaces)

1. Workspace → Tasks → *Buyer Welcome* kebab → **Email transaction party** →
   **Send & complete task** → redirected to `/login`, `velvet_elves_token` cleared.
2. AI Email Review → open a draft → **Approve & send** →
   `401 POST /api/v1/ai-emails/{id}/approve` → redirected to `/login`.

Screenshot: `c:\Projects\_shots\e2e\02-05-after-send.png`.

### Root cause

Two independent decisions collide.

**(a)** The OAuth services raise an *HTTP* 401 for a provider-credential problem:

`velvet-elves-backend/app/services/email/gmail_provider.py:283`
```python
if resp.status_code != 200:
    logger.warning("Google refresh failed: status=%s body=%s", ...)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Gmail credentials expired — please reconnect.",
    )
```
`outlook_provider.py:259` does the same.

**(b)** The SPA treats *every* 401 on an authenticated request as session death:

`velvet-elves-frontend/src/utils/api.ts:138`
```ts
if (response.status === 401 && token && authFailureHandler) {
  authFailureHandler()
}
```
→ `AuthContext.tsx:159` `handleAuthFailure` → `dispatch({ type: 'LOGOUT', payload: { sessionExpired: true } })`.

401 means "your credentials are bad". Here the *user's* credentials are fine; a
*third party's* are not. The status code is carrying the wrong meaning, and the
client's blanket interpretation of it is correct for every other 401 in the system.

### Affected user actions

`POST /tasks/{id}/ai-complete` · `POST /ai-emails/{id}/approve` ·
`POST /ai-emails/{id}/edit-and-send` · `POST /ai-emails/send-ready` ·
`POST /automation/needs-you/send` · `POST /integrations/email/send`.

### Why this is the most urgent finding

Google has not verified the app. Audri's refresh token will die roughly weekly for
the whole test period. This is not an edge case for her — it is her normal Monday.

### Solution

Stop overloading 401 for provider credentials, and make the client precise.

1. **Backend — give the condition its own type and status.** Introduce
   `EmailCredentialsExpired` (a sibling of `EmailProviderUnavailable` in
   `app/services/email/factory.py`) and raise *that* from both
   `refresh_access_token` implementations instead of `HTTPException(401)`. The
   HTTP layer maps it to **409 Conflict** — the same status the codebase already
   uses for "no mailbox connected" in `ai_complete_task` — with a body that names
   the provider and the reconnect destination:
   ```json
   {"error_code": "email_credentials_expired", "provider": "gmail",
    "message": "Your Gmail connection expired. Reconnect it in Settings → Email & E-signature and this will send.",
    "reconnect_path": "/settings/connections"}
   ```
2. **Frontend — narrow the logout trigger.** In `api.ts`, only call
   `authFailureHandler()` when the 401 is about *our* session. Gate it on the
   backend's own auth error codes (or, minimally, skip it when `error_code`
   starts with `email_`). A 401 that is not ours should surface as an ordinary
   `ApiResponseError` for the calling component to render.
3. **Frontend — make the message actionable where it happens.** In `TaskEmailFlow`
   and `AiEmailReviewPage`, catch `email_credentials_expired` and render an inline
   banner with a **Reconnect Gmail** button that deep-links to
   `/settings/connections`. The user never loses their place.

Fix (1) and (2) together; either alone leaves the bug reachable.

---

## I-02 — Executor turns any unclassified failure into a permanent, unexplained park

**Severity: Blocker**

### Symptom

On a brand-new deal, *Buyer Welcome* and *Co-op Agent Welcome* were parked with:

> The AI hit an unexpected error while working on this task. Please handle it manually.

No diagnostic is stored anywhere. And because the code is not retryable, the task
stays parked **even after the underlying cause is fixed** — reconnecting Gmail does
not release it.

### Reproduction

`POST /transactions/f8bf6263-…/tasks/generate` → within seconds:

```
Buyer Welcome        | Automated | Pending | NEEDS:execution_error
Co-op Agent Welcome  | Automated | Pending | NEEDS:execution_error
```

### Root cause

The executor classifies the failures it anticipated and blanket-catches the rest.

`app/services/ai_task_executor.py:489` — the send is wrapped for exactly two
exception types:
```python
try:
    sent = await send_ai_draft(...)
except EmailProviderUnavailable:      # no mailbox connected
    ... code="no_provider"
except DraftPersistError:
    ... code="send_failed"
```

An **expired** token is neither. Per I-01 it surfaces as
`HTTPException(401)`, which sails past both handlers into the outer net:

`app/services/ai_task_executor.py:279`
```python
except Exception:  # noqa: BLE001 — one task never stops the pass
    logger.exception("AI executor: unexpected failure on task %s (%s)", ...)
    outcome = await _surface_task(
        supabase, task, code="execution_error",
        reason="The AI hit an unexpected error while working on this task. Please handle it manually.",
    )
```

Two consequences:
- The exception detail goes to the server log and **nowhere else** — not into
  `metadata_json.ai_needs_user`, so neither the tester nor I can tell from the
  product what happened.
- `"execution_error"` is absent from `_RETRYABLE_CODES`
  (`ai_task_executor.py:200`), so the task is never re-attempted. A *transient*
  failure produces a *permanent* park.

### Solution

1. **Classify the credential case.** Once I-01 introduces
   `EmailCredentialsExpired`, catch it beside `EmailProviderUnavailable` and
   surface `code="mailbox_reconnect_required"` with an honest reason: *"Your Gmail
   connection expired, so the AI couldn't send this. Reconnect it in Settings →
   Email & E-signature and the AI will send this automatically."*
2. **Make transient codes retryable.** Add `mailbox_reconnect_required` (and
   `send_failed`) to `_RETRYABLE_CODES` so the next trigger re-attempts once the
   blocker clears. The existing guard — retries bail *before* composing while still
   blocked — already prevents duplicate email, so this is safe.
3. **Never discard the diagnosis.** In the blanket handler, persist a redacted
   fingerprint into the flag: `{"code": "execution_error", "error_type":
   type(exc).__name__, "error_detail": str(exc)[:200], "at": ...}`. Show it in the
   workspace only to Admin/TeamLead; testers get the plain sentence, we get the
   cause. Without this, the next unclassified failure is just as blind.
4. **Give the user a manual retry.** A "Try again" affordance on an AI-blocked task
   card, calling the existing per-deal executor, so a fixed blocker does not have
   to wait for the next scheduler tick (which, per I-12, may never come).

---

## I-03 — Every failed send leaves another duplicate draft behind

**Severity: High**

### Symptom

Each attempt to send a task email composes a **new** draft. Failures leave theirs
in the review queue. Retry three times and the queue holds three identical emails
to the same person, all badged "Ready to send".

### Reproduction

```
drafts on harness deal BEFORE: 3
attempt 1 -> HTTP 401
attempt 2 -> HTTP 401
drafts on harness deal AFTER 2 more attempts: 5
```

`03-02-draft-open.png` shows three byte-identical *"Welcome — we're under way on
77 Harness Test Lane"* drafts to `crazyaidev20500519@gmail.com`.

### Root cause

`app/services/task_email_planner.py:519` — `execute_task_email_plan` calls
`engine.compose_outbound(...)`, which **inserts a new `communication_logs` row**,
and only then attempts the send. On failure the function raises and the freshly
inserted row is left behind. There is no reuse of an existing pending draft for the
same `(task_id, recipient)` and no rollback. `_execute_email_task` in
`ai_task_executor.py:466` has the identical shape.

The real hazard is the interaction with I-04: those orphans carry
`ai_confidence = 0.9`, so the review page counts every one of them as "ready" and
"Send all ready" would deliver the same welcome email five times.

### Solution

1. **Make compose idempotent per task attempt.** Before composing, look for an open
   (`approval_status='pending_review'`, not discarded) draft on the same
   `transaction_id` whose `ai_source_data.task_id` matches. Reuse it — update
   subject/body/attachments in place — instead of inserting another. This requires
   stamping `task_id` into `ai_source_data` at compose time, which `compose_outbound`
   already has the shape for.
2. **Roll back a draft that never became a message.** Wrap the send so that a
   failure *before the provider accepted anything* marks the row
   `discarded_at = now()` with `error_message` set, unless the task deliberately
   keeps it for review (the `no_provider` path, which is a designed hand-off). Keep
   exactly one draft per task, in whichever state is true.
3. **De-duplicate defensively at the batch boundary.** In whatever replaces
   `handleSendAllReady` (I-04), collapse drafts sharing
   `(transaction_id, task_id, recipient_emails, subject)` and send one, so a
   pre-existing backlog cannot spam a client after the fix ships.
4. **Clean up the existing mess.** A one-off script to discard duplicate pending
   drafts already in dev/stage — see the plan's Phase 4.

---

## I-04 — "Send all ready" means something different on every surface, and bypasses the posture

**Severity: High**

### Symptom

On the same 14 drafts, at the same moment:

| Surface | Reports |
|---|---|
| AI Email Review | **"Send all ready · 11"** and 11 green "Ready to send" badges |
| Needs You | **"0 ready to send"** |
| Database | 0 rows with `approval_status='auto_approved' AND status='ready_to_send'` |

The tenant is on **Manual** posture, whose stated promise is that nothing is
pre-approved — yet the review page offers a one-tap bulk send of 11 emails.

### Root cause

Three different definitions of "ready".

**Backend (the real contract)** —
`app/repositories/communication_log_repository.py:296`:
```python
.eq("approval_status", "auto_approved")
.eq("status", "ready_to_send")
```
**Needs You** uses the same predicate — `app/api/v1/automation.py:282` — and
correctly reports 0.

**AI Email Review invents its own**, client-side, from confidence alone —
`src/pages/AiEmailReviewPage.tsx:113`:
```ts
if ((confidence ?? 0) >= 0.8) {
  return { key: 'ready', label: 'Ready to send', ... }
}
```
```ts
const readyDrafts = useMemo(
  () => drafts.filter((d) => reviewStatus(d).key === 'ready'), [drafts])
```

A confidence score describes how sure the model is about the *content*. It says
nothing about whether a human authorised sending it. Conflating the two is what
lets a Manual-posture tenant get a bulk-send button.

Two further consequences of the same code:

- `handleSendAllReady` (`AiEmailReviewPage.tsx:1141`) loops
  `POST /ai-emails/{id}/approve` **one draft at a time from the browser**. The
  guarded batch endpoint `POST /ai-emails/send-ready` — with its per-draft
  transaction-access checks, `skipped` accounting and batch audit trail — is
  therefore dead code from this page; only Needs You uses it
  (`src/hooks/useAutomation.ts:228`).
- Because each iteration is a separate request, a mid-batch 401 (I-01) logs the
  user out **part-way through**, with some sent and some not, and the toast that
  would have told them never renders.

### Solution

1. **One definition, server-side.** Add `is_ready_to_send: boolean` to the draft
   response, computed from the real predicate, and have the review page use *only*
   that for the badge and the count. Delete the confidence branch from
   `reviewStatus`; keep confidence as the separate signal it is (it already has its
   own "AI confidence 90%" chip in the header).
2. **Route the batch through the guarded endpoint.** Replace the client-side loop
   with a single `POST /ai-emails/send-ready`, and render its
   `{sent, failed[], skipped}` result. That restores the audit trail and makes a
   partial failure legible instead of silent.
3. **Say what the posture is doing.** When the tenant is Manual and nothing is
   pre-approved, the button should be absent and the empty state should explain
   why: *"On Manual, every email waits for your tap. Switch to Autopilot in
   Automation settings to pre-approve high-confidence drafts."* Right now the UI
   quietly contradicts the setting.

---

## I-05 — ~~The whole title task chain disappears when `title_ordered_by` is unset~~ **RETRACTED**

> **CORRECTION (2026-07-28, during Phase 3 implementation). This finding was
> wrong and is withdrawn.** The behaviour is deliberate, tested, and complete.
>
> Attempting the fix broke two existing tests that assert the current behaviour
> on purpose — `test_unanswered_side_excludes_both_tasks` and
> `test_unanswered_title_generates_no_title_task_and_warns`. Reading them showed
> the design I had missed: when the title question is unanswered the system
> raises a **coverage prompt** — `{"key": "title_ordering", "message": "No title
> task exists on this deal — confirm who orders title."}` — which surfaces in
> **Needs You** as a one-click question whose answer PATCHes the field and
> retargets exactly one title task.
>
> Verified live on a purpose-built deal with `title_ordered_by = null`:
> ```
> /plan     → coverage: [{"key": "title_ordering", ...}]
> /needs-you → kinds: {"task": 15, "draft": 18, "coverage": 1}
>              "99 Coverage Probe Lane | No title task exists on this deal — confirm who orders title."
> ```
> So the chain does not vanish *silently* — the system asks, in the queue the
> tester is already working. My original run never observed this because I
> checked Needs You **before** creating that deal and again **after** answering
> the field, never in between. The word "silently" was doing all the work in
> that finding, and it was unearned.
>
> The change was reverted (`_tools/i05_revert.patch`). What was genuinely broken
> is the *downstream* effect — the dependent tasks kept null due dates even
> after the question was answered — and that is **I-06**, which is fixed.
>
> Lesson worth keeping: two failing tests were the signal. A test that asserts
> the behaviour you are about to "fix" is usually a design decision you have not
> read yet.

**Original finding below, retained for the record. Severity: ~~High~~ — not a defect.**

### Symptom

A deal where nobody answered "who orders title?" gets **no title task at all** —
neither *Order Title* nor *Confirm Title Order*. "Order Title" is one of the eight
Automated email tasks and a headline item for this test round; on such a deal it
does not exist.

### Reproduction

| address | use_case | `title_ordered_by` | tasks | title tasks |
|---|---|---|---|---|
| 4567 Oak Ridge Avenue | Buy-Fin | Seller | 40 | Confirm Title Order |
| 5915 E 350 N | Buy-Fin | Buyer | 38 | Order Title |
| 4567 Meadowridge Avenue | Buy-Fin | Seller | 41 | Confirm Title Order |
| **77 Harness Test Lane** | Buy-Fin | **null** | 27 | **— none —** |

Patching `title_ordered_by = "Buyer"` immediately produced *Order Title*, which
confirms the field is the sole cause.

### Root cause

The two templates are a **mutually exclusive pair** — exactly one must always fire:

```
Order Title         #70  conditions: [{"field":"title_responsibility","value":"us"}]
Confirm Title Order #80  conditions: [{"op":"ne","field":"title_responsibility","value":"us"}]
```

`title_responsibility` is derived from `title_ordered_by`
(`dependency_engine.py:446`, `_side_responsibility`), which returns `None` when the
column is unset. And the evaluator excludes on null **for both operators**:

`app/services/dependency_engine.py:541`
```python
if actual is None:
    # Field not set on transaction — condition cannot be confirmed, so
    # exclude the task rather than guess (applies to eq and ne alike).
    return False
```

For an ordinary optional condition ("only if there's an HOA") that rule is right.
For an exhaustive either/or pair it is exactly wrong: "don't guess" silently
deletes the entire branch instead of keeping the safe half of it.

### Blast radius

Larger than two tasks. *Title Work Completed* (#290) depends on #70/#80, and
*Deliver Title* (#300) and *Deliver Title to the Loan Officer* (#320) depend on
#290. With the anchor missing, all three are created with **null due dates** and
can never become due, overdue, or reminder-eligible — 6 of 28 tasks on the harness
deal had no due date, and this is why.

### Solution

1. **Make the pair exhaustive by construction.** Give the "confirm" side of each
   either/or pair a default-when-unknown flag, so a null field resolves to the
   safe branch — chasing the counterparty for confirmation — rather than to
   nothing. Concretely, support `{"op":"ne","field":…,"value":"us","when_null":true}`
   in `evaluate_conditions` and set it on templates #80 and #180 (Confirm Home
   Warranty Order, which has the same shape). Default behaviour for every other
   condition is unchanged.
2. **Backstop the field at intake**, in the same spirit as
   `representation-type-wizard-side-backstop`: when extraction does not determine
   `title_ordered_by`, seed it from the state workflow profile's customary
   ordering side rather than leaving null. A wrong-but-correctable answer is worth
   more than a silently missing workflow.
3. **Detect the impossible state.** Add a generation-time assertion: if a
   `task_family` marked exhaustive yields zero rows, log a warning and include the
   family in the wizard's Review step so the user is asked the question instead of
   losing the branch.

---

## I-06 — Retarget adds the task but never recomputes dependent due dates

**Severity: Medium**

### Symptom

After the missing title task is created (by fixing the field, or by any later key
date edit), the tasks that depend on it keep their null due dates forever.
Completing a predecessor does not fill them in either.

### Reproduction

```
PATCH title_ordered_by=Buyer  →  "Order Title" created ✓
Title Work Completed  | due=null
Deliver Title         | due=null
Deliver Title to the Loan Officer | due=null

PUT /tasks/{Title Work Completed}/status {"status":"Completed"}  →  200
Deliver Title         | due=null       ← unchanged
```

But the dates were computable all along:

```
POST /transactions/{id}/recompute-dates  (dry run)
  Title Work Completed  null -> 2026-08-03
  Deliver Title         null -> 2026-08-03
```

### Root cause

`retarget_conditional_tasks` is wired only to the transaction PATCH
(`app/api/v1/transactions.py:890`) and its job stops at adding and removing rows.
`recompute_task_dates` exists and works, but nothing calls it when the dependency
graph changes underneath it. So a task that gains its anchor keeps the null date it
was born with.

### Solution

1. **Chain the recompute.** When `retarget_conditional_tasks` adds or removes any
   task, follow it with `recompute_task_dates(apply=True)` scoped to that deal,
   inside the same request. The diff is already returned to the caller, so the
   workspace can show "3 dates updated" rather than changing dates invisibly.
2. **Recompute on predecessor completion too.** In the task status-change path,
   when a task with dependents is completed, recompute the dependents' dates from
   the new actual date. This is the behaviour the `FS` / `SS` + float model implies
   and the only reason the model exists.
3. **Never ship a date-less open task silently.** At generation, if a task ends up
   with a null due date because its anchor is missing, mark it
   `metadata_json.date_pending = true` and render it in a "Waiting on an earlier
   step" group rather than dropping it into "on track", where it looks handled and
   is invisible forever.

---

## I-07 — Admin "Run now" / "Send reminders" mail the digest to users who switched it off

**Severity: High**

> Confirmed from source plus verified live state. **I deliberately did not execute
> it** — firing it would have mailed 13 real accounts.

### Symptom

Two admin-facing buttons send the morning digest to **every active user in the
tenant** who has actionable tasks, ignoring the per-user digest opt-in that
Settings → Notifications presents as authoritative ("Morning digest — Off until you
turn it on").

### Verified state

```
GET /api/v1/notifications/digest      → {"enabled": false, "hour": 8, ...}
GET /api/v1/notifications/preferences → daily_summary: {"email": true, ...}
tenant 526cf077…                      → 13 active users
```

### Root cause

Two digest paths with different gates.

**Scheduled path — correct.** `task_notification_service.py:648`:
```python
cfg = normalize_digest_config(user_row.get("profile_settings_json") or {})
if not cfg["enabled"]:
    continue
```

**Admin path — no opt-in check at all.** `task_notification_service.py:620`:
```python
prefs = _normalize_prefs(user_row.get("notification_prefs") or {})
if not prefs.get("daily_summary", {}).get("email", True):
    continue
recipient = _safe_decrypt(user_row.get("email"))
if await send_one_digest(...):
```

The only gate is the notification *channel*, which **defaults to `True`**. So a
user who never touched notification settings — every user in this tenant — is
mailed despite `enabled: false`.

Callers: `POST /api/v1/automation/run-now` (`automation.py:606`) and
`POST /api/v1/ai-emails/reminders/run` (`ai_emails.py:745`).

### Solution

1. **One gate for both paths.** Add the `normalize_digest_config(...)["enabled"]`
   check to `send_daily_summaries`, so the opt-in is honoured no matter who
   triggers the send. The channel pref stays as the second, narrower gate.
2. **Make the admin button's scope explicit.** "Run now" should default to *the
   calling admin only* ("send me my digest now"), with a separate, explicitly
   labelled tenant-wide action behind a confirm dialog that states the recipient
   count: *"Send the morning digest to 13 users now?"* Nobody should be able to
   mail their whole workspace by pressing a button labelled "Run now".
3. **Report what it did.** `RunNowResponse` already returns `summaries_sent`;
   surface it in the UI toast so an accidental blast is at least visible
   immediately.

---

## I-08 — My Task Queue can neither explain nor act on AI-blocked tasks

**Severity: High**

### Symptom

An AI task that is blocked and needs a human appears in **My Task Queue** as an
ordinary overdue row — no badge, no reason, no way to act. The *same task* in the
workspace Tasks tab shows an amber "AI needs you" chip, the full explanation, and
an "Email transaction party" action.

My Task Queue is the page Audri will live in. It is the one that tells her least.

### Reproduction

```
Task queue: shows Buyer Welcome                   = true
Task queue: shows AI-blocked reason ("AI needs you") = false
Task queue: has "Email transaction party" action  = false
Task queue: has "Complete this task" action       = false
```

And in the payload, for all four blocked tasks on the harness deal:
```
Buyer Welcome | critical | due=2026-07-20 | due_state=overdue | ai_reason=null
```

### Root cause

Two gaps.

**The reason is never mapped.** `TaskQueueItem` has an `ai_reason` field, but
`app/api/v1/tasks.py:672` populates it from the task row's own `ai_reason` column —
which is the *"why did the AI suggest this task"* field, used by AI-suggested
tasks. The executor writes its blocker to
`metadata_json.ai_needs_user.reason`, and nothing copies it across. So `ai_reason`
is null for exactly the tasks that most need to explain themselves.

**No action exists.** `TaskEmailFlow` is mounted in `TasksTab.tsx:523` and
`TransactionListPage.tsx:1143`, and reachable from `TasksFullViewModal`. It is
**not** mounted in `TaskQueuePage.tsx`, whose only per-task actions are complete,
reschedule and "open transaction". The cross-deal queue can close a task but not do
the thing that closes it.

### Solution

1. **Carry the blocker into the queue payload.** Populate `ai_reason` from
   `metadata_json.ai_needs_user.reason` when present (falling back to the existing
   column), and add `ai_needs_user: bool` + `ai_blocked_code: str | null`.
2. **Render it.** Give `TaskQueueCard` the same amber "AI needs you" badge and
   reason line the workspace card has. One task, one story, on every surface.
3. **Mount `TaskEmailFlow` in the queue.** Add "Email transaction party" to the
   row's action set, exactly as `TasksTab` does. This is a small change and it is
   the difference between a list and a workspace.
4. **Keep the two surfaces honest going forward.** The backend `is_ai_hidden` and
   the frontend `isAiHandled` are already documented as a mirrored pair that must
   move together; the queue's rendering belongs in that same contract.

---

## I-09 — Task queue "Email all" is a raw `mailto:` — unlogged, unsent, un-Velvet-Elves

**Severity: Medium**

### Symptom

In My Task Queue's vendor grouping, **"Email all"** hands off to the operating
system's default mail client. Nothing is sent from the connected mailbox, nothing
is written to `communication_logs`, the deal has no record of it, and the AI never
sees the thread. It also navigates the SPA away via `window.location.href`.

### Root cause

`src/pages/tasks/TaskQueuePage.tsx:178`
```ts
function emailVendor(cart: VendorCart) {
  const body = cart.tasks.map((t) => `• ${t.task_name} — ${t.transaction_address}`).join('\n')
  window.location.href = `mailto:?subject=${encodeURIComponent(...)}&body=${encodeURIComponent(...)}`
}
```

This is a survivor of the vendor-picker pattern the client rejected in July.
`EmailVendorFlow` was deleted and replaced by `TaskEmailFlow` at the task entry
points, but this vendor-mode button was missed — and it contradicts the product's
central promise that deal email goes from the agent's own mailbox and is logged.

### Solution

Replace it with a real send. Open `TaskEmailFlow` in a multi-task mode seeded with
the cart's tasks: one composed message listing the outstanding items, recipient
resolved through the normal party/vendor resolution, sent through
`compose_outbound` + `send_ai_draft`, logged, and offering to complete the
constituent tasks on success. If multi-task composition is more than this round can
carry, the correct interim behaviour is to **remove the button** rather than keep an
unlogged side channel.

---

## I-10 — Settings → Connections reports "Connected" for a dead mailbox

**Severity: Medium**

### Symptom

Settings → Email & E-signature shows:

> **Gmail** — Connected — crazyaidev20500519@gmail.com — Connected May 12, 2026

The token has been dead since roughly May 19. On 2026-07-28 the page is still
green. There is no health indicator, no "Test connection", and no prompt to
reconnect. The only way to discover the truth is to try to send — which, per I-01,
logs you out.

### Root cause

`GET /api/v1/integrations` returns the stored row and nothing else:
```json
{"provider":"gmail","provider_email":"…","connected_at":"2026-05-12T06:30:37Z","is_active":true}
```
`is_active` is a row flag set at connect time and never revisited. Nothing probes
the credential, and no field carries token state, even though
`metadata_json.token_expires_at` is already stored and the refresh outcome is
already known every time a send is attempted.

Compare the AI provider, which *does* have a live "Test connection" — see
`anthropic-provider-out-of-credit-honest-errors`. Email deserves the same
treatment, and for the same reason.

### Solution

1. **Expose real health.** Add `token_status: 'healthy' | 'expired' | 'unknown'`
   and `last_verified_at` to the integration response, derived from
   `metadata_json.token_expires_at` plus the outcome of the last refresh attempt
   (which I-01's new exception type makes easy to record).
2. **Add "Test connection".** A read-only Gmail/Graph profile call, mirroring the
   AI provider's button, that updates `token_status` and reports plainly. This is
   the single most useful thing Audri can be given for a week of ~7-day tokens.
3. **Surface staleness where the work happens.** When `token_status = 'expired'`,
   show a persistent banner on AI Email Review, Needs You and the workspace
   Email tab with a Reconnect button. She should learn her mailbox is down from
   the app, not from a failed send.
4. **Consider an automatic probe** on the schedule tick, so the state is fresh
   without anyone pressing anything — cheap, and it pairs naturally with the
   existing Gmail watch renewal in the same tick.

---

## I-11 — Orphan drafts with no transaction are invisible to Needs You but sendable in bulk

**Severity: Medium**

### Symptom

Three drafts carry `transaction_id = null`, including one addressed to the
placeholder `party4@example.com`:

```
orphan -> alden.price@minafter.com | conf=0.9 | Welcome — we're under way on 5915 E 350 N…
orphan -> tori.banks@minafter.com  | conf=0.9 | Working together on 5915 E 350 N…
orphan -> party4@example.com       | conf=0.9 | New file: 5915 E 350 N — contract documents
```

They never appear in Needs You, but they do appear in AI Email Review and, at
confidence 0.9, they count toward "Send all ready · 11" (I-04) — so a bulk send
would fire a welcome email at a placeholder address with no deal attached.

### Root cause

Needs You joins drafts to visible transactions and drops anything unmatched —
`app/api/v1/automation.py`, in the drafts loop:
```python
tx = by_id.get(getattr(draft, "transaction_id", None))
if tx is None:
    continue
```
That is right for a deal-scoped queue. The problem is upstream: drafts are being
persisted **without** a `transaction_id` at all, so a genuinely orphaned record is
silently excluded from the surface whose job is to make sure nothing is forgotten,
while remaining live in the surface that can send it.

### Solution

1. **Require the deal at compose time.** Make `transaction_id` non-optional for
   `origin='task_email_flow'` and for executor-composed drafts; reject at the
   service boundary rather than persisting an unattachable record.
2. **Make orphans visible, not invisible.** Give Needs You an "Unattached drafts"
   group rather than dropping them, so anything that does slip through is
   reviewable instead of merely unsendable-by-the-safe-path.
3. **Exclude them from any batch send** until they are attached — belt and braces
   alongside the I-04 fix.
4. **Purge the three existing rows** as part of the Phase 4 data clean-up.

---

## I-12 — No scheduler credential anywhere but `.env.example`

**Severity: Medium** (Blocker for observing automation in stage)

### Symptom

```
POST /api/v1/internal/schedules/tick  →  403 "Invalid or missing scheduler credentials."
GET  /api/v1/automation/status        →  {"last_tick_at": null, "scheduler_healthy": false}
```

Nothing proactive has ever run in this environment: no escalation nags, no morning
digests, no auto-draft sweep, no AI task executor pass, no Gmail watch renewal.

### Root cause

`require_cron_secret` (`app/core/auth.py:179`) is deliberately fail-closed, which is
correct. But `CRON_SHARED_SECRET` is set in **none** of the runtime env files:

```
.env           → absent
.env.stage     → absent
.env.prod      → absent
.env.example   → present  (documentation only)
```

`scripts/run_schedules.py` exists precisely so "a non-developer tester can watch
the morning digest, the escalation nag, and the Auto-Email sweep fire without any
cloud setup" — and it cannot authenticate. This is why nobody caught I-02 earlier:
locally, the executor only ever runs on the generation trigger.

This is the local twin of `prod-scheduler-never-wired`. Stage's runtime truth is
its ECS task definition (secret added 2026-07-23, rev 50), not `.env.stage` — but
prod still has no scheduler at all.

### Solution

1. **Set a local secret** in `.env` and document the two-terminal dev loop in the
   testing guide: backend on :8001, then
   `python scripts/run_schedules.py --base-url http://localhost:8001 --secret … --interval 60`.
2. **Verify stage before Audri starts.** Confirm the task definition still carries
   the secret, fire one manual tick, and read the counts. Per
   `prod-scheduler-never-wired`, a first tick after dormancy can burst a backlog —
   read the numbers before creating any recurring schedule.
3. **Surface the state in the product.** `scheduler_healthy: false` is already
   computed; the automation status chip should say plainly *"Automation is not
   running — the scheduler hasn't checked in"* rather than showing a neutral state.
   Audri needs to be able to tell "the AI decided not to" from "nothing is running".

---

## I-13 — Two "Internal Thank You" rows that look identical to the user

**Severity: Low**

### Symptom

The generated task list contains two rows that are indistinguishable in the UI:

```
Internal Thank You | Agent       | due 2026-09-16 | "Feedback & rating email to agents."
Internal Thank You | Co-op Agent | due 2026-09-16 | "Feedback & rating email to agents."
```

Same name, same description, same date. A tester will report this as a duplicate
bug. It is not — they are genuinely different tasks (thank your own side; thank the
other side) — but nothing on screen says so.

### Root cause

Templates #500 (target Agent), #505 (Both) and #510 (Co-op Agent) share a name and
description and differ only in `target`, which the task card does not render
prominently. Generation correctly selects two of the three for a buyer-rep deal.
The same latent shape exists for *Closing Gift* (#370/#375) and *Deliver Title*
(#300/#305).

### Solution

1. **Disambiguate in the data**: rename to "Internal Thank You — Your Client" and
   "Internal Thank You — Co-op Agent" (and the same for other multi-target
   families), so the list is self-explanatory.
2. **Show the target on the card.** The queue payload already carries `target`;
   render it as a small chip. This also helps the user predict who a task's email
   will go to before opening the flow.

---

## I-14 — The auto-draft sweep cannot be run without also blasting digests

**Severity: Medium**

### Symptom

There is no way to exercise the Auto-Email sweep on its own. Both endpoints that
reach `create_auto_drafts` also call `send_daily_summaries` first:

- `POST /automation/run-now` → summaries, then drafts, then the AI executor
- `POST /ai-emails/reminders/run` → summaries, then drafts

Given I-07, a tester who wants to see "did the auto-draft checkbox work?" must
accept mailing every active user in the tenant. I chose not to, which is why the
sweep is the one path in scope that this run could not exercise.

### Root cause

The two jobs were bundled into a single convenience endpoint. Reasonable for a cron
tick, wrong for a manual button — the tick runs unattended, the button is pressed
by a person who wants one specific effect.

### Solution

1. **Split the actions.** Give `run-now` a `jobs` parameter
   (`['digests','drafts','ai_tasks']`, defaulting to drafts + AI tasks — the two
   that send nothing to third parties) and expose them as separate controls in the
   Automation panel.
2. **Label each by its effect**, e.g. "Draft due emails (nothing sends)" versus
   "Send morning digest to N users". The distinction between *prepares* and *sends*
   is the most important one in this product; the UI should never blur it.
3. **Add the missing test hook**: a per-deal "Run automation on this deal" action
   in the workspace, which is what a tester actually wants and which has a blast
   radius of one file.
