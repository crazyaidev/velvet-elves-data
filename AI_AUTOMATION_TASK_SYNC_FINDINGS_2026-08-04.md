# AI automation ↔ task management — sync test findings

**Date:** 2026-08-04
**Question under test:** *are AI automation and task management functioning in sync?*
**Tester:** Jan Froben · role **Admin** (`shyna.elene@minafter.com`, tenant `526cf077-59da-496a-aa38-8f8d761c29da`)
**Environment:** real Chrome (puppeteer-core driving system Chrome), frontend
`localhost:5173`, backend `localhost:8000` (current working tree)
**Data:** 6 Active deals, 210 tasks, 20 of them AI-owned (`automation_level='Automated'`)

Harness: `C:\Projects\_tools\e2e\txn\a01…a04` · raw JSON + screenshots:
`C:\Projects\_shots\txn\`

> **No source code was changed for this test.** Data mutations were limited to
> reversible probes (one due-date change, one task completion, three posture
> flips), each restored immediately and verified restored.
>
> **One test was NOT run, and needs your go-ahead.** A healthy Gmail mailbox is
> connected (`crazyaidev20500519@gmail.com`, token verified 2026-07-31), so
> triggering the executor's send path — `POST /automation/run-now` with
> `jobs:["ai_tasks"]`, or the scheduler tick — **would send real email to real
> parties** (`tori.banks@…`, `drew.linden@…`). I proved the send-path logic from
> source instead. See §5.

---

## 1. Answer

**No. They are not in sync, and the gap is not cosmetic.**

The task engine is running normally. The AI automation engine that is supposed
to work those tasks **has not run since 2026-07-28 — seven days** — and nothing
anywhere in the product says so. On its last run it failed on 95% of what it
attempted (40 tasks surfaced, 2 completed). Of the tasks it gave up on, **most
can never be retried by any means available to a user**, because the flag that
blocks retry can only be cleared by the very code path the flag prevents from
running.

Meanwhile the interface tells the user the opposite: the Needs You page reads
*"Everything routine already ran on its own"*, and each deal's Activity lens
reads *"Nothing has run automatically on this deal yet"* — on a deal where the
AI did complete a task.

| Severity | Count | IDs |
| --- | --- | --- |
| Blocker | 4 | A-01 … A-04 |
| High | 3 | A-05 … A-07 |
| Medium | 4 | A-08 … A-11 |

---

## 2. Measured state

```
GET /api/v1/automation/status
  last_tick_at        2026-07-28T21:12:15Z      (7 days ago)
  scheduler_healthy   false
  scheduler_state     "stale"
  last_tick_counts    { ai_tasks_completed: 2, ai_tasks_surfaced: 40,
                        auto_drafts_created: 0, escalations_sent: 42,
                        tenants_swept: 22, tenant_errors: 0 }
```

Per-deal, from `GET /transactions/{id}/plan` and `GET /tasks/transaction/{id}?include_ai=true`:

| Deal | Posture | Automated tasks | Stuck (`ai_needs_user`) | `handled_today` | `needs_you` |
| --- | --- | --- | --- | --- | --- |
| Test Seller & Daniel Carter | manual *(inherited)* | 3 | 3 — all `stale_overdue` | 0 | 17 |
| Michael Koenig & Heather Hall-Koenig | manual | 5 | 4 — 3× `execution_error`, 1× `stale_overdue` | 0 | 3 |
| Amelia Brooks | manual | 2 | 0 | 0 | 0 |
| Maya Ellis & Jordan Ellis | manual | 3 | 0 | 0 | 0 |
| Harness Buyer & Harness Seller | manual | 5 | 5 — 2× `execution_error`, 2× `missing_document`, 1× `no_documents_to_review` | 0 | 2 |
| Livefire Buyer & Livefire Seller | manual | 5 | 3 — 1× `no_documents_to_review`, 2× `missing_document` | 0 | 3 |

**15 AI-owned tasks are stuck.** Six carry non-retryable codes
(`execution_error` ×5, `stale_overdue` ×4 — see A-02 for why that matters).

---

## 3. Blockers

### A-01 · The automation engine has been dead for a week and no screen says so

**Severity:** Blocker · **Area:** scheduler ↔ every automation surface

`scheduler_state: "stale"`, last tick 2026-07-28. The AI task executor, the
auto-draft sweep, escalations and digests all ride that tick
(`internal_schedules.py:121-200`), so all of them are dormant.

The API knows. **No user-facing surface reports it.** Measured with a regex for
any phrasing of "not running / stopped / stale / hasn't run / last ran":

| Surface | Warns engine stopped? | "Run now" available? |
| --- | --- | --- |
| `/needs-you` | **no** | no |
| `/settings/ai-automation` | **no** | no |
| deal workspace | **no** | no |
| `/dashboard` | **no** | no |

The only signal a user gets is indirect and misleading: every deal's posture
chip reads *"0 handled today"*, which is indistinguishable from "a quiet day".

This also matches the known production gap — `prod-scheduler-never-wired`
records that EventBridge and `CRON_SHARED_SECRET` were never provisioned in
prod, so this is not a local-only artifact.

**Fix direction:** `GET /automation/status` already returns
`scheduler_healthy`. Surface it as a banner on `/needs-you` and in the deal
posture menu ("Automation last ran 7 days ago — it is not running"), and expose
the existing admin **Run now** where an operator will see it.

---

### A-02 · A task the AI gives up on can never be retried — a hard deadlock

**Severity:** Blocker · **Area:** `ai_task_executor.py`

The executor skips any task already carrying `ai_needs_user` whose code is not
in `_RETRYABLE_CODES` (`ai_task_executor.py:301-303`):

```python
flag = ai_needs_user(row)
if flag is not None and flag.get("code") not in _RETRYABLE_CODES:
    continue  # waiting on the user; don't churn
```

`_RETRYABLE_CODES` = `no_recipient`, `missing_document`,
`no_documents_to_review`, `unsigned_documents`, `mailbox_reconnect_required`
(`:201-214`). So **`execution_error`, `stale_overdue`, `send_failed` and
`no_provider` are terminal.**

And the *only* place that flag is ever cleared is `_complete_task`
(`:892`, `meta.pop(AI_NEEDS_USER_KEY, None)`) — which runs **only** when the
executor successfully completes the task, which the `continue` above prevents.
Verified exhaustively: `grep -rn AI_NEEDS_USER_KEY app/` shows exactly one
writer (`_surface_task`, `:939`) and one clearer (`_complete_task`, `:892`).

There is no endpoint, no admin action and no UI control that clears it —
`/needs-you` offers **no retry control at all** (measured: zero buttons matching
/retry|re-?arm|try again|run/).

**Nine tasks in this tenant are in this state permanently.**

**Fix direction:** clearing `ai_needs_user` must be possible without the
executor — either a "Give this back to the AI" action on the task/Needs-You row
that pops the flag, or clear it automatically whenever the user changes a field
the reason depends on (due date, target, document attachment).

---

### A-03 · The product tells the user to do something that does not work

**Severity:** Blocker · **Area:** executor copy ↔ task PATCH · **Browser-verified**

Every `stale_overdue` task displays, verbatim:

> "This task has been overdue since 2026-06-17. The AI won't send an email this
> late without your say-so — **complete it manually or update the due date to
> re-arm it**."

I did exactly that, through the API the UI uses:

```
task  eff6773e-c3e0-44d5-8d5d-4bace3dd1e6d  "Buyer Welcome"
PATCH /tasks/{id} { due_date: "2026-08-05" }   → 200
re-read: due_date   = "2026-08-05"          ✅ the date changed
         ai_needs_user = { code:"stale_overdue", at:"2026-07-28T20:57:51Z" }
                                             ❌ UNCHANGED — still blocked
```

(Restored to `2026-06-17` afterwards.)

`PATCH /tasks/{id}` merges only `auto_draft_email` and `basis` into
`metadata_json` (`tasks.py:935-966`); it never touches `ai_needs_user`. The
instruction is false, and it is the *only* recovery instruction the product
gives for this state.

---

### A-04 · Completing a stuck task leaves the AI error attached; reopening brings it back

**Severity:** Blocker · **Area:** task status ↔ AI flag · **Browser-verified**

```
task 2fcbf060-2dc5-46e6-90d4-986618f4a746 "Buyer Welcome" (execution_error)
PATCH status → Completed          → 200
  status                = Completed
  ai_needs_user present = TRUE     ❌ not cleared
  Needs-You queue entry = removed  (queue filters on status, not the flag)
PATCH status → Pending  (restore) → 200
  ai_needs_user present = TRUE     ❌ the stale AI error is back
```

So the user's manual completion is recorded, but the deal still carries an
invisible "AI needs you" marker. Anyone who completes a task by mistake and
reopens it gets a week-old AI error presented as current. Combined with A-02,
the flag is now unremovable by any means.

---

## 4. High

### A-05 · "Manual" posture does not stop the AI from sending

**Severity:** High · **Area:** posture ↔ executor

The posture menu — which I verified renders these three captions verbatim —
promises:

| Choice | Caption shown to the user |
| --- | --- |
| **Manual** | *"AI proposes; you click to apply anything."* |
| Assisted | *"Safe actions run on their own; emails wait in review."* |
| Autopilot | *"Hands-off; only sends and judgment calls wait for you."* |

**The AI task executor contains no posture check whatsoever.** `grep -n
"posture" app/services/ai_task_executor.py` returns exactly one hit — a line of
prose in the module docstring saying it *deliberately* bypasses posture:

> "This deliberately goes beyond the automation posture's 'nothing sends without
> a tap' rule … the product owner designated these specific rows as AI-executed."

All six deals in this tenant are on **Manual**. When the scheduler is restored,
the executor will send Buyer/Seller/Co-op-Agent/Loan-Officer Welcome emails,
Order Title and Confirm Title Order **without a click**, to real parties, on
deals whose own control says "you click to apply anything".

This may be the intended product decision — the docstring says it was made
deliberately. **The defect is that the UI states the opposite.** A user reading
that caption cannot predict the system's behaviour, which is the definition of
out-of-sync.

**Fix direction:** either gate the executor on posture, or change the Manual
caption to name the exception (e.g. *"AI proposes; you apply. Welcome emails and
title orders still send automatically."*).

### A-06 · The Needs You page claims everything routine already ran

**Severity:** High · **Browser-verified** (`_shots/txn/a04_needs_you.png`)

Header: **"Needs You — 43 waiting · 0 ready to send"**, and immediately below:

> **"Everything routine already ran on its own.** Waives, date changes, and
> anything unusual always stay individual."

Nothing routine ran. The engine has been stopped for seven days, 15 tasks are
stuck, and 9 of them cannot be recovered. The buckets read
`0 READY TO SEND · 0 TO APPROVE · 28 TO REVIEW · 0 TO DECIDE · 15 TO HANDLE`.
The copy is static reassurance presented as a status report.

### A-07 · The Activity → Automation lens denies work the AI actually did

**Severity:** High · **Browser-verified**

On the Koenig deal, the Automation lens reads:

> "Nothing has run automatically on this deal yet. When your automation posture
> lets the AI apply a safe action or draft a routine email, it appears here with
> an Undo."

But on that same deal the AI **completed a task**: `Review Documentation`,
`completed_at 2026-07-22T10:55:54Z`, `automation_level = Automated`, carrying an
`ai_execution` metadata block. `GET /transactions/{id}/automation/activity`
returns `{"items": []}`.

The lens is fed only by agent *actions* (the approve/undo pipeline); **AI task
executions are never written to it**. The one surface whose stated job is "show
me strictly what ran without a click" is blind to the executor — the largest
source of unattended AI work in the product.

---

## 5. What I did NOT test — needs your decision

The executor's **send path** was not exercised. Running it (`POST
/automation/run-now {jobs:["ai_tasks"]}` or a tick) would, with the healthy
Gmail token now connected, send real welcome/title emails to the addresses
captured on these deals.

What that test would settle, and nothing else can:

1. whether `execution_error` reproduces (i.e. the executor is still broken, not
   just historically broken);
2. whether the two retryable classes (`missing_document`,
   `no_documents_to_review`) clear themselves once a purchase agreement is
   attached;
3. whether a successful run increments `handled_today` and appears in the
   Automation lens.

**Two safe ways to get it**, if you want it:

- **(a)** Point the tenant's mailbox at a sink address (or disconnect Gmail) and
  run `jobs:["ai_tasks"]` — the executor then surfaces `no_provider` instead of
  sending, which still exercises selection and flag-writing.
- **(b)** Create a throwaway deal whose parties all use a mailbox you control,
  and run the executor scoped to it.

`jobs:["drafts"]` is safe on its own — it only *prepares* pending-review drafts
— but with the tenant on Manual it flags nothing, so it would tell us little.

Say which you'd prefer and I'll run it.

---

## 6. Medium

| ID | Finding | Evidence |
| --- | --- | --- |
| **A-08** | **Needs-You count disagrees with every deal's own count.** The queue holds 43 items (28 drafts + 15 tasks); the sum of each deal's `automation.needs_you` is 25. Per deal: Test Seller 17 vs 20, Koenig 3 vs 7, Harness 2 vs 7, Livefire 3 vs 6 — **not one matches**. Two different definitions of "needs you" ship side by side, one in the header chip and one in the queue. |
| **A-09** | **A deal can never go back to inheriting the workspace default.** `apply_deal_posture` always writes `DEAL_POSTURE_KEY` into the transaction metadata (`automation_posture_service.py:194-196`) and there is no null/inherit value — `PUT /transactions/{id}/automation` only accepts the three postures. Measured: the Koenig deal began as `manual (source: tenant_default)`; after setting it to `manual` — the same value — it is permanently `manual (source: deal)`. Changing the workspace default will now silently skip it, and the UI gives no way to undo the pin. |
| **A-10** | **Work the AI completes is invisible in the deal's progress.** Koenig: the AI completed `Review Documentation`, yet `plan.header.counts` reports `tasks_completed: 0` of `tasks_total: 37`, and the header renders "0% complete". AI-owned tasks are excluded from progress by the canonical rule (correct, and deliberate), but nothing else credits the work either — `handled_today` is 0 and the Automation lens is empty (A-07). The AI can complete a deal's tasks and leave no trace on any counter the user reads. |
| **A-11** | **The executor's last real run failed on 95% of what it touched** — 40 surfaced, 2 completed — with `tenant_errors: 0`, so nothing escalated and no operator was told. `execution_error` (a caught, unclassified exception, `:305-318`) appears on 3 deals, which points at one systemic failure rather than per-deal data problems. Its message to the user — *"The AI hit an unexpected error… Please handle it manually"* — names no cause and, per A-02, is terminal. |

---

## 7. What is working correctly

Recorded so the fixes do not regress it:

- **Posture → task flag propagation is exact.** Setting Assisted flagged 29 open
  tasks with a mappable target; Manual unflagged exactly the same 29; the
  reported `tasks_flagged` / `tasks_unflagged` matched the stored
  `auto_draft_email` count every time. Completed and Skipped tasks were never
  touched, as the contract promises.
- **The posture chip round-trips through the UI.** Choosing Autopilot from the
  header menu persisted (`posture: autopilot, source: deal`) and the chip
  re-rendered immediately.
- **The per-task Auto-Email checkbox is honest.** It reads
  `Boolean(meta.auto_draft_email)` and rendered unchecked on all 28 eligible
  rows, matching the stored state exactly. *(I initially suspected a desync
  here; on inspection the label simply renders beside an unchecked box. Not a
  defect.)*
- **Surfacing is well designed where it runs.** Reasons are specific and
  actionable (`missing_document` names the purchase agreement;
  `no_documents_to_review` explains there is nothing to read), and
  `humanize_send_failure` turns provider errors into sentences naming a fix.
  The safety model — named playbook only, deterministic templates, captured
  recipients only, no mailbox → no send — is sound.
- **The retryable/non-retryable split is correctly reasoned.** `send_failed`
  stays terminal because a retry could duplicate a sent email;
  `mailbox_reconnect_required` is retryable because it fails before composition.
  The bug is the missing manual escape hatch (A-02), not this taxonomy.
- **Zero console errors and zero 4xx** across the whole sweep.

---

## 8. Suggested order

1. **A-01** — surface `scheduler_healthy` and get the tick running. Everything
   else is theoretical until the engine runs.
2. **A-02 + A-03 + A-04** — one change: make `ai_needs_user` clearable by the
   user, and clear it on the edits the reasons tell people to make. Then fix
   the instruction text.
3. **A-06 + A-07** — stop the two surfaces asserting things that are false;
   feed executor runs into the Automation lens.
4. **A-05** — decide whether posture gates the executor, then make the caption
   match whichever way you decide.
5. **A-08 … A-11** — one definition of "needs you"; an inherit option; credit
   AI work somewhere the user can see.
