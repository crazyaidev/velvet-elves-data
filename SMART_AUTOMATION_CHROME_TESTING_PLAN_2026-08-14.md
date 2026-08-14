# Smart Automation — Chrome Testing Plan

**Date:** 2026-08-14  
**Companion build plan:** `SMART_AUTOMATION_SYSTEM_PLAN_2026-08-14.md`  
**Status:** Testing plan only. **No product source is changed by this file.**  
**Browser:** real Google Chrome (headed). Playwright, if used, must set `channel: "chrome"` — not Chromium. Also walk the same cases by hand in Chrome.  
**Where:** local app first  
**Frontend:** `http://localhost:5173`  
**Backend:** `http://localhost:8000`  
**Account:** platform admin `shyna.elene@minafter.com` / `QWE!@#asd234`

This plan is how we **prove** the automation stack, **find** errors in Chrome, and **re-test after each fix**. It covers what already ships today (Wave 0) and what each later phase (S0–S8) must pass before it is done.

---

## 0. Read this first — mail can leave the building

The local API talks to the **shared remote database**, not a private sandbox. Several buttons send **real email** through whatever mailbox is connected on this tenant.

| Control | Blast radius | Allowed in Wave 0 local Chrome? |
| --- | --- | --- |
| Settings → AI & Automation → **Preview next tick** | This tenant, read-only | **Yes — prefer this** |
| **Draft due emails** / Run now `jobs: ["drafts"]` | This tenant; creates drafts; does not send | Yes |
| **Run AI tasks (sends deal email)** | This tenant; **sends Class A library mail** to captured parties | **Only** if every party on the test deal is a mailbox we control |
| **Send** / **Send all ready** | Named recipients on screen | Only to mailboxes we control |
| Platform `POST /internal/schedules/tick` | **Every tenant with an active user** | **Do not fire from local Chrome testing.** Use tenant Run now / Preview instead |

**Rule:** before any send path, open the deal’s **People** tab and confirm buyer, seller, co-op, lender, and title emails are tester-owned (or empty, which should *surface*, not send). If a live third-party address is on the file, **do not** Run AI tasks and **do not** Send.

If Preview says `would_send > 0` to an address you do not control: **Got it** / cancel. Do not confirm Run.

---

## 1. Purpose and how this plan is used

### 1.1 What “done” means

A phase of `SMART_AUTOMATION_SYSTEM_PLAN_2026-08-14.md` is not done when the code is written. It is done when:

1. Every case in that phase’s table in **§7** is **Pass** or an explicit **Skip** with a reason.  
2. Chrome at **1440px** and **390px** has **no page errors** and **no red console errors** on the surfaces touched.  
3. Failures were written down, fixed, and **re-run in Chrome** (the loop in §4).  
4. No case required reading CloudWatch or guessing; the product showed the outcome.

### 1.2 What we are testing

Not “does the page load.” Whether automation **behaves like a transaction coordinator**:

- The right letters go out **once**, to the **right people**, or they wait.  
- Manual really stops sends.  
- Needs You is the residual, and its counts match the deal.  
- Money/wire mail is never a Ready draft.  
- Dates and waives never apply themselves.  
- When the AI stops, the on-screen reason is true and the recovery control exists.

### 1.3 How to report a failure

For every Fail, record:

- **Case ID** (e.g. `W0-P-04`)  
- **URL** (copy from the address bar)  
- **Deal address**  
- **What you clicked**  
- **Expected** vs **what happened**  
- **Screenshot** (desktop and 390px if layout)  
- **Console** (any red line)

Do not diagnose in the report. “This felt wrong” is enough. Severity: **Blocker** (wrong send, wrong recipient, silent skip of a real letter), **High** (counts lie, recovery dead, doctrine copy contradicts send), **Medium** (layout, missing evidence, slow), **Low** (copy polish).

---

## 2. Environment and accounts

### 2.1 Local (this round)

| | |
| --- | --- |
| App | `http://localhost:5173` |
| API | `http://localhost:8000` (frontend `.env` `VITE_API_BASE_URL`) |
| Login | `/login` |
| Email | `shyna.elene@minafter.com` |
| Password | `QWE!@#asd234` |
| Role | Admin / platform admin |

Start both servers before Chrome. Confirm `http://localhost:8000/api/health` returns ok.

This credential does **not** log into staging or production (those are different identity stores). Stage/prod Chrome is a later pass with those environments’ admins; do not mix results.

### 2.2 Chrome setup

1. Use **Google Chrome**, not Edge-as-default, not Playwright Chromium.  
2. Window **1440×900** for desktop cases; DevTools device **390×844** for every `…-M` case.  
3. Open DevTools → **Console**. Keep it open. A red exception on the page under test is a Fail unless it is a documented third-party extension.  
4. Allow pop-ups (Gmail connect).  
5. Do not run two headed Chrome logins as the same user in parallel (session fights).

If automating: Playwright `chromium.launch({ channel: "chrome", headless: false })` against `http://localhost:5173`. Hand-walk remains the source of truth for “felt wrong.”

### 2.3 Surfaces (click path and URL)

| Surface | Click path | URL |
| --- | --- | --- |
| Sign in | — | `/login` |
| Needs You | Left sidebar → Workflow → **Needs You** | `/needs-you` |
| AI & Automation | Name menu → Settings → **AI & Automation** | `/admin/confidence` |
| Email & E-signature | Settings → **Email & E-signature** | `/settings/connections` |
| AI Email Review | Workflow → **AI Emails** (or similar) | `/ai-emails` |
| Active Transactions | Deals → **Active Transactions** | `/transactions` or `/transactions/active` |
| Deal workspace | Open a deal | `/transactions/<id>` |
| Deal Tasks / Email / People / Activity | Workspace tabs | same URL, tab |
| Notifications (digest) | Settings → **Notifications** | settings hub |
| Task templates | Settings → task playbook | `/admin/task-templates` |
| New deal | **+ New Transaction** | `/transactions/new` |

### 2.4 Test deals (create or reuse)

Use **dedicated** deals whose party emails we control. Do not Run AI tasks on the existing book (Harness / Livefire / Koenig, etc.) until People is audited.

Suggested naming so artifacts stay findable:

| Deal | Posture | Parties | Purpose |
| --- | --- | --- | --- |
| `QA Auto Manual Lane` | Manual | Tester inboxes | Class A must **not** send |
| `QA Auto Assisted Lane` | Assisted (or inherit Assisted workspace) | Tester inboxes | Class A **may** send on create |
| `QA Auto No Mailbox Lane` | Assisted | Tester inboxes, mailbox disconnected | Must surface, not send |
| `QA Auto No Recipient Lane` | Assisted | Buyer with **no** email | `no_recipient` / Give-back |
| `QA Auto Autopilot Lane` | Autopilot | Tester inboxes | Ready drafts; Send still a tap |

Point every party at mailboxes the tester owns (Gmail/Outlook used for QA). Never use `tori.banks@minafter.com`-class addresses from live fixtures for send tests.

Packet: a signed purchase agreement from `velvet-elves-data/testing_docs/` when the case needs Order Title / loan officer (those require the contract attached).

---

## 3. Doctrine testers must hold in their head

Until S1 rewrites the captions, **the UI and the engine may disagree**. Grade **behavior** against this table, and file copy mismatches as High (doctrine), not as “the send is a bug.”

| Class | What | Machine send? |
| --- | --- | --- |
| **A** | Buyer/seller/co-op/loan welcomes; Order Title; Confirm Title Order; Pending MLS reminder (to the agent) | **Yes** on Assisted/Autopilot, Active deal, captured email, connected mailbox, not >30 days overdue |
| **B** | Due-task drafts, inbound replies, signature-chase, vendor replies | **Never** until you tap Send (Autopilot only marks Ready) |
| **C** | Delayed auto-send with countdown | **Not built** — any such control is a Fail until Jake approves S7 |

**Manual** is a kill-switch for Class A.  
**Dates / waives / legal** never apply themselves.  
**ToBeAutomated** tasks are **not** Class A until a named playbook promotion (S6, Jake).

The hourly **platform** tick is on in staging/production as of 2026-08-14. **Local** has no EventBridge; the Needs You banner may still say the scheduler is stale. That is **expected locally** unless `scripts/run_schedules.py` is running — and that script is cross-tenant, so **do not start it** for this Chrome plan.

---

## 4. Iterative loop (mandatory)

Do not “test everything once.” Each wave:

```
A. Run the wave’s Chrome cases (desktop, then 390px where marked)
B. Log Fail/Skip in the results table (§10)
C. Fix product code (separate change; not this document)
D. Re-run only:
   - every Fail from that wave
   - the smoke set W0-S-*
   - any case whose surface was touched
E. Repeat until the wave is all Pass/Skip
F. Then start the next wave
```

**Stop the wave** if a Blocker send bug appears (wrong recipient, duplicate welcome, send on Manual). Do not continue creating deals until that is fixed and W0-S is green.

**This document’s job in the current session is the plan only.** Execution in Chrome and code fixes come after this file exists.

Suggested artifact folder when a wave is run:

`velvet-elves-data/smart_automation_qa/artifacts_YYYY-MM-DD_<wave>/`

Include: `findings.json`, `desktop.txt` / `mobile_390.txt` dumps, screenshots, and the filled results table.

---

## 5. Shared pass/fail rules (every case)

A case **Fails** if any of these are true:

- Wrong email left a mailbox, or an email went to a party not on People.  
- A Class B draft sent without Send.  
- Class A sent on **Manual**.  
- A second welcome/title-order for the same task.  
- Needs You empty state while items exist (or the reverse after load).  
- Nested `role="button"` / unlabelled icon-only control under 40px.  
- Type under 12px on the surface under test.  
- Uncaught page error or console exception.  
- Recovery copy names a button that is not on the card.  
- Date cascade or waive applied with no confirm/preview.

A case **Passes** only if Expected in the table is met **and** none of the above.

**Skip** only when: the phase is not built yet (mark `N/A until Sx`), or Preview/send is blocked by §0 safety (write the address). Do not Skip because the queue is slow.

---

## 6. Wave 0 — baseline of what ships today

Run this entire wave in Chrome **before** implementing S0–S8. It is the regression floor. Failures here are current-product bugs; they are in scope to fix during iterative testing.

Smoke **W0-S-*** is re-run after every later fix.

### 6.1 Smoke (W0-S)

| ID | Steps | Expected |
| --- | --- | --- |
| W0-S-01 | Sign in as `shyna.elene@minafter.com`. Land on an admin dashboard. | Session holds; no console error. |
| W0-S-02 | Open `/needs-you`. Wait until the header pill is not “Loading”. | Pill shows `N waiting`; empty state only if N=0. Scheduler banner if unhealthy. |
| W0-S-03 | Open `/admin/confidence`. | Posture cards + status chip + Preview / Draft due emails / Run AI tasks / digest. |
| W0-S-04 | Open `/settings/connections`. | Gmail/Outlook/iCloud state visible; Test connection does not send mail. |
| W0-S-05 | Open any Active deal. | Posture chip Manual/Assisted/Autopilot; Tasks / Email / People / Activity tabs. |
| W0-S-06 | 390px: `/needs-you`. | No horizontal overflow; Export CSV and primary actions named (`aria-label` ok). |

### 6.2 Posture and kill-switch (W0-P)

Use `QA Auto Manual Lane` / `QA Auto Assisted Lane`. Prefer **inherit** vs deal pin as the UI allows.

| ID | Steps | Expected |
| --- | --- | --- |
| W0-P-01 | Workspace default on `/admin/confidence`: note current value. Do not save a change unless you will restore it. | Cards Manual / Assisted / Autopilot; Save only when dirty. |
| W0-P-02 | Open a deal → posture menu → **Manual**. | Chip Manual; caption does not promise unattended send. |
| W0-P-03 | Same deal → **Assisted**. | Chip Assisted. |
| W0-P-04 | Same deal → **Autopilot**. | Chip Autopilot; Ready is described as a label, not a send. |
| W0-P-05 | If **Use workspace default** is shown, click it. | Source is tenant default; orange “custom” dot clears. |
| W0-P-06 | Manual deal: Ask AI / agent to advance a task that would auto-apply on Assisted. | Proposal waits; does **not** apply itself. |
| W0-P-07 | Manual deal with Automated welcome tasks still open. **Do not** Run AI tasks. Check Tasks: AI-owned group. | Tasks parked (`posture_manual` or equivalent); **no** new Sent mail to parties. |

### 6.3 Class A library send (W0-A) — safety-gated

Only on `QA Auto Assisted Lane` with **tester-owned** party emails and a **connected** mailbox.

| ID | Steps | Expected |
| --- | --- | --- |
| W0-A-01 | Create deal via wizard with signed packet; parties = tester inboxes; posture Assisted or Autopilot. Wait for generation. | Buyer/seller/co-op welcomes **may** send and complete. Loan officer / Order Title wait if contract attachments required and missing. |
| W0-A-02 | Open Sent (mailbox or deal Email tab). | At most **one** of each welcome; body is the library letter (address + closing date); **no** “written by AI” disclaimer. |
| W0-A-03 | `/admin/confidence` → **Preview next tick**. | Dialog: would_send count; redacted recipients; **Got it** sends nothing. |
| W0-A-04 | If would_send = 0: **Run AI tasks** after confirm. | Completes/surfaces; no surprise third-party send. |
| W0-A-05 | If would_send ≥ 1 to our inboxes: confirm **or** cancel once. If cancel: no send. If confirm: only listed recipients. | Matches preview. |
| W0-A-06 | Create a **second** deal or re-run Preview on the first. | No second welcome for an already-sent task (idempotency). If a duplicate sends, **Blocker**. |
| W0-A-07 | Disconnect Gmail/Outlook on `/settings/connections` (or use `QA Auto No Mailbox Lane`). Preview / create. | Surface `mailbox_reconnect` / no provider; **no** send. Reconnect after the case. |
| W0-A-08 | `QA Auto No Recipient Lane`: buyer has no email. | Welcome surfaces `no_recipient` (Needs You kind **task**); no send to a guessed address. |
| W0-A-09 | Review Documentation on a signed packet. | Completes or surfaces; if signatures missing, a **draft** chase exists — nothing sent until Send. |

### 6.4 Class B drafts and Send (W0-B)

| ID | Steps | Expected |
| --- | --- | --- |
| W0-B-01 | `/admin/confidence` → **Draft due emails**. | Toast: prepared N drafts; **nothing sent**. |
| W0-B-02 | `/needs-you` and `/ai-emails`. | New drafts in To review and/or Ready (Autopilot). |
| W0-B-03 | Expand a **draft** row. | Preview, recipient, deal link; **Send** absent or disabled unless Ready. Review opens `/ai-emails`. |
| W0-B-04 | Autopilot deal: a sweep draft marked Ready. **Do not Send yet.** | Status Ready; mail not in the party inbox. |
| W0-B-05 | **Send** one Ready draft to a tester inbox (confirm if shown). | One message; deal Email = Sent; Needs You count drops by 1. |
| W0-B-06 | **Send all ready** with 0 ready. | Disabled or confirm “0”; no send. |
| W0-B-07 | **Send all ready** with ≥1 ready to tester inboxes. Cancel confirm. | No send. Then confirm: recipients listed match People. |
| W0-B-08 | Compose/send a draft whose body says a file is attached. | The send includes the file **or** the prose is rewritten; never “Attached is X” with nothing. |

### 6.5 Needs You queue (W0-N)

Regression against `NEEDS_YOU_CHROME_QA_2026-08-13.md` (already fixed once — do not regress).

| ID | Steps | Expected |
| --- | --- | --- |
| W0-N-01 | Load `/needs-you`. | Loading pill immediately; then `N waiting · R ready to send`. |
| W0-N-02 | Kind tiles: ready / approve / draft / task (and coverage if any). | Filter works; URL `?kind=`. Refresh keeps kind. |
| W0-N-03 | Search. | `aria-label` Search items; URL `?q=`; empty state if no match. |
| W0-N-04 | Expand a row (`?item=`). Refresh. | Same card open. |
| W0-N-05 | `?tx=<deal-id>`. | One deal; clear chip. |
| W0-N-06 | Export CSV. | File for **visible** rows; named at 390px. |
| W0-N-07 | Approve all safe: **cancel** confirm. | No applies. |
| W0-N-08 | Give-back on a blocked AI task (if shown). | Flag clears or task leaves the blocked set; no send by itself. |
| W0-N-09 | Handle → deal Tasks; Review → AI Emails; Open deal. | Right destination. |
| W0-N-10 | Sidebar badge vs header N. | Equal after load. |
| W0-N-11 | Compare N to each deal’s header “X needs you” summed. | **Today they may disagree (A-08).** Record the two numbers. Fail only if a deal’s chip is 0 while that deal has rows in the queue, or the reverse. After S1, they **must** match — see S1-N-01. |
| W0-N-12 | 390px walk of W0-N-01, 06, 08. | 40px hits; no overflow. |

### 6.6 Scheduler honesty (W0-H)

| ID | Steps | Expected |
| --- | --- | --- |
| W0-H-01 | `/needs-you` and `/admin/confidence`. | If `scheduler_healthy` is false: amber **Automation has stopped** (or never-run wording). If true: green / active. |
| W0-H-02 | Needs You **Open AI & Automation**. | Lands on `/admin/confidence`. **Run now is not on Needs You** (by design). |
| W0-H-03 | Note **last tick** vs **last draft sweep**. | Two clocks; Run now updates sweep, not necessarily the platform tick. |
| W0-H-04 | Local: banner may say many days stale. | **Not a Fail** unless EventBridge/`run_schedules.py` is supposed to be running locally. Do not start the cross-tenant loop to green the chip. |

### 6.7 Inbound and money (W0-I)

Use **Test inbound** on the deal Email/Communications panel if present; otherwise send a real Gmail to the connected mailbox from a **second** tester address (not the same as the sending mailbox — self-mail proves little).

| ID | Steps | Expected |
| --- | --- | --- |
| W0-I-01 | Inbound: “When is the closing date for \<property\>?” | Kept; a factual draft **or** Ready; does not send. |
| W0-I-02 | Inbound: “The title commitment is ready.” (statement, not a question) | **Kept** on the deal or in Email. Must not vanish. Draft optional. |
| W0-I-03 | Inbound: “Please send the **wire instructions** for \<property\>.” | **No reply draft.** Not Ready. Prefer a money/held treatment. |
| W0-I-04 | Inbound: “Please send **banking details** for closing.” | **Record actual behavior.** Today regex may miss this (known gap, S4). Fail as High if a **Ready** draft appears; Fail as Blocker if it **sends**. |
| W0-I-05 | Newsletter-like body with a street in a footer, unknown sender. | Prefer no deal draft. Record if a junk draft appears (S5). |

### 6.8 Boundaries the AI must not cross (W0-X)

| ID | Steps | Expected |
| --- | --- | --- |
| W0-X-01 | Ask AI / agent to change closing date. | Preview; nothing moves until you confirm. |
| W0-X-02 | Waive a checklist item from automation/agent. | Reason required; not in Approve all safe. |
| W0-X-03 | Agent proposals never include “send email” as auto-apply. | Draft-only email actions. |
| W0-X-04 | Settings digest: leave **off**. Run now digest (you only) if offered. | No tenant-wide blast; posture change does not flip digest. |

### 6.9 Activity and credit (W0-Y)

| ID | Steps | Expected |
| --- | --- | --- |
| W0-Y-01 | After a Class A welcome (W0-A-01), deal Activity → Automation lens. | A row for the send or completion. **Today this may be empty (A-07/A-10).** Record as Fail High if empty — in scope for S1, still log it in Wave 0. |
| W0-Y-02 | Header “handled today”. | Should not stay 0 if Class A completed today. Record actual. |
| W0-Y-03 | Undo an auto-applied **agent** action (not a sent email). | Reverts; toast. |

### 6.10 Wave 0 mobile extras (W0-M)

| ID | Steps | Expected |
| --- | --- | --- |
| W0-M-01 | `/admin/confidence` at 390px. | Preview and Draft buttons usable; no overlap. |
| W0-M-02 | Deal posture menu at 390px. | All three postures + inherit reachable. |
| W0-M-03 | `/ai-emails` at 390px. | List + detail usable; Send not accidental. |

---

## 7. Later waves — required when that phase ships

Mark **N/A until Sx** until the build plan phase is in the local tree. When it ships, the wave becomes blocking. Re-run W0-S after each.

### 7.1 S0 — Live tick is safe and visible

| ID | Steps | Expected |
| --- | --- | --- |
| S0-01 | `/admin/confidence`: last tick **counts** (tenants, sent, surfaced, errors). | Visible without CloudWatch. |
| S0-02 | If last tick `ai_tasks_completed > 0`. | Amber honesty: “The hourly run sent N Automated emails.” |
| S0-03 | Preview on this environment (including prod when that pass runs). | **200**, not 404. |
| S0-04 | Duplicate Class A: Preview + create on a deal that already sent welcomes. | would_send does not include already-sent tasks; no second send. |
| S0-05 | (Ops, not Chrome) EventBridge retry = 0; tick timeout does not double-fire. | Confirm in AWS or by last_tick counts not doubling in \<2 min. |

### 7.2 S1 — One doctrine, one count

| ID | Steps | Expected |
| --- | --- | --- |
| S1-01 | Read Assisted and Autopilot captions and the can/cannot panel. | Explicit: library welcomes/title-order **may** send alone; **every other** email waits for Send. No blanket “nothing sends without a tap” unless scoped to Class B. |
| S1-02 | Needs You briefing when scheduler healthy and items exist. | Does not claim “everything routine already ran” if blocked tasks remain. |
| S1-03 | Sum of deal header `needs you` vs Needs You N (same user scope). | **Equal** (closes A-08). |
| S1-04 | After Class A complete: handled today and Automation lens. | Non-zero / visible row (closes A-10). |
| S1-05 | Pin a deal, then inherit workspace default. | Follows tenant default again; changing workspace later applies. |

### 7.3 S2 — Recovery loop

| ID | Steps | Expected |
| --- | --- | --- |
| S2-01 | `no_recipient` welcome: add buyer email on People. **Do not** Give-back. | Next per-deal run or documented Try-now sends or surfaces a **new** honest reason. |
| S2-02 | `missing_document` Order Title: upload purchase agreement. | Retries without Give-back. |
| S2-03 | `stale_overdue`: change due date to today/future. | Copy promised re-arm; task is retryable (closes A-03). |
| S2-04 | `execution_error`: reason names a cause class; Give-back works; Try-now if shown. | No “handle it” with no button. |
| S2-05 | Reconnect mailbox after `mailbox_reconnect_required`. | Next run retries. |
| S2-06 | Admin Try-now on one deal (if shipped). | Does **not** tick all tenants. |

### 7.4 S3 — Morning Queue and satisfaction

| ID | Steps | Expected |
| --- | --- | --- |
| S3-01 | Autopilot deal, Draft due emails / overnight equivalent. | Needs You populated; Class B not sent. |
| S3-02 | Empty Needs You + healthy scheduler. | “Overnight prep ran. Nothing needs you.” only if both true. |
| S3-03 | Deal that already sent Order Title; task still open. | Second tick does **not** send again (`noop_satisfied`). |
| S3-04 | Deal card / header one-liner. | Same numbers as Needs You for that `?tx=`. |

### 7.5 S4 — Content / money

| ID | Steps | Expected |
| --- | --- | --- |
| S4-01 | Inbound “please send the wire instructions.” | No draft; money-held visible. |
| S4-02 | Inbound “please send banking details for closing.” | Same as S4-01 (v2). |
| S4-03 | Draft body “Attached is the inspection report” with no file. | Cannot Send that way; honesty rewrite or attach. |
| S4-04 | Policy tags on a draft (`library-send` / `needs-review` / `money-held`). | Ready never appears on money-held. |
| S4-05 | Sign-off is the **agent** name until Jake answers J6. | Not “Aime” unless J6 = yes and S4 implemented that way. |

### 7.6 S5 — Inbound file clerk

| ID | Steps | Expected |
| --- | --- | --- |
| S5-01 | Inbound pane shows **why this deal**. | One evidence line. |
| S5-02 | Refile to another deal. | Draft moves or is discarded; old deal clean. |
| S5-03 | Filtered-mail tab; Undo filter. | Envelope only; one tap restores. |
| S5-04 | Unknown-sender newsletter with street in footer. | No junk draft. |
| S5-05 | Unmatched but relevant mail. | Visible to match; not dropped. |

### 7.7 S6 — ToBeAutomated promotion (blocked on Jake J1–J5, J7)

| ID | Steps | Expected |
| --- | --- | --- |
| S6-01 | Honesty panel lists ToBeAutomated templates as **not** AI-sent. | Matches open task labels. |
| S6-02 | Template marked Automated **without** playbook key. | Surfaces unknown playbook; **no** send. |
| S6-03 | After a **single** approved promotion on stage. | Only that letter is Class A; others unchanged. |

Do not run a “promote all 35” test.

### 7.8 S7 — Delayed auto-send (blocked on Jake J11)

| ID | Steps | Expected |
| --- | --- | --- |
| S7-01 | Feature **off** by default. | No countdown on drafts. |
| S7-02 | If Jake enabled: factual draft shows countdown; **Hold**. | Returns to pending; no send. |
| S7-03 | Let one window elapse on a **tester** recipient. | Send audited as auto-sent; Hold still worked on a sibling. |
| S7-04 | Money kind never enters the window. | — |

Until J11 is yes, any countdown UI is a **Fail**.

### 7.9 S8 — Per-tenant tick

| ID | Steps | Expected |
| --- | --- | --- |
| S8-01 | New tenant Manual, no mailbox. | Zero Class A. |
| S8-02 | Workspace setting “Hourly automation is on” + doctrine sentence. | Visible to Admin. |
| S8-03 | (Platform) tenant table: last tick, mail health, posture. | Readable without AWS. |

---

## 8. Accessibility and quality bar (every wave)

Walk the surface just changed:

| Check | Bar |
| --- | --- |
| Hit target | Primary actions ≥ 40×40 |
| Type | ≥ 12px in `main` |
| Names | Icon-only controls have accessible names (Export, Send, Give-back) |
| Nested buttons | None |
| Keyboard | Expand/collapse and Send reachable |
| 390px | No horizontal overflow |
| Console | No exceptions |
| Loading | Never show “nothing needs you” while the request is in flight |
| Confirm | Approve all / Send all / Run AI tasks always confirm when they can mutate or send |

---

## 9. Unit/API floor (not a substitute for Chrome)

Run when the wave’s code changes. Failures here stop Chrome for that wave.

| Suite | Path |
| --- | --- |
| Executor / playbook | `velvet-elves-backend/app/tests/test_ai_task_executor.py` |
| Posture | `app/tests/test_automation_posture.py` |
| Auto-draft sweep | `app/tests/test_auto_draft_sweep.py` |
| Tick / digest | `app/tests/test_schedule_tick_and_digest.py` |
| Needs You / batch | `test_automation_posture.py` needs-you cases |
| Frontend cluster | `velvet-elves-frontend` `needsYouCluster` tests |

Chrome is still required: API green + UI lie is a Fail.

---

## 10. Results log (copy per wave)

```
Wave: W0 | Date: YYYY-MM-DD | Chrome version: | Tester:
App: http://localhost:5173 | User: shyna.elene@minafter.com

ID       Result (Pass/Fail/Skip)   Notes / deal address
W0-S-01  Pass
…
Blockers: n   High: n   Medium: n   Low: n
Retest of: (IDs)
Console errors: none / list
```

Promote a wave to **closed** only when Fails = 0 and Skips are justified.

---

## 11. Decisions and questions for Jake

These are recorded here so testing and build do not invent answers. Until he replies, testers **grade against the “Until then” column**, and engineers **do not implement the other branch**.

### 11.1 Blocking product decisions

| ID | Question | Why it changes the test | Until then | Recommendation |
| --- | --- | --- | --- | --- |
| **J1** | Task 235 “Buyer’s Inspection Response Due” does not exist. Did you mean 240, 245, 230, or a new task? | Attachment and automation tests cannot target a missing ID. | No inspection-response Class A test. | 240 or 245 |
| **J2** | Tasks 453 and 455 are in the attachment sheet but not in the system. Add them? | Cannot test attachments for missing tasks. | Skip those IDs. | Yes, add both |
| **J3** | 460/470 are “Request Referrals” in product, “Request Testimonials” on the sheet. Rename? | Testers will look up the wrong name. | Use **product** names in Chrome. | Rename to Testimonials |
| **J4** | 32 tasks have no attachment rule (Appendix A of `EMAIL_GUIDELINE_QUESTIONS_FOR_JAKE.md`). Confirm the pre-filled list? | W0-B-08 / S4-03 cannot be complete for those tasks. | Only test tasks that already have sheet rules. | Confirm the list |
| **J5** | Four tasks are **phone calls** in the system but emails on the sheet. Keep the call and add email? | Automation might try to email a call task. | Class A/B tests ignore those four until answered. | Keep call, add email |
| **J6** | Should **auto-sent** (Class A) letters be signed **Aime** or the **agent**? | W0-A-02 / S4-05 expected sign-off. | Expect the **agent’s** name/signature. Fail if Aime appears. | Guideline: Aime |
| **J7** | Inspection: sheet says automate; guideline says always review. | S6/S7 eligibility; Ready vs pending. | Inspection stays **human / Class B**. Ready on an inspection **response** is a Fail. | Automate **reminders** only |
| **J11** | Approve **Phase 7** delayed auto-send (countdown + Hold) for factual / document-delivery only? | S7 cases. | **No** countdown UI. Any unattended Class C send is a Blocker. | Defer until after S0–S4 |
| **J12** | New production workspaces: hourly Class A **off** until Assisted + healthy mailbox (S8)? | New-tenant Chrome on prod. | Recommend testers assume **yes**; flag if a brand-new tenant sends welcomes with no mailbox. | Yes |

### 11.2 Non-blocking (still needed)

| ID | Question | Until then |
| --- | --- | --- |
| **J8** | Each task needs an exact “how to reply” line on the sheet? | Auto-drafts use the task description as intent; note awkward copy, don’t Fail. |
| **J9** | Writing style per **agent** or per **brokerage**? | Per-user signature/tone as built. |
| **J10** | Naming: “Autopilot” is intake fast-path, deal posture, and (maybe) full-send. Rename? | Keep current labels in tests; file confusion as Low unless a tester cannot tell intake vs deal posture. |

### 11.3 Questions this testing plan adds

These are not in the August 6 email list; they appeared while writing the build plan and this Chrome plan.

| ID | Question | Why |
| --- | --- | --- |
| **J13** | Confirm Class A stays the **closed** named set (welcomes, title order/confirm, pending reminder) and we will **not** grow it without a written yes per template. | Testers need a freeze list. A surprise seventh unattended letter is a Blocker. |
| **J14** | For local/demo tenants that still have third-party addresses on old deals: is it acceptable that Preview/Run AI tasks is **disabled by policy** for testers, or should we scrub those People emails? | Wave 0 cannot safely exercise Class A on the current 6-deal book. |
| **J15** | Staging workspace default was **Autopilot** on 2026-08-14. Should every environment start **Manual** (code default) and Autopilot be opt-in only? | Changes W0-P-01 expected default; Autopilot-as-default increases Ready drafts and Class A on create. |
| **J16** | After a Class A send, should the deal **progress %** count that AI task, or only the Automation lens / handled-today? | W0-Y / S1-04. Today progress often ignores Automated rows on purpose. |
| **J17** | May testers use **Run now → AI tasks** on stage/prod at all, or only Preview + create-deal welcomes? | Stage/prod ticks already hourly; an extra Run now can still send. |

Please answer J6, J7, J11, J13, and J15 first — they change what Chrome grades as Pass this month. J1–J5 block S6 only.

Full attachment-sheet detail remains in `EMAIL_GUIDELINE_QUESTIONS_FOR_JAKE.md` (Appendix A). Do not duplicate the 32-row table here; Jake can answer in that file or this one.

---

## 12. Out of scope for this plan

- SMS, Follow Up Boss, AI Coach.  
- Firing `POST /internal/schedules/tick` from the local machine.  
- Promoting ToBeAutomated in bulk.  
- Recording the Google OAuth demo video (`GOOGLE_DEMO_VIDEO_REQUIREMENTS.md`).  
- Changing product code in the same step as **writing** this plan.

Wizard intake is in scope only as **create a deal to feed automation**. Extraction accuracy has its own guides.

---

## 13. Suggested first execution order (when Chrome testing starts)

1. W0-S (smoke).  
2. W0-H (honesty; no send).  
3. W0-P (posture; no send).  
4. W0-N (queue; no send except if you already have Ready to tester inboxes).  
5. W0-B-01 (drafts only).  
6. People audit → only then W0-A on **new** QA deals.  
7. W0-I with Test inbound or a second mailbox.  
8. W0-X, W0-Y, W0-M.  
9. Fill §10. Fix Blockers/High. Re-run W0-S + failed IDs.  
10. When S0–S1 land, run §7.1–7.2 the same way.

---

*Companion: `SMART_AUTOMATION_SYSTEM_PLAN_2026-08-14.md`. Wave 0 grades today’s product; S0–S8 tables become required as those phases ship. Jake’s answers in §11 decide Class A signature, inspection, delayed auto-send, and default posture — not the tester.*
