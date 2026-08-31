# CASA 3.1.2 — Access-control attributes cannot be set by the end user

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 4.1.2  
**Date:** 31 Aug 2026  

ADA note: **3.1.1–3.1.3 share one written description.** Roles, JWT session, and API guards are in `CASA_3_1_1_least_privilege.md`. This row is the attribute rule: **role, tenant, platform-admin flag, and active flag used by access control are not taken from client-controlled fields** unless that change is an authorized admin/invite path.

## ADA AL1 verification

User and data attributes and policy information used by access controls shall **not** be manipulated by the end user.

## Where policy attributes come from

`get_current_user` verifies the JWT `sub`, then loads `role`, `tenant_id`, `is_platform_admin`, and `is_active` from the **server profile**. It does not take those fields from the request JSON.

| Attribute | Self-service | Authorized path |
| --- | --- | --- |
| `tenant_id` | Register `tenant_id` is **ignored**; server mints a new tenant. OAuth `user_metadata.tenant_id` is ignored. | Invitation join. `X-Workspace-Id` only if the user has an **active membership**. |
| `role` | `PATCH /users/me` has no `role`. Onboarding company patch drops `role`. | Founder may pick a self-signup role on a **new** tenant only. Later changes: `PUT /users/{id}/role` by tenant Admin/owner, same tenant; owner role is locked. |
| `is_platform_admin` | No self-service field. Tests set it in the DB. | Not a public product toggle. |
| `is_active` | Removed from `UserUpdateRequest`. Extra `is_active` on PATCH /me is ignored (`test_profile_update_cannot_self_deactivate`). | Tenant Admin deactivate / platform deactivate. |

## Tests to cite

- `test_register_mints_fresh_tenant_and_ignores_client_supplied`
- `test_oauth_exchange_ignores_client_supplied_tenant_id`
- `test_profile_update_cannot_self_deactivate`
- `test_company_patch_role_is_ignored`

## Staging measurement (31 Aug 2026)

Unsigned `PATCH /users/me` with `role`, `tenant_id`, `is_platform_admin`, and `is_active` in the JSON returns **401**. No account was registered. No other tenant was joined.

## Do not claim

- That register ignores **role** entirely (a founder may choose Agent / TeamLead / TC / Admin on the **new** tenant).
- That `X-Workspace-Id` is ignored (it is allowed only for an active membership).
- RLS as the primary control; MFA for all users; HttpOnly cookies.

## Portal comment

```
Role, tenant, platform-admin, and active flags used for access control come from the server profile after JWT verification, not from client JSON. Register ignores client tenant_id and mints a new tenant. OAuth ignores user_metadata tenant_id. PATCH /users/me has no role, tenant_id, is_platform_admin, or is_active fields; extra is_active is ignored. Role changes after signup go through PUT /users/{id}/role in the same tenant. Staging unsigned PATCH /users/me with those extra fields returns 401.
```
