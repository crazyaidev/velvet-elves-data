# AI Wizard Intake Integrity — Analysis & Remediation Plan

**Status (2026-07-13, approved by Jan; same-day implementation):**
- **Phase 1 — IMPLEMENTED** (uncommitted): A1 chain-signature rule in both prompt passes + deterministic `apply_signature_chain_backstop`; A2 earnest-money window end-to-end (extraction `timeline.earnest_money_days` + `deadline_bases` key → typed models → `_BASIS_TERM_FIELDS` → resolver `SCALAR_FIELDS` → transactions column via migration `20260914090000` **(UNAPPLIED — Jan applies)** → repo/create/preview → `requirement_planner` emd_receipt override with business-day math → wizard apply/submit); A4 `document_name_match.py` + FE `documentNamesMatch` token matcher (address-noise stripping, stemming, generic-token guard) + compliance vocabulary offered to `documents[].document_type` + utilities alias; A5 verifier `satisfied_by_document_id` → wizard auto-accepts + auto-attaches (never "needs your eyes"); A7 `detection.fsbo_reference` extraction + Purchase-Info listing-agent cross-check warning + FSBO-block copy + owner-resolution rejects Client/FSBO roles; B5 closing−7d pull-back for added to-dos landing in the final week (contract deadlines and post-closing tasks untouched; enforced in the generation path only — explicit user rule edits in the workspace/Review steps are NOT clamped, since "walkthrough 1 day before closing" is legitimate intent).
- **Phase 2 — A3 IMPLEMENTED** with the recommended treatment (two groups: "Documents you may have now" + collapsed "Collected as the deal progresses"; user-added and AI rows always stay in the main group); **A6 NOT implemented** (needs Jake: timing table contents + no-live-web-search trade-off).
- **Phase 3 — not started** (B1 registry, B2 term_windows).

**Date:** 2026-07-13
**Trigger:** Client testing round on Wizard Step 3 (Documents) + FSBO classification (Screenshots 80–91).
**Method:** Every root cause below was traced in current source (`NewTransactionWizard.tsx`, `WizardChecklistStep.tsx`, `wizardTypes.ts`, `document_packet_parsing.py`, `intake_intelligence.py`, `requirement_planner.py`, `contract_resolution.py`, `providers/prompts.py`, requirement seed migration `20260817100000`), not inferred from the reports.

**Reading the reports together, they are not seven random bugs.** Five of the seven trace to three systemic flaws: (1) the wizard's document-matching joins three *different* document-type vocabularies with exact string comparison; (2) contract-stated deadline windows have extraction slots for only four hardcoded fields, so every other window silently falls back to a library default; (3) intake surfaces (checklist rows, AI proposals, signature status, FSBO) assert things about the deal without checking what intake *already knows* (the uploaded documents, the extracted parties). Part A analyzes each report; Part B names the systemic flaws; Part C is the phased plan.

---

## Part 0 — Already fixed this round (uncommitted; client tested an older build)

The build the client tested predates this week's uncommitted work. Two of the reported symptoms are already partially addressed:

- **Rows asking for uploaded documents** (PA row "Attach document", Screenshot 80/82): `computeRequirementAutoMatches` (`wizardTypes.ts`) now auto-attaches uploads to rows one-to-one by per-document detected type (alias-mapped) and by normalized filename ↔ row-name equality, driving both the step display and the commit. The PA, EMD receipt, and lead-paint cases are covered. **But it does not yet cover Screenshots 86–89** (utilities, post-closing possession) — exact-match is too brittle for real filenames; see A4/A5.
- **Step 3 verbiage + amber box** (prior feedback): intro prompt added, amber box gated to the AI-unavailable case.

These need the client to retest on the current build; the plan below covers what remains.

---

## Part A — Reported issues: root cause and countermeasure

### A1. "Not fully executed" on a fully-executed countered contract (Screenshots 80/81)

**What happened.** The PA's seller-response section has "☒ The above offer is Countered" — sellers signed the PA *and* the counter-offer; the packet is fully executed. The wizard still behaved as if it were not (signature decision panel appears when packet `all_parties_signed === false`, `NewTransactionWizard.tsx` ~8626; a `false` also feeds review reasons via the double-check).

**Root cause.** Neither extraction pass has **chain semantics** for signatures. The prompts say "all_parties_signed: true only if every required signature block is signed" (`prompts.py`, `CRITICAL_FIELDS_VERIFICATION_INSTRUCTIONS`) — on a countered PA the "Accepted" box is unchecked and the model reads the *base document* as not accepted/executed, even though the checked "Countered" box + a signed counter is exactly how a fully-executed deal looks. The client's rule is correct: a packet is unexecuted **only when a required party never signed anywhere in the controlling chain**.

**Countermeasure.**
1. Add the chain rule to **both** prompt passes (established invariant: domain definitions go into both, or they manufacture double-check disagreements): *"A PA whose seller response is 'Countered' plus a counter-offer signed by all parties IS fully executed at the packet level; judge all_parties_signed on the controlling chain (base agreement + accepted counters/amendments), not on the base document's acceptance boxes."*
2. Deterministic backstop in `contract_resolution.py`: when every document in the controlling chain (`FAMILY_ORDER` walk, acceptance-status-aware) has `all_parties_signed=true` per its own finding, the resolved packet value is `true` regardless of the base-PA read.
3. `WizardSignaturePanel` copy: state *which* document/party is missing a signature (from `missing_signatures`), so a false flag is instantly diagnosable.

**Effort:** S (prompts) + M (resolution backstop + tests).

### A2. Earnest-money deadline ignores the contract: "3 days" vs "2 business days, countered to 4 business days" (Screenshots 82/83/84)

**What happened.** The EMD Receipt row shows the library default "3 days after acceptance" (seed `20260817100000`, `due_days=3`, calendar). The contract says EM delivered "within **2 business** days after acceptance", and Counter #1 changed it to **4 business days**. The committed deadline is simply wrong for this deal.

**Root cause.** There is **no extraction slot for the EM delivery window anywhere in the system** — `TimelineExtraction` has inspection/response/HOA/insurance day counts only, `_BASIS_TERM_FIELDS` (`providers/parsing.py:98`) lists the same four fields, and no transaction column exists (verified: `earnest_money_days` appears nowhere in the backend). The contract term physically cannot flow, so the library default always wins. Counter-override logic is irrelevant while the field doesn't exist.

**Countermeasure** (the full chain, same pattern as the inspection-days fix):
1. Extraction: `timeline.earnest_money_days` (int) + `deadline_bases.earnest_money_days` in `EXTRACTION_OUTPUT_SCHEMA`, the typed `TimelineExtraction` (the drift-guard test enforces parity), both prompt passes' window guidance ("EM delivered within N days" → `earnest_money_days`; counters override the count — extend the existing controlling-value rule to name EM explicitly).
2. Mapping: `_BASIS_TERM_FIELDS` += `earnest_money_days`; `json_to_extraction_result` passthrough; `contract_resolution` field list += it (counters resolve it).
3. Transaction column `earnest_money_days` (+ ride the existing `deadline_day_basis_json` for its basis) — migration, Jan applies.
4. Consumption: the emd_receipt requirement row and the EM task template resolve their due rule from `wizard:earnest_money_days` when set (the planner already supports `wizard:<field>` offsets and `effective_day_basis` does business-day math); library `3 days` stays as the fallback when the contract is silent. Wizard shows the contract-derived basis label ("4 business days after acceptance") with its citation.

**Effort:** M. **Dependency:** one migration.

### A3. Future documents "should not be listed here" (Screenshot 85)

**What happened.** Step 3 lists Loan Application Evidence, Inspection Report, Appraisal, Title Commitment, CD, Deed… as rows with prominent "Attach document" buttons. The client's mental model of this step is *"what do you already have?"* — documents that can only exist later read as nonsense asks. (This got worse when the explanatory amber box was removed at their request: the list lost its "this is tracking, not asking" frame.)

**Root cause.** Information architecture, not data: one flat list conflates two populations — documents that can exist **now** (executed PA, disclosures, receipts, pre-approval) and documents produced **during** the transaction (CD, deed, title commitment…). The checklist itself is correct (the workspace must track all of them); the *presentation as asks at intake* is wrong.

**Countermeasure.** Two-group layout in `WizardChecklistStep`:
- **"Documents you may have now"** — rows whose doc_type is in an intake-plausible set OR that auto-matched an upload; full row UI with Attach.
- **"Collected as the deal progresses"** — everything else, **collapsed by default** behind a one-line summary ("12 more documents will be tracked through closing — view/adjust"), rows expandable with edit/waive but no prominent Attach CTA.
- Grouping key: a static `INTAKE_PLAUSIBLE_DOC_TYPES` set (purchase_agreement, emd_receipt, lead_paint_disclosure, sellers_disclosure, pre_approval_letter, proof_of_funds, hoa_package, referral/agency docs) — deterministic and editable; *not* inferred by the LLM.
- Everything still commits exactly as today (preview = commit unchanged); this is purely presentation.

**Effort:** M (component + integration test + screenshot). **Decision for Jake:** collapse-with-summary (recommended — keeps tester's ability to adjust rows pre-create) vs removing future rows from the step entirely.

### A4. Utilities uploaded, still asked (Screenshots 86/87)

**What happened.** "Utilities - 5915 E 350 N.pdf" is uploaded; the "Final Utility Confirmation" row still asks.

**Root cause.** Both auto-match signals miss: the extraction's document-type enum has no utilities type (the finding will be `other`, which deliberately never type-matches), and normalized-name **equality/containment** fails ("utilities 5915 e 350 n" vs "final utility confirmation" share only a word stem). Exact-match joins across vocabularies are the systemic flaw (B1).

**Countermeasure** (layered, all deterministic):
1. **Classify against the real vocabulary:** the packet extraction's `documents[]` instructions get the *actual requirement-library doc_type list* (it's small and stable — 18 types) appended as allowed `document_type` values, so the model can say `utility_confirmation` directly instead of `other`. The enum in `EXTRACTION_OUTPUT_SCHEMA` becomes "one of: …library types…, or the contract-family types". No new model calls.
2. **Token-similarity fallback** in `computeRequirementAutoMatches`: significant-token overlap with light stemming (utility/utilities) and **address/date-token stripping** (drop tokens matching the deal's address digits/street tokens — filenames like "X - 5915 E 350 N.pdf" are the tester's norm). Threshold high (e.g. all row-name significant tokens present, or ≥0.75 overlap), one-to-one claiming unchanged, manual always wins. Unit-test the exact reported filenames.
3. Alias map += `utilities`/`utility_bill` → `utility_confirmation`.

**Effort:** M. Item 2's matcher is shared with A5.

### A5. "Needs your eyes" proposal for a document that is already uploaded (Screenshots 88/89)

**What happened.** The AI proposed "Post-Closing Possession Agreement" (from contract terms, 99%) as a needs-review checklist add — while "Post-Closing Possession - 5915 E 350 N.pdf" sits in the upload list. The client accepts the proposal mechanism ("if there wasn't a document uploaded, this would be appropriate") — the failure is proposing to *collect* what intake already has.

**Root cause.** `verify_intake_intelligence` (`intake_intelligence.py:232`) verifies proposals against citations and the deterministic floor, but **never against the upload set** — even though it already receives everything needed (`extracted["_packet"].documents` carries file names; `document_findings` carries per-doc types).

**Countermeasure.**
1. Server: the verifier runs the same similarity matcher (port of A4's token matcher) between each checklist proposal's name and the packet's file names + detected types. A hit tags the proposal `satisfied_by_document_id` (kept, not dropped — the deal should still track the document).
2. Wizard: a `satisfied_by_document_id` proposal is **auto-accepted and auto-attached** — it never renders in "Found in the contract — needs your eyes"; it appears directly in the checklist as an AI row showing "Uploaded · <filename>" with its citation chip. The needs-your-eyes section is reserved for proposals that actually need a decision.
3. The frontend matcher (A4.2) independently covers the same case at display time — two layers, same deterministic rule.

**Effort:** M (server matcher + tag + wizard handling + tests).

### A6. "Add This As A Task" under Attach Document (Screenshot 90) — new feature

**What the client wants.** On rows the user won't have up front (their example: seller's post-closing liability insurance), a second action: **Add as a task**, scheduled at "the most common time to perform the task" relative to closing, with a floor: **never later than closing − 7 days**. They suggested the AI "does limited web search".

**Honest constraint:** there is no web-search infrastructure — `AIService.search_public_source` is a deliberate stub (documented limitation §9), and adding live browsing is a real project, not a button. The client's *outcome* (a sensibly-dated task without the user picking a date) does not require browsing.

**Countermeasure.**
1. Row action "Add as task" (secondary, next to Attach) on every unmatched row → creates a wizard added-task (`kind:'deadline'`-adjacent, source `manual`/`ai`) through the existing added-tasks channel — the deterministic planner dates it, preview = commit holds.
2. Timing: a **curated per-doc-type timing table** (server, editable constants: e.g. insurance binder → closing − 10d; utility confirmation → possession − 3d …) as the primary source; when the table has no entry, ask the configured provider for a *rule proposal* (days-before-closing + rationale) through the existing proposal shape — never a resolved date, honest fallback to "closing − 14d" when AI is unavailable.
3. Clamp (client's rule, enforced in the planner for **all** user/AI-added tasks, not just this button): an added task anchored to closing never lands later than closing − 7 days; if a rule computes later, pull to the floor and label it ("pulled to 7 days before closing").

**Effort:** M-L. **Decisions for Jake:** the timing table's contents; confirmation that provider-knowledge (no live web search) is acceptable; whether the button shows on all rows or only future-group rows (recommend: only the "collected later" group from A3).

### A7. Represented seller classified as FSBO (Screenshot 91)

**What happened.** A seller email entered during intake produced "Audri McGrane (ForSaleByOwner)" — on a deal whose contract names a listing agent. The client's rule: **FSBO only when the contract references FSBO / For Sale By Owner; otherwise the seller is a represented Seller.**

**Root cause** (traced): `is_fsbo` is a bare user checkbox on Purchase Info (`NewTransactionWizard.tsx:6306`) — extraction never informs it, nothing cross-checks it against the extracted listing agent, and **the FSBO block is the only place on Purchase Info that asks for a seller email**, so entering the seller's email naturally walks the tester into marking the deal FSBO. Submit then fires the FSBO invite (`:4009`) and the accepted invite creates the `for_sale_by_owner` assignment, which then shows up in owner/rosters as "(ForSaleByOwner)".

**Countermeasure.**
1. **Contract grounding:** extraction gains `detection.fsbo_reference` (bool; true only on explicit "FSBO"/"For Sale By Owner" text or an unrepresented-seller signature block; null otherwise) — both passes, typed models (drift guard covers), flat mapping.
2. **Cross-check in the wizard:** when the user checks FSBO but the extraction found a listing agent (or `fsbo_reference` is false), an inline warning: *"This contract names a listing agent (<name>) — FSBO deals have no listing agent. Keep FSBO?"* with the evidence chip. FSBO stays user-decidable (contracts can be wrong) but never silently.
3. **Give the seller email a correct home:** the seller party card (Address & Contacts) already holds seller emails — the FSBO block's copy states plainly that it *invites the unrepresented seller to a portal*, and a represented seller's email belongs on the seller card. (UX copy + link, no data change.)
4. **Role hygiene downstream:** `ForSaleByOwner` members are excluded from owner-assignment rosters ("Who's Transaction Is It?" options; backend assignable-users query) — an FSBO portal guest must never be selectable as the transaction owner.

**Effort:** M. Items 1–2 deterministic; 4 is a backend roster filter.

---

## Part B — Systemic flaws (found by re-examination, beyond the reports)

**B1. Three document-type vocabularies joined by exact string match.** Extraction enum (`purchase_agreement…other`), requirement library (`emd_receipt`, `utility_confirmation`…), and task/template registry grew independently; every join (auto-match, verification chip, resolver families) is exact-compare plus ad-hoc alias maps. This produced the utilities miss (A4), the possession miss (A5), and needed the alias map a week ago. **Countermeasure:** one canonical registry server-side (extend `document_template_registry`) exposing {canonical type, aliases, intake-plausible flag, timing-table entry}; the extraction enum, the requirement seed, the wizard matcher, and A6's timing table all read it. Phase 3 — do it once, not four more alias maps.

**B2. Contract-stated deadline windows are a closed set of four.** Inspection/response/HOA/insurance have extraction slots; everything else (EM delivery — A2; attorney review has its own bespoke field; appraisal-order windows; any state-form specific window) cannot flow and silently falls to library defaults, which testers correctly read as "the AI missed it". **Countermeasure:** after A2 ships the EM field the same hardcoded way (fastest correct fix), generalize to a keyed `term_windows` map ({field → {days, basis, citation}}) with a registry of known keys, so the next window is a registry row, not a schema change. Phase 3.

**B3. Intake asserts without consulting what intake already knows.** The signature flag ignores the counter chain it extracted itself (A1); proposals ignore the upload set (A5); FSBO ignores the extracted listing agent (A7); checklist rows ignored uploads until this week. **Rule to adopt (invariant):** *any intake-time claim or ask must first be checked against the packet's own evidence; surface the claim with the contradiction when they disagree, never the bare claim.* A1/A5/A7 countermeasures are instances; apply the same review to future wizard features.

**B4. Step 3's IA conflates "provide now" and "collected later"** (A3) — compounded by the amber box removal. The two-group layout is the fix; also restores a place for honest framing without the box.

**B5. Added-task dates have no sanity floor.** User/AI-added tasks can land on/after closing. The client's closing − 7d floor (A6.3) becomes a planner-level clamp for all added tasks + a coverage warning when clamping fired.

**B6. Signature semantics conflate document-level and packet-level execution** (A1). The per-document findings are right; the packet boolean needs chain derivation — same class as last week's per-document identity fix (the clone bug): packet-level and per-document truths must be computed separately and explicitly.

---

## Part C — Execution plan

**Phase 1 — deterministic correctness (no product decisions needed):**
1. A1 chain-signature rule (both prompts) + resolution backstop + panel copy.
2. A2 earnest-money window end-to-end (extraction → column → planner → row/task rules; 1 migration).
3. A4 similarity matcher (+ address-token stripping, stemming) in `computeRequirementAutoMatches` + library-vocabulary classification in the packet prompt + alias additions. Unit tests use the exact reported filenames.
4. A5 verifier `satisfied_by_document_id` + wizard auto-accept/attach.
5. A7.1/2/4 fsbo_reference extraction + listing-agent cross-check warning + roster exclusion.
6. B5 closing − 7d clamp for added tasks.

**Phase 2 — UX (screenshot-gated, needs Jake's eyes):**
7. A3 two-group Step 3 (have-now vs collected-later, collapsed).
8. A6 "Add as task" row action (curated timing table + provider-assisted rule proposal + clamp).
9. A7.3 seller-email placement copy/link.

**Phase 3 — systemic consolidation:**
10. B1 canonical doc-type registry powering extraction enum, matcher, seed, timing table.
11. B2 `term_windows` generalization.

**Verification standard (per project invariants):** every fix proven on rendered output / real parses — replica PDFs for A1 (countered chain) and A2 (EM clause 2→4 business days) through real Textract + production extraction, exact reported filenames in matcher tests, screenshots for Phase 2. Existing invariants preserved: preview = commit, manual decisions win, honest degradation, no silent AI dates.

**Decisions needed from Jake:** A3 collapse-vs-remove; A6 timing table contents + "provider knowledge, no live web search" trade-off + button placement; A7 warning copy.

---

*Related uncommitted work this round: inline checkbox interleave (title checkbox), typed-schema drift fix + guard (inspection days), reference-flag dedupe + per-document identity, Step 3 verbiage/amber box, checklist auto-match v1.*
