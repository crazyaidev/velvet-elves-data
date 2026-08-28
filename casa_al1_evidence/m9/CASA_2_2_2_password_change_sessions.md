# CASA 2.2.2 — Terminate other sessions after password change

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 3.3.3  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

Code snippets **or** documentation showing how session invalidation is handled after a successful password change (including reset/recovery).

Verification: other active sessions (including stateful refresh tokens) are terminated **or** the user is given an option to terminate them.

## Password-change path

Velvet Elves has no logged-in “change password with current password” form. The product path is **Forgot password** / recovery:

1. User requests a reset (`POST /users/password-reset/request` or seller/partner **Email reset link**).
2. User opens the recovery link and sets a new password (`POST /users/password-reset/confirm`).
3. Confirm returns “Password updated successfully. Please sign in.” The SPA shows **Password updated** and redirects to `/login`.

## How other sessions are terminated

Confirm does not call `sign_out` itself. It updates the password through GoTrue, which **by default** deletes other `auth.sessions` rows for that user:

| Confirm path | GoTrue call | Session effect (GoTrue `User.UpdatePassword`) |
| --- | --- | --- |
| Recovery access + refresh tokens | `auth.update_user({password})` with a session | `LogoutAllExceptMe` — every **other** session is deleted; the recovery session is kept. The SPA does not keep that session; it sends the user to sign in. |
| JWT `sub` or PKCE code | `auth.admin.update_user_by_id(..., {password})` | `UpdatePassword(tx, nil)` → `Logout` — **all** sessions for that user are deleted. |

Public source (do not treat as a dashboard toggle): `github.com/supabase/auth` `internal/models/user.go` (`UpdatePassword`) and `internal/api/admin.go` (admin password update passes `sessionID = nil`). Vendor sessions docs also list “the user changes their password” as a session-termination reason.

That is ADA’s “acts by default.” There is no in-app checkbox because there is no in-app password form.

## Federated login / relying parties

Google Sign-in (if used) is a GoTrue session on the same `user_id`. `Logout` / `LogoutAllExceptMe` delete those rows too.

Gmail / Calendar **mailbox** OAuth tokens live in `integrations` and are not Velvet Elves login sessions. This row does not claim those tokens are wiped on password reset.

Velvet Elves is not an IdP for third-party relying parties.

## What we did not do

We did **not** live-reset a staging platform-admin password or run a two-device refresh-replay after a real reset. AL1 is code or documentation.

## Do not claim

- An in-app current-password change form.
- That we call `sign_out(scope="others")` or `scope="global"` in app code.
- That leftover access JWTs die immediately (they expire on their own; see 2.2.3).
- That “Secure password change” / “Require current password” dashboard toggles are the session-kill switch (those are reauth-to-change).
- HttpOnly session cookies; ADA-approved IdP.

## Portal comment

```
Password change is through password reset (Forgot password), not an in-app current-password form. Confirm updates the password in Supabase Auth. GoTrue then terminates other sessions by default: a recovery session logs out every other session; an admin password update logs out all sessions for that user. After a successful reset the app sends the user to sign in. Short-lived access JWTs expire on their own (under 24 hours).
```
