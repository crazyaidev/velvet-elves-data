# Role-based accounts and autonomy — remediation and implementation plan

**Date:** 2026-07-31
**Author:** Jan Froben
**Input:** `ROLE_AUTONOMY_E2E_ISSUES_2026-07-31.md` (R-01 … R-20)
**Status:** Plan only. No source code changed by this document.
**Design posture:** standard, boring, conventional. Every decision below picks
the ordinary SaaS answer over a bespoke one, because the failure mode we are
fixing was caused by inventing a second authority system and only half-wiring
it.

---

## 0. The one decision everything follows from

> **Permission is computed in exactly one place, from exactly two inputs — the
> user's role and whether they own the workspace — and every screen and every
> endpoint reads that one answer. A capability that a user has must be visible;
> a capability they lack must be explained, with the next step offered.**

This is the standard RBAC + resource-ownership model that every comparable
product uses. It is not new architecture: the backend already computes
`is_tenant_owner` correctly and honors it in `require_role`. The frontend
simply never got the same treatment, so today the same permission is decided
three different ways — `settingsCards.ts` gets it right, `AppLayout`'s sidebar
config ignores ownership, and a dozen pages compare `role === 'Admin'` by hand.

Two supporting decisions:

1. **Roles describe a job; ownership grants authority.** "Agent" and "Team
   Leader" say what work a person does and which dashboard they land on.
   "Can rename the org / can pay / can invite" comes from being the owner or
   holding an admin grant. Never from the job label.
2. **Owning a workspace is not the same as being alone in it.** A founder is
   autonomous over *their own* workspace. A person invited into someone else's
   workspace is autonomous over their own work, not over the business. That
   distinction is correct and must be made legible instead of being discovered
   through a 403.

### What this does *not* do

It does not make an invited Agent able to spend the brokerage's money, and it
does not turn Vendor or Client into self-serve products. Those are deliberate
boundaries; the plan makes them explicit and gives each one an action instead
of a wall.

---

## 1. Phase map

| Phase | Title | Closes | Effort | Depends on |
| --- | --- | --- | --- | --- |
| 0 | Close the data leak | R-09, R-10 | 0.5 d | — |
| 1 | One permission source of truth | R-01, R-02, R-03, R-05 | 2 d | — |
| 2 | Navigation follows capability | R-04, R-06, R-07 | 1.5 d | 1 |
| 3 | Paying is never a dead end | R-08 | 1.5 d | 1 |
| 4 | The seat ceiling becomes visible and liftable | R-11, R-12, R-13 | 2.5 d | 1 |
| 5 | Sign-up tells the truth about roles | R-14, R-15, R-16, R-17, R-18 | 2 d | 1 |
| 6 | Connected roles get an honest first session | R-19, R-20 | 2.5 d | 2, 5 |
| 7 | Lock it down with tests | proves 0-6 | 1.5 d | 1-6 |

**≈ 14 developer-days.** Phase 0 ships on its own, today. Phases 1-3 are what
Jake actually reported and are worth releasing before the rest.

---

## Phase 0 — Close the data leak (ship first, independently)

**R-09 / R-10.** An external Vendor can currently read the brokerage's per-deal
fee, prepaid balance and credit ledger by typing a URL. Fix at both layers,
because either one alone leaves a hole.

**0A. Guard the route.** `App.tsx:743` is the only route in the file with no
guard at all:

```tsx
// before
<Route path={ROUTES.ORG_SETTINGS} element={<OrganizationPage />} />

// after
<Route
  path={ROUTES.ORG_SETTINGS}
  element={
    <RoleRoute allowedRoles={INTERNAL_ROLES} ownerBypass>
      <OrganizationPage />
    </RoleRoute>
  }
/>
```

**0B. Guard the data.** Add a `can_manage_billing` check to the read endpoints,
not only the write one:

| Endpoint | Today | After |
| --- | --- | --- |
| `GET /billing/credits/wallet` | any authenticated user | owner / Admin / platform admin — others get the fee and their own workspace's *policy*, never the balance or the ledger |
| `GET /billing/credits/pricing` | any authenticated user | unchanged (the fee is not a secret; the paywall needs it) |
| `GET /billing/credits/ledger` | any authenticated user | owner / Admin / platform admin only |

Keep `can_manage_billing` in the wallet **response** so the pane can still
render its honest non-manager message without a second call.

**0C.** `OrganizationPage`'s `?section=danger` fallback currently renders the
Company card for users who cannot see the Danger zone, which is how the org
name and seat count leaked on that section too. Fall back to a "you do not have
access to this section" panel instead of to another section's content.

**Verification:** re-run `r06_focus.mjs` — every portal role must land on
`/unauthorized` for all four `?section=` values, and `wallet` must return 403
for Client / Vendor / FSBO.

---

## Phase 1 — One permission source of truth

### 1A. A single frontend permission module

New `src/utils/permissions.ts`. Nothing else in the app is allowed to compare
`user.role` to `'Admin'` again.

```ts
export interface Capabilities {
  manageWorkspace: boolean   // rename org, branding, integrations, danger
  manageBilling: boolean     // buy deals, read wallet + ledger
  manageMembers: boolean     // invite, change roles, deactivate
  manageTeamLibrary: boolean // task/vendor/email templates, playbook
  viewOversight: boolean     // audit log, communication audit
  runDeals: boolean          // create + own transactions
}

export function capabilitiesFor(user: User): Capabilities
```

with exactly one rule inside: `const admin = user.role === 'Admin' || !!user.is_tenant_owner`.
This mirrors `require_role`'s owner short-circuit, so the two ends agree by
construction.

Add a `useCapabilities()` hook over `useAuth()` so components read
`const { manageBilling } = useCapabilities()`.

### 1B. Migrate the fourteen call sites

Replace the flags listed in R-05 with the module. The mechanical changes:

| File | Replace |
| --- | --- |
| `pages/organization/OrganizationPage.tsx:82` | `canEditTenant` → `caps.manageWorkspace` **(closes R-01, R-03)** |
| `pages/users/AdminUsersListPage.tsx:56` | `isAdmin` → `caps.manageMembers` |
| `pages/admin/AdminTeamsPage.tsx:54`, `AdminTeamSettingsPage.tsx:70`, `TaskTemplateListPage.tsx:102` | `isAdmin` → `caps.manageTeamLibrary` |
| `pages/admin/CommunicationAuditPage.tsx:77` | `isAdmin` → `caps.viewOversight` |
| `components/team/TeamMembersTable.tsx:110`, `ManageTeamMembersPanel.tsx:68`, `pages/TeamPage.tsx:483,496` | `isAdmin` → `caps.manageMembers` |
| `pages/vendors/VendorListPage.tsx:88`, `pages/EmailTemplatesPage.tsx:75` | → `caps.manageTeamLibrary` |
| `pages/transactions/TransactionListPage.tsx:426`, `components/wizard/NewTransactionWizard.tsx:3309,3321,5812` | → `caps.viewOversight` / `caps.manageMembers` as the branch requires |
| `pages/settings/settingsCards.ts:59,62` | keep the behaviour, re-express via the module so there is one definition |

**Do not** add an owner bypass to the identity dashboards
(`require_exact_roles`, `RoleRoute` without `ownerBypass`). An Agent owner must
still *not* reach `/dashboard/attorney`; that strictness is what keeps routing
coherent, and the route sweep confirms it already behaves correctly.

### 1C. Fix the copy that assumes the reader is not the owner

"Only an Admin can change this. **Ask your workspace owner** if it needs
updating" must never render to the workspace owner. With 1B the owner sees an
editable field instead; for a genuine non-manager the line becomes *"Only a
workspace owner or admin can change this."*

---

## Phase 2 — Navigation follows capability

### 2A. Make the sidebar capability-driven (R-04)

`dashboardShellConfig.ts` keeps `sidebarSections` as the **role** default —
that part is right, it is what makes an Agent's sidebar feel like an agent's
tool. Add capability-driven *augmentation* in `AppLayout`:

```ts
const sections = [...capability.sidebarSections]
if (caps.manageMembers && !sections.includes('team')) sections.push('team')
if (caps.viewOversight && !sections.includes('admin')) sections.push('admin')
```

An Agent founder then gets their agent-shaped sidebar **plus** Team and
Oversight, which is exactly what the Settings hub already shows them. Nothing
changes for an invited Agent.

### 2B. Give an Agent/TC a way to invite (R-06)

Two options; take the second.

- ~~Loosen `/admin/users` to `requiredRole="Agent"`~~ — drags a whole admin
  console in front of a member who should only add a client to their own deal.
- **Adopted:** keep `/admin/users` at TeamLead+, and surface the existing
  `InviteUserModal` where an Agent already works — a "Invite someone" action in
  the Clients hub and in the transaction People tab, scoped by
  `inviteableRolesFor(role, isOwner)`. This is the conventional pattern: admin
  console for administrators, contextual invite for practitioners.

### 2C. Align the invite matrix with the server (R-07)

`inviteableRolesFor`'s `default` branch returns portal roles to Attorney /
Vendor / FSBO / Client, none of whom the backend permits. Change the default to
`[]` and add an explicit `case 'Attorney': return []`. If Attorneys *should* be
able to bring in a client, do it the other way — add `UserRole.ATTORNEY` to the
`require_role` list in `api/v1/invitations.py:127` — but decide it once, in one
place. Until decided, the matrix must not advertise an action that 403s.

---

## Phase 3 — Paying is never a dead end (R-08)

### 3A. Wire the escalation that already exists

`POST /billing/credits/notify-admin` works and returns 202 for every role
tested. Nothing calls it from the Billing pane. Add to the non-manager state:

```
A workspace owner or admin handles payments for this account.
        [ Ask them to add deals ]     ← posts notify-admin
```

with a success toast naming who was notified, and a 24-hour throttle so a
frustrated coordinator cannot spam the owner. The same control belongs in
`CreditPaywallModal`, which is where the need is actually felt — mid-wizard,
with a deal half-created.

### 3B. Decide the Team Leader question explicitly

Today `can_manage_billing` excludes a non-owner Team Leader. That is defensible
but was never chosen. Recommendation: **add a per-workspace "who can pay"
setting** (owner only *(default)* / owner + admins / owner + admins + team
leads) on the Billing section, and read it in `can_manage_billing`. This is the
standard answer, it costs one settings row, and it removes the argument
permanently. `payment_access_policy` already exists as a model to follow.

### 3C. Say why, not just no

When `checkout-session` 403s, the message should name the people who can act:
*"Ask Jane Smith (workspace owner) to add deals"* — the tenant already knows
`owner_user_id`.

---

## Phase 4 — The seat ceiling becomes visible and liftable

### 4A. Show the position where the action is (R-12, R-13)

Put the seat meter on `/admin/users`, next to the **Invite user** button — the
one screen where it matters:

```
Members  3 of 5 seats used  ·  2 pending invitations hold a seat each
```

and disable **Invite user** with that reason when
`active + pending >= seat_limit`, instead of letting the user fill a form and
receive a 409. Surface `staff_seat_count` and a new `pending_staff_invites`
count on `TenantResponse`.

### 4B. Make revoking an invitation obviously free a seat (R-13)

The Users page already lists pending invitations and has a revoke action; label
the consequence — *"Revoke — frees 1 seat"*.

### 4C. Decide the trial ceiling (R-11)

This is a business decision, not a code change, and it is the single biggest
blocker to "operate independently." Three options, in order of preference:

1. **Recommended — raise the default and stop calling it a trial.** Billing is
   already per-transaction at $49; staff seats are not a revenue lever, they
   are a support ceiling. Set `seat_limit = 25` (or `NULL`) for
   self-registration and let the per-deal fee do the monetizing. One line in
   `tenant_repository.provision_for_self_registration`, no UI at all. This is
   the standard model for usage-priced products and it makes every role
   autonomous by default.
2. **Self-serve raise with a guardrail** — a "Request more seats" control that
   lifts the cap to 25 immediately and notifies the platform. Costs a small UI
   plus an audit entry.
3. **Keep 5, sell the upgrade** — requires a plan catalogue, plan-change UI and
   Stripe subscription work. Weeks, not days, and it contradicts "no seats, no
   subscription", which is the copy already shipped on the Billing pane.

Option 1 is the recommendation. Whichever is chosen, the copy on the Company
section must match it — the current text promises online plan changes "once
pricing is finalized," and pricing *is* finalized ($49/transaction, 2026-07-30).

---

## Phase 5 — Sign-up tells the truth about roles

### 5A. Replace the bare dropdown with a described choice (R-17)

Standard sign-up pattern: each option carries one line of consequence. Same
`Select` component, same styling, `label` + `description`:

| Option | Description shown |
| --- | --- |
| Agent | "I run my own deals." |
| Team Leader | "I run deals and manage a team." |
| Transaction Coordinator | "I coordinate deals for agents." |

with the helper line kept: *"You can change this on the next screen."*

### 5B. Drop `Admin` from the public form (R-16)

Ownership already grants full authority — the E2E run proves all four founders
get identical Settings-hub capability — so the Admin option buys nothing and
costs the E-signature onboarding step. Remove it from `ACCOUNT_TYPES_NOW` and
from `SELF_SIGNUP_ROLES_NOW`. Testers who need an Admin-labelled account get one
by invitation or by the owner relabelling themselves.

If Jake wants it kept for demos, then instead add `Admin` to `ESIGN_ROLES` so
the wizard stops varying silently — but removing it is the standard answer.

### 5C. Make the rejection message match the form (R-15)

Generate the message from `SELF_SIGNUP_ROLES_NOW` rather than hard-coding three
role names, so the two can never drift again.

### 5D. Delete the stale contract comment (R-18)

`OnboardingWizard.tsx:184-188` describes behaviour that no longer exists.

### 5E. Which roles may self-register (R-14) — the recommendation

Jake asked for all roles to be self-serve. My recommendation is to **keep
self-registration to the three self-operating roles** and handle the other four
differently, because a self-registered Vendor or Client has no workspace, no
deal, and nothing to do — Phase 6 covers what they get instead. If a role has
no independent job to do on day one, letting it register produces an empty
account, not autonomy.

Concretely:

| Role | How the account is created | Why |
| --- | --- | --- |
| Agent, Team Leader, Transaction Coordinator | self-registration | runs their own workspace |
| Attorney | **self-registration, added in Phase 6** | has a real independent practice; needs a "create a matter" path first |
| ForSaleByOwner | self-registration **once FSBO self-listing exists** (Phase 6 fast-follow) | a seller genuinely can start alone |
| Vendor | invitation or a vendor connect-code | belongs to an outside company; the vendor-organization model is post-MVP |
| Client | invitation only | a client exists relative to a deal |

This is a narrower answer than "all eight," and I recommend saying so to Jake
plainly, with the Phase 6 sequencing as the path to the rest.

---

## Phase 6 — Connected roles get an honest first session

### 6A. Attorney becomes self-operating (R-19)

The largest single win, because an attorney genuinely does have their own
practice. Needs: `Attorney` added to `SELF_SIGNUP_ROLES_NOW` and
`ACCOUNT_TYPES_NOW`, a "Create a matter" entry point on the attorney dashboard
(the legal-packet intake modal already exists and is wired), and `Attorney`
added to the invite-capable list so they can bring in their own client.

### 6B. FSBO self-listing (R-19, R-20)

`FsboOverviewPage`'s empty state tells a self-registered seller their
"coordinator will help" — there is no coordinator. Give FSBO a "Add my
property" path, then open self-registration.

### 6C. Vendor stays invite-only, with a connect code

Standard marketplace pattern: the vendor is onboarded by the party that needs
them. Keep the portal invite-only for now; the vendor-organization work
(`VENDOR_WORKSPACE_SUPERIOR_PLAN.md`) is where a self-serve vendor account
belongs.

### 6D. Fix the portal Settings redirect (R-19)

`/settings/account` silently bouncing a Client to `/client/home` is a broken
promise. Redirect it to the account modal route those roles already have
(`/client/settings`, `/fsbo/settings`, and add the vendor equivalent) so
"Settings → Profile" works for everybody.

---

## Phase 7 — Lock it down with tests

The harness written for this round becomes the regression suite.

**Backend** (`app/tests/test_role_capabilities.py`) — a parametrized matrix over
all eight roles × owner/non-owner asserting the exact status code for:
`checkout-session`, `wallet`, `ledger`, `PATCH /tenants/current`,
`POST /invitations/`, `GET /users`, `GET /audit-logs`. The table in §2 of the
issues document is the expected-value fixture. This is what would have caught
R-09 and R-10.

**Frontend** (`src/tests/unit/permissions.test.ts`) — `capabilitiesFor()` over
the same matrix, plus a guard test asserting that no file outside
`permissions.ts` matches `/role === ['"]Admin/` (a lint rule is even better).

**E2E** — keep `c:\Projects\_tools\e2e\role\` checked in and runnable; it
already registers every role and reads the real screens.

---

## 8. Sequencing

- **R1 — "stop the leak and unblock the founder" (Phases 0-2, ~4 d).** Portal
  users stop reading workspace billing; a non-Admin founder can rename their
  org, edit branding and reach Team/Oversight from the sidebar. This is Jake's
  complaint, fixed.
- **R2 — "money and seats stop being walls" (Phases 3-4, ~4 d).** Every 403 on
  payment offers an action; the seat cap becomes visible, and per 4C most likely
  disappears.
- **R3 — "sign-up tells the truth" (Phase 5, ~2 d).** Described roles, no public
  Admin, honest error copy.
- **R4 — "the other four roles get a job" (Phases 6-7, ~4 d).** Attorney
  self-registration, FSBO self-listing, portal settings fix, the regression
  matrix.

Phase 0 should not wait for R1 planning; it is half a day and it is a live data
exposure.

---

## 9. Decisions needed before R1

| # | Question | Who | Default if unanswered |
| --- | --- | --- | --- |
| 1 | Trial seat cap: raise to 25/unlimited, add self-serve raise, or keep 5 and sell an upgrade? (4C) | Jake | Raise to 25 for self-registration |
| 2 | May a non-owner **Team Leader** pay for deals? (3B) | Jake | No by default, configurable per workspace |
| 3 | Keep `Admin` on the public sign-up form? (5B) | Jake | Remove it |
| 4 | May an **Attorney** invite their own client? (2C) | Audri | Yes — add Attorney to the backend invite list |
| 5 | Do we commit to Attorney + FSBO self-registration this cycle, or hold both to invite-only? (5E, 6A, 6B) | Jake | Commit to Attorney; hold FSBO until self-listing lands |

Questions 1 and 5 are the two that decide whether "every role can sign up and
operate freely" is answered fully or partially. Everything else in this plan is
implementation.

---

## 10. What not to break

- The backend owner anchor and its short-circuit in `require_role` — the fix is
  to make the UI agree with it, never to loosen the server.
- `require_exact_roles` on identity dashboards: an owner labelled Agent must
  still not reach the Attorney dashboard.
- The owner-protection on `PUT /users/{id}/role`: nobody but the owner may
  change the owner's role, and the owner's own relabel stays bounded to the
  self-operating set.
- The honest empty states. No demo data for a role with nothing to do.
- The Step-2 relabel, including the live stepper rebuild — verified working.
