# Milestone 5.1 Dashboard Remediation Plan
## Revised implementation plan for role-specific dashboards

| Field | Value |
| --- | --- |
| Milestone | 5.1 - Role-Specific Dashboards remediation |
| Revised | 2026-05-19 (rev 2) |
| Design references | `completed_designs/ve-homepage_dashboard-solo_agent.html`, `ve-homepage_dashboard-team_leader.html`, `ve-attorney_dashboard.html`, `ve-fsbo_dashboard.html` |
| Spec references | `requirements.txt`, `SYSTEM_DESIGN.md`, `FRONTEND_UI_WORKFLOW_LOGIC.md`, `STYLE_GUIDE.md`, `milestones.txt`, `MILESTONE_5_1_IMPLEMENTATION_PLAN.md` |
| Current implementation references | `velvet-elves-frontend/src/layouts/AppLayout.tsx`, `src/layouts/dashboardShellConfig.ts`, `src/pages/dashboards/DashboardRouter.tsx`, `src/hooks/useDashboard.ts`, `src/hooks/useApiFetch.ts`, `src/pages/dashboards/*`, `src/pages/fsbo/*`, `src/pages/vendor/VendorDocumentPortalPage.tsx`, `src/components/shared/UploadIntakeCard.tsx`, `src/App.tsx`, `velvet-elves-backend/app/api/v1/dashboard_role.py`, `app/services/dashboard_aggregator.py` |

This document supersedes the earlier draft of `MILESTONE_5_1_DASHBOARD_REMEDIATION_PLAN.md`. It keeps the same objective, but corrects several implementation assumptions that were either incomplete, inaccurate, or not strict enough to close Milestone 5.1 cleanly. Revision 2 (this file) also expands §2.2 with the full per-file picture, because the prior revision named only two of the three files that actually need editing for routing.

---

## 0. Deficiencies Corrected In This Revision

### 0.1 Carried forward from the prior draft

The previous draft correctly identified that the approved dashboard designs were not followed closely enough, but it missed or understated these unresolved issues:

1. **The shell capability map is mostly unused.** `dashboardShellConfig.ts` already defines `shellVariant`, `sidebarSections`, `primaryCta`, `searchScope`, and `notificationScope`, but `AppLayout.tsx` currently uses only `canCreateTransaction` and `landingRoute`. As a result, role-specific shell behavior is still hardcoded in `AppLayout`.
2. **Client and Vendor users can receive internal sidebar navigation.** `getNavSections()` falls back to the internal `Deals / Workflow / Vendors / Intelligence` nav for any role that is not Attorney or FSBO. This is a privacy and UX defect for Client and Vendor roles.
3. **FSBO sidebar routes are wrong.** Current FSBO sidebar entries point to shared internal routes such as `/transactions`, `/documents`, `/tasks/queue`, `/ai-suggestions`, and `/sharing` instead of the FSBO workspace routes.
4. **FSBO sidebar styling is internally inconsistent.** `AppLayout` switches the FSBO sidebar container to white while the sidebar nav text remains white. The approved FSBO design uses the same dark sidebar (`#1E3356`) as the rest of the app, so the remediation should keep a dark sidebar unless a complete light portal shell is deliberately implemented.
5. **The topbar primary CTA map is ignored.** Attorney should see `+ Upload Legal Packet`, FSBO should see `Share milestones`, Client should get a client-safe question action, and Vendor should get a scoped upload action. The current topbar still renders only `+ New Transaction` when `canCreateTransaction` is true.
6. **The topbar brand descriptor is hardcoded.** Every role currently sees `Transaction OS` (the literal string sits in `AppLayout.tsx` ~ line 614), despite all four approved designs showing role-specific descriptors.
7. **The prior plan used incorrect endpoint naming for sidebar counts.** The shipped endpoints are under `/api/v1/dashboard/*`, not `/api/v1/workspace/*`.
8. **Attorney counts are not complete in the current backend.** `fetch_attorney()` initializes `missing_docs` but never increments it, `drift_summary.missing_formal_docs` is a hardcoded `0`, and matter cards do not expose a stable `filter_key`. The sidebar and filter tabs cannot be reliable until this is fixed.
9. **The Attorney page remediation was too vague about URL state.** Sidebar filter links, page tabs, modals, and panels must be URL-addressable. Avoid `to: "#"`.
10. **`UploadIntakeCard variant="legal-packet"` does not exist.** The shipped component only takes `onFilesSelected`, `accept`, and `className`. The plan must first extend the component with copy/accept props before asking pages to use it.
11. **FSBO tabs are duplicated in two places.** The old six-tab set appears in both `FsboOverviewPage.tsx` and `pages/fsbo/_shell.tsx`; both must be changed to the four approved portal tabs.
12. **FSBO/customer upload CTAs can incorrectly open the internal transaction wizard or do nothing.** `FsboOverviewPage` passes `intake.openNewTransaction` to `FsboTaskList`'s `onUpload`. `UploadIntakeCard` is also rendered with no `onFilesSelected` in `FsboDocumentsPage` and `VendorDocumentPortalPage`, so a customer click does nothing.
13. **Manual route access is too loose for team dashboards.** `DashboardRouter` correctly sends no-team Agents/TCs to `/dashboard/agent`, but the `/dashboard/team` route in `App.tsx` is wrapped in `RoleRoute allowedRoles={['TeamLead','Agent','TransactionCoordinator','Admin']}` and performs no `team_id` check. Non-team Agents/TCs that paste the URL render the team dashboard.
14. **Vendor portal routing is inconsistent at three layers.** `VendorDocumentPortalPage.tsx` exists but is never imported in `App.tsx`; the `/portal/vendor` route is a `<Navigate to={ROUTES.CLIENT_DOCUMENTS} replace />`; `DashboardRouter.tsx` sends Vendor users to `/client/documents`; and `dashboardShellConfig.ts` lists Vendor's `landingRoute` as `/client/documents`. All three must be corrected; the prior draft named only two.
15. **Tests are not specific enough.** The plan needs role-by-role shell tests, not only page smoke tests.

### 0.2 Newly identified in this revision

The prior draft did not flag these issues, but they block Milestone 5.1 from closing cleanly and must be in scope:

16. **Sidebar KPI tiles fetch from the internal endpoint for every role.** `AppLayout` unconditionally calls `useSidebarKpis()` (`/api/v1/dashboard/sidebar-kpis`) and `useDealStateCounts()` (`/api/v1/dashboard/deal-state-counts`). For FSBO, `getKpiTiles()` then renders `My Properties / Pending Tasks / Documents (0) / Messages (0)` — the last two are hardcoded zeros, and the first two are derived from internal numbers, not FSBO numbers. Attorney, Client, and Vendor are even worse: they receive the same generic four tiles. KPIs for non-internal roles must come from each role's own dashboard endpoint.
17. **`Today's AI Briefing` topbar bar renders for every role.** `AppLayout` always calls `useAiBriefing()` and renders Critical / Needs Attention / On Track pills. The endpoint is internal and the click target opens the internal `AIChatPanel`. Client, FSBO, Vendor, and Attorney must not see the internal briefing bar.
18. **`SearchPalette` ignores `capability.searchScope`.** The palette opens for every role via Cmd/Ctrl+K and `/`, and always queries the tenant-wide search index. FSBO, Client, and Vendor must either be limited to their scope or have the shortcut suppressed.
19. **`NotificationsPanel` ignores `capability.notificationScope`.** All roles use the same panel and the same endpoint. FSBO and Client notifications must not include internal communication-audit events; Vendor should only see vendor-thread events.
20. **The role-dashboard React Query hooks do not accept options.** `useAgentDashboard`, `useTeamDashboard`, `useAttorneyDashboard`, `useAdminDashboard`, `useFsboOverview`, `useClientDashboard`, and `useVendorDashboard` all hardcode their query options. `useApiFetch` already supports an `options` argument, so each role hook must forward `Omit<UseQueryOptions<T>, 'queryKey'|'queryFn'>` to let `AppLayout` gate them with `enabled` per role.
21. **`PrimaryCta['action']` union is missing values.** The union is `'new-transaction' | 'upload-legal-packet' | 'share-milestones' | 'ask-ai' | 'none'`. There is no `upload-document` (Vendor) and no `ask-agent` (Client-safe). Vendor's config currently sets `action: 'none'` even though the label says `Upload document` — internally inconsistent. Client's config uses `action: 'ask-ai'` which the design says is FSBO-only.
22. **The standalone "Dashboard" sidebar link uses the static `capability.landingRoute`.** For Agent and TransactionCoordinator the config returns `/dashboard`, which forces an extra DashboardRouter redirect hop on every click and ignores `team_id`. The link must resolve via a `getLandingRoute(user)` helper that checks `team_id`.
23. **The topbar `<Link to={ROUTES.DASHBOARD}>` brand lockup is fine as `/dashboard`** because `/dashboard` itself is routed through `DashboardRouter` and immediately redirects. This is acceptable but should be documented so future edits do not break it.
24. **The topbar "New Transaction" CTA duplicates the sidebar footer "New Transaction" button.** When `canCreate=true` the button appears twice. Pick one surface for each CTA action.
25. **`/notifications` and `/sharing` routes are global and unguarded.** They are reachable for all roles. FSBO is currently sent to `/sharing` by the leaked internal nav; once FSBO sidebar is corrected to `/fsbo/share` these legacy paths should remain available only to internal roles, or `/sharing` should redirect FSBO users to `/fsbo/share`.
26. **`SoloAgentDashboardPage` is the landing for TransactionCoordinator with no `team_id`.** The page title is "Solo Agent" but TC is not an agent. Confirm copy works for TC or branch the greeting by role.
27. **`/dashboard/team` for Admin.** DashboardRouter sends Admin to `/dashboard/admin`, but `/dashboard/team` allows Admin and many existing links land Admins there. When Admin is on `/dashboard/team`, the descriptor must remain `Admin Console`, not `Team Command`.
28. **The post-login return-location flow.** `AppLayout.handleLogout()` stores `pathname + search + hash` in `localStorage` and re-uses it after re-auth. If a Vendor previously landed on `/client/documents` (the broken default), that URL is restored after re-login and the role landing fix is bypassed. The remediation must invalidate stale return-locations that do not match the new role landing.
29. **`DashboardRouter` fallback sends unknown roles to `/dashboard/agent`.** This is a silent privilege upgrade for any future role. The fallback should be `UnauthorizedPage` or `/login`.
30. **The Attorney design lists `Recording Calendar` as opening `StateModal()`, not navigating.** The prior plan picks the route-based approach (`/attorney/recording-calendar`) without resolving the conflict. Pick one model and apply it consistently — see §3.5.
31. **The Attorney design includes `+ New Matter` in the sidebar footer.** That action does not exist in the system. The Attorney sidebar footer should render the Attorney `primaryCta` (`Upload legal packet`) instead.
32. **`/client/documents` allows both Client and Vendor in `App.tsx` (`RoleRoute allowedRoles={['Client','Vendor']}`).** Once Vendor lands at `/portal/vendor`, decide whether to keep dual access on `/client/documents` or restrict it to Client only.

---

## 1. Guiding Principles

1. **Designs are authoritative for role intent, not pixel-perfect law.** Where a design conflicts with `requirements.txt`, `SYSTEM_DESIGN.md`, `FRONTEND_UI_WORKFLOW_LOGIC.md`, or implemented access rules, the docs and secure implementation win.
2. **The shared shell stays.** Do not redesign the product shell. Remediate descriptors, nav groups, CTAs, route targets, counts, and role-specific page composition.
3. **No dead links.** A sidebar item must navigate to an existing route, a route alias added in this pass, or a URL-controlled modal/panel on an existing page.
4. **No portal data leakage.** Client, FSBO, and Vendor roles must never see internal transaction, task, AI suggestion, vendor directory, communication audit, or analytics navigation unless explicitly allowed by their portal spec. This includes the topbar briefing bar, the Cmd-K search palette, and the notifications panel — not only the sidebar.
5. **AI Coach remains locked.** `milestones.txt` says AI Coach is a future paid add-on. MVP may show a locked teaser for Team Leader only, but no active Coach workflow.
6. **Attorney AI guardrails are absolute.** AI can organize, compare, summarize, and draft. It cannot approve legal equivalence, final packet release, legal position, or same-day disbursement exceptions.
7. **Deep links are part of the dashboard contract.** Filter tabs, cards, sidebar shortcuts, and CTAs must use query params or explicit routes so refresh / back / share behavior works.
8. **One source of truth per behavior.** Role descriptor, sidebar sections, primary CTA, search scope, notification scope, landing route, and `canCreateTransaction` all live in `dashboardShellConfig.ts`. `AppLayout` and `DashboardRouter` read from there — they do not duplicate the rules.

---

## 2. Source-Of-Truth Snapshot

### 2.1 Topbar Descriptor By Role

The small mono-caps descriptor under the Velvet Elves wordmark must become role-aware. Today it is the literal string `Transaction OS` in `AppLayout.tsx`.

| Role / condition | Descriptor |
| --- | --- |
| Agent with no `team_id` | `Transaction OS` |
| TransactionCoordinator with no `team_id` | `Transaction OS` |
| Agent or TransactionCoordinator with `team_id` | `Team Command` |
| TeamLead | `Team Command` |
| Attorney | `Attorney Workspace` |
| ForSaleByOwner | `FSBO Workspace` |
| Admin (on any dashboard route, including `/dashboard/team`) | `Admin Console` |
| Client | `Your Workspace` |
| Vendor | `Vendor Portal` |

Implementation notes:

- Frontend role value is `ForSaleByOwner`; backend role enum value is also `ForSaleByOwner`. Do not use the older document label `FSBO_Customer` in code.
- Resolve via `getBrandDescriptor(user)` exported from `dashboardShellConfig.ts`. Admin overrides team-conditional logic; `getBrandDescriptor` must never return `Team Command` for an Admin even when they manually visit `/dashboard/team`.

### 2.2 Dashboard Landing Routes

This section is the heart of the routing remediation. The prior revision named only `dashboardShellConfig.ts` and `App.tsx` as files needing edits — that was incomplete. **Three files own routing decisions**, plus optional return-location and brand-link consequences. They must all agree, or a user can be sent to the wrong landing depending on whether they signed in, clicked the brand lockup, or clicked the sidebar "Dashboard" item.

#### 2.2.1 Target landing routes

| Role / condition | Target landing route |
| --- | --- |
| Agent with no `team_id` | `/dashboard/agent` |
| TransactionCoordinator with no `team_id` | `/dashboard/agent` |
| Agent or TransactionCoordinator with `team_id` | `/dashboard/team` |
| TeamLead | `/dashboard/team` |
| Attorney | `/dashboard/attorney` |
| Admin | `/dashboard/admin` |
| Client | `/client/transactions` |
| ForSaleByOwner | `/fsbo` |
| Vendor | `/portal/vendor` |
| Unknown / future role | `/unauthorized` (not `/dashboard/agent`) |

#### 2.2.2 Files that participate in landing

| File | What it owns | How it expresses the landing |
| --- | --- | --- |
| `src/pages/dashboards/DashboardRouter.tsx` | Resolves the bare `/dashboard` path (the URL the user hits after login or when clicking the brand lockup) | `switch (user.role)` returning `<Navigate to=... replace />` |
| `src/layouts/dashboardShellConfig.ts` | Provides `landingRoute` to the rest of the shell so the sidebar "Dashboard" link and any "back to dashboard" affordance use the right URL without re-hitting `/dashboard` | `DASHBOARD_SHELL_BY_ROLE[role].landingRoute` |
| `src/App.tsx` | Defines what renders at each landing path (which page, which `RoleRoute`) | `<Route path=... element={<RoleRoute allowedRoles={...}><Page /></RoleRoute>} />` |
| `src/utils/returnLocation.ts` (consumer of stored URL) | Restores last visited URL after re-login | Stored URL in `localStorage` |
| `src/layouts/AppLayout.tsx` brand `<Link to={ROUTES.DASHBOARD}>` | Sends the user to `/dashboard` which then re-routes via `DashboardRouter` | Static — keep as `/dashboard` |

#### 2.2.3 Current state vs. required edits

| Role | DashboardRouter (current) | DashboardRouter (target) | shellConfig.landingRoute (current) | shellConfig.landingRoute (target) | App.tsx route element (current) | App.tsx route element (target) |
| --- | --- | --- | --- | --- | --- | --- |
| Agent no-team | `/dashboard/agent` | unchanged | `/dashboard` (resolved by router on click) | `/dashboard/agent` via `getLandingRoute(user)` helper | `<RoleRoute allowed=[Agent,TC]><SoloAgent/></RoleRoute>` | unchanged |
| TC no-team | `/dashboard/agent` | unchanged | `/dashboard` | `/dashboard/agent` via helper | shares Agent route | unchanged |
| Agent/TC w/ team | `/dashboard/team` | unchanged | `/dashboard` | `/dashboard/team` via helper | `<RoleRoute allowed=[TeamLead,Agent,TC,Admin]><TeamLeader/></RoleRoute>` | wrap with `<TeamDashboardGuard>` — see §2.2.4 |
| TeamLead | `/dashboard/team` | unchanged | `/dashboard/team` | unchanged | as above | as above |
| Attorney | `/dashboard/attorney` | unchanged | `/dashboard/attorney` | unchanged | `<RoleRoute allowed=[Attorney]><AttorneyDashboard/></RoleRoute>` | unchanged |
| Admin | `/dashboard/admin` | unchanged | `/dashboard/admin` | unchanged | `<RoleRoute allowed=[Admin]><AdminDashboard/></RoleRoute>` | unchanged |
| Client | `/client/transactions` | unchanged | `/client/transactions` | unchanged | `<RoleRoute allowed=[Client]><ClientTransactions/></RoleRoute>` | unchanged |
| FSBO | `/fsbo` | unchanged | `/fsbo` | unchanged | `<RoleRoute allowed=[ForSaleByOwner]><FsboOverview/></RoleRoute>` | unchanged |
| **Vendor** | **`/client/documents`** | **`/portal/vendor`** | **`/client/documents`** | **`/portal/vendor`** | **`<Navigate to=/client/documents replace />`** wrapped in `RoleRoute allowed=[Vendor]` | **`<RoleRoute allowed=[Vendor]><VendorDocumentPortalPage/></RoleRoute>`** — also import the page at the top of `App.tsx` |
| Unknown / future | `/dashboard/agent` (silent upgrade) | `/unauthorized` | n/a | n/a | n/a | n/a |

#### 2.2.4 `/dashboard/team` access guard

`/dashboard/team` is currently reachable by any signed-in Agent or TC by typing the URL, because the `RoleRoute` only checks role, not `team_id`. Add a wrapping component:

```tsx
// src/components/TeamDashboardGuard.tsx
function TeamDashboardGuard({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  if (!user) return <Navigate to={ROUTES.LOGIN} replace />
  if ((user.role === 'Agent' || user.role === 'TransactionCoordinator') && !user.team_id) {
    return <Navigate to={ROUTES.DASHBOARD_AGENT} replace />
  }
  return <>{children}</>
}
```

Use it inside the `RoleRoute`:

```tsx
<Route
  path={ROUTES.DASHBOARD_TEAM}
  element={
    <RoleRoute allowedRoles={['TeamLead', 'Agent', 'TransactionCoordinator', 'Admin']}>
      <TeamDashboardGuard><TeamLeaderDashboardPage /></TeamDashboardGuard>
    </RoleRoute>
  }
/>
```

Admin and TeamLead are unaffected. Agents/TCs without a `team_id` are bounced to `/dashboard/agent`.

#### 2.2.5 `getLandingRoute(user)` helper

`landingRoute` in the capability map is static per role, but Agent and TC depend on `team_id`. Replace direct reads of `capability.landingRoute` with a helper:

```ts
export function getLandingRoute(user: User | null | undefined): string {
  if (!user) return ROUTES.LOGIN
  switch (user.role) {
    case 'Agent':
    case 'TransactionCoordinator':
      return user.team_id ? ROUTES.DASHBOARD_TEAM : ROUTES.DASHBOARD_AGENT
    case 'TeamLead': return ROUTES.DASHBOARD_TEAM
    case 'Attorney': return ROUTES.DASHBOARD_ATTORNEY
    case 'Admin':    return ROUTES.DASHBOARD_ADMIN
    case 'Client':   return ROUTES.CLIENT_TRANSACTIONS
    case 'ForSaleByOwner': return ROUTES.FSBO
    case 'Vendor':   return ROUTES.VENDOR_PORTAL
    default: return ROUTES.UNAUTHORIZED
  }
}
```

`DashboardRouter` should also delegate to this helper rather than restate the switch:

```tsx
return <Navigate to={getLandingRoute(user)} replace />
```

This eliminates the silent fallback-to-`/dashboard/agent` for unknown roles (deficiency #29).

#### 2.2.6 Brand-link, sidebar "Dashboard" link, and post-login return

- **Topbar brand lockup** (`<Link to={ROUTES.DASHBOARD}>`): keep as-is — the bare `/dashboard` path is handled by `DashboardRouter` and is already team-aware.
- **Sidebar standalone "Dashboard" link** (`<Link to={capability.landingRoute}>`): change to `<Link to={getLandingRoute(user)}>` so the link is correct on every render without an extra redirect hop.
- **Post-login return-location**: in `AppLayout.handleLogout` / `rememberReturnLocation`, drop any stored URL that does not match the user's allowed surface. The simplest rule:
  - After successful sign-in, if the stored return URL fails the same `RoleRoute` check that gates the matching route, discard it and navigate to `getLandingRoute(user)`.
  - This invalidates the Vendor user's stale `/client/documents` history once Vendor is moved to `/portal/vendor`.

#### 2.2.7 `/dashboard/legacy` and `/dashboard` fallback

- Keep `/dashboard/legacy` as a development escape hatch but do not link to it from any sidebar.
- The bare `/dashboard` path's only job is to call `DashboardRouter`. Do not add a page render at `/dashboard`.

#### 2.2.8 Acceptance for §2.2

1. After login, every role lands on the target route in §2.2.1.
2. Clicking the topbar brand lockup or the sidebar "Dashboard" link from any deep page returns the user to the same target route, with no flash through `/dashboard/agent` or `/client/documents`.
3. A no-team Agent typing `/dashboard/team` is redirected to `/dashboard/agent`.
4. A Vendor visiting `/portal/vendor` sees `VendorDocumentPortalPage`, not `ClientDocumentsPage`.
5. An unknown future role hitting `/dashboard` is sent to `/unauthorized`, not `/dashboard/agent`.
6. A user whose previous session ended on a now-disallowed URL is redirected to their landing route on re-login, not bounced through the disallowed URL.

---

## 3. Shell Remediation

### 3.1 Make `dashboardShellConfig.ts` Active

`dashboardShellConfig.ts` becomes the single source of truth for the shell.

Required changes:

- Add `getBrandDescriptor(user)` and `getLandingRoute(user)` helpers (both must accept the full user object, because Agent/TC behavior depends on `team_id`).
- Extend `PrimaryCta['action']` union to include `'upload-document'` and `'ask-agent'`.
- Update Vendor capability:
  - `landingRoute: ROUTES.VENDOR_PORTAL`
  - `primaryCta: { label: 'Upload document', action: 'upload-document' }`
- Update Client capability:
  - `primaryCta: { label: 'Ask your agent', action: 'ask-agent' }`
- Keep Agent/TC transaction creation enabled where currently allowed.

### 3.2 Rebuild Sidebar From Capability, Not Role Fallbacks

Replace `getNavSections(role, ...)` with a builder that consumes:

```ts
{
  user,
  capability,
  dealCounts,
  sidebarKpis,
  attorneySummary,
  fsboOverview,
  clientSummary,
  vendorSummary,
  pendingNotifications,
  vendorProposals
}
```

The builder must use `capability.sidebarSections`. It must not fall through to the internal nav for Client, FSBO, or Vendor.

### 3.3 Internal Agent / TC Sidebar

Keep the shipped internal nav because it preserves Milestone 4.2 and 4.3 features that the older designs do not show.

Sections:

- Deals: Active Transactions, Pending, Closed, All Transactions
- Workflow: My Task Queue, All Documents, Closing Calendar
- Vendors: Vendor Directory
- Intelligence: AI Suggestions, AI Email Review, Vendor Proposals, Analytics
- Settings: standalone footer link

Do not remove AI Email Review, Vendor Proposals, or Vendor Directory.

### 3.4 Team Sidebar

TeamLead and team-member Agents/TCs use the internal nav plus Team.

Team section:

- Team Overview
- Team Members
- Task Templates
- Vendor Templates
- Communication Audit

Intelligence section:

- Existing internal intelligence items
- Add `AI Coach` with `Locked` badge, but route it to `/dashboard/team?modal=ai-coach` rather than `#`.

The Team dashboard page owns the locked Coach modal. `AppLayout` should not need special Coach modal state.

### 3.5 Attorney Sidebar

Adopt the approved Attorney design structure, but use real routes / query params and resolve the Recording Calendar conflict.

Deals:

| Label | Route |
| --- | --- |
| Attorney Queue | `/dashboard/attorney?filter=all` |
| Pending Review | `/dashboard/attorney?filter=needs-review` |
| Ready To Release | `/dashboard/attorney?filter=ready-to-release` |
| Clean Files | `/dashboard/attorney?filter=clean-files` |

Workflow:

| Label | Route |
| --- | --- |
| Missing Documents | `/dashboard/attorney?filter=missing-docs` |
| Recording Calendar | `/attorney/recording-calendar` |
| Communication Log | `/dashboard/attorney?panel=communications` |

Intelligence:

| Label | Route |
| --- | --- |
| AI Suggestions | `/ai-suggestions?scope=attorney` |
| State Rules | `/dashboard/attorney?panel=state-rules` |

Settings remains the shared settings/profile access pattern, not an Attorney Intelligence item.

Recording Calendar conflict resolution (deficiency #30): the design opens `StateModal()` from the same link, which conflates "what state recording rules apply" with "what is on the recording calendar." Pick the route-based approach:

- `Recording Calendar` → navigates to `/attorney/recording-calendar`.
- `State Rules` (Intelligence section) → opens the state rules modal via `/dashboard/attorney?panel=state-rules`.

Add `ROUTES.ATTORNEY_RECORDING_CALENDAR = '/attorney/recording-calendar'`. For MVP, the route can render a thin wrapper around `CalendarPage` with `scope='attorney'` or redirect to `/calendar?scope=attorney`, but the route must exist because the workflow spec names it.

Sidebar footer button: render Attorney's `primaryCta` (`Upload legal packet`), **not** `+ New Matter`. There is no `New Matter` action in the system (deficiency #31).

### 3.6 FSBO Sidebar

Use the design's two-section split and the real FSBO routes.

Workspace:

| Label | Route | Badge |
| --- | --- | --- |
| Dashboard | `/fsbo` | none |
| My Properties | `/fsbo/properties` | property count if useful |
| Documents | `/fsbo/documents` | `missing_documents_count` when greater than 0 |
| Milestones & Messages | `/fsbo/milestones` | total unread/new message count |

Help:

| Label | Route | Badge |
| --- | --- | --- |
| Ask Velvet Elves AI | `/fsbo/ask-ai` | none |
| Notifications | `/notifications` (or scope-redirect; see §3.12) | unread notification count |
| Sharing | `/fsbo/share` | `Live` only when `share_links_live > 0` |

Implementation notes:

- Suppress the generic standalone Dashboard link for FSBO, because Dashboard is an in-section item in the approved design.
- Keep the dark sidebar style from the design. Remove or revise the current `isFsbo ? 'bg-white' : 'bg-ve-sidebar'` branch unless a complete light sidebar text/color system is built.
- Add green sidebar badge styling for the `Live` badge.

### 3.7 Client Sidebar

Client has no approved dashboard design, but the docs are explicit. Do not show internal navigation.

Client nav:

| Label | Route |
| --- | --- |
| My Transactions | `/client/transactions` |
| Documents | `/client/documents` |
| Milestones | `/client/milestones` |
| Agent Info | `/client/agent` |

Do not show Deals, Workflow, Vendors, Intelligence, Analytics, AI Suggestions, Task Queue, All Documents, Vendor Proposals, or Vendor Directory.

### 3.8 Vendor Sidebar

Vendor is document/request-scoped. Do not show full Client tabs or internal nav.

Vendor nav:

| Label | Route |
| --- | --- |
| Document Requests | `/portal/vendor` |
| My Uploads | `/portal/vendor?view=uploads` |

If the implementation keeps a single-page vendor portal, both entries may target the same component with a query-param view.

Decide whether Vendor retains access to `/client/documents` (currently allowed via `RoleRoute allowedRoles={['Client','Vendor']}`):

- Recommended: remove Vendor from `/client/documents` and rely solely on `/portal/vendor`. The Vendor experience should be document/request-scoped, and reusing the Client page leaks Client-styled context.

### 3.9 Admin Sidebar

Admin has no approved dashboard design. Keep Admin internal access, but make it explicit in config:

- Descriptor: `Admin Console` (also applies when Admin is on `/dashboard/team`).
- Landing route: `/dashboard/admin`
- Sections: internal Deals, Workflow, Vendors, Intelligence, Team, Admin, Settings

Admin may access Team surfaces through existing role hierarchy where intended, but Admin must not be treated as a TeamLead for the topbar descriptor.

### 3.10 Primary CTA Behavior

Render `capability.primaryCta` in the topbar and sidebar footer when `action !== 'none'`. Decide one surface per CTA action and do not duplicate (deficiency #24): topbar is the canonical surface for the primary CTA, sidebar footer is hidden unless `shellVariant === 'fsbo'` (the design shows an `Upload Document` button in the FSBO sidebar footer).

Action mapping:

| Action | Behavior |
| --- | --- |
| `new-transaction` | `openNewTransaction()` |
| `upload-legal-packet` | Navigate to `/dashboard/attorney?panel=upload`; Attorney page focuses or opens the legal packet intake |
| `share-milestones` | Navigate to `/fsbo/share` or open the FSBO share modal if a property is selected |
| `ask-agent` | Navigate to `/client/transactions?ask=1` and focus the client question composer |
| `upload-document` | Navigate to `/portal/vendor?panel=upload` and focus the vendor upload intake |
| `ask-ai` | FSBO-only plain-English AI help; navigate to `/fsbo/ask-ai` or open the FSBO AI panel |
| `none` | Render no primary CTA |

The topbar button label must come from config. Do not hardcode `+ New Transaction`.

### 3.11 Role-Specific KPI And Badge Data

Do not force every role through the generic `SidebarKPIs` and `DealStateCounts` shape (deficiency #16). Specifically, `AppLayout` must stop calling `useSidebarKpis()` and `useDealStateCounts()` unconditionally for portal roles, and `getKpiTiles()` must stop returning hardcoded zeros.

Use:

- Internal Agent/TC/Team/Admin: existing `/api/v1/dashboard/sidebar-kpis` and `/api/v1/dashboard/deal-state-counts`.
- Attorney: existing `/api/v1/dashboard/attorney` payload for `filter_counts`, legal health, and release/blocked counts. If performance becomes a concern, add a slim `/api/v1/dashboard/attorney/sidebar-summary` endpoint later.
- FSBO: existing `/api/v1/dashboard/fsbo/overview` payload for property count, `days_to_close_nearest`, `share_links_live`, and `missing_documents_count`.
- Client: `/api/v1/dashboard/client` for transaction/document/milestone counts if badges are needed.
- Vendor: `/api/v1/dashboard/vendor` for open request/upload counts.

Hook signature changes (deficiency #20):

- `useAgentDashboard`, `useTeamDashboard`, `useAttorneyDashboard`, `useAdminDashboard`, `useFsboOverview`, `useClientDashboard`, `useVendorDashboard` must accept `options?: Omit<UseQueryOptions<T>, 'queryKey'|'queryFn'>` and forward it to `useApiFetch`. `AppLayout` then gates each call with `{ enabled: role === 'X' }` so the shell does not fire seven role-dashboard requests for every login.

### 3.12 Topbar Briefing Bar, Search Palette, Notifications

These three surfaces are tenant-scoped today (deficiencies #17–19). They must respect `capability`:

- **`Today's AI Briefing` bar** in the topbar: render only when `shellVariant === 'internal'`. Do not call `useAiBriefing()` for other variants.
- **`SearchPalette`**: read `capability.searchScope` and either filter results or, for `'fsbo-owned' | 'client-owned' | 'vendor-documents'`, suppress the global Cmd-K shortcut and surface a scoped search inside the portal pages instead.
- **`NotificationsPanel`**: read `capability.notificationScope` and pass it to the notifications endpoint so internal communication-audit events do not appear in FSBO/Client/Vendor panels.

### 3.13 Legacy `/notifications` And `/sharing` Routes

`/notifications` and `/sharing` are global protected routes today (deficiency #25). After the FSBO sidebar is corrected to point at `/fsbo/share`:

- Keep `/notifications` reachable from FSBO Help (the design places it there) but route the portal-specific badge through the FSBO overview payload.
- Add a redirect from `/sharing` to `/fsbo/share` when the user is FSBO, so any stale bookmark still works.
- Keep `/sharing` for internal roles as today.

---

## 4. Page-Level Remediation

### 4.1 Solo Agent Dashboard

Current issue: the page over-implements AI Coach, which is not part of MVP for Solo Agent.

Change `src/pages/dashboards/SoloAgentDashboardPage.tsx`:

1. Remove `CoachUpsellBanner` import and both full-width Coach banners.
2. Remove the Coach recommendation rail card.
3. Remove duplicate `AiPortfolioIntel` from the right rail. It already appears in the production/metrics card.
4. Collapse Row 3 to a single full-width Priority Transactions stack.
5. Remove `coachInfoOpen` state and the Coach info modal.
6. Update `WidgetOrderManager` default order to remove any separate `intel` widget if it no longer exists as a standalone widget.
7. Keep `UploadIntakeCard`, `CommandGrid`, `WidgetOrderManager`, and `FloatingAskAi`.
8. Verify the greeting copy reads naturally for TransactionCoordinator (deficiency #26). If "Solo Agent Dashboard" wording appears anywhere on the page, change to neutral copy such as "Your workspace today."

Acceptance:

- No `AI Coach` banner, rail card, or modal appears on Solo Agent dashboard.
- `AiPortfolioIntel` appears once.
- Priority transactions span the available content width.
- TC users see neutral greeting copy.

### 4.2 Team Leader Dashboard

Current issue: Team page shows more Coach surface than MVP allows.

Change `src/pages/dashboards/TeamLeaderDashboardPage.tsx`:

1. Remove the bottom full-width `CoachUpsellBanner`.
2. Remove the small locked Coach note inside the Agent Board if a new rail teaser is added.
3. Add exactly one compact locked Coach teaser in the right rail or `TeamRailFeeds`.
4. The sidebar `AI Coach` item routes to `/dashboard/team?modal=ai-coach`.
5. The page opens one locked Coach modal when `modal=ai-coach`.
6. The teaser may show price/context, but no active Coach workflow, no billing flow, and no generated coaching plan.

Acceptance:

- Team Leader dashboard contains exactly one Coach teaser surface.
- Clicking the sidebar Coach item opens the same locked teaser modal.
- The page still shows team health, intervention queue, agent board, pipeline health, fast filters, and closings next 14 days.

### 4.3 Attorney Dashboard

Current issue: the page is built as a 3-column matter switcher workspace, not the approved Attorney dashboard landing page. It also lacks URL-driven filters and upload intake.

Change `src/pages/dashboards/AttorneyDashboardPage.tsx`:

1. Read `filter` from the URL. Allowed values:
   - `all`
   - `needs-review`
   - `missing-docs`
   - `ready-to-release`
   - `clean-files`
2. Render the page header as `Attorney Dashboard` with `PageTabBar`.
3. Use `data.filter_counts` for tab counts.
4. Add full-width `UploadIntakeCard` for legal packets.
5. Extend `UploadIntakeCard` first. The shipped component takes only `onFilesSelected`, `accept`, `className`. Add props:

   ```ts
   title?: string
   description?: string
   acceptedLabels?: string[]
   badgeLabel?: string
   ```

   Then use Attorney copy:
   - Title: `Upload legal packet`
   - Description: `AI will extract deadlines, compare versions, index exhibits, and flag missing formal documents.`
   - Accepted labels: `PDF`, `DOCX`, `PNG`, `JPG`
   - Accept: `.pdf,.doc,.docx,.png,.jpg,.jpeg`

6. Render the approved command grid:
   - Hero: legal health score, critical approval gates, drift summary
   - Middle: state rules summary with `Open state rules`
   - Rail: recording/release drift summary
7. Render a Matter Card Stack below the grid.
8. Each matter card is expandable. The expanded drawer reuses the existing components:
   - `MatterSummaryRow`
   - `MatterDocChecklist`
   - `MatterTimeline`
   - `MatterActivity`
   - `AiLegalBrief`
   - `MatterPeoplePanel`
   - `SendPacketModal`
9. Handle URL panels:
   - `panel=state-rules` opens `StateRulesModal`
   - `panel=communications` opens or focuses the communication/audit panel
   - `panel=upload` focuses the legal packet upload card
10. Preserve sign-off and packet-release API calls.

Backend/data changes required for Attorney:

1. In `app/services/dashboard_aggregator.py::fetch_attorney`, add a stable `filter_key` to each `matter_card`.
2. Increment `filter_counts.missing_docs`.
3. Populate `drift_summary.missing_formal_docs` from real document/review data (it is hardcoded `0` today, line 603).
4. Prefer per-matter document checks over the current global zero placeholders.
5. Optionally accept `?filter=needs_review` on `GET /api/v1/dashboard/attorney`, but the frontend may filter client-side if all matter cards are loaded. The URL must still use hyphenated UI keys.

Suggested `filter_key` derivation:

| Condition | `filter_key` |
| --- | --- |
| Missing required legal/critical document | `missing-docs` |
| Unsigned review item or no review item created yet | `needs-review` |
| All review items signed and no release row exists | `ready-to-release` |
| Release row exists and no blockers remain | `clean-files` |

Acceptance:

- `/dashboard/attorney?filter=needs-review` opens the page with the Needs Review tab active and matter stack filtered.
- `/dashboard/attorney?filter=missing-docs` has non-zero counts when formal documents are missing.
- `/dashboard/attorney?panel=state-rules` opens the state rules modal.
- The sidebar `+ Upload legal packet` footer button focuses the upload card (no `+ New Matter` button).
- No AI control can check sign-off boxes or release packets.

### 4.4 FSBO Dashboard And Sub-Pages

Current issues:

- Sidebar routes point to internal app routes.
- Portal tabs show six entries instead of the approved four.
- Tab definitions are duplicated in `FsboOverviewPage.tsx` and `pages/fsbo/_shell.tsx`.
- `FsboOverviewPage.FsboTaskList` is wired to `intake.openNewTransaction` for its `onUpload` callback, opening the internal wizard.
- `FsboDocumentsPage` renders `<UploadIntakeCard />` with no handler.

Change `src/pages/fsbo/FsboOverviewPage.tsx` and `src/pages/fsbo/_shell.tsx`:

Use only four portal tabs:

```ts
const FSBO_PORTAL_TABS = [
  { label: 'Overview', to: ROUTES.FSBO },
  { label: 'Properties', to: ROUTES.FSBO_PROPERTIES },
  { label: 'Documents', to: ROUTES.FSBO_DOCUMENTS },
  { label: 'Support', to: ROUTES.FSBO_MILESTONES },
]
```

Notes:

- `/fsbo/milestones` remains the Milestones & Messages page and should include the support contact/boundary area. The top tab label can be `Support` because the design frames this portal tab as support, while the sidebar keeps `Milestones & Messages`.
- `/fsbo/share` and `/fsbo/ask-ai` remain reachable from the sidebar, not the portal tab bar.

Data/backend fixes:

1. `GET /api/v1/dashboard/fsbo/overview` already returns `share_links_live`; keep it.
2. Stop returning hardcoded `missing_documents_count = 0` and per-property `missing_docs_count = 0` when documents exist.
3. Populate `new_messages_count` from client-visible messages/communication logs if available.

Upload fixes:

1. Replace FSBO calls to `intake.openNewTransaction()` (currently used in `FsboOverviewPage` for the task list `onUpload` prop) with scoped upload behavior or navigation to `/fsbo/documents`.
2. Provide an `onFilesSelected` handler to every `UploadIntakeCard` on FSBO, Client, and Vendor pages. It must upload through the customer/portal upload endpoint or open the correct scoped upload flow. It must not silently do nothing.
3. FSBO cannot open the internal New Transaction wizard from dashboard or document flows.

Acceptance:

- FSBO sidebar uses Workspace and Help sections with FSBO routes.
- FSBO portal tabs are exactly Overview, Properties, Documents, Support on overview and sub-pages.
- Sharing badge shows `Live` only when `share_links_live > 0`.
- FSBO upload actions do not open the New Transaction wizard.
- Every `UploadIntakeCard` instance has a real `onFilesSelected` handler.

### 4.5 Client Portal

No approved dashboard design exists, but the current shell must be made safe.

Required changes:

1. Client sidebar only shows My Transactions, Documents, Milestones, Agent Info.
2. Topbar descriptor is `Your Workspace`.
3. Primary CTA is client-safe: `Ask your agent` (action `ask-agent`), not `Ask AI`.
4. The CTA routes to `/client/transactions?ask=1` and focuses the existing question composer.
5. Client cannot see internal dashboard nav, internal search results, AI Suggestions, vendor tools, task queue, analytics, or communication audit.
6. The topbar `Today's AI Briefing` bar is suppressed for Client.

### 4.6 Vendor Portal

Required changes:

1. Import `VendorDocumentPortalPage` in `App.tsx`.
2. Replace the `<Navigate to={ROUTES.CLIENT_DOCUMENTS} replace />` element on the `/portal/vendor` route with `<VendorDocumentPortalPage />`.
3. `DashboardRouter` (via `getLandingRoute`) sends Vendor to `/portal/vendor`.
4. `dashboardShellConfig.Vendor.landingRoute = ROUTES.VENDOR_PORTAL`.
5. Vendor sidebar shows only vendor document/request entries.
6. Vendor primary CTA focuses scoped document upload (`upload-document` action).
7. Provide an `onFilesSelected` handler for the `<UploadIntakeCard />` instance in `VendorDocumentPortalPage`.
8. Remove Vendor from the `RoleRoute` on `/client/documents` (recommended) so Vendor cannot fall back into the Client page.

### 4.7 Admin Dashboard

No design change is required for body content.

Required shell changes:

1. Descriptor: `Admin Console`, including when Admin is viewing `/dashboard/team` (deficiency #27).
2. Keep Admin internal/team/admin navigation.
3. Do not label Admin as `Team Command`.
4. Ensure Admin dashboard body remains `/dashboard/admin`.

---

## 5. Design Dispositions

| Design item | Disposition |
| --- | --- |
| Solo Agent omits Vendor Directory, AI Email Review, Vendor Proposals | Keep those nav items. They are shipped Milestone 4.2 / 4.3 features. |
| Solo Agent shows no AI Coach | Remove AI Coach surfaces from Solo Agent. |
| Team Leader includes AI Coach | Keep one locked teaser only. No active Coach workflow in MVP. |
| Team Leader design has smaller Team nav | Keep shipped Team Overview, Team Members, Task Templates, Vendor Templates, Communication Audit. |
| Attorney design has role-specific sidebar | Adopt it using URL routes / query params. |
| Attorney design lists Settings under Intelligence | Keep Settings in shared profile/settings access for consistency. |
| Attorney design Recording Calendar link opens `StateModal()` | Route-based instead: `/attorney/recording-calendar`. State Rules remains a separate modal. |
| Attorney design has `+ New Matter` in sidebar footer | Replace with the Attorney `primaryCta` (`Upload legal packet`). No `New Matter` action exists. |
| FSBO design has Workspace/Help split | Adopt it. |
| FSBO design top tabs are Overview/Properties/Documents/Support | Adopt four tabs everywhere FSBO portal tabs are rendered. |
| FSBO design always shows Sharing Live badge | Make it data-driven: show only when `share_links_live > 0`. |

---

## 6. Testing And Verification

Frontend tests to add or update:

1. `AppLayout` role matrix:
   - Agent no team: descriptor `Transaction OS`, internal nav, New Transaction CTA, briefing bar present.
   - Agent with team: descriptor `Team Command`, team landing/nav.
   - TeamLead: descriptor `Team Command`, Team section, locked AI Coach item.
   - Attorney: descriptor `Attorney Workspace`, Attorney sidebar, Upload Legal Packet CTA, no internal briefing bar.
   - FSBO: descriptor `FSBO Workspace`, Workspace/Help sidebar, Share milestones CTA, no internal briefing bar.
   - Client: descriptor `Your Workspace`, client-only nav, `Ask your agent` CTA, no internal nav, no internal briefing bar.
   - Vendor: descriptor `Vendor Portal`, vendor-only nav, Upload document CTA, no internal nav, no internal briefing bar.
   - Admin on `/dashboard/team`: descriptor `Admin Console`, not `Team Command`.
2. `DashboardRouter` / `getLandingRoute`:
   - no-team Agent/TC → `/dashboard/agent`.
   - team Agent/TC → `/dashboard/team`.
   - TeamLead → `/dashboard/team`.
   - Attorney → `/dashboard/attorney`.
   - Admin → `/dashboard/admin`.
   - Client → `/client/transactions`.
   - FSBO → `/fsbo`.
   - Vendor → `/portal/vendor`.
   - Unknown role → `/unauthorized` (not `/dashboard/agent`).
3. `TeamDashboardGuard`: no-team Agent typing `/dashboard/team` is bounced to `/dashboard/agent`; TeamLead and Admin pass through; team-member Agent/TC passes through.
4. `/portal/vendor` route renders `VendorDocumentPortalPage`, not `ClientDocumentsPage`.
5. Brand lockup and sidebar Dashboard link both resolve to the same landing per role.
6. Post-login return-location: a Vendor whose last visited URL was `/client/documents` is redirected to `/portal/vendor` on re-login.
7. Solo dashboard:
   - no `CoachUpsellBanner`.
   - no Coach recommendation.
   - one `AiPortfolioIntel`.
   - greeting copy reads naturally for TC users.
8. Team dashboard:
   - exactly one locked Coach teaser.
   - `?modal=ai-coach` opens locked modal.
9. Attorney dashboard:
   - each `filter` query activates the correct tab.
   - `panel=state-rules` opens modal.
   - `panel=upload` focuses upload.
   - missing-doc count is rendered when backend sends it.
   - sidebar footer renders `Upload legal packet`, not `+ New Matter`.
10. FSBO:
    - four portal tabs in `FsboOverviewPage` and `_shell`.
    - sidebar routes are `/fsbo*`, not internal routes.
    - upload actions do not open `NewTransactionModal`.
    - every `UploadIntakeCard` has a non-null `onFilesSelected`.
11. Vendor: `/portal/vendor` renders `VendorDocumentPortalPage`; Vendor is no longer allowed on `/client/documents` (if §4.6.8 is taken).
12. Search palette and notifications panel respect `capability.searchScope` / `capability.notificationScope` per role.

Backend tests to add or update:

1. `test_dashboard_attorney.py`:
   - `filter_counts.missing_docs` increments when required docs are missing.
   - `drift_summary.missing_formal_docs` reflects real document state.
   - every `matter_card` includes `filter_key`.
   - released/blocked/release-ready states map to expected filter keys.
   - non-Attorney cannot access attorney endpoint.
2. `test_dashboard_fsbo.py`:
   - `missing_documents_count` and per-property `missing_docs_count` are computed.
   - `share_links_live` ignores revoked/expired links.
   - overview is scoped to the FSBO user.
3. `test_dashboard_vendor.py`:
   - vendor dashboard exposes only upload requests, own uploads, open date requests, response chips, and safe thread summaries.
4. Existing auth/RBAC tests:
   - Client/FSBO/Vendor cannot create transactions through internal routes.

Manual QA:

- Capture desktop and mobile screenshots for Solo Agent, Team Leader, Attorney, and FSBO.
- Verify no sidebar text disappears on FSBO.
- Verify topbar descriptors for all roles.
- Verify browser refresh preserves Attorney filters and panels.
- Verify dashboard links never land on a blank page or a 404.
- Verify a Vendor login lands on `/portal/vendor` even when the user's last session ended elsewhere.

---

## 7. Execution Order

1. **Shell safety first**
   - Add `getBrandDescriptor(user)` and `getLandingRoute(user)` helpers in `dashboardShellConfig.ts`.
   - Extend `PrimaryCta['action']` union (`upload-document`, `ask-agent`).
   - Update Vendor and Client capabilities.
   - Wire `dashboardShellConfig` into `AppLayout` (descriptor, sidebar sections, primary CTA, search scope, notification scope, KPI source).
   - Stop Client/Vendor/FSBO internal nav leakage.
   - Suppress internal briefing bar / Cmd-K search palette / tenant notifications for portal roles.

2. **Routing remediation (§2.2)**
   - Fix `DashboardRouter.tsx` Vendor case → `/portal/vendor`.
   - Set `DashboardRouter` fallback → `/unauthorized`.
   - Fix `dashboardShellConfig.Vendor.landingRoute` → `/portal/vendor`.
   - Replace `<Navigate to={ROUTES.CLIENT_DOCUMENTS} replace />` on `/portal/vendor` with `<VendorDocumentPortalPage />`; import the page in `App.tsx`.
   - Wrap `/dashboard/team` with `TeamDashboardGuard` for no-team Agent/TC redirect.
   - Update sidebar Dashboard link to use `getLandingRoute(user)`.
   - Invalidate stale return-location URLs that fail the current role's `RoleRoute` check.
   - Add `/sharing` → `/fsbo/share` redirect for FSBO users.

3. **Hook signature updates**
   - Add optional `options` parameter to all role-dashboard hooks in `useDashboard.ts`.
   - Replace `getKpiTiles()` and `useDealStateCounts()` reads with role-aware sources.

4. **Coach cleanup**
   - Remove Solo Coach surfaces.
   - Reduce Team Coach to one locked teaser plus sidebar deep link.

5. **Role metric data**
   - Fix Attorney `filter_counts.missing_docs`, `drift_summary.missing_formal_docs`, and add `filter_key`.
   - Fix FSBO missing document / message counts.

6. **Attorney page restructure**
   - Header tabs, legal upload intake, command grid, matter card stack, URL panels.
   - Extend `UploadIntakeCard` with copy props before use.
   - Add `ROUTES.ATTORNEY_RECORDING_CALENDAR` route and wrapper.
   - Sidebar footer renders Attorney primaryCta.
   - Preserve sign-off / release behavior.

7. **FSBO page/sidebar remediation**
   - Workspace/Help sidebar.
   - Four portal tabs in both tab definitions.
   - Scoped uploads with real handlers; no New Transaction wizard.

8. **Client/Vendor polish**
   - Client-safe CTA and nav.
   - Vendor portal page route, scoped upload behavior, optional removal of Vendor from `/client/documents`.

9. **Tests and visual QA**
   - Add the role matrix and routing tests before final screenshots.

---

## 8. Out Of Scope

- Building a functional AI Coach product.
- Replacing the shared shell with a new layout system.
- Pixel-perfect recreation of the static HTML files.
- New transaction detail pages for every role.
- Separate full Recording Calendar product if the MVP alias / wrapper satisfies the link.
- Broader redesign of Admin dashboard body content.
- Adding portal-scoped notification or search endpoints — the scope flags will be plumbed, but a dedicated portal search service can wait if the existing endpoint can already filter by scope.

---

## 9. Final Acceptance Criteria

Milestone 5.1 remediation is complete only when:

1. Every role displays the correct topbar descriptor (Admin always shows `Admin Console`, even on `/dashboard/team`).
2. Every role sees only the sidebar nav allowed for that role.
3. Client, FSBO, and Vendor roles do not see internal navigation, the internal briefing bar, internal Cmd-K search results, or internal notifications.
4. Primary CTA behavior is role-specific and never opens the wrong workflow; the CTA appears in exactly one surface per role (no topbar/sidebar duplication).
5. Solo Agent dashboard has no AI Coach surfaces.
6. Team Leader dashboard has exactly one locked AI Coach teaser.
7. Attorney dashboard uses URL-driven filter tabs, legal upload intake, command grid, matter card stack, and URL-driven modals/panels.
8. Attorney missing-doc counts (`filter_counts.missing_docs`, `drift_summary.missing_formal_docs`) are real and non-hardcoded; every `matter_card` has a `filter_key`.
9. FSBO sidebar and portal tabs match the approved design structure; every FSBO/Client/Vendor `UploadIntakeCard` has a real handler.
10. Vendor lands on `/portal/vendor` (rendering `VendorDocumentPortalPage`) from all three layers: `DashboardRouter`, `dashboardShellConfig`, and the `App.tsx` route element. The brand lockup, sidebar Dashboard link, and post-login return all agree.
11. A no-team Agent/TC cannot manually access `/dashboard/team`. An unknown role hitting `/dashboard` is sent to `/unauthorized`.
12. All dashboard/sidebar links navigate to existing routes or URL-controlled panels.
13. Frontend and backend role matrix tests cover the above, including the explicit Vendor three-layer routing assertion.
