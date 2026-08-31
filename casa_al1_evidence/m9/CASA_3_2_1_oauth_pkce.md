# CASA 3.2.1 — OAuth uses authorization code + PKCE (no implicit / ROPC)

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**Date:** 31 Aug 2026  

ADA AL1: if the app uses OAuth 2.0, describe which flow, with evidence. Verification: documentation shall **not** indicate a deprecated flow (Implicit, or Resource Owner Password Credentials).

## Which OAuth 2.0 flows Velvet Elves uses

All OAuth clients use **authorization code** with **PKCE (S256)**. None use Implicit (`response_type=token`) or ROPC against Google/Microsoft/DocuSign.

| Integration | Start | Authorize params |
| --- | --- | --- |
| Google / Microsoft **sign-in** | `POST /users/oauth/{provider}/start` | Supabase `/auth/v1/authorize` with `code_challenge` + `code_challenge_method=s256`. Exchange uses `code_verifier`. |
| Gmail / Outlook **mailbox** | `POST /integrations/gmail\|outlook/authorize-url` | `response_type=code`, `code_challenge`, `code_challenge_method=S256` |
| Google Calendar | `POST /calendar/google/authorize-url` | Same PKCE as Gmail |
| DocuSign | `POST /integrations/docusign/authorize-url` | `response_type=code`, PKCE S256 |

Email/password login is Supabase `sign_in_with_password`. That is **not** an OAuth ROPC grant to Google.

## Staging measurement (31 Aug 2026)

See `CASA_3_2_1_pkce.png`.

- `POST /users/oauth/google/start` with `redirect_to=https://app.stage.velvetelves.com/oauth/callback` → **200**. Returned URL is `/auth/v1/authorize` with `code_challenge_method=s256` and a `code_challenge`. No `response_type=token`. Flow was **not** completed (no exchange, no new user).
- Unsigned `POST /integrations/gmail/authorize-url` → **401** (mailbox OAuth is session-bound).

Do not recapture Google Cloud Console or accounts.google.com. Do not attach `/login`.

Production Google Cloud client **Velvet Elves API – production** (31 Aug 2026): type **Web application**; redirect URIs are production Gmail, Calendar, and Supabase Auth callbacks. Client secret redacted on the packed PNG.

## Tests (names to cite)

`test_oauth_state_is_stateless_and_roundtrips` — PKCE verifier is inside Fernet `state`, not plaintext.  
`test_oauth_exchange_rejects_tampered_state` — garbage state → 400 before exchange.

## Do not claim

- Implicit flow or Google ROPC.
- That Google Sign-in is out of scope (it is an OAuth code+PKCE login path; Gmail/Calendar are separate).
- A live completed consent this session.
- That the GCP Web-client shot proves PKCE (PKCE is in the start URL).
- HttpOnly cookies; MFA for all users.

## Portal comment

```
Velvet Elves OAuth is authorization code with PKCE (S256). Google and Microsoft sign-in start at POST /users/oauth/{provider}/start and pass code_challenge to Supabase /auth/v1/authorize. Gmail, Outlook, Calendar, and DocuSign authorize URLs set response_type=code plus code_challenge_method=S256. There is no implicit flow and no resource-owner password grant to those providers. The production Google Cloud OAuth client is a Web application with HTTPS Gmail, Calendar, and Supabase Auth callback URIs. Staging POST /users/oauth/google/start returned a PKCE authorize URL (s256); the flow was not completed. Unsigned POST /integrations/gmail/authorize-url returns 401.
```
