# Gmail Integration Google Approval Guidelines

**Status:** Draft for production approval  
**Owner:** Jan (sole dev)  
**Last updated:** 2026-05-13  
**Related implementation:** `velvet-elves-backend/app/services/email/gmail_provider.py`, `velvet-elves-backend/app/api/v1/integrations.py`  
**Related project docs:** `MILESTONE_4_1_EMAIL_INTEGRATION_CONFIGURATION_GUIDE.md`, `GMAIL_PUBSUB_WEBHOOK_CONFIGURATION_GUIDE.md`, `MILESTONE_4_2_AI_EMAIL_WORKFLOW.md`, `SYSTEM_DESIGN.md`, `MULTI_TENANCY_IMPLEMENTATION_PLAN.md`

---

## 1. Executive Summary

Velvet Elves has completed Gmail integration testing, but production launch depends on Google OAuth approval. The current implementation requests:

```text
openid
email
profile
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.modify
```

The approval path should be treated as a restricted-scope Google OAuth review because `gmail.readonly` and `gmail.modify` are restricted Gmail scopes. `gmail.send` must also be declared and justified. Google Cloud Console is the source of truth for final scope classification after scopes are added to the production project.

Expected production path:

1. Freeze and minimize Gmail scopes.
2. Prepare public website, privacy policy, terms, and data deletion documentation.
3. Create or clean a production Google Cloud project.
4. Configure OAuth consent screen branding and production redirect URIs.
5. Submit brand/data-access verification with detailed scope justifications and an unlisted demo video.
6. Complete restricted-scope security assessment if Google requires it.
7. Launch only after Google approves the requested scopes.
8. Plan for annual reverification/security reassessment if restricted scopes remain in use.

Recommended planning window: **6 to 8 weeks minimum** before public production launch. Restricted-scope review and security assessment timing depends heavily on Google reviewer questions, assessor availability, and how quickly evidence is supplied.

---

## 2. Approval Goal For Velvet Elves

Google reviewers need to understand one clear story:

> Velvet Elves is a real-estate transaction coordination application. Gmail access lets an authenticated agent connect their own Gmail account, receive transaction-related inbound messages, match those messages to transaction records, generate human-reviewed AI drafts, send user-approved replies from the user's own mailbox, and maintain a communication audit trail for the transaction. Velvet Elves does not sell Google user data, use it for advertising, use it for generalized model training, or send emails without explicit user approval.

Keep every submission artifact aligned to that story. Avoid describing the product as "AI automation" in a way that suggests autonomous sending, bulk marketing, inbox scraping, or model training.

---

## 3. Current Gmail Implementation Inventory

### 3.1 User-facing features

The production approval packet should describe these features:

- Settings -> Integrations -> Connect Gmail.
- OAuth popup and callback through the backend.
- Encrypted token storage in the `integrations` table.
- Gmail Pub/Sub `users.watch` registration for inbound mail.
- Inbound Gmail notifications delivered to `/api/v1/integrations/email/webhook/gmail`.
- Gmail `history.list` delta sync from the stored `historyId`.
- Transaction matching and communication log creation.
- AI Email Review queue that drafts replies but requires human approval before send.
- Approve/Edit & Send using the user's connected Gmail account.
- Disconnect Gmail and stop future use of the user's mailbox.

### 3.2 Data touched by the integration

Document this exactly in the privacy policy and Google verification answers:

| Data type | Why Velvet Elves uses it | Storage behavior |
| --- | --- | --- |
| Gmail account email/profile | Show which mailbox is connected and route provider ownership | Provider email is encrypted at rest in `integrations` |
| OAuth access/refresh tokens | Call Gmail API on behalf of the connected user | Tokens are encrypted at rest |
| Gmail message metadata | Match inbound messages to transaction records and avoid duplicate processing | Persisted as communication log metadata where needed |
| Gmail message subject/body | Create transaction communication logs and draft user-facing replies | Persist only what is needed for transaction workflow and audit |
| Recipient/sender/CC fields | Send replies and preserve transaction communication history | Stored in communication logs according to retention policy |
| AI draft content | Let user review, edit, approve, send, or discard replies | Stored in communication logs/draft workflow; never sent without user action |

### 3.3 Current security controls to highlight

- OAuth Authorization Code flow with PKCE.
- HTTPS production callbacks and webhooks.
- Encrypted access tokens, refresh tokens, and provider emails.
- Tenant and role-scoped backend access.
- Communication logs tied to transaction context.
- AI drafts require explicit human approve/edit action before external send.
- Pub/Sub push JWT validation for Gmail webhook requests.
- Gmail `users.watch` metadata stores `historyId`, expiration, labels, and notification details.
- Gmail watch labels are scoped to `INBOX` for Milestone 4.1.
- No browser `localStorage` persistence of Gmail tokens.
- No Gmail data sale, advertising use, credit/lending use, or generalized AI model training.

---

## 4. Scope Minimization Before Submission

Google's minimum-scope requirement is one of the highest-friction review areas. Do this audit before submitting.

### 4.1 Required scope table

| Scope | Current reason | Approval risk | Action before submission |
| --- | --- | --- | --- |
| `openid` | User identity in OAuth flow | Low | Keep |
| `email` | Connected mailbox identity | Low | Keep |
| `profile` | Display connected account name/avatar | Low/medium | Keep only if UI truly displays profile info; otherwise remove |
| `gmail.send` | Send user-approved transaction replies from connected Gmail | Medium | Keep if outbound send remains core; emphasize human approval |
| `gmail.readonly` | Read inbound messages for transaction matching and AI draft context | High | Keep only if message body/content is needed; justify with AI Email Review workflow |
| `gmail.modify` | Broad read/modify/send capability | Very high | Remove unless the code must modify mailbox state, labels, or message read status |

### 4.2 Strong recommendation: remove `gmail.modify` unless required

The current code path appears to use:

- `users.watch`
- `users.history.list`
- `users.messages.get`
- `users.messages.send`

If Velvet Elves is not modifying labels, changing read/unread state, deleting, archiving, or moving messages, `gmail.modify` will be difficult to justify. Before production submission:

1. Search backend code for Gmail modify calls.
2. Remove `gmail.modify` from `GMAIL_SCOPES` if unused.
3. Re-test OAuth connect, inbound Pub/Sub, history sync, and outbound send.
4. Confirm Google Cloud Console scopes exactly match the code.

If message body is not required for current production behavior, consider whether `gmail.metadata` can replace `gmail.readonly`. It is still restricted, but it better supports a least-privilege story for metadata-only matching. If AI replies need the message body, keep `gmail.readonly` and justify it directly.

### 4.3 Avoid broad Gmail access

Do not request:

```text
https://mail.google.com/
```

That scope is too broad for Velvet Elves because the app should not need full mailbox access, permanent delete, IMAP, SMTP, POP3, or unrestricted mail management.

### 4.4 Freeze scopes during review

After submission:

- Do not add sensitive or restricted scopes in code.
- Do not add unverified OAuth clients to the production project.
- Do not change consent-screen scope descriptions without tracking the impact.
- If scope changes are unavoidable, pause rollout and expect re-review.

---

## 5. Public Website And Policy Requirements

Google reviewers need public, non-login pages that match the app identity shown on the OAuth consent screen.

### 5.1 Required public pages

Host these under the same authorized domain used for OAuth, preferably:

```text
https://velvetelves.com/
https://velvetelves.com/privacy
https://velvetelves.com/terms
https://velvetelves.com/google-data
https://velvetelves.com/data-deletion
https://velvetelves.com/support
```

Minimum contents:

- Home page: explains Velvet Elves as a real-estate transaction coordination app.
- Privacy policy: describes Google user data access, use, storage, sharing, retention, deletion, and AI processing.
- Terms of service: describes acceptable use and user responsibilities.
- Google data page: plain-English explanation of Gmail scopes and Limited Use commitment.
- Data deletion page: explains how users disconnect Gmail and request deletion.
- Support page: monitored support email that matches OAuth consent screen support contact.

### 5.2 Required Limited Use disclosure

Include this exact or near-exact statement in the privacy policy and/or `google-data` page:

> Velvet Elves' use and transfer of information received from Google APIs to any other app will adhere to the Google API Services User Data Policy, including the Limited Use requirements.

### 5.3 AI-specific disclosure

Because Gmail data can feed AI draft generation, disclose this clearly:

- Gmail content is used only to provide user-facing transaction coordination features.
- AI drafts are generated for the connected user/team to review.
- Velvet Elves does not train or improve foundation, generalized, or frontier models using Google user data.
- Google user data is not sold, used for ads, used for retargeting, or used to determine creditworthiness.
- Human users approve or edit drafts before any email is sent.
- Subprocessors that receive Google user data, including AI providers if applicable, are listed in the privacy policy or a subprocessor page.
- The user can disconnect Gmail and request deletion of stored Google-derived data.

### 5.4 Data deletion language

The deletion page should explain:

1. User can disconnect Gmail in Settings -> Integrations.
2. Disconnecting stops future Gmail API calls and disables Gmail-based send/receive.
3. User can revoke access from their Google Account security page.
4. User can request deletion by emailing support.
5. Velvet Elves deletes or anonymizes Google-derived communication data unless legal, compliance, audit, or transaction-record retention obligations require preserving it.
6. Deletion completion target, for example 30 days, should be stated and honored.

---

## 6. Google Cloud Project Setup

Use separate Google Cloud projects for development/testing and production. Submit only the production project for verification.

### 6.1 Production project checklist

- Create/select a production Google Cloud project.
- Enable Gmail API.
- Enable Pub/Sub API for Gmail push notifications.
- Configure OAuth consent screen as External unless the app is limited to one Google Workspace organization.
- Configure branding:
  - App name: `Velvet Elves`
  - App logo: production logo
  - User support email: monitored mailbox
  - Developer contact emails: at least two monitored addresses if possible
  - Home page URL
  - Privacy policy URL
  - Terms URL
  - Authorized domain: `velvetelves.com`
- Verify domain ownership in Google Search Console.
- Create a production OAuth web client.
- Add only production redirect URI:

```text
https://api.prod.velvetelves.com/api/v1/integrations/gmail/callback
```

- Keep local/dev redirect URIs in the dev project, not the production project.
- Remove OAuth clients that are not production-ready before submitting.
- Confirm the OAuth consent screen scopes match the code exactly.
- Publish app to production before preparing verification.

### 6.2 Pub/Sub production checklist

Production Pub/Sub details should match `GMAIL_PUBSUB_WEBHOOK_CONFIGURATION_GUIDE.md`.

- Topic:

```text
projects/<production-project-id>/topics/gmail-inbound-prod
```

- Push endpoint:

```text
https://api.prod.velvetelves.com/api/v1/integrations/email/webhook/gmail
```

- Pub/Sub push audience:

```text
https://api.prod.velvetelves.com/api/v1/integrations/email/webhook/gmail
```

- Gmail publisher service account has Pub/Sub Publisher on the topic:

```text
gmail-api-push@system.gserviceaccount.com
```

- Pub/Sub push service account is user-managed and dedicated to Gmail push.
- Pub/Sub service agent can mint OIDC tokens for the push service account.
- Backend validates the Pub/Sub OIDC JWT audience and service account email.
- Backend resolves Pub/Sub payload `emailAddress` to the active Gmail integration.
- Backend renews `users.watch` daily, before the 7-day expiration window.

---

## 7. OAuth Consent Screen Content

### 7.1 App description

Suggested app description:

> Velvet Elves helps real-estate agents and transaction coordinators manage transaction communications, documents, deadlines, and AI-assisted email drafts. When a user connects Gmail, Velvet Elves can receive transaction-related inbound messages, match them to transaction files, generate draft responses for human review, and send user-approved replies from the user's connected Gmail account.

### 7.2 Scope justifications

Use short, concrete justifications. Google reviewers prefer feature-specific explanations over broad product claims.

| Scope | Suggested justification |
| --- | --- |
| `openid`, `email` | Used to identify the Google account connected by the user and display the connected mailbox in Settings. |
| `profile` | Used to display the connected Google account name/avatar in the integration status UI. Remove this scope if the production UI does not need profile details. |
| `gmail.send` | Used only after the user clicks Approve & Send or Edit & Send in Velvet Elves. This sends a transaction-specific reply from the user's own Gmail mailbox and records the result in the transaction communication log. Velvet Elves does not send Gmail messages without explicit user action. |
| `gmail.readonly` | Used to read inbound transaction-related Gmail messages so Velvet Elves can create communication logs, match messages to transaction records, and prepare AI draft replies for user review. The feature is visible in the AI Email Review queue and transaction communication history. |
| `gmail.modify` | Use only if retained: required to apply or update Gmail labels/read status as part of the user's transaction workflow. If Velvet Elves does not modify mailbox state, remove this scope before submission. |

### 7.3 Reviewer-facing guardrail copy

Include this in optional notes if space allows:

> AI features in Velvet Elves draft and summarize transaction communications. They do not send email, change transaction data, or contact third parties unless a human user explicitly clicks the corresponding action. Gmail sends require Approve & Send or Edit & Send by the authenticated user.

---

## 8. Demo Video Script

Google requires a video that demonstrates the OAuth grant and how each requested sensitive/restricted scope is used. Record with a dedicated test Gmail account and seeded test transactions. Do not expose real client emails.

Recommended length: 6 to 10 minutes.

### 8.1 Setup before recording

- Use the production app URL or a staging URL that exactly matches the submitted OAuth client.
- Use a test Google account with safe test email content.
- Seed one transaction with a property address and parties.
- Prepare one inbound Gmail message from a test contact.
- Prepare one AI draft in pending review or show it generated from inbound flow.
- Ensure browser zoom is readable.
- Keep the browser address bar visible during OAuth consent.
- Show the app name on the Google consent screen.
- Show the OAuth client ID in the consent-screen URL if visible.

### 8.2 Recording outline

1. Open `https://velvetelves.com/`.
   - Show app name and a brief product description.
   - Open privacy policy and Google data page.
2. Sign in to Velvet Elves as a test agent.
3. Navigate to Settings -> Integrations.
4. Click Connect Gmail.
5. Complete Google OAuth consent.
   - Show requested permissions.
   - Say that the user is granting Velvet Elves access to send and read transaction-related Gmail data.
6. Return to Velvet Elves.
   - Show Gmail connected state and connected mailbox address.
7. Demonstrate inbound/read use.
   - Send or display a test inbound email.
   - Show Velvet Elves importing/logging it through Gmail/Pub/Sub.
   - Show the transaction communication log or AI Email Review queue.
   - Explain that this is why `gmail.readonly` is needed.
8. Demonstrate AI draft workflow.
   - Show generated draft.
   - Show safeguards and review state.
   - Edit the draft if useful.
   - Emphasize that the AI did not send the email.
9. Demonstrate send use.
   - Click Approve & Send or Edit & Send.
   - Show success toast/communication log.
   - Show the sent message in the test Gmail mailbox if available.
   - Explain that this is why `gmail.send` is needed.
10. If `gmail.modify` is retained, demonstrate the exact mailbox modification.
    - Example: applying a user-visible Velvet Elves label or marking a processed message.
    - If there is no such demo, remove the scope.
11. Demonstrate disconnect.
    - Return to Settings -> Integrations.
    - Disconnect Gmail.
    - Mention users can also revoke app access in their Google Account.
12. Close with data use statement.
    - No sale of Google data.
    - No advertising use.
    - No generalized model training.
    - User can request deletion.

### 8.3 Demo video mistakes to avoid

- Do not show real client PII.
- Do not skip the OAuth consent screen.
- Do not say "AI sends emails automatically."
- Do not show functionality unrelated to requested Gmail scopes.
- Do not request `gmail.modify` without showing exactly what mailbox state is modified.
- Do not use a dev OAuth client in the video while submitting a production client.
- Do not hide the app URL or consent-screen identity.

---

## 9. Security Assessment Readiness

Apps that access restricted Gmail data from or through servers should expect security assessment requirements. Prepare the evidence before Google asks for it.

### 9.1 Evidence packet

Create a folder for security evidence with:

- Architecture diagram: browser, FastAPI backend, Supabase, Gmail API, Pub/Sub, AI provider, email provider.
- Data flow diagram for Gmail connect, inbound sync, AI draft, send, disconnect, deletion.
- Scope inventory and API method mapping.
- Token storage design: encryption, key location, rotation plan, access controls.
- PII encryption design from `SYSTEM_DESIGN.md`.
- Multi-tenant access controls from `MULTI_TENANCY_IMPLEMENTATION_PLAN.md`.
- Production environment list: domains, API origin, database, storage, logging, monitoring.
- Vulnerability management process.
- Dependency scanning process.
- Secret management and rotation process.
- Incident response plan, including notification to Google for Google data incidents.
- Data retention and deletion policy.
- Employee/admin access policy for user email data.
- Subprocessor list and data processing agreements.
- Backup encryption and restoration process.
- Logging policy that avoids raw email bodies and token leakage.
- Recent test results for Gmail integration and multi-tenant isolation.

### 9.2 Technical hardening checklist

- Enforce HTTPS everywhere in production.
- Encrypt OAuth access tokens and refresh tokens at rest.
- Do not log OAuth tokens, authorization codes, refresh tokens, raw Pub/Sub JWTs, or full Gmail message bodies.
- Mask email addresses in operational logs where practical.
- Validate OAuth `state` and PKCE verifier.
- Validate Pub/Sub push JWT issuer, audience, signature, and service account email.
- Store Gmail `historyId` per integration and process deltas idempotently.
- Renew Gmail watches daily.
- Implement disconnect so the integration is deactivated and future Gmail API calls stop.
- Confirm no cross-tenant access path can read another user's integration or communication log.
- Ensure production service accounts have least privilege.
- Run dependency and container/server vulnerability scans.
- Patch critical/high findings before assessment.
- Keep a written incident response plan.

### 9.3 AI provider controls

If Gmail content is sent to an AI provider for drafting/summarization:

- Confirm the provider contract/API terms prevent training on Velvet Elves customer data.
- Configure any provider-side zero-retention or reduced-retention option if available.
- Document exactly what fields are sent to the AI provider.
- Strip unnecessary headers, quoted threads, signatures, and attachments when not needed.
- Do not send entire mailbox exports.
- Keep prompts transaction-specific and user-facing.
- Document that the AI output is a draft requiring human review.

---

## 10. Submission Workflow

### 10.1 Before submission

1. Decide final Gmail scopes.
2. Remove unused scopes from code and Google Cloud Console.
3. Re-test Gmail connect, inbound sync, AI draft, send, disconnect.
4. Verify production domain ownership.
5. Publish public policy pages.
6. Create production OAuth client.
7. Remove dev/local OAuth clients from the production Google Cloud project.
8. Confirm production redirect URI matches backend exactly.
9. Prepare demo video and upload it as unlisted.
10. Prepare scope justifications.
11. Prepare security evidence packet.
12. Identify who will monitor Google emails daily.

### 10.2 Submit in Google Cloud

In Google Cloud Console:

1. Open OAuth consent screen / Google Auth Platform.
2. Confirm branding.
3. Confirm audience is production.
4. Confirm authorized domains.
5. Confirm data access scopes.
6. Publish app to production if still in testing.
7. Open Verification Center.
8. Prepare for verification.
9. Enter scope justifications.
10. Add documentation links:
    - Home page
    - Privacy policy
    - Google data/Limited Use page
    - Data deletion page
11. Add unlisted YouTube demo video link.
12. Submit for verification.

### 10.3 During review

- Reply to Google reviewer emails within one business day.
- Keep project owner/editor and support emails current.
- Do not change scopes unless Google asks.
- If reviewers ask why a narrower scope is insufficient, answer with API method names and product screens.
- If Google flags privacy policy language, update public pages and reply with exact changed URLs.
- If Google asks for security assessment, contact approved CASA assessors promptly.
- Track every reviewer question and response in an internal log.

### 10.4 After approval

- Save approval emails and any Letter of Assessment.
- Record approved scopes and date in this document or a release log.
- Confirm OAuth no longer shows unverified-app warnings.
- Re-run production Gmail smoke tests.
- Add a calendar reminder for annual restricted-scope reverification/reassessment.
- Require engineering review before adding or changing Gmail scopes.

---

## 11. Launch Timeline

| Timing | Work |
| --- | --- |
| T-8 weeks | Freeze Gmail behavior. Audit scopes. Remove `gmail.modify` unless demonstrably required. |
| T-7 weeks | Publish privacy, Google data, deletion, terms, and support pages. Verify domain ownership. |
| T-6 weeks | Create production Google Cloud project/client. Configure production consent screen. Record demo video. |
| T-5 to T-6 weeks | Submit OAuth verification. Begin monitoring reviewer email daily. |
| T-4 weeks | Respond to Google questions. Update policy pages or video if requested. |
| T-3 to T-4 weeks | Start security assessment if Google requires it. Remediate critical/high findings. |
| T-2 weeks | Confirm approved scopes, production OAuth behavior, Pub/Sub delivery, and disconnect flow. |
| T-1 week | Run end-to-end Gmail production smoke test with test accounts. Freeze launch changes. |
| Launch | Enable Gmail for production tenants. Monitor OAuth failures, webhook delivery, token refresh, and send errors. |
| Post-launch | Review logs weekly for scope errors and watch renewal failures. Prepare annual reverification. |

---

## 12. Common Rejection Risks And Fixes

| Risk | Why Google may object | Fix |
| --- | --- | --- |
| `gmail.modify` requested but no mailbox modification is visible | Fails minimum-scope requirement | Remove it or add a real user-facing mailbox modification feature and demo it |
| Privacy policy is generic | Does not disclose Google data use clearly | Add Gmail-specific data access/use/storage/sharing/deletion language |
| Limited Use statement is missing | Required for Google user data policy alignment | Add exact Limited Use disclosure to privacy or Google data page |
| Demo video only shows login | Does not show how each scope is used | Show connect, inbound read, AI draft, send, disconnect |
| AI workflow sounds autonomous | Google may fear unconsented sends or data misuse | Emphasize human approval before every send |
| Gmail data goes to AI provider without disclosure | Data transfer must be disclosed and policy-compliant | Add subprocessor and AI data-use disclosure |
| Dev/local OAuth clients remain in production project | All clients in submitted project must be production-ready | Move dev clients to separate dev project |
| Authorized domains are not verified | Consent screen cannot be trusted | Verify `velvetelves.com` in Search Console |
| App sends bulk marketing | Gmail scopes cannot be used for spam/unsolicited commercial mail | Limit Gmail send to transaction-specific, user-approved communication |
| Logs contain full Gmail bodies or tokens | Security assessment finding | Redact logs and confirm token/body logging is blocked |
| No data deletion process | Restricted review/security assessment issue | Publish deletion page and implement support procedure |

---

## 13. Production Readiness Checklist

### Scope and code

- [ ] Final scope list is documented.
- [ ] Code requests only final scopes.
- [ ] Google Cloud Console lists only final scopes.
- [ ] `gmail.modify` is removed unless demonstrated.
- [ ] OAuth connect works in production.
- [ ] Token refresh works.
- [ ] Gmail send works.
- [ ] Gmail inbound Pub/Sub works.
- [ ] Gmail watch renewal exists and is monitored.
- [ ] Disconnect stops future Gmail use.

### Public pages

- [ ] Home page is public.
- [ ] Privacy policy is public.
- [ ] Terms are public.
- [ ] Google data/Limited Use page is public.
- [ ] Data deletion page is public.
- [ ] Support page or support email is public and monitored.
- [ ] Domains match authorized domains.

### Google Cloud

- [ ] Production project is separate from dev/test.
- [ ] Gmail API enabled.
- [ ] Pub/Sub API enabled.
- [ ] OAuth consent screen is complete.
- [ ] Branding is complete.
- [ ] Authorized domain is verified.
- [ ] Production OAuth client has exact callback URI.
- [ ] No local/dev redirect URI in production client.
- [ ] Pub/Sub topic/subscription/service account are production-scoped.

### Verification packet

- [ ] Scope justifications prepared.
- [ ] Demo video recorded and unlisted.
- [ ] Demo video shows every requested sensitive/restricted scope.
- [ ] Security evidence packet prepared.
- [ ] Subprocessor list prepared.
- [ ] Owner/editor/support emails monitored.

### Security

- [ ] OAuth tokens encrypted at rest.
- [ ] Gmail-derived data encrypted at rest where appropriate.
- [ ] Tenant isolation tests pass.
- [ ] No token leakage in logs.
- [ ] No raw email body logging.
- [ ] Vulnerability/dependency scans run.
- [ ] Incident response plan exists.
- [ ] Data deletion process exists.
- [ ] AI provider data-use controls documented.

---

## 14. Suggested Reviewer Responses

### Why do you need Gmail read access?

Velvet Elves reads inbound Gmail messages only after a user connects Gmail. The app uses those messages to create transaction communication logs, match emails to the user's real-estate transaction records, and generate draft replies in the AI Email Review queue. The feature is visible to the user in transaction history and review screens. Drafts are not sent until the user approves or edits them.

### Why do you need Gmail send access?

Velvet Elves sends Gmail messages only when the authenticated user clicks Approve & Send or Edit & Send. The message is transaction-specific, sent from the user's connected Gmail account, and logged in the transaction communication history. Velvet Elves does not send autonomous or bulk marketing emails.

### Why do you need Gmail modify access?

Use only if true:

Velvet Elves uses `gmail.modify` to apply/update user-visible Gmail mailbox state as part of the transaction workflow. The demo video shows the exact user-facing mailbox modification.

If that answer is not true, remove `gmail.modify`.

### How do users delete their data?

Users can disconnect Gmail in Settings -> Integrations, revoke access in their Google Account, and request deletion through the public data deletion/support page. Velvet Elves deletes or anonymizes Google-derived data unless transaction-record retention, legal, compliance, or audit obligations require keeping specific records.

### Does AI train on Gmail content?

No. Gmail content is used only to provide user-facing transaction coordination features such as summarization and draft generation for that user/team. It is not sold, used for advertising, used for generalized/foundation model training, or used outside the requested feature.

---

## 15. Operational Maintenance After Approval

- Keep a permanent record of approved scopes and approval date.
- Re-run a scope audit before each major Gmail-related release.
- Track Google policy updates quarterly.
- Monitor Gmail OAuth callback failures.
- Monitor token refresh failures.
- Monitor Pub/Sub delivery failures.
- Monitor Gmail `users.watch` renewal failures.
- Keep privacy policy and subprocessor list current.
- Keep support and developer contact emails current.
- Schedule annual restricted-scope reverification/security reassessment.
- Treat any new Gmail scope as a launch-blocking compliance change.

---

## 16. Official References

Last checked: 2026-05-13.

- OAuth App Verification Help Center: https://support.google.com/cloud/answer/13463073
- Submitting your app for verification: https://support.google.com/cloud/answer/13461325
- Restricted scopes: https://support.google.com/cloud/answer/13464325
- Sensitive scope verification: https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification
- Restricted scope verification: https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification
- OAuth 2.0 scopes for Google APIs: https://developers.google.com/identity/protocols/oauth2/scopes
- Google API Services User Data Policy: https://developers.google.com/terms/api-services-user-data-policy
- Google Workspace API User Data and Developer Policy: https://developers.google.com/workspace/workspace-api-user-data-developer-policy
- Gmail API push notifications: https://developers.google.com/workspace/gmail/api/guides/push
- OAuth verification FAQ: https://support.google.com/cloud/answer/13463817

