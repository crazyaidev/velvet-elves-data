# Navigation IA Plan — Disentangling the "Team" and "Admin" Sidebar Groups

**Status:** Phase 1 implemented (2026-05-20) — see *Implementation status* below
**Date:** 2026-05-20
**Scope:** Internal-shell left-sidebar navigation only (`AppLayout` → `buildSection`). No change to portal shells (FSBO / Client / Vendor / Attorney), page contents, or backend authorization.
**Goal:** Re-categorize the sidebar so the **Team** group contains only team-people-management surfaces and the **Admin** group contains only tenant-administration surfaces — driven by each page's *purpose, functionality, and access tier*, not by an arbitrary split.

### Implementation status

**Phase 1 — shipped (2026-05-20).** All decisions in §7.2 are resolved; the as-built navigation is recorded in §7.1.

- `AppLayout.tsx` — `team` group dropped Communication Audit; `admin` group dropped the duplicate "Users" and now holds **Communication Audit** only. (`Organization Settings` was briefly added then removed — it duplicated the standalone Settings footer link; see D3.)
- `CommunicationAuditPage.tsx` — breadcrumb root changed from `👥 Team` to `🛡 Admin` (`ShieldCheck` icon) to match its new group; unused `Users` import removed.
- No route, guard, or backend change. `tsc` and `eslint` clean.

**Still open:** §8.5 documentation sync (this is the only outstanding Phase 1 item), plus Phase 2/3.

---

## 1. Why this plan exists

In the internal sidebar, the **Team** and **Admin** groups overlap and blur. The Team group currently carries four pages that are administrative in nature and live under the `/admin/*` route namespace, while the Admin group is a single entry that *duplicates* one of them. There is no consistent rule for what lands in which group, so neither label means what it says.

This plan establishes a categorization rule, classifies every affected page against it, and specifies the code and documentation changes needed to align the navigation with the product's role model.

---

## 2. Evidence base (what was reviewed)

| Source | What it told us |
| --- | --- |
| `velvet-elves-frontend/src/layouts/AppLayout.tsx` (`buildSection`, lines 307–324) | Exact current contents of the `team` and `admin` sidebar groups. |
| `velvet-elves-frontend/src/layouts/dashboardShellConfig.ts` (lines 87–112) | Which roles see which groups: `team` → TeamLead + Admin; `admin` → Admin only. |
| `velvet-elves-frontend/src/utils/constants.ts` (`ROUTES`, lines 117–144) | Route constants — including admin routes that are **defined but unused**. |
| `velvet-elves-frontend/src/App.tsx` (lines 348–416) | Registered routes and their `requiredRole` guards (mostly `TeamLead`, not `Admin`). |
| `velvet-elves-frontend/src/pages/TeamPage.tsx`, `pages/users/AdminUsersListPage.tsx` | Confirmed real purpose of `/team` (roster overview) vs `/admin/users` (member management + invites). |
| `velvet-elves-frontend/src/pages/settings/SettingsPage.tsx` (tabs, lines 40–47) | Tenant-admin config (Company, Branding, AI Configuration, Task Templates) already lives here, admin-gated via `hasMinimumRole(role, 'Admin')`. |
| `velvet-elves-backend/app/api/v1/{task_templates,vendor_communications,communication_logs,audit_logs}.py` | Ground-truth role gates (see access table in §4). |
| `velvet-elves-data/FRONTEND_UI_WORKFLOW_LOGIC.md` (Shared Shell line 45; §10 Admin Section) | The spec's own IA — and its internal inconsistency (see §3, problem 5). |
| `velvet-elves-data/SYSTEM_DESIGN.md` (role model line 87, endpoint roles lines 913–1080) | Role hierarchy and per-endpoint role expectations. |

---

## 3. Starting state (before this change)

> The tables below capture the navigation **as it was** prior to Phase 1. The §3.2 problems are what this plan set out to fix; the as-built result is in §7.1.

### 3.1 Sidebar groups as they were

**`team` group** — shown to **TeamLead + Admin** (`AppLayout.tsx:307`):

| Label | Route | Route guard (`App.tsx`) |
| --- | --- | --- |
| Team Overview | `/team` (`ROUTES.TEAM`) | `requiredRole="TeamLead"` |
| Team Members | `/admin/users` (`ROUTES.ADMIN_USERS`) | `requiredRole="TeamLead"` |
| Task Templates | `/admin/task-templates` (`ROUTES.ADMIN_TEMPLATES`) | `requiredRole="TeamLead"` |
| Vendor Templates | `/admin/vendor-templates` (`ROUTES.ADMIN_VENDOR_TEMPLATES`) | `requiredRole="TeamLead"` |
| Communication Audit | `/admin/communications` (`ROUTES.ADMIN_COMMUNICATIONS`) | `requiredRole="TeamLead"` |

**`admin` group** — shown to **Admin only** (`AppLayout.tsx:318`):

| Label | Route | Route guard |
| --- | --- | --- |
| Users | `/admin/users` (`ROUTES.ADMIN_USERS`) | `requiredRole="TeamLead"` |

### 3.2 Problems

1. **Duplicate destination.** "Team Members" (Team group) and "Users" (Admin group) both resolve to `/admin/users`. An Admin sees the same page twice, under two labels, in two groups.
2. **The Team group is mostly administrative.** Four of five Team items live under `/admin/*` and are documented in the spec's *Admin Section* (§10.1, §10.3). Only **Team Overview** is genuinely team-scoped. The label "Team" does not describe its contents.
3. **The Admin group is anemic and redundant.** It contributes zero unique destinations — its only item duplicates a Team item.
4. **Documented admin surfaces are missing entirely.** `ROUTES.ADMIN_CONFIDENCE`, `ADMIN_AUDIT_LOGS`, `ADMIN_TENANT`, `ADMIN_TEMPLATE_IMPORT` exist in `constants.ts` (lines 132–135) but have **no page component, no registered route, and no nav entry**. Most of that functionality has instead been folded into `/settings` tabs (Company / Branding / AI Configuration), admin-gated — so "tenant administration" is hiding inside the Settings page rather than living in the Admin group.
5. **The spec contradicts itself.** `FRONTEND_UI_WORKFLOW_LOGIC.md` Shared Shell (line 45) says *Team = "Agents, Task Templates"*, while §10 *Admin Section* files Users, Task Templates, AI Confidence, Audit Logs, and Tenant Settings under **Admin**. The build follows neither cleanly.
6. **Same page, two homes.** Task Templates appears both as a nav page (`/admin/task-templates`, in Team) **and** as a Settings tab (`SettingsPage.tsx:45`). This is the same Team/Admin confusion in miniature.

---

## 4. The access model (ground truth from the backend)

The split should track the role model, because that is the real, enforced distinction. Backend gates:

| Capability | Endpoint(s) | Roles allowed | Source |
| --- | --- | --- | --- |
| List/create/update/deactivate task templates | `/task-templates` | Admin **+** TeamLead | `task_templates.py:91,209,267` |
| Import task templates (CSV) | `/task-templates/import` | **Admin only** | `task_templates.py:323` |
| Create/edit vendor comm templates | `/vendor-communications/templates` | Admin **+** TeamLead | `vendor_communications.py:190,211` |
| Deactivate vendor comm template | same | **Admin only** | `vendor_communications.py:232` |
| View communication logs | `/communication-logs` | Agent / TC / TeamLead / Admin | `communication_logs.py:53` |
| Fulfill / mint export download | `/communication-logs/exports/...` | **Admin only** | `communication_logs.py:357,391,462` |
| List tenant-wide audit logs | `/audit-logs` | **Admin only** | `audit_logs.py:29` |
| View entity-scoped audit logs | `/audit-logs/{entity}` | Admin **+** TeamLead | `audit_logs.py:55` |
| Edit tenant (branding, name, AI provider) | `/tenants/current` | **Admin only** (client mirrors via `canEditTenant`) | `SettingsPage.tsx:139` |
| Change user role / deactivate user | `/users/{id}/role`, `/admin/users/{id}` | **Admin only** | `SYSTEM_DESIGN.md:916–917` |
| List users / send invitation | `/admin/users`, `/admin/invitations` | Admin **+** TeamLead (invite: Agent+) | `SYSTEM_DESIGN.md:913,919` |

**The line that matters:** some surfaces are *shared management* a Team Lead legitimately operates (roster + invites, task/vendor templates, log viewing); others are *tenant governance* only an Admin performs (role changes, deactivation, audit logs, tenant/AI config, import, export fulfillment). The navigation should make that line legible.

---

## 5. Categorization criteria

A page belongs to **Team** when **both** hold:
- **Purpose:** it manages a team's *people* or its *shared operating playbook* (roster, invitations, the task/vendor template library the team runs on).
- **Access:** a Team Lead can use its primary function (Admin + TeamLead), i.e. it is not Admin-exclusive.

A page belongs to **Admin** when **either** holds:
- **Purpose:** tenant-wide *governance, configuration, or compliance* that is the Administrator's responsibility and is independent of any one team (tenant/AI settings, audit logs, communication compliance, destructive user administration).
- **Access:** its primary function is **Admin-only**.

Where a page has a shared "view/manage" surface but Admin-only "destructive/governance" actions (e.g. Users), it is **classified by its primary day-to-day purpose** and the Admin-only actions stay gated *within* the page. This keeps one canonical destination instead of duplicating the entry across both groups.

---

## 6. Page-by-page classification

| Page | Current group | Proposed group | Rationale |
| --- | --- | --- | --- |
| Team Overview (`/team`) | Team | **Team** | Pure team-people overview (roster, seats, invites snapshot). Already correct. |
| Team Members (`/admin/users`) | Team **+** Admin (dup) | **Team** (single entry) | Primary purpose = roster + invitations (Admin + TeamLead). Admin-only role-change/deactivation lives on the User Detail page, gated. Remove the duplicate "Users" entry from Admin. |
| Task Templates (`/admin/task-templates`) | Team | **Team** | The team's task playbook; Admin + TeamLead. Stays with the team. (Reconcile the duplicate Settings → Task Templates tab; see §8.4.) |
| Vendor Templates (`/admin/vendor-templates`) | Team | **Team** ✅ | Vendor-comms playbook; Admin + TeamLead create/edit. Pairs naturally with Task Templates as "operating standards." (D1 resolved: Team.) |
| Communication Audit (`/admin/communications`) | Team | **Admin** ✅ | Compliance/oversight surface; export *fulfillment* is Admin-only. Not "managing my team's people." Breadcrumb updated to `Admin › Communication audit`. (D2 resolved: Admin.) |
| "Users" duplicate (`/admin/users`) | Admin | **removed** ✅ | Exact duplicate of Team Members. |
| Tenant / Branding / AI config | (in `/settings` tabs) | **Settings footer link** | Already admin-gated in Settings and reachable via the standalone Settings link at the bottom of the sidebar. **Not** duplicated as an Admin-group entry (D3 resolved). |
| AI Confidence (`/admin/confidence`) | — (unbuilt) | **Admin** (future) | Documented §10.6, Admin-only. Not yet implemented; either build standalone or treat the Settings → AI Configuration tab as canonical. |
| Audit Logs (`/admin/audit-logs`) | — (unbuilt) | **Admin** (future) | Documented §10.7, Admin-only. Build + route before surfacing. |

---

## 7. Recommended target IA

### 7.1 Groups and visibility

**Team** — visible to **TeamLead + Admin** (unchanged audience):
1. Team Overview → `/team`
2. Team Members → `/admin/users`
3. Task Templates → `/admin/task-templates`
4. Vendor Templates → `/admin/vendor-templates`

**Admin** — visible to **Admin only** (unchanged audience):
1. Communication Audit → `/admin/communications`
2. *(future)* Audit Logs → `/admin/audit-logs`
3. *(future)* AI Confidence → `/admin/confidence` *(or fold into Settings → AI Configuration)*

Tenant/AI configuration is **not** an Admin-group entry: it lives in the admin-gated tabs of the standalone Settings link at the sidebar footer (D3). Adding a second "Organization Settings" entry would recreate the same duplicate-destination problem this plan removed.

Result: every Team item is team-people/playbook and TeamLead-usable; every Admin item is tenant governance/compliance. No route appears in two groups.

**Breadcrumbs follow the group.** Each page's top-bar breadcrumb names its group, so a moved page's breadcrumb moves with it. Communication Audit now reads `Admin › Communication audit` (was `Team › …`). Pages that stayed put were verified unchanged: Team Overview, Team Members, Task Templates, Vendor Templates, and the User Detail / Task Template Detail pages all already read `Team › …`.

**Communication Audit visibility nuance (D2, resolved → Admin):** the *viewing* endpoint allows TeamLead, but *export fulfillment* is Admin-only and the surface is fundamentally compliance/oversight, so it lives in the Admin group and is hidden from TeamLeads in-nav. The route guard is still `requiredRole="TeamLead"`, so a Team Lead who needs read access can still reach it by URL; if product wants it back in the TeamLead sidebar, the fallback is to return it to Team (accepting a slightly less clean split).

### 7.2 Resolved decisions

- **D1 — Vendor Templates placement → Team.** Pairs with Task Templates as the team's operating-standards library; TeamLead-usable. *(Implemented.)*
- **D2 — Communication Audit placement → Admin.** Compliance/oversight surface with Admin-only export fulfillment; hidden from the TeamLead sidebar, still URL-reachable per its `TeamLead` route guard. *(Implemented.)*
- **D3 — Tenant administration home → standalone Settings link.** Kept tenant/AI config in the admin-gated `/settings` tabs reached via the existing footer link; did **not** build the spec's standalone `/admin/tenant` + `/admin/confidence` pages, and did **not** add a duplicate "Organization Settings" entry to the Admin group. *(Implemented.)*
- **D4 — Route namespace → no change now.** Team-scoped pages stay under `/admin/*` to avoid breaking bookmarks and existing redirects (e.g. `ADMIN_COMMUNICATION_EXPORTS`). Optional later cleanup; labels and grouping carry the IA, URLs can lag. *(Deferred — Phase 3.)*

---

## 8. Implementation plan

### 8.1 `AppLayout.tsx` — the two `buildSection` cases ✅ implemented

`team` case → dropped `Communication Audit`:
```ts
case 'team':
  return {
    label: 'Team',
    items: [
      { to: ROUTES.TEAM, icon: '👥', label: 'Team Overview' },
      { to: ROUTES.ADMIN_USERS, icon: '👤', label: 'Team Members' },
      { to: ROUTES.ADMIN_TEMPLATES, icon: '📖', label: 'Task Templates' },
      { to: ROUTES.ADMIN_VENDOR_TEMPLATES, icon: '📨', label: 'Vendor Templates' },
    ],
  }
```

`admin` case → removed the duplicate `Users` link; Admin group is now Communication Audit only:
```ts
case 'admin':
  return {
    label: 'Admin',
    items: [
      { to: ROUTES.ADMIN_COMMUNICATIONS, icon: '💬', label: 'Communication Audit' },
      // future, once built + routed:
      // { to: ROUTES.ADMIN_AUDIT_LOGS, icon: '📜', label: 'Audit Logs' },
    ],
  }
```
Tenant/AI config is intentionally absent — it stays in the standalone Settings footer link (D3).

### 8.1a `CommunicationAuditPage.tsx` — breadcrumb ✅ implemented

The page moved Team → Admin, so its top-bar breadcrumb root changed to match:
```tsx
// before: <Users …/> Team   →   after:
<span className="flex items-center gap-[3px] text-ve-charcoal-soft">
  <ShieldCheck className="h-[12px] w-[12px]" />
  Admin
</span>
<span className="text-ve-charcoal-ghost text-[11px]">›</span>
<span className="text-ve-text-muted font-medium">Communication audit</span>
```
`ShieldCheck` is the codebase's existing admin/governance glyph (e.g. the owner badge on `TeamPage`). The now-unused `Users` icon import was removed. Pages that did not change group keep their existing `Team › …` breadcrumbs (verified: Task Templates, Vendor Templates, Team Members, User Detail, Task Template Detail).

### 8.2 `dashboardShellConfig.ts` — no change required ✅ verified

`team` already renders for TeamLead + Admin; `admin` already renders for Admin only (lines 89, 109). The audience is correct; only group *contents* changed. Confirmed after the edit: TeamLead no longer sees Communication Audit, and Admin no longer sees a duplicate Users.

### 8.3 `App.tsx` / routes — align guards, then build the future pages

- **Tighten guards to match intent (optional but recommended):** several `/admin/*` routes use `requiredRole="TeamLead"` (App.tsx:362, 378, 392, 412). For Admin-only surfaces (e.g. tenant-wide audit logs) use `requiredRole="Admin"`; leave shared pages (templates, members) at TeamLead. Keep guards consistent with the §4 table.
- **Future Admin pages:** to surface Audit Logs / AI Confidence in nav, first build the page components and register routes for `ROUTES.ADMIN_AUDIT_LOGS` / `ADMIN_CONFIDENCE`. Until then keep them commented out in the `admin` case so we never ship a dead nav link.

### 8.4 Reconcile the Task Templates dual-home (follow-up)

Task Templates exists as both `/admin/task-templates` (nav) and a Settings tab (`SettingsPage.tsx:45`). Choose one canonical surface; if the nav page is canonical, replace the Settings tab with a link to it (or remove the tab). Out of strict scope for the Team/Admin split but the same root cause — recommend tracking together.

### 8.5 Documentation

- Update `FRONTEND_UI_WORKFLOW_LOGIC.md`: fix the Shared Shell line (45) and §10 Admin Section so both reflect the agreed IA (single source of truth). Note which §10 pages (Confidence, Audit Logs, Tenant Settings) are spec-only vs built-in-Settings.
- Add a short "Navigation IA" note to `SYSTEM_DESIGN.md` capturing the Team-vs-Admin rule from §5 so future pages get placed correctly.

---

## 9. Phasing

- **Phase 1 (✅ shipped, except docs):** §8.1 nav edits + §8.1a breadcrumb + §8.2 verification done. Removed the `/admin/users` duplicate and moved Communication Audit to Admin. No new pages required. **Remaining:** §8.5 documentation sync.
- **Phase 2 (optional):** §8.3 guard tightening; build/route Audit Logs (and AI Confidence if not folding into Settings) and add their nav entries.
- **Phase 3 (cleanup):** §8.4 Task Templates de-duplication; optional `/team/*` URL migration (D4) with redirects.

---

## 10. Acceptance criteria

- ✅ An **Admin** sees `/admin/users` exactly once in the sidebar (no "Users"/"Team Members" duplication).
- ✅ The **Team** group contains only team-people/playbook pages, all usable by a Team Lead.
- ✅ The **Admin** group contains only Admin-scoped governance/compliance entries and at least one unique destination (Communication Audit).
- ✅ Each page's top-bar breadcrumb names its current group (Communication Audit → `Admin › …`; the rest still read `Team › …`).
- ✅ No nav item points to an unregistered route (no dead links).
- ✅ A **TeamLead** sees the Team group and not the Admin group; an **Agent/TC/Attorney** sees neither (unchanged).
- ⬜ Spec docs and build agree on group membership *(pending §8.5)*.

## 11. Risks, non-goals, and notes

- **Risk — hiding Communication Audit from TeamLeads (D2).** Accepted. The `requiredRole="TeamLead"` route guard is unchanged, so a Team Lead can still reach it by URL; only the sidebar entry is Admin-scoped. If product wants it back in the TeamLead sidebar, return it to the Team group.
- **Risk — stale bookmarks** if URLs are migrated. Mitigation: URL changes deferred (D4); existing redirects kept.
- **Non-goal:** changing page contents, backend authorization, or portal (FSBO/Client/Vendor/Attorney) navigation.
- **Note:** tenant-admin config already lives in `/settings` (admin-gated) and is reachable via the standalone Settings footer link. The spec's standalone `/admin/tenant` and `/admin/confidence` pages were **not** built, and no duplicate "Organization Settings" Admin-group entry was added — duplicating a working surface would reintroduce the very problem this change removed.
