# Logic review: Staff workspace resolution plan

**Date:** 2026-09-08  
**Plan reviewed:** `STAFF_WORKSPACE_RESOLUTION_PLAN_2026-09-08.md`  
**Method:** Live `velvet-elves-frontend` and `velvet-elves-backend`. Docs in `velvet-elves-data` used as context only. Where a doc disagrees with the code or with the two-layer rule (role is a product; owner is a badge), the code and the rule win.

**Verdict:** The two-layer model is sound. Do **not** implement the plan as written. Amend the five must-fix items below, then ship.

**Follow-up:** Those amendments were folded into `STAFF_WORKSPACE_RESOLUTION_PLAN_2026-09-08.md` (same day). This review is the rationale, not the working plan.

---

## Verdict in one page

Keep: owner jobs on **avatar + home** (no pinned Owner/My setup sidebar); Team Command is **Team Lead-only**; File Desk is not Solo Agent; **keep `/team`**; do not auto-promote; do not 403 GET of inherited task templates.

Do not keep as written: which leak to close for Team Lead scope; “team posture” copy; locking `GET /dashboard/agent` against TC in the same breath as composing File Desk from that API; Owner-first Settings; Team Lead owner with no tenant Invite people on the home.

Cut from must-ship: **P4 File defaults** (new product). **B-TC6** (GET templates 200) is not a defect.

---

## 1. What the plan gets right

The decision in §0 is the right product: each signup role is a desk; ownership is a badge on that desk. That matches how the code already splits `isAdminIdentity` vs `canManageWorkspace`, `require_identity_roles` vs `require_role` owner bypass, and exact-role dashboard routes.

Superseding the old identity-plan line that sent **teamed Agents to Team Command** is correct. `TeamLeaderDashboardPage` is a manager desk. `fetch_agent` is personal (created/assigned). An invited Agent who lands on `/dashboard/agent` still has a working desk. They lose the stolen Team Lead console, not their files.

Keeping **Team Overview** and scoping a Team Lead to **their team** is correct. `TeamOverviewRouter` already does that split. `GET /admin/brokerage/overview` already filters Team Lead users, teams, and aggregates. `team_scope.py` already fails closed. The page should stay.

Avatar + prepaid chip without a pinned Owner sidebar matches the IA that was already rejected. Fake Coach **purchase** CTAs should stay gone. Writes on task templates should stay `require_identity_roles`.

---

## 2. Must-fix (logic errors)

### 2.1 The plan points at the wrong Team Lead leak

**Plan:** Close `GET /users/` “team of one → whole tenant”; treat that as the Overview bug.

**Code:** `TeamLeadOverviewPage` does **not** call `/users/` (comment explicitly avoids it). Overview scoping in `admin_brokerage.py` is already team-only.

The live leak is `fetch_team` in `dashboard_aggregator.py` (~320–327): if a Team Lead’s `team_id` is set but there are no *other* members, the **agent board** widens to every team-eligible user in the tenant. `team_scope.py` / intervention queue stay fail-closed. Same dashboard, two scopes.

**Fix:** P3 first job is **remove that implicit-team fallback**. Keep `/team`. `users.py` fallback is a **Teams “Add member”** issue, not Overview.

### 2.2 “Team posture” is not what the API does

**Plan P0:** Team Lead sets *team* posture; Admin sets tenant floors.

**Code:** `PUT /api/v1/automation/settings` writes **tenant** `default_posture`. Team Lead and Admin write the same row. There is no per-team posture table.

**Fix:** Copy should say **workspace default**. Admin AI Governance remains floors / kill switches. Do not teach a Team Lead they have a private team posture unless you build one (out of scope).

### 2.3 P2 contradicts itself on the Agent dashboard API

**Plan:** File Desk composes from `useAgentDashboard` **and** `/dashboard/agent` stays Agent-only.

**Code:** SPA route is **already** Agent-only (`App.tsx`). `GET /dashboard/agent` is `require_exact_roles(Agent, TransactionCoordinator)` because File Desk uses that payload.

**Fix:** Do not 403 TC on that GET until a coordinator endpoint exists. The P2 “exact-role Agent-only” SPA row is already done — drop it.

### 2.4 Owner-first Settings fights identity setup

**Plan A4:** Compact Owner row **above** Personal.

**Judgment:** P0 avatar Billing / Change my role already solves discovery of owner jobs. Personal is Connections, representation, fees, automation — the identity half of independence. Putting Owner first buries that and duplicates the existing Owner group.

**Fix:** Keep Personal first. Owner jobs on avatar + home chip.

### 2.5 Team Lead owner still cannot hire from the desk

**Plan:** Home **Invite people** for Agent/TC/Admin owners; Team Lead only **Invite to team**.

**A3** is tenant Users & Invites (hire an Admin, hire anyone). A Team Lead founder who owns the tenant still needs that without becoming Admin. Invite to team is the *role* CTA; tenant invite is the *owner* CTA.

**Fix:** Team Command: team-locked Invite to team **and**, if `is_tenant_owner`, Invite people.

---

## 3. Should-fix

| Issue | Why | Fix |
|---|---|---|
| Closing `users.py` fallback | `ManageTeamMembersPanel` lists people *not* on this team from `GET /users/`. A team-of-one TL would lose Add-existing. | If invite-only is the rule, say so and hide Add-existing. |
| Comm audit in Team nav | Admin already has Oversight → Communication Audit. | Team-group item for **TeamLead only**. |
| B-TL2 reorder | KPIs + three Team items before Deals may bury Deals instead. | Measure at 1366×768; do not assume. |
| Intake CTA | No “intake” filter. Documents has `?tab=missing` / `ai_priority`. | Link that tab. |
| Hide Clients for TC | TC still fields client Q&A. | Keep Contacts; prove Clients is origination-only first. |
| P4 File defaults | New product, thin spec, optional wizard follow-up. | Not a gate for independence. |

---

## 4. Already true — do not reopen

- `GET /task-templates` 200 for any signed-in staff: inherit-for-files. Writes already identity-gated. **B-TC6 is not a defect.**
- TC landing already ignores `team_id`. Only **brand** is wrong (`Team Command`). P1 brand fix is the TC item.
- Communication audit **route** already allows Team Lead. Missing from TL **sidebar**.
- Representation + account fee defaults exist (`identityPrefs.ts`). localStorage is a one-time migrate.
- Fake Coach **Add** banner is gone from staff dashboards. Analytics **AI Coach Pro** lock (`ProGateCard`) is still real leftover (S1).
- `ROLE_IDENTITY` §3.1 (teamed Agent → Team Command) and `OWNER_INDEPENDENT` §4.1 (pinned My setup / Owner sidebar) are **stale**. Do not implement those sections to “comply” with this plan.

---

## 5. Recommended ship order (after amend)

1. **P0** — Avatar Billing + Change my role; prepaid chip; Invite people on **all** owner homes including Team Lead; automation copy without “become Admin” or fake team posture; Personal stays first in Settings.  
2. **P1** — Landings/brands; Agent/TC never render Team Command; team dashboard API TeamLead+Admin only. Update `DashboardRouter` comments and `dashboardShellConfig.test.ts`.  
3. **P2** — Real File Desk; intake → `?tab=missing`; nav order. Keep `GET /dashboard/agent` for TC.  
4. **P3** — Remove `fetch_team` implicit fallback; keep `/team`; TL-only comm-audit nav; team-locked invite modal; playbook links from Team Command.  
5. **P5** — Documents copy; hide AI Coach Pro.  
6. **P4** — Optional.  
7. **P6** — Four-role QA at 1366×768, including two-team Overview **and** Team Command board.

---

## 6. Success (unchanged)

A founder stays the role they picked, can pay and hire from that desk, and does not need Admin Console unless they **are** Admin. Team Overview stays; a Team Lead sees **only their team**. File Desk is not Solo Agent. Team Command is not an invited Agent’s home.
