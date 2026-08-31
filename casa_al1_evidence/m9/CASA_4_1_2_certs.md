# CASA 4.1.2 — Trusted TLS certificates on production SPA and API

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 9.2.1  
**Date:** 31 Aug 2026  

ADA: connections to and from the server shall use trusted TLS certificates. Self-signed or internally generated certificates, if used, must pin specific CAs. AL1 named evidence is the same **Qualys SSL Labs PDF** as 4.1.1 (grade B or higher).

## Qualys SSL Labs (31 Aug 2026)

Copied from the 4.1.1 capture (same scans):

| Host | Grade | Chain (Qualys) |
| --- | --- | --- |
| `app.velvetelves.com` | **A+** all CloudFront endpoints | Amazon RSA 2048 M01, Amazon Root CA 1 |
| `api.prod.velvetelves.com` | **A+** both ALB endpoints | Amazon RSA 2048 M04, Amazon Root CA 1 |

## Live peer certificates (31 Aug 2026)

OS trust store (`ssl.create_default_context`) verified both hostnames.

| Host | Subject CN | SAN | Issuer | Valid |
| --- | --- | --- | --- | --- |
| `app.velvetelves.com` | `app.stage.velvetelves.com` | `app.stage.velvetelves.com`, `app.velvetelves.com` | Amazon / Amazon RSA 2048 M01 | 30 Jun 2026 – 13 Jan 2027 |
| `api.prod.velvetelves.com` | `api.prod.velvetelves.com` | `api.prod.velvetelves.com` | Amazon / Amazon RSA 2048 M04 | 1 Jul 2026 – 14 Jan 2027 |

The SPA certificate is one ACM cert covering staging and production SPA names. Production `app.velvetelves.com` is on the SAN. Neither leaf is self-signed. A handshake that expects `evil.example.invalid` does not complete a trusted session (TLS alert / verification failure).

Backend HTTPS clients do not set `verify=False` / `CERT_NONE`.

## ACM console (31 Aug 2026)

- **us-east-2** `api.prod.velvetelves.com`: **Amazon issued**, **Issued**, in use **Yes**, not after **14 January 2027**. See `CASA_4_1_2_acm.png`.
- **us-east-1** `app.stage.velvetelves.com` + `app.velvetelves.com` (one cert): **Amazon issued**, **Issued**, in use **Yes**, not after **13 January 2027**. See `CASA_4_1_2_acm_spa.png`.

DNS validation CNAME name and value are redacted on both. No private key (ACM does not show one). Row is at the 10-file portal cap.

## Do not claim

- A dedicated production-only SPA certificate (SAN also includes `app.stage.velvetelves.com`).
- SSL Labs grades of Supabase, Google, or other outbound hosts.
- An ACM console screenshot of a production-only SPA certificate (the us-east-1 cert also names staging).
- That the API is HTTPS-only on port 80 (see 4.1.1).
- HttpOnly session cookies; MFA for all users.

## Portal comment

```
Production TLS certificates are public Amazon ACM, not self-signed. Qualys SSL Labs on 31 Aug 2026 graded app.velvetelves.com and api.prod.velvetelves.com A+; the chain is Amazon RSA 2048 with Amazon Root CA 1. A live handshake with the OS trust store verified both hostnames. ACM in us-east-1 lists one Amazon-issued certificate covering app.stage.velvetelves.com and app.velvetelves.com, status Issued, in use, valid through 13 January 2027. ACM in us-east-2 lists the api.prod.velvetelves.com certificate as Amazon issued, Issued, in use, valid through 14 January 2027. Both leaves are currently valid. A hostname mismatch does not complete a trusted handshake.
```
