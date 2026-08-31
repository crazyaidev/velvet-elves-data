# CASA 4.1.4 — Cryptographic modules fail securely

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 6.2.1  
**Date:** 31 Aug 2026  

ADA AL1: describe how crypto failures are handled. Errors must not disclose operation state or enable a padding oracle. User-facing messages stay vague and consistent. WSTG-CRYP-02 is AL2.

## Fernet

HMAC-SHA256 is verified before AES-CBC decrypt. A flipped HMAC byte and a flipped ciphertext byte both raise `InvalidToken`. `decrypt()` maps that to `ValueError("Decryption failed — invalid or corrupted ciphertext.")`. Display helpers `_safe_decrypt` / `_safe_decrypt_value` catch `Exception` and return `""` or `None` so the UI never shows `gAAAA` ciphertext.

Live 31 Aug 2026 (ephemeral key, not `ENCRYPTION_KEY`): both mutations → `InvalidToken`, no plaintext in the exception.

## OAuth state and JWT

`_decode_state` returns `None` on `InvalidToken` / parse errors. Exchange returns **400** `Invalid or expired OAuth state.` Staging garbage state: **400**.

`decode_access_token` raises `JWTError`. `get_current_user` maps that to **401** `Could not validate credentials.` Staging `GET /users/me` with `Bearer not-a-jwt`: **401**.

## Padding oracle

No application CBC decrypt returns distinct padding errors. Fernet HMAC failure and payload failure are the same `InvalidToken`. This pack does **not** claim a WSTG-CRYP-02 lab scan. Legacy rows that do not start with `gAAAAA` are returned as-is (plaintext migration).

## Do not claim

- A completed WSTG-CRYP-02 padding-oracle scan.
- That every historical DB row is ciphertext (legacy passthrough).
- Fernet keys, JWTs, or plaintext PII in screenshots.
- HttpOnly session cookies; MFA for all users.

## Portal comment

```
Cryptographic failures fail closed and do not return plaintext. Fernet verifies HMAC-SHA256 before AES-CBC decrypt; a bad MAC and a flipped ciphertext byte both raise InvalidToken, mapped to a generic Decryption failed error. Display helpers return empty on any decrypt exception so ciphertext is not shown in the UI. OAuth state decode returns None on InvalidToken; exchange is 400 Invalid or expired OAuth state. Invalid JWTs raise JWTError and become 401 Could not validate credentials. Staging: GET /users/me with Bearer not-a-jwt is 401; POST /users/oauth/google/exchange with garbage state is 400.
```
