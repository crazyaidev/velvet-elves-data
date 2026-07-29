# Scheduler & Stage Enablement — Runbook

**Date:** 2026-07-28
**Owner:** Jan (steps 1-4) · Audri & Jake (step 5)
**Context:** `TASK_EMAIL_E2E_REMEDIATION_PLAN_2026-07-28.md` §14 (Phase 5)

Turning the scheduler on is the last thing standing between the fixed code and
Audri being able to watch automation work. It is also the single most dangerous
button in this system, so this is a runbook rather than a paragraph.

---

## 0. Read this first — the tick's blast radius is every tenant

`POST /api/v1/internal/schedules/tick` is **cross-tenant by design**. One call
sweeps every tenant with an active user and, for each, runs the AI task executor
— which **sends real email to real deal parties through whatever mailbox that
tenant's deal owner has connected.**

I learned this the hard way twice while implementing these fixes, on the dev
database:

| What I ran | What I believed | What actually happened |
|---|---|---|
| `POST /automation/run-now` (tenant-wide) | "drafts + ai_tasks send nothing to third parties" | **2 emails** sent to deal parties on a dev deal |
| `POST /internal/schedules/tick` with the *Google* client secret deliberately broken | "no mail can leave" | **2 emails** sent — those users were on **Outlook**, whose refresh uses the *Microsoft* secret I had left working |

Both were my error, and the second is the instructive one: a safety guard that
covers one provider is not a safety guard. The system has three (Gmail, Outlook,
iCloud), and a cross-tenant job will find whichever one is live.

**Rule that follows: never "test" a tick against a database that has live mail
credentials you have not personally accounted for.** On the dev DB right now
there are **13 active mail integrations** (8 Gmail, 5 Outlook) across 22 tenants.

---

## 1. Local dev loop (DONE — for reference)

`CRON_SHARED_SECRET` is now set in `velvet-elves-backend/.env`. Verified:

```
POST /internal/schedules/tick                          → 403   (no header)
POST /internal/schedules/tick  X-VE-Cron-Secret: wrong  → 403
POST /internal/schedules/tick  X-VE-Cron-Secret: <ok>   → 200
```

To watch automation fire on a developer machine:

```bash
# terminal 1
venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
# terminal 2
venv/Scripts/python.exe scripts/run_schedules.py \
    --base-url http://localhost:8001 --secret "$CRON_SHARED_SECRET" --interval 60
```

A real local tick returned:

```
escalations_sent      : 42     ← internal log rows (channel=system, direction=internal), NOT email
digests_sent          : 0      ← the Phase 4 opt-in gate, holding across 22 tenants
auto_drafts_created   : 0
ai_tasks_completed    : 2      ← ⚠ this is where email goes out
ai_tasks_surfaced     : 40
tenants_swept         : 22     tenant_errors: 0
gmail_watches_checked : 8      renewed: 0   failures: 8
cost_sync             : ran, AWS 555 rows
```

Two useful facts from that run: **escalations are internal rows, not email** (so
that count is not a spam risk), and **digests came out at 0** because every user
has the digest switched off — before Phase 4 that number would have been a real
blast.

---

## 2. Stage — confirm the secret is still wired (Jan)

Runtime truth is the ECS task definition plus Secrets Manager, **not**
`.env.stage` (which does not carry it).

```bash
aws ecs describe-task-definition --task-definition velvet-elves-stage-backend \
  --query "taskDefinition.secrets[?name=='CRON_SHARED_SECRET']"
aws secretsmanager get-secret-value --secret-id /velvet-elves/stage/backend \
  --query SecretString --output text | jq 'has("CRON_SHARED_SECRET")'
```

Expected: present (added 2026-07-23, task-def rev 50). If absent, add it and roll
the service before going further.

---

## 3. Stage — ONE manual tick, read the counts, do not automate yet (Jan)

Stage has ~17 tenants that have been dormant for months. The first tick after
dormancy can fire a backlog of real email in one go.

**Before firing, neutralise the executor.** The only job in the tick that mails
third parties is the AI task executor. Choose one:

- **(a) Preferred** — confirm which stage tenants have an active mail
  integration, and that every one is a mailbox you or Audri control:
  ```sql
  select t.name, i.provider, i.provider_email, i.is_active
  from integrations i join users u on u.id = i.user_id
  join tenants t on t.id = u.tenant_id
  where i.is_active and i.provider in ('gmail','outlook','icloud');
  ```
- **(b)** Disconnect any mailbox that is not yours for the duration of the test.

Then fire exactly one tick:

```bash
curl -sS -X POST https://<stage-host>/api/v1/internal/schedules/tick \
     -H "X-VE-Cron-Secret: $STAGE_CRON_SECRET" --max-time 600 | jq
```

**Expect the HTTP call to time out while the tick keeps running server-side.**
The last stage run took ~3.5 minutes and exceeded the ALB's 60s idle timeout.
**Do not retry on a timeout — you will double-fire.** Confirm the outcome in
CloudWatch (`/ecs/velvet-elves/stage/backend`, search `schedule tick:`) or via
`GET /api/v1/automation/status`, which now reports `scheduler_state`
(`ok` / `stale` / `never_run`) alongside the counts.

Read `ai_tasks_completed` before doing anything else. That number is emails sent.

---

## 4. Stage — only then, the recurring schedule (Jan)

Once a manual tick has produced a sane `ai_tasks_completed`, create the hourly
EventBridge rule. Not before.

> **Prod is a separate decision.** Per `prod-scheduler-never-wired`, production
> has never ticked once — no EventBridge rule, and `CRON_SHARED_SECRET` absent
> from both the task definition and Secrets Manager. Everything above applies
> there with more force, because prod's recipients are actual clients.

---

## 5. Stage — Gmail (Audri & Jake)

1. Connect Gmail in **Settings → Email & E-signature**. Expect Google's
   "unverified app" warning; continue through it.
2. Confirm the connection took: the integration should report
   `token_status: healthy` (recorded automatically on every successful refresh
   since Phase 1).
3. Send one email to yourself from any task to prove the path.
4. **Expect to repeat this roughly weekly** until Google verifies the app.
   That is now a visible, one-click recovery rather than a logout — but it does
   still need doing.

### Inbound (replies) needs one more thing

Outbound works as soon as the mailbox is connected. **Inbound** additionally
needs the Pub/Sub push endpoint to point at a live host. Locally it is a stale
ngrok tunnel (finding I-15); on stage, verify
`EMAIL_WEBHOOK_PUBLIC_BASE_URL` / `PUBSUB_PUSH_AUDIENCE` resolve to the current
stage hostname. The notification URL is baked into the Gmail watch at
registration, so **after changing it, reconnect Gmail** or the watch keeps
pushing to the old address.

---

## 6. Acceptance — what "ready for Audri" means

- [ ] `GET /automation/status` on stage reports `scheduler_state: "ok"` with a recent `last_tick_at`
- [ ] A stage deal's welcome emails send and self-complete on the tick alone
- [ ] Audri and Jake each have a connected Gmail reporting healthy
- [ ] A reply to one of those emails appears in AI Email Review (proves inbound)
- [ ] The draft backlog has been purged (`scripts/purge_draft_backlog.py --apply`)
