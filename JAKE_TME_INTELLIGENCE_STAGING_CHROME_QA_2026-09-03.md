# Jake TME intelligence — staging Chrome QA (2026-09-03)

**What this pass checked:** the wrap just deployed to realize Jake’s architecture on the live file — two grants (Autopilot = named email send, Trusted = contract dates), You confirm vs Trusted, Verify deadline, typed provenance, overlapping TME stages, one Next line, Contacts flags, legal refuse, Dual Q1 rows, Terminated Listing Success offer, no represented-client Aime.

**Staging:** `https://app.stage.velvetelves.com` / `https://api.stage.velvetelves.com` (`{"status":"ok","env":"staging","version":"0.1.0"}`)

**Accounts:** platform admin `crazyaidev20500519@gmail.com` (Jan Froben, Admin); team lead `keylan.symir@minafter.com`; represented client `ellenore.zynique@minafter.com`; FSBO `brevyn.joshawn@minafter.com`.

**Safety:** I did not Send mail, confirm Run AI tasks, Disconnect, or Change status. I did PUT workspace Contract dates to Trusted and back to You confirm, pin Trusted dates on 12 Guide Test Way and Follow the workspace again, and toggle Dual Buyer Decision-maker then restore it.

**Browser:** Google Chrome via Playwright, headless, 1280×800. Harness: `aime_automation_qa/jake_tme_staging_chrome_qa.mjs` and `jake_tme_staging_chrome_followup.mjs`. Artifacts: `aime_automation_qa/artifacts_jake_tme_staging/`.

This machine had leftover `QA_APP=http://localhost:5173`. The staging run must set:

```powershell
$env:QA_APP='https://app.stage.velvetelves.com'
$env:QA_API='https://api.stage.velvetelves.com'
```

---

## 1. Verdict

The deploy is on staging and the two-grant law holds in the browser: this QA tenant is **Autopilot for email** and **You confirm for contract dates**. Trusted does not turn on with Autopilot. Settings shows two date choices (You confirm / Trusted), not Assisted. The deal header has a Trusted dates group. Ask AI refuses “tell them they can terminate.” Dual still has buyer and seller Deliver Title plus buyer Deliver Utility Info. Terminated 1912 Charles shows a disabled Offer Listing Success control.

Three things did not fully prove out on this tenant, and one of them is a real product miss:

| Severity | Issue | Status |
|---|---|---|
| Medium | Terminated files still rank a leftover task as **Next:** | Open — seen in Chrome |
| Medium | Confirmed / Reported / Conflict never paint on existing files | Open — no typed facts / no backfill |
| Test gap | Needs You **Verify deadline** (Confirm / Keep current / Edit) | Endpoint live; no pending date proposal to click |
| Data | Represented client Ellenore has no assigned file, so Home cards are empty | Not a wrap regression |
| Out of round | FSBO workspace still has Ask Aime | Represented client portal does not |

Staff Chrome (admin): **0 fail / 5 warn / 2 skip / 46 checks**, then follow-up **0 fail / 1 warn / 1 skip / 13 checks**. The first-pass warns were toast timing, Dual Tasks dump taken before the list painted (follow-up found both Deliver Title rows), Terminated Next, and client Home still on the spinner (form login + wait cleared it).

---

## 2. What is live on staging (API + Chrome)

Tenant `9acc81fe-dd18-4269-bf8b-550ddf4cfab3`:

| Setting | Value |
|---|---|
| Workspace email posture | **autopilot** |
| Contract dates (`obligation_autonomy`) | **manual** (You confirm) |
| Named-email send | Allowed |
| Hourly automation | On, healthy; last tick ~2026-09-03 08:47 UTC |
| Needs You | 70 items; **zero** `amendment_date_confirm` / Verify deadline cards |

`POST /transactions/{id}/verify-deadline` with `keep` on a file that has no pending proposal returns **400** `No contract date is waiting for a decision.` The route is deployed.

Plan payloads now include `tenant_obligation_default`, `lse_handoff` (on Terminated), `header.tme_stages` / `tme_stages_line`, and `header.next_action`.

Files used:

| File | Why |
|---|---|
| 12 Guide Test Way (`da681bf7-…`) | Active test file — stages, Next, Trusted pin, timeline |
| 700 Test Dual Ave (`f53d0674-…`) | Both-Fin — Contacts flags, Dual title/utility, Ask AI refuse |
| 1912 Charles St (`fb22c770-…`) | Already Terminated — Offer Listing Success (read only) |

1912 Charles and 5915 E 350 N are Terminated now. I did not change status on this pass.

---

## 3. Pass log

### Settings → AI & Automation → How it runs

- Two cards. Automation posture is still Manual / Assisted / Autopilot with **Save posture**.
- **Contract dates** is its own card: **You confirm** (Recommended) and **Trusted**. No Assisted dates radio. **Save dates**.
- Copy: this does not send email; turning on Autopilot does not turn this on.
- Always true list includes: *Unclear or conflicting contract dates never go live on their own.*
- No “obligation autonomy,” no “Conductor.”
- PUT Trusted → 200, then PUT You confirm → 200. Left the workspace on You confirm.

Health chip in the screenshot: **Automation active · last run 56 min ago.**

### Deal header (Guide Test Way + Dual)

- Lifecycle line: Earnest Money · Inspection / Due Diligence · Financing.
- **Next: Order Title** (Guide) / **Next: Inspection Scheduled** (Dual).
- One Autopilot / Assisted chip. Menu: email choices, then **Trusted dates** — On for this deal / Off for this deal, *This is not email send*, always-true line.
- PUT On for this deal → 200; PUT Follow the workspace → 200. Left Guide Test Way inheriting You confirm.
- Offer Listing Success is **absent** on Active files.

### Contacts (Dual)

- Dual Buyer / Dual Seller present. Decision-maker and Must sign show when the buyer row is expanded. PUT Decision-maker 200; restored.

### Dual tasks (Audri Q1)

API and Chrome Tasks tab, 700 Test Dual Ave:

- Deliver Title · Buyer (legacy 300) and Deliver Title · Seller (legacy 310). No Both-only 305.
- Deliver Utility Info · Buyer (legacy 150).
- Request Utility Info · Seller (140). Co-op welcome 160 is not on this Dual file.

### Ask AI

On Dual: “tell them they can terminate” → *I can quote what the file literally says and draft a question for you to send. I cannot give legal advice or tell a party they may terminate.* Chat did not send mail. No “I disagree.” No Conductor.

### Terminated (1912 Charles)

- Status Terminated. Lifecycle **Terminated / Failed**.
- **Offer Listing Success** visible and disabled. Title: Listing Success is not in this product yet; Aime will not start listing work from a failed file.
- Plan `lse_handoff.offer_lse: true`, `silent_listing_forbidden: true`.
- **Issue:** header still shows **Next: Title Work Completed**.

### Needs You

No Verify deadline card. Remaining items are the usual Handle blocks (`no_recipient`, `missing_document`, …). Confirm / Keep current / Edit were not clickable on this tenant.

### Provenance

Tracking dates and timeline on Guide Test Way / Dual / Charles have dates but `provenance: null`. No Confirmed / Reported / Conflict chips. The `transaction_facts` table shipped; existing columns were not backfilled.

### Team lead

`keylan.symir@minafter.com` opens Guide Test Way. Trusted dates group is in the automation menu. API `obligation_autonomy` is manual.

### Represented client

`ellenore.zynique@minafter.com` reaches `/client/home`. No Ask AI, no Needs You. Nav is Home / Next Steps / Timeline / Documents / Updates. Message Agent / View Timeline / Closing Day Info. Boundary: *Your agent and coordinator handle workflow. Reach them directly for legal questions.*

`GET /api/v1/dashboard/client` returns **0 transactions**. Home cards are empty. That is this user’s data, not a missing Aime chat.

### FSBO

`brevyn.joshawn@minafter.com` at `/fsbo`: empty property list, coordinator card, and an **Ask Aime** composer. Represented client portal does not have that composer. Seller Aime was not part of this wrap.

---

## 4. Issues

### M1 — Terminated files still rank a leftover obligation as Next

**Where:** deal header `plan.header.next_action` on 1912 Charles St (Terminated).

**Seen:** Chrome: **Terminated / Failed** plus **Next: Title Work Completed**, beside the disabled Offer Listing Success chip. API: `next_action.title = "Title Work Completed"`, `kind = obligation`.

**Why it matters:** Jake’s failed-file rule is Terminated, not Closed, with a visible-and-off Listing Success offer and no silent listing start. Ranking title work as the one Next line on a dead file reads as if the file is still being run.

**Expected:** no Next obligation on Terminated, or Next points at the human leftover (Offer Listing Success / archive), not an open title task.

**Not done this pass:** I did not Change status to reproduce on another file.

### M2 — Confirmed / Reported / Conflict never show on files that already have dates

**Where:** tracking-date chips and Timeline. API `tracking_dates[].provenance` and `core_dates[].provenance` are null on Guide Test Way, Dual, Sycamore, and Charles.

**Why:** Phase 1 facts write on wizard confirm, inbound extract, and Verify deadline. The migration creates `transaction_facts` and does **not** backfill existing transaction date columns. `provenance_label` only runs when fact rows exist.

**Expected on the live file:** dates that already went through Confirm Details should read Confirmed (or stay unlabeled until the next signed document). Testers will not see the three words until a new fact is recorded.

**How to prove later:** new wizard Confirm Details, or a later amendment that opens Verify deadline.

### T1 — Verify deadline Confirm / Keep current / Edit not exercised on staging

**Where:** Needs You. API `GET /automation/needs-you`: 70 items, 0 `amendment_date_confirm`.

**Seen:** `POST …/verify-deadline` `{ "decision": "keep" }` → 400, no pending proposal. Chrome search for Verify deadline: none.

**This is not a missing route.** It is missing **data**: no later signed amendment/addendum on this tenant that disagrees with the file dates. Charles already has an amendment whose extracted closing date matches 2026-05-27.

**To close the gap:** upload a later signed amendment that clearly moves closing (or inspection / EM / appraisal / acceptance / possession) on a You confirm file, then tick Confirm and Keep current on Needs You. Do that on a test address, not a live CB Stiles file.

### D1 — Ellenore’s client Home has no file

**Where:** `/client/home` for `ellenore.zynique@minafter.com`.

**Seen:** shell and boundary copy are correct; concierge cards are empty. Dashboard `transactions: []`.

**Not a wrap bug.** Cannot use this user to check client timeline dates or “clients never see Needs You” beyond the shell.

### O1 — FSBO still has Ask Aime (out of round)

**Where:** `/fsbo` for Brevyn. Composer: *Ask me about your properties…*

Represented clients do not get Aime. This wrap did not remove seller Ask Aime. Leave it unless Jake wants FSBO on the same “no client chat until safety rules” rule.

---

## 5. What I did not break / did restore

- Workspace Contract dates left on **You confirm** (manual).
- 12 Guide Test Way left on **Follow the workspace** for dates.
- Dual Buyer Decision-maker left **on**.
- No mail sent. No overnight Run. No Disconnect. No status change.

---

## 6. Re-run

```powershell
cd c:\Projects\velvet-elves-data
$env:QA_APP='https://app.stage.velvetelves.com'
$env:QA_API='https://api.stage.velvetelves.com'
$env:QA_EMAIL='crazyaidev20500519@gmail.com'
$env:QA_PASSWORD='<staging password>'
python aime_automation_qa/_jake_tme_staging_probe.py
node aime_automation_qa/jake_tme_staging_chrome_qa.mjs
node aime_automation_qa/jake_tme_staging_chrome_followup.mjs
```

Do not set `QA_HEADED=1` on this machine unless it has RAM for a visible window. Do not leave `QA_APP` pointed at localhost.
