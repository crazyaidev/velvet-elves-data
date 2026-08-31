# CASA 1.1.3 — Passwords shall be stored in a form that is resistant to offline attacks

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 2.4.1  
**Date:** 27 Aug 2026  
**Do not claim:** that Supabase is an ADA-approved IdP; that Velvet Elves hashes passwords in application code; that we inspected production `auth.users.encrypted_password` values.

## AL1 evidence the lab asked for

### 1. External user authentication services

| Service | Used for | ADA-approved IdP? |
| --- | --- | --- |
| **Supabase Auth (GoTrue)** | Register, login, invite accept, password reset. Owns credential storage. | **Not claimed.** |
| **Google OAuth (code + PKCE)** | Gmail/Calendar tokens (Fernet at rest). Not login passwords. | Out of scope for 1.1.3. |

### 2. Password storage methods

Velvet Elves **does not store user passwords** in application tables.

- `POST /users/register` → `supabase.auth.sign_up()`
- `POST /users/login` → `supabase.auth.sign_in_with_password()`
- Invite accept / password reset update the password through GoTrue admin or recovery APIs
- `public.users` is an application profile keyed by the Auth user UUID. Columns are id, tenant, encrypted PII, role, flags — **no password column**. Inserts in `UserRepository.create` never include a password field. PII (email, name, phone) is Fernet-encrypted; that is not password hashing.

GoTrue stores a **salted bcrypt hash** in `auth.users.encrypted_password` (column name is a misnomer; it is a hash, not reversible encryption). Official source: https://supabase.com/docs/guides/auth/password-security ("How are passwords stored?"). bcrypt is a NIST SP 800-63B §5.1.1.2 one-way key derivation function. Portal image `CASA_1_1_3_supabase_docs.png` is **owner-captured** from that docs site — do not replace it with an agent screenshot.

We do not operate a custom password hasher and we do not log passwords (see 6.5.1).

## Verification mapping

| Control | Velvet Elves |
| --- | --- |
| ADA-approved IdP | Not claimed. |
| NIST 800-63B KDF for password storage | **Pass via vendor.** GoTrue bcrypt + per-hash salt. Application code never persists the password. |

## Portal comment

```
User passwords are not stored in Velvet Elves tables. Login and register call Supabase Auth (GoTrue). GoTrue stores a salted bcrypt hash in auth.users.encrypted_password (hash, not reversible encryption; see supabase.com/docs/guides/auth/password-security). public.users is a profile row with no password column. We do not operate a custom password hasher. Google OAuth tokens are Fernet-encrypted separately and are not login passwords.
```
