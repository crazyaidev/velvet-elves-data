# TAC ESOF portal — CASA AL1 operating guide (Jan)

**Date:** 26 August 2026  
**Portal:** https://casa.tacsecurity.com/  
**Official TAC PDF:** `CASA/ESOF_AppSec_ADA_CASA_User_Guide_Ver.2.0.pdf` (12 pages, 2026)  
**ADA test cases:** [Web App Test Guide v1.0](https://github.com/appdefensealliance/ASA-WG/blob/v1.0/Web%20App%20Profile/Web%20App%20Test%20Guide.md) (this is what TAC **View Details** quotes). AL1 = written evidence + screenshots; AL2 tests are not ours.  
**Login:** `jan@velvetelves.com` (alternate email on Jake’s account; same password as Jake’s TAC login)  
**Google due date:** 18 November 2026  
**GCP:** `velvet-vles` / **538509143953**  
**Companion:** `GOOGLE_CASA_AL1_NEXT_STEPS.md`, `casa_al1_evidence/m9/CASA_PORTAL_PACK.md` (row comments + image descriptions), `casa_al1_evidence/m9/`

This is the lab portal for **ADA-CASA AL1 only**. It is not SOC 2.  
Support: `casasupport@tacsecurity.com`  
Account/login: `account_esof@tacsecurity.co.in`

---

## 0. What the official PDF actually says

Verified against `ESOF_AppSec_ADA_CASA_User_Guide_Ver.2.0.pdf`. TAC’s own 17-step summary (pages 11 and 2–10):

1. Visit the CASA platform  
2. Select a subscription plan  
3. Complete payment (coupon **before** Pay)  
4. Create the CASA account  
5. Verify with OTP  
6. Complete LOV details  
7. **Schedule and run a security scan** (PDF says sidebar **Scans**. The live portal has **no Scans item**. Use **CASA Assessment**.)  
8. **Upload required evidence** (after the scan finishes)  
9. Tester **and** Manager review evidence  
10. Download the Vulnerability Report from **Scans** / Scan List  
11. Patch identified vulnerabilities (prioritize Critical and High)  
12. Rescan until a **clean** report  
13. Enterprise **AL2 only:** TAC’s testers run the assessment (skip this)  
14. Email `casasupport@tacsecurity.com` after a clean scan  
15. TAC reviews and **TAC submits the LOV to Google**  
16. Google sends an LOV reverification email in **5–6 business days**  
17. Google approves; CASA is complete  

**Already done (PDF steps 1–7):** Jake paid, account exists, OTP login works, LOV is **Completed**. Assessment **Velvet Elves** / Web submitted 26 Aug with FILE zip `VelvetElves_CASA_AL1_scans.zip`. List status: **In Progress**.

**You are at PDF step 8:** open the row (eye icon) and upload remaining evidence when that screen appears. Do **not** submit a second assessment.

**AL1 vs AL2 (PDF page 9):** Basic, Premium, and other AL1 plans are **self-scan in the portal**. TAC’s testers do **not** pentest the app unless you bought Enterprise AL2. That matches ADA: you scan, they review.

**SOC 2 Add-on** is listed as optional on page 2 of the PDF. Ignore it. Google did not require it.

The PDF never mentions the 48-check questionnaire by name. The portal still has **Upload Evidence** after the scan. Keep the M9 packet ready for that step, plus Fluid CSV / ZAP XML as supporting files.

---

## 1. What the 25 Aug screenshots show

You are in. LOV step 1 is done. The scan itself is **not** started yet.

| What you see | PDF name | Meaning |
| --- | --- | --- |
| Profile still says **JAKE STILES** | (not in PDF) | Expected. Alternate email shares Jake’s account. |
| Step 1 Submit LOV Details = **Completed** | Complete LOV details | Form + two screenshots were accepted. |
| Step 2 Submit CASA Assessment = **Pending** | Create a New Scan | Next click. |
| Step 3 Assessment Review | Tester/Manager review | Locked until a scan + evidence exist. |
| Step 4 Revalidation | Patch + rescan | After TAC rejects findings or evidence. |
| Step 5 Report Generate | Vulnerability Report | After evidence is approved. |
| Step 6 LOV Submitted | TAC submits LOV to Google | Last portal step. You still reply-all on Google’s thread. |
| CASA Assessment table = **No Results Found** | Scan List empty | Nothing created. |
| Red **SUBMIT CASA ASSESSMENT** | Submit the scan request | Opens/creates the scan form. **Not** “I am done with all evidence.” Do not mash it without filling Target URL / Environment first. |
| Policy list | (not in the CASA PDF) | TAC templates. Not our live policies. Do not upload them as evidence unless TAC asks. |
| Sidebar **SOC 2 / AppSec / SCA / IAST / CRQ** | Optional add-ons | Ignore. |

Application Details that already look right: GCP **538509143953**, Application Type **Web**, Application URL `https://app.velvetelves.com/`.

Still wrong on the recorded LOV, if Edit is still open: email `jake@velvetelves.com.com` (extra `.com`). Fix to `jake@velvetelves.com` if the Edit button still works. Not a reason to redo LOV unless TAC later rejects mail.

---

## 2. Hard rules

1. Do **not** change Google Cloud Console OAuth (scopes, branding, clients, redirect URIs) on `velvet-vles`.
2. Do **not** schedule or buy **SOC 2 / Socify**. The PDF lists it as optional. Google did not require it.
3. Do **not** authenticated-scan **production** with `algoforth33@gmail.com`. That is the Google reviewer account.
4. Do **not** give TAC AWS root, Secrets Manager, or the production database. AL1 is app assessment, not AL2 infrastructure.
5. Do **not** paste API keys, JWTs, or Fernet keys into the portal or into tickets.
6. One CASA license = this one web app (SPA + API together). Do not buy a second license for the API.
7. Do **not** follow the PDF’s AL2 path (TAC testers schedule and run the assessment).
8. Do **not** capture screenshots of other companies’ products (Supabase dashboard or docs, SSL Labs, AWS, Google Cloud, etc.). Those shots must be taken by the owner. If a vendor screenshot is needed, the agent asks first and gives capture guidelines. Agent screenshots are limited to Velvet Elves (`app.` / `api.` / write-up PNGs of our own code).

---

## 3. Portal map (PDF words vs what the UI actually says)

The PDF’s “Navigate to Scans” screen **does not exist** in this portal. **CASA Assessment** is that page. **SCA** in the sidebar is Software Composition Analysis (a different product). Do not open it.

| PDF says | Portal control | Use it for |
| --- | --- | --- |
| CASA Dashboard | Dashboard | Status only. |
| Navigate to **Scans** / Create a New Scan | **CASA Assessment** (highlighted). Form title: **Submit CASA Assessment** | You are here (PDF step 7). |
| Application Name, Target URL, Environment, Scan Frequency, Scan Type, Run immediately | Live form is different. See Section 4. | Fill this form, then the red Submit on the form. |
| Evidence section | **Upload Evidence** after the scan finishes | PDF step 8. M9 + scan files. |
| Uploaded Evidence (if rejected) | Same evidence area | Fix and re-upload. |
| Scans / Scan List | CASA Assessment table | Download the Vulnerability Report. |
| APPLICATION DETAILS | APPLICATION DETAILS | Recheck LOV fields. Edit email typo if possible. |
| Tickets / support email | Tickets + `casasupport@tacsecurity.com` | Ask before a production crawl. |
| Settings | Profile menu → User Guide / Change Password | The PDF you just opened is this User Guide. |
| SOC 2, CRQ, Shield, AppSec, SCA, IAST | Sidebar | Leave alone. |

---

## 4. Next click: fill Submit CASA Assessment (you are already here)

Until a row appears in **CASA Assessment**, steps 2–6 stay locked.

The live form (26 Aug screenshot) does **not** match the PDF field list. There is no Target URL / Environment / Scan Frequency on this screen. Fill what is on the form:

| Field on screen | What to enter |
| --- | --- |
| Application Name | `Velvet Elves` (placeholder says “Enter Scan Name”) |
| Project ID | The Velvet Elves / Asset 1 project in the dropdown (from LOV) |
| Choose Asset Type | **Web** (same as LOV). Open this; it may be radio buttons that appear after Project ID. |
| Scan Source | **FILE** (confirmed 26 Aug). Do **not** pick **URL** unless TAC later rejects the upload and requires their crawler. |
| GCP No. | **538509143953** |
| Application Version | `V1.0` (max 10 characters) |
| Comment | See the paste block below. |
| Authentication Details | Leave **unchecked**. FILE is an upload, not a live login crawl. |

After **FILE**, the portal says **Only zip file is allowed**. Upload this file (already built, ~253 KB, gitignored):

`casa_al1_evidence/2026-08-21/tac_upload/VelvetElves_CASA_AL1_scans.zip`

Inside:

| Zip member | What it is |
| --- | --- |
| `INDEX.txt` | One-page list of builds and results |
| `01-sast-fluid-attacks.csv` | Fluid SAST keep (`5999aab9-…`), 0 High/Critical/Medium |
| `02-dast-spa-zap.xml` | ZAP SPA keep (`10f54abf-…`) |
| `03-dast-api-unauth-zap.xml` | ZAP API unauth keep (`a9d78f05-…`) |
| `04-dast-api-auth-zap.xml` | ZAP API auth keep (`33afa2aa-…`) |

Do **not** zip discarded builds `c13e9c57`, `2fe02778`, `fb752d1f`. M9 architecture / IR / AI screenshots stay for **Upload Evidence**, not this scan zip.

Comment to paste (the portal blocks `.` `@` and likely other punctuation; letters, numbers, and spaces only):

```
ADA CASA AL1 self scan for Velvet Elves web Zip has Fluid Attacks SAST CSV and OWASP ZAP XML for SPA and API from staging Please do not crawl production Contact Jan at velvetelves com
```

Do not click the form’s red **Submit** until Project ID, Asset Type, **FILE**, GCP No., and the scan file are filled.

**26 Aug pre-submit check (Screenshot_55):** Application Name Velvet Elves, Asset **Web**, Scan Source **FILE**, zip `VelvetElves_CASA_AL1_scans.zip`, GCP **538509143953**, version V1.0, comment is the letters-only staging note. **OK to click the form Submit.**

If TAC later rejects FILE and demands **URL**, ticket them first and use staging, not production:

| Field | Value |
| --- | --- |
| Application name | Velvet Elves |
| Application URL | `https://app.stage.velvetelves.com` |
| API (if asked) | `https://api.stage.velvetelves.com` |
| Application type | Web |
| Login | Staging platform-admin `crazyaidev20500519@gmail.com` (password is in Jan’s password store, not in this file) |
| Do not scan | Send, Disconnect, Approve & send, DELETE, register, password reset, webhooks, `/api/v1/internal/schedules/tick` |

Staging is **Autopilot**. Tell TAC not to click send. If they cannot restrict crawls, do not give them a mailbox that can send.

If they refuse staging and demand production: URL `https://app.velvetelves.com`, still **not** `algoforth33`. Use the dedicated testing account only after Gmail is reconnected on that account, and keep posture from auto-sending. Email TAC first.

---

## 5. After the scan completes (PDF steps 8–12)

Do **not** expect the red button alone to finish CASA.

1. Open **Evidence** and upload the packet in Section 6.
2. Submit evidence for review. PDF: assigned tester reviews; **Tester and Manager** both review.
3. If rejected: read comments, fix, re-upload from **Uploaded Evidence**, submit again.
4. If approved: download the Vulnerability Report from the Scan List.
5. Patch **Critical and High** first. PDF then wants rescans until a **clean** report.
6. Email `casasupport@tacsecurity.com` when the report is clean. TAC submits the LOV to Google. You do not email the LOV to Google yourself.

A “clean” TAC report is **their** gate. Google CASA still allows documented compensating controls. If their scanner repeats our known CSP Mediums, attach `compensating_controls.md` in evidence and ask whether those can stay as residuals instead of blocking the LOV.

---

## 6. Evidence to upload (already in our packet)

ADA wants **CSV or XML, not both**, for the scanner outputs. Keep that rule.

| What TAC will ask | File / place | Notes |
| --- | --- | --- |
| SAST (CASA-mapped) | Fluid Attacks CSV from CodeBuild `velvet-elves-casa-fluid-sast:5999aab9-…` | **0 High / 0 Critical / 0 Medium**, 3 Low. Write-up: `casa_al1_evidence/2026-08-21/SAST_SUMMARY.md`. Pull the CSV from the S3 artifact if the portal needs the raw file. |
| DAST web | ZAP XML `10f54abf-…` (`zap-casa-config.conf`) | Staging SPA. **0 High**, 3 Medium (CSP). `DAST_SUMMARY.md`. |
| DAST API unauth | ZAP XML `a9d78f05-…` | After XSS fix. **0 High**. Do **not** upload `c13e9c57-…` or `2fe02778-…`. |
| DAST API auth | ZAP XML `33afa2aa-…` | Staging platform-admin. Send/DELETE excluded. Two Low-confidence Highs are false positives. |
| Architecture, data flow, tokens, isolation, logging, IR, subprocessors | `casa_al1_evidence/m9/M9a`–`M9j` | Honest drafts. Production CSP / headers / Swagger-off are live. |
| AI no-training | `casa_al1_evidence/m9/openai-data-controls.png` | Velvetelves org, Sharing tab, all three Disabled. Not ZDR. |
| Residuals / compensating | `casa_al1_evidence/m9/compensating_controls.md` | CSP Mediums, callback CSP, `localStorage` JWT, leftover pip-audit, Fluid Lows. |
| Self-attestation | `casa_al1_evidence/m9/self_attestation_draft.md` | Non-scannable items. |
| Live privacy / deletion | `https://velvetelves.com/privacy`, `https://velvetelves.com/data-deletion` | Use these URLs. Do not substitute TAC Policy downloads. |
| Test account for Google’s own review | `algoforth33@gmail.com` on production | Gmail healthy, Calendar connected as that address, posture **manual**. For reviewers, not for TAC DAST. |

If the portal only allows one DAST file, ask TAC which XML they want, or zip with a one-page index (SPA / API unauth / API auth) and the three build IDs.

---

## 7. The 48 checks (Evidence page — 27 Aug screenshots)

This is the official ADA CASA web AL1 list (Authentication → Configuration). Rows 1–48. Tester Comment / Remediation / Status stay empty until TAC reviews.

**Do not** check “I confirm that all checklist items have been reviewed and verified” and **do not** click Evidence **Submit** until every required row has a comment and an upload.

Comments may include English letters and symbols (punctuation is allowed). Keep claims honest. Do not paste API keys, JWTs, or secrets. Uploads carry the real filenames and URLs. Canonical paste list: `casa_al1_evidence/m9/CASA_PORTAL_PACK.md`.

Click **View Details** on row 1 (`1.1.1`) first. Per-row **Upload Evidences** accepts **PNG, JPG, JPEG only** (max 10 images). Do **not** upload `.md` or `.zip` there. Keep markdown in `casa_al1_evidence/m9/` as our source; upload PNGs from `casa_al1_evidence/m9/tac_images/<check-id>/` (one folder per row).

Honest gaps the lab may fail or ask to compensate:

| ID | Do not over-claim |
| --- | --- |
| 2.3.1 / 2.3.2 | Session is SPA `localStorage` JWT, not cookies |
| 3.3.1 | TOTP MFA on platform console (packed 31 Aug 2026). Do not attach enroll QR shots. |
| 6.1.1 | pip-audit residuals after 27 Aug upgrades: `ecdsa` (no fix exists), `pytest` (dev-only) |
| 6.7.1 / Disconnect | Encrypted Google tokens remain on the row until wipe |
| 5.1.7 | CSP Medium residuals (compensating) |
| 5.1.8 / 5.1.10 | Auth-API ZAP Highs are false positives — say so |

Comments (punctuation allowed) and files:

| # | ID | Upload | Comment to paste |
| --- | --- | --- | --- |
| 1 | 1.1.1 brute force | `tac_images/1.1.1/` — `CASA_1_1_1_page1.png`, `page2.png`, `login_429.png`, `register_429.png`, `password_rules.png`, `supabase_rate_limits.png` | Login is rate-limited to 10 requests/minute/IP and locked after 20 failed attempts per account per hour. Passwords require min 8 characters, a digit, and reject common passwords (static denylist, not a live HIBP API). Register is rate-limited to 5/minute. TOTP MFA is enforced for platform admins (not all users). CAPTCHA is not used; ADA 1.1.1 is met via options 2.1 and 2.4. Supabase vendor limits apply on top (30 sign-in requests / 5 min / IP). |
| 2 | 1.1.2 initial passwords expire | `tac_images/1.1.2/` — `CASA_1_1_2_page1.png`, `page2.png`, `invite_expired.png`, `forgot_password.png`, `reset_expired.png` | Velvet Elves does not issue system-generated initial passwords. Users choose their own password on register, invite accept, and password reset. Invite activation tokens are 32-character hex (uuid4), single-use, and cannot become the account password. Used, revoked, or unknown tokens return 410/404. Invite links currently expire after 72 hours (ADA 1.1.2 recommends 24h and caps at 48h; we do not claim the 48h cap). Password reset uses a one-time Supabase recovery link; a missing/expired link cannot set a password. |
| 3 | 1.1.3 password storage | `tac_images/1.1.3/` — `CASA_1_1_3_page1.png`, `page2.png`, `users_schema.png`, `supabase_docs.png` | User passwords are not stored in Velvet Elves tables. Login and register call Supabase Auth (GoTrue). GoTrue stores a salted bcrypt hash in auth.users.encrypted_password (hash, not reversible encryption; see supabase.com/docs/guides/auth/password-security). public.users is a profile row with no password column. We do not operate a custom password hasher. Google OAuth tokens are Fernet-encrypted separately and are not login passwords. |
| 4 | 1.2.1 no default credentials | `tac_images/1.2.1/` — `CASA_1_2_1_page1.png`, `page2.png`, `login_empty.png`, `register.png`, `default_rejected.png` | Velvet Elves does not ship default accounts or predefined username/password pairs on public interfaces (no Admin/Admin). Accounts are created only by self-register or invite accept; the user always chooses the password. Login and register forms start empty. A classic default pair is rejected. Google Sign-in is the user's Google account via OAuth, not a shared Velvet Elves password. SQL seeds do not insert passwords. |
| 5 | 1.3.1 OOB verifier expiry | `tac_images/1.3.1/` — `CASA_1_3_1_page1.png`, `page2.png`, `forgot_password.png`, `expires_1h.png`, `reset_expired.png`, `supabase_email_otp.png` | Password reset uses a Supabase Auth recovery email. Auth Email OTP expiration is 3600 seconds (1 hour), matching the app copy. Opening /reset-password without a valid token shows Invalid or expired link and cannot set a password. TOTP MFA codes use a 30-second time step, under ADA's 30-minute MFA verifier limit. We do not send SMS OTPs. |
| 6 | 1.3.2 OOB verifier single use | `tac_images/1.3.2/` — `CASA_1_3_2_page1.png`, `page2.png`, `reset_expired.png`, `confirm_rejected.png` | Password reset recovery links are issued by Supabase Auth and cannot be reused. Confirm requires a valid recovery token from the email. A missing, used, or invalid token returns Invalid or expired reset token and cannot set a password. The reset page with no token shows Invalid or expired link and asks the user to request a new one. TOTP MFA is verified through a GoTrue challenge; codes rotate every 30 seconds. We do not send SMS OTPs. |
| 7 | 1.3.3 OOB verifier securely random | `tac_images/1.3.3/` — `CASA_1_3_3_page1.png`, `page2.png`, `code.png`, `forgot_password.png`, `expires_1h.png`, `reset_expired.png`, `supabase_email_otp.png` | Password-reset recovery links are issued by Supabase Auth. The app does not generate or store a reset code. Email OTP length is 8 digits. Recovery uses a hashed vendor token in the email link, not a sequential number. Invite tokens the app mints are 32-character uuid4 hex. TOTP secrets are generated by GoTrue. We do not send SMS OTPs. |
| 8 | 1.3.4 OOB brute-force resistance | `tac_images/1.3.4/` — `CASA_1_3_4_page1.png`, `page2.png`, `confirm_guesses.png`, `reset_expired.png`, `supabase_rate_limits.png`, `supabase_email_otp.png` | Out-of-band reset codes meet ADA's 20-bit entropy floor. Email OTP is 8 digits (about 27 bits). Recovery links use a hashed GoTrue token with well over 64 bits. Because the 8-digit OTP is under 64 bits, GoTrue rate-limits OTP and magic-link verifications to 30 requests per 5 minutes per IP. Password-reset emails are capped at 30 per hour. TOTP is 6 digits (ADA's typical 20-bit example) and GoTrue limits MFA challenge and verify to 15 requests per hour per IP. Guessing a reset token returns 400 and cannot set a password. We do not send SMS OTPs. |
| 9 | 2.1.1 no tokens in URL | `tac_images/2.1.1/` — `CASA_2_1_1_page1.png`, `page2.png`, `code.png`, `query_rejected.png`, `login.png` | Login is POST /users/login with the password in the request body, never as a GET query parameter. The session JWT is sent as Authorization Bearer, not in the URL. Official ADA ZAP scans of the SPA and API did not report Session ID in URL or Sensitive Information in URL. Google OAuth returns tokens to a popup via postMessage. Password-reset confirm posts the recovery token in the JSON body. Invite accept and public invoice links may include a one-time capability token in the query; those are not the user session JWT. |
| 10 | 2.2.1 logout invalidates | `tac_images/2.2.1/` — `CASA_2_2_1_page1.png`, `page2.png`, `code.png`, `refresh_replay.png`, `logout_menu.png`, `after_logout.png` | Users can log out from the app menu. Logout calls POST /users/logout, which revokes this Supabase session (GoTrue admin sign_out) and then clears browser storage. Replaying the refresh token after logout returns 401. The short-lived access JWT expires on its own (under 24 hours). |
| 11 | 2.2.2 other sessions on password change | `tac_images/2.2.2/` — `CASA_2_2_2_page1.png`, `page2.png`, `code.png`, `gotrue.png`, `login.png`, `forgot_password.png`, `reset_expired.png` | Password change is through password reset (Forgot password), not an in-app current-password form. Confirm updates the password in Supabase Auth. GoTrue then terminates other sessions by default: a recovery session logs out every other session; an admin password update logs out all sessions for that user. After a successful reset the app sends the user to sign in. Short-lived access JWTs expire on their own (under 24 hours). |
| 12 | 2.2.3 stateless token under 24h | `tac_images/2.2.3/` — `CASA_2_2_3_page1.png`, `page2.png`, `code.png`, `exp.png` | The user session access token is a signed JWT. On staging (28 Aug 2026) exp minus iat is 28800 seconds (8 hours), under ADA's 24-hour cap. The API rejects expired JWTs. The app reads exp and refreshes about a minute before expiry. The refresh token is a separate, revocable session token (see 2.2.1), not the stateless token this row covers. |
| 13 | 2.3.1 cookie Secure | `tac_images/2.3.1/` — `CASA_2_3_1_page1.png`, `page2.png`, `code.png`, `zap.png`, `headers.png` | Session tokens are not cookies. Login returns a JWT in the JSON body and the app stores it in localStorage, then sends Authorization Bearer. Staging POST /users/login sets no Set-Cookie and is HTTPS with HSTS. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Cookie Without Secure Flag. There is no session cookie for the Secure attribute to apply to. |
| 14 | 2.3.2 cookie HttpOnly | `tac_images/2.3.2/` — `CASA_2_3_2_page1.png`, `page2.png`, `code.png`, `zap.png`, `headers.png` | Session tokens are not cookies. Login returns a JWT in the JSON body and the app stores it in localStorage, then sends Authorization Bearer. Staging POST /users/login sets no Set-Cookie. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Cookie No HttpOnly Flag. There is no session cookie for the HttpOnly attribute to apply to. |
| 15 | 2.3.3 session tokens not static API keys | `tac_images/2.3.3/` — `CASA_2_3_3_page1.png`, `page2.png`, `code.png`, `dyn.png` | User login does not use a static API key. After a correct password, Supabase Auth issues a new JWT and refresh token for that session. Two successive staging logins produced different iat values. The app sends Authorization Bearer. Gmail and Calendar use that user's OAuth tokens, not a shared mailbox key. Tenant inbound CRM keys (X-API-Key) are a separate machine path for contact push; they are not the user session. |
| 16 | 2.3.4 signed stateless tokens | `tac_images/2.3.4/` — `CASA_2_3_4_page1.png`, `page2.png`, `code.png`, `zap.png`, `reject.png` | The user session is a signed JWT. Staging issues ES256. The API verifies the signature with jose (HS256 secret or JWKS for ES256/RS256) and rejects invalid, expired, or tampered tokens with 401. Official ADA ZAP scans did not report JWT signature-not-verified or JWT none-algorithm findings. Gmail and Calendar tokens are Fernet-encrypted at rest and are not the session JWT. |
| 17 | 2.4.1 reauth for sensitive changes | `tac_images/2.4.1/` — `CASA_2_4_1_page1.png`, `page2.png`, `code.png`, `reject.png`, `profile.png` | Profile and sign-in email changes require a valid JWT session (PATCH /users/me). Staging calls without Authorization, or with Bearer not-a-jwt, return 401. Password change uses a recovery email, not an in-session current-password form. Disabling MFA requires a current authenticator code. Platform admin routes require AAL2. We do not claim a password re-prompt on every profile save. |
| 18 | 3.1.1 least privilege | `tac_images/3.1.1/` — `CASA_3_1_1_page1.png`, `page2.png`, `code.png`, `tests.png`, `deny.png` | Access control is enforced on the API (FastAPI), not only in the browser. Roles are Agent, TransactionCoordinator, TeamLead, Attorney, Admin, Client, ForSaleByOwner, and Vendor. Endpoints use get_current_user plus require_role, require_tenant_access, and require_transaction_access. Tenant Admin is not cross-tenant. Platform /api/v1/platform/* requires is_platform_admin and AAL2. Staging unsigned GET /users/ and GET /platform/users return 401. Postgres RLS is defense in depth; the API is the trusted layer. |
| 19 | 3.1.2 users cannot alter policy attrs | `tac_images/3.1.2/` — `CASA_3_1_2_page1.png`, `page2.png`, `code.png`, `tests.png`, `ignore.png` | Role, tenant, platform-admin, and active flags used for access control come from the server profile after JWT verification, not from client JSON. Register ignores client tenant_id and mints a new tenant. OAuth ignores user_metadata tenant_id. PATCH /users/me has no role, tenant_id, is_platform_admin, or is_active fields; extra is_active is ignored. Role changes after signup go through PUT /users/{id}/role in the same tenant. Staging unsigned PATCH /users/me with those extra fields returns 401. |
| 20 | 3.1.3 fail securely | `tac_images/3.1.3/` — `CASA_3_1_3_page1.png`, `page2.png`, `code.png`, `tests.png`, `fail.png` | Access control fails closed. Missing Authorization returns 401. An invalid JWT raises JWTError and returns 401; it does not load a user. Role, tenant, and assignment misses return 403 (some cross-owner reads return 404). The scheduler tick requires X-VE-Cron-Secret and fails closed if the secret is unset. Unhandled exceptions return a generic 500, not the resource. Staging: GET /users/me without Authorization and with Bearer not-a-jwt both 401; POST /internal/schedules/tick without the cron header returns 403. |
| 21 | 3.1.4 IDOR | `tac_images/3.1.4/` — `CASA_3_1_4_page1.png`, `page2.png`, `code.png`, `tests.png`, `deny.png` | User-supplied object IDs appear in paths such as /users/{id}, /tenants/{id}, /transactions/{id}, /documents/{id}, /invoices/{id}, /tasks/{id}, /teams/{id}, and /audit-logs/{type}/{id}. Knowing a UUID is not enough. After JWT verification the API loads the row and checks tenant (require_tenant_access) and, for deals, assignment (require_transaction_access). Lists are tenant-scoped. A tenant Admin cannot read or change another org's tenant or users (403). Cross-owner FSBO and unrelated document reads return 404. Staging unsigned GET of those ID paths with a placeholder UUID returns 401. |
| 22 | 3.1.5 CSRF | `tac_images/3.1.5/` — `CASA_3_1_5_page1.png`, `page2.png`, `code.png`, `zap.png`, `cors.png`, `register_429.png` | Authenticated APIs use Authorization Bearer, not a cookie session. Login returns JWTs in JSON and sets no Set-Cookie, so a cross-site form cannot send the session. CORS allowlists the SPA origin; a foreign Origin does not receive Access-Control-Allow-Origin. Unauthenticated register is limited to 5 requests per minute per IP. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Absence of Anti-CSRF Tokens. We do not ship a synchronizer CSRF cookie. |
| 23 | 3.1.6 directory browsing | `tac_images/3.1.6/` — `CASA_3_1_6_page1.png`, `page2.png`, `code.png`, `zap.png`, `nolist.png` | Directory browsing is disabled. The SPA is hashed CloudFront assets (S3 origin via OAC), not an Apache or nginx autoindex. Staging GET /assets/, /static/, and a missing hashed JS file return the SPA HTML shell, not Index of / or an S3 ListBucketResult. The API does not mount static files; GET /, /api/v1/, and /static/ return JSON 404. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Directory Browsing. We did not run Burp 6291712. |
| 24 | 3.2.1 OAuth code plus PKCE | `tac_images/3.2.1/` — `CASA_3_2_1_page1.png`, `page2.png`, `code.png`, `tests.png`, `pkce.png` | Velvet Elves OAuth is authorization code with PKCE (S256). Google and Microsoft sign-in start at POST /users/oauth/{provider}/start and pass code_challenge to Supabase /auth/v1/authorize. Gmail, Outlook, Calendar, and DocuSign authorize URLs set response_type=code plus code_challenge_method=S256. There is no implicit flow and no resource-owner password grant to those providers. Staging POST /users/oauth/google/start returned a PKCE authorize URL (s256); the flow was not completed. Unsigned POST /integrations/gmail/authorize-url returns 401. |
| 25 | 3.2.2 redirect uri and state | `tac_images/3.2.2/` — `CASA_3_2_2_page1.png`, `page2.png`, `code.png`, `tests.png`, `deny.png` | OAuth redirect_uri and state are validated to prevent open redirect and OAuth CSRF. Google and Microsoft sign-in redirect_to must match an allowlisted SPA origin; a foreign origin returns 400. Sign-in state is a Fernet token with a 10-minute TTL; a forged state on POST /users/oauth/google/exchange returns 400 Invalid or expired OAuth state. Gmail, Outlook, Calendar, and DocuSign redirect_uri is set by the API from configuration, not by the client. Integration state binds user, provider, and redirect_uri. Callback postMessage targets FRONTEND_URL, not *. Staging: foreign redirect_to 400; garbage state 400. |
| 26 | 3.3.1 admin MFA | `tac_images/3.3.1/` — `CASA_3_3_1_page1.png`, `page2.png`, `code.png`, `tests.png`, `deny.png`, `stage_mfa_prompt.png`, `stage_platform_code.png`, `stage_security_on.png`, `prod_mfa_prompt.png`, `prod_security_on.png` | The application administrative interface is the platform console (/api/v1/platform/*). Those routes require is_platform_admin plus a JWT aal2 claim and a live verified TOTP factor (PLATFORM_ADMIN_MFA_REQUIRED defaults true). Login of an enrolled admin returns mfa_required until the authenticator code is verified. The SPA PlatformMfaGate blocks the console until a code is entered. Staging and production both show the two-step prompt and Security authenticator app is on. Unsigned GET /platform/users returns 401. Tenant Admin is a workspace role and is not this interface; MFA is not required for all users. |
| 27 | 4.1.1 TLS 1 2 plus | `M9a_architecture.md` | HTTPS only ALB and CloudFront HSTS on production API |
| 28 | 4.1.2 trusted certs | `M9a_architecture.md` | Public ACM certificates No self signed on app velvetelves com |
| 29 | 4.1.3 no weak crypto on secrets | `M9e_pii_encryption.md` | Tokens and PII at rest use Fernet AES SHA1 is only a short proposal id Low |
| 30 | 4.1.4 crypto fail securely | `M9e_pii_encryption.md` | Fernet decrypt failures do not return plaintext |
| 31 | 5.1.1 HTTP parameter pollution | `DAST_SUMMARY.md` | FastAPI typed params Official ZAP XML in the scan zip |
| 32 | 5.1.2 open redirect | `M9b_data_flow.md` | OAuth callback does not echo untrusted redirects FRONTEND URL only |
| 33 | 5.1.3 no eval | `SAST_SUMMARY.md` | No user driven eval SAST CSV 0 High |
| 34 | 5.1.4 template injection | `SAST_SUMMARY.md` | Server templates are not user controlled SAST CSV 0 High |
| 35 | 5.1.5 SSRF | `DAST_SUMMARY.md` | No user controlled server fetch of arbitrary URLs ZAP XML attached in scan zip |
| 36 | 5.1.6 XML injection | `DAST_SUMMARY.md` | JSON APIs not XML parsers for user input |
| 37 | 5.1.7 XSS | `compensating_controls.md` | OAuth XSS closed on rescan CSP Mediums are compensating residuals |
| 38 | 5.1.8 SQLi | `DAST_SUMMARY.md` | SQLAlchemy parameterized Auth ZAP SQLi High is false positive replay 422 or generic 500 |
| 39 | 5.1.9 OS command injection | `SAST_SUMMARY.md` | No shelling user input SAST CSV 0 High |
| 40 | 5.1.10 file inclusion | `DAST_SUMMARY.md` | Auth ZAP path traversal High is false positive path segment only |
| 41 | 5.2.1 malicious uploads | `self_attestation_draft.md` | Uploads go to object storage not executed as code |
| 42 | 6.1.1 no known exploitable components | `DEPS_SUMMARY.md` (refresh) + S12 | npm production 0 pip audit clean after upgrades pydantic ai and pypdf upgraded 27 Aug Remaining notes ecdsa has no released fix and pytest is dev only not shipped |
| 43 | 6.2.1 debug off in production | `M9a_architecture.md` | Production APP DEBUG false docs redoc openapi are 404 |
| 44 | 6.3.1 Origin not used as auth | `M9f_tenant_isolation.md` | Auth is JWT not Origin header |
| 45 | 6.4.1 subdomain takeover | `M9a_architecture.md` | Live hosts are CloudFront and ALB No dangling review CNAMEs in use |
| 46 | 6.5.1 do not log credentials | `M9g_logging.md` | Logs mask emails No tokens or mail bodies |
| 47 | 6.6.1 clear browser storage on logout | `compensating_controls.md` | Logout clears velvet elves token keys in localStorage |
| 48 | 6.7.1 server secrets | `M9d_token_storage.md` | Secrets in AWS Secrets Manager Google tokens Fernet encrypted Disconnect is soft deactivate |

File paths under `casa_al1_evidence/m9/` except `DAST_SUMMARY.md` / `SAST_SUMMARY.md` / `DEPS_SUMMARY.md` in `casa_al1_evidence/2026-08-21/`. AI screenshot `openai-data-controls.png` is extra for any secrets/subprocessor question; do not call it ZDR.

If a row upload rejects `.md`, zip that one markdown (letters-only name like `M9d token storage.zip`) and retry.

---

## 8. After TAC reviews (PDF steps 14–17)

1. **Revalidation:** fix only what they fail. Staging first, then prod, then re-upload. Premium covers unlimited retests.
2. Email `casasupport@tacsecurity.com` when the scan is clean (PDF page 10). **TAC** submits the LOV to Google.
3. Google typically sends an LOV reverification email in **5–6 business days**. Reply to that if they ask.
4. **You reply-all** on Google’s Trust and Safety CASA thread (not a new case):

> ADA-CASA AL1 for project 538509143953 (`velvet-vles`) is complete. The authorized lab has issued the Letter of Validation and submitted it to Google. Copy attached. Please continue verification.

5. Watch Cloud Console → Verification Center. Do not tell Google it is complete before the LOV exists.

---

## 9. Holding reply to Google (optional, if not sent)

If the Trust and Safety thread has no “we started” note yet, reply-all:

> We received the ADA-CASA AL1 requirement for project 538509143953 (`velvet-vles`), due 18 November 2026. We are engaging an ADA-authorized lab and will reply again on this thread once the Letter of Validation is issued.

Do not attach the M9 folder. Do not say the assessment is complete.

---

## 10. Checklist

- [x] Login as `jan@velvetelves.com`. LOV complete. Assessment **Velvet Elves** / Web / FILE submitted 26 Aug. Dashboard 27 Aug: step 2 **Completed**, step 3 **Assessment Review / In Progress**, **Upload Evidence** is live.
- [ ] Ignore SOC 2 / Policy template downloads / CRQ / AL2. Do **not** click **SUBMIT CASA ASSESSMENT** again.
- [ ] Click **Upload Evidence** under step 3 (or the cloud **Upload** on the Velvet Elves row). Screenshot the check list before attaching files.
- [ ] Fill every required check from Section 6 / `casa_al1_evidence/m9/`. Use live privacy URLs, not TAC Policy downloads.
- [ ] Edit LOV email typo if Edit still works (`jake@velvetelves.com.com`).
- [ ] After a clean TAC report, email `casasupport@tacsecurity.com`. Wait for TAC to send the LOV to Google, then reply-all on the Trust and Safety thread.
