# Sign-up Account-Type / Role Selection and Onboarding Remediation Plan

**Author:** Jan Froben
**Date:** 2026-06-15 (rev 2, after a full workflow/logic review against source)
**Status:** Plan only. No source code changed in this document.
**Flag:** `ve_signup_role_selection_v1` (new, default off until UI sign-off)

**Rev-2 note:** rev 1 was reviewed end-to-end against the live frontend and backend. The review found five concrete flaws that would have broken tester flows: (a) the original plan only patched backend route guards and missed that the **frontend** route guards (`ProtectedRoute`, `RoleRoute`) and the **invite grant** checks (`inviteableRolesFor`, `create_invitation`) are also role-gated, so a non-Admin owner would be bounced from their own management screens; (b) a self-sign-up **Vendor / FSBO / Attorney** founder lands on a portal that assumes someone invited them, producing an honest-but-dead-end screen (FSBO literally says "your coordinator will help you add your first property") and, for Vendor, a broken upload that targets a null transaction; (c) the `vendor_category` storage mechanism the plan named does not exist (`create()` has no such argument and the `profile_settings_json` whitelist rejects the key); (d) the onboarding wizard has no local role state, so the "editable dropdown reuses existing plumbing" claim was only half true; (e) `is_tenant_owner` would read `False` on login/refresh because those responses are built on a freshly loaded row. All five are corrected below.

**Source reviewed:** `RegisterPage.tsx`, `OnboardingWizard.tsx`, `useOnboarding.ts`, `useInvitations.ts`, `dashboardShellConfig.ts`, `App.tsx`, `ProtectedRoute.tsx`, `RoleRoute.tsx`, `formatters.ts`, `pages/vendor/VendorDocumentPortalPage.tsx`, `pages/fsbo/FsboOverviewPage.tsx`; backend `auth_service.py`, `api/v1/users.py`, `api/v1/onboarding.py`, `api/v1/invitations.py`, `api/v1/dashboard_role.py`, `core/auth.py`, `models/enums.py`, `services/seat_service.py`, `services/payments_aggregator.py`, `repositories/user_repository.py`, `schemas/onboarding.py`; plus `FRONTEND_UI_WORKFLOW_LOGIC.md §2.1 / §3.1`.

---

## 0. What Jake asked for

From the testing note (account creation, Step 1 / Step 2), Jake raised four concrete items plus one direction-setting discussion:

1. **Account type defaults to "Admin" with no choice.** A user should pick their account type at sign-up from: Agent, Team Leader, Attorney, For Sale by Owner, Transaction Coordinator, Mortgage Vendor, Title Vendor. (Broker / Brokerage is manual, later, explicitly **not** MVP.)
2. **Phone masking dropped a digit / prepended country code "1".**
3. **Role auto-assigned to Admin and locked on Step 2.** A user should be able to change it on Step 2, except when the role was system-assigned through a transaction (vendor/client added to a deal), which stays locked.
4. **Company / Brokerage typed at sign-up did not carry into Step 2.**

Plus the thread where Jake and I aligned on the future **vendor-organization / monetization** model and on **treating the Transaction Coordinator as a vendor role**, both of which Jake called **post-MVP**, asking me only to keep the foundation pointed the right way. In that same thread I flagged the unresolved question this plan must now answer cleanly: "a self-sign-up with no organization yet has nowhere to be a Title Vendor."

---

## 1. Current-state audit (grounded in source)

### 1.1 Already fixed in the working tree (items 2 and 4)
- **Phone (item 2):** `toNationalPhoneDigits()` strips a leading country-code "1" from an 11-digit string before capping at 10; both `RegisterPage` and onboarding route through it. Jake's failure cannot recur.
- **Company carry-over (item 4):** `AuthService.register()` seeds `registrant_company` from `organization_name` into `company_name`; `OnboardingWizard` hydrates Step 2 from `user.company_name`.

These need UI verification only (Phase 0), not new logic.

### 1.2 Still open
- **Item 1:** `RegisterPage` has no role field; `AuthService.register()` hardcodes `registrant_role = UserRole.ADMIN`; the register schema marks `role` "accepted but ignored."
- **Item 3:** `OnboardingWizard` renders role read-only and `CompanyProfileUpdate` had `role` removed.

### 1.3 Doc / code divergence
`FRONTEND_UI_WORKFLOW_LOGIC.md §2.1` (line 440) still documents an **editable** Step 2 role dropdown that "rebuilds the step list live" and persists via `PATCH /onboarding/company (company, role)`. The code diverged (locked it) citing owner-protection. So Jake's request is mostly **restoring documented behavior, done safely.**

### 1.4 The owner == Admin invariant
Self-registration provisions a fresh tenant, sets the registrant to Admin, and records `tenant.owner_user_id`. Authority is enforced through `role == Admin` in **213 occurrences across 60 files**. `PUT /users/{id}/role` locks the owner's role, which today also blocks the owner from changing **their own** role (exactly what Step 2 needs).

### 1.5 Per-role experience already renders, but not every role can *act* (the dead-end finding)
`getLandingRoute(user)` and `App.tsx` already route every role to a working shell. But "renders" is not "works end-to-end." By MVP capability a self-sign-up founder splits into two tiers:

- **Self-operating (full MVP workflow as a solo owner): Agent, Team Leader, Transaction Coordinator.** They can open the New Transaction wizard, run deals, manage the workspace. `INTERNAL_ROLES` in `App.tsx` = `[Agent, TransactionCoordinator, TeamLead, Admin]`.
- **Connected / portal (designed to be brought *into* a deal by someone else, no self-serve MVP workflow): Attorney, For Sale by Owner, Mortgage/Title Vendor.**
  - **FSBO** overview empty state literally reads "Your coordinator will help you add your first property." There is **no** self-serve "create my listing" path, and FSBO is not in `INTERNAL_ROLES`, so the New Transaction wizard is gated off.
  - **Vendor** portal (`VendorDocumentPortalPage`) is built for an invited vendor responding to requests. With no deals there is nothing to respond to, and its single action posts an upload with `transactionId: null` (a broken submit).
  - **Attorney** is excluded from `INTERNAL_ROLES`, so an attorney owner cannot self-create a matter through the wizard; their dashboard is matter-driven and arrives empty.

This is the central workflow flaw: a tester who signs up as Vendor/FSBO/Attorney would hit an honest-but-empty dead-end, the exact "end-to-end breaks down" failure. Section 5 fixes it.

### 1.6 Authority is gated in MANY places, including the frontend (the missed-surface finding)
Rev 1 assumed patching backend `require_role` was "the large majority." A full trace shows owner authority must be honored at a specific, enumerable set of choke points on **both** ends, several of which rev 1 missed entirely:

- **Frontend `ProtectedRoute`** (`hasMinimumRole(user.role, requiredRole)`) gates Team and Admin/* surfaces at `requiredRole="TeamLead"`. An Agent/TC/Vendor/FSBO owner fails the hierarchy and is sent to `/unauthorized`.
- **Frontend `RoleRoute`** is a strict `allowedRoles.includes(user.role)` with no hierarchy and no owner bypass. Several admin surfaces use it with internal-only role lists.
- **Frontend `inviteableRolesFor(role)`** returns `[]` for Vendor/FSBO/Attorney (no case), so an owner in those roles sees no one to invite.
- **Backend `create_invitation`** is `require_role(AGENT, TEAM_LEAD, ADMIN)` plus an inline grant check `role_has_permission(current_user.role, payload.role)` for privileged roles. A non-Admin owner fails the grant check.
- **Backend inline service checks** that special-case Admin: `payments_aggregator.py` (lines 44, 282, 294), `payment_access_service.py:71`, `suggestion_engine.py:646`, `fsbo_workspace.py:340`, and `core/auth.py` (`require_team_access`, `list_accessible_transaction_ids`, `require_transaction_access`).

Section 3 turns this into a closed checklist so none is missed.

### 1.7 Storage and wiring realities the plan must respect
- `UserRepository.create(...)` accepts no `profile_settings_json` argument; `update_profile_settings` rejects any key not in `ALLOWED_PROFILE_SETTINGS_KEYS` (which does **not** include `vendor_category`). So the rev-1 storage path for `vendor_category` would 400 / silently no-op.
- `OnboardingWizard` derives `effectiveRole` from `user.role` only; `buildSteps` is memoized on it; `ProfileStep` receives no role setter. There is **no** local role state today. The clamp effect is vestigial.
- Login/refresh build `UserResponse.model_validate(profile)` on a freshly loaded `User` (where a transient `is_tenant_owner` defaults `False`). It must be computed in those builders, not only in `get_current_user`.

---

## 2. The decision

> **A self-registration founder picks their professional role at sign-up and may change it on Step 2. The founder is always the Owner of their workspace. "Owner" is a single, explicit authority anchor (`is_tenant_owner`) honored at every role-gated choke point on both tiers of the stack, so the Owner keeps full workspace-management power regardless of the professional role label and can never be locked out. No self-sign-up role may be a broken dead-end: connected/portal roles get honest empty states plus the Owner affordance (which lets them invite an Agent and generate real work), with their full self-serve workflow explicitly post-MVP.**

This is the literal implementation of what I told Jake ("let them self-label their role, with the founder/owner protected so they can't lock themselves out"), corrected so it actually holds end-to-end.

**Account-type to role mapping (single source of truth for both screens):**

| User-facing account type | Stored `role` | Extra | MVP tier |
|---|---|---|---|
| Agent | `Agent` | - | Self-operating |
| Team Leader | `TeamLead` | - | Self-operating |
| Transaction Coordinator | `TransactionCoordinator` | - | Self-operating |
| Attorney | `Attorney` | - | Connected (honest empty state) |
| For Sale by Owner | `ForSaleByOwner` | - | Connected (honest empty state) |
| Mortgage Vendor | `Vendor` | `vendor_category = "mortgage"` | Connected (honest empty state) |
| Title Vendor | `Vendor` | `vendor_category = "title"` | Connected (honest empty state) |

Notes:
- **Admin and Client are intentionally not self-sign-up choices** (matches Jake's list). Owner authority comes from ownership, not the Admin label; Clients only ever enter via a transaction invite.
- **Mortgage/Title Vendor** collapse to `Vendor` + a category, exactly as I described to Jake. For MVP the category is stored by **adding `vendor_category` to `ALLOWED_PROFILE_SETTINGS_KEYS`** and writing it through the existing settings path (see 4.1D); no migration. The first-class column is part of the post-MVP foundation (section 8).
- **TC stays a staff role for MVP.** Reclassifying it as a vendor is post-MVP (8.4).
- **Connected-tier founders are fully testable** (no crash, no broken button) and use the existing, already-working invitation/transaction path to exercise their *inbound* workflow; their self-serve workflow (FSBO self-listing, vendor-org connection) is post-MVP.

### 2.1 Alternatives considered
- **Cosmetic label only (founder stays Admin; account type is display + onboarding personalization).** Lowest risk and zero dead-ends, but it does not let a tester sign up as an Agent/FSBO/Vendor and see that role's surface, which is the point. Rejected, but retained as the documented fallback if the owner-anchor surface (section 3) is judged too large for this cycle.
- **Narrow MVP to self-operating roles only (Agent/TeamLead/TC self-own; Attorney/FSBO/Vendor invite-only for now).** Removes most of the dead-end and owner-bypass surface. Rejected as the default because Jake explicitly listed all seven, but flagged as the high-confidence de-risking option (see section 9).
- **Store the role with no authority anchor.** The trap that locks a non-Admin owner out of their own org. Rejected.

---

## 3. Owner-authority choke-point inventory (the closed checklist)

`is_tenant_owner` is computed once and honored at exactly these points. Implementation must touch every row; the prior plans broke because this list was implicit.

**Backend**
| # | Location | Change |
|---|---|---|
| B1 | `core/auth.py: get_current_user` | Compute `user.is_tenant_owner = tenant is not None and tenant.owner_user_id == user.id` (tenant already loaded for non-platform-admins). |
| B2 | `core/auth.py: require_role` | Short-circuit `if current_user.is_tenant_owner: return current_user`. Covers all `require_role(ADMIN)` route guards. |
| B3 | `core/auth.py: require_team_access` | `if user.role == ADMIN or user.is_tenant_owner: return`. |
| B4 | `core/auth.py: list_accessible_transaction_ids` | Treat owner like Admin/TeamLead (return `[]`). |
| B5 | `core/auth.py: require_transaction_access` | `if user.role in (ADMIN, TEAM_LEAD) or user.is_tenant_owner: return`. |
| B6 | `api/v1/users.py: change_user_role` | Block only when `owner_user_id == user_id AND current_user.id != user_id AND not is_platform_admin` (owner may change self; nobody else may change the owner). |
| B7 | `api/v1/invitations.py: create_invitation` grant check (line 132) | `... and not (role_has_permission(current_user.role, payload.role) or current_user.is_tenant_owner)`. |
| B8 | `services/payments_aggregator.py` (44, 282, 294) | Add `or user.is_tenant_owner` to the Admin clauses (esp. the tenant-scope gate at 44). |
| B9 | `services/payment_access_service.py:71` | Owner clause on the Admin check. |
| B10 | `services/suggestion_engine.py:646`, `services/fsbo_workspace.py:340` | Owner clause (low impact; included for completeness so a non-Admin owner is never narrowed). |
| B11 | Token builders (`auth_service.register`, `_build_token_response`, login, refresh) | Set `profile.is_tenant_owner` before `UserResponse.model_validate(profile)` so the flag is correct at login, not just on later `/me`. |

Explicitly **do not** add an owner bypass to `require_exact_roles` (the role-specific dashboards). An owner labeled FSBO passes the FSBO dashboard naturally; an owner labeled Agent must correctly *not* reach the FSBO dashboard endpoint. Keeping this strict is what makes the routing coherent.

**Frontend**
| # | Location | Change |
|---|---|---|
| F1 | `components/ProtectedRoute.tsx` | `if (requiredRole && user && !hasMinimumRole(user.role, requiredRole) && !user.is_tenant_owner)`. Safe: `ProtectedRoute requiredRole` is used only for "minimum role" management gating, never identity dashboards. |
| F2 | `components/RoleRoute.tsx` | Add optional `ownerBypass?: boolean`. When true, `allowedRoles.includes(user.role) || user.is_tenant_owner` passes. Apply `ownerBypass` **only** on management/admin routes, never on identity dashboards/portals. |
| F3 | `hooks/useInvitations.ts: inviteableRolesFor` | If the caller is the owner, return the Admin set regardless of role. |
| F4 | `layouts/AppLayout.tsx` | Render the "Workspace owner" affordance + Owner badge when `user.is_tenant_owner`; its links target F1/F2-bypassed routes. |

`is_tenant_owner` must be added to `UserResponse` (backend) and the `User` type (frontend) so every guard above can read it.

---

## 4. MVP implementation

### Phase 0 - Verify the two landed fixes (no product code)
- UI-confirm the phone keeps 10 digits when "1" is autofilled, and Company pre-fills on Step 2.
- Add a frontend unit test (`toNationalPhoneDigits("1 (555) 123-4567") === "5551234567"`) and a backend test (`register(organization_name="Acme")` sets `company_name="Acme"`). Tests are not product source.

### Phase 1 - Backend: owner anchor + role at sign-up
**1A. Owner anchor.** Implement B1-B11 from section 3. Add transient `is_tenant_owner: bool = False` to the `User` dataclass and to `UserResponse`.

**1B. Honor `role` at registration (constrained).**
- In `UserRegisterRequest`, promote `role` to validated-optional and add `vendor_category: Literal["mortgage","title"] | None`.
- Define `SELF_SIGNUP_ROLES = {Agent, TeamLead, TransactionCoordinator, Attorney, ForSaleByOwner, Vendor}`; reject `Admin`/`Client` with 422.
- In `AuthService.register()`: `registrant_role = payload.role if payload.role in SELF_SIGNUP_ROLES else UserRole.AGENT` (default Agent, never silent Admin). **Keep `tenant.owner_user_id = supabase_user_id` regardless of role** (authority rides on ownership). Continue seeding `company_name` from `organization_name`.

**1C. `vendor_category` storage (corrected).** Add `"vendor_category"` to `ALLOWED_PROFILE_SETTINGS_KEYS` in `user_repository.py`. After `create()`, when `role == Vendor`, persist it via `update_profile_settings(user_id, {"vendor_category": payload.vendor_category})`. (Do not pass it to `create()`, which has no such field.) `UserResponse` already exposes `profile_settings_json`, so the frontend can read it back.

**1D. Owner-aware seat math.** `BILLABLE_STAFF_ROLES` excludes Vendor/FSBO/Client. Have `SeatService.staff_seat_count` always count the Owner as one occupied staff seat so a Vendor/FSBO owner does not read "0 of N." When the **owner changes their own role** (Step 2 or later), **skip the billable-seat gate** (they are entitled to their own seat); the gate still runs for inviting/adding other people.

**1E. Re-enable role on the onboarding company endpoint (restores `§2.1`).**
- Re-add `role` (+ `vendor_category`) to `CompanyProfileUpdate`.
- In `PATCH /onboarding/company`, when `role` is present: enforce `SELF_SIGNUP_ROLES`; **refuse** when the role was system-assigned (block if `user.joined_via_invitation_id is not None` or the user has any active `transaction_vendor_assignment` / client party link, per Jake's exception); apply via the same repo path as `change_user_role`, skip the seat gate for the owner-self case, and write the `user_role_changed` audit entry. The endpoint already runs under `get_current_user`, so a founder can call it; the owner-lock refinement (B6) lets the owner relabel.

### Phase 2 - Frontend Step 1: "I am a..." dropdown (RegisterPage)
- New shared `utils/accountTypes.ts`: `ACCOUNT_TYPES = [{label, role, vendorCategory?}]` in Jake's exact order, default **Agent**. Used by Step 1 and Step 2.
- Add a single `@/components/ui/select` labeled **"I am a..."** under Full name (reuse `InviteUserModal` styling). Mouse-only.
- Helper: "This sets up your workspace for how you work. You can change it on the next screen."
- Send `role` (+ `vendor_category` for vendor types) in `UserRegisterRequest`; remove the stale "role is ignored" comment.

### Phase 3 - Frontend Step 2: editable role dropdown (OnboardingWizard), wired correctly
- **Introduce local state** `const [selectedRole, setSelectedRole] = useState<UserRole>(user?.role ?? 'Agent')` and a `vendorCategory` companion. Change `effectiveRole` to derive from `selectedRole` (falling back to `user.role`), so `buildSteps`, `isInternalRole`, and the existing clamp effect all react live. Hydrate `selectedRole` from `user.role` (+ `vendor_category`) in the existing user-hydration effect.
- Replace the read-only role box in `ProfileStep` with a `Select` from `ACCOUNT_TYPES`; pass `selectedRole`/`setSelectedRole`. Restore the hint: "You'll be updated to this role after this step."
- In `advance()` for the profile step: include `role` (+ `vendor_category`) in the `PATCH /onboarding/company` body; **change the company-payload gate** from `isInternalRole && !isInvitee` to `!isInvitee` so a Vendor/FSBO owner can also save a company name.
- **Lock only when warranted:** if `user.joined_via_invitation_id` is set (or the backend flags the role as system-assigned), render the read-only box with the existing "ask a tenant admin" helper. Self-sign-up founders get the editable dropdown.

### Phase 4 - Frontend owner-bypass + Owner affordance (no lock-out)
- Implement F1-F4 from section 3.
- In `AppLayout`, when `user.is_tenant_owner`, always render a compact **"Workspace owner"** entry (orange shield/crown chip) opening Team, Settings, Billing, and Invite, plus an **Owner** badge next to the role label. Because FSBO and Vendor render inside `AppLayout`, this is **one** place (no separate portal shells; Client uses `ClientWorkspaceLayout` but Client is not self-sign-up).
- This is what turns a connected-tier owner from "stuck" into "can invite an Agent and generate real deals," so no role is a dead-end.

### Phase 5 - Honest connected-role landings + concrete fixes (no dead-ends)
- **Vendor portal (`VendorDocumentPortalPage`):** guard the upload so it is disabled (or routes to "no open requests yet") when there is no `upload_requests[0].transaction_id`, instead of posting `transactionId: null`. Add an honest empty-state line: "Vendors connect to deals when an agent shares a code or adds you to a transaction. Full vendor-organization tools are coming soon." Owner affordance remains visible.
- **FSBO overview (`FsboOverviewPage`):** the "your coordinator will help you add your first property" copy is wrong for a self-sign-up FSBO owner. For MVP, change the empty-state copy to an owner-honest message and point the primary CTA at the Owner affordance ("invite a coordinator/agent" or "start a property" once self-listing exists). True FSBO self-serve listing creation is scoped as a fast-follow (section 9), not assumed here.
- **Attorney dashboard:** confirm it shows an honest empty state for an owner with no matters; attorney self-serve matter creation is out of scope.
- All three remain fully UI-testable: no crash, no broken button, honest messaging, reachable management.

### Phase 6 - Profile / AccountModal consistency
- Identity edits live in the shared `AccountModal` (the `/profile` route redirects to `/analytics?scope=me`). Surface the role + **Owner** badge there, and allow the owner to relabel later through `PUT /users/{id}/role` (owner-self-allowed via B6, seat gate skipped per 1D). This satisfies Jake's "maybe they didn't change it on the account screen, this will help us help them" after onboarding too.
- Admin-changes-others already works (`ManageTeamMembersPanel -> PUT /users/{id}/role`); confirm a non-Admin owner reaches it via Phase 4.

---

## 5. UI / UX and visual design
- **Reuse, do not reinvent.** Both dropdowns use `@/components/ui/select` (same as `InviteUserModal`): consistent type scale, `border-[1.5px] border-ve-border`, `focus:border-ve-orange`, radius, focus ring.
- **Mouse-first, minimal typing.** One click from a fixed list on both screens; defaults to Agent so doing nothing still yields a sensible non-Admin role.
- **Onboarding aesthetic unchanged.** Dropdown drops into the existing split-panel shell (dark `ve-sidebar`, serif headings, `font-mono` kickers, orange accent). No layout rework.
- **Professional-tool feel.** The "Workspace owner" chip reuses the orange-accent shield/pill motif from the onboarding privacy card and invite-modal header.
- **Honest empty states** (no mock data) for connected-tier owners, consistent with the no-demo-data rule; the empty state + Owner affordance is the intended first impression.

---

## 6. MVP capability by role (so testers know what "done" looks like)

| Account type | Lands on | Can do in MVP as a solo owner | Inbound workflow tested via |
|---|---|---|---|
| Agent | `/dashboard/agent` | Create/run deals, manage workspace, invite | Self-serve |
| Team Leader | `/dashboard/team` | All of Agent + team management | Self-serve |
| Transaction Coordinator | `/dashboard/agent` or `/dashboard/team` | Coordinate/run deals, manage workspace | Self-serve |
| Attorney | `/dashboard/attorney` | Manage workspace (Owner affordance); honest empty matter list | Invite an Agent who routes a closing matter |
| For Sale by Owner | `/fsbo` | Manage workspace; honest empty state | Invite an agent/coordinator (self-listing = fast-follow) |
| Mortgage / Title Vendor | `/portal/vendor` | Manage workspace; honest empty portal | Be added to a deal / share a code (post-MVP org) |

---

## 7. End-to-end UI test script (non-developer testers, flag on)

**T1 - Agent sign-up.** New "I am a..." defaults to Agent. Phone `1 (317) 555-0142` shows `(317) 555-0142`. Company "Hearthstone Realty" pre-fills on Step 2. Finish → Agent dashboard + "Workspace owner" chip.

**T2 - Fix it on Step 2.** Sign up Agent; on Step 2 switch to **Title Vendor**; confirm the stepper reshapes and the hint shows; finish → Vendor portal with the honest empty state and the Owner chip (no lock-out).

**T3 - Each type renders.** Repeat for Team Leader, TC, Attorney, FSBO, Mortgage Vendor, Title Vendor; confirm each lands on the right surface with the Owner chip and an honest empty state where applicable.

**T4 - Owner cannot lock themselves out (frontend bypass).** As the Title Vendor owner, click "Workspace owner" → Team, Settings, Billing all open (not `/unauthorized`).

**T5 - Owner can actually invite (grant bypass).** As an Agent owner AND as a Vendor owner, open Invite, confirm staff + portal roles are listed, send an invite to an Agent, confirm it sends (no "only an Admin can grant" error).

**T6 - System-assigned role stays locked.** Create a deal as an Agent owner, add a Title vendor by email; that vendor accepts and reaches Step 2; confirm the role field is read-only with the "ask a tenant admin" helper.

**T7 - Vendor action is not broken.** As a Vendor owner with no requests, confirm the upload control is disabled/redirected (no null-transaction submit) and the empty-state copy explains how vendors connect.

**T8 - Admin-style management persists.** As any owner, change an invited teammate's role; confirm it persists and the audit log shows `user_role_changed`.

---

## 8. Post-MVP foundation (do NOT build now)
- **8.1 Vendor companies as real organizations** on the same `tenant` primitive; the MVP `vendor_category` seeds the org category.
- **8.2 Auditable cross-org link** from a transaction to an outside vendor org plus the code that created it; keep vendor identity reference-able, never collapse to free text.
- **8.3 Vendor-owned codes (many-to-many) + fee split**: an agent holds many codes, one per vendor partner; each code is vendor-owned and revocable; per deal the agent picks which vendor applies; billing per organization; AI Coaching reports deal counts back to vendors.
- **8.4 TC as a vendor role**: same wizard slot as title/mortgage vendor; agent-adds-TC and TC-starts-the-deal flows; TC no longer consumes a staff seat or sits on a team. Deferred so MVP keeps TC as staff.
- **8.5 "Leave my workspace and join a brokerage"** (Jake's item B), data/transactions stay with the original account. Nothing here blocks it.
- **8.6 FSBO self-serve listing creation** (fast-follow): the cleanest way to make FSBO a true self-operating role.

---

## 9. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| An owner-authority choke point is missed, locking a non-Admin owner out | Medium | Section 3 is a closed checklist (B1-B11, F1-F4); T4/T5/T8 exercise the management paths directly. |
| Connected-tier (Vendor/FSBO/Attorney) self-sign-up is a dead-end | Medium | Phase 5 honest empty states + concrete fixes + Owner affordance; section 6 sets tester expectations; T3/T7 validate. |
| Scope larger than a single cycle | Medium | Fallback options in 2.1: ship cosmetic-label-only, or narrow self-sign-up to self-operating roles (Agent/TeamLead/TC) and keep Attorney/FSBO/Vendor invite-only. Either removes most of section 3 and Phase 5. |
| `vendor_category` lost | Low | Add to `ALLOWED_PROFILE_SETTINGS_KEYS`; write via `update_profile_settings` (corrected from rev 1). |
| `is_tenant_owner` wrong at login | Low | B11 sets it in every token builder, not only `get_current_user`. |
| Wizard role switch falls off the end | Low | Local `selectedRole` drives `buildSteps`; existing clamp effect handles shrink; T2 verifies. |
| Public form mints Admin/Client | Low | Server-side `SELF_SIGNUP_ROLES` 422. |
| Non-billable owner skews seats | Low | 1D counts the owner as a seat; owner self-role-change skips the seat gate. |

---

## 10. File-by-file checklist

**Backend**
- `app/models/user.py` - transient `is_tenant_owner`.
- `app/core/auth.py` - B1-B5.
- `app/api/v1/users.py` - B6; expose `is_tenant_owner` on `/me`.
- `app/api/v1/invitations.py` - B7 grant-check owner clause.
- `app/services/payments_aggregator.py`, `payment_access_service.py`, `suggestion_engine.py`, `fsbo_workspace.py` - B8-B10 owner clauses.
- `app/services/auth_service.py` - constrained `role`, default Agent, keep owner write, `vendor_category` via settings, B11 token builders.
- `app/services/seat_service.py` - 1D owner-seat + skip gate on owner self-change.
- `app/repositories/user_repository.py` - add `vendor_category` to the whitelist.
- `app/schemas/user.py` - validated `role` + `vendor_category` on register; `is_tenant_owner` on `UserResponse`.
- `app/schemas/onboarding.py` - re-add `role` (+ `vendor_category`) to `CompanyProfileUpdate`.
- `app/api/v1/onboarding.py` - 1E role change with system-assigned guard + audit + seat-gate skip.

**Frontend**
- `src/utils/accountTypes.ts` (new) - shared `ACCOUNT_TYPES`.
- `src/pages/auth/RegisterPage.tsx` - "I am a..." Select; send `role`/`vendor_category`.
- `src/pages/auth/OnboardingWizard.tsx` - local `selectedRole` wiring; editable Select; role in company PATCH; company for all owners; lock only for system-assigned.
- `src/components/ProtectedRoute.tsx` - F1.
- `src/components/RoleRoute.tsx` - F2 `ownerBypass`; apply on management routes in `App.tsx`.
- `src/hooks/useInvitations.ts` - F3 owner-as-Admin invite set.
- `src/layouts/AppLayout.tsx` - F4 Owner affordance + badge.
- `src/pages/vendor/VendorDocumentPortalPage.tsx` - Phase 5 upload guard + honest empty state.
- `src/pages/fsbo/FsboOverviewPage.tsx` - Phase 5 owner-honest empty copy/CTA.
- `src/components/account/*` (AccountModal) - Phase 6 role + Owner badge.
- `src/hooks/useOnboarding.ts` + `src/types/api.ts` - widen `CompanyProfileUpdate` / `UserRegisterRequest` / `User` (`role`, `vendor_category`, `is_tenant_owner`).

**Docs**
- `FRONTEND_UI_WORKFLOW_LOGIC.md §2.1 / §3.1` - reconcile the restored editable-role behavior, the system-assigned lock exception, and the Owner affordance.

---

## 11. Out of scope
- Vendor organizations, codes, fee-splitting, monetization (8.1-8.3).
- TC-as-vendor reclassification (8.4).
- "Leave my workspace and join a brokerage" (8.5).
- FSBO self-serve listing creation beyond the honest empty state (8.6 fast-follow).
- Brokerage / Broker manual setup (not MVP).
- Any change to how invited (non-founder) users receive their role.
