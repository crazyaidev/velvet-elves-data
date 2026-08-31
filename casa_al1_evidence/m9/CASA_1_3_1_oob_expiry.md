# CASA 1.3.1 — Out of band verifier shall expire in a reasonable timeframe

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 2.7.2  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

1. List external user authentication services.
2. If proprietary, describe the out-of-band verifier expiration process.

Verification if not an ADA-approved IdP:

- Password reset verifiers (email links) expire after **7 days** (maximum).
- MFA-related verifiers (e.g. TOTP) expire after **30 minutes**.

## External services

| Service | OOB verifiers | ADA-approved IdP? |
| --- | --- | --- |
| **Supabase Auth (GoTrue)** | Password-reset recovery email; signup email confirmation; TOTP MFA factors | **Not claimed.** |
| **Google OAuth** | Not an email/SMS verifier for Velvet Elves login | Out of scope for 1.3.1. |

We do not send SMS OTPs. Invite activation tokens are 1.1.2 (72 hours), not this row.

## Expiration process

Velvet Elves does not generate proprietary reset codes. `POST /users/password-reset/request` calls `supabase.auth.reset_password_email` (always 202; no email enumeration). Confirm requires the recovery token from the email (`POST /users/password-reset/confirm`). Opening `/reset-password` with no token shows **Invalid or expired link** and cannot set a password.

GoTrue enforces Email OTP / recovery-link expiry. Auth Email settings: **Email OTP expiration = 3600 seconds (1 hour)**. That matches the SPA copy **Link expires in 1 hour** (`ForgotPasswordPage.tsx`). ADA allows up to 7 days.

TOTP: authenticator codes use the standard `otpauth://totp/` 30-second time step (RFC 6238 default; our provisioning URI does not set a longer period). That is under ADA’s 30-minute MFA verifier limit.

## Portal comment

```
Password reset uses a Supabase Auth recovery email. Auth Email OTP expiration is 3600 seconds (1 hour), matching the app copy. Opening /reset-password without a valid token shows Invalid or expired link and cannot set a password. TOTP MFA codes use a 30-second time step, under ADA's 30-minute MFA verifier limit. We do not send SMS OTPs.
```
