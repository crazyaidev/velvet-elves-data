# CASA 1.3.2 — Out of band verifier shall only be used once

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 2.7.3  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

1. List external user authentication services.
2. If proprietary, describe the out-of-band verifier process (single use).

Verification: ADA-approved IdP **or** the OOB verifier can be used only once.

## External services

| Service | OOB verifiers | ADA-approved IdP? |
| --- | --- | --- |
| **Supabase Auth (GoTrue)** | Password-reset recovery email/OTP; signup confirmation; TOTP MFA | **Not claimed.** |
| **Google OAuth** | Not an email/SMS login verifier | Out of scope for 1.3.2. |

No SMS OTPs. Invite-token single-use is 1.1.2.

## Single-use process

Velvet Elves does not mint proprietary reset codes. `POST /users/password-reset/request` sends a GoTrue recovery email. `POST /users/password-reset/confirm` accepts that recovery token (or PKCE auth code) once. A missing, invalid, or already-consumed token returns **400 Invalid or expired reset token. Please request a new one.** The SPA `/reset-password` without a token shows **Invalid or expired link** and **Request a new link** — it cannot set a password.

Staging live: the same non-recovery token posted twice to confirm both return 400; neither sets a password.

TOTP: GoTrue opens a challenge then verifies the current authenticator code. Codes rotate every 30 seconds. We do not persist a reusable email OTP in application tables.

## Portal comment

```
Password reset recovery links are issued by Supabase Auth and cannot be reused. Confirm requires a valid recovery token from the email. A missing, used, or invalid token returns Invalid or expired reset token and cannot set a password. The reset page with no token shows Invalid or expired link and asks the user to request a new one. TOTP MFA is verified through a GoTrue challenge; codes rotate every 30 seconds. We do not send SMS OTPs.
```
