# Milestone 5.1 — Role-Specific Dashboards
## Comprehensive Implementation Plan

| | |
| --- | --- |
| Milestone | **5.1 — Role-Specific Dashboards** (Week 17, 2026-06-29 → 2026-07-05) |
| Phase | Phase 5 — Dashboards, Payments & Profiles |
| Plan version | 1.1 (2026-05-18 post-review corrections) |
| Authoritative sources | `milestones.txt` §5.1 · `FRONTEND_UI_WORKFLOW_LOGIC.md` §3, §8, §9, §10, §11 · `SYSTEM_DESIGN.md` §3.2 (Role-Specific Dashboard Landing Pages, §3.3 Permission Matrix), §4.1, §4.3.1c–§4.3.1f, §4.4 · `STYLE_GUIDE.md` (all sections) |
| Approved HTML references | `completed_designs/ve-homepage_dashboard-solo_agent.html`, `ve-homepage_dashboard-team_leader.html`, `ve-attorney_dashboard.html`, `ve-fsbo_dashboard.html` |
| Visual-consistency anchors | Active Transactions workspace (`/transactions`), All Documents (`/documents`), AI Email Review (`/ai-emails`) |

---

## 1. Executive Summary

Milestone 5.1 ships the **landing-page** experience for every authenticated role in Velvet Elves. The Active Transactions workspace built in Milestone 2.4 is the operating surface; this milestone gives each role a **role-shaped entry point** that:

1. Orients the user the moment they sign in (what matters today, what's drifting, what's healthy).
2. Concentrates the next physical action (upload intake, sign-off checkbox, share milestone, etc.) above the fold.
3. Deep-links into the Active Transactions workspace and other existing tools — **no dead-end pages**, no parallel data stores.
4. Enforces the AI-vs-human guardrails described in `milestones.txt` (especially Attorney) and the customer-facing tone described in `FRONTEND_UI_WORKFLOW_LOGIC.md` §8 (FSBO).

The shared shell, KPI tiles, AI briefing chip, command-grid primitives, and "+ New Transaction" plumbing already exist (Milestones 2.3, 2.4, 3.1–3.3, 4.1–4.3). What is still missing — and what this milestone delivers — is:

- The **dashboard router** (`/dashboard`) that hands the user to the correct landing page by role.
- The **role-specific pages** themselves (`/dashboard/agent`, `/dashboard/team`, `/dashboard/attorney`, `/dashboard/admin`, `/fsbo`, `/client/transactions`, vendor document portal).
- The **aggregation endpoints** declared in `SYSTEM_DESIGN.md` §3.2 (`/api/v1/dashboard/{agent,team,attorney,admin,fsbo}/...`) plus a small set of supporting endpoints (`/api/v1/dashboard/health-score`, secure share-link CRUD, client messaging, vendor document/request feed).
- The **public milestone viewer** (`/milestones/:shareToken`) required by `FRONTEND_UI_WORKFLOW_LOGIC.md` §12.1. The repo currently contains RLS carveout documentation for share tokens but no public route/page/API, so the viewer is now explicitly in scope.
- The **reporting view in `/profile`** for task completion rates and transaction metrics (per milestones.txt §5.1 final bullet).
- A **customizable widget / chart layer** (KPI tiles + interactive charts) reused across Solo Agent, Team Leader, and Admin dashboards. Chart tooling is added in this milestone because `recharts` is not currently bundled.

The plan below is exhaustive: every Milestone 5.1 deliverable in `milestones.txt` and every requirement in `FRONTEND_UI_WORKFLOW_LOGIC.md` §3/§8/§9/§10 maps to an explicit workstream item, file path, API contract, and acceptance test.

---

## 2. Scope

### 2.1 In scope — `milestones.txt` §5.1 deliverables

| # | Deliverable | Workstream |
| --- | --- | --- |
| 1 | Solo Agent Dashboard landing page (per approved design) | §6.B · Slice 2 |
| 2 | Team Leader Dashboard landing page (per approved design) | §6.C · Slice 2 |
| 3 | Attorney Dashboard landing page (per approved design) | §6.D · Slice 3 |
| 4 | FSBO Customer Workspace landing + 5 sub-pages (per approved design) | §6.E · Slice 4 |
| 5 | Admin dashboard (system-wide user mgmt, AI threshold, task add/remove stats, defaults) | §6.F · Slice 5 |
| 6 | Client dashboard (milestones, documents, communication) | §6.G · Slice 4 |
| 7 | Vendor document portal / open-request view (document-scoped, no task/timeline exposure) | §6.H · Slice 4 |
| 8 | Customizable widgets and interactive charts/KPIs | §6.I · §8 |
| 9 | Reporting dashboard inside profile (task completion rates, transaction metrics, search & sort) | §6.J · Slice 5 |
| 10 | Public Milestone Viewer (`/milestones/:shareToken`) + share-token backend | §5.N · §6.K · Slice 4 |

### 2.2 Explicitly excluded (do **not** scope-creep)

- **AI Coach paid add-on** ($79/agent/month) — feature-flagged placeholder only on the Team Leader sidebar / Intelligence section, as `milestones.txt` §5.1 NOTE and Key Dependencies & Risks #7 require.
- **Payment widgets / Stripe surface** — owned by Milestone 5.2.
- **Profile editor enhancements** beyond the Reporting tab — owned by Milestone 5.3.
- **Brokerage profile** (multi-team aggregation) — Milestone 5.3.
- **Mobile native shell** — post-MVP.
- **MLS integration** — deferred per `milestones.txt` Key Dependency #5.

### 2.3 Boundary with adjacent milestones

| Provides upstream of 5.1 | Already shipped |
| --- | --- |
| Shared internal shell (sidebar, topbar, AI briefing chip, KPI tiles) | M2.3 / M2.4 (`AppLayout.tsx`) |
| Active Transactions workspace + aggregation endpoints | M2.4 (`/api/v1/dashboard/{ai-briefing, sidebar-kpis, deal-state-counts, transaction-cards, transaction-tab-counts, ai-chat}`) |
| Shared dashboard primitives | `components/shared/{CommandGrid, HeroCard, MetricCard, InnerPanel, HealthScoreRing, UploadIntakeCard, KpiTile, AiBriefingBadge, PortfolioCard, MatterCard, MilestoneTimeline}` |
| `+ New Transaction` modal, drag-anywhere file drop, AI parsing | M2.4 / M3.1 / M3.2 (`IntakeContext.startIntake(files)`, `openNewTransaction(files?)`, `NewTransactionModal`, `/api/v1/ai/parse-document/{id}`) |
| AI provider abstraction, confidence settings, audit logging | M3.1 / M1.3 |
| Notification preferences, in-app notifications, vendor proposals | M4.1 / M4.2 / M4.3 |
| Transaction history timeline, AI chat panel, milestone bar | M2.1 / M2.4 |
| Closing checklist printing | M2.4 / `printClosingChecklist` |

| Consumed downstream of 5.1 | Owned by |
| --- | --- |
| Stripe payments widget on each dashboard | M5.2 |
| Brokerage / profile checklist editors | M5.3 |
| White-label re-themed dashboards | M6.1 |

---

## 3. Foundation Audit (what exists vs. what we add)

### 3.1 Backend — current state

| Existing | Notes |
| --- | --- |
| `app/api/v1/dashboard.py` (~3.4k lines) | Covers Active Transactions workspace: `ai-briefing`, `sidebar-kpis`, `deal-state-counts`, `transaction-cards`, `transaction-tab-counts`, `documents-ai-briefing`, `documents-priority-queue`, `ai-chat`. **No role-specific landing endpoints yet.** |
| `app/api/v1/transactions.py`, `tasks.py`, `documents.py` | Provide the primitives we aggregate. |
| `app/services/ai_service.py`, `ai_next_step_cache.py`, `ai_documents_briefing_cache.py` | AI provider abstraction + cached next-step copy. Reusable for health-score commentary. |
| `app/services/closing_checklist.py`, `task_notification_service.py` | Reusable for FSBO/Client guidance generation. |
| `app/models/enums.py::UserRole` | Includes all 8 roles: Agent, TC (`TransactionCoordinator`), TeamLead, Attorney, Admin, Client, ForSaleByOwner, Vendor. |
| Audit log + Fernet PII encryption (`_safe_decrypt`) | All new endpoints must reuse `_safe_decrypt` before exposing any PII (per project memory `project_ve_pii_fernet_at_rest.md`). |

| Missing — we build | Notes |
| --- | --- |
| `GET /api/v1/dashboard/agent/*` (hero, production, priority-cards, intelligence) | §5.A |
| `GET /api/v1/dashboard/team/*` (intervention, performance, drift, intelligence) | §5.B |
| `GET /api/v1/dashboard/attorney/*` (queue, hero, matter-cards, state-rules) | §5.C |
| `GET /api/v1/dashboard/admin` (system metrics + AI summary) | §5.D |
| `GET /api/v1/dashboard/fsbo/*` (overview, properties, documents, milestones, share-link CRUD) | §5.E |
| `GET /api/v1/dashboard/client` (milestones, documents, communication highlights) | §5.F |
| `GET /api/v1/dashboard/vendor` (vendor-owned uploads + open document/date requests only; no task/timeline feed) | §5.G |
| `POST /api/v1/attorney/approve`, `release-packet`, `PATCH /matters/{id}`, `GET /releases`, `GET /state-rules`, `GET /recording-calendar` | §5.C.5 |
| `app/api/v1/milestones.py` public router (`GET /api/v1/milestones/shared/{token}`, `POST /viewed`) | §5.N |
| `GET /api/v1/analytics/profile-report` (task completion rates + transaction metrics, scoped to current user) | §5.H |
| `GET /api/v1/users/me/dashboard-layout`, `PUT` (per-user widget order & visibility) | §5.I |
| `app/services/health_score_service.py` | Single source of truth for portfolio / team / legal / customer health scoring. §5.K |
| `app/services/dashboard_aggregator.py` | Reusable aggregator that reads from the existing `dashboard.py` helpers (stage pill, why-badges, fast-filter counts) to avoid duplicate logic. §5.L |
| `app/services/share_link_service.py` + share-link table/model/repository | Stores only token hashes, emits raw token once, records viewer-open notifications. §5.N |

### 3.2 Frontend — current state

| Existing | Notes |
| --- | --- |
| `src/layouts/AppLayout.tsx` | Role-aware sidebar (KPI tiles, deals/workflow/intelligence sections, attorney + FSBO variants), topbar with AI briefing chip, `+ New Transaction` CTA, global search palette, notification panel. **Needs correction for 5.1:** the current shell is only partially portal-aware, and CTA visibility must move to a role/capability map so TC can create transactions, Attorney gets legal-packet upload, and Client/Vendor see no transaction-creation CTA. |
| `src/pages/DashboardPage.tsx` | Generic placeholder dashboard (greeting, my-tasks, upcoming closings). **To be retired / repurposed as a router fallback.** |
| `src/components/shared/*` | `CommandGrid`, `HeroCard`, `MetricCard`, `InnerPanel`, `HealthScoreRing`, `UploadIntakeCard`, `KpiTile`, `AiBriefingBadge`, `PortfolioCard`, `MatterCard`, `MilestoneTimeline`, `SearchPalette`, `NotificationsPanel`, `TransactionCard`. All conform to the style guide (Lora serif titles, IBM Plex Sans body/IBM Plex Mono kicker, `ve-*` tokens, `rounded-md`/`rounded-xl` cards). |
| `src/components/active-transactions/{NewTransactionModal, AIChatPanel, DocumentsModal, HistoryPanel, AddTaskModal, AddContactModal, DateEditPopover, CommunicationsPanel}` | Reused by every internal dashboard so the user has one set of modals across the product. |
| `src/contexts/{IntakeContext, AiChatContext, AuthContext, ThemeContext}` | Reused. The intake context exposes `startIntake(files)` for the confirmation flow and `openNewTransaction(files?)` for direct wizard entry. Dashboard upload cards must use those signatures exactly. |
| `src/hooks/useDashboard.ts` | Exports `useSidebarKpis`, `useAiBriefing`, `useDealStateCounts`, `useTransactionCards`, `useTransactionTabCounts`. We extend with `useAgentDashboard`, `useTeamDashboard`, `useAttorneyDashboard`, `useAdminDashboard`, `useFsboDashboard`, `useClientDashboard`, `useVendorDashboard`, `useHealthScore`, `useDashboardLayout`. |
| `src/utils/constants.ts::ROUTES` | Routes for `DASHBOARD`, transactions, admin, intelligence, etc. We add `DASHBOARD_AGENT`, `DASHBOARD_TEAM`, `DASHBOARD_ATTORNEY`, `DASHBOARD_ADMIN`, FSBO sub-routes, client sub-routes, vendor portal. |
| `src/pages/users/UserProfilePage.tsx` | Currently not tabbed; renders `ProfileCard` + `UserForm`. The Reports deliverable must first add a profile tab shell or intentionally mount reports under `/reports` and link from profile. |
| `package.json` | No `recharts`, `cypress`, or `axe-core` dependency exists today. Any chart/E2E/a11y tooling in this plan must be installed/configured in Slice 0 before use. |

| Missing — we build | Notes |
| --- | --- |
| `src/pages/dashboards/SoloAgentDashboardPage.tsx` | §6.B · Slice 2 |
| `src/pages/dashboards/TeamLeaderDashboardPage.tsx` | §6.C · Slice 2 (+ Agent Drill-Down Drawer) |
| `src/pages/dashboards/AttorneyDashboardPage.tsx` | §6.D · Slice 3 (+ State Rules modal, Send Packet modal) |
| `src/pages/dashboards/AdminDashboardPage.tsx` | §6.F · Slice 5 |
| `src/pages/fsbo/{FsboOverviewPage, FsboPropertiesPage, FsboPropertyDetailPage, FsboDocumentsPage, FsboMilestonesPage, FsboSharingPage, FsboAskAiPage}.tsx` | §6.E · Slice 4 |
| `src/pages/client/{ClientTransactionsPage, ClientDocumentsPage, ClientMilestonesPage, ClientAgentInfoPage}.tsx` | §6.G · Slice 4 |
| `src/pages/vendor/VendorDocumentPortalPage.tsx` | §6.H · Slice 4 |
| `src/pages/public/MilestoneViewerPage.tsx` | §6.K · Slice 4 |
| `src/pages/dashboards/DashboardRouter.tsx` | Workstream Slice 1 — replaces current `DashboardPage` at `/dashboard`; redirects by role. |
| `src/layouts/dashboardShellConfig.ts` (or equivalent helper) | Central role/capability map for dashboard shell variant, primary CTA, sidebar sections, search scope, and notification scope. |
| `src/components/dashboard/{ActionQueueList, DriftDiagnostics, FastFilterStack, PipelineSnapshot, TransactionOverviewTiles, PriorityTransactionList, AiPortfolioIntel, AgentBoard, AgentDrillDownDrawer, AttorneyMatterCardStack, StateRulesModal, SendPacketModal, FsboPortfolioStrip, FsboPropertyTimeline, ShareMilestoneModal, PlainEnglishGuide, AdminQuickActions, AdminAuditPreview, WidgetOrderManager}.tsx` | One small file per concern; everything composed from `components/shared/*`. |
| `src/components/dashboard/charts/{ClosingsByMonthChart, RevenueTrendChart, TaskCompletionChart, TransactionTypeDonut, AiAcceptanceChart}.tsx` | Wrap Recharts with `ve-*` tokens. §8 |
| Profile "Reports" tab content | §6.J · Slice 5 |

### 3.3 Reusable design fragments anchored to the reference pages

| Pattern | Source we copy | Where we apply it |
| --- | --- | --- |
| Page header: breadcrumb · Lora serif title · mono count pill · right-aligned action buttons | `TransactionListPage.tsx` lines ~697–784 | Every dashboard page header |
| Filter tab bar with `border-b-[2.5px]` active orange | `TransactionListPage.tsx` lines ~787–800 | Attorney filter tabs · FSBO portal tabs · Profile Reports tabs |
| Card flavor (default `rounded-xl border border-ve-border bg-white shadow-card`, hero `rounded-2xl border border-ve-border bg-gradient-to-br from-white to-ve-orange-soft/15`) | `STYLE_GUIDE.md` §6.3, `CommandGrid.HeroCard` | All hero / metric cards |
| AI-touched surface: champagne wash + `ve-orange` accent + `Sparkles` icon | `AiEmailReviewPage.tsx` (KIND_TONE) / `UploadIntakeCard` | "AI-prepared next step", "AI suggestions strip", "Ask Velvet Elves AI" |
| Confidence triad (`bg-emerald-50/700`, `bg-amber-50/700`, `bg-rose-50/700`) | `AiEmailReviewPage.tsx` confidence pills | Attorney AI-prepared confidence badge, FSBO AI guidance badge |
| Empty-state card: 1.5 px dashed champagne border, `bg-ve-orange-soft/15`, single explanatory sentence | `STYLE_GUIDE.md` §11 | Every "no matters / no properties / no pending tasks" surface |
| Status pill triad (`bg-ve-{red,amber,green,blue,purple}-bg` + matching `*-border` + `*-text`) | `STYLE_GUIDE.md` §2.3, `MatterCard`, `PortfolioCard` | Action queue items, matter cards, portfolio chips |
| Mono uppercase kicker + Lora serif title | `STYLE_GUIDE.md` §3.2 | Every dashboard card head (`✦ TODAY · 9:14 AM`, `Start here. Three deals need intervention.`) |
| Skeleton + retry-on-error pattern | `DashboardPage.tsx` (current), `TransactionListPage` | All dashboard fetches |

---

## 4. Architecture Overview

### 4.1 Routing

| Route | Page component | Allowed roles | Redirect rule |
| --- | --- | --- | --- |
| `/dashboard` | `DashboardRouter` | All authenticated | Redirects per `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.1 |
| `/dashboard/agent` | `SoloAgentDashboardPage` | `Agent` (no `team_id`), `TransactionCoordinator` (standalone) | Has `team_id` → `/dashboard/team` |
| `/dashboard/team` | `TeamLeaderDashboardPage` | `TeamLead`, `Agent`/`TC` with `team_id` | Without `team_id` → `/dashboard/agent` |
| `/dashboard/attorney` | `AttorneyDashboardPage` | `Attorney` | Other → `/dashboard` |
| `/dashboard/admin` | `AdminDashboardPage` | `Admin` | Other → `/dashboard` |
| `/fsbo` | `FsboOverviewPage` | `ForSaleByOwner` | Other → `/dashboard` |
| `/fsbo/properties`, `/fsbo/properties/:id`, `/fsbo/documents`, `/fsbo/milestones`, `/fsbo/share`, `/fsbo/ask-ai` | FSBO sub-pages | `ForSaleByOwner` | Other → `/dashboard` |
| `/client/transactions`, `/client/documents`, `/client/milestones`, `/client/agent` | Client portal | `Client` | Other → `/dashboard` |
| `/client/documents` | `VendorDocumentPortalPage` when `role=Vendor`; `ClientDocumentsPage` when `role=Client` | `Vendor`, `Client` | Other → `/dashboard` |
| `/portal/vendor` | Redirect alias to `/client/documents` | `Vendor` | Other → `/dashboard` |
| `/profile?tab=reports` | `UserProfilePage` (new Reports tab) | All authenticated | — |
| `/milestones/:shareToken` | `MilestoneViewerPage` | Public | Invalid/expired token → friendly expiry page |

The dashboard router is **pure redirect** (no UI) so a refresh always lands on a real page and avoids the placeholder "Dashboard" page becoming load-bearing.

Routing is based on identity, not data volume. An `Agent` or `TransactionCoordinator` with a `team_id` always lands on `/dashboard/team`; if the team has zero transactions, that page renders a team-empty state and can default the view toggle to "My Deals." It must not fall back to `/dashboard/agent`, because that contradicts `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.1 and hides team membership.

Shell behavior is also identity-based. Add one central dashboard shell configuration with at least: `shellVariant`, `sidebarSections`, `primaryCta`, `canCreateTransaction`, `searchScope`, and `notificationScope`. Required CTA outcomes:
- `Agent`, standalone `TransactionCoordinator`, and team-member `TransactionCoordinator` can open the New Transaction flow.
- `TeamLead` gets the team dashboard CTA set plus New Transaction when the existing permission matrix allows it.
- `Attorney` does **not** get New Transaction; the primary CTA is Upload Legal Packet and routes through the legal-packet intake.
- `Client` and `Vendor` get no transaction-creation CTA. Vendor search/navigation stays document/request-scoped.
- `ForSaleByOwner` replaces New Transaction with Share milestones / Ask AI actions.

### 4.2 Data flow per dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ FE: dashboard page mounts                                   │
│    ↓                                                         │
│ react-query hook (e.g. useAgentDashboard)                    │
│    ↓ GET /api/v1/dashboard/agent (single aggregated payload) │
│    ↓                                                         │
│ BE: app/api/v1/dashboard_role.py                             │
│   1. Auth → User; role check                                 │
│   2. dashboard_aggregator.fetch_agent(user)                  │
│       ├─ health_score_service.compute_portfolio(user)        │
│       ├─ existing _fetch_assigned_transaction_ids            │
│       ├─ existing stage_pill / why-badges helpers             │
│       ├─ tasks repo for overdue / due-today                  │
│       ├─ documents repo for missing-doc concentration         │
│       └─ communication_logs repo for 72h staleness            │
│   3. ai_next_step_cache for action-queue copy (cached 24h)   │
│   4. _safe_decrypt all PII before serialization              │
│   5. Pydantic AgentDashboardResponse                         │
│    ↓                                                         │
│ FE caches via react-query, populates command grid             │
└─────────────────────────────────────────────────────────────┘
```

Every page issues **one primary aggregation call** plus the three existing sidebar/topbar calls (`sidebar-kpis`, `ai-briefing`, `deal-state-counts`) the shell already triggers. We deliberately collapse what `SYSTEM_DESIGN.md` §3.2 lists as 4 separate endpoints per role into one aggregated response per role — fewer round-trips, simpler skeleton states. The 4-endpoint split in the design doc remains accurate for *resource granularity* (we can issue them piecemeal for partial refresh) but the default UI call is the umbrella `/dashboard/{role}` endpoint defined in §5 below.

### 4.3 Permissions

The `SYSTEM_DESIGN.md` §3.3 permission matrix already pins every dashboard cell. We enforce in three layers:

1. **Exact route guard** (FE) — add a `RoleRoute allowedRoles=[...]` wrapper for identity-specific dashboards/portals. Do **not** use `ProtectedRoute requiredRole` alone here because the current helper is hierarchy-based (`Admin` satisfies `Agent`, `TeamLead` satisfies `Agent`/`TC`, and `Attorney` has the same numeric level as `Agent` in `ROLE_LEVEL`).
2. **Exact API guard** (BE) — add `require_exact_roles(*roles)` in `app/core/auth.py` for dashboard identity endpoints. Keep existing `require_role(...)` only for permission-style mutations where hierarchy is intended.
3. **RLS / tenant filters** (DB + repository) — already in place from Milestone 1.2 and later hardening. We only consume rows the current user is authorized to read, and new public share-token reads stay behind an app-level token check on a service-role carveout.

Any cross-role bleed (e.g. an Agent attempting `/dashboard/team` without a `team_id`) returns **403** from the API and the FE soft-redirects.

### 4.4 AI guardrails (`milestones.txt` §5.1 + §3.4 Attorney rules)

| Surface | What AI may do | What AI must NOT do |
| --- | --- | --- |
| Solo Agent / Team Leader hero card | Compute health score, prioritize action queue, draft next-step copy (cached 24 h via `ai_next_step_cache`), summarize drift | Auto-send communications, auto-create transactions, auto-complete tasks |
| Attorney hero / matter cards | Compare settlement-statement versions, extract deadlines, index exhibits, draft transmittal language, summarize comms — every AI output rendered with the orange-bordered "AI-prepared" treatment + confidence badge | Determine legal equivalence; release packet; approve same-day disbursement; auto-check any sign-off checkbox |
| FSBO "Ask Velvet Elves AI" | Plain-English glossary, milestone explanation, next-decision summary, document-requirement explanation | Provide legal advice; act as agent; execute workflow actions; modify documents; share data outside the customer's own scope |
| Admin AI summary | Display approval/usage stats; recommend confidence-threshold tweaks (read-only suggestion) | Mutate confidence settings or tenant config automatically |
| Client dashboard | Surface AI-derived next-step blurb and message-summary guidance (display only) | Take any autonomous action, expose internal communication logs, send messages without a user click |
| Vendor document portal | Surface request-format guidance such as "Reply with: Scheduled: YYYY-MM-DD" | Show internal tasks/timelines, expose full document center, mutate task dates directly, send autonomous replies |

Implementation: every AI-generated string is rendered through the existing AI surface treatment (`ve-orange-soft` background, `Sparkles` icon, `ve-orange` accent) — never plain body text — and every AI button routes through human confirmation (mirrors `AiEmailReviewPage` "Approve / Edit & Send").

---

## 5. Workstream A — Backend Aggregation Endpoints

Every endpoint below lives in **`app/api/v1/dashboard_role.py`** (one new router file mounted under `/api/v1/dashboard/...`) or in **`app/api/v1/attorney.py`** (new, for write actions). Shared helpers move into **`app/services/dashboard_aggregator.py`** and **`app/services/health_score_service.py`**. Existing dashboard helpers in `app/api/v1/dashboard.py` (stage pill, why badges, `_safe_decrypt`, `_fetch_assigned_transaction_ids`) are extracted to a `dashboard_common.py` module — **no logic duplication**.

### 5.A Solo Agent — `GET /api/v1/dashboard/agent`

**Pydantic response** (`app/schemas/dashboard_agent.py`):

```python
class AgentDashboardResponse(BaseModel):
    health_score: int          # 0–100
    health_descriptor: str     # "Strong — 2 items need attention"
    health_delta: int          # -3 since yesterday
    action_queue: list[ActionQueueItem]        # ranked, top 5
    drift_diagnostics: list[DriftRow]          # 3–4 rows, each (count, color, label)
    fast_filter_counts: FastFilterCounts       # critical, missing_response, stale_comm, doc_blockers
    production_snapshot: ProductionSnapshot    # pending_gci, pending_volume, ytd, lifetime, active_count
    transaction_overview: TransactionOverview  # closing_this_week, in_inspection, documents_needed (with $$$)
    priority_transactions: list[PriorityTxCard]  # top 3 cards w/ next-step + key tasks/dates/contacts
    ai_intelligence: list[IntelCard]           # portfolio insights, missing-doc concentration, comms highlights
    refreshed_at: datetime
```

**Compute strategy**:

- `health_score` ← `health_score_service.compute_for_user(user, scope='personal')`. Formula (deterministic + bounded): start at 100; subtract weighted penalties for overdue tasks, stale comms, missing docs, approaching closings without CTC, AI-flagged risks. Reuses `_count_overdue`, `compute_stage_pill`, `_compute_why_badges` from `dashboard.py`. Capped to 0–100. Daily delta cached in `user_metric_snapshots` (new lightweight table; see §5.M).
- `action_queue` ← top 5 transactions ordered by an urgency score (`stage_pill ∈ {red, amber}` × `days_to_close` × `next-step age`). For each item we surface the cached AI next-step (`transactions.ai_next_step_text` already populated by `_background_refresh_ai_next_steps`) with rule-based fallback.
- `production_snapshot` ← currency math reusing `pipeline_value` from sidebar-kpis (active sum), `ytd_closings`/`lifetime_closings` from `transactions` where `status = 'Closed'`, plus stored agent `commission_pct` (optional, default 3 %).
- `priority_transactions` ← reuses `dashboard_transaction_cards`'s mapper with `limit=3` and an "agent-priority" sort key.
- `ai_intelligence` ← rule-based generator that promotes the largest drift category to a card, with one optional LLM polish call (cached). Falls back gracefully when no AI provider is configured.

**Performance budget**: ≤ 350 ms P95. Single DB round-trip via Supabase JOIN through `_fetch_assigned_transaction_ids`. Aggregator caches the AI-polished string for 1 hour.

**Granular sub-endpoints** (kept for partial refresh, per `SYSTEM_DESIGN.md` §3.2):
- `GET /api/v1/dashboard/agent/hero`
- `GET /api/v1/dashboard/agent/production`
- `GET /api/v1/dashboard/agent/priority-cards`
- `GET /api/v1/dashboard/agent/intelligence`

These share the same aggregator and are mounted as `?slice=hero|production|priority|intelligence` shortcuts on the umbrella endpoint to keep the router file thin.

### 5.B Team Leader — `GET /api/v1/dashboard/team`

```python
class TeamDashboardResponse(BaseModel):
    team_health_score: int
    team_health_descriptor: str
    intervention_queue: list[InterventionItem]      # ranked by breaking likelihood
    drift_metrics: DriftMetrics                     # closings_7d_unresolved, no_touch_72h, missing_sigs, coaching_needed
    agent_board: list[AgentBoardRow]                # avatar, name, pending_gci, active_deals, overdue, health, risk_label, stale_comm_count, next_close
    team_financials: TeamFinancials                 # pipeline_health, annual_pace, pending_gci, pending_volume
    closings_next_14d: list[UpcomingClosing]
    ai_intelligence: list[IntelCard]                # team-scoped insights + coach prompts
    ai_coach_locked: bool                           # always True for MVP; FE renders teaser
    refreshed_at: datetime
```

- `team_health_score` aggregates each agent's score weighted by active-deal count.
- `intervention_queue` ranks transactions inside the team by P(break) = composite of stage_pill `red`, missing critical doc, no-touch ≥ 72 h, lender silence ≥ 48 h. Reuses Active Transactions data.
- `agent_board` joins `users` (filtered to team members) with per-agent KPI aggregates. Each row drillable via `/transactions/active?agent={id}` (already supported in Milestone 2.4 backend).
- `?view=personal|team` toggle: same response shape; `personal` mode filters everything to the requesting user (used by Agents on a team).

**Granular**: `team/intervention`, `team/performance`, `team/drift`, `team/intelligence`.

### 5.C Attorney — `GET /api/v1/dashboard/attorney`

```python
class AttorneyDashboardResponse(BaseModel):
    legal_health_score: int           # 0–100, focused on approval gates
    legal_health_descriptor: str
    matters_needing_judgment: list[JudgmentItem]
    critical_approval_gates: list[ApprovalGate]
    drift_summary: AttorneyDrift      # blocked_matters, missing_formal_docs, release_ready_count
    filter_counts: AttorneyFilterCounts  # all, needs_review, missing_docs, ready_to_release, clean_files
    matter_cards: list[MatterCard]    # name, client, status_pills, review_queue (items + sign-off state), key_dates, ai_prepared_next_step{text, confidence, source}
    state_rules_summary: list[StateRuleSummary]   # per matter's closing_mode, recording, disbursement timing
    refreshed_at: datetime
```

**Write endpoints** (one new router `app/api/v1/attorney.py`):

- `POST /api/v1/attorney/approve` body `{matter_id, item_id, action: 'approve'|'hold', note?}` — toggles `attorney_review_items.signed_off`. Audit-logged. Returns updated matter state.
- `POST /api/v1/attorney/release-packet` body `{matter_id, recipient_ids[], document_ids[]}` — guards: every required `review_item` must be `signed_off=true` AND no open `missing_doc` pill, else 422. Emits packet email via `email_service.py`, writes `communication_logs`, audit log.
- `PATCH /api/v1/attorney/matters/{id}` — hold/release/note.
- `GET /api/v1/attorney/releases` — list of release-ready matters (subset of matter_cards).
- `GET /api/v1/attorney/state-rules?state=` — reads from existing `app/services/state_rules.py`.
- `GET /api/v1/attorney/recording-calendar?start=&end=` — calendar entries (county recording office holidays, cutoff times) joined with matter close dates. Backed by `attorney_recording_calendar` table (or static JSON inside `state_rules.py` for MVP).

**Persistence / migrations required before UI work:**
- `attorney_review_items`: `id`, `tenant_id`, `transaction_id`, `document_id?`, `label`, `requires_legal_judgment`, `signed_off`, `signed_off_by`, `signed_off_at`, `hold_reason`, `created_at`, `updated_at`. Index by `(tenant_id, transaction_id, signed_off)`.
- `attorney_packet_releases`: `id`, `tenant_id`, `transaction_id`, `released_by`, `released_at`, `recipient_ids`, `document_ids`, `status`, `communication_log_id`, `audit_log_id`.
- `attorney_recording_calendar` only if static `state_rules.py` data is insufficient for county cutoffs/holidays. If static JSON is used for MVP, document the refresh owner and do not build write endpoints yet.
- RLS: Attorney/Admin can read legal review rows in-tenant; only Attorney/Admin can mutate sign-off/release rows. Agent/TC/Client/Vendor cannot read legal judgment notes.

**AI guardrail enforcement**: `ai_prepared_next_step.source` is always `ai` or `rule`; confidence below the tenant's "Review Required" threshold flips the FE to a "Needs human review" badge; the Send Packet endpoint refuses release for any matter where `ai_prepared_next_step.source = 'ai' AND requires_legal_judgment = true AND human_sign_off = false`.

### 5.D Admin — `GET /api/v1/dashboard/admin`

```python
class AdminDashboardResponse(BaseModel):
    total_users: int
    active_users: int
    users_by_role: dict[UserRole, int]
    total_transactions: int
    transactions_by_status: dict[TransactionStatus, int]
    transactions_by_use_case: dict[TransactionUseCase, int]
    ai_action_summary: AiActionSummary           # week_count, approval_rate, provider_split (openai/claude %)
    task_template_stats: TaskTemplateStats       # added_global, removed_global, top_completion_rates
    recent_audit_logs: list[AuditLogRow]         # last 20
    confidence_threshold_summary: ConfidenceSummary  # current ship-it/review thresholds
    pending_invitations: int
    refreshed_at: datetime
```

Read-only aggregator. Mutations stay on existing admin endpoints (`/admin/users`, `/admin/invitations`, `/admin/task-templates`, `/settings/confidence`, `/settings/ai-provider`, `/admin/audit-logs`).

### 5.E FSBO — `GET /api/v1/dashboard/fsbo/{overview, properties, documents, milestones, share-link}`

Overview response:

```python
class FsboOverviewResponse(BaseModel):
    properties: list[FsboPropertyCard]           # address, status_pill, chips (closing_date, missing_docs, new_messages), state (listing_prep|under_contract)
    critical_next_steps: list[FsboNextStep]      # plain-English, deadline, why-it-matters
    days_to_close_nearest: int | None
    share_links_live: int
    missing_documents_count: int
    ai_guidance: FsboAiGuidance                  # next decision, glossary tooltips, milestone explanations
    recent_milestones: list[FsboMilestoneEvent]  # last 5
    support_contact: FsboSupportContact          # assigned coordinator
    boundary_notice: str                         # canonical disclosure copy
    refreshed_at: datetime
```

- `share-link` becomes a full CRUD set: `GET /api/v1/dashboard/fsbo/share-link?property_id=`, `POST` (create with `expires_in: 24h|48h|7d|30d|custom`, returns the **raw share URL/token once**), `DELETE /{id}` (revoke). The server stores only `token_hash = sha256(raw_token)`; `GET` never returns raw tokens. Viewer-open events flow through the new `/api/v1/milestones/shared/{token}/viewed` endpoint in §5.N.
- All copy must satisfy `FRONTEND_UI_WORKFLOW_LOGIC.md` §8.1 boundary notice ("Velvet Elves coordinates your workflow but does not act as your agent or provide legal advice.").

### 5.F Client — `GET /api/v1/dashboard/client`

Client portal landing already has `GET /api/v1/client/transactions`, `/documents`, `/milestones` per `SYSTEM_DESIGN.md` §3.2. We add a thin **landing summary**:

```python
class ClientDashboardResponse(BaseModel):
    transactions: list[ClientTransactionCard]  # address, status, closing_date, agent (avatar+name)
    upcoming_milestones: list[MilestoneEvent]
    documents_summary: DocumentsSummary        # missing | in_progress | uploaded | verified | complete counts
    recent_messages: list[ClientMessageThread] # client-visible thread summaries only; internal logs hidden
    agent_card: AgentCard                      # name, photo, bio snippet, phone, email
    refreshed_at: datetime
```

Supporting mutations:
- `POST /api/v1/client/messages` creates a client question/request routed to the responsible Agent/TC. It writes `communication_logs` internally but the client response only shows the client-safe message thread.
- `GET /api/v1/client/messages?transaction_id=` returns only client-visible messages and system notifications; no internal notes, AI drafts, vendor traffic, or audit details.

### 5.G Vendor Document Portal — `GET /api/v1/dashboard/vendor`

```python
class VendorDashboardResponse(BaseModel):
    upload_requests: list[VendorUploadAsk]     # docs the vendor must provide, scoped to this vendor only
    own_uploads: list[VendorUpload]            # current + legacy versions uploaded by this vendor
    open_date_requests: list[VendorDateRequest] # constrained requests without exposing internal task/timeline data
    response_template_chips: list[str]         # e.g. "Scheduled: YYYY-MM-DD"
    recent_request_threads: list[VendorThreadSummary] # vendor-facing thread snippets only
    refreshed_at: datetime
```

This endpoint is an aggregator over Milestone 4.3 data, but it must not expose full tasks, timelines, transaction history, internal communications, or the full document center. Vendors can upload their own documents, view their own uploads, and answer constrained date/document requests.

### 5.H Profile Reporting — `GET /api/v1/analytics/profile-report`

```python
class ProfileReportResponse(BaseModel):
    period: Literal['month', 'quarter', 'year', 'custom']
    start: date
    end: date
    task_completion_rate: float                # 0–1
    avg_days_to_close: float
    closings_count: int
    transaction_type_distribution: dict[TransactionUseCase, int]
    closings_by_month: list[MonthBucket]
    revenue_trend: list[MonthBucket]           # commission $ per month (estimated)
    ai_suggestion_acceptance_rate: float
    drift_reasons: list[DriftReason]
```

Backed by `/api/v1/analytics/dashboard` aggregation (already defined in `SYSTEM_DESIGN.md` §3.2 but not implemented). We implement it now since the Reports tab is in scope and so are Solo Agent / Team Leader chart widgets. Supports `?period=`, `?start=`, `?end=`, `?agent_id=` (Team Lead drilldown).

### 5.I Dashboard Layout Persistence — `/api/v1/users/me/dashboard-layout`

```python
class DashboardLayout(BaseModel):
    role: UserRole
    layout: dict[str, list[str]]   # { "agent": ["hero","production","overview","intel"], ... }
    hidden_widgets: list[str]
```

Stored in `users.profile_settings_json.dashboard_layout`. Two endpoints: `GET` (returns role default if unset), `PUT` (overwrite with validation against allowed widget IDs per role). Drives the "customizable widgets" deliverable.

Dashboard layout storage must be exact-role validated. For example, an Admin cannot persist `agent` widget IDs for the Admin dashboard just because Admin satisfies Agent-level permission elsewhere.

### 5.J Notification & Realtime

- Dashboards poll/refetch the existing React Query hooks on the same cadence as the current shell. Supabase Realtime channel wiring is optional follow-up work unless an existing app-wide realtime helper is present; do not assume `AppLayout` already subscribes to database channels.
- The dashboards do **not** generate new notifications (they are read surfaces). Existing notification triggers from M2.4 / M4.x cover all events.

### 5.K Health Score Service — `app/services/health_score_service.py`

Single source of truth so Solo Agent (personal), Team Leader (team), Attorney (legal gates), and FSBO (customer readiness) compute scores from the **same** primitives but with different weightings. Pure functions, no AI calls, fully unit-testable.

```python
PERSONAL_WEIGHTS = {
    "overdue_tasks": -8, "stale_comm_72h": -6, "missing_critical_docs": -10,
    "approaching_close_no_ctc": -12, "ai_flagged_risks": -5,
}

LEGAL_WEIGHTS = {
    "open_approval_gates": -10, "missing_notarized": -15,
    "release_ready_unattended": -4, "recording_window_drift": -8,
}

CUSTOMER_WEIGHTS = {
    "blocking_doc_missing": -12, "milestone_overdue": -10,
    "no_response_72h": -6, "share_link_expired_active_buyer": -3,
}
```

Score rounded to int 0–100; descriptor mapped via the existing `HealthScoreRing.getScoreLabel` thresholds (≥ 80 Healthy, ≥ 60 Needs Attention, < 60 At Risk) plus a sentence assembled from the dominant penalty category.

### 5.L Dashboard Aggregator — `app/services/dashboard_aggregator.py`

Thin orchestration over existing helpers. Importantly, it **does not** re-query data the shell already fetches (sidebar KPIs, AI briefing, deal counts) — those remain split so the shell can refresh independently of the dashboard body.

### 5.M Snapshot Table — `user_metric_snapshots`

New table for day-over-day deltas (health score, active deals, GCI). Migration `20260629090000_create_user_metric_snapshots.sql`:

```sql
CREATE TABLE user_metric_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  scope_owner_id UUID NOT NULL,
  scope TEXT NOT NULL CHECK (scope IN ('personal','team','legal','customer','system')),
  captured_on DATE NOT NULL,
  health_score INT NOT NULL,
  active_deals INT NOT NULL,
  pending_gci NUMERIC(14,2) NOT NULL DEFAULT 0,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, scope, scope_owner_id, captured_on)
);
CREATE INDEX ix_user_metric_snapshots_scope ON user_metric_snapshots (tenant_id, scope, scope_owner_id, captured_on DESC);
```

Populated by an explicit daily job/cron endpoint following the repo's existing cron pattern; do not couple this to `retention_purge_service.py`, which is a retention domain service. On-demand insert if no row exists for "today" the first time the dashboard is loaded. Powers the "down 3 pts from yesterday" copy in every hero card. For personal/legal/customer scope, `scope_owner_id = user_id`; for team scope, `scope_owner_id = team_id`; for admin/system scope, `scope_owner_id = tenant_id`.

### 5.N Public Milestone Viewer + Share-Link Service

This is now in scope because the plan depends on share links and the repo currently has only RLS carveout documentation, not the public viewer implementation.

New backend pieces:
- Migration `20260629090500_create_milestone_share_links.sql`:
  - `id`, `tenant_id`, `transaction_id` or `property_id`, `created_by`, `recipient_name`, `token_hash`, `expires_at`, `revoked_at`, `last_viewed_at`, `view_count`, `created_at`.
  - Unique index on `token_hash`.
  - RLS closed to anon; public reads are through the app-level token check using a service-role client.
- `app/services/share_link_service.py`:
  - `create_link(...)` generates a high-entropy raw token, stores only `sha256(raw_token)`, returns the raw URL once.
  - `resolve_token(raw_token)` hashes and validates active/not expired/not revoked, then returns public-safe milestone data only.
  - `record_view(raw_token, viewer_metadata)` increments `view_count`, stamps `last_viewed_at`, and creates a notification for the link creator.
- `app/api/v1/milestones.py`:
  - `GET /api/v1/milestones/shared/{token}` returns `{ tenant_branding, property_address, agent_name, milestone_steps[], key_dates[], document_status_cues[] }`.
  - `POST /api/v1/milestones/shared/{token}/viewed` records viewer-open notification.

Public viewer safety contract:
- Shows timeline, key dates, and document status names only.
- Does not show document downloads, contact details beyond agent name, internal notes, tasks, workflow logic, communication logs, audit logs, or AI suggestions.
- Expired/invalid/revoked tokens show a friendly expiry page with tenant contact guidance.

---

## 6. Workstream B — Frontend Page Specifications

Each subsection below is prescriptive: layout, component composition, every interaction, every empty/error/loading state, and the visual-consistency anchors back to the reference pages. All pages live under `src/pages/dashboards/` (internal) and `src/pages/fsbo/`, `src/pages/client/`, `src/pages/vendor/` (customer-facing).

### 6.A Dashboard Router — `/dashboard`

`src/pages/dashboards/DashboardRouter.tsx`. Pure redirect logic, mirrors `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.1. Renders `<PageSpinner />` for the millisecond between mount and `<Navigate to=… replace />`. Replaces the current `DashboardPage` at the `/dashboard` route. The old `DashboardPage` file is **retired from routing** and may be deleted only after tests/imports are updated; no active route should render the generic placeholder once each role has its own landing.

The router must use exact role values:
- `Agent` with no `team_id` → `/dashboard/agent`
- `TransactionCoordinator` with no `team_id` → `/dashboard/agent`
- `Agent`/`TransactionCoordinator` with `team_id`, and all `TeamLead` users → `/dashboard/team`
- `Attorney` → `/dashboard/attorney`
- `Admin` → `/dashboard/admin`
- `Client` → `/client/transactions`
- `ForSaleByOwner` → `/fsbo`
- `Vendor` → `/client/documents`

### 6.B Solo Agent Dashboard — `/dashboard/agent`

**Path:** `src/pages/dashboards/SoloAgentDashboardPage.tsx`. **Approved design:** `completed_designs/ve-homepage_dashboard-solo_agent.html`.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ AppLayout shell — sidebar(KPI tiles, nav, +New Tx CTA) + topbar(AI briefing chip)│
├─────────────────────────────────────────────────────────────────────────────────┤
│ Page Header                                                                      │
│   breadcrumb [Dashboard]                                                         │
│   <h1 class="font-serif text-[20px]">Good morning, Jan</h1>                      │
│   <p class="text-[13px] text-ve-text-muted">Three deals need intervention today.│
│ ── thin border-b border-ve-border ─────────────────────────────────────────────│
│                                                                                  │
│ Row 1 (full width)                                                               │
│   <UploadIntakeCard /> — drag/drop → startIntake(files) or openNewTransaction(files) │
│                                                                                  │
│ Row 2 (CommandGrid 1.55fr / .95fr / .8fr)                                        │
│   ┌── Hero Card ──────────┐  ┌── Production Snapshot ──┐  ┌── Transaction OV ─┐  │
│   │ kicker: ✦ TODAY · 9:14│  │ kicker: ✦ PIPELINE       │  │ kicker: ✦ AT A    │  │
│   │ <HealthScoreRing 68>  │  │ MetricCard: 4 stats grid │  │ GLANCE             │  │
│   │ ActionQueueList       │  │ ─────                    │  │ TransactionOverview│  │
│   │ DriftDiagnostics      │  │ AiPortfolioIntel rail-box│  │ Tiles (3)          │  │
│   │ FastFilterStack       │  │                           │  │ deep-link → /txs   │  │
│   └───────────────────────┘  └───────────────────────────┘  └────────────────────┘ │
│                                                                                  │
│ Row 3 (full width)                                                               │
│   "Priority Transactions" section card                                           │
│   PriorityTransactionList (3 cards, each = stripped-down TransactionCard with    │
│   next-step CTA + key tasks + key dates + contacts + footer actions)             │
│                                                                                  │
│ Floating: <AskAiFab /> already in shell — context = portfolio                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Component composition (all reused except where noted ⊕ new):**

| Block | Component(s) |
| --- | --- |
| Upload intake card | `components/shared/UploadIntakeCard` (existing) → onFilesSelected → `startIntake(files)` when a confirmation step is wanted, or `openNewTransaction(files)` for direct wizard entry. Do not call an object-shaped `openNewTransaction({initialFiles})`; that is not the current context signature. |
| Health score ring | `components/shared/HealthScoreRing` (existing) |
| ⊕ Action queue | `components/dashboard/ActionQueueList.tsx` — renders `ActionQueueItem[]` from API; each row = status dot + title + sub + status pill + primary action button. Status dot uses `ve-{red,amber,green}` triad. Button click → either AI Chat with initial prompt, deep-link `/transactions/active?highlight=:id`, or open Documents modal. |
| ⊕ Drift diagnostics | `components/dashboard/DriftDiagnostics.tsx` — 3 rows: large mono number colored by severity + sentence + chevron to filtered Active Tx view. |
| ⊕ Fast filter stack | `components/dashboard/FastFilterStack.tsx` — 4 buttons, each `<button class="filter-btn">` style, navigates to `/transactions/active?filter={key}`. Counts pulled from `fast_filter_counts`. |
| ⊕ Pipeline snapshot | `components/dashboard/PipelineSnapshot.tsx` — 2×2 grid of metric stats; mono lining-nums for $ values; sub-line under each (lifetime baseline). |
| ⊕ Transaction overview tiles | `components/dashboard/TransactionOverviewTiles.tsx` — 3 stacked tiles ("Closing this week", "In inspection", "Documents needed"); each tile is a deep link with a one-sentence drift explanation. |
| ⊕ AI portfolio intel | `components/dashboard/AiPortfolioIntel.tsx` — `intel-card` style (mini hero box with serif h4 + body + suggestion chips). Champagne accent. Each `btn-chip` opens AI Chat with a seeded prompt. |
| ⊕ Priority transaction list | `components/dashboard/PriorityTransactionList.tsx` — wraps the existing `components/shared/TransactionCard` with a "compact" prop. Reuses the next-step banner, info badges, footer actions; the body drawer is **collapsed by default** and clicking the card chevron opens it inline (or the full card on `/transactions/active?highlight=`). |

**API call**: single `useAgentDashboard()` (react-query, `staleTime: 60_000`, refetch on tab focus). Skeleton state = command-grid placeholder + 3 priority-card pulses.

**Empty states**:
- Zero transactions → upload intake card stays, hero replaced with "Get started — create your first transaction" empty card per style-guide §11 (dashed champagne border).
- Zero overdue / on-track → action queue row shows "All deals are on track" + the chip "Focus on prospecting".

**Visual consistency anchors**:
- Page header matches `TransactionListPage` header pattern (breadcrumb + Lora h1 + mono count pill on right, but here without the count pill since dashboards don't paginate).
- Card flavors per `STYLE_GUIDE.md` §6.3. Hero uses the gradient hero variant.
- Skeletons reuse `components/ui/skeleton.tsx`.
- Border / radius / shadow tokens per §5.1–5.3.

### 6.C Team Leader Dashboard — `/dashboard/team`

`src/pages/dashboards/TeamLeaderDashboardPage.tsx`. **Approved design:** `completed_designs/ve-homepage_dashboard-team_leader.html`.

Differences from Solo Agent:

1. **Toggle in page header**: `<Tabs>` (`shadcn/ui`) with two values `My Deals` and `Team View`, persisted in URL (`?view=personal|team`). Switching the toggle refetches the dashboard with the alternate scope.
2. **Team Hero Card** instead of Personal Hero Card: shows team health score + Intervention Queue (replaces Action Queue) + Drift Metrics (team-scoped: closings_7d_unresolved, no_touch_72h, missing_signatures, agents_needing_coaching).
3. **Agent Board** (Column 2) replaces Production Snapshot:
   - `components/dashboard/AgentBoard.tsx` renders one row per team member: avatar (initials), name + role, pending GCI mono, health bar (orange-filled), active-deal count, risk chip (Stable / Watch / Critical), comms/close sub-line, "Drill down" button.
   - Click row → `components/dashboard/AgentDrillDownDrawer.tsx` opens a right-side drawer (Radix Dialog with `data-side="right"`) showing: agent snapshot KPIs grid, "What you should do now" todo list, jump actions (`Open {Agent}'s transactions` → deep-link `/transactions/active?agent={id}`, `Launch AI coach` (locked teaser), `Communication log`), agent note.
4. **Closings Next 14 Days** (Column 3) replaces Transaction Overview Tiles: vertical list with date + agent + client + status indicator.
5. **Sidebar adds Team section** (already wired in `AppLayout` for `TeamLead`/`Admin`): Agents → `/admin/users`, Task Templates → `/admin/task-templates`, AI Coach (locked teaser with $79/agent/month copy).
6. **Coach prompts** in side rail (AI-generated; same surface treatment as Solo Agent's portfolio intel).

For Agents/Elves with `team_id` who aren't TeamLeads, the page renders in `My Deals` mode by default; the toggle is visible but Team View is **read-only** (no drill-down, no coaching indicators) — enforced both BE-side (scope check) and FE-side (component prop).

### 6.D Attorney Dashboard — `/dashboard/attorney`

`src/pages/dashboards/AttorneyDashboardPage.tsx`. **Approved design:** `completed_designs/ve-attorney_dashboard.html`. This is the highest-stakes page and the one with the most explicit AI guardrails.

Layout:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Page Header — "Attorney Dashboard" + filter tabs (All|Needs Review|Missing Docs│
│                |Ready To Release|Clean Files) + "+ Upload Packet" CTA           │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Row 1: UploadIntakeCard — variant="legal-packet"                                 │
│   Accepts: title commitments, settlement statements, affidavits, signed amends, │
│   recording packets. CTAs: "Open intake" + "Open release queue"                 │
│                                                                                  │
│ Row 2: CommandGrid                                                               │
│   ┌── Legal Hero Card ─────────────┐ ┌── State Rules summary ─┐ ┌── Drift ────┐│
│   │ HealthScoreRing (legal_health) │ │ closing_mode chips +   │ │ blocked     ││
│   │ Action list (critical gates)   │ │ "Open state rules" btn │ │ missing fml ││
│   │ Drift summary tiles            │ │                         │ │ release rdy ││
│   │ Filter buttons (legal-specific)│ │                         │ │             ││
│   └────────────────────────────────┘ └─────────────────────────┘ └─────────────┘│
│                                                                                  │
│ Row 3: Matter Card Stack — list of <MatterCard /> (reused/extended)              │
│   Each matter expandable into 3-col drawer:                                      │
│     Col 1: Review queue (sign-off checkboxes, attorney-only)                     │
│     Col 2: Key dates with red/amber/green                                        │
│     Col 3: AI-prepared next step — clearly labeled, confidence badge             │
│   Footer: View docs | Audit trail | Send packet | $price                         │
│                                                                                  │
│ Modals: StateRulesModal · SendPacketModal · DocumentsModal (existing) · AIChat   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Component composition:**

| Block | Component |
| --- | --- |
| ⊕ Filter tabs | `components/shared/PageTabBar` (existing) — keys: `all|needs-review|missing-docs|ready-to-release|clean-files`. Each tab carries a mono count. Active tab has the `border-b-[2.5px] border-ve-orange` treatment from `TransactionListPage`. |
| Upload intake | `UploadIntakeCard` with `variant="legal-packet"` (new prop adds copy + accepted-types chips: PDF, DOCX, PNG, JPG, HEIC; no XLS). Drop uses existing document upload + `/api/v1/ai/parse-document/{document_id}` or `/api/v1/ai/parse-document-packet`; there is no current `/api/v1/documents/intake` endpoint to call directly. |
| Hero card | `HeroCard` + custom inner panels. Health ring colored by `legal_health_score`. |
| ⊕ State rules summary | `components/dashboard/StateRulesSummary.tsx` — chips for the active state (e.g. "Indiana · Attorney closing · 24-hr recording window") + "Open state rules" → opens `StateRulesModal`. |
| ⊕ State Rules Modal | `components/dashboard/StateRulesModal.tsx` — `Dialog` with closing_mode card, recording timelines table, disbursement timing, same-day release checks, recording calendar link, "Legal/audit quick actions" button group. Read-only — no mutations. |
| Matter Card Stack | Existing `components/shared/MatterCard` extended with expandable drawer (`expanded` prop). When `expanded`, renders the 3-col layout with sign-off checkboxes, key dates, and the AI-prepared next step. |
| ⊕ AI-prepared next step | Renders the AI string with `Sparkles` icon + champagne wash + confidence pill (green ≥ 80, amber ≥ 50, rose < 50). If `requires_legal_judgment=true`, an extra "Needs your judgment" badge + disabled "AI auto-act" affordance. |
| ⊕ Send Packet Modal | `components/dashboard/SendPacketModal.tsx` — recipients (multi-select party email chips), included documents (checkbox tree of matter docs), release conditions summary, "Confirm Release" red-charcoal primary button (per style guide §6.5 destructive pattern). Refuses release when API returns 422. |
| Sign-off interaction | Checkbox tick → optimistic UI flip → `POST /api/v1/attorney/approve`. On error → revert + toast. **Never auto-checked by AI.** |
| Audit trail | Opens existing `HistoryPanel` (transaction-scoped) pre-filtered to attorney events. |

**AI guardrail enforcement (UI side):**

1. Every AI-generated string carries the champagne wash + Sparkles icon — no plain-prose rendering.
2. "Send Packet" button is disabled until every required `review_item` is checked AND no `missing_doc` pill remains.
3. If `legal_health_score < 60`, hero card shows a red "Hold" banner over the action list with copy: "Several gates need your judgment before any release is safe."
4. The AI Chat panel here receives `attorney_matters` context but **never** offers a "release packet" suggested action.

### 6.E FSBO Customer Workspace

Path roots:
- `/fsbo` → `src/pages/fsbo/FsboOverviewPage.tsx`
- `/fsbo/properties` → `FsboPropertiesPage.tsx`
- `/fsbo/properties/:id` → `FsboPropertyDetailPage.tsx`
- `/fsbo/documents` → `FsboDocumentsPage.tsx`
- `/fsbo/milestones` → `FsboMilestonesPage.tsx`
- `/fsbo/share` → `FsboSharingPage.tsx`
- `/fsbo/ask-ai` → `FsboAskAiPage.tsx`

**Approved design:** `completed_designs/ve-fsbo_dashboard.html`.

The FSBO shell variant is already in `AppLayout` (the `ForSaleByOwner` role branch). We extend it with:
- Topbar label "FSBO Workspace" suffix (per design header).
- Primary topbar CTA `Share milestones` (replaces `+ New Transaction`).
- Portal tabs in the page header (`Overview | Properties | Documents | Support`) using the same tab bar component but visually distinct from filter tabs (portal tabs use `border-b-[2.5px]` + a pill count; filter tabs already use that pattern — we differentiate by a small `font-mono text-[9px]` "Now" pill on Overview).

**FSBO Overview composition:**

| Block | Component |
| --- | --- |
| Page header | Lora h1 "FSBO Dashboard" + mono count pill ("2 properties") + actions ("Share milestones", "Notification settings") |
| Portal tabs | `PortalTabs` (new variant of `PageTabBar`) — anchors to in-page sections AND mirrors `/fsbo/*` sub-routes |
| ⊕ Property portfolio strip | `components/dashboard/FsboPortfolioStrip.tsx` — horizontal scroll of `PortfolioCard`s (existing). Each card carries property title, status pill, portfolio chips (`📅 Closing Apr 5`, `📄 1 doc missing`, `💬 3 new messages`), quick actions (`Open timeline`, `Share link`). |
| Upload card (customer-friendly) | `UploadIntakeCard` with `variant="customer"` (new prop swaps copy to "Send the docs that move the sale forward", removes the auto-classify chip) |
| Hero card | `HeroCard` "What deserves your attention today" + `HealthScoreRing` (customer-readiness score) + three inner panels: Action Queue (plain-English titles), Milestone Focus (next 3 milestones), Plain-English Guide (glossary callouts + chips). |
| ⊕ Plain-English guide | `components/dashboard/PlainEnglishGuide.tsx` — guide callout + `Ask AI` chip array. Callout copy generated from rule-based templates (no LLM call unless user clicks Ask AI). |
| Portal snapshot | MetricCard with 4 stats (active contract, listing prep, key dates 7d, blocking docs) |
| AI process guidance rail | Same `AiPortfolioIntel` component, customer copy variant |
| Boundary notice | Persistent banner pinned to the bottom of the hero card and inside the Support tab: "Velvet Elves coordinates your workflow but does not act as your agent or provide legal advice." Per `FRONTEND_UI_WORKFLOW_LOGIC.md` §8.1. |
| ⊕ Share Milestone modal | `components/dashboard/ShareMilestoneModal.tsx` — recipient name (optional), expiration radio group (24 h / 48 h / 7 d / 30 d / custom date), description, "Copy link" + "Send email" buttons. Calls `POST /api/v1/dashboard/fsbo/share-link`, which returns the raw URL once while the server stores only the token hash. Mirrors the wizard modal pattern from `STYLE_GUIDE.md` §6.5. |

**Sub-pages**:
- `FsboPropertiesPage` reuses the strip + status filter (Listing Prep / Under Contract).
- `FsboPropertyDetailPage` shows `MilestoneTimeline` (existing) + property-specific key dates + property documents + AI guidance.
- `FsboDocumentsPage` shows the 5-state board (Missing → In Progress → Uploaded → Verified → Complete) with drag-to-reclassify disabled (state changes are server-driven), upload zone, and the "Flag for deletion" action per `FRONTEND_UI_WORKFLOW_LOGIC.md` §8.1.
- `FsboMilestonesPage` is a unified read view of milestones across properties + messages (mirrors `HistoryPanel` styling).
- `FsboSharingPage` lists active share links with revoke + viewer-open log (driven by `notifications` of type `share_link_viewed`).
- `FsboAskAiPage` is a full-page AI chat reusing `AIChatPanel` with FSBO context.

**AI guardrails reaffirmed**: every AI surface here is "Ask AI"-initiated (no autonomous actions); the chat prompt is seeded with the boundary notice; AI cannot mark documents complete, edit dates, or release information outside the customer's own properties.

### 6.F Admin Dashboard — `/dashboard/admin`

`src/pages/dashboards/AdminDashboardPage.tsx`.

Layout (no approved HTML reference — we design to fit the existing internal shell):

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Page Header: "Administrator Dashboard" + "+ Invite User" CTA                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Row 1: Quick Action Tiles (4)                                                    │
│   Manage Users | Task Templates | AI Settings | Tenant Settings                 │
│                                                                                  │
│ Row 2: CommandGrid                                                               │
│   ┌── System Health Hero ─────────┐ ┌── AI Activity ────────┐ ┌── Audit Stream┐│
│   │ Users by Role (donut chart)   │ │ AI actions / week     │ │ Last 10 audit ││
│   │ Active vs Inactive            │ │ Approval rate         │ │ rows, "View   ││
│   │ Pending invitations           │ │ Provider split        │ │ all" deep-link││
│   │ Confidence threshold summary  │ │ AcceptanceChart       │ │               ││
│   └───────────────────────────────┘ └───────────────────────┘ └────────────────┘│
│                                                                                  │
│ Row 3: Charts                                                                    │
│   TransactionTypeDonut · ClosingsByMonthChart · TaskCompletionChart              │
│                                                                                  │
│ Row 4: Task template stats — top added / top removed lists                       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

Each Quick Action tile is `rounded-xl border border-ve-border bg-white shadow-card p-5` with a Lora subtitle + Plex Mono path + chevron, mirroring the section-card pattern. Charts and the donut all use the `ve-{red,amber,green,blue,purple}` palette (see §8).

### 6.G Client Portal — `/client/transactions`, `/client/documents`, `/client/milestones`, `/client/agent`

The client portal needs a **simplified portal shell branch**. The current `AppLayout` is role-aware, but it is not complete enough for Client/Vendor portals as-is: it must suppress internal workspace nav, remove the New Transaction CTA, narrow search/notifications to client-visible objects, and preserve the same visual language as Active Transactions / All Documents. Each page is small:

- `/client/transactions` — list of `ClientTransactionCard`s; click expands to a side panel with key dates and milestone timeline. **No tasks, no internal notes, no AI suggestions.**
- `/client/documents` — same 5-state board as FSBO but scoped to documents shared with the client. Upload + flag-for-deletion only; no delete.
- `/client/milestones` — read-only milestone timeline per transaction.
- `/client/agent` — agent BIO card (avatar, name, company, bio, phone, email with click-to-call/email).
- Client-safe communication lives as a panel on `/client/transactions` and `/client/milestones`: "Ask a question" composer, visible thread summaries, and notification-backed replies. It writes through `POST /api/v1/client/messages`; it never exposes internal communication logs, vendor traffic, AI drafts, or audit history.

These pages reuse the FSBO components 1:1 with role-aware filtering. The boundary notice copy differs: "Your agent and coordinator handle workflow. Reach them directly for legal questions."

### 6.H Vendor Document Portal — `/client/documents` (Vendor), `/portal/vendor` alias

Single page composed of:
- Upload requests list (docs the vendor must produce), scoped to this vendor only.
- Own uploads and document versions, including legacy/outdated versions from re-upload.
- Open date/document requests with constrained response chips such as `Scheduled: YYYY-MM-DD`.
- Recent vendor-facing request-thread snippets only.

No health score for vendors (they don't operate a portfolio in the same sense). Topbar drops the "+ New Transaction" CTA. Sidebar is reduced to document/request navigation. The page must not show internal tasks, timelines, full transaction details, full document center, internal communications, or communication logs.

### 6.I Customizable Widgets & Charts

Two layers of customization:

1. **Hide / re-order widgets**: each dashboard widget carries a stable `widget_id` (`hero`, `production`, `overview`, `priority_tx`, `intel`, `agent_board`, `state_rules`, `quick_actions`, `audit_stream`, ...). A "Customize" button in the page header (gear icon) opens `<WidgetOrderManager />` — a small Radix Dialog with drag handles per widget row + visibility toggle. Persisted via `PUT /api/v1/users/me/dashboard-layout`.
   - Hidden widgets can be re-shown from the same modal.
   - "Reset to default" button restores the role default.
2. **Interactive charts**: chart wrappers live under `src/components/dashboard/charts/` using the Slice 0-approved chart library (`recharts` if installed). All use `ve-*` tokens; tooltips use the Lora serif + Plex Mono number combination from the style guide; legends use mono uppercase kicker.

Default layouts ship per role; the role default is the canonical order documented above. Persistence applies only to ordering and visibility — chart configurations are static for MVP.

### 6.J Profile Reports Tab

Path: `src/pages/users/UserProfilePage.tsx` gains a tab shell first, then a `reports` tab (Personal Info | Notifications | Checklist Templates | Integrations | **Reports**). The current profile page is not tabbed; it renders `ProfileCard` and `UserForm` only. If the profile tab shell cannot land in 5.1 without colliding with Milestone 5.3 profile work, mount the reports surface under the existing analytics route and add a prominent profile link to it.

Reports tab content:

```
Period selector: Month | Quarter | Year | Custom (date pickers)
Search & sort row: search "client name / address", sort by close date / price / status
─────────────────────────────────────────────
KPIs:
  Task completion rate    ###.#%     (with sparkline)
  Avg days to close       ##         (with delta vs prior period)
  Closings count          ##         (period total)
  AI suggestion accept    ###.#%     (period total)
─────────────────────────────────────────────
ClosingsByMonthChart (bar)        RevenueTrendChart (line)
TransactionTypeDonut              TaskCompletionChart (line)
─────────────────────────────────────────────
Drift Reasons list (top 5)
─────────────────────────────────────────────
Recent closings table (paginated, exportable to CSV via existing /transactions export endpoints)
```

Search & sort applies to the recent closings table; period selector drives all charts via `useProfileReport({period, start, end})`.

### 6.K Public Milestone Viewer — `/milestones/:shareToken`

`src/pages/public/MilestoneViewerPage.tsx` is public and must not mount `AppLayout`.

Layout:
- Tenant logo/name header.
- Property address and "Shared milestone timeline" title.
- `MilestoneTimeline` with public-safe steps.
- Key dates with the same red/amber/green date status semantics as Active Transactions.
- Document status cues by name/status only; no document preview/download links.
- Expired/invalid state with friendly copy and tenant contact guidance.

On mount:
- `GET /api/v1/milestones/shared/{token}`.
- If successful, fire-and-forget `POST /api/v1/milestones/shared/{token}/viewed`.
- If 404/410, render expiry state instead of redirecting to login.

---

## 7. Workstream Tickets — Sequenced Backlog

We deliver in six slices so each is independently mergeable and demonstrable. Milestone 5.1 is listed as Week 17 in `milestones.txt`, but the full deliverable set is larger than one calendar week. The highest-value Week 17 demo target is Slice 0-4 (approved Solo Agent, Team Leader, Attorney, FSBO, exact routing, and public sharing). Admin, customization, and reports can continue immediately after that if the project schedule keeps 5.1 as a two-week effort; otherwise split Slice 5 into the Phase 5 follow-up lane so it does not collide with Milestone 5.2 payment work.

### Slice 0 — Tooling / Guardrails (Day 0)

0. **`chore(fe): chart and verification tooling decision`** — install/configure `recharts` (or select an existing chart alternative) before implementing chart wrappers. Add `axe-core`/`jest-axe` and Cypress/Playwright only if the team agrees to those dependencies; otherwise revise tests to existing Vitest/RTL/MSW + manual QA.
0. **`feat(auth): exact dashboard role guards`** — add `RoleRoute allowedRoles` FE helper and `require_exact_roles` BE dependency. Update route/API tests to prove Admin/TeamLead hierarchy does not accidentally render Agent dashboard endpoints.
0. **`feat(fe): dashboard shell capability map`** — centralize shell variant, sidebar sections, primary CTA, search scope, and notification scope before any role page uses `AppLayout`. Fix current CTA behavior so TC can create transactions, Attorney sees Upload Legal Packet, and Client/Vendor cannot start internal transaction workflows.

### Slice 1 — Foundation (Days 1–2)

1. **`feat(be): extract dashboard_common module`** — pull shared helpers out of `dashboard.py` into `app/services/dashboard_common.py`. No behavior change; coverage maintained.
2. **`feat(be): health_score_service`** — pure-function module + 100% unit test coverage (all weight categories, capped 0–100, scope = personal/team/legal/customer).
3. **`feat(be): user_metric_snapshots migration + dashboard metrics job`** — Supabase migration + explicit dashboard-metrics cron/trigger following the repo's existing cron endpoint pattern. Backfill query for existing tenants on first deploy.
4. **`feat(be): dashboard_aggregator`** — orchestration module + per-role fetch functions, each emitting the Pydantic responses defined in §5.
5. **`feat(fe): replace DashboardPage with DashboardRouter`** — route `/dashboard` to a redirect-only component (`<Navigate to=… replace />`) per `FRONTEND_UI_WORKFLOW_LOGIC.md` §3.1. Retire/delete the legacy file after tests/imports are updated. Update tests.

### Slice 2 — Solo Agent + Team Leader (Days 3–5)

6. **`feat(be): GET /api/v1/dashboard/agent`** + sliced sub-endpoints.
7. **`feat(be): GET /api/v1/dashboard/team`** + sliced sub-endpoints.
8. **`feat(fe): hooks useAgentDashboard, useTeamDashboard, useHealthScore`** in `src/hooks/useDashboard.ts`.
9. **`feat(fe): SoloAgentDashboardPage`** + new components: `ActionQueueList`, `DriftDiagnostics`, `FastFilterStack`, `PipelineSnapshot`, `TransactionOverviewTiles`, `AiPortfolioIntel`, `PriorityTransactionList`.
10. **`feat(fe): TeamLeaderDashboardPage`** + new components: `AgentBoard`, `AgentDrillDownDrawer`, `InterventionQueue` (variant of `ActionQueueList`).
11. **`feat(fe): route wiring`** — add `DASHBOARD_AGENT`, `DASHBOARD_TEAM` to `ROUTES`, register routes in `App.tsx`, gate by role.

### Slice 3 — Attorney (Days 6–8)

12. **`feat(be): GET /api/v1/dashboard/attorney`** + sliced sub-endpoints.
13. **`feat(be): attorney review migrations + write endpoints`** — add `attorney_review_items`, `attorney_packet_releases`, optional `attorney_recording_calendar`, RLS, then implement `/approve`, `/release-packet`, `/matters/{id}` PATCH, `/releases`, `/state-rules`, `/recording-calendar`. Each mutation is audit-logged via `audit_service.py`.
14. **`feat(fe): AttorneyDashboardPage`** + components: extend `MatterCard` with `expanded` prop + sign-off drawer, `StateRulesModal`, `SendPacketModal`, AI-prepared next step block.
15. **`fix: attorney workspace router`** — `App.tsx` currently routes `/transactions` to `AttorneyWorkspacePage` for Attorney users; keep that, but the **dashboard landing** is now `/dashboard/attorney`. Both coexist (dashboard is the landing; workspace is the deep matter queue).

### Slice 4 — FSBO + Client + Vendor (Days 9–11)

16. **`feat(be): GET /api/v1/dashboard/fsbo/*`** including share-link CRUD.
17. **`feat(be): GET /api/v1/dashboard/client`** + reuse existing `/client/*` for sub-page data.
18. **`feat(be): GET /api/v1/dashboard/vendor`** document/request-scoped aggregator; no internal task/timeline exposure.
19. **`feat(fe): FsboOverviewPage + 5 sub-pages`** + `FsboPortfolioStrip`, `PlainEnglishGuide`, `ShareMilestoneModal`.
20. **`feat(be/fe): Public Milestone Viewer`** — `share_link_service`, `app/api/v1/milestones.py`, `/milestones/:shareToken`, viewer-open notifications.
21. **`feat(fe): client portal pages`** (`ClientTransactionsPage`, `ClientDocumentsPage`, `ClientMilestonesPage`, `ClientAgentInfoPage`) + client-safe "Ask a question" composer.
22. **`feat(fe): VendorDocumentPortalPage`** at `/client/documents` for Vendor + `/portal/vendor` redirect alias.
23. **`feat(fe): role routing + redirects`** — wire `/fsbo`, `/client/*`, `/portal/vendor`; ensure `/dashboard` redirects each role correctly.

### Slice 5 — Admin + Customization + Reports (Days 12–14)

24. **`feat(be): GET /api/v1/dashboard/admin`**.
25. **`feat(be): GET /api/v1/analytics/profile-report`** + the `/api/v1/analytics/dashboard` umbrella from `SYSTEM_DESIGN.md` §3.2.
26. **`feat(be): dashboard-layout CRUD`** (`GET/PUT /api/v1/users/me/dashboard-layout`).
27. **`feat(fe): AdminDashboardPage`** + Quick Action tiles + Audit preview + chart wrappers.
28. **`feat(fe): WidgetOrderManager`** + integration on every internal dashboard.
29. **`feat(fe): Profile tab shell + Reports tab`** — add profile tabs first, then reports content using chart wrappers + recent-closings table with search/sort. If profile tab shell is deferred to 5.3, mount reports under `/reports` and link from profile.

Each slice is independently testable and demos-ready. Slice 1 is a blocker for Slices 2–5; Slices 2–5 are mostly parallelizable.

---

## 8. Charts, Widgets & Visual Tokens

`recharts` is **not** currently in the frontend bundle, so Slice 0 must either add it or choose another chart implementation before this section is executed. If `recharts` is approved, we wrap it once to lock in `ve-*` tokens:

```tsx
// src/components/dashboard/charts/chartTheme.ts
export const CHART_COLORS = {
  primary: 'var(--ve-orange)',
  primaryMuted: 'var(--ve-orange-mid)',
  red: 'var(--ve-red)',
  amber: 'var(--ve-amber)',
  green: 'var(--ve-green)',
  blue: 'var(--ve-blue)',
  purple: 'var(--ve-purple)',
  axis: 'var(--ve-text-muted)',
  grid: 'var(--ve-border)',
}

export const CHART_TYPOGRAPHY = {
  axis: { fontFamily: 'IBM Plex Mono', fontSize: 10, fill: CHART_COLORS.axis, letterSpacing: '1.5px', textTransform: 'uppercase' },
  tooltipLabel: { fontFamily: 'Lora', fontSize: 13, color: 'var(--ve-text-primary)' },
  tooltipValue: { fontFamily: 'IBM Plex Mono', fontSize: 12, color: 'var(--ve-text-primary)' },
}
```

Five wrappers ship in this milestone:

| Component | Chart | Used by |
| --- | --- | --- |
| `ClosingsByMonthChart` | Recharts BarChart, last 12 months | Solo Agent, Team Leader, Admin, Profile Reports |
| `RevenueTrendChart` | LineChart | Solo Agent, Team Leader, Profile Reports |
| `TaskCompletionChart` | LineChart with reference area for tenant goal | Admin, Profile Reports |
| `TransactionTypeDonut` | PieChart | Admin, Profile Reports |
| `AiAcceptanceChart` | Stacked BarChart (accepted / dismissed / pending) | Admin |

All charts respect `prefers-reduced-motion` (no entrance animations when the user requests reduced motion) and meet WCAG AA contrast on every series color.

---

## 9. Visual Consistency Rules

These rules are non-negotiable and live alongside `STYLE_GUIDE.md` §6 and §13:

1. **One serif Lora title per card.** Use it for the card's protagonist (e.g. "Start here. Three deals need intervention today."). All other headings inside the card are sans-serif (`font-semibold text-[13.5px]`) or mono kickers.
2. **Mono kickers** (`font-mono text-[9px] tracking-[1.8px] uppercase`) only. They live above serif titles and never inside body copy. Example: `✦ TODAY · 9:14 AM`.
3. **Status colors come as triads** (`bg-*`, `border-*`, `text-*`). Never use a status color in isolation; never re-map a triad.
4. **Card flavors** — default = `rounded-xl border border-ve-border bg-white shadow-card`. Hero = `rounded-2xl border bg-gradient-to-br from-white to-ve-orange-soft/15 shadow-[…premium]`. No new shadow tokens, no `rounded-3xl`.
5. **Pages mirror `TransactionListPage` and `DocumentsPage`** for chrome: breadcrumb row, Lora h1, mono count pill, right-aligned action buttons, optional tab bar `border-b-[2.5px]`.
6. **AI surfaces** = champagne (`ve-orange*`) + `Sparkles` from lucide. No other AI iconography (no robot heads, no glowing orbs).
7. **Confidence badges** stay on the `emerald-50/700 / amber-50/700 / rose-50/700` Tailwind defaults (per `STYLE_GUIDE.md` §10 exception) to match `AiEmailReviewPage`.
8. **Empty states are explanatory, never apologetic.** Single sentence, optional small ghost action. No illustrations, no emoji, no oversized dashed mega-cards.
9. **Pills + chips** match the existing patterns in `MatterCard`, `PortfolioCard`, and `TransactionCard` — no new chip shapes.
10. **Mobile responsiveness** — single column under 768 px, two columns 768–1279 px, three columns ≥ 1280 px. Side rails fall below the main stack at the smaller breakpoints. The horizontal portfolio strip becomes a vertical stack on mobile.
11. **Hover regions are uniform** (lists use `w-full`); 48 × 48 minimum tap target per the brand kit; `focus-visible` champagne ring honored.
12. **No `window.confirm/alert/prompt`** — all confirms use `AlertDialog` (style-guide anti-pattern #3).

---

## 10. Testing Strategy

### 10.1 Backend

- **Unit tests** for `health_score_service.py` covering every weight category, scope, and boundary (0, 100, mid-range).
- **Unit tests** for `dashboard_aggregator.py` fetch functions with mocked Supabase fixtures.
- **API integration tests** under `app/tests/` (or `app/tests/api/v1/` if the test tree is reorganized in the same slice):
  - `test_dashboard_agent.py` — happy path, empty portfolio, role mismatch (403), AI provider down → rule-based fallback.
  - `test_dashboard_team.py` — Team Lead full payload, Agent on team partial payload, view toggle, AI Coach lock flag.
  - `test_dashboard_attorney.py` — payload shape, sign-off, release-packet guards (refuses when required item unchecked, refuses when AI flagged `requires_legal_judgment=true` without human sign-off), audit log entries.
  - `test_dashboard_fsbo.py` — overview, share-link CRUD (expiry computation, raw token returned once, token hash stored, revoke), boundary copy presence.
  - `test_public_milestones.py` — valid token, expired token, revoked token, viewer-open notification, no internal fields in payload.
  - `test_dashboard_client.py`, `test_dashboard_vendor.py`, `test_dashboard_admin.py`.
  - `test_dashboard_layout.py` — GET default per role, PUT validation, RBAC.
- **Permission matrix conformance**: parameterized test that loops through `SYSTEM_DESIGN.md` §3.3 dashboard cells and asserts each role can only reach its own landing endpoint.
- **PII fence**: a contract test that asserts every dashboard endpoint runs `_safe_decrypt` over every PII column it returns (regex over response body for ciphertext leakage).

Target: maintain repo-wide ≥ 80 % coverage; new files ≥ 90 %.

### 10.2 Frontend

- **Unit tests** (Vitest + React Testing Library) for each new dashboard page and component. Mock the API hooks via `msw` (mirrors existing test pattern in `tests/`).
- **Snapshot tests** for the chart wrappers. If Slice 0 installs Recharts, assert the rendered SVG strings; otherwise assert the selected chart abstraction's accessible labels, series values, and empty states.
- **A11y tests** via `@testing-library/jest-dom`'s `toHaveAccessibleName`; add `axe-core`/`jest-axe` only if Slice 0 installs it.
- **E2E smoke tests** for the canonical journey per role (login → land on correct dashboard → drill into Active Transactions → return). Use Cypress/Playwright only if Slice 0 installs a runner; otherwise cover with RTL route tests plus manual QA.

### 10.3 Manual QA checklist (per `milestones.txt` §7.1 acceptance bullets)

For each role:
- [ ] Login → dashboard renders without console errors.
- [ ] AI briefing chip counts match `transaction-tab-counts`.
- [ ] All quick-action / fast-filter / card clicks deep-link into `/transactions/active?...` with the expected filter applied.
- [ ] Health score ring matches backend `health_score`.
- [ ] AI-prepared text never auto-acts (no checkboxes auto-tick, no packets auto-send, no comms auto-fire).
- [ ] Sidebar KPI tiles update on next poll when a related action completes.
- [ ] Empty state renders correctly for a zero-data tenant.
- [ ] Customization: hide → reload → state persists; reorder → reload → state persists; reset → returns to defaults.
- [ ] Reports tab: chart values reconcile with backend response; CSV export downloads.

**Attorney-specific:**
- [ ] AI cannot determine legal equivalence (no UI button exists).
- [ ] Release Packet is disabled until every required review item is signed off and no missing-doc pill remains.
- [ ] Same-day disbursement check is human-only.

**FSBO-specific:**
- [ ] Boundary notice visible on hero + Support tab.
- [ ] Share milestone link expiry options work (24 h / 48 h / 7 d / 30 d / custom).
- [ ] Public viewer sees timeline + key dates only, never private documents, tasks, notes, or internal communication history.
- [ ] "Ask Velvet Elves AI" cannot mark documents complete or modify dates.

---

## 11. Risk Register

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Health-score formula tuning lands "wrong" and feels punitive | Medium | Medium | Ship deterministic formula first; instrument with weekly review of distribution; iterate weights via tenant flag after pilot |
| AI provider latency makes hero card sluggish | Medium | High | Use existing `ai_next_step_cache` (24 h TTL) + `BackgroundTasks` regeneration pattern from M2.4 (`_background_refresh_ai_next_steps`); rule-based fallback is instant |
| Attorney release packet authorizes when AI evidence is insufficient | Low | Severe | Hard server-side guard refusing release while `requires_legal_judgment AND !human_sign_off`; backend integration tests plus role-route smoke QA cover this path |
| Customizable widget persistence corrupts user state | Low | Medium | Server validates widget IDs against the role's allowed set; "Reset to default" button always rebuilds from canonical layout |
| Dashboard chart libraries balloon bundle size | Medium | Medium | Decide/install chart package in Slice 0; keep wrappers small; route-split dashboard pages via Vite |
| FSBO boundary-notice copy drift between pages | Low | Medium | Single constant `FSBO_BOUNDARY_NOTICE` in `src/utils/copy.ts`; referenced from every FSBO surface |
| Solo-vs-team routing edge cases (Agent with `team_id` but Team has no transactions) | Medium | Low | Router still sends team members to `/dashboard/team`; render a team-empty state and default to "My Deals" instead of falling back to Solo |
| Share-link token leakage | Low | Severe | Store only `token_hash`; raw token returned once from create; GET lists metadata only; public viewer validates by hashing presented token |
| Vendor portal overexposes internal workflow | Medium | High | Vendor view is document/request-scoped only; no internal tasks, timelines, full documents, communication logs, or transaction history |
| Performance regression from N+1 in dashboard aggregator | Medium | High | Aggregator uses one batch fetch per resource (existing pattern from `dashboard_transaction_cards`); load test with 200-deal seed in CI |

---

## 12. Acceptance Criteria — mapped to milestones.txt

| `milestones.txt` §5.1 success bullet | Verified by |
| --- | --- |
| All 8 role dashboards/workspaces functional with real data | Slice 1–5 acceptance + route/E2E smoke per role |
| Solo Agent, Team Leader, Attorney, and FSBO match approved HTML designs | Visual diff against `completed_designs/*.html`; design review with client; manual QA checklist §10.3 |
| Dashboard cards deep-link into Active Transactions | Each card / filter button / KPI tile has a registered link target; tested in E2E |
| Health score rings, command grids, and portfolio cards rendering | Component snapshots; manual QA |
| AI-vs-human guardrails enforced on Attorney dashboard | Attorney-specific manual QA checklist; backend integration tests for release-packet guards |
| Customizable widgets and interactive charts/KPIs | `WidgetOrderManager` + chart wrappers tested via Vitest snapshots and route/component tests; E2E reorder spec only if an E2E runner is installed in Slice 0 |
| Reporting dashboard in profile (task completion rates, transaction metrics, search & sort) | Profile Reports tab + `analytics/profile-report` integration tests |
| Milestone sharing creates a safe public viewer | Share-link CRUD tests + `/milestones/:shareToken` public page QA + no-internal-field contract tests |

When every row above is green, Milestone 5.1 is **done-done**.

---

## 13. Out-of-Band Notes & References

- This plan respects the project memory entries: PII Fernet at rest (`_safe_decrypt` on every dashboard endpoint), client-facing drafts phrased as "I" (relevant for any client-emailable drafts the dashboards spawn), TC/Elf transaction creation (implemented against the current `TransactionCoordinator` enum role), Transaction & Task Detail pages remain de-scoped (we only deep-link, never embed those views).
- The Active Transactions workspace is the **only** transaction list surface — dashboards never re-implement it. Every `/transactions/...` link routes through the existing routes added in M2.4.
- No commit, push, or PR is performed by this plan (per `feedback_no_independent_vcs.md`). Each slice ships through the normal review path on Jan's command.
- ListedKit comparisons stay out (`feedback_listedkit_sensitivity.md`); marketing-style framing avoided in dashboard copy.
- All dates surfaced on dashboards inherit the existing date status semantics from `getKeyDateStatus` in `TransactionListPage.tsx` so red/amber/green colors are consistent across the product.

---

*End of plan.*
