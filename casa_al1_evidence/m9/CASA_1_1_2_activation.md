# CASA 1.1.2 — System generated initial passwords or activation codes shall be securely randomly generated and expire after a short period

**Source:** ADA Web App Test Guide v1.0 (10 Oct 2024), AL1 evidence + verification.  
**ASVS:** 2.3.1  
**Date:** 27 Aug 2026  
**Do not claim:** that Supabase is an ADA-approved IdP; that invite links expire within 48 hours (they currently expire in 72 hours); that we issue a generated initial password.

## AL1 evidence the lab asked for

### 1. External user authentication services

| Service | Used for | ADA-approved IdP? |
| --- | --- | --- |
| **Supabase Auth (GoTrue)** | Email/password register, invite accept, password reset, email confirmation | **Not claimed.** |
| **Google OAuth (code + PKCE)** | Gmail/Calendar integrations only | Out of scope for 1.1.2. |

### 2. Initial password / activation process

Velvet Elves **does not generate initial passwords**. A user always chooses their own long-term password:

- Self-register: the registrant sets the password (`POST /users/register`, min 8 + digit + denylist).
- Invite accept: the invitee sets the password (`POST /invitations/accept/{token}`). The invite token is **not** the password.
- Password reset: the user sets a new password from a one-time Supabase recovery link. The recovery token cannot remain as the password.

**Invite activation token (our proprietary wrapper around GoTrue):**

- Generated with `uuid.uuid4().hex` — 32 hex characters (letters a–f and digits), 128 bits of randomness (`InvitationRepository.create`).
- Stored on `invitation_tokens`. Marked `is_used` after accept; reused tokens return 410.
- Expired, missing, or revoked tokens return 404/410. The SPA shows “Invalid Invitation”.
- Default lifetime: **72 hours** (`_DEFAULT_EXPIRY_HOURS`). ADA 1.1.2 verification 2.3 recommends 24 hours and **caps at 48 hours**. We do not claim the 48-hour cap. Compensating: the token is not a password, is single-use, and is 32 hex characters. An admin “extend” adds another 72 hours to the same token.
- Email copy currently says “The link expires in 72 hours.”

**Password reset:** `POST /users/password-reset/request` calls `supabase.auth.reset_password_email`. Confirm uses the recovery token once, then the user picks a new password that must differ from the old one. Opening `/reset-password` without a token shows “Invalid or expired link”.

### 3. Screenshots

1. Invite accept with a non-existent token → Invalid Invitation (expiry/one-time enforcement).
2. Forgot-password form (no generated password is mailed as a standing credential).
3. Reset-password page with no token → Invalid or expired link.

## Verification mapping (AL1)

ADA: ADA-approved IdP **or** document 2.1–2.4 for proprietary initial passwords/codes.

| Control | Velvet Elves |
| --- | --- |
| 1 ADA-approved IdP | Not claimed. |
| 2.1 Codes at least 6 characters | **Pass.** Invite token is 32 hex characters. |
| 2.2 Letters and numbers | **Pass.** Hex alphabet (0-9, a-f). |
| 2.3 Expire within 48 hours | **Not claimed.** Invite TTL is 72 hours (extend adds 72). Reset uses vendor recovery (attach Supabase email/OTP settings if available — do not invent the number). |
| 2.4 Must not become the long-term password | **Pass.** Invitee/registrant/reset user always sets their own password. Token is discarded after use. |

## Portal comment

```
Velvet Elves does not issue system-generated initial passwords. Users choose their own password on register, invite accept, and password reset. Invite activation tokens are 32-character hex (uuid4), single-use, and cannot become the account password. Used, revoked, or unknown tokens return 410/404. Invite links currently expire after 72 hours (ADA 1.1.2 recommends 24h and caps at 48h; we do not claim the 48h cap). Password reset uses a one-time Supabase recovery link; a missing/expired link cannot set a password.
```
