# Team Management System — Implementation Plan

| | |
| --- | --- |
| **Status** | **Proposed (2026-05-29, rev. 2 — convenience-first).** Not started. Turns the already-built `teams` backend into a team-management feature **a non-technical brokerage admin can run entirely with mouse + simple text fields.** Awaiting decisions in §4 before Phase 1. |
| **Date** | 2026-05-29 |
| **Operators** | **Real-estate brokerage staff, not developers.** Primary operator = a brokerage **Admin/owner**; secondary = a **Team Lead**. They think in plain terms — "office," "team," "the lead," "my agents" — and expect to point-and-click. No URLs to hand-edit, no JSON, no API calls, no SQL, no "go ask an engineer." |
| **Scope** | **Frontend-heavy + small backend.** Wire the existing `teams` model/API into clear screens: create/rename/delete a team, name a lead (one click → also grants the role), add/move members, invite-into-team, and filter rosters by team — all from buttons and dropdowns. Fix the one real backend bug (invite `team_id` dropped on accept), harden team deletion, and — gated, last — optionally scope deal views by team. **No new backend endpoints; no schema redesign.** |
| **Goal** | Any brokerage Admin can, in a couple of minutes of clicking, divide their office into named **Teams**, appoint a working **Team Lead** for each, and place every agent on a team — and *see* it reflected on every people screen. Today the whole backend exists but nothing in the UI reaches it, so every org runs with **zero** teams. |
| **Decisions to confirm** | (D1) TL **deal** views narrow to their team — Phase 5, opt-in/last. (D2) **one team per user** (keep). (D3) **Admin** creates/deletes; **Team Lead** runs their own team. (D4) "Teams" lives in the **Team** sidebar group (discoverable), visible to **TL + Admin** (role-aware). (D5) Deleting a non-empty team **unassigns members first**. (D6) **No** auto-created default team. (D7) Naming a Team Lead also **grants the `TeamLead` role** in the same action. (D8) Lead↔team integrity — **moving/replacing a lead hands off the lead role first**, and assigning a team **switches Agents/TCs to the Team dashboard** (documented behavior, surfaced in-UI). |
| **Authoritative sources** | `requirements.txt` (1.2 roles **32-43**; §3.1 routing **1064**; §10 admin user-list + invite **1112-1113**; §4.7 per-team confidence **675-679**) · `SYSTEM_DESIGN.md` §2.2.2–§2.2.3, confidence **718-736** · `MILESTONE_5_3_IMPLEMENTATION_PLAN.md` §6.F · `ACCOUNT_MODAL_REDESIGN_PLAN.md` §2,§4-C/D · `STYLE_GUIDE.md` (AdminPageHeader, Dialog, chips, toasts) |
| **Visual-consistency anchors** | `pages/users/AdminUsersListPage.tsx` (tabbed list + filter toolbar) · `components/team/TeamMembersTable.tsx` (member cards) · `components/team/InviteUserModal.tsx` (invite dialog) · `components/active-transactions/AssignTeamModal.tsx` (search-and-pick picker) · `pages/admin/AdminTeamConfigPages.tsx` + `components/admin/AdminPageHeader.tsx` |

---

## 0. Current state (verified 2026-05-29)

The `teams` capability is **built on the server and almost entirely unwired on the client.**

| Layer | Component | State | Evidence |
| --- | --- | --- | --- |
| **Data model** | `Tenant` = "a brokerage organization"; `Team{tenant_id,name,lead_user_id,settings_json}`; `users.team_id` nullable FK; one tenant → N teams | ✅ Complete | `app/models/tenant.py:1-2`, `app/models/team.py`, `app/models/user.py:36`, `SYSTEM_DESIGN.md:202-221` |
| **Backend — CRUD** | `POST/GET/GET{id}/PUT/DELETE /api/v1/teams` (Admin writes; Admin+TL read) | ✅ Complete | `app/api/v1/teams.py:30-122` |
| **Backend — membership** | `POST /teams/{id}/members` sets `users.team_id`; `DELETE …/{userId}` nulls it; TL scoped to own team | ✅ Complete | `app/api/v1/teams.py:128-195` |
| **Backend — promote to lead** | `PUT /users/{id}/role {role,team_id}` (Admin-only) sets **role + team in one call**; owner-locked; seat-guarded | ✅ Complete | `app/api/v1/users.py:545-604` (`:597` sets both) |
| **Backend — roster scoping** | `GET /users/?team_id=&role=&is_active=`; TL auto-scoped to own team **with implicit-team fallback** | ✅ Complete | `app/api/v1/users.py:393-432`, `app/repositories/user_repository.py:273-294` |
| **Backend — dashboard roster** | `fetch_team` scopes the agent board by `team_id` (implicit-team fallback so it never blanks) | ✅ Complete | `app/services/dashboard_aggregator.py:282-333` |
| **Backend — team config** | checklist templates / tagged notes / preferred vendors / internal resources keyed on `teams.settings_json` (+`team_id` query for Admin) | ✅ Complete | `app/api/v1/admin_team.py:47-301` |
| **Backend — overview** | `/admin/brokerage/overview` returns per-team `{name, agent_count, active_transactions}` | ✅ Complete | `app/api/v1/admin_brokerage.py:159-171` |
| **Backend — deal scoping by team** | **Deferred by design.** Generic dashboard `view=team` = full tenant; aggregator tx-fetch is full-tenant with an explicit "multi-team isolation… first" TODO | ⚠️ Intentional gap | `app/api/v1/dashboard.py:315-321`, `app/services/dashboard_aggregator.py:359-362` |
| **Backend — invite carries team** | `team_id` on `InviteUserRequest`, persisted on create… | ⚠️ Half-wired | `app/schemas/invitation.py:16`, `app/api/v1/invitations.py:206` |
| **Backend — invite applies team** | …but **acceptance never copies `invitation.team_id` onto the new user** → invited-into-team silently no-ops | 🔴 **Bug** | `app/api/v1/invitations.py:508-526` |
| **Frontend — create/rename/delete team** | None. Nothing calls `POST/PUT/DELETE /api/v1/teams` (no `useTeams`). No seed inserts teams | 🔴 Missing | (grep: zero callers) |
| **Frontend — assign member / name lead** | None. `TeamMembersTable` offers View/Transfer/Deactivate only; no team column, no lead control, **no role-change UI at all** | 🔴 Missing | `components/team/TeamMembersTable.tsx:230-450` |
| **Frontend — invite into team** | Invite modal sends only `email`+`role`; team picker absent | 🔴 Missing | `components/team/InviteUserModal.tsx:82-85` |
| **Frontend — "By team" card** | Renders teams; each row links `/admin/users?team_id=<id>` and shows a bare "No teams yet" with **no way to create one**… | ⚠️ Present but inert | `pages/TeamPage.tsx:496-529` |
| **Frontend — team filter on Users page** | …and `AdminUsersListPage` ignores `team_id`, so the link is dead | 🔴 Missing | `pages/users/AdminUsersListPage.tsx:38-40, 102-106` |
| **Frontend — team config selector** | The four `/admin/team-*` pages send **no** `team_id` → implicit own-team; an Admin with no team gets a raw **400** | ⚠️ Hostile | `pages/admin/AdminTeamConfigPages.tsx:65-81`, `app/api/v1/admin_team.py:69-77` |

**Net effect today:** there is no in-app path to create a team or place anyone on one, so the `teams` table stays empty and every "team" surface effectively means "the whole brokerage."

> ⚠️ **Naming caution:** `components/active-transactions/AssignTeamModal.tsx` is **not** about `Team` membership — it manages per-transaction `transaction_assignments`. Leave it alone despite the name.

> 🔔 **Assigning a team is NOT cosmetic — it changes runtime behavior (verified).** Per `requirements.txt:1064` + `DashboardRouter.tsx` + `TeamDashboardGuard.tsx`, an **Agent/TC with a `team_id` is routed to `/dashboard/team`** instead of the Solo-Agent dashboard (and `getLandingRoute` / brand lockup follow — `dashboardShellConfig.ts:48,173`). Being on a team also makes **team task-templates and the team's closing/checklist templates take precedence** over personal ones (`requirements.txt:32,499,718`; `closing_checklist.py:167-168`, `me_settings.py:71`) and activates **per-team AI-confidence thresholds** (`requirements.txt:675-679`, `SYSTEM_DESIGN.md:718-736`). These paths are dormant today only because nobody has a `team_id`; **this plan turns them on.** Implications: (a) the assign/invite confirmations must say so in plain words ("Bob will now use the **Team** dashboard and your team's templates"); (b) Phase 4 must be QA'd against the dashboard switch — it is **expected, not a bug**.

---

## 1. Why this plan exists

The product promises team structure (Team Lead role, team-wide templates, team oversight — `SYSTEM_DESIGN.md:221`) and the backend delivers it, but **no screen lets an agent-admin form a team.** A latent, well-tested capability that customers can't reach. The cheapest path to value is **UI wiring on stable endpoints** — and because the operator is non-technical, the bar is not "a developer could do it via the API" but "a busy broker can do it by clicking, with plain words and forgiving prompts."

---

## 2. UX charter — the overriding constraint

Every screen in this plan is measured against these. If a workstream can't meet them, it gets redesigned, not shipped.

1. **Clicks only, no plumbing.** Everything — create, name a lead, add/move members, invite-into-team, filter — is a button, dropdown, search-and-click, or short text field. **No** URL editing, IDs, JSON, role codes, or API knowledge is ever required of the operator.
2. **One intent = one action.** "Make Jane the Team Lead" is *one* button that does everything that intent implies (grants the `TeamLead` role, puts her on the team, marks her the lead) — not three separate developer-style steps. We compose the existing endpoints behind that single gesture (D7).
3. **Plain language, broker's vocabulary.** UI copy says *Brokerage, Team, Team Lead, Members, Agents* — never *tenant, role enum, team_id, scope, implicit fallback*. Section labels read like "Editing templates for: **North Office ▾**".
4. **Manage people where you already see them.** Team assignment is available inline on the **Team Members** list, on a person's **profile**, and at **invite** time — so the operator never has to learn a separate "membership console." A dedicated Teams hub exists for setup, but day-to-day assignment meets them where they are.
5. **No dead ends, no raw errors.** Empty states carry the next action ("No teams yet — **+ Create your first team**"). Backend 400/403/409 are translated to plain sentences ("You've used all 5 seats on the Team plan — remove a member or upgrade to add more"). The current Admin-with-no-team **400** on team config is replaced by a friendly team picker.
6. **Forgiving & reversible.** Destructive or surprising actions confirm in plain terms with the consequence spelled out ("Deleting **North Office** will unassign its **3 members** — their accounts stay active"). Moving a member who's already on a team shows their current team and confirms the move.
7. **Immediate feedback.** Every action shows a toast and updates the visible counts/rows at once (optimistic where safe), so the operator always sees that it worked.
8. **Discoverable.** Teams are introduced where the operator already looks (Team Overview's "By team" card becomes an entry point), with a one-line explainer the first time, so nobody needs a manual.

---

## 3. Target information architecture

```
ORGANIZATION (the Brokerage)
  └── Teams (0..N)                       ← NEW: the "Teams" hub
        ├── Name           (plain text)
        ├── Team Lead      (one click → person is promoted + placed + marked lead)
        └── Members        (search-and-add; a person is on ≤ 1 team)

SIDEBAR — TEAM group (where brokers already look)        ADMIN group (governance)
  Team Overview   ← "By team" card becomes an entry        Communication Audit
                    point: "+ New team", click a team       AI Governance
                    to manage it                            Payment Access · Audit Log
  Teams ★ NEW     ← Admin: create/rename/delete, name lead, staff any team.
                    Team Lead: scoped "My Team" — add/remove its members.
  Team Members    ← gains a "Team" column + inline "Move to team ▾"
                    (Admin: any team / TL: own team) + "Make Team Lead" (Admin)
  Task Templates                                           TEAM-CONFIG group (TL + Admin)
  Vendor Templates                                          Team Checklist Templates ─┐
                                                            Team Tagged Notes         │ gain a
INVITE                                                      Team Vendors              │ team
  "Invite teammate" gains an optional "Add to team" picker  Team Internal Resources ──┘ picker
```

**Why the Team group (not Admin):** a broker looking to organize agents thinks "Team," not "Admin governance." Putting **Teams** beside **Team Overview / Team Members** is where they'll look first (D4). **Team Overview and Team Members are already open to Team Leads** (`App.tsx:590-603`, `requiredRole="TeamLead"`), so a TL lands here naturally. The **Teams** hub is **role-aware**: Admins get full create/rename/delete + staffing; a Team Lead gets a scoped *My Team* view (manage its members) and never sees create/delete.

---

## 4. Decisions to confirm (with recommended defaults)

| # | Question | Recommendation | Why |
| --- | --- | --- | --- |
| **D1** | Narrow a Team Lead's **deal** views to their team? | **Phase 5, opt-in, last.** | The code flags this as the risky part ("multi-team isolation… narrowing here just diverges this surface from the Transactions page" — `dashboard_aggregator.py:359-362`). Ship management first. |
| **D2** | One team per user, or many? | **One** (keep `users.team_id`). | Single-valued column; multi-team needs a join table + RLS rework — out of scope, and simpler for the operator. |
| **D3** | Who creates/deletes vs runs a team? | **Admin** creates/renames/deletes & staffs any team. **Team Lead** runs **their own** team: **invites people into it**, adds/removes its members, edits its playbook — but cannot create/rename/delete teams or grant roles. | Matches existing authz: invite is Agent/TL/Admin (`invitations.py:116`); member add/remove is TL-own-team (`teams.py:143-146,178-181`); create/rename/delete are Admin-only (`teams.py:33,88,113`); role grant is Admin-only (`users.py:549`). No authz change. |
| **D4** | Where does "Teams" live? | **Team** sidebar group, visible to **Team Lead + Admin** (role-aware: Admin = full CRUD; TL = scoped *My Team* members view). Create/rename/delete shown only to Admin. | Discoverability for a non-technical broker (UX charter #4/#8); Team Overview & Team Members are **already** TL-accessible (`App.tsx:590-603`, `requiredRole="TeamLead"`). |
| **D5** | Deleting a team with members (and other team-linked rows)? | **Clear all references first** (members, pending invites, team task-templates, per-team confidence), then delete; never cascade-delete users. | **Four** FKs reference `teams(id)` with **no `ON DELETE`** (`20260319_schema_corrections.sql:160,233,339,364`), so a raw delete — or one clearing only members — errors. See A2. |
| **D6** | Auto-create a default "Main Team"? | **No.** Opt-in. | The implicit-team fallback already prevents blank dashboards (`users.py:413-430`); auto-teams clutter solo/small offices. |
| **D7** | Does naming a Team Lead also grant the `TeamLead` **role**? | **Yes — same action**, and it must run **even when the lead is chosen at team-creation** (the bare `lead_user_id` pointer is not enough — see §7). | A "lead" with no powers is a bug to the operator (UX charter #2). `PUT /users/{id}/role {role:'TeamLead',team_id}` does role+team in one call (`users.py:597`); we add the lead pointer with `PUT /teams/{id}`. `POST /teams {lead_user_id}` writes the pointer only (`team_repository.create`). Existing endpoints only. |
| **D8** | A lead moved / replaced / their team deleted? | A TL's `users.team_id` **must equal the team they lead**. So: **block "Move to team" on a current lead** (hand off the lead role first); replacing a lead leaves the prior lead a TeamLead member (no silent demotion); deleting a team leaves the former lead with role=TeamLead + no team (→ implicit-team fallback) and the confirm copy says so. | The backend scopes a TL by `user.team_id` (`admin_team.py:59-67`, `teams.py:143-146`), **not** by `lead_user_id`; if they diverge the lead silently manages the wrong roster. |

---

## 5. Workstream A — Backend corrections (small, ship first; no new endpoints)

- **A1 — Apply invite `team_id` on accept (bug fix).** In `accept_invitation`, after the profile is created (`app/api/v1/invitations.py:512-526`), persist the team when `invitation.team_id` is set and the team still exists & is same-tenant. **`UserRepository.create()` takes no `team_id` arg** (`user_repository.py:91-101`), so don't pass it there — follow the create with `await user_repo.update(profile, team_id=invitation.team_id)` (the generic `update` passes `team_id` through and skips `None`, `:122-143` — the exact pattern `add_member` uses, `teams.py:155`). Add a regression test in the `app/tests/` invite suites.
- **A2 — Safe team delete (D5) — must clear ALL FOUR FK references.** `teams(id)` is referenced with **no `ON DELETE`** by **four** tables (named constraints in `20260319_schema_corrections.sql`: `fk_users_team:160`, `fk_task_templates_team:233`, `fk_invitations_team:339`, `fk_confidence_team:364`), so a delete that clears only members **still errors** on the other three. In `delete_team` (`teams.py:111-122`), before `repo.delete`, in one server-side pass: `users.team_id`→NULL (keep accounts/roles), `invitation_tokens.team_id`→NULL (pending invites lose the target team), `task_templates.team_id`→NULL (team templates revert to tenant-level — non-destructive), and **delete** `confidence_settings` rows for the team (removes the per-team override; avoids a duplicate tenant-level row under `UNIQUE(tenant_id, team_id)`). Audit-log the unassigned-member count. *(Alt: an `ON DELETE SET NULL`/`CASCADE` migration on all four; the in-app sweep needs no migration and lets us show the count.)*
- **A3 — Member-add role guard (hardening).** `add_member` currently accepts any user; restrict to team-eligible roles (Agent / TC / TeamLead) mirroring `_team_eligible_roles` (`dashboard_aggregator.py:310-314`) so a Client/Vendor can't be shelved onto a team. Return a clear 422 the UI maps to plain copy.
- **A4 — (Optional) Team list enrichment.** Add `member_count` + resolved `lead_name` to `GET /api/v1/teams` items so the hub renders in one call. Cheap aggregate over `list_by_tenant(team_id=…)`. If skipped, the FE composes from `/admin/brokerage/overview`.

**No schema migration** for A1/A3/A4; A2 is code-only unless D5 picks the `ON DELETE` route. **The "Make Team Lead" action needs no backend change** — it composes `PUT /users/{id}/role` + `PUT /teams/{id}`.

---

## 6. Workstream B — Frontend data layer

- **B1 — `hooks/useTeams.ts`** (TanStack Query, mirroring `useInvitations`/`useAssignments`):
  ```ts
  useTeams()                 // GET /api/v1/teams               → Team[] (+member_count, lead_name if A4)
  useCreateTeam()            // POST /api/v1/teams              { name, lead_user_id? }
  useUpdateTeam()            // PUT  /api/v1/teams/{id}         { name?, lead_user_id? }
  useDeleteTeam()            // DELETE /api/v1/teams/{id}
  useAddTeamMember()         // POST /api/v1/teams/{id}/members { user_id }
  useRemoveTeamMember()      // DELETE /api/v1/teams/{id}/members/{userId}
  useMakeTeamLead()          // composite (D7) — ORDER MATTERS: 1) PUT /users/{id}/role
                             //   {role:'TeamLead',team_id} (promote + place), THEN
                             //   2) PUT /teams/{id} {lead_user_id} (mark lead). Failure
                             //   after step 1 = a working TeamLead member (recoverable):
                             //   toast "Promoted; couldn't mark as lead — Retry". Never
                             //   pointer-first (failure would recreate "lead in name only").
  ```
  `Team` exists (`types/api.ts:208-216`); `InviteUserRequest.team_id?` exists (`:97`); `UserRoleUpdateRequest.team_id?` exists (`:89`) and the endpoint applies role+team together (`users.py:597`). Invalidate `QUERY_KEYS.USERS` + a new `TEAMS` key on every mutation so rosters/overview/counts refresh at once (UX charter #7). *(`GET /teams` caps `page_size` at 100 — `teams.py:50`; request 100 and paginate beyond that. The brokerage overview lists up to 200 teams — `admin_brokerage.py:91` — reconcile the two if a tenant ever exceeds 100 teams.)*
- **B2 — Friendly-error helper.** A small `teamErrorMessage(err)` mapping the known backend statuses to plain sentences (seat limit 409 → "You've used all N seats…"; owner-lock 403 → "Transfer ownership first to change the owner's role"; 422 role guard → "Only agents, coordinators, and leads can be added to a team"). Used by every mutation's `onError` (UX charter #5).
- **B3 — `ROUTES` + nav.** Add `ADMIN_TEAMS = '/admin/teams'` (`utils/constants.ts` near `:154`). Register it with `requiredRole="TeamLead"` in `App.tsx` (minimum-role guard → TL + Admin both reach it; the page renders Admin-only controls conditionally). Add a **Teams** item to the **`team`** sidebar group (`AppLayout.tsx` / `dashboardShellConfig.ts:93,114` — the `team` group already renders for TL **and** Admin); show it to **both** — Admins get the full hub, a Team Lead gets the scoped *My Team* view (§7).

---

## 7. Workstream C — The "Teams" hub (`pages/admin/AdminTeamsPage.tsx`)

Role-aware, `AdminPageHeader` pattern. **Admin** sees all teams with full create/rename/delete + staffing. A **Team Lead** sees a scoped **"My Team"** view — manage its members and view its lead — with no create/rename/delete and no role-granting (D3). A broker should set up a whole team without leaving this page.

- **Team list:** cards/rows → **Name**, **Lead** (name chip, or "No lead yet"), **Members** (count), **Active deals** (from overview), and clear row buttons. First-run empty state is a single friendly CTA: *"No teams yet — organize your agents into teams. **+ Create your first team**."* (UX charter #5/#8).
- **Create team — one sitting (2-step dialog, never leaves the modal):**
  1. *Name* (text) + optional *Team Lead* (searchable dropdown of staff). Create → `useCreateTeam`; **if a lead was chosen, immediately run `useMakeTeamLead`** — `POST /teams {lead_user_id}` writes only the pointer (`team_repository.create`), which would leave a "lead in name only" who isn't promoted and isn't on the team. Naming a lead — here or later — *always* runs the full promotion (role + `team_id` + pointer), never the bare pointer (D7).
  2. The same modal then shows *Add members* — a searchable list of agents not yet on a team; click to add (`useAddTeamMember`). "Done" closes. (UX charter #2 — set up in one flow, not three screens.)
- **Make / change Team Lead — one click (D7):** a **"Make Team Lead"** action on a member, or the Lead dropdown in the dialog. Confirmation in plain words: *"Promote **Jane Doe** to Team Lead and set her as lead of **North Office**? She'll be able to manage this team's members and templates."* → `useMakeTeamLead`. **Smart cases:** if the chosen person is already an Admin/owner, skip the role change (they already have full powers) and only set the lead pointer, saying so; if the chosen person **already leads another team**, require handing that off first (D8) so they aren't scoped to one team while still pointed as another's lead; if seat/owner guards trip, show B2's plain message — never a raw error. **Not atomic — order matters:** promote **first** (`PUT /users/{id}/role` → role + `team_id`), then set the **lead pointer** (`PUT /teams/{id}`); if the pointer call fails, the person is already a functioning Team Lead on the team (recoverable) and the UI offers **Retry** — never pointer-first, which on failure recreates the "lead in name only" state.
- **Rename / Delete:** rename via the same dialog. Delete uses `useConfirm`: *"Delete **North Office**? Its **3 members** will be unassigned (their accounts stay active)."* → `useDeleteTeam` (backed by A2).
- **Manage members anytime:** "Manage members" opens the search-and-pick panel (modeled on `AssignTeamModal`): left = current members with a remove ✕; bottom = searchable candidates. Add/remove map to the member mutations. Moving someone already on another team shows *"Currently on Westside — move to North Office?"* (UX charter #6).

---

## 8. Workstream D — Put team management where brokers already are

- **D-1 — Team Members page gains team awareness** (`AdminUsersListPage.tsx` + `TeamMembersTable.tsx`):
  - Read `team_id` from `useSearchParams()`; forward it to the `/users/` fetch (already supported — `users.py:396`). Show a dismissible **"Team: North Office ✕"** chip; clearing returns to all members. *This makes the "By team" links live.* *(A **Team** column and **filter by team** on this list are explicit requirements — `requirements.txt:1112`.)*
  - Add a **Team** column to each member card (name via `useTeams`). **Admins** get an inline **"Move to team ▾"** (add/remove mutations) and **"Make Team Lead"** (D7). A **Team Lead** gets **"Add to / remove from my team"** for their own team's members — the backend already scopes this to the TL's team (`teams.py:143-146,178-181`) — but **not** "Make Team Lead" (granting a role is Admin-only, `users.py:549`). Assignment thus happens where the operator already manages people (UX charter #4). **When a move puts an Agent/TC onto or off a team, the confirm/toast states that their dashboard will switch** (Team ⇄ Solo-Agent — see §0 callout). A current **lead** is not movable here (D8) — the row offers "Hand off lead role" instead.
  - **(Convenience)** Optional row multi-select → **"Assign selected to team ▾"** (Admin: any team; TL: their own) for staffing in one sweep.
- **D-2 — Invite into a team** (`InviteUserModal.tsx`): add an optional **"Add to team"** picker (shown for Agent/TC/TeamLead invites; hidden for Client/FSBO/Vendor). Include `team_id` in the payload (`onSubmit`, `:82-85`); with A1 the invitee lands on the team automatically when they accept — zero follow-up clicks. *(The invite **Team** field is an explicit requirement — `requirements.txt:1113`.)*
  - **Team Leads can already invite** (`invitations.py:116` allows Agent/TL/Admin; the button is on the TL-accessible Team Members page), so for a **TL inviter** the control reads **"Adding to: «My Team»"** — pre-set and locked to their own `team_id`. That is literally *"invite my own team member."* If the TL has no team yet, fall back to a team-less invite (an Admin assigns later).
  - *Authz note:* `create_invitation` does **not** currently scope `team_id`, so the frontend sets the TL's own team. Optional backend hardening: reject an invite whose `team_id` isn't the TL's own team.
- **D-3 — Team config gets a friendly team picker** (`AdminTeamConfigPages.tsx`): a labeled **"Editing for: «Team» ▾"** at the top of all four pages. Admin → choose any team (passes `?team_id=` to the already-accepting endpoints, `admin_team.py:115`); Team Lead → locked to their own team (shown, not editable). **Removes the raw 400** an Admin-with-no-team hits today (UX charter #5). *(Edge: a Team Lead not yet on a team still gets a 403 from `_resolve_team` — `admin_team.py:60-61`; show a friendly "You're not on a team yet — ask an admin to add you" empty state, not an error.)*
- **D-4 — "By team" card becomes the on-ramp** (`TeamPage.tsx:496-529`): add a **"+ New team"** button in the card header and make each row click through to manage that team; add the **Lead** name to each row; keep the now-live `/admin/users?team_id=` link. The empty state becomes *"Create your first team"* instead of an inert "No teams yet."

---

## 9. Workstream E — Deal-level team isolation (gated on D1, ship last)

Only if D1 = "narrow TL deal views." Addresses the one intentional backend gap.

- **E-1 — Shared resolver.** Extract the implicit-team logic (`dashboard_aggregator.py:307-333`) into `resolve_team_member_ids(user) -> list[str]` in `dashboard_common.py`.
- **E-2 — Scope tx fetches.** In `dashboard.py::_user_filter` / `_fetch_transactions_by_statuses` (`:200-253, 315-321`), when `view=team` and the actor is a **TL with a populated team**, filter to deals created-by/assigned-to a member instead of the current full-tenant `None`. Admins keep full tenant (or a chosen team). Apply the same resolver to the aggregator tx-fetch (`:362`), retiring its TODO.
- **E-3 — Transactions page `view=team`** (`dashboard.py:2255-2392`): same scope so dashboard and Transactions agree.
- **E-4 — Tests:** team-scoped vs implicit-fallback vs admin-full-tenant; cross-team isolation; empty-team never blanks the board.

> This is the only phase that changes user-visible **data scope**; keep it isolated and behind D1.

---

## 10. Files — new / changed

| Action | File | Note |
| --- | --- | --- |
| **New** | `velvet-elves-frontend/src/hooks/useTeams.ts` | queries + mutations incl. `useMakeTeamLead` (B1) |
| **New** | `velvet-elves-frontend/src/utils/teamErrors.ts` | plain-language error mapping (B2) |
| **New** | `velvet-elves-frontend/src/pages/admin/AdminTeamsPage.tsx` | the Teams hub (C) |
| **New** | `velvet-elves-frontend/src/components/team/TeamSetupDialog.tsx` | 2-step create (name+lead → add members) (C) |
| **New** | `velvet-elves-frontend/src/components/team/ManageTeamMembersPanel.tsx` | search-and-pick members (C) |
| **Changed** | `velvet-elves-frontend/src/utils/constants.ts` | `ADMIN_TEAMS` + `QUERY_KEYS.TEAMS` (B3) |
| **Changed** | `velvet-elves-frontend/src/App.tsx` | register `/admin/teams` (`requiredRole="TeamLead"`; page gates Admin-only controls) |
| **Changed** | `velvet-elves-frontend/src/layouts/AppLayout.tsx` + `dashboardShellConfig.ts` | **Teams** entry in the **team** group, visible to TL + Admin (role-aware page) |
| **Changed** | `velvet-elves-frontend/src/pages/users/AdminUsersListPage.tsx` | team filter chip; multi-select assign (D-1) |
| **Changed** | `velvet-elves-frontend/src/components/team/TeamMembersTable.tsx` | Team column + "Move to team" + "Make Team Lead" (D-1) |
| **Changed** | `velvet-elves-frontend/src/components/team/InviteUserModal.tsx` | optional "Add to team" picker (D-2) |
| **Changed** | `velvet-elves-frontend/src/pages/admin/AdminTeamConfigPages.tsx` | "Editing for: «Team» ▾" picker; no more 400 (D-3) |
| **Changed** | `velvet-elves-frontend/src/pages/TeamPage.tsx` | "+ New team", clickable rows, lead name (D-4) |
| **Changed** | `velvet-elves-backend/app/api/v1/invitations.py` | apply `team_id` on accept (A1) |
| **Changed** | `velvet-elves-backend/app/api/v1/teams.py` | safe delete (A2) + member role guard (A3); optional enrichment (A4) |
| **Changed (E only)** | `velvet-elves-backend/app/services/dashboard_common.py` · `dashboard_aggregator.py` · `app/api/v1/dashboard.py` | resolver + tx team-scoping (E1-E3) |

No frontend type additions needed (`Team`, `InviteUserRequest.team_id`, `UserRoleUpdateRequest.team_id` already present). **No new backend endpoints.** No schema migration unless D5 picks `ON DELETE SET NULL`.

---

## 11. Phasing

1. **Phase 1 — Backend corrections (A1–A3).** Independent, low-risk; makes invite-into-team and safe-delete correct. Tests.
2. **Phase 2 — Data layer (B).** `useTeams` (incl. `useMakeTeamLead`), error helper, route + nav entry.
3. **Phase 3 — Teams hub (C).** Create a team, name a working lead (one click), staff it — **first and biggest user-visible value.**
4. **Phase 4 — Meet brokers where they are (D).** Team column + inline assign/"Make Team Lead", invite picker, config team picker, "By team" on-ramp. Management now feels complete and is discoverable.
5. **Phase 5 — Deal isolation (E), gated on D1.** Optional; only after teams have members.

Phases 1–4 deliver a fully usable, click-only team-management feature; Phase 5 is an enhancement.

---

## 12. Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| Operator names a "lead" who then can't actually lead (role not granted) | D7: **"Make Team Lead" grants the role + places them + sets the pointer in one action** (`users.py:597` + `PUT /teams/{id}`); plain confirmation states what they'll be able to do |
| Promoting a portal user to lead trips the seat limit | Caught by the endpoint's seat guard (`users.py:581-593`); B2 surfaces "You've used all N seats…", not a raw 409 |
| Trying to make the owner a different role | Endpoint blocks it (`users.py:566-573`); the hub detects owner/Admin and just sets the lead pointer (no role downgrade), explaining why |
| Moving a member silently overwrites their prior team (single `team_id`) | "Move to team" shows current team and confirms the move (UX charter #6) |
| Moving/replacing a **Team Lead** breaks the lead↔team invariant — a TL is scoped by `user.team_id`, not `lead_user_id` | D8: block "Move to team" on a current lead (offer "Hand off lead role" first); replacing leaves the prior lead intact; delete leaves them team-less with a clear note (`admin_team.py:59-67`, `teams.py:143-146`) |
| **Create-with-lead** sets only the pointer → "lead in name only" | §7/D7: choosing a lead always runs `useMakeTeamLead` (role + team_id + pointer), never the bare `POST /teams {lead_user_id}` |
| Operator surprised that adding an Agent to a team **changes their whole dashboard** | Documented/expected (`requirements.txt:1064`, `DashboardRouter`/`TeamDashboardGuard`); assign & invite confirmations state it plainly (§0 callout); QA Phase 4 against the switch |
| Deleting a team errors or strands references — **4 FKs** (users, task_templates, invitation_tokens, confidence_settings) | A2 clears **all four** server-side in one pass before delete (`20260319_schema_corrections.sql:160,233,339,364`); confirm dialog states the member count |
| The **"Make Team Lead" composite** (2 calls) partially fails | Order = **promote first, mark-lead second**; a mid-failure leaves a working TeamLead member (recoverable), surfaced with **Retry**; never pointer-first |
| Admin-with-no-team hits a blank 400 on team config | D-3 replaces it with a friendly team picker |
| Jargon leaks into the UI (tenant, team_id, role enums) | UX charter #3 is a review gate; copy uses Brokerage/Team/Lead/Members only |
| TL auto-scoping in `/users/` "hides" newly-invited unassigned users | Already handled by the endpoint fallback (`users.py:413-430`); document so it isn't "fixed" by accident |
| A Team Lead could invite into **another** team — `create_invitation` doesn't scope `team_id` (`invitations.py:113-147`) | Frontend pre-sets & locks the TL's invite `team_id` to their own team (D-2); optional backend guard rejects a non-own `team_id` from a TL |
| Cross-tenant leakage when picking leads/members | Endpoints enforce `require_tenant_access` + same-tenant checks (`teams.py:140,152-153`, `users.py:563`) + RLS; reuse, don't bypass |

---

## 13. Acceptance criteria (click-paths a broker can run, no dev help)

- Admin → **Team → Teams** → **Create your first team** → type "North Office", pick lead "Jane" → confirm *"Promote Jane to Team Lead and set as lead of North Office?"* → in the same dialog, search and add two agents → **Done**. Row shows *North Office · Lead: Jane · 3 members*, and Jane can now open the Team Lead surfaces.
- Admin → **Team Members** → on an agent's row, **Move to team ▾ → North Office** → toast + the Team column updates. Select three rows → **Assign selected to team → Westside** → all move at once.
- Admin → **Team Overview → By team** → **+ New team** works; clicking "North Office" opens its management; clicking the count opens **Team Members** filtered with a "Team: North Office ✕" chip.
- Admin → **Invite teammate** → role Agent + **Add to team: North Office** → invite; accept in a second session → the new agent appears under North Office automatically.
- Admin (with no personal team) → **Team Checklist Templates** → sees **"Editing for: ▾"** and picks a team — **no error page**. Team Lead → the picker is locked to their team.
- Admin → **Teams → Delete "North Office"** → *"Its 3 members will be unassigned (accounts stay active)"* → after delete those agents show no team and still log in.
- Try to make the **owner** a team's lead → the lead pointer is set, the owner keeps Admin, and a note explains no role change was needed — **never a raw error**.
- **Team Lead** → opens **Team Overview** and **Team Members** normally (no Admin needed) → **Invite teammate** → the dialog shows **"Adding to: «My Team»"** → the invitee accepts → they appear on the Team Lead's team automatically.
- **Team Lead** → **Teams** (or Team Members) → sees only **My Team**; can **add/remove members**; has **no** Create/Rename/Delete and **no** "Make Team Lead" (those are Admin).
- Admin assigns a **solo Agent** to a team → the confirm warns "they'll switch to the **Team** dashboard"; after the Agent's next load they land on `/dashboard/team`; removing them from the team returns them to the Solo-Agent dashboard (expected per `requirements.txt:1064`).
- Admin → **Move to team** on a person who is a team's **Lead** → blocked with *"Hand off the Team Lead role first"* — no silently broken scoping (D8).
- Admin creates a team and picks a lead in the dialog → that person is actually **promoted to Team Lead and placed on the team** (not a pointer-only "lead in name only").
- **(Phase 5, if D1=yes)** TL "team view" shows only their team's deals; an Admin still sees the whole brokerage; a TL of an empty team still sees a populated (implicit) board.

---

## 14. Non-goals

- No new backend endpoints; no schema redesign; no multi-team-per-user (D2).
- No general-purpose role editor — role change is exposed **only** through the bounded "Make Team Lead" action (D7); broader role management stays out of scope.
- No change to `transaction_assignments` or the (misnamed) per-deal `AssignTeamModal`.
- No auto-created default team (D6); no change to seat counting, billing, or invite **email** templates (only the invite *payload* gains `team_id`).
- No Team-Lead ability to create/delete teams (Admin governance only, D3).
- Phase 5 deal-isolation is **optional**, excluded unless D1 selects it.

---

## 15. Documentation sync (part of the work)

- `SYSTEM_DESIGN.md` §2.2.3 / API: mark `/api/v1/teams` as **wired to UI**.
- `FRONTEND_UI_WORKFLOW_LOGIC.md`: add the **Teams** hub (Team group), the Team Members **team column + Move/Make-Lead** actions, and invite-into-team.
- `ACCOUNT_MODAL_REDESIGN_PLAN.md` §2 IA: add **Teams** to the Team group box.
- If Phase 5 ships: record the deal-scoping change and retire the `dashboard_aggregator.py:359-362` TODO.
