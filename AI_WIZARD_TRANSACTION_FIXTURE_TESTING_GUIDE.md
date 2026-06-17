# AI Wizard Transaction Fixture Testing Guide

Use `ai_wizard_transaction_test_fixture.pdf` to test the New Transaction wizard,
the Active Transactions page, and the transaction detail workspace.

This fixture was built from the current frontend and backend contracts:

- Wizard upload and packet parse: `NewTransactionWizard.tsx`, `useWizardApi.ts`
- Extraction schema and prompts: `app/services/providers/prompts.py`
- Packet parsing and double-check: `app/services/document_packet_parsing.py`
- Transaction create shape: `app/schemas/transaction.py`
- Task and compliance preview/generation: `task_generation_service.py`, `requirement_planner.py`
- Active transaction cards and detail workspace: `TransactionListPage.tsx`, `TransactionWorkspacePage.tsx`

## Fixture File

- PDF: `velvet-elves-data/ai_wizard_transaction_test_fixture.pdf`
- Generator: `velvet-elves-data/create_ai_wizard_transaction_fixture.mjs`
- Source baseline date: June 16, 2026
- All key deal dates are future-dated from that baseline.
- All contact emails use `@minafter.com`.
- The signature section is intentionally unsigned and contains only underlined
  blank spaces.

## Recommended Wizard Run

1. Open the full wizard at `/transactions/new`.
2. Select `Buyer & Seller` for represented side.
3. Upload `ai_wizard_transaction_test_fixture.pdf`.
4. Run extraction.
5. On the signature panel, expect the AI to treat the document as unsigned or
   not fully signed. Pick the option you want to test:
   - `Queue for signature` when testing e-sign handoff.
   - `Will collect later` when testing create flow without e-sign.
   - `Not required` only when testing the override path.
6. Confirm the address and party cards.
7. Confirm the acceptance-date anchor on the Timeline step.
8. Review the Compliance and Task steps, then create the transaction.

## Expected Extracted Values

Property:

- Street: `4567 Meadowridge Avenue`
- City/state/ZIP: `Boardman, OH 44512`
- County: `Mahoning`
- Parcel / tax ID: `41-12345-678-000`

Parties and contacts:

- Buyers: Jordan Ellis, Maya Ellis
- Sellers: Avery Morgan, Priya Morgan
- Listing agent: Nora Patel, North Coast Realty
- Buyer's agent: Luis Romero, MetroKey Realty
- Loan officer: Tessa Grant, Buckeye Home Loans
- Title / escrow rep: Elena Ruiz, Reliable Title & Escrow, Inc.
- Closing attorney: Marcus Lee, Lee & Chen Law
- Inspector: Owen Brooks, ClearView Inspections
- Appraiser: Riley Hayes, Mahoning Appraisal Group

Financial terms:

- Purchase price: `$342,500.00`
- Earnest money: `$7,500.00`
- Financing: Conventional mortgage
- Owner occupancy: primary residence

Dates:

- Contract acceptance: July 1, 2026
- Earnest money due: July 4, 2026
- Loan application due: July 6, 2026
- Inspection deadline: July 8, 2026
- HOA document deadline: July 8, 2026
- Inspection response deadline: July 10, 2026
- Survey review deadline: July 12, 2026
- Financing deadline: July 24, 2026
- Appraisal expected: July 31, 2026
- Insurance binder due: August 4, 2026
- Final walk-through: August 13, 2026
- Closing: August 14, 2026
- Possession: August 16, 2026

Terms:

- Has inspection: yes
- Has HOA: yes
- Has home warranty: yes
- Warranty ordered by: Seller
- Title ordered by: Seller
- Closing mode: title / escrow

## What To Check In The Wizard

- The extraction timeline should show field-found events for address, parties,
  price, earnest money, financing, acceptance date, closing date, inspection
  deadline, and signature status.
- Source chips should jump to the matching PDF page for key fields.
- The signature review should not say all parties signed.
- Core missing info should be minimal. If the parser misses county, parcel ID,
  inspector, or appraiser, that is acceptable because those are supporting data,
  not required wizard gates.
- The Timeline step should include the core dates plus inspection, HOA, survey,
  financing, appraisal, insurance, walk-through, closing, and possession.
- The Compliance step should include conditional rows for inspection, HOA, and
  home warranty because the fixture opts into all three.
- The Review Tasks step should generate future-dated work. It should not create
  overdue tasks when tested on June 16, 2026.

## What To Check On Active Transactions

After creation, go to `/transactions/active`.

- Search for `Meadowridge`, `Ellis`, `Morgan`, or `minafter.com`.
- The card should show the buyer/seller display title or the property fallback.
- The price should show about `$342,500`.
- The close date should show `Aug 14, 2026`.
- Contact groups should contain principals, agents, lender, title, attorney,
  inspector, and appraiser when those parties were created.
- The card will usually land in `In Inspection` if the generated inspection
  response task is active and no inspection response date has been set.
- The card should not appear under `Overdue` on the June 16, 2026 baseline.

## What To Check On Transaction Detail

Open the transaction detail page from the card.

- Timeline tab: core dates and term rows should match the fixture dates.
- Compliance tab: missing document requirements should be visible with due
  dates derived from acceptance, inspection, HOA, and closing anchors.
- Documents tab: the PDF should be linked to the transaction.
- Tasks tab: generated tasks should have due dates that match the preview.
- People tab: all extracted party/contact records should be editable.
- Activity tab: create, document-link, requirement, and task-generation events
  should appear as available.
- Agent tab / Email tab: if the agent workspace flag is enabled, references
  should navigate back to the owning rows.

## Sanity Checks

- No original names from `test.pdf` remain in the new fixture.
- No `testmail.com` emails remain.
- No contact email uses any domain other than `minafter.com`.
- Signature names and signature marks are blank underlines only.
- Dates are concrete absolute dates, not relative-only phrasing.
