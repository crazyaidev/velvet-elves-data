# CASA 2.3.4 — Stateless session tokens shall use digital signatures

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 3.5.3  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

Testing results from a scan completed using ADA DAST guidance.

Verification: the scan shall **not** identify Burp **2099456** (JWT signature not verified) or **2099457** (JWT none algorithm supported).

## How Velvet Elves verifies the session JWT

`decode_access_token` (`app/utils/security.py`) uses `jose.jwt.decode`:

- Staging access JWT **alg** measured 28 Aug 2026 on 2.2.3: **ES256**.
- HS256 tokens are verified with `SUPABASE_JWT_SECRET` (algorithms list is `["HS256"]` only).
- Otherwise the header `kid` is resolved from GoTrue JWKS and the token is verified as ES256 or RS256.
- `aud` must be `authenticated`. Issuer is the project's GoTrue URL when configured.
- `jose` raises `JWTError` on invalid, expired, or tampered tokens. `get_current_user` maps that to **401**.

Unit tests in `app/tests/test_security.py`: invalid string, truncated/tampered token, expired token, wrong audience, wrong secret — all raise `JWTError`.

## Official DAST

Official ADA ZAP scans: SPA `10f54abf`, API `a9d78f05`, authenticated API `33afa2aa` (Bearer via Replacer). `DAST_SUMMARY.md` alert tables do **not** list JWT signature-not-verified or JWT none-algorithm findings. Those Burp IDs are not ZAP plugin IDs; the ZAP CASA conf does not map 2099456 / 2099457.

## Staging reject (not a forged token)

`GET /users/me` with no `Authorization`, and with `Authorization: Bearer not-a-jwt`, both return **401**. Token values are not shown.

Gmail / Calendar OAuth tokens are Fernet-encrypted at rest in `integrations`. They are not the session JWT.

## Do not claim

- That official ZAP ran Burp JWT plugins 2099456 / 2099457.
- An explicit `alg == "none"` denylist line in app code (verification is `jwt.decode` with HS256 or JWKS algorithms).
- HttpOnly session cookies; pasting JWTs or `SUPABASE_JWT_SECRET`.

## Portal comment

```
The user session is a signed JWT. Staging issues ES256. The API verifies the signature with jose (HS256 secret or JWKS for ES256/RS256) and rejects invalid, expired, or tampered tokens with 401. Official ADA ZAP scans did not report JWT signature-not-verified or JWT none-algorithm findings. Gmail and Calendar tokens are Fernet-encrypted at rest and are not the session JWT.
```
