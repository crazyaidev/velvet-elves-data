# Jake file logic — staging Chrome QA (2026-08-18)

**Surfaces:** Register, Admin dashboard, AI & Automation, Needs You, All Transactions, deal workspace (posture / status / Email / Tasks), New Transaction wizard  
**Tester:** platform admin `crazyaidev20500519@gmail.com` (`Jan Froben`, role Admin, tenant `9acc81fe-dd18-4269-bf8b-550ddf4cfab3`)  
**Environment:** staging app `https://app.stage.velvetelves.com`, API `https://api.stage.velvetelves.com` (`{"status":"ok","env":"staging","version":"0.1.0"}`)  
**Browser:** Google Chrome via Playwright (`channel: "chrome"`), **headless**, viewport 1280×720, one renderer. Do not set `QA_HEADED=1` on this machine.

**Dataset (live, not seeded for this pass):** five Active **Buy-Fin** files. No cash files. No Terminated files.

| Transaction | Address | Status | Use case | Notes |
| --- | --- | --- | --- | --- |
| `fb22c770-718b-4207-a891-cc44f771b3c4` | 1912 Charles St, Avon, IN, 46123 | Active | Buy-Fin | Autopilot (deal). Amendment PDF already matches file closing date 2026-05-27. Closing-information tasks Completed. |
| `ee6134e7-9753-41cb-b334-770eb8d9e803` | 5915 E 350 N, Franklin, IN, 46131 | Active | Buy-Fin | Autopilot (deal). Pending Buyer Closing Information — used for Q3 email-plan. |
| `bf1b3bbf-32cd-4215-801e-82eede4c52dd` | 9052 Sycamore Ridge, Mason, OH, 45040 | Active | Buy-Fin | Autopilot (tenant default) |
| `1a32e1f7-d808-4dca-9e5e-dc1cbc232246` | auto029269 Automation Test Way | Active | Buy-Fin | Autopilot (deal). Many Needs You items (no purchase agreement). |
| `da681bf7-92e8-45b5-b3d0-8f152e461bca` | 12 Guide Test Way | Active | Buy-Fin | Autopilot (tenant default) |

Harness: `velvet-elves-data/jake_file_logic_qa/jake_file_logic_chrome_qa.mjs`  
API probe: `velvet-elves-data/jake_file_logic_qa/_probe_staging.py`, `_probe_preview.py`  
Artifacts: `velvet-elves-data/jake_file_logic_qa/artifacts_staging_2026-08-18/` (API + first Chrome pass) and `artifacts_staging_2026-08-18_pass3/` (final Chrome pass)

---

## 1. Executive summary

Staging is running the Jake/Audri file-logic UI and the Sell-Cash appraisal planner. Logged in as platform admin, Chrome did not hit a 4xx/5xx on `/api/v1/`, did not show forbidden copy (Conductor / Class A / Library letters / ✦ Autopilot on intake), and the posture split is live: Assisted is tap-to-send, Autopilot is no tap, Terminated is a first-class stage, closing day is not the end of the file.

Final Chrome pass: **49 pass / 0 fail / 1 skip / 50 checks**. The skip is Fast intake on an empty wizard (the hub only appears after a high-confidence extract).

Two product bugs showed up in this pass and are **fixed in the repos, not yet on staging**:

1. **AI & Automation health chip** paints “Automation has stopped” while `/automation/status` is still loading. After the payload arrives, staging correctly shows **Automation active**.
2. **Closing Disclosure omit (Q3)** only matched exact names “Buyer Closing Information” / “Seller Closing Information” and legacy ids 420/430. Live templates also use **440 / 450** (“Seller's Agent Closing Information” / “Buyer's Agent Closing Information”), and existing staging tasks have **no `metadata_json.legacy_task_id`**. Name matching now covers those letters; the dual-leg email planner also strips a forbidden CD.

Q8 (cash appraisal To/CC) is already live on staging via `POST /transactions/preview-tasks` (no cash file in the tenant). Q7 (amendment dates) has nothing to confirm on 1912 Charles: the amendment extract already matches the file’s closing date, and the transaction has no `contract_resolution` blob for the gate to read.

Chrome-green is not the same as “Autopilot is mailing this tenant overnight.” The last hourly tick swept this workspace (**6 surfaced, 0 sent**). Open Automated letters are blocked for honest reasons (missing purchase agreement, stale overdue). Last **draft** sweep for the tenant is ~5 days old; last **tick** was minutes ago.

| Severity | Found | Status |
| --- | --- | --- |
| Medium | 2 | Fixed in code (needs staging redeploy) |
| Low | 1 | Dual-leg CD strip — fixed in code |
| Data / ops | 4 | Documented — no cash/Terminated files; overnight 0 sends; Gmail watch failures |

---

## 2. Account notes

Login succeeded (`onboarding_completed: true`, `is_platform_admin: true`). Tenant default posture is **Autopilot**. Named-letter send is **Allowed**. Hourly automation is **On**. Inspection reminders are **Allowed**. Aime signature is **On**.

`GET /api/v1/automation/status` (during the pass):

- `scheduler_healthy: true`, `last_tick_at` ~2026-08-18 17:47 UTC
- `tenant_last_run_at` 2026-08-14 (draft-sweep clock — Overnight labels this **Last draft sweep**)
- Mailboxes: 4 connected, 2 healthy, 2 unknown
- Last tick platform-wide: 20 tenants swept, 0 Automated sends, 17 surfaced, 6 Gmail watch failures
- This tenant’s last overnight slice: 0 sent, 6 flagged
- This tenant is one of two workspaces listed under “0 Automated sends”

Needs You: **31 items** (`ready: 8`, `safe_approve: 0`) — drafts plus blocked AI tasks (`missing_document`, `no_documents_to_review`, `stale_overdue`). Copy does not mention client Aime or hourly library send.

---

## 3. Pass log

| Pass | Browser | Result |
| --- | --- | --- |
| `api` | urllib against `api.stage` | Inventory, email-plans, templates, cash **preview-tasks** (no persist) |
| `pass1` | Headless Chrome | **FAIL=0**; Q3 Tasks SKIP (Completed closing-info hidden; kebab had no Email) |
| `pass2` | Headless Chrome | **FAIL=0**; Overnight section actually loaded; health chip **Automation active**; Q3 still SKIP on 1912 Completed rows |
| `pass3` | Headless Chrome + `QA_CLOSING_DEAL=ee6134e7-…` | **49 pass / 0 fail / 1 skip / 50 checks** — Buyer Closing Information email plan on 5915 E 350 N, no Closing Disclosure in the plan |

Re-run:

```powershell
cd c:\Projects\velvet-elves-data\jake_file_logic_qa
$env:QA_APP='https://app.stage.velvetelves.com'
$env:QA_EMAIL='crazyaidev20500519@gmail.com'
$env:QA_PASSWORD='<staging admin password>'
$env:QA_CHANNEL='chrome'
$env:QA_CLOSING_DEAL='ee6134e7-9753-41cb-b334-770eb8d9e803'
$env:QA_OUT='c:\Projects\velvet-elves-data\jake_file_logic_qa\artifacts_staging_2026-08-18_pass3'
node jake_file_logic_chrome_qa.mjs
```

Do not set `QA_HEADED=1` on this machine unless it has RAM for a visible Chrome window.

---

## 4. Issues found and resolved

### M1 — Health chip says automation stopped before status loads (fixed)

**Where:** AI & Automation header chip (`AdminAIGovernancePage`)  
**Seen:** First `ai_automation.txt` dump (status still in flight) showed **Automation has stopped**. After `/automation/status` resolved, the same page showed **Automation active · last tick …**. Needs You already waits for the payload before it shows a stopped banner; this chip did not.

**Fix (frontend, not on staging until redeploy):** while `useAutomationStatus` is loading, the chip now says **Checking automation** in a muted style. Stopped / never-run only after a real payload.

### M2 — Closing Disclosure omit missed agent-side closing-info letters (fixed)

**Where:** `task_attachment_policy`  
**Seen:** Staging templates:

| Legacy | Name | Use cases |
| --- | --- | --- |
| 420 | Buyer Closing Information | Buy-Fin, Buy-Cash |
| 430 | Seller Closing Information | Sell-Fin, Sell-Cash |
| 440 | Seller's Agent Closing Information | Buy-Fin, Buy-Cash |
| 450 | Buyer's Agent Closing Information | Sell-Fin, Sell-Cash |

Every live task on this tenant has `metadata_json.legacy_task_id: null`, so id-only matching would miss 420/430 on existing files. Name matching also missed 440/450.

Live email-plans for closing-info tasks had **empty attachments** (no CD on these files), so Chrome Q3 passed vacuously. The omit still had to match the letters Jake named and the buy/sell-side agent variants.

**Fix (backend, not on staging until redeploy):** forbid CD on 420/430/**440/450**, on those four names, and on any task name that contains “closing information”. “Closing Disclosure Delivered” (loan-officer status task) is **not** omitted. Dual-leg `build_task_email_plan` now runs the same strip as the single-letter path.

Tests: `app/tests/test_task_attachment_policy.py` + `test_task_email_flow.py` — **18 passed**.

### L1 — Dual-leg planner skipped the CD strip (fixed)

Same as M2’s planner path. Closing-info is not a dual-leg task today; the strip is now on both paths so a later playbook row cannot attach a CD through the HOA/utility dual builder.

---

## 5. Jake / Audri checks (what staging actually did)

| Item | Result | Evidence |
| --- | --- | --- |
| Q1 Assisted ≠ Autopilot send | **PASS** | Register: Assisted “you tap Send”, Autopilot “No tap”, “only setting that sends without a tap”. COMPARE: Assisted drafted / Autopilot sends without a tap. Workspace posture menu and Email tab repeat the split. |
| Q1 Fast intake (not ✦ Autopilot) | **SKIP** (empty wizard) | `/transactions/new` has no ✦ Autopilot label. Fast intake hub only after a high-confidence extract. |
| Q1 overnight Named letters | **PASS** | Overnight: “Named letters” Allowed; story is Autopilot send / Assisted tap Send. No “Library letters”. |
| Q3 never attach CD on 420/430 | **PASS** on live plans (vacuous) | API email-plans for Buyer / Seller's Agent Closing Information: `attachments: []`. Chrome modal on 5915: no Closing Disclosure. Code now also covers 440/450. |
| Q4 no client Aime | **PASS** | Needs You has no “client Aime” / buyers-and-sellers-talk-to-Aime copy. |
| Q5 closing day ≠ end of file | **PASS** | Completed confirm: “Closing day is not the end of the file”. Files stay Active. |
| Q6 Terminated | **PASS** (empty bucket) | Admin tile → `/transactions/all?tab=Terminated`. Status menu includes Terminated; confirm “fell through” / “not a closed sale”; **Cancel** so no file was terminated. Count is 0. |
| Q7 amendment dates | **SKIP / honest empty** | 1912 amendment extract: closing date 2026-05-27 from *Amend1-…Closing_Date_.pdf* at 0.99 — **already the file date**. No `Confirm amendment dates` task. Transaction has no `contract_resolution` for the gate. |
| Q8 cash 265/271 stay; Sell-Cash To co-op + TC | **PASS** via dry-run | No cash files in the tenant. `POST /api/v1/transactions/preview-tasks` (nothing persisted): Sell-Cash Appraisal Ordered/Completed → To **Co-op Agent**, CC Agent + Co-op Agent + **TransactionCoordinator**. Buy-Cash → To **Buyer**. Buy-Fin stays Loan Officer. |
| Hard stops (money / missing docs / stale) | **PASS** | Needs You: Order Title / Loan Officer Welcome blocked on missing purchase agreement; stale overdue still waits. Last tick sent **0** Automated emails here. |

---

## 6. Remaining skips and ops notes

- **Fast intake** — empty `/transactions/new`. Need a high-confidence extract to see the hub in Chrome.
- **Terminated mail stop** — no Terminated file to prove the executor skip. UI + status confirm are in place.
- **Q7 on a conflicting amendment** — would need a later signed amendment whose dates **differ** from the file, with `contract_resolution` written. Not present.
- **Q3 with a CD on the file** — none of these five deals have a `closing_disclosure` document. Omit is untested against a real CD attachment list; unit tests cover the strip.
- **Last draft sweep 5 days ago** vs last tick minutes ago — Overnight copy is honest. Autopilot is not failing silently; it is surfacing blocked tasks.
- **Gmail watch failures (6)** on the last platform tick — mailbox watch ops, not Jake copy.
- **Existing tasks lack `legacy_task_id`** — new generation stamps it; the CD name fallback covers old closing-info rows after redeploy.

Do not treat this log as proof of Q2 extra letters or client Aime. Those are still not granted.

---

## 7. Code changed in this pass (not committed)

**Frontend**

- `src/pages/admin/AdminAIGovernancePage.tsx` — health chip waits for status before “has stopped”.

**Backend**

- `app/services/task_attachment_policy.py` — 440/450 + “closing information” names.
- `app/services/task_email_planner.py` — dual-leg also drops a forbidden CD.
- `app/tests/test_task_attachment_policy.py` — coverage for the live template names.

Redeploy staging to pick these up. Q8 Sell-Cash stamping is already on the deployed API.
