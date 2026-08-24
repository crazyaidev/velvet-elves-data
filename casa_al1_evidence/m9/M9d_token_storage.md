# M9d — Token storage

Google access and refresh tokens for Gmail and Google Calendar are stored in the `integrations` table (`access_token`, `refresh_token`, `provider_email`) **Fernet-encrypted** before write (`app/repositories/integration_repository.py` → `app/utils/encryption.py`).

- Algorithm: Fernet (AES-128-CBC + HMAC-SHA256) via `cryptography`.
- Key: `ENCRYPTION_KEY` in the API environment (ECS task definition / Secrets Manager — not in git). Production startup fails if the key is missing.
- Who can decrypt: the backend process that holds `ENCRYPTION_KEY`. Application operators do not have a mailbox-level UI that dumps raw tokens. Platform admin is a product role, not a Google-token export.
- OAuth: authorization-code + PKCE. Tokens are not stored in the SPA.
- Disconnect (`DELETE /integrations/{provider}`) sets `is_active=false`. Encrypted tokens **remain on the row** until a later wipe or tenant purge. Product code only loads active integrations.
- Session JWT for the Velvet Elves user is **not** a Google token; it is a Supabase-issued JWT kept in the SPA `localStorage` keys `velvet_elves_token` / `velvet_elves_refresh_token` (see self-attestation compensating control).
