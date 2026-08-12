# Demo Video Production QA Findings

**Date:** 2026-08-12  
**Environment:** https://app.velvetelves.com  
**Account:** `crazyaidev20500519@gmail.com` (Admin OWNER / platform admin)  
**Guide:** `GOOGLE_DEMO_VIDEO_REQUIREMENTS.md`  
**Method:** Real Google Chrome (Playwright headed, `channel: "chrome"`)  
**AI wizard packet:** all **10** PDFs in `velvet-elves-data/testing_docs/` uploaded simultaneously  

Artifacts: `velvet-elves-data/demo_video_testing/artifacts*` (passes 1–6)

---

## Executive summary

Production is **usable for rehearsing Part 1**, but **not yet safe to record** the Google OAuth demo without staging work.

| Area | Verdict |
| --- | --- |
| Login / marketing / privacy | Pass |
| AI wizard 10-PDF simultaneous upload + create | Pass (5915 deal created) |
| Pipeline density | Pass after seeding (4 active deals, ~$2.2M) |
| Deal workspace tabs | Pass (Timeline / Tasks / Documents / Compliance / Contacts / Email) |
| Ask AI on a deal | **Fail for demo** — answered as portfolio summary, not deal-grounded facts |
| Gmail / Calendar UI | Pass (both already Connected) |
| Live OAuth consent + unverified warning + send/readonly/calendar E2E | **Not executed** (must do live with throwaway Google + second mailbox) |

**Bottom line:** Do not hit Record until (1) Ask AI is clearly deal-grounded with an Approve path, (2) Gmail/Calendar are disconnected so consent screens can be filmed, and (3) the pipeline includes at least one healthy-looking flagship deal for Part 1 narration.

---

## What was verified in Chrome

### Part 1 — Product

1. **Marketing** `velvetelves.com` and **Privacy** Google user-data section — OK.  
2. **Sign-in** → `/dashboard/admin` as Crazyai / Admin OWNER — OK.  
3. **Active Transactions** started at **0 deals** (demo-blocking). After QA seeding: **4 deals**.  
4. **AI wizard:** selected Buyer → uploaded all 10 `testing_docs` PDFs in one multi-file chooser → **Start AI extraction** → Contract Details for **5915 E 350 N, Franklin, IN** → purchase-price double-check (**992,000 vs 950,000**) → Verification → **Upload Transaction**.  
5. **Created flagship deal:**  
   `https://app.velvetelves.com/transactions/0cd44ac3-6eea-4384-b1b2-ef5e2baa5f6b`  
6. Workspace tabs present and populated on seeded + 5915 deals: Overview, Timeline, Compliance, Tasks, Documents, Contacts, Billing, Activity, Email.  
7. Also seeded fixtures: Cedar Mill / Harborview / Willowbend (past-due “Unhealthy” optics).

### Part 2 / 3 — Google surfaces (UI only)

| Surface | Route | State |
| --- | --- | --- |
| Email & E-signature | `/settings/connections` | **Gmail Connected** (`crazyaidev20500519@gmail.com`); Outlook also connected; DocuSign not connected |
| Test connection | same | Clickable; no hard failure observed |
| Disconnect dialog | same | “Disconnect Gmail?” explains inbound sync + send impact; cancelled (kept connected) |
| Closing Calendar | `/calendar` | **Google Calendar Connected**; **Add my closings** present; Outlook connect available |

Full consent screens, unverified-app warning, inbox match, Approve & send, and calendar write-back were **not** re-run in this pass (would require Disconnect + throwaway Google + second mailbox on camera).

---

## Issues

### BUG-001 — Account had zero deals at start of QA (demo-blocking data)

- **Severity:** critical (for recording) / data  
- **Details:** Active Transactions showed “No active transactions yet” / 0 deals. Google’s prior rejection was partly “thin product.” Recording Part 1 on an empty book of business would fail again.  
- **Mitigation done in QA:** seeded 3 fixtures + created 5915 packet deal → **4 active deals**.  
- **Still needed:** 1–2 **on-track / healthy** deals so the list is not only Unhealthy/past-due.

### BUG-002 — Ask AI on deal workspace not deal-grounded — FIXED

- **Severity:** critical (Scene 4)  
- **Root cause:** Closed global `AIChatPanel` stayed focusable and stole composer input (portfolio `/dashboard/ai-chat`); Ctrl+L also opened unscoped chat on deal pages; compound “address + price + closing” asks short-circuited to closing-only; Admin chat context used personal filter unlike workspace access.  
- **Fix:** Inert/disabled closed global panel; path-scoped Ctrl+L/`open()`; compound deal-fact reply; Admin/TeamLead chat access aligned with `require_transaction_access`.  
- **Deploy:** frontend + backend to production before recording.

### BUG-003 — Wizard Discard did not guarantee a clean in-memory slate

- **Severity:** high  
- **Details:** During QA, Discard + a fresh 10-file upload once produced **Uploaded · 18** (stale docs merged with new uploads). Discard only cleared storage/banner, not reducer state.  
- **Fix applied in repo (not yet production):** `NewTransactionWizard` Discard now also `dispatch({ type: 'restore_state', state: makeInitialState() })`.  
- **File:** `velvet-elves-frontend/src/components/wizard/NewTransactionWizard.tsx`  
- **Workaround for recording:** Exit wizard fully, reopen New Transaction, Discard if prompted, confirm **Uploaded · 10** before Start AI.

### BUG-004 — 5915 packet blocked on Closing Date / double-check until resolved — FIXED

- **Severity:** medium (UX friction)  
- **Root cause:** Required dates only gated the internal `missing` step (still labeled Contacts & Fees); one-null verification dates became disagreements without filling the field; “Not found” could clear the create gate with an empty date picker.  
- **Fix:** Contract Details Continue now requires closing + acceptance dates; ISO-normalize date writes; adopt pass-2-only dates into the payload; reject empty resolutions for required dates; clarify double-check copy (“to create”). True two-value conflicts (e.g. 992k vs 950k) still require human pick.

### BUG-005 — Demo script tab name “People” vs product “Contacts”

- **Severity:** low (script mismatch)  
- **Details:** Workspace tab is **Contacts**, not “People.” Update narration/script so the walkthrough matches the UI.

### BUG-006 — Intelligence → Email messages “Not linked”

- **Severity:** medium (Scene 6 readiness)  
- **Details:** Inbox shows messages tagged Not linked. Scene 6 needs an inbound message **matched to the correct transaction**. Seed that with a second mailbox email that references **5915 E 350 N** after Gmail reconnect.

---

## Scene checklist (GOOGLE_DEMO_VIDEO_REQUIREMENTS.md)

| Scene | Result | Notes |
| --- | --- | --- |
| 1 Identity (site + privacy) | PASS | |
| 2 Sign in + pipeline | PASS* | *After seeding; was empty initially |
| 3 Inside a transaction tabs | PASS | Use 5915 or Cedar Mill; tab = Contacts not People |
| 4 AI assistant + approve | FAIL / RISK | Portfolio-scoped answer; Approve path not proven |
| 5 Connect Gmail + scopes | UI PASS / OAuth NOT RUN | Already connected — Disconnect→Connect for video |
| 6 gmail.readonly E2E | NOT RUN | Needs inbound test email + match |
| 7 Draft + Edit | NOT RUN | |
| 8 gmail.send Approve & send | NOT RUN | |
| 9 calendar.events | UI PASS / OAuth NOT RUN | Google Calendar already Connected on `/calendar` |
| 10 Disconnect | UI PASS | Dialog verified; left connected |
| 11 Data handling statement | N/A | Narration only |

---

## Must-do before recording

1. **Deploy / verify deal-scoped Ask AI** on production; rehearse a prompt that yields an **Approve** action and show the result on the deal.  
2. **Stage OAuth:** Disconnect Gmail (and Google Calendar if needed) → reconnect throwaway Google so both consent screens + unverified-app warning are on camera.  
3. **Seed inbound mail** from a second mailbox mentioning **5915 E 350 N** for Scene 6 matching.  
4. Keep **5915** as the flagship walkthrough deal; optionally add 1–2 healthier deals so Part 1 does not look like a overdue-only book.  
5. On wizard take: Buyer → confirm **Uploaded · 10** → Start AI → resolve price double-check → confirm closing → Upload Transaction.  
6. Confirm the Trust & Safety reviewer account matches what the video shows (this admin console branding may be acceptable — double-check against the credentials sent to Google).

---

## Code changes from this QA

- **Frontend:** Discard resets in-memory wizard state; closed global AI chat is inert + path-scoped; Contract Details gates required dates; ISO date writes; double-check copy/empty-date guard.
- **Backend:** Compound deal-fact Ask AI replies; Admin chat access parity; verification pass fills null critical dates before apply.
- **Deploy both apps to production** before demo recording.

---

## Credentials / safety note

Platform admin credentials were used only for this production QA. Prefer rotating or using a dedicated reviewer account for the Google submission thread if this password has been shared broadly.
