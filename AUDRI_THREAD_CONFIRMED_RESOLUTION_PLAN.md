# Audri Thread: Confirmed-Issue Resolution Plan (Next Test Round)

**Author:** Jan Froben
**Date:** 2026-06-17 (rev 2: corrected after a second, deeper end-to-end source review; see §0.5)
**Status:** Plan only. No source code changed in this document.
**Flags:** `ve_signup_role_selection_v1` (signup roles, default off until UI sign-off), `ve_ai_cost_metering_v1` (AI cost read-out, default off).
**Supersedes / refines:** `SIGNUP_ROLE_SELECTION_AND_ONBOARDING_REMEDIATION_PLAN.md` (rev 2, 2026-06-15). That plan assumed all 7 account types self-register at once. The Audri thread has since **confirmed the narrower Option B**, so this plan keeps rev-2's owner-anchor analysis but scopes the first build to the three self-operating roles and phases the rest.

---

## 0. How I built this plan (grounding)

I reviewed, against the live tree, every surface this plan touches before writing a line of it, because the recurring failure in past plans was drafting without confirming the code actually supports the workflow end-to-end.

**Docs reviewed:** the Audri thread (this conversation), `SIGNUP_ROLE_SELECTION_AND_ONBOARDING_REMEDIATION_PLAN.md`, `FRONTEND_UI_WORKFLOW_LOGIC.md` (sign-up / onboarding / dashboard routing), `STYLE_GUIDE.md`, `MULTI_TENANCY_IMPLEMENTATION_PLAN.md` (plan / seat / trial fields), `REVENUE_GENERATION_SYSTEM_PLAN.md`.

**Source verified:**
- Frontend: `pages/auth/RegisterPage.tsx`, `pages/auth/OnboardingWizard.tsx`, `App.tsx` (route guards), `components/ProtectedRoute.tsx`, `components/RoleRoute.tsx`, `utils/roles.ts`, `layouts/dashboardShellConfig.ts` (`getLandingRoute`), `pages/dashboards/DashboardRouter.tsx`, `pages/platform/PlatformTenantDetailPage.tsx` (the `PlanSeatsEditor`), `pages/organization/OrganizationPage.tsx`.
- Backend: `services/auth_service.py` (`register`), `models/enums.py` (`UserRole`, grant matrix), `models/tenant.py` (`plan` / `seat_limit` / `trial_ends_at`), `services/seat_service.py`, `api/v1/tenants.py` (`PUT /{tenant_id}` monetization update), `api/v1/platform_tenants.py`, `services/providers/base.py` (AI provider interface), `services/providers/anthropic_provider.py`.

The audit findings are folded into sections 3, 4, 5 so each proposed change is tied to what exists today.

---

## 0.5 Second-pass review: flaws found in rev 1 and corrected here

I re-reviewed rev 1 of this plan against the live source a second time, specifically hunting for workflow/logic breaks. Eight issues surfaced. All are corrected in the body below; they are listed here so the change is transparent.

| # | Flaw in rev 1 | What the source actually shows | Correction (applied in body) |
|---|---|---|---|
| R1 | A1-3 re-added `role` to `PATCH /onboarding/company`, duplicating role-change authority. | `OnboardingWizard.tsx:177-179` makes role read-only **by design** because role changes are deliberately routed through `PUT /users/{id}/role` (`change_user_role`), which already carries the owner-lock, seat guard, and `user_role_changed` audit (`users.py:545-610`). | Step 2 and the AccountModal reuse the **canonical** `PUT /users/{id}/role`, enabled by B2 + B6. No `role` on the onboarding endpoint; no duplicated authority. |
| R2 | A1-3 / 1D said "skip the billable-seat gate for the owner self-change." | `change_user_role`'s seat guard fires only when `will_be_billable and not was_billable` (`users.py:579-581`). Agent, TeamLead, and TC are **all** already billable staff (`seat_service.py:36-44`), so switching among them never triggers it. | Dropped the seat-gate-skip; it is unnecessary this round. Noted why. |
| R3 | T2 / A1-5 claimed the onboarding stepper "reshapes" when the Step 2 role changes. | `buildSteps` branches only on internal-vs-external (`OnboardingWizard.tsx:87-89`). All three roles are internal, so the step list is identical and does **not** change among them. | Removed the "reshape" claim and the live-`buildSteps` machinery for this round; reshape only matters when crossing the internal/external boundary (A2/A3). |
| R4 | rev 1 never refreshed the user after a Step 2 role change. | Onboarding finish navigates via `getLandingRoute(user)` (`dashboardShellConfig.ts:205-226`), which keys off `user.role` / `user.team_id`. A stale local user would land the founder on the **old** role's dashboard. | Added an explicit "refetch `/me` (refresh auth user) after a Step 2 role change, before finishing" step. |
| R5 | rev 1 under-stated the email surface, the test's whole point ("AI + email"). | Email-connect endpoints are per-user (`integrations.py` uses `get_current_user`, not Admin), but the only UI route, `AdminIntegrationsPage`, is `ProtectedRoute requiredRole="Admin"` (`App.tsx:807-813`). A non-Admin founder is bounced from connecting email. | Promoted Integrations/email to a named owner-must-reach surface; F1 + F4 now explicitly cover it; added test T9. |
| R6 | F3 (`inviteableRolesFor` → Admin set) was marked Mandatory. | `inviteableRolesFor` already gives TeamLead `['TeamLead','TransactionCoordinator','Agent','Attorney',...portal]` and appends portal roles for every inviter (`useInvitations.ts:116-125`); the real gate is backend (B7 + B2). The core flow (TeamLead invites Agent) already works. | F3 downgraded to optional polish; B2 + B7 remain the mandatory invite enablers. |
| R7 | A1-2 said "promote `role` to a validated-optional field." | `UserRegisterRequest.role: UserRole \| None = None` already exists (accepted-but-ignored, `schemas/user.py:42`). | Reworded: honor the **existing** field in `auth_service` and add the allow-list; no new field. |
| R8 | rev 1 left the TeamLead-with-no-team landing unverified (the biggest latent dead-end risk). | `fetch_team` explicitly handles a teamless TeamLead via the no-team fallback, rendering a real (near-empty, honest) team shape (`dashboard_aggregator.py:292-332`). | Confirmed not a dead-end; capability table and risks updated to state this. |

Net effect: Workstream A gets **smaller and safer** (fewer new code paths, more reuse of already-tested authority logic), and two real break risks (email access, stale-user landing) are closed.

---

## 1. What is confirmed in the Audri thread (and what is not)

Scope discipline is the whole point of this plan: I resolve only what Audri and I both agreed to, and I list the rest under section 11 so nothing is silently dropped or silently built.

### 1.1 Confirmed (in scope here)

| # | Confirmed decision | Evidence in thread |
|---|---|---|
| **C1** | **Account types at signup follow Option B, phased.** For this test round the signup list is exactly **Agent, Team Leader, Transaction Coordinator**; each can create their own account, land on their own role-based dashboard, and start and manage transactions today. Attorney and FSBO get self-signup **right after** (once each has a "start your own transaction/listing" path). Mortgage and Title Vendors stay invite-only **for now** and gain self-signup plus seat purchase **in the vendor phase**. The foundation must keep all of that open. | Audri: "option B would be the best route... we want to move forward to get to a usable product and to continue testing." Jan's closing message confirmed the phased sequence; Audri's prior message asked for Attorney/FSBO self-accounts and for vendors to be able to buy seats later. |
| **C2** | **Plans are set by hand for the test; no online "upgrade and pay" page yet.** I assign Trial / Solo / Team manually; testers cannot buy a plan online during the test. | Jan proposed it; Audri: "That is good for us." |
| **C3** | **Measure real AI cost per deal during testing.** Both of us want the actual AI cost number from running test transactions (AI + email) before any pricing is set. | Audri: "We like to run through testing of transactions just with AI and email and find out what that AI cost is." This is the agreed prerequisite to pricing. |

### 1.2 Explicitly excluded (unconfirmed; tracked in section 11)

- **Final pricing numbers** (Solo $99, Team $299, Brokerage $899, Vendor $199-$499). Audri explicitly declined to set pricing yet. **Not built.**
- **Online checkout / self-serve payment page.** Deferred until pricing is locked (C2). **Not built.**
- **AI cost-reduction tactics** (smaller-model routing for simple jobs, response caching/reuse). These are my proposal in the last email and Audri has not yet replied to them. **Not built;** only the *measurement* in C3 is in scope.
- **Self-hosting AI vs cloud providers.** Open discussion, no decision. **Not built.**
- **Voice / text messaging cost and pricing.** Later phase, per Audri. **Not built.**

I am keeping the AI-cost work strictly to *instrumentation and a read-out*, so it gives Audri the number she asked for without committing to any pricing or optimization decision that is still open.

---

## 2. The three workstreams at a glance

| Workstream | Confirmed item | Net effort after audit | Why |
|---|---|---|---|
| **A. Signup role selection (phased)** | C1 | **Build** (Phase A1 now; A2/A3 sequenced) | Greenfield: no role field at signup, registrant hardcoded to Admin, no owner anchor. |
| **B. Manual plan assignment + honest billing** | C2 | **Mostly verify + small polish** | The platform-admin set-plan tool already exists and works; billing page already shows an honest placeholder (no broken checkout). |
| **C. AI cost measurement** | C3 | **Focused instrumentation + read-only report** | Providers capture no token usage today; there is a reserved UI slot but nothing behind it. |

The bulk of the new work is Workstream A. B and C are deliberately small and bounded.

---

## 3. Current-state audit (source-grounded)

### 3.1 Workstream A: signup roles
- `RegisterPage.tsx` has **no** account-type field. Its submit comment explicitly states role is omitted and the registrant becomes Admin.
- `auth_service.register()` hardcodes `registrant_role = UserRole.ADMIN` and records `tenant.owner_user_id = supabase_user_id`. **So the ownership fact already exists on the tenant row; it is simply never read back as authority.**
- `is_tenant_owner` exists **nowhere** in backend or frontend (verified by search). This is the missing primitive.
- `UserRole` (enums.py) already has every needed value: `Agent`, `TransactionCoordinator`, `TeamLead`, `Attorney`, `ForSaleByOwner`, `Vendor`, plus `Admin` / `Client`.
- **Lock-out risk (the workflow-breaker):** the moment a founder holds a non-Admin role, role-gated guards bite:
  - `ProtectedRoute requiredRole="TeamLead"` gates Team, Admin Users, Admin Teams, Task Templates, Communications, Vendor Templates. An **Agent** or **TC** founder fails `hasMinimumRole` and is bounced to `/unauthorized` on their own management screens.
  - `ProtectedRoute requiredRole="Admin"` gates User Detail, Audit Logs, AI Governance, Integrations. A **TeamLead** founder fails these.
  - `create_invitation` is `require_role(AGENT, TEAM_LEAD, ADMIN)` with an inline grant check. A **TC** founder cannot even reach it; an Agent founder can only grant `Agent`.
- **Landing routes already work** for all three (`getLandingRoute` / `DashboardRouter`): Agent/TC with no team to `/dashboard/agent`, with a team and all TeamLeads to `/dashboard/team`. All three are in `INTERNAL_OPS_ROLES`, so the New Transaction wizard and workspace are open to them. So once the founder holds the right role and keeps owner authority, the end-to-end deal path is intact.

**Conclusion:** Workstream A needs (1) a role choice at signup limited to the three roles, (2) the role honored server-side, and (3) an **owner anchor** so a non-Admin founder is never locked out of managing their own workspace. The connected-tier dead-end work from rev-2 (Vendor/FSBO/Attorney portals, `vendor_category` storage) is **not** needed now because none of those roles self-register in this round.

### 3.2 Workstream B: manual plan assignment
- `Tenant` model already has `plan: str = "trial"`, `seat_limit: int | None = 5`, `trial_ends_at`.
- `api/v1/tenants.py` `PUT /{tenant_id}` (platform-admin only) already updates the monetization fields, and the frontend `PlatformTenantDetailPage.tsx` already renders a working **`PlanSeatsEditor`** (plan select, seat-limit input, trial-end date) that calls it. **C2's mechanism is already built.**
- `SeatService.assert_staff_seat_available` already enforces plan rules: `solo` forbids extra staff; `seat_limit` caps the rest; `null` means unlimited.
- `OrganizationPage.tsx` shows an **honest placeholder** ("AI usage metering will appear here once billing is connected"), so there is **no broken online-checkout button** for a tester to hit. Good.
- **Gap:** a tester / founder cannot see which plan they are on from their own settings, and there is no one-line honest statement that the plan is managed during the beta. That is the only real gap, and it is a small honesty/visibility polish.

### 3.3 Workstream C: AI cost measurement
- `AIProvider` (base.py) returns plain results; `chat_completion` returns a bare `str`. Neither it nor `anthropic_provider.py` captures `usage` / prompt / completion tokens (verified by search). **No usage is recorded anywhere, so per-deal AI cost cannot be reported today.**
- `OrganizationPage.tsx:554` already reserves a UI slot for usage metering. There is a natural home for the read-out.

**Conclusion:** C3 needs a small capture-and-attribute layer at the provider boundary plus a read-only report. No pricing, no optimization.

---

## 4. The decision

> **A self-registering founder picks their professional role at sign-up from the three self-operating roles (Agent, Team Leader, Transaction Coordinator) and may change it on Step 2. The founder is always the Owner of their workspace. "Owner" is a single explicit authority anchor (`is_tenant_owner`) honored at every role-gated choke point, so a non-Admin founder keeps full workspace-management power and can never lock themselves out. Plans are assigned by hand by a platform admin; the in-app billing surface states this honestly and exposes no online checkout. AI token usage is captured at the provider boundary and surfaced as a read-only per-deal / per-tenant cost figure, with pricing and optimization left for a later, separately confirmed decision.**

**Account-type to role mapping for this round (single source of truth for both screens):**

| User-facing account type | Stored `role` | This round? |
|---|---|---|
| Agent | `Agent` | **Yes (signup)** |
| Team Leader | `TeamLead` | **Yes (signup)** |
| Transaction Coordinator | `TransactionCoordinator` | **Yes (signup)** |
| Attorney | `Attorney` | Phase A2 (right after) |
| For Sale by Owner | `ForSaleByOwner` | Phase A2 (right after) |
| Mortgage Vendor | `Vendor` + `vendor_category="mortgage"` | Phase A3 (vendor phase) |
| Title Vendor | `Vendor` + `vendor_category="title"` | Phase A3 (vendor phase) |

`Admin` and `Client` are never self-signup choices (owner authority comes from ownership, not the Admin label; Clients only enter through a transaction invite).

---

## 5. Implementation

### Workstream A: signup role selection (phased)

#### Phase A0: verify the two already-landed fixes (no product code)
Per rev-2, the phone-digit and Company/Brokerage carry-over fixes are in the tree. Re-confirm in the UI: phone `1 (317) 555-0142` shows `(317) 555-0142`; "Hearthstone Realty" typed at signup pre-fills the Company box on Step 2. These are the bugs Audri's earlier notes raised, already fixed; this is verification only.

#### Phase A1: the three self-operating roles + owner anchor (THIS TEST ROUND)

**A1-1. Owner anchor (backend).** Add a transient `is_tenant_owner: bool` to the `User` model and to `UserResponse`. Compute and honor it at the closed checklist in section 6. Reuse rev-2's exact choke-point list, narrowed to the items the three roles actually hit (B1, B2, B6, B7, B11 are mandatory; B3-B5, B8-B10 included for completeness so no surface is missed). The data already exists (`tenant.owner_user_id`); this only reads it back as authority.

**A1-2. Honor `role` at registration (constrained).**
- `UserRegisterRequest.role: UserRole | None = None` **already exists** (currently accepted-but-ignored, `schemas/user.py:42`). The change is to *honor* it, not add it.
- Define `SELF_SIGNUP_ROLES_NOW = {Agent, TeamLead, TransactionCoordinator}`. Reject anything else (including Admin / Client) with `422`. This server-side allow-list is what guarantees a tester cannot mint an Admin or a not-yet-enabled role even by hand-posting.
- In `auth_service.register()`: replace the hardcoded `registrant_role = UserRole.ADMIN` with `registrant_role = payload.role if payload.role in SELF_SIGNUP_ROLES_NOW else UserRole.AGENT` (default Agent, never silent Admin). **Keep `tenant.owner_user_id = supabase_user_id` regardless of role.** Keep seeding `company_name` from `organization_name`. Remove the stale "role is ignored / registrant is Admin" comment block. The profile row is created before the email-confirmation session check (`auth_service.py:113-122`), so the chosen role persists even when email confirmation is on.

**A1-3. Owner self-role-change through the canonical endpoint (no onboarding duplication).** Do **not** re-add `role` to `CompanyProfileUpdate` / `PATCH /onboarding/company`. Instead, the Step 2 dropdown (and the later AccountModal) change the founder's role through the existing `PUT /users/{id}/role` (`change_user_role`), which already enforces tenant scope, the seat guard, and the `user_role_changed` audit. The only backend changes needed are:
- **B6**: allow the owner to change **their own** role (today `change_user_role` blocks any change where `user_id == owner`, `users.py:566`); still block anyone else from changing the owner's role.
- **B2**: the endpoint is `require_role(ADMIN)` (`users.py:549`); the owner short-circuit lets an Agent/TC/TeamLead founder reach it.
- **Allow-list on the owner-self path**: when `current_user.id == user_id`, restrict `payload.role` to `SELF_SIGNUP_ROLES_NOW` so the founder cannot self-promote to Admin or self-demote into a portal role. Admin-changes-others keeps its existing grant rules.
- **System-assigned stays locked**: an invited teammate (`joined_via_invitation_id` set) is not the owner, so B6 already keeps their role locked. No extra guard needed.
- **No seat-gate-skip**: the seat guard only fires on portal-to-staff promotion (`will_be_billable and not was_billable`, `users.py:579-581`); all three roles are already billable, so it never triggers here.

**A1-4. Step 1 "I am a..." dropdown (RegisterPage).**
- New shared `utils/accountTypes.ts`: `ACCOUNT_TYPES_NOW = [{label:'Agent', role:'Agent'}, {label:'Team Leader', role:'TeamLead'}, {label:'Transaction Coordinator', role:'TransactionCoordinator'}]`, default **Agent**. One source of truth for Step 1 and Step 2.
- Add a single `@/components/ui/select` labeled **"I am a..."** under Full name, styled like `InviteUserModal` (`border-[1.5px] border-ve-border`, `focus:border-ve-orange`). Mouse-only, no typing.
- Helper line: "This sets up your workspace for how you work. You can change it on the next screen."
- Include `role` in the register payload.

**A1-5. Step 2 editable role dropdown (OnboardingWizard).**
- Replace the read-only role box with the same `Select` (from `ACCOUNT_TYPES_NOW`), seeded from `user.role`. Because all three roles are internal, **the step list does not reshape** when the founder switches among them (`buildSteps` branches only on internal-vs-external, `OnboardingWizard.tsx:87-89`); so no live `buildSteps` re-derivation is needed this round. The dropdown only changes which role/dashboard the founder ends on.
- On change, call `PUT /users/{id}/role` (A1-3), then **refetch `/me` / refresh the auth user** so `getLandingRoute` uses the new role at finish (otherwise the founder lands on the previous role's dashboard, `dashboardShellConfig.ts:205-226`). This refresh is the fix for review flaw R4.
- Lock the field (read-only with the existing "ask a tenant admin" helper) only when the user is **not** the owner (i.e. an invitee, `joined_via_invitation_id` set). Founders get the editable dropdown.
- Step 1 is the primary mechanism for the confirmed requirement; Step 2 is the "fix-it-here" affordance from Jake's original note.

**A1-6. Owner-bypass guards + Owner affordance (frontend).** Implement F1 and F4 (mandatory) from section 6; F2 where a management `RoleRoute` would exclude one of the three; F3 as optional polish. Add a compact **"Workspace owner"** entry plus an **Owner** badge in `AppLayout` when `user.is_tenant_owner`, opening Team, Settings, Billing, Invite, **and Integrations (email connection)**. This is what turns an Agent/TC founder from "bounced to /unauthorized" into "can manage their workspace."

**Integrations/email is test-critical (review flaw R5).** The test is "AI + email," so the founder must be able to connect their inbox. The backend email-connect endpoints are already per-user (`integrations.py` uses `get_current_user`), but the only UI route, `AdminIntegrationsPage`, is `ProtectedRoute requiredRole="Admin"` (`App.tsx:807-813`). F1 (owner bypass on `ProtectedRoute`) unblocks it and F4 surfaces the link, so a non-Admin founder can connect email. Without this, the whole AI-email test breaks for every founder who is not labeled Admin.

#### Phase A2: Attorney + FSBO self-signup (right after this round)
- Add Attorney and For Sale by Owner to `ACCOUNT_TYPES` and to the server allow-list.
- Give each a **self-serve "start your own transaction / listing"** entry so they are genuinely self-operating, not an honest-but-empty dead-end (the FSBO overview currently says "your coordinator will help you add your first property," which is wrong for a self-signup founder). This is the "start your own transaction/listing step" I committed to Audri.
- This is sequenced *after* A1 ships and is verified, exactly as agreed.

#### Phase A3: Mortgage / Title Vendor self-signup + seats (vendor phase)
- Add the two vendor types (collapsing to `Vendor` + `vendor_category`), self-signup, seat purchase, and the vendor-organization model. The owner anchor and the constrained allow-list from A1 keep this open without doing it now. Tracked in `VENDOR_WORKSPACE_SUPERIOR_PLAN.md`.

### Workstream B: manual plan assignment + honest billing (C2)

**B-1. Verify the existing hand-set path end-to-end.** As platform admin, on `PlatformTenantDetailPage` set a tenant to Trial, then Solo, then Team with `seat_limit`, then a `trial_ends_at`; confirm each persists via `PUT /tenants/{id}` and is reflected in the tenant's behavior (Solo blocks staff invites with `plan_does_not_allow_staff_members`; Team allows up to `seat_limit`, then `seat_limit_reached`). No new code; this is the documented test procedure for the round.

**B-2. Small honesty/visibility polish (the only build here).** On the founder's own billing/settings surface (`OrganizationPage`), add a **read-only plan badge** ("Your plan: Team, 3 seats" sourced from `TenantResponse.plan` / `seat_limit` / `staff_seat_count`) and one honest line: "During the beta your plan is set by your Velvet Elves account team. Online plan changes arrive once pricing is finalized." No pay button, no checkout, no dead end. This makes C2 fully UI-testable from the tester's seat (they can *see* their plan) and prevents any "where do I pay?" confusion.

### Workstream C: AI cost measurement (C3)

**C-1. Capture usage at the provider boundary.** Extend the `AIProvider` results / `chat_completion` path to return token usage (`prompt_tokens`, `completion_tokens`, model id) from the provider response, for both OpenAI and Anthropic. The interface already centralizes every AI call, so this is one chokepoint.

**C-2. Attribute and store.** Persist one usage row per AI call with `tenant_id`, optional `transaction_id`, `feature` (extraction / email / guidance / chat), `model`, token counts, and a computed `cost_usd` from a small editable rate table (current published per-model rates for the providers actually in use). Attribution to a transaction is what yields "AI cost per deal."

**C-3. Read-only report (UI-testable).** Surface a platform-admin **AI Usage** panel: cost per tenant and per transaction, with date range, behind `ve_ai_cost_metering_v1`. Optionally fill the existing `OrganizationPage` usage placeholder with the tenant's own roll-up. This is exactly the number Audri asked for, and Jan can validate it by running test deals and watching real cost accrue.

**C-4. Out of scope (restated for clarity):** no pricing, no checkout, no model-routing, no caching, no hosting decision. Those wait for a separately confirmed decision (section 11).

---

## 6. Owner-authority choke-point checklist (reused from rev-2, scoped to this round)

`is_tenant_owner` is computed once and honored at exactly these points. The prior plans broke because this list was implicit; here it is explicit and closed.

**Backend**
| # | Location | Change | Priority for A1 |
|---|---|---|---|
| B1 | `core/auth.py: get_current_user` | `user.is_tenant_owner = tenant is not None and tenant.owner_user_id == user.id`. Today the tenant is loaded only inside the `if not user.is_platform_admin` suspension branch (`auth.py:76-78`); ensure it is loaded (or the flag computed) for every non-platform-admin, and that platform admins get `is_tenant_owner = False` safely. | **Mandatory** |
| B2 | `core/auth.py: require_role` | Short-circuit `if current_user.is_tenant_owner: return current_user`. Covers `require_role(ADMIN)` and `require_role(AGENT, TEAM_LEAD, ADMIN)` guards (so a TC founder reaches `create_invitation`). | **Mandatory** |
| B3-B5 | `require_team_access`, `list_accessible_transaction_ids`, `require_transaction_access` | Treat owner like Admin/TeamLead. | Include (low risk; the three roles mostly pass already) |
| B6 | `api/v1/users.py: change_user_role` | Change the owner-lock (`users.py:566`) so the owner may change **their own** role (block only when `owner_user_id == user_id AND current_user.id != user_id AND not is_platform_admin`); on the owner-self path restrict `payload.role` to `SELF_SIGNUP_ROLES_NOW`. This canonical endpoint backs both Step 2 and the AccountModal (no onboarding duplication). | **Mandatory** (Step 2 relabel + owner protection) |
| B7 | `api/v1/invitations.py: create_invitation` grant check | Add `or current_user.is_tenant_owner` to the grant clause. | **Mandatory** (founder can invite) |
| B8-B10 | `payments_aggregator.py`, `payment_access_service.py`, `suggestion_engine.py`, `fsbo_workspace.py` Admin clauses | Add owner clause. | Include (completeness) |
| B11 | Token builders (`auth_service.register`, login, refresh, `_build_token_response`) | Set `is_tenant_owner` before `UserResponse.model_validate`, so it is correct at login, not only on `/me`. | **Mandatory** |

Do **not** add an owner bypass to the role-specific dashboard guards (`require_exact_roles`): an owner labeled Agent must correctly land on the Agent dashboard, not every dashboard. Keeping these strict is what keeps routing coherent.

**Frontend**
| # | Location | Change | Priority for A1 |
|---|---|---|---|
| F1 | `components/ProtectedRoute.tsx` | `... && !hasMinimumRole(user.role, requiredRole) && !user.is_tenant_owner`. Unblocks Agent/TC/TeamLead founders on Team and Admin management routes. | **Mandatory** |
| F2 | `components/RoleRoute.tsx` | Optional `ownerBypass`; apply only on management routes that would exclude one of the three (identity dashboards stay strict). | Include where needed |
| F3 | `hooks/useInvitations.ts: inviteableRolesFor` | Owner returns the Admin invite set regardless of role. | Optional (the core flow already works: `inviteableRolesFor` gives TeamLead the Agent/TC set and appends portal roles for everyone, `useInvitations.ts:116-125`; the real gate is backend B7 + B2) |
| F4 | `layouts/AppLayout.tsx` | "Workspace owner" affordance + Owner badge when `user.is_tenant_owner`. Its links include **Integrations (email)**, which is Admin-gated in the UI (`App.tsx:807-813`) yet test-critical. | **Mandatory** |

`is_tenant_owner` must be added to `UserResponse` (backend) and the `User` type (frontend) so every guard can read it. F1 + F4 together are what make the email-connection surface reachable for a non-Admin founder, so the "AI + email" test can run at all.

---

## 7. UI / UX and visual design (the priority for non-developer testers)

The testers are real-estate professionals, not developers, so every step here is mouse-first, low-typing, honest, and consistent with the existing product chrome.

- **One click, fixed list, sensible default.** Both the signup "I am a..." and the Step 2 role use `@/components/ui/select` with the three options and default **Agent**, so a tester who does nothing still gets a working, non-Admin role. No free-text. (Matches the "mouse-first / minimal typing" rule.)
- **Reuse, do not reinvent.** Same select component, type scale, `border-[1.5px] border-ve-border`, `focus:border-ve-orange`, radius, and focus ring as `InviteUserModal`. The dropdown drops into the existing onboarding split-panel shell (dark `ve-sidebar`, serif headings, `font-mono` kickers, orange accent) with no layout rework, so it harmonizes with the established aesthetic in `STYLE_GUIDE.md`.
- **Professional-tool feel.** The "Workspace owner" chip reuses the orange-accent shield/pill motif already used on the onboarding privacy card and invite-modal header, so the founder's management entry reads as a deliberate professional affordance, not a bolt-on.
- **Honest states, no mock data.** The plan badge shows the real assigned plan; the billing surface states plainly that plans are set during the beta (no fake "pay" button); the AI usage panel shows real captured cost (zero until deals run). This follows the no-demo-data rule and keeps every screen truthful.
- **No dead ends.** Because the only self-signup roles this round are the three self-operating ones, every tester lands on a dashboard where they can immediately start a transaction and manage their workspace. That is the core "end-to-end does not break down" guarantee.

---

## 8. MVP capability by role (so testers know what "done" looks like this round)

| Account type | Lands on | Can do this round as a solo founder/owner |
|---|---|---|
| Agent | `/dashboard/agent` | Create and run deals, manage workspace (Team/Settings/Billing via Owner affordance), invite teammates |
| Team Leader | `/dashboard/team` | All of Agent + team management; invite agents/TCs into the team |
| Transaction Coordinator | `/dashboard/agent` (no team) or `/dashboard/team` | Coordinate and run deals, manage workspace, invite |

A brand-new **Team Leader** founder has no team yet, but `getLandingRoute` sends them to `/dashboard/team` and `fetch_team` renders a real, honest, near-empty team shape via its no-team fallback (`dashboard_aggregator.py:292-332`), so it is not a dead-end; they invite their first agent from the Team page or the Owner affordance.

Attorney, FSBO, and the two Vendor types are **not** signup choices this round (Phases A2 / A3); they continue to join by being added to a transaction, exactly as today, so no tester reaches an empty portal by self-signup.

---

## 9. End-to-end UI test script (non-developer testers, flags on)

**T1: Agent signup.** Register; "I am a..." defaults to **Agent**; phone `1 (317) 555-0142` shows `(317) 555-0142`; "Hearthstone Realty" pre-fills the Company box on Step 2. Finish to the Agent dashboard with a "Workspace owner" chip.

**T2: change role on Step 2.** Sign up as Agent; on Step 2 switch to **Team Leader** and confirm the hint shows (the step list does **not** change, since both are internal roles); finish and confirm the landing is the **Team** dashboard with the Owner chip (proves the post-change user refresh worked, not the old Agent dashboard).

**T3: each of the three renders and works.** Repeat for Team Leader and Transaction Coordinator; each lands on the correct dashboard with the Owner chip and can open the New Transaction wizard.

**T4: founder cannot lock themselves out.** As an **Agent** founder, click "Workspace owner": Team, Settings, Billing, **and Integrations** all open (not `/unauthorized`). Repeat as a **TC** founder and a **Team Leader** founder (the latter must still reach Integrations, which is Admin-gated).

**T5: founder can invite.** As an Agent founder and as a TC founder, open Invite, confirm staff roles are listed, send an invite, confirm it sends (no "only an Admin can grant" error).

**T6: system-assigned role stays locked.** Have a founder invite a teammate; the teammate accepts and reaches Step 2; confirm their role field is read-only with the "ask a tenant admin" helper (a founder relabels; an invitee does not).

**T7: plan set by hand is visible and enforced.** As platform admin, set the tenant to **Solo**; as the founder, confirm the billing surface shows "Your plan: Solo" and that inviting a teammate is correctly refused with a plan message; switch to **Team / 3 seats** and confirm invites now work up to the limit. Confirm there is no online "pay" button anywhere.

**T8: AI cost accrues.** With `ve_ai_cost_metering_v1` on, run one full AI deal (upload a contract, send an AI email); open the platform-admin AI Usage panel and confirm a non-zero cost is attributed to that transaction and tenant.

**T9: founder can connect email (the AI-email prerequisite).** As an **Agent** founder (not Admin), open Integrations via the Owner affordance and connect an inbox; confirm the connect flow completes and an AI email can then be sent on a deal. This is the surface that review flaw R5 would have left unreachable.

---

## 10. File-by-file checklist

**Backend**
- `app/models/user.py` - transient `is_tenant_owner`.
- `app/schemas/user.py` - validated `role` on register; `is_tenant_owner` on `UserResponse`.
- `app/core/auth.py` - B1-B5.
- `app/api/v1/users.py` - B6; expose `is_tenant_owner` on `/me`.
- `app/api/v1/invitations.py` - B7 grant-check owner clause.
- `app/services/payments_aggregator.py`, `payment_access_service.py`, `suggestion_engine.py`, `fsbo_workspace.py` - B8-B10.
- `app/services/auth_service.py` - honor the existing `role` (default Agent), keep owner write, B11 token builders.
- `app/api/v1/users.py: change_user_role` - B6 owner-self-allowed + owner-self allow-list (`SELF_SIGNUP_ROLES_NOW`). This is the **single** role-change authority path; no onboarding-endpoint duplication.
- (`app/schemas/onboarding.py` / `app/api/v1/onboarding.py` are **unchanged** for role - corrected from rev 1, which would have duplicated authority here.)
- **C3:** `app/services/providers/base.py`, `openai_provider.py`, `anthropic_provider.py` - return token usage; new usage-recording service + storage; rate table; platform-admin AI-usage endpoint.

**Frontend**
- `src/utils/accountTypes.ts` (new) - `ACCOUNT_TYPES_NOW`.
- `src/pages/auth/RegisterPage.tsx` - "I am a..." select; send `role`; remove the stale "role omitted" comment.
- `src/pages/auth/OnboardingWizard.tsx` - editable role select calling `PUT /users/{id}/role`; refetch `/me` after change; lock only for invitees (non-owners). No step-list re-derivation.
- `src/components/ProtectedRoute.tsx` - F1 (also unblocks the Admin-gated Integrations route for owners).
- `src/components/RoleRoute.tsx` - F2 where needed.
- `src/hooks/useInvitations.ts` - F3 (optional polish).
- `src/layouts/AppLayout.tsx` - F4 Owner affordance + badge.
- `src/types/api.ts` - widen `UserRegisterRequest` / `CompanyProfileUpdate` / `User` (`role`, `is_tenant_owner`).
- **C2:** `src/pages/organization/OrganizationPage.tsx` - read-only plan badge + honest beta line.
- **C3:** platform-admin AI Usage page/panel + optional tenant roll-up in `OrganizationPage`.

**Docs**
- `FRONTEND_UI_WORKFLOW_LOGIC.md` (sign-up / onboarding / dashboard routing) - reconcile the three-role signup, the Step 2 role change via the canonical `PUT /users/{id}/role` (not the onboarding endpoint), the invitee lock exception, and the Owner affordance (including the Integrations/email entry).

---

## 11. Open items pending Audri (do not build until confirmed)

These are the unconfirmed threads from the email, kept visible so they are followed up, not silently built:

1. **Pricing numbers** (Solo / Team / Brokerage / Vendor). Audri declined to set them until AI cost is known. Workstream C produces that input; pricing is a later, explicit decision.
2. **Online checkout / self-serve payments.** Build only after pricing is locked.
3. **AI cost-reduction tactics** (cheaper model for simple jobs, response caching). My proposal in the last email; awaiting Audri's reply before any implementation.
4. **Self-hosting AI vs cloud providers.** Open discussion; no code.
5. **Voice / text messaging cost and pricing.** Later phase.

---

## 12. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| A non-Admin founder is locked out of their own management screens | Medium | Section 6 is a closed checklist; T4/T5 exercise the management paths directly. |
| Scope creep into the rev-2 all-7-roles build | Medium | Option B is confirmed; this plan ships only the three self-operating roles and phases the rest (A2/A3). |
| Public form mints a not-yet-enabled role | Low | Server-side `SELF_SIGNUP_ROLES_NOW` allow-list returns 422 for anything else. |
| Tester confused about how to pay | Low | C2 honesty line plus no checkout button; T7 verifies. |
| AI cost number is wrong or unattributed | Low | C2/C3 capture at the single provider chokepoint, store per transaction, and T8 validates a real deal. |
| `is_tenant_owner` wrong at login | Low | B11 sets it in every token builder, not only `get_current_user`. |
| Plan change not reflected in tenant behavior | Low | B-1 verifies seat gating after each hand-set; the gate already lives in `SeatService`. |
| Founder cannot connect email, so the AI-email test cannot run | Medium | F1 + F4 expose the Admin-gated Integrations route to owners; backend connect is already per-user; T9 validates. |
| Founder lands on the wrong dashboard after a Step 2 role change | Low | Refetch `/me` before finishing onboarding (A1-5); T2 confirms the Team dashboard, not the old one. |
| A teamless Team Leader founder hits an empty/broken team view | Low | `fetch_team` no-team fallback renders an honest team shape; T3 confirms it loads. |

---

## 13. Out of scope / post-test foundation (kept open, not built now)
- Attorney / FSBO self-serve "start your own transaction/listing" (Phase A2, right after this round).
- Mortgage / Title Vendor self-signup, seat purchase, vendor organizations and codes (Phase A3, vendor phase; see `VENDOR_WORKSPACE_SUPERIOR_PLAN.md`).
- All pricing, online checkout, AI cost-reduction tactics, AI hosting, and voice/text (section 11, pending Audri).
- Brokerage / Broker manual setup (explicitly not MVP).
- Any change to how invited (non-founder) users receive their role.
