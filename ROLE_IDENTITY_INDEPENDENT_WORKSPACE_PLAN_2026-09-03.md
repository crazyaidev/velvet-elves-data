# Role identity and independent workspaces

**Date:** 2026-09-03 · **Updated:** 2026-09-04 — §4.5 owner four-way switch; seat caps removed (membership is unlimited); second-review fixes folded in (guard-split Phase 2F, scope snap activates with 2E, posture decision, Needs You link, TL lead hand-off)
**Status:** Plan only. No source code is changed by this document.
**Repos reviewed:** `velvet-elves-frontend`, `velvet-elves-backend`
**Signup roles in scope:** Agent, Team Leader (`TeamLead`), Transaction Coordinator, Admin
**Supersedes (for staff identity):** the “hide the page / owner bypasses Admin” model in `AUDRI_THREAD_CONFIRMED_RESOLUTION_PLAN.md` §4 and `ROLE_AUTONOMY_REMEDIATION_PLAN_2026-07-31.md` Phase 1–2, *for how a role operates*. Those plans remain correct for **lock-out prevention** and **billing/org authority**. They are the wrong model for **professional identity**.

---

## 0. Decision

> **A role is a product identity, not a permission filter.** Each of the four signup roles gets a workspace it can run independently: its own landing, its own specialized features, and the configuration that identity needs to do the job. Workspace *ownership* (billing, danger zone, inviting staff) is a separate badge on the same person. It must never replace the chosen role, and it must never force that person through another role’s console to become operational.

This is the opposite of the current staff model:

| Today | Target |
|---|---|
| One shared `AppLayout` for Agent / TC / Team Lead / Admin | Four staff identities, each with a first-class workspace (same pattern Client / Vendor / Attorney already have) |
| Differentiate by hiding Team / Admin nav and gating routes | Differentiate by **specialized features and default scope**, not by locking people out of their own tools |
| Agent founder is Owner, so APIs treat them as Admin, but the UI still treats them as a junior Agent | Agent founder stays an **Agent**. Owner settings are a distinct strip, not the Admin Console |
| TC lands on the Solo Agent dashboard | TC lands on a **coordinator workspace** |
| Team Lead founder has no team row | Team Lead founder is minted **with a team they lead** |
| Configuration that makes a role “real” lives on Admin-only pages | Configuration a role needs lives **inside that role’s workspace** |

Attorney, Client, FSBO, and Vendor already follow the target pattern (exact-role shells, own landing, own features). Staff must catch up to that standard—not by cloning those portals, but by giving each staff role the same *completeness*.

---

## 1. Why this is broken now (source-grounded)

### 1.1 Signup already stores the role. Identity still collapses.

Password signup honors Agent / Team Lead / TC / Admin (`SELF_SIGNUP_ROLES_NOW` in `app/models/enums.py`; dropdown in `src/utils/accountTypes.ts`). The founder always gets a new tenant and `tenants.owner_user_id`.

What does **not** happen at mint:

- No team is created (`users.team_id` stays null). A Team Lead lands on Team Command with only themselves in scope (`team_scope.py` fails closed to `[self]`).
- No role-specific settings row (AI confidence, playbook, fee catalog, document defaults).
- No credit wallet until first billed action.
- Task templates stay platform globals (`tenant_id IS NULL`); nothing is cloned for this tenant.
- OAuth signup still **forces `Admin`** (`oauth_service.py` `_get_or_create_profile`), so Google/Microsoft sign-up cannot be an Agent at all.

The role string is a label. The product behind it is still “internal ops, one shell.”

### 1.2 Page-hiding is the differentiator—and it is the flaw

Staff share `AppLayout` and almost the same Deals / Workflow / Intelligence routes. `DASHBOARD_SHELL_BY_ROLE` only adds sidebar sections (`team`, `admin`) and swaps the brand string:

| Role | Brand | Landing | Sidebar extras |
|---|---|---|---|
| Agent (no team) | Transaction OS | `/dashboard/agent` | none |
| TC (no team) | Transaction OS | **same `/dashboard/agent`** | none |
| Agent/TC on a team | Team Command | `/dashboard/team` | none |
| Team Lead | Team Command | `/dashboard/team` | team |
| Admin | Admin Console | `/dashboard/admin` | team + admin |

Identity dashboards use exact `RoleRoute` (no owner bypass). Management pages use `ProtectedRoute requiredRole` **with owner bypass**. Result:

- An Agent founder **cannot** open `/dashboard/admin` (identity gate). That is correct.
- An Agent founder **can** open Integrations, AI Governance, Document Templates, Billing, Users, Teams *if they know the URL or find a Settings card* (`adminOrOwner` in `settingsCards.ts`). That is how the old plans prevented lock-out.
- The Agent **sidebar still omits** those sections (`sidebarSections` is role-only). So the founder is operationally an Admin on the API and a truncated Agent in the chrome.

That split is what “loses distinct identity.” The person picked Agent. The system will not let them finish becoming an Agent unless they borrow Admin surfaces. If they do borrow them, they are no longer working as an Agent—they are a makeshift Admin with an Agent badge.

Concrete examples in the live tree:

- `NeedsYouPage.tsx` — `canManageAutomation = user?.role === 'Admin'` (owner is ignored). An Agent founder who lives on Needs You cannot tune the automation they depend on from that page.
- `POST /teams` is `require_role(ADMIN)` (owner bypass lets a Team Lead founder call it, but the Team Lead UI assumes a team already exists).
- All Documents is documented as “the Agent workflow queue” (`DocumentsPage.tsx`) yet the same page serves Admin and Team Lead with a wider data filter. Scope is not a specialized feature.
- Transaction Coordinator has **no dashboard of its own**. `getLandingRoute` maps TC to the Solo Agent dashboard. There is `SoloAgentDashboardPage`, `TeamLeaderDashboardPage`, `AdminDashboardPage`, `AttorneyDashboardPage`—no coordinator page.

### 1.3 Two kinds of configuration were mashed together

| Kind | What it is | Who must own it |
|---|---|---|
| **Identity config** | Mailbox, e-sign, writing style, Trusted vs Autopilot *for my files*, my fees, my document habits, who I represent | The person doing that job |
| **Workspace admin config** | Company name, billing, branding, tenant-wide AI floors, advertising, payment-access policy, audit log, brokerage document-template library | Owner / Admin |

Today almost all of the first column is either missing at mint or locked behind the second column’s pages. An Agent account therefore cannot apply the configuration that makes it an Agent.

### 1.4 What already works (keep)

- Isolated tenant per self-serve signup.
- `is_tenant_owner` computed on login / `/me` and honored in `require_role`.
- Portal identities (Client / FSBO / Vendor) and Attorney already have independent shells.
- Per-user Connections (`SettingsConnectionsPage`) is already the right *shape* for mailbox / e-sign; Admin Integrations is a different job (webhooks, CRM, tenant keys).
- Owner cannot be locked out of billing / company / invites. **Do not undo that.**

### 1.5 Stale comments (fix in the same workstream, later)

- `UserRegisterRequest.role` still documents “accepted but ignored / always Admin.” Password signup honors the field.
- OAuth comments say they “mirror AuthService.register” while still forcing Admin.
- `users.py` B6 (owner self-role-change): the comment and 422 message still say the owner “cannot self-promote to Admin,” but `SELF_SIGNUP_ROLES_NOW` includes Admin, so they can. Align both with §4.5.

---

## 2. Target model

### 2.1 Three facts on every staff user

```
identity  = UserRole          → which workspace and specialized features
owner     = is_tenant_owner   → business administration of this tenant
scope     = assignment | team | tenant-wide   → which deals the identity sees
```

Never derive identity from owner. Never derive owner from identity. Admin is a *job* (run the brokerage). Owner is a *legal/billing fact*. A person can be both (Admin founder) or only the first (invited Admin) or only the second (Agent founder).

### 2.2 Independent workspace, not a hidden page

For each of the four roles, “workspace” means all of:

1. **Landing** that is that role’s home (not a shared Agent page).
2. **Primary job surface** specialized to that role (not the same queue with a different `WHERE` clause as the only difference).
3. **Identity settings** reachable from that workspace without visiting another role’s console.
4. **A complete first session** after signup: the founder can configure and run that job on day one.
5. **Invitee mode** of the same identity: an invited Agent in a brokerage gets the Agent workspace, not Owner settings.

Client / Vendor / Attorney already satisfy (1)–(3). Staff must satisfy (1)–(5).

### 2.3 Specialize features; share primitives

Share engines, not chrome:

| Shared (keep one implementation) | Specialized per role (own UI + defaults) |
|---|---|
| Transaction record, documents blob store, task engine, calendar, payments ledger, Ask AI | Home dashboard, default nav, default CTA, empty states, “what to do next” |
| Wizard intake pipeline | Which wizard fields are prominent (Agent: representation + listing; TC: file + parties + vendors) |
| Email / e-sign providers | Connections panel inside identity settings |
| Automation Conductor | Agent: Trusted / You confirm on *my* files. Team Lead: team posture. Admin: tenant floors and kill switches |

A page that every staff role hits (All Documents, Needs You, Active Transactions) may stay shared **only if** each identity has a distinct *job* on it (filters, CTAs, empty states, and settings). If two roles would see the same page doing the same job, one of them does not have an identity yet.

### 2.4 Owner strip (not Admin Console)

When `is_tenant_owner` is true, the chrome shows a small **Owner** area (already a badge in `AppLayout`):

- Company, branding, billing, danger zone
- Invite staff (membership is unlimited — VE bills per transaction, never per person)
- Create the first team (Team Lead / Admin founders; Agent founder only if they choose to grow)

This strip must not dump the Agent into `/dashboard/admin`, AI Governance, Advertising, or the tenant audit log. Those remain **Admin identity** features.

---

## 3. The four identities

Each subsection is the definition of “this role can function with its own distinct identity.” If a founder of that role cannot do the listed job without opening another role’s console, the identity is incomplete.

### 3.1 Agent — “I originate and run my files”

**Job.** Represent a side, open deals, keep dates honest (You confirm / Trusted), chase documents, get to closing.

**Workspace.**

- Landing: Solo Agent dashboard (`/dashboard/agent`) for founders and unteamed Agents. Team Command only after they *join* a team, not because they are Owner.
- Brand: Transaction OS (solo) or Team Command (member)—never Admin Console.
- Primary CTA: New Transaction.
- Nav: Deals, Workflow (Needs You, My Task Queue, All Documents, Calendar), Payments, Vendors, Intelligence, **My setup**.

**Identity config (must live here, not on Admin pages).**

- Representation default (Buyer / Seller / both)
- Mailbox + e-sign (existing Connections)
- Writing style / email templates *for me*
- Trusted dates vs Autopilot *for my files* (today’s posture is tenant-default; Agent founder needs a personal or “this workspace is me” control)
- Professional fee defaults for *my* deals
- Document habits: which requirements I track on my files (inherit platform library; allow personal emphasis—not the brokerage template-admin screen)

**Must work on day one without an Admin.** Connect email, set representation, open a deal, upload a PA, confirm dates, see Next / Needs You. AI confidence may use platform defaults until an Admin exists; the Agent must not be blocked waiting for an AI Governance page they cannot (and should not) become.

**Must not become.** Tenant-wide advertising, payment-access policy editor, brokerage audit log, other people’s files (unless assigned). Owner strip covers company/billing only.

### 3.2 Transaction Coordinator — “I run the file”

**Job.** Keep the file moving: documents in, tasks cleared, vendors and dates on track. Origination is secondary.

**Workspace (does not exist today—this is the largest identity hole).**

- Landing: **new** `/dashboard/coordinator` (do not reuse Solo Agent).
- Brand: File desk / Coordinator workspace (final copy TBD; must not say Transaction OS-as-Agent).
- Primary CTA: Open file / New Transaction (solo TC shops still create files) plus “Intake documents.”
- Nav emphasis: All Documents, Needs You, Task Queue, Calendar, Vendors, Contacts—not listing-side marketing chrome.

**Identity config.**

- Same Connections (mailbox / e-sign) as Agent—coordinators send and collect.
- Default document checklist emphasis (what “complete file” means).
- Vendor defaults (title, lender, inspector) for new files they open.
- Notification density (coordinators live in queues; Agents live in dates).

**Must work on day one.** Upload/classify documents, drive Needs You, assign or chase vendors, without being told they are an Agent.

**Must not become.** A skin of Solo Agent. Sharing `SoloAgentDashboardPage` is the current identity collapse and is explicitly in scope to split.

### 3.3 Team Lead — “I run a team’s files”

**Job.** See the team’s blockers, coach, set team playbook, cover coverage gaps. Not “Admin with a team dashboard.”

**Workspace.**

- Landing: `/dashboard/team` (exists).
- Brand: Team Command.
- Primary CTA: New Transaction (for coverage) + Invite to team.

**Bootstrap (mandatory at signup).**

When the chosen role is Team Lead, mint:

1. A `teams` row (`name` from organization or “{Name}’s team”).
2. `lead_user_id` = founder, `users.team_id` = that team.

Without this, Team Lead is a dashboard with no team—the identity is empty. Do **not** require a later visit to Admin → Teams (`create_team` is Admin-gated today).

**Identity config.**

- Team playbook / task-template overrides for *this team*
- Team automation thresholds (the Team Lead path in confidence settings—surface it from Team Command, not only Admin AI Governance)
- Who is on the team (invite Agent / TC into *this* team)

**Owner strip.** Company, billing, invites. Creating a *second* team can wait for Admin identity or a later “add team” Owner action.

**Must not become.** Tenant-wide Admin Console. A Team Lead founder who needs advertising or payment-access policy either invites/hires an Admin or uses a later “promote this workspace to brokerage Admin” flow—not a silent role collapse.

### 3.4 Admin — “I run the brokerage OS”

**Job.** Tenant policy, users, templates, integrations at the *workspace* layer, oversight.

**Workspace.**

- Landing: `/dashboard/admin` (exists).
- Brand: Admin Console.
- Primary CTA: can stay New Transaction for small shops, but the home must lead with oversight (users, health, policy), not a cloned Agent briefing.

**Identity config (Admin-only on purpose).**

- Tenant AI floors / kill switches (`confidence.py`)
- Webhooks, CRM, advertising, payment-access policies
- Brokerage document-template library
- Audit log
- All teams, all users

**Day-one Admin founder.** They should *also* be able to open a deal (small brokerage = Admin who still closes). That is an Admin who **uses** the deal engine, not an Admin forced to wear an Agent identity. Offer “work a file” from Admin Console without changing `role` to Agent.

**Must not steal.** Agent / TC / Team Lead workspaces. Today an Admin cannot open `/dashboard/agent` at all — the route and the API are both exact-role. Keep it that way. If an Admin “view that desk” feature is ever wanted, it is new, read-only work, not a reason to weaken exact-role gates.

---

## 4. Signup and first-run (how identity is minted — and changed later)

### 4.1 Password signup (already chooses a role)

Keep the four choices. Default remains Agent.

On `AuthService.register`, after tenant mint, run a **role starter kit** (new, explicit, testable):

| Choice | Starter kit |
|---|---|
| Agent | Tenant + owner. No team. Seed personal posture from `default_posture` if sent. Point onboarding at Agent setup (Connections, representation). |
| Transaction Coordinator | Tenant + owner. No team. Seed coordinator workspace flag / landing. Onboarding: Connections + file-desk intro (not Agent representation-first copy). |
| Team Lead | Tenant + owner + **create team + attach founder as lead**. Onboarding: invite one Agent/TC (skippable) + team playbook confirmation. |
| Admin | Tenant + owner. Optional “create first team.” Onboarding: company + Connections + “policy later.” |

Do **not** clone the entire platform task-template library on mint (cost and drift). Inherit globals; let Team Lead / Admin overlay later.

### 4.2 OAuth signup

Honor the same four roles as password signup (store intended role in OAuth state or a post-OAuth account-type step **before** profile create). Stop forcing `UserRole.ADMIN`. Owner is still set. Starter kit is the same table. Validate the role read back from OAuth state server-side against `SELF_SIGNUP_ROLES_NOW` at the callback — state is attacker-influenced input.

### 4.3 Onboarding

Today `buildSteps` differs only mechanically (Posture renders for owner non-invitees; the E-sign step excludes Admin via `ESIGN_ROLES`) — no step is identity-shaped. Everyone gets the Agent-shaped path with pieces omitted.

Change onboarding to **identity tracks**:

| Track | Extra / different |
|---|---|
| Agent | Representation default; “your files” copy |
| TC | File-desk copy; skip representation-as-identity (they still pick a side when opening a file) |
| Team Lead | Create/confirm team name; optional first invite |
| Admin | Company + “you can work files or invite an Agent”; do not pretend they are a Solo Agent |

Owner relabel among the four stays available at any time (§4.5). While the tenant is empty — no deals, no other staff — it is frictionless (the Step 2 dropdown). Once the tenant has deals **or other staff**, the same change goes through the §4.5 warned switcher (“this changes your home, not your deals”). The boundary is product-enforced (the confirm UI); the API (B6) stays permissive.

### 4.4 Invitees

Invited Agent / TC / Team Lead / Admin join an existing tenant. They get the identity workspace **without** the Owner strip. This is the healthy case the product already intends. Founder flows must look like a *complete solo version of that same identity*, not like an invitee plus secret Admin powers.

### 4.5 Changing identity later — the owner’s four-way role switch

The motivating case: *a user created an Agent account and later requires the Admin role.* Treat it as a **job change, not a permission upgrade** — and treat it as one instance of a general function:

> **The tenant owner may switch their own identity among the four staff roles — Agent ↔ Transaction Coordinator ↔ Team Lead ↔ Admin — in any direction, through one warned switcher.** Nobody else gets it: invited staff are changed by an Admin (or accept a fresh invite), and only the owner themselves — or a platform admin — may change the owner’s role.

The three facts of §2.1 stay separate: ownership already lets an Agent founder pay, invite, and run the company; it must never quietly turn them into an Admin. The API half already exists: B6 in `users.py` bounds the owner’s self-role-change to `SELF_SIGNUP_ROLES_NOW` — exactly these four (the 422 message claiming Admin is excluded is stale, §1.5) — and the onboarding Step 2 dropdown already offers all four. What is missing is the warned post-onboarding affordance and the per-target side effects below (Phase 2E).

**Triage first: owner work or Admin work?** Most “I need Admin” is owner work, and the Owner strip (§2.4) covers it without touching `role`:

| They need… | That is… | Answer |
|---|---|---|
| Billing, company / branding, invites, danger zone | Owner work | Owner strip. Role stays as chosen |
| Tenant AI floors, advertising, audit log, payment-access policy, brokerage template library, operating all users / teams | Admin identity work | One of the two paths below |

**Two legitimate paths.** One person holds one role per workspace — nobody is Agent and Admin in the same tenant at once. (An Admin can still open and run a file from the Admin Console; that is *using* the deal engine, not wearing the Agent identity — §3.4.)

1. **Keep the current identity — hire the missing one.** Preferred while the person still does the current job (the producing Agent who needs policy / oversight help). The founder keeps their home, settings, and scope, and either invites someone into the needed role (the owner already grants like an Admin on invites — `inviteableRolesFor` F3) or promotes existing staff. This is how a producing Agent grows a brokerage without losing their desk.
2. **Switch identity — deliberate, warned.** For when *this person* will now do the other job. They accept the target identity’s home, nav, settings, and scope; the previous identity’s chrome goes away.

**Accepted trade-off:** a solo founder who needs one Admin-identity knob must switch and switch back. That friction is deliberate — the triage table keeps the common needs on the Owner strip, and rare governance knobs are not a reason to re-add silent bypasses.

**Per-target side effects.** The switch is one function, but the targets are not symmetric. The confirm copy and the write must include:

| Transition | What must ride along |
|---|---|
| **→ Admin** | Home becomes `/dashboard/admin`; tenant-wide visibility; Admin nav plus the Owner strip while they still own the tenant |
| **→ Team Lead** | Run the Team Lead starter kit (§4.1 / Phase 1B): create a team if none exists; if teams already exist, the confirm asks which to lead (or create new). Set `teams.lead_user_id` + `users.team_id`. A TL with no team is scoped to just themselves (`team_scope.py` fails closed) on an empty Team Command — the defect this plan bans |
| **→ Agent / → TC** | Scope narrows to created + assigned once a second staff user exists (§5.3 snap rule); the confirm must say so |
| **Away from Team Lead** (any target) | Nothing clears `teams.lead_user_id` today, so the team row would name a non-TL as its lead (“lead in name only” — the Make / Demote Team Lead flows already forbid this for members). Team of one: clear silently. Team with members: the confirm offers a hand-off (pick a successor) **or** an explicit “leave the team leadless for now” warning — never block the switch on finding a successor (`teams.lead_user_id` is nullable; an owner who switches to Admin still oversees every team) |

**Membership is unlimited — no transition may be blocked by a people count.** VE bills per transaction, never per person, and the marketing site promises this publicly (“No seats, no subscription… invite your whole team free” — `PricingPage`; same copy on FAQ / Brokers & Teams). The old staff-seat gate is retired (`seat_service.py`: `assert_staff_seat_available` is a no-op while `free_members` is on — the shipped default — and new tenants mint with `seat_limit = NULL`). Identity flows must not resurrect it.

**Who may switch whom.**

| Person | How their role changes |
|---|---|
| Founder / owner | Empty tenant (no deals, no other staff): relabel freely among the four (exists today — the Step 2 dropdown). Once the tenant has deals or other staff: **Owner strip → “Change my role”**, a confirm spelling out the per-target consequences above |
| Invited staff (not owner) | Cannot self-switch. An Admin — or the owner acting as workspace admin — changes them via `PUT /users/{id}/role`, or they accept a fresh invite |
| The owner, changed by someone else | Stays locked (as today): only the owner themselves or a platform admin may change the owner’s role |

**Guardrails.**

- **Warned, never silent.** Once the tenant has deals or other staff, every switch requires a confirm stating what changes (home, visibility, team) and what does not (ownership, existing deals, billing). No auto-promote from a 403, an Admin-only link, or a deep-linked Settings card — those surfaces answer “This is Admin work: switch identity, or invite an Admin.”
- **Reversible, with the mirror warning.** Every transition among the four is legal in both directions; the way down (Admin → Agent after hiring) warns about the scope snap exactly as the way up warns about widening.
- **Ownership transfer stops force-promoting.** `POST /tenants/current/transfer-ownership` today relabels the new owner to Admin (`tenants.py`) — the exact owner ≡ Admin conflation §2.1 forbids. Transfer moves the billing/legal fact only; the new owner keeps their job.
- **Never unlock in place.** Do not keep the Agent identity and open Admin APIs to it. That is the bug this plan reverses (§1.2).

**Current state (source-grounded).** B6 in `users.py` already permits the owner self-relabel within `SELF_SIGNUP_ROLES_NOW`, which **includes Admin** — the 422 message and comment claiming they “cannot self-promote to Admin” are stale (§1.5). `UserDetailsModal` correctly refuses self-edit in Users admin. `change_role` writes only `users.role` / `users.team_id`; the Team Lead mint and the lead hand-off do not exist yet. Missing, then: the warned Owner-strip switcher and the per-target side effects (Phase 2E). The free/warned boundary is enforced by the confirm UI; B6 stays permissive.

**Default answers.**

- Producing Agent who needs policy / oversight help → **invite or promote an Admin** (path 1).
- The same person now runs the brokerage → **switch identity once, warned** (path 2).
- They only need to pay, brand, or invite → **Owner strip**; role stays as chosen.

---

## 5. Navigation and authorization rewrite

### 5.1 Stop using hide-the-page as staff RBAC

Rules:

1. **Identity routes** (`/dashboard/agent`, `/dashboard/coordinator`, `/dashboard/team`, `/dashboard/admin`, portals) stay exact-role (`RoleRoute`, no owner bypass). An Agent owner does not become Admin by URL.
2. **Identity settings** for a role are allowed for that role (and the owner *of that identity*, i.e. themselves)—Connections, My Playbook, My fees. Not Admin-gated.
3. **Workspace admin** routes stay Owner or Admin (`ProtectedRoute` + `adminOrOwner`). These are Company, Billing, Users, Danger—not AI Governance, Advertising, Audit (those are Admin identity).
4. **Admin identity** routes stay `role === Admin` (plus platform admin). Owner who is an Agent does **not** pass. If they need those tools, they change identity to Admin or invite one.
5. Sidebar is built from **identity + owner strip**, never from “if Agent, omit everything useful.”

This is the explicit reversal of “navigation follows every owner capability” in the autonomy plan. Owner capability is the strip. Role capability is the workspace.

### 5.2 Shared operational pages

Keep one route for All Documents / Needs You / Transactions **if** each identity injects:

- default filter (mine / team / tenant)
- empty state copy
- primary action
- settings link *into that identity’s setup*, not into Admin

Example: Agent empty All Documents → “Upload on a file or start a transaction.” Admin empty → “No files in the tenant yet—invite an Agent or open a file yourself.”

### 5.3 Backend

- Keep `is_tenant_owner` bypass on **workspace-admin** endpoints only (tenant update, billing, invites).
- Remove the implication that owner ≡ Admin on **identity** endpoints (`require_exact_roles` for dashboards stays).
- Audit `require_role(ADMIN)` usages. Split into `require_workspace_admin` (owner or Admin) vs `require_admin_identity` (Admin role only).
- `POST /tenants/current/transfer-ownership` stops force-promoting the new owner to Admin (`tenants.py` does this today). Ownership transfer moves the billing/legal fact only; the new owner keeps their identity (§4.5).
- `list_accessible_transaction_ids`: Agent/TC stay assignment-scoped even if they are owner. **This is load-bearing for identity.** Today B4 treats owner like Admin (tenant-wide). That is why an Agent founder “loses” Agent scope—the whole tenant is their queue, which is correct for a solo shop *only if* we still present it as *my files*, not as Admin oversight. Product rule: solo owner sees all files in *their* tenant (there is no one else); the day they invite an Agent, Owner-as-Agent still sees **their** assignments unless they switch to Admin identity. Document this in API tests so it cannot regress. The snap covers **all three sibling bypasses together** — B4 `list_accessible_transaction_ids`, B5 `require_transaction_access`, B3 `require_team_access` — otherwise lists shrink while any deal stays openable by URL and team data stays exposed.

**Solo-tenant exception (explicit):** If the tenant has a single staff user, “my files” and “the tenant” are the same set. No extra UI. The moment a second staff user exists, Agent scope snaps to assignment+created. Do not keep silent tenant-wide access for an Agent founder after they hire help—that is identity collapse again. **“Staff” means the internal roles** (Agent / TC / Team Lead / Admin): an invited Attorney is a matter-scoped collaborator and does not trigger the snap (`BILLABLE_STAFF_ROLES` membership is a billing artifact, not a scope rule). The exception is **scope-only**: the settings split stands — personal posture covers a solo founder; tenant floors exist to govern others.

### 5.4 Frontend permission module

`ROLE_AUTONOMY_REMEDIATION_PLAN` Phase 1 (`permissions.ts`, stop scattering `role === 'Admin'`) is still required, but the predicates must be:

- `canManageWorkspace` → owner or Admin
- `isAdminIdentity` → role Admin
- `isCoordinatorIdentity` / `isAgentIdentity` / `isTeamLeadIdentity`
- `canManageAutomationPolicy` → Admin identity (tenant floors) vs `canManageMyAutomation` → Agent/TC/TL for *their* posture

Correction from source: `NeedsYouPage` has **no in-page automation controls** — `canManageAutomation` only gates the scheduler-health banner’s link to Settings → AI & Automation, an Admin-identity page. Route that link per identity instead: Admin → AI Governance; Agent / TC / TL → their identity automation settings once 2B ships (hidden until then). Tenant kill switches stay on Admin Console.

---

## 6. Configuration that must move (so Agent stops “losing” itself)

| Capability | Today | Target |
|---|---|---|
| Mailbox / e-sign | Connections (good) vs Admin Integrations (confused) | Connections = identity. Integrations = Admin identity (webhooks/CRM) |
| Autopilot / Trusted | Tenant cage at mint + per-deal override; no per-user layer (Needs You’s banner links only Admins to AI & Automation) | Agent/TC/TL: my/team posture in identity settings (solo tenants alias to tenant posture first — Phase 2B; true per-user layer is a follow-up). Admin: tenant floor |
| AI confidence | Defaults until Admin writes | Same split: personal/team usable defaults; Admin writes floors |
| Fees | No server catalog; parse-time plus the wizard’s per-browser `loadLastFees` prefill | Agent identity: “my fee defaults” (extend the prefill into identity settings; don’t duplicate it). Admin: optional brokerage schedule |
| Task templates | Globals; write TeamLead+ | Team Lead identity: team overlay. Admin: tenant library. Agent: use inherited |
| Teams | Created only via Admin API | Team Lead signup mints one. Admin manages many |
| Document templates | Admin-only | Admin identity keeps **brokerage forms**. Agent/TC keep **using** them on files |
| All Documents labels | Shared page | Shared page + identity empty states / default filters |

---

## 7. Phased delivery

Do not rewrite the world in one PR. Each phase must leave every signup role able to log in.

### Phase 0 — Spec freeze and inventory (0.5 d)

- Publish this document as the identity contract.
- Spreadsheet of every `require_role(ADMIN)`, `RoleRoute`, `ProtectedRoute requiredRole`, and `role === 'Admin'` in frontend. Tag each: workspace-admin / admin-identity / bug / identity-settings.
- No product code.

### Phase 1 — Stop the identity collapse (founders become who they picked)

**1A. OAuth honors signup role** (or a required post-OAuth role step before profile insert).

**1B. Team Lead starter kit:** create team + attach founder. Team Command is non-empty.

**1C. Coordinator landing:** add `/dashboard/coordinator` and `getLandingRoute` for TC. First version may compose existing KPI widgets with coordinator copy and nav emphasis—**must not** mount `SoloAgentDashboardPage` as the TC home.

**1D. Agent scope after second staff user:** build the snap-to-assignment rule (backend + tests), covering all three owner bypasses together (B3 / B4 / B5 — §5.3), **but do not activate it before 2E ships.** The snap removes a non-Admin owner’s tenant-wide view, and the sanctioned remedy — switch identity to Admin — is the 2E switcher; activating earlier strands those owners with no UI path. Ship dark behind the flag and turn on with 2E. Rollout: one-time audit of live tenants with a non-Admin owner and ≥ 2 internal staff; notify those owners before activation.

**1E. Onboarding copy tracks** (Agent vs TC vs Team Lead vs Admin) without a full wizard rewrite.

**Exit:** A tester who picks each of the four roles gets four different homes and a Team Lead who actually has a team. No source from later phases required for this to be demoable.

### Phase 2 — Identity settings (Agent can finish becoming an Agent)

**2A.** `permissions.ts` with the predicates in §5.4.

**2B.** Move “my posture / Trusted / You confirm” and “my fee defaults” onto Agent (and TC) settings. **Posture decision:** no per-user posture backend exists (tenant settings + per-deal override only), so this phase aliases a solo tenant’s “my posture” to the tenant posture (same file set — §5.3 solo exception) and defers the true per-user layer (precedence deal → user → tenant; touches the conductor) to a follow-up. Needs You’s scheduler banner links to the viewer’s identity automation settings (§5.4), not Admin AI Governance.

**2C.** Owner strip in Settings hub: Company / Billing / Invites only. Remove Agent-owner cards that deep-link into Admin identity (AI Governance, Advertising, Audit, Document Templates admin). Those cards visible only for `isAdminIdentity`.

**2D.** Sidebar: identity sections + Owner strip. Do not append the Admin Oversight group for an Agent owner.

**2E.** Identity switch (§4.5): a four-way “Change my role” switcher on the Owner strip behind the warned confirm, with the per-target side effects — Team Lead entry mints / attaches a team (reuse 1B; picker when several exist), Team Lead exit offers a lead hand-off or an explicit leadless state, Agent / TC targets warn about the scope snap. **Activate the 1D scope snap in this same release — never earlier.** Backend rides along: fix the stale B6 message; stop the transfer-ownership force-promotion.

**2F.** Backend guard split (§5.3): implement `require_workspace_admin` (owner or Admin) vs `require_admin_identity` (Admin only) and re-tag every `require_role(ADMIN)` endpoint per the Phase 0 inventory. This removes the global owner short-circuit from admin-identity endpoints — without it, Phase 2 is cosmetic: the cards hide while the AI Governance / Advertising / Audit APIs still admit an Agent owner.

**Exit:** Agent founder can connect email, set Trusted/You confirm, set fees, open a deal, and never open `/dashboard/admin` or AI Governance — and the Admin-identity APIs refuse them (2F), not just the chrome.

### Phase 3 — Specialized job surfaces (shared pages earn their keep)

**3A.** All Documents / Needs You / Active Transactions: per-identity default filter, title, empty state, CTA.

**3B.** Team Lead: team playbook and invites from Team Command (not only Admin Users).

**3C.** Admin Console: oversight home; “work a file” is a secondary action that does not change role.

**3D.** Coordinator dashboard: document/task/vendor-first layout (may reuse widgets).

**Exit:** A screenshot of each role’s home is distinguishable without reading the role badge.

### Phase 4 — Hardening

- Tests: register × 4 roles → landing, starter kit, settings visibility, scope snap.
- Update stale schema comments.
- Chrome QA (low-RAM): one founder per role, Connections, one deal, confirm they never need another role’s console to complete the happy path.
- Invitee path regression: invited Agent has no Owner strip.

---

## 8. What we will not do

- Will not mint Attorney / FSBO / Vendor at self-serve in this plan (still later phases of the Audri Option B sequence).
- Will not give invited Agents the Owner strip or tenant billing.
- Will not make Agent founder silently Admin on identity dashboards.
- Will not split into four deployable apps. One frontend, four identities.
- Will not clone the full task-template library per tenant at signup.
- Will not undo `is_tenant_owner` on billing / company / invites (lock-out is still forbidden).
- Will not auto-promote anyone to Admin — not on ownership transfer, not from clicking an Admin-only surface. Identity changes are explicit (§4.5).
- Will not reintroduce a member / seat cap anywhere in these flows. Membership is unlimited and billing is per transaction — the retired gate in `seat_service.py` stays dormant, and no signup, invite, promotion, or role switch counts people (§4.5; marketing-public promise).

---

## 9. Relationship to earlier plans

| Plan | What it got right | What this plan changes |
|---|---|---|
| `SIGNUP_ROLE_SELECTION_AND_ONBOARDING_REMEDIATION_PLAN.md` | Founder picks a role; owner cannot be locked out | Owner bypass must not equal Admin identity |
| `AUDRI_THREAD_CONFIRMED_RESOLUTION_PLAN.md` | Option B: four staff roles at signup | Admin as a signup choice is a real identity, not a test shortcut |
| `ROLE_AUTONOMY_REMEDIATION_PLAN_2026-07-31.md` | One permission function; visible capabilities | Split workspace-admin vs admin-identity; nav follows **identity**, not every owner capability |
| `ROLE_DASHBOARDS_DESIGN_UPDATE_PLAN.md` | Distinct dashboard *visuals* | TC still missing; dashboards alone are not identity if settings live elsewhere |
| Attorney / Client / Vendor / FSBO workspace plans | Independent shells work | Staff must meet that bar |

---

## 10. Verification (after implementation—not this document)

For **each** of Agent, TC, Team Lead, Admin, using a **new** self-serve account (password and OAuth):

1. Landing URL and brand match §3.
2. First-run can connect mailbox (or skip) and complete the identity’s primary CTA without a 403.
3. Settings hub shows identity cards; Admin-only cards appear only for Admin.
4. Owner badge present; Owner strip does not open Admin Console for non-Admin.
5. After inviting a second staff user, Agent/TC data scope is assignment-based.
6. Team Lead has a team row and can invite into it from Team Command.
7. The owner can switch among all four roles with the §4.5 warnings: → Admin lands on Admin Console, → Team Lead mints / attaches a team, leaving Team Lead offers a lead hand-off or an explicit leadless state, and switching back restores the identity’s scope. Ownership transfer does not change the new owner’s role.
8. Admin-identity APIs (AI Governance, Advertising, Audit) return 403 for a non-Admin owner — verified at the API (2F), not only by hidden cards.

Failure of (2) or (3) is the original bug: the account cannot apply the configuration that makes it itself.

---

## 11. Suggested implementation order (repos)

| Step | Repo | Notes |
|---|---|---|
| Starter kit + Team Lead team mint + OAuth role | backend | No UI yet; landings still old until frontend ships 1C |
| `getLandingRoute` + coordinator route + onboarding tracks | frontend | Depends on TC dashboard stub |
| `permissions.ts` + Settings hub split + Needs You banner link | frontend | Posture is tenant + per-deal only today; 2B aliases solo “my posture” to tenant posture; per-user layer is a follow-up |
| Scope snap when second staff exists | backend + tests | B3 / B4 / B5 together; ships dark, activates with 2E (do not strand non-Admin owners) |
| Owner-strip four-way role switch + transfer-ownership fix | frontend + backend | §4.5 / Phase 2E; TL mint + lead hand-off-or-leadless; includes the stale B6 message cleanup |
| Guard split `require_workspace_admin` vs `require_admin_identity` | backend + tests | Phase 2F; per Phase 0 inventory; removes the global owner short-circuit from admin-identity endpoints |
| Shared-page empty states | frontend | Phase 3 polish |

Flag (optional): `ve_role_identity_workspaces_v1`, default off until Phase 1 exit is signed off. Prefer **not** flagging the Team Lead team mint—empty Team Command is already a defect. The 1D scope snap keeps its own gate until 2E ships, regardless of this flag.

---

## 12. Success

A person who creates an **Agent** account is an Agent: they configure Agent tools, work Agent files, and keep an Agent home. Ownership only means they can pay and invite. The same sentence must be true, with the nouns swapped, for Team Lead, Transaction Coordinator, and Admin.
