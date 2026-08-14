# Demo video production QA — Chrome pass (2026-08-12)

**Date:** 2026-08-12  
**Environment:** https://app.velvetelves.com  
**Account:** `crazyaidev20500519@gmail.com` (Admin OWNER)  
**Guide:** `GOOGLE_DEMO_VIDEO_REQUIREMENTS.md`  
**Method:** Real Google Chrome (Playwright headed, `channel: "chrome"`)  
**Test PDF:** `velvet-elves-data/demo_video_testing/willowbrook_purchase_agreement.pdf` (3 pages)  
**Flagship deal:** https://app.velvetelves.com/transactions/e17bca76-8d70-44da-be4b-f6ace2367ff6  

Contact emails in the PDF (tester-controlled):

| Role on PDF | Name | Email |
| --- | --- | --- |
| Buyer | James L. Selman | james.l.selman13@gmail.com |
| Seller | Harper Devlin | happydev0705@gmail.com |
| Listing agent | Devin Forrester | developer.defi0782@gmail.com |
| Buyer’s agent | Morgan Goto | gotohigher0705@gmail.com |

Artifacts: `velvet-elves-data/demo_video_testing/artifacts_2026-08-12/` and `artifacts_2026-08-12_pass2/`.

---

## Executive summary

Production can support **Part 1 rehearsal** on the new Willowbrook deal, and **Scenes 4, 7, and 8 are now staged** (Ask AI propose → Approve, plus an Outbox draft to `james.l.selman13@gmail.com`). It is **not yet safe to hit Record** for the Google OAuth video.

| Area | Verdict |
| --- | --- |
| Marketing + Privacy (Google user data) | Pass |
| Sign-in | Pass |
| Pipeline density | **Fail for recording** — 1 active deal (book was empty at start) |
| AI wizard create (Willowbrook PDF) | Pass |
| Deal workspace tabs | Pass (Timeline / Tasks / Documents / Compliance / Contacts / Email) |
| Ask AI facts (address, price, closing) | Pass — deal-grounded |
| Ask AI propose → Approve | Pass with ISO-dated prompt; natural “Propose adding… due August 18” failed until a code fix |
| Gmail / Calendar UI | Pass (both already Connected) |
| Outbox draft + Edit + Approve & send button | Pass (send left unsent for the camera) |
| Live OAuth consent + unverified warning | **Not run** (already connected) |
| `gmail.readonly` inbound match (Scene 6) | **Not run** — needs the inbound test email below |

**Bottom line:** Do not record until (1) the pipeline has several real-looking deals, (2) Willowbrook is not an overdue-only “Unhealthy” file, (3) Gmail/Calendar are disconnected and reconnected on camera with a throwaway Google account, and (4) an inbound Gmail mentioning **1842 Willowbrook Lane** is matched in Intelligence → Email.

---

## What was verified in Chrome

### Part 1 — Product

1. **Marketing** `velvetelves.com` and **Privacy** `#google` (“Google user data (Gmail and Calendar)”) — OK.  
2. **Sign-in** → `/dashboard/admin` as Crazyai / Admin OWNER — OK.  
3. **Active Transactions** started at **0 deals** (demo-blocking). After this QA: **1 deal**, **$485K** pipeline.  
4. **AI wizard:** Buyer → upload Willowbrook PDF → Start AI extraction → Contract Details (double-check agreed on 7 fields) → Contacts & Fees → Upload Transaction.  
5. **Created flagship deal:** `1842 Willowbrook Lane, Carmel, IN 46032` — purchase price **$485,000**, closing **Sep 25, 2026** (44 days out), 39 tasks, 19 checklist items, 1 document.  
6. Workspace tabs populated: Overview, Timeline (acceptance Aug 8, inspection Aug 22, closing Sep 25), Tasks, Documents, Compliance, Contacts, Email.  
7. In-app **Closing Calendar** shows Willowbrook on **Aug 8**; **Add my closings** is present (Google Calendar already connected).

### Part 2 / 3 — Google surfaces

| Surface | Route | State |
| --- | --- | --- |
| Email & E-signature | `/settings/connections` | **Gmail Connected** (`crazyaidev20500519@gmail.com`); Outlook also connected; DocuSign not connected |
| Test connection | same | Clickable; no hard failure |
| Disconnect dialog | same | “Disconnect Gmail?” explains inbound sync + send impact; cancelled (kept connected) |
| Intelligence → Email | `/ai-emails` | Inbox has older **Not linked** mail (`auto029269 Automation Test Way`). Outbox has Willowbrook drafts. |
| Closing Calendar | `/calendar` | Connected state (`Calendars` + **Add my closings**) |

Full consent screens, unverified-app warning, inbound match, and live **Approve & send** were **not** executed (would send real mail / require Disconnect + throwaway Google).

---

## Issues

### BUG-001 — Book of business was empty at start of QA (demo-blocking)

- **Severity:** critical (for recording) / data  
- **Details:** Active Transactions showed “No active transactions yet” / 0 deals. Google’s prior rejection was partly “thin product.” One Willowbrook deal is better than zero, but Part 1 still needs **several** deals in different states.  
- **Mitigation done:** created Willowbrook.  
- **Still needed:** 2–3 more healthy-looking deals (different addresses/stages) so the list is not a single Unhealthy file.

### BUG-002 — Ask AI “Propose adding a task named … due August 18, 2026” did not propose an action

- **Severity:** high (Scene 4)  
- **Details:** Deal-scoped facts work (address / $485,000 / 2026-09-25). The natural-language propose prompt was answered as a compliance Q&A about earnest money — **no Proposed action / Approve card**.  
- **Workaround that works in production today:**  
  `Add a task called Confirm earnest money received due 2026-08-18`  
  That produced **✦ Proposed action → Approve**, and the task landed on the deal.  
- **Fix in repo (not yet production):** deterministic intent now accepts “Propose adding…”, “adding”, and spoken dates (`August 18, 2026`).  
- **Files:** `velvet-elves-backend/app/api/v1/transaction_agent.py`, tests in `app/tests/test_transaction_agent.py`.

### BUG-003 — Seller missing after AI extract (and Add seller UI did not refresh)

- **Severity:** high (Scene 3 People/Contacts)  
- **Details:** Contacts showed **No seller on file**. The PDF listed Harper Devlin as seller **and** loan officer on the same Gmail (`happydev0705@gmail.com`); extraction kept her as lender only.  
- **Add seller:** toast “Contact added”, but the Seller group stayed empty until a later navigation. `AddContactModal` only invalidated `['dashboard']`, not `['transaction', 'parties', id]`.  
- **Fix in repo (not yet production):** invalidate the parties query after add.  
- **File:** `velvet-elves-frontend/src/components/active-transactions/AddContactModal.tsx`  
- **Recording workaround:** Add seller with a **unique** email (Gmail plus-address is fine, e.g. `happydev0705+seller@gmail.com`), then refresh if the card does not appear.

### BUG-004 — Flagship deal is Unhealthy (7 overdue tasks)

- **Severity:** high (Part 1 optics)  
- **Details:** Acceptance is **Aug 8, 2026**; several generated tasks fell on Aug 8–11, so the file immediately shows **Unhealthy**, **7 overdue**, **0% complete**. Google reviewers should not see an overdue-only book.  
- **Workaround:** complete or reschedule the overdue tasks before recording, or create a second deal whose acceptance date is **today**.

### BUG-005 — Wizard PDF viewer stuck on “Preparing viewer…” during Contract Details

- **Severity:** medium (Scene 3 “See in Doc”)  
- **Details:** After extraction, the right-hand viewer stayed on “Loading preview…” / “Preparing viewer…” across screenshots. “See in Doc” is the proof that the system read the contract.  
- **Recording workaround:** wait until the PDF pages render before narrating citations; if it never loads, open the file from the Documents tab.

### BUG-006 — Intelligence → Email still has “Not linked” mail

- **Severity:** medium (Scene 6)  
- **Details:** Inbox still shows unmatched `auto029269 Automation Test Way` messages. Scene 6 needs a **new** inbound that matches Willowbrook.  
- **Action:** send the inbound test email in the section below.

### BUG-007 — Closed global AI chat still exposes `role="dialog"`

- **Severity:** low (a11y / automation)  
- **Details:** Closed panel is `inert` (BUG-002 from earlier QA) but still `role="dialog"`, so it remains in the accessibility tree and stole a Compose-modal locator.  
- **Fix in repo (not yet production):** `role` / `aria-label` only while open.  
- **File:** `velvet-elves-frontend/src/components/active-transactions/AIChatPanel.tsx`

### BUG-008 — Lead-based paint checklist item on a 2004 home

- **Severity:** low  
- **Details:** PDF states the home was built in 2004 (no LBP disclosure). Agent pane still flagged **Lead-Based Paint Disclosure** due 2026-08-13. Do not dwell on this in the video.

### Script mismatch (not a product bug)

- Workspace tab is **Contacts**, not “People.”  
- Wizard confirmation header is **Confirm Details**, not “Verification.”

---

## Scene checklist (`GOOGLE_DEMO_VIDEO_REQUIREMENTS.md`)

| Scene | Result | Notes |
| --- | --- | --- |
| 1 Identity (site + privacy) | PASS | Google user-data section present |
| 2 Sign in + pipeline | FAIL* | *Login OK; pipeline was empty, now 1 deal — still too thin |
| 3 Inside a transaction tabs | PASS | Use Willowbrook; tab = Contacts; seller was missing at first |
| 4 AI assistant + approve | PASS* | *Use the ISO-dated “Add a task called … due 2026-08-18” prompt until BUG-002 is deployed |
| 5 Connect Gmail + scopes | UI PASS / OAuth NOT RUN | Already connected — Disconnect→Connect for video |
| 6 `gmail.readonly` E2E | NOT RUN | Send the inbound email below, then show Inbox match |
| 7 Draft + Edit | PASS | Outbox draft to James; Edit works; “Nothing sends until you approve it” |
| 8 `gmail.send` Approve & send | READY / NOT SENT | Button present; left unsent for the camera |
| 9 `calendar.events` | UI PASS / OAuth NOT RUN | In-app calendar shows the deal; Google already connected |
| 10 Disconnect | UI PASS | Dialog verified; left connected |
| 11 Data handling statement | N/A | Narration only |

---

## Staged Outbox draft (Scene 7–8)

Ready at **Intelligence → Email → Outbox**, linked to Willowbrook:

- **To:** james.l.selman13@gmail.com  
- **Cc:** crazyaidev20500519@gmail.com  
- **Subject:** Received signed purchase agreement for 1842 Willowbrook Lane  
- **Body (excerpt):** confirms the signed PA for 1842 Willowbrook Lane, Carmel, IN 46032; closing September 25, 2026; labeled as a demo-video QA message.  
- **UI:** Facts the AI used, **Approve & send**, **Edit**, “Nothing sends until you approve it.”

On camera: open the draft → **Edit** (change a sentence) → **Approve & send** → show Sent + the deal Email tab. Do not send until you are recording (or send once now as a dry run, then compose a fresh draft).

---

## Inbound test email I need you to send (Scene 6)

Please send this **from one of your four Gmail accounts** (James is the buyer on the deal):

- **From:** james.l.selman13@gmail.com  
- **To:** crazyaidev20500519@gmail.com  
- **Subject:** Question about 1842 Willowbrook Lane closing  
- **Body:**

```
Hi,

When is the closing date for 1842 Willowbrook Lane, Carmel, IN 46032 (WILLOWBROOK-1842-DEMO)?
Please confirm we are still tracking to September 25, 2026.

Thanks,
James Selman
```

After it arrives, tell me and I can re-check **Intelligence → Email → Inbox** for auto-match to Willowbrook (and the deal Email tab + communication history). If Gmail sync is slow, use Refresh on `/ai-emails`.

---

## Must-do before recording

1. **Seed 2–3 more deals** so Active Transactions is not a one-row book. Keep Willowbrook as the flagship walkthrough.  
2. **Clean Unhealthy optics** on Willowbrook (complete/reschedule the 7 overdue tasks, or add a healthier second deal).  
3. **Confirm seller** is visible on Contacts (add with a unique email if still missing).  
4. **Deploy** the Ask AI spoken-date / “propose adding” fix if you want the narration to use plain English dates. Until then, use `due 2026-08-18`.  
5. **Stage OAuth:** Disconnect Gmail (and Google Calendar) → reconnect a **throwaway** Google account so both consent screens + the unverified-app warning are on camera.  
6. **Send the inbound email above**, then film Scene 6 only after it is matched (not “Not linked”).  
7. Film Scene 8 from the staged Outbox draft (or a fresh Compose). Always say: **the AI drafts; a person approves**.  
8. Confirm the Trust & Safety reviewer account matches what the video shows (this admin console branding may be acceptable — double-check against the credentials sent to Google).

---

## Code changes from this QA (local repos — not production until deployed)

- **Backend:** Ask AI deterministic intents accept “Propose adding a task…”, gerunds (`adding`), and spoken calendar dates (`August 18, 2026`).  
- **Frontend:** Closed global AI chat drops `role="dialog"`; Add Contact invalidates the deal parties query so the Contacts tab refreshes.

---

## Credentials / safety note

Platform admin credentials were used only for this production QA. Prefer rotating or using a dedicated reviewer account for the Google submission thread if this password has been shared broadly.
