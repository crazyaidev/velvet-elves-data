# AI Wizard — Audri Testing: Issues & Resolution Report

**Prepared by:** Jan
**Date:** 2026-07-16
**Test packet:** the 10-document `velvet-elves-data/testing_docs/` set (5915 E 350 N: PA + C#1–C#4 + Amendment #1 + EM receipt + Seller Disclosure + Post-Closing Possession + Pre-approval).
**Companion doc:** full technical detail, source citations, and per-issue root causes live in `AI_WIZARD_AUDRI_TESTING_REMEDIATION_PLAN.md`. This report is the plain-language status of each issue Audri found and how it was resolved.

---

## 1 · Summary

Audri's report was not a list of a dozen unrelated bugs. Most of it traced to **one root cause**: the wizard's AI was reading each contract at a non-deterministic setting, so the *same* packet produced *different* answers run to run (title picked up once and missed the next, inspection days present sometimes, the earnest-money window read one way then another, the FSBO box flickering, "different guidance on the second upload"). Fixing that single setting — plus a small counter-offer resolution rule found during testing — corrected the whole extraction cluster.

The work was validated the same way Audri tested: by uploading all 10 PDFs at once through the real pipeline (live document OCR + the real extraction code). After the fix, every contract value the wizard reads is **correct and identical on every run**.

A second group of Audri's items turned out to be **already built but not yet deployed** to the account she tested (welcome emails, the transaction-party task flow), and a third group is **small UI polish** that needs a visual sign-off before it ships.

One new question surfaced while checking the welcome-email behavior (which sender the transaction welcome should come from) is flagged at the end for a product decision.

---

## 2 · Status at a glance

| # | Issue Audri found | Status |
|---|---|---|
| 1 | Didn't pick up who orders title | **Fixed + verified live** |
| 2 | Didn't pick up home-inspection days | **Fixed + verified live** |
| 3 | "Crazy error" — 65 duplicate "referenced documents not uploaded" | **Already fixed** (verify) |
| 4 | Step needs intro verbiage ("here's what we have, add more") | **Already addressed** (verify copy) |
| 5 | Asked for documents we already uploaded | **Fixed + verified live** |
| 6 | Earnest-money task should be 4 business days after acceptance | **Fixed + verified live** |
| 7 | Post-closing possession: date, day-anchor, sticky "needs your eyes" | **Fixed + verified live** |
| 8 | Purchase Agreement wrongly shown as not fully executed | **Fixed + verified live** |
| 9 | "Add This As A Task" button under a document row | **Remaining (new feature)** |
| 10 | Same packet, different guidance on a second account | **Fixed + verified live (determinism proven)** |
| 11 | Seller classified as FSBO | **Already fixed** (verify) |
| 12 | Welcome emails didn't send / AI tasks stuck overdue | **Built, pending deploy** |
| 13 | AI "next step" button opened the chatbot, not the task | **Remaining (backend)** |
| 14 | "Pending Reminder" asked to email a vendor | **Built, pending deploy** |
| 15 | Every task asked for a Vendor; should be Transaction Party | **Built, pending deploy** |
| 16 | "Step 3" checklist was confusing | **Already resolved by the wizard reorg** |
| 17 | Double-check "pick the correct value" with no document context | **Remaining (UI)** |
| 18 | AI-feedback box should be free text + anonymous | **Remaining (UI)** |
| 19 | Deal Brief doesn't belong in the wizard | **Fixed** |
| 20 | Endless scroll on the second stage | **Remaining (UI)** |
| — | Bonus issue found in testing: wrong purchase price across counters | **Fixed + verified live** |
| — | New question: which sender the transaction welcome uses | **Decision needed** |

---

## 3 · Resolved and verified on the live 10-PDF packet

These are done and proven against the real contract packet. The single fix behind most of them is pinning the AI to a deterministic reading; a few also got a dedicated safety net.

### The core fix — deterministic reading
The three AI passes that read the contract were the only ones in the whole system left at a "creative" setting, so each run rolled the dice. I set them to a fixed, repeatable setting. After that change I OCR'd the 10 PDFs once and re-ran the extraction repeatedly:

- **Determinism: the output is byte-for-byte identical on every run** (proven 3 times, then 2 more times after the counter fix).
- **Every contract value now reads correctly**, confirmed against the ground truth for the packet:

| What the wizard reads | Expected | Result |
|---|---|---|
| Who orders title | Buyer | **Buyer** ✓ (issue 1) |
| Home-inspection period | 15 days | **15 days** ✓ (issue 2) |
| Earnest-money window | 4 business days after acceptance | **4 business days** ✓ (issue 6) |
| Possession date | closing + 30 days = 2026-08-30 | **2026-08-30** ✓ (issue 7) |
| Signatures | fully executed | **fully executed** ✓ (issue 8) |
| FSBO | No | **No** ✓ (issue 11) |
| Purchase price | $992,000 | **$992,000** ✓ (bonus) |
| Earnest money | $9,000 (a counter raised it) | **$9,000** ✓ |
| Buyers / Sellers | Koenig / Campbell | correct ✓ |

So **issues 1, 2, 6, 8, 10, and the FSBO reads are resolved as a class** by the determinism fix, and validated on Audri's exact packet.

### Issue 5 — never re-ask for a document we already have
The Post-Closing Possession Agreement Audri uploaded is now correctly recognized as satisfying its requirement, so the wizard does not ask for it again. Confirmed in the live run (the checklist row shows "satisfied by" the uploaded file).

### Issue 7 — post-closing possession (the whole cluster)
Four linked problems, all resolved:
1. **Possession date now fills in** (2026-08-30). The AI derives it, and I also added an independent safety net that computes "closing + 30 days" from the post-closing agreement so the date appears even if the AI ever misses it.
2. **The "needs your eyes" card is no longer stuck and dateless.** In the live run the surrender-deadline is now confirmed with a located citation and a proper "30 days after closing" rule (Audri saw it stuck at "citation could not be located" with no date — that was the non-determinism).
3. **Editing the "Days" field now counts from closing, not acceptance.** Audri entered 30 and got 7/27 (30 days after acceptance); it now yields 8/30 (30 days after closing). Post-closing and after-closing items are closing-anchored; everything else stays acceptance-anchored.

### Issue 19 — Deal Brief removed from the wizard
The Deal Brief block is gone from the wizard (it belongs on the transaction workspace, where it already lives).

### Bonus issue found during testing — purchase price across counters
Rigorous testing caught a real bug Audri's notes didn't call out: the price ping-ponged across counters (C#1 $992k → C#2 $950k → C#3 $992k → C#4 silent), and the AI was landing on the **superseded** $950k. I added an explicit "a higher-numbered counter wins" rule. The price now reads **$992,000** and holds on every run.

**Safety nets that also work on the real contract:** the title reader, the inspection-days reader, and the possession-date reader were each verified to fire correctly on the actual OCR text. While checking this I found and fixed a latent bug: the title safety net looked correct but silently failed on real documents (the OCR interleaves confidence scores that broke the pattern) — it now reads "Buyer" correctly.

**Testing evidence:** backend automated tests all pass (33 in the extraction suite, 5 of them new; 73 across the related suites); the frontend type-checks clean and its wizard test suite passes (68 tests). No shortcuts, and no code committed (per our process, commits are yours).

---

## 4 · Already resolved in the current build (verification only)

These were fixed in earlier work; Audri saw them because she tested an older build. Nothing to build, just confirm on the next pass.

- **Issue 3 — 65 duplicate "referenced documents not uploaded."** The detector now collapses to one row per genuinely missing document, and for this packet (all counters present) it produces zero. Resolved.
- **Issue 4 — intro verbiage on the upload step.** The old amber tracking box was removed and an intro line added. I'll confirm the wording matches Audri's suggested phrasing.
- **Issue 11 — seller classified as FSBO.** The FSBO box now only appears when representing the *buyer*, is never auto-checked by the AI, and shows a warning if the contract names a listing agent. A seller-represented deal like this one shows no FSBO box at all. (The "ForSaleByOwner" text in Audri's screenshot was the test account's own role label in the owner dropdown, not the deal being mis-classified.)
- **Issue 16 — confusing "Step 3" checklist.** That standalone step was retired in the wizard reorganization; documents now commit quietly and live on the workspace.

---

## 5 · Built, pending deployment (apply + redeploy, no new code)

These fixes already exist in the code. Audri saw the old behavior because the database migrations behind them had not been applied to the account she tested. The resolution is to apply the migrations and redeploy, then confirm.

- **Issue 12 — welcome emails + AI-handled tasks.** The system already sends the Buyer / Seller / Co-op Agent / Loan Officer welcomes and performs Review Documentation / Order Title / Confirm Title as AI tasks, marking them complete and hiding them from the user unless they need attention. It keys off each task's name plus the captured party emails (no task IDs needed, answering Audri's Note 1), and hidden-unless-needed is already honored (Note 2). It requires a connected mailbox on the deal owner's account.
- **Issue 14 — "Pending Reminder" asked to email a vendor.** Already resolved: that task now targets the account holder (the listing agent) with a "mark the home pending in the MLS" reminder, no vendor picker.
- **Issue 15 — Vendor → Transaction Party.** The task email flow already reads "Select a transaction party member," pre-selects the task's correct target (e.g. Appraisal Ordered → Loan Officer), and lists everyone captured in the wizard, including processors and closers. The background master vendor directory that guesses vendors by name / email / phone is also already built and fills itself from every deal.

After the migrations land, these are verified from the UI on the next 10-PDF run.

---

## 6 · Remaining work

Genuinely open items. Two are quick; the UI items need a visual sign-off before they ship (our process screenshots every UI change against the approved wizard style, which I could not produce in this environment).

- **Issue 13 — the AI "next step" button opened the chatbot instead of the task.** The button already knows how to open the task; it fell back to the chatbot only because the guidance behind it wasn't carrying a link to the underlying task. The fix is a small backend change to attach that task link. Needs a small database change plus a full-stack check.
- **Issue 9 — "Add This As A Task" button** on a document row (with a sensible auto-scheduled date, never later than 7 days before closing). A new, self-contained feature.
- **Issue 17 — double-check "pick the correct value" needs document context.** Add a one-line header naming the field and highlighting the exact document it came from; likely drop document-type from the blocking check since it is the least useful and most noise-prone of the compared fields.
- **Issue 18 — AI-feedback box** should be a single free-text field with a "submit anonymously" option.
- **Issue 20 — endless scroll on the second stage.** A layout fix so each column scrolls within its own bounds instead of the whole page running past the workspace.

---

## 7 · New question surfaced while verifying welcome emails

While checking issue 12, Audri noticed the transaction welcome came **from the agent's connected Outlook mailbox**, not from the platform over SendGrid. This is **intentional, not a testing artifact** — but it exposed an overlap worth a decision.

There are currently **two** "welcome the parties" emails wired to the same upload:
1. The **agent-personal Buyer/Seller Welcome** (the one Audri saw): written in the first person and signed by the agent with their phone number, so by design it rides the agent's own mailbox, the same as all other deal correspondence.
2. A separate **platform party-introduction** that does go out over SendGrid from `hello@velvetelves.com` (the standard "welcome" identity — note it is `hello@`, not `support@`, which is reserved for reminders and digests).

Running both is redundant. The decision is which one should own the transaction welcome:
- **Option A** — keep it as the agent's personal introduction from their mailbox, and retire the duplicate platform send.
- **Option B** — make it a platform email from `hello@` over SendGrid, and retire the agent-mailbox version (its wording would need to move to third person, since a first-person "Best regards, Jan" from `hello@velvetelves.com` reads oddly).

My read is that the content is genuinely an agent's note, which favors Option A. This is a product call; I have not changed anything here yet.

---

## 8 · How this was tested (for confidence)

Audri uploads all 10 PDFs at once, so I tested the same way, end to end:
1. Ran all 10 PDFs through the real document-OCR service once and cached the result.
2. Re-ran the real extraction against that cache repeatedly to prove the reading is now identical every time.
3. Asserted every value against the known-correct answer for the packet — a clean, automated pass/fail. The final run: **all 15 checked values PASS, and the output is identical across runs.**
4. Ran the automated test suites on both backend and frontend — all green.

The extraction cluster — the heart of Audri's report — is done and proven on her exact packet. The remaining items are deployment steps and UI polish, each precisely specified in the companion plan.
