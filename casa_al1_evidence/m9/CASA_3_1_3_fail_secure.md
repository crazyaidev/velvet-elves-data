# CASA 3.1.3 — Access controls fail securely

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 4.1.5  
**Date:** 31 Aug 2026  

ADA note: **3.1.1–3.1.3 share one written description.** Roles and API guards are in `CASA_3_1_1_least_privilege.md`. This row is **fail closed**: missing or bad credentials do not grant access; denials are 401/403 (or 404 that hides the object); exceptions do not open the resource.

## ADA AL1 verification

Access controls shall fail securely, including when an exception occurs.

## How Velvet Elves fails closed

| Failure | Result |
| --- | --- |
| No `Authorization` | FastAPI `OAuth2PasswordBearer` → **401** Not authenticated |
| Invalid / expired / garbage JWT | `JWTError` in `get_current_user` → **401** Could not validate credentials |
| JWT `sub` with no profile | **401** |
| Inactive user | **403** Account is inactive |
| Suspended tenant (non-platform) | **403** |
| Role / tenant / assignment miss | **403** (some cross-owner reads **404**, still deny) |
| Cron tick with missing/wrong `X-VE-Cron-Secret` | **403**; unset secret is unreachable (fail closed) |
| Unhandled exception | Generic **500** `"An internal server error occurred."` — not a successful read |

`require_role` and `require_tenant_access` raise HTTPException; they do not return an empty 200. Tests: `test_get_me_unauthenticated_returns_401`, `test_client_role_cannot_create_transaction` (403), `test_unauthenticated_transaction_request_returns_401`, cron fail-closed in `test_schedule_tick_and_digest.py`.

## Staging measurement (31 Aug 2026)

See `CASA_3_1_3_fail.png`.

- `GET /users/me` no Authorization → **401**
- `GET /users/me` `Bearer not-a-jwt` → **401**
- `POST /internal/schedules/tick` no cron header → **403**

The tick was not run. No other tenant was queried.

## Do not claim

- That every deny is 403 (missing auth is 401).
- Stack traces in API JSON (unhandled path is a generic 500 message).
- MFA for all users; HttpOnly cookies.

## Portal comment

```
Access control fails closed. Missing Authorization returns 401. An invalid JWT raises JWTError and returns 401; it does not load a user. Role, tenant, and assignment misses return 403 (some cross-owner reads return 404). The scheduler tick requires X-VE-Cron-Secret and fails closed if the secret is unset. Unhandled exceptions return a generic 500, not the resource. Staging: GET /users/me without Authorization and with Bearer not-a-jwt both 401; POST /internal/schedules/tick without the cron header returns 403.
```
