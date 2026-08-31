# M9h — Scan process (honest)

ADA wants CASA-mapped SAST (Fluid Attacks `checks:`) and DAST (ZAP with `zap-casa-*.conf`), reports in **CSV or XML**, not both.

## What exists (21 Aug 2026)

| Scan | Result | Lab-ready? |
| --- | --- | --- |
| Unauth ZAP 2.17.0 `-quickurl` on staging SPA + API health | 0 High. SPA 3 Medium (CSP `img-src https:`, `style-src unsafe-inline`, SRI). Write-up: `../2026-08-21/DAST_SUMMARY.md` | **No** — not the official conf/XML packet; did not crawl OpenAPI |
| `npm audit --omit=dev` | 0 after `react-router-dom` 7.18.2 | Supporting |
| `pip-audit` after FastAPI/crypto bumps | 4 leftover packages (`pydantic-ai-slim`, `PyPDF2`, pytest-in-old-image, `ecdsa`). `../2026-08-21/DEPS_SUMMARY.md` | Supporting |
| Fluid Attacks SAST | CodeBuild `velvet-elves-casa-fluid-sast:5999aab9-…` (21 Aug, after non-root USER). CSV. **0 High / 0 Critical / 0 Medium**, 3 Low. `../2026-08-21/SAST_SUMMARY.md`. | **Yes for SAST CSV** |
| Official ZAP SPA | CodeBuild `velvet-elves-casa-zap-dast:10f54abf-…` `zap-full-scan.py` + `zap-casa-config.conf`. XML. **0 High**, 3 Medium (CSP/SRI). `../2026-08-21/DAST_SUMMARY.md`. | **Yes for SPA XML** |
| Official ZAP API | Keep `a9d78f05-…` (after XSS fix). XML. **0 High**, 3 Medium (callback CSP). `c13e9c57-…` superseded; `2fe02778-…` discarded. | **Yes for unauth API XML** |
| Official ZAP API (authenticated) | Keep `33afa2aa-…` (21 Aug). XML. **No XSS High.** Two High/Low-confidence alerts (CWE-89, CWE-22) written as false positives in `../2026-08-21/DAST_SUMMARY.md`. Ran as staging platform-admin at the user’s request; send/DELETE excluded. Discard `fb752d1f-…` (stopped, no XML). | **Yes for auth API XML** |
| Authenticated SPA ZAP | Not run — traditional spider stays on login (`localStorage` JWT) | Optional |

## Process

1. Backend SAST: CodeBuild `velvet-elves-casa-fluid-sast` + `casa_al1_evidence/aws/config.yaml` (CASA `checks:`, current `sast.include` schema). Backend only.
2. ZAP web: CodeBuild `velvet-elves-casa-zap-dast` + `zap-casa-config.conf` → `https://app.stage.velvetelves.com` (XML `10f54abf-…`).
3. ZAP API: same project, `SCAN_TARGET=api`, filtered OpenAPI (no cron tick / inbound webhooks) + `zap-casa-api-config.conf`.
4. ZAP API authenticated: `SCAN_TARGET=api-auth`, Bearer via Replacer (`SCAN_BEARER` env, never committed). Extra path drops + strip DELETE.
5. Export **one** of CSV or XML into `casa_al1_evidence/` (gitignored dumps).
6. Close CASA-mapped High/Critical or write a compensating control (`compensating_controls.md` + `../2026-08-21/PHASE3_WORKING_LIST.md`).

Do not scan production with `algoforth33@gmail.com`. The one authenticated staging API scan used platform-admin **because the user asked**; do not repeat that on production.
