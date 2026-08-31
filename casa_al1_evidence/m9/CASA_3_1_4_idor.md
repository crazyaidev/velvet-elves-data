# CASA 3.1.4 — Sensitive resources protected against IDOR

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 4.2.1  
**Date:** 31 Aug 2026  

ADA AL1 wants (1) a list of APIs where the user supplies a URL or parameter ID, and (2) a written description of how those APIs are protected from Insecure Direct Object Reference. Verification: a process is in place to mitigate IDOR.

## APIs that take a user-supplied object ID

Path IDs (not an exhaustive nested list; these families cover the sensitive records):

| Family | Example paths | Guard |
| --- | --- | --- |
| Users | `GET /users/{user_id}`, `PUT /users/{user_id}/role`, `DELETE /users/{user_id}` | Admin + `require_tenant_access` |
| Tenants | `GET/PUT/DELETE /tenants/{tenant_id}` | `require_platform_admin` (tenant Admin is not cross-tenant) |
| Transactions | `GET/PATCH /transactions/{id}` and nested parties / plan / assignments | `require_transaction_access` (tenant + assignment) |
| Documents | `GET /documents/{document_id}`, `GET /documents/transaction/{transaction_id}` | Transaction access; unrelated document **404** |
| Invoices / payments | `GET /invoices/{invoice_id}`, `GET /payments/{payment_id}` | Load by `tenant_id`; Agents scoped to accessible deals |
| Tasks | `GET /tasks/{task_id}` | Transaction access; repo also filters `tenant_id` |
| Teams | `GET/PUT /teams/{team_id}` | Same tenant |
| Audit | `GET /audit-logs/{entity_type}/{entity_id}` | Admin/TeamLead; `get_for_entity(tenant_id, …)` |
| Platform | `/api/v1/platform/tenants/{tenant_id}/…`, `/platform/users/{id}` | `is_platform_admin` + AAL2 |

List endpoints (`GET /transactions`, `GET /users/`, `GET /contacts/`) are tenant-scoped (and assignment-scoped for Agents). They are not a global dump.

Public invoice / invite / share links may carry a **capability token** in the URL. Those are not the user session JWT (see 2.1.1). They are not listed here as session IDOR.

## How IDOR is mitigated

Knowing a UUID is not enough.

1. Missing or invalid JWT → **401** (no object is loaded for the caller).
2. The API loads the row, then `require_tenant_access` → **403** if the object's `tenant_id` is not the caller's (platform admins excepted). Tenant Admin is **not** cross-tenant (`test_tenant_admin_cannot_read_another_tenant_by_id`, `test_admin_cannot_manage_user_in_another_tenant`).
3. Deal objects use `require_transaction_access`: missing row **404**; other tenant **403**; Agent/TC/Attorney must be creator or assigned else **403** (`test_agent_cannot_get_other_users_transaction_by_id`).
4. Some cross-owner reads return **404** (FSBO, unrelated documents) so the object is not confirmed.
5. Audit entity reads filter `current_user.tenant_id` (`test_entity_audit_logs_do_not_leak_across_tenants`).
6. Postgres RLS is defense in depth. The API uses the service-role client, so the FastAPI checks are the control.

## Staging measurement (31 Aug 2026)

See `CASA_3_1_4_deny.png`. Unsigned GETs of placeholder UUIDs on `/transactions/{id}`, `/users/{id}`, `/tenants/{id}`, `/documents/{id}`, and `/invoices/{id}` all return **401**. No other tenant was queried. No staging user was registered.

## Do not claim

- A live authenticated two-tenant IDOR replay this session (`QA_PASSWORD` was not set).
- That ZAP proved IDOR-free (official scans did not run WSTG-ATHZ-04).
- That **every** object route uses `require_tenant_access` (`GET /contacts/{id}` compares `tenant_id` and currently skips that deny when `role == Admin`).
- RLS as the primary control; MFA for all users; HttpOnly cookies.

## Portal comment

```
User-supplied object IDs appear in paths such as /users/{id}, /tenants/{id}, /transactions/{id}, /documents/{id}, /invoices/{id}, /tasks/{id}, /teams/{id}, and /audit-logs/{type}/{id}. Knowing a UUID is not enough. After JWT verification the API loads the row and checks tenant (require_tenant_access) and, for deals, assignment (require_transaction_access). Lists are tenant-scoped. A tenant Admin cannot read or change another org's tenant or users (403). Cross-owner FSBO and unrelated document reads return 404. Staging unsigned GET of those ID paths with a placeholder UUID returns 401.
```
