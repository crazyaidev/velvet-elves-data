# Milestone 4.1 — Email Integration Configuration Guide

Last reviewed: 2026-05-06

This guide lists every external configuration needed to close out **Milestone 4.1 — Email Integration (Week 14)** in [milestones.txt](milestones.txt). The backend code (OAuth services, provider implementations, inbound dispatch, retention purge) is already implemented — what remains is registering apps with Google / Microsoft, generating credentials, wiring up webhooks for inbound mail, and setting the matching environment variables.

It is structured the same way as [DOCUSIGN_SETUP_GUIDE.md](DOCUSIGN_SETUP_GUIDE.md): for each provider you'll go to a developer portal, register redirect URIs, copy a client ID + secret into `.env`, and confirm the in-app "Connect" button works end-to-end.

---

## Environment summary

| Item | Local development | Shared dev (EC2) |
| --- | --- | --- |
| Frontend origin | `http://localhost:5173` | `https://dev.velvetelves.com` |
| Backend origin | `http://localhost:8000` | `https://dev.velvetelves.com` |
| Gmail OAuth callback | `http://localhost:8000/api/v1/integrations/gmail/callback` | `https://dev.velvetelves.com/api/v1/integrations/gmail/callback` |
| Outlook OAuth callback | `http://localhost:8000/api/v1/integrations/outlook/callback` | `https://dev.velvetelves.com/api/v1/integrations/outlook/callback` |
| Gmail inbound webhook (Pub/Sub push) | `https://<ngrok-tunnel>/api/v1/integrations/email/webhook/gmail` | `https://dev.velvetelves.com/api/v1/integrations/email/webhook/gmail` |
| Outlook inbound webhook (Graph subscription) | `https://<ngrok-tunnel>/api/v1/integrations/email/webhook/outlook` | `https://dev.velvetelves.com/api/v1/integrations/email/webhook/outlook` |

The OAuth callback URI must match what is registered in the provider portal **character for character** (trailing slash, http vs https, host). Inbound webhook URIs must be HTTPS — Google and Microsoft both refuse plain-HTTP receivers, so for local development you'll need an ngrok tunnel (or skip inbound testing and rely on the dev EC2 box for webhook flows).

---

## Required `.env` keys (backend)

These are the keys the backend reads ([config.py](../velvet-elves-backend/app/core/config.py)). Add them to [.env](../velvet-elves-backend/.env) on each environment. The example file at [.env.example](../velvet-elves-backend/.env.example) does not currently list the email keys — append the block below to it as part of this milestone so future operators don't have to rediscover them.

```env
# ── Email providers (Milestone 4.1) ────────────────────────────────────────
# Gmail (Google Cloud OAuth client)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
# Optional override; when empty the backend derives the redirect URI from the
# inbound request URL. Set this in production to lock the value.
GMAIL_REDIRECT_URI=

# Outlook (Microsoft Azure App Registration)
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
# 'common' = personal + work/school. Set to a tenant GUID to restrict.
MICROSOFT_TENANT=common
OUTLOOK_REDIRECT_URI=

# Shared secret for inbound webhook receivers (Gmail Pub/Sub, MS Graph).
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
EMAIL_WEBHOOK_SECRET=
# Optional HTTPS public origin for inbound webhook callbacks. Use this when
# the OAuth callback is local but Graph/Pub/Sub must reach an ngrok URL.
EMAIL_WEBHOOK_PUBLIC_BASE_URL=

# Communication-log retention (days). Default 730 = 2 years per req 6.1.
COMMUNICATION_RETENTION_DAYS=730
```

Behaviour when the keys are blank:

- Gmail / Outlook OAuth start endpoints return **HTTP 503** with an actionable message ("set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"). The rest of the app keeps working.
- iCloud has no env vars — it uses an app-specific password the user pastes into the connect form.
- `EMAIL_WEBHOOK_SECRET` blank means the inbound webhook accepts unsigned requests. **Always set this in dev and prod** so a public webhook URL cannot be used to flood the communication log.
- `EMAIL_WEBHOOK_PUBLIC_BASE_URL` blank means webhook URLs are derived from the incoming backend request. Set it to an HTTPS ngrok origin for local inbound testing, or to `https://dev.velvetelves.com` on shared dev if the callback is reached through a different host.

---

## Step 1: Gmail (Google Cloud OAuth)

The Gmail provider uses **OAuth 2.0 Authorization Code Grant with PKCE** ([gmail_provider.py](../velvet-elves-backend/app/services/email/gmail_provider.py)). The scopes requested are `gmail.send`, `gmail.readonly`, `gmail.modify`, plus `openid email profile` for the userinfo lookup.

### 1a. Create the project (one time)

1. Open https://console.cloud.google.com/projectcreate.
2. Project name: `Velvet Elves`. Organisation: leave default. Click **Create**.
3. Switch the top-bar project picker to the new project.

### 1b. Enable the Gmail API

1. https://console.cloud.google.com/apis/library/gmail.googleapis.com → **Enable**.
2. Also enable **People API** (used by the userinfo endpoint) at https://console.cloud.google.com/apis/library/people.googleapis.com.

### 1c. Configure the OAuth consent screen

1. https://console.cloud.google.com/apis/credentials/consent.
2. User type: **External**. Click **Create**.
3. Fill in:
   - App name: `Velvet Elves`
   - User support email: a real mailbox you control
   - App logo: `velvet-elves-data/logo.png` (optional but recommended before going live)
   - Developer contact: same as user support email
4. **Scopes** screen → **Add or remove scopes** and select:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.modify`
5. **Test users** → add Jan's and Audri's Gmail addresses (anyone connecting before app verification must be a test user).
6. Save. Leave the app in **Testing** publishing status until production launch — this is sufficient for local + EC2 dev.

### 1d. Create the OAuth client ID

1. https://console.cloud.google.com/apis/credentials → **Create credentials** → **OAuth client ID**.
2. Application type: **Web application**.
3. Name: `Velvet Elves Backend`.
4. **Authorized JavaScript origins** — leave empty (the backend, not the SPA, is the OAuth client).
5. **Authorized redirect URIs** — add **all four**:
   ```
   http://localhost:8000/api/v1/integrations/gmail/callback
   https://dev.velvetelves.com/api/v1/integrations/gmail/callback
   ```
   Add the production URL later when [DOCUSIGN_SETUP_GUIDE.md](DOCUSIGN_SETUP_GUIDE.md)'s Step 8 / Promote-to-Production pattern is applied.
6. Click **Create**. Copy the **Client ID** and **Client secret** that appear in the modal.

### 1e. Wire to `.env`

```env
GOOGLE_CLIENT_ID=<paste from step 1d>
GOOGLE_CLIENT_SECRET=<paste from step 1d>
GMAIL_REDIRECT_URI=https://dev.velvetelves.com/api/v1/integrations/gmail/callback   # EC2 only
```

For local dev leave `GMAIL_REDIRECT_URI` blank — the backend derives it from `request.url_for("gmail_oauth_callback")`.

### 1f. Inbound mail (Gmail Pub/Sub)

Gmail does not POST inbound messages directly to a webhook; you subscribe a Cloud Pub/Sub topic to a user's mailbox via `users.watch`, and Pub/Sub pushes notifications to the backend. The backend webhook route [`POST /api/v1/integrations/email/webhook/gmail`](../velvet-elves-backend/app/api/v1/integrations.py) already accepts the Pub/Sub envelope and re-fetches recent messages.

1. Create a Pub/Sub topic:
   - https://console.cloud.google.com/cloudpubsub/topic/list → **Create topic**.
   - Topic ID: `velvet-elves-gmail-inbound`. Leave **Add a default subscription** unchecked.
2. Grant Gmail's service account permission to publish:
   - Topic detail page → **Permissions** → **Add principal**.
   - Principal: `gmail-api-push@system.gserviceaccount.com`
   - Role: `Pub/Sub Publisher`
3. Create a **push subscription** that delivers to the backend webhook:
   - **Subscriptions** → **Create subscription**.
   - Subscription ID: `velvet-elves-gmail-push-dev`
   - Topic: `velvet-elves-gmail-inbound`
   - Delivery type: **Push**
   - Endpoint URL:
     ```
     https://dev.velvetelves.com/api/v1/integrations/email/webhook/gmail?user_id={USER_ID}
     ```
     For local dev replace the host with your ngrok tunnel. The `user_id` query parameter is required by the webhook handler so we can resolve the right mailbox.
   - **Authentication**: enable **Use authentication header**, then use the OIDC token approach **or** add a custom header `X-VE-Webhook-Secret: <EMAIL_WEBHOOK_SECRET>`. The current backend reads `X-VE-Webhook-Secret`; if you'd rather rely on Google's OIDC token signature, that requires an additional verification helper that's out of scope for this milestone.
4. Per-user `users.watch` registration is performed by the backend after a successful Gmail OAuth connect. (If you find this is not yet implemented, add a follow-up task: after `gmail_oauth_callback` persists tokens, call `POST gmail.users.watch` with `topicName=projects/<gcp-project>/topics/velvet-elves-gmail-inbound`, then renew the watch every 7 days via the existing scheduler.)

> **Local dev shortcut:** if you don't need to test inbound during local dev, skip Step 1f entirely. Outbound send and the OAuth handshake work without it. Wire Pub/Sub on the EC2 dev box only.

---

## Step 2: Outlook (Microsoft Azure App Registration)

The Outlook provider uses Microsoft Identity Platform v2 with PKCE ([outlook_provider.py](../velvet-elves-backend/app/services/email/outlook_provider.py)). Scopes requested: `Mail.Send`, `Mail.Read`, `Mail.ReadWrite`, `User.Read`, plus `openid profile email offline_access`.

### 2a. Register the app

1. Sign in at https://entra.microsoft.com/ as a directory admin (Audri's account, since she owns the tenant).
2. **App registrations** → **New registration**.
3. Name: `Velvet Elves Email Connector`.
4. Supported account types: **Accounts in any organizational directory and personal Microsoft accounts** (matches `MICROSOFT_TENANT=common`).
5. **Redirect URI** → platform: **Web**, value:
   ```
   http://localhost:8000/api/v1/integrations/outlook/callback
   ```
6. Click **Register**. Copy the **Application (client) ID** that appears on the overview page.

### 2b. Add the second redirect URI

1. App overview → **Authentication** → **Add a platform** → **Web** (skip if Web already exists).
2. Add:
   ```
   https://dev.velvetelves.com/api/v1/integrations/outlook/callback
   ```
3. Under **Implicit grant and hybrid flows**, leave both checkboxes off — we only use Authorization Code with PKCE.
4. Save.

### 2b.1. Troubleshoot `unauthorized_client`

If the Outlook popup shows:

> We're unable to complete your request  
> `unauthorized_client: The client does not exist or is not enabled for consumers.`

This is almost always an Azure app-registration audience mismatch, not a Velvet Elves backend or webhook error.

Check these items in order:

1. Confirm `.env` is using the **Application (client) ID** from the app's Overview page:
   ```env
   MICROSOFT_CLIENT_ID=<Application (client) ID>
   ```
   Do not paste the client secret ID, object ID, directory ID, or secret value into `MICROSOFT_CLIENT_ID`.
2. Decide which kind of Outlook account you are connecting:
   - For personal Outlook / Hotmail / Live accounts, the app registration must support **Accounts in any organizational directory and personal Microsoft accounts**. In the manifest this is `signInAudience: AzureADandPersonalMicrosoftAccount`.
   - For work/school accounts from any tenant, the app registration can support **Accounts in any organizational directory**. In the manifest this is `signInAudience: AzureADMultipleOrgs`.
   - For accounts only in Audri's tenant, the app registration can be **single tenant**, but then `MICROSOFT_TENANT` should be Audri's tenant GUID instead of `common`, and the user must sign in with a work/school account from that tenant.
3. Because this guide's default `.env` uses:
   ```env
   MICROSOFT_TENANT=common
   ```
   the safest app registration setting is **Accounts in any organizational directory and personal Microsoft accounts**. `common` allows the user to choose either a work/school account or a personal Microsoft account, but personal accounts only work when the app's supported account type includes consumers.
4. If the app was created with the wrong supported account type, fix it in **App registrations -> Velvet Elves Email Connector -> Manifest** by changing `signInAudience`, or create a new app registration with the correct account type and copy the new **Application (client) ID** and secret into `.env`.
5. Restart the backend after changing `.env`.
6. Retry from a fresh browser session or incognito window so Microsoft does not silently reuse a previously selected personal/work account.

Quick decision table:

| Account you want to connect | Azure supported account type | `.env` `MICROSOFT_TENANT` |
| --- | --- | --- |
| Personal Outlook / Hotmail / Live | Any org directory + personal Microsoft accounts | `common` |
| Work/school account in any tenant | Any org directory, or any org directory + personal | `common` or `organizations` |
| Work/school account only in one tenant | Single tenant | `<Directory (tenant) ID>` |

### 2c. Create a client secret

1. **Certificates & secrets** → **New client secret**.
2. Description: `velvet-elves-dev`. Expiry: 24 months (max). Click **Add**.
3. Copy the **Value** column **immediately** — Azure hides it after navigating away.

### 2d. Configure API permissions

1. **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions**.
2. Tick: `Mail.Send`, `Mail.Read`, `Mail.ReadWrite`, `User.Read`, `offline_access`, `openid`, `profile`, `email`.
3. Click **Add permissions**.
4. Click **Grant admin consent for <tenant>**. The "Status" column flips to a green check.

### 2e. Wire to `.env`

```env
MICROSOFT_CLIENT_ID=<Application (client) ID from 2a>
MICROSOFT_CLIENT_SECRET=<Value from 2c>
MICROSOFT_TENANT=common
OUTLOOK_REDIRECT_URI=https://dev.velvetelves.com/api/v1/integrations/outlook/callback   # EC2 only
```

### 2f. Inbound mail (Microsoft Graph subscription)

Graph inbound mail works differently from outbound send. For outbound, the backend calls Graph when a user clicks **Send**. For inbound, the backend must first create a per-user Microsoft Graph **subscription**. While that subscription is active, Graph POSTs a small notification to our webhook whenever a new Inbox message is created; the backend then fetches the full message with the connected user's Graph token and logs it through `inbound_dispatch.py`.

Important rules:

- Graph requires the `notificationUrl` to be public HTTPS. It cannot call `localhost`, plain `http://`, or a private VPC-only URL.
- The webhook URL includes `?user_id=<Velvet-Elves-user-id>`. Microsoft Graph preserves query parameters when it delivers notifications, so the backend can resolve the correct connected mailbox.
- The backend creates the subscription automatically during `outlook_oauth_callback` only if it can build an HTTPS webhook URL.
- `EMAIL_WEBHOOK_SECRET` is sent to Graph as `clientState`; inbound Graph notifications are accepted only when each notification's `clientState` matches that secret.
- Graph validates the webhook during subscription creation by POSTing `?validationToken=...` to the notification URL. The backend must return the decoded token as `text/plain` within 10 seconds. This is already implemented in `email_inbound_webhook`.

What the backend sends to Graph after Outlook OAuth succeeds:

```http
POST https://graph.microsoft.com/v1.0/subscriptions
Content-Type: application/json
Authorization: Bearer <connected-user-access-token>

{
  "changeType": "created",
  "notificationUrl": "https://<public-backend-origin>/api/v1/integrations/email/webhook/outlook?user_id=<user_id>",
  "resource": "me/mailFolders('Inbox')/messages",
  "expirationDateTime": "<now + 70 hours, ISO-8601>",
  "clientState": "<EMAIL_WEBHOOK_SECRET>",
  "latestSupportedTlsVersion": "v1_2"
}
```

#### Local development with inbound testing

Use this path only when you need to prove reply/inbound logging locally. If you only need OAuth and outbound send locally, skip inbound testing and use the production/shared-dev path later.

1. Run the backend locally on port 8000.
2. Start an HTTPS tunnel to the backend, for example:
   ```powershell
   ngrok http 8000
   ```
3. Copy the HTTPS ngrok origin only, not the full path. Example:
   ```env
   EMAIL_WEBHOOK_PUBLIC_BASE_URL=https://abc123.ngrok-free.app
   ```
4. Keep local OAuth callbacks local:
   ```env
   OUTLOOK_REDIRECT_URI=
   ```
   With this blank, the backend derives `http://localhost:8000/api/v1/integrations/outlook/callback` for local OAuth. That redirect URI must already be registered in the Microsoft app.
5. Set a webhook secret:
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Then paste it into:
   ```env
   EMAIL_WEBHOOK_SECRET=<generated-secret>
   ```
6. Restart the backend so `.env` is reloaded.
7. In the frontend, disconnect and reconnect Outlook. Reconnect is required because subscription creation happens during the Outlook OAuth callback.
8. Confirm the integration row has subscription metadata:
   - `metadata_json.outlook_subscription.id`
   - `metadata_json.outlook_subscription.expirationDateTime`
   - `metadata_json.outlook_subscription.notificationUrl`
9. Send a test email to the connected Outlook account. The webhook should receive a Graph notification, fetch the message from Graph, and create an inbound `communication_logs` row.

Local troubleshooting:

- If `metadata_json.outlook_subscription_skipped_reason` is `notification_url_must_be_https`, `EMAIL_WEBHOOK_PUBLIC_BASE_URL` was blank or not HTTPS when Outlook was connected.
- If `metadata_json.outlook_subscription_error` mentions validation, confirm the ngrok tunnel is running and points to the backend port, then reconnect Outlook.
- If the ngrok URL changes, update `EMAIL_WEBHOOK_PUBLIC_BASE_URL`, restart the backend, and reconnect Outlook. Existing subscriptions still point to the old ngrok URL.
- If `EMAIL_WEBHOOK_SECRET` changes, reconnect Outlook so the Graph subscription's `clientState` uses the new value.

#### Shared dev / production

Use this path on EC2 shared dev and production because the deployed backend already has a stable HTTPS origin.

1. Set the OAuth callback explicitly:
   ```env
   OUTLOOK_REDIRECT_URI=https://dev.velvetelves.com/api/v1/integrations/outlook/callback
   ```
   For production, replace the host with the production hostname after it is final.
2. Set the public webhook origin explicitly:
   ```env
   EMAIL_WEBHOOK_PUBLIC_BASE_URL=https://dev.velvetelves.com
   ```
   This may be left blank only if the backend receives the Outlook OAuth callback through the same public HTTPS host that Graph should call. Explicit is safer for deployed environments.
3. Set `EMAIL_WEBHOOK_SECRET` to a strong generated value.
4. Deploy/restart the backend.
5. Connect or reconnect Outlook from the UI. The callback creates the Graph subscription and stores the subscription response under `integrations.metadata_json.outlook_subscription`.
6. Schedule daily renewal as an admin-authenticated HTTP call:
   ```cron
   # Run daily at 04:00 UTC. Replace $ADMIN_BEARER_TOKEN with a valid admin JWT
   # or call this from a small script that signs in as the service admin first.
   0 4 * * * curl -X POST \
     -H "Authorization: Bearer $ADMIN_BEARER_TOKEN" \
     https://dev.velvetelves.com/api/v1/integrations/outlook/subscriptions/renew-due
   ```
   The endpoint renews Outlook subscriptions expiring within 24 hours by PATCHing Graph and updating `metadata_json.outlook_subscription.expirationDateTime`.
7. Monitor renewal output. A healthy response looks like:
   ```json
   {
     "checked": 3,
     "renewed": 1,
     "skipped": 2,
     "failed": 0,
     "errors": []
   }
   ```

Production troubleshooting:

- If subscription creation fails, check backend logs around `Outlook connected but Graph subscription creation failed`.
- If Graph validation fails, confirm the public route returns the validation token:
  ```powershell
  Invoke-WebRequest `
    -Uri "https://dev.velvetelves.com/api/v1/integrations/email/webhook/outlook?validationToken=test-token" `
    -Method POST `
    -UseBasicParsing
  ```
  Expected body: `test-token`, content type: `text/plain`.
- If notifications are received but no logs appear, confirm `EMAIL_WEBHOOK_SECRET` matches the subscription `clientState`, the integration is active, and the connected account still has `Mail.Read`.
- If a user disconnects Outlook, Graph may still retry old notifications briefly; the backend returns an accepted no-op when there is no active integration.

> Same caveat as Gmail: inbound mail is optional for local development. Outbound send and the OAuth handshake work without a public webhook tunnel.

---

## Step 3: iCloud (no portal — app-specific password)

Apple does not offer a generic OAuth API for iCloud Mail. The supported pattern is an **app-specific password** against `smtp.mail.me.com:587` (outbound) and `imap.mail.me.com:993` (inbound), implemented in [icloud_provider.py](../velvet-elves-backend/app/services/email/icloud_provider.py).

There is no admin-side configuration for this milestone. Each end user goes through the in-app **Connect iCloud** flow:

1. User signs into https://account.apple.com/.
2. **Sign-In and Security** → **App-Specific Passwords** → **+** to generate a new password labelled `Velvet Elves`.
3. Pastes the generated password into the **Connect iCloud** modal in the Velvet Elves frontend along with their iCloud email address.
4. Backend stores the password Fernet-encrypted in the `integrations.access_token` column.

What you, as the operator, need to confirm:

- The deployment target's outbound network allows TCP `587` to `smtp.mail.me.com` (some VPCs block SMTP). On EC2 dev, confirm the security group permits egress on `587`.
- The IMAP poller (used because Apple has no push notifications) is scheduled. The MVP path is "user-triggered refresh" — schedule a `POST /api/v1/integrations/email/refresh-inbound?provider=icloud` cron entry every 15 minutes once the endpoint exists; if it doesn't, treat it as a follow-up under Milestone 4.1.

---

## Step 4: Inbound webhook secret

The webhook receiver uses `EMAIL_WEBHOOK_SECRET` differently per provider ([integrations.py](../velvet-elves-backend/app/api/v1/integrations.py) — `email_inbound_webhook`): Gmail Pub/Sub checks the `X-VE-Webhook-Secret` header, while Microsoft Graph checks each notification's `clientState`.

```powershell
# Generate a secret on Windows
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add the value to `.env` on each environment **and** to the Pub/Sub push attributes (Step 1f) and Graph subscription `clientState` (Step 2f). Do **not** check the secret into git or commit it to `.env.example`.

---

## Step 5: Communication-log retention (2-year quarterly purge)

Per req 6.1 and the Milestone 4.1 success criterion, communication logs are purged when older than 2 years from the tenant's last user login. The implementation is in [communication_export.py](../velvet-elves-backend/app/services/communication_export.py) (`purge_expired_communications`) and exposed at `POST /api/v1/admin/communication-logs/purge-now` for manual fulfillment.

What's left to configure:

1. **Confirm the env default.** The `.env` should leave `COMMUNICATION_RETENTION_DAYS` unset (defaults to 730). Override only for tests.
2. **Schedule the quarterly cron.** On the EC2 dev box, add a quarterly job:
   ```cron
   # crontab -e (run every quarter, 03:00 UTC on the 1st of Jan/Apr/Jul/Oct)
   0 3 1 1,4,7,10 * curl -X POST -H "X-VE-Admin-Secret: $VE_ADMIN_SECRET" \
       https://dev.velvetelves.com/api/v1/admin/communication-logs/purge-now
   ```
   If the admin endpoint requires a Supabase JWT instead of a shared secret, swap the cron entry for a small Python script that signs in as a service-role admin and POSTs.
3. **Document the rollback.** The purge is `DELETE` against `communication_logs`; rows are not soft-deleted. Confirm Supabase nightly backups are enabled before letting the cron fire in production.

---

## Step 6: Frontend — what the UI expects

The frontend already has the connect surfaces wired ([useIntegrations.ts](../velvet-elves-frontend/src/hooks/useIntegrations.ts), [SettingsPage.tsx](../velvet-elves-frontend/src/pages/settings/SettingsPage.tsx), [OnboardingWizard.tsx](../velvet-elves-frontend/src/pages/auth/OnboardingWizard.tsx)). Verify the env at [.env](../velvet-elves-frontend/.env) on each environment points to the correct backend:

```env
VITE_API_BASE_URL=http://localhost:8000        # local
VITE_API_BASE_URL=https://dev.velvetelves.com  # EC2 dev
VITE_APP_ENV=development
```

No additional frontend env keys are needed for Milestone 4.1 — the OAuth handshakes are popup → backend callback → `postMessage` back to the opener (same pattern as DocuSign in Milestone 3.4).

---

## Step 7: Smoke-test checklist

Before marking Milestone 4.1 complete, walk through this on **both** local and EC2 dev:

| # | Action | Expected result |
|---|--------|-----------------|
| 1 | Restart the backend after editing `.env` | Server log shows no warnings about missing `GOOGLE_CLIENT_ID` / `MICROSOFT_CLIENT_ID` |
| 2 | Sign in as a test user → **Settings → Integrations → Connect Gmail** | Popup opens to `accounts.google.com`; consent screen lists Velvet Elves and the requested scopes |
| 3 | Approve consent | Popup closes; integrations list shows Gmail with the connected email |
| 4 | **Send test email** from the Communication tab on a transaction | Recipient receives the message; `communication_logs` row created with `direction='outbound'`, `status='sent'`, `provider_name='gmail'`, `provider_ref_id` populated |
| 5 | Reply to that email from the recipient mailbox | Backend logs an inbound row within ~1 minute (Pub/Sub) or after the next poll (iCloud); `transaction_id` is auto-matched by sender address |
| 6 | Repeat 2–5 with **Connect Outlook** | Same outcome via Microsoft Graph |
| 7 | Generate an iCloud app-specific password and run **Connect iCloud** | Modal accepts password; outbound send via iCloud succeeds; IMAP fetch returns recent messages |
| 8 | Hit `POST /admin/communication-logs/purge-now` with `COMMUNICATION_RETENTION_DAYS=1` and a tenant whose last login is 2 days old | Endpoint returns `{ rows_purged: > 0 }`; reset to 730 afterwards |
| 9 | Hit a webhook URL with a wrong `X-VE-Webhook-Secret` | Returns 401 |
| 10 | Disconnect each provider via the UI | Integration row flips `is_active=false`; subsequent send returns 409 with `EmailProviderUnavailable` message |

---

## Production hand-off (Phase 7)

These items don't block Milestone 4.1 acceptance but should be tracked as production blockers when Milestone 7.2 (Production Deployment) opens:

- Promote the Google Cloud project's OAuth consent screen from **Testing** to **In production** (requires Google verification of the requested scopes — start the review 4–6 weeks before launch).
- Add the production redirect URIs to both Google and Microsoft apps once the production hostname is finalised.
- Create a separate Microsoft client secret with a 24-month expiry and document its rotation date.
- Replace `MICROSOFT_TENANT=common` with the production tenant GUID if the launch tenant is enterprise-only.
- Confirm Supabase production backups before enabling the quarterly purge cron.
- Document `EMAIL_WEBHOOK_SECRET` rotation procedure (rotate the env var, then update Pub/Sub push attributes and Graph subscription `clientState`).

---

## Appendix A: where each piece lives in code

| Concern | File |
| --- | --- |
| Env vars + defaults | [app/core/config.py](../velvet-elves-backend/app/core/config.py) |
| Gmail OAuth + send/list | [app/services/email/gmail_provider.py](../velvet-elves-backend/app/services/email/gmail_provider.py) |
| Outlook OAuth + send/list | [app/services/email/outlook_provider.py](../velvet-elves-backend/app/services/email/outlook_provider.py) |
| iCloud SMTP/IMAP | [app/services/email/icloud_provider.py](../velvet-elves-backend/app/services/email/icloud_provider.py) |
| Provider factory + token refresh | [app/services/email/factory.py](../velvet-elves-backend/app/services/email/factory.py) |
| Inbound dispatch + transaction matching | [app/services/email/inbound_dispatch.py](../velvet-elves-backend/app/services/email/inbound_dispatch.py) |
| HTTP routes (connect / send / webhook / disconnect) | [app/api/v1/integrations.py](../velvet-elves-backend/app/api/v1/integrations.py) |
| Communication-log read/search/CSV | [app/api/v1/communication_logs.py](../velvet-elves-backend/app/api/v1/communication_logs.py) |
| Retention purge | [app/services/communication_export.py](../velvet-elves-backend/app/services/communication_export.py) |
| DB schema additions for this milestone | [supabase/migrations/20260429_milestone_4_1_email_integration.sql](../velvet-elves-backend/supabase/migrations/20260429_milestone_4_1_email_integration.sql) |

## Appendix B: deliverable mapping

This guide closes out the **configuration** portion of these Milestone 4.1 deliverables from [milestones.txt](milestones.txt):

- [x] Integrate Gmail API (OAuth2 flow, send/receive) — Step 1
- [x] Integrate Microsoft Graph API for Outlook (OAuth2, send/receive) — Step 2
- [x] Integrate Apple iCloud email API — Step 3
- [x] Build email connection flow during account creation — Step 6 (frontend already wired)
- [x] Define provider-agnostic hooks for future SMS and click-to-call / voice — already in `inbound_dispatch.py` (no config required)
- [x] Build unified communication log backend — already implemented; verify via Step 7
- [x] Implement log download (one transaction at a time per user) — already implemented
- [x] Build admin export request workflow (multi-transaction) — schema added in the 20260429 migration
- [x] Implement 2-year retention with quarterly auto-purge checks — Step 5
- [x] Build inbound email processing (logging, trigger hooks) — Steps 1f / 2f / 4
- [ ] Unit tests for email integration — not config; track separately
