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
| 2.2.2 | **Verified 28 Aug 2026.** Not a dashboard toggle. Password change is reset/recovery (`POST /users/password-reset/confirm`). GoTrue `User.UpdatePassword` then `LogoutAllExceptMe` (recovery session) or `Logout` all sessions (admin password update, `sessionID` nil). Packed in `CASA_PORTAL_PACK.md`. Do not claim a live two-device reset. |
| 2.2.3 | **Verified 31 Aug 2026.** Staging access JWT `exp − iat` = **3600 s (1.00 hour)** after owner set VelvetElves Stage Sessions to 3600 s (was 28800 s earlier that day). Production Sessions also 3600 s. Packed in `CASA_PORTAL_PACK.md`. Do not treat inactivity/time-box 0 as this row. |
| 1.3.x | Supabase OTP/reset token expiry + single use. Screenshot the auth settings page. |
| 4.1.1/4.1.2 | **Packed 31 Aug 2026.** Qualys SSL Labs **A+** on both production hosts. 4.1.2 live peer certs are public Amazon ACM. ACM us-east-1: SPA cert covers `app.stage` + `app.velvetelves.com` through 13 Jan 2027. ACM us-east-2: API `api.prod.velvetelves.com` through 14 Jan 2027. API ALB HTTP:80 still serves FastAPI (`GET /api/v1/health` **200**) — that is a 4.1.1 note, not a cert-trust fail. |
| 6.4.1 | Quick Route 53 review: no dangling CNAMEs to dead services. Attest. |
| 1.1.1/3.1.5 | Staging register 429 screenshot (6 signups in a minute) + register password-rules UI. |

## Ready today (attest with existing evidence)

- **1.1.2, 1.1.3, 1.2.1, 1.3.1–1.3.4** — Supabase Auth issues hashed passwords, one-time expiring verifiers; no default credentials. (`self_attestation_draft.md`, M9d)
- **2.1.1** — Bearer header, no tokens in URLs (ZAP XML supports).
- **2.3.1** — **Verified 28 Aug 2026.** Honest N/A: requirement is cookie-based session tokens. Staging login Set-Cookie none; Bearer + localStorage. Official ZAP did not report plugin 10011. Packed in `CASA_PORTAL_PACK.md`. Do not claim a Secure session cookie.
- **2.3.2** — **Verified 28 Aug 2026.** Honest N/A: same architecture as 2.3.1. Staging login Set-Cookie none. Official ZAP did not report plugin 10010. Packed in `CASA_PORTAL_PACK.md`. Do not claim HttpOnly cookies or that localStorage equals HttpOnly.
- **2.3.3** — **Verified 28 Aug 2026.** User session is a GoTrue JWT minted after login (two staging `iat` values differed). Packed in `CASA_PORTAL_PACK.md`. Inbound CRM `X-API-Key` is a separate machine path, not the human session. Do not claim the product has no API keys anywhere.
- **2.3.4** — **Verified 28 Aug 2026.** Session JWT verified by `jose.jwt.decode` (staging ES256). Official ZAP lists did not report JWT signature-not-verified / none-algorithm. Packed in `CASA_PORTAL_PACK.md`. Do not claim ZAP ran Burp plugins 2099456/2099457.
- **2.4.1** — **Verified 28 Aug 2026.** Profile/email via `PATCH /users/me` + `get_current_user` (staging unsigned PATCH/GET 401; valid JWT GET 200). Password change is recovery email, not in-session current-password. MFA disable requires a current TOTP. Packed in `CASA_PORTAL_PACK.md`. Do **not** claim a password re-prompt on every save, or that email change is restricted.
- **3.1.1** — **Verified 31 Aug 2026.** Least privilege on FastAPI (`require_role` / `require_tenant_access` / `require_transaction_access`). Staging unsigned GET /users/ and GET /platform/users **401**. Packed in `CASA_PORTAL_PACK.md`. Do not claim RLS as the primary control.
- **3.1.2** — **Verified 31 Aug 2026.** Role/tenant/platform-admin/active loaded from the server profile. Register and OAuth ignore client `tenant_id`. PATCH /me has no policy fields. Packed in `CASA_PORTAL_PACK.md`. Do not claim register ignores role entirely (founder may pick a self-signup role on a new tenant).
- **3.1.3** — **Verified 31 Aug 2026.** Missing/invalid JWT → **401**; role/tenant miss → **403**; cron tick fail-closed without secret; unhandled exceptions generic **500**. Packed in `CASA_PORTAL_PACK.md`. Do not claim every deny is 403, or a live DB-exception probe.
- **3.1.4** — **Verified 31 Aug 2026.** ID-parameter APIs listed; IDOR process is load-then-`require_tenant_access` / `require_transaction_access`. Staging unsigned placeholder UUID GETs **401**. Packed in `CASA_PORTAL_PACK.md`. Do not claim a live authenticated two-tenant probe, or that every route uses `require_tenant_access` (contacts skip tenant deny for `role == Admin`).
- **3.1.5** — **Verified 31 Aug 2026.** Bearer session (no cookie CSRF); CORS does not echo `evil.example`; register 5/min. Official ZAP did not list 10202/20012. Packed in `CASA_PORTAL_PACK.md`. Do not claim a CSRF cookie or that Burp 2098944 ran.
- **3.1.6** — **Verified 31 Aug 2026.** SPA prefix GETs return the HTML shell (not `Index of /` / ListBucket). API directory-like paths JSON **404**. Production frontend S3 **Block all public access On**. Official ZAP did not list plugin 0. Packed in `CASA_PORTAL_PACK.md`. Do not claim missing `/assets/*` is 403 on staging.
- **3.2.1** — **Verified 31 Aug 2026.** Authorization code + PKCE S256 on sign-in, Gmail/Outlook/Calendar, and DocuSign. Staging Google start returned `s256`; flow not completed. Production GCP client is **Web application** with HTTPS callbacks (secret redacted). Packed in `CASA_PORTAL_PACK.md`. Do not claim implicit or Google ROPC.
- **3.2.2** — **Verified 31 Aug 2026.** Sign-in `redirect_to` origin-checked vs CORS; Fernet `state` 10 min TTL; integration `redirect_uri` server-set; postMessage not `*`. Staging foreign `redirect_to` **400**; garbage exchange state **400**. GCP lists production Gmail/Calendar/Supabase Auth redirects. Packed in `CASA_PORTAL_PACK.md`. Do not claim WSTG-ATHZ-05 or exact-path match on sign-in.
- **3.3.1** — **Verified 31 Aug 2026.** Platform console requires TOTP (`aal2` + live factor). Staging/prod two-step prompt and Security on. Unsigned platform GETs **401**. Packed in `CASA_PORTAL_PACK.md`. Do not claim MFA for all users. Do not attach enroll QR PNGs (TOTP secret in frame).
- **4.1.3** — **Verified 31 Aug 2026.** Fernet AES-128-CBC + HMAC-SHA256 for tokens/PII; bcrypt via GoTrue; SHA-256 / HMAC-SHA256 elsewhere. SHA-1 is a 16-hex intake proposal id (F052 Low). Packed in `CASA_PORTAL_PACK.md`. Do not claim AES-256 or a key-rotation drill.
- **4.1.4** — **Verified 31 Aug 2026.** Fernet HMAC/ciphertext flips both `InvalidToken`. Staging garbage JWT **401**; garbage OAuth state **400**. Packed in `CASA_PORTAL_PACK.md`. Do not claim WSTG-CRYP-02.
- **5.1.1** — **Verified 31 Aug 2026.** Official ZAP 20014 not in DAST_SUMMARY alert lists. Staging duplicate query last-wins (help search 422 vs 200). Packed in `CASA_PORTAL_PACK.md`. Do not claim Burp 5248000/5248001 or WSTG-INPV-04.
- **5.1.2** — **Verified 31 Aug 2026.** Official ZAP 20019 not in DAST_SUMMARY alert lists. Staging foreign OAuth `redirect_to` **400**; SPA `?next=` has no `Location` to the foreign host. Packed in `CASA_PORTAL_PACK.md`. Do not claim Burp 5243136–5243154 or WSTG-CLNT-04.
- **5.1.3–5.1.10** — Packed 31 Aug 2026 in `CASA_PORTAL_PACK.md`. Official ZAP + live probes. Auth SQLi/path-traversal Highs remain FP. 5.1.5 authenticated metadata webhook is 400. Burp not run.
- **5.2.1** — Packed. MIME allowlists; unsigned upload 401; authenticated probe.exe 415.
- **6.1.1** — Packed lockfile scans. npm 0. pip-audit ecdsa CVSS 7.4 no fix. Production ECR linux/amd64 child of prod-latest scanned 29 Aug 2026: 48 Critical, 174 High (OS/base layer). Image index itself is not scannable.
- **6.2.1** — Packed. Prod docs 404; staging docs 200.
- **6.3.1** — Packed. Foreign Origin /users/me 401.
- **6.4.1** — Packed live DNS. Route 53 console NOT captured.
- **6.5.1** — Packed code mask. CloudWatch login/payment log samples NOT captured (ADA-named gap).
- **6.6.1** — Packed. Staging Log Out: token keys gone; velvet_elves_return_location remains. DevTools Application panel not captured.
- **6.7.1** — Packed write-up. AWS Secrets Manager console NOT captured.

## Recommended sequence (updated 27 Aug — code work done)

1. ~~Land the logout revocation endpoint~~ **Done in code** (with login hardening, MFA, dependency bumps — all tests green locally).
2. **Owner deploys**: staging → verify (login/logout/MFA enroll/platform gate) → production. The agent never commits or pushes.
3. Take the **screenshot batch** (Supabase settings, SSL Labs, login/register 429, password UI, logout replay 401, fresh audits) — S7/S10/S12 need the deploy first.
4. Regenerate the 1.1.1 PNGs and render the new 2.2.1 / 3.3.1 pages from the updated write-ups.
5. Then fill all 48 rows from `TAC_ESOF_PORTAL_GUIDE.md` §7 and submit. Known Mediums stay as compensating controls — that is allowed; false claims are not.
