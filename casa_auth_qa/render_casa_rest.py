"""Render write-up / code / zap PNGs for remaining CASA rows 5.1.3–6.7.1."""
from __future__ import annotations

from pathlib import Path

from casa_pack_lib import save_code, save_page1, save_page2

ROOT = Path(r"c:\Projects\velvet-elves-data\casa_al1_evidence\m9\tac_images")
DAST = (
    "Official ADA ZAP 21 Aug 2026: SPA 10f54abf, API a9d78f05, auth 33afa2aa, staging. "
    "SPA traditional spider hit /, /robots.txt, /sitemap.xml. We did not run Burp."
)


def out(cid: str) -> Path:
    p = ROOT / cid
    p.mkdir(parents=True, exist_ok=True)
    return p


def dast_row(cid, stem, title, burp, zap, extra_p1, extra_p2, attest, snippet, zap_snip):
    d = out(cid)
    save_page1(
        d,
        stem,
        title,
        [
            ("Source", f"ADA Web App Test Guide v1.0. AL1 evidence is ADA DAST. {burp} {DAST}"),
            ("Official ZAP mapping", zap),
            ("Product control", extra_p1),
            ("Honest limit", extra_p2),
        ],
    )
    save_page2(
        d,
        stem,
        f"{cid} AL1 verification mapping",
        [
            ("Official DAST", zap),
            ("Burp plugins", "Burp was not run. Closest analog is the ZAP rule named above."),
            ("SPA spider", "Authenticated SPA routes were not crawled."),
        ],
        attest,
    )
    save_code(d, stem, f"{cid} code", snippet)
    save_code(d, stem, f"{cid} Official ADA ZAP", zap_snip, suffix="zap")


def main():
    dast_row(
        "5.1.3",
        "CASA_5_1_3_eval",
        "5.1.3 Avoid eval and dynamic code execution",
        "Verification: scan shall not identify Burp 1051904, 1052160, 1052416, 1052432, 1051648, 1052672, 1052448. WSTG-INPV-11 is AL2.",
        "SPA plugin 90019 Server Side Code Injection FAIL; 20018 RCE FAIL; 90025 EL WARN. DAST_SUMMARY alert tables did not list code injection, Python injection, or EL injection.",
        "The API does not call eval, exec, or os.system on user input. Frontend src has no eval or new Function. Email tokens are {{name}} substitution of an allowlisted key, not eval.",
        "Fluid SAST 5999aab9: 0 High/Critical/Medium. AL2 WSTG-INPV-11 was not run.",
        "Velvet Elves does not execute user input with eval. Official ZAP did not report server-side code injection.",
        "# Backend app/ has no eval( or exec( on user input.\n# Frontend src/ has no eval( or new Function(.\n# Email templates: _TOKEN_PATTERN {{name}} -> mapping.get(key), not eval.",
        "# zap-casa-config.conf\n90019 FAIL (Server Side Code Injection)\n20018 FAIL (Remote Code Execution)\n90025 WARN (Expression Language Injection)\n\nDAST_SUMMARY.md: not in alert lists.\nBurp 1051904 / 1052432 / 1052448 not run.",
    )
    dast_row(
        "5.1.4",
        "CASA_5_1_4_ssti",
        "5.1.4 Protect against template injection",
        "Verification: scan shall not identify Burp 1052800. WSTG-INPV-18 is AL2.",
        "No dedicated SSTI plugin in the ADA ZAP conf. 90025 EL Injection is WARN. DAST_SUMMARY did not list template injection or EL injection.",
        "APIs return JSON. There is no Jinja/Mako render of user templates. Email and vendor copy use named {{token}} substitution from a mapping; unknown keys become empty.",
        "Do not claim a Jinja sandbox. WSTG-INPV-18 was not run.",
        "Velvet Elves does not render user-controlled server templates. Official ZAP did not report EL or template injection.",
        "# app/services/vendor_template_service.py\n_TOKEN_PATTERN = {{ name }}\ndef _substitute(template, mapping):\n    return mapping.get(key, '')  # not eval, not Jinja",
        "# ADA ZAP conf has no SSTI rule.\n90025 WARN (Expression Language Injection)\n\nDAST_SUMMARY.md: not in alert lists.\nBurp 1052800 not run.",
    )
    dast_row(
        "5.1.5",
        "CASA_5_1_5_ssrf",
        "5.1.5 Prevent server-side request forgery",
        "Verification: scan shall not identify Burp 1051136, 3146240, 3146256. WSTG-INPV-19 is AL2.",
        "ADA ZAP conf has no dedicated SSRF plugin. 10107 Httpoxy is FAIL on SPA. DAST_SUMMARY did not list SSRF, OOB resource load, or external service interaction.",
        "Tenant webhook and ad click URLs pass assert_safe_url: http(s) only, no localhost/metadata, no private/loopback after DNS. Unsigned webhook POSTs are 401. Authenticated POST with a metadata URL is 400 (URL isn't allowed).",
        "JWKS fetch uses a configured URL, not a client URL. WSTG-INPV-19 was not run.",
        "Velvet Elves does not fetch arbitrary URLs from user query parameters. Official ZAP did not report SSRF-class alerts.",
        "# app/utils/url_safety.py  assert_safe_url\n# scheme http/https only\n# blocks localhost, metadata.google.internal\n# rejects loopback / private / link-local after getaddrinfo\n# used by webhooks, accounting, ad click_url",
        "# No SSRF plugin in zap-casa-config.conf\n10107 FAIL (Httpoxy)\n\nDAST_SUMMARY.md: not SSRF / OOB.\nBurp 1051136 / 3146240 / 3146256 not run.",
    )
    dast_row(
        "5.1.6",
        "CASA_5_1_6_xml",
        "5.1.6 Protect against XPath and XML injection",
        "Verification: scan shall not identify Burp 1050368, 1050112, 1049600, 2098016-2098018. WSTG-INPV-07/09 are AL2.",
        "SPA 90023 XXE FAIL; 90021 XPath FAIL. DAST_SUMMARY did not list XXE, XPath, or XML injection.",
        "Public APIs are JSON. app/ has no lxml/etree/xpath parsers of user bodies. DocuSign traffic is via the vendor SDK, not a user XML parser.",
        "WSTG-INPV-07 and INPV-09 were not run.",
        "Velvet Elves does not parse user XML or XPath. Official ZAP did not report XXE or XPath injection.",
        "# grep of app/: no lxml, xml.etree, xpath, defusedxml.\n# FastAPI request bodies are JSON / multipart, not XML.",
        "# zap-casa-config.conf\n90023 FAIL (XML External Entity Attack)\n90021 FAIL (XPath Injection)\n\nDAST_SUMMARY.md: not in alert lists.\nBurp XML/XPath plugins not run.",
    )
    dast_row(
        "5.1.7",
        "CASA_5_1_7_xss",
        "5.1.7 Context-aware XSS protections",
        "Verification: scan shall not identify Burp 2097408, 2097920, 2097936-2097938.",
        "SPA 40012/40014/40026 FAIL. Unauth API a9d78f05 closed reflected XSS on OAuth callbacks. Auth scan: persistent XSS in JSON Low/Low confidence (40014). CSP Mediums remain (10055 WARN).",
        "Callback HTML escapes query error text and postMessages FRONTEND_URL only. JSON APIs are not HTML. SPA does not dangerouslySetInnerHTML user documents. One onboarding label uses first-party HTML entities, not user HTML.",
        "CSP img-src https: and style-src unsafe-inline are compensating residuals, not a claim of zero XSS findings.",
        "Reflected XSS on OAuth callbacks was closed on rescan a9d78f05. Remaining CSP Mediums are compensating. Auth JSON XSS Low is not HTML.",
        "# app/utils/oauth_popup.py  html.escape on callback text\n# postMessage target FRONTEND_URL, not *\n# Auth ZAP 40014 persistent XSS in JSON: Low confidence; Content-Type is not HTML.",
        "# zap-casa-config.conf\n40012 FAIL (XSS Reflected)\n40014 FAIL (XSS Persistent)\n40026 FAIL (XSS DOM)\n10055 WARN (CSP)\n\nSPA 0 High. API XSS Highs closed on a9d78f05.\nBurp XSS plugins not run.",
    )
    dast_row(
        "5.1.8",
        "CASA_5_1_8_sqli",
        "5.1.8 Protect against database injection",
        "Verification: scan shall not identify Burp 1049088 or 1049104. WSTG-INPV-05 is AL2.",
        "SPA 40018 SQLi FAIL. API conf maps 40018 to WARN. Auth scan 33afa2aa raised SQL Injection High/Low confidence (28). Replay: page_size='( is 422 Pydantic; other noise is generic JSON 500, no SQL error text.",
        "Queries go through SQLAlchemy / PostgREST filters, not string-concatenated SQL from the client.",
        "Do not claim the auth-scan Highs were confirmed SQLi. They are false positives / compensating. WSTG-INPV-05 was not run.",
        "Velvet Elves uses parameterized data access. Official unauth scans did not confirm SQLi. Auth ZAP SQLi Highs replayed as 422 or generic 500.",
        "# FastAPI Query(int) rejects page_size='(\n# SQLAlchemy / PostgREST; no client SQL strings.\n# Auth ZAP 40018 High (Low confidence): HTTP 500 only, no SQL text.",
        "# SPA 40018 FAIL  API 40018 WARN\nAuth 33afa2aa: SQL Injection High/Low x28\nReplay: 422 or generic 500. Not confirmed CWE-89.\nBurp 1049088 / 1049104 not run.",
    )
    dast_row(
        "5.1.9",
        "CASA_5_1_9_oscmd",
        "5.1.9 Protect against OS command injection",
        "Verification: scan shall not identify Burp 1048832. WSTG-INPV-12 is AL2.",
        "SPA 90020 Remote OS Command Injection FAIL; 10048 Shell Shock FAIL. DAST_SUMMARY did not list OS command injection or Shell Shock.",
        "app/ has no subprocess, os.system, or shell=True. Fluid SAST 0 High/Critical/Medium.",
        "WSTG-INPV-12 was not run.",
        "Velvet Elves does not shell user input. Official ZAP did not report OS command injection.",
        "# grep of app/: no subprocess, os.system, os.popen, shell=True.",
        "# zap-casa-config.conf\n90020 FAIL (Remote OS Command Injection)\n10048 FAIL (Shell Shock)\n\nDAST_SUMMARY.md: not in alert lists.\nBurp 1048832 not run.",
    )
    dast_row(
        "5.1.10",
        "CASA_5_1_10_lfi",
        "5.1.10 Protect against file inclusion",
        "Verification: scan shall not identify Burp 1049344 or 1051392.",
        "SPA plugin 6 Path Traversal WARN; 7 RFI WARN; 43 File Inclusion WARN. Auth scan raised Path Traversal High/Low x4 with empty evidence; attacks were URL path segments (team, templates, settings). Replay GET /dashboard/team?view=team is 200 normal JSON.",
        "Uploads go to object storage. The API does not include local files from a user path. Unknown ad hooks 404.",
        "Do not claim the auth-scan Highs were confirmed LFI. They are false positives.",
        "Velvet Elves does not include local or remote files from user paths. Auth ZAP path-traversal Highs were path segments, not LFI.",
        "# Documents: MIME allowlist, stored in Supabase/S3, not executed.\n# No user-controlled open(path) include.\n# Auth ZAP plugin 6 High/Low: empty evidence, path segments.",
        "# SPA 6 WARN Path Traversal; 7 WARN RFI; 43 WARN File Inclusion\nAuth 33afa2aa: Path Traversal High/Low x4 FP.\nBurp 1049344 / 1051392 not run.",
    )

    d = out("5.2.1")
    save_page1(
        d,
        "CASA_5_2_1_uploads",
        "5.2.1 Protect against malicious file uploads",
        [
            ("Source", "ADA AL1: identify upload situations; describe type checks and how execution is prevented; source or screenshots. WSTG-BUSL-08/09 are AL2."),
            ("Where we accept files", "Deal documents POST /documents/upload (PDF, DOCX, DOC, JPEG, PNG, WEBP, GIF, TXT, max 20 MB). Logos (JPEG/PNG/WEBP/SVG/GIF, 2 MB) to a public logos bucket. Ad creatives image MIME allowlist. No upload is executed as HTML, JS, or server code."),
            ("Storage", "Files go to Supabase Storage / S3 object storage, not under the API process path. Textract reads bytes for OCR; it does not execute them."),
            ("Live", "Staging unsigned POST /documents/upload is 401. Authenticated probe.exe application/x-msdownload is 415. We did not upload malware samples."),
        ],
    )
    save_page2(
        d,
        "CASA_5_2_1_uploads",
        "5.2.1 AL1 verification mapping",
        [
            ("Type restrictions", "ALLOWED_MIME_TYPES on documents; LOGO_ALLOWED_MIME_TYPES; ad creative MIME set."),
            ("No execution", "Object storage, not an executable webroot."),
            ("Auth", "Document upload requires a JWT session. Authenticated disallowed MIME is 415."),
        ],
        "Velvet Elves restricts upload MIME types and stores files in object storage. Uploaded content is not executed as application code.",
    )
    save_code(
        d,
        "CASA_5_2_1_uploads",
        "5.2.1 MIME allowlists; object storage",
        """# app/api/v1/documents.py
ALLOWED_MIME_TYPES = pdf, docx, doc, jpeg, png, webp, gif, text/plain
MAX_FILE_BYTES = 20 MB
# unknown type -> 415

# app/services/logo_storage.py
LOGO_ALLOWED_MIME_TYPES = jpeg, png, webp, svg+xml, gif
LOGO_MAX_BYTES = 2 MB

# Storage: Supabase/S3. Not executed as HTML/JS/Python.""",
    )

    d = out("6.1.1")
    save_page1(
        d,
        "CASA_6_1_1_deps",
        "6.1.1 Components without known exploitable vulns",
        [
            ("Source", "ADA AL1: output of a dependency scan (OWASP dependency-check or ADA-approved). Pass if no CVE CVSS >= 7.0, or justify unused code / no patch available."),
            ("Tools", "pip-audit on backend requirements.txt; npm audit --omit=dev on the SPA. Not OWASP dependency-check. Fluid SAST is source, not a dependency CVE scan."),
            ("Lockfile as of this pack", "pydantic-ai-slim 1.107.5 and pypdf 6.16.2 are pinned (27 Aug code). ecdsa remains a python-jose transitive with no listed fix. pytest is requirements-dev only."),
            ("Honest limit", "This pack scans the local lockfiles. It is not a screenshot of the running production image layers. Owner deploy of the 27 Aug pins is required before claiming production matches."),
        ],
    )
    save_page2(
        d,
        "CASA_6_1_1_deps",
        "6.1.1 AL1 verification mapping",
        [
            ("Scan output", "See pip-audit and npm audit PNGs generated this session if the tools ran."),
            ("ecdsa", "No upstream fix. JWT verify uses python-jose[cryptography]. Accepted residual."),
            ("Production image", "Not claimed equal to this lockfile until the owner deploy (S12)."),
        ],
        "Local lockfiles were scanned with pip-audit and npm audit --omit=dev. ecdsa has no released fix. Production image equality is not claimed without the owner deploy.",
    )
    save_code(
        d,
        "CASA_6_1_1_deps",
        "6.1.1 Pinned upgrades in requirements.txt",
        """pydantic-ai-slim[openai,anthropic]==1.107.5
pypdf==6.16.2
# pytest lives in requirements-dev.txt (not the API image intent)
# ecdsa is transitive via python-jose; no fix listed.""",
    )

    d = out("6.2.1")
    save_page1(
        d,
        "CASA_6_2_1_debug",
        "6.2.1 Disable debug modes in production",
        [
            ("Source", "ADA AL1 DAST. Verification: scan shall not identify Burp 1050624 ASP.NET debugging enabled. Production is FastAPI, not ASP.NET."),
            ("Official ZAP", "SPA 10023 Debug Error Messages FAIL; 10056 X-Debug-Token FAIL. DAST_SUMMARY listed Application error / debug text as Low on some JSON 500s (generic message, no stack)."),
            ("Production control", "APP_DEBUG must be false when APP_ENV=production (settings validator + create_app). /api/docs /api/redoc /api/openapi.json are unset in production (404). Staging still serves docs."),
            ("Honest", "Staging docs are on. Auth ZAP Low application-error findings are generic 500 JSON, not a debug console."),
        ],
    )
    save_page2(
        d,
        "CASA_6_2_1_debug",
        "6.2.1 AL1 verification mapping",
        [
            ("Production docs", "Live GET production /api/docs is 404."),
            ("Staging docs", "Staging /api/docs is still 200. Not claimed as production."),
            ("Burp 1050624", "ASP.NET-specific. Burp was not run. App is FastAPI."),
        ],
        "Production debug and OpenAPI UI are off. Official ZAP did not report ASP.NET debugging. Staging docs remain enabled.",
    )
    save_code(
        d,
        "CASA_6_2_1_debug",
        "6.2.1 Production APP_DEBUG false; docs off",
        """# app/main.py
enable_api_docs = not get_settings().is_production
docs_url = /api/docs only when not production

# app/core/config.py
APP_DEBUG must be false when APP_ENV=production""",
    )
    save_code(
        d,
        "CASA_6_2_1_debug",
        "6.2.1 Official ADA ZAP debug rules",
        """# zap-casa-config.conf
10023 FAIL (Debug Error Messages)
10056 FAIL (X-Debug-Token)

DAST_SUMMARY: app-error Low on generic JSON 500s.
Burp 1050624 ASP.NET debugging not run.""",
        suffix="zap",
    )

    d = out("6.3.1")
    save_page1(
        d,
        "CASA_6_3_1_origin",
        "6.3.1 Origin is not used for access control",
        [
            ("Source", "ADA AL1 DAST. Verification: scan shall not identify Burp 2098689 CORS arbitrary origin trusted."),
            ("Official ZAP", "10098 / 20016 Cross-Domain Misconfiguration WARN. DAST_SUMMARY did not list arbitrary-origin CORS."),
            ("Authz", "Access control is JWT + require_role / require_tenant_access. Origin is only used for CORS allowlist (echo of known SPA origins) and password-reset redirect origin checks. A foreign Origin on GET /users/me is still 401."),
            ("Honest", "CORS allow_methods and allow_headers are *. Origins are the allowlist. Do not claim Origin is ignored for CORS."),
        ],
    )
    save_page2(
        d,
        "CASA_6_3_1_origin",
        "6.3.1 AL1 verification mapping",
        [
            ("Auth", "Missing Bearer is 401 regardless of Origin."),
            ("CORS", "Foreign Origin does not receive Access-Control-Allow-Origin (see 3.1.5)."),
            ("Burp 2098689", "Not run. Closest analog is ZAP 10098/20016."),
        ],
        "Velvet Elves authenticates with JWT, not the Origin header. Official ZAP did not report arbitrary-origin CORS as a High.",
    )
    save_code(
        d,
        "CASA_6_3_1_origin",
        "6.3.1 JWT auth; CORS origin allowlist only",
        """# app/core/auth.py  get_current_user
# JWT required. Origin is not read for authz.

# app/main.py  CORSMiddleware
allow_origins = settings.cors_origins_list
# not reflect-any-origin""",
    )
    save_code(
        d,
        "CASA_6_3_1_origin",
        "6.3.1 Official ADA ZAP CORS rules",
        """# zap-casa-config.conf
10098 WARN (Cross-Domain Misconfiguration)
20016 WARN (Cross-Domain Misconfiguration)

Burp 2098689 not run.""",
        suffix="zap",
    )

    d = out("6.4.1")
    save_page1(
        d,
        "CASA_6_4_1_dns",
        "6.4.1 Subdomain takeover protections",
        [
            ("Source", "ADA AL1: DNS evidence that names point at resources you control, or that third-party targets are still active. WSTG-CONF-10 is AL2."),
            ("Live names", "app.velvetelves.com and app.stage.velvetelves.com resolve to CloudFront. api.prod.velvetelves.com and api.stage.velvetelves.com resolve to the ALB. help.velvetelves.com is the help site. velvetelves.com is the marketing site."),
            ("What this pack has", "Live DNS lookups (A/AAAA/CNAME) from this machine on 31 Aug 2026."),
            ("What this pack does not have", "A Route 53 hosted-zone screenshot (AWS console is owner-captured). No claim that every historical review app CNAME was audited in the console."),
        ],
    )
    save_page2(
        d,
        "CASA_6_4_1_dns",
        "6.4.1 AL1 verification mapping",
        [
            ("Live hosts", "SPA CloudFront and API ALB answers exist (see dns PNG)."),
            ("Route 53 console", "Not captured in this pack."),
            ("AL2", "WSTG-CONF-10 was not run."),
        ],
        "Live production and staging names resolve to CloudFront or the ALB. A Route 53 console screenshot was not taken.",
    )
    save_code(
        d,
        "CASA_6_4_1_dns",
        "6.4.1 Names this pack resolved",
        """app.velvetelves.com          CloudFront
app.stage.velvetelves.com    CloudFront
api.prod.velvetelves.com     ALB
api.stage.velvetelves.com    ALB
help.velvetelves.com         help site
velvetelves.com              marketing

Route 53 console: not captured.""",
    )

    d = out("6.5.1")
    save_page1(
        d,
        "CASA_6_5_1_logs",
        "6.5.1 Do not log credentials or payment details",
        [
            ("Source", "ADA AL1 and AL2: written description, a login log sample, and a payment log sample if applicable. Session tokens in logs only as irreversible hashes."),
            ("Code", "Login takes the password in the POST body; handlers do not log it. Gmail paths mask emails (ab***@domain). JSON logs carry request_id, not Authorization. Payment card data is Stripe-hosted; we store Stripe ids, not PAN/CVV."),
            ("Obtained", "Write-up and code PNGs; _mask_email snippet."),
            ("Not obtained", "A CloudWatch (or other sink) sample captured during a real login. A sample captured during a real payment. AWS console is owner-captured. Do not claim those samples exist in this folder."),
        ],
    )
    save_page2(
        d,
        "CASA_6_5_1_logs",
        "6.5.1 AL1 verification mapping",
        [
            ("Written description", "This page plus M9g_logging.md."),
            ("Login log sample", "NOT captured from CloudWatch this session."),
            ("Payment log sample", "NOT captured. Cards are on Stripe Checkout."),
        ],
        "Code masks emails and does not log passwords or PAN. Live login and payment log extracts from CloudWatch were not obtained.",
    )
    save_code(
        d,
        "CASA_6_5_1_logs",
        "6.5.1 Email mask; no password logger",
        """# app/services/email/gmail_provider.py
def _mask_email(value):
    local_mask = local[:2] + '***'
    return f'{local_mask}@{domain}'

# Login: OAuth2 password form. Password is not written to the logger.
# Stripe: checkout_url / session ids, not PAN/CVV.""",
    )

    d = out("6.6.1")
    save_page1(
        d,
        "CASA_6_6_1_logout",
        "6.6.1 Browser storage cleared on logout",
        [
            ("Source", "ADA AL1: written description of confidential data in the browser after logout."),
            ("What is stored", "velvet_elves_token and velvet_elves_refresh_token in localStorage. Not Google tokens."),
            ("Logout", "POST /users/logout revokes the Supabase session, then clearTokens() removes both token keys. Staging 31 Aug 2026: both token keys present before Log Out, both absent after. velvet_elves_return_location remains."),
            ("Honest", "Short-lived access JWT can still work until expiry if stolen before logout revoke. Refresh replay after logout is 401 (2.2.1)."),
        ],
    )
    save_page2(
        d,
        "CASA_6_6_1_logout",
        "6.6.1 AL1 verification mapping",
        [
            ("Keys removed", "clearTokens removes velvet_elves_token and velvet_elves_refresh_token."),
            ("Server revoke", "POST /users/logout signs out the Supabase session."),
            ("UI shot", "Fresh staging Log Out this session: /login. Key-presence PNG from Playwright evaluate (not DevTools Application panel)."),
        ],
        "Logout clears the SPA token keys in localStorage and revokes the refresh session. velvet_elves_return_location remains after logout.",
    )
    save_code(
        d,
        "CASA_6_6_1_logout",
        "6.6.1 clearTokens on logout",
        """# frontend AuthContext.logout
# POST /users/logout then clearTokens()
# localStorage keys velvet_elves_token / velvet_elves_refresh_token removed""",
    )

    d = out("6.7.1")
    save_page1(
        d,
        "CASA_6_7_1_secrets",
        "6.7.1 Server-side secrets storage",
        [
            ("Source", "ADA AL1: written description plus source/screenshots of secrets management. Access control, crypto, monitoring."),
            ("Where secrets live", "AWS Secrets Manager for ENCRYPTION_KEY, Supabase JWT material, and other API env. Not in git. Production fails closed if ENCRYPTION_KEY is missing. Google tokens are Fernet-encrypted in integrations."),
            ("Disconnect", "is_active=false. Encrypted tokens remain on the row (soft deactivate). Do not claim a token wipe."),
            ("Not obtained", "AWS Secrets Manager console screenshot (owner). CloudTrail secret-access log screenshot. No secret values are attached."),
        ],
    )
    save_page2(
        d,
        "CASA_6_7_1_secrets",
        "6.7.1 AL1 verification mapping",
        [
            ("Access control", "ECS task role reads the secret; not in the SPA."),
            ("Crypto", "Fernet for Google tokens; Secrets Manager for the key."),
            ("Monitoring", "AWS CloudTrail exists for the account; a sample screenshot was not taken."),
        ],
        "Server secrets are in AWS Secrets Manager. Google tokens are Fernet-encrypted. Disconnect is soft deactivate. No secret values or AWS console shots are in this folder.",
    )
    save_code(
        d,
        "CASA_6_7_1_secrets",
        "6.7.1 Secrets Manager + Fernet; no values",
        """# ENCRYPTION_KEY from environment / Secrets Manager
# Production fails if missing (4.1.3)
# Google tokens Fernet-encrypted at rest (M9d)
# Disconnect: integrations.is_active = false
# Secret values are not in this screenshot.""",
    )


if __name__ == "__main__":
    main()
