# Staging DAST — 21 Aug 2026

## Official CASA packet (ZAP Docker via CodeBuild)

Tool: `ghcr.io/zaproxy/zaproxy:stable` (`zap-full-scan.py` / `zap-api-scan.py`) in privileged CodeBuild project `velvet-elves-casa-zap-dast`, us-east-2. Configs: ADA `zap-casa-config.conf` / `zap-casa-api-config.conf`. Output **XML only**.

Unauthenticated staging SPA + API, plus one authenticated staging API scan. Not `algoforth33@gmail.com`. Do **not** submit the stopped auth build `fb752d1f-…`.

### SPA (keep)

| | |
| --- | --- |
| Target | `https://app.stage.velvetelves.com` |
| Build | `velvet-elves-casa-zap-dast:10f54abf-974d-4372-aa2a-1051aeb7ff46` |
| Artifact | `s3://velvet-elves-stage-codebuild-source-388482955098/casa-al1/results/10f54abf-974d-4372-aa2a-1051aeb7ff46/zap-dast-results` |
| Local XML | `casa_al1_evidence/2026-08-21/dast/spa-10f54abf/extracted/zap-casa-spa.xml` |

**0 High.** 3 Medium, 4 Low, 3 Informational. Same Mediums as the earlier `-quickurl` pass.

| Alert | Risk | CWE | CASA conf | Notes |
| --- | --- | --- | --- | --- |
| CSP: Wildcard Directive (`img-src https:`) | Medium | 693 | WARN (10055) | Compensating: tenant logos / signed thumbs. |
| CSP: style-src unsafe-inline | Medium | 693 | WARN (10055) | Compensating: Radix/inline styles; no nonce on S3 SPA. |
| Sub Resource Integrity Attribute Missing | Medium | 345 | not in conf (default WARN) | Compensating: Maps JS has no stable `integrity=`. |
| Missing COEP / COOP / CORP | Low | 693 | — | New vs quickurl. Not required to isolate the SPA from Maps/Stripe iframes. |
| Server leaks version (`AmazonS3` / CloudFront) | Low | 497 | — | Expected on the SPA origin. |
| Modern Web Application / cache info | Info | — | — | Not a fail. |

Traditional spider only (ADA command does not pass `-j`). URLs hit: `/`, `/robots.txt`, `/sitemap.xml`. Authenticated app routes were not crawled.

### API (keep)

| | |
| --- | --- |
| Target | Filtered staging OpenAPI (`https://api.stage.velvetelves.com`), 481 paths / 635 imported URLs |
| Build | `velvet-elves-casa-zap-dast:a9d78f05-362d-44f0-9481-60fab6dd7c21` |
| Artifact | `s3://velvet-elves-stage-codebuild-source-388482955098/casa-al1/results/a9d78f05-362d-44f0-9481-60fab6dd7c21/zap-dast-results` |
| Local XML | `casa_al1_evidence/2026-08-21/dast/api-a9d78f05/extracted/zap-casa-api.xml` |
| ZAP exit | 0 |

Dropped from the spec (documented): cron tick + inbound Stripe / DocuSign / email webhooks.

**0 High / 0 Critical.** 3 Medium (callback CSP), 11 Low.

Live curl after `velvet-elves-stage-backend:109`: all five OAuth callbacks return generic “cancelled” copy, do **not** echo `</p><scrIpt>…`, and send callback CSP.

Do **not** submit `c13e9c57-…` (XSS Highs, superseded) or `2fe02778-…` (failed import).

| Alert | Risk | CWE | Where | Decision |
| --- | --- | --- | --- | --- |
| Reflected / DOM XSS | — | 79 | OAuth HTML callbacks | **Closed** on re-scan `a9d78f05-…`. |
| CSP Header Not Set | — | 693 | Same pages | **Closed.** Replaced by callback CSP. |
| CSP: `script-src`/`style-src` unsafe-inline; missing fallbacks | Medium | 693 | Gmail / Outlook / DocuSign / Calendar Google callback HTML | **Compensating.** Popup needs a first-party inline script to `postMessage` the opener; styles are a tiny static block; query strings are escaped; origin is locked. JSON API routes have no CSP (by design). |
| HTTPS content via HTTP / HSTS not set | Low | 311 / 319 | `http://api.stage.velvetelves.com` | ALB HTTP probe. HTTPS already sends HSTS. |
| Server 500s | Low | 388 | `/api/v1/ads/hook_id/click`, some public help `locale=` fuzz | Follow up; not CASA High. |
| Application error / debug text | Low | 550 / 1295 | ads click 500 body | Follow up. |
| Missing COEP/COOP/CORP; unexpected content-type | Low | 693 / — | JSON API | Compensating / expected. |

Client-error flood (613 + 6672 Informational) is unauthenticated 401/422 against the OpenAPI surface. Expected.

### API authenticated (keep)

Ran at the user’s request as the **staging platform-admin** session (not a throwaway user). Bearer JWT via ZAP Replacer. Token and password were **not** written into git, CASA markdown, or the S3 source zip.

| | |
| --- | --- |
| Target | Filtered staging OpenAPI, **446 paths kept**, 37 DELETE ops stripped, **591 imported URLs** |
| Build | `velvet-elves-casa-zap-dast:33afa2aa-875e-4b18-a848-c13a790562ee` |
| Window | `2026-08-21T19:57:31Z` → `2026-08-21T23:08:10Z` (~3h 11m). Import at `20:01:34Z`. |
| Artifact | `s3://velvet-elves-stage-codebuild-source-388482955098/casa-al1/results/33afa2aa-875e-4b18-a848-c13a790562ee/zap-dast-results` |
| Local XML | `casa_al1_evidence/2026-08-21/dast/api-auth-33afa2aa/extracted/zap-casa-api-auth.xml` |
| ZAP exit | 0 |
| Tool | ZAP 2.17.0, official `zap-casa-api-config.conf` |

Excluded so Gmail and tenants are not destroyed: register / password-reset / schedule-deletion / send / approve / resend / email / legal-hold / refund / platform user email change, plus **all DELETE**. The crawler can still have mutated staging rows via POST/PATCH/PUT.

Discard `fb752d1f-…` (STOPPED mid-BUILD, no XML).

**No confirmed XSS High.** OAuth callback CWE-79 stays closed. Persistent XSS in JSON is **Low / Low confidence** (plugin 40014; ZAP notes Content-Type is not HTML).

ZAP still raised two **High / Low-confidence** active-scan alerts. Official API CASA conf maps SQL Injection (40018) to **WARN**, not FAIL. Path Traversal (plugin 6) is not a FAIL rule on the API conf. Replay against live staging after the scan:

| Alert | Risk (conf) | CWE | Count | Decision |
| --- | --- | --- | --- | --- |
| SQL Injection | High (Low) | 89 | 28 | **False positive / compensating.** Evidence is `HTTP/1.1 500` only — no SQL error text, no timing proof. Replay: `page_size='(` → **422** Pydantic `int_parsing`; `team_id='` and `use_case="` → generic JSON `{"status_code":500,"message":"An internal server error occurred."}`. Queries go through SQLAlchemy; unhandled enum/UUID noise should be 422, not 500. Follow-up, not a confirmed CWE-89. |
| Path Traversal | High (Low) | 22 | 4 | **False positive.** Empty evidence. “Attacks” are URL path segments (`team`, `templates`, `settings`). Replay `GET /api/v1/dashboard/team?view=team` → **200** normal JSON. |
| Callback CSP `unsafe-inline` / missing fallbacks | Medium | 693 | 12 | Same compensating control as unauth API. |
| CSP Header Not Set | Medium | 693 | 2 | JSON 500s on placeholder `event_id` / `tenant_id` — not HTML. JSON APIs do not ship CSP. |
| Persistent XSS in JSON | Low (Low) | 79 | 13 | Compensating: JSON, not HTML; SPA does not `dangerouslySetInnerHTML` those fields. |
| Server 500s / app-error / “debug” text | Low | 388 / 550 / 1295 | documents `document_id` placeholders + the SQLi 500 set | Follow up: coerce bad IDs/enums to 422. Bodies do not leak stacks. |
| `Server: awselb/2.0` | Low | 497 | 2 | ALB default on two error paths. App already omits uvicorn `Server`. |
| HTTPS-via-HTTP / HSTS not set | Low | 311 / 319 | handful | Same ALB HTTP probe as unauth. HTTPS already sends HSTS. |

Session alerts are Informational (`Authentication Request Identified`, `Session Management Response Identified`). API auth is `Authorization: Bearer`, not cookies — cookie HttpOnly/Secure flags were not raised.

## Earlier first pass (not the lab XML)

Portable ZAP 2.17.0 `-quickurl` on this Windows box. Useful smoke; **not** `zap-casa-*.conf` XML.

| Target | Mode | High | Medium | Low |
| --- | --- | --- | --- | --- |
| `https://app.stage.velvetelves.com` | `-quickurl` | **0** | **3** | 1 |
| `https://api.stage.velvetelves.com/api/v1/health` | `-quickurl` | **0** | **0** | 1 |

## Still to do

- Authenticated **SPA** ZAP (traditional spider stays on login; JWT is in `localStorage`) — optional; API auth is the coverage that was missing
- Do **not** run authenticated production ZAP with `algoforth33@gmail.com`
