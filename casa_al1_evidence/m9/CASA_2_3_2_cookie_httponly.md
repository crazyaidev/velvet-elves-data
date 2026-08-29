# CASA 2.3.2 — Cookie-based session tokens shall have the HttpOnly attribute

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 3.4.2  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

Testing results from a scan completed using ADA DAST guidance.

Verification: the scan shall **not** identify Burp **500600** (Cookie without HttpOnly flag set). Official ZAP equivalent in `zap-casa-config.conf`: plugin **10010** Cookie No HttpOnly Flag = **FAIL**.

The requirement text is **cookie-based** session tokens.

## How Velvet Elves holds the session

| Piece | Mechanism |
| --- | --- |
| Issue | `POST /users/login` JSON body: `access_token`, `refresh_token` |
| Browser store | `localStorage` keys `velvet_elves_token`, `velvet_elves_refresh_token` |
| API auth | `Authorization: Bearer` (`OAuth2PasswordBearer`) |
| Cookie session | **None.** Login `Set-Cookie` names on staging 28 Aug 2026: **none** |

`localStorage` is readable by JavaScript. That is **not** HttpOnly. This row does not claim HttpOnly.

## Official DAST

| Scan | Build |
| --- | --- |
| SPA `https://app.stage.velvetelves.com` | `10f54abf` |
| API | `a9d78f05` |
| Authenticated API (Bearer, not a cookie) | `33afa2aa` |

`DAST_SUMMARY.md`: cookie HttpOnly / Secure flags were **not** raised. Session alerts were Informational only.

API CASA conf maps 10010 to **WARN** (not FAIL). SPA conf maps it to **FAIL**. Neither alert list included Cookie No HttpOnly Flag.

## Compensating (not an HttpOnly claim)

HTTPS-only app and API, CSP `connect-src` locked to the env API, OAuth callback XSS closed, logout clears the localStorage keys, access JWT expires in 8 hours (2.2.3). Cookie migration would be the follow-up if a lab requires HttpOnly session cookies.

## Do not claim

- HttpOnly session cookies.
- That localStorage is equivalent to HttpOnly.
- That the JWT is a cookie with the Secure flag (2.3.1).

## Portal comment

```
Session tokens are not cookies. Login returns a JWT in the JSON body and the app stores it in localStorage, then sends Authorization Bearer. Staging POST /users/login sets no Set-Cookie. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Cookie No HttpOnly Flag. There is no session cookie for the HttpOnly attribute to apply to.
```
