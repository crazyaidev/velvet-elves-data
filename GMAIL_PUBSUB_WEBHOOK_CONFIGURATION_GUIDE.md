# Gmail Pub/Sub Webhook Configuration Guide

Last reviewed: 2026-05-12

This guide explains the exact configuration required for Gmail inbound
webhooks in Velvet Elves. It is a focused supplement to
[MILESTONE_4_1_EMAIL_INTEGRATION_CONFIGURATION_GUIDE.md](MILESTONE_4_1_EMAIL_INTEGRATION_CONFIGURATION_GUIDE.md).

The current Gmail OAuth flow can connect a mailbox and send email. Gmail
webhooks need additional Google Cloud Pub/Sub configuration plus a backend
`users.watch` registration for each connected mailbox.

Important: settings alone do not create Gmail webhooks. The backend must also:

1. Call Gmail `users.watch` after Gmail OAuth succeeds.
2. Store the returned `historyId` and `expiration` per integration.
3. Renew the watch before expiration. Google recommends daily renewal because
   watches expire within 7 days.
4. Validate Pub/Sub push JWTs on inbound Gmail webhook requests.
5. Resolve the Gmail Pub/Sub payload's `emailAddress` to the matching active
   integration, rather than relying on a `user_id` query parameter.

---

## 1. Required Moving Parts

Gmail push delivery has three layers:

| Layer | What It Does | Example |
| --- | --- | --- |
| Gmail API OAuth | Lets Velvet Elves access the user's mailbox. | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |
| Gmail `users.watch` | Tells Gmail which Pub/Sub topic to publish mailbox changes to. | `GMAIL_PUBSUB_TOPIC_NAME=projects/velvet-elves-dev/topics/gmail-inbound-dev` |
| Pub/Sub push subscription | Delivers topic messages to our FastAPI webhook. | `https://dev.velvetelves.com/api/v1/integrations/email/webhook/gmail` |

The Gmail watch does not point directly at our webhook. It points at a Pub/Sub
topic. The Pub/Sub subscription points at our webhook.

---

## 2. Backend Environment Variables

These variables are now present in `velvet-elves-backend/.env`,
`velvet-elves-backend/.env.example`, and `app/core/config.py`.

```env
# Existing Gmail OAuth settings
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GMAIL_REDIRECT_URI=

# Existing public webhook origin
EMAIL_WEBHOOK_PUBLIC_BASE_URL=

# Gmail Pub/Sub push notifications
GMAIL_PUBSUB_TOPIC_NAME=
GMAIL_WATCH_LABEL_IDS=INBOX
GMAIL_WATCH_LABEL_FILTER_BEHAVIOR=INCLUDE

# Pub/Sub authenticated push validation
PUBSUB_PUSH_AUDIENCE=
PUBSUB_PUSH_SERVICE_ACCOUNT_EMAIL=
```

### What Each Setting Means

`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

Google OAuth web client credentials. These are required before Gmail can
connect at all.

`GMAIL_REDIRECT_URI`

Optional but recommended outside local development. It must exactly match the
redirect URI registered in Google Cloud.

`EMAIL_WEBHOOK_PUBLIC_BASE_URL`

The public HTTPS API origin that Pub/Sub can reach. Do not include the webhook
path here. Use only the origin:

```env
EMAIL_WEBHOOK_PUBLIC_BASE_URL=https://d205-34-229-120-245.ngrok-free.app
```

or:

```env
EMAIL_WEBHOOK_PUBLIC_BASE_URL=https://dev.velvetelves.com
```

`GMAIL_PUBSUB_TOPIC_NAME`

The full Pub/Sub topic resource name passed to Gmail `users.watch`.

```env
GMAIL_PUBSUB_TOPIC_NAME=projects/velvet-elves-dev/topics/gmail-inbound-dev
```

`GMAIL_WATCH_LABEL_IDS`

Comma-separated Gmail labels to watch. Keep `INBOX` for Milestone 4.1 so we
only respond to inbound mail, not every sent/draft/label mutation.

```env
GMAIL_WATCH_LABEL_IDS=INBOX
```

`GMAIL_WATCH_LABEL_FILTER_BEHAVIOR`

How Gmail applies `GMAIL_WATCH_LABEL_IDS`. Use `INCLUDE` to watch only the
listed labels.

```env
GMAIL_WATCH_LABEL_FILTER_BEHAVIOR=INCLUDE
```

`PUBSUB_PUSH_AUDIENCE`

The audience expected in Pub/Sub's signed OIDC JWT. Keep this aligned with the
push subscription configuration.

```env
PUBSUB_PUSH_AUDIENCE=https://dev.velvetelves.com/api/v1/integrations/email/webhook/gmail
```

`PUBSUB_PUSH_SERVICE_ACCOUNT_EMAIL`

The user-managed service account configured on the Pub/Sub push subscription.
The backend should verify the JWT `email` claim equals this value.

```env
PUBSUB_PUSH_SERVICE_ACCOUNT_EMAIL=pubsub-push-gmail-dev@velvet-elves-dev.iam.gserviceaccount.com
```

---

## 3. Local Development Example

Use this when the frontend and backend run locally:

| Item | Local Value |
| --- | --- |
| Frontend | `http://localhost:5173` |
| Backend | `http://localhost:8000` |
| Public API tunnel | `https://<your-ngrok-id>.ngrok-free.app` |
| Gmail OAuth callback | `http://localhost:8000/api/v1/integrations/gmail/callback` |
| Gmail Pub/Sub push endpoint | `https://<your-ngrok-id>.ngrok-free.app/api/v1/integrations/email/webhook/gmail` |

### Step 1: Start the Local Backend

Run the backend on port 8000. Pub/Sub will not call `localhost`; ngrok will
forward public HTTPS traffic to it.

```powershell
cd C:\Projects\velvet-elves-backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Step 2: Start an ngrok Tunnel

```powershell
ngrok http 8000
```

Copy the HTTPS forwarding URL. Example:

```text
https://d205-34-229-120-245.ngrok-free.app
```

### Step 3: Set Local `.env`

Replace the project, topic, and service account placeholders with your real
Google Cloud values.

```env
APP_ENV=development

GOOGLE_CLIENT_ID=<local-or-dev-google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<local-or-dev-google-oauth-client-secret>
GMAIL_REDIRECT_URI=http://localhost:8000/api/v1/integrations/gmail/callback

EMAIL_WEBHOOK_PUBLIC_BASE_URL=https://d205-34-229-120-245.ngrok-free.app

GMAIL_PUBSUB_TOPIC_NAME=projects/velvet-elves-dev/topics/gmail-inbound-dev
GMAIL_WATCH_LABEL_IDS=INBOX
GMAIL_WATCH_LABEL_FILTER_BEHAVIOR=INCLUDE

PUBSUB_PUSH_AUDIENCE=https://d205-34-229-120-245.ngrok-free.app/api/v1/integrations/email/webhook/gmail
PUBSUB_PUSH_SERVICE_ACCOUNT_EMAIL=pubsub-push-gmail-dev@velvet-elves-dev.iam.gserviceaccount.com
```

When ngrok restarts, its URL usually changes. Update both:

```env
EMAIL_WEBHOOK_PUBLIC_BASE_URL=
PUBSUB_PUSH_AUDIENCE=
```

Then restart the backend and recreate or update the Pub/Sub push subscription.

### Step 4: Register Local OAuth Redirect URI

In Google Cloud Console:

1. Open APIs and Services -> Credentials.
2. Open the Gmail OAuth web client.
3. Add this authorized redirect URI:

```text
http://localhost:8000/api/v1/integrations/gmail/callback
```

### Step 5: Create Local/Dev Pub/Sub Resources

Use a non-production Google Cloud project when possible.

```powershell
$PROJECT_ID = "velvet-elves-dev"
$PROJECT_NUMBER = "<numeric-project-number>"
$TOPIC = "gmail-inbound-dev"
$SUBSCRIPTION = "gmail-inbound-dev-push-local"
$PUSH_SA = "pubsub-push-gmail-dev@$PROJECT_ID.iam.gserviceaccount.com"
$PUSH_ENDPOINT = "https://d205-34-229-120-245.ngrok-free.app/api/v1/integrations/email/webhook/gmail"
$AUDIENCE = $PUSH_ENDPOINT

gcloud config set project $PROJECT_ID
gcloud services enable gmail.googleapis.com pubsub.googleapis.com
gcloud pubsub topics create $TOPIC
gcloud iam service-accounts create pubsub-push-gmail-dev `
  --display-name "Pub/Sub Gmail push dev"
```

Grant Gmail permission to publish to the topic:

```powershell
gcloud pubsub topics add-iam-policy-binding $TOPIC `
  --member="serviceAccount:gmail-api-push@system.gserviceaccount.com" `
  --role="roles/pubsub.publisher"
```

Grant the Pub/Sub service agent permission to mint OIDC tokens for the push
service account:

```powershell
$PUBSUB_SERVICE_AGENT = "service-$PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$PUBSUB_SERVICE_AGENT" `
  --role="roles/iam.serviceAccountTokenCreator"
```

If the subscription creator gets an `actAs` error, grant that operator account
Service Account User on the push service account:

```powershell
gcloud iam service-accounts add-iam-policy-binding $PUSH_SA `
  --member="user:<your-google-account@example.com>" `
  --role="roles/iam.serviceAccountUser"
```

Create the authenticated push subscription:

```powershell
gcloud pubsub subscriptions create $SUBSCRIPTION `
  --topic=$TOPIC `
  --push-endpoint=$PUSH_ENDPOINT `
  --push-auth-service-account=$PUSH_SA `
  --push-auth-token-audience=$AUDIENCE `
  --ack-deadline=60 `
  --min-retry-delay=30s `
  --max-retry-delay=300s
```

The longer ack deadline and retry backoff prevent local/dev retry storms while
the backend is fetching Gmail deltas and writing communication logs. If the
subscription already exists, update it:

```powershell
gcloud pubsub subscriptions update $SUBSCRIPTION `
  --ack-deadline=60 `
  --min-retry-delay=30s `
  --max-retry-delay=300s
```

### Step 6: Reconnect Gmail

After the backend implements `users.watch`, disconnect and reconnect Gmail from
Settings -> Email Integrations. The OAuth callback should:

1. Store the Gmail tokens.
2. Call `POST https://gmail.googleapis.com/gmail/v1/users/me/watch`.
3. Use `GMAIL_PUBSUB_TOPIC_NAME` as `topicName`.
4. Store `historyId`, `lastHistoryId`, and `expiration` in the integration metadata.
5. On each Pub/Sub notification, call Gmail `users.history.list` with the
   stored `lastHistoryId`, process only new message IDs, then advance
   `lastHistoryId`.

### Step 7: Local Verification

1. Connect Gmail in Settings.
2. Send a real test email to the connected Gmail inbox.
3. Watch `velvet-elves-backend/logs/backend-debug.log`.
4. Expected log sequence:

```text
Connected Gmail integration for user=...
Gmail users.watch created for user=... history_id=... expiration=...
Received gmail email webhook ...
Gmail webhook Pub/Sub envelope decoded ...
gmail email webhook completed ... persisted=1 parsed=1
```

If the log shows no webhook request, inspect the Pub/Sub subscription delivery
attempts in Google Cloud Console.

---

## 4. Shared Dev / Production Example

Use this when the backend has a stable HTTPS hostname.

| Item | Shared Dev Example | Production Example |
| --- | --- | --- |
| Frontend | `https://dev.velvetelves.com` | `https://app.velvetelves.com` |
| Backend/API | `https://dev.velvetelves.com` | `https://api.prod.velvetelves.com` or final production API host |
| Gmail OAuth callback | `https://dev.velvetelves.com/api/v1/integrations/gmail/callback` | `https://api.prod.velvetelves.com/api/v1/integrations/gmail/callback` |
| Gmail webhook | `https://dev.velvetelves.com/api/v1/integrations/email/webhook/gmail` | `https://api.prod.velvetelves.com/api/v1/integrations/email/webhook/gmail` |

If production uses a single combined host instead of `api.prod.velvetelves.com`,
replace every production API example with that real backend host.

### Production `.env` Example

Use separate Google Cloud resources from local/dev.

```env
APP_ENV=production

GOOGLE_CLIENT_ID=<production-google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<production-google-oauth-client-secret>
GMAIL_REDIRECT_URI=https://api.prod.velvetelves.com/api/v1/integrations/gmail/callback

EMAIL_WEBHOOK_PUBLIC_BASE_URL=https://api.prod.velvetelves.com

GMAIL_PUBSUB_TOPIC_NAME=projects/velvet-elves-prod/topics/gmail-inbound-prod
GMAIL_WATCH_LABEL_IDS=INBOX
GMAIL_WATCH_LABEL_FILTER_BEHAVIOR=INCLUDE

PUBSUB_PUSH_AUDIENCE=https://api.prod.velvetelves.com/api/v1/integrations/email/webhook/gmail
PUBSUB_PUSH_SERVICE_ACCOUNT_EMAIL=pubsub-push-gmail-prod@velvet-elves-prod.iam.gserviceaccount.com
```

### Production Google Cloud Setup

```bash
PROJECT_ID="velvet-elves-prod"
PROJECT_NUMBER="<numeric-project-number>"
TOPIC="gmail-inbound-prod"
SUBSCRIPTION="gmail-inbound-prod-push"
PUSH_SA="pubsub-push-gmail-prod@$PROJECT_ID.iam.gserviceaccount.com"
PUSH_ENDPOINT="https://api.prod.velvetelves.com/api/v1/integrations/email/webhook/gmail"
AUDIENCE="$PUSH_ENDPOINT"

gcloud config set project "$PROJECT_ID"
gcloud services enable gmail.googleapis.com pubsub.googleapis.com
gcloud pubsub topics create "$TOPIC"
gcloud iam service-accounts create pubsub-push-gmail-prod \
  --display-name "Pub/Sub Gmail push prod"

gcloud pubsub topics add-iam-policy-binding "$TOPIC" \
  --member="serviceAccount:gmail-api-push@system.gserviceaccount.com" \
  --role="roles/pubsub.publisher"

PUBSUB_SERVICE_AGENT="service-$PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$PUBSUB_SERVICE_AGENT" \
  --role="roles/iam.serviceAccountTokenCreator"

gcloud pubsub subscriptions create "$SUBSCRIPTION" \
  --topic="$TOPIC" \
  --push-endpoint="$PUSH_ENDPOINT" \
  --push-auth-service-account="$PUSH_SA" \
  --push-auth-token-audience="$AUDIENCE" \
  --ack-deadline=60 \
  --min-retry-delay=30s \
  --max-retry-delay=300s
```

### Production OAuth Setup

In the production Google OAuth web client, add:

```text
https://api.prod.velvetelves.com/api/v1/integrations/gmail/callback
```

For production launch, the Google OAuth consent screen must also be production
ready. Because Gmail scopes are sensitive/restricted, plan verification time
before inviting real customers.

---

## 5. Backend Behavior To Expect After Configuration

### Gmail Watch Request Body

The backend should construct a request like this after Gmail OAuth succeeds:

```json
{
  "topicName": "projects/velvet-elves-dev/topics/gmail-inbound-dev",
  "labelIds": ["INBOX"],
  "labelFilterBehavior": "INCLUDE"
}
```

### Gmail Watch Response

The response contains:

```json
{
  "historyId": "1234567890",
  "expiration": "1767225600000"
}
```

Store both values in `integrations.metadata_json`, for example:

```json
{
  "gmail_watch": {
    "topicName": "projects/velvet-elves-dev/topics/gmail-inbound-dev",
    "historyId": "1234567890",
    "lastHistoryId": "1234567890",
    "expiration": "1767225600000",
    "created_at": "2026-05-12T00:00:00Z"
  }
}
```

### Pub/Sub Push Body

The webhook receives a Pub/Sub envelope:

```json
{
  "message": {
    "data": "base64url-encoded-json",
    "messageId": "2070443601311540",
    "publishTime": "2026-05-12T00:00:00Z"
  },
  "subscription": "projects/velvet-elves-dev/subscriptions/gmail-inbound-dev-push"
}
```

The decoded `message.data` looks like:

```json
{
  "emailAddress": "agent@example.com",
  "historyId": "9876543210"
}
```

The backend should use `emailAddress` to find the active Gmail integration.
That is safer than embedding `user_id` in the push endpoint because a Pub/Sub
subscription endpoint is usually shared by all watched Gmail accounts.

The backend should not scan recent inbox messages for every Pub/Sub push. The
push payload only tells us that the mailbox changed. The correct processing
path is:

1. Read `gmail_watch.lastHistoryId` from `integrations.metadata_json`.
2. Call Gmail `users.history.list` with `startHistoryId=lastHistoryId`.
3. Extract only newly added `INBOX` message IDs.
4. Fetch those message IDs.
5. Persist the inbound rows.
6. Advance `gmail_watch.lastHistoryId` to the latest Gmail history ID.

---

## 6. Troubleshooting

### Gmail connects but no webhook arrives

Likely causes:

- `GMAIL_PUBSUB_TOPIC_NAME` is blank.
- The backend did not call Gmail `users.watch`.
- Gmail was not granted `roles/pubsub.publisher` on the topic.
- The Pub/Sub subscription endpoint still points at an old ngrok URL.
- The backend was restarted with a different `.env` than expected.

Check:

```powershell
gcloud pubsub topics get-iam-policy gmail-inbound-dev
gcloud pubsub subscriptions describe gmail-inbound-dev-push-local
```

### Pub/Sub delivery attempts show 401 or 403

Likely causes:

- `PUBSUB_PUSH_AUDIENCE` does not match the subscription audience.
- `PUBSUB_PUSH_SERVICE_ACCOUNT_EMAIL` does not match the push auth service account.
- The backend is still checking `X-VE-Webhook-Secret` for Gmail instead of
  validating the Pub/Sub `Authorization: Bearer <jwt>` header.
- The Pub/Sub service agent lacks `roles/iam.serviceAccountTokenCreator`.

### Pub/Sub delivery attempts show 404

Likely causes:

- Push endpoint host or path is wrong.
- ngrok is offline.
- The backend API is not running.
- A reverse proxy is not forwarding `/api/v1/integrations/email/webhook/gmail`.

### Pub/Sub delivery attempts show 5xx

Likely causes:

- Backend exception while parsing the Pub/Sub body.
- Gmail access token expired and refresh failed.
- The integration cannot be found for the decoded `emailAddress`.
- Supabase write failed.

### Webhook arrives but persists zero rows

Possible but not always wrong:

- The inbound message was already logged and deduped.
- Gmail `history.list` returned no new `INBOX` message IDs for the stored
  cursor.
- The notification was stale and its `historyId` was already processed.
- Gmail rejected an old cursor; the backend re-baselined `lastHistoryId` and
  marked `historySyncRequired` in metadata.

---

## 7. Verification Checklist

Use this checklist for local and production.

1. `.env` has a non-empty `GMAIL_PUBSUB_TOPIC_NAME`.
2. `.env` has `EMAIL_WEBHOOK_PUBLIC_BASE_URL` set to the public API origin.
3. `.env` has `PUBSUB_PUSH_AUDIENCE` set to the exact Gmail webhook URL.
4. `.env` has `PUBSUB_PUSH_SERVICE_ACCOUNT_EMAIL` set to the push auth service account.
5. Google OAuth client includes the correct Gmail callback URI.
6. Gmail API and Pub/Sub API are enabled in the Google Cloud project.
7. Pub/Sub topic exists.
8. `gmail-api-push@system.gserviceaccount.com` has publisher rights on the topic.
9. Pub/Sub push subscription exists and points to the correct webhook URL.
10. Pub/Sub push subscription authentication is enabled.
11. Pub/Sub service agent has `roles/iam.serviceAccountTokenCreator`.
12. Backend implements Gmail `users.watch`.
13. Gmail integration metadata contains watch `historyId` and `expiration`.
14. Test inbound email produces a backend log entry and a communication log row.

---

## 8. Official References

- Gmail API push notifications:
  `https://developers.google.com/workspace/gmail/api/guides/push`
- Pub/Sub authenticated push subscriptions:
  `https://cloud.google.com/pubsub/docs/authenticate-push-subscriptions`
- Pub/Sub push subscription creation:
  `https://cloud.google.com/pubsub/docs/create-push-subscription`
