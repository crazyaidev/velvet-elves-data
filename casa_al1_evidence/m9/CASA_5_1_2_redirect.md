# CASA 5.1.2 — URL redirects limited to allowlisted URLs

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 5.1.5  
**Date:** 31 Aug 2026  

ADA AL1 evidence is ADA DAST. Verification: the scan shall **not** identify Burp **5243136**, **5243137**, **5243152**, **5243153**, or **5243154** (open redirection). Official scans were ZAP with the ADA CASA conf (SPA plugin **20019** External Redirect = FAIL; API **20019** = WARN). We did not run Burp. WSTG-CLNT-04 is AL2.

## Official DAST

| Scan | Build |
| --- | --- |
| SPA | `10f54abf` |
| API | `a9d78f05` |
| Authenticated API | `33afa2aa` |

`DAST_SUMMARY.md` (21 Aug 2026) alert lists did **not** include External Redirect or open redirection. SPA: 0 High. API and auth scans exited 0. Traditional SPA spider hit `/`, `/robots.txt`, `/sitemap.xml` only. Do not recapture ZAP UI.

## Allowlists

- OAuth sign-in `redirect_to`: `validate_redirect_to` vs `CORS_ORIGINS`. Foreign origin → **400** `redirect_to is not an allowed origin.` Origin allowlist, not a single exact path.
- Password reset: disallowed `redirect_to` is **ignored** (not 400). Email uses `FRONTEND_URL/reset-password` or an allowlisted `Origin`.
- Integration OAuth `redirect_uri` is server-set. Callback `postMessage` targets `FRONTEND_URL`, not `*`.
- Ad click `GET /ads/{hook_id}/click` 302s to a **stored** `click_url` (SSRF-safe http/https). No `url=` query param. Unknown hook → **404**, no `Location`.
- SPA post-login restore: paths must start with `/`.

## Staging measurement (31 Aug 2026)

See `CASA_5_1_2_deny.png`. Redirects were **not followed**.

| Request | Result |
| --- | --- |
| `POST /users/oauth/google/start` `redirect_to=https://evil.example/steal` | **400**, Location none |
| `POST /users/password-reset/request` same `redirect_to` | **202** generic message, Location none, body has no evil host |
| `GET /ads/{uuid}/click` unknown hook | **404** `Ad not found.`, Location none |
| SPA `GET /?next=https://evil.example/steal` | **200** HTML shell, Location none |

Consent was not completed. Do not attach `/login`. Do not recapture Google Cloud Console.

## Do not claim

- That Burp 5243136–5243154 ran.
- A completed WSTG-CLNT-04 procedure (AL2).
- That password-reset foreign `redirect_to` is 400 (it is ignored; 202).
- That ad `click_url` is limited to CORS origins (it is a stored public http(s) URL).
- That the SPA traditional spider crawled authenticated app routes.
- HttpOnly session cookies; MFA for all users.

## Portal comment

```
Official ADA ZAP scans of staging (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report External Redirect (ZAP plugin 20019; SPA conf FAIL, API conf WARN). We did not run Burp 5243136, 5243137, 5243152, 5243153, or 5243154. OAuth sign-in redirect_to must match a CORS origin; a foreign origin is 400. Password-reset redirect_to that is not allowlisted is ignored. Ad click 302 uses a stored click_url, not a query parameter; an unknown hook is 404. OAuth callback postMessage targets FRONTEND_URL, not *. SPA return URLs must start with /. Staging: POST /users/oauth/google/start with https://evil.example/steal is 400 with no Location; GET /ads/{uuid}/click is 404 with no Location; SPA GET ?next=https://evil.example is 200 with no Location to that host. WSTG-CLNT-04 is AL2 and was not run.
```
