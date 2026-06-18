# Multi-Workspace Membership Design Plan (Independent Agent Joins a Team)

**Author:** Jan Froben
**Date:** 2026-06-17
**Status:** Design plan only. No source code changed in this document.
**Flag (when built):** `ve_multi_workspace_v1` (default off until UI sign-off).

**Problem in one sentence:** today a person who self-registered (and therefore owns their own workspace) cannot be invited into another organization with the same email, so an independent agent cannot later join a team or brokerage without abandoning their account.

---

## 0. How I built this plan (grounding)

I verified every load-bearing claim against the live tree before writing, because the recurring failure mode in past plans was designing against an assumed architecture rather than the real one.

**Source verified:**
- `app/api/v1/invitations.py` (the existing-email rejection, lines 151-157; tenant-scoped invite checks).
- `app/models/user.py` (`User.tenant_id` is a single column; the transient `is_tenant_owner` I added this round).
- `app/core/auth.py` (`get_current_user` resolves the request's tenant from the user's single `tenant_id`; `require_tenant_access`, `require_team_access`).
- `app/core/supabase_client.py` (`get_supabase` uses the **service-role** key and bypasses RLS; `get_user_supabase` is the anon+JWT path where RLS applies).
- `app/services/seat_service.py` (`BILLABLE_STAFF_ROLES`, `staff_seat_count`, `tenants.seat_limit`, plan gating).
- `app/services/auth_service.py` (register writes `tenant_id` into Supabase Auth `user_metadata` and onto the profile row).

**Docs reviewed:** `MULTI_TENANCY_IMPLEMENTATION_PLAN.md` (which **explicitly lists this as out of scope for v1**, lines 41-45: *"Multi-tenant per-user membership (a user belonging to multiple tenants simultaneously with a switcher). Current model is one-tenant-per-user."*), `REVENUE_GENERATION_SYSTEM_PLAN.md` (Phase 7 account join/merge, and the rule that original data stays with the original account), `SIGNUP_ROLE_SELECTION_AND_ONBOARDING_REMEDIATION_PLAN.md` (§8.5), and `AUDRI_THREAD_CONFIRMED_RESOLUTION_PLAN.md` (the owner anchor this builds on).

This is the single largest architectural item on the roadmap. It is deliberately framed as a phased plan so the first slices are shippable and UI-testable on their own.

---

## 0.5 Second-pass review: flaws found in rev 1 and corrected here

I re-reviewed rev 1 against the live source a second time, specifically hunting for workflow/logic breaks. Five issues surfaced (four substantive plus a phasing-order problem). All are corrected in the body below; they are listed here so the change is transparent.

| # | Flaw in rev 1 | What the source actually shows | Correction (applied in body) |
|---|---|---|---|
| R1 | §7 changed only the **app-layer** seat mirror; it missed the authoritative gate. | The real seat gate is the SQL function `create_invitation_with_seat_check` (migration `20260512095000`). It counts active staff from `users WHERE tenant_id=p_tenant_id AND role IN(...)` (lines 97-104) **and** counts **every** staff-role pending invite toward the cap (lines 106-115). | The DB function MUST be rewritten to count from `workspace_memberships` (home/billable) and to **exempt guest** invites/memberships; otherwise a host at its seat limit cannot invite an existing agent as a guest (contradicts R4). This becomes a required migration in **M2**, not M3 (see §7, §10). |
| R2 | §5/§12 treated RLS as live "defense-in-depth on the anon path." | `get_user_supabase` (the anon/RLS client) is used **zero** times in `app/api`/`app/services`; all 59 API call sites use the **service-role** client, which **bypasses RLS**. `auth_tenant_id()` (the RLS tenant resolver) reads the single `users.tenant_id` and *deliberately ignores the JWT* (migration `20260511094000`, lines 18-22). | Active-workspace enforcement is **entirely application-layer** (simpler than rev 1 implied: no per-request Postgres session variable is needed for the live path). But there is **no RLS backstop in practice**, so a missed `tenant_id` filter leaks with no safety net, and the dormant single-tenant `auth_tenant_id()` is a latent landmine that must be fixed before any route ever adopts the anon client. |
| R3 | §5 offered "a claim in a short-lived token" as a way to carry the active workspace. | The codebase deliberately does **not** trust JWT `tenant_id` (staleness, per the `auth_tenant_id()` comment), and tokens are Supabase-issued session JWTs the backend cannot stamp a per-switch custom claim onto. | Dropped the JWT-claim option. The active workspace is an **explicit request parameter** (header/path) validated against `workspace_memberships`. |
| R4 | §6 implied the existing accept endpoint can attach an existing identity. | `POST /accept/{token}` (`invitations.py:381`) provisions a **new** auth user and **sets a password** (Strategy 1 updates the pre-created auth user; Strategy 2 does a `sign_up`). It assumes the email has no account, which the 409 guaranteed. Invites also pre-create a Supabase Auth user (`invitation.auth_user_id`). | Existing-identity guest invites need a different path: (a) `create_invitation` must **skip auth-user pre-creation** (the auth user exists), and (b) accept must be an **authenticated** "accept membership" action by the already-logged-in person (insert a membership), NOT the public password-setting flow. The public token-accept path stays only for brand-new emails. (See §6.) |
| R5 | tenant_id representation was left implicit. | `tenants.id` is a UUID; `user.tenant_id` is normally that UUID, with legacy slug tolerance via `get_tenant_uuid` (`tenant_repository.py:59`). | `workspace_memberships.tenant_id` references `tenants(id)` (UUID). Keep `users.tenant_id` as the home anchor (the seat function and `auth_tenant_id()` both read it). |

Net effect: the live-path design gets **simpler** (pure app-layer, no RLS session plumbing), one real correctness gap is closed (the seat gate now exempts guests, in the right phase), and the auth/accept flow for existing identities is specified instead of hand-waved.

---

## 1. Requirements (what this must deliver)

From the client thread (Jake/Audri) and the billing model agreed in conversation:

1. **R1. One identity, many workspaces.** An independent agent keeps their own workspace **and** can be invited into another organization with the same email/login.
2. **R2. Original data stays put.** Joining a team never moves or merges the person's own workspace or its transactions. (Jake/Audri's explicit rule.)
3. **R3. Permission-scoped guest access.** Inside a host org, a guest sees only what their host-org role and assignments allow, and never bleeds their home-org data into the host (or vice versa).
4. **R4. Billing follows the workspace.** A transaction processed inside Org B is Org B's, and Org B's subscription covers it. An invited agent/team-leader/TC does **not** participate in the host org's seat billing; they are a paid seat only in their **home** org.
5. **R5. No lock-out, no orphaning.** The owner of a workspace can never be locked out of it, and leaving a host org never strands data.
6. **R6. Fully UI-testable by non-developers.** A real-estate tester must be able to validate the whole flow (accept an invite to a second org, switch workspaces, see the right data and the right billing) by mouse, with no developer tooling.

---

## 2. Current-state audit (why it is blocked today)

There is a shallow blocker and a deep one. The shallow one is a symptom of the deep one.

### 2.1 The shallow blocker (the visible error)
`create_invitation` rejects any email that already has a user:

```
# app/api/v1/invitations.py:151-157
existing = await user_repo.get_by_email(payload.email)
if existing:
    raise HTTPException(409, "A user with this email already exists.")
```

Removing this line alone would **not** make the feature work; it would corrupt data, because of the deep blocker.

### 2.2 The deep blocker (one user belongs to exactly one tenant)
- `User.tenant_id` is a **single, required column** (`app/models/user.py`). A user has one workspace, full stop.
- There is **no membership table**. A search of `app/models` finds nothing like `user_tenant_memberships`. There is nowhere to record "this person is also a member of Org B."
- The request's tenant is derived from that one column: `get_current_user` loads the user by JWT `sub` and reads `user.tenant_id`; `require_tenant_access` compares `user.tenant_id` to the resource's tenant. So "which org am I acting in" is implicit and fixed per user.
- `MULTI_TENANCY_IMPLEMENTATION_PLAN.md` names this exact limitation as out of scope for v1.

If the 409 were removed and an invite reused the existing user, the accept flow would overwrite that user's single `tenant_id`, yanking them (and the `is_tenant_owner` anchor) out of their own workspace. That is the data-corruption path R2/R5 forbid.

### 2.3 How tenant isolation is actually enforced (verified, and not what rev 1 said)
Every API call site uses the **service-role key** (`get_supabase`, 59 usages), which **bypasses RLS**. The anon-key RLS client (`get_user_supabase`) is used **zero times** in `app/api`/`app/services`. So **RLS is not in the live request path at all**; tenant isolation today is enforced **entirely in the application layer** (explicit `tenant_id` filters plus `require_tenant_access`).

Two consequences for this design:
- **The active-workspace change is purely application-layer.** No per-request Postgres session variable or RLS plumbing is needed for the live path. This is simpler than rev 1 implied.
- **There is no RLS safety net.** A handler that forgets to filter by the active workspace leaks across tenants with nothing behind it. App-layer correctness is therefore load-bearing, which is why §5 concentrates tenant resolution at a single validated choke point. Separately, the RLS resolver `auth_tenant_id()` reads the single `users.tenant_id` (and ignores the JWT by design); it is dormant today but is a latent landmine that must be made membership/active-workspace aware before any route ever switches to the anon client.

### 2.4 The seat model today
`SeatService.staff_seat_count` counts active users whose role is in `BILLABLE_STAFF_ROLES` (Admin, TeamLead, Agent, TransactionCoordinator, Attorney) within a tenant, gated by `tenants.seat_limit` / `plan`. It assumes every billable person lives in exactly one tenant, which is the assumption multi-membership breaks.

---

## 3. The decision

> **Introduce per-user multi-workspace membership using the "guest / outside-collaborator" pattern. A person has exactly one home workspace (which they may own) and zero or more guest memberships in other workspaces. Every authenticated request resolves an explicit active workspace, validated against the caller's memberships; all data access and billing are scoped to that active workspace. Billing follows the workspace: a guest never consumes the host org's paid seat, and the host org's deal-level cost is covered by the host's own plan. The person's home workspace and its data are never moved or merged.**

This is the literal implementation of R1-R6, and it matches how mature multi-tenant SaaS (Slack/Notion guests, GitHub outside collaborators) behave.

### 3.1 The one hinge that must be decided: host billing basis
"Guests don't pay into the host org" is only self-consistent if the host org's billing does not depend on counting people:

- **If host billing stays purely seat-based** (today's model), guests-are-free opens a free-rider hole: a brokerage invites 40 external agents who each run deals while the brokerage pays for 2 seats. Mitigation options: (a) a discounted **"guest seat"** the host pays, or (b) move part of host billing to **per-transaction/usage**.
- **If the host org has a transaction/usage billing component** (the revenue plan's per-transaction platform fee), the model is airtight: cost tracks deals, not headcount.

**Recommendation:** pair "guests are seat-free in the host org" with a usage/transaction billing component for host orgs. Until that exists, the safe interim rule is the **guest seat** (host pays a reduced seat for each external collaborator), so seat pricing still correlates with usage. This is a pricing decision for Jake/Audri (see §11).

---

## 4. Data model

### 4.1 New: `workspace_memberships`
The new source of truth for "who can act in which workspace."

| Column | Purpose |
|---|---|
| `id` | PK. |
| `user_id` | The person (one auth identity). FK to `users(id)`. |
| `tenant_id` | The workspace they are a member of. FK to `tenants(id)` (UUID; `user.tenant_id` is already this UUID, with legacy slug tolerance handled by `get_tenant_uuid`). |
| `role` | Their permission role **in this workspace** (Agent, TeamLead, TC, Attorney, Admin, portal roles). Per-workspace, not global. |
| `membership_type` | `home` or `guest`. Exactly one `home` per user. |
| `account_type` | Optional per-workspace market label (their `home` carries their self-selected account type). |
| `team_id` | Their team within this workspace, if any (replaces the single `users.team_id` for guests). |
| `is_billable_here` | Whether this membership consumes a seat in this tenant. `home` staff = true; `guest` = false (or "guest seat" per §3.1). |
| `invited_via_invitation_id` | Audit link for guest memberships (mirrors today's `joined_via_invitation_id`). |
| `status` | `active`, `suspended`, `left`. |
| `created_at` / `updated_at` | Timestamps. |
| UNIQUE | `(user_id, tenant_id)`. |

### 4.2 What changes on existing tables
- `users.tenant_id` becomes the **home** workspace anchor (kept for back-compat and to identify the home org), but **per-request role/team/tenant come from the active membership**, not from `users.*`. Migrating all reads to the membership is the bulk of the work.
- `users.role` / `users.team_id` effectively become "home-workspace role/team" and stop being the universal answer. New code reads the active membership's `role`/`team_id`.
- `tenant.owner_user_id` (the owner anchor I just built) stays exactly as is: ownership is already per-tenant, so it composes cleanly (see §7).

### 4.3 Backfill
Every existing user gets exactly one `workspace_memberships` row: `membership_type='home'`, `tenant_id=users.tenant_id`, `role=users.role`, `team_id=users.team_id`, `is_billable_here = role in BILLABLE_STAFF_ROLES`. This is a pure derivation, zero behavior change on day one.

---

## 5. The core engineering: active-workspace resolution

This is the heart of the change and the riskiest part. Today "the tenant" is implicit in `user.tenant_id`. Under multi-membership it must become explicit and validated.

1. **Carry an active workspace per request.** The frontend sends the chosen workspace as an **explicit request parameter** (an `X-Workspace-Id` header, or a path segment), defaulting to the user's `home` workspace when absent. Do **not** put the active workspace in the JWT: tokens are Supabase-issued session JWTs the backend cannot re-stamp per switch, and the codebase already deliberately refuses to trust JWT `tenant_id` for authority (the `auth_tenant_id()` comment in migration `20260511094000`). The parameter is untrusted input and is only meaningful after step 2 validates it.
2. **Validate it.** A new dependency (call it `get_active_membership`) loads `workspace_memberships` for `(user_id, active_workspace_id)`; if there is no active membership, reject with 403. This replaces the implicit `user.tenant_id` read.
3. **Derive identity from the membership.** `get_current_user` (or a thin wrapper) sets the request's effective `tenant_id`, `role`, `team_id`, and `is_tenant_owner` from the **active membership** + that tenant's `owner_user_id`, not from the `users` row. Every `require_role` / `require_team_access` / `require_tenant_access` then operates on the active workspace automatically.
4. **App-layer filters are the only enforcement, so they are load-bearing.** Because every route uses the service-role client (RLS bypassed, §2.3), the protection is the explicit `tenant_id` filter (now sourced from the active membership) plus `require_tenant_access`. There is no RLS backstop, so the resolution choke point in steps 2-3 must be the *only* place a request's tenant is decided, and a CI guard should flag any request handler that reads `user.tenant_id` directly instead of the active membership. The dormant `auth_tenant_id()` RLS function is updated (membership-aware) in M4 purely so RLS is correct if a route ever adopts the anon client; it is not relied upon as live defense today.

The win: once identity is sourced from the active membership, the **existing** guards (the ones I extended with the owner anchor this round) keep working unchanged. The work is concentrated at the resolution point, not smeared across every endpoint.

---

## 6. The invite-flow change (the user-visible feature)

`create_invitation` and the accept flow change from "create a brand-new user" to "create a membership."

The existing accept endpoint cannot be reused as-is for an existing identity: `POST /accept/{token}` (`invitations.py:381`) provisions a **new** auth user and **sets a password** (Strategy 1 updates the pre-created `invitation.auth_user_id`; Strategy 2 does a `sign_up`). That is correct for a brand-new email but wrong for someone who already has an account and a password. So the flow forks by whether the email already exists:

- **Invite of an existing identity (`create_invitation`):** when `get_by_email` finds an existing user, **do not 409** and **do not pre-create a Supabase Auth user** (it already exists). Create a pending invitation flagged as a *membership* invite. Keep a 409 only for genuinely conflicting states (an already-active membership in that tenant).
- **Accept of an existing identity:** this is an **authenticated** action, not the public password-setting path. The already-logged-in person (or a person who signs in with their existing password first) accepts, which inserts the `workspace_memberships` row (`membership_type='guest'`, role from the invite, `is_billable_here` per §3.1), marks the invitation used, writes the audit link, and optionally switches their active workspace to the host. No new auth user, no new profile, no password change, no `users.tenant_id` write. The home workspace is untouched.
- **Brand-new emails:** unchanged. The existing `POST /accept/{token}` password-provisioning path runs, and the new user gets a single `home` membership.

This is the smallest change that delivers R1 once §4 and §5 exist beneath it, but it is explicitly **two** accept paths (public-provision for new, authenticated-attach for existing), not one.

---

## 7. Billing rules (R4 made concrete)

Resolving the three policy questions from the conversation:

1. **Does a guest count against the host org's seat cap?** No (per R4). There are **two** places that enforce seats and **both** must change, not just the app-layer one:
   - The authoritative transactional gate is the SQL function `create_invitation_with_seat_check` (migration `20260512095000`), which today counts active staff from `users WHERE tenant_id=host AND role IN(staff)` and counts **every** staff-role pending invite toward the cap. It must be rewritten to count active staff from `workspace_memberships` (home/billable) and to **exclude guest invitations/memberships** from the count, or a host at its seat limit could not invite an existing agent as a guest, and an accepted guest would wrongly consume a host seat. This is a required migration and it must ship **with M2** (the moment existing-user invites become possible), not later.
   - The app-layer mirror `SeatService.staff_seat_count` changes the same way (count `workspace_memberships WHERE tenant_id=host AND is_billable_here=true`, excluding guests).
   - If Jake/Audri choose the "guest seat" pricing option (§3.1) instead of free guests, then `is_billable_here=true` for guests and both counters include them at the guest rate; the structural change is identical, only the flag differs.
2. **What about a guest whose home org is free/trial?** Their home plan covers their home seat; the host covers the **deal** cost. This is exactly why §3.1 recommends a usage/transaction billing component (or a guest seat) for host orgs, so a free-home guest is never unpaid labor in a paid host.
3. **Which workspace owns a guest-created transaction, and bills it?** The **active workspace** at creation time. A guest TC who starts a deal "inside Org B" creates an Org B transaction (`tenant_id = Org B`), billed to Org B. The TC-starts-the-deal flow from the revenue plan slots in here: the TC selects the agent, but the deal lives in (and is billed by) the workspace they are acting in.

Seat accounting therefore stays per-workspace and correct: each person is billable in exactly one workspace (their home), and host orgs pay for deals (and optionally guest seats), never for guests' home seats.

---

## 8. Owner-anchor compatibility (no rework of this round's change)

The owner anchor I shipped this round is **per-tenant** (`tenant.owner_user_id == user.id`), not per-user-global. Under multi-membership it composes cleanly:

- A person is the **owner** of their home workspace (full authority there via the existing B1-B11 / F1-F4 guards).
- In a host workspace they are a **plain member** with their host role; `is_tenant_owner` is computed against the **active** workspace's `owner_user_id`, so it is correctly `false` there.
- The "Workspace owner" affordance and Owner badge I added render based on the active membership, so they appear only in the workspace the person actually owns.

Nothing built this round needs to be undone; it was deliberately anchored on ownership rather than the role label for exactly this reason.

---

## 9. UI / UX (must be testable by real-estate professionals)

Mouse-first, low-typing, honest, consistent with the existing chrome:

- **Workspace switcher.** A control in the sidebar header (next to the brand lockup) listing the person's workspaces with their role in each ("Hearthstone Realty - Owner", "North Side Team - Agent"). One click switches the active workspace; the whole app re-scopes. This is the single most important testable surface.
- **Active-workspace clarity.** The current workspace name + the person's role in it are always visible, so a tester never wonders which org they are acting in.
- **Guest indicator.** A small "Guest" chip when the active membership is `guest`, so it is obvious this is not their own workspace.
- **Invite that "adds" not "blocks".** When an admin invites an email that already exists, the UI says "We'll add them to your workspace" rather than erroring, and the recipient gets an "accept" that lands them in the host workspace with a switcher back to their own.
- **Billing honesty.** Each workspace's billing page shows only that workspace's seats and plan; a guest membership shows "Billed by your home workspace" so there is no confusion about who pays.

UI-testability check: a tester can (1) own a solo workspace, (2) accept an invite to a team with the same login, (3) switch between the two, (4) confirm each shows only its own deals, (5) confirm the team's billing does not count them as a seat. All by mouse.

---

## 10. Phasing (so slices are shippable and testable on their own)

| Phase | Deliverable | Testable outcome |
|---|---|---|
| **M0** | `workspace_memberships` table + backfill (one `home` row per existing user). Reads still come from `users.*`. | Zero behavior change; pure data foundation, regression-safe. |
| **M1** | Active-workspace resolution: identity (`tenant_id`/`role`/`team_id`/`is_tenant_owner`) sourced from the active membership instead of `users.*`, defaulting to home. | Existing single-workspace users behave identically; the plumbing is in place. |
| **M2** | Invite-an-existing-email creates a guest membership (§6, the two-path accept) + the workspace switcher UI (§9) + **the seat-gate exemption for guests in `create_invitation_with_seat_check` and `SeatService`** (§7 R1). The seat change is part of M2, not optional, because existing-user invites flow through the seat gate the moment they are enabled. | The headline feature: an independent agent accepts a team invite and switches workspaces, and inviting them never trips the host's seat cap. |
| **M3** | Host billing policy from §3.1 (guest-seat rate or usage/transaction component) + guest indicators + per-workspace billing copy. | Host billing is economically correct, not just seat-cap-correct. |
| **M4** | RLS policy update (membership-aware) on the anon path; audit events for join/leave; "leave workspace" flow that never orphans data. | Defense-in-depth and lifecycle complete. |

M0 and M1 are invisible and safe; the user-visible feature lands at M2. Pricing decisions (§3.1) gate M3 but not M0-M2.

---

## 11. Open questions for Jake / Audri (decisions needed before M3)

1. **Host billing basis.** Guest-seat (host pays a reduced seat per external collaborator) vs usage/transaction billing (host pays per deal)? This is the §3.1 hinge and the only thing that makes "guests don't pay into the host" airtight.
2. **Who may invite an existing identity?** Same grant rules as inviting a new user (Admin/owner/TeamLead per the existing cap), or stricter for cross-org adds?
3. **Can a guest be promoted to a billable home-style member of the host** (i.e. actually leave their solo workspace and become staff)? That is a separate "transfer" flow on top of this; R2 says the default is keep-both.
4. **Portal roles (Client/FSBO/Vendor) and multi-membership.** Do those ever need it, or is multi-membership staff-only (Agent/TeamLead/TC/Attorney) for now? Recommend staff-only first.

---

## 12. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| A query keeps reading `users.tenant_id` and leaks across the active workspace | Medium | M1 centralizes identity at the resolution point; add a lint/test that flags direct `user.tenant_id` reads in request handlers; M0/M1 ship behind a flag with the old path intact. |
| Free-rider: guests run deals in a host that pays for few seats | Medium | §3.1 host-billing rule (guest seat or usage billing); §7 seat math excludes guests explicitly. |
| Cross-workspace data bleed (home data visible in host) | High if rushed | There is **no RLS backstop** in the live path (§2.3), so the mitigation is structural: a single validated active-workspace choke point (§5) + a CI guard flagging direct `user.tenant_id` reads in handlers; the UI guest indicator makes mis-scoping visible in testing. The RLS update (M4) hardens only the currently-dormant anon path. |
| Seat gate blocks or mis-bills guest invites | Medium | The DB function `create_invitation_with_seat_check` and `SeatService` are both made guest-aware in M2 (§7 R1), so existing-user invites neither trip the host cap nor silently consume a seat. |
| Owner accidentally locked out after joining a host | Low | Ownership is per-tenant and untouched (§8); the person remains owner of their home workspace regardless of guest memberships. |
| Scope explosion | High | Strict phasing (§10); M0/M1 are invisible and safe; the feature is flag-gated; pricing-dependent work (M3) is isolated. |

---

## 13. Out of scope (explicitly not in this plan)
- Self-service Stripe billing / charging (modelling only; the revenue plan owns charging).
- The full vendor-organization / partner-code monetization (separate plan).
- Account **merge** (combining two existing identities into one) - this plan is about one identity holding many memberships, not merging two identities.
- SSO / SAML.
- Tenant-scoped encryption keys.

---

## 14. Bottom line
The feature is possible and the model the client described (guest access, billing follows the workspace, seats are home-org) is the right one. The work is not the line that throws the 409; it is (1) a `workspace_memberships` table, (2) sourcing per-request identity from an explicit active workspace instead of the user's single `tenant_id`, and (3) a host-billing rule that keeps seat pricing honest when guests are free. Phasing M0-M1 lands invisibly and safely; the headline "independent agent joins a team" feature lands at M2; and nothing built in the owner-anchor round this week needs to be undone to get there.
