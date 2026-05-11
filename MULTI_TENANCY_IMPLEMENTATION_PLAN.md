# Multi-Tenancy Implementation Plan

**Status:** Draft (second design-review remediation) &middot; **Owner:** Jan &middot; **Last updated:** 2026-05-11

This document captures everything still required to take the multi-tenancy work
from "data-isolation closed, lifecycle plumbed, invitation API live" to
"end-to-end usable in product, defense-in-depth at the DB, retention-compliant,
and ready for paid production." It does not duplicate work already shipped —
for that, see the table in &sect;2.

The 2026-05-11 revision pass addressed several flaws in the v1 draft: a
broken hard-delete cascade order, RLS migration bugs that would have hidden
system task templates and the public milestone viewer, missing retention /
legal-hold coverage, a Supabase-dashboard email path that's incompatible with
white-label, race conditions in seat-checking, audit-log ordering that
couldn't write the "tenant deleted" row, and an onboarding heuristic that
re-routed the original founder through the company-name step after an
ownership transfer.

The second 2026-05-11 review tightened the plan further: paid-seat counting
now excludes Client / FSBO / Vendor portal accounts; hard-delete writes a
durable purge manifest before live rows disappear; retention is anchored to
the requirements' "2 years from last login" rule; RLS activation keeps
tenant-admin mutation routes on service-role until role-aware policies land;
system task templates are read-only defaults with tenant-scoped overrides;
legal holds survive deleted tenants through a platform-level hold table; and
white-label URLs use the existing `tenants.domain` field plus DNS-verification
metadata instead of an invented `custom_domain` column.

---

## 1. Purpose & scope

The goal is **flawless multi-tenant management**: a brokerage's data is fully
isolated from every other brokerage at every layer (API, repo, DB), invite-only
joining is end-to-end usable through the product (not just the API), tenant
lifecycle (founding, suspension, ownership transfer, scheduled deletion,
legal hold) is well-defined, and the platform's documented 2-year retention
obligations survive customer departures.

Out of scope for v1:

- SSO / SAML for enterprise tenants.
- Multi-tenant *per-user* membership (a user belonging to multiple tenants
  simultaneously with a switcher). Current model is one-tenant-per-user.
- Self-service billing / Stripe integration. Plan-and-seat *modelling* is in
  scope as a precondition; charging is not.
- Tenant-scoped Fernet keys. The archive in &sect;4.11 keeps PII as
  ciphertext under the current platform-scoped key; tenant-scoped keys are
  a separate future change.

---

## 2. Current state (already shipped)

| Capability | Status |
|---|---|
| Self-registration provisions a fresh tenant per signup | &check; `AuthService.register` &rarr; `TenantRepository.provision_for_self_registration` |
| Client-supplied `tenant_id` ignored on register (closed cross-account leak) | &check; |
| Founder forced to `UserRole.ADMIN`; role NOT self-pickable at signup | &check; |
| Onboarding wizard no longer lets users change their own role | &check; |
| `tenants.owner_user_id` set on signup | &check; |
| `is_platform_admin` flag separate from `UserRole.ADMIN` | &check; |
| `require_tenant_access` no longer short-circuits for Admin | &check; |
| Cross-tenant endpoints (`/tenants` list/get/update/delete) gated by `require_platform_admin` | &check; |
| `PATCH /tenants/current` for tenant Admin to edit own org | &check; |
| `POST /tenants/current/transfer-ownership` (owner-only, auto-promote) | &check; |
| Owner-protection on `PUT /users/{id}/role` and `DELETE /users/{id}` | &check; |
| Suspended tenant blocks every authenticated request (`get_current_user`) | &check; |
| Tenant branding (name, logo, colors) lives on the `tenants` row | &check; |
| Onboarding mirrors `company_name`/`company_logo_url` to `tenants` | &check; |
| Settings &rarr; Company section wired to `GET`/`PATCH /tenants/current` | &check; |
| `tasks.tenant_id` column + repo-level filtering | &check; |
| Invitation API (`POST` / `GET` / `verify` / `accept` / `DELETE`) | &check; |
| Role-cap on invitations (`_PRIVILEGED_INVITE_ROLES`) | &check; |
| RLS policies authored via `auth_tenant_id()` + `auth_is_platform_admin()` | &check; (dormant; **see &sect;4.5.1 for two bugs to fix before activation**) |
| Legacy `tenant-1` backfill helpers (`split_user_to_new_tenant`, `legacy_tenant_users` view) | &check; (installed, not executed) |
| `InviteAcceptPage` at `/invite/accept?token=…` | &check; |
| Test suite: 481 backend, frontend type-check + lint + RegisterPage tests | &check; |

**Note on the dormant RLS migration.** The shipped policy on
`task_templates` excludes system-default rows (`tenant_id IS NULL`), and
the migration has no carveout for the public milestone viewer
(Requirements &sect;9.4a). Both are addressed in a precursor migration
before G2 activation &mdash; see &sect;4.5.1 and &sect;4.5.2.

---

## 3. Gap analysis

Ordered roughly by severity (data-leak / compliance / blocker risk first,
polish last).

| # | Gap | Layer | Severity |
|---|---|---|---|
| G1 | **No frontend UI to create / list / revoke invitations.** API works; product can't drive it. | Frontend | Blocker (product is unusable end-to-end for new tenants beyond a single founder) |
| G13 | **No departed-tenant archive or legal-hold mechanism.** Hard-delete (G5) cannot ship without this or it violates Requirements &sect;6.1 / &sect;10.3 (2-year retention, Indiana audit obligations). | Backend / Compliance | High (compliance blocker for G5) |
| G2 | **RLS policies dormant + two existing bugs:** the `task_templates` policy hides system defaults; no carveout exists for the public milestone viewer. | Backend / DB | High (defense in depth missing; existing bugs would surface the moment any caller switches to the authenticated role) |
| G3 | **No UI for ownership transfer.** API works; owner has no in-app path. | Frontend | High (UX) |
| G4 | **No platform-admin console UI.** Cannot list/suspend tenants from the app. | Frontend | High (operational) |
| G10 | **No per-tenant branded invitation email.** Supabase dashboard templates are project-global &mdash; incompatible with white-label (Requirements &sect;1.5, &sect;9.5). Must go through SendGrid. | Backend | Medium (was Low in v1) |
| G14 | **Invitation URL ignores per-tenant custom domain.** Copy-link uses `FRONTEND_URL` even though Requirements &sect;9.5 promises per-tenant subdomains/custom domains. | Frontend + Backend | Medium |
| G5 | **No tenant hard-delete with cascading cleanup, storage purge, or auth-user enumeration order.** Soft-suspend exists; permanent deletion does not. Depends on G13. | Backend + Frontend | Medium |
| G6 | **Legacy `tenant-1` cohort not migrated.** Function exists; never executed against prod data. | Ops | Medium |
| G7 | **No seat / plan / quota model + grandfathering migration.** Invitations don't check seat availability. Without grandfathering, the seat migration would suspend every existing tenant 14 days after it ships. | Backend | Medium (becomes Blocker the moment monetisation starts) |
| G8 | **Tenant-level audit-log coverage is patchy + cascade-survivable platform audit table missing.** Owner transfer, suspension, member invitations are not always logged; "tenant deleted" cannot be written to `audit_logs` because the cascade drops it. | Backend | Medium |
| G9 | **Invitation resend / extend-expiry endpoints don't exist.** Sole option is delete + re-create. | Backend + Frontend | Low |
| G11 | **No "Team Members" / "Pending Invites" management page.** | Frontend | Bundled with G1 / G3 |
| G12 | **Onboarding flow doesn't differ for invited users vs founders.** Invited users land in the same wizard which asks for company info. | Frontend | Low |

---

## 4. Detailed specs

### 4.1 Invitation management UI (G1, G11)

The single biggest product gap. The API is complete; this is purely frontend
work with one small backend addition (&sect;4.1.6). The shape below is the
canonical pattern; details can flex.

#### 4.1.1 Admin user-management surface

Use the canonical Admin information architecture from Requirements
&sect;10.5 / `FRONTEND_UI_WORKFLOW_LOGIC.md`: `/admin/users` is the primary
surface for team-member and invitation management. `SettingsPage.tsx` may
link to it from the Company / Team settings card, but it must not become a
second, partially overlapping user-management product.

Extend `/admin/users` (or replace the current placeholder page) with:

- **Members table** &mdash; columns: avatar/name, email, role badge, status
  (active / inactive), joined date. Row actions per current-user role:
  - Admin: Change role (opens role-picker), Deactivate, Set as Owner
    (if current user is the existing owner).
  - TeamLead: limited to viewing the team.
  - Other roles: read-only or hidden.
- **Pending invitations table** &mdash; columns: invited email, role badge,
  expires in N hours/days (highlighted &lt; 12 h), invited by. Row actions:
  Revoke, Copy invite link.
- **Invite button** &rarr; opens an "Invite teammate" modal (see 4.1.2).
- **Staff-seat counter** &mdash; "4 / 5 staff seats used" (when the
  seat-limit applies; see &sect;4.6). Counts only paid internal staff roles,
  not Client / FSBO Customer / Vendor portal accounts. Disables internal
  staff-role invites at the cap with a tooltip ("You've reached the staff
  seat limit on the {plan} plan.") while still allowing transaction-scoped
  Client / Vendor / FSBO invites when permitted by role.

Data sources:

- `GET /api/v1/users/` (existing) for members.
- `GET /api/v1/invitations/` (existing) for pending invitations.
- `GET /api/v1/tenants/current` for `plan`, `seat_limit`,
  `staff_seat_count`, lifecycle fields, owner fields, and the resolved
  `invite_base_url` (see &sect;4.12 and &sect;4.13).

Wireframe sketch (text only):

```
Admin &rarr; User Management                    4 / 5 staff seats
  ----------------------------------------------------
  Active members (4)                       [+ Invite]
  ----------------------------------------------------
  Jane Founder   jane@acme.com   Admin       …
  Sam Closer     sam@acme.com    TC          …
  Pat Agent      pat@acme.com    Agent       …
  ----------------------------------------------------
  Pending invitations (2)
  ----------------------------------------------------
  newbie@…       Agent           expires 2d  Revoke | Copy link
  vendor@…       Vendor          expires 6h  Revoke | Copy link
  ----------------------------------------------------
```

#### 4.1.2 Invite teammate modal

Triggered from 4.1.1. Fields:

- **Email** (required, validated)
- **Role** (dropdown &mdash; filtered to roles the inviter is allowed to grant
  per `_PRIVILEGED_INVITE_ROLES`; e.g. an Agent does not see "Admin" in the
  list)
- **Team** (optional, only shown when teams feature is active)
- **Transaction to attach to** (optional, only for Client/Vendor roles)

Submission &rarr; `POST /api/v1/invitations/` &rarr; on success, refresh the
pending-invitations table and toast "Invite sent to {email}."

Failure modes to surface clearly:

- 403 with role-cap message &rarr; show "Only an Admin can invite Admins."
- 409 (existing user) &rarr; "{email} already has an account."
- 409 (staff seat limit) &rarr; "You've reached the staff seat limit on the
  {plan} plan." with an upgrade CTA when paid plans exist. This applies
  only to internal staff roles (`Admin`, `TeamLead`, `Agent`,
  `TransactionCoordinator`, `Attorney`).
- 403 (plan does not allow staff members) &rarr; "The Solo plan does not
  support additional staff members. Upgrade to Team to invite teammates."
  Transaction-scoped Client / FSBO / Vendor portal invites are not staff
  seats and use their own permission checks (see &sect;4.6.6).
- Any other error &rarr; generic with retry CTA.

#### 4.1.3 Pending invitations actions

- **Revoke**: confirm dialog, then `DELETE /api/v1/invitations/{id}`.
  The endpoint keeps the HTTP verb for compatibility but must soft-revoke
  pending invitation rows (`revoked_at`, `revoked_by`) instead of physically
  deleting them. It still deletes the pre-created `auth.users` row when the
  invitation is unused. Used invitations cannot be revoked/deleted; they are
  retained for audit and as the stable target of
  `users.joined_via_invitation_id`.
- **Copy invite link**: copies `${tenant.invite_base_url}/invite/accept?token=${token}`
  to clipboard, where `invite_base_url` is the tenant's resolved white-label
  origin (&sect;4.12 covers the resolution order). The `token` is not
  currently in the `InvitationResponse` schema &mdash; &sect;4.1.6 below adds
  it, gated to the same roles that can create invitations.
- **Resend**: out of scope for v1 (deferred to G9). Workaround: revoke +
  re-create.

#### 4.1.4 Hooks to add

`src/hooks/useInvitations.ts` (new file):

```ts
// Hook signatures (no implementation here — see &sect;6 implementation order)
export function useInvitations() // GET /api/v1/invitations/
export function useCreateInvitation() // POST /api/v1/invitations/
export function useRevokeInvitation() // DELETE /api/v1/invitations/{id}
```

#### 4.1.5 Types to add to `types/api.ts`

```ts
export interface InviteUserRequest {
  email: string
  role: UserRole
  team_id?: string
  transaction_id?: string
}

export interface InvitationResponse {
  id: string
  email: string
  role: UserRole
  team_id: string | null
  transaction_id: string | null
  expires_at: string
  is_used: boolean
  // The raw token, exposed only to inviter-privileged roles
  // (see &sect;4.1.6). Used to build the copy-link affordance.
  token?: string
}
```

#### 4.1.6 Backend change required to support copy-link

`InvitationResponse` in `app/schemas/invitation.py` currently omits `token`.
Add it, but **only return the field to callers that hold an invite-creating
role** (Agent, TeamLead, Admin, platform-admin). Tradeoff worth naming:
embedding the token in the authenticated list response means a compromise
of an inviter's session (XSS, leaked support logs, cached browser response)
hands attackers ready-to-use accept URLs without intercepting email.
That's a real but bounded weakening of the email-bearer model; gating
the field by role keeps the blast radius at roles that could mint
fresh invitations anyway.

Effort: ~10 lines of code + tests asserting:

- `token` is present in the list response for Admin / TeamLead / Agent.
- `token` is absent from any role that cannot create invitations (e.g.
  Client looking at their own invite via a different endpoint, if added
  later).
- `token` is absent from the unauthenticated `verify` endpoint (already
  the case &mdash; just lock it in with a regression test).

#### 4.1.7 Invitee onboarding differentiation (G12)

Today an invited user lands on `/invite/accept`, sets a password, then is
shoved into the same onboarding wizard as founders &mdash; which asks for
"company name." That's wrong for an invitee: their tenant already has a name,
their logo is already set. The wizard should detect that the user joined
via an invitation and:

- Skip the company-name step entirely.
- Show the brokerage's existing branding read-only ("Joining: Acme Realty").
- Keep the personal-profile and email-integration steps.

**Implementation: store the signal, do not infer it.** The v1 of this
section proposed `user.tenant.owner_user_id !== user.id` as the
"invited" flag. That's wrong: after an ownership transfer (&sect;4.2),
the original founder is no longer the owner and would be re-routed
through the company-name step on next login.

Add a `users.joined_via_invitation_id UUID REFERENCES
public.invitation_tokens(id) ON DELETE SET NULL` column. `accept_invitation`
sets it when creating the user profile. Used invitations are retained (see
&sect;4.1.3) so the FK should normally remain populated; `ON DELETE SET NULL`
is only a defensive fallback for operator cleanup.

The wizard reads the persisted signal directly:
`if (user.joined_via_invitation_id)` &rarr; skip company-name. Founders have
`NULL`, transferred owners stay `NULL`, invitees have a value. No heuristic,
no edge case. `UserResponse` and the frontend `User` type must expose the
field; otherwise the UI cannot make the decision without reintroducing a
heuristic.

#### 4.1.8 Test plan

Frontend unit tests (with `vitest` + `msw`):

- Invite modal: role dropdown is filtered for Agent caller; 403 surfaces
  human-friendly text; 409 surfaces "already exists"; 409 (staff seat)
  surfaces the staff-seat-limit copy; 403 (plan) surfaces the upgrade copy.
- Pending invitations table: rendered from mocked GET response; revoke
  optimistically removes the row.
- Copy-link uses `tenant.invite_base_url`, not a global env var.

Backend regression for &sect;4.1.6: assert `token` field is present in the
list response for invite-creating roles, absent from any path callable by
roles outside the invite-creating set (`_PRIVILEGED_INVITE_ROLES` plus
`AGENT`), and absent from `verify`.

Backend regression for &sect;4.1.7: assert `accept_invitation` writes
`joined_via_invitation_id` on the user profile.

---

### 4.2 Owner transfer UI (G3)

Surfaces the `POST /tenants/current/transfer-ownership` endpoint that already
exists.

#### 4.2.1 Where it lives

Admin &rarr; User Management &rarr; member row action menu &rarr; "Set as
owner." A Settings shortcut may deep-link here, but the action should live
with the rest of user management. Only visible when the current user is
themselves the tenant owner (`user.id === tenant.owner_user_id`). This
requires `TenantResponse.owner_user_id` to be exposed to the frontend.

#### 4.2.2 Flow

1. Click "Set as owner" on a target member.
2. Confirm dialog (copy must reflect the actual side effects):

   > Transfer ownership of {tenant.name} to {target.full_name}?
   >
   > {target.full_name} is currently **{target.role}**. As the new owner,
   > they will be promoted to **Admin**. You will stay as an Admin and lose
   > owner-only abilities (schedule deletion, transfer ownership again).
   >
   > This action is logged.

   When `target.role === 'admin'` already, the second paragraph drops the
   "promoted to Admin" sentence.

3. POST the API.
4. On success, refetch tenant + members, show "Ownership transferred to
   {target.full_name}."
5. The previous owner's UI updates &mdash; they no longer see the "Set as
   owner" option, the schedule-deletion CTA in Danger Zone (&sect;4.4.5), or
   the cancel-deletion banner action.

#### 4.2.3 Edge cases

- Target is currently inactive &rarr; API returns 400 ("inactive"). Show that.
- Target is in a different tenant &rarr; impossible from the UI (selector
  only shows tenant members) but API guards anyway.
- Target's role auto-promotion races with a concurrent role change &rarr;
  the API's auto-promote is a single UPDATE; the last write wins. The UI
  refetches after success so the displayed role is authoritative.
- Network failure mid-transfer &rarr; idempotent: the API is a single update,
  retry safe.

---

### 4.3 Platform-admin console (G4)

A separate route at `/platform/tenants`, gated by `is_platform_admin`. Two
sub-views.

#### 4.3.1 Tenant list (`/platform/tenants`)

- Table: id, name, slug, owner, member count, active/suspended,
  legal-hold indicator, deletion-scheduled date if any, created_at.
- Filter: active / suspended / scheduled-for-deletion / legal-hold / all.
- Row actions: View details, Suspend (toggle), Schedule deletion,
  Cancel deletion (when scheduled), Set/clear legal hold.

Data source: `GET /api/v1/tenants` (already platform-admin only).

#### 4.3.2 Tenant detail (`/platform/tenants/{id}`)

- Header: name, slug, owner, legal-hold badge if set.
- Sections: members list, recent audit events (from `audit_logs` while
  tenant exists; from `platform_audit` for cross-tenant lifecycle events),
  plan/usage (when G7 lands).
- Actions: Edit (uses `PUT /tenants/{id}`), Suspend / Reactivate (uses
  `is_active` toggle), Schedule deletion / Cancel deletion (uses the
  new endpoints in &sect;4.4), Set legal hold / Clear legal hold (new
  endpoints in &sect;4.11.2), Delete (only when scheduled deletion has
  fired and the tenant row is still present &mdash; soft fallback).

#### 4.3.3 Permission hiding

The whole `/platform/*` route tree is hidden from non-platform-admins. Add a
`PlatformAdminGuard` component (mirror of existing role guards) that 404s
non-platform users so the route doesn't even leak its existence.

---

### 4.4 Tenant hard-delete with cascading cleanup (G5)

Currently `DELETE /api/v1/tenants/{id}` sets `is_active = false`. Real
deletion requires several pieces that the v1 of this section missed
(cascade order, storage purge, retention archive, legal-hold gating).
This depends on G13 / &sect;4.11 landing first.

#### 4.4.1 New endpoint: `POST /tenants/current/schedule-deletion`

- Owner-only.
- Sets `tenants.deletion_scheduled_at = now() + grace_period_days`.
- **Leaves `is_active = true`.** Schedule-deletion is not suspension &mdash;
  members must still be able to log in to cancel.
- Optionally takes a `reason` string for the audit log.
- Returns the scheduled date.
- Refuses (409) if `tenants.legal_hold = true`. See &sect;4.11.2.

#### 4.4.2 New endpoint: `POST /tenants/current/cancel-deletion`

- Owner-only, valid only when `deletion_scheduled_at IS NOT NULL`.
- Clears the column.
- **Stuck-state carveout.** A tenant that is both suspended
  (`is_active = false`) *and* scheduled for deletion blocks its owner
  from logging in to cancel because the suspension guard in
  `get_current_user` fires first. For that combination, only platform
  admins can cancel via `POST /platform/tenants/{id}/cancel-deletion`.
  The owner-facing endpoint returns a 403 with copy directing them to
  platform support.

#### 4.4.3 Cron / scheduled task

A new cron entry that processes tenants matching
`deletion_scheduled_at < now() AND legal_hold = false`. **Per tenant,
the runner must create a durable deletion run before any live rows are
removed.** In-memory enumeration is not enough: once `public.users`,
`documents`, and `tenants` are gone, the next cron tick cannot rediscover
which `auth.users` rows or storage blobs still need cleanup.

New durable table:

```sql
CREATE TABLE public.tenant_deletion_runs (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id              UUID NOT NULL,             -- snapshot, not FK
    tenant_slug            TEXT,
    status                 TEXT NOT NULL DEFAULT 'pending',
    retention_anchor_at    TIMESTAMPTZ,
    purge_after            TIMESTAMPTZ,
    auth_user_ids          UUID[] NOT NULL DEFAULT '{}',
    storage_manifest       JSONB NOT NULL DEFAULT '[]'::jsonb,
    tenant_snapshot        JSONB NOT NULL,
    delete_started_at      TIMESTAMPTZ,
    live_rows_deleted_at   TIMESTAMPTZ,
    storage_purged_at      TIMESTAMPTZ,
    auth_users_purged_at   TIMESTAMPTZ,
    completed_at           TIMESTAMPTZ,
    last_error             TEXT,
    retry_count            INTEGER NOT NULL DEFAULT 0,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tenant_deletion_runs_tenant
    ON public.tenant_deletion_runs (tenant_id);
CREATE INDEX idx_tenant_deletion_runs_status
    ON public.tenant_deletion_runs (status);
```

Runner order:

1. **Acquire a tenant-level lock.** Use `FOR UPDATE SKIP LOCKED` on the
   eligible `tenants` row so two cron workers cannot process the same
   tenant.
2. **Enumerate and persist the manifest.** Before deleting rows, write or
   reuse one `tenant_deletion_runs` row containing:
   - `auth_user_ids` &mdash; all `auth.users.id` values joined via
     `public.users` for this tenant.
   - `storage_manifest` &mdash; bucket/path pairs for `documents.storage_path`,
     `tenants.logo_url` / logo storage keys, generated export files, and any
     other tenant-scoped storage references.
   - `tenant_snapshot` &mdash; tenant row plus enough user/member metadata to
     answer who/when questions after the tenant row disappears.
   - `retention_anchor_at` &mdash; `MAX(users.last_login_at)` for the tenant,
     falling back to tenant/user creation time only when no login was ever
     recorded.
   - `purge_after` &mdash; `retention_anchor_at + interval '2 years'` so the
     archive follows Requirements &sect;6.1 / &sect;10.3. Physical purge still
     runs on the quarterly cadence in &sect;4.11.
3. **Archive to platform-level retention** (&sect;4.11). Write
   `audit_logs`, `communication_logs`, and a `full_export` record into
   `platform_archive` using the deletion run's `retention_anchor_at` and
   `purge_after`. Encrypted PII columns are archived **as ciphertext**.
4. **Write `tenant_deletion_started` to `platform_audit`.** This row has no
   FK back to `tenants`, so a crash after live-row deletion still leaves an
   operator-visible lifecycle event and a durable manifest to resume from.
5. **Delete database rows in an explicit FK-aware order.** The service should
   maintain an inventory derived from the migrations/RLS table list, not an
   ad hoc "every table with `tenant_id`" loop. Current order:
   - Soft-revoked/pending `invitation_tokens`.
   - `communication_export_requests`, `audit_logs`, `communication_logs`.
   - `transaction_field_corrections` and other transaction child tables added
     by later milestones.
   - `transaction_assignments`, `transaction_parties`, `tasks`.
   - `documents` after first clearing or child-first deleting tenant-local
     `documents.parent_id` links.
   - `transactions`.
   - `task_templates` where `tenant_id = tenant.id` after tasks are gone
     (never delete `tenant_id IS NULL` system templates).
   - `confidence_settings`, `advertising_hooks`, `vendors`.
   - `integrations` joined through tenant users.
   - `contacts`.
   - Break cyclic user/team references by setting `users.team_id = NULL`
     and `teams.lead_user_id = NULL`, then delete `teams`.
   - Delete `users`.
   - Delete the `tenants` row.
6. **Mark `live_rows_deleted_at`.** From this point forward, retries use the
   deletion run manifest, not live tenant tables.
7. **Storage purge.** Remove every bucket/path in `storage_manifest`.
   Missing paths count as success. Transient failures leave the run in
   `storage_pending` and retry from the manifest on the next cron tick.
8. **`auth.users` purge.** Delete every `auth_user_id` in the manifest.
   Missing auth users count as success. Permanent failures move the run to
   `needs_operator`.
9. **Write completion events.** Write `tenant_deletion_executed` when live
   rows are gone and `tenant_purge_completed` when storage/auth cleanup is
   complete. Both go to `platform_audit`.

Idempotency: every step after manifest creation is keyed by
`tenant_deletion_runs.id` and can be retried. The tenant row disappearing is
no longer a one-way loss of retry information.

#### 4.4.4 New schema columns

```sql
ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS deletion_scheduled_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS grace_period_days INTEGER NOT NULL DEFAULT 30,
    ADD COLUMN IF NOT EXISTS legal_hold BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS legal_hold_reason TEXT;

COMMENT ON COLUMN public.tenants.deletion_scheduled_at IS
    'When the tenant is scheduled to be permanently deleted. The cron picks '
    'up rows past this date and runs the cascading cleanup. Leaves is_active '
    'untouched so the owner can cancel via cancel-deletion. Suspended-AND-'
    'scheduled tenants require platform-admin to cancel.';
COMMENT ON COLUMN public.tenants.legal_hold IS
    'Platform-admin-set flag that blocks scheduling and execution of '
    'tenant deletion, and exempts the tenant''s archive rows from the '
    'retention purge cron. Required for litigation holds, subpoena '
    'response, or regulatory retention obligations.';
```

#### 4.4.5 UI &mdash; Settings &rarr; Danger Zone

- "Delete this organization" button (owner-only).
- Multi-step confirm: type the org name to enable the button.
- After scheduling: a persistent banner on every page
  ("Your organization is scheduled for deletion on {date}. [Cancel deletion]").
- Member logins continue working until the deletion runs &mdash; they see
  the banner.
- If `legal_hold = true`, the button is disabled with copy:
  "This organization is on legal hold and cannot be scheduled for
  deletion. Contact platform support."

#### 4.4.6 Data retention SLA

`grace_period_days` defaults to 30 and is configurable per tenant by
platform admin. After the cascade runs, the platform-level archive
(&sect;4.11) holds the tenant's audit/communication logs and full
export until **2 years after the tenant's last recorded user login**,
matching Requirements &sect;6.1 and &sect;10.3. The deletion run snapshots
`retention_anchor_at = MAX(users.last_login_at)` before users are deleted
and stores the computed `purge_after` in both `tenant_deletion_runs` and
`platform_archive`. Tenants on legal hold are retained indefinitely until
the hold is lifted, even if the normal `purge_after` date has passed.

---

### 4.5 RLS activation: switch backend off `service_role` for user-scoped reads (G2)

The RLS policies authored in `20260511094000_rls_tenant_isolation.sql`
are correct *in shape* but have two existing bugs and a sizable rollout
matrix that the v1 of this section understated. Rewritten below.

#### 4.5.1 Existing bug: `task_templates.tenant_id IS NULL` is hidden under RLS

The shipped policy on `task_templates` reads:

    USING (tenant_id = auth_tenant_id() OR auth_is_platform_admin())

System-wide default templates use `tenant_id IS NULL` per
[SYSTEM_DESIGN.md &sect;2.1 task_templates](velvet-elves-data/SYSTEM_DESIGN.md#L407-L463)
("NULL = system-wide default"). `NULL = uuid` evaluates to `NULL`, not
`TRUE`, so under RLS *every* system-default template disappears from
*every* authenticated user. Task generation will silently fall back to
per-tenant overrides only, which means newly registered tenants have no
template library at all.

Fix in a precursor migration **before** any authenticated-role pathway
ships:

```sql
DROP POLICY IF EXISTS tenant_isolation ON public.task_templates;
CREATE POLICY tenant_isolation ON public.task_templates
    FOR ALL TO authenticated
    USING (
        tenant_id IS NULL
        OR tenant_id = public.auth_tenant_id()
        OR public.auth_is_platform_admin()
    )
    WITH CHECK (
        tenant_id = public.auth_tenant_id()
        OR public.auth_is_platform_admin()
    );
```

`USING` allows reading system templates; `WITH CHECK` still forbids
non-platform-admins from writing to the `tenant_id IS NULL` slot.

Product clarification: tenant Admins may manage **tenant-wide** defaults, but
they must not mutate global `tenant_id IS NULL` system templates that every
brokerage reads. When an Admin edits a system template, the UI/API should use
a copy-on-write flow: create a tenant-scoped override with
`tenant_id = current_user.tenant_id` and preserve the system template as the
platform default. Any UI copy that currently says tenant Admins edit
"system-wide defaults" should be revised to "tenant defaults" unless the
actor is a platform admin.

#### 4.5.2 Existing gap: public share-token routes

Requirements &sect;9.4a defines `/milestones/:shareToken` as a **public,
unauthenticated** route that must read transaction milestone data.
Anonymous PostgREST calls run as the `anon` role and the current
policies grant no access to `anon`. Two acceptable options:

- **Recommended:** keep public share-token routes on the service-role
  client. The route is gated by a token check in app code; RLS would
  only re-validate the same gate.
- Alternative: narrowly scoped `anon` policies that validate the token
  via a join. More moving parts; only worth it if direct frontend &rarr; DB
  calls are ever needed for share-token flows.

Either way, the share-token route is in the &sect;4.5.3 carveout list.

#### 4.5.3 Service-role carveout &mdash; full list

After activation, `Depends(get_user_supabase)` is the default for new
and existing routers. The following routes/helpers must explicitly keep
`Depends(get_supabase)` (service-role):

- **Cron jobs**: `run_escalations`, tenant deletion runner
  (&sect;4.4.3), trial expiry runner (&sect;4.6.6), retention purge
  runner (&sect;4.11).
- **Webhook handlers**: inbound email dispatch, esign callbacks,
  Stripe webhooks (Phase 5).
- **Auth/registration endpoints** that operate before a user JWT
  exists: `POST /auth/register`, `POST /users/login`.
- **`get_current_user` itself** ([auth.py:42-88](velvet-elves-backend/app/core/auth.py#L42-L88))
  &mdash; runs before the JWT is bound to a PostgREST client; reads
  the user row and tenant row to make the auth decision. Cannot use
  the user-scoped client because the auth decision *is* what binds it.
- **Invitation accept** ([invitations.py:283-360](velvet-elves-backend/app/api/v1/invitations.py#L283-L360))
  &mdash; calls `supabase.auth.admin.update_user_by_id`, which
  requires service-role regardless of RLS.
- **Public share-token routes** (&sect;4.5.2).
- **Platform-admin endpoints** that legitimately operate across
  tenants: `/tenants` list, suspend, schedule-deletion (when called
  by platform-admin), legal-hold mutations.
- **Tenant-admin mutation endpoints until role-aware RLS policies land.**
  The current authenticated RLS policies allow users to update themselves
  but do not let a tenant Admin update/deactivate another user in the same
  tenant. Keep routes such as `PUT /users/{id}/role`, `DELETE /users/{id}`,
  future reactivate endpoints, tenant-wide task-template mutations, and
  ownership-transfer internals on the service-role client while app-level
  RBAC enforces tenant scope. A later hardening pass can replace these with
  role-aware RLS policies or `SECURITY DEFINER` RPCs.
- **Storage upload/download proxies** &mdash; Supabase Storage policies
  are separate from table RLS; service-role is the simplest path for
  v1 here.
- **Helpers that fan out tenant-scoped reads** like
  `list_accessible_transaction_ids` in
  [auth.py:181](velvet-elves-backend/app/core/auth.py#L181) &mdash;
  these accept a `supabase` arg from callers and will need both
  client kinds threaded through.

The sweep is roughly **15 routers + ~6 helper functions**. Closer to
multi-day work than "~15 files."

#### 4.5.4 FastAPI dependency

```python
# Pseudo-code; verify actual signatures in supabase_client.py before
# writing. The production shape may differ — see &sect;4.5.5.
async def get_user_supabase(
    token: str = Depends(oauth2_scheme),
) -> AsyncClient:
    """Per-request anon-key client bound to the caller's JWT. Queries
    run as the ``authenticated`` Postgres role so RLS policies apply.
    """
    settings = get_settings()
    client = await acreate_client(
        settings.supabase_url,
        settings.supabase_anon_key,
    )
    await client.postgrest.auth(token)
    return client
```

#### 4.5.5 Performance

`acreate_client` allocates a fresh HTTPX session per request and the
supabase-py async client is not designed for per-request lifecycle.
Before committing to this shape, evaluate:

- **Header-injection wrapper** around a single shared anon client.
  Override the `Authorization` header per call. Avoids per-request
  client construction entirely.
- **JWT-keyed client pool** with a short TTL (e.g. 5 min). Caps total
  client count; risks staleness if a user's tenant_id changes
  mid-session.

Pick whichever benchmarks cleanest in dev with realistic concurrent
request counts. The pseudo-code above is the simplest shape, not
necessarily the production shape.

#### 4.5.6 Test impact

The v1 of this section said "the mock applies to both clients, so most
tests stay." That's wrong. Once routers depend on `get_user_supabase`,
every test currently overriding `get_supabase` needs a parallel
override for `get_user_supabase`. Roughly the entire user-scoped test
suite needs a sweep &mdash; mechanical but non-trivial (~half a day).

Add an integration-test lane that runs the migrations against a local
Postgres so RLS correctness is actually exercised, not just inferred.
The current mock client doesn't execute policies, so the 481 passing
tests tell you nothing about RLS behavior. The Supabase CLI's local
stack (Docker) is the simplest path. This is its own deliverable;
budget half a day for the lane setup plus a focused integration suite
covering: cross-tenant denied; same-tenant allowed; platform-admin
exempt; system-default `task_templates` readable; share-token route
works.

#### 4.5.7 Rollback path

A **request-level** feature flag (not startup-only, which the v1
proposed) so a single bad endpoint can be reverted without redeploying:

```python
async def get_user_supabase_or_service(
    token: str = Depends(oauth2_scheme),
) -> AsyncClient:
    if settings.use_user_scoped_supabase:
        return await get_user_supabase(token)
    return await get_supabase()
```

Granularity at the dependency level lets the flag be flipped per
deployment; per-endpoint overrides can be added later if needed.

#### 4.5.8 Effort: L

Multi-day work. The plan should treat this as its own milestone, last
in the implementation order, with the precursor migration (&sect;4.5.1
+ &sect;4.5.2 documentation) shipping a week earlier so the policy
fixes are in prod before any caller starts running as `authenticated`.

---

### 4.6 Staff-seat / plan model (G7)

Even before billing, modelling staff seats prevents abuse (a free tenant
inviting 1000 internal users) and creates the lever monetisation will pull.
Seats are **not** the same as all authenticated users. Client, FSBO Customer,
and Vendor portal accounts are customer/counterparty access, often
transaction-scoped, and must not consume paid staff seats.

#### 4.6.1 Seat cohort definition

Billable staff roles:

```text
Admin, TeamLead, Agent, TransactionCoordinator, Attorney
```

Non-seat portal roles:

```text
Client, ForSaleByOwner, Vendor
```

Rules:

- `staff_seat_count_active`: active `users` in a billable staff role.
- `staff_seat_count_pending`: unused, unrevoked, unexpired invitations for a
  billable staff role.
- Expired invitations and revoked invitations do not count.
- Deactivated staff users do not count until reactivated.
- Client / FSBO / Vendor invites are still permission-checked and should
  usually require `transaction_id`, but they do not count against
  `seat_limit`.

This distinction must be visible in UI copy: "staff seats," not "members,"
when referring to the paid cap.

#### 4.6.2 New columns on `tenants`

Do not rely on a migration default that accidentally applies trial expiry to
existing tenants. Add nullable columns first, backfill existing tenants, then
set defaults for future inserts:

```sql
BEGIN;

ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS plan TEXT,
    ADD COLUMN IF NOT EXISTS seat_limit INTEGER,
    ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMPTZ;

-- Grandfather every tenant that existed before seats shipped.
UPDATE public.tenants
   SET plan = COALESCE(plan, 'enterprise'),
       seat_limit = NULL,
       trial_ends_at = NULL
 WHERE created_at < statement_timestamp()
   AND plan IS NULL;

ALTER TABLE public.tenants
    ALTER COLUMN plan SET DEFAULT 'trial',
    ALTER COLUMN plan SET NOT NULL,
    ALTER COLUMN seat_limit SET DEFAULT 5,
    ALTER COLUMN trial_ends_at SET DEFAULT (now() + interval '14 days');

COMMIT;
```

`TenantRepository.provision_for_self_registration` should also set
`plan='trial'`, `seat_limit=5`, and `trial_ends_at=now()+14 days`
explicitly so tests and local fixtures do not depend on database defaults.

Initial plan tiers (no billing yet):

| Plan | Default staff `seat_limit` | Trial | Notes |
|---|---|---|---|
| `trial` | 5 | 14 days | Founder staff seat counts toward the cap. |
| `solo` | 1 | n/a | Founder only for internal staff; transaction-scoped portal invites still allowed. |
| `team` | 25 | n/a | |
| `enterprise` | NULL (unlimited) | n/a | Grandfathered default for existing tenants. |

#### 4.6.3 Seat-check on invitation create &mdash; transactional

`POST /api/v1/invitations/` adds a precondition only when the invited role is
in the billable staff cohort. To avoid a read-then-write race between two
simultaneous staff invites, the check runs inside a transaction with a
row-level lock on the tenant. PostgREST doesn't expose explicit transactions,
so the seat check is implemented as a single SQL function.

Security requirements for the SQL function:

- `SECURITY DEFINER SET search_path = public, pg_temp`.
- `REVOKE ALL ON FUNCTION ... FROM PUBLIC, anon, authenticated`; grant only to
  `service_role` unless/until a direct PostgREST caller is deliberately
  supported.
- Validate `p_invited_by` belongs to `p_tenant_id`.
- Validate `p_team_id` and `p_transaction_id`, when present, belong to the
  same tenant.
- Validate `p_role` is one of the supported `UserRole` values.
- Enforce staff-seat limits only when `p_role` is in the billable staff role
  set.

```sql
CREATE OR REPLACE FUNCTION public.create_invitation_with_seat_check(
    p_tenant_id UUID,
    p_invited_by UUID,
    p_email TEXT,                  -- already Fernet-encrypted by caller
    p_role TEXT,
    p_team_id UUID,
    p_transaction_id UUID,
    p_expires_at TIMESTAMPTZ
) RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_seat_limit INTEGER;
    v_plan TEXT;
    v_is_staff_role BOOLEAN;
    v_active_count INTEGER;
    v_pending_count INTEGER;
    v_new_id UUID;
BEGIN
    IF p_role NOT IN (
        'Admin', 'TeamLead', 'Agent', 'TransactionCoordinator',
        'Attorney', 'Client', 'ForSaleByOwner', 'Vendor'
    ) THEN
        RAISE EXCEPTION 'invalid_invitation_role' USING ERRCODE = 'P0003';
    END IF;

    SELECT seat_limit, plan INTO v_seat_limit, v_plan
      FROM public.tenants
     WHERE id = p_tenant_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'tenant_not_found' USING ERRCODE = 'P0004';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM public.users
         WHERE id = p_invited_by
           AND tenant_id = p_tenant_id
           AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION 'inviter_not_in_tenant' USING ERRCODE = 'P0005';
    END IF;

    IF p_team_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.teams
         WHERE id = p_team_id AND tenant_id = p_tenant_id
    ) THEN
        RAISE EXCEPTION 'team_not_in_tenant' USING ERRCODE = 'P0006';
    END IF;

    IF p_transaction_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.transactions
         WHERE id = p_transaction_id AND tenant_id = p_tenant_id
    ) THEN
        RAISE EXCEPTION 'transaction_not_in_tenant' USING ERRCODE = 'P0007';
    END IF;

    v_is_staff_role := p_role IN (
        'Admin', 'TeamLead', 'Agent', 'TransactionCoordinator', 'Attorney'
    );

    IF v_is_staff_role AND v_plan = 'solo' THEN
        RAISE EXCEPTION 'plan_does_not_allow_staff_members'
            USING ERRCODE = 'P0001';
    END IF;

    IF v_is_staff_role AND v_seat_limit IS NOT NULL THEN
        SELECT COUNT(*) INTO v_active_count
          FROM public.users
         WHERE tenant_id = p_tenant_id
           AND is_active = TRUE
           AND role IN (
               'Admin', 'TeamLead', 'Agent',
               'TransactionCoordinator', 'Attorney'
           );

        SELECT COUNT(*) INTO v_pending_count
          FROM public.invitation_tokens
         WHERE tenant_id = p_tenant_id
           AND is_used = FALSE
           AND revoked_at IS NULL
           AND expires_at > now()
           AND role IN (
               'Admin', 'TeamLead', 'Agent',
               'TransactionCoordinator', 'Attorney'
           );

        IF v_active_count + v_pending_count >= v_seat_limit THEN
            RAISE EXCEPTION 'seat_limit_reached'
                USING ERRCODE = 'P0002';
        END IF;
    END IF;

    INSERT INTO public.invitation_tokens (
        tenant_id, invited_by, email, role, team_id, transaction_id,
        token, expires_at
    ) VALUES (
        p_tenant_id, p_invited_by, p_email, p_role, p_team_id,
        p_transaction_id, gen_random_uuid()::TEXT, p_expires_at
    ) RETURNING id INTO v_new_id;

    RETURN v_new_id;
END$$;

REVOKE ALL ON FUNCTION public.create_invitation_with_seat_check(
    UUID, UUID, TEXT, TEXT, UUID, UUID, TIMESTAMPTZ
) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.create_invitation_with_seat_check(
    UUID, UUID, TEXT, TEXT, UUID, UUID, TIMESTAMPTZ
) TO service_role;
```

The router (`app/api/v1/invitations.py`) calls this via
`supabase.rpc("create_invitation_with_seat_check", ...)` and maps:

- `P0001` &rarr; 403 with the plan-feature staff message.
- `P0002` &rarr; 409 with the staff-seat-limit message.
- `P0003`..`P0007` &rarr; 400 / 403 according to the validation failure.

#### 4.6.4 Reactivation and role-change path

Any route that changes a user's role into the billable staff cohort or
reactivates a billable staff user must run the same locked seat check.
Otherwise deactivate-then-reactivate, or Client-to-Agent role changes, become
back doors past the cap. Implement a sibling RPC such as
`assert_staff_seat_available_for_user(p_tenant_id, p_user_id, p_new_role)`.

#### 4.6.5 Platform-admin can override

`PUT /tenants/{id}` accepts `seat_limit`, `plan`, and `trial_ends_at` updates
from platform admin only. Changes are logged to `platform_audit`.

#### 4.6.6 Trial expiry

Cron job: when `trial_ends_at < now() AND plan = 'trial' AND legal_hold = false`,
set `tenants.is_active = false`. The existing `get_current_user`
suspension guard takes it from there. Members see a banner directing
them to upgrade. Out of scope for v1: the actual upgrade flow.

The legal-hold check matters here even though trial expiry doesn't delete
anything &mdash; suspending a tenant under legal hold would block discovery
access. Skipping the suspension while on hold keeps the data accessible to
platform admin without changing the customer's billing posture.

#### 4.6.7 Solo plan semantics

A `solo` tenant has `seat_limit = 1` and the founder already occupies that
staff seat. The seat-check function refuses invitations for additional
billable staff roles with `plan_does_not_allow_staff_members`, so the UI can
surface "upgrade to Team to invite teammates." Transaction-scoped Client /
FSBO / Vendor invites are not staff seats and should remain allowed when the
inviter has normal permission to invite that portal role.

---

### 4.7 Legacy `tenant-1` backfill execution (G6)

The function is installed. To use it:

1. Connect to production DB.
2. `SELECT * FROM public.legacy_tenant_users;` &mdash; review the cohort. Decide
   per-user whether they were genuine co-workers or stray test/orphan accounts.
3. For each user that should be re-sharded:
   `SELECT public.split_user_to_new_tenant('<user_uuid>', '<their tenant name>');`
4. After all splits, the residual `tenant-1` tenant either gets re-purposed
   (renamed to a real org if a legitimate brokerage remains) or deactivated.
5. **Force session invalidation** for affected users so the new
   `tenant_id` is read on next request. The current
   `auth_tenant_id()` function reads from `public.users` per request
   so JWTs themselves don't need re-issuing, but any in-memory caches
   keyed on tenant_id (none today, watch for any added) need
   clearing.

The decision in step 2 is environment-specific and cannot be safely
automated. Document it as an operator runbook, not a migration.

This must run **before** G2 (RLS activation). Once RLS is live, the
legacy-tenant-1 cohort with multiple disjoint owners in the same
tenant will trip cross-tenant visibility checks for users whose data
no longer matches their auth context.

---

### 4.8 Tenant-level audit-log coverage (G8)

Today `AuditService` writes to `audit_logs`, which has `NOT NULL` FKs
to both `tenants(id)` and `users(id)`. The v1 spec missed two
sequencing problems.

#### 4.8.1 Tenant created (founder signup) &mdash; ordering

`AuthService.register` creates the tenant, then the user, then binds
the founder. The audit rows must wait until both parents exist:

1. INSERT `tenants` (founder's id is in `owner_user_id`).
2. INSERT `users` (matched to `auth.users.id` returned by `sign_up`).
3. INSERT `audit_logs` row for `tenant_created` (entity_type=tenant,
   user_id=founder).
4. INSERT `audit_logs` row for `user_registered` (entity_type=user,
   user_id=founder).
5. INSERT `platform_audit` row for `tenant_created` &mdash; mirror of
   step 3 so the cross-tenant timeline survives a future hard-delete.

#### 4.8.2 Tenant deleted &mdash; `platform_audit` table

The "tenant deleted (executed)" audit can't go in `audit_logs` because
step 3 of the deletion cascade (&sect;4.4.3) drops every row with that
`tenant_id` including the audit log itself, and step 4 drops the FK
target. Add a separate platform-level table:

```sql
CREATE TABLE public.platform_audit (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_user_id   UUID,                  -- nullable: cron has no human actor
    actor_role      TEXT,
    tenant_id       UUID,                  -- not a FK on purpose
    tenant_slug     TEXT,                  -- snapshot at the event
    action          TEXT NOT NULL,
    summary         TEXT,
    payload         JSONB
);

CREATE INDEX idx_platform_audit_tenant ON public.platform_audit (tenant_id);
CREATE INDEX idx_platform_audit_action ON public.platform_audit (action);
```

Cross-tenant lifecycle events go here, **in addition** to a mirror
entry in `audit_logs` while the tenant still exists:

- `tenant_created`, `tenant_suspended`, `tenant_reactivated`
- `tenant_deletion_scheduled`, `tenant_deletion_cancelled`,
  `tenant_deletion_executed`
- `tenant_plan_changed`, `tenant_seat_limit_overridden`
- `tenant_legal_hold_set`, `tenant_legal_hold_cleared`
- `tenant_ownership_transferred`

`platform_audit` has no FK to `tenants` so it survives the cascade.

#### 4.8.3 Per-tenant audit additions

Sprinkle `await audit.log(...)` calls in:

- `app/services/auth_service.py::register` (after both rows exist;
  &sect;4.8.1).
- `app/api/v1/tenants.py::update_current_tenant`,
  `transfer_current_tenant_ownership`, `deactivate_tenant`,
  `schedule_deletion`, `cancel_deletion`,
  `set_legal_hold`, `clear_legal_hold`.
- `app/api/v1/invitations.py::create_invitation`, `accept_invitation`,
  `revoke_invitation`.
- `app/api/v1/users.py::change_user_role`, `deactivate_user`,
  `reactivate_user`.

Each entry: `action`, `entity_type` (`tenant` / `user` / `invitation`),
`entity_id`, `before_state`, `after_state`, `summary`. Cross-tenant
lifecycle events additionally write to `platform_audit` per &sect;4.8.2.

#### 4.8.4 Why this matters

The first time a customer asks "who removed Pat?" or "why was my org
suspended?", the answer needs to exist. The platform-level mirror
matters the first time a regulator or subpoena lands after a tenant
was deleted &mdash; that's compliance, not user-experience.

---

### 4.9 Invitation resend / extend (G9)

Two small backend endpoints + UI affordances:

- `POST /api/v1/invitations/{id}/resend` &mdash; re-runs
  `send_invitation_email` (the SendGrid-backed one per &sect;4.10) for
  the same row. Useful when the inviter knows the recipient didn't
  receive the original.
- `POST /api/v1/invitations/{id}/extend` &mdash; pushes `expires_at`
  forward by another 72h. Owner / inviter only.

UI: row actions in the pending invitations table (&sect;4.1.3).

---

### 4.10 Branded invitation email via SendGrid (G10)

The v1 of this section recommended editing the Supabase project's
invitation template as the "cheapest path." That's wrong:
**Supabase invite templates are global per project, not per-tenant**.
The white-label promise in Requirements &sect;1.5 and &sect;9.5 is
per-tenant logos, colors, and sender names. The two are
fundamentally incompatible.

The mandatory path:

1. Stop using `supabase.auth.admin.invite_user_by_email` (which both
   creates the auth user *and* sends Supabase's generic email).
2. Use `supabase.auth.admin.create_user(email=..., email_confirm=False)`
   to create the auth user without an email send.
3. Render the invitation email in app code with the inviting tenant's
   branding (logo, colors, sender name from `tenants`).
4. Send via the existing SendGrid integration (see
   `SENDGRID_SETTINGS_GUIDE.md` in the backend).

Implementation note: `send_invitation_email` already exists in
`app/services/email_service.py`. The change is: (a) split the auth-user
creation from the email send, (b) move the template into the codebase
where it can read `tenants` at send time, (c) compose the accept URL
from the tenant's resolved `invite_base_url` (&sect;4.12).

Effort: **M** (was S in v1). This is not dashboard-only.

Phased rollout option: ship the SendGrid path behind a feature flag
`USE_BRANDED_INVITE_EMAIL` so the Supabase fallback remains available
during the first week in prod.

---

### 4.11 Departed-tenant archive and legal hold (G13) &mdash; NEW

Hard-deleting a tenant (&sect;4.4) immediately destroys
`communication_logs` and `audit_logs` for that tenant. Two project
constraints make the v1 cascade unacceptable as-shipped:

- Requirements &sect;6.1: communication logs must be retained for
  **2 years from last user login**.
- Requirements &sect;10.3: Indiana broker compliance requires
  "non-destructive history" and 2-year audit retention.

The &sect;4.4 cascade satisfies the customer-facing "delete my data"
ask, but a subpoena landing on day 31 must still be answerable.

#### 4.11.1 New table: `platform_archive`

```sql
CREATE TABLE public.platform_archive (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL,                   -- snapshot, not FK
    tenant_slug       TEXT,
    archived_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    retention_anchor_at TIMESTAMPTZ NOT NULL,          -- max last login snapshot
    purge_after       TIMESTAMPTZ NOT NULL,            -- anchor + 2 years
    record_type       TEXT NOT NULL,                   -- 'audit_log','comm_log','full_export'
    payload           JSONB NOT NULL,                  -- ciphertext PII stays ciphertext
    storage_path      TEXT                             -- optional pointer to S3/Supabase storage
);

CREATE INDEX idx_archive_tenant ON public.platform_archive (tenant_id);
CREATE INDEX idx_archive_purge ON public.platform_archive (purge_after);
```

The cron in &sect;4.4.3 writes archive rows here before the cascade runs.
`retention_anchor_at` and `purge_after` come from the durable
`tenant_deletion_runs` manifest. A separate retention-purge cron deletes
archive rows past `purge_after` on the quarterly cadence, **excluding**
rows whose tenant has an active platform legal hold (see &sect;4.11.2).

Retention purge must cover both states:

- **Live tenants:** purge eligible `communication_logs` / `audit_logs` only
  when the tenant has no active legal hold and the tenant's max
  `users.last_login_at` is more than 2 years old. This is a quarterly
  compliance job, not a request-path behavior.
- **Departed tenants:** purge eligible `platform_archive` rows when
  `purge_after < now()` and there is no active platform legal hold for that
  `tenant_id`.

**PII handling.** Fernet-encrypted columns are archived **as
ciphertext**. The current Fernet key is platform-scoped, so the
ciphertext is decryptable for legitimate compliance response without
any further key management. If a future iteration moves to
tenant-scoped keys, the archive must either retain a key reference
or shift to plaintext at archive time (with the obvious sensitivity
tradeoff) &mdash; this is open decision #9 in &sect;7.

#### 4.11.2 Legal hold

`tenants.legal_hold` and `tenants.legal_hold_reason` columns are
added in the &sect;4.4.4 migration as the live-tenant convenience flags.
Add a separate platform-level hold table with no FK back to `tenants` so
hold state can survive hard-delete and can be audited even after the tenant
row is gone:

```sql
CREATE TABLE public.platform_legal_holds (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,          -- snapshot, not FK
    tenant_slug     TEXT,
    set_by          UUID,
    set_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason          TEXT NOT NULL,
    cleared_by      UUID,
    cleared_at      TIMESTAMPTZ,
    clear_reason    TEXT
);

CREATE INDEX idx_platform_legal_holds_tenant
    ON public.platform_legal_holds (tenant_id);
CREATE INDEX idx_platform_legal_holds_active
    ON public.platform_legal_holds (tenant_id)
    WHERE cleared_at IS NULL;
```

When a hold is set, update `tenants.legal_hold = true` and insert an active
`platform_legal_holds` row. When a hold is cleared, update
`tenants.legal_hold = false` and set `cleared_at` / `cleared_by` on the active
platform hold row. The retention-purge cron checks both the live tenant flag
and active `platform_legal_holds` rows.

When `legal_hold = true` or an active platform hold exists:

- `POST /tenants/current/schedule-deletion` refuses with 409.
- The tenant-deletion cron (&sect;4.4.3) skips any tenant with
  `legal_hold = true`.
- The trial-expiry cron (&sect;4.6.6) skips suspension for tenants
  with `legal_hold = true`.
- The retention-purge cron skips live rows or archive rows whose `tenant_id`
  has an active platform hold.

Setting or clearing the hold is platform-admin-only via
`POST /platform/tenants/{id}/legal-hold` (body: `{ reason }`) and
`DELETE /platform/tenants/{id}/legal-hold` (body: `{ reason }`). Both write
to `platform_audit` with the actor's user id and the reason.

#### 4.11.3 Retention SLA summary

| State | Tenant data | Archive |
|---|---|---|
| Active tenant | Live in primary tables | None |
| Suspended (`is_active=false`) | Live in primary tables | None |
| Schedule-deletion (T+0 &rarr; T+grace) | Live; banner in UI | None until cron runs |
| Cron-executed deletion | Removed | Written, retained until 2 years after last recorded login |
| Legal hold (any state) | Frozen &mdash; no scheduled deletion | Frozen &mdash; no purge |

---

### 4.12 White-label invitation URL (G14) &mdash; NEW

Requirements &sect;9.5 promises per-tenant custom domain or
subdomain. The v1 of &sect;4.1.3 built the copy-link URL as
`${FRONTEND_URL}/invite/accept?token=…` &mdash; a single env var that
ignores the white-label boundary. An invite sent under
`acmerealty.velvet-elves.com` must not land users on
`www.velvet-elves.com`.

#### 4.12.1 Resolution order

When building the link (frontend) or the SendGrid email (&sect;4.10
backend), resolve the base URL in this order:

1. `tenants.domain` if set and DNS-verified.
2. `tenants.slug + '.' + APP_BASE_DOMAIN` if subdomain mode is enabled.
3. `FRONTEND_URL` fallback (platform default).

The current schema uses `tenants.domain`; do not introduce a parallel
`custom_domain` column. Add verification metadata instead:

```sql
ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS domain_status TEXT NOT NULL DEFAULT 'unverified',
    ADD COLUMN IF NOT EXISTS domain_verified_at TIMESTAMPTZ;
```

`domain_status = 'verified'` and `domain_verified_at IS NOT NULL` are required
before the domain wins the resolution order.

#### 4.12.2 API surface

`GET /api/v1/tenants/current` returns a new computed field:

```json
{
  "id": "...",
  "name": "Acme Realty",
  "domain": "acmerealty.velvet-elves.com",
  "domain_status": "verified",
  "invite_base_url": "https://acmerealty.velvet-elves.com",
  ...
}
```

`invite_base_url` is computed server-side using the same resolution
order. The frontend never reconstructs it from parts &mdash; that keeps
DNS-verification logic in one place.

#### 4.12.3 Scope

This same field powers the SendGrid invitation template (&sect;4.10)
so the recipient lands on the inviting brokerage's branded shell
regardless of whether they clicked the email link or the
copy-pasted URL.

### 4.13 API contract surfacing for new UI states &mdash; NEW

Several features above depend on data that currently exists only in backend
models or planned migrations. Ship the response-contract work as a small
precursor before the UI features so frontend code does not fall back to
heuristics.

`TenantResponse` additions:

```ts
owner_user_id: string | null
plan: 'trial' | 'solo' | 'team' | 'enterprise'
seat_limit: number | null
staff_seat_count: number
trial_ends_at: string | null
deletion_scheduled_at: string | null
grace_period_days: number
legal_hold: boolean
legal_hold_reason: string | null
domain: string | null
domain_status: 'unverified' | 'pending' | 'verified' | 'failed'
domain_verified_at: string | null
invite_base_url: string
```

`UserResponse` additions:

```ts
joined_via_invitation_id: string | null
last_login_at: string | null
```

`InvitationResponse` additions:

```ts
token?: string
revoked_at: string | null
revoked_by: string | null
```

Backend files affected: `app/models/tenant.py`, `app/schemas/tenant.py`,
`app/repositories/tenant_repository.py`, `app/models/user.py`,
`app/schemas/user.py`, `app/repositories/user_repository.py`,
`app/models/invitation.py`, `app/schemas/invitation.py`, and
`app/repositories/invitation_repository.py`. Frontend files affected:
`src/types/api.ts`, `src/hooks/useAuth.ts`, and any tenant hook created for
admin/settings pages.

---

## 5. Recommended implementation order

Ordered by **product value per unit of effort, audit/compliance
preconditions, and contract dependencies**, not pure severity. Audit
foundation and response-contract surfacing now come before the UI because
Requirements &sect;10.3 says every mutation must be logged, and the UI needs
owner/lifecycle/seat fields exposed rather than inferred. G13 sits ahead of
G5 because the cascade cannot ship without retention coverage; G10 / G14
piggyback on the invitation UI because they share the same code path; the
RLS-policy fixes in &sect;4.5.1 / &sect;4.5.2 ship as a precursor migration ahead
of G2.

| Order | Item | Effort | Why this slot |
|---|---|---|---|
| 1 | G8 foundation: `platform_audit` table + audit helpers (4.8) | M | Every later tenant/user/invite mutation must log from day one. |
| 2 | API contract surfacing (4.13) + G14 backend URL resolver (4.12) | S/M | UI needs owner/lifecycle/seat/domain fields; copy-link/email must use the server-computed base URL. |
| 3 | G1: Invitation management UI (4.1) + G3: Owner transfer UI (4.2) | M | Unblocks every multi-user brokerage without duplicating `/settings` and `/admin/users` surfaces. |
| 4 | G12: Invitee-specific onboarding via `joined_via_invitation_id` flag (4.1.7) | S | Noticeable UX fix; uses the stored flag, not owner heuristics. |
| 5 | G4: Platform-admin console (4.3) | M | Ops cannot manage tenants today without DB access. Needed before first real customer. |
| 6 | G10: Branded SendGrid invitation email (4.10) | M | Can't ship dashboard-only without breaking white-label. Goes with G14 because both touch invite URLs. |
| 7 | G6: Legacy backfill execution (4.7) | S (ops) | One-time. Must run before G2 / RLS activation. |
| 8 | G7: Staff-seat / plan model + grandfathering migration (4.6) | M | Precondition for monetisation; avoids counting Client / FSBO / Vendor portal accounts as paid staff seats. |
| 9 | G13: `platform_archive`, legal-hold history, retention purge (4.11) | M | Hard compliance precondition for G5. |
| 10 | G5: Tenant hard-delete with durable purge manifest (4.4) | M/L | Required for customer departure; depends on G13 and the manifest table. |
| 11 | G2: RLS activation **with policy fixes precursor** (4.5) | L | Largest change. Keep tenant-admin mutations service-role until role-aware policies/RPCs land. |
| 12 | G9: Resend / extend invitations (4.9) | S | Nice-to-have. |

---

## 6. Test strategy

Each item gets its own test layer:

| Item | Backend tests | Frontend tests | Manual / ops |
|---|---|---|---|
| 4.1 Invitation UI | Existing `test_invitations_api.py` covers API; add tests for `token` field role-gating (4.1.6), soft-revoke fields, `joined_via_invitation_id` write (4.1.7), and staff-seat error mapping (4.6.3) | Vitest: invite modal happy path, role-cap filtering, staff-seat-limit error copy, plan-feature error copy, revoke optimistic update, copy-link uses `tenant.invite_base_url` | Send a real invite via SendGrid; verify branded template lands on the tenant's `invite_base_url`. |
| 4.2 Owner transfer | Existing `test_tenants_api.py` covers API | Vitest: action only visible to owner; confirm-dialog copy includes target's prior role; auto-promote messaging conditional. | Verify after transfer, old owner cannot revoke deletion / transfer / set legal hold. |
| 4.3 Platform-admin console | API already covered | Vitest: route 404s for non-platform users; suspend/schedule-deletion/legal-hold actions wired. | Promote a user to platform admin in DB; verify the console loads and the platform-only cancel-deletion path works for suspended-and-scheduled tenants. |
| 4.4 Hard-delete | New `test_tenant_deletion_api.py`: schedule, cancel, durable `tenant_deletion_runs` manifest, FK-aware cascade order, retry storage/auth purge after live rows are gone, `platform_audit` rows for started/executed/completed, legal-hold blocks schedule | Danger-zone modal flow; legal-hold disables the button. | Run cron on a dev tenant; verify all tenant rows disappear, manifest remains, storage/auth retries work from the manifest, and archive rows were written before cascade. |
| 4.5 RLS activation | Precursor: regression test that `task_templates.tenant_id IS NULL` is readable but copy-on-write prevents tenant Admins from mutating global templates. New integration suite against local Postgres: cross-tenant denied; same-tenant allowed; platform-admin exempt; tenant-admin service-role mutation carveouts still pass; share-token route works via service-role carveout. | n/a | Sanity-check every dashboard widget and admin mutation against staging Supabase. |
| 4.6 Staff seats | `test_invitations_api::test_staff_seat_limit_blocks_staff_invite`, `test_portal_invites_do_not_count_against_staff_seats`, `test_solo_plan_refuses_staff_invite_but_allows_transaction_scoped_portal_invite`, race-condition test using two concurrent `rpc` calls, reactivate-past-cap test, grandfathering migration test verifying existing rows become `enterprise`. | Vitest: staff-seat-limit error and plan-feature error surfacing. | Try two simultaneous staff invites at the limit; verify only one succeeds and portal invites remain allowed. |
| 4.7 Backfill | `split_user_to_new_tenant` already has no test; add one in `test_legacy_backfill.py`. | n/a | Run against a snapshot of production. |
| 4.8 Audit | Repo-level test that each tenant-mutation writes an audit row in `audit_logs` and (for cross-tenant events) `platform_audit`. Test that `tenant_deletion_executed` is written **after** the cascade. | n/a | Spot-check the audit log in dev. |
| 4.9 Resend / extend | `test_invitations_api`: resend re-sends; extend pushes `expires_at`. | Vitest: row-action affordances. | Verify SendGrid doesn't rate-limit consecutive resends. |
| 4.10 SendGrid invite email | `test_email_service.py`: invitation email renders with tenant branding; auth user is created without Supabase's email send; feature flag fallback uses the legacy path. | n/a | QA the rendered HTML in a real inbox. |
| 4.11 Archive + legal hold | `test_platform_archive.py`: archive rows use `retention_anchor_at`; retention-purge cron handles live and departed tenants; active `platform_legal_holds` exempts archive rows from purge; legal-hold blocks schedule-deletion. | Vitest: legal-hold badge and disabled-button copy in admin console. | Set and clear legal hold; verify purge skips while active and resumes only after clear workflow. |
| 4.12 White-label URL | `test_tenants_api::test_invite_base_url_resolution`: verified `domain` > subdomain > fallback; unverified domain is ignored. | Vitest: copy-link uses `tenant.invite_base_url`. | Send invite from tenant with verified custom domain; verify the link in the email matches. |
| 4.13 API contracts | Response-model tests for owner/lifecycle/staff-seat/domain fields on `TenantResponse`, `joined_via_invitation_id` on `UserResponse`, and revoke fields on `InvitationResponse`. | Type-level coverage in consuming hooks/components. | Verify no UI branch infers owner/invite/lifecycle state from heuristics. |

---

## 7. Open decisions

These need a stakeholder call before implementation, listed in the order
they'll bite you:

1. **Plan tiers & default staff-seat limits** (&sect;4.6). The values above
   are guesses. Real numbers depend on what Jake wants to charge for
   and what a typical brokerage looks like. The plan now assumes Client /
   FSBO / Vendor portal accounts are not paid seats; confirm commercially.
2. **Hard-delete grace period** (&sect;4.4.6). 30 days is a starting
   point. Some jurisdictions / customer agreements may require shorter
   or longer.
3. **Trial length** (&sect;4.6.2). 14 days vs 30. Affects funnel math;
   not a technical choice.
4. **Invitation token TTL** (currently 72h). Long enough to survive a
   long weekend? Probably yes. Worth confirming.
5. **Whether to keep `_PRIVILEGED_INVITE_ROLES = {Admin, TeamLead}`** or
   tighten further. E.g. should TeamLead be allowed to invite TeamLeads,
   or should that be Admin-only? Current behaviour allows it.
6. **Same-tenant duplicate-name policy.** Two brokerages can both be
   named "Acme Realty" today (slugs are UUIDs). Is that fine, or should
   the UI surface "an organization with this name already exists" and
   require a confirmation? Technically harmless; commercially might
   matter for trust.
7. **Branded email rollout cadence.** Ship SendGrid path behind a flag
   for the first week (&sect;4.10) or flip directly? Depends on
   confidence in the SendGrid template at GA.
8. **Multi-tenant per user.** Not in scope here, but worth a tracked
   "deferred" decision. The Slack model (one identity, many workspaces
   with a switcher) is the alternative to the current one-tenant-per-user
   model.
9. **Tenant-scoped Fernet keys vs platform-scoped.** The archive in
   &sect;4.11 keeps ciphertext as-is &mdash; correct under a
   platform-scoped key. If a future iteration moves to tenant-scoped
   keys, the archive needs to retain a key reference or migrate to
   plaintext at archive time (with the obvious sensitivity tradeoff).
   Decide before &sect;4.11 ships.
10. **Legal-hold lift workflow.** When a hold is lifted on a tenant
    whose `deletion_scheduled_at` is already in the past, does the
    cascade run immediately on next cron tick, or does the operator
    need to re-schedule? Pick a default that won't surprise the legal
    team.
11. **`auth.users` cleanup retries.** Step 8 of &sect;4.4.3 calls the
    auth admin API per user. With hundreds of users this could take
    seconds and a partial failure leaves orphaned auth rows. The durable
    deletion manifest supports retries, but retry limits, alert thresholds,
    and a daily "orphan auth users" reconciler still need a product/ops call.
12. **Cron primitive.** &sect;4.4.3 (deletion), &sect;4.6.6 (trial
    expiry), and &sect;4.11.1 (retention purge) add three new
    scheduled jobs to whatever the existing `run_escalations` host is.
    Pick a primitive (APScheduler in-process, external worker, Supabase
    pg_cron) before the third job lands; in-process becomes a
    single-point-of-failure quickly.
13. **RLS role-aware mutation strategy.** The safe v1 keeps tenant-admin
    mutation endpoints on service-role with app RBAC. Decide later whether
    to invest in role-aware RLS policies, `SECURITY DEFINER` RPCs, or keep
    the backend-as-policy-enforcer architecture for writes.
14. **Retention minimum after customer-requested deletion.** Requirements say
    2 years from last login. If a tenant's last login is already older than
    2 years when deletion runs, the archive may be purge-eligible on the next
    quarterly job. Confirm whether customer agreements or legal counsel want
    a short post-deletion minimum hold for operational response.
15. **Domain verification workflow.** The plan adds `domain_status` and
    `domain_verified_at`, but the DNS challenge format, certificate issuance,
    and failure/expiry UX need a separate white-label-domain runbook.

---

## 8. File / endpoint inventory for implementers

When a contributor picks up an item, they'll touch the following. Listed so
the diff stays focused.

### 4.1 Invitation UI

- New: `src/hooks/useInvitations.ts`
- New: `src/components/team/TeamMembersTable.tsx`
- New: `src/components/team/InviteUserModal.tsx`
- New: `src/components/team/PendingInvitationsTable.tsx`
- Modify: `src/pages/users/AdminUsersListPage.tsx` (primary `/admin/users`
  surface for members + pending invitations)
- Modify: `src/pages/settings/SettingsPage.tsx` (link to `/admin/users`,
  not a duplicate management surface)
- Modify: `src/types/api.ts` (`InviteUserRequest`, `InvitationResponse`,
  `TenantResponse` with `invite_base_url`)
- Modify: `app/schemas/invitation.py` (role-gated `token` field,
  `revoked_at`, `revoked_by`)
- New migration: `20260XXX_users_joined_via_invitation.sql` (adds
  `users.joined_via_invitation_id` per &sect;4.1.7)
- New migration: `20260XXX_invitation_soft_revoke.sql` (`revoked_at`,
  `revoked_by`; used invitations are retained)
- Modify: `app/api/v1/invitations.py::accept_invitation` (write the
  new column)

### 4.2 Owner transfer

- Modify: `src/components/team/TeamMembersTable.tsx` (row action in the
  `/admin/users` surface)
- New: `src/hooks/useTransferOwnership.ts`

### 4.3 Platform-admin console

- New: `src/pages/platform/TenantsPage.tsx`
- New: `src/pages/platform/TenantDetailPage.tsx`
- New: `src/components/platform/PlatformAdminGuard.tsx`
- Modify: `src/App.tsx` (route)
- Modify: `src/utils/constants.ts` (route constants)
- New: `app/api/v1/platform_tenants.py` (legal-hold endpoints,
  platform-admin cancel-deletion path)

### 4.4 Hard-delete

- New migration: `20260XXX_tenant_deletion_and_legal_hold.sql`
  (`deletion_scheduled_at`, `grace_period_days`, `legal_hold`,
  `legal_hold_reason`)
- New migration: `20260XXX_tenant_deletion_runs.sql`
  (`tenant_deletion_runs` durable purge manifest)
- Modify: `app/api/v1/tenants.py` (schedule + cancel endpoints)
- New: `app/services/tenant_deletion_service.py` (cascading cleanup
  with durable manifest + FK-aware order from &sect;4.4.3)
- New: cron entry alongside `run_escalations`
- New: `src/components/settings/DangerZone.tsx`

### 4.5 RLS activation

- New migration (precursor): `20260XXX_rls_fixes_task_templates_and_share_tokens.sql`
  (task_templates `tenant_id IS NULL` allowance per &sect;4.5.1;
  documentation comment for share-token carveout per &sect;4.5.2)
- Modify: `app/core/supabase_client.py` (add `get_user_supabase`
  factory + `get_user_supabase_or_service` flag dispatcher)
- Modify: `app/core/auth.py` (new dep; keep `get_current_user` on
  service-role)
- Modify: every user-scoped router in `app/api/v1/*.py` (sweep,
  &sim;15 files)
- Modify: every helper in `app/repositories/*` and `app/core/auth.py`
  that accepts a `supabase` arg (~6 helpers)
- Modify: tests that mocked the service-role client &mdash; parallel
  override for `get_user_supabase` (entire user-scoped suite)
- New: `tests/integration/test_rls_policies.py` running against a
  local Postgres / Supabase Docker

### 4.6 Staff seats

- New migration: `20260XXX_tenant_plan_seats_and_grandfather.sql`
  (nullable ALTER + grandfather UPDATE + defaults per &sect;4.6.2)
- New migration: `20260XXX_seat_check_function.sql`
  (`create_invitation_with_seat_check` per &sect;4.6.3, locked down to
  `service_role`)
- Modify: `app/api/v1/invitations.py` (call rpc, map P0001/P0002
  errors)
- Modify: `app/api/v1/users.py::change_user_role`,
  `reactivate_user` (equivalent staff-seat check on reactivation path)
- Modify: `app/schemas/tenant.py` (`plan`, `seat_limit`,
  `staff_seat_count`, `trial_ends_at` on TenantResponse)
- New: `app/services/seat_service.py` (counter helpers shared by
  invitation create and reactivation)
- Modify: `src/components/team/InviteUserModal.tsx` (surface limit
  and plan-feature errors)

### 4.7 Backfill execution

- Ops runbook only. Add: `docs/runbooks/legacy_tenant_backfill.md`.

### 4.8 Audit

- New migration: `20260XXX_platform_audit_table.sql`
  (`platform_audit` per &sect;4.8.2)
- Modify: `app/services/audit_service.py` (helper for tenant entity
  types; new `platform_audit` write helper)
- Sprinkle `await audit.log(...)` / `audit.log_platform(...)` calls
  in:
  - `app/services/auth_service.py::register` (after both rows exist
    per &sect;4.8.1)
  - `app/api/v1/tenants.py::update_current_tenant`,
    `transfer_current_tenant_ownership`,
    `deactivate_tenant`, `schedule_deletion`, `cancel_deletion`,
    `set_legal_hold`, `clear_legal_hold`
  - `app/api/v1/invitations.py::create_invitation`,
    `accept_invitation`, `revoke_invitation`
  - `app/api/v1/users.py::change_user_role`, `deactivate_user`,
    `reactivate_user`
  - `app/services/tenant_deletion_service.py` (writes
    `tenant_deletion_executed` to `platform_audit` after step 4 of
    the cascade)

### 4.9 Resend / extend

- Modify: `app/api/v1/invitations.py` (two new endpoints)
- Modify: `src/components/team/PendingInvitationsTable.tsx`

### 4.10 SendGrid invitation email

- Modify: `app/services/email_service.py::send_invitation_email`
  (render branded template; read `tenants` for sender + colors; use
  resolved `invite_base_url`)
- Modify: `app/api/v1/invitations.py::create_invitation` (call
  `create_user` instead of `invite_user_by_email` when the
  feature flag is on)
- New: `app/templates/invitation_email.html` (or wherever templates
  live)
- Modify: `app/core/config.py` (add `USE_BRANDED_INVITE_EMAIL` flag)

### 4.11 Archive + legal hold

- New migration: `20260XXX_platform_archive_table.sql`
  (`platform_archive` per &sect;4.11.1 with `retention_anchor_at`)
- New migration: `20260XXX_platform_legal_holds.sql`
  (`platform_legal_holds` per &sect;4.11.2)
- New: `app/services/tenant_archive_service.py` (write archive rows;
  step 2 of the &sect;4.4.3 cascade)
- New: `app/services/retention_purge_service.py` (cron-driven
  live/archive purge with active platform-hold checks)
- Modify: `app/api/v1/platform_tenants.py` (legal-hold endpoints per
  &sect;4.11.2)
- New: cron entry for retention purge

### 4.12 White-label URL

- Modify: `app/schemas/tenant.py` (add computed `invite_base_url`)
- Modify: `app/api/v1/tenants.py::get_current_tenant` (resolve the
  field per &sect;4.12.1)
- New migration: `20260XXX_tenant_domain_verification.sql`
  (`domain_status`, `domain_verified_at`)
- Modify: `src/hooks/useTenant.ts` (consume the new field)
- Modify: `src/components/team/PendingInvitationsTable.tsx`
  (copy-link uses the field)
- Modify: SendGrid template render to use the same field

### 4.13 API contract surfacing

- Modify: `app/models/tenant.py`, `app/schemas/tenant.py`,
  `app/repositories/tenant_repository.py`
- Modify: `app/models/user.py`, `app/schemas/user.py`,
  `app/repositories/user_repository.py`
- Modify: `app/models/invitation.py`, `app/schemas/invitation.py`,
  `app/repositories/invitation_repository.py`
- Modify: `src/types/api.ts`, `src/hooks/useAuth.ts`, and tenant/admin hooks

---

## 9. Done definition

The plan is complete when:

- Any tenant Admin can invite, manage, and remove team members entirely
  through the product UI &mdash; no API calls required.
- Owner can transfer ownership and schedule deletion through the
  product UI; cancel-deletion is available to the owner unless the
  tenant is also suspended, in which case the platform admin can
  cancel.
- Platform admin can list, suspend, schedule-delete, set/clear legal
  hold, and view archive entries for departed tenants through the
  product UI.
- RLS policies are live and the backend runs queries as
  `authenticated` for user-scoped requests. The two existing
  policy bugs (system task templates hidden; no share-token carveout)
  are fixed in a precursor migration before activation.
- Staff seats are enforced transactionally (no race-past-cap), expired
  or revoked staff invitations do not count, Client / FSBO / Vendor
  portal invites do not consume paid staff seats, deactivate-then-
  reactivate respects the cap, and existing tenants are grandfathered
  to `enterprise` on the seat migration.
- Trial expiry suspends a tenant automatically; legal hold exempts.
- Every tenant-level mutation writes to `audit_logs`; every
  cross-tenant lifecycle event also writes to `platform_audit`, which
  survives the hard-delete cascade.
- Hard-delete writes a durable `tenant_deletion_runs` manifest with
  `auth.users` ids, storage paths, tenant snapshot, and retention
  anchor **before** live rows disappear; archives audit/communication
  logs and a full export to `platform_archive`; then purges database
  rows, storage blobs, and auth users in retryable stages driven from
  that manifest, refusing entirely when `legal_hold = true`.
- The legacy `tenant-1` cohort has been re-sharded or formally
  retained as a real brokerage **before** RLS activates.
- Invitation emails render with per-tenant branding via SendGrid; the
  Supabase generic template is no longer the user-visible path.
- Invitation copy-links and email accept-URLs use the inviting
  tenant's `invite_base_url`, honouring custom domains and
  subdomains.
- `TenantResponse`, `UserResponse`, and `InvitationResponse` surface the
  owner, lifecycle, seat, domain-verification, invite-origin, and
  revoke metadata required by the UI, so frontend flows do not infer
  those states heuristically.
- New integration tests for RLS pass against a real Postgres,
  including: cross-tenant denied, same-tenant allowed, platform-admin
  exempt, system-default task templates readable, share-token route
  works via service-role carveout.
- Retention-purge cron deletes eligible live/archive rows on the
  quarterly schedule while preserving rows for tenants with active
  legal holds, including departed tenants tracked through
  `platform_legal_holds`.
