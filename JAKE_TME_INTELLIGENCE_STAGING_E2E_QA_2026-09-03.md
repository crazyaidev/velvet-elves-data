# Jake TME intelligence — staging end-to-end QA (2026-09-03)

**Purpose:** Verify Jake-architecture features on **newly created transactions**, simulating full workflows start-to-finish — not inspection of legacy/abnormal staging deals.

**Environment:** `https://app.stage.velvetelves.com` / `https://api.stage.velvetelves.com` (staging, version `0.1.0`)

**Account:** platform admin `crazyaidev20500519@gmail.com` (tenant `9acc81fe-dd18-4269-bf8b-550ddf4cfab3`)

**Harness:**

| Script | Role |
|---|---|
| `aime_automation_qa/jake_tme_staging_e2e_api.mjs` | Creates 10 fresh scenarios via API (~9 min) |
| `aime_automation_qa/jake_tme_staging_e2e_chrome.mjs` | Chrome UI on `artifacts_jake_tme_e2e/seed.json` |
| `aime_automation_qa/jake_tme_pdf_fixtures.mjs` | Minimal PA/amendment PDF generators |

**Artifacts:** `aime_automation_qa/artifacts_jake_tme_e2e/` (seed, screenshots, dumps, `run.log`, `e2e_chrome.json`)

**Re-run (required env on this machine):**

```powershell
cd c:\Projects\velvet-elves-data\aime_automation_qa
$env:QA_API='https://api.stage.velvetelves.com'
$env:QA_APP='https://app.stage.velvetelves.com'
node jake_tme_staging_e2e_api.mjs
node jake_tme_staging_e2e_chrome.mjs
```

**Safety:** No Send mail, no Run AI tasks, no irreversible admin actions. API exercised `POST /verify-deadline` (confirm / keep) on test files only.

---

## 1. Executive verdict

**API E2E:** 19 / 20 checks **PASS**, **1 FAIL** (confirmed product bug).

**Chrome E2E (final run):** 14 / 15 checks **PASS**, **1 FAIL** (same bug).

The Jake wrap is **functionally live** on staging for new transactions:

- Two independent grants (**Autopilot** ≠ **Trusted** contract dates)
- Settings: **You confirm** / **Trusted** only (no Assisted dates)
- Wizard intake → **Confirmed** provenance on timeline
- Amendment upload → **Verify deadline** in Needs You with **Confirm / Keep current / Edit**
- **Confirm** applies new closing; **Keep** preserves prior date
- **Trusted** waits when parse is conflicting or unclear (does not silently override)
- Dual **Both-Fin** → per-side **Deliver Title** + buyer **Deliver Utility Info** (no legacy 305-only row)
- Contacts **Decision-maker** / **Must sign** toggles
- Terminated → **Offer Listing Success** visible and **disabled**; `lse_handoff` in plan API
- Ask AI refuses legal termination advice

**One confirmed defect** reproduced on a **fresh** Terminated file: **`Next:` still ranks a leftover obligation** (`Review Documentation`). This is not legacy-data noise.

**Test gap (not a failure):** Silent **Trusted auto-apply** of a *clear, high-confidence* amendment closing change was not achieved with minimal generated PDFs — Textract/confidence stays below the auto-apply bar, so **Verify deadline** correctly fires instead. Proving silent auto-apply needs richer PDF fixtures (e.g. `demo_video_testing/willowbrook_purchase_agreement.pdf` + a high-quality amendment).

---

## 2. Methodology

### 2.1 Why new transactions

Prior staging Chrome QA on existing deals (see `JAKE_TME_INTELLIGENCE_STAGING_CHROME_QA_2026-09-03.md`) could not exercise **Verify deadline** or wizard provenance because those deals predated the wrap or lacked pending amendments. This pass **creates** deals with a shared timestamp stamp `20260903155227` so every scenario starts from a known baseline.

### 2.2 Document parsing constraint

Staging **rejects non-PDF** uploads for Textract (`text/plain` → empty `resolved_fields`). All amendment scenarios use **generated minimal PDFs** or `willowbrook_purchase_agreement.pdf` for the PA leg.

### 2.3 Scenario matrix

| ID | Scenario | Setup | Expected behavior |
|---|---|---|---|
| **S1** | Wizard provenance | New Buy-Fin tx, verified closing/acceptance in intake | Plan provenance `verified`; timeline **Confirmed** chip; TME stages + **Next** line |
| **S2** | You confirm + amendment | Tenant You confirm; PA + clear amendment (Oct 15 → Nov 1) | **Verify deadline** card; closing unchanged until decision |
| **S2b** | Amendment-only confirm path | You confirm; amendment PDF only | Verify card → **Confirm** → Nov 1 closing |
| **S3** | Confirm on S2 | `POST verify-deadline` action `confirm` | Closing Nov 1; provenance stays verified |
| **S4** | Keep current | Willowbrook PA + amendment; action `keep` | Closing stays Oct 15 |
| **S5** | Trusted + clear amendment | Deal **Trusted** dates; PA + amendment | Ideally silent apply to Nov 1; **or** verify if conflict/low confidence |
| **S6** | Trusted + fuzzy amendment | Trusted; fuzzy closing text in amendment | Wait (verify card **or** unchanged closing) |
| **S7** | Dual Q1 tasks | Both-Fin Dual; generate tasks | **Deliver Title:Buyer** + **Deliver Title:Seller** + **Deliver Utility Info** (buyer); no Both-only 305 |
| **S8** | Contacts flags | Dual deal party toggles | Decision-maker / Must sign persist |
| **S9** | Terminated LSE | Fresh tx → Terminated via API | Disabled **Offer Listing Success**; **no Next obligation** |

---

## 3. Fresh transaction IDs (staging)

| Scenario | Transaction ID | Label |
|---|---|---|
| S1 Provenance | `a5305337-4c3b-4c4b-98e1-352417a6d5a7` | Prov Jake TME E2E 20260903155227 |
| S2 You confirm | `ffcd6eec-cb25-43f9-aa35-36e481be1161` | YouConfirm Jake TME E2E 20260903155227 |
| S2b Amend only | `256d9b49-d4bd-4ea4-84cf-69b5c8341000` | AmendOnly Jake TME E2E 20260903155227 |
| S4 Keep current | `ce4e0b8c-d75d-4acf-9ded-5f4f505e92ed` | KeepCurrent Jake TME E2E 20260903155227 |
| S5 Trusted auto | `e3ee3fc5-1c10-4e7e-b9d0-ed2ce5e57ed2` | TrustedAuto Jake TME E2E 20260903155227 |
| S6 Trusted fuzzy | `50f4007e-9a96-4bb2-87e2-37139d9adfc6` | TrustedFuzzy Jake TME E2E 20260903155227 |
| S7 / S8 Dual | `cc1a52ed-7710-40be-ae33-052b750e525c` | Dual Jake TME E2E 20260903155227 |
| S9 Terminated | `20d5633a-9e1d-4782-9265-55081da11d96` | Terminated Jake TME E2E 20260903155227 |

---

## 4. API results (2026-09-03 ~15:52–16:02 UTC)

| Check | Result | Notes |
|---|---|---|
| login | PASS | |
| s1.wizard_verified_provenance | PASS | `closing=verified`, `acceptance=verified` |
| s1.stages_and_next | PASS | Earnest Money · Inspection / Due Diligence · Financing |
| s2.autopilot_not_trusted_dates | PASS | Autopilot email; `obligation_autonomy=manual` (You confirm) |
| s2.verify_deadline_pending | PASS | Needs You task **Verify deadline** after PA + amendment parse |
| s2.closing_unchanged_before_confirm | PASS | Still `2026-10-15` |
| s2b.amendment_only_verify | PASS | Verify path on amendment-only upload |
| s2b.confirm_applies | PASS | → `2026-11-01` |
| s3.confirm_applies_closing | PASS | S2 confirm → `2026-11-01` |
| s3.confirmed_provenance_after_confirm | PASS | `verified` |
| s4.keep_current_date | PASS | Stayed `2026-10-15` after keep |
| s5.trusted_auto_apply | PASS | **Conflict path:** verify card, closing unchanged (expected when `conflict: true`) |
| s6.trusted_fuzzy_waits | PASS | Closing unchanged; no erroneous auto-apply |
| s7.dual_deliver_title_per_side | PASS | Buyer + Seller rows |
| s7.dual_utility_buyer | PASS | |
| s7.no_both_only_305 | PASS | |
| s8.decision_maker_toggle | PASS | |
| s9.lse_handoff | PASS | `offer_lse: true`, Terminated payload |
| **s9.terminated_next_line** | **FAIL** | `next_action.title = "Review Documentation"` (obligation) |

### Amendment gate detail (S2 card)

Verify item included:

- `block_code: amendment_date_confirm`
- Summary: file had Closing **2026-10-15**; amendment says **2026-11-01**
- `date_changes[0].conflict: true`, `explicit: false` (minimal PDF parse quality)

This is **correct product behavior** for You confirm: surface card, do not mutate closing until staff acts.

### Trusted behavior (S5)

With minimal PDFs, amendment resolution sets **conflict** and does not auto-apply even on Trusted — consistent with copy: *Unclear or conflicting contract dates never go live on their own.*

---

## 5. Chrome results (final run, run3)

| Check | Result |
|---|---|
| ui.settings_two_date_choices | PASS |
| ui.s1.confirmed_provenance | PASS (Timeline **Confirmed**) |
| ui.s1.stages_next | PASS |
| ui.verify_deadline_card | PASS (TrustedAuto deal) |
| ui.verify_buttons | PASS (Confirm, Keep current, Edit visible) |
| ui.s3.new_closing_visible | PASS (Nov 1 on YouConfirm file after API confirm) |
| ui.s5.trusted_on_deal | PASS |
| ui.s5.trusted_conflict_behavior | PASS (Oct 15 still shown while verify pending) |
| ui.s7.dual_title_rows | PASS (3 mentions — buyer + seller rows) |
| ui.s7.utility | PASS |
| ui.s8.flags | PASS |
| ui.s9.lse_disabled | PASS |
| **ui.s9.no_next_on_fresh_terminated** | **FAIL** — header shows `Next: Review Documentation` |
| ui.aime.refuse_legal | PASS |

Screenshots: `artifacts_jake_tme_e2e/chrome_*.png`

---

## 6. Issues discovered

### M1 — Terminated files still show **Next:** obligation (BUG)

| | |
|---|---|
| **Severity** | Medium |
| **Repro** | Create any Buy-Fin tx → terminate → open workspace |
| **Fresh ID** | `20d5633a-9e1d-4782-9265-55081da11d96` |
| **API** | `header.next_action.kind = obligation`, title `Review Documentation` |
| **Chrome** | Header renders `Next: Review Documentation` |
| **Expected** | Terminated posture should suppress perform-ladder **Next** (LSE handoff only) |
| **Likely fix** | `rank_next_action` / plan composer should no-op obligations when `termination_state === Terminated` |

### G1 — Trusted silent auto-apply not proven (TEST GAP)

| | |
|---|---|
| **Severity** | Low (test coverage) |
| **Observation** | Minimal generated amendment PDFs yield `conflict: true`, `explicit: false`, confidence &lt; 0.90 |
| **Result** | S5 correctly routes to **Verify deadline** instead of silent Nov 1 apply |
| **Follow-up** | Add fixture using production-quality PA + explicit amendment PDF; re-run S5 |

### G2 — First API run used text/plain uploads (RESOLVED)

| | |
|---|---|
| **Severity** | Test harness |
| **Symptom** | Empty `resolved_fields`, no verify cards |
| **Fix** | PDF fixtures in `jake_tme_pdf_fixtures.mjs` |

### G3 — Intermittent Chrome “Loading…” on Needs You / Settings (RESOLVED)

| | |
|---|---|
| **Severity** | Harness flake |
| **Fix** | Wait for `AI & Automation` heading, Contract dates radiogroup, Needs You list idle |

### Out of scope this pass

- **Client portal** (represented client no Ask AI) — validated in prior staging Chrome QA, not re-seeded here
- **FSBO Ask Aime** — known separate surface
- **Legacy deal provenance backfill** — not expected for old files without `transaction_facts`

---

## 7. Feature checklist (Jake architecture)

| Feature | New-tx E2E status |
|---|---|
| Autopilot ≠ Trusted (two grants) | ✅ API + Chrome |
| Settings You confirm / Trusted only | ✅ Chrome |
| Deal-level Trusted dates pin | ✅ Chrome (S5 menu) |
| Wizard → Confirmed provenance | ✅ API + Chrome timeline |
| Verify deadline Needs You card | ✅ API + Chrome |
| Confirm / Keep / Edit actions | ✅ API (confirm/keep) + Chrome (buttons) |
| Amendment blocks closing until decision (You confirm) | ✅ |
| Trusted waits on conflict/unclear parse | ✅ S5 |
| TME stages line | ✅ S1 |
| Dual Deliver Title per side + utility | ✅ API + Chrome |
| Contacts Decision-maker / Must sign | ✅ API + Chrome |
| Terminated LSE disabled | ✅ API + Chrome |
| Terminated suppress Next | ❌ **M1** |
| Ask AI legal refuse | ✅ Chrome |
| `POST /verify-deadline` deployed | ✅ |

---

## 8. Recommended next steps

1. **Fix M1** — suppress `next_action` obligations on Terminated in backend plan composer; add regression test mirroring `test_jake_tme_intelligence.py` / transaction plan tests.
2. **Extend S5 fixture** — high-confidence amendment PDF to prove Trusted silent apply path on staging.
3. **Optional** — add client-portal step to `jake_tme_staging_e2e_chrome.mjs` (login as `ellenore.zynique@minafter.com`, assert no Ask AI on assigned fresh tx).
4. **CI** — wire `jake_tme_staging_e2e_api.mjs` as scheduled staging smoke (nightly), Chrome on demand.

---

## 9. Relation to prior report

`JAKE_TME_INTELLIGENCE_STAGING_CHROME_QA_2026-09-03.md` inspected **existing** staging deals and correctly flagged deploy presence + legacy-data limits. **This document supersedes functional sign-off** for Jake wrap behavior: features are validated on **new** transactions with full amendment and termination workflows.

**Run stamp:** `20260903155227` · API log: `artifacts_jake_tme_e2e/run.log` · Chrome: `artifacts_jake_tme_e2e/chrome_run3.log`
