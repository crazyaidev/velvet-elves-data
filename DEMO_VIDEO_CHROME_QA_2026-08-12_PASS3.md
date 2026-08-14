# Demo video production QA — Chrome pass 3 (2026-08-12)

**Date:** 2026-08-12 (evening re-test)  
**Environment:** https://app.velvetelves.com (frontend + backend deploy live)  
**Account:** `crazyaidev20500519@gmail.com` (Admin OWNER)  
**Guide:** `GOOGLE_DEMO_VIDEO_REQUIREMENTS.md`  
**Method:** Real Google Chrome (Playwright headed, `channel: "chrome"`)  
**Flagship deal:** https://app.velvetelves.com/transactions/e17bca76-8d70-44da-be4b-f6ace2367ff6  

Inbound test mail (sent by tester):

- **From:** james.l.selman13@gmail.com  
- **To:** crazyaidev20500519@gmail.com  
- **Subject:** Question about 1842 Willowbrook Lane closing  

Artifacts: `velvet-elves-data/demo_video_testing/artifacts_2026-08-12_pass3/` and `artifacts_2026-08-12_pass3b/`.

**Scope change vs pass 2:** Gmail/Calendar already being connected is **not** a QA blocker. Consent-screen filming is a camera staging choice, not a product fail.

---

## Executive summary

The deployed Ask AI fix and the inbound Willowbrook Gmail both work on production. Scene 6 (`gmail.readonly`) is **ready to film**. Scene 4’s natural “Propose adding… due August 18, 2026” prompt now proposes and lands a task.

Production is still **not record-ready for Part 1**, because the book of business is a single Unhealthy deal.

| Area | Verdict |
| --- | --- |
| Ask AI spoken-date / “Propose adding…” (deployed) | **Pass** — proposed and created `Confirm title commitment reviewed` due Aug 18, 2026 |
| Scene 4 Approve click | **Warn for camera** — tenant auto-apply (`Ran automatically · your rule`) skipped the Approve button |
| Seller on Contacts | **Pass** — Harper Devlin is on file |
| Scene 6 inbound match | **Pass** — Inbox, deal match, history, AI category, reply draft |
| Outbox draft + Approve & send | **Pass** (send left unsent) |
| Gmail / Calendar connected | **Info** — not a blocker |
| Pipeline density | **Fail for recording** — 1 active deal, Unhealthy, 7 overdue |

**Bottom line:** Film Scene 6 on Willowbrook now. Do not hit Record for the full Google video until Active Transactions has several real-looking deals and Willowbrook is not an overdue-only Unhealthy file. Turn off Ask AI auto-apply before Scene 4 so the camera can show Approve.

---

## What was verified

### Deployed Ask AI fix (Scene 4)

Prompt used on the Willowbrook deal:

`Propose adding a task named Confirm title commitment reviewed due August 18, 2026`

Result:

- Proposed action: **Add task: Confirm title commitment reviewed** due 2026-08-18  
- Applied immediately: **Ran automatically · your rule**  
- Task is on the Tasks tab, **Pending**, due **Aug 18, 2026** (alongside the earlier earnest-money task)

The previous ISO-only workaround is no longer required.

**Camera note:** Because auto-apply fired, there was no Approve button to click. Scene 4 narration (“the assistant proposes, and a person approves every change”) needs the auto-apply rule off for the take.

### Contacts

Harper Devlin is visible under **Seller**. The earlier “No seller on file” state is gone. Cache-invalidation after Add Contact was not re-exercised (seller already present).

### Scene 6 — `gmail.readonly` end to end

Intelligence → Email → Inbox (search “Willowbrook”), first refresh:

| Check | Result |
| --- | --- |
| Message present | **James Selman** · ~10m ago · *Question about 1842 Willowbrook Lane closing* |
| Body snippet | Closing date for 1842 Willowbrook Lane, Carmel, IN 46032 (WILLOWBROOK-1842-DEMO); September 25, 2026 |
| Matched deal | **1842 Willowbrook Lane** (not “Not linked”) |
| AI category | **Question** |
| AI follow-through | **Reply ready** |
| Deal Email tab | Inbox badge **1**; Outbox includes AI reply *Re: Question about 1842 Willowbrook Lane closing* to `james.l.selman13@gmail.com` |
| Activity / communications | Inbound logged at 10:55 PM; **Matched by party**; From James Selman · Received · Gmail |
| Communication audit | Inbound body + drafted reply confirming closing **September 25, 2026** (`factual`) |

The older unmatched `auto029269` mail is not in the Willowbrook-filtered Inbox (count **1**). Film Scene 6 with the deal filter / search on Willowbrook.

### Scenes 7–9 (staging)

- Outbox still has Willowbrook drafts, including the new reply to James.  
- **Approve & send** is present; not clicked.  
- In-app Closing Calendar still shows Willowbrook. Gmail remains connected — informational only.

---

## Issues

### Still blocking the full video

#### BUG-001 — Book of business is still one deal (demo-blocking)

- **Severity:** critical (for recording) / data  
- **Details:** Active Transactions = **1 deal**, **$485K**, Overdue **1**. Google’s prior rejection was “thin product.” Scene 6 no longer depends on this; Part 1 still does.  
- **Still needed:** 2–3 more healthy-looking deals at different stages.

#### BUG-004 — Flagship deal is Unhealthy (7 overdue tasks)

- **Severity:** high (Part 1 optics)  
- **Details:** Acceptance Aug 8, 2026; file still shows **Unhealthy**, **7 overdue**, **0% complete**.  
- **Workaround:** complete or reschedule overdue tasks, or add a healthier second deal whose acceptance is today.

### Recording workaround (not a product regression)

#### AUTO-001 — Ask AI auto-applied the proposed task

- **Severity:** medium (Scene 4 camera)  
- **Details:** After the deployed parser proposed the task, the UI showed **Applied / Ran automatically · your rule**. Approve was never shown.  
- **For the video:** disable that auto-apply rule, then re-run a “Propose adding…” prompt so Approve is on camera. The product still applied the change to the deal.

### Closed / verified this pass

- **BUG-002** (natural “Propose adding…” / spoken dates) — **fixed in production**.  
- **BUG-003** seller missing — **seller is on file**.  
- **BUG-006** Scene 6 not run / unmatched inbox — **inbound matched**.  
- Gmail/Calendar already connected — **removed from the block list** (staging note only).

### Not re-tested this pass

- BUG-005 wizard PDF viewer “Preparing viewer…”  
- BUG-007 closed Ask AI `role="dialog"` (deployed; not re-checked in a11y tree)  
- BUG-008 lead-based paint on a 2004 home  
- Live **Approve & send** (left for camera)  
- Live OAuth consent screens (not a QA blocker)

---

## Scene checklist (`GOOGLE_DEMO_VIDEO_REQUIREMENTS.md`)

| Scene | Result | Notes |
| --- | --- | --- |
| 1 Identity (site + privacy) | PASS | Prior pass |
| 2 Sign in + pipeline | FAIL* | *Login OK; still 1 Unhealthy deal |
| 3 Inside a transaction tabs | PASS | Seller now visible on Contacts |
| 4 AI assistant + approve | PASS* | *Spoken-date propose works; auto-apply skipped Approve — turn the rule off for the take |
| 5 Connect Gmail + scopes | INFO | Already connected; not a QA fail. Film Disconnect→Connect only if the video still needs both consent screens |
| 6 `gmail.readonly` E2E | **PASS** | Matched, logged, categorized Question, reply drafted |
| 7 Draft + Edit | PASS | Outbox includes the inbound reply draft |
| 8 `gmail.send` Approve & send | READY / NOT SENT | Button present |
| 9 `calendar.events` | PASS (in-app) | Willowbrook on Closing Calendar; Google already connected |
| 10 Disconnect | INFO | Dialog verified on prior pass; left connected |
| 11 Data handling statement | N/A | Narration only |

---

## Must-do before recording the full video

1. **Seed 2–3 more deals** so Active Transactions is not a one-row book. Keep Willowbrook as the Scene 3 / 6 flagship.  
2. **Clean Unhealthy optics** on Willowbrook (complete/reschedule the 7 overdue tasks).  
3. **Disable Ask AI auto-apply** so Scene 4 shows Propose → Approve → task on the deal.  
4. Film Scene 6 from Intelligence → Email → Inbox (Willowbrook filter): James’s closing question, **1842 Willowbrook Lane**, **Question**, **Reply ready**, then deal Email / communications (**Matched by party**).  
5. Film Scene 7–8 from the staged Outbox reply to James (or the earlier PA-received draft). Always say: **the AI drafts; a person approves**.  
6. Consent screens: optional for this QA; include them on camera if Google still needs both Gmail and Calendar grants plus the unverified-app warning.

---

## Credentials / safety note

Platform admin credentials were used only for this production QA. Prefer rotating or using a dedicated reviewer account for the Google submission thread if this password has been shared broadly.
