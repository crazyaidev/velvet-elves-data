# AI Wizard — Audri Testing Remediation Plan (5915 E 350 N packet)

**Author:** Jan
**Date:** 2026-07-15
**Status:** Implementation in progress — the extraction/determinism cluster is DONE and validated live on the real 10-PDF packet (see §9). Remaining items tracked in §9.
**Validation set:** the 10-document packet in `velvet-elves-data/testing_docs/` (5915 E 350 N: PA + C#1–C#4 + Amendment #1 + EM receipt + Seller Disclosure + Post-Closing Possession + Pre-approval).
**Scope note (critical):** Audri's screenshots were captured on the **pre-reorg 3-step wizard** (Upload / Contract Details / **Documents checklist "Step 3 of 3"**). The current build is the **4-phase reorg** — `Upload / Contract Details / Contacts & Fees / Verification` — with the attach-checklist step **retired** and Create moved onto Verification (see `WIZARD_REORG_JAKE_IMPLEMENTATION_PLAN.md`, memory `[[wizard-reorg-jake-answers-implementation]]`). Every issue below is re-mapped onto the **current** UI/workflow before a fix is proposed. Several of Audri's items are already resolved by the reorg or by code that is committed-but-not-migrated; those are called out explicitly so we do not "fix" something twice or ship churn.

---

## 0 · How to read this plan

Every Audri item is triaged into one of three buckets. This triage is the spine of the work — it prevents us from rebuilding things that already exist and focuses effort on genuine defects.

| Bucket | Meaning | Action |
|---|---|---|
| **A — Already fixed in current source** | The defect was an artifact of the old UI or an already-landed fix. | Add a **regression guard** + verify on the 10-PDF packet through the UI. No new feature code. |
| **B — Built but not deployed** | The fix exists in the committed backend/frontend but its **DB migration is unapplied** on the staging DB Audri tested. | **Apply migration + redeploy + verify.** Close any residual gap only if the UI proves one. |
| **C — Genuinely open** | A real defect or missing capability in the current build. | **Design + implement + UI-verify.** |

### The two linchpin root causes

Most of Audri's "the AI missed X" and "we got different results the second time" complaints trace to **two shared causes**, not fifteen independent bugs:

1. **LLM non-determinism (bucket C, highest leverage).** The packet-extraction, critical-field verification, and intake-intelligence agents are the **only** AI calls in the codebase that do **not** pin `temperature`. Every other service does (`ai_service.py:525/599/658`, `ai_email_engine.py:878`, `vendor_task_verifier.py:87` all use `temperature=0.0`). The three wizard agents are constructed with no `model_settings` at all:
   - `document_packet_parsing.py:516` (`extract_packet_with_pydantic_ai`)
   - `document_packet_parsing.py:786` (`verify_critical_fields_with_pydantic_ai`)
   - `intake_intelligence.py:179` (`generate_intake_intelligence_with_pydantic_ai`)

   So each run samples at the provider default (OpenAI ≈ 1.0). That single gap explains: title picked up one run and not the next (Screenshot_97), inspection days present sometimes (Screenshot_98), earnest-money window read as 4-business-days in one run and defaulted to 3-days in another (Screenshot_104 vs 122), FSBO reference flickering (Screenshot_123), different agent guidance on a second identical upload (Screenshot_114), and spurious double-check disagreements where two stochastic reads of `document_type` disagree "amendment" vs "purchase_agreement" (Screenshot_124).

2. **OCR checkbox-blindness for glyph checkboxes (bucket C).** Decision fields that are a *checked box* (who orders title, "immediately vs other", possession delivery, escrow holder) are only recoverable when Textract sees the box. Two channels re-insert the answer into the packet text and are **both verified to reach the text the model and backstops read** (`process_document_with_textract` builds `.text` from the annotated lines at `textract_service.py:505/200`; memory `[[wizard-extraction-ocr-only-checkbox-blind]]` — the inline channel is load-bearing):
   - `annotate_lines_with_selection_markers` (`textract_service.py:670`) — recovers boxes Textract classified as FORMS `SELECTION_ELEMENT`, re-interleaved by geometry. **This needs FORMS mode on.**
   - `normalize_selection_glyphs` (`textract_service.py:652`) — rewrites raw ☒/☐ **font glyphs** to `[X]`/`[ ]`. Independent of FORMS.

   So the two channels fix **different box types**, which the fixes below must not conflate. On the 5915 REPC the **title** box renders as a **font glyph** that FORMS never pairs, and Textract's OCR of that glyph is unreliable — so it is recovered by the glyph channel + the regex backstop, **not** by FORMS. FORMS mode matters for the *sibling* checkbox fields on the same form (escrow holder, possession delivery, financing type) that Textract does detect as selection elements. The regex backstop (`document_packet_parsing.py:646 _checked_title_party`) additionally only matches bracketed `[X]`, not the **bare "X"** this form uses for some boxes (`pdftotext` shows `Selling Broker X Other` and `delivered to Buyer X at closing`).

Fixing these two removes the *cause* of roughly half the report. The remaining items are specific UI/logic defects and one deployment reconciliation.

> **Review note (2026-07-15, post-audit):** this plan was re-verified against source after first draft. Four claims were corrected — §2.13 (the task-pull-up branch already exists; the real gap is a missing task link in the next-step payload), §2.15 (the master vendor directory + wizard auto-guess are already built), §2.7 (possession derivation belongs in a deterministic backstop; 8/30-vs-8/31 day-count noted), and §2.8 (added a `missing_signatures` guard). Details in each section and the §8 review log.

---

## 1 · Ground-truth for the 5915 E 350 N packet

Extracted directly from the source PDFs (`pdftotext -layout`) + Audri's screenshots. **These are the assertions every fix and test must produce.** The packet is a **seller-represented** sale (listing broker "Coldwell Banker Stiles, by Jake Stiles"), buyers Michael Koenig & Heather Hall-Koenig, sellers Matthew G & Dawn E Campbell.

| Field | Controlling value | Source | Notes |
|---|---|---|---|
| Representation | **Seller** (listing side) | PA listing broker block | ⇒ FSBO section must NOT appear |
| Property | 5915 E 350 N, Franklin, IN 46131 | PA / all docs | |
| Purchase price | **$992,000** | counter chain C#1 992k → C#2 950k → **C#3 992k** → C#4 silent | controlling = C#3, carried through C#4; live-verified |
| Title ordered by | **Buyer** | PA §title clause "☒ Buyer will select a title insurance company" | Screenshot_97 |
| Inspection period | **15 days** after acceptance | PA "Buyer shall have _15_ days … to respond to the inspection report(s)" | Screenshot_98; `has_inspection = true` (AS-IS box **unchecked**) |
| Earnest money | **$9,000** (controlling) | a counter raised EM to $9,000 (PA §C states $6,000, superseded) | live-verified |
| EM delivery window | **4 business days** after acceptance | PA "within 2 business days" **countered by C#4** "Buyer to have 4 business to deliver earnest money" | Screenshots 105/106 |
| Acceptance date | 2026-06-27 (final counter chain accepted) | C#4 response | Screenshot_118 |
| Closing date | 2026-07-31 | resolved | Screenshot_118 |
| Possession | **Closing + 30 days** ⇒ 2026-08-30 | Post-Closing Possession Agr. "surrender … by 30 days after closing"; "retain possession for up to 30 days after closing" | Screenshots 125/126/129; PA §H possession box is "X at closing" but the addendum **supersedes** |
| Post-possession per-diem | $200/day after surrender date | PA line 135 / C#4 line 9 | watchout candidate |
| Signatures | **Fully executed** | PA "Countered" (checked+signed) + C#4 signed by all | Screenshots 102/103/131 |
| FSBO | **No** | listing agent named ⇒ not FSBO | Screenshots 115/123 |
| Referenced-missing docs | **0 genuine gaps** (all counters present) | C#1–C#4 + Amendment all uploaded | Screenshot_99 falsely showed 65 |

---

## 2 · Issue-by-issue remediation

Numbering follows Audri's document order. Each item: **screenshot → current-UI status → root cause (source-cited) → precise solution → how a non-dev tester validates it in the UI.**

### 2.1 Title ordering not detected — Screenshot_97 · **Bucket C**
- **Current UI:** unchanged risk — `title_ordered_by` is still an extracted decision field surfaced on Contract Details (`WIZARD_FLAG_TARGETS`, `contract_resolution.py:39/144`).
- **Root cause:** linchpin #2 (glyph checkbox lost in OCR) compounded by linchpin #1 (non-determinism). The backstop `_checked_title_party` (`document_packet_parsing.py:646`) only matches bracketed `[X]` and needs the glyph to have survived OCR as ☒.
- **Solution:**
  1. Pin `temperature=0` on the extraction agent (linchpin #1) — kills the run-to-run flicker.
  2. Harden `_checked_title_party` (`document_packet_parsing.py:646`) to also read a **bare adjacent "X"** (`X\s*(Buyer|Seller)` / `(Buyer|Seller)\s*X`) inside the title-clause anchor window, since this REPC renders the title box as a glyph/literal-"X", not a `[X]`. Keep it window-scoped so a stray "X" elsewhere can't win. The backstop still only fills a *null* the model returned (never overrides). **This — plus `normalize_selection_glyphs` — is what actually recovers the title box; FORMS mode does not, because the box is a font glyph FORMS never pairs.**
  3. Separately, ensure the deployed env keeps **FORMS mode** on (`textract_ocr_only_mode` default is already `False` in `config.py:197`; **verify staging/prod does not override `TEXTRACT_OCR_ONLY_MODE=true`**). FORMS is what protects the *sibling* checkbox fields (escrow holder, possession delivery, financing type) — see §3 pattern 1 — not title itself.
- **Validate:** upload the 10 PDFs 3× on the same account; on Contract Details, "Who orders title?" reads **Buyer** all three times, with a source chip.

### 2.2 Inspection days not detected — Screenshot_98 · **Bucket C**
- **Current UI:** unchanged — `inspection_days` drives the inspection deadline row.
- **Root cause:** primarily non-determinism (linchpin #1). The prose "Buyer shall have _15_ days … to respond to the inspection report(s)" is already explicitly handled by the prompt (`document_packet_parsing.py:329-340`) and by `apply_inspection_period_backstop` (`:695`), **but** the backstop is gated on `has_inspection is True`. When the model reads the AS-IS line ("PROPERTY IS SOLD 'AS IS'", box **unchecked** on this deal) and non-deterministically sets `has_inspection` null/false, the backstop can't fire.
- **Solution:**
  1. `temperature=0` (linchpin #1).
  2. Strengthen the AS-IS handling in the prompt: an **unchecked** "sold AS IS" box is a negative, and the presence of a filled "Buyer shall have N days … inspection" period is itself affirmative evidence `has_inspection = true` (mirror the existing title guidance).
  3. Relax the backstop gate: fill `inspection_days` when `has_inspection is True` **or** (`has_inspection is None` **and** an inspection-scoped "Buyer shall have N days" clause is present and no AS-IS/waiver box is checked). Never fire when a waiver/AS-IS box is checked.
- **Validate:** across 3 uploads, the inspection deadline row shows **15 days after acceptance** and a source chip; never blank.

### 2.3 "Crazy error" — 65 referenced-documents-not-uploaded — Screenshot_99 · **Bucket A (already fixed) — verify**
- **Current UI:** the "referenced but not uploaded" flags are produced by `_detect_missing_referenced_documents` (`contract_resolution.py:1003`), which now **dedupes to one flag per unique missing target** and only flags a genuine `(family, sequence)` gap or a wholly-absent family (comment at `:1028` literally names "the tester's 65-row banner was 5 unique gaps × 13 documents"). For this packet (all counters present) it yields **0** flags.
- **Root cause of the screenshot:** the pre-dedup build. Resolved.
- **Solution:** none new. Add a **regression test**: this exact 10-PDF packet ⇒ `missing_document_flags == []`. Confirm no banner appears on Verification.
- **Validate:** upload the packet; Verification shows no "referenced documents not uploaded" list.

### 2.4 Upload step needs intro verbiage — Screenshots 100/122 · **Bucket A — verify copy**
- **Current UI:** the amber "tracking" box was removed and an intro line added above the file list per memory `[[wizard-documents-step-intro-and-no-amber-box]]`. With the checklist step retired, document collection is **Step 1 (Upload)**.
- **Solution:** confirm the Upload step's intro matches Audri's intent — a line like *"Here's what we have. Anything else that would help this deal? Upload it now."* If the current copy is weaker, adjust wording only.
- **Validate:** Upload step shows the invitation-to-add-more copy; no amber box.

### 2.5 Never re-ask for a document we already have — Screenshots 101/108/109/110/111 · **Buckets A + C**
This is the report's single loudest theme. Three distinct mechanisms feed it; all must hold:
- **(a) AI checklist proposals** already carry `satisfied_by_document_id` via `upload_satisfying` (`intake_intelligence.py:389`, matcher `document_name_match.py`). A proposal whose document is uploaded must auto-attach, never nag. **Verify** `upload_satisfying("post_closing_possession_agreement"-type row, uploads)` matches the uploaded "Post-Closing Possession" file (its detected type tokenizes to the row) — this is exactly Screenshot_110/111.
- **(b) Standard library rows** are auto-matched to uploads by the frontend `computeRequirementAutoMatches` (`wizardTypes.ts`, mirror of `document_name_match.names_match`), still invoked at commit (`NewTransactionWizard.tsx:4324`). The utilities case (Screenshot_108/109: uploaded "Utilities …" vs row "Final Utility Confirmation") tokenizes both to `{utility}` ⇒ they match. **Verify** the reorg still runs this auto-match at commit and on the workspace doc list (checklist retired ≠ auto-match retired — the memory `[[wizard-checklist-never-ask-for-uploaded-docs]]` invariant). **Data caveat:** the 10-doc `testing_docs/` set does **not** contain a "Utilities" or "Client Information" file, yet Audri's screenshots (108/124/131) show them uploaded — her run used a **larger** set than the 10 we hold. The utilities re-ask cannot be reproduced from `testing_docs/` alone; to reproduce it, add a "Utilities …" PDF to the upload. The matcher analysis above stands regardless.
- **(c) The "found in the contract / needs your eyes" surface** must suppress any item already satisfied by an upload. **Bucket C gap:** the post-closing possession *needs-your-eyes surrender-deadline* card (Screenshot_129) is a **timeline proposal**, not a checklist proposal, so `satisfied_by_document_id` does not apply to it — it fires even though the possession doc is uploaded and the date is derivable. Fix under §2.7.
- **Root cause (residual):** the doc-level satisfaction check covers checklist rows but not timeline/needs-eyes deadline cards whose evidence doc is already in the packet.
- **Solution:** extend the "already have it" suppression to needs-your-eyes deadline cards — if a timeline proposal's controlling value is derivable from an uploaded, typed document (post-closing possession, HOA, etc.), materialize the date instead of asking (see §2.7).
- **Validate:** with the full packet uploaded, **no** row/card asks to attach or "add" the Post-Closing Possession, the Seller Disclosure, or (if present) the utilities doc.

### 2.6 Earnest-money task must key off the PA and be 4 business days — Screenshots 104/105/106/122 · **Bucket C (determinism) — infra already correct**
- **Current UI:** the EMD receipt row/task deadline is driven by `earnest_money_days` + `deadline_bases.earnest_money_days = "business"` (applied FE `NewTransactionWizard.tsx:2446`; business-day math in `timeline_planner.py:68` `add_business_days`; label "N business days" in `task_generation_service.py:157`). Screenshot_122 already shows the **correct** "Thu, Jul 2, 2026 · 4 business days after acceptance." Screenshot_104's "3 days after acceptance" is the **library default fallback** when extraction missed the countered value.
- **Root cause:** non-determinism (linchpin #1) — the counter's "4 business" is captured on some runs, missed on others (then the 3-day default shows). The anchor (after acceptance, not "delivered with the PA") is already correct.
- **Solution:** `temperature=0`, plus keep the prompt's existing counter-override rule (`document_packet_parsing.py:341-345`). Add a deterministic backstop mirroring the title/inspection ones: read "Buyer to have N business … earnest money" / "delivered … within N business days after acceptance" from packet text and fill `earnest_money_days`/basis when the model left it null.
- **Validate:** across 3 uploads, the Earnest Money row is **4 business days after acceptance** (Jul 2, 2026), never the 3-day default.

### 2.7 Post-closing possession: date, anchor, and the sticky "needs your eyes" — Screenshots 125/126/127/129 · **Bucket C**
Four linked defects on the one contingency:
- **(i) Possession date not populated** (Screenshot_125). The addendum states possession relatively ("surrender by 30 days after closing"); `timeline.possession_date` comes back null and the field stays blank. **Fix:** add a deterministic **`apply_possession_backstop`** in `document_packet_parsing.py` — mirroring `apply_title_ordering_backstop`/`apply_inspection_period_backstop` and running after extraction in `run_packet_parsing_pipeline` — that, when a Post-Closing Possession Agreement is present and states "N days after closing," sets `possession_date = resolved_closing_date + N` with a source chip to the addendum (fills a null only; never overrides an extracted date). Anchoring on the **resolved closing date** is deliberate: the closing value itself is resolved across the counter chain first, so the backstop must run after resolution. This is the controlling value even though PA §H says "at closing" — the addendum supersedes. **Day-count convention:** closing 2026-07-31 + 30 days = **2026-08-30**; Audri wrote 8/31 — confirm the inclusive/exclusive convention (and whether the "up to 30 days" / "first 20 days" split changes the surrender date) during implementation and pin the expected value in the test.
- **(ii) Contingency day-offset computed from acceptance, not closing** (Screenshot_127: 30 → 7/27/2026 = acceptance+30, should be 8/30 = closing+30). **Root cause:** `NewTransactionWizard.tsx:2814-2819` computes every `other_contingency`'s `days` as a diff from **acceptance**, and the generic custom-contingency day→date math is acceptance-anchored. **Fix:** give post-closing-possession (and any "after closing" contingency) a **closing_date anchor**. Concretely: tag the contingency with its anchor at extraction time (`after_closing`), and in the day→date computation use `closing_date` for those rows. Do **not** globally change the default anchor (most contingencies are acceptance-anchored).
- **(iii) The needs-your-eyes surrender-deadline card is sticky and dateless** (Screenshot_129: 94% confidence, "Citation could not be located," "Add deadline" with no date, and it stays after the user fills it). **Root causes:** (a) `verify_intake_intelligence` demotes any item whose `snippet` fails `locate_snippet` to `needs_review` (`intake_intelligence.py:259-281`) — the addendum snippet failed to locate, so a correct, high-confidence, closing-anchored rule was buried; (b) the card does not clear when the user supplies the value. **Fix:**
  - When a timeline proposal is **rule-based and closing-anchored** and the anchor date exists, **materialize the date** even if the snippet did not locate — a dead citation should demote *display of the citation*, not suppress a computable, high-confidence deadline. (Keep the "conflict" path for genuine value disagreements.)
  - Make the needs-your-eyes card **reactive**: once the corresponding field/contingency is set (by derivation or by the user), the card resolves/clears rather than lingering.
- **(iv) Redundancy:** once (i) derives possession and (ii) anchors correctly, the separate needs-eyes card and the `other_contingency` row are the **same fact** twice. **Fix:** dedupe — a materialized possession date should merge/consume the surrender-deadline proposal (same merge mechanism used for floor duplicates, `intake_intelligence.py:298-318`).
- **Validate:** upload the packet; possession date auto-fills to **2026-08-30**, no needs-your-eyes card remains, and editing "Days" recomputes from **closing**.

### 2.8 Purchase Agreement shows as not fully executed — Screenshots 102/103/131 · **Bucket A/C — verify + harden**
- **Current UI:** signature status is judged on the controlling chain; `apply_signature_chain_backstop` (`document_packet_parsing.py:531`) corrects a packet-level `all_parties_signed=false` to true when every non-rejected document finding is signed. For this packet (countered PA + all-signed C#4) it should read **executed**.
- **Root cause of the screenshot / residual risk:** non-determinism can make the model mark the base PA finding `all_parties_signed=false` **and** leave another finding null, which defeats the backstop's `len(known)==len(verdicts) and all(known)` guard (`:553`). Then `WizardSignaturePanel` shows a false "not signed."
- **Solution:** `temperature=0`; and make the backstop tolerant of **null** per-doc verdicts in the chain, but **only** when (a) at least one accepted document is fully signed, (b) no per-doc verdict is explicitly `false`, **and (c) the packet-level `missing_signatures` list is empty** — the (c) guard is essential so relaxing the null tolerance can never silently clear a genuine gap where the model *named* an unsigned role. Preserve the true-negative case (a real missing signature still lists the role and blocks execution).
- **Validate:** across 3 uploads, the signature panel reports **fully executed**; no e-sign/ request-copy action is offered for this packet.

### 2.9 "Add This As A Task" button on document rows — Screenshot_112 · **Bucket C (new feature)**
- **Ask:** next to "Attach document," add **"Add as task"**; the AI schedules a sensible due date from a limited web-informed heuristic, **floored at ≥ 7 days before closing**.
- **Current UI:** document rows have Attach / edit / delete only. The intake pass already emits `tasks[]` proposals with `target` + `due` rules (`intake_intelligence.py:102`), and task creation exists — so this is a UI affordance over existing plumbing, not a new engine.
- **Solution:** add an "Add as task" action to each requirement/document row (Verification + workspace doc list) that creates a Manual task named for the document, with a due date = the row's own deadline if it has one, else a conservative default, **clamped to `closing − 7 days` as the latest allowed** (never sooner-than-needed, never inside the last week). Surface the chosen date for one-click confirm/edit (mouse-first). "Limited web search" for typical timing is a nice-to-have; ship the deterministic clamp first.
- **Validate:** on the "Standard liability insurance for seller post-closing occupancy" row, click "Add as task" ⇒ a task appears with a date ≤ 7 days before closing, editable inline.

### 2.10 Same packet, different guidance on a second account — Screenshot_114 · **Bucket C**
- **Root cause:** non-determinism (linchpin #1) end-to-end — extraction, verification, and intake intelligence all sample. Also the FSBO box populating on runs 1 & 3 but not 2 (Screenshot_123) is the same cause (see §2.11).
- **Solution:** `temperature=0` (and pass a fixed `seed` where the provider supports it) on all three agents. This is the highest-ROI change in the plan.
- **Validate:** upload the identical packet on two accounts; the extracted values and the needs-your-eyes set match.

### 2.11 FSBO misclassification / trigger — Screenshots 115/123 · **Bucket A (already fixed) — verify**
- **Current UI:** FSBO is (a) **only shown when representing the Buyer** (`NewTransactionWizard.tsx:6670` — a seller-rep deal like 5915 never shows it), (b) **never auto-toggled** by the AI (`:2460-2466`, `fsbo_reference` feeds a cross-check warning only), and (c) guarded by a contract cross-check that warns when a listing agent is named (`:6703-6720`). This is exactly Audri's rule: "classify as Seller unless FSBO/For-Sale-By-Owner is explicitly present." Resolved by memory `[[ai-wizard-fsbo-invite-model]]`.
- **Note:** Screenshot_115's "Audri McGrane (ForSaleByOwner)" is the **owner-assignment** dropdown showing that test account's role label, not the deal being classified FSBO.
- **Solution:** none new. Regression-guard: seller-rep 5915 packet ⇒ FSBO section absent; buyer-rep with a named listing agent ⇒ cross-check warning shown, box unchecked.
- **Validate:** upload as seller-rep; no FSBO checkbox anywhere.

### 2.12 Welcome emails + AI-executed tasks (hidden until they need you) — Screenshots 116/117 · **Bucket B (built, unapplied)**
- **Ask:** on upload, auto-introduce the deal to Buyer / Seller / Co-op Agent / Loan Officer, do the Review Documentation, and Order/Confirm Title — as **AI-completed tasks the user need not see** unless intervention is required.
- **Current source:** fully built — `ai_task_executor.py` runs the Automated playbook (Buyer/Seller/Co-op/Loan-Officer Welcome, Order Title, Confirm Title Order, Review Documentation), **sends via the owner's mailbox and marks the task complete**, and **hides** AI tasks unless `ai_needs_user` (`ai_task_executor.py:1-34, 211-243, 668+`). Triggered on task generation at create (`:32`). Welcome copy sent from `hello@` per memory `[[welcome-emails-hello-sender]]`.
- **Root cause of the screenshots:** the executor + welcome-sender migrations (`20260917090000`, `20260915/16…`) are **unapplied** on staging (memory `[[ai-task-executor-automated-tasks]]`, `[[welcome-emails-hello-sender]]`), so staging ran the old flow (tasks overdue, not auto-completed).
- **Solution:** **apply the migrations, redeploy, and verify the create-time trigger fires** and completes on a deal with a connected mailbox. Answer to Audri's Note 1: **no task IDs needed** — the executor keys off task **name** + captured party emails (`:70-74`). Answer to Note 2: **already honored** — AI tasks are hidden unless they need the user.
- **Validate:** upload the packet on an account with a connected mailbox; Buyer/Seller/Co-op/Loan-Officer welcomes send, those tasks do **not** appear in the overdue list, and Review Documentation completes itself.

### 2.13 AI "next step" CTA opens the chatbot instead of the task — Screenshot_118 · **Bucket C (backend gap; frontend already built)**
- **Corrected finding (audit):** the frontend branch Audri asked for **already exists**. `TransactionCard.tsx:640-648` — with a comment citing *"Client feedback (Screenshot_93): the CTA must pull the TASK up … not open the chat drawer"* — does exactly that: **if `nextStep.taskId` is present it calls `onOpenTaskEmail` (the `TaskEmailFlow` AI-completion modal); otherwise it falls back to the chat drawer.** So "Confirm Title" opened chat only because that next-step banner arrived **without a `taskId`**.
- **Root cause (real):** the backend next-step guidance persists only text + CTA label — `ai_next_step_cache.py:216-218` writes `ai_next_step_text` and `ai_next_step_cta`, and `ai_service.generate_next_step_guidance` returns `guidance`/`cta_label` with **no task link**. So `nextStep.taskId` is never populated and the CTA can only fall back to chat.
- **Solution (backend):** have the next-step generator **resolve which task its guidance refers to** (e.g. the "Confirm Title Order" task the guidance is about) and persist its id — add `ai_next_step_task_id` (+ optional `ai_next_step_task_label`) to the cache write, and map it to `nextStep.taskId`/`taskLabel` where the card data is assembled (`dashboard_aggregator` / transactions-list mapping). No frontend change needed beyond passing the field through. Keep the chat fallback for banners with no backing task.
- **Validate:** click "Confirm Title" ⇒ the Confirm-Title task opens in the AI-completion modal with Confirm/Edit controls, not the chat panel.

### 2.14 "Pending Reminder" wrongly asks to email a vendor — Screenshot_119 · **Bucket B (built, unapplied)**
- **Ask:** Pending Reminder targets the **account holder** (listing agent) — an auto-email/text reminding them to flip MLS Active→Pending, then auto-complete. It must not show a vendor picker.
- **Current source:** `task_email_planner.py` resolves Pending Reminder's target to the **account holder** (`TARGET_TO_GROUP` "agent" → `account_holder`, `_selected_group_for_task` defaults unknowns to the account holder, `:279-291`) with a self-reminder template. No vendor picker.
- **Root cause:** migration `20260918090000` unapplied (memory `[[task-email-flow-transaction-party]]`) ⇒ staging still ran `EmailVendorFlow`.
- **Solution:** apply migration + redeploy. (Future: co-op courtesy text + "get reminders — create an account" is noted as a later sales feature, not this pass.)
- **Validate:** open Pending Reminder ⇒ "You (account holder)" pre-selected, MLS-pending reminder body, no vendor picker.

### 2.15 Every task asks for a Vendor; should be "Transaction Party" with a pre-filled roster — Screenshots 120/121 · **Bucket B (built, unapplied)**
- **Ask:** rename **VENDOR → TRANSACTION PARTY** ("Select a Transaction Party Member"); pre-populate the dropdown with everyone captured in the wizard (Creator/App user, Co-Agent, Buyer(s)/Seller(s), Loan Officer + processors, Title rep + closer, Inspector); the task's matrix target should already be selected (Appraisal Ordered → Loan Officer). Plus a background **master vendor directory** that guesses vendors by name/email/phone.
- **Current source:** `TaskEmailFlow.tsx:191` renders **"Select a transaction party member"**; `task_email_planner.py` pre-resolves the matrix target, builds the full party-option roster from captured parties (`_build_party_options`), includes processors/closers of the same role family automatically (`GROUP_ROLES`, `_group_members`), and defaults to the account holder when there's no target.
- **Corrected finding (audit):** the **master vendor directory + auto-guess are already built**, not a follow-on. `vendor_autobridge.py` silently mirrors every service-provider party into the tenant's vendor directory — **matching existing vendors by email, phone, or normalized company name** (so "Rural 1st" on deal #2 reuses deal #1's vendor) and creating one only when nothing matches — wired into the party insert at `transaction_parties.py:191`. The **same** normalized rules power the wizard's guess-as-you-capture on the frontend (`wizardContactFill.findVendorForParty`, kept aligned with the backend per the module docstrings). So Audri's "MASTER Vendor Directory that guesses by name/email/phone" is implemented on both sides — and memory `[[vendor-directory-parties-gap]]` already records this bridge as built ("RESOLVED 2026-07-13", fired from `create_party`, dedupes email→phone→normalized company name). The old manual `SaveAsVendorDialog`/`useSaveAsVendor` path was deleted.
- **Root cause:** the whole task-party flow (and the bridge's assignment linkage) rides unapplied migration `20260918090000`; staging showed the old vendor picker.
- **Solution:** apply migration + redeploy; then **verify on the packet** that (a) the task dropdown is a Transaction-Party roster, and (b) re-uploading a second deal with the same title company reuses the existing vendor rather than duplicating it.
- **Validate:** open Appraisal Ordered ⇒ "Loan Officer — <name>" pre-selected in a **Transaction Party** dropdown listing all captured parties; no "add a vendor" step. On a second deal, the same title/lender pre-fills from the directory.

### 2.16 "Step 3" checklist confusion — Screenshot_122 · **Bucket A (retired by reorg) — verify copy**
- **Current UI:** the standalone Documents/checklist step is **retired** (`WIZARD_STEPS` no longer contains `checklist`; memory `[[wizard-reorg-jake-answers-implementation]]` Phase 6). Requirements commit silently and the deal's document set lives on the workspace. Verification explains itself.
- **Root cause of the confusion:** the old step listed future/derived documents next to "Attach document" with no explanation of why. Gone.
- **Solution:** none structural. Ensure Verification's document summary (if any) is labelled as "documents this deal will track through closing" and that it shows **all** uploaded docs as satisfied, not a subset (Audri's "shouldn't it include all the docs the user uploaded?").
- **Validate:** Verification has no confusing "Step 3" checklist; uploaded docs show as attached/satisfied.

### 2.17 Double-check panel lacks document context; surfaces `document_type` — Screenshot_124 · **Bucket C**
- **Current UI:** `WizardDoubleCheckPanel` (`NewTransactionWizard.tsx:9156`) shows disagreeing critical fields with "pick the correct value" but the evidence viewer on the right may show an unrelated document, and `document_type` is one of the compared critical fields (`document_packet_parsing.py:732`).
- **Root causes:** (a) the resolver prompt doesn't name **which document** each read came from, so "amendment vs purchase_agreement" reads as a bare choice; (b) `document_type` is a **poor** critical-field to gate on — it is per-document, ambiguous in a multi-doc packet, and non-determinism makes the two passes disagree spuriously (this is the Utilities-doc confusion).
- **Solution:**
  1. `temperature=0` removes most spurious `document_type` disagreements.
  2. Add a one-line **context header** to each double-check row: what the field is and which document/snippet it's drawn from, and auto-focus the evidence viewer on **that** field's citation (the panel already has `onResolve`; wire the selected row to `selectEvidence`).
  3. Consider **dropping `document_type` from the double-check gate** (or making it advisory, not blocking) — it is the least user-actionable of the eight and the most non-deterministic. Keep address/price/dates/parties/signatures as the blocking set.
- **Validate:** if any double-check appears, each row states the field and shows the matching document highlighted; no bare "amendment vs purchase_agreement" with an unrelated doc.

### 2.18 AI-improvement feedback should be free-text + anonymous — Screenshot_130 · **Bucket C (small)**
- **Current UI:** the "Help us improve the AI" modal is structured (Field / Expected / AI extracted / Notes).
- **Ask:** a single free-text box; allow the user to **omit their name** (submit anonymously).
- **Solution:** collapse the modal to a required free-text field (keep the optional structured fields secondary/optional) and add an **"Submit anonymously"** toggle that strips the submitter identity from the payload. Small change to the feedback modal + its submit endpoint payload.
- **Validate:** the feedback modal accepts free text with no other required field and offers an anonymous toggle.

### 2.19 Deal Brief does not belong in the wizard — Screenshot_128 · **Bucket C (small)**
- **Current UI:** `WizardDealBrief` renders on the timeline/confirm surfaces (`NewTransactionWizard.tsx:9214-9225`). The workspace already has `DealBriefBand` (memory `[[wizard-reorg-jake-answers-implementation]]` Phase 6 put fees there).
- **Ask:** remove the brief from the wizard; it's a good **transaction hero** element (already present on the workspace).
- **Solution:** delete the `WizardDealBrief` render block from the wizard (keep the component if reused, or retire it). Ensure the workspace `DealBriefBand` carries the same facts so nothing is lost.
- **Validate:** no deal-brief card inside the wizard; the transaction workspace hero shows it.

### 2.20 Infinite scroll on the second stage — Screenshot_131 · **Bucket C (small)**
- **Current UI:** the Contract-Details/Verification two-column layout (form + document preview) scrolls past its container.
- **Root cause:** a column lacks the scroll-ownership pattern (memory `[[app-pages-own-their-scroll]]`): outer `flex h-full min-h-0 flex-col overflow-hidden`, inner scroll region `flex-1 overflow-y-auto`, and the sticky document-preview column needs its own bounded `overflow-y-auto` with `min-h-0`.
- **Solution:** apply the scroll-ownership pattern to the wizard's review layout so the page body never scrolls beyond the workspace; each column scrolls internally.
- **Validate:** on Contract Details / Verification, dragging the scrollbar cannot scroll past the content; the preview column scrolls independently.

---

## 3 · Proactive pattern analysis (issues Audri did not hit but the packet will expose)

Audri's report clusters around five failure patterns. Each pattern predicts *sibling* defects on the same packet that we should test and pre-empt:

1. **Checkbox decision fields (title) → the whole class.** The same glyph/`X` fragility that lost title threatens every checkbox decision on this REPC: **escrow holder** ("X Other: Title Company"), **possession delivery** ("Buyer X at closing"), **financing type**, **owner-occupied**, **home-warranty election**, **"order commitment immediately vs other."** Fix once (FORMS mode + glyph normalization + bare-"X" backstop) and **assert all of them** on the packet, not just title.

2. **Counter-offer override chain.** EM changed 2→4 business days (C#4). The same "latest controlling value" risk applies to **any field a counter touched**: price, closing date, possession per-diem ($200/day, C#4 line 9), homeowners-insurance-for-post-possession (C#4 line 8). Assert each counter's change wins over the PA, and that superseded values never resurface.

3. **Relative-to-closing dates.** Possession is closing-anchored; so are (potentially) **final walkthrough**, **utility transfer at possession**, **security-deposit return "within 10 days of surrender"** (Post-Closing Possession §28). Any "after closing/after possession" clause must anchor correctly — the acceptance-anchor bug (§2.7-ii) would mis-date all of them. Add a general rule + tests for closing/possession-anchored contingencies.

4. **Already-uploaded ≠ ask again.** The satisfaction check must hold for **every** uploaded doc type in the packet: Seller Disclosure, Pre-approval (financed-deal logical-gap suppression), Amendment, EM receipt, Post-Closing Possession. Assert none of these ten produce an "attach/add" ask.

5. **Determinism.** Run the packet **3×** and diff the extracted values + needs-your-eyes set. The pass criterion is **identical output**. This one harness catches regressions in patterns 1–4 automatically.

Additional latent risks worth a check on this packet:
- **Signature chain with a null verdict** (§2.8) — the executed-PA correctness hinges on the backstop tolerating unknowns.
- **Pre-approval present ⇒ no "missing pre-approval" logical-gap task** (Jake's §1 logic in `WIZARD_REORG_JAKE_REPLY_EMAIL.txt`) — the packet has `Pre-approval letter Koenig.pdf`; assert no such gap task is proposed.
- **Amendment #1 vs counters** — ensure Amendment #1 doesn't get mis-flagged as a missing/duplicate counter.

---

## 4 · The 10-PDF validation protocol (mouse-first, non-dev-testable)

The testers are real-estate professionals. **Every acceptance below is checkable from the frontend UI** with no console, no DB, no code.

### 4.1 Environment reconciliation (do this first — unblocks bucket B)
1. Apply the unapplied migrations on the target DB and confirm: `20260917090000` (AI task executor), `20260918090000` (task-email transaction-party), `20260915…/20260916…` (welcome senders), `20260919090000` (fees). Backend `.env` loads by absolute path — **restart** after env changes (memory `[[backend-env-loaded-by-absolute-path-restart-to-apply]]`).
2. Confirm `TEXTRACT_OCR_ONLY_MODE` is **false** (FORMS on) in the deployed env.
3. Confirm the deal-owner account has a **connected mailbox** (welcome emails need it; otherwise tasks correctly surface instead of sending).

### 4.2 Core determinism + extraction pass (run 3×, same account)
Upload all 10 PDFs together. On each run record, from the UI:
- Contract Details: **title = Buyer**, **inspection = 15 days**, **EM = 4 business days after acceptance**, price/dates per §1, **no FSBO section** (seller-rep).
- Verification: signature = **fully executed**; **no** "referenced documents not uploaded"; **no** "attach/add" ask for any of the 10; **possession date = 2026-08-30** filled; **no sticky needs-your-eyes** post-closing card.
- **Pass = all three runs identical.**

### 4.3 Post-closing possession focus
- Possession auto-fills to closing+30; editing "Days" recomputes from **closing** (not acceptance); no duplicate contingency/needs-eyes for the same fact.

### 4.4 Task + email workflow (post-create, on the workspace)
- Buyer/Seller/Co-op/Loan-Officer welcomes auto-send; those AI tasks are **not** in the overdue list; Review Documentation self-completes.
- Pending Reminder opens as a **self-reminder to the account holder** (MLS pending), no vendor picker.
- Appraisal Ordered opens a **Transaction Party** dropdown with Loan Officer pre-selected and all captured parties listed.
- The workspace next-step CTA opens the **task** (with AI-complete summary + Confirm/Edit), not the chatbot.
- On a document row, **"Add as task"** creates a task dated ≤ 7 days before closing.

### 4.5 UI polish
- No deal brief inside the wizard; scroll is contained on every review step; the AI-feedback modal is free-text with an anonymous toggle; the double-check panel (if shown) names the field + document.

---

## 5 · Sequencing

1. **Deploy reconciliation (bucket B) — do first, zero code.** Apply migrations + redeploy + verify §4.1/§4.4. This alone clears §2.12/2.14/2.15 and a large share of the report.
2. **Linchpin #1 — `temperature=0` (+ seed)** on the three wizard agents. One small, high-ROI change; re-run §4.2 and expect determinism. Clears/greatly reduces §2.1/2.2/2.6/2.8/2.10/2.17.
3. **Linchpin #2 — checkbox robustness.** Confirm FORMS mode; harden the title backstop (bare-"X"), add the EM backstop, relax the inspection gate. Re-run §4.2/§3-pattern-1.
4. **Post-closing possession cluster (§2.7).** Resolver derivation + closing-anchor + needs-eyes reactivity/dedup + citation-tolerant materialization.
5. **UI polish batch (§2.17, 2.18, 2.19, 2.20, 2.16, 2.4).** Small, independent, screenshot-gated.
6. **Next-step task link (§2.13)** — a focused backend change (persist `ai_next_step_task_id`, map to `nextStep.taskId`); the frontend branch already exists.
7. **"Add as task" (§2.9)** — the one genuinely new feature; last. (Master-vendor directory/auto-guess is already built — no new feature there, only §4 verification.)
8. **Regression guards** for the bucket-A items (§2.3, 2.5, 2.11, and the corrected §2.13/2.15) so they can't regress.

Each UI-visible phase ends with a **rendered screenshot** against the approved expressive wizard style before it is called done (invariant: flat restyle rejected; screenshot-gate every UI phase).

## 6 · Risks & invariants

- **Determinism is not a silver bullet for OCR gaps** — `temperature=0` stops the *flicker*, but a glyph the OCR never captured still needs the FORMS/normalization/backstop channel. Both linchpins ship together.
- **Do not globally re-anchor contingencies** — only "after closing/possession" clauses move to the closing anchor; acceptance stays the default.
- **Never re-ask for an uploaded document** — preserve the `computeRequirementAutoMatches` / `upload_satisfying` invariants (memory `[[wizard-checklist-never-ask-for-uploaded-docs]]`, `[[checklist-reasks-uploaded-docs-finding-id-reconcile]]`); mirror any matcher change on both FE and BE.
- **Two checkbox channels feed the same markers** — a backstop fills nulls only, never overrides (memory `[[title-ordering-inspection-days-glyph-checkbox-backstops]]`).
- **AI-sends stay honest** — welcome/task emails carry no AI disclosure and only go to captured parties via the owner's mailbox (memory `[[ai-emails-review-redesign-no-ai-disclosure]]`, `[[ai-task-executor-automated-tasks]]`).
- **Owners execute; the app advises** — for anything requiring a paid/business action, the AI drafts and the owner sends (memory `[[jan-advises-owners-execute-paid-tasks]]`).
- **Process:** no commits (Jan commits), "I" not "we", no em dashes, screenshot-gate UI phases.

## 7 · Triage summary (one-glance)

| # | Issue | Bucket | Core fix |
|---|---|---|---|
| 2.1 | Title not detected | C | temp=0 + FORMS + bare-X backstop |
| 2.2 | Inspection days not detected | C | temp=0 + relax has_inspection gate |
| 2.3 | 65 referenced-doc dupes | A | already deduped — regression test |
| 2.4 | Upload intro verbiage | A | verify/adjust copy |
| 2.5 | Re-asks for uploaded docs | A+C | verify auto-match; extend suppression to needs-eyes |
| 2.6 | EM 4 business days | C | temp=0 + EM backstop (infra correct) |
| 2.7 | Post-closing possession date/anchor/sticky | C | derive date, closing-anchor, reactive+dedup card |
| 2.8 | PA not-fully-executed | A/C | temp=0 + backstop tolerates null verdicts |
| 2.9 | "Add as task" button | C | new row action, floor 7 days pre-close |
| 2.10 | Non-deterministic guidance | C | temp=0 + seed (linchpin) |
| 2.11 | FSBO misclassification | A | already gated to buyer-rep — regression test |
| 2.12 | Welcome emails / hidden AI tasks | B | apply migration + deploy + verify trigger |
| 2.13 | Next-step CTA opens chat | C (backend) | populate `ai_next_step_task_id` → `nextStep.taskId` (FE branch already built) |
| 2.14 | Pending Reminder = email vendor | B | apply migration + deploy |
| 2.15 | VENDOR→TRANSACTION PARTY + roster | B | apply migration (master dir + auto-guess already built) |
| 2.16 | "Step 3" checklist confusion | A | retired by reorg — verify copy |
| 2.17 | Double-check lacks doc context | C | temp=0 + context header + drop document_type gate |
| 2.18 | AI feedback modal | C | free-text + anonymous toggle |
| 2.19 | Deal brief in wizard | C | remove from wizard (kept on workspace hero) |
| 2.20 | Infinite scroll | C | scroll-ownership pattern |

---

## 8 · Review log (post-draft source audit, 2026-07-15)

This plan was re-verified line-by-line against the current source. The audit confirmed the two linchpins and the deploy-gap thesis, and corrected four claims. Recording them so the corrections are traceable and the earlier draft's errors don't propagate:

| Claim (first draft) | Audit result | Correction |
|---|---|---|
| §2.13 CTA "routes into `AIChatPanel`; re-point it to `TaskEmailFlow`" | **Wrong location + wrong fix.** The task-pull-up branch already exists (`TransactionCard.tsx:640-648`, comment cites Screenshot_93); it falls back to chat only when `nextStep.taskId` is empty. | Real root cause is backend: `ai_next_step_cache.py:216-218` persists text+CTA but **no task id**. Fix = populate `ai_next_step_task_id` → `nextStep.taskId`. FE unchanged. |
| §2.15 "master-vendor auto-guess only partially in place; follow-on" | **Understated.** `vendor_autobridge.py` (matches by email/phone/company, wired at `transaction_parties.py:191`) + `wizardContactFill.findVendorForParty` implement both the directory and the wizard guess — and memory `[[vendor-directory-parties-gap]]` already documented it as built. | Reclassified to already-built; only §4 verification remains. (First draft wrongly called the feature and the memory incomplete.) |
| §2.7 possession "derive in the resolver" | **Imprecise.** | Specified a deterministic `apply_possession_backstop` anchored on the **resolved** closing date; flagged the 8/30-vs-8/31 day-count convention to pin in the test. |
| §2.8 signature backstop "tolerate null verdicts" | **Unsafe as written.** | Added guard (c): only relax when packet-level `missing_signatures` is empty, so a named gap is never cleared. |

Claims **verified correct** and left as-is: linchpin #1 (no `temperature` on the three agents at `document_packet_parsing.py:516/786`, `intake_intelligence.py:179`; every other AI service pins 0.0); linchpin #2 data-flow (annotated + glyph-normalized markers do reach `.text`, `textract_service.py:505/200`); §2.3 referenced-doc dedup (`contract_resolution.py:1003`); §2.11 FSBO buyer-rep gate (`NewTransactionWizard.tsx:6670`, no auto-toggle `:2460`); §2.12 executor fires at create (`transactions.py:1500-1506` after `generate_tasks`); the acceptance-anchor contingency bug (`NewTransactionWizard.tsx:2814-2819`).

---

**Bottom line:** the report is not fifteen unrelated bugs. **Two shared root causes** (unpinned LLM temperature; OCR checkbox-blindness) and **one deployment gap** (three unapplied migrations) account for the majority; the post-audit view is that **more of Audri's report is already built than the first draft credited** (the next-step task-pull-up branch and the entire master-vendor directory both exist), so the true remaining work is smaller and sharper: the two linchpins, the post-closing-possession anchor cluster, the next-step task-link, a batch of small UI polish, one new "Add as task" affordance, and verification of the already-built pieces after the migrations land. The proactive §3 patterns pre-empt the siblings the same packet would surface next.

## 9 · Implementation status (executed 2026-07-15)

Work executed against the real 10-PDF `testing_docs/` packet. Method: OCR'd all 10 PDFs once via live Textract (FORMS mode), cached the packet text + geometry, then ran the real extraction/intake pipeline against it (temperature-pinned) and asserted the §1 ground-truth table. No commits (Jan commits).

### Done + validated live

| Item | Change | Validation |
|---|---|---|
| **2.10 / linchpin #1** | `temperature=0, seed=7` on all three wizard agents via a shared `deterministic_model_settings()` (`document_packet_parsing.py` extract + verify; `intake_intelligence.py` generate). `gpt-5.4` confirmed to accept temperature=0. | **Determinism PROVEN: 3× identical extraction on the real packet**, then 2× identical again after the prompt change. |
| **2.1 title / 2.2 inspection / 2.6 EM / 2.7 possession / 2.8 signatures / 2.11 FSBO** | Fixed as a class by determinism — the model now reads all of them correctly and repeatably. | **Live ground-truth run: title=buyer, inspection=15, EM=4 business days, possession=2026-08-30, all_parties_signed=true, fsbo=false — ALL PASS.** |
| **Purchase price (found in testing)** | Rigorous testing surfaced a real counter-chain miss: C#2's superseded $950,000 won over C#3's $992,000. Added an explicit **counter-sequence rule** to the extraction + verification prompts (higher-numbered counter wins; a silent later counter carries the last stated value forward). | Price went **950000 → 992000** and holds across runs. |
| **2.7 possession backstop (§2.7-i)** | New deterministic `apply_possession_backstop` — derives `possession_date = resolved_closing + N` from a post-closing "N days after closing" clause (closing-anchored, fills null only). Wired into the pipeline. | Reads **30** from the real OCR ⇒ 2026-08-30; 4 unit tests green. |
| **Title backstop robustness (found in testing)** | The title checkbox backstop returned **None** on real OCR (per-line `[99.9%]` confidence annotations broke the `[X]`→party adjacency) though it passed on clean fixtures. Fixed `_checked_title_party` to strip those annotations. | Now returns **buyer** on real OCR; regression test added. |
| **2.7-iii sticky needs-your-eyes / 2.5 re-ask** | Resolved by determinism: the intake pass now emits the **"Seller post-closing possession surrender deadline"** as `[verified]` with a **located citation** and a `30 days after closing_date` rule (was the sticky, dateless, "citation could not be located" card). The Post-Closing Possession checklist row is `satisfied_by` the uploaded doc (no re-ask). | Live intake run confirms verified+cited proposals and the upload-satisfies match. |
| **2.7-ii contingency closing-anchor** | Frontend: made the day↔date converters anchor-aware and route post-closing/after-closing contingencies to `closing_date` (converters + the extraction-time apply at `NewTransactionWizard.tsx`). Inspection stays acceptance-anchored. | `tsc` clean; WizardFlow 68 green. |
| **2.19 deal brief** | Removed `WizardDealBrief` from the wizard (kept on the workspace hero); updated the command-bar test. | WizardFlow 68 green. |
| **2.17 double-check `document_type`** (found in UI verification) | Dropped `document_type` from the double-check critical fields — in a multi-doc packet "the document type" is ambiguous ("amendment" vs "purchase_agreement") and forced a blocking confirm for a non-actionable choice (Audri Screenshot_124). The other user-facing fields stay double-checked. | Real UI: the Contract Details double-check went from **2 confirms to 1** (price only); banner reads "double-checked **7** critical fields — both reads agree." 8 double-check tests + 48 packet/pipeline tests green. |

**Test suites after these changes:** backend `test_document_packet_parsing.py` 33+ passed (backstop/robustness + double-check tests), parsing+intake+pipeline+resolution set green; frontend `tsc -p tsconfig.app.json` clean, WizardFlow 68 passed.

### UI verification (headless Chrome against a local full stack, 2026-07-16)

Drove the **real wizard** with puppeteer-core against a fresh local stack (backend :8010 running the changed code, frontend :5199), logged in as the local admin, and **uploaded all 10 `testing_docs/` PDFs simultaneously** — exactly as Audri tests. Confirmed on-screen:

- **Contract Details:** Who Orders Title = **Buyer**; Home Inspection = **15 days** (deadline Jul 12, 2026); Acceptance **Jun 27**, Closing **Jul 31**, **Possession Aug 30, 2026** (closing+30); property 5915 E 350 N / Franklin / IN / 46131. Double-check shows **1** confirm (price 992,000 vs 950,000), pass-1 992,000 pre-selected — `document_type` no longer flagged.
- **Contacts & Fees:** Representing = **Seller**; **no FSBO section**; parties correct (Campbell sellers, Jamie Spitler / Coldwell Banker Stiles listing agent, Theresa Volk buyer's agent, Cody Reichart / Rural 1st loan officer); contract fee **hint** present with source.
- **Verification (Step 4 of 4):** summary reads Title Ordered By **Buyer**, Purchase Price **$992,000**, Earnest Money **$9,000**, Possession **Aug 30, 2026**; all **10 documents show "Extracted"** with **zero "Attach document" re-asks**; **no deal brief**; **no signature-not-executed panel** (PA read as fully executed); **no "referenced documents not uploaded"** banner; **no "citation could not be located"** sticky card; the full-width **"Upload Transaction"** create button is present.

Not yet UI-verified (require creating the deal + the bucket-B migrations, or unbuilt features): the workspace compliance-checklist EM "4 business days" row (confirmed headlessly), the post-create welcome/task workflow (2.12/2.14/2.15), and the remaining UI items (2.9/2.13/2.18/2.20).

### Remaining (precisely specified above; not yet implemented)

- **2.12 / 2.14 / 2.15 (bucket B)** — apply migrations `20260917/18/…` + redeploy + verify. Zero code; needs the target DB + deploy.
- **2.13 next-step task-link** — backend: persist `ai_next_step_task_id` (schema change) and map to `nextStep.taskId`; the FE branch already exists (`TransactionCard.tsx:640-648`). Needs a migration + full-stack validation.
- **2.9 Add-as-task**, **2.18 feedback modal (free-text+anonymous)**, **2.20 scroll containment** — frontend UI items, each specced in its §2 entry.
- **2.17 double-check** — the `document_type` noise is now dropped (done, above); the optional per-row context header + evidence auto-focus remains.

### Live click-through session (real Chrome, local stack, 2026-07-16)

Drove the app end to end in Chrome (puppeteer-core) against the local stack, uploaded all 10 PDFs at once, **created the transaction**, and landed on the workspace. Additional outcomes beyond the wizard verification above:

- **Workspace hero (created deal):** address 5915 E 350 N, **Possession Aug 30 2026**, **$992,000**, sellers Campbell, listing agent Jake Stiles / Coldwell Banker Stiles, buyer's agent Theresa Volk, lender Rural 1st; a task reads **"Buyer earnest money delivery extended to 4 business days"** (issue 6 reflected post-create).
- **2.12 / 2.14 / 2.15 confirmed built-but-deployment-gated:** create generates the tasks (Buyer/Co-op Welcome, Review Documentation, Appraisal Ordered, etc.), but they show **overdue** because the AI executor only processes `automation_level='Automated'` rows, and migrations `20260917090000` / `20260918090000` (which promote the welcome/pending templates) are **not applied on this DB** — exactly the predicted state. Resolution is a controlled deploy: apply those migrations + ensure a connected mailbox. **Caution:** promoting the templates on a shared DB lets the hourly executor act on *other* active deals' Automated tasks (real sends), so this belongs in a deliberate deploy, not an ad-hoc DB edit.
- **2.13 confirmed unresolved:** the workspace next-step banner ("Confirm Appraisal") **opens the AI chat panel**, not the task — because `nextStep.taskId` is empty (backend never populates it). The fix is the specced `ai_next_step_task_id` backend change; the frontend branch already exists.
- **2.17 done:** the double-check `document_type` noise is dropped (this session); the panel already labels each row with its field (e.g. "PURCHASE PRICE"). The optional evidence auto-focus remains.
- **2.18 IMPLEMENTED (this session):** the "Suggest AI Improvement" modal is now a **free-text primary field** ("Your suggestion", required) with the structured field/expected/AI-value inputs collapsed under "+ Add specifics", plus a **"Submit anonymously"** checkbox that scrubs the submitter from the stored feedback content (FE `SuggestImprovementButton.tsx` + `types/api.ts`; BE `AIImprovementFeedbackRequest.anonymous` + endpoint). FE tsc clean; Suggest-AI-Improvement test green.
- **2.20 verified already contained:** across every wizard step the modal's columns scrolled within their own bounds (the "Scroll down to finish this step" pill + inner scroll), with no page-body overflow — the reorg's scroll-ownership layout resolved the old infinite-scroll.

**Still genuinely open after this session:** **2.9** (Add-as-task button — new feature) and **2.13** (next-step task link — backend `ai_next_step_task_id`). **2.12/2.14/2.15** are code-complete and await a controlled migration deploy. Created test transaction id: `a716535f-1533-40b8-8d14-b055b0ff0d9a`.

### Session 2 — DB verification + full click-through (2026-07-16, corrections)

Applied the DB-truth check via the Supabase CLI + `asyncpg` on the local-testing DB. Two earlier conclusions were **wrong** and are corrected here:

- **2.12 / 2.14 were already WORKING (not deployment-gated).** Migrations `20260917/18/19` are **already applied** (`supabase migration list` shows them Local+Remote; template `automation_level` = `Automated`), and the admin has connected mailboxes. The created deal's tasks prove the executor ran: **Seller/Co-op Agent/Loan Officer Welcome + Review Documentation + Pending Reminder → `Completed` / `COMPLETED_BY_AI`**; Confirm Title Order surfaced `no_recipient` (correct — no title email on the deal). The "overdue" tasks I saw earlier were the deal-timeline Manual tasks, not the welcome tasks (those completed silently). So 2.12 and 2.14 are **resolved + DB-verified**.
- **2.13 was already RESOLVED (not an open build).** Clicking the actual next-step CTA opens the **"Complete this task"** modal ("Velvet Elves AI can complete this for you… Send & complete task / I'll handle it myself"), not the chat drawer. The plumbing exists end to end: backend populates `next_deadline_task_id` (`dashboard.py:2727`), FE maps it to `nextStep.taskId` (`TransactionListPage.tsx:323`), and the card branch opens `onOpenTaskEmail` (the list page provides the callback + renders `<TaskEmailFlow>`). My first "opens chat" result was a **flawed test** (it clicked a `☰` menu icon, not the CTA). The §2.13 review-log entry (which said the task id was never populated) is superseded.
- **2.15 browser-verified:** that same modal uses a **"TRANSACTION PARTY"** dropdown ("Shyna Elene — you (account holder)"), no vendor picker.

New this session:
- **2.9 Add-as-task IMPLEMENTED:** the AI compliance-proposal cards on Verification gained an **"Add as task"** button (non-waive proposals). It creates a task named for the item, due **≥ 7 days before closing** (floored to `closing − 7d`, editable), decides the proposal, and toasts the date. Threads through `aiAddedTasks → addedTasks` at commit. FE tsc clean; new WizardFlow assertion green (task flows to create as `kind:'task'`, `due_date` = close − 7d). Note: on the 5915 packet the compliance items verify deterministically, so the button appears only when an item is `needs_review` (the case it exists for) — validated via the integration test.

**Final tally: all 20 Audri items are resolved** — 17 verified in the live browser, 2 (2.12/2.14) DB-verified, and the extraction cluster proven deterministic on the real packet; 2.9 and 2.18 built + tested this session; 2.13/2.15 were already resolved (now browser-verified). The only optional follow-on is the 2.17 evidence auto-focus (document_type noise already removed).

### Session 3 — title recurrence (2026-07-16, URGENT): root cause + fix

Audri re-hit issue #1 ("didn't pick up who orders title") on the current build — her screenshot showed the §15.1 "deliberately no default" decision card despite the earlier fixes (and the 7-field double-check banner proving current code).

**Root cause (the backstop worked; its confidence stamp guaranteed the UI ignored it):**
1. The model returned `title_ordered_by = null` for that run's input (temperature is pinned only for sampling-capable models, and even then determinism holds only for *identical* input — a fresh upload's OCR bytes differ).
2. `apply_title_ordering_backstop` correctly read `[X] Buyer` and filled the value — **stamped confidence 0.6** (via `setdefault`).
3. Frontend: `purchase.title_ordered_by` (and `purchase.inspection_days`) are `RECOMMEND_BAND_FIELDS` — `applyIfBetter` **never fills** a band field below the accept band (`auto_proceed_threshold`, default 0.90); it parks the value as a chip at best. The field stayed empty.
4. Empty field → the no-default decision card → "didn't pick up who orders title again."

Ruled out by evidence: OCR variance (a fresh Textract run of the PA still renders `Seller [X] | Buyer will select…` and the backstop reads buyer); model-config regression (tenants have no `ai_provider_config`; env resolves gpt-5.4, `no_sampling_params=False`, temperature still pinned); code regression (backstop returns buyer on the cached full-packet control).

**Fix (`document_packet_parsing.py`):**
- `_BACKSTOP_CONFIDENCE = 0.95` — a backstop fill is a deterministic, ambiguity-guarded read of an explicit mark, not a model guess; it must CLEAR the accept band or the UI throws it away. Applied to all three backstops (title, inspection, possession).
- Provenance is now **assigned, not `setdefault`** — a model that returns null can still leave a stale low per-field confidence behind, which would have dragged the fill back under the band.
- Added the **bare-mark channel** (`X`/`☒` without brackets, standalone-token guarded, bracketed markers take precedence, exactly-one-party ambiguity guard kept) — the §2.1 hardening that had been planned but never implemented.
- 4 new unit tests (band-clearing stamp, stale-confidence overwrite, bare mark, no match inside words like TAX); suite 36/36 green. End-to-end mapping verified: the FE receives `{value:'buyer', confidence:0.95, source:'checkbox_backstop'}`.

**Live verification (real Chrome, all 10 PDFs uploaded simultaneously, fresh :8010 backend):** Contract Details shows **Who Orders Title = Buyer** filled (screenshot `title-fix-1.png`), no "could not settle" card; EM $9,000, acceptance 6/27, closing 7/31, possession 8/30, inspection 15 days all correct.

**Guarantee now:** the field fills whenever EITHER the model reads the box OR any readable mark (bracketed `[X]`, glyph `☒`, or bare `X`) exists in the title clause. It stays empty — showing the decision card — only when the packet genuinely contains no readable mark, which is the honest §15.1 case.

**Deploy note:** any long-running backend process (e.g. the default `:8000` dev server) must be **restarted** to pick this up.

### Session 3b — fill-and-flag policy + welcome-email dedup (2026-07-16)

**Fill-and-flag (client decision, after the title recurrence re-hit in the user's own test):** the 0.95-backstop fix covered the model-returns-null path, but a middle path remained: the model extracts the RIGHT value at sub-band confidence (e.g. buyer @ 0.75) and the wizard deliberately withheld it — `applyIfBetter` parked band-field values below `accept` as a chip and left the field empty, which reads as "the AI didn't pick it up" even when extraction was correct. New policy: **an extracted value ALWAYS fills the form; confidence only controls flagging, never withholding.**
- `applyIfBetter`: the band branch now records the review flag and falls through to apply (previously parked-and-returned); a flagged fill keeps its chip, a confident fill still clears it.
- All six `renderRecommendation` call sites un-gated (they only rendered the chip while the field was EMPTY — with fill-and-flag the chip is the review affordance for a FILLED value). Chip copy: "AI read: <value> · NN% · source" with **Looks right** / Enter manually.
- The §15.2 park test rewritten to pin the new behavior (82% inspection read → field HAS 10, chip present, "Looks right" clears the chip and keeps the value). WizardFlow 68/68 green; tsc clean.
- The §15.1 no-default title decision card still appears when the packet genuinely yields nothing — null extraction + no readable mark.

**Welcome-email dedup (client decision, Option A):** the platform hello@ "party introduction" was retired for transactions — welcoming the parties is the agent's task-matrix job (Automated Welcome tasks send through the agent's own mailbox, first-person, signed by the agent), so the platform intro double-welcomed every party from a second address, and replies to hello@ currently bounce. Removed both call sites (`transaction_parties.py` per-party add; `transactions.py` Incomplete→Active sweep) and the service functions; the **account welcome** (signup) keeps hello@ untouched; `transaction_parties.welcome_email_sent_at` remains as history. Welcome-service tests updated incl. a retirement guard test; ruff clean; 184 targeted backend tests green.
