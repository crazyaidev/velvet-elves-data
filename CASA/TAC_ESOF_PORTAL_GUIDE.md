# TAC ESOF portal — CASA AL1 operating guide (Jan)

**Date:** 26 August 2026  
**Portal:** https://casa.tacsecurity.com/  
**Official TAC PDF:** `CASA/ESOF_AppSec_ADA_CASA_User_Guide_Ver.2.0.pdf` (12 pages, 2026)  
**Login:** `jan@velvetelves.com` (alternate email on Jake’s account; same password as Jake’s TAC login)  
**Google due date:** 18 November 2026  
**GCP:** `velvet-vles` / **538509143953**  
**Companion:** `GOOGLE_CASA_AL1_NEXT_STEPS.md`, `casa_al1_evidence/m9/`

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

## 7. The 48 checks (after Upload Evidence appears)

Fill every required check. Typical mapping:

| Theme | Use |
| --- | --- |
| Auth / session | M9d + compensating JWT-in-`localStorage` write-up. Do not claim HttpOnly cookies. |
| Access control / tenancy | M9f + isolation tests. |
| TLS / headers | Production API HSTS / nosniff / XFO DENY; SPA CSP. Staging docs stay on; prod `/api/docs` is 404. |
| Input validation | ZAP XML + false-positive SQLi / path-traversal notes. |
| Secrets / encryption | M9d, M9e. Fernet. No keys in git. |
| Logging | M9g. No tokens or full mail bodies. |
| OAuth / Google data | M9b, M9c. PKCE. Disconnect is soft-deactivate. |
| Deletion / IR | M9i. 30-day public SLA. Notify Google of a Google-data incident. |
| Subprocessors / AI | M9j + Sharing PNG. |
| SAST / DAST | Section 6 files. |

Where a ZAP Medium remains, paste the compensating-control paragraph. Do not mark Highs as pass if they are still open. The two auth-API Highs are **false positives** with replay notes in `DAST_SUMMARY.md`.

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

- [x] Login as `jan@velvetelves.com`. LOV complete. Assessment **Velvet Elves** / Web / FILE submitted 26 Aug. Status **In Progress**.
- [ ] Ignore SOC 2 / Policy template downloads / CRQ / AL2. Do **not** click **SUBMIT CASA ASSESSMENT** again.
- [ ] Open the bell (badge **1**) and the blue **eye** on the Velvet Elves row. Screenshot both.
- [ ] If **Upload Evidence** / questionnaire is there, fill the 48 checks from Section 6 / `casa_al1_evidence/m9/`.
- [ ] If the row only says **In Progress** with no upload UI, wait for TAC to ingest the zip (or ticket `casasupport@tacsecurity.com` after a business day).
- [ ] Edit LOV email typo if Edit still works (`jake@velvetelves.com.com`).
- [ ] After a clean TAC report, email `casasupport@tacsecurity.com`. Wait for TAC to send the LOV to Google, then reply-all on the Trust and Safety thread.
