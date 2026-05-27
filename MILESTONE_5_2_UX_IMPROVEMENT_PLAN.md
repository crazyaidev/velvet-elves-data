# Milestone 5.2 — Payment Workflow UX Improvement Plan

| | |
|---|---|
| Document | **UX Improvement Plan — Milestone 5.2 Payment Features** |
| Version | 1.0 (2026-05-27) |
| Status | Draft — awaiting review |
| Prepared after | Hands-on review of live frontend source code + all M5.2 planning documents |
| Authoritative sources | `MILESTONE_5_2_IMPLEMENTATION_PLAN.md` · `MILESTONE_5_2_TESTING_GUIDE.md` · `FRONTEND_UI_WORKFLOW_LOGIC.md` · `STYLE_GUIDE.md` · `requirements.txt` §2.5, §7.7 |
| Scope | All M5.2 frontend UI components: New Invoice Modal, Payments List, Invoice Detail, Client Invoice, Commission Payouts form, Dashboard Payment Widget, Transaction card entry point |

---

## Executive Summary

The M5.2 Payment features are functionally built but suffer from a **mental-model mismatch** that makes them feel complex and error-prone. The core flaw: the UI is designed around database identifiers (`payer_contact_id`, `transaction_id`) rather than the agent's real workflow ("I have a deal — I want to bill someone on that deal").

The result is two independent free-text search fields in the "New Invoice" modal that routinely return nothing, because:

1. **The payer search** requires knowing a contact's exact name or email — but the contact only has meaning _within_ a transaction, which the user hasn't selected yet.
2. **The transaction search** is a separate, parallel operation — but the most natural entry point is _from_ a transaction card, which doesn't yet exist.

This document identifies **ten specific UX defects** and provides **concrete redesign recommendations** for each, grounded in the project's requirements, design system, and workflow logic. No source code changes are made here; this is a planning and specification document.

---

## Part 1 — Root Cause Analysis

### 1.1 The Core Mental-Model Problem

A real estate agent's mental model when creating an invoice is sequential and deal-anchored:

```
Step 1: "Which deal is this for?"         → Select a transaction
Step 2: "Who owes me money on this deal?" → Select a party from that transaction
Step 3: "What am I billing them for?"     → Add line items
Step 4: Send it
```

The current New Invoice modal reverses this order and breaks the dependency chain: **Payer** and **Transaction** are two independent free-text search fields presented side by side, with no indication that one narrows the other. The user is expected to know the payer's name or email (searched globally, not filtered by transaction) while simultaneously searching for the transaction by address.

This is equivalent to asking someone to fill in two unrelated fields that secretly belong together — a classic form design anti-pattern documented in `STYLE_GUIDE.md §13` ("Decisive defaults, fewer choices, clear hierarchy").

### 1.2 Missing Entry Point: The Transaction Card

`MILESTONE_5_2_IMPLEMENTATION_PLAN.md §6.C` specifies **three entry points** for invoice creation:

> 1. `/payments` "+ New Invoice" CTA  
> 2. Active Transactions expanded card → "Invoice this deal" footer action  
> 3. AI chatbot quick action "Invoice the Young deal $495 compliance fee" → opens the modal pre-filled

Only Entry Point 1 is implemented. Entry Point 2 — the most natural path for a user who is already working inside a transaction — is completely absent. This forces users to leave the transaction context, navigate to Payments, then re-find the same transaction and payer from scratch. This is the "complex operation" the user is describing.

### 1.3 Summary of Issues Found

| # | Area | Problem Type | Severity |
|---|---|---|---|
| 1 | New Invoice Modal — Payer field | Wrong UX ordering; search returns nothing | Critical |
| 2 | New Invoice Modal — Transaction field | Decoupled from payer; redundant when accessed from a transaction | Critical |
| 3 | New Invoice Modal — Task linking | Promised in the spec but not implemented | High |
| 4 | Active Transactions card | "Invoice this deal" CTA is missing | High |
| 5 | Invoice Detail Page | Raw UUIDs shown for payer and transaction | High |
| 6 | Payments List — search filter | Placeholder claims payer/transaction search; filter only checks invoice number | Medium |
| 7 | Commission Payouts form | Raw UUID text input for transaction ID; no autocomplete | Medium |
| 8 | PaymentsWidget — styling | Uses non-`ve-*` tokens; doesn't follow card vocabulary from Style Guide §16.2 | Medium |
| 9 | Invoice ↔ Transaction linking | No "View Transaction" link on invoice detail; no "Invoices" section in transaction drawer | Medium |
| 10 | Client Invoice Page — context | Client sees no deal/property context for why they are being billed | Low–Medium |

---

## Part 2 — Defect Details and Recommended Fixes

---

### Defect 1 — New Invoice Modal: Payer Search Returns Nothing

**File:** `src/components/payments/NewInvoiceModal.tsx` — `SearchField` component (lines 27–153), `"inv-payer"` field (lines 337–347)

#### What is happening

The "Bill to (payer)" field uses `useGlobalSearch` (hook at `src/hooks/useSearch.ts`) which calls `GET /api/v1/search?q=<query>` and filters for `type === 'contact'`. This search is:

- **Global** — it searches all contacts in the system, not contacts specific to any transaction.
- **Cold** — the user must type a name or email they remember, with no visual hints about who is billable.
- **Invisible on failure** — when a contact isn't indexed or the search term doesn't match exactly, the field silently shows "No results" with no guidance on what to try.

Additionally, the field is independent of the Transaction field. Selecting a transaction does not filter or narrow the payer options. A user working on the "Smith Purchase" deal must independently remember that the buyer's name is "John Smith" and that his email ends in `@gmail.com`. If they type "buyer" or "smith deal" or "123 Main St buyer," they get nothing.

#### Recommended Fix

**A: Make Transaction the first field (change field ordering)**

Reorder the two grid columns so "Transaction" appears first (left column) and "Bill to (payer)" appears second (right column). Add a visual dependency hint beneath the transaction field: `"Selecting a transaction will show you who to bill."` Per `STYLE_GUIDE.md §9.1`, help text uses `text-[11.5px] text-ve-charcoal-soft/75`.

**B: Cascade payer options from the selected transaction**

When a transaction is selected, replace the free-text contact search with a **dropdown of known parties on that transaction**, fetched from:

```
GET /api/v1/transactions/{id}/parties
```

The dropdown renders each party as:
```
[Name] · [Role] · [email/phone]  
e.g. "John Smith · Buyer · jsmith@gmail.com"
```

This means the user never needs to know the contact's email or search globally. They pick a deal, the system shows them who's on it. The global contact search is retained only as a fallback ("Bill someone not on this transaction" — a small ghost link below the dropdown), because standalone invoices to off-deal contacts are a valid but rarer use case.

**C: Update the SearchField's empty-state copy**

When no transaction is selected and the user types in the payer field with no results, the empty state should say:

> "No contacts found for '{query}'. Try selecting a transaction first — we'll show you everyone on that deal."

---

### Defect 2 — New Invoice Modal: Transaction Field is Redundant When Opened from a Transaction

**File:** `src/components/payments/NewInvoiceModal.tsx` lines 157–272; `src/pages/payments/PaymentsListPage.tsx` lines 34–45

#### What is happening

The `NewInvoiceModal` currently has no way to receive a pre-filled `transactionId` or `payerContactId` as props. It always opens blank. The implementation plan (§6.C) specifies that when opened via the "Invoice this deal" transaction card entry point, the transaction and payer should be pre-filled. Since that entry point is missing (Defect 4), the modal always starts cold.

Additionally, `NewInvoiceModalProps` only has `open: boolean` and `onClose: () => void` — no context props.

#### Recommended Fix

**A: Add context props to `NewInvoiceModal`**

Extend the `NewInvoiceModalProps` interface with optional pre-fill values:

```typescript
interface NewInvoiceModalProps {
  open: boolean
  onClose: () => void
  // Context passed when opened from a transaction or AI action
  prefilledTransactionId?: string
  prefilledTransactionLabel?: string
  prefilledPayerContactId?: string
  prefilledPayerLabel?: string
}
```

When these are provided:
- Skip directly to the payer + line items section.
- Render the transaction as a **read-only chip** (not an editable search field) with a small "Change" ghost link for users who want to switch. This mirrors the pattern used in `AddTaskModal` where the transaction context is shown as a non-editable badge.
- If `prefilledPayerContactId` is also provided (e.g., from an AI quick action), pre-select the payer too.

**B: Show a contextual header when pre-filled**

When a `prefilledTransactionId` is present, show a champagne-tinted header banner above the form body:

> `✦ Invoicing for: [address/label]`  
> `[Change transaction ×]`

This makes it immediately clear to the user what deal they're invoicing, reducing cognitive overhead.

---

### Defect 3 — New Invoice Modal: Task Linking is Missing

**File:** `src/components/payments/NewInvoiceModal.tsx`; `MILESTONE_5_2_IMPLEMENTATION_PLAN.md §6.C`; `MILESTONE_5_2_TESTING_GUIDE.md` Scenario 2, Step 4

#### What is happening

The implementation plan (§6.C) specifies:

> "optional checkbox 'Mark task X complete when this invoice is paid' (lists open tasks on the transaction)"

The testing guide (Scenario 2, Step 4) mentions:

> "If you see a checkbox or dropdown that says 'Mark task complete when paid,' check it and select the open task..."

The current modal has no such feature. The `InvoiceCreateRequest` type does not include `linked_task_ids`. Tester instructions say "if you see" — suggesting this is known to be missing. However, the backend already has the `invoice_task_links` join table (§5.J), so the database contract exists; only the UI is absent.

Without task linking, the key M5.2 deliverable — **"Payment-triggered task/status updates"** — cannot be invoked through the normal user workflow. The feature exists in the backend (webhook dispatcher completes linked tasks on `checkout.session.completed`) but users have no UI to set up the link.

#### Recommended Fix

When a transaction is selected in the modal, add a collapsible "Link to a task (optional)" section below the line items card. It renders a checkbox list of open tasks on the selected transaction, fetched from:

```
GET /api/v1/transactions/{id}/tasks?status=open
```

Each task shows:
- Task name
- Due date (if set)
- Assigned-to avatar (if assigned)

The user checks any task(s) they want auto-completed on payment. The selected task IDs are included in the `POST /api/v1/invoices` payload as `linked_task_ids: string[]`.

UI treatment per `STYLE_GUIDE.md §9`:
- Section header: `font-mono text-[9px] tracking-[1.8px] uppercase text-ve-text-muted`
- Each task row: checkbox + task name + due date, `text-[13px]`
- Empty state if no open tasks: `text-[12px] text-ve-text-ghost` — "No open tasks on this transaction."
- If no transaction is selected: section is hidden (task linking requires a transaction)
- Loading state: 2–3 skeleton rows

---

### Defect 4 — Active Transactions Card: "Invoice this deal" CTA is Missing

**File:** `src/pages/transactions/TransactionListPage.tsx` — card footer actions; `MILESTONE_5_2_IMPLEMENTATION_PLAN.md §6.C`

#### What is happening

The implementation plan (§6.C) explicitly lists the expanded transaction card as one of three invoice creation entry points:

> "(2) Active Transactions expanded card → 'Invoice this deal' footer action"

The `FRONTEND_UI_WORKFLOW_LOGIC.md §4.1` describes the card footer actions:

> "Footer actions bar: 'View/Add Documents' | 'Print Checklist' | 'Transaction History' | Price display"

There is no "Invoice" or payment-related footer action. The payment entry point from a transaction does not exist.

This is the **single most impactful missing piece** because:
- Real estate agents think in terms of deals, not payments.
- The most natural moment to invoice is when working inside a deal.
- Without this entry point, the user must leave the deal, go to Payments, search for the deal again, search for the payer separately — four extra steps with two failure-prone searches.

#### Recommended Fix

**A: Add "Invoice deal" to the transaction card footer**

Add a payment action to the expanded card footer bar, gated by `usePaymentCapabilities().canCreateInvoice`:

```
"View/Add Documents" | "Print Checklist" | "Transaction History" | [💳 Invoice deal] | Price display
```

The button uses the `variant="outline"` ghost button pattern, consistent with the other footer actions.

**B: Pre-fill the modal from transaction context**

When "Invoice deal" is clicked:
1. The `NewInvoiceModal` opens with `prefilledTransactionId` and `prefilledTransactionLabel` set from the transaction card data.
2. The Transaction field is rendered as a read-only chip (not a search field).
3. The Payer field immediately shows a dropdown of parties from that transaction (fetched from `GET /api/v1/transactions/{id}/parties`).
4. The user selects a payer, adds line items, and submits — **no search required**.

This reduces the invoice creation workflow from ~8 steps to ~4 steps for the most common case.

**C: Also link from the Transaction Overview widget on dashboards**

The Solo Agent and Team Leader dashboards show a "Transaction Overview" column with "Closing Soon," "In Inspection," etc. Add a secondary "Invoice" mini-action on these cards as well (icon-only, tooltip: "Invoice this deal"), gated by capability check.

---

### Defect 5 — Invoice Detail Page: Raw UUIDs for Payer and Transaction

**File:** `src/pages/payments/InvoiceDetailPage.tsx` lines 263–275

#### What is happening

The `InvoiceDetailPage` renders the payer as:

```jsx
<span className="font-mono text-[12px] text-ve-text-primary">
  {invoice.payer_contact_id}
</span>
```

This outputs a raw UUID such as `3f7a9c12-0b41-4f2e-a5d3-18e7ca229b1c`. The same raw UUID treatment applies to `transaction_id`. Neither field has a human-readable label, name, or address.

For a professional invoicing tool, this is equivalent to showing an accounting ID instead of a client name. The user cannot tell from the invoice detail page who the invoice is for or which deal it's linked to. Testers would correctly flag this as broken.

Additionally, `linked_task_ids` is rendered as a comma-joined string of UUIDs — equally unreadable.

#### Recommended Fix

**A: Extend the `Invoice` API response type**

The backend's `GET /api/v1/invoices/{id}` endpoint should include resolved human-readable fields alongside the IDs. In `src/types/payments.ts`, the `Invoice` type should add:

```typescript
payer_name: string | null        // e.g. "John Smith"
payer_email: string | null       // e.g. "jsmith@gmail.com"
transaction_address: string | null  // e.g. "123 Main St, Denver CO"
linked_task_names: string[]      // e.g. ["Collect compliance fee"]
```

These fields let the frontend display human-readable names without additional fetches.

**B: Update the Detail Sidebar rendering**

Replace the raw UUID spans with the resolved names:

```
Payer       John Smith (jsmith@gmail.com)
Transaction 123 Main St, Denver CO  [→ View transaction]
Linked tasks  ✓ Collect compliance fee
```

The "View transaction" link navigates to the Active Transactions page with `?highlight={transactionId}`, deep-linking to the transaction card for that deal.

**C: Fallback to truncated UUID only when name is null**

If the backend cannot resolve a name (e.g., archived contact), gracefully fall back to the first 8 characters of the UUID with a muted style — not the full 36-character UUID.

---

### Defect 6 — Payments List: Search Placeholder Mismatches Actual Filter

**File:** `src/pages/payments/PaymentsListPage.tsx` lines 139–149, 61–72

#### What is happening

The search input placeholder reads:

> `"Search by invoice number, payer, or transaction…"`

The `filteredInvoices` filter (lines 61–72) only checks:

```typescript
(inv.invoice_number ?? '').toLowerCase().includes(term) ||
(inv.terms_note ?? '').toLowerCase().includes(term) ||
inv.id.toLowerCase().includes(term)
```

It does **not** filter by payer name or transaction address. A user typing "John Smith" or "123 Main St" will see "No invoices" — which is false. This erodes trust ("does the system know about my invoice?").

**Secondary issue:** `invoice_number` is often `null` and falls back to `inv.id.slice(0, 8)` in the UI, but the filter searches the full 36-character UUID. A user who sees "3f7a9c12" in the table and types "3f7a9c12" would get a match, but the match is against the full UUID in the filter — so it actually works. But payer and transaction don't.

#### Recommended Fix

**A: Short-term — fix the placeholder copy**

Update the placeholder to accurately reflect what is actually searchable:

> `"Search by invoice # or reference…"`

This is a 2-character fix that removes the false promise immediately.

**B: Medium-term — add payer_name and transaction_address to invoice list items**

Extend the `InvoiceListResponse` items to include `payer_name` and `transaction_address` fields (mirrors Defect 5 fix). Update the `filteredInvoices` filter:

```typescript
(inv.invoice_number ?? '').toLowerCase().includes(term) ||
(inv.payer_name ?? '').toLowerCase().includes(term) ||
(inv.transaction_address ?? '').toLowerCase().includes(term) ||
inv.id.slice(0, 8).toLowerCase().includes(term)
```

Also add a `Payer` column and a `Transaction` column to the invoices table (between Status and Total), replacing the currently invisible data. This makes the list genuinely scannable — a user can find "John Smith's invoice for 123 Main St" at a glance.

---

### Defect 7 — Commission Payouts Form: Raw UUID Input for Transaction

**File:** `src/pages/payments/CommissionPayoutsPage.tsx` lines 245–257

#### What is happening

The "Trigger Payout" modal has a "Transaction (optional)" field that is a plain `<Input>` with placeholder `"transaction_…"` — expecting the user to type or paste a raw transaction UUID:

```jsx
<Input
  id="po-tx"
  value={transactionId}
  onChange={(e) => setTransactionId(e.target.value)}
  placeholder="transaction_…"
/>
```

This is a developer shortcut, not a user-facing design. No real estate agent, TC, or team lead knows their transaction UUID. This field will either be left empty (losing the audit trail linkage) or cause errors when users type a friendly label instead of an ID.

#### Recommended Fix

Replace the raw text input with a typeahead search field using the same `SearchField` component already in `NewInvoiceModal.tsx`, typed to `'transaction'`. The component already handles the `GET /api/v1/search?q=&type=transaction` pattern. The user types an address, selects from the dropdown, and the component stores the ID internally.

```
Transaction (optional)
[🔍 Search by address…        ▼]
```

Per `STYLE_GUIDE.md §9.3`, "Never use a native `<select>`" — the same principle extends to raw ID inputs for entity lookups.

---

### Defect 8 — PaymentsWidget: Styling Deviates from Design System

**File:** `src/components/payments/PaymentsWidget.tsx`

#### What is happening

The `PaymentsWidget` and `PaymentsHealthStrip` components use several non-`ve-*` class tokens that don't exist in the design system:

| Used in widget | Should be (per Style Guide) |
|---|---|
| `text-ve-text` | `text-ve-text-primary` (§2.2) |
| `bg-ve-surface-muted` | `bg-ve-surface-2` (§2.2) — `ve-surface-muted` is not in the token list |
| `text-ve-blue` | `text-ve-blue-text` (§2.3 — status triads use `-text` suffix) |
| `text-ve-red` | `text-ve-red-text` (§2.3) |
| Raw `rounded-lg border border-ve-border bg-white p-4` | Per §16.2, dashboard widgets should use the shared `SectionCard`/`RailCard` vocabulary, not ad-hoc card chrome |

Additionally, the widget is styled as a minimal card with `h3` "Payments" heading using `text-sm font-semibold` — which conflicts with §3.2 ("Section serif title: `font-serif text-[16px]–[18px] font-semibold`"). Dashboard section headers should be serif per the design system.

The "Outstanding invoices" list items use `className="... hover:bg-ve-surface-muted/40"` which references a non-existent token.

The overall aesthetic of the widget reads like a placeholder/prototype rather than a production component — it lacks the mono kicker pattern (`font-mono text-[9px] tracking-[1.8px] uppercase`) used by every other card section header in the codebase.

#### Recommended Fix

Rebuild `PaymentsWidget` to conform to the shared dashboard card vocabulary established by existing components:

```
┌─────────────────────────────────────────────────────┐
│ [9px MONO KICKER] PAYMENTS                          │
│                                                     │
│ ┌────────────────┐   ┌────────────────┐             │
│ │ Collected MTD  │   │ Payouts (TL)   │             │  ← 2-col grid, MoneyAmount
│ │ $2,450.00      │   │ $12,000.00     │             │    tabular-nums, large
│ │ actual, not    │   │ $3k scheduled  │             │
│ │ pipeline       │   │                │             │
│ └────────────────┘   └────────────────┘             │
│                                                     │
│ Outstanding Invoices                                │  ← sub-section kicker
│ ─────────────────────────────────────────────────   │
│ John Smith · 123 Main   $495  [open]  12d out       │  ← list rows
│ Sarah Jones · 456 Oak   $295  [open]  3d out        │
└─────────────────────────────────────────────────────┘
```

Use only `ve-*` tokens. Match the card chrome (`rounded-xl border border-ve-border bg-white shadow-[0_1px_4px_rgba(30,30,30,0.03)]`) used by adjacent dashboard cards, so the payments card looks like a member of the same family.

For the `PaymentsHealthStrip` on the Admin dashboard, align with `AdminKpiCard` or `AdminStat` patterns from `§16.4`, using the same `AdminCard compact` shell as other rail/stat cards, rather than a bespoke `rounded-lg` card.

---

### Defect 9 — Invoice ↔ Transaction: No Bidirectional Linking

**File:** `src/pages/payments/InvoiceDetailPage.tsx`; `src/pages/transactions/TransactionListPage.tsx`

#### What is happening

The invoice and transaction systems are **one-way** linked in the UI:
- The Invoice Detail page shows a transaction ID (as a UUID, per Defect 5) but no navigation link to the transaction.
- The Transaction expanded drawer has no "Invoices" section — a user working in a deal has no visibility into any invoices on that deal.

Per `MILESTONE_5_2_IMPLEMENTATION_PLAN.md §6.D`:

> "FSBO / Client workspace gains a read-only 'Payments' section listing their invoices"

This bidirectional linking is also implied for internal users: an agent on a deal should see all invoices linked to it. The testing guide (Scenario 5) asks the tester to "go to the transaction" and "open the Tasks section" — but doesn't say go to Payments first.

#### Recommended Fix

**A: Add "View Transaction" link on Invoice Detail**

In the Details sidebar of `InvoiceDetailPage.tsx`, replace the raw `transaction_id` UUID with a human-readable transaction label + a blue "View transaction →" link that navigates to `/transactions/active?highlight={transactionId}`.

**B: Add "Invoices" section in the Transaction expanded drawer**

In `TransactionListPage.tsx`, within the expanded card drawer (Column 2 — currently "Key Dates"), add a compact "Invoices" section below the key dates (or as a 4th expandable mini-section below the 3 columns):

```
Invoices for this deal
──────────────────────────────────
INV-0042  Draft   $495.00  due 06/15   [View]
INV-0038  Paid    $250.00  paid 05/01  [View]
──────────────────────────────────
[+ Invoice this deal]   (gated by canCreateInvoice)
```

This section is fetched from `GET /api/v1/invoices?transaction_id={id}` and renders only when `items.length > 0` OR the user has `canCreateInvoice` permission. The `[+ Invoice this deal]` CTA opens the `NewInvoiceModal` with `prefilledTransactionId` (fixing Defect 4 at the same time).

**C: Add "Invoices" to the AI Suggestions panel**

Per `FRONTEND_UI_WORKFLOW_LOGIC.md §4.1`, the AI Suggestions panel in the expanded drawer shows contextual suggestions. Add a suggestion rule: if the transaction has open tasks with `completion_method='payment'` AND no open invoice exists, suggest "Send an invoice to collect [task name] fee."

---

### Defect 10 — Client Invoice Page: Missing Deal Context

**File:** `src/pages/client/ClientInvoiceDetailPage.tsx`; `src/pages/client/ClientInvoicesPage.tsx`

#### What is happening

The `ClientInvoicesPage` shows a minimal table with columns: Invoice | Status | Amount | Due | [Pay now / View]. There is no indication of **which property** or **what the invoice is for**. A client who has multiple transactions (e.g., they have both a listing and a purchase) cannot tell which deal the invoice belongs to.

The `ClientInvoiceDetailPage` similarly shows line items and a total but no transaction context.

From the client's perspective, they receive an email with a "Pay $495" button, follow the link, pay, and then return to a page that says "$495.00 — Open" — with no property address or human-readable description of the deal.

This creates support burden: clients email agents asking "what is this charge for?"

#### Recommended Fix

**A: Add transaction context to `ClientInvoicesPage`**

Add a "Property" column to the client invoices table, showing `transaction_address` from the extended invoice API response (resolved per Defect 5):

```
Invoice   Status   Property              Amount   Due
──────────────────────────────────────────────────────
INV-0042  Open     123 Main St, Denver   $495     06/15   [Pay now]
INV-0038  Paid     456 Oak Ave, Denver   $250     —       [View]
```

**B: Add a property/deal banner on `ClientInvoiceDetailPage`**

At the top of the invoice detail, above the line items, show a context banner:

```
┌─────────────────────────────────────────────────────┐
│  This invoice is for your transaction at:           │
│  123 Main St, Denver CO 80202                       │
└─────────────────────────────────────────────────────┘
```

Styled as an informational `ve-blue-bg / ve-blue-border` card (per §2.3 status triads — "Informational" maps to blue).

**C: Copy on the terms note**

Instruct agents (via UI hint in the New Invoice modal's `terms_note` field) to include the property address in the terms note field when the payer is a client:

> Helper text: `"Tip: include the property address here so your client knows what this invoice is for."`

This is a guidance improvement that works even before the backend returns resolved `transaction_address`.

---

## Part 3 — UX Workflow Redesign: New Invoice Creation

The following describes the redesigned end-to-end flow for creating an invoice, incorporating all the fixes above.

### 3.1 Flow A: From a Transaction Card (Primary Path — Most Common)

**Entry:** Agent clicks "💳 Invoice deal" in the expanded transaction card footer  
**Pre-condition:** Agent has `canCreateInvoice` capability

```
Transaction Card (Expanded)
  └─ Footer: [View/Add Docs] [Print Checklist] [History] [💳 Invoice deal]
                                                                  │
                                          New Invoice Modal opens, pre-filled:
                                          ┌────────────────────────────────┐
                                          │ ✦ New Invoice                  │
                                          │ Create an invoice              │
                                          ├────────────────────────────────┤
                                          │ ✦ Invoicing for: 123 Main St   │
                                          │ [Change transaction ×]         │
                                          ├────────────────────────────────┤
                                          │ Bill to (payer) *              │
                                          │ [Buyer: John Smith        ▼]   │  ← Dropdown of deal parties
                                          │ [Seller: Sarah Jones         ] │
                                          │ [Listing Agent: Mike D.      ] │
                                          │ [or: Search for someone else…] │
                                          ├────────────────────────────────┤
                                          │ Line items                [+]  │
                                          │ TC Compliance Fee  1  $495.00  │
                                          ├────────────────────────────────┤
                                          │ Link to task (optional)        │
                                          │ ☐ Collect compliance fee  ...  │
                                          │ ☐ Process transaction docs ... │
                                          ├────────────────────────────────┤
                                          │ Due date      [06/15/2026]     │
                                          │ Tax           [$0.00]          │
                                          │ Terms note    [optional text]  │
                                          ├────────────────────────────────┤
                                          │  [Cancel]  [Save draft]  [Send]│
                                          └────────────────────────────────┘
```

**Steps:**
1. Transaction chip pre-filled, read-only.
2. Payer dropdown loads parties from `GET /api/v1/transactions/{id}/parties`. Agent selects "Buyer: John Smith."
3. Agent adds line items.
4. (Optional) Agent checks a task to auto-complete on payment.
5. Agent clicks "Save draft" or "Send now."
6. On success: navigate to invoice detail page. Toast: "Draft saved" or "Invoice sent."

**Result:** Zero searches required. Zero chance of "No results found." The cognitive load drops from 8+ steps to 4 steps.

---

### 3.2 Flow B: From the Payments List (Secondary Path — Less Common)

**Entry:** Agent clicks "+ New Invoice" on the Payments List page  
**Pre-condition:** No transaction context; may be invoicing for an off-deal fee

```
Payments List → "+ New Invoice"
  │
  New Invoice Modal opens (blank):
  ┌────────────────────────────────┐
  │ ✦ New Invoice                  │
  │ Create an invoice              │
  ├────────────────────────────────┤
  │ Transaction (optional)         │
  │ [🔍 Search by address…]        │  ← Global transaction search
  │  ↓ After selection:            │
  │  ✦ Invoicing for: 456 Oak Ave  │  ← Chip replaces search field
  │  [Change transaction ×]        │
  │                                │
  │ Bill to (payer) *              │
  │ [Buyer: Sarah Jones       ▼]   │  ← Populated AFTER transaction selected
  │ (or [🔍 Search by name/email…] │     if no transaction selected)
  ├────────────────────────────────┤
  │ … rest of form same as Flow A  │
  └────────────────────────────────┘
```

**Key difference from current:** Selecting a transaction changes the Payer field from a free-text global search into a party dropdown for that deal. If no transaction is selected, the global contact search is available as a fallback for truly standalone invoices.

**Instructional text when no transaction is selected:**
> "Select a transaction to see who to bill, or search for any contact to invoice someone outside a deal."

---

### 3.3 Flow C: From AI Quick Action (Future/Phase 3)

Per §6.C, the AI chatbot quick action ("Invoice the Young deal for $495 compliance fee") opens the modal pre-filled with `prefilledTransactionId`, `prefilledPayerContactId` (resolved by the AI from the deal's buyer), and a line item pre-populated. This flow works automatically once Defect 2 (context props) is fixed.

---

## Part 4 — Payments List Page: Recommended Column Additions

The current `InvoicesTable` in `PaymentsListPage.tsx` shows: Invoice | Status | Total | Paid | Due | Created | Actions.

**Add:** Payer (name) | Transaction (address truncated to 20 chars).

**Remove or collapse:** "Created" can move to the detail page; the list is crowded. Priority visible columns on a responsive table:

| Priority | Column | Desktop | Tablet | Mobile |
|---|---|---|---|---|
| 1 | Invoice # | ✓ | ✓ | ✓ |
| 2 | Payer | ✓ | ✓ | — |
| 3 | Status | ✓ | ✓ | ✓ |
| 4 | Total | ✓ | ✓ | ✓ |
| 5 | Transaction | ✓ | — | — |
| 6 | Due | ✓ | ✓ | — |
| 7 | Actions | ✓ | ✓ | ✓ |

The "Paid" column (currently always shows `$0.00` placeholder via `variant="muted"`) should be replaced by the Payer column; the paid amount is visible on the detail page.

---

## Part 5 — Prioritized Implementation Backlog

The fixes are ordered by user-facing impact, with the most critical workflow blockers first.

| Priority | Fix | Defect # | Effort Estimate |
|---|---|---|---|
| P0 | Add "Invoice deal" CTA to transaction card footer | 4 | S (2–4h) |
| P0 | Pre-fill NewInvoiceModal from transaction context (add props) | 2 | S (2–4h) |
| P0 | Cascade payer dropdown from selected transaction | 1 | M (4–8h) |
| P1 | Add task-linking section to New Invoice modal | 3 | M (4–8h) |
| P1 | Extend Invoice API to return `payer_name`, `transaction_address`, `linked_task_names` | 5 | M (4–8h backend + 2h frontend) |
| P1 | Fix Invoice Detail page to display resolved names instead of UUIDs | 5 | S (2–4h, depends on API fix) |
| P2 | Add "Invoices" section to expanded transaction drawer | 9B | M (4–8h) |
| P2 | Add "View Transaction" link on Invoice Detail | 9A | S (1–2h, depends on API fix) |
| P2 | Fix Payments List search placeholder (short-term fix) | 6A | XS (30min) |
| P2 | Add payer + transaction columns to Invoices table | 6B, 5 | M (4–8h) |
| P2 | Replace raw UUID Transaction input on Commission Payouts form | 7 | S (2–4h) |
| P3 | Rebuild PaymentsWidget to use `ve-*` design tokens | 8 | M (4–8h) |
| P3 | Add transaction context to Client Invoice pages | 10 | S (2–4h, depends on API fix) |
| P3 | Update Invoice search filter to include payer_name / transaction_address | 6B | S (1–2h) |

**Total estimated frontend effort:** 5–8 developer-days  
**Total estimated backend effort:** 1–2 developer-days (resolving joined fields in API responses)

---

## Part 6 — Design System Consistency Checklist

All redesigned components must pass these checks before code review:

- [ ] All color tokens use `ve-*` namespace (no `text-ve-text`, no `bg-ve-surface-muted`)
- [ ] Card chrome matches: `rounded-xl border border-ve-border bg-white shadow-[0_1px_4px_rgba(30,30,30,0.03)]`
- [ ] Section kickers use: `font-mono text-[9px] tracking-[1.8px] uppercase text-ve-text-muted`
- [ ] Section titles use: `font-serif text-[16px]–[18px] font-semibold`
- [ ] Body text uses: `text-[13px] leading-[1.55]`
- [ ] Help text uses: `text-[11.5px] text-ve-charcoal-soft/75`
- [ ] No `window.confirm()` or `window.alert()` — use `<AlertDialog>`
- [ ] No native `<select>` — use Radix `<Select>` (§9.3)
- [ ] Required field indicators use: `<span className="ml-0.5 text-ve-orange">*</span>`
- [ ] Money amounts use: `tabular-nums lining-nums`, right-aligned in tables
- [ ] Status pills use paired bg + border + text tokens (§2.3)
- [ ] Empty states use: `rounded-xl border-[1.5px] border-dashed border-ve-orange-border bg-ve-orange-soft/15`
- [ ] No full-row clickable cards (every row must have explicit action buttons per §16.5)
- [ ] `canCreateInvoice`, `canRefund`, `canTriggerPayout` gates all payment actions

---

## Part 7 — Summary: Why These Changes Matter

The M5.2 payment features represent a significant value add for agents and TCs — automated task completion, digital invoicing, payment tracking — but only if users can actually reach them without friction. The current UX creates confusion at the very first interaction (creating an invoice) by requiring knowledge of two independent pieces of information (contact email + transaction address) rather than guiding the user down the natural deal-anchored path.

The changes in this plan are conservative: they add missing entry points, cascade context that the system already has (transaction parties), resolve display IDs that the system already stores (contact names), and align visual components with the established design vocabulary. No new backend data model changes are required beyond extending existing API responses to include resolved display names.

The net result:

| Before | After |
|---|---|
| 8+ steps to create an invoice from a transaction | 4 steps |
| 2 independent searches that often fail | 0 searches (pre-filled from deal context) |
| Raw UUIDs in invoice detail | Human names and clickable links |
| No visibility into deal invoices from transaction view | Invoices section in expanded drawer |
| No task-linking UI despite backend support | Task checkbox list in modal |
| Raw UUID field for payouts | Autocomplete transaction search |
| Widget uses non-system tokens | Fully conformant to design system |

---

_End of plan._
