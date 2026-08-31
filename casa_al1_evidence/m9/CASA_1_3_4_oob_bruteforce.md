# CASA 1.3.4 — Out of band verifier shall be resistant to brute force attacks

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 2.7.6  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

1. List external user authentication services.
2. If proprietary, describe generation **and** any rate-limiting on validation.

Verification if not an ADA-approved IdP:

- Codes contain at least **20 bits** of entropy (ADA: typically a six-digit random number is sufficient).
- If the secret has **less than 64 bits**, the application shall implement a rate-limiting mechanism.

## External services

| Service | OOB verifiers | ADA-approved IdP? |
| --- | --- | --- |
| **Supabase Auth (GoTrue)** | Password-reset recovery email / Email OTP; TOTP MFA | **Not claimed.** |
| **Google OAuth** | Not an email/SMS login verifier | Out of scope for 1.3.4. |

No SMS OTPs. Invite-token entropy is included because it is the only OOB-style code Velvet Elves mints; accept-path rate limits are not required once entropy is ≥64 bits.

## Entropy

| Verifier | What it is | Entropy | vs 20 / 64 bits |
| --- | --- | --- | --- |
| Email OTP | 8 decimal digits (Auth Email setting) | log2(10^8) ≈ **26.6 bits** | ≥20, **<64** → rate limit required |
| Recovery link | Hashed GoTrue token / PKCE code in the email, not an 8-digit code the app stores | **>64 bits** | Rate limit not required by ADA item 3 |
| Invite token | `uuid.uuid4().hex` (32 hex; 122 random bits) | **>64 bits** | Rate limit not required by ADA item 3 |
| TOTP | 6 digits, 30 s step (RFC 6238; ADA’s typical 20-bit example) | **~20 bits** | ≥20, **<64** → rate limit required |

Velvet Elves does not mint reset OTPs. `POST /users/password-reset/request` calls `reset_password_email`. Confirm uses the vendor recovery token. Guessing that token returns **400** and cannot set a password.

## Rate limiting (secrets <64 bits)

**Email OTP / magic-link verify (GoTrue, customizable):** production Auth Rate Limits: **token verifications = 30 requests / 5 minutes / IP** (360/hour). That is the OTP and magic-link verify bucket. Password-reset **emails** are also capped at **30 / hour**.

**TOTP (GoTrue, not customizable):** official docs (supabase.com/docs/guides/auth/rate-limits): MFA challenge and verify are **15 requests / hour / IP**. `POST /users/mfa/verify` calls GoTrue `factors/:id/challenge` then `factors/:id/verify`. Velvet Elves does **not** attach a separate in-app limiter on confirm or MFA verify.

Login IP limiter (10/min) and account lockout (20 failures/hour) are **1.1.1**, not this row.

## Portal comment

```
Out-of-band reset codes meet ADA's 20-bit entropy floor. Email OTP is 8 digits (about 27 bits). Recovery links use a hashed GoTrue token with well over 64 bits. Because the 8-digit OTP is under 64 bits, GoTrue rate-limits OTP and magic-link verifications to 30 requests per 5 minutes per IP. Password-reset emails are capped at 30 per hour. TOTP is 6 digits (ADA's typical 20-bit example) and GoTrue limits MFA challenge and verify to 15 requests per hour per IP. Guessing a reset token returns 400 and cannot set a password. We do not send SMS OTPs.
```
