# CASA 2.2.3 — Stateless authentication tokens expire within 24 hours

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 3.3.4  
**Date:** 31 Aug 2026  

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

## Staging and production measurement (31 Aug 2026)

GoTrue **Authentication → Sessions**: **Access token expiry time = 3600 seconds** on both VelvetElves Stage and production.

`POST /users/login` on `api.stage.velvetelves.com` after that staging change, then decode the access JWT payload (token never printed or screenshotted):

- Algorithm: **ES256**
- `exp − iat` = **3600 seconds (1.00 hour)**
- ADA cap: 86400 seconds (24 hours)
- Under 24 hours: **yes**

Earlier on 31 Aug (and on 28 Aug) the same staging login issued **28800 seconds (8 hours)**. Do not paste that older lifetime into the portal comment.

The Stage project's orange **PRODUCTION** badge is the primary-branch label, not the production app host.

## How expiry is enforced

1. GoTrue sets `exp` when it issues the JWT.
2. `decode_access_token` (`app/utils/security.py`) verifies the JWT. `jose` raises `JWTError` on expired or tampered tokens. The API then returns 401.
3. The SPA reads `exp` via `getTokenExpirationMs` (`src/utils/jwt.ts`) and silent-refreshes about 60 seconds before expiry (`TOKEN_REFRESH_LEAD_MS`). If refresh fails, it signs the user out.

## Out of scope for this row

- Invite activation tokens (72 hours today) — capability tokens, not the session JWT (1.1.2).
- Password-reset recovery links — OOB verifiers (1.3.1).
- Gmail / Calendar mailbox OAuth tokens — not login sessions.
- Refresh-token lifetime — stateful; covered by 2.2.1 / 2.2.2.
- **Inactivity timeout** / **Time-box user sessions** (both 0 = never on the Sessions PNGs) — not the access JWT `exp`.

## Do not claim

- That staging still issues an 8-hour access JWT (owner set 3600 s on 31 Aug).
- That the refresh token expires within 24 hours.
- HttpOnly session cookies; MFA for all users; pasting JWTs or secrets.

## Portal comment

```
The user session access token is a signed JWT. Production and staging GoTrue Sessions both set access token expiry to 3600 seconds (1 hour). Staging login on 31 Aug 2026 issued tokens with exp minus iat of 3600 seconds. Both environments are under ADA's 24-hour cap. The API rejects expired JWTs. The app reads exp and refreshes about a minute before expiry. The refresh token is a separate, revocable session token (see 2.2.1), not the stateless token this row covers.
```
