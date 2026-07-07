# Gmail Google Approval: To-Do List

**Purpose:** the sequenced, checkbox task list to take Velvet Elves' Gmail integration from "works in testing" to "approved by Google for external production users."
**Owner:** Jan (sole dev). Items needing Jake are tagged **[Jake]** (legal entity, support mailbox, domain/Search Console access, final sign-off).
**Companion doc:** `GMAIL_GOOGLE_APPROVAL_GUIDELINES.md` holds the reasoning, policy language, scope justifications, demo script, and reviewer answers. This file is the actionable checklist; that file is the reference.
**Last updated:** 2026-07-06.

---

## How to read this

- Work top to bottom. Phases 0 to 3 must finish before Phase 4 (packet), which must finish before Phase 5 (submit).
- `[ ]` open, `[~]` in progress, `[x]` done, `[!]` blocked (see the blocker log at the bottom).
- Every item that touches Google Cloud Console notes whether it is **Console-UI only** (gcloud cannot do it) or scriptable.
- "Prod project" always means GCP project **`velvet-vles`** (project number 538509143953, display name "Velvet Elves"). "Staging project" means **`velvet-elves-495419`**. Only the prod project is submitted for verification.

---

## Current state snapshot (start line)

What is already true as of 2026-07-06, so I do not redo it:

- **Prod GCP project exists** (`velvet-vles`), Gmail + Pub/Sub + Calendar APIs enabled, Jake holds Owner.
- **Prod Pub/Sub is wired**: topic `gmail-inbound-prod`, push subscription `gmail-inbound-prod-push`, endpoint and audience already moved to `https://api.prod.velvetelves.com/api/v1/integrations/email/webhook/gmail`.
- **Dedicated prod OAuth 2.0 Web client created** (`538509143953-sl6god134...`); `PROD_GOOGLE_CLIENT_ID`/`SECRET` set in `.env.prod`.
- **Backend prod domain settled** at `api.prod.velvetelves.com`; `.env.prod` fully on the new host.
- **Integration code is feature-complete and tested**: connect, encrypted token storage, `users.watch`, Pub/Sub inbound, `history.list` delta sync, transaction matching, AI draft (human-approved), send, disconnect.

What is NOT done yet (this list closes these):

- OAuth client **redirect URIs not yet updated** to the new prod domain (Gmail + Calendar callbacks). Until fixed, prod connect returns `redirect_uri_mismatch`.
- **Scopes not minimized**: `gmail.modify` is still requested but unused (see Phase 1). Removing it drops a restricted scope.
- **Consent screen likely still in Testing** (test-user allowlist), not published to production.
- **Public privacy policy is insufficient**: `velvetelves.com/legal` describes only the marketing site's email capture, not Gmail/Google user data, Limited Use, AI processing, or app deletion.
- **No demo video, no scope-justification packet, no security evidence packet** yet.
- **Verification not submitted.**

---

## Phase 0: Decisions and prerequisites

- [ ] **[Jake]** Confirm the legal entity name and jurisdiction that owns the app and appears in the privacy policy and terms. The marketing `/legal` page's own comment flags this as the one open item before publish.
- [ ] **[Jake]** Confirm a monitored support mailbox (for example `support@velvetelves.com`) that will match the consent-screen support email and the deletion/support page. Someone must read it daily during review.
- [ ] **[Jake]** Confirm I have (or Jake performs) Google Search Console access for `velvetelves.com` to verify the authorized domain.
- [ ] Decide the final scope set. Recommendation, code-verified in Phase 1: `openid`, `email`, `profile`, `gmail.send`, `gmail.readonly` (drop `gmail.modify`). Calendar keeps `calendar.events`.
- [ ] Confirm which AI provider(s) receive Gmail-derived content in prod, and that their terms forbid training on our customer data (needed for the subprocessor disclosure and security packet). See [[ai-provider-selected-manually-never-auto-switch]].
- [ ] Set a target public-launch date and back-plan from it. Assume **6 to 8 weeks minimum**; restricted-scope review plus any CASA security assessment is the long pole and is not fully in my control.

---

## Phase 1: Scope minimization (code, do this first)

The single highest-leverage pre-submission action. Google's minimum-scope rule is the top rejection cause, and every restricted scope I carry widens the security-assessment surface.

- [x] **Drop `gmail.modify`.** DONE 2026-07-06: removed from `GMAIL_SCOPES` in `app/services/email/gmail_provider.py` with a guard comment stating it must not return; test mock scope string updated; `test_email_integration_api.py` all 46 green. (Basis: code-verified that the provider calls only `messages/send`, `messages` list/get, `history`, and `users/me/watch`; no modify/trash/label call exists.) `gmail.readonly` is now the only restricted scope.
- [ ] Re-test end to end after the scope change on staging: OAuth connect, inbound Pub/Sub delivery, `history.list` delta sync, and outbound send all still work with `send` + `readonly` only.
- [ ] Decide on `profile`. Keep only if the integration UI actually shows the Google account name or avatar. If it shows only the email address, drop `profile` and rely on `email`. Verify against the Settings > Integrations UI before deciding.
- [ ] Do NOT request `https://mail.google.com/`, `gmail.compose`, `gmail.insert`, or `gmail.settings.*`. Confirm none are present.
- [ ] After the code change, make the Google Cloud Console consent-screen scope list **exactly** match the code (Phase 3). Code and Console must never disagree at submission.
- [ ] Freeze scopes. From here until approval, no new sensitive/restricted scope lands in code without treating it as a launch-blocking change.
- [ ] **Harden the Gmail webhook against duplicate/stale integrations (staging incident 2026-07-06).** The same mailbox connected under two users made `get_active_by_provider_email` resolve every Pub/Sub push to the stale row; its dead refresh token (Testing-mode tokens expire in 7 days) threw an HTTPException out of the webhook, the non-200 made Pub/Sub redeliver in an endless storm (500+/hour), and the healthy row never saw a notification. Fixes: (a) resolution must prefer the row with a live watch / most recent token, or process all matching rows; (b) token-refresh failure inside the webhook must be caught, mark the integration unhealthy, and return 200 so Pub/Sub stops retrying; (c) surface "connection unhealthy, reconnect Gmail" in the Integrations UI instead of failing silently. Interim fix applied: stale stage row `9ff3e5e9` deactivated by hand.
- [x] **Build Gmail watch auto-renewal — BUILT 2026-07-06 (uncommitted).** Root cause: `users.watch` expires after 7 days and nothing renewed it; every staging watch dead since mid-May, prod watch was set to die 2026-07-08. Implementation: `app/services/email/gmail_watch_renewal.py` with (a) `renew_due_gmail_watches` scan + `POST /integrations/gmail/watches/renew-due` (admin, mirrors the Outlook renew-due endpoint) and (b) opportunistic renewal inside the Gmail webhook after each successful sync (36h window), so active mailboxes self-sustain with no scheduler. Renewal preserves the `lastHistoryId` cursor (no message gap). 6 new tests + full email-integration suite green (52 total).
  - [ ] Remaining: deploy to stage/prod BEFORE 2026-07-08 19:55 UTC (prod watch expiry; any inbound email after deploy renews it), and wire a daily cron for the renew-due endpoint to cover idle mailboxes (ties into the platform's missing-scheduler gap).
  - [ ] Update the guidelines/security-answer wording from "renews daily" to the true mechanism: due-scan endpoint + renewal-after-sync.

---

## Phase 2: Public website and policy pages

Google reviewers open public, non-login pages on the authorized domain and check that they match the app on the consent screen. Everything here is hosted on `velvetelves.com` (the marketing site).

- [x] **App-scoped privacy policy covering Google user data — BUILT 2026-07-06 (uncommitted).** New `/privacy` route (`PrivacyPage.tsx`): entity (Orange Door, LLP dba Velvet Elves, Indiana), per-scope Google-data section (read/send/calendar; explicitly states no mailbox modification is requested), encrypted-at-rest statement, named subprocessors (AWS, Supabase, Stripe, SendGrid, OpenAI or Anthropic, Google APIs), retention + 30-day deletion, support contact. `/legal` now cross-links to it as the app policy. SSG build green (19 routes); compliance strings verified present in prerendered `dist/privacy.html`.
- [x] **Exact Limited Use statement — DONE**, in `/privacy#google`, verbatim with a link to the Google API Services User Data Policy.
- [x] **AI disclosure — DONE**, in `/privacy` (human-reviewed drafts, no sale/ads/model training, named AI providers, only feature-scoped content sent).
- [x] **Data-deletion page — BUILT 2026-07-06 (uncommitted).** New `/data-deletion` route (`DataDeletionPage.tsx`): disconnect in Settings > Integrations, revoke at myaccount.google.com/connections, email support@velvetelves.com, 30-day window with the transaction-record caveat. Footer "Company" column links both new pages so they are crawlable.
  - [ ] Remaining for this block: deploy the marketing site; Jake's optional read-through of the policy text (default-publish after a day or two, per the email to him).
- [ ] **Ensure a public support page or support email** is reachable and matches the consent-screen support contact.
- [ ] Confirm every one of these URLs is public (no login wall), loads over HTTPS, and lives on the authorized domain `velvetelves.com`.
- [ ] **[Jake]** Final attorney/entity review of privacy + terms (the `/legal` page flags this as a formality on accuracy, not a blocker, but it should happen before public launch).

---

## Phase 3: Google Cloud project and consent screen (prod project `velvet-vles`)

All Console-UI only unless noted. gcloud cannot edit OAuth clients or the consent screen.

### 3.1 OAuth client (fix the blocker first)

- [ ] **Update the prod OAuth Web client redirect URIs** to the new domain (this is the outstanding `redirect_uri_mismatch` blocker):
  - `https://api.prod.velvetelves.com/api/v1/integrations/gmail/callback`
  - `https://api.prod.velvetelves.com/api/v1/calendar/google/callback`
  - Confirm each path against the live backend routes before saving.
- [ ] Confirm the Supabase "Sign in with Google" callback `https://kbgvnsjdkgzixpeazmtn.supabase.co/auth/v1/callback` is present where that login flow needs it (it is unaffected by the backend domain change, but verify it is not accidentally dropped).
- [ ] Remove any dev/local redirect URIs from the prod client. Local and staging URIs belong in the staging project, not `velvet-vles`.
- [ ] Confirm there are no leftover unverified or test OAuth clients in the prod project. Every client in the submitted project should be production-ready.

### 3.2 Consent screen branding

- [ ] App name: `Velvet Elves`.
- [ ] App logo: production logo (the brand logo PNG, per [[marketing-site-daybreak-redesign]] brand rule; do not invent a mark).
- [ ] User support email: the monitored mailbox from Phase 0.
- [ ] Developer contact emails: at least two monitored addresses if possible.
- [ ] Home page URL: `https://velvetelves.com/`.
- [ ] Privacy policy URL: the app-scoped privacy page from Phase 2.
- [ ] Terms URL: `https://velvetelves.com/legal` (or `/terms`).
- [ ] Authorized domain: `velvetelves.com` (top private domain; unchanged by the `api.prod` backend move).

### 3.3 Domain and scopes

- [ ] **Verify domain ownership** of `velvetelves.com` in Google Search Console (Phase 0 access).
- [ ] Set the consent-screen **data-access scopes** to exactly the Phase 1 final set: `gmail.send`, `gmail.readonly`, `calendar.events` (plus `openid`/`email`/`profile` as retained). No `gmail.modify`.
- [ ] Note the coupling: **`calendar.events` shares this OAuth client**. It is a sensitive scope and will be reviewed alongside Gmail. Either include Calendar in this submission (describe it and demo it) or accept that Calendar connect keeps showing the unverified-app screen until covered. Decide and record which.
- [ ] Set audience to **External**.
- [ ] Add test users while still in Testing so I can rehearse the full flow on the prod client before publishing.

### 3.4 Publish

- [ ] Publish the app to **Production** (out of Testing) so verification can be requested.
- [ ] Re-confirm Pub/Sub prod is intact after any Console changes: topic `gmail-inbound-prod`, subscription `gmail-inbound-prod-push`, publisher `gmail-api-push@system.gserviceaccount.com`, push audience `https://api.prod.velvetelves.com/api/v1/integrations/email/webhook/gmail`, daily `users.watch` renewal running.

---

## Phase 4: Verification packet

### 4.1 Scope justifications

- [ ] Write one concrete, feature-specific justification per scope (pull the wording from guidelines Section 7.2). Reference API method names and the exact screen where the user sees the feature.
- [ ] `gmail.send`: sent only after the user clicks Approve & Send / Edit & Send; transaction-specific; from the user's own mailbox; logged. No autonomous or bulk sending.
- [ ] `gmail.readonly`: reads inbound transaction mail to build communication logs, match to transaction records, and prepare human-reviewed AI drafts (AI Email Review queue).
- [ ] `calendar.events` (if in scope): writes transaction deadlines/events to the user's calendar after user action.

### 4.2 Demo video (unlisted)

- [ ] Record a 6 to 10 minute video with a dedicated test Google account and seeded test transactions (no real client PII). Follow the shot list in guidelines Section 8.2.
- [ ] Show, in order: public home + privacy/Google-data pages, sign in, Settings > Integrations, **the full OAuth consent screen with the app name and permissions visible**, connected state, inbound read via Pub/Sub landing in the transaction log, AI draft (emphasize the AI does not send), Approve & Send, the sent message in the test mailbox, and Disconnect.
- [ ] Do NOT demo `gmail.modify` (it is being removed). Do NOT say "AI sends emails automatically." Do NOT use a dev OAuth client in the recording.
- [ ] Upload as unlisted YouTube; keep the link for the submission.

### 4.3 Security evidence packet (assume CASA will be required for restricted `gmail.readonly`)

- [ ] Architecture + data-flow diagrams (browser, FastAPI backend, Supabase, Gmail API, Pub/Sub, AI provider, email provider).
- [ ] Scope-to-API-method mapping.
- [ ] Token storage design: encryption at rest, key location, rotation, access controls. Cross-check the stateless Fernet OAuth state fix ([[oauth-inmemory-state-multiinstance-bug]]).
- [ ] PII encryption design (from `SYSTEM_DESIGN.md`) and multi-tenant isolation (from `MULTI_TENANCY_IMPLEMENTATION_PLAN.md`), with passing isolation tests.
- [ ] Logging policy proof: no OAuth tokens, auth codes, refresh tokens, raw Pub/Sub JWTs, or full Gmail bodies in logs; email addresses masked where practical.
- [ ] Vulnerability/dependency scanning process and evidence; critical/high findings remediated.
- [ ] Incident response plan including notifying Google for any Google-data incident.
- [ ] Data retention + deletion policy; subprocessor list + data processing terms; backup encryption.
- [ ] AI provider controls: contractual no-training on our data, zero/reduced retention if available, exact fields sent, quoted-thread/attachment stripping where not needed.

---

## Phase 5: Submit

- [ ] Final pre-submit gate: code requests only final scopes; Console lists only final scopes; connect/refresh/send/inbound/disconnect all pass in prod; all public pages live; demo video uploaded; packet ready; support mailbox monitored.
- [ ] In Google Cloud Console: open the OAuth consent screen / Google Auth Platform, confirm branding, audience (Production), authorized domains, and data-access scopes.
- [ ] Open the Verification Center, prepare for verification, enter the scope justifications, add the documentation links (home, privacy, Google-data/Limited Use, deletion), and the unlisted demo video link.
- [ ] Submit for verification. Record the submission date and case/reference in the log at the bottom.

---

## Phase 6: During review

- [ ] Reply to every Google reviewer email within one business day. Keep owner/support emails current.
- [ ] Do not change scopes unless Google asks. If asked why a narrower scope will not work, answer with API method names and product screens.
- [ ] If privacy language is flagged, update the public page and reply with the exact changed URL.
- [ ] If Google requires a security assessment, engage an approved CASA assessor promptly; remediate critical/high findings.
- [ ] Log every reviewer question and my response.

---

## Phase 7: After approval

- [ ] Save the approval email(s) and any Letter of Assessment.
- [ ] Record approved scopes + approval date in this file's log and in a release note.
- [ ] Confirm prod OAuth no longer shows the unverified-app warning for Gmail (and Calendar if covered).
- [ ] Re-run the prod Gmail smoke test (connect, inbound, AI draft, send, disconnect, token refresh, watch renewal).
- [ ] Enable Gmail for production tenants; monitor OAuth failures, webhook delivery, token refresh, watch renewal, send errors.
- [ ] Add a calendar reminder for annual restricted-scope reverification / security reassessment.
- [ ] Add an engineering rule: any new Gmail scope is a launch-blocking compliance change requiring re-review.

---

## Blocker and decision log

Record blockers `[!]` and decisions here as they resolve, so the state is never guessed.

| Date | Item | Status | Note |
| --- | --- | --- | --- |
| 2026-07-06 | Prod OAuth redirect URIs on old domain | Open | Must update to `api.prod.velvetelves.com` (Phase 3.1) before prod connect works |
| 2026-07-06 | `gmail.modify` unused | Decision | Code-verified unused; drop it (Phase 1) |
| 2026-07-06 | Public privacy policy Gmail-insufficient | Open | `/legal` covers marketing capture only; needs app + Google-data policy (Phase 2) |
| 2026-07-06 | `calendar.events` on same client | Open decision | Include Calendar in this submission or accept unverified Calendar warning (Phase 3.3) |
| 2026-07-06 | Legal entity / support mailbox | **Resolved** | Orange Door, LLP dba Velvet Elves (Indiana); `support@velvetelves.com` live via GoDaddy catchall now, Workspace mailbox later |
| 2026-07-06 | Workspace signup (K3 = yes) | In progress | Jake hit Google's 24h signup cooldown; on retry he sends me the `google-site-verification=` TXT and I add it in Route 53; same record verifies domain ownership (J6) |
| | Verification submission | Not started | Fill date + case ref on submit (Phase 5) |

---

## Official references (last checked 2026-05-13 in the guidelines doc)

- OAuth App Verification: https://support.google.com/cloud/answer/13463073
- Submitting for verification: https://support.google.com/cloud/answer/13461325
- Restricted scopes: https://support.google.com/cloud/answer/13464325
- Restricted-scope verification: https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification
- Google API Services User Data Policy (Limited Use): https://developers.google.com/terms/api-services-user-data-policy
- Gmail API push notifications: https://developers.google.com/workspace/gmail/api/guides/push
