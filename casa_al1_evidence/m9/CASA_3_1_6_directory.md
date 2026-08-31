# CASA 3.1.6 — Directory browsing disabled

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 4.3.2  
**Date:** 31 Aug 2026  

ADA AL1 evidence is ADA DAST. Verification: the scan shall **not** identify Burp **6291712** (Directory Listing). Official scans were ZAP; SPA conf maps plugin **0** Directory Browsing to **FAIL**. We did not run Burp.

## How Velvet Elves is served

The SPA is hashed Vite assets on **CloudFront**, origin **S3 via Origin Access Control** (not a public website listing). Default root object is `index.html`. A CloudFront Function rewrites extensionless routes to `/index.html` so client routes work. The API is FastAPI on ECS. It does **not** mount `StaticFiles` and has no Apache/nginx autoindex.

## Staging measurement (31 Aug 2026)

See `CASA_3_1_6_nolist.png`.

| Request | Result |
| --- | --- |
| SPA `GET /assets/`, `/static/`, `/assets/missing-316.js` | **200** `text/html` SPA shell (`<!doctype html>`). Not `Index of /`. Not S3 `ListBucketResult`. |
| API `GET /`, `/api/v1/`, `/static/` | **404** JSON `{"status_code":404,"message":"Not Found"}` |

Do **not** claim missing hashed files return 403 on staging; they currently return the SPA HTML shell. That is still not a directory listing.

Staging still serves `/api/docs` (OpenAPI UI). That is a documented API page, not a filesystem index. Production `/api/docs` is 404 (6.2.1).

## Official DAST

| Scan | Build |
| --- | --- |
| SPA | `10f54abf` |
| API | `a9d78f05` |
| Authenticated API | `33afa2aa` |

`DAST_SUMMARY.md` (21 Aug 2026) alert lists did **not** include Directory Browsing (plugin 0). Do not recapture ZAP UI or the AWS console.

## Do not claim

- That missing `/assets/*` files return 403 on staging (they return the SPA shell).
- An AWS console / S3 listing screenshot (owner-captured if TAC asks).
- That Burp 6291712 ran.
- HttpOnly cookies; MFA for all users.

## Portal comment

```
Directory browsing is disabled. The SPA is hashed CloudFront assets (S3 origin via OAC), not an Apache or nginx autoindex. Staging GET /assets/, /static/, and a missing hashed JS file return the SPA HTML shell, not Index of / or an S3 ListBucketResult. The API does not mount static files; GET /, /api/v1/, and /static/ return JSON 404. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Directory Browsing. We did not run Burp 6291712.
```
