# CASA 2.4.1 — Full login session or re-auth before sensitive account changes

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 3.7.1  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

Code snippets **or** documentation that the user has a full login session **or** an account verification process before account modifications or sensitive data transactions.

Verification (AL1): either a full login session **or** an account verification process before those changes.

This is an **or**. A valid session is enough. Step-up password re-entry on every save is not required.

## What the product does

| Change | Gate | Kind |
| --- | --- | --- |
| Profile (name, phone, bio, avatar) | `PATCH /users/me` → `Depends(get_current_user)` | Full login session (signed JWT) |
| Sign-in email (self-service) | Same `PATCH /users/me`; applied with `email_confirm=True` | Full login session. **Not** restricted. **Not** a new-inbox confirm. |
| Password | `POST /users/password-reset/request` then confirm with the recovery token from email | Secondary / OOB verification. Not an in-session current-password form. |
| Turn MFA off | `POST /users/mfa/disable` with a current TOTP code | Secondary verification. A leftover `aal2` JWT is not enough. |
| Platform admin mutations | `require_platform_admin` | Valid session **and** `aal=aal2` plus a live TOTP factor (3.3.1). |

`get_current_user` (`app/core/auth.py`) verifies the JWT (`decode_access_token`), loads the profile, and rejects inactive users. Missing or garbage `Authorization` → **401**.

The SPA account screens (`/settings/account`, `/settings/security`) sit behind `ProtectedRoute`. Unauthenticated callers are sent to `/login`. The API is the enforcement; the route guard is UX.

## Staging measurement (28 Aug 2026)

`api.stage.velvetelves.com`:

- `PATCH /api/v1/users/me` with no Authorization → **401**
- `PATCH /api/v1/users/me` with `Authorization: Bearer not-a-jwt` → **401**
- `GET /api/v1/users/me` with no Authorization → **401**
- `GET /api/v1/users/me` with a valid login JWT → **200**

No email address was changed on the QA account. No MFA factor was removed.

## Do not claim

- A password re-prompt (current password) before `PATCH /users/me`.
- That self-service email change is restricted or requires confirming the new inbox (`email_confirm=True` applies it immediately).
- MFA default for **all** users (platform admins are gated; others may enroll).
- HttpOnly session cookies.

## Portal comment

```
Profile and sign-in email changes require a valid JWT session (PATCH /users/me). Staging calls without Authorization, or with Bearer not-a-jwt, return 401. Password change uses a recovery email, not an in-session current-password form. Disabling MFA requires a current authenticator code. Platform admin routes require AAL2. We do not claim a password re-prompt on every profile save.
```
