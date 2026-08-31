# CASA 2.2.3 — Stateless authentication tokens expire within 24 hours

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 3.3.4  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

Code snippets, **screenshot**, or documentation of the validity period of stateless session tokens.

Verification: expiration **within 24 hours** of issue.

## What is in scope

The Velvet Elves login session is two tokens:

| Token | Kind | This row |
| --- | --- | --- |
| Access JWT (`velvet_elves_token`) | **Stateless** signed JWT. API verifies signature and `exp`. | **Yes** — must expire within 24 hours. |
| Refresh token (`velvet_elves_refresh_token`) | **Stateful** GoTrue session. Revoked on logout (2.2.1) and on password change (2.2.2). | **No** — ADA 2.2.3 is for non-revocable stateless tokens. |

`TokenResponse` returns `access_token` and `refresh_token`. Lifetime is in the JWT `iat` / `exp` claims, not an `expires_in` field on that schema.

## Staging measurement (28 Aug 2026)

`POST /users/login` on `api.stage.velvetelves.com`, then decode the access JWT payload (token never printed or screenshotted):

- Algorithm: **ES256**
- `exp − iat` = **28800 seconds (8.00 hours)**
- ADA cap: 86400 seconds (24 hours)
- Under 24 hours: **yes**

Do not claim the GoTrue **default** of 1 hour. This project’s issued access JWT is **8 hours**.

## How expiry is enforced

1. GoTrue sets `exp` when it issues the JWT.
2. `decode_access_token` (`app/utils/security.py`) verifies the JWT. `jose` raises `JWTError` on expired or tampered tokens. The API then returns 401.
3. The SPA reads `exp` via `getTokenExpirationMs` (`src/utils/jwt.ts`) and silent-refreshes about 60 seconds before expiry (`TOKEN_REFRESH_LEAD_MS`). If refresh fails, it signs the user out.

## Out of scope for this row

- Invite activation tokens (72 hours today) — capability tokens, not the session JWT (1.1.2).
- Password-reset recovery links — OOB verifiers (1.3.1).
- Gmail / Calendar mailbox OAuth tokens — not login sessions.
- Refresh-token lifetime — stateful; covered by 2.2.1 / 2.2.2.

## Do not claim

- A 1-hour access JWT (measured 8 hours).
- That the refresh token expires within 24 hours.
- HttpOnly session cookies; MFA for all users; pasting JWTs or secrets.

## Portal comment

```
The user session access token is a signed JWT. On staging (28 Aug 2026) exp minus iat is 28800 seconds (8 hours), under ADA's 24-hour cap. The API rejects expired JWTs. The app reads exp and refreshes about a minute before expiry. The refresh token is a separate, revocable session token (see 2.2.1), not the stateless token this row covers.
```
