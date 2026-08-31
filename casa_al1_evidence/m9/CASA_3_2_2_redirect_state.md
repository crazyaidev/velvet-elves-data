# CASA 3.2.2 — OAuth redirect_uri and state prevent open redirect / CSRF

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 4.0.3 (OAuth client `redirect_uri` / `state`)  
**Date:** 31 Aug 2026  

ADA AL1: if the app uses OAuth 2.0, written description plus evidence of how **state** and **redirect_uri** prevent open redirect and OAuth CSRF. Verification: those parameters are used securely. WSTG-ATHZ-05 is AL2; we did not run it.

## How Velvet Elves uses redirect_uri and state

### Sign-in (Google / Microsoft via Supabase)

- `POST /users/oauth/{provider}/start` takes `redirect_to`. `validate_redirect_to` (`app/utils/redirects.py`) requires the URL origin to match `CORS_ORIGINS`. A foreign origin returns **400** `redirect_to is not an allowed origin.`
- `state` is a Fernet token (PKCE verifier + provider). TTL **10 minutes**. Exchange (`POST /users/oauth/{provider}/exchange`) calls `_decode_state`; missing, tampered, expired, or provider-mismatched state returns **400** `Invalid or expired OAuth state.` before any code exchange.

This is an **origin** allowlist, not a single exact path. Tokens cannot be sent to `evil.example`.

### Mail, calendar, DocuSign

- `redirect_uri` is **server-derived** (`gmail_redirect_uri` / settings, or `request.url_for(callback)`). The SPA does not supply it.
- `state` encrypts `user_id`, provider, `redirect_uri`, and the PKCE verifier (same 10-minute Fernet TTL). The callback exchanges using `state_data.redirect_uri`. Garbage state: Gmail `Invalid or expired Google OAuth state.`

### Popup postMessage

Callback HTML `postMessage`s to `FRONTEND_URL` origin (`frontend_post_message_origin()`), not `*`. The SPA ignores messages unless `isTrustedOAuthMessageOrigin` matches the API host.

## Staging measurement (31 Aug 2026)

See `CASA_3_2_2_deny.png`.

- `POST /users/oauth/google/start` with `redirect_to=https://evil.example/steal` → **400**.
- Same start with `https://app.stage.velvetelves.com/oauth/callback` → **200** (flow not completed).
- `POST /users/oauth/google/exchange` with garbage `state` → **400** `Invalid or expired OAuth state.`

Do not recapture Google Cloud Console. Do not complete consent. Do not attach `/login`.

Production Google Cloud authorized redirect URIs (same PNG as 3.2.1): Gmail callback, Calendar callback, Supabase Auth callback. Secret redacted.

## Tests (names to cite)

`test_oauth_exchange_rejects_tampered_state` — garbage Fernet → 400.  
`test_oauth_exchange_rejects_provider_mismatch` — Azure state on Google exchange → 400.  
`test_email_oauth_callback_html_does_not_use_wildcard_origin` — postMessage target is the SPA origin.  
`test_email_oauth_state_rejects_garbage` — decode returns None.

## Do not claim

- WSTG-ATHZ-05 / AL2 lab testing.
- That sign-in `redirect_to` is an exact-path match (it is origin vs CORS).
- A completed consent this session.
- That GCP registered URIs replace API origin checks.
- HttpOnly cookies; MFA for all users.

## Portal comment

```
OAuth redirect_uri and state are validated to prevent open redirect and OAuth CSRF. Google and Microsoft sign-in redirect_to must match an allowlisted SPA origin; a foreign origin returns 400. Sign-in state is a Fernet token with a 10-minute TTL; a forged state on POST /users/oauth/google/exchange returns 400 Invalid or expired OAuth state. Gmail, Outlook, Calendar, and DocuSign redirect_uri is set by the API from configuration, not by the client. Google Cloud lists the production Gmail, Calendar, and Supabase Auth callback URIs as authorized redirects. Integration state binds user, provider, and redirect_uri. Callback postMessage targets FRONTEND_URL, not *. Staging: foreign redirect_to 400; garbage state 400.
```
