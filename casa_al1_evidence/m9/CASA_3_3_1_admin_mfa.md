# CASA 3.3.1 — Platform administrative interface enforces TOTP MFA

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 4.3.1  
**Date:** 31 Aug 2026  

ADA: application-exposed administrative interfaces must enforce MFA for administrative accounts. Infrastructure consoles (GCP, AWS) are out of this check. AL1: evidence that those interfaces enforce MFA.

## What Velvet Elves treats as the administrative interface

The **platform console** (`/platform/*` in the SPA, `/api/v1/platform/*` on the API) is the cross-tenant operator surface (users, tenants, billing, registrations). It is gated by `require_platform_admin`:

1. `is_platform_admin` on the server profile (not a client flag).
2. JWT `aal` claim **aal2** (TOTP proved when this token was issued).
3. A **currently verified** TOTP factor (`has_verified_totp_factor`). A leftover aal2 JWT after unenroll is not enough.

`PLATFORM_ADMIN_MFA_REQUIRED` defaults **true**. The env escape hatch `false` is emergency-only and is not claimed as the production posture.

Login of an enrolled account returns `mfa_required=true`, an AAL1 access token, and **no refresh token** until `POST /users/mfa/verify`. The SPA `PlatformMfaGate` blocks `/platform/*` until a code is entered (or until Security enrollment is finished). Enrollment QR never runs on Tenants/Users pages.

**Tenant Admin** is a workspace role, not this interface. Ordinary users may enroll TOTP; they are not required to.

## Staging and production UI (already captured; not recaptured this session)

See `CASA_3_3_1_stage_mfa_prompt.png` / `CASA_3_3_1_prod_mfa_prompt.png` (login two-step).  
See `CASA_3_3_1_stage_platform_code.png` (console code gate).  
See `CASA_3_3_1_*_security_on.png` (Security: authenticator app is on).

## Staging API (31 Aug 2026)

See `CASA_3_3_1_deny.png`. Unsigned `GET /platform/users`, `GET /platform/registrations`, and `GET /users/mfa/factors` → **401**. `QA_PASSWORD` was unset, so a live aal1-vs-aal2 probe was not repeated; that path is covered by `test_platform_route_rejects_aal1_platform_admin`.

## Tests (names to cite)

`test_platform_route_rejects_aal1_platform_admin` — 403 `mfa_required`.  
`test_platform_route_allows_aal2_platform_admin` — 200.  
`test_platform_route_rejects_stale_aal2_after_unenroll` — 403 after factor removal.  
`test_login_returns_mfa_required_for_enrolled_account`.

## Do not attach (on disk, not for TAC)

- `*_security_enroll.png` — QR + setup key (TOTP secret in frame).
- `*_login.png` — generic password form; MFA evidence is the two-step prompt.
- `*_security_off.png`, `*_platform_unlocked.png`, `*_platform_setup.png`.

## Do not claim

- MFA default for **all** users, or for every tenant Admin.
- GCP / AWS console MFA (out of this check).
- That `PLATFORM_ADMIN_MFA_REQUIRED` cannot be turned off.
- HttpOnly session cookies.

## Portal comment

```
The application administrative interface is the platform console (/api/v1/platform/*). Those routes require is_platform_admin plus a JWT aal2 claim and a live verified TOTP factor (PLATFORM_ADMIN_MFA_REQUIRED defaults true). Login of an enrolled admin returns mfa_required until the authenticator code is verified. The SPA PlatformMfaGate blocks the console until a code is entered. Staging and production both show the two-step prompt and Security authenticator app is on. Unsigned GET /platform/users returns 401. Tenant Admin is a workspace role and is not this interface; MFA is not required for all users.
```
