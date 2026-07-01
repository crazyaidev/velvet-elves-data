# Google Auth (OAuth) Setup Guide for Velvet Elves

Last reviewed: 2026-07-01

This guide covers the **Google Cloud OAuth consent screen and OAuth 2.0 Web
Client** that power the in-app "Connect Gmail" and "Connect Google Calendar"
flows. This is the piece often called "Google Auth."

It complements two sibling guides:

- [GMAIL_PUBSUB_WEBHOOK_CONFIGURATION_GUIDE.md](GMAIL_PUBSUB_WEBHOOK_CONFIGURATION_GUIDE.md) — how Gmail push delivery (Pub/Sub) reaches the backend. That is a *separate* concern from OAuth.
- [CI_CD_PIPELINE_IMPLEMENTATION_GUIDELINES.md](CI_CD_PIPELINE_IMPLEMENTATION_GUIDELINES.md) — the canonical domain model (`api.stage.velvetelves.com`, `api.velvetelves.com`).

> **Important — this is a manual, Console-only setup.** Unlike Pub/Sub topics
> and subscriptions, the OAuth consent screen and OAuth 2.0 **web** Client ID
> **cannot be created with `gcloud`**. The CLI only supports IAP-type OAuth
> clients, which is the wrong kind for this consumer-style OAuth flow. Every
> step below is done in the Google Cloud Console web UI.

---

## Environment summary

Each environment has its own Google Cloud project and therefore its own OAuth
consent screen + OAuth client. The **backend** (not the frontend) handles the
OAuth callback, so all redirect URIs point at the API host.

| Environment | GCP project | Project number | API host | Gmail redirect URI | Calendar redirect URI |
| ----------- | ----------- | -------------- | -------- | ------------------ | --------------------- |
| Staging     | `velvet-elves-495419` | `690290770751` | `api.stage.velvetelves.com` | `https://api.stage.velvetelves.com/api/v1/integrations/gmail/callback` | `https://api.stage.velvetelves.com/api/v1/calendar/google/callback` |
| Production  | `velvet-vles`         | `538509143953` | `api.velvetelves.com`       | `https://api.velvetelves.com/api/v1/integrations/gmail/callback`       | `https://api.velvetelves.com/api/v1/calendar/google/callback`       |

Gmail and Calendar **share one OAuth client** per environment (the backend uses
the same client for both, with different scope sets). You register **both**
redirect URIs on the **same** client.

Current state as of this writing:

- Staging (`velvet-elves-495419`) already has a working OAuth client:
  `690290770751-vr7qdivi02nr9ppvk0a2ridkhd3f5jvg.apps.googleusercontent.com`.
- Production (`velvet-vles`) has **no** OAuth client yet. `PROD_GOOGLE_CLIENT_ID`
  in `.env.prod` currently still points at the *staging* client. Creating the
  production client (Steps 2–6) and swapping those values is the main open task.

---

## Scopes this application requests

These come from the backend (`app/services/email/gmail_provider.py`). You must
declare every one of them on the consent screen, or users will hit
`invalid_scope` / partial-consent errors.

**Gmail integration** (`provider="gmail"`):

| Scope | Google sensitivity tier |
| ----- | ----------------------- |
| `openid` | Non-sensitive |
| `email` (`.../auth/userinfo.email`) | Non-sensitive |
| `profile` (`.../auth/userinfo.profile`) | Non-sensitive |
| `https://www.googleapis.com/auth/gmail.send` | **Sensitive** |
| `https://www.googleapis.com/auth/gmail.readonly` | **Restricted** |
| `https://www.googleapis.com/auth/gmail.modify` | **Restricted** |

**Google Calendar integration** (`provider="google_calendar"`):

| Scope | Google sensitivity tier |
| ----- | ----------------------- |
| `openid` | Non-sensitive |
| `email` | Non-sensitive |
| `https://www.googleapis.com/auth/calendar.events` | **Sensitive** |

Why the tiers matter: **Sensitive** and **Restricted** scopes require Google to
verify the app before it can serve external users in production. Restricted
Gmail scopes (`gmail.readonly`, `gmail.modify`) additionally require an annual
third-party security assessment (CASA). See [Step 8](#step-8-publishing-and-verification-required-for-production).

---

## Prerequisites

1. You are signed into the Google Cloud Console as an **Owner** or **Editor** of
   the target project.
   - Production: `crazyaidev20500519@gmail.com` has been granted **Owner** on
     `velvet-vles` (verified 2026-07-01).
2. The Gmail API and Google Calendar API are enabled on the project. For
   `velvet-vles` these were enabled on 2026-07-01 (`gmail.googleapis.com`,
   `calendar-json.googleapis.com`). To confirm:
   ```bash
   gcloud services list --enabled --project velvet-vles \
     --filter="config.name:(gmail.googleapis.com OR calendar-json.googleapis.com)"
   ```
3. You know the API host for the environment (see the summary table).

---

## Step 1: Open the OAuth configuration

Google is mid-migration, so you may see either UI:

- **Newer UI — "Google Auth Platform":** Console → **APIs & Services** →
  **OAuth consent screen** now opens **Google Auth Platform**, with a left nav:
  **Overview**, **Branding**, **Audience**, **Clients**, **Data Access**,
  **Verification center**.
- **Legacy UI — "OAuth consent screen":** a single scrollable page with App
  information, Scopes, Test users, and Summary sections.

Make sure the **project picker at the top of the Console reads the correct
project** (`velvet-vles` for production) before doing anything. The consent
screen and client are project-scoped; configuring them in the wrong project is
the most common mistake.

If the project has never had a consent screen, the UI prompts you to **Get
started** / **Configure consent screen** first.

---

## Step 2: Set the user type (Audience)

New UI: **Audience** tab. Legacy UI: first screen of the consent-screen wizard.

Choose **External**.

- **External** is required — Velvet Elves connects real-estate customers' own
  Gmail/Google accounts, which are outside any single Workspace org.
- **Internal** would only allow accounts in one Google Workspace organization
  and is not appropriate here.

While the app is in **Testing** (see Step 8), only **test users** you list here
can complete consent. Add the emails of everyone who needs to test staging or
production before verification is complete.

---

## Step 3: Configure Branding (app information)

New UI: **Branding** tab. Legacy UI: "App information".

| Field | Value |
| ----- | ----- |
| App name | `Velvet Elves` |
| User support email | a monitored address (e.g. `support@velvetelves.com`) |
| App logo | optional now, **required for verification** — 120×120 PNG, no rounded corners |
| Application home page | `https://velvetelves.com` |
| Application privacy policy | `https://velvetelves.com/privacy` (or the real URL) |
| Application terms of service | `https://velvetelves.com/terms` (or the real URL) |
| Authorized domain | `velvetelves.com` |
| Developer contact email | an address Google can reach you at |

Notes:

- **Authorized domain** must be the top private domain `velvetelves.com`, not a
  subdomain. It authorizes `app.velvetelves.com`, `api.velvetelves.com`, etc.
- The privacy policy and terms URLs must be live and on the authorized domain
  before you can submit for verification.

---

## Step 4: Declare scopes (Data Access)

New UI: **Data Access** tab → **Add or remove scopes**. Legacy UI: "Scopes"
step.

Add every scope listed in [Scopes this application requests](#scopes-this-application-requests):

1. Click **Add or remove scopes**.
2. For non-sensitive scopes, filter for and tick `openid`, `.../auth/userinfo.email`, `.../auth/userinfo.profile`.
3. For the Gmail and Calendar scopes, paste each full scope string into the
   "Manually add scopes" box (they may not all appear in the filtered list),
   click **Add to table**, then **Update**:
   ```
   https://www.googleapis.com/auth/gmail.send
   https://www.googleapis.com/auth/gmail.readonly
   https://www.googleapis.com/auth/gmail.modify
   https://www.googleapis.com/auth/calendar.events
   ```
4. Confirm the table shows the three tiers grouped as "Non-sensitive",
   "Sensitive", and "Restricted". Save.

Keep this list **exactly** in sync with `GMAIL_SCOPES` and
`GOOGLE_CALENDAR_SCOPES` in `gmail_provider.py`. If the code ever requests a
scope not declared here, consent fails at runtime.

---

## Step 5: Create the OAuth 2.0 Web Client

New UI: **Clients** tab → **Create client**. Legacy UI: **APIs & Services** →
**Credentials** → **Create credentials** → **OAuth client ID**.

1. **Application type:** `Web application`.
2. **Name:** `Velvet Elves API — production` (or `— staging`). This is internal
   only; users never see it.
3. **Authorized JavaScript origins:** leave empty. The OAuth flow is handled
   server-side by the backend, so browser origins are not needed.
4. **Authorized redirect URIs:** click **Add URI** and add **both** of these
   (production example — substitute `api.stage.` for staging):
   ```
   https://api.velvetelves.com/api/v1/integrations/gmail/callback
   https://api.velvetelves.com/api/v1/calendar/google/callback
   ```
5. Click **Create**.
6. A dialog shows the **Client ID** and **Client secret**. Copy both
   immediately into a safe place (they can be retrieved later, but copy now to
   save a round trip).

**Critical — redirect URIs must match byte-for-byte** what the backend sends
(`PROD_GMAIL_REDIRECT_URI` and `PROD_GOOGLE_CALENDAR_REDIRECT_URI`). Common
mismatches that cause `redirect_uri_mismatch`:

- Trailing slash (`/callback` vs `/callback/`)
- `http` vs `https`
- Wrong host (`app.` vs `api.`, `stage.` vs prod)
- A stray path typo

---

## Step 6: Wire the client into the backend config

The backend reads these from environment config. Production values live in
`velvet-elves-backend/.env.prod`:

```env
PROD_GOOGLE_CLIENT_ID=<new client id from Step 5>
PROD_GOOGLE_CLIENT_SECRET=<new client secret from Step 5>
PROD_GMAIL_REDIRECT_URI=https://api.velvetelves.com/api/v1/integrations/gmail/callback
PROD_GOOGLE_CALENDAR_REDIRECT_URI=https://api.velvetelves.com/api/v1/calendar/google/callback
```

The redirect URIs are already correct in `.env.prod`; only the client ID and
secret need replacing (they currently hold the staging client's values).

> **Deployment note (per the CI/CD guide, section 3.2):** OAuth client secrets
> are runtime secrets. They belong in **AWS Secrets Manager**
> (`/velvet-elves/prod/backend`), not in GitHub. `.env.prod` is the local source
> of truth that gets synced into Secrets Manager; do not hand-edit `.env` on the
> running server. After updating the secret store, restart/redeploy the ECS
> service so the new values load.

Staging equivalent (`.env.stage`) already has a working client and needs no
change unless you deliberately rotate it.

---

## Step 7: Repeat for staging (only if creating a fresh client)

Staging already has a client. If you ever need to recreate it, repeat Steps 1–6
inside project `velvet-elves-495419`, using the `api.stage.velvetelves.com`
redirect URIs, and write the values to `STAGE_GOOGLE_CLIENT_ID` /
`STAGE_GOOGLE_CLIENT_SECRET` in `.env.stage`.

Keep staging and production clients **separate**. Do not point production at the
staging client (the current temporary state) once the production client exists —
mixing environments couples their consent screens, verification status, and
branding.

---

## Step 8: Publishing and verification (required for production)

This is the long pole for a production launch. Plan for it early.

### Publishing status: Testing vs In production

New UI: **Audience** tab shows **Publishing status**. Legacy UI: "Publishing
status" on the consent screen page.

- **Testing** — only listed test users can consent. Refresh tokens issued in
  Testing mode **expire after 7 days**, so a connected mailbox silently stops
  syncing a week later. Fine for early staging, **not** acceptable for
  production.
- **In production** — anyone can consent, and refresh tokens are long-lived.
  Moving here with Sensitive/Restricted scopes triggers Google's verification
  requirement.

### Verification requirements for our scopes

Because we request Sensitive (`gmail.send`, `calendar.events`) and Restricted
(`gmail.readonly`, `gmail.modify`) scopes, production external use requires:

1. **Brand verification** — logo, home page, privacy policy, and terms must be
   live on `velvetelves.com` and the domain ownership verified.
2. **OAuth app verification** — submit from the **Verification center** (new UI)
   or the consent screen (legacy). Google reviews scope justification and a demo
   video showing how each restricted scope is used.
3. **CASA security assessment** — Restricted Gmail scopes require an annual
   third-party **Cloud Application Security Assessment** (Tier 2). This is a paid
   engagement and can take weeks. Start it as soon as the domain and privacy
   policy exist.

Until verification completes, external (non-test) users see an
**"Access blocked: this app is not verified"** screen. Test users on the list
can bypass it via the "Advanced → Go to Velvet Elves (unsafe)" path, which is
acceptable for internal testing only.

---

## Step 9: Verify end to end

Do this per environment after the client exists and the backend has the matching
config.

**Gmail:**

1. Sign into the app (staging: `https://app.stage.velvetelves.com`; prod:
   `https://app.velvetelves.com`).
2. Go to **Settings → Email Integrations → Connect Gmail**.
3. Complete Google sign-in and consent. You should be redirected back to
   `.../api/v1/integrations/gmail/callback` and land on a "connected" state.
4. Backend logs show `Connected Gmail integration for user=...` and, once
   Pub/Sub is wired, `Gmail users.watch created ...`.

**Calendar:**

1. **Settings → Calendar → Connect Google Calendar**.
2. Consent to the `calendar.events` scope. You are redirected to
   `.../api/v1/calendar/google/callback`.
3. The integration row is stored under `provider="google_calendar"`, separate
   from the Gmail row.

---

## Troubleshooting

### `redirect_uri_mismatch`

The redirect URI the backend sent is not registered on the client, character for
character. Compare `PROD_GMAIL_REDIRECT_URI` / `PROD_GOOGLE_CALENDAR_REDIRECT_URI`
against the **Authorized redirect URIs** on the client (Step 5). Check for
trailing slash, `http` vs `https`, and `app.` vs `api.` host.

### `Access blocked: Velvet Elves has not completed the Google verification process`

Expected while the app is in Testing or pending verification. Either add the
user to **test users** (Step 2), or complete verification (Step 8) for open
external access.

### `invalid_client`

The `PROD_GOOGLE_CLIENT_ID` / `PROD_GOOGLE_CLIENT_SECRET` in use do not match a
client in the project the OAuth request targets — commonly because production is
still using the staging client, or the secret was rotated without updating the
secret store. Re-copy from the client in `velvet-vles`.

### `invalid_scope` or the consent screen omits a permission

A scope requested by the code is not declared on the consent screen. Add it in
**Data Access** (Step 4) so the declared scopes match `gmail_provider.py`.

### A connected mailbox stops syncing after ~7 days

The app was in **Testing** publishing status when the user consented, so the
refresh token expired. Move the app to **In production** (Step 8) and have the
user reconnect to get a long-lived refresh token.

### Scope change doesn't take effect

Changing scopes requires users to re-consent. Existing tokens keep their old
scope grant until the user disconnects and reconnects.

---

## Reference values

```text
Production project:   velvet-vles (number 538509143953)
Staging project:      velvet-elves-495419 (number 690290770751)

Production redirect URIs (both on one web client):
  https://api.velvetelves.com/api/v1/integrations/gmail/callback
  https://api.velvetelves.com/api/v1/calendar/google/callback

Staging redirect URIs (both on one web client):
  https://api.stage.velvetelves.com/api/v1/integrations/gmail/callback
  https://api.stage.velvetelves.com/api/v1/calendar/google/callback

Gmail scopes:    openid, email, profile,
                 gmail.send (sensitive),
                 gmail.readonly (restricted),
                 gmail.modify (restricted)
Calendar scopes: openid, email, calendar.events (sensitive)

Backend .env keys:
  PROD_GOOGLE_CLIENT_ID / PROD_GOOGLE_CLIENT_SECRET
  PROD_GMAIL_REDIRECT_URI / PROD_GOOGLE_CALENDAR_REDIRECT_URI
  (STAGE_* equivalents in .env.stage)
```

## Official references

- OAuth consent screen / Google Auth Platform:
  `https://support.google.com/cloud/answer/10311615`
- Create OAuth 2.0 client credentials:
  `https://developers.google.com/identity/protocols/oauth2/web-server`
- OAuth API verification and restricted scopes:
  `https://support.google.com/cloud/answer/9110914`
- Gmail API scopes:
  `https://developers.google.com/gmail/api/auth/scopes`
- Google Calendar API scopes:
  `https://developers.google.com/calendar/api/auth`
