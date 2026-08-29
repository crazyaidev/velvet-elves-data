# CASA 2.3.3 — Session tokens rather than static API secrets and keys

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 3.5.2  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

Code snippets of session token creation showing dynamically generated tokens, **or** documentation of how session tokens are dynamically generated.

Verification: session tokens shall be **dynamically generated after user authentication**.

Exception: legacy implementations that still use static API secrets.

## User session (this row)

After a correct password, `AuthService.login` calls GoTrue `sign_in_with_password`. GoTrue returns a **new** `session.access_token` and `session.refresh_token` for that sign-in. The API returns them in `TokenResponse`. The SPA sends `Authorization: Bearer`. A later login issues a different JWT (`iat` changes).

Staging 28 Aug 2026: two successive logins on `api.stage.velvetelves.com` produced two different `iat` values. Tokens were not printed.

Google Sign-in / MFA verify also receive a GoTrue session JWT, not a shared static key.

## Not the user session

| Secret | What it is |
| --- | --- |
| Gmail / Calendar OAuth tokens | Per-user tokens in `integrations`, Fernet-encrypted. Not a shared mailbox API key. Not the login session. |
| Tenant inbound CRM keys (`vek_…`, `X-API-Key`) | Machine path to push contacts. Created with `secrets.token_urlsafe`; stored as SHA-256. Managing keys requires an admin **JWT**. These keys do not log a human into the SPA. |
| OpenAI / Stripe / SendGrid / Supabase service role | Backend service secrets. Not issued to the browser as the user session. |

## Do not claim

- That the product has no API keys anywhere.
- That inbound CRM keys are the user session.
- HttpOnly session cookies; pasting JWTs or key values.

## Portal comment

```
User login does not use a static API key. After a correct password, Supabase Auth issues a new JWT and refresh token for that session. Two successive staging logins produced different iat values. The app sends Authorization Bearer. Gmail and Calendar use that user's OAuth tokens, not a shared mailbox key. Tenant inbound CRM keys (X-API-Key) are a separate machine path for contact push; they are not the user session.
```
