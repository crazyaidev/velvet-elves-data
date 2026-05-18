# Milestone 4.2 vs 4.3 — Functional Overlap Analysis

**Audited:** 2026-05-18
**Question:** Is `/vendor-proposals` (M4.3) duplicating `/ai-emails` (M4.2)?
**Verdict (short):** There is **real overlap, but it is narrow and intentional.** The two pages serve different mental models. **One specific surface — the inline `LinkedVendorProposalPanel` inside `/ai-emails` — is the genuine duplicate**, and it is the one piece worth deciding about. The rest is each page doing its own job.

This document is research only — per Jan's `feedback_no_independent_vcs` instruction, no code or migrations are changed.

---

## 1. What each page actually owns

### 1.1 `/ai-emails` — [AiEmailReviewPage.tsx](../velvet-elves-frontend/src/pages/AiEmailReviewPage.tsx)

| Aspect | Detail |
|---|---|
| Data source | [`useAiEmailDrafts`](../velvet-elves-frontend/src/hooks/useAiEmails.ts) — `communication_logs` rows with `is_ai_generated=true` (4.2 AI drafts) |
| Scope | All five AI draft kinds: `factual`, `document_request`, `vendor_reply`, `uncertain`, `other` |
| Layout | List-on-left + detail-rail-on-right |
| Mental model | "Inbox of AI drafts I need to triage and send" |
| Primary actions (per draft) | **Approve & Send**, **Edit & Send**, **Regenerate**, **Discard** |
| Filters | All / Needs Review / Ready to Send / Completed |
| Owner milestone | M4.2 |

### 1.2 `/vendor-proposals` — [VendorProposalsPage.tsx](../velvet-elves-frontend/src/pages/VendorProposalsPage.tsx)

| Aspect | Detail |
|---|---|
| Data source | [`useVendorProposals`](../velvet-elves-frontend/src/hooks/useVendorComms.ts) — `vendor_proposals` table |
| Scope | Only proposals (task-date update offers extracted from `vendor_reply` drafts) |
| Layout | Flat queue, no detail rail |
| Mental model | "Queue of proposed task-date changes I need to approve/reject" |
| Primary actions (per proposal) | **Accept** (mutates `tasks.due_date`), **Reject**, **Clarify** |
| Filters | Awaiting decision / Awaiting vendor / All open |
| Owner milestone | M4.3 |

---

## 2. The overlap — five specific places

### Overlap #1 — The `LinkedVendorProposalPanel` inside `/ai-emails`
[AiEmailReviewPage.tsx:284-328](../velvet-elves-frontend/src/pages/AiEmailReviewPage.tsx#L284)

**This is the only true UI duplicate.** When the agent opens a `vendor_reply` draft on `/ai-emails`, the right rail renders the exact same `VendorProposalCard` with the **same three buttons** (Accept / Reject / Clarify) and the **same three hooks** (`useAcceptVendorProposal`, `useRejectVendorProposal`, `useClarifyVendorProposal`) that `/vendor-proposals` uses. Two surfaces, identical action.

### Overlap #2 — Shared component
[`VendorProposalCard.tsx`](../velvet-elves-frontend/src/components/vendors/VendorProposalCard.tsx) is rendered by both pages. Not wasted code (good reuse), but the user sees the same card twice depending on where they enter.

### Overlap #3 — Shared hooks
Both pages import the same three mutation hooks from `useVendorComms.ts`. Same backend endpoints called from both surfaces.

### Overlap #4 — Sidebar navigation
[AppLayout.tsx:180-194](../velvet-elves-frontend/src/layouts/AppLayout.tsx#L180-L194) puts **AI Email Review** and **Vendor Proposals** as siblings under the "Intelligence" group. Two chips, two destinations, partially overlapping content.

### Overlap #5 — Polling
Both pages poll their respective queries every 60 s ([useAiEmails.ts](../velvet-elves-frontend/src/hooks/useAiEmails.ts) + [useVendorComms.ts:111](../velvet-elves-frontend/src/hooks/useVendorComms.ts#L111)). When both are open in different tabs/windows, the proposal data is fetched twice. Minor cost.

---

## 3. What is NOT overlap (kept distinct on purpose)

These features exist on exactly one page and shouldn't be duplicated:

| Feature | Lives only on | Why |
|---|---|---|
| Approve & Send AI draft | `/ai-emails` | The send decision is about the *email reply* (not the task date). |
| Edit & Send | `/ai-emails` | Same — modifies the AI body and sends. |
| Regenerate draft | `/ai-emails` | Re-runs the engine on the inbound. Has no analogue in proposals. |
| Discard AI draft | `/ai-emails` | Different lifecycle from "reject proposal." Discarding the draft does NOT reject the proposal, and vice versa. |
| Side-by-side inbound + draft body preview | `/ai-emails` | Email-centric UI. |
| Confidence bar, AI kind label, assumptions chips | `/ai-emails` | AI metadata visualization. |
| Per-proposal **status filtering** (`pending` / `needs_clarification`) | `/vendor-proposals` | Proposal lifecycle is *not* the same as draft lifecycle. |
| Original-vs-proposed date diff (clean, no email chrome) | `/vendor-proposals` | Optimized for the schedule decision, not the reply decision. |
| Proposals where the AI draft was discarded but the proposal is still alive | `/vendor-proposals` | A proposal can be orphaned from its draft — `/ai-emails` would not surface it once the draft is discarded. |

---

## 4. Why the overlap exists (the design intent I can read from the code)

A `vendor_reply` inbound triggers **two distinct decisions**, both done by the same person but at different cognitive levels:

```
Decision 1 — about the email           Decision 2 — about the schedule
"Should we reply, and what should      "Should the task date change to
 the reply say?"                        what the vendor proposed?"
  Approve & Send                          Accept (move tasks.due_date)
  Edit & Send                             Reject (keep current date)
  Regenerate                              Clarify (ask vendor to re-send)
  Discard
```

Conceptually these are independent. In practice they almost always travel together — when the vendor says "Scheduled: 2026-07-12," the agent both wants to *accept the date* and *send a brief confirmation*. The inline panel on `/ai-emails` exists so the agent can do both without context-switching.

`/vendor-proposals` exists for a different journey: a Transaction Coordinator does a daily/weekly scheduling sweep and just wants to triage the proposal queue without wading through unrelated `factual` or `document_request` drafts.

So both pages are *justified* — but the inline accept/reject buttons in `/ai-emails` mean the same physical action lives in two places.

---

## 5. Options and recommendation

| # | Option | Pros | Cons |
|---|---|---|---|
| A | **Keep both pages as-is** (current state) | Optimizes both user journeys; no rework. | Same action behind two buttons confuses some users. |
| B | **Drop `/vendor-proposals`** entirely; only `/ai-emails` carries the proposal panel | One queue. Fewer routes. | TCs doing schedule sweeps have to filter the AI Email Review queue manually. Orphaned proposals (where the draft was discarded) become unreachable. Losing the `pending` vs `needs_clarification` tabs. |
| C | **Drop the inline `LinkedVendorProposalPanel` from `/ai-emails`**; replace it with a small badge ("Linked task proposal: pending — view in queue →") that links to `/vendor-proposals` | One canonical surface for the proposal decision; UI is cleaner. | Agent loses one-click decision while looking at the draft — must click through to act. |
| D | **Keep inline panel as a status display only**; show "Pending — task date 2026-06-10 → 2026-07-12" and the agent's name when decided, but **remove the three action buttons** from the inline panel | Eliminates duplicate buttons. Keeps the cross-reference for situational awareness. Proposal decision happens at `/vendor-proposals` only. | Same as C — agent must click through to act. |

### My recommendation: **Option D, only if the duplicate buttons are actually a problem in practice.**

Reasoning:

- The current design (Option A) is *not wasted development*. The inline panel exists because of the legitimate UX point that the agent is already looking at the inbound and the draft when they make the date decision — letting them act there is a real workflow win, not redundancy for its own sake.
- The pages target two genuinely different mental models. Removing `/vendor-proposals` (Option B) eliminates the TC's scheduling-sweep journey and creates an orphaned-proposal blind spot.
- The thing that's *unambiguously* duplicated is the **action buttons** in the inline panel, not the panel itself. Option D removes only that duplication, keeping the cross-reference. If user testing on dev shows agents are confused about "which buttons should I click," do Option D as a 30-minute frontend tweak. If they aren't confused, leave it alone.

### What I do NOT recommend

- Keeping a "Vendor Proposals" sidebar entry under Intelligence **and** an "AI Email Review" entry pointing partially at the same data — without any tooltip explaining the difference. **Lowest-cost win:** add a one-line subtitle under each sidebar entry in [AppLayout.tsx](../velvet-elves-frontend/src/layouts/AppLayout.tsx) like:
  - *AI Email Review — drafts to approve and send*
  - *Vendor Proposals — task-date changes to approve*

  Two sentences in markup. Resolves the navigation ambiguity without rebuilding anything.

---

## 6. Other potential 4.2/4.3 overlaps I checked and ruled out

I went hunting for further duplication so I could report it here. None of these are real overlap:

1. **`communication_logs` table reuse** — M4.3 reuses M4.2's AI columns (`ai_kind`, `ai_source_data`, `parent_log_id`) and adds `metadata_json`, `message_id_header`, `in_reply_to_header`, `thread_key`. Additive, not duplicative.
2. **Audit-log actions** — M4.2 actions (`approve_and_send`, `edit_and_send`, `regenerate`, `discard`) and M4.3 actions (`vendor_request_sent`, `vendor_proposal_*`) are disjoint sets. No shadowing.
3. **AI engine entry point** — M4.2's `ai_email_inbound_hook` is the only hook. M4.3 added `propose_from_vendor_reply` as a side effect *inside* the existing flow, wrapped in try/except so it can never break M4.2. Clean layering, no parallel pipeline.
4. **Notifications taxonomy** — Both milestones add notification kinds; they don't share kinds. The [NotificationsPanel](../velvet-elves-frontend/src/components/shared/NotificationsPanel.tsx) is the single render surface for both. Good consolidation.
5. **Email provider abstraction** — Both milestones go through the same `get_email_provider_for_user`. No duplicate provider wrappers.
6. **Unified communication log** — There's exactly one comm-log page at `/admin/communications` ([CommunicationAuditPage](../velvet-elves-frontend/src/pages/admin/CommunicationAuditPage.tsx)). M4.2's AI filter and M4.3's vendor-traffic filter sit on the same page. No duplicate listing UI.

The two pages this analysis focused on are the *only* place in 4.2/4.3 where I found two surfaces touching the same action.

---

## 7. Quick-decision summary for Jake (or yourself in three months)

> Are `/ai-emails` and `/vendor-proposals` doing the same job? **No, not really.** `/ai-emails` decides "what email goes out." `/vendor-proposals` decides "what task date changes." These are two distinct workflows that happen to be triggered by the same vendor reply.
>
> The one real duplication is the **Accept/Reject/Clarify buttons** that appear both in the inline panel on `/ai-emails` and on `/vendor-proposals`. If we ever see agents asking "which one am I supposed to click," demote the inline buttons to a status badge with a link to the queue. That's a small frontend cleanup — not a milestone reopen.
>
> The pages themselves are not wasted development.

---

**End of analysis.**
