# DocuSign Setup Guide for Velvet Elves

This guide configures DocuSign so the in-app "Connect DocuSign" wizard works for both local development and the dev deployment.

## Environment summary

| Environment | Backend callback URL (must be registered in DocuSign)                            |
| ----------- | -------------------------------------------------------------------------------- |
| Local dev   | `http://localhost:8000/api/v1/integrations/docusign/callback`                    |
| EC2 dev     | `https://dev.velvetelves.com/api/v1/integrations/docusign/callback`              |

The DocuSign **redirect URI** must point to the **backend** callback endpoint (not the frontend). The endpoint path is always `/api/v1/integrations/docusign/callback`.

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
DOCUSIGN_OAUTH_BASE_URL="xxx"
DOCUSIGN_SCOPES="xxx"
DOCUSIGN_REDIRECT_URI="xxx"
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
DOCUSIGN_INTEGRATION_KEY="b69b0237-468f-4b71-9c8a-68dfe3c82664"
DOCUSIGN_SECRET_KEY="fae3fe29-2c27-4b20-8087-f6aae9e01ede"
DOCUSIGN_OAUTH_BASE_URL="https://account-d.docusign.com"
DOCUSIGN_SCOPES="signature"
DOCUSIGN_REDIRECT_URI="https://dev.velvetelves.com/api/v1/integrations/docusign/callback"
```

Restart the backend service so the new env vars take effect (use whichever process manager the deployment uses: `systemctl restart`, `pm2 restart`, `docker compose restart`, etc.).

## Step 5: Apply the database migration (one-time)

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

## Step 6: Test end to end

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

## Production migration (later, not now)

The Apps and Keys page already shows the Velvet Elves app with **Go Live Status: "Ready to Submit / Promote to production"**. This means the demo Integration Key has accumulated enough successful API calls to be eligible for promotion. When ready to ship to real users:

1. On the Apps and Keys page, click **Promote to production** on the Velvet Elves row (or click the green status indicator). DocuSign will run an automated review of recent API requests and either approve immediately or queue for human review (typically 1-3 business days).
   - Alternative: if Audri prefers to keep the dev Integration Key untouched, generate a brand-new Integration Key in a paid production DocuSign account at https://admin.docusign.com.
2. Once promoted (or once the new prod key is created), register production redirect URIs against it, e.g. `https://app.velvetelves.com/api/v1/integrations/docusign/callback`.
3. Swap `DOCUSIGN_OAUTH_BASE_URL` to `https://account.docusign.com` (no `-d`) on the production backend.
4. Swap `DOCUSIGN_INTEGRATION_KEY`, `DOCUSIGN_SECRET_KEY`, and `DOCUSIGN_REDIRECT_URI` to the production values.

The code requires no changes for the prod swap. It is purely a config change.
