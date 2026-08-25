# Compensating controls (CASA AL1 residuals)

**Date:** 24 Aug 2026  
**Scope:** Residuals after Fluid Attacks SAST (0 High/Critical/Medium) and official ZAP CASA XML (SPA `10f54abf-…`, unauth API `a9d78f05-…`, auth API `33afa2aa-…`).  
**Do not claim:** Zero Data Retention; that leftover Mediums are Highs; that session JWT is HttpOnly.

Companion: `../2026-08-21/PHASE3_WORKING_LIST.md`, `../2026-08-21/DAST_SUMMARY.md`, `../2026-08-21/DEPS_SUMMARY.md`.

## SPA CSP Mediums (ZAP CWE-693 / 345)

Live on `app.velvetelves.com` and `app.stage.velvetelves.com` (CloudFront policies `velvet-elves-prod-frontend-security-headers` / `velvet-elves-stage-frontend-security-headers`). Rechecked 24 Aug 2026 via GET `/`.

| Finding | Why it stays | Compensating control |
| --- | --- | --- |
| `img-src` includes `https:` | Tenant logos and signed document thumbs are not a closed host list. Tightening on a guessed allowlist would break real files. | First-party scripts are `'self'` (hashed CloudFront filenames). No user HTML is rendered as script. Maps autocomplete is off (`ADDRESS_AUTOCOMPLETE_ENABLED = false`). Gmail/Calendar OAuth popups and in-app PDF preview were smoke-tested after CSP attach. |
| `style-src 'unsafe-inline'` | Radix / inline `style=` attributes. CloudFront serves a static S3 `index.html`; there is no nonce injection pipeline. | No inline `<script>` from user content. `script-src` is `'self'` + Google Maps hosts only. Styles from `fonts.googleapis.com` are CSS only. |
| Missing SRI on Maps JS | `maps.googleapis.com/maps/api/js` is loaded dynamically. Google does not publish a stable `integrity=` hash. | First-party JS is same-origin hashed assets. Fonts CSS is style-only. Maps is not required for Gmail/Calendar review. |

CASA ZAP web conf maps plugin 10055 (CSP) to **WARN**. These are accepted residuals, not unfixed Highs.

## OAuth callback CSP Medium (ZAP CWE-693)

Callback HTML (`/api/v1/integrations/gmail/callback` and siblings) uses `script-src`/`style-src 'unsafe-inline'` for a **first-party** one-shot `postMessage` to the SPA.

Compensating:

- Query `error` / `error_description` are HTML-escaped; cancelled copy is generic (does not echo the query).
- `postMessage` target is `FRONTEND_URL` only (`https://app.velvetelves.com` in prod). SPA ignores other `event.origin` values.
- JSON API routes have no CSP by design; they are not HTML.

Re-scan after the XSS fix: unauth API `a9d78f05-…` **0 High**.

## Session: JWT in `localStorage` (ASVS session-management)

Keys: `velvet_elves_token`, `velvet_elves_refresh_token`. Not Google tokens. Google tokens stay Fernet-encrypted in `integrations` (M9d).

Not migrated to HttpOnly cookies for AL1: SPA is CloudFront+S3; cookies would need API `Set-Cookie`, CSRF, SameSite, and credentialed CORS. That is a separate product change.

Compensating for AL1:

- App and API are HTTPS-only.
- CSP `connect-src` locked to the env API (`api.prod.velvetelves.com` / `api.stage.velvetelves.com`) plus listed SaaS hosts.
- Logout clears the keys.
- Supabase JWT expiry + refresh rotation.
- XSS on OAuth callbacks closed (CWE-79 re-scan 0 High).

If a lab maps “no HttpOnly session cookie” as fail-without-fix, cookie migration is the follow-up. Do not tell the lab the session is a cookie today.

## Leftover `pip-audit` (not CASA SAST Highs)

| Package | Why open | Residual risk |
| --- | --- | --- |
| `pydantic-ai-slim` 1.22.0 | Fix 1.56.0 needs a coordinated AI-stack bump and the `opentelemetry-api<1.44` pin. | Draft/triage library, not auth. Dedicated PR later. |
| `PyPDF2` 3.0.1 | Advisory cites 3.9.0; PyPI latest is still 3.0.1. | Document parse only. Migrate to `pypdf` in a parse PR. |
| `ecdsa` 0.19.2 | No fix listed. Transitive of `python-jose`. | JWT verify uses `python-jose[cryptography]`, not the ecdsa backend. |

pytest/ruff were split to `requirements-dev.txt` (21 Aug). Do not treat leftover pip-audit as CASA-mapped Highs.

## Fluid Attacks Lows (SAST CSV `5999aab9-…`)

| Finding | Compensating |
| --- | --- |
| F052 SHA-1 proposal ids | Not PII/token crypto. Tokens/PII use Fernet (AES). |
| F380 unpinned `python:3.12-slim` | Pin a digest only with a verified current digest. Do not invent one. |
| F418 `COPY . .` | `.dockerignore` excludes logs and junk. Narrow COPY if the lab requires it. |

## Authenticated ZAP Highs (Low confidence) — not confirmed vulns

| Alert | Decision |
| --- | --- |
| CWE-89 SQLi (plugin 40018) | False positive / compensating. Evidence was HTTP 500 only, no SQL text. Replay: some params 422-validate; others generic JSON 500. SQLAlchemy parameterized queries. CASA API conf maps 40018 to WARN. |
| CWE-22 path traversal | False positive. “Attack” equaled a path segment (`team` / `templates` / `settings`). Live `GET …/dashboard/team?view=team` is 200 JSON. |

## Production vs staging (24 Aug 2026)

| Control | Staging | Production |
| --- | --- | --- |
| API HSTS / nosniff / XFO DENY / Referrer / Permissions-Policy / no `Server` | Live | Live |
| SPA CSP | Live | Live |
| `/api/docs` `/api/redoc` `/api/openapi.json` | **200** (kept for staging) | **404** |
| OpenAI `gpt-5.4` live test (`POST /settings/ai-provider/test`) | ok | ok |
| Official ZAP/Fluid XML/CSV | Staging only (ADA AL1 evidence surface) | Not re-scanned with ZAP |

Do not authenticated-ZAP production. Do not use Google reviewer `algoforth33@gmail.com` as a scan principal.
