# CASA AL1 — portal pack (comments and image descriptions)

**Filename (fixed):** `casa_al1_evidence/m9/CASA_PORTAL_PACK.md` — do not rename. Append new rows here; update the scope line only.  
**Updated:** 28 Aug 2026  
**Rows in this file:** 1.1.1, 1.1.2, 1.1.3, 1.2.1, 1.3.1, 1.3.2, 1.3.3, 1.3.4, 2.1.1, 2.2.1, 2.2.2, 2.2.3, 2.3.1, 2.3.2, 2.3.3, 2.3.4, 2.4.1  
**Portal:** https://casa.tacsecurity.com/ — per-row **Upload Evidences** (PNG/JPG/JPEG, max 10). Do not upload this markdown.  
**Images:** `casa_al1_evidence/m9/tac_images/<check-id>/` — one folder per row. MFA shots for later row 3.3.1 are in `tac_images/3.3.1/` (do not attach those on 1.1.x / 1.2.1).  
**Operating guide:** `CASA/TAC_ESOF_PORTAL_GUIDE.md` §7  
**ADA source:** [Web App Test Guide v1.0](https://github.com/appdefensealliance/ASA-WG/blob/v1.0/Web%20App%20Profile/Web%20App%20Test%20Guide.md)

Do not check “I confirm…” or click Evidence **Submit** until all 48 rows are filled.

**Screenshot rule:** agent captures Velvet Elves only (`app.` / `api.` staging or production, plus our own write-up PNGs). Screenshots of other products (Supabase dashboard, supabase.com docs, SSL Labs, AWS, Google Cloud) are owner-captured. If one is needed, the agent will ask and give guidelines — it will not take the shot. Write-up PNGs are for TAC: cite ADA/ASVS, state what the product does. Keep internal “do not claim” / portal-process notes in this markdown only — never on images the lab will see. Do **not** attach `/login` unless that screen is the evidence for the check (today: 2.1.1 address bar, 2.2.2 Forgot password).

---

## How to use this file

1. Open the matching row in TAC (eye icon / View Details).
2. Paste the **portal comment** for that row (punctuation is allowed). Do not paste secrets.
3. Open that row’s folder under `tac_images/` and attach only those PNGs. Do **not** attach MFA shots from `tac_images/3.3.1/`.
4. Source write-ups stay in this folder; they are not portal uploads.

Global do-not-claim (these rows): HttpOnly session cookies; MFA default for **all** users; live HIBP API; ADA-approved IdP for Supabase; production hash dumps; API keys / JWTs / Fernet keys in screenshots.

| Row | ID | Title | PNG count | Source write-up |
| --- | --- | --- | ---: | --- |
| 1 | 1.1.1 | Authentication is resistant to brute force attacks | 6 | `CASA_1_1_1_brute_force.md` |
| 2 | 1.1.2 | Initial passwords / activation codes expire | 5 | `CASA_1_1_2_activation.md` |
| 3 | 1.1.3 | Passwords stored resistant to offline attacks | 4 | `CASA_1_1_3_password_storage.md` |
| 4 | 1.2.1 | Default credentials shall not be present | 5 | `CASA_1_2_1_default_credentials.md` |
| 5 | 1.3.1 | Out of band verifier shall expire | 6 | `CASA_1_3_1_oob_expiry.md` |
| 6 | 1.3.2 | Out of band verifier shall only be used once | 4 | `CASA_1_3_2_oob_single_use.md` |
| 7 | 1.3.3 | Out of band verifier shall be securely random | 7 | `CASA_1_3_3_oob_random.md` |
| 8 | 1.3.4 | Out of band verifier shall be resistant to brute force attacks | 6 | `CASA_1_3_4_oob_bruteforce.md` |
| 9 | 2.1.1 | URLs shall not expose authentication material | 5 | `CASA_2_1_1_no_tokens_in_url.md` |
| 10 | 2.2.1 | Logout invalidates stateful session tokens | 6 | `CASA_2_2_1_logout.md` |
| 11 | 2.2.2 | Terminate other sessions after password change | 7 | `CASA_2_2_2_password_change_sessions.md` |
| 12 | 2.2.3 | Stateless authentication tokens expire within 24 hours | 4 | `CASA_2_2_3_stateless_expiry.md` |
| 13 | 2.3.1 | Cookie-based session tokens shall have the Secure attribute | 5 | `CASA_2_3_1_cookie_secure.md` |
| 14 | 2.3.2 | Cookie-based session tokens shall have the HttpOnly attribute | 5 | `CASA_2_3_2_cookie_httponly.md` |
| 15 | 2.3.3 | Session tokens rather than static API secrets and keys | 4 | `CASA_2_3_3_session_not_static_key.md` |
| 16 | 2.3.4 | Stateless session tokens shall use digital signatures | 5 | `CASA_2_3_4_signed_jwt.md` |
| 17 | 2.4.1 | Full login session or re-auth before sensitive account changes | 5 | `CASA_2_4_1_sensitive_changes.md` |

---

## 1.1.1 — Authentication is resistant to brute force attacks

**ADA:** at least **one** of 2.1–2.5 (or ADA-approved IdP). Velvet Elves claims **2.1** and **2.4**. CAPTCHA (2.2) is not implemented and is not required if 2.1/2.4 hold. MFA-for-all (2.3) is not claimed.

**Claimed controls**

- Login: 10 requests / 60 s / IP (`_login_limiter`).
- Per-account lockout: 20 failed attempts / rolling hour (`app/core/login_throttle.py`). Two backend tasks → worst case 40/hour, still ≤100.
- Register: 5 requests / 60 s / IP.
- Passwords: min 8 + digit + static common-password denylist (`app/core/weak_passwords.py`). Not a live HIBP API.
- TOTP MFA is enforced for **platform admins**, not all users (see 3.3.1; do not attach those images here).

**Do not claim:** CAPTCHA; MFA for all users; live HIBP; ADA-approved IdP; that the Supabase dashboard 30/5 min/IP limit is the 2.1 proof (that is per-IP, not per-account). Live 20-failure lockout from one IP is impractical because the IP limiter fires first — cite `test_login_account_lockout_survives_ip_rotation`.

**Helpers:** `casa_auth_qa/render_casa_111_pages.py`, `casa_111_live_evidence.py`, `casa_111_password_ui.mjs`

### Images

| File | Description |
| --- | --- |
| [`tac_images/1.1.1/CASA_1_1_1_page1.png`](tac_images/1.1.1/CASA_1_1_1_page1.png) | Written evidence page 1 of 2. Lists external auth (Supabase GoTrue, Google OAuth out of scope), password policy (min 8, digit, static denylist, SPA complexity), and anti-automation (login 10/min/IP, 20 failures/account/hour, register 5/min, no CAPTCHA, MFA for platform admins only). |
| [`tac_images/1.1.1/CASA_1_1_1_page2.png`](tac_images/1.1.1/CASA_1_1_1_page2.png) | Written evidence page 2 of 2. AL1 mapping: not an ADA-approved IdP; **PASS** on 2.1 and 2.4; 2.2/2.3/2.5 not claimed. Notes lockout test vs live IP limiter. |
| [`tac_images/1.1.1/CASA_1_1_1_login_429.png`](tac_images/1.1.1/CASA_1_1_1_login_429.png) | Live staging: repeated `POST /users/login` from one IP; after 10 requests in 60 s the API returns **429**. This is the in-app IP limiter, not the per-account lockout. |
| [`tac_images/1.1.1/CASA_1_1_1_register_429.png`](tac_images/1.1.1/CASA_1_1_1_register_429.png) | Live staging: sixth rapid `POST /users/register` in one minute returns **429** (5 / 60 s limiter). |
| [`tac_images/1.1.1/CASA_1_1_1_password_rules.png`](tac_images/1.1.1/CASA_1_1_1_password_rules.png) | Staging register UI password rules (length + complexity). API additionally requires a digit and rejects the static denylist (e.g. `password123` → 422). |
| [`tac_images/1.1.1/CASA_1_1_1_supabase_rate_limits.png`](tac_images/1.1.1/CASA_1_1_1_supabase_rate_limits.png) | Production Supabase dashboard → Authentication → Rate Limits. Vendor backup only: 30 sign-in requests / 5 min / IP. **Not** the ADA 2.1 per-account proof. No project keys in frame. |

### Portal comment

```
Login is rate-limited to 10 requests/minute/IP and locked after 20 failed attempts per account per hour. Passwords require min 8 characters, a digit, and reject common passwords (static denylist, not a live HIBP API). Register is rate-limited to 5/minute. TOTP MFA is enforced for platform admins (not all users). CAPTCHA is not used; ADA 1.1.1 is met via options 2.1 and 2.4. Supabase vendor limits apply on top (30 sign-in requests / 5 min / IP).
```

---

## 1.1.2 — Initial passwords / activation codes expire

**ADA:** for proprietary codes, **2.1–2.4 are all required** (not “at least one”). We do not claim 2.3 (48-hour cap).

**Claimed controls**

- No system-generated initial passwords. Users set their own password on register, invite accept, and reset.
- Invite token: `uuid.uuid4().hex` (32 hex, 128-bit), single-use; missing/used/expired → 404/410; SPA “Invalid Invitation”.
- Token is not the account password.
- Password reset is a one-time Supabase recovery link. `/reset-password` without a token → “Invalid or expired link”. Reset **expiry duration** itself is a 1.3.x question (up to 7 days); do not invent the number here.

**Do not claim:** 48-hour invite expiry (default TTL is **72 hours**, `_DEFAULT_EXPIRY_HOURS`; admin extend adds another 72h; email copy says 72 hours). Compensating for 2.3: token is not a password, single-use, 32 hex. If TAC fails 2.3, change TTL to ≤48h, deploy, re-upload.

**Helpers:** `casa_auth_qa/render_casa_112_pages.py`, `casa_112_shots.mjs`

### Images

| File | Description |
| --- | --- |
| [`tac_images/1.1.2/CASA_1_1_2_page1.png`](tac_images/1.1.2/CASA_1_1_2_page1.png) | Written evidence page 1 of 2. States we issue no generated initial passwords; invite token is 32 hex, single-use; default TTL 72 hours (ADA cap 48h **not claimed**); reset uses a one-time recovery link. |
| [`tac_images/1.1.2/CASA_1_1_2_page2.png`](tac_images/1.1.2/CASA_1_1_2_page2.png) | Written evidence page 2 of 2. AL1 mapping: 2.1 length PASS, 2.2 alphanumeric PASS, 2.3 48h **not claimed**, 2.4 token cannot become the password PASS. |
| [`tac_images/1.1.2/CASA_1_1_2_invite_expired.png`](tac_images/1.1.2/CASA_1_1_2_invite_expired.png) | Live staging: invite accept with an unknown/expired token shows **Invalid Invitation**. |
| [`tac_images/1.1.2/CASA_1_1_2_forgot_password.png`](tac_images/1.1.2/CASA_1_1_2_forgot_password.png) | Forgot-password form. A standing generated password is not mailed as the account credential. |
| [`tac_images/1.1.2/CASA_1_1_2_reset_expired.png`](tac_images/1.1.2/CASA_1_1_2_reset_expired.png) | `/reset-password` with no recovery token shows **Invalid or expired link**. |

### Portal comment

```
Velvet Elves does not issue system-generated initial passwords. Users choose their own password on register, invite accept, and password reset. Invite activation tokens are 32-character hex (uuid4), single-use, and cannot become the account password. Used, revoked, or unknown tokens return 410/404. Invite links currently expire after 72 hours (ADA 1.1.2 recommends 24h and caps at 48h; we do not claim the 48h cap). Password reset uses a one-time Supabase recovery link; a missing/expired link cannot set a password.
```

---

## 1.1.3 — Passwords stored resistant to offline attacks

**ADA AL1:** list external auth services + written description of password storage (salts/hashing). Verification: ADA-approved IdP **or** NIST 800-63B §5.1.1.2 KDFs.

**Claimed controls**

- Velvet Elves **does not store passwords**. `AuthService` → `sign_up` / `sign_in_with_password`.
- `public.users` is a profile keyed by Auth UUID. `UserRepository.create` never inserts a password. PII Fernet is **not** password hashing.
- GoTrue stores **salted bcrypt** in `auth.users.encrypted_password` (column name is a misnomer; it is a hash). Vendor FAQ: https://supabase.com/docs/guides/auth/password-security
- Google OAuth tokens are Fernet-encrypted separately and are **not** login passwords.

**Do not claim:** ADA-approved IdP for Supabase; that Velvet Elves hashes passwords in app code; a bcrypt cost factor; that we dumped production `encrypted_password` values; live HIBP on GoTrue unless a dashboard shot shows it.

**Helpers:** `casa_auth_qa/render_casa_113_pages.py` (write-up PNGs of our own schema/attestation only). Vendor docs screenshot is owner-captured — do not regenerate it.

### Images

| File | Description |
| --- | --- |
| [`tac_images/1.1.3/CASA_1_1_3_page1.png`](tac_images/1.1.3/CASA_1_1_3_page1.png) | Written evidence page 1 of 2. External services (GoTrue owns credentials; Google OAuth tokens out of scope). App tables have no password column. Hash lives in GoTrue as salted bcrypt. |
| [`tac_images/1.1.3/CASA_1_1_3_page2.png`](tac_images/1.1.3/CASA_1_1_3_page2.png) | Written evidence page 2 of 2. AL1 mapping: IdP not claimed; NIST KDF **PASS via vendor**; no custom application hasher. Attestation that production hashes were not exported. |
| [`tac_images/1.1.3/CASA_1_1_3_users_schema.png`](tac_images/1.1.3/CASA_1_1_3_users_schema.png) | `public.users` from `supabase/migrations/20260225_init.sql`: id, tenant, email, name, phone, role, flags, timestamps — **no password column**. Comment that hashes live in `auth.users.encrypted_password`. |
| [`tac_images/1.1.3/CASA_1_1_3_supabase_docs.png`](tac_images/1.1.3/CASA_1_1_3_supabase_docs.png) | **Owner-captured** supabase.com docs (Ask Supabase AI): bcrypt, random salt, hash in `auth.users.encrypted_password` (column name is a misnomer). No project keys. |

### Portal comment

```
User passwords are not stored in Velvet Elves tables. Login and register call Supabase Auth (GoTrue). GoTrue stores a salted bcrypt hash in auth.users.encrypted_password (hash, not reversible encryption; see supabase.com/docs/guides/auth/password-security). public.users is a profile row with no password column. We do not operate a custom password hasher. Google OAuth tokens are Fernet-encrypted separately and are not login passwords.
```

---

## 1.2.1 — Default credentials shall not be present

**ADA:** default credentials = predefined username **and** password pairs (Admin/Admin). An admin with a user-chosen password is not a default credential. AL1: if default accounts exist on public interfaces, confirm default credentials are not used.

**Claimed controls**

- No default accounts on public interfaces. Ship path is self-register or invite accept; the user always chooses the password.
- Login and register forms start empty (placeholders only). `DEFAULT_ACCOUNT_ROLE` is the register role picker (Agent), not a password.
- SQL seeds do not insert `auth.users` or passwords.
- Google Sign-in is the user’s Google account via OAuth, not a shared Velvet Elves password.
- Staging: classic pair `admin@velvetelves.com` / `Admin` → Invalid email or password.

**Do not claim:** ADA-approved IdP; that we fuzzed every published default pair; that operator QA accounts do not exist (they are operator-created, not shipped).

**Helpers:** `casa_auth_qa/render_casa_121_pages.py`, `casa_121_shots.mjs` (Velvet Elves staging only).

### Images

| File | Description |
| --- | --- |
| [`tac_images/1.2.1/CASA_1_2_1_page1.png`](tac_images/1.2.1/CASA_1_2_1_page1.png) | Written evidence page 1 of 2. ADA definition, account-creation paths, empty login form, live classic-pair check. |
| [`tac_images/1.2.1/CASA_1_2_1_page2.png`](tac_images/1.2.1/CASA_1_2_1_page2.png) | Written evidence page 2 of 2. AL1 mapping: no default accounts, no Admin/Admin, admin OK if user-chosen, Google OAuth is not a default password. |
| [`tac_images/1.2.1/CASA_1_2_1_login_empty.png`](tac_images/1.2.1/CASA_1_2_1_login_empty.png) | Live staging `/login`: empty email and password fields (placeholders only). |
| [`tac_images/1.2.1/CASA_1_2_1_register.png`](tac_images/1.2.1/CASA_1_2_1_register.png) | Live staging `/register`: empty password / confirm fields and strength checklist. User must create the password. |
| [`tac_images/1.2.1/CASA_1_2_1_default_rejected.png`](tac_images/1.2.1/CASA_1_2_1_default_rejected.png) | Live staging: `admin@velvetelves.com` with classic `Admin` rejected — “Invalid email or password.” Password remains masked. |

### Portal comment

```
Velvet Elves does not ship default accounts or predefined username/password pairs on public interfaces (no Admin/Admin). Accounts are created only by self-register or invite accept; the user always chooses the password. Login and register forms start empty. A classic default pair is rejected. Google Sign-in is the user's Google account via OAuth, not a shared Velvet Elves password. SQL seeds do not insert passwords.
```

---

## 1.3.1 — Out of band verifier shall expire

**ADA:** list external auth services + written expiry process. If not an ADA-approved IdP: password-reset links expire within **7 days**; MFA verifiers within **30 minutes**.

**Claimed controls**

- Reset is GoTrue `reset_password_email`. Auth Email OTP expiration is **3600 seconds (1 hour)**. App copy matches.
- `/reset-password` without a token → Invalid or expired link.
- TOTP uses a 30-second time step (under the 30-minute MFA cap).
- No SMS OTP. Invite TTL stays on row 1.1.2.

**Helpers:** `casa_auth_qa/render_casa_131_pages.py`, `casa_131_shots.mjs` (Velvet Elves staging only).

### Images

| File | Description |
| --- | --- |
| [`tac_images/1.3.1/CASA_1_3_1_page1.png`](tac_images/1.3.1/CASA_1_3_1_page1.png) | Written evidence page 1 of 2. External services, GoTrue recovery email, 3600-second OTP expiry, TOTP 30-second step. |
| [`tac_images/1.3.1/CASA_1_3_1_page2.png`](tac_images/1.3.1/CASA_1_3_1_page2.png) | Written evidence page 2 of 2. AL1 mapping vs 7-day reset cap and 30-minute MFA cap. |
| [`tac_images/1.3.1/CASA_1_3_1_forgot_password.png`](tac_images/1.3.1/CASA_1_3_1_forgot_password.png) | Live staging `/forgot-password`: user requests a reset email. |
| [`tac_images/1.3.1/CASA_1_3_1_expires_1h.png`](tac_images/1.3.1/CASA_1_3_1_expires_1h.png) | Live staging after submit: **Link expires in 1 hour**. |
| [`tac_images/1.3.1/CASA_1_3_1_reset_expired.png`](tac_images/1.3.1/CASA_1_3_1_reset_expired.png) | Live staging `/reset-password` with no token: **Invalid or expired link**. |
| [`tac_images/1.3.1/CASA_1_3_1_supabase_email_otp.png`](tac_images/1.3.1/CASA_1_3_1_supabase_email_otp.png) | **Owner-captured** Auth Email settings: Email OTP expiration **3600** seconds (1 hour). Same setting covers recovery links. |

### Portal comment

```
Password reset uses a Supabase Auth recovery email. Auth Email OTP expiration is 3600 seconds (1 hour), matching the app copy. Opening /reset-password without a valid token shows Invalid or expired link and cannot set a password. TOTP MFA codes use a 30-second time step, under ADA's 30-minute MFA verifier limit. We do not send SMS OTPs.
```

This dashboard shot also shows GoTrue min password length 6 and HaveIBeenPwned off. Do not use it to claim HIBP or that GoTrue’s minimum is 8. Row 1.1.1 already states our API requires 8 + digit + a static denylist.

---

## 1.3.2 — Out of band verifier shall only be used once

**ADA:** list external auth services + written process. If not an ADA-approved IdP, the OOB verifier can be used only once.

**Claimed controls**

- Recovery email is GoTrue; we do not store a reusable reset code.
- Confirm without a valid token → 400 Invalid or expired reset token.
- SPA `/reset-password` with no token cannot set a password; user must request a new link.
- Staging: same invalid token posted twice, both 400.

**Helpers:** `casa_auth_qa/render_casa_132_pages.py`, `casa_132_shots.mjs`, `casa_132_confirm.py` (Velvet Elves staging only).

### Images

| File | Description |
| --- | --- |
| [`tac_images/1.3.2/CASA_1_3_2_page1.png`](tac_images/1.3.2/CASA_1_3_2_page1.png) | Written evidence page 1 of 2. GoTrue recovery is single-use; 400 on invalid token. |
| [`tac_images/1.3.2/CASA_1_3_2_page2.png`](tac_images/1.3.2/CASA_1_3_2_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/1.3.2/CASA_1_3_2_reset_expired.png`](tac_images/1.3.2/CASA_1_3_2_reset_expired.png) | Live staging `/reset-password` with no token: Invalid or expired link; Request a new link. |
| [`tac_images/1.3.2/CASA_1_3_2_confirm_rejected.png`](tac_images/1.3.2/CASA_1_3_2_confirm_rejected.png) | Staging API: same invalid recovery token twice, both HTTP 400. |

### Portal comment

```
Password reset recovery links are issued by Supabase Auth and cannot be reused. Confirm requires a valid recovery token from the email. A missing, used, or invalid token returns Invalid or expired reset token and cannot set a password. The reset page with no token shows Invalid or expired link and asks the user to request a new one. TOTP MFA is verified through a GoTrue challenge; codes rotate every 30 seconds. We do not send SMS OTPs.
```

---

## 1.3.3 — Out of band verifier shall be securely random

**ADA:** list external auth services + written generation algorithm. If not an ADA-approved IdP, codes must be generated so an attacker cannot predict or manipulate them.

**Claimed controls**

- Reset is GoTrue `reset_password_email`. The app does not mint or store a reset OTP.
- Auth Email OTP length is **8 digits**. Recovery emails carry a hashed GoTrue token, not a sequential app counter.
- Invite tokens the app mints: `uuid.uuid4().hex` (32 hex; CPython uses `os.urandom`).
- TOTP shared secret comes from GoTrue factor enroll.

**Do not claim:** a specific GoTrue CSPRNG source file; ADA-approved IdP; that Email OTP length 8 is ≥64 bits (that is 1.3.4). This dashboard shot also shows GoTrue min password 6 and HIBP off — do not use it to claim HIBP or that GoTrue’s minimum is 8.

**Helpers:** `casa_auth_qa/render_casa_133_pages.py`, `casa_133_shots.mjs` (Velvet Elves staging only). Owner Email OTP shot is copied from 1.3.1 — do not recapture supabase.com.

### Images

| File | Description |
| --- | --- |
| [`tac_images/1.3.3/CASA_1_3_3_page1.png`](tac_images/1.3.3/CASA_1_3_3_page1.png) | Written evidence page 1 of 2. Vendor reset codes; uuid4 invite tokens; GoTrue TOTP secret. |
| [`tac_images/1.3.3/CASA_1_3_3_page2.png`](tac_images/1.3.3/CASA_1_3_3_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/1.3.3/CASA_1_3_3_code.png`](tac_images/1.3.3/CASA_1_3_3_code.png) | Application code: reset delegates to GoTrue; invite token is uuid4 hex; TOTP secret from GoTrue enroll. |
| [`tac_images/1.3.3/CASA_1_3_3_forgot_password.png`](tac_images/1.3.3/CASA_1_3_3_forgot_password.png) | Live staging `/forgot-password`: user requests a reset **link**. No app-generated code is shown. |
| [`tac_images/1.3.3/CASA_1_3_3_expires_1h.png`](tac_images/1.3.3/CASA_1_3_3_expires_1h.png) | Live staging after submit: check inbox; link expires in 1 hour. Still no displayed OTP. |
| [`tac_images/1.3.3/CASA_1_3_3_reset_expired.png`](tac_images/1.3.3/CASA_1_3_3_reset_expired.png) | Live staging `/reset-password` with no token: Invalid or expired link. |
| [`tac_images/1.3.3/CASA_1_3_3_supabase_email_otp.png`](tac_images/1.3.3/CASA_1_3_3_supabase_email_otp.png) | **Owner-captured** Auth Email settings: Email OTP length **8** digits (same panel as 1.3.1). |

### Portal comment

```
Password-reset recovery links are issued by Supabase Auth. The app does not generate or store a reset code. Email OTP length is 8 digits. Recovery uses a hashed vendor token in the email link, not a sequential number. Invite tokens the app mints are 32-character uuid4 hex. TOTP secrets are generated by GoTrue. We do not send SMS OTPs.
```

---

## 1.3.4 — Out of band verifier shall be resistant to brute force attacks

**ADA:** list external auth services + written generation and rate-limiting. If not an ADA-approved IdP: ≥**20 bits** of entropy; if **<64 bits**, a rate-limiting mechanism is required.

**Claimed controls**

- Email OTP is **8 digits** (~26.6 bits): meets 20 bits, under 64 bits → rate limit required.
- Recovery link is a hashed GoTrue token (**>64 bits**). Guessed confirm tokens return **400** and cannot set a password.
- Invite token is uuid4 hex (**>64 bits**).
- TOTP is 6 digits (~20 bits, ADA’s typical example), under 64 bits → rate limit required.
- GoTrue Auth Rate Limits (production, owner-captured): **token verifications 30 / 5 min / IP**; **emails 30 / hour**.
- GoTrue MFA challenge/verify: **15 / hour / IP** per official docs (not a customizable dashboard field). App does **not** add a second limiter on confirm or `/users/mfa/verify`.

**Do not claim:** an in-app limiter on password-reset confirm or MFA verify; that we live-hit a 429 on OTP verify; ADA-approved IdP; SMS OTP; live HIBP (same Email settings panel still shows HIBP off and GoTrue min 6).

**Helpers:** `casa_auth_qa/render_casa_134_pages.py`, `casa_134_confirm.py`, `casa_134_shots.mjs`. Rate Limits and Email OTP shots are copies of owner captures from 1.1.1 / 1.3.1 — do not recapture supabase.com.

### Images

| File | Description |
| --- | --- |
| [`tac_images/1.3.4/CASA_1_3_4_page1.png`](tac_images/1.3.4/CASA_1_3_4_page1.png) | Written evidence page 1 of 2. Entropy of Email OTP, recovery token, invite uuid4, and TOTP. |
| [`tac_images/1.3.4/CASA_1_3_4_page2.png`](tac_images/1.3.4/CASA_1_3_4_page2.png) | Written evidence page 2 of 2. Rate limits for secrets under 64 bits; AL1 mapping. |
| [`tac_images/1.3.4/CASA_1_3_4_confirm_guesses.png`](tac_images/1.3.4/CASA_1_3_4_confirm_guesses.png) | Staging API: five guessed recovery tokens, all HTTP 400. None set a password. |
| [`tac_images/1.3.4/CASA_1_3_4_reset_expired.png`](tac_images/1.3.4/CASA_1_3_4_reset_expired.png) | Live staging `/reset-password` with no token: Invalid or expired link. |
| [`tac_images/1.3.4/CASA_1_3_4_supabase_rate_limits.png`](tac_images/1.3.4/CASA_1_3_4_supabase_rate_limits.png) | **Owner-captured** Auth Rate Limits: token verifications 30 / 5 min / IP; emails 30 / hour. |
| [`tac_images/1.3.4/CASA_1_3_4_supabase_email_otp.png`](tac_images/1.3.4/CASA_1_3_4_supabase_email_otp.png) | **Owner-captured** Auth Email: OTP length **8** digits (entropy source). |

### Portal comment

```
Out-of-band reset codes meet ADA's 20-bit entropy floor. Email OTP is 8 digits (about 27 bits). Recovery links use a hashed GoTrue token with well over 64 bits. Because the 8-digit OTP is under 64 bits, GoTrue rate-limits OTP and magic-link verifications to 30 requests per 5 minutes per IP. Password-reset emails are capped at 30 per hour. TOTP is 6 digits (ADA's typical 20-bit example) and GoTrue limits MFA challenge and verify to 15 requests per hour per IP. Guessing a reset token returns 400 and cannot set a password. We do not send SMS OTPs.
```

---

## 2.1.1 — URLs shall not expose authentication material

**ADA:** DAST results. Scan must not find password-via-GET, password in query string, or session token in URL. Secrets go in the body or headers.

**Claimed controls**

- Login is `POST /users/login` with password in the form body. Staging GET with password in the query does **not** authenticate (401).
- Session JWT is `Authorization: Bearer` (`apiFetch` / `OAuth2PasswordBearer`). `GET /users/me?access_token=` is ignored.
- SPA `/login` address is `https://app.stage.velvetelves.com/login` (no token query).
- Google OAuth: code + PKCE; callback `postMessage`. Reset confirm is POST JSON body.
- Official ZAP (SPA `10f54abf`, API `a9d78f05`, auth `33afa2aa`): plugins 3 and 10024 are FAIL in the CASA config and were **not** reported.

**Do not claim:** that *no* token ever appears in any URL. Invite accept and public invoice links may include a one-time **capability** token in the query; those are not the session JWT. GoTrue recovery may use a URL **fragment**. Session is still `localStorage` JWT, not cookies.

**Helpers:** `casa_auth_qa/render_casa_211_pages.py`, `casa_211_probe.py`, `casa_211_shots.mjs`.

### Images

| File | Description |
| --- | --- |
| [`tac_images/2.1.1/CASA_2_1_1_page1.png`](tac_images/2.1.1/CASA_2_1_1_page1.png) | Written evidence page 1 of 2. Password POST body; JWT Bearer; OAuth postMessage; capability tokens called out. |
| [`tac_images/2.1.1/CASA_2_1_1_page2.png`](tac_images/2.1.1/CASA_2_1_1_page2.png) | Written evidence page 2 of 2. DAST mapping + live GET probes. |
| [`tac_images/2.1.1/CASA_2_1_1_code.png`](tac_images/2.1.1/CASA_2_1_1_code.png) | Login POST body; apiFetch Authorization header; OAuth2PasswordBearer. |
| [`tac_images/2.1.1/CASA_2_1_1_query_rejected.png`](tac_images/2.1.1/CASA_2_1_1_query_rejected.png) | Staging: GET login with password query, GET /me with access_token query, GET /me — all 401. |
| [`tac_images/2.1.1/CASA_2_1_1_login.png`](tac_images/2.1.1/CASA_2_1_1_login.png) | Live staging `/login`. Address bar: `https://app.stage.velvetelves.com/login` (no token query). |

### Portal comment

```
Login is POST /users/login with the password in the request body, never as a GET query parameter. The session JWT is sent as Authorization Bearer, not in the URL. Official ADA ZAP scans of the SPA and API did not report Session ID in URL or Sensitive Information in URL. Google OAuth returns tokens to a popup via postMessage. Password-reset confirm posts the recovery token in the JSON body. Invite accept and public invoice links may include a one-time capability token in the query; those are not the user session JWT.
```

---

## 2.2.1 — Logout invalidates stateful session tokens

**ADA:** code or docs showing logout/expiration invalidate session tokens, including refresh tokens. Server-side invalidation on logout and expiration.

**Claimed controls**

- App menu **Log Out** (and MFA gate **Sign out**) call `AuthContext.logout()`.
- `POST /users/logout` → GoTrue `admin.sign_out(token, "local")` then **204**.
- SPA clears `velvet_elves_token` / `velvet_elves_refresh_token` and goes to `/login`.
- Staging: login 200 → logout 204 → refresh replay **401**.
- Access JWT is stateless and expires on its own (2.2.3). Scope `local` is this session, not every device.

**Do not claim:** HttpOnly cookies; that the access JWT is killed instantly; global logout of all devices.

**Helpers:** `casa_auth_qa/render_casa_221_pages.py`, `casa_221_replay.py` (`QA_PASSWORD`), `casa_221_shots.mjs`.

### Images

| File | Description |
| --- | --- |
| [`tac_images/2.2.1/CASA_2_2_1_page1.png`](tac_images/2.2.1/CASA_2_2_1_page1.png) | Written evidence page 1 of 2. Logout flow, GoTrue sign_out, staging replay. |
| [`tac_images/2.2.1/CASA_2_2_1_page2.png`](tac_images/2.2.1/CASA_2_2_1_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/2.2.1/CASA_2_2_1_code.png`](tac_images/2.2.1/CASA_2_2_1_code.png) | Logout endpoint + AuthContext fetch and clearTokens. |
| [`tac_images/2.2.1/CASA_2_2_1_refresh_replay.png`](tac_images/2.2.1/CASA_2_2_1_refresh_replay.png) | Staging API: login 200, logout 204, refresh replay 401. Tokens not shown. |
| [`tac_images/2.2.1/CASA_2_2_1_logout_menu.png`](tac_images/2.2.1/CASA_2_2_1_logout_menu.png) | Live staging admin dashboard with **Log Out**. |
| [`tac_images/2.2.1/CASA_2_2_1_after_logout.png`](tac_images/2.2.1/CASA_2_2_1_after_logout.png) | After Log Out: staging `/login`. |

### Portal comment

```
Users can log out from the app menu. Logout calls POST /users/logout, which revokes this Supabase session (GoTrue admin sign_out) and then clears browser storage. Replaying the refresh token after logout returns 401. The short-lived access JWT expires on its own (under 24 hours).
```

---

## 2.2.2 — Terminate other sessions after password change

**ADA:** after a successful password change (including reset/recovery), terminate all **other** active sessions including refresh tokens, **or** give the user an option. AL1: code **or** documentation.

**Claimed controls**

- Password change is **Forgot password** / recovery. There is no logged-in current-password form.
- Confirm is `POST /users/password-reset/confirm`. Success: “Please sign in.” SPA redirects to `/login`.
- Confirm updates the password in GoTrue. GoTrue **by default** deletes other `auth.sessions` rows:
  - recovery session present → `LogoutAllExceptMe`;
  - `admin.update_user_by_id({password})` → `Logout` of all sessions (`sessionID` is nil).
- Public source: `github.com/supabase/auth` `User.UpdatePassword`. Not a dashboard toggle.

**Do not claim:** that app code calls `sign_out(others)`; a live two-device reset of a production account; that leftover access JWTs die instantly (2.2.3); that Gmail/Calendar mailbox tokens are login sessions; that “Secure password change” OFF is the session-kill switch; HttpOnly cookies.

**Helpers:** `casa_auth_qa/render_casa_222_pages.py`, `casa_222_shots.mjs` (Velvet Elves staging only). Do **not** recapture supabase.com.

### Images

| File | Description |
| --- | --- |
| [`tac_images/2.2.2/CASA_2_2_2_page1.png`](tac_images/2.2.2/CASA_2_2_2_page1.png) | Written evidence page 1 of 2. Reset/recovery path; GoTrue LogoutAllExceptMe vs Logout all; access JWT vs federated mailbox tokens. |
| [`tac_images/2.2.2/CASA_2_2_2_page2.png`](tac_images/2.2.2/CASA_2_2_2_page2.png) | Written evidence page 2 of 2. AL1 mapping. Attested from confirm code + public GoTrue source, not a live two-device reset. |
| [`tac_images/2.2.2/CASA_2_2_2_code.png`](tac_images/2.2.2/CASA_2_2_2_code.png) | Confirm: `update_user({password})` or `admin.update_user_by_id({password})`; then sign in. |
| [`tac_images/2.2.2/CASA_2_2_2_gotrue.png`](tac_images/2.2.2/CASA_2_2_2_gotrue.png) | Public GoTrue `UpdatePassword` excerpt. Pillow write-up of source, not a supabase.com screenshot. |
| [`tac_images/2.2.2/CASA_2_2_2_login.png`](tac_images/2.2.2/CASA_2_2_2_login.png) | Live staging `/login` with **Forgot password?** |
| [`tac_images/2.2.2/CASA_2_2_2_forgot_password.png`](tac_images/2.2.2/CASA_2_2_2_forgot_password.png) | Live staging forgot-password form. |
| [`tac_images/2.2.2/CASA_2_2_2_reset_expired.png`](tac_images/2.2.2/CASA_2_2_2_reset_expired.png) | Live staging `/reset-password` with no token: **Invalid or expired link**. |

### Portal comment

```
Password change is through password reset (Forgot password), not an in-app current-password form. Confirm updates the password in Supabase Auth. GoTrue then terminates other sessions by default: a recovery session logs out every other session; an admin password update logs out all sessions for that user. After a successful reset the app sends the user to sign in. Short-lived access JWTs expire on their own (under 24 hours).
```

---

## 2.2.3 — Stateless authentication tokens expire within 24 hours

**ADA:** non-revocable **stateless** authentication tokens must expire **within 24 hours** of issue. AL1: code, screenshot, or documentation of the validity period.

**Claimed controls**

- Access JWT is the stateless session token. Refresh is a separate, stateful GoTrue session (2.2.1 / 2.2.2).
- Staging 28 Aug 2026: `POST /users/login` then decode `iat` / `exp` — **28800 seconds (8.00 hours)**, ES256. Token not shown.
- `decode_access_token` verifies the JWT; expired tokens raise `JWTError` → 401.
- SPA reads `exp` (`getTokenExpirationMs`) and silent-refreshes ~60 s before expiry.

**Do not claim:** a 1-hour access JWT (this project issues **8 hours**); that the refresh token expires within 24 hours; HttpOnly cookies; invite/reset/mailbox tokens as the session JWT; pasting JWTs.

**Helpers:** `casa_auth_qa/render_casa_223_pages.py`, `casa_223_exp.py` (`QA_PASSWORD`). Do **not** recapture supabase.com. Owner JWT-settings dashboard shot is optional backup (S2).

### Images

| File | Description |
| --- | --- |
| [`tac_images/2.2.3/CASA_2_2_3_page1.png`](tac_images/2.2.3/CASA_2_2_3_page1.png) | Written evidence page 1 of 2. Access JWT vs refresh; staging 8-hour lifetime; API and SPA exp handling. |
| [`tac_images/2.2.3/CASA_2_2_3_page2.png`](tac_images/2.2.3/CASA_2_2_3_page2.png) | Written evidence page 2 of 2. AL1 mapping. Measured from live staging login. |
| [`tac_images/2.2.3/CASA_2_2_3_code.png`](tac_images/2.2.3/CASA_2_2_3_code.png) | `decode_access_token` verifies `exp`; SPA `getTokenExpirationMs` and silent refresh 60 s before expiry. |
| [`tac_images/2.2.3/CASA_2_2_3_exp.png`](tac_images/2.2.3/CASA_2_2_3_exp.png) | Staging API: login 200, JWT `exp − iat` = 28800 s (8.00 hours), under 24 hours. Token not shown. |

### Portal comment

```
The user session access token is a signed JWT. On staging (28 Aug 2026) exp minus iat is 28800 seconds (8 hours), under ADA's 24-hour cap. The API rejects expired JWTs. The app reads exp and refreshes about a minute before expiry. The refresh token is a separate, revocable session token (see 2.2.1), not the stateless token this row covers.
```

---

## 2.3.1 — Cookie-based session tokens shall have the Secure attribute

**ADA:** cookie-based session tokens must have the **Secure** attribute. AL1 evidence is ADA DAST. Verification: scan must not identify Burp 5243392 (TLS cookie without secure flag). ZAP plugin **10011**.

**Claimed controls**

- Session is **not a cookie**. Login JSON body has `access_token`; SPA stores `velvet_elves_token` in `localStorage`; API uses `Authorization: Bearer`.
- Staging 28 Aug 2026: `POST /users/login` **Set-Cookie names: none**. HTTPS. HSTS present.
- Official ZAP SPA `10f54abf`, API `a9d78f05`, auth `33afa2aa`: Cookie Without Secure Flag **not** reported. SPA CASA conf maps 10011 to FAIL.

**Do not claim:** that the JWT is a cookie with Secure; HttpOnly session cookies (that is 2.3.2); that localStorage equals HttpOnly.

**Helpers:** `casa_auth_qa/render_casa_231_pages.py`, `casa_231_headers.py` (`QA_PASSWORD`). Do **not** recapture ZAP UI or supabase.com.

### Images

| File | Description |
| --- | --- |
| [`tac_images/2.3.1/CASA_2_3_1_page1.png`](tac_images/2.3.1/CASA_2_3_1_page1.png) | Written evidence page 1 of 2. Not a cookie session; staging Set-Cookie none; DAST 10011 not raised. |
| [`tac_images/2.3.1/CASA_2_3_1_page2.png`](tac_images/2.3.1/CASA_2_3_1_page2.png) | Written evidence page 2 of 2. AL1 mapping. Secure attribute N/A because there is no session cookie. |
| [`tac_images/2.3.1/CASA_2_3_1_code.png`](tac_images/2.3.1/CASA_2_3_1_code.png) | localStorage persistTokens; Authorization Bearer; OAuth2PasswordBearer; HSTS. |
| [`tac_images/2.3.1/CASA_2_3_1_zap.png`](tac_images/2.3.1/CASA_2_3_1_zap.png) | Official CASA ZAP config 10011 FAIL; scan IDs; alert not listed. Not a ZAP product screenshot. |
| [`tac_images/2.3.1/CASA_2_3_1_headers.png`](tac_images/2.3.1/CASA_2_3_1_headers.png) | Staging login 200, Set-Cookie none, HSTS yes, session keys in JSON. Token values not shown. |

### Portal comment

```
Session tokens are not cookies. Login returns a JWT in the JSON body and the app stores it in localStorage, then sends Authorization Bearer. Staging POST /users/login sets no Set-Cookie and is HTTPS with HSTS. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Cookie Without Secure Flag. There is no session cookie for the Secure attribute to apply to.
```

---

## 2.3.2 — Cookie-based session tokens shall have the HttpOnly attribute

**ADA:** cookie-based session tokens must have the **HttpOnly** attribute. AL1 evidence is ADA DAST. Verification: scan must not identify Burp 500600 (Cookie without HttpOnly flag). ZAP plugin **10010**.

**Claimed controls**

- Session is **not a cookie**. Login JSON body has `access_token`; SPA stores `velvet_elves_token` in `localStorage`; API uses `Authorization: Bearer`.
- Staging 28 Aug 2026: `POST /users/login` **Set-Cookie names: none**.
- Official ZAP SPA `10f54abf`, API `a9d78f05`, auth `33afa2aa`: Cookie No HttpOnly Flag **not** reported. SPA CASA conf maps 10010 to FAIL.
- `localStorage` is readable by JavaScript. This row does **not** claim HttpOnly.

**Do not claim:** HttpOnly session cookies; that localStorage equals HttpOnly; that the JWT is a Secure cookie (2.3.1).

**Helpers:** `casa_auth_qa/render_casa_232_pages.py`, `casa_232_headers.py` (`QA_PASSWORD`). Do **not** recapture ZAP UI or supabase.com.

### Images

| File | Description |
| --- | --- |
| [`tac_images/2.3.2/CASA_2_3_2_page1.png`](tac_images/2.3.2/CASA_2_3_2_page1.png) | Written evidence page 1 of 2. Not a cookie session; localStorage is not HttpOnly; DAST 10010 not raised. |
| [`tac_images/2.3.2/CASA_2_3_2_page2.png`](tac_images/2.3.2/CASA_2_3_2_page2.png) | Written evidence page 2 of 2. AL1 mapping. HttpOnly N/A because there is no session cookie. |
| [`tac_images/2.3.2/CASA_2_3_2_code.png`](tac_images/2.3.2/CASA_2_3_2_code.png) | localStorage persistTokens / clearTokens; Authorization Bearer; OAuth2PasswordBearer. |
| [`tac_images/2.3.2/CASA_2_3_2_zap.png`](tac_images/2.3.2/CASA_2_3_2_zap.png) | Official CASA ZAP config 10010 FAIL; scan IDs; alert not listed. Not a ZAP product screenshot. |
| [`tac_images/2.3.2/CASA_2_3_2_headers.png`](tac_images/2.3.2/CASA_2_3_2_headers.png) | Staging login 200, Set-Cookie none, session keys in JSON. Token values not shown. |

### Portal comment

```
Session tokens are not cookies. Login returns a JWT in the JSON body and the app stores it in localStorage, then sends Authorization Bearer. Staging POST /users/login sets no Set-Cookie. Official ADA ZAP scans (SPA 10f54abf, API a9d78f05, auth 33afa2aa) did not report Cookie No HttpOnly Flag. There is no session cookie for the HttpOnly attribute to apply to.
```

---

## 2.3.3 — Session tokens rather than static API secrets and keys

**ADA:** use session tokens rather than static API secrets, except legacy implementations. AL1: code or docs of dynamically generated tokens. Verification: session tokens generated after user authentication.

**Claimed controls**

- After password login, GoTrue `sign_in_with_password` mints a new `access_token` / `refresh_token`. SPA sends `Authorization: Bearer`.
- Staging 28 Aug 2026: two logins → `iat` 1787941282 then 1787941285 (different). Tokens not shown.
- Gmail/Calendar: per-user OAuth tokens in `integrations` (Fernet), not a shared mailbox key, not the login session.
- Tenant inbound CRM keys (`X-API-Key`) are a machine contact-push path. Creating them requires an admin JWT. They are not the human session.

**Do not claim:** that the product has no API keys anywhere; that inbound CRM keys are the user session; HttpOnly cookies; pasting JWTs or key values.

**Helpers:** `casa_auth_qa/render_casa_233_pages.py`, `casa_233_dyn.py` (`QA_PASSWORD`).

### Images

| File | Description |
| --- | --- |
| [`tac_images/2.3.3/CASA_2_3_3_page1.png`](tac_images/2.3.3/CASA_2_3_3_page1.png) | Written evidence page 1 of 2. GoTrue JWT after login; per-user Google tokens; inbound CRM keys called out as not the session. |
| [`tac_images/2.3.3/CASA_2_3_3_page2.png`](tac_images/2.3.3/CASA_2_3_3_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/2.3.3/CASA_2_3_3_code.png`](tac_images/2.3.3/CASA_2_3_3_code.png) | `sign_in_with_password` returns session JWT; inbound `vek_` key generation. |
| [`tac_images/2.3.3/CASA_2_3_3_dyn.png`](tac_images/2.3.3/CASA_2_3_3_dyn.png) | Two staging logins, different `iat`. Tokens not shown. |

### Portal comment

```
User login does not use a static API key. After a correct password, Supabase Auth issues a new JWT and refresh token for that session. Two successive staging logins produced different iat values. The app sends Authorization Bearer. Gmail and Calendar use that user's OAuth tokens, not a shared mailbox key. Tenant inbound CRM keys (X-API-Key) are a separate machine path for contact push; they are not the user session.
```

---

## 2.3.4 — Stateless session tokens shall use digital signatures

**ADA:** stateless session tokens must use signatures / encryption against tampering and `alg=none`. AL1 evidence is ADA DAST. Verification: scan must not identify Burp 2099456 (JWT signature not verified) or 2099457 (JWT none algorithm supported).

**Claimed controls**

- `decode_access_token` uses `jose.jwt.decode`. Staging alg **ES256** (2.2.3). HS256 uses `algorithms=["HS256"]`; otherwise JWKS by `kid` (ES256/RS256). `aud` must be `authenticated`.
- `JWTError` → 401 from `get_current_user`.
- Unit tests reject invalid, tampered, expired, wrong audience, and wrong secret.
- Official ZAP SPA `10f54abf`, API `a9d78f05`, auth `33afa2aa`: DAST_SUMMARY does not list JWT signature-not-verified or none-algorithm. Those Burp IDs are not ZAP plugin IDs in the CASA conf.
- Staging: `GET /users/me` with no Authorization, and with `Bearer not-a-jwt`, both **401**. No forged JWT was sent.

**Do not claim:** that ZAP ran Burp plugins 2099456/2099457; an explicit `alg == "none"` denylist line; HttpOnly cookies; pasting JWTs or `SUPABASE_JWT_SECRET`.

**Helpers:** `casa_auth_qa/render_casa_234_pages.py`, `casa_234_reject.py`. Do **not** recapture ZAP/Burp UI.

### Images

| File | Description |
| --- | --- |
| [`tac_images/2.3.4/CASA_2_3_4_page1.png`](tac_images/2.3.4/CASA_2_3_4_page1.png) | Written evidence page 1 of 2. jose verify; DAST; Google tokens not the session JWT. |
| [`tac_images/2.3.4/CASA_2_3_4_page2.png`](tac_images/2.3.4/CASA_2_3_4_page2.png) | Written evidence page 2 of 2. AL1 mapping. |
| [`tac_images/2.3.4/CASA_2_3_4_code.png`](tac_images/2.3.4/CASA_2_3_4_code.png) | `decode_access_token` + 401 on `JWTError`. |
| [`tac_images/2.3.4/CASA_2_3_4_zap.png`](tac_images/2.3.4/CASA_2_3_4_zap.png) | Burp JWT IDs vs official ZAP scans; alerts not listed. Not a ZAP/Burp screenshot. |
| [`tac_images/2.3.4/CASA_2_3_4_reject.png`](tac_images/2.3.4/CASA_2_3_4_reject.png) | Staging GET /users/me: no Authorization 401; Bearer not-a-jwt 401. |

### Portal comment

```
The user session is a signed JWT. Staging issues ES256. The API verifies the signature with jose (HS256 secret or JWKS for ES256/RS256) and rejects invalid, expired, or tampered tokens with 401. Official ADA ZAP scans did not report JWT signature-not-verified or JWT none-algorithm findings. Gmail and Calendar tokens are Fernet-encrypted at rest and are not the session JWT.
```

---

## 2.4.1 — Full login session or re-auth before sensitive account changes

**ADA:** a **full, valid login session** or **re-authentication / secondary verification** before sensitive transactions or account modifications. AL1 evidence is code or documentation. Verification is the same **or**.

**Claimed controls**

- `PATCH /users/me` (profile and sign-in email) uses `Depends(get_current_user)`. JWT must verify; inactive users 403.
- Staging 28 Aug 2026: `PATCH /users/me` no Authorization **401**; `Bearer not-a-jwt` **401**; `GET /users/me` no Authorization **401**; valid session JWT **200**.
- SPA Settings → Profile (`/settings/account`) is behind `ProtectedRoute`.
- Password change is Forgot password / recovery email (OOB), not an in-session current-password form.
- `POST /users/mfa/disable` requires a current TOTP. A leftover `aal2` JWT is not enough. Platform admin APIs also need `aal2` (3.3.1).

**Do not claim:** password re-prompt before every profile save; that self-service email change is restricted or waits for a new-inbox confirm (`email_confirm=True` applies it immediately); MFA for all users; HttpOnly cookies.

**Helpers:** `casa_auth_qa/render_casa_241_pages.py`, `casa_241_reject.py` (`QA_PASSWORD`), `casa_241_shots.mjs` (staging Settings Profile only). Do **not** attach `/login`. Do **not** change the QA email or turn MFA off.

### Images

| File | Description |
| --- | --- |
| [`tac_images/2.4.1/CASA_2_4_1_page1.png`](tac_images/2.4.1/CASA_2_4_1_page1.png) | Written evidence page 1 of 2. Session gate on PATCH /me; password via recovery email; MFA disable needs current TOTP. |
| [`tac_images/2.4.1/CASA_2_4_1_page2.png`](tac_images/2.4.1/CASA_2_4_1_page2.png) | Written evidence page 2 of 2. AL1 mapping. Email change is not claimed as restricted. |
| [`tac_images/2.4.1/CASA_2_4_1_code.png`](tac_images/2.4.1/CASA_2_4_1_code.png) | `get_current_user`; `PATCH /me`; password-reset request; `mfa/disable`. |
| [`tac_images/2.4.1/CASA_2_4_1_reject.png`](tac_images/2.4.1/CASA_2_4_1_reject.png) | Staging: unsigned PATCH/GET 401; garbage Bearer 401; valid JWT GET 200. Email redacted on 200. |
| [`tac_images/2.4.1/CASA_2_4_1_profile.png`](tac_images/2.4.1/CASA_2_4_1_profile.png) | Live staging Settings → Profile while signed in. Personal information (name, sign-in email, phone). Save is PATCH /users/me. Not a login page. |

### Portal comment

```
Profile and sign-in email changes require a valid JWT session (PATCH /users/me). Staging calls without Authorization, or with Bearer not-a-jwt, return 401. Password change uses a recovery email, not an in-session current-password form. Disabling MFA requires a current authenticator code. Platform admin routes require AAL2. We do not claim a password re-prompt on every profile save.
```

---

## Regeneration

From `casa_auth_qa/` (headless Chrome; one page at a time):

| Row | Commands |
| --- | --- |
| 1.1.1 | `python render_casa_111_pages.py` then live/UI shot scripts |
| 1.1.2 | `python render_casa_112_pages.py` then `node casa_112_shots.mjs` |
| 1.1.3 | `python render_casa_113_pages.py` only. Do **not** recapture supabase.com. |
| 1.2.1 | `python render_casa_121_pages.py` then `node casa_121_shots.mjs` (Velvet Elves staging only). |
| 1.3.1 | `python render_casa_131_pages.py` then `node casa_131_shots.mjs` (Velvet Elves staging only). Owner Email OTP shot is already on disk. |
| 1.3.2 | `python render_casa_132_pages.py` then `python casa_132_confirm.py` and `node casa_132_shots.mjs` (staging only). |
| 1.3.3 | `python render_casa_133_pages.py` then `node casa_133_shots.mjs` (staging only). Owner Email OTP shot is copied from 1.3.1 — do **not** recapture supabase.com. |
| 1.3.4 | `python render_casa_134_pages.py` then `python casa_134_confirm.py` and `node casa_134_shots.mjs` (staging only). Rate Limits and Email OTP shots are copies of owner captures — do **not** recapture supabase.com. |
| 2.1.1 | `python render_casa_211_pages.py` then `python casa_211_probe.py` and `node casa_211_shots.mjs` (staging only). Re-run the render script after the login shot so the address bar is stamped. Do not upload `login_raw.png`. |
| 2.2.1 | `python render_casa_221_pages.py` then `python casa_221_replay.py` and `node casa_221_shots.mjs` (staging; needs `QA_PASSWORD`). |
| 2.2.2 | `python render_casa_222_pages.py` then `node casa_222_shots.mjs` (staging only). Do **not** reset a live account and do **not** recapture supabase.com. |
| 2.2.3 | `python render_casa_223_pages.py` then `python casa_223_exp.py` (`QA_PASSWORD`). Do **not** recapture supabase.com. |
| 2.3.1 | `python render_casa_231_pages.py` then `python casa_231_headers.py` (`QA_PASSWORD`). Do **not** recapture ZAP UI or supabase.com. |
| 2.3.2 | `python render_casa_232_pages.py` then `python casa_232_headers.py` (`QA_PASSWORD`). Do **not** recapture ZAP UI or supabase.com. |
| 2.3.3 | `python render_casa_233_pages.py` then `python casa_233_dyn.py` (`QA_PASSWORD`). |
| 2.3.4 | `python render_casa_234_pages.py` then `python casa_234_reject.py`. Do **not** recapture ZAP or Burp UI. |
| 2.4.1 | `python render_casa_241_pages.py` then `python casa_241_reject.py` (`QA_PASSWORD`) and `node casa_241_shots.mjs` (staging Settings Profile only). Do **not** attach `/login`. Do **not** change the QA email or disable MFA. |

Eyeball every PNG for cut-off text before re-upload.
