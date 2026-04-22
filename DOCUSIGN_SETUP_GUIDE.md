# DocuSign Setup Guide for Velvet Elves

This guide configures DocuSign so the in-app "Connect DocuSign" wizard works for both local development and the dev deployment.

## Environment summary

| Environment | Backend OAuth callback (registered in DocuSign app)                              | Connect webhook URL (registered in DocuSign Connect)                               |
| ----------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Local dev   | `http://localhost:8000/api/v1/integrations/docusign/callback`                    | `https://<your-ngrok-subdomain>.ngrok-free.app/api/v1/esign/webhooks/docusign` (tunnel required — see Step 5g) |
| EC2 dev     | `https://dev.velvetelves.com/api/v1/integrations/docusign/callback`              | `https://dev.velvetelves.com/api/v1/esign/webhooks/docusign`                       |

The DocuSign **redirect URI** must point to the **backend** callback endpoint (not the frontend). The endpoint path is always `/api/v1/integrations/docusign/callback`.

The DocuSign **Connect webhook URL** is separate from the OAuth callback — it is how DocuSign pushes envelope-status events (e.g. "envelope completed") back to us so the document row flips from `sent_for_signature` to `signed` automatically. Configure it in **Admin → Connect → Configurations**, not in the Apps and Keys screen.

## Prerequisites

1. You are signed in to the DocuSign developer admin console as an Administrator on the **Velvet Elves** account. Either of these URLs works (DocuSign is mid-migration between the old and new admin UIs):
   - Newer UI: https://apps-d.docusign.com/admin/admin-dashboard
   - Legacy UI: https://admindemo.docusign.com
2. The Integration Key from the backend `.env` exists in this account: `b69b0237-468f-4b71-9c8a-68dfe3c82664`.
3. You have shell access to the EC2 instance to update its `.env` and restart the backend service.

### Confirmed account values (verified 2026-04-21)

When you open **Apps and Keys**, the "My Account Information" panel at the top shows the values below. They match the backend config and confirm you are in the correct DocuSign environment:

| Field             | Value                                       | Where it shows up in our config              |
| ----------------- | ------------------------------------------- | -------------------------------------------- |
| Account ID        | `46874583`                                  | (informational, not used by code)            |
| API Account ID    | `d42338d1-c783-4e74-8ef2-578418268fd7`      | Optional fallback for `DOCUSIGN_ACCOUNT_ID`  |
| Account Base URI  | `https://demo.docusign.net`                 | Matches `DOCUSIGN_BASE_URL` in `config.py`   |
| App name          | `Velvet Elves`                              | (informational)                              |
| Integration Key   | `b69b0237-468f-4b71-9c8a-68dfe3c82664`      | `DOCUSIGN_INTEGRATION_KEY` in `.env`         |
| Environment       | `Development`                               | Confirms sandbox / demo, matches `account-d.*` |
| Go Live Status    | `Ready to Submit` (Promote to production)   | Used during the production migration step    |

We do not need to set `DOCUSIGN_ACCOUNT_ID` in `.env`: the OAuth flow auto-discovers the per-user `account_id` and stores it on the integration row. The API Account ID above is only useful as a fallback if we ever bypass OAuth.

## Step 1: Register redirect URIs in DocuSign

1. From the **Apps and Keys** page, locate the **Velvet Elves** row in the "Apps and Integration Keys" table.
2. On the right side of that row, click the **Actions** dropdown, then choose **Edit App**.
   - You can also just click the app name "Velvet Elves" in the **App Name** column to open the same detail page.
3. On the app detail page, find the section labeled **Additional Settings** (in the new UI it may be a collapsible panel near the bottom). Inside it, locate **Redirect URIs**.
4. Click **Add URI** and paste the local development callback:
   ```
   http://localhost:8000/api/v1/integrations/docusign/callback
   ```
5. Click **Add URI** again and paste the EC2 dev callback:
   ```
   https://dev.velvetelves.com/api/v1/integrations/docusign/callback
   ```
6. Click **Save** at the bottom of the page (label may be "Save Changes" depending on the UI version).

**Critical**: the URI must match what the backend sends, character for character. Common mismatches that cause "no redirect URIs registered":

- Trailing slash (`/callback` vs `/callback/`), pick one and be consistent everywhere
- `http` vs `https`
- `localhost` vs `127.0.0.1`
- Different port number

## Step 2: OAuth scopes (no action needed, here's why)

You will not find an "OAuth Scopes" toggle on the app detail page. This is expected.

DocuSign handles scopes by auth-flow type:

- **Authorization Code Grant** (what our backend uses): scopes are sent in the `?scope=` query parameter of the OAuth authorize URL each time a user connects. There is no admin-side toggle. Whatever the backend requests is what the user sees on the consent screen.
- **JWT Grant** (service-account, not used here): requires a separate one-time admin consent URL.
- **Legacy Service Integration**: may show a scope checklist in old account UIs; not relevant for Authorization Code Grant.

Our backend requests the `signature` scope (`DOCUSIGN_SCOPES="signature"` in `.env`). This scope is available by default on every Integration Key, so no admin enablement is required.

**How to verify scopes are working at runtime:**

1. Trigger the connect wizard.
2. After signing in, DocuSign will show a consent screen titled something like "Velvet Elves wants to access your DocuSign account".
3. The screen lists the requested permissions, e.g. "Send envelopes on your behalf". These map to the `signature` scope.
4. If you can click **Allow Access** without seeing an `invalid_scope` error, scopes are working.

If you ever change `DOCUSIGN_SCOPES` to include restricted scopes like `impersonation` or `organization_read`, those would require additional admin consent and may surface a per-scope enablement step. For the current code, you are done with this step.

## Step 3: Configure backend `.env` for local development

Edit `velvet-elves-backend/.env`. The Integration Key and Secret are already set. Add or confirm:

```env
DOCUSIGN_INTEGRATION_KEY="xxx"
DOCUSIGN_SECRET_KEY="xxx"
DOCUSIGN_OAUTH_BASE_URL="https://account-d.docusign.com"
DOCUSIGN_SCOPES="signature"
DOCUSIGN_REDIRECT_URI="http://localhost:8000/api/v1/integrations/docusign/callback"
```

Pinning `DOCUSIGN_REDIRECT_URI` explicitly is important. Without it, the backend derives the URI from the request host, which can be fragile behind proxies.

Restart the backend:

```bash
cd velvet-elves-backend
./venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

## Step 4: Configure backend `.env` on EC2

SSH into EC2 and edit the backend's `.env` file. Set the same values as above, but change the redirect URI to the dev URL:

```env
DOCUSIGN_INTEGRATION_KEY="xxx"
DOCUSIGN_SECRET_KEY="xxx"
DOCUSIGN_OAUTH_BASE_URL="https://account-d.docusign.com"
DOCUSIGN_SCOPES="signature"
DOCUSIGN_REDIRECT_URI="https://dev.velvetelves.com/api/v1/integrations/docusign/callback"
```

Restart the backend service so the new env vars take effect (use whichever process manager the deployment uses: `systemctl restart`, `pm2 restart`, `docker compose restart`, etc.).

## Step 5: Configure the DocuSign Connect webhook (required for auto-sync)

Without Connect, DocuSign will never tell the backend when an envelope is signed, and every document will stay stuck at `sent_for_signature` until a user clicks **Refresh Signature Status** in the UI. Connect is what closes that loop automatically.

By default this step targets **EC2 dev** (and production later). To wire the same auto-sync into your **local backend**, you need a public HTTPS tunnel pointing at `localhost:8000` — see **Step 5g** below for the ngrok recipe. Without a tunnel, local dev still works end-to-end via the in-app **Refresh Signature Status** button or `POST /esign/sync`; Connect just won't fire to localhost.

### 5a. Navigate to Connect (new admin UI: https://apps-d.docusign.com/admin)

1. In the left sidebar, look for **Integrations** and expand it.
2. Click **Connect**.
   - Direct URL: https://apps-d.docusign.com/admin/connect
3. You should land on the **Connect** page with a list of existing configurations (probably empty) and a **+ Add Configuration** button in the upper right.

### 5b. Create the Custom Configuration

1. Click **+ Add Configuration**.
2. A dropdown appears. Choose **Custom**. (Do **not** pick Salesforce, Box, etc.)
3. The "Add Custom Configuration" form opens. Fill in the **top section** as follows:

   | Field                                  | Value                                                              |
   | -------------------------------------- | ------------------------------------------------------------------ |
   | **Name**                               | `Velvet Elves — dev`                                               |
   | **URL to Publish**                     | `https://dev.velvetelves.com/api/v1/esign/webhooks/docusign`       |
   | **Enable Log**                         | **On** (you will need these logs when something goes wrong)        |
   | **Require Acknowledgement**            | **On** (so DocuSign retries on non-2xx responses)                  |
   | **Include Documents**                  | **On** (we need the signed PDF in the payload for auto-replace)    |
   | **Include Certificate of Completion**  | Optional — Off is fine                                             |
   | **Send Message Format**                | **JSON** ← critical, the backend does not parse XML                |

   Leave any other top-section toggles at their defaults.

4. Scroll to the **Trigger Events** section. You'll see two columns: **Envelope Events** and **Recipient Events**.

   In **Envelope Events**, tick:
   - ☑ **Sent** (optional, useful for debugging)
   - ☑ **Delivered** (optional)
   - ☑ **Completed** ← required (this is what flips the doc to "Signed")
   - ☑ **Declined** ← required
   - ☑ **Voided** ← required

   In **Recipient Events**: leave everything **unticked** for now. Per-recipient noise is not needed.

5. In the **Associated Users** section, choose **All Users** (or "Select Users" and pick the user that owns the Integration Key). For dev, **All Users** is simpler.

6. Scroll to the bottom and click **Add Configuration**. The form closes and the new config appears in the list.

### 5c. Add the HMAC Secret

> **Important: HMAC keys are account-wide, not per-configuration.** In the new admin UI (apps-d.docusign.com/admin/connect), the row for "Velvet Elves — dev" is **not clickable** — this surprised the Velvet Elves team the first time. Instead, DocuSign manages HMAC keys in a separate **Connect Keys** tab at the top of the Connect page, and every configuration on the account inherits them. Enabling HMAC verification on a given configuration is a separate toggle reached via **Actions → Edit**.

This section has **two parts**:
- **5c-1** — generate the HMAC key in **Connect Keys**
- **5c-2** — enable "Include HMAC Signature" on the **Velvet Elves — dev** configuration via Actions → Edit

#### 5c-1. Generate the HMAC key (Connect Keys tab)

1. Still on the Connect page (https://apps-d.docusign.com/admin/connect), look at the tab bar directly above the configurations list: **Configurations** | **Connect Keys** | **OAuth 2.0** | **Publish** | **Logs** | **Dashboard**.
2. Click **Connect Keys**.
3. You'll see a list of keys (probably empty) and an **Add Secret Key** button (label may be "Generate Key" or "+ Add Key" depending on rollout state).
4. Click it. DocuSign immediately generates and displays a long random key — something like `aB3xYz9...` (40+ characters).
5. **Copy it immediately to a safe place (1Password, a scratch file, whatever).** DocuSign will mask the value and refuse to show it again after you leave this page. If you lose it, your only recovery is to delete the key and generate a new one — which also means re-pasting the new value into `.env` on EC2.
6. The key is saved as soon as it is generated; no explicit save button.

#### 5c-2. Turn on HMAC verification for the Velvet Elves — dev configuration

1. Click the **Configurations** tab to go back to the list.
2. On the **Velvet Elves — dev** row, click the **Actions** dropdown on the right.
3. Choose **Edit**. The same form from Step 5b opens.
4. Scroll down to the **Connect Security** (or **Include HMAC Signature**) section — it's usually near the bottom, below the Trigger Events.
5. Toggle **Include HMAC Signature** **On**.
6. Save the configuration (button at the bottom, typically **Save** or **Update Configuration**).

From this point on, every webhook DocuSign posts for this configuration will include an `X-DocuSign-Signature-1` header — the base64 HMAC-SHA256 of the raw request body, keyed by the secret you copied in 5c-1.

> **Alternative if the new UI is confusing:** switch to the legacy UI at https://admindemo.docusign.com → Settings → Connect. There, HMAC keys and the per-configuration toggle live on the same page. Anything you do there is reflected in the new UI.

### 5d. Put the secret into EC2

SSH into the EC2 instance and edit the backend `.env`:

```bash
ssh <ec2-user>@dev.velvetelves.com
cd /path/to/velvet-elves-backend
nano .env   # or vim
```

Add (or replace) this line, pasting the key you copied from the HMAC tab:

```env
DOCUSIGN_WEBHOOK_SECRET=aB3xYz9...the-long-key-from-docusign...
```

Save and exit. Restart the backend with whichever process manager dev uses:

```bash
sudo systemctl restart velvet-elves-backend
# or
docker compose restart backend
# or
pm2 restart velvet-elves-backend
```

Confirm the backend came back:

```bash
curl https://dev.velvetelves.com/api/v1/health
```

Should return `200 OK`.

With HMAC enabled, DocuSign sends `X-DocuSign-Signature-1` on every webhook containing the base64 HMAC-SHA256 of the raw body keyed by the secret. The backend verifies this signature constant-time; requests with a missing or wrong signature are rejected with 401.

**If `DOCUSIGN_WEBHOOK_SECRET` is empty**, signature verification is skipped entirely — acceptable for local development, not acceptable for EC2 dev or production.

### 5e. Verify end-to-end

1. In the app at https://dev.velvetelves.com, send a test document for signature to an address you control.
2. Open the email DocuSign sent and complete the signing.
3. **Within 30 seconds**, two things should happen:
   - In DocuSign admin → Connect → **Velvet Elves — dev** → **Logs** tab, a new entry appears with status **Success (200)**.
   - In the app, the document row flips from "Sent for Signature" to **Signed** automatically (no Refresh click needed).

### 5f. Reading the Connect Logs

| Log status                              | Meaning                                          | Fix                                                                                                                                                                                                                                              |
| --------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Success 200**                         | Working                                          | Nothing to do.                                                                                                                                                                                                                                   |
| **Failure 401**                         | HMAC signature mismatch                          | The secret in EC2's `.env` does not match the one on DocuSign. Re-copy. If the HMAC tab no longer shows the key value, delete the secret on DocuSign, generate a new one, and paste it again.                                                    |
| **Failure 5xx / connection refused**    | Backend down or URL unreachable                  | Verify the backend is running and the URL is correct. Test from outside EC2: `curl -X POST https://dev.velvetelves.com/api/v1/esign/webhooks/docusign -d '{}' -H 'Content-Type: application/json'` should return **400** (malformed payload), not a connection error. |
| **Failure 400**                         | Payload shape mismatch                           | Inspect the body shown in the log entry. Extend the `EsignWebhookEvent` schema in `app/schemas/esign.py` to match what DocuSign actually sends.                                                                                                  |
| **No log entry at all**                 | Connect did not fire                             | Confirm the trigger events include **Completed**, that the envelope reached "Completed" status in DocuSign, and that **Enable Log** is on for this configuration.                                                                                |

### 5g. Wire the local backend through an ngrok tunnel (optional, for testing webhooks against `localhost`)

DocuSign Connect requires a publicly-reachable **HTTPS** URL — it cannot post to `http://localhost:8000`. To exercise the real webhook path against your local backend (HMAC verification, payload parsing, auto-replace, auto-distribute), tunnel `localhost` through ngrok and register that tunnel URL as a **second** Connect configuration.

> Use a **separate** Connect configuration for local — do not edit the dev one. Otherwise, every signature in DocuSign tries to deliver to your laptop, and the moment ngrok is down, DocuSign will retry against an unreachable URL.

#### One-time setup

1. Install ngrok:
   - macOS: `brew install ngrok/ngrok/ngrok`
   - Windows: `winget install ngrok.ngrok` or download from https://ngrok.com/download
   - Linux: see https://ngrok.com/download
2. Sign up at https://dashboard.ngrok.com and copy your authtoken from **Your Authtoken**.
3. Register the authtoken locally — once per machine:
   ```bash
   ngrok config add-authtoken <your-authtoken>
   ```

#### Each session

1. Make sure the local backend is running:
   ```bash
   cd velvet-elves-backend
   ./venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
   ```
2. In a second terminal, start the tunnel:
   ```bash
   ngrok http 8000
   ```
3. ngrok prints a public HTTPS URL like `https://a1b2c3d4.ngrok-free.app`. Copy it — this is your tunnel base URL.
4. Confirm the tunnel reaches your backend:
   ```bash
   curl https://a1b2c3d4.ngrok-free.app/api/v1/health
   ```
   Should return `200 OK`.

#### Register the tunnel as a Connect configuration

1. Back in https://apps-d.docusign.com/admin/connect, click **+ Add Configuration → Custom**.
2. Use the same form fields as **Step 5b**, but with **two differences**:
   - **Name**: `Velvet Elves — local (ngrok)`
   - **URL to Publish**: `https://a1b2c3d4.ngrok-free.app/api/v1/esign/webhooks/docusign` (substitute your actual ngrok subdomain)
3. Save.
4. Open the new configuration → **HMAC** tab → **Add Secret**. Copy the generated secret.
5. Add it to your **local** `velvet-elves-backend/.env` (this is in addition to the EC2 secret — they are independent):
   ```env
   DOCUSIGN_WEBHOOK_SECRET=local-ngrok-secret-from-docusign...
   ```
6. Restart the local backend so the new env value takes effect.

#### Verify

1. From the local frontend, send a test envelope and sign it.
2. ngrok's terminal should show an inbound `POST /api/v1/esign/webhooks/docusign` returning `200`.
3. The DocuSign **local** Connect configuration's **Logs** tab shows `Success 200`.
4. The local backend logs show the audit entry `esign_webhook` being written.

#### Caveats

- The free ngrok plan **rotates the subdomain every restart**. After every `ngrok http 8000` you must update the **URL to Publish** field on the local Connect configuration. To avoid this, either upgrade ngrok to a paid plan with a reserved domain, or use a free Cloudflare Tunnel with a custom hostname (`cloudflared tunnel --url http://localhost:8000`).
- Disable or delete the local Connect configuration when you are not actively testing — otherwise every real envelope signed in the shared dev DocuSign account will also try to fire at your laptop. Deletion in the Connect admin is one click and is reversible.
- If multiple developers each register their own tunnel, that is fine — DocuSign supports many configurations per account, and each one delivers independently.

## Step 6: Apply the database migration (one-time)

The DocuSign OAuth flow stores `account_id` and `base_uri` in a `metadata_json` JSONB column. Apply the migration to both your local Supabase and the dev Supabase:

```bash
# From velvet-elves-backend root
supabase db push
```

Or run the SQL manually in the Supabase dashboard SQL editor:

```sql
-- File: supabase/migrations/20260421_integration_metadata.sql
ALTER TABLE public.integrations
  ADD COLUMN IF NOT EXISTS metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb;
```

## Step 7: Test end to end

### On local

1. Start the frontend: `cd velvet-elves-frontend && npm run dev`
2. Sign in to the app at http://localhost:5173
3. Go to a transaction or All Documents
4. Click **Send for Signature**
5. In the modal, click **Connect DocuSign**
6. The wizard opens. Click **Continue to DocuSign**.
7. A popup opens to `account-d.docusign.com`. Sign in with your DocuSign user.
8. Click **Allow Access** when DocuSign prompts for consent.
9. Popup closes. Wizard advances to "DocuSign connected".
10. Send for Signature button is now enabled.

### On EC2 dev

Repeat the same steps against `https://dev.velvetelves.com/`. If anything fails on dev that worked locally, the difference is almost always the redirect URI registration or the `DOCUSIGN_REDIRECT_URI` env value.

## Troubleshooting

### "There are no redirect URIs registered with DocuSign"

The exact URI the backend sent does not match any URI registered on the Integration Key. To debug:

1. Open browser DevTools → Network tab
2. Trigger the connect wizard
3. Find the request to `POST /api/v1/integrations/docusign/authorize-url`
4. Look at the response JSON. The `redirect_uri` field is the exact string the backend will send to DocuSign.
5. Copy that string. Go back to DocuSign Admin → Apps and Keys → your app → Redirect URIs.
6. Add the exact string (or fix the registered one to match).

### Popup opens then immediately closes with no "connected" message

Browser blocked the postMessage from the callback page back to the opener. Causes:

- The OAuth callback is on a different origin than the frontend, and the browser is enforcing strict cross-origin messaging. The current implementation uses `targetOrigin: '*'` so this should work, but check the browser console on the popup before it closes.
- Ad blocker or privacy extension closed the popup.

### "invalid_client" error in DocuSign popup

The Integration Key or Secret in `.env` does not match what DocuSign expects, or the key lives in a different DocuSign environment (production vs demo).

- Confirm `DOCUSIGN_INTEGRATION_KEY` matches the GUID shown on the Apps and Keys page.
- Confirm `DOCUSIGN_OAUTH_BASE_URL` is `https://account-d.docusign.com` for demo.

### Connect succeeds but Send for Signature still fails

Check the backend logs. The most common cause is a missing or wrong DocuSign **account ID** or **base URI** lookup. The backend now reads these from the `metadata_json` column on the integration row. If that row was created before the metadata feature shipped, disconnect and reconnect to re-run the OAuth flow and repopulate metadata.

### Envelope was signed in DocuSign but the document is still listed as "Sent for Signature"

This means the Connect webhook never made it to the backend — or was rejected. There are now two recovery paths, and a permanent fix:

**Immediate recovery (per-document):**

- In the app, open **All Documents** (or any transaction's documents tab), find the stuck document, and click the circular **Refresh Signature Status** button that replaces "Send for Signature" while an envelope is in flight.
- This calls `POST /api/v1/documents/{id}/esign/sync`, which pulls live state from DocuSign, and — if DocuSign reports the envelope complete — runs the same auto-replace + auto-distribute pipeline a webhook would have.
- A toast confirms the new status (`Signature complete`, `Envelope voided`, etc.).

**Programmatic recovery:**

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  https://dev.velvetelves.com/api/v1/documents/$DOC_ID/esign/sync
```

Safe to invoke on any in-flight envelope; idempotent if the state is already current.

**Permanent fix — figure out why the webhook is missing:**

1. DocuSign admin → Connect → the configuration → **Logs**. If there is no entry for this envelope, DocuSign never tried to publish — check that the trigger events include "Envelope Signed/Completed" and that the envelope status in DocuSign actually advanced to Completed.
2. If the log shows `Failure 401`, HMAC verification failed. Re-sync the secret between the Connect configuration and `DOCUSIGN_WEBHOOK_SECRET` in `.env`.
3. If the log shows `Failure 5xx` or connection-refused, the backend was down or the URL is unreachable — confirm `https://dev.velvetelves.com/api/v1/esign/webhooks/docusign` resolves from outside your network (not just from EC2).
4. If the log shows `Failure 400`, the payload shape our endpoint expects does not match what DocuSign is sending. Inspect the body in the log and align the `EsignWebhookEvent` schema.

### Need to cancel a sent envelope

Any in-flight envelope exposes a **Void Envelope** action in the row's dropdown menu (internal roles only). This calls `POST /api/v1/documents/{id}/esign/void`, flips the document to `voided` locally, and tells DocuSign to revoke the signers' links. Use this before resending if a signer needs to be swapped or the subject was wrong.

## Production migration (later, not now)

The Apps and Keys page already shows the Velvet Elves app with **Go Live Status: "Ready to Submit / Promote to production"**. This means the demo Integration Key has accumulated enough successful API calls to be eligible for promotion. When ready to ship to real users:

1. On the Apps and Keys page, click **Promote to production** on the Velvet Elves row (or click the green status indicator). DocuSign will run an automated review of recent API requests and either approve immediately or queue for human review (typically 1-3 business days).
   - Alternative: if Audri prefers to keep the dev Integration Key untouched, generate a brand-new Integration Key in a paid production DocuSign account at https://admin.docusign.com.
2. Once promoted (or once the new prod key is created), register production redirect URIs against it, e.g. `https://app.velvetelves.com/api/v1/integrations/docusign/callback`.
3. Swap `DOCUSIGN_OAUTH_BASE_URL` to `https://account.docusign.com` (no `-d`) on the production backend.
4. Swap `DOCUSIGN_INTEGRATION_KEY`, `DOCUSIGN_SECRET_KEY`, and `DOCUSIGN_REDIRECT_URI` to the production values.

The code requires no changes for the prod swap. It is purely a config change.
