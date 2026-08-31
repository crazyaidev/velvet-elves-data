# CASA 2.3.1 — Cookie-based session tokens shall have the Secure attribute

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 3.4.1  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

Testing results from a scan completed using ADA DAST guidance.

Verification: the scan shall **not** identify Burp **5243392** (TLS cookie without secure flag set). Official ZAP equivalent in `zap-casa-config.conf`: plugin **10011** Cookie Without Secure Flag = **FAIL**.

The requirement text is **cookie-based** session tokens.

## How Velvet Elves holds the session

| Piece | Mechanism |
| --- | --- |
| Issue | `POST /users/login` JSON body: `access_token`, `refresh_token` |
| Browser store | `localStorage` keys `velvet_elves_token`, `velvet_elves_refresh_token` |
| API auth | `Authorization: Bearer` (`OAuth2PasswordBearer`) |
| Cookie session | **None.** Login `Set-Cookie` names on staging 28 Aug 2026: **none** |

Transport is HTTPS. The API sends `Strict-Transport-Security`. That is not the same as a Secure session cookie, because there is no session cookie.

## Official DAST

| Scan | Build |
| --- | --- |
| SPA `https://app.stage.velvetelves.com` | `10f54abf` |
| API | `a9d78f05` |
| Authenticated API (Bearer, not a cookie) | `33afa2aa` |

`DAST_SUMMARY.md`: cookie HttpOnly / Secure flags were **not** raised. Session alerts were Informational only.

API CASA conf maps 10011 to **WARN** (not FAIL). SPA conf maps it to **FAIL**. Neither alert list included Cookie Without Secure Flag.

## Compensating (not a cookie claim)

HTTPS-only app and API, HSTS on the API, CSP `connect-src` locked to the env API, logout clears the localStorage keys, access JWT expires in 1 hour (2.2.3).

## Do not claim

- That the session JWT is a cookie with the Secure flag.
- HttpOnly session cookies (2.3.2).
- That localStorage is equivalent to HttpOnly.

## Portal comment

```
Session tokens are not cookies. Login returns a JWT in the JSON body and the app stores it in localStorage, then sends Authorization Bearer. Staging POST /users/login sets no Set-Cookie and is HTTPS with HSTS. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Cookie Without Secure Flag. There is no session cookie for the Secure attribute to apply to.
```
