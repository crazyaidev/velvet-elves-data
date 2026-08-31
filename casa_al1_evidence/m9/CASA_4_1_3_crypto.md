# CASA 4.1.3 — No weak cryptography that meaningfully impacts confidentiality or integrity

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** (guide lists 4.1.3 without a single ASVS id)  
**Date:** 31 Aug 2026  

ADA AL1: describe encryption, hashing, and MAC/HMAC (algorithms, key size, IV, key management). Baseline SP.800-57p1r5 / SP.800-131Ar2, **112-bit** security (SHA-224+, RSA 2048 / ECC 224).

## Encryption / decryption

| Item | Velvet Elves |
| --- | --- |
| Algorithm | Fernet: AES-128-CBC + HMAC-SHA256 (`cryptography`) |
| Key | 256-bit Fernet key (`ENCRYPTION_KEY`) in AWS Secrets Manager / ECS. Production `_load_fernet` raises if missing. |
| IV | Fresh 128-bit IV per token (Fernet library). Not a static IV in app code. |
| Used for | Integration OAuth tokens, selected PII (email, name, phone, address), OAuth `state` |
| Not | Browser end-to-end encryption. The API decrypts to call Gmail/Calendar. |
| Rotation | Planned ops task. **No rotation drill attached.** |

`decrypt` returns legacy non-`gAAAAA` strings as-is. Invalid Fernet raises `ValueError` (see 4.1.4).

## Hashing

- Passwords: salted **bcrypt** in GoTrue (1.1.3). Not in `public.users`.
- Capability secrets (share links, colleague tokens, CRM keys): **SHA-256** of the secret stored, not the secret.
- PKCE: **S256** (SHA-256).
- Email fingerprints / similar ids: SHA-256.

## MAC / HMAC / signatures

- Fernet HMAC-SHA256 on ciphertext.
- Webhooks / e-sign callbacks: HMAC-SHA256.
- Session JWT: ES256 (P-256) or HS256, verified with `jose`.
- TOTP: HMAC-SHA1 per **RFC 6238** (authenticator codes), not PII at rest.

## SHA-1 that is not secret crypto

`_proposal_id` in `intake_intelligence.py` uses `hashlib.sha1(...).hexdigest()[:16]` as a short intake proposal label. Fluid SAST **F052 Low**. Compensating: not a password KDF, token MAC, or PII cipher.

TLS: Qualys **A+** (4.1.1). The API report still lists two TLS 1.2 CBC suites as WEAK; modern clients negotiate TLS 1.3 AES-GCM. Do not claim the API has no Qualys-flagged weak ciphers.

## Do not claim

- AES-256 (Fernet is AES-128-CBC; 128-bit still meets the 112-bit baseline).
- A completed key-rotation drill.
- That SHA-1 is unused.
- Production hash dumps or Fernet keys in screenshots.
- HttpOnly session cookies; MFA for all users.

## Portal comment

```
Confidential data uses Fernet (AES-128-CBC plus HMAC-SHA256) with a 256-bit key stored as ENCRYPTION_KEY in AWS Secrets Manager. Production fails to start if the key is missing. Fernet issues a fresh 128-bit IV per token. That covers OAuth tokens, selected PII, and OAuth state. User passwords are salted bcrypt in Supabase GoTrue, not in application tables. Capability secrets are stored as SHA-256 hashes. Webhooks use HMAC-SHA256. Session JWTs are ES256 or HS256. SHA-1 appears only as a 16-character intake proposal id (not a password or token MAC). No encryption keys are attached.
```
