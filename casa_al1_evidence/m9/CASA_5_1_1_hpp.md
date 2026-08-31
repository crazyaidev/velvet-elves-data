# CASA 5.1.1 — Protect against HTTP parameter pollution

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 5.1.1  
**Date:** 31 Aug 2026  

ADA AL1 evidence is ADA DAST. Verification: the scan shall **not** identify Burp **5248000** (client-side HTTP parameter pollution, reflected) or **5248001** (stored). Official scans were ZAP with the ADA CASA conf (SPA plugin **20014** = FAIL; API **20014** = WARN). We did not run Burp. WSTG-INPV-04 is AL2.

## Official DAST

| Scan | Build |
| --- | --- |
| SPA | `10f54abf` |
| API | `a9d78f05` |
| Authenticated API | `33afa2aa` |

`DAST_SUMMARY.md` (21 Aug 2026) alert lists did **not** include HTTP Parameter Pollution. SPA: 0 High. API and auth scans exited 0. Traditional SPA spider hit `/`, `/robots.txt`, `/sitemap.xml` only. Do not recapture ZAP UI.

## Typed parameters

FastAPI binds query and path values as typed scalars (`Query(int)`, constrained `str`, enums). The backend does not call `request.query_params.getlist`. Starlette `MultiDict.get()` returns one value; duplicate keys are not concatenated. Session is `Authorization: Bearer`, not a query key.

The SPA reads filters with `URLSearchParams.get` (a single value). Those keys are UI filters, not authorization.

## Staging measurement (31 Aug 2026)

See `CASA_5_1_1_hpp.png`.

| Request | Result |
| --- | --- |
| `GET /api/v1/health?x=1&x=2` | **200** `{"status":"ok",...}` |
| `GET /api/v1/public/help/search?q=ok&q=<161 chars>` | **422** `string_too_long` on `q` (last value) |
| `GET /api/v1/public/help/search?q=<161 chars>&q=ok` | **200** JSON array (last value accepted; concatenation would still be >160 and 422) |
| `GET /api/v1/teams?page=1&page=2` unsigned | **401** `Not authenticated` |
| `GET /api/v1/public/pay/invoices/{id}?token=aaa&token=bbb` | **403** `Invalid or expired payment link.` |

## Do not claim

- That Burp 5248000 / 5248001 ran.
- A completed WSTG-INPV-04 lab procedure (AL2).
- That every query parameter is a scalar (`list[str] = Query(...)` exists on some authenticated filters and collects multiples by design).
- That the SPA traditional spider crawled authenticated app routes.
- HttpOnly session cookies; MFA for all users.

## Portal comment

```
Official ADA ZAP scans of staging (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report HTTP Parameter Pollution (ZAP plugin 20014; SPA conf FAIL, API conf WARN). We did not run Burp 5248000 or 5248001. FastAPI binds query and path parameters as typed scalars; the backend does not call getlist. Duplicate keys take one value and are not concatenated. Staging public help search: q=ok plus a 161-character q is 422 on the last value; a long q plus q=ok is 200. Unsigned GET /teams?page=1&page=2 is 401. Duplicate public payment tokens are 403. Session is Authorization Bearer, not a query parameter. WSTG-INPV-04 is AL2 and was not run.
```
