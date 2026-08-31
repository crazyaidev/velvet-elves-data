# CASA AL1 — missing screenshot checklist

**Date:** 31 Aug 2026  
**Use:** tick items as you capture them, copy PNGs into `casa_al1_evidence/m9/tac_images/<id>/`, then update that row’s **Missing** line in `casa_al1_evidence/m9/CASA_PORTAL_PACK.md`.  
**Do not** upload this markdown to TAC. Portal accepts PNG/JPG/JPEG only, max **10** files per row.  
**Do not** check “I confirm…” or click Evidence **Submit** until all 48 rows are filled.

ADA source: [Web App Test Guide v1.0](https://github.com/appdefensealliance/ASA-WG/blob/v1.0/Web%20App%20Profile/Web%20App%20Test%20Guide.md).  
Companions: `casa_al1_evidence/m9/CASA_PORTAL_PACK.md`, `CASA/TAC_ESOF_PORTAL_GUIDE.md` §7.

Already on disk (do **not** recapture): SSL Labs A+ (4.1.1 / 4.1.2), Supabase Rate Limits and Email OTP (1.1.1 / 1.3.x), Qualys copies, Fluid CSV, ZAP XML under `casa_al1_evidence/2026-08-21/`.

---

## How to use this file

1. Work **by ID**, top to bottom in the index. **6.5.1 is first** — ADA names those two samples; the pack is incomplete without them.
2. Follow that ID’s **Capture** steps. If the frame does not match **Must show**, do not save it.
3. Save as PNG. Suggested names are below. Folder: `casa_al1_evidence/m9/tac_images/<id>/`.
4. Tick the checkbox here. Add the file to that row’s image table in `CASA_PORTAL_PACK.md` and drop it from **Missing**.
5. Each row already has write-up PNGs. Stay under **10** files total in that folder (counts are listed per ID).

---

## Global capture rules (every shot)

| Rule | Detail |
| --- | --- |
| Format | PNG (JPG/JPEG also accepted). No PDF, XML, CSV, or markdown in the row modal. |
| Filename | `CASA_<id-with-underscores>_<short-what>.png` e.g. `CASA_6_5_1_login_log.png`. |
| Who | **Owner** takes AWS, GCP, Stripe, Supabase, ZAP UI, Burp UI. Velvet Elves `app.` / `api.` staging may be captured by owner or agent. |
| Environment | Prefer **staging** (`app.stage.velvetelves.com`, `api.stage.velvetelves.com`) so customer PII is not in the lab pack. Label the host in the shot (address bar or CloudWatch log-group name). Production is only required where ADA is about production (certs, debug-off, Secrets Manager). |
| Account | QA platform admin `crazyaidev20500519@gmail.com`. Never `algoforth33@gmail.com`. Never complete Google OAuth. |
| Secrets | Crop or redact: passwords, JWTs, `Authorization`, Fernet/`ENCRYPTION_KEY`, Stripe secret keys, Supabase service keys, AWS secret **values**, GCP client **secrets**, full card numbers, CVV, bank accounts. Secret **names** (e.g. `/velvet-elves/prod/backend`) are fine. |
| Login page | Do **not** attach `/login` unless that screen is the evidence (not the case for any item below except 6.6.1 after-logout, which is already on disk). |
| GCP OAuth | **Read-only.** Do not change clients, redirects, scopes, or branding on `velvet-vles` / **538509143953**. |
| AWS | Account `388482955098`, region **us-east-2** unless Route 53 (global). Do not open secret **values**. |
| Internal banners | No “do not claim” / portal-process notes on the PNG the lab will see. |
| After capture | Eyeball for cut-off text and leaked tokens before you treat it as done. |

---

## Index

Priority: **P0** ADA-named samples · **P1** owner consoles ADA asks for · **P2** live Velvet Elves extras · **P3** optional (scanner UI / backups).

| Pri | ID | Missing shot | Who | Folder count now |
| --- | --- | --- | --- | ---: |
| P0 | [6.5.1](#651--do-not-log-credentials-or-payment-details) | Login log sample | Owner (CloudWatch) | 4 |
| P0 | [6.5.1](#651--do-not-log-credentials-or-payment-details) | Payment log sample | Owner (CloudWatch or Stripe) | 4 |
| P1 | [6.4.1](#641--subdomain-takeover) | Route 53 hosted zone | Owner | 4 |
| P1 | [6.7.1](#671--server-side-secrets) | Secrets Manager console | Owner | 3 |
| P1 | [6.7.1](#671--server-side-secrets) | CloudTrail secret-access | Owner | 3 |
| P1 | [6.1.1](#611--no-known-exploitable-components) | Production image scan | Owner | 5 |
| P1 | [6.2.1](#621--debug-off-in-production) | ECS env (`APP_DEBUG`) | Owner | 5 |
| P2 | [5.1.4](#514--template-injection) | Live SSTI probe | Staging API | 4 |
| P2 | [5.1.7](#517--xss) | Stored-XSS UI (escaped) | Staging SPA | 5 |
| P2 | [5.1.8](#518--sql-injection) | Authenticated SQLi replay | Staging API | 5 |
| P2 | [5.1.9](#519--os-command-injection) | Live OS-command probe | Staging API | 4 |
| P2 | [5.1.10](#5110--file-inclusion) | Authenticated path-replay | Staging API | 5 |
| P2 | [5.2.1](#521--malicious-file-uploads) | Upload-picker UI | Staging SPA | 5 |
| P2 | [6.6.1](#661--clear-browser-storage-on-logout) | DevTools Application panel | Staging SPA | 5 |
| P3 | [3.1.6](#316--directory-browsing-disabled) | S3 / CloudFront listing off | Owner — **done 31 Aug** (S3; CloudFront OAC optional leftover) | 6 |
| P3 | [3.2.1](#321--oauth-authorization-code--pkce) / [3.2.2](#322--oauth-redirect_uri-and-state) | GCP OAuth client (read-only) | Owner | 5 each |
| P3 | [4.1.2](#412--trusted-tls-certificates) | ACM console | Owner | 8 |
| P3 | [2.2.3](#223--stateless-tokens-expire-within-24-hours) | Supabase JWT expiry (optional) | Owner — **done 31 Aug** | 6 |
| P3 | [Scanner UI](#scanner-ui--zap--burp-all-dast-rows) | ZAP / Burp product UI | Owner | — |

---

## Scanner UI — ZAP / Burp (all DAST rows)

Official DAST is **ZAP** (staging XML: SPA `10f54abf`, API `a9d78f05`, auth `33afa2aa`). Burp was **not** run. Packed “zap” PNGs are Pillow of the ADA conf + `DAST_SUMMARY.md`, not the ZAP product.

**Skip unless TAC rejects a DAST row for missing scanner UI.** Recreating Burp just for a plugin-ID screenshot is not required for the current portal comments.

If TAC asks:

- **ZAP (prefer):** open the matching local XML in ZAP (`casa_al1_evidence/2026-08-21/dast/…`). Screenshot the Alerts tree for that plugin (empty or Low-confidence FP). Crop any `Authorization` header. Do not scan **production**. Do not use `algoforth33@gmail.com`.
- **Burp:** do not start a new authenticated crawl of production. If you already have a local Burp project, screenshot the issue list showing the ADA plugin ID **not** present.

Applies to: 2.3.1, 2.3.2, 2.3.4, 3.1.5, 3.1.6, 5.1.1–5.1.10, 6.2.1, 6.3.1.

- [ ] ZAP UI (only if TAC asks)
- [ ] Burp UI (only if TAC asks)

---

## 2.2.3 — Stateless tokens expire within 24 hours

**Packed:** staging live `exp − iat` = **3600 s** (`CASA_2_2_3_exp.png`). Production Sessions **3600 s** (`CASA_2_2_3_supabase_jwt.png`). VelvetElves Stage Sessions **3600 s** (`CASA_2_2_3_supabase_jwt_stage.png`). All under 24 hours.

**Done 31 Aug 2026.** Do not recapture supabase.com. Do not treat Inactivity timeout 0 / Time-box 0 as this row. The Stage project's **PRODUCTION** badge is the primary-branch label, not `app.velvetelves.com`.

- [x] Production Supabase Authentication → Sessions PNG (`CASA_2_2_3_supabase_jwt.png`)
- [x] VelvetElves Stage Authentication → Sessions PNG (`CASA_2_2_3_supabase_jwt_stage.png`)

---

## 3.1.6 — Directory browsing disabled

**Packed:** staging SPA prefixes return the HTML shell; API prefixes return JSON 404; production S3 **Block all public access On** (`CASA_3_1_6_s3_block.png`).

**Done 31 Aug 2026** for the required S3 Permissions shot. Do not recapture the AWS console. Do not claim missing `/assets/*` is 403 (it is the SPA shell). Optional leftover: CloudFront OAC for `app.velvetelves.com` — skip unless TAC asks.

- [x] S3 listing-off PNG (`CASA_3_1_6_s3_block.png`)
- [ ] CloudFront OAC PNG (optional)

---

## 3.2.1 — OAuth authorization code + PKCE

**Already packed:** staging `POST /users/oauth/google/start` returns `s256`; flow not completed.

**Still missing (optional):** Google Cloud Console client showing Web + redirect URIs (not Implicit).

### Capture (read-only)

1. Google Cloud → project **velvet-vles** (538509143953) → **APIs & Services** → **Credentials**.
2. Open the **Web client** used for Velvet Elves sign-in (do **not** edit).
3. Screenshot: application type **Web application**, **Authorized redirect URIs** (Supabase / Velvet Elves callbacks). Crop **Client secret**.

**Must show:** Web client, redirect URIs.  
**Must not show:** client secret, other projects’ clients, any edit confirmation.  
**Save as:** `tac_images/3.2.1/CASA_3_2_1_gcp_client.png`  
Copy the **same** file into `tac_images/3.2.2/` as `CASA_3_2_2_gcp_client.png` if redirect URIs are visible (covers 3.2.2).  
**Who:** owner. Do **not** change OAuth. Do **not** complete consent. Do **not** attach `/login`.

- [ ] GCP OAuth client PNG (also ticks 3.2.2)

---

## 3.2.2 — OAuth redirect_uri and state

Same GCP shot as 3.2.1 if redirect URIs are in frame. No extra Google accounts screenshot.

- [ ] GCP redirect-URI PNG (or reuse 3.2.1)

---

## 4.1.2 — Trusted TLS certificates

**Already packed:** Qualys A+ + live ACM peer cert (`CASA_4_1_2_cert.png`).

**Still missing (optional):** ACM console.

### Capture

1. AWS **us-east-2** (API ALB) and/or **us-east-1** (CloudFront certs often live in us-east-1) → **Certificate Manager**.
2. Open the cert whose SAN includes `app.velvetelves.com` and/or `api.prod.velvetelves.com`.
3. Screenshot: **Amazon issued**, status **Issued**, domain names, not expired. No private key (ACM never shows one).

**Must show:** Amazon-issued, matching names, valid.  
**Must not show:** unrelated account certs with customer apps if you can crop them.  
**Save as:** `tac_images/4.1.2/CASA_4_1_2_acm.png`  
Row already has **8** files; this is 9. Stay under 10.

- [ ] ACM console PNG

---

## 5.1.4 — Template injection

**Already packed:** code (`mapping.get`, not Jinja). No live SSTI PNG.

### Capture

1. Staging, no auth needed: `GET https://api.stage.velvetelves.com/api/v1/health?q={{7*7}}` (or any public JSON query the API ignores).
2. Screenshot the response: **200** JSON health (or 422), body is **not** `49`, and the raw `{{7*7}}` is not evaluated as a template.

**Must show:** request URL (or query), status, JSON body with no template evaluation.  
**Must not show:** Bearer tokens. This is not an exploit write-up — one ignored query is enough.  
**Save as:** `tac_images/5.1.4/CASA_5_1_4_probe.png`  
**Who:** owner or agent on Velvet Elves staging only.

- [ ] Live SSTI-ignored probe PNG

---

## 5.1.7 — XSS

**Already packed:** Gmail callback does not echo a script tag (`CASA_5_1_7_callback.png`). CSP Mediums remain.

**Still missing:** authenticated **stored** XSS UI (string stored, then rendered as text).

### Capture

1. Staging, QA user, open a deal → **Contacts** (or a task title).
2. Set a display name to a script-looking string (type the characters of a script tag). Save.
3. Screenshot the list/detail: the string appears as **text**, not as a running script (no alert dialog).
4. Revert the name immediately.

**Must show:** staging URL, the stored string visible as text.  
**Must not show:** JWT in DevTools, other tenants’ data, `/login`. Do not use production.  
**Save as:** `tac_images/5.1.7/CASA_5_1_7_stored.png`

- [ ] Stored-XSS escaped UI PNG
- [ ] Name reverted on staging

---

## 5.1.8 — SQL injection

**Already packed:** unsigned `page_size='(` → **401**. Auth ZAP Highs are Low-confidence FPs (plugin **40018**, 28 URLs).

**Still missing:** authenticated replay of those ZAP URIs (status only — not a new attack).

### Capture

1. Open `casa_al1_evidence/2026-08-21/dast/api-auth-33afa2aa/extracted/zap-casa-api-auth.xml`. Filter alerts with plugin id **40018**.
2. Log in to staging as QA (keep the token in a local env var, never in a PNG).
3. Replay **each listed URI** with `Authorization: Bearer` against `https://api.stage.velvetelves.com`. Expect **422** (Pydantic) or generic JSON **500** with message `An internal server error occurred.` — **no** SQLSTATE, no table names, no `syntax error at`.
4. Screenshot a **table or stacked list** of URI path + HTTP status + first ~80 chars of JSON (Pillow or DevTools). One collage is enough if all 28 fit; otherwise page1/page2.

**Must show:** authenticated (status is not 401), no SQL error text.  
**Must not show:** the Bearer value, password, raw DB errors.  
**Save as:** `tac_images/5.1.8/CASA_5_1_8_auth_replay.png`  
Do not scan production. Do not write a new exploit.

- [ ] Authenticated 40018 replay PNG (all 28 URIs)

---

## 5.1.9 — OS command injection

**Already packed:** grep — no `subprocess` / `os.system` / `shell=True` in `app/`.

**Still missing:** live probe PNG (same style as 5.1.3 health).

### Capture

1. Staging: `GET https://api.stage.velvetelves.com/api/v1/health` with an extra query that looks like a command fragment (health ignores extra query).
2. Screenshot **200** `{"status":"ok",...}` — not command stdout.

**Must show:** URL, 200 JSON health.  
**Must not show:** tokens. Do not run commands on the server.  
**Save as:** `tac_images/5.1.9/CASA_5_1_9_probe.png`

- [ ] Live OS-command-ignored probe PNG

---

## 5.1.10 — File inclusion

**Already packed:** `GET /ads/../etc/passwd/click` → **404**. Auth ZAP path-traversal Highs (plugin **6**, four alerts) were path segments `team` / `templates` / `settings`.

**Still missing:** authenticated replay of those four ZAP URIs.

### Capture

1. Same XML as 5.1.8. Filter plugin id **6**.
2. Replay each URI with a staging Bearer. Documented example already: `GET /api/v1/dashboard/team?view=team` → **200** normal JSON (not `/etc/passwd`).
3. Screenshot path + status + JSON prefix for all four.

**Must show:** 200 JSON or 404 JSON, not file contents.  
**Must not show:** Bearer, local file dumps.  
**Save as:** `tac_images/5.1.10/CASA_5_1_10_auth_replay.png`

- [ ] Authenticated plugin-6 replay PNG (all 4 URIs)

---

## 5.2.1 — Malicious file uploads

**Already packed:** MIME allowlist code; unsigned **401**; authenticated `probe.exe` **415** (`CASA_5_2_1_415.png`).

**Still missing:** SPA upload picker showing the deny (or the accept list).

### Capture

1. Staging → a deal workspace → Compliance / **Add document** (`AddDocumentModal` dropzone).
2. Either: screenshot the file input / helper text that lists allowed types (PDF, DOCX, images, TXT), **or** choose a `.exe` / `.html` and screenshot the in-app error (415 / not supported).
3. Do **not** upload malware.

**Must show:** staging deal URL, allowlist or reject message.  
**Must not show:** other clients’ documents, tokens.  
**Save as:** `tac_images/5.2.1/CASA_5_2_1_picker.png`

- [ ] Upload-picker UI PNG

---

## 6.1.1 — No known exploitable components

**Already packed:** `npm audit --omit=dev` 0 vulns; `pip-audit` `ecdsa` 0.19.2 CVSS 7.4, no fix.

**Still missing:** scan of the **running production image**, not the laptop lockfile.

### Capture

1. AWS **us-east-2** → **ECR** → `velvet-elves/backend` → image tagged `prod-latest` or the digest currently on ECS `velvet-elves-prod` / `velvet-elves-prod-backend`.
2. Run **ECR Enhanced Scanning** / Inspector (or `docker scout` / Grype against that digest) and screenshot the summary: image URI + High/Critical count.
3. If `ecdsa` still appears, the lockfile justification in the existing pip PNG still applies — do not hide it.

**Must show:** production image tag or digest, scanner name, date.  
**Must not show:** registry auth tokens.  
**Save as:** `tac_images/6.1.1/CASA_6_1_1_ecr.png`  
**Who:** owner. OWASP dependency-check is optional if ECR/Inspector is in frame.

- [ ] Production image scan PNG
- [ ] (optional) Confirm ECS task uses that same digest

---

## 6.2.1 — Debug off in production

**Already packed:** prod `/api/docs` `/redoc` `/openapi.json` **404**; staging docs **200**.

**Still missing:** task definition / env showing `APP_DEBUG=false`.

### Capture

1. AWS **us-east-2** → **ECS** → cluster `velvet-elves-prod` → service `velvet-elves-prod-backend` → **Task definition**.
2. Container **api** → Environment. Screenshot `APP_ENV=production` and `APP_DEBUG=false` (plain env, not a secret value).
3. Crop any other env that is a URL with tokens. Secrets stay as `ValueFrom` ARNs only.

**Must show:** `APP_DEBUG=false`, `APP_ENV=production`.  
**Must not show:** `ENCRYPTION_KEY`, JWT secret, database URLs with passwords.  
**Save as:** `tac_images/6.2.1/CASA_6_2_1_ecs_env.png`

- [ ] ECS env PNG

---

## 6.4.1 — Subdomain takeover

**Already packed:** live DNS A/AAAA for app / api / help / apex → CloudFront or ALB.

**Still missing:** Route 53 hosted-zone console (ADA: names you control).

### Capture

1. AWS → **Route 53** → Hosted zones → `velvetelves.com` (known zone id **`Z04016973TWW2D0EKIMFB`** — confirm it is still the one in use).
2. Screenshot the **record list**: `app`, `app.stage`, `api.prod`, `api.stage`, `help`, apex. Each alias/A should point at CloudFront or the ALB — not a deleted Heroku/GitHub/S3 website.
3. Optional second PNG: filter **CNAME** only and confirm none point at deprovisioned SaaS.

**Must show:** hosted zone name, those hostnames, target (CloudFront/ALB).  
**Must not show:** registrar login, unrelated zones.  
**Save as:** `tac_images/6.4.1/CASA_6_4_1_route53.png`  
**Who:** owner.

- [ ] Route 53 hosted-zone PNG

---

## 6.5.1 — Do not log credentials or payment details

**ADA AL1 requires all three:** written description (already packed) **+ login log sample + payment log sample**. This row is **not** complete until both samples exist.

Log group: `/ecs/velvet-elves/stage/backend` (prefer) or `/ecs/velvet-elves/prod/backend`. Region **us-east-2**.

### A. Login log

1. Sign in once on **staging** as the QA user.
2. CloudWatch → Logs → that log group → **Logs Insights** (or Live Tail) around that timestamp.
3. Find the request (`request_id`, path `/api/v1/users/login` or equivalent). Screenshot a window that shows the event **without** a `password` field and **without** `Authorization`.
4. If the logger never writes login bodies, screenshot that window anyway — empty of secrets is the proof. Mask full emails (`ab***@domain`) if they appear.

**Must show:** CloudWatch log group name, timestamp, login-related line, no password.  
**Must not show:** password, JWT, MFA secret.  
**Save as:** `tac_images/6.5.1/CASA_6_5_1_login_log.png`

- [ ] Login log sample PNG

### B. Payment log

1. Prefer a **staging** Stripe test checkout (test mode). Production: only a QA invoice, never a real client PAN.
2. Either:
   - CloudWatch around the checkout / webhook (`/api/v1/.../stripe` or billing path): screenshot Stripe `cs_` / `pi_` / `in_` ids, **no** PAN/CVV; or
   - Stripe Dashboard (test) → that Payment → screenshot amount + Stripe id, **no** full card number (last4 is OK).
3. We store Stripe ids, not PAN. The shot must not contradict that.

**Must show:** payment event with Stripe id or “checkout session”, no PAN/CVV.  
**Must not show:** full card, bank account, webhook signing secret.  
**Save as:** `tac_images/6.5.1/CASA_6_5_1_payment_log.png`

- [ ] Payment log sample PNG

After both exist: edit `CASA_PORTAL_PACK.md` 6.5.1 **Missing** and the portal comment so they no longer say the samples were not obtained.

---

## 6.6.1 — Clear browser storage on logout

**Already packed:** Playwright key presence — `velvet_elves_token` / `velvet_elves_refresh_token` true then false; `velvet_elves_return_location` remains; `/login` after Log Out.

**Still missing:** Chrome **DevTools → Application** panel (what ADA reviewers often expect).

### Capture

1. Staging, Chrome, QA login. F12 → **Application** → **Local Storage** → `https://app.stage.velvetelves.com`.
2. Screenshot **before** Log Out: keys `velvet_elves_token` and `velvet_elves_refresh_token` present. **Blur or crop the Values column** (JWTs).
3. **Log Out**. Same panel: those two keys gone. `velvet_elves_return_location` may remain (path only — that is honest).
4. Address bar should be `/login`.

**Must show:** Application localStorage, key **names**, Values column redacted.  
**Must not show:** JWT strings, password field filled.  
**Save as:** `tac_images/6.6.1/CASA_6_6_1_devtools.png` (before+after can be one stacked PNG or `_devtools_before` / `_devtools_after`). Row is at 5 files; two more stay under 10.

- [ ] DevTools Application PNG (values redacted)

---

## 6.7.1 — Server-side secrets

**Already packed:** write-up + code comments (no secret values). Disconnect is **soft deactivate** (ciphertext remains).

**Still missing:** Secrets Manager console + CloudTrail access log.

### A. Secrets Manager

1. AWS **us-east-2** → **Secrets Manager** → `/velvet-elves/prod/backend` (staging: `/velvet-elves/stage/backend`).
2. Screenshot the **secret list or details header**: name, rotation if any, KMS key alias. Stay on the overview — **do not** click Retrieve secret value for the PNG.
3. Optional: ECS task definition showing `ENCRYPTION_KEY` as `valueFrom` that ARN (name only).

**Must show:** secret **name** `/velvet-elves/prod/backend`.  
**Must not show:** plaintext `ENCRYPTION_KEY`, JWT secret, provider keys.  
**Save as:** `tac_images/6.7.1/CASA_6_7_1_sm.png`

- [ ] Secrets Manager console PNG (no values)

### B. CloudTrail

1. AWS → **CloudTrail** → Event history. Filter Event source `secretsmanager.amazonaws.com`, event `GetSecretValue` (or `DescribeSecret`).
2. Screenshot one recent event: time, user/role, secret **ARN or name**, region. Open the event JSON only if the value is not in it (CloudTrail should not contain the secret plaintext).

**Must show:** Secrets Manager API call, resource name.  
**Must not show:** secret string in response elements.  
**Save as:** `tac_images/6.7.1/CASA_6_7_1_cloudtrail.png`

- [ ] CloudTrail secret-access PNG

---

## After you finish an ID

1. File is in `tac_images/<id>/` and under 10 files.
2. Checkbox ticked above.
3. `CASA_PORTAL_PACK.md` image table + **Missing** + portal comment updated (and `CASA/TAC_ESOF_PORTAL_GUIDE.md` §7 if the one-line comment changed).
4. Commit/push only `velvet-elves-data` `main` when you want the pack on git (`docs(casa): add <id> <what> screenshot`).
