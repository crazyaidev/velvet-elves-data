# Should "Vendor Proposals" sit in the "Vendors" sidebar group?

**Written:** 2026-06-24
**Question (from Jan):** Today the "Vendors" sidebar group contains only "Vendor
Directory." Shouldn't "Vendor Proposals" also live there instead of under
"Intelligence"? And the relationship between *Vendor Directory*, *Vendor
Proposals*, and *AI Email Review* feels unclear / not yet finalized.
**Mode:** Research only. No source code changed. This file is the answer.
**Codebases reviewed:** [velvet-elves-frontend/](../velvet-elves-frontend/), [velvet-elves-backend/](../velvet-elves-backend/)
**Companion docs:** [FRONTEND_UI_WORKFLOW_LOGIC.md](FRONTEND_UI_WORKFLOW_LOGIC.md), [MILESTONE_4_3_IMPLEMENTATION_PLAN.md](MILESTONE_4_3_IMPLEMENTATION_PLAN.md), [VENDOR_COMMUNICATION_SYSTEM_AUDIT.md](VENDOR_COMMUNICATION_SYSTEM_AUDIT.md), [VENDOR_POSITION_IN_TRANSACTION.md](VENDOR_POSITION_IN_TRANSACTION.md)

---

## TL;DR

| Question | Answer |
|---|---|
| Is "Vendor Proposals" really outside the "Vendors" group today? | **Yes.** It sits in **Intelligence**, next to "AI Email Review." "Vendors" holds only "Vendor Directory." |
| Is that a bug / oversight? | **No.** It is the **documented, intended** placement (spec + milestone plan both put it under Intelligence). |
| Is your instinct to group it with "Vendor Directory" wrong, then? | **Not wrong, just a different grouping axis.** You are grouping by *noun* ("vendor"); the current design groups by *function* ("an AI-produced queue a human must approve"). Both are defensible. |
| Is the relationship between the three pages genuinely unclear / unfinished? | **Yes, your impression is correct and is already documented.** There is real overlap between *Vendor Proposals* and *AI Email Review*, and *Vendor Directory* is a separate "address book" that is largely disconnected from the deal flow. See §4. |
| My recommendation | Keep Vendor Proposals under Intelligence (function-based), but resolve the *Vendor Directory vs. Vendor Proposals vs. AI Email Review* ambiguity first. The grouping question is downstream of that. See §5. |

---

## 1. What the three surfaces actually are

| Surface | Route | What it is | AI involved? | Interaction style |
|---|---|---|---|---|
| **Vendor Directory** | `/vendors` ([VendorListPage.tsx](../velvet-elves-frontend/src/pages/vendors/VendorListPage.tsx)) | A tenant-wide **address book** of vendor companies (inspectors, appraisers, title cos.). CRUD: add / edit / mark preferred / delete / invite a colleague. | No | Manage durable records |
| **AI Email Review** | `/ai-emails` ([AiEmailReviewPage.tsx](../velvet-elves-frontend/src/pages/AiEmailReviewPage.tsx)) | The **master queue of every AI-drafted email reply** (kinds: factual, document_request, **vendor_reply**, uncertain). Human approves / edits / sends / discards. | Yes | Triage a live queue |
| **Vendor Proposals** | `/vendor-proposals` ([VendorProposalsPage.tsx](../velvet-elves-frontend/src/pages/VendorProposalsPage.tsx)) | A **narrow sub-queue**: the task-date change proposals (`Scheduled: YYYY-MM-DD`) the engine extracts **from `vendor_reply` drafts**. Human accepts / rejects / asks for clarification. | Yes | Triage a live queue |

The key structural fact: **a Vendor Proposal is born from an AI Email draft.** The
engine classifies an inbound vendor reply, drafts a `vendor_reply` email, and
*from that same draft* spawns a proposal. The proposal row carries the
`draft_log_id` of the email draft it came from. That is why the AI Email Review
page can render the very same proposal inline (the `LinkedVendorProposalPanel`,
[AiEmailReviewPage.tsx:326-427](../velvet-elves-frontend/src/pages/AiEmailReviewPage.tsx#L326)),
finding it by `proposal.draft_log_id === draft.id`.

So the lineage is:

```
Vendor's email reply
   └─ AI engine → vendor_reply DRAFT ............... shows in  AI Email Review
                     └─ task-date PROPOSAL ......... shows in  Vendor Proposals
                                                     (and inline inside AI Email Review)
```

Vendor Directory is **not** in this chain at all. It is the static company
roster. It has no queue, no AI, no per-deal state.

---

## 2. Current state in code (verified)

Sidebar groups are built in [AppLayout.tsx](../velvet-elves-frontend/src/layouts/AppLayout.tsx):

- **Vendors** group ([AppLayout.tsx:342-346](../velvet-elves-frontend/src/layouts/AppLayout.tsx#L342)):
  - Vendor Directory
- **Intelligence** group ([AppLayout.tsx:347-368](../velvet-elves-frontend/src/layouts/AppLayout.tsx#L347)):
  - AI Suggestions
  - **AI Email Review** (badge = pending AI drafts)
  - **Vendor Proposals** (badge = pending proposals)
  - Analytics
  - AI Coach (locked teaser, Team-Lead context only)

The two badges are even fed the same way and at the same cadence: the layout
polls `useVendorProposals(...)` and `usePendingNotifications(...)` together and
passes `aiDraftsPending` and `vendorProposalsPending` side by side into the same
Intelligence section ([AppLayout.tsx:608-645](../velvet-elves-frontend/src/layouts/AppLayout.tsx#L608)).

So in the running app, "AI Email Review" and "Vendor Proposals" are deliberately
presented as twin queues.

---

## 3. Is this intentional? Yes — and it is documented in two places

This is not an accident of implementation. Two governing docs explicitly place
Vendor Proposals under Intelligence:

1. **The UI spec** — [FRONTEND_UI_WORKFLOW_LOGIC.md](FRONTEND_UI_WORKFLOW_LOGIC.md),
   "Shared Shell Reference," lists the navigation groups verbatim:
   > - **Vendors** — Vendor Directory
   > - **Intelligence** — AI Suggestions (badge), AI Email Review (badge), **Vendor Proposals (badge)**, Analytics

   The code matches this spec exactly.

2. **The milestone plan** — [MILESTONE_4_3_IMPLEMENTATION_PLAN.md](MILESTONE_4_3_IMPLEMENTATION_PLAN.md):
   - §6.1 describes `/vendor-proposals` as a *"sibling to `/ai-emails`."*
   - §6.4 ("UX touchpoints") says: *"**Sidebar Intelligence section.** New chip
     'Vendor Proposals (N)' next to the existing 'AI Email Review' chip; same
     polling cadence (60 s)."*

And the system audit reinforces the functional pairing.
[VENDOR_COMMUNICATION_SYSTEM_AUDIT.md](VENDOR_COMMUNICATION_SYSTEM_AUDIT.md) §2.1
describes the approval step (Phase 3) as:
> "Agent opens **/vendor-proposals OR /ai-emails** (LinkedVendorProposalPanel) → click Accept / Reject / Clarify"

i.e. the two pages are two doors into the *same* human-approval action.

**Conclusion for the placement question:** the design groups by **what the user
is doing** (reviewing AI output before it changes data or gets sent), not by the
noun in the label. Vendor Proposals lives with AI Email Review because it *is* a
slice of AI Email Review, surfaced separately for convenience.

---

## 4. Your instinct is reasonable — here is the case for each side

You asked me to verify, not just defend the status quo. Both groupings are
legitimate; they optimize for different things.

### 4.1 The case FOR moving it to "Vendors" (your view)

- **Label affinity.** "Vendor Proposals" and "Vendor Directory" share the word
  "Vendor." A user hunting for anything vendor-related will scan the Vendors
  group first.
- **The Vendors group is thin.** It holds a single item today, which looks
  unfinished. A second entry balances it.
- **Same milestone / same backend domain.** Both came from Milestone 4.3 and
  both are served by the vendor-communications domain
  (`/api/v1/vendor-communications/...`, see [useVendorComms.ts](../velvet-elves-frontend/src/hooks/useVendorComms.ts)).
- **"Intelligence" is arguably mis-scoped.** AI Suggestions and Analytics are
  read-and-explore surfaces; AI Email Review and Vendor Proposals are
  approve-and-act queues. One could argue the Intelligence group is already
  doing two jobs.

### 4.2 The case AGAINST (why it is where it is)

- **Provenance.** A proposal is generated by the AI engine from an AI email
  draft. It is an *AI output awaiting human sign-off*, exactly like every other
  row in AI Email Review. Vendor Directory has no AI and no queue.
- **Shared machinery.** The two queues share the `VendorProposalCard` component,
  the 60-second polling, the orange "pending" badge, and the same accept / reject
  backend calls. Vendor Directory shares none of this.
- **They are literally the same data in two views.** A `vendor_reply` draft shows
  in AI Email Review *with its proposal embedded*; the proposal also stands alone
  in Vendor Proposals. Splitting one of those views into a different,
  non-adjacent group would hide that they are the same workflow.
- **Interaction mode.** Vendor Directory is "manage records I keep forever."
  Vendor Proposals is "clear a time-sensitive queue today." Putting a triage
  queue next to an address book mixes two mental modes under one heading.

On balance the function-based placement is the stronger one *as long as the
Intelligence group stays "AI work that needs my approval."* But that is exactly
where the deeper problem you sensed comes in.

---

## 5. The real issue you put your finger on: the three pages aren't cleanly separated

Your second observation — that the *relationship* between Vendor Directory,
Vendor Proposals, and AI Email Review is unclear and "not fully finalized" — is
**correct, and it is already on record.** The grouping debate is a symptom of it.
The underlying ambiguities:

### 5.1 Vendor Proposals overlaps AI Email Review

A vendor reply that proposes a date appears in **both** queues:
- in **AI Email Review** as a `vendor_reply` draft, with the proposal panel
  inline (you can Accept the date *without leaving the page*), and
- in **Vendor Proposals** as a standalone card.

So a diligent user can process the same item from two places. That redundancy is
intentional convenience today, but it is also exactly what makes the IA feel
unsettled: is Vendor Proposals a *destination* or just a *saved filter* of AI
Email Review? Right now it is closer to the latter dressed as the former.

### 5.2 Vendor Directory is disconnected from the deal flow

[VENDOR_POSITION_IN_TRANSACTION.md](VENDOR_POSITION_IN_TRANSACTION.md) documents
that the Directory is "a separate 'address book' surface, mostly disconnected
from any specific deal," and that the two pieces meant to connect it to live work
are **defined but not wired into any page**:
- `VendorRequestModal` (the "Email vendor" template flow) is never imported.
- `useVendorAssignments` (assign a vendor to a transaction in a role) is never
  imported.

So today: the Directory holds companies, the AI engine matches *inbound* vendor
replies by email and spawns proposals — but the *outbound* "email this vendor
about this task" path that ties the Directory to the queue is not reachable from
the UI yet. The chain has a missing middle link. That is the strongest evidence
that the vendor workflow is genuinely mid-build, not just mis-labeled.

### 5.3 There are also two unbridged definitions of "vendor"

Same doc: vendors exist both as `transaction_parties` rows (older) and as
`vendors` + `transaction_vendor_assignments` (M4.3). They are not bridged, so a
vendor added via the wizard may not be the vendor the proposal engine matches.
This doesn't affect the sidebar grouping, but it is part of why "vendor" feels
slippery across the product.

---

## 6. Recommendation

**1. Don't reshuffle the sidebar in isolation.** Moving "Vendor Proposals" into
"Vendors" purely for label affinity would split it from AI Email Review, which is
its actual twin, and would put a live triage queue next to a static address book.
That trades one kind of confusion for another. The current placement matches the
spec and the proposal's real provenance, so I would keep it under Intelligence
**for now**.

**2. Decide the bigger question first, because it dictates the grouping:**
is "Vendor Proposals" a standalone destination at all, or a view of AI Email
Review? Three coherent end states, in rough order of how much they change:

- **Option A — Keep as is (function grouping).** Vendor Proposals stays in
  Intelligence beside AI Email Review. Lowest effort, matches current docs.
  Cost: the Vendors group stays a single item, and the AI Email Review / Vendor
  Proposals overlap (§5.1) remains.

- **Option B — Fold Vendor Proposals into AI Email Review as a tab/filter.**
  Since every proposal already renders inline in AI Email Review, make
  "Vendor Proposals" a filter there (a "Vendor replies" tab) and drop the
  separate nav item. Removes the redundancy; makes "one queue" the story. The
  Vendors group then legitimately holds just the Directory (an address book),
  which is fine.

- **Option C — Build a real "Vendors" workspace and move it there (your view).**
  Make the Vendors group a true vendor hub: Directory + Proposals + (once wired)
  the per-transaction assignment / "Email vendor" surface from §5.2. This is the
  version where your instinct is clearly right, because the group would then be
  about the whole vendor lifecycle, not just a roster. It is also the most work
  and depends on wiring the missing pieces first.

My suggestion: **Option B is the cleanest near-term cleanup** (it resolves the
overlap and the thin-group feeling at once), and **Option C is the right
long-term target** if/when the outbound vendor-comms surfaces get wired. Either
way, the label-affinity move alone (just relocating the item) is the one I would
not do, because it separates twins.

**3. Whatever is chosen, record it.** The grouping is currently asserted in
[FRONTEND_UI_WORKFLOW_LOGIC.md](FRONTEND_UI_WORKFLOW_LOGIC.md) and
[MILESTONE_4_3_IMPLEMENTATION_PLAN.md](MILESTONE_4_3_IMPLEMENTATION_PLAN.md) but
the *rationale* (function over noun) is not stated anywhere a reader will hit it.
A one-line note next to the nav spec would stop this exact question recurring.

---

## 7. Bottom line

- Your factual observation is right: Vendor Proposals is **not** in the Vendors
  group; it is in Intelligence next to AI Email Review.
- That placement is **deliberate and documented**, not an oversight: a proposal
  is an AI-generated, human-approved artifact derived from an AI email draft, so
  it is grouped by function with its sibling queue.
- Your instinct to group it with Vendor Directory is **reasonable** but optimizes
  for label affinity over workflow; the current design optimizes the reverse.
- Your bigger impression — that the workflow/logic isn't finalized — is
  **accurate and already documented**: Vendor Proposals overlaps AI Email Review,
  and Vendor Directory is an address book not yet wired into the deal flow. The
  grouping question is best answered *after* deciding whether Vendor Proposals
  should remain a separate destination at all (§6, Options A/B/C).

---

**End of analysis.**
