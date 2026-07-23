# AI Wizard — Audri's Testing Notes, Procedures & Questions (2026-07-22)

> Verbatim record of Audri's testing round on the AI Wizard, the resolution
> procedures applied, and the follow-up questions raised. Screenshots referenced
> below live in `velvet-elves-data/ai_wizard/`. Status column reflects the
> as-built state after the 2026-07-22/23 remediation.

---

## 1. Audri's raw testing notes (as written)

### AI wizard

**Step 1**
- Can we please make this question stand out more since it's required before
  uploading docs? It needs to grab the user's attention.
- Can we center the "WHO ARE YOU REPRESENTING?" and put the Buyer, Seller and
  Buyer & Seller boxes below the question.
  (`ai_wizard/Screenshot_133.png`)

- Instead of listing all the docs as it parses and listing all the info it finds
  in the contract (pic 2 below) can we keep it as pic 1 below until it's
  finished? We want the user to know what the system is doing and that it's still
  "thinking" but we don't need to give them all the details on what it's parsing.
  - Pic 1 — `ai_wizard/Screenshot_134.png`
  - Pic 2 — `ai_wizard/Screenshot_135.png`

**Step 2**
- None of the "Find in Document" (magnifying glass) features work in this
  section. (`ai_wizard/Screenshot_136.png`)

**Step 3**
- Can we make it where if the user's mouse is in this section they are able to
  scroll through the pages of the document? If they are not in this section then
  it scrolls the entire page. (`ai_wizard/Screenshot_137.png`)
- Add button under "Company" box to be able to skip this step on all roles except
  Buyer, Seller and Co Agent. "Create A Task To Collect This Information." Once
  the user selects this option then the boxes are no longer mandatory and the
  task is created upon transaction upload. It should also show the added task in
  the summary screen so the user knows it has been created.
  (`ai_wizard/Screenshot_138.png`)
- Remove "separate from the app's own per deal billing fee" in the Transaction
  fee box.
- Remove orange box and the info in it.

- **New Request:** This should only exist if representing the Seller or Buyer &
  Seller — we will need to ask what the listing professional fee is, along with
  the buyer agent's professional fee. We need to ask if the Seller is paying any
  of the buyer's agent fee, and if so, we need to know how much. If we represent
  the buyer we see what you have below. If we represent the seller then we will
  need to ask if the seller is paying the buyer's agent fee, and if so, how much
  are they paying. I don't feel I'm being clear so ask any questions if you're
  unclear. 😊 (`ai_wizard/Screenshot_139.png`)

- Can we make these requests more clear. I love how they are bold and at the top
  of the screen, but it's not clear on what's wrong, or what needs to be fixed.
  Eg, the first box says Counter offer expiration, when it should say "Counter
  Offer 1 Expiration". Can you please explain the "Counter offer expiration"
  error to us? If this populated because it's past the date of the counter offer,
  it should never populate. Regardless of document, it should never call out
  expiration dates. If a user is uploading the transaction the expiration dates
  are irrelevant. (`ai_wizard/Screenshot_140.png`)

**Step 4**
- Please add the Professional Fee(s) here as well. There is nowhere a user can
  verify/modify the info.
- Add "Paid by Buyer" instead of "buyer". If it's paid by seller then it should
  state "Paid by Seller". (`ai_wizard/Screenshot_141.png`)
- Move the "Upload Transaction" button to the bottom of the page. You can leave
  the disclaimer below the button, but everything else should be above the
  button. (`ai_wizard/Screenshot_142.png`)

**SALES NOTE:** The vendor directory is a great way to keep track of vendors you
had a great transaction with and you want to remember them. This works especially
well if you are working out of the area and want to save a title vendor or even a
handyman or general contractor.

---

## 2. Resolution procedures applied

| # | Item | Resolution | Source of truth |
| --- | --- | --- | --- |
| 1 | Step 1 question prominence + centering | Centered, large serif heading with Buyer / Seller / Buyer & Seller stacked below; card glows champagne until answered. | `NewTransactionWizard.tsx` `renderUpload` |
| 2 | Parsing screen noise | Four fixed phases only (*Reading documents · Extracting property data · Identifying parties · Checking dates*), spinner on the active one, checks on completed. No per-document narration. | `renderParsing` |
| 3 | "Find in Document" broken | Root cause: dates stored as `YYYY-MM-DD`, prices as `$287,000` — no contract writes them that way, so every locate found nothing. Now searches the forms a document actually uses (`07/14/2026`, `July 14, 2026`, `287000`, `$287,000.00`); token-fallback scorer fixed. | `utils/ocrHighlight.ts` (`valueSearchVariants`, `findCitationMatch`) |
| 4 | Document scroll within pane | Viewer rewritten to render **every page stacked in one scroll container** → native, continuous, smooth scrolling through all pages. Toolbar counter + thumbnail highlight derive from scroll (IntersectionObserver); citation jumps scroll the pane only. | `WizardPdfDocument.tsx` |
| 5 | Collect-info task on vendor cards | Button under Company on vendor roles (title, lender, inspector, appraiser, attorney); once chosen, email/phone stop being required and a `contact_info` task is created at commit and listed on Verification. Excludes buyer, seller, and both agents. | `renderAddress` / party card; `task_generation_service.py`; `schemas/transaction.py` |
| 6 | Remove billing-fee sentence | "Separate from the app's own per-deal billing fee" removed from the Transaction fee hint. | `renderFeeCard`, `FeeEditDialog.tsx` |
| 7 | Remove orange contract-clause box | The read-only "the contract mentions…" box removed from the fee cards (kept in parse result, not rendered). | `renderFeeCard` |
| 8 | Seller/dual professional fees | Listing-side deals (Seller / Buyer & Seller) capture the listing fee, the buyer-agent fee, and "is the seller paying any of the buyer agent's fee? how much?". `fees_json.professional` still holds "your side's fee"; new `listing` / `buyer_agent` / `seller_pays_buyer_agent` ride alongside. | `wizardTypes.ts` (`feesToPayload`), `renderListingSideFees`, `schemas/transaction.py` |
| 9 | "Needs your eyes" clarity | One-line explanation of what each section wants; fixed the blank-titled waive card (read `waive` not `name`); demotion reasons said in plain English. | `renderConfirm` proposal cards, `explainProposalReason` |
| 10 | Expiration deadlines never populate | LLM told never to propose offer/counter-offer/acceptance expirations; any that slip through dropped by label. | `intake_intelligence.py` (`_is_expiration_proposal`) |
| 11 | Step 4 professional fees + payer wording | Fees always shown on Verification with "Paid by Buyer" / "Paid by Seller"; listing-side breakdown included. | `feeSummaryRows`, `DealBriefBand.tsx` `formatFee` |
| 12 | Move Upload Transaction to bottom | Commit action rendered last on Verification — below review cards, command bar, and Back; disclaimers kept with the button. | `renderCreateAction` |

---

## 3. Follow-up questions for Audri

| # | Question | Assumed default (shipped) | Audri's answer |
| --- | --- | --- | --- |
| Q1 | Parsing screen — 4 fixed phases with spinner, no per-file detail? | 4 fixed phases + spinner, no per-file narration | **Confirmed** (2026-07-23): "displaying 4 fixed steps and the corresponding spinner." |
| Q2 | Document scroll — page-turn at the edge, or scroll-within-page only? | Scroll through pages, advancing at the edge | **Confirmed** (2026-07-23): "I wanted the page to turn at the edge of the page." → delivered as continuous multi-page scroll, which turns pages at the edge smoothly. |
| Q3 | Collect-info excluded roles — exact set? Audri named Buyer/Seller/Co Agent. | Hide on buyer, seller, and **both** agent roles; show on vendors | Open |
| Q4 | Expiration cards — suppress entirely vs. rename "Counter Offer 1 Expiration"? | Suppress entirely (they can never be actionable post-acceptance) | Open |
| Q5 | Dual rep (Buyer & Seller) fee model — capture both sides + seller contribution? | Capture listing + buyer-agent + seller contribution | Open |

---

## 4. Verification procedure (real Chrome, admin account)

1. Log in with the admin account through the real login form.
2. New Transaction wizard → Step 1: pick representation; confirm the question is
   centered/prominent and the choices sit below it.
3. Upload the **10 PDFs together** from `velvet-elves-data/testing_docs/`
   (`Amend #1`, `C#1`–`C#4`, `EM`, `PA`, `Post-Closing Possession`,
   `Pre-approval letter`, `SD (signed)` — all for 5915 E 350 N).
4. Start extraction; confirm the parsing screen shows only the 4 fixed phases.
5. Step 2 (Contract Details): confirm "Find in Document" (magnifier) locates and
   highlights values; confirm the document pane scrolls continuously through all
   pages when the mouse is over it.
6. Step 3 (Contacts & Fees): confirm the fee section matches the representation
   (buyer = single professional fee; seller/dual = listing + buyer-agent + seller
   contribution); confirm the billing-fee sentence and orange clause box are
   gone; confirm a vendor card offers "Create a task to collect this
   information."
7. Verification (Step 4): confirm the "needs your eyes" cards are clear with no
   expiration deadlines; fees show "Paid by Buyer/Seller"; deferred-contact tasks
   are listed; the Upload Transaction button is at the bottom.

Testing fixture set: 10 documents for **5915 E 350 N** (Koenig), a financed
purchase with a purchase agreement, four counter offers, an amendment, earnest
money, seller's disclosure, post-closing possession, and a pre-approval letter.
