# Team Management System - Overhaul Plan

| | |
| --- | --- |
| **Status** | **Proposed (2026-06-24).** Plan only, no source changes. A convenience-first overhaul of the three team-management surfaces (`/team`, `/admin/teams`, `/admin/users`) so a non-technical brokerage admin can run their whole team from clear, consistent screens. |
| **Date** | 2026-06-24 |
| **Operators** | Real-estate brokerage staff, not developers. Primary = brokerage **Admin/owner**; secondary = **Team Lead**. They think in plain words ("office", "team", "the lead", "my agents") and expect to point-and-click. No URLs to hand-edit, no role codes, no JSON. |
| **Scope** | **Frontend-heavy, one small backend filter.** Clean up Team Overview, turn `/admin/teams` into a true in-place team workspace (see members without leaving the page, invite into a team), and make "who can be on a team" consistent everywhere. No schema changes, no new tables. The invite-carries-team accept bug is already fixed (`invitations.py:714-739`), so invite-into-team works end to end once the UI is wired. |
| **Goal** | Each of the three surfaces does one job, with no dead-end redirects and no off-team people shown where only team members belong: **Team Overview** = scan team health; **Teams** = build and run teams (members visible inline, invite in place); **Users & Invites** = the full directory of every person in the workspace. |
| **Authoritative sources read** | `velvet-elves-frontend/src/pages/TeamPage.tsx`, `TeamLeadOverviewPage.tsx`, `TeamOverviewRouter.tsx`, `pages/admin/AdminTeamsPage.tsx`, `pages/users/AdminUsersListPage.tsx`; `components/team/{ManageTeamMembersPanel,TeamMembersTable,TeamSetupDialog,InviteUserModal,PendingInvitationsTable}.tsx`; `hooks/{useTeams,useInvitations}.ts`; `utils/constants.ts`; `pages/settings/settingsCards.ts`; `App.tsx`; `layouts/AppLayout.tsx`. Backend: `api/v1/{teams,invitations,admin_brokerage}.py`. |
| **Supersedes / extends** | `TEAM_MANAGEMENT_IMPLEMENTATION_PLAN.md` (2026-05-29) wired the `teams` backend into the UI. That work shipped (create/rename/delete team, make-lead, member picker, team filter, invite `team_id`). This plan fixes the **usability and consistency** gaps that remain now that the wiring exists. |

---

## 0. How to read this plan

Section 1 is the verified current state with file:line evidence. Section 2 restates Jan's feedback and the extra issues I found while reading the code. Section 3 sets the information architecture (what each page is *for*). Section 4 is the single source of truth for "who is a team member". Sections 5-8 are the concrete, phased changes. Section 9 is the test plan a non-technical tester can follow. Section 10 lists the few open product decisions.

---

## 0.1 Review log (second pass, 2026-06-24)

I re-checked the first draft against `requirements.txt`, the source, and the data flow, and corrected five workflow/logic errors. They are folded into the sections below; recorded here so the changes are traceable.

| # | Flaw in the first draft | Correction | Evidence |
| --- | --- | --- | --- |
| R1 | **Team Lead "Add existing member" silently has no candidates.** The draft featured "Add member" (search existing users) for all TeamLead+ operators. But `/users/` scopes a Team Lead to **their own team** once it has other members, so the candidate list (people *not yet* on the team) is empty for an established TL. | For a Team Lead the reliable growth path is **Invite to team** (works regardless of `/users/` scope). "Add existing member" is presented as an **Admin** tool (and a TL bootstrap-only case). See Phase 2 + Q6. | `users.py:506-517` (TL `effective_team_id`); fallback to tenant only when the team has no other members |
| R2 | **Unsafe backend filter.** The draft said "filter `users` to those roles before building `agent_rows`", but `users` is shared with `team_rows`, `scoped_user_ids`, and the tenant aggregates - mutating it would distort per-team counts and the transaction scope. | Filter **only** the `agent_rows` list comprehension into a new local; leave `users`, `team_rows`, `scoped_user_ids`, and all transaction aggregates untouched. `tenant.agent_count` is unused by any consumer, so it is left as-is. | `admin_brokerage.py:109` (`scoped_user_ids`), `:164-179` (agent_rows), `:182-193` (team_rows), `:201` (agent_count); consumers are only `TeamPage`/`AdminTeamsPage`/`TeamLeadOverviewPage` (grep) |
| R3 | **Overstated seat rationale.** The draft justified dropping the seat tiles as "moving away from seat-based billing." Seats are **still enforced** on invite; the billing-model change is plan-only behind **off** flags. | Reframe: remove the seat *display* from Team Overview because Jan finds it out of place there; seat/plan status, if shown at all, belongs on Billing/Org settings. Enforcement is unchanged. | `invitations.py:222-257` (live seat gate); `ve_credit_billing_v1`/`ve_free_members_v1` off (memory) |
| R4 | **Inaccurate reuse story for the inline roster.** The draft implied `UserDetailsModal` could be dropped in with "no change expected", but it needs owner/admin/deactivate/transfer props wired. | Reuse **`TeamMembersTable`** scoped by `teamId` for the inline roster - it already fetches `/users/?team_id=`, renders the table, and wires `UserDetailsModal` + deactivate/transfer for free. Team mutations (make-lead/remove) come from `ManageTeamMembersPanel`'s logic. | `TeamMembersTable.tsx:67-244` (self-contained, opens `UserDetailsModal`); `UserDetailsModal.tsx:54-65` (required props) |
| R5 | **Mislabeled action permissions.** The draft grouped "Remove" with Admin-only actions. | Remove-from-team is allowed for a **Team Lead** on their own team; only **Make lead / Make agent** are Admin-only (they hit the role endpoint). | `teams.py:231-260` (remove_member allows TEAM_LEAD); `useTeams.ts:142-198` (make/demote -> `PUT /users/{id}/role`, Admin-only) |

Two confirmations from the docs that the IA is sound: `requirements.txt:1112-1113` specifies the admin Users list as "Team, Status, Last Login; filter by role/status/team; search; '+ Invite User' modal (email, role, team, optional transaction)" - exactly the general directory this plan keeps. `requirements.txt:43` ("Team Lead assigns Elves to their team") and `:1064` (an Agent/Elf on a team routes to `/dashboard/team`) confirm membership is `{Agent, TC/"Elf", TeamLead}` and that it changes runtime behavior.

---

## 1. Current state (verified 2026-06-24)

The team backend is fully built and now wired. What is broken is the **routing intent, the data scoping, and the page-level UX** on top of it.

### 1.1 The three surfaces today

| Surface | Route | Component | Audience | Job today |
| --- | --- | --- | --- | --- |
| Team Overview | `/team` | `TeamOverviewRouter` -> `TeamPage` (Admin) / `TeamLeadOverviewPage` (TeamLead) | TeamLead+ | At-a-glance KPIs + production roster + teams + invites |
| Teams | `/admin/teams` | `AdminTeamsPage` | TeamLead+ (Admin writes) | Create/rename/delete teams, manage members (in a modal), make lead |
| Users & Invites | `/admin/users` | `AdminUsersListPage` | TeamLead+ | Full people directory (all roles) + pending invitations + the invite modal |

`TeamOverviewRouter.tsx:11-15` branches by role. `App.tsx:741-766` gates all three at `requiredRole="TeamLead"`. The sidebar Team group has a single entry, "Team Overview" -> `/team` (`AppLayout.tsx:374-378`); Teams and Users are reached from the Settings hub Workspace cards (`settingsCards.ts:193-212`).

### 1.2 Backend facts that anchor the fixes

- **"Team member" is already defined on the server.** `teams.py:33-37` `_TEAM_ELIGIBLE_ROLES = {AGENT, TRANSACTION_COORDINATOR, TEAM_LEAD}`. `add_member` rejects anyone else with 422 (`teams.py:215-219`). So Attorney, Admin, Client, Vendor, FSBO **cannot** be placed on a team. This is the canonical set the UI must mirror.
- **The brokerage overview does NOT filter by role.** `admin_brokerage.py:88-90` lists *all* active users (`is_active=True`), and `:164-179` turns every one of them into an "agent" row. That is why Team Overview's "Agents & production" table shows vendors, clients, attorneys, and FSBOs. (For a Team Lead the list is correctly scoped to their own `team_id` at `:97-108`, so this leak is mainly the Admin view.)
- **Invite-into-team works end to end.** `InviteUserRequest` carries `team_id` (`invitations.py:184, 261-268`) and acceptance now copies it onto the new user (`invitations.py:714-739`). The old "team_id dropped on accept" bug is fixed. Inviting as `TeamLead` grants the role and places them on the team, but does **not** set the team's `lead_user_id` pointer (that stays a separate "Make lead" action).
- **Invite role cap.** Only Admin/owner (and a TeamLead for the TeamLead role) may grant privileged staff roles (`invitations.py:139-156`). The frontend already mirrors this in `inviteableRolesFor` (`useInvitations.ts:105-132`).
- **The general invite already strips `team_id` for non-eligible roles.** `InviteUserModal.onSubmit` only attaches `team_id` when the role is in `{Agent, TC, TeamLead}` (`InviteUserModal.tsx:104-108`), so a Client/Vendor/Attorney invite can never carry a team. The Teams-page invite restriction (Phase 2) is therefore belt-and-suspenders, not the only guard. (Note: the *accept* path applies `invitation.team_id` unconditionally - `invitations.py:721-739` - so the role restriction must stay on the create side, which it does.)
- **`/users/` is team-scoped for a Team Lead.** A TL sees only their own team once it has other members; it falls back to tenant-wide *only* while their team has no other members (`users.py:506-517`). Consequence (R1): a TL cannot search for "people not yet on my team", so their reliable way to grow a team is **Invite to team**, not "Add existing member".
- **Seats are still enforced.** Inviting a billable staff role runs the live seat gate (`invitations.py:222-257`); the credit-wallet/free-members billing change is plan-only and behind off flags. This plan removes seat *display* from Team Overview but changes no enforcement (R3).

### 1.3 What each surface gets wrong

**Team Overview (`TeamPage.tsx`, Admin view):**

| # | Problem | Evidence |
| --- | --- | --- |
| A | "Seats Used" KPI tile is out of place on a team dashboard (seat/plan status belongs on Billing/Org settings; enforcement is unchanged) | `TeamPage.tsx:370-380` |
| B | A whole "Seat usage" rail card repeats the same seat data | `TeamPage.tsx:660-696` |
| C | "Manage team" button goes to `/admin/users` (Users & Invites), not `/admin/teams` | `TeamPage.tsx:321-328` (`to={ROUTES.ADMIN_USERS}`) |
| D | "By team" section rows link to `/admin/users?team_id=...` instead of `/admin/teams` | `TeamPage.tsx:552` |
| E | "Agents & production" shows non-team roles (vendor/client/attorney/FSBO) because the source list is unfiltered | `TeamPage.tsx:266-272, 453-475` fed by unfiltered `admin_brokerage.py:164-179` |
| F | Role-coverage and the "members" count include non-team roles too | `TeamPage.tsx:235-250, 291-297, 483-500` |
| G | The two bottom quick-link cards ("Team Members", "Task Templates") are redundant filler | `TeamPage.tsx:701-732` |
| H | Decorative chrome (gradient `h-[3px]` strips, "✦" kickers) conflicts with the flat, modern tool aesthetic | `TeamPage.tsx:233, 398, 235, 402, 667` |

**Teams (`AdminTeamsPage.tsx`):**

| # | Problem | Evidence |
| --- | --- | --- |
| I | You cannot see a team's members on the page. To view them you click "View on Team Members", which navigates away to `/admin/users?team_id=...` | `AdminTeamsPage.tsx:237-242` |
| J | The only in-place member view is a modal ("Manage members" -> `ManageTeamMembersPanel`); nothing is visible at rest | `AdminTeamsPage.tsx:205-209` + `ManageTeamMembersPanel.tsx` |
| K | There is no way to invite a person *into a team* from this page; invites only live on Users & Invites | `AdminTeamsPage.tsx` (no invite affordance) |

**Cross-cutting:**

| # | Problem | Evidence |
| --- | --- | --- |
| L | Three definitions of "staff/team" roles drift apart: `TeamPage` STAFF_ROLES includes Attorney + Admin; `ManageTeamMembersPanel`/`TeamSetupDialog` use `{Agent, TC, TeamLead}` (+Admin for lead pointer); backend uses `{Agent, TC, TeamLead}` | `TeamPage.tsx:291-297` vs `ManageTeamMembersPanel.tsx:31` vs `teams.py:33-37` |
| M | The Team Lead overview's primary button also points at Users & Invites, not Teams | `TeamLeadOverviewPage.tsx:186-192, 248` |

---

## 2. The feedback, restated as goals

Jan's points, plus the gaps above, reduce to four goals:

1. **Team Overview shows only the team, cleanly.** Drop seats (A, B), point team actions at `/admin/teams` (C, D, M), restrict the roster/coverage/counts to real team members (E, F), and remove the filler cards (G).
2. **Teams is a real workspace.** See a team's members in place without leaving the page (I, J), and invite people straight into a team with only team-eligible roles offered (K).
3. **"Team member" means one thing everywhere** (L) - the backend's `{Agent, TransactionCoordinator, TeamLead}`.
4. **It looks like a professional tool** (H) - flat, modern, consistent with the rest of the app.

---

## 3. Information architecture - what each page is for

The single biggest cause of confusion is that all three pages currently feel like overlapping "people" screens. The overhaul gives each a sharp, non-overlapping job. **Keep all three pages** (merging Overview into Teams would overload one screen); just sharpen the division of labor and remove every cross-link that violates it.

| Page | One-sentence job | Primary actions | What it must NOT do |
| --- | --- | --- | --- |
| **Team Overview** `/team` | "How is my team doing right now?" | Scan KPIs, production, invites; jump to Teams to act | Show non-team people; offer create/edit (that is Teams); show seats |
| **Teams** `/admin/teams` | "Build and run my teams." | Create/rename/delete; see members inline; add/move/remove; make lead; **invite into this team** | Show portal users (client/vendor/attorney/FSBO); duplicate the full directory |
| **Users & Invites** `/admin/users` | "Everyone in my workspace." | Full directory of all roles, role filter, deactivate, transfer ownership, **general invite** (any eligible role), pending-invites table | Be the only place to see team members |

Navigation rule after this plan: every "manage / view team" affordance on Team Overview points to **`/admin/teams`**. Person-profile affordances (clicking a specific human to see their account) point to **`/admin/users`** or open the existing `UserDetailsModal`. Invitations management (resend/revoke/copy-link) stays on **Users & Invites**, but *creating* an invite is available from both Teams (scoped to a team) and Users & Invites (general).

---

## 4. "Team member" - the single source of truth

Adopt one shared constant and use it on every team surface. It must equal the backend guard.

```
TEAM_MEMBER_ROLES = ['Agent', 'TransactionCoordinator', 'TeamLead']   // === teams.py _TEAM_ELIGIBLE_ROLES
```

Rules derived from it:

- **Team Overview roster, role coverage, and member count** include only these roles.
- **Teams "add member" search** already uses exactly this set (`ManageTeamMembersPanel.tsx:31`); leave it, and reuse the shared constant.
- **Invite-into-a-team** offers only the intersection of `inviteableRolesFor(inviterRole, isOwner)` and `TEAM_MEMBER_ROLES`. For an Admin that is `{Agent, TC, TeamLead}`; for a Team Lead the same set, scoped to their own team.
- **Admin** is deliberately excluded from the production roster: an Admin/owner is the operator, not a team member, and the server already refuses to put them on a team. An Admin may still be *named the lead pointer* of a team without changing their role (the existing `skipRoleChange` path, `TeamSetupDialog.tsx:104-108`, `ManageTeamMembersPanel.tsx:142-166`); that is a lead assignment, not team membership. See open decision Q1 if Jan wants producing Admins counted.
- **Lead-eligible** (who can be picked as a team's lead) stays the slightly wider `{Agent, TC, TeamLead, Admin}` (`TeamSetupDialog.tsx:37`), because an Admin/owner can be the lead pointer.

Put the constant in `utils/constants.ts` (next to `ROLE_LEVEL`) so frontend and tests share it, and add a one-line comment tying it to `teams.py:_TEAM_ELIGIBLE_ROLES` so the two never drift again.

---

## 5. UX charter (the bar every screen is measured against)

1. **Clicks, not plumbing.** Create a team, see its members, add/move someone, make a lead, invite into the team - all buttons, dropdowns, search-and-click, or a short text field. Never an ID, URL, role code, or JSON.
2. **One intent, one action.** "Make Jane the lead" stays one button (grant role + place on team + set pointer), as already built.
3. **No dead-end redirects.** A button labelled about *teams* lands on the Teams page; a button about *people* lands on the directory. Nothing sends you somewhere unrelated and makes you backtrack.
4. **See before you act.** A team's members are visible on the Teams page itself; you never navigate elsewhere just to read the roster.
5. **Plain language.** "Team", "Team Lead", "Members", "Invite to team" - never "tenant", "role enum", "team_id", "scope".
6. **Honest empty states.** No demo/sample rows. If a team has no members, say so and offer the add/invite buttons (mirrors `no-test-affordances-on-production-surfaces` and `no-demo-data-without-real-data`).
7. **Confirm the consequential.** Moving someone between teams, deleting a team, demoting a lead - all keep their existing confirm dialogs.

---

## 6. The plan, phase by phase

### Phase 1 - Team Overview cleanup (`TeamPage.tsx` + `TeamLeadOverviewPage.tsx`)

Frontend only. No backend dependency.

1. **Remove the "Seats Used" KPI tile** (`TeamPage.tsx:370-380`) and **the "Seat usage" rail card** (`:660-696`). Drop the now-unused `seatLimit/staffSeats/seatsRemaining/seatPercent` math (`:285-289`) and the `ShieldCheck` import if it falls out of use. This is a *display* change only - the seat gate on invite is unchanged (R3); plan/seat status, if surfaced anywhere, stays on Billing/Org settings. The KPI grid goes from six tiles to a clean four or five: **Team Members, Active Tx, Pipeline, Pending Invites** (and optionally Recently Active). Re-balance the grid columns (it is `lg:grid-cols-6` today at `:337`).
2. **Repoint "Manage team"** (`:321-328`) from `ROUTES.ADMIN_USERS` to `ROUTES.ADMIN_TEAMS`. Keep the label "Manage teams".
3. **Repoint the "By team" rows** (`:552`) from `${ROUTES.ADMIN_USERS}?team_id=...` to `ROUTES.ADMIN_TEAMS` (optionally `?team=<id>` so Teams can deep-select that team, see Phase 2). The section's "Manage" / "Create your first team" links already correctly target `ADMIN_TEAMS` (`:525-541`) - leave them.
4. **Restrict the roster to team members.** Filter `agentsByPipeline` (`:266-272`) to `TEAM_MEMBER_ROLES`. This removes vendors/clients/attorneys/FSBOs from "Agents & production". (Belt and suspenders even after the backend filter in Phase 3.)
5. **Restrict role coverage, the header count, and recently-active to team members.** Critically, `members` is sourced from `/users/` (`:235-238`), which for an Admin returns **every role including clients/vendors**, so today the "N members" pill and "Active Members" KPI silently count portal users. Filter `members`/`roleCounts` (`:235-250`), the `STAFF_ROLES` coverage list (`:291-297, 491-498`), and `recentlyActive` (`:252-263`) to `TEAM_MEMBER_ROLES`, so the pill, the KPI, the coverage bars, and "Recently active" all agree with the roster.
6. **Remove the two bottom quick-link cards** ("Team Members", "Task Templates", `:701-732`). Task Templates already has its own Settings card (`settingsCards.ts:213-222`); the people link is replaced by the header button. If a quiet jump-off is still wanted, fold a single inline text link ("Manage in Teams ->") into the roster header instead of two big cards.
7. **Team Lead overview parity** (`TeamLeadOverviewPage.tsx`): repoint the header button (`:186-192`) and the empty-state link (`:248`) from `ROUTES.ADMIN_USERS` to `ROUTES.ADMIN_TEAMS`. The TL roster is already correctly scoped to `myTeamId` (`:114-120`), and `/admin/teams` already shows a TL only their own team (`AdminTeamsPage.tsx:77-81`), so this lands them exactly where they manage their team.

**Outcome:** Team Overview is a clean, honest, team-only dashboard whose every action button takes you to the right place.

### Phase 2 - Teams becomes an in-place workspace (`AdminTeamsPage.tsx`)

This is the heart of the overhaul. Today a team is a one-line row whose members are hidden behind a modal or an off-page redirect. Make members visible **on the page** and let you invite into the team **on the page**.

**Layout: master + detail (recommended).** Within the existing `SettingsPageShell width="wide"` single column:

- **Top: the team list** stays, but each row becomes *selectable* (click a row to select it). Keep the create/rename/delete affordances and the lead/member/active summary line (`:181-235`). Remove the "View on Team Members" off-page link (`:237-242`).
- **Below (or beside on wide screens): the selected team's detail panel**, rendered in place:
  - **Header**: team name, lead (crown), member count; primary button **"Invite to team"** (always) and, for Admins, **"Add member"** (search existing users); secondary **Rename** / **Delete** (Admin only). See the TL note below on why Invite leads.
  - **Roster table (reuse `TeamMembersTable`, R4)**: render `<TeamMembersTable teamId={selected.id} currentUser={user} />`. It already fetches `/users/?team_id=`, renders the Name+email / Role / Last sign-in table, and wires row-click -> `UserDetailsModal` with the owner/deactivate/transfer plumbing - so viewing a member and acting on their account works inline with no new wiring. Add a small prop to hide its now-redundant "Team" column when it is scoped to a single team.
  - **Team membership actions**: Make lead / Make agent / Remove-from-team reuse `useMakeTeamLead` / `useDemoteTeamMember` / `useRemoveTeamMember` and their confirm dialogs from `ManageTeamMembersPanel`. Surface them either (a) inline by extending `TeamMembersTable` with optional `teamActions` props (cleanest, one table), or (b) by keeping the existing in-page **"Manage members"** editor modal for mutations while the inline table handles viewing. Either way there is no page navigation. **Permissions (R5):** Remove-from-team is allowed for a Team Lead on their own team (`teams.py:231-260`); **Make lead / Make agent are Admin-only** (they call `PUT /users/{id}/role`, `useTeams.ts:142-198`), so gate those two on `isAdmin`.
  - **Empty state**: "No members yet" + the Invite (and, for Admins, Add member) buttons (honest, no demo rows).
- **First team auto-selected** on load (the TL's own team, or the first team for an Admin) so members are visible immediately with zero clicks. Read an optional `?team=<id>` query param (via `useSearchParams`, as `AdminUsersListPage` does) so Team Overview can deep-link a specific team into the selected state (ties to Phase 1.3).

**Add member vs Invite - the Team Lead reality (R1).** "Add member" searches existing users *not yet on this team*. For an **Admin** that works (they read the whole directory). For a **Team Lead** it does **not**: `/users/` returns only their own team once it has members (`users.py:506-517`), so the candidate search is empty. Therefore: lead with **"Invite to team"** for everyone (it works regardless of `/users/` scope and lands the new person on the team on accept), and show **"Add member" to Admins** (and to a TL only in the bootstrap case of an empty team, where the fallback makes the directory visible). This keeps the search-and-pick flow where it actually works and never presents a TL an empty, confusing picker. A backend scope change to let a TL pull unassigned agents into their team is possible but out of scope here (see Q6).

> Alternative considered: keep `AdminTeamsPage` as a list and make each row an **accordion** that expands to its roster inline. Simpler to build, but it scales worse with many members and reads less like a tool. Master+detail is the recommendation; accordion is the fallback if Jan prefers minimal change (open decision Q2).

**Invite to team** (new, but pure reuse):

- Reuse `InviteUserModal`, opened from the selected team's header with the team **pre-set** (no team picker needed since the team is the context) and the role dropdown **restricted to `TEAM_MEMBER_ROLES` intersected with `inviteableRolesFor`**. Today `InviteUserModal` offers all inviteable roles and shows a team picker (`:230-283`); for the Teams-page entry point it should accept props like `lockedTeamId` and `roleAllowList` so it renders "Inviting to <Team name>" as fixed context and only lists `{Agent, TC, TeamLead}` (further capped by the inviter's privileges).
- On submit it calls the same `useCreateInvitation` with `team_id` set. Acceptance already lands the person on the team (`invitations.py:714-739`). Inviting as TeamLead grants the role + places them; it does not auto-set the team's lead pointer - the success toast should say so ("Invited as Team Lead and added to <Team>. Use Make lead to hand off leadership.").
- After sending, the new invite appears in the Pending Invites surfacing. Decide where pending invites for a team show (open decision Q3): minimally, keep the canonical pending-invites table on Users & Invites and show a small "N pending invites to this team" line in the team detail that links there; ideally, render a compact per-team pending list inside the detail panel by filtering `useInvitations()` on `team_id` (the data is already available, as `TeamLeadOverviewPage.tsx:139-145` does).

**Outcome:** From `/admin/teams` an Admin selects a team, sees exactly who is on it, and adds/moves/invites without a single off-page hop. Only team-eligible roles can ever be invited or added.

### Phase 3 - Make the backend roster team-only (`admin_brokerage.py`)

One small, surgical filter so Team Overview's data is correct at the source (not just hidden in the client).

- **Filter only the flat roster, not the shared `users` list (R2).** Build `agent_rows` (`admin_brokerage.py:164-179`) from a *new local* `roster_users = [u for u in users if u.role in TEAM_MEMBER_ROLES]`. Do **not** mutate `users` itself - it is also used for `scoped_user_ids` (the transaction-scope set, `:109`), `team_rows` agent_count (`:182-193`), and the tenant aggregates. Mutating it would distort per-team counts and the TL transaction scope.
- **Leave the aggregates and per-team counts untouched.** The tenant-wide transaction figures (active_transaction_count, pipeline_volume_cents, closing_this_week_count, `:139-159`) stay computed over all deals - they are brokerage totals, labeled "Active Tx"/"Pipeline", not "team member" counts. `team_rows` agent_count is already effectively eligible-only (a non-eligible user can never have `team_id` set via the API), so it needs no change. `tenant.agent_count` (`:201`) is read by **no** consumer (grep: only `TeamPage`/`AdminTeamsPage`/`TeamLeadOverviewPage` use the response, and none read `tenant.agent_count`), so leave it as-is.
- The Team Lead path already filters to the lead's `team_id` (`:97-108`); the new role filter on `roster_users` is consistent and harmless there.
- This is the only backend change in the plan. It removes the root cause of issue E rather than papering over it on the client; the Phase 1.4 client filter then becomes a cheap second guard.

> Decision point Q1: if Jan wants Admins who personally carry deals to appear in production, widen the roster filter to `TEAM_MEMBER_ROLES + {Admin}` and label the page accordingly. Default in this plan: team members only.

### Phase 4 - Design modernization (flat, professional tool)

Apply the established flat aesthetic (per the `flat-modern-tool-aesthetic` and `jan-list-surfaces-table-modal-modern-selectors` guidance) to the two surfaces we are already touching, so the overhaul also *looks* finished:

- **Remove the decorative gradient `h-[3px]` top strips** on cards (`TeamPage.tsx:233, 398`; `TeamLeadOverviewPage.tsx:233`) and the **"✦" mono kickers** (`TeamPage.tsx:235, 402, 667`), replacing them with flat card headers, hairline dividers, and sentence-case section labels.
- **Selectors are shadcn `Select` + `SegmentedControl`**, never native `<select>` (the invite/role/team pickers already use shadcn `Select` - keep that).
- **List surfaces are tables; detail is a modal** (`UserDetailsModal`), matching `AdminUsersListPage` / `TeamMembersTable`.
- **Filter + search on one line** where both exist (already true on Users & Invites `:140-199`).
- Keep within `SettingsPageShell` (single white sheet, centered column) so Teams and Users read as one document family.

This phase is presentation only - no behavior change - and should be screenshot-verified before being called done.

---

## 7. Backend changes (complete list)

Exactly one, and it is a filter, not a new endpoint or schema:

| File | Change | Why |
| --- | --- | --- |
| `api/v1/admin_brokerage.py:164-179` | Build `agent_rows` from a new local `roster_users` filtered to `{AGENT, TRANSACTION_COORDINATOR, TEAM_LEAD}`. Do **not** mutate the shared `users`; leave `scoped_user_ids` (`:109`), `team_rows` (`:182-193`), `tenant.agent_count` (`:201`), and the transaction aggregates (`:139-159`) untouched (R2) | Team Overview's roster must be team members only (issue E) without distorting per-team counts or transaction scope |

Everything else (create/rename/delete team, add/remove member, make/demote lead, invite with `team_id`, accept applies `team_id`, role cap) **already exists and is correct** - this plan only consumes it.

---

## 8. Frontend change inventory (file by file)

| File | Phase | Change |
| --- | --- | --- |
| `utils/constants.ts` | 4/all | Add shared `TEAM_MEMBER_ROLES = ['Agent','TransactionCoordinator','TeamLead']` with a comment tying it to `teams.py:_TEAM_ELIGIBLE_ROLES` |
| `pages/TeamPage.tsx` | 1,4 | Remove Seats KPI (`:370-380`) + Seat usage card (`:660-696`) + seat math (`:285-289`); repoint "Manage team" (`:321-328`) and "By team" rows (`:552`) to `ADMIN_TEAMS`; filter roster/coverage/count to `TEAM_MEMBER_ROLES`; remove bottom quick cards (`:701-732`); flatten chrome (`:233,398,235,402`) |
| `pages/TeamLeadOverviewPage.tsx` | 1,4 | Repoint header button (`:186-192`) + empty-state link (`:248`) to `ADMIN_TEAMS`; flatten chrome (`:233,235`) |
| `pages/admin/AdminTeamsPage.tsx` | 2,4 | Master+detail layout: selectable team rows; render `TeamMembersTable` as the in-place roster; "Invite to team" (all) + "Add member" (Admins); remove "View on Team Members" redirect (`:237-242`); auto-select first/own team; read optional `?team=` via `useSearchParams` to deep-select |
| `components/team/TeamMembersTable.tsx` | 2 | Reused for the inline roster scoped by `teamId` (already wires `UserDetailsModal` + deactivate/transfer). Add an optional prop to hide the redundant "Team" column when single-team; optionally accept `teamActions` (make-lead/remove) to render membership actions inline (R4) |
| `components/team/ManageTeamMembersPanel.tsx` | 2 | Source of the candidate-search + make/demote/remove logic (kept as the in-page "Manage members"/"Add member" editor, or folded into `TeamMembersTable` `teamActions`); use shared `TEAM_MEMBER_ROLES` (`:31`) |
| `components/team/InviteUserModal.tsx` | 2 | Add optional `lockedTeamId` + `roleAllowList` props so the Teams-page entry pre-sets the team and lists only team-eligible roles; default behavior unchanged for Users & Invites. (`onSubmit` already strips `team_id` for non-eligible roles, `:104-108`.) |
| `components/users/UserDetailsModal.tsx` | - | No change. It is reached *through* `TeamMembersTable`, which supplies its required owner/admin/deactivate/transfer props - so it is not wired directly by `AdminTeamsPage` (R4) |
| (optional) `pages/settings/settingsCards.ts` | - | Minor consistency: the "Teams" card is `adminOrOwner` (`:211`) while the route is TeamLead+; consider widening to `teamLeadOrOwner` so a TL can find Teams in the Settings hub too (see Q4) |
| (optional) `pages/users/AdminUsersListPage.tsx` | - | No change required; remains the general directory + invite (matches `requirements.txt:1112-1113`) |

No route additions. No changes to `App.tsx` routing (the three routes already exist at TeamLead+).

---

## 9. Test plan - validatable entirely by a non-technical tester

Each step is mouse-driven and observable in the UI. "PASS" criteria are concrete.

**A. Team Overview is clean and team-only**
1. Open **Team Overview** (`/team`) as an Admin. PASS: there is **no** "Seats Used" KPI tile and **no** "Seat usage" card.
2. Look at "Agents & production". PASS: every row is an Agent, Transaction Coordinator, or Team Lead. **No** clients, vendors, attorneys, or FSBOs appear. The "N members" pill equals the number of rows.
3. Click **"Manage teams"** (top right). PASS: you land on the **Teams** page (`/admin/teams`), not Users & Invites.
4. In the "By team" list, click any team. PASS: you land on the **Teams** page (not Users & Invites).
5. Scroll to the bottom. PASS: the old "Team Members" and "Task Templates" cards are gone.
6. Repeat 1-4 signed in as a **Team Lead**: the page shows only your team, and the top button lands you on Teams scoped to your team.

**B. Teams shows members in place**
7. Open **Teams**. PASS: the first team is selected and **its members are listed right there** - you did not have to click "View team members" or leave the page.
8. Click another team in the list. PASS: the member roster updates in place to that team.
9. Click a member row. PASS: their detail opens in a modal (no page navigation).

**C. Add / move / lead, all in place (signed in as an Admin)**
10. Click **"Add member"**, search a name, click it. PASS: they appear in the roster immediately; a toast confirms.
11. Add someone already on another team. PASS: a confirm dialog explains the move; after confirming they move teams.
12. On a non-lead member, click **Make lead**, confirm. PASS: the crown moves to them; the toast confirms. (Make lead / Make agent appear only for Admins.)
13. Try to find a vendor/client/attorney in "Add member" search. PASS: they never appear (only Agent/TC/TeamLead are listed).

**D. Invite into a team, restricted roles**
14. Click **"Invite to team"** on a selected team. PASS: the dialog names the team it is inviting to; the Role dropdown lists **only** Agent, Transaction Coordinator, Team Lead - no Client/Vendor/Attorney/FSBO/Admin.
15. Send an invite as "Agent". PASS: a success toast; the invite shows in pending invites; (when accepted) the new user lands already on that team.
16. Sign in as a **Team Lead** and open Teams. PASS: you see only your own team, its members are listed inline, and **"Invite to team"** is the primary way to add people (it is fixed to your team, same restricted roles). "Add member" is absent (or shows no candidates) because a TL's directory is scoped to their team - this is expected, not a bug (R1).

**E. Users & Invites still does the general job**
17. Open **Users & Invites**. PASS: the full directory (all roles incl. clients/vendors) is here, with role filter and the general "Invite user" (which still offers portal roles). Nothing about this page regressed.

**F. Looks like a tool**
18. Eyeball Team Overview and Teams. PASS: no gradient top strips, no "✦" kickers; flat headers, hairline dividers, shadcn selectors; consistent with Users & Invites.

A short screen-recording of A-F is the acceptance artifact (mirrors `verify-rendered-output-not-just-mechanism`).

---

## 10. Open decisions (small, with a recommended default)

| # | Question | Recommended default |
| --- | --- | --- |
| Q1 | Should Admins who personally carry deals appear in "Agents & production"? | **No** - team members only (`{Agent, TC, TeamLead}`). Admins are operators; the server already bars them from teams. |
| Q2 | Teams detail layout: master+detail panel vs accordion rows? | **Master+detail** (auto-select first/own team). Accordion is the low-effort fallback. |
| Q3 | Where do pending invites for a team live? | Keep the canonical table on Users & Invites; show a compact per-team pending list in the Teams detail by filtering `useInvitations()` on `team_id`. |
| Q4 | Should the Team sidebar group add a direct "Teams" entry next to "Team Overview"? | Optional. Teams is already reachable from Settings + the Overview button; add a sidebar entry only if Jan wants one-click access. |
| Q5 | Keep `/team` and `/admin/teams` as two pages? | **Yes** - distinct jobs (scan vs manage). Merging overloads one screen. |
| Q6 | Should a Team Lead be able to pull *unassigned* agents into their team via "Add member"? | **Defer.** Today `/users/` scopes a TL to their own team (`users.py:506-517`), so this needs a backend scope change (e.g. let a TL also see team-less, team-eligible users). Out of scope for this plan; TLs grow their team via Invite. Revisit if testers ask. |

---

## 11. Out of scope (explicitly)

- No schema changes, no new tables, no new endpoints (one backend filter only).
- No change to per-team task templates, checklist templates, tagged notes, preferred vendors, or internal resources (`settingsCards.ts:243-281`) - they keep their Settings cards.
- No change to seat/credit billing logic; this plan only *stops displaying* seat counts on Team Overview. Billing model work is tracked separately (`platform-payment-credit-wallet-build-plan`, `stable-user-mgmt-credit-billing-plan`).
- No change to the dashboard-routing side effect of assigning a team (an Agent/TC with a `team_id` is routed to the Team dashboard); that behavior is intended and documented in the prior plan.
- `components/active-transactions/AssignTeamModal.tsx` is unrelated (it manages per-transaction assignments, not team membership) - leave it alone despite the name.

---

## 12. Why this is the right shape

- **Grounded:** every change cites a verified file:line, and the central fix (team-only roster) corrects a real backend leak (`admin_brokerage.py` lists all roles), not a cosmetic symptom.
- **Convenience-first:** the operator never leaves a page to do a page's job - members are visible where teams are managed, and invites are one button from the team they belong to.
- **Consistent:** one `TEAM_MEMBER_ROLES` constant, equal to the server guard, removes the three-way drift that let off-team people show up.
- **Low-risk:** almost entirely UI wiring on stable, already-built endpoints; the one backend change is a filter; no migrations.
- **Testable by non-developers:** section 9 is a pure click-through with concrete PASS criteria and a recorded walkthrough as the acceptance artifact.
