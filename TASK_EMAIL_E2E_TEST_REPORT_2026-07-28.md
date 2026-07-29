# Task Lists & Email — End-to-End Test Report (local, real browser)

**Date:** 2026-07-28
**Tester:** Jan (Claude-assisted, automated browser harness)
**Purpose:** Verify the task-list and email features work end to end *before* Audri
and Jake test them in stage, per the 2026-07-27 thread ("any idea when we will be
able to test the true functionality of the task lists/email functionality").
**Scope:** task generation → task surfaces → task email flow → AI Email Review →
automation/scheduler. Wizard extraction was explicitly out of scope (covered by
`AI_WIZARD_AUDRI_FEEDBACK_2026-07-27_RESOLUTION_PLAN.md`).

**Companion documents**
- `TASK_EMAIL_E2E_ISSUES_AND_SOLUTIONS_2026-07-28.md` — every issue, its root cause and its solution.
- `TASK_EMAIL_E2E_REMEDIATION_PLAN_2026-07-28.md` — the sequenced fix plan.

> **No source code was changed during this exercise.** The only files written were
> throwaway harness scripts outside every repo (`c:\Projects\_tools\e2e\`) and these
> three documents.

---

## 1. Headline result

**The task-list and email features are not ready for Audri to test as-is.**

Fourteen distinct defects were found, four of them blocking. The single most
damaging one is not in the task engine at all — it is that **an expired mailbox
token returns HTTP 401, and the SPA logs the user out on any 401.** So the moment
Audri's weekly Gmail expiry hits (which it will, because Google has not verified
the app yet), every attempt to send a task email will throw her back to the login
screen with the message *"Your session has expired for your security."* — a message
that is not true and gives her no way to discover the real problem.

That single bug will make the entire test week look like a broken product. Every
other finding is downstream of, or smaller than, that one.

---

## 2. Environment

| Component | Setting |
|---|---|
| Backend | fresh `uvicorn app.main:app` on `127.0.0.1:8001` (per `ve-dev-backend-stale-8000`: the long-running :8000 instance serves stale code) |
| Frontend | `vite` dev server on `localhost:5173`, `VITE_API_BASE_URL=http://localhost:8001` |
| Database | shared dev Supabase (`bkkefsdikcerrtbxvfaw`) |
| Account | `shyna.elene@minafter.com` — Admin, platform admin, tenant `526cf077-59da-496a-aa38-8f8d761c29da` |
| Browser | system Chrome via `puppeteer-core`, headless, 1600×1000 |
| AI provider | OpenAI `gpt-5.4` (`AI_PROVIDER=openai`) |
| Mailbox | Gmail `crazyaidev20500519@gmail.com`, connected 2026-05-12 — **OAuth refresh token dead** |

### 2.1 A harness note worth keeping

The browser must be driven against **`http://localhost:5173`**, not
`http://127.0.0.1:5173`. `CORS_ORIGINS` lists `localhost`, and the browser treats
the two as different origins, so every API call fails CORS and login silently does
nothing. This cost the first two harness runs and will cost anyone else the same.

### 2.2 Safety rules I worked under

Deal email sends from the *user's own connected mailbox* to real people, so I
constrained the blast radius deliberately:

- I created a dedicated harness deal whose every party email is an address I
  control (`crazyaidev20500519@gmail.com`, the connected mailbox itself, and
  `shyna.elene@minafter.com`, the test admin). Every send I triggered was
  self-addressed.
- **No email left the system during this exercise.** Every send attempt failed at
  provider resolution (dead token) before a message was composed on the wire.
- I did **not** fire `POST /automation/run-now` or `POST /ai-emails/reminders/run`.
  Both send morning digests to *every active user in the tenant* (13 accounts here).
  Issue **I-07** — which says they do that even though every one of those users has
  the digest switched off — is therefore confirmed from source plus verified live
  state, **not** by executing the blast.

---

## 3. Test data created

| Object | Id / value |
|---|---|
| Harness transaction | `f8bf6263-99cd-4ed6-8225-b9a5a951de07` — "77 Harness Test Lane, Columbus, OH 43004", Buy-Fin, close 2026-09-15 |
| Parties | buyer, seller, listing_agent (co-op), loan_officer, title_rep — all self-owned emails |
| Tasks generated | 27 initially, 28 after the title fix experiment |
| Drafts produced | 5 on this deal (3 of them duplicates — see I-03) |

This deal is still in the dev tenant and is useful as a live reproduction. Delete
it when the fixes land.

---

## 4. Scenarios executed

| # | Scenario | Method | Result |
|---|---|---|---|
| S-1 | Route sweep — 13 task/email routes render without console or API errors | browser | **PASS** — 0 console errors, 0 page errors, 0 failed API calls |
| S-2 | Create deal → generate tasks → inspect the generated set | API | **FAIL** — I-05 (title chain missing), I-13 (duplicate-looking rows) |
| S-3 | AI task executor runs on generation | API + DB inspection | **FAIL** — I-02 (two tasks parked with an opaque error) |
| S-4 | Task email plan resolves the matrix target | API | **PASS** — correct recipient, subject, body, party dropdown |
| S-5 | Workspace Tasks tab → "Email transaction party" → "Send & complete task" | browser | **FAIL** — I-01 (logged out) |
| S-6 | AI Email Review → "Approve & send" | browser | **FAIL** — I-01 (logged out) |
| S-7 | Repeated failed sends | API | **FAIL** — I-03 (drafts 3 → 5) |
| S-8 | "Send all ready" semantics vs Needs You | browser + API | **FAIL** — I-04 (11 vs 0 on identical data) |
| S-9 | My Task Queue surfaces and actions | browser + API | **FAIL** — I-08 (no reason, no action) |
| S-10 | Conditional retarget after a key-date edit | API | **PARTIAL** — task appears (good), dates stay null (I-06) |
| S-11 | Dependent due-date fill on predecessor completion | API | **FAIL** — I-06 |
| S-12 | Scheduler tick | API | **FAIL** — I-12 (403, no local secret; never ticked) |
| S-13 | Digest opt-in honoured by admin run buttons | source + live state | **FAIL** — I-07 |
| S-14 | Mailbox health visible in Settings → Connections | browser | **FAIL** — I-10 (green "Connected" on a dead token) |

---

## 5. Key evidence

### 5.1 The logout (I-01) — the one that matters most

Driving the real UI: workspace → Tasks tab → *Order Title* kebab → **Email
transaction party** → **Send & complete task**.

```
clicked "Send & complete task": true
URL before=/transactions/f8bf6263-…?tab=tasks  after=/login
token still present: false
LOGGED OUT: true
page mentions session expired: true
```

The login page then renders both a false explanation and, in a toast the user can
no longer act on, the true one:

> *Your session has expired for your security. Please sign in again to continue.*
> *Gmail credentials expired — please reconnect.*

Screenshot: `c:\Projects\_shots\e2e\02-05-after-send.png`.

Reproduced independently from AI Email Review → **Approve & send**:

```
401 POST /api/v1/ai-emails/{id}/approve  {"message":"Gmail credentials expired — please reconnect."}
url after = http://localhost:5173/login      LOGGED OUT = true
```

### 5.2 The opaque executor failure (I-02)

On a **brand-new** deal, seconds after `POST /transactions/{id}/tasks/generate`:

```
Review Documentation   | Automated | Pending | NEEDS:no_documents_to_review
Buyer Welcome          | Automated | Pending | NEEDS:execution_error
Co-op Agent Welcome    | Automated | Pending | NEEDS:execution_error
Loan Officer Welcome   | Automated | Pending | NEEDS:missing_document
```

The user-facing text is *"The AI hit an unexpected error while working on this
task. Please handle it manually."* Nothing anywhere records what the error was.
`execution_error` is not in `_RETRYABLE_CODES`, so **reconnecting Gmail does not
un-stick these tasks** — they wait for a human forever.

Screenshot: `c:\Projects\_shots\e2e\02-02-tasks-tab.png`.

### 5.3 Duplicate drafts pile up (I-03)

```
drafts on harness deal BEFORE: 3
attempt 1 -> HTTP 401   attempt 2 -> HTTP 401
drafts on harness deal AFTER 2 more attempts: 5
```

Screenshot `03-02-draft-open.png` shows three byte-identical *"Welcome — we're
under way on 77 Harness Test Lane"* drafts to the same recipient, each badged
green **"Ready to send"**. If the mailbox is reconnected and the user taps
"Send all ready", that buyer is welcomed five times.

### 5.4 Two surfaces, one dataset, contradictory answers (I-04)

| Surface | Says |
|---|---|
| AI Email Review | **"Send all ready · 11"**, 11 green "Ready to send" badges |
| Needs You | **"0 ready to send"** |
| Database | `approval_status='auto_approved' AND status='ready_to_send'` → **0 rows** |

The review page derives "ready" from `ai_confidence >= 0.8` on the client. It has
nothing to do with the automation posture that is supposed to govern sending, and
it does not use the guarded batch endpoint.

### 5.5 The title chain vanishes (I-05)

```
address                        use_case   title_ordered_by   tasks   title tasks
4567 Oak Ridge Avenue          Buy-Fin    Seller             40      [Confirm Title Order]
5915 E 350 N                   Buy-Fin    Buyer              38      [Order Title]
8104 Riverstone Place          Buy-Cash   Buyer              35      [Confirm Title Order]
4567 Meadowridge Avenue        Buy-Fin    Seller             41      [Confirm Title Order]
77 Harness Test Lane           Buy-Fin    null               27      []          ← no title task at all
```

*Order Title* and *Confirm Title Order* are a mutually exclusive pair — exactly one
should always fire. When the field is null, **neither** does, and the flagship
"Order Title" automated email simply does not exist on the deal. The gap cascades:
Title Work Completed, Deliver Title and Deliver Title to the Loan Officer all
inherit a null due date and can never become due.

---

## 6. What did pass

Worth stating plainly, because most of this machinery is sound:

- **All 13 task/email routes render clean** — zero console errors, zero page
  errors, zero failed API calls across the sweep.
- **Task generation is fast and largely correct** — 27 tasks on a fresh Buy-Fin
  deal, correct milestone dates, correct use-case filtering, correct dual-agency
  and attorney-workflow exclusions.
- **The matrix target routing works.** `GET /tasks/{id}/email-plan` resolved
  *Order Title* → Title Rep with the right subject, a well-written body, the deal
  owner auto-cc'd, and a complete transaction-party dropdown. This was the feature
  the client asked for in July and it behaves exactly as specified.
- **`cc_targets` parsing is correct** — `"Agent, Co-op Agent"` in the source CSV is
  stored as `["Agent","Co-op Agent"]`, so the co-op cc rule matches.
- **The Automated template set is correct** — all 8 expected templates carry
  `automation_level='Automated'`; both pending migrations are applied in this DB.
- **Review Documentation works** — it auto-completed on a deal with six signed
  documents and correctly reported `no_documents_to_review` on the empty harness deal.
- **Conditional retarget works** — patching `title_ordered_by` immediately created
  the correct title task (its dates are the problem, not its existence).
- **`recompute-dates` computes correctly** — the dry run resolved the null dates to
  2026-08-03. The data was always derivable; nothing calls it at the right moment.

---

## 7. Recommendation on timing

Audri asked when they can test task lists and email. My answer, based on this run:

- **I-01 and I-02 must land before she connects Gmail.** They are the difference
  between "the automation had a problem, here's what and why" and "the app keeps
  logging me out". Both are small, well-understood fixes.
- **I-03, I-04, I-05, I-07 should land in the same pass.** Each one produces
  behaviour a tester will reasonably report as a bug, and I-07 can email 13 people
  by accident.
- The remainder are safe to schedule after the first feedback round.

Sequencing and effort are in `TASK_EMAIL_E2E_REMEDIATION_PLAN_2026-07-28.md`.

One prerequisite is outside the code: **stage needs a live Gmail connection and a
running scheduler tick**, or the automated tasks Audri is meant to observe will
never fire at all (see I-12 and `prod-scheduler-never-wired`).
