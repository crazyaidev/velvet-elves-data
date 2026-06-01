# Client Workspace — "Closing Concierge" Home Redesign Plan (rev 1)

*Drafted: 2026-05-30. Grounded in the AI-generated design Jake supplied
(`ClientPageFiles/` source + `Client_workspace_design.png`), the existing
represented-client portal (shipped per `CLIENT_WORKSPACE_PLAN.md` rev 1, 2026-05-23),
and the FSBO/Attorney sibling builds.*

> **STATUS: IMPLEMENTED 2026-05-30 (this plan).** Decisions taken: **D1** new
> `/client/home` landing + nav `Home · Timeline · Documents · Payments · Agent Info`
> (comp's Next Steps/Updates folded into Home cards); **D2** additive `home` block
> on `GET /api/v1/dashboard/client` (no new endpoint); **D3** "What Velvet Is
> Handling" derived from real deal state; **D4** "Ask Velvet" reuses the existing
> two-way `is_client_visible` thread (no new LLM — an AI answerer remains a
> separate slice); **D5** Recent Updates from client-visible comms; **D6** warm
> concierge look kept for Home via named `concierge-*` Tailwind tokens.
>
> **rev 2 (2026-05-30) — D7 REVERSED per Jake's review.** Jake wants a *pixel-exact*
> replica of the comp, so the Client portal no longer reuses `AppLayout`. A new
> **`ClientWorkspaceLayout`** reproduces the comp's own chrome exactly — the deep
> navy (`concierge-navy`) sidebar with VE branding + `Home · Next Steps · Timeline
> · Documents · Updates` nav + bottom user chip, the desktop topbar (Message Agent
> / View Timeline / Closing Day Info, on the Home), and the mobile off-canvas
> drawer + 5-slot bottom nav. The Client-only routes (`/client/home`,
> `/client/transactions`, `/client/documents`, `/client/milestones`,
> `/client/agent`) are mounted under this layout in `App.tsx`, **outside**
> `AppLayout`. "Next Steps"/"Updates" scroll to the Next Best Action / Ask Velvet
> sections on Home; Timeline→milestones, Documents→documents are real pages.
> Backend: 8 pure projections in `client_workspace.py` + a `ClientHome`
> schema, 12 new pytest cases (52 client tests green). Frontend: `ClientHomePage`
> + 8 decomposed cards under `components/client/home/`; `tsc`, `eslint`, and
> `vite build` clean. **Scope note (boundary):** the represented-client document
> surface stays own-uploads-scoped, so "Documents Needing Attention" surfaces the
> client's own uploads bounced back for review / out for signature — not
> agent-internal documents (kept the document boundary unchanged).

> **What this is.** Jake had Codex generate a brand-new, "light-hearted and warm"
> Client landing screen (`VelvetElvesClientHomeScreen.tsx`, 700 lines, all mock
> data) plus a PNG comp. The ask: **reconstruct that screen inside the real
> `velvet-elves-frontend`, wired to real data, and build the backend API that
> feeds it.** This is the first time the Client portal has an actual *design comp*
> — `CLIENT_WORKSPACE_PLAN.md` §11 #6 explicitly noted "there's no Jake/Jan Client
> design, so the bar is 'matches the FSBO portal.'" That constraint is now lifted:
> this comp **is** the design north star, and it deliberately follows the AGENTS.md
> "Client Portal Rules" (Home / Next Steps / Timeline / Documents / Updates;
> "closing concierge," not a smaller agent dashboard).

> **Relationship to the existing portal.** The rev-1 rebuild already shipped a
> *working, truthful* backend half: a canonical client→transaction resolver, real
> milestone timelines, a real document-status summary, a correct "Your agent"
> card, and a real two-way `is_client_visible` message thread. **This redesign
> keeps all of that and builds on top of it** — it is a *new presentation layer*
> (a single rich Home) plus a handful of **new derived projections** (progress %,
> next-best-action, "What Velvet is handling," recent-updates feed, documents-
> needing-attention list, multi-party Key Contacts). It is not a teardown. The
> four existing tool pages stay reachable; the Home becomes the new landing.

---

## 1. Goals

1. **Reproduce the comp faithfully** as a real, responsive page in
   `velvet-elves-frontend` — the warm navy/orange "closing concierge" look the
   client signed off on, not a restyle into the existing `ve-` tool-page chrome.
2. **Make every card tell the truth from real model state** — no card ships with
   the mock arrays still hardcoded. Each of the 9 surfaces maps to a real backend
   field or is explicitly cut for MVP (no fake zero boards, the recurring rule
   from `feedback-root-cause-over-patches`).
3. **Reuse the rev-1 backend, extend it additively.** Keep `/api/v1/dashboard/client`
   as the one canonical client read (prior plan D3); add the new Home fields to it
   rather than forking a parallel endpoint that could disagree.
4. **Hold the customer boundary.** Every new projection (updates feed, "Velvet is
   handling," contacts) must pass the same filter the rest of the portal does:
   no internal tasks, notes, AI drafts, audit chatter, or other parties' private
   data; all PII Fernet-decrypted before it leaves the service
   (`project-ve-pii-fernet-at-rest`).
5. **No new LLM call to render the page.** The "Ask Velvet" box reuses the existing
   human Q&A thread for MVP (see Decision D4); the AI-answerer is a separately
   scoped slice, not part of this reconstruction.

---

## 2. The design, deconstructed

`ClientPageFiles/src/VelvetElvesClientHomeScreen.tsx` is one screen. Stripping the
mock arrays, it is a fixed-left **navy sidebar** + a scrolling **content column**:

**Chrome**
- **Sidebar** (`#06244A`): VE logo + "Transaction OS" eyebrow; 5 nav items — Home,
  Next Steps, Timeline, Documents, Updates (icons: Home, CheckSquare, CalendarDays,
  FolderOpen, MessageSquare); a user chip at the bottom ("Sarah Anderson / Buyer
  Client"). Mobile: off-canvas drawer + a 5-slot bottom nav (Home / Steps / Docs /
  Updates / More).
- **Topbar** (`QuickActionBar`, desktop only): "Message Agent", "View Timeline",
  "Closing Day Info". Mobile header: hamburger + bell.

**Content (9 cards)**
| # | Card | Mock content in the comp |
|---|------|--------------------------|
| 1 | **Hero** | "You're Buying 123 Main Street", "Welcome back, Sarah", status chip "Inspection Period", "Closing target: June 14, 2026", "42% to closing" progress bar, "Velvet is monitoring deadlines…" |
| 2 | **Next Best Action** (tall, focal) | "Choose your inspection time", body, "Requested by: Your agent", "Estimated time: 2 minutes", buttons "Select a Time" / "Why this matters" |
| 3 | **What Velvet Is Handling** | 3 bullets: "Waiting on lender appraisal order", "Checking contract deadlines", "Monitoring signed documents" |
| 4 | **Upcoming Dates** | Inspection appointment / response deadline / appraisal target / **Closing day** (emphasized) + "Add to calendar" |
| 5 | **Recent Updates** | Timeline feed: "Agent sent inspection options · 1 hour ago", "Title company received the contract · Today", "Earnest money received · Yesterday" |
| 6 | **Documents Needing Attention** | Seller Disclosure → *Review*, Wire Fraud Notice → *Acknowledge*, Inspection Agreement → *Sign*; "Open Documents" |
| 7 | **Key Contacts** | Jessica Miller (Real Estate Agent), David Chen (Loan Officer, Summit Lending), Olivia Martinez (Title Officer); call + email buttons each |
| 8 | **Ask Velvet** (wide) | input "Ask anything about your transaction…" + send; quick prompts "What happens next?" / "What am I waiting on?" / "Explain appraisal" |

Design tokens in the comp: bg `#F5F7FB`, sidebar `#06244A`, hero `#041F42`, orange
`orange-500/600`, `rounded-3xl` cards with soft shadows, Inter font, `lucide-react`
icons, `react@19`. (Frontend target is also React 19 + Tailwind + lucide, so the
component ports cleanly.)

---

## 3. What already exists — the reuse inventory

The rev-1 build did most of the backend work. Verified in the repo:

| Capability | Where it lives | Reuse |
|---|---|---|
| Canonical client→tx resolver | `client_workspace.list_client_transaction_ids` / `assert_client_transaction_access` ([client_workspace.py:60](velvet-elves-backend/app/services/client_workspace.py#L60)) | **As-is** for every new read |
| Per-tx view: address (decrypted), status, closing_date, **key_dates**, **milestones** (done/active/upcoming + explanation), next_milestone | `build_client_transaction_view` ([client_workspace.py:278](velvet-elves-backend/app/services/client_workspace.py#L278)) | Feeds Hero, Upcoming Dates (#4), and progress (#1) |
| Document status summary (in_progress/uploaded/verified/complete) | `fetch_client_documents` + `build_documents_summary` ([client_workspace.py:116](velvet-elves-backend/app/services/client_workspace.py#L116)) | Base for Documents-needing-attention (#6) |
| "Your agent" card (owner-first, PII-decrypted, bio/company/avatar) | `resolve_agent_card` ([client_workspace.py:206](velvet-elves-backend/app/services/client_workspace.py#L206)) | First entry of Key Contacts (#7) |
| Two-way `is_client_visible` Q&A thread | `POST/GET /api/v1/client/messages` ([client_messages.py](velvet-elves-backend/app/api/v1/client_messages.py)); `useTransactionClientThread`, `ClientAskThread` | Powers Ask Velvet (#8) |
| Key-dates builder | `fsbo_workspace.build_key_dates` ([fsbo_workspace.py:387](velvet-elves-backend/app/services/fsbo_workspace.py#L387)) | Upcoming Dates (#4) |
| Milestone timeline | `fsbo_workspace.build_milestone_timeline` ([fsbo_workspace.py:404](velvet-elves-backend/app/services/fsbo_workspace.py#L404)) | Progress %, Timeline page |
| **Next-step derivation** (real, ranked, non-fabricated) | `fsbo_workspace.derive_next_steps` ([fsbo_workspace.py:474](velvet-elves-backend/app/services/fsbo_workspace.py#L474)) | Pattern for Next Best Action (#2) |
| **Counterparties** from `transaction_parties`, PII-decrypted, role-labeled (loan_officer, title_rep, …) | `fsbo_workspace.fetch_property_contacts` + `_PARTY_ROLE_LABELS` ([fsbo_workspace.py:900](velvet-elves-backend/app/services/fsbo_workspace.py#L900)) | Key Contacts beyond the agent (#7) |
| `transactions.representation_type` (`'Buyer'` default) | schema ([20260305_phase1_schema.sql:124](velvet-elves-backend/supabase/migrations/20260305_phase1_schema.sql)) | Hero "Buying" vs "Selling" (#1) |
| Client shell capability config (`client` variant, `client-owned` scope, AI bar off) | `dashboardShellConfig.ts:117` | Keep; landing route changes (Decision D1) |
| Frontend client read hook + types | `useClientDashboard` / `ClientDashboardResponse` ([useDashboard.ts:990](velvet-elves-frontend/src/hooks/useDashboard.ts#L990)) | Extend additively |

**Takeaway:** ~70% of the data the comp needs already ships. The genuinely new
backend work is 5 derived projections (§5), and most reuse existing helpers.

---

## 4. Card → data mapping (the heart of the plan)

Each comp card, the field it needs, the source, and the work:

| # | Card | Field(s) | Source | Work |
|---|------|----------|--------|------|
| 1 | Hero verb + address | `representation_type` → "Buying"/"Selling"; decrypted `address` | `transactions` (already in tx view) | **S** — add `representation_type` to tx view |
| 1 | Hero status chip | current-phase label | derive from `next_milestone.label`/`status` | **S** — `phase_label` helper |
| 1 | Hero closing target | `closing_date` | tx view ✓ | none |
| 1 | Hero progress % | `done / total` of milestone timeline | new `build_progress(timeline)` | **S** |
| 1 | Hero monitoring line | static copy | constant | none |
| 2 | **Next Best Action** | title, body, requested_by, est_minutes, cta | new `derive_client_next_action` (port of FSBO `derive_next_steps`, take top 1, client-safe copy) | **M** |
| 3 | **What Velvet Is Handling** | plain-English bullets of automated/monitored work | new `build_velvet_handling` — derived from real deal state (open milestones, pending appraisal/inspection/signature), **not** raw internal task names | **M** (Decision D3) |
| 4 | Upcoming Dates | label + date, emphasize closing | `key_dates` (tx view ✓) | **XS** — render only; tag `emphasis` on closing |
| 5 | **Recent Updates** | label + relative time | new `build_recent_updates` — client-safe events: client-visible comms + client-visible document status changes + just-completed milestones | **M** (Decision D5 on scope) |
| 6 | **Documents Needing Attention** | doc label + action (Review/Acknowledge/Sign) | new `build_documents_needing_attention` — project `documents.review_status`/`signature_status` into an action verb, scoped client-safe | **M** |
| 7 | **Key Contacts** | name, role, initials, phone, email | `resolve_agent_card` (agent) + `fetch_property_contacts` (`transaction_parties`: loan_officer, title_rep, …), PII-decrypted | **S** — merge two existing helpers |
| 8 | **Ask Velvet** | thread + send + quick prompts | `GET/POST /api/v1/client/messages` (relabel "agent"→"Velvet"); quick prompts are static starters | **S** (Decision D4) |
| — | Topbar / sidebar | nav targets | routes | **S** — Decision D1 |

Sizing: XS<1h, S≈½d, M≈1d.

**Multi-deal note.** The comp is single-transaction. A represented client *can* be
on several deals. The Home renders **one focused deal** — the nearest-closing
active transaction — with a compact deal switcher in the Hero if `transactions.length
> 1`. All cards key off that selected `transaction_id`. (The existing
`/client/transactions` list page remains the multi-deal index, reachable from the
Hero address / "View details.")

---

## 5. New backend projections (the real new work)

All additive, in `app/services/client_workspace.py`, surfaced through the existing
`GET /api/v1/dashboard/client` (Decision D2). No new LLM calls (goal #5).

### 5.1 `build_progress(timeline) -> {done, total, pct}`
`pct = round(done/total*100)` over the milestone timeline already built per tx.
0/0 → 0%. Pure function, unit-testable. Feeds Hero #1.

### 5.2 `phase_label(tx_view) -> str`
Map the active/next milestone to a short chip ("Inspection Period", "Under
Contract", "Clear to Close", "Closing Week"). Heuristic over `next_milestone.label`
+ `status`, same spirit as `_milestone_explanation`. Feeds Hero chip #1.

### 5.3 `derive_client_next_action(tx_view, docs, thread) -> NextAction | None`
Port `fsbo_workspace.derive_next_steps` to the *represented-client* lens and return
the single top-ranked action. Ranking (most-actionable first):
1. A document awaiting the **client's** signature/acknowledgement (`signature_status`
   pending on a client-visible doc) → "Sign {doc}".
2. The active milestone that names a client decision (inspection window open, option
   period) → "Choose your inspection time" etc.
3. An unanswered agent question in the thread → "Reply to your agent".
4. Else the next upcoming milestone as a soft "Here's what's next."
Each action carries `title`, `body` (plain English), `requested_by` ("Your agent" /
"Velvet"), `est_minutes`, `cta_label`, `cta_target` (a real route). **No fabricated
guidance** — each anchors to a real row, per FSBO's `derive_next_steps` discipline.
Feeds #2.

### 5.4 `build_velvet_handling(tx_view, docs) -> list[str]`
A short, plain-English list of what the platform is monitoring **on this deal**,
derived from real state — never raw internal task names (boundary). Rules e.g.:
- appraisal milestone open & not done → "Waiting on the lender's appraisal".
- any key date in the future → "Checking your contract deadlines".
- a doc in `signature_status` in-flight → "Monitoring signed documents".
Cap at 3–4. Decision D3 governs whether this is derived (recommended) or cut.
Feeds #3.

### 5.5 `build_recent_updates(tx_id, ...) -> list[{label, ts}]`
A client-safe activity feed, newest first, ≤5 items, union of:
- client-visible `communication_logs` (the same `is_client_visible` rows the thread
  shows) → "Your agent sent inspection options".
- client-visible document status transitions (uploaded/verified/complete on
  client-relevant docs) — *if* a timestamped status-event source exists; otherwise
  derive from `documents.updated_at` + status.
- just-completed milestones → "Earnest money received".
Each item gets a relative-time label client-side. Decision D5 fixes the exact
sources (and whether doc-events are in-scope for MVP). Feeds #5.

### 5.6 `build_documents_needing_attention(docs) -> list[{id, label, action, tone}]`
Filter the client's documents to those needing a **client** action and map status →
verb: `signature_status` pending → **Sign** (green); a disclosure/notice flagged for
acknowledgement → **Acknowledge** (blue); `review_status` needs the client → **Review**
(amber). Reuses `fetch_client_documents` + `classify_document_board_state`. Feeds #6.
(The existing zero-safe `documents_summary` stays for the AppLayout KPI tiles.)

### 5.7 `build_key_contacts(supabase, tx_id, client_user_id) -> list[contact]`
Merge `resolve_agent_card` (the agent, first) with `fetch_property_contacts`
(`transaction_parties` → loan officer, title rep, attorney, etc.), each projected to
`{name, role_label, initials, email, phone}` with PII decrypted via `_safe_decrypt`.
Drop the client's own row and any contactless row. Reuses
`party_role_label`/`_PARTY_ROLE_ORDER`. Feeds #7.

### 5.8 Response shape
Add a `home` block to `ClientDashboardResponse` (and the matching TS interface),
populated for the **selected** transaction:
```jsonc
"home": {
  "transaction_id": "…",
  "hero": { "verb": "Buying", "address": "123 Main Street", "status_label": "Inspection Period",
            "closing_date": "2026-06-14", "progress": { "done": 5, "total": 12, "pct": 42 } },
  "next_action": { "title": "…", "body": "…", "requested_by": "Your agent",
                   "est_minutes": 2, "cta_label": "Select a Time", "cta_target": "…" } | null,
  "velvet_handling": ["…","…"],
  "upcoming_dates": [ { "label": "Closing day", "date": "2026-06-14", "emphasis": true }, … ],
  "recent_updates": [ { "label": "…", "ts": "…" }, … ],
  "documents_needing_attention": [ { "id": "…", "label": "Seller Disclosure", "action": "Review", "tone": "amber" }, … ],
  "key_contacts": [ { "name": "…", "role_label": "Real Estate Agent", "initials": "JM", "email": "…", "phone": "…" }, … ]
}
```
`ClientDashboardResponse` is a `_Loose` model, so this is purely additive — the four
existing pages and the KPI tiles keep working unchanged. The selected-deal data is
duplicated from `transactions[selected]` for convenience but stays consistent because
it's computed from the same `build_client_transaction_view` output.

---

## 6. Decision register (recommendations; flag in the implementing PR)

- **D1 — Navigation & landing.** Adopt the comp's 5-item nav (**Home, Next Steps,
  Timeline, Documents, Updates**) and make **Home the landing**.
  *Recommended mapping:* Home → new `/client/home`; Timeline → existing
  `/client/milestones`; Documents → existing `/client/documents`; Next Steps and
  Updates → render as **anchored sections of Home** for MVP (the comp only fully
  designs Home; its other tabs are dead `setActive` state), promotable to their own
  routes later. Keep **Payments** (`/client/invoices`) and **Agent Info** reachable
  (Agent Info content now also lives in Key Contacts) — don't strand the existing
  invoice flow. Update `dashboardShellConfig` `landingRoute`/`brandDescriptor` and
  `AppLayout` `client` group accordingly.
- **D2 — One endpoint.** *Recommended:* extend `GET /api/v1/dashboard/client` with the
  `home` block (consistent with prior plan D3, "keep `/dashboard/client` canonical").
  Alternative: a dedicated `GET /api/v1/dashboard/client/home`; rejected for MVP to
  avoid two reads that can disagree.
- **D3 — "What Velvet Is Handling" source.** *Recommended:* derive a capped, plain-
  English list from real deal state (§5.4) — it reads as the AGENTS.md "invisible
  operator" without leaking internal task rows. Alternative: cut the card for MVP if
  product judges the derived list too speculative. **Do not** surface raw internal
  task names (boundary).
- **D4 — "Ask Velvet" = AI or human?** The comp's copy ("Velvet has answers") implies
  an AI assistant, but the only shipped infra is the **two-way human Q&A thread**.
  *Recommended for this reconstruction:* wire "Ask Velvet" to the existing
  `/client/messages` thread (relabel the agent-thread copy to the Velvet voice;
  quick-prompts pre-fill the composer), honoring goal #5 "no new LLM to render."
  Building a real LLM answerer (new endpoint, retrieval over deal state, cost +
  hallucination guardrails) is a **separate, explicitly-scoped slice** — flag it,
  don't smuggle it into the rebuild. This is the single biggest scope fork.
- **D5 — Recent-updates sources.** *Recommended MVP:* client-visible comms +
  completed milestones (both already client-safe). Add document status-change events
  **only if** a timestamped, client-safe event source exists; otherwise defer doc-
  events rather than mine internal audit rows. Confirm before building.
- **D6 — Visual language.** *Recommended:* preserve the comp's warm navy/orange
  "concierge" look for the **Home** surface (the client explicitly chose it), but
  route its raw hex (`#06244A`, `#041F42`, `orange-600`, `#F5F7FB`) through Tailwind
  config tokens (extend `ve-` palette) instead of scattering literals, so it stays
  themeable and lint-clean. The existing tool pages (Documents/Milestones/Payments)
  keep their current `ve-` chrome — the Home is intentionally the one warm,
  client-facing surface, exactly as AGENTS.md frames it.
- **D7 — Sidebar vs in-shell nav (carry-over of prior L1).** The Home reuses the
  **AppLayout** sidebar — it does **not** re-introduce a second in-component nav.
  The comp ships its own `<Sidebar>`; we map its nav items into the AppLayout client
  group and drop the comp's standalone sidebar to avoid the duplicate-nav defect the
  rev-1 plan fixed. (The comp's warm navy sidebar styling can be adopted by the
  AppLayout client variant if product wants the look there too — flag separately.)

---

## 7. Frontend plan

### 7.1 New page + components (`src/pages/client/`)
- **`ClientHomePage.tsx`** — port `VelvetElvesClientHomeScreen.tsx`, gutting the mock
  arrays and driving every card from `useClientDashboard().data.home`. Loading
  (skeletons), empty (no active deal), and error states added (comp has none).
- Decompose the 700-line monolith into `src/components/client/home/`:
  `HeroCard`, `NextBestActionCard`, `VelvetHandlingCard`, `UpcomingDatesCard`,
  `RecentUpdatesCard`, `DocumentsAttentionCard`, `KeyContactsCard`, `AskVelvetCard`,
  plus the comp's `StatusChip`/`IconBadge`/`Card` primitives. Mock-data-out,
  props-in (the AGENTS.md "data arrays separated from rendering" pattern, inverted
  to props).
- Reuse `ClientAskThread` ([components/client/ClientAskThread.tsx](velvet-elves-frontend/src/components/client/ClientAskThread.tsx)) inside `AskVelvetCard`
  (Decision D4) rather than building a second composer.

### 7.2 Wiring
- Extend `ClientDashboardResponse` + add `ClientHome*` interfaces in
  `useDashboard.ts` to match §5.8.
- Hero deal-switcher when `transactions.length > 1`; otherwise the lone deal.
- Card CTAs target real routes: "Open Documents" → `/client/documents?transaction=`,
  "View Timeline"/"Select a Time" → milestones / the next-action target, contact
  call/email → `tel:`/`mailto:`.

### 7.3 Routing & nav
- Add `ROUTES.CLIENT_HOME = '/client/home'`; register `ClientHomePage` (RoleRoute
  `['Client']`) in `App.tsx`; set it as `landingRoute`/`redirectRoute` for Client.
- Rewrite the `AppLayout` `client` nav group per Decision D1.
- Mobile bottom nav: the comp's pattern is fine but the project already has an
  AppLayout mobile treatment — adopt one, don't ship two (carry-over of the
  duplicate-nav lesson).

### 7.4 Design tokens
- Extend `tailwind.config.js` with the concierge palette (Decision D6); replace raw
  hex in the ported component with tokens. Inter is already the project font.

---

## 8. Backend plan

1. Add the §5 helpers to `client_workspace.py` (all pure or single-query, unit-
   testable; reuse `build_key_dates`, `build_milestone_timeline`,
   `derive_next_steps` shape, `fetch_property_contacts`, `resolve_agent_card`).
2. Select the focused transaction (nearest active closing) and assemble the `home`
   block in `get_client_dashboard` ([dashboard_role.py:660](velvet-elves-backend/app/api/v1/dashboard_role.py#L660)).
3. Extend `ClientDashboardResponse` in `schemas/dashboard_role.py` with a typed
   `home` sub-model (keep `_Loose` so it stays forward-compatible).
4. **No** new endpoint (D2). "Ask Velvet" keeps using `/api/v1/client/messages`.
5. Boundary tests (§9). PII decrypt on every name/email/phone/address.

---

## 9. Verification checklist

**Frontend**
- `npx tsc --noEmit -p tsconfig.app.json` and `eslint` clean on changed files.
- No mock array from the comp survives (grep: `velvetTasks`, `quickPrompts` literals
  gone; `dates`/`updates`/`documents`/`contacts` come from props).
- Single navigation system (AppLayout sidebar only — no second in-component nav).
- Loading / empty (no active deal) / error states render.
- Every CTA resolves to a real route or `tel:`/`mailto:` (no dead buttons — the comp
  ships all 9 cards with no handlers).
- Responsive at desktop / tablet / mobile incl. the bottom nav.

**Backend**
- `venv/Scripts/python.exe -m pytest app/tests -k "client"` passes, adding:
  progress math (done/total/0-0); next-action ranking picks the real top item;
  `velvet_handling`/`recent_updates` exclude internal/non-client-visible rows;
  documents-needing-attention only lists client-actionable docs; key-contacts merges
  agent + parties, drops the client's own row, **no `gAAAAAB…` ciphertext** in any
  field; `home` block scoped to the current client only; cross-client 403 unchanged.

**Manual QA, logged in as a Client**
- Home matches the comp; the warm look renders; the right deal is focused (and the
  switcher appears with >1 deal).
- Hero verb matches `representation_type`; progress % matches the timeline; chip
  reflects the live phase.
- Next Best Action points at a *real* pending item with a working CTA.
- Documents-needing-attention lists only the client's actionable docs with the right
  verb; "Open Documents" deep-links.
- Key Contacts shows the real agent + real parties (loan officer/title) with working
  call/email; no other client's data.
- Ask Velvet sends into the real thread and shows replies (Decision D4).
- No internal tasks / notes / AI drafts / audit chatter / other-party PII anywhere;
  boundary notice present.

---

## 10. Execution order (~4.5 dev days + QA)

- **Phase A — Tokens + static shell (~0.5d).** Tailwind concierge palette;
  `ClientHomePage` scaffold + decomposed card components rendering against a typed
  mock that matches §5.8 (so frontend/backend can proceed in parallel). Routing +
  nav rewrite (D1). **Exit:** page renders pixel-close to the comp on mock; one nav.
- **Phase B — Backend projections (~1.5d).** §5 helpers + `home` assembly + schema +
  tests. **Exit:** `/dashboard/client` returns a real `home` block; boundary tests
  green.
- **Phase C — Wire cards to live data (~1.0d).** Replace the mock with
  `useClientDashboard`; loading/empty/error; CTAs to real routes; deal switcher.
  **Exit:** every card live; no mock arrays left.
- **Phase D — Ask Velvet + Recent Updates + polish (~1.0d).** Thread reuse (D4);
  updates feed (D5); responsive/mobile-nav pass; a11y labels (comp already labels
  icon buttons — preserve). **Exit:** thread round-trips; feed shows real events.
- **Phase E — Doc reconciliation + QA (~0.5d).** Note the redesign in
  `FRONTEND_UI_WORKFLOW_LOGIC.md` §9 and `SYSTEM_DESIGN.md` (new Home landing, nav
  set, `home` block). Manual QA per §9; screenshots in the PR.

---

## 11. Risks & open questions

1. **D4 (Ask Velvet AI vs thread)** is the biggest fork — confirm before Phase D. The
   recommendation (reuse the human thread, no new LLM) keeps scope honest; an AI
   answerer is a separate project.
2. **"What Velvet is handling" (D3)** and **recent-updates doc-events (D5)** risk
   feeling fabricated or leaking internals if mined from the wrong source. Both are
   derived from already-client-safe state in the recommendation; if product wants
   richer feeds, scope them explicitly rather than widening the query into internal
   tables.
3. **`transaction_parties` coverage.** Key Contacts is only as rich as the parties
   actually recorded on a deal; many deals may have just the agent. The card must
   render gracefully with 1 contact (no empty "Loan Officer" placeholder).
4. **Buyer/Seller detection.** Driven by `transactions.representation_type`; confirm
   its real values (`Buyer`/`Seller`/`Dual`) and the verb for `Dual` before shipping
   the Hero copy.
5. **Multi-deal focus.** "Nearest active closing" is a heuristic; verify it picks the
   deal a client expects when they have several, and that the switcher is discoverable.
6. **Visual divergence (D6).** The warm Home now looks different from the other client
   tool pages. That's intentional and matches AGENTS.md, but flag it so product isn't
   surprised by the seam between Home and Documents/Milestones.

---

## 12. Cross-references

- `ClientPageFiles/` + `Client_workspace_design.png` — the comp being reconstructed.
- `ClientPageFiles/AGENTS.md` — the Client Portal Rules the comp follows (nav set,
  concierge framing, "Ask Velvet," card patterns).
- `CLIENT_WORKSPACE_PLAN.md` (rev 1) — the shipped backend this builds on (resolver,
  agent card, thread, doc summary, projections).
- `CLIENT_WORKSPACE_UI_BUILD_PLAN.md` — the staff-side Client access + Q&A drawer that
  the same `is_client_visible` thread powers.
- `FSBO_WORKSPACE_PLAN.md` — sibling portal; source of `derive_next_steps`,
  `fetch_property_contacts`, `build_key_dates`, milestone timeline reused here.
- `FRONTEND_UI_WORKFLOW_LOGIC.md` §9 / `SYSTEM_DESIGN.md` — reconcile in Phase E.
- `STYLE_GUIDE.md` — token system to extend (D6).
- Feedback memories: `feedback-root-cause-over-patches`, `project-ve-pii-fernet-at-rest`,
  `feedback-cost-effective-llm`, `feedback-alert-card-clickability`,
  `feedback-design-benchmarks`.

---

*Plan drafted 2026-05-30 (rev 1), grounded in the supplied comp, the shipped rev-1
Client backend, and the FSBO/Attorney sibling builds.*
