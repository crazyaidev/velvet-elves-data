# Staff workspace resolution plan

**Date:** 2026-09-08  
**Updated:** 2026-09-08 — logic review folded in (`STAFF_WORKSPACE_PLAN_LOGIC_REVIEW_2026-09-08.md`)  
**Status:** Plan only. No product source is changed by this document.  
**Repos:** `velvet-elves-frontend`, `velvet-elves-backend`  
**Evidence:** live code + `TEAM_LEAD_AND_TC_WORKSPACE_FINDINGS_2026-09-08.md`  
**Reference (not rules):** `ROLE_IDENTITY_INDEPENDENT_WORKSPACE_PLAN_2026-09-03.md`; `OWNER_INDEPENDENT_WORKSPACE_COMPLETION_PLAN_2026-09-07.md`. Stale vs this plan: identity-plan §3.1 (teamed Agent → Team Command); completion-plan §4.1 (pinned My setup / Owner sidebar).

This plan lists **open** problems and the work to close them. It does not clone Agent onto Team Lead or TC. It does not auto-promote anyone to Admin. It does not reintroduce seat caps.

---

## 0. Decision

> Each signup role is a product. Ownership is a badge on that product. A founder must be able to run the company **from the desk they signed up for**, and that desk must do **that job**.

Two layers, both required:

| Layer | Meaning |
|---|---|
| **A — Owner independence** | Billing, prepaid deals, tenant invites, Change my role — reachable on day one from Agent / TC / Team Lead / Admin chrome at **1366×768**, without becoming Admin. |
| **B — Role product** | Agent = originate and run my files. TC = run the file (intake, docs, tasks, vendors, dates). Team Lead = run the team’s files (blockers, coverage, playbook, invite into *this* team). Admin = brokerage OS. |

**Chrome constraint (do not violate):** Owner jobs and identity setup stay in the **Settings hub** as the catalog. They must *also* be reachable from **avatar + home** so a laptop user never has to discover a buried heading. Do **not** pin new **My setup** or **Owner** sidebar groups. That IA was already rejected. **Keep Personal first** on the Settings hub (Connections, fees, representation, automation). Do not put an Owner row above Personal — avatar + home chip already solve owner discovery; burying setup under Owner fights independence.

**Identity constraint (supersedes older Team Command-for-members copy):** Team Command is the **Team Lead** home. A teamed Agent keeps an **Agent** home (`fetch_agent` is already personal). A TC always keeps **File Desk**, including after they join a team. Brand string never says Team Command for Agent or TC.

**Automation constraint:** `PUT /automation/settings` writes the **tenant / workspace default**, not a per-team posture. Team Lead and Admin write the same row. Copy must say **workspace default**. Admin AI Governance remains floors / kill switches. Do not invent team-scoped automation in this plan.

---

## 1. Already shipped — do not redo

| Done | Keep |
|---|---|
| Four signup identities, OAuth honors role, Team Lead mint + team row | Starter kits |
| Exact-role SPA homes: `/dashboard/agent` is Agent-only; `/dashboard/coordinator` is TC-only | `App.tsx` `RoleRoute` |
| TC **landing** ignores `team_id` (already File Desk) | `getLandingRoute` — only **brand** is still wrong |
| Settings group labeled **Owner**; library cards follow **identity** (not owner) | `settingsCards.ts` |
| Representation (Agent) + fee defaults on the account (`localStorage` is a one-time migrate) | `identityPrefs.ts` |
| Automation hire-guard: Agent/TC tenant `PUT` only while sole staff; Team Lead/Admin always | `can_write_tenant_automation` |
| Template **writes** use `require_identity_roles` (no owner bypass) | `task_templates.py` |
| Template **GET** is inherit-for-all-staff (`get_current_user`) | **Not a defect.** Do not 403. |
| Fake Coach **purchase** CTAs (nav, modal, dashboard Add banner, invited-Agent teaser) | Stay gone. Analytics **AI Coach Pro** lock remains (S1). |
| Change-my-role page, four-way switch, TL mint / leadless, transfer does not force Admin | Keep |
| Scope snap after second internal staff | Keep |
| Team Overview **page** + role split | `TeamOverviewRouter` → `TeamLeadOverviewPage` vs `TeamPage` |
| Overview **API** already team-scopes a Team Lead | `GET /admin/brokerage/overview` |
| `team_scope.py` fail-closed for deal/KPI lists | Keep; Team Command board must match it |
| Communication audit **route** already allows Team Lead | Missing from TL **sidebar**, not from the route |

Stale review items that are **closed** (do not reopen): Settings tiles bouncing Agent owners into Task Templates; representation missing as a field; fees only in `localStorage`; Coach Add banner on Solo Agent home; `GET /task-templates` 200 for Agent/TC (inherit).

---

## 2. Open problems

IDs match the 2026-09-08 findings where they exist. Agent owner gaps are the same **class** as A1–A5 (not “make TL/TC look like Agent”).

### 2.1 Owner independence (all four founder identities)

| ID | Problem | Why it still fails |
|---|---|---|
| **A1** | No prepaid-deal buy UI on home, visible nav, or avatar | Wallet and `/organization?section=billing` work; the desk does not present them. Copy stays **prepaid deals**, never credits. |
| **A2** | Change my role not on home, nav, or avatar | Page exists at `/settings/change-role`. Avatar is Settings / Help / Log Out only. |
| **A3** | Tenant **Users & Invites** not on chrome | Team Lead has role CTA “Invite to team” (wrong destination — §2.3). **Owner** Team Lead still cannot hire an Admin from the desk. TC/Agent founders have **no** hire control on the home. |
| **A4** | Settings **Owner** group sits under Personal, below the 1366×768 fold | Catalog exists; discovery fails. **Fix is avatar + home chip**, not reordering Settings to put Owner first (that buries identity setup). |
| **A5** | Automation copy tells owners to **switch to Admin** after a hire | Backend: Team Lead **keeps** workspace-default `PUT`. Agent/TC lose tenant write (correct) but recovery must be **invite Admin or Team Lead**, stay this identity, per-file override. Do not call it “team posture.” Strings: `SettingsMyAutomationPage`, `AutomationPostureSection`, `tenant_automation_hire_guard_detail`, `require_identity_roles` 403. |

Invitees: still must **not** get A1–A4.

### 2.2 Identity theft (wrong home / brand)

| ID | Problem |
|---|---|
| **B-TL1 / B-TL16** | `getLandingRoute`: Agent with `team_id` → `/dashboard/team`. Brand → **Team Command**. Page is the manager desk. Invited Agents get Team Lead product. `DashboardRouter` comments still describe that. Tests in `dashboardShellConfig.test.ts` still expect it. |
| **B-TC2 / B-TC18** | TC **landing** is already File Desk. `getBrandDescriptor` → **Team Command** when `team_id` is set. That is the TC P1 item. |
| **API** | `GET /dashboard/team` allows Agent and TC. After routing fix, those identities must 403. **Admin stays.** Do **not** 403 TC on `GET /dashboard/agent` (File Desk uses it). |

### 2.3 Team Lead product (Team Command)

| ID | Problem |
|---|---|
| **B-TL2** | Team Overview / Teams sit below the sidebar fold (after Deals + Workflow). Reorder is an experiment — measure at 1366×768; KPIs + three Team items may bury Deals instead. |
| **B-TL3** | Home **Invite to team** goes to `/admin/users` with no `team_id`. Teams page already has a team-locked invite modal. |
| **B-TL4** | **Keep `/team`.** Overview page + overview API are already Team Lead–scoped. The **live leak** is `fetch_team` in `dashboard_aggregator.py`: when the Team Lead’s team has no *other* members, the agent board widens to every team-eligible user in the tenant. Intervention queue still uses fail-closed `team_scope.py`. Same dashboard, two scopes. |
| **B-TL4b** | `GET /users/` “team of one → whole tenant” fallback. **Not** used by Team Overview. It feeds Teams **Add member**. Closing it without a product rule empties that picker. Rule: a Team Lead grows the team by **invite**. Hide Add-existing for Team Lead (Admin keeps it). Unassigned staff are not this Team Lead’s members until invited onto the team. |
| **B-TL5 / B-TL12** | Playbook, task/vendor templates, **workspace** automation not reachable from Team Command. |
| **B-TL7 / B-TL14** | Communication audit missing from **Team Lead** sidebar (route already allows them). Audit **Log** stays Admin. Do not add the audit item to Admin’s Team group (they already have Oversight). |
| **B-TL8 / B-TL19** | Leftover Coach **language** (empty intervention, Ask AI hint, drift “Coaching needed”). Purchase CTAs already gone. |
| **B-TL9** | Drill-down Email/Call/Text are empty stubs. `AgentBoardRow` has no email/phone. |
| **B-TL10** | “My Task Queue” / Documents-as-Agent-queue on a team desk. |
| **B-TL13** | Coverage (open a file) and invite must both stay **on this desk**. Owner Team Lead also needs tenant Invite people (A3). |
| **B-TL18** | Dead `TeamRailFeeds.tsx` still encodes fake coach prompts. |
| **B-TL20** | Settings Workspace blurb for TL libraries reads as brokerage-wide Admin policy. |

### 2.4 TC product (File Desk)

| ID | Problem |
|---|---|
| **B-TC1 / B-TC7 / B-TC19** | `CoordinatorDashboardPage` = `SoloAgentDashboardPage identity="coordinator"`. Money-first Agent KPIs, Agent Ask AI hint, same payload. SPA `/dashboard/agent` is already Agent-only. |
| **B-TC3 / B-TC13** | Same Deals/Intelligence nav as Agent. Put Workflow then Vendors before Deals. **Keep Contacts.** Do **not** hide Clients until it is proven origination-only (TC still fields client Q&A). |
| **B-TC4** | All Documents still the Agent workflow queue in comments/UI chrome. |
| **B-TC8** | No **Intake documents** action next to + Open file. There is no “intake” filter. Documents already has `?tab=missing` and `ai_priority`. |
| **B-TC9–B-TC11** | Complete-file checklist, vendor defaults, queue-dense notifications — **optional follow-up (P4)**, not a gate for independence. |

**Not a problem:** GET `/task-templates` 200 (inherit). Writes already identity-gated.

### 2.5 Shared leftover

| ID | Problem |
|---|---|
| **S1** | Analytics `ProGateCard` / **AI Coach Pro** lock (purchase still fake). |
| **S2** | Intelligence below the 768 fold. Accept scroll for Intelligence. Do not pin it. |
| **S3** | `require_identity_roles` 403: “Switch your role…” Prefer **invite**; switching is owner-only and must not be the first instruction for invitees. |

---

## 3. Target (what “fully resolved” looks like)

Viewport bar: **1366×768**. New password account per role. No Admin promotion to pass.

### 3.1 Owner chrome (every founder, including Admin)

**Avatar** (owners only, above Settings): **Billing**, **Change my role**, then Settings / Help / Log Out.  
**Home chip** (owners, billing on, not exempt): `Prepaid deals: N · Buy` → billing section.  
**Home invite:**

- **Every owner** (Agent, TC, Team Lead, Admin): **Invite people** → Users & Invites (tenant hire: Admin, Agent, TC, etc.). Not labeled Invite to team.
- **Team Lead (identity):** **Invite to team** opens the **team-locked** invite modal (stay on Team Command or Teams). An owner Team Lead gets **both** buttons.

**Settings hub:** Personal stays first. Owner group stays below Personal (catalog). Invitees: no Owner group.

### 3.2 Landings and brands

| Role | Landing | Brand | Notes |
|---|---|---|---|
| Agent | always `/dashboard/agent` | always **Transaction OS** | `team_id` does not change home. `fetch_agent` stays personal. |
| TC | always `/dashboard/coordinator` | always **File Desk** | landing already correct; fix brand only |
| Team Lead | `/dashboard/team` | **Team Command** | only this identity + Admin *visit* |
| Admin | `/dashboard/admin` | **Admin Console** | may open `/dashboard/team` from Team nav; must not land there at signup |

`TeamDashboardGuard`: Agent and TC **always** bounce off `/dashboard/team` (with or without `team_id`).  
`GET /dashboard/team*`: `TeamLead` + `Admin` only.  
`GET /dashboard/agent`: stays Agent **and** TC until a coordinator endpoint exists.

Update `DashboardRouter` comments and `dashboardShellConfig.test.ts` to match.

### 3.3 File Desk (TC)

Own page component (not a one-line wrapper). May reuse `ActionQueueList`, document queue, glance tiles. Compose from `useAgentDashboard` + `useDocumentsPriorityQueue`. **Keep** `GET /dashboard/agent` for TC. Add `GET /dashboard/coordinator` only if the frontend must hide half the Agent schema.

**KPI strip (lead with the file, not GCI):** Active files · Docs needed · Overdue tasks · Closings this week. Pipeline $ / GCI if shown at all, last and muted.

**Hero:** What to chase (docs / tasks / vendors).  
**CTAs:** + Open file (existing wizard, including “whose file”) **and** Intake documents → `/documents?tab=missing` (or `ai_priority`). Do not invent a new filter or wizard.  
**Ask AI:** coordinator hint (intake, missing docs, vendors, dates).  
**Nav:** Workflow then Vendors before Deals. Keep Contacts **and** Clients unless a later pass proves Clients is origination-only.

**Settings (TC Personal):** Connections, My automation, fees, playbook. File defaults (P4) are optional after File Desk no longer looks like Solo Agent.

### 3.4 Team Command (Team Lead)

**Keep the Team Overview page.** It stays at `/team`, stays in the Team sidebar, and is not redirected to Teams.

| Surface | Job |
|---|---|
| **Team Lead Dashboard** (`/dashboard/team`) | Day-to-day desk: intervention queue + member activity glance (include TC, not “agents only”). Board scope **must match** `team_scope.py` (no implicit whole-tenant team). **See all** → `/team`. |
| **Team Overview** (`/team`) | First-class page. Keep `TeamOverviewRouter`. **Team Lead:** only members of their team (already). **Admin:** brokerage-wide `TeamPage`. Add a two-team regression test so this cannot regress. |
| **Teams** (`/admin/teams`) | Membership. Team Lead sees only their team. **Grow by invite.** Hide Add-existing for Team Lead. Admin keeps Add-existing. |

**Scope rules (required):**

1. `TeamOverviewRouter` stays. Never mount `TeamPage` for `role === TeamLead`.
2. `GET /admin/brokerage/overview` keeps server-side TL scoping. **Pytest:** two teams; Team Lead A’s overview contains only team A.
3. **Remove** `fetch_team` implicit-team fallback (`dashboard_aggregator.py` ~320–327 and the “no team_id” TL branch that uses all team-eligible users). Agent board members = `team_member_ids` (fail closed).
4. `GET /users/` for Team Lead: **no** “team of one → whole tenant” fallback. Pair with hiding Add-existing on Teams for Team Lead so the picker is not an empty trap.
5. Invitations on TL Overview: UI already filters `team_id`. Prefer server filter when cheap; client filter may stay as defense in depth.
6. Empty Overview: Team Lead **owner** with no `team_id` is a mint bug — do not tell them to “ask an Admin.” Invitees without a team can be told to ask their Admin.

**Dashboard glance (does not replace `/team`).** Relabel Agent board as team member activity (Agents **and** TCs). Drill-down Email/Call when contact fields exist. Empty: team-locked invite.

**Sidebar:** Try `team` before `deals` so Team Overview / Teams paint earlier. Communication audit item: **TeamLead only** (Admin keeps Oversight). **Measure at 1366×768** before treating reorder as done. If Deals disappears, do not ship the reorder.

- Invite to team: modal locked to `user.team_id`.  
- Owner Team Lead: also **Invite people**.  
- Rail **Team setup** links: Team Playbook, Task Templates, Vendor Templates, My automation (workspace default).  
- Relabel Workflow task item **Team task queue**.  
- Copy: no “coach an agent” / “pricing-coach” / “Coaching needed.” Drift → **Needs a check-in** or similar.  
- Delete `TeamRailFeeds.tsx`.  
- Workspace Settings description for TL libraries: **this team**, not “everyone in your brokerage.”

### 3.5 Agent (unteamed and teamed)

Unteamed: Transaction OS, representation, money-first KPIs, + New Transaction — keep.  
Teamed: **same Agent home**, personal `fetch_agent` scope, **not** Team Command. Owner chrome from §3.1. No Team Lead libraries. No Invite to team (owner → Invite people).

---

## 4. Implementation phases

Frontend-first unless a phase names backend. Reuse running Vite / API. Do not restart stacks. Do not auto-promote.

### P0 — Owner independence + honest automation copy

**Closes:** A1–A5, S3.

| Change | Where |
|---|---|
| Avatar: Billing, Change my role for `is_tenant_owner` | `AppLayout.tsx` |
| Home prepaid chip (owners, billing on, not exempt) | Agent home, File Desk, Team Command, Admin Console — shared `OwnerPrepaidChip` |
| Home **Invite people** for **every** owner, including Team Lead | those four homes |
| Settings hub: **do not** move Owner above Personal | — |
| Identity-aware automation strings (workspace default, not team posture; never “become Admin” as the recovery) | `SettingsMyAutomationPage.tsx`, `AutomationPostureSection.tsx`, `identity_scope.py`, `auth.py` `require_identity_roles` |
| Tests | avatar/owner chrome; hire-guard copy by role (owner vs invitee; TL vs Agent/TC) |

**Copy rules:**

- Team Lead (can write): you set the **workspace default** for new files. Admin AI Governance is floors / kill switches. Never “switch to Admin.” Never “team posture.”
- Agent/TC owner, sole staff: solo alias (already).
- Agent/TC owner, after hire: cannot write workspace default; **invite an Admin or Team Lead**; per-file override remains; Change my role exists but is **not** the recommended recovery.
- Invitee, after hire: same without mentioning Change my role.

**DoD:** At 1366×768, each founder opens Billing and Change my role from the **avatar** without scrolling Settings. Every founder can Invite people from the home. No string tells them to become Admin to keep the company running. No string claims per-team automation.

### P1 — Stop identity theft

**Closes:** B-TL1, B-TL16, B-TC2, B-TC18, team API leak.

| Change | Where |
|---|---|
| Agent landing + brand ignore `team_id` | `dashboardShellConfig.ts` |
| TC brand always File Desk | `getBrandDescriptor` |
| Guard: Agent/TC never render Team Command | `TeamDashboardGuard.tsx`; `App.tsx` `/dashboard/team` → `TeamLead` + `Admin` only |
| Comments | `DashboardRouter.tsx` |
| Tests | `dashboardShellConfig.test.ts` (teamed TC brand File Desk; teamed Agent → `/dashboard/agent`) |
| `GET /dashboard/team*` | `dashboard_role.py` — `require_exact_roles(TEAM_LEAD, ADMIN)` only |
| Tests | invited Agent 403 on `/dashboard/team`, 200 on `/dashboard/agent` |

**DoD:** Invited Agent with `team_id` lands on `/dashboard/agent`, brand Transaction OS. Invited TC with `team_id` lands on `/dashboard/coordinator`, brand File Desk. Pasting `/dashboard/team` bounces them.

### P2 — File Desk is a coordinator product

**Closes:** B-TC1, B-TC3 (nav order), B-TC7, B-TC8, B-TC13, B-TC19.

| Change | Where |
|---|---|
| Real `CoordinatorDashboardPage` | Stop mounting Solo Agent. Reuse queue/docs widgets. |
| KPI + Ask AI + empty copy | Compose from existing agent + documents-queue APIs. **Keep** `GET /dashboard/agent` for TC. |
| Intake documents | File Desk control → `/documents?tab=missing` |
| TC sidebar: Workflow, Vendors before Deals | `dashboardShellConfig.ts`, `AppLayout.tsx` |
| Clients nav | **Keep** unless a later pass proves otherwise |

**DoD:** Screenshot of File Desk is distinguishable from Solo Agent without the avatar badge. No Pending GCI as the first KPI. Intake is one click (`?tab=missing`). TC can still load `GET /dashboard/agent`.

### P3 — Team Command is a Team Lead product

**Closes:** B-TL2–B-TL5, B-TL7–B-TL10, B-TL12–B-TL14, B-TL18, B-TL20.

| Change | Where |
|---|---|
| Remove `fetch_team` implicit-team fallback; board = `team_member_ids` | `dashboard_aggregator.py` + tests |
| Keep `/team`; keep `TeamOverviewRouter` | **do not delete** |
| Two-team pytest on overview API **and** team dashboard board | `admin_brokerage.py`, `dashboard_aggregator.py` |
| `GET /users/` no whole-tenant fallback for TL; hide Add-existing for TL | `users.py`, `ManageTeamMembersPanel.tsx` / `AdminTeamsPage.tsx` |
| Dashboard member glance (include TC); **See all** → `/team` | `TeamLeaderDashboardPage.tsx`, `AgentBoard.tsx` |
| Invite modal on Team Command (`lockedTeamId`) | `InviteUserModal` |
| Team setup rail + owner Invite people | same page |
| Communication audit in Team nav **for TeamLead only** | `AppLayout.tsx` |
| Communication audit title/copy not “Admin →” | `CommunicationAuditPage.tsx` |
| Coach wording + delete `TeamRailFeeds.tsx` | dashboard + drift labels |
| Task queue label for Team Lead | `AppLayout.tsx` |
| `AgentBoardRow` email, phone, last activity, role | aggregator + drawer |
| Workspace group description when TL not Admin | `SettingsHubPage.tsx` |
| TL-owner empty Overview copy | `TeamLeadOverviewPage.tsx` |
| Sidebar `team` before `deals` | **only if** 1366×768 still shows Deals after measure |

**DoD:** `/team` still in nav. Two-team tenant: Team Lead A never sees team B on Overview **or** Team Command board. Add-existing is not how a Team Lead poaches the tenant. Invite to team never opens unscoped Users. Playbook is one click from Team Command. Team Overview is not removed.

### P4 — TC file defaults (optional)

**Closes:** B-TC9–B-TC11 if still needed after P2.

Not a gate for independence. Ship only if File Desk still feels like Agent after P2.

| Change | Where |
|---|---|
| `profile_settings_json` file-desk keys | PATCH `/me` |
| Settings card **File defaults** (TC only) | `settingsCards.ts` + small page |
| Wizard applies vendor defaults | follow-up if cheap |

### P5 — Shared honesty + leftover Coach

**Closes:** B-TC4, B-TL10 (Documents copy), S1.

| Change | Where |
|---|---|
| Documents heading/comments not “Agent workflow queue” for TC/TL | `DocumentsPage.tsx` |
| Hide Analytics **AI Coach Pro** / `ProGateCard` | `AnalyticsCharts.tsx` |

Do **not** 403 GET `/task-templates`.

### P6 — Four-role verification

Reuse local API/Vite. New accounts. Viewport **1366×768**. Do not put secrets in the plan or in git.

Accounts: Agent owner, TC owner, Team Lead owner, invited Agent with `team_id`, invited TC with `team_id`. Plus a **two-team** tenant for TL scope.

Checklist: §3 landings/brands; avatar Billing + Change my role **only** for owners; **Invite people** on every owner home (including Team Lead); invited Agent not on Team Command; File Desk ≠ Agent screenshot; File Desk intake → `?tab=missing`; Team Lead Invite modal team-locked; `/team` still in nav; two-team Overview **and** Team Command board show only their members; no “switch to Admin”; no “team posture”; no fake Coach Add / Coach Pro; prepaid chip present for owners; TC `GET /dashboard/agent` still 200.

---

## 5. Suggested coding order

1. **P0** — founders can pay, invite, and change identity from the desk they have.  
2. **P1** — stop putting the wrong person on Team Command.  
3. **P2** — File Desk becomes a coordinator desk.  
4. **P3** — Team Command board matches fail-closed team scope; Overview stays.  
5. **P5** — Documents copy + hide AI Coach Pro.  
6. **P4** — optional File defaults.  
7. **P6** — Chrome QA.

P0 and P1 may ship together. P2 does not wait on P4. P3 does not wait on P2. **P4 is not on the independence critical path.**

---

## 6. What we will not do

- Auto-promote anyone to Admin (signup, 403, Settings, ownership transfer).  
- Pin **My setup** or **Owner** as new sidebar groups.  
- Put Owner **above** Personal on the Settings hub.  
- Give TC Team Lead libraries, Team Command, or Invite to team.  
- Give Team Lead Advertising, Payment Access, AI Governance, Audit Log, or Admin Console.  
- Make Agent, TC, and Team Lead homes identical.  
- Reintroduce seat caps or customer-facing “credits.”  
- Document **Settings → Organization** as navigation.  
- Rely on 1920×1080 or “scroll the sidebar past Workflow” for owner jobs.  
- Clone the platform task-template library at mint.  
- Build a real AI Coach product, or a per-team automation table, in this plan.  
- True per-user automation precedence (deal → user → tenant). Post-hire Agent/TC lose **workspace-default** write; Team Lead/Admin keep that write (same tenant row).  
- **Delete Team Overview** or redirect `/team` to Teams.  
- 403 `GET /task-templates` or 403 TC on `GET /dashboard/agent` in this plan.  
- Hide Clients for TC without a dedicated pass.  
- Treat `GET /users/` fallback as the Overview bug (Overview does not call it).  
- Teach “team posture” in UI copy.

---

## 7. Success

A person who creates an **Agent** account originates from Transaction OS, pays and invites from that desk, and never becomes Admin or a Team Lead to finish setup — including after they join a team.

A person who creates a **Transaction Coordinator** account runs File Desk (intake and chase), pays and hires from that desk, and never wears Team Command or Solo Agent KPIs.

A person who creates a **Team Lead** account runs Team Command with a real team, opens **Team Overview** and sees **only that team’s members**, invites into that team (and, as owner, into the tenant), sets workspace automation and playbook from that desk, and pays from that desk — without Admin Console.

That is a fully independent owner workspace **and** four distinct staff products.
