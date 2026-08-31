# Google ADA-CASA AL1 — Analysis and Next Steps

**Prepared for:** Jake, Audri, Jan  
**Date:** August 20, 2026  
**Trigger:** Trust and Safety email for project `538509143953` (`velvet-vles`) requiring ADA-CASA AL1 by **18 November 2026**  
**Companion docs:** `GMAIL_GOOGLE_APPROVAL_PACKAGE_PLAYBOOK.md`, `GMAIL_GOOGLE_APPROVAL_MATERIALS_AND_STEPS.md` (M9 security packet), `GMAIL_GOOGLE_APPROVAL_GUIDELINES.md`, `GOOGLE_REVIEWER_TESTING_GUIDELINES.md`

---

## Bottom line

Google is not rejecting the app. The video, scopes, and in-app testing were enough to move the case forward. The remaining gate is a **paid ADA-CASA AL1 security assessment**, because `gmail.readonly` is a restricted scope. Verification cannot finish until a lab issues a Letter of Validation (LOV) and we reply on this same thread with that confirmation.

**Required:** AL1 (formerly Tier 2), due **18 November 2026**.  
**Not required:** AL2. That is a deeper infrastructure audit plus a Workspace Marketplace badge Velvet Elves does not need.

Today is 20 August. Google says 2–6 weeks, and remediations slip. Start this week. Do not wait until October.

---

## What the email actually means

| Google said | What it means for Velvet Elves |
| --- | --- |
| Complete ADA-CASA **AL1** by **18 Nov 2026** | Mandatory. Annual after that. Triggered by `gmail.readonly` on project `velvet-vles` (538509143953). |
| 2–6 weeks, start now | Lab queue + findings + retest. Budget ~8 weeks with slack, not 2. |
| Option 1 AL1 vs option 2 AL2 | AL1 is what they assigned. AL2 is optional and more expensive. |
| TAC Security, discounted | Google’s preferred ADA lab. Typical AL1 Basic **$675**, Premium **$855**. Any [ADA-authorized lab](https://appdefensealliance.dev/casa/casa-assessors) is allowed. |
| Due-date extension via the **lab**, not Google | If the lab is slow, they request the extension. |
| Reply after the issues are fixed | The confirmation reply is **after** the LOV, not “we will do it.” A short holding reply that we have started is still useful. |
| Cancel if you no longer need the scopes | Only if we drop `gmail.readonly` and kill inbound Gmail matching. Do not do that. |
| Make changes in Cloud Console | Do **not** change scopes, branding, or clients while this runs. |

The other checklist items (homepage, domain, privacy, demo video, in-app testing, minimum scopes) are the earlier round. This email’s only new requirement is **CASA**.

AL2 is not a faster AL1. It tests the app, AWS/ECS, and data stores (Supabase). It is about **$4,500** and mainly useful for Marketplace badging. Skip it.

---

## Who does what

This matches the existing split: Jake/Audri spend and sign; Jan prepares evidence and remediates.

| Role | Owns |
| --- | --- |
| **Jake / Audri** | Approve budget, pick the lab, pay, sign the SOW, send Google’s CASA notification email to the lab, send the holding reply and the final LOV reply |
| **Jan** | Evidence packet, scans, lab questionnaires, test access, fix findings, confirm nothing in Console changes |
| **Lab** | Scan/verify, retest after fixes, issue LOV, send LOV to Google |

---

## Step-by-step plan

### Step 1 — Same day: freeze Console and acknowledge Google

1. Do not change OAuth scopes, branding, clients, or redirect URIs on `velvet-vles`.
2. Reply-all on the existing thread (from `jan@velvetelves.com` is fine). Short holding note only:

> We received the ADA-CASA AL1 requirement for project 538509143953 (`velvet-vles`), due 18 November 2026. We are engaging an ADA-authorized lab and will reply again on this thread once the Letter of Validation is issued.

3. Do not attach internal docs. Do not say the assessment is complete.

### Step 2 — Same day: Jake/Audri approve AL1 spend

Recommend **TAC Security AL1**, not AL2, not a SOC 2 bundle.

- **Basic — $675:** one AL1, two retest cycles. Enough if the first scan is clean.
- **Premium — $855:** unlimited retests. Safer if the first scan finds several issues.

Portal: [casa.tacsecurity.com](https://casa.tacsecurity.com/site/home)  
Support: `casasupport@tacsecurity.com`  
Official process: [CASA kickoff](https://appdefensealliance.dev/casa/casa-start)

Jake pays and signs. Jan does not engage the vendor.

### Step 3 — This week: kick off the lab

1. Register at the TAC portal (or another ADA lab from [the assessor list](https://appdefensealliance.dev/casa/casa-assessors)).
2. Send them **Google’s CASA email** (the notification is what starts the assessment).
3. Give them:
   - Project: Velvet Elves / `velvet-vles` / 538509143953
   - App URL: `https://app.velvetelves.com`
   - Level: **AL1** (not AL2)
   - Due date: 18 November 2026
   - Test login: `algoforth33@gmail.com` (same workspace as the demo)
4. Confirm the lab’s exact method (they scan, you upload SAST/DAST results, or both) and the date they will start.

### Step 4 — This week, in parallel: Jan prepares what the lab will ask for

The M9 security packet was never assembled. That is now on the critical path. Produce one folder, honest against production code:

1. Architecture diagram (browser, FastAPI, Supabase, Gmail, Pub/Sub, Calendar, AI provider).
2. Data-flow: connect → inbound → draft → send → calendar write → disconnect → deletion.
3. Scope-to-API map (`users.watch` / `history.list` / `messages.get` / `messages.send` / Calendar events).
4. Token storage: encrypted at rest, who can access, rotation.
5. PII encryption and tenant isolation, with passing isolation tests.
6. Logging policy: no tokens, auth codes, or full mail bodies.
7. Dependency/vulnerability scan of the live stack; fix critical/high before the lab scan.
8. Incident response (including notifying Google of a Google-data incident), retention, deletion (`https://velvetelves.com/data-deletion`).
9. Subprocessor list and AI-provider no-training terms.

Also confirm before they scan:

- HTTPS everywhere on `app.velvetelves.com` and `api.prod.velvetelves.com`
- The test account still signs in with no 2FA/card wall
- Data deletion / disconnect still matches the public pages
- No document claims a Gmail-watch behavior the code does not do (the old “renews daily” wording)

The lab will fail false claims.

### Step 5 — Lab scan and questionnaire (about 1–2 weeks after kickoff)

Typical AL1 surface (OWASP ASVS subset): authentication, sessions, access control, TLS, input validation, config, secure OAuth.

Jan:

- Completes their questionnaire from evidence, not from memory
- Gives them the production URL and test account
- Uploads scan results if they ask for SAST/DAST
- Does **not** give production AWS/root or the database to an AL1 lab unless they explicitly require it (that is AL2 territory)

### Step 6 — Remediate every finding, then retest

1. Treat every open CASA-mapped finding as a launch blocker.
2. Patch, redeploy production, tell the lab to re-scan.
3. Repeat until the lab is clean. This is what turns 2 weeks into 6.
4. If the calendar slips past mid-October, ask **the lab** for a due-date extension. Do not email Google for that.

### Step 7 — Letter of Validation

1. Lab issues the LOV and sends it to you and to Google.
2. Save the PDF. Record the issue date. Set a calendar reminder for **annual recertification ~ October 2027** (12 months from LOV, before Google’s next notice).
3. Wait a few business days; TAC says Google often updates the Verification Center within about a week of LOV submission.

### Step 8 — Final reply to Google (this is the required “confirm”)

Reply-all on the **same** CASA email, after the LOV exists:

> ADA-CASA AL1 for project 538509143953 (`velvet-vles`) is complete. The authorized lab has issued the Letter of Validation and submitted it to Google. Copy attached. Please continue verification.

Attach the LOV. Then check Cloud Console → Verification Center until CASA is marked complete.

### Step 9 — After Google accepts CASA

1. Confirm remaining verification rows in the Verification Center are green.
2. Confirm production OAuth no longer shows the unverified-app warning for new users.
3. Re-run Gmail connect → inbound → Approve & send → Calendar → disconnect on production.
4. Freeze new Gmail/Calendar scopes. Any new restricted scope restarts this.

---

## Timeline (working backward from 18 Nov)

| When | What |
| --- | --- |
| **20–22 Aug** | Holding reply. Jake approves AL1 budget. Kick off TAC. Jan starts the evidence folder and a vuln scan. |
| **Late Aug** | Lab intake done. First scan/questionnaire in progress. |
| **Early Sep** | Findings in. Remediate and redeploy. |
| **Mid–late Sep** | Retest clean. LOV issued. Final reply to Google. |
| **Oct** | Slack if remediations ran long. Ask the lab for an extension if needed. |
| **18 Nov** | Hard Google due date. Do not arrive here without an LOV. |
| **~Oct 2027** | Annual recertification. |

---

## Do not do

- Drop `gmail.readonly` to dodge CASA.
- Buy AL2 or a SOC 2 add-on unless Jake separately wants those.
- Change Cloud Console OAuth settings during the assessment.
- Reply “complete” before the LOV exists.
- Use a lab that is not on the ADA authorized list.
- Hand the lab production secrets or customer mailboxes. Use the demo test account only.

---

## Official links

- [Google: Security Assessment](https://support.google.com/cloud/answer/13465431)
- [ADA CASA overview](https://appdefensealliance.dev/casa)
- [CASA kickoff (notification → lab → LOV)](https://appdefensealliance.dev/casa/casa-start)
- [Assurance levels (AL1 vs AL2)](https://appdefensealliance.dev/casa/casa-tiering)
- [ADA-authorized assessors](https://appdefensealliance.dev/casa/casa-assessors)
- [TAC Security CASA portal](https://casa.tacsecurity.com/site/home)
- [OAuth App Verification Help Center](https://support.google.com/cloud/answer/13463073)

---

## The decision that unblocks everything else

**Jake/Audri approve AL1 spend this week and Jan starts the evidence packet the same day.**
