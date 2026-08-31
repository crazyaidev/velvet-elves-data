# CASA 3.1.5 — Anti-CSRF for authenticated APIs; anti-automation for unauthenticated

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 4.2.2  
**Date:** 31 Aug 2026  

ADA AL1 evidence is ADA DAST. Verification: the scan shall **not** identify Burp **2098944** (Cross-site request forgery). Official scans were ZAP with the ADA CASA conf (SPA plugin **10202** / **20012** = FAIL). We did not run Burp.

## Authenticated functionality

Session is **not a cookie**. Login returns JWTs in JSON; the SPA stores `velvet_elves_token` / `velvet_elves_refresh_token` in `localStorage` and sends `Authorization: Bearer`. Staging login `Set-Cookie` names: **none** (2.3.1). A cross-site form cannot attach that header.

CORS (`app/main.py`) allowlists exact origins (`CORS_ORIGINS`). A foreign `Origin` does not get `Access-Control-Allow-Origin`. Production allowlist (owner-verified 20 Aug 2026): `https://velvetelves.com`, `https://app.velvetelves.com`, `https://help.velvetelves.com`. We do **not** ship a synchronizer CSRF cookie.

## Unauthenticated functionality

ADA also wants anti-automation or anti-CSRF on unauthenticated actions. `POST /users/register` is JSON (preflight) and limited to **5 requests / 60 s / IP**. `POST /users/login` is **10 / 60 s / IP**. Tests: `test_registration_is_rate_limited`, `test_login_is_rate_limited_per_ip`.

## Official DAST

| Scan | Build |
| --- | --- |
| SPA | `10f54abf` |
| API | `a9d78f05` |
| Authenticated API | `33afa2aa` |

`DAST_SUMMARY.md` (21 Aug 2026) alert lists did **not** include Absence of Anti-CSRF Tokens (10202) or Anti CSRF Tokens Scanner (20012). Do not recapture ZAP UI. Do not claim Burp plugin 2098944 ran.

## Staging measurement (31 Aug 2026)

See `CASA_3_1_5_cors.png`. OPTIONS `/users/me` with `Origin: https://app.stage.velvetelves.com` returns **200** and that origin. The same OPTIONS with `Origin: https://evil.example` returns **400** and **no** `Access-Control-Allow-Origin`. Unsigned GET with the foreign origin is **401** and still has no ACAO for that origin.

Register 429 evidence is copied from the 1.1.1 staging capture (`CASA_3_1_5_register_429.png`). This session did not mint new staging users.

## Do not claim

- A synchronizer CSRF token or CSRF cookie.
- HttpOnly session cookies.
- That `allow_methods` / `allow_headers` are locked (they are `*`; origins are the control).
- That we ran Burp 2098944.
- CAPTCHA; MFA for all users.

## Portal comment

```
Authenticated APIs use Authorization Bearer, not a cookie session. Login returns JWTs in JSON and sets no Set-Cookie, so a cross-site form cannot send the session. CORS allowlists the SPA origin; a foreign Origin does not receive Access-Control-Allow-Origin. Unauthenticated register is limited to 5 requests per minute per IP. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Absence of Anti-CSRF Tokens. We do not ship a synchronizer CSRF cookie.
```
