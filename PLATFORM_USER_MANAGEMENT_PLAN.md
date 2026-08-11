# Platform User Management: Implementation Plan

**Date:** 2026-08-07. **Rev 2** 2026-08-10 after a full workflow/logic review against `requirements.txt`, `SYSTEM_DESIGN.md`, `FRONTEND_UI_WORKFLOW_LOGIC.md` and the shipped source; corrections marked **[rev2]**. **Rev 3** 2026-08-10: staff-seat enforcement removed from the console after Jan's call that a per-seat cap has no place in a per-transaction billing model, and the seat retirement plus the two security fixes promoted to a **Phase 0 that ships ahead of the console**; corrections marked **[rev3]**.
**Author:** Jan Froben
**Status:** **IMPLEMENTED 2026-08-10** — Phases 0 through 4 built, uncommitted. See §15.
**Surface:** `/platform/users` (platform-admin only, cross-tenant)
**Absorbs and extends:** `/platform/registrations` (`PLATFORM_SIGNUPS_PAGE_PLAN_2026-08-05.md`)

---

## 15. Implementation status (2026-08-10)

All five phases are built and verified. **Uncommitted, and no migration has been
applied to any database** — see "Not done" below before deploying.

**Verification:** backend `1790 passed, 0 failed` (1749 before this work; 41 of
the new tests are in `app/tests/test_platform_users_api.py`), frontend `tsc -b` clean and
`eslint` clean on every touched path, `vite build` exit 0. The one remaining
typecheck error is pre-existing in `vite.config.ts` (a Vitest `test` key on a
`UserConfigExport`), untouched by this work.

| Phase | Scope | State |
|---|---|---|
| 0a | Staff-seat gate retired (`seat_service`, invitations, repo, defaults, migration) | Done |
| 0b | D5 audit `get_for_entity` cross-tenant IDOR; D6 `is_active` mass-assignment | Done |
| 1 | Shared directory loader, `GET /platform/users` + `/{id}`, Directory + detail pages, nav, redirects | Done |
| 2 | Role change, deactivate/reactivate, `log_platform_action_on_tenant`, activity timeline | Done |
| 3 | Deals, workspace billing/ledger, credit adjustment | Done |
| 4 | Password reset, sign-in email change, bulk deactivate | Done |

**Decisions taken during the build, beyond the plan as written:**

* **`ReasonDialog` instead of `useConfirm`.** Every write requires a reason
  (`Field(min_length=3)`) that lands in both audit rows. `useConfirm` is yes/no
  only, so a confirm followed by an empty reason would satisfy the API and
  destroy the value of the trail.
* **Bulk selection clears on filter change, survives pagination.** A sweep may
  legitimately span pages; carrying a selection across a filter change would let
  an operator deactivate accounts no longer on screen.
* **Bulk deactivate takes explicit ids, never a filter.** The bot assessment
  stays advisory, so no heuristic can deactivate a real person nobody reviewed.
* **`/platform/registrations` redirects rather than remaining a page.** Its view
  survives as the `outside` segment. Two implementations of one table drift.
* **The read-only wallet card was folded into `UserBillingSection`**, which
  carries the same "shared by everyone in this workspace" sentence — the one
  line on the detail page that must never be dropped.
* **Email change writes Auth first and rolls it back if the profile write
  fails**, because there is no transaction across Supabase Auth and `users`. A
  failed rollback logs `CRITICAL` with both addresses.
* **Two Phase-3 tests initially asserted absolute balances** and failed:
  `get_or_create_wallet` grants free starter credits on first touch. The tests
  were corrected to assert the delta and the Alice/Bob equality; the product
  behaviour is right and was not changed.

**Not done, and why:**

* **`20260927090000_user_deactivation_stamp.sql` has not been applied** to dev,
  stage or prod. `deactivated_at` / `deactivated_reason` are written by
  `UserRepository.deactivate`, so the migration must land before deploy.
* **No live browser verification.** The local backend points at a Supabase
  project I could not confirm is disposable, and registering accounts would have
  written real rows and potentially sent mail. Everything below the UI is
  covered by the 41 API tests; the pages themselves are verified by typecheck,
  lint and a production build only. Worth a pass on dev before this ships.
* **Nothing is committed.** Per standing practice, Jan commits.

---

## 0. The request, restated

A platform admin needs one console that manages every user account on the platform, across every tenant. Four things were asked for:

1. Everything the current **Platform › Account Registrations** page shows: registration details, profile, activity.
2. **Role modification** for every role type except the platform-admin role itself.
3. **Credit updates** and **transaction history** monitoring.
4. Everything else a real operator needs to actually run the platform day to day.

This plan answers all four from the shipped source, names the files that exist, names the files to create, and calls out seven places where the code as written today will not let a platform admin do the job. Three of those (D5, D6, D7) are defects that should be fixed regardless of whether this console is ever built.

---

## 1. What exists today (read from source, 2026-08-07; re-verified 2026-08-10)

### 1.1 The Account Registrations page

Backend: `velvet-elves-backend/app/api/v1/platform_registrations.py`

| Route | Guard | Purpose |
|---|---|---|
| `GET /api/v1/platform/registrations` | `require_platform_admin` | Every account, every tenant |
| `GET /api/v1/platform/registrations/alert-settings` | `require_platform_admin` | Who is emailed on a new registration |
| `PUT /api/v1/platform/registrations/alert-settings` | `require_platform_admin` | Replace either list whole |

`SignupRow` returns: `user_id`, `email`, `full_name`, `role`, `is_active`, `tenant_id`, `tenant_name`, `tenant_plan`, `tenant_trial_ends_at`, `tenant_is_active`, `joined_via_invitation`, `invited_by_name`, `is_internal`, `last_login_at`, `onboarding_completed`, `deal_count`, `created_at`, `activity_state`, `is_suspected_bot`, `bot_signals`.

`SignupsSummary` returns whole-table figures that deliberately ignore the filters: `total`, `outside`, `new_7d`, `new_24h`, `new_workspaces_7d`, `ever_signed_in`, `suspected_bots`, `genuine_outside`.

Query surface: `segment` (all/founders/invited/outside), `activity` (all/never_signed_in/signed_in/onboarded/has_deals/deactivated), `authenticity` (all/genuine/suspected), `search`, `since`, `until`, `sort` (created/name/workspace/role/joined/activity), `direction`, `limit` (max 1000), `offset`.

Three mechanics in that file are load-bearing and must survive into the new page:

- **`_fetch_all`** walks every table in 1000-row ranges. A single unpaginated `.execute()` silently returns a short page from PostgREST. This is the bug that made the cost console under-count (G-7).
- **`_safe_pii` plus Python-side search.** `users.email` and `users.full_name` are Fernet-encrypted at rest. Search cannot be an SQL `ilike`. Rows are fetched, decrypted, then filtered in Python. Do not "optimize" this into SQL.
- **`_activity_state`** derives the engagement label once, server-side, so the filter, the sort order and the on-screen label cannot disagree. The client renders the string, it never re-derives it. Ordering matters inside it: `deactivated` outranks everything, then `has_deals`, then `never_signed_in`, then `signed_in`, then `onboarded`.

Frontend:

- `velvet-elves-frontend/src/pages/platform/PlatformRegistrationsPage.tsx` (678 lines): KPI strip, controls row, sortable server-side table, page-size select, CSV export that walks the whole filtered list rather than the visible page.
- `velvet-elves-frontend/src/pages/platform/RegistrationAlertsPage.tsx` (288 lines): sub-page reached from the header, not a nav entry.
- `velvet-elves-frontend/src/hooks/usePlatformRegistrations.ts`: `usePlatformRegistrations`, `useFetchAllRegistrations`, `useRegistrationAlertSettings`, `useUpdateRegistrationAlertSettings`, `BOT_SIGNAL_LABELS`.
- Route constants: `src/utils/constants.ts:231-251`. Route tree: `src/App.tsx:891` under `PlatformAdminGuard`. Nav: `src/layouts/AppLayout.tsx:466-479`.

Git state: the base page is committed (`ee9020e feat(platform): add account registrations page`). The alerts sub-page, `src/components/ui/email-list-input.tsx` and the bot-signal work are still uncommitted working-tree changes.

### 1.2 Everything else already built that this page can compose

**Users** (`app/api/v1/users.py`)
- `GET /api/v1/users/` (`require_role(ADMIN, TEAM_LEAD, TRANSACTION_COORDINATOR)`): tenant-scoped roster.
- `GET /api/v1/users/{user_id}` (`require_role(ADMIN)` plus `require_tenant_access`).
- `PUT /api/v1/users/{user_id}/role` (`require_role(ADMIN)`): owner lock, self-relabel bounded by `SELF_SIGNUP_ROLES_NOW`, seat guard via `SeatService.assert_staff_seat_available`, audited as `user_role_changed`.
- `DELETE /api/v1/users/{user_id}` (`require_role(ADMIN)`): deactivate, refuses self and refuses the tenant owner, audited as `user_deactivated`.
- `PATCH /api/v1/users/me`: the only path that changes an email address, and it does the two writes that matter, `supabase.auth.admin.update_user_by_id({email, email_confirm: True})` plus the encrypted `users.email` column, with a 409 on collision.

**Session enforcement** (`app/core/auth.py`) **[rev2, and this changes several decisions below]**
`get_current_user` re-reads the user row on **every request** and raises 403 "Account is inactive" when `is_active` is false (line 76), and 403 when the tenant is deactivated (line 83). Deactivation therefore takes effect on the target's next API call. No token revocation is required to cut off access.

**Roles** (`app/models/enums.py`)
- `UserRole`: Agent, TransactionCoordinator, TeamLead, Attorney, Admin, Client, ForSaleByOwner, Vendor.
- `ROLE_HIERARCHY` (line 141) and `role_has_permission`.
- `SELF_SIGNUP_ROLES_NOW` (line 180): Agent, TeamLead, TransactionCoordinator, Admin.
- `is_platform_admin` is **not** a `UserRole`. It is a separate boolean column on `users`.

**Seats** (`app/services/seat_service.py`) **[rev3: this whole mechanism is being retired, see D7]**
- `BILLABLE_STAFF_ROLES` = Admin, TeamLead, Agent, TransactionCoordinator, Attorney. Client, ForSaleByOwner and Vendor are free.
- `staff_seat_count` counts users with `is_active = True` **and** a billable role.
- `assert_staff_seat_available` raises `PlanForbidsStaffError` (when `plan == 'solo'`) or `SeatLimitReachedError` (when the active count is at or above `seat_limit`).
- Enforced in three places: `invitations.py:246` (plus a second pending-invite check at `:261` and the DB function via `repo.create_with_seat_check`), and `users.py:763` (role change into a billable role).
- Migration `20260512094000_tenant_plan_seats_and_grandfather.sql` sets `plan DEFAULT 'trial' NOT NULL` and `seat_limit DEFAULT 5`. Tenants that existed at migration time were grandfathered to `enterprise` with `seat_limit = NULL` (unlimited). **Every tenant created since is capped at five billable staff.**

**Credits** (tenant-scoped throughout)
- `app/models/credit.py`: `CreditWallet(tenant_id, balance, free_credits_granted)`, `CreditPurchase`, `CreditLedgerEntry(entry_type, delta, balance_after, idempotency_key, transaction_id, purchase_id, actor_user_id, reason)`.
- Tables: `credit_wallets`, `credit_ledger`, `credit_purchases`, `credit_packs` (`app/repositories/credit_repository.py:26-29`).
- `CreditWalletService.grant(tenant_id, credits, *, reason, actor_user_id, entry_type='adjustment')`: `credits` may be negative; a negative resulting balance raises `InsufficientCreditsError`.
- `app/api/v1/platform_billing.py`: `GET /platform/billing/tenants/{tid}/wallet`, `POST /platform/billing/tenants/{tid}/grant-credits`, `POST /platform/billing/purchases/{id}/refund`, plus `GET/PUT /platform/billing/settings` and `GET /platform/billing/health`.

**Spend and AI usage per user** (`app/api/v1/platform_costs.py`)
- `GET /platform/costs/users` (line 371) via the `cost_usage_by_user` Postgres RPC.
- `GET /platform/costs/users/{user_id}` (line 542): by feature, model, provider, day, transaction.
- **[rev2]** Both sit behind `_require_cost_console` (line 45), which is `require_platform_admin` **plus** the `ve_cost_console_v1` feature flag, and **404s when the flag is off**. Anything embedding these must handle that.

**Audit** (`app/services/audit_service.py`, `app/repositories/audit_repository.py`)
- `log()` writes `audit_logs`, `log_platform()` writes `platform_audit` (snapshot `tenant_id`, survives a hard delete), `log_lifecycle()` writes both.
- `AuditRepository.create` takes `tenant_id` explicitly, so writing into another tenant needs no repository change.
- `GET /api/v1/audit-logs/` is tenant-scoped and `require_role(ADMIN)`.
- **[rev2, correction]** `GET /api/v1/audit-logs/{entity_type}/{entity_id}` is **not** tenant-scoped. See D5.
- `PlatformAuditRepository` offers `create`, `list_by_tenant`, `list_all`. There is no payload-search method.

**Transactions and assignments**
- `transactions.created_by` is the deal owner. The property address is PII and encrypted by the repository.
- `TransactionAssignment(transaction_id, user_id, role_in_transaction, is_active, assigned_at, assigned_by)`.

**Tenants** (`app/api/v1/tenants.py`, `app/api/v1/platform_tenants.py`)
- `GET/POST /tenants`, `GET/PUT/DELETE /tenants/{id}` on `require_platform_admin`; `POST /tenants/current/transfer-ownership`, `/schedule-deletion`, `/cancel-deletion`.
- Legal hold set/clear/history, retention archive listing.
- Frontend: `PlatformTenantsPage.tsx` plus `components/platform/TenantDetailModal.tsx` (633 lines).

**Invitations** (`app/api/v1/invitations.py`): create, list, verify, accept, accept-membership, resend, extend, revoke. All tenant-scoped.

**RLS** **[rev2]** `SYSTEM_DESIGN.md` §2.4 enables row-level security with tenant-isolation policies, and states that the service-role key bypasses it. `app/core/supabase_client.py:59` confirms the backend uses `SUPABASE_SERVICE_ROLE_KEY`. Cross-tenant reads and writes from the API are therefore unobstructed by RLS. Recording this so the design is not later challenged on a false premise.

---

## 2. Gap analysis

### 2.1 What the ask needs that does not exist

| # | Need | Status today |
|---|---|---|
| G1 | Cross-tenant role change | No endpoint. `PUT /users/{id}/role` is `require_role(ADMIN)`. |
| G2 | Cross-tenant deactivate / reactivate | Deactivate exists but is `require_role(ADMIN)`; **there is no reactivate endpoint at all**. `UserRepository` has `deactivate` (line 320) and no mirror. Requirement 10.5 explicitly asks for "edit/deactivate/activate actions". |
| G3 | Per-user detail view | `ROUTES.ADMIN_USER(id)` is defined at `constants.ts:205`, has **no route registered in App.tsx and zero call sites**. `FRONTEND_UI_WORKFLOW_LOGIC.md` §10.2 specifies this page; it was never built. |
| G4 | Credit adjustment from the user console | Exists but only tenant-addressed and only on `/platform/billing`. Nothing links a user to their workspace wallet. |
| G5 | Deal history per user | Only `deal_count` (an integer). No list. |
| G6 | Billing history per user | `credit_ledger` and `credit_purchases` are readable per tenant, never surfaced next to a person. |
| G7 | Cross-tenant activity log **[rev2, reframed]** | A *deliberate* one does not exist. An *accidental, unguarded* one does (D5). The console needs a guarded read, and D5 needs closing whether or not this console is built. |
| G8 | Password reset on behalf of a user | Only self-service (`POST /users/password-reset/request`). No admin-initiated path. |
| G9 | Email correction on another user's account | Only `PATCH /users/me`. |
| G10 | Force sign-out **[rev2, downgraded]** | Nothing, and **little is needed**: `get_current_user` 403s an inactive user on the next request, so deactivation already ends access. Optional nicety, not a requirement. |
| G11 | Bulk actions | Nothing. |

### 2.2 Seven defects in the current code

Stated as findings. Fixing them is in scope where marked; D5, D6 and D7 should be fixed independently of this console.

**D1: `require_role` does not honour `is_platform_admin`.**
`app/core/auth.py:143`. It returns early for `is_tenant_owner` (line 160) and then checks the role hierarchy. A platform admin whose own `users.role` is, say, `Agent` is **rejected** by `PUT /users/{id}/role`. It only works today because the platform admins in use happen to be Admin and owner of their own tenant. Reusing the tenant endpoints for cross-tenant work is therefore load-bearing on a coincidence. The fix is not to loosen `require_role`; it is to give the platform console its own endpoints under `require_platform_admin`. Note that `require_tenant_access` (line 229) *does* return early for platform admins, so the tenant check is not the blocker, the role check is.

**D2: audit rows land in the wrong tenant.**
`AuditService.log()` writes `tenant_id=user.tenant_id`, the **actor's** tenant. When a platform admin changes a user in tenant B, the row is written under tenant A. Tenant B's own `/admin/audit-logs` never shows that their user's role was changed by the vendor. For the Indiana broker-responsibility and "clear audit trails, non-destructive history" requirement (`requirements.txt` 10.3) that is the wrong answer. Every platform action in this plan writes **two** rows: one into the target tenant's `audit_logs`, one into `platform_audit`.

**D3: credits are a workspace fact, not a user fact.**
`credit_wallets` is keyed by `tenant_id`. There is no per-user balance anywhere in the schema. "Update user credit information" can only mean "adjust the wallet of the workspace this user belongs to", which is shared with every other member. If the UI says "Add credits" on a person's row without saying whose wallet moves, an operator will believe they granted one person 10 deals when they granted the whole brokerage 10 deals. This is a labelling requirement, not a schema change (§5.4).

**D4: the registrations endpoint reads three whole tables per request.**
`_fetch_all` pulls all `users`, all `tenants`, and all `transactions` (for `created_by` counting) on every call. Fine at current volume (the module note says so explicitly), not fine at 10k accounts. §9 sets the trigger and the migration path. **[rev2]** This is the budget the new list row has to fit inside; see F6 in §2.3.

**D5 (new, security): `GET /api/v1/audit-logs/{entity_type}/{entity_id}` reads across tenants with no tenant check.** **[rev2]**
`app/api/v1/audit_logs.py:51` is guarded by `require_role(ADMIN, TEAM_LEAD)` and calls `AuditRepository.get_for_entity` (`audit_repository.py:102`), which filters on `entity_type` and `entity_id` only. There is no `.eq("tenant_id", ...)` and no `require_tenant_access` call anywhere on that path. Any tenant Admin or Team Lead who knows or guesses a UUID reads another tenant's audit rows, including the `before_state` / `after_state` diffs and summaries that carry email addresses. This is a cross-tenant IDOR and it directly contradicts the isolation posture that `require_tenant_access` exists to enforce. **Fix independently and ahead of this plan:** add the tenant predicate to `get_for_entity` and a `require_tenant_access` call at the route, keeping the platform-admin early return so the console's own read still works.

**D6 (new): `PATCH /api/v1/users/me` mass-assigns.** **[rev2]**
`UserUpdateRequest` carries `is_active`, and `UserRepository.update` (line 137) has no field whitelist; it writes whatever it is handed, and `False` passes the `if value is None: continue` filter. A user can self-deactivate through the profile endpoint, and it audits as a generic `profile_update` rather than a deactivation. Not exploitable for privilege escalation (`role` is not on that schema, and an inactive user cannot re-authenticate), but it means "who deactivated this account and why" has a third answer path the console will not show. Remove `is_active` from `UserUpdateRequest`.

**D7 (new): the staff-seat gate is live, contradicts the billing model, and its retirement switch was never wired.** **[rev3]**

The platform bills **per transaction** ($49, `deal_fee_cents`, one DB setting). It does not bill per person. Nothing in the product sells a seat: there is no seat purchase UI, no seat line item, no plan upgrade flow, and `tenants.plan` is only ever `trial` (the column default) or `enterprise` (the grandfather backfill). `trial_ends_at` is set but never enforced. Yet `seat_limit` is enforced on every invite and every promotion into a staff role.

The consequence in production: a workspace created since 2026-05-12 hits `409 "You've reached the staff seat limit on the trial plan"` when inviting a sixth staff member, with no way to pay for a sixth, because a sixth is not for sale. The gate cannot generate revenue; it can only block customers. **[rev3]** No live workspace has hit it yet (confirmed 2026-08-10), so this is a quiet fault rather than an active incident. It bites earlier than the headline number suggests, though: the invite path refuses at `active + pending >= seat_limit`, so outstanding invites hold seats too. See R10.

The retirement was already decided. `STABLE_USER_MANAGEMENT_AND_CREDIT_BILLING_SUPERIOR_PLAN.md` (2026-06-18) states it explicitly: "stop billing people, bill per transaction; members become free; retiring the seat gate removes the most failure-prone user-mgmt branches." The switch for it, `ve_free_members_v1`, **exists as a platform setting and is read by nothing.** It is defined at `platform_settings_service.py:24`, defaults to `"false"` (line 52), is loaded into `CreditSettings.free_members` (line 146), and is editable from `/platform/billing` via the mapping at `platform_billing.py:90`. Grep the backend for `free_members` and those are the only hits outside tests and schemas. `SeatService`, `invitations.py` and `users.py` never consult it. An operator can toggle "free members" on today and nothing whatsoever changes, which is worse than not having the toggle.

**Decision for this plan:** the console does not enforce seats and does not offer a seat override (DD8). Retiring the gate itself is **Phase 0 in §10**, shipping ahead of the console, because it belongs to the invite path and because leaving it live would make the console's lack of a seat check the de facto workaround for a billing bug.

### 2.3 Review findings corrected in this revision **[rev2]**

The nineteen issues found reviewing rev 1 against the docs and source. Each is fixed in the section named.

- **F1** Rev 1 claimed "there is no cross-tenant audit read anywhere". False, and the truth is worse. Now D5; G7 reframed.
- **F2** Reactivate must run the seat check, because `staff_seat_count` counts active billable users, so deactivating frees a seat and reactivating consumes one. Rev 1 put the seat guard only on role change. **[rev3: superseded.](#)** The finding was correct given rev 2's assumption that the console enforces seats. That assumption is gone (D7), so the console runs no seat check anywhere and the asymmetry disappears. The underlying coupling is still real and is the reason the retirement in §10 has to cover the reactivate path too.
- **F3** Deactivating the tenant owner is not survivable, so "reason plus confirm" was the wrong control. Now a 409 with a remedy. Fixed in §6.2 and §8.5.
- **F4** Force sign-out is near-worthless because `get_current_user` already 403s an inactive user. Downgraded in G10, §6.2 and §12.
- **F5** The AI-usage embed 404s when `ve_cost_console_v1` is off. Fixed in §5.2 and §6.1.
- **F6** `ai_cost_usd_30d` on every list row would run the `cost_usage_by_user` RPC per request and inherit the cost-console flag. Dropped from the row in §6.1; the other added fields now state how they load.
- **F7** New KPI tiles referenced summary fields that did not exist. `SignupsSummary` extension now specified in §6.1.
- **F8** New columns had no sort keys on a page whose sorting is entirely server-side. `SortKey` extension now specified in §6.1.
- **F9** "`platform_audit` rows whose payload names the target" was an unindexed JSONB scan with no repository support. Now `list_by_tenant` plus a Python filter, in §6.1.
- **F10** Owner role changes had no bound. Now bounded to `BILLABLE_STAFF_ROLES` in §6.2.
- **F11** Writes shipped in phase 2 while the audit reader shipped in phase 4. Activity read moved to phase 2 in §10.
- **F12** A mid-session deactivation surfaces as 403, not a clean logout. Now an explicit edge case in §5.6 and a test in §11.
- **F13** Doc drift found against the shipped code. Recorded in §14.
- **F14** RLS is a non-issue because the backend uses the service-role key. Stated in §1.2 so the design is not challenged on a false premise.
- **F15** Rate-limiting the write routes conflicted with the bulk endpoint and bought little on an authenticated operator surface. Dropped from §8.
- **F16** `PATCH /users/me` mass-assignment. Now D6.
- **F17** DD1 made `/platform/registrations` a redirect in phase 1 while §13 deferred deleting the page "until parity". Contradiction resolved in DD1 and §13. "Tab" language replaced with "view"; the page has sections, not tabs.
- **F18** An admin-sent password reset on an OAuth-provisioned account silently creates a password. Edge case added to §6.2.
- **F19** The proposed `status` filter duplicated and could contradict `activity=deactivated`, since `_activity_state` makes `deactivated` outrank every other state (so `activity=has_deals&status=deactivated` is always empty). Replaced with an `include_deactivated` toggle in §5.1 and §6.1.

---

## 3. Design decisions

**DD1: one page with sections, replacing the registrations page. [rev2]**
`/platform/users` becomes the console. In **phase 1**, `/platform/registrations` becomes a `<Navigate replace>` to `/platform/users?segment=outside`, which is exactly what that page shows today, and `/platform/registrations/alerts` redirects to `/platform/users/alerts`. `PlatformRegistrationsPage.tsx` is unreachable from that moment and is deleted in the same phase, not later: keeping a dead component behind a redirect is how two implementations of the same table start drifting. The registrations *view* survives as the Directory's default filter set. The base page is only one commit old and undeployed, so the bookmark risk is near zero.

**DD2: the role select offers all eight roles and no platform-admin option.**
All eight `UserRole` values are selectable. `is_platform_admin` gets no write path in the UI or the API and stays a DB-only flag, exactly as it is today (no API sets it anywhere in the codebase; the tests flip it through the repository). A platform-admin target renders a "Platform admin" badge and its role select is disabled with a reason. This satisfies "all role types except the platform admin role itself" without inventing a privilege-escalation surface.

**DD3: "transaction history" means two different things, so name both.**
Requirement 3 is ambiguous in exactly the way that produces the wrong build. The detail view carries two separate sections: **Deals** (real-estate transactions the user created or is assigned to) and **Billing** (credit ledger entries and Stripe purchases for their workspace). Neither is labelled "transactions" on its own.

**DD4: every mutation is confirm-gated and reason-stamped.**
Role change, deactivate, reactivate, credit adjust and email change all require a typed reason that lands in both audit rows. This mirrors the discipline already enforced on the per-deal fee change (`platform_billing.py`: "A reason is required to change the per-deal fee").

**DD5: read-only first.**
Phase 1 ships the console with zero write capability. Writes land in phase 2 onward, each behind its own confirm.

**DD6: guests are shown, never edited from here.**
With `ve_multi_workspace_v1` on, a guest's `users.tenant_id` is their *home* tenant (`MULTI_WORKSPACE_MEMBERSHIP_DESIGN_PLAN.md` §9). The directory lists each identity once against its home workspace and lists guest memberships as a sub-line. Editing a guest's host role belongs to the host workspace's own team page.

**DD7 (new): deactivation is the session control. [rev2]**
Because `get_current_user` re-reads `users.is_active` on every request and 403s, deactivating a user ends their access at the next API call without touching tokens. `FRONTEND_UI_WORKFLOW_LOGIC.md` §10.1 lists "user's JWT invalidated" as a side effect of deactivation; that is satisfied in substance already. Force sign-out is therefore an optional nicety for the "still active but must re-authenticate" case, not a gap to close, and it is not on the critical path.

**DD8: the console does not enforce seats. [rev3, replaces the rev2 version]**
Rev 2 wired a shared seat check through role change and reactivate. That is removed. Per D7 the platform bills per transaction, not per person; no seat is for sale, so a seat cap cannot do anything except block a customer. Concretely:

- No seat check on role change, no seat check on reactivate, no `override_seat_limit` field, no seat-override audit action.
- `UserRoleSelect` shows no seat warning.
- The detail page shows the workspace's **staff head count** (useful context) and not `seat_limit` (a number nobody can buy their way past).

This does leave one asymmetry while the gate still exists elsewhere: a tenant Admin promoting a sixth staff member through `PUT /users/{id}/role` still gets a 409, while a platform admin doing the same through this console does not. That is the correct direction for an operator console (the vendor can always unstick a customer) and it is temporary, because §10 retires the gate outright.

---

## 4. Information architecture

```
/platform/users                      Directory        (list, KPI strip, filters, CSV)
/platform/users/:userId              User detail      (6 sections, see §5.2)
/platform/users/alerts               Registration alerts (moved from /platform/registrations/alerts)
```

Nav (`src/layouts/AppLayout.tsx:466-479`): the `Registrations` entry becomes `Users`. Group order stays the funnel reading top-down: Tenants, Users, Waitlist, AI usage, Costs and pricing, Help center. This is a console, not configuration, so it belongs in the sidebar rather than the Settings hub, consistent with the comment already at `AppLayout.tsx:463-465`.

Route constants to add in `src/utils/constants.ts`:

```ts
PLATFORM_USERS: '/platform/users',
PLATFORM_USER: (id: string) => `/platform/users/${id}`,
PLATFORM_USER_ALERTS: '/platform/users/alerts',
// kept, now redirect sources:
PLATFORM_REGISTRATIONS: '/platform/registrations',
PLATFORM_REGISTRATION_ALERTS: '/platform/registrations/alerts',
```

`ADMIN_USER` (`constants.ts:205`) stays untouched and dead for now. It belongs to the tenant-side drill-down that `FRONTEND_UI_WORKFLOW_LOGIC.md` §10.2 specifies and nobody built; that is a separate piece of work (§14).

---

## 5. Frontend

### 5.1 Directory: `/platform/users`

New file: `src/pages/platform/PlatformUsersPage.tsx`. Built from `PlatformRegistrationsPage.tsx`, the closest working reference for every mechanic (server-side sort, `keepPreviousData`, page-size select, CSV walk).

**Header.** `PlatformPageHeader` with `title="Users"`, the account-count badge, and trailing links: `Alerts` (existing bell) and `CSV`.

**KPI strip.** Four `KpiCard`s from `@/components/analytics/AnalyticsCharts`, whole-table figures that never follow the filter (the existing contract on `SignupsSummary`). **[rev2]** Each names the summary field that backs it, and §6.1 adds the two that do not exist yet:

- New this week: `new_7d`, sub `new_24h` in the last 24h. *(exists)*
- Real outside signups: `genuine_outside`, sub "N suspected bots excluded". *(exists)*
- Active accounts: `active` / `total`, sub "ever signed in: `ever_signed_in`". *(`active` is new)*
- Deals created: `total_deals`, sub "`workspaces_with_deals` workspaces". *(both new)*

**Controls row** (above the list, no intro prose, per the standing list-page rule).
Left: search, date range, activity, authenticity, **role** (new), **workspace** (new, typeahead over tenants).
Right: segment `SegmentedControl`, an **Include deactivated** toggle (new), refresh, CSV.

**[rev2]** There is deliberately **no** separate "status" filter. `_activity_state` already makes `deactivated` outrank every other state, so a `status` filter would duplicate `activity=deactivated` and produce silently-empty results in combination with it (`activity=has_deals&status=deactivated` can never match). The toggle is the honest control: default off, meaning deactivated rows are hidden unless `activity=deactivated` is explicitly selected, which turns it on.

**Table.** Columns: Person (name, email, and Internal / Suspected-bot / Platform-admin / Owner chips), Workspace (name, plan, trial days left, links to `/platform/tenants`), Role (chip), Joined via, Activity (dot, label, last seen), Wallet (workspace prepaid deals, right-aligned), Registered (date, relative), and a trailing **Actions** kebab (View, Change role, Deactivate/Reactivate, Adjust credits, Send password reset).

Row click opens the detail route. The kebab stops propagation. Every column header in that list is sortable, which requires the `SortKey` extension in §6.1.

**Selection and bulk bar.** A checkbox column and a sticky bulk bar at one or more selections: Deactivate, Reactivate, Export selected. Bulk role change is deliberately **not** offered: the seat guard and the owner rules are per-target decisions, and a bulk role change that half-fails is worse than none.

**Empty states.** Keep the existing per-filter copy, which already distinguishes "no match for this search" from "no outside registrations yet, every account so far is one of ours".

### 5.2 Detail: `/platform/users/:userId`

New file: `src/pages/platform/PlatformUserDetailPage.tsx`. Full page, not a modal: six sections do not fit a dialog without it becoming a page with a backdrop.

Header: `PlatformPageHeader` with `crumbs=[{label:'Users', to: ROUTES.PLATFORM_USERS}]`, the person's name as title, status chips, and the action cluster.

1. **Identity.** Name, email, phone, avatar, `role`, `is_active`, `is_platform_admin`, `onboarding_completed`, `joined_via_invitation_id`, `created_at`, `last_login_at`, `welcome_email_sent_at`, `team_id`. Every PII field decrypted server-side via `_safe_pii`.
2. **Workspace.** Tenant name, slug, plan, **staff head count** (from `SeatService.staff_seat_count`, as information, not as a cap) **[rev3: `seat_limit` deliberately not shown, see DD8]**, `trial_ends_at`, `is_active`, `legal_hold`, `deletion_scheduled_at`, and whether this user is `owner_user_id`. Links to `/platform/tenants`. Guest memberships listed with host workspace and host role.
3. **Deals.** Transactions where `created_by = user_id`, plus active `transaction_assignments`. Address (decrypted), status, `use_case`, closing date, created date, and the assignment's `role_in_transaction` where it came from an assignment. Links into the transaction workspace.
4. **Billing.** The workspace wallet balance, `free_credits_granted`, the `credit_ledger` for that tenant (entry_type, delta, balance_after, reason, actor, created_at) and `credit_purchases` (credits, amount, status, Stripe session). Ledger rows whose `actor_user_id` is this user are marked. An **Adjust credits** action and a **Refund** action per paid purchase.
5. **AI usage and cost.** Embeds `GET /platform/costs/users/{user_id}`. **[rev2]** That endpoint is behind `ve_cost_console_v1` and 404s when the flag is off, so the detail response carries a `cost_console_enabled` boolean and the section renders only when it is true. No spinner that never resolves, and no error toast for a flag that is simply off.
6. **Activity.** Merged timeline from the target tenant's `audit_logs` (this user as actor and as `entity_id`) plus `platform_audit` rows for that tenant naming them, with registration and login milestones. Backed by the new endpoint in §6.1.

### 5.3 Hooks

New file: `src/hooks/usePlatformUsers.ts`, keeping the shape of `usePlatformRegistrations.ts`:

- `usePlatformUsers(filters)`: list, `placeholderData: keepPreviousData`.
- `useFetchAllPlatformUsers()`: the CSV walk, 1000 per page, not a react-query hook, using `apiFetch` (never a bare `fetch`).
- `usePlatformUser(userId)`, `usePlatformUserDeals(userId)`, `usePlatformUserBilling(userId)`, `usePlatformUserActivity(userId)`.
- `useChangePlatformUserRole()`, `useSetPlatformUserActive()`, `useAdjustPlatformUserCredits()`, `useSendPlatformUserPasswordReset()`, `useUpdatePlatformUserEmail()`.

Every mutation invalidates `PLATFORM_USERS_KEY`; credit mutations also invalidate the platform billing keys.

**[rev2]** `useUpdateRegistrationAlertSettings` must keep invalidating the user-list key, not just the alert-settings key. The tester list decides who counts as `is_internal`, so saving it changes what the `outside` segment means. The existing hook already does this; the new list key has to be wired into it or the Internal chips go stale.

`usePlatformRegistrations.ts` keeps the alerts hooks and is re-exported from the new file.

### 5.4 The credit-scope labelling rule (D3)

Anywhere credits appear next to a person, the control is titled **"Workspace wallet"**, never "user credits", and carries:

> Prepaid deals are shared by everyone in **{tenant_name}** ({n} members). Adjusting this changes the balance for all of them.

The confirm dialog repeats the workspace name and the member count. Without it the feature is a foot-gun.

### 5.5 Components to create

- `src/components/platform/UserRoleSelect.tsx`: the eight `UserRole` values; disabled with a reason for a platform-admin target; restricted to `BILLABLE_STAFF_ROLES` for an owner target. **[rev3]** No seat warning (DD8). `BILLABLE_STAFF_ROLES` is still the right constant for the owner bound, since it names the roles that can actually operate a workspace; that it also happens to name the old billing set is incidental.
- `src/components/platform/UserActionsMenu.tsx`: the kebab, in one place so the row menu and the detail header cannot drift.
- `src/components/platform/CreditAdjustDialog.tsx`: signed integer, required reason, workspace-scope warning.
- `src/components/platform/UserActivityTimeline.tsx`.
- `src/components/platform/BulkUserActionBar.tsx`.

Reuse `PlatformPageHeader`, `KpiCard`, `SegmentedControl`, `Select`, `useConfirm` (`src/components/ui/confirm-dialog.tsx`), `useToast`, `apiFetch` / `useApiFetch` / `useApiMutate`. Every destructive toggle goes through `useConfirm`.

### 5.6 Edge cases **[rev2]**

Following the `FRONTEND_UI_WORKFLOW_LOGIC.md` per-page convention (its §10 "Edge Cases and Special Behaviors" slot):

- **Self-deactivation while the console is open.** Blocked server-side (409), but the UI also hides the action on the caller's own row rather than surfacing an error.
- **A user deactivated mid-session.** Their next API call returns **403** "Account is inactive", not 401. The app's session handling keys on 401 for forced sign-out, so a 403 will surface as an error rather than a clean logout. Either accept that (the user is locked out either way) or extend the 401 handler to treat this specific 403 detail as a session end. Flagged rather than silently assumed.
- **Deactivating a user who owns in-flight deals.** Their transactions and assignments are untouched; the deals continue with no owner who can sign in. The confirm names the deal count.
- **The target's tenant is itself suspended.** `get_current_user` 403s on the tenant check too, so a user-level reactivate does not restore access. The confirm says so and links to the tenant.
- **Search matches nothing because the query is ciphertext-shaped.** Not possible today (search runs post-decryption) and the §11 test locks that in.

---

## 6. Backend

New file: `velvet-elves-backend/app/api/v1/platform_users.py`, prefix `/platform/users`, **every route on `require_platform_admin`**. Registered in `app/api/v1/router.py`.

`platform_registrations.py` is not deleted. Its list handler is refactored into a shared loader both modules call, so `_fetch_all`, `_safe_pii`, `_activity_state` and the bot assessment keep exactly one implementation.

### 6.1 Read

**`GET /api/v1/platform/users`**

Existing registration params plus `role`, `tenant_id`, `include_deactivated` (bool, default false), `platform_admin` (any/only/exclude). **[rev2]** No `status` param; see F19.

Response row is `SignupRow` widened to `PlatformUserRow` with:

```
team_id, team_name, phone, company_name,
is_tenant_owner, is_platform_admin,
guest_memberships: [{tenant_id, tenant_name, role}],
wallet_balance, wallet_tenant_id
```

**[rev2] How the added fields load, inside D4's budget.** The shared loader already reads `users`, `tenants` and `transactions`. It gains exactly two more `_fetch_all` calls, both small and both keyed in memory: `teams` (id, name) and `credit_wallets` (tenant_id, balance). `guest_memberships` adds a third only when `ve_multi_workspace_v1` is on, over `workspace_memberships`. `is_tenant_owner` is derived from the `tenants` map already in hand and costs nothing.

**[rev2] `ai_cost_usd_30d` is deliberately not on the row.** It would require the `cost_usage_by_user` RPC on every list request, duplicating `/platform/costs/users`, and would drag the cost-console feature flag into a page that must work without it. AI spend lives on the detail page and on the existing cost console.

**[rev2] `SignupsSummary` gains** `active` (count of `is_active`), `total_deals` (sum of `deal_count`) and `workspaces_with_deals` (distinct tenants with at least one deal). All three are computed from rows already in memory, like every existing summary field, and stay whole-table rather than filter-scoped.

**[rev2] `SortKey` gains** `wallet` and `team`. It is a closed `Literal`, so a column without a key is a column that cannot be ordered, on a page whose entire sorting story is server-side. Every sortable column in §5.1 has a key.

Filter order: segment, search, activity, authenticity, role, tenant, deactivated-visibility, date; then sort; then slice. `total` tracks the filter, `summary` does not.

**`GET /api/v1/platform/users/{user_id}`**: the Identity and Workspace payload of §5.2, plus `cost_console_enabled` **[rev2]**. Deals, billing and activity are their own routes so a slow section cannot block the page.

**`GET /api/v1/platform/users/{user_id}/deals`**: paginated. `transactions` where `created_by = user_id`, unioned with `transaction_assignments` where `user_id = target` and `is_active = true`, carrying `role_in_transaction`. Address decrypted server-side.

**`GET /api/v1/platform/users/{user_id}/billing`**: wallet, ledger page and purchases page for the user's tenant, with `actor_user_id == user_id` marked. Thin wrapper over `CreditLedgerRepository` and `CreditPurchaseRepository`.

**`GET /api/v1/platform/users/{user_id}/activity`**: closes G7.
**[rev2] How it reads, given the repositories that exist:**
- `audit_logs`: two `AuditRepository.list_by_tenant(target.tenant_id, ...)` calls, one filtered by `user_id=target` and one by `entity_type='user', entity_id=target`, merged and de-duplicated by row id. The tenant predicate is passed explicitly. This does **not** use `get_for_entity`, which is the unguarded method in D5.
- `platform_audit`: `PlatformAuditRepository.list_by_tenant(target.tenant_id)`, then filtered in Python for rows naming the target in `payload` or `actor_user_id`. Rev 1 proposed matching on payload contents directly; there is no such repository method and it would be an unindexed JSONB scan of the whole table.

This is the only *deliberate* cross-tenant audit read, it is `require_platform_admin`, and it is read-only.

### 6.2 Write

**`PUT /api/v1/platform/users/{user_id}/role`**
Body `{role, team_id?, reason}`. **[rev3: no `override_seat_limit`, see DD8]**
- 404 unknown user.
- 409 when the target `is_platform_admin` (DD2).
- 409 when the target is the caller (§8.3).
- **[rev2]** Owner target (`tenants.owner_user_id == user_id`): permitted, but `role` must be in `BILLABLE_STAFF_ROLES`. Moving an owner to `Client`, `ForSaleByOwner` or `Vendor` leaves them holding the `is_tenant_owner` bypass in `require_role` while landing them in a portal shell, which is a workspace nobody can coherently administer. Rev 1 left this unbounded.
- **[rev3]** No seat check. This endpoint never calls `SeatService`.
- Writes both audit rows (D2).

**`POST /api/v1/platform/users/{user_id}/deactivate`**
Body `{reason}`.
- 409 when the target is the caller.
- **[rev2]** 409 when the target is `tenants.owner_user_id`, with the remedy in the message: transfer ownership via `POST /tenants/current/transfer-ownership` first. Rev 1 allowed this with a reason and a warning. It is not survivable: `get_current_user` 403s the deactivated owner on every request, `require_role` grants authority through `is_tenant_owner`, and `tenants.owner_user_id` still points at the dead row, so the workspace is left with nobody who can administer it. A warning is not a control for an unrecoverable state.
- Response includes the target's open deal count so the confirm can name it.
- Both audit rows.

**`POST /api/v1/platform/users/{user_id}/reactivate`**
Body `{reason}`. **[rev3: no seat check and no override, see DD8]**
- Warns when the target's tenant is itself inactive, because reactivating the user does not restore access in that case.
- Both audit rows.

`UserRepository` gains `reactivate(user_id)` mirroring `deactivate` (line 320).

**`POST /api/v1/platform/users/{user_id}/password-reset`**
Closes G8. Calls the same Supabase path the self-service route uses, addressed to the decrypted email, `redirect_to` validated through `is_allowed_redirect` exactly as `POST /users/password-reset/request` does. Returns 202 and never reveals delivery state. Audited.
**[rev2] Edge case:** an account provisioned through `OAuthService` (Google / Microsoft) may have no password. A reset silently creates one, turning an SSO-only account into one that also has password auth. The confirm says so.

**`PATCH /api/v1/platform/users/{user_id}/email`**
Closes G9. Body `{email, reason}`. Does both writes in the order `PATCH /users/me` already proves correct: `supabase.auth.admin.update_user_by_id(id, {"email": ..., "email_confirm": True})`, then the encrypted column. 409 on collision, checked with `UserRepository.get_by_email`, which compares decrypted values. Audited with old and new address. Highest-risk write on the page; phase 4, double-confirmed.

**`POST /api/v1/platform/users/{user_id}/credits`**
Body `{delta: int, reason: str}`. Wrapper over `CreditWalletService.grant(tenant_id, delta, reason=..., actor_user_id=...)` resolved from the user's tenant. Returns the workspace balance and a fresh ledger page. `InsufficientCreditsError` maps to 409. It does not duplicate grant logic; `POST /platform/billing/tenants/{tid}/grant-credits` stays the tenant-addressed route and both call the same service.

**`POST /api/v1/platform/users/bulk`**
Body `{user_ids: [...], action: 'deactivate'|'reactivate', reason}`. Per-item results, never all-or-nothing, so a partial failure reports exactly which rows moved. Capped at 200 ids. Each item runs the same guards as the single-target route, including the owner refusal.

**Force sign-out: not built. [rev2]** Rev 1 specified `POST .../sign-out` and hedged on whether Supabase exposes a revoke. Per DD7 it is not needed: deactivation already ends access at the next request. Dropping it removes a route, a risk and a dependency on an unverified admin API.

### 6.3 The audit helper (D2)

Add to `AuditService`:

```python
async def log_platform_action_on_tenant(
    self, *, actor: User, tenant_id: str, action: str,
    entity_type: str, entity_id: str,
    before_state: dict | None, after_state: dict | None,
    summary: str, reason: str,
) -> None
```

Writes one `audit_logs` row with `tenant_id` = the **target** tenant and `user_id` = the platform admin, and one `platform_audit` row. Neither write may raise into the request path, matching the existing contract that audit logging never breaks the main flow. Every write route in §6.2 calls this and nothing else. `AuditRepository.create` already takes `tenant_id` explicitly, so no repository change is needed.

### 6.4 New audit actions

`platform_user_role_changed`, `platform_user_deactivated`, `platform_user_reactivated`, `platform_user_credits_adjusted`, `platform_user_password_reset_sent`, `platform_user_email_changed`. **[rev3]** `platform_user_seat_limit_overridden` is dropped: with no seat check there is nothing to override.

---

## 7. Data model

No new tables. No migration required for the core plan.

Two additions, both worth doing with the phase they belong to:

- **`users.deactivated_at` and `users.deactivated_reason`.** Today `is_active=false` records the fact and loses the when and the why; the reason lives only in an audit summary. A column pair makes "who did we suspend and why" a query instead of a log grep. Ship with the deactivate/reactivate pair in phase 2.
- **`platform_user_directory` RPC.** See §9. Not needed at current volume.

---

## 8. Permissions and safety rails

1. Every route: `require_platform_admin`. Never `require_role(ADMIN)` for cross-tenant work; that role is tenant-scoped, and D1 shows the current reuse is accidental.
2. Frontend: the whole subtree sits under `PlatformAdminGuard`, which renders `NotFoundPage` (a 404, not a 403) so the routes do not leak their existence.
3. **No self-mutation.** A platform admin cannot change their own role, deactivate themselves, or adjust credits on their own workspace from this page. 409 with a clear message, and the UI hides the actions on their own row.
4. **No platform-admin targets.** Role change, deactivate and email change all 409 against a row with `is_platform_admin = true`. The flag has no API write path anywhere and gains none here.
5. **Owner protection. [rev2]** Deactivating `tenants.owner_user_id` is **refused** (409) with the transfer-ownership remedy in the message, because the resulting state is unrecoverable through the product. Changing an owner's role is permitted but bounded to `BILLABLE_STAFF_ROLES`. Rev 1 allowed owner deactivation behind a warning; that was wrong.
6. **No seat enforcement. [rev3]** This console never calls `SeatService.assert_staff_seat_available`. Seats are a per-person billing control in a product that bills per transaction and sells no seats (D7). Enforcing a cap nobody can pay to raise only blocks customers. The staff head count is still shown as information.
7. **Reason required** on every write, stored in both audit rows.
8. **PII.** Decrypt only for display, in the response model. Never log a decrypted email or address. `_safe_pii` returns `None` on a bad token rather than leaking ciphertext, and that behaviour is kept.
9. **RLS is not a factor. [rev2]** The backend holds the service-role key (`supabase_client.py:59`), which bypasses the tenant-isolation policies in `SYSTEM_DESIGN.md` §2.4. Isolation on this surface is enforced by the FastAPI guards alone, which is precisely why D5 matters.
10. **No rate limiter on these routes. [rev2]** Rev 1 proposed `build_rate_limiter`. It would fight the bulk endpoint, it is per-process across two ECS tasks so it guarantees nothing, and the threat model for an authenticated operator surface is misuse, not volume. The controls are the confirms, the reason field and the double audit. The 200-id bulk cap stays.

---

## 9. Scale

The loader reads all `users`, all `tenants` and all `transactions` per request (D4), and gains `teams` plus `credit_wallets` under this plan (§6.1). All are small tables that grow with customers, not with activity.

**Trigger:** total accounts past roughly 5,000, or list p95 past 1.5s.

**Move:** a `platform_user_directory` Postgres RPC doing the joins and the `deal_count` group-by SQL-side, returning still-encrypted `email` and `full_name`. Search stays in Python over the decrypted page. Do not push search down: encrypted columns are not searchable, and an `ilike` against ciphertext matches nothing silently, which reads as "no results" rather than as a bug.

Interim, cheap: cache the tenant, team and wallet maps for 30 seconds per process. All three change far slower than the page is refreshed.

---

## 10. Phasing

**Phase 0: fix what is broken before adding a console. [rev3, Jan's call 2026-08-10]** Nothing in this phase depends on the console, and the console should not be the workaround for any of it.

*0a. Retire the staff-seat gate (D7).* Smallest correct change, in order:

1. Make `SeatService.assert_staff_seat_available` a no-op when `CreditSettings.free_members` is true. This is the wiring `ve_free_members_v1` was created for and never got. One `if` in one method covers both application call sites (`invitations.py:246`, `users.py:763`).
2. Do the same for the second, inline cap check at `invitations.py:261`, which duplicates the logic and would otherwise keep enforcing after step 1.
3. Drop the DB-level gate on the invite insert. `repo.create_with_seat_check` calls the `create_invitation_with_seat_check` function from migration `20260512095000` and maps its `P0001` to a 409. With the flag on this is the only remaining enforcement, and it is the one that cannot be reasoned about from the application code.
4. Set `ve_free_members_v1 = true` in platform settings and confirm from `/platform/billing` that the toggle now does something.
5. Backfill `seat_limit = NULL` (the existing "unlimited" convention) on tenants created since the 2026-05-12 migration, so the column stops being a live cap even for a caller that bypasses the flag.

Leave `tenants.plan`, `seat_limit` and `trial_ends_at` in place, dormant, exactly as `STABLE_USER_MANAGEMENT_AND_CREDIT_BILLING_SUPERIOR_PLAN.md` §E specified. A per-seat product may return (`requirements.txt` 12.10 prices an AI Coach add-on per agent per month, marked non-MVP), and the columns cost nothing while unused. What has to stop is the *enforcement*.

**Verify before step 5:** whether any live tenant has `plan = 'solo'`. `assert_staff_seat_available` refuses `solo` tenants outright, before it ever looks at `seat_limit`, so a solo tenant cannot add any staff at all and step 5 alone would not free them. The column default is `trial` and nothing in the product sets `solo`, so the expected count is zero, but it is a one-query check and the failure mode is a customer who silently cannot build a team.

*0b. Close the two security defects.* D5 (the unguarded `get_for_entity`: add the tenant predicate and a `require_tenant_access` call, keeping the platform-admin early return) and D6 (drop `is_active` from `UserUpdateRequest`). **[rev3]** These were previously filed as "out of band, ahead of phase 2". Phase 0 now exists and is a better home than an undated bucket: D5 is a live cross-tenant read of another customer's audit history, which is more urgent than anything else in this document. Both are small and neither touches the console. Say so if you would rather they ship separately from the seat work.

*Acceptance for phase 0:* a workspace with five active billable staff can invite a sixth and promote a seventh; **a workspace with three active staff and two unexpired pending invites can send a third invite** (the `active + pending` path at `invitations.py:261`, which R10 shows is the condition that actually bites first); the D5 regression test in §11 passes; `PATCH /users/me {"is_active": false}` is rejected.

**Phase 1: read-only console.** `GET /platform/users` (widened row, extended summary, extended sort keys), `GET /platform/users/{id}`, the Directory page, the detail page's Identity and Workspace sections, the redirects from `/platform/registrations`, deletion of `PlatformRegistrationsPage.tsx`, the nav rename. Ships requirement 1 plus the drill-down (G3).

**Phase 2: role and status, with its audit trail visible. [rev2]** `PUT .../role`, `POST .../deactivate`, `POST .../reactivate`, `UserRepository.reactivate`, the `deactivated_at` columns, the audit helper (§6.3), **and `GET .../activity` plus the Activity section**. Rev 1 shipped two phases of cross-tenant mutation before the in-app way to read the trail those mutations write; the control the plan leans on has to arrive with the first write. Ships requirement 2 (G1, G2) and G7. **[rev3]** No seat helper; see DD8.

**Phase 3: money and history.** `GET .../deals`, `GET .../billing`, `POST .../credits`, the Deals and Billing sections, `CreditAdjustDialog`, the flag-guarded AI usage section. Ships requirement 3 (G4, G5, G6).

**Phase 4: operations.** Password reset, email change, bulk deactivate/reactivate, CSV of the full filtered set. Ships the rest of requirement 4 (G8, G9, G11).

**Phase 5: hardening.** The caching from §9, and the RPC if the trigger has been hit.

Phase 0 ships first and stands alone. Phases 1 and 2 are the minimum that answers the literal ask.

---

## 11. Testing

**Backend:** new `app/tests/test_platform_users_api.py`, following `test_platform_registrations_api.py` (platform-admin fixture at line 42).

- Guard: every route 403s for a tenant Admin, 403s for an owner who is not a platform admin, 200s for a platform admin.
- **D1 regression:** a platform admin whose `users.role` is `Agent` and who is not their tenant's owner can still change a role through the new endpoint. This is the test that proves the console does not rest on a coincidence.
- **D2 regression:** after a cross-tenant role change, the `audit_logs` row exists under the **target** tenant, and a `platform_audit` row exists.
- **D5 regression [rev2]:** `GET /api/v1/audit-logs/{entity_type}/{entity_id}` returns nothing for an entity in another tenant when called by a tenant Admin. This test fails today; it is the acceptance test for the out-of-band fix.
- Role change: platform-admin target 409s; self target 409s; owner target rejects a portal role and accepts a staff role.
- **No seat enforcement [rev3]:** in a tenant whose active billable staff count is already at `seat_limit`, promoting a Client to Agent through this console **succeeds**, and reactivating a deactivated Agent **succeeds**. These are the tests that lock DD8 in; they fail if someone later reintroduces a `SeatService` call here.
- **Owner deactivate [rev2]:** 409 with the transfer-ownership remedy in the detail. Deactivating a non-owner in the same tenant succeeds.
- **Deactivation ends access [rev2]:** after deactivate, a request bearing the target's still-valid token gets 403 "Account is inactive". This is what makes force sign-out unnecessary (DD7).
- Credits: `delta` applied to the correct tenant wallet; a negative delta past zero 409s; the ledger row carries `actor_user_id` = the platform admin and `entry_type='adjustment'`.
- Email change: collision 409s; success updates both Supabase Auth and the encrypted column.
- Search: a user whose name matches only after decryption is found, guarding against a future SQL `ilike` "optimization".
- **Filters [rev2]:** `include_deactivated=false` hides deactivated rows; selecting `activity=deactivated` shows them regardless; `total` tracks the filter while `summary` does not.
- **Summary [rev2]:** `active`, `total_deals` and `workspaces_with_deals` are whole-table and do not move when a filter is applied.

**Frontend:** a browser pass sized to the change, roughly 12 to 15 checks, not a full matrix. Directory loads and paginates; each filter narrows correctly; sort toggles and survives paging, including the new Wallet column; row click opens detail; role change round-trips and the row updates; deactivate reflects in the Activity column; the owner row's deactivate action is refused with the remedy visible; credit adjust shows the workspace warning and the balance moves; the AI usage section is absent rather than broken with `ve_cost_console_v1` off; the redirect from `/platform/registrations` lands on the Directory with `segment=outside`; CSV downloads a real CSV with the filtered row count, not the SPA's `index.html`; a non-platform-admin gets a 404.

Drive `localhost:5173`, not `127.0.0.1`.

---

## 12. Risks and open questions

**R1: cross-tenant read of another customer's audit trail.** `GET .../activity` is a genuine privacy expansion: the vendor reading a brokerage's internal action history. Defensible for support and for the broker-responsibility requirement, but it should be a conscious decision, and the read itself should arguably be audited. **Question for Jake:** should platform-admin reads of a tenant's audit trail be logged and disclosed?

**R2: email change on a live account.** Changing someone's login email out from under them breaks their saved credentials and invalidates any pending confirmation link. Phase 4, double-confirmed. **Question for Jake:** notify the user on an admin-initiated email change, or silent?

**R3: credit adjustments are real money.** `grant` moves prepaid deals worth $49 each. The reason field and the double audit are the control. Consider a soft cap (say plus or minus 50 per action) above which a second confirm is required. **Question for Jake.**

**R4: D5 is live today.** The unguarded `get_for_entity` is a cross-tenant leak in production code, independent of this plan. It needs a fix and, depending on how the log retention reads, possibly a look at whether it was ever exercised.

**R5: D4 at scale.** Covered in §9. The failure mode is a slow page, not a wrong page, which is the acceptable direction.

**R6: two "user management" surfaces.** `/admin/users` (tenant Admin, `AdminUsersListPage.tsx`) and `/platform/users` (vendor, cross-tenant) will look similar and do different things. They must not share components beyond the primitives, and the platform one keeps the `PlatformPageHeader` breadcrumb so an operator always knows which side of the fence they are on.

**R7: the uncommitted registrations work.** The alerts sub-page, `email-list-input.tsx` and the bot-signal work are still working-tree changes. Commit them before building on top, or the phase-1 refactor of `platform_registrations.py` collides with them.

**R9 [rev3]: the seat cap. Closed, no customer impact to date.** D7 is live behaviour: any workspace created since 2026-05-12 is capped at five billable staff and cannot buy a sixth, because a sixth is not for sale. Rev 3 asked whether the retirement should ship before phase 1; **Jan's answer, 2026-08-10, is yes**, and it is now Phase 0. Jan also confirmed the same day that **no live workspace has hit the limit**, so there is no support message owed and no customer to unblock. The seat work in Phase 0 is therefore correctness and debt removal on a quiet fault, not an incident response. That changes the *reason* Phase 0 ships first but not the decision: D5 in Phase 0b is a live cross-tenant read and is now the phase's urgency driver.

**R10 [rev3]: the cap bites earlier than "five staff", so "nobody has five staff" is not the same as "nobody can be blocked."** `invitations.py:261` refuses when `active + pending_billable >= seat_limit`, where `pending_staff_invite_count` counts invitations that are unused, unrevoked **and** unexpired. A three-person workspace with two outstanding invites is already at the wall and its next invite is refused, with a message about a "staff seat limit on the trial plan" that names a plan nobody can buy. Invites live 72 hours by default (`invitation_repository.py:23`) and `POST /invitations/{id}/extend` pushes that out further, so an abandoned or repeatedly-extended invite holds a seat for days without anyone joining. Nothing to do beyond Phase 0, which removes both checks, but it is the reason not to read "no workspace has five staff" as "the gate is dormant."

**R8 [rev2]: the 403-versus-401 session edge.** §5.6 flags that a mid-session deactivation surfaces as 403 while the app's forced-sign-out path keys on 401. Deciding whether to extend that handler is a small call, but it should be a deliberate one.

---

## 13. Documentation drift found during review **[rev2]**

Recorded because the plan was checked against these docs and they disagree with the shipped code. None blocks the work; all three are worth correcting so the next reader is not misled.

- **`FRONTEND_UI_WORKFLOW_LOGIC.md` §10.1** specifies `GET /api/v1/admin/users` and `PATCH /api/v1/admin/users/:id`. Neither path exists. The shipped routes are `GET /api/v1/users/` and `DELETE /api/v1/users/{user_id}`, and there is no PATCH for another user at all. Its "Invite User" call, `POST /api/v1/admin/invitations`, is really `POST /api/v1/invitations/`.
- **`FRONTEND_UI_WORKFLOW_LOGIC.md` §10.2** specifies `/admin/users/:userId` with an activity log, transaction assignments and integration status. It has no route in `App.tsx` and no page component. This plan builds the platform-side equivalent; the tenant-side page named in that spec remains unbuilt, which is what `ROUTES.ADMIN_USER` was reserved for.
- **`SYSTEM_DESIGN.md` §3.3** permission matrix has no platform-admin column. It predates the `is_platform_admin` flag and describes "User management: Admin CRUD" as if the tenant Admin were the top of the tree. Worth a footnote there pointing at `require_platform_admin`.

---

## 14. File manifest

**Create, backend**
- `app/api/v1/platform_users.py`
- `app/tests/test_platform_users_api.py`

**Modify, backend**
- `app/api/v1/router.py` (register the router)
- `app/api/v1/platform_registrations.py` (extract the shared loader; keep the routes)
- `app/services/audit_service.py` (add `log_platform_action_on_tenant`)
- `app/repositories/user_repository.py` (add `reactivate`)

**Modify, backend, Phase 0 (§10), shipping ahead of the console [rev3]**
- `app/services/seat_service.py` and `app/api/v1/invitations.py` (D7: honour `ve_free_members_v1`, remove the duplicate inline cap check at `:261` and the DB-level invite gate), plus a `seat_limit` backfill migration
- `app/repositories/audit_repository.py` and `app/api/v1/audit_logs.py` (D5: tenant predicate plus `require_tenant_access`)
- `app/schemas/user.py` (D6: drop `is_active` from `UserUpdateRequest`)

**Create, frontend**
- `src/pages/platform/PlatformUsersPage.tsx`
- `src/pages/platform/PlatformUserDetailPage.tsx`
- `src/hooks/usePlatformUsers.ts`
- `src/components/platform/UserRoleSelect.tsx`
- `src/components/platform/UserActionsMenu.tsx`
- `src/components/platform/CreditAdjustDialog.tsx`
- `src/components/platform/UserActivityTimeline.tsx`
- `src/components/platform/BulkUserActionBar.tsx`

**Modify, frontend**
- `src/App.tsx` (routes plus redirects under `PlatformAdminGuard`)
- `src/utils/constants.ts` (`PLATFORM_USERS`, `PLATFORM_USER`, `PLATFORM_USER_ALERTS`)
- `src/layouts/AppLayout.tsx` (nav entry rename)
- `src/pages/platform/RegistrationAlertsPage.tsx` (move under `/platform/users/alerts`, breadcrumb update)
- `src/hooks/usePlatformRegistrations.ts` (keep the alerts hooks; invalidate the new list key on save)

**Delete, frontend**
- `src/pages/platform/PlatformRegistrationsPage.tsx`, in phase 1, at the same time the redirect lands. **[rev2]** Rev 1 deferred this "until the Directory reaches parity", which contradicted making the route a redirect in phase 1. Once the route redirects, the component is unreachable, and leaving it is how two implementations of the same table start drifting.
