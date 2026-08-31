# CASA 3.1.1 — Least privilege on a trusted service layer

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 4.1.1  
**Date:** 31 Aug 2026  

ADA note: **3.1.1–3.1.3 share one written description.** This file is that description. This portal row is **least privilege on a trusted service layer**. 3.1.2 (client cannot set policy attributes) and 3.1.3 (fail securely) reuse the same model with different probes.

## ADA AL1 evidence

1. How authentication and authorization are implemented, what roles exist, and how rules are enforced.
2. Least privilege: users reach only functions and data they are authorized for.

Verification: access control rules are enforced on a **trusted service layer**.

## Trusted service layer

The SPA (`RoleRoute`, `ProtectedRoute`) hides URLs. **Enforcement is the FastAPI API.**

1. `get_current_user` verifies the JWT and loads the profile (`app/core/auth.py`). Role and `tenant_id` come from the server record, not from client JSON.
2. Route dependencies: `require_role`, `require_exact_roles`, `require_platform_admin`, `require_cron_secret`.
3. Object checks: `require_tenant_access`, `require_transaction_access`. Repositories also filter `tenant_id`.

Postgres RLS on some tables is **defense in depth**. The API uses the Supabase **service-role** client, which can bypass RLS. Do not claim RLS is the primary control.

## Roles

`UserRole` (`app/models/enums.py`): Agent, TransactionCoordinator, TeamLead, Attorney, Admin, Client, ForSaleByOwner, Vendor.

Hierarchy (`ROLE_HIERARCHY` / `role_has_permission`): Admin satisfies every role check. TeamLead satisfies TeamLead, Agent, and TransactionCoordinator. Agent, TC, Attorney, Client, FSBO, and Vendor satisfy only themselves.

`is_platform_admin` is a **separate flag**, not a `UserRole`. Tenant Admin cannot call `/api/v1/platform/*`. Those routes use `require_platform_admin` (flag + session `aal=aal2` + a live TOTP factor).

Workspace owner (`is_tenant_owner`) bypasses `require_role` minimums on management surfaces so a founder labeled Agent is not locked out of their own tenant settings. Identity portals (Client / FSBO / Vendor) still require an exact role (`require_exact_roles` / `RoleRoute`).

## Least privilege examples

| Resource | Who |
| --- | --- |
| `PATCH /users/me` | Any authenticated user, own row only |
| `GET /users/{id}`, `PUT /users/{id}/role` | Tenant Admin (or owner), **same tenant** (`require_tenant_access`) |
| Create transaction | Staff roles; Client **403** (`test_client_role_cannot_create_transaction`) |
| Transaction by id | Same tenant; Agent/TC/Attorney only if creator or assigned |
| Gmail tokens | That user's `integrations` row, not every mailbox in the tenant |
| `/api/v1/platform/*` | Platform admin + AAL2, not tenant Admin |

## Staging measurement (31 Aug 2026)

See `CASA_3_1_1_deny.png`. Unsigned `GET /api/v1/users/` and `GET /api/v1/platform/users` both return **401**. No other tenant's data was requested. Platform AAL2 is enforced in `require_platform_admin` (tests in `test_mfa_api.py`); this row does not attach a live AAL2 403.

## Tests (names to cite)

`test_rbac.py`: hierarchy; Client cannot create a transaction; Agent cannot `GET /users/{other}`.  
Isolation (M9f): `test_two_self_registrations_get_isolated_tenants`, `test_tenant_admin_cannot_read_another_tenant_by_id`, `test_admin_cannot_manage_user_in_another_tenant`, `test_task_get_by_id_respects_tenant_filter`, `test_api_key_acts_only_in_its_own_tenant`, FSBO cross-owner 404s.

## Do not claim

- RLS as the primary control.
- That a tenant Admin is a platform admin.
- A live Agent-vs-Admin probe on staging (this pack used the platform-admin QA account plus unsigned calls).
- MFA for **all** users; HttpOnly cookies.

## Portal comment

```
Access control is enforced on the API (FastAPI), not only in the browser. Roles are Agent, TransactionCoordinator, TeamLead, Attorney, Admin, Client, ForSaleByOwner, and Vendor. Endpoints use get_current_user plus require_role, require_tenant_access, and require_transaction_access. Tenant Admin is not cross-tenant. Platform /api/v1/platform/* requires is_platform_admin and AAL2. Staging unsigned GET /users/ and GET /platform/users return 401. Postgres RLS is defense in depth; the API is the trusted layer.
```
