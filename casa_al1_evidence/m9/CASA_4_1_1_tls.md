# CASA 4.1.1 — TLS 1.2+ on production SPA and API

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 9.1.2  
**Date:** 31 Aug 2026  

ADA: the application shall enforce TLS for all connections and default to TLS 1.2+. AL1 named evidence is a **Qualys SSL Labs PDF export**, typically grade **B or higher**, reviewed against NIST SP.800-52r2. Portal accepts PNG only; the finished SSL Labs HTML reports were captured as PNG.

## Qualys SSL Labs (31 Aug 2026)

| Host | Grade | Protocols |
| --- | --- | --- |
| `app.velvetelves.com` | **A+** on all tested CloudFront IPv4/IPv6 endpoints | TLS 1.3 Yes, TLS 1.2 Yes, TLS 1.1/1.0 No, SSL 3/2 No |
| `api.prod.velvetelves.com` | **A+** on both ALB IPv4 endpoints | TLS 1.3 Yes, TLS 1.2 Yes, TLS 1.1/1.0 No, SSL 3/2 No |

SPA ciphers are TLS 1.3 AES-GCM / ChaCha20 and TLS 1.2 ECDHE-RSA AES-GCM / ChaCha20. The API Qualys report also lists two TLS 1.2 CBC suites as **WEAK**; overall grade is still A+. Do not claim the API has no weak cipher suites.

## Live handshake on Velvet Elves hosts (31 Aug 2026)

| Host | Default TLS | Forced TLS 1.2 | HTTPS HSTS |
| --- | --- | --- | --- |
| `app.velvetelves.com` | TLS 1.3 `TLS_AES_128_GCM_SHA256` | accepted `ECDHE-RSA-AES128-GCM-SHA256` | `max-age=31536000; includeSubDomains` |
| `api.prod.velvetelves.com` | TLS 1.3 `TLS_AES_128_GCM_SHA256` | accepted `ECDHE-RSA-AES128-GCM-SHA256` | `max-age=31536000; includeSubDomains` |

Certificates: issuer organization **Amazon** (public ACM). That supports 4.1.2.

HTTP:

- `GET http://app.velvetelves.com/` → **301** `Location: https://app.velvetelves.com/`
- `GET http://api.prod.velvetelves.com/api/v1/health` → **200** JSON from FastAPI. The ALB HTTP listener currently **forwards** to the app. Do **not** claim the API is HTTPS-only.

## Architecture (not a live AWS console shot)

- SPA: CloudFront, `MinimumProtocolVersion` TLSv1.2_2021, managed SecurityHeadersPolicy HSTS.
- API: ALB + ECS, documented `ELBSecurityPolicy-TLS13-1-2-2021-06`. FastAPI `SecurityHeadersMiddleware` stamps HSTS (`app/core/security_headers.py`). Production live 22 Aug 2026.

The production deploy plan already says the ALB HTTP listener should redirect to HTTPS. Live 31 Aug 2026 it does not.

## Tests

`test_health_response_includes_security_headers` — HSTS on `/api/v1/health`.  
`test_security_headers_on_not_found` — nosniff / X-Frame-Options on 404.

## Do not claim

- That the API is HTTPS-only while port 80 returns FastAPI JSON.
- That the API has no Qualys-flagged weak ciphers (two TLS 1.2 CBC suites are WEAK; grade is still A+).
- HttpOnly session cookies; MFA for all users.

## Portal comment

```
The production SPA (app.velvetelves.com) and API (api.prod.velvetelves.com) terminate TLS on CloudFront and an ALB. Qualys SSL Labs on 31 Aug 2026 graded every tested endpoint A+ (TLS 1.3 and 1.2 enabled; TLS 1.1, TLS 1.0, SSL 3, and SSL 2 disabled). HTTPS responses send Strict-Transport-Security: max-age=31536000; includeSubDomains. HTTP on the SPA returns 301 to HTTPS. HTTP on the API currently reaches FastAPI (GET /api/v1/health returned 200 JSON); that listener is not claimed as HTTPS-only. Certificates are Amazon ACM.
```
