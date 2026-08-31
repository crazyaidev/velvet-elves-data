# CASA 2.2.1 — Logout invalidates stateful session tokens

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 3.3.1  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

Code snippets **or** documentation showing logout and expiration invalidate session tokens, including refresh tokens.

Verification: server-side session invalidation on user logout and session expiration.

## Logout process

Users can log out from the app menu (**Log Out**) and from the platform MFA gate (**Sign out**).

1. `AuthContext.logout()` `POST`s `/api/v1/users/logout` with `Authorization: Bearer` (`keepalive`, best-effort).
2. `POST /users/logout` decodes the JWT. If it is valid it calls GoTrue `auth.admin.sign_out(token, "local")` — this session’s refresh token is revoked. Invalid/expired bearer still returns **204** so the client can always finish sign-out.
3. The SPA then clears `velvet_elves_token` and `velvet_elves_refresh_token` and sends the user to `/login`.

The access JWT is stateless and expires on its own (row **2.2.3**, under 24 hours). Logout’s server-side job is the **stateful refresh token**. Scope is `local` (this session), not every device.

## Staging check

Login → `POST /users/logout` **204** → replay the same refresh token to `POST /users/refresh` → **401** Refresh token is invalid or expired.

## Portal comment

```
Users can log out from the app menu. Logout calls POST /users/logout, which revokes this Supabase session (GoTrue admin sign_out) and then clears browser storage. Replaying the refresh token after logout returns 401. The short-lived access JWT expires on its own (under 24 hours).
```
