# Where does "Vendor" sit in a Velvet Elves transaction?

**Audited:** 2026-05-18
**Question:** Buyer / Seller / Buyer's Agent / Seller's Agent map cleanly to a real-estate transaction. **Where is the Vendor?**
**Short answer:** Today the codebase carries **two parallel representations** of a vendor — one inherited from earlier milestones (`transaction_parties`) and one introduced by M4.3 (`vendors` + `transaction_vendor_assignments`). They are not yet bridged. This doc explains both, names the bridge that is missing, and locates a real UI gap: the "Email vendor" CTA from the testing guide is **not actually wired into the UI today**.

---

## 1. The conceptual position of a Vendor in a real-estate transaction

A vendor is **not a party to the contract.** Buyer, Seller, Buyer's Agent, Seller's Agent (and, depending on state, the closing attorney) are *parties* — they sign, they have legal standing, they are named in the purchase agreement. A vendor is a **third-party service provider** engaged to deliver a service that gates a contract milestone.

| Group | Role in the deal | Signs the contract? | Owns a deadline? | Persistent across deals? |
|---|---|---|---|---|
| Buyer | Principal party | ✅ | n/a | No — one-shot relationship |
| Seller | Principal party | ✅ | n/a | No — one-shot relationship |
| Buyer's Agent | Fiduciary representative of buyer | ✅ (agency disclosure) | n/a (manages the others) | Sometimes (repeat clients) |
| Seller's Agent (Listing Agent) | Fiduciary representative of seller | ✅ | n/a (manages the others) | Sometimes |
| **Vendor** (Inspector, Appraiser, Title Co., Closing Attorney, Home-Warranty, Pest Inspector, Surveyor, etc.) | **Service provider** | ❌ | ✅ (their deadline is the contract contingency they gate) | ✅ **Yes — same vendor used across many deals** |

The "vendor" is the only category with all three properties:

1. **Not a party** — no legal standing on this specific contract.
2. **Gates a deadline** — the inspector's visit is the inspection contingency; the appraiser's report is the appraisal contingency; the title company's commitment unlocks closing.
3. **Persists across transactions** — the agent works with the same inspector for years; the title company handles every deal in a county.

That third property is the entire reason M4.3 added a vendor-company model in the first place. Parties are *one-shot rows attached to one deal*; vendors are *durable directory entries reused on many deals*.

---

## 2. How vendors are represented in the data model — today there are two ways

### 2.1 Representation A: as a `transaction_party` (older, since earlier milestones)

A row in `transaction_parties`, with `party_role` drawn from a controlled vocabulary in [app/utils/party_roles.py](../velvet-elves-backend/app/utils/party_roles.py):

```
Contract parties:        buyer, seller, listing_agent, buyers_agent
Service providers:       inspector, appraiser, loan_officer, title_rep,
                         title_company, closing_attorney,
                         settlement_attorney, home_warranty
Catch-all:               other
```

So **both contract parties and vendors live in the same table**, distinguished only by `party_role`. The wizard, contract parsing (Milestone 2.x), AI suggestions, and manual UI entry all write here. Email/phone are stored denormalized on the row (optionally also linked to a `contact_id`).

This is what populates the parties column you see on a transaction detail page.

### 2.2 Representation B: as a `vendors` + `transaction_vendor_assignments` pair (newer, M4.3)

Three tables working together:

```
   vendors                    contacts (is_vendor=true)
   ───────────────            ──────────────────────────
   id                         id
   tenant_id                  vendor_id  ── FK ──┐
   company_name               full_name          │
   email                      email              │
   phone                      phone              │
   address                    title              │
   category                                      │
   is_preferred                                  │
                                                 │
   transaction_vendor_assignments                │
   ─────────────────────────────────             │
   id                                            │
   transaction_id ── FK to transactions          │
   vendor_id      ── FK to vendors  ─────────────┘
   role            (inspector|appraiser|title_co|attorney|...)
   notes
   is_active

   transaction_vendor_assignment_contacts
   ──────────────────────────────────────
   id
   assignment_id  ── FK to transaction_vendor_assignments
   contact_id     ── FK to contacts (where is_vendor=true)
   is_primary
```

This says: *"For THIS transaction, the role of Inspector is being played by Acme Home Inspection (vendor row), and the person at Acme to email is Joe Smith (contact row), and Joe is the primary contact for this deal."*

Same Acme on the next deal? Reuse the vendor row, create a new assignment.

### 2.3 The two representations are not yet bridged

This is the load-bearing finding of this doc.

| Concern | Representation A (`transaction_parties`) | Representation B (`vendors` + assignments) |
|---|---|---|
| Created by wizard | ✅ | ❌ (not yet) |
| Created by contract parser | ✅ | ❌ |
| Created by manual UI entry on the transaction card | ✅ | ❌ (no UI surface today — see §3) |
| Required for "Email vendor" template flow | ❌ | ✅ |
| Required for vendor-proposal task-date update | ❌ | ✅ (proposals match by vendor email → `vendor_id`, not by party row) |
| Persists across transactions | ❌ (one row per deal) | ✅ |
| Background refresh suggestions | ❌ | ✅ |
| Colleague invite | ❌ | ✅ |

**Concrete consequence:** If an agent adds "Acme Home Inspection / Joe Smith / joe@acme.com" through the wizard, that information lives in `transaction_parties` only. When Joe later replies with `Scheduled: 2026-07-12`, the AI engine tries to match the sender email against `vendors.email` and `contacts.email (is_vendor=true)`. **It does not look at `transaction_parties.email`.** If no vendor row exists for Acme, the proposal is created with `vendor_id=NULL` and the "saved across deals" benefits don't apply.

The bridge that doesn't exist yet: a flow that says "this party is also a saved vendor → create the vendor row, create the assignment, link the contact." That gap is what makes "Vendor" feel ambiguous in the product right now — the system has two definitions and the user can be in either world depending on which entry point they used.

---

## 3. Where the vendor actually surfaces in the UI today — and where the gap is

I went route-by-route in the frontend.

| Surface | What you see | Verdict |
|---|---|---|
| `/vendors` ([VendorListPage](../velvet-elves-frontend/src/pages/vendors/VendorListPage.tsx)) | Tenant-wide vendor company directory. | Wired |
| `/vendors/:vendorId` ([VendorDetailPage](../velvet-elves-frontend/src/pages/vendors/VendorDetailPage.tsx)) | Vendor company card, contacts, transactions where used, "Refresh info" CTA, "Add colleague" link. | Wired |
| `/vendor-proposals` ([VendorProposalsPage](../velvet-elves-frontend/src/pages/VendorProposalsPage.tsx)) | Queue of task-date proposals from vendor replies. | Wired |
| `/admin/vendor-templates` ([VendorTemplatesPage](../velvet-elves-frontend/src/pages/admin/VendorTemplatesPage.tsx)) | Template CRUD. | Wired |
| `/v/:token` ([AddColleaguePage](../velvet-elves-frontend/src/pages/public/AddColleaguePage.tsx)) | Public colleague self-attach. | Wired |
| Inline panel on `/ai-emails` ([LinkedVendorProposalPanel](../velvet-elves-frontend/src/pages/AiEmailReviewPage.tsx#L284)) | Linked task proposal beside a vendor-reply draft. | Wired |
| Transaction detail / Active Transactions drawer — "Email vendor" CTA on a task | Per testing guide §2 and implementation plan §6.4: should open `VendorRequestModal` pre-bound to the task. | **NOT WIRED — see below** |
| Transaction detail — "Vendor assignments" management panel | Per implementation plan §6.4: agent assigns a vendor company + role + contacts to a transaction. | **NOT WIRED — see below** |

### 3.1 The missing UI wires

Grepping the entire frontend tree:

```
$ grep -rln "VendorRequestModal" src/
src/components/vendors/VendorRequestModal.tsx     ← only the definition
$ grep -rln "useVendorAssignments" src/
src/hooks/useVendorAssignments.ts                  ← only the definition
```

Both `VendorRequestModal` and the assignment-management hooks (`useVendorAssignments`, `useCreateVendorAssignment`, `useUpdateVendorAssignmentContacts`, `useDeleteVendorAssignment`) are **defined but never imported by any page.** [`VendorContactCard`](../velvet-elves-frontend/src/components/vendors/VendorContactCard.tsx) exposes an `onEmailPrimary` callback prop that [`VendorDetailPage`](../velvet-elves-frontend/src/pages/vendors/VendorDetailPage.tsx) never passes.

**The practical effect:** an internal user cannot today reach the "Email vendor" template flow through normal navigation. The backend endpoint `POST /api/v1/vendor-communications/send` works, the modal is built, and the backend tests pass — but to actually invoke the workflow as a user, you need to call the API directly.

This is consistent with the prior audit finding that the system *backend is sound*. The gap is purely in **how the user reaches the vendor-comms flow from a transaction**.

### 3.2 What this means for "where is the vendor in the workflow"

Today, in the live UI:

- **Vendors-as-companies** (Representation B) are reachable through `/vendors` and `/vendors/:id`. Treat them as a separate "address book" surface, mostly disconnected from any specific deal.
- **Vendors-as-parties** (Representation A) appear in the transaction's parties list and contact directory, alongside buyer/seller/agents, distinguished only by `party_role`.
- **The bridge** — assigning a vendor company to a specific transaction in a specific role, and emailing them with a template tied to a task — is the part of M4.3 that needs the UI surface to land. The hooks and components exist; the page-level wiring does not.

---

## 4. Recommended mental model (and how I'd explain it to Jake)

Think of every person who touches a deal as belonging to one of three buckets:

```
┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
│   CONTRACT PARTIES      │    │   SERVICE PROVIDERS     │    │   INTERNAL TEAM         │
│   (one-shot per deal)   │    │   (vendors — durable)   │    │   (your firm)           │
├─────────────────────────┤    ├─────────────────────────┤    ├─────────────────────────┤
│  Buyer                  │    │  Inspector              │    │  Agent (file owner)     │
│  Seller                 │    │  Appraiser              │    │  Transaction            │
│  Buyer's Agent          │    │  Title Company / Rep    │    │  Coordinator (Elf)      │
│  Listing Agent          │    │  Closing Attorney       │    │  Team Lead              │
│                         │    │  Home Warranty          │    │  Admin                  │
│                         │    │  Loan Officer*          │    │  Attorney (staff)       │
│  ──────────────────     │    │  Surveyor / Pest /      │    │                         │
│  Signs the contract     │    │  Photographer / etc.    │    │                         │
│  Stored in              │    │  ──────────────────     │    │  Stored as users + RBAC │
│  transaction_parties    │    │  Gates a deadline       │    │                         │
│  with party_role of     │    │  Reused across deals    │    │                         │
│  buyer/seller/agent     │    │  Stored in vendors +    │    │                         │
│                         │    │  transaction_vendor_    │    │                         │
│                         │    │  assignments            │    │                         │
└─────────────────────────┘    └─────────────────────────┘    └─────────────────────────┘
       Party                          Vendor                         User
```

(*Loan Officer can go either way — they're often modeled as a party in this codebase because they sometimes co-sign and are typically deal-specific.)

So the answer to the user's question — *what is the position of a vendor?* — is:

> A vendor is a **durable third-party service provider** that this firm reuses across many transactions. On any one transaction, the vendor sits *outside* the contract-party group (Buyer/Seller/Agents) but *gates a deadline* on that transaction's task list (inspection, appraisal, title, closing). In the data model, vendors are represented as a **company row** (persisted across deals) plus a **per-deal assignment row** that names the role they're playing and which contact at that company is primary for this transaction.

---

## 5. What I'd do next (no code changes here — research only)

Three follow-ups would close the conceptual ambiguity. Listed in order of value-to-effort.

1. **Wire the missing UI surfaces** — import `VendorRequestModal` into the Active Transactions drawer (Tasks column) and add an "Email vendor" button. Import `useVendorAssignments` and add an assignment-management panel on the transaction detail/drawer. Backend is already complete; this is purely frontend plumbing. **This is the single biggest unlock** — without it, the M4.3 workflow can't be reached from where users actually live (the deal page).

2. **Promote-to-vendor flow from a party** — small UI affordance on a `transaction_party` row with `party_role IN (inspector, appraiser, title_company, closing_attorney, home_warranty)`: "Save as vendor." Creates a `vendors` row and a `transaction_vendor_assignments` row in one click, optionally creates a `contacts` row from the party's email/phone, and links them. Bridges Representation A → Representation B and stops the ambiguity at the source.

3. **One-pager in the product docs** — the table in §4 above, placed in `FRONTEND_UI_WORKFLOW_LOGIC.md`. Eliminates the "what's a vendor again?" question for new TCs and clients.

None of these require milestone reopens; (1) and (2) are frontend tasks that fit cleanly in Phase 5's UI polish window.

---

**End of analysis.**
