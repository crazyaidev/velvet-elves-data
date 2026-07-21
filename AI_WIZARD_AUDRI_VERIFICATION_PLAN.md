# AI Wizard — Audri Issues: Verification & No-Hardcoding Plan

**Author:** Jan
**Date:** 2026-07-16
**Scope:** verify, one by one, that every issue Audri raised is correctly resolved, by uploading the **10 PDFs in `velvet-elves-data/testing_docs/` simultaneously**, and prove the fixes are **general logic, not hard-coded to this packet** (so they work on other contracts and introduce no new issues).
**Source material constraint:** only the 10 documents in `testing_docs/` are used. Generalization is proven by **controlled edits to those documents' own content** plus a **source-code audit**, never by importing other packets.
**Companion docs:** `AI_WIZARD_AUDRI_TESTING_REMEDIATION_PLAN.md` (root causes, source citations, §9 implementation status) and `AI_WIZARD_AUDRI_ISSUES_RESOLUTION_REPORT.md` (plain-language status).

---

## 0 · The three questions this plan must answer

1. **Resolved?** For each Audri issue, does the simultaneous 10-PDF upload now produce the correct result?
2. **No hard-coding?** Does every fix respond to the *contract's content* rather than a value baked in for this packet? (If I flip a value in the document, does the output flip with it?)
3. **No new issues?** Do the changes leave every other scenario — waived inspection, at-closing possession, a genuinely missing counter, an unsigned deal, an FSBO seller — working correctly?

A fix passes only when **all three** are green. Question 1 is the "one by one" verification (Part 1). Questions 2 and 3 are the anti-hard-coding proof (Parts 2–4).

### Definition of "no hard-coding" for this work
- **Zero packet-specific answer values in product code.** No `5915`, `992000`, `950000`, `9000`, `Koenig`, `Campbell`, `2026-07-31`, `2026-08-30`, and no forced `"buyer"`, `30`, `15`, `4` as answers. Such literals may appear **only** in test files and in one illustrative rule-example inside a prompt (flagged in Part 2).
- **Every deterministic backstop fills a null only and never overrides** what the document/model already said. Structurally it cannot force a wrong value onto a contract that states otherwise.
- **Input-response symmetry:** editing a field in the document changes the extracted result to match. This is the decisive test (Part 3).

---

## 1 · Pre-flight (once, before verifying)

1. **OCR mode:** confirm `TEXTRACT_OCR_ONLY_MODE=false` (FORMS on) in the target environment (`config.py:197` default is already `false`).
2. **Deterministic AI:** confirm the three wizard agents carry `deterministic_model_settings()` (temperature 0 + seed) — this is the core fix and must be present for every run.
3. **Migrations for the deploy-gated items (Audri 12/14/15):** apply `20260917090000` (AI task executor), `20260918090000` (task-email transaction-party), the welcome-sender migrations, and `20260919090000` (fees); restart the backend (`.env` loads by absolute path, so `--reload` does not pick it up).
4. **Connected mailbox:** the deal-owner account used for the UI run has a connected Gmail/Outlook mailbox (welcome/AI-task sends need it; otherwise those tasks correctly *surface* instead of sending).
5. **Uploading all 10 at once:** in the New Transaction wizard Step 1 (Upload), select the **representation = Seller** (this packet is a listing-side sale), then drag or file-pick **all 10 PDFs together** into the drop zone in a single action, and wait for the parse to complete before advancing. The pipeline OCRs and resolves them as one packet.

---

## 2 · Two verification tracks

Every item is checked on at least one track; the extraction items are checked on both.

- **Track A — Real UI, end-to-end (what Audri does).** Upload all 10 in the wizard, click through Contract Details → Contacts & Fees → Verification → Upload Transaction → workspace. Everything is observed in the UI, no console. This is the acceptance a non-developer runs.
- **Track B — Deterministic pipeline harness (repeatable, automated).** OCR the 10 PDFs once, cache the result, then run the real extraction/intake code against the cache and assert the ground truth. Track B is what proves determinism and lets Part 3/4 run cheaply and repeatably. (Harness already built during implementation: an OCR-cache step + a ground-truth assertion that exits pass/fail. It should be promoted into the repo as a live-gated integration test, e.g. `app/tests/live/test_real_packet_5915.py`, skipped when API keys are absent, with the OCR cache committed as a fixture so only the LLM call needs network.)

---

## 3 · Part 1 — Per-issue verification on the simultaneous 10-PDF upload

Verify each item in order. "Track" = where it is checked. "Pass" = the exact acceptance. Numbering follows Audri's report.

### Extraction cluster (Track A + B)

| # | Issue | Where to look (UI) | Pass criterion |
|---|---|---|---|
| 1 | Who orders title | Contract Details → "Who orders title?" | reads **Buyer**, with a source chip |
| 2 | Inspection days | Contract Details → inspection deadline row | **15 days** after acceptance |
| 6 | Earnest-money window | Contract Details / timeline | **4 business days after acceptance** (not the 3-day default) |
| 8 | Signatures | Verification → signature panel | **fully executed**; no e-sign / request-copy action offered |
| 10 | Determinism | repeat the whole upload 3× | **identical** reads all three times |
| 11 | FSBO | Contacts step | **no FSBO box** appears (seller-rep) |
| — | Purchase price (bonus) | Contract Details → price | **$992,000** (the controlling counter, not the superseded $950,000) |
| — | Earnest money amount | Contract Details | **$9,000** (the counter-raised value) |

Track B mirror: run the ground-truth assertion (15 checked fields) and the 3× determinism check; **pass = all fields correct AND output identical across runs.**

### Documents / possession cluster

| # | Issue | Where to look | Pass criterion |
|---|---|---|---|
| 5 | Re-asking for uploaded docs | Verification document list | the Post-Closing Possession (and each of the 10) shows **satisfied / attached**, never an "attach" or "add" ask |
| 7-i | Possession date | Contract Details → possession date | auto-fills to **2026-08-30** (closing + 30) |
| 7-ii | Contingency day-anchor | add/edit a post-closing contingency, type `30` in Days | date computes to **closing + 30** (8/30), not acceptance + 30 (7/27) |
| 7-iii | Sticky "needs your eyes" | Verification "found in the contract" area | the surrender-deadline is **confirmed/cited**, not stuck at "citation could not be located" with no date |
| 3 | 65 duplicate referenced-docs | Verification | **no** "referenced documents not uploaded" list |
| 4 | Upload intro copy | Step 1 (Upload) | intro invites adding more docs; no amber tracking box |
| 16 | "Step 3" checklist | wizard nav | no standalone confusing checklist step (retired) |
| 19 | Deal Brief in wizard | anywhere in the wizard | **no** Deal Brief card in the wizard |

### Post-create workflow (Track A, after Upload Transaction — needs the Pre-flight migrations)

| # | Issue | Where to look | Pass criterion |
|---|---|---|---|
| 12 | Welcome emails + hidden AI tasks | workspace task list + sent mail | Buyer/Seller/Co-op/Loan-Officer welcomes send; those AI tasks are **not** in the overdue list; Review Documentation self-completes |
| 14 | Pending Reminder | open Pending Reminder task | opens a **self-reminder to the account holder** (MLS pending), **no vendor picker** |
| 15 | Vendor → Transaction Party | open Appraisal Ordered task | **"Select a transaction party member"** dropdown, Loan Officer pre-selected, all captured parties listed |

### Remaining items (verify the fix once built; see Part 5)

| # | Issue | Pass criterion (when implemented) |
|---|---|---|
| 9 | "Add as task" button | a document row's "Add as task" creates a task dated ≤ 7 days before closing, editable |
| 13 | Next-step CTA | clicking the next-step CTA opens the **task** (AI-completion modal), not the chatbot |
| 17 | Double-check context | each double-check row names its field + highlights the matching document |
| 18 | Feedback box | free-text field + "submit anonymously" toggle |
| 20 | Endless scroll | each column scrolls within its bounds; the page never runs past the workspace |

---

## 4 · Part 2 — Anti-hard-coding source audit (static, no execution)

The goal: prove the product code contains no answer baked for this packet.

1. **Full diff review.** Read the complete diff of every changed product file: `document_packet_parsing.py` (temperature settings, counter-sequence prompt text, possession backstop, title-annotation fix), `intake_intelligence.py` (temperature settings), `NewTransactionWizard.tsx` (contingency anchor, deal-brief removal). Confirm each change is general logic.
2. **Literal scan.** Grep the **product** code (excluding tests) for every packet value: `5915`, `992000`, `950000`, `6000`, `9000`, `koenig`, `campbell`, `2026-07-31`, `2026-08-30`, and for suspicious forced constants (`= "buyer"`, `= "seller"`, `possession.*30`, `inspection.*15`, `earnest.*4`). **Expected result: zero hits in product code.**
3. **The one deliberate exception.** The extraction prompt contains an *illustrative* counter-sequence example using 992,000 / 950,000. It teaches the **rule** ("a higher-numbered counter wins; a silent later counter carries the last stated value forward"), not an answer. It is flagged here and **must be proven to generalize** by the price-chain flip test in Part 3 (different numbers → different, correct result). If the flip test ever failed, the fix would be to abstract the example to generic tokens (Counter #1 = A, #2 = B, #3 = A).
4. **Fill-null-only invariant.** Confirm in source that `apply_title_ordering_backstop`, `apply_inspection_period_backstop`, `apply_possession_backstop`, and `apply_signature_chain_backstop` each **return early without changing anything when the field is already set** (they only fill nulls and correct a self-contradicted signature flag). This guarantees a backstop can never overwrite a correct contract value with a packet-specific guess.
5. **Answers live only in tests.** Confirm the ground-truth table (992000, buyer, 15, …) exists **only** in the test harness / test files, never imported by product code.

**Exit for Part 2:** the diff is general; the literal scan is clean; the prompt example is the sole packet-derived literal and is queued for the flip test.

---

## 5 · Part 3 — Generalization by input-response ("flip") tests

This is the decisive proof. Using **only the 10 `testing_docs/`** as the base, create edited copies of their extracted text that change one field at a time, run the **same** code, and require the output to change to match. If any output stays pinned to the original packet answer, something is hard-coded.

### 5a · Deterministic-layer flips (no LLM — fast, repeatable, add to the unit suite)
These target the pure functions I added/changed; they need no API keys and run in milliseconds.

| Flip (edit to the packet text) | Function under test | Required output |
|---|---|---|
| `[X] Buyer will select` → `[X] Seller will select` | `_checked_title_party` / `apply_title_ordering_backstop` | title = **seller** |
| remove all checkbox markers around Seller/Buyer | same | returns **null** (never guesses first-listed) — already covered, keep |
| `[X] Seller [X] Buyer` (both checked) | same | returns **null** (ambiguous) — already covered, keep |
| confidence noise `[87.4%]` between box and label | same | still reads the checked party (regression for the real-OCR bug) |
| "Buyer shall have 15 days" → "Buyer shall have 9 days" | `_inspection_period_days` | **9** |
| AS-IS box `[ ]` → `[X]` + has_inspection false | `apply_inspection_period_backstop` | **no fill** (waived) — already covered, keep |
| "30 days after closing" → "45 days after closing" | `_possession_days_after_closing` + `apply_possession_backstop` | possession = **closing + 45** |
| "surrender by 30 days after closing" → "possession delivered at closing" | same | **no fill** (no after-closing window) |
| possession already set to a date | `apply_possession_backstop` | **no override** — already covered, keep |
| contingency name "post-closing possession" vs "financing" (frontend) | `contingencyAnchorIso` | post-closing → **closing** anchor; financing → **acceptance** anchor |

Each flip asserts the **changed** answer, proving the code is driven by the document, not a constant.

### 5b · LLM-layer flips (live, gated by API keys — run a representative subset)
These edit the cached OCR text of the 10 PDFs and run the full extraction. Slower/cost money, so run once per release.

| Flip | Required output | Proves |
|---|---|---|
| Change C#3's price from 992,000 to a novel number (e.g. **877,500**) | extraction returns **877,500**, not 992,000 | the counter-sequence rule is a rule, not the memorized example (retires the Part 2 flag) |
| Reorder so the **latest** counter sets a lower price | extraction returns the **latest** counter's price | "higher-numbered counter wins" is truly sequence-driven |
| Blank a required signer in the controlling counter | `all_parties_signed = false` + the missing role named | signature judgment is evidence-driven, not forced true |
| Remove the listing-broker line + inject "For Sale By Owner" | `fsbo_reference = true` | FSBO is contract-driven, not forced false |
| Change EM counter "4 business" → "6 calendar days" | `earnest_money_days = 6`, basis **calendar** | EM window + basis are read, not fixed at 4/business |

### 5c · Determinism is not packet-specific
Run **each 5b variant 3×** and require identical output. This shows the determinism fix (temperature 0 + seed) holds for *different* content, not just the original packet.

**Exit for Part 3:** every flip produces the flipped, correct answer, and every variant is deterministic. That is direct evidence the solution generalizes and nothing is hard-coded.

---

## 6 · Part 4 — Regression safety (no new issues)

1. **Full backend suite** green — especially the extraction/backstop suite (title reads seller, inspection gated on waived, possession never overrides, signature backstop leaves genuinely-unsigned deals alone), intake, pipeline, and contract-resolution tests. These are independent synthetic scenarios that must all still pass.
2. **Full frontend suite** green — `tsc` clean and the WizardFlow integration suite (68 tests) passing, so the contingency-anchor and deal-brief changes didn't break the flow.
3. **Negative/edge assertions on the 10-PDF packet itself:** no false "referenced document missing"; the Pre-approval present ⇒ no "missing pre-approval" gap task; Amendment #1 not mis-flagged as a missing counter; no phantom contingency rows.
4. **Sibling checkbox fields** (Part 3 pattern): with FORMS mode on, spot-check that escrow holder, possession delivery, and financing-type reads on the packet are stable across the 3× determinism runs (they ride the same checkbox channel the title fix depends on).

**Exit for Part 4:** all suites green; no regression on the independent synthetic scenarios; the packet's negative cases hold.

---

## 7 · Exit criteria / sign-off checklist

The verification is complete only when every box is checked:

- [ ] **Part 1:** all 22 items verified on the simultaneous 10-PDF upload — extraction cluster and possession cluster on Track A + B; workflow items (12/14/15) on Track A after migrations; remaining items (9/13/17/18/20) verified once built.
- [ ] **Part 2:** diff reviewed; literal scan of product code returns zero packet answers; the single prompt example is the only exception and is queued for the price flip.
- [ ] **Part 3a:** all deterministic-layer flip tests pass (added to the unit suite).
- [ ] **Part 3b:** the representative LLM flips produce flipped, correct answers — in particular the **877,500 price flip** clears the counter-example flag.
- [ ] **Part 3c:** each variant is deterministic across 3 runs.
- [ ] **Part 4:** full backend + frontend suites green; packet negative cases hold.
- [ ] Track A run captured with **screenshots** at each wizard step (per the screenshot-gate invariant) for Jake/Audri sign-off.

---

## 8 · Risk register

- **LLM flips need network + keys and cost money.** Mitigation: cache the OCR once; keep 3b to a small representative subset run per release; make the deterministic 3a flips the everyday guard.
- **The prompt counter-example could bias the model.** Mitigation: the 877,500 flip test is mandatory; if it ever fails, abstract the example to generic tokens.
- **Determinism is best-effort at the provider.** Mitigation: temperature 0 is the primary lever; the seed is secondary; the 3× checks catch any drift, and the deterministic backstops backstop the critical fields regardless.
- **UI items (9/13/17/18/20) can't be screenshot-gated in a headless environment.** Mitigation: verify them in a real browser session before sign-off; they are specced field-by-field in the remediation plan.
- **Editing OCR text for flips must stay realistic.** Mitigation: change only the target token(s), keep surrounding structure (line numbers, confidence annotations) intact, so the flip exercises the real code path rather than a cleaned-up one.

---

**Bottom line:** Part 1 answers "is each issue resolved?" on Audri's exact 10-PDF simultaneous upload. Parts 2–4 answer "is it real, not hard-coded, and safe for other contracts?" — by a source audit, by flipping each value in the documents and requiring the output to flip with it, and by keeping every independent synthetic scenario green. A fix is accepted only when all three hold.
