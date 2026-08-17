# Client Portal — Operational Rebuild Plan

*Drafted: 2026-08-17. Grounded in the shipping represented-client workspace
(`ClientWorkspaceLayout` / closing concierge), `CLIENT_WORKSPACE_PLAN.md` (rev 1,
2026-05-23), `CLIENT_WORKSPACE_REDESIGN_PLAN.md` (rev 2, 2026-05-30),
`CLIENT_PORTAL_TESTING_GUIDE.md`, `FRONTEND_UI_WORKFLOW_LOGIC.md` §9,
`CLIENT_PORTAL_CHROME_QA_2026-08-17.md`, and the live code in
`velvet-elves-backend` / `velvet-elves-frontend`.*

> **STATUS: IMPLEMENTED 2026-08-17.** Concierge chrome is unchanged. The action
> model now matches this contract: shared documents, completable CTAs, one
> ranker, honest Ask-your-team copy, deal switcher, updates+bell, and Payments
> hidden when there are no open invoices. Apply
> `20261001090000_client_visible_documents.sql` before using Share with client
> against a live database.

> **Relationship to prior plans.** Rev-1 made the data layer truthful. Rev-2
> rebuilt the presentation into Jake's concierge Home. **This rebuild keeps
> both.** It does not restyle the navy sidebar, does not move clients back into
> `AppLayout`, and does not add an LLM "Ask Velvet" in the first slice. It
> changes the **action model**: what the client can see, what a CTA actually
> does, and which page is the single source of "what do I do next."

---

## 1. Thesis

The portal today is a **status board + human mailbox + own-upload tray**.

A represented buyer/seller's actual jobs are:

1. See where the deal is.
2. Finish the one thing that is waiting on them (sign, acknowledge, upload, pay, reply).
3. Read what the team just sent.
4. Reach a human without guessing whether Velvet is an AI.

Jobs 1 and 4-as-mailbox already work. Jobs 2 and 3 do not, because documents are
scoped to `uploaded_by == client.id` and most Next Best Action buttons open
another status page.

**North star for this rebuild:** every named client action is completable
in-portal, without a staff detour, and without leaking internal workflow.

---

## 2. Goals

1. **Shared documents, not own-uploads-only.** The client sees (a) files they
   uploaded and (b) files the team explicitly shared for review / acknowledge /
   signature. Staff-internal files stay invisible.
2. **CTAs complete the named job.** "Sign" opens signing. "Reply" focuses the
   thread. "Pay" opens Checkout. If there is no scheduler, the card is not titled
   "Choose your inspection time."
3. **One next-action brain.** Home and Next Steps render the same ranked
   `home.next_action`. No second prefixer that invents "Review {milestone}."
4. **Honest Ask-your-team.** Keep the `is_client_visible` thread. Stop implying
   instant answers. Show awaiting-reply state.
5. **Multi-deal Home that the client can switch.** Nearest-closing focus is a
   default, not a lock.
6. **Hold the customer boundary.** No tasks, internal notes, AI drafts, audit
   rows, or other parties' private files. PII still Fernet-decrypts in the
   service before it leaves.

---

## 3. Non-goals (this rebuild)

- Pixel restyle of `ClientWorkspaceLayout`, Home cards, or concierge tokens.
- An LLM / retrieval "Ask Velvet" answerer (still Redesign D4, a later slice).
- Exposing the staff All Documents center, task queue, or communication audit.
- Client self-serve milestone share links (still `CLIENT_WORKSPACE_PLAN.md` §11.3).
- Replacing Stripe pay-link; only surfacing it when an open invoice exists.
- Changing how clients get onto a deal (`transaction_assignments` remains the gate).

Do **not** start the LLM slice until Phases 1–3 below are in production. An
assistant that describes work the client still cannot do makes the portal worse.

---

## 4. What we keep

| Keep | Where |
| --- | --- |
| Concierge shell + 5-item nav | `ClientWorkspaceLayout` — Home · Next Steps · Timeline · Documents · Updates |
| Canonical client read | `GET /api/v1/dashboard/client` + additive `home` block |
| Assignment gate | `client_workspace.list_client_transaction_ids` / `assert_client_transaction_access` |
| Human Q&A | `GET/POST /api/v1/client/messages` gated by `communication_logs.is_client_visible` |
| Staff Client access + Client Q&A | `client_staff.py` / transaction card actions |
| Agent card (primary_agent first) | `resolve_agent_card` |
| Invoice pay-link | `GET/POST /api/v1/client/invoices…` |
| Flag for deletion | client-owned uploads only; shared packets are not client-deletable |
| Chrome QA harness | `velvet-elves-data/client_portal_qa/client_portal_chrome_qa.mjs` |

---

## 5. Decision register

Recommendations. Flag in the implementing PR if product overrides.

| ID | Decision | Recommendation | Rejected alternative |
| --- | --- | --- | --- |
| **O1** | How a client sees an agent file | New `documents.is_client_visible` boolean, same mental model as `communication_logs.is_client_visible`. Staff "Share with client" / "Send for client signature" sets it. Client fetch = own uploads **OR** (`is_client_visible` AND assigned to that transaction). | Opening every document on the transaction to the client (leaks internal packets). A parallel `client_document_shares` table for MVP (extra join, two sources of truth). |
| **O2** | Client action on a shared doc | Derived, not a free-text field: in-flight `signature_status` → **Sign**; new `acknowledged_at` null on a notice type → **Acknowledge**; `review_status = needs_follow_up` on an own upload, or staff-flagged review on a shared packet → **Review**. | Storing a mutable `client_action` string that can drift from signature state. |
| **O3** | Sign in-portal | `GET /api/v1/client/documents/{id}/sign-url` returns the existing DocuSign recipient URL when the client is a signer on an in-flight envelope. If no envelope yet, **Open** the PDF (download URL) and the NBA copy says "Review & sign when your agent sends it" — never a fake Sign button. | Telling the client to check email with no in-portal path. Building a second e-sign stack. |
| **O4** | Acknowledge | `POST /api/v1/client/documents/{id}/acknowledge` stamps `acknowledged_at` / `acknowledged_by` (client user id). Staff sees it on the document row. No legal e-sign substitute — notices and wire-fraud attestations only. | Using `review_status = approved` (that is the agent's review of the client's upload). |
| **O5** | Next-action source | `derive_client_next_action` remains the **only** ranker. Next Steps and Home both render `data.home.next_action`. Ranking stays: Sign → Acknowledge → Review/revise → unanswered team message → **client-completable** active milestone → soft upcoming (timeline, labeled as "What's next", not as a fake verb). | Keeping `ClientNextStepsPage.actionTitle` / `selectPriority`. |
| **O6** | Milestone titles | `_next_action_title` keyword rewrite is removed. Use the milestone's plain-English `explanation` / `label`. A scheduler CTA is allowed only when a real `cta_target` exists (not in this slice). | Shipping "Choose your inspection time" that opens the timeline. |
| **O7** | Ask Velvet copy | Relabel to **Ask your team**. Placeholder: "Send a question to your agent." Quick prompts stay as message starters. Composer footer: "Your agent replies here — this is not an instant answer." | Building the LLM in this rebuild. Leaving "Ask anything about your transaction / Explain the appraisal" in place. |
| **O8** | Multi-deal Home | `GET /dashboard/client?transaction_id=` (optional). Omitted → current `select_focus_transaction`. Present → that deal if the client is assigned, else 403. Frontend: hero switcher writes the query; every Home card keys off `home.transaction_id`. | A second home endpoint. Hiding deal 2 until the client opens Timeline. |
| **O9** | Updates feed | `build_recent_updates` unions (1) outbound `is_client_visible` comms, (2) milestones that flipped to `done` if a timestamp exists, (3) client-visible document events (`shared_at`, `acknowledged_at`, `signature_status` changes, own-upload `review_status` changes). Cap 5 on Home, 20 on Updates. No synthetic `ts: null` rows. | `ClientUpdatesPage.derivedUpdates` fabricating "completed" lines. |
| **O10** | Notifications | Reuse `notifications` + the existing pending/last-seen API if it is already role-safe for Client; otherwise a thin client-safe list. Types in this slice: `client_reply` (team answered), `client_document_shared`, `client_signature_ready`, `client_invoice_open`. Bell shows unread count and opens Updates (or the deep link). | Leaving the bell as a silent shortcut. |
| **O11** | Payments chrome | Not a sixth nav item. If `open` invoice count > 0, Home NBA may rank **Pay {invoice}** above soft milestones, and the Home topbar Payments button stays. If count = 0, hide the topbar Payments button. | Adding Payments to the 5-item nav (breaks the signed-off comp). Showing an empty Payments door as a primary action. |
| **O12** | Document list actions | Per row: **Open** (signed download URL — already `GET /documents/{id}/download`). **Sign** / **Acknowledge** when derived. **Flag for deletion** only on own uploads that are not shared packets. Status chip: Uploaded / Needs you / Signed / Acknowledged. | Keeping Flag as the only row action. |

---

## 6. Target journeys (the acceptance stories)

These are the rebuild's definition of done. Chrome checks are not enough.

### 6.1 Sign what the agent sent

1. Staff opens the deal, shares a disclosure with the assigned client, sends it
   for signature (client is a recipient).
2. Client Home Next Best Action = "Sign {label}", CTA **Review & Sign**.
3. CTA opens the signing URL (or the in-portal viewer that launches it).
4. After complete, NBA clears that item; Documents row shows Signed.

### 6.2 Acknowledge a notice

1. Staff shares a wire-fraud / information notice as Acknowledge (no envelope).
2. Client sees it on Home Documents Needing Attention and on Documents.
3. Client opens it, taps Acknowledge, confirms.
4. Row leaves "needs you"; staff sees acknowledged timestamp.

### 6.3 Upload a revision

1. Staff marks the client's upload `needs_follow_up`.
2. NBA = "Update {label}" → Documents, with the review note visible.
3. Client opens the file, uploads a replacement via the existing modal.
4. Bucket moves; NBA clears if nothing else is waiting.

### 6.4 Reply to the team

1. Staff sends a Client Q&A reply.
2. NBA = "Reply to your agent" → focuses Ask-your-team on the **same deal**.
3. Bell unread count increments. Updates feed shows the team message with a real timestamp.

### 6.5 Two deals

1. Client is assigned to two active transactions.
2. Home hero lists both addresses; switching rewrites `?transaction=` and every card.
3. Next Steps still shows one **priority** action (from the focused deal's ranker)
   plus a compact list of the other deal's next action — both from `derive_client_next_action`,
   never from `Review {label}`.

### 6.6 Empty but honest

- No assignment → existing empty portal copy. Unchanged.
- Assigned, nothing waiting → "You're all caught up" **and** Ask-your-team still available.
- No invoices → Payments control hidden, not an empty table behind a primary button.

---

## 7. Phases

Implement in order. Each phase is separately mergeable. Do not skip Phase 1.

### Phase 1 — Client-visible documents (the product hole)

**Backend**

1. Migration: `documents.is_client_visible BOOLEAN NOT NULL DEFAULT FALSE`,
   `documents.shared_with_client_at TIMESTAMPTZ`, `documents.shared_with_client_by UUID`,
   `documents.acknowledged_at TIMESTAMPTZ`, `documents.acknowledged_by UUID`.
   Partial index on `(transaction_id) WHERE is_client_visible`.
2. Staff write path (transaction workspace, same place as Client Q&A):
   `POST /api/v1/transactions/{id}/documents/{doc_id}/share-with-client`
   `{ "action": "review" | "acknowledge" | "sign" }`.
   - Sets `is_client_visible`, stamps `shared_with_client_*`.
   - `sign` requires an in-flight envelope **or** creates one with the client's
     decrypted email as recipient (reuse `POST /documents/{id}/esign` internally).
   - 403 unless caller is internal and assigned / tenant-authorized on the deal.
3. Unshare: `DELETE` same path — only if signature is not in-flight. Sets
   `is_client_visible = false`. Does not delete the file.
4. Widen `_can_access_doc` in `app/api/v1/documents.py`: Client/FSBO may access if
   `uploaded_by == current_user.id` **OR** (`is_client_visible` and
   `assert_client_transaction_access` on `doc.transaction_id`).
5. Widen `fetch_client_documents` in `client_workspace.py` the same way. Still
   exclude `is_deleted`. Never return documents for transactions the client is
   not assigned to.
6. `GET /api/v1/client/documents/{id}/sign-url` — 403 if not shared / not a signer;
   409 if no in-flight envelope.
7. `POST /api/v1/client/documents/{id}/acknowledge` — 403 if not shared for
   acknowledge; idempotent if already acknowledged.
8. Expand `_document_action` to return Acknowledge (O2). Rank Sign above
   Acknowledge above Review in `derive_client_next_action` **and**
   `build_documents_needing_attention`.
9. NBA `cta_target` for Sign → `/client/documents/{id}?sign=1` (or a dedicated
   route). For Acknowledge → `/client/documents/{id}?ack=1`. For Review →
   `/client/documents/{id}`. Stop targeting the list with no document id.

**Frontend**

1. `PortalDocumentList` (client concierge variant): Open, status chip, Sign,
   Acknowledge, Flag (own uploads only). Call existing download helper in
   `useDocuments`.
2. Documents page: keep upload modal; add an "From your team" group above
   "You uploaded."
3. Home Documents Needing Attention rows become links to the document, not
   a dead chip plus a generic Open Documents button.
4. Staff UI: one **Share with client** control on the deal document row /
   Client Q&A-adjacent surface. Do not hide this behind Swagger.

**Tests**

- Client cannot GET download / sign-url for an unshared agent doc (403).
- Shared doc appears in `home.documents_needing_attention` and dashboard documents list.
- Unshare drops it from the client list.
- Cross-transaction: client on deal A cannot open a shared doc on deal B.
- `test_client_workspace.py` + new `test_client_document_share.py`.
- Frontend: `ClientWorkspace.test.tsx` — Sign CTA href includes document id.

**Done when:** Journey 6.1 and 6.2 pass on local with the Bradyn (or equivalent)
client and a staff share, without SQL.

---

### Phase 2 — One ranker, honest CTAs

**Backend** (`app/services/client_workspace.py`)

1. Delete `_next_action_title` keyword rewrites (inspection → "Choose your
   inspection time", etc.).
2. Ranking (replace the current 1–5 list):
   1. Sign (in-flight signature on a client-visible doc).
   2. Acknowledge (shared notice, `acknowledged_at` is null).
   3. Review / revise (`needs_follow_up` on a client-visible doc).
   4. Unanswered outbound team message (`direction == outbound` on latest
      visible row) — `cta_target` = `/client/home?transaction={tid}&ask=1`.
   5. Open invoice (if Phase 6 is not split out, include here; else leave a
      hook). `cta_target` = `/client/invoices/{id}`.
   6. Soft upcoming milestone: title = milestone label or explanation,
      `cta_label` = "View timeline", `requested_by` = "Velvet",
      `est_minutes` = `null`.
3. Drop fabricated `est_minutes` on non-completable actions. Keep a real
   estimate only on Sign (3) / Acknowledge (1) / Reply (2) if product wants it.
4. `Why this matters` is **not** a second button to the same URL. Either remove
   it or point at a short static explainer route later. This slice: remove the
   duplicate link on Home.

**Frontend**

1. `ClientNextStepsPage` reads `data.home.next_action` for the focused deal.
   Delete `actionTitle`, `selectPriority` as the priority card source.
2. For other deals on Next Steps, call the same ranker per transaction —
   extend `home` **or** add `transactions[].next_action` computed in
   `assemble_client_home` / `build_client_transaction_view` so the client never
   re-derives ranking in React. Prefer `next_action` on each tx view so Next
   Steps does not need N extra round trips.
3. `resolveClientCtaTarget` keeps rewriting legacy `?transaction=` milestone
   URLs; add document-id routes.

**Done when:** Home and Next Steps show the same title + CTA for the focused
deal. No "Review Inspection Period" unless that is the real milestone label.

---

### Phase 3 — Honest Ask-your-team

**Copy**

- Home card title: **Ask your team** (keep "Velvet" in the product chrome, not
  in the composer promise).
- Placeholder: "Send a question to your agent."
- Prompts: keep three starters; drop "Explain the appraisal" or retitle it
  "Ask my agent to explain the appraisal."
- After send: existing toast is fine ("Your agent will see it and reply here").

**State**

- If latest visible row is inbound: "Waiting for your agent" + relative time.
- If latest is outbound: primary CTA on the card = Reply (already NBA rank 4).
- `ClientAskThread` empty copy already honest — reuse it on Home; do not
  duplicate a second composer that implies chat.

**Do not** add RAG, deal-state Q&A, or a new messages endpoint in this phase.

**Done when:** a first-time client cannot reasonably believe Velvet will answer
in seconds. Chrome QA prompt strings are updated.

---

### Phase 4 — Multi-deal Home

**Backend**

- `GET /api/v1/dashboard/client?transaction_id=` honors O8.
- `assemble_client_home` already takes a focus tx; wire the query param in
  `dashboard_role.py`.

**Frontend**

- Hero: if `transactions.length > 1`, a compact switcher (address + closing
  date), not only "View all N timelines."
- `useSearchParams` on Home: `transaction`, keep existing `ask=1`.
- Switching deals refocuses Ask-your-team onto that `transaction_id`.
- Updates page already has a picker — align it on the same query param name.

**Done when:** Bradyn's two QA deals (`77 Harness` / `88 Livefire`) are both
reachable from Home without opening Timeline.

---

### Phase 5 — Updates feed + bell

**Backend**

- Rewrite `build_recent_updates` per O9. Require a real `ts` on every item.
- On staff share, staff Q&A reply, invoice open, signature-ready: insert
  `notifications` rows for the client user (best-effort, same pattern as
  `client_messages.py` already uses for `client_question`).
- Confirm `GET /api/v1/notifications/pending` is safe for Client role; if it
  leaks staff types, add a client filter (`type IN (...)`) rather than a new
  stack.

**Frontend**

- Delete `derivedUpdates` fallback in `ClientUpdatesPage`.
- Bell: unread count from pending notifications; `aria-label` includes the count.
- Deep links: reply → Home `?ask=1&transaction=`; document → Documents `/{id}`;
  invoice → invoice detail.

**Done when:** a staff Q&A reply increments the bell without a full reload
(refetch on window focus is enough; sockets are Phase 7).

---

### Phase 6 — Payments surfacing

- Include open invoices in `derive_client_next_action` (rank after documents,
  before soft milestones).
- Hide Home topbar Payments when `invoice_count_open == 0`.
- Empty `/client/invoices` copy stays; it is no longer a primary door.
- Chrome QA CP-47 becomes: "Payments hidden when none" rather than "empty table
  visible from Home."

Staff still creates the invoice; this phase does not invent billing.

---

### Phase 7 — Convenience polish (after 1–6)

- Add-to-calendar on every upcoming key date (ICS + Google), not closing-only
  (`ClientHomePage` `googleCalendarHref`).
- Refetch `useClientMessages` while the Ask card is focused (5–10s interval) or
  on `visibilitychange`.
- Reconcile `FRONTEND_UI_WORKFLOW_LOGIC.md` §9 nav with shipping
  Home · Next Steps · Timeline · Documents · Updates; Payments/Agent remain
  Home-reachable, not sidebar items.
- Drop `est_minutes` from remaining soft actions if any remain.

---

## 8. Staff-side work this rebuild depends on

The portal cannot become useful if agents have no UI to share a file. That is
the same class of gap Client access / Client Q&A closed on 2026-05-25.

Required staff surface (Phase 1, same PR or an immediately following PR):

- On the deal's document row (and/or Client Q&A drawer): **Share with client**
  with Review / Acknowledge / Sign.
- Sign path pre-fills the assigned client's email from the decrypted user row.
- Clients hub (`assemble_clients_hub`) already has a "to review" count for
  client uploads. Add a **waiting on client** count: unacked + unsigned shared
  packets.

Without that UI, Phase 1 is only a schema.

---

## 9. Spec documents to update in the same slice

| Document | Change |
| --- | --- |
| `FRONTEND_UI_WORKFLOW_LOGIC.md` §9 | Nav = shipping 5 items. Documents = own uploads **plus** `is_client_visible`. Ask = human thread, honest copy. Next Steps consumes `home.next_action`. |
| `CLIENT_PORTAL_TESTING_GUIDE.md` | Replace "agent docs never appear" with the share rule. Add share / sign / acknowledge setup steps. Note Missing is still omitted (required-doc tracking stays the agent's job; shared packets are explicit, not a Missing counter). |
| `CLIENT_WORKSPACE_REDESIGN_PLAN.md` | Status banner: document boundary **changed** by this plan (O1). D4 still no LLM. D5 implemented in Phase 5. |
| `CLIENT_PORTAL_CHROME_QA_2026-08-17.md` | Do not rewrite history; add a pointer to this plan for operational follow-up. Extend the Playwright harness in a later pass for Sign/Ack journeys. |

Do not leave §9 claiming Payments is a sidebar item.

---

## 10. Test plan

**Backend (pytest)**

- `test_client_workspace.py` — ranker order with shared sign / ack / review /
  reply / upcoming; no keyword title rewrite.
- New share/access tests (Phase 1).
- Dashboard `?transaction_id=` 200 / 403.
- Acknowledge idempotency.

**Frontend (vitest)**

- `ClientWorkspace.test.tsx` — Home NBA CTA href; Next Steps matches Home title;
  deal switcher writes `transaction`; Ask copy; Payments button absent when
  count is 0; document row has Open.

**Browser**

- Keep `client_portal_chrome_qa.mjs` green (chrome must not regress).
- New headed/headless cases after Phase 1: share as agent → sign CTA as Bradyn;
  two-deal switcher; bell count after a staff reply.

**Manual / staff**

- Walk `CLIENT_PORTAL_TESTING_GUIDE.md` once rewritten: invite → assign → share
  doc → client completes → staff sees state.

---

## 11. Suggested PR split

| PR | Phase | Notes |
| --- | --- | --- |
| A | 1 (schema + API + staff share control + client Open/Sign/Ack) | Largest. Do not merge schema without the staff button. |
| B | 2 (single ranker + CTA targets + Next Steps) | Depends on A for document-id targets; can land ranker cleanup first if A slips. |
| C | 3 (copy) | Small, can ship with B. |
| D | 4 (deal switcher + query param) | Independent of A once Home already has `transaction_id`. |
| E | 5 (feed + bell) | Needs A for document events. |
| F | 6–7 | Payments hide + calendar + spec sync. |

---

## 12. Explicitly out of order

Do not do these first:

- LLM Ask Velvet.
- Another visual pass on the navy sidebar.
- A second dashboard endpoint for Home.
- Showing Missing document counts (still fiction for represented clients;
  sharing is explicit).
- Letting clients hard-delete shared packets.
- Auto-sharing every document on the transaction.

---

## 13. Success metric

The portal is "in the right direction" when a represented client with two
active deals can, without staff sitting next to them:

- switch deals on Home,
- open a file the agent shared,
- finish Sign or Acknowledge,
- see that completion reflected in Next Best Action,
- send a question and understand a human will reply,
- and never land on a button whose label they cannot complete.

Chrome QA staying green is necessary. Completing §6 journeys is sufficient.
