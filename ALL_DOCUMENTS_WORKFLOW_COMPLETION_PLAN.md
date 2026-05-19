# All Documents — Workflow Completion Plan

**Status:** Reviewed and revised for implementation
**Owner:** Jan (sole dev)
**Last updated:** 2026-05-19
**Reference design:** `velvet-elves-data/VE-New-AllDocuments.html`
**Frontend root:** `velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx`
**Backend roots:** `velvet-elves-backend/app/api/v1/documents.py`, `app/api/v1/dashboard.py`
**Companion plan:** `velvet-elves-data/ALL_DOCUMENTS_COMPLETION_PLAN.md` (structural completion plan; this file extends it with the workflow-and-UX gaps surfaced by client testing).

---

## 0. Purpose Of This Plan

The structural completion plan (`ALL_DOCUMENTS_COMPLETION_PLAN.md`) covers persistence, endpoint catalogue, route aliases, modal accessibility, and template generation. That work is partially landed and remains valid.

This plan responds specifically to client testing item **27.4 ("All Documents — Cleared Today strip")**, where Jake's feedback flagged the page as **"Needs Work"** with two anchor questions:

1. **"What is the 'Cleared Today Strip'?"** — the strip is a passive UI element with no introduction, no legend, and no way to find out what it is or what it does.
2. **"How do I reassign/reclassify a doc?"** — the rename modal exists, but it is buried in a `More` menu on non-AI tabs only, and it does not let a user move a document to a different transaction (which is what "reassign" usually means).

Beyond those two anchors, this plan also bundles the smaller workflow gaps that emerged while auditing the page:

- The Cleared Today strip only renders on the AI Priority tab, so it disappears the moment a user switches tabs.
- Recently-cleared cards for Mark-N/A items currently toast on click instead of opening the priority detail/audit view (the documented expected behavior in test 27.4).
- Recently-cleared cards are whole-card click targets, which violates the project rule that flag/alert cards must expose explicit `View Details` and `Open` buttons with role-aware badges (memory: `feedback_alert_card_clickability`).
- AI Priority rows with an attached document expose no Rename / Reclassify / Reassign affordance; Missing rows need Upload/Assign affordances instead because there is no document to move yet. Today the edit menu only lives on the non-AI tab `DocCard` component.
- No `Restore archived` path, no per-row Undo for Approve / Flag / Resend (only Mark N/A wires an Undo into its toast — and the toast disappears).
- No bulk actions across rows; no multi-select.

**Goal:** every visible affordance reads exactly as it behaves, every reachable action persists, and the user can always answer the two questions a brand-new operator should never have to ask: *what am I looking at?* and *how do I move this somewhere else?*

---

## 1. Completion Goal And Non-Goals

### Goal

Bring `/documents` to a state where:

- A first-time user can tell at a glance what the Cleared Today strip is, what makes a card appear in it, and what each badge means — without opening docs or asking.
- The user can reassign or reclassify any document they can see, from any tab, without hunting through a hidden menu.
- Every action shown in the UI has a real backend effect, reconciles the queue, and is reversible within a short window when reversible is sensible.
- Edge cases (no transactions, PII decrypt failure, e-sign provider not connected, large libraries, role gating) degrade calmly without dead buttons.
- The page satisfies the existing `feedback_alert_card_clickability` rule: cards expose explicit `View Details` / `Open` buttons with role-aware badges, never a single whole-card click target where multiple useful destinations exist.

### Non-Goals (deferred)

- Server-side document search beyond what global Cmd+K already does.
- MLS-driven template enrichment (still future per the structural plan).
- Cross-tenant bulk admin tools (Admin-wide tenant ops belong elsewhere).
- Read receipt / open tracking on emailed documents.
- Full-text vector search (Phase 5+).

---

## 2. What "Cleared Today" Actually Means — And How To Show It

Today the strip is implemented at [DocumentsPage.tsx:3046-3127](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3046-L3127) and only renders inside the `ai_priority` tab branch at [DocumentsPage.tsx:1501-1519](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1501-L1519). The backend builds the rows from `document_priority_events.event_type='clear'` at [dashboard.py:1514-1591](velvet-elves-backend/app/api/v1/dashboard.py#L1514-L1591). Both pieces work — but a user with no project context has no way to learn that. We will give the strip a real identity:

### 2.1 Strip Header Identity

Replace the bare `Cleared today · 4 documents` header at [DocumentsPage.tsx:3070-3080](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3070-L3080) with a self-explaining header block:

- **Title row:** `Cleared today` + the count pill.
- **One-line subtitle directly below:** `Documents resolved in the last 24 hours — uploaded, signed, approved, generated, replaced, voided, or marked N/A.`
- **Info icon** next to the title opening a small popover that lists every badge and its meaning (see §2.2). The popover uses Radix `HoverCard`/`Popover` for keyboard parity.
- **"Why isn't an item I just touched here?" affordance:** trailing text link → opens a side sheet labeled `What counts as cleared?` with the rule we already enforce server-side (touches like request / nudge / call / forward log a touch event, **not** a clear event).

### 2.2 Badge Legend

Right now the strip renders a coloured badge from `VIA_ACTION_BADGE` at [DocumentsPage.tsx:3008-3045](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3008-L3045) but the page never tells the user what each colour means. The legend popover from §2.1 contains:

| Badge | Meaning |
| --- | --- |
| Signed | E-sign envelope completed (DocuSign returned signed). |
| Approved | An internal reviewer marked the document `review_status='approved'`. |
| Marked N/A | A priority waiver was created — the requirement no longer applies to this transaction. |
| Generated | A draft was created from a template using transaction/party data. |
| Replaced | A new version was uploaded and the prior version is now Legacy. |
| Voided | An e-sign envelope was voided, removing the in-flight requirement. |
| Uploaded | An upload satisfied a missing-requirement item. |

These map to `VIA_ACTION_BADGE` and `_via_action_from_event`. Current code already includes the `upload -> Uploaded` badge mapping; the missing piece is that uploads which satisfy a priority requirement do not consistently write the `clear` event needed for the strip to render them.

### 2.3 Strip Visibility Across Tabs

Show the strip on **every** tab, not just AI Priority. The reasoning: the user just cleared something on the All Docs or Signed tab and reasonably expects to see it land in `Cleared today` without needing to switch tabs first.

Implementation: lift the `RecentlyDoneStrip` render out of the AI-priority-only branch and render it once at the bottom of the scroll canvas (above the floating `AskAiFab`). Hide it only when `recentlyDone.length === 0` and the user is on a non-AI tab (avoid empty noise on the bottom of large lists). On `ai_priority` keep it visible even when empty, with a calm `Nothing cleared in the last 24 hours yet.` placeholder so the strip's identity is never invisible at the moment a user is first learning the page.

### 2.4 Card Click Behavior (Fixing The 27.4 Bug)

Today's behavior at [DocumentsPage.tsx:1501-1518](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1501-L1518):

- If the row has a `document_id`, the click opens the preview modal.
- If it does **not** (Mark-N/A, waiver-only), the click fires a toast — that's the "dead preview" the test guide calls out as wrong.

Required behavior (matching `feedback_alert_card_clickability` and test 27.4):

Replace each card's single whole-card click with a small footer toolbar inside the card:

- **`Open`** — opens the document preview when `document_id` is present; opens the source transaction's documents view otherwise.
- **`View Details`** — opens a new `ClearedItemDetailModal` (small, read-only) showing:
  - The doc label, the transaction address, the `via_action` badge, the actor name (who cleared it), the cleared-at timestamp.
  - The before/after state pulled from the `audit_logs` row referenced by the event, when present.
  - The current document review state if `document_id` is set.
  - For waivers: the `reason` text the user wrote and an `Undo (revoke waiver)` action if the current user is the actor or has Admin/TeamLead role.
- **Badge area** in the corner: role-aware badge that already exists today (Signed, Approved, etc.).

The whole-card click target goes away — the card body remains visually clickable on hover but the actual mutation is bound to the two explicit buttons.

### 2.5 Per-Card Undo

Wire the badge-aware Undo right onto the card, not just into the disappearing toast. Rules:

| via_action | Undo behavior |
| --- | --- |
| `waive` | Revoke the waiver via existing `POST /documents/priority-waivers/revoke`. Restores the queue row. |
| `approve` | New `POST /documents/{id}/review/unapprove`. Restores `review_status='unreviewed'`, logs an audit row, fires a `clear`→`unclear` priority event. |
| `signed` | No undo. Toast: `Signed envelopes can't be undone — void the envelope from the document row instead.` |
| `generated` | Soft-delete the draft and write a reversal event (`event_type='unclear'`, `action_key='delete_generated'`). Do **not** delete the original priority event; the audit chain must remain intact. Confirmation dialog: "Delete this generated draft? The missing-doc row will return." |
| `replace` | No undo from here — version history lets the user roll back manually. |
| `void` | Not yet supported by the e-sign provider integration — show `Send for signature again` shortcut instead, which is the practical recovery path. |
| `upload` | Soft-delete the uploaded document (existing flow). |

Undo button uses `AlertDialog` for the dialog confirmation step where deletion is involved; otherwise it fires directly and shows a completion toast with a clear way to reopen the affected item.

Important reconciliation rule: `recently_done` must suppress or mark clear events that were later reversed by `unwaive`, `unapprove`, generated-draft deletion, uploaded-document archive, or restore/rollback events. Never remove historical `document_priority_events` rows to make the strip look right; add a reversal event and let the query derive the current display state from event order.

### 2.6 Strip Filters

Add a small inline filter row inside the strip header:

- **`All`** (default) — every actor.
- **`Me`** — only items where `actor_id` matches `auth.user.id`.
- **`Team`** — internal teammates excluding current user.

Implementation: the backend already filters by tenant; add `?cleared_actor_scope=all|me|team` to `GET /api/v1/dashboard/documents-priority-queue` (default `all`) and to the 7-day cleared sheet endpoint. This scope applies only to `recently_done` / cleared-event rows, not to active queue items. Frontend toggles the existing `cleared_scope` URL param and refetches.

### 2.7 View All Cleared

Currently the strip caps at 8 rows ([dashboard.py:1591](velvet-elves-backend/app/api/v1/dashboard.py#L1591)). For a high-volume team, the user has no way to see beyond that today. Add a trailing tile `View all cleared (last 7 days)` that opens a side sheet listing the full `document_priority_events.event_type='clear'` for the tenant over a 7-day window with the same filter chips. Pagination is server-side (`limit=25`, `cursor`-based). No new top-level route — this is a sheet over the page.

---

## 3. Reassign And Reclassify — Solving The Second Client Question

### 3.1 The Current State

- The backend `PATCH /api/v1/documents/{document_id}` already accepts a `transaction_id` field for internal roles ([documents.py:611-620](velvet-elves-backend/app/api/v1/documents.py#L611-L620)). `_validate_internal_transaction_access` enforces tenant scope.
- The frontend hook `useUpdateDocument` already supports `transaction_id` in its input ([useDocuments.ts:204-210](velvet-elves-frontend/src/hooks/useDocuments.ts#L204-L210)).
- **But the only UI surface that calls it — `RenameDocumentModal` at [RenameDocumentModal.tsx:29-124](velvet-elves-frontend/src/components/documents/RenameDocumentModal.tsx) — does not expose a transaction picker.** The reassign capability is fully built on the back side and invisible on the front side.
- The modal itself is only reachable from the More menu of `DocCard` ([DocumentsPage.tsx:3489-3493](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3489-L3493)), which is **only used on the non-AI tabs**. AI Priority rows and Missing rows have no rename/reclassify menu at all.

### 3.2 The Fix In Three Pieces

**A. Surface a transaction picker in the existing modal.**

Add a `Transaction` selector to `RenameDocumentModal`:

- A `Combobox` populated from the same `/api/v1/transactions` list the page already loads (txById Map at [DocumentsPage.tsx:484-488](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L484-L488)).
- For an `Agent` actor, the list is filtered to transactions the actor has access to (Repo + RLS already enforce this).
- Confirmation banner when changing transactions: `Moving this document will reattach the audit history and version chain to the new transaction. Signed or in-flight envelopes cannot be moved.` Render in amber, not destructive red — the operation is reversible by reassigning back when the document is eligible.
- Save sends a `PATCH` with `transaction_id` plus any of the existing rename fields the user changed.

**B. Rename the action surface.**

Replace the More-menu label `Rename / Reclassify` at [DocumentsPage.tsx:3491](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3491) with **`Edit Document…`**. That covers all three operations (rename, reclassify, reassign) in language that matches what users actually call it. Update the modal title to `Edit Document`. Inside, group the fields visually: `Identity` (file name, label, type) and `Assignment` (transaction).

**C. Expose `Edit Document` from every list view.**

Today the menu only lives on `DocCard`. Add a parallel entry to the AI Priority and Missing row's alt-actions surface:

- In the `PriorityDetailModal` (open via "View Details" from queue rows), add an `Edit Document` row to the alt-actions if `item.document_id` exists.
- Also expose it from the `QueueRow` more-menu on hover — same dropdown pattern as `DocCard` but only enabled when `document_id` is non-null, so it never appears on `missing` items where there is nothing to edit yet.
- Hide for client/FSBO/vendor roles using the same `isInternal` gate already used at [DocumentsPage.tsx:3489](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3489).

### 3.3 The Reassign Audit Trail

Use the existing `AuditService.log_update` instrumentation that already runs on `PATCH /documents/{id}` ([documents.py:627-634](velvet-elves-backend/app/api/v1/documents.py#L627-L634)). Current code already includes `transaction_id` in `_doc_snapshot`; keep it there and add a regression test so a later cleanup cannot remove the field and silently break reassign audit diffs.

Also fire priority events when the transaction changes, but do **not** treat every reassign as a clear on the old transaction:

- For the old transaction: write `event_type='touch'`, `action_key='reassign_out'`, `item_key=item_key_for_old_tx`, `note='Reassigned to {new_tx_address}'`. Then let the queue recompute. If the moved document had been satisfying a requirement, the old transaction should become missing again; the event must not mask that.
- For the new transaction: if the reassigned document satisfies a currently missing requirement, write `event_type='clear'`, `action_key='reassign'`, `item_key=item_key_for_new_tx`, `note='Reassigned from {old_tx_address}'`. If it does not satisfy a missing requirement, write only a `touch`.
- The `recently_done` strip may show **Reassigned** only for the destination-side clear case. A pure cleanup move that does not resolve a requirement belongs in audit history, not Cleared Today.

Add `reassign` to `VIA_ACTION_BADGE` and `_via_action_from_event` with the label **Reassigned** (neutral grey badge).

### 3.4 Edge Cases

| Case | Behavior |
| --- | --- |
| Reassign to a transaction that already has a current-version doc of the same type | Modal warns and offers `Keep both` for MVP. `Make this the latest version` requires a dedicated reparent/version-chain endpoint and must not be smuggled into the basic metadata `PATCH`. |
| Reassign to a transaction the user can't access | Save blocked client-side; backend would return 403 anyway. |
| Reassign while an envelope is in flight | Modal blocks the save with a clear message: `Void or wait for the envelope before reassigning — moving signed envelopes between transactions breaks the audit chain.` |
| Reassign a doc that has been used as a "clear" event source | Audit log keeps the original event; the new transaction picks up the doc as if uploaded today. |
| Two users edit the same doc concurrently | Backend already wins last-write; we surface a refetch hint after success and surface the new snapshot in the modal. No optimistic-locking ETag yet — Phase 5+. |

---

## 3.5 Template Generation Workflow Recovery

This sub-section sits with §3 (rather than as a standalone top-level section) because it is the third recurring client-facing workflow surface that interrupts the user today. Where §2 fixed "what is Cleared Today" and §3 fixed "how do I reassign," this fixes "I clicked Generate and now I'm stuck."

### 3.5.1 The Two Stuck States

The `Generate` action at [DocumentsPage.tsx:1162-1232](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1162-L1232) calls `POST /api/v1/documents/generate-from-template` at [documents.py:1841-1888](velvet-elves-backend/app/api/v1/documents.py#L1841-L1888) and opens a single shared modal for any non-success response. That modal has only one button (`Got it`) and offers no recovery path. Two distinct failures land in it today, with different root causes but identical UX:

| Failure | Root cause | What the user sees | What's broken |
| --- | --- | --- | --- |
| `no_template` | `item_key` is not in `_TEMPLATE_RULES` at [documents.py:1715-1743](velvet-elves-backend/app/api/v1/documents.py#L1715-L1743) — yet the priority queue config at [dashboard.py:1052-1059](velvet-elves-backend/app/api/v1/dashboard.py#L1052-L1059) still lists `template` as an alt action for the same `item_key` (e.g. `appraisal_report`). | "No template is registered for this requirement yet…" + trailing "Fill these on the transaction first" copy that does not apply (no fields are listed). | The button should not have been offered. The user has no Upload or Request pivot from the modal. |
| `missing_fields` | The template exists but a required field on the transaction is empty (e.g. `seller_name` because the seller party row is missing). | "I can prepare this draft once the missing fields are filled" + a list with the human label and the raw machine field name next to it. | No deep link to the place where the field lives. The machine name is noise. The user does a seven-step manual scavenger hunt to fill one name. |

### 3.5.2 Backend Changes

**A. Filter unregistered templates from `alt_actions` and `suggested_action`.**

Before assembling each ranked item, drop `template` from the `alt_actions` array (and replace it as `suggested_action` with the next-best action — typically `request` or `upload`) when `item.item_key not in _TEMPLATE_RULES`. Add a single source-of-truth helper `def _template_registered(item_key: str) -> bool` so both the priority queue endpoint and the generate endpoint share the same registry check. This eliminates the dead button for Appraisal Report, Title Commitment, and any other requirement we don't have a template for yet.

**B. Split the response status.**

Today the endpoint returns `status="missing_fields"` for both failures. Change to:

```ts
type DocumentTemplateGenerateResponse =
  | { status: "generated", document_id: string, message: string | null }
  | { status: "missing_fields", missing_fields: { field: string, label: string }[], message: string }
  | { status: "no_template", message: string, suggested_alternatives: ("upload" | "request")[] }
```

`suggested_alternatives` lets the backend hint which pivots make sense for that requirement based on the same priority-queue rules — the frontend renders them as real buttons.

**C. Add the "where to fix" pointer to each missing field.**

Extend `DocumentTemplateMissingField` with a `fix_route` discriminated union so the frontend can build a deep link without knowing the schema:

```ts
type DocumentTemplateMissingField = {
  field: string
  label: string
  fix_route:
    | { kind: "party", role: "buyer" | "seller" | "title_company" | ... }
    | { kind: "transaction_field", field: "purchase_price" | "address" | "title_company" | ... }
}
```

Mapping examples: `seller_name` → `{kind: "party", role: "seller"}`; `purchase_price` → `{kind: "transaction_field", field: "purchase_price"}`; `title_company` → `{kind: "transaction_field", field: "title_company"}` (or `{kind: "party", role: "title_company"}` if the title company is modelled as a party in that tenant).

### 3.5.3 Frontend Changes

**A. Split the modal into two intent-specific surfaces.**

- `TemplateNotAvailableModal` — for `status="no_template"`. Title: `No template yet for {label}`. Body: one calm sentence explaining the system doesn't have a draft template for this requirement type. Footer has two real CTAs derived from `suggested_alternatives`: **Upload draft manually** (opens the existing upload modal pre-filled for this transaction + doc type) and **Request from counter-party** (opens the request modal pre-filled). No "Got it" dead end.
- `TemplateMissingFieldsModal` — for `status="missing_fields"`. Title: `Almost ready — {label}`. Body lists the **human labels only** (no raw `seller_name` machine names). Each row gets an inline `Fix →` button whose destination is derived from `fix_route`. Footer has two CTAs: **Open transaction** (deep link, default focus) and **Cancel**.

**B. Inline fix for the small-data cases.**

For `fix_route.kind === "transaction_field"` on a small set of safe-to-edit fields (`purchase_price`, `title_company`), render a tiny inline input inside the modal row instead of forcing navigation. Save calls `PATCH /api/v1/transactions/{id}` (existing). For `fix_route.kind === "party"`, navigation is the right call — the parties tab has the full role/email/phone form and we should not duplicate that surface.

**C. Deep-link targets in the transaction page.**

The deep link uses query params already supported by the transaction detail page (`?tab=parties` and `?tab=overview`) plus a new one: `?focus_missing=<field_or_role>` that scrolls to and highlights the missing field/party row for ~2.5s using the same `search-focus-flash` animation already used at [DocumentsPage.tsx:655](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L655).

**D. Auto-retry after fix.**

When the user navigates back to `/documents` from a deep link they originally launched from the missing-fields modal, the page sees the `?retry_template=<item_key>` param it added on departure, fires Generate again silently, and either replaces the previous modal with the `TemplateMissingFieldsModal` (if more is still missing) or surfaces the new draft directly. This closes the loop without forcing a second user click.

### 3.5.4 Copy Rules (Replace The Current Strings)

| Where | Old | New |
| --- | --- | --- |
| `no_template` body | "No template is registered for this requirement yet. Upload your draft manually and we'll attach it to this transaction." | "I don't have a template for {label} yet. You can attach your own draft, or ask the counter-party for one." |
| `no_template` footer line | "Fill these on the transaction first and try again — I never guess where a signature line should go." | Removed entirely. The "I never guess" line stays only on the missing-fields modal where it's relevant. |
| `missing_fields` row | `Seller's full name` + raw `seller_name` chip | `Seller's full name` only. Trailing `Fix →` button replaces the raw chip. |
| `missing_fields` body | "I can prepare this draft once the missing fields are filled. Add them to the transaction first, then try again." | "I'll draft {label} as soon as these are on the transaction. Click Fix on any row to jump straight there." |

### 3.5.5 Edge Cases

| Case | Behavior |
| --- | --- |
| Template registered but the deep link target field is read-only for the user's role | `Fix →` is disabled with a tooltip "Ask your team lead — this field is restricted." |
| User opens two missing-fields modals via the same `item_key` in two tabs | Auto-retry on return only fires for the most recent retry token; older tokens are ignored. |
| User fills the field then closes the tab without returning | Next time the row is rendered, normal Generate flow works. No stale retry state. |
| Backend can't determine a `fix_route` for a custom tenant-specific field | Modal still lists the label; the `Fix →` button is replaced by `Open transaction` for that row. |
| The list of `suggested_alternatives` is empty (rare) | Footer shows only `Cancel` plus a `View document detail` link to the priority detail modal. |

---

## 3.6 Sort Dropdown Coverage

This sub-section sits with §3 alongside the other workflow-interruption fixes. It addresses a silent contract violation: the sort dropdown above the filter tabs persuades the user that picking `Document name` (or any other option) will reorder the list — but on four of the six tabs that promise is not kept.

### 3.6.1 The Current State

The sort state at [DocumentsPage.tsx:343-378](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L343-L378) is global to the page and persists to `?sort=`. It feeds `visibleQueue` at [DocumentsPage.tsx:566-591](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L566-L591), which is the source for `aiPriorityListItems` and `missingItems`. Those two tabs honour the sort.

The other four tabs (`all_docs`, `pending_review`, `sent_for_signature`, `signed`) render `CategorizedView` at [DocumentsPage.tsx:1547-1573](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1547-L1573). The `sort` prop is **not** passed in. Inside `CategorizedView` at [DocumentsPage.tsx:3171-3186](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3171-L3186), the only derivation is the tab filter — there is no sort step. The `<ul>` then iterates `filtered` directly, leaving the documents in the order `useAllDocuments()` returned them (typically `created_at DESC` from the backend).

Net effect: the dropdown chip and the URL update correctly, but the visible list never re-orders on the four categorized tabs. This violates the principle stated in §1 that "no action shown in the UI is cosmetic."

### 3.6.2 Why The Fix Is A Two-Parter

The five sort keys were designed against `DocumentPriorityItem`, which carries `days_to_close`, `last_touched_at`, and a server-provided AI rank. `UploadedDocument` has none of those directly — so naively passing `sort` into `CategorizedView` is not enough. We need an explicit mapping from each sort key to a comparator over `UploadedDocument`:

| Sort key | Behavior on raw documents |
| --- | --- |
| `ai_impact` | No server-ranked AI order exists for raw docs. Fall back to `recently_updated`. Keep the dropdown chip label as `AI impact` so users on the AI Priority tab don't lose context when they switch tabs — but make the chip subtitle read `(falls back to Recently updated on this tab)` so the behavior is honest. |
| `close_date` | Join through `txById.get(d.transaction_id)?.closing_date`. Docs whose transaction has no closing date sort last. |
| `doc_name` | `(d.doc_label ?? d.file_name).localeCompare(...)`. Case-insensitive. |
| `recently_updated` | `(d.updated_at ?? d.created_at)` descending. |
| `last_touched` | Same as `recently_updated` for raw docs — no per-document touch ledger exists yet. The dropdown chip stays `Last touched` but the behaviour is documented as equivalent to `Recently updated` on these tabs. A future enhancement could read `document_priority_events.event_type='touch'` per document to make this distinct. |

Centralise these comparators in a single helper module — see §3.6.3 — so the AI Priority / Missing path and the categorized path stay symmetric and the chip label always means the same thing.

### 3.6.3 Frontend Changes

**A. Pass `sort` into `CategorizedView`.**

Update the `CategorizedView` props at [DocumentsPage.tsx:3149-3167](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3149-L3167) and the render call at [DocumentsPage.tsx:1547-1573](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1547-L1573) to include `sort: DocSortKey` and `txById: Map<string, Transaction>` (already present for transaction-address rendering).

**B. Extract a single sort helper module.**

Create `src/utils/documentsSort.ts` exporting two pure functions:

```ts
sortPriorityItems(items: DocumentPriorityItem[], sort: DocSortKey): DocumentPriorityItem[]
sortUploadedDocs(
  docs: UploadedDocument[],
  sort: DocSortKey,
  txById: Map<string, Transaction>,
): UploadedDocument[]
```

Move the existing inline sort body from `visibleQueue` ([DocumentsPage.tsx:566-591](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L566-L591)) into `sortPriorityItems` so there is exactly one definition of each sort key's behavior. Both functions use the mapping table in §3.6.2.

**C. Apply the sort inside `CategorizedView`.**

In the `filtered` `useMemo` at [DocumentsPage.tsx:3171-3186](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3171-L3186), wrap the tab-filtered array with `sortUploadedDocs(arr, sort, txById)`. The memo dependency list gains `sort` and `txById`.

**D. Update the sort dropdown subtitle when on a categorized tab.**

In `DocFilterTabs` (around [DocumentsPage.tsx:2169-2261](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L2169-L2261)), when `activeTab` is one of the categorized tabs and `sort === 'ai_impact'`, render a small one-line caption under the dropdown chip: `Sorted by Recently updated on this tab.` This keeps the user honest about the fallback without changing the chip's label or position.

**E. Numbering / row index reset.**

`DocCard` receives an `index` prop. The current ordering is `idx + 1` from the iteration — that means sorting will renumber rows visually, which is fine and expected. No change needed beyond confirming the visual reads correctly when the list is reordered (e.g. closing-date ascending: row #1 is the soonest-to-close, not the first one uploaded).

### 3.6.4 Edge Cases

| Case | Behavior |
| --- | --- |
| Sort by `close_date` on All Docs when most docs belong to closed/legacy transactions with no `closing_date` | Those rows sink to the bottom; the head of the list is the soonest-to-close active deal. |
| Sort by `doc_name` and the doc has neither `doc_label` nor `file_name` | Treated as empty string — sorts to the top in ascending order. Should never happen in practice (file_name is required at upload time). |
| Switch from `ai_impact` to `doc_name` on All Docs, then back to AI Priority tab | The dropdown chip stays `Document name` and is honoured on every tab. No second click required. |
| 10,000-document tenant | Sorting is O(n log n) client-side; on a list of 10k the perceived cost is single-digit milliseconds and acceptable. Future improvement: server-side sort + pagination. |
| User picks `last_touched` on the Signed tab | Falls back to `recently_updated` per the mapping table; the dropdown caption explains the equivalence on categorized tabs. |

---

## 3.7 Deletion Approval Surface — Workflow Completion

This sub-section closes the loop on the `Flag for deletion` → `Deletion Queue` → approve/reject workflow. The feature works end-to-end at the API layer but has five concrete UX holes that make it unfinished from the user's perspective.

### 3.7.1 The Five Gaps

| Gap | Where it lives today |
| --- | --- |
| 1. External users can't reach `Flag for deletion` from their dedicated portal documents pages | [ClientDocumentsPage.tsx](velvet-elves-frontend/src/pages/client/ClientDocumentsPage.tsx) is a count-summary stub; [FsboDocumentsPage.tsx:30](velvet-elves-frontend/src/pages/fsbo/FsboDocumentsPage.tsx#L30) literally tells users to *"click Flag for deletion"* — a button that does not exist on the page. The only path is the Transaction Documents modal (which §3.8 fixes separately). |
| 2. No pending-count badge on the `Deletion Queue` header button | [DocumentsPage.tsx:1393-1403](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1393-L1403) — reviewers can't tell at a glance whether anything is waiting. |
| 3. The requester never hears back when approve/reject fires | Backend endpoints at [documents.py:1318, 1353](velvet-elves-backend/app/api/v1/documents.py#L1318) record the decision in `audit_logs` but emit **no notification, no email**, to the user who originally flagged the document. |
| 4. `Approve` is destructive but has no confirmation step | [DeletionApprovalsPanel.tsx:29-43](velvet-elves-frontend/src/components/documents/DeletionApprovalsPanel.tsx#L29-L43) — a single click archives the document. Should be a Radix `AlertDialog` confirm, especially for signed documents. |
| 5. The placement violates the page's AI-led identity | [DocumentsPage.tsx:1393-1403](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1393-L1403) — Jake's new design dropped the button; it's a moderation surface on a "work surface." See `VE-New-AllDocuments.html` — no Deletion Queue button anywhere. |

### 3.7.2 The Fix

**A. Real document lists with Flag entry on every external portal page.**

Replace the stubs:

- `ClientDocumentsPage` → render a real per-document list using the existing role-scoped `GET /api/v1/documents`, or add `GET /api/v1/client/documents` as a thin alias if the portal needs a dedicated route. Each row exposes the same three-dot menu the Transaction Documents modal uses, with `Flag for deletion` as the action for Client role.
- `FsboDocumentsPage` → render the same role-scoped document list, or add `GET /api/v1/dashboard/fsbo/documents` as a thin alias if the dashboard route needs a stable contract.
- `VendorDocumentPortalPage` → same pattern using the generic role-scoped endpoint unless a vendor-specific alias is implemented in the same slice.
- Each row also shows a small `Flagged` badge inline when `deletion_flagged=true` so the requester can see their own pending requests without re-clicking.
- The Flag button itself reuses `FlagForDeletionModal` — no new modal needed.

**B. Pending-count badge on the Deletion Queue button (and hide when zero).**

Add a lightweight count endpoint that doesn't load the full row payload:

```text
GET /api/v1/documents/flagged/count → { pending: number }
```

Backed by a `COUNT(*)` over the same filter the existing `GET /flagged/list` uses. Cached for 30s server-side.

New frontend hook `useFlaggedDocumentsCount()` polled alongside the priority queue. The button at [DocumentsPage.tsx:1393-1403](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1393-L1403) gains:

- A pill badge showing `pending` when `> 0`.
- `display: none` when `pending === 0` (no zero-state noise alongside Upload / Send for Sig).
- A subtle dot indicator within the first 24h of any new flag to signal recency.

This is the bridge fix while migration **E** (below) lands.

**C. Notify the requester on every decision.**

Backend changes on `approve-deletion` and `reject-deletion`:

- Insert a row into the existing `notifications` table addressed to `documents.deletion_flagged_by`. Notification body includes the decision (`Approved` / `Rejected`), the doc label, the reviewer's name, and the reviewer's `decision_reason` if provided.
- Send email through a concrete deletion-decision notification helper. Do not assume a generic dispatcher exists; the helper owns notification insert, email send/skip, and logging as described in §3.9.14.
- Email subject: `Your deletion request for {doc_label} was {approved|rejected}`.
- Email body uses first-person plural from the system (`Your agent reviewed your request…`) — this is system-generated, not agent-as-Jan, so the `feedback_first_person_singular` rule does not apply here.

Frontend: the requester's notification bell shows the entry; clicking it deep-links to the transaction's Documents modal (now reachable via the `?focus=<document_id>` pattern already used in §3.7.2A).

**D. Confirmation step on Approve.**

Wrap the existing Approve button in a Radix `AlertDialog`:

- Title: `Approve deletion of {doc_label}?`
- Body (default): `This archives the document. The requester will be notified. You can restore it via Restore Archived for up to 90 days.`
- Body (when `doc.is_signed === true`): `This document has a signed signature record. Archiving it removes it from the active document list, but the signature audit trail stays in audit_logs. The requester will be notified.`
- Confirm button: `Archive document`, styled with the canonical destructive-dialog treatment from `STYLE_GUIDE.md` (type-led Radix `AlertDialog`, no native confirm, no one-off red styling unless the shared destructive token already does that).
- Cancel: returns focus to the row.

Reject keeps its current behavior — no confirm dialog needed since it's non-destructive — but the existing Reject reason textarea becomes required (≥3 chars) so the requester always gets a "why" line in their notification.

**E. Migrate the surface off the AI-led header (default path).**

The durable answer: emit deletion-flag rows as priority items.

- In `dashboard.py:dashboard_documents_priority_queue`, after the existing queue is assembled, query `documents WHERE deletion_flagged = true` for the tenant and emit a priority item per row with:
  - `kind = 'deletion_review'`
  - `severity` = `critical` if the doc is signed, else `medium`
  - `suggested_action = 'review_deletion'`
  - `suggested_action_label = 'Review deletion request'`
  - `alt_actions = ['preview', 'edit']`
- New action key `review_deletion` opens the existing `DeletionApprovalsPanel` filtered to just that one row (or opens an inline expansion).
- Once the priority-item path lands, the header button is removed entirely. Path B's badge becomes irrelevant.
- If the migration slips, the header button + badge from B is the stable bridge.

### 3.7.3 Edge Cases

| Case | Behavior |
| --- | --- |
| Deletion approved on a doc with an in-flight envelope | Block the approve with a 409 + structured `envelope_in_flight` error — same pattern as reassign in §3.4. The reviewer must void the envelope first. |
| Two reviewers approve the same flag simultaneously | First write wins; the second `POST /approve-deletion` returns 409 `already_decided` with the decision and reviewer; the UI surfaces a calm toast and refetches. |
| Requester is no longer on the tenant when the decision fires | Notification dispatch logs a warning and skips email; in-app notification is not created. No crash. |
| Doc is already soft-deleted before approve fires (race) | Approve becomes a no-op + 200; notification still fires so the requester sees the closure. |
| Tenant has notifications disabled | In-app notification still inserts; email is skipped silently per the tenant setting. |
| Decision reason is empty on Reject | Backend returns 422 with a structured error pointing the reviewer to fill the field. Reason is required on Reject (per D); optional on Approve. |

---

## 3.8 Transaction Documents Modal — Stacking And Completion

This sub-section addresses a related but distinct surface: the **Transaction Documents modal** at [DocumentsModal.tsx](velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx) — the overlay that opens from a transaction card's footer (`View / Add Documents`) on `/transactions/active`. The same external users who use it to `Flag for deletion` (§3.7) and the same internal users who use it for in-context document review experience six broken affordances today, all rooted in the same bug.

### 3.8.1 The Critical Bug — Stacking Context Inversion

The parent overlay at [DocumentsModal.tsx:541](velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx#L541) uses a hard-coded **`z-[600]`** arbitrary Tailwind class:

```tsx
<div className="fixed inset-0 bg-[rgba(30,30,30,0.45)] z-[600] flex ..." onClick={onClose}>
```

Every child surface inside it is a Radix primitive that ships at `z-50`:

| Child component | Source line | z-index |
| --- | --- | --- |
| `DocumentEmailModal` (Radix `Dialog`) | [dialog.tsx:18, 35](velvet-elves-frontend/src/components/ui/dialog.tsx#L18) | `z-50` overlay + `z-50` content |
| `VersionHistoryPanel` (Radix `Dialog`) | same | `z-50` |
| `RenameDocumentModal` (Radix `Dialog`) | same | `z-50` |
| `FlagForDeletionModal` (Radix `Dialog`) | same | `z-50` |
| Archive confirm (Radix `AlertDialog`) | [alert-dialog.tsx:16](velvet-elves-frontend/src/components/ui/alert-dialog.tsx#L16) | `z-50` |
| AI-parsed updates confirm (Radix `AlertDialog`) | same | `z-50` |
| More-actions menu (Radix `DropdownMenu`) | [dropdown-menu.tsx:39](velvet-elves-frontend/src/components/ui/dropdown-menu.tsx#L39) | `z-50` |

Radix portals each child to `document.body`, so they become siblings of the parent overlay element at the DOM root and compete on z-index alone. `50 < 600` → every child renders correctly but is **visually obscured under the parent's `z-[600]` backdrop**. The user clicks the button, the modal IS open and IS receiving focus — they just can't see it. Six surfaces broken from one root cause.

### 3.8.2 A Second Separate Bug — Download Popup Blocker

`handleDownload` at [DocumentsModal.tsx:508-519](velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx#L508-L519) `await`s the signed URL and then calls `window.open(url, '_blank')`. Most modern browsers (Chrome, Safari, Firefox) block `window.open` when invoked after an `await` because the user-gesture context has elapsed. This is independent of §3.8.1 — Download would feel broken even if the parent z-index were correct.

Fix the user-gesture problem in every path. For **Open in new tab**, pre-create the tab synchronously inside the click handler, then mutate its `location.href` once the signed URL resolves. For a button labeled **Download**, prefer attachment/blob behavior per §3.9.4 so the action saves the file instead of merely opening a preview.

```ts
const openSignedDocumentUrl = async (doc: UploadedDocument) => {
  const win = window.open('about:blank', '_blank', 'noopener,noreferrer')
  try {
    const url = await downloadDoc(doc.id)
    if (!url) { win?.close(); throw new Error('No download URL'); }
    if (win) win.location.href = url
    else window.location.href = url   // popup blocked anyway → navigate current tab
  } catch (err) {
    win?.close()
    toast({ title: 'Open failed', description: err instanceof Error ? err.message : '', variant: 'destructive' })
  }
}
```

Use the same gesture-safe pattern wherever `window.open` is needed in the documents code path, and use blob/attachment semantics for true downloads.

### 3.8.3 The Right Fix — Replace The Hand-Rolled Overlay With Radix

Bumping `z-[600]` to `z-[700]` (and then to `z-[800]` next time) is not the right fix — the same bug will resurface every time a new child surface ships. The structural fix is to **replace the hand-rolled parent overlay with a Radix `Sheet` (slide-in panel) or `Dialog`** so the parent and all its children share the same `z-50` stack and stacking-context inversion becomes impossible.

Benefits, all in one change:

- Z-index parity with every other modal in the app — no more arbitrary `z-[N]` values.
- Built-in focus trap and Escape handling (currently the hand-rolled parent has neither — Tab escapes the modal, Escape does nothing).
- Proper `role="dialog"`, `aria-modal="true"`, and `aria-labelledby` for free.
- A `data-state` attribute the rest of the app can lean on for animations.

Recommendation: use **Radix `Sheet`** with side `right` (or `bottom` on mobile) because the surface is content-dense — a side panel reads better than a centered dialog for long document lists. The existing visual styling can be ported over with minimal change; only the outer container element changes.

### 3.8.4 Feature Completeness Gaps Beyond The Stacking Fix

While auditing the modal I found seven feature gaps relative to what the All Documents page already does for the same documents. The transaction-context modal should reach feature parity with `/documents` for everything except cross-transaction operations.

| # | Missing capability | Why it matters |
| --- | --- | --- |
| 1 | Send for Signature button | Internal users in transaction context have no way to start a signing flow without leaving the modal. The `useSendForSignature` hook already exists. |
| 2 | Document preview (currently the doc name button only downloads) | All Documents has a real PDF/image preview modal; this surface forces a tab open for every viewing. Reuse the same preview modal. |
| 3 | Filter / sort / search within the list | Large transactions with 30+ docs are unscannable. Reuse `sortUploadedDocs` from §3.6 — already the right helper. |
| 4 | Sync / Void envelope on `awaiting` docs | If a signature stalls there's no recovery here — user must leave to `/documents`. Both hooks exist (`useSyncEsignStatus`, `useVoidEsign`). |
| 5 | Edit Document (rename + reclassify + reassign) | Currently uses `RenameDocumentModal` which (per §3.2A) does not yet expose a transaction picker. Once §3 lands, this surface picks up the same Combobox automatically. |
| 6 | Restore Archived entry point | After Archive is approved, no restore path on this surface. Reuse the `RestoreArchivedPanel` from §7.1. |
| 7 | Internal follow-up flag (`document_followup_flags`) | Today's `Flag` action in this modal means *"request deletion."* There's no internal *"needs follow-up"* flag, even though the table exists in the companion plan. Add a separate `Mark for follow-up` row in the More menu when `isInternal`. |

### 3.8.5 Edge Cases

| Case | Behavior |
| --- | --- |
| Parent modal is open while a child dialog is open (after stacking fix) | Parent backdrop dims slightly more (Radix stacks overlay opacity); child has its own backdrop; closing the child returns focus to the parent's last focused element. |
| Customer opens the modal from a transaction they share but contains no documents | Empty state copy already exists — confirm it still reads correctly after the conversion to Radix `Sheet`. |
| User clicks Download while the modal is closing | The `await` resolves after unmount; the pre-opened tab navigates to the URL anyway — no crash. |
| User upload completes after they closed the modal | The AI-parsed updates AlertDialog should still appear (Radix portals to body, not to the parent). After the fix it's visible regardless of whether the parent modal is open. |
| Same document appears here and in `/documents` simultaneously | Both surfaces use the same React Query cache. A mutation in one surface invalidates and refreshes the other. |

---

## 3.9 Plan Review Corrections And Newly Found Gaps

This section supersedes any earlier line that conflicts with it. It captures the issues found while cross-checking this draft against the current frontend/backend implementation and the companion structural plan.

### 3.9.1 Clear-Event Ledger Completeness

The draft explains the Cleared Today UI, but it still assumes the backend ledger already contains every clear. It does not.

Current gaps:

| Action | Current state | Required correction |
| --- | --- | --- |
| Upload from a Missing row | `POST /documents/upload` creates the document and audit row, but does not receive the originating `item_key` and does not write a `document_priority_events` clear row. | Add `priority_item_key` and `doc_label` to the upload form payload when launched from a queue row. Log `event_type='clear'`, `action_key='upload'` only when the upload satisfies that missing requirement. |
| Upload from the header | User may upload an unassigned/unclassified doc; this should not appear as Cleared Today unless it resolves a specific missing requirement. | Treat as ordinary upload. It appears in All Docs but not Cleared Today until assigned/classified in a way that satisfies a requirement. |
| New version / Replace | `create_new_version` writes audit history but no priority event. | When replacement is launched from a queue item, log `event_type='clear'`, `action_key='replace'`, with source and new document ids in metadata. |
| Signed envelope completion | E-sign completion stores a signed version, but no `action_key='signed'` clear event is written. The current fallback only scans signed docs when there are **no** clear events at all, so signed docs can disappear from the strip once any other clear exists. | In `_apply_envelope_event`, after the signed version is stored, log `event_type='clear'`, `action_key='signed'` for the signed version and originating queue item. |
| Void envelope | Void updates `signature_status='voided'` and audit logs, but no priority event records why the sent row left or changed state. | Log a `touch` or clear/recovery event based on final product behavior: if void removes an in-flight requirement from the queue, log `clear` + `void`; if it should prompt resend, keep the row and log `touch` + `void`. Do not silently drop it. |
| Reversal / Undo | The draft sometimes says to remove priority events. | Never delete ledger rows for normal undo. Add reversal rows (`unwaive`, `unapprove`, `delete_generated`, `archive_uploaded`, `restore_uploaded`) and make read queries derive the visible strip from ordered events. |

Implementation detail: add a backend helper such as `record_document_resolution_event(...)` in a service module shared by `documents.py`, `esign.py`, and `dashboard.py`. It should normalize `item_key` values, attach `tenant_id`, `transaction_id`, `document_id`, `actor_id`, and optional `audit_log_id`, and avoid duplicate clear rows for the same action id.

### 3.9.2 Event Detail Needs An Audit Link

`ClearedItemDetailModal` is supposed to show before/after audit data, but `document_priority_events` currently has no durable pointer to `audit_logs`.

Required correction:

- Add nullable `audit_log_id` (or `related_audit_log_id`) to `document_priority_events`.
- When a mutation writes both audit and priority-event rows, write audit first and store its id on the event.
- If legacy events lack an audit id, the detail endpoint may fall back to a best-effort lookup by `entity_id`, `actor_id`, and timestamp window, but the new contract should not depend on fuzzy matching.

### 3.9.3 E-Sign Status Taxonomy Mismatch

The current frontend and backend both classify sent documents with `signature_status === 'sent'`, but the e-sign send endpoint stores `signature_status='sent_for_signature'`. That means documents can appear in `Pending review` instead of `Sent for sig`, and voided/declined envelopes can lose their recovery affordance.

Required correction:

- Create one status normalizer used by both frontend helpers and backend queue logic:
  - `sent_for_signature`, `sent`, `delivered`, `pending` with an envelope id → sent/in-flight.
  - `signed`, `completed`, or `is_signed=true` → signed.
  - `voided`, `declined` → recoverable envelope state with **Resend** as the primary action.
  - `processed`/`pending` without an envelope → pending review.
- Update `_doc_status_for`, `getDocStatus`, tab counts, `hasInFlightEnvelope`, and row action rendering to use the same taxonomy.
- Send for Signature must block signed docs and in-flight docs (`sent_for_signature`, `sent`, `delivered`, `pending`) with clear copy.
- Voided/declined rows must offer `Resend`, not disappear from every workflow surface.

### 3.9.4 Download Means Download

The draft caught the popup-blocker bug in the Transaction Documents modal, but the same bug exists on the All Documents page: `handleDownload` awaits the signed URL and then calls `window.open`.

Required correction:

- Apply the pre-opened-tab pattern to every document download path, including `DocumentsPage.tsx`.
- Distinguish **Open in new tab** from **Download**. A button labeled Download should either:
  - call a backend endpoint that sets `Content-Disposition: attachment`, or
  - fetch the blob and click an `<a download>` object URL.
- Keep preview/open behavior as a separate affordance so PDFs do not merely open when the user asked to save.

### 3.9.5 Scope And Badge Contract

The companion plan already flagged this, but the workflow draft did not carry it forward strongly enough: the page currently mixes scopes.

Current risk:

- `dashboard_documents_priority_queue` builds queue items from active transactions in the user's personal/assigned scope.
- `useAllDocuments()` loads the broader accessible document corpus.
- `tab_counts.all_docs` uses a tenant-wide document count in the dashboard endpoint.

Required correction:

- Add an explicit workspace scope contract (`scope=personal|team|tenant`, with role gates) before adding more counts or filters.
- Include `scope` in the priority-queue query key and in any new cleared-events query key.
- Compute `items`, `tab_counts`, hero, briefing, and recently-done from the same scope the visible document list uses.
- For Team Lead/Admin, expose a visible scope toggle instead of silently mixing personal queue work with tenant-wide document counts.

### 3.9.6 Mutation Invalidation Is Not Fully Centralized

`useInvalidateDocumentsWorkspace()` exists, but several high-impact hooks still invalidate only document lists or single-document caches.

Required correction:

- Migrate upload, new version, update/reassign, delete, restore, approve/reject deletion, and all e-sign mutations to the shared invalidation helper.
- Add `QUERY_KEYS.DASHBOARD_DOCUMENTS_AI_BRIEFING` to the helper so the briefing does not stay stale after a clear.
- Include transaction-document query invalidation when the mutation has a `transaction_id`.
- Keep direct `refetchPriority()` calls as a UI nicety, not as the only correctness mechanism.

### 3.9.7 External Role Access And Portal Document Lists

The draft covers dedicated Client/FSBO/Vendor portal pages, but two route/API details need correction:

- `/documents` currently redirects non-internal roles to the dashboard with no explanation. That matches the current expected test result, but the revised workflow should add a role-aware toast or tiny redirect landing note: `Your documents live in your portal Documents page.` Then send Client/Vendor to `/client/documents` and FSBO to `/fsbo/documents`.
- The documented `/api/v1/client/documents` and `/api/v1/dashboard/fsbo/documents` endpoints are not implemented in the current backend. Either implement those aliases as documented, or reuse the existing role-scoped `GET /api/v1/documents` endpoint for the portal lists. Do not write frontend hooks against routes that do not exist.

### 3.9.8 Template Registry Should Not Live In A Router

The draft proposes `_template_registered(item_key)` shared by `documents.py` and `dashboard.py`, but `_TEMPLATE_RULES` currently lives inside `documents.py`. Importing router modules into each other is brittle.

Required correction:

- Move `_TEMPLATE_RULES`, `_template_registered`, required-field mapping, and `fix_route` mapping into a small service module, e.g. `app/services/document_template_registry.py`.
- Normalize item keys in that module so both `lead_paint_disclosure` and `missing:{tx_id}:lead_paint_disclosure` resolve to the same template key.
- Both the dashboard priority builder and the generate endpoint import this service module.

### 3.9.9 Edit Document Modal Data Flow

`RenameDocumentModal` is already titled `Edit Document` in the shipped code, so that part of the draft is stale. The remaining work is the action label, transaction selector, and backend hardening.

Required correction:

- Change the row menu label from `Rename / Reclassify` to `Edit Document...`.
- Pass the transaction list into `RenameDocumentModal` or give it a narrowly scoped transaction-picker hook. Do not make the modal guess from global page state.
- Disable transaction reassignment for signed docs and in-flight envelopes before submit; backend still returns 409 as authority.
- If the new transaction already has a current doc of the same type, MVP should offer `Keep both`; "make latest version" requires a separate version-chain endpoint.

### 3.9.10 Interactive Row Accessibility

`QueueRow` and `DocCard` currently render the whole row as `role="button"` while also containing nested buttons/dropdowns. That is fragile for keyboard and screen-reader users.

Required correction:

- Convert the row shell to a non-interactive `article`/`div`.
- Keep explicit `View Details`, `Preview`, `Open`, and action buttons as the actual interactive controls.
- If the body remains clickable for pointer users, do not expose it as a second keyboard button competing with the visible controls.
- Apply this to Recently Done cards, queue rows, and categorized document cards for consistency.

### 3.9.11 Archive And Restore Need A List Contract

The draft mentions a Restore Archived panel but only references the restore mutation. The UI also needs a way to list archived docs.

Required correction:

- Prefer reusing `GET /api/v1/documents?is_deleted=true&page=...&page_size=...` for the panel if it already satisfies role/scope rules.
- If the generic endpoint is insufficient, add `GET /api/v1/documents/archived`.
- Archive success should offer an immediate Undo toast for eligible docs, backed by `PUT /documents/{id}/restore`.
- Signed or envelope-linked documents require signed-aware archive copy and may need restore restrictions if external distribution has already happened.

### 3.9.12 DocuSign Connect Wizard Has Its Own Popup And Stack Issues

The draft focuses on Transaction Documents stacking, but `ConnectEsignWizardModal` also uses an arbitrary `z-[700]` and opens the DocuSign popup after awaiting the authorize-url request.

Required correction:

- Convert `ConnectEsignWizardModal` to the shared `Dialog` primitive or the same Radix stack used by other document modals.
- Pre-open a blank popup synchronously on the user's `Continue to DocuSign` click, then navigate it after `/integrations/docusign/authorize-url` resolves.
- If authorize-url fails, close the blank popup and keep the user in the wizard with retry copy.

### 3.9.13 Header Metric Semantics

The header currently reads `{signed} of {all_docs} complete`, but `signed` is not the same as document completion. Some valid documents may never be signed, and approved/generated/uploaded docs can be ready without being signed.

Required correction:

- Either relabel the metric to `signed` explicitly, or compute a real readiness count from signed + approved + accepted/current non-signature docs.
- Keep the chip consistent with tab counts; the user should not have to infer what "complete" means.

### 3.9.14 Deletion Notifications Need A Concrete Dispatcher

The draft says to "enqueue an email via the existing notification dispatcher." The repo has notifications surfaces and some notification inserts, but no clearly reusable generic email dispatcher for arbitrary notification rows.

Required correction:

- Create a small deletion-decision notification helper that inserts the in-app notification and sends email through the project's actual outbound path.
- If tenant email notifications are disabled or no provider is available, the in-app notification still inserts and the email skip is logged.
- Tests should assert both the notification row and the email-send/skip branch, not just that an audit row exists.

---

## 4. Workflow Discrepancies Found During Audit

Each item below is a concrete deviation from the design intent that we'll resolve as part of this work. File-line references point to the offending location today.

| # | Discrepancy | Where | Fix |
| --- | --- | --- | --- |
| 1 | Cleared Today strip is invisible on non-AI tabs | [DocumentsPage.tsx:1501-1519](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1501-L1519) | Hoist render out of the `ai_priority` branch; show on every tab (§2.3). |
| 2 | Mark-N/A card click fires a toast instead of opening detail | [DocumentsPage.tsx:1504-1517](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1504-L1517) | Replace with `View Details` / `Open` buttons + `ClearedItemDetailModal` (§2.4). |
| 3 | Whole-card click target violates the card-clickability rule | [DocumentsPage.tsx:3087-3122](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3087-L3122) | Split into explicit buttons (§2.4). |
| 4 | Rename modal omits transaction picker even though backend supports it | [RenameDocumentModal.tsx:68-122](velvet-elves-frontend/src/components/documents/RenameDocumentModal.tsx#L68-L122) | Add transaction `Combobox` (§3.2A). |
| 5 | Edit/Rename entry hidden in More menu and only on non-AI tabs | [DocumentsPage.tsx:3489-3493](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3489-L3493) | Expose from AI Priority / Missing rows via QueueRow more-menu + Priority Detail Modal alt-actions (§3.2C). |
| 6 | Uploads that satisfy a missing requirement do not reliably write a `clear` priority event | [documents.py:392-487](velvet-elves-backend/app/api/v1/documents.py#L392-L487) creates the document and audit row but no `document_priority_events` row; the frontend upload prefill also does not pass the originating `item_key` | Add `priority_item_key`/`doc_label` context to the upload flow, log `event_type='clear'`, `action_key='upload'` only when the upload actually satisfies a missing item, and keep the existing `upload → Uploaded` badge mapping. |
| 7 | No Undo path for Approve / Generated / Uploaded clears | [DocumentsPage.tsx:1059-1074](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1059-L1074) | Wire badge-aware Undo on each card (§2.5). |
| 8 | Soft-deleted documents leave no restore-archived path | (Not present in UI) | Add a `Restore archived` panel toggle from the More menu next to the existing `Deletion Queue` button (read uses existing `PUT /documents/{id}/restore` at [documents.py:677](velvet-elves-backend/app/api/v1/documents.py#L677)). |
| 9 | No bulk actions on Missing items | [DocumentsPage.tsx:1523-1545](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1523-L1545) | Multi-select checkboxes on Missing tab + a bulk action bar with `Mark N/A`, `Request`, and `Upload/Assign`. Do **not** offer `Reassign` on Missing rows because they have no `document_id`; reassign belongs to existing-document rows only. |
| 10 | Strip count limited to 8 with no way to see more | [dashboard.py:1591](velvet-elves-backend/app/api/v1/dashboard.py#L1591) | Add `View all cleared (last 7 days)` side sheet (§2.7). |
| 11 | Strip has no actor filter | (Not present in API) | Add `?cleared_actor_scope=all|me|team` for `recently_done` / cleared-event rows only (§2.6). |
| 12 | Reassign emits no priority/audit event that the strip can explain | (Not present in API) | Write `reassign_out` touch events for the source transaction and `reassign` clear events only when the destination move satisfies a missing requirement (§3.3). |
| 13 | `feedback_alert_card_clickability` rule not applied to recently-done cards | [DocumentsPage.tsx:3087-3122](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3087-L3122) | Explicit View Details + Open buttons + role-aware badge — see §2.4. |
| 14 | Edit Document menu surfaces on `signed` docs without warning the signature chain | (Not present in modal) | Modal disables the transaction picker when an in-flight or signed envelope exists; tooltip explains why (§3.4). |
| 15 | `_doc_snapshot` includes `transaction_id` today, but the plan had it as unknown | [documents.py:_doc_snapshot](velvet-elves-backend/app/api/v1/documents.py) | Keep the field and add a regression test so reassign audit diffs cannot lose it (§3.3). |
| 16 | `Generate` button offered for requirements the system has no template for | [dashboard.py:1052-1059](velvet-elves-backend/app/api/v1/dashboard.py#L1052-L1059) — `appraisal_report` lists `template` in `alt_actions` even though `_TEMPLATE_RULES` has no `appraisal_report` entry | Filter `template` out of `alt_actions`/`suggested_action` when `item_key not in _TEMPLATE_RULES` (§3.5.2A). |
| 17 | `Generate` failure modal mixes two failure modes under one status and one dead-end button | [DocumentsPage.tsx:2066-2110](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L2066-L2110) + [documents.py:1857-1888](velvet-elves-backend/app/api/v1/documents.py#L1857-L1888) | Split backend status into `no_template` vs `missing_fields`; split frontend modal into two intent-specific surfaces with real Upload/Request CTAs (§3.5.2B + §3.5.3A). |
| 18 | Missing-fields modal lists raw machine field names with no deep link to fix them | [DocumentsPage.tsx:2081-2097](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L2081-L2097) | Hide raw field names; add `fix_route` to each row from the backend; render a `Fix →` button per row that deep-links to the parties/overview tab with `?focus_missing=` highlight, with inline edit for safe transaction fields (§3.5.2C + §3.5.3B-D). |
| 19 | Sort dropdown is a no-op on All Docs / Pending review / Sent for sig / Signed | `CategorizedView` props at [DocumentsPage.tsx:3149-3167](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3149-L3167) — no `sort` prop passed; `filtered` `useMemo` at [DocumentsPage.tsx:3171-3186](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3171-L3186) never sorts | Extract `sortPriorityItems` / `sortUploadedDocs` helpers; pass `sort` and `txById` into `CategorizedView`; apply `sortUploadedDocs` after the tab filter; show fallback caption when `ai_impact`/`last_touched` are picked on categorized tabs (§3.6.3). |
| 20 | Transaction Documents modal renders every child modal invisibly behind its own backdrop | Parent overlay at [DocumentsModal.tsx:541](velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx#L541) uses `z-[600]`; Radix children render at `z-50` and lose | Replace hand-rolled overlay with Radix `Sheet`/`Dialog` so parent and children share the same `z-50` stack (§3.8.3). |
| 21 | Transaction Documents Download button is blocked by browser popup blockers | `handleDownload` at [DocumentsModal.tsx:508-519](velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx#L508-L519) calls `window.open` after an `await` | Pre-create the new tab synchronously in the click handler; navigate it once the signed URL resolves (§3.8.2). |
| 22 | Transaction Documents modal has no Send for Signature, Sync, or Void affordance | [DocumentsModal.tsx:629-695](velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx#L629-L695) | Wire the existing `useSendForSignature`, `useSyncEsignStatus`, `useVoidEsign` hooks into the action row (§3.8.4 #1, #4). |
| 23 | Transaction Documents modal has no in-modal preview — every view is a tab open | [DocumentsModal.tsx:615-621](velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx#L615-L621) — doc-name click calls `handleDownload` | Reuse the All-Documents preview modal here; only fall back to a new tab if the file type can't be previewed (§3.8.4 #2). |
| 24 | Transaction Documents modal has no filter/sort/search inside the list | (Not present) | Reuse `sortUploadedDocs` from §3.6.3B; add a small status filter chip row for `Uploaded / Awaiting / Signed / Flagged` (§3.8.4 #3). |
| 25 | Transaction Documents modal has no internal follow-up flag — `Flag` here only means deletion request | [DocumentsModal.tsx:683-693](velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx#L683-L693) | Add a separate `Mark for follow-up` action in the More menu when `isInternal`, wired to the `document_followup_flags` endpoints from the companion plan (§3.8.4 #7). |
| 26 | Transaction Documents modal has no focus trap, no Escape handler, no `role="dialog"`/`aria-modal` | Hand-rolled overlay at [DocumentsModal.tsx:540-547](velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx#L540-L547) | Resolved by the Radix conversion in §3.8.3. |
| 27 | External users cannot reach `Flag for deletion` from their dedicated portal documents pages | [ClientDocumentsPage.tsx](velvet-elves-frontend/src/pages/client/ClientDocumentsPage.tsx) (summary stub), [FsboDocumentsPage.tsx:30](velvet-elves-frontend/src/pages/fsbo/FsboDocumentsPage.tsx#L30) (placeholder telling users to click a button that doesn't exist) | Replace stubs with real per-document lists backed by the role-scoped `GET /documents` endpoint, or add thin aliases for `GET /client/documents` and `GET /dashboard/fsbo/documents` in the same slice; expose Flag entry per row (§3.7.2A). |
| 28 | `Deletion Queue` header button has no pending-count badge and shows even when count is zero | [DocumentsPage.tsx:1393-1403](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1393-L1403) | New `GET /documents/flagged/count` endpoint; `useFlaggedDocumentsCount()` hook; render badge when `> 0`, hide button when `= 0` (§3.7.2B). |
| 29 | Approve / Reject of a deletion request never notifies the requester | [documents.py:1318, 1353](velvet-elves-backend/app/api/v1/documents.py#L1318) — audit log only; no notification, no email | On both endpoints, call a deletion-decision notification helper that inserts the `notifications` row and sends or explicitly skips email through the project's actual outbound path (§3.7.2C, §3.9.14). |
| 30 | `Approve` is destructive but takes no confirmation step | [DeletionApprovalsPanel.tsx:29-43](velvet-elves-frontend/src/components/documents/DeletionApprovalsPanel.tsx#L29-L43) | Wrap in Radix `AlertDialog` with signed-document-aware copy; make Reject reason a required field (§3.7.2D). |
| 31 | Deletion-review surface lives on the AI-led page header — conflicts with the page's identity | [DocumentsPage.tsx:1393-1403](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1393-L1403); Jake's redesign drops it entirely | Emit deletion-flag rows as priority items (`kind='deletion_review'`, `suggested_action='review_deletion'`); remove the header button once that path lands (§3.7.2E). |
| 32 | Signed, voided, replaced, and uploaded resolution paths do not consistently write `clear` events | `documents.py` upload/versioning and `esign.py` completion/void paths | Add the shared resolution-event helper from §3.9.1 and cover each path in tests. |
| 33 | Sent-for-signature status normalization is wrong | `getDocStatus` and `_doc_status_for` check `signature_status === 'sent'`, while e-sign send stores `sent_for_signature` | Add a shared status taxonomy that treats `sent_for_signature` / `sent` / `delivered` / envelope `pending` as in-flight, and treats `voided` / `declined` as recoverable states with Resend (§3.9.3). |
| 34 | All Documents Download has the same popup-blocker bug as Transaction Documents | [DocumentsPage.tsx:733-734](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L733-L734) awaits a signed URL then calls `window.open` | Pre-open the tab synchronously or fetch a blob with `<a download>`; apply to every document download path (§3.9.4). |
| 35 | Download buttons may open previews instead of saving files | Current download flows open signed URLs in a new tab | Split `Open` from `Download`; implement attachment semantics for Download (§3.9.4). |
| 36 | Page scope and tab counts are mixed | Priority queue is built from active personal/assigned transactions while `all_docs` counts tenant documents and `useAllDocuments()` loads a broader corpus | Add explicit `scope` and compute queue, counts, hero, briefing, and strip from the same visible corpus (§3.9.5). |
| 37 | Shared invalidation helper exists but key mutations bypass it | Upload/update/delete/restore/e-sign hooks still invalidate partial caches | Migrate all document/e-sign mutations to `invalidateDocumentsWorkspace()` and include the documents AI briefing key (§3.9.6). |
| 38 | External portal plan references endpoints that are documented but not implemented | `/api/v1/client/documents` and `/api/v1/dashboard/fsbo/documents` do not exist in current backend | Either implement documented aliases or reuse role-scoped `GET /api/v1/documents`; do not create frontend hooks against missing routes (§3.9.7). |
| 39 | Template registry sharing would create router coupling | `_TEMPLATE_RULES` currently lives in `documents.py`, but dashboard also needs the registry | Move template rules to `app/services/document_template_registry.py` and normalize item keys there (§3.9.8). |
| 40 | `QueueRow` and `DocCard` use row-level `role="button"` around nested buttons | [DocumentsPage.tsx:2491+](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L2491), [DocumentsPage.tsx:3342+](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L3342) | Convert row shells to non-interactive containers and expose explicit Preview / View Details / action buttons (§3.9.10). |
| 41 | Restore Archived panel lacks a list contract | The plan only references `PUT /documents/{id}/restore` | Use `GET /documents?is_deleted=true` or add `GET /documents/archived` for the panel (§3.9.11). |
| 42 | Connect DocuSign wizard uses arbitrary `z-[700]` and opens the popup after awaiting an authorize URL | [ConnectEsignWizardModal.tsx](velvet-elves-frontend/src/components/documents/ConnectEsignWizardModal.tsx) | Convert to shared Dialog stack and pre-open the OAuth popup synchronously (§3.9.12). |
| 43 | Header says `{signed} of {all_docs} complete`, but signed is not equivalent to complete | [DocumentsPage.tsx:1374-1376](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1374-L1376) | Rename the metric to signed or compute a real readiness count (§3.9.13). |
| 44 | `ClearedItemDetailModal` needs audit before/after data, but priority events have no audit id | `document_priority_events` schema/repository | Add nullable `audit_log_id` and write audit first when a mutation logs both audit and priority events (§3.9.2). |
| 45 | `/documents` redirects external users without a helpful handoff | [DocumentsPage.tsx:320-326](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L320-L326) | Keep the internal-only route, but add a role-aware note/toast and redirect to the correct portal documents page (§3.9.7). |

---

## 5. Data Model Changes

Most of the work fits the existing structures the companion plan already laid out (`document_priority_waivers`, `document_followup_flags`, `document_priority_events`, document `review_status` columns). The review adds a few concrete contract details:

### 5.1 Resolution Event Keys And Reversal Keys

No schema change is needed for new action keys because `document_priority_events` already supports any `action_key` string. Adopt these documented conventions and add them to the migration/table comment:

- Clear actions: `upload`, `template`, `approve`, `waive`, `signed`, `replace`, `void`, `reassign`.
- Touch/recovery actions: `request`, `nudge`, `forward`, `call`, `flag`, `reassign_out`, `resend`.
- Reversal actions: `unwaive`, `unapprove`, `delete_generated`, `archive_uploaded`, `restore_uploaded`.

The strip reads clear actions after applying later reversal actions. It must not delete history rows.

### 5.2 Approve Reversal

Add an explicit `unapprove` endpoint to flip `review_status` back to `unreviewed`:

```text
POST /api/v1/documents/{id}/review/unapprove
```

Behavior:

- Sets `review_status='unreviewed'`, clears `reviewed_by`, `reviewed_at`, `review_note`.
- Inserts an audit row.
- Inserts a priority event `event_type='unclear'`, `action_key='unapprove'`. Do not delete the matching `approve` clear event; the original clear and later reversal must both remain in the audit chain, and `recently_done` should suppress or mark the original clear by reading the reversal event.
- Required so the badge-aware Undo (§2.5) has a real backend path.

### 5.3 Strip Pagination Schema

The new "View all cleared (7 days)" sheet needs a paginated endpoint:

```text
GET /api/v1/dashboard/documents-priority-queue/cleared
  ?window_hours=168
  &cleared_actor_scope=all|me|team
  &limit=25
  &cursor=<opaque>
```

Returns `{ items: DocumentRecentlyDone[], next_cursor: string | null }`. Implemented on top of the existing `event_repo.list_recent_clears` with a wider hour window and a cursor-friendly index. Tenant filter is mandatory; non-internal roles return 403.

### 5.4 Priority Event Audit Link

Add nullable `audit_log_id` (or `related_audit_log_id`) to `document_priority_events` so the cleared-item detail endpoint can show reliable before/after audit data.

Index:

```sql
CREATE INDEX IF NOT EXISTS idx_document_priority_events_audit
  ON document_priority_events (tenant_id, audit_log_id)
  WHERE audit_log_id IS NOT NULL;
```

Backfill is optional. Legacy events may fall back to best-effort audit lookup, but all new mutating endpoints should write audit first and store the audit id on the event.

---

## 6. Endpoint Catalogue Updates

| Endpoint | Method | Purpose | Notes |
| --- | --- | --- | --- |
| `/api/v1/documents/{id}` | PATCH | Existing — already accepts `transaction_id` | `_doc_snapshot` already includes `transaction_id`; keep it and test it. Add reassign event semantics from §3.3. |
| `/api/v1/documents/{id}/review/unapprove` | POST | New — reverse an approval | Internal roles only; emits `unapprove` event. |
| `/api/v1/dashboard/documents-priority-queue` | GET | Existing | Add `scope=personal|team|tenant` and `cleared_actor_scope=all|me|team` query params. Keep actor filtering scoped to `recently_done`; it must not filter active queue items by actor. |
| `/api/v1/dashboard/documents-priority-queue/cleared` | GET | New — paginated cleared list for the 7-day sheet | Cursor pagination, tenant scope. |
| `/api/v1/documents/priority-events/{event_id}` | GET | New — read-only event detail | Powers the `ClearedItemDetailModal`. Returns the event row + linked audit row via `audit_log_id` + minimum doc info. |
| `/api/v1/documents/generate-from-template` | POST | Existing — response contract widens | Response status splits into `generated` / `missing_fields` / `no_template`; missing-field rows gain a `fix_route` discriminated union (§3.5.2B-C). |
| `/api/v1/dashboard/documents-priority-queue` | GET | Existing | Filter `template` from `alt_actions`/`suggested_action` when the item's template is unregistered (§3.5.2A). |
| `/api/v1/transactions/{id}` | PATCH | Existing | Used by the inline-fix input for safe transaction fields (`purchase_price`, `title_company`). No backend change. |
| `/api/v1/documents/flagged/count` | GET | New — pending deletion-request count | Cheap COUNT(*); 30s server-side cache; internal roles only; powers the header-button badge in §3.7.2B. |
| `/api/v1/documents/{id}/approve-deletion` | POST | Existing — gains notification side effect | Call the deletion-decision notification helper for `deletion_flagged_by`; block with 409 `envelope_in_flight` when document has an in-flight envelope (§3.7.2C + §3.7.3 + §3.9.14). |
| `/api/v1/documents/{id}/reject-deletion` | POST | Existing — gains notification side effect + required reason | Call the same helper; require `reason` in the request body (≥3 chars) — return 422 if missing (§3.7.2D + §3.7.3 + §3.9.14). |
| `/api/v1/documents?is_deleted=true` or `/api/v1/documents/archived` | GET | Existing generic list or new alias — archived document list | Powers `RestoreArchivedPanel`; use the generic endpoint if it satisfies role/scope rules. |
| `/api/v1/client/documents` | GET | New alias or replace with existing `GET /api/v1/documents` | Product docs mention this route, but current backend does not implement it. Either add the alias or point `ClientDocumentsPage` at the role-scoped generic documents endpoint. |
| `/api/v1/dashboard/fsbo/documents` | GET | New alias or replace with existing `GET /api/v1/documents` | Same correction for `FsboDocumentsPage`; do not ship a hook against a missing route. |
| `/api/v1/dashboard/documents-priority-queue` | GET | Existing — adds new item kind | Emit deletion-flag rows as `kind='deletion_review'` priority items so the work appears in the AI queue (§3.7.2E). |

For each: keep tenant + role gates consistent with the existing handlers, and instrument every new endpoint with an `AuditService` call where it mutates state.

---

## 7. Frontend Work

### 7.1 Component Changes

| Component | File | Change |
| --- | --- | --- |
| `RecentlyDoneStrip` | DocumentsPage.tsx ~3046 | Header gets subtitle + info popover; cards switch to explicit-button footer; supports `actorScope`, per-card Undo. |
| New `ClearedItemDetailModal` | new file under `src/components/documents/` | Read-only detail of a clear event + audit linkage. Reused by all card `View Details` clicks. |
| `RenameDocumentModal` | RenameDocumentModal.tsx | Title is already `Edit Document`; add transaction `Combobox`, visual section grouping, signed/in-flight reassign guard, and a transaction-list prop/hook. |
| `DocCard` | DocumentsPage.tsx ~3236 | More-menu label `Rename / Reclassify` → `Edit Document…`. |
| `QueueRow` | DocumentsPage.tsx ~2491 | Add a small more-menu trigger to the right of alt-actions; only renders when `document_id` is set; offers `Edit Document` (internal roles). |
| `PriorityDetailModal` | DocumentsPage.tsx | Add `Edit Document` to the alt-actions list when `document_id` is set. |
| New `RestoreArchivedPanel` | new file under `src/components/documents/` | Drawer reachable from the page header's More menu next to `Deletion Queue`. Lists soft-deleted documents from the last 90 days, calls existing `PUT /documents/{id}/restore`. |
| New `ClearedAllSheet` | new file under `src/components/documents/` | 7-day paginated cleared-events sheet (§2.7). |
| New `BulkActionsBar` | embedded inside `DocumentsPage.tsx` | Renders when ≥1 Missing row is selected; offers Mark N/A, Request, and Upload/Assign. Reassign is deliberately excluded here because Missing rows do not have a document to move. |
| New `TemplateNotAvailableModal` | new file under `src/components/documents/` | Replaces today's single-button "no template" dead end. Surfaces real Upload / Request CTAs derived from the backend's `suggested_alternatives` (§3.5.3A). |
| New `TemplateMissingFieldsModal` | new file under `src/components/documents/` | Replaces today's mixed-purpose modal for the `missing_fields` path. Renders human labels only, with a `Fix →` button per row that deep-links to the transaction's parties/overview tab or edits the field inline (§3.5.3A-B). |
| Existing `templateMissing` modal at DocumentsPage.tsx ~2066 | DocumentsPage.tsx | Removed — replaced by the two split modals above. The `templateMissing` state in `DocumentsPage` becomes a discriminated union `{ kind: "no_template" \| "missing_fields", ... }`. |
| New `src/utils/documentsSort.ts` helper | new file under `src/utils/` | Exports `sortPriorityItems(items, sort)` and `sortUploadedDocs(docs, sort, txById)`. Single source of truth for sort behavior across the AI Priority / Missing path and the categorized path (§3.6.3B). |
| New `src/utils/documentStatus.ts` helper | new file under `src/utils/` | Normalizes document/e-sign state for tabs and row actions (`sent_for_signature`, `delivered`, `voided`, `declined`, etc.) so frontend behavior matches backend queue logic (§3.9.3). |
| `CategorizedView` | DocumentsPage.tsx ~3131 | Accept `sort: DocSortKey` and `txById: Map<string, Transaction>` props; apply `sortUploadedDocs(filtered, sort, txById)` after the tab filter (§3.6.3A + §3.6.3C). |
| `DocFilterTabs` | DocumentsPage.tsx ~2169 | Render a one-line caption under the sort chip when `activeTab` is a categorized tab and the active sort key falls back (`ai_impact` / `last_touched`) — e.g. `Sorted by Recently updated on this tab.` (§3.6.3D). |
| `DocumentsModal` (Transaction Documents) | [DocumentsModal.tsx](velvet-elves-frontend/src/components/active-transactions/DocumentsModal.tsx) | Convert hand-rolled overlay to Radix `Sheet`/`Dialog`; pre-open the download tab synchronously; add Send for Signature / Sync / Void buttons next to the existing icon row; replace doc-name click with the All-Documents preview modal; add status filter chips + sort dropdown using `sortUploadedDocs`; add `Mark for follow-up` to the More menu when internal; add Restore Archived entry point (§3.8). |
| `ClientDocumentsPage` | [ClientDocumentsPage.tsx](velvet-elves-frontend/src/pages/client/ClientDocumentsPage.tsx) | Replace count-summary stub with a real per-document list backed by either the existing role-scoped `GET /documents` endpoint or a newly implemented `GET /client/documents` alias; expose `Flag for deletion` per row via existing `FlagForDeletionModal` (§3.7.2A, §3.9.7). |
| `FsboDocumentsPage` | [FsboDocumentsPage.tsx](velvet-elves-frontend/src/pages/fsbo/FsboDocumentsPage.tsx) | Replace placeholder columns with a real per-document list backed by role-scoped `GET /documents` or a newly implemented `GET /dashboard/fsbo/documents` alias; expose `Flag for deletion` per row (§3.7.2A, §3.9.7). |
| `VendorDocumentPortalPage` | `src/pages/vendor/VendorDocumentPortalPage.tsx` | Same as the FSBO/Client treatment using the vendor-scoped generic endpoint or an implemented alias (§3.7.2A, §3.9.7). |
| `ConnectEsignWizardModal` | [ConnectEsignWizardModal.tsx](velvet-elves-frontend/src/components/documents/ConnectEsignWizardModal.tsx) | Convert arbitrary `z-[700]` overlay to shared Dialog stack; pre-open OAuth popup synchronously before fetching authorize URL (§3.9.12). |
| Deletion Queue button | [DocumentsPage.tsx:1393-1403](velvet-elves-frontend/src/pages/documents/DocumentsPage.tsx#L1393-L1403) | Add pending-count badge; hide entirely when count is 0. Bridge until §3.7.2E removes the button (§3.7.2B). |
| `DeletionApprovalsPanel` | [DeletionApprovalsPanel.tsx](velvet-elves-frontend/src/components/documents/DeletionApprovalsPanel.tsx) | Wrap Approve in a Radix `AlertDialog` confirm with signed-document-aware copy; mark Reject reason as required; surface the reviewer's reason in the toast and the notification (§3.7.2D). |

### 7.2 New Hooks

- `useUnapproveDocumentReview()` — POST `/documents/{id}/review/unapprove`.
- `useClearedEventsPage(cursor, scope)` — paginated 7-day list.
- `useClearedEventDetail(eventId)` — read-only event detail for the modal.
- `useReassignDocument()` — thin wrapper over `useUpdateDocument` that only sends `transaction_id` and any optional rename fields; used by existing-document rows and any future bulk-reassign surface, not by Missing-row bulk actions.
- `useRestoreArchivedDocument()` — existing endpoint hook if missing.
- `useUpdateTransactionField(transactionId)` — thin wrapper over the existing `PATCH /transactions/{id}` for the inline-fix input inside the missing-fields modal; scoped to safe fields only.
- `useFlaggedDocumentsCount()` — lightweight polled count for the Deletion Queue badge (§3.7.2B).
- `useClientDocumentsList()` — paginated list backing the new `ClientDocumentsPage` real-list view; use role-scoped `GET /documents` unless a `/client/documents` alias is implemented (§3.7.2A, §3.9.7).
- `useFsboDocumentsList()` — same for `FsboDocumentsPage`; use role-scoped `GET /documents` unless a `/dashboard/fsbo/documents` alias is implemented (§3.7.2A, §3.9.7).
- `useDocumentStatusNormalizer()` is not needed as a hook; implement the e-sign status taxonomy as a pure helper shared by row rendering, tabs, and tests (§3.9.3).

These hooks live in `src/hooks/useDocuments.ts` (or, for e-signature-specific hooks, `src/hooks/useEsign.ts`) and use the shared `invalidateDocumentsWorkspace()` helper described in the companion plan §5 so the priority queue, all-docs list, transaction-doc lists, audit-log views, and the strip refresh consistently.

### 7.3 URL State

Extend the existing `?tab=` and `?sort=` query state with:

- `?scope=personal|team|tenant` — controls the visible workspace corpus for roles allowed to switch scope; query keys must include it.
- `?cleared_scope=all|me|team` — applies to the strip and the 7-day sheet.
- `?sheet=cleared-all` — opens the 7-day sheet on load (lets a notification or deep link send the user straight there).
- `?edit=<document_id>` — opens the `Edit Document` modal pre-loaded for the doc. Used for deep links from the Cleared modal, audit log, and Cmd+K results.
- `?retry_template=<item_key>` — set automatically when the missing-fields modal sends the user to a transaction's parties/overview tab. On return, the page silently re-fires Generate for that item and either renders the new draft preview or replaces the modal with the next missing-fields state.
- `?focus_missing=<field_or_role>` — accepted by the transaction detail page; scrolls to and flashes the matching row using the existing `search-focus-flash` style.

### 7.4 Accessibility

- The new `ClearedItemDetailModal`, `ClearedAllSheet`, and updated `RenameDocumentModal` use the existing `Dialog` / `Sheet` primitives with built-in focus trap and Escape.
- The strip's per-card buttons must be reachable via Tab in DOM order: `Open`, `View Details`, `Undo`.
- Queue rows and document cards must not expose a row-level `role="button"` that wraps nested buttons/dropdowns. Use explicit controls for keyboard users.
- `aria-label` on every icon-only button (Undo, ellipsis menus).
- Tooltip-only info on the strip header must also be reachable on focus (use Radix `HoverCard`, which is focus-aware).
- The bulk-actions bar must announce its presence via `role="region" aria-live="polite"` so screen-reader users hear "3 items selected" after toggling a checkbox.

### 7.5 Copy Rules

- Strip subtitle: `Documents resolved in the last 24 hours — uploaded, signed, approved, generated, replaced, voided, or marked N/A.`
- Strip empty state on AI Priority: `Nothing cleared in the last 24 hours yet.`
- Strip empty state on non-AI tabs: hide entirely.
- Reassign confirmation banner: `Moving this document will reattach the audit history and version chain to the new transaction. Signed or in-flight envelopes cannot be moved.`
- Approve undo toast: `Undid: Approved {label}. Back in review queue.`
- All toast copy follows the existing pattern: present-tense start (`Reassigning…`), past-tense end (`Reassigned to {address}`).
- First-person singular (`I` not `we`) only applies to client-facing email/SMS drafts, not internal toasts (see memory `feedback_first_person_singular`).

---

## 8. Backend Work

### 8.1 Dashboard Endpoint

- Accept `cleared_actor_scope` query param. Default `all`. `me` filters cleared-event rows to `actor_id = current_user.id`. `team` filters cleared-event rows to internal teammates of the same tenant minus `current_user.id`. This parameter must not filter the active priority queue.
- Ensure `recently_done` rows include `actor_id` and a derived `actor_name` so the strip can show "Cleared by Jane".
- Keep the existing `upload` mapping in `_via_action_from_event`, and add the missing upload-side `clear` event so uploads that satisfied a requirement actually reach the strip.

### 8.2 New Endpoints

- `POST /documents/{id}/review/unapprove` — see §5.2.
- `GET /dashboard/documents-priority-queue/cleared` — see §5.3.
- `GET /documents/priority-events/{event_id}` — joined read of the event + audit row + minimal document/transaction info. Requires tenant + role gate identical to the dashboard endpoint.

### 8.3 PATCH /documents Hardening

- Keep `_doc_snapshot.transaction_id` in place and test it so reassignments continue to show up as a diff in audit logs.
- When `transaction_id` changes:
  - Fire a `touch` priority event for the **old** transaction (`action_key='reassign_out'`) and a destination-side `clear` event (`action_key='reassign'`) only when the move resolves a missing requirement on the new transaction.
  - Block the change when any envelope on that document has status in `('sent', 'delivered')` or the doc `is_signed=true`; return a 409 with a structured error code `envelope_in_flight`. Frontend surfaces this as the §3.4 modal warning.

### 8.4 Restore Endpoint Surface

`PUT /documents/{id}/restore` already exists; just ensure it returns the restored doc as `DocumentResponse` so the React Query cache can swap it in without a refetch.

### 8.4.1 E-Sign Status And Resolution Events

- Normalize signature states across `esign.py`, `dashboard.py`, and frontend helpers: `sent_for_signature`, `sent`, `delivered`, and envelope `pending` are in-flight; `voided` and `declined` are recoverable; `signed`/`completed` are complete.
- In `_apply_envelope_event`, log a signed `clear` event after the signed version is stored.
- In `void_envelope`, log the correct recovery event and keep enough state for the UI to offer Resend.
- `send_for_signature` must block already-signed docs and all in-flight signature states, not only the subset currently checked.

### 8.5 Tenant Scope And RLS

Every new endpoint must:

- Pass through `require_internal_role` (or equivalent) for read access.
- Reuse `_validate_internal_transaction_access` when accepting any `transaction_id` body field.
- Use the existing tenant repo filters and the RLS policies defined in the multi-tenancy implementation plan.
- Be covered by a tenant-isolation test in the integration test suite (real Postgres, not mocked supabase).

### 8.6 Background AI

No new model calls in this plan. The strip never blocks on AI; the existing background note enrichment from the companion plan handles AI text. New endpoints are pure SQL joins.

### 8.7 Template Generation Hardening

- Move `_TEMPLATE_RULES` into `app/services/document_template_registry.py` and expose `template_registered(item_key: str)`, `normalize_template_item_key(item_key: str)`, and missing-field `fix_route` helpers. Both the dashboard priority-queue builder and the generate endpoint import this service module.
- In the dashboard priority-queue builder, drop `template` from `alt_actions` when `_template_registered(item_key)` is `False`. If `suggested_action == "template"` for an unregistered item, demote it to the next-best action available on that requirement (typically `request` or `upload`).
- Split the generate endpoint response shape into a discriminated union (`generated` / `missing_fields` / `no_template`); add `suggested_alternatives: list[str]` to the `no_template` branch and `fix_route` to each entry under `missing_fields` (§3.5.2B-C).
- Update the OpenAPI schema and the existing backend test `test_template_generation_creates_draft_or_missing_fields_response` to assert the new contract.

---

## 9. Test Plan

### Backend

- `test_strip_cleared_actor_scope_all_returns_tenant_clears`
- `test_strip_cleared_actor_scope_me_filters_to_actor_id`
- `test_strip_cleared_actor_scope_team_excludes_actor`
- `test_upload_event_returns_uploaded_via_action`
- `test_upload_from_missing_item_logs_clear_event_with_priority_item_key`
- `test_header_upload_without_priority_item_key_does_not_log_clear_event`
- `test_signed_envelope_completion_logs_signed_clear_event`
- `test_void_envelope_logs_recovery_event_and_preserves_resend_path`
- `test_replace_version_logs_replace_clear_event_when_launched_from_queue`
- `test_recently_done_suppresses_clear_events_reversed_by_later_unclear_event`
- `test_unapprove_restores_review_status_and_logs_event`
- `test_reassign_blocks_when_envelope_in_flight`
- `test_reassign_fires_touch_event_on_old_transaction`
- `test_reassign_fires_clear_event_only_when_destination_requirement_is_satisfied`
- `test_reassign_audit_diff_includes_transaction_id`
- `test_priority_event_stores_audit_log_id_for_detail_view`
- `test_document_status_normalizer_treats_sent_for_signature_as_in_flight`
- `test_document_status_normalizer_treats_voided_and_declined_as_recoverable`
- `test_priority_queue_scope_counts_match_visible_documents_scope`
- `test_cleared_seven_day_endpoint_paginates_with_cursor`
- `test_cleared_seven_day_endpoint_denies_external_roles`
- `test_priority_event_detail_returns_audit_link`
- `test_priority_event_detail_denies_cross_tenant_access`
- `test_priority_queue_filters_template_action_for_unregistered_item_keys`
- `test_priority_queue_demotes_template_suggested_action_when_unregistered`
- `test_generate_returns_no_template_status_when_item_key_unregistered`
- `test_generate_no_template_response_includes_suggested_alternatives`
- `test_generate_missing_fields_response_includes_fix_route_per_field`
- `test_generate_missing_fields_fix_route_party_seller_resolves_to_parties_tab`
- `test_flagged_count_endpoint_returns_pending_count_for_tenant`
- `test_flagged_count_endpoint_denies_external_roles`
- `test_approve_deletion_inserts_notification_for_requester`
- `test_approve_deletion_enqueues_email_for_requester`
- `test_approve_deletion_blocks_when_envelope_in_flight_with_409`
- `test_reject_deletion_requires_reason_returns_422_when_missing`
- `test_reject_deletion_includes_reviewer_reason_in_notification`
- `test_concurrent_approve_returns_409_already_decided`
- `test_priority_queue_emits_deletion_review_items_for_flagged_docs`
- `test_priority_queue_deletion_review_severity_is_critical_for_signed_docs`

### Frontend (Vitest + RTL)

- `RecentlyDoneStrip renders on every tab when items present`
- `RecentlyDoneStrip Mark N/A card opens detail modal, not toast`
- `RecentlyDoneStrip card View Details button focuses inside modal on open`
- `RecentlyDoneStrip Open button preview falls back to transaction docs when document_id null`
- `RecentlyDoneStrip Undo on approve calls unapprove endpoint`
- `RecentlyDoneStrip cleared actor scope filter changes URL and refetches recently_done only`
- `RecentlyDoneStrip hides or marks undone clear events after reversal`
- `Edit Document modal renders transaction selector for internal roles`
- `Edit Document modal blocks reassign when envelope is in flight (server 409)`
- `QueueRow more-menu shows Edit Document only when document_id is set`
- `PriorityDetailModal exposes Edit Document in alt actions`
- `RestoreArchivedPanel lists soft-deleted documents and restores`
- `BulkActionsBar appears on multi-select on Missing tab without offering Reassign`
- `Upload from Missing row sends priority_item_key and doc label context`
- `All Documents download pre-opens a new tab synchronously or uses blob download`
- `Download button uses attachment semantics while Open uses preview/new tab semantics`
- `documentStatus normalizes sent_for_signature into Sent for sig tab`
- `documentStatus exposes voided and declined rows with Resend action`
- `QueueRow and DocCard do not expose a row-level role=button around nested controls`
- `ConnectEsignWizardModal pre-opens OAuth popup before fetching authorize URL`
- `ConnectEsignWizardModal uses shared Dialog stack without z-[700]`
- `Header metric labels signed vs ready documents accurately`
- `Generate alt action is absent on rows whose item_key has no template registered`
- `TemplateNotAvailableModal renders Upload and Request CTAs from suggested_alternatives`
- `TemplateMissingFieldsModal hides raw machine field names and shows Fix buttons per row`
- `TemplateMissingFieldsModal inline-edits purchase_price and title_company without leaving the page`
- `TemplateMissingFieldsModal deep link to parties tab passes focus_missing param`
- `retry_template URL param silently re-fires Generate on return and surfaces the result`
- `sortUploadedDocs orders by doc_name case-insensitively`
- `sortUploadedDocs by close_date joins through txById and sinks docs without a closing date to the bottom`
- `sortUploadedDocs by ai_impact falls back to recently_updated for raw docs`
- `sortUploadedDocs by last_touched matches recently_updated for raw docs`
- `CategorizedView reorders when sort changes (All Docs, Pending review, Sent for sig, Signed)`
- `DocFilterTabs renders fallback caption when ai_impact or last_touched is active on a categorized tab`
- `Switching tabs preserves the active sort key in URL and applies it on the destination tab`
- `Transaction DocumentsModal child Email dialog is visible above the parent overlay (real DOM stacking, not just mount assertion)`
- `Transaction DocumentsModal More-actions dropdown is visible above the parent overlay`
- `Transaction DocumentsModal Version history panel is visible above the parent overlay`
- `Transaction DocumentsModal Archive confirm AlertDialog is visible above the parent overlay`
- `Transaction DocumentsModal Flag for deletion modal is visible above the parent overlay`
- `Transaction DocumentsModal Download pre-opens a new tab synchronously and is not popup-blocked`
- `Transaction DocumentsModal Escape closes the modal and returns focus to the trigger element`
- `Transaction DocumentsModal Tab key cycles inside the modal and does not escape`
- `Transaction DocumentsModal Send for Signature button opens the existing sig modal`
- `Transaction DocumentsModal Sync envelope button refreshes signature_status for awaiting docs`
- `Transaction DocumentsModal Void envelope button voids in-flight envelopes`
- `Transaction DocumentsModal doc-name click opens the preview modal instead of forcing a download`
- `Transaction DocumentsModal status filter chips narrow the list to Uploaded / Awaiting / Signed / Flagged`
- `Transaction DocumentsModal Mark for follow-up internal action creates a document_followup_flags row`
- `ClientDocumentsPage renders a real document list with Flag for deletion entry per row`
- `FsboDocumentsPage renders a real document list with Flag for deletion entry per row`
- `Deletion Queue button shows a pending-count badge when count > 0 and is hidden when count is 0`
- `DeletionApprovalsPanel Approve opens an AlertDialog confirm before archiving`
- `DeletionApprovalsPanel Approve dialog body uses signed-document copy when doc.is_signed is true`
- `DeletionApprovalsPanel Reject without a reason shows a validation error and does not submit`
- `Priority queue surfaces deletion_review items when documents have deletion_flagged=true`

### E2E (Playwright)

1. Log in as Agent.
2. Mark a Missing row N/A; confirm a Cleared card appears with `Marked N/A` badge.
3. Click `View Details` on the card; confirm the new detail modal opens.
4. Click `Undo` from the modal; confirm the row returns to Missing.
5. From a `Pending Review` doc, open the `Edit Document` modal via the More menu.
6. Reassign the doc to a different transaction.
7. Confirm the doc disappears from the original transaction's documents list and appears under the new one.
8. If the destination transaction was missing that requirement, confirm a `Reassigned` badge appears in `Cleared today`; if it was only a cleanup move, confirm the audit/touch history updates but the strip does not falsely show a clear.
9. Switch to the All Docs tab; confirm the strip is still visible.
10. Open the `View all cleared (last 7 days)` sheet; confirm the same row is listed there.
11. Filter the strip to `Me`; confirm only the rows the logged-in actor cleared remain visible.
12. From a `Missing` row whose `item_key` has no template (e.g. Appraisal Report), confirm the row's button set has no Generate; only Upload / Request / Call appear.
13. From a Missing row that does have a template but is missing `seller_name` on its transaction (e.g. Lead-Based Paint Disclosure), click Generate; the `TemplateMissingFieldsModal` opens with `Seller's full name` and a `Fix →` button.
14. Click `Fix →`; the transaction parties tab opens with the seller row flashed and focused.
15. Add the seller; return to `/documents`; confirm the Generate flow retries silently and the draft preview opens, without the user clicking Generate a second time.
16. On the All Docs tab, pick `Document name` from the sort dropdown; confirm the list reorders alphabetically by `doc_label ?? file_name`.
17. Switch to the Pending review tab without touching the sort chip; confirm the list there is also alphabetically ordered (sort persists across categorized tabs).
18. Switch to AI Priority; confirm the chip remains `Document name` and the AI queue is also alphabetically ordered.
19. Pick `Close date` on the Signed tab; confirm docs whose transaction has no `closing_date` sink to the bottom and the head is the soonest-to-close.
20. Pick `AI impact` on the Signed tab; confirm the dropdown caption reads `Sorted by Recently updated on this tab.` and the rows are ordered by `updated_at` descending.
21. Upload from a Missing row and confirm the upload appears in Cleared Today with `Uploaded`; upload from the header without a missing-row context and confirm it does not appear in Cleared Today unless it satisfies a requirement.
22. Send a document for signature and confirm `sent_for_signature` appears on the Sent for sig tab, not Pending review.
23. Complete a stub envelope and confirm the signed copy appears in Cleared Today with `Signed`.
24. Void or decline an envelope and confirm the row offers `Resend` instead of disappearing from every workflow surface.
25. Open the Transaction Documents modal from a transaction card's footer; click `Email`, `Version history`, the `More` dropdown, and `Archive` in sequence; confirm each child surface is visible above the parent backdrop and accepts a click.
26. Click `Download` on a document inside the Transaction Documents modal; confirm the file opens in a new tab and is not blocked by the browser's popup blocker.
27. Inside the Transaction Documents modal as an internal user, click `Send for Signature`; confirm the existing signature modal opens above the parent.
28. With at least one `Awaiting` document, click `Refresh signature status`; confirm a toast describes the new state and the badge updates.
29. With the Transaction Documents modal open, press Tab repeatedly; confirm focus cycles inside the modal and does not escape to the page behind. Press Escape; the modal closes and focus returns to the transaction card footer button that opened it.
30. Sign in as a Client/FSBO/Vendor; navigate to `/client/documents` (or the FSBO/Vendor equivalent); confirm a real document list renders with a `Flag for deletion` action on each row.
31. Flag a document; sign out; sign in as the Agent who owns the transaction.
32. On `/documents`, confirm the `Deletion Queue` button now shows a pending-count badge.
33. Click `Deletion Queue`; click `Approve` on the request; confirm a Radix `AlertDialog` opens with the correct copy (signed-document copy if applicable); click `Archive document` to confirm.
34. Sign back in as the original requester; confirm a notification appears in the notification bell with the reviewer's name and reason; confirm an email was sent to the requester's address.
35. Sign back in as the Agent; click `Deletion Queue` again to reject a different request without typing a reason; confirm a validation error appears and the request does not submit. Add a reason; the rejection completes and the requester receives a notification.
36. On `/documents`, confirm the priority queue surfaces a `deletion_review` row for any remaining flagged documents (post-migration to §3.7.2E).

---

## 10. Edge Cases

| Case | Behavior |
| --- | --- |
| User reassigns then immediately undoes via audit | Audit log shows both moves; current `transaction_id` reflects the latest state. No data loss. |
| Strip click on a deleted doc | Detail modal renders with the doc label and the cleared-at timestamp; preview button is disabled with a "This document was removed" message. |
| User restores a soft-deleted doc that was the source of a `clear` event | The clear event remains in history; the doc reappears in the appropriate tab with its current review state intact. |
| Bulk Upload/Assign 5 missing items, 1 fails 409 | The 4 successful rows reconcile independently; the 1 failed row stays selected with an inline error. No partial rollback. Bulk reassign is not offered on Missing rows because there is no existing document to move. |
| `cleared_actor_scope=me` for a teammate with no clears in the window | Strip shows empty state copy; subtitle still describes what `Cleared today` is. |
| Network drops mid-undo | Optimistic state rolls back; toast surfaces the failure; the row stays in the strip. |
| Two browsers reassign the same doc simultaneously | Last-write wins; the slower tab refetches and reflects the final transaction. No optimistic locking yet (Phase 5+). |
| Strip on a tenant with no internal teammates (solo agent) | The `Team` filter chip is hidden — only `All` and `Me` render. |

---

## 11. Rollout Slices

Each slice ships standalone and is verifiable end-to-end on the dev deployment at `https://dev.velvetelves.com`.

### Slice 1 — Cleared Today Identity (2 days)

- Strip subtitle, info popover with badge legend, empty state copy.
- Hoist strip render to be visible on every tab.
- Keep the existing `upload -> Uploaded` badge mapping and add the missing upload-side `clear` event context.
- Frontend tests for the renders.

### Slice 2 — Strip Cards Get Real Affordances (2 days)

- Replace whole-card click with `View Details` / `Open` / badge layout.
- Add `ClearedItemDetailModal` + new backend `priority-events/{event_id}` endpoint.
- Per-card Undo for waive (already supported) and approve (new `unapprove`).
- Backend tests for the new endpoints + RLS scoping.

### Slice 3 — Reassign Capability (2 days)

- Add transaction selector to the existing rename modal, retitle to `Edit Document`.
- Expose `Edit Document` from `QueueRow` more-menu and `PriorityDetailModal` alt-actions.
- Backend: `_doc_snapshot.transaction_id` regression test, in-flight envelope block, and source/destination priority events for reassign.
- E2E covering reassign + cleared-strip reflection.

### Slice 3.5 — Template Generation Recovery (1.5 days)

- Backend: filter `template` from `alt_actions`/`suggested_action` for unregistered item keys; split response into `generated` / `missing_fields` / `no_template`; add `fix_route` to each missing field; add `suggested_alternatives` to `no_template`.
- Frontend: split the existing modal into `TemplateNotAvailableModal` and `TemplateMissingFieldsModal`; wire `Fix →` deep links and inline edit for safe transaction fields; wire `retry_template` auto-retry on return; update copy per §3.5.4.
- Update backend test `test_template_generation_creates_draft_or_missing_fields_response` to assert the new contract.
- E2E steps 12-15 in §9 cover this slice end-to-end.

### Slice 3.6 — Sort Dropdown Coverage (0.5 days)

- Extract `src/utils/documentsSort.ts` with `sortPriorityItems` and `sortUploadedDocs`; move the inline sort body out of `visibleQueue`.
- Pass `sort` and `txById` into `CategorizedView`; apply `sortUploadedDocs` after the tab filter.
- Add the fallback caption under the sort chip when `ai_impact` / `last_touched` are active on categorized tabs.
- Cover with the new frontend unit tests and E2E steps 16-20 in §9.

### Slice 3.7 — Deletion Approval Surface Completion (1.5 days)

- **Day 1 — close the loop on the existing surface.**
  - Backend: add `GET /documents/flagged/count`; on `approve-deletion` and `reject-deletion`, call the deletion-decision notification helper to insert a `notifications` row and send/skip email for `deletion_flagged_by`; add 409 `envelope_in_flight` block on approve; make Reject reason required (422 on missing).
  - Frontend: add `useFlaggedDocumentsCount()`; wire the badge + hide-when-zero on the header button; wrap Approve in a Radix `AlertDialog` confirm with signed-doc-aware copy; mark Reject reason required in the UI.
  - Tests cover the new endpoints, the notification side effect, and the confirm dialog.
- **Day 1 (continued) — give external users a real surface.** Replace the stubs in `ClientDocumentsPage`, `FsboDocumentsPage`, and `VendorDocumentPortalPage` with real document lists backed by the generic role-scoped `GET /documents` endpoint, or add the dedicated alias endpoints in the same slice; expose `Flag for deletion` per row.
- **Day 0.5 — migrate to AI priority items (default).** Emit deletion-flag rows as `kind='deletion_review'` priority items from the dashboard endpoint; add `review_deletion` action to the frontend dispatcher; remove the header button once the priority-item path is verified on dev.
- E2E steps 26-32 in §9 cover this slice end-to-end.

### Slice 3.8 — Transaction Documents Modal Stacking + Completion (2 days)

- **Day 1 — stop the bleeding.** Convert the hand-rolled overlay at `DocumentsModal.tsx:540-547` to a Radix `Sheet` (or `Dialog`) so the parent and every child share the same `z-50` stack. Remove the `z-[600]` arbitrary class. Verify all six previously-invisible surfaces (Email, Version history, Rename, Flag for deletion, Archive confirm, More menu) render visibly. Add focus trap + Escape + `role="dialog"` parity for free.
- **Day 1 — fix Download.** Fix the Transaction modal and All Documents download paths together: no `window.open` after an `await`; use the pre-opened-tab pattern for Open/new-tab flows and attachment/blob semantics for buttons labeled Download.
- **Day 2 — parity with `/documents`.** Wire `useSendForSignature`, `useSyncEsignStatus`, `useVoidEsign` into the row action set when `isInternal`. Replace doc-name click with the All-Documents preview modal. Add a small status filter chip row (`All / Uploaded / Awaiting / Signed / Flagged`) plus the sort dropdown from §3.6.3 (reusing `sortUploadedDocs`). Add `Mark for follow-up` to the More menu for internal users, wired to the `document_followup_flags` endpoint. Add the `Restore Archived` entry from §7.1 to the page header of the modal.
- Cover with the new frontend tests and E2E steps 21-25 in §9.

### Slice 4 — View All Cleared + Filters + Restore + Bulk (2-3 days)

- 7-day cleared sheet with cursor pagination.
- `cleared_actor_scope` chips on the strip and sheet.
- `Restore archived` panel.
- Bulk actions on the Missing tab (Mark N/A, Request, Upload/Assign). Existing-document tabs can get bulk Reassign later, but it is not a Missing-row action.

### Slice 5 — Polish (1 day)

- A11y audit (keyboard path, focus restoration, screen-reader announcements).
- Final visual pass against the design and the style guide.
- Update the testing guide with new affordances (test 27.4 closes after this slice).

---

## 12. Definition Of Done

The All Documents page is complete for this workflow remediation when:

- A user reading `/documents` for the first time can name what the Cleared Today strip is, and what each badge means, without leaving the page.
- The Cleared Today strip is visible on every tab when there is data to show.
- Every Cleared Today card has explicit `View Details` and `Open` buttons; clicking a Mark-N/A card opens the new detail modal — no dead previews.
- Per-card Undo works for Approve, Mark N/A, Generated, and Uploaded clears. Signed/Replaced/Voided show calm explanations of why undo isn't offered.
- A user can reassign any document they can see to any transaction they can access from any tab — without hunting through a hidden menu.
- The Edit Document modal sets transaction, file name, label, and document type in a single round trip and records every change in the audit log.
- An in-flight or signed envelope blocks reassign with a clear error, not a silent failure.
- The strip respects a `cleared_actor_scope` filter and offers a 7-day cleared sheet for deeper review.
- Soft-deleted documents are restorable from a Restore Archived panel without a database admin.
- Missing-tab rows support multi-select and bulk Mark N/A / Request / Upload/Assign.
- All new endpoints have RLS coverage and pass tenant-isolation integration tests on local Postgres.
- The new affordances pass keyboard-only navigation, including focus restoration on modal close.
- Tests 27.4 and 27.9 in `FRONTEND_CLIENT_TESTING_REVIEW.md` are updated to reflect the new affordances; both pass.
- No action shown in the UI is cosmetic — every button persists state and reconciles the queue, hero, briefing, tab badges, and strip after success.
- The Generate button is offered only for requirements the system has a registered template for; rows without a template surface Upload / Request / Call instead.
- The "no template registered" path opens a modal with real Upload and Request CTAs — never a single dead-end Got it button.
- The "missing fields" path shows human field labels only (no raw machine names) and offers a `Fix →` deep link or an inline edit on every row.
- After a user fills the missing field and returns to `/documents`, Generate auto-retries silently; the user does not have to click Generate a second time.
- The sort dropdown reorders the visible list on every tab — AI Priority, Missing, All Docs, Pending review, Sent for sig, and Signed — and the choice persists across tab switches.
- When a sort key has no natural mapping on a categorized tab (`ai_impact`, `last_touched`), the dropdown shows an honest fallback caption rather than silently misleading the user.
- The Transaction Documents modal's child surfaces (Email, Version history, Rename, Flag for deletion, More menu, Archive confirm, AI-parsed updates confirm) all render visibly above the parent backdrop. No arbitrary `z-[N]` values remain in the modal stack.
- Download from All Documents and the Transaction Documents modal is never opened after an `await`; Open and Download have distinct semantics, and the download path uses attachment/blob behavior when the storage provider supports it.
- The Transaction Documents modal has a focus trap, Escape closes it, focus returns to the trigger element, and the surface carries `role="dialog"` + `aria-modal="true"` + `aria-labelledby`.
- Internal users can Send for Signature, Sync, and Void envelopes from inside the Transaction Documents modal — they no longer have to leave to `/documents` for an in-context signature operation.
- The Transaction Documents modal previews documents inline (not via a forced new-tab download), filters by status, sorts via the same `sortUploadedDocs` helper as the All Documents page, and exposes `Mark for follow-up` for internal users.
- External users (Client, FSBO, Vendor) can reach `Flag for deletion` from their dedicated portal documents pages — not only from the Transaction Documents modal.
- The `Deletion Queue` header button reflects pending count via a badge, hides itself when count is 0, and is removed entirely once deletion requests land as AI priority items.
- Every approve or reject of a deletion request notifies the requester via an in-app notification and an email — they never have to come check whether their flag was honoured.
- Approve requires an explicit Radix `AlertDialog` confirmation with copy that adapts to whether the document is signed; Reject requires a non-empty reason.
- Deletion-review work appears as first-class priority items in the AI queue (`kind='deletion_review'`), severity `critical` for signed documents and `medium` otherwise.

---

## 13. Defaults

Unless Jake says otherwise:

1. Strip subtitle uses the language in §2.1 verbatim.
2. The `Edit Document` modal blocks reassign for in-flight envelopes — no override.
3. The 7-day cleared sheet's hour window is **168** (7 days) and tunable only by future param.
4. `cleared_actor_scope` defaults to `all` on first load; user choice persists in URL only — no per-user setting yet.
5. Undo on approve produces an explicit `unapprove` event; the original `approve` clear event stays in the audit chain.
6. Bulk Upload/Assign treats each row independently; partial failures don't roll back successful ones. Bulk Reassign is reserved for existing-document rows if/when that separate surface ships.
7. Restore Archived shows the last 90 days only; older docs require admin support.
8. AI never recommends, drafts, or executes a reassign without an explicit user click (consistent with the companion plan's AI guardrail).
9. The Generate action is hidden whenever the system has no template registered for the requirement — no exceptions and no per-tenant overrides for MVP.
10. Inline edit inside `TemplateMissingFieldsModal` is restricted to a small allow-list of safe transaction fields (`purchase_price`, `title_company`); everything else routes through the parties/overview tab deep link to keep the modal scope tight.
11. `retry_template` auto-retry only fires for the most recent retry token; older tokens are ignored if the user opened multiple tabs.
12. `ai_impact` and `last_touched` fall back to `recently_updated` on the categorized tabs (All Docs / Pending review / Sent for sig / Signed) for MVP. A future enhancement can introduce a per-document touch ledger to make `last_touched` distinct.
13. Sort comparators live in a single helper (`src/utils/documentsSort.ts`) — no per-tab inline sort bodies. Adding a new sort key means editing one file, not five.
14. No arbitrary `z-[N]` Tailwind classes anywhere in the documents modal stack — every overlay uses Radix primitives so z-index is `z-50` everywhere and stacking-context inversion cannot recur.
15. The Transaction Documents modal renders as a Radix `Sheet` (side `right` on desktop, side `bottom` on mobile). It does not become a centered `Dialog` — long document lists read better in a side panel.
16. `window.open` is **never** called after an `await` in the documents code path. The new tab is always pre-opened synchronously inside the click handler and navigated once the URL resolves.
17. Reject of a deletion request requires a non-empty reason (≥3 chars). Approve makes the reason optional but always passes any provided text into both the in-app notification and the email.
18. Deletion-review priority items use severity `critical` for signed documents and `medium` for everything else — never `low` (a deletion request is always a deliberate user action, not routine).
19. The Deletion Queue header button is a **bridge** affordance only. It is removed from the page header the same week the priority-item path lands; the badge endpoint and hook stay for any future moderation surface that wants the same pattern.
