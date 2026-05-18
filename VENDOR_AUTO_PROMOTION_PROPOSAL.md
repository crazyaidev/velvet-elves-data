# Auto-Promote Wizard Parties to Vendors — Proposal

**Drafted:** 2026-05-18
**Author:** Jan (via Claude analysis pass)
**Status:** Research only. No code changes here — per Jan's instruction.
**Related docs:** [VENDOR_POSITION_IN_TRANSACTION.md](VENDOR_POSITION_IN_TRANSACTION.md), [M4_3_DOC_REMEDIATION_PLAN.md](M4_3_DOC_REMEDIATION_PLAN.md), [M4_2_VS_M4_3_OVERLAP_ANALYSIS.md](M4_2_VS_M4_3_OVERLAP_ANALYSIS.md).

---

## TL;DR

Your intuition is correct. **The wizard already collects inspector / appraiser / title-company / closing-attorney information, but it writes only to `transaction_parties` — not to the `vendors` directory.** That's why the "Email vendor" flow can't find them; users have to retype data the system already has. The recommended fix is a small **"Save as vendor"** prompt inside the wizard's parties step (or a one-click promote button on each existing service-provider party row) — not a silent auto-create. The reasoning and a concrete plan are below.

---

## 1. What I observed in the code

| Surface | What it does today | What it does NOT do |
|---|---|---|
| `NewTransactionWizard` ([wizardTypes.ts:309-340](../velvet-elves-frontend/src/components/wizard/wizardTypes.ts#L309-L340)) | Parses the contract via Milestone 2.x; collects parties with `party_role ∈ { buyer, seller, listing_agent, buyers_agent, loan_officer, title_rep, title_company, closing_attorney, settlement_attorney, inspector, appraiser, home_warranty, other }` | Does **not** create `vendors` rows. The service-provider parties go to `transaction_parties` only — one-shot, per-deal, no cross-deal reuse. |
| `transaction_parties` table | Stores all parties: contract parties (buyer/seller/agents) AND service providers (inspector/appraiser/title co.) in the same table, distinguished by `party_role`. | No link to `vendors.id`. The vendor-comms flow (Milestone 4.3) cannot use these rows. |
| `vendors` table | Tenant-wide durable directory; reusable across transactions; carries `company_name`, `email`, `phone`, `category`, `is_preferred`. | Populated only via direct user action (the new `AddVendorModal` I wired today). The wizard ignores it entirely. |
| `transaction_vendor_assignments` | Per-deal link: vendor company → transaction → role. Required for the M4.3 "Email vendor" workflow to find the right vendor for a task. | Created only via direct API call (no UI in `NewTransactionWizard`, no UI elsewhere yet). |

So today, after running the wizard with a fully-parsed contract:
- ✅ `transactions.address`, `closing_date`, etc. are populated.
- ✅ `transaction_parties` has every party the contract named.
- ❌ `vendors` is empty.
- ❌ `transaction_vendor_assignments` is empty.
- ❌ Clicking "Email vendor" on a task from this transaction shows the empty dropdown.

That is the gap you noticed.

---

## 2. Why it was built this way (and what I'd preserve)

Before recommending a change, here's the honest case for the current behavior — so we don't break something on purpose:

1. **Parties are one-shot facts; vendors are tenant-wide commitments.** Saving a company as a "vendor" is implicitly saying *"I plan to keep using this company."* That's a judgment call, not an automatic step. A buyer's contract might mention an inspector the agent has never worked with and won't again.
2. **Contract parser confidence varies.** The Milestone 2.x parser extracts most parties well, but service-provider sections of contracts can be ambiguous. Silently writing low-confidence extractions into the tenant directory pollutes it forever.
3. **Duplicate explosion.** Without an entity-resolution step ("Acme Inspection" vs "Acme Home Inspections, LLC" vs "ACME INSPECTION CO."), every transaction would create new vendor rows for the same real-world company. The directory becomes a graveyard within a quarter.
4. **PII retention.** Vendor emails/phones are Fernet-encrypted at rest, but they're persistent beyond the transaction. Auto-saving every service provider mentioned on every contract is a quieter form of "save everyone's PII forever."

These concerns rule out **silent** auto-creation. They do not rule out a deliberate, transparent **prompt** at wizard finish.

---

## 3. Recommended solution

A two-step pattern that respects both UX and data-quality concerns.

### 3.1 Inside the wizard — "Save service providers as vendors" step

After the parties review step (or as a small footer on it), show a single-screen panel listing only the parties whose `party_role` is in the service-provider subset:

```
{ inspector, appraiser, title_company, title_rep, closing_attorney,
  settlement_attorney, home_warranty, loan_officer }
```

For each row:

- Show `full_name`, `company` (if present), `email`, `phone` — same data the wizard already has.
- **Default-checked** if no existing `vendors` row matches `company_name` (case-insensitive, fuzzy).
- **Pre-linked** (not a new row) if an existing vendor matches — show the existing match's company name and let the user "Use existing" or "Save as new anyway." Default to "Use existing."

When the user clicks **Finish**:

1. For each ticked row with no match → `POST /api/v1/vendors/` (existing endpoint) and capture the new `vendor_id`.
2. For each ticked row (new or matched) → `POST /api/v1/transactions/{tx_id}/vendor-assignments` with `vendor_id`, `role` (mapped from `party_role`), and the contact's email/phone seeded into a new `contacts` row with `is_vendor=true` for use as the primary assignment contact.
3. The wizard finishes as it does today.

**Implementation effort:** small frontend addition; zero new backend endpoints (all routes already exist and have tests).

### 3.2 Retroactive promotion — "Save as vendor" inline button on existing parties

For transactions created before this feature ships (or for parties added manually after the fact), put a small **"Save as vendor"** button on each `transaction_party` row whose role is in the service-provider subset. One click:

1. Pre-fills `AddVendorModal` with the party's `company`, `email`, `phone`.
2. On save, creates the vendor + the assignment in the background.

This means no historical deal is permanently stuck without vendor data.

### 3.3 What NOT to do

- ❌ **Silent auto-create.** Always show the user what's being written to the tenant directory. The wizard already shows parties; we're just adding one extra checkbox per service-provider row.
- ❌ **Blind dedup.** Don't merge "Acme Inspection" and "Acme Home Inspections" automatically; ask the user with the suggested match shown.
- ❌ **Auto-create contacts as primary on existing assignments.** A vendor might have many contacts; the wizard knows only the one named on this contract. Default that contact as primary for *this transaction's* assignment, but never modify other deals' primary contacts.

---

## 4. Trade-off summary (for Jake)

| Approach | Pros | Cons |
|---|---|---|
| **Current (manual only)** | Zero risk of polluting the vendor directory; users know exactly when they're committing. | High friction — you described it ("had to add it manually… puzzling"). The system has the data and throws it away. |
| **Silent auto-create on wizard finish** | Lowest friction; everything just works. | Pollutes directory with duplicates, low-confidence extractions, one-off names. Hard to clean up. |
| **Recommended: explicit "Save as vendor" step in wizard + retroactive button on parties** | Captures intent + data quality. Users see what's about to happen. Existing transactions can be retroactively promoted. | A small extra step at wizard finish (~10 seconds). Frontend work. |

---

## 5. Concrete next steps (when you're ready to implement)

These are scoped so each is a single focused change. None require backend changes.

1. **Add a `useSaveAsVendorFromParty(partyId)` hook** that POSTs to `/api/v1/vendors/` and then `/api/v1/transactions/{id}/vendor-assignments`. Returns the new `assignment_id` for the caller.
2. **Add a footer step inside `NewTransactionWizard`** — render after the parties review step. Lists service-provider parties with one checkbox each, defaulted on for non-duplicates. On wizard finish, call the hook from step 1 in parallel for each checked row.
3. **Add a "Save as vendor" inline button** on the `transaction_parties` row UI (wherever those are rendered today — likely the transaction detail or Active Transactions drawer's contacts column). Opens `AddVendorModal` pre-filled.
4. **Optionally — fuzzy-match company names** before creating: use a simple `Levenshtein < 3` over lowercased company strings to suggest existing vendors. This is the cheapest first-pass dedup; can be replaced with a proper entity-resolution pass later.

Estimated frontend effort: **1–2 days total** (most of it is the UI for step 2). Backend: **zero changes** — every endpoint already exists and is tested.

---

## 6. What this unblocks

Once landed:

- The "Email vendor" CTA on a task card pre-selects the right vendor without the user picking from a dropdown. The picker only opens when no assignment exists.
- The `transaction_vendor_assignments` table starts to accumulate cross-deal data, which is what the M4.3 vendor-proposal task-matching logic ([VendorProposalService._match_task](../velvet-elves-backend/app/services/vendor_proposal_service.py)) uses to route inbound vendor replies back to the right task.
- The vendor directory at `/vendors` starts being meaningful instead of empty.
- The background-refresh feature (M4.3 deliverable §4) has real data to drift-check against.

---

## 7. Open questions for Jake

1. **Default-on or default-off for the wizard checkboxes?** I'd default-on for non-duplicates (most cases the user wants this). Open to flipping it.
2. **What roles count as "service provider"?** My recommendation above is `{ inspector, appraiser, title_company, title_rep, closing_attorney, settlement_attorney, home_warranty, loan_officer }`. Should we also include `co_agent` from the contacts side? I'd say no — co-agents are people, not companies, and don't fit the vendor model.
3. **Should the inline "Save as vendor" button on existing parties also create a `transaction_vendor_assignment` automatically?** I'd say yes — the user is on a specific transaction when they click, so the intent is clear.

None of these block the recommendation. They're refinements for when the work actually starts.

---

**End of proposal.**
