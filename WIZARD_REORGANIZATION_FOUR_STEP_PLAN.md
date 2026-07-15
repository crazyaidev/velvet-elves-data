# Wizard Reorganization: Four-Step "Less Is More" Plan

**Source:** Audri's email "Wizard Reorganization" (received 2026-07-14).
**Prepared by:** Jan.
**Date:** 2026-07-14 (rev 2, after a full workflow/logic review against source; see Appendix A for what the review corrected).
**Status:** Plan only. No source changes yet.
**Companion docs:** `WIZARD_REORGANIZATION_EMAIL_REPLY.txt` (the reply that raised the open questions), `WIZARD_TESTING_GUIDE.md` (updated in Phase 7), `STYLE_GUIDE.md`, `FRONTEND_UI_WORKFLOW_LOGIC.md` §13.A / Cross-Cutting Workflow A.

---

## Part 0: What Audri asked for, mapped to this plan

| Audri's item | Plan section |
|---|---|
| Step 1 Document Upload, no changes | §2.1 (kept as-is; only step numbering text changes) |
| Step 2 Review Contract Details with the six groups + "needs your eyes" by AI certainty | §2.2, Phase 3 |
| Step 3 Contact Information and Fees, all parties + professional fee + transaction fee, % or $, payer buyer/seller/both | §2.3, Phases 1 and 4 |
| Step 4 Verification: full summary, disclaimer above the button, full-width "Upload Transaction" button | §2.4, Phase 5 |
| "Less is more" | §1.3 (two steps retired from the flow), §3 (decisions) |

Design constraints carried from standing client decisions (do not re-litigate):

- The wizard's expressive visual style is the approved aesthetic (flat restyle was rejected 2026-07-09). This plan changes structure and content grouping, not the visual language. Every UI phase ends with a rendered-screenshot check.
- The transient `'parsing'` screen stays non-navigable (client feedback 2026-07-09).
- The AI double-check gate on critical fields keeps blocking create (`blockedByDoubleCheck`).
- Contract decision fields stay one-click choices, never free typing (`MissingChoiceRow` pattern).
- Decision-critical answers keep their launch gate: a deal must not be created while `title_ordered_by` (requirements §15.1) or a cash deal's appraisal election (§15.3) is unanswered. Reorganizing steps must not weaken this (see §2.5).
- Testers are real-estate professionals: every acceptance criterion below is verifiable by mouse in the running frontend.

---

## Part 1: Current state (verified in source, 2026-07-14)

### 1.1 The step machine today

`velvet-elves-frontend/src/components/wizard/wizardTypes.ts:56` defines the navigable flow:

```
upload → address → purchase → missing → confirm → checklist
```

plus three retired-but-valid values: `parsing` (transient), `timeline` and `review` (folded away by earlier Audri feedback; kept for stale drafts). The public stepper shows three phases (`WIZARD_PHASES`, wizardTypes.ts:89): Upload / Review details / Documents. Create currently happens **from the `checklist` step footer** (`NewTransactionWizard.tsx:8711`, "Approve & Create Transaction" + the billing fee suffix from `commitFeeSuffix`, line 3469), or from `confirm` under Autopilot (line 8728).

### 1.2 What each current step contains, and its gate

| Step | Content (verified) | Continue gate (`canAdvance`, line 4828) |
|---|---|---|
| `upload` | Drop zone, packet parse, inline ready card. `parsing` auto-advances. | Representation picked + a persisted document (or manual mode) |
| `address` (`renderAddress`, line 5688) | "Property Details" FieldTable with Google address autocomplete **and** the Contacts section (party cards, line ~5924, vendor one-click fill, agent self-card auto-fill, owner selector). | All four address fields + at least one party + every party has name, email, phone + a principal party matching the representation choice (lines 4842-4881) |
| `purchase` (`renderPurchase`, line 6149) | FieldTables "Deal Type & Pricing" (6417), "Key Dates" (6588), "Contingencies & Extras" (6639), "Additional Contingencies" (6851), "Notes" with pin (6957). | Purchase price only; "anything else still missing is collected on the Missing Info step" (comment at 4883) |
| `missing` (`renderMissing`, line 7019) | Gap list: `MissingFieldRow` (type it or AI public-source search) and `MissingChoiceRow` (one-click decision options). Skipped automatically when nothing is missing (`isSkippableStep`, line 1449). Also hosts the red "upload at least one document" notice (7021). | **Hard gate:** `missingFields.length === 0 && hasRequiredDocument` (line 4888) |
| `confirm` (`renderConfirm`, line 7117) | Read-only review rows grouped Property / Dates / Financing / Terms with per-row citations; Autopilot hub (7295); "Found in the contract - needs your eyes" panel for pending AI **timeline** proposals (7352); double-check gating. | `hasRequiredDocument` |
| `checklist` (`renderChecklist` 8168 → `WizardChecklistStep`) | Requirements preview + auto-matching (`computeRequirementAutoMatches`), attach/add/edit/remove rows, **pending AI checklist-requirement proposals** (`pendingProposals` prop, line 8201), and the create button. | `hasRequiredDocument` |

### 1.3 Cross-cutting machinery this plan must move carefully (all verified)

- **Parse auto-advance targets `'address'`.** When extraction resolves (or the user skips ahead), the wizard dispatches `set_step('address')` at `NewTransactionWizard.tsx:3682`, `3835`, `3852` (and `'confirm'` under Autopilot, reducer line 1643). Reordering the steps without retargeting these lands the user on the wrong step after parsing.
- **Field→step navigation table.** `WIZARD_FLAG_TARGETS` (lines 857-1165) maps every field key to `{step, inputId}` for flag alerts and focus-jumps: all `address.*` property entries point at `step: 'address'`; `parties.*` entries also point at `'address'`; `purchase.*` at `'purchase'`. The `resolveWizardFlagTarget` fallbacks (line 1292) hard-code the same prefix→step rules. Any content move must retarget these or chips/flags navigate to the wrong step.
- **`detectMissingFields` (wizardTypes.ts:1392) spans both future steps:** address fields, required purchase fields, conditional contingency day counts, `title_ordered_by` (§15.1, exempt for attorney closings), cash-deal `has_appraisal` (§15.3), and required party roles. Its output currently powers the `missing` step's hard gate. `resolve_missing` (reducer line 1885) writes resolved values back into `state.address`/`state.purchase` so the gate clears - it is field-key based and works from any step.
- **Confidence:** per-field `aiConfidences`; `auto_proceed_threshold` (default 0.9) and `recommendation_floor` (default 0.7) from server settings (lines 3323-3326). Borderline values park as one-click `aiRecommendations` (reducers 1941-1976, `AiRecommendationRow`). Empty-and-unreviewed fields get the champagne highlight (5694-5705, 6155-6165).
- **Commit chain** (`submit()`, ~3900-4441): create transaction → link documents → server requirements preview re-run + bulk insert with `computeRequirementAutoMatches` (4193-4219, preview equals commit) → tasks → deal brief → e-sign sends. The 402 paywall interrupts create and resumes after payment (3457, 4416, 4498). **The chain itself does not change; only the step that triggers it moves.**
- **Drafts persist the whole `WizardState`** as `draft_json` via `useWizardDraft` (applied at lines 4805-4813), including `step`. New state fields (fees) persist automatically; retired step ids in old drafts must be normalized at the draft-apply point.
- **Fees today: nothing.** `TransactionCreateRequest` (backend `app/schemas/transaction.py:15-100`) has no fee fields. `TransactionRepository.create()` is an **explicit kwarg whitelist** (repository lines 42-132: named parameters + an `_optional` dict), not a pass-through - a new column must be threaded through schema → API endpoint → repository signature → `_row_to_transaction` → response. The extractor detects only a free-text `detection.professional_fees` description (evidence label "Professional Fees", wizardTypes.ts:405/443/483); it is never an input and never persisted.
- **`SegmentedControl` exists** at `src/components/ui/segmented-control.tsx` (already used by `WizardTimelineStep.tsx:35`) - the fee UI reuses it, nothing new to build.

---

## Part 2: Target design

### 2.1 The new step machine (end state)

```
WIZARD_STEPS = ['upload', 'purchase', 'address', 'confirm']
```

Four navigable steps, one public phase each ("Step N of 4"). Existing step **ids are reused** so saved drafts, `visitedSteps`, flag section keys, and `editFromConfirm` targets keep working; only labels, order, and content grouping change (the codebase already tolerates id/label divergence: `checklist` is labeled "Documents" today).

| Order | Id (unchanged) | New label | Content |
|---|---|---|---|
| 1 | `upload` (+ transient `parsing`) | Upload Documents | Unchanged. |
| 2 | `purchase` | Contract Details | Property Details (moved in from `address`) + Deal Type & Pricing + Key Dates + Financing Summary + Contingencies, Terms & Extras + Notes. |
| 3 | `address` | Contacts & Fees | Parties & Contacts (unchanged content) + new Fees section. |
| 4 | `confirm` | Verification | Full summary (now including contacts and fees), AI proposal decisions, disclaimer, full-width "Upload Transaction" create button. |

**Auto-advance robustness rule:** every parse/skip auto-advance site (3682, 3835, 3852) switches from the literal `'address'` to a single constant `FIRST_REVIEW_STEP` (defined as `WIZARD_STEPS[1]` in wizardTypes.ts), so this class of bug cannot recur if steps are ever reordered again. The Autopilot target stays `'confirm'` (still the last step). The wizardTypes.ts comment block (lines 38-55), which documents the old targets, is rewritten to match.

Retired from navigation (values stay legal for stale drafts, exactly like `timeline`/`review`):

- **`missing`** - its rows fold into the Steps 2/3 needs-your-eyes band (§2.2) and its hard gate is re-homed per §2.5. The `isSkippableStep` special case (1449) is deleted with it.
- **`checklist`** - the create action moves to Step 4; the requirement commit already re-runs server-side at create, independent of the step having been visited (4193-4219). The pending AI checklist-proposal decisions it hosts (8201) move to Step 4's proposals panel. The workspace's Missing Documents panel and Compliance tab remain the post-creation editing surface. **Decision D1 (§3) - default is retire, pending Audri's reply.**

**Draft normalization** applied at the single draft-apply point (the `pendingDraft` application, 4805-4813, plus the local-draft restore path): `missing → purchase`, `checklist → confirm`, `review → confirm`, `timeline → confirm` (existing behavior), `parsing → upload` (existing). `phaseIndexForStep` keeps mappings for all retired ids.

### 2.2 Step 2: Review Contract Details

Section order matches Audri's list exactly, reusing the existing `FieldTable` components:

1. **Property Details** - the FieldTable + Google autocomplete block moves verbatim from `renderAddress` into the top of `renderPurchase`, together with the `aiFilledBanner` that currently leads the first review step (5709).
2. **Deal Type & Pricing** - existing (6417).
3. **Key Dates** - existing (6588).
4. **Financing Summary** - the existing financing fields regrouped under their own header (financing type, mortgage type, owner-occupied, appraisal election).
5. **Contingencies, Terms & Extras** - existing (6639 + 6851).
6. **Notes** - existing (6957).

**"Needs your eyes" band (new, shared component `WizardNeedsYourEyesBand`):** a single strip at the top of Steps 2 and 3, in the same visual voice as the existing confirm-step panel (`✦ Found in the contract - needs your eyes`, orange-soft card, 7352). One chip per flagged field; clicking a chip scrolls to and focuses the field (reusing the `WIZARD_FLAG_TARGETS` focus mechanism). A field is flagged when any of:

- AI confidence below `auto_proceed_threshold`, including parked `aiRecommendations`;
- the field is in this step's missing-fields subset (§2.5) or required-but-empty and unreviewed;
- the double-check pass disagreed on it.

Flag presentation on the field: the existing champagne highlight plus a confidence chip ("AI · 82%") **only on flagged fields** (Decision D4 default). Editing, accepting a recommendation, or answering a choice row clears the flag through the existing `reviewedFields` / `accept_recommendation` / `resolve_missing` reducers (`resolve_missing` already writes back into `state.address`/`state.purchase`, so gates clear correctly - verified, reducer 1885-1915). The band embeds the former missing-step rows for its step's gaps: `MissingChoiceRow` (one-click decisions) and `MissingFieldRow` (type it or AI public-source search) render inside the band, so the gap-filling assist survives the step's retirement. When nothing is flagged the band shows one honest line ("Everything here read clean") - no fake work.

The red "upload at least one document" notice (currently on `missing`, 7021) moves to the top of Step 2 and also renders on Step 4.

### 2.3 Step 3: Contacts & Fees

**Parties & Contacts:** the existing Contacts section is unchanged (party cards with citations, vendor one-click fill, agent self-card auto-fill, owner selector gated on `canAssignOwner`, FSBO invite model untouched). The needs-your-eyes band covers low-confidence extracted contacts and this step's missing subset (required party roles).

**Fees (new section, two identical cards):**

| Control | Design | Interaction |
|---|---|---|
| Card 1 "Professional fee" / Card 2 "Transaction fee" | Same card anatomy as existing wizard sections (rounded-2xl, hairline border, serif section title) | - |
| Amount | Single `Input`, numeric | Type one number - the only typing in the section |
| Unit | `SegmentedControl` (`ui/segmented-control.tsx`) `$ | %` | One click |
| Who pays | `SegmentedControl` `Buyer | Seller | Both` | One click; `Both` shows a 50/50 note with an "Adjust split" reveal for exact shares (two inputs validating to 100%) - Decision D3 default |
| Helper text | Transaction fee card only: one line distinguishing it from the platform's own per-deal billing fee - Decision D2 | - |

Convenience rules (minimal input, mouse-first):

- **Prefill from last deal:** on successful create, entered fees are silently remembered to the user's `profile_settings` (existing JSON mechanism on the user model, no migration); the next wizard run prefills both cards with a quiet "Prefilled from your last deal" hint and a one-click clear.
- **AI hint, never auto-fill:** when the parse found `detection.professional_fees`, its snippet renders as an advisory citation chip beside the card. Fees are money: the user always enters/confirms the value.
- **Fees never gate:** empty fee cards flag in the band but block nothing - unlike the §2.5 missing-field gates, fees are additive data with no downstream task-generation dependency.

### 2.4 Step 4: Verification

Extends the existing `renderConfirm`:

1. **Full contract summary** - existing grouped review rows (Property / Dates / Financing / Terms with per-row citations and Edit-jumps) **plus two new groups:** "Parties & Contacts" (name, role, email per party; Edit jumps to Step 3) and "Fees" (both fee lines formatted "3% · paid by Seller"; Edit jumps to Step 3). Property rows' Edit-jump retargets from `address` to `purchase`.
2. **AI proposal decisions in one place** - the pending **timeline** proposals panel already lives here (7352). The pending **checklist-requirement** proposals (`pendingChecklistProposals`, currently rendered by the retired checklist step via its `pendingProposals` prop, 8201) join the same panel with the same accept/decline handler (`handleDecideProposal`, 7808). Accepted ones flow into the existing commit payload (`extra_requirements`, 4176) unchanged.
3. **Disclaimer** - one paragraph directly above the button, per Audri: "By uploading this transaction you confirm the information you verified is correct. Velvet Elves will use it to build this deal's timeline, document checklist, tasks, and communications." (Copy finalized at implementation; short, not legal boilerplate.)
4. **"Upload Transaction" button** - renamed from "Approve & Create Transaction", rendered **inside the review column at full width** (`w-full`, size `lg`), keeping the billing fee suffix and every existing gate (§2.5 table). The sticky footer on this step keeps only Back - one create button, never two. The `WizardCommandBar` approve action (8991/9010) gets the same label. The Autopilot in-footer create (8728) becomes the same in-content CTA.
5. **Create chain** - `submit()` unchanged; the silent requirement commit keeps `computeRequirementAutoMatches` as the single matcher (preview equals commit), so uploaded documents auto-attach to their checklist rows and the wizard never asks for a document it already has.

### 2.5 Gate re-homing (the missing step's hard gate must not be lost)

Today the `missing` step blocks until `missingFields.length === 0` (4888). That gate protects decision-critical answers whose absence changes what gets generated (`title_ordered_by` decides which title task is created, §15.1; cash-deal `has_appraisal` decides appraisal tasks, §15.3). Retiring the step **re-homes** the gate rather than dropping it:

| Gate | Old owner | New owner |
|---|---|---|
| Four address fields | `address` Continue | Step 2 (`purchase`) Continue - moves **with** the fields |
| Purchase price | `purchase` Continue | Step 2 Continue (unchanged owner) |
| Step-2 missing subset: `address.*` + `purchase.*` entries of `detectMissingFields` (required fields, conditional contingency day counts, `title_ordered_by`, `has_appraisal`) | `missing` Continue | Step 2 Continue |
| Party completeness (≥1 party; name+email+phone each; principal matches representation) | `address` Continue | Step 3 (`address`) Continue (unchanged owner) |
| Step-3 missing subset: required party-role entries of `detectMissingFields` | `missing` Continue | Step 3 Continue |
| `hasRequiredDocument` | `missing`/`confirm`/create | Step 4 + create button (notice surfaces on Steps 2 and 4) |
| Full `missingFields.length === 0` | `missing` Continue | **Backstop on the Upload Transaction button** (belt and suspenders: per-step gates should make this unreachable) |
| Double-check disagreements, undecided proposal conflicts, `anchorConfirmed` (Autopilot), `isConfirmingPayment` | create button | create button (unchanged) |

Implementation shape: `detectMissingFields` gains a step-partitioned variant (`detectMissingFieldsForStep(state, step)`) driven by the same field-prefix rules `resolveWizardFlagTarget` uses, so the band, the gates, and chip navigation all share one source of truth. The user is never blocked without the fix in front of them: the band on the gating step hosts the exact rows (choice buttons / input / AI search) that clear the gate, and the disabled Continue explains itself ("2 answers needed above").

---

## Part 3: Decisions (defaults chosen so work is never blocked)

| # | Question (owner: Audri/Jake) | Default in this plan if unanswered |
|---|---|---|
| D1 | Confirm the Documents checklist step leaves the wizard (asked in Jan's reply email) | Retire it. Requirements still commit at create with auto-matching; the workspace Missing Documents panel / Compliance tab are the editing surface. |
| D2 | What "transaction fee" means (coordinator/brokerage admin fee paid inside the deal?) and its on-screen label | Label "Transaction fee" with helper text separating it from the platform's per-deal billing fee. |
| D3 | Split entry: simple Buyer/Seller/Both, or exact shares | Both = 50/50 by default with an optional "Adjust split" for exact shares. |
| D4 | Show AI percentage on every field or only flagged ones | Percentage chip on flagged fields only. |

---

## Part 4: Implementation phases

Sequencing rule: **every phase leaves a fully working end-to-end wizard** (upload through create), so testing never hits a broken interim build. Steps are retired only in the phase that relocates their function.

### Phase 1: Fees backend

**Migration** `supabase/migrations/20260919090000_transaction_fees.sql` (verified free slot; latest is 20260918090000):

```sql
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS fees_json JSONB;
COMMENT ON COLUMN transactions.fees_json IS
  'Agent-entered deal fees: {professional: {amount, unit, payer, buyer_share?, seller_share?}, transaction: {...}}';
```

One JSONB column, mirroring the `attorney_review_json` / `deadline_day_basis_json` precedent.

**Thread the column through the whole verified chain** (the repository is a kwarg whitelist, not a pass-through):

1. `app/schemas/transaction.py`: `TransactionFeeEntry` (`amount: Decimal ge=0`; `unit: Literal['percent','flat']` with percent ≤ 100; `payer: Literal['buyer','seller','split']`; optional shares summing to 100 when `payer='split'`) and `TransactionFeesPayload {professional?, transaction?}`; add `fees_json` to `TransactionCreateRequest`, `TransactionUpdateRequest`, and the response schema.
2. `app/api/v1/transactions.py`: pass `fees_json` in the create endpoint's `repo.create(...)` kwargs and allow it through the update path.
3. `app/repositories/transaction_repository.py`: add `fees_json` to `create()`'s signature and `_optional` dict (line 108); confirm `update()` passes it; map it in `_row_to_transaction`.
4. `app/models/transaction.py`: add the field to the `Transaction` model.
5. Frontend `src/types/api.ts`: mirror `fees_json` on the `TransactionCreateRequest`/response types.

Fees are user-entered, not AI-resolved: **not** added to `TRANSACTION_FIELD_TO_RESOLUTION_PATH` in `contract_corrections.py` (no spurious correction rows).

**Tests:** backend (`test_transaction_fees.py` or extend `test_transactions_advanced.py`): create with both fees; percent > 100 rejected; split shares must sum to 100; update round-trip; response echo; create with no fees succeeds.

**Acceptance:** backend suite green; Swagger create with `fees_json` persists and echoes.

### Phase 2: Step machine reorder (no content moves yet)

`wizardTypes.ts`: reorder to `['upload', 'purchase', 'address', 'missing', 'confirm', 'checklist']` (pure swap of the two review steps - both live inside the same "Review details" public phase, so the top stepper needs no change yet); add `FIRST_REVIEW_STEP = WIZARD_STEPS[1]` and rewrite the stale comment block (38-55).

`NewTransactionWizard.tsx`: switch the three parse/skip auto-advance sites (3682, 3835, 3852) to `FIRST_REVIEW_STEP`; extend the draft-apply normalization (4805-4813) with the retired-step mapping table (inert until later phases, but in place once).

Interim state (documented, fully navigable): upload → Deal/Pricing → Address & Contacts → Missing Info → Confirm → Documents. Gates keep their current owners because no field has moved.

**Tests:** update `src/tests/integration/WizardFlow.test.tsx` step-order expectations.

**Acceptance (mouse-only):** parse lands on the pricing step; Back from it reaches Upload; the full flow through create still works; a saved draft on any step reopens correctly.

### Phase 3: Step 2 assembly - property move, band, missing-step retirement

Move the Property Details block (autocomplete + `aiFilledBanner` included) into the top of `renderPurchase`; regroup per §2.2; relabel `purchase` → "Contract Details". **Move together, in this phase:**

- the four-address-fields gate from `canAdvance('address')` into `canAdvance('purchase')`;
- the `address.*` property entries of `WIZARD_FLAG_TARGETS` (857-929) and the `address.` prefix fallback in `resolveWizardFlagTarget` (1296) → `step: 'purchase'` (`parties.*` entries stay `'address'`);
- `editFromConfirm` targets for property rows → `'purchase'`.

Build `WizardNeedsYourEyesBand` + `detectMissingFieldsForStep` (§2.5); mount the band on Steps 2 and 3; fold the missing-step rows in; add the step-subset gates to both steps' Continue; move the document-required notice; then remove `missing` from `WIZARD_STEPS` and delete its `isSkippableStep` case. `renderMissing` stays as a stale-draft guard that redirects.

**Tests:** WizardFlow integration (missing-step scenarios become band scenarios: title_ordered_by unanswered must disable Step 2 Continue with the choice row visible); unit tests for `detectMissingFieldsForStep`.

**Acceptance (mouse-only, after parsing a test packet):** six groups in Audri's order; every low-confidence or missing field appears as one chip; chip click focuses the field on the **same step**; a one-click choice answers title-ordered-by and enables Continue; a fully-clean parse shows the honest empty state; screenshots match the approved aesthetic.

### Phase 4: Step 3 Contacts & Fees

`renderAddress` keeps only Contacts + the new `WizardFeeSection` (§2.3); relabel `address` → "Contacts & Fees" (label changes here, when it becomes true). New `fees` state + `set_fee` reducer; include in `buildDraftPayload()` → `fees_json` (drafts persist it automatically via `draft_json`). Prefill from `profile_settings` on mount; write-back on successful create. Advisory AI chip from the `professional_fees` citation when present.

**Tests:** reducer unit tests for `set_fee` + prefill; WizardFlow fee-entry scenario.

**Acceptance (mouse-only):** entering "3", clicking `%`, clicking `Seller` is the entire professional-fee flow; Both shows the 50/50 note and optional split validating to 100; a second wizard run arrives prefilled with a one-click clear; empty fees flag a chip but never block.

### Phase 5: Step 4 Verification + create move + checklist retirement

Add Parties and Fees summary groups; fold `pendingChecklistProposals` into the confirm proposals panel (reusing `handleDecideProposal`); add the disclaimer; render the full-width in-content "Upload Transaction" CTA with the §2.5 gate set (including the `missingFields` backstop); suppress the footer create branches (8711, 8728) and relabel the command bar (8991/9010); relabel `confirm` → "Verification"; remove `checklist` from `WIZARD_STEPS`; rewrite `WIZARD_PHASES` to the four 1:1 phases (the public stepper changes only now, once the four-step reality exists).

**Tests:** WizardFlow create-from-verification scenario incl. paywall 402 and Autopilot; checklist-proposal decision moved-surface scenario.

**Acceptance (mouse-only):** summary shows property, dates, financing, terms, parties, fees with working Edit jumps; disclaimer sits directly above a button spanning the review column; create lands on the workspace; checklist rows exist with the uploaded purchase agreement auto-attached; paywall and Autopilot paths complete; double-check disagreements still block with the existing explanation; stepper reads "Step 4 of 4".

### Phase 6: Fees in the workspace

Display both fees in the workspace deal-facts surface (`DealBriefBand.tsx` / `WorkspaceHeader.tsx`, exact placement chosen against the live layout) formatted "Professional fee · 3% · Seller pays", with inline edit through the existing PATCH flow. Honest absence: no fee entered → no fee row.

**Acceptance (mouse-only):** fees entered in the wizard are visible on the workspace after create; editing one there persists across reload.

### Phase 7: Documentation, testing guide, regression

Update `WIZARD_TESTING_GUIDE.md` with the four-step click-script (written for non-developers); update `FRONTEND_UI_WORKFLOW_LOGIC.md` §13.A / Workflow A; run the full Part 5 matrix; rendered screenshots of all four steps at desktop and mobile widths for Jake/Audri sign-off.

---

## Part 5: End-to-end verification matrix (all via the frontend UI)

| # | Scenario | Expected |
|---|---|---|
| 1 | Happy path: upload packet → 2 → 3 → 4 → Upload Transaction | Deal created; tasks, timeline, checklist generated; fees on workspace; uploaded docs auto-attached to checklist rows |
| 2 | Parse completes | Wizard lands on Step 2 (Contract Details), never on Contacts |
| 3 | Manual mode (skip upload) | Steps 2-3 empty-but-highlighted; document notice on Steps 2 and 4; create blocked until a document is uploaded |
| 4 | `title_ordered_by` unanswered (non-attorney state) | Step 2 Continue disabled; band shows the one-click Buyer/Seller choice; answering enables Continue; create backstop never reachable in this state |
| 5 | Cash deal, appraisal election unanswered | Same pattern as #4 on Step 2 |
| 6 | Autopilot (high-confidence parse) | Lands on Step 4 with the hub; anchor confirm then full-width create |
| 7 | Borderline reads | Parked recommendations appear as chips on Steps 2/3; one-click accept clears; chip click focuses the field on the correct step |
| 8 | Double-check disagreement | Create blocked on Step 4 with the existing explanation row |
| 9 | AI checklist proposal pending | Decided on Step 4's proposals panel; accepted row appears in the created deal's checklist |
| 10 | Billing paywall (402) | Payment flow interrupts and resumes create from Step 4 |
| 11 | Draft resume from every step id, including retired `missing`/`checklist`/`timeline`/`review` | Reopens on the mapped step with data intact |
| 12 | FSBO deal | Seller-invite model unchanged on Step 3 |
| 13 | Fees skipped entirely | Deal creates; workspace shows no fee row; no console errors |
| 14 | Second deal by the same user | Fee cards prefilled from the last deal; one-click clear works |
| 15 | Back-navigation from Step 4 to each step and forward again | No data loss; `returnToConfirmAfterEdit` jump still returns to Step 4 |

---

## Part 6: Risks and mitigations

- **Reused step ids with new meanings** (`address` = contacts step): documented in `wizardTypes.ts` comments at implementation; the alternative (new ids) breaks draft resume for every in-flight draft.
- **Gate regression risk** is the highest-consequence failure (a deal launching without `title_ordered_by` silently changes task generation): §2.5 keeps a create-button backstop on the full `missingFields` set even though per-step gates should make it unreachable, and matrix rows 4-5 test it explicitly.
- **Losing the checklist step's pre-create editing** (add/override/remove requirement rows): accepted under "less is more"; the workspace offers add, attach, waive, and email-request post-create. If D1 comes back "keep it", the step re-enters as an optional link from Step 4, not a fifth required step.
- **Fee semantics ambiguity** (D2/D3): the JSONB shape absorbs label and split changes without another migration.
- **Aesthetic drift**: every UI phase gates on screenshots against the approved expressive style.

## Part 7: Out of scope

- Quick-create modal (separate path, untouched).
- Commission payout/invoicing off the entered fees (future; the data now exists for it).
- Any change to parsing, extraction schemas, or the checkbox/reconciliation backstops shipped 2026-07-14.
- Platform billing (the per-deal flat fee) - only referenced for label disambiguation.

---

## Appendix A: What the rev-2 review corrected (workflow/logic flaws found in rev 1)

1. **Parse auto-advance was unhandled.** Rev 1 reordered steps without retargeting the three `set_step('address')` parse-resolution sites (3682/3835/3852); users would have landed on Contacts & Fees after parsing, skipping Contract Details. Fixed with the `FIRST_REVIEW_STEP` constant (§2.1, Phase 2).
2. **The missing step's hard gate was silently dropped.** Rev 1 said band flags "do not block Continue or create," which would have allowed deals to launch without `title_ordered_by` / `has_appraisal` - changing task generation. Fixed with the §2.5 gate re-homing table, per-step subsets, and a create backstop. ("Fees never gate" remains true; the missing-field gates were never optional.)
3. **Phase sequencing left interim builds unable to create a transaction.** Rev 1's Phase 2 cut `WIZARD_STEPS` to four steps while the create button still lived on the checklist step (removed only in Phase 5). Fixed: Phase 2 is a pure reorder; `missing` retires in Phase 3 with its replacement, `checklist` in Phase 5 with the create move; every phase ships a working E2E wizard.
4. **The field→step navigation table was missed.** `WIZARD_FLAG_TARGETS` (857-1165) and the `resolveWizardFlagTarget` prefix fallbacks (1292-1310) pin `address.*` fields to the address step; without retargeting, flag alerts and band chips would navigate to the wrong step after the property move. Fixed in Phase 3.
5. **The address gate is more than "required street."** It requires all four address fields plus party completeness and a principal matching the representation choice (4842-4881). Fixed: the address-fields portion moves with the fields (Phase 3); the party portion stays on Step 3.
6. **"Pass-through" backend description was wrong.** `TransactionRepository.create()` is an explicit kwarg whitelist; rev 2 lists the exact five-touchpoint chain (Phase 1).
7. **Checklist-proposal decisions location confirmed** (they are decided on the checklist step via `pendingProposals`, 8201) and their move to Step 4 is now tied to the concrete handler (`handleDecideProposal`, 7808).
8. **`SegmentedControl` verified to exist** (`ui/segmented-control.tsx`, used by the timeline step) - no new primitive needed.
9. **Test updates assigned per phase** (WizardFlow integration, reducer/unit tests) instead of deferred to the end.
10. **Matrix extended** with rows 2, 4, 5, 9 covering the corrected behaviors.
