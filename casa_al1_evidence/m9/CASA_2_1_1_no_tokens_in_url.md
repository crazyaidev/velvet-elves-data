# CASA 2.1.1 — URLs shall not expose authentication material

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 3.1.1  
**Date:** 28 Aug 2026  

## ADA AL1 evidence

Testing results from a scan completed using ADA DAST guidance (ZAP with official `zap-casa-config.conf` / `zap-casa-api-config.conf`).

Verification:

1. Scan shall not identify: Password submitted using GET (Burp 4195072); Password returned in URL query string (4195328); Session token in URL (5244672). ZAP equivalents in the ADA config are **FAIL**: plugin **3** (Session ID in URL Rewrite) and **10024** (Sensitive Information in URL).
2. Sensitive data shall not be sent via the URL, **or** an option shall exist to send it in the HTTP body or headers.

## How Velvet Elves sends secrets

| Material | How it is sent | In the URL? |
| --- | --- | --- |
| Login password | `POST /users/login` form body (`username` + `password`) | **No.** GET with password in the query does not authenticate (401). |
| Session JWT | `Authorization: Bearer` (`apiFetch`). Stored in `localStorage` keys `velvet_elves_token` / `velvet_elves_refresh_token` | **No.** `GET /users/me?access_token=…` is ignored; still unauthenticated. |
| Google OAuth tokens | Authorization code + PKCE. Callback HTML `postMessage`s the opener; tokens are Fernet-encrypted in `integrations`. Not stored in the SPA. | **No** session JWT in the SPA query string. |
| Password-reset confirm | JSON body to `POST /users/password-reset/confirm` | Recovery email may use a URL **fragment** (`#access_token=`), which is not a query string and is not sent to the API. Confirm is POST body. |

Official DAST (builds `10f54abf` SPA, `a9d78f05` API, `33afa2aa` auth API): **0 High**. Alert lists in `DAST_SUMMARY.md` do not include Session ID in URL or Sensitive Information in URL. Those rules are FAIL in the CASA ZAP config, so a finding would have been listed.

## Capability tokens that are not the session JWT

Invite accept emails use `/invite/accept?token=` (activation token; 1.1.2). Public invoice pay links and a fulfilled communications-export download may include a short-lived capability `token` query param. Those are not the user session JWT. Export download still requires `Authorization: Bearer`.

## Portal comment

```
Login is POST /users/login with the password in the request body, never as a GET query parameter. The session JWT is sent as Authorization Bearer, not in the URL. Official ADA ZAP scans of the SPA and API did not report Session ID in URL or Sensitive Information in URL. Google OAuth returns tokens to a popup via postMessage. Password-reset confirm posts the recovery token in the JSON body. Invite accept and public invoice links may include a one-time capability token in the query; those are not the user session JWT.
```
