# CASA AL1 — Jan prep plan (before asking Jake)

**Date:** August 20, 2026  
**Audience:** Jan  
**Companion:** `GOOGLE_CASA_AL1_NEXT_STEPS.md` (Jake spend / lab kickoff)  
**Goal:** Know we can pass ADA-CASA AL1 *before* Jake pays a lab.

Live facts in this file were re-checked on 20 August 2026 (`curl.exe` against production and staging). Do not treat older internal notes as the source of truth for headers or Swagger.

---

## Verdict

**No. The project is not yet sufficiently prepared to pass with confidence.**

The product has real security foundations (encrypted tokens and PII, PKCE, tenant filtering, HTTPS, privacy/deletion pages, isolation tests, and CloudFront security headers on the SPA). That is necessary and not sufficient.

CASA AL1 (ADA spec v2.1.1, June 2026) is a **verified self-assessment**:

1. **You** produce CASA-mapped SAST/DAST evidence and remediate failed CWEs
2. **You** self-attest the remaining OWASP ASVS / CASA test cases
3. An ADA-authorized lab **reviews that evidence** (it does not independently pentest the app — that is AL2). Google may still require the work to go through an authorized lab such as TAC.

We have not produced (1). Several items a first CASA-mapped scan will fail are still true. Asking Jake now would buy a first review we already know will bounce, then burn the two Basic retest cycles (or extra weeks) on work we can do ourselves.

Do that work first. Then ask Jake.

---

## What is already in good shape

Do not rebuild these. Document them for the lab questionnaire.

| Area | Evidence in the product |
| --- | --- |
| OAuth least privilege | Restricted/sensitive Google scopes in production are `gmail.readonly`, `gmail.send`, and `calendar.events`. Identity scopes (`openid`, `userinfo.email`, and Gmail also `userinfo.profile`) are requested with them. PKCE. Encrypted tokens in `integrations`. |
| PII / tokens at rest | Fernet (`app/utils/encryption.py`). `ENCRYPTION_KEY` required in production. Confirm the live value lives in the backend Secrets Manager secret — do not assume from docs. |
| Tenant isolation | App-layer filters plus isolation tests (`test_integration_isolation.py`, `test_task_tenant_isolation.py`). RLS policies exist (`20260511094000_rls_tenant_isolation.sql`) as defense in depth; the backend still uses `service_role`, so RLS is not what enforces isolation today. |
| Gmail logging | Provider logs mask addresses (`_mask_email`). Policy: no tokens, auth codes, or full bodies. |
| Transport | Production is HTTPS (`app.velvetelves.com`, `api.prod.velvetelves.com`). |
| SPA security headers | CloudFront already injects AWS managed SecurityHeadersPolicy `67f7725c-6f97-4210-82d7-5512b31e9d03` on `app.velvetelves.com` and `app.stage.velvetelves.com`: HSTS (`max-age=31536000`), `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-XSS-Protection`. |
| Auth | Supabase Auth + JWT. Registration rate-limited. |
| Public policy | Privacy (Limited Use), data deletion, terms — live. Disconnect in Settings. |
| Abuse guards | Rate limits on register and several public routes. Webhook SSRF blocked (`url_safety`). |

---

## What will fail a first lab review (fix before Jake)

These are observed in the current tree or live production, not hypothetical.

### A. No CASA-mapped scan exists (the AL1 evidence the lab reviews)

ADA’s AL1 process is: **you scan, you remediate, you attest; the lab verifies the packet.** Recommended tools: Fluid Attacks (SAST) **or** OWASP ZAP (DAST), using the CASA CWE config for the application types we actually ship (**web + API**). If those tools are used, upload results in **CSV or XML** (not both). Another scanner is allowed only with CWE-mapped PASS/FAIL plus OWASP Benchmark evidence.

Practical coverage for this product (SPA + FastAPI): Fluid Attacks SAST on both repos **and** ZAP DAST against the staging app, which exercises the API. That is more than the minimum “or,” and it is what we should have before paying TAC. Confirm TAC’s exact method at kickoff (upload-only vs they also re-run a scan).

CI today is lint + pytest / lint + build. There is no Fluid Attacks, ZAP, pip-audit, npm audit, Trivy, or Dependabot job.

Until a scan against the CASA CWE set is green (or every fail is remediated and re-scanned), we are not ready.

Guide: https://appdefensealliance.dev/casa/tier-2/ast-guide

### B. Missing headers — API yes, SPA mostly no (except CSP)

**Do not tell a lab that production has no security headers.** The SPA already has HSTS / frame options / nosniff / referrer (see table above).

Still missing as of 20 August 2026:

| Surface | Missing |
| --- | --- |
| `https://app.velvetelves.com` (CloudFront) | `Content-Security-Policy`, `Permissions-Policy`. No CSP meta tag in the frontend repo either. |
| `https://api.prod.velvetelves.com` (uvicorn behind ALB) | All of the above, plus HSTS, `X-Frame-Options`, nosniff, Referrer-Policy. Live GET `/api/v1/health` returns only `server: uvicorn` and `x-request-id`. |

CSP belongs on the **SPA**, not as a first-class requirement on JSON API responses. The API needs HSTS / nosniff / frame options (and should stop advertising `server: uvicorn`).

`curl -I` against the API health route is `HEAD` and returns **405**. Use `curl.exe -sI -X GET https://api.prod.velvetelves.com/api/v1/health`.

### C. OpenAPI / Swagger is always on (confirmed live)

```python
docs_url="/api/docs"
redoc_url="/api/redoc"
openapi_url="/api/openapi.json"
```

These are not gated on `app_env`. Production currently serves them (`/api/docs` 200, `/api/openapi.json` ~910 KB). Labs treat public API docs in production as an information-disclosure finding. Disable them when `is_production`.

### D. Session token in `localStorage`

`AuthContext` stores `velvet_elves_token` and `velvet_elves_refresh_token` in `localStorage` (`TOKEN_KEY` / `REFRESH_TOKEN_KEY` in `src/utils/constants.ts`). That is a CASA / ASVS session-management item (sensitive data in browser storage; XSS can steal the session). A default ZAP spider does **not** reliably fail this as High — do not plan around that. The lab questionnaire will still ask.

Moving to httpOnly cookies is the correct long-term fix and is a real frontend+backend change. For AL1, either:

- **Fix it** (httpOnly Secure SameSite cookies), or
- **Keep it** and write a compensating-control attestation: tight CSP, XSS sanitization, short JWT TTL, refresh rotation — and accept the lab may still fail it.

Do not discover this for the first time on a paid review.

### E. CORS is wide

`allow_methods=["*"]`, `allow_headers=["*"]`, `allow_credentials=True`. Origins come from `CORS_ORIGINS` (hopefully production-only in AWS Secrets Manager). Confirm prod origins are exactly the Velvet Elves hosts, then tighten methods/headers if the lab flags it.

### F. Evidence packet (M9) was never assembled

`GMAIL_GOOGLE_APPROVAL_MATERIALS_AND_STEPS.md` still lists M9 as **To do**. The lab questionnaire will ask for architecture, data flow, token handling, deletion, incident response, subprocessors. We cannot self-attest from memory.

### G. Defaults that must be proven false in production

- `app_debug: bool = True` in `config.py` (`APP_DEBUG`) — must be false in prod secrets
- `supabase_jwt_secret` default `"test-supabase-secret"` — must be the real Supabase secret in prod
- Readiness handler returns `str(exc)` on DB failure — can leak internals

### H. Documentation the lab will compare to production

Old “Gmail watch renews daily” wording is false. Production does two different things, both observed 20 Aug 2026:

- **Opportunistic renew-after-sync** on active mailboxes.
- **Idle `renew-due` sweep** on the hourly EventBridge tick (`velvet-elves-prod-hourly-tick` → POST `/api/v1/internal/schedules/tick`). Logs show `gmail_watches=0/4(fail=1)` each hour: the sweep runs; one of four watches is currently failing (operational, not “scheduler missing”).

Do not write “renews daily.” Do not claim EventBridge target invocations succeed (`FailedInvocations` is 1/hour because the tick is synchronous and API destinations time out); claim the backend completes.

---

## Prep plan (Jan only — no Jake, no spend)

Work in this order. Do not skip to the lab until the gate in Phase 6 is green.

### Phase 0 — Inventory (half a day)

- [x] Confirm production `APP_DEBUG=false`, real `ENCRYPTION_KEY`, real `SUPABASE_JWT_SECRET`, production-only `CORS_ORIGINS` — **PASS 20 Aug 2026.** Live task `velvet-elves-prod-backend:43`: `APP_ENV=production`, `APP_DEBUG=false`. `ENCRYPTION_KEY` and `SUPABASE_JWT_SECRET` are mapped from `/velvet-elves/prod/backend` (Fernet 32-byte key; JWT is not the test default). `CORS_ORIGINS=https://velvetelves.com,https://app.velvetelves.com,https://help.velvetelves.com` (no localhost, no stage).
- [x] Confirm `/api/docs` is reachable on `https://api.prod.velvetelves.com` — **CONFIRMED 20 Aug 2026 (this is the bug, not a pass).** Unauthenticated GET: `/api/docs` 200 Swagger UI, `/api/redoc` 200, `/api/openapi.json` 200 (~910 KB, 471 paths, includes `/api/v1/internal/schedules/tick`). Staging `/api/docs` is also 200. Health body: `{"status":"ok","env":"production","version":"0.1.0"}`. Fix in Phase 1: disable docs when `is_production`.
- [x] Re-record headers — **CONFIRMED 20 Aug 2026 (GET, not HEAD).** SPA `app.velvetelves.com` (CloudFront): HSTS `max-age=31536000`, `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-XSS-Protection: 1; mode=block`. **Missing CSP and Permissions-Policy.** Staging app matches. API `api.prod.velvetelves.com` `/api/v1/health`: **no security headers**; `server: uvicorn` + `x-request-id` only. Staging API matches. (Marketing and help CloudFront distributions have the same SPA header set; also no CSP.)
- [x] Confirm whether EventBridge actually POSTs `/api/v1/internal/schedules/tick` in production — **CONFIRMED 20 Aug 2026.** Rule `velvet-elves-prod-hourly-tick` is ENABLED (`rate(1 hour)`). Target is API destination `velvet-elves-prod-schedule-tick` → `POST https://api.prod.velvetelves.com/api/v1/internal/schedules/tick` with connection `velvet-elves-prod-cron` (`X-VE-Cron-Secret`). EventBridge Scheduler (the v2 service) has no schedules; classic EventBridge is what fires. CloudWatch logs `/ecs/velvet-elves/prod/backend` show a completed `schedule tick:` every hour (e.g. 14:13–19:13 UTC today), including `gmail_watches=0/4(fail=1)` so idle `renew-due` **does run**. EventBridge `FailedInvocations` is also 1/hour: the tick is synchronous (`VE_TICK_ASYNC` is not set on the task) and API destinations time out before the ~25s tick returns; retries are 0 so it does not double-run. Attest hourly tick + renew-due as live. Do not claim EventBridge “succeeds”; claim the backend completes.
- [x] List subprocessors actually used in prod — **INVENTORIED 20 Aug 2026** from live ECS task `velvet-elves-prod-backend:43` plus presence (not values) of keys in `/velvet-elves/prod/backend`. See table below. Privacy page (`velvetelves.com/privacy` sharing section) lists AWS, Supabase, Stripe, SendGrid, OpenAI or Anthropic, Google APIs. It does **not** name DocuSign, Microsoft, Textract, or Google Cloud Pub/Sub — fix in M9 / privacy copy later, not now.
- [x] Confirm AI provider contracts/API settings: no training on customer data — **UPDATED 24 Aug 2026.** OpenAI and Anthropic **API terms** default to no training. AWS Textract is **opted out** org-wide (`p-90qm6ijnvl`). OpenAI Sharing screenshot captured (`casa_al1_evidence/m9/openai-data-controls.png`): Velvetelves org, all three radios Disabled. Do not claim Zero Data Retention. There is no “Improve the model for everyone” control.

Production subprocessors (what is actually configured, 20 Aug 2026):

| Vendor | Role in production | Evidence it is live |
| --- | --- | --- |
| Amazon Web Services | Hosting (ECS, ALB, CloudFront, S3, Secrets Manager, EventBridge, CloudWatch); document OCR via Textract | Task env `DOCUMENT_TEXT_EXTRACTION_PROVIDER=textract`; `TEXTRACT_S3_BUCKET` SET; `TEXTRACT_OCR_ONLY_MODE=false` |
| Supabase | Auth + Postgres | `SUPABASE_URL` SET (`*.supabase.co`); service role + JWT mapped |
| Stripe | Tenant billing / pay links | `STRIPE_SECRET_KEY`, publishable key, webhook secret SET |
| SendGrid | Platform transactional email (welcome / notify / invite) | `SENDGRID_API_KEY` SET |
| OpenAI | Default AI provider (`AI_PROVIDER=openai`, `OPENAI_MODEL=gpt-5.4`) | `OPENAI_API_KEY` SET; tenants may override per workspace |
| Anthropic | Alternate AI provider (tenant can select Claude) | `ANTHROPIC_API_KEY` SET; `ANTHROPIC_MODEL=claude-sonnet-5` |
| Google | Gmail + Calendar OAuth/APIs; Gmail Pub/Sub watch | `GOOGLE_CLIENT_ID/SECRET` SET; `GMAIL_PUBSUB_TOPIC_NAME` SET |
| Microsoft | Outlook mail + calendar OAuth (optional per user) | `MICROSOFT_CLIENT_ID/SECRET` SET |
| DocuSign | E-signature | Integration key SET; **still demo/sandbox** (`DOCUSIGN_BASE_URL=https://demo.docusign.net/restapi`, OAuth `account-d.docusign.com`) |

Not a customer-data subprocessor, but public: Swagger UI loads `cdn.jsdelivr.net` while `/api/docs` stays on. Goes away when Phase 1 disables docs.

AI / ML training (20 Aug 2026):

| Processor | Trains on Velvet Elves customer content by default? | What we verified | Gap |
| --- | --- | --- | --- |
| OpenAI API (`chat.completions` in `openai_provider.py`; default prod provider) | **No**, unless the org explicitly opts in. API data is not used to train as of 1 Mar 2023. Code does not fine-tune and does not set `store=true`. | Terms + code path. Sharing PNG 24 Aug 2026 (`casa_al1_evidence/m9/openai-data-controls.png`): all three radios Disabled. Privacy page claim matches. | Not Zero Data Retention (30-day abuse monitoring still applies). |
| Anthropic API (`messages.create` in `anthropic_provider.py`; tenant-selectable) | **No.** Commercial Terms: Anthropic may not train on Customer Content from Services. | Terms + code path. | No ZDR agreement. Consumer Claude.ai terms do **not** apply (we use the API). |
| Amazon Textract (all uploaded PDF/image parse) | **Opted out 20 Aug 2026.** AWS org root policy `velvet-elves-ai-services-opt-out` (`p-90qm6ijnvl`) sets `default.opt_out_policy=optOut`. Effective policy on the prod account confirms it. | `describe-effective-policy` → `{"services":{"default":{"opt_out_policy":"optOut"}}}`. | Privacy page still does not mention Textract. Screenshot not required for AWS. |

Sources: [OpenAI your data](https://developers.openai.com/api/docs/guides/your-data), [OpenAI business data](https://openai.com/business-data/), [Anthropic Privacy Center](https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training), [Textract FAQs](https://aws.amazon.com/textract/faqs/), [AWS AI opt-out](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_ai-opt-out.html).

### Phase 1 — Cheap hardening the first scan will fail without (1–2 days)

Deploy to **staging first**, then production.

- [x] FastAPI security-headers middleware for the **API** — **STAGING LIVE 21 Aug 2026; PRODUCTION LIVE 22 Aug 2026** (`velvet-elves-prod-backend:44`). `SecurityHeadersMiddleware` stamps HSTS (`max-age=31536000; includeSubDomains`), nosniff, XFO DENY, Referrer-Policy, Permissions-Policy. Live GET `https://api.prod.velvetelves.com/api/v1/health` returns those headers and **no** `server: uvicorn`. Tests: `app/tests/test_security_headers.py`.
- [x] CSP on the **SPA** via CloudFront — **STAGING LIVE 20 Aug 2026; PRODUCTION LIVE 22 Aug 2026.** Production policy `velvet-elves-prod-frontend-security-headers` (`0e5af791-5c34-4879-a0d4-e8eb3860ec33`) on `app.velvetelves.com` (`E1MO4BC0WAQDKB`). **Post-CSP Chrome smoke PASSED 22 Aug 2026** on the dedicated testing account: Gmail Test connection, Calendar Add my closings, Ask AI, in-app PDF preview.
- [x] Disable `/api/docs`, `/api/redoc`, `/api/openapi.json` when `is_production` — **PRODUCTION LIVE 22 Aug 2026** (all three 404). Staging keeps docs on purpose (`APP_ENV=staging`). Tests: `app/tests/test_openapi_docs.py`.
- [x] Stop returning raw exception strings from `/api/v1/health/ready` — **STAGING HEALTHY 21 Aug 2026; production not redeployed.** Happy path on staging is `200 {"status":"ready","db":true}` with the new security headers. 503 hide-details was covered in tests (`test_readiness_ok`, `test_readiness_hides_exception_details`), not forced against live staging.
- [x] Confirm `app_debug` cannot be true in production (assert in startup) — **CODE DEPLOYED TO STAGING 21 Aug 2026; production image not updated yet.** Settings validator rejects `APP_ENV=production` + `APP_DEBUG=true` at load. Startup raises `RuntimeError` if those flags are mutated after load. Live staging health is `env=staging` (guard does not apply). Live prod already has `APP_DEBUG=false` on the task definition (Phase 0) and will pick up the guard on the next prod backend deploy. Tests: `app/tests/test_production_debug_guard.py`.
- [x] Enable AWS Organizations AI services opt-out for Textract (and other AWS AI) — **LIVE 20 Aug 2026.** Enabled `AISERVICES_OPT_OUT_POLICY` on org root `r-07ts`. Created policy `velvet-elves-ai-services-opt-out` (`p-90qm6ijnvl`), attached to the root, locked so child policies cannot override. Effective policy for account `388482955098`: `default.opt_out_policy = optOut` (covers Textract and future AWS AI services). OpenAI Sharing screenshot **captured 24 Aug 2026** (`casa_al1_evidence/m9/openai-data-controls.png`). Do not claim ZDR from the Data retention tab.

Do **not** change OAuth scopes, redirect URIs, or consent-screen branding. Google froze those for the verification case.

### Phase 2 — First CASA-mapped scans (1–2 days)

Run the tools ADA documents, not a random scanner.

Official ADA files are on disk (21 Aug 2026) at `velvet-elves-data/casa_al1_evidence/configs/official/` — `fluid-config.yaml`, `fluid-Dockerfile`, `zap-casa-config.conf`, `zap-casa-api-config.conf`. ADA: Fluid Attacks pre-configured SAST is **not** listed as compatible with TypeScript/JavaScript; backend is the SAST target; SPA is ZAP web + API OpenAPI.

Portable **Temurin 17 + ZAP 2.17.0** now live under `casa_al1_evidence/tools/` (gitignored). Fluid Attacks SAST still needs Docker/WSL (not installed; enabling WSL would require a reboot).

**SAST (backend + frontend)**

- [x] Official Fluid Attacks CASA config + Dockerfile downloaded (21 Aug 2026)
- [x] Run Fluid Attacks SAST on `velvet-elves-backend` via AWS CodeBuild (`velvet-elves-casa-fluid-sast`, 21 Aug 2026). CSV only. Keep build `5999aab9-…` (after non-root `USER`): **0 High / 0 Critical / 0 Medium**, 3 Low (SHA-1 proposal id, unpinned base image, `COPY . .`). Write-up: `casa_al1_evidence/2026-08-21/SAST_SUMMARY.md`. Do not scan the TS frontend with this tool.
- [ ] Frontend static: ZAP DAST first pass done below; custom CWE-mapped SAST + OWASP Benchmark only if a lab insists on SAST for TS

**DAST (live app)**

- [x] Official ZAP CASA web + API configs downloaded (21 Aug 2026)
- [x] Unauthenticated ZAP 2.17.0 `-quickurl` against staging (21 Aug 2026). **0 High** on SPA and API health. SPA **3 Medium** (CSP wildcard `img-src https:`, `style-src unsafe-inline`, missing SRI). API health **0 Medium**, 1 Low (HTTP-vs-HTTPS probe). Write-up: `casa_al1_evidence/2026-08-21/DAST_SUMMARY.md`.
- [x] Official CASA SPA XML via CodeBuild `zap-full-scan.py` + `zap-casa-config.conf` (21 Aug 2026). Keep `10f54abf-…`. **0 High**, 3 Medium (same CSP/SRI), 4 Low. Traditional spider only (login wall).
- [x] Official CASA API XML via `zap-api-scan.py`. Keep `a9d78f05-…` (after XSS fix). **0 High**, 3 Medium (callback CSP `unsafe-inline`). Supersedes `c13e9c57-…`. Discard `2fe02778-…`.
- [x] OAuth callback HTML XSS (CWE-79) **staging live** 21 Aug (`velvet-elves-stage-backend:109`). Live curl: five callbacks do not reflect script; generic cancelled copy; callback CSP present.
- [x] Authenticated ZAP API on staging (21 Aug 2026). User requested the **staging platform-admin** session instead of a throwaway user. Keep `33afa2aa-…`. Filtered OpenAPI (no send/DELETE). **No XSS High.** Two **High / Low-confidence** alerts (SQLi CWE-89, path traversal CWE-22) replayed as false positives — write-up in `DAST_SUMMARY.md`. Crawler may have mutated staging rows via POST/PATCH/PUT. Discard stopped build `fb752d1f-…`.
- [ ] Authenticated **SPA** ZAP still optional (traditional spider stays on login; JWT is in `localStorage`)
- [ ] Do **not** run an authenticated production ZAP with `algoforth33@gmail.com` as the first pass

**Dependencies**

- [x] `pip-audit` — **re-run 21 Aug 2026 after bumps: 4 vulns in 4 packages** (was 56/9). Remaining: `pydantic-ai-slim` 1.22.0 (needs coordinated AI-stack bump), `PyPDF2` 3.0.1 (PyPI has no 3.9.0; migrate to `pypdf` later), `pytest` 8.3.4 (split to `requirements-dev.txt`; staging image as of later 21 Aug deploy should no longer ship it), `ecdsa` 0.19.2 (transitive of python-jose; no fix listed).
- [x] `npm audit --omit=dev` — **0 vulnerabilities** after pinning `react-router-dom` **7.18.2**. Dev toolchain vulns (Vitest UI, etc.) remain out of the CloudFront SPA.
- [x] Production High remediations **staging live 21 Aug 2026** (prod still old FastAPI image until a prod deploy):
  - Frontend: `react-router-dom` 7.13.1 → **7.18.2**.
  - Backend: FastAPI 0.115.6 → **0.135.4** + Starlette **1.3.1**; `python-multipart` **0.0.32**; `python-jose` **3.5.0**; `cryptography` **50.0.0**; Pillow **12.3.0**.
  - Staging smoke after that deploy: health `env=staging` with CASA headers and no `Server`; ready `db=true`; login as platform admin 200; `/users/me` 200; Gmail + Calendar `authorize-url` still `accounts.google.com` with PKCE. Prod health still `server: uvicorn` (expected).

Store all reports in `velvet-elves-data/casa_al1_evidence/` (do not commit secrets, ZAP homes, or HTML scan dumps).

### Phase 3 — Remediate every CASA-mapped fail (the long pole)

- [x] Open a working list: CWE, where it is, fix or compensating control — `casa_al1_evidence/2026-08-21/PHASE3_WORKING_LIST.md`.
- [x] Split pytest/ruff out of the production image (`requirements-dev.txt`). **Staging live 21 Aug 2026.**
- [x] OAuth popup `postMessage` target `*` → `FRONTEND_URL` origin; SPA ignores other origins. **Staging live 21 Aug 2026.** Browser smoke: Gmail + Calendar popups connected; PDF preview worked. Maps autocomplete not tested (feature stopped).
- [x] Dockerfile non-root `USER appuser` (F266 / CWE-250). **Staging live** 21 Aug; **production image** after 22 Aug `main`→`prod` merge.
- [x] OAuth callback HTML XSS (CWE-79). **Staging live** 21 Aug (`velvet-elves-stage-backend:109`). Re-scan `a9d78f05-…` is 0 High.
- [x] CSP `img-src https:` — **compensating control written** 24 Aug 2026 (`casa_al1_evidence/m9/compensating_controls.md`). Do not drop `https:` without a closed host list.
- [x] `style-src 'unsafe-inline'` and Maps SRI — **compensating control written** 24 Aug 2026 (same file).
- [x] `pydantic-ai-slim` / `PyPDF2` / `ecdsa` leftover pip-audit — **documented, not remediating in this pass** (same file + `DEPS_SUMMARY.md`).
- [ ] Fix remaining items, deploy staging, re-scan — **not required for the accepted residuals**; re-scan only if we change CSP or bump those packages.
- [x] Residual CASA-mapped High/Critical closed or written (ZAP Low-confidence SQLi/path-traversal treated as false positives in DAST_SUMMARY + compensating_controls).
- [x] `localStorage` JWT: **compensating-control write-up** 24 Aug 2026 (cookie migration deferred unless a lab fails session-management without HttpOnly).
- [ ] Re-run isolation tests after any auth/session change — N/A until a cookie migration.

Typical first-scan pile besides CSP: cookie flags, information disclosure (Swagger, stack traces, `server: uvicorn`), mixed content, CORS, outdated JS libs.

### Phase 4 — M9 evidence folder (2–3 days, can overlap Phase 2)

One folder, honest against production. Short statements, not novels.

| ID | Artifact |
| --- | --- |
| M9a | Architecture — **draft** `m9/M9a_architecture.md` (ECS + CloudFront, not the old EC2 sketch) |
| M9b | Data-flow — **draft** `m9/M9b_data_flow.md` (hourly tick + after-sync watch renewal; disconnect is soft-deactivate) |
| M9c | Scope → Google API methods — **draft** `casa_al1_evidence/m9/M9c_scope_to_google_api.md` |
| M9d | Token storage — **draft** `m9/M9d_token_storage.md` |
| M9e | PII encryption — **draft** `m9/M9e_pii_encryption.md` |
| M9f | Tenant isolation + passing test names — **draft** `m9/M9f_tenant_isolation.md` |
| M9g | Logging — **draft** `m9/M9g_logging.md` |
| M9h | Scan process — **draft** `m9/M9h_scan_process.md` (Fluid CSV + official ZAP SPA/API unauth + API auth XML) |
| M9i | Incident response + retention/deletion — **draft** `m9/M9i_incident_response.md` |
| M9j | Subprocessors + AI no-training — **draft** `m9/M9j_subprocessors_ai.md` (Sharing PNG captured 24 Aug 2026) |

Also write a one-page **self-attestation draft** covering non-scannable items: access control, key rotation, backup encryption, employee access to mailboxes (there should be none except the connected user), deletion SLA (30 days). **Started:** `casa_al1_evidence/m9/self_attestation_draft.md`. Residuals: `casa_al1_evidence/m9/compensating_controls.md`.

### Phase 5 — Production smoke after hardening

- [x] Sign in and post-CSP smoke **22 Aug 2026** as dedicated testing account `crazyaidev20500519@gmail.com` (Gmail Test connection healthy; Calendar Add my closings; Ask AI; PDF preview). Do not use this account in the Trust and Safety reviewer guidelines.
- [x] Google reviewer account `algoforth33@gmail.com` — Gmail **healthy** and Google Calendar **connected as `algoforth33@gmail.com`** (verified 24 Aug 2026). Unverified-app warning still expected.
- [ ] Inbound match + Approve & send (optional; not required for CASA headers). Not run in the 22 Aug API smoke.
- [x] Calendar Add my closings — **PASSED** on the testing account after CSP.
- [ ] Disconnect still works (not re-tested 22 Aug; skip unless a reviewer needs a fresh consent screen).
- [x] CSP did not break Ask AI, PDF preview, or Google OAuth (user-verified after attaching `0e5af791-…`).

### Phase 6 — Gate: only then message Jake

Jake is asked to pay **only when all of these are true:**

1. Staging ZAP + Fluid Attacks CASA-mapped reports exist, with no open High/Critical on CASA CWEs (or each leftover has a written compensating control)
2. SPA CSP is live on production (`0e5af791-…`, 22 Aug 2026); API baseline security headers are live; Swagger is off. Re-smoke OAuth popups after CSP before treating this row as fully green.
3. Swagger is off in production
4. M9 folder exists and matches the code (including Gmail watch behavior that is actually scheduled)
5. Prod Gmail/Calendar smoke test passed after the hardening deploy
6. Recommended TAC plan is still AL1 Premium ($855), not AL2

If Phase 3 is still full of Highs, do not ask Jake. Fix them.

---

## Suggested calendar (Jan, no lab)

| When | Work |
| --- | --- |
| Day 1 | Phase 0 inventory + API headers / CSP / docs / debug fixes on a branch |
| Day 2 | Deploy staging; first ZAP + Fluid Attacks scan |
| Days 3–7 | Remediate, re-scan. Cookie/CSP decisions here |
| Days 5–8 | M9 folder in parallel once scan shape is known |
| Day 9 | Production hardening deploy + smoke |
| Day 10 | Gate check. If green, send Jake the spend ask |

If cookie migration is required, add several days. That is still cheaper than a failed paid AL1.

---

## What this prep is not

- Not AL2 (no AWS/root, no Supabase dashboard for a lab; AL2 is lab-executed testing of the live app and infrastructure)
- Not dropping `gmail.readonly`
- Not changing Cloud Console OAuth settings
- Not a SOC 2 project
- Not asking Jake until Phase 6 is green

---

## Official scan references

- [CASA specification (AL1 = verified self-assessment)](https://github.com/appdefensealliance/ASA-WG/blob/main/CASA/CASA%20Specification.md)
- [CASA AL1/Tier 2 overview](https://appdefensealliance.dev/casa/tier-2/tier2-overview)
- [Application scanning guide (Fluid Attacks / ZAP / CWE mapping)](https://appdefensealliance.dev/casa/tier-2/ast-guide)
- [Google security assessment](https://support.google.com/cloud/answer/13465431)
- [CASA kickoff](https://appdefensealliance.dev/casa/casa-start)
