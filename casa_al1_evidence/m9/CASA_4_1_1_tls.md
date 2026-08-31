# CASA 4.1.1 — TLS 1.2+ on production SPA and API

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 9.1.2  
**Date:** 31 Aug 2026  

ADA: the application shall enforce TLS for all connections and default to TLS 1.2+. AL1 named evidence is a **Qualys SSL Labs PDF export**, typically grade **B or higher**, reviewed against NIST SP.800-52r2.

## What was measured on Velvet Elves hosts (31 Aug 2026)

| Host | Default TLS | Forced TLS 1.2 | TLS 1.0 / 1.1 | HTTPS HSTS |
| --- | --- | --- | --- | --- |
| `app.velvetelves.com` | TLS 1.3 `TLS_AES_128_GCM_SHA256` | accepted `ECDHE-RSA-AES128-GCM-SHA256` | rejected (this client) | `max-age=31536000; includeSubDomains` |
| `api.prod.velvetelves.com` | TLS 1.3 `TLS_AES_128_GCM_SHA256` | accepted `ECDHE-RSA-AES128-GCM-SHA256` | rejected (this client) | `max-age=31536000; includeSubDomains` |

Certificates: issuer organization **Amazon** (public ACM). That supports 4.1.2; it is not a Qualys grade.

HTTP:

- `GET http://app.velvetelves.com/` → **301** `Location: https://app.velvetelves.com/`
- `GET http://api.prod.velvetelves.com/api/v1/health` → **200** JSON `{"status":"ok","env":"production",...}` from FastAPI. The ALB HTTP listener currently **forwards** to the app. Do **not** claim the API is HTTPS-only.

TLS 1.0/1.1 “rejected” is from this workstation’s TLS client (OpenSSL also deprecates those versions). Qualys SSL Labs is the ADA-named server-side protocol matrix.

## Architecture (not a live AWS console shot)

- SPA: CloudFront, `MinimumProtocolVersion` TLSv1.2_2021, managed SecurityHeadersPolicy HSTS.
- API: ALB + ECS, documented `ELBSecurityPolicy-TLS13-1-2-2021-06`. FastAPI `SecurityHeadersMiddleware` stamps HSTS (`app/core/security_headers.py`). Production live 22 Aug 2026.

The production deploy plan already says the ALB HTTP listener should redirect to HTTPS. Live 31 Aug 2026 it does not.

## Tests

`test_health_response_includes_security_headers` — HSTS on `/api/v1/health`.  
`test_security_headers_on_not_found` — nosniff / X-Frame-Options on 404.

## Owner captures (S5 / S6) — required for ADA AL1

Do **not** ask the agent to screenshot ssllabs.com. Drop PNGs in `tac_images/4.1.1/` (copy the same two into `tac_images/4.1.2/` for the next row):

1. https://www.ssllabs.com/ssltest/analyze.html?d=app.velvetelves.com  
2. https://www.ssllabs.com/ssltest/analyze.html?d=api.prod.velvetelves.com  
3. Wait until the scan **finishes**. Screenshot the summary: hostname, overall grade, protocol list (1.2 / 1.3). Portal accepts PNG/JPG only — if Qualys offers a PDF, screenshot the first page or convert.  
4. Filenames: `CASA_4_1_1_ssllabs_app.png`, `CASA_4_1_1_ssllabs_api.png`. No account keys in frame.

## Do not claim

- A Qualys letter grade without the owner screenshots.
- That the API is HTTPS-only while port 80 returns FastAPI JSON.
- Full NIST SP.800-52r2 cipher compliance from a single Python handshake.
- HttpOnly session cookies; MFA for all users.

## Portal comment

```
The production SPA (app.velvetelves.com) and API (api.prod.velvetelves.com) terminate TLS on CloudFront and an ALB. On 31 Aug 2026 a live handshake negotiated TLS 1.3 (TLS_AES_128_GCM_SHA256) on both hosts; TLS 1.2 was also accepted. HTTPS responses send Strict-Transport-Security: max-age=31536000; includeSubDomains. HTTP on the SPA returns 301 to HTTPS. HTTP on the API currently reaches FastAPI (GET /api/v1/health returned 200 JSON); that listener is not claimed as HTTPS-only. Certificates are Amazon ACM.
```
