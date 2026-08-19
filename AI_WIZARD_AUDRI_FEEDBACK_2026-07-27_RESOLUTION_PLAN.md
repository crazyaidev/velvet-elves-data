# AI Wizard - Audri 7/27 Feedback: Root-Cause Findings and Resolution Plan

**Date:** 2026-07-28
**Author:** Jan (investigation and plan; no source changes made)
**Scope:** Every item in Audri's 2026-07-27 testing feedback, plus the open threads from the Q&A rounds (pre-approval expiration, collect-info task behavior, fee scripting).
**Method:** Live two-stage end-to-end test in real Chrome (puppeteer-core driving the installed Chrome binary, headless), local stack (backend :8000 at commit `32868ec`, vite dev :5173), all 10 PDFs from `velvet-elves-data/testing_docs/` uploaded at once, representation = Seller. Stage 1 ran on Anthropic `claude-sonnet-5`, stage 2 on OpenAI `gpt-5.4`. Both stages walked Upload -> Contract Details -> Contacts & Fees -> Verification -> Upload Transaction, created a real deal each (Claude: `4bc8209a`, OpenAI: `760e8039`), and captured the workspace Tasks tab. Nothing below is speculation: every root cause was either reproduced in the browser or pinned to the exact source line, usually both.

> **Testing environment notes.**
> - Anthropic billing is fixed: `POST /settings/ai-provider/test` returned `ok: true` for `claude-sonnet-5` in 2.7 s, and the full packet parse succeeded on Claude. The 7/24 "credit balance too low" blocker is gone.
> - Two throwaway tenants were created for the runs (`ve.wizardtest.0728@gmail.com`, `...0728b@gmail.com`, both onboarding-completed via API; each used its free first deal). They are isolated test tenants on the dev Supabase and can be deleted at will.
> - Evidence (screenshots, page-text dumps, all API response bodies) is in this session's scratchpad under `evidence/claude/` and `evidence/openai/`. The load-bearing numbers and strings are quoted inline below because the scratchpad is ephemeral.

---

## 0a · Implementation status (2026-07-28)

Batches 1-3 of §8.6 are **built** (uncommitted, per the no-commits rule). What landed:

| Item | Status | Where |
|---|---|---|
| 2 · Step headers | Built | Phase heading above the double-check banner on every step |
| 3 · "Still thinking" parse copy | Built | Elapsed-time headline rotation at 20s / 45s / 90s / 180s |
| 4 · County | Built | `county` added to prompt schema, `PropertyExtraction`, provider result, merge list, FE apply + citation |
| 5 · Insured Conventional | Built | Prompt enum extended + explicit rule; FE map handles the reversed "Conventional - Insured" wording |
| 6 · UUID in the chip | Built | `resolveSourceDocumentName` maps a model-written source onto a real upload; a UUID can never render |
| 7 · See in Doc | Built | One `SeeInDocButton` (page icon + label) at every source site; citation field list extended; backstops now cite file + page |
| 8 · Notes placeholder | Built | Her example wording verbatim |
| 9 · No assumed buyer-agent fee | Built | Last-deal prefill no longer carries any buyer-side figure |
| 10 · Payer follows Step 1 | Built | `seed_fee_payers`, guarded on blank fees |
| 11-13 · Fee copy | Built | Subtitle and both helper lines removed; Title Case across wizard, Verification, workspace |
| 14 · Question-first buyer-agent card | Built | Buyer-agent total no longer collected on listing-side deals |
| 15 · No inferred remainder | Built | "rest Paid by Buyer" removed from Verification and `DealFeesSection` |
| 16 · Created moment | Built | `TransactionCreatedCelebration` renders on the workspace at `?created=1` |
| 17 · Raw OAuth JSON | Built | `humanize_send_failure` classifies the failure; raw payload goes to logs only |
| §7.1 · Fee percent validation | Built | Inline warning per card + create gated with a jump back to the fee step |
| Q5 · Collect-info transparency | Built (copy) | The defer confirmation now names who gets contacted |

**Tests:** backend **1356 pass** (full suite), including 2 backstop assertions updated to the new citation contract, 1 new backstop-citation test, and 3 new executor-wording tests. Frontend: WizardFlow **70/70** (7 assertions updated to the new intended contract), all unit suites **253/253** including 12 new tests in `wizardFeesAndCitations.test.ts`, `tsc` clean, ruff clean.

**Live re-verification (real Chrome, all 10 PDFs, both providers).** Re-ran the §8.4 protocol against the rebuilt stack. Confirmed on screen:
- Step body headings render ("Upload", "Contract Details") above the green banner.
- Parse headline rotates on both providers: `Reading your contract…` → `Still thinking…` (t≈21s) → `I promise I'm still working.` (t≈47s) → `Big packet — worth the wait.` (t≈92s) → `Extraction complete`.
- **Every** AI-filled Contract Details field now carries "See in Doc" — Street/City/State/ZIP, County, Price, Earnest Money, both dates, Possession, Days For Homeowners Commitment, Days For Home Inspection, and Inspection Deadline Date. Only Notes (user-typed, uncited) has none, which is correct.
- Chips read `AI read: Buyer · 85% · Purchase Agreement · page 6` — document name and page, never an id.
- Fee cards: `Listing Professional Fee` / `Buyer Agent's Professional Fee` (question only, no amount box until Yes) / `Transaction Fee`; helper lines and the section subtitle gone; "Who pays?" opens on **Seller** for a seller-rep deal.
- Verification summary: `Listing Professional Fee 2.5% · Paid by Seller`, `Buyer Agent's Professional Fee 2% · Paid by Seller`, `Transaction Fee $275 · Paid by Seller` — no inferred remainder anywhere.
- Typing `275` with the `%` unit selected shows the inline red warning and **blocks create**; the deal's free credit was still unspent afterward, proving the gate fired instead of the old server-side 422.
- The centered "Transaction Created!" moment renders full-viewport on the workspace with live counts (26 Tasks / 12 Checklist items / 10 Documents) and auto-dismisses to the receipt strip.
- Workspace task boxes: every amber reason is plain English; no provider JSON anywhere.

Two things the live run corrected mid-build, both now fixed and covered by tests: providers write page references as `p6` as well as `page 6` (the parser accepted only the latter, which silently cost those fields their jump), and a short reference like `PA` substring-matched `Amend #1 to PA …` (the resolver now scores candidates and refuses an ambiguous match rather than naming the wrong document).

**Field note on County.** Both providers return `Franklin` at low confidence (0.55) — and that is what the contract says: the citation is the PA's own form field, `County, = Franklin`. The extraction is faithful to the document; if the form was filled in with the town rather than the county, the honest fix is the agent correcting it in the field, which the low-confidence flag invites.

**Not yet built** (batches 4-6): session timeout (1, pending Audri's 24h confirmation), pre-approval expiration card + expired-letter email (§6.2), the AI actually *working* the collect-info task (§6.3 execution), and the two investigations (§7.2 double-check chronology, §7.3 referenced-doc false positive).

---

## 0 · Executive summary

| # | Audri's item | Live repro | Root cause | Size |
|---|---|---|---|---|
| 1 | Auto sign-in never times out | Confirmed by design reading | Silent token refresh + localStorage, no session cap (`constants.ts:307-313`) | S |
| 2 | No step header above the fields | Confirmed (all 4 steps) | Step bodies render content directly; only the top-center "Step X of 4" exists | S |
| 3 | Parsing >15-20 s needs playful copy | Confirmed: static copy for 364 s (Claude) / 176 s (OpenAI) | `renderParsing` header is a fixed string, no elapsed-time rotation | S |
| 4 | County not pulled | Confirmed: County empty both providers | `county` absent from extraction schema and prompt (deliberate "Category B" gap) | M |
| 5 | "Insured Conventional" pulled as "Conventional" | Root-caused (fixture can't repro, see §3.2) | Prompt enum `<conventional\|FHA\|VA\|USDA\|cash\|null>` cannot express it | S |
| 6 | UUID reference in the AI chip; want doc name + View in Document | Root-caused; provider-dependent | Chip renders the raw model-authored `source` string; prompt allows "document id **or** file name" | M |
| 7 | Magnifier -> page icon + "See in Doc", on ALL fields | Confirmed: County, Days For Home Inspection, Inspection Deadline Date have no icon | Icon gated on citation existence; `EVIDENCE_CITATION_FIELDS` omits those keys; backstop sources carry no page | M |
| 8 | Notes placeholder needs an example | Confirmed: "Additional notes for this transaction…" | Static placeholder (`NewTransactionWizard.tsx:7924`) | XS |
| 9 | Never assume buyer-agent fee | Partially present | Last-deal prefill seeds every fee incl. buyer-agent; summary invents "rest Paid by Buyer" | S |
| 10 | Transaction fee payer should follow Step 1 answer | Confirmed static | `EMPTY_FEE.payer: 'seller'` hardcoded (`wizardTypes.ts:1124`) | S |
| 11-13 | Fee card titles/verbiage | Confirmed verbatim | Strings at `NewTransactionWizard.tsx:6712-6776` | XS |
| 14 | Buyer-agent card: question first, amount only after Yes | Confirmed: amount box shows up front; "rest…" line after Yes | Card structure at `:6721-6761` | S |
| 15 | Verification: drop "rest Paid by Buyer", capitalize | Confirmed: "2.5% · Paid by Seller 2%, rest Paid by Buyer" | `feeSummaryRows` at `:8093-8107` + workspace `DealFeesSection.tsx:39` | S |
| 16 | "Transaction Created" bigger, centered, fun | Confirmed worse: the toast never visibly appears | Corner `toast()` at `:4816` races the navigation to the workspace | S |
| 17 | Raw OAuth JSON in task descriptions | Mechanism reproduced with friendly variants | `ai_task_executor.py:474-476` interpolates the provider's raw `error_message` | S |

Plus: three trailing Q&A decisions to build (§6), five new findings from the test itself (§7), and the repeatable two-stage test protocol with per-item acceptance assertions (§8).

---

## 1 · Session and auth (item 1)

**Audri:** "The system still signs me in without asking for the UN and PW. This should time out after a set time. Does 24 hours make sense, or should it be less?"

**Current behavior (by design, verified in source).** The app stores `velvet_elves_token` and `velvet_elves_refresh_token` in localStorage and silently refreshes the access token 60 s before expiry (`src/utils/constants.ts:307-313`, refresh loop in the auth layer). Refresh tokens rotate indefinitely, so a browser that has signed in once stays signed in forever. Nothing is broken; there is simply no session ceiling.

**Fix design.**
- Record `auth_time` (first credential login) alongside the tokens. On app load and before every silent refresh, if `now - auth_time > SESSION_MAX_AGE`, clear both tokens and route to `/login` with a "signed out for your security" notice.
- Default `SESSION_MAX_AGE` = 24 hours. 24 h is the right default for this product: users are real-estate professionals living in the app all day, and shorter caps (bank-style 15-30 min idle) would punish them hourly. Anything longer stops being a security measure.
- Add a "Keep me signed in for 30 days" checkbox on the login form for users who explicitly opt out of the daily re-auth (opt-in persistence instead of silent-forever persistence).
- Server side, set the Supabase refresh-token TTL to match so a stolen refresh token dies on the same clock.

**Answer to her question, for the reply email:** yes, 24 hours is the right default; I would not go shorter without an idle-timeout design, and I propose an optional "keep me signed in" for people who hate typing passwords daily.

**Test.** Sign in, set the stored `auth_time` back 25 h via devtools, reload: must land on /login. Fresh sign-in must survive a reload. Automated variant included in the protocol (§8.5).

---

## 2 · Wizard chrome (items 2, 3, 16)

### 2.1 Step headers (item 2)
**Verified.** All four steps identify themselves only in the top-center bar ("Step 4 of 4 · Verification"). The step body starts directly with content: on Verification that is the green double-check banner (her Screenshot_4), on Contract Details the intro paragraph.

**Fix.** Add a serif step heading at the top of each step body, above any banner: "Upload", "Contract Details", "Contacts & Fees", "Verification". Same type treatment as the existing serif section titles (20 px serif per the comfort scale), with the top-center stepper untouched, exactly as she asked ("the header in the center will stay").

### 2.2 "Still thinking" parse copy (item 3)
**Verified live.** The parse screen shows "Reading your contract…" / "Pulling the parties, dates, price, and deadlines from your documents." as a fixed string for the whole parse. Claude took **364 s**, OpenAI **176 s**; the copy never changed once (screenshots at t=15/45/120/240 s are identical apart from the phase ticks). The same static screen serves re-runs ("Re-running…").

**Fix.** In `renderParsing` (`NewTransactionWizard.tsx:6140`), rotate the headline on elapsed time, keeping the 4-phase list exactly as is (it was Audri's earlier "less is more" request, so only the headline gets playful):
- 0-20 s: "Reading your contract…"
- 20-45 s: "Still thinking…"
- 45-90 s: "I promise I'm still working."
- 90-180 s: "Big packet! Worth the wait."
- 180 s+: "Almost there - triple-checking the fine print."
Final copy list to be tweaked at build time; requirement is: first rotation at ~15-20 s, light-hearted tone, applies to first runs and re-runs alike.

### 2.3 The created moment (item 16)
**Verified worse than reported.** The success path fires a standard corner `toast({ title: 'Transaction Created' })` (`:4816`) and immediately navigates to the new workspace (`/transactions/<id>?created=1`). In both live runs the toast was **never visible in any capture** (0.6 s, 1.8 s, 9 s after click): the navigation unmounts/obscures it. Audri saw it on staging where navigation is slower; locally it simply vanishes.

**Fix.** Replace the toast with a centered full-screen success moment rendered by the *workspace* when it mounts with `?created=1` (that flag already exists and the workspace already shows a quiet "Created just now · 26 tasks · 12 checklist items · 10 documents attached · Fees captured" band, verified live). Design: dimmed backdrop, large serif "Transaction Created!", the receipt numbers it already computes, a small celebratory flourish consistent with the brand (sparkles motif, no confetti library), auto-dismiss ~2.5 s or on click. Rendering it on the workspace side kills the race by construction.

---

## 3 · Extraction gaps (items 4, 5)

### 3.1 County (item 4)
**Verified live on both providers:** County input empty, no source icon, while address/city/state/zip filled correctly. **Root cause:** `county` does not exist anywhere in the extraction pipeline - not in `PropertyExtraction` (`document_packet_parsing.py:174-178`), not in the prompt schema (`providers/prompts.py`), and the frontend comment says so explicitly ("Not extracted today (Category B - county, parcel/tax ID …)", `wizardTypes.ts:471`). Only Google-address autocomplete can fill it today. The model is never asked, so it can never answer.

**Fix (follows the packet-extraction-typed-schema-drift invariant: model + prompt + FE in the same change).**
1. `PropertyExtraction.county: str | None` + prompt schema key `property.county` + a source entry required like every other field.
2. FE apply: map `extracted.county` into `address.county` via `applyIfBetter`, with citation.
3. Add `county` to `EVIDENCE_CITATION_FIELDS` so it gets the See-in-Doc affordance (§4).
4. Keep the Google-autocomplete fallback; extraction wins only when the user hasn't typed.

**Test.** On the 5915 packet the property is in Johnson County, IN; assert County = "Johnson" (or exactly what the PA page 1 states) with a page-1 citation, both providers.

### 3.2 Insured Conventional (item 5)
**Root cause (definitive, schema-level).** The prompt hard-constrains the value: `"financing_type": "<conventional|FHA|VA|USDA|cash|null>"` (`providers/prompts.py:21`). "Insured conventional" is not in the enumeration, so a model that reads the "Insured Conventional" checkbox *must* collapse it to `conventional`. The frontend map is already able to display it (`'insured conventional': 'Insured Conventional'`, `NewTransactionWizard.tsx:2422`) - it just never receives it. This exactly produces her Screenshots 6-8.

**Fixture caveat, discovered live.** Our 5915 test packet cannot reproduce her case: OpenAI's citation quotes the PA page 2 as `'[X] Conventional [ ] Insured Conventional [ ] FHA [ ] USDA [ ] VA'` - plain Conventional is genuinely the marked box, and both providers correctly returned `conventional` at 0.85-0.95 confidence. Audri tested with her own 3885 Honey Creek Ct packet, where **Insured Conventional** is marked (her Screenshot_6). We need either her packet or a one-page fixture with Insured Conventional marked for the regression test (§8.3).

**Fix.**
1. Extend the prompt enum: `<conventional|insured conventional|FHA|VA|USDA|portfolio|hard money|cash|other|null>` with an explicit instruction: "when the marked checkbox is 'Insured Conventional', return `insured conventional`, never plain `conventional`" (checkbox glyph guidance already exists for title/inspection; mirror it).
2. Harden the FE map with synonyms ('conventional insured', 'conventional - insured') since pre-approval letters word it backwards ("Conventional - Insured", her Screenshot_7). Unknown strings keep falling back to 'Other'.
3. Priority rule stays: the PA checkbox is the controlling source, the pre-approval letter is corroboration.

---

## 4 · Source citations and "See in Doc" (items 6, 7)

### 4.1 The UUID in the orange chip (item 6)
**Root cause, with a provider twist confirmed live.** The amber "AI read: …" chip renders the model-authored source string **verbatim**: `{recommendation.source}` at `NewTransactionWizard.tsx:10864`. The prompt tells the model a source entry "must include document id **or** file name" (`document_packet_parsing.py:400-406`) - so what the chip shows is whatever the model felt like writing:
- Claude this run: `PA (page 6): '…'` (readable)
- OpenAI this run: `PA_-_5915_E_350_N.pdf page 2: '…'` (readable)
- OpenAI on Audri's staging run: `aa6ea579-9caf-43b3-8807-5dcc87f72fd4 page 1: …` (the raw `<DOCUMENT id>` header, her Screenshot_8)

Same code, three formats. Rendering a model-composed string raw is the bug; the UUID is just its ugliest outfit.

**Fix (belt and braces).**
1. Prompt: "reference the document by its `file_name`, NEVER by its id" (ids stay for the `documents[]` inventory where they are load-bearing).
2. FE: stop rendering the raw string. Parse it (`parseSourceCitation`) and resolve the document to a display name via the existing `resolveDocumentDisplayName(documentId, documents)` (`wizardTypes.ts:413`, already powering the compliance cards' "Counter Offer · page 1" lines, verified rendering correctly this run). Chip becomes: `AI read: Seller · 87% · Counter Offer One · page 1`. Defensive rule: any UUID-shaped token in a source string is never displayed.
3. Add the click-through she asked for: a right-aligned **"See in Doc"** action inside the chip (same jump the compliance cards' source line does), using the §4.2 shared affordance.

### 4.2 Page icon + "See in Doc", on every field (item 7)
**Verified live.** On Contract Details, fields with citations show a bare magnifier icon; fields without citations show nothing. Missing the icon in both provider runs: **County** (no extraction), **Days For Home Inspection**, **Inspection Deadline Date**; **Possession Date** had it under OpenAI but *not* under Claude. Matches her Screenshot_10 list.

**Two distinct root causes:**
1. **Frontend allow-list gap:** `EVIDENCE_CITATION_FIELDS` (`wizardTypes.ts:474-503`) omits `inspection_days` (and `county`); the citation map is only built for listed keys, so even though Claude returned a perfectly good source for inspection days (verified in the packet payload: `PA (page 4): 'Buyer shall have 15 days…'`), the UI throws it away.
2. **Backstop sources carry no page:** Claude's possession came from the deterministic backstop with `source: "possession_clause_backstop"` - no page, no snippet -> no icon. OpenAI extracted possession directly with a real citation -> icon. Same field, different provider, different UI.

**Fix.**
1. One shared `SeeInDoc` affordance: page/file icon (lucide `FileText`) + visible label "See in Doc", replacing the bare `Search` icon at all its render sites (field rows, `ReviewDataRow:10549`, party rows, `ProposalSourceLine:10446`, the intro sentence at `:8349` which should now say "Click See in Doc on any value…"). Keep the aria labels.
2. Extend `EVIDENCE_CITATION_FIELDS` with `inspection_days`, `county`, `earnest_money_days`, `inspection_response_days`, and the boolean drivers (`has_inspection`, `has_home_warranty`, `has_hoa`) - backend sources-parity (2026-07-24 fix) already requires the model to source every non-null field, so the data is there.
3. Derived fields inherit their driver's citation: Inspection Deadline Date (computed from acceptance + inspection_days) carries the inspection_days citation.
4. Backstops must emit page-bearing sources: they read a located clause, so `apply_possession_backstop` (and the title/inspection backstops) should stamp `"<file_name> page N: '<clause>'"` instead of the bare marker string, keeping the marker as a suffix for provenance (`document_packet_parsing.py:896/935/992`).

**Test.** Assert every AI-filled field on Contract Details renders a "See in Doc" control, both providers; assert Possession Date has one even when the backstop filled it (Claude path).

---

## 5 · Fees (items 9-15) and Notes (item 8)

All string/structure findings verified live this run; exact current strings quoted from the DOM dumps.

### 5.1 Card copy (items 11, 12, 13)
- Remove the subtitle under "Fees" ("The professional fees on both sides of this deal, and any transaction fee." / the buyer-rep variant) - `NewTransactionWizard.tsx:6772-6776`.
- "Listing professional fee" -> **"Listing Professional Fee"**; delete "What the listing side earns on this deal. Paid by the seller." - `:6712-6717`.
- "Buyer agent professional fee" -> **"Buyer Agent's Professional Fee"**; delete "What the buyer's agent earns on this deal." (and the dual variant) - `:6722-6729`.
- Same Title Case sweep on: Verification row labels (`:8094/8101`), the workspace `DealFeesSection.tsx` and `FeeEditDialog.tsx` (they mirror the card anatomy), and "Transaction Fee".

### 5.2 Buyer-agent card restructure (item 14)
**Current (verified):** the card shows the buyer-agent *total* fee amount up front, then the seller question; answering Yes reveals "How much is the seller paying?" plus the line "The rest of the buyer agent's fee is paid by the buyer."

**Target (her Screenshots 15-17):** the card is *question-first and question-only*:
1. Title only. Then: "Is the seller paying any of the buyer agent's fee?" Yes / No (still starts unanswered - keep the never-default behavior).
2. On Yes: "How much is the seller paying?" + amount with %/$ toggle.
3. The buyer-agent **total** fee input is removed from listing-side deals entirely (we only know what our seller pays; the rest is not our data). The buyer-rep single "Professional Fee" card is untouched.
4. Delete the "rest of the buyer agent's fee…" sentence (`:6755-6757`).
`fees_json` keys stay for compatibility; the wizard just stops collecting `buyerAgent` total on listing side, and `DealFeesSection`/Verification display only what was answered.

### 5.3 No inferred remainder on Verification (item 15)
**Current (verified):** `Buyer agent professional fee - 2.5% · Paid by Seller 2%, rest Paid by Buyer`, built at `:8104`; the no-contribution branch `:8105` even renders `· Paid by Buyer` - both are assumptions Audri explicitly banned ("We assume the buyer is paying zero since we do not have that info"). The workspace duplicates the string (`DealFeesSection.tsx:39`).

**Target:** with the §5.2 restructure the row becomes simply `Buyer Agent's Professional Fee - 2% · Paid by Seller` (or the row is absent when the answer was No/unanswered). Both render sites change together.

### 5.4 Defaults follow Step 1 (item 10) and no assumed buyer-agent fee (item 9)
- **Payer default:** `EMPTY_FEE.payer` is hardcoded `'seller'` (`wizardTypes.ts:1123-1127`). Fix: initialize the Transaction Fee payer (and the buyer-rep Professional Fee payer) from the Step 1 representation when the fee step first renders: Buyer -> buyer, Seller -> seller, Buyer & Seller -> seller. A payer the user has touched is never overwritten.
- **Prefill scope:** the last-deal prefill (`loadLastFees()` -> `prefill_fees`, `NewTransactionWizard.tsx:3198-3203`) currently carries **every** fee field. Fix: strip `buyerAgent`, `sellerPaysBuyerAgent`, and `sellerBuyerAgentShare` from what prefill applies; listing fee and transaction fee remain prefillable ("For listings and dual we can assume the Listing Professional Fee"), still behind the existing "Looks right" confirmation gate.
- **"Unless otherwise stated in the contract":** the contract-mentions hint was removed from the fee card on 2026-07-22 (comment at `:6623-6627`) because it quoted useless boilerplate. Reinstate it *narrowly*: only when the extraction found an actual amount for the buyer-agent side (e.g. a stated co-op commission), show a read-only hint with document name + page + See in Doc. Never auto-fills.

### 5.5 Notes placeholder (item 8)
`:7924`: `"Additional notes for this transaction…"` -> `"Additional notes for this transaction… e.g. Need to collect Lead Based Paint disclosure."` Exactly her wording.

---

## 6 · Post-create tasks and the trailing Q&A decisions

### 6.1 Raw OAuth JSON in the task boxes (item 17)
**Mechanism fully reproduced.** The amber box under a task is the executor's `_surface_task` reason. Live run (no mailbox connected on the test tenant) rendered the friendly variants: "The AI prepared this email, but there's no connected mailbox to send it from…" and "This task has been overdue since 2026-06-27. The AI won't send an email this late without your say-so…". Audri's Screenshot_19 came from the third branch: send attempted and failed, where the code interpolates the provider's raw error verbatim - `f"Sending this email failed ({sent.error_message})…"` (`ai_task_executor.py:474-476`). On staging the Gmail token is dead, `error_message` is Google's full OAuth-401 JSON blob, and that goes straight into the UI. So: not a parse error, exactly the message that was designed to populate - the design is wrong in that one branch.

**Fix.**
1. Classify send failures into plain English before surfacing, reusing the category taxonomy the AI-settings test endpoint already ships (auth / rate_limit / connection / provider_down / unknown, `ai_settings.py:68-84`). The Screenshot_19 case becomes: "Your Gmail connection has expired, so this email could not be sent. Reconnect Gmail in Settings -> Integrations, then send the prepared draft from AI Emails." Raw provider JSON goes to server logs only.
2. Guard rule: no `_surface_task` reason may ever contain a raw provider payload; add a unit test that feeds a Google-style JSON error through and asserts the surfaced text is the friendly line.
3. The *trigger* on staging remains the dead Gmail token + unwired scheduler (tracked in `GMAIL_GOOGLE_APPROVAL_REMAINING_TASKS.md` §D: deploy scheduler, manual tick, reconnect Gmail). This plan fixes the symptom's rendering; that doc owns the infra cause.

### 6.2 Pre-approval / financing-letter expiration (Q2 conclusion + Q1 answer)
**Current state (verified in source and live):** all expirations are suppressed - prompt ban plus the `_EXPIRATION_LABEL_RE` net that explicitly includes "pre-approval or financing pre-qualification letter expiration" (`intake_intelligence.py:163-191`); zero expiration mentions rendered in either run. Audri wants pre-approval/proof-of-funds expiration back as a compliance call-out, and: "If it's expired the AI agent should send an email to the lender, and copy both agents (if applicable), asking for an updated version… We won't worry about ones expiring."

**Build design.**
1. **Extraction:** a dedicated `financing_letter` block on the pre-approval document type: letter date, explicit expiration date if stated, or stated validity window (the Koenig fixture letter states no date but "still shopping 90 days beyond the date of this letter" -> derived expiration = letter date + 90). No date and no window -> no finding (honest absence).
2. **Surface:** a small "Compliance note" card on Verification (its own card, since it is neither a calendar deadline nor a waivable checklist row): "Pre-approval letter expired Jun 30 - Koenig letter · page 1 [See in Doc]". Not blocking, informational, with the citation.
3. **Action when expired at intake:** queue the AI email to the loan officer, CC both agents, requesting an updated pre-approval/proof of funds "for compliance". Runs through the standard task/email machinery (an Automated task named e.g. "Request Updated Pre-Approval"), so the deal's automation posture governs draft-vs-send, and a missing loan-officer email degrades into the §6.3 collect-info behavior. Expiring-but-not-yet-expired: no action, per Audri.
4. Narrow the suppression regex so this one finding type passes; every other expiration stays banned.

### 6.3 Collect-info tasks: transparency + AI works the task (Q5 conclusion)
**Current state (verified in source):** deferring a vendor's details creates a manual task due immediately, addressed to nobody; the confirmation line says only "A task will be created to collect X's contact details" (`NewTransactionWizard.tsx:11822-11829`). Audri: the user "should know whom is being contacted for the info", and the AI should work the task.

**Build design.**
1. **Transparency at defer time.** The confirmation line states the actual plan, computed from what is known at that moment:
   - vendor email known, phone missing: "I'll email {vendor} to ask for a phone number and any additional contacts (processors, assistants)."
   - nothing known: "I'll email you and the co-op agent ({name}) to ask for {vendor}'s contact details."
2. **Execution.** Register the "Collect contact details for …" task name in the AI task executor (name-keyed like the welcome tasks):
   - Partial contact -> email the vendor directly asking for the phone number and any additional contacts they want on file.
   - Zero contact -> email the agent (account holder) and the co-op agent, asking the co-op agent for the vendor's details (their vendor, their rolodex).
   - Both respect the deal's automation posture (Manual = draft in AI Email Review; Automated = send and complete). Replies land through the normal inbound flow; filling the Contacts tab from a reply is phase 2 (the reply sits in AI Emails for one-click apply in phase 1).
3. Due-immediately stays as built.

### 6.4 Title-company welcome scripting (Q3/Q4)
Blocked on Audri: she owes the scripts ("I'll send you scripts to outline what this looks like"). The fee data the scripts need (listing fee, seller's share of the buyer-agent fee) is captured and will survive the §5 restructure. No build until the scripts arrive; the reply email should nudge for them.

### 6.5 Own-profile prefill (Q1 trailing "Agreed but…")
Already built (own agent card prefilled from profile, "From your profile" tag, save-back of missing phone/brokerage). Goes into the regression checklist (§8.5) rather than new work.

---

## 7 · New findings from this test run (not in Audri's list)

1. **Fee validation gap (found by accident, real bug).** The harness initially set the transaction fee to 275 with the % unit still active. The wizard let it through to the server, which correctly rejected it (`422: "A percentage fee cannot exceed 100"` on `fees_json.transaction.seller`), and the UI showed only a generic corner toast "Could not create transaction - Request validation failed." Fix: inline validation on percent fee inputs (>100 flags the field before create) and map create-422 `details[].loc` back onto the offending field with a specific message. A user typing a typo'd "275%" today gets a dead-end error at the very last click.
2. **Double-check price recurrence under OpenAI.** The verification pass disagreed on purchase price: pass 1 = 992,000, pass 2 = **950,000** - the superseded C#2 price beating C#3's controlling 992k *in the second read*, despite the counter-sequence prompt rule added 2026-07-15. It surfaced correctly as a blocking verify card (resolved by clicking "First read"), so no wrong data landed, but it recreates needless blocking friction on a clean packet. Fix: feed the resolver's document chronology into the double-check pass (or strengthen its counter-sequence rule), and add the packet to the double-check regression tests. Claude's pass agreed on all 7 fields ("AI double-checked 7 critical fields - both reads agree", green banner verified).
3. **Referenced-document false positive under Claude.** Verification showed "1 referenced document not uploaded - counter_offer sequence appears incomplete; missing document number(s): 1" although C#1-C#4 were all uploaded and individually parsed. Not root-caused this session; needs a look at the sequence detection in `contract_resolution.py` with the captured payloads. (OpenAI run: no such banner.)
4. **Provider profile differences (informational, for the model recommendation).** Claude `claude-sonnet-5`: parse 364 s, packet confidence 74%, three sub-band recommendation chips, two needs-eyes deadline cards, one waive suggestion, one referenced-doc banner. OpenAI `gpt-5.4`: parse 176 s, confidence 84%, zero chips/cards, one compliance-review group, but the §7.2 double-check disagreement. Extracted *values* were identical on every ground-truth field (address, city, state, zip, price 992k, EM 9k, acceptance 6/27, closing 7/31, possession 8/30, inspection 15, insurance 25, EM-delivery 4 business days) - the 2026-07-24 parity fix holds.
5. **Console hygiene.** Two warnings on the wizard route worth a small cleanup: `Query data cannot be undefined … ["ad-slot","wizard_confirmation"]` and a `PopChild ref` warning from the animation wrapper.

---

## 8 · Testing strategy

### 8.1 Principles
- Every fix lands with (a) a targeted unit/regression test and (b) a line in the live-browser acceptance checklist below. UI work is screenshot-gated as always.
- The live test is the arbiter: the same two-stage, all-10-PDFs protocol used for this investigation, re-run after the build. Real Chrome (installed binary via puppeteer-core), real backend, real Textract + LLM calls, no mocks.

### 8.2 Environment
- Local stack: current backend on :8000, vite dev on :5173 (verify freshness first: process start vs latest commit; restart uvicorn if stale - long-running :8000 has bitten before).
- Two dedicated test tenants (reuse `ve.wizardtest.0728` / `0728b` or mint fresh ones; onboarding-complete via `POST /onboarding/complete`). Tenant A pinned to Anthropic via `PUT /settings/ai-provider`; tenant B stays on the OpenAI default. Preflight both providers (`GET /ai/preflight`, `POST /settings/ai-provider/test`) before starting; abort with an honest report if either fails (no silent provider swap, per the no-auto-switch rule).
- Billing: each fresh tenant carries one free deal; a re-run that needs a second create either mints a fresh tenant or grants a credit first. Budget one deal per stage.

### 8.3 Fixtures
- **Baseline packet:** the 10 `testing_docs/` PDFs (5915 E 350 N), uploaded simultaneously, representation = Seller. Ground truth: the 12-field table in §7.4.
- **Gap to close:** the packet cannot exercise item 5 (its PA marks plain Conventional - verified from the extraction citation). Ask Audri for the 3885 Honey Creek Ct packet, or add a one-page Insured-Conventional PA fixture; that document then also carries the county assertion for a second county source.
- **Pre-approval expiration cases (§6.2):** the Koenig letter (dated 6/2/26 + 90-day window = not expired) is the negative case; add a copy with the date shifted back 5 months as the expired case.

### 8.4 Two-stage protocol (per stage: Claude first, then OpenAI)
1. Log in fresh (assert the §1 session rules while at it), open the wizard, pick Seller, drop all 10 PDFs at once, Start AI extraction.
2. During parse, sample the hero copy at 10/20/45/90/180 s (item 3 assertion: rotation begins by 20 s; re-run parse once to cover the re-run path).
3. Contract Details: dump every field (label, value, See-in-Doc presence), the chips, the Notes placeholder; assert items 2, 4, 5*, 6, 7, 8 (* on the Insured-Conventional fixture).
4. Contacts & Fees: assert card titles/copy, payer defaults from Step 1, question-first buyer-agent card, no prefilled buyer-agent fee (items 9-14). Fill listing 2.5%, seller-pays 2%, transaction fee $275 Seller.
5. Verification: assert step header, fee summary strings ("no rest Paid by Buyer", Title Case), compliance cards still name their documents, pre-approval compliance note on the expired fixture, and the fee inline-validation fix (type 275%, expect a field-level flag, not a server 422).
6. Create: assert the centered created moment (item 16), landing on the workspace, receipt band numbers.
7. Workspace Tasks tab: assert every amber reason is plain English (feed the executor a simulated provider-JSON failure in the unit suite; in the live run assert the no-mailbox and overdue variants render, and grep the page text for `{"error"` = must be absent) (item 17).
8. Capture everything (screenshots + DOM text + API bodies) exactly as this investigation did; the two stages must agree on the ground-truth values (§7.4 parity).

### 8.5 Regression guards to add in code
- Unit: fee summary builder (no remainder inference in any branch), prompt enum contains `insured conventional`, `EVIDENCE_CITATION_FIELDS` covers every AI-fillable Contract Details field (assert against the field registry so the next field can't be forgotten), executor error classifier (raw JSON in -> friendly line out), session-age gate, backstop sources carry a page.
- Existing suites to keep green: WizardFlow (68), backend packet/double-check suites; update the §15.2 chip test for the new chip format and the fee-card tests for the restructure.
- Manual/visual: the §2 headers and §2.3 created moment get before/after screenshots for Audri.

### 8.6 Order of work
1. Quick wins, one PR-sized batch: items 8, 11-15 strings + step headers (2) + parse copy (3) + payer defaults (10) + prefill scope (9). All XS/S, zero backend.
2. Extraction batch: county (4), insured conventional (5) + fixture, chip/See-in-Doc (6, 7), backstop citations. One coordinated FE+BE change per the schema-drift invariant.
3. Post-create batch: created moment (16), executor error classification (17), fee inline validation (§7.1).
4. Behavior builds: session timeout (1, pending Audri's confirmation of 24 h), pre-approval expiration card + expired email (§6.2), collect-info AI execution (§6.3).
5. Investigations: referenced-doc false positive (§7.3), double-check chronology (§7.2).
6. Blocked on Audri: title-company scripts (§6.4); Honey Creek packet (or approve the synthetic fixture); 24 h confirmation.
7. Full two-stage acceptance re-run (§8.4), then the reply email to Audri with before/after screenshots.

---

## 9 · Open questions for Audri (for the reply email)

1. **Session:** 24-hour re-login confirmed as the default? And do you want the optional "Keep me signed in for 30 days" checkbox, or hard 24 h for everyone?
2. **Insured Conventional regression:** can you share the 3885 Honey Creek Ct packet (or just its PA page 2 and pre-approval letter) so the exact case is in the regression set? Otherwise I'll build a synthetic fixture.
3. **Listing fee edge:** you mentioned a live deal where the buyer pays the full professional fee and the seller zero. The listing card assumes seller-paid with no toggle - should it get a quiet override for deals like that one, or is manual note-keeping fine there?
4. **Title-company scripts:** still waiting on the wording so the fee split can flow into the welcome email.

---

*Constraint honored: no source files were changed for this document; all line references are against backend `32868ec` and the current frontend working tree.*
