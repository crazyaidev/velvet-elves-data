"""Append remaining CASA rows 5.1.3–6.7.1 into the portal pack and related guides."""
from pathlib import Path

PACK = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\CASA_PORTAL_PACK.md")
TAC = Path(r"c:\Projects\velvet-elves-data\CASA\TAC_ESOF_PORTAL_GUIDE.md")
REV = Path(r"c:\Projects\velvet-elves-data\CASA\CASA_48_CHECKS_REVISION_PLAN.md")
GAP = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\GAP_ANALYSIS_48_CHECKS.md")

SECTIONS = r'''
---

## 5.1.3 — Avoid eval / dynamic code execution

**ADA:** AL1 DAST. Burp 1051904 / 1052160 / 1052416 / 1052432 / 1051648 / 1052672 / 1052448 shall not be identified.

**Claimed:** Official ZAP 90019/20018 not in DAST_SUMMARY. No eval/exec on user input. Staging health extra query still 200.

**Missing:** Burp UI; ZAP UI; WSTG-INPV-11.

**Helpers:** `render_casa_rest.py`, `casa_rest_live.py`

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.3/CASA_5_1_3_eval_page1.png`](tac_images/5.1.3/CASA_5_1_3_eval_page1.png) | Write-up |
| [`tac_images/5.1.3/CASA_5_1_3_eval_page2.png`](tac_images/5.1.3/CASA_5_1_3_eval_page2.png) | AL1 mapping |
| [`tac_images/5.1.3/CASA_5_1_3_eval_code.png`](tac_images/5.1.3/CASA_5_1_3_eval_code.png) | No eval/exec |
| [`tac_images/5.1.3/CASA_5_1_3_eval_zap.png`](tac_images/5.1.3/CASA_5_1_3_eval_zap.png) | ZAP 90019 Pillow |
| [`tac_images/5.1.3/CASA_5_1_3_probe.png`](tac_images/5.1.3/CASA_5_1_3_probe.png) | Staging health extra query 200 |

### Portal comment

```
Official ADA ZAP scans of staging (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report server-side code injection (ZAP 90019 FAIL, 20018 FAIL). We did not run Burp 1051904, 1052432, or 1052448. The API does not call eval or exec on user input. The SPA source has no eval or new Function. Email templates substitute named {{token}} keys from a mapping. Staging GET /health with an import-looking query is still 200 JSON. WSTG-INPV-11 is AL2 and was not run.
```

---

## 5.1.4 — Template injection

**ADA:** AL1 DAST. Burp 1052800 shall not be identified.

**Claimed:** No Jinja of user templates; {{name}} mapping only. ZAP has no SSTI rule; 90025 WARN not in alerts.

**Missing:** Burp 1052800; WSTG-INPV-18; live SSTI probe PNG (code-only extra).

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.4/CASA_5_1_4_ssti_page1.png`](tac_images/5.1.4/CASA_5_1_4_ssti_page1.png) | Write-up |
| [`tac_images/5.1.4/CASA_5_1_4_ssti_page2.png`](tac_images/5.1.4/CASA_5_1_4_ssti_page2.png) | AL1 mapping |
| [`tac_images/5.1.4/CASA_5_1_4_ssti_code.png`](tac_images/5.1.4/CASA_5_1_4_ssti_code.png) | _substitute mapping.get |
| [`tac_images/5.1.4/CASA_5_1_4_ssti_zap.png`](tac_images/5.1.4/CASA_5_1_4_ssti_zap.png) | No SSTI plugin; 90025 WARN |

### Portal comment

```
Official ADA ZAP scans did not report template injection or expression-language injection. The ADA ZAP conf has no dedicated SSTI rule (90025 EL is WARN). APIs return JSON. Email and vendor copy replace named {{token}} keys from a mapping; unknown keys are empty. We do not render user Jinja. We did not run Burp 1052800. WSTG-INPV-18 is AL2 and was not run.
```

---

## 5.1.5 — SSRF

**ADA:** AL1 DAST. Burp 1051136 / 3146240 / 3146256 shall not be identified.

**Claimed:** No SSRF plugin in ADA ZAP conf; alerts did not list SSRF. assert_safe_url rejects loopback/metadata/private. Unsigned webhook POST 401.

**Missing:** Burp OOB plugins; WSTG-INPV-19; authenticated webhook create with a metadata URL.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf_page1.png`](tac_images/5.1.5/CASA_5_1_5_ssrf_page1.png) | Write-up |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf_page2.png`](tac_images/5.1.5/CASA_5_1_5_ssrf_page2.png) | AL1 mapping |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf_code.png`](tac_images/5.1.5/CASA_5_1_5_ssrf_code.png) | assert_safe_url |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf_zap.png`](tac_images/5.1.5/CASA_5_1_5_ssrf_zap.png) | No SSRF plugin |
| [`tac_images/5.1.5/CASA_5_1_5_ssrf.png`](tac_images/5.1.5/CASA_5_1_5_ssrf.png) | Local rejects + unsigned 401 |

### Portal comment

```
Official ADA ZAP scans did not report SSRF, OOB resource load, or external service interaction. The ADA ZAP conf has no dedicated SSRF plugin. Tenant webhook and ad click URLs pass assert_safe_url (http/https only; no localhost, metadata, or private addresses). Staging unsigned POST /integrations/webhooks with a metadata URL is 401. We did not run Burp 1051136, 3146240, or 3146256. WSTG-INPV-19 is AL2 and was not run.
```

---

## 5.1.6 — XML / XPath injection

**ADA:** AL1 DAST. Burp 1050368 / 1050112 / 1049600 / 2098016-18 shall not be identified.

**Claimed:** ZAP 90023/90021 not in alerts. No lxml/etree. XML login body rejected.

**Missing:** Burp XML plugins; WSTG-INPV-07/09.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.6/CASA_5_1_6_xml_page1.png`](tac_images/5.1.6/CASA_5_1_6_xml_page1.png) | Write-up |
| [`tac_images/5.1.6/CASA_5_1_6_xml_page2.png`](tac_images/5.1.6/CASA_5_1_6_xml_page2.png) | AL1 mapping |
| [`tac_images/5.1.6/CASA_5_1_6_xml_code.png`](tac_images/5.1.6/CASA_5_1_6_xml_code.png) | No XML parser |
| [`tac_images/5.1.6/CASA_5_1_6_xml_zap.png`](tac_images/5.1.6/CASA_5_1_6_xml_zap.png) | ZAP 90023/90021 |
| [`tac_images/5.1.6/CASA_5_1_6_xml.png`](tac_images/5.1.6/CASA_5_1_6_xml.png) | XML Content-Type on login rejected |

### Portal comment

```
Official ADA ZAP scans did not report XXE, XPath, or XML injection (ZAP 90023 FAIL, 90021 FAIL). Public APIs are JSON. The backend has no lxml, xml.etree, or xpath parser of user bodies. Staging POST /users/login with Content-Type application/xml is 400/415/422 and does not echo the XML. We did not run Burp 1050368, 1050112, or 1049600. WSTG-INPV-07 and INPV-09 are AL2 and were not run.
```

---

## 5.1.7 — XSS

**ADA:** AL1 DAST. Burp 2097408 / 2097920 / 2097936-38 shall not be identified.

**Claimed:** OAuth XSS closed on a9d78f05. Callback does not echo script tags. CSP Mediums compensating. Auth JSON XSS Low.

**Missing:** Burp XSS plugins; authenticated stored-XSS UI shot.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.7/CASA_5_1_7_xss_page1.png`](tac_images/5.1.7/CASA_5_1_7_xss_page1.png) | Write-up |
| [`tac_images/5.1.7/CASA_5_1_7_xss_page2.png`](tac_images/5.1.7/CASA_5_1_7_xss_page2.png) | AL1 mapping |
| [`tac_images/5.1.7/CASA_5_1_7_xss_code.png`](tac_images/5.1.7/CASA_5_1_7_xss_code.png) | html.escape callback |
| [`tac_images/5.1.7/CASA_5_1_7_xss_zap.png`](tac_images/5.1.7/CASA_5_1_7_xss_zap.png) | ZAP XSS plugins |
| [`tac_images/5.1.7/CASA_5_1_7_callback.png`](tac_images/5.1.7/CASA_5_1_7_callback.png) | Staging callback no script echo |

### Portal comment

```
Official unauth API ZAP a9d78f05 closed reflected XSS on OAuth callbacks (0 High). SPA 10f54abf was 0 High. Auth scan 33afa2aa reported persistent XSS in JSON at Low confidence; those responses are JSON, not HTML. CSP Mediums (img-src https:, style-src unsafe-inline) remain as compensating residuals. Staging GET gmail callback with a script in error does not put a script tag in the HTML. We did not run Burp XSS plugins 2097408 / 2097920 / 2097936.
```

---

## 5.1.8 — SQL injection

**ADA:** AL1 DAST. Burp 1049088 / 1049104 shall not be identified.

**Claimed:** Auth ZAP SQLi High/Low is FP; unsigned page_size='( is 401, no SQL text.

**Missing:** Burp SQLi; WSTG-INPV-05; authenticated replay of all 28 ZAP URLs.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.8/CASA_5_1_8_sqli_page1.png`](tac_images/5.1.8/CASA_5_1_8_sqli_page1.png) | Write-up |
| [`tac_images/5.1.8/CASA_5_1_8_sqli_page2.png`](tac_images/5.1.8/CASA_5_1_8_sqli_page2.png) | AL1 mapping |
| [`tac_images/5.1.8/CASA_5_1_8_sqli_code.png`](tac_images/5.1.8/CASA_5_1_8_sqli_code.png) | Parameterized access |
| [`tac_images/5.1.8/CASA_5_1_8_sqli_zap.png`](tac_images/5.1.8/CASA_5_1_8_sqli_zap.png) | Auth High FP note |
| [`tac_images/5.1.8/CASA_5_1_8_replay.png`](tac_images/5.1.8/CASA_5_1_8_replay.png) | Unsigned page_size quote is 401 |

### Portal comment

```
Official unauth ZAP scans did not confirm SQL injection. Auth ZAP 33afa2aa raised SQL Injection High with Low confidence (plugin 40018 WARN on the API conf). Evidence was HTTP 500 only, no SQL error text. Staging unsigned GET /teams?page_size='( is 401 Not authenticated, not a database error. Queries go through SQLAlchemy / PostgREST, not client SQL strings. We did not run Burp 1049088 or 1049104. WSTG-INPV-05 is AL2 and was not run.
```

---

## 5.1.9 — OS command injection

**ADA:** AL1 DAST. Burp 1048832 shall not be identified.

**Claimed:** No subprocess/os.system. ZAP 90020 not in alerts.

**Missing:** Burp 1048832; WSTG-INPV-12; live command-injection probe PNG (grep-only extra).

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.9/CASA_5_1_9_oscmd_page1.png`](tac_images/5.1.9/CASA_5_1_9_oscmd_page1.png) | Write-up |
| [`tac_images/5.1.9/CASA_5_1_9_oscmd_page2.png`](tac_images/5.1.9/CASA_5_1_9_oscmd_page2.png) | AL1 mapping |
| [`tac_images/5.1.9/CASA_5_1_9_oscmd_code.png`](tac_images/5.1.9/CASA_5_1_9_oscmd_code.png) | No subprocess |
| [`tac_images/5.1.9/CASA_5_1_9_oscmd_zap.png`](tac_images/5.1.9/CASA_5_1_9_oscmd_zap.png) | ZAP 90020 |

### Portal comment

```
Official ADA ZAP scans did not report OS command injection or Shell Shock (ZAP 90020 FAIL, 10048 FAIL). The backend has no subprocess, os.system, or shell=True. Fluid SAST 5999aab9 was 0 High/Critical/Medium. We did not run Burp 1048832. WSTG-INPV-12 is AL2 and was not run.
```

---

## 5.1.10 — File inclusion

**ADA:** AL1 DAST. Burp 1049344 / 1051392 shall not be identified.

**Claimed:** Auth path-traversal Highs are FP path segments. Ad click traversal is 404, not /etc/passwd.

**Missing:** Burp LFI plugins; authenticated replay of all four ZAP path-traversal URLs.

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.1.10/CASA_5_1_10_lfi_page1.png`](tac_images/5.1.10/CASA_5_1_10_lfi_page1.png) | Write-up |
| [`tac_images/5.1.10/CASA_5_1_10_lfi_page2.png`](tac_images/5.1.10/CASA_5_1_10_lfi_page2.png) | AL1 mapping |
| [`tac_images/5.1.10/CASA_5_1_10_lfi_code.png`](tac_images/5.1.10/CASA_5_1_10_lfi_code.png) | Object storage |
| [`tac_images/5.1.10/CASA_5_1_10_lfi_zap.png`](tac_images/5.1.10/CASA_5_1_10_lfi_zap.png) | Plugin 6 FP |
| [`tac_images/5.1.10/CASA_5_1_10_path.png`](tac_images/5.1.10/CASA_5_1_10_path.png) | Ad click traversal 404 |

### Portal comment

```
Official SPA ZAP did not report directory listing or file inclusion as High. Auth ZAP 33afa2aa raised Path Traversal High/Low four times with empty evidence; the payloads were URL path segments such as team, templates, settings. Staging GET /ads/../etc/passwd/click is 404 JSON, not a local file. Uploads go to object storage and are not executed. We did not run Burp 1049344 or 1051392.
```

---

## 5.2.1 — Malicious file uploads

**ADA:** AL1 written description plus source/screenshots of type checks and no execution.

**Claimed:** MIME allowlists; S3/Supabase storage; unsigned upload 401.

**Missing:** Authenticated upload of a disallowed type (415) UI; malware sample (not attempted).

### Images

| File | Description |
| --- | --- |
| [`tac_images/5.2.1/CASA_5_2_1_uploads_page1.png`](tac_images/5.2.1/CASA_5_2_1_uploads_page1.png) | Write-up |
| [`tac_images/5.2.1/CASA_5_2_1_uploads_page2.png`](tac_images/5.2.1/CASA_5_2_1_uploads_page2.png) | AL1 mapping |
| [`tac_images/5.2.1/CASA_5_2_1_uploads_code.png`](tac_images/5.2.1/CASA_5_2_1_uploads_code.png) | MIME allowlists |
| [`tac_images/5.2.1/CASA_5_2_1_deny.png`](tac_images/5.2.1/CASA_5_2_1_deny.png) | Unsigned POST /documents/upload 401 |

### Portal comment

```
Deal documents POST /documents/upload allow PDF, DOCX, DOC, JPEG, PNG, WEBP, GIF, and TXT, max 20 MB; other types are 415. Logos allow JPEG, PNG, WEBP, SVG, GIF, max 2 MB. Files go to Supabase Storage / S3 and are not executed as HTML, JavaScript, or Python. Staging unsigned POST /documents/upload is 401. We did not upload malware.
```

---

## 6.1.1 — No known exploitable components

**ADA:** AL1 dependency scan output. CVE CVSS >= 7.0 needs unused-code or no-patch justification.

**Claimed:** npm audit --omit=dev 0 vulns. pip-audit: only ecdsa 0.19.2 PYSEC-2026-1325 / CVE-2024-23342 CVSS 7.4; no upstream fix; JWT verify uses python-jose[cryptography], not ecdsa signing.

**Missing:** Production image layer scan; OWASP dependency-check; owner deploy proof that staging/prod match these lockfiles.

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.1.1/CASA_6_1_1_deps_page1.png`](tac_images/6.1.1/CASA_6_1_1_deps_page1.png) | Write-up |
| [`tac_images/6.1.1/CASA_6_1_1_deps_page2.png`](tac_images/6.1.1/CASA_6_1_1_deps_page2.png) | AL1 mapping |
| [`tac_images/6.1.1/CASA_6_1_1_deps_code.png`](tac_images/6.1.1/CASA_6_1_1_deps_code.png) | Pins |
| [`tac_images/6.1.1/CASA_6_1_1_pip.png`](tac_images/6.1.1/CASA_6_1_1_pip.png) | pip-audit ecdsa only |
| [`tac_images/6.1.1/CASA_6_1_1_npm.png`](tac_images/6.1.1/CASA_6_1_1_npm.png) | npm audit 0 vulns |

### Portal comment

```
Local pip-audit of backend requirements.txt on 31 Aug 2026 reported one finding: ecdsa 0.19.2 PYSEC-2026-1325 (CVE-2024-23342, CVSS 7.4). There is no upstream fix. Session JWTs are verified with python-jose[cryptography], not ecdsa.SigningKey.sign_digest (verification is out of scope for that CVE). npm audit --omit=dev on the SPA reported 0 vulnerabilities. This is a lockfile scan, not a screenshot of production image layers. pydantic-ai-slim 1.107.5 and pypdf 6.16.2 are pinned in requirements.txt.
```

---

## 6.2.1 — Debug off in production

**ADA:** AL1 DAST. Burp 1050624 ASP.NET debugging.

**Claimed:** Prod /api/docs /redoc /openapi.json 404. Staging docs 200. APP_DEBUG false in production.

**Missing:** Burp 1050624 (N/A ASP.NET); env var console screenshot.

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.2.1/CASA_6_2_1_debug_page1.png`](tac_images/6.2.1/CASA_6_2_1_debug_page1.png) | Write-up |
| [`tac_images/6.2.1/CASA_6_2_1_debug_page2.png`](tac_images/6.2.1/CASA_6_2_1_debug_page2.png) | AL1 mapping |
| [`tac_images/6.2.1/CASA_6_2_1_debug_code.png`](tac_images/6.2.1/CASA_6_2_1_debug_code.png) | docs off in prod |
| [`tac_images/6.2.1/CASA_6_2_1_debug_zap.png`](tac_images/6.2.1/CASA_6_2_1_debug_zap.png) | ZAP 10023 |
| [`tac_images/6.2.1/CASA_6_2_1_docs.png`](tac_images/6.2.1/CASA_6_2_1_docs.png) | Prod 404 / staging 200 |

### Portal comment

```
Production FastAPI hides OpenAPI UI: GET https://api.prod.velvetelves.com/api/docs, /api/redoc, and /api/openapi.json are 404. Staging still serves /api/docs (200). APP_DEBUG must be false when APP_ENV=production. Official ZAP listed generic JSON 500 application-error as Low, not a debug console. We did not run Burp 1050624 (ASP.NET debugging); this app is FastAPI.
```

---

## 6.3.1 — Origin not used for authz

**ADA:** AL1 DAST. Burp 2098689 arbitrary origin trusted.

**Claimed:** JWT authz. Foreign Origin GET /users/me is 401. CORS allowlist (3.1.5).

**Missing:** Burp 2098689.

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.3.1/CASA_6_3_1_origin_page1.png`](tac_images/6.3.1/CASA_6_3_1_origin_page1.png) | Write-up |
| [`tac_images/6.3.1/CASA_6_3_1_origin_page2.png`](tac_images/6.3.1/CASA_6_3_1_origin_page2.png) | AL1 mapping |
| [`tac_images/6.3.1/CASA_6_3_1_origin_code.png`](tac_images/6.3.1/CASA_6_3_1_origin_code.png) | JWT not Origin |
| [`tac_images/6.3.1/CASA_6_3_1_origin_zap.png`](tac_images/6.3.1/CASA_6_3_1_origin_zap.png) | ZAP 10098/20016 |
| [`tac_images/6.3.1/CASA_6_3_1_origin.png`](tac_images/6.3.1/CASA_6_3_1_origin.png) | Origin evil 401 |

### Portal comment

```
Access control is the JWT plus require_role / require_tenant_access. The Origin header is not used to grant a session. Staging GET /users/me with Origin https://evil.example and no Bearer is 401. CORS allowlists SPA origins (a foreign Origin does not receive Access-Control-Allow-Origin). Official ZAP 10098/20016 are WARN. We did not run Burp 2098689.
```

---

## 6.4.1 — Subdomain takeover

**ADA:** AL1 DNS evidence that names point at resources you control.

**Claimed:** Live DNS for app/api/help/apex to CloudFront or ALB IPs.

**Missing:** Route 53 hosted-zone console screenshot (AWS, owner). Full dangling-CNAME audit of unused names.

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.4.1/CASA_6_4_1_dns_page1.png`](tac_images/6.4.1/CASA_6_4_1_dns_page1.png) | Write-up |
| [`tac_images/6.4.1/CASA_6_4_1_dns_page2.png`](tac_images/6.4.1/CASA_6_4_1_dns_page2.png) | AL1 mapping |
| [`tac_images/6.4.1/CASA_6_4_1_dns_code.png`](tac_images/6.4.1/CASA_6_4_1_dns_code.png) | Name list |
| [`tac_images/6.4.1/CASA_6_4_1_dns.png`](tac_images/6.4.1/CASA_6_4_1_dns.png) | Live A/AAAA answers |

### Portal comment

```
Live DNS on 31 Aug 2026: app.velvetelves.com and app.stage.velvetelves.com resolve to CloudFront addresses; api.prod.velvetelves.com and api.stage.velvetelves.com resolve to ALB addresses; help.velvetelves.com and velvetelves.com resolve. A Route 53 hosted-zone console screenshot was not taken. WSTG-CONF-10 is AL2 and was not run.
```

---

## 6.5.1 — Do not log credentials or payment details

**ADA:** Written description PLUS a login log sample PLUS a payment log sample.

**Claimed:** Code does not log passwords; emails masked; Stripe holds PAN. Staging CloudWatch login event logs user id + request_id only. Staging CloudWatch after Buy one deal: Stripe SDK POST /v1/checkout/sessions and response 200; no PAN/CVV/secret.

**Missing:** Webhook dispatcher line (`Dispatching Stripe event type= id=evt_`) was not in this 15-minute Stripe filter. Not required once a payment-process sample exists.

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.5.1/CASA_6_5_1_logs_page1.png`](tac_images/6.5.1/CASA_6_5_1_logs_page1.png) | Write-up |
| [`tac_images/6.5.1/CASA_6_5_1_logs_page2.png`](tac_images/6.5.1/CASA_6_5_1_logs_page2.png) | AL1 mapping |
| [`tac_images/6.5.1/CASA_6_5_1_logs_code.png`](tac_images/6.5.1/CASA_6_5_1_logs_code.png) | _mask_email; Login user id logger |
| [`tac_images/6.5.1/CASA_6_5_1_mask.png`](tac_images/6.5.1/CASA_6_5_1_mask.png) | Mask helper |
| [`tac_images/6.5.1/CASA_6_5_1_login_log.png`](tac_images/6.5.1/CASA_6_5_1_login_log.png) | Staging Insights: Login user id, no password |
| [`tac_images/6.5.1/CASA_6_5_1_payment_log.png`](tac_images/6.5.1/CASA_6_5_1_payment_log.png) | Staging Insights: Stripe checkout/sessions 200 |
| [`tac_images/6.5.1/CASA_6_5_1_payment_request.png`](tac_images/6.5.1/CASA_6_5_1_payment_request.png) | Staging Insights: Stripe POST checkout/sessions |

### Portal comment

```
Login passwords are not written to the application logger. Gmail paths mask emails (local-part prefix plus ***). JSON logs include a request id, not the Authorization header. Card data is collected on Stripe Checkout; we store Stripe ids, not PAN or CVV. Staging CloudWatch log group /ecs/velvet-elves/stage/backend on 31 Aug 2026 recorded INFO Login user id=<uuid> with a request_id; the event has no password field and no Authorization header. The same log group after a staging Buy one deal checkout recorded stripe logger INFO POST https://api.stripe.com/v1/checkout/sessions and Stripe API response path=https://api.stripe.com/v1/checkout/sessions response_code=200. Those events have no PAN, CVV, or Stripe secret key.
```

---

## 6.6.1 — Clear browser storage on logout

**ADA:** AL1 written description of what remains in the browser after logout.

**Claimed:** clearTokens removes velvet_elves_token and velvet_elves_refresh_token; POST /users/logout revokes. Staging Chrome DevTools Application: token keys present then gone.

**Missing:** none for ADA AL1 written description. JWT values redacted on the before shot.

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.6.1/CASA_6_6_1_logout_page1.png`](tac_images/6.6.1/CASA_6_6_1_logout_page1.png) | Write-up |
| [`tac_images/6.6.1/CASA_6_6_1_logout_page2.png`](tac_images/6.6.1/CASA_6_6_1_logout_page2.png) | AL1 mapping |
| [`tac_images/6.6.1/CASA_6_6_1_logout_code.png`](tac_images/6.6.1/CASA_6_6_1_logout_code.png) | clearTokens |
| [`tac_images/6.6.1/CASA_6_6_1_after_logout.png`](tac_images/6.6.1/CASA_6_6_1_after_logout.png) | Staging /login after Log Out |
| [`tac_images/6.6.1/CASA_6_6_1_storage.png`](tac_images/6.6.1/CASA_6_6_1_storage.png) | Playwright key presence |
| [`tac_images/6.6.1/CASA_6_6_1_devtools_before.png`](tac_images/6.6.1/CASA_6_6_1_devtools_before.png) | Application localStorage signed-in; JWT values redacted |
| [`tac_images/6.6.1/CASA_6_6_1_devtools_after.png`](tac_images/6.6.1/CASA_6_6_1_devtools_after.png) | Application localStorage after Log Out; token keys gone |

### Portal comment

```
The SPA stores velvet_elves_token and velvet_elves_refresh_token in localStorage. Logout calls POST /users/logout (revokes the Supabase session) then clearTokens(), which removes both keys. Staging Chrome DevTools Application on 31 Aug 2026: those two keys are present while signed in (JWT values redacted in evidence) and gone after Log Out. Remaining keys include velvet_elves_return_location and a last_visit key. The browser is on /login. Google tokens are not in the browser.
```

---

## 6.7.1 — Server-side secrets

**ADA:** Written description plus source/screenshots of secrets management.

**Claimed:** Secrets Manager for ENCRYPTION_KEY; Fernet for Google tokens; production fail-closed; Disconnect soft-deactivate. Console: `/velvet-elves/prod/backend`, KMS `aws/secretsmanager`, Retrieve secret value not used, rotation Disabled.

**Missing:** CloudTrail secret-access log screenshot. No secret values attached (correct).

### Images

| File | Description |
| --- | --- |
| [`tac_images/6.7.1/CASA_6_7_1_secrets_page1.png`](tac_images/6.7.1/CASA_6_7_1_secrets_page1.png) | Write-up |
| [`tac_images/6.7.1/CASA_6_7_1_secrets_page2.png`](tac_images/6.7.1/CASA_6_7_1_secrets_page2.png) | AL1 mapping |
| [`tac_images/6.7.1/CASA_6_7_1_secrets_code.png`](tac_images/6.7.1/CASA_6_7_1_secrets_code.png) | No secret values |
| [`tac_images/6.7.1/CASA_6_7_1_sm.png`](tac_images/6.7.1/CASA_6_7_1_sm.png) | Secrets Manager overview; Retrieve not clicked |
| [`tac_images/6.7.1/CASA_6_7_1_sm_rotation.png`](tac_images/6.7.1/CASA_6_7_1_sm_rotation.png) | Rotation Disabled |

### Portal comment

```
API secrets including ENCRYPTION_KEY live in AWS Secrets Manager, not in git. Production fails to start if ENCRYPTION_KEY is missing. Google access and refresh tokens are Fernet-encrypted in the integrations table. Disconnect sets is_active false; ciphertext remains on the row (soft deactivate, not a wipe). The SPA does not hold those secrets. AWS Secrets Manager console on 31 Aug 2026 shows secret /velvet-elves/prod/backend in us-east-2, encryption key aws/secretsmanager. Retrieve secret value was not used. Rotation is Disabled. A CloudTrail GetSecretValue screenshot was not taken. No secret values are attached.
```
'''

def main():
    text = PACK.read_text(encoding="utf-8")
    old_rows = (
        "1.1.1, 1.1.2, 1.1.3, 1.2.1, 1.3.1, 1.3.2, 1.3.3, 1.3.4, 2.1.1, 2.2.1, 2.2.2, 2.2.3, "
        "2.3.1, 2.3.2, 2.3.3, 2.3.4, 2.4.1, 3.1.1, 3.1.2, 3.1.3, 3.1.4, 3.1.5, 3.1.6, 3.2.1, 3.2.2, "
        "3.3.1, 4.1.1, 4.1.2, 4.1.3, 4.1.4, 5.1.1, 5.1.2"
    )
    new_rows = old_rows + (
        ", 5.1.3, 5.1.4, 5.1.5, 5.1.6, 5.1.7, 5.1.8, 5.1.9, 5.1.10, 5.2.1, "
        "6.1.1, 6.2.1, 6.3.1, 6.4.1, 6.5.1, 6.6.1, 6.7.1"
    )
    text = text.replace(old_rows, new_rows, 1)
    index = """| 32 | 5.1.2 | Open redirect / allowlisted URLs | 6 | `CASA_5_1_2_redirect.md` |
| 33 | 5.1.3 | No eval / code injection | 5 | pack 5.1.3 |
| 34 | 5.1.4 | Template injection | 4 | pack 5.1.4 |
| 35 | 5.1.5 | SSRF | 5 | pack 5.1.5 |
| 36 | 5.1.6 | XML / XPath | 5 | pack 5.1.6 |
| 37 | 5.1.7 | XSS | 5 | pack 5.1.7 |
| 38 | 5.1.8 | SQLi | 5 | pack 5.1.8 |
| 39 | 5.1.9 | OS command injection | 4 | pack 5.1.9 |
| 40 | 5.1.10 | LFI / RFI | 5 | pack 5.1.10 |
| 41 | 5.2.1 | Malicious uploads | 4 | pack 5.2.1 |
| 42 | 6.1.1 | Dependency scan | 5 | pack 6.1.1 |
| 43 | 6.2.1 | Debug off in production | 5 | pack 6.2.1 |
| 44 | 6.3.1 | Origin not authz | 5 | pack 6.3.1 |
| 45 | 6.4.1 | Subdomain takeover | 4 | pack 6.4.1 |
| 46 | 6.5.1 | No credential logs | 7 | pack 6.5.1 |
| 47 | 6.6.1 | Logout clears storage | 7 | pack 6.6.1 |
| 48 | 6.7.1 | Server secrets | 5 | pack 6.7.1 — CloudTrail missing |

---"""
    text = text.replace(
        "| 32 | 5.1.2 | Open redirect / allowlisted URLs | 6 | `CASA_5_1_2_redirect.md` |\n\n---",
        index,
        1,
    )
    marker = "\n## Regeneration\n"
    if marker not in text:
        raise SystemExit("regeneration marker missing")
    text = text.replace(marker, SECTIONS + "\n## Regeneration\n", 1)
    regen = (
        "| 5.1.2 | `python render_casa_512_pages.py` then `python casa_512_deny.py`. "
        "Do **not** attach `/login`. Do **not** recapture ZAP UI or Google Cloud Console. Do **not** complete OAuth. |\n"
        "| 5.1.3–6.7.1 | `python render_casa_rest.py` then `python casa_rest_live.py`. "
        "Do **not** recapture ZAP, Burp, AWS, or CloudWatch. Do **not** print secrets. |\n"
    )
    text = text.replace(
        "| 5.1.2 | `python render_casa_512_pages.py` then `python casa_512_deny.py`. Do **not** attach `/login`. Do **not** recapture ZAP UI or Google Cloud Console. Do **not** complete OAuth. |\n",
        regen,
        1,
    )
    PACK.write_text(text, encoding="utf-8")
    print("updated pack")

    tac = TAC.read_text(encoding="utf-8")
    for old, new in [
        (
            "| 33 | 5.1.3 no eval | `SAST_SUMMARY.md` | No user driven eval SAST CSV 0 High |",
            "| 33 | 5.1.3 no eval | `tac_images/5.1.3/` | Official ZAP did not report code injection. No eval/exec on user input. Staging health extra query 200. Burp not run. |",
        ),
        (
            "| 34 | 5.1.4 template injection | `SAST_SUMMARY.md` | Server templates are not user controlled SAST CSV 0 High |",
            "| 34 | 5.1.4 template injection | `tac_images/5.1.4/` | JSON APIs; named {{token}} mapping not Jinja. ZAP no SSTI plugin. Burp 1052800 not run. |",
        ),
        (
            "| 35 | 5.1.5 SSRF | `DAST_SUMMARY.md` | No user controlled server fetch of arbitrary URLs ZAP XML attached in scan zip |",
            "| 35 | 5.1.5 SSRF | `tac_images/5.1.5/` | assert_safe_url blocks metadata/private. Unsigned webhook 401. No ZAP SSRF plugin. Burp OOB not run. |",
        ),
        (
            "| 36 | 5.1.6 XML injection | `DAST_SUMMARY.md` | JSON APIs not XML parsers for user input |",
            "| 36 | 5.1.6 XML injection | `tac_images/5.1.6/` | No lxml/xpath. XML login body rejected. ZAP 90023/90021 not in alerts. |",
        ),
        (
            "| 37 | 5.1.7 XSS | `compensating_controls.md` | OAuth XSS closed on rescan CSP Mediums are compensating residuals |",
            "| 37 | 5.1.7 XSS | `tac_images/5.1.7/` | OAuth XSS closed on a9d78f05. Callback does not echo script. CSP Mediums compensating. Auth JSON XSS Low. |",
        ),
        (
            "| 38 | 5.1.8 SQLi | `DAST_SUMMARY.md` | SQLAlchemy parameterized Auth ZAP SQLi High is false positive replay 422 or generic 500 |",
            "| 38 | 5.1.8 SQLi | `tac_images/5.1.8/` | Auth ZAP SQLi High is Low-confidence FP. Unsigned page_size quote is 401 not SQL. |",
        ),
        (
            "| 39 | 5.1.9 OS command injection | `SAST_SUMMARY.md` | No shelling user input SAST CSV 0 High |",
            "| 39 | 5.1.9 OS command injection | `tac_images/5.1.9/` | No subprocess/os.system. ZAP 90020 not in alerts. Burp 1048832 not run. |",
        ),
        (
            "| 40 | 5.1.10 file inclusion | `DAST_SUMMARY.md` | Auth ZAP path traversal High is false positive path segment only |",
            "| 40 | 5.1.10 file inclusion | `tac_images/5.1.10/` | Auth path-traversal Highs are FP path segments. Ad click traversal 404. |",
        ),
        (
            "| 41 | 5.2.1 malicious uploads | `self_attestation_draft.md` | Uploads go to object storage not executed as code |",
            "| 41 | 5.2.1 malicious uploads | `tac_images/5.2.1/` | MIME allowlists. Object storage. Unsigned POST /documents/upload 401. |",
        ),
        (
            "| 42 | 6.1.1 no known exploitable components | `DEPS_SUMMARY.md` (refresh) + S12 | npm production 0 pip audit clean after upgrades pydantic ai and pypdf upgraded 27 Aug Remaining notes ecdsa has no released fix and pytest is dev only not shipped |",
            "| 42 | 6.1.1 no known exploitable components | `tac_images/6.1.1/` | npm audit --omit=dev 0. pip-audit: ecdsa 0.19.2 PYSEC-2026-1325 CVSS 7.4 no fix; JWT verify uses jose/cryptography. Not a production image scan. |",
        ),
        (
            "| 43 | 6.2.1 debug off in production | `M9a_architecture.md` | Production APP DEBUG false docs redoc openapi are 404 |",
            "| 43 | 6.2.1 debug off in production | `tac_images/6.2.1/` | Prod /api/docs /redoc /openapi.json 404. Staging docs 200. |",
        ),
        (
            "| 44 | 6.3.1 Origin not used as auth | `M9f_tenant_isolation.md` | Auth is JWT not Origin header |",
            "| 44 | 6.3.1 Origin not used as auth | `tac_images/6.3.1/` | GET /users/me with foreign Origin is 401. JWT authz. |",
        ),
        (
            "| 45 | 6.4.1 subdomain takeover | `M9a_architecture.md` | Live hosts are CloudFront and ALB No dangling review CNAMEs in use |",
            "| 45 | 6.4.1 subdomain takeover | `tac_images/6.4.1/` | Live DNS to CloudFront/ALB. Route 53 console not captured. |",
        ),
        (
            "| 46 | 6.5.1 do not log credentials | `M9g_logging.md` | Logs mask emails No tokens or mail bodies |",
            "| 46 | 6.5.1 do not log credentials | `tac_images/6.5.1/` — `CASA_6_5_1_logs_page1.png`, `logs_page2.png`, `logs_code.png`, `mask.png`, `login_log.png`, `payment_log.png`, `payment_request.png` | Login passwords are not written to the application logger. Gmail paths mask emails (local-part prefix plus ***). JSON logs include a request id, not the Authorization header. Card data is collected on Stripe Checkout; we store Stripe ids, not PAN or CVV. Staging CloudWatch log group /ecs/velvet-elves/stage/backend on 31 Aug 2026 recorded INFO Login user id=<uuid> with a request_id; the event has no password field and no Authorization header. The same log group after a staging Buy one deal checkout recorded stripe logger INFO POST https://api.stripe.com/v1/checkout/sessions and Stripe API response path=https://api.stripe.com/v1/checkout/sessions response_code=200. Those events have no PAN, CVV, or Stripe secret key. |",
        ),
        (
            "| 47 | 6.6.1 clear browser storage on logout | `compensating_controls.md` | Logout clears velvet elves token keys in localStorage |",
            "| 47 | 6.6.1 clear browser storage on logout | `tac_images/6.6.1/` — `CASA_6_6_1_logout_page1.png`, `logout_page2.png`, `logout_code.png`, `after_logout.png`, `storage.png`, `devtools_before.png`, `devtools_after.png` | The SPA stores velvet_elves_token and velvet_elves_refresh_token in localStorage. Logout calls POST /users/logout (revokes the Supabase session) then clearTokens(), which removes both keys. Staging Chrome DevTools Application on 31 Aug 2026: those two keys are present while signed in (JWT values redacted in evidence) and gone after Log Out. Remaining keys include velvet_elves_return_location and a last_visit key. The browser is on /login. Google tokens are not in the browser. |",
        ),
        (
            "| 48 | 6.7.1 server secrets | `M9d_token_storage.md` | Secrets in AWS Secrets Manager Google tokens Fernet encrypted Disconnect is soft deactivate |",
            "| 48 | 6.7.1 server secrets | `tac_images/6.7.1/` — `CASA_6_7_1_secrets_page1.png`, `secrets_page2.png`, `secrets_code.png`, `sm.png`, `sm_rotation.png` | API secrets including ENCRYPTION_KEY live in AWS Secrets Manager, not in git. Production fails to start if ENCRYPTION_KEY is missing. Google access and refresh tokens are Fernet-encrypted in the integrations table. Disconnect sets is_active false; ciphertext remains on the row (soft deactivate, not a wipe). The SPA does not hold those secrets. AWS Secrets Manager console on 31 Aug 2026 shows secret /velvet-elves/prod/backend in us-east-2, encryption key aws/secretsmanager. Retrieve secret value was not used. Rotation is Disabled. A CloudTrail GetSecretValue screenshot was not taken. No secret values are attached. |",
        ),
    ]:
        if old not in tac:
            print("TAC miss:", old[:60])
        else:
            tac = tac.replace(old, new, 1)
    TAC.write_text(tac, encoding="utf-8")
    print("updated TAC")

    rev = REV.read_text(encoding="utf-8")
    replacements = {
        "| 33 | 5.1.3 | Ready | sast | [ ] |": "| 33 | 5.1.3 | Packed 31 Aug (ZAP 90019 not in alerts; no eval) | CASA_5_1_3 | [ ] |",
        "| 34 | 5.1.4 | Ready | sast | [ ] |": "| 34 | 5.1.4 | Packed 31 Aug (no Jinja; ZAP no SSTI plugin) | CASA_5_1_4 | [ ] |",
        "| 35 | 5.1.5 | Ready | dast + attest | [ ] |": "| 35 | 5.1.5 | Packed 31 Aug (assert_safe_url; unsigned webhook 401) | CASA_5_1_5 | [ ] |",
        "| 36 | 5.1.6 | Ready | dast | [ ] |": "| 36 | 5.1.6 | Packed 31 Aug (no XML parser; XML login rejected) | CASA_5_1_6 | [ ] |",
        "| 37 | 5.1.7 | Ready (comp CSP) | comp + dast | [ ] |": "| 37 | 5.1.7 | Packed 31 Aug (XSS closed a9d78f05; CSP Mediums residual) | CASA_5_1_7 | [ ] |",
        "| 38 | 5.1.8 | Ready (FP note) | dast | [ ] |": "| 38 | 5.1.8 | Packed 31 Aug (auth SQLi High FP; unsigned 401) | CASA_5_1_8 | [ ] |",
        "| 39 | 5.1.9 | Ready | sast | [ ] |": "| 39 | 5.1.9 | Packed 31 Aug (no subprocess; ZAP 90020 not in alerts) | CASA_5_1_9 | [ ] |",
        "| 40 | 5.1.10 | Ready (FP note) | dast | [ ] |": "| 40 | 5.1.10 | Packed 31 Aug (path-traversal High FP; ad click 404) | CASA_5_1_10 | [ ] |",
        "| 41 | 5.2.1 | Ready | attest | [ ] |": "| 41 | 5.2.1 | Packed 31 Aug (MIME allowlist; unsigned upload 401) | CASA_5_2_1 | [ ] |",
        "| 42 | 6.1.1 | Code landed → deploy + S12 | deps (refreshed) + S12 | [ ] |": "| 42 | 6.1.1 | Packed 31 Aug (npm 0; pip ecdsa 7.4 no fix). Production image not scanned | CASA_6_1_1 | [ ] |",
        "| 43 | 6.2.1 | Ready | M9a + S11 | [ ] |": "| 43 | 6.2.1 | Packed 31 Aug (prod docs 404; staging docs 200) | CASA_6_2_1 | [ ] |",
        "| 44 | 6.3.1 | Ready | M9f | [ ] |": "| 44 | 6.3.1 | Packed 31 Aug (foreign Origin /users/me 401) | CASA_6_3_1 | [ ] |",
        "| 45 | 6.4.1 | Verify S9 | M9a + S9 | [ ] |": "| 45 | 6.4.1 | Packed 31 Aug (live DNS). Route 53 console NOT captured | CASA_6_4_1 | [ ] |",
        "| 46 | 6.5.1 | Ready | M9g | [ ] |": "| 46 | 6.5.1 | Packed 31 Aug (code mask + staging CloudWatch login + Stripe checkout/sessions 200) | CASA_6_5_1 | [ ] |",
        "| 47 | 6.6.1 | Ready (verified 27 Aug) | comp | [ ] |": "| 47 | 6.6.1 | Packed 31 Aug (DevTools Application before/after Log Out; JWT values redacted) | CASA_6_6_1 | [ ] |",
        "| 48 | 6.7.1 | Ready | M9d | [ ] |": "| 48 | 6.7.1 | Packed 31 Aug (Secrets Manager console /velvet-elves/prod/backend, rotation Disabled). CloudTrail NOT captured | CASA_6_7_1 | [ ] |",
    }
    for old, new in replacements.items():
        if old not in rev:
            print("REV miss:", old[:70])
        else:
            rev = rev.replace(old, new, 1)
    REV.write_text(rev, encoding="utf-8")
    print("updated revision")

    gap = GAP.read_text(encoding="utf-8")
    old = "- **5.1.3–5.1.10** — SAST 0 High/Critical/Medium + three ZAP XMLs; XSS callback fix verified; SQLi and path-traversal Highs written up as false positives with replays.\n- **5.2.1** — Uploads to object storage, never executed.\n- **6.2.1** — `APP_DEBUG=false`, prod docs/redoc/openapi 404 (smoke-tested).\n- **6.3.1** — Origin never used for authz.\n- **6.5.1** — Log masking (M9g), no tokens/bodies.\n- **6.6.1** — **Verified today:** `LOGOUT` action calls `clearTokens()` removing both `velvet_elves_token` and `velvet_elves_refresh_token`; since the 27 Aug fix it also revokes the Supabase session server-side first.\n- **6.7.1** — Secrets Manager + Fernet; state Disconnect soft-deactivate honestly."
    new = """- **5.1.3–5.1.10** — Packed 31 Aug 2026 in `CASA_PORTAL_PACK.md`. Official ZAP + live probes. Auth SQLi/path-traversal Highs remain FP. Burp not run.
- **5.2.1** — Packed. MIME allowlists; unsigned upload 401.
- **6.1.1** — Packed lockfile scans. npm 0. pip-audit ecdsa CVSS 7.4 no fix. Production image not scanned.
- **6.2.1** — Packed. Prod docs 404; staging docs 200.
- **6.3.1** — Packed. Foreign Origin /users/me 401.
- **6.4.1** — Packed live DNS. Route 53 console NOT captured.
- **6.5.1** — Packed code mask + staging CloudWatch login (user id) + Stripe checkout-session POST/200 (no PAN).
- **6.6.1** — Packed. Staging DevTools Application: token keys present then gone; return_location remains. JWT values redacted.
- **6.7.1** — Packed write-up + Secrets Manager console `/velvet-elves/prod/backend` (no values; rotation Disabled). CloudTrail GetSecretValue NOT captured."""
    if old not in gap:
        print("GAP miss block")
    else:
        gap = gap.replace(old, new, 1)
        GAP.write_text(gap, encoding="utf-8")
        print("updated GAP")


if __name__ == "__main__":
    main()
