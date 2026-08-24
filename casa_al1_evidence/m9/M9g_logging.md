# M9g — Logging

Production logs are **JSON lines** with a request id (`app/utils/logging.py`). There is no log sink that is supposed to hold Gmail bodies or OAuth tokens.

## What is logged (Gmail path)

- Connected/disconnected: `provider` + `user_id` (UUID), not the access token.
- Mailbox identifiers in Gmail client logs go through `_mask_email` (`app/services/email/gmail_provider.py`): `ab***@domain`.
- Pub/Sub: JWT validation failures log *that* validation failed (kid missing, issuer mismatch). The raw push JWT is not written as a successful payload dump.
- Inbound webhook: `user_id`, content-type, accept/reject reason.

## What is not supposed to be in logs

- Access/refresh tokens, PKCE verifier, auth codes.
- Full email bodies / HTML. Bodies live in `communication_logs` (application data), not the log stream.
- Raw Pub/Sub message data beyond a small summary helper.

## Proof in tests (narrow)

- `_mask_email` is used on Gmail list/watch/send paths (code inspection 21 Aug 2026).
- There is **no** automated “scanner grepped logs for tokens” job yet. Do not claim one.

CloudWatch (API) and browser consoles are out of this file. Operators with AWS/Supabase admin can still see ciphertext or decrypt with `ENCRYPTION_KEY` (see self-attestation).
