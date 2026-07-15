# Wizard Reorg — Jake's Answers: Implementation Plan

**Source:** Jake's replies to the five open questions (2026-07-15).
**Prepared by:** Jan.
**Date:** 2026-07-15 (rev 2, after a source-grounded workflow/logic review; see Appendix A for what changed).
**Status:** Plan only. Grounded in the current source (committed reorg Phases 1-4 + uncommitted Phases 3b/5-partial/6/7-partial).
**Validation set:** the 10-document `velvet-elves-data/testing_docs/` packet (5915 E 350 N: PA + 4 counters + amendment + EM + seller disclosure + post-closing possession + pre-approval).

---

## Part 0 · Jake's answers, mapped to phases

| # | Jake's answer | Phase |
|---|---|---|
| 3 | Split: each side can differ in amount AND unit ("seller 2%, buyer $250") | **Phase 1** (fee-model rework) |
| 2 | Two fee fields stay; transaction fee = broker/team admin fee; capture-only | **Phase 2** (label) |
| 4 | Flag only uncertain fields, confidence number on those | **Phase 3** (mostly already done) |
| 5 | Contract hint by the fee box; prefill last deal but confirm-to-use | **Phase 4** |
| 1 | Collect all docs in Step 1; review execution + logical gaps; propose client-scoped tasks; retire the attach checklist; create on Verification | **Phase 5** (review→tasks) + **Phase 6** (retire checklist + move create) |

---

## Part 1 · Grounded current state (verified in source)

- **Fee model (committed):** `WizardFeeEntry { amount, unit, payer('buyer'|'seller'|'split'), buyerShare, sellerShare }` + `WizardFees` in `wizardTypes.ts`; `feesToPayload` (uses buyerShare/sellerShare); backend `TransactionFeeEntry`/`TransactionFeesPayload` in `app/schemas/transaction.py`. **Consumers (all must change in Phase 1):** `feesToPayload` + types (`wizardTypes.ts`); `set_fee` reducer (`NewTransactionWizard.tsx:~1570`); `buildDraftPayload` (`:~3976`); `renderFeeCard` (`:~6025`); the **Confirm-summary fees card** (`renderConfirm`, `:~7743`, uses buyerShare/sellerShare); `formatFee` + the fees `<dl>` in `DealBriefBand.tsx`; the `TransactionFeeEntry`/`TransactionFees` types in `types/api.ts`. `fees_json` is JSONB (no migration); repo/model are pass-through.
- **Confidence flagging — ALREADY IMPLEMENTED:** `AiRecommendationRow` (`:~9846`) renders a borderline read as an empty field plus a chip carrying the value, source, and **`Math.round(confidence*100)%`**. Missing-required fields get the champagne highlight; Phase 3b added the needs-your-eyes decision band. High-confidence reads (>= `auto_proceed_threshold`, default 0.9) fill silently. Source citations and party cards also show the %. So "flag only the ones that need a look, with the number on those" is essentially the existing behavior.
- **Documents review surfaces — exist on Confirm:** `WizardMissingDocsPanel` (from `state.aiMissingDocuments`, which is set by `resolutionMissingDocuments(resolution.transaction_resolution)` at RESOLUTION time, NOT the intake pass); `WizardSignaturePanel` (shown when `aiAllPartiesSigned === false`; offers the e-sign queue via `signatureChoice === 'queue'`); `aiProposals.{timeline,checklist,tasks,watchouts}`.
- **`missing_signatures` is NOT in wizard state.** The parse returns it (backend `payload.detection.missing_signatures` / `payload.documents[].missing_signatures`), and mocks include it, but `NewTransactionWizard.tsx` captures only `all_parties_signed → aiAllPartiesSigned`. The wizard does not know *who* is unsigned.
- **`generate_intake_intelligence_with_pydantic_ai(packet_text, *, provider_name)`** takes ONLY packet text. It has no `represented_side` and no structured signature/missing-doc findings. It is a pure LLM pass; deterministic client-scoped tasks cannot be "added" inside it.
- **`represented_side`** IS available to the backend pipeline: `extract_packet_with_pydantic_ai(..., represented_side=...)` and `run_packet_parsing_pipeline(*, documents, represented_side, ...)`. The wizard also has `state.purchase.representation_choice` ('Buyer'|'Seller'|'Buyer & Seller').
- **`professional_fees` is free text.** Backend `ProfessionalFeesDetection { description: str | None }`; the extraction returns `detection.professional_fees` as a FieldExtraction (value = description, plus confidence/source). It is NOT a number and is NOT applied to any wizard `state` field today.
- **No frontend `profile_settings` write path.** `profile_settings` exists on the user model (used server-side for the product tour) but there is no frontend hook/endpoint the wizard can call to persist per-user fee defaults.

---

## Phase 1 · Fee model rework — per-side amounts (Jake #3)

**Redesign.** A fee is paid by buyer, seller, or both; each paying side carries its OWN amount and unit.

**Frontend (`wizardTypes.ts`).**
```ts
export type FeeUnit = 'percent' | 'flat'
export interface FeeShare { amount: string; unit: FeeUnit }
export interface WizardFeeEntry {
  payer: 'buyer' | 'seller' | 'both'
  buyer: FeeShare   // used when payer is 'buyer' | 'both'
  seller: FeeShare  // used when payer is 'seller' | 'both'
}
export const EMPTY_FEE: WizardFeeEntry = {
  payer: 'seller',
  buyer: { amount: '', unit: 'percent' },
  seller: { amount: '', unit: 'percent' },
}
```
`feesToPayload` emits only the paying side(s) with a non-blank amount (`{payer, buyer?, seller?}`); a fee with no non-blank paying side is omitted.

**Backend (`app/schemas/transaction.py`).** Reshape (no migration; `fees_json` is JSONB):
```python
class FeeShare(BaseModel):
    amount: float = Field(ge=0)
    unit: Literal['percent', 'flat']  # validator: percent <= 100

class TransactionFeeEntry(BaseModel):
    payer: Literal['buyer', 'seller', 'both']
    buyer: FeeShare | None = None
    seller: FeeShare | None = None
    # validator: the payer's side(s) present; the other side nulled.
```

**UI (`renderFeeCard`).** "Who pays?" stays Buyer / Seller / Both. Buyer or Seller = one amount box + its own `$ / %` toggle. **Both = two labeled rows** (Buyer [amount][$/%], Seller [amount][$/%]), independent. `set_fee` updates the nested share.

**Display.** Rewrite `formatFee` and the Confirm-summary fees card for the new shape: buyer-only `3% · buyer`; seller-only `3% · seller`; both `buyer $250 · seller 2%`. **Both display sites must tolerate old-shape `fees_json`** (render nothing rather than crash), since dev deals may hold the committed shape.

**Consumers to touch:** all six listed in Part 1, plus `types/api.ts`.

**Tests:** FE fee-flow integration test; backend `test_transaction_fees.py`; `DealBriefBand.test.tsx`; `test_transaction_plan.py` fee tests.

**Acceptance:** "Both" shows two amount+toggle rows; seller "2 %" + buyer "250 $" persists as `{payer:'both', seller:{2,percent}, buyer:{250,flat}}`; Confirm summary and workspace brief read "buyer $250 · seller 2%".

---

## Phase 2 · Transaction fee label (Jake #2)

In `renderFeeCard`: transaction-fee helper text ("A broker, team, or brokerage admin fee collected on the deal, separate from the app's own per-deal billing fee"). No behavior change; capture-only. Invoicing tie-in noted as future, not built.

---

## Phase 3 · Confidence: confirm existing, minor polish (Jake #4)

**This is largely already built.** Borderline reads park as `AiRecommendationRow` (empty field + chip with value + confidence %); missing fields get the champagne highlight + needs-your-eyes band; high-confidence reads fill silently. That is exactly "flag only the ones that need a look, with the number on those."

**Work:** verify the existing treatment reads as Jake expects on the reorganized steps, and (only if a gap shows) add a small consistency touch. Do NOT build a new per-field percentage chip on high-confidence filled fields; that contradicts "flag only." Net-new code here is small or none.

**Acceptance:** a field parsed at 82% shows the recommendation chip with "82%" and stays empty until accepted; a 98% field fills with no flag.

---

## Phase 4 · Fee convenience (Jake #5)

**4a · Contract hint.** `detection.professional_fees` is a free-text description (not a number), available in the extraction result.
- Capture it during `apply_extraction` into a new state field (e.g. `aiDetectedFeeNote: { text, page, snippet } | null`).
- On the Professional-fee card, show it as a one-line **informational hint** ("The contract mentions: '…'" with a source link). It informs the user; it does NOT auto-fill a numeric amount, because the value is prose.

**4b · Prefill from last deal, confirm-to-use (use localStorage).** There is no frontend `profile_settings` write path, so:
- On successful create, write the entered `fees` to `localStorage` (per browser). No backend, no migration.
- On a new wizard, prefill both cards from that value but mark them **unconfirmed**: a "Prefilled from your last deal, confirm" state with a one-click "Looks right." The prefilled value is NOT sent in the create payload until confirmed or edited (honors Jake's "don't let a lazy human skate past it").
- (Cross-device prefill via `profile_settings` would need a new settings endpoint + hook; out of scope unless Jake wants it.)

**Acceptance:** contract-stated fee shows as a hint; a second wizard run arrives prefilled-but-flagged, and the fee only commits after confirm or edit.

---

## Phase 5 · Documents review → client-scoped task suggestions (Jake #1a)

The review surfaces exist; this phase makes each gap a clear, one-click action scoped to the client. **Corrected approach** (the scoping is data-driven from findings the frontend must first capture; it does NOT go in the packet-text-only intake pass):

**5a · Capture `missing_signatures` into wizard state.** In the parse-result handler (where `all_parties_signed → aiAllPartiesSigned` is set), also read `missing_signatures` (and/or the per-document findings) into a new state field, e.g. `aiMissingSignatures: string[]`. This is the "who is unsigned" the scoping needs; today it is dropped.

**5b · Scope the signature action (client vs other agent).** Deterministic, frontend, using `representation_choice` vs the roles in `aiMissingSignatures`:
- Missing signature is the **client's** side (you rep the buyer and 'buyer' is unsigned) → the existing **"send for signature to your client"** path (`WizardSignaturePanel` / e-sign queue) is correct.
- Missing signature is the **other** side ('seller' unsigned on a buyer-rep deal) → offer a NEW **"request the signed copy from the other agent"** action (a task, or an AI email draft to the co-op agent), NOT an e-sign to them.
- The controlling-chain rule already prevents false positives (a countered PA with a signed counter reads executed via `apply_signature_chain_backstop`), so this only fires on a genuine gap.
- `WizardSignaturePanel` gains the client-vs-other-agent branch and wording.

**5c · Missing-document request.** `aiMissingDocuments` (already in state, from the resolution) lists referenced-but-missing docs (e.g. Counter #2). For each, offer a one-click **"request [document] from the other agent"** (task / email draft). No new detection needed; this reuses `aiMissingDocuments`.

**5d · Commit.** Accepted signature/request actions ride the existing task-creation and e-sign-queue paths at create; no new commit channel required for the common cases.

**Acceptance (validated on the 10-doc packet):** buyer-rep + seller-countered → if the fully executed copy is absent, the review proposes "request the signed copy from the other agent" (not an e-sign to the seller); a deliberately-removed Counter #2 yields "request Counter #2 from the other agent."

> Task/action wording is worth a one-line confirm from Jake, but the mechanism and scoping are specified.

---

## Phase 6 · Retire the checklist step, move create to Verification (Jake #1b)

D1 confirmed. Recipe (built once, reverted; now proceed):
- **Create on Confirm/Verification:** full-width **"Upload Transaction"** button + disclaimer in the review column; footer Back-only on this step; command bar unified to the same create.
- **Retire `checklist`** from `WIZARD_STEPS`/`WIZARD_PHASES`; relabel `confirm` → **Verification**; four public phases Upload / Contract Details / Contacts & Fees / Verification (`missing` stays a hidden auto-skip).
- **Requirement commit stays** in `submit()` (auto-match still runs at create); library requirements still generate. `WizardChecklistStep` kept as a stale-draft guard.
- **Fold** AI checklist-requirement proposals (`aiProposals.checklist`) into the Verification proposals panel.

**Test churn (expected, per D1):** rewrite the create-flow (`advanceToChecklist`/`confirmTimeline`/"Approve & Create" → one "Upload Transaction"); remove/convert the ~6 checklist-UI integration tests (that surface moves to the workspace); adapt the AI-proposals-flow test.

**Acceptance:** last step is Verification; its full-width "Upload Transaction" creates the deal; created deals keep requirement rows + auto-attached uploads; paywall/Autopilot/double-check gates hold; stepper reads "Step 4 of 4".

---

## Phase 7 · Docs + real-PDF validation

- Update `WIZARD_TESTING_GUIDE.md` §0 (drop the "Verification move not shipped" note once Phase 6 lands) and `FRONTEND_UI_WORKFLOW_LOGIC.md` §13.A.
- **Validate against the 10-doc `testing_docs/` packet** (in hand): parse resolves the chain ($992k, title→seller, close 2026-07-31); the signature/missing-doc review proposes the correct client-scoped actions; fees round-trip in the per-side shape; create lands on the workspace with fees on the deal brief. Extend the real-packet integration test.

---

## Sequencing & rationale

1. **Phase 1, 2, 4 first** (fees + hint/prefill): self-contained, keep the suite green with a screenshot check. **Phase 3 is confirm-existing** (little or no code).
2. **Phase 5** (capture missing_signatures + scope actions): builds on the existing signature/missing-doc surfaces; mostly frontend scoping + one new "request from other agent" action.
3. **Phase 6** (retire checklist + move create): the large test-churn structural change, done last so earlier phases stay green.
4. **Phase 7**: docs + the 10-PDF end-to-end pass.

## Risks & decisions

- **Fee-model reshape is breaking** vs. the committed shape. Dev-only data, `fees_json` JSONB (no migration), display tolerates old rows. Acceptable.
- **Checklist retirement removes ~6 wizard tests** — expected and correct (feature moves to the workspace per D1).
- **Phase 5 wording** (task/action titles) needs a one-line confirm from Jake; nothing blocks the build.
- **Every UI phase** ends with a rendered-screenshot check against the approved expressive style.

---

## Appendix A · What the rev-2 review corrected

1. **Phase 5 could not scope tasks in `generate_intake_intelligence`.** That function takes only `packet_text` (no `represented_side`, no signature findings). Rewrote Phase 5 to capture `missing_signatures` into state and scope the actions deterministically on the frontend (representation vs unsigned roles), reusing the existing e-sign queue and adding a "request from the other agent" action.
2. **`missing_signatures` is not in wizard state.** The wizard captures only `aiAllPartiesSigned` (a bool). Phase 5 now explicitly captures the missing roles (5a).
3. **`aiMissingDocuments` comes from the contract resolution**, not the intake pass. Phase 5c ties the missing-doc request to that existing signal instead of inventing a new detector.
4. **`professional_fees` is a free-text description, not a number.** Phase 4a now surfaces it as an informational hint and does not claim to auto-fill a numeric amount.
5. **No frontend `profile_settings` write path.** Phase 4b now uses `localStorage` for the prefill instead of a settings endpoint that doesn't exist.
6. **Phase 3 was overstated.** The confidence percentage is already shown on flagged (borderline) fields via `AiRecommendationRow`, and "flag only" is already the design. Phase 3 is reduced to confirm-existing with minimal net-new code.
7. **Phase 1 consumer list completed:** added the Confirm-summary fees card (`renderConfirm`) and `types/api.ts`, and a requirement that both display sites tolerate old-shape `fees_json`.
