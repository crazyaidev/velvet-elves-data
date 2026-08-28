# Gap analysis — 48 CASA AL1 checks before upload

**Date:** 27 Aug 2026. Verified against ADA Web App Test Guide v1.0 and current code (backend `users.py` / `AuthContext.tsx` read today).
**Update (27 Aug, PM):** all four gaps below are **fixed in code** — backend suite 2069 passed, frontend suite 546 passed, `tsc`/`eslint` clean. They become true claims once the user deploys to staging → production (deploys are owner-run, never by the agent). Do not upload rows 1, 10, 26, 42 before the production deploy.
**Verdict:** 44 of 48 ready to attest once the deploy lands; the remaining screenshot batch is config verification only.

## Real gaps — all four FIXED IN CODE 27 Aug, pending deploy

| # | ID | Was | Fix that landed | Status |
| --- | --- | --- | --- | --- |
| 10 | 2.2.1 | Logout was client-side only; the Supabase **refresh token stayed valid** server-side. | `POST /api/v1/users/logout` revokes the Supabase session (`admin.sign_out`, scope local); `AuthContext.logout()` calls it (keepalive, best-effort) before `clearTokens()`. Test: `test_logout_revokes_supabase_session`. | **Fixed in code** — deploy, then replay-401 screenshot (S10). |
| 26 | 3.3.1 | Platform admin console had **no MFA** — the one likely hard fail. | Option A implemented: TOTP MFA via Supabase (`/users/mfa/enroll·verify·factors`), `require_platform_admin` demands the `aal2` JWT claim (`PLATFORM_ADMIN_MFA_REQUIRED=true` default), login returns `mfa_required` step-up, SPA has enrollment QR + code screens (`PlatformMfaGate`) and a login challenge step. Tests: `test_mfa_api.py` (13 tests). | **Fixed in code** — after deploy, platform admins must enroll TOTP. |
| 1 | 1.1.1 | `/users/login` had no app rate limiter and no breached-password check. | 10 req/min/IP limiter on login + **20 failed attempts/account/hour** soft lockout (`app/core/login_throttle.py`, meets ADA 2.1's ≤100/hour) + ~200-entry common-password denylist shared by register/invite/reset (`app/core/weak_passwords.py`, meets 2.4). Static list — do not call it HIBP. | **Fixed in code** — regenerate `CASA_1_1_1_page1/2.png` from the rewritten write-up after deploy. |
| 42 | 6.1.1 | pip-audit: `pydantic-ai-slim` (PYSEC-2026-2980), `PyPDF2` (PYSEC-2026-1835), `ecdsa` (no fix). | `pydantic-ai-slim` 1.22.0 → 1.107.5 (pulled openai 3.5.0 / anthropic 1.1.0 / pydantic 2.13.4; packet-parsing transport adapted to the SDKs' httpx2 core). `PyPDF2` → `pypdf` 6.16.2 everywhere. Dockerfile upgrades pip at build. Remaining findings: `ecdsa` (no fix exists — accepted-risk note) and `pytest` (dev-only, not shipped). | **Fixed in code** — rerun `pip-audit`/`npm audit` screenshots after deploy (S12). |

## Verify, then attest (no code, needs a look or a screenshot)

| ID | What to check |
| --- | --- |
| 2.2.2 | Does Supabase revoke other sessions on password change/reset? Check project auth settings; attest what is true. |
| 2.2.3 | Access-JWT expiry in Supabase dashboard (default 1 h, well under 24 h). Screenshot. |
| 1.3.x | Supabase OTP/reset token expiry + single use. Screenshot the auth settings page. |
| 4.1.1/4.1.2 | Run Qualys SSL Labs on `app.velvetelves.com` and `api.prod.velvetelves.com`; screenshot grades. The test guide names SSL Labs explicitly. |
| 6.4.1 | Quick Route 53 review: no dangling CNAMEs to dead services. Attest. |
| 1.1.1/3.1.5 | Staging register 429 screenshot (6 signups in a minute) + register password-rules UI. |

## Ready today (attest with existing evidence)

- **1.1.2, 1.1.3, 1.2.1, 1.3.1–1.3.4** — Supabase Auth issues hashed passwords, one-time expiring verifiers; no default credentials. (`self_attestation_draft.md`, M9d)
- **2.1.1** — Bearer header, no tokens in URLs (ZAP XML supports).
- **2.3.1 / 2.3.2** — Honest **N/A**: the requirement is conditional on *cookie-based* session tokens; we use header-borne JWT. Attach the localStorage compensating write-up; do not claim cookies.
- **2.3.3 / 2.3.4 / 2.4.1** — Session JWTs (signed), not static keys; sensitive changes need a valid session.
- **3.1.1–3.1.6** — Tenant isolation tests, server-side role/tenant from JWT, 401/403 fail-secure, IDOR covered by M9f + auth ZAP, CSRF N/A for Bearer APIs + register limiter, no directory listing (CloudFront OAC / no static API).
- **3.2.1 / 3.2.2** — PKCE code flow; `redirect_uri` fixed, `state` validated (test: "Invalid or expired OAuth state").
- **4.1.3 / 4.1.4** — Fernet for tokens/PII; SHA-1 is a non-security proposal id (Fluid Low, compensating); decrypt failures return generic errors.
- **5.1.1–5.1.10** — SAST 0 High/Critical/Medium + three ZAP XMLs; XSS callback fix verified; SQLi and path-traversal Highs written up as false positives with replays.
- **5.2.1** — Uploads to object storage, never executed.
- **6.2.1** — `APP_DEBUG=false`, prod docs/redoc/openapi 404 (smoke-tested).
- **6.3.1** — Origin never used for authz.
- **6.5.1** — Log masking (M9g), no tokens/bodies.
- **6.6.1** — **Verified today:** `LOGOUT` action calls `clearTokens()` removing both `velvet_elves_token` and `velvet_elves_refresh_token`; since the 27 Aug fix it also revokes the Supabase session server-side first.
- **6.7.1** — Secrets Manager + Fernet; state Disconnect soft-deactivate honestly.

## Recommended sequence (updated 27 Aug — code work done)

1. ~~Land the logout revocation endpoint~~ **Done in code** (with login hardening, MFA, dependency bumps — all tests green locally).
2. **Owner deploys**: staging → verify (login/logout/MFA enroll/platform gate) → production. The agent never commits or pushes.
3. Take the **screenshot batch** (Supabase settings, SSL Labs, login/register 429, password UI, logout replay 401, fresh audits) — S7/S10/S12 need the deploy first.
4. Regenerate the 1.1.1 PNGs and render the new 2.2.1 / 3.3.1 pages from the updated write-ups.
5. Then fill all 48 rows from `TAC_ESOF_PORTAL_GUIDE.md` §7 and submit. Known Mediums stay as compensating controls — that is allowed; false claims are not.
