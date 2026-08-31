# CASA 1.1.1 — Authentication is resistant to brute force attacks

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 2.2.1  
**Date:** 27 Aug 2026 (rewritten after the login-hardening code landed; deploy to production before rendering/uploading this page)  
**Do not claim:** that Supabase Auth is on an ADA-approved IdP list; CAPTCHA; MFA default for **all** users; a live breached-password API (HIBP) — our denylist is a static in-repo list.

## AL1 evidence the lab asked for

### 1. External user authentication services

| Service | Used for | ADA-approved IdP? |
| --- | --- | --- |
| **Supabase Auth** (GoTrue) | Velvet Elves email/password login, register, invite accept, password reset, JWT issue/refresh, TOTP MFA factors | **Not claimed.** Treat as a non-ADA-approved external auth service unless TAC confirms otherwise. |
| **Google OAuth (authorization code + PKCE)** | Gmail and Google Calendar **integrations only**. Not the Velvet Elves login IdP. | Out of scope for 1.1.1 password brute force. Covered under 3.2.x. |

We do not operate a custom password hasher. `POST /api/v1/users/login` calls `supabase.auth.sign_in_with_password()`. Passwords are not stored in our tables (see 1.1.3 / M9d).

### 2. Password policy (proprietary / our wrapper)

- Register, invite accept, and password change require **minimum 8 characters** (`Field(min_length=8)` in `app/schemas/user.py` and `invitation.py`).
- API also requires **at least one digit**.
- API rejects passwords on a **common/breached-password denylist** (~200 top entries from public breach corpora, checked case-insensitively in `app/core/weak_passwords.py`; shared by register, invite accept, and password reset). This is a **static in-repo list**, not a live HIBP lookup — say so if asked.
- SPA register/invite UI additionally requires uppercase, lowercase, digit, and symbol (`passwordPolicy` in `PasswordStrengthIndicator.tsx`).

### 3. Anti-automation

| Control | Status |
| --- | --- |
| Register rate limit | **Yes.** `POST /api/v1/users/register` is 5 requests / 60 seconds per address (`_register_limiter`). Test: `test_registration_is_rate_limited`. |
| Login rate limit in our API | **Yes.** `POST /api/v1/users/login` is 10 requests / 60 seconds per IP (`_login_limiter`). Test: `test_login_is_rate_limited_per_ip`. |
| Per-account soft lockout | **Yes.** 20 failed attempts per account per rolling hour, keyed on the submitted email whether or not the account exists, cleared on success (`app/core/login_throttle.py`). Survives IP rotation. Test: `test_login_account_lockout_survives_ip_rotation`. |
| CAPTCHA | **No.** |
| MFA default for all users | **No.** TOTP MFA **is enforced for platform administrators** (see 3.3.1) and available to any account via `/users/mfa/*`; ordinary tenant users are not forced to enroll. |
| Unfamiliar-device OTP | **No.** |

Supabase Auth applies its own project-level rate limits on top (dashboard: Authentication → Rate Limits). Attach a screenshot of that page for production as supporting evidence. Do not invent numbers. Do not screenshot secrets.

**Honest scaling note:** the limiter and throttle are in-process. With N backend tasks the worst-case ceiling multiplies by N (production runs 2 tasks → worst case 40 failures/hour/account), still well under the ADA 100/hour ceiling.

### 4. Screenshots to attach with this note

1. Login 429: eleven `POST /api/v1/users/login` attempts from one client in one minute — later calls **429** (matches the unit test). Use staging.
2. Login lockout 429 with rotating IPs after 20 failures for one account (matches `test_login_account_lockout_survives_ip_rotation`) — cite the test if a live replay is impractical.
3. Register 429: six `POST /api/v1/users/register` from one client in one minute (matches the unit test).
4. Weak-password rejection: register with `password123` → 422 "too common".
5. Optional: Supabase Auth Rate Limits page for the **production** project (no API keys in frame).
6. Optional: register UI password rules (8 + complexity).

## Verification mapping (AL1)

ADA: an ADA-approved IdP **or** at least **one** of 2.1–2.5.

| Option | Velvet Elves |
| --- | --- |
| 1 ADA-approved IdP | Not claimed for Supabase. |
| 2.1 ≤100 failed logins / account / hour | **Pass.** Our login route enforces 20 failed attempts / account / hour (worst case 40 with two tasks — still ≤100), plus 10/min/IP, plus Supabase vendor limits. |
| 2.2 CAPTCHA | No. |
| 2.3 MFA default all users | No (platform admins only — see 3.3.1). |
| 2.4 Min 8 + no weak/breached passwords | **Pass:** min 8 + digit + static common-password denylist (API), stronger UI rules. Not a live HIBP check. |
| 2.5 Unfamiliar device/location step-up | No. |

**Attestation for TAC:** we meet **2.1** (per-account failure ceiling in our login route, plus vendor limits) and **2.4** (min length 8 + digit + common-password denylist). Register endpoint is separately rate-limited. TOTP MFA is enforced for platform administrators.

## Portal comment

```
Login is rate-limited to 10 requests/minute/IP and locked after 20 failed attempts per account per hour. Passwords require min 8 characters, a digit, and reject common passwords (static denylist, not a live HIBP API). Register is rate-limited to 5/minute. TOTP MFA is enforced for platform admins (not all users). CAPTCHA is not used; ADA 1.1.1 is met via options 2.1 and 2.4. Supabase vendor limits apply on top (30 sign-in requests / 5 min / IP).
```
