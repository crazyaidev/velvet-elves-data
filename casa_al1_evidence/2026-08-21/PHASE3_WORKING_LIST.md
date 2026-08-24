# Phase 3 working list — 21 Aug 2026

CWE / finding, where it lives, fix vs compensating control. Official CASA XML packet exists (SPA + unauth API + auth API). Leftover pip-audit and compensating Mediums remain.

## Closed or in this pass

| Item | CWE / scanner | Where | Status |
| --- | --- | --- | --- |
| API HSTS / nosniff / XFO / Referrer / Permissions-Policy / no `Server` | CWE-16, CWE-200 | FastAPI `SecurityHeadersMiddleware` | **Staging live** 21 Aug. Prod still old. |
| Swagger public | CWE-200 | `/api/docs` gated when `APP_ENV=production` | **Code on staging**; prod still public until prod deploy. Staging keeps docs on purpose. |
| FastAPI / multipart / jose / cryptography / Pillow | pip-audit Highs | `requirements.txt` | **Staging live** 21 Aug (login + Gmail/Calendar authorize-url smoke passed). |
| `react-router-dom` 7.13.1 | npm audit | SPA | **Staging live** 21 Aug, pin 7.18.2. |
| pytest/ruff in prod image | PYSEC-2026-1845 | `requirements.txt` | **Staging live** 21 Aug — split to `requirements-dev.txt`. |
| OAuth popup `postMessage(..., "*")` | CWE-346 | Gmail/Outlook/DocuSign + Calendar callback HTML; SPA listeners | **Staging live** 21 Aug — target `FRONTEND_URL`; SPA ignores other origins. **Browser smoke passed:** Gmail + Calendar popups connected. |
| Dockerfile as root | F266 / CWE-250 | `Dockerfile` | **Staging live** 21 Aug (`velvet-elves-stage-backend:108`, image `main-e2d6989` / PR #276). `USER appuser`. Prod still old. |
| OAuth callback reflected/DOM XSS | CWE-79 | Five HTML callbacks (`error`, `error_description`) | **Staging live** 21 Aug (`velvet-elves-stage-backend:109`). Unauth re-scan `a9d78f05-…` **0 High**. Auth re-scan `33afa2aa-…` also **0 XSS High**. |
| Authenticated ZAP API | CWE-89 / CWE-22 (Low confidence Highs) | Staging OpenAPI with Bearer (platform-admin, user-requested) | **Done** 21 Aug, build `33afa2aa-…`. Highs are false positives — see DAST_SUMMARY. Send/DELETE excluded. |

## Open — scanner Mediums (SPA CSP)

| Item | Decision |
| --- | --- |
| `img-src … https:` | **Compensating control** after staging smoke 21 Aug (Gmail/Calendar popups + PDF preview passed). Tenant logos and signed thumbs are not a closed host list, so do not drop `https:` on a guess. Maps/Places autocomplete is out of test scope (`ADDRESS_AUTOCOMPLETE_ENABLED = false`). |
| `style-src 'unsafe-inline'` | **Compensating control.** Vite/Tailwind emit a hashed CSS file, but Radix/inline style attributes still need `'unsafe-inline'`. No nonce pipeline in CloudFront HTML (S3 SPA). Lab write-up: no inline `<script>` from user content; scripts are `'self'` + Google Maps hosts. |
| Missing SRI | **Compensating control for Maps.** `https://maps.googleapis.com/maps/api/js` is loaded dynamically; Google does not publish a stable `integrity=` hash. First-party JS is same-origin from CloudFront (hashed filenames). Fonts CSS from `fonts.googleapis.com` is style-only. |

## Open — scanner Mediums (OAuth callback CSP)

| Item | Decision |
| --- | --- |
| Callback `script-src`/`style-src 'unsafe-inline'` | **Compensating control.** The popup is a tiny first-party HTML page that must run one inline script to `postMessage` the SPA. Query strings are escaped; postMessage origin is locked to `FRONTEND_URL`. A nonce would need CloudFront/ALB HTML rewriting we do not have. |

## Open — Fluid Attacks SAST (backend)

| Item | Decision |
| --- | --- |
| F052 SHA-1 proposal ids (Low) | Compensating: not PII/token crypto. Fernet is AES. |
| F380 unpinned `python:3.12-slim` (Low) | Pin digest if the lab requires it. Do not pin a guessed digest. |
| F418 `COPY . .` (Low) | `.dockerignore` exists (`logs/` added). Narrow COPY if the lab requires it. |

## Open — authenticated API Highs (false positive / follow-up)

| Item | Decision |
| --- | --- |
| ZAP SQL Injection High (Low conf, 28 instances) | **Compensating / not confirmed SQLi.** Evidence is HTTP 500 only. Live replay: some params 422-validate; others return generic JSON 500 with no SQL text. SQLAlchemy parameterized queries. CASA API conf maps plugin 40018 to WARN. Follow-up: bad query/enum/UUID → 422 instead of 500. |
| ZAP Path Traversal High (Low conf, 4 instances) | **False positive.** Empty evidence; “attack” equals a path segment (`team` / `templates` / `settings`). `GET …/dashboard/team?view=team` is 200 JSON. |

## Open — leftover pip-audit

| Package | Decision |
| --- | --- |
| `pydantic-ai-slim` 1.22.0 | Dedicated bump later. 1.56.0 needs AI-stack + revisit of `opentelemetry-api<1.44` pin. Do not mix into a CASA weekend. |
| `PyPDF2` 3.0.1 | Audit cites 3.9.0; PyPI latest is still 3.0.1. Migrate to `pypdf` in a doc-parse PR. |
| `ecdsa` 0.19.2 | No fix listed. Transitive of python-jose; JWT verify path uses `python-jose[cryptography]`. |

## Open — session (CASA session-management)

| Item | Decision |
| --- | --- |
| JWT in `localStorage` (`velvet_elves_token`) | **Compensating control for AL1 unless a lab fails it.** SPA is CloudFront+S3; HttpOnly cookie needs API `Set-Cookie` + CSRF + SameSite + CORS credential mode. Prefer cookie migration before a paid lab if the CASA session case is mapped as fail-without-HttpOnly. Compensating today: HTTPS-only app, short-lived Supabase JWT, refresh token also in localStorage (same risk), logout clears keys, CSP `connect-src` locked to staging/prod API. |

## Optional / later

- Authenticated **SPA** ZAP (login-wall spider). API auth XML is the packet.
- Do not authenticated-ZAP production with `algoforth33@gmail.com`.
